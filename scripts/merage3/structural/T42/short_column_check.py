# -*- coding: utf-8 -*-
"""Task 42: short-column check of the stair columns C2 (A/2) and C6 (B/2) restrained at mid storey by the half-landing beam
and the inclined stair slab (boss T38d, architect T41). ACI 318-19: Ve = (Mpr,top + Mpr,bot) / lu (18.7.6.1.1, Mpr with
1.25 fy and phi = 1, largest over the factored axial range), Vc = 0 when Pu < Ag f'c / 20 (18.7.6.2.1), Vs = Av fyt d / s
(22.5.8.5.3), Vs <= 0.66 sqrt(f'c) b d (22.5.1.2), phi = 0.75 (21.2.1). Axial range from ETABS Rev6 (Merage3_Rev6_stair_columns.csv).
python short_column_check.py  -> short_column_check.csv / .json"""
import csv, json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FC, FY, FYT, ES, ECU = 25.0, 400.0, 340.0, 200000.0, 0.003
AB = {12: 113.1, 16: 201.1, 18: 254.5, 20: 314.2}


def layers(h, nb_face, db, dprime=60.0):
    """16 bars, 5 per face: layers along the depth (mm from the compression face, area mm2)"""
    n_int = nb_face - 2
    ys = [dprime + k * (h - 2 * dprime) / (nb_face - 1) for k in range(nb_face)]
    out = []
    for k, y in enumerate(ys):
        nb = nb_face if k in (0, nb_face - 1) else 2
        out.append((y, nb * AB[db]))
    return out


def PM(b, h, lay, c, fy):
    a = min(0.85 * c, h) if True else None
    b1 = 0.85
    a = min(b1 * c, h)
    P = 0.85 * FC * a * b
    M = P * (h / 2 - a / 2)
    for y, As in lay:
        eps = ECU * (c - y) / c
        fs = max(-fy, min(fy, ES * eps))
        if y < a:
            fs -= 0.85 * FC          # displaced concrete
        P += fs * As; M += fs * As * (h / 2 - y)
    return P / 1e3, M / 1e6


def Mpr_at(b, h, lay, P_kN, fy):
    lo, hi = 1.0, 5 * h
    for _ in range(80):
        c = (lo + hi) / 2
        P, M = PM(b, h, lay, c, fy)
        if P > P_kN:
            hi = c
        else:
            lo = c
    return PM(b, h, lay, (lo + hi) / 2, fy)[1]


def main():
    sc = list(csv.DictReader(open(os.path.join(PRJ, "ETABS", "Merage3_Rev6_stair_columns.csv"), encoding="utf-8-sig")))
    sec = {"Story1": (500, 16), "Story2": (500, 16), "Story3": (450, 16), "Story4": (450, 16)}
    # clear segments (m): landing beam 0.30 x 0.40, landing TOS ground +2.09 / typical mid storey (architect T41)
    segs = {"Story1": {"lower (+0.00 -> u/s landing beam +1.69)": 1.69, "upper (landing +2.09 -> u/s beam +3.50)": 1.41},
            "Story2": {"lower (+4.00 -> +5.30)": 1.30, "upper (+5.70 -> +6.90)": 1.20},
            "Story3": {"lower (+7.40 -> +8.70)": 1.30, "upper (+9.10 -> +10.30)": 1.20},
            "Story4": {"lower (+10.80 -> +12.10)": 1.30, "upper (+12.50 -> +13.70)": 1.20}}
    rows = []
    for r in sc:
        if r["Column"] not in ("C2", "C6"):
            continue
        st = r["Story"]
        h, db0 = sec[st]
        for db in ([16, 20] if st == "Story1" else [16]):
            b = h
            lay = layers(h, 5, db)
            Pmin, Pmax = float(r["Pu_min_comp_kN"]), float(r["Pu_max_comp_kN"])
            Ps = [Pmin + k * (Pmax - Pmin) / 20 for k in range(21)]
            Mpr = max(Mpr_at(b, h, lay, P, 1.25 * FY) for P in Ps)
            d = h - 60.0
            Ag = b * h
            vc_zero = Pmin < Ag * FC / 20 / 1e3
            Vc = 0.0 if vc_zero else 0.17 * (1 + Pmin * 1e3 / (14 * Ag)) * math.sqrt(FC) * b * d / 1e3
            for legs, dt, s in ((3, 12, 85), (4, 12, 75), (4, 12, 60)):
                Vs = min(legs * AB[dt] * FYT * d / s, 0.66 * math.sqrt(FC) * b * d) / 1e3
                phiVn = 0.75 * (Vc + Vs)
                for seg, lu in segs[st].items():
                    Ve = 2 * Mpr / lu
                    rows.append({"Column": r["Column"], "Story": st, "section": f"{h}x{h} 16phi{db}", "segment": seg, "lu_m": lu,
                                 "Pu_range_kN": f"{Pmin:.0f}..{Pmax:.0f}", "Mpr_kNm": round(Mpr, 1), "Ve_kN": round(Ve, 1),
                                 "Vu_ETABS_kN": max(float(r["V2_max"]), float(r["V3_max"])), "Vc_kN": round(Vc, 1), "hoops": f"{legs} legs phi{dt}@{s}",
                                 "Vs_kN": round(Vs, 1), "phiVn_kN": round(phiVn, 1), "ratio": round(Ve / phiVn, 3), "result": "OK" if Ve <= phiVn else "رد",
                                 "Vn_max_ok (0.66+0.17)": Ve <= 0.75 * (0.66 + 0.17) * math.sqrt(FC) * b * d / 1e3})
    with open(os.path.join(HERE, "short_column_check.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(os.path.join(HERE, "short_column_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for r in rows:
        print(r["Column"], r["Story"], r["section"], r["segment"][:5], r["lu_m"], r["Pu_range_kN"], r["Mpr_kNm"], r["Ve_kN"], r["Vu_ETABS_kN"], r["Vc_kN"], r["hoops"], r["phiVn_kN"], r["ratio"], r["result"], r["Vn_max_ok (0.66+0.17)"])


if __name__ == "__main__":
    main()
