# -*- coding: utf-8 -*-
"""Rev.8 (task 39) sheet builders used by make_arch_rev8.py:

    car_block       block CAR_SEDAN (top view of a sedan 1.80 x 4.50, front = +x), layer 0 / BYBLOCK
    copy_typical    floors 2 and 3 = copies of the floor-1 (typical) drawing, shifted in model space
    floor_sheet     titles, level, floor-specific notes, schedule title, frame + legend of one typical floor
    roof_sheet      A-105 roof plan: parapet, stair house, elevator overrun, ducts, drains, slopes, door, levels
    add_layouts     one named paper-space layout per sheet (A3, one locked viewport at 1:100)

M = the make_arch_rev8 module (set by it before use: helpers Sheet, fa, sheet_frame, legend, union_edges ...).
"""
import math

from ezdxf.enums import TextEntityAlignment as TA

M = None

A3_MEDIA = "ISO_full_bleed_A3_(420.00_x_297.00_MM)"


# ---------------------------------------------------------------- car
def car_block(doc):
    """Sedan, top view, 4.50 x 1.80 (front = +x), entities on layer 0 with BYBLOCK colour / lineweight so the
    INSERT on A-PRKG-CARS prints grey 0.09."""
    if "CAR_SEDAN" in doc.blocks:
        return
    b = doc.blocks.new("CAR_SEDAN", base_point=(0, 0), dxfattribs={"description": "Sedan car 4.50 x 1.80, top view, front +x"})
    at = {"layer": "0", "color": 0, "lineweight": -2}
    L2, W2, rf, rr = 2.25, 0.90, 0.38, 0.28
    q = math.tan(math.radians(22.5))                 # bulge of a 90 deg arc
    body = [(-L2 + rr, -W2, 0), (L2 - rf, -W2, q), (L2, -W2 + rf, 0), (L2, W2 - rf, q), (L2 - rf, W2, 0),
            (-L2 + rr, W2, q), (-L2, W2 - rr, 0), (-L2, -W2 + rr, q)]
    b.add_lwpolyline(body, format="xyb", close=True, dxfattribs=at)
    # windshield (front glass) and rear glass
    b.add_lwpolyline([(0.45, -0.66, 0), (1.08, -0.77, 0.10), (1.08, 0.77, 0), (0.45, 0.66, 0.06)], format="xyb", close=True, dxfattribs=at)
    b.add_lwpolyline([(-1.05, 0.66, 0), (-1.52, 0.74, 0.08), (-1.52, -0.74, 0), (-1.05, -0.66, 0.05)], format="xyb", close=True, dxfattribs=at)
    # roof sides, side glass lines
    for s in (1, -1):
        b.add_line((-1.05, s * 0.66), (0.45, s * 0.66), dxfattribs=at)
        b.add_line((-1.52, s * 0.80), (1.08, s * 0.80), dxfattribs=at)
        b.add_line((1.30, s * 0.42), (2.05, s * 0.36), dxfattribs=at)           # bonnet creases
        b.add_lwpolyline([(0.92, s * 0.90), (0.84, s * 1.03), (0.70, s * 1.03), (0.72, s * 0.90)], dxfattribs=at)  # mirrors
        b.add_line((2.02, s * 0.80), (2.22, s * 0.52), dxfattribs=at)           # headlights
        b.add_line((-2.17, s * 0.78), (-2.17, s * 0.50), dxfattribs=at)         # tail lights
    b.add_line((-1.95, -0.70), (-1.95, 0.70), dxfattribs=at)                     # boot lid


# ---------------------------------------------------------------- typical floors
def copy_typical(doc, offsets):
    msp = doc.modelspace()
    ents = list(msp)
    n = 0
    for dx in offsets:
        for e in ents:
            c = e.copy()
            c.translate(dx, 0, 0)
            msp.add_entity(c)
            n += 1
    return n


def floor_sheet(doc, dx, sheet_no, en, fa_name, lev, stall):
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    msp = doc.modelspace()
    old = fa("جدول در و پنجره - طبقات تیپ ۱ تا ۳ - ") + REV
    for e in msp.query("TEXT"):
        if e.dxf.text == old and -29.5 + dx < e.dxf.insert.x < 12.5 + dx:
            e.dxf.text = fa(f"جدول در و پنجره - {fa_name} - ") + REV
    # T40: lev = TOS (structural top of slab, from the top of foundation +-0.00); FFL = TOS + 0.08
    ffl = lev + 0.08
    nxt = {3.50: "TOS +6.40 (FLOOR 2, A-103)", 6.40: "TOS +9.30 (FLOOR 3, A-104)", 9.30: "TOS +12.20 (ROOF, A-105)"}[lev]
    below = {3.50: "parking FFL +0.08 on the foundation top +-0.00 (A-101)", 6.40: "floor 1 TOS +3.50 (A-102)",
             9.30: "floor 2 TOS +6.40 (A-103)"}[lev]
    special = {
        3.50: ["14. FLOOR 1 (first floor over the parking): ground stair 20 x 0.175 arrives at this landing (A-101). The ducts START at",
               "     this slab (not in the parking; pipes under this slab to the facade / yard). Rear balcony above the yard passage."],
        6.40: ["14. FLOOR 2 (middle floor): plan identical to floors 1 and 3. Stair 20 x 0.145 up / down; ducts pass through the slab.",
               "     Rear balcony above the floor-1 balcony."],
        9.30: ["14. FLOOR 3 (top floor): stair continues to the roof stair house and roof door DR1 (A-105). Elevator top stop FFL +9.38,",
               "     overrun above the roof. Ducts end in vent caps on the roof. Ceiling = roof slab (thermal insulation on the roof, Mobhas 19)."],
    }[lev]
    y = -4.95
    sh.text_uv("FLOOR-SPECIFIC NOTES (" + sheet_no + ")", -5.3 + dx, y + 0.35, 0.18, align=TA.MIDDLE_LEFT, width=0.85)
    for s in [f"12. LEVELS (+-0.00 = top of foundation): this floor TOS {lev:+.2f} (structural), FFL {ffl:+.2f}. Below: {below}.",
              f"     Above: {nxt}. Storey 2.90; beams 0.50: u/s beam {lev + 2.40:+.2f} = FFL+2.32; u/s slab = FFL+2.51.",
              f"13. Parking stall of this unit: {stall} (A-101). One dwelling unit per floor."] + special:
        sh.text_uv(s, -5.3 + dx, y, 0.15, align=TA.MIDDLE_LEFT, width=0.8)
        y -= 0.27
    sh.level(f"FFL {ffl:+.2f} (TOS {lev:+.2f})", 2.72, 12.05, h=0.12)
    sh.text("واحد " + fa_name, 5.6, 16.4, 0.20, farsi=True, rot=0.0)
    u_min, u_max, v_max = -20.254, 0.25, 7.40
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa(f"پیش نویس - پلان معماری {fa_name}") + " - " + REV,
                  f"{en} PLAN  -  TOS {lev:+.2f} / FFL {ffl:+.2f}  -  {REV} DRAFT  -  1:100  -  DIMENSIONS IN METRES", sheet_no,
                  f"{REV} DRAFT (T40 levels from the foundation top): {en.lower()} = typical geometry Rev.6 FINAL + grid B' / C19 2.500. SOURCE: memary500 BASIS PDF",
                  (u_min + u_max) / 2 + dx, v_max)
    M.legend(sh, 4.6 + dx, 12.6)
    return sh


# ---------------------------------------------------------------- roof
COL40 = [(0.0, 7.5016), (2.3486, 7.5016), (0.0, 13.5032), (2.3486, 13.5032)]       # stair-house columns 40x40 (T34)
RW = [  # roof walls cut at ~+13.2: parapets 20 cm h 1.20 (T40), stair house 20 cm, elevator overrun
    (-0.25, -0.05, -0.25, 20.254, "R-PA", 20, "parapet / stair-house wall on axis A (boundary)"),
    (7.20, 7.40, -0.25, 20.254, "R-PC", 20, "parapet axis C (boundary)"),
    (-0.05, 7.20, -0.25, -0.05, "R-P1", 20, "parapet front (axis 1)"),
    (-0.05, 7.20, 20.054, 20.254, "R-P5", 20, "parapet rear (balcony edge, axis 5)"),
    (-0.05, 2.45, 7.55, 7.75, "SH-2", 20, "stair house front wall (axis 2 side)"),
    (2.25, 2.45, 7.55, 13.604, "SH-B", 20, "stair house wall to the roof (B side, on W24 / beam line), door DR1"),
    (-0.05, 2.60, 13.604, 13.754, "OV-F", 15, "stair house / elevator overrun (W19 line)"),
    (2.45, 2.60, 13.604, 15.703, "OV-B", 15, "elevator overrun side (W18 line)"),
    (-0.05, 2.60, 15.553, 15.703, "OV-R", 15, "elevator overrun back (W17 line)"),
    (0.349, 0.449, 13.754, 15.553, "OV-D", 10, "shaft / duct D-1 (W20 line)"),
]
ROPEN = [("DR1", "door", 2.25, 2.45, 12.30, 13.20)]
DRAINS = [("RD1", 6.80, 0.30), ("RD2", 6.80, 11.00), ("RD3", 6.80, 19.70), ("RD4", 0.40, 0.30), ("RD5", 0.40, 19.70)]
RIDGES = [(3.60, -0.05, 3.60, 7.55), (3.60, 5.50, 7.20, 5.50), (2.45, 7.55, 3.60, 7.55), (2.60, 15.703, 7.20, 15.703),
          (2.60, 15.703, 2.60, 20.054)]
SLOPES = [((5.40, 3.00), "RD1"), ((1.90, 4.20), "RD4"), ((4.60, 7.90), "RD2"), ((4.60, 14.40), "RD2"), ((4.70, 17.90), "RD3"),
          ((1.40, 17.60), "RD5")]
ROOF = dict(   # T40: all levels from the top of foundation +-0.00; TOS = structural top of slab
    slab_top=12.20, finish_at_drains=12.32, finish_at_ridges=12.44, landing_FFL=12.28,
    parapet_thick=0.20, parapet_h_from_TOS=1.20, parapet_top=13.40, coping_top=13.45,
    parapet_guard_above_finish="1.08 (+0.05 coping = 1.13) at the low line +12.32; ~0.96-1.01 where ridges reach the parapet",
    stair_house_columns=2.90, stair_house_beams=0.40, stair_house_roof=15.10, stair_house_us_beam=14.70,
    stair_house_parapet=0.20, stair_house_parapet_thick=0.20, stair_house_parapet_top=15.30,
    overrun_roof=13.40, overrun_note="assumption: overhead 3.62 (u/s beam +13.00 - top stop FFL +9.38); supplier to confirm",
    door_DR1="0.90 x 2.10, sill +12.53 (0.25 step from the landing FFL +12.28), head +14.63 < u/s beam +14.70",
    drains="RD1-RD5 dia 100 with leaf guard, catchments ~22-34 m2 each, slope 2%",
    buildup="slope screed 2% (0.03-0.15) + XPS 0.06 (Mobhas 19) + 2 layers bituminous membrane, upturn 0.30 on parapets + tiles",
)


def arrow(sh, layer, X1, Y1, X2, Y2, head=0.22):
    sh.line(layer, X1, Y1, X2, Y2)
    a = math.atan2(Y2 - Y1, X2 - X1)
    for d in (0.4, -0.4):
        sh.line(layer, X2, Y2, X2 - head * math.cos(a + d), Y2 - head * math.sin(a + d))


def roof_sheet(doc, dx, cols_all):
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    col_r = [(x - 0.20, x + 0.20, y - 0.20, y + 0.20) for x, y in COL40]
    rects = [r[:4] for r in RW]
    holes = [o[2:] for o in ROPEN]
    for X1, Y1, X2, Y2 in M.union_edges(rects, holes, col_r):
        sh.line("A-WALL", X1, Y1, X2, Y2)
    for r in col_r:
        sh.rect("A-COLS", *r)
        h = sh.msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
        h.paths.add_polyline_path([sh.E(r[0], r[2]), sh.E(r[1], r[2]), sh.E(r[1], r[3]), sh.E(r[0], r[3])], is_closed=True)
    # parapet coping (inner line of the 0.30 coping, 0.05 overhang) + membrane upturn note
    sh.rect("A-ROOF", -0.05 + 0.05, 7.20 - 0.05, -0.05 + 0.05, 20.054 - 0.05)
    # door DR1 (opens outward to the roof), threshold upstand
    sh.door(2.45, 13.20, (0, -1), (1, 0), 0.90)
    sh.tag("DR1", 2.95, 11.80)
    # stair (typical geometry, F3 +9.30 -> roof +12.20), all visible from the cut
    yh, ye = 8.958, 11.958
    for k in range(11):
        Yt = yh + 0.30 * k
        sh.line("A-STRS", -0.05, Yt, 1.05, Yt)
        sh.line("A-STRS", 1.15, Yt, 2.25, Yt)
    sh.line("A-STRS", 1.05, yh, 1.05, ye)
    sh.line("A-STRS", 1.15, yh, 1.15, ye)
    arrow(sh, "A-STRS", 0.50, ye + 0.20, 0.50, yh + 0.25, head=0.15)
    sh.msp.add_circle(sh.E(0.50, ye + 0.20), 0.04, dxfattribs={"layer": "A-STRS"})
    sh.text("DN", 0.50, ye + 0.45, 0.15, rot=0.0)
    sh.text("20 x 14.5 / 30 FROM FFL +9.38", 1.70, 10.45, 0.09, rot=0.0)
    sh.text("HALF LANDING FFL +10.83", 1.10, 8.35, 0.09, rot=90.0)
    sh.text("خرپشته", 1.80, 12.80, 0.20, farsi=True, rot=0.0)
    sh.text("STAIR HOUSE", 1.48, 12.80, 0.10, rot=0.0)
    sh.level("FFL +12.28 (TOS +12.20)", 1.00, 13.40, h=0.10)
    sh.text("STAIR-HOUSE ROOF TOS +15.10, CURB 0.20 x 0.20 TOP +15.30", 2.75, 10.60, 0.075, rot=0.0)
    # spout from the stair-house roof onto the main roof (B side)
    sh.rect("A-ROOF-DRAN", 2.45, 2.70, 8.20, 8.32)
    sh.text("SPOUT", 2.95, 8.26, 0.07, rot=0.0)
    # elevator overrun + duct D-1
    sh.line("A-ELEV", 0.449, 13.754, 2.449, 15.553)
    sh.line("A-ELEV", 0.449, 15.553, 2.449, 13.754)
    sh.text("ELEV. OVERRUN", 1.75, 14.65, 0.09, rot=0.0)
    sh.text("TOS +13.40 (approx.)", 1.20, 14.65, 0.08, rot=0.0)
    sh.text("D-1", 0.15, 14.65, 0.08, rot=90.0)
    sh.text("آسانسور", 2.15, 14.65, 0.12, farsi=True, rot=0.0)
    # duct D-2 vent cap (C side)
    sh.rect("A-ROOF", 6.753, 7.20, 9.30, 10.60)
    sh.line("A-ROOF", 6.753, 9.30, 7.20, 10.60)
    sh.line("A-ROOF", 6.753, 10.60, 7.20, 9.30)
    sh.text("D-2 VENT CAP h 0.60", 6.45, 9.95, 0.08, rot=0.0)
    # optional AC outdoor units on pads (front B-C zone)
    for k in range(3):
        y0 = 1.20 + k * 1.30
        sh.rect("A-ROOF", 6.20, 7.10, y0, y0 + 0.90)
        sh.text("AC", 6.65, y0 + 0.45, 0.10, rot=0.0, layer="A-EQPM")
    sh.text("AC OUTDOOR UNITS 3 x PAD 0.90 x 0.90 - OPTIONAL", 6.00, 3.05, 0.08, rot=0.0)
    # drains, ridges, slopes
    for tg, X, Y in DRAINS:
        sh.msp.add_circle(sh.E(X, Y), 0.10, dxfattribs={"layer": "A-ROOF-DRAN"})
        sh.msp.add_circle(sh.E(X, Y), 0.05, dxfattribs={"layer": "A-ROOF-DRAN"})
        sh.text(tg, X - 0.28 if X > 3 else X + 0.28, Y, 0.10, rot=0.0, layer="A-ROOF-DRAN")
    for X, Yw, tg in ((6.30, -0.25, "OF1"), (6.30, 20.054, "OF2")):          # overflow spouts (street / yard side, not to neighbours)
        sh.rect("A-ROOF-DRAN", X, X + 0.15, Yw, Yw + 0.20)
        sh.text(tg, X + 0.07, Yw - 0.25 if Yw < 0 else Yw + 0.45, 0.08, rot=0.0, layer="A-ROOF-DRAN")
    for X1, Y1, X2, Y2 in RIDGES:
        sh.line("A-ROOF-RIDG", X1, Y1, X2, Y2)
    dr = {t: (X, Y) for t, X, Y in DRAINS}
    for (X1, Y1), tg in SLOPES:
        X2, Y2 = dr[tg]
        L = math.hypot(X2 - X1, Y2 - Y1)
        e = (L - 0.35) / L
        Xe, Ye = X1 + (X2 - X1) * e, Y1 + (Y2 - Y1) * e
        arrow(sh, "A-ROOF-SLOP", X1, Y1, Xe, Ye)
        sh.text("2%", (X1 + Xe) / 2 + 0.15, (Y1 + Ye) / 2, 0.11, rot=0.0, layer="A-ROOF-SLOP")
    # names and levels
    sh.text("بام", 4.60, 5.10, 0.25, farsi=True, rot=0.0)
    sh.text("ROOF", 4.20, 5.10, 0.14, rot=0.0)
    sh.level("TOS +12.20, FIN. +12.32 (DRAIN) / +12.44 (RIDGE)", 4.10, 12.80, h=0.10)
    sh.level("FIN. +12.32", 4.70, 19.30, h=0.10)
    sh.level("FIN. +12.32", 4.10, 1.30, h=0.10)
    sh.text("PARAPET 0.20 x 1.20, TOP +13.40", 7.06, 15.0, 0.08, rot=0.0)
    sh.text("PARAPET 0.20 x 1.20, TOP +13.40", 0.10, 4.20, 0.08, rot=0.0)
    sh.text("PARAPET 0.20 x 1.20", 4.30, 0.12, 0.08, rot=90.0)
    sh.text("PARAPET 0.20 x 1.20", 4.30, 19.90, 0.08, rot=90.0)
    sh.text("معبر - فرض", 3.6, -2.65, 0.18, farsi=True, rot=90.0)

    # dimensions + grid (as A-101)
    AX_Y = [0.0, 7.5016, 13.5032, 18.806, 20.006]
    AX_X = [0.0, 2.3486, 7.1499]
    v_min, v_max = -0.25, 7.40
    u_max, u_min = sh.E(0, -0.25)[0], sh.E(0, 20.254)[0]
    us = [u_max] + [sh.E(0, Y)[0] for Y in AX_Y] + [u_min]
    for a, b in zip(us, us[1:]):
        sh.dim((a, v_min), (b, v_min), (a, v_min - 1.0), 0)
    sh.dim((u_max, v_min), (u_min, v_min), (u_max, v_min - 1.8), 0)
    vs = [v_min] + AX_X + [v_max]
    for a, b in zip(vs, vs[1:]):
        sh.dim((u_max, a), (u_max, b), (u_max + 1.0, a), 90)
    sh.dim((u_max, v_min), (u_max, v_max), (u_max + 1.8, v_min), 90)
    R = 0.40
    for lab, Y in zip("12345", AX_Y):
        u = sh.E(0, Y)[0]
        sh.msp.add_line((u, v_min - 3.0), (u, v_min - 0.2), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_line((u, v_max + 0.2), (u, v_max + 1.0), dxfattribs={"layer": "A-GRID"})
        if lab == "5":
            sh.msp.add_circle((u - 0.45, v_min - 3.0 - R), R, dxfattribs={"layer": "A-GRID-IDEN"})
            sh.text_uv(lab, u - 0.45, v_min - 3.0 - R, 0.35, layer="A-GRID-IDEN")
            continue
        sh.msp.add_circle((u, v_min - 3.0 - R), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u, v_min - 3.0 - R, 0.35, layer="A-GRID-IDEN")
    for lab, X in zip("ABC", AX_X):
        sh.msp.add_line((u_min - 1.0, X), (u_min - 0.2, X), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_line((u_max + 0.2, X), (u_max + 3.0, X), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_circle((u_max + 3.0 + R, X), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u_max + 3.0 + R, X, 0.35, layer="A-GRID-IDEN")
    # interior dims: stair house + overrun block, door, drains
    sh.dimY(7.55, 15.703, 3.75)
    sh.dimX(-0.05, 2.60, 16.30)
    sh.dimX(2.45, 6.80, 0.30)            # RD1 position from the stair-house line
    sh.dimY(-0.05, 0.30, 5.90)

    # frame + legend
    plan_cx = (u_min + u_max) / 2
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa("پیش نویس - پلان بام - روف") + " - " + REV,
                  f"ROOF PLAN  -  ROOF TOS +12.20 / STAIR HOUSE TOS +15.10 (+-0.00 = FDN TOP)  -  {REV} DRAFT  -  1:100  -  DIMENSIONS IN METRES", "A-105",
                  f"{REV} DRAFT (T40: parapet 0.20 x 1.20, stair house beams 0.40 / columns 2.90 / curb 0.20; T39 roof items R1-R12)", plan_cx, v_max)
    M.legend(sh, 4.6 + dx, 12.6)
    # roof schedule + notes
    sx0, sy0 = -29.5 + dx + 1.6, -4.6
    sched = [("TAG", "ITEM", "SIZE", "LEVEL", "NOTE"),
             ("DR1", "STEEL DOOR", "0.90x2.10", "sill +12.53", "stair house -> roof, opens out, head +14.63 (u/s beam +14.70), weather seal"),
             ("RD1-5", "ROOF DRAIN", "dia 100", "+12.32", "leaf guard; downpipes: RD2 in duct D-2, RD1/RD4 front, RD3/RD5 rear facade"),
             ("SPOUT", "SPOUT", "dia 75", "~+15.20", "through the 0.20 curb of the stair-house roof -> main roof (B side), splash tile"),
             ("D-1", "DUCT VENT", "0.35x1.80", "> +13.40", "beside the lift, vents through the overrun roof"),
             ("D-2", "DUCT CAP", "0.45x1.30", "+13.03", "C side duct, louvred cap h 0.60, membrane upturn 0.30"),
             ("OVR", "LIFT OVERRUN", "2.15x1.95", "TOS +13.40", "approx.; beams 0.40 -> overhead 3.62 above top stop FFL +9.38 (supplier)"),
             ("AC", "AC PADS (OPT.)", "3x0.9x0.9", "+12.48", "split outdoor units, one per unit (mechanical to confirm)")]
    colx = [0.0, 1.2, 3.3, 4.8, 6.3]
    sh.text_uv(fa("جدول اقلام بام - ") + REV, sx0 + 4.0, sy0 + 0.45, 0.30, farsi=True)
    for k, row in enumerate(sched):
        yy = sy0 - k * 0.30
        for cx, s in zip(colx, row):
            sh.text_uv(s, sx0 + cx, yy, 0.15 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
        sh.msp.add_line((sx0 - 0.1, yy - 0.15), (sx0 + 13.0, yy - 0.15), dxfattribs={"layer": "A-ANNO-TABL"})
    yy = sy0 - len(sched) * 0.30 - 0.05
    notes = [
        "ROOF NOTES / ASSUMPTIONS (no roof plan in the basis PDF; architect's assumptions, T39):",
        "R1. LEVELS (T40): +-0.00 = top of foundation. Roof slab TOS +12.20 (ETABS Story4, typical geometry + rear cantilever to axis 5);",
        "     stair landing FFL +12.28. Roof beams 0.50.",
        "R2. Build-up: slope screed 2% (0.03 at drains -> ~0.15 at ridges) + XPS 0.06 (Mobhas 19) + 2-layer membrane + tiles:",
        "     finished roof +12.32 at the drains / parapet low line, ~+12.44 at the ridges. Membrane upturn 0.30 on parapets.",
        "R3. Parapet (boss T40): 20 cm wall, 1.20 high from the roof slab TOS +12.20 -> top +13.40, coping 0.30 (top ~+13.45).",
        "     Guard above the finish: 1.08-1.13 at the low line; ~0.96-1.01 where ridges meet the parapet (Mobhas 4: 1.10) - see T40.",
        "R4. Stair house A-B / 2-3 on columns 40x40 (C2, C6, C16, C18), columns 2.90, beams 0.40 (boss T40): roof TOS +15.10,",
        "     u/s beam +14.70; walls 20 cm. On its roof a 20 cm curb 0.20 high (top +15.30), membrane over the curb + cap; spout.",
        "R5. Door DR1 0.90 x 2.10 in the B-side wall, from the landing FFL +12.28 (one 0.25 step): sill +12.53, head +14.63.",
        "R6. Elevator overrun over the shaft: walls 15 cm, TOS ~+13.40, beams 0.40, overhead 3.62 (ASSUMED, supplier); not in ETABS.",
        "R7. Ducts: D-1 (beside the lift) vents through the overrun roof; D-2 (C side) louvred cap h 0.60.",
        "R8. Drainage: 5 drains dia 100 (RD1-RD5), 2% falls, ridges dashed; overflow spouts in the parapet next to RD1 / RD3.",
        "R9. No water tank on the roof (tank 2000 L in the yard pump room, A-101). No solar heater assumed.",
        "R10. AC outdoor units (optional): 3 pads in the front B-C zone, ~0.6 kN each. Antenna / satellite on the stair-house wall.",
        "R11. No lightning rod (electrical predesign: SPD only). Access to the stair-house roof: removable ladder (not fixed).",
        "R12. Structural (coordination 65): roof parapet 1.20 (model 1.18), stair-house curb 0.20 (model 0.60), stair-house beams 0.40.",
    ]
    for k, s in enumerate(notes):
        sh.text_uv(s, sx0 - 0.3, yy - k * 0.24, 0.14 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
    walls = []
    for x0, x1, y0, y1, wid, t, note in RW:
        L = max(x1 - x0, y1 - y0)
        walls.append(dict(id=wid, x=[x0, x1], y=[y0, y1], length=round(L, 3), thick_cm=t, note=note))
    return dict(walls=walls, openings=ROPEN, drains=DRAINS, ridges=RIDGES, levels=ROOF, columns_40=COL40, notes=notes)


# ---------------------------------------------------------------- layouts
def add_layouts(doc, sheets, ctb):
    """sheets: {sheet_no: (layout_name, [x0, y0, x1, y1] model window of the A3 frame)}"""
    if "A-ANNO-NPLT" in doc.layers:
        doc.layers.get("A-ANNO-NPLT").dxf.plot = 0
    for no, (name, (x0, y0, x1, y1)) in sheets.items():
        lay = doc.layouts.new(name)
        lay.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units="mm", offset=(0, 0), rotation=0, scale=1,
                       name=A3_MEDIA, device="DWG To PDF.pc3")
        lay.dxf_layout.dxf.current_style_sheet = ctb
        vp = lay.add_viewport(center=(210, 148.5), size=(420, 297), view_center_point=((x0 + x1) / 2, (y0 + y1) / 2),
                              view_height=(y1 - y0), dxfattribs={"layer": "A-ANNO-NPLT"})
        vp.dxf.flags = vp.dxf.flags | 16384          # display locked
    for nm in list(doc.layouts.names()):
        if nm.lower().startswith("layout"):
            doc.layouts.delete(nm)
