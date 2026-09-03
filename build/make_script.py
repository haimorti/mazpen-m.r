#!/usr/bin/env python3
"""Regenerate video/script.md (storyboard + running narration) from build/scenes.json,
so the script and the rendered slides can never drift apart."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = json.load(open(os.path.join(ROOT, 'build', 'scenes.json'), encoding='utf-8'))

def visual(s):
    t = s['type']
    if t == 'title':   return 'לוגו הביטוח הלאומי, אגף שיקום'
    if t == 'points':  return 'מסך טקסט, רשימה ממוספרת'
    if t == 'chips':   return 'מסך טקסט, רשימת שמות הטבות'
    if t == 'cards':   return 'מסך טקסט, שני כרטיסים זה לצד זה'
    if t == 'flow':    return 'מסך טקסט, שלושה שלבים בשורה'
    if t == 'fields':  return 'מסך טקסט, שדות הטופס'
    v = s['img']
    if s.get('zoom'):  return f"{v} (זום על אזור)"
    if s.get('crop'):  return f"{v} (חלק {'עליון' if s['crop']=='top' else 'תחתון'})"
    return v

def mark(s):
    if s.get('highlight'): return 'מסגרת אדומה על האזור הרלוונטי'
    if s.get('zoom'):      return 'הגדלה של האזור הנדון'
    if s.get('cap_title'): return 'ללא סימון'
    return '—'

rows = []
for i, s in enumerate(sc, 1):
    title = s.get('title', '')
    cap = s.get('cap') or s.get('lead') or s.get('sub', '')
    rows.append(f"| {i} | {title} | {visual(s)} | {mark(s)} | \"{s['vo']}\" | {s['dur']} ש' |")

total = sum(s['dur'] for s in sc)
out = f"""<div dir="rtl">

# מצפן הזכויות שלי – תסריט וסטוריבורד לסרטון הדרכה

> **הקובץ הזה נוצר אוטומטית מ-`build/scenes.json`.** אין לערוך אותו ידנית:
> עורכים את `scenes.json` ומריצים `./build/build-video.sh`, שמרענן גם אותו.

**אורך:** {len(sc)} סצנות, {total // 60} דקות ו-{total % 60} שניות.
**פורמט:** 16:9, שקופיות ב-3840×2160, סרטון ב-1920×1080. **שפה:** עברית, קריינות + כתוביות.
**קהל:** נפגעי פעולות איבה ומשפחות שכולות. הטון: שקט, מכבד, מעשי.

## סטוריבורד

| # | סצנה | מה על המסך | סימון | קריינות | משך |
|---|---|---|---|---|---|
{chr(10).join(rows)}

## קריינות רציפה (להקלטה)

קצב מומלץ: איטי ורגוע, כ-110 מילים לדקה.

{chr(10).join(chr(10).join(['', s['vo']]) for s in sc).strip()}

## הערות הפקה

- **כתוביות** הן חובה. הקובץ `build/out/subtitles.srt` נוצר מהתסריט הזה.
- **סימונים והגדלות** מוגדרים ב-`scenes.json` בשדות `highlight` ו-`zoom`, במיקום
  באחוזים ביחס לצילום המסך, ולכן אפשר לכוונן אותם בלי לערוך תמונות.
- **רזולוציה:** השקופיות מרונדרות ב-2x ולכן הטקסט חד גם במסך מלא. צילומי המסך
  עצמם מוגבלים לאיכות המקור, ולכן כדאי לצלם אותם מחדש ברזולוציה מלאה.
- **קצב:** 3 שניות לפחות על כל מסך לפני שמתחילים לדבר עליו.

</div>
"""
open(os.path.join(ROOT, 'video', 'script.md'), 'w', encoding='utf-8').write(out)
print(f'wrote video/script.md — {len(sc)} scenes, {total}s')
