import sys,types,json,collections,openpyxl
from unittest.mock import MagicMock
exec(open("_measure_corners.py").read().split("M=\"")[0])
M="../combined_red_black_brick_with_clips_red_d_se_garden_position_fix.py"
src=open(M).read().replace('    def add(s,base,normal,t):\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',
   '    def add(s,base,normal,t):\n        _BR.append((s.n,min(p.z for p in base)))\n        k=len(base); off=Vector(normal).normalized()*t; b0=len(s.v)',1)
import os;g={"_BR":[],"__file__":os.path.abspath(M),"__name__":"x"};exec(compile(src,M,"exec"),g)
BR=g["_BR"]; bc=collections.Counter(n for n,z in BR)
nred=sum(v for k,v in bc.items() if k.startswith("Red")); nblk=sum(v for k,v in bc.items() if k.startswith("Black"))
nbelow=sum(1 for n,z in BR if n.startswith("Red") and z<-0.001)
print("MODEL: total %d (red %d, black %d, redL %d) | red bricks with z<0: %d (must be 0)"%(nred+nblk,nred,nblk,bc.get("Red_L",0),nbelow))
BT={t["type_id"]:t for t in json.load(open("../brick_types.json"))["types"]}
print("BRICK model==brick_types:",nred+nblk==sum(m['qty'] for m in BT.values()),"| total",sum(m['qty'] for m in BT.values()),"types",len(BT))
CI=json.load(open("../clip_instances_red_d_se_garden_position_fix.json"));mclip=collections.Counter(c["type_id"] for c in CI["clips"])
dxfq={t["type_id"]:t["qty"] for t in CI["types"]}
wb=openpyxl.load_workbook("../clip_schedule_red_d_se_garden_position_fix.xlsx",data_only=True);ws=wb["Procurement Summary"];rows=list(ws.iter_rows(values_only=True))
h=[i for i,r in enumerate(rows) if r and any(isinstance(c,str) and "quantity" in c.lower() for c in r)][0]
tcol=next(j for j,c in enumerate(rows[h]) if isinstance(c,str) and "type" in c.lower());qcol=next(j for j,c in enumerate(rows[h]) if isinstance(c,str) and "quantity" in c.lower())
xl={r[tcol].strip():r[qcol] for r in rows[h+1:] if r and isinstance(r[tcol],str) and r[tcol][:1] in "RT" and isinstance(r[qcol],int)}
print("CLIP model==excel==dxf:",all(mclip.get(t)==xl.get(t)==dxfq.get(t) for t in set(list(mclip)+list(xl)+list(dxfq))),"| total model %d excel %d dxf %d"%(sum(mclip.values()),sum(xl.values()),sum(dxfq.values())))
