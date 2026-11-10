# -*- coding: utf-8 -*-
"""Merage3 Rev6b build (task 46, boss approval 2026-10-31 17:00 of the 11 proposals of report 2026-10-31).
Fresh copy of _backup\\Merage3_Rev6a_before_T46.EDB (= Rev6a) -> Merage3_Rev6b.EDB (Rev6a untouched).   python r6b_build.py
  1. Story2 columns C50X50/16T16 -> C50X50/16T18 (12 columns); Story1 16T20, Story3-4 C45X45/16T16, Story5 C40X40/12T16 unchanged
  2. new Story5 cantilevers B3 / B5 (146, 147): FrameType Sway Ordinary + torsion J = 0.1 (as the other 12)
  3. torsional irregularity: accidental eccentricity 0.05 -> 0.0585 (Ax = (1.298/1.2)^2 = 1.17, ASCE 7-22 12.8.4.3) through the
     Auto Seismic table (EccRatio only; direction flags checked unchanged on a test copy, r6b_ecc_test.py). The +25 % diaphragm
     connection force (ASCE 7-22 12.3.3.4) is a design requirement for the slab-to-beam / collector connections (rebar report).
  5. stair-landing corbel eccentricity: SuperDead point MOMENT about global Y at the landing level on C2 (+) and C6 (-),
     M = P_D x e, e = column half width + 0.125 (bearing centre from the face)
  8. elevator hook beam BH 25x40 under the penthouse slab on Y 14.65 between the new Story5 B31 (X 0) and B33 (X 2.3825), pinned ends
     (M3 released, torsion released at J), Sway Ordinary; hook 25 kN at (1.45, 14.65) moved from B31 / B33 to BH (mass unchanged:
     same diaphragm, joint masses at the B31 / B33 ends kept)
  4 (gap 80 mm), 6 (3-leg hoops B38 / B10 / B12), 7 (parking 16phi20 kept), 9 (sleeves phi125) : no model change (drawings / schedule)
Writes r6b_build_summary.json, geom_Rev6b.json, log_r6b_build.txt"""
import sys, os, json, shutil, math
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
SRC6A = os.path.join(HERE, "Merage3_Rev6a.EDB")
BAK = os.path.join(HERE, "_backup", "Merage3_Rev6a_before_T46.EDB")
EDB6B = os.path.join(HERE, "Merage3_Rev6b.EDB")
ECC = 0.0585
S = {}
e = None
try:
    if not os.path.exists(BAK):
        shutil.copy2(SRC6A, BAK)
    shutil.copy2(BAK, EDB6B)
    for ext in (".$et", ".ebk", ".msh", ".ico", ".EDB.tlog", ".Y_"):
        pth = os.path.join(HERE, "Merage3_Rev6b" + ext)
        if os.path.exists(pth):
            os.remove(pth)
    p("fresh copy", BAK, "->", EDB6B)
    e, m = connect(EDB6B); m.SetModelIsLocked(False)
    G6A = json.load(open(os.path.join(HERE, "geom_Rev6a.json"), encoding="utf-8"))
    newlab = G6A["new_objects_project_labels"]
    pts, frs, ars = geometry(m)
    for u, v in newlab["frames"].items():
        frs[u]["label_etabs"] = frs[u]["label"]; frs[u]["label"] = v["label"]
    # 1. Story2 columns 16T18
    base, new = "C50X50/16T16", "C50X50/16T18"
    rect = m.PropFrame.GetRectangle(base); rb = m.PropFrame.GetRebarColumn(base)
    p("SetRectangle", m.PropFrame.SetRectangle(new, rect[1], rect[2], rect[3]))
    args = list(rb[:-1]); args[8] = "18"
    p("SetRebarColumn", m.PropFrame.SetRebarColumn(new, *args), m.PropFrame.GetRebarColumn(new))
    m.PropFrame.SetModifiers(new, list(m.PropFrame.GetModifiers(base)[0]))
    s2 = [f for f, v in frs.items() if v["kind"] == "column" and v["story"] == "Story2"]
    assert len(s2) == 12 and all(frs[f]["sec"] == base for f in s2)
    for f in s2:
        assert m.FrameObj.SetSection(f, new, 0) == 0
    S["story2_columns"] = sorted(frs[f]["label"] for f in s2)
    p("1. Story2 ->", new, S["story2_columns"])
    # 2. Story5 cantilevers
    c5 = [f for f, v in frs.items() if v["story"] == "Story5" and v["label"] in ("B3", "B5") and v["kind"] == "beam"]
    assert sorted(c5) == ["146", "147"], c5
    for f in c5:
        mods = list(m.FrameObj.GetModifiers(f)[0]); mods[3] = 0.1
        assert m.FrameObj.SetModifiers(f, mods)[-1] == 0
        p("  overwrite", f, m.DesignConcrete.ACI318_19.SetOverwrite(f, 1, 3, 0), m.DesignConcrete.ACI318_19.GetOverwrite(f, 1))
    S["story5_cantilevers"] = c5
    # 3. eccentricity
    db = m.DatabaseTables
    key = "Load Pattern Definitions - Auto Seismic - User Coefficient"
    before = table(m, key)
    rr = db.GetTableForEditingArray(key, "")
    ver, fields, n, data = rr[0], list(rr[1]), rr[2], list(rr[3])
    nf = len(fields); rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
    ie = fields.index("EccRatio")
    for r_ in rows:
        r_[ie] = "0/0585"
    fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
    flat = [v if v is not None else "" for r_ in rows for v in r_]
    p("  Set", db.SetTableForEditingArray(key, ver, list(fi[3]), n, flat)[-1])
    res = db.ApplyEditedTables(True); p("  Apply", res[0], res[1], res[2], res[3])
    after = table(m, key)
    flags = ["XDir", "XDirPlusE", "XDirMinusE", "YDir", "YDirPlusE", "YDirMinusE", "C", "K", "TopStory", "BotStory"]
    assert (before[flags].astype(str).values == after[flags].astype(str).values).all(), (before, after)
    assert (abs(after["EccRatio"] - ECC) < 1e-6).all(), after
    S["auto_seismic_after"] = after.to_dict("records")
    p("3. auto seismic\n", after.to_string())
    # 5. corbel eccentricity moments
    rows5 = []
    for f, v in frs.items():
        if v["kind"] == "column" and v["label"] in ("C2", "C6") and v["story"] != "Story5":
            r = m.FrameObj.GetLoadPoint(f)
            sd = [(r[6][k], r[8][k]) for k in range(r[0]) if r[2][k] == "SuperDead" and r[3][k] == 1]
            assert len(sd) == 1, (f, sd)
            rel, P = sd[0]
            half = int(v["sec"][1:3]) / 200.0
            ecc = half + 0.125
            M = P * ecc * (1 if v["label"] == "C2" else -1)
            assert m.FrameObj.SetLoadPoint(f, "SuperDead", 2, 5, rel, M, "Global", True, False, 0) == 0
            rows5.append({"Story": v["story"], "Column": v["label"], "UniqueName": f, "rel": round(rel, 4), "P_D": P, "e_m": ecc, "My_kNm": round(M, 2)})
    S["corbel_moments"] = rows5
    p("5. corbel moments", rows5)
    # 8. hook beam
    bw = m.PropFrame.GetRectangle("BW40xH40"); rbb = m.PropFrame.GetRebarBeam("BW40xH40")
    p("  BW25xH40", m.PropFrame.SetRectangle("BW25xH40", bw[1], 0.40, 0.25),
      m.PropFrame.SetRebarBeam("BW25xH40", rbb[0], rbb[1], rbb[2], rbb[3], rbb[4], rbb[5], rbb[6], rbb[7]),
      m.PropFrame.SetModifiers("BW25xH40", list(m.PropFrame.GetModifiers("BW40xH40")[0])))
    n31 = [f for f, v in newlab["frames"].items() if v["label"] == "B31"][0]
    n33 = [f for f, v in newlab["frames"].items() if v["label"] == "B33"][0]
    for f in (n31, n33):
        r = m.FrameObj.GetLoadPoint(f)
        pl = [(r[2][k], r[8][k]) for k in range(r[0])]
        p("  point loads before", f, pl)
        assert len(pl) == 1 and pl[0][0] == "SuperDead"
        m.FrameObj.DeleteLoadPoint(f, "SuperDead", 0)
    Y = 14.65
    xb = 2.35 + (Y - 13.5) / (18.81 - 13.5) * 0.15
    qa = m.PointObj.AddCartesian(0.0, Y, 17.8, "", "")[0]; qb = m.PointObj.AddCartesian(xb, Y, 17.8, "", "")[0]
    r = m.FrameObj.AddByPoint(qa, qb, "", "BW25xH40", ""); fh = r[0]; assert r[-1] == 0
    ref = "57"
    ins = m.FrameObj.GetInsertionPoint(ref)
    m.FrameObj.SetInsertionPoint(fh, ins[0], ins[1], ins[2], list(ins[3]), list(ins[4]), ins[5])
    m.FrameObj.SetModifiers(fh, list(m.FrameObj.GetModifiers(ref)[0]))
    p("  releases", m.FrameObj.SetReleases(fh, [False, False, False, False, False, True], [False, False, False, True, False, True], [0] * 6, [0] * 6, 0))
    p("  overwrite BH", m.DesignConcrete.ACI318_19.SetOverwrite(fh, 1, 3, 0))
    t = 1.45 / xb
    assert m.FrameObj.SetLoadPoint(fh, "SuperDead", 1, 10, t, 25.0, "Global", True, False, 0) == 0
    S["hook_beam"] = {"UniqueName": fh, "label_etabs": m.FrameObj.GetLabelFromName(fh)[:2], "i": qa, "j": qb, "x_j": round(xb, 4), "y": Y, "rel_hook": round(t, 4)}
    p("8. hook beam", S["hook_beam"])
    pts, frs, ars = geometry(m)
    newlab["frames"][fh] = {"label": "BH", "story": "Story5"}
    newlab["points"][qa] = {"label": "BH-i"}; newlab["points"][qb] = {"label": "BH-j"}
    json.dump({"points": pts, "frames": frs, "areas": ars, "new_objects_project_labels": newlab},
              open(os.path.join(HERE, "geom_Rev6b.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    p("save", m.File.Save(EDB6B)); S["saved"] = True
except Exception:
    import traceback; p(traceback.format_exc())
json.dump(S, open(os.path.join(HERE, "r6b_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
finish("r6b_build")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
