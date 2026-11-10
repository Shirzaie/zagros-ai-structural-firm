# -*- coding: utf-8 -*-
"""Zagros Ahan-Beton integrated pipeline: ETABS model -> AutoCAD drawings, SAFE foundation, Tekla 3D model.

One file, driven by a JSON config; every parameter can be overridden on the command line and the
whole chain re-run. Contract (data model, stage signature, company rules): CONTRACT.md next to this file.

    python zagros_pipeline.py --config ../../Merage3/pipeline_config.json
    python zagros_pipeline.py --config ... --stages etabs,autocad
    python zagros_pipeline.py --config ... --set safe.ks=24000 --set autocad.scale=50

Stages run in order etabs -> autocad -> safe -> tekla. A stage whose software is missing returns
ok=False with a warning and the chain goes on (unless "strict": true). Outputs land in a new
folder <project>/work/pipeline/<run_id>/ ; nothing is deleted and the original model is never saved.
All outputs are drafts until approved by the engineer of record.
"""
import argparse
import copy
import datetime
import json
import os
import sys
import traceback
from pathlib import Path

DRAFT_FA = "پیش‌نویس — منتظر تأیید مهندس محاسب"

DEFAULTS = {
    "strict": False,
    "project": {"name": "Project", "dir": ".", "engineer": "رحمت‌الله شیرزایی"},
    "etabs": {
        "model": "",                 # .EDB; empty -> use "geometry" json only
        "geometry": "",              # fallback / offline input (Merage3_geometry.json format)
        "run_analysis": False,       # True: run analysis + concrete design on a copy before extracting
        "reaction_cases": ["Dead", "SuperDead", "Live", "EXP", "EXN", "EYP", "EYN"],
        "temp_dir": r"C:\ZagrosTemp",
    },
    "autocad": {
        "accoreconsole": r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe",
        "scale": 100, "sheet": "A1",
        "sheets": ["grid_columns", "beam_framing", "column_schedule", "beam_details"],
        "plot_pdf": True,
    },
    "safe": {
        "exe_tlb": r"C:\Program Files\Computers and Structures\SAFE 23\NativeAPI\x64\SAFEv1.tlb",
        "type": "mat",               # mat | strip
        "thickness": 700, "edge_offset": 600,
        "qa": 150.0, "ks": [12000, 18000, 24000],   # kPa, kN/m3 (estimated -> flagged)
        "fc": 25.0, "fy": 400.0, "cover": 75,
        "run_design": True,
    },
    "tekla": {
        "mode": "auto",              # auto | api | ifc
        "bin": r"C:\Program Files\Tekla Structures\2026.0\bin",
        "concrete_by_fc": {"20": "C20/25", "25": "C25/30", "30": "C30/37", "35": "C35/45"},
        "include_foundation": True, "include_rebar": True,
    },
    "rebar": {"bar_sizes": [10, 12, 14, 16, 18, 20, 22, 25, 28], "stirrup": 10, "cover_beam": 40, "cover_column": 40},
}

STAGE_ORDER = ["etabs", "autocad", "safe", "tekla"]


# ---------------------------------------------------------------- config
def deep_merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def parse_value(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def apply_override(cfg, item):
    key, _, value = item.partition("=")
    node = cfg
    parts = key.strip().split(".")
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    node[parts[-1]] = parse_value(value)


def load_config(path, overrides):
    with open(path, encoding="utf-8") as f:
        cfg = deep_merge(DEFAULTS, json.load(f))
    for item in overrides or []:
        apply_override(cfg, item)
    base = Path(path).resolve().parent
    cfg["project"]["dir"] = str((base / cfg["project"]["dir"]).resolve())
    for sec, key in (("etabs", "model"), ("etabs", "geometry")):
        if cfg[sec][key]:
            cfg[sec][key] = str((base / cfg[sec][key]).resolve())
    return cfg


# ---------------------------------------------------------------- stages
# Each stage: stage_<name>(model, cfg, out, log) -> {"ok", "files", "summary", "warnings"}
# The bodies below are filled in by the discipline owners (see CONTRACT.md).

# >>> STAGE etabs
# <<< STAGE etabs

# >>> STAGE autocad
# <<< STAGE autocad

# >>> STAGE safe
# <<< STAGE safe

# >>> STAGE tekla
# <<< STAGE tekla


def _load_dev_stages():
    """While the single file is being assembled, stage bodies may live in stages/stage_<name>.py."""
    here = Path(__file__).resolve().parent / "stages"
    found = {}
    for name in STAGE_ORDER:
        fn = globals().get("stage_" + name)
        if fn is None and (here / f"stage_{name}.py").exists():
            sys.path.insert(0, str(here))
            mod = __import__(f"stage_{name}")
            fn = getattr(mod, "stage_" + name)
        if fn is not None:
            found[name] = fn
    return found


# ---------------------------------------------------------------- runner
def run(cfg, stages):
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(cfg["project"]["dir"]) / "work" / "pipeline" / run_id
    out.mkdir(parents=True, exist_ok=False)
    logf = open(out / "pipeline.log", "a", encoding="utf-8")

    def log(msg):
        line = f"{datetime.datetime.now():%H:%M:%S} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    with open(out / "config_used.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)

    model = {"project": cfg["project"]["name"], "units": "N, mm"}
    geo = cfg["etabs"]["geometry"]
    if geo and os.path.exists(geo):
        with open(geo, encoding="utf-8") as f:
            model.update(json.load(f))
        log(f"geometry loaded from {geo}")

    available = _load_dev_stages()
    results = {}
    for name in STAGE_ORDER:
        if name not in stages:
            continue
        fn = available.get(name)
        if fn is None:
            results[name] = {"ok": False, "files": [], "summary": {}, "warnings": ["stage not implemented"]}
            log(f"[{name}] not implemented - skipped")
            continue
        (out / name).mkdir(exist_ok=True)
        log(f"[{name}] start")
        try:
            res = fn(model, cfg, out, log) or {}
        except Exception as e:
            if cfg["strict"]:
                raise
            res = {"ok": False, "files": [], "summary": {}, "warnings": [f"{type(e).__name__}: {e}"]}
            log(traceback.format_exc())
        res.setdefault("ok", False)
        res.setdefault("files", [])
        res.setdefault("summary", {})
        res.setdefault("warnings", [])
        results[name] = res
        log(f"[{name}] {'OK' if res['ok'] else 'NOT OK'} files={len(res['files'])} warnings={len(res['warnings'])}")
        with open(out / "model.json", "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=1, default=str)

    write_report(cfg, out, results)
    logf.close()
    return out, results


def write_report(cfg, out, results):
    lines = [f"# گزارش اجرای اسکریپت یکپارچه — {cfg['project']['name']}", "",
             f"**{DRAFT_FA}**", "", f"پوشه‌ی خروجی: `{out}`", "",
             "| مرحله | وضعیت | فایل‌ها | هشدارها |", "|---|---|---|---|"]
    for name in STAGE_ORDER:
        if name in results:
            r = results[name]
            lines.append(f"| {name} | {'✅' if r['ok'] else '⚠️'} | {len(r['files'])} | {len(r['warnings'])} |")
    for name, r in results.items():
        lines += ["", f"## {name}"]
        for k, v in r["summary"].items():
            lines.append(f"- {k}: {v}")
        for w in r["warnings"]:
            lines.append(f"- ⚠️ {w}")
        for p in r["files"]:
            lines.append(f"- `{p}`")
    (out / "pipeline_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--stages", default=",".join(STAGE_ORDER))
    ap.add_argument("--set", action="append", default=[], metavar="key.sub=value")
    a = ap.parse_args(argv)
    cfg = load_config(a.config, a.set)
    stages = [s.strip() for s in a.stages.split(",") if s.strip()]
    out, results = run(cfg, stages)
    print(f"\nreport: {out / 'pipeline_report.md'}")
    return 0 if all(r["ok"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
