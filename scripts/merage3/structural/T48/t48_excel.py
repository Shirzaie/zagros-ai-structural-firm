# -*- coding: utf-8 -*-
"""Task 48: rebar schedule workbook Merage3_Rev6c_rebar_schedule.xlsx from t48_design.json + t48_hand_checks.json"""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "t48_design.json"), encoding="utf-8"))
H = json.load(open(os.path.join(HERE, "t48_hand_checks.json"), encoding="utf-8"))
FL = {"Story1": "طبقه‌ی اول (روی پارکینگ) +4.00", "Story2": "طبقه‌ی دوم +7.40", "Story3": "طبقه‌ی سوم +10.80", "Story4": "بام +14.20", "Story5": "بام خرپشته +17.50"}
CFL = {"Story1": "پارکینگ (±0.00 تا +4.00)", "Story2": "طبقه‌ی اول (+4.00 تا +7.40)", "Story3": "طبقه‌ی دوم (+7.40 تا +10.80)", "Story4": "طبقه‌ی سوم (+10.80 تا +14.20)", "Story5": "خرپشته (+14.20 تا +17.50)"}
wb = Workbook()
thin = Side(style="thin", color="999999"); B = Border(left=thin, right=thin, top=thin, bottom=thin)
def sheet(ws, head, rows, widths):
    ws.sheet_view.rightToLeft = True
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDEBF7"); c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows():
        for c in row:
            c.border = B
            if c.row > 1:
                c.alignment = Alignment(horizontal="center", vertical="center")
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "A2"
ws = wb.active; ws.title = "تیرها"
rows = []
order = ["Story1", "Story2", "Story3", "Story4", "Story5"]
for r in sorted(D["beams"], key=lambda r: (order.index(r["story"]), int(r["label"][1:]) if r["label"][1:].isdigit() else 99)):
    kind = "کنسول" if (r["label"] in ("B3", "B5", "B6") and r["story"] != "Story5") else ("تیر قلاب آسانسور" if r["label"] == "BH" else ("کنسول خرپشته" if r["label"] in ("B3", "B5") else "تیر"))
    top_mid = r["top"] if kind not in ("کنسول",) else "3φ25 (سراسری)"
    rows.append([FL[r["story"]], r["label"], r["label_etabs"], kind, r["sec"].replace("BW", "").replace("xH", "×"), r["L"], r["topI"], r["topJ"], top_mid,
                 r["bot"], r["bot"], r["web"] or "-", r["hoop_h"], r["hoop_m"], r.get("legs", 2) if kind != "کنسول" else 2,
                 r.get("AsTop_req"), r.get("AsBot_req"), r.get("Al_req"), r.get("q_h"), "OK" if r["ok"] else "کنترل"])
sheet(ws, ["تراز", "تیر (پروژه)", "برچسب ETABS", "نوع", "b×h (cm)", "طول c/c (m)", "بالا تکیه‌گاه I", "بالا تکیه‌گاه J", "بالا وسط دهانه",
           "پایین تکیه‌گاه", "پایین وسط دهانه", "میلگرد جان (پیچش)", "خاموت ناحیه‌ی ویژه (2h)", "خاموت وسط", "تعداد شاخه",
           "As بالا لازم (mm²)", "As پایین لازم", "Al لازم", "q = Av/s+2At/s", "نتیجه"], rows,
      [22, 9, 9, 14, 9, 8, 15, 15, 13, 15, 15, 11, 18, 18, 8, 10, 10, 8, 9, 7])
ws = wb.create_sheet("ستون‌ها")
rows = []
for c in sorted(D["columns"], key=lambda c: (order.index(c["story"]), int(c["label"][1:]))):
    rows.append([CFL[c["story"]], c["label"], c["sec"].split("/")[0].replace("C", "").replace("X", "×"), c["bars"], c["legs"], c["lo_mm"], c["hoop"], c["hoop_mid"],
                 "φ12@85 (در چشمه‌ی اتصال، 18.8.3.1)", round(c["pmm"], 3), c["combo"], round(c["v"], 2), "OK" if c["pmm"] <= 1 and c["v_ok"] else "رد"])
sheet(ws, ["طبقه", "ستون", "b×h (cm)", "میلگرد طولی", "شاخه در هر جهت", "lo (mm)", "خاموت ناحیه‌ی ویژه lo", "خاموت وسط ستون", "خاموت اتصال",
           "PMM", "ترکیب حاکم", "Av/s لازم (mm²/mm)", "نتیجه"], rows, [24, 7, 9, 11, 10, 8, 16, 15, 24, 8, 18, 11, 7])
ws = wb.create_sheet("خاموت ستون‌ها")
rows = [[k, v["bars"], f"{v['rho']}%", v["legs"], v["hoop"], v["Ash_s_req"], v["Ash_s_prov"], v["s_max"], v["hoop_mid"], v["cap_mid"]] for k, v in D["column_hoops"].items()]
sheet(ws, ["مقطع", "طولی", "ρ", "شاخه", "خاموت lo", "Ash/s لازم", "Ash/s موجود", "s حداکثر", "خاموت وسط", "ظرفیت وسط (mm²/mm)"], rows, [16, 9, 7, 6, 10, 10, 10, 9, 10, 12])
ws = wb.create_sheet("پله، کنسولک، قلاب")
st = H["stair_waist_t200"]; jt = H["joist_7.5m"]; tb = H["tie_beams"]; hb = H["hook_beam_BH"]
rows = [["تیرچه‌های دهانه‌ی 7.5 (آکس 1–2، A–B و B–C، همه‌ی طبقات)", "جهت / طول", "Y (دهانه‌ی 7.5)، پشت‌درپشت تیرها، طول 8.00 m، فاصله 0.50 (فرض)", f"As لازم هر تیرچه {jt['As_req_mm2 (d 270)']} mm² ⇒ 2φ16 پایین (جدول سازنده)؛ ⚠️ h 0.31 < l/21 = 0.36"],
        ["تای‌بیم TB (۳ عدد در هر دهانه‌ی 7.5)", "محل", "Y = 1.875 / 3.75 / 5.625", f"{tb['section']}؛ {tb['bars']}؛ {tb['anchorage']}"],
        ["تیرچه‌های سقف خرپشته", "جهت", "X (دهانه‌ی 2.3)، دستور رئیس", "بدون تای‌بیم (دستور داده نشده)"],
        ["دهانه‌های 6.0 و 5.31 و کنسول‌ها", "جهت", "بدون تغییر (X)", "سؤال از رئیس"],
        ["دال شیبدار پله t = 0.20 (دهانه‌ی افقی 6.00)", "اصلی پایین", st["As_prov"], f"As لازم {st['As_req_mm2_m']} mm²/m، Mu {st['Mu_kNm_m']} kN·m/m"],
        ["", "توزیع", st["distribution"], ""], ["", "بالا در دو سر", "φ10@200 به طول L/4", "کنترل ترک"],
        ["", "خیز", f"زنده {st['delta_L_mm']} ≤ {st['L/360_mm']} ✓؛ بلندمدت {st['delta_long_term_plus_L_mm']} > L/240 = {st['L/240_mm']} ⚠️", "تصمیم رئیس"],
        ["دال پاگرد t = 0.20", "اصلی", "φ16@125 ادامه‌ی میلگرد بازو، توزیع φ10@200", "جزء همان نوار یک‌طرفه"],
        ["تیر پاگرد 30×40", "بالا / پایین", "3φ16 / 3φ16", "Mu 40.8 kN·m (As 370)، Vu 69 kN؛ خاموت φ10@100 بسته؛ روی کنسولک‌ها، بدون اتصال به ستون"],
        ["کنسولک نشیمن (C2، C6، هر تراز)", "کششی اصلی Asc", "4φ14 (616 ≥ 394)", "Vu 69.8، Nuc 14.0 kN؛ av/d 0.32"],
        ["", "خاموت بسته Ah", "3φ10 بسته در 2d/3 (471 ≥ 174)", "ابعاد 400×300×450، لبه ≥ 250"],
        ["", "نشیمن", "بالشتک الاستومری 150×250×20 + PTFE / زنگ‌نزن", "تنش 1.86 MPa؛ درز 40 mm دور ستون؛ میل‌راهنمای φ16 در غلاف شکاف‌دار ±40"],
        ["سر بالای پله روی B36", "نشیمن لغزشی", "Nib تیر B36 + PTFE، طول نشیمن ≥ 220", "درز 70 mm در جهت پله؛ بدون ادامه‌ی میلگرد"],
        ["تیر قلاب BH 25×40 (Y 14.65)", "پایین / بالا", f"{hb['bottom']} / {hb['top']}", f"خاموت {hb['stirrups']}؛ Mu {hb['Mu_kNm(1.2D)']}، Vu {hb['Vu_kN']} kN؛ دو سر مفصلی"],
        ["", "آویز", "2φ10 خاموت آویز هر طرف قلاب", "ورق مدفون / پیچ چشمی طبق سازنده"],
        ["چاهک آسانسور", "عمق", "2.00 m؛ کف چاهک −2.00 از روی پی (معمار Rev.12)", "جزء پی (SAFE)؛ دیوار و کف چاهک در نقشه‌ی پی"],
        ["غلاف‌های φ125 سقف خرپشته", "تقویت", "1φ10 کنار هر غلاف در لایه‌ی رویه", "بین تیرچه‌ها، (0.30, 14.10) و (0.30, 15.20)؛ 37 mm تا بَر تیر"]]
sheet(ws, ["عضو", "جزء", "آرماتور", "توضیح"], rows, [32, 18, 40, 60])
ws = wb.create_sheet("یادداشت‌ها")
notes = ["مدل: ETABS/Merage3_Rev6c.EDB، ACI 318-19، ۵۱ ترکیب A22، Ax = 1.17 (خروج از مرکز 5.85٪).",
         "بتن f'c = 25 MPa؛ طولی S400؛ خاموت S340؛ پوشش آزاد تیر و ستون 40 mm.",
         "تیرها: 4φ16 بالا و 4φ16 پایین سراسری؛ اضافه‌ی بالا از بَر ستون تا Ln/3؛ اضافه‌ی پایین سراسری.",
         "خاموت تیر: ناحیه‌ی ویژه 2h از بَر (s ≤ d/4، 6db، 150)؛ وسط s ≤ d/2. سه‌شاخه در B38، B10، B12 (دستور رئیس) و B36 Story1.",
         "ستون‌ها: lo ≥ max(h، Ln/6، 450)؛ خاموت lo طبق Ash (18.7.5.4)؛ وسط s ≤ min(6db، 150) (18.7.5.5)؛ در چشمه‌ی اتصال مثل lo.",
         "وصله‌ی ستون‌ها فقط در نیمه‌ی میانی ارتفاع آزاد، کلاس B، با خاموت @ ≤ 100.",
         "اتصال دال به تیرها و جمع‌کننده‌ها: نیرو ۲۵٪ افزایش یابد (ASCE 7-22 بند 12.3.3.4، نامنظمی پیچشی): میلگرد انتظار دال در تیرهای پیرامونی φ10@200 به‌جای @250.",
         "درز میان‌قاب 80 mm (دستور رئیس).", "تیرچه‌ها در دهانه‌ی 7.5 در جهت Y با ۳ تای‌بیم؛ خرپشته در جهت X؛ دال پله 0.20؛ چاهک 2.00 (دستورهای رئیس 2026-10-31)."]
ws.sheet_view.rightToLeft = True
for n in notes:
    ws.append([n])
ws.column_dimensions["A"].width = 140
out = os.path.join(HERE, "Merage3_Rev6c_rebar_schedule.xlsx")
wb.save(out); print(out)
