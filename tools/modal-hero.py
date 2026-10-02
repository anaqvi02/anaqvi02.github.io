"""Cloud-only Stella hero render. No local 3D rendering.
modal run tools/modal-hero.py --mode preflight
modal run --detach tools/modal-hero.py --mode render
modal run tools/modal-hero.py --mode master
The lossless master stays outside Git; browser encoding happens locally.
"""
from pathlib import Path
import json,os,modal
HERE=Path(__file__).resolve().parent
app=modal.App('ali-hero-stella-v11')
volume=modal.Volume.from_name('ali-hero-final-20261001',create_if_missing=True)
image=(modal.Image.debian_slim(python_version='3.11')
       .apt_install('xorg','libxkbcommon0','libegl1','ffmpeg')
       .uv_pip_install('bpy==4.5.0','numpy','pillow')
       .add_local_file(HERE/'render-hero.py','/opt/hero/render-hero.py',copy=True))
LOCAL=HERE.parent.parent/'hero-render-v11'
CLOUD=Path('/data/stella-v11')
SIZE=1024
ENV={'ALI_HERO_FPS':'60','ALI_HERO_REQUIRE_GPU':'1','ALI_HERO_DEVICE':'OPTIX','ALI_HERO_SAMPLES':'96','ALI_HERO_FAST_EXIT':'1'}

@app.function(image=image,gpu='L4',cpu=4,memory=12288,timeout=1200,volumes={'/data':volume},env=ENV)
def preflight():
    import subprocess,shutil
    report={}
    for mode in ['preview','gem-preview','audit']:
        root=Path('/tmp')/mode;root.mkdir(exist_ok=True)
        with (root/f'{mode}.log').open('w') as log:
            subprocess.run(['python','/opt/hero/render-hero.py','--',mode,str(SIZE)],env={**os.environ,'ALI_HERO_RENDER_DIR':str(root)},stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1000)
        dest=CLOUD/mode;dest.mkdir(parents=True,exist_ok=True)
        for file in root.iterdir():
            if file.is_file():shutil.copy2(file,dest/file.name)
        if mode=='audit':report=json.loads((root/'geometry-audit.json').read_text())
        volume.commit()
    return report

@app.function(image=image,gpu='L4',cpu=4,memory=12288,timeout=3600,max_containers=8,volumes={'/data':volume},env=ENV)
def render_chunk(bounds):
    import subprocess,shutil,time
    start,end=bounds;root=Path(f'/tmp/hero-{start:04d}');root.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'ALI_HERO_RENDER_DIR':str(root),'ALI_HERO_START':str(start),'ALI_HERO_END':str(end)}
    t=time.monotonic()
    with (root/'render.log').open('w') as log:
        subprocess.run(['python','/opt/hero/render-hero.py','--','chunk',str(SIZE)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    for directory in ['frames','orb-mask','logs']:(CLOUD/directory).mkdir(parents=True,exist_ok=True)
    frames=list((root/'frames').glob('frame_*.png'));assert len(frames)==end-start+1
    for directory in ['frames','orb-mask']:
        for file in (root/directory).glob('*.png'):shutil.copy2(file,CLOUD/directory/file.name)
    shutil.copy2(root/'render.log',CLOUD/'logs'/f'chunk-{start:04d}.log')
    if start==1:
        for name in ['render-manifest.json','chrome-orbit.blend']:shutil.copy2(root/name,CLOUD/name)
        shutil.copy2('/opt/hero/render-hero.py',CLOUD/'render-source.py')
    volume.commit()
    return {'start':start,'end':end,'frames':len(frames),'seconds':round(time.monotonic()-t,2),'gpu':'L4'}

@app.function(image=image,cpu=8,memory=12288,timeout=3600,volumes={'/data':volume})
def master():
    import subprocess,hashlib
    volume.reload();frames=sorted((CLOUD/'frames').glob('frame_*.png'))
    assert len(frames)==1200 and all(p.name==f'frame_{i:04d}.png' for i,p in enumerate(frames,1))
    dest=CLOUD/'hero-stella-v11-lossless.mkv'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','60','-i',str(CLOUD/'frames/frame_%04d.png'),'-frames:v','1200','-an','-c:v','ffv1','-level','3','-coder','1','-context','1','-slicecrc','1','-pix_fmt','gbrap16le','-threads','8',str(dest)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames:format=duration','-of','json',str(dest)]))
    s=probe['streams'][0];assert s['codec_name']=='ffv1' and s['pix_fmt']=='gbrap16le' and s['width']==SIZE and s['height']==SIZE and s['r_frame_rate']=='60/1' and s['nb_read_frames']=='1200'
    # Compare decoded RGBA16 samples with their source PNGs: no quantization.
    exact=[]
    for n in [1,301,601,901,1200]:
        source=subprocess.check_output(['ffmpeg','-v','error','-i',str(frames[n-1]),'-frames:v','1','-pix_fmt','rgba64le','-f','rawvideo','-'])
        decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(dest),'-vf',f'select=eq(n\\,{n-1})','-frames:v','1','-pix_fmt','rgba64le','-f','rawvideo','-'])
        assert source==decoded,f'Lossless verification failed at frame {n}'
        exact.append(n)
    report={'master':dest.name,'bytes':dest.stat().st_size,'source_pixel_matches':exact,'sha256':hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),'probe':probe}
    (CLOUD/'master-audit.json').write_text(json.dumps(report,indent=2));volume.commit();return report

@app.local_entrypoint()
def main(mode:str='preflight'):
    LOCAL.mkdir(parents=True,exist_ok=True)
    if mode=='preflight':report=preflight.remote()
    elif mode=='render':
        report=[{'start':start,'end':min(start+149,1200),'call_id':render_chunk.spawn((start,min(start+149,1200))).object_id} for start in range(1,1201,150)]
    elif mode=='master':report={'call_id':master.spawn().object_id}
    else:raise ValueError('Mode must be preflight, render or master')
    (LOCAL/f'{mode}-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
