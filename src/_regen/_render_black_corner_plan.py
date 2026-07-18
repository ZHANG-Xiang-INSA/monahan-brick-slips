#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused plan-view (x-y) of the black canopy's TWO front corners (front-left / front-right),
lowest 6 courses, straight from black_placement_fixed7.json. Each brick drawn as its true
footprint (extruded by th_mm opposite its outward normal so the slip is visible in plan):
full slip = grey, cut slip = orange. The building arris (outer corner edge, x=+-1725.5 / gable
front plane y=-350) is marked with a red star + dashed crosshair. Confirms course-by-course
that the corner is a FLAT PAIR (one wall's brick laps 20mm past the arris, the other wall's /
gable's brick is cut back 20mm to tuck behind it) -- alternating side each course -- not a
one-piece L slip."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "..")
BLK = json.load(open(os.path.join(INP, "black_placement_fixed7.json")))["bricks"]
OUT = os.path.join(INP, "_black_corner_plan.png")

def zbot(b): return min(p[2] for p in b["verts"])
def is_vert(b):
    nx, ny, nz = b["normal"]; return abs(nz) < 0.05 and (abs(nx) > 0.9 or abs(ny) > 0.9)
def cx(b):
    xs = [p[0] for p in b["verts"]]; return sum(xs) / len(xs)

vert = [b for b in BLK if is_vert(b)]
courses = sorted(set(round(zbot(b), 1) for b in vert))[:6]
print("courses used (lowest 6):", courses)

OUTER = 1725.5   # true outer building corner (outer wall face), from the placement data
GFRONT = -350.0  # gable-front plane

def footprint(b):
    xs = [p[0] for p in b["verts"]]; ys = [p[1] for p in b["verts"]]
    nx, ny, nz = b["normal"]; th = b["th_mm"]
    dx = max(xs) - min(xs)
    if dx < 1.0:  # wall-type brick: constant x, runs in y
        x0 = xs[0]
        xr = (x0, x0 + th) if nx < 0 else (x0 - th, x0)
        yr = (min(ys), max(ys))
    else:         # gable-type brick: constant y, runs in x
        y0 = ys[0]
        yr = (y0, y0 + th) if ny < 0 else (y0 - th, y0)
        xr = (min(xs), max(xs))
    return xr, yr

def in_window(b, side):
    c = cx(b)
    return (-2000 <= c <= -1050) if side == "L" else (1050 <= c <= 2000)

fig, axes = plt.subplots(len(courses), 2, figsize=(11.5, 3.15 * len(courses)))
for i, z in enumerate(courses):
    for j, (side, corner_x) in enumerate([("L", -OUTER), ("R", OUTER)]):
        ax = axes[i, j]
        cbricks = [b for b in vert if abs(zbot(b) - z) < 1 and in_window(b, side)]
        for b in cbricks:
            xr, yr = footprint(b)
            full = (b["cat"] == "flat_full")
            color = "#a3a3a3" if full else "#e3872f"
            ax.add_patch(Rectangle((xr[0], yr[0]), xr[1] - xr[0], yr[1] - yr[0],
                                    facecolor=color, edgecolor="black", linewidth=0.7, zorder=3))
        ax.axvline(corner_x, color="crimson", linestyle="--", linewidth=0.9, alpha=0.85, zorder=4)
        ax.axhline(GFRONT, color="crimson", linestyle="--", linewidth=0.9, alpha=0.85, zorder=4)
        ax.plot([corner_x], [GFRONT], marker="*", color="crimson", markersize=13, zorder=5)
        ax.set_xlim(-1980, -1080) if side == "L" else ax.set_xlim(1080, 1980)
        ax.set_ylim(-460, 160)
        ax.set_aspect("equal")
        corner_name = "front-LEFT" if side == "L" else "front-RIGHT"
        ax.set_title("course z=%.0f  |  %s corner  (n=%d slips)" % (z, corner_name, len(cbricks)), fontsize=9)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("x (mm)", fontsize=7); ax.set_ylabel("y (mm)", fontsize=7)

full_patch = Rectangle((0, 0), 1, 1, facecolor="#a3a3a3", edgecolor="black")
cut_patch = Rectangle((0, 0), 1, 1, facecolor="#e3872f", edgecolor="black")
fig.legend([full_patch, cut_patch], ["full slip (flat_full)", "cut slip (flat_cut)"],
           loc="upper center", ncol=2, fontsize=10, bbox_to_anchor=(0.5, 1.012))
fig.suptitle("Black canopy corners -- lowest 6 courses, plan view (x-y)\n"
             "red star / dashed crosshair = building arris. Each course: one wall's slip laps 20mm past the "
             "arris (full) while the other face is cut back 20mm (orange) -- flat pair, alternating side each "
             "course. No one-piece L slip.", fontsize=11, y=1.035)
plt.tight_layout()
plt.savefig(OUT, dpi=130, bbox_inches="tight")
print("Saved", OUT)
