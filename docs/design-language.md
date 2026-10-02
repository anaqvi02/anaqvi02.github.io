# Chrome Fieldnotes

**Chrome Fieldnotes** is an editorial portfolio with a technical pulse: warm paper, confident type, sparse circuit notation, and one improbable piece of liquid metal. It pairs the tactility of a printed field notebook with the impossible polish of the hero sculpture.

This guide records the intended direction and the current foundation; it does not claim every recommendation has shipped. The site already has the paper palette, typography roles, project marks, circuit drawings, chromatic portrait, and pre-rendered hero. Some late CSS overrides make washes and panels broad and rectangular; refine those against this system.

## The visual idea

The portfolio has two registers. **Fieldnotes** organize information through editorial spacing, rules, captions, project labels, and human handwriting. **Chrome** appears as a singular sculptural event: thick, folded thorn-like ribbons with swept ends and deep black-to-mirror contrast, rotating around a smoked purple orb. A turbulent star stays contained inside the shell. The object should feel weighty and reflective, not like a thin wire logo or pasted-on sticker.

Circuit paths and screen-print marks behave like annotations: they point, register, measure, and frame. Keep the paper calm enough that the sculpture reads immediately and the work remains easy to scan.

## Color tokens and roles

| Token | Value | Role |
| --- | --- | --- |
| Paper | `#f5f3ed` | Main page ground; the largest color area and the source of warmth. |
| Surface | `#faf8f3` | Quiet raised reading areas, if a surface is needed. |
| Ink | `#292630` | Primary text, dark artwork contrast, and occasional dark field. |
| Violet | `#5e3bc4` | Structural anchor: section headings, circuit paths, project identity, and the orb’s surrounding atmosphere. |
| Signal red | `#af3047` | A recurring second signal: status, action, selected traces, registration marks, active rules, and small emphasis. |
| Muted | `#6c6572` | Secondary prose and annotations. |
| Rule | `#d3cfd5` | Quiet dividers and technical baselines. |

Red should recur throughout the page as a deliberate system. Give each major section at least one role—status marker, rule segment, active circuit path, label, or registration corner—while varying size and placement. Keep most marks small and precise. Violet remains the chromatic anchor and cream the readable base. In the sculpture, near-black reflections make the chrome legible against the pale page and purple shell.

## Typography hierarchy

Use typography to separate voice and function, not to decorate every line. Keep the established type family roles coherent across the homepage, gallery, About, Connect, and project pages.

| Role | Typeface | Use |
| --- | --- | --- |
| Display | Antonio | Oversized name, section punches, compact all-caps headlines. Use tight leading and tracking with room around the form. |
| Technical sans | Chakra Petch through `--tech` | Navigation, project subheads, actions, and concise technical statements. Its technical character should remain easy to read. |
| Body | DM Sans | Paragraphs, descriptions, and ordinary interface text. Prefer comfortable line lengths and relaxed leading. |
| Readout | IBM Plex Mono | Coordinates, status labels, dates, tags, small IDs, and circuit annotations. Keep it small and purposeful. |
| Human countervoice | Instrument Serif | Italic status notes and a few selected phrases. Use sparingly to interrupt the machine precision with warmth. |

The page should not acquire a new typeface for every mood. Let Antonio carry scale, Chakra Petch carry technical clarity, DM Sans carry reading, IBM Plex Mono carry data, and Instrument Serif carry the handwritten tension. These existing roles cover the system; no additional family is needed. Serif phrases should stay short; mono should not become body copy.

## Composition and graphic grammar

Use shared page edges, open margins, and a consistent column rhythm. The header is a compact masthead. Give the name and sculpture room to coexist. Project cards may vary in width or artwork, but align metadata, title, and description. About and Connect return to editorial reading: a clear heading, one image or schematic, then open text and links.

Circuit motifs use thin orthogonal paths, measured bends, small nodes, ticks, red signal segments, and cropped registration corners. Repeat a few across sections for continuity, leaving quiet stretches of paper between them. Avoid full angular borders around every section; use a corner, rule, or partial trace instead.

Screen-print texture behaves like ink. Use diagonal violet halftone near the sculpture’s shadow or a project mark, masked to fade or follow an organic silhouette. Preserve contrast and whitespace; never turn the texture into wallpaper or reduce text legibility.

## Light, gradients, and chromatic registration

Build the hero’s violet field from soft radial or elliptical light around the sculpture. Feather it to transparent; clip halftone to light, shadow, or silhouette. Keep media transparent. No rectangular gradient plate, square halo, hard-edged color block, or broad stripe should read as a separate layer. Project art may use localized glow or texture, while keeping its mark and surface primary.

Chromatic aberration is a purposeful registration error. Use restrained magenta/red and cyan offsets on selected high-contrast edges, especially the name or portrait. Keep the split crisp and edge-bound so text and portrait stay sharp. The portrait may respond subtly to pointer movement through channel offset alone; never rotate or wobble it. Avoid RGB haze, rainbow glow, and repeated glitches.

## Page-specific expression

- **Hero:** Establish name first, then the status/readout, then the sculpture. Keep the sculpture’s folded thorn chrome substantial, black-contrasted, and cleanly silhouetted; preserve the smoked purple orb and fully contained star. Give the name a restrained dark-purple halftone in the lower third of each glyph, clipped to the text so its violet fill, depth shadow, and registration fringes remain legible. Add fixed-to-orb silver hooks that sit on the glass surface; they rotate with the ball and stay still relative to it. Place local violet atmosphere and halftone behind the sculpture’s transparent edges. Circuit detail should sit toward the stage perimeter. Keep the motion control clear and close to the artwork.
- **Selected work:** Let each project have a distinct mark and one or two graphic cues that relate to its subject. Apply red consistently to labels, active traces, or selection cues across the set. Keep card backgrounds related to the project rather than forcing a chrome treatment onto them. Use a quiet grid and aligned metadata to make the gallery feel curated.
- **About:** Pair portrait registration and sparse circuit notation with genuinely open space for the story. One strong heading, one image treatment, selective red markers, and a readable text column are enough. Avoid stacking clipped boxes around the lead, story, and every interest list.
- **Connect:** Treat contact choices like clear links in the same information system. Use a red active edge or signal line and a small violet schematic if useful; keep text and interaction state primary.

## Motion and interaction

Motion should explain arrival, state, or physical form. The offline, alpha-preserving hero loop turns once per 20 seconds; its final cloud master and selected published finish are native 60 fps (1,200 unique frames). Higher frame rate smooths the motion without changing the orbit speed. Keep it slow, preserve the still poster, and keep the star inside the orb. Prefer a clear page-arrival fade to jitter, flashing, or cascades. A signal path can travel slowly; a link underline can appear on hover or focus. Do not animate every element at once.

Respect pause controls and `prefers-reduced-motion`. Reduced motion should leave a composed still, not hide useful information. Pointer response should be limited to a gentle registration shift on the portrait or other explicit target, never page-wide movement or image rotation. Keyboard focus remains visible and functional.

## Keep and avoid

**Keep:** warm cream paper; ink-dark text; violet as the visual anchor; recurring red as a meaningful signal; the Antonio / Chakra Petch / DM Sans / IBM Plex Mono / Instrument Serif voice system; the unique chrome sculpture; sparse circuit notation; localized halftone; sharp readable copy; responsive editorial spacing.

**Avoid:** chrome on unrelated buttons or cards; square or central rectangular gradients; broad diagonal stripes; circuit mazes; boxes around every content group; clipped-corner overload; full-page halftone; indiscriminate red borders; neon glow; constant chromatic blur; portrait rotation; scroll jitter; and motion that competes with reading.

When an effect does not reinforce the sculpture, the print language, the information hierarchy, or the human voice, remove it. The page should still feel complete when every animation is paused and every decorative layer is hidden.
