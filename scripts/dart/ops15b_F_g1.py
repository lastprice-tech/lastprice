"""15차 확장 작업 F·F-2·F-3 그룹 g1 — 원문 로더·대조 공용 함수 (ops15b_F_g1.py·verify15b_F_g1.py 가 import).

원문(출처 텍스트) 정의 — 생성기와 검증기가 같은 정의를 씀:
- 사업보고서(OpenDART XML md, dart_out/text/ops15/사업보고서__…md): md 의 머리(첫 「### [절」 앞)는 버림.
  「### [절 n] 제목」 줄은 「제목」만 남기고(제목 글은 XML TITLE 원문), 「[표 n]」「[표 끝]」 줄은 변환 표지라 지움.
  대조 때는 공백·줄바꿈에 더해 md 표지 「|」「<br>」를 양쪽에서 지움(COMMON15b 대조 규칙).
- 연차보고서 FY2023(dart_out/text/ops15/연차보고서__<회사>__2024__<유형>.md, pymupdf 글): 머리(첫 「## p.1」 앞) 버림,
  「## p.N」 줄은 쪽 표지라 지우고 쪽 번호만 기억.
- 연차보고서 FY2024·FY2025(dart_out/ops15/kit56/연차보고서_섹션.csv, 6차 섹션): 같은 파일의 섹션 본문을 섹션순번·chunk_seq 순으로 이어 붙인 글.
  page = 그 글이 든 섹션의 시작페이지.
- 표시용 글: 줄마다 공백 연속을 한 칸으로, 앞뒤 공백·빈 줄 지움(공백만 바뀜 — 대조는 공백·줄바꿈을 지우고 봄).
"""
import csv, os, re, bisect
from datetime import datetime, timezone, timedelta

csv.field_size_limit(10**9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KST = timezone(timedelta(hours=9))
G1 = ['KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'NH농협금융지주']
NA = '문서에 없음'

_cache = {}


def _norm_lines(lines):
    out = []
    for ln in lines:
        s = re.sub(r'[ \t 　]+', ' ', ln).strip()
        if s:
            out.append(s)
    return out


class Doc:
    """display: 표시용 글, marks: [(display_offset, label)] 쪽/절 표지."""

    def __init__(self, did, kind, corp, fy, doc_kind, doc_name, ref, collected_at, path, display, marks, xml=False, extra=None):
        self.id, self.kind, self.corp, self.fy = did, kind, corp, fy
        self.doc_kind, self.doc_name, self.ref, self.collected_at, self.path = doc_kind, doc_name, ref, collected_at, path
        self.display, self.marks, self.xml = display, marks, xml
        self.extra = extra or {}
        idx = []
        chars = []
        for i, c in enumerate(display):
            if not c.isspace():
                idx.append(i)
                chars.append(c)
        self.stripped = ''.join(chars)
        self.smap = idx
        self.mark_pos = [m[0] for m in marks]
        self.cmp = cmpnorm(display, xml)

    def label_at(self, pos):
        k = bisect.bisect_right(self.mark_pos, pos) - 1
        return self.marks[k][1] if k >= 0 else ''

    def find(self, s, after=0):
        """공백 무시 찾기 → display 시작 위치 (없으면 -1). after = display 위치."""
        ss = re.sub(r'\s+', '', s)
        sa = bisect.bisect_left(self.smap, after)
        p = self.stripped.find(ss, sa)
        if p < 0:
            return -1
        return self.smap[p]

    def grab(self, start, end=None, after=None, upto=None, occ=0, eafter=None):
        """start(포함)~end(포함) 이어진 글. upto 를 주면 upto 앞까지(미포함). after = 이 글 뒤에서 찾기.
        eafter = end·upto 를 start 뒤의 이 글 뒤에서 찾음(같은 끝 글이 여러 번 나올 때)."""
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
        ea = p
        if eafter:
            ea = self.find(eafter, p)
            if ea < 0:
                raise ValueError(f'{self.id}: eafter 못 찾음 {eafter!r}')
        if end is None and upto is None:
            ss = re.sub(r'\s+', '', start)
            si = bisect.bisect_left(self.smap, p)
            e = self.smap[si + len(ss) - 1] + 1
        elif upto is not None:
            q = self.find(upto, max(p + 1, ea))
            if q < 0:
                raise ValueError(f'{self.id}: upto 못 찾음 {upto!r}')
            e = q
        else:
            ss = re.sub(r'\s+', '', end)
            q = self.find(end, ea)
            if q < 0:
                raise ValueError(f'{self.id}: end 못 찾음 {end!r}')
            si = bisect.bisect_left(self.smap, q)
            e = self.smap[si + len(ss) - 1] + 1
        txt = self.display[p:e].strip()
        return txt, p, e

    def page(self, p, e):
        a, b = self.label_at(p), self.label_at(max(p, e - 1))
        if self.kind == 'AR_md':
            return f'p.{a}' if a == b else f'p.{a}~{b}'
        if self.kind == 'AR_kit':
            return f'p.{a}' if a == b else f'p.{a}~{b}'
        return a if a == b else f'{a} ~ {b}'


def cmpnorm(t, xml=False):
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return re.sub(r'\s+', '', t)


def to_kst(s):
    s = s.strip()
    if not s:
        return ''
    if s.endswith('+0000'):
        d = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S+0000').replace(tzinfo=timezone.utc)
        return d.astimezone(KST).isoformat()
    return s


def br_rows():
    if 'br_rows' not in _cache:
        _cache['br_rows'] = list(csv.DictReader(open(f'{ROOT}/dart_out/ops15/사업보고서_원문.csv', encoding='utf-8-sig')))
    return _cache['br_rows']


def load_br(rcept):
    key = 'BR:' + rcept
    if key in _cache:
        return _cache[key]
    x = [r for r in br_rows() if r['rcept_no'] == rcept][0]
    lines = open(f"{ROOT}/{x['text_path']}", encoding='utf-8').read().split('\n')
    disp, marks = [], []
    off = 0
    cur_sec, cur_tab, started = '', '', False
    for ln in lines:
        m = re.match(r'^### \[절 (\d+)\] ?(.*)$', ln)
        if m:
            started = True
            cur_sec = f'XML [절 {m.group(1)}] 「{m.group(2).strip()}」'
            cur_tab = ''
            marks.append((off, cur_sec))
            ln = m.group(2)
        elif not started:
            continue
        else:
            mt = re.match(r'^\[표 (\d+)\]\s*$', ln.strip())
            if mt:
                cur_tab = f' [표 {mt.group(1)}]'
                marks.append((off, cur_sec + cur_tab))
                continue
            if ln.strip() == '[표 끝]':
                cur_tab = ''
                marks.append((off, cur_sec))
                continue
        s = _norm_lines([ln])
        if s:
            disp.append(s[0])
            off += len(s[0]) + 1
    display = '\n'.join(disp)
    d = Doc(key, 'BR', x['label'], int(x['fy']), '사업보고서', x['report_nm'], x['rcept_no'], x['fetched_at'],
            x['text_path'], display, marks, xml=True, extra=dict(kind=x['kind'], rcept_dt=x['rcept_dt'], raw_path=x['raw_path'], sha=x['raw_sha256']))
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
            p = f'{ROOT}/dart_out/ops15/연차보고서15_목록_{g}.csv'
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
        _cache['kit'] = list(csv.DictReader(open(f'{ROOT}/dart_out/ops15/kit56/연차보고서_섹션.csv', encoding='utf-8-sig')))
    return _cache['kit']


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
            s = _norm_lines([ln])
            if s:
                disp.append(s[0])
                off += len(s[0]) + 1
        meta = [r for r in ar_list() if r['회사'] == corp and r['공시연도'] == str(year) and r['공시유형'] == typ][0]
        url = meta['파일_url'].split(' (')[0]
        d = Doc(key, 'AR_md', corp, year - 1, '지배구조 및 보수체계 연차보고서', meta['제목'], url, meta['fetched_at'], path,
                '\n'.join(disp), marks, extra=dict(rcept_dt=meta['공시일'], sha=meta['sha256'], raw_url_note=meta['파일_url']))
    else:
        rows = [r for r in kit_rows() if r['지주명'] == corp and r['공시연도'] == str(year) and r['공시유형'] == typ and '지배구조' in r['파일명']]
        rows.sort(key=lambda r: (int(r['섹션순번']), int(r['chunk_seq'])))
        fname = rows[0]['파일명']
        meta = [r for r in kit_files() if r['파일명'] == fname][0]
        disp, marks, off = [], [], 0
        parent = ''
        secmarks = []
        for r in rows:
            if re.match(r'^\d+\.$', r['섹션번호'].strip()) or r['섹션번호'].startswith('제'):
                parent = f"{r['섹션번호']} {r['섹션제목_원문']}"
            body = r['본문']
            if not body:
                continue
            lab = r['시작페이지'] or '?'
            marks.append((off, lab))
            st = f"{r['섹션번호']} {r['섹션제목_원문']}".strip()
            secmarks.append((off, parent or st))
            for s in _norm_lines(body.split('\n')):
                disp.append(s)
                off += len(s) + 1
        # kit 본문 chunk 경계가 줄 중간일 수 있음 — 표시 글에서는 줄로 나뉘지만 대조는 공백 무시라 같음
        d = Doc(key, 'AR_kit', corp, year - 1, '지배구조 및 보수체계 연차보고서', meta['제목'], meta['url'], to_kst(meta['fetched_at']),
                f'dart_out/ops15/kit56/연차보고서_섹션.csv (파일명 {fname})', '\n'.join(disp), marks,
                extra=dict(sha=meta['sha256'], fname=fname))
        sp = [m[0] for m in secmarks]
        d.extra['sec_at'] = lambda q: secmarks[max(0, bisect.bisect_right(sp, q) - 1)][1] if secmarks else ''
    _cache[key] = d
    return d


def doc_by_ref(ref, corp=None, fy=None):
    """rcept_no 또는 URL → Doc."""
    if re.fullmatch(r'\d{14}', ref):
        return load_br(ref)
    for r in ar_list():
        if r['파일_url'].split(' (')[0] == ref:
            return load_ar(r['회사'], r['공시연도'], r['공시유형'])
    for r in kit_files():
        if r['url'] == ref and '지배구조' in r['파일명']:
            return load_ar(r['지주명'], r['공시연도'], r['공시유형'])
    raise KeyError(ref)


def refs_in(note):
    """note 안의 rcept_no·URL."""
    out = re.findall(r'(?<!\d)(\d{14})(?!\d)', note or '')
    out += re.findall(r'(https?://[^\s」』)\]]+)', note or '')
    return out


# ───────────────────────── 생성기 ─────────────────────────
KW_F = ['협의회', '협의체', '회의체', '위원회', '그룹', '리스크', '내부통제', '준법', '감사', '소비자보호', 'ESG', '디지털', 'AI', 'IT',
        '정보보호', '브랜드', '시너지', '개최', '분기', '매월']


def function_kw(*texts):
    """REQUEST15b 작업 F 키워드 중 body_name·source_text 에 든 낱말(공백 지우고 찾음, AI·IT 는 앞뒤가 영문자가 아닐 때만)."""
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


class Spans:
    """원문 md 로 쓸 구간 모음: (doc, p, e)."""

    def __init__(self):
        self.items = {}

    def add(self, task, corp, fy, doc, p, e):
        self.items.setdefault((task, corp, fy, doc.id), (doc, []))[1].append((p, e))


SPANS = Spans()


def field(f, corp, default_doc, task, fy, notes, fname):
    """f: None → 문서에 없음 / dict(s=, e=|upto=, after=, doc=, occ=) / ('lit', 값) 원문이 아닌 고정값(분류 칸 등)."""
    if f is None:
        return NA, None
    if isinstance(f, tuple) and f[0] == 'lit':
        return f[1], None
    d = get_doc(f['doc'], corp) if 'doc' in f else default_doc
    txt, p, e = d.grab(f['s'], f.get('e'), after=f.get('after'), upto=f.get('upto'), occ=f.get('occ', 0), eafter=f.get('eafter'))
    if f.get('trim', True) and f.get('upto'):
        # upto 로 자른 글 끝의 쪽 번호·다음 절 번호(예 「194 / 14.」)만 떼어 냄(앞부분 이어진 글은 그대로)
        txt = re.sub(r'(\s*(\d{1,3}\.?|[가-하]\.|\(\d+\)))+\s*$', '', txt)
    if f.get('max') and len(txt) > f['max']:
        raise ValueError(f'{fname} 너무 김 {len(txt)}')
    SPANS.add(task, corp, fy, d, p, e)
    if d is not default_doc:
        notes.append(f'{fname} 는 {d.doc_kind} {d.ref} {d.page(p, e)}')
    elif f.get('locnote'):
        notes.append(f'{fname} 위치 {d.page(p, e)}')
    return txt, (d, p, e)


def held_from(spec, vals):
    """spec: None → 문서에 없음, ('lit', 값, note), dict(field=, re=) → 원문 숫자."""
    if spec is None:
        return NA, ''
    if spec[0] == 'lit':
        return spec[1], spec[2]
    fld, rx = spec[1], spec[2]
    m = re.search(rx, re.sub(r'\s+', ' ', vals[fld]))
    if not m:
        raise ValueError('held 못 찾음 ' + rx)
    return m.group(1), f'held_count 원문 「{m.group(0)}」({fld} 칸)'


F_COLS = ['corp_label', 'fy', 'body_name', 'function_kw', 'chair_text', 'members_text', 'cadence_text', 'held_count', 'agenda_text',
          'doc_kind', 'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
F2_COLS = ['corp_label', 'fy', 'committee', 'established', 'held_count', 'agenda_list_text', 'subsidiary_related', 'members_text',
           'rcept_no', 'page', 'note', 'doc_name', 'collected_at']
F3_COLS = ['corp_label', 'fy', 'function', 'unit_name', 'headcount', 'concurrent_or_dispatched', 'duty_text', 'rcept_no_or_url', 'page',
           'note', 'doc_name', 'collected_at']
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note']


def sec_title(d, p, given=None):
    if given:
        return given
    if d.kind == 'BR':
        lab = d.label_at(p)
        return re.sub(r' \[표 \d+\]$', '', lab)
    if d.kind == 'AR_kit':
        # 이 위치가 든 섹션 제목(6차 섹션 제목_원문)
        return d.extra.get('sec_at', lambda q: '')(p)
    # 연차보고서 md: 앞쪽에서 가장 가까운 「N. 제목」 줄(목차 점선 줄 제외)
    for m in reversed(list(re.finditer(r'(?m)^(\d{1,2})\. ?([가-힣A-Za-z][^\n.]{1,40})$', d.display[:p]))):
        if '..' not in m.group(0):
            return m.group(0).strip()
    return ''


def build_F(spec):
    co, fy = spec['co'], spec['fy']
    d = get_doc(spec['doc'], co)
    notes = []
    vals = {}
    locs = {}
    if spec.get('src') is None:
        # 문서에 없음 행
        return {'corp_label': co, 'fy': fy, 'body_name': spec['body'], 'function_kw': function_kw(spec['body']), 'chair_text': NA,
                'members_text': NA, 'cadence_text': NA, 'held_count': NA, 'agenda_text': NA, 'doc_kind': d.doc_kind,
                'section_title': spec.get('section', ''), 'source_text': NA, 'rcept_no_or_url': d.ref, 'page': spec.get('page', ''),
                'note': spec.get('note', ''), 'doc_name': d.doc_name, 'collected_at': d.collected_at}
    vals['source_text'], locs['source_text'] = field(spec['src'], co, d, 'F', fy, [], 'source_text')
    for k in ('chair', 'members', 'cadence', 'agenda'):
        vals[k + '_text'], locs[k + '_text'] = field(spec.get(k), co, d, 'F', fy, notes, k + '_text')
    held, hn = held_from(spec.get('held'), vals)
    if hn:
        notes.append(hn)
    _, p, e = locs['source_text']
    # 15b 검증 고침: *_text 칸이 source_text 와 같은 문서의 다른 쪽·절에서 왔으면 note 에 그 위치(COMMON15b)
    src_pg = d.page(p, e)
    for k in ('chair', 'members', 'cadence', 'agenda'):
        lk = locs.get(k + '_text')
        if lk and lk[0] is d:
            pg = d.page(lk[1], lk[2])
            if pg != src_pg and not any(n.startswith(f'{k}_text 위치') for n in notes):
                notes.append(f'{k}_text 위치 {pg}' + (' (6차 섹션 시작페이지)' if d.kind == 'AR_kit' else ''))
    allnotes = ([spec['note']] if spec.get('note') else []) + notes
    return {'corp_label': co, 'fy': fy, 'body_name': spec['body'],
            'function_kw': function_kw(spec['body'], vals['source_text']),
            'chair_text': vals['chair_text'], 'members_text': vals['members_text'], 'cadence_text': vals['cadence_text'],
            'held_count': held, 'agenda_text': vals['agenda_text'], 'doc_kind': d.doc_kind,
            'section_title': spec.get('section') or sec_title(d, p), 'source_text': vals['source_text'],
            'rcept_no_or_url': d.ref, 'page': d.page(p, e) + (' (6차 섹션 시작페이지)' if d.kind == 'AR_kit' else ''),
            'note': ' / '.join(allnotes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}


def S(s, e=None, **kw):
    d = dict(s=s)
    if e is not None:
        d['e'] = e
    d.update(kw)
    return d


def HRE(fld, rx):
    return ('re', fld, rx)


# ───────────── 작업 F 명세(회사별) ─────────────
F_SPECS = []
AR_SEC23 = {}  # FY2023 연차보고서 md 의 절 제목(손으로 — md 에 절 구조가 없음)


def spec_F_KB():
    co = 'KB금융지주'
    ends_rmc = {2024: '바젤기준 거액익스포져 한도규제 도입(안)', 2025: '(2024.12.4.) 현황 점검', 2026: '[협의 안건] 2026년 리스크관리 전략방향'}
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        doc = ('AR', yr)
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹 경영관리위원회', doc=doc,
            section='12. 그룹 경영관리위원회' if yr == 2024 else None,
            src=S('그룹 경영관리위원회는 정관상의 기구로', '경영의사결정을 지원하고 있습니다.'),
            cadence=S('위원회는 정기적으로 개최하는 것을 원칙으로', '성원을 구성합니다.'),
            members=S('위원회 위원은 대표이사 회장 및 대표이사 회장이 지명하는', upto='라. 활동내역 개요 동 위원회는'),
            chair=S('양종희', '위원장', after='그룹경영관리위원회 구성>'),
            agenda=S(f'동 위원회는 {fy}년 총', '관련된 사항입니다.'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*차례'),
            note=('사업보고서 Ⅱ 리스크관리 서술(「2) 리스크관리협의회」 문단)에 「그룹 경영관리위원회 검토 요청 사항」으로 이름만 나옴' if fy >= 2023 else ''),
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='리스크관리협의회', doc=doc,
            section='13. 리스크관리협의회' if yr == 2024 else None,
            src=S('리스크관리협의회는 리스크관리위원회로부터', '역할을 수행합니다.'),
            cadence=S('리스크관리협의회는 「리스크관리협의회규정」 제6조에 따라 분기 1회', '수시로 소집할 수 있습니다.'),
            members=S('리스크관리협의회 위원은 「리스크관리협의회규정」 제2조', upto='라. 활동내역 개요'),
            chair=S('협의회의 위원장은 지주회사 위험관리책임자가', '직무를 수행하고 있습니다.'),
            agenda=S(f'{fy}년 리스크관리협의회는 총', ends_rmc[yr]),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회\s*개최'),
            note='같은 협의회를 사업보고서 Ⅱ(리스크관리 — 「2) 리스크관리협의회」 문단)와 Ⅲ 주석(금융위험의 관리 — 「- 리스크관리협의회」 문단)에도 적음 — 연차보고서 글을 기준으로 함',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='지주 경영위원회', doc=doc,
            section='2. 이사회 > 가. 역할(권한과 책임)' if yr == 2024 else None,
            src=S('이 경우 당해', '배당(안)을 결의하고 있습니다.', after='예산 및 결산'),
            agenda=S('지주 경영위원회의 심의를 거쳐', '예산 편성(안)을 결의하였으며'),
            note='이사회 역할(예산·결산 승인) 서술 안에 이름만 나옴 — 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 전문 「지주 경영위원회」·「경영위원회」, 사업보고서 Ⅱ·Ⅵ)에 없음; agenda_text 는 그해 예산(안) 심의 문장',
        ))
    # FY2025 내부통제협의회(연차보고서 FY2025 에만)
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제협의회', doc=('AR', 2026),
        src=S('또한, 대표이사를 위원장으로 하는 내부통제협의회를', '지원하고 있습니다.'),
        chair=S('대표이사를 위원장으로 하는 내부통제협의회를'),
        cadence=None,
        agenda=S('KB금융지주는 2025년 상ㆍ하반기 (6.24., 12.22.) 내부통제협의회를 개최하였으며', '점검하였습니다.', locnote=True),
        held=('lit', '2', '(판단) agenda_text 의 「2025년 상ㆍ하반기 (6.24., 12.22.) 내부통제협의회를 개최」에 적힌 개최일 2개를 셈'),
        note='내부통제위원회 절의 문장. 첨부 내부통제위원회규정 「제 12 조(협의회) 위원회는 효율적인 업무수행을 위하여 내부통제협의회를 설치하여 운영할 수 있다.」(p.264 섹션). FY2023·FY2024 연차보고서·사업보고서에는 「내부통제협의회」 낱말 없음',
    ))
    # FY2025 사업보고서 고객정보 보호 서술의 정보보호 의사결정기구
    for body in ('정보보호위원회', '그룹정보보협의회'):
        F_SPECS.append(dict(
            co=co, fy=2025, body=body, doc=('BR', 2025),
            src=S('KB금융그룹은 고객정보 보호를 고객 신뢰에 중대한 영향을', '정보보호 거버넌스 체계를 구축하고 있습니다.', after='[KB금융지주]'),
            note=('body_name 은 원문 글자 그대로(「그룹정보보협의회」 — 원문 표기). ' if body.startswith('그룹') else '') +
                 '사업보고서 FY2025 「4. 작성기준일 이후 발생한 주요사항 등 기타사항」의 고객정보 보호 서술에 「이사회·정보보호위원회·그룹정보보협의회 등 의사결정기구」로 이름만 나옴(이사회 내 위원회 목록에는 없음). 구성·주기 서술 없음. FY2023·FY2024 사업보고서의 같은 서술([KB금융지주] 문단)에는 이 이름 없음',
        ))


# ───────────── 쓰기 ─────────────
OUT = f'{ROOT}/dart_out/ops15'
F2_SPECS, F3_SPECS, CHK_SPECS = [], [], []
SPEC_FUNCS = []  # 회사별 spec 함수(아래에서 등록)


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
    written = []
    groups = {}
    for (task, corp, fy, did), (doc, spans) in SPANS.items.items():
        groups.setdefault((task, corp, fy, did), (doc, spans))
    for (task, corp, fy, did), (doc, spans) in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3])):
        # 구간을 표지 경계로 넓힘
        if doc.kind == 'BR':
            bounds = [m[0] for m in doc.marks if '[표' not in m[1]] + [len(doc.display)]
        else:
            bounds = sorted(set([m[0] for m in doc.marks] + [len(doc.display)]))
        ivs = []
        for p, e in spans:
            a = bounds[max(0, bisect.bisect_right(bounds, p) - 1)]
            b = bounds[min(len(bounds) - 1, bisect.bisect_left(bounds, e))]
            if doc.kind == 'BR' and b - a > 80000:
                a, b = max(a, p - 3000), min(b, e + 3000)
            ivs.append([a, b])
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        if doc.kind == 'BR':
            dname = f'사업보고서_{doc.ref}'
        else:
            yr = doc.fy + 1
            dname = f"연차보고서_{yr}공시_{doc.id.split(':')[-1]}"
        sub = {'F': 'F', 'F2': 'F2', 'F3': 'F3', 'CHK': 'F2'}[task]
        path = f'{OUT}/원문/{sub}/{corp}__FY{doc.fy}__{dname}.md'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lines = [f'# {doc.doc_kind} — {corp} FY{doc.fy}', '',
                 f'- 문서: {doc.doc_name}', f'- 출처: {doc.ref}', f'- 받은 시각: {doc.collected_at}', f'- 글: {doc.path}',
                 '- 아래는 행의 글이 나온 절(사업보고서 XML md, 「[표 n]」 표지는 지움) 또는 쪽(연차보고서 FY2023 PDF 글)·섹션(연차보고서 FY2024·25 6차 섹션 글) 전체. 줄 안 공백 연속은 한 칸으로 줄임.', '']
        for a, b in merged:
            lines.append(f'## {doc.page(a, b)}')
            lines.append('')
            lines.append(doc.display[a:b])
            lines.append('')
        # 같은 파일을 F/F2 가 함께 쓰면 덧붙임
        mode = 'a' if path in written else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        written.append(path)
    return written


def doclist(rows_all):
    seen = {}
    for task, rows in rows_all:
        for r in rows:
            ref = r.get('rcept_no_or_url') or r.get('rcept_no')
            if not ref or ref in seen:
                continue
            try:
                d = doc_by_ref(ref)
            except Exception:
                continue
            seen[ref] = d
    out = []
    for ref, d in sorted(seen.items(), key=lambda x: (x[1].corp, x[1].fy, x[1].doc_kind)):
        out.append(dict(doc_kind=d.doc_kind, corp_label=d.corp, fy_or_date=f'FY{d.fy}', report_nm=d.doc_name, rcept_no_or_url=ref,
                        rcept_dt=d.extra.get('rcept_dt', ''), raw_path=d.extra.get('raw_path', '') or d.extra.get('fname', ''),
                        sha256=d.extra.get('sha', ''), fetched_at=d.collected_at, text_path=d.path, status='받음',
                        note=('6차 섹션 글(PDF 원본은 이번 컨테이너에 없음)' if d.kind == 'AR_kit' else
                              ('연차보고서 PDF 글(pymupdf, 「## p.N」)' if d.kind == 'AR_md' else 'OpenDART XML md'))))
    # 13차 보관 FY2025 사업보고서 본문 PDF 글(page 칸 쪽 번호에만 씀)
    for corp in G1:
        mt = _cache.get('P13meta:' + corp)
        P = _cache.get('P13:' + corp)
        if mt and P:
            out.append(dict(doc_kind='사업보고서 본문 PDF 글(13차 보관)', corp_label=corp, fy_or_date='FY2025', report_nm='사업보고서 (2025.12)',
                            rcept_no_or_url=P[0], rcept_dt='', raw_path='handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip',
                            sha256=mt['sha'], fetched_at='', text_path='handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip:' + mt['member'],
                            status='받음', note='FY2025 사업보고서 행의 page 칸 「p.N(본문 PDF, 13차 보관)」을 찾는 데만 씀; sha256 은 md 머리의 원본 PDF 값; 받은 시각은 zip 머리에 없음'))
    # 15b 검증 고침: F 범위로 찾았으나 행이 나오지 않은 문서(사업보고서 본·연차보고서 본공시 FY2023~25)도 목록에 둠
    for corp in G1:
        for fy in (2023, 2024, 2025):
            cands = []
            rc = br_id(corp, fy)
            if rc:
                cands.append(rc)
            try:
                cands.append(load_ar(corp, fy + 1).ref)
            except Exception:
                pass
            for ref in cands:
                if ref in seen:
                    continue
                d = doc_by_ref(ref)
                seen[ref] = d
                out.append(dict(doc_kind=d.doc_kind, corp_label=d.corp, fy_or_date=f'FY{d.fy}', report_nm=d.doc_name, rcept_no_or_url=ref,
                                rcept_dt=d.extra.get('rcept_dt', ''), raw_path=d.extra.get('raw_path', '') or d.extra.get('fname', ''),
                                sha256=d.extra.get('sha', ''), fetched_at=d.collected_at, text_path=d.path, status='받음',
                                note='작업 F 범위로 찾은 문서 — 이 문서에서 나온 행 없음(F 의 회의체는 같은 FY 다른 문서 행으로 둠)'))
    # 15b 검증 고침: kit 행의 실제 PDF 쪽을 찾은 글(같은 sha256)
    for path in sorted(set(PDFAR_USED)):
        out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서 PDF 쪽 글(같은 sha256)', corp_label=PDFAR_USED[path][0], fy_or_date=f'FY{PDFAR_USED[path][1]}',
                        report_nm=PDFAR_USED[path][2], rcept_no_or_url=PDFAR_USED[path][3], rcept_dt='', raw_path='', sha256=PDFAR_USED[path][4],
                        fetched_at=PDFAR_USED[path][5], text_path=path, status='받음',
                        note='kit56 섹션 글 행의 page 칸 「PDF p.N」을 찾는 데만 씀(6차 섹션 글과 같은 sha256 PDF 의 「## p.N」 글)' +
                        ('' if PDFAR_USED[path][5] else '; 받은 시각은 13차 zip 머리에 없음')))
    # NH 연차보고서 FY2019~2023 없음 기록
    for r in ar_list():
        if r['회사'] == 'NH농협금융지주' and r['공시연도'] in ('2024',):
            out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label='NH농협금융지주', fy_or_date='FY2023', report_nm=r['제목'],
                            rcept_no_or_url=r['게시판_url'], rcept_dt=r['공시일'], raw_path='', sha256='', fetched_at=r['fetched_at'],
                            text_path='', status='없음',
                            note='연차보고서15_목록_g1.csv 에 NH 공시연도 2024(FY2023) 파일 없음 — ' + (r['robots_판정'] or '')[:200]))
    return out


def main():
    for fn in SPEC_FUNCS:
        fn()
    frows, f2rows, f3rows, chk = [], [], [], []
    errs = []
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
    add_pdf13(frows, 'source_text', 'rcept_no_or_url')
    add_pdf13(f2rows, 'agenda_list_text', 'rcept_no')
    add_pdfpage(frows, 'source_text', 'rcept_no_or_url')
    add_pdfpage(f3rows, '_anchor', 'rcept_no_or_url')
    add_pdfpage(chk, 'source_excerpt', 'rcept_no_or_url')
    for rows, task in ((frows, 'F'), (f2rows, 'F2'), (f3rows, 'F3'), (chk, 'CHK')):
        check_variants(rows, task)
    print('판 대조:', VAR_STAT)
    write_csv(f'{OUT}/조각/F_g1.csv', F_COLS, frows)
    write_csv(f'{OUT}/조각/F2_g1.csv', F2_COLS, f2rows)
    write_csv(f'{OUT}/조각/F3_g1.csv', F3_COLS, f3rows)
    write_csv(f'{OUT}/조각/확인_F_g1.csv', CHK_COLS, chk)
    for sub in ('F', 'F2', 'F3'):
        dd = f'{OUT}/원문/{sub}'
        if os.path.isdir(dd):
            for fn in os.listdir(dd):
                if any(fn.startswith(c + '__') for c in G1):
                    os.remove(os.path.join(dd, fn))
    write_wonmun()
    dl = doclist([('F', frows), ('F2', f2rows), ('F3', f3rows), ('CHK', chk)])
    write_csv(f'{OUT}/문서목록15b_F_g1.csv', ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path',
                                            'sha256', 'fetched_at', 'text_path', 'status', 'note'], dl)
    print(f'F {len(frows)}  F2 {len(f2rows)}  F3 {len(f3rows)}  확인 {len(chk)}  문서 {len(dl)}')
    for e in errs:
        print('ERR', e)
    return frows, f2rows, f3rows, chk


def pdf13(corp):
    """13차 보관 FY2025 사업보고서 본문 PDF 글(「## p.N」) → (rcept, stripped, [(stripped_offset, page)])."""
    key = 'P13:' + corp
    if key not in _cache:
        import zipfile
        z = zipfile.ZipFile(f'{ROOT}/handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip')
        name = f'13차_지주관리유형/텍스트/사업보고서__{corp}.md'
        if name not in z.namelist():
            _cache[key] = None
            return None
        t = z.read(name).decode('utf-8')
        m = re.search(r'dart_out/doc/(\d{14})/', t[:2000])
        chars, marks = [], []
        n = 0
        for ln in t.split('\n'):
            mm = re.match(r'^## p\.(\d+)', ln)
            if mm:
                marks.append((n, int(mm.group(1))))
                continue
            if not marks:
                continue
            s = re.sub(r'\s+', '', ln)
            chars.append(s)
            n += len(s)
        sh = re.search(r'sha256 ([0-9a-f]{64})', t[:2000])
        _cache[key] = (m.group(1) if m else '', ''.join(chars), marks)
        _cache['P13meta:' + corp] = dict(sha=sh.group(1) if sh else '', member=name)
    return _cache[key]


VAR_FIELDS = {'F': ['source_text', 'chair_text', 'members_text', 'cadence_text', 'agenda_text'],
              'F2': ['agenda_list_text', 'members_text', 'established'],
              'F3': ['function', 'unit_name', 'concurrent_or_dispatched', 'duty_text'],
              'CHK': ['source_excerpt']}
VAR_STAT = {}


def variants_of(d):
    """같은 문서의 다른 판: 연차보고서 → [(유형, Doc)], 사업보고서 → [(정정 rcept, Doc 또는 None, report_nm)]."""
    key = 'VAR:' + d.id
    if key in _cache:
        return _cache[key]
    out = []
    if d.kind == 'AR_kit':
        typs = sorted({r['공시유형'] for r in kit_rows() if r['지주명'] == d.corp and r['공시연도'] == str(d.fy + 1) and '지배구조' in r['파일명']} - {'본공시'})
        for t in typs:
            out.append((t, load_ar(d.corp, d.fy + 1, t)))
    elif d.kind == 'AR_md':
        for r in ar_list():
            if r['회사'] == d.corp and r['공시연도'] == str(d.fy + 1) and r['공시유형'] != '본공시' and \
                    os.path.exists(f"{ROOT}/dart_out/text/ops15/연차보고서__{d.corp}__{d.fy + 1}__{r['공시유형']}.md"):
                out.append((r['공시유형'], load_ar(d.corp, d.fy + 1, r['공시유형'])))
    elif d.kind == 'BR':
        for r in br_rows():
            if r['label'] == d.corp and r['fy'] == str(d.fy) and r['kind'] == '정정':
                out.append((r['rcept_no'], load_br(r['rcept_no']) if r['text_path'] else None, r['report_nm']))
    _cache[key] = out
    return out


def check_variants(rows, task):
    """본공시·본 보고서 기준 행의 *_text 칸이 추가·정정공시(연차보고서)나 정정판(사업보고서)에 그대로 있는지 보고, 다르면 note 에 사실만."""
    for r in rows:
        ref = r.get('rcept_no_or_url') or r.get('rcept_no') or ''
        if not ref:
            continue
        try:
            d = doc_by_ref(ref)
        except Exception:
            continue
        vals = [(c, r.get(c, '')) for c in VAR_FIELDS[task] if r.get(c, '') not in ('', NA)]
        vals = [(c, v) for c, v in vals if cmpnorm(v, d.xml) in d.cmp]  # 이 문서에서 온 칸만
        add = []
        for item in variants_of(d):
            if d.kind == 'BR':
                rc, vd, nm = item
                if vd is None:
                    add.append(f'정정 {rc}({nm}): XML md 없음(첨부정정·파일 미제공 등) — 대조 못 함')
                    VAR_STAT['BR 정정 대조 못 함'] = VAR_STAT.get('BR 정정 대조 못 함', 0) + 1
                    continue
                VAR_STAT['BR 정정 대조'] = VAR_STAT.get('BR 정정 대조', 0) + 1
                for c, v in vals:
                    if cmpnorm(v, True) in vd.cmp:
                        continue
                    lines = [ln for ln in v.split('\n') if len(cmpnorm(ln, True)) >= 4]
                    lost = [ln for ln in lines if cmpnorm(ln, True) not in vd.cmp]
                    add.append(f'정정 {rc}: {c} 칸 글 {len(lines)}줄 중 {len(lost)}줄이 정정판에 없음' +
                               (f'(첫 줄 「{lost[0].strip()[:40]}」)' if lost else '(줄은 모두 있으나 한 덩어리로 이어서는 나오지 않음)'))
                    VAR_STAT['BR 정정 다름'] = VAR_STAT.get('BR 정정 다름', 0) + 1
            else:
                typ, vd = item
                VAR_STAT['AR 추가·정정 대조'] = VAR_STAT.get('AR 추가·정정 대조', 0) + 1
                if len(vd.cmp) < 0.2 * len(d.cmp):
                    add.append(f'{typ} {vd.ref} 는 본공시와 다른 짧은 글(공백 뺀 {len(vd.cmp):,}자) — 이 행 글 없음')
                    VAR_STAT['AR 짧은 별도 글'] = VAR_STAT.get('AR 짧은 별도 글', 0) + 1
                    continue
                for c, v in vals:
                    if cmpnorm(v) in vd.cmp:
                        continue
                    lines = [ln for ln in v.split('\n') if len(cmpnorm(ln)) >= 4]
                    lost = [ln for ln in lines if cmpnorm(ln) not in vd.cmp]
                    if not lost:
                        add.append(f'{typ} {vd.ref} 대조: {c} 칸 글의 줄은 모두 {typ} 글에 있으나 한 덩어리로 이어서는 나오지 않음(줄 순서·쪽 머리글 위치가 다름)')
                        VAR_STAT['AR 추가·정정 줄 순서만 다름'] = VAR_STAT.get('AR 추가·정정 줄 순서만 다름', 0) + 1
                    else:
                        add.append(f'{typ} {vd.ref} 대조: {c} 칸 글 {len(lines)}줄 중 {len(lost)}줄이 {typ} 글에 없음(첫 줄 「{lost[0].strip()[:40]}」)')
                        VAR_STAT['AR 추가·정정 줄 없음'] = VAR_STAT.get('AR 추가·정정 줄 없음', 0) + 1
        if add:
            r['note'] = (r['note'] + ' / ' if r.get('note') else '') + ' / '.join(add)


def add_pdf13(rows, col, refcol):
    """FY2025 사업보고서(OpenDART XML) 행: 13차 보관 본문 PDF 글에서 같은 글(공백·「|」·<br> 지움)의 쪽을 찾아 page 에 덧붙임(COMMON15 page 규칙)."""
    for r in rows:
        ref = r.get(refcol, '')
        if str(r.get('fy')) != '2025' or not re.fullmatch(r'\d{14}', ref) or r.get(col, NA) == NA:
            continue
        P = pdf13(r['corp_label'])
        if not P or P[0] != ref:
            continue
        rc, st, marks = P
        mp = [m[0] for m in marks]
        v = re.sub(r'\s+', '', r[col].replace('<br>', '').replace('|', ''))
        pgs = []
        for i in range(0, max(1, len(v) - 15), 15):
            w = v[i:i + 15]
            if len(w) < 8:
                break
            k = st.find(w)
            if k >= 0 and st.find(w, k + 1) < 0:
                pgs.append(marks[bisect.bisect_right(mp, k) - 1][1])
            if len(pgs) > 400:
                break
        if pgs:
            med = sorted(pgs)[len(pgs) // 2]
            pgs = [g for g in pgs if abs(g - med) <= 8]  # 우연히 다른 쪽에 하나만 있는 짧은 조각은 뺌
            a, b = min(pgs), max(pgs)
            r['page'] += f" / {'p.%d' % a if a == b else 'p.%d~%d' % (a, b)}(본문 PDF, 13차 보관)"
        else:
            r['note'] = (r['note'] + ' / ' if r['note'] else '') + '13차 보관 본문 PDF 글에서 같은 글의 쪽을 못 찾음'


def ar_committee_count(corp, fy, name):
    """연차보고서(공시연도 fy+1, 본공시)에서 그 위원회 절(번호 붙은 큰 절 제목에 위원회 이름) 글의 첫 「총 N회 개최」류 문구(비교용)."""
    try:
        d = load_ar(corp, fy + 1)
    except Exception:
        return None, '', ''
    key = re.sub(r'\s', '', name)
    rows = [r for r in kit_rows() if r['파일명'] == d.extra.get('fname')]
    rows.sort(key=lambda r: (int(r['섹션순번']), int(r['chunk_seq'])))
    parent, txt, pg, title = '', '', '', ''
    for r in rows:
        if re.match(r'^\d+\.$', r['섹션번호'].strip()):
            if txt:
                break
            parent = re.sub(r'\s', '', r['섹션제목_원문'])
            title = f"{r['섹션번호']} {r['섹션제목_원문']}"
            pg = r['시작페이지']
        if parent == key or (key in parent and len(parent) <= len(key) + 4):
            txt += r['본문']
    if not txt:
        return None, '', ''
    m = re.search(r'총\s*(\d+)\s*(?:회|차례)[^,.\n]{0,15}개최[^\s,.]{0,6}', re.sub(r'\s+', ' ', txt))
    if not m:  # 「총 N회의 ○○위원회가 소집되었습니다」 꼴
        m = re.search(r'총\s*(\d+)\s*(?:회|차례)[^,.\n]{0,25}(?:소집|개최)[^\s,.]{0,8}', re.sub(r'\s+', ' ', txt))
    if not m:
        return -1, f'「{title}」(p.{pg})', ''
    return int(m.group(1)), f'「{title}」(p.{pg})', re.sub(r'\s+', ' ', m.group(0))


def ar_hint_count(corp, fy, h):
    """연차보고서(공시연도 fy+1, 본공시)의 h['s']~h['e'] 문장에서 h['rx'] 첫 무리 = 횟수(비교용). h['title'] = 절 이름(표시용)."""
    d = load_ar(corp, fy + 1)
    txt, p, e = d.grab(h['s'], h.get('e'), after=h.get('after'))
    m = re.search(h['rx'], re.sub(r'\s+', ' ', txt))
    if not m:
        return -1, f"「{h['title']}」({d.page(p, e)})", ''
    return int(m.group(1)), f"「{h['title']}」({d.page(p, e)})", re.sub(r'\s+', ' ', m.group(0))


def searched_page(d):
    """「문서에 없음」 행의 page: 찾아본 절(사업보고서 Ⅵ 1. 이사회에 관한 사항)."""
    if d.kind == 'BR':
        labs = [m[1] for m in d.marks if '「1. 이사회에 관한 사항」' in m[1] and '[표' not in m[1]]
        if labs:
            return labs[-1] + ' (찾은 곳)'
    return '(찾은 곳은 note)'


def build_F2(sp):
    raise NotImplementedError


def build_F3(sp):
    raise NotImplementedError


def build_CHK(sp):
    raise NotImplementedError


SPEC_FUNCS.append(spec_F_KB)

# ───────────── 작업 F-2 ─────────────
ALLD = []
ALLR = []  # 표 「회차」 칸의 서로 다른 값
DATE_RX = re.compile(r'(20\d\d)\s*[.\-년]\s*(\d{1,2})\s*[.\-월]\s*(\d{1,2})')


def table_dates(txt):
    """md 표에서 「개최일자」·「개최일」 칸의 서로 다른 날짜(머리행 칸 번호 기준). 칸을 못 찾으면 글 전체의 날짜.
    ALLD(전역)에 날짜가 적힌 행마다 날짜를 쌓음(같은 날 두 번 연 회의 셈용)."""
    ALLD.clear()
    ALLR.clear()
    rcol = [None]
    dates, col = [], None
    for ln in txt.split('\n'):
        if ln.startswith('|'):
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            hit = [i for i, c in enumerate(cells) if re.sub(r'\s|<br>', '', c) in ('개최일자', '개최일', '개최일시', '일자', '개최일자(회차)')]
            if hit:
                col = hit[0]
                continue
            if col is not None:
                # 칸 수가 머리행과 다르면(병합) 날짜 패턴이 있는 첫 칸
                nz = lambda c: re.sub(r'<br>|\s', '', c)
                cand = nz(cells[col]) if col < len(cells) else ''
                m = DATE_RX.search(cand) or None
                if not m:
                    for c in cells[:max(col + 2, 3)]:
                        m = DATE_RX.search(nz(c))
                        if m:
                            break
                if m:
                    k = (m.group(1), int(m.group(2)), int(m.group(3)))
                    ALLD.append(k)
                    if k not in dates:
                        dates.append(k)
        else:
            col = col  # 표 밖 줄은 그대로
    if not dates:
        for m in DATE_RX.finditer(re.sub(r'<br>|\s', '', txt)):
            k = (m.group(1), int(m.group(2)), int(m.group(3)))
            if k not in dates:
                dates.append(k)
        ALLD.clear()
        return dates, False
    return dates, True


def comp_row(d, region, name, occ='last'):
    """구성 표(region=(시작 글, upto 글))에서 첫 칸이 위원회 이름인 줄부터 다음 위원회 줄 앞까지."""
    a = d.find(region[0])
    b = d.find(region[1], a + 1)
    if a < 0 or b < 0:
        raise ValueError(f'구성 표 범위 못 찾음 {region}')
    seg = d.display[a:b]
    norm = lambda c: re.sub(r'\s|<br>|■', '', c)
    lines, off, starts = seg.split('\n'), a, []
    pos = []
    for ln in lines:
        pos.append(off)
        off += len(ln) + 1
    key = norm(name)
    hits = []
    for i, ln in enumerate(lines):
        if ln.startswith('|'):
            first = norm(ln.strip().strip('|').split('|')[0])
            if first == key or (first.startswith(key) and len(first) <= len(key) + 2):
                hits.append(i)
    if not hits:
        raise ValueError(f'구성 표에 {name} 없음')
    i0 = hits[-1] if occ == 'last' else hits[0]
    j = i0 + 1
    while j < len(lines):
        ln = lines[j]
        if not ln.startswith('|'):
            break
        first = norm(ln.strip().strip('|').split('|')[0])
        if '위원회' in first and first != key:
            break
        if first in ('위원회명', '위원회', '구분'):
            break
        j += 1
    p, e = pos[i0], pos[j - 1] + len(lines[j - 1])
    return d.display[p:e], p, e, len(hits)


def build_F2(sp):
    co, fy = sp['co'], sp['fy']
    d = get_doc(sp['doc'], co)
    notes = [sp['note']] if sp.get('note') else []
    if sp.get('agenda') is None:
        return {'corp_label': co, 'fy': fy, 'committee': sp['committee'], 'established': NA, 'held_count': NA, 'agenda_list_text': NA,
                'subsidiary_related': NA, 'members_text': NA, 'rcept_no': d.ref, 'page': sp.get('page') or searched_page(d), 'note': ' / '.join(notes),
                'doc_name': d.doc_name, 'collected_at': d.collected_at}
    agenda, loc = field(sp['agenda'], co, d, 'F2', fy, notes, 'agenda_list_text')
    _, p, e = loc
    # 구성
    if sp.get('members_region'):
        md = get_doc(sp.get('members_doc', sp['doc']), co)
        mtxt, mp, me, nh = comp_row(md, sp['members_region'], sp.get('members_name', sp['committee']))
        SPANS.add('F2', co, fy, md, mp, me)
        if md is not d:
            notes.append(f'members_text 는 {md.doc_kind} {md.ref} {md.page(mp, me)}')
        else:
            notes.append(f'members_text 위치 {md.page(mp, me)}' + (f'(구성 표에 기간별 {nh}번 나와 마지막 기간 행)' if nh > 1 else ''))
    else:
        mtxt, _ = field(sp.get('members'), co, d, 'F2', fy, notes, 'members_text')
    est, _ = field(sp.get('established'), co, d, 'F2', fy, notes, 'established')
    if est == NA:
        notes.append(sp.get('est_note', 'established: 찾은 범위(사업보고서 Ⅵ 1. 이사회에 관한 사항·연차보고서 해당 위원회 절, 검색어 「설치」「신설」)에 설치일 없음'))
    if sp.get('held'):
        held, hn = held_from(sp['held'], {'agenda_list_text': agenda})
        notes.append(hn)
    else:
        ds, intable = table_dates(agenda)
        nrow, ndis = len(ALLD), len(ds)
        if sp.get('ar_hint'):
            n_ar, t_ar, m_ar = ar_hint_count(co, fy, sp['ar_hint'])
        else:
            n_ar, t_ar, m_ar = (ar_committee_count(co, fy, sp.get('ar_name', sp['committee'])) if d.kind == 'BR' else (None, '', ''))
        nhoe = len(ALLR)
        tbl = (f'사업보고서 표 개최일자가 적힌 행 {nrow}개(서로 다른 날짜 {ndis}개)'
               if intable else f'개최일자 칸을 못 찾아 글 안 서로 다른 날짜 {ndis}개')
        if n_ar is not None and n_ar >= 0 and (n_ar == nrow or n_ar == ndis):
            held = str(n_ar)
            notes.append(f'held_count 는 연차보고서 {t_ar} 원문 「{m_ar}」 — {tbl}')
        else:
            held = str(nrow if intable else ndis)
            notes.append('(판단) held_count 는 ' + tbl + ' 중 ' + ('행 수' if intable else '날짜 수') + '를 셈' +
                         (f'; 연차보고서 {t_ar} 「{m_ar}」 — 횟수가 다름' if (n_ar is not None and n_ar >= 0) else
                          ('; 연차보고서 그 절에서 「총 N회 개최」 문구 못 찾음' if n_ar == -1 else '')))
            if n_ar is not None and n_ar >= 0:
                print('  !! F2 횟수 다름', co, fy, sp['committee'], n_ar, nrow, ndis)
        if d.kind == 'BR':
            notes.append('(판단) 안건 목록은 사업보고서 Ⅵ 위원회 활동 표를 씀' + (f' — 연차보고서 {t_ar} 에 같은 해 회의별 서술이 있음' if t_ar else ' — 연차보고서(본공시) 목차에서 이 위원회 절을 찾지 못함'))
    sub = 'Y' if re.search('자회사|그룹|계열사', re.sub(r'\s+', '', agenda)) else 'N'
    return {'corp_label': co, 'fy': fy, 'committee': sp['committee'], 'established': est, 'held_count': held, 'agenda_list_text': agenda,
            'subsidiary_related': sub, 'members_text': mtxt, 'rcept_no': d.ref,
            'page': d.page(p, e) + (' (6차 섹션 시작페이지)' if d.kind == 'AR_kit' else ''),
            'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}


def f2_blocks(co, fy, after, seq, region, doc=None, names=None, extra=None):
    """seq = [(위원회 원문 이름, 머리 글, 다음 머리 글)] — 사업보고서 Ⅵ 위원회 활동 표 블록."""
    for item in seq:
        com, head, nxt = item[:3]
        opt = item[3] if len(item) > 3 else {}
        sp = dict(co=co, fy=fy, committee=com, doc=doc or ('BR', fy),
                  agenda=S(head, upto=nxt, after=after) if head else None,
                  members_region=region if head and not opt.get('no_members') else None,
                  members_name=opt.get('members_name', com))
        sp.update({k: v for k, v in opt.items() if k not in ('members_name', 'no_members')})
        F2_SPECS.append(sp)


def spec_F2_KB():
    co = 'KB금융지주'
    after = ['VI. 이사회 등 회사의 기관에 관한 사항', '다. 이사회내 위원회']
    reg = ('다. 이사회내 위원회', '- 감사위원회')
    common = ''
    f2_blocks(co, 2025, after, [
        ('계열사대표이사후보추천위원회', '- 계열사대표이사후보추천위원회', '- 감사위원후보추천위원회', dict(note='자회사대표이사후보추천위원회에 해당하는 KB 위원회 이름(원문). ' + common)),
        ('내부통제위원회', '- 내부통제위원회', '- 계열사대표이사후보추천위원회', dict(note=common)),
        ('감사위원회', '- 감사위원회', '- 리스크관리위원회', dict(note=common)),
        ('ESG위원회', '- ESG위원회', '- 사외이사후보추천위원회', dict(note=common)),
        ('리스크관리위원회', '- 리스크관리위원회', '- 평가보상위원회', dict(note=common)),
    ], reg)
    f2_blocks(co, 2024, after, [
        ('계열사대표이사후보추천위원회', '- 계열사대표이사후보추천위원회', '- 감사위원후보추천위원회', dict(note='자회사대표이사후보추천위원회에 해당하는 KB 위원회 이름(원문). ' + common)),
        ('내부통제위원회', None, None, dict(note='사업보고서 FY2024 Ⅵ 「다. 이사회내 위원회」 구성 표·활동 표와 연차보고서 FY2024(공시연도 2025) 목차에 내부통제위원회 없음(찾은 범위: 두 문서 전문 「내부통제위원회」). FY2025 사업보고서 활동 표 기간이 「2025.3.26 ~ 2025.12.31」')),
        ('감사위원회', '- 감사위원회', '- 리스크관리위원회', dict(note=common)),
        ('ESG위원회', '- ESG위원회', '- 사외이사후보추천위원회', dict(note=common)),
        ('리스크관리위원회', '- 리스크관리위원회', '- 평가보상위원회', dict(note=common)),
    ], reg)


SPEC_FUNCS.append(spec_F2_KB)


def spec_F_SH():
    co = '신한금융지주'
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        doc = ('AR', yr)
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹경영회의', doc=doc,
            src=S('당사는 그룹경영회의 운영규정 제2조에 따라', upto='나. 구성'),
            members=S('그룹경영회의는 그룹경영회의 운영규정 제3조', '부서장이 담당합니다.'),
            chair=S('회의의 위원장은 대표이사 회장이며', '직무를 대행합니다.'),
            cadence=S('그룹경영회의는 위원장의 소집에 따라', '조정할 수 있습니다.'),
            agenda=S(f'그룹경영회의는 {fy}년', '사항들입니다.'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*차례'),
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹리스크협의회', doc=doc,
            src=S('그룹리스크협의회는 그룹리스크협의회규정 제2조에 따라', upto='나. 구성'),
            members=S('그룹리스크협의회는 그룹리스크협의회규정 제3조', upto='다. 협의절차'),
            chair=S('그룹리스크협의회의 위원장은 당사의 위험관리책임자', '참석시킬 수 있습니다.'),
            cadence=S('그룹리스크협의회규정 제4조에 따라', '수시로 소집합니다.'),
            agenda=S('라. 활동내역', upto='감독당국 권고사항', after='그룹리스크협의회규정 제4조에 따라'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='같은 협의회를 사업보고서 Ⅱ 리스크관리 서술에도 적음 — 연차보고서 글을 기준으로 함',
        ))


SPEC_FUNCS.append(spec_F_SH)


def spec_F_SH2():
    co = '신한금융지주'
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹 위기관리협의회', doc=('AR', yr),
            src=S('그 밖에', '의견을 개진하였습니다.', after='매분기 보고 받았습니다'),
            note='위험관리위원회 절의 활동 개요 문장에 위험관리위원회가 보고 받은 안건 이름으로만 나옴(구성·주재자·주기·개최 횟수 서술은 찾은 범위 — 연차보고서 전문·사업보고서 Ⅱ·Ⅵ 「위기관리협의회」 — 에 없음)' +
                 ('. 같은 절 회의별 내역에 「보고-마. 그룹 위기관리위원회 및 위기관리협의회 개최 결과 보고 : 그룹 위기관리규정에 따라 …」 문장이 있음(p.159 섹션)' if yr == 2026 else ''),
        ))
    F_SPECS.append(dict(
        co=co, fy=2025, body='그룹 위기관리위원회', doc=('AR', 2026),
        src=S('보고-마. 그룹 위기관리위원회 및 위기관리협의회 개최 결과 보고 :', '정기적으로 위험관리위원회에 보고하고 있습니다.'),
        cadence=None,
        note='위험관리위원회 회의별 내역 안의 보고 안건 설명 문장에만 나옴(구성·주재자·주기·개최 횟수 서술은 찾은 범위 — 연차보고서 FY2025 전문·사업보고서 FY2025 Ⅱ·Ⅵ 「위기관리위원회」 — 에 없음). FY2023·FY2024 연차보고서에는 「그룹 위기관리위원회」 낱말 없음',
    ))
    # 사업보고서 Ⅵ 2. 감사제도 「(2) 준법지원인(준법감시인) 등의 주요 활동내역 및 그 처리결과」 표
    tbl_note = '사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「(2) 준법지원인 등의 주요 활동내역 및 그 처리결과」 표(칸: 점검일시 | 주요 활동 내용 | 점검 결과)의 행 — cadence_text 는 그 행의 「점검일시」 칸 글'
    for fy in (2023, 2024):
        row = S('분기 | 그룹 준법감시인협의회/자금세탁방지협의회/소비자보호협의회 | 적정함')
        for body in ('그룹 준법감시인협의회', '자금세탁방지협의회', '소비자보호협의회'):
            F_SPECS.append(dict(co=co, fy=fy, body=body, doc=('BR', fy), src=row,
                                cadence=S('분기', after='내부거래 점검'),
                                note=tbl_note + '. 한 칸에 「그룹 준법감시인협의회/자금세탁방지협의회/소비자보호협의회」로 함께 적힘(이름은 「/」로 나눔). 구성·주재자·개최 횟수 서술 없음'))
    F_SPECS.append(dict(co=co, fy=2025, body='그룹 준법감시인협의회', doc=('BR', 2025), src=S('분기 | 그룹 준법감시인협의회 | 적정함'),
                        cadence=S('분기', after='내부거래 점검'),
                        note=tbl_note + '. 구성·주재자·개최 횟수 서술 없음. FY2025 표에는 FY2023·24 의 「자금세탁방지협의회/소비자보호협의회」 대신 아래 반기 행이 있음'))
    for body in ('내부통제운영위원회', '그룹 자금세탁방지 협의체'):
        F_SPECS.append(dict(co=co, fy=2025, body=body, doc=('BR', 2025),
                            src=S('반기 | 내부통제위원회/내부통제운영위원회/그룹 자금세탁방지 협의체 | 적정함'),
                            cadence=S('반기', after='그룹 준법감시인협의회 | 적정함'),
                            members=(S('내부통제운영위원회는 대표이사를 위원장으로 하고', '임원을 위원으로 한다.', doc=('AR', 2026)) if body == '내부통제운영위원회' else None),
                            chair=(S('내부통제운영위원회는 대표이사를 위원장으로 하고', doc=('AR', 2026)) if body == '내부통제운영위원회' else None),
                            note=tbl_note + '. 한 칸에 「내부통제위원회/내부통제운영위원회/그룹 자금세탁방지 협의체」로 함께 적힘(내부통제위원회는 이사회 내 위원회라 F-2)' +
                            ('. 연차보고서 FY2025 첨부 내부통제 관련 규정 「제8조의2(내부통제운영위원회) ① 그룹사는 내부통제 관련 주요 사항을 심의하기 위하여 내부통제운영위원회를 설치할 수 있다.」(p.251 부근 섹션) — chair·members 는 같은 조 ②항' if body == '내부통제운영위원회' else '. 구성·주재자·개최 횟수 서술 없음')))


SPEC_FUNCS.append(spec_F_SH2)


def spec_F2_SH():
    co = '신한금융지주'
    after = ['(2) 이사회내의 위원회 활동내역']
    reg = ('(1) 위원회의 구성, 설치목적 및 권한사항', '(2) 이사회내의 위원회 활동내역')
    f2_blocks(co, 2025, after, [
        ('자회사최고경영자후보추천위원회', '(아) 자회사최고경영자후보추천위원회', '라. 이사의 독립성', dict(note='자회사대표이사후보추천위원회에 해당하는 신한 위원회 이름(원문)')),
        ('내부통제위원회', '(라) 내부통제위원회', '(마) 사외이사및감사위원후보추천위원회',
         dict(established=S('주) 2025년 3월 내부통제위원회 신설'), note='established 는 Ⅵ 구성 표 아래 주석 글')),
        ('감사위원회', '(다) 감사위원회', '(라) 내부통제위원회', {}),
        ('ESG전략위원회', '(사) ESG전략위원회', '(아) 자회사최고경영자후보추천위원회', {}),
        ('위험관리위원회', '(가) 위험관리위원회', '(나) 보수위원회', {}),
    ], reg)
    f2_blocks(co, 2024, after, [
        ('자회사최고경영자후보추천위원회', '(사) 자회사최고경영자후보추천위원회', '라. 이사의 독립성', dict(note='자회사대표이사후보추천위원회에 해당하는 신한 위원회 이름(원문)')),
        ('내부통제위원회', None, None, dict(note='사업보고서 FY2024 Ⅵ 구성 표·활동 표에 내부통제위원회 없음(찾은 범위: Ⅵ 1. 이사회에 관한 사항 전문 「내부통제위원회」). FY2025 사업보고서 Ⅵ 주석 「주) 2025년 3월 내부통제위원회 신설」')),
        ('감사위원회', '(다) 감사위원회', '(라) 사외이사및감사위원후보추천위원회', {}),
        ('ESG전략위원회', '(바) ESG전략위원회', '(사) 자회사최고경영자후보추천위원회', {}),
        ('위험관리위원회', '(가) 위험관리위원회', '(나) 보수위원회', {}),
    ], reg)


SPEC_FUNCS.append(spec_F2_SH)


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
    return {'item_id': sp['item_id'], 'item_text': sp.get('item_text', REQ_LINE_F2), 'corp_label': co, 'fy': sp['fy'], 'result': sp.get('result', '원문 있음'),
            'where': sp.get('where', ''), 'rcept_no_or_url': d.ref, 'page': d.page(p, e) + (' (6차 섹션 시작페이지)' if d.kind == 'AR_kit' else ''),
            'source_excerpt': txt, 'note': sp.get('note', '')}


def spec_SH_jahoesa():
    co = '신한금융지주'
    est = S('2021년 3월 25일에는 자회사경영관리위원회를 이사회내위원회에 편입하여', doc=('AR', 2024))
    F2_SPECS.append(dict(co=co, fy=2022, committee='자회사경영관리위원회', doc=('BR', 2022),
                         agenda=S('7) 자회사경영관리위원회', upto='라. 이사의 독립성', after=['(2) 이사회내의 위원회 활동내역']),
                         members_region=('(1) 위원회의 구성, 설치목적 및 권한사항', '(2) 이사회내의 위원회 활동내역'),
                         established=est, est_note='',
                         note='함께 볼 것(신한 자회사경영관리위원회) 때문에 넣은 FY2022 행. established 는 연차보고서 FY2023 「10. 자회사최고경영자후보추천위원회 (舊 자회사경영관리위원회)」 절 문장(이사회내위원회 편입일)'))
    F2_SPECS.append(dict(co=co, fy=2023, committee='자회사최고경영자후보추천위원회', doc=('BR', 2023),
                         agenda=S('(사) 자회사최고경영자후보추천위원회', upto='라. 이사의 독립성', after=['(2) 이사회내의 위원회 활동내역']),
                         members_region=('(1) 위원회의 구성, 설치목적 및 권한사항', '(2) 이사회내의 위원회 활동내역'),
                         established=est, est_note='',
                         note='함께 볼 것(신한 자회사경영관리위원회) 때문에 넣은 FY2023 행. 연차보고서 FY2023 절 제목 「10. 자회사최고경영자후보추천위원회 (舊 자회사경영관리위원회)」 — 2023년 3월 명칭 변경(확인_F_g1.csv SH-1~3)'))
    item = '신한 「자회사경영관리위원회」가 없어지거나 자회사최고경영자후보추천위원회로 합쳐진 시점과 사유(FY2022·FY2023)'
    CHK_SPECS.extend([
        dict(item_id='F2-SH-1', item_text=REQ_LINE_F2, co=co, fy=2023, doc=('AR', 2024),
             src=S('2023년의 경우 2월 28일 개최한 제1회 정기이사회를 통해', '명칭을 자회사최고경영자후보추천위원회로 변경하였으며,'),
             where='연차보고서 FY2023 「2. 이사회」(정관 변경 서술) — F2_g1.csv 신한금융지주 FY2023 자회사최고경영자후보추천위원회 행',
             note='시점: 2023.2.28 제1회 정기이사회 승인 → 2023.3.23 정기주주총회 확정(정관 일부 변경). 원문 낱말은 「명칭을 … 변경」(없어지거나 합쳐졌다는 낱말은 없음)'),
        dict(item_id='F2-SH-2', item_text=REQ_LINE_F2, co=co, fy=2023, doc=('AR', 2024),
             src=S('당사는 2023년 3월 자회사경영관리위원회 및 자회사경영관리위원회규정의 명칭을', '심의/결의 대상을 정비하였습니다.'),
             where='연차보고서 FY2023 「10. 자회사최고경영자후보추천위원회 (舊 자회사경영관리위원회)」 — 같은 행',
             note='사유로 적힌 원문 글: 「자회사최고경영자 후보 추천이라는 본연의 기능에 보다 충실할 수 있도록 심의/결의 대상을 정비」(source_excerpt 안)'),
        dict(item_id='F2-SH-3', item_text=REQ_LINE_F2, co=co, fy=2023, doc=('AR', 2024),
             src=S('결의-나. 정관 일부 변경의 건 :', '부의하기로 결의하였습니다.'),
             where='연차보고서 FY2023 「2. 이사회」 활동내역(제1회 정기이사회 결의-나) — 같은 행',
             note='정관 변경 안건 설명 문장'),
        dict(item_id='F2-SH-4', item_text=REQ_LINE_F2, co=co, fy=2022, doc=('BR', 2022),
             src=S('자회사경영관리위원회 운영 개선(案)', after='7) 자회사경영관리위원회'),
             where='F2_g1.csv 신한금융지주 FY2022 자회사경영관리위원회 행(활동 표의 보고 안건)',
             note='FY2022 사업보고서 Ⅵ 위원회 활동 표 7) 자회사경영관리위원회의 보고 안건 이름(내용 서술은 없음). FY2022 사업보고서에는 위원회 이름이 아직 「자회사경영관리위원회」'),
        dict(item_id='F2-SH-5', item_text=REQ_LINE_F2, co=co, fy=2023, doc=('AR', 2024),
             src=S('9. 자회사경영관리위원회 (2021.3.25 신설)', '9. 자회사최고경영자후보추천위원회 (2023.3.23 개정)'),
             where='연차보고서 FY2023 첨부 정관(이사회내 위원회 조항 개정 이력)',
             note='정관 조항 이력 표기: 2021.3.25 신설, 2023.3.23 개정(명칭)'),
    ])


SPEC_FUNCS.append(spec_SH_jahoesa)


def spec_F_HN():
    co = '하나금융지주'
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        doc = ('AR', yr)
        F_SPECS.append(dict(
            co=co, fy=fy, body='경영관리협의회', doc=doc,
            src=S('하나금융지주는 당사와 자회사 등에 대한 전략적 의사결정을', upto='나. 협의 절차'),
            cadence=S('경영관리협의회는 연 1회 이상 소집함을 원칙으로', '수시로 소집'),
            members=S('협의회는 당사 최고경영자인', upto='라. 활동내역 개요'),
            chair=S('협의회는 당사 최고경영자인 하나금융지주 대표이사 회장을 위원장으로 하고'),
            agenda=S('라. 활동내역 개요', upto='리스크관리집행위원회', after='협의회는 당사 최고경영자인'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='연차보고서 첨부 「경영관리협의회 규정」도 있음',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='관계회사경영관리위원회', doc=doc,
            src=S('제1조(목적) 이 규정은 관계회사경영관리위원회', '역할을 수행한다.', after='관계회사경영관리위원회 규정 제정 2008-03-31'),
            members=S('① 위원회는 대표이사 회장, 부회장, 하나은행장', '정하는 사람으로 구성한다.', after='관계회사경영관리위원회 규정 제정 2008-03-31'),
            chair=S('② 위원장은 대표이사 회장으로 한다.', after='관계회사경영관리위원회 규정 제정 2008-03-31'),
            cadence=S('① 위원회는 심의ㆍ결의사항이 있을 시 위원장이 수시로 소집한다.', after='관계회사경영관리위원회 규정 제정 2008-03-31'),
            agenda=S('① 위원회는 다음의 각호의 사항을 심의, 결의한다.', '그룹 임원후보추천위원회에 보고하여야 한다.', after='관계회사경영관리위원회 규정 제정 2008-03-31'),
            note='연차보고서 첨부 「관계회사경영관리위원회 규정」(제1조~제4조·제6조) 글 — agenda_text 는 규정의 결의사항 조항(그해 실제 안건 아님). 그해 개최 횟수 서술은 찾은 범위(연차보고서 전문 「관계회사경영관리위원회」)에 없음; 그룹임원후보추천위원회 회의 내역에 「관계회사경영관리위원회 결의사항」 보고 안건으로 나옴. 연차보고서 조직도에 이름이 있음',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹경영전략협의회', doc=doc,
            src=S('그룹임원워크숍 및 그룹경영전략협의회를 통해', '마련한 후,'),
            agenda=S('그룹임원워크숍 및 그룹경영전략협의회를 통해', '마련한 후,'),
            note='이사회 역할(경영목표·전략의 수립) 서술 안의 문장 — agenda_text 는 같은 문장(경영계획(안) 마련). 연차보고서 조직도에는 「경영전략협의회」로 적힘. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 전문 「경영전략협의회」)에 없음',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹감사협의회', doc=doc,
            src=S('그룹감사협의회 연간활동 보고'),
            agenda=S('그룹감사협의회 연간활동 보고'),
            note='감사위원회 회의 내역의 보고 안건 이름으로만 나옴(감사위원회가 보고 받은 「…그룹감사협의회 연간활동 보고」). 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 전문·사업보고서 「그룹감사협의회」)에 없음',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='소비자리스크관리운영위원회', doc=doc,
            src=S('소비자리스크관리운영위원회 규정의 제정 및'),
            note='「1. 지배구조 일반」 내부기관 표의 소비자리스크관리위원회(이사회 내 위원회) 결의사항 칸에 「소비자리스크관리운영위원회 규정의 제정 및 (개폐)」로 이름만 나옴(표 글이 PDF 추출로 줄이 섞임). 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 전문 「소비자리스크관리운영위원회」)에 없음',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='인재육성위원회', doc=doc,
            src=S('1) 조직도', '리스크관리집행위원회'),
            note='「1. 지배구조 일반 > 나. 지배구조 현황 > 1) 조직도」 그림의 글자에 이름만 나옴(PDF 글 추출 순서라 그림 안 배치는 이 글로 알 수 없음). 역할·구성 서술 없음(찾은 범위: 연차보고서 전문 「인재육성위원회」)',
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='리스크관리집행위원회', doc=doc,
            src=S('리스크관리집행위원회는 위험관리업무의 효율적 수행을 위해', upto='나. 협의절차'),
            cadence=S('리스크관리집행위원회는 월 1회 소집함을 원칙으로', '수시로 소집할 수 있도록 하고 있습니다.'),
            members=S('리스크관리집행위원회규정 제2조에 따라', upto='라. 활동내역'),
            chair=S('관리집행위원장은 그룹리스크관리 담당 임원이며', '소집할 수 있습니다.'),
            agenda=S('라. 활동내역', upto='감독당국 권고사항', after='리스크관리집행위원회규정 제2조에 따라'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='「14. 리스크관리집행위원회」 절. (판단) 이사회 내 위원회가 아닌 회의체로 둠 — 이 절 원문 「리스크관리위원회로부터 위임받은 세부적인 사항을 수립 및 수행하는 역할」. 조직도에도 이름이 있음',
        ))
    for yr in (2025, 2026):
        F_SPECS.append(dict(
            co=co, fy=yr - 1, body='내부통제협의체', doc=('AR', yr),
            src=S('이사회내 위원회로 설치되는 내부통제위원회와 대표이사를 위원장으로 하는 내부통제협의체', '마련하였습니다.'),
            chair=S('대표이사를 위원장으로 하는 내부통제협의체'),
            note='2024년 12월 제10회 이사회의 그룹내부통제 규정 개정 서술 안의 문장(설치 근거 마련). 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 전문 「내부통제협의」)에 없음',
        ))


SPEC_FUNCS.append(spec_F_HN)


def spec_F2_HN():
    co = '하나금융지주'
    after = ['라. 이사회내 위원회', '(활동내용)']
    reg = ('라. 이사회내 위원회', '(활동내용)')
    gim = '자회사대표이사후보추천위원회에 해당하는 하나 위원회로 둔 것(판단): 연차보고서 내부기관 표의 이 위원회 결의사항에 「주요 관계회사 최고경영자 후보 추천 및 경영승계계획」이 있음'
    aud = dict(agenda=None)
    for fy, seq in ((2025, [
        ('그룹임원후보추천위원회', '■ 그룹임원후보추천위원회', '■ 지속가능경영위원회', dict(note=gim)),
        ('내부통제위원회', '■ 내부통제위원회', '■ 경영발전보상위원회', {}),
        ('지속가능경영위원회', '■ 지속가능경영위원회', '■ 소비자리스크관리위원회', {}),
        ('리스크관리위원회', '■ 리스크관리위원회', '■ 내부통제위원회', {}),
    ]), (2024, [
        ('그룹임원후보추천위원회', '■ 그룹임원후보추천위원회', '■ 지속가능경영위원회', dict(note=gim)),
        ('내부통제위원회', None, None, dict(note='사업보고서 FY2024 Ⅵ 이사회내 위원회 구성 표·활동 내용에 내부통제위원회 없음(찾은 범위: Ⅵ 1. 이사회에 관한 사항 전문 「내부통제위원회」). FY2025 구성 표에 「내부통제위원회 | (2025.3. ~ )」')),
        ('지속가능경영위원회', '■ 지속가능경영위원회', '■ 소비자리스크관리위원회', {}),
        ('리스크관리위원회', '■ 리스크관리위원회', '■ 경영발전보상위원회', {}),
    ])):
        f2_blocks(co, fy, after, seq, reg)
        F2_SPECS.append(dict(co=co, fy=fy, committee='감사위원회', doc=('BR', fy),
                             agenda=S('라. 감사위원회의 활동', upto='마. 감사위원회 교육실시 계획', after=['마. 이사의 독립성', '가. 감사위원 현황']),
                             members_region=reg, members_name='감사위원회',
                             note='감사위원회 활동 표는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항 > 라. 감사위원회의 활동」'))


SPEC_FUNCS.append(spec_F2_HN)


def spec_F_WR():
    co = '우리금융지주'
    for yr in (2024, 2025, 2026):
        fy = yr - 1
        doc = ('AR', yr)
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹경영협의회', doc=doc,
            src=S('당사는 그룹경영협의회규정 제1조에 따라', upto='나. 구성'),
            members=S('그룹경영협의회규정 제2조에 따라', upto='다. 운영현황'),
            chair=S('임종룡', '의장', after='그룹경영협의회 위원 현황'),
            cadence=S('그룹경영협의회는 매월 1회 개최함을 원칙으로', '소집할 수 있습니다.'),
            agenda=S(f'그룹경영협의회는 {fy}년 총', '필요한 사항입니다.'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹리스크관리협의회', doc=doc,
            src=S('그룹리스크관리협의회는 리스크관리위원회가 수립한', '역할을 수행합니다.'),
            cadence=S('그룹리스크관리협의회는 분기 1회 이상 개최하는 것을 원칙으로', '수시로 소집할 수 있습니다.'),
            members=S('그룹리스크관리협의회 위원은 지주회사 리스크관리책임자', upto='라. 활동내역 및 평가'),
            chair=S('그룹리스크관리협의회의 의장은 지주회사 리스크관리책임자이며', '참석시킬 수 있습니다.'),
            agenda=S('(1) 활동내역 개요', upto='감독당국 권고사항', after='그룹리스크관리협의회 위원은 지주회사 리스크관리책임자'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='같은 협의회를 사업보고서 Ⅱ 리스크관리 서술에도 적음 — 연차보고서 글을 기준으로 함',
        ))
    for fy in (2023, 2024, 2025):
        F_SPECS.append(dict(
            co=co, fy=fy, body='그룹준법감시인협의회', doc=('BR', fy),
            src=S('그룹준법감시인협의회 등 회의체 운영'),
            note='사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 준법감시인 지원조직 현황 표의 ' + ('준법정책부' if fy == 2025 else '준법지원부') +
                 ' 주요 활동내역 칸에 회의체 이름으로만 나옴(「…그룹준법감시인협의회 등 회의체 운영」). 구성·주재자·주기·개최 횟수 서술은 찾은 범위(사업보고서 전문·연차보고서 전문 「준법감시인협의회」)에 없음',
        ))
    F_SPECS.append(dict(
        co=co, fy=2025, body='내부통제협의회', doc=('AR', 2026),
        src=S('책무구조도상 내부통제체계를 총괄하는 대표이사는', '역할을 수행하고 있습니다.'),
        chair=S('대표이사는 ‘내부통제협의회’의 의장을 역임하고 있으며'),
        note='「2. 이사회」 역할 서술 안의 문장. 윤리·내부통제위원회규정(첨부)의 보고사항에 「1. 내부통제협의회 활동내용」, 사업보고서 FY2025 Ⅵ 준법정책부 활동 칸에 「윤리·내부통제위원회, 내부통제협의회, 그룹준법감시인협의회 등 회의체 운영」. 구성·주기·개최 횟수 서술은 찾은 범위에 없음. FY2023·FY2024 연차보고서에는 「내부통제협의회」 낱말 없음',
    ))


SPEC_FUNCS.append(spec_F_WR)


def spec_F2_WR():
    co = '우리금융지주'
    after = ['(2) 이사회내의 위원회 활동내역']
    reg = ('(1) 위원회별 명칭', '(2) 이사회내의 위원회 활동내역')
    for fy, seq in ((2025, [
        ('자회사대표이사후보추천위원회', '6) 자회사대표이사후보추천위원회', '7) ESG경영위원회', {}),
        ('윤리·내부통제위원회', '4) 윤리·내부통제위원회', '5) 임원후보추천위원회', dict(note='내부통제위원회에 해당하는 우리 위원회 이름(원문)')),
        ('ESG경영위원회', '7) ESG경영위원회', '라. 이사의 독립성', {}),
        ('리스크관리위원회', '2) 리스크관리위원회', '3) 보상위원회', {}),
    ]), (2024, [
        ('자회사대표이사후보추천위원회', '5) 자회사대표이사후보추천위원회', '6) ESG경영위원회', {}),
        ('내부통제위원회', None, None, dict(note='사업보고서 FY2024 Ⅵ 위원회 구성 표·활동 내역(1)~6))에 내부통제 관련 이사회 내 위원회 없음(찾은 범위: Ⅵ 1. 이사회에 관한 사항 전문 「내부통제」). 사업보고서 FY2023 정관 변경 이력: 2023.03.24 제4기 정기주주총회 「이사회內 위원회 중 내부통제관리위원회 삭제」; FY2025 사업보고서 활동 내역에 「4) 윤리·내부통제위원회」')),
        ('ESG경영위원회', '6) ESG경영위원회', '라. 이사의 독립성', {}),
        ('리스크관리위원회', '2) 리스크관리위원회', '3) 보상위원회', {}),
    ])):
        f2_blocks(co, fy, after, seq, reg)
        F2_SPECS.append(dict(co=co, fy=fy, committee='감사위원회', doc=('BR', fy),
                             agenda=S('(3) 감사위원회의 주요활동내역', upto='(4) 감사위원회 교육 실시 계획', after=['(2) 감사위원회 위원의 독립성']),
                             members_region=reg, members_name='감사위원회',
                             note='감사위원회 활동 표는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항 > 가. 감사위원회 > (3) 감사위원회의 주요활동내역」(1. 이사회에 관한 사항의 「1) 감사위원회」는 그곳을 참조하라는 글)'))


SPEC_FUNCS.append(spec_F2_WR)


# ───────────── NH농협금융지주 (연차보고서 FY2019~2023 없음 — FY2023 은 사업보고서만) ─────────────
NH_NO_AR23 = 'NH 연차보고서 FY2023(공시연도 2024)은 이번 입력에 없음(연차보고서15_목록_g1.csv 에 NH 파일 없음 — 문서목록15b_F_g1.csv 에 「없음」 행) — 사업보고서만 봄'


def spec_F_NH():
    co = 'NH농협금융지주'
    for yr in (2025, 2026):
        fy = yr - 1
        doc = ('AR', yr)
        sec_ceo = '11. 최고경영자협의회' if yr == 2025 else '최고경영자협의회 > 가. 역할(이 글에 절 번호 글 없음 — 6차 섹션 제목)'
        sec_rmc = '12. 리스크관리협의회' if yr == 2025 else '리스크관리협의회 > 가. 역할(이 글에 절 번호 글 없음 — 6차 섹션 제목)'
        F_SPECS.append(dict(
            co=co, fy=fy, body='최고경영자협의회', doc=doc, section=sec_ceo,
            src=S('당사는 그룹의 주요 현안에 대한 전략적 경영의사결정을 지원하기 위하여 최고경영자', upto='나. 협의절차'),
            cadence=S('협의가 필요한 사항이 있을 경우 위원장이 소집하며'),
            chair=S('협의회의 위원장은 금융지주 회장으로 하고'),
            members=S('협의회의 위원장은 금융지주 회장으로 하고', upto='라. 활동내역 개요'),
            agenda=S(f'{fy}년 최고경영자협의회는 경영전략회의와 연계하여',
                     '농협금융 혁신 방안, CEO간 소통 등' if fy == 2024 else '2025년 하반기 경영전략, 농협금융 중장기 전략, CEO간 소통'),
            held=HRE('agenda_text', r'총\s*(\d+)\s*차례'),
            note='연차보고서 첨부 「최고경영자협의회규정」도 있음. 사업보고서 FY%d Ⅱ·Ⅵ 에는 「최고경영자협의회」 낱말 없음' % fy,
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='리스크관리협의회', doc=doc, section=sec_rmc,
            src=S('리스크관리협의회는 금융지주 리스크관리위원회로부터 위임받은', '역할을 합니다.'),
            cadence=S('리스크관리협의회는 분기 1회 이상 소집하는 것을 원칙으로', '서면으로 운영할 수 있습니다.'),
            chair=S('리스크관리협의회 의장은 지주회사 위험관리책임자로 하고'),
            members=S('리스크관리협의회 의장은 지주회사 위험관리책임자로 하고', upto='라. 활동내역 개요'),
            agenda=(S('2024년에는 총 7회의 리스크관리협의회가 개최되었고', '농협금융 유동성 비상계획 개정(안) 보고') if fy == 2024 else
                    S('2025 년에는 총 8회의 리스크관리협의회가 개최되었고', '자회사별 리스크관리위원회 중요결의사항 보고 보고', eafter='8차')),
            held=HRE('agenda_text', r'총\s*(\d+)\s*회'),
            note='같은 협의회를 사업보고서 FY%d Ⅲ 주석(위험관리)·Ⅳ 이사의 경영진단(「실무적 의사결정기구인 리스크관리협의회」)에도 적음 — 연차보고서 글을 기준으로 함' % fy,
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='경영전략회의', doc=doc, section=sec_ceo.replace('가. 역할', '라. 활동내역 개요'),
            src=S(f'{fy}년 최고경영자협의회는 경영전략회의와 연계하여', '실시함.'),
            note='최고경영자협의회 활동 개요 문장에 「경영전략회의와 연계하여」로 이름만 나옴. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY%d 전문·사업보고서 FY%d Ⅱ·Ⅵ 「경영전략회의」)에 없음' % (fy, fy) +
                 ('. 사업보고서 FY2024 Ⅵ 사외이사 교육 표에 「2023년도 농협금융 경영전략회의」(2022.11.10 이사회사무국 내부교육) 행이 있음' if fy == 2024 else ''),
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='내부통제협의회', doc=doc,
            section='첨부 「내부통제위원회규정」 제11조',
            src=S('제11조(내부통제협의회) ① 위원회는 위원회의 원활한 업무수행을 보좌하기 위하여', '정한 바에 따른다.'),
            note='첨부 내부통제위원회규정 조문(설치 근거) — 같은 규정 보고사항에 「2. 내부통제협의회 운영 현황」. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY%d 전문 「내부통제협의」)에 없음' % fy +
                 ('. 사업보고서 FY2024 에는 「내부통제협의회」 낱말 없음' if fy == 2024 else
                  '. 사업보고서 FY2025(20260331004252) Ⅱ 「5. 재무건전성 등 기타 참고사항」과 Ⅳ 「2. 개요」에 「먼저, 내부통제협의회를 개최하는 등 그룹 차원의 내부통제를 강화하고 금융소비자보호 체계를 개선하였습니다.」 문장(개최 횟수·날짜 없음)'),
        ))
        F_SPECS.append(dict(
            co=co, fy=fy, body='경영협의회', doc=doc,
            section='첨부 「지배구조내부규범」 제29조',
            src=S('제29조 (임원 및 부서장 등에 대한 교육) ① 지주회사는 임원 및 부서장 등을 위해 교', '실시하여야 한다.'),
            note='첨부 지배구조내부규범 교육 조문에 「교육 및 연수제도의 일환으로 경영협의회」로 이름만 나옴. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY%d 전문·사업보고서 FY%d 「경영협의회」)에 없음' % (fy, fy),
        ))
    # FY2024 연차보고서에만: ESG 협의회 2개, 인사조정위원회
    esg_src = S('그룹 ESG 경영 내재화 및 추진을 위해', '체계를 구축했습니다.')
    for body, chair in (('ESG전략협의회', '회장 주관「ESG전략협의회」'), ('ESG추진협의회', '미래성장부문장 주관「ESG추진협의회」')):
        F_SPECS.append(dict(
            co=co, fy=2024, body=body, doc=('AR', 2025),
            section='【 참고 : 농협금융 2024년 ESG 주요 추진현황 】 > 가. 농협금융 ESG 경영 거버넌스 확립',
            src=esg_src, chair=S(chair),
            note='ESG위원회 절 뒤 「참고」 글의 문장. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2024 전문 「%s」)에 없음. 연차보고서 FY2025 에는 이 이름 없음(「ESG업무방법」 제정 서술에 「위원회·협의체 운영」만). 사업보고서 FY2024 녹색경영 문단에는 「CEO 주관 협의회, 부사장 주관 협의회」로 적힘(같은 협의회인지 원문으로 확인 안 됨 — 따로 행)' % body,
        ))
    F_SPECS.append(dict(
        co=co, fy=2024, body='인사조정위원회', doc=('AR', 2025), section='13. 감독 당국 권고사항 및 개선계획 > 가. 금융감독원 수시검사',
        src=S('【지배구조 관련 조치요구사항】', '공로금 관련 규정 개선'),
        note='금융감독원 수시검사(2024.3) 지배구조 관련 조치요구사항 글에 이름만 나옴. 역할·구성·주기 서술은 찾은 범위(연차보고서 FY2024·FY2025 전문, 사업보고서 FY2023~FY2025 「인사조정위원회」)에 없음',
    ))
    # 사업보고서 녹색경영 문단(FY2023~FY2025) — 이름 없이 「… 주관 협의회」
    green = {2023: S('전사적 녹색경영 추진을 위해 이사회', '내부 구동체계를 구축하였으며'),
             2024: S('전사적 녹색경영 추진을 위해 이사회', '내부 구동체계를 구축하였으며'),
             2025: S('전사적 친환경 경영 추진을 위해 이사회', 'ESG경영 거버넌스를 구축하였으며')}
    for fy, src in green.items():
        for body in (('CEO 주관 협의회', '부사장 주관 협의회') if fy >= 2024 else ('CEO 주관 협의회',)):
            F_SPECS.append(dict(
                co=co, fy=fy, body=body, doc=('BR', fy),
                src=src, chair=S(body.replace(' 협의회', ''), after=src['s']),
                note='(판단) 원문에 고유 이름 없이 「%s」로만 적혀 body_name 은 그 글. 사업보고서 「4. 작성기준일 이후 발생한 주요사항 등 기타사항」 녹색경영 문단. 구성·주기·개최 횟수 서술 없음' % body +
                     ('. FY2023 문단에는 「부사장 주관 협의회」 없음. ' + NH_NO_AR23 if fy == 2023 else
                      ('. 연차보고서 FY2024 「참고」 글에는 회장 주관「ESG전략협의회」·미래성장부문장 주관「ESG추진협의회」로 적힘(같은 협의회인지 원문으로 확인 안 됨)' if fy == 2024 else
                       '. 연차보고서 FY2025 에는 ESG 협의회 이름 없음')),
            ))
    # FY2023: 사업보고서만
    F_SPECS.append(dict(
        co=co, fy=2023, body='리스크관리협의회', doc=('BR', 2023),
        src=S('연결기업의 리스크관리 조직은 리스크관리 최고 의사결정기구인 리스크관리위원회와 실무적 의사결정기구인 리스크관리협의회', '심의, 의결할 수 있도록 규정하고 있습니다.', occ=1),
        note='사업보고서 Ⅳ 이사의 경영진단 및 분석의견의 리스크관리 서술(같은 글이 Ⅲ 연결재무제표 주석에도 있음; 다음 문장에 「관리 실태를 정기적으로 리스크관리협의체에 보고」). 구성·주재자·주기·개최 횟수 서술 없음. ' + NH_NO_AR23,
    ))


SPEC_FUNCS.append(spec_F_NH)


def spec_F_extra():
    """이름만 나오는 그룹 회의체 보충(KB·신한·하나·우리 — 연차보고서·사업보고서 전문 「협의회|협의체|회의체」 훑기로 찾음)."""
    for fy in (2023, 2024, 2025):
        F_SPECS.append(dict(
            co='KB금융지주', fy=fy, body='그룹 아키텍처 협의회' if fy >= 2024 else '그룹 아키텍처협의회', doc=('BR', fy),
            src=(S('또한 그룹 아키텍처 협의회 참여를 통해', '지원을강화하고 있습니다.') if fy >= 2024 else
                 S('또한 그룹 아키텍처협의회에 참여하는 등', 'Digitalization을 지원할 것입니다.')),
            note='사업보고서 Ⅱ 「5. 재무건전성 등 기타 참고사항」의 「(8) IT서비스업」 업종 서술 안 문장(「당사」는 그 업종 서술의 회사 — 원문 그대로). 구성·주재자·주기·개최 횟수 서술은 찾은 범위(사업보고서 FY%d 전문·연차보고서 「아키텍처 협의회」)에 없음' % fy,
        ))
    F_SPECS.append(dict(
        co='신한금융지주', fy=2023, body='그룹 회계감사 실무자 회의체', doc=('AR', 2024),
        src=S('또한 그룹 회계감사 실무자 회의체를 신설하여', '소통을 강화하였습니다.'),
        note='감사위원회 절 활동 서술 문장(신설 연도 글은 이 문장에 없음). 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2023~FY2025 전문 「실무자 회의체」)에 없음; FY2024·FY2025 연차보고서에는 이 이름 없음',
    ))
    F_SPECS.append(dict(
        co='하나금융지주', fy=2025, body='위험관리책임자 협의체', doc=('AR', 2026),
        src=S('파) 그룹 공동투자 리스크관리체계 개선', '리스크관리체계를 강화할 필요가 있음.'),
        section='15. 감독당국 권고사항 및 개선계획 > 가. 금융감독원 정기검사',
        note='금융감독원 정기검사 지적·개선 필요사항 글(「위험관 리책임자 협의체 개최 요건을 … 명확화」 — PDF 글 줄바꿈 그대로). body_name 은 줄바꿈을 뺀 원문 글. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2024·FY2025 전문 「책임자 협의체」)에 없음',
    ))
    F_SPECS.append(dict(
        co='우리금융지주', fy=2023, body='기업문화협의회', doc=('AR', 2024),
        src=S('기업문화 혁신을 위해 외부전문가를 초청하여', '강조함'),
        note='사외이사 활동(조언) 표 안의 글에 「기업문화협의회 소속 임직원」으로 이름만 나옴. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2023~FY2025 전문 「기업문화협의회」)에 없음',
    ))


SPEC_FUNCS.append(spec_F_extra)


def spec_F2_NH():
    co = 'NH농협금융지주'
    after = ['(2) 이사회내의 위원회 활동내역']
    reg = ('(1) 이사회내 위원회 구성현황', '(2) 이사회내의 위원회 활동내역')
    gim = '(판단) 자회사대표이사후보추천위원회에 해당하는 NH 위원회로 둔 것: 사업보고서 활동 표 각주 「(주2) 완전자회사 대표이사 추천 시 위원회 구성」·자회사 대표이사 후보 안건이 이 위원회에 있음(따로 자회사 대표 추천 위원회 없음)'
    hints = {
        2024: dict(gim=('2024년 중 위원회는 총 19회 개최되었습니다.', None, '임원후보추천위원회 > 라. 활동내역 및 평가'),
                   rmc=('2024년 총 13회의 리스크관리위원회가 소집되었고', None, '리스크관리위원회 > 1) 활동내역 개요'),
                   esg=('2024년 ESG위원회(舊 사회가치 및 녹색금융 위원회)는 5회 개최하였으며', None, 'ESG위원회 > 1) 활동내역 개요'),
                   aud=('2024년도에는 총 13회의', '감사위원회가 소집되었습니다.', '감사위원회 > 1) 활동내역 개요'),
                   icc=('2024년도에는 총 3', '회의 내부통제위원회가 소집되었습니다.', '8. 내부통제위원회 > 다. 활동내역 및 평가')),
        2025: dict(gim=('2025년 중 위원회는 총 9회 개최되었습니다.', None, '임원후보추천위원회 > 1) 활동내역 개요'),
                   rmc=('2025년 총 14회의 리스크관리위원회가 소집되었고', None, '리스크관리위원회 > 1) 활동내역 개요'),
                   esg=('2025년 ESG위원회는 5회 개최하였으며', None, 'ESG위원회 > 1) 활동내역 개요'),
                   aud=('2025년도에는 총 13회의', None, '감사위원회 > 1) 활동내역 개요'),
                   icc=('2025 년도에는 총 6회의 내', '부통제위원회가 소집되었습니다', '내부통제위원회 > 1) 활동내역 개요')),
    }
    for fy in (2024, 2025):
        h = hints[fy]
        mk = lambda k, rx=r'총\s*(\d+)\s*회': dict(s=h[k][0], e=h[k][1], rx=(rx if 'ESG' not in h[k][0] else r'(\d+)\s*회\s*개최'), title=h[k][2])
        icc_est = S('6. 내부통제위원회(2024.10.30.신설)', doc=('AR', fy + 1))
        f2_blocks(co, fy, after, [
            ('임원후보추천위원회', '1) 임원후보추천위원회', '2) 리스크관리위원회', dict(note=gim, ar_hint=mk('gim'),
                                                                      est_note='established: 찾은 범위(사업보고서 Ⅵ 1. 이사회에 관한 사항, 연차보고서 첨부 정관 제43조 위원회 목록 — 이 위원회는 날짜 표기 없음)에 설치일 없음')),
            ('내부통제위원회', '6) 내부통제위원회', '라. 이사의 독립성', dict(established=icc_est, ar_hint=mk('icc'),
                                                               note='established 는 연차보고서 첨부 정관 제43조 위원회 목록 표기' + ('. 첫 개최는 확인_F_g1.csv F2-NH-1~5' if fy == 2024 else ''))),
            ('감사위원회', '5) 감사위원회', '6) 내부통제위원회', dict(established=S('2012.03.02. 감사위원회 설치'), ar_hint=mk('aud'),
                                                          note='established 는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「감사위원회 설치 여부」 칸 글')),
            ('ESG위원회', '4) ESG위원회', '5) 감사위원회', dict(established=S('5. ESG위원회(2021.03.02.신설)(2024.10.30.개정)', doc=('AR', fy + 1)), ar_hint=mk('esg'),
                                                        members_name='ESG위원회[(舊)사회가치 및 녹색금융위원회]',
                                                        note='사업보고서 구성 표의 위원회 이름 칸은 「ESG위원회[(舊)사회가치 및 녹색금융위원회]」. established 는 연차보고서 첨부 정관 제43조 위원회 목록 표기')),
            ('리스크관리위원회', '2) 리스크관리위원회', '3) 보수위원회', dict(ar_hint=mk('rmc'),
                                                              est_note='established: 찾은 범위(사업보고서 Ⅵ 1. 이사회에 관한 사항, 연차보고서 첨부 정관 제43조 위원회 목록 — 이 위원회는 날짜 표기 없음)에 설치일 없음')),
        ], reg)
    item = REQ_LINE_F2
    CHK_SPECS.extend([
        dict(item_id='F2-NH-1', item_text=item, co=co, fy=2024, doc=('AR', 2025),
             src=S('① 제2024년도 제1차 내부통제위원회 : 2024. 11. 22.(금) 11:20 ~ 11:40', '내부통제위원회 운영계획(안)'),
             where='F2_g1.csv NH농협금융지주 FY2024 내부통제위원회 행(연차보고서 「8. 내부통제위원회 > 다. 활동내역 및 평가 > 2) 회의 개최내역」)',
             note='첫 개최일 2024.11.22(제1차), 첫 안건: (의안 제1호) 내부통제위원회 위원장 선임(안), (의안 제2호) 내부통제위원회 운영계획(안) — 둘 다 가결. 같은 회의 「주요 안건 내용」에 「내부통제위원회 신설에 따른 위원장 선임」「내부통제위원회 신설에 따른 위원회 운영방안 수립」'),
        dict(item_id='F2-NH-2', item_text=item, co=co, fy=2024, doc=('BR', 2024),
             src=S('| 1 | 2024.11.22. | (의안 제1호) 내부통제위원회 위원장 선임(안) |', '(의안 제2호) 내부통제위원회 운영계획(안)', after='6) 내부통제위원회'),
             where='F2_g1.csv NH농협금융지주 FY2024 내부통제위원회 행(사업보고서 Ⅵ 활동 표 첫 행)',
             note='사업보고서 FY2024 Ⅵ 「(2) 이사회내의 위원회 활동내역」 6) 내부통제위원회 표 첫 회차 — 연차보고서와 같은 날짜·안건'),
        dict(item_id='F2-NH-3', item_text=item, co=co, fy=2024, doc=('AR', 2025),
             src=S('◦ (의안 제28호) 농협금융지주 정관 일부개정정관(안)', '설치 등을 반영한 정관 개정'),
             where='연차보고서 FY2024 「2. 이사회 > 다. 활동내역 > 2) 회의 개최내역」 ⑪ 2024년 제11차 정기이사회(2024. 10. 29.) 주요 안건 내용',
             note='같은 회의에 「(의안 제29호) 내부통제위윈회규정 제정(안)」(원문 표기 「위윈회」). 정관 제43조 목록 표기는 「6. 내부통제위원회(2024.10.30.신설)」'),
        dict(item_id='F2-NH-4', item_text=item, co=co, fy=2024, doc=('AR', 2025),
             src=S('6. 내부통제위원회(2024.10.30.신설)'),
             where='F2_g1.csv NH농협금융지주 FY2024·FY2025 내부통제위원회 행 established 칸(연차보고서 첨부 정관 제43조)',
             note='설치일 표기'),
        dict(item_id='F2-NH-5', item_text=item, co=co, fy=2024, doc=('AR', 2025),
             src=S('◦ (의안 제36호) 이사회 내 위원회 위원 선임(안)', '서은숙 이사'),
             where='연차보고서 FY2024 「2. 이사회 > 다. 활동내역 > 2) 회의 개최내역」 ⑫ 2024년 제12차 임시이사회(2024. 11. 22.(금) 11:10 ∼ 12:00) 주요 안건 내용',
             note='원문 시각: 위원 선임 제12차 임시이사회 2024.11.22 11:10~12:00, 같은 날 제1차 내부통제위원회 11:20~11:40(F2-NH-1)'),
    ])


SPEC_FUNCS.append(spec_F2_NH)


# ───────────── 작업 F-3 (연차보고서 FY2025 = 공시연도 2026, 본공시) ─────────────
_14 = {}


def rows14():
    if not _14:
        _14['rows'] = list(csv.DictReader(open(f'{ROOT}/handoff/14차_조직인원겸직/14_지원조직_인원.csv', encoding='utf-8-sig')))
    return _14['rows']


def cmp14(co, kinds):
    """14차 14_지원조직_인원.csv 의 사업보고서 표 행(출처 칸에 rcept_no, 조직 종류가 kinds 로 시작, 「연차보고서」 아님) 요약(비교용 사실)."""
    out = []
    for r in rows14():
        if r['회사'] != co or '연차보고서' in r['조직 종류'] or not re.search(r'\d{14}', r['출처']):
            continue
        if any(r['조직 종류'].startswith(k) for k in kinds):
            if '추출 범위' in r['부서(팀)명']:
                out.append(f"「{r['조직 종류']}」 행 — 부서·인원 칸 「추출 범위에 없음」")
            else:
                out.append(f"{re.sub(chr(10), '', r['부서(팀)명'])} {r['직원수'][:30]}")
    if not out:
        return f"14차 14_지원조직_인원.csv 에 {co} 사업보고서 표 행({'/'.join(kinds)}) 없음"
    return f"14차 14_지원조직_인원.csv(사업보고서 FY2025 표, {'/'.join(kinds)}): " + '; '.join(out)


def br_loc(co, phrase, fy=2025):
    """사업보고서 FY 본문에서 phrase(표 제목 글) 뒤 첫 「[표 n]」 표지의 위치 글."""
    d = load_br(br_id(co, fy))
    p = d.find(phrase)
    if p < 0:
        raise ValueError(f'br_loc 못 찾음 {co} {phrase}')
    labs = [m[1] for m in d.marks if m[0] > p and '[표' in m[1]]
    return f'사업보고서 FY{fy}({d.ref}) 「{phrase}」 표({labs[0] if labs else d.label_at(p)})'


def build_F3(sp):
    co, fy = sp['co'], 2025
    d = get_doc(('AR', 2026), co)
    notes = [sp['note']] if sp.get('note') else []
    if sp.get('na'):
        return {'corp_label': co, 'fy': fy, 'function': NA, 'unit_name': NA, 'headcount': NA, 'concurrent_or_dispatched': NA, 'duty_text': NA,
                'rcept_no_or_url': d.ref, 'page': '(찾은 곳은 note)', 'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at}
    anc, (ad, ap, ae) = field(sp['anchor'], co, d, 'F3', fy, notes, 'anchor')
    vals = {}
    for k in ('function', 'unit', 'conc', 'duty'):
        v = sp.get(k)
        if isinstance(v, dict) and 'after' not in v and sp.get('near'):
            v = dict(v, after=sp['near'])
        fnm = {'function': 'function', 'unit': 'unit_name', 'conc': 'concurrent_or_dispatched', 'duty': 'duty_text'}[k]
        vals[k], lk = field(v, co, d, 'F3', fy, notes, fnm)
        # 15b 검증 고침: 같은 문서의 다른 쪽(섹션)에서 온 칸은 note 에 위치
        if lk and lk[0] is d and k in ('conc', 'duty') and d.page(lk[1], lk[2]) != d.page(ap, ae):
            notes.append(f'{fnm} 위치 {d.page(lk[1], lk[2])} (6차 섹션 시작페이지)')
        if k in ('function', 'unit') and vals[k] != NA and '\n' in vals[k]:
            # 짧은 이름 칸의 PDF 줄바꿈만 지움(공백만 바뀜 — 대조는 공백 무시)
            vals[k] = re.sub(r'(?<=[가-힣])\s*\n\s*(?=[가-힣])', '', vals[k]).replace('\n', ' ')
            notes.append(f"{ {'function': 'function', 'unit': 'unit_name'}[k] } 칸은 PDF 글 줄바꿈을 지움(공백만)")
    hc = sp['headcount']
    if hc is None:
        head = NA
    else:
        head = hc[0]
        notes.append(hc[1].replace('{anc}', re.sub(r'\s+', ' ', anc)))
    return {'corp_label': co, 'fy': fy, 'function': vals['function'], 'unit_name': vals['unit'], 'headcount': head,
            'concurrent_or_dispatched': vals['conc'], 'duty_text': vals['duty'], 'rcept_no_or_url': d.ref,
            'page': d.page(ap, ae) + ' (6차 섹션 시작페이지)', 'note': ' / '.join(notes), 'doc_name': d.doc_name, 'collected_at': d.collected_at,
            '_anchor': anc}


F3_TBL = '연차보고서 FY2025 에 「준법감시인·위험관리책임자 지원조직 현황」이라는 이름의 표는 없음(찾은 범위: 연차보고서 FY2025 전문 「지원조직」「준법감시」「위험관리」「인원」)'
F3_AUD = '연차보고서 FY2025 에 「감사위원회 지원조직(내부감사부서) 현황」이라는 이름의 표는 없음(찾은 범위: 연차보고서 FY2025 전문 「지원조직」「내부감사부서」「감사보조」) — 이 행은 감사위원회 절 「라. 감사보조조직 등」(NH 「라. 감사보좌기구」) 서술 문단에서 옮김(판단: 표 대신 서술)'


def spec_F3():
    # KB — 평가보상위원회 절 「(3) 위험관리, 준법감시 부서의 인원현황」 표
    co = 'KB금융지주'
    near = '(3) 위험관리, 준법감시 부서의 인원현황'
    kbt = '표 「(3) 위험관리, 준법감시 부서의 인원현황」(평가보상위원회 절) 행; 표 아래 「* 2025년 12월말 기준 현재 담당업무 경영진을 제외한 직원 수」. ' + \
          F3_TBL.replace('는 없음', '는 없고 이 표가 있음') + '. 같은 보고서 「(2) 준법감시직원 현황」은 「- 해당사항 없음」'
    F3_SPECS.append(dict(co=co, near=near, anchor=S('리스크관리부 19명', after=near), function=S('위험관리 부서'), unit=S('리스크관리부'),
                         headcount=('19', 'headcount 원문 「{anc}」(인원수 칸) — 비고 칸은 자격 보유 인원(FRM·CFA)'), conc=None,
                         duty=None, note=kbt + '. duty_text·concurrent_or_dispatched: 표·문단에 담당 업무·겸직·파견 글 없음. ' + cmp14(co, ['위험관리'])))
    F3_SPECS.append(dict(co=co, near=near, anchor=S('준법추진부 11명', after=near), function=S('준법 감시 부서'), unit=S('준법추진부'),
                         headcount=('11', 'headcount 원문 「{anc}」(인원수 칸; 문단은 「11명(변호사 4명 포함)」)'), conc=None,
                         duty=None, note=kbt + '. duty_text·concurrent_or_dispatched: 표·문단에 담당 업무·겸직·파견 글 없음. ' + cmp14(co, ['준법감시인 지원'])))
    F3_SPECS.append(dict(co=co, near=['라. 감사보조조직 등', '라. 감사보조조직 등'], anchor=S('감사위원회는 효율적인 감사업무수행을 위하여 감사위원회 보조 기구로 감사부를 두고 있으며', '유지하고 있습니다.'),
                         function=S('감사보조조직'), unit=S('감사부'), headcount=('15', 'headcount 원문 「적정 인원(15명)」(「{anc}」)'),
                         conc=None, duty=None,
                         note=F3_AUD + '. duty_text: 이 문단에 감사부 담당 업무를 따로 적은 문장 없음(감사위원회 보조 기구라는 문장과 「감사부가 감사위원회에 보고하거나 지원한 주요내용」 표만). 겸직·파견 글 없음. ' + cmp14(co, ['감사위원회 지원'])))
    # 신한 — 「(2) 준법감시직원 현황 및 비율」 표, 감사보조조직 문단
    co = '신한금융지주'
    near = '(2) 준법감시직원 현황 및 비율'
    F3_SPECS.append(dict(co=co, near=near, anchor=S('인원 10 0 0 10', after=near), function=S('준법감시직원 현황'), unit=None,
                         headcount=('10', 'headcount 원문 표 행 「{anc}」(칸: 구분 | 준법감시직원* | 재고용직원등 | 기타 | 총계)'), conc=None, duty=None,
                         note='표 「① 준법감시직원 현황 (2025년말 기준 / 준법감시인 제외)」(「기타 지배구조 관련 주요사항 > 나. 인사 관련 내부통제 현황」) — 부서 이름 칸이 없어 unit_name 「문서에 없음」. 같은 곳 ② 비율 표 「총 임직원 수 252 임원 제외 / 겸직 포함」「준법감시직원 수 10 준법감시인 제외」. ' +
                              F3_TBL + '. 담당 업무·겸직·파견 글 없음. ' + cmp14(co, ['준법감시인 지원'])))
    F3_SPECS.append(dict(co=co, na=True,
                         note='(찾은 표) 위험관리책임자 지원조직 — ' + F3_TBL + '; 위험관리 부서 인원 표·문단도 없음(연차보고서 조직도 글자에 「리스크관리팀 (14명)」 — 14차 조직도 행). 사업보고서 FY2025 에도 위험관리책임자 지원조직 표 없음(Ⅵ 「(3) 준법지원인 등 지원조직 현황」만 — ' + br_loc(co, '(3) 준법지원인 등 지원조직 현황') + ')'))
    F3_SPECS.append(dict(co=co, near=['라. 감사보조조직 등', '라. 감사보조조직 등'], anchor=S('감사팀은 팀장 1명, 공인회계사(CPA) 2명, 실무 경력이 풍부한 책임자 이상의 직원으로', '모니터링하고 있습니다.'),
                         function=S('감사보조조직'), unit=S('감사팀'), headcount=None, conc=None,
                         duty=S('감사위원회는 보조조직인 감사팀을 직접 지휘하여 회사와 자회사에 대한 업무감사를 실시하고 자회사의 감사활동을 모니터링하고 있습니다.'),
                         note=F3_AUD + '. headcount: 문단에 총원 숫자 없음(「{0}」). 겸직·파견 글 없음. '.format('팀장 1명, 공인회계사(CPA) 2명, 실무 경력이 풍부한 책임자 이상의 직원으로 구성') + cmp14(co, ['감사위원회 지원'])))
    # 하나 — 「3) 리스크관리, 준법감시 부서의 인원 현황」 표
    co = '하나금융지주'
    near = '3) 리스크관리, 준법감시 부서의 인원 현황'
    hnt = '표 「3) 리스크관리, 준법감시 부서의 인원 현황」(보수위원회 절) 행 — 표 칸: 분류 | 인원수 | 해당부서 평균 근속기간(현재원·전출자) | 비고. ' + \
          F3_TBL.replace('는 없음', '는 없고 이 표가 있음') + '. 같은 보고서 「(2) 준법감시직원 현황」은 「: 해당사항 없음.」. 표의 인원 글은 숫자 뒤에 각주 번호가 붙어 「91)」처럼 추출됨 — headcount 는 문단 「각각 9명, 12명, 7명, 9명」 순서와 맞춤(판단)'
    for unit, n, fn, conc, alab in (('리스크관리팀', '9', '리스크관리 관련 부서', S('1) 관계회사사 파견직원 2명 포함 기준입니다.'), '리스크관리팀 91)'),
                                    ('리스크분석팀', '12', '리스크관리 관련 부서', S('2) 관계회사 겸직직원 4명, 파견직원 1명 포함 기준입니다.'), '리스크분석팀 122)'),
                                    ('리스크검증팀', '7', '리스크관리 관련 부서', S('3) 관계회사 겸직직원 6명 포함 기준입니다.'), '리스크검증팀 73)'),
                                    ('준법지원팀', '9', '준법감시 부서', S('(단, 근무직원 수는 관계사 파견 직원 및 겸직 직원 포함 기준입니다)'), '준법지원팀 9 2.2년')):
        F3_SPECS.append(dict(co=co, near=near, anchor=S(alab, after=near), function=S(fn), unit=S(unit),
                             headcount=(n, 'headcount 원문 표 행 「{anc}」·문단 「2025년 말 기준, 각각 9명, 12명, 7명, 9명(변호사 2명 포함)이 근무」'),
                             conc=conc, duty=None,
                             note=hnt + ('. concurrent_or_dispatched 는 표 아래 각주' if unit != '준법지원팀' else
                                         '. (판단) 이 행에는 각주 번호가 없어 concurrent_or_dispatched 는 문단의 단서 문장(네 부서 공통)') +
                             '. 담당 업무 글 없음. ' + cmp14(co, ['준법감시인 지원' if unit == '준법지원팀' else '위험관리'])))
    F3_SPECS.append(dict(co=co, near=['라. 감사보조조직 등', '라. 감사보조조직 등'], anchor=S('감사보조조직은 2025년말 기준 감사부문장 1명과 감사팀원 10명이며'),
                         function=S('감사보조조직'), unit=S('감사팀'),
                         headcount=('10', 'headcount 원문 「{anc}」 — 감사팀원 수(감사부문장 1명은 따로)'), conc=None,
                         duty=S('감사팀은 감사위원회 지원업무, 재무감사, 업무감사, 대외 감독기관 수검 지원 및 자료 제출 등의 역할을 수행하고 있습니다.'),
                         note=F3_AUD + '. 같은 문단 「관계회사인 하나은행, 하나증권 등의 감사담당 부서 인력 등 관계회사 (전문)인력과 협력을 통해 감사업무를 수행」(겸직·파견 낱말은 없음). ' + cmp14(co, ['감사위원회 지원'])))
    # 우리 — 준법·위험 표 없음, 감사보조조직 문단
    co = '우리금융지주'
    F3_SPECS.append(dict(co=co, na=True,
                         note='(찾은 표) 준법감시인·위험관리책임자 지원조직 — ' + F3_TBL + '; 「위험관리, 준법감시 부서의 인원 현황」·「준법감시직원 현황」 표도 없음. 사업보고서에 있는 곳: ' + br_loc(co, '(3) 준법감시인 등 지원조직 현황') + '. ' + cmp14(co, ['준법감시인 지원', '위험관리'])))
    F3_SPECS.append(dict(co=co, near=['라. 감사보조조직 등', '라. 감사보조조직 등'], anchor=S('감사부는 부서장 1명, 부원 11명(2025년말 현재)이며'),
                         function=S('감사보조조직'), unit=S('감사부'),
                         headcount=('12', '(판단) headcount 는 원문 「{anc}」의 부서장 1명과 부원 11명을 더함'), conc=None,
                         duty=S('감사부는 전년도말 감사위원회의 승인을 득한 연간 감사계획에 의거하여 회사 및 자회사 등에 대한', '연 1회 이사회에 보고하고 있습니다.'),
                         note=F3_AUD + '. 겸직·파견 글 없음. ' + cmp14(co, ['감사위원회 지원'])))
    # NH — 준법·위험 표 없음, 감사보좌기구 문단
    co = 'NH농협금융지주'
    F3_SPECS.append(dict(co=co, na=True,
                         note='(찾은 표) 준법감시인·위험관리책임자 지원조직 — ' + F3_TBL + '; 「위험관리, 준법감시 부서의 인원 현황」·「준법감시직원 현황」 표도 없음(연차보고서 지배구조 현황 표에 「내부통제위원회 준법지원부」「리스크관리위윈회 리스크관리부」로 지원부서 이름만). 사업보고서에 있는 곳: ' + br_loc(co, '(3) 준법지원인 등 지원조직 현황') + '. ' + cmp14(co, ['준법감시인 지원'])))
    F3_SPECS.append(dict(co=co, near='라. 감사보좌기구', anchor=S('2026년 1월 1일자로 부장(M급) 1명, 팀장(3급) 4명, 검사역(4급) 2명 및 검사역(전문직)', '효율적인 업무수행을 하고 있습니다.'),
                         function=S('감사보좌기구'), unit=S('감사부'),
                         headcount=('9', '(판단) headcount 는 원문 「{anc}」의 인원(1+4+2+2)을 더함 — 기준일 2026.1.1(원문)'), conc=None,
                         duty=S('감사부는 감사실시, 결과보고 등 감사업무 수행에 관한 전반적인 사항', '그 결과를 감사위원회에 보고하고 있습니다.'),
                         note=F3_AUD + '. 겸직·파견 글 없음. ' + cmp14(co, ['감사위원회 지원'])))


SPEC_FUNCS.append(spec_F3)



# ───────────── 15b 독립 검증(verify15b_F_g1.py)에서 나온 고침 ─────────────
PDFAR_USED = {}  # PDF 쪽 글 경로 → (회사, fy, 문서명, URL, sha256, 받은 시각)
ZIP13 = f'{ROOT}/handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip'


def pdf_ar_text(sha):
    """kit56 섹션 글과 같은 sha256 PDF 의 「## p.N」 글: gov_old 가 다시 받은 md(문서목록15b_gov_old.csv) → 없으면 13차 연차보고서 md."""
    key = 'PDFAR:' + sha
    if key in _cache:
        return _cache[key]
    res = None
    gl = f'{ROOT}/dart_out/ops15/문서목록15b_gov_old.csv'
    if sha and os.path.exists(gl):
        for g in csv.DictReader(open(gl, encoding='utf-8-sig')):
            if g.get('sha256') == sha and g.get('text_path') and os.path.exists(f"{ROOT}/{g['text_path']}"):
                res = (g['text_path'], open(f"{ROOT}/{g['text_path']}", encoding='utf-8').read(), to_kst(g.get('fetched_at', '')))
                break
    if res is None and sha:
        import zipfile
        z = zipfile.ZipFile(ZIP13)
        for c in G1:
            name = f'13차_지주관리유형/텍스트/연차보고서__{c}.md'
            if name in z.namelist():
                t = z.read(name).decode('utf-8')
                if f'sha256 {sha}' in t[:3000]:
                    res = ('handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip:' + name, t, '')
                    break
    if res:
        path, t, fa = res
        chars, marks, n = [], [], 0
        for ln in t.split('\n'):
            mm = re.match(r'^## p\.(\d+)', ln)
            if mm:
                marks.append((n, int(mm.group(1))))
                continue
            if not marks:
                continue
            s_ = re.sub(r'\s+', '', ln)
            chars.append(s_)
            n += len(s_)
        res = (path, ''.join(chars), marks, fa)
    _cache[key] = res
    return res


def add_pdfpage(rows, col, refcol):
    """kit56 섹션 글(연차보고서 FY2024·25) 행: 같은 sha256 PDF 쪽 글에서 그 칸 글의 실제 PDF 쪽을 찾아 page 에 덧붙임
    (COMMON15 「연차보고서 PDF 는 PDF 쪽 번호」 — 6차 섹션 시작페이지는 그대로 두고 뒤에 붙임)."""
    for r in rows:
        ref = r.get(refcol, '') or ''
        v = r.get(col) or ''
        if not v or v == NA or not ref or re.fullmatch(r'\d{14}', ref):
            continue
        try:
            d = doc_by_ref(ref)
        except Exception:
            continue
        if d.kind != 'AR_kit':
            continue
        P = pdf_ar_text(d.extra.get('sha', ''))
        if not P:
            continue
        path, st, marks, fa = P
        mp = [m[0] for m in marks]
        pg_at = lambda k: marks[bisect.bisect_right(mp, k) - 1][1]
        m0 = re.search(r'p\.(\d+)', r['page'])
        start = int(m0.group(1)) if m0 else 0

        def best(w):
            k, cands = st.find(w), []
            while k >= 0 and len(cands) < 50:
                cands.append(k)
                k = st.find(w, k + 1)
            if not cands:
                return None
            # 6차 섹션 시작페이지와 가장 가까운 곳(앞쪽 3쪽까지 허용)
            return min(cands, key=lambda q: (pg_at(q) < start - 3, abs(pg_at(q) - start)))

        sv = re.sub(r'\s+', '', v)
        k = best(sv)
        if k is not None:
            a, b = pg_at(k), pg_at(k + len(sv) - 1)
        else:
            pgs = []
            for ln in v.split('\n'):
                w = re.sub(r'\s+', '', ln)
                if len(w) >= 8:
                    q = best(w)
                    if q is not None:
                        pgs.append(pg_at(q))
            pgs = [g for g in pgs if start - 3 <= g <= start + 40]
            if not pgs:
                r['note'] = (r['note'] + ' / ' if r['note'] else '') + '같은 sha256 PDF 쪽 글에서 이 행 글의 쪽을 못 찾음'
                continue
            a, b = min(pgs), max(pgs)
        r['page'] += f" / PDF p.{a if a == b else f'{a}~{b}'}(같은 sha256 PDF 쪽 글)"
        PDFAR_USED[path] = (d.corp, d.fy, d.doc_name, d.ref, d.extra.get('sha', ''), fa)


EST_FIX = {
    # (회사, FY, 위원회) → (established 명세, 덧붙일 note)
    ('KB금융지주', 2025, '내부통제위원회'): (S('2025.03.26 | 제17기정기주주총회 | 이사회 결의사항 추가 및 이사회내 위원회(내부통제위원회) 신설', locnote=True),
                                    'established 는 사업보고서 Ⅰ 「5. 정관에 관한 사항」 정관 변경 이력 표 행(정관변경일 | 해당주총명 | 주요변경사항)'),
    ('KB금융지주', 2025, 'ESG위원회'): (S('KB금융그룹은 2020년 전 계열사가 ESG 이행원칙을 선언하고 이사회 내 ESG위원회를 신설하였으며', locnote=True),
                                  'established 는 사업보고서 FY2025 지속가능금융 서술 문장(날짜는 「2020년」만). 연차보고서 FY2025 이사 명단 아래 주석 「ESG위원회는 2020년 3월, 내부통제위원회는 2025년 3월에 신설」'),
    ('KB금융지주', 2024, 'ESG위원회'): (S('ESG위원회는 2020년 3월에 신설', doc=('AR', 2025)), 'established 는 연차보고서 이사 명단 아래 주석 글'),
    ('KB금융지주', 2024, '계열사대표이사후보추천위원회'): (S('지배구조위원회는 2018년 3월 23일에 폐지되어 회장후보추천위원회와 계열사 대표이사후보추천위원회로 분리되었으며', doc=('AR', 2025)),
                                           '(판단) established 는 연차보고서 이사 명단 아래 주석 글 — 원문 낱말은 「분리」(「신설」·「설치」 아님)'),
    ('KB금융지주', 2025, '계열사대표이사후보추천위원회'): (S('지배구조위원회는 2018년 3월 23일에 폐지되어 회장후보추천위원회와 계열사 대표이사후보추천위원회로 분리되었으며', doc=('AR', 2026)),
                                           '(판단) established 는 연차보고서 이사 명단 아래 주석 글 — 원문 낱말은 「분리」(「신설」·「설치」 아님)'),
    ('신한금융지주', 2024, '자회사최고경영자후보추천위원회'): (S('7. 자회사최고경영자후보추천위원회 (2021.3.25 신설, 2023.3.23 개정)', doc=('AR', 2025)),
                                              'established 는 연차보고서 첨부 이사회규정 제17조(이사회내위원회) 목록 글'),
    ('신한금융지주', 2025, '자회사최고경영자후보추천위원회'): (S('7. 자회사최고경영자후보추천위원회 (2021.3.25 신설, 2023.3.23 개정)', doc=('AR', 2026)),
                                              'established 는 연차보고서 첨부 이사회규정 제17조(이사회내위원회) 목록 글'),
    ('신한금융지주', 2024, 'ESG전략위원회'): (S('2015년 3월 25일 국내 금융사 최초로 ESG전략위원회(舊사회책임경영위원회)를 신설하여', doc=('AR', 2025)),
                                     'established 는 연차보고서 「(마) 기업의 사회적 책임 및 지속 가능경영 강화」 문장. 첨부 이사회규정 목록은 「6. ESG전략위원회 (2021.3.25 개정, 2024.5.9 개정)」(개정일만)'),
    ('신한금융지주', 2025, 'ESG전략위원회'): (S('2015년 3월 25일 국내 금융사 최초로 ESG전략위원회(舊사회책임경영위원회)를 신설하여', doc=('AR', 2026)),
                                     'established 는 연차보고서 「(마) 기업의 사회적 책임 및 지속 가능경영 강화」 문장. 첨부 이사회규정 목록은 「6. ESG전략위원회 (2021.3.25 개정, 2024.5.9 개정)」(개정일만)'),
    ('하나금융지주', 2024, '지속가능경영위원회'): (S("2021.03.26 | 제16기 정기주주총회 | 이사회 내에 '지속가능경영위원회'및 '소비자리스크관리위원회' 신설", locnote=True),
                                       'established 는 사업보고서 Ⅰ 「5. 정관에 관한 사항」 정관 변경 이력 표 행'),
    ('하나금융지주', 2025, '지속가능경영위원회'): (S("2021.03.26 | 제16기 정기주주총회 | 이사회 내에 '지속가능경영위원회'및 '소비자리스크관리위원회' 신설", doc=('BR', 2024)),
                                       'established 는 사업보고서 FY2024 Ⅰ 「5. 정관에 관한 사항」 정관 변경 이력 표 행(FY2025 사업보고서 이력 표에는 이 행 없음)'),
    ('하나금융지주', 2025, '내부통제위원회'): (S('2025.03.25 | 제 20기 정기주주총회 | 분기배당절차 개선방안 도입, 이사회의 권한 추가, 이사회 내 위원회 신설(내부통제위원회)', locnote=True),
                                    'established 는 사업보고서 Ⅰ 「5. 정관에 관한 사항」 정관 변경 이력 표 행. 연차보고서 FY2025 「9. 내부통제위원회」 「2025년 3월 25일 제20기 정기주주총회에서 이사회내 위원회로 내부통제위원회를 신설하였습니다」'),
    ('우리금융지주', 2025, '윤리·내부통제위원회'): (S('2025.03.26 | 이사회 내 윤리·내부통제위원회 설치', locnote=True),
                                        'established 는 사업보고서 Ⅰ 「2. 회사의 연혁」 표 행'),
    ('우리금융지주', 2024, 'ESG경영위원회'): (S('2021.03.05 | 이사회 내 ESG경영위원회 설치', locnote=True),
                                     'established 는 사업보고서 Ⅰ 「2. 회사의 연혁」 표 행. 같은 보고서 정관 변경 이력 표에 「2021-03-26 | 제2기정기주주총회 | ·ESG경영위원회 설치 및 운영기준 마련…」 행'),
    ('우리금융지주', 2025, 'ESG경영위원회'): (S('2021.03.05 | 이사회 내 ESG경영위원회 설치', locnote=True),
                                     'established 는 사업보고서 Ⅰ 「2. 회사의 연혁」 표 행'),
    ('신한금융지주', 2024, '감사위원회'): (S('2001.9.1 감사위원회 설치', locnote=True),
                                 'established 는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「감사위원회 설치 여부」 칸 글'),
    ('신한금융지주', 2025, '감사위원회'): (S('2001.9.1 감사위원회 설치', locnote=True),
                                 'established 는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「감사위원회 설치 여부」 칸 글'),
    ('하나금융지주', 2024, '감사위원회'): (S('2005.12.1 감사위원회 설치', locnote=True),
                                 'established 는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「감사위원회 설치 여부」 칸 글'),
    ('하나금융지주', 2025, '감사위원회'): (S('2005.12.01 감사위원회 설치', locnote=True),
                                 'established 는 사업보고서 Ⅵ 「2. 감사제도에 관한 사항」 「감사위원회 설치 여부」 칸 글'),
    # NH 감사위원회: 이미 넣은 established 에 위치(XML 절·표)만 더함
    ('NH농협금융지주', 2024, '감사위원회'): (S('2012.03.02. 감사위원회 설치', locnote=True), ''),
    ('NH농협금융지주', 2025, '감사위원회'): (S('2012.03.02. 감사위원회 설치', locnote=True), ''),
}
NOTE_ADD_F2 = {
    ('신한금융지주', 2024, '내부통제위원회'): '사업보고서 FY2024 Ⅰ 「5. 정관에 관한 사항」 문장: 「공시서류제출일 이후인 2025년 3월 26일 개최 예정인 제24기 정기주주총회의 안건에는 정관 변경(분기배당 기준일, 내부통제위원회 신설)의 건이 포함되어 있습니다」',
    ('하나금융지주', 2024, '내부통제위원회'): '연차보고서 FY2024 「2. 이사회」 2024년 12월 그룹내부통제 규정 개정 서술: 「이사회내 위원회로 설치되는 내부통제위원회와 대표이사를 위원장으로 하는 내부통제협의체에 대한 설치 근거를 마련」',
}


def _fspec(co, fy, body, doc, src, note, section=None, chair=None):
    d = dict(co=co, fy=fy, body=body, doc=doc, src=src, note=note)
    if section:
        d['section'] = section
    if chair:
        d['chair'] = chair
    F_SPECS.append(d)


def spec_verify15b():
    """verify15b_F_g1.py 의 (c) 빠짐 훑기·(d) 「문서에 없음」 반박에서 나온 고침."""
    # F-2 established 반박
    for sp in F2_SPECS:
        k = (sp['co'], sp['fy'], sp['committee'])
        if k in EST_FIX and sp.get('agenda') is not None:
            sp['established'] = EST_FIX[k][0]
            if EST_FIX[k][1]:
                sp['note'] = ((sp.get('note') or '').rstrip() + ' / ' if sp.get('note') else '') + EST_FIX[k][1]
        if k in NOTE_ADD_F2:
            sp['note'] = ((sp.get('note') or '').rstrip() + ' / ' if sp.get('note') else '') + NOTE_ADD_F2[k]
    # 신한 내부통제운영위원회: held·agenda 「문서에 없음」 찾은 범위
    for sp in F_SPECS:
        if sp['co'] == '신한금융지주' and sp['body'] == '내부통제운영위원회':
            sp['note'] += ' / held_count·agenda_text: 찾은 범위(사업보고서 FY2025 전문·연차보고서 FY2025 전문 「내부통제운영위원회」)에 개최 횟수·안건 글 없음'
    # 작업 F 빠짐(출처 글 「협의회|협의체|회의체」 훑기)
    for fy in (2023, 2024, 2025):
        _fspec('신한금융지주', fy, '경영협의회', ('AR', fy + 1),
               S('② 준법감시인은 이사회, 이사회 내 위원회, 경영협의회 등 각종 회의에 참석', '직접 보고할 수 있다.'),
               f'첨부 그룹내부통제규정 준법감시인 조문에 「경영협의회」로 이름만 나옴. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY{fy} 전문·사업보고서 FY{fy} 「경영협의회」)에 없음',
               section='첨부 「그룹내부통제규정」 제35조(의무와 권한)')
        _fspec('신한금융지주', fy, '실무협의회', ('AR', fy + 1),
               S('제11조(실무협의회) 협의회의 원활한 운영과', '실무협의회를 둘 수 있다.'),
               f'첨부 그룹리스크협의회규정 조문(「협의회 내에 실무협의회를 둘 수 있다」 — 여기 「협의회」는 이 규정의 그룹리스크협의회). 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY{fy} 전문 「실무협의회」)에 없음',
               section='첨부 「그룹리스크협의회규정」 제11조(실무협의회)')
        _fspec('KB금융지주', fy, '그룹자체정상화계획위원회', ('AR', fy + 1),
               S('「그룹자체정상화계획위원회규정」에서 보고사항으로 정한 사항'),
               f'첨부 리스크관리위원회규정 보고사항 조문에 규정 이름으로만 나옴(첨부 이사회규정의 규정 목록에도 「그룹자체정상화계획위원회규정」). 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY{fy} 전문·사업보고서 FY{fy} 「자체정상화계획위원회」)에 없음',
               section='첨부 「리스크관리위원회규정」 보고사항')
    _fspec('신한금융지주', 2023, '그룹 IT감사 실무자 협의체', ('AR', 2024),
           S('2024년에는 2선 및 3선 부서 간 협업을 통한 위험평가체계 마련', '소통을 더욱 강화할 예정입니다.'),
           '감사위원회 절 활동 서술(다음 해 계획) 문장 — 「그룹 IT감사 실무자 협의체를 신설하여 … 강화할 예정」. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2023~FY2025 전문 「실무자 협의체」)에 없음')
    _fspec('신한금융지주', 2024, '그룹 감사 담당자 협의체', ('AR', 2025),
           S('또한 그룹 감사 담당자 협의체를 통한', '소통 강화를 추진하였습니다.'),
           '감사위원회 절 활동 서술 문장. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2024 전문 「협의체」)에 없음')
    for body in ('그룹사 감사위원과의 협의체', '그룹 감사업무 담당자 간 협의체'):
        _fspec('신한금융지주', 2024, body, ('AR', 2025),
               S('자회사 소통 강화를 위해서는 그룹사 감사위원과의 협의체를 운영하고', '정례화를 추진할 계획입니다.'),
               '(판단) 원문에 고유 이름 없이 「' + body + '」로 적혀 body_name 은 그 글. 감사위원회 절 다음 해(2025년) 계획 문장. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2024 전문 「협의체」)에 없음')
    _fspec('신한금융지주', 2025, '감사 실무자 협의체', ('AR', 2026),
           S('그룹 공통 이슈에 대해서는 지주 및 자회사 전문 분야 자원을 활용한 공동 감사를 실시하는 등', '강화해 나갈 계획입니다.'),
           '감사위원회 절 다음 해 계획 문장. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2025 전문 「실무자 협의체」)에 없음')
    _fspec('신한금융지주', 2025, '자본시장 협의체', ('AR', 2026),
           S('최영권 이사는 자본시장의 서플라이 체인과 생태계를 고려할 때', '제 언 하 였 습 니다.'),
           '(판단) 이사회 회의 내역(2025년 제1회 정기이사회)의 사외이사 의견 글 안 이름. PDF 글 추출로 표의 안건 칸 글(「가. 2024년 그룹 사업계획 추진실적」)이 문장 사이에 끼어 있음 — 원문 글 그대로. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY2025 전문·사업보고서 FY2025 「자본시장 협의체」)에 없음')
    _fspec('신한금융지주', 2025, '증권-은행 퇴직연금 협의체', ('BR', 2025),
           S('CIB Co-마케팅을 통한 기업 가망고객 협업체계를 확대하고', '적극적으로 나설 계획입니다.'),
           '사업보고서 Ⅱ 사업의 내용 중 금융투자업 계획 서술 문장. 구성·주기·개최 횟수 서술은 찾은 범위(사업보고서 FY2025 전문·연차보고서 FY2025 「퇴직연금 협의체」)에 없음')
    for fy in (2024, 2025):
        _fspec('하나금융지주', fy, '내부통제협의회', ('AR', fy + 1),
               S('제6조의2(내부통제협의회)', '대표이사가 별도로 정하는 바에 따른다.'),
               f'첨부 그룹내부통제 규정 조문(「그룹사는 … 별도의 협의회를 설치할 수 있다」, 구성·운영은 「대표이사가 별도로 정하는 바」). ' + ('「점검☞협의하기」의 ☞ 는 원문 글 글자 그대로(6차 섹션 글·같은 sha256 PDF 쪽 글 모두 ☞). ' if fy == 2025 else '') + f'같은 FY 「내부통제협의체」 행(대표이사를 위원장으로 하는 내부통제협의체 설치 근거 마련 서술)과 같은 협의체인지 원문으로 확인 안 됨 — 따로 행. 구성·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY{fy} 전문 「내부통제협의」)에 없음',
               section='첨부 「그룹내부통제 규정」 제6조의2(내부통제협의회)')
        _fspec('NH농협금융지주', fy, '경영관리협의회', ('AR', fy + 1),
               S('지주회사 리스크관리협의회가 경영관리협의회에 제출한 의견 현황'),
               f'첨부 리스크관리위원회규정 보고사항 조문에 이름만 나옴. 같은 FY 「최고경영자협의회」 행과 같은 협의회인지 원문으로 확인 안 됨 — 따로 행. 구성·주재자·주기·개최 횟수 서술은 찾은 범위(연차보고서 FY{fy} 전문·사업보고서 FY{fy} 「경영관리협의회」)에 없음',
               section='첨부 「리스크관리위원회규정」 보고사항')


SPEC_FUNCS.append(spec_verify15b)

if __name__ == '__main__':
    main()
