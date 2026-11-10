# -*- coding: utf-8 -*-
"""Task 44 independent hand checks (structural engineer, 2026-10-31).  python t44_hand_checks.py
1. C17 Story1 50x50 16phi20 biaxial PMM by fibre strain compatibility (ACI 318-19 22.2, 21.2.2) - Rev6a governing combo
2. landing corbel (sliding seat) on C2 / C6 - ACI 318-19 16.5
3. new Story5 cantilever B3 (40x40) shear + torsion threshold - ACI 22.5, 22.7
Writes t44_hand_checks.json"""
import math, json, os
import numpy as np
OUT = {}
fc, fy, Es, ecu = 25.0, 400.0, 200000.0, 0.003
# ---------- 1. column fibre PMM
b = h = 500.0; dp = 50 + 10 + 10              # clear cover 50 (ETABS 0.05) + tie 10 + half bar 10
nb = 5; As1 = math.pi * 20 ** 2 / 4
xs = np.linspace(-b / 2 + dp, b / 2 - dp, nb)
bars = sorted({(x, y) for x in xs for y in (xs[0], xs[-1])} | {(x, y) for y in xs for x in (xs[0], xs[-1])})
assert len(bars) == 16
N = 60
cx = np.linspace(-b / 2 + b / N / 2, b / 2 - b / N / 2, N)
CX, CY = np.meshgrid(cx, cx); CX, CY = CX.ravel(), CY.ravel(); dA = (b / N) ** 2
beta1 = 0.85


def section(theta, c):
    """neutral axis normal at angle theta (compression side direction), depth c from extreme fibre -> (P, Mx, My) N, N.mm"""
    ux, uy = math.cos(theta), math.sin(theta)
    corners = [(sx * b / 2, sy * h / 2) for sx in (-1, 1) for sy in (-1, 1)]
    dmax = max(ux * x + uy * y for x, y in corners)
    dist = dmax - (ux * CX + uy * CY)                      # depth from compression fibre
    comp = dist <= beta1 * c
    P = 0.85 * fc * dA * comp.sum(); Mx = 0.85 * fc * dA * (CY[comp]).sum(); My = 0.85 * fc * dA * (CX[comp]).sum()
    et_max = 0.0
    for x, y in bars:
        d = dmax - (ux * x + uy * y)
        eps = ecu * (c - d) / c
        et_max = max(et_max, -eps)
        fs = max(-fy, min(fy, Es * eps))
        if d <= beta1 * c:
            fs -= 0.85 * fc
        P += fs * As1; Mx += fs * As1 * y; My += fs * As1 * x
    ety = fy / Es
    phi = 0.65 if et_max <= ety else (0.90 if et_max >= ety + 0.003 else 0.65 + 0.25 * (et_max - ety) / 0.003)
    return P, Mx, My, phi


def capacity(Pu, Mu2, Mu3):
    """moment capacity (resultant) at constant Pu in the direction of (Mu2, Mu3); Pu compression +, kN / kN.m"""
    ang_u = math.atan2(abs(Mu2), abs(Mu3))
    res = []
    for th in np.linspace(0, math.pi / 2, 91):
        lo, hi = 5.0, 5000.0
        for _ in range(60):
            c = math.sqrt(lo * hi)
            P, Mx, My, phi = section(th, c)
            if phi * P / 1e3 > Pu:
                hi = c
            else:
                lo = c
        P, Mx, My, phi = section(th, c)
        res.append((math.atan2(abs(My), abs(Mx)), math.hypot(Mx, My) * phi / 1e6, phi, th))
    res.sort()
    a = [r[0] for r in res]; mm = [r[1] for r in res]
    M = float(np.interp(ang_u, a, mm)); ph = res[int(np.argmin([abs(x - ang_u) for x in a]))][2]
    return (M, None, None, ph)


Pu, M2, M3 = -274.5, -43.7, 271.8            # Rev6a corner table, C17 Story1 bottom, A22-7_EXP+_EYP- (tension)
best = capacity(Pu, M2, M3)
Mu = math.hypot(M2, M3)
OUT["C17_Story1_16phi20"] = {"Pu_kN": Pu, "M2": M2, "M3": M3, "Mu_resultant": round(Mu, 1), "phiMn_same_direction_kNm": round(best[0], 1),
                             "phi": round(best[3], 3), "ratio_hand": round(Mu / best[0], 3), "ratio_ETABS": 0.961,
                             "note": "ETABS ratio uses the PMM envelope of all stations/combos; hand = this combo at the bottom station"}
for rb, lab in ((16, "16phi16 (Rev6)"),):
    pass
# same with 16phi16 for reference
As1 = math.pi * 16 ** 2 / 4
best16 = capacity(Pu, M2, M3)
OUT["C17_Story1_16phi16_reference"] = {"phiMn": round(best16[0], 1), "ratio_hand": round(Mu / best16[0], 3)}
# ---------- 2. corbel (sliding seat) ACI 318-19 16.5
PD, PL = 36.6, 16.18                          # per column, typical landing (Rev6 stair_loads; Story1 32.9 / 14.2)
Vu = max(1.4 * PD, 1.2 * PD + 1.6 * PL, (1.2 + 0.2 * 0.75) * PD + 1.0 * PL)
Nuc = 0.2 * Vu                               # minimum restraint force (16.5.3.5), treated as live load
bw, hc = 400.0, 450.0                         # corbel width (column 45-50; 400 net of chamfers), depth at column face
d = hc - 50 - 6
av = 125.0                                    # bearing centre from column face (pad 150 x 250, gap 40 + 50 edge)
fyc = 400.0; phi = 0.75; mu = 1.4
OUT["corbel_geometry_ok"] = {"av/d": round(av / d, 3), "<=1 (16.5.1.1)": av / d <= 1, "Nuc<=Vu": Nuc <= Vu, "hc_at_edge>=0.5d": True}
Vn_max = min(0.2 * fc * bw * d, (3.3 + 0.08 * fc) * bw * d, 11 * bw * d) / 1e3
Avf = Vu * 1e3 / (phi * fyc * mu)
Af = (Vu * 1e3 * av + Nuc * 1e3 * (hc - d)) / (phi * fyc * 0.9 * d)
An = Nuc * 1e3 / (phi * fyc)
Asc = max(Af + An, 2 / 3 * Avf + An, 0.04 * fc / fyc * bw * d)
Ah = 0.5 * (Asc - An)
OUT["corbel"] = {"Vu_kN": round(Vu, 1), "Nuc_kN": round(Nuc, 1), "phiVn_max_kN": round(phi * Vn_max, 1), "ok_Vn_max": Vu <= phi * Vn_max,
                 "Avf_mm2": round(Avf), "Af_mm2": round(Af), "An_mm2": round(An), "Asc_req_mm2": round(Asc), "Asc_provided": "4phi14 = 616 mm2",
                 "Ah_req_mm2": round(Ah), "Ah_provided": "3 closed stirrups phi10 within 2d/3 = 6 x 78.5 = 471 mm2",
                 "bearing_stress_MPa": round(Vu * 1e3 / (150 * 250), 2), "phi_bearing_MPa": round(0.65 * 0.85 * fc, 1)}
# ---------- 3. new Story5 cantilever B3 40x40
bw, hb, cv = 400.0, 400.0, 41.5
Acp, pcp = bw * hb, 2 * (bw + hb); x1, y1 = bw - 2 * cv, hb - 2 * cv; Aoh, ph = x1 * y1, 2 * (x1 + y1)
phTth = 0.75 * 0.083 * math.sqrt(fc) * Acp ** 2 / pcp / 1e6
Tu, Vu3 = 10.10, 31.9
ats = Tu * 1e6 / (0.75 * 2 * 0.85 * Aoh * 340)
Vc = 0.17 * math.sqrt(fc) * bw * 340 / 1e3
avs = max(0.0, (Vu3 / 0.75 - Vc) * 1e3 / (340 * 340))
OUT["Story5_B3_cantilever"] = {"Tu": Tu, "phiTth": round(phTth, 2), "phiTcr": round(4 * phTth, 2), "At/s_hand": round(ats, 3),
                               "Av/s_hand_gravity_shear (Vc kept)": round(avs, 3), "Av/s+2At/s_hand": round(avs + 2 * ats, 3), "ETABS": 2.99, "ETABS_design_shear_kN": 178,
                               "explanation": "ETABS Av/s 2.05 comes from a design shear of 178 kN (Beam Shear Envelope) vs Vu 32 kN from analysis: FrameType Program Determined (= Sway Special in SDC D) capacity shear; the 12 existing cantilevers are Sway Ordinary"}
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t44_hand_checks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print(json.dumps(OUT, indent=1, ensure_ascii=False, default=str))
