(() => {
 'use strict';
 const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
 const motion = document.querySelector('.motion-button');
 const statusUrl = new URL('status.json', document.currentScript.src);
 let requestedPause = false;
 try { requestedPause = localStorage.getItem('ali-motion-paused') === 'true'; } catch { /* Storage is optional. */ }
 const setMotion = paused => {
  const effectivePause = reduced.matches || paused;
  document.documentElement.classList.toggle('motion-paused', effectivePause);
  document.body.classList.toggle('motion-paused', effectivePause);
  if (!motion) return;
  motion.setAttribute('aria-pressed', String(effectivePause));
  motion.disabled = reduced.matches;
  motion.textContent = reduced.matches ? 'Motion reduced' : effectivePause ? 'Resume motion' : 'Pause motion';
 };
 setMotion(requestedPause);
 motion?.addEventListener('click', () => {
  requestedPause = !requestedPause;
  try { localStorage.setItem('ali-motion-paused', String(requestedPause)); } catch { /* Storage is optional. */ }
  setMotion(requestedPause);
 });
 reduced.addEventListener('change', () => setMotion(requestedPause));
 // Automatic suspension is independent of the user's saved motion preference.
 const syncVisibility = () => document.documentElement.classList.toggle('motion-background', document.hidden);
 document.addEventListener('visibilitychange', syncVisibility);
 syncVisibility();
 // Content remains visible without JavaScript; each arrival animates only once.
 if ('IntersectionObserver' in window) {
  const arrivals = new IntersectionObserver(entries => {
   entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    if (!document.body.classList.contains('motion-paused')) entry.target.classList.add('is-entering');
    arrivals.unobserve(entry.target);
   });
  }, {threshold: .12});
  document.querySelectorAll('.reveal, .dossier-chapter').forEach(node => arrivals.observe(node));
  const ambientMotion = new IntersectionObserver(entries => {
   entries.forEach(entry => entry.target.classList.toggle('motion-offscreen', !entry.isIntersecting));
  });
  document.querySelectorAll('.hero-art, .hero-proof, .work-section .project-art, .about-section, .contact-section, .project-header, .dossier-summary').forEach(node => ambientMotion.observe(node));
  document.addEventListener('projectsloaded', () => {
   document.querySelectorAll('[data-project-gallery] .reveal').forEach(node => arrivals.observe(node));
   document.querySelectorAll('[data-project-gallery] .project-art').forEach(node => ambientMotion.observe(node));
  });
 }
 // Keep the reading menu aligned with the section actually in view.
 const readingNav = document.querySelector('.dossier-nav nav');
 if (readingNav) {
  const chapters = [...readingNav.querySelectorAll('a[href^="#"]')].map(link => ({
   link, section: document.getElementById(link.getAttribute('href').slice(1))
  })).filter(item => item.section);
  const markReadingPosition = () => {
   const boundary = Math.min(160, innerHeight * .25);
   let current = chapters[0];
   chapters.forEach(item => { if (item.section.getBoundingClientRect().top <= boundary) current = item; });
   chapters.forEach(item => {
    if (item === current) item.link.setAttribute('aria-current', 'location');
    else item.link.removeAttribute('aria-current');
   });
  };
  let readingFrame = null;
  const scheduleReadingPosition = () => {
   if (readingFrame !== null) return;
   readingFrame = requestAnimationFrame(() => { readingFrame = null; markReadingPosition(); });
  };
  window.addEventListener('scroll', scheduleReadingPosition, {passive: true});
  window.addEventListener('resize', scheduleReadingPosition);
  document.fonts?.ready.then(scheduleReadingPosition);
  markReadingPosition();
 }
 // Progress comes from the project's current status file and refreshes without inventing movement.
 if (document.querySelector('[data-progress-value], [data-personal-status]')) {
  // An unavailable ETA helper must not block independently valid progress.
  const readEta = deadline => {
   try { return typeof projectEta === 'function' ? projectEta(deadline) : null; }
   catch { return null; }
  };
  const updateEta = () => document.querySelectorAll('[data-progress-eta]').forEach(node => {
   const eta = readEta(node.dataset.deadline);
   if (eta) node.textContent = 'ETA / ' + eta;
  });
  const updateProgress = async () => {
   if (document.hidden) return;
   updateEta();
   try {
    const response = await fetch(statusUrl, {cache:'no-store'});
    if (!response.ok) return;
    const status = await response.json();
    if (status.project !== 'mtdi') return;
    // Personal copy updates independently of the project's numeric progress.
    if (typeof status.personal_status === 'string') {
     const personal = status.personal_status.trim();
     if (personal && personal.length <= 80) document.querySelectorAll('[data-personal-status]').forEach(node => { node.textContent = personal; });
    }
    if (!Number.isFinite(status.completion) || status.completion < 0 || status.completion > 100) return;
    document.querySelectorAll('[data-progress-value]').forEach(node => {
     node.replaceChildren(document.createTextNode(String(status.completion)));
     const suffix = document.createElement('span'); suffix.textContent = '%'; node.appendChild(suffix);
    });
    document.querySelectorAll('.status-meter').forEach(meter => {
     meter.setAttribute('aria-valuenow', String(status.completion));
     meter.querySelector('span').style.width = status.completion + '%';
    });
    if (readEta(status.deadline)) document.querySelectorAll('[data-progress-eta]').forEach(node => { node.dataset.deadline = status.deadline; });
    updateEta();
   } catch { /* The authored status remains readable if a refresh is unavailable. */ }
  };
  updateProgress(); setInterval(updateProgress,60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) updateProgress(); });
 }
})();
