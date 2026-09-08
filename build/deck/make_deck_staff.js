// המצגת לעובדים. הדגשים לקוחים מ"מדריך לעובד אתר מצפן אישי",
// והצורה של כל שקף היא הצורה שהתוכן שלו לובש: מסלול, מפה, צומת, כלל.
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const A = path.join(__dirname, 'assets');
const OUT = path.join(__dirname, '..', 'out', 'מצפן זכויות איבה - מצגת לעובדים.pptx');

const NAVY = '14477E', INK = '1E2C24', MUTED = '64796C', LINE = 'CFE0D5';
const GREEN = '2C7A5B', CLAY = 'B85C22', RED = 'A8281F', PAPER = 'FFFFFF';
const F = 'Arial', W = 13.33, H = 7.5, M = 0.75;

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

function ground(bg) {
  const s = pres.addSlide();
  s.addImage({ path: path.join(A, bg), x: 0, y: 0, w: W, h: H });
  return s;
}
function page(title, kicker) {
  const s = ground('bg_sage.jpg');
  s.addText(title, { ...rtl, x: M, y: 0.5, w: W - 2 * M, h: 0.7, fontSize: 33, bold: true, color: NAVY });
  if (kicker) s.addText(kicker, { ...rtl, x: M, y: 1.16, w: W - 2 * M, h: 0.4, fontSize: 15.5, color: MUTED });
  s.addText('מצפן זכויות איבה · מדריך לעובד · אגף שיקום', {
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
  if (note) s.addText(note, { ...rtl, x: M, y: y + 1.15, w: W - 2 * M, h: 0.9, fontSize: 18, color: 'C3DCCF' });
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
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: o.r === undefined ? 0.12 : o.r,
    fill: { color: o.fill || PAPER }, line: { color: o.line || LINE, width: o.lw || 1 },
  });
}
function pill(s, o) {
  const [c, tint] = ST[o.key];
  card(s, { x: o.x, y: o.y, w: o.w, h: 0.6, r: 0.3, fill: tint, line: c, lw: 1.5 });
  s.addShape(pres.ShapeType.ellipse, { x: o.x + o.w - 0.5, y: o.y + 0.2, w: 0.2, h: 0.2, fill: { color: c } });
  s.addText(o.key, { ...ctr, x: o.x + 0.18, y: o.y, w: o.w - 0.72, h: 0.6, fontSize: 18, bold: true, color: c, valign: 'middle' });
}
function arrow(s, x, y, w = 0.34) {
  s.addShape(pres.ShapeType.leftArrow, { x, y, w, h: 0.22, fill: { color: LINE } });
}
function legend(s, rows, o) {
  rows.forEach((r, i) => {
    const y = o.y + i * o.gap;
    badge(s, o.x + o.w - 0.42, y, i + 1, r[2] || NAVY);
    s.addText(r[0], { ...rtl, x: o.x, y: y - 0.03, w: o.w - 0.58, h: 0.36, fontSize: o.title || 16, bold: true, color: NAVY });
    s.addText(r[1], { ...rtl, x: o.x, y: y + 0.33, w: o.w - 0.58, h: o.gap - 0.36, fontSize: o.body || 13, color: MUTED, valign: 'top' });
  });
}

// ================================================================ 1 · cover
{
  const s = ground('bg_forest.jpg');
  s.addImage({ path: path.join(A, 'logo.png'), x: W - M - 2.0, y: 0.55, w: 2.0, h: 0.73 });
  s.addText('אגף שיקום · מדריך לעובד', { ...rtl, x: M, y: 2.35, w: W - 2 * M, h: 0.4, fontSize: 18, color: '8FC7AC', bold: true });
  s.addText('אתר מצפן אישי', { ...rtl, x: M, y: 2.8, w: W - 2 * M, h: 1.35, fontSize: 62, bold: true, color: 'FFFFFF' });
  s.addText('מה המבוטח רואה, ומה זה משנה בעבודה שלנו.', {
    ...rtl, x: M, y: 4.15, w: W - 2 * M, h: 0.55, fontSize: 22, color: 'C3DCCF',
  });
  s.addNotes('פתיחה. המצפן נועד לרכז עבור המבוטח, במקום אחד, תמונה מלאה של הזכויות וההטבות המגיעות לו כנפגע איבה.');
}

// ================================================================ 2 · the route of the talk
{
  const s = page('מה נעבור', 'שלוש תחנות, ואז שאלות');
  const stops = [
    ['מי רואה מה', 'אילו אוכלוסיות, ומה מוצג להן'],
    ['מה הוא רואה במסך', 'המבנה, הסטטוסים, וההגשה'],
    ['מה זה משנה אצלנו', 'מסלול המסמך, והכללים שחייבים לזכור'],
  ];
  const NW = 3.6, GAP = 0.55, Y = 2.85;
  const xOf = i => W - M - NW - i * (NW + GAP);
  s.addShape(pres.ShapeType.rect, { x: xOf(2) + NW / 2, y: Y + 0.55, w: xOf(0) - xOf(2), h: 0.02, fill: { color: LINE } });
  stops.forEach((st, i) => {
    const x = xOf(i);
    badge(s, x + NW / 2 - 0.28, Y + 0.28, i + 1, NAVY, 0.56);
    s.addText(st[0], { ...ctr, x, y: Y + 1.0, w: NW, h: 0.45, fontSize: 23, bold: true, color: NAVY });
    s.addText(st[1], { ...ctr, x: x + 0.2, y: Y + 1.5, w: NW - 0.4, h: 0.8, fontSize: 15, color: MUTED, valign: 'top' });
  });
  card(s, { x: M, y: 5.4, w: W - 2 * M, h: 0.95 });
  s.addText([
    { text: 'החלק השלישי הוא העיקר. ', options: { bold: true, color: GREEN } },
    { text: 'שני הראשונים נועדו כדי שנוכל לנהל שיחה על מסך שאנחנו לא רואים מול העיניים.', options: { color: INK } },
  ], { ...rtl, x: M + 0.35, y: 5.4, w: W - 2 * M - 0.7, h: 0.95, fontSize: 17, valign: 'middle' });
}

// ================================================================ 3 · the asymmetry
{
  const s = page('מה הוא רואה, ומה אנחנו רואים', 'הפער הזה הוא הדבר החשוב ביותר במצגת');
  const cw = (W - 2 * M - 0.6) / 2;
  const cols = [
    ['המבוטח, במצפן', NAVY, [
      'תכניות מהשנתיים האחרונות בלבד.',
      'רק הטבות שכבר הוטמעו במצפן.',
      'סטטוס, תקופת זכאות, סוג תשלום ויתרה למימוש.',
    ]],
    ['אנחנו, בתיק', GREEN, [
      'את התיק כולו, בלי מגבלת שנתיים.',
      'גם הטבות שעדיין לא מוצגות במצפן.',
      'את הנימוקים, ההחלטות והמשימות שמאחורי הסטטוס.',
    ]],
  ];
  cols.forEach((col, i) => {
    const x = M + (1 - i) * (cw + 0.6);
    card(s, { x, y: 1.85, w: cw, h: 2.95, line: col[1], lw: 1.6 });
    s.addText(col[0], { ...rtl, x: x + 0.35, y: 2.12, w: cw - 0.7, h: 0.5, fontSize: 22, bold: true, color: col[1] });
    col[2].forEach((t, j) => {
      s.addShape(pres.ShapeType.ellipse, { x: x + cw - 0.62, y: 2.86 + j * 0.68, w: 0.14, h: 0.14, fill: { color: col[1] } });
      s.addText(t, { ...rtl, x: x + 0.35, y: 2.74 + j * 0.68, w: cw - 1.05, h: 0.62, fontSize: 15.5, color: INK, valign: 'top' });
    });
  });
  card(s, { x: M, y: 5.1, w: W - 2 * M, h: 1.3, fill: 'FBEFE6', line: CLAY, lw: 1.6 });
  s.addText('כשמבוטח אומר "זה לא מופיע במצפן, אז זה לא מגיע לי" — זו טעות.', {
    ...rtl, x: M + 0.4, y: 5.3, w: W - 2 * M - 0.8, h: 0.45, fontSize: 21, bold: true, color: CLAY,
  });
  s.addText('המצפן מציג שנתיים אחורה, והוא נבנה בהדרגה. הזכאות אינה תלויה במה שמוצג בו — וזה מה שצריך לומר לו.', {
    ...rtl, x: M + 0.4, y: 5.78, w: W - 2 * M - 0.8, h: 0.5, fontSize: 16, color: INK,
  });
  s.addNotes('זה השקף שהכי חשוב לעובד. בלעדיו הוא עלול לאשר בטעות אמירה שגויה של המבוטח.');
}

// ================================================================ 4 · who sees it
{
  const s = page('אילו אוכלוסיות רואות את המצפן בשלב זה');
  const cw = (W - 2 * M - 0.6) / 2;
  card(s, { x: M + cw + 0.6, y: 1.85, w: cw, h: 3.2, line: NAVY, lw: 1.6 });
  s.addText('בוגרים', { ...rtl, x: M + cw + 0.95, y: 2.1, w: cw - 0.7, h: 0.5, fontSize: 24, bold: true, color: NAVY });
  [['נפגעי פעולות איבה (נכים)', 'שיש להם תיק איבה והכרה.'],
   ['משפחות שכולות', 'שיש להן בדלפק שורה של נפגעי איבה — "תלוי".']].forEach((r, i) => {
    const y = 2.75 + i * 1.02;
    s.addText(r[0], { ...rtl, x: M + cw + 0.95, y, w: cw - 0.7, h: 0.36, fontSize: 17, bold: true, color: INK });
    s.addText(r[1], { ...rtl, x: M + cw + 0.95, y: y + 0.36, w: cw - 0.7, h: 0.6, fontSize: 15, color: MUTED, valign: 'top' });
  });
  card(s, { x: M, y: 1.85, w: cw, h: 3.2, line: GREEN, lw: 1.6 });
  s.addText('קטינים', { ...rtl, x: M + 0.35, y: 2.1, w: cw - 0.7, h: 0.5, fontSize: 24, bold: true, color: GREEN });
  s.addText('כל מי שיש לו תיק באיבה או בשיקום עם הטבה פעילה, וההורה המוכר כנפגע איבה מקבל עבורו את התשלומים.', {
    ...rtl, x: M + 0.35, y: 2.75, w: cw - 0.7, h: 1.2, fontSize: 16, color: INK, valign: 'top',
  });
  s.addText('ההורה רואה את ההטבות של הילד בתוך המצפן שלו, באזור "הצגת הטבות עבור".', {
    ...rtl, x: M + 0.35, y: 4.0, w: cw - 0.7, h: 0.85, fontSize: 15, color: MUTED, valign: 'top',
  });
  card(s, { x: M, y: 5.35, w: W - 2 * M, h: 0.95 });
  s.addText('מי ששייך לאחת הקבוצות ועדיין לא רואה את המצפן — מפנים אותו אלינו. אין צורך שיגיש שוב שום דבר.', {
    ...rtl, x: M + 0.35, y: 5.35, w: W - 2 * M - 0.7, h: 0.95, fontSize: 16.5, color: INK, valign: 'middle' });
}

// ================================================================ 5 · what he sees: the map
{
  const s = page('מבנה המצפן', 'ארבעה נושאים — וזה המסך שהוא חוזר אליו בכל פעם');
  shot(s, 'zones.png', { x: M, y: 1.7, w: 8.35, h: 4.55 });
  legend(s, [
    ['הצגת הטבות עבור', 'בחירת בן המשפחה שעבורו רואים מידע. מוצג רק כשיש ילדים קטינים שההטבה מתקבלת עבורם.', 'E8842B'],
    ['קטגוריות חיפוש', 'חיפוש הטבה לפי שם או לפי נושא — טיפול או אביזר רפואי, שיקום מקצועי, רווחה ועוד.', '2E9E4F'],
    ['ההטבות שלי', 'רשימת ההטבות שהמבוטח הגיש, והסטטוס של כל אחת.', '8E3BB5'],
    ['הטבות פוטנציאליות', 'הטבות שייתכן שהוא זכאי להן ועדיין לא ביקש.', '2A9BD6'],
  ], { x: 9.4, y: 1.85, w: W - M - 9.4, gap: 1.14 });
  s.addNotes('אפשר להצביע על המסך ולעבור אזור אזור. השמות הם השמות שהמבוטח יגיד בטלפון.');
}

// ================================================================ 6 · my benefits — what is shown
{
  const s = page('ההטבות שלי', 'תכניות מתיק השיקום — מה בדיוק מוצג בכל שורה');
  const items = [
    ['תאריך ההגשה', 'מתי הוגשה הבקשה'],
    ['סטטוס הטיפול', 'אושרה · אושרה חלקית · נדחתה · בטיפול'],
    ['תקופת הזכאות', 'מאיזה תאריך ההטבה בתוקף'],
    ['סוג התשלום', 'חודשי · שנתי · חד-פעמי · הכפוף להחזר הוצאות'],
    ['היתרה למימוש', 'כמה נותר, בגרף'],
  ];
  items.forEach((it, i) => {
    const y = 1.85 + i * 0.86;
    card(s, { x: M, y, w: 6.9, h: 0.72 });
    s.addText(it[0], { ...rtl, x: 4.55, y, w: 3.0, h: 0.72, fontSize: 16.5, bold: true, color: NAVY, valign: 'middle' });
    s.addText(it[1], { ...rtl, x: M + 0.3, y, w: 3.6, h: 0.72, fontSize: 14.5, color: MUTED, valign: 'middle' });
  });
  card(s, { x: M, y: 6.15, w: 6.9, h: 0.72, fill: 'FBEFE6', line: CLAY, lw: 1.5 });
  s.addText('מוצגות תכניות מהשנתיים האחרונות בלבד.', {
    ...ctr, x: M, y: 6.15, w: 6.9, h: 0.72, fontSize: 17, bold: true, color: CLAY, valign: 'middle' });
  shot(s, 'benefit.png', { x: 8.0, y: 1.85, w: W - M - 8.0, h: 5.0 });
}

// ================================================================ 7 · statuses as a path
{
  const s = page('חמישה סטטוסים, מסלול אחד', 'זו השפה שהמבוטח רואה — ולכן זו השפה שבה נדבר איתו');
  const LINES = {
    'פוטנציאלי': 'טרם הוגשה ותיתכן בה זכאות. אפשר להגיש דרך האתר האישי.',
    'בטיפול': 'הוגשה וטרם התקבלה בה החלטה.',
    'פעילה': 'אושרה, ויש בה יתרה. אפשר להגיש בה קבלות להחזר.',
    'הסתיימה': 'לא נותרה בה יתרה, ולא ניתן להגיש בה קבלות נוספות.',
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
  s.addText('הבקשה נדחתה, וסיבת הדחייה מאישור ההחלטה מופיעה כאן — המבוטח קורא אותה.', {
    ...rtl, x: bx - 3.35, y: Y + 2.66, w: 3.15, h: 0.7, fontSize: 13.5, color: MUTED, valign: 'top',
  });
  card(s, { x: 10.03, y: Y + 2.4, w: 2.55, h: 1.05, fill: 'E9F3ED', line: GREEN, lw: 1.4 });
  s.addText('הסטטוס גלוי למבוטח בכל רגע.', {
    ...ctr, x: 10.15, y: Y + 2.4, w: 2.31, h: 1.05, fontSize: 15, bold: true, color: '1F6E43', valign: 'middle' });
  s.addNotes('הנימוק שנבחר באישור ההחלטה הוא טקסט שהמבוטח יקרא. שווה לומר את זה במפורש.');
}

// ================================================================ 8 · details page anatomy
{
  const s = page('"פרטים נוספים" — התמונה המלאה של התכנית', 'שלושה אזורים, וזה מה שהוא רואה בכל אחד');
  shot(s, 'emp_details.png', { x: 6.5, y: 1.7, w: W - M - 6.5, h: 4.7 });
  legend(s, [
    ['פרטי ההטבה', 'משקף את התכנית שאושרה בתיק השיקום — סטטוס, תקופה, סכום וסוג תשלום.'],
    ['סיכום מימוש', 'בר עם סכום ההטבה או כמות הטיפולים: כמה נוצל וכמה עוד ניתן לנצל.'],
    ['בקשות להחזר', 'כל קבלה שהוגשה — מספר, סכום, הסכום שאושר, והורדה של הקבלה עצמה.'],
  ], { x: M, y: 1.95, w: 5.35, gap: 1.5, title: 18, body: 14.5 });
  s.addText('בתכנית פעילה מופיע גם הכפתור להגשת חשבונית או קבלה חדשה.', {
    ...rtl, x: M, y: 6.05, w: 5.35, h: 0.5, fontSize: 15, bold: true, color: GREEN, valign: 'top',
  });
}

// ================================================================ 9 · potential benefits
{
  const s = page('הטבות פוטנציאליות', 'לפי הפרופיל האישי — ומה קורה כשהוא לוחץ');
  s.addText('מוצג מגוון הטבות שייתכן שהמבוטח זכאי להן, אך הוא עדיין לא בדק את זכאותו ולא ביקש אותן בעבר. הוא יכול להיכנס לכל אחת מהן ולהגיש בקשה לבדיקת זכאות — בשתי דרכים:', {
    ...rtl, x: M, y: 1.8, w: W - 2 * M, h: 0.9, fontSize: 17, color: INK, valign: 'top',
  });
  const cw = (W - 2 * M - 0.6) / 2;
  const routes = [
    ['טופס מקוון', '1F7A4D', 'btn_request.png', 'הבקשה נכנסת כטופס מקוון ומגיעה אלינו לטיפול.'],
    ['שליחת פנייה', '6B3FA0', 'btn_inquiry.png', 'הפנייה נשלחת למקום המתאים: מוקד רכב, דיור, או עובד השיקום.'],
  ];
  routes.forEach((r, i) => {
    const x = M + (1 - i) * (cw + 0.6);
    card(s, { x, y: 2.95, w: cw, h: 2.3, line: r[1], lw: 1.6 });
    shot(s, r[2], { x: x + cw - 2.1, y: 3.2, w: 1.8, h: 0.55 });
    s.addText(r[0], { ...rtl, x: x + 0.32, y: 3.85, w: cw - 0.64, h: 0.45, fontSize: 20, bold: true, color: r[1] });
    s.addText(r[3], { ...rtl, x: x + 0.32, y: 4.32, w: cw - 0.64, h: 0.8, fontSize: 15.5, color: INK, valign: 'top' });
  });
  card(s, { x: M, y: 5.55, w: W - 2 * M, h: 0.85 });
  s.addText('בשני המקרים הבקשה מופיעה למבוטח במצפן, והוא עוקב אחריה משם.', {
    ...ctr, x: M, y: 5.55, w: W - 2 * M, h: 0.85, fontSize: 16.5, color: INK, valign: 'middle' });
}

// ================================================================ 10 · submitting an invoice
{
  const s = page('הגשת חשבונית או קבלה', 'רק בתכנית פעילה — וזה מה שהוא מקבל בסוף');
  const steps = [
    'בתכנית פעילה, לחיצה על "להגשת חשבונית / קבלה חדשה".',
    'נפתח טופס מקוון עם פרטיו, כולל היתרה למימוש.',
    'הוא מצרף את המסמכים הרלוונטיים לאותה הטבה.',
    'לאחר השליחה מופיעה הודעת אישור.',
  ];
  steps.forEach((t, i) => {
    const y = 1.9 + i * 0.95;
    badge(s, M + 6.0 - 0.44, y, i + 1, i === 3 ? GREEN : NAVY, 0.44);
    s.addText(t, { ...rtl, x: M, y: y - 0.03, w: 5.4, h: 0.8, fontSize: 16.5, color: INK, valign: 'top' });
  });
  shot(s, 'emp_sent.png', { x: 7.1, y: 2.3, w: W - M - 7.1, h: 2.0 });
  card(s, { x: 7.1, y: 4.6, w: W - M - 7.1, h: 1.5, fill: 'FBEFE6', line: CLAY, lw: 1.5 });
  s.addText('המסמכים הנדרשים משתנים מהטבה להטבה, והם מפורטים בטופס עצמו.', {
    ...rtl, x: 7.45, y: 4.6, w: W - M - 7.45 - 0.3, h: 1.5, fontSize: 16, color: INK, valign: 'middle' });
  s.addText('הודעת האישור אומרת שהפנייה נקלטה — לא שהזכאות אושרה.', {
    ...rtl, x: M, y: 6.0, w: W - 2 * M, h: 0.45, fontSize: 16, bold: true, color: CLAY, align: 'center' });
}

// ================================================================ 11 · divider
dark('החלק השלישי', 'מה זה משנה בעבודה שלנו', 'מסלול המסמך מהמצפן אל התיק — והכללים שחייבים לזכור.');

// ================================================================ 12 · the document's route
{
  const s = page('מסלול המסמך מהמצפן', 'תהליך העבודה בתיק השיקום לטפסים המקוונים');
  const Y = 2.15;
  const CW = 3.55, GAP = 0.55;
  const xOf = i => W - M - CW - i * (CW + GAP);
  const stops = [
    ['המבוטח מגיש', 'טופס מקוון מהמצפן, עם המסמכים.'],
    ['רובוט מפענח', 'כל מסמך שמגיע מהמצפן — גם מסמך שאינו חשבונית או קבלה.'],
    ['אישור החלטה למגשרת', 'כשיש תכנית פתוחה.'],
  ];
  s.addShape(pres.ShapeType.rect, { x: xOf(2) + CW / 2, y: Y + 0.31, w: xOf(0) - xOf(2), h: 0.02, fill: { color: LINE } });
  stops.forEach((st, i) => {
    const x = xOf(i);
    badge(s, x + CW / 2 - 0.3, Y + 0.02, i + 1, NAVY, 0.6);
    s.addText(st[0], { ...ctr, x, y: Y + 0.78, w: CW, h: 0.45, fontSize: 21, bold: true, color: NAVY });
    s.addText(st[1], { ...ctr, x: x + 0.2, y: Y + 1.3, w: CW - 0.4, h: 0.9, fontSize: 14.5, color: MUTED, valign: 'top' });
  });
  card(s, { x: M, y: 4.6, w: W - 2 * M, h: 1.55, fill: 'FBEFE6', line: CLAY, lw: 1.6 });
  s.addText('שתי תכניות שאינן עוברות למגשרת:', {
    ...rtl, x: M + 0.4, y: 4.78, w: W - 2 * M - 0.8, h: 0.4, fontSize: 17, bold: true, color: CLAY });
  s.addText('תכנית ליווי אישית ליתומים (תל"א)   ·   התערבות לרווחה רגשית', {
    ...rtl, x: M + 0.4, y: 5.22, w: W - 2 * M - 0.8, h: 0.5, fontSize: 20, bold: true, color: INK });
  s.addNotes('הרובוט מפענח כל מסמך שמגיע מהמצפן, גם כזה שאינו חשבונית או קבלה.');
}

// ================================================================ 13 · wrong benefit — two routes
{
  const s = page('קבלה שהועלתה לתכנית לא מתאימה', 'שני מצבים — ולכל אחד טיפול אחר');
  const cw = (W - 2 * M - 0.6) / 2;
  card(s, { x: M + cw + 0.6, y: 1.8, w: cw, h: 4.1, line: GREEN, lw: 1.6 });
  s.addText('המגשרת שמה לב בפענוח', { ...rtl, x: M + cw + 0.95, y: 2.05, w: cw - 0.7, h: 0.45, fontSize: 21, bold: true, color: GREEN });
  ['משנה את השיוך ומשייכת להטבה קיימת, או פותחת חדשה בעזרת +.',
   'בעת הפענוח היא רואה את יתרת סכום התכנית, כדי לשייך במדויק.',
   'המבוטח יראה במצפן: "בקשה זו הועברה לטיפול בהטבה X".',
  ].forEach((t, i) => {
    const y = 2.7 + i * 1.05;
    s.addShape(pres.ShapeType.ellipse, { x: M + cw + 0.6 + cw - 0.62, y: y + 0.12, w: 0.14, h: 0.14, fill: { color: GREEN } });
    s.addText(t, { ...rtl, x: M + cw + 0.95, y, w: cw - 1.05, h: 0.95, fontSize: 15.5, color: INK, valign: 'top' });
  });
  card(s, { x: M, y: 1.8, w: cw, h: 4.1, line: CLAY, lw: 1.6 });
  s.addText('העו"ס מגלה בפתיחת התכנית', { ...rtl, x: M + 0.35, y: 2.05, w: cw - 0.7, h: 0.45, fontSize: 21, bold: true, color: CLAY });
  ['תמיד לפתוח את התכנית — גם אם היא שגויה.',
   'לדחות אותה עם הנימוק "התכנית שנבחרה אינה מתאימה להטבה המבוקשת".',
   'לפתוח תכנית שכן מתאימה למסמך, ולסרוק את המסמך מחדש.',
  ].forEach((t, i) => {
    const y = 2.7 + i * 1.05;
    s.addShape(pres.ShapeType.ellipse, { x: M + cw - 0.62, y: y + 0.12, w: 0.14, h: 0.14, fill: { color: CLAY } });
    s.addText(t, { ...rtl, x: M + 0.35, y, w: cw - 1.05, h: 0.95, fontSize: 15.5, color: INK, valign: 'top' });
  });
  s.addText('הכל משתקף למבוטח במצפן, בזמן אמת.', {
    ...rtl, x: M, y: 6.1, w: W - 2 * M, h: 0.45, fontSize: 17, bold: true, color: NAVY, align: 'center' });
}

// ================================================================ 14 · the rule
{
  const s = ground('bg_forest.jpg');
  s.addImage({ path: path.join(A, 'logo.png'), x: W - M - 1.7, y: 0.5, w: 1.7, h: 0.62 });
  s.addText('הכלל שאסור לשכוח', { ...rtl, x: M, y: 1.85, w: W - 2 * M, h: 0.4, fontSize: 16, bold: true, color: '8FC7AC' });
  s.addText('על העו"ס תמיד לפתוח תכנית', { ...rtl, x: M, y: 2.3, w: W - 2 * M, h: 1.0, fontSize: 46, bold: true, color: 'FFFFFF' });
  s.addText('גם כשברור שהתכנית שנבחרה שגויה.', { ...rtl, x: M, y: 3.35, w: W - 2 * M, h: 0.55, fontSize: 22, color: 'C3DCCF' });
  card(s, { x: M, y: 4.2, w: W - 2 * M, h: 1.25, fill: '2A4A3E', line: '8FC7AC', lw: 1.4 });
  s.addText([
    { text: 'אם לא פותחים את התכנית — היא נעלמת מהמצפן. ', options: { bold: true, color: 'FFD9A8' } },
    { text: 'המבוטח מגיש, ואז לא רואה כלום. משם מתחילות הפניות.', options: { color: 'E4F0E9' } },
  ], { ...rtl, x: M + 0.4, y: 4.2, w: W - 2 * M - 0.8, h: 1.25, fontSize: 19, valign: 'middle' });
  s.addText('פותחים ← דוחים עם הנימוק המתאים ← פותחים תכנית נכונה ← סורקים מחדש.', {
    ...rtl, x: M, y: 5.75, w: W - 2 * M, h: 0.5, fontSize: 18, bold: true, color: 'FFFFFF' });
  s.addNotes('אם יש שקף אחד שצריך לצאת מהכנס — זה הוא.');
}

// ================================================================ 15 · what he sees meanwhile
{
  const s = page('וזה מה שהמבוטח רואה בינתיים', 'הפעולה שלנו מופיעה אצלו כטקסט, מילה במילה');
  shot(s, 'emp_moved.png', { x: M, y: 2.0, w: W - 2 * M, h: 1.5 });
  const rows = [
    ['סיבת הדחייה', 'הנימוק שנבחר באישור ההחלטה הוא הטקסט שהוא קורא. שווה לבחור אותו בקפידה.'],
    ['ההעברה להטבה אחרת', 'מופיעה אצלו כ"בקשה זו הועברה לטיפול בהטבה X" — הוא יודע שהקבלה לא אבדה.'],
    ['אין צורך שיגיש שוב', 'וזה מה שנאמר לו כשהוא מתקשר לשאול.'],
  ];
  rows.forEach((r, i) => {
    const cw = (W - 2 * M - 0.8) / 3, x = M + (2 - i) * (cw + 0.4);
    card(s, { x, y: 3.9, w: cw, h: 2.2 });
    s.addText(r[0], { ...rtl, x: x + 0.3, y: 4.15, w: cw - 0.6, h: 0.45, fontSize: 17.5, bold: true, color: NAVY });
    s.addText(r[1], { ...rtl, x: x + 0.3, y: 4.62, w: cw - 0.6, h: 1.3, fontSize: 15, color: INK, valign: 'top' });
  });
}

// ================================================================ 16 · what to remember
{
  const s = page('חמישה דברים לקחת מכאן');
  const rules = [
    ['המצפן מציג שנתיים אחורה', '"לא מופיע במצפן" אינו "לא מגיע לי".'],
    ['תמיד לפתוח תכנית', 'אחרת היא נעלמת מהמצפן, והמבוטח לא רואה דבר.'],
    ['הנימוק נקרא על ידי המבוטח', 'סיבת הדחייה מאישור ההחלטה מוצגת לו כלשונה.'],
    ['קבלה בתכנית שגויה לא אובדת', 'משייכים אותה, והוא רואה "הועברה לטיפול בהטבה X".'],
    ['"בטיפול" לא דורש הגשה חוזרת', 'וזה מה שאומרים לו בטלפון.'],
  ];
  rules.forEach((r, i) => {
    const y = 1.85 + i * 1.0;
    card(s, { x: M, y, w: W - 2 * M, h: 0.86 });
    badge(s, W - M - 0.65, y + 0.22, i + 1, NAVY, 0.42);
    s.addText(r[0], { ...rtl, x: 7.6, y, w: 4.15, h: 0.86, fontSize: 17.5, bold: true, color: NAVY, valign: 'middle' });
    s.addText(r[1], { ...rtl, x: M + 0.35, y, w: 6.6, h: 0.86, fontSize: 15.5, color: INK, valign: 'middle' });
  });
  s.addNotes('אפשר לחלק את השקף הזה כדף אחד, לתלייה ליד המסך.');
}

// ================================================================ 17 · close
{
  const s = dark('', 'שאלות', '', { y: 2.6, size: 54 });
  s.addText('ומה שנשמע מכם בשטח — חוזר אלינו ונכנס לגרסה הבאה של המצפן.', {
    ...rtl, x: M, y: 4.0, w: W - 2 * M, h: 0.6, fontSize: 20, color: 'C3DCCF',
  });
}

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));
