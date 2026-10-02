"""Bounded Modal previews for the nested glass/white Stella material study."""
from pathlib import Path
import os,json,modal
HERE=Path(__file__).resolve().parent
app=modal.App('ali-glass-stella-study-v12')
volume=modal.Volume.from_name('ali-hero-final-20261001')
image=(modal.Image.debian_slim(python_version='3.11').apt_install('xorg','libxkbcommon0','libegl1','ffmpeg').uv_pip_install('bpy==4.5.0','numpy','pillow').add_local_file(HERE/'render-hero.py','/opt/hero/render-hero.py',copy=True))
ENV={'ALI_HERO_FPS':'12','ALI_HERO_REQUIRE_GPU':'1','ALI_HERO_DEVICE':'OPTIX','ALI_HERO_SAMPLES':'128','ALI_HERO_FAST_EXIT':'1','ALI_HERO_CORE_STYLE':'glass'}
CLOUD=Path('/data/stella-glass-study-v12');LOCAL=HERE.parent.parent/'stella-glass-study-v12'
@app.function(image=image,gpu='L4',cpu=4,memory=12288,timeout=900,volumes={'/data':volume},env=ENV)
def stills():
    import subprocess,shutil
    root=Path('/tmp/glass-stills');root.mkdir(exist_ok=True)
    for mode in ['preview','gem-preview']:
        with (root/f'{mode}.log').open('w') as log:
            subprocess.run(['python','/opt/hero/render-hero.py','--',mode,'1024'],env={**os.environ,'ALI_HERO_RENDER_DIR':str(root)},stdout=log,stderr=subprocess.STDOUT,check=True)
    dest=CLOUD/'stills';dest.mkdir(parents=True,exist_ok=True)
    for file in root.glob('*'):
        if file.is_file():shutil.copy2(file,dest/file.name)
    volume.commit();return {'stills':[p.name for p in dest.glob('*.png')],'source_size':1024,'samples':128}
@app.function(image=image,gpu='L4',cpu=4,memory=12288,timeout=1800,max_containers=4,volumes={'/data':volume},env=ENV)
def frames(bounds):
    import subprocess,shutil
    start,end=bounds;root=Path(f'/tmp/glass-{start}');root.mkdir(exist_ok=True)
    with (root/'render.log').open('w') as log:
        subprocess.run(['python','/opt/hero/render-hero.py','--','chunk','512'],env={**os.environ,'ALI_HERO_RENDER_DIR':str(root),'ALI_HERO_START':str(start),'ALI_HERO_END':str(end)},stdout=log,stderr=subprocess.STDOUT,check=True)
    dest=CLOUD/'frames';dest.mkdir(parents=True,exist_ok=True)
    for file in (root/'frames').glob('*.png'):shutil.copy2(file,dest/file.name)
    volume.commit();return {'start':start,'end':end,'count':end-start+1}
@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/data':volume})
def encode():
    import subprocess
    volume.reload();files=sorted((CLOUD/'frames').glob('*.png'));assert len(files)==240
    out=CLOUD/'glass-stella-preview.webm'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(CLOUD/'frames/frame_%04d.png'),'-frames:v','240','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','600000','-crf','30','-auto-alt-ref','0','-row-mt','1','-cpu-used','2',str(out)],check=True)
    volume.commit();return {'bytes':out.stat().st_size,'fps':12,'frames':240,'duration_seconds':20}
@app.local_entrypoint()
def main(mode:str='stills'):
    LOCAL.mkdir(exist_ok=True)
    if mode=='stills':result=stills.remote()
    elif mode=='motion':result=[{'start':start,'call_id':frames.spawn((start,start+59)).object_id} for start in (1,61,121,181)]
    elif mode=='encode':result={'call_id':encode.spawn().object_id}
    else:raise ValueError(mode)
    (LOCAL/f'{mode}-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
