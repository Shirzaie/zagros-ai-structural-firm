# -*- coding: utf-8 -*-
"""Task 57 (2026-11-07, boss): BEAMS: longitudinal bars phi16 only (continuous, extra, web, cantilevers, BS/BT/BH); stirrups phi10
only - single closed phi10 (2 legs) where s >= 75 mm, else DOUBLE closed phi10 (2 hoops, 4 legs; the outer hoop alone carries the
torsion 2At/s); never phi12 in beams. Bars that do not fit one layer go to a 2nd layer and d is reduced for that. Cantilevers B3/B5/B6:
8phi16 top + 8phi16 bottom (>= the former 3phi25 = 1473 mm2), phi10 @ 80 full length (single or double).
Task 55 (2026-11-07) = task-50 script re-pointed to ETABS Rev6h (E 4700 sqrt fc, rho 1.0, EV on the cantilevers, k 1.05;
C17 Story1 C50X50/18T20 = 6 x 5 bars, 4-leg hoops across the 6-bar faces). Previous header: Task 50 (2026-10-31) = task-48 script re-pointed to ETABS Rev6d (all floor joists in Y, stair beam BS and trimmer BT 30x50). Previous header: Task 46 (2026-10-31) = task-44 script re-pointed to ETABS Rev6b (Story2 columns 16phi18, 3-leg hoops in B38/B10/B12 and wherever
2 legs would need s < 50, hook beam BH 25x40, column hoops in lo and mid zones). Previous header: Task 44 (2026-10-31) = task-42 script re-pointed to ETABS Rev6a (Story1 columns 16phi20, cantilever J = 0.1, penthouse extended;
new Story5 frames carry their project labels from geom_Rev6d.json; new Story5 cantilevers B3/B5 40x40 use the general beam rules).
Task 42 header: task-34 script re-pointed to ETABS Rev6 (storeys 4.00/3.40/3.30, stair, half/half wall mass).
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
XLSX = os.path.join(PRJ, "ETABS", "Merage3_Rev6h_results.xlsx")
GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6d.json")
AB = {10: 78.54, 12: 113.1, 14: 153.9, 16: 201.1, 18: 254.5, 20: 314.2, 22: 380.1, 25: 490.9}
CONT = 4 * AB[16]                       # 4phi16 = 804 mm2
CANT = {"B3", "B5", "B6"}
STORIES = ["Story1", "Story2", "Story3", "Story4", "Story5"]


def nmax(bw):
    """phi16 bars that fit one layer: clear spacing 25 mm, cover 40, phi10 hoop (ACI 25.2.1)"""
    return int((bw - 2 * 40 - 2 * 10 - 16) // (16 + 25)) + 1


def extra_bars(need, bw=None, dd=None, base=4):
    """phi16 only (boss 2026-11-07): n = ceil(need / 201.1), at least 2; with a 2nd layer the lever arm is reduced
    (centroid shift 41 mm x bars in the 2nd layer / all bars) and n is raised until the area covers need x d / (d - shift)"""
    if need <= 1.0:
        return "", 0.0
    n = max(2, math.ceil(need / AB[16]))
    if bw and dd:
        for _ in range(20):
            tot = base + n; n2 = max(0, tot - nmax(bw)); shift = 41.0 * n2 / tot
            if (tot * AB[16]) >= (need + base * AB[16]) * dd / (dd - shift) - 1e-6:
                break
            n += 1
    return f"{n}φ16", n * AB[16]


THREE = {"B38", "B10", "B12"}            # boss 2026-10-31 (task 46): 3-leg hoops


def hoop(q, smax, at2=0.0):
    """phi10 only (boss 2026-11-07). q = Av/s + 2At/s (mm2/mm). Single closed phi10 (2 legs) if s >= 75 mm; else DOUBLE closed
    phi10 (two hoops, 4 legs) with the outer hoop alone carrying 2At/s. s rounded down to 5 mm, s <= smax.
    returns (text, s, capacity q, legs, ok)"""
    s1 = min(smax, math.floor(2 * AB[10] / max(q, 1e-9) / 5) * 5)
    if s1 >= 75:
        return f"φ10@{s1}", s1, round(2 * AB[10] / s1, 3), 2, True
    s2 = min(smax, math.floor(min(4 * AB[10] / max(q, 1e-9), 2 * AB[10] / max(at2, 1e-9)) / 5) * 5)
    return f"2xφ10@{s2} (double)", s2, round(4 * AB[10] / s2, 3), 4, s2 >= 50


def main():
    g = json.load(open(GEOM, encoding="utf-8"))
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows = list(wb["Beam Design Summary"].iter_rows(values_only=True))
    h = rows[0]
    st = defaultdict(list)
    for r in rows[1:]:
        d = dict(zip(h, r))
        st[(d["Label_project"], d["Story"])].append(d)
    newl = g.get("new_objects_project_labels", {}).get("frames", {})
    for u, v in newl.items():
        g["frames"][u]["label_etabs"] = g["frames"][u]["label"]
        g["frames"][u]["label"] = v["label"]
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
        cant = lab in CANT and sto != "Story5"
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
    for k, b in sorted(beams.items(), key=lambda kv: (STORIES.index(kv[0][1]), int(kv[0][0][1:]) if kv[0][0][1:].isdigit() else 99)):
        r = dict(label=b["label"], story=b["story"], label_etabs=b["label_etabs"], sec=b["sec"], L=b["L"])
        if b["label"] in ("BS", "BT"):
            r.update(top="3φ16", topI="3φ16", topJ="3φ16", bot="3φ16", web="", hoop_h="φ10@200", hoop_m="φ10@200", legs=2,
                     AsTop_req=round(max(b["topI"], b["topJ"])), AsBot_req=round(b["bot"]), AsBot_prov=603, AsTop_prov_I=603, AsTop_prov_J=603,
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=None, q_cap_h=round(2 * AB[10] / 200, 3),
                     ok=max(b["bot"], 462) <= 603 and max(b["topI"], b["topJ"]) <= 603 and b["q_h"] <= 2 * AB[10] / 200,
                     note=("stair beam" if b["label"] == "BS" else "elevator trimmer") + " 30x50, pinned ends; As,min = 1.4/fy bw d = 462 mm2")
        elif b["label"] == "BH":
            r.update(top="2φ16", topI="2φ16", topJ="2φ16", bot="2φ16", web="", hoop_h="φ10@150", hoop_m="φ10@150", legs=2,
                     AsTop_req=round(max(b["topI"], b["topJ"])), AsBot_req=round(b["bot"]), AsBot_prov=402, AsTop_prov_I=402, AsTop_prov_J=402,
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=None, q_cap_h=round(2 * AB[10] / 150, 3),
                     ok=b["bot"] <= 402 and max(b["topI"], b["topJ"]) <= 402 and b["q_h"] <= 2 * AB[10] / 150,
                     note="hook beam 25x40, pinned ends (M3 released), hook 25 kN; As,min = 1.4/fy bw d = 298 mm2")
        elif b["cant"]:
            nc = max(math.ceil(3 * AB[25] / AB[16]), math.ceil((max(b["topI"], b["topJ"]) + b["Al"] / 3) / AB[16]), math.ceil((b["bot"] + b["Al"] / 3) / AB[16]))
            ht, hs, hc, hl, hok = hoop(b["q_h"], 80, 2 * b["At"])
            r.update(top=f"{nc}φ16", topI=f"{nc}φ16", topJ="(free end)", bot=f"{nc}φ16", web="2φ16 EF",
                     hoop_h=ht, hoop_m=ht + " (full L)", legs=hl, AsTop_req=round(max(b["topI"], b["topJ"])), AsBot_req=round(b["bot"]),
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=None, q_cap_h=hc, n_layer_max=nmax(b["bw"]),
                     ok=hok and b["q_h"] <= hc + 1e-6 and nc <= nmax(b["bw"]) and max(b["topI"], b["topJ"]) + b["Al"] / 3 <= nc * AB[16] + 1 and b["bot"] + b["Al"] / 3 <= nc * AB[16] + 1)
        else:
            dd = int(b["sec"].split("H")[1]) * 10 - 60
            eI, aI = extra_bars(gov[(k, "I")] - CONT, b["bw"], dd)
            eJ, aJ = extra_bars(gov[(k, "J")] - CONT, b["bw"], dd)
            # mid-span top demand (rare) and 18.6.3.2 (bottom >= 1/2 top at the face, any section >= 1/4 max)
            needb = max(b["bot"] + b["Al"] / 3, 0.5 * max(b["topI"], b["topJ"]), 0.25 * max(gov[(k, "I")], gov[(k, "J")]))
            eb, ab = extra_bars(needb - CONT, b["bw"], dd)
            web = ""
            if b["Al"] > 1:
                side = b["Al"] / 3 / 2
                web = f"{max(1, math.ceil(side / AB[16]))}φ16 EF"
            hth, sh, caph, lh, okh = hoop(b["q_h"], min(90, int(dd / 4 / 5) * 5), 2 * b["At"])
            okm = True
            if b["q_m"] is not None:
                hm, sm, capm, lm, okm = hoop(b["q_m"], min(200, int(dd / 2 / 5) * 5), 2 * b["At"])
            else:
                capm, hm = None, "(2h zones meet)"
            n2 = [max(0, 4 + (int(e.split("φ")[0]) if e else 0) - nmax(b["bw"])) for e in (eI, eJ, eb)]
            r.update(top="4φ16", topI=("4φ16+" + eI) if eI else "4φ16", topJ=("4φ16+" + eJ) if eJ else "4φ16",
                     bot=("4φ16+" + eb) if eb else "4φ16", web=web, hoop_h=hth, hoop_m=hm, legs=lh, layer2=dict(topI=n2[0], topJ=n2[1], bot=n2[2]), n_layer_max=nmax(b["bw"]),
                     AsTop_req=round(max(gov[(k, "I")], gov[(k, "J")])), AsTopI_gov=round(gov[(k, "I")]), AsTopJ_gov=round(gov[(k, "J")]),
                     AsTopI_own=round(b["topI"]), AsTopJ_own=round(b["topJ"]),
                     AsTop_prov_I=round(CONT + aI), AsTop_prov_J=round(CONT + aJ), AsBot_req=round(needb), AsBot_prov=round(CONT + ab),
                     Al_req=round(b["Al"]), q_h=round(b["q_h"], 2), q_m=round(b["q_m"], 2) if b["q_m"] is not None else None,
                     q_cap_h=caph, q_cap_m=capm, topmid_req=round(b["topmid"]), topq_req=round(max(b["topqI"], b["topqJ"])),
                     ok=(CONT + aI >= gov[(k, "I")] - 1 and CONT + aJ >= gov[(k, "J")] - 1 and CONT + ab >= needb - 1
                         and okh and okm and caph >= b["q_h"] - 1e-6 and (capm is None or capm >= b["q_m"] - 1e-6) and CONT >= b["topmid"] - 1
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
    for sec_, b_, nb, db, legs, dh, s in (("C50X50/18T20", 500, 18, 20, 4, 12, 85), ("C50X50/16T20", 500, 16, 20, 3, 12, 85), ("C50X50/16T18", 500, 16, 18, 3, 12, 85), ("C50X50/16T16", 500, 16, 16, 3, 12, 85),
                                         ("C45X45/16T16", 450, 16, 16, 3, 12, 85), ("C40X40/12T16", 400, 12, 16, 4, 12, 90)):
        bc = b_ - 2 * cov
        Ag, Ach = b_ * b_, bc * bc
        ash = max(0.3 * (Ag / Ach - 1) * fc / fyt * bc, 0.09 * bc * fc / fyt)
        smax = min(b_ / 4, 6 * db, 150)
        cap = legs * AB[dh] / s
        s_mid = min(6 * db, 150) // 5 * 5
        hoops[sec_] = dict(bars=f"{nb}φ{db}", rho=round(nb * AB[db] / Ag * 100, 2), Ash_s_req=round(ash, 2), legs=legs, hoop=f"φ{dh}@{s}",
                           Ash_s_prov=round(cap, 2), s_max=smax, ok=cap >= ash and s <= smax, hoop_mid=f"φ{dh}@{s_mid}", cap_mid=round(legs * AB[dh] / s_mid, 2))
    cols = []
    for k, c in sorted(col.items(), key=lambda kv: (int(kv[0][0][1:]), kv[0][1])):
        c["warn"] = sorted(c["warn"])
        c["bars"] = hoops[c["sec"]]["bars"]; c["hoop"] = hoops[c["sec"]]["hoop"]
        c["v_ok"] = hoops[c["sec"]]["cap_mid"] >= c["v"]
        c["hoop_mid"] = hoops[c["sec"]]["hoop_mid"]; c["legs"] = hoops[c["sec"]]["legs"]
        ln = {"Story1": 4.00, "Story5": 3.30}.get(c["story"], 3.40) - (0.40 if c["story"] == "Story5" else 0.50)
        b_ = int(c["sec"][1:3]) * 10
        c["lo_mm"] = int(math.ceil(max(b_, ln * 1000 / 6, 450) / 50) * 50)
        cols.append(c)
    res = dict(beams=out, columns=cols, column_hoops=hoops, source=dict(xlsx=XLSX, geom=GEOM))
    json.dump(res, open(os.path.join(HERE, "t55_design.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "t55_beam_schedule.csv"), "w", encoding="utf-8-sig", newline="") as fo:
        keys = ["story", "label", "label_etabs", "sec", "L", "topI", "topJ", "bot", "web", "hoop_h", "hoop_m", "AsTopI_own", "AsTopJ_own",
                "AsTopI_gov", "AsTopJ_gov", "AsTop_prov_I", "AsTop_prov_J", "AsBot_req", "AsBot_prov", "Al_req", "q_h", "q_cap_h", "q_m", "q_cap_m", "ok", "warn"]
        w = csv.DictWriter(fo, keys, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow(r)
    bad = [r for r in out if not r["ok"]]
    print("beams", len(out), "not ok:", [(r["label"], r["story"]) for r in bad])
    print("hoops", hoops)
    with open(os.path.join(HERE, "t55_column_schedule.csv"), "w", encoding="utf-8-sig", newline="") as fo:
        w = csv.DictWriter(fo, ["story", "label", "sec", "bars", "legs", "lo_mm", "hoop", "hoop_mid", "pmm", "combo", "v", "v_ok", "warn"], extrasaction="ignore")
        w.writeheader()
        for c in cols:
            w.writerow(c)
    print("col max pmm", max(c["pmm"] for c in cols), "col v not ok", [(c["label"], c["story"]) for c in cols if not c["v_ok"]])
    for r in out:
        if r["story"] in ("Story1",) or r["label"] in ("B12", "B32"):
            print(r["story"], r["label"], r["sec"], r["topI"], "|", r["topJ"], "| bot", r["bot"], "|", r["web"], "|", r["hoop_h"], r["hoop_m"], "q", r["q_h"], r.get("q_m"), "Al", r["Al_req"])


if __name__ == "__main__":
    main()
