# -*- coding: utf-8 -*-
"""Re-run the Rev.6 generator (inputs/make_basis_plan_dwg_rev6.py, unchanged copy) in --dxf-only mode
with all output paths redirected to a temp folder, so the Rev.6 final files in arch/ are never touched.

    from rev6_source import build_rev6   ->  (dxf_path, geometry_json_path)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
TMP = "C:/ZagrosTemp/arch7"


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
    }
    for a, b in rep.items():
        assert a in src, a
        src = src.replace(a, b)
    argv = sys.argv
    sys.argv = ["rev6", "--dxf-only"]
    try:
        exec(compile(src, "make_basis_plan_dwg_rev6", "exec"), {"__name__": "__main__", "__file__": TMP + "/x.py"})
    finally:
        sys.argv = argv
    return TMP + "/Merage3_arch_plan_BASIS.dxf", TMP + "/r6_geom_arch.json"


if __name__ == "__main__":
    print(build_rev6())
