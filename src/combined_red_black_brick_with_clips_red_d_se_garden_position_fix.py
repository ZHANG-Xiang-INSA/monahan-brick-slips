#!/usr/bin/env python3
# *** NEW REQUIREMENT 2 - FLAT CORNERS: the 3 red one-piece L-corner slips are REPLACED by
#     PAIRS of FLAT slips (per course: one FULL 215 lapping the arris on the face that had
#     the 215 leg + one HALF 107.5 butting it, set back 20, on the other face; assignment
#     swaps every course). The corner flats now live IN red_brick_placement_v7_stairfix.json
#     (markers "corner"/"cp"), so NO procedural L generation remains in this model.
#     BLACK (incl. its 272 L-corners) untouched. ***
# *** FIXED: stairfix red + fixed black (no U-brick) + fixed clips 0.25mm. Clips in hideable translucent layers. ***
# -*- coding: utf-8 -*-
# ============================================================================
#  COMBINED RED+BLACK BRICK MODEL **WITH CLIPS (CORRECTED CANOPY 40deg)** - 3 Monahan Ave
#  Reads clip_instances_v3.json. Clips = course band INTERSECT brick coverage
#  (no overhang / no floating). RED + BLACK ORDINARY = standard only. BLACK
#  SLOPED CANOPY = long-stock cut/angled one-pieces, NO 20mm. 5 hideable
#  translucent clip layers by region+kind.
#  ONE model showing both colours in their correct relative positions.
#  Does NOT overwrite the red-only / black-only models, and changes NO logic:
#    - RED flats from red_brick_placement_v7_stairfix.json (4 walls, FFL-aligned),
#      incl. the FLAT corner pairs (cp=lap/half) at the 3 connected corners - NO red L.
#    - BLACK canopy from black_placement.json (extracted 1:1 from the revised
#      black model, counts 746/414/268/4) placed into the C_NW front-centre
#      GAP (the entrance slot between the two red front segments), as a porch in
#      front of the wall (back face just clear of the red skin -> no overlap).
#  Six colour categories, every slip a real solid:
#    Red full | Red cut | Red L | Black full | Black cut | Black L
#    + window/door VOIDS.
#  Run:  blender --python combined_red_black_brick_model.py
# ============================================================================
import bpy, json, os, math
from collections import defaultdict
from mathutils import Vector

MM=0.001
BRICK_T=20*MM; BRICK_H=65*MM; COURSE_P=BRICK_H+10*MM
L_LONG=215*MM; L_SHORT=102.5*MM; MIN_CUT=20*MM
FIRST_FLOOR=2891*MM
WX=11513*MM; WY=13604*MM
# black canopy placement -> front-centre gap of C_NW (local u-centre 5766 mm);
# back face set just in front of the red skin (z aligned to FFL=0).
BDX=5.766; BDY=-0.370; BDZ=0.0

def jload(*cands):
    here=os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ""
    for rel in cands:
        for base in (here, r"C:\Users\Stras\Documents\Claude\Projects\Brick slip PJ 001\New requirement 6 - website v2",
                     os.path.join(here,"..","03_regeneration_kit","inputs"),
                     os.path.join(here,"..","..")):
            p=os.path.join(base,rel)
            if os.path.isfile(p): return json.load(open(p))
    raise FileNotFoundError(cands)
RED=jload("04_red_brick_calculation/red_brick_placement_v7_stairfix.json","red_brick_placement_v7_stairfix.json")
BLACK=jload("black_placement_fixed7.json","08_clip_system/01_scripts/black_placement_fixed7.json","black_placement_fixed.json","01_scripts/black_placement_fixed.json","../01_scripts/black_placement_fixed.json")

ASSEMBLY={
 "C_NW_front":  dict(origin=Vector((0,0,0)),   u=Vector((1,0,0)),  n=Vector((0,-1,0))),
 "A_NE_side":   dict(origin=Vector((0,WY,0)),  u=Vector((0,-1,0)), n=Vector((-1,0,0))),   # FIX: left, deep/stair end at back (beside D_SE), outward West
 "D_SE_garden": dict(origin=Vector((WX+0.997,WY,0)), u=Vector((-1,0,0)), n=Vector((0,1,0))),   # FIX: slid +997mm east -> stair-end seats flush on A_NE (x=0)
 "B_SW_side":   dict(origin=Vector((WX,0,0)),  u=Vector((0,1,0)),  n=Vector((1,0,0))),   # FIX: right, outward East
}
Z=Vector((0,0,1))

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for c in (bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        for b in list(c): c.remove(b)
reset(); scene=bpy.context.scene
def col(n):
    c=bpy.data.collections.new(n); scene.collection.children.link(c); return c
C_RF=col("Red_Full"); C_RC=col("Red_Cut"); C_RL=col("Red_L_corner")
C_BF=col("Black_Full"); C_BC=col("Black_Cut"); C_BL=col("Black_L_corner")
C_OP=col("Window_Door_Voids"); C_AN=col("Annotation")
def mat(n,rgba,a=1.0):
    m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value=rgba
        if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=a
    if a<1: m.blend_method='BLEND'
    return m
M_RF=mat("Red_Full",(0.62,0.20,0.12,1));  M_RC=mat("Red_Cut",(0.88,0.55,0.28,1)); M_RL=mat("Red_L",(0.80,0.30,0.10,1))
M_RQ=mat("Red_CornerFlat",(0.95,0.15,0.55,1))   # corner flat pair (lap + half), magenta like the old L
M_BF=mat("Black_Full",(0.12,0.16,0.26,1));M_BC=mat("Black_Cut",(0.38,0.45,0.62,1));M_BL=mat("Black_L",(0.20,0.55,0.62,1))
M_OP=mat("Opening",(0.07,0.08,0.09,1))

class Mesh:
    def __init__(s,n,c,m): s.n=n;s.c=c;s.m=m;s.v=[];s.f=[]
    def add(s,base,normal,t):
        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)
        for p in base: s.v.append((p.x,p.y,p.z))
        for p in base: q=p+off; s.v.append((q.x,q.y,q.z))
        s.f.append([b0+i for i in range(k)]); s.f.append([b0+k+i for i in range(k-1,-1,-1)])
        for i in range(k): j=(i+1)%k; s.f.append([b0+i,b0+j,b0+k+j,b0+k+i])
    def build(s):
        if not s.v: return
        me=bpy.data.meshes.new(s.n); me.from_pydata(s.v,[],s.f); me.update()
        o=bpy.data.objects.new(s.n,me); o.data.materials.append(s.m); s.c.objects.link(o)
RF=Mesh("Red_Full",C_RF,M_RF); RC=Mesh("Red_Cut",C_RC,M_RC); RL=Mesh("Red_L",C_RL,M_RL)
RQ=Mesh("Red_CornerFlat",C_RL,M_RQ)   # flat corner slips (lap+half) in the old L collection
BF=Mesh("Black_Full",C_BF,M_BF); BC=Mesh("Black_Cut",C_BC,M_BC); BL=Mesh("Black_L",C_BL,M_BL)
cnt=defaultdict(int)

# ---- RED flats from placement (per wall) ----
for nm,A in ASSEMBLY.items():
    o=A["origin"]; U=A["u"]; N=A["n"]
    for br in RED[nm]["bricks"]:
        vs=br["verts"][:-1] if (len(br["verts"])>1 and br["verts"][0]==br["verts"][-1]) else br["verts"]
        base=[o+U*(x*MM)+Z*(y*MM) for (x,y) in vs]
        if len(base)<3: continue
        cp=br.get("cp")
        if cp in ("lap","half"):                      # flat corner slips (replace the old L)
            RQ.add(base,N,BRICK_T); cnt["red_corner_lap" if cp=="lap" else "red_corner_half"]+=1
        else:
            (RF if br["t"]=="full" else RC).add(base,N,BRICK_T)
            cnt["red_full" if br["t"]=="full" else "red_cut"]+=1
    for (l,x0,y0,x1,y1) in RED[nm]["windows"]:
        base=[o+U*(x0*MM)+Z*(y0*MM),o+U*(x1*MM)+Z*(y0*MM),o+U*(x1*MM)+Z*(y1*MM),o+U*(x0*MM)+Z*(y1*MM)]
        me=bpy.data.meshes.new(f"{nm}_{l}"); me.from_pydata([(p.x,p.y,p.z) for p in base],[],[[0,1,2,3]]); me.update()
        ob=bpy.data.objects.new(f"{nm}_OPEN_{l}",me); ob.location+=N*(BRICK_T*0.5); ob.data.materials.append(M_OP); C_OP.objects.link(ob)

# ---- RED corners: FLAT-PAIR method (NEW REQUIREMENT 2) ----
# The one-piece wrapped L-slips are GONE. Each of the 3 red corners is covered per course by
# a FULL 215 flat slip lapping the arris + a HALF 107.5 flat slip butting it (set back 20),
# swapping faces every course. These pieces are IN the placement JSON ("cp":"lap"/"half")
# and are built by the placement loop above into the Red_CornerFlat mesh. No corner() calls.

# ---- BLACK canopy from placement, translated into the front-centre gap ----
OFF=Vector((BDX,BDY,BDZ))
for br in BLACK["bricks"]:
    base=[Vector((v[0]*MM,v[1]*MM,v[2]*MM))+OFF for v in br["verts"]]
    if len(base)<3: continue
    nrm=Vector(br["normal"]); th=br["th_mm"]*MM
    cat=br["cat"]
    if cat=="flat_full": BF.add(base,nrm,th); cnt["black_full"]+=1
    elif cat=="flat_cut": BC.add(base,nrm,th); cnt["black_cut"]+=1
    elif cat=="L_corner_full": BL.add(base,nrm,th); cnt["black_L_full"]+=1
    elif cat=="L_corner_cut": BL.add(base,nrm,th); cnt["black_L_cut"]+=1
for m in (RF,RC,RL,RQ,BF,BC,BL): m.build()

# labels + camera + light
def label(t,loc,col=(1,1,1,1),size=0.32):
    cu=bpy.data.curves.new(t,type='FONT');cu.body=t;cu.size=size
    ob=bpy.data.objects.new("L_"+t[:10],cu);ob.location=loc;ob.rotation_euler=(math.radians(90),0,0)
    mt=bpy.data.materials.new("lm"+t[:6]);mt.use_nodes=True;b=mt.node_tree.nodes.get("Principled BSDF")
    if b:b.inputs["Base Color"].default_value=col
    cu.materials.append(mt);C_AN.objects.link(ob)
label("BLACK canopy (blue brick) in front-centre entrance gap",(2.0,-2.2,3.2),(0.4,0.7,1,1))
for nm,A in ASSEMBLY.items():
    uw=max((v[0] for br in RED[nm]["bricks"] for v in br["verts"]),default=0)*MM
    mid=A["origin"]+A["u"]*(uw/2)+A["n"]*0.5
    label("RED "+nm,(mid.x,mid.y,FIRST_FLOOR+0.3),(1,0.8,0.6,1))

def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
ctr=Vector((WX/2,WY/2,0.5))
cam=bpy.data.objects.new("Camera",bpy.data.cameras.new("Camera"));cam.location=Vector((WX/2,-WY-3,7));cam.data.lens=24
scene.collection.objects.link(cam);look(cam,Vector((WX/2,0,1)));scene.camera=cam
sun=bpy.data.objects.new("Sun",bpy.data.lights.new("Sun",'SUN'));sun.data.energy=3.3
sun.rotation_euler=(math.radians(54),math.radians(16),math.radians(-52));scene.collection.objects.link(sun)
scene.world=bpy.data.worlds.new("W");scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get("Background")
if bg: bg.inputs["Color"].default_value=(0.55,0.6,0.66,1);bg.inputs["Strength"].default_value=0.6
scene.render.engine='CYCLES'
try: scene.cycles.device='GPU'
except Exception: pass
scene.cycles.samples=48;scene.render.resolution_x=1800;scene.render.resolution_y=1200


# ============================ CLIP LAYER (new; bricks above are unchanged) ============================
import json as _json
_CIP=None
_HD=os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ""
for _c in [os.path.join(_HD,"clip_instances_red_d_se_garden_position_fix.json"),
           r"C:\Users\Stras\Documents\Claude\Projects\Brick slip PJ 001\New requirement 6 - website v2\clip_instances_red_d_se_garden_position_fix.json",
           os.path.join(_HD,"..","03_regeneration_kit","inputs","clip_instances_red_d_se_garden_position_fix.json")]:
    if os.path.isfile(_c): _CIP=_json.load(open(_c)); break
if _CIP:
    CLIPS=_CIP["clips"]
    def _cc(n):
        c=bpy.data.collections.new(n); scene.collection.children.link(c); c.hide_viewport=False; return c
    CC={"Rs":_cc("Clips_Red_Standard"),
        "Bos":_cc("Clips_Black_Ordinary_Standard"),
        "Bcs":_cc("Clips_Black_Canopy_Standard"),
        "Bcc":_cc("Clips_Black_Canopy_Cut"),
        "Bca":_cc("Clips_Black_Canopy_Angled")}
    def _cm(n,rgba):
        m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value=rgba
            if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=1.0
        m.blend_method='OPAQUE'; return m   # clips now OPAQUE (alpha 1.0)
    CM={"Rs":_cm("clip_RedStd",(0.95,0.30,0.22,1.0)),
        "Bos":_cm("clip_BlkOrdStd",(0.25,0.50,0.95,1.0)),
        "Bcs":_cm("clip_BlkCanStd",(0.35,0.65,0.98,1.0)),
        "Bcc":_cm("clip_BlkCanCut",(0.98,0.62,0.18,1.0)),
        "Bca":_cm("clip_BlkCanAng",(0.10,0.85,0.72,1.0))}   # OPAQUE
    class _Acc:
        def __init__(s,key): s.key=key; s.v=[]; s.f=[]
        def add(s,poly,nrm):
            k=len(poly); off=Vector(nrm).normalized()*(-0.25*MM); b0=len(s.v)  # 0.25mm behind (-normal)  # 1mm behind (-normal)
            for p in poly: s.v.append(tuple(p))
            for p in poly: q=Vector(p)+off; s.v.append((q.x,q.y,q.z))
            s.f.append([b0+i for i in range(k)]); s.f.append([b0+k+i for i in range(k-1,-1,-1)])
            for i in range(k):
                j=(i+1)%k; s.f.append([b0+i,b0+j,b0+k+j,b0+k+i])
        def build(s):
            if not s.v: return
            me=bpy.data.meshes.new("ClipMesh_"+s.key); me.from_pydata(s.v,[],s.f); me.update()
            o=bpy.data.objects.new("Clips_"+s.key,me); o.data.materials.append(CM[s.key]); CC[s.key].objects.link(o)
    ACC={k:_Acc(k) for k in CC}
    for cl in CLIPS:
        rg=cl.get("region"); kd=cl["kind"]
        if cl["colour"]=="Red": key="Rs"
        elif rg=="black_ordinary": key="Bos"
        elif kd=="angled": key="Bca"
        elif kd=="cut": key="Bcc"
        else: key="Bcs"                       # black canopy standard
        ACC[key].add(cl["poly"], cl["normal"])
    for a in ACC.values(): a.build()
    na=sum(1 for c in CLIPS if c["angled"]); nc=sum(1 for c in CLIPS if c["kind"]=="cut")
    n20=sum(1 for c in CLIPS if c.get("region")=="black_sloped_canopy" and c["source"]==20)
    print(f"CLIPS (corrected 40deg) added: {len(CLIPS)} pieces (canopy angled={na}, canopy cut={nc}, canopy 20mm={n20}) in 5 hideable translucent layers")

print("="*60);print("  COMBINED RED+BLACK model built (FLAT CORNERS - no red L)")
for k in ("red_full","red_cut","red_corner_lap","red_corner_half","red_L_full","red_L_cut","black_full","black_cut","black_L_full","black_L_cut"):
    print(f"    {k:16}{cnt[k]}")
red=cnt['red_full']+cnt['red_cut']+cnt['red_corner_lap']+cnt['red_corner_half']+cnt['red_L_full']+cnt['red_L_cut']
blk=cnt['black_full']+cnt['black_cut']+cnt['black_L_full']+cnt['black_L_cut']
print(f"    RED total {red} | BLACK total {blk} | GRAND {red+blk}")
