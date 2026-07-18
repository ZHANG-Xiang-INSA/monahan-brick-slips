#!/usr/bin/env python3
"""BLACK canopy corners: one-piece L-slips -> FLAT slip pairs (New requirement 5).

Per arris per course the L (side leg s, front leg f; {s,f}={235,122.5} incl. the
20mm corner zone) becomes TWO wall-style flats (substrate-plane rect, th 20):
  SIDE piece  LAPS the arris: starts at front outer plane y=-370,
              length 215 (s=235 long) or 107.5 half (s=122.5 short).
  FRONT piece BUTTS the lap, set back 20 from the arris: length f-20
              (215 full or 102.5 cut) -> front-face coverage == old L exactly,
              so the gable-front field and both-corner closure joints are untouched.
Side-face field rows (all rows start at a corner; faces are only 720 deep) are
re-laid: full 215s from the corner (10mm joints), single cut at the house end.
Red and every other black face untouched.
"""
import json, os, collections
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
F=os.path.join(ROOT,"black_placement_fixed7.json")
SRC=os.path.join(ROOT,"black_placement_fixed7_PREFLATCORNER.bak.json")  # convert FROM backup (deterministic re-run)
d=json.load(open(SRC)); B=d["bricks"]
def bb(b):
    xs=[v[0] for v in b["verts"]]; ys=[v[1] for v in b["verts"]]; zs=[v[2] for v in b["verts"]]
    return (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))
def r3(v): return round(v+0.0,3)
ARR={ -1745.5:(-1725.5,[-1.0,0.0,0.0],+1), -1378.0:(-1398.0,[1.0,0.0,0.0],-1),
       1378.0:( 1398.0,[-1.0,0.0,0.0],+1),  1745.5:( 1725.5,[1.0,0.0,0.0],-1)}
def arrof(b):
    Bx=bb(b)
    for ax in ARR:
        if abs(Bx[0]-ax)<0.6 or abs(Bx[1]-ax)<0.6: return ax
    raise SystemExit("unknown arris")
keep=[]; Ls=[]; nside=0
for b in B:
    if b["cat"].startswith("L_corner"): Ls.append(b)
    elif b["face"]=="Bricks_Field" and abs(b["normal"][0])>0.9: nside+=1   # dropped, re-laid
    else: keep.append(b)
assert len(Ls)==272 and nside==816, (len(Ls),nside)
def rect_side(plane,nrm,y0,y1,z0,z1):
    return dict(cat="flat_full" if (abs((y1-y0)-215)<0.01 and abs((z1-z0)-65)<0.01) else "flat_cut",
        face="Bricks_Field",
        verts=[[r3(plane),r3(y0),r3(z0)],[r3(plane),r3(y1),r3(z0)],[r3(plane),r3(y1),r3(z1)],[r3(plane),r3(y0),r3(z1)]],
        normal=list(nrm),th_mm=20.0)
def rect_front(x0,x1,z0,z1):
    return dict(cat="flat_full" if (abs((x1-x0)-215)<0.01 and abs((z1-z0)-65)<0.01) else "flat_cut",
        face="Bricks_FrontFrame",
        verts=[[r3(x0),-350.0,r3(z0)],[r3(x1),-350.0,r3(z0)],[r3(x1),-350.0,r3(z1)],[r3(x0),-350.0,r3(z1)]],
        normal=[0.0,-1.0,0.0],th_mm=20.0)
new=[]; cnt=collections.Counter()
for L in sorted(Ls,key=lambda b:(arrof(b),bb(b)[4])):
    X=bb(L); ax=arrof(L); plane,nrm,dirx=ARR[ax]
    z0=X[4]; h=L["th_mm"]; s=X[3]-X[2]; f=X[1]-X[0]
    assert abs(z0-round(z0/75)*75)<0.01 and h in (65.0,46.0,50.0)
    assert {round(s,1),round(f,1)}=={235.0,122.5}, (s,f)
    assert abs(X[2]+370)<0.01                       # side leg starts at front outer plane
    Lside=215.0 if s>200 else 107.5
    Lfront=f-20.0                                   # 215 or 102.5 -> old front coverage preserved
    new.append(rect_side(plane,nrm,-370.0,-370.0+Lside,z0,z0+h)); cnt["corner_side_%g"%Lside]+=1
    x0,x1=(plane,plane+dirx*Lfront) if dirx>0 else (plane+dirx*Lfront,plane)
    new.append(rect_front(x0,x1,z0,z0+h)); cnt["corner_front_%g"%Lfront]+=1
    near=-370.0+Lside+10.0                          # field: first slip butts corner, 10mm joint
    while 350.0-near>215.0+0.01:
        new.append(rect_side(plane,nrm,near,near+215.0,z0,z0+h)); near+=225.0; cnt["field_full"]+=1
    tail=350.0-near
    assert 10.0<tail<=215.0, tail
    new.append(rect_side(plane,nrm,near,350.0,z0,z0+h)); cnt["field_tail_%g"%tail]+=1
d["bricks"]=keep+new
json.dump(d,open(F,"w"))
c=collections.Counter(b["cat"] for b in d["bricks"])
print("converted: L->0, new pieces",len(new),dict(cnt))
print("cats:",dict(c),"total",len(d["bricks"]))
