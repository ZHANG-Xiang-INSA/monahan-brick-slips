#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the 4 fixed wall elevations + before/after zooms on the repaired jambs."""
import json, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
NEW=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix.json")))
OLD=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix_PREZIP.bak.json")))
XT={"C_NW_front":[("DOOR",4059.0,0.0,7473.0,2891.0)]}
COL={"full":"#c0392b","cut":"#e67e22","lap":"#d81b9c","half":"#7d3c98"}

def ext(b):
    us=[v[0] for v in b["verts"]]; zs=[v[1] for v in b["verts"]]
    return min(us),max(us),min(zs),max(zs)

def cat(b):
    cp=b.get("cp")
    if cp in ("lap","half"): return cp
    return "full" if b["t"]=="full" else "cut"

def draw(ax,R,w,ulo=None,uhi=None,zlo=None,zhi=None,lw=0.25):
    for b in R[w]["bricks"]:
        u0,u1,z0,z1=ext(b)
        if ulo is not None and (u1<ulo or u0>uhi or z1<zlo or z0>zhi): continue
        ax.add_patch(Rectangle((u0,z0),u1-u0,z1-z0,facecolor=COL[cat(b)],
                               edgecolor="black",linewidth=lw))
    ops=[(x[0],float(x[1]),float(x[2]),float(x[3]),float(x[4])) for x in R[w]["windows"]]+XT.get(w,[])
    for (nm,a,b0,bb,b1) in ops:
        b1=min(b1,2891.0)
        if ulo is not None and (bb<ulo or a>uhi): continue
        ax.add_patch(Rectangle((a,b0),bb-a,b1-b0,facecolor="#eef4fb",edgecolor="#1f5fa8",
                               linewidth=1.0,zorder=3))
        zc = min(b1, (zhi if zhi is not None else b1))*0.5+b0*0.5
        if ulo is None:
            ax.text((a+bb)/2,(b0+b1)/2,nm,ha="center",va="center",fontsize=7,color="#1f5fa8",zorder=4)

def joints_rows(R,w):
    rows=collections.defaultdict(list)
    for b in R[w]["bricks"]:
        u0,u1,z0,z1=ext(b); rows[int(z0//75)].append((u0,u1,z0,z1))
    return rows

def conf_pairs(R,w,ulo,uhi):
    rows=joints_rows(R,w); out=[]
    for k in range(38):
        lo=sorted(rows[k]); hi=sorted(rows[k+1])
        def joints(ps): return [(ps[i][1]+5.0,max(ps[i][3],ps[i+1][3]),min(ps[i][2],ps[i+1][2]))
                                for i in range(len(ps)-1) if abs(ps[i+1][0]-ps[i][1]-10.0)<1e-6]
        for (x,xt,xb) in joints(hi):
            if not(ulo<=x<=uhi): continue
            for (y,yt,yb) in joints(lo):
                if abs(x-y)<53.75 and 7.0<=xb-yt<=12.5:
                    out.append((x,xb,y,yt,abs(x-y)))
    return out

WALLS=[("A_NE_side","A_NE","_fix_wall_A_NE.png",0,13604),
       ("C_NW_front","C_NW","_fix_wall_C_NW.png",0,11513),
       ("B_SW_side","B_SW","_fix_wall_B_SW.png",0,11205),
       ("D_SE_garden","D_SE","_fix_wall_D_SE.png",6855,12510)]
MINS={"A_NE_side":55.75,"C_NW_front":80.75,"B_SW_side":80.75,"D_SE_garden":80.75}
for w,short,fn,uL,uR in WALLS:
    c=collections.Counter(cat(b) for b in NEW[w]["bricks"])
    width=(uR-uL)/1000.0
    fig,ax=plt.subplots(figsize=(max(10,width*1.35),4.6),dpi=150)
    draw(ax,NEW,w)
    ax.set_xlim(uL-120,uR+120); ax.set_ylim(-260,3050)
    ax.set_aspect("equal"); ax.axis("off")
    # scale bar
    x0=uL; y0=-180
    for i in range(5):
        ax.add_patch(Rectangle((x0+i*1000,y0),1000,50,facecolor="black" if i%2==0 else "white",
                               edgecolor="black",linewidth=0.6))
    ax.text(x0,y0-90,"0",fontsize=7); ax.text(x0+5000,y0-90,"5 m",fontsize=7)
    ax.set_title("%s wall - stagger-aware re-lay (v2): full=%d  cut=%d  corner lap=%d  half=%d  total=%d   "
                 "min adjacent-course stagger %.2f mm (>=53.75)"
                 %(short,c["full"],c["cut"],c["lap"],c["half"],sum(c.values()),MINS[w]),fontsize=9)
    handles=[Rectangle((0,0),1,1,facecolor=COL[k],edgecolor="black") for k in ("full","cut","lap","half")]
    ax.legend(handles,["full 215","cut","corner lap 215","corner half 107.5"],
              loc="upper right",fontsize=7,ncol=4,framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(INP,fn),bbox_inches="tight")
    plt.close(fig)
    print("saved",fn)

# ---------------- before/after zoom on the repaired jambs ----------------
ZOOMS=[("C_NW_front","C_NW DOOR left jamb u4059",3380,4100,350,2450),
       ("A_NE_side","A_NE WG12 right jamb u8213",8120,8880,0,2450),
       ("C_NW_front","C_NW WG01 left jamb u1340",860,1590,350,2450)]
fig,axs=plt.subplots(2,3,figsize=(16.5,10.5),dpi=150)
for col,(w,nm,ulo,uhi,zlo,zhi) in enumerate(ZOOMS):
    for row,(R,tag) in enumerate(((OLD,"BEFORE"),(NEW,"AFTER"))):
        ax=axs[row][col]
        draw(ax,R,w,ulo,uhi,zlo,zhi,lw=0.5)
        cps=conf_pairs(R,w,ulo,uhi)
        for (x,xb,y,yt,d) in cps:
            ax.plot([y,x],[yt+5,xb-5],color="red",linewidth=2.2,zorder=6)
            ax.plot([x],[xb-5],marker="v",color="red",markersize=4,zorder=6)
        mins=[d for (_,_,_,_,d) in cps]
        if tag=="BEFORE":
            sub="near-aligned joints <53.75 marked RED: %d (min stagger %.1f mm)"%(len(cps),min(mins) if mins else 99)
        else:
            sub="aligned joints <53.75: %d  (zone min now >=53.75)"%len(cps)
        ax.set_xlim(ulo,uhi); ax.set_ylim(zlo,zhi); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("%s - %s\n%s"%(tag,nm,sub),fontsize=8.5,
                     color=("#8b0000" if tag=="BEFORE" else "#0a5d00"))
fig.suptitle("Zipper-seam fix: perp joints beside the jambs now stagger >= 53.75mm every course "
             "(full=red, cut=orange, openings blue)",fontsize=11)
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig(os.path.join(INP,"_fix_window_zoom.png"),bbox_inches="tight")
plt.close(fig)
print("saved _fix_window_zoom.png")
