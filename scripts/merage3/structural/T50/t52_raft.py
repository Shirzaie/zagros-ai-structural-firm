# -*- coding: utf-8 -*-
"""Task 52: raft under the column rows A and B/B' (boss: "raft - only strips A and B"), strip C as given (0.80 x 2.00).
Rigid-foundation method (ACI 318-19 ch. 13): for every A22 combination the soil pressure is linear along Y (resultant of the
column loads), bending moment / shear by statics with the column point loads; envelope over the 51 combinations.
Raft: X -0.25 .. 3.35 (outer edge of strip A to 1.00 beyond axis B), Y -0.25 .. 20.01; columns C1 C2 C16 C17 (A), C5 C6 C18 C19 (B/B').
Checks: longitudinal flexure (per m), one-way shear (lambda_s = 1.0 for footings, ACI 13.2.6.2), punching at every column,
transverse flexure, soil pressure (service D+SD+L, linear). Thickness: 0.80 tried first, then the minimum that passes.
Writes t52_raft.json"""
import json, math, os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
fc, fy = 25.0, 400.0
R = pd.read_csv(os.path.join(PRJ, "ETABS", "Merage3_Rev6d_joint_reactions_SAFE.csv"), encoding="utf-8-sig")
G = json.load(open(os.path.join(PRJ, "ETABS", "geom_Rev6d.json"), encoding="utf-8"))
P = G["points"]
col = {(round(v["xi"], 2), round(v["yi"], 2)): v["label"] for v in G["frames"].values() if v["kind"] == "column" and v["story"] == "Story1"}
R["lab"] = [col[(round(P[str(u)]["x"], 2), round(P[str(u)]["y"], 2))] for u in R["UniqueName"]]
XY = {col[(round(P[str(u)]["x"], 2), round(P[str(u)]["y"], 2))]: (P[str(u)]["x"], P[str(u)]["y"]) for u in R["UniqueName"].unique()}
RAFT_COLS = ["C1", "C2", "C16", "C17", "C5", "C6", "C18", "C19"]
X0, X1, Y0, Y1 = -0.25, 3.35, -0.25, 20.01
Bw, Lr = X1 - X0, Y1 - Y0
combos = [c for c in R["Output Case"].unique() if str(c).startswith("A22-")]


def loads(case_list):
    g = R[R["Output Case"].isin(case_list)].groupby("lab")["FZ"].sum()
    return {c: float(g[c]) for c in RAFT_COLS}


def statics(Pc, ys):
    """linear pressure along Y (per unit length) balancing the loads; returns M(y), V(y) samples and the end pressures"""
    Ptot = sum(Pc.values()); My = sum(Pc[c] * XY[c][1] for c in Pc)
    yc = My / Ptot
    e = yc - (Y0 + Y1) / 2
    w_avg = Ptot / Lr
    k = 12 * Ptot * e / Lr ** 3                                         # slope of w(y) about the centre
    w = lambda y: w_avg + k * (y - (Y0 + Y1) / 2)
    out = []
    for y in ys:
        # integrate w from Y0 to y (trapezoid closed form)
        a = y - Y0
        W = w_avg * a + k * ((y - (Y0 + Y1) / 2) ** 2 - ((Y0 - Y1) / 2) ** 2) / 2
        Mw = w_avg * a * a / 2 + k * (a ** 3 / 3 - a * a * Lr / 4)       # moment of w about y (w linear: k*(s - Lr/2), s from Y0)
        V = W - sum(Pc[c] for c in Pc if XY[c][1] <= y)
        M = Mw - sum(Pc[c] * (y - XY[c][1]) for c in Pc if XY[c][1] <= y)
        out.append((y, M, V))
    return out, w(Y0), w(Y1), e


ys = [Y0 + i * 0.01 for i in range(int(Lr / 0.01) + 1)]
env = {"Mpos": 0.0, "Mneg": 0.0, "V": 0.0}
crit = {}
colsY = sorted({XY[c][1] for c in RAFT_COLS})
for c in combos:
    Pc = loads([c])
    res, w0, w1, e = statics(Pc, ys)
    for y, M, V in res:
        if M > env["Mpos"]:
            env["Mpos"], crit["Mpos"] = M, (c, round(y, 2))
        if M < env["Mneg"]:
            env["Mneg"], crit["Mneg"] = M, (c, round(y, 2))
    # one-way shear at d from the column faces: evaluated per thickness below (store full curves for the governing combos)
Pserv = loads(["Dead", "SuperDead", "Live", "Lr"])
res_s, w0s, w1s, es = statics(Pserv, ys)
q_serv = (max(w0s, w1s) / Bw + 25 * 0.0, min(w0s, w1s) / Bw)


def check(t):
    db, dt_ = t * 1000 - 100 - 25 - 12.5, t * 1000 - 70 - 25 - 12.5     # phi25 assumed, two layers
    d = min(db, dt_)
    Mpos = env["Mpos"] / Bw; Mneg = -env["Mneg"] / Bw                    # kN.m per m width
    def As_req(Mu, dd):
        Rn = Mu * 1e6 / (0.9 * 1000 * dd ** 2)
        if 2 * Rn / (0.85 * fc) >= 1:
            return float("inf")
        return max(0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc))) * 1000 * dd, 0.0018 * 1000 * t * 1000)
    # one-way shear: envelope of |V| at d from the faces of the columns (0.25 + d)
    Vmax = 0.0
    for c in combos:
        res, *_ = statics(loads([c]), ys)
        for y, M, V in res:
            if all(abs(y - yc_) >= 0.25 + d / 1000 for yc_ in colsY):
                Vmax = max(Vmax, abs(V))
    vu = Vmax / Bw
    phiVc = 0.75 * 0.17 * math.sqrt(fc) * 1000 * d / 1e3
    # punching: interior / edge / corner perimeters at d/2
    pun = {}
    for cl in RAFT_COLS:
        Pu = max(float(R[(R.lab == cl) & (R["Output Case"] == c)]["FZ"].sum()) for c in combos)
        x, y = XY[cl]
        b1 = 0.5 + d / 1000 if x > X0 + 0.5 else 0.5 + d / 2000          # A columns flush with the raft edge (X -0.25)
        b2 = 0.5 + d / 1000 if (Y0 + 0.5 < y < Y1 - 0.5) else 0.5 + d / 2000
        bo = (2 * b1 + 2 * b2) if (x > X0 + 0.5 and Y0 + 0.5 < y < Y1 - 0.5) else ((2 * b1 + b2) if (x <= X0 + 0.5) != (not (Y0 + 0.5 < y < Y1 - 0.5)) else (b1 + b2))
        alpha = 40 if bo == 2 * b1 + 2 * b2 else (30 if bo == 2 * b1 + b2 else 20)
        vc = min(0.33, 0.17 * (1 + 2 / 1.0), 0.083 * (alpha * d / (bo * 1000) + 2)) * math.sqrt(fc)
        qnet = Pu / (Bw * Lr)
        Vu = Pu - qnet * b1 * b2
        pun[cl] = {"Pu": round(Pu, 1), "bo_m": round(bo, 2), "vu_MPa": round(Vu * 1e3 / (bo * 1000 * d), 3), "phi_vc_MPa": round(0.75 * vc, 3),
                   "ok": Vu * 1e3 / (bo * 1000 * d) <= 0.75 * vc}
    # transverse: per m strip, supports at X 0 and 2.35, overhang 1.00 beyond B, pressure = max linear net factored pressure
    qmax_u = 0.0
    for c in combos:
        _, w0, w1, _ = statics(loads([c]), ys)
        qmax_u = max(qmax_u, max(w0, w1) / Bw)
    Mt_over = qmax_u * 1.0 ** 2 / 2
    Mt_span = qmax_u * 2.35 ** 2 / 8 - Mt_over / 2
    return {"t_m": t, "d_mm": round(d), "Mu_long_pos_kNm_m (top)": round(Mpos, 1), "Mu_long_neg_kNm_m (bottom)": round(Mneg, 1),
            "As_top_req_mm2_m": round(As_req(Mpos, dt_)), "As_bot_req_mm2_m": round(As_req(Mneg, db)),
            "vu_kN_m": round(vu, 1), "phiVc_kN_m": round(phiVc, 1), "one_way_ok": vu <= phiVc,
            "punching": pun, "punching_ok": all(v["ok"] for v in pun.values()),
            "q_u_max_kPa": round(qmax_u, 1), "Mu_transverse_overhang_kNm_m": round(Mt_over, 1), "Mu_transverse_span_kNm_m": round(Mt_span, 1),
            "As_transverse_bot_req": round(As_req(max(Mt_over, Mt_span), db)), "As_transverse_top_req": round(As_req(max(Mt_over, 1.0), dt_))}


tries = [check(t) for t in (0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60)]
ok = next((c for c in tries if c["one_way_ok"] and c["punching_ok"] and c["As_top_req_mm2_m"] < 1e6 and c["As_bot_req_mm2_m"] < 1e6), None)
OUT = {"raft_plan": {"X": [X0, X1], "Y": [Y0, Y1], "width_m": round(Bw, 2), "length_m": round(Lr, 2), "columns": RAFT_COLS},
       "envelope_long": {"M_pos_kNm (whole width)": round(env["Mpos"], 1), "at": crit.get("Mpos"), "M_neg_kNm": round(env["Mneg"], 1), "at_neg": crit.get("Mneg")},
       "service_soil_pressure_kPa": {"max": round(max(w0s, w1s) / Bw + 25 * (ok["t_m"] if ok else 0.8), 1), "min": round(min(w0s, w1s) / Bw + 25 * (ok["t_m"] if ok else 0.8), 1),
                                     "eccentricity_m": round(es, 3)},
       "tries": tries, "selected": ok}
json.dump(OUT, open(os.path.join(HERE, "t52_raft.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for c in tries:
    print(c["t_m"], c["d_mm"], "M+", c["Mu_long_pos_kNm_m (top)"], "M-", c["Mu_long_neg_kNm_m (bottom)"], "As t/b", c["As_top_req_mm2_m"], c["As_bot_req_mm2_m"],
          "vu", c["vu_kN_m"], "phiVc", c["phiVc_kN_m"], "pun", c["punching_ok"], "trans", c["Mu_transverse_overhang_kNm_m"], c["Mu_transverse_span_kNm_m"])
print("selected", ok["t_m"] if ok else None, json.dumps(OUT["service_soil_pressure_kPa"]), OUT["envelope_long"])
