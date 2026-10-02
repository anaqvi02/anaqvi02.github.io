"""Package completed cloud ProRes pixels for Safari; never render 3D locally.
Usage: python3 tools/package-safari.py CLOUD_MEDIA_DIRECTORY
"""
from pathlib import Path
import json, re, subprocess, sys, tempfile

root=Path(sys.argv[1]).resolve()
assets=Path(__file__).resolve().parent.parent/'assets'
version=subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]
match=re.search(r'ffmpeg version (\d+)',version)
if not match or int(match[1])<8:
    raise SystemExit('Safari packaging requires FFmpeg 8 or newer for the tested ProRes alpha repack.')
reports={}
with tempfile.TemporaryDirectory(prefix='safari-package-',dir=root) as scratch:
    scratch=Path(scratch);binary=scratch/'encode-alpha'
    subprocess.run(['swiftc','-module-cache-path',str(scratch/'swift-cache'),str(Path(__file__).with_name('encode-alpha.swift')),'-o',str(binary)],check=True)
    for stem,size,bitrate in [('hero-final',512,850000),('hero-final-mobile',320,350000)]:
        source=root/f'{stem}-prores.mov';compatible=scratch/f'{stem}.mov'
        # FFmpeg decodes the cloud alpha correctly. Normalize its ProRes bitstream
        # to the 8-bit alpha that was verified against macOS AVFoundation.
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','8','-threads','4',str(compatible)],check=True)
        output=assets/f"hero-orb-v10{'-mobile' if size==320 else ''}.mov"
        subprocess.run([str(binary),str(compatible),str(output),str(size),str(bitrate)],check=True)
        report=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(output)]))
        stream=report['streams'][0]
        assert stream['r_frame_rate']=='60/1' and stream['nb_read_frames']=='1200' and float(report['format']['duration'])==20
        assert output.stat().st_size <= (5000000 if size==512 else 2000000), 'Safari export exceeds download budget'
        report['bytes']=output.stat().st_size;reports[output.stem]=report
        for temporary in assets.glob(f'{output.name}.sb-*'):temporary.unlink()
(root/'safari-media-audit.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Safari packages verified: 60fps, 1200 frames, 20 seconds.')
