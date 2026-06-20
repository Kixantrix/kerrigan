# Asset playbook test plan

## Toolchain choice

Use a **pure Python stdlib compositor** for this Track A sample instead of HTML/CSS + browser capture.

### Why this wins on the playbook criteria

- **Diffable text source:** shared system, card row, and every layer definition are plain text files in this directory.
- **Headless + scriptable:** `build.sh` and `smoke.sh` run without a GUI or browser dependency.
- **Deterministic:** the export is assembled from fixed source files with a deterministic PNG writer and fixed layer order.
- **Native target format:** the build emits a print-ready PNG with explicit DPI metadata.
- **License / maturity / team fit:** no new third-party runtime is required beyond Python already used elsewhere in the repo.

## Declared print geometry

- Card face: **2.5in × 3.5in**
- Bleed: **0.125in** on each edge
- Export size including bleed: **2.75in × 3.75in**
- DPI: **400**
- Pixel size: **1100 × 1500**

## Layer stack

1. back
2. border
3. frame
4. art placeholder
5. set logo
6. nameplate
7. text box + watermark
8. rules text
9. card-shape mask applied to the front stack before compositing over the back
