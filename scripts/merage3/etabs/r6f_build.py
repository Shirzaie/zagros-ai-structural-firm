# -*- coding: utf-8 -*-
"""Merage3 Rev6f build (task 53, boss order 2026-11-07: apply the 6 answers of task 52).   python r6f_build.py
Fresh copy of Merage3_Rev6e.EDB -> Merage3_Rev6f.EDB (Rev6e untouched). Own ETABS instance (never attaches to an open ETABS).
  1. rho = 1.3 (ASCE 7-22 12.3.4.2: torsionally irregular, 2-bay frames in X): seismic factors x 1.3 in the 51 A22 and the ASD combos.
  2. drift patterns EXDP/EXDN/EYDP/EYDN (2800 ed.4 and ASCE 12.8.6.2: analytical T, no 1.25T cap), Ecc as EXP..:
     X: T 0.990 -> B = 1.263 x 1.098 = 1.386, C = 0.30 x 1.386 / 7.5 = 0.0555, k = 0.5T + 0.75 = 1.245
     Y: T 1.132 -> B = 1.104 x 1.126 = 1.243, C = 0.0497, k = 1.316   (A 0.30, soil II: Ts 0.5, S 1.5; I 1.0; R 7.5)
     Linear static cases from the PDELTA stiffness. Used for drift only (not in any combination).
  3. vertical earthquake on the 14 cantilevers (frames with torsion modifier 0.1): pattern EV = 0.18 (D + Dead part + SD)
     (2800 ed.4: Fv = 0.6 A I Wp = 0.18 Wp). From a first run of Rev6e: support shear V and moment M of D + DP + SD on each
     cantilever give an equivalent uniform load q and tip load P (V = qL + P, M = qL^2/2 + PL); EV = 0.18 q and 0.18 P.
     In the A22 combos: A22-6* (1.35D, gravity) + EV, A22-7* (0.75D, uplift) - EV; ASD-8* +0.7EV, ASD-9* +0.525EV, ASD-10* -0.7EV.
     ASCE 12.4.4 (net upward 0.2D on cantilevers): checked by hand in r6f_run.py (a new design combo cannot be flagged by the API).
  4. modal initial stiffness: NOT changed (the modal table edit corrupted MaxModes on a probe copy) -> manual step in ETABS.
  5. k = 1.05 for EXP, EXN, EYP, EYN (design T = 1.25 x 0.05 x 12.2^0.9 = 0.594 s; ASCE CuTa 0.62 s).
  6. deleted the 75 combos that no design or script uses (ACI-*, U*, UDConS*, ACI-ENVELOPE); kept A22 (51 + A22-ENV) and ASD (76 + ASD-ENV).
Writes r6f_build_summary.json, cantilever_EV_Rev6f.csv, log_r6f_build.txt"""
import sys, os, json, shutil, csv, math
import comtypes.client
from r5_common import HERE, EXE, p, table, finish
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SRC = os.path.join(HERE, "Merage3_Rev6e.EDB")
EDB = os.path.join(HERE, "Merage3_Rev6f.EDB")
RHO = 1.3
SEIS = ["EXP", "EXN", "EYP", "EYN"]
DRIFT = [("EXDP", "EXP", 0.0555, 1.245), ("EXDN", "EXN", 0.0555, 1.245), ("EYDP", "EYP", 0.0497, 1.316), ("EYDN", "EYN", 0.0497, 1.316)]
K_STR = 1.05
FV = 0.6 * 0.30 * 1.0
DEADS = ["Dead", "Dead part", "SuperDead"]
S = {"rho": RHO, "drift": DRIFT, "k": K_STR, "Fv_ratio": FV}


def edit_table(m, key, fn):
    db = m.DatabaseTables
    rr = db.GetTableForEditingArray(key, "")
    ver, fields, n, data = rr[0], list(rr[1]), rr[2], list(rr[3])
    nf = len(fields); rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
    rows = fn(fields, rows)
    fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
    flat = [v if v is not None else "" for r_ in rows for v in r_]
    p("  Set", db.SetTableForEditingArray(key, ver, list(fi[3]), len(rows), flat)[-1])
    res = db.ApplyEditedTables(True); p("  Apply", res[0], res[1], res[2], res[3])
    assert res[1] == 0, "table import errors"


def fmt(v):
    return str(v).replace(".", "/")


if __name__ == "__main__":
    e = None
    try:
        assert not os.path.exists(EDB), "Rev6f already exists - not overwritten"
        shutil.copy2(SRC, EDB); p("fresh copy", SRC, "->", EDB)
        h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
        e = h.CreateObject(EXE); p("ApplicationStart (own instance)", e.ApplicationStart()); m = e.SapModel
        assert m.File.OpenFile(EDB) == 0 and os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB)
        m.SetPresentUnits(6)  # kN, m
        # ---- 3a. cantilevers and their dead-load support forces (first run of the unchanged model)
        frames = list(m.FrameObj.GetNameList()[1])
        cant = [f for f in frames if abs(m.FrameObj.GetModifiers(f)[0][3] - 0.1) < 1e-6]
        p("cantilevers (torsion modifier 0.1):", len(cant), cant); assert len(cant) == 14, cant
        m.Analyze.SetRunCaseFlag("", False, True)
        for c in ["PDELTA"] + DEADS:
            m.Analyze.SetRunCaseFlag(c, True, False)
        p("run (PDELTA + dead cases)", m.Analyze.RunAnalysis())
        rows = []
        for f in cant:
            pi, pj = m.FrameObj.GetPoints(f)[0:2]
            xi, xj = m.PointObj.GetCoordCartesian(pi), m.PointObj.GetCoordCartesian(pj)
            L = math.dist(xi[0:3], xj[0:3])
            tot = None
            for c in DEADS:
                m.Results.Setup.DeselectAllCasesAndCombosForOutput(); m.Results.Setup.SetCaseSelectedForOutput(c)
                r = m.Results.FrameForce(f, 0, 0, [], [], [], [], [], [], [], [], [], [], [], [], [])
                st, V2, M3 = list(r[2]), list(r[9]), list(r[13])
                tot = [(s, v, mm) for s, v, mm in zip(st, V2, M3)] if tot is None else [(s, a + v, b + mm) for (s, a, b), v, mm in zip(tot, V2, M3)]
            k = max(range(len(tot)), key=lambda i: abs(tot[i][2]))
            s_sup, V, M = tot[k][0], abs(tot[k][1]), abs(tot[k][2])
            sup_at_i = s_sup < L / 2
            Lc = L - s_sup if sup_at_i else s_sup  # from the support station to the tip
            q = max(0.0, 2 * (V - M / Lc) / Lc); P = max(0.0, V - q * Lc)
            if P == 0.0:
                q = V / Lc
            rows.append({"frame": f, "L": round(L, 3), "support_end": "I" if sup_at_i else "J", "s_support": round(s_sup, 3), "V_D": round(V, 2), "M_D": round(M, 2),
                         "q_D": round(q, 3), "P_tip_D": round(P, 2), "q_EV": round(FV * q, 3), "P_EV": round(FV * P, 2)})
        S["cantilevers"] = rows
        for r_ in rows:
            p(" ", r_)
        m.SetModelIsLocked(False)
        # ---- 3b. EV pattern and loads
        r = m.LoadPatterns.Add("EV", 8, 0, True); p("Add EV", r)
        try:
            p("EV initial case PDELTA", m.LoadCases.StaticLinear.SetInitialCase("EV", "PDELTA"))
        except Exception as ex:
            p("EV initial case not set:", ex)
        for r_ in rows:
            f = r_["frame"]
            if r_["q_EV"] > 0:
                rr = m.FrameObj.SetLoadDistributed(f, "EV", 1, 10, 0, 1, r_["q_EV"], r_["q_EV"], "Global", True, True)
                assert (rr[-1] if isinstance(rr, (tuple, list)) else rr) == 0, (f, rr)
            if r_["P_EV"] > 0:
                tip = 1.0 if r_["support_end"] == "I" else 0.0
                rr = m.FrameObj.SetLoadPoint(f, "EV", 1, 10, tip, r_["P_EV"], "Global", True, False)
                assert (rr[-1] if isinstance(rr, (tuple, list)) else rr) == 0, (f, rr)
        with open(os.path.join(HERE, "cantilever_EV_Rev6f.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        # ---- 2. drift patterns
        for nm, src, C, K in DRIFT:
            p("Add", nm, m.LoadPatterns.Add(nm, 5, 0, True))
            try:
                p("  initial PDELTA", m.LoadCases.StaticLinear.SetInitialCase(nm, "PDELTA"))
            except Exception as ex:
                p("  initial case not set:", ex)
        key = "Load Pattern Definitions - Auto Seismic - User Coefficient"
        before = table(m, key)

        def seis(fields, rows_):
            base = {r[0]: r for r in rows_}
            out = []
            for r in rows_:
                if r[0] in SEIS:
                    r = list(r); r[fields.index("K")] = fmt(K_STR)
                if r[0] not in [d[0] for d in DRIFT]:
                    out.append(r)
            for nm, src, C, K in DRIFT:
                r = list(base[src]); r[0] = nm; r[fields.index("C")] = fmt(C); r[fields.index("K")] = fmt(K); out.append(r)
            return out
        edit_table(m, key, seis)
        after = table(m, key); p(after.to_string())
        flags = ["XDir", "XDirPlusE", "XDirMinusE", "YDir", "YDirPlusE", "YDirMinusE", "EccRatio", "TopStory", "BotStory"]
        for nm, src, C, K in DRIFT:
            a_, b_ = after[after.Name == nm].iloc[0], before[before.Name == src].iloc[0]
            assert all(str(a_[f]) == str(b_[f]) for f in flags), (nm, a_, b_)
            assert abs(a_["C"] - C) < 1e-6 and abs(a_["K"] - K) < 1e-6
        for nm in SEIS:
            a_, b_ = after[after.Name == nm].iloc[0], before[before.Name == nm].iloc[0]
            assert all(str(a_[f]) == str(b_[f]) for f in flags) and abs(a_["C"] - 0.1) < 1e-9 and abs(a_["K"] - K_STR) < 1e-9, (nm, a_)
        S["auto_seismic_after"] = after.to_dict("records")
        # ---- 6. delete unused combos
        names = list(m.RespCombo.GetNameList(0, [])[1])
        drop = [n for n in names if not (n.startswith("A22") or n.startswith("ASD"))]
        drop.sort(key=lambda n: 0 if "ENV" in n.upper() else 1)
        for n in drop:
            assert m.RespCombo.Delete(n) == 0, n
        S["deleted_combos"] = drop; p("6. deleted combos", len(drop))
        # ---- 1 + 3c. rho and EV in the combos
        names = list(m.RespCombo.GetNameList(0, [])[1])
        nE = nEV = 0
        for n in names:
            if n.endswith("ENV"):
                continue
            r = m.RespCombo.GetCaseList(n)
            items = list(zip(r[2], r[3]))
            if not any(c in SEIS for c, _ in items):
                continue
            for c, sf in items:
                if c in SEIS:
                    assert m.RespCombo.SetCaseList(n, 0, c, round(sf * RHO, 6))[-1] == 0; nE += 1
            ev = 1.0 if n.startswith("A22-6") else -1.0 if n.startswith("A22-7") else 0.7 if n.startswith("ASD-8") else 0.525 if n.startswith("ASD-9") else -0.7 if n.startswith("ASD-10") else 0
            if ev:
                assert m.RespCombo.SetCaseList(n, 0, "EV", ev)[-1] == 0; nEV += 1
        S["rho_terms"] = nE; S["ev_added_to"] = nEV
        p("1. rho x1.3 on", nE, "terms; 3. EV in", nEV, "combos")
        chk = m.RespCombo.GetCaseList("A22-6_EXP+_EYP+"); p("  check A22-6_EXP+_EYP+", list(zip(chk[2], chk[3])))
        chk = m.RespCombo.GetCaseList("ASD-10-EXP"); p("  check ASD-10-EXP", list(zip(chk[2], chk[3])))
        S["modal"] = "unchanged (manual: Load Cases > Modal > Stiffness = Nonlinear Case PDELTA)"
        p("save", m.File.Save(EDB)); S["saved"] = True
    except Exception:
        import traceback
        p(traceback.format_exc()); S["error"] = traceback.format_exc()
    json.dump(S, open(os.path.join(HERE, "r6f_build_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    finish("r6f_build")
    try:
        if e is not None:
            p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    finish("r6f_build")
    os._exit(0)
