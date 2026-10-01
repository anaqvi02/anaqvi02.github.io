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
