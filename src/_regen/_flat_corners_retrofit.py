#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FLAT-CORNER RETROFIT (New requirement 2): replace the 3 red one-piece L-corners with
PAIRS of FLAT slips, editing red_brick_placement_v7_stairfix.json IN PLACE.

Per corner, per course k=0..38 (parity lo=(k%2==0), exactly like the old L legs):
  LONG face (had the 215 leg)  -> FULL 215xH flat slip LAPPING the arris:
        u from (corner - s*20) to (corner + s*195); outer end flush with the
        adjacent wall's outer plane (arris covered).
  SHORT face (had the 102.5 leg) -> HALF 107.5xH flat slip BUTTING the side of the
        lapping full slip, set back BRICK_T=20 from the (external) arris:
        u from corner to (corner + s*107.5).
  H = min(65, 2891-75k); k=38 -> 41 (>= MIN_CUT 20, kept).
Field re-anchor (ONLY the 2 corner-adjacent bricks per face per course):
  LONG face : brick1 shifts toward the corner by dL = old_setback-205 (20/21/21.5)
              so it butts the lap slip with a 10 mm joint; brick2 (full 215) is
              REPLACED by a pair of equal half-bats (215+dL-10)/2 each (closer pair)
              so brick3 onwards is untouched.
  SHORT face: brick1 shifts away from the corner by dS = 117.5-old_setback (5/4/3.5)
              to butt the half slip with a 10 mm joint; brick2 is trimmed by dS at
              its corner-facing edge (215 -> 210/211/211.5 cut). Rest untouched.
Markers on new/changed pieces: "corner": FL|FR|BL, "cp": lap|half|pair|trim (b1 kept
unmarked apart from "cp":"b1shift" note field removed – b1 keeps original dict, only verts move).
"""
import json,os,collections,math
HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
SRC=os.path.join(INP,"red_brick_placement_v7_stairfix.json")
R=json.load(open(SRC))
CP=75.0; FF=2891.0; BH=65.0; T=20.0; MINCUT=20.0
LAP_IN=195.0   # lap slip inner-end setback  (215 - 20)
HALF=107.5     # half slip = 215/2 exactly
SB_L=205.0     # new long-side field setback  (195+10)
SB_S=117.5     # new short-side field setback (107.5+10)
# corner, longwall(on even), cu, s, shortwall(on even), cu2, s2
CORNERS=[("FL","C_NW_front",0.0,+1,"A_NE_side",13604.0,-1),
         ("FR","B_SW_side",0.0,+1,"C_NW_front",11513.0,-1),
         ("BL","A_NE_side",0.0,+1,"D_SE_garden",12510.0,-1)]
def bz(br):
    zs=[v[1] for v in br["verts"]]; return min(zs),max(zs)
def bu(br):
    us=[v[0] for v in br["verts"]]; return min(us),max(us)
def course_bricks(wall,k):
    out=[]
    for i,br in enumerate(R[wall]["bricks"]):
        z0,z1=bz(br)
        if abs(z0-k*CP)<1.0 and z1<=k*CP+66.0: out.append(i)
    return out
def near2(wall,k,cu,s):
    """the two bricks of course k nearest the corner (sorted by distance)"""
    ids=course_bricks(wall,k); d=[]
    for i in ids:
        u0,u1=bu(R[wall]["bricks"][i])
        cf=(u0 if s>0 else u1)                  # corner-facing edge
        dist=(cf-cu)*s
        if -1<dist<700: d.append((dist,i))
    d.sort(); return d
def shift_brick(wall,i,du):
    br=R[wall]["bricks"][i]
    br["verts"]=[[round(v[0]+du,4),v[1]] for v in br["verts"]]
def rectverts(u0,z0,u1,z1):
    return [[u0,z1],[u1,z1],[u1,z0],[u0,z0],[u0,z1]]
log=collections.Counter(); details=[]
newbr=collections.defaultdict(list); killed=collections.defaultdict(list)
for cn,wA,cuA,sA,wB,cuB,sB in CORNERS:
    k=0
    while k*CP<FF-1e-6:
        z0=k*CP; h=min(BH,FF-z0)
        if h<MINCUT: break
        lo=(k%2==0)
        (wL,cuL,sL)=(wA,cuA,sA) if lo else (wB,cuB,sB)   # LONG face this course
        (wS,cuS,sS)=(wB,cuB,sB) if lo else (wA,cuA,sA)   # SHORT face this course
        # ---- corner flat pair ----
        uu=sorted([cuL-sL*T, cuL+sL*LAP_IN])
        newbr[wL].append(dict(t=("full" if h>=BH-1e-6 else "cut"),
            verts=rectverts(uu[0],z0,uu[1],z0+h),corner=cn,cp="lap"))
        uu=sorted([cuS, cuS+sS*HALF])
        newbr[wS].append(dict(t="cut",verts=rectverts(uu[0],z0,uu[1],z0+h),corner=cn,cp="half"))
        log["lap"]+=1; log["half"]+=1
        # ---- LONG face field: b1 shift + b2 -> closer pair ----
        nb=near2(wL,k,cuL,sL)
        assert len(nb)>=2, (cn,wL,k,nb)
        (sb1,i1),(sb2,i2)=nb[0],nb[1]
        dL=sb1-SB_L
        assert 19.0<dL<22.0, (cn,wL,k,"unexpected long setback",sb1)
        b2=R[wL]["bricks"][i2]; u20,u21=bu(b2)
        j12=sb2-(sb1+abs(bu(R[wL]["bricks"][i1])[1]-bu(R[wL]["bricks"][i1])[0]))
        assert abs(j12-10)<1.0,(cn,wL,k,"joint b1-b2",j12)
        assert abs((u21-u20)-215.0)<1.0,(cn,wL,k,"b2 not full-length",u21-u20)
        shift_brick(wL,i1,-sL*dL)
        # pair fills from (b1 new far edge +10) to b2's far edge
        b1u0,b1u1=bu(R[wL]["bricks"][i1])
        b1far=(b1u1 if sL>0 else b1u0); b2far=(u21 if sL>0 else u20)
        span=abs(b2far-(b1far+sL*10.0)); c=(span-10.0)/2.0
        p0=b1far+sL*10.0
        q1=sorted([p0,p0+sL*c]); q2=sorted([p0+sL*(c+10.0),p0+sL*(2*c+10.0)])
        z20,z21=bz(b2)
        assert MINCUT<=c<=215.01,(cn,wL,k,"pair piece size",c)
        killed[wL].append(i2)
        newbr[wL].append(dict(t="cut",verts=rectverts(q1[0],z20,q1[1],z21),corner=cn,cp="pair"))
        newbr[wL].append(dict(t="cut",verts=rectverts(q2[0],z20,q2[1],z21),corner=cn,cp="pair"))
        log["b1_long_shift"]+=1; log["b2_split"]+=1; log["pair_pieces"]+=2
        details.append((cn,wL,k,"long",round(dL,2),round(c,2)))
        # ---- SHORT face field: b1 shift + b2 trim ----
        nb=near2(wS,k,cuS,sS)
        assert len(nb)>=2,(cn,wS,k,nb)
        (sb1,i1),(sb2,i2)=nb[0],nb[1]
        dS=SB_S-sb1
        assert 3.0<dS<5.5,(cn,wS,k,"unexpected short setback",sb1)
        shift_brick(wS,i1,+sS*dS)     # away from corner (cf edge: cu+s*sb -> cu+s*117.5)
        b1u0,b1u1=bu(R[wS]["bricks"][i1])
        b2=R[wS]["bricks"][i2]; u20,u21=bu(b2); z20,z21=bz(b2)
        assert abs((u21-u20)-215.0)<1.0,(cn,wS,k,"b2 not full-length",u21-u20)
        b1far=(b1u1 if sS>0 else b1u0)
        newcf=b1far+sS*10.0           # b2 corner-facing edge
        uu=sorted([newcf, (u21 if sS>0 else u20)])
        b2["verts"]=rectverts(uu[0],z20,uu[1],z21); b2["t"]="cut"; b2["corner"]=cn; b2["cp"]="trim"
        L2=uu[1]-uu[0]
        assert MINCUT-0.01<=L2<=215.01,(cn,wS,k,"b2 trim length",L2)
        log["b1_short_shift"]+=1; log["b2_trim"]+=1
        details.append((cn,wS,k,"short",round(dS,2),round(uu[1]-uu[0],2)))
        k+=1
# apply removals + additions
for w in R:
    if not isinstance(R[w],dict) or "bricks" not in R[w]: continue
    keep=[br for i,br in enumerate(R[w]["bricks"]) if i not in set(killed[w])]
    R[w]["bricks"]=keep+newbr[w]
json.dump(R,open(SRC,"w"))
tot=sum(len(R[w]["bricks"]) for w in R if isinstance(R[w],dict) and "bricks" in R[w])
print("RETROFIT DONE:",dict(log))
print("red placement bricks now:",tot,"(was 5740 field; +117 pair, +234 corner flats = 6091)")
per=collections.Counter()
for w in R:
    if isinstance(R[w],dict) and "bricks" in R[w]:
        per[w]=len(R[w]["bricks"])
print("per wall:",dict(per))
import itertools
print("sample long fixes:",details[0:2]); print("sample short fixes:",[d for d in details if d[3]=='short'][0:2])
szs=collections.Counter((d[3],d[4]) for d in details)
print("shift magnitudes (side,mm)->count:",dict(szs))
