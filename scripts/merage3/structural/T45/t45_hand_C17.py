# -*- coding: utf-8 -*-
"""Task 45: hand check C17 Story1 50x50 with 16phi18 (fibre / strain compatibility, functions of T44/t44_hand_checks.py)."""
import os, math, json
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "T44", "t44_hand_checks.py"), encoding="utf-8").read()
exec(src[:src.index("Pu, M2, M3 = ")])               # section(), capacity(), bars, fc, fy ...
Pu, M2, M3 = -274.5, -43.7, 271.8                     # trial 16phi18: C17 S1 bottom, A22-7_EXP+_EYP- (same forces as Rev6a)
Mu = math.hypot(M2, M3)
res = {}
for db in (18, 20):
    As1 = math.pi * db ** 2 / 4
    r = capacity(Pu, M2, M3)
    res[f"16phi{db}"] = {"phiMn": round(r[0], 1), "phi": round(r[3], 3), "ratio_hand": round(Mu / r[0], 3), "rho_%": round(16 * As1 / 250000 * 100, 2)}
res["Mu"] = round(Mu, 1); res["ETABS_16phi18"] = 1.150; res["ETABS_16phi20"] = 0.961
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t45_hand_C17.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
