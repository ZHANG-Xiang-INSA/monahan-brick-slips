#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render brick_layout_black_canopy_faces.dxf (9 canopy faces, flat-corner edition) to PNG.
Every BRICK-layer polyline drawn as a filled shape (outline black, fill light grey);
face/title labels overlaid so a human can see which panel is which and confirm the
former L-return slots ('L-return LEFT'/'L-return RIGHT') are now empty (0 bricks) --
those corner bricks are now flat pairs folded into the OUTER/INNER wall faces."""
import os, ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "..")
DXF = os.path.join(INP, "brick_layout_black_canopy_faces.dxf")
OUT = os.path.join(INP, "_black_canopy_faces.png")

doc = ezdxf.readfile(DXF)
msp = doc.modelspace()

polys = [[(p[0], p[1]) for p in e.get_points()] for e in msp.query('LWPOLYLINE[layer=="BRICK"]')]
print("brick polylines:", len(polys))

LABEL_YMIN = -21000.0  # excludes the 27-type swatch legend block (starts ~y=-28032)
labels = []
for e in msp.query('TEXT[layer=="TITLE"]'):
    x, y, _ = e.dxf.insert
    if y > LABEL_YMIN:
        labels.append((x, y, e.dxf.text, e.dxf.height, True))
for e in msp.query('TEXT[layer=="TXT"]'):
    x, y, _ = e.dxf.insert
    if y > LABEL_YMIN:
        labels.append((x, y, e.dxf.text, e.dxf.height, False))
print("labels kept:", len(labels))

fig, ax = plt.subplots(figsize=(22, 15))
pc = PatchCollection([Polygon(p, closed=True) for p in polys],
                      facecolor="#ececec", edgecolor="black", linewidths=0.3)
ax.add_collection(pc)
for x, y, s, h, is_title in labels:
    fs = max(6, min(15, h * 0.03))
    ax.text(x, y, s, fontsize=fs, fontweight=("bold" if is_title else "normal"),
            color=("#1a1a1a" if is_title else "#444444"), va="top", ha="left")

# flag the two former-L-return slots explicitly (placed well clear, below the "0 bricks" caption)
for lx, ly in [(5920.0, -11050.0), (6168.0, -19846.0)]:
    ax.text(lx, ly - 550, "no bricks here now --\ncorner is now a flat pair;\nsee OUTER / INNER panels",
            fontsize=8, color="#b03030", style="italic", va="top", ha="left")

ax.set_xlim(-300, 8900)
ax.set_ylim(-25700, 1900)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Black canopy by face (9 faces) -- FLAT CORNERS -- former L-return slots now empty",
             fontsize=15, pad=12)
plt.tight_layout()
plt.savefig(OUT, dpi=130)
print("Saved", OUT)
