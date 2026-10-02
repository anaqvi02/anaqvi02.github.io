"""Create HEVC-alpha Safari equivalents of the verified browser exports.
Usage: python3 tools/package-stella-safari.py /path/to/encoded-clips
All large intermediate files are temporary and removed automatically.
"""
from pathlib import Path
import subprocess,tempfile,json,sys
root=Path(sys.argv[1]).resolve();reports={}
with tempfile.TemporaryDirectory(prefix='safari-',dir=root) as temp:
    scratch=Path(temp);binary=scratch/'encode-alpha'
    subprocess.run(['swiftc','-module-cache-path',str(scratch/'swift-cache'),str(Path(__file__).with_name('encode-alpha.swift')),'-o',str(binary)],check=True)
    for stem,size,bitrate in [('hero-stella-v11',768,1400000),('hero-stella-v11-mobile',512,650000)]:
        source=root/f'{stem}.webm';compatible=scratch/'compatible.mov'
        subprocess.run(['ffmpeg','-v','error','-y','-c:v','libvpx-vp9','-i',str(source),'-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','8','-threads','4',str(compatible)],check=True)
        dest=root/f'{stem}.mov'
        subprocess.run([str(binary),str(compatible),str(dest),str(size),str(bitrate)],check=True)
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(dest)]))
        s=data['streams'][0];assert s['width']==size and s['height']==size and s['r_frame_rate']=='60/1' and s['nb_read_frames']=='1200'
        data['bytes']=dest.stat().st_size;reports[stem]=data
        compatible.unlink()
(root/'safari-audit.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
