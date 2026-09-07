// דוגמה: אותו תוכן, ברמת עיצוב אחרת.
const pptxgen = require('pptxgenjs');
const path = require('path');

const A = path.join(__dirname, 'assets');
const OUT = path.join(__dirname, '..', 'out', 'דוגמת עיצוב - שקף אחד.pptx');
const F = 'Arial', W = 13.33;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.rtl = true;
const rtl = { fontFace: F, rtlMode: true, align: 'right', isTextBox: true };
const ctr = { fontFace: F, rtlMode: true, align: 'center', isTextBox: true, margin: 0 };

const s = pres.addSlide();
s.addImage({ path: path.join(A, 'bg_dark.png'), x: 0, y: 0, w: 13.33, h: 7.5 });

// ---- the head
s.addText('מ ס ל ו ל   ה ה ט ב ה', {
  ...rtl, x: 0.8, y: 0.62, w: W - 1.6, h: 0.32, fontSize: 12, color: '6E93BC',
  bold: true, charSpacing: 2,
});
s.addText('חמישה סטטוסים, מסלול אחד', {
  ...rtl, x: 0.8, y: 0.95, w: W - 1.6, h: 0.78, fontSize: 40, bold: true, color: 'FFFFFF',
});
s.addText('הסטטוס יושב בשורת ההטבה, והוא מתעדכן לבד. זה כל מה שצריך לדעת כדי לקרוא אותו.', {
  ...rtl, x: 0.8, y: 1.78, w: 8.6, h: 0.4, fontSize: 15, color: 'A9C3DD',
});

// ---- the spine
const NODES = [
  { key: 'פוטנציאלי', c: 'B58CE8', tint: '2A2247', line: 'עוד לא ביקשת. ייתכן שאתה זכאי — ואפשר להגיש בקשה.' },
  { key: 'בטיפול', c: 'E8B45C', tint: '3A2E17', line: 'הבקשה הוגשה ועדיין אין החלטה. אין צורך להגיש שוב.' },
  { key: 'פעילה', c: '68D69B', tint: '10321F', line: 'אושרה, התקופה בתוקף ויש יתרה. כאן מגישים קבלות.' },
  { key: 'הסתיימה', c: '9FB6CC', tint: '1B2C3E', line: 'נוצלה במלואה, או שתקופת הזכאות חלפה.' },
];
const NW = 2.55, GAP = 0.55, SPINE = 3.34;
const xOf = i => 12.71 - NW - i * (NW + GAP);

s.addShape(pres.ShapeType.rect, {          // the track the states sit on
  x: xOf(3) + NW / 2, y: SPINE + 0.30, w: xOf(0) + NW / 2 - (xOf(3) + NW / 2), h: 0.02,
  fill: { color: '2C4C70' },
});

NODES.forEach((n, i) => {
  const x = xOf(i);
  s.addShape(pres.ShapeType.roundRect, {
    x, y: SPINE, w: NW, h: 0.62, rectRadius: 0.31,
    fill: { color: n.tint }, line: { color: n.c, width: 1.5 },
  });
  s.addShape(pres.ShapeType.ellipse, { x: x + NW - 0.52, y: SPINE + 0.21, w: 0.2, h: 0.2, fill: { color: n.c } });
  s.addText(n.key, { ...ctr, x: x + 0.2, y: SPINE, w: NW - 0.75, h: 0.62, fontSize: 19, bold: true, color: n.c, valign: 'middle' });
  s.addText(n.line, { ...rtl, x, y: SPINE + 0.85, w: NW, h: 1.1, fontSize: 13.5, color: 'B7CCE1', valign: 'top' });
  if (i < 3) {
    s.addShape(pres.ShapeType.leftArrow, {
      x: x - GAP + 0.10, y: SPINE + 0.20, w: 0.34, h: 0.22, fill: { color: '3E6A96' },
    });
  }
});

// ---- the branch that leaves the track
const bx = xOf(1);
s.addShape(pres.ShapeType.rect, { x: bx + NW / 2 - 0.015, y: SPINE + 2.02, w: 0.03, h: 0.65, fill: { color: '7E3B36' } });
s.addShape(pres.ShapeType.roundRect, {
  x: bx, y: SPINE + 2.67, w: NW, h: 0.62, rectRadius: 0.31,
  fill: { color: '3B1A18' }, line: { color: 'F08A80', width: 1.5 },
});
s.addShape(pres.ShapeType.ellipse, { x: bx + NW - 0.52, y: SPINE + 2.88, w: 0.2, h: 0.2, fill: { color: 'F08A80' } });
s.addText('נדחתה', { ...ctr, x: bx + 0.2, y: SPINE + 2.67, w: NW - 0.75, h: 0.62, fontSize: 19, bold: true, color: 'F08A80', valign: 'middle' });
s.addText('סיבת הדחייה מופיעה על כרטיס ההטבה עצמו.', {
  ...rtl, x: bx - 3.3, y: SPINE + 2.78, w: 3.1, h: 0.5, fontSize: 13.5, color: 'B7CCE1',
});

// ---- the one line worth remembering
s.addShape(pres.ShapeType.roundRect, {
  x: 10.16, y: SPINE + 2.45, w: 2.55, h: 1.05, rectRadius: 0.12,
  fill: { color: '11395F' }, line: { color: '1E5385', width: 1 },
});
s.addText([
  { text: 'רק ב"פעילה" ', options: { bold: true, color: '68D69B' } },
  { text: 'אפשר להגיש חשבוניות וקבלות.', options: { color: 'DCE9F6' } },
], { ...rtl, x: 10.38, y: SPINE + 2.58, w: 2.11, h: 0.8, fontSize: 15, valign: 'middle' });

s.addText('מצפן זכויות איבה · הביטוח הלאומי, אגף שיקום', {
  ...rtl, x: 0.8, y: 6.92, w: W - 1.6, h: 0.3, fontSize: 10, color: '577A9E',
});
s.addNotes('דוגמת עיצוב: אותו תוכן של שקף הסטטוסים, מוצג כמסלול ולא כרשימה.');

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));
