# Optional Premium Imagery — `images/`

The landing page is **complete and premium with zero images** — every scene
ships with hand-built, animated SVG art natively, themed per section.

If you want to upgrade any scene to a rendered/photographic visual, drop a file
into this folder with the **exact filename** listed below. The page lazy-loads
it (`loading="lazy"`, fades in on load) and layers it **over** the SVG art. If a
file is missing or fails to load, the SVG art stays — there is never a broken
image or empty space.

Images are loaded from the path `/images/<filename>` (this folder). They should
be **square** (1:1) and ≥ 1024×1024. Recommended format: **PNG with transparent
background**, or a flat JPEG on the page background `#f4f4f6` so the canvas blends.

## Global visual rules (match the existing premium tone)

- **Background:** light cool grey `#f4f4f6` (or transparent).
- **Primary accent:** teal `#138aa5` (deep teal `#0c6d83` for depth).
- **Ink / line work:** charcoal `#3e4145`, mid grey `#c5c6c8`.
- **Aesthetic:** clean, technical, **sharp/angular** — the page globally forces
  `border-radius: 0`, so avoid heavy soft glow / blurry clouds; prefer wireframe,
  schematic, blueprint, or product-render looks. Fine line work, subtle.
- **Mood:** scientific, restrained, expensive — like a pharma R&D keynote.
- **No text** baked into images (the page types its own labels).

---

## Per-scene slots

| # | Scene | Filename | Visual prompt |
|---|-------|----------|---------------|
| 00 | Hero | `hero.png` | A vertical DNA double helix rendered as an elegant scientific wireframe, teal `#138aa5` and grey strands, floating on a soft light-grey `#f4f4f6` background, fine line work, minimal, premium, 3D molecular render hint, depth-of-field, no text. |
| 01 | Who We Are | `who-we-are.png` | Abstract orbital diagram: a central glowing nucleus ringed by two tilted electron orbits, teal and grey strokes, on light grey, technical schematic style, dot particles along orbits, sharp line art. |
| 02 | What We're Doing | `what-we-do.png` | A descending optimization curve / eigenvalue-vs-iterations graph as a crisp neon-teal polyline over faint reference gridlines, charcoal axis, on light grey, premium data-viz, thin strokes, no text. |
| 03 | Theory | `theory.png` | A 3D molecular lattice of atoms and bonds, teal node highlights at vertices, grey bonds, cubic grid connection lines, translucent scientific render on light grey, depth shading, fine line work. |
| 05 | Layer 1 | `layer-1.png` | API-connection schematic: a central rounded-free node labeled visually as a chip, connected by teal lines to two outer atoms/servers, grey outlines, light grey background, minimal technical diagram style. |
| 06 | Layer 2 | `layer-2.png` | A generative neural net feeding into a chemistry tree: stacked teal-grey rectangles (LSTM cells) connected to a branching molecular SMILES tree, line art, scientific, light grey bg. |
| 07 | Layer 3 | `layer-3.png` | A relaxed 3D drug molecule (ball-and-stick) docking into a protein pocket represented as concentric contour rings centered in frame, teal molecule, grey pocket, blueprint tone, sharp. |
| 08 | Layer 4 | `layer-4.png` | A quantum circuit / chip die top view: square teal outline with inner qubit pads and bond traces, four corner contact pads, cyan glow at center, technical blueprint, fine line work, light grey bg. |
| 09 | Layer 5 | `layer-5.png` | A flat aromatic ring (hexagon) flagged with a faint warning grid behind it, versus a saturated 3D tetrahedral carbon, grey/teal contrast, schematic toxicity-check illustration, minimal, no text. |
| 10 | Layer 6 | `layer-6.png` | A 5-point dose-response curve (sigmoid) with teal points and a thin binding-curve overlay above faint dollar/rupee axis hints, premium chart art, charcoal lines, light grey bg, no text labels. |
| 11 | SMILES LSTM | `smiles-lstm.png` | Four stacked recurrent cells in a horizontal row with connection arrows and small character glyphs (C, N, =) flowing through, teal/grey schematic, monospace vibe, light grey bg. |
| 12 | AlphaFold | `alphafold.png` | A translucent ribbon-style 3D protein fold structure with highlighted active-site residues as teal nodes inside a faint pocket cavity, scientific render, soft, light grey bg. |
| 13 | Price & Drug Resolvers | `price-resolvers.png` | Two endpoint nodes (US flag-neutral “$” and India-neutral “₹” symbols rendered minimally, not as literal flags) connected by teal lines to a central QuantumShield hub node, grey schematic, sharp, light grey bg, no text other than the symbols. |
| 14 | Local Quantum Simulation | `local-sim.png` | A Qiskit-style circuit diagram: horizontal quantum wires with H, RY, CZ gates, teal and grey, square gate boxes, classical registers at bottom, technical, light grey bg. |
| 15 | IBM Hardware | `ibm-hardware.png` | A heavy-hex quantum processor topology: grid of qubit dots connected in the IBM heavy-hex layout, teal central qubits, grey outer, blueprint tone, a faint “QPU” silhouette chip body behind, sharp, light grey bg. |

### Transition overlay (bonus)
| | Transition | Filename | Prompt |
|---|------------|----------|--------|
| — | Enter Platform HUD | `virus_target.png` | A single clean pathogen rendering (stylized mycobacterium or virus capsid) on a pure white background, teal line accents, scientific illustration, centered, would be multiplied/blended — works best on white. Transparent or white bg essential. |

---

## Modules grid slots (Scene 17)

| # | Module | Filename | Visual prompt |
|---|--------|----------|---------------|
| 17a | VQE | `mod-vqe.png` | A 3D render of a quantum computing chip die, top view, fine line work, teal #138aa5 and charcoal #3e4145 wireframe, blueprint technical diagram style, on a transparent background, square 1024x1024, minimal, no text. |
| 17b | LSTM | `mod-lstm.png` | A schematic visualization of a character-level LSTM neural network generating molecular SMILES strings, technical wireframe style, teal #138aa5 and charcoal #3e4145 nodes and connections, on a transparent background, square 1024x1024, minimal, no text. |
| 17c | AlphaFold | `mod-alphafold.png` | An elegant 3D molecular ribbon protein structure render showing a binding pocket, minimal scientific wireframe, teal #138aa5 and charcoal #3e4145 lines, on a transparent background, square 1024x1024, no text. |
| 17d | RDKit | `mod-docking.png` | A 3D molecular conformation docking schematic, a small molecule fitting into a pocket contour grid, technical wireframe style, teal #138aa5 highlights, charcoal #3e4145 grid lines, on a transparent background, square 1024x1024, minimal, no text. |
| 17e | ADMET | `mod-admet.png` | A scientific toxicity check diagram, chemical structure hexagon with alert highlights, minimal technical schematic wireframe, teal #138aa5 and charcoal #3e4145, on a transparent background, square 1024x1024, no text. |
| 17f | Price | `mod-price.png` | A minimal data visualization chart showing comparative pricing metrics, fine wireframe graph, teal #138aa5 and charcoal #3e4145, on a transparent background, square 1024x1024, no text. |

---

## Notes

- Filenames are **case-sensitive on most servers** — use lowercase exactly as shown.
- Only add the files you want to upgrade; the rest keep their built-in SVG art.
- To revert a scene back to SVG art, just delete (or rename) its file from this folder.
- The optional image fades in over ~0.8s on lazy load and sits above the SVG, so SVG and raster never conflict.
