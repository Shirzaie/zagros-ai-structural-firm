# -*- coding: utf-8 -*-
"""Rev.8 (task 39) sheet builders used by make_arch_rev8.py:

    car_block       block CAR_SEDAN (top view of a sedan 1.80 x 4.50, front = +x), layer 0 / BYBLOCK
    copy_typical    floors 2 and 3 = copies of the floor-1 (typical) drawing, shifted in model space
    floor_sheet     titles, level, floor-specific notes, schedule title, frame + legend of one typical floor
    roof_sheet      A-105 roof plan: parapet, stair house, elevator overrun, ducts, drains, slopes, door, levels
    stair_house_sheet  A-106 (T43): stair-house roof plan +17.50 (extended to axis 5) + section S-1
    add_layouts     one named paper-space layout per sheet (A3, one locked viewport at 1:50)

M = the make_arch_rev8 module (set by it before use: helpers Sheet, fa, sheet_frame, legend, union_edges ...).
"""
import math

from ezdxf.enums import TextEntityAlignment as TA

M = None

A1_MEDIA = "ISO_full_bleed_A1_(841.00_x_594.00_MM)"   # T49: 1:50 on A1 (model window 42.0 x 29.7 m)


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


def stair_typical(sh, lev, first_floor):
    """T41 stair on a floor plan (cut ~1.2 m above FFL). B side (X 1.15-2.25) UP 10 risers x 0.170, treads 0.30,
    from the floor-landing edge Y 11.658 to the half landing (edge Y 8.958): solid to the cut, dashed beyond.
    A side (X -0.05-1.05) DN = the flight below, visible: typical 10 risers / 0.30 (edge 11.658); on floor 1 the
    parking flight 11 risers x 0.174 / 0.28 (edge 11.758)."""
    ffl = lev + 0.08
    ycut = 9.95
    yl = 11.658
    for k in range(10):
        Yt = yl - 0.30 * k
        sh.line("A-STRS" if Yt >= ycut else "A-STRS-OVHD", 1.15, Yt, 2.25, Yt)
    sh.line("A-STRS", 1.15, ycut, 1.15, yl)
    sh.line("A-STRS-OVHD", 1.15, 8.958, 1.15, ycut)
    sh.line("A-STRS", 1.15, ycut - 0.05, 2.25, ycut + 0.20)          # break line
    ya, ta, na = (11.758, 0.28, 11) if first_floor else (11.658, 0.30, 10)
    for k in range(na):
        sh.line("A-STRS", -0.05, ya - ta * k, 1.05, ya - ta * k)
    sh.line("A-STRS", 1.05, 8.958, 1.05, ya)
    # walking lines
    sh.line("A-STRS", 1.70, yl - 0.15, 1.70, ycut + 0.25)
    sh.line("A-STRS", 1.70, ycut + 0.25, 1.60, ycut + 0.45)
    sh.line("A-STRS", 1.70, ycut + 0.25, 1.80, ycut + 0.45)
    sh.msp.add_circle(sh.E(1.70, yl - 0.15), 0.04, dxfattribs={"layer": "A-STRS"})
    sh.line("A-STRS", 0.68, ya - 0.15, 0.68, 9.30)
    sh.line("A-STRS", 0.68, 9.30, 0.58, 9.50)
    sh.line("A-STRS", 0.68, 9.30, 0.78, 9.50)
    sh.msp.add_circle(sh.E(0.68, ya - 0.15), 0.04, dxfattribs={"layer": "A-STRS"})
    sh.text("UP", 1.70, yl + 0.17, 0.15, rot=0.0, layer="A-STRS")
    sh.text("DN", 0.68, ya + 0.17, 0.15, rot=0.0, layer="A-STRS")
    up_to = "+14.28" if lev > 10 else f"{ffl + 3.40:+.2f}"
    sh.text(f"20 x 17.0/30 TO {up_to}", 1.97, 11.20, 0.07, rot=0.0)
    if first_floor:
        sh.text("23 x 17.4/28 TO +0.08", 0.93, 11.20, 0.07, rot=0.0)
        hl_dn = 2.17
    else:
        sh.text(f"20 x 17.0/30 TO {ffl - 3.40:+.2f}", 0.93, 11.20, 0.07, rot=0.0)
        hl_dn = round(ffl - 1.70, 2)
    hl_up = round(ffl + 1.70, 2)
    sh.text(f"HALF LANDING UP FFL {hl_up:+.2f}", 1.10, 8.22, 0.075, rot=90.0)
    sh.text(f"(DN {hl_dn:+.2f}) ON STAIR COLUMNS", 1.10, 8.42, 0.065, rot=90.0)
    sh.text(f"FLOOR LANDING FFL {ffl:+.2f}", 1.10, 12.30, 0.075, rot=90.0)
    sh.dimY(yl, 13.604, 0.28)                                        # floor landing 1.95
    sh.dimY(8.958, yl, 0.28)                                         # going 2.70
    sh.dimY(7.75, 8.958, 0.28)                                       # half landing 1.21


def floor_sheet(doc, dx, sheet_no, en, fa_name, lev, stall):
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    msp = doc.modelspace()
    old = fa("جدول در و پنجره - طبقات تیپ ۱ تا ۳ - ") + REV
    for e in msp.query("TEXT"):
        if e.dxf.text == old and -29.5 + dx < e.dxf.insert.x < 12.5 + dx:
            e.dxf.text = fa(f"جدول در و پنجره - {fa_name} - ") + REV
    # T41: lev = TOS (structural top of slab, from the top of foundation +-0.00); FFL = TOS + 0.08; storey 3.40
    ffl = lev + 0.08
    nxt = {4.00: "TOS +7.40 (FLOOR 2, A-103)", 7.40: "TOS +10.80 (FLOOR 3, A-104)", 10.80: "TOS +14.20 (ROOF, A-105)"}[lev]
    below = {4.00: "parking FFL +0.08 on the foundation top +-0.00 (A-101)", 7.40: "floor 1 TOS +4.00 (A-102)",
             10.80: "floor 2 TOS +7.40 (A-103)"}[lev]
    special = {
        4.00: ["14. FLOOR 1: parking stair 23 x 0.174 / 0.28 arrives here (A side, landing edge 0.10 behind the B side). Ducts START",
               "     at this slab (pipes under it to the facade / yard). Half landings: DN +2.17 (parking), UP +5.78."],
        7.40: ["14. FLOOR 2 (middle floor): plan identical to floors 1 and 3. Stair 20 x 0.170 / 0.30 up and down;",
               "     half landings DN +5.78, UP +9.18. Ducts pass through the slab."],
        10.80: ["14. FLOOR 3 (top floor): stair 20 x 0.170 to the roof landing FFL +14.28 and door DR1 (A-105), half landing +12.58.",
                "     Elevator top stop FFL +10.88; shaft continues to the stair-house roof +17.50 (T43). Ceiling = roof slab (insulation on the roof)."],
    }[lev]
    y = -4.95
    sh.text_uv("FLOOR-SPECIFIC NOTES (" + sheet_no + ")", -5.3 + dx, y + 0.35, 0.18, align=TA.MIDDLE_LEFT, width=0.85)
    for s in [f"12. LEVELS (+-0.00 = top of foundation): this floor TOS {lev:+.2f} (structural), FFL {ffl:+.2f}. Below: {below}.",
              f"     Above: {nxt}. Storey 3.40 = clear 2.90 (slab TOS -> u/s beam, boss) + beam 0.50: u/s beam {lev + 2.90:+.2f} = FFL+2.82.",
              f"13. Parking stall of this unit: {stall} (A-101). One dwelling unit per floor. Stair: flights 1.10, well 0.10, 2h+b = 0.64."] + special:
        sh.text_uv(s, -5.3 + dx, y, 0.15, align=TA.MIDDLE_LEFT, width=0.8)
        y -= 0.27
    stair_typical(sh, lev, lev == 4.00)
    sh.level(f"FFL {ffl:+.2f} (TOS {lev:+.2f})", 2.72, 12.05, h=0.12)
    sh.text("واحد " + fa_name, 5.6, 16.4, 0.20, farsi=True, rot=0.0)
    u_min, u_max, v_max = -20.254, 0.25, 7.40
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa(f"برای تأیید - پلان معماری {fa_name}") + " - " + REV,
                  f"{en} PLAN  -  TOS {lev:+.2f} / FFL {ffl:+.2f}  -  {REV} FOR APPROVAL  -  1:50  -  DIMENSIONS IN METRES", sheet_no,
                  f"{REV} FOR APPROVAL (T41: storey 3.40 = clear 2.90 + beam 0.50; stair 20 x 0.170): {en.lower()} = Rev.6 FINAL + grid B' / C19 2.500",
                  (u_min + u_max) / 2 + dx, v_max)
    M.legend(sh, 4.6 + dx, 12.6)
    return sh


# ---------------------------------------------------------------- roof
COL40 = [(0.0, 7.5016), (2.3486, 7.5016), (0.0, 13.5032), (2.3486, 13.5032),       # stair-house columns 40x40 (T34)
         (0.0, 18.806), (2.500, 18.806)]                                            # T43 (boss 2026-10-31): new C17 / C19 above the roof
# T43: stair-house roof slab outline (TOS +17.50): old part Y 7.30-13.40, extension to the rear facade face 20.254 (cantilever)
SH_ROOF = [(-0.25, 7.30), (2.55, 7.30), (2.55, 13.40), (2.70, 13.40), (2.70, 20.254), (-0.25, 20.254)]
# curb 0.20 x 0.20 on the stair-house roof (+17.50 -> +17.70): (x0, x1, y0, y1, id, new?) - T43 boss: continued on the new edges
CURB = [(-0.25, -0.05, 7.55, 13.60, "K-A1", False), (-0.05, 2.45, 7.55, 7.75, "K-2", False), (2.25, 2.45, 7.75, 13.60, "K-B1", False),
        (-0.25, -0.05, 13.60, 20.254, "K-A2", True), (2.25, 2.70, 13.40, 13.60, "K-J", True), (2.50, 2.70, 13.60, 20.254, "K-B2", True),
        (-0.05, 2.50, 20.054, 20.254, "K-5", True)]
CURB_REMOVED = "old rear curb of the stair house on axis 3 (X -0.05..2.45, 2.50 m): now inside the roof (T43)"
RW = [  # roof walls cut at ~+13.2: parapets 20 cm h 1.20 (T40), stair house 20 cm, elevator overrun
    (-0.25, -0.05, -0.25, 20.254, "R-PA", 20, "parapet / stair-house wall on axis A (boundary)"),
    (7.20, 7.40, -0.25, 20.254, "R-PC", 20, "parapet axis C (boundary)"),
    (-0.05, 7.20, -0.25, -0.05, "R-P1", 20, "parapet front (axis 1)"),
    (-0.05, 7.20, 20.054, 20.254, "R-P5", 20, "parapet rear (balcony edge, axis 5)"),
    (-0.05, 2.45, 7.55, 7.75, "SH-2", 20, "stair house front wall (axis 2 side)"),
    (2.25, 2.45, 7.55, 13.604, "SH-B", 20, "stair house wall to the roof (B side, on W24 / beam line), door DR1"),
    (-0.05, 2.60, 13.604, 13.754, "OV-F", 15, "stair house / lift shaft front (W19 line), full height"),
    (2.45, 2.60, 13.604, 15.703, "OV-B", 15, "lift shaft side (W18 line): T43 full height to u/s stair-house roof (was 0.55)"),
    (-0.05, 2.60, 15.553, 15.703, "OV-R", 15, "lift shaft back (W17 line): T43 full height to u/s stair-house roof (was 0.55)"),
    (0.349, 0.449, 13.754, 15.553, "OV-D", 10, "shaft / duct D-1 (W20 line): T43 full height to u/s stair-house roof"),
    # T43 (boss 2026-10-31): stair house enclosed up to axis 4 with 20 cm walls (clear 2.90) on the beams C18-C19 and C17-C19;
    # on axis A the boundary wall R-PA is full height between C16 and C17 (was parapet 1.20)
    (2.40, 2.60, 15.703, 18.606, "SH-B2", 20, "T43: stair-house extension wall, east (beam C18-C19), clear 2.90"),
    (0.20, 2.30, 18.706, 18.906, "SH-4", 20, "T43: stair-house extension wall on axis 4 (beam C17-C19), clear 2.90"),
]
ROPEN = [("DR1", "door", 2.25, 2.45, 12.30, 13.20),
         ("DR2", "door", 0.80, 1.70, 18.706, 18.906)]     # T47 (boss): door to the closed space behind the shaft, in SH-4
VS1 = (2.449, 2.599, 14.35, 14.95)               # T47: shaft vent louvre 0.60 x 0.30 in OV-B, sill +16.40, head +16.70
SPOUTS = [("SP1", 2.45, 2.70, 8.20, 8.32), ("SP2", 2.70, 2.95, 19.74, 19.86)]   # T47: SP2 at the cantilever end
VENTS = [("VP1", 0.28, 14.10), ("VP2", 0.28, 15.20)]   # T47: D-1 stack vents, sleeves dia 125 in the stair-house roof
DRAINS = [("RD1", 6.80, 0.30), ("RD2", 6.80, 11.00), ("RD3", 6.80, 19.70), ("RD4", 0.40, 0.30), ("RD5", 0.40, 19.70)]
RIDGES = [(3.60, -0.05, 3.60, 7.55), (3.60, 5.50, 7.20, 5.50), (2.45, 7.55, 3.60, 7.55), (2.60, 15.703, 7.20, 15.703),
          (2.60, 18.906, 2.60, 20.054)]
SLOPES = [((5.40, 3.00), "RD1"), ((1.90, 4.20), "RD4"), ((4.60, 7.90), "RD2"), ((4.60, 14.40), "RD2"), ((4.70, 17.90), "RD3"),
          ((1.20, 19.95), "RD5")]
ROOF = dict(   # T41: all levels from the top of foundation +-0.00; TOS = structural top of slab; clear heights + beams
    slab_top=14.20, finish_at_drains=14.32, finish_at_ridges=14.44, landing_FFL=14.28,
    parapet_thick=0.20, parapet_h_from_TOS=1.20, parapet_bottom=14.20, parapet_top=15.40, coping_top=15.45,
    parapet_guard_above_finish="1.08 (+0.05 coping = 1.13) at the low line +14.32; ~0.96-1.01 where ridges reach the parapet",
    stair_house_clear=2.90, stair_house_beams=0.40, stair_house_storey=3.30, stair_house_roof=17.50, stair_house_us_beam=17.10,
    stair_house_wall_clear_h=2.90,
    stair_house_parapet=0.20, stair_house_parapet_thick=0.20, stair_house_parapet_top=17.70,
    overrun_T43="REMOVED (boss 2026-10-31): no separate overrun on the roof; shaft walls OV-B / OV-R / OV-D continue to u/s stair-house roof (beam +17.10 / slab ~+17.19); overhead above the top stop FFL +10.88 > 3.87 (boss min.); hook under the stair-house roof slab",
    stair_house_extension_T43="roof +17.50 continued Y 13.50 -> 20.01 (cantilever 1.20 beyond axis 4) over X 0.00-2.35/2.50; columns C17 (0, 18.806) / C19 (2.50, 18.806) 40x40 12T16; 20 cm walls clear 2.90 on beams C16-C17 (boundary), C18-C19, C17-C19 -> closed stair house to axis 4; curb 0.20 x 0.20 on the new roof edges (A side, east side, axis 5); no new doors / windows",
    stair_floor3_to_roof="FFL +10.88 -> +14.28: 20 risers x 0.170, treads 0.30, half landing FFL +12.58",
    door_DR1="0.90 x 2.10, sill +14.53 (0.25 step from the landing FFL +14.28), head +16.63 < u/s beam +17.10",
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
    # stair (T41: F3 FFL +10.88 -> roof landing FFL +14.28, 10 + 10 risers x 0.170, treads 0.30), all visible from the cut
    yh, ye = 8.958, 11.658
    for k in range(10):
        Yt = yh + 0.30 * k
        sh.line("A-STRS", -0.05, Yt, 1.05, Yt)
        sh.line("A-STRS", 1.15, Yt, 2.25, Yt)
    sh.line("A-STRS", 1.05, yh, 1.05, ye)
    sh.line("A-STRS", 1.15, yh, 1.15, ye)
    arrow(sh, "A-STRS", 0.50, ye + 0.20, 0.50, yh + 0.25, head=0.15)
    sh.msp.add_circle(sh.E(0.50, ye + 0.20), 0.04, dxfattribs={"layer": "A-STRS"})
    sh.text("DN", 0.50, ye + 0.45, 0.15, rot=0.0)
    sh.text("20 x 17.0 / 30 FROM FFL +10.88", 1.70, 10.30, 0.09, rot=0.0)
    sh.text("HALF LANDING FFL +12.58", 1.10, 8.35, 0.09, rot=90.0)
    sh.text("خرپشته", 1.80, 12.80, 0.20, farsi=True, rot=0.0)
    sh.text("STAIR HOUSE", 1.48, 12.80, 0.10, rot=0.0)
    sh.level("FFL +14.28 (TOS +14.20)", 1.00, 13.40, h=0.10)
    sh.text("STAIR-HOUSE ROOF TOS +17.50, CURB 0.20 x 0.20 TOP +17.70", 2.75, 10.60, 0.075, rot=0.0)
    # spout from the stair-house roof onto the main roof (B side)
    sh.rect("A-ROOF-DRAN", 2.45, 2.70, 8.20, 8.32)
    sh.text("SPOUT", 2.95, 8.26, 0.07, rot=0.0)
    # elevator overrun + duct D-1
    sh.line("A-ELEV", 0.449, 13.754, 2.449, 15.553)
    sh.line("A-ELEV", 0.449, 15.553, 2.449, 13.754)
    sh.text("SHAFT TO S.H. ROOF", 1.75, 14.55, 0.09, rot=0.0)
    sh.text("(OVERRUN REMOVED, T43)", 1.20, 14.55, 0.08, rot=0.0)
    # T43: extended stair-house roof above (dashed), new columns
    sh.pline("A-FLOR-OVHD", SH_ROOF)
    sh.text("STAIR-HOUSE EXTENSION (T43)", 2.05, 17.25, 0.08, rot=0.0)
    sh.text("ENCLOSED, DOOR DR2 (T47)", 1.85, 17.25, 0.08, rot=0.0)
    # T47: door DR2 (opens out to the roof under the cantilever), shaft vent VS1 (high), spout SP2 splash
    sh.door(1.70, 18.906, (-1, 0), (0, 1), 0.90)
    sh.tag("DR2", 1.25, 19.30)
    sh.rect("A-FLOR-OVHD", *VS1)
    sh.tag("VS1", 2.95, 14.65)
    sh.rect("A-ROOF-DRAN", 2.70, 2.95, 19.74, 19.86)
    sh.text("SP2 SPLASH", 3.40, 19.80, 0.07, rot=0.0)
    sh.text("فضاى بسته خرپشته", 1.30, 17.25, 0.13, farsi=True, rot=0.0)
    sh.text("C17 NEW 40x40", 0.10, 17.85, 0.07, rot=0.0)
    sh.text("C19 NEW 40x40", 3.05, 18.806, 0.07, rot=0.0)
    sh.text("CANTILEVER 1.20", 2.20, 19.55, 0.07, rot=0.0)
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
    sh.level("TOS +14.20, FIN. +14.32 (DRAIN) / +14.44 (RIDGE)", 4.10, 12.80, h=0.10)
    sh.level("FIN. +14.32", 4.70, 19.30, h=0.10)
    sh.level("FIN. +14.32", 4.10, 1.30, h=0.10)
    sh.text("PARAPET 0.20 x 1.20, TOP +15.40", 7.06, 15.0, 0.08, rot=0.0)
    sh.text("PARAPET 0.20 x 1.20, TOP +15.40", 0.10, 4.20, 0.08, rot=0.0)
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
    sh.dimY(7.55, 18.906, 3.75)
    sh.dimX(-0.05, 2.60, 15.63)
    sh.dimX(2.45, 6.80, 0.30)            # RD1 position from the stair-house line
    sh.dimY(-0.05, 0.30, 5.90)

    # frame + legend
    plan_cx = (u_min + u_max) / 2
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa("برای تأیید - پلان بام - روف") + " - " + REV,
                  f"ROOF PLAN  -  ROOF TOS +14.20 / STAIR HOUSE TOS +17.50 (+-0.00 = FDN TOP)  -  {REV} FOR APPROVAL  -  1:50  -  DIMENSIONS IN METRES", "A-105",
                  f"{REV} FOR APPROVAL (T43: stair house extended: roof to axis 5, cols C17/C19, walls to axis 4; T47 DR2 / VS1 / SP2; R1-R14)", plan_cx, v_max)
    M.legend(sh, 4.6 + dx, 12.6)
    # roof schedule + notes
    sx0, sy0 = -29.5 + dx + 1.6, -4.6
    sched = [("TAG", "ITEM", "SIZE", "LEVEL", "NOTE"),
             ("DR1", "STEEL DOOR", "0.90x2.10", "sill +14.53", "stair house -> roof, opens out, head +16.63 (u/s beam +17.10), weather seal"),
             ("RD1-5", "ROOF DRAIN", "dia 100", "+14.32", "leaf guard; downpipes: RD2 in duct D-2, RD1/RD4 front, RD3/RD5 rear facade"),
             ("SPOUT", "SPOUT", "dia 75", "~+17.60", "through the 0.20 curb of the stair-house roof -> main roof (B side), splash tile"),
             ("D-1", "DUCT", "0.35x1.80", "< +17.19", "beside the lift; 2 stack vents VP1/VP2 dia 100 in sleeves dia 125 through the S.H. roof (T47)"),
             ("DR2", "STEEL DOOR", "0.90x2.10", "sill +14.53", "T47: closed space behind the shaft -> roof under the cantilever (wall SH-4), opens out"),
             ("VS1", "SHAFT VENT", "0.60x0.30", "+16.40", "T47: louvre with insect mesh at the top of the lift shaft (wall OV-B), to the open roof"),
             ("SP2", "SPOUT", "dia 75", "~+17.60", "T47: second spout of the stair-house roof, east curb at the cantilever end (Y ~19.80)"),
             ("D-2", "DUCT CAP", "0.45x1.30", "+15.03", "C side duct, louvred cap h 0.60, membrane upturn 0.30"),
             ("SHFT", "LIFT SHAFT", "2.00x1.80", "to +17.19", "T43: overrun removed, shaft walls to u/s stair-house roof; hook under the roof slab"),
             ("T43", "S.H. EXTENSION", "2.5x6.5", "TOS +17.50", "roof Y 13.50->20.01, cols C17/C19, 20 cm walls to axis 4, curb; A-106"),
             ("AC", "AC PADS (OPT.)", "3x0.9x0.9", "+14.48", "split outdoor units, one per unit (mechanical to confirm)")]
    colx = [0.0, 1.2, 3.3, 4.8, 6.3]
    sh.text_uv(fa("جدول اقلام بام - ") + REV, sx0 + 4.0, sy0 + 0.45, 0.30, farsi=True)
    for k, row in enumerate(sched):
        yy = sy0 - k * 0.30
        for cx, s in zip(colx, row):
            sh.text_uv(s, sx0 + cx, yy, 0.15 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
        sh.msp.add_line((sx0 - 0.1, yy - 0.15), (sx0 + 13.0, yy - 0.15), dxfattribs={"layer": "A-ANNO-TABL"})
    yy = sy0 - len(sched) * 0.30 - 0.05
    notes = [
        "ROOF NOTES / ASSUMPTIONS (no roof plan in the basis PDF; architect assumptions T39, levels T41):",
        "R1. LEVELS (T41): +-0.00 = top of foundation; floor 3 TOS +10.80 + 3.40 (clear 2.90 + beam 0.50) -> roof slab TOS +14.20",
        "     (typical geometry + rear cantilever to axis 5); roof stair landing FFL +14.28. Roof beams 0.50 (u/s +13.70).",
        "R2. Build-up: slope screed 2% (0.03 at drains -> ~0.15 at ridges) + XPS 0.06 (Mobhas 19) + 2-layer membrane + tiles:",
        "     finished roof +14.32 at the drains / parapet low line, ~+14.44 at the ridges. Membrane upturn 0.30 on parapets.",
        "R3. Parapet (boss): 20 cm wall, 1.20 high from the roof slab TOS +14.20 -> top +15.40, coping 0.30 (top ~+15.45).",
        "     Guard above the finish: 1.08-1.13 at the low line; ~0.96-1.01 where ridges meet the parapet (Mobhas 4: 1.10).",
        "R4. Stair house A-B / 2-3 on columns 40x40: clear 2.90 + beams 0.40 = 3.30 (boss) -> roof TOS +17.50, u/s beam +17.10; T43: roof to axis 5;",
        "     walls 20 cm, clear 2.90 on the roof beams. On its roof a 20 cm curb 0.20 high (+17.50 -> +17.70) + cap; spout to the roof.",
        "R5. Stair F3 -> roof: FFL +10.88 -> +14.28, 20 x 0.170 / 0.30, half landing +12.58. Door DR1 0.90 x 2.10: sill +14.53, head +16.63.",
        "R6. T43: separate lift overrun removed; shaft walls continue to u/s stair-house roof (overhead > 3.87, boss approved 3.87 min).",
        "R7. Ducts: D-1 (beside the lift) vents VP1/VP2 through the stair-house roof (T47); D-2 (C side) cap h 0.60 (~+15.03).",
        "R8. Drainage: 5 drains dia 100 (RD1-RD5), 2% falls, ridges dashed; overflow spouts in the parapet next to RD1 / RD3.",
        "R9. No water tank on the roof (tank 2000 L in the yard pump room, A-101). No solar heater assumed.",
        "R10. AC outdoor units (optional): 3 pads in the front B-C zone, ~0.6 kN each. Antenna / satellite on the stair-house wall.",
        "R11. No lightning rod (electrical predesign: SPD only). Access to the stair-house roof: removable ladder (not fixed).",
        "R12. Structural (coordination 66 / 69): parapet 1.20 on the roof edge beams, stair-house walls clear 2.90, curb 0.20 (T43 data file).",
        "R13. T43 (boss 2026-10-31): stair-house roof +17.50 continues from axis 3 to the end of the cantilever (axis 5) over X 0-2.50;",
        "R14. T47 (boss): door DR2 in SH-4, shaft vent VS1 in OV-B, D-1 vents VP1/VP2 (sleeves dia 125), spout SP2; infill gap 80 mm.",
        "     new columns C17 / C19 40x40 (12T16); 20 cm walls (clear 2.90) to axis 4 = closed stair house; curb 0.20 on the new edges; no new doors / windows. A-106.",
    ]
    for k, s in enumerate(notes):
        sh.text_uv(s, sx0 - 0.3, yy - k * 0.24, 0.14 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
    walls = []
    for x0, x1, y0, y1, wid, t, note in RW:
        L = max(x1 - x0, y1 - y0)
        walls.append(dict(id=wid, x=[x0, x1], y=[y0, y1], length=round(L, 3), thick_cm=t, note=note))
    return dict(walls=walls, openings=ROPEN, drains=DRAINS, ridges=RIDGES, levels=ROOF, columns_40=COL40, notes=notes)


# ---------------------------------------------------------------- T43: A-106 stair-house roof plan + section S-1
# Scope (boss 2026-10-31 + approval): roof continued to the end of the cantilever, end columns C17 / C19, 20 cm walls to
# axis 4 (closed stair house), overrun removed (shaft walls to the roof), curb on the new edges; no new doors / windows.
SEC_DZ = 8.0          # section: u = -Y + dx (aligned with the plan), v = Z - SEC_DZ


def stair_house_sheet(doc, dx):
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    msp = sh.msp
    # ---- plan of the stair-house roof +17.50
    sh.pline("A-ROOF", SH_ROOF)                                   # slab edge (old part + extension)
    for X1, Y1, X2, Y2 in M.union_edges([c[:4] for c in CURB], [], []):     # curb 0.20 x 0.20 (T43: continued on the new edges)
        sh.line("A-WALL", X1, Y1, X2, Y2)
    for r in RW:                                                  # stair-house / shaft walls below (dashed)
        if r[4] in ("SH-B2", "SH-4", "OV-B", "OV-R", "OV-D", "OV-F", "SH-B", "SH-2"):
            sh.rect("A-FLOR-OVHD", *r[:4])
    sh.line("A-FLOR-OVHD", -0.25, 13.40, 2.55, 13.40)             # end of the old roof (dashed reference)
    for x, y in COL40:                                            # columns below (dashed)
        sh.rect("A-FLOR-OVHD", x - 0.20, x + 0.20, y - 0.20, y + 0.20)
    for (xa, ya), (xb, yb) in [((0.0, 7.5016), (0.0, 20.006)), ((2.3486, 7.5016), (2.3486, 13.5032)),
                               ((2.3486, 13.5032), (2.500, 18.806)), ((2.500, 18.806), (2.500, 20.006)),
                               ((0.0, 7.5016), (2.3486, 7.5016)), ((0.0, 13.5032), (2.3486, 13.5032)),
                               ((0.0, 18.806), (2.500, 18.806)), ((0.0, 20.006), (2.500, 20.006))]:
        sh.line("A-GRID", xa, ya, xb, yb)                          # beam centre lines 40x40
    for tg, x0, x1, y0, y1 in SPOUTS:                              # SP1 existing, SP2 T47
        sh.rect("A-ROOF-DRAN", x0, x1, y0, y1)
        sh.text(tg + " dia 75", x1 + 0.50, (y0 + y1) / 2, 0.10, rot=0.0, layer="A-ROOF-DRAN")
    for tg, X, Y in VENTS:                                         # T47: D-1 vents through the slab (sleeves dia 125)
        sh.msp.add_circle(sh.E(X, Y), 0.0625, dxfattribs={"layer": "A-SHFT"})
        sh.text(tg, X + 0.30, Y, 0.08, rot=0.0, layer="A-SHFT")
    sh.line("A-ROOF-RIDG", -0.05, 13.50, 2.50, 13.50)              # ridge on axis 3: 2% to SP1 (front) and SP2 (rear)
    arrow(sh, "A-ROOF-SLOP", 1.90, 13.00, 2.40, 8.70)
    arrow(sh, "A-ROOF-SLOP", 1.90, 14.00, 2.45, 19.40)
    sh.text("بام خرپشته", 1.45, 10.60, 0.20, farsi=True, rot=0.0)
    sh.text("STAIR-HOUSE ROOF", 1.15, 10.60, 0.10, rot=0.0)
    sh.level("TOS +17.50", 0.45, 9.20, h=0.09)
    sh.text("EXISTING (Rev.9)", 0.80, 11.50, 0.10, rot=0.0)
    # T49 add. (boss): all stair-house joists along X (span 2.30): direction symbol
    sh.line("A-STRS", 0.15, 12.70, 2.25, 12.70)
    arrow(sh, "A-STRS", 1.20, 12.70, 0.15, 12.70, head=0.15)
    arrow(sh, "A-STRS", 1.20, 12.70, 2.25, 12.70, head=0.15)
    sh.text("JOISTS ALONG X, SPAN 2.30 (T49)", 1.10, 12.45, 0.08, rot=90.0)
    sh.text("EXTENSION T43: Y 13.50 -> 20.01", 1.25, 16.90, 0.11, rot=0.0)
    sh.text("CURB 0.20 x 0.20, TOP +17.70", 0.25, 16.90, 0.08, rot=0.0)
    sh.text("WALLS BELOW DASHED: SHAFT 15 cm, NEW 20 cm (CLEAR 2.90)", 0.75, 17.60, 0.08, rot=0.0)
    sh.text("CANT. 1.20", 1.25, 19.40, 0.10, rot=0.0)
    for nm, (x, y) in zip(("C2", "C6", "C16", "C18", "C17 NEW", "C19 NEW"), COL40):
        sh.text(nm, x + (0.35 if x < 1 else -0.35), y, 0.09, rot=0.0)
    sh.text("BEAMS 40x40 (CENTRE LINES)", 1.95, 10.60, 0.10, rot=0.0)
    # section mark S-1 at X = 1.20
    for Y, d in ((6.70, 0.6), (21.00, -0.6)):
        sh.line("A-ANNO", 1.20, Y, 1.20, Y + d)
        arrow(sh, "A-ANNO", 1.20, Y, 1.80, Y, head=0.15)
        sh.text("S-1", 2.05, Y, 0.14, rot=0.0)
    # dimensions + grid
    AX_Y = [7.5016, 13.5032, 18.806, 20.006]
    v_min, v_max = -0.25, 2.70
    us = [sh.E(0, 7.30)[0]] + [sh.E(0, Y)[0] for Y in AX_Y] + [sh.E(0, 20.254)[0]]
    for a, b in zip(us, us[1:]):
        sh.dim((a, v_min), (b, v_min), (a, v_min - 0.9), 0)
    sh.dim((us[0], v_min), (us[-1], v_min), (us[0], v_min - 1.6), 0)
    u_max = sh.E(0, 7.30)[0]
    vs = [v_min, 0.0, 2.500, v_max]
    for a, b in zip(vs, vs[1:]):
        sh.dim((u_max, a), (u_max, b), (u_max + 0.9, a), 90)
    R = 0.35
    for lab, Y in zip("2345", AX_Y):
        u = sh.E(0, Y)[0]
        msp.add_line((u, v_min - 2.6), (u, v_min - 0.2), dxfattribs={"layer": "A-GRID"})
        uu = u + (0.40 if lab == "5" else 0.0)
        msp.add_circle((uu, v_min - 2.6 - R), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, uu, v_min - 2.6 - R, 0.30, layer="A-GRID-IDEN")
    for lab, X in (("A", 0.0), ("B'", 2.50)):
        msp.add_line((u_max + 0.2, X), (u_max + 2.2, X), dxfattribs={"layer": "A-GRID"})
        msp.add_circle((u_max + 2.2 + R, X), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u_max + 2.2 + R, X, 0.28, layer="A-GRID-IDEN")
    sh.text_uv("PLAN - STAIR-HOUSE ROOF TOS +17.50  1:50", sh.E(0, 13.8)[0], v_min - 4.0, 0.22)
    sh.text_uv(fa("پلان بام خرپشته"), sh.E(0, 13.8)[0], v_min - 4.5, 0.28, farsi=True)

    # ---- section S-1 (cut at X = 1.20, looking towards axis A)
    def P(Y, Z):
        return (-Y + dx, Z - SEC_DZ)

    def box(layer, y0, y1, z0, z1):
        msp.add_lwpolyline([P(y0, z0), P(y1, z0), P(y1, z1), P(y0, z1)], close=True, dxfattribs={"layer": layer})

    def lev(s_, Y, Z, left=False):
        u, v = P(Y, Z)
        msp.add_lwpolyline([(u, v), (u - 0.09, v + 0.15), (u + 0.09, v + 0.15)], close=True, dxfattribs={"layer": "A-ANNO"})
        msp.add_line((u - 0.25, v), (u + 0.25, v), dxfattribs={"layer": "A-ANNO"})
        sh.text_uv(s_, u + (-0.15 if left else 0.15), v + 0.22, 0.10, align=TA.BOTTOM_RIGHT if left else TA.BOTTOM_LEFT)

    Y0 = 6.60
    for y0, y1 in ((Y0, 13.754), (15.553, 20.254)):                 # main roof slab +14.20 with the shaft opening
        box("A-WALL", y0, y1, 14.20 - 0.31, 14.20)
    for Y in (7.5016, 13.5032, 18.806):
        box("A-WALL", Y - 0.20, Y + 0.20, 13.70, 13.89)
    box("A-WALL", 19.806, 20.254, 13.70, 13.89)                    # edge beam axis 5
    box("A-WALL", 20.054, 20.254, 14.20, 15.40)                    # rear parapet 1.20 (existing)
    box("A-ROOF", 20.004, 20.304, 15.40, 15.45)                    # coping
    box("A-WALL", 7.55, 7.75, 14.20, 17.19)                        # stair-house front wall SH-2 (existing)
    box("A-WALL", 13.604, 13.754, 14.20, 17.10)                    # OV-F stair house / shaft (existing)
    box("A-WALL", 15.553, 15.703, 14.20, 17.19)                    # OV-R shaft back: T43 to u/s slab (overrun removed)
    box("A-WALL", 18.706, 18.906, 14.20, 14.53)                    # SH-4 (axis 4) with door DR2 (T47)
    box("A-DOOR", 18.706, 18.906, 14.53, 16.63)
    box("A-WALL", 18.706, 18.906, 16.63, 17.10)
    box("A-WALL", 7.55, 7.75, 17.50, 17.70)                        # curb front (existing)
    box("A-WALL", 20.054, 20.254, 17.50, 17.70)                    # curb rear (T43)
    for Y in (13.754, 15.553):
        msp.add_line(P(Y, 12.40), P(Y, 13.89), dxfattribs={"layer": "A-FLOR-OVHD"})
    sh.text_uv("LIFT SHAFT", P(14.65, 13.20)[0], P(14.65, 13.20)[1], 0.10)
    # T49 add. (boss): stair-house joists along X (span 2.30): S-1 (along Y) cuts across the ribs (schematic 0.10 @ 0.50)
    box("A-WALL", 7.30, 20.254, 17.44, 17.50)
    hh = msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
    hh.paths.add_polyline_path([P(7.30, 17.44), P(20.254, 17.44), P(20.254, 17.50), P(7.30, 17.50)], is_closed=True)
    msp.add_line(P(7.30, 17.19), P(20.254, 17.19), dxfattribs={"layer": "A-WALL"})
    yr = 7.30
    while yr < 20.254 - 1e-6:
        y2 = min(yr + 0.10, 20.254)
        box("A-WALL", yr, y2, 17.19, 17.44)
        hh = msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
        hh.paths.add_polyline_path([P(yr, 17.19), P(y2, 17.19), P(y2, 17.44), P(yr, 17.44)], is_closed=True)
        yr += 0.50
    sh.text_uv("JOISTS ALONG X (SPAN 2.30) - CUT ACROSS THE RIBS", P(10.4, 17.0)[0], P(10.4, 17.0)[1], 0.08)
    for Y in (7.5016, 13.5032, 18.806):
        box("A-WALL", Y - 0.20, Y + 0.20, 17.10, 17.19)
    box("A-WALL", 19.806, 20.254, 17.10, 17.19)
    for Y in (7.5016, 13.5032, 18.806):                            # columns beyond (axis A), +14.20 -> +17.10
        box("A-COLS", Y - 0.20, Y + 0.20, 14.20, 17.10)
    msp.add_line(P(8.958, 12.58), P(11.658, 14.28), dxfattribs={"layer": "A-STRS"})
    msp.add_line(P(7.75, 12.58), P(8.958, 12.58), dxfattribs={"layer": "A-STRS"})
    msp.add_line(P(11.658, 14.28), P(13.604, 14.28), dxfattribs={"layer": "A-STRS"})
    msp.add_line(P(Y0, 12.30), P(Y0, 18.10), dxfattribs={"layer": "A-ANNO"})   # break line
    sh.text_uv("STAIR HOUSE", P(10.40, 16.20)[0], P(10.40, 16.20)[1], 0.12)
    sh.text_uv(fa("خرپشته پله"), P(10.40, 15.85)[0], P(10.40, 15.85)[1], 0.14, farsi=True)
    sh.text_uv("EXTENSION T43", P(17.20, 16.20)[0], P(17.20, 16.20)[1], 0.12)
    sh.text_uv("(ENCLOSED)", P(17.20, 15.90)[0], P(17.20, 15.90)[1], 0.10)
    sh.text_uv("LIFT SHAFT", P(14.65, 16.00)[0], P(14.65, 16.00)[1], 0.10)
    sh.text_uv("OVERRUN REMOVED", P(14.60, 15.60)[0], P(14.60, 15.60)[1], 0.08)
    sh.text_uv("CANT. 1.20", P(19.41, 16.70)[0], P(19.41, 16.70)[1], 0.08)
    lev("+17.70", 20.70, 17.85)
    lev("+17.50", 21.40, 17.50)
    lev("+17.10 U/S BEAM", 21.40, 17.10)
    lev("+15.40", 20.70, 15.40)
    lev("+14.20 ROOF TOS", 21.40, 14.20)
    lev("+14.28", 12.80, 14.28, left=True)
    lev("+12.58", 8.40, 12.58, left=True)
    vb = 12.10 - SEC_DZ
    for a, b in zip([7.5016, 13.5032, 18.806], [13.5032, 18.806, 20.006]):
        sh.dim((-a + dx, vb), (-b + dx, vb), (-a + dx, vb), 0)
    for z0, z1, Yd in ((14.20, 17.10, 22.0), (17.10, 17.50, 22.0), (14.20, 17.19, 15.45)):
        uu = -Yd + dx
        sh.dim((uu, z0 - SEC_DZ), (uu, z1 - SEC_DZ), (uu, z0 - SEC_DZ), 90)
    for lab, Y in zip("2345", [7.5016, 13.5032, 18.806, 20.006]):
        u = -Y + dx
        msp.add_line((u, 13.75 - SEC_DZ), (u, 18.30 - SEC_DZ), dxfattribs={"layer": "A-GRID"})
        msp.add_circle((u, 18.30 - SEC_DZ + 0.30), 0.30, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u, 18.30 - SEC_DZ + 0.30, 0.25, layer="A-GRID-IDEN")
    sh.text_uv("SECTION S-1 (X = 1.20, LOOKING TO AXIS C)  1:50", P(13.8, 11.75)[0], P(13.8, 11.75)[1], 0.22)

    # ---- frame, legend, notes
    plan_cx = sh.E(0, 13.8)[0]
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa("برای تأیید - پلان بام خرپشته و برش") + " - " + REV,
                  f"STAIR-HOUSE ROOF PLAN TOS +17.50 + SECTION S-1  -  {REV} FOR APPROVAL  -  1:50  -  DIMENSIONS IN METRES", "A-106",
                  f"{REV} FOR APPROVAL (T43, boss 2026-10-31: roof to axis 5, cols C17 / C19, walls to axis 4, curb; T47 DR2, VS1, VP1/2, SP2)", plan_cx, 9.9)
    M.legend(sh, 4.6 + dx, 12.6)
    notes = [
        "STAIR-HOUSE ROOF NOTES (T43, boss 2026-10-31):",
        "S1. The stair-house roof (TOS +17.50, beams 40x40, u/s +17.10) continues in Y from axis 3 (13.50) to the end of the",
        "     cantilever, axis 5 (20.01), over the strip X 0.00 -> 2.35 / 2.50 (east beam on the C18 -> C19 line, as the beams below).",
        "S2. Two end columns added: C17 (0.00, 18.81) and C19 (2.50, 18.81), 40x40, reinforcement as C2 / C6 / C16 / C18 (12T16).",
        "S3. Boss approved: 20 cm walls (clear 2.90) on beams C16-C17 (boundary), C18-C19 and C17-C19 -> stair house closed to axis 4;",
        "     separate lift overrun removed, shaft walls (15 / 10 cm) continue to the underside of the stair-house roof.",
        "S4. Curb 0.20 x 0.20 (top +17.70) continued on the new edges (A side, east side, axis 5); old rear curb on axis 3 removed.",
        "S5. T47 (boss): door DR2 0.90 x 2.10 in SH-4 (sill +14.53); shaft vent VS1 0.60 x 0.30 in OV-B (+16.40 -> +16.70);",
        "     D-1 stack vents VP1 / VP2 dia 100 in sleeves dia 125 at X 0.28 (outside the axis-A beam), top +18.00; spout SP2 at Y ~19.80.",
        "S7. Joists of the stair-house roof: ALL along X (span 2.30), boss T49; other floors along Y (7.50).",
        "S6. Structural data: work/architecture/2026-10-31_T43_for_structural.md; coordination item 69.",
    ]
    sx0, yy = -28.2 + dx, -6.3
    for k, s_ in enumerate(notes):
        sh.text_uv(s_, sx0, yy - k * 0.26, 0.14 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
    return dict(slab_outline=SH_ROOF, new_columns=COL40[4:], notes=notes,
                curbs=[dict(id=c[4], x=c[:2], y=c[2:4], new=c[5], length=round(max(c[1] - c[0], c[3] - c[2]), 3)) for c in CURB],
                curb_removed=CURB_REMOVED, scope="boss T43 + approval 2026-10-31: walls to axis 4, overrun removed, curb on new edges")


# ---------------------------------------------------------------- T47: building sections A-201 (along Y) / A-202 (along X)
# Schematic architectural sections at 1:50 from the plan geometry (Rev.9-11): +-0.00 = top of foundation concrete,
# slabs 0.31, beams 0.50 (stair house 0.40), finish 0.08. Structural sizes per the structural drawings.
SL_TOS = [4.00, 7.40, 10.80, 14.20]
SL_T, BM, BM_SH, FIN_ = 0.31, 0.50, 0.40, 0.08
GAP_MM = 80                     # infill / frame separation gap (boss 2026-10-31, coordination 67/70)
ST_T = 0.20                     # T49 (boss): stair slab thickness
J_TOP, J_RIB, J_SP = 0.06, 0.10, 0.50   # joist slab 60 + 250 (ETABS deck TIRCHEH); rib width / spacing SCHEMATIC
SEC_V = 5.8                     # v = Z - SEC_V on both section sheets


class Sec:
    """Section drawing helper: h = coordinate along the cut (Y or X), u = s * h + c, v = Z - SEC_V."""

    def __init__(self, doc, s, c):
        self.msp, self.s, self.c = doc.modelspace(), s, c

    def P(self, h, z):
        return (self.s * h + self.c, z - SEC_V)

    def box(self, layer, h0, h1, z0, z1, fill=False):
        pts = [self.P(h0, z0), self.P(h1, z0), self.P(h1, z1), self.P(h0, z1)]
        self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        if fill:
            hh = self.msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
            hh.paths.add_polyline_path(pts, is_closed=True)

    def poly(self, layer, pts, close=True, fill=False):
        q = [self.P(h, z) for h, z in pts]
        self.msp.add_lwpolyline(q, close=close, dxfattribs={"layer": layer})
        if fill:
            hh = self.msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
            hh.paths.add_polyline_path(q, is_closed=True)

    def line(self, layer, h0, z0, h1, z1):
        self.msp.add_line(self.P(h0, z0), self.P(h1, z1), dxfattribs={"layer": layer})

    def text(self, s_, h, z, ht=0.15, farsi=False, align=TA.MIDDLE_CENTER, rot=0.0):
        u, v = self.P(h, z)
        t = self.msp.add_text(M.fa(s_) if farsi else s_, height=ht, rotation=rot,
                              dxfattribs={"layer": "A-ANNO", "style": "FARSI" if farsi else "LATIN", "width": 1.0 if farsi else 0.85})
        t.set_placement((u, v), align=align)

    def level(self, s_, h, z, ht=0.13, du=0.0):
        u, v = self.P(h, z)
        u += du
        self.msp.add_lwpolyline([(u, v), (u - 0.09, v + 0.15), (u + 0.09, v + 0.15)], close=True, dxfattribs={"layer": "A-ANNO"})
        self.msp.add_line((u - 0.30, v), (u + 0.30, v), dxfattribs={"layer": "A-ANNO"})
        t = self.msp.add_text(s_, height=ht, dxfattribs={"layer": "A-ANNO", "style": "LATIN", "width": 0.85})
        t.set_placement((u + 0.25, v + 0.05), align=TA.BOTTOM_LEFT)

    def vdim(self, h, z0, z1, du=0.0):
        u = self.P(h, 0)[0] + du
        d = self.msp.add_linear_dim(base=(u, z0 - SEC_V), p1=(u, z0 - SEC_V), p2=(u, z1 - SEC_V), angle=90, dimstyle="A100",
                                    text=f"{abs(z1 - z0):.2f}", dxfattribs={"layer": "A-DIMS"})
        d.render()

    def hdim(self, h0, h1, z):
        p1, p2 = self.P(h0, z), self.P(h1, z)
        d = self.msp.add_linear_dim(base=p1, p1=p1, p2=p2, angle=0, dimstyle="A100", text=f"{abs(h1 - h0):.2f}",
                                    dxfattribs={"layer": "A-DIMS"})
        d.render()

    def grid(self, lab, h, z0=-2.5, z1=18.2):
        u = self.P(h, 0)[0]
        self.msp.add_line((u, z0 - SEC_V), (u, z1 - SEC_V), dxfattribs={"layer": "A-GRID"})
        self.msp.add_circle((u, z0 - SEC_V - 0.40), 0.35, dxfattribs={"layer": "A-GRID-IDEN"})
        t = self.msp.add_text(lab, height=0.30, dxfattribs={"layer": "A-GRID-IDEN", "style": "LATIN", "width": 0.9})
        t.set_placement((u, z0 - SEC_V - 0.40), align=TA.MIDDLE_CENTER)


def _flight_down(f, y_top, riser, tread, n):
    """Cut flight rising towards -h: top profile from (y_top, f) up n risers; returns points."""
    pts = [(y_top, f)]
    y = y_top
    for k in range(1, n + 1):
        pts.append((y, f + riser * k))
        if k < n:
            y -= tread
            pts.append((y, f + riser * k))
    return pts, y


def _flight_up(f, y_bot, riser, tread, n):
    pts = [(y_bot, f)]
    y = y_bot
    for k in range(1, n + 1):
        pts.append((y, f + riser * k))
        if k < n:
            y += tread
            pts.append((y, f + riser * k))
    return pts


def _sheet_notes(sh, dx, extra):
    notes = [
        "SECTION NOTES (T47, boss 2026-10-31) - FOR APPROVAL, NOT FOR CONSTRUCTION:",
        "N1. +-0.00 = top of foundation concrete (ETABS Base). TOS = top of structural slab; FFL = TOS + 0.08. Sidewalk -0.07 (assumed).",
        "N2. Storeys = clear height + beam (boss T41): parking 3.50 + 0.50 = 4.00; floors 2.90 + 0.50 = 3.40; stair house 2.90 + 0.40 = 3.30.",
        "N3. Slabs 0.31, beams 0.50 (stair house 0.40), stair slab 0.20 (boss), landing beams 30x40 on axis 2: schematic, see structural drawings.",
        "N4. Stairs: parking 23 x 0.174 / 0.28 (12 + 11), half landing FFL +2.17; floors 20 x 0.170 / 0.30, half landings +5.78 / +9.18 / +12.58.",
        "N5. Lift: top stop FFL +10.88; shaft walls up to the stair-house roof (T43), hook under the roof slab; pit depth 2.00 (boss), bottom -2.00.",
        f"N6. Infill walls: separation gap {GAP_MM} mm to columns and beam soffits (boss 2026-10-31), compressible filler + sealant; ties per structural.",
        "N7. Roof: parapet 0.20 x 1.20 (+14.20 -> +15.40); stair-house roof +17.50 to axis 5 (cantilever 1.20), curb 0.20 (top +17.70).",
        "N8. Foundation drawn schematically (dashed); type and depth per structural / SAFE.",
        "N11. Slabs: joist slab 0.31 (topping 0.06 + block 0.25), JOISTS ALONG Y = the 7.50 span, L 8 m, 3 tie beams per span (boss T49); sizes per structural.",
        "      Stair-house roof +17.50: ALL joists along X = the 2.30 span (boss T49 add.). Rib size / spacing schematic.",
        "N10. Stair (structural, coordination 70): half-landing beam on column corbels with PTFE sliding pads, gap 40 to the columns;",
        "      stair slab sliding on beam B36 (axis 3) with gap 70. Details on the structural stair drawing.",
    ] + extra
    sx0, yy = -28.2 + dx, -10.6
    for k, s_ in enumerate(notes):
        sh.text_uv(s_, sx0, yy - k * 0.26, 0.14 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
    return notes


def joist_cut(S, h0, h1, t):
    """T49 (boss): joists along Y (7.50 span). In a cut along X the slab shows the topping + cut ribs + blocks (schematic)."""
    if h1 - h0 < 0.6:
        S.box("A-SECT", h0, h1, t - SL_T, t, fill=True)
        return
    S.box("A-SECT", h0, h1, t - J_TOP, t, fill=True)
    S.line("A-SECT-BYND", h0, t - SL_T, h1, t - SL_T)
    x = h0
    while x < h1 - 1e-6:
        xr = min(x + J_RIB, h1)
        S.box("A-SECT", x, xr, t - SL_T, t - J_TOP, fill=True)
        x += J_SP
    S.line("A-SECT-BYND", h1, t - SL_T, h1, t - J_TOP)


SPANS_Y = [(0.0, 7.5016), (7.5016, 13.5032), (13.5032, 18.806)]
TIE_W = 0.15                     # tie beam width SCHEMATIC (per structural); 3 tie beams per span (boss T49)


def joist_along(S, h0, h1, t, ties=True):
    """T49: cut along Y BETWEEN joists: topping 0.06 (filled), blocks (outline), 3 tie beams per span (filled, at the quarter points)."""
    S.box("A-SECT", h0, h1, t - J_TOP, t, fill=True)
    S.line("A-SECT-BYND", h0, t - SL_T, h1, t - SL_T)
    for a, b in (SPANS_Y if ties else []):
        for k in (1, 2, 3):
            yc = a + (b - a) * k / 4
            if h0 + TIE_W / 2 <= yc <= h1 - TIE_W / 2:
                S.box("A-SECT", yc - TIE_W / 2, yc + TIE_W / 2, t - SL_T, t - J_TOP, fill=True)
    for h in (h0, h1):
        S.line("A-SECT-BYND", h, t - SL_T, h, t - J_TOP)


def section_long(doc, dx):
    """A-201: longitudinal section at X = 1.20 (through stair flight B, lift shaft, stair house), looking to +X (axis B/C)."""
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    S = Sec(doc, -1.0, dx - 6.0)
    # ground, foundation (schematic), sidewalk, yard
    S.line("A-SECT", -1.30, -0.07, -0.25, -0.07)
    S.line("A-SECT", -0.25, -0.07, -0.25, 0.00)
    S.line("A-SECT", -0.25, 0.00, 22.556, 0.00)
    S.line("A-SECT-BYND", -0.25, 0.08, 19.056, 0.08)
    S.line("A-SECT-BYND", 19.056, 0.08, 22.356, 0.08)
    for z in (-0.60,):
        S.line("A-FLOR-OVHD", -0.25, z, 19.056, z)
    S.line("A-FLOR-OVHD", -0.25, 0.0, -0.25, -0.60)
    S.line("A-FLOR-OVHD", 19.056, 0.0, 19.056, -0.60)
    S.text("FOUNDATION PER STRUCTURAL (SCHEMATIC)", 4.0, -0.32, 0.12)
    for h in (13.754, 15.553):                                            # lift pit (supplier)
        S.line("A-FLOR-OVHD", h, 0.0, h, -2.00)
    S.line("A-FLOR-OVHD", 13.754, -2.00, 15.553, -2.00)
    S.level("PIT -2.00", 15.70, -2.00, ht=0.10)
    S.text("LIFT PIT 2.00 (BOSS)", 14.65, -1.20, 0.10)
    # floor slabs + beams (cut), voids: stair 7.75-11.658, shaft 13.754-15.553
    for t in SL_TOS:
        for h0, h1 in ((-0.25, 7.75), (11.658, 13.754), (15.553, 20.254)):
            joist_along(S, h0, h1, t)
        for yb in (0.0, 7.5016, 13.5032, 18.806, 20.006):
            h0, h1 = yb - 0.20, min(yb + 0.20, 20.254)
            S.box("A-SECT", h0, h1, t - BM, t - SL_T, fill=True)
        S.line("A-SECT-BYND", -0.25, t + FIN_, 7.75, t + FIN_) if t < 14.20 else None
        if t < 14.20:
            S.line("A-SECT-BYND", 11.658, t + FIN_, 13.604, t + FIN_)
            S.line("A-SECT-BYND", 15.703, t + FIN_, 20.054, t + FIN_)
    # stair-house roof +17.50 (Y 7.30 -> 20.254), beams 0.40, curbs
    joist_cut(S, 7.30, 20.254, 17.50)     # T49 add. (boss): stair-house joists along X (span 2.30) -> cut across the ribs here
    for yb in (7.5016, 13.5032, 18.806, 20.006):
        S.box("A-SECT", yb - 0.20, min(yb + 0.20, 20.254), 17.50 - BM_SH, 17.50 - SL_T, fill=True)
    S.box("A-WALL", 7.55, 7.75, 17.50, 17.70)
    S.box("A-WALL", 20.054, 20.254, 17.50, 17.70)
    # columns beyond (axis B line) per storey
    tops = [0.0] + SL_TOS
    for z0, z1 in zip(tops, tops[1:]):
        for yb in (0.0, 7.5016, 13.5032, 18.806):
            S.box("A-SECT-BYND", yb - 0.20, yb + 0.20, z0, z1 - BM)
    for yb in (7.5016, 13.5032, 18.806):
        S.box("A-SECT-BYND", yb - 0.20, yb + 0.20, 14.20, 17.50 - BM_SH)
    # ---- ground floor walls at X = 1.20
    S.box("A-DOOR", 0.25, 0.45, 0.08, 3.50)                            # DG2 door to u/s beam
    S.text("DG2", 0.35, 1.9, 0.10, rot=90.0)
    S.box("A-WALL", 7.65, 7.75, 0.0, 3.50)                             # W21
    S.box("A-WALL", 13.604, 13.754, 2.08, 3.50)                        # W19 above DL1
    S.box("A-DOOR", 13.604, 13.754, 0.08, 2.08)
    S.box("A-WALL", 15.553, 15.703, 0.0, 4.00 - SL_T)                  # W17
    S.box("A-WALL", 16.60, 16.70, 0.0, 4.00 - SL_T)                    # G-S2
    S.box("A-WALL", 17.65, 17.75, 0.0, 4.00 - SL_T)                    # G-S3
    S.box("A-WALL", 18.856, 19.056, 0.0, 1.58)                         # G-R1 + WG3
    S.box("A-GLAZ", 18.856, 19.056, 1.58, 2.98)
    S.box("A-WALL", 18.856, 19.056, 2.98, 3.50)
    S.box("A-WALL", 20.356, 20.506, 0.0, 2.50)                         # yard pump room
    S.box("A-WALL", 22.356, 22.556, 0.0, 2.50)
    S.line("A-SECT-BYND", 20.356, 2.50, 22.556, 2.50)
    # ---- typical floors 1-3 walls
    for t in SL_TOS[:3]:
        f, T = t + FIN_, t + 3.40
        S.line("A-FLOR-HRAL", -0.20, t, -0.20, f + 1.10)
        S.line("A-FLOR-HRAL", -0.25, f + 1.10, -0.15, f + 1.10)
        S.box("A-DOOR", 0.75, 0.95, f, T - SL_T)                        # W22 steel door
        S.box("A-WALL", 7.65, 7.75, t, T - BM)                          # W21
        S.box("A-WALL", 13.604, 13.754, f + 2.00, T - BM)               # W19 above DL1
        S.box("A-DOOR", 13.604, 13.754, f, f + 2.00)
        S.box("A-WALL", 15.553, 15.703, t, T - SL_T)                    # W17
        S.box("A-WALL", 18.856, 19.056, t, f + 0.70)                    # W5c + WN2 window to u/s beam
        S.box("A-GLAZ", 18.856, 19.056, f + 0.70, T - BM)
        S.box("A-WALL", 20.054, 20.254, t, f + 1.10)                    # W4 parapet
    # ---- roof
    S.box("A-WALL", -0.25, -0.05, 14.20, 15.40)                         # front parapet
    S.box("A-ROOF", -0.30, 0.00, 15.40, 15.45)
    S.box("A-WALL", 20.054, 20.254, 14.20, 15.40)                       # rear parapet
    S.box("A-ROOF", 20.004, 20.304, 15.40, 15.45)
    S.line("A-SECT-BYND", -0.05, 14.32, 7.55, 14.32)
    S.line("A-SECT-BYND", 18.906, 14.32, 20.054, 14.32)
    S.line("A-SECT-BYND", 11.658, 14.28, 13.604, 14.28)
    S.box("A-WALL", 7.55, 7.75, 14.20, 17.50 - SL_T)                    # SH-2
    S.box("A-WALL", 13.604, 13.754, 14.20, 17.50 - BM_SH)               # OV-F
    S.box("A-WALL", 15.553, 15.703, 14.20, 17.50 - SL_T)                # OV-R (T43 to u/s slab)
    S.box("A-WALL", 18.706, 18.906, 14.20, 14.53)                       # SH-4 + door DR2 (T47)
    S.box("A-DOOR", 18.706, 18.906, 14.53, 16.63)
    S.box("A-WALL", 18.706, 18.906, 16.63, 17.50 - BM_SH)
    S.text("DR2", 18.45, 15.60, 0.10, rot=90.0)
    # ---- stairs: flight B cut (X 1.20), flight A beyond
    # parking: B 12 x 0.1739 / 0.28 from Y 12.038 (FFL +0.08) to the half landing Y 8.958 (+2.17)
    rg = (4.08 - 0.08) / 23
    pts, yl = _flight_down(0.08, 12.038, rg, 0.28, 12)
    zl = 0.08 + 12 * rg
    # T49 (boss): stair slab 0.20 -> waist 0.20 / cos 0.850 = 0.235 below the root line, landing 0.20
    S.poly("A-SECT", pts + [(7.50, zl), (7.50, zl - FIN_ - ST_T), (8.958, zl - FIN_ - ST_T), (8.958, 1.758), (11.788, 0.0), (12.038, 0.0)],
           fill=True)
    S.box("A-SECT", 7.35, 7.65, zl - FIN_ - 0.40, zl - FIN_ - ST_T, fill=True)    # landing beam 30x40
    S.poly("A-SECT-BYND", _flight_up(zl, 8.958, rg, 0.28, 11), close=False)
    S.level(f"+{zl:.2f}", 8.20, zl, ht=0.10)
    for t in SL_TOS[:3]:
        f = t + FIN_
        pts, yl = _flight_down(f, 11.658, 0.170, 0.30, 10)
        zl = f + 1.70
        S.poly("A-SECT", pts + [(7.50, zl), (7.50, zl - FIN_ - ST_T), (8.958, zl - FIN_ - ST_T), (8.958, f + 1.30),
                                (11.658, f - 0.230)], fill=True)          # waist 0.20 / cos 0.870 = 0.230
        S.box("A-SECT", 7.35, 7.65, zl - FIN_ - 0.40, zl - FIN_ - ST_T, fill=True)
        S.poly("A-SECT-BYND", _flight_up(zl, 8.958, 0.170, 0.30, 10), close=False)
        S.level(f"+{zl:.2f}", 8.20, zl, ht=0.10)
        S.text("SLIDING SEAT (N10)", 7.50, zl - 0.75, 0.07)
    # ---- lift: car at the top stop (dashed), hook under the stair-house roof
    S.box("A-FLOR-OVHD", 13.95, 15.35, 10.88, 13.18)
    S.text("LIFT CAR AT TOP STOP +10.88", 14.65, 12.0, 0.08, rot=90.0)
    S.line("A-ELEV", 14.65, 17.19, 14.65, 16.95)
    S.text("HOOK", 14.65, 16.80, 0.08)
    S.text("LIFT SHAFT", 14.65, 15.6, 0.10, rot=90.0)
    # ---- labels
    for t, nm, nf in ((0.0, "PARKING", "پارکينگ"), (4.0, "FLOOR 1", "طبقه اول"), (7.4, "FLOOR 2", "طبقه دوم"), (10.8, "FLOOR 3", "طبقه سوم")):
        S.text(nm, 4.0, t + 1.9, 0.18)
        S.text(nf, 4.0, t + 1.5, 0.20, farsi=True)
        S.text("STAIR", 10.3, t + 2.9, 0.12)
    S.text("STORAGES S1-S3", 17.25, 1.2, 0.10)
    S.text("YARD +0.08", 21.4, 0.5, 0.12)
    S.text("PUMP ROOM", 21.4, 1.4, 0.10)
    for t in SL_TOS[:3]:
        S.text("ROOM", 17.2, t + 1.9, 0.12)
        S.text("BALC.", 19.55, t + 0.6, 0.10)
        S.text("TERR.", 0.25, t + 0.6, 0.09)
    S.text("ROOF", 4.0, 15.0, 0.18)
    S.text("بام", 4.0, 14.65, 0.20, farsi=True)
    S.text("STAIR HOUSE", 10.6, 16.2, 0.14)
    S.text("خرپشته", 10.6, 15.8, 0.18, farsi=True)
    S.text("ENCLOSED (T43)", 17.2, 16.0, 0.10)
    S.text("CANT. 1.20", 19.40, 16.6, 0.09)
    S.text("STREET", -0.85, 0.55, 0.10)
    S.text("JOIST SLAB 0.31: JOISTS ALONG Y (7.50 SPAN, L 8 m) - CUT BETWEEN JOISTS; 3 TIE BEAMS ACROSS (ALONG X) PER SPAN", 4.0, 4.00 - 0.55, 0.08)
    # ---- levels (right of the front face) + dimension chains
    levs = [(0.00, "+-0.00 FDN TOP / FFL +0.08"), (4.00, "TOS +4.00 / FFL +4.08"), (7.40, "TOS +7.40 / FFL +7.48"),
            (10.80, "TOS +10.80 / FFL +10.88"), (14.20, "ROOF TOS +14.20"), (15.40, "PARAPET +15.40"),
            (17.10, "U/S BEAM +17.10"), (17.50, "S.H. ROOF TOS +17.50"), (17.70, "CURB +17.70")]
    for z, s_ in levs:
        S.level(s_, -1.0, z, ht=0.12, du=1.6)
    S.level("SIDEWALK -0.07", -0.80, -0.07, ht=0.10, du=0.0)
    chain = [0.0, 4.00, 7.40, 10.80, 14.20, 17.50, 17.70]
    for a, b in zip(chain, chain[1:]):
        S.vdim(-0.25, a, b, du=0.70)
    S.vdim(-0.25, 0.0, 17.70, du=1.40)
    S.vdim(-0.25, 14.20, 15.40, du=-0.30) if False else None
    for a, b in ((0.08, 3.50), (4.08, 6.90)):
        S.vdim(5.0, a, b)
    S.text("CLEAR 3.42 (FFL -> U/S BEAM)", 5.35, 1.9, 0.08, rot=90.0)
    S.text("CLEAR 2.82", 5.35, 5.5, 0.08, rot=90.0)
    ys = [-0.25, 0.0, 7.5016, 13.5032, 18.806, 20.006, 20.254]
    for a, b in zip(ys, ys[1:]):
        S.hdim(a, b, -2.25)
    for lab, yb in zip("12345", (0.0, 7.5016, 13.5032, 18.806, 20.006)):
        S.grid(lab, yb)
    u_c = S.P(10.0, 0)[0]
    sh.text_uv("LONGITUDINAL SECTION 1-1 (X = 1.20, THROUGH STAIR, LIFT AND STAIR HOUSE, LOOKING TO AXIS C)  1:50",
               u_c, -9.45, 0.25)
    sh.text_uv(fa("برش طولى ۱-۱"), u_c, -10.0, 0.32, farsi=True)
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa("برای تأیید - برش طولى ساختمان ۱-۱") + " - " + REV,
                  f"LONGITUDINAL SECTION 1-1 (X = 1.20)  -  {REV} FOR APPROVAL  -  1:50  -  DIMENSIONS IN METRES", "A-201",
                  f"{REV} FOR APPROVAL (T47, boss 2026-10-31): section along Y, foundation top to the stair-house curb +17.70",
                  u_c, 10.55)
    M.legend(sh, 4.6 + dx, 12.6)
    return _sheet_notes(sh, dx, ["N9. Section line 1-1 on plans A-101 ... A-106 at X = 1.20; T47 door DR2 in wall SH-4 (axis 4) cut here."])


def section_trans(doc, dx):
    """A-202: transverse section at Y = 10.30 (through both stair flights, corridor, WC, duct D-2), looking to +Y (rear)."""
    fa, REV = M.fa, M.REV
    sh = M.Sheet(doc, dx)
    S = Sec(doc, 1.0, dx - 20.0)
    S.line("A-SECT", -1.0, 0.0, 8.15, 0.0)
    S.line("A-SECT-BYND", -0.25, 0.08, 7.40, 0.08)
    S.line("A-FLOR-OVHD", -0.25, -0.60, 7.40, -0.60)
    for h in (-0.25, 7.40):
        S.line("A-FLOR-OVHD", h, 0.0, h, -0.60)
    S.text("FOUNDATION PER STRUCTURAL (SCHEMATIC)", 3.6, -0.32, 0.12)
    # slabs: stair void X -0.05..2.25; duct D-2 void X 6.752..7.20 at +7.40 / +10.80 / +14.20
    for t in SL_TOS:
        segs = [(-0.25, -0.05), (2.25, 6.752 if t > 4.0 else 7.40)] + ([(7.20, 7.40)] if t > 4.0 else [])
        for h0, h1 in segs:
            joist_cut(S, h0, h1, t)
        for xb, (h0, h1) in ((0.0, (-0.25, 0.20)), (2.3486, (2.149, 2.549)), (7.15, (6.95, 7.40))):
            S.box("A-SECT", h0, h1, t - BM, t - SL_T, fill=True)
        if t < 14.20:
            S.line("A-SECT-BYND", 2.40, t + FIN_, 7.20, t + FIN_)
    joist_along(S, -0.25, 2.55, 17.50, ties=False)   # T49 add.: stair-house joists along X -> cut between joists (no tie beams)
    # T49: lift pit 2.00 beyond the cut (shaft X 0.449-2.449 at Y 13.75-15.55), dashed
    for h in (0.449, 2.449):
        S.line("A-FLOR-OVHD", h, 0.0, h, -2.00)
    S.line("A-FLOR-OVHD", 0.449, -2.00, 2.449, -2.00)
    S.text("LIFT PIT 2.00 BEYOND (BOSS)", 1.45, -1.20, 0.09)
    S.level("PIT -2.00", 2.60, -2.00, ht=0.10)
    S.text("JOIST SLAB 0.31: JOISTS ALONG Y (7.50 SPAN) - CUT ACROSS THE RIBS; TIE BEAMS ALONG X PER STRUCTURAL", 4.70, 4.00 - 0.55, 0.08)
    for h0, h1 in ((-0.25, 0.20), (2.149, 2.549)):
        S.box("A-SECT", h0, h1, 17.50 - BM_SH, 17.50 - SL_T, fill=True)
    S.box("A-WALL", -0.25, -0.05, 17.50, 17.70)
    S.box("A-WALL", 2.25, 2.45, 17.50, 17.70)
    # columns beyond (axis 3)
    tops = [0.0] + SL_TOS
    for z0, z1 in zip(tops, tops[1:]):
        for h0, h1 in ((-0.20, 0.20), (2.149, 2.549), (6.95, 7.35)):
            S.box("A-SECT-BYND", h0, h1, z0, z1 - BM)
    for h0, h1 in ((-0.20, 0.20), (2.149, 2.549)):
        S.box("A-SECT-BYND", h0, h1, 14.20, 17.50 - BM_SH)
    # walls cut at Y = 10.30
    for h0, h1 in ((-0.25, -0.05), (2.25, 2.40), (7.20, 7.40)):
        S.box("A-WALL", h0, h1, 0.0, 4.00 - BM)                      # ground: G-A2, W24, G-C2
    for t in SL_TOS[:3]:
        T = t + 3.40
        for h0, h1 in ((-0.25, -0.05), (2.25, 2.40), (7.20, 7.40)):
            S.box("A-WALL", h0, h1, t, T - BM)                         # W2c, W24, W1c (on beams)
        for h0, h1 in ((3.958, 4.108), (5.303, 5.403), (6.602, 6.752)):
            S.box("A-WALL", h0, h1, t, T - SL_T)                       # W15, W12, W11 (on the slab)
        S.text("CORRIDOR", 3.18, t + 1.6, 0.11)
        S.text("LOBBY", 4.70, t + 1.6, 0.11)
        S.text("WC-1", 6.00, t + 1.6, 0.11)
        S.text("D-2", 6.98, t + 2.4, 0.09)
        S.text("STAIR", 1.10, t + 3.0, 0.11)
    # roof
    S.box("A-WALL", -0.25, -0.05, 14.20, 17.50 - BM_SH)                 # stair-house wall, A (boundary)
    S.box("A-WALL", 2.25, 2.45, 14.20, 17.50 - BM_SH)                   # SH-B
    S.box("A-WALL", 7.20, 7.40, 14.20, 15.40)                           # parapet C
    S.box("A-ROOF", 7.15, 7.45, 15.40, 15.45)
    S.line("A-SECT-BYND", 2.45, 14.32, 7.20, 14.32)
    S.box("A-ROOF", 6.753, 7.20, 14.32, 15.03)                          # D-2 cap
    S.text("D-2 CAP", 6.30, 15.2, 0.08)
    # stairs cut at Y = 10.30: flight B (X 1.15-2.25) and A (X -0.05-1.05)
    rg = (4.08 - 0.08) / 23
    S.box("A-SECT", 1.15, 2.25, 0.924, 0.08 + 7 * rg, fill=True)                 # T49: stair slab 0.20
    S.box("A-SECT", -0.05, 1.05, 2.766, 0.08 + 12 * rg + 5 * rg, fill=True)
    for t in SL_TOS[:3]:
        f = t + FIN_
        S.box("A-SECT", 1.15, 2.25, f + 0.54, f + 0.85, fill=True)
        S.box("A-SECT", -0.05, 1.05, f + 2.23, f + 2.55, fill=True)
    S.text("PARKING  P3", 5.65, 1.9, 0.16)
    S.text("پارکينگ", 5.65, 1.5, 0.20, farsi=True)
    S.text("STAIR HOUSE", 1.10, 16.2, 0.12)
    S.text("خرپشته", 1.10, 15.8, 0.16, farsi=True)
    S.text("ROOF", 4.80, 15.0, 0.16)
    S.text("بام", 4.80, 14.65, 0.18, farsi=True)
    for h in (-0.75, 7.90):
        S.text("NEIGHBOUR", h, 8.0, 0.12, rot=90.0)
        S.text("همسايه", h + 0.25, 8.0, 0.14, farsi=True, rot=90.0)
    levs = [(0.00, "+-0.00 FDN TOP / FFL +0.08"), (4.00, "TOS +4.00 / FFL +4.08"), (7.40, "TOS +7.40 / FFL +7.48"),
            (10.80, "TOS +10.80 / FFL +10.88"), (14.20, "ROOF TOS +14.20"), (15.40, "PARAPET +15.40"),
            (17.10, "U/S BEAM +17.10"), (17.50, "S.H. ROOF TOS +17.50"), (17.70, "CURB +17.70")]
    for z, s_ in levs:
        S.level(s_, 7.40, z, ht=0.12, du=2.4)
    chain = [0.0, 4.00, 7.40, 10.80, 14.20, 15.40]
    for a, b in zip(chain, chain[1:]):
        S.vdim(7.40, a, b, du=0.9)
    S.vdim(7.40, 0.0, 17.70, du=1.6)
    for a, b in ((14.20, 17.50), (17.50, 17.70)):
        S.vdim(-0.25, a, b, du=-0.6)
    xs = [-0.25, 0.0, 2.3486, 7.15, 7.40]
    for a, b in zip(xs, xs[1:]):
        S.hdim(a, b, -2.25)
    for lab, xb in (("A", 0.0), ("B", 2.3486), ("C", 7.15)):
        S.grid(lab, xb)
    u_c = S.P(3.6, 0)[0]
    sh.text_uv("TRANSVERSE SECTION 2-2 (Y = 10.30, THROUGH BOTH STAIR FLIGHTS, LOOKING TO AXIS 3)  1:50", u_c, -9.45, 0.25)
    sh.text_uv(fa("برش عرضى ۲-۲"), u_c, -10.0, 0.32, farsi=True)
    M.sheet_frame(sh, -29.5 + dx, -15.2, fa("برای تأیید - برش عرضى ساختمان ۲-۲") + " - " + REV,
                  f"TRANSVERSE SECTION 2-2 (Y = 10.30)  -  {REV} FOR APPROVAL  -  1:50  -  DIMENSIONS IN METRES", "A-202",
                  f"{REV} FOR APPROVAL (T47, boss 2026-10-31): section along X, foundation top to the stair-house curb +17.70",
                  u_c, 10.55)
    M.legend(sh, 4.6 + dx, 12.6)
    return _sheet_notes(sh, dx, ["N9. Section line 2-2 on plans A-101 ... A-106 at Y = 10.30, looking to the rear (axis 3)."])


def section_marks(doc, offsets):
    """Section lines 1-1 (X = 1.20) and 2-2 (Y = 10.30) on every plan sheet (model-space offsets)."""
    for dx in offsets:
        sh = M.Sheet(doc, dx)
        for Y, d in ((-0.75, 0.6), (23.0, -0.6)):
            sh.line("A-ANNO", 1.20, Y, 1.20, Y + d)
            arrow(sh, "A-ANNO", 1.20, Y, 1.85, Y, head=0.18)
            sh.text("1", 0.80, Y, 0.22, rot=0.0)
        for X, d in ((-0.65, 0.35), (7.85, -0.35)):
            sh.line("A-ANNO", X, 10.30, X + d, 10.30)
            arrow(sh, "A-ANNO", X, 10.30, X, 10.95, head=0.18)
            sh.text("2", X, 11.20, 0.22, rot=0.0)


def section_sheets(doc, dxl, dxt):
    n1 = section_long(doc, dxl)
    n2 = section_trans(doc, dxt)
    return dict(long=dict(sheet="A-201", cut="X = 1.20, looking to +X", notes=n1),
                trans=dict(sheet="A-202", cut="Y = 10.30, looking to +Y", notes=n2), infill_gap_mm=GAP_MM)


# ---------------------------------------------------------------- layouts
def add_layouts(doc, sheets, ctb):
    """sheets: {sheet_no: (layout_name, [x0, y0, x1, y1] model window of the A3 frame)}"""
    if "A-ANNO-NPLT" in doc.layers:
        doc.layers.get("A-ANNO-NPLT").dxf.plot = 0
    for no, (name, (x0, y0, x1, y1)) in sheets.items():
        lay = doc.layouts.new(name)
        lay.page_setup(size=(841, 594), margins=(0, 0, 0, 0), units="mm", offset=(0, 0), rotation=0, scale=1,
                       name=A1_MEDIA, device="DWG To PDF.pc3")
        lay.dxf_layout.dxf.current_style_sheet = ctb
        vp = lay.add_viewport(center=(420.5, 297), size=(841, 594), view_center_point=((x0 + x1) / 2, (y0 + y1) / 2),
                              view_height=(y1 - y0), dxfattribs={"layer": "A-ANNO-NPLT"})
        vp.dxf.flags = vp.dxf.flags | 16384          # display locked
    for nm in list(doc.layouts.names()):
        if nm.lower().startswith("layout"):
            doc.layouts.delete(nm)
