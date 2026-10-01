"""Encode the offline Blender frames; FFmpeg, Pillow, NumPy and macOS avconvert.

Usage: python3 tools/encode-hero.py /absolute/path/to/render-output
The still and four browser/size variants are written to assets/.
"""
from pathlib import Path
import subprocess, sys, shutil
from PIL import Image
import numpy as np

def apply_print_finish(pixels):
    """Apply fixed-screen print grain and a restrained purple halftone tint."""
    height, width = pixels.shape[:2]
    rgb = pixels[:,:,:3].astype(np.float32)
    alpha = pixels[:,:,3]

    # Grain remains deterministic at the loop seam and scales to any render size.
    grain = np.random.default_rng(48).normal(0, .65, (height, width, 1))

    # One tiny dot per screen-cell: 4 px spacing at the 768 px master size.
    period = max(2, round(min(width, height) / 192))
    y, x = np.indices((height, width))
    center = period // 2
    dots = ((x % period == center) & (y % period == center)).astype(np.float32)

    luminance = rgb[:,:,0] * .2126 + rgb[:,:,1] * .7152 + rgb[:,:,2] * .0722
    shadows_and_midtones = np.clip((236 - luminance) / 68, 0, 1)
    purple_tint = np.array([1.0, .35, 2.0], dtype=np.float32)
    tint = dots[:,:,None] * shadows_and_midtones[:,:,None] * purple_tint

    result = pixels.copy()
    result[:,:,:3] = np.clip(rgb + grain + tint, 0, 255).astype(np.uint8)
    result[alpha == 0, :3] = 0
    return result


def main(root):
    assets = Path(__file__).resolve().parent.parent / 'assets'
    frames = sorted((root / 'frames').glob('frame_*.png'))
    if len(frames) != 384:
        raise SystemExit(f'Expected 384 frames, found {len(frames)}. Do not encode an incomplete loop.')
    if any(frame.name != f'frame_{number:04d}.png' for number, frame in enumerate(frames, 1)):
        raise SystemExit('Frames must form the uninterrupted sequence frame_0001.png to frame_0384.png.')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('FFmpeg is required.')
    graded = root / 'graded'
    graded.mkdir(exist_ok=True)
    for frame in frames:
        pixels = np.array(Image.open(frame).convert('RGBA'))
        if any(pixels[y, x, 3] != 0 for y, x in [(0, 0), (0, -1), (-1, 0), (-1, -1)]):
            raise SystemExit(f'{frame.name} has an opaque corner. Preserve transparent film and compositor alpha.')
        Image.fromarray(apply_print_finish(pixels)).save(graded / frame.name)
    Image.open(graded/'frame_0001.png').save(assets/'hero-mercury-poster.webp',quality=94,method=6)

    def run(args):
        subprocess.run(args,check=True)

    for stem,size,crf in [('hero-mercury',768,29),('hero-mercury-mobile',512,30)]:
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


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
