"""Encode compact browser clips locally from the ungraded FFV1 master.
No Blender rendering; the 16-bit 60fps source is never modified.
python3 tools/encode-stella.py /path/hero-stella-v11-lossless.mkv --output-dir assets
"""
from pathlib import Path
import argparse,subprocess,json,hashlib
import numpy as np
from PIL import Image

def finish(pixels):
    # A fine fixed screen in purple shadows, no random film grain.
    h,w=pixels.shape[:2];rgb=pixels[:,:,:3].astype(np.float32)
    y,x=np.indices((h,w));period=max(3,round(w/192))
    u=(x+y)/np.sqrt(2);v=(y-x)/np.sqrt(2)
    shade=np.clip((220-(rgb[:,:,0]*.2126+rgb[:,:,1]*.7152+rgb[:,:,2]*.0722))/170,0,1)
    radius=period*(.10+.25*shade)
    dots=(((u%period-period/2)**2+(v%period-period/2)**2)<radius**2)
    violet=np.clip((rgb[:,:,2]-rgb[:,:,1])/30,0,1)
    ink=dots*shade*violet*.18
    pixels[:,:,:3]=np.clip(rgb*(1-ink[:,:,None])+dots[:,:,None]*shade[:,:,None]*violet[:,:,None]*np.array([1,0,3]),0,255).astype(np.uint8)
    pixels[pixels[:,:,3]==0,:3]=0
    return pixels

def main(master,output,crf):
    output.mkdir(parents=True,exist_ok=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,pix_fmt:format=duration','-of','json',str(master)]))
    s=probe['streams'][0];assert s['width']==1024 and s['height']==1024 and s['r_frame_rate']=='60/1' and s['pix_fmt']=='gbrap16le'
    report={'source':master.name,'source_sha256':hashlib.file_digest(master.open('rb'),'sha256').hexdigest(),'finish':'fine halftone on violet surfaces at 18% ink; no grain','clips':{}}
    for size,quality,bitrate in [(768,crf,1100000),(512,crf+2,450000)]:
        stem='hero-stella-v11'+('-mobile' if size==512 else '')
        dest=output/f'{stem}.webm'
        decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(master),'-vf',f'scale={size}:{size}:flags=lanczos','-pix_fmt','rgba','-f','rawvideo','-'],stdout=subprocess.PIPE)
        encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{size}x{size}','-r','60','-i','-','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v',str(bitrate),'-maxrate',str(bitrate*2),'-crf',str(quality),'-auto-alt-ref','0','-row-mt','1','-threads','6','-cpu-used','2',str(dest)],stdin=subprocess.PIPE)
        count=0
        try:
            while True:
                raw=decoder.stdout.read(size*size*4)
                if not raw:break
                assert len(raw)==size*size*4
                pixels=finish(np.frombuffer(raw,dtype=np.uint8).reshape(size,size,4).copy())
                assert all(pixels[y,x,3]==0 for y,x in [(0,0),(0,-1),(-1,0),(-1,-1)])
                if count==0 and size==768:
                    Image.fromarray(pixels).save(output/'hero-stella-v11-poster.webp',quality=95,method=6)
                    Image.fromarray(pixels).save(output/'hero-stella-v11-encoding-reference.png')
                encoder.stdin.write(pixels.tobytes());count+=1
            encoder.stdin.close();assert encoder.wait()==0 and decoder.wait()==0 and count==1200
        finally:
            if decoder.poll() is None:decoder.kill()
            if encoder.poll() is None:encoder.kill()
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,r_frame_rate,nb_read_frames:stream_tags=ALPHA_MODE:format=duration','-of','json',str(dest)]))
        stream=data['streams'][0];assert stream['nb_read_frames']=='1200' and stream['r_frame_rate']=='60/1' and stream['tags'].get('alpha_mode')=='1'
        data['bytes']=dest.stat().st_size;data['crf']=quality;data['target_bitrate']=bitrate;report['clips'][stem]=data
        print('Encoded',stem,dest.stat().st_size,'bytes',flush=True)
    (output/'hero-stella-v11-encode-report.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('master',type=Path);parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--crf',type=int,default=34)
    args=parser.parse_args();main(args.master,args.output_dir,args.crf)
