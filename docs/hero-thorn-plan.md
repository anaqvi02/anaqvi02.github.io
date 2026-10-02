# Hero thorn study: hooked mercury around the storm

## Goal

The hero should read as a thorned, folded-metal sculpture guarding a small, contained star. Keep the approved three folded rings, camera, framing, smoked amethyst orb, and calm 20-second revolution. The new idea is not another ring or a field of random needles: it is a more legible thorn hierarchy. Preserve the existing nine long swept thorns as the outer, dramatic silhouette; add three or four smaller hooked claws near the orb so the inner metal appears to grasp and protect it.

Render the final loop through Modal on an L40S at 60 fps. A 20-second loop is 1,200 frames. Do not render locally. Keep the approved v6 24 fps poster as a visual reference for the folded-ring arrangement and transparent framing, not as evidence that the additional claw forms have already been implemented.

## What the references say

`assets/chrome-orbital.png` has useful aggression: its bands feel forged, its points have long directional sweeps, and their changing lengths create a memorable spined silhouette. It also has too many delicate crossing filaments around the core. Some prongs read as wire or orbital linework, so the form can drift toward a generic science-fiction atom mark instead of a single sculptural object.

The approved v6 24fps poster restores a stronger hierarchy. Broad, folded silver ribbons dominate; the dark gaps between them give the object volume; the purple glass orb remains visible. It is cleaner, but the current hero can still read as smooth interlocking loops with a few polished spikes. Those existing spikes are long and mostly sweep away from the center. Their pointed ends alone do not create the visual hook, concave root, and barb that make a form unmistakably thorny.

The renderer confirms that distinction. `Stream` creates three continuous folded bands at radii 3.25, 2.42, and 1.73 around a shell of radius 1.08. Each carries three integrated thorns, for nine total. `update()` moves their angle and length slightly over the shared turn. The cross-section already has folded shoulders and a return edge, but a thorn’s silhouette is mainly a swept projection from the ribbon. The design opportunity is to make the long thorns feel more rooted and to add a second, clearly hooked class close to the core.

## Thorn hierarchy and shape language

**The nine existing thorns stay.** Keep their count, positions, role, and overall reach. They are the long outer blades: asymmetric, swept, and sharp enough to break the outer silhouette. Preserve the rings’ current approved diameter and loop crossings. Improve their readability through roots and profile, not by making them longer or by adding more outward spikes. Each should emerge from a visible shoulder in its ribbon, broaden briefly at its root, form a shallow concave scoop on the trailing side, then narrow rapidly into a clean apex. A slim raised ridge catches the studio reflection; the underside falls into dark purple-black contrast. The root and thorn should flow as one surface, with no ball-like joint or separate cone.

**Add three or four inner claws to the innermost folded band.** Place them on camera-facing inner arcs that frame the shell—two flanking the upper orb, with a lower or lateral third; use a fourth only if its negative space stays clear. Distribute them by visible image composition, not equal abstract angles alone. Leave the star’s central highlight readable and preserve a clean view of the orb silhouette. Keep the claws inside the already approved overall projection so they do not change the sculpture’s external envelope.

A claw starts flush with the inner lip, swells into a rooted shoulder, then curves inward toward the shell and hooks tangentially backward at its tip. It should suggest a talon curling around glass, not a straight spike aimed at the star. Use a strong concave root, a convex polished ridge, a darker recessed underside, and a narrow, decisive apex. The hook must be visible at homepage scale: use a clear change of direction through the final third rather than a barely bent needle. Avoid perfect bilateral symmetry; alternate hook direction and length slightly so the object feels grown and forged, while retaining balance around the orb.

As a first geometry pass, give each claw roughly 0.35–0.55 units of visible curved path, with about 0.18–0.28 units of inward reach from its root. Keep the tip at least 0.15–0.20 units outside the 1.08-radius shell in every evaluated pose. These are starting dimensions, not permission to intersect the glass or other rings. If the available inner-lip clearance is smaller after deformation, shorten the hook and sharpen its curve instead of moving the ring or shell. The root should be broad enough to read as part of the ribbon; the tip should taper to a crisp, non-rounded point. Use a triangular or flattened leaf-like cross-section with a ridge, not a round tube.

This separation of roles matters: the nine long outer thorns supply silhouette and forward motion; the three or four inner claws supply proximity, tension, and a protective grasp. Do not make every thorn a hook, fill every gap, or add a dense halo of wires. The orb needs surrounding negative space to remain the focal point.

## Light, finish, and print

Retain the mirror-chrome studio reflections and strong black-to-white value range. Silver should read as metal through broad clean highlights and nearly black reflection bands; violet may tint selected reflections and shadow wells. Avoid a uniform purple chrome coating, blown-out white plates, or diffuse grey that hides the fold. Make the new root scoops legible with reflected contrast rather than outlines or added graphic strokes.

Keep the smoked amethyst shell dark and sharply bounded, with the turbulent star and every flare, ember, and glow contained inside it. The hero already has a mask that confines orb bloom; preserve that boundary. Apply restrained magenta/cyan chromatic separation only to the visible glass rim, using an object/rim mask and roughly 1–2 px of channel offset at 768 px. Keep a sharp base orb silhouette underneath the faint registration split; leave the star and metal highlight centers crisp. The current global lens-dispersion effect fringes unrelated bright details; a selective rim mask is more controlled. The split should read as slight print misregistration, not a moving RGB glitch.

Keep the diagonal purple halftone shadow-bound to the sculpture and alpha-preserving. Dots should reveal form where metal occludes light, then fade into transparency. Do not place a rectangular screen, striped panel, or full-frame dot field behind the transparent object.

## Motion and validation

Keep the common slow 20-second turn, existing band flow, glass rotation, and evolving contained storm. New claws should move as continuous portions of their parent band; do not animate them independently, pulse their tips, or make the chrome shimmer with frame-to-frame color noise. Their shape change over the loop should be barely perceptible, and the loop must close exactly at frame 1,201. At 60 fps, export 1,200 unique frames and confirm first/last seam continuity.

Before final rendering, check every pose for: cross-band triangle intersections; hook-to-shell minimum clearance; hook-to-star visual occlusion; self-intersection at concave roots; camera clearance; preservation of the existing outer silhouette; and transparent alpha around the media. Review the hook hierarchy at thumbnail size as well as full size: nine outer blades should still read as long swept thorns, while the inner claws should register as claws rather than crossing ring fragments. A contact sheet at quarter turns is enough to catch changing tangencies before committing the Modal render.

## Guardrails

Do not replace the rings, alter the approved camera or crop, enlarge the shell, break the star containment, or move existing outer thorns just to make room. Do not make the sculpture a literal crown, spider, atom icon, or barbed-wire ball. Do not add extra rings, loose claw meshes, uniform spikes, bright outlines, global rainbow dispersion, or independent jitter. The goal is a stronger thorn language inside the existing folded-metal object: visibly rooted, concave, ridged, sharply tapered, and carefully hooked around the storm.


## Final preflight decision

The v7 preview keeps nine long outer thorns and adds three inner claws with length parameters of 0.70, 0.74, and 0.68 units. Full-size and 400px contact-sheet review passed, followed by desktop and phone homepage inspection. Reflected black bands keep the chrome folds readable. A foreground band partially crosses the core during the turn, but the shell and star remain recognizable. No camera or speed change was needed.

The cloud audit evaluated 1,201 poses, including the seam, with 3,603 cross-band BVH checks. Minimum shell clearance was 0.145 units, loop mesh delta was zero, and the projected sculpture stayed inside the camera at a half extent of 0.444. Concave roots were reviewed visually; the numeric collision audit tests separate bands rather than self-intersection inside a band. The final export keeps the 20-second turn and raises native sampling to 60 fps.
