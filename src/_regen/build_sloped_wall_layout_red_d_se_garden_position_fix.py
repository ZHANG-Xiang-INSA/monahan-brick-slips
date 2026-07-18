#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DXF 2 (FIXED5): black_sloped_canopy_clip_wall_layout_red_d_se_garden_position_fix.dxf
   Wall layout: canopy clips in real positions, filled by Type-ID colour, with the
   Type ID drawn INSIDE each clip (identification). NO angle arcs (小圆孔 removed).
   Legend placed to the RIGHT of the panels (does not overlap the wall)."""
import json, os, math, collections, ezdxf
from shapely.geometry import Polygon
from shapely.ops import unary_union
HERE=os.path.dirname(os.path.abspath(__file__)); B="/sessions/tender-cool-ritchie/mnt/Brick slip PJ 001"
D=json.load(open(os.path.join(HERE,"..","clip_instances_red_d_se_garden_position_fix.json"))); clips=D["clips"]; types=D["types"]
blk=json.load(open(os.path.join(HERE,"..","black_placement_fixed7.json")))["bricks"]
OUT=os.path.join(HERE,"..","black_sloped_canopy_clip_wall_layout_red_d_se_garden_position_fix.dxf"); os.makedirs(os.path.dirname(OUT),exist_ok=True)
def unit(a):
    L=math.sqrt(sum(x*x for x in a)); return tuple(x/L for x in a)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b): return sum(a[i]*b[i] for i in range(3))
def rn(n): return (round(n[0],2),round(n[1],2),round(n[2],2))
def inpl(n):
    n=unit(n)
    if abs(n[1])>0.9: return (1.,0.,0.),(0.,0.,1.)
    if abs(n[0])>0.9: return (0.,1.,0.),(0.,0.,1.)
    U=unit(cross(n,(0.,0.,1.))); V=unit(cross(U,n))
    if V[2]<0: V=tuple(-x for x in V)
    return U,V
doc=ezdxf.new("R2010",setup=True); doc.header["$INSUNITS"]=4; msp=doc.modelspace()
if "WALL" not in doc.layers: doc.layers.add("WALL",color=7)
if "TXT" not in doc.layers: doc.layers.add("TXT",color=7)
def poly(pts,col,lay="0"): msp.add_lwpolyline(pts,close=True,dxfattribs={"color":col,"layer":lay})
def txt(x,y,s,h=20,col=7):
    t=msp.add_text(s,height=h,dxfattribs={"color":col,"layer":"TXT"})
    t.set_placement((x,y),align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER); return t
def txtL(x,y,s,h=20,col=7):
    t=msp.add_text(s,height=h,dxfattribs={"color":col,"layer":"TXT"}); t.set_placement((x,y)); return t
cano=[c for c in clips if c["region"]=="black_sloped_canopy"]
def boundary(nrm):
    U,V=inpl(nrm); brs=[b for b in blk if rn(tuple(b["normal"]))==rn(nrm)]
    return unary_union([Polygon([(dot(v,U),dot(v,V)) for v in b["verts"]]) for b in brs]).buffer(6,2).buffer(-6,2)
panel_right=0.0
def panel(ox,oy,title,nrm,facematch):
    global panel_right
    g=boundary(nrm); minx,miny,maxx,maxy=g.bounds
    for gg in ([g] if g.geom_type=="Polygon" else list(g.geoms)):
        if gg.area < 3000: continue   # drop tiny buffer-artifact blobs (the old ~13mm "small circles")
        poly([(ox+x-minx,oy+y-miny) for x,y in gg.exterior.coords],7,"WALL")
        for r in gg.interiors:
            if Polygon(r).area < 3000: continue   # drop tiny artifact holes too
            poly([(ox+x-minx,oy+y-miny) for x,y in r.coords],7,"WALL")
    cs=[c for c in cano if facematch(c["face"])]
    for c in cs:
        uvp=[(ox+u-minx,oy+v-miny) for u,v in c["uv"]]
        poly(uvp,c["aci"])
        cu=sum(p[0] for p in uvp)/len(uvp); cv=sum(p[1] for p in uvp)/len(uvp)
        w=max(p[0] for p in uvp)-min(p[0] for p in uvp); h=max(p[1] for p in uvp)-min(p[1] for p in uvp)
        th=min(max(min(w*0.42,h*0.55),12),34)            # text height fits the clip
        txt(cu,cv,c["type_id"],th,7)                       # ID INSIDE the clip
    txtL(ox,oy+(maxy-miny)+110,title,38,7); txtL(ox,oy+(maxy-miny)+60,f"{len(cs)} clips - filled by Type-ID colour; ID shown inside each clip",20)
    panel_right=max(panel_right, ox+(maxx-minx))
    return ox+(maxx-minx)
xe=panel(0,0,"PANEL 1 - GABLE FRONT (x-z) rake 40deg",(0.0,-1.0,0.0),lambda f:"frontframe" in f)
x2=panel(xe+800,0,"PANEL 2 - SLOPE L (unfolded, 40deg)",(0.643,0.0,-0.766),lambda f:f.startswith("black_slopeL"))
panel(x2+800,0,"PANEL 3 - SLOPE R (unfolded, 40deg)",(-0.643,0.0,-0.766),lambda f:f.startswith("black_slopeR"))
# LEGEND to the RIGHT of all panels (clear of the wall)
cant=[t for t in types if t["type_id"] in set(c["type_id"] for c in cano)]
lx=panel_right+900; ly=2200
txtL(lx,ly+120,"LEGEND - black sloped canopy clip types (Type ID + colour; matches the cutting sheet)",30,7)
txtL(lx,ly+70,"All rake cuts = 40deg. swatch  ID   shape  kind   src  bottom/top  angle  qty",18,8)
for i,t in enumerate(cant):
    yy=ly-i*160; e=t["edges"]
    poly([(lx,yy),(lx+230,yy),(lx+230,yy+95),(lx,yy+95)],t["aci"])
    txt(lx+115,yy+47,t["type_id"],34,7)     # ID inside the legend swatch too
    s=f'  {t["shape"][:5]:5s} {t["kind"]:8s} {t["source"]:4d}  '+(f'{e["bottom"]:.0f}/{e["top"]:.0f}  {t["angle"]:.0f}deg' if t["kind"]=="angled" else f'{t["length"]:.0f}    -')+f'   x{t["qty"]}'
    txtL(lx+300,yy+34,s,22,7)
doc.saveas(OUT); print("Saved DXF2",OUT,"| canopy clips:",len(cano),"| legend types:",len(cant),"| small-circle artifacts removed")
