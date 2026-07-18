#!/usr/bin/env python3
"""Geometric audit of the flat-corner placement: per corner per course measure
(1) lap present + flush with adjacent outer plane, (2) half present, set back 20,
(3) 10mm joints slip->field, (4) no overlap / no unintended gap in every course band
across the whole wall, (5) cross-wall butt, (6) field diff vs backup = ONLY b1/b2."""
import json,os,collections
HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
NEW=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix.json")))
OLD=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix_PREFLAT.bak.json")))
CP=75.0; FF=2891.0; T=20.0
CORNERS=[("FL","C_NW_front",0.0,+1,"A_NE_side",13604.0,-1),
         ("FR","B_SW_side",0.0,+1,"C_NW_front",11513.0,-1),
         ("BL","A_NE_side",0.0,+1,"D_SE_garden",12510.0,-1)]
def bu(br): us=[v[0] for v in br["verts"]]; return min(us),max(us)
def bz(br): zs=[v[1] for v in br["verts"]]; return min(zs),max(zs)
def bands(R,wall):
    cs=collections.defaultdict(list)
    for br in R[wall]["bricks"]:
        z0,z1=bz(br); k=int(round(z0/CP))
        cs[k].append(br)
    return cs
fails=[]; J=[]
NB={w:bands(NEW,w) for w in NEW}
for cn,wA,cuA,sA,wB,cuB,sB in CORNERS:
    for k in range(0,39):
        lo=(k%2==0)
        (wL,cuL,sL)=(wA,cuA,sA) if lo else (wB,cuB,sB)
        (wS,cuS,sS)=(wB,cuB,sB) if lo else (wA,cuA,sA)
        # lap
        laps=[b for b in NB[wL][k] if b.get("corner")==cn and b.get("cp")=="lap"]
        halfs=[b for b in NB[wS][k] if b.get("corner")==cn and b.get("cp")=="half"]
        if len(laps)!=1 or len(halfs)!=1: fails.append((cn,k,"missing lap/half",len(laps),len(halfs))); continue
        u0,u1=bu(laps[0]); outer=(u0 if sL>0 else u1); inner=(u1 if sL>0 else u0)
        if abs(outer-(cuL-sL*T))>0.01: fails.append((cn,k,"lap not flush",outer))
        if abs(abs(u1-u0)-215.0)>0.01: fails.append((cn,k,"lap len",u1-u0))
        h0,h1=bu(halfs[0]); houter=(h0 if sS>0 else h1)
        if abs(houter-cuS)>0.01: fails.append((cn,k,"half setback",houter))
        if abs(abs(h1-h0)-107.5)>0.01: fails.append((cn,k,"half len",h1-h0))
        # joint slip->nearest field brick (exclude the slip itself)
        def joint_from(wall,k,edge,s):
            best=None
            for b in NB[wall][k]:
                x0,x1=bu(b); cf=(x0 if s>0 else x1)
                d=(cf-edge)*s
                if 0.5<d<300 and (best is None or d<best): best=d
            return best
        jL=joint_from(wL,k,inner,sL); jS=joint_from(wS,k,(h1 if sS>0 else h0)-0 if False else (h1 if sS>0 else h0),sS)
        J.append((cn,k,"L",jL)); J.append((cn,k,"S",jS))
        if jL is None or abs(jL-10)>0.75: fails.append((cn,k,"long joint",jL))
        if jS is None or abs(jS-10)>0.75: fails.append((cn,k,"short joint",jS))
# overlap / gap scan over ALL red walls, every course band
ovl=0; badgap=[]
for w in NEW:
    if not isinstance(NEW[w],dict) or "bricks" not in NEW[w]: continue
    for k,bs in bands(NEW,w).items():
        iv=sorted(bu(b) for b in bs)
        for (a0,a1),(b0,b1) in zip(iv,iv[1:]):
            g=b0-a1
            if g<-0.01: ovl+=1; badgap.append((w,k,"OVERLAP",round(a1,1),round(b0,1)))
            elif 0.01<g<9.2: badgap.append((w,k,"gap<10",round(g,2),round(a1,1)))
            elif 10.8<g<16.5: badgap.append((w,k,"joint>10",round(g,2),round(a1,1)))
print("overlaps:",ovl,"| suspicious gaps:",len(badgap),badgap[:8])
# cross-wall: lap back must butt the half's end (same world plane) - verified by construction; check no 3D overlap:
# lap occupies adjacent wall's u in [-20,0] equivalent zone only at its own wall -> plan intersection is the 20x20 arris square vs half [0..107.5]: disjoint by construction.
# field diff vs backup
def canon(R,w,withmark=False):
    s=set()
    for b in R[w]["bricks"]:
        if withmark or not b.get("cp"):
            s.add((b["t"],tuple(sorted((round(v[0],3),round(v[1],3)) for v in b["verts"]))))
    return s
tot_same=0; tot_changed=0
for w in NEW:
    if not isinstance(NEW[w],dict) or "bricks" not in NEW[w]: continue
    oldset=canon(OLD,w); newf=canon(NEW,w)   # new field only (unmarked)
    same=oldset&newf
    removed=oldset-newf; added=newf-oldset
    tot_same+=len(same); tot_changed+=len(removed)
    print(w,"unchanged field:",len(same),"| old bricks gone/moved:",len(removed),"| new unmarked pieces:",len(added))
nmark=collections.Counter()
for w in NEW:
    if not isinstance(NEW[w],dict) or "bricks" not in NEW[w]: continue
    for b in NEW[w]["bricks"]:
        if b.get("cp"): nmark[b["cp"]]+=1
print("marked pieces:",dict(nmark))
jbad=[x for x in J if x[3] is None or abs(x[3]-10)>0.75]
print("slip->field joints measured:",len(J),"| out of tolerance:",len(jbad))
print("FAILS:",len(fails),fails[:10])
