# -*- coding: utf-8 -*-
"""Merage3 task 58 (2026-11-07, boss order): dropdowns for the column hoops (size, single / double) and the tie beam TB 30x30
(top / bottom bar count and size, hoop size, single / double, hoops between two joists). Saves t55_options.json and, on request,
rebuilds: t55_design.py -> t55_hand_checks.py -> make_struct_Rev5.py -> plot_Rev5.py. Run: python t55_options_gui.py"""
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = os.path.join(HERE, "t55_options.json")
STEPS = ["t55_design.py", "t55_hand_checks.py", "make_struct_Rev5.py", "plot_Rev5.py"]
TYPE = {"تکی (یک خاموت بسته + سنجاقی)": "single", "دوبل (دو خاموت بسته)": "double"}
TYPE_TB = {"تکی": "single", "دوبل (دو خاموت بسته)": "double"}

o = json.load(open(OPT, encoding="utf-8"))
root = tk.Tk()
root.title("Merage3 - تنظیم خاموت ستون و تای بیم 30x30")
F = ("Tahoma", 10)
root.option_add("*Font", F)
frm = ttk.Frame(root, padding=12)
frm.grid()
V = {}


def row(r, label, key, values, cur):
    ttk.Label(frm, text=label, anchor="e", justify="right").grid(row=r, column=1, sticky="e", padx=6, pady=3)
    v = tk.StringVar(value=cur)
    ttk.Combobox(frm, textvariable=v, values=values, state="readonly", width=30, justify="center").grid(row=r, column=0, pady=3)
    V[key] = v


def inv(d, val):
    return next(k for k, x in d.items() if x == val)


ttk.Label(frm, text="خاموت ستون ها (همه ى مقاطع)", font=("Tahoma", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="e", pady=(0, 4))
row(1, "نمره ى خاموت ستون", "col.db", ["10", "12"], str(o["col"]["db"]))
row(2, "نوع خاموت ستون", "col.type", list(TYPE), inv(TYPE, o["col"]["type"]))
ttk.Separator(frm).grid(row=3, column=0, columnspan=2, sticky="we", pady=8)
ttk.Label(frm, text="تاى بيم TB 30x30", font=("Tahoma", 11, "bold")).grid(row=4, column=0, columnspan=2, sticky="e", pady=(0, 4))
t = o["tb"]
row(5, "تعداد ميلگرد بالا", "tb.nTop", ["2", "3", "4"], str(t["nTop"]))
row(6, "نمره ى ميلگرد بالا", "tb.dbTop", ["10", "12", "14", "16", "18"], str(t["dbTop"]))
row(7, "تعداد ميلگرد پايين", "tb.nBot", ["2", "3", "4"], str(t["nBot"]))
row(8, "نمره ى ميلگرد پايين", "tb.dbBot", ["10", "12", "14", "16", "18"], str(t["dbBot"]))
row(9, "نمره ى خاموت", "tb.hoopDb", ["8", "10", "12"], str(t["hoopDb"]))
row(10, "نوع خاموت", "tb.hoopType", list(TYPE_TB), inv(TYPE_TB, t["hoopType"]))
row(11, "تعداد خاموت بين دو تيرچه", "tb.nHoop", ["1", "2", "3", "4"], str(t["nHoop"]))

msg = tk.Text(frm, width=78, height=14, font=("Consolas", 9))
msg.grid(row=13, column=0, columnspan=2, pady=(10, 0))


def say(s):
    msg.insert("end", s + "\n"); msg.see("end")


def save():
    o["col"] = {"db": int(V["col.db"].get()), "type": TYPE[V["col.type"].get()]}
    o["tb"] = {"nTop": int(V["tb.nTop"].get()), "dbTop": int(V["tb.dbTop"].get()), "nBot": int(V["tb.nBot"].get()),
               "dbBot": int(V["tb.dbBot"].get()), "hoopDb": int(V["tb.hoopDb"].get()), "hoopType": TYPE_TB[V["tb.hoopType"].get()],
               "nHoop": int(V["tb.nHoop"].get())}
    json.dump(o, open(OPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    say("saved t55_options.json: " + json.dumps(o, ensure_ascii=False))


def report():
    d = json.load(open(os.path.join(HERE, "t55_design.json"), encoding="utf-8"))
    say("COLUMN HOOPS (ACI 18.7.5.4 Ash):")
    for sec, h in d["column_hoops"].items():
        say(f"  {sec:14s} lo {h['hoop']:12s} mid {h['hoop_mid']:12s} legs {h['legs']}  Ash/s {h['Ash_s_prov']} >= {h['Ash_s_req']}  "
            + ("OK" if h["ok"] else "NOT OK (s < 50 mm or Ash short)"))
    bad = [c["label"] + " " + c["story"] for c in d["columns"] if not c.get("v_ok", True)]
    say("  column shear (mid hoops): " + ("OK" if not bad else "NOT OK " + ", ".join(bad)))
    hc = json.load(open(os.path.join(HERE, "t55_hand_checks.json"), encoding="utf-8"))["tie_beam_30x30"]
    say(f"TIE BEAM: {hc['bars']} | {hc['hoops']} | phiMn {hc['phiMn_kNm']} kNm (info, not in ETABS)")


def build(steps):
    def run():
        btn1.state(["disabled"]); btn2.state(["disabled"])
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        for s in steps:
            say(f"> python {s} ...")
            r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                say(r.stdout[-800:] + r.stderr[-1500:]); say("STOPPED - error in " + s); break
            say("  done")
            if s == "t55_hand_checks.py":
                report()
        else:
            if "plot_Rev5.py" in steps:
                say("drawings: Merage3\\struct\\Merage3_struct_Rev5.dwg / .pdf")
        btn1.state(["!disabled"]); btn2.state(["!disabled"])
    save()
    threading.Thread(target=run, daemon=True).start()


bf = ttk.Frame(frm)
bf.grid(row=12, column=0, columnspan=2, pady=(8, 0))
btn1 = ttk.Button(bf, text="ذخيره و كنترل (بدون نقشه)", command=lambda: build(STEPS[:2]))
btn1.grid(row=0, column=1, padx=4)
btn2 = ttk.Button(bf, text="ذخيره، كنترل و ساخت نقشه ها (چند دقيقه)", command=lambda: build(STEPS))
btn2.grid(row=0, column=0, padx=4)
say("Pick the values, then press a button. Current file: " + OPT)
root.mainloop()
