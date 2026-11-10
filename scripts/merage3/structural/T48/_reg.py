# -*- coding: utf-8 -*-
"""one-off: board.md task 48 row + coordination.md item 76"""
import os
PRJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
bp = os.path.join(PRJ, "board.md")
b = open(bp, encoding="utf-8").read()
lines = b.split("\n")
row = ("| 48 | دستور رئیس 2026-10-31: تیرچه‌ها در جهت 7.5 (Y)، طول 8 m، ۳ تای‌بیم؛ تیرچه‌های خرپشته در X (2.3)؛ دال پله 0.20؛ چاهک 2.00؛ قلاب 25 kN تأیید؛ نقشه‌ها 1:50 | structural-engineer | "
       "⛔ 2026-10-31: `ETABS/Merage3_Rev6c.EDB` (Rev6b دست نخورد؛ پشتیبان `_backup/Merage3_Rev6b_before_T48.EDB`). تیرچه‌ی دهانه‌ی 7.5 (F1، F4) در مدل از قبل Y بود (آزمون `r6c_deck_test.py`)؛ خرپشته F17 → X؛ دال پله 0.20. "
       "W=10355.1، V=1035.5، T1=1.055، دریفت 0.822، جابه‌جایی 69.9 mm، **PMM 0.976؛ هیچ عضوی رد نیست**. ⚠️ خیز پله 69 > 25 mm (φ16@125)؛ ⚠️ دال 0.31 برای تیرچه‌ی 7.5 کمتر از l/21. "
       "گزارش `work/structural/2026-10-31_T48.md` و `2026-10-31_T48_rebar_report_Rev6c.md` + `T48/Merage3_Rev6c_rebar_schedule.xlsx`؛ نقشه‌ها `struct/Merage3_struct_Rev2.dwg/pdf` (۷ شیت A1، 1:50، برای تأیید). "
       "⛔ سؤال: تیرچه‌ی دهانه‌های 6.0 و 5.31 (اجرا نشد)، خیز پله، عمق تیرچه. coordination ۷۶ |")
assert not any(l.startswith("| 48 |") for l in lines)
i = [k for k, l in enumerate(lines) if l.startswith("| 47 |")][0]
lines.insert(i + 1, row)
open(bp, "w", encoding="utf-8").write("\n".join(lines))
cp = os.path.join(PRJ, "coordination.md")
c = open(cp, encoding="utf-8").read().rstrip("\n")
assert "| 76 |" not in c
c += ("\n| 76 | 2026-10-31 | structural | → architect / safe-operator / رئیس | **کار ۴۸ (Rev6c و نقشه‌های سازه Rev2 1:50؛ پاسخ قلم ۷۵)**: "
      "(۱) تیرچه‌ی دهانه‌ی 7.5 (آکس 1 تا 2) در Y، طول 8.00، ۳ تای‌بیم TB 15×31 در Y 1.875 / 3.75 / 5.625 (2φ12 + 2φ12، φ8@200)؛ در مدل از قبل Y بود. "
      "(۲) خرپشته: همه‌ی تیرچه‌ها X (F17 از 90° به 0°). (۳) **دهانه‌های 6.0 و 5.31 و کنسول‌ها: X ماندند تا پاسخ رئیس**؛ پس دیوارهای W7 تا W20 هم تغییری ندارند (نکته‌ی ۳ قلم ۷۵). "
      "(۴) دال پله 0.20: φ16@125 + φ10@200؛ ⚠️ خیز بلندمدت 69 mm > 25. (۵) چاهک 2.00 (کف −2.00 طبق Rev.12) کنار C16 و C18: پی و دیوار چاهک با SAFE. "
      "(۶) قلاب 25 kN تأیید رئیس، روی BH. (۷) SAFE: `ETABS/Merage3_Rev6c_joint_reactions_SAFE*.csv`. گزارش `work/structural/2026-10-31_T48.md`؛ نقشه‌ها `struct/Merage3_struct_Rev2.pdf` | باز |\n")
open(cp, "w", encoding="utf-8").write(c)
print("ok")
