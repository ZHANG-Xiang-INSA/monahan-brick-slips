#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIELD RE-LAY v4 - TRUE CONTINUOUS GRID (New requirement 4).

Fixes v3's straight-joint "zipper" seams (per-segment "W mod 225" re-anchoring at
jambs made same-parity courses identical inside window bands) while keeping the
SINGLE-CUT rule (each fill = n fulls + at most ONE cut piece; never a mosaic).

METHOD - one continuous grid per wall-half:
  grid lines = corner_field_start + n*225 ; corner_field_start = 205 after a lap
  course / 117.5 after a half course (alternates 87.5/course -> bond stagger).
  The grid runs CONTINUOUSLY across the whole half, straight THROUGH openings;
  no re-anchoring at jambs.  A grid slip truncated by an opening jamb = ONE
  single reveal cut ending at the jamb (its inner joint stays on the grid).
  Slips fully inside an opening are omitted; fully solid slips stay full 215.
  Two-corner walls (A_NE, C_NW): left grid <-> left half, right grid <-> right
  half, split at the central opening (A_NE WG12 7303-8213, C_NW DOOR 4059-7473);
  full-width clear courses meet mid-wall (A_NE residue 6.5mm -> all-full with
  joints fattened <=+0.5mm).  One-corner walls (B_SW, D_SE): one grid from the
  corner; the FREE end gets the single make-up cut.
MIN_CUT fixes (reveal/make-up would be <20mm) - never 2 pieces, never a bare gap:
  * left-edge tiny/gap  -> FLUSH-CONVERGE: full slip flush at the jamb, then
    joints fattened <=+2mm until back on the pure grid (or the residual shift is
    absorbed by the far-edge single cut).
  * right-edge tiny/gap -> RESPACE: pieces stay pure from the anchored side,
    run joints fattened <=+2mm (Bresenham, 0.25mm quanta); residual 10..12mm is
    the jamb joint.  Corner-side joint fattened (<=12mm) only when unavoidable.
Corner flat pairs (117 lap + 117 half, "cp") KEPT BYTE-IDENTICAL. BLACK untouched.
D_SE sill/head strips (h20/h45 full rips 7920..10385) laid verbatim.
Deterministic: pure arithmetic, no RNG, sorted iteration.
"""
import json, os, math, shutil, collections

HERE = os.path.dirname(os.path.abspath(__file__))
INP  = os.path.join(HERE, "..")
SRC  = os.path.join(INP, "red_brick_placement_v7_stairfix.json")
BAK  = os.path.join(INP, "red_brick_placement_v7_stairfix_PRE_CONTGRID.bak.json")

FULL=215.0; J=10.0; MOD=FULL+J; H=65.0; CP=75.0; MIN_CUT=20.0; EPS=1e-6
FATJ=2.0; Q=0.25

WALLS = {
 "A_NE_side":  dict(uL=0.0,    uR=13604.0, left="corner", right="corner",
                    lapE_L=True, lapE_R=False),
 "C_NW_front": dict(uL=0.0,    uR=11513.0, left="corner", right="corner",
                    lapE_L=True, lapE_R=False),
 "B_SW_side":  dict(uL=0.0,    uR=11205.0, left="corner", right="free",
                    lapE_L=True, lapE_R=None),
 "D_SE_garden":dict(uL=6855.0, uR=12510.0, left="free",   right="corner",
                    lapE_L=None, lapE_R=False),
}
SPLIT = {"A_NE_side": (7303.0, 8213.0), "C_NW_front": (4059.0, 7473.0)}
EXTRA_OPENINGS = {"C_NW_front": [("DOOR", 4059.0, 0.0, 7473.0, 10000.0)]}
TOP_H = {"A_NE_side":41.0, "C_NW_front":41.0, "B_SW_side":61.0, "D_SE_garden":41.0}
STRIPS = {"D_SE_garden": [(6, 450.0, 470.0, 7920.0, 10385.0),
                          (28, 2120.0, 2165.0, 7920.0, 10385.0)]}

DEV=collections.Counter(); MEET=collections.Counter(); GAPDOC=collections.Counter()

def snap(x): return round(x*4.0)/4.0
def setback(lapE,k): return 205.0 if ((k%2==0)==lapE) else 117.5
def ring(u0,z0,u1,z1):
    r4=lambda x: round(x,4)
    u0,u1,z0,z1=r4(u0),r4(u1),r4(z0),r4(z1)
    return [[u0,z1],[u1,z1],[u1,z0],[u0,z0],[u0,z1]]
def piece(u0,z0,u1,z1,mk=None):
    L=u1-u0; h=z1-z0
    assert MIN_CUT-EPS<=L<=FULL+EPS,("bad piece",u0,u1,L)
    t="full" if (abs(L-FULL)<EPS and abs(h-H)<EPS) else "cut"
    d=dict(t=t,verts=ring(u0,z0,u1,z1))
    if mk is not None and L<FULL-EPS: d["mk"]=mk
    return d
def openings_for(wall,wn):
    ops=[(w[0],float(w[1]),float(w[2]),float(w[3]),float(w[4])) for w in wall["windows"]]
    return sorted(ops+EXTRA_OPENINGS.get(wn,[]),key=lambda o:o[1])
def band_segments(cfg,ops,z0,z1):
    cuts=sorted((u0,u1) for (_,u0,w0,u1,w1) in ops if w0<z1-1e-9 and w1>z0+1e-9)
    segs=[]; pos=cfg["uL"]
    for (u0,u1) in cuts:
        if u0>pos+1e-9: segs.append((pos,u0))
        pos=max(pos,u1)
    if cfg["uR"]>pos+1e-9: segs.append((pos,cfg["uR"]))
    return segs

def grid_raw(cfg,k,side,a,b):
    """pure slips of the wall-half grid clipped to [a,b]"""
    out=[]
    if side=="L":
        s=cfg["uL"]+setback(cfg["lapE_L"],k)
        j=max(0,int(math.floor((a-s)/MOD))-1)
        while True:
            u0=s+j*MOD; u1=u0+FULL; j+=1
            if u0>=b-EPS: break
            if u1<=a+EPS: continue
            out.append([max(u0,a),min(u1,b)])
    else:
        E=cfg["uR"]-setback(cfg["lapE_R"],k)
        i=max(0,int(math.floor((E-b)/MOD))-1)
        while True:
            u1=E-i*MOD; u0=u1-FULL; i+=1
            if u1<=a+EPS: break
            if u0>=b-EPS: continue
            out.append([max(u0,a),min(u1,b)])
        out.sort()
    return [r for r in out if r[1]-r[0]>EPS]

def bres(total_mm,m):
    """total_mm over m joints in 0.25 quanta, each <=FATJ; None if infeasible"""
    q=int(round(total_mm/Q))
    if m<=0 or q<0 or q>m*int(round(FATJ/Q)): return None
    if abs(q*Q-total_mm)>1e-9: return None
    return [((i*q)//m-((i-1)*q)//m)*Q for i in range(1,m+1)]

def flush_converge(wn,k,a,b,raw,endR):
    """left-edge tiny/gap: full flush at a, fat joints (<=12) converge to grid."""
    out=[[a,a+FULL]]
    rest=[r for r in raw if r[1]>a+FULL+J+MIN_CUT-EPS]
    if not rest: return None
    for idx,r in enumerate(rest):
        prev=out[-1][1]
        st=max(prev+J,min(r[0],prev+J+FATJ))
        last=(idx==len(rest)-1)
        if last and abs(r[1]-b)<EPS:
            if endR=="corner" and abs(st-r[0])>EPS: return None
            en=b
        else:
            en=st+FULL
        if not (MIN_CUT-EPS<=en-st<=FULL+EPS): return None
        out.append([st,en])
    if abs(out[-1][1]-b)>EPS: return None
    DEV[(wn,"flush-converge @u%g"%a,k%2)]+=1
    return out

def respace(wn,k,a,b,raw,side,endC):
    """tiny/gap at the NON-anchored edge: drop tiny, fatten run joints from the
    anchored side; residual 0 or 10..12 = jamb joint.  side: which edge has the
    problem ('R'=at b anchor left, 'L'=at a anchor right).  endC = end type of
    the anchored end ('corner' allows +2 on the corner joint as last resort)."""
    ps=[list(r) for r in raw]
    if side=="R":
        if ps and ps[-1][1]-ps[-1][0]<MIN_CUT-EPS: ps.pop()
        if not ps: return None
        gap0=b-ps[-1][1]
    else:
        if ps and ps[0][1]-ps[0][0]<MIN_CUT-EPS: ps.pop(0)
        if not ps: return None
        gap0=ps[0][0]-a
    n=len(ps); m=n-1
    for usec in (False,True):
        if usec and endC!="corner": continue
        sol=None
        for g in [0.0]+[snap(10.0+Q*i) for i in range(int(round(FATJ/Q))+1)]:
            A=snap(gap0-g)
            if A<-EPS: continue
            fats=bres(A,m+(1 if usec else 0))
            if fats is not None: sol=(g,fats); break
        if sol is None: continue
        g,fats=sol
        base=fats[0] if usec else 0.0
        internals=fats[1:] if usec else fats
        out=[list(r) for r in ps]; sh=[0.0]*n
        if side=="R":
            c=base
            for i in range(n):
                if i>0: c+=internals[i-1] if i-1<len(internals) else 0.0
                sh[i]=c
            for i,r in enumerate(out): r[0]=snap(r[0]+sh[i]); r[1]=snap(r[1]+sh[i])
            assert abs((b-out[-1][1])-g)<1e-6,(wn,k,b,out[-1],g)
            if g>EPS: GAPDOC[(wn,"gap %.4g @u%.5g-%.5g"%(g,b-g,b),k%2)]+=1
        else:
            c=base
            for i in range(n-1,-1,-1):
                if i<n-1: c+=internals[n-2-i] if n-2-i<len(internals) else 0.0
                sh[i]=c
            for i,r in enumerate(out): r[0]=snap(r[0]-sh[i]); r[1]=snap(r[1]-sh[i])
            assert abs((out[0][0]-a)-g)<1e-6,(wn,k,a,out[0],g)
            if g>EPS: GAPDOC[(wn,"gap %.4g @u%.5g-%.5g"%(g,a,a+g),k%2)]+=1
        DEV[(wn,"respace%s @%s%g"%("+cornerjoint" if usec else "",side,b if side=="R" else a),k%2)]+=1
        return out
    return None

def lay_run(wn,cfg,k,a,b,side,eL,eR):
    raw=grid_raw(cfg,k,side,a,b)
    assert raw,("empty run",wn,k,a,b)
    if eL=="corner":
        assert abs(raw[0][0]-a)<EPS and raw[0][1]-raw[0][0]>FULL-EPS,("cornerL",wn,k,a,raw[0])
    if eR=="corner":
        assert abs(raw[-1][1]-b)<EPS and raw[-1][1]-raw[-1][0]>FULL-EPS,("cornerR",wn,k,b,raw[-1])
    probL=eL!="corner" and (raw[0][0]-a>EPS or raw[0][1]-raw[0][0]<MIN_CUT-EPS)
    probR=eR!="corner" and (b-raw[-1][1]>EPS or raw[-1][1]-raw[-1][0]<MIN_CUT-EPS)
    assert not (probL and probR),("both-edge problem",wn,k,a,b)
    if probL:
        out=flush_converge(wn,k,a,b,raw,eR)
        if out is None: out=respace(wn,k,a,b,raw,"L",eR)
        assert out is not None,("left fix failed",wn,k,a,b)
        return out
    if probR:
        out=respace(wn,k,a,b,raw,"R",eL)
        assert out is not None,("right fix failed",wn,k,a,b)
        return out
    return raw

def lay_meet(wn,cfg,k):
    """full-width clear course on a two-corner wall: grids meet mid-wall"""
    P=cfg["uL"]+setback(cfg["lapE_L"],k); E=cfg["uR"]-setback(cfg["lapE_R"],k)
    W=snap(E-P); r=snap(W%MOD)
    if MIN_CUT-EPS<=r<FULL-EPS:
        n=int(round((W-r)/MOD)); mid=(cfg["uL"]+cfg["uR"])/2.0
        nL=max(0,min(n,int(round((mid-P-r/2.0)/MOD))))
        out=[[P+i*MOD,P+i*MOD+FULL] for i in range(nL)]
        cu=P+nL*MOD; out.append([cu,cu+r])
        out+=[[cu+r+J+i*MOD,cu+r+J+i*MOD+FULL] for i in range(n-nL)]
        assert abs(out[-1][1]-E)<EPS
        MEET[(wn,"mid make-up cut %.4g @u%.5g"%(r,cu))]+=1
        return out,True
    if r<MIN_CUT: n=int(round((W-r)/MOD)); A=snap(r+J)
    else:         n=int(round((W-r)/MOD))+1; A=snap(r-FULL)
    fats=bres(A,n-1)
    assert fats is not None,("meet dead-zone infeasible",wn,k,r)
    out=[]; u=P
    for i in range(n):
        out.append([u,u+FULL])
        u=snap(u+MOD+(fats[i] if i<n-1 else 0.0))
    assert abs(out[-1][1]-E)<EPS,("meet flush",wn,k,out[-1][1],E)
    MEET[(wn,"all-full n=%d (+%.4gmm over %d joints)"%(n,A,n-1))]+=1
    return out,False

def lay_wall(wn,cfg,wall):
    ops=openings_for(wall,wn); new=[]
    for k in range(39):
        z0=k*CP; z1=z0+(H if k<38 else TOP_H[wn])
        for (sL,sR) in band_segments(cfg,ops,z0,z1):
            full_wall=abs(sL-cfg["uL"])<EPS and abs(sR-cfg["uR"])<EPS
            if wn in SPLIT and full_wall:
                prs,_=lay_meet(wn,cfg,k); mkL=mkR=None; is_meet=True
            else:
                is_meet=False
                if wn in SPLIT:
                    sp=SPLIT[wn]
                    if sR<=sp[0]+EPS: side="L"
                    elif sL>=sp[1]-EPS: side="R"
                    else: raise AssertionError(("segment crosses split",wn,k,sL,sR))
                else:
                    side="L" if cfg["left"]=="corner" else "R"
                eL=("corner" if (cfg["left"]=="corner" and abs(sL-cfg["uL"])<EPS) else
                    "free" if (cfg["left"]=="free" and abs(sL-cfg["uL"])<EPS) else "jamb")
                eR=("corner" if (cfg["right"]=="corner" and abs(sR-cfg["uR"])<EPS) else
                    "free" if (cfg["right"]=="free" and abs(sR-cfg["uR"])<EPS) else "jamb")
                a=sL+(setback(cfg["lapE_L"],k) if eL=="corner" else 0.0)
                b=sR-(setback(cfg["lapE_R"],k) if eR=="corner" else 0.0)
                prs=lay_run(wn,cfg,k,a,b,side,eL,eR)
                mkL="free" if eL=="free" else ("jamb" if eL=="jamb" else None)
                mkR="free" if eR=="free" else ("jamb" if eR=="jamb" else None)
            for i,(u0,u1) in enumerate(prs):
                mk=None
                if u1-u0<FULL-EPS:
                    mk="meet" if is_meet else (mkL if i==0 else (mkR if i==len(prs)-1 else None))
                new.append(piece(u0,z0,u1,z1,mk))
        for (sk,s0,s1,f0,f1) in STRIPS.get(wn,[]):
            if sk!=k: continue
            nn=int(round((f1-f0+J)/MOD))
            assert abs(nn*MOD-J-(f1-f0))<EPS
            for i in range(nn): new.append(piece(f0+i*MOD,s0,f0+i*MOD+FULL,s1))
    new.sort(key=lambda br:(int(min(v[1] for v in br["verts"])//CP),
                            min(v[0] for v in br["verts"])))
    return new

def main():
    R=json.load(open(SRC))
    if not os.path.isfile(BAK): shutil.copy2(SRC,BAK)
    nlap=sum(1 for w in WALLS for b in R[w]["bricks"] if b.get("cp")=="lap")
    nhalf=sum(1 for w in WALLS for b in R[w]["bricks"] if b.get("cp")=="half")
    assert nlap==117 and nhalf==117,(nlap,nhalf)
    stats={}
    for wn in sorted(WALLS):
        cfg=WALLS[wn]; wall=R[wn]
        keep=[b for b in wall["bricks"] if b.get("cp") in ("lap","half")]
        new=lay_wall(wn,cfg,wall)
        wall["bricks"]=new+keep
        Lof=lambda b:max(v[0] for v in b["verts"])-min(v[0] for v in b["verts"])
        stats[wn]=dict(field=len(new),lap=sum(1 for b in keep if b["cp"]=="lap"),
                       half=sum(1 for b in keep if b["cp"]=="half"),
                       full=sum(1 for b in new if abs(Lof(b)-FULL)<1e-6),
                       cut=sum(1 for b in new if Lof(b)<FULL-1e-6))
    json.dump(R,open(SRC,"w"))
    print("FIELD RE-LAY v4 (CONTINUOUS GRID) DONE")
    tot=collections.Counter()
    for w in sorted(stats):
        s=stats[w]; tot.update(s)
        print("  %-12s field=%4d (%4d full-len + %3d single cuts) corners %d+%d tot=%4d"
              %(w,s["field"],s["full"],s["cut"],s["lap"],s["half"],s["field"]+s["lap"]+s["half"]))
    print("  TOTAL field=%d = %d full-len + %d cuts ; corners 117 lap+117 half ; RED=%d"
          %(tot["field"],tot["full"],tot["cut"],tot["field"]+234))
    print("MEET / clear-course handling:")
    for key,cnt in sorted(MEET.items()): print("   %-12s %-42s x%d courses"%(key[0],key[1],cnt))
    print("MIN_CUT FIXES (mechanism -> courses):")
    for key,cnt in sorted(DEV.items()): print("   %-12s %-34s par%d x%d"%(key[0],key[1],key[2],cnt))
    print("DOCUMENTED JAMB GAPS (10..12mm joint at jamb):")
    for key,cnt in sorted(GAPDOC.items()): print("   %-12s %-28s par%d x%d"%(key[0],key[1],key[2],cnt))

if __name__=="__main__":
    main()
