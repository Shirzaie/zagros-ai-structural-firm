# قرارداد اسکریپت یکپارچه‌ی شرکت — `zagros_pipeline.py`

هدف این است که یک فایل پایتون از مدل ETABS (و در صورت وجود، نقشه‌ی معماری) شروع کند و بدون دخالت دستی، سه خروجی بسازد:
1. **AutoCAD**: نقشه‌های سازه‌ای DWG و PDF، شامل:
   - پلان آکس‌بندی و ستون‌گذاری
   - قالب‌بندی تیرها
   - جدول ستون‌ها و جزئیات آرماتور تیر و ستون
2. **SAFE**: مدل پی، تحلیل و طراحی دال پی، و جدول‌های نتیجه.
3. **Tekla Structures**: مدل سه‌بعدی سازه. اگر Tekla نصب یا باز نبود، خروجی IFC4 ساخته می‌شود که Tekla آن را می‌خواند.

## اجرا
```
python zagros_pipeline.py --config Merage3/pipeline_config.json              # همه‌ی مرحله‌ها
python zagros_pipeline.py --config ... --stages etabs,autocad                # فقط چند مرحله
python zagros_pipeline.py --config ... --set safe.ks=24000 --set safe.qa=150 # تغییر پارامتر و اجرای دوباره
```

## مرحله‌ها و امضای تابع‌ها
همه‌ی مرحله‌ها یک امضا دارند: `def stage_<name>(model: dict, cfg: dict, out: Path, log) -> dict`
- `model`: مدل داده‌ی مشترک (پایین). هر مرحله فقط کلیدهای خودش را **اضافه** می‌کند و چیزی را پاک نمی‌کند.
- `cfg`: کل پیکربندی. هر مرحله بخش خودش را می‌خواند (`cfg["autocad"]`، `cfg["safe"]` و...).
- `out`: پوشه‌ی خروجی این اجرا (`<project>/work/pipeline/<run_id>/`). هر مرحله زیرپوشه‌ی خودش را دارد: `out/"autocad"` و...
- `log(msg)`: ثبت در `out/pipeline.log` و چاپ روی صفحه.
- مقدار برگشتی: `{"ok": bool, "files": [مسیرها], "summary": {...}, "warnings": [...]}`
- اگر نرم‌افزار در دسترس نبود، مرحله نباید کل اجرا را متوقف کند. `ok=False` برمی‌گرداند و دلیل را در warnings می‌نویسد. فقط وقتی `cfg["strict"]` روشن است، خطا بالا می‌رود.

ترتیب اجرا: `etabs` ← `autocad` ← `safe` ← `tekla` ← گزارش نهایی (`out/pipeline_report.md`).

## مدل داده‌ی مشترک (`model.json` در پوشه‌ی خروجی)
واحدها: N و mm. فرمت ادامه‌ی همان `Merage3_geometry.json` (خروجی `etabs_export_geometry.py`) است:
```
project      str
source       مسیر EDB
units        "N, mm"
stories      [[name, elev], ...]   پایین به بالا، شامل Base
grids        [{label, dir:"X"|"Y", coord}]
frames       [{name, label, story, kind:"Column"|"Beam"|"Brace", section, i:[x,y,z], j:[x,y,z], angle, cardinal}]
areas        [{name, label, story, prop, pts:[[x,y,z],...], angle}]
sections     {name: {material, depth, width, ...}}
materials    {name: {type, fc, fy, E, U, W}}
--- اضافه‌شده توسط مرحله‌ی etabs (اگر ETABS نتایج داشت) ---
reactions    [{point, x, y, case, Fx, Fy, Fz, Mx, My, Mz}]      حالت‌های بار تکی (و ترکیب‌های سرویس اگر خواسته شد)
design       {"beams": {frame_name: {top_mm2:[i,mid,j], bot_mm2:[i,mid,j], av_s:[...], at_s:[...], combo}},
              "columns": {frame_name: {as_mm2, pmm, combo}}, "combos": [...], "code": "ACI 318-19"}
--- اضافه‌شده توسط مرحله‌های بعدی ---
foundation   {type, thickness, regions:[...], soil:{qa, ks}, results:{max_pressure, settlement, punching:[...], rebar:{...}}}   (safe)
drawings     [مسیر فایل‌ها]                                                                                          (autocad)
bim          {mode:"tekla"|"ifc", file, counts}                                                                       (tekla)
```

## پیکربندی (`pipeline_config.json`)
بخش‌ها: `project`، `etabs`، `autocad`، `safe`، `tekla` و `rebar`. نمونه‌ی کامل در `pipeline_config.example.json` است.

## قواعد شرکت که در کد رعایت می‌شود
- **مدل اصلی هرگز تغییر نمی‌کند و ذخیره نمی‌شود.** مرحله‌ی etabs اگر لازم باشد Run بزند، اول یک کپی در `out/etabs/` می‌سازد و روی آن کار می‌کند. نتایج قبل از Save خوانده می‌شوند، چون `File.Save` در ETABS 19 نتایج را پاک می‌کند.
- ETABS 19 مسیر فارسی را نمی‌خواند. اگر مسیر غیر ASCII بود، مدل در `C:\ZagrosTemp\` کپی می‌شود.
- هیچ فایلی حذف نمی‌شود. خروجی هر اجرا در پوشه‌ی تازه‌ی `run_id` با تاریخ و ساعت ساخته می‌شود.
- همه‌ی خروجی‌ها برچسب **«پیش‌نویس — منتظر تأیید مهندس محاسب»** دارند.
- متن فارسی AutoCAD طبق نکته‌های `Merage3/CLAUDE.md` نوشته می‌شود: ی و ي، ZWNJ، و بدون reshape.
- در هر لحظه هر نرم‌افزار فقط یک نمونه دارد. اگر نرم‌افزار باز بود، مرحله به همان وصل می‌شود و آن را نمی‌بندد. اگر خود مرحله آن را باز کرده باشد، در پایان می‌بندد.
