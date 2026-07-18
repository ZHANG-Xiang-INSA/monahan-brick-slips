#!/usr/bin/env python3
"""Dimensioned FL corner detail - clean layout (horizontal dims below, vertical dims left)."""
import json,math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
AFT=json.load(open("_after_red_geometry.json"))
def plan_piece(nm,base,nrm,t):
    zs=[p[2] for p in base]
    xy=[(p[0],p[1]) for p in base]
    (x0,y0)=min(xy); (x1,y1)=max(xy)
    return [(x0,y0),(x1,y1),(x1+nrm[0]*t,y1+nrm[1]*t),(x0+nrm[0]*t,y0+nrm[1]*t)],min(zs),max(zs)
def at_z(BR,z):
    out=[]
    for nm,base,nrm,t in BR:
        poly,z0,z1=plan_piece(nm,base,nrm,t)
        if z0-1e-9<=z<=z1+1e-9: out.append((nm,poly))
    return out
def colof(nm,poly):
    if nm=="Red_CornerFlat":
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        return "#e6007e" if max(max(xs)-min(xs),max(ys)-min(ys))>0.15 else "#7a3fd1"
    return "#c0613f" if nm=="Red_Full" else "#e8a25f"
def hdim(ax,x0,x1,y,label,fs=8.5):
    ax.annotate("",xy=(x1,y),xytext=(x0,y),arrowprops=dict(arrowstyle="<->",lw=0.8))
    ax.plot([x0,x0],[y,-0.02],lw=0.4,color="0.4",ls=":"); ax.plot([x1,x1],[y,-0.02],lw=0.4,color="0.4",ls=":")
    ax.text((x0+x1)/2,y-0.016,label,fontsize=fs,ha="center",va="top")
def vdim(ax,y0,y1,x,label,fs=8.5):
    ax.annotate("",xy=(x,y1),xytext=(x,y0),arrowprops=dict(arrowstyle="<->",lw=0.8))
    ax.plot([x,-0.02],[y0,y0],lw=0.4,color="0.4",ls=":"); ax.plot([x,-0.02],[y1,y1],lw=0.4,color="0.4",ls=":")
    ax.text(x-0.016,(y0+y1)/2,label,fontsize=fs,ha="right",va="center",rotation=90)
fig,axes=plt.subplots(1,2,figsize=(17,8.6))
ZE,ZO=0.93,1.005
for c,(z,ttl) in enumerate([(ZE,"EVEN course (k=12, z0=900): FULL lap on C_NW  |  HALF on A_NE"),
                            (ZO,"ODD course (k=13, z0=975): FULL lap on A_NE  |  HALF on C_NW")]):
    ax=axes[c]
    for nm,poly in at_z(AFT,z):
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        if min(xs)>0.95 or min(ys)>0.95: continue
        ax.add_patch(MP(poly,closed=True,facecolor=colof(nm,poly),edgecolor="k",lw=0.7))
    ax.plot([0],[0],marker="+",color="k",ms=11)
    ax.annotate("structural corner (0,0)",xy=(0,0),xytext=(0.28,0.30),fontsize=8,
                arrowprops=dict(arrowstyle="->",lw=0.7))
    ax.annotate("external arris (-20,-20)\nlap end FLUSH here",xy=(-0.02,-0.02),xytext=(0.28,0.21),fontsize=8,
                arrowprops=dict(arrowstyle="->",lw=0.7))
    if c==0:
        # C_NW horizontal (skin y in [-20,0]): lap -20..195 | b1 205..420 | pair 430..542.5 552.5..665 | b3 675..890
        hdim(ax,-0.020,0.195,-0.150,"FULL lap 215 x 65 (STANDARD)")
        hdim(ax,0.205,0.420,-0.075,"215 std (b1, shifted -20)")
        hdim(ax,0.430,0.5425,-0.150,"112.5")
        hdim(ax,0.5525,0.665,-0.225,"112.5  (closer pair, was one 215)")
        hdim(ax,0.675,0.890,-0.075,"215 std (unchanged)")
        hdim(ax,0.195,0.205,-0.260,"joints 10 (typ.)")
        # A_NE vertical (skin x in [-20,0]): half 0..107.5 | b1 117.5..332.5 | trim 342.5..552.5 | 562.5..
        vdim(ax,0.0,0.1075,-0.150,"HALF 107.5 = 215/2\n(set back 20 from arris)")
        vdim(ax,0.1175,0.3325,-0.075,"215 std (b1, shifted +5)")
        vdim(ax,0.3425,0.5525,-0.150,"210 cut (b2, was 215)")
        vdim(ax,0.5625,0.7775,-0.075,"215 std (unchanged)")
        ax.annotate("lap projects 20 past the corner:\nits back butts the HALF slip's end",
                    xy=(-0.01,-0.01),xytext=(0.28,0.12),fontsize=8,arrowprops=dict(arrowstyle="->",lw=0.7))
    else:
        vdim(ax,-0.020,0.195,-0.150,"FULL lap 215 x 65 (STANDARD)")
        vdim(ax,0.205,0.420,-0.075,"215 std (b1, shifted -20)")
        vdim(ax,0.430,0.5425,-0.150,"112.5")
        vdim(ax,0.5525,0.665,-0.225,"112.5  (closer pair, was one 215)")
        vdim(ax,0.675,0.890,-0.075,"215 std (unchanged)")
        hdim(ax,0.0,0.1075,-0.150,"HALF 107.5 = 215/2\n(set back 20 from arris)")
        hdim(ax,0.1175,0.3325,-0.075,"215 std (b1, shifted +5)")
        hdim(ax,0.3425,0.5525,-0.150,"210 cut (b2, was 215)")
        hdim(ax,0.5625,0.7775,-0.075,"215 std (unchanged)")
        ax.annotate("faces SWAP each course\n-> staggered quoin, no\ncontinuous vertical joint",
                    xy=(-0.01,0.19),xytext=(0.28,0.12),fontsize=8,arrowprops=dict(arrowstyle="->",lw=0.7))
    ax.set_xlim(-0.36,0.98); ax.set_ylim(-0.36,0.98); ax.set_aspect("equal")
    ax.set_title(ttl,fontsize=10.5); ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("FRONT-LEFT RED corner (C_NW ^ A_NE) - FLAT-CORNER PAIR plan detail (mm) - same rule at FRONT-RIGHT & BACK-LEFT\n"
             "magenta = FULL 215 lap slip (standard brick) | purple = HALF 107.5 slip | red/orange = field std/cut | bed & perp joints 10 mm | slip thickness 20",
             fontsize=12)
plt.tight_layout(rect=[0,0,1,0.91]); plt.savefig("../flat_corner_detail_dimensioned.png",dpi=120); plt.close()
print("saved")
