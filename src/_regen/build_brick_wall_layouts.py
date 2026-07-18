#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-wall (red) + per-face (black) brick-slip LAYOUT DXFs - FLAT-CORNER edition.
The red one-piece corner L-slips are GONE: each of the 3 red corners is covered per course
by a FULL 215 flat slip lapping the arris + a HALF 107.5 flat slip butting it (in the
placement JSON, markers cp=lap/half). They are drawn as normal bricks on their own wall
(the lap extends 20mm past the arris line) + outlined magenta on layer CORNERFLAT.
Black canopy = 9 faces (unchanged, incl. its 272 black L-corners)."""
import json,os,math,collections,ezdxf
HERE=os.path.dirname(os.path.abspath(__file__)); INP=os.path.join(HERE,".."); OUT=os.path.join(HERE,"..")
RED=json.load(open(os.path.join(INP,"red_brick_placement_v7_stairfix.json")))
BLK=json.load(open(os.path.join(INP,"black_placement_fixed7.json")))["bricks"]
BT={t["type_id"]:t for t in json.load(open(os.path.join(INP,"brick_types.json")))["types"]}
TOL=5.0; FULL_W,FULL_H=215.0,65.0
def parea(p):
    a=0.0
    for i in range(len(p)): x1,y1=p[i]; x2,y2=p[(i+1)%len(p)]; a+=x1*y2-x2*y1
    return abs(a)/2
def dedup(pts):
    o=[]
    for p in pts:
        if not o or abs(p[0]-o[-1][0])>0.5 or abs(p[1]-o[-1][1])>0.5: o.append((round(p[0],1),round(p[1],1)))
    if len(o)>1 and abs(o[0][0]-o[-1][0])<0.5 and abs(o[0][1]-o[-1][1])<0.5: o.pop()
    return o
def edges_ang(p):
    es=[];ang=0.0
    for i in range(len(p)):
        x0,y0=p[i];x1,y1=p[(i+1)%len(p)];dx=x1-x0;dy=y1-y0;L=math.hypot(dx,dy)
        if L<1: continue
        es.append(round(L))
        if abs(dx)>3 and abs(dy)>3: ang=max(ang,round(math.degrees(math.atan2(abs(dy),abs(dx)))))
    return es,ang
def shape_family(p):
    n=len(p)
    if n==3: return "triangle"
    if n!=4: return "polygon"
    xs=[q[0] for q in p];ys=[q[1] for q in p];bb=(max(xs)-min(xs))*(max(ys)-min(ys));ar=parea(p)
    if bb<1: return "degenerate"
    if abs(ar-bb)<0.04*bb: return "rectangle"
    vmn=min(ys);vmx=max(ys);bot=[q for q in p if abs(q[1]-vmn)<2];top=[q for q in p if abs(q[1]-vmx)<2]
    if len(bot)<2 or len(top)<2: return "angled"
    b0=min(q[0] for q in bot);b1=max(q[0] for q in bot);t0=min(q[0] for q in top);t1=max(q[0] for q in top)
    Ls=abs(t0-b0)>4;Rs=abs(t1-b1)>4
    if Ls and Rs: return "parallelogram" if (t0-b0)*(t1-b1)>0 and abs((t0-b0)-(t1-b1))<8 else "trapezoid"
    return "right-trapezoid"
def inplane(x):
    n=x["normal"]
    def crs(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    def dot(a,b):return sum(a[i]*b[i] for i in range(3))
    def unit(a):
        L=math.sqrt(dot(a,a));return (a[0]/L,a[1]/L,a[2]/L) if L>1e-9 else a
    if abs(n[1])>0.9: U,V=(1,0,0),(0,0,1)
    elif abs(n[0])>0.9: U,V=(0,1,0),(0,0,1)
    else:
        U=unit(crs(n,(0,0,1)));V=unit(crs(U,n))
        if V[2]<0: V=(-V[0],-V[1],-V[2])
    return [(dot(v,U),dot(v,V)) for v in x["verts"]]
bricks=[]
# RED field
for wall,v in RED.items():
    if not isinstance(v,dict) or "bricks" not in v: continue
    for br in v["bricks"]:
        pts=dedup([(p[0],p[1]) for p in br["verts"]]);xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        bricks.append(dict(colour="Red",region=wall,fam=shape_family(pts),w=round(max(xs)-min(xs)),h=round(max(ys)-min(ys)),
                           area=round(parea(pts)),edges=[],angle=edges_ang(pts)[1],pts=pts,draw="field",dwall=wall,
                           cp=br.get("cp"),cnr=br.get("corner")))
# (red corner L generation + per-wall L-leg drawing REMOVED - flat corner pairs are in the placement)
# BLACK
def xmid(x): return sum(v[0] for v in x["verts"])/len(x["verts"])
for x in BLK:
    if x["cat"].startswith("L_corner"):
        pts=dedup([(p[0],p[1]) for p in x["verts"]]);xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        stretcher=round(max(max(xs)-min(xs),max(ys)-min(ys))-20);header=round(min(max(xs)-min(xs),max(ys)-min(ys))-20)
        comp="canopy front-left corner" if min(xs)<0 else "canopy front-right corner"
        z0=x["verts"][0][2]
        bricks.append(dict(colour="Black",region=comp,fam="L",w=stretcher,h=65,area=round((stretcher+header)*65),
                           edges=[stretcher,header,65],angle=0.0,Lreturn=header,draw="blackL",
                           bface=("L return LEFT" if xmid(x)<0 else "L return RIGHT"),
                           ymin=min(v[1] for v in x["verts"]),ymax=max(v[1] for v in x["verts"]),z0=z0));continue
    uv=dedup(inplane(x));xs=[p[0] for p in uv];ys=[p[1] for p in uv];n=x["normal"]
    role=("canopy side wall" if abs(n[0])>0.9 else "canopy gable front" if abs(n[1])>0.9 else "canopy pitched slope")
    if abs(n[1])>0.9: bf="Gable FRONT (chevron)"
    elif abs(n[0])>0.3 and abs(n[2])>0.3: bf="Soffit slope LEFT" if xmid(x)<0 else "Soffit slope RIGHT"
    elif n[0]>0.9: bf="RIGHT wall OUTER (+x)" if xmid(x)>0 else "LEFT wall INNER (+x)"
    else: bf="LEFT wall OUTER (-x)" if xmid(x)<0 else "RIGHT wall INNER (-x)"
    bricks.append(dict(colour="Black",region="canopy: "+role,fam=shape_family(uv),w=round(max(xs)-min(xs)),h=round(max(ys)-min(ys)),
                       area=round(parea(uv)),edges=[],angle=edges_ang(uv)[1],pts=uv,draw="flat",bface=bf))
# ---- cluster + tag (same as summary) ----
def abk(a): return 0 if a<5 else int(round(a))
groups=collections.defaultdict(list)
for b in bricks: groups[(b["colour"],b["fam"],abk(b["angle"]),(b.get("Lreturn") if b["fam"]=="L" else None),
        (b["fam"]=="rectangle" and abs(b["w"]-FULL_W)<=3 and abs(b["h"]-FULL_H)<=3))].append(b)
clusters=[]
for key,gb in groups.items():
    gb.sort(key=lambda b:-b["area"]);cl=[]
    for b in gb:
        pl=False
        for c in cl:
            if abs(b["w"]-c["cw"])<=TOL and abs(b["h"]-c["ch"])<=TOL:
                c["items"].append(b);n=len(c["items"]);c["cw"]=(c["cw"]*(n-1)+b["w"])/n;c["ch"]=(c["ch"]*(n-1)+b["h"])/n;pl=True;break
        if not pl: cl.append(dict(cw=b["w"],ch=b["h"],items=[b],key=key))
    clusters+=cl
def kindof(c):
    fam=c["key"][1]
    if fam=="L": return "L-corner"
    if fam=="rectangle": return "standard" if abs(c["cw"]-FULL_W)<=3 and abs(c["ch"]-FULL_H)<=3 else "cut"
    return "angled"
ordk={"standard":0,"cut":1,"angled":2,"L-corner":3}
clusters.sort(key=lambda c:(0 if c["key"][0]=="Red" else 1,ordk[kindof(c)],-max(b["area"] for b in c["items"])))
TYPE={}
for i,c in enumerate(clusters,1):
    tid="B%02d"%i
    TYPE[tid]=dict(colour=c["key"][0],kind=kindof(c),w=round(c["cw"]),h=round(c["ch"]))
    for b in c["items"]: b["type_id"]=tid
assert len(TYPE)==len(BT), (len(TYPE),len(BT))
for tid in TYPE: assert BT[tid]["qty"]==sum(1 for b in bricks if b.get("type_id")==tid), tid
print("reconciles with summary brick_types.json:",len(TYPE),"types,",sum(m["qty"] for m in BT.values()),"bricks")
# colours
PAL=[3,4,2,40,8,140,190,210,90,110,170,230,250,20,50,70,150,160,180,200,220,240,12,22,42,62,82,102,122,132,152,172,182,202,52,72,92,112]
col={};pi=0
for tid,m in TYPE.items():
    if m["kind"]=="standard" and m["colour"]=="Red": col[tid]=1
    elif m["kind"]=="standard" and m["colour"]=="Black": col[tid]=5
    elif m["kind"]=="L-corner": col[tid]=6 if m["colour"]=="Red" else 30
    else: col[tid]=PAL[pi%len(PAL)];pi+=1
def newdoc():
    d=ezdxf.new("R2010",setup=False);d.header["$INSUNITS"]=4
    for n,c in (("BRICK",7),("WIN",7),("TXT",7),("TITLE",7),("LEG",7),("GROUND",3),("LSLIP",6),("CORNERFLAT",6)): 
        if n not in d.layers: d.layers.add(n,color=c)
    return d,d.modelspace()
def poly(msp,pts,c,lay="BRICK",fill=False):
    msp.add_lwpolyline(list(pts)+[pts[0]],dxfattribs={"color":c,"layer":lay})
def txt(msp,x,y,s,h=150,c=7,lay="TXT"):
    t=msp.add_text(s,height=h,dxfattribs={"color":c,"layer":lay});t.set_placement((x,y));return t
def swatch(msp,x,y,c,w=360,h=230):
    poly(msp,[(x,y),(x+w,y),(x+w,y+h),(x,y+h)],7,"LEG");hh=msp.add_hatch(color=c);hh.paths.add_polyline_path([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],is_closed=True);hh.dxf.layer="LEG"
def legend(msp,x,y,title,counts,total):
    txt(msp,x,y,title,240,7,"TITLE");yy=y-470
    txt(msp,x,yy,"swatch Type  size      kind        qty",140,8);yy-=330
    for tid,q in sorted(counts.items()):
        m=TYPE[tid];swatch(msp,x,yy-25,col[tid]);txt(msp,x+430,yy,"%s %dx%-3d %-9s x%d"%(tid,m["w"],m["h"],m["kind"],q),140,7);yy-=330
    yy-=110;txt(msp,x,yy,total,180,1,"TITLE")
# ================= RED 4 per-wall =================
WT={"A_NE_side":"WALL A_NE (NE side, has stair)","B_SW_side":"WALL B_SW (SW side)","C_NW_front":"WALL C_NW (NW front)","D_SE_garden":"WALL D_SE (SE garden)"}
for wall in ["A_NE_side","B_SW_side","C_NW_front","D_SE_garden"]:
    fb=[b for b in bricks if b.get("dwall")==wall and b["draw"]=="field"]
    cflat=[b for b in fb if b.get("cp") in ("lap","half")]
    xs=[p[0] for b in fb for p in b["pts"]]
    ys=[p[1] for b in fb for p in b["pts"]]
    minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys)
    d,msp=newdoc()
    for b in fb: poly(msp,b["pts"],col[b["type_id"]],"BRICK",TYPE[b["type_id"]]["kind"]!="standard")
    for b in cflat:   # highlight the flat corner slips (lap + half) in magenta on their own layer
        poly(msp,b["pts"],6,"CORNERFLAT",True)
    if miny<-1: msp.add_line((minx,0),(maxx,0),dxfattribs={"color":3,"layer":"GROUND"});txt(msp,minx,40,"GROUND z=0",120,3,"GROUND")
    for w in RED[wall].get("windows",[]):
        lbl,x0,z0,x1,z1=w;poly(msp,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],7,"WIN")
        msp.add_line((x0,z0),(x1,z1),dxfattribs={"color":7,"layer":"WIN"});msp.add_line((x0,z1),(x1,z0),dxfattribs={"color":7,"layer":"WIN"})
        txt(msp,(x0+x1)/2-200,(z0+z1)/2,str(lbl),140,7,"WIN")
    nlap=sum(1 for b in cflat if b["cp"]=="lap"); nhalf=sum(1 for b in cflat if b["cp"]=="half")
    txt(msp,minx,maxy+780,"3 MONAHAN AVE (HA23007) - %s  | %d bricks on this wall (incl. %d corner FULL-lap + %d corner HALF flat slips, magenta outline; lap extends 20mm past the arris)"%(WT[wall],len(fb),nlap,nhalf),300,7,"TITLE")
    txt(msp,minx,maxy+420,"FLAT CORNERS: no one-piece L-slips. Per course: FULL 215 laps the arris on one wall + HALF 107.5 butts it (set back 20) on the other; faces swap every course. Bricks coloured by Brick Type ID (= summary schedule).",150,8)
    cnt=collections.Counter(b["type_id"] for b in fb)
    legend(msp,maxx+1300,maxy,"BRICK TYPES ON %s"%wall,cnt,"%d bricks total on this wall (field %d + corner flats %d; = summary)"%(len(fb),len(fb)-len(cflat),len(cflat)))
    p=os.path.join(OUT,"brick_layout_wall_%s.dxf"%wall);d.saveas(p);print("Saved",os.path.basename(p),"| bricks",len(fb),"cornerflats",len(cflat),"types",len(cnt))
# ================= BLACK 9 faces (clean spaced layout, no overlap) =================
FORDER=["Gable FRONT (chevron)","Soffit slope LEFT","Soffit slope RIGHT",
        "LEFT wall OUTER (-x)","LEFT wall INNER (+x)","L return LEFT",
        "RIGHT wall OUTER (+x)","RIGHT wall INNER (-x)","L return RIGHT"]
ROWS=[["Gable FRONT (chevron)","Soffit slope LEFT","Soffit slope RIGHT"],
      ["LEFT wall OUTER (-x)","LEFT wall INNER (+x)","L return LEFT"],
      ["RIGHT wall OUTER (+x)","RIGHT wall INNER (-x)","L return RIGHT"]]
SHORT={"Gable FRONT (chevron)":"Gable FRONT","Soffit slope LEFT":"Soffit slope LEFT","Soffit slope RIGHT":"Soffit slope RIGHT",
       "LEFT wall OUTER (-x)":"LEFT wall OUTER","LEFT wall INNER (+x)":"LEFT wall INNER","L return LEFT":"L-return LEFT",
       "RIGHT wall OUTER (+x)":"RIGHT wall OUTER","RIGHT wall INNER (-x)":"RIGHT wall INNER","L return RIGHT":"L-return RIGHT"}
faces=collections.defaultdict(list)
for b in bricks:
    if b["colour"]=="Black": faces[b["bface"]].append(b)
def face_cells(f):
    fb=faces.get(f,[]); cells=[]
    if f.startswith("L return"):
        for b in fb: cells.append(([(b["ymin"],b["z0"]),(b["ymax"],b["z0"]),(b["ymax"],b["z0"]+65),(b["ymin"],b["z0"]+65)],col[b["type_id"]]))
    else:
        for b in fb: cells.append(([(p[0],p[1]) for p in b["pts"]],col[b["type_id"]]))
    allp=[p for c,_ in cells for p in c]
    if not allp: return cells,0.0,0.0,0.0,0.0  # face now empty (e.g. former L-return faces: corners are flat pairs, folded into the OUTER/INNER wall faces instead)
    mnx=min(p[0] for p in allp); mnz=min(p[1] for p in allp)
    return cells,mnx,mnz,max(p[0] for p in allp)-mnx,max(p[1] for p in allp)-mnz
fdata={f:face_cells(f) for f in FORDER}
d,msp=newdoc()
TH=200.0; GAPX=1100.0; GAPY=2600.0; TITLEZONE=900.0
txt(msp,0,1500,"3 MONAHAN AVE (HA23007) - BLACK CANOPY by FACE (9 faces) - 1:1 mm",320,7,"TITLE")
txt(msp,0,1050,"Gable front + 2 soffit slopes (40 deg) + each side wall = OUTER + INNER + front L-return. Bricks coloured by Brick Type ID; counts reconcile with the schedule.",150,8)
cursor=0.0
for row in ROWS:
    maxh=max(fdata[f][4] for f in row); baseline=cursor-TITLEZONE-maxh; ox=0.0
    for f in row:
        cells,mnx,mnz,w,h=fdata[f]
        for pts,c in cells:
            poly(msp,[(ox+px-mnx,baseline+pz-mnz) for px,pz in pts],c,"BRICK",True)
        txt(msp,ox,baseline+maxh+340,SHORT[f],TH,7,"TITLE")
        txt(msp,ox,baseline+maxh+90,"%d bricks (%.0fx%.0f mm)"%(len(faces.get(f,[])),w,h),140,8)
        colpitch=max(w, len(SHORT[f])*TH*0.62)+GAPX
        ox+=colpitch
    cursor=baseline-GAPY
cnt=collections.Counter(b["type_id"] for b in bricks if b["colour"]=="Black")
legend(msp,0,cursor-200,"BLACK BRICK TYPES (all 9 faces)",cnt,"%d black bricks total (= schedule)"%sum(cnt.values()))

p=os.path.join(OUT,"brick_layout_black_canopy_faces.dxf");d.saveas(p)
print("Saved",os.path.basename(p),"| 9 faces |",sum(len(faces[fc]) for fc in FORDER),"black bricks")
