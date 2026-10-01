(() => {
 'use strict';
 const scriptElement = document.currentScript || [...document.scripts].find(script => /hero-video\.js(?:[?#]|$)/i.test(script.src));
 const scriptUrl = scriptElement?.src || location.href;

 const initialize = () => {
  const video = document.querySelector('video[data-hero-video]');
  const frame = video?.closest('.hero-video-frame');
  if (!video || !frame) return;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobileAsset = window.innerWidth <= 700;
  const userAgent = navigator.userAgent || '';
  const safariLike = (navigator.vendor === 'Apple Computer, Inc.' || /Safari/i.test(userAgent))
   && !/(?:Chrome|Chromium|CriOS|Firefox|FxiOS|Edg(?:A|iOS)?|Edge|OPR|Opera)/i.test(userAgent);
  const ios = /iPad|iPhone|iPod/i.test(userAgent)
   || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  let inViewport = false;
  let sourcesAdded = false;
  let failed = false;
  let attempt = 0;

  video.autoplay = false;
  video.loop = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = 'none';
  video.setAttribute('muted', '');
  video.setAttribute('playsinline', '');

  const allowed = () => !reduced.matches
   && !document.hidden
   && !document.documentElement.classList.contains('motion-paused')
   && !document.body?.classList.contains('motion-paused')
   && inViewport
   && !failed;

  const addSources = () => {
   if (sourcesAdded) return true;
   sourcesAdded = true;
   const stem = mobileAsset ? 'hero-rose-mobile' : 'hero-rose';
   const hevc = 'video/quicktime; codecs="hvc1"';
   const hevcSupported = video.canPlayType('video/mp4; codecs="hvc1"') !== '';
   const candidates = safariLike || ios
    ? (hevcSupported ? [[`${stem}.mov`, hevc]] : [])
    : [[`${stem}.webm`, 'video/webm; codecs="vp9"']];
   if (!candidates.length) {
    failed = true;
    return false;
   }
   const assetBase = new URL('assets/', new URL('.', scriptUrl));
   candidates.forEach(([path, type]) => {
    const source = document.createElement('source');
    source.src = new URL(path, assetBase).href;
    source.type = type;
    video.append(source);
   });
   video.load();
   return true;
  };

  const showPoster = () => {
   frame.classList.remove('video-ready');
  };

  const suspend = ({poster = false} = {}) => {
   attempt++;
   video.pause();
   if (poster) showPoster();
  };

  const start = () => {
   if (!allowed()) {
    suspend({poster: reduced.matches});
    return;
   }
   if (!video.paused || video.error) return;

   if (!addSources()) return;
   const currentAttempt = ++attempt;
   try {
    const result = video.play();
    if (result && typeof result.catch === 'function') {
     result.catch(() => {
      if (currentAttempt !== attempt) return;
      showPoster();
     });
    }
   } catch {
    if (currentAttempt === attempt) showPoster();
   }
  };

  video.addEventListener('playing', () => {
   if (!allowed()) {
    suspend({poster: reduced.matches});
    return;
   }
   frame.classList.add('video-ready');
  });
  video.addEventListener('error', () => {
   failed = true;
   suspend({poster: true});
  });

  const syncMotion = () => {
   if (reduced.matches) suspend({poster: true});
   else if (allowed()) start();
   else suspend();
  };

  const motionObserver = new MutationObserver(syncMotion);
  motionObserver.observe(document.documentElement, {attributes: true, attributeFilter: ['class']});
  if (document.body) motionObserver.observe(document.body, {attributes: true, attributeFilter: ['class']});
  reduced.addEventListener('change', syncMotion);
  document.addEventListener('visibilitychange', syncMotion);

  if ('IntersectionObserver' in window) {
   const visibilityObserver = new IntersectionObserver(entries => {
    const entry = entries[entries.length - 1];
    inViewport = Boolean(entry?.isIntersecting);
    syncMotion();
   });
   visibilityObserver.observe(frame);
  } else {
   const checkViewport = () => {
    const bounds = frame.getBoundingClientRect();
    inViewport = bounds.bottom > 0 && bounds.top < window.innerHeight
     && bounds.right > 0 && bounds.left < window.innerWidth;
    syncMotion();
   };
   window.addEventListener('scroll', checkViewport, {passive: true});
   window.addEventListener('resize', checkViewport, {passive: true});
   checkViewport();
  }

  syncMotion();
 };

 if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize, {once: true});
 } else {
  initialize();
 }
})();
