#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clip cutting / procurement DXF - SIMPLIFIED 6 TYPES ONLY.
   R1000 R500 R250 R20 (rectangles) + T_LEFT_40 T_RIGHT_40 (right trapezoids, top30/bottom111/H68/40deg).
   Engineering dims: dim lines, extension lines, ticks, 40deg arc, right-angle markers, no text overlap."""
import json,os,math,ezdxf
HERE=os.path.dirname(os.path.abspath(__file__)); B="/sessions/tender-cool-ritchie/mnt/Brick slip PJ 001"
D=json.load(open(os.path.join(HERE,"..","clip_instances_red_d_se_garden_position_fix.json"))); types={t["type_id"]:t for t in D["types"]}
OUT=os.path.join(HERE,"..","clip_cutting_layout_red_d_se_garden_position_fix.dxf")
doc=ezdxf.new("R2010",setup=True); doc.header["$INSUNITS"]=4; msp=doc.modelspace()
for n,ci in (("SHAPE",7),("DIM",8),("TEXT",7),("TITLE",7),("SWATCH",7),("ANGLE",1)):
    if n not in doc.layers: doc.layers.add(n,color=ci)
def line(p0,p1,col=8,lay="DIM"): msp.add_line(p0,p1,dxfattribs={"color":col,"layer":lay})
def txt(x,y,s,h=16,col=7,lay="TEXT"): t=msp.add_text(s,height=h,dxfattribs={"color":col,"layer":lay}); t.set_placement((x,y)); return t
def tick(p,d=7): line((p[0]-d,p[1]-d),(p[0]+d,p[1]+d),8)
def dim_h(x0,x1,y,off,s):
    ye=y+off; line((x0,y),(x0,ye)); line((x1,y),(x1,ye)); line((x0,ye),(x1,ye)); tick((x0,ye)); tick((x1,ye))
    txt((x0+x1)/2-len(s)*4,ye+(9 if off>0 else -20),s,14)
def dim_v(y0,y1,x,off,s):
    xe=x+off; line((x,y0),(xe,y0)); line((x,y1),(xe,y1)); line((xe,y0),(xe,y1)); tick((xe,y0)); tick((xe,y1))
    txt(xe+(9 if off>0 else -40),(y0+y1)/2-7,s,14)
def dim_diag(p0,p1,off,s):
    dx=p1[0]-p0[0]; dy=p1[1]-p0[1]; L=math.hypot(dx,dy) or 1; nx=-dy/L; ny=dx/L
    q0=(p0[0]+nx*off,p0[1]+ny*off); q1=(p1[0]+nx*off,p1[1]+ny*off)
    line(p0,q0); line(p1,q1); line(q0,q1); txt((q0[0]+q1[0])/2-18,(q0[1]+q1[1])/2,s,14)
def rt(corner,vx,vy,sz=20):
    a=(corner[0]+vx[0]*sz,corner[1]+vx[1]*sz); b=(corner[0]+vy[0]*sz,corner[1]+vy[1]*sz); c=(a[0]+vy[0]*sz,a[1]+vy[1]*sz)
    line(a,c); line(c,b)
def arc(corner,r,a0,a1,s):
    msp.add_arc(corner,r,a0,a1,dxfattribs={"color":1,"layer":"ANGLE"})
    am=math.radians((a0+a1)/2); txt(corner[0]+(r+12)*math.cos(am)-14,corner[1]+(r+12)*math.sin(am),s,14,1,"ANGLE")
def swatch(x,y,aci): msp.add_lwpolyline([(x,y),(x+60,y),(x+60,y+60),(x,y+60)],close=True,dxfattribs={"color":aci,"layer":"SWATCH"})
W=68.0; TOPW=30.0; BOT=111.0; RUN=81.0
txt(0,600,"3 MONAHAN AVE (HA23007) - CLIP CUTTING / PROCUREMENT SHEET - 10 TYPES  1:1 mm | width 68 | thickness 0.25",26,7,"TITLE")
txt(0,566,"Rectangles R1000/R700/R500/R300/R250/R100/R50/R20 (added 700/300/100/50 to cut 20mm count) + T_LEFT_40/T_RIGHT_40 trapezoids (canopy rakes, mirrored).",14,7,"TITLE")
ORDER=["R1000","R700","R500","R300","R250","R100","R50","R20","T_LEFT_40","T_RIGHT_40"]
COLW=1300.0; oy=250.0
for i,tid in enumerate(ORDER):
    t=types.get(tid)
    if not t: continue
    ox=(i%2)*COLW; row=i//2; cy=oy-row*430
    swatch(ox,cy+W+95,t["aci"]); txt(ox+75,cy+W+112,"%s  [%s]"%(tid,t["colour"]),22,7,"TITLE")
    if tid.startswith("R"):
        L=int(tid[1:])
        msp.add_lwpolyline([(ox,cy),(ox+L*0.5,cy),(ox+L*0.5,cy+W),(ox,cy+W)] if L>250 else [(ox,cy),(ox+L,cy),(ox+L,cy+W),(ox,cy+W)],close=True,dxfattribs={"color":7,"layer":"SHAPE"})
        draw=L*0.5 if L>250 else L
        txt(ox,cy+W+60,"rectangle  %d x 68 x 0.25 mm   qty=%d   from %dmm stock"%(L,t["qty"],L),13,7)
        dim_h(ox,ox+draw,cy,-46,("%d (drawn 1:2)"%L if L>250 else "%d"%L)); dim_v(cy,cy+W,ox,-40,"68")
        rt((ox,cy),(1,0),(0,1)); rt((ox+draw,cy),(-1,0),(0,1))
    else:
        if tid=="T_LEFT_40":  pts=[(ox,cy),(ox+BOT,cy),(ox+BOT,cy+W),(ox+RUN,cy+W)]   # sloped LEFT
        else:                 pts=[(ox,cy),(ox+BOT,cy),(ox+BOT-RUN,cy+W),(ox,cy+W)]   # sloped RIGHT
        msp.add_lwpolyline(pts,close=True,dxfattribs={"color":7,"layer":"SHAPE"})
        txt(ox,cy+W+60,"right trapezoid  top=30  bottom=111  H=68  t=0.25  angle=40deg   qty=%d  (%s sloped)"%(t["qty"],"LEFT" if tid=="T_LEFT_40" else "RIGHT"),13,7)
        dim_h(ox,ox+BOT,cy,-46,"bottom 111"); dim_v(cy,cy+W,ox-(0 if tid=='T_LEFT_40' else 0),-40,"68")
        if tid=="T_LEFT_40":
            dim_h(ox+RUN,ox+BOT,cy+W,46,"top 30"); dim_diag((ox,cy),(ox+RUN,cy+W),-26,"slope"); arc((ox,cy),50,0,40,"40deg"); rt((ox+BOT,cy),(-1,0),(0,1))
        else:
            dim_h(ox,ox+TOPW,cy+W,46,"top 30"); dim_diag((ox+BOT,cy),(ox+BOT-RUN,cy+W),26,"slope"); arc((ox+BOT,cy),50,140,180,"40deg"); rt((ox,cy),(1,0),(0,1))
txt(0,oy-5*430-80,"All clips width 68 mm, thickness 0.25 mm. Rectangles drawn 1:2 above 250mm. Trapezoid bottom 111 = top 30 + 68/tan(40deg); T_LEFT_40/T_RIGHT_40 identical size mirrored. Matches the Blender model, wall-layout DXF and Excel.",13,7)
doc.saveas(OUT); print("Saved",OUT,"| %d types:"%len(ORDER),ORDER)
