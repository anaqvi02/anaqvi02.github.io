"""Create HEVC-alpha Safari equivalents of the verified browser exports.
Usage: python3 tools/package-stella-safari.py /path/to/encoded-clips [--study]
All large intermediate files are temporary and removed automatically.
"""
from pathlib import Path
import subprocess,tempfile,json,sys
root=Path(sys.argv[1]).resolve();reports={};study='--study' in sys.argv[2:]
clips=[('glass-stella-study',512,600000)] if study else [('hero-stella-v12',768,1400000),('hero-stella-v12-mobile',512,650000)]
mobile_only='--mobile-only' in sys.argv[2:]
if mobile_only:
    clips=[clip for clip in clips if clip[1]==512]
    previous=root/('safari-study-audit.json' if study else 'safari-audit.json')
    if previous.exists():reports=json.loads(previous.read_text())
fps,frames=(12,240) if study else (60,1200)
with tempfile.TemporaryDirectory(prefix='safari-',dir=root) as temp:
    scratch=Path(temp);binary=scratch/'encode-alpha'
    subprocess.run(['swiftc','-module-cache-path',str(scratch/'swift-cache'),str(Path(__file__).with_name('encode-alpha.swift')),'-o',str(binary)],check=True)
    for stem,size,bitrate in clips:
        source=root/f'{stem}.webm';compatible=scratch/'compatible.mov'
        try:
            subprocess.run(['ffmpeg','-v','error','-y','-c:v','libvpx-vp9','-i',str(source),'-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','8','-threads','4',str(compatible)],check=True)
            dest=root/f'{stem}.mov'
            subprocess.run([str(binary),str(compatible),str(dest),str(size),str(bitrate)],check=True)
            data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(dest)]))
            s=data['streams'][0];assert s['width']==size and s['height']==size and s['r_frame_rate']==f'{fps}/1' and s['nb_read_frames']==str(frames)
            data['bytes']=dest.stat().st_size;reports[stem]=data
        finally:
            compatible.unlink(missing_ok=True)
            # AVFoundation can leave temporary safe-save copies beside the export.
            for sidecar in root.glob(f"{stem}.mov.sb-*"):sidecar.unlink()
(root/('safari-study-audit.json' if study else 'safari-audit.json')).write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
