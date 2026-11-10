# -*- coding: utf-8 -*-
"""one-off: board.md task 50 + coordination.md item 78"""
import os
PRJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
bp = os.path.join(PRJ, "board.md")
lines = open(bp, encoding="utf-8").read().split("\n")
row = ("| 50 | دستور فوری رئیس 2026-10-31: Rev6d (همه‌ی تیرچه‌ها Y، تکیه‌گاه میانی پله، t 0.20، تای‌بیم 30×30) و نقشه‌های DWG کامل 1:20 با آرماتورگذاری و پی نواری مرکب 0.80×2.00 | structural-engineer | "
       "⛔ 2026-10-31: `ETABS/Merage3_Rev6d.EDB` (Rev6c دست نخورد؛ پشتیبان `_backup/Merage3_Rev6c_before_T50.EDB`)؛ F12/F13/F14 → Y؛ BT 30×50 در Y 15.30 (ناگزیر، چاهک)؛ BS 30×50 در Y 11.658 (تکیه‌گاه میانی پله). "
       "W=10429.4، V=1042.9، T1=1.059، دریفت 0.827، جابه‌جایی 70.3 mm، **PMM 0.985؛ سازه‌ی بالای پی رد ندارد**. **❌ پی نواری رئیس: خمش ~3× و برش ~2× ظرفیت** (فقط گزارش، تغییر داده نشد)؛ ⚠️ تداخل نوار A و B (0.40)؛ ⚠️ خیز پله 23 > 17 mm و تیرچه‌ها. "
       "نقشه‌ها `struct/Merage3_struct_Rev3.dwg/pdf` (۱۶ شیت A0، 1:20، برای تأیید: پی، تیرها، ستون‌ها، سقف‌ها، پله)؛ گزارش `work/structural/2026-10-31_T50.md` و `2026-10-31_T50_rebar_report_Rev6d.md` + xlsx؛ coordination ۷۷s، ۷۸ |")
assert not any(l.startswith("| 50 |") for l in lines)
i = max(k for k, l in enumerate(lines) if l.startswith("| 4"))
lines.insert(i + 1, row)
open(bp, "w", encoding="utf-8").write("\n".join(lines))
cp = os.path.join(PRJ, "coordination.md")
c = open(cp, encoding="utf-8").read().rstrip("\n")
assert "| 78 |" not in c
c += ("\n| 78 | 2026-10-31 | structural | → architect / safe-operator / رئیس | **کار ۵۰ (Rev6d و struct Rev3 1:20)**: (۱) تیرچه‌های همه‌ی دهانه‌ها Y، کنسول‌ها X، خرپشته X؛ تای‌بیم 30×30 مخفی یکسره در X (2φ14 + 2φ14، 3 خاموت φ10 20×20 بین هر دو تیرچه)، ۳ عدد در هر دهانه در L/4. "
      "(۲) BS و BT طبق قلم ۷۷s. (۳) **پی:** نوارهای طولی زیر A، B/B' و C از آکس 1 تا 5 کشیده شد (فرض)؛ **نوار A و B 0.40 هم‌پوشانی دارند**؛ Rev.13 معمار نوار عرضی زیر آکس‌های 1 تا 4 دارد؛ ناهماهنگ است تا تصمیم رئیس. "
      "**با ابعاد و میلگرد رئیس، خمش و برش نوار رد است** (گزارش T50). (۴) چاهک −2.00: دیوار 0.25 و دال 0.30 (پیشنهاد) و پله‌ای شدن نوارها دور چاهک. (۵) SAFE: `ETABS/Merage3_Rev6d_joint_reactions_SAFE*.csv`. "
      "نقشه‌ها `struct/Merage3_struct_Rev3.pdf` | باز |\n")
open(cp, "w", encoding="utf-8").write(c)
print("ok")
