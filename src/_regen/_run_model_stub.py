#!/usr/bin/env python3
"""Headless model build: bpy/mathutils stub, exec the combined model, read printed cnt."""
import sys, types, math, os
from unittest.mock import MagicMock

class Vector:
    __slots__ = ("x", "y", "z")
    def __init__(s, t=(0, 0, 0)):
        t = list(t) + [0, 0, 0]
        s.x, s.y, s.z = float(t[0]), float(t[1]), float(t[2])
    def __add__(s, o): return Vector((s.x+o.x, s.y+o.y, s.z+o.z))
    def __sub__(s, o): return Vector((s.x-o.x, s.y-o.y, s.z-o.z))
    def __mul__(s, k): return Vector((s.x*k, s.y*k, s.z*k))
    __rmul__ = __mul__
    def __truediv__(s, k): return Vector((s.x/k, s.y/k, s.z/k))
    def __neg__(s): return Vector((-s.x, -s.y, -s.z))
    def dot(s, o): return s.x*o.x + s.y*o.y + s.z*o.z
    def cross(s, o): return Vector((s.y*o.z-s.z*o.y, s.z*o.x-s.x*o.z, s.x*o.y-s.y*o.x))
    @property
    def length(s): return (s.x*s.x + s.y*s.y + s.z*s.z) ** 0.5
    def normalized(s):
        L = s.length
        return Vector((s.x/L, s.y/L, s.z/L)) if L > 1e-12 else Vector((0, 0, 0))
    def copy(s): return Vector((s.x, s.y, s.z))
    def __iter__(s): return iter((s.x, s.y, s.z))
    def __getitem__(s, i): return (s.x, s.y, s.z)[i]
    def to_track_quat(s, *a):
        class Q:
            def to_euler(self): return (0.0, 0.0, 0.0)
        return Q()

mu = types.ModuleType("mathutils"); mu.Vector = Vector; sys.modules["mathutils"] = mu
bpy = MagicMock()
for a in ("meshes", "materials", "cameras", "lights", "collections", "objects",
          "curves", "worlds", "images", "node_groups"):
    m = MagicMock(); m.__iter__ = lambda self=m: iter([]); setattr(bpy.data, a, m)
bpy.data.filepath = ""; sys.modules["bpy"] = bpy; sys.modules["bmesh"] = MagicMock()

M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py")
src = open(M).read()
g = {"__file__": os.path.abspath(M), "__name__": "__main__"}
exec(compile(src, M, "exec"), g)
c = g["cnt"]
red = c["red_full"]+c["red_cut"]+c["red_corner_lap"]+c["red_corner_half"]+c["red_L_full"]+c["red_L_cut"]
blk = c["black_full"]+c["black_cut"]+c["black_L_full"]+c["black_L_cut"]
print("STUB-CHECK red=%d black=%d GRAND=%d" % (red, blk, red+blk))
# expectations derived from the live placement json (v2 stagger-aware re-lay)
import json as _json
_R = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                  "red_brick_placement_v7_stairfix.json")))
_W = ["A_NE_side", "C_NW_front", "B_SW_side", "D_SE_garden"]
_exp_full = sum(1 for w in _W for b in _R[w]["bricks"]
                if b["t"] == "full" and b.get("cp") not in ("lap", "half"))
_exp_cut  = sum(1 for w in _W for b in _R[w]["bricks"]
                if b["t"] == "cut" and b.get("cp") not in ("lap", "half"))
_exp_lap  = sum(1 for w in _W for b in _R[w]["bricks"] if b.get("cp") == "lap")
_exp_half = sum(1 for w in _W for b in _R[w]["bricks"] if b.get("cp") == "half")
assert c["red_full"] == _exp_full and c["red_cut"] == _exp_cut, (dict(c), _exp_full, _exp_cut)
assert c["red_corner_lap"] == _exp_lap == 117 and c["red_corner_half"] == _exp_half == 117, dict(c)
assert c["red_L_full"] == 0 and c["red_L_cut"] == 0, dict(c)
assert blk == 1733 and c["black_L_full"]+c["black_L_cut"] == 0 and red == _exp_full+_exp_cut+_exp_lap+_exp_half, (red, blk)
print("STUB-CHECK PASS")
