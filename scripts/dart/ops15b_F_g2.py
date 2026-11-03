"""15차 확장 작업 F·F-2·F-3 그룹 g2(메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주) 생성기.

실행: python3 scripts/dart/ops15b_F_g2.py  (인자 없음; 네트워크 안 씀 — 이미 있는 글만 읽음)
산출: dart_out/ops15/조각/F_g2.csv·F2_g2.csv·F3_g2.csv·확인_F_g2.csv, dart_out/ops15/원문/F·F2·F3/<g2 회사>__…md,
      dart_out/ops15/문서목록15b_F_g2.csv

원문(출처 텍스트) 정의 — 검증기(verify15b_F_g2.py)도 같은 정의로 따로 읽음:
- 사업보고서(OpenDART XML md, dart_out/text/ops15/사업보고서__…md): md 머리(첫 「### [절」 앞)는 버림.
  「### [절 n] 제목」 줄은 「제목」만 남기고, 「[표 n]」「[표 끝]」 줄(변환 표지)은 지움.
  대조 때는 공백·줄바꿈에 더해 md 표지 「|」「<br>」를 양쪽에서 지움(COMMON15b 대조 규칙).
- 연차보고서 FY2023(dart_out/text/ops15/연차보고서__<회사>__2024__<유형>.md, PDF 글): 머리(첫 「## p.N」 앞) 버림, 「## p.N」 줄은 쪽 표지.
- 연차보고서 FY2024·FY2025(dart_out/ops15/kit56/연차보고서_섹션.csv, 6차 섹션): 같은 파일의 섹션 본문을 섹션순번·chunk_seq 순으로 이은 글.
  page = 그 글이 든 섹션의 시작페이지.
- 표시용 글: 줄마다 공백 연속을 한 칸으로, 앞뒤 공백·빈 줄 지움(공백만 바뀜 — 대조는 공백·줄바꿈을 지우고 봄).

분류 칸 기준(기계적):
- function_kw: REQUEST15b 작업 F 키워드 중 body_name·source_text 에 든 낱말(공백 지우고 찾음; AI·IT 는 앞뒤가 영문자가 아닐 때만), 「, 」로.
- subsidiary_related: agenda_list_text(공백 지움)에 「자회사」「그룹」「계열사」 중 하나가 있으면 Y, 없으면 N(「문서에 없음」 행은 「문서에 없음」).
- held_count: 원문 횟수 글(note 에 원문) 또는 개최 내역 표의 개최일 수(note 「(판단)」).

검증(verify15b_F_g2.py, 2026-11-03) 때 고친 것 — 다시 돌려도 같은 결과:
- 기준 칸(source_text·agenda_list_text·unit_name)과 다른 위치에서 온 같은 문서의 칸은 note 「<칸> 위치 <위치>」(add_locnotes).
- F 행 더함: JB 사업보고서 Ⅵ 준법지원인 활동 표 「내부통제 관련 회의체 운영」 행 묶음(FY2023~2025), JB 「그룹 리스크RM 실무협의회」(FY2023·2024),
  iM 「집행위원회」(FY2023~2025), 메리츠 「내부통제위원회」(사업보고서 Ⅵ 준법감시인 활동 표, FY2023·2024) — note 「(검증 때 더한 행)」.
- iM 위험관리협의회 chair_text: 구성 표 비고 「의장」 행 글. F-2 established: 연차보고서 첨부 정관(등) 위원회 목록 「…(신설 날짜)」(EST).
- F-2 FY2024 내부통제위원회 「문서에 없음」 행 note 에 찾은 범위·조항 신설 글, F-3 「문서에 없음」 행 note 에 iM·JB 관련 글(사실만).
"""
import csv, os, re, bisect, sys
from datetime import datetime, timezone, timedelta

csv.field_size_limit(10**9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KST = timezone(timedelta(hours=9))
G2 = ['메리츠금융지주', 'iM금융지주', 'BNK금융지주', 'JB금융지주', '한국투자금융지주']
NA = '문서에 없음'
OUT = f'{ROOT}/dart_out/ops15'

_cache = {}


CTRL_RX = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]')
CTRL_COUNT = {}


def _norm_lines(lines, key=None):
    out = []
    for ln in lines:
        n = len(CTRL_RX.findall(ln))
        if n:
            ln = CTRL_RX.sub('', ln)  # 보이지 않는 제어문자만 지움(COMMON15b) — 행 note 「제어문자 지움」
            if key:
                CTRL_COUNT[key] = CTRL_COUNT.get(key, 0) + n
        s = re.sub(r'[ \t\u00a0\u3000]+', ' ', ln).strip()
        if s:
            out.append(s)
    return out


def cmpnorm(t, xml=False):
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return re.sub(r'\s+', '', t)


class Doc:
    """display: 표시용 글, marks: [(display_offset, label)] 쪽/절 표지."""

    def __init__(self, did, kind, corp, fy, doc_kind, doc_name, ref, collected_at, path, display, marks, xml=False, extra=None):
        self.id, self.kind, self.corp, self.fy = did, kind, corp, fy
        self.doc_kind, self.doc_name, self.ref, self.collected_at, self.path = doc_kind, doc_name, ref, collected_at, path
        self.display, self.marks, self.xml = display, marks, xml
        self.extra = extra or {}
        idx, chars = [], []
        for i, c in enumerate(display):
            if not c.isspace():
                idx.append(i)
                chars.append(c)
        self.stripped = ''.join(chars)
        self.smap = idx
        self.mark_pos = [m[0] for m in marks]

    def label_at(self, pos):
        k = bisect.bisect_right(self.mark_pos, pos) - 1
        return self.marks[k][1] if k >= 0 else ''

    def find(self, s, after=0):
        """공백 무시 찾기 → display 시작 위치(없으면 -1). after = display 위치."""
        ss = re.sub(r'\s+', '', s)
        sa = bisect.bisect_left(self.smap, after)
        p = self.stripped.find(ss, sa)
        return -1 if p < 0 else self.smap[p]

    def count(self, s):
        return self.stripped.count(re.sub(r'\s+', '', s))

    def grab(self, start, end=None, after=None, upto=None, occ=0):
        """start(포함)~end(포함) 이어진 글. upto 를 주면 upto 앞까지(미포함). after = 이 글 뒤에서 찾기(목록이면 차례로)."""
        a0 = 0
        if after:
            for aa in (after if isinstance(after, (list, tuple)) else [after]):
                q = self.find(aa, a0)
                if q < 0:
                    raise ValueError(f'{self.id}: after 못 찾음 {aa!r}')
                a0 = q + 1
        p = self.find(start, a0)
        for _ in range(occ):
            p = self.find(start, p + 1)
        if p < 0:
            raise ValueError(f'{self.id}: start 못 찾음 {start!r}')
        if end is None and upto is None:
            ss = re.sub(r'\s+', '', start)
            si = bisect.bisect_left(self.smap, p)
            e = self.smap[si + len(ss) - 1] + 1
        elif upto is not None:
            q = self.find(upto, p + 1)
            if q < 0:
                raise ValueError(f'{self.id}: upto 못 찾음 {upto!r}')
            e = q
        else:
            ss = re.sub(r'\s+', '', end)
            q = self.find(end, p)
            if q < 0:
                raise ValueError(f'{self.id}: end 못 찾음 {end!r}')
            si = bisect.bisect_left(self.smap, q)
            e = self.smap[si + len(ss) - 1] + 1
        txt = self.display[p:e].strip()
        return txt, p, e

    def page(self, p, e):
        a, b = self.label_at(p), self.label_at(max(p, e - 1))
        if self.kind in ('AR_md', 'AR_kit'):
            return f'p.{a}' if a == b else f'p.{a}~{b}'
        return a if a == b else f'{a} ~ {b}'


def to_kst(s):
    s = (s or '').strip()
    if not s:
        return ''
    if s.endswith('+0000'):
        d = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S+0000').replace(tzinfo=timezone.utc)
        return d.astimezone(KST).isoformat()
    return s


def br_rows():
    if 'br_rows' not in _cache:
        _cache['br_rows'] = list(csv.DictReader(open(f'{OUT}/사업보고서_원문.csv', encoding='utf-8-sig')))
    return _cache['br_rows']


def load_br(rcept):
    key = 'BR:' + rcept
    if key in _cache:
        return _cache[key]
    x = [r for r in br_rows() if r['rcept_no'] == rcept][0]
    lines = open(f"{ROOT}/{x['text_path']}", encoding='utf-8').read().split('\n')
    disp, marks, sec_starts = [], [], []
    off = 0
    cur_sec, started = '', False
    for ln in lines:
        m = re.match(r'^### \[절 (\d+)\] ?(.*)$', ln)
        if m:
            started = True
            cur_sec = f'XML [절 {m.group(1)}] 「{m.group(2).strip()}」'
            marks.append((off, cur_sec))
            sec_starts.append(off)
            ln = m.group(2)
        elif not started:
            continue
        else:
            mt = re.match(r'^\[표 (\d+)\]\s*$', ln.strip())
            if mt:
                marks.append((off, cur_sec + f' [표 {mt.group(1)}]'))
                continue
            if ln.strip() == '[표 끝]':
                marks.append((off, cur_sec))
                continue
        s = _norm_lines([ln], key)
        if s:
            disp.append(s[0])
            off += len(s[0]) + 1
    d = Doc(key, 'BR', x['label'], int(x['fy']), '사업보고서', x['report_nm'], x['rcept_no'], x['fetched_at'],
            x['text_path'], '\n'.join(disp), marks, xml=True,
            extra=dict(kind=x['kind'], rcept_dt=x['rcept_dt'], raw_path=x['raw_path'], sha=x['raw_sha256'], sec_starts=sec_starts))
    _cache[key] = d
    return d


def br_id(corp, fy, kind='본'):
    for r in br_rows():
        if r['label'] == corp and r['fy'] == str(fy) and r['kind'] == kind:
            return r['rcept_no']
    return None


def ar_list():
    if 'arl' not in _cache:
        rows = []
        for g in ('g1', 'g2'):
            p = f'{OUT}/연차보고서15_목록_{g}.csv'
            if os.path.exists(p):
                rows += list(csv.DictReader(open(p, encoding='utf-8-sig')))
        _cache['arl'] = rows
    return _cache['arl']


def kit_files():
    if 'kitf' not in _cache:
        _cache['kitf'] = list(csv.DictReader(open(f'{ROOT}/handoff/연차보고서_파일목록.csv', encoding='utf-8-sig')))
    return _cache['kitf']


def kit_rows():
    if 'kit' not in _cache:
        _cache['kit'] = list(csv.DictReader(open(f'{OUT}/kit56/연차보고서_섹션.csv', encoding='utf-8-sig')))
    return _cache['kit']


def gov_old_rows():
    if 'gov_old' not in _cache:
        p = f'{OUT}/문서목록15b_gov_old.csv'
        _cache['gov_old'] = list(csv.DictReader(open(p, encoding='utf-8-sig'))) if os.path.exists(p) else []
    return _cache['gov_old']


def kit_ref(meta):
    """6차 파일 URL. 같은 URL(POST 내려받기)이 여러 파일이면 gov_old 목록에서 sha256 이 같은 행의 URL(POST 값 포함)을 씀."""
    url = meta['url']
    if sum(1 for r in kit_files() if r['url'] == url and '지배구조' in r['파일명']) <= 1:
        return url
    for r in gov_old_rows():
        if r.get('sha256') == meta['sha256'] and r.get('rcept_no_or_url', '').startswith(url):
            return r['rcept_no_or_url']
    return f"{url} (파일명 {meta['파일명']})"


def load_ar(corp, year, typ='본공시'):
    """year = 공시연도(FY+1)."""
    key = f'AR:{corp}:{year}:{typ}'
    if key in _cache:
        return _cache[key]
    year = int(year)
    if year <= 2024:
        path = f'dart_out/text/ops15/연차보고서__{corp}__{year}__{typ}.md'
        lines = open(f'{ROOT}/{path}', encoding='utf-8').read().split('\n')
        disp, marks, off, started = [], [], 0, False
        for ln in lines:
            m = re.match(r'^## p\.(\d+)(\s.*)?$', ln)
            if m:
                started = True
                marks.append((off, m.group(1)))
                continue
            if not started:
                continue
            s = _norm_lines([ln], key)
            if s:
                disp.append(s[0])
                off += len(s[0]) + 1
        meta = [r for r in ar_list() if r['회사'] == corp and r['공시연도'] == str(year) and r['공시유형'] == typ][0]
        url = meta['파일_url'].split(' (')[0]
        if sum(1 for r in ar_list() if r['파일_url'].split(' (')[0] == url) > 1:
            url = meta['파일_url']  # 같은 URL(POST)이 여러 파일 — POST 값까지 적어 구분
        d = Doc(key, 'AR_md', corp, year - 1, '지배구조 및 보수체계 연차보고서', meta['제목'], url, meta['fetched_at'], path,
                '\n'.join(disp), marks, extra=dict(rcept_dt=meta['공시일'], sha=meta['sha256'], raw_url_note=meta['파일_url']))
    else:
        rows = [r for r in kit_rows() if r['지주명'] == corp and r['공시연도'] == str(year) and r['공시유형'] == typ and '지배구조' in r['파일명']]
        rows.sort(key=lambda r: (int(r['섹션순번']), int(r['chunk_seq'])))
        fname = rows[0]['파일명']
        meta = [r for r in kit_files() if r['파일명'] == fname][0]
        disp, marks, off, secmarks, parent = [], [], 0, [], ''
        for r in rows:
            if re.match(r'^\d+\.$', r['섹션번호'].strip()) or r['섹션번호'].startswith('제'):
                parent = f"{r['섹션번호']} {r['섹션제목_원문']}"
            body = r['본문']
            if not body:
                continue
            marks.append((off, r['시작페이지'] or '?'))
            st = f"{r['섹션번호']} {r['섹션제목_원문']}".strip()
            secmarks.append((off, parent or st))
            for s in _norm_lines(body.split('\n'), key):
                disp.append(s)
                off += len(s) + 1
        d = Doc(key, 'AR_kit', corp, year - 1, '지배구조 및 보수체계 연차보고서', meta['제목'], kit_ref(meta), to_kst(meta['fetched_at']),
                f'dart_out/ops15/kit56/연차보고서_섹션.csv (파일명 {fname})', '\n'.join(disp), marks,
                extra=dict(sha=meta['sha256'], fname=fname, rcept_dt=meta.get('공시일', '')))
        sp = [m[0] for m in secmarks]
        d.extra['sec_at'] = lambda q: secmarks[max(0, bisect.bisect_right(sp, q) - 1)][1] if secmarks else ''
    _cache[key] = d
    return d


def doc_by_ref(ref):
    """rcept_no 또는 URL → Doc."""
    if re.fullmatch(r'\d{14}', ref):
        return load_br(ref)
    for r in ar_list():
        if r['파일_url'] == ref or r['파일_url'].split(' (')[0] == ref:
            d = load_ar(r['회사'], r['공시연도'], r['공시유형'])
            if d.ref == ref:
                return d
    for r in kit_files():
        if ref.startswith(r['url']) and '지배구조' in r['파일명']:
            d = load_ar(r['지주명'], r['공시연도'], r['공시유형'])
            if d.ref == ref:
                return d
    raise KeyError(ref)


# ───────────────────────── 생성 공용 ─────────────────────────
KW_F = ['협의회', '협의체', '회의체', '위원회', '그룹', '리스크', '내부통제', '준법', '감사', '소비자보호', 'ESG', '디지털', 'AI', 'IT',
        '정보보호', '브랜드', '시너지', '개최', '분기', '매월']


def function_kw(*texts):
    t = re.sub(r'\s+', '', ' '.join(texts))
    out = []
    for k in KW_F:
        if k in ('AI', 'IT'):
            if re.search(r'(?<![A-Za-z])' + k + r'(?![A-Za-z])', t):
                out.append(k)
        elif k in t:
            out.append(k)
    return ', '.join(out)


def get_doc(spec_doc, corp):
    """('AR', 공시연도[, 유형]) | ('BR', fy[, kind]) | rcept_no 문자열."""
    if isinstance(spec_doc, str):
        return load_br(spec_doc)
    if spec_doc[0] == 'AR':
        return load_ar(corp, spec_doc[1], spec_doc[2] if len(spec_doc) > 2 else '본공시')
    if spec_doc[0] == 'BR':
        return load_br(br_id(corp, spec_doc[1], spec_doc[2] if len(spec_doc) > 2 else '본'))
    raise ValueError(spec_doc)


SPANS = {}


def add_span(task, corp, fy, doc, p, e):
    SPANS.setdefault((task, corp, fy, doc.id), (doc, []))[1].append((p, e))


def S(s, e=None, **kw):
    d = dict(s=s)
    if e is not None:
        d['e'] = e
    d.update(kw)
    return d


def field(f, corp, default_doc, task, fy, notes, fname):
    """f: None → 문서에 없음 / S(...) dict / ('lit', 값)."""
    if f is None:
        return NA, None
    if isinstance(f, tuple) and f[0] == 'lit':
        return f[1], None
    d = get_doc(f['doc'], corp) if 'doc' in f else default_doc
    if 'block' in f:
        txt, p, e = table_block(d, f['block'], f['after'], f['upto'], f['hdr'] if 'hdr' in f else '위원회명 | 개최일자')
        add_span(task, corp, fy, d, p, e)
        return txt, (d, p, e)
    if 'row' in f:
        txt, p, e = table_row(d, f['row'], f.get('after'), f.get('ncell', 3), f.get('first', 0))
        add_span(task, corp, fy, d, p, e)
        notes.append(f'{fname} 위치 {d.page(p, e)}' if d is default_doc else f'{fname} 는 {d.doc_kind} {d.ref} {d.page(p, e)}')
        return txt, (d, p, e)
    txt, p, e = d.grab(f['s'], f.get('e'), after=f.get('after'), upto=f.get('upto'), occ=f.get('occ', 0))
    if f.get('trim', True) and f.get('upto'):
        txt = re.sub(r'(\s*(\d{1,3}\.?|[가-하]\.|\(\d+\)|[가-하]\)|\d+\)|\|))+\s*$', '', txt)
    if len(txt) > f.get('max', {'chair_text': 1500, 'cadence_text': 1500, 'members_text': 6000, 'source_text': 6000, 'established': 400,
                                 'concurrent_or_dispatched': 800, 'unit_name': 200, 'function': 200, 'headcount': 200}.get(fname, 30000)):
        raise ValueError(f'{fname} 너무 김 {len(txt)}')
    add_span(task, corp, fy, d, p, e)
    if d is not default_doc:
        notes.append(f'{fname} 는 {d.doc_kind} {d.ref} {d.page(p, e)}')
    elif f.get('locnote'):
        notes.append(f'{fname} 위치 {d.page(p, e)}')
    return txt, (d, p, e)


def table_block(d, name, after, upto, hdr):
    """여러 위원회가 한 표에 이어진 활동 표: 머리행(hdr)마다 덩어리를 나누고, 덩어리 첫 자료행 첫 칸(공백·<br> 지움)이 name 으로
    시작하는 덩어리들의 처음~끝(이어진 글) → (글, p, e). 그 위원회 덩어리가 떨어져 있으면 오류."""
    a0 = 0
    for aa in (after if isinstance(after, (list, tuple)) else [after]):
        q = d.find(aa, a0)
        if q < 0:
            raise ValueError(f'{d.id}: block after 못 찾음 {aa!r}')
        a0 = q + 1
    b0 = d.find(upto, a0)
    if b0 < 0:
        raise ValueError(f'{d.id}: block upto 못 찾음 {upto!r}')
    hk = re.sub(r'\s+', '', hdr) if hdr else None
    key = re.sub(r'\s+', '', name)
    blocks, cur = [], None  # [start, end, owner]
    ls = d.display.rfind('\n', 0, a0) + 1
    while ls < b0:
        le = d.display.find('\n', ls)
        le = len(d.display) if le < 0 else le
        ln = d.display[ls:le]
        c0 = re.sub(r'\s+|<br>', '', ln.strip().strip('|').split('|')[0]) if ln.startswith('|') else ''
        if hdr is None and ln.startswith('|') and c0.endswith('위원회'):
            cur = [ls, le, c0]
            blocks.append(cur)
        elif hdr is not None and hk in re.sub(r'\s+', '', ln):
            cur = [ls, le, None]
            blocks.append(cur)
        elif cur is not None:
            cur[1] = le
            if cur[2] is None and ln.startswith('|'):
                c0 = re.sub(r'\s+|<br>', '', ln.strip().strip('|').split('|')[0])
                if re.search(r'위원회$', c0) or c0.endswith('위원회'):
                    cur[2] = c0
        ls = le + 1
    mine = [i for i, b in enumerate(blocks) if b[2] and b[2].startswith(key)]
    if not mine:
        raise ValueError(f'{d.id}: block 없음 {name!r}')
    if mine != list(range(mine[0], mine[-1] + 1)):
        raise ValueError(f'{d.id}: block 떨어져 있음 {name!r}')
    p, e = blocks[mine[0]][0], blocks[mine[-1]][1]
    return d.display[p:e], p, e


def table_row(d, key, after, ncell=3, first=0):
    """after 뒤 첫 md 표 행 중 칸 글(공백 지움)이 key 로 시작하는 칸이 있는 행 → 그 칸부터 ncell 칸(「 | 」로 이어진 원문 그대로)."""
    a0 = 0
    for aa in (after if isinstance(after, (list, tuple)) else ([after] if after else [])):
        q = d.find(aa, a0)
        if q < 0:
            raise ValueError(f'{d.id}: row after 못 찾음 {aa!r}')
        a0 = q + 1
    k = re.sub(r'\s+', '', key)
    ls = d.display.rfind('\n', 0, a0) + 1
    hits = 0
    while ls < len(d.display):
        le = d.display.find('\n', ls)
        le = len(d.display) if le < 0 else le
        ln = d.display[ls:le]
        if ln.startswith('|'):
            cells = ln.strip().strip('|').split('|')
            for i, c in enumerate(cells):
                if re.sub(r'\s+|<br>', '', c).startswith(k):
                    if hits == first:
                        seg = ' | '.join(x.strip() for x in cells[i:i + ncell])
                        p = d.find(seg, ls)
                        if p < 0 or p > le:
                            raise ValueError(f'{d.id}: row 글 못 찾음 {seg!r}')
                        si = bisect.bisect_left(d.smap, p)
                        e = d.smap[si + len(re.sub(r'\s+', '', seg)) - 1] + 1
                        return d.display[p:e], p, e
                    hits += 1
                    break
        ls = le + 1
    raise ValueError(f'{d.id}: row 못 찾음 {key!r}')


def held_from(spec, vals):
    """None → 문서에 없음 / ('lit', 값, note) / ('re', 칸, 정규식) → 원문 숫자."""
    if spec is None:
        return NA, ''
    if spec[0] == 'lit':
        return spec[1], spec[2]
    if spec[0] == 'rows':
        fld = spec[1]
        n, ds = 0, []
        for ln in vals[fld].split('\n'):
            if not ln.startswith('|'):
                continue
            cells = [re.sub(r'\s|<br>', '', c) for c in ln.strip().strip('|').split('|')][:3]
            hit = [c for c in cells if re.fullmatch(r'20\d\d\.\d{1,2}\.\d{1,2}\.?', c)]
            if hit:
                n += 1
                ds.append(hit[0])
        if not n:
            raise ValueError('held rows 0')
        return str(n), f'(판단) held_count 는 활동 표에서 앞 3칸 중 한 칸이 개최일자(날짜만 적힌 칸)인 행 수를 셈(행 {n}개, 서로 다른 날짜 {len(set(ds))}개)'
    if spec[0] == 'count':
        fld, rx = spec[1], spec[2]
        ms = re.findall(rx, vals[fld])
        n = len(ms) if len(spec) > 3 and spec[3] == 'all' else len(set(ms))
        if not n:
            raise ValueError('held count 0 ' + rx)
        return str(n), f'(판단) held_count 는 {fld} 의 회의별 개최일 글({len(set(ms))}개: {", ".join(sorted(set(ms))[:12])}{"…" if len(set(ms)) > 12 else ""})을 셈 — 원문에 개최 횟수 글 없음'
    fld, rx = spec[1], spec[2]
    m = re.search(rx, re.sub(r'\s+', ' ', vals[fld]))
    if not m:
        raise ValueError('held 못 찾음 ' + rx)
    return m.group(1), f'held_count 원문 「{m.group(0)}」({fld} 칸)'


def HRE(fld, rx):
    return ('re', fld, rx)


F_COLS = ['corp_label', 'fy', 'body_name', 'function_kw', 'chair_text', 'members_text', 'cadence_text', 'held_count', 'agenda_text',
          'doc_kind', 'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
F2_COLS = ['corp_label', 'fy', 'committee', 'established', 'held_count', 'agenda_list_text', 'subsidiary_related', 'members_text',
           'rcept_no', 'page', 'note', 'doc_name', 'collected_at']
F3_COLS = ['corp_label', 'fy', 'function', 'unit_name', 'headcount', 'concurrent_or_dispatched', 'duty_text', 'rcept_no_or_url', 'page',
           'note', 'doc_name', 'collected_at']
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note']
DL_COLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at',
           'text_path', 'status', 'note']

F_SPECS, F2_SPECS, F3_SPECS, CHK_SPECS = [], [], [], []
SPEC_FUNCS = []


def sec_title(d, p):
    if d.kind == 'BR':
        return re.sub(r' \[표 \d+\]$', '', d.label_at(p))
    if d.kind == 'AR_kit':
        return d.extra['sec_at'](p)
    for m in reversed(list(re.finditer(r'(?m)^(\d{1,2}|[IVX]+)\. ?([가-힣A-Za-z][^\n.]{1,40})$', d.display[:p]))):
        if '..' not in m.group(0) and '·' not in m.group(0)[-3:]:
            return m.group(0).strip()
    return ''


def pg(d, p, e):
    return d.page(p, e) + (' (6차 섹션 시작페이지)' if d.kind == 'AR_kit' else '')


def add_locnotes(d, main_pe, locs, cols, notes):
    """(검증 보완) 기준 칸(source_text·agenda_list_text·unit_name)과 다른 위치(절·표 / 쪽 / 섹션)에서 온 같은 문서의 칸은 note 에 「<칸> 위치 <위치>」.
    COMMON15b: *_text 칸이 source_text 와 다른 곳에서 왔으면 note 에 그 위치(page)."""
    mp = d.page(*main_pe)
    for k in cols:
        lc = locs.get(k)
        if not lc or lc[0] is not d:
            continue
        pk = d.page(lc[1], lc[2])
        if pk != mp and not any(n.startswith(k + ' ') for n in notes):
            notes.append(f'{k} 위치 {pk}')


def build_F(spec):
    co, fy = spec['co'], spec['fy']
    d = get_doc(spec['doc'], co)
    notes = []
    if spec.get('src') is None:
        return {'corp_label': co, 'fy': fy, 'body_name': spec['body'], 'function_kw': function_kw(spec['body']), 'chair_text': NA,
                'members_text': NA, 'cadence_text': NA, 'held_count': NA, 'agenda_text': NA, 'doc_kind': d.doc_kind,
                'section_title': spec.get('section', ''), 'source_text': NA, 'rcept_no_or_url': d.ref, 'page': spec.get('page', '(찾은 곳은 note)'),
                'note': spec.get('note', ''), 'doc_name': d.doc_name, 'collected_at': d.collected_at}
    vals, locs = {}, {}
    vals['source_text'], locs['source_text'] = field(spec['src'], co, d, 'F', fy, [], 'source_text')
    for k in ('chair', 'members', 'cadence', 'agenda'):
        vals[k + '_text'], locs[k + '_text'] = field(spec.get(k), co, d, 'F', fy, notes, k + '_text')
    held, hn = held_from(spec.get('held'), vals)
    if hn:
        notes.append(hn)
    _, p, e = locs['source_text']
    add_locnotes(d, (p, e), locs, ('chair_text', 'members_text', 'cadence_text', 'agenda_text'), notes)
    allnotes = ([spec['note']] if spec.get('note') else []) + notes
    na_cols = [k for k in ('chair_text', 'members_text', 'cadence_text', 'agenda_text') if vals[k] == NA] + (['held_count'] if held == NA else [])
    if na_cols and not spec.get('na_note_given'):
        allnotes.append(f"「문서에 없음」 칸({', '.join(na_cols)}): 찾은 범위 — {spec.get('searched', d.doc_kind + ' 전문(협의체 이름)·사업보고서 Ⅱ·Ⅵ')}")
    return {'corp_label': co, 'fy': fy, 'body_name': spec['body'],
            'function_kw': function_kw(spec['body'], vals['source_text']),
            'chair_text': vals['chair_text'], 'members_text': vals['members_text'], 'cadence_text': vals['cadence_text'],
            'held_count': held, 'agenda_text': vals['agenda_text'], 'doc_kind': d.doc_kind,
            'section_title': spec.get('section') or sec_title(d, p), 'source_text': vals['source_text'],
            'rcept_no_or_url': d.ref, 'page': pg(d, p, e),
            'note': ' / '.join(allnotes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}


# ───────────── F-2 공용 ─────────────
DATE_RX = re.compile(r'(?<!\d)(20\d\d|\d\d)\s*[.\-년/]\s*(\d{1,2})\s*[.\-월/]\s*(\d{1,2})(?!\d)')


def table_dates(txt):
    """md 표의 「개최일자」류 칸에서 날짜가 적힌 행 수·서로 다른 날짜 → (행 날짜 목록, 칸 찾음 여부)."""
    rows, col = [], None
    for ln in txt.split('\n'):
        if not ln.startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        hit = [i for i, c in enumerate(cells) if re.sub(r'\s|<br>', '', c) in ('개최일자', '개최일', '개최일시', '일자', '개최일자(회차)', '개최일(회차)', '회의일자')]
        if hit:
            col = hit[0]
            continue
        if col is None:
            continue
        nz = lambda c: re.sub(r'<br>|\s', '', c)
        m = DATE_RX.search(nz(cells[col])) if col < len(cells) else None
        if not m:
            for c in cells[:col + 1]:
                m = DATE_RX.search(nz(c))
                if m:
                    break
        if m:
            rows.append((m.group(1), int(m.group(2)), int(m.group(3))))
    return rows, col is not None


def ar_count_note(co, fy, com, held):
    """연차보고서(같은 FY, 본공시 — JB FY2025 는 정정공시)에서 「<위원회>는 <연도>년 중 총 N회」류 문장을 찾아 사업보고서 표 행 수와 맞대기(사실만)."""
    try:
        d = load_ar(co, fy + 1, '정정공시' if (co == 'JB금융지주' and fy == 2025) else '본공시')
    except Exception:
        return '연차보고서 글을 못 읽어 횟수 대조 못 함'
    k = re.escape(re.sub(r'\s+', '', com))
    rx = re.compile(r'(?:' + k + r'(?:는|은)?\d{4}년(?:중|도|도중)?총(\d+)(?:회|차례)|\d{4}년(?:중|도|도중)?' + k + r'(?:는|은)총(\d+)(?:회|차례))')
    hits = []
    for m in rx.finditer(d.stripped):
        n = m.group(1) or m.group(2)
        p0, p1 = d.smap[m.start()], d.smap[m.end() - 1] + 1
        hits.append((n, d.display[p0:p1].replace('\n', ' '), d.page(p0, p1)))
    if not hits:
        return f'연차보고서 FY{fy}({d.ref}) 에서 「{com}는 {fy}년 중 총 N회」류 문장 못 찾음(횟수 대조 못 함)'
    n, txt, pg_ = hits[0]
    same = (n == held)
    return f'연차보고서 FY{fy} {pg_} 원문 「{txt}」 — 사업보고서 표로 센 {held}회와 ' + ('같음' if same else '다름(사실만 적음)')


def build_F2(sp):
    co, fy = sp['co'], sp['fy']
    d = get_doc(sp['doc'], co)
    notes = [sp['note']] if sp.get('note') else []
    if sp.get('agenda') is None:
        return {'corp_label': co, 'fy': fy, 'committee': sp['committee'], 'established': NA, 'held_count': NA, 'agenda_list_text': NA,
                'subsidiary_related': NA, 'members_text': NA, 'rcept_no': d.ref, 'page': sp.get('page', '(찾은 곳은 note)'),
                'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}
    agenda, (ad, p, e) = field(sp['agenda'], co, d, 'F2', fy, notes, 'agenda_list_text')
    mtxt, mloc = field(sp.get('members'), co, d, 'F2', fy, notes, 'members_text')
    if mtxt == NA:
        notes.append('members_text: ' + sp.get('mem_note', '찾은 범위(사업보고서 Ⅵ 위원회 구성 표·연차보고서 위원회 절)에 위원 구성 글 없음'))
    est_spec = sp.get('established') or EST.get((co, fy, sp['committee']), (None, ''))[0]
    est, eloc = field(est_spec, co, d, 'F2', fy, notes, 'established')
    if est == NA:
        notes.append(sp.get('est_note', 'established: 찾은 범위(사업보고서 Ⅵ 1. 이사회에 관한 사항·연차보고서 해당 위원회 절·첨부 정관 위원회 조항, 검색어 「설치」「신설」「설립」)에 설치일 없음'))
    elif not sp.get('established') and (co, fy, sp['committee']) in EST:
        notes.append(EST[(co, fy, sp['committee'])][1])
    add_locnotes(ad, (p, e), {'members_text': mloc, 'established': eloc}, ('members_text', 'established'), notes)
    if sp.get('held'):
        held, hn = held_from(sp['held'], {'agenda_list_text': agenda})
        notes.append(hn)
    else:
        rows, intable = table_dates(agenda)
        if not intable or not rows:
            raise ValueError('개최일 칸 못 찾음 — held 를 명세에 줄 것')
        held = str(len(rows))
        ndis = len(set(rows))
        notes.append(f'(판단) held_count 는 개최 내역 표에서 개최일이 적힌 행 수를 셈(행 {len(rows)}개, 서로 다른 날짜 {ndis}개)' +
                     (sp.get('held_note', '')))
    if d.kind == 'BR':
        notes.append(ar_count_note(co, fy, sp['committee'], held))
    sub = 'Y' if re.search('자회사|그룹|계열사', re.sub(r'\s+', '', agenda)) else 'N'
    return {'corp_label': co, 'fy': fy, 'committee': sp['committee'], 'established': est, 'held_count': held, 'agenda_list_text': agenda,
            'subsidiary_related': sub, 'members_text': mtxt, 'rcept_no': d.ref, 'page': pg(d, p, e),
            'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}


def build_F3(sp):
    co, fy = sp['co'], sp['fy']
    d = get_doc(sp['doc'], co)
    notes = [sp['note']] if sp.get('note') else []
    if sp.get('unit') is None:
        notes += cmp14(co, sp.get('cmp14'), None, None)
        return {'corp_label': co, 'fy': fy, 'function': NA, 'unit_name': NA, 'headcount': NA,
                'concurrent_or_dispatched': NA, 'duty_text': NA, 'rcept_no_or_url': d.ref, 'page': sp.get('page', '(찾은 곳은 note)'),
                'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}
    vals = {}
    locs = {}
    for k in ('function', 'unit', 'cod', 'duty', 'hc'):
        vals[k], locs[k] = field(sp.get(k), co, d, 'F3', fy, notes, {'unit': 'unit_name', 'cod': 'concurrent_or_dispatched', 'duty': 'duty_text',
                                                                          'hc': 'headcount', 'function': 'function'}[k])
    hc = vals['hc']
    if sp.get('hc_val'):
        notes.append(f"headcount 원문 「{hc}」 — " + sp['hc_val'][1])
        hc = sp['hc_val'][0]
    elif hc != NA:
        m = re.search(r'\d+', hc)
        notes.append(f'headcount 원문 「{hc}」')
        hc = m.group(0) if m and sp.get('hc_num', True) else hc
    if vals['cod'] == NA:
        notes.append(sp.get('cod_note', 'concurrent_or_dispatched: 그 글에 겸직·파견 표시 없음'))
    notes += cmp14(co, sp.get('cmp14', '감사위원회 지원'), vals['unit'], hc)
    _, p, e = locs['unit']
    add_locnotes(d, (p, e), {'function': locs['function'], 'concurrent_or_dispatched': locs['cod'], 'duty_text': locs['duty']},
                 ('function', 'concurrent_or_dispatched', 'duty_text'), notes)
    return {'corp_label': co, 'fy': fy, 'function': vals['function'], 'unit_name': vals['unit'], 'headcount': hc,
            'concurrent_or_dispatched': vals['cod'], 'duty_text': vals['duty'], 'rcept_no_or_url': d.ref, 'page': pg(d, p, e),
            'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}


def cmp14(co, kind, unit, hc):
    """14차 handoff/14차_조직인원겸직/14_지원조직_인원.csv(사업보고서 기준 행)와 맞대기 — 사실만 note 로."""
    if not kind:
        return []
    rows = [r for r in csv.DictReader(open(f'{ROOT}/handoff/14차_조직인원겸직/14_지원조직_인원.csv', encoding='utf-8-sig'))
            if r['회사'] == co and r['조직 종류'].startswith(kind) and '연차보고서' not in r['조직 종류'] and '사업보고서' in r['출처']]
    if not rows:
        return [f'14차 14_지원조직_인원.csv 에 {co} 「{kind}」 사업보고서 행 없음(14차 대상 8개사 밖이거나 행 없음)']
    out = []
    for r in rows:
        s = f"14차 14_지원조직_인원.csv(사업보고서 기준) 「{r['조직 종류']}」 {r['부서(팀)명']} 직원수 {r['직원수']}"
        if unit is not None:
            same_u = re.sub(r'\s', '', r['부서(팀)명']) == re.sub(r'\s', '', unit)
            same_h = re.sub(r'\D', '', r['직원수']) == re.sub(r'\D', '', str(hc))
            s += ' — ' + ('부서 이름 같음' if same_u else '부서 이름 다름') + ', ' + ('인원 같음' if same_h else '인원 다름')
        out.append(s)
    return out


REQ_LINE_F2 = '함께 볼 것: NH·BNK 내부통제위원회 첫 개최일과 첫 안건(FY2024), 신한 \'자회사경영관리위원회\'가 없어지거나 자회사최고경영자후보추천위원회로 합쳐진 시점과 사유(FY2022·FY2023)'


def build_CHK(sp):
    co = sp['co']
    if sp.get('src') is None:
        return {'item_id': sp['item_id'], 'item_text': sp.get('item_text', REQ_LINE_F2), 'corp_label': co, 'fy': sp['fy'], 'result': sp['result'],
                'where': sp.get('where', ''), 'rcept_no_or_url': sp.get('ref', ''), 'page': sp.get('page', ''), 'source_excerpt': NA, 'note': sp['note']}
    d = get_doc(sp['doc'], co)
    txt, (dd, p, e) = field(sp['src'], co, d, 'CHK', sp['fy'], [], 'source_excerpt')
    if len(re.sub(r'\s+', ' ', txt)) > 300:
        raise ValueError(f'source_excerpt 300자 넘음 {len(txt)}')
    return {'item_id': sp['item_id'], 'item_text': sp.get('item_text', REQ_LINE_F2), 'corp_label': co, 'fy': sp['fy'],
            'result': sp.get('result', '원문 있음'), 'where': sp.get('where', ''), 'rcept_no_or_url': d.ref, 'page': pg(d, p, e),
            'source_excerpt': txt, 'note': sp.get('note', '')}


# ───────────── 쓰기 ─────────────
def write_csv(path, cols, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})
    os.replace(tmp, path)


def write_wonmun():
    """행의 글이 나온 절(사업보고서)·쪽(연차보고서 FY2023)·섹션(연차보고서 FY2024·25) 전체를 회사·FY·문서별 md 로."""
    files = {}
    for (task, corp, fy, did), (doc, spans) in sorted(SPANS.items(), key=lambda x: (x[0][0], x[0][1], str(x[0][2]), x[0][3])):
        if doc.kind == 'BR':
            bounds = sorted(set(doc.extra['sec_starts'] + [len(doc.display)]))  # 절(XML TITLE) 시작마다 — 절 전체
        else:
            bounds = sorted(set([m[0] for m in doc.marks] + [len(doc.display)]))
        ivs = []
        for p, e in spans:
            a = bounds[max(0, bisect.bisect_right(bounds, p) - 1)]
            b = bounds[min(len(bounds) - 1, bisect.bisect_left(bounds, e))]
            if b - a > 80000:
                a, b = max(a, p - 3000), min(b, e + 3000)
            ivs.append([a, b])
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        sub = {'F': 'F', 'F2': 'F2', 'F3': 'F3', 'CHK': 'F2'}[task]
        if doc.kind == 'BR':
            dname = f'사업보고서_{doc.ref}'
        else:
            dname = f"연차보고서_{doc.fy + 1}공시_{doc.id.split(':')[-1]}"
        path = f'{OUT}/원문/{sub}/{corp}__FY{doc.fy}__{dname}.md'
        files.setdefault(path, (doc, []))[1].extend(merged)
    for path, (doc, ivs) in files.items():
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        lines = [f'# {doc.doc_kind} — {doc.corp} FY{doc.fy}', '',
                 f'- 문서: {doc.doc_name}', f'- 출처: {doc.ref}', f'- 받은 시각: {doc.collected_at}', f'- 글: {doc.path}',
                 '- 아래는 행의 글이 나온 절(사업보고서 XML md, 「[표 n]」 표지는 지움) 또는 쪽(연차보고서 FY2023 PDF 글)·섹션(연차보고서 FY2024·25 6차 섹션 글) 전체. 줄 안 공백 연속은 한 칸으로 줄임.', '']
        for a, b in merged:
            lines += [f'## {doc.page(a, b)}', '', doc.display[a:b], '']
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    return list(files)


def doclist(rows_all):
    """쓴 문서(행 출처) + 찾은 범위로 읽은 문서(g2 5개사 FY2023~2025 사업보고서 본·정정, 연차보고서 모든 공시유형) + 13차 보관 PDF 글 zip."""
    used = set()
    for task, rows in rows_all:
        for r in rows:
            ref = r.get('rcept_no_or_url') or r.get('rcept_no') or ''
            if ref:
                used.add(ref)
    docs = []
    for co in G2:
        for fy in (2023, 2024, 2025):
            for x in br_rows():
                if x['label'] == co and x['fy'] == str(fy):
                    if x['text_path']:
                        docs.append(load_br(x['rcept_no']))
                    else:
                        docs.append(x)
            yr = fy + 1
            if yr <= 2024:
                typs = sorted(set(r['공시유형'] for r in ar_list() if r['회사'] == co and r['공시연도'] == str(yr)))
            else:
                typs = sorted(set(r['공시유형'] for r in kit_rows() if r['지주명'] == co and r['공시연도'] == str(yr) and '지배구조' in r['파일명']))
            for ty in typs:
                try:
                    docs.append(load_ar(co, yr, ty))
                except Exception as ex:
                    docs.append(('AR', co, fy, ty, str(ex)))
    out = []
    for d in docs:
        if isinstance(d, dict):  # XML 글 없는 정정(첨부정정 등)
            out.append(dict(doc_kind='사업보고서', corp_label=d['label'], fy_or_date=f"FY{d['fy']}", report_nm=d['report_nm'], rcept_no_or_url=d['rcept_no'],
                            rcept_dt=d['rcept_dt'], raw_path=d['raw_path'], sha256=d['raw_sha256'], fetched_at=d['fetched_at'], text_path='',
                            status='받음', note='XML 본문 글 없음(첨부정정 등) — 대조 안 함'))
            continue
        if isinstance(d, tuple):
            out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label=d[1], fy_or_date=f'FY{d[2]}', report_nm='', rcept_no_or_url='', rcept_dt='',
                            raw_path='', sha256='', fetched_at='', text_path='', status='실패', note=f'{d[3]} 글 읽기 실패: {d[4][:100]}'))
            continue
        kind = ('6차 섹션 글(PDF 원본은 이번 컨테이너에 없음)' if d.kind == 'AR_kit' else
                ('연차보고서 PDF 글(「## p.N」)' if d.kind == 'AR_md' else f"OpenDART XML md ({d.extra.get('kind')})"))
        typ = '' if d.kind == 'BR' else d.id.split(':')[3]
        role = '행 출처' if d.ref in used else '찾은 범위로 읽음(행 출처 아님 — note 에 위치를 적은 곳 포함)'
        extra = ''
        if d.id == 'AR:JB금융지주:2026:본공시':
            extra = ' / 글자 겹침(두 번씩)으로 출처로 쓰지 않음 — 같은 해 정정공시 글을 씀'
        if 'BNK' in d.corp and typ == '수정공시':
            extra = ' / 보수체계 연차보고서 수정 공시(지배구조 부분 아님)'
        out.append(dict(doc_kind=d.doc_kind, corp_label=d.corp, fy_or_date=f'FY{d.fy}', report_nm=d.doc_name, rcept_no_or_url=d.ref,
                        rcept_dt=d.extra.get('rcept_dt', ''), raw_path=d.extra.get('raw_path', '') or d.extra.get('fname', ''),
                        sha256=d.extra.get('sha', ''), fetched_at=d.collected_at, text_path=d.path, status='받음',
                        note=f'{kind}' + (f' {typ}' if typ else '') + f' / {role}' + extra +
                        (f' / 제어문자 {CTRL_COUNT[d.id]}개 지움' if CTRL_COUNT.get(d.id) else '')))
    out.append(dict(doc_kind='사업보고서 본문 PDF 글(13차 보관)', corp_label='메리츠금융지주·iM금융지주·한국투자금융지주', fy_or_date='FY2025',
                    report_nm='13차_지주관리유형_텍스트.zip 안 텍스트/사업보고서__<회사>.md', rcept_no_or_url='', rcept_dt='',
                    raw_path='handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip', sha256='', fetched_at='', text_path='',
                    status='받음', note='COMMON15 page 규칙 — FY2025 사업보고서 행 page 에 「p.N(본문 PDF, 13차 보관)」을 덧붙이려고 읽음(글 대조는 XML md 로 함)'))
    return out


Z13 = f'{ROOT}/handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip'


def pdf13(co):
    """13차 보관 FY2025 사업보고서 본문 PDF 글(「## p.N」) → (공백·표지 지운 글, 쪽 시작 위치 목록)."""
    key = 'P13:' + co
    if key not in _cache:
        import zipfile
        z = zipfile.ZipFile(Z13)
        names = [n for n in z.namelist() if n.endswith(f'텍스트/사업보고서__{co}.md')]
        if not names:
            _cache[key] = None
        else:
            t = z.read(names[0]).decode('utf-8')
            parts, marks, buf = [], [], 0
            for m in re.finditer(r'(?m)^## p\.(\d+).*$', t):
                marks.append((m.start(), int(m.group(1))))
            st, pos = [], []
            for i, (s0, n) in enumerate(marks):
                e0 = marks[i + 1][0] if i + 1 < len(marks) else len(t)
                body = t[s0:e0].split('\n', 1)[1] if '\n' in t[s0:e0] else ''
                c = re.sub(r'\s+', '', body)
                pos.append((buf, n))
                st.append(c)
                buf += len(c)
            _cache[key] = (''.join(st), pos)
    return _cache[key]


def add_pdf13(rows, col, refcol):
    """COMMON15 page 규칙: FY2025 사업보고서(메리츠·iM·한국투자) 행은 13차 보관 본문 PDF 글에서 칸 글 첫머리(공백·「|」「<br>」 지운 20자)를 찾아 쪽을 덧붙임."""
    for r in rows:
        ref = r.get(refcol, '')
        if r['corp_label'] not in ('메리츠금융지주', 'iM금융지주', '한국투자금융지주') or str(r['fy']) != '2025' or not re.fullmatch(r'\d{14}', ref):
            continue
        if ref != br_id(r['corp_label'], 2025):
            continue
        v = r.get(col, '')
        if not v or v == NA:
            continue
        P = pdf13(r['corp_label'])
        if not P:
            continue
        txt, pos = P
        full = re.sub(r'\s+', '', v.replace('<br>', '').replace('|', ''))
        hits = []
        for off in (0, 8, 20, 40, 80):
            k = full[off:off + 20]
            if len(k) < 12:
                break
            hits = [m.start() for m in re.finditer(re.escape(k), txt)]
            if hits:
                break
        if len(hits) >= 1:
            pages = sorted(set(pos[bisect.bisect_right([x[0] for x in pos], h) - 1][1] for h in hits))
            r['page'] += f" / p.{pages[0]}(본문 PDF, 13차 보관 — 칸 글 {off}자째부터 20자 위치" + (f", 같은 글 {len(hits)}곳 중 첫 곳)" if len(hits) > 1 else ')')
        else:
            r['page'] += ' / 13차 보관 본문 PDF 글에서 칸 글 첫머리를 못 찾음(PDF 표 글 순서가 달라서일 수 있음)'


def add_corr(rows, cols, refcol):
    """COMMON15: 본 보고서 기준, 같은 FY 정정판이 있으면 같은 글이 있는지 보고 다르면 note 「정정 <rcept_no>: …」."""
    for r in rows:
        ref = r.get(refcol, '')
        if not re.fullmatch(r'\d{14}', ref):
            continue
        d = load_br(ref)
        if d.extra.get('kind') != '본':
            continue
        cors = [x for x in br_rows() if x['label'] == d.corp and x['fy'] == str(d.fy) and x['kind'] == '정정']
        if not cors:
            continue
        msg = []
        for x in cors:
            if not x['text_path']:
                msg.append(f"정정 {x['rcept_no']}({x['report_nm']}): XML 글 없음 — 대조 못 함")
                continue
            if x['report_nm'].startswith('[첨부정정]'):
                msg.append(f"정정 {x['rcept_no']}({x['report_nm']}): 첨부 서류 정정(본문 Ⅱ·Ⅵ 글 없음) — 대조 안 함")
                continue
            cd = load_br(x['rcept_no'])
            cs = cmpnorm(cd.display, True)
            bad = [c for c in cols if r.get(c) and r[c] != NA and cmpnorm(r[c], True) not in cs]
            msg.append(f"정정 {x['rcept_no']}({x['report_nm']}): " + ('같은 글 있음' if not bad else '이 칸 글이 그대로 있지 않음 — ' + ', '.join(bad)))
        r['note'] = (r['note'] + ' / ' if r['note'] else '') + '; '.join(msg)


def ar_variants(d):
    """같은 회사·공시연도의 다른 공시유형(추가·정정·재공시·수정) Doc 목록."""
    corp, year, typ = d.id.split(':')[1], int(d.id.split(':')[2]), d.id.split(':')[3]
    if year <= 2024:
        typs = sorted(set(r['공시유형'] for r in ar_list() if r['회사'] == corp and r['공시연도'] == str(year)
                          and not ('보수체계' in r['제목'] and '지배구조' not in r['제목'])
                          and os.path.exists(f"{ROOT}/dart_out/text/ops15/연차보고서__{corp}__{year}__{r['공시유형']}.md")))
    else:
        typs = sorted(set(r['공시유형'] for r in kit_rows() if r['지주명'] == corp and r['공시연도'] == str(year) and '지배구조' in r['파일명']))
    return [load_ar(corp, year, x) for x in typs if x != typ]


def add_ar_var(rows, cols, refcol):
    """연차보고서: 본공시 기준 — 같은 해 추가·정정·재공시·수정 공시가 있으면 같은 글이 있는지 note."""
    for r in rows:
        ref = r.get(refcol, '')
        if not ref.startswith('http'):
            continue
        d = doc_by_ref(ref)
        msg = []
        for v in ar_variants(d):
            if v.id == 'AR:JB금융지주:2026:본공시':
                msg.append(f"같은 해 본공시({v.ref}): 6차 섹션 글이 글자 겹침(두 번씩)으로 나와 글자 대조 못 함")
                continue
            cs = cmpnorm(v.display)
            bad = [c for c in cols if r.get(c) and r[c] != NA and cmpnorm(r[c]) not in cs]
            nm = v.id.split(':')[3]
            msg.append(f"같은 해 {nm}({v.ref}): " + ('같은 글 있음' if not bad else '이 칸 글이 그대로 있지 않음 — ' + ', '.join(bad)))
        if msg:
            r['note'] = (r['note'] + ' / ' if r['note'] else '') + '; '.join(msg)


def main():
    for fn in SPEC_FUNCS:
        fn()
    frows, f2rows, f3rows, chk, errs = [], [], [], [], []
    for sp in F_SPECS:
        try:
            frows.append(build_F(sp))
        except Exception as ex:
            errs.append(f"F {sp['co']} FY{sp['fy']} {sp['body']}: {ex}")
    for sp in F2_SPECS:
        try:
            f2rows.append(build_F2(sp))
        except Exception as ex:
            errs.append(f"F2 {sp['co']} FY{sp['fy']} {sp['committee']}: {ex}")
    for sp in F3_SPECS:
        try:
            f3rows.append(build_F3(sp))
        except Exception as ex:
            errs.append(f"F3 {sp['co']} {sp.get('unit')}: {ex}")
    for sp in CHK_SPECS:
        try:
            chk.append(build_CHK(sp))
        except Exception as ex:
            errs.append(f"CHK {sp['item_id']}: {ex}")
    for rows, refc in ((frows, 'rcept_no_or_url'), (f2rows, 'rcept_no'), (f3rows, 'rcept_no_or_url')):
        for r in rows:
            try:
                dd = doc_by_ref(r[refc])
            except Exception:
                continue
            if CTRL_COUNT.get(dd.id) and not all(r.get(c) == NA for c in r if c.endswith('_text') or c == 'source_text'):
                r['note'] = (r['note'] + ' / ' if r['note'] else '') + f'제어문자 지움(출처 글의 보이지 않는 제어문자 \\x00 등 {CTRL_COUNT[dd.id]}개를 지우고 옮김)'
    add_corr(frows, ['source_text', 'chair_text', 'members_text', 'cadence_text', 'agenda_text'], 'rcept_no_or_url')
    add_corr(f2rows, ['agenda_list_text', 'members_text'], 'rcept_no')
    add_ar_var(frows, ['source_text', 'chair_text', 'members_text', 'cadence_text', 'agenda_text'], 'rcept_no_or_url')
    add_ar_var(f2rows, ['agenda_list_text', 'members_text'], 'rcept_no')
    add_ar_var(f3rows, ['duty_text', 'concurrent_or_dispatched'], 'rcept_no_or_url')
    add_pdf13(frows, 'source_text', 'rcept_no_or_url')
    add_pdf13(f2rows, 'agenda_list_text', 'rcept_no')
    write_csv(f'{OUT}/조각/F_g2.csv', F_COLS, frows)
    write_csv(f'{OUT}/조각/F2_g2.csv', F2_COLS, f2rows)
    write_csv(f'{OUT}/조각/F3_g2.csv', F3_COLS, f3rows)
    write_csv(f'{OUT}/조각/확인_F_g2.csv', CHK_COLS, chk)
    for sub in ('F', 'F2', 'F3'):
        dd = f'{OUT}/원문/{sub}'
        if os.path.isdir(dd):
            for fn in os.listdir(dd):
                if any(fn.startswith(c + '__') for c in G2):
                    os.remove(os.path.join(dd, fn))
    write_wonmun()
    dl = doclist([('F', frows), ('F2', f2rows), ('F3', f3rows), ('CHK', chk)]) + EXTRA_DOCS
    write_csv(f'{OUT}/문서목록15b_F_g2.csv', DL_COLS, dl)
    print(f'F {len(frows)}  F2 {len(f2rows)}  F3 {len(f3rows)}  확인 {len(chk)}  문서 {len(dl)}')
    for e in errs:
        print('ERR', e)
    return 1 if errs else 0


EXTRA_DOCS = []

# ═════════════════════════ 회사별 명세 ═════════════════════════
AUDIT_PARA_NOTE = '(판단) 연차보고서 FY2025 에 「감사위원회 지원조직(내부감사부서) 현황」 표는 없고 「감사위원회」 절 「라. 감사보조조직 등」 문단에 부서·인원이 적혀 있어 그 문단을 옮김(function 은 그 절 제목 원문)'
COMP_NA_NOTE = '연차보고서 FY2025(6차 섹션 공시연도 2026) 전문에 「준법감시인·위험관리책임자 지원조직 현황」 표 없음(찾은 범위: 연차보고서 전문 「지원조직」「준법감시」「위험관리책임자」「직원수」「부서(팀)명」).'
FY23_AR_NOTE = '연차보고서 FY2023 은 PDF 글(pymupdf) — 글자 순서가 흩어져 숫자·문장부호가 다른 줄에 나옴(글 순서 그대로 옮김)'
BR_VI_SEARCH = '사업보고서 Ⅵ 「1. 이사회에 관한 사항」 이사회내 위원회 구성 표·활동 표와 「2. 감사제도에 관한 사항」, 연차보고서 목차'


def spec_MZ():
    co = '메리츠금융지주'
    # ── F: 경영협의회 ──
    gy_br = '사업보고서 Ⅸ 「다. 계열회사간의 업무조정이나 이해관계를 조정하는 기구의 현황」에 「그룹 경영협의회를 구성하여 운영」 문장이 있음(FY2023~2025 같은 글) — 연차보고서 글을 기준으로 함'
    chair_na = 'chair_text: 협의절차에 「협의회 의장이 별도로 소집할 수 있습니다」라고만 있고 의장이 누구인지 적은 글은 찾은 범위(연차보고서 「경영협의회」 절·사업보고서 Ⅸ)에 없음'
    F_SPECS.append(dict(
        co=co, fy=2023, body='경영협의회', doc=('AR', 2024), section='8. 경영협의회',
        src=S('메리츠금융그룹은 지주 및 자회사 간의 원활한 의사소통과', '현안을 공유하고협의하고 있습니다,.'),
        cadence=S('지주 및 자회사의 효과적인 의사소통을 위해 통상적으로 월회 개최하고', '의장이 별도로 소집할 수 있습니다'),
        members=S('그룹 경영협의회는 메리츠금융지주', '별도 선임일은 기재하지 않습니다* 2023.12.31.,.'),
        agenda=S('년 경영협의회는 총', '안에 대한 협의가 진행되었습니다.'),
        held=('lit', '12', '(판단) held_count: PDF 글에서 「년 경영협의회는 총 / 회 개최되었습니다 / 2023 / 12」로 숫자가 줄 밖으로 밀려 나옴 — 12 를 그해 개최 횟수로 읽음'),
        note=FY23_AR_NOTE + ' / ' + gy_br + ' / ' + chair_na, na_note_given=True))
    for yr in (2025, 2026):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='경영협의회', doc=('AR', yr),
            src=S('메리츠금융그룹은 지주 및 자회사 간의 원활한 의사소통과', '현안을 공유하고, 협의하고 있습니다.'),
            cadence=S('지주 및 자회사의 효과적인 의사소통을 위해 통상적으로 월 1회 개최하고', '별도로 소집할 수 있습니다.'),
            members=S('그룹 경영협의회는 메리츠금융지주 CEO', '협의회 구성의 별도 선임일은 기재하지 않습니다.'),
            agenda=S(f'{fy}년 경영협의회는 총', '안에 대한 협의가 진행되었습니다.'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=gy_br + ' / ' + chair_na + (' / FY2025 연차보고서에는 「보고서 제출일 현재 기준 경영협의회 구성원이 일부 변경」 표가 하나 더 있음(members_text 는 2025.12.31. 기준 표까지)' if fy == 2025 else ''),
            na_note_given=True))
    # ── F: 그룹리스크협의회 ──
    rk_br = '같은 협의회를 사업보고서 Ⅱ 위험관리 서술·Ⅲ 주석(「그룹리스크관리위원회 및 그룹리스크협의회를 통해서 정기적으로 신용위험을 점검」 등)에도 적음 — 연차보고서 글을 기준으로 함'
    F_SPECS.append(dict(
        co=co, fy=2023, body='그룹리스크협의회', doc=('AR', 2024), section='9. 그룹리스크협의회',
        src=S('메리츠금융그룹의 지주 및 자회사 리스크관리를 위한 협의체인 그룹리스크협의회에서는', '그 외에 위원회 협의 요청건 및 위원장이 필요하다고 인정한 사항·'),
        cadence=S('그룹리스크협의회는 최소 분기 회 개최하는 것을 원칙으로 하며', '로 회의를 소집할 수 있습니다'),
        members=S('회사는 그룹내 전략적 의사결정에 대한 리스크를 측정관리하고자', '별도 선임일은 기재하지 않습니다* 2023.12.31.,.'),
        chair=S('협의회 의장은 그룹리스크관리최고책임자로 하고 의장은', '의회에 참석 시킬 수 있습니다.'),
        agenda=S('년에는 총 회의 그룹리스크협의회가 소집되었고', '시행세칙 제정안()가결'),
        held=('lit', '4', '(판단) held_count: PDF 글 「년도에는 총 / 회의 그룹리스크협의회가 개최되었습니다 / 협의회 / . 2023 / 4」에서 숫자가 줄 밖으로 밀려 나옴 — 4 를 그해 개최 횟수로 읽음(개최 내역 표 회차 4개와 같음)'),
        note=FY23_AR_NOTE + ' / ' + rk_br + ' / agenda_text 는 「라. 활동내역 개요」와 세부 개최 내역 표 글(표의 첫 줄 「메리츠자산운용 위험관리책임자 윤명수 위원 그룹리스크협의회 참여 (2023.01.01.~203.06.30.)」 주석 포함 — 원문 「203.06.30.」 그대로)'))
    ends = {2024: '1.CY2025 그룹 및 계열사 MRR한도 협의', 2025: '1.CY2026 그룹 및 계열사 MRR한도 협의(안)'}
    for yr in (2025, 2026):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹리스크협의회', doc=('AR', yr),
            src=S('메리츠금융그룹의 지주 및 자회사 리스크관리를 위한 협의체인 그룹리스크협의회에서는', '· 기타 협의회가 필요하다고 인정하는 사항'),
            cadence=S('그룹리스크협의회는 최소 분기 1회 개최하는 것을 원칙으로 하며', '로 회의를 소집할 수 있습니다.'),
            members=S('회사는 그룹 내 전략적 의사결정에 대한 리스크를 측정·관리하고자', '협의회 구성의 별도 선임일은 기재하지 않습니다.'),
            chair=S('협의회 의장은 그룹리스크관리최고책임자로 하고 의장은', '의회에 참석 시킬 수 있습니다.'),
            agenda=S(f'{fy}년에는 총', ends[fy]),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=rk_br + ' / agenda_text 는 「라. 활동내역 개요」와 세부 개최 내역 표 글(쪽 머리·꼬리 글 포함 그대로)' +
            (' / FY2025 연차보고서에는 「보고서 제출일 현재 기준 그룹리스크협의회 구성원이 일부 변경」 표가 하나 더 있음' if fy == 2025 else '')))
    # ── F: 내부통제협의회(FY2025) ──
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제협의회', doc=('AR', 2026),
        src=S('이에 따라 회사 내부통제 관리업무의 효율적 수행을 위하여 내부통제위원회와는 별도로', '「내부통제협의회운영지침」 제정을 심의·의결하였습니다.'),
        chair=S('대표이사를 의', '장으로 하고', after='내부통제위원회와는 별도로'),
        members=S('준법감시인, 위험관리책임자 등을 위원으로 구성하는 내부통제협의회를', after='내부통제위원회와는 별도로'),
        note='연차보고서 FY2025 「내부통제위원회」 절(내부통제위원회 권한 서술) 안의 문장. 첨부 내부통제위원회 규정 「제12조(내부통제협의회) 위원회는 내부통제 관리 업무의 효율적 수행을 위해 내부통제 관리협의회를 둘 수 있다.」. 사업보고서 FY2025 Ⅵ 내부통제위원회 활동 표 25.07.15 「2. 내부통제협의회 운영지침 제정의 건」. 주기·개최 횟수·안건 글은 찾은 범위(연차보고서 FY2025 전문·사업보고서 FY2025 「내부통제협의회」)에 없음. FY2023·FY2024 문서에는 「내부통제협의회」 낱말 없음'))
    # ── F: 그룹 감사협의회(FY2024 연차보고서에 이름만) ──
    F_SPECS.append(dict(
        co=co, fy=2024, body='그룹 감사협의회', doc=('AR', 2025),
        src=S('-나.「감사위원회규정」제12조,「감사위원회직무규정시행세칙」제2조 및「내부회계관리규정」제22조에 의거,', '감사위원회직무규정 및 내부회계관리규정 등을 개정'),
        note='연차보고서 FY2024(2025 공시) 감사위원회 회의 내역(「CY2025 감사업무 추진계획 승인의 건」 회의 — 2025년 회의)의 의결안건 설명에 「그룹 감사협의회운영지침을 제정」으로 이름만 나옴. 구성·주재자·주기·개최 횟수·안건 서술은 찾은 범위(연차보고서 FY2023~FY2025 전문·사업보고서 FY2023~FY2025 「감사협의회」)에 없음. 연차보고서 FY2025 에는 「감사협의회」 낱말 없음',
        na_note_given=True))
    # ── F-2 ──
    mz_bodies = '이사회내 위원회: 보수위원회·리스크관리위원회·임원후보추천위원회' 
    for fy in (2024, 2025):
        after = ['VI. 이사회 등 회사의 기관에 관한 사항', '라. 이사회내 위원회']
        comp = ['VI. 이사회 등 회사의 기관에 관한 사항', '라. 이사회내 위원회']
        n_ar = {2024: 2025, 2025: 2026}[fy]
        F2_SPECS.append(dict(co=co, fy=fy, committee='리스크관리위원회', doc=('BR', fy),
                             agenda=S('(2) 리스크관리위원회의 활동내역', upto='(3) 임원후보추천위원회의 활동내역', after=after),
                             members=dict(row='리스크관리위원회', after=comp, ncell=3),
                             note='(판단) 안건 목록은 사업보고서 Ⅵ 위원회 활동 표를 씀 — 연차보고서(본공시) 「그룹리스크관리위원회」 절에 같은 해 회의별 서술이 있음'))
        F2_SPECS.append(dict(co=co, fy=fy, committee='감사위원회', doc=('BR', fy),
                             agenda=S('다. 감사위원회의 활동', upto='라. 교육 실시계획', after=['VI. 이사회 등 회사의 기관에 관한 사항', '2. 감사제도에 관한 사항']),
                             members=S('안동현[위원장]', '조홍희(출석률:100%)', after=['2. 감사제도에 관한 사항', '다. 감사위원회의 활동']),
                             note='(판단) 안건 목록은 사업보고서 Ⅵ 「2. 감사제도에 관한 사항 > 다. 감사위원회의 활동」 표를 씀 — 연차보고서(본공시) 「감사위원회」 절에 같은 해 회의별 서술이 있음 / members_text 는 활동 표 머리행의 위원 이름 칸(위원 인적사항 표는 Ⅵ 「2. 가. 감사위원회 위원의 인적사항」)'))
        F2_SPECS.append(dict(co=co, fy=fy, committee='자회사대표이사후보추천위원회', doc=('BR', fy),
                             note=f'사업보고서 FY{fy} Ⅵ 「라. 이사회내 위원회」 표의 위원회는 보수위원회·리스크관리위원회·임원후보추천위원회' + ('·내부통제위원회' if fy == 2025 else '') +
                             '(감사위원회는 Ⅵ.2) — 자회사 대표이사 후보 추천을 맡는 위원회 이름 없음. 임원후보추천위원회 설치목적 칸 원문 「대표이사, 사외이사, 감사위원 후보자 추천 및 후보군 관리」. 찾은 범위: ' + BR_VI_SEARCH + '(「자회사」「후보추천」)'))
        F2_SPECS.append(dict(co=co, fy=fy, committee='ESG위원회', doc=('BR', fy),
                             note=f'사업보고서 FY{fy} Ⅵ 이사회내 위원회 표·연차보고서 목차에 ESG위원회(지속가능경영위원회 등) 없음 — 이사회 보고 안건 「그룹 ESG 경영현황 보고」만 있음. 찾은 범위: ' + BR_VI_SEARCH + '(「ESG」「지속가능」)'))
    F2_SPECS.append(dict(co=co, fy=2025, committee='내부통제위원회', doc=('BR', 2025),
                         agenda=S('(4) 내부통제위원회의 활동내역', upto='마. 이사의 독립성', after=['VI. 이사회 등 회사의 기관에 관한 사항', '라. 이사회내 위원회']),
                         members=dict(row='내부통제위원회', after=['VI. 이사회 등 회사의 기관에 관한 사항', '라. 이사회내 위원회'], ncell=3),
                         established=S('2025. 3. 26.부 내부통제위원회가 설립된', doc=('AR', 2026)),
                         note='(판단) 안건 목록은 사업보고서 Ⅵ 위원회 활동 표를 씀 — 연차보고서 FY2025 「내부통제위원회」 절에 같은 해 회의별 서술이 있음. 사업보고서 FY2025 이사회 표 25.03.26 「2. 내부통제위원회 설치 및 관련 내규 제·개정의 건」'))
    F2_SPECS.append(dict(co=co, fy=2024, committee='내부통제위원회', doc=('BR', 2024),
                         note='사업보고서 FY2024 Ⅵ 이사회내 위원회 표·활동 표와 연차보고서 FY2024 목차에 내부통제위원회 없음(찾은 범위: ' + BR_VI_SEARCH + ' 「내부통제위원회」). 연차보고서 FY2025 「2025. 3. 26.부 내부통제위원회가 설립된」'))
    # ── F-3 ──
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026),
                         function=S('라. 감사보조조직 등'),
                         unit=S('감사팀', after='라. 감사보조조직 등'),
                         hc=S('총4명', after='라. 감사보조조직 등'),
                         cod=S('필요시', '인력을 파견 받아', after='라. 감사보조조직 등'),
                         duty=S('효율적인 업무수행을 위하여 감사위원회의 감사보조조직으로서', '효과적으로 감사업무를 수행하고 있습니다.', after='라. 감사보조조직 등'),
                         note=AUDIT_PARA_NOTE))
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026), function=None, unit=None,
                         cmp14='준법감시인 지원', note=COMP_NA_NOTE + ' 사업보고서 FY2025 Ⅵ 「사. 준법감시인 등에 관한 사항 > (3) 준법감시인 지원조직 현황」 표 있음.'))


SPEC_FUNCS.append(spec_MZ)


def spec_HT():
    co = '한국투자금융지주'
    ov = '연차보고서 「1. 지배구조 일반」에 「법률에서는 별도로 규정되지 않았으나 그룹 내 계열사의 전략적 경영의사결정을 담당하는 그룹경영협의회와 … 그룹리스크관리협의회를 별도로 운영」 문장이 있음'
    nx = {2023: ('11. 그룹리스크관리협의회', '12. 감독당국 권고사항'), 2024: ('11. 그룹리스크관리협의회', '12. 감독당국 권고사항'),
          2025: ('12. 그룹리스크관리협의회', '13. 감독당국 권고사항')}
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹경영협의회', doc=('AR', yr),
            src=S('당사의 그룹경영협의회는 당사 및 자회사 등에 대한 전략적 경영의사결정을 위한', upto='나. 협의 절차'),
            chair=S('당사의 그룹경영협의회는 지주회사 대표이사를 위원장으로 하며'),
            members=S('당사의 그룹경영협의회는 지주회사 대표이사를 위원장으로 하며', upto='라. 활동내역'),
            agenda=S('1) 활동내역 개요', upto=nx[fy][0], after='당사의 그룹경영협의회는 지주회사 대표이사를 위원장으로 하며'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=ov + ' / cadence_text: 「나. 협의 절차」에 주기 글 없음(소집 전 사전 통보·관계인 출석만) — 찾은 범위: 연차보고서 「그룹경영협의회」 절·첨부 그룹경영협의회규정 목차' +
                 (' / ' + FY23_AR_NOTE if fy == 2023 else ''),
            na_note_given=True))
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹리스크관리협의회', doc=('AR', yr),
            src=S('그룹리스크관리협의회(이하 “협의회”라 한다)는 리스크관리 정책 및 절차를', '역할을 수행합니다.'),
            cadence=S('본 협의회는 분기', '서면으로 운영할 수 있습니다.', after=['그룹리스크관리협의회(이하 “협의회”라 한다)는', '나. 협의절차']),
            chair=S('위원장은 그룹리스크관리책임자로 합니다.'),
            members=S('본 협의회는 그룹리스크관리책임자와 자회사 등의', upto='라. 활동내역'),
            agenda=S('1) 활동내역 개요', upto=nx[fy][1], after='본 협의회는 그룹리스크관리책임자와 자회사 등의'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=ov + ' / 같은 협의회를 사업보고서 Ⅱ 「마. 위험관리정책에 관한 사항」 표·Ⅲ 주석(금융위험의 관리)에도 적음 — 연차보고서 글을 기준으로 함' +
                 (' / ' + FY23_AR_NOTE if fy == 2023 else '')))
    for yr in (2024, 2025):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='내부통제위원회', doc=('AR', yr),
            src=S('당사는 이사회 내 위원회와는 별도로', '보호하는 것을 목적으로 하고 있습니다.'),
            chair=S('대표이사를 위원장으로 하는 내부통제위원회를 구성∙운영하고 있습니다.'),
            note='(이사회 내 위원회 아님) 원문 「이사회 내 위원회와는 별도로 「금융회사의 지배구조에 관한 법률 시행령」 제19조 제2항에 의거, 대표이사를 위원장으로 하는 내부통제위원회」 — 연차보고서 「1. 지배구조 일반」 문단. 같은 쪽 지배구조 현황 요약 표에 「내부통제 점검결과를 공유하고 개선방안을 검토하며, 내부통제 취약부문에 대한 점검 및 대응방안을 마련」·위원장 김남구(사내)·근거 「내부통제위원회 운영지침」 칸이 있으나 PDF 글에서 두 칸 글이 섞여 이어진 글로 옮기지 않음. 구성원·주기·개최 횟수·안건 글은 찾은 범위(연차보고서 전문·사업보고서 Ⅱ·Ⅵ 「내부통제위원회」)에 없음. FY2025 연차보고서에는 이 문단이 없고 2025.3.28 이사회 내 위원회로 내부통제위원회 설치(F2_g2.csv)'))
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제협의회', doc=('AR', 2026),
        src=S('3. 내부통제협의회를 소집한 경우 회의에서 결정된 사항'),
        note='연차보고서 FY2025 첨부 내부통제위원회 규정 「제6조(보고사항)」의 호에 이름만 나옴(위원회에 대한 보고사항). 구성·주재자·주기·개최 횟수·안건 글은 찾은 범위(연차보고서 FY2023~2025 전문·사업보고서 FY2023~2025 「내부통제협의회」)에 없음',
        na_note_given=True))
    # ── F-2 ──
    for fy in (2024, 2025):
        after = ['VI. 이사회 등 회사의 기관에 관한 사항', '2) 이사회내의 위원회 활동내역']
        comp = ['VI. 이사회 등 회사의 기관에 관한 사항', '1) 이사회내 위원회 구성현황']
        esg_next = '■ 내부통제위원회 활동내역' if fy == 2025 else '마. 사외이사의 전문성'
        esg_mem_next = '내부통제위원회 | 사외이사' if fy == 2025 else '2) 이사회내의 위원회 활동내역'
        nt = '(판단) 안건 목록은 사업보고서 Ⅵ 위원회 활동 표를 씀 — 연차보고서(본공시)에 같은 위원회 절의 회의 개최내역이 있음 / members_text 는 Ⅵ 「1) 이사회내 위원회 구성현황」 표의 그 위원회 행(기간별 2행: 앞 행 설치목적 칸 포함 그대로)'
        F2_SPECS.append(dict(co=co, fy=fy, committee='리스크관리위원회', doc=('BR', fy),
                             agenda=S('■ 리스크관리위원회', upto='■ 보상위원회', after=after),
                             members=S('리스크관리위원회 | 상근이사', upto='보상위원회 | 상근이사', after=comp), note=nt))
        F2_SPECS.append(dict(co=co, fy=fy, committee='감사위원회', doc=('BR', fy),
                             agenda=S('다. 감사위원회(감사)의 주요활동내역', upto='라. 감사위원회 교육실시 계획', after='2. 감사제도에 관한 사항'),
                             members=S('감사위원회 | 사외이사 3명', upto='임원후보추천위원회 | 상근이사', after=comp),
                             established=S('감사위원회 설치', after='1) 감사위원회 설치', e='감사위원회 설치') if False else S('2003.01.11 감사위원회 설치'),
                             note=nt.replace('Ⅵ 위원회 활동 표', 'Ⅵ 「2. 감사제도에 관한 사항 > 다. 감사위원회(감사)의 주요활동내역」 표') + ' / established 는 Ⅵ 「2. 나. 1) 감사위원회 설치」 표 글'))
        F2_SPECS.append(dict(co=co, fy=fy, committee='ESG위원회', doc=('BR', fy),
                             agenda=S('■ ESG위원회 활동내역', upto=esg_next, after=after),
                             members=S('ESG위원회 | 상근이사', upto=esg_mem_next, after=comp), note=nt))
        F2_SPECS.append(dict(co=co, fy=fy, committee='자회사대표이사후보추천위원회', doc=('BR', fy),
                             note=f'사업보고서 FY{fy} Ⅵ 「1) 이사회내 위원회 구성현황」 표의 위원회는 경영위원회·리스크관리위원회·보상위원회·감사위원회·임원후보추천위원회·ESG위원회' + ('·내부통제위원회' if fy == 2025 else '') +
                             ' — 자회사 대표이사 후보 추천을 맡는 위원회 이름 없음. 임원후보추천위원회 설치목적 칸 원문 「사외이사, 대표이사, 감사위원 후보를 선정하여 …」. 찾은 범위: ' + BR_VI_SEARCH + '(「자회사」「후보추천」)'))
    F2_SPECS.append(dict(co=co, fy=2025, committee='내부통제위원회', doc=('BR', 2025),
                         agenda=S('■ 내부통제위원회 활동내역', upto='마. 사외이사의 전문성', after=['VI. 이사회 등 회사의 기관에 관한 사항', '2) 이사회내의 위원회 활동내역']),
                         members=dict(row='내부통제위원회', after=['VI. 이사회 등 회사의 기관에 관한 사항', '1) 이사회내 위원회 구성현황'], ncell=3),
                         established=S('2025.3.28 개최된 제 7차 이사회 승인을 통해 이사회 내 위원회로 내부통제위원회를', '설치하였습니다.', doc=('AR', 2026)),
                         note='(판단) 안건 목록은 사업보고서 Ⅵ 위원회 활동 표를 씀 — 연차보고서 FY2025 「10. 내부통제위원회」 절에 같은 회의 개최내역이 있음. 사업보고서 FY2025 이사회 표 제7차(2025.03.28) 의안 「사규 제·개정 및 이사회내 위원회 설치 (내부통제위원회)」'))
    F2_SPECS.append(dict(co=co, fy=2024, committee='내부통제위원회', doc=('BR', 2024),
                         note='사업보고서 FY2024 Ⅵ 이사회내 위원회 구성 표·활동 표에 내부통제위원회 없음(찾은 범위: ' + BR_VI_SEARCH + ' 「내부통제위원회」). 연차보고서 FY2024 의 「내부통제위원회」는 이사회 내 위원회와 별도의 대표이사 위원장 위원회(F_g2.csv 행). 이사회 내 위원회 설치는 2025.3.28(연차보고서 FY2025)'))
    # ── F-3 ──
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026),
                         function=S('라. 감사보조조직 등'),
                         unit=S('윤리경영지원실', after=['라. 감사보조조직 등', '당사는 감사위원회 산하에']),
                         hc=S('윤리경영지원실장(전무)과 감사인 5명', after='라. 감사보조조직 등'),
                         hc_val=('6', '(판단) 원문에 합계 숫자가 없어 실장 1명과 감사인 5명을 더함'),
                         duty=S('당사는 감사위원회 산하에 윤리경영지원실을 감사보조조직으로 두어', '감사 결과를 감사위원회에 보고하고 있습니다.', after='라. 감사보조조직 등'),
                         note=AUDIT_PARA_NOTE))
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026), unit=None, cmp14='준법지원인 등 지원',
                         note=COMP_NA_NOTE + ' 사업보고서 FY2025 Ⅵ 「바. 준법감시인에 관한 사항 > 3) 준법지원인 등 지원조직 현황」 표 있음.'))


SPEC_FUNCS.append(spec_HT)


IM_RC_CHAIR = {2023: S('신현진 DGB금융지주 CRO', '의장', after='<DGB금융지주 위험관리협의회 구성>'),
               2024: S('박병수 DGB금융지주 CRO', '의장', after='<DGB금융지주 위험관리협의회 구성>'),
               2025: S('iM금융지주 CRO', '의장', after='<iM금융지주 위험관리협의회 구성>')}


def spec_IM():
    co = 'iM금융지주'
    pre = {2023: 'DGB금융지주', 2024: 'DGB금융지주', 2025: 'iM금융지주'}
    num = {2023: (12, 13, '14. 감독당국 권고사항'), 2024: (13, 14, '15. 감독당국 권고사항'), 2025: (13, 14, '15. 감독당국 권고사항')}
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        a, b, nxt = num[fy]
        dg = ' / 연차보고서 FY2023·FY2024 는 옛 이름 DGB금융지주로 적힘' if fy < 2025 else ''
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹경영관리협의회', doc=('AR', yr),
            src=S(f'{pre[fy]}는 지주회사 및 자회사', upto='나. 협의절차'),
            chair=S('위원장(회장)', after=f'{pre[fy]}는 지주회사 및 자회사'),
            cadence=S('그룹경영관리협의회는 분기 1회 개최함을 원칙으로 하며', '수시 소집이 가능합니다.'),
            members=S('그룹경영관리협의회는 회장', upto='라. 활동'),
            agenda=S('그룹경영관리협의회는 2015년 2월에 신설되어', upto=f'{b}. 위험관리협의회'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='chair_text 는 「가. 역할」 논의사항 (6) 안의 글(위원장이 회장임을 적은 곳); 구성 표에도 회장 행 비고 「위원장」' + dg +
                 ' / 사업보고서 Ⅱ·Ⅵ 에는 이 협의회 서술 없음(FY2024 사업보고서에 이름만 1곳)' + (' / ' + FY23_AR_NOTE if fy == 2023 else '')))
        F_SPECS.append(dict(
            co=co, fy=fy, body='위험관리협의회', doc=('AR', yr),
            src=S('위험관리협의회는 그룹과 자회사 리스크정책 및 전략을 일관되게', '사전심의 기능을 수행하고 있습니다.'),
            cadence=S('위험관리협의회는 분기 1회 소집을 원칙으로 하되', '수시 소집할 수 있습니다.'),
            members=S('위험관리협의회는', upto=('<2023년 DGB금융지주 위험관리협의회 활동내역>' if fy == 2023 else '라. 활동'), after=['위험관리협의회는 분기 1회 소집을 원칙으로 하되', '다. 구성']),
            agenda=S(('<2023년 DGB금융지주 위험관리협의회 활동내역>' if fy == 2023 else '라. 활동'), upto=nxt, after=['위험관리협의회는 분기 1회 소집을 원칙으로 하되', '다. 구성']),
            held=('count', 'agenda_text', r'\((20\d\d\.\d\d\.\d\d)\)'),
            chair=IM_RC_CHAIR[fy],
            note='chair_text 는 구성 표에서 비고 칸이 「의장」인 행 글(검증 때 고침 — 주재자 문장은 없음)' +
                 (' — FY2025 표 그 행 글은 「iM금융지주 CRO 2024.04.08 2026.04.07 의장」으로 이름 글이 없음(바로 뒤 「박병수」는 다음 글 「iM뱅크 CRO1)」 앞에 나옴)' if fy == 2025 else '') +
                 ' / 같은 협의회를 사업보고서 Ⅱ 위험관리 서술·Ⅲ 주석에도 적음 — 연차보고서 글을 기준으로 함' + dg +
                 (' / ' + FY23_AR_NOTE if fy == 2023 else ''),
            na_note_given=False))
    # ESG경영협의회(이름만)
    F_SPECS.append(dict(co=co, fy=2023, body='ESG경영협의회', doc=('AR', 2024),
                        src=S('결의 안건은 ESG경영협의회 규정 개정', '모두 가결되었습니다.'),
                        note='연차보고서 FY2023 「11. ESG위원회」 활동내역 개요 문장에 ESG위원회 결의 안건 이름(「ESG경영협의회 규정 개정」)으로만 나옴. 사업보고서 Ⅵ 위원회 표 ESG위원회 권한 「2. ESG경영협의회 규정의 제정 및 개폐」. 구성·주재자·주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「ESG경영협의회」)에 없음',
                        na_note_given=True))
    for yr in (2025, 2026):
        F_SPECS.append(dict(co=co, fy=yr - 1, body='ESG경영협의회', doc=('AR', yr),
                            src=S('2. ESG경영협의회 규정의 제정 및 개폐'),
                            note='연차보고서 ESG위원회 권한(심의·의결 사항) 목록에 「ESG경영협의회 규정의 제정 및 개폐」로 이름만 나옴(사업보고서 Ⅵ 위원회 표 ESG위원회 권한 칸도 같은 글). 구성·주재자·주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「ESG경영협의회」)에 없음',
                            na_note_given=True))
    F_SPECS.append(dict(co=co, fy=2025, body='그룹 위기관리협의회', doc=('AR', 2026),
                        src=S('5. 그룹 위기관리협의회 운영 결과 보고 특이의견 없음'),
                        note='연차보고서 FY2025 「9. 위험관리위원회」 회의별 내역(보고 안건에 대한 의견)에 보고 안건 이름으로만 나옴. 사업보고서 FY2025 Ⅵ 위원회 활동 표 위험관리위원회 「8. 그룹 위기관리협의회 운영 결과 보고」. 구성·주재자·주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「위기관리협의회」)에 없음',
                        na_note_given=True))
    tbl = '사업보고서 FY2025 Ⅵ 「2. 감사제도에 관한 사항」 「(2) 준법감시인의 주요활동내역 및 그 처리결과」 표(칸: 점검일시 | 주요 점검내용 | 점검결과)의 행 — cadence_text 는 그 행 「점검일시」 칸 글. FY2023·FY2024 같은 표에는 이 협의회 이름 없음. 구성·주재자·개최 횟수 글은 찾은 범위(사업보고서·연차보고서 FY2023~2025)에 없음'
    for body in ('그룹 준법감시인협의회', '그룹 금융소비자보호협의회'):
        F_SPECS.append(dict(co=co, fy=2025, body=body, doc=('BR', 2025),
                            src=S('분기 | 그룹 준법감시인협의회/그룹 금융소비자보호협의회 | 적정함'),
                            cadence=S('분기', after='수시 | 자회사 준법감시업무 점검'),
                            note=tbl + '. 한 칸에 「그룹 준법감시인협의회/그룹 금융소비자보호협의회」로 함께 적힘(이름은 「/」로 나눔)', na_note_given=True))
    F_SPECS.append(dict(co=co, fy=2025, body='내부통제협의회', doc=('BR', 2025),
                        src=S('수시 | 내부통제위원회/내부통제협의회 | 적정함'),
                        cadence=S('수시', after='분기 | 그룹 준법감시인협의회/그룹 금융소비자보호협의회 | 적정함'),
                        note=tbl + '. 한 칸에 「내부통제위원회/내부통제협의회」로 함께 적힘(내부통제위원회는 이사회 내 위원회라 F-2). 같은 Ⅵ 「(3) 준법감시인 등 지원조직 현황」 표 준법지원부 활동 칸 「내부통제위원회, 내부통제협의회 운영 등」',
                        na_note_given=True))
    # ── F-2 ──
    order = ['보수위원회', '위험관리위원회', '감사위원회', '그룹임원후보추천위원회', '회장후보추천위원회', '사외이사후보추천위원회', '감사위원후보추천위원회', 'ESG위원회', '내부통제위원회']
    first_cell = {'보수위원회': '사외이사', '위험관리위원회': '사외이사', '감사위원회': '사외이사', '그룹임원후보추천위원회': '상임이사',
                  '회장후보추천위원회': '사외이사', '사외이사후보추천위원회': '사외이사', '감사위원후보추천위원회': '사외이사', 'ESG위원회': '상임이사', '내부통제위원회': '사외이사'}
    for fy in (2024, 2025):
        comp = ['다. 이사회내 위원회', '(1) 위원회별 명칭']
        act = ['다. 이사회내 위원회', '(2) 위원회의 활동내용']
        names = order if fy == 2025 else order[:-1]

        def mem(n):
            i = names.index(n)
            up = (names[i + 1] + ' | ' + first_cell[names[i + 1]]) if i + 1 < len(names) else '(2) 위원회의 활동내용'
            return S(n + ' | ' + first_cell[n], upto=up, after=comp)
        nt = '(판단) 안건 목록은 사업보고서 Ⅵ 「(2) 위원회의 활동내용」 표(여러 위원회가 한 표)에서 이 위원회 덩어리(머리행 포함)를 씀 — 연차보고서(본공시)에 같은 위원회 절의 회의별 서술이 있음 / members_text 는 Ⅵ 「(1) 위원회별 명칭, 이사의 성명, 설치목적과 권한」 표의 그 위원회 행(기간별 행·설치목적 칸 포함 그대로)'
        for com, extra in (('위험관리위원회', ''), ('감사위원회', ''), ('ESG위원회', ''),
                           ('그룹임원후보추천위원회', ' / 자회사대표이사후보추천위원회에 해당하는 iM 위원회(원문 이름) — 구성 표 설치목적 칸 「1. 자회사 최고경영자 후보 추천」')):
            F2_SPECS.append(dict(co=co, fy=fy, committee=com, doc=('BR', fy),
                                 agenda=dict(block=com, after=act, upto='라. 이사의 독립성'),
                                 members=mem(com), note=nt + extra))
    F2_SPECS.append(dict(co=co, fy=2025, committee='내부통제위원회', doc=('BR', 2025),
                         agenda=dict(block='내부통제위원회', after=['다. 이사회내 위원회', '(2) 위원회의 활동내용'], upto='라. 이사의 독립성'),
                         members=S('내부통제위원회 | 사외이사', upto='(2) 위원회의 활동내용', after=['다. 이사회내 위원회', '(1) 위원회별 명칭']),
                         est_note='established: 설치일 글 없음(찾은 범위: 사업보고서 FY2025 Ⅵ·연차보고서 FY2025 「설치」「신설」) — 사업보고서 FY2025 이사회 표 2025.02.07 회의 의안 「12. 내부통제위원회 구성(안)」 가결, 구성 표 첫 기간 「사외이사 3명(2025년 2월 ~ 2025년 3월)」',
                         note='(판단) 안건 목록은 사업보고서 Ⅵ 「(2) 위원회의 활동내용」 표의 이 위원회 덩어리 — 연차보고서 FY2025 「10. 내부통제위원회」 절에 회의별 서술이 있음'))
    F2_SPECS.append(dict(co=co, fy=2024, committee='내부통제위원회', doc=('BR', 2024),
                         note='사업보고서 FY2024 Ⅵ 「(2) 이사회내의 위원회 명칭」 목록·구성 표·활동 표에 내부통제위원회 없음(찾은 범위: 사업보고서 FY2024 Ⅵ·연차보고서 FY2024, 검색어 「내부통제위원회」). 연차보고서 FY2024 「10. 내부통제위원회」 절: 구성 「지배구조법 부칙 제5조의 경과조치에 따라 법 시행 이후 최초로 소집되는 주주총회일까지 설치 예정입니다.」, 활동내역 「“해당사항 없음”」 / 같은 연차보고서 첨부 정관 위원회 조항 목록 「9.내부통제위원회(신설2024.03.28.)」, 다른 첨부 규정 목록 「내부통제위원회(신설2024.10.18.)」; 사업보고서 FY2024 Ⅰ 정관 변경 표 「2024.03.28 제13기 정기주주총회 1.내부통제위원회 신설(45조)」 — 조항 신설 글이고 FY2024 위원회 구성·개최 글은 없음'))
    # ── F-3 ──
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026),
                         function=S('라. 감사보조조직 등'),
                         unit=S('검사부', after='라. 감사보조조직 등'),
                         hc=S('총 6명(그룹감사총괄 1명, 부장 1명, 검사역 4명)', after='라. 감사보조조직 등'),
                         duty=S('iM금융지주는 감사업무의 실질적인 운영과 효율성 제고를 위하여', '활동 내용을 감사위원회에 보고하였습니다.', after='라. 감사보조조직 등'),
                         note=AUDIT_PARA_NOTE))
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026), unit=None, cmp14='준법감시인 지원',
                         note=COMP_NA_NOTE + ' 사업보고서 FY2025 Ⅵ 「(3) 준법감시인 등 지원조직 현황」 표 있음. 연차보고서 FY2025 「기타 지배구조 관련 주요사항」 「나. 인사 관련 내부통제 현황」에 「2) 준법감시직원 현황 - 해당사항 없음」(p.136 섹션)이 있음(검증 때 더한 사실).'))


SPEC_FUNCS.append(spec_IM)


def spec_BNK():
    co = 'BNK금융지주'
    rn = '연차보고서 「가.역할」: 「2015년 2월부터 설치하였으며, 2023년 4월 명칭을 그룹경영위원회로 변경」(FY2024·FY2025). body_name 은 그해 연차보고서 절 제목 원문'
    # 그룹경영관리협의회(FY2023·FY2024) / 그룹경영위원회(FY2025)
    gm = {2023: ('그룹경영관리협의회', '동 협의회는', '협의회의 위원은 당사 회장(의장) 및', S('(1)개요', '제2호 : 2024년 그룹 경영계획(안)4.보고사항-', after=['협의회의 위원은 당사 회장(의장) 및', '라.활동내역 개요'])),
          2024: ('그룹경영관리협의회', '동 위원회는', '위원회의 위원은 당사 회장(의장) 및', S('(1)개요', '4.보고사항 -', after=['위원회의 위원은 당사 회장(의장) 및', '라.활동내역 개요'])),
          2025: ('그룹경영위원회', '동 위원회는', '위원회의 위원은 당사 회장(의장) 및', S('(1)개요', '4.보고사항 -', after=['위원회의 위원은 당사 회장(의장) 및', '라.활동내역 개요']))}
    for fy, (body, dong, mem, ag) in gm.items():
        F_SPECS.append(dict(
            co=co, fy=fy, body=body, doc=('AR', fy + 1),
            src=S('당사는 지주회사와 자회사의 경영의사결정을 지원하기 위해', '경영의사결정을 지원하는 역할을 수행하고 있습니다.'),
            chair=S(f'{dong} 의장인 당사 회장이 회의를 소집하며'),
            cadence=S(f'{dong} 의장인 당사 회장이 회의를 소집하며', '수시로 회의를 소집할 수 있습니다.'),
            members=S(mem, upto='라.활동내역 개요'),
            agenda=ag, held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=rn + ' / 사업보고서 Ⅱ·Ⅵ 에는 이 협의회 서술 없음(찾은 범위: 사업보고서 FY2023~2025 「그룹경영」)' + (' / ' + FY23_AR_NOTE if fy == 2023 else '') +
                 (' / agenda_text 원문에 「2025년 그룹경영관리위원회는 총 1회」로 적힘' if fy == 2025 else '')))
    # 리스크관리협의회
    rk = {2023: ('12 리스크관리협의회', '윤석준 BNK금융지주 위험관리책임자', "BNK자산운용의 그룹 공동 해외투자 부동산 현황 보고('23.11월)-"),
          2024: ('13 리스크관리협의회', '윤석준 BNK금융지주 위험관리책임자', '캐피탈 및 저축은행 소매신용평가모형 적합성검증 결과 -'),
          2025: ('13 리스크관리협의회', '김주성 BNK금융지주 위험관리책임자', '[협의] 2026 년도 자회사 리스크관리 제한도 배분(안) -')}
    for fy, (hd, ch, last) in rk.items():
        F_SPECS.append(dict(
            co=co, fy=fy, body='리스크관리협의회', doc=('AR', fy + 1),
            src=S('당사는 「리스크관리규정」 제10조에 의거', upto='나.협의절차', after=hd),
            cadence=S('리스크관리협의회는 분기 1회 이상 개최를 원칙으로', '서면으로 운영할 수 있습니다.'),
            members=S('리스크관리협의회는 지주회사 위험관리책임자', upto='라.활동내역 개요'),
            chair=S(ch, '위원장', after='<리스크관리협의회 구성>'),
            agenda=S(f'리스크관리협의회는 {fy}년 중 총', last),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='chair_text 는 구성 표의 위원장 행 / 같은 협의회를 사업보고서 Ⅱ 위험관리 서술(리스크관리 조직)에도 적음 — 연차보고서 글을 기준으로 함' +
                 (' / 구성 표에 「윤석준」이 BNK금융지주 위험관리책임자 행과 부산은행 위험관리책임자 행에 함께 나옴 — 출생년월 글이 없어 같은 사람인지 문서로 알 수 없음' if fy == 2024 else '') +
                 (' / ' + FY23_AR_NOTE if fy == 2023 else '')))
    # 사업보고서 Ⅵ 준법지원인 활동 표의 회의체(FY2023~2025)
    tb = '사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「준법지원인 주요 활동내역 및 그 처리결과」 표(칸: 구분 | 점검일시 | 주요 점검내용 | 점검결과)의 「내부통제체제 총괄」 행 — cadence_text 는 그 행 「점검일시」 칸 글. 한 칸에 「내부통제위원회, 내부통제협의회, 그룹준법감시인 간담회 운영」으로 함께 적힘. 구성·주재자·개최 횟수 글은 찾은 범위(사업보고서·연차보고서 FY2023~2025 같은 이름)에 없음'
    for fy in (2023, 2024, 2025):
        row = '반기 | ○내부통제 위원회, 내부통제 협의회, 그룹준법감시인 간담회 운영 | 선제적 내부통제 점검 및 문제점 개선' if fy == 2023 else \
              '반기 | ○내부통제위원회, 내부통제협의회, 그룹준법감시인 간담회 운영 | 선제적 내부통제 점검 및 문제점 개선'
        bodies = [('내부통제협의회', ''), ('그룹준법감시인 간담회', '')]
        if fy < 2025:
            bodies.insert(0, ('내부통제위원회', f'(판단) 사업보고서 FY{fy} Ⅵ 이사회 내 위원회 목록에 내부통제위원회가 없어(이사회 내 내부통제위원회는 2025.3 정기주주총회 정관 변경 뒤 구성) 이 표의 「내부통제위원회」를 이사회 내 위원회가 아닌 회의체로 보고 F 에 넣음. '))
        for body, pre in bodies:
            F_SPECS.append(dict(co=co, fy=fy, body=body, doc=('BR', fy), src=S(row),
                                cadence=S('반기', after='○각 자회사의 내부통제 현황 보고'),
                                note=pre + tb + (' (FY2023 원문은 「내부통제 위원회, 내부통제 협의회」 띄어 씀)' if fy == 2023 else ''), na_note_given=True))
    F_SPECS.append(dict(co=co, fy=2025, body='그룹 금융소비자보호협의회', doc=('BR', 2025),
                        src=S('○그룹 금융소비자보호협의회 운영'),
                        note='사업보고서 FY2025 Ⅵ 「(2) 준법지원인 등 지원조직 현황」 표 금융소비자보호부 주요 활동 칸에 「○그룹 금융소비자보호협의회 운영」으로 이름만 나옴. 구성·주재자·주기·개최 횟수 글은 찾은 범위(사업보고서·연차보고서 FY2023~2025 「금융소비자보호협의회」)에 없음', na_note_given=True))
    for fy in (2023, 2024):
        F_SPECS.append(dict(co=co, fy=fy, body='그룹 ESG실무협의회', doc=('AR', fy + 1),
                            src=S('그룹 ESG실무협의회 운영'),
                            note='연차보고서 「ESG위원회」 회의 내역의 보고안건 설명(그룹 ESG 관련 주요 현안 보고)에 이름만 나옴. 구성·주재자·주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「ESG실무협의회」)에 없음. FY2025 연차보고서에는 이 이름 없음', na_note_given=True))
    F_SPECS.append(dict(co=co, fy=2025, body='BNK부울경지역형 생산적금융협의회', doc=('BR', 2025),
                        src=S('2025.10.14 BNK부울경지역형 생산적금융협의회 출범'),
                        note='사업보고서 FY2025 「I. 회사의 개요」 연혁 줄에 출범만 나옴(그룹 밖 기관이 함께하는지 등 구성 글 없음). 구성·주재자·주기·개최 횟수·안건 글은 찾은 범위(사업보고서·연차보고서 FY2025 「생산적금융협의회」)에 없음', na_note_given=True))
    # ── F-2 ──
    blk = {2024: ['(나) 리스크관리위원회', '(다) 보수위원회', '(라) 감사위원회', '(마) 임원후보추천위원회', '(바) ESG위원회', '(사) 자회사CEO후보추천위원회', '라. 이사(감사위원회 위원 포함)의 독립성'],
           2025: ['(나) 리스크관리위원회', '(다) 보수위원회', '(라) 감사위원회', '(마) 임원후보추천위원회', '(바) ESG위원회', '(사) 자회사CEO후보추천위원회', '(아)내부통제위원회', '라. 이사(감사위원회 위원 포함)의 독립성']}
    memb = {'리스크관리위원회': '보수위원회 |', '감사위원회': '임원후보추천위원회 |', 'ESG위원회': '자회사CEO후보추천위원회 |',
            '자회사CEO후보추천위원회': {2024: '주1)ESG위원회 및 자회사CEO후보추천위원회를 제외한', 2025: '내부통제위원회 |'}, '내부통제위원회': '1)자회사CEO후보추천위원회를 제외한'}
    nt = '(판단) 안건 목록은 사업보고서 Ⅵ 「(2) 위원회 활동내용」 표를 씀 — 연차보고서(본공시)에 같은 위원회 절의 회의별 서술이 있음 / members_text 는 Ⅵ 「(1) 위원회 구성 현황」 표의 그 위원회 행(기간별 행·목적 칸 포함 그대로)'
    for fy in (2024, 2025):
        hs = blk[fy]
        for com, i in (('리스크관리위원회', 0), ('감사위원회', 2), ('ESG위원회', 4), ('자회사CEO후보추천위원회', 5)) + ((('내부통제위원회', 6),) if fy == 2025 else ()):
            up = memb[com][fy] if isinstance(memb[com], dict) else memb[com]
            F2_SPECS.append(dict(co=co, fy=fy, committee=com, doc=('BR', fy),
                                 agenda=S(hs[i], upto=hs[i + 1], after='(2) 위원회 활동내용'),
                                 members=S(com + ' |', upto=up, after='(1) 위원회 구성 현황'),
                                 est_note=('established: 설치일 글 없음(찾은 범위: 사업보고서 FY2025 Ⅵ·연차보고서 FY2025 「설치」「신설」) — 연차보고서 FY2025 「2025년 2월 개최된 제2차 이사회에서 ‘정관 일부 변경(안)’의 건을 의결 … 내부통제위원회를 신설하고, 이사회 내 위원회에 내부통제위원회를 추가하여 기존 7개에서 8개의 위원회로 구성 … 2025년 3월 개최된 정기주주총회에서 이러한 정관 일부 변경(안)이 승인」, 구성 표 첫 기간 「\'25.03.26~\'25.12.31」' if com == '내부통제위원회' else
                                          'established: 찾은 범위(사업보고서 Ⅵ 1. 이사회에 관한 사항·연차보고서 해당 위원회 절, 검색어 「설치」「신설」「설립」)에 설치일 없음'),
                                 note=nt + (' / 감사위원회 활동은 Ⅵ 「2. 감사제도에 관한 사항 > (3) 감사위원회 활동」 표에도 있음(같은 회의)' if com == '감사위원회' else '') +
                                 (' / 자회사대표이사후보추천위원회에 해당하는 BNK 위원회 이름(원문)' if com.startswith('자회사CEO') else '')))
    F2_SPECS.append(dict(co=co, fy=2024, committee='내부통제위원회', doc=('BR', 2024),
                         note='사업보고서 FY2024 Ⅵ 「(1) 위원회 구성 현황」·「(2) 위원회 활동내용」에 내부통제위원회 없음(찾은 범위: 사업보고서 FY2024 Ⅵ·연차보고서 FY2024, 검색어 「내부통제위원회」). 연차보고서 FY2024 첨부 다른 규정(이사회내위원회 조항) 목록에 「내부통제위원회(2024.12.18신설)」(규정 조항 글). 연차보고서 FY2024 「11.내부통제위원회」 절: 「당사는 2024년 12월 18일 제8차 이사회에서 내부통제위원회규정 제정을 결의하였고, 2025년 3월 정기주주총회일부터 시행 예정입니다. 그에 따라 내부통제위원회 구성과 활동내역 및 평가는 ’25년말 기준 연차보고서부터 공시할 예정입니다.」(확인_F_g2.csv BNK-1)'))
    # ── F-3 ──
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026),
                         function=S('라.감사보조조직 등', after='다.활동내역 및 평가'),
                         unit=S('검사부', after='당사는 감사업무의 실질적 운영과 효율성 제고를 위해'),
                         hc=S('감사담당 임원 1명(2024.1.1 신규 선임), 검사부장 1명 및 검사원 4명'),
                         hc_val=('6', '(판단) 원문에 합계 숫자가 없어 감사담당 임원 1명·검사부장 1명·검사원 4명을 더함'),
                         duty=S('당사는 감사업무의 실질적 운영과 효율성 제고를 위해 감사위원회 산하 감사보조', '감사업무를 수행하고 있습니다.'),
                         note=AUDIT_PARA_NOTE + ' / 사업보고서 FY2025 Ⅵ 「(7) 감사위원회 지원조직 현황」 표 있음'))
    F3_SPECS.append(dict(co=co, fy=2025, doc=('AR', 2026), unit=None, cmp14='준법',
                         note=COMP_NA_NOTE + ' 사업보고서 FY2025 Ⅵ 「(2) 준법지원인 등 지원조직 현황」 표 있음.'))
    # ── 확인(함께 볼 것: BNK 내부통제위원회 첫 개최일·첫 안건 FY2024) ──
    CHK_SPECS.extend([
        dict(item_id='F2-BNK-1', co=co, fy=2024, doc=('AR', 2025), result='문서에 없음',
             src=S('당사는 2024년 12월 18일 제8차 이사회에서 내부통제위원회규정 제정을 결의', '’25년말 기준 연차보고서부터 공시할 예정입니다.'),
             where='F2_g2.csv BNK금융지주 FY2024 내부통제위원회 행(문서에 없음) — 연차보고서 FY2024 「11.내부통제위원회」 나.구성',
             note='FY2024 중 내부통제위원회 개최 기록 없음: 연차보고서 FY2024 는 규정 제정 결의(2024.12.18 제8차 이사회)와 2025년 3월 정기주주총회일부터 시행 예정만 적음. 사업보고서 FY2024 Ⅵ 위원회 구성·활동 표에 내부통제위원회 없음. 사업보고서 FY2024 이사회 표 2024.12.18 제8차 의안은 「4.지배구조 관련 내규 제정 및 개정(안)」(내부통제위원회규정 이름은 그 칸에 없음)'),
        dict(item_id='F2-BNK-2', co=co, fy=2025, doc=('BR', 2025), result='원문 있음',
             src=S('| 1 | 2025.03.26 | <결의안건> |', '1.위원장 선임(안)', after='(아)내부통제위원회'),
             where='F2_g2.csv BNK금융지주 FY2025 내부통제위원회 행(활동 표 첫 행)',
             note='첫 개최: 2025.03.26(1회차), 결의안건 「1.위원장 선임(안)」, 보고안건 「해당사항 없음」. 2회차 2025.04.25 「1.내부통제 기본방침 및 전략 수립」·「2.임직원의 직업윤리와 준법정신을 중시하는 조직문화의 정착방안 마련」'),
    ])


SPEC_FUNCS.append(spec_BNK)


JB25 = ('AR', 2026, '정정공시')
JB25_NOTE = '(판단) 연차보고서 FY2025 는 본공시(6차 섹션 공시연도 2026 본공시) 글이 PDF 글 추출에서 글자가 두 번씩 겹쳐 나와(예 「라라. 감사보조조직감사보조조직등등」) 같은 해 정정공시 글을 출처로 씀'
JB23_NOTE = '연차보고서 FY2023 은 PDF 글(pymupdf) — 같은 줄이 문장부호 없는 글과 있는 글로 두 번씩 나오는 곳이 많음(글 순서 그대로 옮김)'

# (검증 보완 2026-11-03) F-2 established: 연차보고서 첨부 규정의 위원회 목록 글 「<위원회>(…신설)」 — 그 연차보고서에서 처음 나오는 곳(첨부 정관 위원회 조항)을 씀.
# 같은 연차보고서의 다른 첨부 규정(지배구조내부규범·이사회규정 이사회내위원회 조항)에 다른 날짜가 있으면 note 에 적음(사실만).
_EST_PRE = 'established 는 연차보고서 첨부 정관 위원회 조항 목록 글(그 위원회 이름 뒤 괄호의 신설 날짜)'
EST = {
    ('iM금융지주', 2024, 'ESG위원회'): (S('ESG위원회(신설2021.03.26.)', doc=('AR', 2025)), _EST_PRE),
    ('iM금융지주', 2025, 'ESG위원회'): (S('ESG위원회(신설2021.03.26.)', doc=('AR', 2026)), _EST_PRE),
    ('iM금융지주', 2025, '내부통제위원회'): (S('내부통제위원회(신설2024.03.28.)', doc=('AR', 2026)),
                                      _EST_PRE + ' — 같은 연차보고서 첨부 다른 규정(이사회내위원회 조항)에는 「내부통제위원회(신설2024.10.18.)」. 사업보고서 FY2025 이사회 표 2025.02.07 의안 「12. 내부통제위원회 구성(안)」 가결, 구성 표 첫 기간 「사외이사 3명(2025년 2월 ~ 2025년 3월)」'),
    ('BNK금융지주', 2024, 'ESG위원회'): (S('ESG위원회(2021.3.26신설)', doc=('AR', 2025)), _EST_PRE),
    ('BNK금융지주', 2025, 'ESG위원회'): (S('ESG위원회(2021.3.26신설)', doc=('AR', 2026)), _EST_PRE),
    ('BNK금융지주', 2024, '자회사CEO후보추천위원회'): (S('자회사CEO후보추천위원회(2024.3.22신설)', doc=('AR', 2025)),
                                             _EST_PRE + ' — 같은 연차보고서 첨부 다른 규정(이사회내위원회 조항)에는 「자회사CEO후보추천위원회(2024.4.1신설)」'),
    ('BNK금융지주', 2025, '자회사CEO후보추천위원회'): (S('자회사CEO후보추천위원회(2024.3.22신설)', doc=('AR', 2026)),
                                             _EST_PRE + ' — 같은 연차보고서 첨부 다른 규정(이사회내위원회 조항)에는 「자회사CEO후보추천위원회(2024.4.1신설)」'),
    ('BNK금융지주', 2025, '내부통제위원회'): (S('내부통제위원회(2025.3.26신설)', doc=('AR', 2026)),
                                       _EST_PRE + ' — 같은 연차보고서 첨부 다른 규정(이사회내위원회 조항)에는 「내부통제위원회(2024.12.18신설)」. 연차보고서 FY2025 「2025년 2월 개최된 제2차 이사회에서 ‘정관 일부 변경(안)’의 건을 의결 … 2025년 3월 개최된 정기주주총회에서 이러한 정관 일부 변경(안)이 승인」, 구성 표 첫 기간 「\'25.03.26~\'25.12.31」'),
    ('JB금융지주', 2024, 'ESG위원회'): (S('ESG위원회(2021.3.31.신설)', doc=('AR', 2025)), _EST_PRE),
    ('JB금융지주', 2025, 'ESG위원회'): (S('ESG위원회(2021.3.31.신설)', doc=JB25), _EST_PRE + ' / ' + JB25_NOTE),
    ('JB금융지주', 2024, '자회사CEO후보추천위원회'): (S('자회사CEO후보추천위원회(2018.5.11신설)', doc=('AR', 2025)),
                                            'established 는 연차보고서 첨부 규범(「이 규범은 … 임원의 자격요건」) 제23조(이사회내위원회) 목록 글(첨부 정관 위원회 조항 목록은 「2.자회사CEO후보추천위원회」로 날짜 없음) — 같은 연차보고서 첨부 이사회규정 제15조(이사회내위원회) 목록은 「자회사CEO후보추천위원회(2018.5.11.신설)」'),
    ('JB금융지주', 2025, '자회사CEO후보추천위원회'): (S('자회사CEO후보추천위원회(2018.5.11신설)', doc=JB25),
                                            'established 는 연차보고서 첨부 규범(「이 규범은 … 임원의 자격요건」) 제23조(이사회내위원회) 목록 글(첨부 정관 위원회 조항 목록은 「2.자회사CEO후보추천위원회」로 날짜 없음) — 같은 연차보고서 첨부 이사회규정 제15조(이사회내위원회) 목록은 「자회사CEO후보추천위원회(2018.5.11.신설)」 / ' + JB25_NOTE),
}


def spec_JB():
    co = 'JB금융지주'
    docs = {2023: ('AR', 2024), 2024: ('AR', 2025), 2025: JB25}
    for fy in (2023, 2024, 2025):
        d = docs[fy]
        base = (JB25_NOTE if fy == 2025 else (JB23_NOTE if fy == 2023 else ''))
        F_SPECS.append(dict(
            co=co, fy=fy, body='경영협의회', doc=d,
            src=S('당사는 당사와 자회사간 원활한 의사소통과', '기타 의장이 필요하다고 인정하는 사항'),
            cadence=S('정기회의는 매월 1회 소집하고', '소집합니다.'),
            chair=S('협의회의 의장은 회장이 되며', '직무를 대행합니다.') if fy != 2023 else S('협의회의 의장은 회장이 되며'),
            members=(S('당사는 그룹 내 전략적 의사결정을 위하여 경영협의회를 설치하고', upto='라. 활동내역 개요') if fy != 2023 else
                     S('당사는 그룹 내 전략적 의사결정을 위하여 경영협의회를 설치하고', '총 7명으로 구성되어 있습니다')),
            agenda=S(f'당사 경영협의회는 {fy}년 중 총', '시너지 창출 극대화를 도모하고 있습니다.'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=' / '.join(x for x in [base, '사업보고서 Ⅱ·Ⅵ 에는 이 협의회 서술 없음(찾은 범위: 사업보고서 FY2023~2025 「경영협의회」)'] if x)))
        rk_end = {2023: None, 2024: '5. 양행 소매신용평가모형(AS) 재개발 결과 보고', 2025: '3. 리스크평가모형 사전 적합성검증 결과'}[fy]
        F_SPECS.append(dict(
            co=co, fy=fy, body='리스크관리운영위원회', doc=d,
            src=S('당사 리스크관리운영위원회는 리스크관리위원회에서 그 설치를 결정한', '(리스크관리규정§8)'),
            cadence=(S('리스크관리운영위원회는 분기 1회 이상 개최를 원칙으로', '(리스크관리운영위원회규정 §3ⅰ)') if fy != 2023 else
                     S('또한, 리스크관리운영위원회는 분기 1회 이상 개최를 원칙으로', '수시로 개최할 수 있습니다.')),
            chair=(S('이승국 지주사 CRO 2019.04.30 위원장') if fy != 2023 else S('지주사/광주은행CRO(겸직)', '위원장')),
            members=(S('당사는 리스크관리 업무의 효율적 수행을 위해 리스크관리운영위원회를 설치하여', upto='라. 활동내역 개요') if fy != 2023 else
                     S('당사는 리스크관리 업무의 효율적 수행을 위해 리스크관리운영위원회를 설치하여', upto='년에는 총 회의 리스크관리운영위원회가')),
            agenda=(S(f'{fy}년에는 총', rk_end, after='당사는 리스크관리 업무의 효율적 수행을 위해 리스크관리운영위원회를 설치하여') if fy != 2023 else
                    S('2023년에는 총 8회의 리스크관리운영위원회가 소집되었고', upto='감독당국권고사항및개선계획')),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note=' / '.join(x for x in [base, '(이사회 내 위원회 아님) 원문 「리스크관리위원회에서 그 설치를 결정한 의사결정기구」 — 지주 CRO 가 위원장, 자회사 CRO·리스크관리부장이 위원', '사업보고서 Ⅱ 위험관리 서술에도 「그룹 리스크관리운영위원회」가 나옴 — 연차보고서 글을 기준으로 함', 'chair_text 는 구성 표의 위원장 행'] if x)))
    for fy in (2023, 2024):
        F_SPECS.append(dict(
            co=co, fy=fy, body='집행위원회', doc=docs[fy],
            src=(S('이사회가 위임한 업무의 집행을 위하여 제1항의 위원회와는 별도로 집행위원회를 두고', '집행위원회의 조직 및 운영에 관한 사항은 이사회에서 정한다.') if fy == 2024 else
                 S('이사회가 위임한 업무의 집행을 위하여 제1항의 위원회와는 별도로 집행위원회를 두고')),
            note=' / '.join(x for x in [JB23_NOTE if fy == 2023 else '', '연차보고서 첨부 정관 조항(이사회 내 위원회 조항 ②항) 글. 사업보고서 Ⅵ 이사회 권한 표 보고사항 「2. 집행위원회 결의사항」, 이사회 안건 표에 분기마다 「… 집행위원회 결의사항」 보고가 있음. 구성·주재자·주기·개최 횟수·안건 글은 찾은 범위(연차보고서·사업보고서 「집행위원회」)에 없음'] if x),
            na_note_given=True))
    F_SPECS.append(dict(
        co=co, fy=2025, body='집행위원회', doc=JB25,
        src=S('⑤ 내부통제협의회규정 제정 등 2025년도 2분기 집행위원회 결의사항 보고'),
        note=JB25_NOTE + ' / 연차보고서 FY2025 이사회 회의 내역의 보고안건 글. 같은 해 분기마다 「… 2024년도 4분기·2025년도 1분기·3분기 집행위원회 결의사항 보고」 안건이 있음. 정관 조항 「제1항의 위원회와는 별도로 집행위원회를 두고」(첨부 정관). 구성·주재자·주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2025 「집행위원회」)에 없음',
        na_note_given=True))
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제협의회', doc=JB25,
        src=S('① 2025년 제1차 내부통제협의회', '원안대로'),
        note=JB25_NOTE + ' / 연차보고서 FY2025 「내부통제위원회」 회의 내역(2025.7 회의)의 보고 안건에 대한 의견 칸(「① 2025년 제1차 내부통제협의회 주요 운용현황 보고」로 글이 표 칸에 나뉨). 2025년도 2분기 집행위원회 결의사항에 「내부통제협의회규정 제정」. 사업보고서 FY2025 Ⅵ 내부통제위원회 활동 표 2025.07.24 보고안건 「1. 2025년 제1차 내부통제협의회 주요 운영현황」. 구성·주재자·주기 글은 찾은 범위(연차보고서·사업보고서 FY2025 「내부통제협의회」)에 없음. FY2023·FY2024 문서의 같은 이름(띄어 쓴 「내부통제 협의회」)은 사업보고서 Ⅵ 준법지원인 활동 표 행(이 조각의 FY2023·FY2024 「내부통제 협의회」 행). 사업보고서 FY2025 같은 표에는 「분기 | 내부통제 실무협의회 운영」 행이 있음(이 조각 「내부통제 실무협의회」 행)',
        na_note_given=True))
    # (검증 보완 2026-11-03) 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 준법지원인 활동 표의 「내부통제 관련 회의체 운영」 행 묶음(FY2023~2025)
    jtb = ('사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「(3) 준법지원인(준법감시인)의 주요 활동내역」 표(FY2025 제목 끝 「및 그 처리결과」; 칸: 구분 | 주기 | 활동내역 | 점검결과)의 「내부통제 관련 회의체 운영」 행 묶음 — '
           'cadence_text 는 그 행 「주기」 칸 글. 구성·주재자·개최 횟수·안건 글은 찾은 범위(사업보고서·연차보고서 FY2023~2025 같은 이름)에 없음')
    for fy in (2023, 2024, 2025):
        dash = '- ' if fy < 2025 else ''
        rows = [('그룹 준법감시인 협의회', S(f'내부통제 관련 회의체 운영 | 격월 | {dash}그룹 준법감시인 협의회 운영'), S('격월', after='내부통제 관련 회의체 운영'), ''),
                ('그룹 내부통제담당 실무협의회', S(f'{dash}그룹 내부통제담당 실무협의회 운영', after='내부통제 관련 회의체 운영'), S('격월', after='내부통제 관련 회의체 운영'),
                 'cadence_text 는 바로 위 행의 「격월」 칸 — 원본 XML 표에서 그 칸이 ROWSPAN="2"(이 행까지 합친 칸)라 md 행에는 주기 칸이 없음. ')]
        if fy < 2025:
            rows.append(('내부통제 협의회', S(f'분기 | {dash}내부통제 협의회 운영', after='내부통제 관련 회의체 운영'), S('분기', after='그룹 내부통제담당 실무협의회 운영'), ''))
            rows.append(('내부통제 위원회', S(f'반기 | {dash}내부통제 위원회 운영', after='내부통제 관련 회의체 운영'), S('반기', after='내부통제 협의회 운영'),
                         f'(판단) 사업보고서 FY{fy} Ⅵ 이사회 내 위원회 목록·구성 표에 내부통제위원회가 없어(이사회 내 내부통제위원회는 2025년 3월 정기주주총회에서 신설) 이 표의 「내부통제 위원회」를 이사회 내 위원회가 아닌 회의체로 보고 F 에 넣음. '))
        else:
            rows.append(('내부통제 실무협의회', S('분기 | 내부통제 실무협의회 운영', after='내부통제 관련 회의체 운영'), S('분기', after='그룹 내부통제담당 실무협의회 운영'),
                         '(판단) 같은 표 「반기 | 내부통제 위원회 운영」 행은 이사회 내 내부통제위원회(2025년 3월 신설, F2_g2.csv JB FY2025 행)로 보고 F 에 넣지 않음. '))
        for body, src_, cad, pre in rows:
            F_SPECS.append(dict(co=co, fy=fy, body=body, doc=('BR', fy), src=src_, cadence=cad,
                                note=pre + jtb + ' / (검증 때 더한 행)', na_note_given=True))
    # (검증 보완) 그룹 리스크RM 실무협의회 — 연차보고서 「○2024년 그룹 리스크관리 기본방침 및 중점추진업무」 목록에 이름만
    for fy in (2023, 2024):
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹 리스크RM 실무협의회', doc=docs[fy],
            src=S('<그룹 리스크RM 실무협의회 신설&운영>'),
            note=' / '.join(x for x in [JB23_NOTE if fy == 2023 else '',
                                        '연차보고서 리스크관리위원회 절 「○2024년 그룹 리스크관리 기본방침 및 중점추진업무」 목록의 「그룹 리스크 관리체계 업그레이드」 아래 항목 글로 이름만 나옴(신설 계획·운영 항목). 구성·주재자·주기·개최 횟수·안건 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「RM 실무협의회」「리스크 실무협의회」)에 없음. FY2025 문서에는 이 이름 없음 / (검증 때 더한 행)'] if x),
            na_note_given=True))
    # ── F-2 ──
    nt = '(판단) 안건 목록은 사업보고서 Ⅵ 「(2) 위원회 활동내용」 표(여러 위원회가 한 표)에서 이 위원회 행 묶음을 씀 — 연차보고서(본공시)에 같은 위원회 절의 회의별 서술이 있음 / members_text 는 Ⅵ 「(1) 위원회 구성 현황」 표의 그 위원회 행 앞 3칸(위원회명 | 구성 | 소속 이사명)'
    for fy in (2024, 2025):
        coms = [('자회사CEO후보추천위원회', ' / 자회사대표이사후보추천위원회에 해당하는 JB 위원회 이름(원문)'), ('감사위원회', ''), ('리스크관리위원회', ''), ('ESG위원회', '')]
        if fy == 2025:
            coms.append(('내부통제위원회', ''))
        for com, extra in coms:
            sp = dict(co=co, fy=fy, committee=com, doc=('BR', fy), held=('rows', 'agenda_list_text'),
                      agenda=dict(block=com, after=['다. 이사회내 위원회', '(2) 위원회 활동내용' if fy == 2025 else '2) 이사회내의 위원회 활동내역'], upto='라. 이사의 독립성', hdr=None),
                      members=dict(row=com, after=['다. 이사회내 위원회', '(1) 위원회 구성 현황'], ncell=3),
                      note=nt + extra)
            if com == '내부통제위원회':
                sp['established'] = S('2025년 3월 정기주주총회에서 신설한 내부통제위원회')
                sp['note'] += ' / established 는 Ⅵ 「가. 이사회 구성개요」 문장 안의 글'
            F2_SPECS.append(sp)
    F2_SPECS.append(dict(co=co, fy=2024, committee='내부통제위원회', doc=('BR', 2024),
                         note='사업보고서 FY2024 Ⅵ 「(1) 위원회 구성 현황」·「(2) 위원회 활동내용」에 내부통제위원회 없음(찾은 범위: 사업보고서 FY2024 Ⅵ·연차보고서 FY2024, 검색어 「내부통제위원회」 — 사업보고서 FY2024 Ⅰ 정관 변경 표와 Ⅵ 준법지원인 활동 표 「반기 | - 내부통제 위원회 운영」 행(F_g2.csv JB FY2024 「내부통제 위원회」 행)에만 이 이름). 사업보고서 FY2025 Ⅵ 「2025년 3월 정기주주총회에서 신설한 내부통제위원회」'))
    # ── F-3 ──
    F3_SPECS.append(dict(co=co, fy=2025, doc=JB25,
                         function=S('라. 감사보조조직 등'),
                         unit=S('감사본부', after='라. 감사보조조직 등'),
                         hc=S('총 6명(본부장 1, 부장 1, 감사역 4)', after='라. 감사보조조직 등'),
                         duty=S('당사는 감사업무의 실질적인 운영과 효율성 제고를 위해 감사위원회 산하 감사보조기구로', '감사업무를 수행하고 있습니다.', after='라. 감사보조조직 등'),
                         note=JB25_NOTE + ' / ' + AUDIT_PARA_NOTE + ' / 사업보고서 FY2025 Ⅵ 「(7) 감사위원회 지원조직 현황」 표 있음'))
    F3_SPECS.append(dict(co=co, fy=2025, doc=JB25, unit=None, cmp14='준법',
                         note=JB25_NOTE + ' / ' + COMP_NA_NOTE + ' 사업보고서 FY2025 Ⅵ 「(4) 준법지원인(준법감시인) 지원조직 현황」 표 있음. ''연차보고서 FY2025 「1. 지배구조 일반」 「1)조직도 (‘26.2월말기준)」 글(p.8 섹션)에 이사회 내 위원회 아래 「이사회사무국 감사부 리스크기획팀 이사회사무국 준법감시부 ESG팀」과 「(3명) (5명) (4명) (3명) (4명) (2명)」이 차례로 나옴 — 조직도 그림 글이라 위원회·부서·인원 짝은 PDF 글 순서로만 보여 행으로 넣지 않음(검증 때 더한 사실).'))


SPEC_FUNCS.append(spec_JB)


def spec_extra():
    # 한국투자 그룹비상경영위원회(첨부 그룹경영협의회규정 제8조)
    co = '한국투자금융지주'
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹비상경영위원회', doc=('AR', yr),
            src=S('제8조(그룹비상경영위원회)', '「그룹위기상황대응지침」에서 규정한 내용을 따른다.'),
            members=S('② 그룹비상경영위원회의 구성은 제3조를 따르되', '일부만 참여할 수도 있으며'),
            note='연차보고서 첨부 「그룹경영협의회규정」 제8조 — 위기상황 때 그룹경영협의회가 그룹비상경영위원회로 전환된다는 조항(그해 개최 기록 아님). members_text 는 같은 조 ②항(구성은 그룹경영협의회 제3조를 따름). 주재자·주기·개최 횟수·안건 글은 찾은 범위(연차보고서·사업보고서 「그룹비상경영위원회」·「그룹위기상황대응지침」)에 없음' +
                 (' / ' + FY23_AR_NOTE if fy == 2023 else ''),
            na_note_given=True))
    # BNK 내부통제집행위원회(FY2025)
    co = 'BNK금융지주'
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제집행위원회', doc=('AR', 2026),
        src=S('또한, 대표이사는 내부통제등 총괄관리의무의 실효적 수행을 위해서 대표이사를', '내부통제집행위원회를 설치 및 운영하고 있습니다.'),
        chair=S('대표이사를 위원장으로 하고', after='또한, 대표이사는 내부통제등 총괄관리의무의 실효적 수행을 위해서'),
        members=S('전 임원이 참석하여', after='또한, 대표이사는 내부통제등 총괄관리의무의 실효적 수행을 위해서'),
        agenda=S('내부통제등 관리의무 이행 결과 및 조치내', '역을 보고하는', after='또한, 대표이사는 내부통제등 총괄관리의무의 실효적 수행을 위해서'),
        note='연차보고서 FY2025 「2. 이사회」 서술(대표이사 내부통제등 총괄관리의무) 안의 문장. 첨부 규정 「제7조의2(내부통제집행위원회)(2025.1.2 신설)」 — 세부사항은 「내부통제집행위원회규정」에서 정한다. 주기·개최 횟수 글은 찾은 범위(연차보고서·사업보고서 FY2025 「내부통제집행위원회」)에 없음. FY2023·FY2024 문서에는 이 이름 없음'))
    # iM 그룹임원인사위원회(사업보고서 Ⅵ 이사회 안건 표에 이름만)
    co = 'iM금융지주'
    for fy in (2023, 2024, 2025):
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹임원인사위원회', doc=('BR', fy),
            src=S('그룹임원인사위원회 위원 선임', after='VI. 이사회 등 회사의 기관에 관한 사항'),
            note=f'사업보고서 FY{fy} Ⅵ 이사회 안건 표의 결의 안건 이름(「그룹임원인사위원회 위원 선임」)으로만 나옴' +
                 ('; 같은 표 보고 안건 「그룹임원인사위원회 결의사항 보고」도 있음' if fy < 2025 else '') +
                 '. 연차보고서에 첨부 규정 목록 「자. 그룹임원인사위원회규정」(이사회 결의사항 목록)만 있음. 이사회 내 위원회 목록((2) 이사회내의 위원회 명칭)에 없음. 구성·주재자·주기·개최 횟수·안건 글은 찾은 범위(사업보고서·연차보고서 FY2023~2025 「임원인사위원회」)에 없음',
            na_note_given=True))


    # (검증 보완 2026-11-03) 메리츠 내부통제위원회(FY2023·FY2024) — 사업보고서 Ⅵ 준법감시인 활동 표 행
    for fy in (2023, 2024):
        F_SPECS.append(dict(
            co='메리츠금융지주', fy=fy, body='내부통제위원회', doc=('BR', fy),
            src=S('반기 | 내부통제위원회 활동(내부통제 주요 이슈 점검 등) | 특이사항 없음'),
            cadence=S('반기', after='연간 내부통제체제 점검'),
            note=f'(판단) 사업보고서 FY{fy} Ⅵ 이사회 내 위원회 목록·구성 표에 내부통제위원회가 없어(이사회 내 내부통제위원회는 2025. 3. 26. 설립 — F2_g2.csv 메리츠 FY2025 행) 이 표의 「내부통제위원회」를 이사회 내 위원회가 아닌 회의체로 보고 F 에 넣음. '
                 f'사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「{"②" if fy == 2023 else "(2)"} 준법감시인 등의 주요 활동내역 및 그 처리결과」 표(칸: 점검일시 | 주요 점검내용 | 점검결과) 행 — cadence_text 는 그 행 「점검일시」 칸 글. '
                 '구성·주재자·개최 횟수·안건 글은 찾은 범위(사업보고서·연차보고서 FY2023·FY2024 「내부통제위원회」)에 없음. 사업보고서 FY2025 같은 표의 같은 행은 이사회 내 내부통제위원회(F-2)로 보고 F 에 넣지 않음(판단) / (검증 때 더한 행)',
            na_note_given=True))
    # (검증 보완 2026-11-03) iM 집행위원회 — 연차보고서 첨부 규범 조항(상임이사·업무집행책임자가 구성원)
    for fy in (2023, 2024, 2025):
        sent = S('상임이사 및 업무집행책임자는 회장이 정한 역할을 수행하며', '의사결정에 참여한다.')
        F_SPECS.append(dict(
            co=co, fy=fy, body='집행위원회', doc=('AR', fy + 1), src=sent, members=sent,
            note=' / '.join(x for x in [FY23_AR_NOTE if fy == 2023 else '',
                                        '연차보고서 첨부 규범 조항 「② 상임이사 및 업무집행책임자는 … 집행위원회의 구성원으로 의사결정에 참여한다.」(members_text 도 같은 글). 같은 첨부 이사회 결의사항 목록에 「사. 집행위원회규정」, 이사회규정 「긴급을 요할 시에는 집행위원회의 승인을 얻어 사전 취급」' +
                                        ('. 연차보고서 FY2025 이사회 회의 내역 보고 안건 「집행위원회 결의사항 결과」, 사업보고서 FY2025 Ⅵ 이사회 표 2025.08.12 보고 「2. 집행위원회 결의사항 결과 보고」·2025.12.12 보고 「1. 집행위원회 의결사항 결과 보고」' if fy == 2025 else '') +
                                        '. 주재자·주기·개최 횟수·안건 글은 찾은 범위(연차보고서·사업보고서 FY2023~2025 「집행위원회」)에 없음 / (검증 때 더한 행)'] if x),
            na_note_given=True))


SPEC_FUNCS.append(spec_extra)


if __name__ == '__main__':
    sys.exit(main())
