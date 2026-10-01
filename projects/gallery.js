(() => {
 'use strict';
 const gallery = document.querySelector('[data-project-gallery]');
 if (!gallery) return;
 const manifestUrl = new URL(gallery.dataset.manifest, location.href);
 const fallback = new Map([...gallery.children].map(card => [card.dataset.project, card]));
 const loadGallery = async () => {
  try {
   const response = await fetch(manifestUrl);
   if (!response.ok) return;
   const files = await response.json();
   if (!Array.isArray(files) || !files.length || new Set(files).size !== files.length || !files.every(file => typeof file === 'string' && /^[a-z0-9-]+\.html$/.test(file))) return;
   const cards = await Promise.all(files.map(async file => {
    const id = file.slice(0, -5);
    try {
     const response = await fetch(new URL(file, manifestUrl));
     if (!response.ok) return fallback.get(id);
     const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
     const card = parsed.body.firstElementChild;
     if (parsed.body.children.length !== 1 || !card?.matches('article.project') || card.dataset.project !== id || card.querySelector('script,iframe,object,embed')) return fallback.get(id);
     return document.importNode(card, true);
    } catch { return fallback.get(id); }
   }));
   const available = cards.filter(Boolean);
   if (!available.length) return;
   // Updating background data must not displace an active keyboard target.
   if (gallery.contains(document.activeElement)) return;
   gallery.replaceChildren(...available);
   document.dispatchEvent(new Event('projectsloaded'));
  } catch { /* The complete static gallery remains usable offline or without data. */ }
 };
 loadGallery();
})();
