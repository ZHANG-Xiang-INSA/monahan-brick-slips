#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIX 2 - red walls: kill the over-wide closing joints (10.5-15 mm) left where the
re-tiled runs meet. Per course-segment (between corner cp / window-door jamb anchors):
- the segment's CUT piece(s) are EXTENDED (never a full 215, never a cp lap/half, cap 215)
  to absorb the surplus, fulls slide, every joint becomes exactly 10.0;
- all-full segments with sub-half-mm surplus per joint spread it evenly (joints < 10.45);
- all-full segments with no cut to extend keep the corner-grid anchored at the cp and the
  surplus moves into the adjacent window/door reveal gap (covered by the frame trim).
Deterministic; edits red_brick_placement_v7_stairfix.json in place."""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "..", "red_brick_placement_v7_stairfix.json")
R = json.load(open(F))
FIXED, EXT, DUMPS, SPREADS = 0, [], [], 0

def uspan(b):
    us = [p[0] for p in b["verts"]]
    return min(us), max(us)

def move(b, nu0, nu1):
    ou0, ou1 = uspan(b)
    for p in b["verts"]:
        p[0] = round(nu0 if abs(p[0]-ou0) < abs(p[0]-ou1) else nu1, 2)

for w, v in R.items():
    rows = collections.defaultdict(list)
    for b in v["bricks"]:
        rows[round(min(p[1] for p in b["verts"]), 2)].append(b)
    for z0, row in rows.items():
        row.sort(key=lambda b: uspan(b)[0])
        segs = [[row[0]]]
        for b in row[1:]:
            (segs.append([b]) if uspan(b)[0]-uspan(segs[-1][-1])[1] > 50 else segs[-1].append(b))
        for si, seg in enumerate(segs):
            sp = [uspan(b) for b in seg]
            gaps = [sp[i+1][0]-sp[i][1] for i in range(len(seg)-1)]
            bad = [g for g in gaps if 10.5 <= g <= 15.0]
            if not bad:
                continue
            L0, R0 = sp[0][0], sp[-1][1]
            sizes = [u1-u0 for u0, u1 in sp]
            n = len(gaps)
            E = R0 - L0 - sum(sizes) - 10.0*n
            assert E > -0.01, (w, z0, E)
            cuts = sorted([i for i, b in enumerate(seg)
                           if b.get("t") == "cut" and "cp" not in b],
                          key=lambda i: (-(215.0-sizes[i]), sp[i][0]))
            rem = E
            for i in cuts:
                take = min(rem, 215.0-sizes[i])
                if take > 0.01:
                    sizes[i] += take; rem -= take
                    EXT.append((w, z0, round(take, 2), round(sizes[i], 2)))
            spread, dump = 0.0, None
            if rem > 0.01:
                if rem/n < 0.45:
                    spread = rem/n; SPREADS += 1
                else:
                    cand = (["L"] if si > 0 else []) + (["R"] if si < len(segs)-1 else [])
                    # never dump on a side whose end piece is a corner cp (cp must not move)
                    cand = [c for c in cand
                            if "cp" not in (seg[0] if c == "L" else seg[-1])]
                    assert cand, (w, z0, "surplus with no opening to take it")
                    dump = ("L" if ("cp" in seg[-1] and "L" in cand) else
                            ("R" if ("cp" in seg[0] and "R" in cand) else cand[0]))
                    DUMPS.append((w, z0, dump, round(rem, 2)))
            if dump == "L":
                cur = R0
                for i in range(len(seg)-1, -1, -1):
                    move(seg[i], cur-sizes[i], cur); cur -= sizes[i]+10.0
            else:
                cur = L0 + (0.0 if dump != "R" else 0.0)
                for i, b in enumerate(seg):
                    move(b, cur, cur+sizes[i]); cur += sizes[i]+10.0+spread
            FIXED += len(bad)
            assert all(20.0-1e-6 <= s <= 215.0+1e-6 for s in sizes), (w, z0, sizes)

json.dump(R, open(F, "w"))
print("FIX2: %d over-wide joints fixed; %d cuts extended (%.1f mm total); "
      "%d segments spread<0.45; %d reveal-gap segments: %s"
      % (FIXED, len(EXT), sum(e[2] for e in EXT), SPREADS,
         len(DUMPS), collections.Counter(d[3] for d in DUMPS)))
