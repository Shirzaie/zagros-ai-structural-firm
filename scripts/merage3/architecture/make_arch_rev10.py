# -*- coding: utf-8 -*-
"""Merage3 architecture Rev.7 (tasks 35 + 36, 2026-10-23).

T35: thin, normal line weights (walls 0.25, doors / glazing / stairs / dims 0.13, grid / fill 0.09, text 0.18,
     border 0.35) set on the layers AND in a colour-dependent plot style Zagros_ARCH_Rev7.ctb.
T36: drawings "typical for 3 storeys over parking" with standard layers:
     A-101 ground floor / parking plan (new, assumptions listed on the sheet)
     A-102 typical floor plan, floors 1-3 (= Rev.6 FINAL geometry, unchanged; only layers, weights, titles, notes)

The Rev.6 final files in arch/ are NOT touched. The Rev.6 geometry is regenerated in a temp folder from an
unchanged copy of its generator (rev6_source.py), then re-layered here; the ground floor is drawn in ETABS
metres (X across A->C, Y along 1->4). DWG coordinates: u = -Y + DX, v = X.

T37 (boss decisions 2026-10-23): ground stair 20 risers x 0.175 (= typical stair geometry, 10 treads 0.30 per
     flight, half landing +1.75, flights 1.10); 3 tandem stalls kept; rear yard at +-0.00, ~3.50 deep (approx., to be
     checked with the deed); C19 = 2.500 / grid B' approved; note A11 = structural proposal (coordination 57):
     half landing +1.75 on an independent support from the foundation, 2-3 cm gap to the columns (pending boss).

T39 (boss 2026-10-23) -> Rev.8 DRAFT:
     - entry niche depth 0.50 (was 0.80): door wall G-F1 right behind the column faces A1 / B1 (Y 0.25-0.45);
       the side returns G-N1 / G-N2 disappear (the column faces are the niche sides); P1 moved 0.25 forward.
     - a proper sedan car block (CAR_SEDAN, 1.80 x 4.50, layer A-PRKG-CARS, grey) in P1, P2, P3.
     - ONE DWG with 5 separate titled sheets, each also a named paper-space layout:
       A-101 parking (ground) +-0.00, A-102 floor 1 +3.50, A-103 floor 2 +6.40, A-104 floor 3 +9.30, A-105 roof.

T40 (boss 2026-10-23): levels from the TOP OF FOUNDATION CONCRETE (+-0.00 = ETABS Base); parking storey 3.50,
     typical 2.90, beams 0.50; stair house beams 0.40, columns 2.90, 20 cm curb 0.20 high on its roof; main-roof
     parapet 20 cm x 1.20 high (from the top of the roof slab). Levels on the sheets: TOS (structural, top of slab)
     and FFL (= TOS + 0.08 finish). Parking FFL +0.08, sidewalk -0.07 (assumed = parking FFL - 0.15).

T41 (boss 2026-10-24) -> Rev.9 DRAFT: the boss's heights are CLEAR heights (top of the concrete below = foundation
     or slab, to the underside of the beam); storey = clear + beam. Parking 3.50 + 0.50 = 4.00, floors 1-3
     2.90 + 0.50 = 3.40, stair house 2.90 + 0.40 = 3.30. TOS: floor 1 +4.00, floor 2 +7.40, floor 3 +10.80,
     roof +14.20, stair-house roof +17.50; FFL = TOS + 0.08 (parking FFL +0.08). Rev.8 levels were wrong.
     Stairs redesigned: parking 23 risers x 0.1739 (12 + 11), treads 0.28 (2h+b 0.628), half landing FFL +2.17;
     floors 20 risers x 0.170 (10 + 10), treads 0.30 (2h+b 0.64), half landings +5.78 / +9.18 / +12.58;
     flights 1.10, half landings on the stair columns (axis 2). Roof parapet 0.20 x 1.20 (+14.20 -> +15.40),
     stair house roof +17.50 with curb 0.20 x 0.20 (top +17.70), lift overrun slab TOS +14.90 (assumed).

T43 (boss 2026-10-31) -> Rev.10 DRAFT: the stair-house roof (TOS +17.50) continues in Y from axis 3 (13.50) to the end
     of the cantilever (axis 5, 20.01) over the strip X 0.00..2.35/2.50; 2 new stair-house columns on C17 / C19 (40x40,
     12T16). Boss approval (same day): 20 cm walls clear 2.90 on beams C16-C17, C18-C19, C17-C19 (stair house closed to
     axis 4); separate lift overrun removed, shaft walls to the u/s of the stair-house roof; curb 0.20 x 0.20 on the new
     roof edges; no new doors / windows. New sheet A-106 = stair-house roof plan + section S-1.
     Boss decision 7 (2026-10-31): parking FFL +0.08, parking stair 23 x 0.174, overhead 3.87 approved.

    python make_arch_rev10.py   -> arch/Merage3_arch_Rev10.dwg (+ PDFs via plot_rev10.py)
"""
import json
import math
import os
import subprocess

import ezdxf
from ezdxf.addons import acadctb
from ezdxf.enums import TextEntityAlignment as TA

from rev9_source import build_rev6, TMP
import rev10_sheets as rev8_sheets

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", ".."))
ARCH = os.path.join(PRJ, "arch")
OUT_DWG = os.path.join(ARCH, "Merage3_arch_Rev10.dwg")
OUT_JSON = os.path.join(ARCH, "Merage3_arch_Rev10_ground_geometry.json")
CTB_NAME = "Zagros_ARCH_Rev7.ctb"
CTB_DIR = os.path.join(os.environ["APPDATA"], "Autodesk", "AutoCAD 2026", "R25.1", "enu", "Plotters", "Plot Styles")
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
REV = "Rev.10"
DATE = "1405/08/09"
C19_X = 2.500                   # T33 (structural, coordination 55): grid B' = 2.50, C19 moved from 2.507 (boss approved 2026-10-23)
C19_OLD = 2.507
DXG = -45.0                     # ground-floor sheet offset in model space (left of the typical sheet)
# T39: sheets (model-space offset of each plan, sheet no., layout name, level)
FLOORS = [(0.0, "A-102", "A-102_FLOOR-1", "FLOOR 1", "طبقه ی اول", 4.00, "P3"),
          (45.0, "A-103", "A-103_FLOOR-2", "FLOOR 2", "طبقه ی دوم", 7.40, "P2"),
          (90.0, "A-104", "A-104_FLOOR-3", "FLOOR 3", "طبقه ی سوم", 10.80, "P1")]
DXR = 135.0                     # roof sheet offset
DXS = 180.0                     # T43: stair-house roof sheet offset
SHEETS = {"A-101": (DXG, "A-101_PARKING"), "A-102": (0.0, "A-102_FLOOR-1"), "A-103": (45.0, "A-103_FLOOR-2"),
          "A-104": (90.0, "A-104_FLOOR-3"), "A-105": (DXR, "A-105_ROOF"),
          "A-106": (DXS, "A-106_STAIR-HOUSE-ROOF")}


def sheet_window(dx):
    return [-29.5 + dx, -15.2, 12.5 + dx, 14.5]

# ---------------------------------------------------------------- T35: layers (colour, linetype, lw 1/100 mm)
# colour -> plot lineweight in the CTB (same as the layer lineweight)
CTB_LW = {1: 0.13, 2: 0.18, 3: 0.25, 4: 0.13, 5: 0.09, 6: 0.35, 7: 0.18, 8: 0.09, 9: 0.09}
LAYERS = {
    "A-WALL": (3, "CONTINUOUS", 25, "Walls, cut (20/15/10 cm)"),
    "A-COLS": (3, "CONTINUOUS", 25, "Concrete columns, outline"),
    "A-COLS-PATT": (8, "CONTINUOUS", 9, "Concrete columns, solid fill"),
    "A-DOOR": (1, "CONTINUOUS", 13, "Doors, leaves and swings, gates"),
    "A-GLAZ": (1, "CONTINUOUS", 13, "Windows, glazing, vents"),
    "A-STRS": (4, "CONTINUOUS", 13, "Stairs below the cut plane"),
    "A-STRS-OVHD": (5, "HIDDEN", 9, "Stairs above the cut plane (dashed)"),
    "A-FLOR-OVHD": (5, "HIDDEN", 9, "Overhead outlines (balcony above)"),
    "A-FLOR-HRAL": (4, "CONTINUOUS", 13, "Railings and guards"),
    "A-ELEV": (4, "CONTINUOUS", 13, "Elevator shaft symbol"),
    "A-SHFT": (4, "CONTINUOUS", 13, "Ducts and shafts"),
    "A-PRKG": (1, "CONTINUOUS", 13, "Parking stall striping"),
    "A-EQPM": (9, "CONTINUOUS", 9, "Equipment: tank, booster, meters, grey"),
    "A-DIMS": (1, "CONTINUOUS", 13, "Dimensions"),
    "A-ANNO": (2, "CONTINUOUS", 18, "Text: titles, room names, notes, levels"),
    "A-ANNO-IDEN": (1, "CONTINUOUS", 13, "Door / window tags"),
    "A-ANNO-TABL": (1, "CONTINUOUS", 13, "Schedule and legend table lines"),
    "A-GRID": (5, "CENTER", 9, "Structural grid lines"),
    "A-GRID-IDEN": (2, "CONTINUOUS", 18, "Grid bubbles and labels"),
    "A-ANNO-TTLB": (7, "CONTINUOUS", 18, "Title block and sheet trim"),
    "A-ANNO-BRDR": (6, "CONTINUOUS", 35, "Drawing border"),
    "A-SITE-PROP": (6, "PHANTOM", 25, "Property line (rear: approx., check with the deed)"),
    "A-PRKG-OPTN": (1, "HIDDEN", 13, "Parking stall, option only (dashed)"),
    "A-PRKG-CARS": (9, "CONTINUOUS", 9, "Cars: sedan symbol (block CAR_SEDAN 1.80 x 4.50), grey"),
    "A-ROOF": (4, "CONTINUOUS", 13, "Roof: coping line, upstands, duct caps, equipment pads"),
    "A-ROOF-DRAN": (1, "CONTINUOUS", 13, "Roof drains and downpipes"),
    "A-ROOF-SLOP": (1, "CONTINUOUS", 13, "Roof slope arrows (2%)"),
    "A-ROOF-RIDG": (5, "HIDDEN", 9, "Roof ridge / catchment lines (dashed)"),
    "A-ANNO-NPLT": (8, "CONTINUOUS", 9, "Viewport frames (not plotted)"),
}
OLD2NEW = {"A-WALL": "A-WALL", "A-STAIR": "A-STRS", "A-ELEV": "A-ELEV", "A-SHAFT": "A-SHFT",
           "A-OPENING": "A-GLAZ", "A-RAIL": "A-FLOR-HRAL", "A-DOOR": "A-DOOR", "A-DIM": "A-DIMS"}
TAGS = {"WN1", "WN2", "DW1", "D1", "D2", "D3", "D4", "DS1", "DL1", "DE1"}

# ---------------------------------------------------------------- ground floor (ETABS metres)
COLS = None   # filled from the Rev.6 geometry (columns_etabs)
H_GROUND, H_TYP, H_SH = 4.00, 3.40, 3.30     # T41 (boss): storey = clear height + beam
CLEAR_GROUND, CLEAR_TYP, CLEAR_SH = 3.50, 2.90, 2.90
# T40 (boss): +-0.00 = top of the foundation concrete (= ETABS Base); beams 0.50 (stair house 0.40); finish 0.08
FIN, BEAM, BEAM_SH, SLAB = 0.08, 0.50, 0.40, 0.31
# (name, farsi, TOS = structural top of slab / foundation, FFL or finished level text)
LEVELS = [("FOUNDATION TOP / PARKING", "روى پى - پارکينگ", 0.00, "+0.08"), ("FLOOR 1", "طبقه ى اول", 4.00, "+4.08"),
          ("FLOOR 2", "طبقه ى دوم", 7.40, "+7.48"), ("FLOOR 3", "طبقه ى سوم", 10.80, "+10.88"),
          ("ROOF", "بام", 14.20, "+14.32/+14.44"), ("STAIR HOUSE ROOF", "بام خرپشته", 17.50, "-")]
PARK_FFL, SIDEWALK = 0.08, -0.07
LEVELS_T41 = dict(
    datum="+-0.00 = top of the foundation concrete (ETABS Base) - boss T40; heights = CLEAR heights + beam (boss T41)",
    clear_heights_boss={"parking": "3.50 from the foundation top to u/s beam", "floors_1_3": "2.90 from the slab TOS to u/s beam",
                        "stair_house": "2.90 from the roof TOS to u/s beam 0.40"},
    storey={"parking": 4.00, "floor1": 3.40, "floor2": 3.40, "floor3": 3.40, "stair_house": 3.30},
    TOS={"foundation": 0.00, "floor1": 4.00, "floor2": 7.40, "floor3": 10.80, "roof": 14.20, "stair_house_roof": 17.50},
    FFL={"parking": 0.08, "floor1": 4.08, "floor2": 7.48, "floor3": 10.88, "roof_landing": 14.28},
    finish=FIN, beams=BEAM, stair_house_beams=BEAM_SH, stair_house_columns_clear=2.90, slab=SLAB,
    us_beam={"parking": 3.50, "floor1": 6.90, "floor2": 10.30, "floor3": 13.70, "stair_house": 17.10},
    clear_under_beam_structural={"parking": 3.50, "typical": 2.90, "stair_house": 2.90},
    clear_under_beam_architectural={"parking": 3.42, "typical": 2.82, "stair_house_from_landing": 2.82},
    clear_under_slab_architectural={"parking": 3.61, "typical": 3.01},
    wall_clear_height_on_beams={"parking": 3.50, "floors_1_3": 2.90, "stair_house": 2.90},
    sidewalk=-0.07, sidewalk_note="assumed = parking FFL - 0.15 (as before); check with the site survey / street level",
    roof_parapet=dict(thick=0.20, h_from_TOS=1.20, bottom=14.20, top=15.40, coping_top=15.45,
                      guard_above_finish="1.08-1.13 at the low line (+14.32), ~0.96-1.01 where ridges reach the parapet (+14.44)"),
    stair_house_curb=dict(thick=0.20, h=0.20, bottom=17.50, top=17.70),
    overrun=dict(TOS=14.90, slab=0.15, us_slab=14.75, walls="15 cm, +14.20 -> +14.75 (0.55)", overhead_from_top_stop=3.87,
                 note="3.87 min. boss approved 2026-10-31 (decision 7); T43: separate overrun REMOVED, shaft walls to u/s stair-house roof (overhead > 3.87)"))
LEVELS_T40 = LEVELS_T41
# T41: stairs redesigned for the new storeys. Core: flights X -0.05..1.05 (A side) and 1.15..2.25 (B side) = 1.10
# each, well 0.10; half landing Y 7.75-8.958 (1.21) against the axis-2 column faces, on the stair columns (boss T38d).
# Parking 0.08 -> 4.08 = 4.00: 23 risers x 0.1739 (12 B side + 11 A side), treads 0.28, 2h+b = 0.628
HL_Y = (7.75, 8.958)
G_RISER = (4.08 - PARK_FFL) / 23
STAIR_G = dict(rise=4.00, from_FFL=PARK_FFL, to_FFL=4.08, n_risers=23, riser=round(G_RISER, 4), tread=0.28,
               flights={"B (UP from the parking)": dict(risers=12, treads=11, going=3.08, Y=[8.958, 12.038]),
                        "A (to floor 1)": dict(risers=11, treads=10, going=2.80, Y=[8.958, 11.758])},
               flight_width=1.10, well=0.10, y_half=8.958, y_end=round(8.958 + 11 * 0.28, 3),
               half_landing_FFL=round(PARK_FFL + 12 * G_RISER, 2), half_landing_TOS_approx=round(PARK_FFL + 12 * G_RISER - FIN, 2),
               half_landing_Y=list(HL_Y), half_landing_size=[2.30, 1.208],
               ground_landing_Y=[round(8.958 + 11 * 0.28, 3), 13.604], ground_landing_depth=round(13.604 - 8.958 - 11 * 0.28, 3),
               floor1_landing_A_edge=11.758, two_h_plus_b=round(2 * G_RISER + 0.28, 3),
               why="4.00 rise: 22 risers = 0.182 (> 0.18), 24 = 0.167 (< 0.17) -> 23 x 0.174, unequal flights 12 + 11; "
                   "tread 0.28 so that the 12-riser flight (3.08) leaves a 1.57 ground landing (lift door DL1 + fire door DG3)")
STAIR_T = dict(rise=3.40, n_risers=20, riser=0.170, tread=0.30, flights="10 + 10 risers, 9 treads each, going 2.70",
               flight_Y=[8.958, 11.658], floor_landing_Y=[11.658, 13.604], floor_landing_depth=1.946,
               half_landing_Y=list(HL_Y), two_h_plus_b=0.64,
               half_landing_FFL={"F1->F2": 5.78, "F2->F3": 9.18, "F3->roof": 12.58},
               half_landing_TOS_approx={"F1->F2": 5.70, "F2->F3": 9.10, "F3->roof": 12.50})
YARD = dict(depth=3.50, y0=19.056, y1=19.056 + 3.50, level=0.08,
            note="rear yard at +0.08 (= parking FFL; T40 datum = top of foundation), depth ~3.50 from the rear wall face to the rear property line: "
                 "APPROXIMATE, to be checked with the deed (boss 2026-10-23)")

# wall rectangles (x0, x1, y0, y1, id, thickness cm, note)
# T38 (boss 2026-10-23): ground floor = PARKING ONLY. Removed vs T37: G-F2 (front B-C, now one steel door frame),
# G-B1 (line B 1-2), G-P1 (meter / pump room), G-S1 (storage); rooms: meter room, pump room + tank, storage.
GW = [
    (-0.25, -0.05, 0.25, 7.25, "G-A1", 20, "axis A 1-2, boundary"),
    (-0.25, -0.05, 7.75, 13.25, "G-A2", 20, "axis A 2-3, boundary (stair)"),
    (-0.25, -0.05, 13.75, 18.556, "G-A3", 20, "axis A 3-4, boundary (void, elevator, storages S1-S3)"),
    (7.20, 7.40, 0.25, 7.25, "G-C1", 20, "axis C 1-2, boundary"),
    (7.20, 7.40, 7.75, 13.25, "G-C2", 20, "axis C 2-3, boundary"),
    (7.20, 7.40, 13.75, 18.556, "G-C3", 20, "axis C 3-4, boundary"),
    # T38d (boss): pedestrian door DG2 recessed 0.80 behind the facade face -> covered entry niche (intercom) in bay A-B
    # niche clear X 0.25-2.10 (between the column faces A1 / B1), Y -0.25 (facade face) .. 0.55 (door wall face)
    # T39 (boss): niche depth 0.50 -> the door wall sits right behind the column back faces (Y 0.25-0.45);
    # niche sides = column faces A1 / B1; returns G-N1 / G-N2 removed
    (-0.05, 2.30, 0.25, 0.45, "G-F1", 20, "niche back wall (door wall), A-B, 0.50 behind the facade, against the back faces of "
                                          "columns A1 / B1: door DG2 1.20 (T39)"),
    (2.60, 3.90, -0.25, -0.05, "G-F2", 20, "front facade axis 1, B-C: wall beside car door DG1, vent WG1 (T38a)"),
    (0.25, 2.250, 18.856, 19.056, "G-R1", 20, "rear wall axis 4, A-B (storage S3, vent window WG3)"),
    # T38d (boss): the 2 m parking extension into the yard is reverted -> G-R2 restored as in T38b
    (2.750, 6.90, 18.856, 19.056, "G-R2", 20, "rear wall axis 4, B-C (yard door DG4, vent window WG2) - restored T38d"),
    (0.25, 2.10, 7.65, 7.75, "W21", 10, "axis 2 A-B, stair half landing / parking (stair enclosure)"),
    (2.25, 2.40, 7.75, 13.25, "W24", 15, "core wall stair / parking (as typical W24), fire door DG3"),
    (0.25, 2.099, 13.604, 13.754, "W19", 15, "elevator front to the ground floor landing, lift door DL1"),
    (2.449, 2.599, 13.754, 15.553, "W18", 15, "elevator side, parking"),
    (-0.05, 2.599, 15.553, 15.703, "W17", 15, "elevator back / storage S1"),
    (0.349, 0.449, 13.754, 15.553, "W20", 10, "elevator shaft side (closed void beside it: no duct at the ground, T38b)"),
    # T38b (boss): 3 storages (one per unit) behind the elevator toward the yard, doors to the parking side (east)
    (2.449, 2.599, 15.703, 18.556, "G-S1", 15, "storages S1-S3 front wall to the parking (doors DS1-DS3), W18 line"),
    (-0.05, 2.449, 16.60, 16.70, "G-S2", 10, "partition S1 / S2"),
    (-0.05, 2.449, 17.65, 17.75, "G-S3", 10, "partition S2 / S3"),
]
STORES = [("S1", "انباری واحد ۱", 15.703, 16.60), ("S2", "انباری واحد ۲", 16.70, 17.65), ("S3", "انباری واحد ۳", 17.75, 18.856)]
GW_REMOVED_T38 = {"G-B1": "line B 1-2, 15 cm, 7.00 m", "G-P1": "meter / pump room, 10 cm, 2.30 m",
                  "G-D1..D3": "plumbing duct enclosure at axis C, 10 cm, 2.40 m (T38b: ducts end at the floor-1 slab, Rev.9 TOS +4.00)",
                  "G-F1 (T38a-c)": "front facade axis 1 A-B, 20 cm, X 0.25-2.10 on the axis-1 ground beam (DG2 1.20): replaced in T38d by "
                                   "the entry niche (door wall G-F1 0.80 behind the facade + returns G-N1 / G-N2)",
                  "G-N1 / G-N2 (T38d)": "niche side returns (30 cm 0.30 m / 20 cm 0.30 m): removed in T39, niche depth 0.50 = "
                                        "column depth, the column faces A1 / B1 are the niche sides",
                  "G-F1 (T38d)": "niche door wall at Y 0.55-0.75: moved to Y 0.25-0.45 (T39)"}
NICHE = dict(x=[0.25, 2.10], y=[-0.25, 0.25], depth=0.50, clear_width=1.85, door="DG2 1.20 in the back wall G-F1 (Y 0.25-0.45)",
             sides="faces of columns A1 / B1 (no return walls)",
             roof="covered by the floor-1 slab / axis-1 beam (u/s beam +3.50 = FFL+3.42, T41)", intercom="IC on the column B1 face (X 2.10, Y ~0.0), h 1.40-1.60",
             floor="FFL +0.08 at the door (= parking), 2% fall outward to the facade line (+0.07), then step 0.14 to the sidewalk -0.07 (assumed)",
             task="T39 (boss): depth 0.50 instead of 0.80")
# openings cut through walls (x0, x1, y0, y1)
GOPEN = [
    ("WG2", "window", 4.60, 6.40, 18.856, 19.056), ("WG3", "window", 0.60, 1.80, 18.856, 19.056),
    ("DG4", "door", 2.95, 3.95, 18.856, 19.056), ("DG3", "door", 2.25, 2.40, 12.30, 13.20),
    ("DL1", "lift", 0.60, 1.80, 13.604, 13.754),
    ("DG2", "door", 0.55, 1.75, 0.25, 0.45), ("WG1", "vent", 2.85, 3.65, -0.25, -0.05),
    ("DS1", "door", 2.449, 2.599, 15.80, 16.50), ("DS2", "door", 2.449, 2.599, 16.85, 17.55),
    ("DS3", "door", 2.449, 2.599, 17.80, 18.50),
]
# T38a (boss 2026-10-23): meters, pump room (tank + booster) and one storage per unit in the REAR YARD (separate
# light structure on grade, not part of the building frame). Yard inner X -0.05..7.20, Y 19.056..22.356.
YW = [
    (-0.25, -0.05, 19.056, 22.556, "Y-A", 20, "yard boundary wall, A side (gas meter niche GM)"),
    (7.20, 7.40, 19.056, 22.556, "Y-C", 20, "yard boundary wall, C side"),
    (-0.05, 7.20, 22.356, 22.556, "Y-R", 20, "rear boundary wall at the approx. property line"),
    # T38c: pump room moved to the A-B part of the yard (behind storage S3); the B-C part is now parking
    (-0.05, 2.60, 20.356, 20.506, "Y-F", 15, "pump room front wall (door DY4, meter cabinet EM), A-B part of the yard"),
    (2.45, 2.60, 20.506, 22.356, "Y-P3", 15, "pump room side wall to the parking extension"),
]
YOPEN = [("DY4", "door", 1.45, 2.35, 20.356, 20.506)]
YROOMS = [("MR", "موتورخانه", -0.05, 2.45)]
YROOM_Y = (20.506, 22.356)
# front axis 1, bay B-C: one steel frame between the column faces X 2.60-6.90 (4.30):
# DG2 pedestrian 1.20 (B side) + mullion 0.10 + DG1 car door 3.00 (neighbour side C), both to u/s of beam +2.92
# T38a: DG2 pedestrian 1.20 alone in the front A-B bay; DG1 car door 3.00 alone in bay B-C at the neighbour (C)
# side; the rest of B-C (X 2.60-3.90) = 20 cm wall G-F2 with a high vent WG1. Both doors to u/s of beam +2.92.
FRONT = dict(DG2=(0.55, 1.75), DG2_recess=0.50, DG1=(3.90, 6.90), wall_B_C=(2.60, 3.90), head=3.42,
             head_note="3.42 above parking FFL +0.08 = u/s beam +3.50 (T41)")
# door symbols: (tag, hinge X, hinge Y, closing dir, opening dir, width)
GDOORS = [
    ("DG2", 0.55, 0.45, (1, 0), (0, 1), 1.20),          # T39: niche back wall at Y 0.25-0.45, hinge A side, opens inward
    ("DG4", 3.95, 19.056, (-1, 0), (0, 1), 1.00),        # T38d: restored (as T38b)
    ("DG3", 2.40, 13.20, (0, -1), (1, 0), 0.90),
    ("DS1", 2.449, 16.50, (0, -1), (-1, 0), 0.70), ("DS2", 2.449, 17.55, (0, -1), (-1, 0), 0.70),
    ("DS3", 2.449, 18.50, (0, -1), (-1, 0), 0.70),
]
# stalls: (tag, x0, x1, y0, y1, label)
# T38b (boss): P3 added as a real stall (tandem in front of P2)
# T38c (boss): parking +2.00 m into the yard (bay B-C); P3 and P2 each 6.00 long, 1.00 gap; P2 = unit floor 2,
# P3 (the tandem partner, in front of P2) = unit floor 1, P1 = unit floor 3
# T38d (boss): P1, P2, P3 each 2.50 x 5.00; parking back inside the building line; P1 behind the walk strip
# T39: P1 0.25 forward (Y 1.85-6.85): walk strip 0.45-1.75 = 1.30 behind the door wall, 0.40 to column A2 face
STALLS = [("P1", -0.05, 2.45, 1.85, 6.85, "2.50x5.00 PARALLEL - F3"),
          ("P2", 4.40, 6.90, 13.55, 18.55, "2.50x5.00 - F2 BEHIND P3"),
          ("P3", 4.40, 6.90, 7.90, 12.90, "2.50x5.00 - F1 TANDEM")]
STALL_UNIT = {"P1": "واحد طبقه ی سوم", "P2": "واحد طبقه ی دوم", "P3": "واحد طبقه ی اول"}


def fa(text):
    import re
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


# ---------------------------------------------------------------- plot style
def make_ctb():
    src = os.path.join(CTB_DIR, "monochrome.ctb")
    ctb = acadctb.load(src)
    ctb.description = "Zagros ARCH Rev.7: all black, colour 9 grey 60%; object (layer) lineweights: walls 0.25, doors/glazing/stairs/dims 0.13, text 0.18, grid/fill 0.09, border 0.35"
    for aci, lw in CTB_LW.items():
        st = ctb[aci]
        # index into the file's own 27-entry table (float32: ezdxf's set_lineweight would append new entries
        # past index 26, which AutoCAD clamps to 2.11 mm)
        # Test 2026-10-23: weights assigned in the CTB were plotted one step thinner by DWG To PDF.pc3
        # (0.25 -> 0.21, 0.13 -> 0.085, 0.09 -> 0.04 mm). So the CTB keeps "use object lineweight" (index 0)
        # and the LAYER lineweights (same values as CTB_LW, by colour) drive the plot: 0.25 -> 0.254 mm etc.
        st.lineweight = 0
        if aci == 9:
            st.screen = 60           # cars / equipment print grey
    paths = []
    for d in (CTB_DIR, ARCH):
        p = os.path.join(d, CTB_NAME)
        ctb.save(p)
        paths.append(p)
    return paths


# ---------------------------------------------------------------- helpers
class Sheet:
    def __init__(self, doc, dx):
        self.doc, self.msp, self.dx = doc, doc.modelspace(), dx

    def E(self, X, Y):
        return (-Y + self.dx, X)

    def line(self, layer, X1, Y1, X2, Y2, **kw):
        self.msp.add_line(self.E(X1, Y1), self.E(X2, Y2), dxfattribs={"layer": layer, **kw})

    def pline(self, layer, pts, close=True):
        self.msp.add_lwpolyline([self.E(*p) for p in pts], close=close, dxfattribs={"layer": layer})

    def rect(self, layer, x0, x1, y0, y1):
        self.pline(layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def text(self, s, X, Y, h, layer="A-ANNO", farsi=False, rot=90.0, align=TA.MIDDLE_CENTER, width=None):
        """Text at ETABS (X, Y). rot=90 -> reads along +X? No: DWG rotation; 0 = along -Y (plan horizontal)."""
        u, v = self.E(X, Y)
        return self.text_uv(s, u, v, h, layer, farsi, rot, align, width)

    def text_uv(self, s, u, v, h, layer="A-ANNO", farsi=False, rot=0.0, align=TA.MIDDLE_CENTER, width=None):
        st = "FARSI" if farsi else "LATIN"
        t = self.msp.add_text(fa(s) if farsi else s, height=h, rotation=rot,
                              dxfattribs={"layer": layer, "style": st, "width": width or (1.0 if farsi else 0.9)})
        t.set_placement((u, v), align=align)
        return t

    def dim(self, p1, p2, base, ang):
        # explicit text: ezdxf 1.4 re-rendering in a reloaded doc rounded the measurement to whole metres
        meas = abs(p2[0] - p1[0]) if ang == 0 else abs(p2[1] - p1[1])
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="A100", text=f"{meas:.2f}",
                                    dxfattribs={"layer": "A-DIMS"})
        d.render()

    def dimY(self, Y1, Y2, X):           # dimension along Y (horizontal on the sheet), dim line at X
        self.dim(self.E(X, Y1), self.E(X, Y2), self.E(X, Y1), 0)

    def dimX(self, X1, X2, Y):           # dimension along X (vertical on the sheet), dim line at Y
        self.dim(self.E(X1, Y), self.E(X2, Y), self.E(X1, Y), 90)

    def door(self, hx, hy, c, o, w, layer="A-DOOR"):
        lu = (-o[1], o[0])
        cv = (-c[1], c[0])
        H = self.E(hx, hy)
        self.msp.add_line(H, (H[0] + lu[0] * w, H[1] + lu[1] * w), dxfattribs={"layer": layer})
        ao = round(math.degrees(math.atan2(lu[1], lu[0]))) % 360
        ac = round(math.degrees(math.atan2(cv[1], cv[0]))) % 360
        if (ac - ao) % 360 == 90:
            self.msp.add_arc(H, w, ao, ac, dxfattribs={"layer": layer})
        else:
            self.msp.add_arc(H, w, ac, ao, dxfattribs={"layer": layer})

    def tag(self, s, X, Y):
        u, v = self.E(X, Y)
        self.msp.add_lwpolyline([(u - 0.22, v - 0.1), (u + 0.22, v - 0.1), (u + 0.22, v + 0.1), (u - 0.22, v + 0.1)],
                                close=True, dxfattribs={"layer": "A-ANNO-IDEN"})
        self.text_uv(s, u, v, 0.11, layer="A-ANNO-IDEN")

    def level(self, s, X, Y, h=0.12):
        """Level mark: small triangle + text, at ETABS (X, Y)."""
        u, v = self.E(X, Y)
        self.msp.add_lwpolyline([(u, v), (u - 0.09, v + 0.15), (u + 0.09, v + 0.15)], close=True,
                                dxfattribs={"layer": "A-ANNO"})
        self.msp.add_line((u - 0.25, v), (u + 0.25, v), dxfattribs={"layer": "A-ANNO"})
        self.text_uv(s, u + 0.15, v + 0.22, h, align=TA.BOTTOM_LEFT)


def union_edges(rects, holes, solids):
    """Outline of the union of axis-aligned wall rectangles minus openings (holes). Edges against
    'solids' (columns, drawn separately) are omitted. Returns merged segments [(X1, Y1, X2, Y2)]."""
    xs = sorted({r[0] for r in rects + holes + solids} | {r[1] for r in rects + holes + solids})
    ys = sorted({r[2] for r in rects + holes + solids} | {r[3] for r in rects + holes + solids})

    def inside(x, y, rs):
        return any(r[0] < x < r[1] and r[2] < y < r[3] for r in rs)

    nx, ny = len(xs) - 1, len(ys) - 1
    st = {}
    for i in range(nx):
        for j in range(ny):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if inside(cx, cy, solids):
                st[i, j] = 2
            elif inside(cx, cy, rects) and not inside(cx, cy, holes):
                st[i, j] = 1
            else:
                st[i, j] = 0

    def s(i, j):
        return st.get((i, j), 0)

    segs = []
    for i in range(nx + 1):                      # vertical edges x = xs[i]
        for j in range(ny):
            a, b = s(i - 1, j), s(i, j)
            if {a, b} == {0, 1}:
                segs.append(("V", xs[i], ys[j], ys[j + 1]))
    for j in range(ny + 1):                      # horizontal edges y = ys[j]
        for i in range(nx):
            a, b = s(i, j - 1), s(i, j)
            if {a, b} == {0, 1}:
                segs.append(("H", ys[j], xs[i], xs[i + 1]))
    merged = []
    for kind in ("V", "H"):
        group = sorted([g for g in segs if g[0] == kind], key=lambda g: (round(g[1], 6), g[2]))
        cur = None
        for g in group:
            if cur and abs(cur[1] - g[1]) < 1e-9 and abs(cur[3] - g[2]) < 1e-9:
                cur = (kind, cur[1], cur[2], g[3])
            else:
                if cur:
                    merged.append(cur)
                cur = g
        if cur:
            merged.append(cur)
    out = []
    for kind, c, a, b in merged:
        out.append((c, a, c, b) if kind == "V" else (a, c, b, c))
    return out


# ---------------------------------------------------------------- A-102: typical floor (re-layer Rev.6)
def relayer_typical(doc):
    msp = doc.modelspace()
    kill = []
    for e in msp:
        L, T = e.dxf.layer, e.dxftype()
        if L == "A-SHEET":
            kill.append(e)
            continue
        if L == "A-COLUMN":
            new = "A-COLS-PATT" if T == "HATCH" else "A-COLS"
        elif L == "A-AXIS":
            new = "A-GRID" if T == "LINE" else "A-GRID-IDEN"
        elif L == "A-TEXT":
            if T == "TEXT" and e.dxf.text in TAGS:
                new = "A-ANNO-IDEN"
            elif T == "LWPOLYLINE":
                new = "A-ANNO-IDEN"
            elif T == "LINE":
                new = "A-ANNO-TABL"
            else:
                new = "A-ANNO"
        else:
            new = OLD2NEW[L]
        e.dxf.layer = new
        if T != "DIMENSION":
            e.dxf.color = 256
        e.dxf.lineweight = -1
        if T == "CIRCLE" and new == "A-GRID-IDEN":
            e.dxf.linetype = "BYLAYER"
    for e in kill:
        msp.delete_entity(e)
    # text edits
    kill = []
    for e in msp.query("TEXT"):
        t = e.dxf.text
        if t.startswith(fa("پلان معماری")) or t.startswith("TYPICAL FLOOR ARCHITECTURAL PLAN") or e.dxf.style == "FARSI" \
                and (t.startswith(fa("شرکت")) or t.startswith(fa("پروژه")) or t.startswith(fa("عنوان")) or
                     t.startswith(fa("مهندس")) or t.startswith(fa("مقیاس"))) or t.startswith("SOURCE: arch/"):
            kill.append(e)
        elif t == fa("جدول در و پنجره - ") + "Rev.6":
            e.dxf.text = fa("جدول در و پنجره - طبقات تیپ ۱ تا ۳ - ") + REV
        elif t.startswith("11. Rev.6 FINAL"):
            e.dxf.text = "11. Rev.9: geometry = Rev.6 FINAL (unchanged) + grid B'; storey 3.40 (T41); stair redrawn 20 x 0.170 / 0.30; one sheet per floor."
        elif t == fa("پله"):
            e.set_placement((-12.85, 1.75), align=TA.MIDDLE_CENTER)
        elif t == fa("مدل ETABS باید با این هماهنگ شود"):
            kill.append(e)                   # T37: ETABS Rev5 already has C19 = 2.500 on grid B'
        elif t.startswith("2. Axis 4 at 18.81 and column C19"):
            e.dxf.text = "2. Axis 4 at 18.81; column C19 at X=2.500 on new grid B' (ETABS T33; was 2.507, 7 mm; boss approved 2026-10-23):"
        elif t.startswith("1. Redrawn from the vector PDF"):
            e.dxf.text = "1. Redrawn from the vector basis PDF (all lines), scale from its dimension texts. Rev.1 to Rev.6 = boss decisions 2026-10-22/23."
    for e in kill:
        msp.delete_entity(e)
    # T33: C19 centre 2.507 -> 2.500 (move its outline / fill by -7 mm in v)
    from ezdxf import bbox
    for e in list(msp.query("*[layer=='A-COLS' | layer=='A-COLS-PATT']")):
        b = bbox.extents([e])
        if b.has_data and b.extmin.x > -19.10 and b.extmax.x < -18.50 and b.extmin.y > 2.20 and b.extmax.y < 2.80:
            e.translate(0, C19_X - C19_OLD, 0)
    sh = Sheet(doc, 0.0)
    grid_bprime(sh, -20.254, 0.25)
    return sh


def grid_bprime(sh, u_min, u_max, u_end=None, stub=False):
    """Grid B' (X = 2.50) for column C19: drawn from axis 3 to the rear, bubble at the rear (left) end,
    because B (2.349) is only 0.151 away and its bubble is at the front (right) end."""
    R = 0.40
    ue = u_min if u_end is None else u_end           # T37: on A-101 the grid runs past the rear yard
    u3 = sh.E(0, 13.5032)[0]
    # T38c: on A-101 only a stub outside the lot (no dash-dot line through the parking / yard)
    sh.msp.add_line(((ue - 0.2) if stub else (u3 + 0.8), C19_X), (ue - 1.0, C19_X), dxfattribs={"layer": "A-GRID"})
    sh.msp.add_circle((ue - 1.0 - R, C19_X), R, dxfattribs={"layer": "A-GRID-IDEN"})
    sh.text_uv("B'", ue - 1.0 - R, C19_X, 0.30, layer="A-GRID-IDEN")
    sh.dim((ue - 0.5, 2.3486), (ue - 0.5, C19_X), (ue - 0.5, 2.3486), 90)
    sh.text_uv("B' = 2.50 (C19)", ue - 1.0 - R, C19_X - 0.75, 0.10, layer="A-GRID-IDEN")


# ---------------------------------------------------------------- sheet furniture (both sheets)
def sheet_frame(sh, fx0, fy0, title_fa, title_en, sheet_no, status, plan_cx, plan_vtop):
    m = 1.0
    fx1, fy1 = fx0 + 42.0, fy0 + 29.7
    msp = sh.msp
    msp.add_lwpolyline([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], close=True, dxfattribs={"layer": "A-ANNO-TTLB"})
    msp.add_lwpolyline([(fx0 + m, fy0 + m), (fx1 - m, fy0 + m), (fx1 - m, fy1 - m), (fx0 + m, fy1 - m)], close=True,
                       dxfattribs={"layer": "A-ANNO-BRDR"})
    sh.text_uv(title_fa, plan_cx, plan_vtop + 2.6, 0.50, farsi=True)
    sh.text_uv(title_en, plan_cx, plan_vtop + 1.9, 0.25)
    tw, th = 17.0, 6.6
    bx1, by0 = fx1 - m, fy0 + m
    bx0, by1 = bx1 - tw, by0 + th
    msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], close=True, dxfattribs={"layer": "A-ANNO-TTLB"})
    rows = [
        ("شرکت آهن بتن زاگرس - سهامی خاص", 0.40, True),
        ("پروژه: مرآژ ۳ - Merage3 - مسکونی ۳ طبقه روی پارکینگ", 0.36, True),
        ("عنوان: " + title_fa, 0.32, True),
        ("مهندس محاسب: رحمت الله شیرزایی", 0.40, True),
        (f"مقیاس: 1:100     واحد: متر     تاریخ: {DATE}     شماره نقشه: {sheet_no}", 0.28, True),
        (status, 0.22, False),
    ]
    rh = th / len(rows)
    for k, (s, hh, farsi) in enumerate(rows):
        yy = by1 - (k + 0.5) * rh
        if k:
            msp.add_line((bx0, by1 - k * rh), (bx1, by1 - k * rh), dxfattribs={"layer": "A-ANNO-TTLB"})
        sh.text_uv(s, (bx0 + bx1) / 2, yy, hh, farsi=farsi, width=1.0 if farsi else 0.85)
    return fx1, fy1, bx0, by1


def legend(sh, x0, y0):
    """Layer / line-weight legend + level table at sheet coordinates (x0, y0 = top-left)."""
    msp = sh.msp
    sh.text_uv("LAYERS / PLOT LINE WEIGHTS (mm) - " + CTB_NAME, x0, y0, 0.17, align=TA.MIDDLE_LEFT, width=0.85)
    rows = [("A-WALL", "walls (cut)"), ("A-COLS", "columns"), ("A-DOOR", "doors, gates"), ("A-GLAZ", "windows"),
            ("A-STRS", "stairs"), ("A-STRS-OVHD", "stairs above"), ("A-ELEV", "elevator"), ("A-SHFT", "ducts"),
            ("A-FLOR-HRAL", "railings"), ("A-PRKG", "parking stalls"), ("A-PRKG-CARS", "cars (grey)"),
            ("A-EQPM", "equipment (grey)"), ("A-SITE-PROP", "property line"), ("A-DIMS", "dimensions"), ("A-ANNO", "text"), ("A-GRID", "grid"),
            ("A-COLS-PATT", "column fill"), ("A-ANNO-BRDR", "border")]
    y = y0 - 0.32
    for name, what in rows:
        col, lt, lw, _ = LAYERS[name]
        msp.add_line((x0, y), (x0 + 0.9, y), dxfattribs={"layer": name})
        sh.text_uv(name, x0 + 1.1, y, 0.13, align=TA.MIDDLE_LEFT, width=0.8)
        sh.text_uv(f"{lw / 100:.2f}", x0 + 3.0, y, 0.13, align=TA.MIDDLE_LEFT, width=0.8)
        sh.text_uv(what, x0 + 3.6, y, 0.13, align=TA.MIDDLE_LEFT, width=0.8)
        y -= 0.25
    y -= 0.25
    sh.text_uv("LEVELS (m)  -  +-0.00 = TOP OF FOUNDATION CONCRETE", x0, y, 0.17, align=TA.MIDDLE_LEFT, width=0.85)
    y -= 0.32
    for k, s_ in enumerate(("TOS", "FFL", "LEVEL")):
        sh.text_uv(s_, x0 + (0.0, 0.95, 2.25)[k], y, 0.12, align=TA.MIDDLE_LEFT, width=0.85)
    msp.add_line((x0, y - 0.13), (x0 + 6.4, y - 0.13), dxfattribs={"layer": "A-ANNO-TABL"})
    y -= 0.28
    for en, f, lev, ffl in reversed(LEVELS):
        sh.text_uv(f"{lev:+.2f}" if lev else "+-0.00", x0, y, 0.14, align=TA.MIDDLE_LEFT, width=0.85)
        sh.text_uv(ffl, x0 + 0.95, y, 0.11 if len(ffl) > 6 else 0.14, align=TA.MIDDLE_LEFT, width=0.75)
        sh.text_uv(en, x0 + 2.25, y, 0.12, align=TA.MIDDLE_LEFT, width=0.8)
        sh.text_uv(f, x0 + 6.4, y, 0.14, farsi=True, align=TA.MIDDLE_RIGHT)
        msp.add_line((x0, y - 0.14), (x0 + 6.4, y - 0.14), dxfattribs={"layer": "A-ANNO-TABL"})
        y -= 0.30
    for s_ in ("TOS = top of structural slab (ETABS storey level); FFL = TOS + 0.08 finish.",
               "Boss T41: clear heights (concrete below -> u/s beam) parking 3.50, floors 2.90, stair house 2.90.",
               "Storeys = clear + beam: parking 4.00, floors 3.40, stair house 3.30 (beam 0.40).",
               "Clear u/s beam above FFL: parking 3.42, floors 2.82 (finish 0.08).",
               "Parapets: roof 0.20 x 1.20 (+14.20 -> +15.40); stair-house roof 0.20 x 0.20 (top +17.70).",
               "Sidewalk -0.07 assumed (= parking FFL - 0.15): check with the site survey."):
        sh.text_uv(s_, x0, y, 0.11, align=TA.MIDDLE_LEFT, width=0.8)
        y -= 0.21


# ---------------------------------------------------------------- A-101: ground floor / parking
def ground(doc, cols):
    sh = Sheet(doc, DXG)
    col_r = [(x - 0.25, x + 0.25, y - 0.25, y + 0.25) for x, y in cols]
    rects = [(r[0], r[1], r[2], r[3]) for r in GW + YW]
    holes = [(o[2], o[3], o[4], o[5]) for o in GOPEN + YOPEN]
    for X1, Y1, X2, Y2 in union_edges(rects, holes, col_r):
        sh.line("A-WALL", X1, Y1, X2, Y2)
    for r in col_r:
        sh.rect("A-COLS", *r)
        h = sh.msp.add_hatch(dxfattribs={"layer": "A-COLS-PATT"})
        h.paths.add_polyline_path([sh.E(r[0], r[2]), sh.E(r[1], r[2]), sh.E(r[1], r[3]), sh.E(r[0], r[3])], is_closed=True)

    # glazing / vents (two lines in the wall thickness), gate, doors
    for tg, kind, x0, x1, y0, y1 in GOPEN:
        if kind in ("window", "vent"):
            t = y1 - y0
            for f in (0.4, 0.6):
                sh.line("A-GLAZ", x0, y0 + f * t, x1, y0 + f * t)
    # T38 front bay B-C: one steel frame between the column faces; DG1 overhead car door (leaf in the wall line
    # + dashed open position under the ceiling), mullion, DG2 pedestrian swing door
    a, b = FRONT["DG1"]
    sh.rect("A-DOOR", a, b, -0.17, -0.13)
    sh.rect("A-STRS-OVHD", a + 0.05, b - 0.05, -0.05, 2.35)                 # door leaf open, overhead (dashed)
    sh.text("DG1 OPEN (OVERHEAD)", 5.40, 2.15, 0.08, rot=0.0)
    sh.line("A-DOOR", 6.90, -0.25, 6.90, -0.05)
    for tg, kind, x0, x1, y0, y1 in YOPEN:                                   # yard room doors (swing into the rooms)
        sh.door(x1, y1, (-1, 0), (0, 1), x1 - x0)
    for t, hx, hy, c, o, w in GDOORS:
        sh.door(hx, hy, c, o, w)

    # elevator + duct symbols (as typical), lift door gap
    sh.line("A-ELEV", 0.449, 13.754, 2.449, 15.553)
    sh.line("A-ELEV", 0.449, 15.553, 2.449, 13.754)
    # T38b: no ducts in the parking (they end at the floor-1 slab); closed void beside the elevator
    sh.text("VOID", 0.15, 14.65, 0.07, rot=90.0)

    # stair (T37): ground flight = typical, 10 treads 0.30 (20 risers x 0.175), B side UP solid to the cut line, rest dashed
    # T41: B side UP 12 risers x 0.174 / treads 0.28 (ground landing edge Y 12.038 -> half landing edge 8.958);
    # A side (above the cut, dashed) 11 risers to the floor-1 landing (edge Y 11.758)
    yh, ye = STAIR_G["y_half"], STAIR_G["y_end"]
    ycut = 10.30                                                     # ~1.2 m above the parking FFL (7th riser)
    for k in range(12):
        Yt = ye - 0.28 * k
        sh.line("A-STRS" if Yt >= ycut else "A-STRS-OVHD", 1.15, Yt, 2.25, Yt)
    for k in range(11):
        Yt = yh + 0.28 * k
        sh.line("A-STRS-OVHD", -0.05, Yt, 1.05, Yt)
    sh.line("A-STRS", 1.15, ycut, 1.15, ye)
    sh.line("A-STRS-OVHD", 1.15, yh, 1.15, ycut)
    sh.line("A-STRS-OVHD", 1.05, yh, 1.05, 11.758)
    sh.line("A-STRS", 1.15, ycut - 0.05, 2.25, ycut + 0.20)          # break line
    sh.line("A-STRS", 1.70, ye - 0.15, 1.70, ycut + 0.25)            # walking line UP
    sh.line("A-STRS", 1.70, ycut + 0.25, 1.60, ycut + 0.45)
    sh.line("A-STRS", 1.70, ycut + 0.25, 1.80, ycut + 0.45)
    sh.msp.add_circle(sh.E(1.70, ye - 0.15), 0.04, dxfattribs={"layer": "A-STRS"})
    sh.text("UP", 1.70, ye + 0.17, 0.15, rot=0.0)
    sh.text("12 + 11 = 23 x 17.4/28 TO +4.08", 1.97, 11.00, 0.07, rot=0.0)
    sh.text("HALF LANDING FFL +2.17 (above)", 1.05, 8.25, 0.09, rot=90.0)
    sh.text("GROUND LANDING FFL +0.08", 1.10, 12.55, 0.075, rot=90.0)
    # *A11: proposed independent landing support (structural, coordination 57; pending boss), dashed below the landing
    # T38c: the dashed *A11 support outline is no longer drawn (it read as a wall beside P1); text reference only
    # T38d (boss): landing on the stair columns via a landing beam (note A11); text only, nothing dashed
    sh.text("LANDING BEAM ON COLUMNS - A11", 1.10, 8.60, 0.07, rot=90.0)
    sh.text("FLIGHT ABOVE", 0.50, 10.60, 0.10, rot=90.0)

    # parking: stall striping, wheel stops, cars
    for tg, x0, x1, y0, y1, lab in STALLS:
        sh.rect("A-PRKG", x0, x1, y0, y1)
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        # T39 (boss): one sedan per stall (block CAR_SEDAN, front = block +x). P2 / P3 driven in nose first (front to
        # the rear = +Y -> sheet -u -> rotation 180); P1 parallel, reversed in (front to the street -Y -> rotation 0)
        sh.msp.add_blockref("CAR_SEDAN", sh.E(xc, yc), dxfattribs={"layer": "A-PRKG-CARS", "rotation": 0.0 if tg == "P1" else 180.0})
        sh.text(tg, xc, yc + 0.05, 0.30, rot=0.0)
        sh.text(lab, xc, (y1 - 0.12) if tg == "P1" else (y0 + 0.12), 0.08, rot=90.0)      # end strip outside the car
        sh.text(STALL_UNIT[tg], (x0 + 0.16) if tg == "P1" else (x1 - 0.09), (yc + 1.00) if tg == "P1" else (yc - 1.00), 0.12, farsi=True, rot=0.0)
    # T38: parking only - whole ground floor; the core (stair + elevator) and the ducts remain
    sh.text("پارکینگ", 3.50, 16.60, 0.17, farsi=True, rot=90.0)
    sh.text("PARKING FFL +0.08", 3.50, 17.05, 0.09, rot=90.0)
    for tg, name, y0, y1 in STORES:                                  # storages behind the elevator
        yc = (y0 + y1) / 2
        sh.text(name, 1.45, yc, 0.11, farsi=True, rot=0.0)
        sh.text(f"{tg}  {2.499 * (y1 - y0):.1f} m2", 1.05, yc, 0.08, rot=0.0)
        sh.tag("D" + tg, 0.35, yc)
    sh.text("AISLE 4.30 (ONE LANE)", 5.40, 7.20, 0.10, rot=90.0)
    # T38d: parking ends inside the building (rear wall G-R2 restored); B-C part of the yard open
    sh.text("حیاط پشتی", 5.10, 20.90, 0.13, farsi=True, rot=90.0)
    sh.text("طول تقریبی - طبق سند", 5.10, 21.20, 0.10, farsi=True, rot=90.0)
    sh.text("YARD +0.08 (OPEN)", 5.10, 21.48, 0.09, rot=90.0)
    # T38d: entry niche (DG2 recessed 0.80): intercom on the column B1 face, niche floor note
    # T39: niche 1.85 x 0.50 between the column faces A1 / B1; IC on the B1 face
    sh.rect("A-EQPM", 2.04, 2.10, -0.10, 0.10)
    sh.text("IC", 1.96, -0.17, 0.06, rot=0.0, layer="A-EQPM")
    sh.text("آیفون", 1.92, -0.50, 0.09, farsi=True, rot=0.0)
    sh.line("A-ANNO", 1.98, -0.42, 2.03, -0.12)
    sh.text("ENTRY NICHE 1.85x0.50", 1.30, 0.10, 0.065, rot=90.0)
    sh.text("+0.08, 2% OUT", 1.30, -0.10, 0.065, rot=90.0)
    # pedestrian route (painted walkway): DG2 (niche) -> strip behind the door wall -> along line B -> DG3
    sh.line("A-PRKG", -0.05, 1.75, 3.50, 1.75)          # T39: walk strip Y 0.45-1.75 (1.30)
    sh.line("A-PRKG", 3.50, 1.75, 3.50, 12.20)
    sh.text("مسیر پیاده", 3.22, 4.80, 0.15, farsi=True, rot=0.0)
    sh.line("A-ANNO", 3.05, 2.6, 3.05, 3.7)
    sh.line("A-ANNO", 3.05, 3.7, 2.95, 3.5)
    sh.line("A-ANNO", 3.05, 3.7, 3.15, 3.5)

    # T38a: equipment in the rear yard: meters EM (on Y-F, passage side) and GM (niche in Y-A), tank + booster in MR
    sh.rect("A-EQPM", 0.20, 1.20, 20.236, 20.356)
    sh.text("EM", 0.70, 20.10, 0.10, rot=0.0, layer="A-EQPM")
    sh.rect("A-EQPM", -0.05, 0.10, 19.30, 19.90)
    sh.text("GM", 0.30, 19.60, 0.10, rot=0.0, layer="A-EQPM")
    sh.msp.add_circle(sh.E(0.80, 21.70), 0.65, dxfattribs={"layer": "A-EQPM"})
    sh.text("T 2000 L", 0.80, 21.70, 0.11, rot=0.0, layer="A-EQPM")
    sh.rect("A-EQPM", 1.65, 2.25, 21.60, 22.30)
    sh.text("BOOSTER", 1.95, 21.95, 0.08, rot=90.0, layer="A-EQPM")
    for tg, name, x0, x1 in YROOMS:
        xc = (x0 + x1) / 2
        area = (x1 - x0) * (YROOM_Y[1] - YROOM_Y[0])
        if tg == "MR":
            sh.text(name, 0.75, 20.74, 0.11, farsi=True, rot=90.0)
            sh.text(f"MR 2.50 x 1.85 = {area:.1f} m2", 0.75, 20.92, 0.07, rot=90.0)

    # balcony above (outline), yard, street
    sh.pline("A-FLOR-OVHD", [(-0.25, 19.056), (-0.25, 20.254), (7.40, 20.254), (7.40, 19.056)], close=False)
    sh.text("BALCONY ABOVE", 5.9, 19.75, 0.09, rot=90.0)
    # T37: rear yard at +-0.00 (same level as the parking), ~3.50 deep, property line approximate
    y0, y1 = YARD["y0"], YARD["y1"]
    sh.pline("A-SITE-PROP", [(-0.25, y0), (-0.25, y1), (7.40, y1), (7.40, y0)], close=False)
    sh.text("PASSAGE (YARD)", 1.40, 19.55, 0.08, rot=90.0)
    sh.text("PROPERTY LINE (APPROX.)", 4.90, y1 + 0.20, 0.10, rot=90.0)
    sh.text("معبر و پیاده رو - فرض", 3.6, -2.65, 0.18, farsi=True, rot=90.0)
    sh.text("SIDEWALK -0.07 (ASSUMED)", 3.6, -3.00, 0.11, rot=90.0)

    # room names + levels
    names = [("پله", 0.55, 12.95, None), ("آسانسور", 1.85, 14.65, None)]
    for s, X, Y, sub in names:
        sh.text(s, X, Y, 0.18 if len(s) < 12 else 0.15, farsi=True, rot=0.0)
        if sub:
            sh.text(sub, X - 0.30, Y, 0.11, rot=0.0)
    sh.level("FFL +0.08 (FDN TOP +-0.00)", 3.05, 10.90, h=0.11)

    sh.text("LIFT PIT BELOW FDN TOP", 0.85, 14.65, 0.07, rot=0.0)

    # tags
    tags = [("DG1", 5.40, -0.55), ("DG2", 0.35, -0.50), ("WG1", 3.25, -0.55), ("DG3", 3.05, 12.75), ("DG4", 3.45, 18.45),
            ("DL1", 0.95, 13.30), ("WG2", 4.95, 18.70), ("DY4", 1.00, 19.80)]
    for tg, X, Y in tags:
        sh.tag(tg, X, Y)

    # dimensions: overall + grid (same layout as the typical sheet)
    AX_Y = [0.0, 7.5016, 13.5032, 18.806]
    AX_X = [0.0, 2.3486, 7.1499]
    v_min, v_max, u_max, u_min = -0.25, 7.40, sh.E(0, -0.25)[0], sh.E(0, 19.056)[0]
    u_yard = sh.E(0, YARD["y1"])[0]
    us = [u_max] + [sh.E(0, Y)[0] for Y in AX_Y] + [u_min]
    for a, b in zip(us, us[1:]):
        sh.dim((a, v_min), (b, v_min), (a, v_min - 1.0), 0)
    sh.dim((u_max, v_min), (u_min, v_min), (u_max, v_min - 1.8), 0)
    vs = [v_min] + AX_X + [v_max]
    for a, b in zip(vs, vs[1:]):
        sh.dim((u_max, a), (u_max, b), (u_max + 1.0, a), 90)
    sh.dim((u_max, v_min), (u_max, v_max), (u_max + 1.8, v_min), 90)
    R = 0.40
    for lab, Y in zip("1234", AX_Y):
        u = sh.E(0, Y)[0]
        # T38c: grid lines only outside the plan (no dash-dot line through the parking)
        sh.msp.add_line((u, v_min - 3.0), (u, v_min - 0.2), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_line((u, v_max + 0.2), (u, v_max + 1.0), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_circle((u, v_min - 3.0 - R), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u, v_min - 3.0 - R, 0.35, layer="A-GRID-IDEN")
    for lab, X in zip("ABC", [0.0, 2.3486, 7.1499]):
        sh.msp.add_line((u_yard - 1.0, X), (u_yard - 0.2, X), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_line((u_max + 0.2, X), (u_max + 3.0, X), dxfattribs={"layer": "A-GRID"})
        sh.msp.add_circle((u_max + 3.0 + R, X), R, dxfattribs={"layer": "A-GRID-IDEN"})
        sh.text_uv(lab, u_max + 3.0 + R, X, 0.35, layer="A-GRID-IDEN")
    # C19 at X=2.507 on axis 4: note
    grid_bprime(sh, u_min, u_max, u_end=u_yard, stub=True)
    # T37: yard depth ~3.50 (approx.) and lot depth ~22.81 (front facade face to the rear property line)
    for p1, p2, base, txt in (((u_min, v_min), (u_yard, v_min), (u_min, v_min - 1.0), "~3.50"),
                              ((u_max, v_min), (u_yard, v_min), (u_max, v_min - 2.4), f"~{YARD['y1'] + 0.25:.2f} (LOT, APPROX.)")):
        d = sh.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=0, dimstyle="A100", text=txt, dxfattribs={"layer": "A-DIMS"})
        d.render()
    # interior dimensions
    sh.dimY(7.90, 12.90, 4.05)          # P3 5.00 (T39: dim line in the aisle, outside the stall)
    sh.dimY(12.90, 13.55, 4.05)         # gap 0.65 between P3 and P2
    d = sh.msp.add_linear_dim(base=sh.E(-0.70, -0.25), p1=sh.E(-0.25, -0.25), p2=sh.E(-0.25, 0.25), angle=0, dimstyle="A100",
                              text="0.50 NICHE", dxfattribs={"layer": "A-DIMS"})   # T39: niche depth 0.50, outside the plan
    d.render()
    sh.dimY(0.45, 1.75, 2.75)           # T39: walk strip 1.30 behind the door wall
    sh.dimY(ye, 13.604, 0.30)           # T41: ground landing 1.57
    sh.dim(sh.E(2.45, 1.85), sh.E(2.45, 6.85), sh.E(2.80, 1.85), 0)   # P1 5.00, dim line OUTSIDE the stall
    sh.dimY(6.85, 7.25, 1.20)           # T39: P1 rear end to the column A2 face 0.40
    sh.dimY(13.55, 18.55, 4.05)         # P2 5.00
    sh.dimX(-0.05, 2.45, 6.30)          # P1 2.50 (inside the stall, clear of the 0.40 dim)
    sh.dimX(4.40, 6.90, 18.40)          # P2 2.50
    sh.dimX(2.60, 6.90, 7.50)           # aisle between the column faces 4.30
    sh.dimX(0.25, 2.10, -0.95)          # T38d: niche clear width 1.85 (A-B, between the column faces)
    sh.dimX(-0.05, 2.45, 22.20)         # yard pump room 2.50
    sh.dimY(19.056, 20.356, 2.10)       # yard passage 1.30
    sh.dimX(3.90, 6.90, -0.95)          # car door 3.00
    for xa, xb in ((-0.05, 1.05), (1.05, 1.15), (1.15, 2.25)):
        sh.dimX(xa, xb, 9.60)

    # sheet
    plan_cx = (u_min + u_max) / 2
    fx0, fy0 = -29.5 + DXG, -15.2
    title_fa = "پلان پارکینگ - همکف"
    sheet_frame(sh, fx0, fy0, fa("پیش نویس - " + title_fa) + " - " + REV, f"PARKING PLAN  -  FDN TOP +-0.00, FFL +0.08, CEILING TOS +4.00  -  {REV} DRAFT  -  1:100  -  DIMENSIONS IN METRES",
                "A-101", f"{REV} DRAFT (T41: clear 3.50 + beam 0.50 = parking storey 4.00, floor 1 TOS +4.00; stair 23 x 0.174 / 0.28) - A1-A11",
                plan_cx, v_max)
    legend(sh, 4.6 + DXG, 12.6)

    # schedule + notes
    sx0, sy0 = fx0 + 1.6, -4.3          # T40: 0.30 higher (longer notes)
    sched = [("TAG", "TYPE", "W", "SILL", "HEAD", "WHERE / NOTE"),
             ("DG1", "CAR DOOR", "3.00", "0.00", "3.42", "front axis 1 B-C, neighbour (C) side, overhead sectional, grille, to u/s beam"),
             ("DG2", "STEEL DOOR", "1.20", "0.00", "3.42", "A-B, recessed 0.50 behind the facade (covered entry niche 1.85 x 0.50), opens inward"),
             ("IC", "INTERCOM", "-", "1.40", "1.60", "entry niche, on the column B1 face (side of the niche), with the door release"),
             ("WG1", "VENT", "0.80", "1.80", "2.70", "front wall G-F2 (B-C beside DG1), parking ventilation, louvre"),
             ("DG3", "FIRE DOOR", "0.90", "0.00", "2.10", "core wall W24 to the parking, self-closing, opens to the parking"),
             ("DL1", "LIFT DOOR", "1.20", "0.00", "2.00", "elevator, to the ground landing (as floors 1-3)"),
             ("DG4", "STEEL DOOR", "1.00", "0.00", "2.10", "rear wall axis 4 B-C to the rear yard (yard +0.08 = parking, no step) - restored T38d"),
             ("DS1-3", "STEEL DOOR", "0.70", "0.00", "2.10", "storages S1-S3 behind the elevator (one per unit), open from the parking"),
             ("DY4", "STEEL DOOR", "0.90", "0.00", "2.10", "yard pump room MR (A-B part, tank 2000 L + booster), louvred"),
             ("EM/GM", "METERS", "1.00", "0.60", "1.80", "yard A-B part: EM on pump room wall Y-F (passage side), GM niche in wall Y-A"),
             ("WG2", "WINDOW", "1.80", "1.50", "2.90", "rear wall B-C, parking ventilation, grille - restored T38d"),
             ("WG3", "WINDOW", "1.20", "1.50", "2.90", "rear wall A-B, storage S3 ventilation, grille")]
    colx = [0.0, 1.2, 3.4, 4.3, 5.2, 6.3]
    sh.text_uv(fa("جدول در و پنجره - همکف - ") + REV, sx0 + 4.0, sy0 + 0.45, 0.30, farsi=True)
    for k, row in enumerate(sched):
        yy = sy0 - k * 0.30
        for cx, s in zip(colx, row):
            sh.text_uv(s, sx0 + cx, yy, 0.15 if k else 0.16, align=TA.MIDDLE_LEFT, width=0.85)
        sh.msp.add_line((sx0 - 0.1, yy - 0.15), (sx0 + 13.0, yy - 0.15), dxfattribs={"layer": "A-ANNO-TABL"})
    yy = sy0 - len(sched) * 0.30 - 0.05
    notes = [
        "NOTES / ASSUMPTIONS (no ground-floor plan exists in memary 500.dwg or in the basis PDF):",
        "A1. LEVELS (boss T40/T41): +-0.00 = TOP OF FOUNDATION CONCRETE. Boss: CLEAR height 3.50 from the foundation top to u/s beam",
        "     + beam 0.50 = parking storey 4.00 -> floor-1 slab TOS +4.00 (FFL +4.08). Parking finish 0.08 (concrete topping) -> FFL +0.08;",
        "     u/s beam +3.50 = FFL+3.42 (>= 2.20); u/s slab FFL+3.61. Schedule heights above FFL +0.08 (DG1 / DG2 head 3.42 = u/s beam).",
        "A2. Street at axis 1 (front, west); sidewalk -0.07 (ASSUMED = FFL-0.15, check site survey). Rear yard +0.08 (= parking), depth ~3.50",
        "     from the rear wall face to the rear property line (APPROXIMATE - check with the deed); balcony 1.20 above. Lot depth ~22.81.",
        "A3. T38-T38b (boss 2026-10-23): ground floor = parking + stair / elevator core + 3 storages behind the elevator (one per",
        "     unit, doors to the parking). Meters and the pump room are in the REAR YARD (light structure on grade, joint to the building).",
        "A4. Columns, axes, boundary walls A/C, elevator, ducts and core wall W24 exactly as the typical floor (Rev.6).",
        "A5. Ground stair (T41): +0.08 -> +4.08 = 4.00, 23 risers x 0.174, treads 0.28 (2h+b = 0.63); unequal flights: B side 12 UP",
        "     (going 3.08), A side 11 (2.80); flights 1.10 + well 0.10 + 1.10; half landing FFL +2.17 at Y 7.75-8.96; ground landing 1.57.",
        "A6. Front axis 1: bay A-B (T39) = covered ENTRY NICHE 1.85 x 0.50 (sides = column faces A1 / B1, under the slab / u/s beam +3.50):",
        "     pedestrian door DG2 1.20 in its back wall G-F1 0.50 behind the facade, intercom IC on the B1 face; niche floor +0.08, 2% out,",
        "     step 0.14 to the sidewalk. Bay B-C: car door DG1 3.00 at the C side + wall G-F2 1.30 with vent WG1. Walk: DG2 -> strip",
        "     1.30 behind the door wall -> along line B -> fire door DG3 (W24) -> ground landing / lift.",
        "A7. T38d/T39 (boss): stalls 5.00 long inside the building line, one sedan (1.80 x 4.50) drawn in each stall.",
        "     P1 2.50 x 5.00 parallel (unit F3, Y 1.85-6.85), P3 in B-C (unit F1), gap 0.65, P2 behind P3 (unit F2, tandem).",
        "     Free strip X 2.60-4.40 (1.80) for people: DG3 -> storages DS1-3 -> yard door DG4. No wall beside P1.",
        "     Storages S1-S3: 2.50 wide x 0.90 / 0.95 / 1.10 deep = 2.2 / 2.4 / 2.8 m2 (minus column corners in S3), doors 0.70 inward.",
        "A8. Yard: pump room MR 2.50 x 1.85 = 4.6 m2 (tank 2000 L ~22 kN + booster, on grade) in the A-B part; meters EM on its",
        "     front wall, GM niche in wall Y-A; passage 1.30 under the balcony from yard door DG4; B-C part of the yard open.",
        "A9. Ducts do NOT come down to the parking (boss): they end at the floor-1 slab (TOS +4.00), pipes under the slab; lift pit below the foundation top (lowered foundation, depth per supplier).",
        "A10. Parking ventilation: DG1 grille + WG1 + rear windows WG2, WG3 + DG4 (natural); mechanical to check. Mobhas 3 not checked.",
        "A11. BOSS DECISION (T38d): half landing (T41: FFL +2.17) is carried ON THE STAIR COLUMNS by a landing beam framing into the columns",
        "     at the landing corners (axis 2, A-B). The independent support (coordination 57) is dropped. Structural: short-column check.",
        "FA11",
    ]
    for k, s in enumerate(notes):
        if s == "FA11":
            sh.text_uv(fa("تصمیم رئیس: پاگرد میانی +2.17 با تیر پاگرد روی ستون های پله - کنترل ستون کوتاه با مهندس سازه"),
                       sx0 - 0.3 + 0.3, yy - k * 0.21, 0.13, farsi=True, align=TA.MIDDLE_LEFT)
            continue
        sh.text_uv(s, sx0 - 0.3, yy - k * 0.21, 0.13 if k else 0.15, align=TA.MIDDLE_LEFT, width=0.85)

    # wall table for the structural engineer (on foundation / ground beams)
    walls = []
    for x0, x1, y0, y1, wid, t, note in GW:
        L = max(x1 - x0, y1 - y0)
        ops = [o for o in GOPEN if o[2] >= x0 - 1e-6 and o[3] <= x1 + 1e-6 and o[4] >= y0 - 1e-6 and o[5] <= y1 + 1e-6]
        walls.append(dict(id=wid, x=[x0, x1], y=[y0, y1], length=round(L, 3), thick_cm=t, note=note,
                          openings=[dict(tag=o[0], kind=o[1], width=round(max(o[3] - o[2], o[5] - o[4]), 3)) for o in ops],
                          net_length=round(L - sum(max(o[3] - o[2], o[5] - o[4]) for o in ops if o[1] in ("door", "gate", "lift")), 3)))
    tot = {}
    for w in walls:
        tot[w["thick_cm"]] = round(tot.get(w["thick_cm"], 0) + w["net_length"], 2)
    return dict(walls=walls, net_length_by_thickness_cm=tot, wall_height_on_ground_beam=H_GROUND - 0.50,
                stair=STAIR_G, stair_typical=STAIR_T, stalls=STALLS, levels=LEVELS, levels_T41=LEVELS_T41, rear_yard=YARD,
                landing_support="T38d boss decision (T41 level: parking half landing FFL +2.17, TOS ~+2.09): half landing carried on the stair columns (axis 2, A-B side) by a "
                                "landing beam framing into the columns at the landing corners; independent support (coord. 57) "
                                "dropped; structural: short-column check of those columns at ~+2.09 (parking) and at +5.70 / +9.10 / +12.50 (floors)",
                storages=[dict(id=t, name=n, x=[-0.05, 2.449], y=[a, b], area_m2=round(2.499 * (b - a), 2)) for t, n, a, b in STORES],
                front_doors=FRONT, walls_removed_T38=GW_REMOVED_T38,
                yard_structures=yard_structures(),
                parking_extension_T38c="REVERTED in T38d: parking ends inside the building line; rear wall G-R2 restored (DG4, WG2)",
                stall_units={"P1": "unit floor 3", "P2": "unit floor 2", "P3": "unit floor 1 (tandem partner of P2, in front of it)"},
                building_vs_yard="walls = on the building ground beams / foundation (SAFE line loads); yard_structures.walls = "
                                 "separate light structure on grade (not ETABS / SAFE building). Niche walls G-F1/G-N1/G-N2 are "
                                 "building walls but NOT on the axis-1 ground beam (0.55-0.75 behind it): own strip footing / tie beam",
                entry_niche_T38d="superseded by entry_niche_T39 (depth 0.80 -> 0.50)",
                entry_niche_T39=NICHE,
                cars=dict(block="CAR_SEDAN", size=[1.80, 4.50], layer="A-PRKG-CARS", stalls=["P1", "P2", "P3"]),
                task="T41 2026-10-24 (Rev.9): levels from clear heights (storeys 4.00 / 3.40 / 3.30), stairs redesigned. "
                     "T39 2026-10-23 (Rev.8): entry niche depth 0.50 (door wall G-F1 at Y 0.25-0.45 behind the columns A1/B1, "
                     "returns G-N1/G-N2 removed); sedan block in P1-P3; P1 Y 1.85-6.85. T38d: stalls 2.50 x 5.00, rear wall "
                     "G-R2 restored, half landing +1.75 on the stair columns (landing beam)")


def yard_structures():
    walls = []
    for x0, x1, y0, y1, wid, t, note in YW:
        L = max(x1 - x0, y1 - y0)
        ops = [o for o in YOPEN if o[2] >= x0 - 1e-6 and o[3] <= x1 + 1e-6 and o[4] >= y0 - 1e-6 and o[5] <= y1 + 1e-6]
        walls.append(dict(id=wid, x=[x0, x1], y=[y0, y1], length=round(L, 3), thick_cm=t, note=note,
                          openings=[o[0] for o in ops], net_length=round(L - sum(o[3] - o[2] for o in ops), 3)))
    tot = {}
    for w in walls:
        tot[w["thick_cm"]] = round(tot.get(w["thick_cm"], 0) + w["net_length"], 2)
    rooms = [dict(id=tg, name=n, x=[x0, x1], y=list(YROOM_Y), area_m2=round((x1 - x0) * (YROOM_Y[1] - YROOM_Y[0]), 2))
             for tg, n, x0, x1 in YROOMS]
    return dict(note="separate light structure on grade in the rear yard (NOT on the building frame / ETABS); "
                     "walls h ~2.40-2.60, light roof; joint to the building; boundary walls on the approx. property line",
                walls=walls, net_length_by_thickness_cm=tot, rooms=rooms,
                tank=dict(volume_l=2000, load_kN=22, where="pump room MR (A-B part, T38c), on grade slab, centre X 0.75 Y 21.60"),
                passage_depth=1.30, meters="EM on Y-F (passage side), GM niche in Y-A; utilities may require street access")


def main():
    import sys
    rev8_sheets.M = sys.modules[__name__]
    ctb_paths = make_ctb()
    dxf6, geom6 = build_rev6()
    g6 = json.load(open(geom6, encoding="utf-8"))
    doc = ezdxf.readfile(dxf6)
    # layers / linetypes
    if "PHANTOM" not in doc.linetypes:
        doc.linetypes.add("PHANTOM", pattern=[1.00, 0.50, -0.10, 0.10, -0.10, 0.10, -0.10], description="Phantom ____ _ _ ____")
    if "HIDDEN" not in doc.linetypes:
        doc.linetypes.add("HIDDEN", pattern=[0.30, 0.20, -0.10], description="Hidden __ __ __")
    for name, (c, lt, lw, desc) in LAYERS.items():
        if name in doc.layers:
            lay = doc.layers.get(name)
            lay.dxf.color, lay.dxf.linetype, lay.dxf.lineweight = c, lt, lw
        else:
            lay = doc.layers.add(name, color=c, linetype=lt, lineweight=lw)
        lay.description = desc
    doc.layers.get("0").dxf.lineweight = 13
    sh_t = relayer_typical(doc)
    for old in ("A-COLUMN", "A-STAIR", "A-SHAFT", "A-OPENING", "A-RAIL", "A-DIM", "A-AXIS", "A-TEXT", "A-SHEET"):
        if old in doc.layers:
            doc.layers.remove(old)
    # T39: floors 1-3 = one sheet each (floor 2 / 3 = copies of floor 1), then floor-specific texts
    rev8_sheets.copy_typical(doc, [f[0] for f in FLOORS[1:]])
    for dx, no, lay, en, fan, lev, stall in FLOORS:
        rev8_sheets.floor_sheet(doc, dx, no, en, fan, lev, stall)
    rev8_sheets.car_block(doc)
    cols = [(C19_X, y) if abs(x - C19_OLD) < 0.01 else (x, y) for x, y in g6["columns_etabs"]]
    gres = ground(doc, cols)
    rres = rev8_sheets.roof_sheet(doc, DXR, cols)
    sres = rev8_sheets.stair_house_sheet(doc, DXS)
    sheets = {no: (name, sheet_window(dx)) for no, (dx, name) in SHEETS.items()}
    rev8_sheets.add_layouts(doc, sheets, CTB_NAME)
    if "A-FURN" in doc.layers and not doc.modelspace().query('*[layer=="A-FURN"]'):
        doc.layers.remove("A-FURN")
    doc.header["$LWDISPLAY"] = 1
    doc.set_modelspace_vport(height=31, center=(30.0, 0.0))
    dxf8 = os.path.join(TMP, "Merage3_arch_Rev10.dxf")
    doc.saveas(dxf8)
    gres.update(rev=REV, sheets={no: dict(layout=v[0], model_window=v[1]) for no, v in sheets.items()}, roof_T41=rres, stair_house_T43=sres,
                ctb=ctb_paths, layers={k: dict(color=v[0], linetype=v[1], lineweight_mm=v[2] / 100, desc=v[3]) for k, v in LAYERS.items()})
    json.dump(gres, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    scr = os.path.join(TMP, "save10.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{OUT_DWG}"\n')
    if os.path.exists(OUT_DWG):
        os.remove(OUT_DWG)
    r = subprocess.run([ACCORE, "/i", dxf8, "/s", scr, "/l", "en-US"], capture_output=True, timeout=300)
    if not os.path.exists(OUT_DWG):
        print(r.stdout.decode("utf-16-le", errors="ignore")[-2000:])
        raise SystemExit("DWG not written")
    print("DWG:", OUT_DWG, os.path.getsize(OUT_DWG))
    print(json.dumps(dict(net=gres["net_length_by_thickness_cm"], ctb=ctb_paths), ensure_ascii=False))


if __name__ == "__main__":
    main()
