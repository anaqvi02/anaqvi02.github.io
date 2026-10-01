"""Encode the offline Blender frames; FFmpeg, Pillow, NumPy and macOS avconvert.

Usage: python3 tools/encode-hero.py /absolute/path/to/render-output
The still and four browser/size variants are written to assets/.
"""
from pathlib import Path
import subprocess, sys, shutil
from PIL import Image
import numpy as np

root = Path(sys.argv[1]).resolve()
assets = Path(__file__).resolve().parent.parent / 'assets'
frames = sorted((root / 'frames').glob('frame_*.png'))
if len(frames) != 384:
    raise SystemExit(f'Expected 384 frames, found {len(frames)}. Do not encode an incomplete loop.')
ffmpeg = shutil.which('ffmpeg')
if not ffmpeg:
    raise SystemExit('FFmpeg is required.')
graded = root / 'graded'
graded.mkdir(exist_ok=True)
noise = np.random.default_rng(48).normal(0, .65, (768,768,1))
for frame in frames:
    pixels = np.array(Image.open(frame).convert('RGBA'))
    # A fixed fine print grain, matching at the loop seam. Alpha stays untouched.
    pixels[:,:,:3] = np.clip(pixels[:,:,:3].astype(float) + noise,0,255).astype(np.uint8)
    pixels[pixels[:,:,3] == 0,:3] = 0
    Image.fromarray(pixels).save(graded / frame.name)
Image.open(graded/'frame_0001.png').save(assets/'hero-orbit-poster.webp',quality=94,method=6)

def run(args):
    subprocess.run(args,check=True)

for stem,size,crf in [('hero-orbit',768,29),('hero-orbit-mobile',512,30)]:
    common = [ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','24',
              '-start_number','1','-i',str(graded/'frame_%04d.png'),'-frames:v','384',
              '-vf',f'scale={size}:{size}:flags=lanczos','-an']
    run(common+['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf',str(crf),
                '-auto-alt-ref','0','-row-mt','1','-threads','4','-cpu-used','4',
                str(assets/f'{stem}.webm')])
    if shutil.which('avconvert'):
        intermediate = root/f'{stem}-prores.mov'
        run(common+['-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le',
                    '-alpha_bits','16',str(intermediate)])
        if shutil.which('swift'):
            run(['swift',str(Path(__file__).with_name('encode-alpha.swift')),str(intermediate),
                 str(assets/f'{stem}.mov'),str(size),str(1800000 if size==768 else 850000)])
        else:
            run(['avconvert','--source',str(intermediate),'--preset',
                 'PresetHEVCHighestQualityWithAlpha','--output',str(assets/f'{stem}.mov'),'--replace'])
        for temporary in assets.glob(f'{stem}.mov.sb-*'):
            temporary.unlink()
    else:
        print('HEVC-alpha requires macOS; existing MOV variants were retained.')
    print('Encoded',stem,flush=True)
