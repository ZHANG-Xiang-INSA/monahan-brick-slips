#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-audit of the black gable front (y=-350) after _fix_gable_voids.py.
Designed outline = wall rect +-1725.5 x 0..5296 + 40-deg gable to the apex.
Voids = outline minus union(bricks dilated 5.3 to close 10 mm joints), eroded 2.2, area>150.
PASS = after-voids == designed openings (= before-voids minus the 4 defect boxes),
0 overlaps, all same-course joints 10+-0.6 mm (openings excluded), no piece < 20 mm."""
import json, math, os
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__))
T40 = math.tan(math.radians(40.0))
APEX = 5296.0 + 1725.5 * T40
OUTLINE = Polygon([(-1725.5, 0), (1725.5, 0), (1725.5, 5296.0), (0, APEX), (-1725.5, 5296.0)])
DEFECT = unary_union([box(*b) for sgn in (-1, 1) for b in
                      ((min(sgn*-1623, sgn*-1398), 4845, max(sgn*-1623, sgn*-1398), 4880),
                       (min(sgn*-1725.6, sgn*-1585), 5240, max(sgn*-1725.6, sgn*-1585), 5330))])

def polys(fn):
    d = json.load(open(os.path.join(HERE, "..", fn)))["bricks"]
    return [Polygon([(v[0], v[2]) for v in b["verts"]]) for b in d
            if all(abs(v[1]+350.0) < 1e-6 for v in b["verts"])], d

def voids(ps):
    cov = unary_union([p.buffer(5.3, join_style=2) for p in ps])
    v = OUTLINE.difference(cov).buffer(-2.2).buffer(2.2)
    return [g for g in getattr(v, "geoms", [v]) if g.area > 150.0]

before, _ = polys("black_placement_fixed7_PREV1FIX.bak.json")
after, raw = polys("black_placement_fixed7.json")
vb, va = voids(before), voids(after)
openings = unary_union(vb).difference(DEFECT).buffer(-2.2).buffer(2.2)
ua = unary_union(va) if va else Polygon()
defects_left = ua.intersection(DEFECT).area
newvoids = ua.difference(openings.buffer(6.0)).area
symdiff = ua.symmetric_difference(openings).area
# overlaps
ov = 0.0
for i in range(len(after)):
    for j in range(i+1, len(after)):
        if after[i].intersects(after[j]):
            ov = max(ov, after[i].intersection(after[j]).area)
# joints + min piece size (gable rows)
import collections
rows = collections.defaultdict(list)
mindim = 1e9
for b in raw:
    if not all(abs(v[1]+350.0) < 1e-6 for v in b["verts"]):
        continue
    xs = [v[0] for v in b["verts"]]; zs = [v[2] for v in b["verts"]]
    rows[round(min(zs))].append((min(xs), max(xs)))
    if len(b["verts"]) > 3:  # triangles taper to a point by design
        mindim = min(mindim, max(xs)-min(xs), max(zs)-min(zs))
badj = []
for z0, row in rows.items():
    row.sort()
    for a, c in zip(row, row[1:]):
        g = c[0]-a[1]
        if g < 50 and abs(g-10.0) > 0.6:
            badj.append((z0, round(a[1], 1), round(g, 2)))
print("gable audit: before-voids=%d after-voids=%d defect-area-left=%.0f new-void-area=%.0f "
      "symdiff-vs-openings=%.0f max-overlap=%.1f bad-joints=%d min-piece-dim=%.1f"
      % (len(vb), len(va), defects_left, newvoids, symdiff, ov, len(badj), mindim))
ok = defects_left < 50 and newvoids < 50 and symdiff < 2000 and ov < 1.0 and not badj and mindim >= 20
print("GABLE AUDIT %s" % ("PASS" if ok else ("FAIL " + str(badj[:6]))))
