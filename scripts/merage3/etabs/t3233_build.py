# -*- coding: utf-8 -*-
"""Merage3 Rev.5 -> tasks 32 + 33 (structural engineer, 2026-10-23).  python t3233_build.py
Backup before running: _backup\\Merage3_Rev5_before_T32-33.EDB
  33. new X grid line "B'" at X = 2.50 (copy of grid B row); C19 line (C19 all levels + B5 cantilever tip, X = 2.507)
      moved -0.007 in X so the column sits exactly on the new grid (EditGeneral.Move).
  32. loads rebuilt from arch JSON Rev.6 with the Rev.5 build functions: W24 (15 cm, net 11.238 m2) now a line load
      on B32 (Story1..3); W24 removed from the equivalent partition of slabs F1/F4/F12/F13/F14 (0.968 -> 0.743 kN/m2).
Model is saved only if every check passes. Mass is rebuilt by r5_run.py.
Writes: wall_loads_Rev5.csv, slab_wall_point_loads_Rev5.csv, partition_Rev5.json (overwritten, old in _backup),
        geom_after_T32-33.json, t3233_build_summary.json, log_t3233_build.txt
"""
import sys, os, json, csv
from r5_common import *
from r5_build import wall_rows, slab_parallel_point_loads, partition, apply_loads, TOL

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
X_OLD, X_NEW, GRID_ID = 2.507, 2.50, "B'"


def add_grid(m):
    key = "Grid Definitions - Grid Lines"
    db = m.DatabaseTables
    r = db.GetTableForEditingArray(key, "")
    ver, fields, n, data = r[0], list(r[1]), r[2], list(r[3])
    nf = len(fields)
    p("  fields", fields)
    rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
    for row in rows:
        p("   ", row)
    iid, iord, ilt = fields.index("ID"), fields.index("Ordinate"), fields.index("LineType")
    if any(row[iid] == GRID_ID for row in rows):
        p("  grid already present"); return True
    src = [row for row in rows if row[ilt].startswith("X") and row[iid] == "B"]
    assert len(src) == 1, src
    new = list(src[0]); new[iid] = GRID_ID; new[iord] = f"{X_NEW:.2f}".replace(".", "/")
    k = rows.index(src[0]) + 1
    rows.insert(k, new)
    fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
    fl = list(fi[3])
    assert len(fl) == nf
    flat = [v if v is not None else "" for row in rows for v in row]
    p("  SetTableForEditingArray", db.SetTableForEditingArray(key, ver, fl, n + 1, flat)[-1])
    res = db.ApplyEditedTables(True)
    p("  ApplyEditedTables fatal/err/warn/info", res[0], res[1], res[2], res[3])
    if res[1] or res[0]:
        p("  log:", str(res[4]).replace("\r\n", " | ")[:1500])
    gl = table(m, key)
    p(gl.to_string())
    ok = len(gl) == n + 1 and abs(float(gl[gl.ID.astype(str) == GRID_ID]["Ordinate"].iloc[0]) - X_NEW) < 1e-6
    for gid, v in (("A", 0.0), ("B", 2.35), ("C", 7.15), ("1", 0.0), ("2", 7.5), ("3", 13.5), ("4", 18.81), ("5", 20.01)):
        s = gl[gl.ID.astype(str) == gid]
        ok = ok and len(s) == 1 and abs(float(s["Ordinate"].iloc[0]) - v) < 1e-6
    p("  CHECK grid:", "OK" if ok else "FAILED")
    return ok


def move_c19(m):
    pts, frs, ars = geometry(m)
    sel = [q for q, v in pts.items() if abs(v["x"] - X_OLD) < TOL]
    p("  joints at X=2.507:", [(q, pts[q]["story"], pts[q]["y"]) for q in sel])
    assert all(abs(pts[q]["y"] - 18.81) < TOL or abs(pts[q]["y"] - 20.01) < TOL for q in sel)
    m.SelectObj.ClearSelection()
    for q in sel:
        m.PointObj.SetSelected(q, True)
    p(f"  move {X_NEW - X_OLD:+.3f} in X: {len(sel)} joints ->", m.EditGeneral.Move(X_NEW - X_OLD, 0, 0))
    m.SelectObj.ClearSelection()
    pts, frs, ars = geometry(m)
    c19 = [(v["story"], v["label_etabs"], v["xi"], v["yi"], v["xj"]) for v in frs.values() if v["label"] == "C19"]
    p("  C19:", c19)
    for lab in ("B33", "B5", "B38", "B39", "B2"):
        p("  ", lab, [(v["story"], v["label_etabs"], (v["xi"], v["yi"]), (v["xj"], v["yj"]), v["L"]) for v in frs.values() if v["label"] == lab and v["story"] == "Story1"])
    left = [q for q, v in pts.items() if abs(v["x"] - X_OLD) < TOL]
    ok = not left and len(c19) == 4 and all(abs(x - X_NEW) < TOL and abs(xj - X_NEW) < TOL and abs(y - 18.81) < TOL for _, _, x, y, xj in c19)
    p("  CHECK C19 on grid B':", "OK" if ok else "FAILED")
    return ok, len(sel)


if __name__ == "__main__":
    S = {}
    try:
        e, m = connect()
        p("reopen from disk:", m.File.OpenFile(EDB)); m.SetPresentUnits(6)
        m.SetModelIsLocked(False)
        arch = json.load(open(ARCH, encoding="utf-8"))
        assert arch["rev"] == "Rev.6", arch["rev"]
        p("T33a grid"); S["grid_ok"] = add_grid(m)
        assert S["grid_ok"], "grid check failed -> STOP (not saved)"
        p("T33b C19 to X=2.50"); S["c19_ok"], S["moved"] = move_c19(m)
        assert S["c19_ok"], "C19 check failed -> STOP (not saved)"
        pts, frs, ars = geometry(m)
        json.dump({"points": pts, "frames": frs, "areas": ars}, open(os.path.join(HERE, "geom_after_T32-33.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        p("T32 loads (arch JSON Rev.6)")
        rows = wall_rows(arch, frs)
        pls = slab_parallel_point_loads(arch, frs)
        part = partition(arch, ars)
        assert "W24" not in part["walls"]
        p("  partition", json.dumps(part, ensure_ascii=False))
        for r in rows:
            if r["Beam"] in ("B32", "B12", "B33", "B38", "B39", "B5") and r["Story"] in ("Story1", "Story4"):
                p("  ", r)
        with open(os.path.join(HERE, "wall_loads_Rev5.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
        with open(os.path.join(HERE, "slab_wall_point_loads_Rev5.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(pls[0])); wr.writeheader(); wr.writerows(pls)
        json.dump(part, open(os.path.join(HERE, "partition_Rev5.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        apply_loads(m, frs, ars, rows, pls, part)
        # read back B32 and F12 loads
        for st in ("Story1", "Story2", "Story3", "Story4"):
            f = [u for u, v in frs.items() if v["story"] == st and v["label"] == "B32" and v["kind"] == "beam"][0]
            r = m.FrameObj.GetLoadDistributed(f)
            rp = m.FrameObj.GetLoadPoint(f)
            a = [u for u, v in ars.items() if v["story"] == st and v["label"] == "F12"][0]
            ra = m.AreaObj.GetLoadUniform(a)
            S[f"{st} B32 ({f})"] = {"line": [(r[2][k], r[10][k]) for k in range(r[0])], "point": [(rp[2][k], rp[6][k], rp[8][k]) for k in range(rp[0])],
                                    "F12": [(ra[2][k], ra[5][k]) for k in range(ra[0])]}
            p("  readback", st, S[f"{st} B32 ({f})"])
        sums = {}
        for r in rows:
            sums[r["Story"]] = sums.get(r["Story"], 0.0) + r["Total_kN/m"] * r["L_m"]
        S["line_load_totals_kN"] = {k: round(v, 1) for k, v in sums.items()}
        S["partition"] = part
        p("  totals", S["line_load_totals_kN"])
        p("save", m.File.Save(EDB))
        S["saved"] = True
    except Exception:
        import traceback
        p(traceback.format_exc())
    json.dump(S, open(os.path.join(HERE, "t3233_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    finish("t3233_build")
    os._exit(0)
