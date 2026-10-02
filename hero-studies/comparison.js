(() => {
 const videos = [...document.querySelectorAll('video')];
 const button = document.querySelector('#toggle');
 const status = document.querySelector('#status');
 const safari = /iPad|iPhone|iPod/.test(navigator.userAgent)
  || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  || (navigator.vendor === 'Apple Computer, Inc.' && !/Chrome|Chromium|CriOS|Firefox|FxiOS|Edg|Opera|OPR/.test(navigator.userAgent));
 const mobile = innerWidth <= 700;
 let loaded = false;
 let generation = 0;
 let objectUrls = [];

 const ready = video => video.readyState >= 3 ? Promise.resolve() : new Promise((resolve, reject) => {
  const cleanup = () => {
   clearTimeout(timer);
   video.removeEventListener('canplay', success);
   video.removeEventListener('error', failure);
  };
  const success = () => { cleanup(); resolve(); };
  const failure = () => { cleanup(); reject(new Error('Media unavailable')); };
  const timer = setTimeout(failure, 20000);
  video.addEventListener('canplay', success, {once: true});
  video.addEventListener('error', failure, {once: true});
 });

 const resetTime = video => new Promise(resolve => {
  if (video.currentTime === 0 && !video.seeking) { resolve(); return; }
  video.addEventListener('seeked', resolve, {once: true});
  video.currentTime = 0;
 });

 const pause = () => {
  generation++;
  videos.forEach(video => video.pause());
  button.textContent = 'Play comparison';
  button.setAttribute('aria-pressed', 'false');
 };

 const clearMedia = () => {
  videos.forEach(video => { video.removeAttribute('src'); video.load(); });
  objectUrls.forEach(url => URL.revokeObjectURL(url));
  objectUrls = [];
  loaded = false;
 };

 const loadPair = async () => {
  // Buffer both complete clips before playing: separate network stalls would
  // otherwise make one orbit run ahead and undermine the frame-rate comparison.
  const paths = videos.map(video => `../assets/hero-halftone-${video.dataset.fps}${mobile ? '-mobile' : ''}.${safari ? 'mov' : 'webm'}`);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
   const blobs = await Promise.all(paths.map(async path => {
    const response = await fetch(path, {signal: controller.signal});
    if (!response.ok) throw new Error('Media unavailable');
    return response.blob();
   }));
   blobs.forEach((blob, index) => {
    const video = videos[index];
    const url = URL.createObjectURL(blob);
    objectUrls.push(url);
    video.dataset.assetSrc = new URL(paths[index], location.href).href;
    video.preload = 'auto';
    video.src = url;
    video.load();
   });
   await Promise.all(videos.map(ready));
   loaded = true;
  } catch (error) {
   controller.abort();
   clearMedia();
   throw error;
  } finally { clearTimeout(timeout); }
 };

 button.addEventListener('click', async () => {
  if (button.getAttribute('aria-pressed') === 'true') { pause(); return; }
  const attempt = ++generation;
  status.textContent = loaded ? '' : 'Loading both clips…';
  button.disabled = true;
  try {
   if (!loaded) await loadPair();
   if (attempt !== generation) { status.textContent = ''; return; }
   videos.forEach(video => { video.pause(); video.playbackRate = 1; });
   await Promise.all(videos.map(resetTime));
   if (attempt !== generation) { status.textContent = ''; return; }
   await Promise.all(videos.map(video => video.play()));
   if (attempt !== generation) { videos.forEach(video => video.pause()); return; }
   status.textContent = '';
   button.textContent = 'Pause comparison';
   button.setAttribute('aria-pressed', 'true');
  } catch {
   pause();
   clearMedia();
   status.textContent = 'Playback unavailable. The stills show the matching print finish.';
  } finally { button.disabled = false; }
 });

 document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
 window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', event => { if (event.matches) pause(); });
})();
