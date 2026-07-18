#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier for the CONTINUOUS-GRID single-cut re-lay (v4).
Measures everything from the written placement, prints counts/mins/pass-fail only."""
import json, os, hashlib, collections

HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
SRC=os.path.join(INP,"red_brick_placement_v7_stairfix.json")
BAK=os.path.join(INP,"red_brick_placement_v7_stairfix_PRE_CONTGRID.bak.json")
FULL,J,MOD,H=215.0,10.0,225.0,65.0
SMIN=53.75; JLO,JHI=9.99,12.26
WCFG={"A_NE_side":  dict(uL=0.0,uR=13604.0,left="corner",right="corner"),
      "C_NW_front": dict(uL=0.0,uR=11513.0,left="corner",right="corner"),
      "B_SW_side":  dict(uL=0.0,uR=11205.0,left="corner",right="free"),
      "D_SE_garden":dict(uL=6855.0,uR=12510.0,left="free",right="corner")}
DOOR={"C_NW_front":[("DOOR",4059.0,0.0,7473.0,10000.0)]}
# documented jamb gaps (wall, u0, u1, parity, expected #courses)
GAPS=[("C_NW_front",1328.0,1340.0,0,11),("C_NW_front",10172.0,10183.0,1,11),
      ("D_SE_garden",7900.0,7910.0,0,12)]
FAIL=[]
def chk(ok,msg):
    print(("  PASS  " if ok else "  FAIL  ")+msg)
    if not ok: FAIL.append(msg)
def ext(b):
    us=[v[0] for v in b["verts"]]; zs=[v[1] for v in b["verts"]]
    return min(us),max(us),min(zs),max(zs)

R=json.load(open(SRC)); B=json.load(open(BAK)); WALLS=sorted(WCFG)
rows={}; runs=[]
for w in WALLS:
    rr=collections.defaultdict(list)
    for b in R[w]["bricks"]:
        u0,u1,z0,z1=ext(b)
        rr[(z0,z1)].append(dict(u0=u0,u1=u1,L=u1-u0,h=z1-z0,cp=b.get("cp"),t=b["t"],mk=b.get("mk")))
    for key in rr: rr[key].sort(key=lambda p:p["u0"])
    rows[w]=rr
    for (z0,z1),ps in sorted(rr.items()):
        fld=[p for p in ps if not p["cp"]]
        cur=[]
        for p in fld:
            if cur and p["u0"]-cur[-1]["u1"]>15.0:
                runs.append(dict(w=w,z0=z0,z1=z1,pieces=cur)); cur=[]
            cur.append(p)
        if cur: runs.append(dict(w=w,z0=z0,z1=z1,pieces=cur))
print("rows: "+", ".join("%s %d"%(w,len(rows[w])) for w in WALLS)+" | field runs: %d"%len(runs))

print("(1) SINGLE-CUT RULE (per run: no adjacent cuts; <=2 cuts, 2 only at opposite edges):")
bad=[]; ncut=0
for r_ in runs:
    ps=r_["pieces"]
    cuts=[i for i,p in enumerate(ps) if p["L"]<FULL-1e-6]
    ncut+=len(cuts)
    for i,i2 in zip(cuts,cuts[1:]):
        if i2==i+1: bad.append((r_["w"],r_["z0"],"ADJACENT cuts"))
    if len(cuts)>2: bad.append((r_["w"],r_["z0"],">2 cuts"))
    elif len(cuts)==2 and not (cuts[0]==0 and cuts[1]==len(ps)-1):
        bad.append((r_["w"],r_["z0"],"2 cuts not at opposite edges"))
chk(not bad,"violations: %d | single cuts total=%d over %d runs"%(len(bad),ncut,len(runs)))
if bad[:4]: print("   detail:",bad[:4])

print("(2) cut sizes & full share per wall:")
for w in WALLS:
    fld=[p for ps in rows[w].values() for p in ps if not p["cp"]]
    nf=sum(1 for p in fld if abs(p["L"]-FULL)<1e-6)
    print("   %-12s field %4d: full-length %4d (%.1f%%), cuts %3d"%(w,len(fld),nf,100.0*nf/len(fld),len(fld)-nf))

print("(3) first field slip adjacent to every corner piece is FULL 215 (joint 10..12):")
nc=0; okc=0
for w in WALLS:
    fld_by_z0=collections.defaultdict(list)
    for (z0,z1),ps in rows[w].items():
        for q in ps:
            if not q["cp"]: fld_by_z0[z0].append(q)
    for (z0,z1),ps in rows[w].items():
        for p in ps:
            if not p["cp"]: continue
            nc+=1
            fld=fld_by_z0[z0]
            if p["u0"]<WCFG[w]["uL"]+300:
                adj=[q for q in fld if J-1e-6<=q["u0"]-p["u1"]<=12.0+1e-6]
                adj.sort(key=lambda q:q["u0"])
            else:
                adj=[q for q in fld if J-1e-6<=p["u0"]-q["u1"]<=12.0+1e-6]
                adj.sort(key=lambda q:-q["u1"])
            if adj and abs(adj[0]["L"]-FULL)<1e-6: okc+=1
            else: print("   MISS %s z%g %s u[%g,%g]"%(w,z0,p["cp"],p["u0"],p["u1"]))
chk(okc==nc==234,"full-after-corner: %d/%d (expect 234/234)"%(okc,nc))

print("(4) cuts only at jamb / free end / mid make-up:")
loc=collections.Counter(); badloc=[]
for w in WALLS:
    ops=[(float(o[1]),float(o[3])) for o in R[w]["windows"]]+[(o[1],o[3]) for o in DOOR.get(w,[])]
    jambs=set(x for pr in ops for x in pr)
    for (z0,z1),ps in rows[w].items():
        for p in ps:
            if p["cp"] or p["L"]>=FULL-1e-6: continue
            at_j=any(abs(p["u0"]-jj)<1e-6 or abs(p["u1"]-jj)<1e-6 for jj in jambs)
            at_f=(WCFG[w]["left"]=="free" and abs(p["u0"]-WCFG[w]["uL"])<1e-6) or \
                 (WCFG[w]["right"]=="free" and abs(p["u1"]-WCFG[w]["uR"])<1e-6)
            if at_j: loc["jamb"]+=1
            elif at_f: loc["free"]+=1
            elif p.get("mk")=="meet": loc["meet"]+=1
            else: badloc.append((w,z0,p["u0"],p["L"]))
chk(not badloc,"cut locations %s ; elsewhere: %d"%(dict(loc),len(badloc)))
if badloc[:4]: print("   detail:",badloc[:4])

print("(5) ZIPPER CHECK - adjacent-course perp-joint stagger (JOINTS incl corner flats):")
tviol=0
for w in WALLS:
    jrows=[]
    for (z0,z1),ps in sorted(rows[w].items()):
        js=[]
        for a,b2 in zip(ps,ps[1:]):
            g=b2["u0"]-a["u1"]
            if JLO<=g<=JHI: js.append((a["u1"]+b2["u0"])/2.0)
        jrows.append((z0,z1,js))
    mn=(1e9,None); nv=0
    for (z0,z1,ja) in jrows:
        for (y0,y1,jb) in jrows:
            if not (7.0<=y0-z1<=12.5): continue
            for xb in jb:
                ds=[abs(xb-xa) for xa in ja if abs(xb-xa)<MOD]
                if not ds: continue
                d=min(ds)
                if d<mn[0]: mn=(d,(z0,y0,round(xb,1)))
                if d<SMIN-1e-9: nv+=1
    tviol+=nv
    print("   %-12s min stagger %.2f mm at z%g/z%g u%s | pairs <%.2f: %d"
          %(w,mn[0],mn[1][0] if mn[1] else -1,mn[1][1] if mn[1] else -1,
            mn[1][2] if mn[1] else "-",SMIN,nv))
chk(tviol==0,"TOTAL adjacent-course alignments < 53.75mm: %d (MUST be 0)"%tviol)

print("(6) corner flats byte-identical to PRE_CONTGRID backup:")
allok=True
for w in WALLS:
    a=sorted(json.dumps(x,sort_keys=True) for x in R[w]["bricks"] if x.get("cp") in("lap","half"))
    c=sorted(json.dumps(x,sort_keys=True) for x in B[w]["bricks"] if x.get("cp") in("lap","half"))
    allok&=(a==c)
chk(allok,"corner flats identical on all 4 walls (117 lap + 117 half)")

print("(7) geometry: overlaps / sizes / joints / edge gaps:")
jh=collections.Counter(); nover=0; badpc=0; badj=0
for w in WALLS:
    for (z0,z1),ps in rows[w].items():
        for a,b2 in zip(ps,ps[1:]):
            g=round(b2["u0"]-a["u1"],4)
            if g<-1e-6: nover+=1
            elif g<=12.26: jh[g]+=1
            if 12.26<g<=15.0: badj+=1
        for p in ps:
            if p["cp"]: continue
            if not (20.0-1e-6<=p["L"]<=FULL+1e-6): badpc+=1
chk(nover==0,"overlaps: %d"%nover)
chk(badpc==0,"pieces outside 20..215: %d"%badpc)
chk(badj==0,"joints in (12.26,15]: %d"%badj)
print("   joint widths (mm -> n): "+", ".join("%.4g:%d"%(k,v) for k,v in sorted(jh.items())))
# strict run-edge coverage
gap_seen=collections.Counter(); voids=[]
for r_ in runs:
    w=r_["w"]; z0,z1=r_["z0"],r_["z1"]
    ops=[(float(o[1]),float(o[2]),float(o[3]),float(o[4])) for o in R[w]["windows"]]+ \
        [(o[1],o[2],o[3],o[4]) for o in DOOR.get(w,[])]
    if w=="D_SE_garden" and r_["pieces"][0]["h"] in (20.0,45.0):
        okS=abs(r_["pieces"][0]["u0"]-7920.0)<1e-6 and abs(r_["pieces"][-1]["u1"]-10385.0)<1e-6
        if not okS: voids.append((w,z0,"strip extent"))
        continue
    zops=[(u0,u1) for (u0,w0,u1,w1) in ops if w0<z1-1e-9 and w1>z0+1e-9]
    corn=[]
    for (zz0,zz1),ps2 in rows[w].items():
        if abs(zz0-z0)<1e-6: corn+=[p for p in ps2 if p["cp"]]
    u0=r_["pieces"][0]["u0"]; u1=r_["pieces"][-1]["u1"]
    candL=[WCFG[w]["uL"]]+[uu1 for (_,uu1) in zops]+[p["u1"] for p in corn if p["u0"]<WCFG[w]["uL"]+300]
    candR=[WCFG[w]["uR"]]+[uu0 for (uu0,_) in zops]+[p["u0"] for p in corn if p["u0"]>WCFG[w]["uL"]+300]
    bL=max([c for c in candL if c<=u0+1e-6],default=None)
    bR=min([c for c in candR if c>=u1-1e-6],default=None)
    for (bb,uu,side) in ((bL,u0,"L"),(bR,u1,"R")):
        if bb is None: voids.append((w,z0,side,"no boundary")); continue
        d=round(abs(uu-bb),4)
        iscorner=any(abs(p["u1"]-bb)<1e-6 or abs(p["u0"]-bb)<1e-6 for p in corn)
        if iscorner:
            if not (J-1e-6<=d<=12.0+1e-6): voids.append((w,z0,side,"corner joint %.2f"%d))
            continue
        if d<1e-6: continue
        par=int(round(z0/75))%2
        doc=[(g0,g1) for (wq,g0,g1,pq,_) in GAPS if wq==w and pq==par
             and abs(d-(g1-g0))<1e-6 and (abs(bb-g0)<1e-6 or abs(bb-g1)<1e-6)]
        if doc: gap_seen[(w,doc[0])]+=1
        else: voids.append((w,z0,side,"undocumented gap %.2f at %.1f"%(d,bb)))
chk(not voids,"undocumented edge gaps/voids: %d %s"%(len(voids),voids[:4]))
exp={(wq,(g0,g1)):n for (wq,g0,g1,pq,n) in GAPS}
chk(dict(gap_seen)==exp,"documented jamb gaps exactly as expected: %s"%dict(gap_seen))

print("(8) black md5:")
md5=hashlib.md5(open(os.path.join(INP,"black_placement_fixed7.json"),"rb").read()).hexdigest()
ref=open(os.path.join(HERE,"_black_md5_PRE_SINGLECUT.txt")).read().split()[0]
chk(md5==ref,"black md5 unchanged (%s)"%md5[:10])

print("(9) counts:")
gt=0
for w in WALLS:
    n=len(R[w]["bricks"]); gt+=n
    fld=sum(1 for ps in rows[w].values() for p in ps if not p["cp"])
    print("   %-12s total %4d = field %4d + corners %d"%(w,n,fld,n-fld))
try:
    BT=json.load(open(os.path.join(INP,"brick_types.json")))
    sq=sum(t["qty"] for t in BT["types"])
    chk(BT["n_bricks"]==sq==gt+1461,"brick_types: n=%d sum(qty)=%d == red %d + black 1461"%(BT["n_bricks"],sq,gt))
    print("   Brick Type IDs: %d"%len(BT["types"]))
except FileNotFoundError:
    print("   (brick_types.json not yet rebuilt)")
area=sum(p["L"]*p["h"] for w in WALLS for ps in rows[w].values() for p in ps)
print("   RED total %d ; + black 1461 = GRAND %d ; red area %.3f m2"%(gt,gt+1461,area/1e6))
ncs=len(set(round(p["L"],2) for w in WALLS for ps in rows[w].values() for p in ps if not p["cp"] and p["L"]<FULL-1e-6))
print("   distinct cut lengths: %d"%ncs)

print("ALL CHECKS PASS" if not FAIL else "FAILURES: %d -> %s"%(len(FAIL),FAIL[:6]))
