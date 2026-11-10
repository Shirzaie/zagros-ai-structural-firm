# -*- coding: utf-8 -*-
"""Task 42 (2026-10-24) = task-34 script re-pointed to ETABS Rev6 (storeys 4.00/3.40/3.30, stair, half/half wall mass).
Original header (task 34): beam / column reinforcement selection from the ETABS Rev5 (after T32-33)
ACI 318-19 design results. READ ONLY: uses ETABS/Merage3_Rev5_results.xlsx + geom_after_T32-33.json;
the EDB is not opened.

Output: t34_design.json (consumed by make_struct_T34.py) and t34_beam_schedule.csv

Rules (all documented in the T34 report):
  materials  f'c = 25 MPa, longitudinal S400 (fy 400), transverse S340 (fyt 340), clear cover 40 mm (ACI 20.5.1.3)
  beams      continuous 4phi16 top + 4phi16 bottom (>= As,min 1.4/fy bw d, ACI 9.6.1.2 / 18.6.3.1)
             extra top at each end = ETABS AsTop(end) - 804 (+Al/3 if torsion), unified at a joint for collinear beams
             extra bottom (full length) = max AsBot - 804 (+Al/3)
             web torsion bars (Al/3 split on two faces) when ETABS TLngRebar > 0
             hoops: q = Av/s + 2At/s (ETABS VRebar + 2 TTrnRebar); hinge zone 2h from the face
                    s <= min(d/4=110, 6db=96, 150) -> 90 (ACI 18.6.4.4); middle s <= d/2 -> 200 (18.6.4.6)
             cantilevers B3/B5/B6: boss decision 3phi25 top + 3phi25 bottom + 2phi16 per side, closed phi12@80 full length
  columns    as modelled (16phi16 / 12phi16, ETABS check mode); hoops from Ash (ACI 18.7.5.4) and 6db (18.7.5.3/5)
"""
import csv
import json
import math
import os
from collections import defaultdict

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
XLSX = os.path.join(PRJ, "ETABS", "Merage3_Rev6_results.xlsx")
GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6.json")
AB = {10: 78.54, 12: 113.1, 14: 153.9, 16: 201.1, 18: 254.5, 20: 314.2, 22: 380.1, 25: 490.9}
CONT = 4 * AB[16]                       # 4phi16 = 804 mm2
CANT = {"B3", "B5", "B6"}
STORIES = ["Story1", "Story2", "Story3", "Story4", "Story5"]


def extra_bars(need):
    """smallest-area set of 2..4 equal bars (phi16..phi22) >= need; '' if need <= 0"""
    if need <= 1.0:
        return "", 0.0
    best = None
    for n in (2, 3, 4):
        for d in (16, 18, 20, 22):
            a = n * AB[d]
            if a >= need and (best is None or a < best[2] - 1e-6):
                best = (n, d, a)
    if best is None:
        n = math.ceil(need / AB[25])
        best = (n, 25, n * AB[25])
    return f"{best[0]}φ{best[1]}", best[2]


def hoop(q, smax):
    """two-leg closed hoop for demand q (mm2/mm): phi10 if s >= 75, else phi12; s rounded down to 5 mm"""
    for d in (10, 12):
        s = min(smax, math.floor(2 * AB[d] / max(q, 1e-9) / 5) * 5)
        if s >= 75 or d == 12:
            return d, s, round(2 * AB[d] / s, 3)


def main():
    g = json.load(open(GEOM, encoding="utf-8"))
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows = list(wb["Beam Design Summary"].iter_rows(values_only=True))
    h = rows[0]
    st = defaultdict(list)
    for r in rows[1:]:
        d = dict(zip(h, r))
        st[(d["Label_project"], d["Story"])].append(d)
    frames = {(f["label"], f["story"]): f for f in g["frames"].values() if f["kind"] == "beam"}
    beams = {}
    for (lab, sto), lst in st.items():
        f = frames[(lab, sto)]
        L = f["L"]
        sec = lst[0]["DesignSect"]                                   # BWxxH50
        bw = int(sec[2:4]) * 10
        hh = int(sec.split("H")[1]) * 10                             # BW40xH40 on Story5 (Rev6)
        lst.sort(key=lambda d: d["Station"])
        s0, s1 = lst[0]["Station"], lst[-1]["Station"]                # column faces (rigid end offsets)
        cant = lab in CANT
        Al = max(d["TLngRebar"] for d in lst) * 1e6
        At = max(d["TTrnRebar"] for d in lst) * 1e3
        q = [(d["Station"], d["VRebar"] * 1e3 + 2 * d["TTrnRebar"] * 1e3) for d in lst]
        hz = 2 * hh / 1000
        q_h = max(v for s, v in q if (s - s0) <= hz + 1e-6 or (s1 - s) <= hz + 1e-6 or cant)
        mid = [v for s, v in q if (s - s0) > hz + 1e-6 and (s1 - s) > hz + 1e-6]
        q_m = max(mid) if mid else None
        topI = lst[0]["AsTop"] * 1e6
        topJ = lst[-1]["AsTop"] * 1e6
        bot = max(d["AsBot"] for d in lst) * 1e6
        n_ = len(lst)
        topmid = lst[n_ // 2]["AsTop"] * 1e6 if n_ >= 5 else 0          # mid-span station
        topqI = lst[1]["AsTop"] * 1e6 if n_ >= 5 else 0                 # quarter stations (Ln/4 from the face)
        topqJ = lst[-2]["AsTop"] * 1e6 if n_ >= 5 else 0
        asmin = max(d["AsMinTop"] for d in lst) * 1e6
        warn = sorted({d["WarnMsg"] for d in lst} | {d["ErrMsg"] for d in lst} - {"No Message"})
        warn = [w for w in warn if w != "No Message"]
        beams[(lab, sto)] = dict(label=lab, story=sto, sec=sec, bw=bw, L=round(L, 3), xi=f["xi"], yi=f["yi"], xj=f["xj"], yj=f["yj"],
                                 topI=topI, topJ=topJ, topmid=topmid, topqI=topqI, topqJ=topqJ, bot=bot, asmin=asmin, Al=Al, At=At, q_h=q_h, q_m=q_m,
                                 cant=cant, warn=warn, label_etabs=f["label_etabs"])
    # unify top steel at joints of collinear beams (same story)
    def key(x, y):
        return (round(x, 3), round(y, 3))
    ends = defaultdict(list)
    for k, b in beams.items():
        if b["cant"]:
            continue
        ends[(b["story"],) + key(b["xi"], b["yi"])].append((k, "I"))
        ends[(b["story"],) + key(b["xj"], b["yj"])].append((k, "J"))

    def direc(b):
        return "Y" if abs(b["xj"] - b["xi"]) < 0.5 else "X"
    req = {}
    for k, b in beams.items():
        req[(k, "I")] = b["topI"] + b["Al"] / 3
        req[(k, "J")] = b["topJ"] + b["Al"] / 3
    gov = dict(req)
    for jt, lst in ends.items():
        for d in ("X", "Y"):
            grp = [e for e in lst if direc(beams[e[0]]) == d]
            if len(grp) > 1:
                m = max(req[e] for e in grp)
                for e in grp:
                    gov[e] = m
    out = []
    for k, b in sorted(beams.items(), key=lambda kv: (STORIES.index(kv[0][1]), int(kv[0][0][1:]))):
        r = dict(label=b["label"], story=b["story"], label_etabs=b["label_etabs"], sec=b["sec"], L=b["L"])
        if b["cant"]:
            r.update(top="3φ25", topI="3φ25", topJ="(free end)", bot="3φ25", web="2φ16 EF",
                     hoop_h="φ12@80", hoop_m="φ12@80 (full L)", AsTop_req=round(max(b["topI"], b["topJ"])), AsBot_req=round(b["bot"]),
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=None, q_cap_h=round(2 * AB[12] / 80, 3),
                     ok=b["q_h"] <= 2 * AB[12] / 80 and max(b["topI"], b["topJ"]) + b["Al"] / 3 <= 3 * AB[25] + 1 and b["bot"] + b["Al"] / 3 <= 3 * AB[25] + 1)
        else:
            eI, aI = extra_bars(gov[(k, "I")] - CONT)
            eJ, aJ = extra_bars(gov[(k, "J")] - CONT)
            # mid-span top demand (rare) and 18.6.3.2 (bottom >= 1/2 top at the face, any section >= 1/4 max)
            needb = max(b["bot"] + b["Al"] / 3, 0.5 * max(b["topI"], b["topJ"]), 0.25 * max(gov[(k, "I")], gov[(k, "J")]))
            eb, ab = extra_bars(needb - CONT)
            web = ""
            if b["Al"] > 1:
                side = b["Al"] / 3 / 2
                d = 12 if side <= AB[12] else (14 if side <= AB[14] else 16)
                web = f"1φ{d} EF"
            dd = int(b["sec"].split("H")[1]) * 10 - 60
            dh, sh, caph = hoop(b["q_h"], min(90, int(dd / 4 / 5) * 5))
            if b["q_m"] is not None:
                dm, sm, capm = hoop(b["q_m"], min(200, int(dd / 2 / 5) * 5))
                hm = f"φ{dm}@{sm}"
            else:
                capm, hm = None, "(2h zones meet)"
            r.update(top="4φ16", topI=("4φ16+" + eI) if eI else "4φ16", topJ=("4φ16+" + eJ) if eJ else "4φ16",
                     bot=("4φ16+" + eb) if eb else "4φ16", web=web, hoop_h=f"φ{dh}@{sh}", hoop_m=hm,
                     AsTop_req=round(max(gov[(k, "I")], gov[(k, "J")])), AsTopI_gov=round(gov[(k, "I")]), AsTopJ_gov=round(gov[(k, "J")]),
                     AsTopI_own=round(b["topI"]), AsTopJ_own=round(b["topJ"]),
                     AsTop_prov_I=round(CONT + aI), AsTop_prov_J=round(CONT + aJ), AsBot_req=round(needb), AsBot_prov=round(CONT + ab),
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=round(b["q_m"], 2) if b["q_m"] is not None else None,
                     q_cap_h=caph, q_cap_m=capm, topmid_req=round(b["topmid"]), topq_req=round(max(b["topqI"], b["topqJ"])),
                     ok=(CONT + aI >= gov[(k, "I")] - 1 and CONT + aJ >= gov[(k, "J")] - 1 and CONT + ab >= needb - 1
                         and caph >= b["q_h"] - 1e-6 and (capm is None or capm >= b["q_m"] - 1e-6) and CONT >= b["topmid"] - 1
                         and CONT + aI >= b["topqI"] - 1 and CONT + aJ >= b["topqJ"] - 1))
        r["warn"] = b["warn"]
        out.append(r)
    # columns
    rows = list(wb["Column Design Summary"].iter_rows(values_only=True))
    h = rows[0]
    col = {}
    for rr in rows[1:]:
        d = dict(zip(h, rr))
        k = (d["Label_project"], d["Story"])
        c = col.setdefault(k, dict(label=k[0], story=k[1], sec=d["DesignSect"], pmm=0, combo="", v=0, warn=set()))
        if d["PMMRatio"] > c["pmm"]:
            c["pmm"], c["combo"] = d["PMMRatio"], d["PMMCombo"]
        c["v"] = max(c["v"], d["VMajRebar"] * 1e3, d["VMinRebar"] * 1e3)
        if d["WarnMsg"] != "No Message":
            c["warn"].add(d["WarnMsg"])
    fc, fyt, cov = 25.0, 340.0, 40.0
    hoops = {}
    for b_, nb, legs, dh, s in ((500, 16, 3, 12, 85), (450, 16, 3, 12, 85), (400, 12, 4, 12, 90)):
        bc = b_ - 2 * cov
        Ag, Ach = b_ * b_, bc * bc
        ash = max(0.3 * (Ag / Ach - 1) * fc / fyt * bc, 0.09 * bc * fc / fyt)
        smax = min(b_ / 4, 6 * 16, 150)
        cap = legs * AB[dh] / s
        hoops[b_] = dict(bars=f"{nb}φ16", rho=round(nb * AB[16] / Ag * 100, 2), Ash_s_req=round(ash, 2), legs=legs, hoop=f"φ{dh}@{s}",
                         Ash_s_prov=round(cap, 2), s_max=smax, ok=cap >= ash and s <= smax)
    cols = []
    for k, c in sorted(col.items(), key=lambda kv: (int(kv[0][0][1:]), kv[0][1])):
        b_ = int(c["sec"][1:3]) * 10
        c["warn"] = sorted(c["warn"])
        c["v_ok"] = hoops[b_]["Ash_s_prov"] >= c["v"]
        cols.append(c)
    res = dict(beams=out, columns=cols, column_hoops=hoops, source=dict(xlsx=XLSX, geom=GEOM))
    json.dump(res, open(os.path.join(HERE, "t42_design.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "t42_beam_schedule.csv"), "w", encoding="utf-8-sig", newline="") as fo:
        keys = ["story", "label", "label_etabs", "sec", "L", "topI", "topJ", "bot", "web", "hoop_h", "hoop_m", "AsTopI_own", "AsTopJ_own",
                "AsTopI_gov", "AsTopJ_gov", "AsTop_prov_I", "AsTop_prov_J", "AsBot_req", "AsBot_prov", "Al_req", "q_h", "q_cap_h", "q_m", "q_cap_m", "ok", "warn"]
        w = csv.DictWriter(fo, keys, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow(r)
    bad = [r for r in out if not r["ok"]]
    print("beams", len(out), "not ok:", [(r["label"], r["story"]) for r in bad])
    print("hoops", hoops)
    print("col max pmm", max(c["pmm"] for c in cols), "col v not ok", [(c["label"], c["story"]) for c in cols if not c["v_ok"]])
    for r in out:
        if r["story"] in ("Story1",) or r["label"] in ("B12", "B32"):
            print(r["story"], r["label"], r["sec"], r["topI"], "|", r["topJ"], "| bot", r["bot"], "|", r["web"], "|", r["hoop_h"], r["hoop_m"], "q", r["q_h"], r.get("q_m"), "Al", r["Al_req"])


if __name__ == "__main__":
    main()
