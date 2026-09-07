// אותו שקף, חמישה רקעים. כל וריאציה היא קובץ נפרד.
const pptxgen = require('pptxgenjs');
const path = require('path');

const A = path.join(__dirname, 'assets');
const OUTDIR = path.join(__dirname, '..', 'out', 'variants');
const F = 'Arial', W = 13.33;

// each theme says how the words and the pills sit on its ground
const THEMES = {
  dawn: {
    label: 'שחר', bg: 'bg_dawn.png', dark: false,
    ink: '1B2C3E', head: '17395F', muted: '6B7C8C', track: 'D8CFC4', eyebrow: 'A08A72',
    note: { fill: 'FFFFFF', line: 'E4D8C9' },
  },
  sky: {
    label: 'שמיים', bg: 'bg_sky.png', dark: false,
    ink: '16283C', head: '14477E', muted: '5D7A96', track: 'CBDCEC', eyebrow: '86A6C4',
    note: { fill: 'FFFFFF', line: 'D3E2F0' },
  },
  sand: {
    label: 'חול', bg: 'bg_sand.png', dark: false,
    ink: '2A2721', head: '3E5A72', muted: '7A7266', track: 'DED3C2', eyebrow: 'A2937E',
    note: { fill: 'FFFFFF', line: 'E6DCCB' },
  },
  sage: {
    label: 'מרווה', bg: 'bg_sage.png', dark: false,
    ink: '1E2C24', head: '2C5A44', muted: '64796C', track: 'CBDCD0', eyebrow: '8AA394',
    note: { fill: 'FFFFFF', line: 'D6E4DA' },
  },
  dusk: {
    label: 'דמדומים', bg: 'bg_dusk.png', dark: true,
    ink: 'FFFFFF', head: 'FFFFFF', muted: 'A9BFD8', track: '32506F', eyebrow: '7D9AB9',
    note: { fill: '1A3550', line: '2A5077' },
  },
};

// the product's own status colours, once for paper and once for night
const LIGHT = {
  'פוטנציאלי': ['5E3A94', 'EFE8F8'], 'בטיפול': ['8A5B00', 'FFF1CF'],
  'פעילה': ['1F6E43', 'E3F3E9'], 'הסתיימה': ['4E5F72', 'E8EEF4'], 'נדחתה': ['A8281F', 'FBE8E6'],
};
const NIGHT = {
  'פוטנציאלי': ['B58CE8', '2A2247'], 'בטיפול': ['E8B45C', '3A2E17'],
  'פעילה': ['68D69B', '10321F'], 'הסתיימה': ['9FB6CC', '1B2C3E'], 'נדחתה': ['F08A80', '3B1A18'],
};

const LINES = {
  'פוטנציאלי': 'עוד לא ביקשת. ייתכן שאתה זכאי — ואפשר להגיש בקשה.',
  'בטיפול': 'הבקשה הוגשה ועדיין אין החלטה. אין צורך להגיש שוב.',
  'פעילה': 'אושרה, התקופה בתוקף ויש יתרה. כאן מגישים קבלות.',
  'הסתיימה': 'נוצלה במלואה, או שתקופת הזכאות חלפה.',
};
const ORDER = ['פוטנציאלי', 'בטיפול', 'פעילה', 'הסתיימה'];

function build(key, t) {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.rtl = true;
  const rtl = { fontFace: F, rtlMode: true, align: 'right', isTextBox: true };
  const ctr = { fontFace: F, rtlMode: true, align: 'center', isTextBox: true, margin: 0 };
  const P = t.dark ? NIGHT : LIGHT;

  const s = pres.addSlide();
  s.addImage({ path: path.join(A, t.bg), x: 0, y: 0, w: 13.33, h: 7.5 });

  s.addText('מ ס ל ו ל   ה ה ט ב ה', {
    ...rtl, x: 0.8, y: 0.62, w: W - 1.6, h: 0.32, fontSize: 12, color: t.eyebrow, bold: true, charSpacing: 2,
  });
  s.addText('חמישה סטטוסים, מסלול אחד', {
    ...rtl, x: 0.8, y: 0.95, w: W - 1.6, h: 0.78, fontSize: 40, bold: true, color: t.head,
  });
  s.addText('הסטטוס יושב בשורת ההטבה, והוא מתעדכן לבד. זה כל מה שצריך לדעת כדי לקרוא אותו.', {
    ...rtl, x: 0.8, y: 1.78, w: 8.6, h: 0.4, fontSize: 15, color: t.muted,
  });

  const NW = 2.55, GAP = 0.55, SPINE = 3.34;
  const xOf = i => 12.71 - NW - i * (NW + GAP);

  s.addShape(pres.ShapeType.rect, {
    x: xOf(3) + NW / 2, y: SPINE + 0.30, w: xOf(0) - xOf(3), h: 0.02, fill: { color: t.track },
  });

  ORDER.forEach((key2, i) => {
    const [c, tint] = P[key2];
    const x = xOf(i);
    s.addShape(pres.ShapeType.roundRect, {
      x, y: SPINE, w: NW, h: 0.62, rectRadius: 0.31,
      fill: { color: tint }, line: { color: c, width: 1.5 },
    });
    s.addShape(pres.ShapeType.ellipse, { x: x + NW - 0.52, y: SPINE + 0.21, w: 0.2, h: 0.2, fill: { color: c } });
    s.addText(key2, { ...ctr, x: x + 0.2, y: SPINE, w: NW - 0.75, h: 0.62, fontSize: 19, bold: true, color: c, valign: 'middle' });
    s.addText(LINES[key2], { ...rtl, x, y: SPINE + 0.85, w: NW, h: 1.1, fontSize: 13.5, color: t.muted, valign: 'top' });
    if (i < 3) {
      s.addShape(pres.ShapeType.leftArrow, {
        x: x - GAP + 0.10, y: SPINE + 0.20, w: 0.34, h: 0.22, fill: { color: t.track },
      });
    }
  });

  const [rc, rtint] = P['נדחתה'];
  const bx = xOf(1);
  s.addShape(pres.ShapeType.rect, { x: bx + NW / 2 - 0.015, y: SPINE + 2.02, w: 0.03, h: 0.65, fill: { color: t.track } });
  s.addShape(pres.ShapeType.roundRect, {
    x: bx, y: SPINE + 2.67, w: NW, h: 0.62, rectRadius: 0.31,
    fill: { color: rtint }, line: { color: rc, width: 1.5 },
  });
  s.addShape(pres.ShapeType.ellipse, { x: bx + NW - 0.52, y: SPINE + 2.88, w: 0.2, h: 0.2, fill: { color: rc } });
  s.addText('נדחתה', { ...ctr, x: bx + 0.2, y: SPINE + 2.67, w: NW - 0.75, h: 0.62, fontSize: 19, bold: true, color: rc, valign: 'middle' });
  s.addText('סיבת הדחייה מופיעה על כרטיס ההטבה עצמו.', {
    ...rtl, x: bx - 3.3, y: SPINE + 2.78, w: 3.1, h: 0.5, fontSize: 13.5, color: t.muted,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 10.16, y: SPINE + 2.45, w: 2.55, h: 1.05, rectRadius: 0.12,
    fill: { color: t.note.fill }, line: { color: t.note.line, width: 1 },
  });
  s.addText([
    { text: 'רק ב"פעילה" ', options: { bold: true, color: P['פעילה'][0] } },
    { text: 'אפשר להגיש חשבוניות וקבלות.', options: { color: t.ink } },
  ], { ...rtl, x: 10.38, y: SPINE + 2.58, w: 2.11, h: 0.8, fontSize: 15, valign: 'middle' });

  s.addText('מצפן זכויות איבה · הביטוח הלאומי, אגף שיקום', {
    ...rtl, x: 0.8, y: 6.92, w: W - 1.6, h: 0.3, fontSize: 10, color: t.muted,
  });
  return pres.writeFile({ fileName: path.join(OUTDIR, `רקע ${t.label}.pptx`) });
}

require('fs').mkdirSync(OUTDIR, { recursive: true });
(async () => {
  for (const [k, t] of Object.entries(THEMES)) {
    await build(k, t);
    console.log('wrote', t.label);
  }
})();
