// המצגת לכנס: היכרות עם מצפן זכויות איבה.
// הצילומים והטקסטים באים מאותם מקורות של הסרטונים והמדריכים.
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const A = path.join(__dirname, 'assets');
const OUT = path.join(__dirname, '..', 'out', 'מצפן זכויות איבה - מצגת לכנס.pptx');

const NAVY = '14477E', INK = '0B2949', ORANGE = 'DC7B1E';
const BODY = '25384C', MUTED = '5A6E82', TINT = 'F1F5FA', LINE = 'D6E0EA';
const F = 'Arial';
const W = 13.33, H = 7.5, M = 0.62;

const png = f => {                       // width/height straight out of the IHDR
  const b = fs.readFileSync(path.join(A, f));
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
};
const shadow = () => ({ type: 'outer', color: '9FB3C8', blur: 12, offset: 3, angle: 90, opacity: 0.35 });

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.rtl = true;

const rtl = { fontFace: F, rtlMode: true, align: 'right', isTextBox: true };

// ---------------------------------------------------------------- slide shells
function dark(sub, title, note, o = {}) {
  const y = o.y !== undefined ? o.y : 2.85;
  const size = o.size || 54;
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addImage({ path: path.join(A, 'logo.png'), x: W - M - 1.7, y: M - 0.1, w: 1.7, h: 0.62 });
  if (sub) s.addText(sub, { ...rtl, x: M, y: y - 0.4, w: W - 2 * M, h: 0.4, fontSize: 20, color: '9EC5EE', bold: true });
  s.addText(title, { ...rtl, x: M, y, w: W - 2 * M, h: size / 45, fontSize: size, bold: true, color: 'FFFFFF' });
  if (note) s.addText(note, { ...rtl, x: M, y: y + size / 45 + 0.06, w: W - 2 * M, h: 0.9, fontSize: 20, color: 'BFD4E8' });
  return s;
}

function page(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addText(title, { ...rtl, x: M, y: 0.42, w: W - 2 * M, h: 0.72, fontSize: 34, bold: true, color: NAVY });
  if (kicker) s.addText(kicker, { ...rtl, x: M, y: 1.12, w: W - 2 * M, h: 0.42, fontSize: 16, color: MUTED });
  s.addText('מצפן זכויות איבה · הביטוח הלאומי, אגף שיקום', {
    ...rtl, x: M, y: H - 0.52, w: W - 2 * M, h: 0.3, fontSize: 10, color: 'A8B8C8',
  });
  return s;
}

// a screenshot, sized from its own pixels to fit a box
function shot(s, file, box) {
  const d = png(file);
  const ratio = d.w / d.h;
  let w = box.w, h = w / ratio;
  if (h > box.h) { h = box.h; w = h * ratio; }
  s.addImage({
    path: path.join(A, file), w, h,
    x: box.cx !== undefined ? box.cx - w / 2 : box.x + (box.w - w) / 2,
    y: box.y + (box.h - h) / 2,
  });
}

// numbered rows: the circle sits on the right, the words run left from it
function steps(s, items, o) {
  const { x, y, w, gap = 0.92, size = 16, dia = 0.44, color = NAVY } = o;
  items.forEach((it, i) => {
    const top = y + i * gap;
    s.addShape(pres.ShapeType.ellipse, {
      x: x + w - dia, y: top, w: dia, h: dia, fill: { color },
    });
    s.addText(String(i + 1), {
      x: x + w - dia, y: top, w: dia, h: dia, fontSize: 14, bold: true,
      color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, fontFace: F, isTextBox: true,
    });
    s.addText(it, {
      ...rtl, x, y: top - 0.06, w: w - dia - 0.18, h: 0.75, fontSize: size, color: BODY,
      valign: 'top', margin: 0,
    });
  });
}

function card(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1,
    fill: { color: o.fill || TINT }, line: { color: o.line || LINE, width: 1 },
  });
}

// ---------------------------------------------------------------- 1 · the cover
{
  const s = dark('הביטוח הלאומי · אגף שיקום', 'מצפן זכויות איבה',
    'כל הזכויות וההטבות שלך, במקום אחד באזור האישי.');
  s.addShape(pres.ShapeType.roundRect, {
    x: W - M - 2.55, y: 5.5, w: 2.55, h: 0.62, rectRadius: 0.31, fill: { color: NAVY },
  });
  s.addText('למשפחות שכולות', {
    x: W - M - 2.55, y: 5.5, w: 2.55, h: 0.62, fontSize: 18, bold: true, color: 'FFFFFF',
    align: 'center', valign: 'middle', fontFace: F, isTextBox: true, margin: 0,
  });
}

// ---------------------------------------------------------------- 2 · agenda
{
  const s = page('מה נעבור היום');
  steps(s, [
    'מה זה המצפן, ולמי הוא פתוח בשלב זה',
    'איך נכנסים אליו',
    'המסך הראשי — ארבעה אזורים',
    'דף ההטבה, הסטטוסים, והתמונה המלאה',
    'בקשה להטבה חדשה, ומה קורה אחרי שמגישים',
    'הגשת חשבונית או קבלה דרך המצפן',
    'שאלות ותשובות',
  ], { x: M, y: 1.85, w: 7.6, gap: 0.66, size: 17 });
  card(s, { x: 8.6, y: 1.85, w: W - M - 8.6, h: 4.6 });
  s.addText('הרעיון בשורה אחת', {
    ...rtl, x: 8.85, y: 2.15, w: W - M - 8.85 - 0.25, h: 0.4, fontSize: 15, bold: true, color: ORANGE,
  });
  s.addText('במקום לחפש מה מגיע לך, המצפן מציג את זה מראש — לפי הנתונים האישיים שלך, עם הסטטוס של כל הטבה ואפשרות להגיש בקשה או קבלה מאותו מקום.', {
    ...rtl, x: 8.85, y: 2.6, w: W - M - 8.85 - 0.25, h: 3.5, fontSize: 17, color: BODY, valign: 'top',
  });
}

// ---------------------------------------------------------------- 3 · what it is
{
  const s = page('מה זה מצפן הזכויות', 'ארבעה דברים שאפשר לעשות בו');
  const items = [
    ['לגלות', 'הטבות שאתה עשוי להיות זכאי להן, ולהגיש בקשה'],
    ['לעקוב', 'אחר כל בקשה שהגשת, ולראות את הסטטוס שלה'],
    ['לראות', 'כמה מימשת מכל הטבה וכמה נותר לך'],
    ['להגיש', 'חשבוניות וקבלות להחזר, ישירות מהמצפן'],
  ];
  items.forEach((it, i) => {
    const x = M + (3 - i % 4) * 0; // laid out below
    const col = i % 2, row = Math.floor(i / 2);
    const cw = (W - 2 * M - 0.4) / 2, ch = 1.95;
    const cx = M + (1 - col) * (cw + 0.4), cy = 1.9 + row * (ch + 0.35);
    card(s, { x: cx, y: cy, w: cw, h: ch, fill: 'FFFFFF', line: LINE });
    s.addShape(pres.ShapeType.ellipse, { x: cx + cw - 0.95, y: cy + 0.42, w: 0.62, h: 0.62, fill: { color: NAVY } });
    s.addText(String(i + 1), {
      x: cx + cw - 0.95, y: cy + 0.42, w: 0.62, h: 0.62, fontSize: 20, bold: true, color: 'FFFFFF',
      align: 'center', valign: 'middle', margin: 0, fontFace: F, isTextBox: true,
    });
    s.addText(it[0], { ...rtl, x: cx + 0.3, y: cy + 0.34, w: cw - 1.4, h: 0.45, fontSize: 22, bold: true, color: NAVY });
    s.addText(it[1], { ...rtl, x: cx + 0.3, y: cy + 0.85, w: cw - 1.4, h: 0.9, fontSize: 16, color: BODY, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 4 · who sees it
{
  const s = page('למי המצפן פתוח בשלב זה');
  card(s, { x: M, y: 1.9, w: W - 2 * M, h: 1.75, fill: NAVY, line: NAVY });
  s.addText('בשלב זה — למשפחות שכולות בלבד', {
    x: M, y: 1.9, w: W - 2 * M, h: 1.75, fontSize: 38, bold: true, color: 'FFFFFF',
    align: 'center', valign: 'middle', fontFace: F, isTextBox: true, rtlMode: true, margin: 0,
  });
  const rows = [
    ['בהמשך', 'המצפן ייפתח לאוכלוסיות נוספות, ובהן נכי פעולות איבה.'],
    ['ילדים קטינים', 'הורה שמקבל הטבות עבור ילדיו רואה אותן בתוך המצפן שלו, באזור "הצגת הטבות עבור".'],
    ['אם לא רואים', 'מי ששייך לקבוצה ועדיין לא רואה את המצפן — מוזמן לפנות אלינו.'],
  ];
  rows.forEach((r, i) => {
    const y = 4.1 + i * 0.92;
    s.addText(r[0], { ...rtl, x: W - M - 2.4, y, w: 2.4, h: 0.45, fontSize: 17, bold: true, color: ORANGE });
    s.addText(r[1], { ...rtl, x: M, y, w: W - 2 * M - 2.7, h: 0.75, fontSize: 17, color: BODY, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 5 · getting in
{
  const s = page('איך נכנסים', 'שלושה מסכים, ואתם בפנים');
  steps(s, [
    'נכנסים לאזור האישי באתר הביטוח הלאומי.',
    'בתפריט הצד בוחרים "מצפן הזכויות שלי", ואז "כניסה למצפן הזכויות".',
    'בעמוד שנפתח לוחצים על הכפתור הכחול.',
  ], { x: M, y: 2.0, w: 4.9, gap: 1.0, size: 17 });
  card(s, { x: M, y: 5.15, w: 4.9, h: 1.25 });
  s.addText('הכתובת: ps.btl.gov.il', {
    x: M + 0.25, y: 5.35, w: 4.4, h: 0.4, fontSize: 17, bold: true, color: NAVY,
    align: 'right', fontFace: F, isTextBox: true, margin: 0,
  });
  s.addText('אותו אזור אישי שכבר מוכר לכם — המצפן יושב בתוכו.', {
    ...rtl, x: M + 0.25, y: 5.75, w: 4.4, h: 0.5, fontSize: 14, color: MUTED,
  });
  shot(s, 'entry.png', { x: 6.1, y: 1.75, w: W - M - 6.1, h: 4.9 });
}

// ---------------------------------------------------------------- 6 · main screen
{
  const s = page('המסך הראשי', 'ארבעה אזורים — וזה המסך שנחזור אליו בכל פעם');
  shot(s, 'zones.png', { x: M, y: 1.65, w: 8.15, h: 5.05 });
  const zones = [
    ['1', 'הצגת הטבות עבור', 'בוחרים עבור מי להציג. מופיע רק להורים לילדים קטינים.', 'E8842B'],
    ['2', 'חיפוש', 'לפי שם ההטבה או לפי נושא — דיור, רכב, טיפול רפואי.', '2E9E4F'],
    ['3', 'ההטבות שלי', 'מה שכבר ביקשת, או שכבר אושר לך.', '8E3BB5'],
    ['4', 'ההטבות הפוטנציאליות', 'כל ההטבות שאתה עשוי להיות זכאי להן.', '2A9BD6'],
  ];
  zones.forEach((z, i) => {
    const y = 1.75 + i * 1.24;
    const x = 9.0, w = W - M - 9.0;
    s.addShape(pres.ShapeType.ellipse, { x: x + w - 0.42, y, w: 0.42, h: 0.42, fill: { color: z[3] } });
    s.addText(z[0], {
      x: x + w - 0.42, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: 'FFFFFF',
      align: 'center', valign: 'middle', margin: 0, fontFace: F, isTextBox: true,
    });
    s.addText(z[1], { ...rtl, x, y: y - 0.02, w: w - 0.58, h: 0.35, fontSize: 16, bold: true, color: NAVY });
    s.addText(z[2], { ...rtl, x, y: y + 0.33, w: w - 0.58, h: 0.85, fontSize: 13, color: MUTED, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 7 · my benefits
{
  const s = page('ההטבות שלי', 'מכאן נכנסים להטבה אחת ורואים מה קורה בה');
  shot(s, 'main.png', { x: 5.2, y: 1.7, w: W - M - 5.2, h: 4.9 });
  const rows = [
    ['מה מופיע כאן', 'כל ההטבות שכבר ביקשת, או שכבר אושרו לך.'],
    ['לחיצה על הטבה', 'פותחת את דף ההטבה שלה, עם הסטטוס והפרטים.'],
    ['אם ריק', 'המצפן מציג הטבות מהשנתיים האחרונות. אז כדאי לבדוק את ההטבות הפוטנציאליות.'],
  ];
  rows.forEach((r, i) => {
    const y = 2.0 + i * 1.45;
    s.addText(r[0], { ...rtl, x: M, y, w: 4.3, h: 0.4, fontSize: 18, bold: true, color: ORANGE });
    s.addText(r[1], { ...rtl, x: M, y: y + 0.42, w: 4.3, h: 1.0, fontSize: 16, color: BODY, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 8 · benefit page
{
  const s = page('דף ההטבה', 'אותו מבנה בכל הטבה, כך שתמיד יודעים איפה להסתכל');
  shot(s, 'benefit.png', { x: M, y: 1.7, w: 7.7, h: 4.9 });
  steps(s, [
    'שם ההטבה והקטגוריה, בראש הדף.',
    'תיבת ההסבר — מה ההטבה נותנת, כמה, ובאיזה תנאי.',
    'שורת ההטבה: הסטטוס, הסכום, תקופת הזכאות.',
    '"פרטים נוספים" פותח את התמונה המלאה.',
  ], { x: 8.55, y: 2.0, w: W - M - 8.55, gap: 1.0, size: 15 });
}

// ---------------------------------------------------------------- 9 · statuses
{
  const s = page('חמישה סטטוסים', 'הסטטוס אומר מה מצב ההטבה, ומה אפשר לעשות בה');
  const st = [
    ['בטיפול', '8A5B00', 'FFF1CF', 'הגשת בקשה ועדיין לא התקבלה החלטה. אין צורך להגיש שוב.'],
    ['פעילה', '1F6E43', 'E3F3E9', 'ההטבה אושרה, התקופה לא חלפה ויש בה יתרה. אפשר להגיש קבלות.'],
    ['הסתיימה', '4E5F72', 'E8EEF4', 'נוצלה במלואה, או שתקופת הזכאות חלפה. אי אפשר להגיש בה קבלות.'],
    ['נדחתה', 'A8281F', 'FBE8E6', 'הבקשה נדחתה. סיבת הדחייה מופיעה על כרטיס ההטבה.'],
    ['פוטנציאלי', '5E3A94', 'EFE8F8', 'עדיין לא ביקשת וייתכן שאתה זכאי. אפשר להגיש בקשה.'],
  ];
  st.forEach((r, i) => {
    const y = 1.85 + i * 1.02;
    card(s, { x: M, y, w: W - 2 * M, h: 0.86, fill: 'FFFFFF', line: LINE });
    s.addShape(pres.ShapeType.roundRect, {
      x: W - M - 2.3, y: y + 0.19, w: 1.95, h: 0.48, rectRadius: 0.24, fill: { color: r[2] },
    });
    s.addText(r[0], {
      x: W - M - 2.3, y: y + 0.19, w: 1.95, h: 0.48, fontSize: 16, bold: true, color: r[1],
      align: 'center', valign: 'middle', margin: 0, fontFace: F, isTextBox: true, rtlMode: true,
    });
    s.addText(r[3], {
      ...rtl, x: M + 0.3, y: y + 0.19, w: W - 2 * M - 2.9, h: 0.48, fontSize: 16, color: BODY, valign: 'middle',
    });
  });
}

// ---------------------------------------------------------------- 10 · full picture
{
  const s = page('התמונה המלאה של ההטבה', 'הכול על הטבה אחת, במסך אחד');
  shot(s, 'details.png', { x: 6.6, y: 1.65, w: W - M - 6.6, h: 5.0 });
  steps(s, [
    'פרטי ההטבה — הסטטוס, תקופת הזכאות, הסכום וסוג התשלום.',
    'סיכום מימוש — כמה כבר שולם, וכמה נותר לממש.',
    'הכפתור הכחול — להגשת חשבונית או קבלה חדשה.',
    'בקשות להחזר — כל קבלה שהגשת, והסטטוס שלה.',
  ], { x: M, y: 1.95, w: 5.6, gap: 1.12, size: 16 });
}

// ---------------------------------------------------------------- 11 · potential
{
  const s = page('ההטבות הפוטנציאליות', 'מה שעדיין לא ביקשת, ואולי מגיע לך');
  shot(s, 'potential.png', { x: M, y: 1.65, w: W - 2 * M, h: 2.75 });
  s.addText('לכל מבוטח רשימה אחרת, לפי הנתונים האישיים שלו. בכל הטבה מופיע אחד משני הכפתורים — וכל אחד פותח מסך אחר:', {
    ...rtl, x: M, y: 4.5, w: W - 2 * M, h: 0.5, fontSize: 17, color: BODY,
  });
  const cw = (W - 2 * M - 0.4) / 2;
  const routes = [
    ['הגשת בקשה', '1F7A4D', 'btn_request.png', 'בכרטיס כתוב "לבדיקת זכאות חדשה". נפתח טופס בקשה בן שלושה שלבים.'],
    ['שליחת פנייה', '6B3FA0', 'btn_inquiry.png', 'בכרטיס כתוב "אפשר לפנות לעובד השיקום". נפתחת פנייה לגורם המקצועי.'],
  ];
  routes.forEach((r, i) => {
    const x = M + (1 - i) * (cw + 0.4);
    card(s, { x, y: 5.1, w: cw, h: 1.35, fill: 'FFFFFF', line: r[1] });
    shot(s, r[2], { x: x + cw - 1.85, y: 5.3, w: 1.6, h: 0.5 });
    s.addText(r[3], { ...rtl, x: x + 0.28, y: 5.3, w: cw - 2.2, h: 1.0, fontSize: 15, color: BODY, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 12 · after
{
  const s = page('מה קורה אחרי שהגשת');
  const items = [
    ['הבקשה נקלטת', 'מופיעה הודעת אישור, והבקשה מופיעה במצפן.'],
    ['הסטטוס הוא "בטיפול"', 'ומתעדכן שם לבד. אין צורך לעשות דבר.'],
    ['בסיום', 'הסטטוס משתנה ל"אושרה" או ל"נדחתה", ובבקשות להחזר יופיע הסכום שאושר לתשלום.'],
  ];
  items.forEach((it, i) => {
    const cw = (W - 2 * M - 0.8) / 3;
    const x = M + (2 - i) * (cw + 0.4);
    card(s, { x, y: 2.1, w: cw, h: 3.4, fill: 'FFFFFF', line: LINE });
    s.addShape(pres.ShapeType.ellipse, { x: x + cw - 1.0, y: 2.45, w: 0.66, h: 0.66, fill: { color: NAVY } });
    s.addText(String(i + 1), {
      x: x + cw - 1.0, y: 2.45, w: 0.66, h: 0.66, fontSize: 22, bold: true, color: 'FFFFFF',
      align: 'center', valign: 'middle', margin: 0, fontFace: F, isTextBox: true,
    });
    s.addText(it[0], { ...rtl, x: x + 0.32, y: 3.35, w: cw - 0.64, h: 0.75, fontSize: 19, bold: true, color: NAVY, valign: 'top' });
    s.addText(it[1], { ...rtl, x: x + 0.32, y: 4.1, w: cw - 0.64, h: 1.2, fontSize: 15, color: BODY, valign: 'top' });
  });
  s.addText('הגשת בקשה אינה אישור אוטומטי. הזכאות נבדקת לפי הקריטריונים שנקבעו בחוק.', {
    ...rtl, x: M, y: 5.85, w: W - 2 * M, h: 0.5, fontSize: 16, bold: true, color: ORANGE, align: 'center',
  });
}

// ---------------------------------------------------------------- 13 · divider
dark('החלק השני', 'הגשת חשבונית או קבלה', 'למה דרך המצפן, מה אפשר דרכו, ואיפה מגישים כשאי אפשר.');

// ---------------------------------------------------------------- 14 · why
{
  const s = page('למה דווקא דרך המצפן');
  const items = [
    ['ישר לתיק שלך', 'ההגשה נכנסת להטבה הנכונה, בלי תחנת ביניים.'],
    ['רואים מה קרה', 'כל קבלה מופיעה עם התאריך, הסכום וסטטוס הטיפול בה.'],
    ['הכול במקום אחד', 'אפשר לצרף כמה חשבוניות לאותה בקשה, ולפתוח כל קבלה שהוגשה.'],
  ];
  items.forEach((it, i) => {
    const cw = (W - 2 * M - 0.8) / 3;
    const x = M + (2 - i) * (cw + 0.4);
    card(s, { x, y: 2.0, w: cw, h: 3.6, fill: 'FFFFFF', line: LINE });
    s.addText(it[0], { ...rtl, x: x + 0.32, y: 2.4, w: cw - 0.64, h: 0.9, fontSize: 22, bold: true, color: NAVY, valign: 'top' });
    s.addText(it[1], { ...rtl, x: x + 0.32, y: 3.4, w: cw - 0.64, h: 1.7, fontSize: 16, color: BODY, valign: 'top' });
  });
  s.addText('לעומת שליחה כללית של מסמך, שמגיעה לתיק ולא להטבה — ואי אפשר לעקוב אחריה מהמצפן.', {
    ...rtl, x: M, y: 5.9, w: W - 2 * M, h: 0.5, fontSize: 16, color: MUTED, align: 'center',
  });
}

// ---------------------------------------------------------------- 15 · what / where
{
  const s = page('מה אפשר דרך המצפן — ואיפה כן, כשאי אפשר');
  const cw = (W - 2 * M - 0.5) / 2;
  card(s, { x: M + cw + 0.5, y: 1.8, w: cw, h: 3.2, fill: 'FFFFFF', line: '1F7A4D' });
  s.addText('אפשר דרך המצפן', { ...rtl, x: M + cw + 0.8, y: 2.1, w: cw - 0.6, h: 0.5, fontSize: 22, bold: true, color: '1F7A4D' });
  s.addText([
    { text: 'בהטבה בסטטוס "פעילה" — הכפתור הכחול "להגשת חשבונית / קבלה חדשה".', options: { bullet: true, breakLine: true } },
    { text: 'בהטבה פוטנציאלית שבה מופיע הכפתור "הגשת בקשה".', options: { bullet: true, breakLine: true } },
    { text: 'כמה חשבוניות לאותה בקשה, בטופס אחד.', options: { bullet: true } },
  ], { ...rtl, x: M + cw + 0.8, y: 2.68, w: cw - 0.6, h: 2.2, fontSize: 16, color: BODY, valign: 'top', paraSpaceAfter: 10 });

  card(s, { x: M, y: 1.8, w: cw, h: 3.2, fill: 'FFFFFF', line: ORANGE });
  s.addText('כשאי אפשר — איפה כן', { ...rtl, x: M + 0.3, y: 2.1, w: cw - 0.6, h: 0.5, fontSize: 22, bold: true, color: ORANGE });
  s.addText([
    { text: 'בהטבה שהסתיימה או נדחתה אין כפתור הגשה.', options: { bullet: true, breakLine: true } },
    { text: 'בהטבה פוטנציאלית שבה כתוב "שליחת פנייה" — ההגשה אינה במצפן.', options: { bullet: true, breakLine: true } },
    { text: 'במקרים האלה מגישים דרך "העלאת מסמכים" באזור האישי — בשקף הבא.', options: { bullet: true } },
  ], { ...rtl, x: M + 0.3, y: 2.68, w: cw - 0.6, h: 2.2, fontSize: 16, color: BODY, valign: 'top', paraSpaceAfter: 10 });
}

// ---------------------------------------------------------------- 16 · upload
{
  const s = page('כשלא מופיע "הגשת בקשה"', 'ההגשה נעשית דרך "העלאת מסמכים" באזור האישי');
  shot(s, 'upload.png', { x: M, y: 1.75, w: 8.0, h: 4.85 });
  steps(s, [
    'בתפריט "פעולות באתר" — העלאת מסמכים.',
    'נושא: שיקום.',
    'קטגוריה: פניות.',
    'מסמך: פנייה.',
    'צרף קובץ — החשבונית או הקבלה.',
    'שלח מסמך.',
  ], { x: 8.85, y: 1.95, w: W - M - 8.85, gap: 0.72, size: 15 });
}

// ---------------------------------------------------------------- 17 · the form
{
  const s = page('טופס ההגשה', 'אותו טופס בשתי הדרכים — שלושה שלבים');
  const files = ['form1.png', 'form2.png', 'form3.png'];
  const caps = [
    ['שלב 1', 'בודקים את פרטי ההטבה ולוחצים "הבא".'],
    ['שלב 2', 'מצרפים את הקובץ, וממלאים מספר, תאריך וסכום כולל מע״מ.'],
    ['שלב 3', 'קוראים את ההצהרה, מסמנים, חותמים ושולחים.'],
  ];
  files.forEach((f, i) => {
    const cw = (W - 2 * M - 0.8) / 3;
    const x = M + (2 - i) * (cw + 0.4);
    shot(s, f, { x, y: 1.8, w: cw, h: 2.9 });
    s.addText(caps[i][0], { ...rtl, x, y: 4.9, w: cw, h: 0.4, fontSize: 20, bold: true, color: NAVY });
    s.addText(caps[i][1], { ...rtl, x, y: 5.32, w: cw, h: 1.1, fontSize: 15, color: BODY, valign: 'top' });
  });
}

// ---------------------------------------------------------------- 18 · Q&A divider
dark('', 'שאלות ותשובות', 'התשובות שלהלן הן אלה שחוזרות הכי הרבה.');

// ---------------------------------------------------------------- 19-21 · FAQ
const FAQ = [
  ['כניסה, ומה רואים', [
    ['אני לא מוצא את "מצפן הזכויות שלי" בתפריט. למה?',
      'בשלב זה המצפן מוצג רק למשפחות שכולות. בהמשך הוא ייפתח לאוכלוסיות נוספות. מי ששייך ועדיין לא רואה — מוזמן לפנות אלינו.'],
    ['אני רואה את המצפן אבל אין בו הטבות.',
      'המצפן מציג הטבות מהשנתיים האחרונות. אם לא הוגשו בקשות בתקופה זו, "ההטבות שלי" יהיה ריק — כדאי לבדוק את ההטבות הפוטנציאליות.'],
    ['הטבה שאני מקבל לא מופיעה במצפן. איבדתי אותה?',
      'לא. המצפן נבנה בהדרגה והטבות מתווספות אליו. הזכאות אינה תלויה במה שמוצג בו.'],
  ]],
  ['סטטוסים ומעקב', [
    ['מה ההבדל בין "פעילה" ל"הסתיימה"?',
      '"פעילה" היא הטבה מאושרת שנשארה בה יתרה, ואפשר להגיש בה קבלות. "הסתיימה" היא הטבה שנוצלה במלואה, או שתקופת הזכאות שלה חלפה.'],
    ['הבקשה שלי בסטטוס "בטיפול" כבר הרבה זמן.',
      '"בטיפול" אומר שהבקשה התקבלה ועדיין לא התקבלה בה החלטה. אין צורך להגיש שוב.'],
    ['איך יודעים כמה עוד נשאר לנצל?',
      'בדף ההטבה, באזור "סיכום מימוש", מופיע הסכום ששולם, מה שנותר, והסכום הכולל.'],
  ]],
  ['בקשות והגשות', [
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
    const y = 1.85 + i * 1.62;
    card(s, { x: M, y, w: W - 2 * M, h: 1.42, fill: 'FFFFFF', line: LINE });
    s.addText(q[0], { ...rtl, x: M + 0.32, y: y + 0.16, w: W - 2 * M - 0.64, h: 0.42, fontSize: 18, bold: true, color: NAVY });
    s.addText(q[1], { ...rtl, x: M + 0.32, y: y + 0.6, w: W - 2 * M - 0.64, h: 0.7, fontSize: 15, color: BODY, valign: 'top' });
  });
});

// ---------------------------------------------------------------- 22 · closing
{
  const s = dark('', 'מה יש למבוטחים', '', { y: 1.15, size: 44 });
  const items = [
    ['שני סרטוני הסבר', 'הסבר כללי (4 דקות), והגשת חשבונית או קבלה (3 דקות).'],
    ['שני מדריכים כתובים', 'גרסת A4 להדפסה, וגרסה לטלפון.'],
    ['שאלות ותשובות', 'רשימה מלאה, לעדכון לפי מה שיישאל בשטח.'],
  ];
  items.forEach((it, i) => {
    const y = 2.55 + i * 1.15;
    s.addText(it[0], { ...rtl, x: W - M - 4.6, y, w: 4.6, h: 0.42, fontSize: 20, bold: true, color: '9EC5EE' });
    s.addText(it[1], { ...rtl, x: 4.3, y: y + 0.05, w: W - M - 4.6 - 4.5, h: 0.8, fontSize: 15, color: 'CBDCEC', valign: 'top' });
  });
  s.addImage({ path: path.join(A, 'qr.png'), x: M, y: 2.7, w: 1.95, h: 1.95 });
  s.addText('ps.btl.gov.il', {
    x: M, y: 4.78, w: 1.95, h: 0.35, fontSize: 13, bold: true, color: 'FFFFFF',
    align: 'center', fontFace: F, isTextBox: true, margin: 0,
  });
  s.addText('תודה', { ...rtl, x: M, y: 6.05, w: W - 2 * M, h: 0.6, fontSize: 26, bold: true, color: 'FFFFFF', align: 'center' });
}

// ---------------------------------------------------------------- speaker notes
const NOTES = [
  'פתיחה. המצפן הוא אזור חדש בתוך האזור האישי, ובשלב זה הוא פתוח למשפחות שכולות בלבד. אפשר לפתוח באמירה שהמטרה היא שלא יצטרכו לחפש מה מגיע להם.',
  'סדר היום. החלק הגדול הוא היכרות עם המצפן; ההגשה של חשבוניות בסוף.',
  'ארבע היכולות. שווה להתעכב על "לגלות" — זה החידוש האמיתי מול המצב היום.',
  'למי הוא פתוח. חשוב לומר את זה במפורש, כדי שלא ייצא מישהו מהכנס ויחפש אצלו משהו שלא קיים.',
  'הכניסה. אותו אזור אישי מוכר; המצפן יושב בתוכו, בתפריט הצד.',
  'המסך הראשי. זה המסך שחוזרים אליו בכל פעם. ארבעת האזורים לפי הסדר.',
  'ההטבות שלי. מכאן נכנסים להטבה אחת. אם המסך ריק — לא בהכרח אין זכאות; המצפן מציג שנתיים אחורה.',
  'דף ההטבה. אותו מבנה בכל הטבה, כך שאחרי פעם אחת יודעים איפה להסתכל.',
  'הסטטוסים. זה השקף שהכי נשאלים עליו. שווה לעצור בו.',
  'התמונה המלאה. נפתחת מ"פרטים נוספים" בהטבה פעילה.',
  'ההטבות הפוטנציאליות. לכל אחד רשימה אחרת. שני הכפתורים — ההבדל ביניהם חוזר בשאלות.',
  'אחרי ההגשה. להדגיש: אין צורך להגיש שוב, ואין כאן אישור אוטומטי.',
  'מעבר לחלק השני — הגשת חשבונית או קבלה. חלק קצר.',
  'למה דרך המצפן. הנקודה המרכזית: ההגשה נכנסת להטבה הנכונה, ואפשר לעקוב.',
  'מה אפשר ומה לא. השקף הזה עונה מראש על "ניסיתי ולא הצלחתי".',
  'הדרך החלופית. שישה שלבים; שווה להראות את המסך.',
  'הטופס. אותם שלושה שלבים בשתי הדרכים.',
  'מעבר לשאלות ותשובות.',
  'שאלות על כניסה ועל מה שרואים.',
  'שאלות על סטטוסים ומעקב.',
  'שאלות על בקשות והגשות.',
  'סיום. להפנות לסרטונים ולמדריכים, ולהשאיר את ה-QR על המסך בזמן השאלות.',
];
(pres._slides || []).forEach((sl, i) => { if (NOTES[i]) sl.addNotes(NOTES[i]); });

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));
