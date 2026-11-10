# -*- coding: utf-8 -*-
"""Task 42 workaround for an ETABS 19 API defect: after Story.SetHeight the deck (area) objects report the new
elevations but the analysis mesh keeps them at the OLD elevations (shells connected to the columns at mid-height ->
model ~3x too stiff). Remedy: delete and re-add every area object on the same point names with the same unique name,
restoring property, local axis, diaphragm, edge constraint, opening flag, uniform loads and modifiers."""
from r5_common import p


def recreate_areas(m):
    log = []
    names = list(m.AreaObj.GetNameList()[1])
    data = {}
    for a in names:
        n, pts, _ = m.AreaObj.GetPoints(a)
        r = m.AreaObj.GetLoadUniform(a)
        data[a] = {"pts": list(pts), "prop": m.AreaObj.GetProperty(a)[0], "ax": m.AreaObj.GetLocalAxes(a)[0],
                   "dia": m.AreaObj.GetDiaphragm(a)[0], "edge": m.AreaObj.GetEdgeConstraint(a)[0], "op": m.AreaObj.GetOpening(a)[0],
                   "mod": list(m.AreaObj.GetModifiers(a)[0]), "label": m.AreaObj.GetLabelFromName(a)[:2],
                   "loads": [(r[2][k], r[3][k], r[4][k], r[5][k]) for k in range(r[0])]}   # pattern, csys, dir, value
    for a in names:                     # keep area-only points (e.g. opening corners) alive through the delete
        for q in data[a]["pts"]:
            m.PointObj.SetSpecialPoint(q, True)
    for a in names:
        assert m.AreaObj.Delete(a, 0) == 0, a
    for a in names:
        d = data[a]
        prop = d["prop"] if d["prop"] and d["prop"] != "None" else "TIRCHEH"   # openings: added with a deck prop, then flagged
        r = m.AreaObj.AddByPoint(len(d["pts"]), d["pts"], "", prop, a)
        nm = r[1] if isinstance(r, (list, tuple)) else None
        assert nm == a, (a, r)
        if d["op"]:
            m.AreaObj.SetOpening(a, True, 0)
        m.AreaObj.SetLocalAxes(a, d["ax"], 0)
        if d["dia"] and d["dia"] != "None":
            m.AreaObj.SetDiaphragm(a, d["dia"])
        m.AreaObj.SetEdgeConstraint(a, d["edge"], 0)
        if any(abs(x - 1) > 1e-9 for x in d["mod"]):
            m.AreaObj.SetModifiers(a, d["mod"], 0)
        for pat, cs, dr, val in d["loads"]:
            assert m.AreaObj.SetLoadUniform(a, pat, val, dr, False, cs, 0) == 0, (a, pat)
        log.append((a, d["label"], m.AreaObj.GetLabelFromName(a)[:2], prop, d["op"], len(d["loads"])))
    for x in log:
        p("  area re-added", x)
    return data, log
