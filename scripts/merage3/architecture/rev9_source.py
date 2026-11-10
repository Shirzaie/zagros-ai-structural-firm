# -*- coding: utf-8 -*-
"""Rev.9 (task 41): re-run the Rev.6 generator (inputs/make_basis_plan_dwg_rev6.py, unchanged copy) in --dxf-only
mode, output redirected to a temp folder (arch/ is never touched), with the T41 storey heights:

  - storeys from the boss's CLEAR heights + beam 0.50: parking 4.00, typical 3.40 (was 3.50 / 2.90 from ETABS Rev5)
  - door / window schedule heads: u/s beam = FFL + 2.82, u/s slab = FFL + 3.01 (was 2.32 / 2.51)
  - the Rev.6 stair (10 treads 0.30 per flight, generic labels) is NOT drawn here: rev9_sheets.floor_sheet draws
    the T41 stair per floor (10 + 10 risers x 0.170, treads 0.30) with its counts and landing levels.

    from rev9_source import build_rev6   ->  (dxf_path, geometry_json_path)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
TMP = "C:/ZagrosTemp/arch9"


def build_rev6():
    os.makedirs(TMP, exist_ok=True)
    src = open(os.path.join(HERE, "inputs", "make_basis_plan_dwg_rev6.py"), encoding="utf-8").read()
    rep = {
        'PDF = os.path.join(PRJ, "arch", "memary500_Model_600_BASIS.pdf")':
            f'PDF = "{HERE}/inputs/memary500_Model_600_BASIS.pdf"',
        'OUT_DWG = os.path.join(PRJ, "arch", "Merage3_arch_plan_BASIS.dwg")': f'OUT_DWG = "{TMP}/never.dwg"',
        'OUT_JSON = os.path.join(HERE, "task08c_basis_geometry.json")': f'OUT_JSON = "{TMP}/r6_geom.json"',
        'OUT_JSON_ARCH = os.path.join(PRJ, "arch", "Merage3_arch_plan_BASIS_geometry.json")':
            f'OUT_JSON_ARCH = "{TMP}/r6_geom_arch.json"',
        'GEOM = os.path.join(PRJ, "work", "etabs", "Merage3_geometry.json")':
            f'GEOM = "{HERE}/inputs/Merage3_geometry.json"',
        'tmp = tempfile.mkdtemp(prefix="m3_basis_")': f'tmp = "{TMP}"',
        'print(json.dumps(dict(K=K, dims=dim_check, totals=totals, counts=counts), ensure_ascii=False, indent=1))': 'pass',
        # T41: storey heights from the boss's clear heights (clear + beam 0.50)
        'storeys = {"ground (Base->Story1)": (stories["Story1"] - stories["Base"]) / 1000,\n'
        '               "typical (Story1..3 -> next)": (stories["Story2"] - stories["Story1"]) / 1000}':
            'storeys = {"ground (Base->Story1)": 4.00, "typical (Story1..3 -> next)": 3.40}   # T41 (boss): clear + beam',
        '    h_typ = 2.90\n': '    h_typ = 3.40   # T41\n',
        '"Heights in m above finished floor (FFL), typical storey h=2.90: u/s beam = FFL+2.32, u/s slab = FFL+2.51;"':
            '"Heights in m above finished floor (FFL), typical storey 3.40 (clear 2.90 + beam 0.50): u/s beam = FFL+2.82, u/s slab = FFL+3.01;"',
        '"ground storey h=3.50: u/s beam = FFL+2.92, u/s slab = FFL+3.11.  Slab 0.31, beams 0.50 (ETABS); floor finish 0.08."':
            '"parking storey 4.00 (clear 3.50 + beam 0.50): u/s beam = FFL+3.42.  Slab 0.31, beams 0.50; floor finish 0.08 (T41)."',
    }
    for a, b in rep.items():
        assert a in src, a
        src = src.replace(a, b)
    a = src.index("    # stair regenerated")
    b = src.index("    # ---------------- Rev.6: door symbols")
    src = src[:a] + "    # T41: stair drawn per floor by rev9_sheets.floor_sheet\n\n" + src[b:]
    argv = sys.argv
    sys.argv = ["rev6", "--dxf-only"]
    try:
        exec(compile(src, "make_basis_plan_dwg_rev6", "exec"), {"__name__": "__main__", "__file__": TMP + "/x.py"})
    finally:
        sys.argv = argv
    return TMP + "/Merage3_arch_plan_BASIS.dxf", TMP + "/r6_geom_arch.json"


if __name__ == "__main__":
    print(build_rev6())
