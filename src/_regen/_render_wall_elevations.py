#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the 4 red wall elevations from the CURRENT red_brick_placement_v7_stairfix.json
so a human can inspect the bond after the re-lay. Fallback renderer (the prior-folder
_render_fix_walls.py depends on a PREZIP backup that does not exist in this folder, so it
cannot run here) - drawing logic (colour categories, opening outlines, scale bar) mirrors
that proven script, restricted to the 4 required elevation PNGs.
Categories: full=one colour, cut=orange, corner lap=magenta, half=purple."""
import json, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "..")
NEW = json.load(open(os.path.join(INP, "red_brick_placement_v7_stairfix.json")))

# extra openings not present in the per-wall "windows" list (verified by scanning brick
# coverage for gaps): C_NW_front has a full-height DOOR u[4059,7473] z[0,2891].
XT = {"C_NW_front": [("DOOR", 4059.0, 0.0, 7473.0, 2891.0)]}
COL = {"full": "#c0392b", "cut": "#e67e22", "lap": "#d81b9c", "half": "#7d3c98"}
LEGEND_LABELS = {"full": "full 215", "cut": "cut", "lap": "corner lap (full 215)", "half": "corner half (107.5)"}


def ext(b):
    us = [v[0] for v in b["verts"]]; zs = [v[1] for v in b["verts"]]
    return min(us), max(us), min(zs), max(zs)


def cat(b):
    cp = b.get("cp")
    if cp in ("lap", "half"):
        return cp
    return "full" if b["t"] == "full" else "cut"


def draw(ax, R, w):
    for b in R[w]["bricks"]:
        u0, u1, z0, z1 = ext(b)
        ax.add_patch(Rectangle((u0, z0), u1 - u0, z1 - z0, facecolor=COL[cat(b)],
                                edgecolor="black", linewidth=0.25))
    ops = [(x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4])) for x in R[w]["windows"]] + XT.get(w, [])
    for (nm, a, b0, bb, b1) in ops:
        ax.add_patch(Rectangle((a, b0), bb - a, b1 - b0, facecolor="#eef4fb", edgecolor="#1f5fa8",
                                linewidth=1.0, zorder=3))
        ax.text((a + bb) / 2, (b0 + b1) / 2, nm, ha="center", va="center", fontsize=7, color="#1f5fa8", zorder=4)


WALLS = [("A_NE_side", "A_NE", "_wall_A_NE.png", 0, 13624),
         ("C_NW_front", "C_NW", "_wall_C_NW.png", 0, 11533),
         ("B_SW_side", "B_SW", "_wall_B_SW.png", 0, 11205),
         ("D_SE_garden", "D_SE", "_wall_D_SE.png", 6855, 12530)]

for w, short, fn, uL, uR in WALLS:
    c = collections.Counter(cat(b) for b in NEW[w]["bricks"])
    width = (uR - uL) / 1000.0
    fig, ax = plt.subplots(figsize=(max(10, width * 1.35), 4.6), dpi=150)
    draw(ax, NEW, w)
    ax.set_xlim(uL - 120, uR + 120); ax.set_ylim(-260, 3050)
    ax.set_aspect("equal"); ax.axis("off")
    # scale bar (5 x 1m sections)
    x0 = uL; y0 = -180
    for i in range(5):
        ax.add_patch(Rectangle((x0 + i * 1000, y0), 1000, 50, facecolor="black" if i % 2 == 0 else "white",
                                edgecolor="black", linewidth=0.6))
    ax.text(x0, y0 - 90, "0", fontsize=7); ax.text(x0 + 5000, y0 - 90, "5 m", fontsize=7)
    ax.set_title("%s wall elevation (both-sides-single-cut re-lay): full=%d  cut=%d  corner lap=%d  half=%d  total=%d"
                 % (short, c["full"], c["cut"], c["lap"], c["half"], sum(c.values())), fontsize=9)
    handles = [Rectangle((0, 0), 1, 1, facecolor=COL[k], edgecolor="black") for k in ("full", "cut", "lap", "half")]
    ax.legend(handles, [LEGEND_LABELS[k] for k in ("full", "cut", "lap", "half")],
              loc="upper right", fontsize=7, ncol=4, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(INP, fn), bbox_inches="tight")
    plt.close(fig)
    print("saved", fn, "| full=%d cut=%d lap=%d half=%d total=%d" % (c["full"], c["cut"], c["lap"], c["half"], sum(c.values())))
