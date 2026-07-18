#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIX 1 - black gable front (y=-350): fill the 4 mirror-symmetric defect voids.
V1/V2 opening-head band: extend the 215x50 slips (u +-1398..1613, z 4800-4850) to full 215x65.
V3/V4 eave/rake spring: replace each 102.5x46 corner cut (u +-1623..1725.5, z 5250-5296) with a
single-cut rake-profiled piece (rect with 40-deg corner cut, follows the outer rake); re-anchor
the 3 adjacent fulls of course 5250 at the corner piece (10 mm joint, shift 22.6 toward corner)
and widen the opening-head rake triangle into a quad so the opening-rake joint stays 10 mm.
Deterministic; edits black_placement_fixed7.json in place. Prints a short audit."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "..", "black_placement_fixed7.json")
D = json.load(open(F))
BR = D["bricks"]
T40 = math.tan(math.radians(40.0))

def gable(b):
    return all(abs(v[1] + 350.0) < 1e-6 for v in b["verts"])

def bb(b):
    xs = [v[0] for v in b["verts"]]; zs = [v[2] for v in b["verts"]]
    return min(xs), max(xs), min(zs), max(zs)

def find(x0, x1, z0, z1, tol=0.6):
    out = [i for i, b in enumerate(BR) if gable(b) and
           abs(bb(b)[0]-x0) < tol and abs(bb(b)[1]-x1) < tol and
           abs(bb(b)[2]-z0) < tol and abs(bb(b)[3]-z1) < tol]
    assert len(out) == 1, (x0, x1, z0, z1, out)
    return out[0]

def setpoly(i, pts, cat):
    BR[i]["verts"] = [[round(x, 1), -350.0, round(z, 1)] for x, z in pts]
    BR[i]["cat"] = cat

changed = []
KNEE = round(-1725.5 + 19.0 / T40, 1)          # -1702.9 (outer rake at z=5315)
QIN = round(-915.4 - 5.0 * 71.5 / 60.0, 1)     # -921.4 (opening rake at z=5250)
for s in (-1.0, 1.0):
    def m(pts):  # mirror; keep CCW order by reversing when mirrored
        q = [(s * x, z) for x, z in pts]
        return q if s < 0 else q[::-1]
    # V1/V2: extend 215x50 head slip to 215x65
    i = find(min(s*-1613.0, s*-1398.0), max(s*-1613.0, s*-1398.0), 4800.0, 4850.0)
    x0, x1, _, _ = bb(BR[i])
    setpoly(i, [(x0, 4800.0), (x1, 4800.0), (x1, 4865.0), (x0, 4865.0)], "flat_full")
    changed.append(("V-head extend 215x65", i))
    # V3/V4: corner cut 102.5x46 -> rake-profiled single-cut piece (max h 65, 46 at arris)
    i = find(min(s*-1725.5, s*-1623.0), max(s*-1725.5, s*-1623.0), 5250.0, 5296.0)
    setpoly(i, m([(-1725.5, 5250.0), (-1623.0, 5250.0), (-1623.0, 5315.0),
                  (KNEE, 5315.0), (-1725.5, 5296.0)]), "flat_cut")
    changed.append(("corner rake piece", i))
    # re-anchor the three fulls of course 5250 at the corner piece (shift 22.6)
    for a in (-1590.4, -1365.4, -1140.4):
        i = find(min(s*a, s*(a+215.0)), max(s*a, s*(a+215.0)), 5250.0, 5315.0)
        n0 = a - 22.6
        setpoly(i, m([(n0, 5250.0), (n0+215.0, 5250.0), (n0+215.0, 5315.0), (n0, 5315.0)]),
                "flat_full")
        changed.append(("full shift", i))
    # widen the opening-head rake triangle into a quad (joint to shifted full = 10)
    tri = [i for i, b in enumerate(BR) if gable(b) and len(b["verts"]) == 3 and
           abs(bb(b)[2]-5255.0) < 0.6 and abs(min(s*bb(b)[0], s*bb(b)[1]) - (-915.4)) < 0.6]
    assert len(tri) == 1, tri
    setpoly(tri[0], m([(-938.0, 5250.0), (QIN, 5250.0), (-843.9, 5315.0), (-938.0, 5315.0)]),
            "flat_cut")
    changed.append(("opening-rake quad", tri[0]))

json.dump(D, open(F, "w"))
print("FIX1 applied: %d pieces changed (2 extend, 2 corner-rake, 6 shift, 2 quad)" % len(changed))
