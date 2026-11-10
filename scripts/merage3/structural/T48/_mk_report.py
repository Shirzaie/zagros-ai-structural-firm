# -*- coding: utf-8 -*-
"""one-off: derive t48_report.py from T46/t46_report.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, "..", "T46", "t46_report.py"), encoding="utf-8").read()
def rep(a, b):
    global s
    assert a in s, a[:40]
    s = s.replace(a, b)
rep('"t46_design.json"', '"t48_design.json"'); rep('"t46_hand_checks.json"', '"t48_hand_checks.json"')
rep('"Merage3_Rev6b_summary.json"', '"Merage3_Rev6c_summary.json"'); rep('A = S["Rev6a"]', 'A = S["Rev6b"]')
rep('گزارش میلگردگذاری و خاموت همه‌ی طبقات — Merage3 (مدل ETABS Rev6b)', 'گزارش میلگردگذاری و خاموت همه‌ی طبقات — Merage3 (مدل ETABS Rev6c)')
rep('# کار ۴۶', '# کار ۴۸')
rep('`ETABS/Merage3_Rev6b.EDB` (کپی Rev6a؛ Rev6a دست نخورد؛ پشتیبان `ETABS/_backup/Merage3_Rev6a_before_T46.EDB`)',
    '`ETABS/Merage3_Rev6c.EDB` (کپی Rev6b؛ Rev6b دست نخورد؛ پشتیبان `ETABS/_backup/Merage3_Rev6b_before_T48.EDB`)')
rep('`work/structural/T46/Merage3_Rev6b_rebar_schedule.xlsx`. نقشه‌ها (برای تأیید): `struct/Merage3_struct_Rev1.dwg` و `.pdf` (۷ شیت).',
    '`work/structural/T48/Merage3_Rev6c_rebar_schedule.xlsx`. نقشه‌ها (برای تأیید، 1:50): `struct/Merage3_struct_Rev2.dwg` و `.pdf`. گزارش کار: `work/structural/2026-10-31_T48.md`.')
a = s.index('w("## ۱.'); b = s.index('w("")\nw("| مورد | Rev6a |')
s = s[:a] + '''w("## ۱. تغییرهای Rev6c (دستورهای رئیس 2026-10-31) و نتایج\n")
w("| # | دستور | اعمال در Rev6c |")
w("|---|---|---|")
for a_, b_ in [("1", "تیرچه‌های دهانه‌ی 7.5 (آکس 1 تا 2، پانل‌های F1 و F4، همه‌ی طبقات) در جهت Y: در Rev6b از قبل همین بود (زاویه‌ی محلی 90°؛ آزمون بار Lr: B10 تا B13 بار می‌گیرند و B1/B4/B7 تقریباً صفر). مدل تغییر نکرد؛ نقشه‌ها اصلاح شد. طول تیرچه 8 m و ۳ تای‌بیم در L/4 (عضو فرعی دال؛ در ETABS مدل نمی‌شود)"),
               ("1b", "تیرچه‌های سقف خرپشته در جهت X (دهانه‌ی 2.3): زاویه‌ی F17 از 90° به 0°؛ بار به B30/B32 رفت (q آن‌ها 0.48 → 0.62)"),
               ("2", "دال پله t = 0.20: بار پله از نو (D تیر پاگرد هر تراز 73.2 → 64.2 kN، B36 هر تراز 66.5 → 57.5 kN)؛ لنگر کنسولک 10.8 تا 12.0 kN·m؛ جرم −66.6 kN"),
               ("3", "چاهک آسانسور 2.00 m و قلاب 25 kN (تأیید): در مدل سازه‌ی بالای پی اثری ندارد (چاهک جزء پی است؛ قلاب از Rev6b روی BH است)"),
               ("4", "دهانه‌های 6.0 و 5.31 و کنسول‌ها: بدون تغییر (X)؛ سؤال از رئیس")]:
    w(f"| {a_} | {b_} | ✓ |")
''' + s[b:]
rep('w("| مورد | Rev6a | **Rev6b** | حد / توضیح |")', 'w("| مورد | Rev6b | **Rev6c** | حد / توضیح |")')
i = s.index('خیز دال پله.**'); a = s.rfind("\nw(", 0, i) + 1; b = s.index('w("## ۲.')
s = s[:a] + '''st0 = H["stair_waist_t200"]; jt = H["joist_7.5m"]
w("\n**هشدار ۱: خیز دال پله با t = 0.20 (دستور رئیس).**")
w("")
w(f"- مقاومت با φ16@125 کافی است (φMn {st0['phiMn_kNm_m']} ≥ Mu {st0['Mu_kNm_m']} kN·m/m؛ εt = {st0['eps_t']}). در t = 0.25 φ16@150 بود.")
w(f"- خیز زنده {st0['delta_L_mm']} mm ≤ L/360 = {st0['L/360_mm']} ✓؛ **خیز بلندمدت + زنده {st0['delta_long_term_plus_L_mm']} mm > L/240 = {st0['L/240_mm']} mm** (ACI 24.2؛ t = 0.20 < l/20 = 0.30). فقط گزارش؛ تغییری داده نشد.")
w("\n**هشدار ۲: عمق تیرچه‌ی دهانه‌ی 7.5.** دال تیرچه‌بلوک 0.31 (بلوک 0.25 + رویه 0.06، فرض مدل) از حداقل جدول ACI 9.3.1.1 کمتر است: ساده l/16 = 0.47، یک سر پیوسته l/18.5 = 0.41، دو سر پیوسته l/21 = 0.36. خیز باید محاسبه شود یا ارتفاع بیشتر شود (سؤال از رئیس). As لازم هر تیرچه " + str(jt["As_req_mm2 (d 270)"]) + " mm² (2φ16، طبق جدول سازنده برای L = 8.0).\n")
''' + s[b:]
rep('st = H["stair_waist_t250"]', 'st = H["stair_waist_t200"]')
rep('w(f"**دال شیبدار و پاگرد t = 0.25:**")', 'w(f"**دال شیبدار و پاگرد t = 0.20 (دستور رئیس):**")')
rep('w("- بالا φ12@200 به طول L/4 در دو سر.")', 'w("- بالا φ10@200 به طول L/4 در دو سر.")')
a = s.index('w("## ۷.')
s = s[:a] + '''tb = H["tie_beams"]
w("## ۶-۱. تیرچه‌ها، تای‌بیم‌ها و چاهک\n")
w("- **تیرچه‌های دهانه‌ی 7.5** (آکس 1 تا 2، A–B و B–C، طبقات ۱ تا ۳ و بام): جهت Y، پشت‌درپشت تیرهای آکس 1 (B10/B11) و آکس 2 (B12/B13)، طول 8.00 m، فاصله 0.50 (فرض)؛ میلگرد پایین هر تیرچه 2φ16 (As لازم " + str(jt["As_req_mm2 (d 270)"]) + ")، طبق جدول سازنده.")
w(f"- **تای‌بیم TB:** ۳ عدد در هر دهانه‌ی 7.5 در Y = 1.875، 3.75 و 5.625، عمود بر تیرچه‌ها؛ {tb['section']}؛ {tb['bars']}؛ {tb['anchorage']}.")
w("- **سقف خرپشته:** همه‌ی تیرچه‌ها در جهت X (دهانه‌ی 2.3)؛ تای‌بیم دستور داده نشده است.")
w("- **دهانه‌های 6.0 و 5.31 و کنسول‌ها:** بدون تغییر (X)؛ سؤال از رئیس (گزارش T48).")
w("- **چاهک آسانسور:** عمق 2.00 m زیر FFL پارکینگ (+0.08) ⇒ کف چاهک حدود −1.92 (فرض)؛ جزء پی (SAFE).\n")
''' + s[a:]
a = s.index('for f_ in ["`ETABS/Merage3_Rev6b.EDB`'); b = s.index("]:", a) + 2
s = s[:a] + '''for f_ in ["`ETABS/Merage3_Rev6c.EDB`؛ `ETABS/Merage3_Rev6c_summary.json`، `_analysis.xlsx`، `_results.xlsx`، `_joint_reactions_SAFE*.csv`",
           "`ETABS/r6c_build.py`، `r6c_run.py`، `r6c_deck_test.py`، `r6c_build_summary.json`، `stair_loads_Rev6c.csv`، `geom_Rev6c.json`",
           "`work/structural/T48/t48_design.py`، `t48_beam_schedule.csv`، `t48_column_schedule.csv`، `t48_design.json`",
           "`work/structural/T48/t48_hand_checks.py` / `.json`، `t48_excel.py`، `t48_report.py`، `Merage3_Rev6c_rebar_schedule.xlsx`",
           "`work/structural/T48/make_struct_Rev2.py`، `plot_Rev2.py`؛ `struct/Merage3_struct_Rev2.dwg`، `struct/Merage3_struct_Rev2.pdf`، `struct/pdf_Rev2/`"]:''' + s[b:]
rep('"2026-10-31_T46_rebar_report.md"', '"2026-10-31_T48_rebar_report_Rev6c.md"')
rep('همه‌ی نقشه‌ها و این جدول', 'همه‌ی نقشه‌ها (1:50) و این جدول')
rep('Task 46: writes the Persian rebar report work/structural/2026-10-31_T46_rebar_report.md', 'Task 48: writes the Persian rebar report work/structural/2026-10-31_T48_rebar_report_Rev6c.md')
open(os.path.join(HERE, "t48_report.py"), "w", encoding="utf-8").write(s)
print("ok")
