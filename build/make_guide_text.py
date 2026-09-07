#!/usr/bin/env python3
"""Write the guides out as plain Markdown, straight from the page that was printed.

The PDF and the text file therefore say exactly the same thing: both are read
from build/out/<name> - דסקטופ.html, which make_guide.py has just written.

Usage: python3 build/make_guide_text.py
Output: content/מדריך ... .md
"""
import html
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'out')
DEST = os.path.join(ROOT, 'content')

NAMES = ['מדריך מצפן זכויות איבה', 'מדריך הגשת חשבונית או קבלה']
SKIP = {'style', 'script', 'head'}
DROP = ('bx', 'zn')          # the numbers painted on a screenshot travel with the picture


class ToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, classes)
        self.out = []            # finished lines
        self.buf = []            # text of the block being read
        self.skip = 0
        self.step = 0
        self.dropped = []

    # -- helpers ---------------------------------------------------------
    def has(self, cls):
        return any(cls in c for _, c in self.stack)

    def flush(self, prefix='', suffix=''):
        text = re.sub(r'[ \t\r\n]+', ' ', ''.join(self.buf)).strip()
        text = re.sub(r' ?\x00 ?', '  \n', text).strip()
        self.buf = []
        if text:
            self.out.append(prefix + text + suffix)
            self.out.append('')

    # -- parsing ---------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        a = dict(attrs)
        cls = a.get('class', '')
        if any(c in cls.split() for c in DROP):
            self.skip += 1
            self.dropped.append(tag)
            return
        self.stack.append((tag, cls))

        if tag in ('b', 'strong'):
            self.buf.append('**')
        elif tag == 'span' and 'url' in cls:
            self.buf.append('\x00')
        elif tag == 'ol' and 'steps' in cls:
            self.step = 0
        elif tag == 'tr':
            self.buf.append('| ')
        elif tag == 'td':
            pass

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.dropped and self.dropped[-1] == tag:
            self.dropped.pop()
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        cls = ''
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                cls = self.stack[i][1]
                del self.stack[i:]
                break

        if tag in ('b', 'strong'):
            self.buf.append('**')
        elif tag == 'h1':
            self.flush('# ')
        elif tag == 'h2':
            text = ' '.join(''.join(self.buf).split())
            self.buf = []
            m = re.match(r'^(\d+)\s+(.*)$', text)
            self.out += [f'## {m.group(1)}. {m.group(2)}' if m else f'## {text}', '']
        elif tag == 'h3':
            self.flush('### ')
        elif tag == 'li':
            if self.has('steps'):
                self.step += 1
                self.flush(f'{self.step}. ')
            else:
                self.flush('- ')
        elif tag == 'dt':
            self.flush('**', '**')
        elif tag == 'dd':
            self.flush()
        elif tag == 'td':
            self.buf.append(' | ')
        elif tag == 'tr':
            self.flush('', '|')
        elif tag == 'figcaption':
            self.flush('_תמונה: ', '_')
        elif tag == 'p':
            if 'sub' in cls:
                self.flush('*', '*')
            elif self.has('note'):
                self.flush('> ')
            elif self.has('route'):
                self.flush('- ')
            else:
                self.flush()
        elif tag == 'div':
            if 'note' in cls:
                self.flush('> ')
            elif 'qr' in cls:
                self.flush('', '')
            elif 'foot' in cls:
                self.flush('*', '*')
            else:
                self.flush()
        elif tag == 'span' and 'url' in cls:
            self.buf.append('\x00')
        elif tag == 'section':
            self.flush()
            self.out.append('---')
            self.out.append('')

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def convert(name):
    src = os.path.join(OUT, f'{name} - דסקטופ.html')
    page = open(src, encoding='utf-8').read()
    page = re.sub(r'<img[^>]*>', '', page)          # the pictures do not travel as text
    page = re.sub(r'<style.*?</style>', '', page, flags=re.S)
    p = ToMarkdown()
    p.feed(page)
    p.flush()
    lines, blank = [], True
    for line in p.out:                              # no runs of empty lines
        if line == '' and blank:
            continue
        blank = line == ''
        lines.append(line)
    while lines and lines[-1] in ('', '---'):
        lines.pop()
    body = '\n'.join(lines).replace('****', '')
    dest = os.path.join(DEST, f'{name}.md')
    open(dest, 'w', encoding='utf-8').write('<div dir="rtl">\n\n' + body + '\n\n</div>\n')
    print('wrote', os.path.relpath(dest, ROOT), f'{len(body)} chars')


if __name__ == '__main__':
    for n in NAMES:
        convert(n)
