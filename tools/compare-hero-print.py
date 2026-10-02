"""Compare native smooth playback with a 12fps screen-print interpretation.
Usage: python3 tools/compare-hero-print.py render-directory [output-directory]
Comparison files stay outside published assets unless explicitly copied there.
"""
from pathlib import Path
import json,sys,shutil,subprocess
import numpy as np
from PIL import Image

import importlib.util
_spec=importlib.util.spec_from_file_location('hero_encode',Path(__file__).with_name('encode-hero.py'))
_encoder=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_encoder)
screenprint=_encoder.screenprint

def main(root,out):
    manifest=json.loads((root/'render-manifest.json').read_text());fps=manifest['fps'];count=manifest['frames']
    assert fps%12==0,'Native fps must be divisible by 12 for exact decimation.'
    assets=Path(__file__).resolve().parent.parent/'assets';out.mkdir(parents=True,exist_ok=True)
    frames=root/'screenprint-frames';frames.mkdir(exist_ok=True)
    for index,source in enumerate(range(1,count+1,fps//12),1):
        pixels=np.array(Image.open(root/'frames'/f'frame_{source:04d}.png').convert('RGBA'))
        Image.fromarray(screenprint(pixels)).save(frames/f'frame_{index:04d}.png')
    Image.open(frames/'frame_0001.png').save(out/'screenprint-poster.webp',quality=94)
    subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'frame_%04d.png'),'-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','29','-auto-alt-ref','0','-row-mt','1','-threads','4','-cpu-used','4',str(out/'screenprint-12fps.webm')],check=True)
    shutil.copy2(assets/'hero-star.webm',out/'smooth-60fps.webm');shutil.copy2(assets/'hero-star-poster.webp',out/'smooth-poster.webp')
    if (assets/'hero-star.mov').exists():
        shutil.copy2(assets/'hero-star.mov',out/'smooth-60fps.mov')
        intermediate=root/'screenprint-prores.mov'
        subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'frame_%04d.png'),'-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','16',str(intermediate)],check=True)
        subprocess.run(['swift',str(Path(__file__).with_name('encode-alpha.swift')),str(intermediate),str(out/'screenprint-12fps.mov'),'768','1800000'],check=True)
        for temporary in out.glob('screenprint-12fps.mov.sb-*'):temporary.unlink()
    (out/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hero motion studies</title><style>body{margin:0;background:#f5f3ed;color:#292630;font-family:ui-monospace,monospace;padding:clamp(16px,3vw,40px)}h1{font-size:clamp(22px,3vw,36px);font-weight:500;margin:0 0 12px}p{font-size:14px;line-height:1.5;color:#68616d}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}figure{margin:0;border-top:2px solid #5e3bc4}figcaption{padding:15px 0;color:#5e3bc4}video{width:100%;display:block}button{background:#292630;color:#f5f3ed;border:0;padding:12px 20px;font:inherit;cursor:pointer;border-left:4px solid #af3047;margin:8px 0 24px}@media(max-width:700px){main{grid-template-columns:1fr}}</style><h1>Hero motion studies</h1><p>The same slow 20-second orbit, with two different finishes.</p><button type="button" id="toggle">Play comparison</button><main><figure><figcaption>60 fps · smooth chrome / fine purple grain</figcaption><video muted loop playsinline preload="metadata" poster="smooth-poster.webp" src="smooth-60fps.webm"></video></figure><figure><figcaption>12 fps · graphic motion / diagonal screen-print dots</figcaption><video muted loop playsinline preload="metadata" poster="screenprint-poster.webp" src="screenprint-12fps.webm"></video></figure></main><script>const videos=[...document.querySelectorAll('video')],button=document.querySelector('button');const safari=(/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.vendor==='Apple Computer, Inc.'&&!/Chrome|Chromium|CriOS|Firefox|FxiOS|Edg|Opera|OPR/.test(navigator.userAgent)));if(safari)videos.forEach(v=>v.src=v.getAttribute('src').replace('.webm','.mov'));let playing=false;button.onclick=async()=>{if(playing){videos.forEach(v=>v.pause());button.textContent='Play comparison';playing=false}else{videos.forEach(v=>v.currentTime=0);await Promise.all(videos.map(v=>v.play()));button.textContent='Pause comparison';playing=true}};</script></html>''')
    print('Comparison exported:',out,flush=True)

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve();main(root,Path(sys.argv[2]).resolve() if len(sys.argv)>2 else root/'comparison')
