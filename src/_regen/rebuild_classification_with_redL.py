#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FLAT-CORNER classifier (New requirement 2): the red one-piece L-corner slips are GONE.
The 3 red corners are covered by PAIRS of FLAT slips (117 full 215 lapping the arris +
117 half 107.5 butting them, markers "cp":"lap"/"half"), which now live directly in
red_brick_placement_v7_stairfix.json and are classified like any other flat/cut slip.
Black (incl. its 272 L-corners) untouched. Writes brick_types.json."""
import json,math,collections,os
HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
RED=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix.json")))
BLK=json.load(open(os.path.join(INP,"black_placement_fixed7.json")))["bricks"]
TOL=5.0; FULL_W,FULL_H=215.0,65.0
def parea(pts):
    a=0.0
    for i in range(len(pts)):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%len(pts)]; a+=x1*y2-x2*y1
    return abs(a)/2.0
def dedup(pts):
    out=[]
    for p in pts:
        if not out or abs(p[0]-out[-1][0])>0.5 or abs(p[1]-out[-1][1])>0.5: out.append((round(p[0],1),round(p[1],1)))
    if len(out)>1 and abs(out[0][0]-out[-1][0])<0.5 and abs(out[0][1]-out[-1][1])<0.5: out.pop()
    return out
def edges_ang(pts):
    es=[]; ang=0.0
    for i in range(len(pts)):
        x0,y0=pts[i]; x1,y1=pts[(i+1)%len(pts)]; dx=x1-x0; dy=y1-y0; L=math.hypot(dx,dy)
        if L<1: continue
        es.append(round(L))
        if abs(dx)>3 and abs(dy)>3: ang=max(ang,round(math.degrees(math.atan2(abs(dy),abs(dx)))))
    return es,ang
def shape_family(pts):
    n=len(pts)
    if n==3: return "triangle"
    if n!=4: return "polygon"
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; bb=(max(xs)-min(xs))*(max(ys)-min(ys)); ar=parea(pts)
    if bb<1: return "degenerate"
    if abs(ar-bb)<0.04*bb: return "rectangle"
    vmn=min(ys);vmx=max(ys); bot=[p for p in pts if abs(p[1]-vmn)<2]; top=[p for p in pts if abs(p[1]-vmx)<2]
    if len(bot)<2 or len(top)<2: return "angled"
    b0=min(p[0] for p in bot);b1=max(p[0] for p in bot);t0=min(p[0] for p in top);t1=max(p[0] for p in top)
    Ls=abs(t0-b0)>4; Rs=abs(t1-b1)>4
    if Ls and Rs: return "parallelogram" if (t0-b0)*(t1-b1)>0 and abs((t0-b0)-(t1-b1))<8 else "trapezoid"
    return "right-trapezoid"
def inplane(x):
    n=x["normal"]
    def crs(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    def dot(a,b):return sum(a[i]*b[i] for i in range(3))
    def unit(a):
        L=math.sqrt(dot(a,a)); return (a[0]/L,a[1]/L,a[2]/L) if L>1e-9 else a
    if abs(n[1])>0.9: U,V=(1,0,0),(0,0,1)
    elif abs(n[0])>0.9: U,V=(0,1,0),(0,0,1)
    else:
        U=unit(crs(n,(0,0,1))); V=unit(crs(U,n))
        if V[2]<0: V=(-V[0],-V[1],-V[2])
    return [(dot(v,U),dot(v,V)) for v in x["verts"]]
bricks=[]
for wall,v in RED.items():
    if not isinstance(v,dict) or "bricks" not in v: continue
    for br in v["bricks"]:
        pts=dedup([(p[0],p[1]) for p in br["verts"]]); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        fam=shape_family(pts); es,ang=edges_ang(pts)
        bricks.append(dict(colour="Red",region=wall,fam=fam,w=round(max(xs)-min(xs)),h=round(max(ys)-min(ys)),
                           area=round(parea(pts)),edges=es,angle=ang,pts=pts))
# ---- (red corner L generation REMOVED - flat corner pairs come from the placement) ----
# ---- BLACK ----
for x in BLK:
    if x["cat"].startswith("L_corner"):
        pts=dedup([(p[0],p[1]) for p in x["verts"]]); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        legX=max(xs)-min(xs); legY=max(ys)-min(ys); stretcher=round(max(legX,legY)-20); header=round(min(legX,legY)-20)
        comp="canopy front-left corner" if min(xs)<0 else "canopy front-right corner"
        bricks.append(dict(colour="Black",region=comp,fam="L",w=stretcher,h=65,area=round((stretcher+header)*65),
                           edges=[stretcher,header,65],angle=0.0,Lreturn=header,pts=pts)); continue
    uv=dedup(inplane(x)); xs=[p[0] for p in uv]; ys=[p[1] for p in uv]
    role=("canopy side wall" if abs(x["normal"][0])>0.9 else "canopy gable front" if abs(x["normal"][1])>0.9 else "canopy pitched slope")
    fam=shape_family(uv); es,ang=edges_ang(uv)
    bricks.append(dict(colour="Black",region="canopy: "+role,fam=fam,w=round(max(xs)-min(xs)),h=round(max(ys)-min(ys)),
                       area=round(parea(uv)),edges=es,angle=ang,pts=uv))
# ---- cluster ----
def abk(a): return 0 if a<5 else int(round(a))
groups=collections.defaultdict(list)
for b in bricks: groups[(b["colour"],b["fam"],abk(b["angle"]),(b.get("Lreturn") if b["fam"]=="L" else None),
        (b["fam"]=="rectangle" and abs(b["w"]-FULL_W)<=3 and abs(b["h"]-FULL_H)<=3))].append(b)
clusters=[]
for key,gb in groups.items():
    gb.sort(key=lambda b:-b["area"]); cl=[]
    for b in gb:
        placed=False
        for c in cl:
            if abs(b["w"]-c["cw"])<=TOL and abs(b["h"]-c["ch"])<=TOL:
                c["items"].append(b); n=len(c["items"]); c["cw"]=(c["cw"]*(n-1)+b["w"])/n; c["ch"]=(c["ch"]*(n-1)+b["h"])/n; placed=True; break
        if not placed: cl.append(dict(cw=b["w"],ch=b["h"],items=[b],key=key))
    clusters+=cl
def kindof(c):
    fam=c["key"][1]
    if fam=="L": return "L-corner"
    if fam=="rectangle": return "standard" if abs(c["cw"]-FULL_W)<=3 and abs(c["ch"]-FULL_H)<=3 else "cut"
    return "angled"
ordk={"standard":0,"cut":1,"angled":2,"L-corner":3}
clusters.sort(key=lambda c:(0 if c["key"][0]=="Red" else 1, ordk[kindof(c)], -max(b["area"] for b in c["items"])))
types=[]
for i,c in enumerate(clusters,1):
    its=c["items"]; rep=max(its,key=lambda b:b["area"]); fam=c["key"][1]; kind=kindof(c)
    ox=min(p[0] for p in rep["pts"]); oy=min(p[1] for p in rep["pts"]); outline=[[round(p[0]-ox,1),round(p[1]-oy,1)] for p in rep["pts"]]
    shape={"rectangle":("standard flat" if kind=="standard" else "cut flat"),"L":"L-shaped corner",
           "triangle":"triangular cut","trapezoid":"trapezoid","right-trapezoid":"right-trapezoid",
           "parallelogram":"parallelogram","angled":"angled cut","polygon":"polygon cut","degenerate":"sliver"}.get(fam,fam)
    types.append(dict(type_id="B%02d"%i,colour=c["key"][0],kind=kind,shape=shape,
        w=round(c["cw"]),h=round(c["ch"]),angle=rep["angle"] if kind=="angled" else 0.0,edges=rep["edges"],outline=outline,
        qty=len(its),area_per=round(sum(b["area"] for b in its)/len(its)),total_area=sum(b["area"] for b in its),
        regions=sorted(set(b["region"] for b in its)),region_qty=dict(collections.Counter(b["region"] for b in its)),
        size_range=[round(min(b["w"] for b in its)),round(max(b["w"] for b in its)),round(min(b["h"] for b in its)),round(max(b["h"] for b in its))]))
out=dict(types=types,n_bricks=len(bricks),tol_mm=TOL,
         red_area=sum(b["area"] for b in bricks if b["colour"]=="Red"),black_area=sum(b["area"] for b in bricks if b["colour"]=="Black"))
json.dump(out,open(os.path.join(INP,"brick_types.json"),"w"))
print("bricks:",len(bricks),"-> Brick Type IDs:",len(types))
redL_types=[t for t in types if t["colour"]=="Red" and t["kind"]=="L-corner"]
print("red L types:",[(t["type_id"],t["qty"],t["region_qty"]) for t in redL_types])
print("black L types:",[(t["type_id"],t["qty"]) for t in types if t["colour"]=="Black" and t["kind"]=="L-corner"])
print("red %.2f m2 | black %.2f m2 | total %.2f m2"%(out["red_area"]/1e6,out["black_area"]/1e6,(out["red_area"]+out["black_area"])/1e6))