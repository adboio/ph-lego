# Max the PostHog Hedgehog

A seated brick interpretation of Max, based on the PostHog plushie: **873 pieces, 44 part/color combinations, and 282 building steps**. Approximately 18.9 × 11.8 × 18.9 cm, using five colors.

**[Open the interactive 3D building guide](https://adboio.github.io/ph-lego/)**

![Max brick model](max/renders/front-right.png)

Drag to rotate, scroll or pinch to zoom, and right-drag to pan. Switch between the complete model and the current building step, or select the rendered step illustration. The guide also works offline when its surrounding folders are kept together.

The revised face has thinner, concentric ears, a compact curved tan muzzle, a brown nose, and round black eyes with white quarter-tile highlights. The thick muzzle outline is gone. No eye stickers are required; the skin color, body and feet are unchanged.

## Downloads

- [Genuine LEGO / BrickLink ordering version](https://adboio.github.io/ph-lego/lego-order/) — 976 pieces, with documented substitutions and new-only or any-condition wanted lists
- [Printable instructions](max/instructions.pdf)
- [BrickWith upload — LDraw](brickwith-upload/max-brickwith.ldr)
- [BrickWith upload — BrickLink XML](brickwith-upload/max-brickwith.xml)
- [Inventory CSV](max/parts.csv) and [supplier product links](brickwith-parts.csv)
- [Editable model JSON](max/model.json) and [display-color LDraw model](max/model.ldr)

Use the dedicated `brickwith-upload` files for [BrickWith’s importer](https://www.brickwith.com/en/part-list/upload). The display-color LDraw file uses custom colors that its importer does not recognize. The revised LDraw file was tested on October 2, 2026: **43 available combinations / 871 pieces**, with an available-parts subtotal of **US$72.06** before shipping and tax. **Two tan 60474 ear backing plates are unavailable at BrickWith**; use the [two-piece BrickLink supplement](brickwith-upload/missing-ear-plates-bricklink.xml), or choose the complete genuine LEGO version above. See [import evidence](brickwith-upload/import-confirmed.png). Availability and prices can change. The XML is generated locally from the same inventory.

## Build status

This is a digital prototype, not a physically tested build. Digital checks pass for connections, assembly order, one connected final assembly, and conservative part envelopes. Partial-support warnings remain around the face, ears, arms, and some body overhangs. Clutch strength, stability, and load capacity need a physical test build. See [the validation report](max/validation.json).

The editable model uses the project-local `max-1.0` extension. Its toolchain is included in [working/engine](working/engine); rendering requires Python dependencies, Blender, and the official LDraw library at `working/library/ldraw`. Downloaded libraries, local reference photos, research, and draft bundles are not included. Viewing the finished guide needs only a WebGL-capable browser.

## Deployment

Pushes to `main` publish the guide and downloads through [GitHub Actions](.github/workflows/pages.yml). The root `index.html` opens `max/instructions/index.html`; all viewer code and geometry are embedded, with no external runtime or CDN dependency.

## Credits

- Character: Max / PostHog, based on supplied reference images. This is an unofficial model.
- Model and tool extensions: created with Codex for Adam.
- Brick Models engine: © 2026 Selami Selvi, [MIT license](working/engine/LICENSE).
- Geometry: [LDraw Parts Library contributors](https://www.ldraw.org/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Three.js and OrbitControls 0.160.1: [MIT license](working/engine/vendor/THREE-LICENSE.txt), also embedded in the viewer.

The model itself is currently marked `UNLICENSED`; third-party components retain their respective licenses.
