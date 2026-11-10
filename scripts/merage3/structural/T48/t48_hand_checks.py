# -*- coding: utf-8 -*-
"""Task 48 hand checks (stair t = 0.20 by boss order; joists of the 7.5 m bay in Y; tie beams): stair waist slab t = 0.20 (flexure + deflection, ACI 318-19 7.3, 24.2), hook beam BH 25x40,
penthouse-slab sleeves phi125. Writes t46_hand_checks.json"""
import math, json, os
fc, fy, Ec = 25.0, 400.0, 26857.0
OUT = {}
# ---- stair: one-way strip, horizontal span 6.00 (axis 2 landing beam -> B36 axis 3); flight B top end sliding = simply supported
L = 6000.0; t = 200.0; d = t - 20 - 8                      # cover 20 (interior slab), phi16 half
qD, qL = 25 * 0.20 / 0.870 + 4.43, 4.79                 # kN/m2 on plan, flight t 0.20 (landing 7.12 lower)
wu = max(1.4 * qD, 1.2 * qD + 1.6 * qL)
Mu = wu * (L / 1000) ** 2 / 8
Rn = Mu * 1e6 / (0.9 * 1000 * d ** 2)
rho = 0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc)))
As = max(rho * 1000 * d, 0.0018 * 1000 * t)
As_prov = 201.1 * 1000 / 125                              # phi16@125
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
OUT["stair_waist_t200"] = {"span_m": 6.0, "wu_kN_m2": round(wu, 2), "Mu_kNm_m": round(Mu, 1), "As_req_mm2_m": round(As), "As_prov": "φ16@125 = 1609",
                           "distribution": "φ10@200 (0.0018 b t = 360)", "Ie_mm4_m": round(Ie / 1e6, 1), "Mcr": round(Mcr, 1),
                           "delta_L_mm": round(dL, 1), "L/360_mm": round(L / 360, 1), "delta_long_term_plus_L_mm": round(dlong, 1), "L/240_mm": round(L / 240, 1),
                           "L/480_mm": round(L / 480, 1), "table_7.3.1.1_simply_supported_l/20_mm": round(L / 20),
                           "result": "flexure OK with φ16@125; deflection: see numbers (t = 0.20 < l/20 = 0.30)"}
# t = 0.30 alternative
# flexure capacity check of phi16@125
a_ = As_prov * fy / (0.85 * fc * 1000); phiMn = 0.9 * As_prov * fy * (d - a_ / 2) / 1e6
eps_t = 0.003 * (d - a_ / 0.85) / (a_ / 0.85)
OUT["stair_waist_t200"].update({"phiMn_kNm_m": round(phiMn, 1), "eps_t": round(eps_t, 4), "d_mm": d})
# ---- joists of the 7.5 m bay (Y), length 8 m, slab 0.31 (block 0.25 + topping 0.06), spacing 0.50 (ASSUMPTION, as model deck)
hj, sj, Lj = 310.0, 0.50, 7.5
OUT["joist_7.5m"] = {"span_m": Lj, "slab_h_mm": hj, "ACI_table_9.3.1.1_simply_supported_l/16_mm": round(Lj * 1000 / 16),
                     "one_end_continuous_l/18.5_mm": round(Lj * 1000 / 18.5), "both_continuous_l/21_mm": round(Lj * 1000 / 21),
                     "result": "h = 0.31 < l/21 = 0.357 even with both ends continuous -> deflection must be computed or depth increased (question to the boss)"}
qDj = 2.6 + 3.418; qLj = 2.0
wuj = (1.2 * qDj + 1.6 * qLj) * sj
OUT["joist_7.5m"].update({"wu_kN_m_per_joist": round(wuj, 2), "Mu_simple_kNm": round(wuj * Lj ** 2 / 8, 1),
                          "As_req_mm2 (d 270)": round(wuj * Lj ** 2 / 8 * 1e6 / (0.9 * 400 * 0.95 * 270)),
                          "note": "precast lattice joist; bottom bars per joist from the supplier table for L = 8.0; self weight of the block slab 2.6 kN/m2 (ASSUMPTION)"})
# ---- tie beams (کلاف عرضی): 3 per 7.5 m bay at L/4, perpendicular to the joists, in the slab depth
OUT["tie_beams"] = {"positions_Y_m": [1.875, 3.75, 5.625], "section": "TB 15 x 31 (slab depth), cast with the topping",
                    "bars": "2φ12 bottom + 2φ12 top, closed φ8@200", "anchorage": "into the edge beams B1 / B4 / B7 (axes A, B, C), ld = 0.50 m",
                    "basis": "tie (distribution) ribs for joist spans > 4 m; minimum detailing, not a primary member (not in ETABS)"}
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
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t48_hand_checks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(OUT, indent=1, ensure_ascii=False))
