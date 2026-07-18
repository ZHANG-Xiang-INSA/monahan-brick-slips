import sys,types,math
from unittest.mock import MagicMock
class Vector:
    __slots__=("x","y","z")
    def __init__(s,t=(0,0,0)):
        t=list(t)+[0,0,0]; s.x,s.y,s.z=float(t[0]),float(t[1]),float(t[2])
    def __add__(s,o): return Vector((s.x+o.x,s.y+o.y,s.z+o.z))
    def __sub__(s,o): return Vector((s.x-o.x,s.y-o.y,s.z-o.z))
    def __mul__(s,k): return Vector((s.x*k,s.y*k,s.z*k))
    __rmul__=__mul__
    def __truediv__(s,k): return Vector((s.x/k,s.y/k,s.z/k))
    def __neg__(s): return Vector((-s.x,-s.y,-s.z))
    def dot(s,o): return s.x*o.x+s.y*o.y+s.z*o.z
    def cross(s,o): return Vector((s.y*o.z-s.z*o.y,s.z*o.x-s.x*o.z,s.x*o.y-s.y*o.x))
    @property
    def length(s): return (s.x*s.x+s.y*s.y+s.z*s.z)**0.5
    def normalized(s):
        L=s.length; return Vector((s.x/L,s.y/L,s.z/L)) if L>1e-12 else Vector((0,0,0))
    def copy(s): return Vector((s.x,s.y,s.z))
    def __iter__(s): return iter((s.x,s.y,s.z))
    def __getitem__(s,i): return (s.x,s.y,s.z)[i]
    def to_track_quat(s,*a):
        class Q:
            def to_euler(self): return (0.0,0.0,0.0)
        return Q()
mu=types.ModuleType("mathutils"); mu.Vector=Vector; sys.modules["mathutils"]=mu
bpy=MagicMock()
for a in ("meshes","materials","cameras","lights","collections","objects","curves","worlds","images","node_groups"):
    m=MagicMock(); m.__iter__=lambda self=m: iter([]); setattr(bpy.data,a,m)
bpy.data.filepath=""; sys.modules["bpy"]=bpy; sys.modules["bmesh"]=MagicMock()
M="../combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py"
src=open(M).read()
src=src.replace('    def add(s,base,normal,t):\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',
                '    def add(s,base,normal,t):\n        _BR.append((s.n,[(p.x,p.y,p.z) for p in base],(normal.x,normal.y,normal.z)))\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',1)
import os; g={"_BR":[],"__file__":os.path.abspath(M),"__name__":"x"}; exec(compile(src,M,"exec"),g)
BR=g["_BR"]
WX,WY=11.513,13.604
# pick a ground-floor course z ~ 1.0 ; for each corner, list field-brick footprints + L footprints near corner
def at_course(z):
    out=[]
    for nm,base,nrm in BR:
        if not nm.startswith("Red"): continue
        zs=[p[2] for p in base]
        if min(zs)<=z<=max(zs):
            xs=[p[0] for p in base]; ys=[p[1] for p in base]
            out.append((nm,min(xs),max(xs),min(ys),max(ys)))
    return out
def near(items,cx,cy,r=0.35):
    return [it for it in items if abs((it[1]+it[2])/2-cx)<r and abs((it[3]+it[4])/2-cy)<r]
for label,(cx,cy) in [("FRONT-LEFT (0,0) C^A [reference, said OK]",(0,0)),
                      ("FRONT-RIGHT (WX,0) B^C [void]",(WX,0)),
                      ("BACK-LEFT (0,WY) A^D [ordinary]",(0,WY))]:
    it=near(at_course(1.0),cx,cy)
    fld=[i for i in it if i[0]!="Red_L"]; L=[i for i in it if i[0]=="Red_L"]
    print("="*60); print(label,"  @z=1.0")
    print(" field bricks (nm,xmin,xmax,ymin,ymax) within 350mm of corner:")
    for i in sorted(fld,key=lambda q:(q[1],q[3])): print("   %s x[%.3f,%.3f] y[%.3f,%.3f]"%(i[0],i[1],i[2],i[3],i[4]))
    print(" L-slips:")
    for i in L: print("   Red_L x[%.3f,%.3f] y[%.3f,%.3f]"%(i[1],i[2],i[3],i[4]))
