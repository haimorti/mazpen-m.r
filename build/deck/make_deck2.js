// המצגת לכנס, מהדורה שנייה.
// כל שקף מקבל את הצורה שמלמדת אותו: מסלול, מפה, צומת, ציר זמן, השוואה —
// ולא רשימה. הרקע אחד לכולם, והצבעים הם אלה שהמבוטח רואה במסך עצמו.
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const A = path.join(__dirname, 'assets');
const OUT = path.join(__dirname, '..', 'out', 'מצפן זכויות איבה - מצגת לכנס.pptx');

const NAVY = '14477E', INK = '1E2C24', MUTED = '64796C', LINE = 'CFE0D5';
const GREEN = '2C7A5B', CLAY = 'B85C22', PAPER = 'FFFFFF';
const F = 'Arial', W = 13.33, H = 7.5, M = 0.75;

// the product's own status colours
const ST = {
  'פוטנציאלי': ['5E3A94', 'EFE8F8'], 'בטיפול': ['8A5B00', 'FFF1CF'],
  'פעילה': ['1F6E43', 'E3F3E9'], 'הסתיימה': ['4E5F72', 'E8EEF4'], 'נדחתה': ['A8281F', 'FBE8E6'],
};

const png = f => {
  const b = fs.readFileSync(path.join(A, f));
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
};

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.rtl = true;
const rtl = { fontFace: F, rtlMode: true, align: 'right', isTextBox: true };
const ctr = { fontFace: F, rtlMode: true, align: 'center', isTextBox: true, margin: 0 };

// ---------------------------------------------------------------- shells
function ground(bg) {
  const s = pres.addSlide();
  s.addImage({ path: path.join(A, bg), x: 0, y: 0, w: W, h: H });
  return s;
}

function page(title, kicker) {
  const s = ground('bg_sage.jpg');
  s.addText(title, { ...rtl, x: M, y: 0.5, w: W - 2 * M, h: 0.7, fontSize: 34, bold: true, color: NAVY });
  if (kicker) s.addText(kicker, { ...rtl, x: M, y: 1.18, w: W - 2 * M, h: 0.4, fontSize: 15.5, color: MUTED });
  s.addText('מצפן זכויות איבה · הביטוח הלאומי, אגף שיקום', {
    ...rtl, x: M, y: H - 0.5, w: W - 2 * M, h: 0.3, fontSize: 10, color: '93A79B',
  });
  return s;
}

function dark(eyebrow, title, note, o = {}) {
  const s = ground('bg_forest.jpg');
  const y = o.y !== undefined ? o.y : 2.8;
  s.addImage({ path: path.join(A, 'logo.png'), x: W - M - 1.7, y: 0.5, w: 1.7, h: 0.62 });
  if (eyebrow) s.addText(eyebrow, { ...rtl, x: M, y: y - 0.42, w: W - 2 * M, h: 0.36, fontSize: 15, color: '8FC7AC', bold: true });
  s.addText(title, { ...rtl, x: M, y, w: W - 2 * M, h: 1.2, fontSize: o.size || 50, bold: true, color: 'FFFFFF' });
  if (note) s.addText(note, { ...rtl, x: M, y: y + 1.15, w: W - 2 * M, h: 0.8, fontSize: 18, color: 'C3DCCF' });
  return s;
}

function shot(s, file, box) {
  const d = png(file), ratio = d.w / d.h;
  let w = box.w, h = w / ratio;
  if (h > box.h) { h = box.h; w = h * ratio; }
  const x = box.x + (box.w - w) / 2, y = box.y + (box.h - h) / 2;
  s.addImage({ path: path.join(A, file), x, y, w, h });
  return { x, y, w, h };
}

function badge(s, x, y, n, color, d = 0.42) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color }, line: { color: PAPER, width: 2 } });
  s.addText(String(n), { ...ctr, x, y, w: d, h: d, fontSize: d > 0.5 ? 18 : 14, bold: true, color: PAPER, valign: 'middle' });
}

function card(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: o.r || 0.12,
    fill: { color: o.fill || PAPER }, line: { color: o.line || LINE, width: o.lw || 1 },
  });
}

function pill(s, o) {
  const [c, tint] = ST[o.key];
  card(s, { x: o.x, y: o.y, w: o.w, h: 0.6, r: 0.3, fill: tint, line: c, lw: 1.5 });
  s.addShape(pres.ShapeType.ellipse, { x: o.x + o.w - 0.5, y: o.y + 0.2, w: 0.2, h: 0.2, fill: { color: c } });
  s.addText(o.key, { ...ctr, x: o.x + 0.18, y: o.y, w: o.w - 0.72, h: 0.6, fontSize: 18, bold: true, color: c, valign: 'middle' });
  return c;
}

function arrow(s, x, y, w = 0.34) {
  s.addShape(pres.ShapeType.leftArrow, { x, y, w, h: 0.22, fill: { color: LINE } });
}

// ================================================================ 1 · cover
{
  const s = ground('bg_forest.jpg');
  s.addImage({ path: path.join(A, 'logo.png'), x: W - M - 2.0, y: 0.55, w: 2.0, h: 0.73 });
  s.addText('הביטוח הלאומי · אגף שיקום', { ...rtl, x: M, y: 2.35, w: W - 2 * M, h: 0.4, fontSize: 18, color: '8FC7AC', bold: true });
  s.addText('מצפן זכויות איבה', { ...rtl, x: M, y: 2.8, w: W - 2 * M, h: 1.35, fontSize: 62, bold: true, color: 'FFFFFF' });
  s.addText('כל הזכויות וההטבות שלך, במקום אחד באזור האישי.', {
    ...rtl, x: M, y: 4.15, w: W - 2 * M, h: 0.55, fontSize: 22, color: 'C3DCCF',
  });
  card(s, { x: W - M - 2.6, y: 5.35, w: 2.6, h: 0.66, r: 0.33, fill: '2C7A5B', line: '2C7A5B' });
  s.addText('למשפחות שכולות', { ...ctr, x: W - M - 2.6, y: 5.35, w: 2.6, h: 0.66, fontSize: 18, bold: true, color: 'FFFFFF', valign: 'middle' });
  s.addNotes('פתיחה. המצפן הוא אזור חדש בתוך האזור האישי, ובשלב זה הוא פתוח למשפחות שכולות בלבד.');
}

// ================================================================ 2 · the talk as a route
{
  const s = page('מה נעבור היום', 'ארבע תחנות, ואז שאלות');
  const stops = [
    ['מה זה', 'ולמי הוא פתוח'],
    ['איפה זה', 'ואיך נכנסים'],
    ['מה רואים בו', 'ההטבות, הסטטוסים, התמונה המלאה'],
    ['מה עושים בו', 'בקשה חדשה, וחשבונית או קבלה'],
  ];
  const NW = 2.72, GAP = 0.5, Y = 2.9;
  const xOf = i => W - M - NW - i * (NW + GAP);
  s.addShape(pres.ShapeType.rect, { x: xOf(3) + NW / 2, y: Y + 0.55, w: xOf(0) - xOf(3), h: 0.02, fill: { color: LINE } });
  stops.forEach((st, i) => {
    const x = xOf(i);
    badge(s, x + NW / 2 - 0.28, Y + 0.28, i + 1, NAVY, 0.56);
    s.addText(st[0], { ...ctr, x, y: Y + 1.0, w: NW, h: 0.45, fontSize: 22, bold: true, color: NAVY });
    s.addText(st[1], { ...ctr, x, y: Y + 1.5, w: NW, h: 0.9, fontSize: 14.5, color: MUTED, valign: 'top' });
  });
  card(s, { x: M, y: 5.35, w: W - 2 * M, h: 0.95, fill: 'FFFFFF' });
  s.addText([
    { text: 'ובסוף — שאלות ותשובות. ', options: { bold: true, color: GREEN } },
    { text: 'הרעיון בשורה אחת: במקום לחפש מה מגיע לך, המצפן מציג את זה מראש.', options: { color: INK } },
  ], { ...rtl, x: M + 0.35, y: 5.35, w: W - 2 * M - 0.7, h: 0.95, fontSize: 17, valign: 'middle' });
  s.addNotes('סדר היום. החלק הגדול הוא היכרות; ההגשה של חשבוניות בסוף וקצרה.');
}

// ================================================================ 3 · before / after
{
  const s = page('מה משתנה', 'אותן זכויות. מה שהשתנה הוא מה שרואים');
  const cw = (W - 2 * M - 0.6) / 2;
  const cols = [
    ['היום, בלי המצפן', MUTED, LINE, [
      'צריך לדעת מה לבקש כדי לבקש.',
      'אחרי שהגשת — לא ברור מה קרה לבקשה.',
      'כל קבלה נשלחת בנפרד, בלי מקום אחד לעקוב.',
    ]],
    ['עם המצפן', GREEN, GREEN, [
      'ההטבות שאתה עשוי להיות זכאי להן מוצגות מראש.',
      'לכל בקשה יש סטטוס, והוא מתעדכן לבד.',
      'חשבונית או קבלה נכנסות ישר להטבה הנכונה.',
    ]],
  ];
  cols.forEach((col, i) => {
    const x = M + (1 - i) * (cw + 0.6);
    card(s, { x, y: 1.95, w: cw, h: 3.55, line: col[2], lw: i ? 1.6 : 1 });
    s.addText(col[0], { ...rtl, x: x + 0.35, y: 2.25, w: cw - 0.7, h: 0.5, fontSize: 22, bold: true, color: col[1] });
    col[3].forEach((t, j) => {
      s.addShape(pres.ShapeType.ellipse, { x: x + cw - 0.62, y: 3.03 + j * 0.85, w: 0.14, h: 0.14, fill: { color: col[1] } });
      s.addText(t, { ...rtl, x: x + 0.35, y: 2.9 + j * 0.85, w: cw - 1.05, h: 0.75, fontSize: 15.5, color: INK, valign: 'top' });
    });
  });
  s.addText('המצפן לא יוצר זכאות ולא מבטל אותה. הוא רק מראה אותה.', {
    ...rtl, x: M, y: 5.75, w: W - 2 * M, h: 0.5, fontSize: 17, bold: true, color: CLAY, align: 'center',
  });
  s.addNotes('זה הטיעון של כל הכנס. שווה לעצור כאן.');
}

// ================================================================ 4 · a stage, not a limit
{
  const s = page('למי המצפן פתוח', 'זה שלב, לא גבול');
  const Y = 2.6;
  s.addShape(pres.ShapeType.rect, { x: 2.2, y: Y + 0.72, w: 9.55, h: 0.03, fill: { color: LINE } });
  const now = { x: 7.35, w: 4.4 };
  card(s, { x: now.x, y: Y, w: now.w, h: 1.5, fill: '2C7A5B', line: '2C7A5B' });
  s.addText('היום', { ...rtl, x: now.x + 0.4, y: Y + 0.18, w: now.w - 0.8, h: 0.35, fontSize: 14, bold: true, color: 'A9E3C6' });
  s.addText('משפחות שכולות', { ...rtl, x: now.x + 0.4, y: Y + 0.55, w: now.w - 0.8, h: 0.7, fontSize: 30, bold: true, color: 'FFFFFF' });
  const later = { x: 2.2, w: 4.4 };
  card(s, { x: later.x, y: Y + 0.2, w: later.w, h: 1.1, fill: 'FFFFFF', line: LINE });
  s.addText('בהמשך', { ...rtl, x: later.x + 0.35, y: Y + 0.34, w: later.w - 0.7, h: 0.3, fontSize: 13, bold: true, color: MUTED });
  s.addText('אוכלוסיות נוספות, ובהן נכי פעולות איבה', {
    ...rtl, x: later.x + 0.35, y: Y + 0.64, w: later.w - 0.7, h: 0.55, fontSize: 17, bold: true, color: NAVY,
  });
  arrow(s, 6.6, Y + 0.65, 0.5);

  const notes = [
    ['ילדים קטינים', 'הורה שמקבל הטבות עבור ילדיו רואה אותן בתוך המצפן שלו, באזור "הצגת הטבות עבור".'],
    ['ומי שלא רואה', 'מי ששייך לקבוצה ועדיין לא רואה את המצפן — מוזמן לפנות אלינו.'],
  ];
  notes.forEach((n, i) => {
    const cw = (W - 2 * M - 0.5) / 2, x = M + (1 - i) * (cw + 0.5);
    card(s, { x, y: 4.85, w: cw, h: 1.35 });
    s.addText(n[0], { ...rtl, x: x + 0.32, y: 5.05, w: cw - 0.64, h: 0.36, fontSize: 17, bold: true, color: CLAY });
    s.addText(n[1], { ...rtl, x: x + 0.32, y: 5.42, w: cw - 0.64, h: 0.7, fontSize: 14.5, color: INK, valign: 'top' });
  });
  s.addNotes('חשוב לומר את זה במפורש ומוקדם, כדי שאיש לא יחפש אצלו משהו שעדיין לא קיים.');
}

// ================================================================ 5 · the way in, as a path
{
  const s = page('איך נכנסים', 'שלוש לחיצות מהאזור האישי');
  const steps = ['האזור האישי', 'מצפן הזכויות שלי', 'כניסה למצפן הזכויות', 'הכפתור הכחול'];
  const CW = 2.72, GAP = 0.42, Y = 2.0;
  const xOf = i => W - M - CW - i * (CW + GAP);
  steps.forEach((t, i) => {
    const x = xOf(i);
    card(s, { x, y: Y, w: CW, h: 0.78, r: 0.14, fill: i === 3 ? '14477E' : PAPER, line: i === 3 ? '14477E' : LINE });
    s.addText(t, { ...ctr, x: x + 0.15, y: Y, w: CW - 0.3, h: 0.78, fontSize: 15.5, bold: true, color: i === 3 ? 'FFFFFF' : NAVY, valign: 'middle' });
    if (i < 3) arrow(s, x - GAP + 0.04, Y + 0.28, 0.34);
  });
  shot(s, 'entry_wide.png', { x: M, y: 3.05, w: 8.6, h: 3.25 });
  s.addText('הכתובת של האזור האישי', { ...rtl, x: 9.7, y: 3.35, w: W - M - 9.7, h: 0.35, fontSize: 14, color: MUTED });
  s.addText('ps.btl.gov.il', { x: 9.7, y: 3.68, w: W - M - 9.7, h: 0.5, fontSize: 26, bold: true, color: NAVY, align: 'right', fontFace: F, isTextBox: true, margin: 0 });
  s.addText('אותו אזור אישי שכבר מוכר לכם. המצפן יושב בתוכו, בתפריט הצד — ומשם נכנסים אליו בכפתור הכחול.', {
    ...rtl, x: 9.7, y: 4.28, w: W - M - 9.7, h: 1.5, fontSize: 15, color: INK, valign: 'top',
  });
  s.addNotes('הכניסה. לא צריך שום דבר חדש — אותו אזור אישי.');
}

// ================================================================ 6 · the main screen, as a map
{
  const s = page('המסך הראשי', 'ארבעה אזורים — וזה המסך שנחזור אליו בכל פעם');
  shot(s, 'zones.png', { x: M, y: 1.7, w: 8.35, h: 4.55 });
  const zones = [
    ['הצגת הטבות עבור', 'בוחרים עבור מי להציג. מופיע רק להורים לילדים קטינים.', 'E8842B'],
    ['חיפוש', 'לפי שם ההטבה או לפי נושא — דיור, רכב, טיפול רפואי.', '2E9E4F'],
    ['ההטבות שלי', 'מה שכבר ביקשת, או שכבר אושר לך.', '8E3BB5'],
    ['ההטבות הפוטנציאליות', 'מה שאתה עשוי להיות זכאי לו ועדיין לא ביקשת.', '2A9BD6'],
  ];
  zones.forEach((z, i) => {
    const y = 1.85 + i * 1.14, x = 9.4, w = W - M - 9.4;
    badge(s, x + w - 0.42, y, i + 1, z[2]);
    s.addText(z[0], { ...rtl, x, y: y - 0.03, w: w - 0.58, h: 0.36, fontSize: 16, bold: true, color: NAVY });
    s.addText(z[1], { ...rtl, x, y: y + 0.33, w: w - 0.58, h: 0.75, fontSize: 13, color: MUTED, valign: 'top' });
  });
  s.addNotes('מפה, לא רשימה: אפשר להצביע על המסך ולעבור אזור אזור.');
}

// ================================================================ 7 · mine vs potential
{
  const s = page('שתי רשימות, והבדל אחד', 'זה ההבדל שהכי מבלבל, ולכן הוא לבד על שקף');
  const cw = (W - 2 * M - 0.55) / 2;
  const cols = [
    ['ההטבות שלי', '8E3BB5', 'band_mine.png', 'מה שכבר ביקשת, או שכבר אושר לך.', 'לחיצה פותחת את דף ההטבה, עם הסטטוס והיתרה.'],
    ['ההטבות הפוטנציאליות', '2A9BD6', 'band_potential.png', 'מה שאתה עשוי להיות זכאי לו — ועדיין לא ביקשת.', 'לחיצה פותחת את ההטבה, ובה כפתור להגשה או לפנייה.'],
  ];
  cols.forEach((c, i) => {
    const x = M + (1 - i) * (cw + 0.55);
    card(s, { x, y: 1.85, w: cw, h: 3.5, line: c[1], lw: 1.6 });
    s.addText(c[0], { ...rtl, x: x + 0.32, y: 2.1, w: cw - 0.64, h: 0.48, fontSize: 23, bold: true, color: c[1] });
    shot(s, c[2], { x: x + 0.32, y: 2.68, w: cw - 0.64, h: 1.15 });
    s.addText(c[3], { ...rtl, x: x + 0.32, y: 3.95, w: cw - 0.64, h: 0.6, fontSize: 16, bold: true, color: INK, valign: 'top' });
    s.addText(c[4], { ...rtl, x: x + 0.32, y: 4.6, w: cw - 0.64, h: 0.9, fontSize: 14.5, color: MUTED, valign: 'top' });
  });
  s.addText('אותה הטבה יכולה להופיע בשתיהן — כשאפשר להרחיב אותה לתקופה נוספת או לבן משפחה נוסף.', {
    ...rtl, x: M, y: 5.65, w: W - 2 * M, h: 0.45, fontSize: 15, color: CLAY, align: 'center',
  });
  s.addNotes('ההבדל בין השתיים חוזר בשאלות יותר מכל דבר אחר.');
}

// ================================================================ 8 · the benefit page, as anatomy
{
  const s = page('דף ההטבה', 'אותו מבנה בכל הטבה, כך שאחרי פעם אחת יודעים איפה להסתכל');
  shot(s, 'benefit.png', { x: M, y: 1.65, w: 8.1, h: 4.6 });
  const parts = [
    ['שם וקטגוריה', 'בראש הדף — איזו הטבה זו, ולאיזה תחום היא שייכת.'],
    ['תיבת ההסבר', 'מה ההטבה נותנת, כמה, ובאיזה תנאי.'],
    ['שורת ההטבה', 'הסטטוס, הסכום ותקופת הזכאות — בשורה אחת.'],
    ['פרטים נוספים', 'פותח את התמונה המלאה של ההטבה.'],
  ];
  parts.forEach((p, i) => {
    const y = 1.85 + i * 1.14, x = 9.15, w = W - M - 9.15;
    badge(s, x + w - 0.42, y, i + 1, NAVY);
    s.addText(p[0], { ...rtl, x, y: y - 0.03, w: w - 0.58, h: 0.36, fontSize: 16, bold: true, color: NAVY });
    s.addText(p[1], { ...rtl, x, y: y + 0.33, w: w - 0.58, h: 0.75, fontSize: 13, color: MUTED, valign: 'top' });
  });
  s.addNotes('אנטומיה של דף אחד. אחרי זה כל הטבה נראית מוכרת.');
}

// ================================================================ 9 · the statuses, as a path
{
  const s = page('חמישה סטטוסים, מסלול אחד', 'הסטטוס יושב בשורת ההטבה, והוא מתעדכן לבד');
  const LINES = {
    'פוטנציאלי': 'עוד לא ביקשת. ייתכן שאתה זכאי — ואפשר להגיש בקשה.',
    'בטיפול': 'הבקשה הוגשה ועדיין אין החלטה. אין צורך להגיש שוב.',
    'פעילה': 'אושרה, התקופה בתוקף ויש יתרה. כאן מגישים קבלות.',
    'הסתיימה': 'נוצלה במלואה, או שתקופת הזכאות חלפה.',
  };
  const ORDER = ['פוטנציאלי', 'בטיפול', 'פעילה', 'הסתיימה'];
  const NW = 2.55, GAP = 0.55, Y = 2.35;
  const xOf = i => W - M - NW - i * (NW + GAP);
  s.addShape(pres.ShapeType.rect, { x: xOf(3) + NW / 2, y: Y + 0.29, w: xOf(0) - xOf(3), h: 0.02, fill: { color: LINE } });
  ORDER.forEach((k, i) => {
    const x = xOf(i);
    pill(s, { key: k, x, y: Y, w: NW });
    s.addText(LINES[k], { ...rtl, x, y: Y + 0.82, w: NW, h: 1.1, fontSize: 13.5, color: MUTED, valign: 'top' });
    if (i < 3) arrow(s, x - GAP + 0.10, Y + 0.19);
  });
  const bx = xOf(1);
  s.addShape(pres.ShapeType.rect, { x: bx + NW / 2 - 0.015, y: Y + 2.0, w: 0.03, h: 0.62, fill: { color: LINE } });
  pill(s, { key: 'נדחתה', x: bx, y: Y + 2.62, w: NW });
  s.addText('סיבת הדחייה מופיעה על כרטיס ההטבה עצמו.', {
    ...rtl, x: bx - 3.25, y: Y + 2.73, w: 3.05, h: 0.5, fontSize: 13.5, color: MUTED,
  });
  card(s, { x: 10.03, y: Y + 2.4, w: 2.55, h: 1.05 });
  s.addText([
    { text: 'רק ב"פעילה" ', options: { bold: true, color: ST['פעילה'][0] } },
    { text: 'אפשר להגיש חשבוניות וקבלות.', options: { color: INK } },
  ], { ...rtl, x: 10.25, y: Y + 2.52, w: 2.11, h: 0.8, fontSize: 15, valign: 'middle' });
  s.addNotes('מסלול ולא רשימה: חמישה סטטוסים הם דבר אחד שזז. זה השקף שהכי נשאלים עליו.');
}

// ================================================================ 10 · questions the screen answers
{
  const s = page('התמונה המלאה של ההטבה', 'שלוש שאלות — ואיפה כל תשובה יושבת');
  shot(s, 'details.png', { x: 6.55, y: 1.7, w: W - M - 6.55, h: 4.6 });
  const qs = [
    ['כמה כבר קיבלתי, וכמה נשאר?', 'באזור "סיכום מימוש" — הסכום ששולם, מה שנותר, והסכום הכולל.'],
    ['מה קרה לקבלה שהגשתי?', 'באזור "בקשות להחזר" — התאריך, הסכום וסטטוס הטיפול בה.'],
    ['איך מגישים עוד אחת?', 'בכפתור הכחול, מעל "בקשות להחזר".'],
  ];
  qs.forEach((q, i) => {
    const y = 1.85 + i * 1.5;
    card(s, { x: M, y, w: 5.5, h: 1.3 });
    badge(s, M + 5.5 - 0.62, y + 0.24, i + 1, GREEN);
    s.addText(q[0], { ...rtl, x: M + 0.3, y: y + 0.18, w: 4.5, h: 0.4, fontSize: 17, bold: true, color: NAVY });
    s.addText(q[1], { ...rtl, x: M + 0.3, y: y + 0.6, w: 4.9, h: 0.6, fontSize: 14, color: MUTED, valign: 'top' });
  });
  s.addNotes('שאלות ולא חלקים: אנשים לא זוכרים "ארבעה אזורים", הם זוכרים איפה נמצאת התשובה שלהם.');
}

// ================================================================ 11 · the fork
{
  const s = page('בהטבה פוטנציאלית — מה כתוב על הכפתור', 'שני כפתורים, שני מסכים שונים');
  card(s, { x: 4.4, y: 1.75, w: 4.53, h: 0.72, r: 0.36, fill: '14477E', line: '14477E' });
  s.addText('מה כתוב על הכפתור?', { ...ctr, x: 4.4, y: 1.75, w: 4.53, h: 0.72, fontSize: 19, bold: true, color: 'FFFFFF', valign: 'middle' });
  const cw = (W - 2 * M - 0.6) / 2;
  const routes = [
    ['הגשת בקשה', '1F7A4D', 'btn_request.png', 'בכרטיס כתוב "לבדיקת זכאות חדשה".', 'נפתח טופס בקשה בן שלושה שלבים, והמערכת בודקת אותו.'],
    ['שליחת פנייה', '6B3FA0', 'btn_inquiry.png', 'בכרטיס כתוב "אפשר לפנות לעובד השיקום".', 'נפתחת פנייה לעובד השיקום, והזכאות נבדקת מולו.'],
  ];
  routes.forEach((r, i) => {
    const x = M + (1 - i) * (cw + 0.6);
    s.addShape(pres.ShapeType.rect, { x: x + cw / 2 - 0.015, y: 2.6, w: 0.03, h: 0.5, fill: { color: LINE } });
    card(s, { x, y: 3.1, w: cw, h: 2.6, line: r[1], lw: 1.6 });
    shot(s, r[2], { x: x + cw - 2.1, y: 3.35, w: 1.8, h: 0.55 });
    s.addText(r[3], { ...rtl, x: x + 0.32, y: 4.05, w: cw - 0.64, h: 0.6, fontSize: 16, bold: true, color: r[1], valign: 'top' });
    s.addText(r[4], { ...rtl, x: x + 0.32, y: 4.65, w: cw - 0.64, h: 0.85, fontSize: 15, color: INK, valign: 'top' });
  });
  s.addText('בשני המקרים הבקשה נכנסת למצפן, ואפשר לעקוב אחריה משם.', {
    ...rtl, x: M, y: 5.95, w: W - 2 * M, h: 0.45, fontSize: 16, color: CLAY, align: 'center',
  });
  s.addNotes('צומת אחת עם שאלה אחת. ההבדל בין השניים חוזר בשאלות.');
}

// ================================================================ 12 · after you send
{
  const s = page('מה קורה אחרי שהגשת', 'ומה נדרש ממך בכל שלב');
  const Y = 2.5;
  const steps = [
    ['נשלח', 'מופיעה הודעת אישור, והבקשה מופיעה במצפן.', 'לא נדרש דבר'],
    ['בטיפול', 'הבקשה התקבלה ועדיין אין החלטה.', 'לא נדרש דבר'],
    ['החלטה', 'הסטטוס משתנה ל"פעילה" או ל"נדחתה".', 'כאן מתחילים להגיש קבלות'],
  ];
  const CW = 3.5, GAP = 0.62;
  const xOf = i => W - M - CW - i * (CW + GAP);
  s.addShape(pres.ShapeType.rect, { x: xOf(2) + CW / 2, y: Y + 0.31, w: xOf(0) - xOf(2), h: 0.02, fill: { color: LINE } });
  steps.forEach((st, i) => {
    const x = xOf(i);
    badge(s, x + CW / 2 - 0.3, Y + 0.02, i + 1, i === 2 ? GREEN : NAVY, 0.6);
    s.addText(st[0], { ...ctr, x, y: Y + 0.78, w: CW, h: 0.45, fontSize: 24, bold: true, color: i === 2 ? GREEN : NAVY });
    s.addText(st[1], { ...ctr, x: x + 0.2, y: Y + 1.3, w: CW - 0.4, h: 0.85, fontSize: 14.5, color: MUTED, valign: 'top' });
    card(s, { x: x + 0.55, y: Y + 2.2, w: CW - 1.1, h: 0.6, r: 0.3, fill: i === 2 ? 'E3F3E9' : 'FFFFFF', line: i === 2 ? GREEN : LINE });
    s.addText(st[2], { ...ctr, x: x + 0.55, y: Y + 2.2, w: CW - 1.1, h: 0.6, fontSize: 14, bold: true, color: i === 2 ? '1F6E43' : MUTED, valign: 'middle' });
  });
  s.addText('הגשת בקשה אינה אישור אוטומטי. הזכאות נבדקת לפי הקריטריונים שנקבעו בחוק.', {
    ...rtl, x: M, y: 6.0, w: W - 2 * M, h: 0.45, fontSize: 16, bold: true, color: CLAY, align: 'center',
  });
  s.addNotes('ציר זמן, ובכל תחנה מה נדרש מהמבוטח. התשובה ברוב הדרך היא כלום.');
}

// ================================================================ 13 · divider
dark('החלק השני', 'הגשת חשבונית או קבלה', 'למה דרך המצפן, מה אפשר דרכו, ואיפה מגישים כשאי אפשר.');

// ================================================================ 14 · comparison
{
  const s = page('למה דווקא דרך המצפן', 'אותה חשבונית, שתי דרכים לשלוח אותה');
  const rows = [
    ['לאן זה מגיע', 'ישר להטבה הנכונה בתיק שלך', 'לתיק, ומשם צריך לשייך אותה'],
    ['מה רואים אחר כך', 'הקבלה מופיעה עם סכום וסטטוס טיפול', 'אין מעקב מהמצפן'],
    ['כמה חשבוניות בבת אחת', 'כמה שצריך, באותה בקשה', 'כל מסמך בנפרד'],
  ];
  const HX = 4.05, CW = 4.1;
  s.addText('דרך המצפן', { ...ctr, x: W - M - CW, y: 1.9, w: CW, h: 0.45, fontSize: 19, bold: true, color: GREEN });
  s.addText('שליחת מסמך כללית', { ...ctr, x: W - M - CW - 0.3 - CW, y: 1.9, w: CW, h: 0.45, fontSize: 19, bold: true, color: MUTED });
  rows.forEach((r, i) => {
    const y = 2.5 + i * 1.15;
    card(s, { x: W - M - CW, y, w: CW, h: 0.98, fill: 'E9F3ED', line: GREEN, lw: 1.4 });
    card(s, { x: W - M - CW - 0.3 - CW, y, w: CW, h: 0.98, fill: 'FFFFFF', line: LINE });
    s.addText(r[1], { ...ctr, x: W - M - CW + 0.2, y, w: CW - 0.4, h: 0.98, fontSize: 15, bold: true, color: '1F6E43', valign: 'middle' });
    s.addText(r[2], { ...ctr, x: W - M - CW - 0.3 - CW + 0.2, y, w: CW - 0.4, h: 0.98, fontSize: 15, color: MUTED, valign: 'middle' });
    s.addText(r[0], { ...rtl, x: M, y, w: HX - M - 0.3, h: 0.98, fontSize: 15.5, bold: true, color: NAVY, valign: 'middle' });
  });
  s.addText('שתי הדרכים מגיעות אלינו. רק אחת מהן מספרת לך מה קרה אחר כך.', {
    ...rtl, x: M, y: 6.15, w: W - 2 * M, h: 0.45, fontSize: 17, bold: true, color: CLAY, align: 'center',
  });
  s.addNotes('השוואה ולא רשימת יתרונות. השורה השנייה היא זו שמשכנעת.');
}

// ================================================================ 15 · the decision tree
{
  const s = page('יש לך חשבונית — לאן היא הולכת', 'שתי שאלות, ואתה יודע');
  const q = (x, y, w, t) => {
    card(s, { x, y, w, h: 0.68, r: 0.34, fill: '14477E', line: '14477E' });
    s.addText(t, { ...ctr, x: x + 0.15, y, w: w - 0.3, h: 0.68, fontSize: 16, bold: true, color: 'FFFFFF', valign: 'middle' });
  };
  const ans = (x, y, w, h, label, body, color, fill) => {
    card(s, { x, y, w, h, line: color, lw: 1.6, fill: fill || 'FFFFFF' });
    s.addText(label, { ...rtl, x: x + 0.28, y: y + 0.2, w: w - 0.56, h: 0.42, fontSize: 17, bold: true, color });
    s.addText(body, { ...rtl, x: x + 0.28, y: y + 0.64, w: w - 0.56, h: h - 0.85, fontSize: 14.5, color: INK, valign: 'top' });
  };
  const drop = (x, y, h) => s.addShape(pres.ShapeType.rect, { x: x - 0.015, y, w: 0.03, h, fill: { color: LINE } });

  q(8.15, 1.75, 4.43, 'ההטבה מופיעה ב"ההטבות שלי"?');
  drop(10.36, 2.43, 0.42);
  ans(8.15, 2.85, 4.43, 1.5, 'כן — זו הדרך הקצרה', 'נכנסים להטבה ← "פרטים נוספים" ← הכפתור הכחול "להגשת חשבונית / קבלה חדשה".', GREEN, 'E9F3ED');
  drop(10.36, 4.35, 0.4);
  s.addText('רק בהטבה בסטטוס "פעילה". בהטבה שהסתיימה או נדחתה אין כפתור הגשה.', {
    ...rtl, x: 8.15, y: 4.75, w: 4.43, h: 0.8, fontSize: 13.5, color: MUTED, valign: 'top',
  });

  q(M, 1.75, 6.9, 'לא מופיעה? מחפשים אותה בהטבות הפוטנציאליות — ומה כתוב שם על הכפתור?');
  drop(M + 1.75, 2.43, 0.42);
  drop(M + 5.15, 2.43, 0.42);
  const cw2 = 3.3;
  ans(M, 2.85, cw2, 2.05, '"הגשת בקשה"', 'אפשר להגיש כאן. נפתח אותו טופס בן שלושה שלבים.', GREEN, 'E9F3ED');
  ans(M + cw2 + 0.3, 2.85, cw2, 2.05, 'לא מופיע', 'ההגשה נעשית דרך "העלאת מסמכים" באזור האישי — בשקף הבא.', CLAY, 'FBEFE6');
  s.addText('בכל מקרה החשבונית מגיעה אלינו. השאלה היחידה היא מאיזה מסך.', {
    ...rtl, x: M, y: 5.75, w: W - 2 * M, h: 0.45, fontSize: 16, color: NAVY, align: 'center', bold: true,
  });
  s.addNotes('עץ החלטה. זה השקף שעונה מראש על "ניסיתי ולא הצלחתי".');
}

// ================================================================ 16 · the upload form, filled
{
  const s = page('כשלא מופיע "הגשת בקשה"', 'העלאת מסמכים באזור האישי — ארבעה שדות ושליחה');
  shot(s, 'upload.png', { x: M, y: 1.75, w: 7.75, h: 4.6 });
  const fields = [
    ['בתפריט', 'פעולות באתר ← העלאת מסמכים'],
    ['נושא', 'שיקום'],
    ['קטגוריה', 'פניות'],
    ['מסמך', 'פנייה'],
    ['הקובץ', 'צרף קובץ — החשבונית או הקבלה'],
    ['ואז', 'שלח מסמך'],
  ];
  fields.forEach((f, i) => {
    const y = 1.9 + i * 0.74, x = 8.75, w = W - M - 8.75;
    badge(s, x + w - 0.36, y + 0.06, i + 1, i === 5 ? GREEN : NAVY, 0.36);
    s.addText(f[0], { ...rtl, x: x + w - 1.95, y: y + 0.04, w: 1.45, h: 0.32, fontSize: 13, color: MUTED });
    s.addText(f[1], { ...rtl, x, y: y + 0.3, w: w - 0.5, h: 0.36, fontSize: 15, bold: true, color: i === 5 ? GREEN : NAVY });
  });
  s.addNotes('טופס ולא רשימת פעולות: רואים איזה שדה ומה בוחרים בו.');
}

// ================================================================ 17 · the three steps
{
  const s = page('טופס ההגשה', 'אותו טופס בשתי הדרכים — שלושה שלבים');
  const files = ['form1.png', 'form2.png', 'form3.png'];
  const caps = [
    ['פרטי ההטבה', 'רק בודקים שהפרטים נכונים, ולוחצים "הבא".'],
    ['החשבונית', 'מצרפים את הקובץ, וממלאים מספר, תאריך וסכום כולל מע״מ.'],
    ['הצהרה וחתימה', 'קוראים, מסמנים, חותמים בעכבר או באצבע — ושולחים.'],
  ];
  const CW = (W - 2 * M - 0.8) / 3;
  s.addShape(pres.ShapeType.rect, { x: M + CW / 2, y: 1.95, w: W - 2 * M - CW, h: 0.02, fill: { color: LINE } });
  files.forEach((f, i) => {
    const x = M + (2 - i) * (CW + 0.4);
    badge(s, x + CW / 2 - 0.26, 1.71, i + 1, NAVY, 0.52);
    shot(s, f, { x, y: 2.5, w: CW, h: 2.5 });
    s.addText(caps[i][0], { ...ctr, x, y: 5.15, w: CW, h: 0.42, fontSize: 19, bold: true, color: NAVY });
    s.addText(caps[i][1], { ...ctr, x: x + 0.15, y: 5.6, w: CW - 0.3, h: 1.0, fontSize: 14, color: MUTED, valign: 'top' });
  });
  s.addNotes('שלושה שלבים, ואפשר לראות שהראשון הוא רק אישור.');
}

// ================================================================ 18 · Q&A divider
dark('', 'שאלות ותשובות', 'לפי הרגע שבו הן נשאלות.');

// ================================================================ 19-21 · FAQ
const FAQ = [
  ['לפני שנכנסים', [
    ['אני לא מוצא את "מצפן הזכויות שלי" בתפריט. למה?',
      'בשלב זה המצפן מוצג רק למשפחות שכולות. בהמשך הוא ייפתח לאוכלוסיות נוספות. מי ששייך ועדיין לא רואה — מוזמן לפנות אלינו.'],
    ['אני רואה את המצפן אבל אין בו הטבות.',
      'המצפן מציג הטבות מהשנתיים האחרונות. אם לא הוגשו בקשות בתקופה זו, "ההטבות שלי" יהיה ריק — כדאי לבדוק את ההטבות הפוטנציאליות.'],
    ['הטבה שאני מקבל לא מופיעה במצפן. איבדתי אותה?',
      'לא. המצפן נבנה בהדרגה והטבות מתווספות אליו. הזכאות אינה תלויה במה שמוצג בו.'],
  ]],
  ['כשמסתכלים על הטבה', [
    ['מה ההבדל בין "פעילה" ל"הסתיימה"?',
      '"פעילה" היא הטבה מאושרת שנשארה בה יתרה, ואפשר להגיש בה קבלות. "הסתיימה" היא הטבה שנוצלה במלואה, או שתקופת הזכאות שלה חלפה.'],
    ['הבקשה שלי בסטטוס "בטיפול" כבר הרבה זמן.',
      '"בטיפול" אומר שהבקשה התקבלה ועדיין לא התקבלה בה החלטה. אין צורך להגיש שוב.'],
    ['איך יודעים כמה עוד נשאר לנצל?',
      'בדף ההטבה, באזור "סיכום מימוש", מופיע הסכום ששולם, מה שנותר, והסכום הכולל.'],
  ]],
  ['כשמגישים', [
    ['מה ההבדל בין "הגשת בקשה" ל"שליחת פנייה"?',
      'זה תלוי בהטבה. "הגשת בקשה" פותחת טופס בן שלושה שלבים שהמערכת בודקת. "שליחת פנייה" נשלחת לעובד השיקום, והזכאות נבדקת מולו.'],
    ['האם הגשת הבקשה מבטיחה שאקבל את ההטבה?',
      'לא. הגשת בקשה אינה אישור אוטומטי. הזכאות נבדקת לפי הקריטריונים שנקבעו בחוק ובהתאם למסמכים שהוגשו.'],
    ['אילו מסמכים צריך לצרף?',
      'זה משתנה מהטבה להטבה. יש הטבות שדורשות קבלה בלבד, ויש שדורשות מסמכים נוספים. המסמכים הנדרשים יפורטו בטופס.'],
  ]],
];
FAQ.forEach(([group, qa]) => {
  const s = page('שאלות ותשובות', group);
  qa.forEach((q, i) => {
    const y = 1.9 + i * 1.55;
    card(s, { x: M, y, w: W - 2 * M, h: 1.35 });
    s.addText(q[0], { ...rtl, x: M + 0.34, y: y + 0.15, w: W - 2 * M - 0.68, h: 0.4, fontSize: 17.5, bold: true, color: NAVY });
    s.addText(q[1], { ...rtl, x: M + 0.34, y: y + 0.57, w: W - 2 * M - 0.68, h: 0.68, fontSize: 14.5, color: INK, valign: 'top' });
  });
});

// ================================================================ 22 · closing
{
  const s = dark('', 'מה כבר מוכן למבוטחים', '', { y: 1.15, size: 42 });
  const items = [
    ['שני סרטוני הסבר', 'הסבר כללי (4 דקות), והגשת חשבונית או קבלה (3 דקות).'],
    ['שני מדריכים כתובים', 'גרסת A4 להדפסה, וגרסה לטלפון — רצף אחד, בלי דפדוף.'],
    ['שאלות ותשובות', 'רשימה מלאה, לעדכון לפי מה שיישאל בשטח.'],
  ];
  items.forEach((it, i) => {
    const y = 2.6 + i * 1.15;
    s.addText(it[0], { ...rtl, x: W - M - 4.7, y, w: 4.7, h: 0.42, fontSize: 21, bold: true, color: '8FC7AC' });
    s.addText(it[1], { ...rtl, x: 4.35, y: y + 0.06, w: W - M - 4.7 - 4.55, h: 0.85, fontSize: 15, color: 'C3DCCF', valign: 'top' });
  });
  s.addImage({ path: path.join(A, 'qr.png'), x: M, y: 2.7, w: 1.95, h: 1.95 });
  s.addText('ps.btl.gov.il', { x: M, y: 4.78, w: 1.95, h: 0.35, fontSize: 13, bold: true, color: 'FFFFFF', align: 'center', fontFace: F, isTextBox: true, margin: 0 });
  s.addText('תודה', { ...rtl, x: M, y: 6.05, w: W - 2 * M, h: 0.6, fontSize: 26, bold: true, color: 'FFFFFF', align: 'center' });
  s.addNotes('סיום. להשאיר את ה-QR על המסך בזמן השאלות.');
}

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));
