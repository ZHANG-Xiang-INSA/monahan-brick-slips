#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-audit of red walls after _fix_red_joints.py: 0 joints in 10.5-15 mm (openings excluded),
all in-course joints 9.4-10.49, 0 overlaps, pieces 20-215, adjacent-course stagger >= 53.75,
cp lap/half pieces byte-identical to the backup."""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "red_brick_placement_v7_stairfix.json")))
B = json.load(open(os.path.join(HERE, "..", "red_brick_placement_v7_stairfix_PREJOINTFIX.bak.json")))

def uspan(b):
    us = [p[0] for p in b["verts"]]
    return min(us), max(us)

bad, over, minstag, npieces, sizefail = [], 0, 1e9, 0, []
for w, v in R.items():
    rows = collections.defaultdict(list)
    for b in v["bricks"]:
        rows[round(min(p[1] for p in b["verts"]), 2)].append(b)
        npieces += 1
        u0, u1 = uspan(b)
        if not (20.0-0.01 <= u1-u0 <= 215.0+0.01):
            sizefail.append((w, round(u1-u0, 2)))
    zs = sorted(rows)
    joints = {}
    for z0 in zs:
        row = sorted(rows[z0], key=lambda b: uspan(b)[0])
        js = []
        for a, c in zip(row, row[1:]):
            g = uspan(c)[0]-uspan(a)[1]
            if g < -0.01: over += 1
            if g <= 50:
                js.append((uspan(a)[1]+uspan(c)[0])/2.0)
                if 10.5 <= g <= 15.0: bad.append((w, z0, round(uspan(a)[1], 1), round(g, 2)))
                elif not (9.4 <= g <= 10.49): bad.append((w, z0, round(uspan(a)[1], 1), round(g, 2)))
        joints[z0] = js
    for z0, z1 in zip(zs, zs[1:]):
        if z1-z0 > 75.01: continue
        for j in joints[z0]:
            near = [abs(j-k) for k in joints[z1]]
            if near: minstag = min(minstag, min(near))
    # cp integrity vs backup
    cpn = [json.dumps(b, sort_keys=True) for b in v["bricks"] if "cp" in b]
    cpo = [json.dumps(b, sort_keys=True) for b in B[w]["bricks"] if "cp" in b]
    assert sorted(cpn) == sorted(cpo), (w, "cp pieces changed!")
red_tot = {w: len(v["bricks"]) for w, v in R.items()}
print("red audit: joints-out-of-range=%d overlaps=%d min-stagger=%.2f size-fails=%d "
      "pieces=%d per-wall=%s" % (len(bad), over, minstag, len(sizefail), npieces, red_tot))
if bad[:6]: print("  bad sample:", bad[:6])
print("RED AUDIT %s" % ("PASS" if not bad and not over and minstag >= 53.75 and not sizefail
                        else "FAIL"))
