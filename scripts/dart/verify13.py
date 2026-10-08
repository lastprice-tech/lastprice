# -*- coding: utf-8 -*-
"""13차(리스크부문 작업 9) 마무리 대조 — 00_목록.md · 00_종합표.csv 와 13차 산출물 전체.

    python3 scripts/dart/verify13.py          # 대조 ①~⑥ → 문제 0 이면 exit 0, 아니면 exit 1. 결과 dart_out/risk13/verify13.txt
    python3 scripts/dart/verify13.py build    # 00_목록.md 의 생성 칸(<!-- build13:begin:… --> 표지 사이: 2-2·2-4·3절·4-1·4-2)과
                                              #   00_종합표.csv(utf-8-sig)를 각 md·상태 CSV 에서 다시 씀. 손으로 쓴 1절·2-1·2-3·4-3 은 그대로.

대조(인자 없이):
 ① scripts/dart/verify13_*.py(이 파일 빼고) 전부와 fix13_*.py check 를 돌려 exit 코드 모음 — raas·law91·law92 와 스크립트 머리에
    「python3 -I scripts/dart/<이름>.py」라고 적힌 것은 python3 -I 로.
 ② 키·OC 값(환경변수 DART_API_KEY·LAW_OC, 없으면 저장소 루트 .env — 값은 찍지 않음)이 handoff/13차_산출물·dart_out/risk13·
    scripts/dart/*13* 의 파일에 없음(값이 없으면 그 검사는 건너뜀이라고 적음). 가리지 않은 「OC=」·「crtfc_key=」 꼴도 봄.
 ③ handoff/13차_산출물 에 PDF·HWP·HWPX 없음(확장자와 파일 머리 바이트).
 ④ 9~11차 산출물(handoff/원문_10차 등 9~11차 폴더·파일)이 커밋 2688274 와 같음(git diff --quiet + 추적 안 된 파일 없음).
 ⑤ 00_목록.md 1절 파일 목록 = 폴더 실제 파일. 2절(2-1·2-3 손 정리 표의 조 번호·R2 표지·9-4-1 상태, 2-2·2-4 생성 표)·3절·00_종합표.csv 의
    조 번호·상태가 각 md·상태 CSV 와 같음(생성 칸은 build 결과와 한 글자도 같아야 하고, 따로 다시 읽어 맞대기도 함).
 ⑥ 00_목록.md·00_종합표.csv 의 원문 인용(「」 안 글, 코드 블록·> 줄)이 13차 md 에 글자 그대로(공백 무시) 있음.
웹 요청 없음. API 키·OC 값은 화면·파일에 찍지 않는다.
"""
from __future__ import annotations

import collections
import csv
import glob
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

OUT = 'handoff/13차_산출물'
WORK = 'dart_out/risk13'
LIST_MD = OUT + '/00_목록.md'
SUM_CSV = OUT + '/00_종합표.csv'
RESULT = WORK + '/verify13.txt'
ART_CSV = WORK + '/모범규준_조목록.csv'
STATE_CSVS = [WORK + '/9-4_지시서항목_상태_A.csv', WORK + '/9-4_지시서항목_상태_B.csv']
BASE911 = '2688274'
PATHS911 = ['handoff/원문_10차', 'handoff/법령원문_10차', 'handoff/법령원문_저용량', 'handoff/원문_11차', 'handoff/법령원문_11차',
            'handoff/법령원문_9차', 'handoff/원문_지주리스크체계_원문', 'handoff/RAAS_매뉴얼_원문.md', 'handoff/법령해석_원문',
            'handoff/원문텍스트_9차', 'handoff/생보협회_자율규제_원문', 'handoff/9차_보고.md', 'handoff/원문_위험관리위원회_활동.csv',
            'handoff/원문_지주조직_CRO.csv', 'handoff/원문_지주내부회계.csv', 'handoff/원문_비은행지주_자본지표.csv',
            'handoff/원문_보험자회사_지주연계.csv', 'handoff/목록_생보협회_자율규제.csv', 'handoff/목록_법령해석.csv',
            'handoff/원문_외국계보험사_대주주거래.csv']
ISO_FORCE = {'verify13_raas', 'verify13_law91', 'verify13_law92'}
CSV_COLS = ['작업', '지시서_항목', '구분', '내용', '출처', '수집일', '모범규준_조', '조_제목', '판단여부', '파일', '위치']
INDEX_ITEM = '3절 조 번호별 색인'

# md 파일: (작업, 짧은 이름, 파일 규칙상 조 대응 모두 판단, 회사 이름(상태 CSV))
MD = collections.OrderedDict([
    ('9-1_법령원문.md', ('9-1', '9-1', True, None)),
    ('9-2-1_2_ORSA_연혁.md', ('9-2-1·9-2-2', '9-2-1_2', True, None)),
    ('9-2-3_5_별표37_별표22.md', ('9-2-3·9-2-5', '9-2-3_5', True, None)),
    ('9-2-4_ORSA_보도자료.md', ('9-2-4', '9-2-4', True, None)),
    ('9-3_RAAS.md', ('9-3', '9-3', True, None)),
    ('9-4_메리츠금융지주.md', ('9-4', '메리츠', False, '메리츠금융지주')),
    ('9-4_한국투자금융지주.md', ('9-4', '한국투자', False, '한국투자금융지주')),
    ('9-4_KB금융지주.md', ('9-4', 'KB', False, 'KB금융지주')),
    ('9-4_신한금융지주.md', ('9-4', '신한', False, '신한금융지주')),
    ('9-4_하나금융지주.md', ('9-4', '하나', False, '하나금융지주')),
    ('9-4_우리금융지주.md', ('9-4', '우리', False, '우리금융지주')),
    ('9-4_iM금융지주.md', ('9-4', 'iM', False, 'iM금융지주')),
    ('9-4_NH농협금융지주.md', ('9-4', 'NH', False, 'NH농협금융지주')),
    ('9-4_모범규준_원문.md', ('9-4(기준)', '모범원문', False, None)),
    ('9-4_모범규준_대조표.md', ('9-4-1', '대조표', False, None)),
    ('9-5_금감원_검사결과.md', ('9-5', '9-5', True, None)),
])
COMPANY_MD = {v[3]: k for k, v in MD.items() if v[3]}
GROUP_A = ['메리츠금융지주', '한국투자금융지주', 'iM금융지주', 'NH농협금융지주']
COMPANIES = ['메리츠금융지주', '한국투자금융지주', 'KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'iM금융지주', 'NH농협금융지주']
JISI = {3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55}
JISI_EXTRA = {'메리츠': {9, 57}, 'iM': {28, 30}, '대조표': {9, 57, 28, 30}, '모범원문': {9, 57, 28, 30}}
ITEM_TEXT = {  # 지시서(REQUEST13) 9-4 2.·3. 원문 — 회사 md 지시서 항목 대조 표 「지시서 원문」 칸과 같은 글
    '21·22·24': '21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부',
    '27': '27조 전략·평판위험: 관리 체제, 측정이나 평가 수단',
    '34': '34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고',
    '3': '3조: 위험이 경미한 자회사를 적용에서 빼는 기준',
    '17': '17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)',
    '55': '55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)',
    '53': '53조 위기대응조직: 구성과 전환 요건',
    '4·5': '위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구',
}
ORDER_942 = [('3', [3]), ('17', [17]), ('21·22·24', [21, 22, 24]), ('27', [27]), ('34', [34]), ('53', [53]), ('55', [55]),
             ('4·5', [4, 5])]


def norm(s):
    return re.sub(r'[\s·ㆍ∙・‧•･]', '', s)


def nows(s):
    return re.sub(r'\s+', '', s)


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def lines_of(path):
    return read(path).split('\n')


def code_mask(L):
    mask, inc = [], False
    for l in L:
        if l.startswith('```'):
            mask.append(True)
            inc = not inc
            continue
        mask.append(inc)
    return mask


def load_articles():
    arts = {}
    with open(ART_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            arts[int(r['조'])] = (r['제목_2016.8.1판'], r['제목_2012.3.13제정판'], r['제목_2016.7개정예고안'])
    return arts


ARTS = load_articles()


def title_ok(n, title):
    if n not in ARTS:
        return False
    t = norm(title)
    return any(c and t.startswith(norm(c)) for c in ARTS[n])


def paren_end(s, i):
    """s[i] == '(' — 짝 괄호 다음 위치."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '(':
            depth += 1
        elif s[j] == ')':
            depth -= 1
            if depth == 0:
                return j + 1
    return len(s)


def load_states():
    rows = []
    for p in STATE_CSVS:
        with open(p, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                r['_csv'] = p
                rows.append(r)
    return rows


# ───────────────────────── 조 태그 줄 모으기(3절) ─────────────────────────
TAG_A = re.compile(r'^\s*(?:-\s*)?(?:note:\s*)?(?:이 글이 닿는 )?모범규준 (?:조(?=\s*[(:：])|대응\s)')
TAG_B = re.compile(r'\]\s*—\s*모범규준 조\s*[:：]')
TAG_HEAD_B = re.compile(r'—\s*모범규준 조\s*[:：]')
TAG_C = re.compile(r'· 모범규준 ([\d·~]+)조((?:\(제5장\) 주제)?)\(판단\)')
SRC_RE = re.compile(r'^\s*(?:-\s*)?(?:인용 출처:|인용:|인용\([^)]*\):)?\s*\[|^\s*인용 —')
RANGE_RE = re.compile(r'(?<![\d\-.])제?(\d{1,2})조?(?:\([^()]*(?:\([^()]*\)[^()]*)*\))?\s*[~∼]\s*제?(\d{1,2})조')
ART_RE = re.compile(r'(?<![\d\-.~∼])제?(\d{1,2})조\(')
DATE_RE = re.compile(r'(?<!원본 )(?<!PDF )(옮김|인용|수집)\s*(?:시각\s*)?(\d{4}-\d{2}-\d{2}(?:~\d{2})?(?:\([^()]*\))?(?:T\d{2}:\d{2}:\d{2}[+\-]\d{2}:?\d{2})?)')
ORIG_RE = re.compile(r'원본(?: PDF)? 수집\s*(\d{4}-\d{2}-\d{2}(?:T[\d:]+(?:[+\-]\d{2}:?\d{2})?)?)')


def jisi_set(short):
    return JISI | JISI_EXTRA.get(short, set())


def headings_of(L, mask):
    hs = []
    for i, l in enumerate(L):
        if not mask[i] and re.match(r'^#{1,6} ', l):
            hs.append((i, len(re.match(r'^(#+)', l).group(1)), l))
    return hs


def sec_id(fname, L, hs, k, doc95):
    i, lvl, h = hs[k]
    t = re.sub(r'^#+\s*', '', h)
    m = (re.match(r'^\[([A-Z]{1,2}-[A-Z]?\d+[a-z]?)\]', t) or re.match(r'^([A-Z]{1,2}-\d+[a-z]?)\s', t)
         or re.match(r'^([A-Z](?:-\d+)+(?:·\d+)?)\s', t))
    if m:
        return m.group(1)
    if fname.startswith('9-5'):
        m = re.match(r'^\[(\d+)\]', t)
        if m and doc95:
            return '%s [%s]' % (doc95, m.group(1))
        m = re.match(r'^(.+?) — 제재조치요구일 (\d{8})', t)
        if m:
            return '%s %s 문서 머리' % (m.group(1).replace('금융지주', ''), m.group(2)[2:])
    m = re.match(r'^(Q\d+)\s', t)
    if m:
        return m.group(1)
    m = re.match(r'^(\d+(?:-\d+)*(?:-참고)?)\.?\s', t)
    if m:
        num = m.group(1)
        return num + ('절' if '-' not in num else '')
    if t.startswith('제') or t.startswith('부칙'):
        # 위 번호 머리 아래의 조문 절(9-1 2절 제8조 등)
        for j in range(k - 1, -1, -1):
            if hs[j][1] < lvl:
                pid = sec_id(fname, L, hs, j, doc95)
                return '%s %s' % (pid, '부칙' if t.startswith('부칙') else re.sub(r'\).*$', ')', t)[:30])
        return t[:30]
    if t.startswith('검증 기록') or t.startswith('대조 기록'):
        return '검증 기록'
    return t[:24]


def find_src(L, mask, s, e, t):
    """태그 줄 t 의 출처 줄 — 아래로(첫 코드 블록 앞까지), 없으면 위로(절 머리까지)."""
    for j in range(t, e):
        if mask[j]:
            break
        if SRC_RE.match(L[j]) or TAG_B.search(L[j]):
            return L[j]
    for j in range(t - 1, s, -1):
        if not mask[j] and (SRC_RE.match(L[j]) or TAG_B.search(L[j])):
            return L[j]
    return ''


def clean_src(line):
    s = line.strip()
    s = re.sub(r'\s*—\s*모범규준 조\s*[:：].*$', '', s)
    if '[' in s:
        a = s.index('[')
        b = s.rfind(']')
        s = s[a + 1:b] if b > a else s[a + 1:]
    else:
        s = re.sub(r'^\s*인용 —\s*', '', s)
    return s.strip()


def src_date(src, fallback):
    ds = []
    for m in DATE_RE.finditer(src):
        d = re.sub(r'\((KST|UTC)[;,][^)]*\)', r'(\1)', m.group(2))
        d = re.sub(r'\((?!KST|UTC)[^)]*\)$', '', d)
        ds.append(d)
    o = ORIG_RE.search(src)
    out = ds[0] if ds else ''
    if o:
        out = (out + ' · ' if out else '') + '원본 수집 ' + o.group(1)
    return out or fallback


def parse_seg(rest, kw_judged, alljudged):
    """태그 글(키워드 뒤) → [(kind, value, title, judged)] kind: art|range|label."""
    out = []
    for seg in re.split(r'\s+[;；]\s+', rest):
        sj = seg.strip().startswith('(판단)')
        st = seg.strip()
        if st.startswith('전체'):
            j = st.find('(')
            lab = st[:paren_end(st, j)] if j >= 0 else '전체'
            out.append(('label', lab, '', False))
            continue
        m = re.search(r'9-4 조문 대조\(대조표 [^)]*\)', seg)
        if m:
            out.append(('label', m.group(0), '', False))
        m = re.search(r'조 번호 해당 없음', seg)
        if m:
            k = m.end()
            lab = '조 번호 해당 없음'
            if k < len(seg) and seg[k] == '(':
                lab = seg[m.start():paren_end(seg, k)]
            out.append(('label', lab, '', 'judged' if '판단' in lab else False))
        work = seg
        for m in RANGE_RE.finditer(seg):
            a, b = int(m.group(1)), int(m.group(2))
            if 1 <= a < b <= 59:
                j = alljudged or kw_judged or sj or ('(판단' in seg[m.end():])
                out.append(('range', (a, b), '', j))
                work = work[:m.start()] + ' ' * (m.end() - m.start()) + work[m.end():]
        for m in ART_RE.finditer(work):
            n = int(m.group(1))
            p = m.end() - 1
            q = paren_end(work, p)
            title = work[p + 1:q - 1]
            if not title_ok(n, title):
                continue
            after = work[q:q + 12]
            after2 = re.sub(r'^[①-⑳]+(?:\d+호)?', '', after)
            j = alljudged or kw_judged or sj or after2.startswith('(판단')
            out.append(('art', n, ARTS[n][0], j))
    return out


def extract_index():
    """각 md 의 조 태그 줄 → 항목 목록."""
    file_dates = parse_part1_dates()
    entries = []
    for fname, (task, short, alljudged, comp) in MD.items():
        path = OUT + '/' + fname
        L = lines_of(path)
        mask = code_mask(L)
        hs = headings_of(L, mask)
        top_verif = [False] * len(L)
        cur = False
        for i, l in enumerate(L):
            if not mask[i] and l.startswith('## '):
                cur = ('검증 기록' in l) or ('대조 기록' in l)
            top_verif[i] = cur
        doc95 = ''
        hk = -1
        sec_has_code = {}
        for k, (i, lvl, h) in enumerate(hs):
            e = hs[k + 1][0] if k + 1 < len(hs) else len(L)
            sec_has_code[k] = any(mask[j] for j in range(i, e))
        seen_sec = collections.Counter()
        tagged = []
        for i, l in enumerate(L):
            if mask[i]:
                continue
            while hk + 1 < len(hs) and hs[hk + 1][0] <= i:
                hk += 1
                hh = hs[hk][2]
                if fname.startswith('9-5'):
                    m = re.match(r'^### (.+?) — 제재조치요구일 (\d{8})', hh)
                    if m:
                        doc95 = '%s %s' % (m.group(1).replace('금융지주', ''), m.group(2)[2:])
                    elif hh.startswith('## '):
                        doc95 = ''
            if l.startswith('|') or l.startswith('>'):
                continue
            kind = None
            if l.startswith('#'):
                m = TAG_C.search(l)
                if m and fname.startswith('9-5'):
                    kind = 'C'
                elif TAG_HEAD_B.search(l):
                    kind = 'B'
            elif TAG_B.search(l):
                kind = 'B'
            elif TAG_A.match(l):
                kind = 'A'
            if not kind:
                continue
            if hk < 0:
                continue
            if top_verif[i] and not sec_has_code.get(hk, False):
                continue
            tagged.append((i, kind, hk, doc95))
        for i, kind, hk, d95 in tagged:
            l = L[i]
            s0 = hs[hk][0]
            e0 = hs[hk + 1][0] if hk + 1 < len(hs) else len(L)
            parts = []
            if kind == 'C':
                m = TAG_C.search(l)
                for piece in m.group(1).split('·'):
                    if '~' in piece:
                        a, b = piece.split('~')
                        parts.append(('range', (int(a), int(b)), m.group(2), True))
                    elif piece:
                        n = int(piece)
                        parts.append(('art', n, ARTS[n][0], True))
                src = find_src(L, mask, s0, e0, i + 1)
            else:
                if kind == 'B':
                    mm = TAG_HEAD_B.search(l)
                    rest = l[mm.end():]
                    kwj = False
                    src = l if not l.startswith('#') else find_src(L, mask, s0, e0, i + 1)
                else:
                    mm = re.search(r'모범규준 (?:조|대응)', l)
                    rest = l[mm.end():]
                    kwj = False
                    if rest.startswith('('):
                        q = paren_end(rest, 0)
                        kwj = '판단' in rest[:q]
                        rest = rest[q:]
                    rest = rest.lstrip(' :：')
                    src = find_src(L, mask, s0, e0, i + 1)
                parts = parse_seg(rest, kwj, alljudged)
            sid = sec_id(fname, L, hs, hk, d95 if fname.startswith('9-5') else '')
            seen_sec[sid] += 1
            fallback = file_dates.get(fname, ('', ''))[1]
            src_c = clean_src(src) if src else ''
            date = src_date(src_c, fallback)
            heading = re.sub(r'^#+\s*', '', hs[hk][2]).strip()
            for kind2, val, title, j in parts:
                entries.append(dict(file=fname, task=task, short=short, alljudged=alljudged, sec=sid, line=i + 1,
                                    heading=heading, kind=kind2, val=val, title=title, judged=bool(j),
                                    src=src_c or file_dates.get(fname, ('', ''))[0], date=date))
        # 같은 절에 태그 줄이 여럿이면 묶음 이름에 줄 번호를 붙임
        multi = {s for s, c in seen_sec.items() if c > 1}
        for en in entries:
            if en['file'] == fname and en['sec'] in multi:
                en['sec_disp'] = '%s 줄 %d' % (en['sec'], en['line'])
            elif en['file'] == fname:
                en['sec_disp'] = en['sec']
    for en in entries:
        en['jlabel'] = judge_label(en)
    return entries


MOBEOM_SRC = re.compile(r'^(?:금감원 행정지도|「금융지주회사 통합(?:위험|리스크)관리 모범규준」)')


def judge_label(en):
    if en['kind'] == 'label':
        v = en['val']
        if v.startswith('9-4 조문 대조'):
            return '9-4 조문 대조'
        if v.startswith('조 번호 해당 없음'):
            return '조 번호 해당 없음'
        return '모범규준 원문(전체)'
    if en['judged']:
        return '판단'
    if MOBEOM_SRC.match(en['src'] or ''):
        return '모범규준 원문(그 조 글)'
    if en['kind'] == 'art' and en['val'] in jisi_set(en['short']):
        return '지시서 조'
    return '판단 표시 없음'


# ───────────────────────── 00_목록.md 읽기 ─────────────────────────
def table_cells(l):
    body = l.strip()
    if body.startswith('|'):
        body = body[1:]
    if body.endswith('|') and not body.endswith('\\|'):
        body = body[:-1]
    return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', body)]


def md_tables(L, start_pat, stop_pat=r'^#{2,3} '):
    """start_pat 머리 아래 첫 표의 행(머리·구분 줄 뺀 칸 목록)."""
    rows, on, intable = [], False, False
    for i, l in enumerate(L):
        if re.match(start_pat, l):
            on = True
            continue
        if on and re.match(stop_pat, l) and not re.match(start_pat, l):
            break
        if on and l.startswith('|'):
            cells = table_cells(l)
            if not intable:
                intable = True
                continue
            if set(''.join(cells)) <= set('-: '):
                continue
            rows.append((i + 1, cells))
        elif on and intable and not l.startswith('|'):
            if rows:
                break
    return rows


def parse_part1_dates():
    """1절 표: 파일 → (출처, 수집일)."""
    if not os.path.exists(LIST_MD):
        return {}
    L = lines_of(LIST_MD)
    out = {}
    for _, c in md_tables(L, r'^## 1\. '):
        m = re.search(r'`([^`]+)`', c[0])
        if m and len(c) >= 4:
            out[m.group(1)] = (c[2], c[3])
    return out


def hand_rows():
    L = lines_of(LIST_MD)
    rows = []
    for pat in (r'^### 2-1 ', r'^### 2-3 '):
        for ln, c in md_tables(L, pat):
            rows.append(dict(line=ln, cells=c))
    return rows


def split_tokens(cell):
    return [t.strip() for t in cell.split(' · ') if t.strip()]


TOK_ART = re.compile(r'^(\d{1,2})조\(([^()]*)\)(\(판단\))?$')
TOK_RANGE = re.compile(r'^(\d{1,2})~(\d{1,2})조(?:\(.*\))?$')


def token_info(tok):
    m = TOK_ART.match(tok)
    if m:
        return ('art', int(m.group(1)), m.group(2), bool(m.group(3)))
    m = TOK_RANGE.match(tok)
    if m:
        return ('range', (int(m.group(1)), int(m.group(2))), '', '(판단)' in tok)
    return ('label', tok, '', '판단' in tok)


def files_in(cell):
    fs = re.findall(r'`([^`]+\.md)`', cell)
    return [f for f in fs if f in MD]


def items_of(cell):
    return [x.strip() for x in cell.split('<br>') if x.strip() and x.strip() not in ('—', '-')]


# ───────────────────────── 생성: 2-2·2-4·3절·4절 ─────────────────────────
def esc(s):
    return s.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def ids_of(geo):
    ids = []
    for m in re.finditer(r'\[?([A-Z]{1,2}-[A-Z]?\d+[a-z]?)\]?(?:\(|\s)(?:handoff/13차_산출물/)?(?:9-4_[^:\s]+\.md:(\d+))?', geo):
        ids.append(m.group(1) + ('(md %s줄)' % m.group(2) if m.group(2) else ''))
    seen, out = set(), []
    for x in ids:
        k = x.split('(')[0]
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def company_diffs():
    """회사 md 의 「원문과 다른 것」 — A 그룹 5장 표(조 칸), B 그룹 6장 표(지시서 항목 행) → {(회사, 조): [글]}."""
    out = collections.defaultdict(list)
    for comp in COMPANIES:
        f = COMPANY_MD[comp]
        L = lines_of(OUT + '/' + f)
        short = MD[f][1]
        if comp in GROUP_A:
            for _, c in md_tables(L, r'^## 5\. 받은 것'):
                if len(c) >= 4 and c[0].startswith('원문과 다른 것'):
                    cell = re.sub(r'9-4 조문 대조\(대조표 [^)]*\)', ' ', c[3])
                    nums = {int(x) for x in re.findall(r'(?<![\d\-.~])(\d{1,2})(?![\d\-.])', cell)}
                    for n in nums:
                        out[(comp, n)].append('%s: %s(%s)' % (short, c[1], c[2]))
        else:
            for _, c in md_tables(L, r'^## 6\. 지시서 항목별 대조'):
                if len(c) >= 7 and c[6] not in ('-', '—', ''):
                    lab = c[0]
                    m = re.match(r'^9-4-([23]) (.+)$', lab) or re.match(r'^9-4-(3)$', lab)
                    if not m:
                        continue
                    key = '4·5' if lab == '9-4-3' else m.group(2)
                    for k, ns in ORDER_942:
                        if k == key:
                            for n in ns:
                                out[(comp, n)].append('%s: %s' % (short, c[6]))
    return out


def gen_22(states):
    by = collections.defaultdict(dict)
    for r in states:
        by[int(r['모범규준_조'])][r['회사']] = r
    diffs = company_diffs()
    lines = ['| 작업 | 지시서 항목 | 받은 것 | 받지 못한 것(추출 범위에 없음 — 찾은 방법은 상태 CSV ‘찾은_방법’ 열) | 원문과 다른 것을 발견한 곳(회사 md 5장·6장) | 모범규준 조 번호 | 위치 |',
             '|---|---|---|---|---|---|---|']
    for key, ns in ORDER_942:
        task = '9-4-3' if key == '4·5' else '9-4-2'
        for n in ns:
            rs = by[n]
            got = collections.OrderedDict([('받은 글', []), ('일부', []), ('추출 범위에 없음', [])])
            miss = []
            for comp in COMPANIES:
                r = rs[comp]
                st = r['상태']
                cat = '받은 글' if st == '받은 글' else ('추출 범위에 없음' if st.startswith('추출 범위에 없음') else '일부')
                got[cat].append(MD[COMPANY_MD[comp]][1])
                if r['빠진_핵심'].strip() not in ('-', ''):
                    miss.append('%s: %s' % (MD[COMPANY_MD[comp]][1], r['빠진_핵심'].strip()))
            got_txt = '<br>'.join('%s — %s' % (k, '·'.join(v)) for k, v in got.items() if v)
            got_txt += '<br>(회사별 상태 글·있는 핵심·근거 인용은 2-4)'
            dl = []
            for comp in COMPANIES:
                for d in diffs.get((comp, n), []):
                    if d not in dl:
                        dl.append(d)
            row = [task, ITEM_TEXT[key], got_txt, '<br>'.join(miss) or '—', '<br>'.join(dl) or '—',
                   '%d조(%s)' % (n, ARTS[n][0]),
                   '`dart_out/risk13/9-4_지시서항목_상태_A.csv` · `dart_out/risk13/9-4_지시서항목_상태_B.csv` · 회사 md 0장·3장 · 7장(메리츠·한국투자·iM·NH)/6장(KB·신한·하나·우리)']
            lines.append('| ' + ' | '.join(esc(x) for x in row) + ' |')
    return '\n'.join(lines)


def gen_24(states):
    lines = ['| 작업 | 조 | 회사 | 상태(상태 CSV 그대로) | 있는 핵심 | 빠진 핵심(추출 범위에 없음) | 근거 인용(md 줄) | 위치 |',
             '|---|---|---|---|---|---|---|---|']
    order = {c: i for i, c in enumerate(COMPANIES)}
    keyorder = {n: i for i, (k, ns) in enumerate(ORDER_942) for n in ns}
    for r in sorted(states, key=lambda r: (keyorder[int(r['모범규준_조'])], int(r['모범규준_조']), order[r['회사']])):
        n = int(r['모범규준_조'])
        task = '9-4-3' if n in (4, 5) else '9-4-2'
        f = COMPANY_MD[r['회사']]
        row = [task, '%d조(%s)' % (n, ARTS[n][0]), r['회사'], r['상태'], r['있는_핵심'].strip() or '-', r['빠진_핵심'].strip() or '-',
               ', '.join(ids_of(r['근거'])) or '-', '`%s` 0장·3장 %d조 · `%s`' % (f, n, os.path.basename(r['_csv']))]
        lines.append('| ' + ' | '.join(esc(x) for x in row) + ' |')
    return '\n'.join(lines)


def orig_lines():
    L = lines_of(OUT + '/9-4_모범규준_원문.md')
    s5 = next(i for i, l in enumerate(L) if l.startswith('## 5.'))
    s6 = next(i for i, l in enumerate(L) if l.startswith('## 6.'))
    s7 = next(i for i, l in enumerate(L) if l.startswith('## 7.'))
    out = {}
    for i in range(s5, s7):
        m = re.match(r'^제(\d{1,2})조\(', L[i])
        if m:
            n = int(m.group(1))
            key = 5 if i < s6 else 6
            out.setdefault((n, key), i + 1)
    return out


def d_rows():
    L = lines_of(OUT + '/9-4_모범규준_대조표.md')
    out = {}
    for _, c in md_tables(L, r'^## D\. '):
        if c and c[0].isdigit():
            cats = collections.Counter()
            for cell in c[3:11]:
                for k in ('받은 글', '일부', '추출 범위에 없음', '(판단)', '9-4 검색 범위 밖'):
                    if cell.startswith(k):
                        cats[k] += 1
                        break
                else:
                    cats['기타'] += 1
            out[int(c[0])] = (c[2], cats)
    return out


def art_scope(n):
    if n in (3, 17, 21, 22, 24, 27, 34, 53, 55):
        return '지시서 조(9-4-2)'
    if n in (4, 5):
        return '지시서 조(9-4-3)'
    if n in (28, 30):
        return '지시서 조(9-4-1 iM)'
    if n in (9, 57):
        return '지시서 조(9-4-1 메리츠)'
    return '지시서에 없는 조'


def fmt_ids(ens):
    by = collections.OrderedDict()
    for en in ens:
        by.setdefault(en['short'], [])
        mark = {'판단': '(판단)', '판단 표시 없음': '(판단 표시 없음)', '모범규준 원문(그 조 글)': '(모범규준 원문)'}.get(en['jlabel'], '')
        x = en['sec_disp'] + mark
        if x not in by[en['short']]:
            by[en['short']].append(x)
    return '<br>'.join('**%s**: %s' % (k, ', '.join(v)) for k, v in by.items())


def gen_3(entries):
    ol = orig_lines()
    dr = d_rows()
    arts = collections.defaultdict(list)
    ranges = collections.defaultdict(list)
    labels = collections.defaultdict(list)
    for en in entries:
        if en['kind'] == 'art':
            arts[en['val']].append(en)
        elif en['kind'] == 'range':
            key = '%d~%d조' % en['val'] + (en['title'] if en['title'] else '')
            ranges[key].append(en)
        else:
            labels[en['val']].append(en)
    out = []
    out.append('### 3-1 모범규준 3~58조')
    out.append('')
    out.append('| 조 | 조 제목(2016.8.1판) | 자료(파일 · 절/인용 번호) | 판단 여부 |')
    out.append('|---|---|---|---|')

    def art_row(n):
        ens = arts.get(n, [])
        parts = []
        a5, a6 = ol.get((n, 5)), ol.get((n, 6))
        parts.append('모범규준 원문: `9-4_모범규준_원문.md` 5장 md %s줄(2016.8.1판) · 6장 md %s줄(2012.3.13판)' % (a5 or '-', a6 or '-'))
        if n in dr:
            y, cats = dr[n]
            parts.append('대조표 D %d조 행(9-4 조사 %s — %s)' % (n, y, ' · '.join('%s %d' % (k, v) for k, v in cats.items())))
        body = fmt_ids(ens)
        if body:
            parts.append(body)
        else:
            parts.append('(md 조 태그 줄에서 이 조를 가리킨 자료는 찾지 못함 — 2절 표의 조 칸·대조표 D 행 참조)')
        c = collections.Counter(en['jlabel'] for en in ens)
        jl = '%s — 판단 %d · 지시서 조 %d · 모범규준 원문 %d · 판단 표시 없음 %d' % (
            art_scope(n), c['판단'], c['지시서 조'], c['모범규준 원문(그 조 글)'], c['판단 표시 없음'])
        return '| %d | %s | %s | %s |' % (n, esc(ARTS[n][0]), esc('<br>'.join(parts)), esc(jl))

    for n in range(3, 59):
        out.append(art_row(n))
    out.append('')
    out.append('### 3-2 범위로 붙인 자료(N~M조 — md 표기 그대로, 범위 안 조 행 모두에 닿음)')
    out.append('')
    out.append('| 범위 | 자료(파일 · 절/인용 번호) | 판단 여부 |')
    out.append('|---|---|---|')
    for key in sorted(ranges, key=lambda k: tuple(int(x) for x in re.match(r'(\d+)~(\d+)', k).groups())):
        ens = ranges[key]
        c = collections.Counter(en['jlabel'] for en in ens)
        out.append('| %s | %s | %s |' % (esc(key), esc(fmt_ids(ens)), esc(' · '.join('%s %d' % kv for kv in c.items()))))
    out.append('')
    out.append('### 3-3 3~58조 밖 — 1조·2조·59조(주제1 표 범위 밖)')
    out.append('')
    out.append('| 조 | 조 제목(2016.8.1판) | 자료(파일 · 절/인용 번호) | 판단 여부 |')
    out.append('|---|---|---|---|')
    for n in (1, 2, 59):
        out.append(art_row(n))
    out.append('')
    out.append('### 3-4 9-4 조문 대조(대조표 A~C) 묶음 · 모범규준 원문 전체 묶음')
    out.append('')
    out.append('| 표지(md 표기) | 자료(파일 · 절/인용 번호) |')
    out.append('|---|---|')
    for key in sorted(k for k in labels if not k.startswith('조 번호 해당 없음')):
        out.append('| %s | %s |' % (esc(key), esc(fmt_ids(labels[key]))))
    out.append('')
    out.append('### 3-5 조 번호 해당 없음 묶음')
    out.append('')
    out.append('| 표지(md 표기) | 자료(파일 · 절/인용 번호) |')
    out.append('|---|---|')
    for key in sorted(k for k in labels if k.startswith('조 번호 해당 없음')):
        out.append('| %s | %s |' % (esc(key), esc(fmt_ids(labels[key]))))
    c = collections.Counter(en['jlabel'] for en in entries)
    out.append('')
    out.append('note: 모은 조 태그 %d개(자료 묶음 %d개, md %d개) — %s. 판단 여부는 md 표기 그대로(‘판단 표시 없음’이 있으면 md 의 R2 표기를 다시 볼 곳).' % (
        len(entries), len({(e['file'], e['line']) for e in entries}), len({e['file'] for e in entries}),
        ' · '.join('%s %d' % kv for kv in sorted(c.items()))))
    return '\n'.join(out)


def shorten(s, n):
    if len(s) <= n:
        return s
    t = s[:n]
    if t.count('「') > t.count('」'):
        t = t[:t.rfind('「')]
    if t.count('(') > t.count(')'):
        t = t[:t.rfind('(')]
    return t.rstrip(' ,·') + '…'


def gen_41(hrows, states):
    out = []
    for r in hrows:
        c = r['cells']
        its = items_of(c[3])
        if not its:
            continue
        for it in its:
            if it.startswith('해당 없음'):
                continue
            out.append('- **%s** %s — %s' % (c[0], esc(shorten(c[1], 60)), it))
    by = collections.defaultdict(list)
    for r in states:
        if r['빠진_핵심'].strip() not in ('-', ''):
            by[r['회사']].append('%s조 %s' % (r['모범규준_조'], r['빠진_핵심'].strip()))
    for comp in COMPANIES:
        if by.get(comp):
            out.append('- **9-4-2·9-4-3** %s(상태 CSV 빠진 핵심 — 추출 범위에 없음, 찾은 방법은 ‘찾은_방법’ 열): %s' % (
                comp, ' / '.join(sorted(by[comp], key=lambda x: int(x.split('조')[0])))))
    return '\n'.join(out)


def gen_42(hrows, gen22_rows):
    out = []
    for c in [r['cells'] for r in hrows] + gen22_rows:
        for it in items_of(c[4]):
            if re.search(r'지시서|사용자 표|사용자 메모', it):
                out.append('- **%s** %s — %s' % (c[0], esc(shorten(c[1], 40)), it))
    return '\n'.join(dict.fromkeys(out))


def replace_block(text, name, body):
    pat = re.compile(r'(<!-- build13:begin:%s -->\n)(.*?)(<!-- build13:end:%s -->)' % (re.escape(name), re.escape(name)), re.S)
    if not pat.search(text):
        raise SystemExit('표지 없음: %s' % name)
    return pat.sub(lambda m: m.group(1) + body + '\n' + m.group(3), text, count=1)


def built_md(entries, states):
    text = read(LIST_MD)
    text = replace_block(text, '2-2', gen_22(states))
    text = replace_block(text, '2-4', gen_24(states))
    text = replace_block(text, '3', gen_3(entries))
    hrows = hand_rows()
    g22 = [table_cells(l) for l in gen_22(states).split('\n')[2:]]
    text = replace_block(text, '4-1', gen_41(hrows, states))
    text = replace_block(text, '4-2', gen_42(hrows, g22))
    return text


# ───────────────────────── 생성: 00_종합표.csv ─────────────────────────
def built_csv(entries, states, md_text):
    p1 = parse_part1_dates()
    rows = []
    L = md_text.split('\n')

    def tok_rows(base, cell):
        for tok in split_tokens(cell):
            kind, val, title, judged = token_info(tok)
            if kind == 'art':
                yield str(val), ARTS[val][0], ('판단' if judged else '지시서 조')
            elif kind == 'range':
                yield '%d~%d' % val, '%s~%s' % (ARTS[val[0]][0], ARTS[val[1]][0]), ('판단' if judged else '모범규준 원문(조 번호 그대로)')
            else:
                yield tok, '', ('9-4 조문 대조' if tok.startswith('9-4 조문 대조') else
                                ('조 번호 해당 없음' if tok.startswith('조 번호 해당 없음') else '판단' if judged else ''))

    by_short = {v[1]: k for k, v in MD.items() if v[3]}

    def add_hand(c, which=('받은 것', '받지 못한 것', '원문과 다른 것')):
        fs0 = files_in(c[6])
        for col, gub in ((2, '받은 것'), (3, '받지 못한 것'), (4, '원문과 다른 것')):
            if gub not in which:
                continue
            for it in items_of(c[col]):
                fs = fs0
                mm = re.match(r'^(\S+): ', it)
                if not fs and mm and mm.group(1) in by_short:
                    fs = [by_short[mm.group(1)]]
                src, date = p1.get(fs[0], ('', '')) if fs else ('', '')
                for jo, title, jl in tok_rows(None, c[5]):
                    rows.append([c[0], c[1], gub, it, src, date, jo, title, jl, ' · '.join(OUT + '/' + f for f in fs), c[6]])

    for pat in (r'^### 2-1 ', r'^### 2-2 ', r'^### 2-3 '):
        for _, c in md_tables(L, pat):
            if len(c) != 7:
                continue
            add_hand(c, ('원문과 다른 것',) if pat == r'^### 2-2 ' else ('받은 것', '받지 못한 것', '원문과 다른 것'))
    keyorder = {n: i for i, (k, ns) in enumerate(ORDER_942) for n in ns}
    order = {c: i for i, c in enumerate(COMPANIES)}
    for r in sorted(states, key=lambda r: (keyorder[int(r['모범규준_조'])], int(r['모범규준_조']), order[r['회사']])):
        n = int(r['모범규준_조'])
        task = '9-4-3' if n in (4, 5) else '9-4-2'
        f = COMPANY_MD[r['회사']]
        key = next(k for k, ns in ORDER_942 if n in ns)
        item = '%s — %s' % (ITEM_TEXT[key], r['회사'])
        date = p1.get(f, ('', ''))[1]
        pos = '%s 0장·3장 %d조 · %s' % (f, n, os.path.basename(r['_csv']))
        got = '상태: %s · 있는 핵심: %s' % (r['상태'], r['있는_핵심'].strip() or '-')
        if r.get('비고', '').strip():
            got += ' · 비고: ' + r['비고'].strip()
        rows.append([task, item, '받은 것', got, r['근거'].strip(), date, str(n), ARTS[n][0], '지시서 조', OUT + '/' + f, pos])
        if r['빠진_핵심'].strip() not in ('-', ''):
            miss = '상태: %s · 빠진 핵심(추출 범위에 없음): %s · 찾은 방법: %s' % (r['상태'], r['빠진_핵심'].strip(), r['찾은_방법'].strip())
            rows.append([task, item, '받지 못한 것', miss, r['근거'].strip(), date, str(n), ARTS[n][0], '지시서 조', OUT + '/' + f, pos])
    for en in entries:
        if en['kind'] == 'art':
            jo, title = str(en['val']), ARTS[en['val']][0]
        elif en['kind'] == 'range':
            jo = '%d~%d' % en['val'] + (en['title'] or '')
            title = '%s~%s' % (ARTS[en['val'][0]][0], ARTS[en['val'][1]][0])
        else:
            jo, title = en['val'], ''
        rows.append([en['task'], '%s — %s' % (INDEX_ITEM, en['short']), '받은 것', en['heading'], en['src'], en['date'], jo, title,
                     en['jlabel'], OUT + '/' + en['file'], '%s · 태그 줄 %d' % (en['sec_disp'], en['line'])])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\r\n')
    w.writerow(CSV_COLS)
    for r in rows:
        w.writerow([x.replace('\r', ' ').replace('\n', ' ') for x in r])
    return '\ufeff' + buf.getvalue()


def build():
    states = load_states()
    entries = extract_index()
    text = built_md(entries, states)
    with open(LIST_MD, 'w', encoding='utf-8') as f:
        f.write(text)
    csvtext = built_csv(entries, states, text)
    with open(SUM_CSV, 'w', encoding='utf-8', newline='') as f:
        f.write(csvtext)
    c = collections.Counter(en['jlabel'] for en in entries)
    print('build: 00_목록.md 생성 칸 5개, 00_종합표.csv %d행, 조 태그 %d개 (%s)' % (
        csvtext.count('\r\n') - 1, len(entries), ' · '.join('%s %d' % kv for kv in sorted(c.items()))))


# ───────────────────────── 대조 ─────────────────────────
class Rep:
    def __init__(self):
        self.lines, self.problems = [], []

    def h(self, s):
        self.lines.append('')
        self.lines.append('## ' + s)

    def ok(self, s):
        self.lines.append('  ' + s)

    def bad(self, s):
        self.problems.append(s)
        self.lines.append('  문제: ' + s)


def check_1(rep):
    rep.h('① 대조 스크립트 exit 코드(verify13_*.py · fix13_*.py check)')
    scripts = sorted(p for p in glob.glob('scripts/dart/verify13_*.py')) + sorted(glob.glob('scripts/dart/fix13_*.py'))
    for p in scripts:
        name = os.path.basename(p)[:-3]
        head = read(p)[:4000]
        iso = name in ISO_FORCE or ('python3 -I scripts/dart/%s.py' % name) in head
        cmd = [sys.executable] + (['-I'] if iso else []) + [p] + (['check'] if name.startswith('fix13_') else [])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            code = r.returncode
            last = ([x for x in (r.stdout + '\n' + r.stderr).strip().split('\n') if x.strip()] or [''])[-1][:160]
        except subprocess.TimeoutExpired:
            code, last = -1, '시간 초과(900초)'
        disp = 'python3 %s%s%s' % ('-I ' if iso else '', p, ' check' if name.startswith('fix13_') else '')
        if code == 0:
            rep.ok('%-52s exit 0 — %s' % (disp, last))
        else:
            rep.bad('%s exit %d — %s' % (disp, code, last))
    rep.ok('스크립트 %d개' % len(scripts))


def secret_values():
    vals = {}
    for k in ('DART_API_KEY', 'LAW_OC'):
        v = os.environ.get(k, '').strip()
        if v:
            vals[k] = (v, '환경변수')
    if os.path.exists('.env'):
        with open('.env', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip().replace('export ', '')
                v = v.strip().strip('"').strip("'")
                if k in ('DART_API_KEY', 'LAW_OC') and v and k not in vals:
                    vals[k] = (v, '.env')
    return vals


def check_2(rep):
    rep.h('② API 키·OC 값 문자열(값은 찍지 않음)')
    targets = []
    for base in (OUT, WORK):
        for dp, dn, fn in os.walk(base):
            targets += [os.path.join(dp, x) for x in fn]
    targets += [p for p in glob.glob('scripts/dart/*13*') if os.path.isfile(p)]
    targets = sorted(set(targets))
    vals = secret_values()
    for k in ('DART_API_KEY', 'LAW_OC'):
        if k not in vals:
            rep.ok('%s: 환경변수·.env 에 값이 없음 — 이 검사는 건너뜀' % k)
    blobs = {}
    for p in targets:
        with open(p, 'rb') as f:
            blobs[p] = f.read()
    for k, (v, where) in vals.items():
        if len(v) < 4:
            rep.ok('%s(%s): 값이 너무 짧아 문자열 검사를 건너뜀' % (k, where))
            continue
        hit = [p for p, b in blobs.items() if v.encode('utf-8') in b]
        if hit:
            for p in hit:
                rep.bad('%s 값이 %s 에 있음' % (k, p))
        else:
            rep.ok('%s(%s 에서 읽음): 파일 %d개에 없음' % (k, where, len(targets)))
    pat = re.compile(rb'[?&]OC=(?!\*{3})[A-Za-z0-9_]{3,}|crtfc_key=(?!\*)[0-9A-Za-z]{10,}')
    n = 0
    for p, b in blobs.items():
        for m in pat.finditer(b):
            n += 1
            rep.bad('가리지 않은 인증값 꼴이 %s 에 있음(자리 %d)' % (p, m.start()))
    if not n:
        rep.ok('가리지 않은 「OC=…」·「crtfc_key=…」 꼴 0곳(파일 %d개)' % len(targets))


def check_3(rep):
    rep.h('③ handoff/13차_산출물 에 PDF·HWP·HWPX 없음')
    bad = 0
    files = sorted(os.listdir(OUT))
    for fn in files:
        p = os.path.join(OUT, fn)
        if os.path.isdir(p):
            continue
        ext = os.path.splitext(fn)[1].lower()
        with open(p, 'rb') as f:
            head = f.read(4096)
        kind = None
        if ext in ('.pdf', '.hwp', '.hwpx'):
            kind = '확장자 ' + ext
        elif head.startswith(b'%PDF'):
            kind = 'PDF 머리 바이트'
        elif head.startswith(b'\xd0\xcf\x11\xe0'):
            kind = 'OLE(HWP 등) 머리 바이트'
        elif head.startswith(b'PK') and (b'hwp' in head.lower()):
            kind = 'HWPX(zip) 머리 바이트'
        if kind:
            bad += 1
            rep.bad('%s — %s' % (p, kind))
    if not bad:
        rep.ok('파일 %d개 — PDF·HWP·HWPX 0개' % len(files))


def check_4(rep):
    rep.h('④ 9~11차 산출물이 커밋 %s 와 같음' % BASE911)
    miss = [p for p in PATHS911 if not os.path.exists(p)]
    for p in miss:
        rep.bad('경로 없음: %s' % p)
    r = subprocess.run(['git', 'diff', '--quiet', BASE911, '--'] + PATHS911, capture_output=True)
    if r.returncode != 0:
        d = subprocess.run(['git', 'diff', '--stat', BASE911, '--'] + PATHS911, capture_output=True, text=True).stdout.strip()
        rep.bad('git diff --quiet %s 가 다름(exit %d): %s' % (BASE911, r.returncode, d[-300:]))
    else:
        rep.ok('git diff --quiet %s -- (경로 %d개) → exit 0' % (BASE911, len(PATHS911)))
    s = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--'] + PATHS911, capture_output=True, text=True).stdout
    if s.strip():
        rep.bad('작업 트리에 바뀌거나 새로 생긴 파일: %s' % s.strip()[:300])
    else:
        rep.ok('git status(추적 안 된 파일 포함) — 바뀐 것 0')


def check_5(rep, states, entries):
    rep.h('⑤ 00_목록.md·00_종합표.csv ↔ 각 md·상태 CSV')
    L = lines_of(LIST_MD)
    # (a) 1절 파일 목록
    listed = []
    for _, c in md_tables(L, r'^## 1\. '):
        m = re.search(r'`([^`]+)`', c[0])
        if m:
            listed.append(m.group(1))
    actual = sorted(fn for fn in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, fn)))
    if sorted(listed) != actual or len(listed) != len(set(listed)):
        rep.bad('1절 파일 목록 ≠ 폴더: 목록에만 %s · 폴더에만 %s' % (sorted(set(listed) - set(actual)), sorted(set(actual) - set(listed))))
    else:
        rep.ok('1절 파일 목록 %d개 = 폴더 실제 파일 %d개' % (len(listed), len(actual)))
    # (b) 생성 칸·CSV = build 결과
    want_md = built_md(entries, states)
    have_md = read(LIST_MD)
    if want_md != have_md:
        rep.bad('00_목록.md 생성 칸이 지금 md·상태 CSV 로 다시 만든 것과 다름 — python3 scripts/dart/verify13.py build 를 다시 돌릴 것')
    else:
        rep.ok('00_목록.md 생성 칸(2-2·2-4·3절·4-1·4-2) = 다시 만든 것')
    want_csv = built_csv(entries, states, want_md)
    with open(SUM_CSV, encoding='utf-8', newline='') as f:
        have_csv = f.read()
    if want_csv != have_csv:
        rep.bad('00_종합표.csv 가 다시 만든 것과 다름 — build 를 다시 돌릴 것')
    else:
        rep.ok('00_종합표.csv = 다시 만든 것(%d행)' % (have_csv.count('\r\n') - 1))
    # (c) 2-4 표 ↔ 상태 CSV(따로 읽기)
    st = {(r['회사'], int(r['모범규준_조'])): r['상태'] for r in states}
    got = {}
    for _, c in md_tables(L, r'^### 2-4 '):
        m = re.match(r'^(\d+)조', c[1])
        if m:
            got[(c[2], int(m.group(1)))] = c[3].replace('\\|', '|')
    if got != st:
        diff = [k for k in set(st) | set(got) if st.get(k) != got.get(k)]
        rep.bad('2-4 표 상태 ≠ 상태 CSV: %d칸 (예: %s)' % (len(diff), sorted(diff)[:5]))
    else:
        rep.ok('2-4 표 %d칸 상태 = 상태 CSV A·B(%d행)' % (len(got), len(states)))
    # (d) 2-2 표 — 조별 받은 글 회사 = 상태 CSV
    short = {v[3]: v[1] for v in MD.values() if v[3]}
    nprob = 0
    rows22 = md_tables(L, r'^### 2-2 ')
    for _, c in rows22:
        m = re.match(r'^(\d+)조', c[5])
        if not m:
            continue
        n = int(m.group(1))
        cats = {}
        for it in items_of(c[2]):
            mm = re.match(r'^(받은 글|일부|추출 범위에 없음) — (.+)$', it)
            if mm:
                cats[mm.group(1)] = set(mm.group(2).split('·'))
        for comp in COMPANIES:
            s = st[(comp, n)]
            cat = '받은 글' if s == '받은 글' else ('추출 범위에 없음' if s.startswith('추출 범위에 없음') else '일부')
            if short[comp] not in cats.get(cat, set()):
                nprob += 1
                rep.bad('2-2 %d조 %s: 상태 CSV 분류 %s 와 다름' % (n, comp, cat))
    if not nprob:
        rep.ok('2-2 표 %d행 — 조별 받은 글/일부/추출 범위에 없음 회사 = 상태 CSV' % len(rows22))
    # (e) 2-1·2-3 손 정리 행 — 조 번호·R2 표지·9-4-1 상태
    texts = {}
    for f in MD:
        LL = lines_of(OUT + '/' + f)
        mk = code_mask(LL)
        texts[f] = [l for l, m in zip(LL, mk) if not m]
    ntok = nrow = 0
    for r in hand_rows():
        c = r['cells']
        nrow += 1
        if len(c) != 7:
            rep.bad('00_목록.md %d줄: 칸 수 %d(7이어야 함)' % (r['line'], len(c)))
            continue
        fs = files_in(c[6])
        if not fs:
            rep.bad('00_목록.md %d줄: 위치 칸에 md 파일 이름이 없음' % r['line'])
            continue
        task = c[0]
        is94 = task.startswith('9-4')
        allowed = set(JISI)
        if '메리츠' in c[1] or '메리츠' in c[6]:
            allowed |= {9, 57}
        if 'iM' in c[1] or 'iM금융지주' in c[6]:
            allowed |= {28, 30}
        for tok in split_tokens(c[5]):
            kind, val, title, judged = token_info(tok)
            ntok += 1
            if kind == 'art':
                if title != ARTS[val][0]:
                    rep.bad('00_목록.md %d줄: %d조 제목 「%s」 ≠ 조목록 「%s」' % (r['line'], val, title, ARTS[val][0]))
                if not is94 and not judged:
                    rep.bad('00_목록.md %d줄: %s 의 조 %d 에 (판단) 없음(R2 — 9-1·9-2·9-3·9-5 는 모두 판단)' % (r['line'], task, val))
                if is94 and not judged and val not in allowed:
                    rep.bad('00_목록.md %d줄: 지시서 밖 조 %d 에 (판단) 없음(R2)' % (r['line'], val))
                if is94 and judged and val in JISI:
                    rep.bad('00_목록.md %d줄: 지시서 조 %d 에 (판단)(R2)' % (r['line'], val))
                rx = re.compile(r'(?<![\d\-.~∼])제?%d조' % val)
                hit = [f for f in fs if any(rx.search(l) for l in texts[f])]
                if not hit:
                    rep.bad('00_목록.md %d줄: %d조 가 위치 칸 md(%s)에서 찾아지지 않음' % (r['line'], val, ', '.join(fs)))
                elif judged and is94 and not any(rx.search(l) and '판단' in l for f in fs for l in texts[f]):
                    rep.bad('00_목록.md %d줄: (판단) %d조 — 위치 칸 md 에 판단 표기와 함께 나오지 않음' % (r['line'], val))
            elif kind == 'range':
                a, b = val
                if not (1 <= a < b <= 59):
                    rep.bad('00_목록.md %d줄: 범위 %s 이상' % (r['line'], tok))
                if not is94 and not judged:
                    rep.bad('00_목록.md %d줄: %s 의 범위 %s 에 (판단) 없음(R2)' % (r['line'], task, tok))
            else:
                lab_ok = (tok.startswith('9-4 조문 대조(대조표 A~C)') or tok.startswith('조 번호 해당 없음('))
                if not lab_ok:
                    rep.bad('00_목록.md %d줄: 조 칸 표지 「%s」 — R2 표지가 아님' % (r['line'], tok))
                elif not any(tok.split('(')[0] in l for f in fs for l in texts[f]):
                    rep.bad('00_목록.md %d줄: 표지 「%s」 가 위치 칸 md 에 없음' % (r['line'], tok))
        m = re.match(r'^(?:\S+ )?상태: (.+?)(?:<br>| — |$)', c[2])
        if task == '9-4-1' and m and len(fs) >= 1 and fs[0] in COMPANY_MD.values():
            want = m.group(1).strip()
            f = fs[0]
            LL = lines_of(OUT + '/' + f)
            cand = []
            rtype = 'iM' if c[1].startswith('1. iM 그룹') else ('메리츠' if c[1].startswith('1. 메리츠 그룹') else '회사')
            for pat in (r'^## 7\. 지시서 항목별 대조', r'^## 6\. 지시서 항목별 대조'):
                for _, cc in md_tables(LL, pat):
                    lab = cc[0]
                    if rtype == '회사' and lab in ('9-4 1.', '9-4-1 목차'):
                        cand += cc
                    if rtype == 'iM' and lab == '9-4 1. iM':
                        cand += cc
                    if rtype == '메리츠' and lab == '9-4 1. 메리츠':
                        cand += cc
            if want not in cand:
                rep.bad('00_목록.md %d줄: 9-4-1 상태 「%s」 가 %s 지시서 항목 대조 표에 없음' % (r['line'], want, f))
    rep.ok('2-1·2-3 손 정리 행 %d개 · 조 칸 표지 %d개 대조' % (nrow, ntok))
    # (f) CSV 색인 행 ↔ md 태그 줄(따로 읽기)
    with open(SUM_CSV, encoding='utf-8-sig', newline='') as f:
        crow = list(csv.DictReader(f))
    if not crow or list(crow[0].keys()) != CSV_COLS:
        rep.bad('00_종합표.csv 행이 없거나 열 ≠ %s' % CSV_COLS)
    cache = {}
    nidx = nbad = 0
    for r in crow:
        jo = r['모범규준_조']
        if re.fullmatch(r'\d{1,2}', jo) and r['조_제목'] != ARTS[int(jo)][0]:
            nbad += 1
            rep.bad('00_종합표.csv 조 %s 제목 「%s」 ≠ 조목록' % (jo, r['조_제목']))
        if not r['지시서_항목'].startswith(INDEX_ITEM):
            continue
        nidx += 1
        m = re.search(r'태그 줄 (\d+)$', r['위치'])
        f = r['파일']
        if not m or not os.path.exists(f):
            nbad += 1
            rep.bad('00_종합표.csv 색인 행 위치·파일 이상: %s %s' % (f, r['위치']))
            continue
        if f not in cache:
            cache[f] = lines_of(f)
        line = cache[f][int(m.group(1)) - 1]
        fname = os.path.basename(f)
        ok = True
        if re.fullmatch(r'\d{1,2}', jo):
            n = int(jo)
            rx = re.compile(r'(?<![\d\-.~∼])제?%d조|(?<![\d\-.~])%d(?=[·~][\d·~]*조\(판단\))|(?<=[·])%d(?=조\(판단\))' % (n, n, n))
            ok = bool(rx.search(line))
            if ok and r['판단여부'] == '판단' and not MD[fname][2] and '판단' not in line:
                ok = False
            if ok and r['판단여부'] == '지시서 조' and n not in jisi_set(MD[fname][1]):
                ok = False
        elif re.match(r'^\d{1,2}~\d{1,2}', jo):
            a, b = re.match(r'^(\d{1,2})~(\d{1,2})', jo).groups()
            ok = bool(re.search(r'%s\D{0,30}[~∼]\s*제?%s' % (a, b), line))
        else:
            ok = jo.split('(')[0] in line
        if not ok:
            nbad += 1
            rep.bad('00_종합표.csv 색인 행 %s 줄 %s: 조 「%s」·판단 「%s」 가 그 태그 줄과 맞지 않음' % (fname, m.group(1), jo, r['판단여부']))
    rep.ok('00_종합표.csv %d행 가운데 색인 행 %d개를 md 태그 줄과 다시 맞댐 — 문제 %d' % (len(crow), nidx, nbad))
    # (g) CSV 상태 행 ↔ 상태 CSV
    nst = 0
    for r in crow:
        if r['작업'] in ('9-4-2', '9-4-3') and r['내용'].startswith('상태: '):
            comp = r['지시서_항목'].rsplit(' — ', 1)[-1]
            want = st.get((comp, int(r['모범규준_조'])))
            if want is None or not r['내용'].startswith('상태: %s · ' % want):
                rep.bad('00_종합표.csv 상태 행 %s %s조 ≠ 상태 CSV' % (comp, r['모범규준_조']))
            nst += 1
    rep.ok('00_종합표.csv 상태 행 %d개 = 상태 CSV 「상태」' % nst)
    # (h) 3절 판단 표시 없음(참고)
    nomark = [e for e in entries if e['jlabel'] == '판단 표시 없음']
    rep.ok('참고: 9-4 파일의 지시서 밖 조인데 태그 줄에 (판단)이 없는 곳 %d개(md 표기 그대로 — 문제로 세지 않음)%s' % (
        len(nomark), (': ' + ', '.join(sorted({'%s:%d(%s조)' % (e['short'], e['line'], e['val']) for e in nomark})[:12])) if nomark else ''))


def frag_list(text):
    """「」 안 글 — 바깥 짝 기준(겹친 「」 포함)."""
    out, stack = [], []
    for i, ch in enumerate(text):
        if ch == '「':
            stack.append(i)
        elif ch == '」' and stack:
            a = stack.pop()
            if not stack:
                out.append(text[a:i + 1])
    return out


def check_6(rep):
    rep.h('⑥ 00_목록.md·00_종합표.csv 의 원문 인용(「」·코드 블록·> 줄)이 13차 md 에 글자 그대로')
    corpus = nows(''.join(read(OUT + '/' + f) for f in MD))
    st_corpus = nows(''.join(read(p) for p in STATE_CSVS))
    L = lines_of(LIST_MD)
    mask = code_mask(L)
    frags, blocks = [], []
    for i, l in enumerate(L):
        if mask[i] and not l.startswith('```'):
            blocks.append(l)
        elif l.startswith('>'):
            blocks.append(l[1:])
        else:
            frags += [('00_목록.md %d줄' % (i + 1), x) for x in frag_list(l)]
    with open(SUM_CSV, encoding='utf-8-sig', newline='') as f:
        for k, r in enumerate(csv.DictReader(f), 2):
            stcopy = r['작업'] in ('9-4-2', '9-4-3') and r['내용'].startswith('상태: ')
            for col in ('내용', '출처', '지시서_항목'):
                frags += [('CSV %d행 %s%s' % (k, col, ' (상태 CSV 글)' if stcopy else ''), x) for x in frag_list(r[col])]
    uniq = {}
    for where, x in frags:
        uniq.setdefault(x, where)
    nb = nst = 0
    for x, where in uniq.items():
        inner = nows(x[1:-1])
        if inner in corpus:
            continue
        if '(상태 CSV 글)' in where and inner in st_corpus:
            nst += 1
            continue
        nb += 1
        rep.bad('「」 안 글이 13차 md 에 없음(%s): %s' % (where, x[:80]))
    if nst:
        rep.ok('참고: 상태 CSV 에서 그대로 옮긴 칸(찾은_방법 등)의 「」 글 %d개는 md 에는 같은 글자로 없고 상태 CSV 에 있음(문서 이름 줄임 등 — 원문 인용 아님)' % nst)
    for b in blocks:
        if b.strip() and nows(b) not in corpus:
            nb += 1
            rep.bad('인용 줄이 13차 md 에 없음: %s' % b[:80])
    rep.ok('「」 글 %d개(겹침 빼고 %d개)·인용 줄 %d개 대조 — 문제 %d' % (len(frags), len(uniq), len(blocks), nb))


def verify():
    rep = Rep()
    rep.lines.append('# verify13 — 13차 마무리 대조(00_목록.md · 00_종합표.csv · 13차 산출물 전체)')
    states = load_states()
    entries = extract_index()
    check_1(rep)
    check_2(rep)
    check_3(rep)
    check_4(rep)
    check_5(rep, states, entries)
    check_6(rep)
    rep.lines.append('')
    rep.lines.append('## 결과')
    rep.lines.append('문제 %d건 — exit %d' % (len(rep.problems), 1 if rep.problems else 0))
    with open(RESULT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(rep.lines) + '\n')
    print('verify13: 문제 %d건 → %s' % (len(rep.problems), RESULT))
    for p in rep.problems[:30]:
        print('  - ' + p[:200])
    return 1 if rep.problems else 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        build()
        sys.exit(0)
    sys.exit(verify())
