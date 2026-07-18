# src — source & generation kit (3 Monahan Avenue · HA23007)

Archive of the scripts and input data that generate the brick-slip / clip
take-off and the drawings/data used by the website under `/v2/`.

## Layout
- `combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py` — the
  combined Blender model (runs headless via a `bpy`/`mathutils` stub; builds
  red field + corner-flat quoins + black canopy + steel clips).
- `_regen/` — generation & verification kit:
  - `clip_engine_*.py` — steel guiding-rail clip placement engine.
  - `build_clip_types_svg.py` — the website clip **forming & cutting** sheet
    (M-section guiding rail: base 68 + legs 15 + inward lips 10, opening 62.5,
    developed blank 118, t=0.25; holes per the `guiding rail designs` ref).
  - `build_brick_tile_dxf/excel_*.py`, `build_brick_wall_layouts.py`,
    `build_clip_dxf/excel_*.py`, `build_sloped_wall_layout_*.py` — DXF / xlsx
    schedules and per-face layouts.
  - `rebuild_classification_with_redL.py` — brick Type-ID classifier.
  - `_fix_*`, `_field_from_corners_retile.py`, `_black_corner_to_flat.py`,
    `_flat_corners_retrofit.py` — one-off geometry transforms applied over the
    project's revision history.
  - `_audit_*`, `_verify*`, `_measure_corners.py`, `_render_*` — checks & renders.

## Input data (JSON)
- `red_brick_placement_v7_stairfix.json` — red field + corner-flat placement.
- `black_placement_fixed7.json` — black canopy placement (corners = flat pairs).
- `brick_types.json` — 46-type brick schedule (id, colour, w×h, qty, area).
- `clip_instances_red_d_se_garden_position_fix.json` — placed clip instances.

## Current totals (black-corners-flat revision, = website `/v2/`)
Red 5,964 + Black 1,733 = **7,697** slips · **98.42 m²** · clips **2,215** ·
screws **11,782**. Half-brick rule (≤107.5×65 = ½): red 5,644 whole + 320 half;
black 1,230 whole + 503 half.

> The built website (HTML/CSS/JS/SVG/data) lives in `/v2/`. This `src/` folder
> is a source archive; regenerating requires Python (ezdxf, openpyxl) and the
> bpy-stub used by the model script.
