#!/usr/bin/env python3
"""Renders: (1) 3D before/after, (2) corner plan before/after grid, (3) dimensioned FL detail."""
import json,math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
BEF=json.load(open("_before_red_geometry.json"))
AFT=json.load(open("_after_red_geometry.json"))
WX,WY=11.513,13.604
def plan_piece(nm,base,nrm,t):
    """plan footprint polygon (xy) of a piece at a probe z, or None"""
    zs=[p[2] for p in base]
    if max(zs)-min(zs)<1e-6:   # horizontal base (old L): extruded UP; footprint = base poly
        return [(p[0],p[1]) for p in base], min(zs), min(zs)+t
    # vertical base: plan = segment +- normal*t
    xy=[(p[0],p[1]) for p in base]
    (x0,y0)=min(xy); (x1,y1)=max(xy)
    return [(x0,y0),(x1,y1),(x1+nrm[0]*t,y1+nrm[1]*t),(x0+nrm[0]*t,y0+nrm[1]*t)], min(zs), max(zs)
def at_z(BR,z):
    out=[]
    for nm,base,nrm,t in BR:
        pp=plan_piece(nm,base,nrm,t)
        if pp is None: continue
        poly,z0,z1=pp
        if z0-1e-9<=z<=z1+1e-9: out.append((nm,poly,base))
    return out
def colof(nm,poly):
    if nm=="Red_L": return "#ff33cc"
    if nm=="Red_CornerFlat":
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        L=max(max(xs)-min(xs),max(ys)-min(ys))
        return "#e6007e" if L>0.15 else "#7a3fd1"   # lap magenta / half purple
    return "#c0613f" if nm=="Red_Full" else "#e8a25f"
CORNERS=[("FRONT-LEFT C_NW^A_NE",0.0,0.0),("FRONT-RIGHT C_NW^B_SW",WX,0.0),("BACK-LEFT A_NE^D_SE",0.0,WY)]
# ---------------- 2. corner plan grid ----------------
fig,axes=plt.subplots(3,4,figsize=(17,12))
ZE,ZO=0.93,1.005   # even k=12, odd k=13
for r,(lbl,cx,cy) in enumerate(CORNERS):
    for c,(BR,ttl,z) in enumerate([(BEF,"BEFORE even (L)",ZE),(BEF,"BEFORE odd (L)",ZO),
                                   (AFT,"AFTER even (flats)",ZE),(AFT,"AFTER odd (flats)",ZO)]):
        ax=axes[r][c]
        for nm,poly,base in at_z(BR,z):
            xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
            if min(abs(min(xs)-cx),abs(max(xs)-cx))>0.75 and min(abs(min(ys)-cy),abs(max(ys)-cy))>0.75: continue
            if abs(min(xs)-cx)>0.9 and abs(max(xs)-cx)>0.9: continue
            if abs(min(ys)-cy)>0.9 and abs(max(ys)-cy)>0.9: continue
            ax.add_patch(MP(poly,closed=True,facecolor=colof(nm,poly),edgecolor="k",lw=0.5))
        ax.plot([cx],[cy],marker="+",color="k",ms=10)
        ax.set_xlim(cx-0.8,cx+0.8); ax.set_ylim(cy-0.8,cy+0.8); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        if r==0: ax.set_title(ttl,fontsize=11)
        if c==0: ax.set_ylabel(lbl,fontsize=10)
fig.suptitle("3 MONAHAN AVE - RED corners: one-piece L-slips (BEFORE) -> FLAT slip pairs (AFTER)\n"
             "AFTER: FULL 215 laps the arris (magenta) + HALF 107.5 butts it, set back 20 (purple); faces swap each course; 10 mm joints",fontsize=13)
plt.tight_layout(rect=[0,0,1,0.94]); plt.savefig("../flat_corners_before_after.png",dpi=110); plt.close()
print("saved flat_corners_before_after.png")
# ---------------- 1. 3D before/after ----------------
fig=plt.figure(figsize=(16,8))
for i,(BR,ttl) in enumerate([(BEF,"BEFORE: 117 one-piece L-corner slips (magenta)"),
                             (AFT,"AFTER: flat corners - 117 FULL 215 laps + 117 HALF 107.5 (magenta/purple)")]):
    ax=fig.add_subplot(1,2,i+1,projection="3d"); polys=[];cols=[]
    for nm,base,nrm,t in BR:
        zs=[p[2] for p in base]
        if max(zs)-min(zs)<1e-6:
            face=[(p[0],p[1],min(zs)+t) for p in base]
        else:
            face=[(p[0]+nrm[0]*t,p[1]+nrm[1]*t,p[2]+nrm[2]*t) for p in base]
        xy=[(p[0],p[1]) for p in base]
        polys.append(face); cols.append(colof(nm,xy))
    ax.add_collection3d(Poly3DCollection(polys,facecolors=cols,edgecolors="none"))
    ax.set_xlim(-1,12.5);ax.set_ylim(-1,14);ax.set_zlim(0,3.1)
    ax.view_init(elev=12,azim=-125); ax.set_box_aspect((12.5,14,4.2))
    ax.set_xticks([]);ax.set_yticks([]);ax.set_zticks([0,2.89]); ax.set_title(ttl,fontsize=11)
plt.tight_layout(); plt.savefig("../flat_corners_3d.png",dpi=115); plt.close()
print("saved flat_corners_3d.png")
# ---------------- 3. dimensioned FL detail ----------------
fig,axes=plt.subplots(1,2,figsize=(16,8))
def dim(ax,p0,p1,off,label,rot=0,fs=9,color="k"):
    (x0,y0),(x1,y1)=p0,p1; dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy)
    nx,ny=-dy/L,dx/L
    q0=(x0+nx*off,y0+ny*off); q1=(x1+nx*off,y1+ny*off)
    ax.annotate("",xy=q1,xytext=q0,arrowprops=dict(arrowstyle="<->",color=color,lw=0.9))
    ax.plot([x0,q0[0]],[y0,q0[1]],color=color,lw=0.5); ax.plot([x1,q1[0]],[y1,q1[1]],color=color,lw=0.5)
    ax.text((q0[0]+q1[0])/2+nx*0.012,(q0[1]+q1[1])/2+ny*0.012,label,fontsize=fs,ha="center",va="center",rotation=rot,color=color)
for c,(z,ttl) in enumerate([(ZE,"EVEN course k=12 (z0=900): FULL lap on C_NW, HALF on A_NE"),
                            (ZO,"ODD course k=13 (z0=975): FULL lap on A_NE, HALF on C_NW")]):
    ax=axes[c]
    for nm,poly,base in at_z(AFT,z):
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        if min(xs)>0.9 or min(ys)>0.9: continue
        ax.add_patch(MP(poly,closed=True,facecolor=colof(nm,poly),edgecolor="k",lw=0.7))
    ax.plot([0],[0],marker="+",color="k",ms=12)
    ax.annotate("structural corner (0,0)",xy=(0,0),xytext=(0.09,-0.12),fontsize=8,arrowprops=dict(arrowstyle="->",lw=0.6))
    ax.annotate("external arris (-20,-20)",xy=(-0.02,-0.02),xytext=(-0.02,-0.16),fontsize=8,ha="left",arrowprops=dict(arrowstyle="->",lw=0.6))
    if c==0:
        dim(ax,(-0.02,-0.02),(0.195,-0.02),-0.05,"FULL 215 x 65 (standard) - laps the arris")
        dim(ax,(-0.02,0.0),(0.0,0.0),0.14,"lap 20",rot=90,fs=8)
        dim(ax,(-0.02,0.0),(-0.02,0.1075),-0.05,"HALF 107.5 = 215/2\n(set back 20 from arris)",rot=90)
        dim(ax,(0.195,-0.02),(0.205,-0.02),-0.11,"10",fs=8)
        dim(ax,(-0.02,0.1075),(-0.02,0.1175),-0.11,"10",fs=8,rot=90)
        dim(ax,(0.205,-0.02),(0.420,-0.02),-0.17,"field 215 std (shifted -20)")
        dim(ax,(0.430,-0.02),(0.5425,-0.02),-0.11,"112.5",fs=8)
        dim(ax,(0.5525,-0.02),(0.665,-0.02),-0.11,"112.5 (closer pair)",fs=8)
        dim(ax,(-0.02,0.1175),(-0.02,0.3325),-0.11,"field 215 std (shifted +5)",rot=90)
        dim(ax,(-0.02,0.3425),(-0.02,0.5525),-0.17,"210 cut (was 215)",rot=90)
    else:
        dim(ax,(-0.02,-0.02),(-0.02,0.195),-0.05,"FULL 215 x 65 (standard) - laps the arris",rot=90)
        dim(ax,(0.0,-0.02),(0.1075,-0.02),-0.05,"HALF 107.5 = 215/2\n(set back 20 from arris)")
        dim(ax,(-0.02,0.195),(-0.02,0.205),-0.11,"10",fs=8,rot=90)
        dim(ax,(0.1075,-0.02),(0.1175,-0.02),-0.11,"10",fs=8)
        dim(ax,(-0.02,0.205),(-0.02,0.420),-0.17,"field 215 std (shifted -20)",rot=90)
        dim(ax,(-0.02,0.430),(-0.02,0.5425),-0.11,"112.5",rot=90,fs=8)
        dim(ax,(-0.02,0.5525),(-0.02,0.665),-0.11,"112.5 (closer pair)",rot=90,fs=8)
        dim(ax,(0.1175,-0.02),(0.3325,-0.02),-0.11,"field 215 std (shifted +5)")
        dim(ax,(0.3425,-0.02),(0.5525,-0.02),-0.17,"210 cut (was 215)")
    ax.set_xlim(-0.28,0.85); ax.set_ylim(-0.28,0.85); ax.set_aspect("equal")
    ax.set_title(ttl,fontsize=10); ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("FRONT-LEFT corner (C_NW ^ A_NE) - FLAT-CORNER PAIR, plan detail 1:1 (dims in mm)\n"
             "magenta = FULL 215 lap slip | purple = HALF 107.5 slip | red/orange = field (std/cut) | all bed joints 10 mm",fontsize=12)
plt.tight_layout(rect=[0,0,1,0.92]); plt.savefig("../flat_corner_detail_dimensioned.png",dpi=115); plt.close()
print("saved flat_corner_detail_dimensioned.png")
