# -*- coding: utf-8 -*-
"""Task 46 hand checks: stair waist slab t = 0.25 (flexure + deflection, ACI 318-19 7.3, 24.2), hook beam BH 25x40,
penthouse-slab sleeves phi125. Writes t46_hand_checks.json"""
import math, json, os
fc, fy, Ec = 25.0, 400.0, 26857.0
OUT = {}
# ---- stair: one-way strip, horizontal span 6.00 (axis 2 landing beam -> B36 axis 3); flight B top end sliding = simply supported
L = 6000.0; t = 250.0; d = t - 20 - 8                      # cover 20 (interior slab), phi16 half
qD, qL = 11.61, 4.79                                      # kN/m2 on plan (Rev6 stair loads, flight; landing 8.37 lower)
wu = max(1.4 * qD, 1.2 * qD + 1.6 * qL)
Mu = wu * (L / 1000) ** 2 / 8
Rn = Mu * 1e6 / (0.9 * 1000 * d ** 2)
rho = 0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc)))
As = max(rho * 1000 * d, 0.0018 * 1000 * t)
As_prov = 201.1 * 1000 / 150                              # phi16@150
# deflection (24.2.3.5, Ie of 318-19)
n = 200000 / Ec; rp = As_prov / (1000 * d)
k = math.sqrt(2 * n * rp + (n * rp) ** 2) - n * rp
Icr = 1000 * (k * d) ** 3 / 3 + n * As_prov * (d - k * d) ** 2
Ig = 1000 * t ** 3 / 12
Mcr = 0.62 * math.sqrt(fc) * Ig / (t / 2) / 1e6
def defl(w):
    Ma = w * (L / 1000) ** 2 / 8
    Ie = Icr / (1 - (2 / 3 * Mcr / Ma) ** 2 * (1 - Icr / Ig)) if Ma > 2 / 3 * Mcr else Ig
    return 5 * w * L ** 4 / (384 * Ec * min(Ie, Ig)), Ie
dDL, Ie = defl(qD + qL); dD, _ = defl(qD)
dL = dDL - dD
lam = 2.0 / (1 + 50 * 0.0)                                # xi = 2.0 (5 years), no compression steel
dlong = lam * dD + dL
OUT["stair_waist_t250"] = {"span_m": 6.0, "wu_kN_m2": round(wu, 2), "Mu_kNm_m": round(Mu, 1), "As_req_mm2_m": round(As), "As_prov": "φ16@150 = 1341",
                           "distribution": "φ10@150 (0.0018 b t = 450)", "Ie_mm4_m": round(Ie / 1e6, 1), "Mcr": round(Mcr, 1),
                           "delta_L_mm": round(dL, 1), "L/360_mm": round(L / 360, 1), "delta_long_term_plus_L_mm": round(dlong, 1), "L/240_mm": round(L / 240, 1),
                           "L/480_mm": round(L / 480, 1), "table_7.3.1.1_simply_supported_l/20_mm": round(L / 20),
                           "result": "flexure OK; live-load deflection OK; long-term deflection > L/240 -> WARNING (t = 0.25 < l/20 = 0.30)"}
# t = 0.30 alternative
t2 = 300.0; d2 = t2 - 28; Ig2 = 1000 * t2 ** 3 / 12
OUT["stair_alternative_t300_Ig_ratio"] = round(Ig2 / Ig, 2)
# ---- hook beam BH 25x40, span 2.38 (B31 -> B33), pinned, hook 25 kN at 1.45 m + self weight + slab strip (ETABS)
b, h = 250.0, 400.0; dd = h - 40 - 10 - 8
Lh = 2.3825; a = 1.45; P = 25.0
w = 25 * 0.25 * 0.40 * 1.2
Mu_h = 1.2 * P * a * (Lh - a) / Lh + w * Lh ** 2 / 8
Vu_h = 1.2 * P * a / Lh + w * Lh / 2
As_h = Mu_h * 1e6 / (0.9 * fy * 0.9 * dd)
As_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy) * b * dd
phiVc = 0.75 * 0.17 * math.sqrt(fc) * b * dd / 1e3
OUT["hook_beam_BH"] = {"Mu_kNm(1.2D)": round(Mu_h, 1), "Vu_kN": round(Vu_h, 1), "As_req": round(As_h), "As_min": round(As_min), "bottom": "2φ16 = 402",
                       "top": "2φ14 = 308 (hanger / anchorage)", "phiVc_kN": round(phiVc, 1), "stirrups": "φ10@150 closed (Av,min, s <= d/2 = 171)",
                       "ETABS": "As bot 247, Av/s 0 (min), Vu 25.4 kN", "impact": "with an impact factor 2.0 on the hook load As = 2 x 173 = 346 < 402 OK", "note": "the hook point needs an embedded plate or a cast-in eye bolt designed by the elevator supplier; hanger stirrups 2φ10 each side of the hook"}
# ---- sleeves phi125 in the penthouse joist slab at (0.30, 14.10) and (0.30, 15.20)
OUT["sleeves"] = {"positions": [(0.30, 14.10), (0.30, 15.20)], "dia_mm": 125, "edge_to_beam_face_mm": round((0.30 - 0.0625 - 0.20) * 1000),
                  "check": "inside the block (filler) zone between two joists; no joist and no beam cut; 1φ10 trimming bar each side of each sleeve in the topping (opening smaller than the joist spacing; slab strength not reduced)",
                  "condition": "set out the joists so that each sleeve falls between joists (joist spacing ~0.50); if a joist falls on a sleeve, double the adjacent joists"}
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t46_hand_checks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(OUT, indent=1, ensure_ascii=False))
