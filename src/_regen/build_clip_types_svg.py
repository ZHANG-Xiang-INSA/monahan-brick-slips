# -*- coding: utf-8 -*-
"""
Regenerate website svg/cut_clip_types.svg to match the AUTHORITATIVE guiding-rail
reference (New requirement/guiding rail designs/_gen_guiding_rail.py):

 * The clip is a FORMED sheet-metal M-section guiding rail, NOT a flat strip:
     central flat 68 + vertical leg 15 each side + inward return lip 10 each side
     (lips hook INWARD ~16 deg), channel OPENS UPWARD, clear opening 62.5 between
     hook tips, developed / flat blank = 10+15+68+15+10 = 118, thickness t=0.25.
 * Hole positions taken from the reference (authoritative). Ø3.5.
 * Quantities + per-type hole COUNTS = current (black-corners-flat revision), so the
   screw total stays 11,782.

Each type card shows: FRONT view (holes dimensioned) + SECTION (M profile) mini.
A banner at top shows the enlarged typical cross-section + developed blank 118.
"""
import math, os

# ---- profile geometry (from reference) ----
W=68.0; LEG=15.0; RET=10.0; THK=0.25
OPEN=62.5; RIN=(W-OPEN)/2.0                      # 2.75 inward per side
ANGV=math.degrees(math.asin(RIN/RET))            # 15.96 deg
RUP=RET*math.cos(math.radians(ANGV))             # 9.614 lip vertical rise
DEVEL=RET+LEG+W+LEG+RET                           # 118
HD=3.5; TIPH=W/2-RIN                              # 31.25 (opening/2)

COL={"R1000":"#2C5FAE","R700":"#E08A2B","R500":"#3E8E41","R300":"#B8901F",
     "R250":"#2AA6B8","R100":"#6FA8DC","R50":"#8E44AD","R20":"#6E7378",
     "T_LEFT_40":"#B23B2E","T_RIGHT_40":"#B0389E"}
CNAME={"R1000":"blue","R700":"orange","R500":"green","R300":"gold","R250":"cyan",
       "R100":"lt-blue","R50":"violet","R20":"grey","T_LEFT_40":"red","T_RIGHT_40":"magenta"}
QTY={"R1000":1157,"R700":413,"R500":44,"R300":216,"R250":23,"R100":155,
     "R50":132,"R20":7,"T_LEFT_40":34,"T_RIGHT_40":34}

# rectangular types: (name, length, [hole x positions on centre-line], pitch-note)
RECT=[("R1000",1000,[125,250,375,500,625,750,875],"7×Ø3.5 · 间距125 · 端距125"),
      ("R700",700,[100,225,350,475,600],"5×Ø3.5 · 间距125 · 端距100"),
      ("R500",500,[125,250,375],"3×Ø3.5 · 间距125 · 端距125"),
      ("R300",300,[75,150,225],"3×Ø3.5 · 间距75 · 端距75"),
      ("R250",250,[62.5,187.5],"2×Ø3.5 · 间距125 · 端距62.5"),
      ("R100",100,[25,75],"2×Ø3.5 · 间距50 · 端距25"),
      ("R50",50,[12.5,37.5],"2×Ø3.5 · 间距25 · 端距12.5")]
# R20 special: 2 holes ACROSS the 68 width at x=10 (mid length)
R20=("R20",20,[(10,17),(10,51)],"2×Ø3.5 · 跨68布置 · x=10")
# trapezoids
def trap_pts(side):
    BOT,TOP,H=111.0,30.0,68.0; RUN=BOT-TOP
    if side=="LEFT":
        pts=[(0,0),(BOT,0),(BOT,H),(RUN,H)]; holes=[(BOT-18,17),(BOT-18,51),(RUN*(15.0/H)+26,15)]
    else:
        pts=[(0,0),(BOT,0),(TOP,H),(0,H)]; holes=[(18,17),(18,51),(BOT-RUN*(15.0/H)-26,15)]
    return pts,holes

S=[]  # svg fragments
def esc(t): return (t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
def line(x1,y1,x2,y2,stroke="#111",w=1.0,dash=None):
    d=' stroke-dasharray="%s"'%dash if dash else ''
    S.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>'%(x1,y1,x2,y2,stroke,w,d))
def rect(x,y,w,h,fill="none",stroke="#111",sw=1.0,rx=0):
    S.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.1f" fill="%s" stroke="%s" stroke-width="%.2f"/>'%(x,y,w,h,rx,fill,stroke,sw))
def poly(pts,fill="none",stroke="#111",sw=1.0,close=True):
    d="".join(("%.2f,%.2f "%(px,py)) for px,py in pts)
    tag="polygon" if close else "polyline"
    S.append('<%s points="%s" fill="%s" stroke="%s" stroke-width="%.2f" stroke-linejoin="round"/>'%(tag,d.strip(),fill,stroke,sw))
def circle(cx,cy,r,fill="#fff",stroke="#111",sw=1.0):
    S.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"/>'%(cx,cy,r,fill,stroke,sw))
def txt(x,y,s,size=13,fill="#111",anchor="start",weight="normal",style="normal",mono=False):
    fam=' font-family="ui-monospace,Menlo,Consolas,monospace"' if mono else ''
    S.append('<text x="%.2f" y="%.2f" font-size="%d" fill="%s" text-anchor="%s" font-weight="%s" font-style="%s"%s>%s</text>'%(x,y,size,fill,anchor,weight,style,fam,esc(s)))
def swatch(x,y,sz,col):
    rect(x,y,sz,sz,fill=col,stroke="#0000",sw=0)

def hole(cx,cy,rpx):
    circle(cx,cy,rpx,fill="#ffffff",stroke="#111",sw=1.0)
    m=rpx+3
    line(cx-m,cy,cx+m,cy,stroke="#c23b2e",w=0.7)
    line(cx,cy-m,cx,cy+m,stroke="#c23b2e",w=0.7)

# dimension: horizontal
def dimh(x0,x1,y,label,tick_up_to=None,size=11):
    line(x0,y,x1,y,stroke="#6a6a6a",w=0.7)
    for xx in (x0,x1):
        line(xx,y-3,xx,y+3,stroke="#6a6a6a",w=0.7)
        if tick_up_to is not None: line(xx,y,xx,tick_up_to,stroke="#c9c9c9",w=0.5)
    txt((x0+x1)/2,y-4,label,size,"#555","middle")
def dimv(x,y0,y1,label,tick_to=None,size=11,left=True):
    line(x,y0,x,y1,stroke="#6a6a6a",w=0.7)
    for yy in (y0,y1):
        line(x-3,yy,x+3,yy,stroke="#6a6a6a",w=0.7)
        if tick_to is not None: line(x,yy,tick_to,yy,stroke="#c9c9c9",w=0.5)
    tx=x-6 if left else x+6
    S.append('<text x="%.2f" y="%.2f" font-size="%d" fill="#555" text-anchor="middle" transform="rotate(-90 %.2f %.2f)">%s</text>'%(tx,(y0+y1)/2,size,tx,(y0+y1)/2,esc(label)))

# ---- M cross-section (opens up). base_y = SVG y of the flat base; y-up in mm ----
def section(cx, base_y, s, full=False, col="#111"):
    def P(xmm,ymm): return (cx+xmm*s, base_y-ymm*s)
    pts=[P(-W/2+RIN,LEG-RUP),P(-W/2,LEG),P(-W/2,0),P(W/2,0),P(W/2,LEG),P(W/2-RIN,LEG-RUP)]
    poly(pts,fill="none",stroke=col,sw=2.0 if full else 1.6,close=False)
    if full:
        b=W/2*s
        dimh(cx-b,cx+b,base_y+34,"68 底面",tick_up_to=base_y,size=13)
        dimv(cx+b+30,base_y-LEG*s,base_y,"腿 15",tick_to=cx+b,size=12,left=False)
        dimv(cx-b-30,base_y-LEG*s,base_y,"腿 15",tick_to=cx-b,size=12,left=True)
        # lip 10 aligned
        (lx0,ly0)=P(W/2,LEG); (lx1,ly1)=P(W/2-RIN,LEG-RUP)
        txt(lx0+14,ly0-4,"唇 10 @16°",12,"#555","start")
        # opening 62.5 between tips
        t0=P(-TIPH,LEG-RUP); t1=P(TIPH,LEG-RUP)
        line(t0[0],t0[1]-16,t1[0],t1[1]-16,stroke="#6a6a6a",w=0.7)
        for tp in (t0,t1): line(tp[0],tp[1],tp[0],tp[1]-16,stroke="#c9c9c9",w=0.5)
        txt(cx,t0[1]-20,"开口 62.5 (钩尖净距)",13,"#555","middle")
        txt(cx-b-8,base_y+2,"t=0.25",12,"#555","end")
        txt(cx,base_y+52,"成型断面 · 向上开口 (M形)",12,"#888","middle")
    else:
        txt(cx,base_y+20,"断面 68·开口62.5·t0.25",10.5,"#888","middle")

# ================= build =================
CW=2000
x=60
S.append('')  # placeholder for <svg> after we know height

# header
def header():
    txt(x,52,"钢卡扣 成型与切割图  Guiding-Rail Clip — Forming & Cutting",26,"#111",weight="bold")
    txt(x,82,"10 型 · 成型钢片 t=0.25 · 断面：底面 68 + 腿 15×2 + 内钩唇 10×2（内倾 16°）· 向上开口 62.5 · 展开料 118 · 孔 Ø3.5 · 尺寸 mm",13,"#666")

# banner: enlarged typical section + developed blank
def banner(y):
    rect(x,y,CW-2*x,300,fill="#ffffff",stroke="#e6e4df",sw=1,rx=8)
    txt(x+26,y+34,"典型断面 TYPICAL CROSS-SECTION",14,"#111",weight="bold")
    section(x+300, y+210, 5.2, full=True, col="#333")
    # developed blank
    bx=x+1050; by=y+150; bh=52; s=5.2
    txt(bx,y+34,"展开 / 下料 DEVELOPED BLANK  118 = 10+15+68+15+10",14,"#111",weight="bold")
    seg=[(RET,"10"),(LEG,"15"),(W,"68"),(LEG,"15"),(RET,"10")]
    xx=bx
    rect(bx,by,DEVEL*s,bh,fill="#eef1f4",stroke="#5a5a5a",sw=1.2)
    for seglen,lab in seg:
        if xx>bx+0.1: line(xx,by,xx,by+bh,stroke="#9aa0a6",w=0.8)
        dimh(xx,xx+seglen*s,by+bh+22,lab,tick_up_to=by+bh,size=12)
        xx+=seglen*s
    dimh(bx,bx+DEVEL*s,by+bh+50,"展开宽 118",tick_up_to=by+bh+22,size=13)
    txt(bx,by-14,"平钢片折弯成 M 形导轨；折弯线如上",12,"#888")

header()
BANNER_Y=104
banner(BANNER_Y)

# ---- type cards ----
CARD_W=(CW-2*x-30)/2      # two columns, 30 gap
CARD_H=326
GAP_Y=26
col_x=[x, x+CARD_W+30]
row_y0=BANNER_Y+300+34

order=RECT+[R20,("T_LEFT_40",),("T_RIGHT_40",)]

def front_scale(length):
    return min(470.0/length, 1.7)

def draw_card(cx0, cy0, item):
    name=item[0]; col=COL[name]
    rect(cx0,cy0,CARD_W,CARD_H,fill="#ffffff",stroke="#e6e4df",sw=1,rx=8)
    ix=cx0+28; iy=cy0+34
    swatch(ix,iy-16,18,col)
    txt(ix+28,iy,name,23,"#111",weight="bold")
    txt(cx0+CARD_W-26,iy-2,"QTY %d · 螺钉 %d/件"%(QTY[name], 2 if name=="R20" else (3 if name.startswith("T_") else len(item[2]))),13,"#555","end",mono=True)
    # note line
    note = item[3] if len(item)>3 else "3×Ø3.5 · 2孔竖排 + 1孔斜边区"
    txt(ix+28,iy+20,"%s · 颜色 %s"%(note,CNAME[name]),12,"#7a7a7a")

    fx=cx0+40; ftop=cy0+92    # front-view area top
    if name.startswith("T_"):
        side="LEFT" if "LEFT" in name else "RIGHT"
        pts,holes=trap_pts(side); s=front_scale(111)
        H=68.0
        P=lambda xm,ym:(fx+xm*s, ftop+ (H-ym)*s)
        poly([P(a,b) for a,b in pts],fill="#f7f8fa",stroke=col,sw=1.6)
        for hx,hy in holes: hole(*P(hx,hy),rpx=max(HD/2*s,2.2))
        dimh(fx,fx+111*s,ftop+H*s+26,"底 111",tick_up_to=ftop+H*s,size=12)
        dimv(fx-14,ftop,ftop+H*s,"H 68",tick_to=fx,size=12,left=True)
        txt(fx,ftop+H*s+52,"顶 30 · 斜切 40° · 斜边 %.1f"%math.hypot(81,68),12,"#7a7a7a")
        section(cx0+CARD_W-150, cy0+150, 2.5, col=col)
        txt(cx0+CARD_W-150, cy0+190, "3 孔：2 竖排 + 1 斜边区", 11, "#888","middle")
        return
    length=item[1]; s=front_scale(length); H=68.0
    fw=length*s; fh=H*s
    rect(fx,ftop,fw,fh,fill="#f7f8fa",stroke=col,sw=1.6)
    if name=="R20":
        for hx,hy in item[2]:
            hole(fx+hx*s, ftop+(H-hy)*s, max(HD/2*s,2.2))
        dimv(fx-14,ftop,ftop+fh,"68",tick_to=fx,size=12,left=True)
        dimh(fx,fx+fw,ftop+fh+26,"20",tick_up_to=ftop+fh,size=12)
        dimh(fx,fx+10*s,ftop+fh+50,"x=10",tick_up_to=ftop+fh+26,size=11)
        txt(fx,ftop-12,"2×Ø3.5 跨 68 竖排 @ x=10",12,"#7a7a7a")
    else:
        holes=item[2]
        for hx in holes:
            hole(fx+hx*s, ftop+fh/2, max(HD/2*s,2.2))
        dimv(fx-14,ftop,ftop+fh,"68",tick_to=fx,size=12,left=True)
        dimh(fx,fx+fw,ftop+fh+26,"%g"%length,tick_up_to=ftop+fh,size=12)
        # hole chain
        xs=[0]+list(holes)+[length]
        yy=ftop+fh+50
        for i in range(len(xs)-1):
            dimh(fx+xs[i]*s,fx+xs[i+1]*s,yy,"%g"%(xs[i+1]-xs[i]),tick_up_to=(ftop+fh+26) if i==0 else None,size=10)
        txt(fx,ftop-12,"Ø3.5 · 中心线布孔",12,"#7a7a7a")
    # section mini at right
    section(cx0+CARD_W-150, cy0+150, 2.5, col=col)
    txt(cx0+CARD_W-150, cy0+190, "向上开口 · 净距 62.5", 11, "#888","middle")

yy=row_y0
rows=[order[i:i+2] for i in range(0,len(order),2)]
for r in rows:
    for j,item in enumerate(r):
        draw_card(col_x[j], yy, item)
    yy+=CARD_H+GAP_Y

total_h=yy+20
svg=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="Inter,\'Noto Sans SC\',system-ui,Arial,sans-serif">'%(CW,int(total_h))
     +'<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>'%(CW,int(total_h))
     +"".join(S)+'</svg>')
out=os.path.join(os.path.dirname(__file__),"..","website","svg","cut_clip_types.svg")
out=os.path.abspath(out)
open(out,"w",encoding="utf-8").write(svg)
print("wrote",out,"bytes",len(svg),"height",int(total_h))
# screw reconciliation
sc=sum(QTY[n]*(2 if n=="R20" else (3 if n.startswith("T_") else c)) for n,c in
       {"R1000":7,"R700":5,"R500":3,"R300":3,"R250":2,"R100":2,"R50":2,"R20":2,"T_LEFT_40":3,"T_RIGHT_40":3}.items())
print("clip total",sum(QTY.values()),"| screw total",sc)
