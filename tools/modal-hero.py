"""Cloud-only final hero render, notebook and export via Modal CLI.
modal run tools/modal-hero.py --mode preview
modal run tools/modal-hero.py --mode render
modal run tools/modal-hero.py --mode encode
modal run tools/modal-hero.py --mode stop-notebook
"""
from pathlib import Path
import json,os,sys,modal
HERE=Path(__file__).resolve().parent
app=modal.App('ali-hero-final')
volume=modal.Volume.from_name('ali-hero-final-20261001',create_if_missing=True)
image=(modal.Image.debian_slim(python_version='3.11')
       .apt_install('xorg','libxkbcommon0','libegl1','ffmpeg')
       .uv_pip_install('bpy==4.5.0','numpy','pillow','jupyterlab')
       .add_local_file(HERE/'render-hero.py','/opt/hero/render-hero.py',copy=True)
       .add_local_file(HERE/'encode-hero.py','/opt/hero/encode-hero.py',copy=True))
LOCAL=HERE.parent.parent/'hero-render-v7'
ENV={'ALI_HERO_FPS':'60','ALI_HERO_REQUIRE_GPU':'1','ALI_HERO_DEVICE':'OPTIX','ALI_HERO_SAMPLES':'32','ALI_HERO_FAST_EXIT':'1'}

@app.function(image=image,gpu='L40S',cpu=4,memory=12288,timeout=900,volumes={'/data':volume},env=ENV)
def preflight():
    import subprocess,shutil
    results={}
    for mode in ['preview','audit']:
        root=Path('/tmp')/mode;root.mkdir(exist_ok=True)
        env={**os.environ,'ALI_HERO_RENDER_DIR':str(root)}
        with (root/f'{mode}.log').open('w') as log:
            subprocess.run(['python','/opt/hero/render-hero.py','--',mode,'768'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=700)
        dest=Path('/data')/mode;dest.mkdir(exist_ok=True)
        for file in root.iterdir():
            if file.is_file():shutil.copy2(file,dest/file.name)
        if mode=='audit':results=json.loads((root/'geometry-audit.json').read_text())
        volume.commit()
    return results

@app.function(image=image,gpu='L40S',cpu=4,memory=12288,timeout=1800,max_containers=4,volumes={'/data':volume},env=ENV)
def render_chunk(bounds):
    import subprocess,shutil,time
    start,end=bounds;root=Path(f'/tmp/hero-{start:04d}');root.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'ALI_HERO_RENDER_DIR':str(root),'ALI_HERO_START':str(start),'ALI_HERO_END':str(end)}
    t=time.monotonic()
    with (root/'render.log').open('w') as log:
        subprocess.run(['python','/opt/hero/render-hero.py','--','chunk','768'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    # Different containers write only their own frame names; commit after each
    # complete chunk, then the encoding function reloads the unified snapshot.
    out=Path('/data/final');(out/'frames').mkdir(parents=True,exist_ok=True);(out/'orb-mask').mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    frames=list((root/'frames').glob('frame_*.png'));assert len(frames)==end-start+1
    for directory in ['frames','orb-mask']:
        for file in (root/directory).glob('*.png'):shutil.copy2(file,out/directory/file.name)
    shutil.copy2(root/'render.log',out/'logs'/f'chunk-{start:04d}.log')
    if start==1:
        shutil.copy2(root/'render-manifest.json',out/'render-manifest.json')
        shutil.copy2(root/'chrome-orbit.blend',out/'chrome-orbit.blend')
        shutil.copy2('/opt/hero/render-hero.py',out/'render-source.py')
    volume.commit()
    return {'start':start,'end':end,'frames':len(frames),'seconds':round(time.monotonic()-t,2),'gpu':'L40S'}

@app.function(image=image,cpu=8,memory=12288,timeout=1800,volumes={'/data':volume})
def encode():
    import importlib.util,subprocess,hashlib
    import numpy as np
    from PIL import Image,ImageFilter
    volume.reload();root=Path('/data/final');frames=sorted((root/'frames').glob('frame_*.png'));assert len(frames)==1200
    masks=sorted((root/'orb-mask').glob('mask_*.png'));assert len(masks)==1200
    spec=importlib.util.spec_from_file_location('hero_encode','/opt/hero/encode-hero.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from concurrent.futures import ThreadPoolExecutor
    # Grade independent frames on local scratch, avoiding serial Volume writes.
    # Screen and grain are deterministic, so scheduling cannot alter the finish.
    graded=Path('/tmp/hero-graded');graded.mkdir(exist_ok=True)
    report={'frames':1200,'fps':60,'seconds':20,'unique_frames':0,'alpha_corners':0,'bounds':[768,768,0,0]}
    def grade(pair):
        n,file=pair;assert file.name==f'frame_{n:04d}.png'
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        im=Image.open(file).convert('RGBA');alpha=im.getchannel('A');box=alpha.getbbox()
        assert all(alpha.getpixel(xy)==0 for xy in [(0,0),(767,0),(0,767),(767,767)])
        pixels=module.screenprint(np.array(im));mask=np.array(Image.open(root/'orb-mask'/f'mask_{n:04d}.png').convert('L'))
        # Equivalent to Pillow MinFilter(7), verified pixel-for-pixel in cloud.
        padded=np.pad(mask,3,mode='edge');horizontal=np.minimum.reduce([padded[:,i:i+768] for i in range(7)])
        eroded=np.minimum.reduce([horizontal[i:i+768] for i in range(7)])
        rim=(mask.astype(np.float32)-eroded.astype(np.float32))/255
        rgb=pixels[:,:,:3].astype(np.float32);lum=rgb[:,:,0]*.2126+rgb[:,:,1]*.7152+rgb[:,:,2]*.0722
        strength=rim*.65*np.clip((225-lum)/110,0,1)
        shifted=rgb.copy();shifted[:,:,0]=np.roll(rgb[:,:,0],2,axis=1);shifted[:,:,1]=np.roll(rgb[:,:,1],-2,axis=1);shifted[:,:,2]=np.roll(rgb[:,:,2],-2,axis=1)
        pixels[:,:,:3]=np.clip(rgb*(1-strength[:,:,None])+shifted*strength[:,:,None],0,255).astype(np.uint8);pixels[pixels[:,:,3]==0,:3]=0
        Image.fromarray(pixels).save(graded/file.name,compress_level=1)
        return digest,box
    with ThreadPoolExecutor(max_workers=6) as pool:
        records=list(pool.map(grade,enumerate(frames,1)))
    report['unique_frames']=len({digest for digest,box in records});assert report['unique_frames']==1200
    report['bounds']=[min(box[0] for _,box in records),min(box[1] for _,box in records),max(box[2] for _,box in records),max(box[3] for _,box in records)]
    out=root/'media';out.mkdir(exist_ok=True);Image.open(graded/'frame_0001.png').save(out/'hero-final-poster.webp',quality=94,method=6)
    report['clips']={}
    for stem,size,bitrate,maxrate,budget in [('hero-final',768,1200000,1600000,7000000),('hero-final-mobile',512,600000,800000,3500000)]:
        webm=out/f"{stem.replace('hero-final','hero-lean')}.webm"
        common=['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','60','-i',str(graded/'frame_%04d.png'),'-frames:v','1200','-vf',f'scale={size}:{size}:flags=lanczos','-an']
        subprocess.run(common+['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v',str(bitrate),'-maxrate',str(maxrate),'-bufsize',str(maxrate*2),'-crf','38','-auto-alt-ref','0','-row-mt','1','-threads','4','-cpu-used','3',str(webm)],check=True)
        # The only local operation later is macOS HEVC-alpha packaging from
        # these already-rendered/graded pixels; all 3D rendering stays on Modal.
        subprocess.run(common+['-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','16','-threads','4',str(out/f'{stem}-prores.mov')],check=True)
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(webm)]))
        assert data['streams'][0]['r_frame_rate']=='60/1' and data['streams'][0]['nb_read_frames']=='1200';assert webm.stat().st_size<=budget, 'Browser export exceeds download budget';data['bytes']=webm.stat().st_size;report['clips'][webm.stem]=data
    (root/'raster-media-audit.json').write_text(json.dumps(report,indent=2));volume.commit();return report

@app.local_entrypoint()
def main(mode:str='preview'):
    LOCAL.mkdir(parents=True,exist_ok=True)
    state=LOCAL/'notebook-state.json'
    if mode=='preflight':
        report=preflight.remote();(LOCAL/'geometry-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    elif mode=='preview':
        import secrets
        token=secrets.token_urlsafe(32)
        notebook_app=modal.App.lookup('ali-hero-notebook',create_if_missing=True)
        sandbox=modal.Sandbox.create('jupyter','lab','--no-browser','--allow-root','--ip=0.0.0.0','--port=8888','--ServerApp.root_dir=/data','--ServerApp.shutdown_no_activity_timeout=3600',
            app=notebook_app,image=image,gpu='L40S',cpu=4,memory=12288,timeout=3600,encrypted_ports=[8888],volumes={'/data':volume},secrets=[modal.Secret.from_dict({'JUPYTER_TOKEN':token})],env=ENV)
        tunnel=sandbox.tunnels()[8888]
        # Keep the notebook authentication URL in a private local file, never
        # in the repository, dashboard log output or a published website.
        access=LOCAL/'notebook-access.txt';access.write_text(tunnel.url+'/?token='+token+'\n');access.chmod(0o600)
        state.write_text(json.dumps({'sandbox_id':sandbox.object_id,'gpu':'L40S','url':tunnel.url,'timeout_seconds':3600},indent=2))
        process=sandbox.exec('bash','-lc','mkdir -p /data/preview; ALI_HERO_RENDER_DIR=/data/preview python /opt/hero/render-hero.py -- preview 768 > /data/preview/preview.log 2>&1',timeout=600)
        assert process.wait()==0,'Cloud preview failed; inspect notebook logs.'
        audit=sandbox.exec('bash','-lc','mkdir -p /data/audit; ALI_HERO_RENDER_DIR=/data/audit python /opt/hero/render-hero.py -- audit 768 > /data/audit/audit.log 2>&1',timeout=600)
        assert audit.wait()==0,'Cloud geometry audit failed; full rendering stopped.'
        sandbox.exec('sync','/data').wait()
        print('Cloud notebook preview and geometry audit completed. Notebook state:',state)
    elif mode=='render':
        bounds=[(1,300),(301,600),(601,900),(901,1200)]
        reports=list(render_chunk.map(bounds));(LOCAL/'cloud-render-report.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
    elif mode=='encode':
        report=encode.remote();(LOCAL/'raster-media-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    elif mode=='stop-notebook':
        if state.exists():
            sandbox=modal.Sandbox.from_id(json.loads(state.read_text())['sandbox_id']);sandbox.terminate();print('Notebook GPU stopped.')
    else:raise ValueError('Mode must be preflight, preview, render, encode or stop-notebook.')
