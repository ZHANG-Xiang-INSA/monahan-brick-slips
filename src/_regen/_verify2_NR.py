# SUPERSEDED: this second-pass verifier belongs to the BASEMENT-REMOVED variant (7318/117 L/46).
# For the FLAT-CORNER variant in THIS folder run:  python3 _verify_flat.py  (33 checks)
import sys; print(__doc__ or 'SUPERSEDED - run _verify_flat.py instead'); sys.exit(0)
# ---- original (inert) below ----
# import sys,types,json,collections,openpyxl,ezdxf,hashlib
# from unittest.mock import MagicMock
# exec(open("_measure_corners.py").read().split("M=\"")[0])
# NR=".."  # New requirement root
# M=NR+"/combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py"
# src=open(M).read().replace('    def add(s,base,normal,t):\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',
#    '    def add(s,base,normal,t):\n        _BR.append((s.n,min(p.z for p in base),max(p.z for p in base)))\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',1)
# import os;g={"_BR":[],"__file__":os.path.abspath(M),"__name__":"x"};exec(compile(src,M,"exec"),g)
# BR=g["_BR"];bc=collections.Counter(n for n,a,b in BR)
# nred=sum(v for k,v in bc.items() if k.startswith("Red"));nblk=sum(v for k,v in bc.items() if k.startswith("Black"))
# P=[]
# P.append(("model red slips below z=0 (must 0)", sum(1 for n,a,b in BR if n.startswith("Red") and b<-0.001), 0))
# BT={t["type_id"]:t for t in json.load(open(NR+"/brick_types.json"))["types"]}
# P.append(("model total == brick_types total", nred+nblk, sum(m["qty"] for m in BT.values())))
# P.append(("model total == 7318", nred+nblk, 7318))
# P.append(("model black == 1461 (unchanged)", nblk, 1461))
# P.append(("model red_L == 117", bc.get("Red_L",0), 117))
# P.append(("brick_types type count == 46", len(BT), 46))
# # brick cutting DXF headers
# d=ezdxf.readfile(NR+"/brick_tile_cutting_layout_red_d_se_garden_position_fix.dxf")
# nh=sum(1 for e in d.modelspace() if e.dxftype()=="TEXT" and e.dxf.text.split()[:1] and e.dxf.text.split()[0].startswith("B") and e.dxf.text.split()[0][1:].isdigit())
# P.append(("brick cutting DXF headers == 46", nh, 46))
# # brick Excel procurement total
# wb=openpyxl.load_workbook(NR+"/brick_tile_schedule_detailed_red_d_se_garden_position_fix.xlsx",data_only=True)
# ws=wb["Brick Procurement Summary"];rows=list(ws.iter_rows(values_only=True));hd=[i for i,r in enumerate(rows) if r and any(isinstance(c,str) and c.strip() in("Type ID","Brick Type ID") for c in r)][0]
# tc=next(j for j,c in enumerate(rows[hd]) if isinstance(c,str) and "Type" in c);qc=next(j for j,c in enumerate(rows[hd]) if isinstance(c,str) and c.strip()=="Quantity")
# exq={r[tc].strip():r[qc] for r in rows[hd+1:] if r and isinstance(r[tc],str) and r[tc].strip().startswith("B") and isinstance(r[qc],int)}
# P.append(("brick Excel Procurement total == 7318", sum(exq.values()), 7318))
# P.append(("brick Excel per-type == brick_types", sum(1 for k in BT if exq.get(k)!=BT[k]["qty"]), 0))
# # clips model==excel==dxf, none below grade
# CI=json.load(open(NR+"/clip_instances_red_d_se_garden_position_fix.json"));clips=CI["clips"];mclip=collections.Counter(c["type_id"] for c in clips)
# dxfq={t["type_id"]:t["qty"] for t in CI["types"]}
# wb2=openpyxl.load_workbook(NR+"/clip_schedule_red_d_se_garden_position_fix.xlsx",data_only=True);ws2=wb2["Procurement Summary"];r2=list(ws2.iter_rows(values_only=True))
# h2=[i for i,r in enumerate(r2) if r and any(isinstance(c,str) and "quantity" in c.lower() for c in r)][0]
# t2=next(j for j,c in enumerate(r2[h2]) if isinstance(c,str) and "type" in c.lower());q2=next(j for j,c in enumerate(r2[h2]) if isinstance(c,str) and "quantity" in c.lower())
# xl2={r[t2].strip():r[q2] for r in r2[h2+1:] if r and isinstance(r[t2],str) and r[t2][:1] in "RT" and isinstance(r[q2],int)}
# P.append(("clip model==excel==dxf totals", (sum(mclip.values()),sum(xl2.values()),sum(dxfq.values())), (2232,2232,2232)))
# P.append(("clip per-type model==excel==dxf", all(mclip.get(t)==xl2.get(t)==dxfq.get(t) for t in set(list(mclip)+list(xl2)+list(dxfq))), True))
# # clip z (look for any vertical coord <0 in clip polys)
# zbad=0
# for c in clips:
#     vs=c.get("poly") or c.get("verts") or []
#     for v in vs:
#         if len(v)>=3 and v[2]<-1: zbad+=1; break
# P.append(("clips below grade (z<0) (must 0)", zbad, 0))
# # above-grade red identical + black identical (independent recompute)
# OLD=json.load(open("../../11_final_red_d_se_garden_position_fix/03_regeneration_kit/inputs/red_brick_placement_v7_stairfix.json"))
# NEW=json.load(open(NR+"/red_brick_placement_v7_stairfix.json"))
# def zge(p,w): return sorted((b["t"],tuple(tuple(round(c,1) for c in v) for v in b["verts"])) for b in p[w]["bricks"] if sum(v[1] for v in b["verts"])/len(b["verts"])>=-1)
# P.append(("above-grade red identical (4 walls)", all(zge(OLD,w)==zge(NEW,w) for w in ["A_NE_side","B_SW_side","C_NW_front","D_SE_garden"]), True))
# P.append(("black placement byte-identical", hashlib.md5(open("../../11_final_red_d_se_garden_position_fix/03_regeneration_kit/inputs/black_placement_fixed7.json","rb").read()).hexdigest()==hashlib.md5(open(NR+"/black_placement_fixed7.json","rb").read()).hexdigest(), True))
# # per-wall DXF reconcile is printed by the builder; here check black-face DXF exists + brick layout files present
# import glob
# P.append(("per-wall + black-face DXFs present (5)", len(glob.glob(NR+"/brick_layout_*.dxf")), 5))
# ok=all(a==b for _,a,b in P)
# for lab,a,b in P: print(("PASS  " if a==b else "FAIL  ")+lab+": %s vs %s"%(a,b))
# print("\nSECOND-PASS:", "ALL PASS ✓" if ok else "HAS FAILURES")
