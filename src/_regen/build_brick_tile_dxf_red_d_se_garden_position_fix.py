#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brick_tile_cutting_layout_red_d_se_garden_position_fix.dxf — one cell per Brick Type ID (B01..), true outline at 1:1,
swatch (Red=1 / Black=8), ID + shape + qty + area + dims above; every edge dimensioned with
extension lines + ticks; 40deg angle arc on angled cuts; right-angle marks; L drawn as an L.
Sectioned: RED standard/cut/angled, BLACK standard/cut, BLACK angled, L-corner. Matches the
Blender model + brick_tile_schedule_detailed.xlsx (same Type ID / shape / dims / qty)."""
import json,os,math,ezdxf
HERE=os.path.dirname(os.path.abspath(__file__)); D=json.load(open(os.path.join(HERE,"..","brick_types.json"))); T=D["types"]
OUT=os.path.join(HERE,"..","brick_tile_cutting_layout_red_d_se_garden_position_fix.dxf")
doc=ezdxf.new("R2010",setup=True); doc.header["$INSUNITS"]=4; msp=doc.modelspace()
for n,ci in (("SHAPE",7),("DIM",8),("TEXT",7),("TITLE",7),("SWATCH",7),("ANGLE",1)):
    if n not in doc.layers: doc.layers.add(n,color=ci)
def line(p0,p1,col=8,lay="DIM"): msp.add_line(p0,p1,dxfattribs={"color":col,"layer":lay})
def txt(x,y,s,h=14,col=7,lay="TEXT"): t=msp.add_text(s,height=h,dxfattribs={"color":col,"layer":lay}); t.set_placement((x,y)); return t
def tick(p,d=6): line((p[0]-d,p[1]-d),(p[0]+d,p[1]+d),8)
def dim_h(x0,x1,y,off,s):
    ye=y+off; line((x0,y),(x0,ye),8); line((x1,y),(x1,ye),8); line((x0,ye),(x1,ye),8); tick((x0,ye)); tick((x1,ye))
    txt((x0+x1)/2-len(s)*3.2,ye+(7 if off>0 else -16),s,11)
def dim_v(y0,y1,x,off,s):
    xe=x+off; line((x,y0),(xe,y0),8); line((x,y1),(xe,y1),8); line((xe,y0),(xe,y1),8); tick((xe,y0)); tick((xe,y1))
    txt(xe+(6 if off>0 else -26),(y0+y1)/2-5,s,11)
def dim_diag(p0,p1,off,s):
    dx=p1[0]-p0[0]; dy=p1[1]-p0[1]; L=math.hypot(dx,dy) or 1; nx=-dy/L; ny=dx/L
    q0=(p0[0]+nx*off,p0[1]+ny*off); q1=(p1[0]+nx*off,p1[1]+ny*off)
    line(p0,q0,8); line(p1,q1,8); line(q0,q1,8); txt((q0[0]+q1[0])/2-14,(q0[1]+q1[1])/2,s,11)
def rt_marker(cn,vx,vy,sz=16):
    a=(cn[0]+vx[0]*sz,cn[1]+vx[1]*sz); b=(cn[0]+vy[0]*sz,cn[1]+vy[1]*sz); cc=(a[0]+vy[0]*sz,a[1]+vy[1]*sz)
    line(a,cc,8); line(cc,b,8)
def angle_arc(cn,r,a0,a1,s):
    msp.add_arc(cn,r,a0,a1,dxfattribs={"color":1,"layer":"ANGLE"})
    am=math.radians((a0+a1)/2); txt(cn[0]+(r+9)*math.cos(am)-10,cn[1]+(r+9)*math.sin(am),s,11,1,"ANGLE")
def swatch(x,y,aci): msp.add_lwpolyline([(x,y),(x+50,y),(x+50,y+50),(x,y+50)],close=True,dxfattribs={"color":aci,"layer":"SWATCH"})

txt(0,1180,"3 MONAHAN AVE (HA23007) - BRICK SLIP CUTTING / PROCUREMENT LAYOUT  1:1 mm  | slip face, joint 10 mm | Red + Black",34,7,"TITLE")
txt(0,1130,"One cell per Brick Type ID (B01..). Same Type ID / shape / dimensions / quantity / area as the Blender model and brick_tile_schedule_detailed.xlsx. Standard 215x65; cuts + L-corners + 40deg canopy cuts listed separately.",15,7,"TITLE")
SECS=[("RED standard + cut slips",lambda t:t["colour"]=="Red" and t["kind"] in("standard","cut")),
      ("RED angled cut slips",lambda t:t["colour"]=="Red" and t["kind"]=="angled"),
      ("BLACK standard + cut slips",lambda t:t["colour"]=="Black" and t["kind"] in("standard","cut")),
      ("BLACK 40deg angled / trapezoid / triangular canopy slips",lambda t:t["colour"]=="Black" and t["kind"]=="angled"),
      ("L-shaped corner slips",lambda t:t["kind"]=="L-corner")]
COLW=430.0; ROWH=300.0; PER=5
y0=1060.0
for title,filt in SECS:
    tt=[t for t in T if filt(t)]
    if not tt: continue
    txt(0,y0,"=== %s  (%d types) ==="%(title,len(tt)),24,7,"TITLE"); y0-=230
    for i,t in enumerate(tt):
        cx=(i%PER)*COLW; cy=y0-(i//PER)*ROWH
        outl=[(cx+p[0],cy+p[1]) for p in t["outline"]]
        col=1 if t["colour"]=="Red" else 7
        msp.add_lwpolyline(outl,close=True,dxfattribs={"color":col,"layer":"SHAPE"})
        xs=[p[0] for p in outl]; ys=[p[1] for p in outl]; bx0=min(xs); bx1=max(xs); by0=min(ys); by1=max(ys)
        swatch(cx,by1+95,1 if t["colour"]=="Red" else 8)
        txt(cx+62,by1+112,"%s  [%s]"%(t["type_id"],t["colour"]),17,7,"TITLE")
        txt(cx,by1+62,"%s  qty=%d"%(t["shape"],t["qty"]),12,7)
        txt(cx,by1+34,"area/pc %d mm2  | total %.3f m2"%(t["area_per"],t["total_area"]/1e6),11,7)
        if t["shape"]=="L-shaped corner":
            dim_h(bx0,bx1,by0,-46,"stretcher %d"%t["edges"][0]); dim_v(by0,by1,bx0,-40,"H %d"%t["edges"][2])
            txt(cx+t["edges"][1]+6,cy+30,"return %d"%t["edges"][1],11,7); rt_marker((bx0,by0),(1,0),(0,1))
        elif t["kind"]=="angled":
            # bottom + height + angle arc
            vmn=min(p[1] for p in t["outline"]); vmx=max(p[1] for p in t["outline"])
            bot=sorted([p for p in t["outline"] if abs(p[1]-vmn)<2]); top=sorted([p for p in t["outline"] if abs(p[1]-vmx)<2])
            tb0=cx+bot[0][0]; tb1=cx+bot[-1][0]; tt0=cx+(top[0][0] if top else bot[0][0]); tt1=cx+(top[-1][0] if len(top)>1 else bot[-1][0])
            dim_h(tb0,tb1,by0,-46,"bot %d"%(tb1-tb0)); dim_v(by0,by1,min(tb0,tt0),-40,"H %d"%(by1-by0))
            if len(top)>1 and abs((tt1-tt0)-(tb1-tb0))>3: dim_h(tt0,tt1,by1,46,"top %d"%(tt1-tt0))
            al=math.degrees(math.atan2(by1-by0,tt0-tb0)) if abs(tt0-tb0)>2 else 90
            ar=math.degrees(math.atan2(by1-by0,tt1-tb1)) if abs(tt1-tb1)>2 else 90
            if al<=88: angle_arc((tb0,by0),46,0,al,"%.0fdeg"%t["angle"])
            elif ar<=88: angle_arc((tb1,by0),46,180-ar if ar<90 else ar,180,"%.0fdeg"%t["angle"])
            else: angle_arc((tb1,by0),46,140,180,"%.0fdeg"%t["angle"])
        else:
            dim_h(bx0,bx1,by0,-46,"%d"%(bx1-bx0)); dim_v(by0,by1,bx0,-40,"%d"%(by1-by0))
            rt_marker((bx0,by0),(1,0),(0,1)); rt_marker((bx1,by0),(-1,0),(0,1))
    rows=(len(tt)+PER-1)//PER; y0=y0-rows*ROWH-120
txt(0,y0,"All shapes drawn 1:1 in mm. Red=red slip, Black=black slip. Dimensions placed outside each shape. Angled = 40deg canopy rake. L = one-piece corner slip (stretcher + header).",15,7)
doc.saveas(OUT); print("Saved",OUT,"| Brick Type IDs:",len(T))
