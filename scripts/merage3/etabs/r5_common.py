# -*- coding: utf-8 -*-
"""Shared helpers for the Merage3 Rev.5 ETABS model (all files live in Merage3\\ETABS\\)."""
import os, sys, math, json
import comtypes.client
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EDB = os.path.join(HERE, "Merage3_Rev5.EDB")
ARCH = os.path.join(HERE, "..", "arch", "Merage3_arch_plan_BASIS_geometry.json")
EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
G = 9.80665
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def connect(path=EDB):
    h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
    e = None
    try:
        e = h.GetObject("CSI.ETABS.API.ETABSObject")
        m = e.SapModel
        m.GetModelFilename()
        p("attached to running ETABS:", m.GetModelFilename())
    except Exception:
        e = h.CreateObject(EXE)
        p("ApplicationStart", e.ApplicationStart())
        m = e.SapModel
    cur = m.GetModelFilename() or ""
    if os.path.normcase(cur) != os.path.normcase(path):
        assert os.path.basename(path).lower() != "merage3.edb"
        r = m.File.OpenFile(path)
        p("OpenFile", path, r)
        assert r == 0
    assert os.path.normcase(m.GetModelFilename()) == os.path.normcase(path)
    m.SetPresentUnits(6)  # kN, m, C
    return e, m


def num(df):
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except (ValueError, TypeError):
            try:
                df[c] = pd.to_numeric(df[c].str.replace("/", ".", regex=False))
            except (ValueError, TypeError, AttributeError):
                pass
    return df


def table(m, key):
    try:
        r = m.DatabaseTables.GetTableForDisplayArray(key, [], "All", 0, [], 0, [])
        f, n, d = list(r[2]), r[3], list(r[4])
        if not n or not f:
            return pd.DataFrame()
        nf = len(f)
        return num(pd.DataFrame([d[i * nf:(i + 1) * nf] for i in range(n)], columns=f)
                   .rename(columns={"OutputCase": "Output Case"}))
    except Exception as ex:
        p("  ! table", key, ex)
        return pd.DataFrame()


def geometry(m):
    """frames / points / areas with labels and coordinates (m)."""
    pts = {}
    for q in m.PointObj.GetNameList()[1]:
        x, y, z, _ = m.PointObj.GetCoordCartesian(q)
        lab, st, _ = m.PointObj.GetLabelFromName(q)
        pts[q] = {"label": lab, "story": st, "x": round(x, 4), "y": round(y, 4), "z": round(z, 4)}
    frs = {}
    for f in m.FrameObj.GetNameList()[1]:
        i, j, _ = m.FrameObj.GetPoints(f)
        lab, st, _ = m.FrameObj.GetLabelFromName(f)
        kind = "beam" if m.FrameObj.GetDesignOrientation(f)[0] == 2 else "column"
        a, b = pts[i], pts[j]
        frs[f] = {"label": lab, "story": st, "kind": kind, "i": i, "j": j, "sec": m.FrameObj.GetSection(f)[0],
                  "xi": a["x"], "yi": a["y"], "xj": b["x"], "yj": b["y"], "zi": a["z"], "zj": b["z"],
                  "L": round(math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"])), 4)}
    ars = {}
    for a in m.AreaObj.GetNameList()[1]:
        n, ap, _ = m.AreaObj.GetPoints(a)
        lab, st, _ = m.AreaObj.GetLabelFromName(a)
        xy = [(pts[q]["x"], pts[q]["y"]) for q in ap]
        A = abs(sum(xy[k][0] * xy[k - 1][1] - xy[k - 1][0] * xy[k][1] for k in range(n))) / 2
        ars[a] = {"label": lab, "story": st, "pts": list(ap), "xy": xy, "A": round(A, 4), "prop": m.AreaObj.GetProperty(a)[0]}
    # ETABS 19 re-labels every object whose plan position changes (EditGeneral.Move or point-table edit; labels are
    # not importable). Keep the project labels (Run 1-3, architect JSON) by unique name: "label" = old label,
    # "label_etabs" = the label ETABS shows now.
    gb = os.path.join(HERE, "geom_before.json")
    if os.path.exists(gb):
        old = json.load(open(gb, encoding="utf-8"))
        for d, k in ((pts, "points"), (frs, "frames"), (ars, "areas")):
            for u, v in d.items():
                v["label_etabs"] = v["label"]
                if u in old[k]:
                    v["label"] = old[k][u]["label"]
    return pts, frs, ars


def finish(name):
    open(os.path.join(HERE, f"log_{name}.txt"), "w", encoding="utf-8").write("\n".join(LOG))
