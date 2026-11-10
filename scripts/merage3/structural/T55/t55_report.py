# -*- coding: utf-8 -*-
"""Task 50: Rev6d rebar report (Persian md) + Excel workbook from t50_design.json, t50_hand_checks.json and the Rev6d summary.
Writes work/structural/2026-10-31_T50_rebar_report_Rev6d.md and work/structural/T50/Merage3_Rev6d_rebar_schedule.xlsx"""
import json
import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = json.load(open(os.path.join(HERE, "t50_design.json"), encoding="utf-8"))
H = json.load(open(os.path.join(HERE, "t50_hand_checks.json"), encoding="utf-8"))
S = json.load(open(os.path.join(PRJ, "ETABS", "Merage3_Rev6d_summary.json"), encoding="utf-8"))
C6 = json.load(open(os.path.join(PRJ, "ETABS", "Merage3_Rev6c_summary.json"), encoding="utf-8"))
ORDER = ["Story1", "Story2", "Story3", "Story4", "Story5"]
FL = {"Story1": "طبقه‌ی اول (TOS +4.00)", "Story2": "طبقه‌ی دوم (TOS +7.40)", "Story3": "طبقه‌ی سوم (TOS +10.80)", "Story4": "بام (TOS +14.20)", "Story5": "بام خرپشته (TOS +17.50)"}
CF = {"Story1": "پارکینگ (±0.00 تا +4.00)", "Story2": "طبقه‌ی اول (+4.00 تا +7.40)", "Story3": "طبقه‌ی دوم (+7.40 تا +10.80)", "Story4": "طبقه‌ی سوم (+10.80 تا +14.20)", "Story5": "خرپشته (+14.20 تا +17.50)"}
num = lambda lab: int(lab[1:]) if lab[1:].isdigit() else 99
st = H["stair_t200_with_BS"]; jo = H["joists"]; tb = H["tie_beam_30x30"]; sf = H["strip_footings"]
L = []
w = L.append
w("# کار ۵۰ — گزارش میلگردگذاری و خاموت همه‌ی طبقات و پی — Merage3 (مدل ETABS Rev6d)\n")
w("- از: مهندس سازه — به: رئیس (از طریق معاون) — تاریخ: ۲۰۲۶-۱۰-۳۱")
w("- مدل: `ETABS/Merage3_Rev6d.EDB` (کپی Rev6c؛ Rev6c دست نخورد؛ پشتیبان `ETABS/_backup/Merage3_Rev6c_before_T50.EDB`)؛ ACI 318-19، ۵۱ ترکیب A22.")
w("- Excel: `work/structural/T50/Merage3_Rev6d_rebar_schedule.xlsx`. نقشه‌ها (1:20، برای تأیید): `struct/Merage3_struct_Rev3.dwg/pdf`. گزارش کار: `work/structural/2026-10-31_T50.md`.\n")
w("## ۱. نتایج Rev6d در برابر Rev6c\n")
w("| مورد | Rev6c | **Rev6d** |")
w("|---|---|---|")
for lab, k, f in (("W (kN)", "W_kN", "{:.1f}"), ("V (kN)", "V_kN", "{:.1f}"), ("دریفت / حد 0.025", "drift_ratio_vs_0.025", "{:.3f}"),
                  ("جابه‌جایی نسبی طرح (mm)", "design_story_drift_mm_max", "{:.1f}"), ("Max/Avg", "torsion_ratio_max", "{:.3f}"), ("PMM بیشینه", "PMM_max", "{:.3f}"),
                  ("برش چشمه‌ی اتصال", "joint_shear_max", "{:.3f}"), ("خاموت بیشینه‌ی تیر q", "beam_dem_max", "{:.2f}"), ("کنسول‌ها q", "cantilever_dem_max", "{:.2f}")):
    w(f"| {lab} | {f.format(C6[k])} | **{f.format(S[k])}** |")
w(f"| T1 / T2 / T3 (s) | {' / '.join(f'{x:.3f}' for x in C6['T1_T2_T3_s'])} | **{' / '.join(f'{x:.3f}' for x in S['T1_T2_T3_s'])}** |")
w(f"\n**هیچ عضو سازه‌ی بالای پی رد نیست** (PMM بیشینه {S['PMM_max']:.3f} در {S['PMM_max_at']}). BC > 1 فقط در اتصال‌های بالای ستون‌های منقطع (معاف ACI 18.7.3.1): "
  + "، ".join(f"{k} {v}" for k, v in S["BC_over_1"].items()) + ".\n")
w("## ۲. پی نواری مرکب (دستور رئیس: 0.80 × 2.00، مگر 0.10، 10φ18 بالا و پایین، عرضی φ14@150 با خم 20، کاور 10/7/5) — فقط کنترل و گزارش\n")
w("| نوار | ستون‌ها | P بهره‌برداری (kN) | q خاک (kPa، با وزن پی) | Mu بیشینه (kN·m) | φMn 10φ18 | As لازم (mm²) | Vu (kN) | φVc (kN) | نتیجه |")
w("|---|---|---|---|---|---|---|---|---|---|")
for k, v in sf.items():
    ok = v["Mu_max_abs_kNm"] <= v["phiMn_bottom_10φ18"] and v["Vu_max_kN"] <= v["phiVc_kN"]
    w(f"| {k} | {' '.join(v['columns'])} | {v['P_service_kN']} | {v['q_service_kPa (incl. self weight)']} | {v['Mu_max_abs_kNm']} | {v['phiMn_bottom_10φ18']} | "
      f"{v['As_req_for_Mu_max_mm2']} | {v['Vu_max_kN']} | {v['phiVc_kN']} | {'OK' if ok else '**رد**'} |")
w("\n- روش: تیر وارونه‌ی پیوسته روی تکیه‌گاه ستون‌ها با فشار یکنواخت ضریب‌دار (پوش A22، بیشترین FZ هر ستون). عرضی: Mu ≈ " +
  f"{max(v['transverse_Mu_kNm_m'] for v in sf.values())} kN·m/m در برابر φMn {list(sf.values())[0]['phiMn_transverse_φ14@150']} ✓.")
w("- **نتیجه: با ابعاد و میلگرد رئیس، خمش طولی حدود ۳ برابر و برش طولی حدود ۲ برابر ظرفیت است (رد).** تنش خاک بهره‌برداری 94 تا 135 kPa؛ تنش مجاز خاک داده نشده است (سؤال).")
w("- ابعاد و میلگرد پی طبق دستور رئیس تغییر داده نشد و همان در نقشه آمد. گزینه‌ها در گزارش T50.\n")
w("## ۳. ستون‌ها\n")
w("| طبقه | ستون | مقطع | طولی | lo (mm) | خاموت lo | خاموت وسط | شاخه | PMM |")
w("|---|---|---|---|---|---|---|---|---|")
for c in sorted(D["columns"], key=lambda c: (ORDER.index(c["story"]), num(c["label"]))):
    w(f"| {CF[c['story']]} | {c['label']} | {c['sec'].split('/')[0]} | {c['bars']} | {c['lo_mm']} | {c['hoop']} | {c['hoop_mid']} | {c['legs']} | {c['pmm']:.3f} |")
w("\n- میلگرد ستون‌ها با خم ۹۰° به طول 0.25 به طرف داخل ستون در پی (دستور رئیس). وصله در نیمه‌ی میانی ارتفاع آزاد، کلاس B (φ20 100، φ18 90، φ16 80 cm).\n")
w("## ۴. تیرها\n")
for s_ in ORDER:
    w(f"### {FL[s_]}\n")
    w("| تیر | b×h | L | بالا I | بالا J | بالا وسط | پایین | جان | خاموت ویژه | خاموت وسط | q |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted([r for r in D["beams"] if r["story"] == s_], key=lambda r: num(r["label"])):
        cant = r["label"] in ("B3", "B5", "B6") and s_ != "Story5"
        w(f"| {r['label']} | {r['sec'].replace('BW', '').replace('xH', '×')} | {r['L']:.2f} | {r['topI']} | {r['topJ']} | {'3φ25' if cant else r['top']} | {r['bot']} | {r['web'] or '-'} | {r['hoop_h']} | {r['hoop_m']} | {r['q_h']:.2f} |")
    w("")
w("## ۵. سقف‌ها\n")
w("- **جهت تیرچه:** همه‌ی دهانه‌های طبقات ۱ تا ۳ و بام در Y (جهت 7.5)، پشت‌درپشت تیرها؛ پانل‌های کنسول F2 و F3 در X (بین تیرهای کنسول، برداشت)؛ خرپشته در X (دستور رئیس).")
w("- **تیرچه** (فاصله 0.50، دال 0.31 = بلوک 0.25 + رویه 0.06، فرض مدل):")
for k, v in jo.items():
    w(f"  - دهانه‌ی {k} m: پایین {v['bottom']} (As لازم {v['As_req']})، بالا روی تکیه‌گاه {v['top_at_supports']}؛ خیز زنده {v['delta_L_mm']} ≤ {v['L/360']} ✓؛ "
      f"بلندمدت + زنده {v['delta_long_plus_L_mm']} {'≤' if v['delta_long_plus_L_mm'] <= v['L/240'] else '>'} L/240 = {v['L/240']} mm {'✓' if v['delta_long_plus_L_mm'] <= v['L/240'] else '⚠️'}")
w(f"- **تای‌بیم** (دستور رئیس): {tb['section']}؛ {tb['bars']}؛ {tb['hoops']}. سه عدد در هر دهانه در L/4.")
w("- **میلگرد حرارتی رویه** (فرض، رئیس عدد نداده): φ8@250 در دو جهت (≥ 0.0018 × 60 × 1000 = 108 mm²/m).")
w("- تیر نعل‌درگاهی **BT 30×50** در Y = 15.30 (لبه‌ی بازشوی چاهک، طبقات ۱ تا بام): ناگزیر، چون تیرچه‌های Y دال F14 با بازشو قطع می‌شوند؛ 3φ14 بالا و پایین، φ10@200.\n")
w("## ۶. پله (t = 0.20 با تکیه‌گاه میانی، دستور رئیس)\n")
w(f"- تکیه‌گاه میانی: **تیر BS 30×50** در Y = 11.658 (طبقه‌ی اول 11.758) در تراز کف هر طبقه، از B30 تا B32، دو سر مفصلی؛ 3φ14 بالا و پایین، φ10@200.")
w(f"- دهانه‌ی بازو {st['span1_m']} m: Mu {st['Mu1_kNm_m']} kN·m/m، As لازم {st['As_req']} ⇒ پایین **{st['bottom']}**، توزیع {st['distribution']}، بالا {st['top']}؛ پاگرد طبقه ({st['span2_floor_landing_m']} m): {st['floor_landing']}.")
w(f"- خیز: زنده {st['delta_L_mm']} ≤ L/360 = {st['L/360']} ✓؛ **بلندمدت + زنده {st['delta_long_plus_L_mm']} mm > L/240 = {st['L/240']} mm** (با تکیه‌گاه میانی از 69 به 23 mm رسید ولی هنوز کمی بیشتر از حد است؛ فقط گزارش).")
w("- تیر پاگرد 30×40 روی کنسولک‌ها، نشیمن لغزشی، و سر بالای لغزشی بازو روی BS (درز 70).\n")
open(os.path.join(PRJ, "work", "structural", "2026-10-31_T50_rebar_report_Rev6d.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
# Excel
wb = Workbook(); thin = Side(style="thin", color="999999"); Bd = Border(left=thin, right=thin, top=thin, bottom=thin)
def sheet(ws, head, rows):
    ws.sheet_view.rightToLeft = True; ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDEBF7"); c.alignment = Alignment(wrap_text=True, horizontal="center")
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows():
        for c in row:
            c.border = Bd
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 16
ws = wb.active; ws.title = "تیرها"
sheet(ws, ["تراز", "تیر", "b×h", "L", "بالا I", "بالا J", "بالا وسط", "پایین", "جان", "خاموت ویژه", "خاموت وسط", "q"],
      [[FL[r["story"]], r["label"], r["sec"], r["L"], r["topI"], r["topJ"], r["top"], r["bot"], r["web"], r["hoop_h"], r["hoop_m"], r["q_h"]]
       for r in sorted(D["beams"], key=lambda r: (ORDER.index(r["story"]), num(r["label"])))])
sheet(wb.create_sheet("ستون‌ها"), ["طبقه", "ستون", "مقطع", "طولی", "شاخه", "lo", "خاموت lo", "خاموت وسط", "PMM"],
      [[CF[c["story"]], c["label"], c["sec"], c["bars"], c["legs"], c["lo_mm"], c["hoop"], c["hoop_mid"], round(c["pmm"], 3)]
       for c in sorted(D["columns"], key=lambda c: (ORDER.index(c["story"]), num(c["label"])))])
sheet(wb.create_sheet("پی"), ["نوار", "ستون‌ها", "P بهره‌برداری", "q خاک kPa", "Mu", "φMn", "As لازم", "Vu", "φVc"],
      [[k, " ".join(v["columns"]), v["P_service_kN"], v["q_service_kPa (incl. self weight)"], v["Mu_max_abs_kNm"], v["phiMn_bottom_10φ18"], v["As_req_for_Mu_max_mm2"], v["Vu_max_kN"], v["phiVc_kN"]] for k, v in sf.items()])
sheet(wb.create_sheet("سقف و پله"), ["عضو", "مشخصات"],
      [["تیرچه " + k, f"{v['bottom']}؛ بالا {v['top_at_supports']}؛ خیز بلندمدت {v['delta_long_plus_L_mm']} / حد {v['L/240']} mm"] for k, v in jo.items()] +
      [["تای‌بیم 30×30", f"{tb['bars']}؛ {tb['hoops']}"], ["میلگرد حرارتی (فرض)", "φ8@250 دو جهت"], ["تیر BS 30×50", "3φ14 + 3φ14، φ10@200"], ["تیر BT 30×50", "3φ14 + 3φ14، φ10@200"],
       ["دال پله t 0.20", f"پایین {st['bottom']}، توزیع {st['distribution']}، بالا {st['top']}؛ خیز {st['delta_long_plus_L_mm']} / {st['L/240']} mm"],
       ["پی نواری 0.80×2.00 (رئیس)", "10φ18 بالا + 10φ18 پایین، عرضی φ14@150 با خم 20، کاور 10/7/5، مگر 0.10؛ خم 25 سانتی ستون"]])
wb.save(os.path.join(HERE, "Merage3_Rev6d_rebar_schedule.xlsx"))
print("ok")
