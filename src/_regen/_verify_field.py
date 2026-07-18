#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SELF-VERIFY for the v2 stagger-aware field-from-corners re-lay.
Checks: 1 corner flats byte-identical+parity | 2 sizes/verts | 3 flush/joints/overlap/area
4 cuts only in allowed zones (jamb/free ends, meeting make-up, strips), <=2 per zone
5 FULL 215 against every corner piece | 6 placement==model==brick_types (+per-wall DXF)
7 black md5 unchanged | 9 adjacent-course perp-joint stagger >= 53.75 EVERYWHERE
10 deterministic (2x re-run from backup, byte-identical)"""
import json, os, sys, math, hashlib, collections, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
INP  = os.path.join(HERE, "..")
SRC  = os.path.join(INP, "red_brick_placement_v7_stairfix.json")
BAK  = os.path.join(INP, "red_brick_placement_v7_stairfix_PREFIELD.bak.json")
sys.path.insert(0, HERE)
import _field_from_corners_retile as T

R   = json.load(open(SRC))
BKP = json.load(open(BAK))
EPS = 1e-6
results = []
def rep(cid, name, ok, detail):
    results.append((cid, name, ok, detail))
    print("  [%s] %-4s %-46s %s" % (cid, "PASS" if ok else "FAIL", name, detail))

def ext(br):
    us=[v[0] for v in br["verts"]]; zs=[v[1] for v in br["verts"]]
    return min(us), max(us), min(zs), max(zs)

def course_of(br):
    return int(ext(br)[2]//75)

# ---------------- check 1: corner flats identical + parity ----------------
ok=True; det=[]
for w in T.WALLS:
    cur=[b for b in R[w]["bricks"]   if b.get("cp") in ("lap","half")]
    old=[b for b in BKP[w]["bricks"] if b.get("cp") in ("lap","half")]
    if cur!=old: ok=False; det.append(w+" corner dicts differ")
nlap =sum(1 for w in T.WALLS for b in R[w]["bricks"] if b.get("cp")=="lap")
nhalf=sum(1 for w in T.WALLS for b in R[w]["bricks"] if b.get("cp")=="half")
parity_bad=0
for w,cfg in T.WALLS.items():
    for b in R[w]["bricks"]:
        cp=b.get("cp")
        if cp not in ("lap","half"): continue
        u0,u1,z0,z1=ext(b); k=int(z0//75)
        at_left = abs(min(abs(u0-cfg["uL"]),abs(u0-(cfg["uL"]-20))))<1e-6
        lapE = cfg["lapE_L"] if at_left else cfg["lapE_R"]
        lap_here = ((k%2==0)==lapE)
        if (cp=="lap")!=lap_here: parity_bad+=1
        if cp=="lap" and abs((u1-u0)-215)>EPS: parity_bad+=1
        if cp=="half" and abs((u1-u0)-107.5)>EPS: parity_bad+=1
rep("1","corner flats kept + parity", ok and nlap==117 and nhalf==117 and parity_bad==0,
    "lap=%d half=%d dict-identical=%s parity_bad=%d"%(nlap,nhalf,ok,parity_bad))

# ---------------- check 2: no pair/trim/bond artifacts, verts, sizes ----------------
npair=sum(1 for w in T.WALLS for b in R[w]["bricks"] if b.get("cp") in ("pair","trim"))
nv_bad=0; too_small=0; too_long=0
for w in T.WALLS:
    for b in R[w]["bricks"]:
        vs={tuple(v) for v in b["verts"]}
        if len(vs)>4: nv_bad+=1
        u0,u1,z0,z1=ext(b)
        if (u1-u0)<20-EPS or (z1-z0)<20-EPS: too_small+=1
        if b.get("cp") not in ("lap","half") and (u1-u0)>215+EPS: too_long+=1
rep("2","no pair/trim; <=4 verts; 20..215",
    npair==0 and nv_bad==0 and too_small==0 and too_long==0,
    "pair/trim=%d verts>4=%d <20mm=%d field>215=%d"%(npair,nv_bad,too_small,too_long))

# ---------------- check 3: flush ends / 10mm joints / no overlap / area ----------------
j_bad=[]; flush_bad=[]; ovl=0
area_meas=0.0; area_exp=0.0
for w,cfg in T.WALLS.items():
    ops = T.openings_for(R[w], w)
    rows = collections.defaultdict(list)
    for b in R[w]["bricks"]:
        rows[course_of(b)].append(b)
    for k in range(39):
        z0=k*75.0; h=(65.0 if k<38 else T.TOP_H[w]); z1=z0+h
        segs = T.band_segments(cfg, ops, z0, z1)
        strips=[(f0,f1,s0,s1) for (sk,s0,s1,f0,f1) in T.STRIPS.get(w,[]) if sk==k]
        lapL = cfg["left"]=="corner"  and ((k%2==0)==cfg["lapE_L"])
        lapR = cfg["right"]=="corner" and ((k%2==0)==cfg["lapE_R"])
        expL = cfg["uL"]-(20.0 if lapL else 0.0)
        expR = cfg["uR"]+(20.0 if lapR else 0.0)
        holes=[(u0,u1) for (lab,u0,w0,u1,w1) in ops if w0<z0+EPS and w1>z1-EPS]
        pieces=sorted(rows.get(k,[]), key=lambda b: ext(b)[0])
        assert pieces, (w,k,"empty course")
        e=[ext(b) for b in pieces]
        if abs(e[0][0]-expL)>EPS or abs(e[-1][1]-expR)>EPS:
            flush_bad.append((w,k,"row ends",e[0][0],expL,e[-1][1],expR))
        for i in range(len(e)-1):
            g=e[i+1][0]-e[i][1]
            if g<-EPS: ovl+=1
            if abs(g-10.0)<=EPS: continue
            if any(abs(e[i][1]-h0)<EPS and abs(e[i+1][0]-h1)<EPS for (h0,h1) in holes): continue
            j_bad.append((w,k,e[i][1],e[i+1][0],g))
        for (u0,u1,zz0,zz1) in e: area_meas += (u1-u0)*(zz1-zz0)
        # expected area: fill spans minus 10mm joints (piece-count based)
        for (sL,sR) in segs:
            cL = cfg["left"]=="corner"  and abs(sL-cfg["uL"])<1e-6
            cR = cfg["right"]=="corner" and abs(sR-cfg["uR"])<1e-6
            a = sL + (T.setback(cfg["lapE_L"],k) if cL else 0.0)
            b_= sR - (T.setback(cfg["lapE_R"],k) if cR else 0.0)
            sub=[x for x in e if x[0]>a-EPS and x[1]<b_+EPS and abs(x[3]-x[2]-h)<EPS]
            area_exp += ((b_-a) - 10.0*(len(sub)-1))*h
        for (f0,f1,s0,s1) in strips:
            nn=len([x for x in e if x[0]>f0-EPS and x[1]<f1+EPS and (x[3]-x[2])<50])
            area_exp += ((f1-f0) - 10.0*(nn-1))*(s1-s0)
for w in T.WALLS:
    for b in R[w]["bricks"]:
        if b.get("cp") in ("lap","half"):
            u0,u1,z0,z1=ext(b); area_exp += (u1-u0)*(z1-z0)
rep("3","flush ends / 10mm joints / no overlap-void",
    not j_bad and not flush_bad and ovl==0 and abs(area_meas-area_exp)<1.0,
    "bad_joints=%d bad_flush=%d overlaps=%d area meas %.0f vs exp %.0f mm2"
    %(len(j_bad),len(flush_bad),ovl,area_meas,area_exp))
if j_bad[:3]: print("      j_bad sample:",j_bad[:3])
if flush_bad[:3]: print("      flush_bad sample:",flush_bad[:3])

# ---------------- check 4: cuts only in allowed zones; <=2 per zone ----------------
zone_bad=[]; clus_bad=[]
for w,cfg in T.WALLS.items():
    ops=T.openings_for(R[w],w)
    rows=collections.defaultdict(list)
    for b in R[w]["bricks"]:
        if b.get("cp") in ("lap","half"): continue
        rows[course_of(b)].append(ext(b))
    for k in range(39):
        z0=k*75.0; h=(65.0 if k<38 else T.TOP_H[w]); z1=z0+h
        segs=T.band_segments(cfg,ops,z0,z1)
        nf=[x for x in rows[k] if (x[1]-x[0])<215.0-EPS]
        for x in nf:
            if any(sk==k and f0-1<=x[0] and x[1]<=f1+1 for (sk,s0,s1,f0,f1) in T.STRIPS.get(w,[])):
                continue
            ok=False
            for (sL,sR) in segs:
                if not(x[0]>=sL-EPS and x[1]<=sR+EPS): continue
                cL = cfg["left"]=="corner" and abs(sL-cfg["uL"])<1e-6
                cR = cfg["right"]=="corner" and abs(sR-cfg["uR"])<1e-6
                if not cL and x[0]<=sL+455: ok=True
                if not cR and x[1]>=sR-455: ok=True
                if cL and cR:
                    a=sL+T.setback(cfg["lapE_L"],k); b_=sR-T.setback(cfg["lapE_R"],k)
                    L=b_-a;n=int(math.floor(L/225+1e-9));r=L-n*225
                    if 0<r<20-1e-9:n-=1;r+=225
                    nL=(n+1)//2;nR=n-nL
                    if a+nL*225-230<=x[0] and x[1]<=b_-nR*225+230: ok=True
            if not ok: zone_bad.append((w,k,x[0],x[1]))
        # cut clusters (adjacent non-full pieces) must be <=2 pieces
        nfs=sorted(nf); i=0
        while i<len(nfs):
            jj=i
            while jj+1<len(nfs) and abs(nfs[jj+1][0]-nfs[jj][1]-10.0)<EPS: jj+=1
            if jj-i+1>2: clus_bad.append((w,k,nfs[i][0],jj-i+1))
            i=jj+1
rep("4","cuts only at jamb/free/meet/strip zones, <=2/zone",
    not zone_bad and not clus_bad,
    "outside_zone=%d clusters>2=%d"%(len(zone_bad),len(clus_bad)))
if zone_bad[:3]: print("      zone sample:",zone_bad[:3])
if clus_bad[:3]: print("      cluster sample:",clus_bad[:3])

# ---------------- check 5: FULL 215 against every corner piece ----------------
c5_bad=[]; c5_n=0
for w,cfg in T.WALLS.items():
    rows=collections.defaultdict(list)
    for b in R[w]["bricks"]:
        if b.get("cp") in ("lap","half"): continue
        rows[course_of(b)].append(ext(b))
    for k in range(39):
        for side in ("L","R"):
            lapE = cfg["lapE_L"] if side=="L" else cfg["lapE_R"]
            if lapE is None: continue
            sb=T.setback(lapE,k)
            a = cfg["uL"]+sb if side=="L" else cfg["uR"]-sb-215.0
            hits=[p for p in rows[k] if abs(p[0]-a)<1e-6 and (p[3]-p[2])>12.5]
            c5_n+=1
            if not (hits and abs((hits[0][1]-hits[0][0])-215.0)<EPS): c5_bad.append((w,k,side))
rep("5","FULL 215 against every corner piece", not c5_bad and c5_n==234,
    "checked=%d (expect 234) bad=%d"%(c5_n,len(c5_bad)))
if c5_bad[:3]: print("      c5 sample:",c5_bad[:3])

# ---------------- check 6: counts reconcile ----------------
pl_red=sum(len(R[w]["bricks"]) for w in T.WALLS)
bt=json.load(open(os.path.join(INP,"brick_types.json")))
bt_red=sum(t["qty"] for t in bt["types"] if t["colour"]=="Red")
bt_blk=sum(t["qty"] for t in bt["types"] if t["colour"]=="Black")
out=subprocess.run([sys.executable,os.path.join(HERE,"_run_model_stub.py")],
                   capture_output=True,text=True)
mdl=[l for l in out.stdout.splitlines() if l.startswith("STUB-CHECK red=")]
mdl_ok = bool(mdl) and ("red=%d black=1461 GRAND=%d"%(pl_red,pl_red+1461)) in mdl[0] \
         and "STUB-CHECK PASS" in out.stdout
rep("6","placement==model==brick_types",
    pl_red==bt_red and bt_blk==1461 and mdl_ok,
    "placement red=%d brick_types red=%d black=%d model:%s"%(pl_red,bt_red,bt_blk,
     mdl[0].replace("STUB-CHECK ","") if mdl else "STUB FAILED: "+out.stdout[-200:]+out.stderr[-200:]))

# ---------------- check 7: black md5 ----------------
md5=hashlib.md5(open(os.path.join(INP,"black_placement_fixed7.json"),"rb").read()).hexdigest()
rec=open(os.path.join(HERE,"_black_md5_PREFLAT.txt")).read().split()[0]
rep("7","black md5 unchanged", md5==rec=="3c22c315d16ee546ef9eb43bbc52f403", md5)

# ---------------- check 9: adjacent-course perp-joint stagger >= 53.75 EVERYWHERE ----------------
permin={}
for w in T.WALLS:
    rows=collections.defaultdict(list)
    for b in R[w]["bricks"]:
        u0,u1,z0,z1=ext(b); rows[int(z0//75)].append((u0,u1,z0,z1))
    m=1e9; n=0
    for k in range(38):
        lo=sorted(rows.get(k,[])); hi=sorted(rows.get(k+1,[]))
        def joints(ps):
            return [(ps[i][1]+5.0, max(ps[i][3],ps[i+1][3]), min(ps[i][2],ps[i+1][2]))
                    for i in range(len(ps)-1) if abs(ps[i+1][0]-ps[i][1]-10.0)<=EPS]
        jlo=joints(lo); jhi=joints(hi)
        for (x,xt,xb) in jhi:
            for (y,yt,yb) in jlo:
                if abs(x-y)>=225.0: continue
                if not (7.0 <= xb-yt <= 12.5): continue     # bed-joint adjacency
                n+=1; m=min(m, abs(x-y))
    permin[w]=(m,n)
mall=min(v[0] for v in permin.values())
rep("9","perp-joint stagger >= 53.75 (ALL adjacent joints)", mall>=53.75-1e-9,
    " ".join("%s=%.2f/%d"%(w,v[0],v[1]) for w,v in permin.items()))

# ---------------- check 10: determinism ----------------
cur=open(SRC,"rb").read(); h1=hashlib.md5(cur).hexdigest()
import shutil as sh
h=[]
for rnd in range(2):
    sh.copy2(BAK,SRC)
    r=subprocess.run([sys.executable,os.path.join(HERE,"_field_from_corners_retile.py")],
                     capture_output=True,text=True)
    assert r.returncode==0, r.stderr[-500:]
    h.append(hashlib.md5(open(SRC,"rb").read()).hexdigest())
rep("10","deterministic (2x from backup, byte-identical)", h[0]==h[1]==h1,
    "orig=%s run1=%s run2=%s"%(h1[:10],h[0][:10],h[1][:10]))

nfail=sum(1 for c in results if not c[2])
print("="*70)
print("VERIFY SUMMARY: %d checks, %d FAIL"%(len(results),nfail))
sys.exit(1 if nfail else 0)
