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

The deterministic 3D sculpture has three asymmetric folded mirror-chrome ribbons and six long, concave-rooted thorns around smoked amethyst glass. Four tapered silver claws rise from a girdle rail and hook over the orb as a proper stone collet, fixed to the turning glass. Inside it, a textured eight-point star rotates independently twice per loop. The scene renders 1,200 native 60fps frames for a 20-second loop; compact browser delivery is 30fps. The browser plays video and never runs a 3D renderer.

All 3D rendering runs on Modal GPUs through the authenticated CLI. The measured L4 preview was about 20% slower per frame than L40S for this Blender scene but cost about half as much; H100 performed far worse on the same Cycles/OptiX sample. `tools/render-hero.py` defines the Blender 4.5 scene; `tools/modal-hero.py` runs the preview/audit, eight bounded L4 frame workers, and a CPU export job:

```sh
modal run tools/modal-hero.py --mode preflight
modal run tools/modal-hero.py --mode render
modal run tools/modal-hero.py --mode encode
```

Inspect the six preflight views before the full render. The geometry audit samples 301 poses at 67 ms intervals and checks the closing seam for cross-band and prong intersections, shell clearance, camera bounds, and motion continuity. Concave thorn roots also receive visual inspection; the numeric collision test compares separate meshes. See [the thorn study](docs/hero-thorn-plan.md) for shape decisions.

The final Blender scene, source and manifest live in the Modal Volume `ali-hero-final-20261001`. Eight L4 workers render independent ranges. The CPU job verifies sequence, unique frames, transparent corners and media metadata; it applies deterministic diagonal purple halftone, fixed fine grain, and subtle red/cyan registration limited to the glass rim. Grading uses cloud-local scratch and six independent workers. The validated web exports and poster live under `/final/media/`; temporary full-resolution PNGs and previews are cleared after encoding to conserve volume storage.

Desktop and mobile VP9-alpha exports are 512px and 320px at 30fps. The encoder verifies all 600 delivered frames, transparency, 20-second duration, full-file decoding, and file-size ceilings of 2 MB desktop and 800 KB mobile. Safari and iOS retain the matching WebP poster until HEVC-alpha packaging runs on a compatible macOS host. Raw 60fps PNG frames are removed after the validated export; the Blender scene and generator remain available on Modal for a future rerender.

The optional `--mode preview` starts a token-protected L40S Jupyter sandbox with a one-hour maximum lifetime. Its authentication URL belongs only in the private local access file. Use `--mode stop-notebook` when finished to avoid idle GPU billing. The bounded preflight is sufficient for ordinary rendering without an idle notebook.

The matching WebP poster loads immediately. `hero-video.js` loads a clip only when visible and motion is enabled. Hero/footer Pause motion buttons share the saved preference. Reduced motion, no JavaScript, unavailable codecs and blocked playback preserve the poster; hidden tabs and offscreen playback suspend the clip. Name and portrait interactions stay independent.

The public `hero-studies/` page offers manual playback of the current 30fps compact finish. `tools/encode-hero.py` supports lower-rate experiments using exact frame subsampling, never interpolation. Prior local render runs and obsolete published clips are removed after final verification; keep the current cloud master, source, poster and browser exports.

## Design language

The visual system is documented in [Chrome Fieldnotes](docs/design-language.md), with a visual guide at [design-guide/](design-guide/). Use these as the common reference for future changes.

## Circuit motion

Short red and violet current pulses follow the existing hero frame, About traces, portrait wiring, and Connect paths. They use SVG stroke dashes rather than layout transforms. Pause motion, reduced motion, hidden tabs and offscreen sections suspend them alongside the existing project-card circuits. Decorative SVGs remain outside the reading and focus order.
