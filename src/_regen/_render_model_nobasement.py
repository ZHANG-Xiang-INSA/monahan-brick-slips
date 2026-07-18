import sys,types,collections
from unittest.mock import MagicMock
exec(open("_measure_corners.py").read().split("M=\"")[0])
import matplotlib;matplotlib.use("Agg");import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def build(model_path):
    src=open(model_path).read().replace('    def add(s,base,normal,t):\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',
       '    def add(s,base,normal,t):\n        _BR.append((s.n,[(p.x,p.y,p.z) for p in base],(normal.x,normal.y,normal.z),t))\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',1)
    import os;g={"_BR":[],"__file__":os.path.abspath(model_path),"__name__":"x"};exec(compile(src,model_path,"exec"),g);return g["_BR"]
def col(nm):return {"Red_Full":"#c0613f","Red_Cut":"#e0a060","Red_L":"#ff33cc","Black_Full":"#3a3a3a","Black_Cut":"#5a5a5a","Black_L":"#7a40a0"}.get(nm,"#888")
fig=plt.figure(figsize=(15,8))
for i,(mp_,ttl) in enumerate([("../../11_final_red_d_se_garden_position_fix/01_deliverables/combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py","FOLDER 11 (full, WITH basement)"),
                              ("../combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py","NEW REQUIREMENT (basement removed)")]):
    BR=build(mp_); ax=fig.add_subplot(1,2,i+1,projection="3d");polys=[];cols=[]
    for nm,base,nrm,t in BR:
        if nm.startswith("Red"):
            z0=min(p[2] for p in base)
            face=[(p[0],p[1],z0+t) for p in base] if nm=="Red_L" else [(p[0]+nrm[0]*t,p[1]+nrm[1]*t,p[2]+nrm[2]*t) for p in base]
        else:
            face=[(p[0]+nrm[0]*t,p[1]+nrm[1]*t,p[2]+nrm[2]*t) for p in base]
        polys.append(face);cols.append(col(nm))
    pc=Poly3DCollection(polys,facecolors=cols,edgecolors="none");ax.add_collection3d(pc)
    nbelow=sum(1 for nm,base,nrm,t in BR if nm.startswith("Red") and min(p[2] for p in base)<-0.001)
    ax.set_xlim(-1,12.5);ax.set_ylim(-1,14);ax.set_zlim(-2.9,3.0);ax.view_init(elev=8,azim=-128)
    ax.set_box_aspect((12.5,14,5.5));ax.set_xticks([]);ax.set_yticks([]);ax.set_zticks([-2.55,0,2.89])
    ax.set_title("%s\nred bricks below z=0: %d"%(ttl,nbelow),fontsize=10)
plt.tight_layout();plt.savefig("../model_basement_removed_3d.png",dpi=115);print("saved")
