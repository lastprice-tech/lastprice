#!/usr/bin/env python3
"""Minimal HWP 5.0 -> Markdown extractor (paragraphs + tables, headers/footers skipped).

Usage: python3 hwp2md.py input.hwp output.md
"""
import struct
import sys
import zlib

import olefile

TAG_BEGIN = 0x10
PARA_HEADER = TAG_BEGIN + 50
PARA_TEXT = TAG_BEGIN + 51
CTRL_HEADER = TAG_BEGIN + 55
LIST_HEADER = TAG_BEGIN + 56
TABLE = TAG_BEGIN + 61

EXT_CTRL = {1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}
INLINE_CTRL = {4, 5, 6, 7, 8, 19, 20}


def records(data):
    pos, n = 0, len(data)
    while pos + 4 <= n:
        (h,) = struct.unpack_from('<I', data, pos)
        pos += 4
        tag = h & 0x3FF
        level = (h >> 10) & 0x3FF
        size = (h >> 20) & 0xFFF
        if size == 0xFFF:
            (size,) = struct.unpack_from('<I', data, pos)
            pos += 4
        yield tag, level, data[pos:pos + size]
        pos += size


def decode_text(payload):
    units = struct.unpack('<%dH' % (len(payload) // 2), payload[: len(payload) // 2 * 2])
    out, i = [], 0
    while i < len(units):
        c = units[i]
        if c in EXT_CTRL or c in INLINE_CTRL:
            i += 8
            continue
        if c == 9:
            out.append(ord('\t'))
            i += 8
            continue
        if c == 10:
            out.append(ord('\n'))
        elif c == 13 or c == 0:
            pass
        elif c == 24:
            out.append(ord('-'))
        elif c in (30, 31):
            out.append(ord(' '))
        elif c < 32:
            pass
        else:
            out.append(c)
        i += 1
    b = struct.pack('<%dH' % len(out), *out)
    return b.decode('utf-16-le', errors='replace')


def ctrl_id(payload):
    if len(payload) < 4:
        return ''
    (v,) = struct.unpack_from('<I', payload, 0)
    return struct.pack('>I', v).decode('latin-1')


class Table:
    def __init__(self, level):
        self.level = level
        self.rows = self.cols = 0
        self.cells = {}  # (row, col) -> [texts]
        self.spans = {}
        self.cur = None

    def to_md(self):
        if not self.cells:
            return ''
        rows = self.rows or (max(r for r, _ in self.cells) + 1)
        cols = self.cols or (max(c for _, c in self.cells) + 1)
        grid = [['' for _ in range(cols)] for _ in range(rows)]
        for (r, c), texts in self.cells.items():
            if r < rows and c < cols:
                t = '<br>'.join(x.strip().replace('|', '\\|') for x in texts if x.strip())
                grid[r][c] = t.replace('\n', '<br>')
        lines = []
        for i, row in enumerate(grid):
            lines.append('| ' + ' | '.join(row) + ' |')
            if i == 0:
                lines.append('|' + '---|' * cols)
        return '\n'.join(lines)


def extract(path):
    ole = olefile.OleFileIO(path)
    header = ole.openstream('FileHeader').read()
    props = struct.unpack_from('<I', header, 36)[0]
    compressed = bool(props & 1)
    if props & 2:
        raise SystemExit('password protected')
    if props & 4:
        raise SystemExit('distribution document (ViewText) not supported')
    sections = sorted(
        ['/'.join(e) for e in ole.listdir() if e[0] == 'BodyText'],
        key=lambda s: int(s.split('Section')[-1]),
    )
    blocks = []  # list of (kind, payload)
    for sec in sections:
        data = ole.openstream(sec).read()
        if compressed:
            data = zlib.decompress(data, -15)
        stack = []  # contexts: dict(kind, level, table?)
        for tag, level, payload in records(data):
            # pop contexts that ended
            while stack and level <= stack[-1]['level']:
                ctx = stack.pop()
                if ctx['kind'] == 'tbl ':
                    md = ctx['table'].to_md()
                    target = stack_target(stack, blocks)
                    target.append(('table', md))
            if tag == CTRL_HEADER:
                cid = ctrl_id(payload)
                ctx = {'kind': cid, 'level': level}
                if cid == 'tbl ':
                    ctx['table'] = Table(level)
                stack.append(ctx)
            elif tag == TABLE and stack and stack[-1]['kind'] == 'tbl ':
                if len(payload) >= 8:
                    _, r, c = struct.unpack_from('<IHH', payload, 0)
                    stack[-1]['table'].rows, stack[-1]['table'].cols = r, c
            elif tag == LIST_HEADER and stack and stack[-1]['kind'] == 'tbl ':
                t = stack[-1]['table']
                if len(payload) >= 16:
                    col, row, cs, rs = struct.unpack_from('<HHHH', payload, 8)
                    t.cur = (row, col)
                    t.cells.setdefault((row, col), [])
            elif tag == PARA_TEXT:
                text = decode_text(payload)
                owner = innermost(stack)
                if owner is None:
                    blocks.append(('p', text))
                elif owner['kind'] in ('head', 'foot'):
                    continue
                elif owner['kind'] == 'tbl ':
                    t = owner['table']
                    if t.cur is not None:
                        t.cells[t.cur].append(text)
                elif owner['kind'] in ('fn  ', 'en  '):
                    blocks.append(('p', '(각주) ' + text))
                else:
                    blocks.append(('p', text))
        while stack:
            ctx = stack.pop()
            if ctx['kind'] == 'tbl ':
                stack_target(stack, blocks).append(('table', ctx['table'].to_md()))
    return blocks


def innermost(stack):
    return stack[-1] if stack else None


def stack_target(stack, blocks):
    # nested tables: flatten into the parent cell as text; top-level: blocks list
    for ctx in reversed(stack):
        if ctx['kind'] == 'tbl ':
            t = ctx['table']
            if t.cur is not None:
                class _Adapter(list):
                    def append(self_inner, item):
                        t.cells[t.cur].append('[내부표] ' + item[1].replace('\n', ' / '))
                return _Adapter()
    return blocks


def main():
    src, dst = sys.argv[1], sys.argv[2]
    blocks = extract(src)
    out = []
    for kind, payload in blocks:
        if kind == 'p':
            out.append(payload.rstrip())
        else:
            out.append('')
            out.append(payload)
            out.append('')
    text = '\n'.join(out)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    print(dst, len(text), 'chars', sum(1 for k, _ in blocks if k == 'table'), 'tables')


if __name__ == '__main__':
    main()
