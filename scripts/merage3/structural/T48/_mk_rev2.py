# -*- coding: utf-8 -*-
"""one-off: derive make_struct_Rev2.py / plot_Rev2.py (task 48: Rev6c, scale 1:50 on A1) from the Rev1 tools in T46"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, "..", "T46", "make_struct_Rev1.py"), encoding="utf-8").read()


def rep(a, b, count=None):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b) if count is None else s.replace(a, b, count)


rep('"""Merage3 - task 46 (2026-10-31): structural drawings Rev1 FOR APPROVAL from ETABS Rev6b and the Rev.10 levels.',
    '"""Merage3 - task 48 (2026-10-31): structural drawings Rev2 FOR APPROVAL from ETABS Rev6c, SCALE 1:50 (boss 2026-10-31).\n'
    'Same sheet layout as Rev1 (A3 frames at 1:100 = A1 frames at 1:50: plotted on A1 with 20 mm per metre).\n'
    'Boss orders: joists of the 7.5 m bay in Y, length 8 m, 3 tie beams per bay; stair-house joists in X (2.3); stair t = 0.20;\n'
    'elevator pit 2.00; hook 25 kN approved.\nRev1 header:')
rep('GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6b.json")', 'GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6c.json")')
rep('DES = os.path.join(HERE, "t46_design.json")', 'DES = os.path.join(HERE, "t48_design.json")')
rep('HC = os.path.join(HERE, "t46_hand_checks.json")', 'HC = os.path.join(HERE, "t48_hand_checks.json")')
rep('OUT_DWG = os.path.join(OUT_DIR, "Merage3_struct_Rev1.dwg")', 'OUT_DWG = os.path.join(OUT_DIR, "Merage3_struct_Rev2.dwg")')
rep('TMP = "C:/ZagrosTemp/rev1"', 'TMP = "C:/ZagrosTemp/rev2"')
rep('SRC = "Source: ETABS Merage3_Rev6b.EDB (task 46), ACI 318-19, 51 A22 combos, Ax = 1.17 - read only; levels arch Rev.10"',
    'SRC = "Source: ETABS Merage3_Rev6c.EDB (task 48), ACI 318-19, 51 A22 combos, Ax = 1.17 - read only; levels arch Rev.10/11"')
rep('ویرایش: Rev1', 'ویرایش: Rev2')
rep('"Merage3_struct_Rev1.dxf"', '"Merage3_struct_Rev2.dxf"'); rep('"save_rev1.scr"', '"save_rev2.scr"')
rep('"Merage3_struct_Rev1_prev.dwg"', '"Merage3_struct_Rev2_prev.dwg"'); rep('"rev1_sheets.json"', '"rev2_sheets.json"')
rep("(task 46)", "(task 48)")
# every scale text 1:100 -> 1:50 (the T34 patch strings too)
s = s.replace("1:100", "1:50")
# stair t = 0.20
rep('st = hc["stair_waist_t250"]', 'st = hc["stair_waist_t200"]')
rep("    t = 0.25\n", "    t = 0.20\n")
rep('f"S1. Waist + landing slab t = 0.25 (boss); main bottom', 'f"S1. Waist + landing slab t = 0.20 (boss 2026-10-31); main bottom')
rep("top φ12@200 over L/4 at both ends.", "top φ10@200 over L/4 at both ends.")
rep('"    WARNING - t = 0.25 < l/20 = 0.30 (ACI table 7.3.1.1, simply supported); camber / t = 0.30 / mid support: boss decision.",',
    '"    WARNING - t = 0.20 < l/20 = 0.30 (ACI table 7.3.1.1, simply supported): reported to the boss, no change made.",')
rep("S3. Landing beam 30x40 between C2 and C6: 3φ16 top + 3φ16 bottom, closed φ10@100; it rests on corbels only (no bars into the columns).",
    "S3. Landing beam 30x40 between C2 and C6: 3φ16 top + 3φ16 bottom, closed φ10@100 (Mu 36 kN.m with t = 0.20); rests on corbels only.")
# hook approved, pit
rep('sh.T("hook 25 kN (supplier)"', 'sh.T("hook 25 kN (approved)"')
rep('"Hook: cast-in eye bolt or embedded plate per the elevator supplier; hanger hoops 2φ10 on each side of the hook point.",',
    '"Hook 25 kN APPROVED by the boss; cast-in eye bolt / embedded plate per the supplier; hanger hoops 2φ10 each side.",\n'
    '        "Elevator pit depth 2.00 m below the parking FFL +0.08 (pit floor about -1.92): part of the foundation (SAFE, pending).",')
rep('"9. Foundation / starter bars: by SAFE (pending)."], h=0.13, step=0.26, head="COLUMN NOTES")',
    '"9. Foundation / starter bars: by SAFE (pending). Elevator pit 2.00 m deep (floor ~ -1.92) next to C16 / C18 (boss)."], h=0.13, step=0.26, head="COLUMN NOTES")')
# framing: joists of the 7.5 m bay in Y with tie beams; drawn after the T34 framing sheet
rep('''def framing(doc, geom, des, i, stories, no, tfa, ten, nl, roof=False):
    return M.framing_sheet(doc, geom, des, i, stories, no, tfa, ten, nl, roof)''', '''_joist_x = M.joist


def _joist_skip_y(sh, X0, X1, Y, tag, h=0.25):
    """T34 draws every panel with X joists; the 7.5 m bay panels F1 / F4 are drawn in Y by bay_75() instead"""
    if tag in ("F1", "F4"):
        return
    _joist_x(sh, X0, X1, Y, tag, h)


M.joist = _joist_skip_y


def joist_y(sh, X, Y0, Y1, tag):
    sh.lineE("S-SLAB", X, Y0, X, Y1)
    for Y in (Y0, Y1):
        sh.lineE("S-SLAB", X - 0.12, Y, X + 0.12, Y)
    for Y, d in ((Y0, 1), (Y1, -1)):
        sh.poly("S-SLAB", [sh.E(X, Y), sh.E(X - 0.07, Y + d * 0.18), sh.E(X + 0.07, Y + d * 0.18)])
    u, v = sh.E(X, (Y0 + Y1) / 2)
    sh.T(tag, u, v + 0.10, 0.13, layer="S-SLAB", align=TA.BOTTOM_CENTER)


def bay_75(sh):
    """joists in Y over the 7.5 m bay (axis 1-2), length 8.00 back to back over the beams, 3 tie beams at L/4"""
    joist_y(sh, 1.10, 0.30, 7.20, "F1  joists Y, L = 8.00")
    joist_y(sh, 4.75, 0.30, 7.20, "F4  joists Y, L = 8.00")
    for Y in (1.875, 3.75, 5.625):
        for sgn in (-1, 1):
            sh.lineE("S-BEAM", 0.25, Y + sgn * 0.075, 6.90, Y + sgn * 0.075)
        u, v = sh.E(6.0, Y)
        sh.T("TB 15x31", u - 0.12, v, 0.11, layer="S-ANNO-IDEN", rot=90)
    u, v = sh.E(3.6, 3.75)
    sh.T("3 tie beams TB 15x31 at L/4 (Y 1.875 / 3.75 / 5.625): 2φ12 top + 2φ12 bottom, φ8@200", u + 0.55, v, 0.11, layer="S-ANNO-IDEN", rot=90)


def framing(doc, geom, des, i, stories, no, tfa, ten, nl, roof=False):
    sh = M.framing_sheet(doc, geom, des, i, stories, no, tfa, ten, nl, roof)
    bay_75(sh)
    return sh''')
rep('"5. Joist slabs (tirche): joists span in X; slab-to-beam dowels φ10@200 (+25% connection force, torsional irregularity).",',
    '"5. Joists: 7.5 m bay (axis 1-2) in Y, 8.00 long back to back over B10/B11 and B12/B13, 3 tie beams TB per bay (boss);",\n'
    '                "   bays 2-3 / 3-4 / cantilevers unchanged in X (question to the boss). Slab-to-beam dowels φ10@200 (+25%).",')
rep('"4. Stair-house roof (lower part): extended to axis 5 (task 43/44); columns C2, C6, C16, C17, C18, C19 40x40;",',
    '"4. Stair-house roof (lower part): ALL joists in X, span 2.3 (boss); extended to axis 5; columns C2, C6, C16, C17, C18, C19 40x40;",')
rep('"5. Reinforcement: S-105.",', '"5. Roof bay 1-2: joists in Y, 8.00, 3 tie beams TB (as floors). Reinforcement: S-105.",')
rep('"G6. Joist (tirche) slabs: joists span in X; slab-to-beam dowels φ10@200",',
    '"G6. Joists: 7.5 m bay in Y (8.00, 3 TB), stair house in X; dowels φ10@200",')
open(os.path.join(HERE, "make_struct_Rev2.py"), "w", encoding="utf-8").write(s)
pl = open(os.path.join(HERE, "..", "T46", "plot_Rev1.py"), encoding="utf-8").read()
for a, b in (('"""Plot Merage3_struct_Rev1.dwg (A3 1:100', '"""Plot Merage3_struct_Rev2.dwg (A1 1:50'),
             ("from make_struct_Rev1 import", "from make_struct_Rev2 import"),
             ('A3 = "ISO full bleed A3 (420.00 x 297.00 MM)"', 'A3 = "ISO full bleed A1 (841.00 x 594.00 MM)"'),
             ('PNG = "C:/ZagrosTemp/rev1"', 'PNG = "C:/ZagrosTemp/rev2"'), ('"rev1_sheets.json"', '"rev2_sheets.json"'),
             ('os.path.join(OUT_DIR, "pdf", f"Merage3_struct_Rev1_{name}_{NAMES[name]}.pdf")', 'os.path.join(OUT_DIR, "pdf_Rev2", f"Merage3_struct_Rev2_{name}_{NAMES[name]}.pdf")'),
             ('scale="10:1"', 'scale="20:1"'), ('"Merage3_struct_Rev1.pdf"', '"Merage3_struct_Rev2.pdf"')):
    assert a in pl, a
    pl = pl.replace(a, b)
open(os.path.join(HERE, "plot_Rev2.py"), "w", encoding="utf-8").write(pl)
print("ok")
