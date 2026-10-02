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

The deterministic 3D sculpture has three asymmetric folded mirror-chrome ribbons, nine swept rose-like thorns, and three integrated claws curling around smoked amethyst glass. A changing stellar photosphere, coronal flares and embers remain inside the darker orb. The sculpture turns once per 20 seconds; its native 60fps export contains 1,200 unique frames. The browser plays video and never runs a 3D renderer.

All 3D rendering runs on Modal L40S GPUs through the authenticated CLI. `tools/render-hero.py` defines the Blender 4.5 scene; `tools/modal-hero.py` runs the preview/audit, four bounded frame workers, and a CPU export job:

```sh
modal run tools/modal-hero.py --mode preflight
modal run tools/modal-hero.py --mode render
modal run tools/modal-hero.py --mode encode
```

Inspect the six preflight views before the full render. The geometry audit checks 1,201 poses, including the closing seam, for cross-band triangle intersections, shell clearance, camera bounds, and motion continuity. The final v7 preflight has 0.145 units of minimum shell clearance and zero loop mesh delta. Concave thorn roots also receive visual inspection; the numeric collision test compares separate bands. See [the thorn study](docs/hero-thorn-plan.md) for shape decisions.

The final master and scene live in the Modal Volume `ali-hero-final-20261001`. Unique frame paths allow four workers to commit independent ranges. The CPU job verifies sequence, unique frames, transparent corners and media metadata; it applies deterministic diagonal purple halftone, fixed fine grain, and subtle red/cyan registration limited to the glass rim. Grading uses cloud-local scratch and six independent workers. Final media is written under `/final/media/`; source and reproducible scene remain alongside the raw frames.

Desktop exports are 768px and mobile exports 512px. Chrome/Firefox use VP9-alpha WebM. Safari/iOS use HEVC-alpha MOV, packaged on macOS from the already-rendered cloud ProRes master with `tools/encode-alpha.swift`; this is video encoding, not local 3D rendering. Run `python3 tools/package-safari.py path/to/downloaded/media` with FFmpeg 8 or newer. The helper normalizes the cloud ProRes alpha to a macOS-compatible bitstream, checks decoded transparency before writing, and verifies 60fps/1,200 frames/20 seconds afterward. Its temporary repacks and compiler cache are removed automatically.

The optional `--mode preview` starts a token-protected L40S Jupyter sandbox with a one-hour maximum lifetime. Its authentication URL belongs only in the private local access file. Use `--mode stop-notebook` when finished to avoid idle GPU billing. The bounded preflight is sufficient for ordinary rendering without an idle notebook.

The matching WebP poster loads immediately. `hero-video.js` loads a clip only when visible and motion is enabled. Hero/footer Pause motion buttons share the saved preference. Reduced motion, no JavaScript, unavailable codecs and blocked playback preserve the poster; hidden tabs and offscreen playback suspend the clip. Name and portrait interactions stay independent.

The public `hero-studies/` page offers manual playback of the current 60fps finish. `tools/encode-hero.py` supports lower-rate experiments using exact frame subsampling, never interpolation. Prior local render runs and obsolete published clips are removed after final verification; keep the current cloud master, source, poster and browser exports.

## Design language

The visual system is documented in [Chrome Fieldnotes](docs/design-language.md), with a visual guide at [design-guide/](design-guide/). Use these as the common reference for future changes.
