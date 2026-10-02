# Ali Naqvi's portfolio

Plain static HTML, CSS, and JavaScript. Published at https://anaqvi02.github.io/. GitHub Pages serves the repository root from `main`. Serve the root for local previews (`python3 -m http.server 4175 --bind 127.0.0.1`). Relative links and data requests support deployment under a GitHub Pages project path.

## Adding projects to the gallery

Each project is an independent HTML card in `projects/items/`. `index.json` lists filenames in display order. The gallery loads these files at runtime; the grid has no fixed project count.

1. Copy an existing card to a new lowercase, hyphenated filename such as `new-project.html`.
2. Set its `data-project` to the matching filename stem, update its title, description, tags, repository and detail links, and customize its artwork. Keep one `article.project` per file and decorative artwork `aria-hidden`.
3. Add the filename to `items/index.json`. Card links resolve relative to the gallery page (`projects/index.html`), not the `items/` folder.
4. Run `node tools/sync-gallery.mjs` to refresh the static fallback. This preserves the complete gallery when JavaScript or data requests are unavailable.
5. Add a detail page if needed and preview narrow/desktop layouts before publishing.

Homepage selected work is curated separately; adding a gallery entry does not require changing the homepage. Data-load failures preserve available static cards. Motion controls and reduced-motion behavior also apply to loaded cards.

## Current status

Edit `personal_status` in `status.json` to change the hero’s Current status readout (up to 80 characters). It refreshes from that file alongside mtdi progress, once per minute while the page is visible. It keeps the authored text if the file is unavailable or the value is invalid; the homepage HTML is the no-JavaScript fallback.

## Offline chrome hero

The hero is a deterministic, pre-rendered 3D sculpture: three asymmetric folded chrome ribbons carry nine long swept needles around a smoked amethyst orb. The approved ribbon shape, camera and studio reflections stay intact. Inside the darker glass, a compact star has a continuously changing molten photosphere, curved coronal flares, a faint plasma atmosphere and small orbiting embers. Every energy feature stays inside the shell; star bloom is masked to the visible glass silhouette. The sculpture completes one calm turn per 20 seconds at 12fps with a diagonal halftone print finish and gentle local ribbon flow. No 3D renderer runs in the browser.

`tools/render-hero.py` creates the Blender scene and renders 1,200 transparent PNG frames at 768px and 60fps. Use Blender 4.5, with Metal acceleration when available:

```sh
blender --background --factory-startup --python tools/render-hero.py -- preview 768
blender --background --factory-startup --python tools/render-hero.py -- render 768
blender --background --factory-startup --python tools/render-hero.py -- audit 768
python3 tools/encode-hero.py work/hero-render screenprint
python3 tools/compare-hero-print.py work/hero-render
```

The audit checks all 1,201 poses for actual triangle intersections between ribbons, core containment and camera clearance, then verifies loop, thunder, cloud, and orb-rotation closure between frames 1 and 1,201. It writes the measurements to `geometry-audit.json`. Render intermediates default to the ignored `work/hero-render/` directory. Set `ALI_HERO_RENDER_DIR` to use another output directory. Encoding needs FFmpeg, Pillow and NumPy; macOS produces the HEVC-alpha MOV variants for Safari/iOS. The included Swift encoder bounds bitrate; `avconvert` is the fallback when Swift is unavailable. The other browsers use VP9-alpha WebM. Desktop is 768px; mobile is 512px. Both remain transparent so the page’s circuit frame and gradients show through. The published finish samples every fifth native frame for 240 frames across the same 20-second orbit. Shadow-dependent diagonal purple halftone dots and fixed fine grain are baked into the transparent media. The optional smooth encoding preserves all 1,200 frames at 60fps.

The matching WebP still loads immediately. `hero-video.js` loads clips only when visible and motion is enabled. The hero and footer Pause motion buttons share the saved preference. Reduced motion, no JavaScript, unavailable codecs, and blocked playback preserve the still; hidden tabs and offscreen playback are suspended. Nothing about the video changes the name or portrait interactions.

After also encoding with `smooth`, the optional comparison exporter writes a private 12fps diagonal screen-print study beside the native 60fps clip in the render directory’s `comparison/` folder. Its Play/Pause page supports both WebM and Safari HEVC-alpha. It does not change published assets.
