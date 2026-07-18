import sys,types,collections
from unittest.mock import MagicMock
exec(open("_measure_corners.py").read().split("M=\"")[0])
NRabs=r"C:\Users\Stras\Documents\Claude\Projects\Brick slip PJ 001\New requirement"
SBabs="/sessions/tender-cool-ritchie/mnt/Brick slip PJ 001/New requirement"
M="../combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py"
base=open(M).read().replace('    def add(s,base,normal,t):\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',
   '    def add(s,base,normal,t):\n        _BR.append((s.n,min(p.z for p in base)))\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',1)
import os
def run(label, set_file, sub_sandbox):
    src=base
    if sub_sandbox: src=src.replace(NRabs, SBabs)  # so the Windows abs path resolves in this Linux sandbox
    g={"_BR":[],"__name__":"x"}
    if set_file: g["__file__"]=os.path.abspath(M)
    exec(compile(src,M,"exec"),g)
    bc=collections.Counter(n for n,z in g["_BR"])
    nred=sum(v for k,v in bc.items() if k.startswith("Red")); nblk=sum(v for k,v in bc.items() if k.startswith("Black"))
    nbelow=sum(1 for n,z in g["_BR"] if n.startswith("Red") and z<-0.001)
    print("  [%s] total=%d red=%d black=%d redL=%d | red z<0 =%d"%(label,nred+nblk,nred,nblk,bc.get("Red_L",0),nbelow))
print("VERIFY model input-loading robustness:")
run("WITH __file__ (blender --python)", True, False)
run("WITHOUT __file__ (Text Editor; abs-path-first)", False, True)
