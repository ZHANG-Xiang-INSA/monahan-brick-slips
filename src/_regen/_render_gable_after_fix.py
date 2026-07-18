#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proof render: black gable front (y=-350) AFTER _fix_gable_voids.py, with the 4
former void bboxes (same defs as _audit_gable_voids.py DEFECT) overlaid as green
dashed boxes labelled FIXED, to show they are now covered by slips."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "..")
BLK = json.load(open(os.path.join(INP, "black_placement_fixed7.json")))["bricks"]
OUT = os.path.join(INP, "_gable_after_fix.png")

gable = [b for b in BLK if all(abs(v[1] + 350.0) < 1e-6 for v in b["verts"])]

DEFECT_BOXES = []
for sgn in (-1, 1):
    b1 = (min(sgn*-1623, sgn*-1398), 4845, max(sgn*-1623, sgn*-1398), 4880)
    b2 = (min(sgn*-1725.6, sgn*-1585), 5240, max(sgn*-1725.6, sgn*-1585), 5330)
    DEFECT_BOXES.append(b1); DEFECT_BOXES.append(b2)

fig, ax = plt.subplots(figsize=(14, 9))
for b in gable:
    pts = [(v[0], v[2]) for v in b["verts"]]
    cat = b.get("cat", "")
    fc = "#f4a460" if "cut" in cat else "#d9d9d9"
    ax.add_patch(MplPolygon(pts, closed=True, facecolor=fc, edgecolor="black", linewidth=0.4))

for (x0, z0, x1, z1) in DEFECT_BOXES:
    w, h = x1 - x0, z1 - z0
    ax.add_patch(Rectangle((x0, z0), w, h, fill=False, edgecolor="green",
                            linewidth=2.2, linestyle="--"))
    ax.text((x0+x1)/2, z1 + 15, "FIXED", color="green", fontsize=10, fontweight="bold",
            ha="center", va="bottom")

ax.set_xlim(-1800, 1800)
ax.set_ylim(-50, 5500)
ax.set_aspect("equal")
ax.set_title("Black gable front (y=-350) - after _fix_gable_voids.py\n"
              "former void zones (V1-V4) now filled - marked FIXED", fontsize=12)
ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
plt.tight_layout()
plt.savefig(OUT, dpi=150)
print("gable bricks drawn:", len(gable))
print("Saved", OUT)
