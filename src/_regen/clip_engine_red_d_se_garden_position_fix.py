#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  CLIP ENGINE (FIXED) - reads stairfix red + fixed black (no U-brick); clip 0.25mm; Type-IDs
#  Fixes:
#   (A) clip = course band INTERSECT actual brick coverage  -> no overhang, no
#       floating clip; every clip sits on a real brick back, within its edges.
#   (B) STANDARD-ONLY everywhere except the black SLOPED canopy: vertical faces
#       (red walls, black +-X walls, front-frame rectangular part) use only
#       1000/500/250/20 mm pieces (no arbitrary cut); 5 mm gaps; remainder filled
#       with 20 mm patches; small end gap allowed (no non-standard cut).
#   (C) Black SLOPED canopy (front-frame gable + the two pitched slopes) may use
#       ANGLED pieces: standard mother length (1000/500/250/20) end-cut to the
#       sloped top AND bottom / verge boundaries, clipped exactly to the bricks.
#   (D) L-legs folded into their wall/frame face coverage (no separate floating
#       short clips).
#  v3 change: black SLOPED CANOPY (gable triangle + pitched slopes) uses NO
#  20mm patches - long stock (1000/500/250) cut to a one-piece that fits the
#  sloped boundary (final remainder = one cut piece from the smallest stock).
#  Red + black ORDINARY regions keep standard 1000/500/250/20 + 20mm patches.
#  Each clip tagged with region: red | black_ordinary | black_sloped_canopy.
#  Reads existing placements ONLY; writes clip_instances_v3.json.
# ============================================================================
import json, os, math, collections
from shapely.geometry import Polygon, box, MultiPolygon, GeometryCollection
from shapely.ops import unary_union

HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,"..")
RED=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix.json")))
BLACK=json.load(open(os.path.join(INP,"black_placement_fixed7.json")))["bricks"]
MM=0.001; CLIP_W=68.0; COURSE_P=75.0; GAP=5.0; MINSEG=20.0; MERGE=16.0
STOCK=[1000.0,700.0,500.0,300.0,250.0,100.0,50.0]   # preferred pieces big->small (added 700/300/100/50)
FILL=[50.0,20.0]                                     # tail/middle filler; 20mm ONLY as last resort
CLIP_THICK_MM=0.25   # v2: clip thickness 1mm -> 0.25mm
BOFF=(5.766,-0.370,0.0)   # v2: depth 700 -> back stays just in front of red skin

def v3(a): return (a[0],a[1],a[2])
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
    L=math.sqrt(dot(a,a)); return (a[0]/L,a[1]/L,a[2]/L) if L>1e-9 else (0,0,0)

def _greedy(L,stk,fill):
    out=[]; pos=0.0
    while True:
        gap=0.0 if not out else GAP; space=L-(pos+gap); p=None
        for st in stk:
            if space>=st-1e-6: p=st; break
        if p is None: break
        out.append((pos+gap,p)); pos+=gap+p
    gap=0.0 if not out else GAP; rem=L-(pos+gap)          # ONE final filler (<=1 twenty per run)
    for fz in fill:
        if rem>=fz-1e-6: out.append((pos+gap,fz)); break
    return out
def _both(L,stk,fill):
    res=[]; lo=0.0; hi=L; turn=0
    while True:
        if turn==0:
            gap=0.0 if lo<=1e-6 else GAP; avail=(hi-lo)-gap; s=None
            for st in stk:
                if avail>=st-1e-6: s=st; break
            if s is None: break
            res.append((lo+gap,s)); lo+=gap+s
        else:
            gap=0.0 if (L-hi)<=1e-6 else GAP; avail=(hi-lo)-gap; s=None
            for st in stk:
                if avail>=st-1e-6: s=st; break
            if s is None: break
            res.append((hi-gap-s,s)); hi-=gap+s
        turn^=1
    gap=GAP; rem=(hi-lo)-gap                                # one middle filler
    for fz in fill:
        if rem>=fz-1e-6: res.append((lo+gap,fz)); break
    return sorted(res)
def std_pieces(L, anchor="low", maxp=None, allow20=True):
    """Cover [0,L] big-first (5mm gaps). anchor: 'low' long pieces from u=0; 'high' from u=L;
       'both' long pieces start at BOTH ends, gap in the middle. maxp caps the largest piece.
       allow20=False drops the final <=49mm filler entirely (small space left bare, no 20mm)."""
    if L<=0: return []
    stk=STOCK if maxp is None else [x for x in STOCK if x<=maxp+1e-6]
    fill=FILL if allow20 else [x for x in FILL if x>=50-1e-6]
    if anchor=="both" and L>2*stk[0]: return _both(L,stk,fill)
    out=_greedy(L,stk,fill)
    if anchor=="high": out=sorted([(L-(p+ln),ln) for (p,ln) in out])
    return out

SPRING_Z=5325.0   # front-frame: rectangular lintel below, gable triangle above
def canopy_pieces(L):
    """Sloped-canopy: a course/segment <=1000mm is ONE clip cut to fit (both ends raked
    where they meet a sloped edge) - NOT split into pieces with a gap. Wider courses use
    full 1000mm pieces + a single final cut. NO 20mm in the canopy."""
    out=[]; pos=0.0
    while True:
        gap=0.0 if not out else GAP; rem=L-(pos+gap)
        if rem<1: break
        if rem<=1000.0+1e-6:
            src=250 if rem<=250 else (500 if rem<=500 else 1000)
            out.append((pos+gap, rem, src, True)); break          # ONE cut piece for the remainder
        out.append((pos+gap, 1000.0, 1000, False)); pos+=gap+1000.0
    # avoid a sliver final cut: rebalance a <120mm final cut with the preceding full 1000
    if len(out)>=2 and out[-1][3] and out[-1][1]<120 and out[-2][1]==1000.0 and not out[-2][3]:
        ps=out[-2][0]; ls,ll=out[-1][0],out[-1][1]; span=(ls+ll)-ps; half=(span-GAP)/2.0
        src=250 if half<=250 else (500 if half<=500 else 1000)
        out[-2]=(ps,half,src,True); out[-1]=(ps+half+GAP,half,src,True)
    return out

clips=[]
def emit(colour,face,region,kind,poly3d,normal,length,source,angle,reason):
    clips.append(dict(colour=colour,face=face,region=region,kind=kind,
        length=round(length,1),source=int(source),
        angled=(kind=="angled"), is_cut=(kind in("angled","cut")), angle=round(angle,1),
        reason=reason, thick_mm=CLIP_THICK_MM, poly=[[round(c,4) for c in p] for p in poly3d], normal=[round(c,3) for c in normal]))

def canonicalize(uv):
    """Reduce any clip outline to a CLEAN quad (rectangle or right-trapezoid): bottom edge
    [b0,b1] at vmin, top edge [t0,t1] at vmax. Removes pentagons/weird shapes so the model,
    DXF1 (cut sheet) and DXF2 (wall layout) all show the SAME shape per clip."""
    vmin=min(p[1] for p in uv); vmax=max(p[1] for p in uv)
    bot=[p[0] for p in uv if abs(p[1]-vmin)<2.0]; top=[p[0] for p in uv if abs(p[1]-vmax)<2.0]
    if not bot or not top:
        umin=min(p[0] for p in uv); umax=max(p[0] for p in uv)
        return [(umin,vmin),(umax,vmin),(umax,vmax),(umin,vmax)]
    b0,b1=min(bot),max(bot); t0,t1=min(top),max(top)
    return [(b0,vmin),(b1,vmin),(t1,vmax),(t0,vmax)]
def shape_name(uv):
    """Name a clip's true outline: rectangle / parallelogram / trapezoid (two raked sides) /
    right-trapezoid (one vertical + one raked) / triangle."""
    if len(uv)==3: return "triangle"
    vs=[p[1] for p in uv]; vmn,vmx=min(vs),max(vs)
    bot=[p for p in uv if abs(p[1]-vmn)<2.0]; top=[p for p in uv if abs(p[1]-vmx)<2.0]
    if len(bot)<2 or len(top)<2: return "quad"
    b0=min(p[0] for p in bot); b1=max(p[0] for p in bot); t0=min(p[0] for p in top); t1=max(p[0] for p in top)
    Lsh=t0-b0; Rsh=t1-b1; Ls=abs(Lsh)>4.0; Rs=abs(Rsh)>4.0; bw=b1-b0; tw=t1-t0
    if (bw<6.0 or tw<6.0): return "triangle"
    if not Ls and not Rs: return "rectangle"
    if Ls and Rs:
        if Lsh*Rsh>0 and abs(Lsh-Rsh)<8.0: return "parallelogram"
        return "trapezoid"
    return "right-trapezoid"
def longest_diag(uv):
    """angle (from horizontal) of the LONGEST non-axis edge; (length,angle). Used so a
    clip's reported cut angle is its dominant rake, not a spurious short knee edge."""
    best=(0.0,0.0); n=len(uv)
    for i in range(n):
        x0,y0=uv[i]; x1,y1=uv[(i+1)%n]; dx=x1-x0; dy=y1-y0; L=math.hypot(dx,dy)
        if L<1: continue
        if abs(dx)<3.0 or abs(dy)<3.0: continue      # axis-aligned within 3 mm
        a=math.degrees(math.atan2(abs(dy),abs(dx)))   # from horizontal
        if L>best[0]: best=(L,a)
    return best
def poly_angle(pts2d):
    """max deviation of any edge from horizontal/vertical (deg) -> the cut rake."""
    best=0.0
    n=len(pts2d)
    for i in range(n):
        x0,y0=pts2d[i]; x1,y1=pts2d[(i+1)%n]; dx=x1-x0; dy=y1-y0
        if abs(dx)<1e-6 or abs(dy)<1e-6: continue   # axis-aligned edge
        a=math.degrees(math.atan2(abs(dy),abs(dx)))
        dev=min(a,90-a)            # rake from the nearest axis
        best=max(best,90-a if a>45 else a)
        best=max(best, min(a,90-a))
    return best

# ---------------- RED (all vertical -> standard only) ----------------
WX=11513.0; WY=13604.0
RFRAME={"C_NW_front":((0,0,0),(1,0,0),(0,0,1),(0,-1,0)),
        "A_NE_side":((0,WY*MM,0),(0,-1,0),(0,0,1),(-1,0,0)),   # FIX: left side, deep/stair end at back (beside D_SE), outward West
        "D_SE_garden":(((WX+997)*MM,WY*MM,0),(-1,0,0),(0,0,1),(0,1,0)),   # FIX: slid +997mm east -> stair-end seats flush on A_NE (x=0)
        "B_SW_side":((WX*MM,0,0),(0,1,0),(0,0,1),(1,0,0))}   # FIX: right side, outward East
RC={"C_NW_front":(True,True),"A_NE_side":(True,True),"B_SW_side":(True,False),"D_SE_garden":(False,True)}   # FIX: D_SE now abuts A_NE at its WEST(u=max) end; free east(u=0) end -> no clip overhang
# FLAT CORNERS: the corner lap slips extend 20mm PAST the structural arris (u<0 or u>wall length).
# Clips mount on the substrate, so red coverage is CLAMPED to the structural wall domain:
UDOM={"C_NW_front":(0.0,11513.0),"A_NE_side":(0.0,13604.0),"B_SW_side":(0.0,None),"D_SE_garden":(None,12510.0)}
for nm,d in RED.items():
    O,U,V,N=RFRAME[nm]; lc,rc=RC[nm]
    ulo,uhi=UDOM[nm]
    def _cl(u):
        if ulo is not None: u=max(u,ulo)
        if uhi is not None: u=min(u,uhi)
        return u
    umax=max(_cl(v[0]) for br in d["bricks"] for v in br["verts"])
    zmin=min(v[1] for br in d["bricks"] for v in br["verts"]); zmax=max(v[1] for br in d["bricks"] for v in br["verts"])
    courses=collections.defaultdict(list)
    for br in d["bricks"]:
        vs=[v[1] for v in br["verts"]]; us=[v[0] for v in br["verts"]]
        u0,u1=_cl(min(us)),_cl(max(us))
        if u1-u0>1.0: courses[round(((min(vs)+max(vs))/2)/COURSE_P)].append((u0,u1))
    for kk,it in sorted(courses.items()):
        it.sort(); vC=(min(a[0] for a in it),0)  # placeholder
        vmidlist=[(a[0],a[1]) for a in it]
        vC=sum(((a[0]+a[1])/2) for a in it)/len(it)  # not used; need v centre
        # course centre v from bricks
        # rebuild proper vC
        vcs=[ (sum(vv for vv in [])) ]
        # compute course v centre from one brick band
        # (use the course index*pitch approximation but clamp)
        zc=None
        zc=None
        # get v centre from bricks of this course
        zb=[]
        for br in d["bricks"]:
            vs=[v[1] for v in br["verts"]]
            if round(((min(vs)+max(vs))/2)/COURSE_P)==kk: zb+=vs
        vC=(min(zb)+max(zb))/2.0
        vC=min(max(vC,zmin+CLIP_W/2),zmax-CLIP_W/2) if (zmax-zmin)>=CLIP_W else (zmin+zmax)/2
        # merge runs
        runs=[]; cs,ce=it[0]
        for a0,a1 in it[1:]:
            if a0-ce<=MERGE: ce=max(ce,a1)
            else: runs.append((cs,ce)); cs,ce=a0,a1
        runs.append((cs,ce))
        for r0,r1 in runs:
            a_low=bool(lc and r0<=230); a_high=bool(rc and (umax-r1)<=230)
            if a_low: r0=0.0
            if a_high: r1=umax
            anc="both" if (a_low and a_high) else ("high" if a_high else "low")
            if nm=="D_SE_garden": anc="both"          # FIX: D_SE clips start aligned from BOTH wall edges -> window
            for (s,ln) in std_pieces(r1-r0, anc, allow20=False):   # FIX: red omits the final <=49mm 20mm filler (small space left bare)
                u0=r0+s; v0=vC-CLIP_W/2; v1=vC+CLIP_W/2
                poly=[add(add(O,mul(U,(u0)*MM)),mul(V,v0*MM)), add(add(O,mul(U,(u0+ln)*MM)),mul(V,v0*MM)),
                      add(add(O,mul(U,(u0+ln)*MM)),mul(V,v1*MM)), add(add(O,mul(U,(u0)*MM)),mul(V,v1*MM))]
                emit("Red",nm,"red","standard",poly,N,ln,int(ln),0.0,"wall course (standard)")

# ---------------- BLACK ----------------
def rnd(n): return (round(n[0],2),round(n[1],2),round(n[2],2))
flats=[b for b in BLACK if b["cat"] in("flat_full","flat_cut")]
Ls=[b for b in BLACK if b["cat"].startswith("L_corner")]
def inplane(n):
    n=unit(n)
    if abs(n[1])>0.9: return (1.,0.,0.),(0.,0.,1.)   # front frame (normal +-Y): U=X, V=Z
    if abs(n[0])>0.9: return (0.,1.,0.),(0.,0.,1.)   # side walls (normal +-X): U=Y, V=Z
    U=unit(cross(n,(0.,0.,1.)))                       # pitched slope: U horizontal in-plane
    V=unit(cross(U,n))                                # V up-slope, in-plane
    if V[2]<0: V=(-V[0],-V[1],-V[2])
    return U,V
# group flats by face
byface=collections.defaultdict(list)
for b in flats:
    n=tuple(b["normal"]); cc=[sum(v[i] for v in b["verts"])/len(b["verts"]) for i in range(3)]
    byface[(rnd(n),round(dot(cc,n)/20)*20)].append(b)
# split L legs -> add to matching face by normal
def legs_of(b):
    hx=[tuple(v) for v in b["verts"]]
    if len(hx)<6: return []
    A_in,A_out,cor,B_out,B_in,C0=hx
    out=[]
    for (P0,P1,Pout) in ((C0,A_in,A_out),(C0,B_in,B_out)):
        nrm=unit(cross(unit((P1[0]-P0[0],P1[1]-P0[1],P1[2]-P0[2])),(0,0,1)))
        # face normal = direction from leg line outward = (Pout - P1) approx
        nout=unit((Pout[0]-P1[0],Pout[1]-P1[1],Pout[2]-P1[2]))
        # build a thin rectangle (leg) as a pseudo-brick on that face
        zc=C0[2]
        out.append((P0,P1,nout))
    return out
legbyface=collections.defaultdict(list)
for b in Ls:
    for (P0,P1,nout) in legs_of(b):
        legbyface[(rnd(nout),round(dot(P1,nout)/20)*20)].append((P0,P1,b["cat"]))

def is_sloped_face(n):
    # pitched slope = normal neither in a vertical plane (nz~0) nor flat (|nz|~1)
    return 0.1 < abs(rnd(n)[2]) < 0.95

for (nkey,off),brs in byface.items():
    n=nkey; U,V=inplane(n)
    # all verts for this face (flats) + legs that belong here
    allbr=[b["verts"] for b in brs]
    legverts=[]
    for (P0,P1,cat) in legbyface.get((nkey,off),[]):
        # leg rectangle in 3D: P0->P1 (length) x 65 up (z), thin
        h=65.0
        legverts.append([list(P0),list(P1),[P1[0],P1[1],P1[2]+h],[P0[0],P0[1],P0[2]+h]])
    allverts=allbr+legverts
    # in-plane origin
    pts=[p for poly in allverts for p in poly]
    O3=[0,0,0]
    # O3 = mean(vert - U*(u) - V*(v))
    accum=[0.,0.,0.]
    for p in pts:
        u=dot(p,U); v=dot(p,V)
        for i in range(3): accum[i]+= p[i]-U[i]*u-V[i]*v
    O3=[a/len(pts) for a in accum]
    def to3d(u,v):  # canopy-local mm -> world m
        c=add(add(tuple(O3),mul(U,u)),mul(V,v)); return add(mul(c,MM),BOFF)
    # build coverage polygon(s) in (u,v)
    polys=[]
    for poly in allverts:
        uv=[(dot(p,U),dot(p,V)) for p in poly]
        try:
            pg=Polygon(uv)
            if pg.is_valid and pg.area>1: polys.append(pg)
        except Exception: pass
    if not polys: continue
    cover=unary_union(polys).buffer(8.0,join_style=2).buffer(-8.0,join_style=2)  # close 10mm joints into runs
    minu,minv,maxu,maxv=cover.bounds
    sloped=is_sloped_face(n)
    is_front=abs(n[1])>0.9
    fid="black_"+("slopeL" if (sloped and n[0]>0) else "slopeR" if (sloped and n[0]<0) else ("frontframe" if is_front else ("wallXp" if n[0]>0.5 else "wallXn")))+f"_{off:+.0f}"
    k=0
    v=minv
    # course bands aligned so a band centre sits on brick rows
    kstart=int(math.floor(minv/COURSE_P))
    for kk in range(kstart,int(math.ceil(maxv/COURSE_P))+1):
        vc=kk*COURSE_P+COURSE_P/2 if False else kk*COURSE_P
    # iterate course bands by 75 from minv
    kk=0; base=minv
    while base+kk*COURSE_P < maxv-1e-6:
        v0=base+kk*COURSE_P; v1=v0+CLIP_W
        bandpoly=cover.intersection(box(minu-1,v0,maxu+1,v1))
        kk+=1
        if bandpoly.is_empty or bandpoly.area<MINSEG*MINSEG*0.4: continue
        parts=[bandpoly] if bandpoly.geom_type=="Polygon" else [g for g in bandpoly.geoms if g.geom_type=="Polygon"]
        for part in parts:
            pminu,pv0,pmaxu,pv1=part.bounds
            # rectangular? (area ~ full bbox)
            rect = abs(part.area-(pmaxu-pminu)*(pv1-pv0))<60.0
            course_sloped = sloped or is_front   # whole gable FRAME + pitched slopes = sloped canopy
            region = "black_sloped_canopy" if course_sloped else "black_ordinary"
            if course_sloped:
                # 6-TYPE canopy: T_LEFT_40 / T_RIGHT_40 FIXED trapezoids on the gable-front rakes
                # (top=30, bottom=111, H=68, 40deg); rectangular standard clips 1000/500/250/20
                # fill the vertical-overlap middle (no exceed). Slopes + legs = rectangles only.
                q=canonicalize(list(part.exterior.coords)[:-1])
                (bL,vmn),(bR,_a),(tR,vmx),(tL,_b)=q
                if (bR-bL)<MINSEG or (vmx-vmn)<1: continue
                dxL=tL-bL; dxR=tR-bR; TBOT=111.0; TOPW=30.0; RUN=81.0
                cur=bL; end=bR
                # LEFT edge rake -> T_LEFT_40 (vertical edge inward, sloped edge hugs the band edge):
                #   outer (up-right, dxL>0) = normal (bottom 111); inner (up-left, dxL<0) = mirrored/flipped (bottom 30)
                if is_front and abs(dxL)>6 and (vmx-vmn)>=66:
                    XR=bL+(TBOT if dxL>0 else TOPW)
                    if XR<bR-1:
                        topL=bL+(RUN if dxL>0 else -RUN)
                        uvT=[(bL,vmn),(XR,vmn),(XR,vmx),(topL,vmx)]
                        emit("Black",fid,region,"angled",[to3d(u,vv) for u,vv in uvT],n,TBOT,250,40.0,
                             "TLEFT 40deg trapezoid (%s)"%("outer" if dxL>0 else "inner-mirror"))
                        cur=XR+GAP
                # RIGHT edge rake -> T_RIGHT_40: outer (up-left, dxR<0)=normal; inner (up-right, dxR>0)=mirrored/flipped
                if is_front and abs(dxR)>6 and (vmx-vmn)>=66:
                    XL=bR-(TBOT if dxR<0 else TOPW)
                    if XL>cur+1:
                        topR=bR+(-RUN if dxR<0 else RUN)
                        uvT=[(XL,vmn),(bR,vmn),(topR,vmx),(XL,vmx)]
                        emit("Black",fid,region,"angled",[to3d(u,vv) for u,vv in uvT],n,TBOT,250,40.0,
                             "TRIGHT 40deg trapezoid (%s)"%("outer" if dxR<0 else "inner-mirror"))
                        end=XL-GAP
                ovL=max(bL,tL); ovR=min(bR,tR); fillL=max(cur,ovL); fillR=min(end,ovR)
                run=max(0.0,fillR-fillL)
                if is_front and vmn<SPRING_Z and 290.0<=run<=370.0:   # NARROW door-side jamb ONLY -> ONE R300 centred (~12mm gap each side)
                    off=(run-300.0)/2.0; u0=fillL+off
                    uvR=[(u0,vmn),(u0+300.0,vmn),(u0+300.0,vmx),(u0,vmx)]
                    emit("Black",fid,region,"standard",[to3d(u,vv) for u,vv in uvR],n,300.0,300,0.0,"canopy front jamb R300 centred")
                else:                                                  # gable arms / lintel / soffit slopes -> greedy FULL coverage (fixes side voids)
                    for (st,ln) in std_pieces(run):
                        u0=fillL+st; uvR=[(u0,vmn),(u0+ln,vmn),(u0+ln,vmx),(u0,vmx)]
                        emit("Black",fid,region,"standard",[to3d(u,vv) for u,vv in uvR],n,ln,int(ln),0.0,"canopy rectangle R%d"%int(ln))
            else:
                for (st,ln) in std_pieces(pmaxu-pminu, maxp=700.0):
                    seg=part.intersection(box(pminu+st, pv0-1, pminu+st+ln, pv1+1))
                    if seg.is_empty or seg.area<MINSEG*MINSEG*0.4: continue
                    segs=[seg] if seg.geom_type=="Polygon" else [g for g in seg.geoms if g.geom_type=="Polygon"]
                    for sg in segs:
                        uv0=canonicalize(list(sg.exterior.coords)[:-1])
                        umn=min(p[0] for p in uv0); umx=max(p[0] for p in uv0); vmn=min(p[1] for p in uv0); vmx=max(p[1] for p in uv0)
                        uv=[(umn,vmn),(umx,vmn),(umx,vmx),(umn,vmx)]
                        poly3=[to3d(u,vv) for (u,vv) in uv]
                        emit("Black",fid,region,"standard",poly3,n,ln,int(ln),0.0,"wall course (standard)")

# ---------------- summary ----------------
def summ(cl):
    tot=sum(c["length"] for c in cl); bylen=collections.Counter(c["source"] for c in cl)
    return dict(pieces=len(cl),total_len_m=round(tot/1000,2),
                standard=sum(1 for c in cl if c["kind"]=="standard"),
                cut=sum(1 for c in cl if c["kind"]=="cut"),
                angled=sum(1 for c in cl if c["angled"]),
                by_stock={str(k):v for k,v in sorted(bylen.items())})
red=[c for c in clips if c["colour"]=="Red"]; blk=[c for c in clips if c["colour"]=="Black"]
ordn=[c for c in clips if c["region"]=="black_ordinary"]; cano=[c for c in clips if c["region"]=="black_sloped_canopy"]
ang_outside=[c for c in clips if c["angled"] and c["region"]!="black_sloped_canopy"]
cut_outside=[c for c in clips if c["is_cut"] and c["region"]!="black_sloped_canopy"]
canopy_20=[c for c in cano if c["source"]==20]
nonstd_ord=[c for c in clips if c["region"] in("red","black_ordinary") and c["source"] not in (1000,700,500,300,250,100,50,20)]
res=dict(red=summ(red),black=summ(blk),all=summ(clips),
         black_ordinary=summ(ordn),black_sloped_canopy=summ(cano),
         angled_or_cut_outside_canopy=len(ang_outside)+len(cut_outside),
         canopy_20mm_pieces=len(canopy_20), nonstandard_in_ordinary=len(nonstd_ord))
here=os.path.dirname(os.path.abspath(__file__))
# ---------- per-clip face-2D outline (mm) + Type-ID + colour ----------
def face_uv(c):
    n=tuple(c["normal"]); U,V=inplane(n)
    return [(round(dot([(p[i]-BOFF[i])/MM for i in range(3)],U),1),
             round(dot([(p[i]-BOFF[i])/MM for i in range(3)],V),1)) for p in c["poly"]]
def edge_dims(uv):
    # bottom/top = horizontal edges (low/high v); left/right = vertical-ish; diag = rake
    n=len(uv); edges=[]
    for i in range(n):
        x0,y0=uv[i]; x1,y1=uv[(i+1)%n]; dx=x1-x0; dy=y1-y0; L=math.hypot(dx,dy)
        if L<1: continue
        horiz=abs(dy)<3; vert=abs(dx)<3
        edges.append(dict(L=round(L,1),mx=(x0+x1)/2,my=(y0+y1)/2,horiz=horiz,vert=vert,
                          ang=(0.0 if (horiz or vert) else round(math.degrees(math.atan2(abs(dy),abs(dx))),1))))
    h=[e for e in edges if e["horiz"]]; v=[e for e in edges if e["vert"]]; d=[e for e in edges if not e["horiz"] and not e["vert"]]
    bottom=min(h,key=lambda e:e["my"])["L"] if h else 0.0
    top=max(h,key=lambda e:e["my"])["L"] if h else 0.0
    left=min(v,key=lambda e:e["mx"])["L"] if v else 0.0
    right=max(v,key=lambda e:e["mx"])["L"] if v else 0.0
    diag=max(d,key=lambda e:e["L"])["L"] if d else 0.0
    dang=max(d,key=lambda e:e["L"])["ang"] if d else 0.0
    return dict(bottom=bottom,top=top,left=left,right=right,diag=round(diag,1),diag_angle=dang)
for c in clips:
    c["uv"]=face_uv(c); c["edges"]=edge_dims(c["uv"]); c["shape"]=shape_name(c["uv"])
# ---- 6 ALLOWED CLIP TYPES ONLY: R1000 R500 R250 R20 T_LEFT_40 T_RIGHT_40 ----
COL6={"R1000":("blue",5),"R700":("orange",30),"R500":("green",3),"R300":("yellow",2),"R250":("cyan",4),"R100":("ltblue",140),"R50":("violet",210),"R20":("grey",8),"T_LEFT_40":("red",1),"T_RIGHT_40":("magenta",6)}
def type_of(c):
    r=c.get("reason","")
    if r.startswith("TLEFT"):  return "T_LEFT_40"
    if r.startswith("TRIGHT"): return "T_RIGHT_40"
    return "R%d"%int(c["source"])
for c in clips:
    tid=type_of(c); c["type_id"]=tid; c["colour_name"]=COL6[tid][0]; c["aci"]=COL6[tid][1]
    c["angled"]=tid.startswith("T_"); c["is_cut"]=tid.startswith("T_")
ORDER=["R1000","R700","R500","R300","R250","R100","R50","R20","T_LEFT_40","T_RIGHT_40"]
typetable=[]
for tid in ORDER:
    cs=[c for c in clips if c["type_id"]==tid]
    if not cs: continue
    rr=cs[0]; ou=min(p[0] for p in rr["uv"]); ov=min(p[1] for p in rr["uv"])
    outline=[[round(p[0]-ou,1),round(p[1]-ov,1)] for p in rr["uv"]]
    isT=tid.startswith("T_")
    typetable.append(dict(type_id=tid,colour=COL6[tid][0],aci=COL6[tid][1],
        kind=("angled" if isT else "standard"),shape=("right-trapezoid" if isT else "rectangle"),
        source=int(rr["source"]),length=round(sum(x["length"] for x in cs)/len(cs)),qty=len(cs),
        region_set=sorted(set(x["region"] for x in cs)),angle=(40.0 if isT else 0.0),
        edges=rr["edges"],outline=outline,top=(30.0 if isT else None),bottom=(111.0 if isT else None)))
json.dump(dict(clips=clips,summary=res,types=typetable),open(os.path.join(INP,"clip_instances_red_d_se_garden_position_fix.json"),"w"))
print("\nCLIP TYPES (%d):"%len(typetable))
for t in typetable:
    print("  %-10s %-8s %-14s src%-4d len%-5d ang%-3.0f qty%-5d  %s"%(t["type_id"],t["colour"],t["shape"],t["source"],t["length"],t["angle"],t["qty"],",".join(t["region_set"])))
print("RED            :",res["red"])
print("BLACK ordinary :",res["black_ordinary"])
print("BLACK canopy   :",res["black_sloped_canopy"])
print("BLACK total    :",res["black"])
print("ALL            :",res["all"])
print("CHECK angled/cut OUTSIDE canopy (=0):",res["angled_or_cut_outside_canopy"])
print("CHECK 20mm IN canopy (=0):",res["canopy_20mm_pieces"])
print("CHECK non-standard in ordinary (=0):",res["nonstandard_in_ordinary"])
