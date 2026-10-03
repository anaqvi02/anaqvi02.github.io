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

Run `python3 ~/Desktop/update_project.py` for an interactive project/progress/deadline update that commits and pushes automatically. The maintained source is `tools/update-project.py`. Blank answers keep the current value; `-` clears the deadline. Completion accepts an integer from 0–100 or any non-integer text (for example `unknown`, `-`, or `42.5`); non-integer text is saved, pushed, and shown in the percentage spot without a `%` suffix or progress bar, including the no-JavaScript fallback. Enter an integer later to show progress again. For a direct update: `python3 tools/update-project.py --project "mtdi" --completion 95 --deadline 2026-10-14`. Use `--dry-run` to preview without writing or pushing, and `--push-only` to retry a failed push. It requires a clean `main` checkout, syncs with origin first, and updates both `status.json` and the homepage's no-JavaScript fallback. Dates use America/Toronto.

Edit `status_options` in `status.json` to change the hero’s Current status choices. Course choices use “Studying COURSE” or “Working on COURSE” for ECON 101, COMMST 100, MATH 137, MATH 135, and CS 135; “Working away on PROJECT...” follows the current project name. The page chooses one option at random on its first successful status-file load and keeps it for that page load; the once-per-minute refresh updates current project progress without rerolling the personal status. The homepage HTML contains a readable no-JavaScript fallback. A project's detail-page progress remains scoped to that project.

## Offline chrome hero

The deterministic sculpture has three folded mirror-chrome ribbons and six long, concave-rooted thorns surrounding a rotating Stella Octangula. The outer center is the exact compound of two regular tetrahedra: eight tips and 24 exposed triangular faces in dark amethyst glass. A smaller white emissive Stella Octangula rotates independently inside, refracting through the glass. The rings and outer center complete one calm 20-second orbit; the inner shape makes two relative turns around a different axis. The browser plays prerecorded media and never runs a 3D renderer.

All 3D rendering runs on Modal L4 GPUs through the authenticated CLI. `tools/render-hero.py` defines the Blender 4.5 scene. `tools/modal-hero.py` produces six preflight views, an isolated center preview, and a geometry audit before rendering eight bounded frame ranges. The 1024px source contains 1,200 native 60fps RGBA16 frames at 128 Cycles samples with denoising.

```sh
modal run tools/modal-hero.py --mode preflight
modal run --detach tools/modal-hero.py --mode render
modal run --detach tools/modal-hero.py --mode master
```

Detached jobs save their FunctionCall IDs in the private sibling `hero-render-v12/` directory. Poll those IDs before starting the master job. The Modal Volume `ali-hero-final-20261001` stores this version under `/stella-v12/`. The geometry audit samples 301 poses and checks the closing seam, cross-band intersections, center clearance, camera bounds, both independent center rotations, nested-core containment, and the Stella’s manifold topology. The six thorn roots also receive visual inspection; the numeric collision test compares separate meshes.

The cloud CPU job assembles an **ungraded lossless FFV1 master** at 1024px / 60fps with 16-bit color and alpha. It checks all 1,200 frames and compares decoded RGBA16 pixels with five source frames exactly. Preserve this master outside Git for future local encoding; no rerender is needed to change compression or print texture.

```sh
modal volume get ali-hero-final-20261001 /stella-v12/hero-stella-v12-lossless.mkv ../hero-render-v12/hero-stella-v12-lossless.mkv
python3 tools/encode-stella.py ../hero-render-v12/hero-stella-v12-lossless.mkv --output-dir ../hero-render-v12/browser
python3 tools/package-stella-safari.py ../hero-render-v12/browser
```

Local encoding adds a restrained fixed purple halftone at 18% ink without random grain. The desktop and mobile browser clips use 768px and 512px at native 60fps, preserving the 20-second orbit speed. VP9-alpha serves Chromium/Firefox; HEVC-alpha serves Safari/iOS. Only compact browser files and their matching WebP poster belong in `assets/`. Temporary ProRes intermediates are deleted automatically. Keep one private lossless master, the scene, source, and audit; remove raw frame sequences after verifying the downloaded master and deployed exports.

`hero-video.js` loads only the appropriate clip when visible and motion is enabled. Hero/footer Pause motion buttons share the saved preference. Reduced motion, no JavaScript, unavailable codecs and blocked playback preserve the matching poster; hidden tabs and offscreen playback suspend the clip. Name and portrait interactions stay independent. The public `hero-studies/` page offers manual playback of the current finish.

### Glass Stella close-up

`hero-studies/glass-stella.html` offers manual playback of the current 60 fps sculpture alongside a high-resolution close-up. The white inner compound’s 0.28-unit circumsphere fits inside the outer glass compound’s 0.34-unit insphere at every orientation. Facets remain sharp; bloom is restrained and masked to the glass. The production Modal pipeline explicitly selects `ALI_HERO_CORE_STYLE=glass`. `tools/modal-stella-study.py` can still produce inexpensive 12 fps material studies for future experiments; completed study frames are removed after packaging.

## Design language

The visual system is documented in [Chrome Fieldnotes](docs/design-language.md), with a visual guide at [design-guide/](design-guide/). Use these as the common reference for future changes.

The private sibling `../source-assets/` holds the current portrait PNG, its edit prompt, and the original chrome reference image. These editing sources stay outside the published site; `assets/` contains only media used by the current pages. Completed experiments, duplicate exports, and retired render previews can be removed. Keep `../hero-render-v12/hero-stella-v12-lossless.mkv` and its manifest for future re-encoding; current validation reports are in `docs/`.

## Circuit motion

Short red and violet current pulses follow the existing hero frame, About traces, portrait wiring, and Connect paths. They use SVG stroke dashes rather than layout transforms. Pause motion, reduced motion, hidden tabs and offscreen sections suspend them alongside the existing project-card circuits. Decorative SVGs remain outside the reading and focus order.
