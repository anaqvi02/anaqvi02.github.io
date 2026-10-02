(() => {
const videos=[...document.querySelectorAll('video')],button=document.querySelector('#toggle'),status=document.querySelector('#status');
const safari=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1)||(navigator.vendor==='Apple Computer, Inc.'&&!/Chrome|Chromium|CriOS|Firefox|FxiOS|Edg|Opera|OPR/.test(navigator.userAgent));
const mobile=innerWidth<=700;let loaded=false,generation=0;
const ready=v=>v.readyState>=3?Promise.resolve():new Promise((resolve,reject)=>{
const cleanup=()=>{clearTimeout(timer);v.removeEventListener('canplay',ok);v.removeEventListener('error',fail);};
const ok=()=>{cleanup();resolve();},fail=()=>{cleanup();reject(new Error('Media unavailable'));};
const timer=setTimeout(fail,20000);v.addEventListener('canplay',ok,{once:true});v.addEventListener('error',fail,{once:true});
});
const pause=()=>{generation++;videos.forEach(v=>v.pause());button.textContent='Play comparison';button.setAttribute('aria-pressed','false');};
button.addEventListener('click',async()=>{
if(button.getAttribute('aria-pressed')==='true'){pause();return;}
const attempt=++generation;status.textContent='';button.disabled=true;
try {
if(!loaded){videos.forEach(v=>{v.preload='auto';v.src=`../assets/hero-halftone-${v.dataset.fps}${mobile?'-mobile':''}.${safari?'mov':'webm'}`;v.load();});loaded=true;}
await Promise.all(videos.map(ready));if(attempt!==generation)return;
videos.forEach(v=>{v.currentTime=0;v.playbackRate=1;});await Promise.all(videos.map(v=>v.play()));
if(attempt!==generation){videos.forEach(v=>v.pause());return;}
button.textContent='Pause comparison';button.setAttribute('aria-pressed','true');
} catch {loaded=false;pause();status.textContent='Playback unavailable. The stills show the matching print finish.';} finally {button.disabled=false;}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>{if(e.matches)pause();});
})();
