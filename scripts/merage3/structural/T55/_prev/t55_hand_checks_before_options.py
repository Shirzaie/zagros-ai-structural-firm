# -*- coding: utf-8 -*-
"""Task 50 hand checks (ACI 318-19), writes t50_hand_checks.json:
 1. stair waist slab t = 0.20 with the intermediate support BS (span landing beam -> BS = 4.158 m, floor landing 1.842 m)
 2. joists (all floor bays in Y): flexure + deflection of the 7.5 m joist (T section, h 0.31), 6.0 and 5.31 bays
 3. tie beam 30 x 30 hidden in the joists (boss detail) - capacity info only
 4. combined strip footing 0.80 x 2.00 (boss), longitudinal strips under axes A, B/B', C: soil pressure, flexure, shear
    (rigid strip, uniform pressure, Rev6h reactions; task 55)"""
import json, math, os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
fc, fy, Ec = 25.0, 400.0, 26857.0
n = 200000 / Ec
OUT = {}


def Ie_rect(b, h, d, As, Ma):
    rp = As / (b * d); k = math.sqrt(2 * n * rp + (n * rp) ** 2) - n * rp
    Icr = b * (k * d) ** 3 / 3 + n * As * (d - k * d) ** 2
    Ig = b * h ** 3 / 12; Mcr = 0.62 * math.sqrt(fc) * Ig / (h / 2) / 1e6
    return (Icr / (1 - (2 / 3 * Mcr / Ma) ** 2 * (1 - Icr / Ig)) if Ma > 2 / 3 * Mcr else Ig), Icr, Ig, Mcr


def flex(b, d, Mu):
    Rn = Mu * 1e6 / (0.9 * b * d ** 2)
    rho = 0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc)))
    return rho * b * d


# ---- 1. stair
t, d = 200.0, 200 - 20 - 6
qD, qL = 25 * 0.20 / 0.870 + 4.43, 4.79
L1, L2 = (11.658 - 7.5) * 1000, (13.5 - 11.658) * 1000
wu = max(1.4 * qD, 1.2 * qD + 1.6 * qL)
Mu1 = wu * (L1 / 1000) ** 2 / 8
As1 = max(flex(1000, d, Mu1), 0.0018 * 1000 * t)
As_prov = 113.1 * 1000 / 150                       # phi12@150
Ma = (qD + qL) * (L1 / 1000) ** 2 / 8
Ie, Icr, Ig, Mcr = Ie_rect(1000, t, d, As_prov, Ma)
dDL = 5 * (qD + qL) * L1 ** 4 / (384 * Ec * Ie)
MaD = qD * (L1 / 1000) ** 2 / 8
IeD = Ie_rect(1000, t, d, As_prov, MaD)[0]
dD = 5 * qD * L1 ** 4 / (384 * Ec * IeD)
dL = dDL - dD
OUT["stair_t200_with_BS"] = {"span1_m": round(L1 / 1000, 3), "span2_floor_landing_m": round(L2 / 1000, 3), "wu": round(wu, 2), "Mu1_kNm_m": round(Mu1, 1),
                             "As_req": round(As1), "bottom": "φ12@150 = 754", "distribution": "φ10@200", "top": "φ10@200 over L/4 at the supports",
                             "floor_landing": "φ10@200 both ways (As,min 360)", "delta_L_mm": round(dL, 1), "L/360": round(L1 / 360, 1),
                             "delta_long_plus_L_mm": round(2 * dD + dL, 1), "L/240": round(L1 / 240, 1), "L/480": round(L1 / 480, 1),
                             "table_l/20_mm": round(L1 / 20), "ok_L240": 2 * dD + dL <= L1 / 240}
# ---- 2. joists, T section: web 100, flange 500 x 60, h 310, block 250 (ASSUMPTION as the model deck)
bw, bf, hf, h = 100.0, 500.0, 60.0, 310.0
qDj, qLj, s = 2.6 + 3.418, 2.0, 0.5                # self weight (ASSUMPTION) + SD of the floors (finish + partition), L 2.0
jo = {}
for name, Lm, bar in (("7.5", 7.5, (2, 16)), ("6.0", 6.0, (2, 14)), ("5.31", 5.31, (2, 12))):
    wuj = (1.2 * qDj + 1.6 * qLj) * s
    Muj = wuj * Lm ** 2 / 8
    dj = h - 25 - 8 - bar[1] / 2
    Asr = Muj * 1e6 / (0.9 * fy * (dj - hf / 2))
    As = bar[0] * math.pi * bar[1] ** 2 / 4
    # deflection: cracked T (NA in the flange), Ig of the T section
    yb = (bw * h * h / 2 + (bf - bw) * hf * (h - hf / 2)) / (bw * h + (bf - bw) * hf)
    Ig = bw * h ** 3 / 12 + bw * h * (h / 2 - yb) ** 2 + (bf - bw) * hf ** 3 / 12 + (bf - bw) * hf * (h - hf / 2 - yb) ** 2
    kd = (-n * As + math.sqrt((n * As) ** 2 + 2 * bf * n * As * dj)) / bf
    Icr = bf * kd ** 3 / 3 + n * As * (dj - kd) ** 2
    Mcr = 0.62 * math.sqrt(fc) * Ig / yb / 1e6
    def de(w):
        Ma_ = w * Lm ** 2 / 8
        Ie_ = Icr / (1 - (2 / 3 * Mcr / Ma_) ** 2 * (1 - Icr / Ig)) if Ma_ > 2 / 3 * Mcr else Ig
        return 5 * w * (Lm * 1000) ** 4 / (384 * Ec * min(Ie_, Ig))
    dD_ = de(qDj * s); dDL_ = de((qDj + qLj) * s)
    jo[name] = {"span_m": Lm, "wu_kN_m": round(wuj, 2), "Mu_kNm": round(Muj, 1), "As_req": round(Asr), "bottom": f"{bar[0]}φ{bar[1]} = {round(As)}",
                "top_at_supports": "1φ12 per joist, L/4 (back to back over the beams)", "delta_L_mm": round(dDL_ - dD_, 1), "L/360": round(Lm * 1000 / 360, 1),
                "delta_long_plus_L_mm": round(2 * dD_ + dDL_ - dD_, 1), "L/240": round(Lm * 1000 / 240, 1), "simply_supported_assumed": True}
OUT["joists"] = jo
# ---- 3. tie beam 30 x 30 (boss): 2phi14 top + 2phi14 bottom, 3 hoops 20x20 phi10 between joists
OUT["tie_beam_30x30"] = {"section": "30 x 30 hidden in the joist slab (boss)", "bars": "2φ14 top + 2φ14 bottom, continuous in X over the whole width, end hooks",
                         "hoops": "3 closed hoops 20 x 20 φ10, 135° hooks, in each 50 cm between two joists", "note": "distribution / tie member; not a primary member (not in ETABS)",
                         "phiMn_kNm": round(0.9 * 308 * fy * (300 - 30 - 10 - 7 - 308 * fy / (0.85 * fc * 300) / 2) / 1e6, 1)}
# ---- 4. strip footings
R = pd.read_csv(os.path.join(PRJ, "ETABS", "Merage3_Rev6h_joint_reactions_SAFE.csv"), encoding="utf-8-sig")
G = json.load(open(os.path.join(PRJ, "ETABS", "geom_Rev6d.json"), encoding="utf-8"))
P = G["points"]
col = {(round(v["xi"], 2), round(v["yi"], 2)): v["label"] for v in G["frames"].values() if v["kind"] == "column" and v["story"] == "Story1"}
def grp(cases):
    g = R[R["Output Case"].isin(cases)].groupby("UniqueName")["FZ"].sum()
    return {col[(round(P[str(u)]["x"], 2), round(P[str(u)]["y"], 2))]: (P[str(u)]["x"], P[str(u)]["y"], float(v)) for u, v in g.items()}
D = grp(["Dead", "SuperDead"]); Lv = grp(["Live", "Lr"])
combos = [c for c in R["Output Case"].unique() if str(c).startswith("A22-")]
U = {}
for c in combos:
    g = R[R["Output Case"] == c].groupby("UniqueName")["FZ"].max()
    for u, v in g.items():
        lab = col[(round(P[str(u)]["x"], 2), round(P[str(u)]["y"], 2))]
        U.setdefault(lab, []).append(float(v))
strips = {"A": ["C1", "C2", "C16", "C17"], "B/B'": ["C5", "C6", "C18", "C19"], "C": ["C9", "C10", "C20", "C21"]}
Y0, Y1, B, Hf = -0.25, 20.01, 2.0, 0.80
gam = 25 * Hf + 18 * 0.0                       # footing self weight; backfill above ignored (top +-0.00)
As10 = 10 * math.pi * 18 ** 2 / 4
db = 800 - 100 - 14 - 9; dt = 800 - 70 - 14 - 9
a_ = As10 * fy / (0.85 * fc * B * 1000)
phiMn_b = 0.9 * As10 * fy * (db - a_ / 2) / 1e6; phiMn_t = 0.9 * As10 * fy * (dt - a_ / 2) / 1e6
phiVc = 0.75 * 0.17 * math.sqrt(fc) * B * 1000 * db / 1e3
st = {}
for sname, cols in strips.items():
    Ls = Y1 - Y0
    Ps = sum(D[c][2] + Lv[c][2] for c in cols); Pu = sum(max(U[c]) for c in cols)
    q_serv = Ps / (B * Ls) + gam
    wu = Pu / Ls                                   # kN/m upward (factored, self weight excluded: it does not bend the strip)
    ys = [D[c][1] for c in cols]
    # inverted continuous beam: uniform upward net factored pressure wu on rigid supports at the columns (conventional method);
    # FE beam (EI constant), 100 elements per span, overhangs at both ends
    import numpy as np
    xs = sorted(set([Y0] + ys + [Y1]))
    nodes = []
    for x0, x1 in zip(xs, xs[1:]):
        k_ = max(4, int((x1 - x0) / 0.05))
        nodes += [x0 + (x1 - x0) * i / k_ for i in range(k_)]
    nodes.append(xs[-1]); N = len(nodes)
    K = np.zeros((2 * N, 2 * N)); F = np.zeros(2 * N)
    for e in range(N - 1):
        l = nodes[e + 1] - nodes[e]
        ke = np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l], [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]]) / l ** 3
        fe = wu * np.array([l / 2, l * l / 12, l / 2, -l * l / 12])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        for i in range(4):
            F[idx[i]] += fe[i]
            for j in range(4):
                K[idx[i], idx[j]] += ke[i, j]
    sup = [min(range(N), key=lambda i: abs(nodes[i] - y)) for y in ys]
    free = [i for i in range(2 * N) if i // 2 not in sup or i % 2 == 1]
    u = np.zeros(2 * N); u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    Mv, Vv = [], []
    for e in range(N - 1):
        l = nodes[e + 1] - nodes[e]
        ue = u[[2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]]
        ke = np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l], [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]]) / l ** 3
        fe = ke @ ue - wu * np.array([l / 2, l * l / 12, l / 2, -l * l / 12])
        Mv += [-fe[1], fe[3]]; Vv += [fe[0], -fe[2]]
    Mmax_pos = max(Mv); Mmax_neg = min(Mv); Vmax = max(abs(v) for v in Vv)
    Rsup = [float(K[2 * i] @ u - F[2 * i]) for i in sup]
    # transverse: cantilever (B - 0.5) / 2 from the column face, q_u net
    qn = Pu / (B * Ls)
    lc = (B - 0.50) / 2
    Mt = qn * lc ** 2 / 2
    As_t = 153.9 * 1000 / 150
    phiMt = 0.9 * As_t * fy * (db + 9 + 7 - As_t * fy / (0.85 * fc * 1000) / 2) / 1e6
    st[sname] = {"columns": cols, "length_m": round(Ls, 2), "P_service_kN": round(Ps, 1), "Pu_max_sum_kN": round(Pu, 1),
                 "q_service_kPa (incl. self weight)": round(q_serv, 1), "Mu_+ (one face)": round(Mmax_pos, 1), "Mu_- (other face)": round(-Mmax_neg, 1), "Mu_max_abs_kNm": round(max(Mmax_pos, -Mmax_neg), 1), "As_req_for_Mu_max_mm2": round(max(Mmax_pos, -Mmax_neg) * 1e6 / (0.9 * fy * 0.9 * db)), "phiMn_top_10φ18": round(phiMn_t, 1), "phiMn_bottom_10φ18": round(phiMn_b, 1),
                 "Vu_max_kN": round(Vmax, 1), "support_reactions_kN (FE, vs column Pu)": [round(-r, 1) for r in Rsup], "phiVc_kN": round(phiVc, 1), "transverse_Mu_kNm_m": round(Mt, 1), "phiMn_transverse_φ14@150": round(phiMt, 1)}
OUT["strip_footings"] = st
OUT["strip_note"] = ("conventional method: inverted continuous beam on the column supports with uniform net factored pressure; worst A22 FZ per column summed (envelope, conservative); the allowable soil pressure is not "
                     "given (SAFE / geotechnical report pending) - QUESTION; strips A (X -0.25..1.75, outer edge flush with the column face at the boundary) "
                     "and B (X 1.35..3.35) overlap 0.40 m (merge)")
OUT["column_loads"] = {c: {"x": D[c][0], "y": D[c][1], "D_SD": round(D[c][2], 1), "L_Lr": round(Lv[c][2], 1), "Pu_max": round(max(U[c]), 1)} for c in D}
json.dump(OUT, open(os.path.join(HERE, "t55_hand_checks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(OUT, indent=1, ensure_ascii=False))
