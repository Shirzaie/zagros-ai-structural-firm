# -*- coding: utf-8 -*-
"""Merage3 Rev6e build (task 52, boss order 2026-11-07: apply the correct settings found by comparing with the softcivil
5-story concrete example).   python r6e_build.py
Fresh copy of Merage3_Rev6d.EDB -> _backup\\Merage3_Rev6d_before_T52.EDB -> Merage3_Rev6e.EDB (Rev6d untouched).
Always starts its OWN ETABS instance (another ETABS window may be open with the user's work; it is never attached).
  1. concrete modulus: C25 and C0  E = 4700 sqrt(f'c) = 23500 MPa (ACI 318-19 19.2.2.1(b)); the model had 26857 MPa
     (= 0.043 wc^1.5 sqrt(f'c) with wc = 2500, the reinforced-concrete weight, not the concrete density).
  2. accidental eccentricity 0.0585 -> 0.0610: Ax = (1.325 / 1.2)^2 = 1.219 from the Rev6d torsion ratio 1.325
     (ASCE 7-22 12.8.4.3; same as 2800 ed.4). Auto Seismic table, EccRatio only; direction flags asserted unchanged.
  3. (modal from P-Delta stiffness: not possible through the ETABS 19 API; left as a manual step)
  4. service (ASD) combinations for the foundation in SAFE, ASCE 7-22 2.4.5 with Ev = 0.2 SDS D (SDS 0.75 as the A22 set):
     D | D+L | D+Lr | D+0.75L+0.75Lr | 1.105D +- 0.7E | 1.07875D + 0.75L +- 0.525E | 0.495D +- 0.7E,
     E = each seismic pattern alone and with 30 % of the other direction (same pairing as A22). Not design combos.
Writes r6e_build_summary.json, log_r6e_build.txt"""
import sys, os, json, shutil
import comtypes.client
from r5_common import HERE, EXE, p, table, finish
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SRC = os.path.join(HERE, "Merage3_Rev6d.EDB")
BAK = os.path.join(HERE, "_backup", "Merage3_Rev6d_before_T52.EDB")
EDB = os.path.join(HERE, "Merage3_Rev6e.EDB")
E_C = 4700 * 25 ** 0.5 * 1000  # kN/m2
ECC = round(0.05 * (1.325 / 1.2) ** 2, 4)  # 0.061
SDS = 0.75
DEAD = ["Dead", "Dead part", "SuperDead"]
S = {"ecc": ECC, "E_kNm2": E_C}


def new_instance():
    h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
    e = h.CreateObject(EXE)
    p("ApplicationStart (own instance)", e.ApplicationStart())
    return e, e.SapModel


def seismic_terms():
    """[(suffix, [(case, sf)...])]: single patterns +- and the 100/30 pairs of the A22 set"""
    out = []
    for q in ("EXP", "EXN", "EYP", "EYN"):
        out += [(f"+{q}", [(q, 1)]), (f"-{q}", [(q, -1)])]
    for a, b in (("EXP", "EYP"), ("EXN", "EYN"), ("EYP", "EXP"), ("EYN", "EXN")):
        for sa in (1, -1):
            for sb in (1, -1):
                out.append((f"_{a}{'+' if sa > 0 else '-'}_{b}{'+' if sb > 0 else '-'}", [(a, sa), (b, 0.3 * sb)]))
    return out


def asd_combos():
    C = {"ASD-1": [(d, 1) for d in DEAD], "ASD-2": [(d, 1) for d in DEAD] + [("Live", 1)], "ASD-3": [(d, 1) for d in DEAD] + [("Lr", 1)],
         "ASD-4": [(d, 1) for d in DEAD] + [("Live", 0.75), ("Lr", 0.75)]}
    kD = {"ASD-8": 1 + 0.14 * SDS, "ASD-9": 1 + 0.105 * SDS, "ASD-10": 0.6 - 0.14 * SDS}
    fE = {"ASD-8": 0.7, "ASD-9": 0.525, "ASD-10": 0.7}
    for k in kD:
        for suf, terms in seismic_terms():
            C[k + suf] = [(d, round(kD[k], 5)) for d in DEAD] + ([("Live", 0.75)] if k == "ASD-9" else []) + [(c, round(fE[k] * s, 5)) for c, s in terms]
    return C


if __name__ == "__main__":
    e = None
    try:
        assert not os.path.exists(EDB), "Rev6e already exists - not overwritten"
        os.makedirs(os.path.dirname(BAK), exist_ok=True)
        if not os.path.exists(BAK):
            shutil.copy2(SRC, BAK)
        shutil.copy2(BAK, EDB)
        p("fresh copy", BAK, "->", EDB)
        e, m = new_instance()
        r = m.File.OpenFile(EDB); p("OpenFile", r); assert r == 0
        assert os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB)
        m.SetPresentUnits(6)  # kN, m, C
        m.SetModelIsLocked(False)
        # 1. concrete modulus
        S["materials"] = {}
        for mat in ("C25", "C0"):
            g = m.PropMaterial.GetMPIsotropic(mat, 0, 0, 0, 0)
            E0, U, A = g[0], g[1], g[2]
            r = m.PropMaterial.SetMPIsotropic(mat, E_C, U, A)
            g2 = m.PropMaterial.GetMPIsotropic(mat, 0, 0, 0, 0)
            S["materials"][mat] = {"E_before": E0, "E_after": g2[0], "U": U}
            p("1.", mat, "E", E0, "->", g2[0], "ret", r); assert abs(g2[0] - E_C) < 1
        # 2. eccentricity (EccRatio only)
        db = m.DatabaseTables
        key = "Load Pattern Definitions - Auto Seismic - User Coefficient"
        before = table(m, key)
        rr = db.GetTableForEditingArray(key, "")
        ver, fields, n, data = rr[0], list(rr[1]), rr[2], list(rr[3])
        nf = len(fields); rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
        ie = fields.index("EccRatio")
        for r_ in rows:
            r_[ie] = str(ECC).replace(".", "/")
        fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
        flat = [v if v is not None else "" for r_ in rows for v in r_]
        p("2. Set", db.SetTableForEditingArray(key, ver, list(fi[3]), n, flat)[-1])
        res = db.ApplyEditedTables(True); p("   Apply", res[0], res[1], res[2], res[3])
        after = table(m, key)
        flags = ["XDir", "XDirPlusE", "XDirMinusE", "YDir", "YDirPlusE", "YDirMinusE", "C", "K", "TopStory", "BotStory"]
        assert (before[flags].astype(str).values == after[flags].astype(str).values).all(), (before, after)
        assert (abs(after["EccRatio"] - ECC) < 1e-6).all(), after
        S["auto_seismic_after"] = after.to_dict("records")
        p(after.to_string())
        # 3. modal from P-Delta stiffness
        S["modal_initial"] = "not set: ModalEigen.SetInitialCase does not exist in the ETABS 19 API (manual: Load Cases > Modal > Initial conditions > PDELTA)"
        # 4. ASD combinations
        C = asd_combos()
        names = list(m.RespCombo.GetNameList(0, [])[1])
        for nm, terms in C.items():
            assert nm not in names, nm
            assert m.RespCombo.Add(nm, 0) == 0, nm
            for c, sf in terms:
                assert m.RespCombo.SetCaseList(nm, 0, c, sf)[-1] == 0, (nm, c)
        assert m.RespCombo.Add("ASD-ENV", 1) == 0
        for nm in C:
            assert m.RespCombo.SetCaseList("ASD-ENV", 1, nm, 1)[-1] == 0
        S["asd_combos"] = {k: [list(t) for t in v] for k, v in C.items()}
        p("4. ASD combos", len(C), "+ ASD-ENV")
        p("save", m.File.Save(EDB)); S["saved"] = True
    except Exception:
        import traceback
        p(traceback.format_exc()); S["error"] = traceback.format_exc()
    json.dump(S, open(os.path.join(HERE, "r6e_build_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    finish("r6e_build")
    try:
        if e is not None:
            p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    finish("r6e_build")
    os._exit(0)
