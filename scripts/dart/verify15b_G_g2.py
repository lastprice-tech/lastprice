#!/usr/bin/env python3
"""ops15b 작업 G 그룹 g2 독립 검증 — dart_out/ops15/조각/G_g2.csv · 확인_G_g2.csv · 문서목록15b_G_g2.csv · 원문/G/*.md.

수집 스크립트(ops15b_G_g2.py)의 함수는 쓰지 않고, 출처 글(사업보고서 md·연차보고서 md·6차 섹션 csv·13차 PDF 글)을 직접 다시 읽어 본다.
결과: dart_out/ops15/verify15b_G_g2.txt, exit 0(실패 0) / 1.
  --test <다른 G.csv>  : 그 csv 로 돌리고 결과 txt 는 쓰지 않음(일부러 망가뜨린 사본 시험용).

검사(작업 지시 (a)~(h)):
 (a) 원문 대조(COMMON15b): source_text·basis_text 는 출처 글의 한 곳에서 이어진 글.
     - 사업보고서 표 행(「|」로 시작): page 의 [절 n]·[표 m] 안 md 한 줄과 글자 그대로 같아야 함(「|」 끼워 넣기·칸 추가 방지).
     - 사업보고서 문단: 공백·줄바꿈(&cr; 포함)만 지우고 page 의 [절 n] 범위 안에 이어서 있어야 함(「|」「<br>」는 지우지 않음 — 더 엄격).
     - 연차보고서 PDF 글(FY2019~2023): 공백만 지우고 page 「p.N」 쪽(다음 쪽으로 넘어가는 것 허용) 안에서 시작해 이어서 있어야 함.
     - 연차보고서 6차 섹션 글(FY2024·2025): page 의 섹션(시작쪽 일치) 글 안에 이어서 있어야 하고, gov_old PDF 글 쪽(p.N)에도 첫 글이 있어야 함.
     - item_kind 는 그 표(또는 문단) 안의 원문 낱말, counterparty 는 그 표 안(칸 합침이면 위 행)·표 앞 문단의 원문 낱말(「문서에 없음」 제외).
     - section_title 의 절·주석 제목이 md 에 있음(연차보고서는 그 글 안에 있음).
 (b) 머리행·열 순서·utf-8-sig(BOM), 빈 칸 0, collected_at KST·출처 목록과 같음, doc_name 이 출처 목록 제목과 같음, page 꼴.
 (c) 빠짐: 회사×FY 마다 별도 주석 거래 행·주요 경영진 행·산정 기준(브랜드 행 또는 「(산정 기준 문단)」)·겸직 보수 행·Ⅱ 영업수익 구성 행.
     쓰인 손익 표마다 데이터 행 × 당기 칸(0·「-」·빈 칸·합계 제외)을 내가 다시 풀어 G 행과 1:1 로 맞춤.
     Ⅱ·별도 주석을 키워드로 직접 grep(「수익원」, 「브랜드」「상표」, 「경영자문」, BNK 배당금수익)해 조각 밖 자리를 찾음.
 (d) 「문서에 없음」 행 반박: 더 넓은 검색어로 출처 글을 다시 grep — 걸리면 FAIL.
 (e) 금액: 모든 금액 행에서 note 의 원문 숫자 = 내가 표 머리로 다시 정한 그 열(당기)의 칸, 단위 = 표 앞 「(단위 : …)」, amount_krw = 숫자×단위.
     30개 이상 표본을 결과 txt 에 SAMPLE 로 적음(원문 칸·열 머리·환산값).
 (f) direction: 내 기준으로 다시 정함 — 가로 표 열 이름(…수익/…이익 → 수입, …비용/임차료/손실/전입/상각비/운용비/수수료비용 하위 → 지출,
     「손익」 → 숫자 부호, 「취득」 → (판단) 지출), iM 표 안 「<수익>」「<비용>」 머리, 한국투자 FY2019~2024 「수 익」「비 용」 칸,
     JB 계정 이름 끝말, 주요 경영진 보상 → (판단) 지출. 수입·지출 행 note 에 「방향:」 또는 「(판단)」.
     note 에 이유·의도 추정 낱말(때문·위해·의도·추정·짐작·아마·보인다 등)과 기능 분류 낱말이 없어야 함(「…」 인용 안은 뺌).
 (g) 확인_G_g2.csv: REQUEST15b 의 「특히 볼 것」 1번 줄(BNK·iM·JB 해당)이 글자 그대로, BNK·iM·JB × FY2019~2025 × (브랜드, 경영관리·용역) 모두,
     result 가 G 행과 맞음(있음 ⇔ 그 이름의 행), source_excerpt 원문 대조, note 에 추정 낱말(「로만 나옴」 등) 없음.
 (h) 비밀(DART_API_KEY 값·40자리 16진·crtfc_key) 없음, 이 작업 산출 폴더에 PDF·zip·XML·그림 없음, dart_out/raw·dart_out/text 는 git 무시.
"""
import csv, os, re, sys, hashlib, subprocess, zipfile, collections, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OPS = os.path.join(ROOT, 'dart_out', 'ops15')
G = os.path.join(OPS, '조각', 'G_g2.csv')
CHK = os.path.join(OPS, '조각', '확인_G_g2.csv')
DOCS = os.path.join(OPS, '문서목록15b_G_g2.csv')
MDDIR = os.path.join(OPS, '원문', 'G')
OUT = os.path.join(OPS, 'verify15b_G_g2.txt')
TEST = False
if len(sys.argv) > 2 and sys.argv[1] == '--test':
    G = os.path.abspath(sys.argv[2])
    OUT = os.devnull
    TEST = True
CORPS = ['메리츠금융지주', 'iM금융지주', 'BNK금융지주', 'JB금융지주', '한국투자금융지주']
FYS = range(2019, 2026)
COLS = ['corp_label', 'fy', 'item_kind', 'counterparty', 'direction', 'amount_krw', 'basis_text', 'doc_kind',
        'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note', 'doc_name', 'collected_at']
DOC_COLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at', 'text_path', 'status', 'note']
NONE = '문서에 없음'
REP = '사업보고서'
ANN = '지배구조 및 보수체계 연차보고서'
UNIT = {'천원': 1000, '백만원': 1000000, '원': 1, '억원': 100000000}
PLACEHOLDER = {'(산정 기준 문단)', '(겸직 임원 보수 지급·배분 기준)', '(영업수익 구성 문단)'}
csv.field_size_limit(10 ** 9)

fails, checks, samples = [], [], []


def fail(msg):
    fails.append(msg)


def rel(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def ws(s):  # 공백·줄바꿈(&cr; 포함)만 지움
    return re.sub(r'\s+', '', s.replace('&cr;', ' '))


def nx(s):  # XML md 표지까지 지움(COMMON15b 기본 규칙)
    return ws(s.replace('<br>', ' ').replace('|', ' '))


def cells(line):
    s = line.strip()
    if not s.startswith('|'):
        return []
    return [c.strip() for c in s.strip('|').split('|')]


NUMRE = re.compile(r'^\(?-?[\d,]+\)?$')


def numcell(c):
    t = c.replace('<br>', '').replace(' ', '').replace('&cr;', '')
    return t if NUMRE.match(t) else None


def tailable(c):
    t = c.replace('<br>', '').replace(' ', '').replace('&cr;', '')
    return t == '' or t == '-' or bool(NUMRE.match(t))


def numval(t):
    neg = t.startswith('(') or t.startswith('-')
    return (-1 if neg else 1) * int(t.strip('()-').replace(',', ''))


def is_sum(c):
    return bool(re.match(r'^(합\s*계|소\s*계|총\s*계|계|순수수료손익|합계)$', ws(c)))


def base(c):  # 열 이름 「…, 특수관계자거래」 의 앞말
    return ws(c.split(',')[0])


# ------------------------------------------------------------------ 출처 목록
rep = {}
cors = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(OPS, '사업보고서_원문.csv'), encoding='utf-8-sig')):
    if r['label'] in CORPS:
        rep[r['rcept_no']] = r
        if r['kind'] != '본':
            cors[(r['label'], r['fy'])].append(r)
main_rep = {(r['label'], r['fy']): r for r in rep.values() if r['kind'] == '본'}
_md = {}


class Rep:
    def __init__(self, r):
        self.r = r
        self.raw = open(rel(r['text_path']), encoding='utf-8').read()
        self.L = self.raw.split('\n')
        self.heads = [(i, l) for i, l in enumerate(self.L) if l.startswith('### [절 ')]
        self.hidx = {}
        for k, (i, l) in enumerate(self.heads):
            m = re.match(r'### \[절 (\d+)\] (.*)$', l)
            end = self.heads[k + 1][0] if k + 1 < len(self.heads) else len(self.L)
            self.hidx[m.group(1)] = (i, end, m.group(2).strip())
        self.tab = {}
        for i, l in enumerate(self.L):
            m = re.match(r'^\[표 (\d+)\]$', l)
            if m:
                j = i + 1
                while j < len(self.L) and self.L[j] != '[표 끝]':
                    j += 1
                self.tab[m.group(1)] = (i, j)

    def sec_range(self, name):  # 「II. 사업의 내용」 ~ 「III.」 처럼 큰 절
        st = [i for i, l in self.heads if re.search(name[0], l)]
        en = [i for i, l in self.heads if re.search(name[1], l)]
        return (st[0], en[0]) if st and en else None


def R(rcept):
    if rcept not in _md:
        r = rep.get(rcept)
        _md[rcept] = Rep(r) if r and r['text_path'] and os.path.exists(rel(r['text_path'])) else None
    return _md[rcept]


# 연차보고서
ann_md = {}  # url -> [(md path, row)]
for r in csv.DictReader(open(os.path.join(OPS, '연차보고서15_목록_g2.csv'), encoding='utf-8-sig')):
    p = 'dart_out/text/ops15/연차보고서__%s__%s__%s.md' % (r['회사'], r['공시연도'], r['공시유형'])
    ann_md.setdefault(r['파일_url'], []).append((p, r))
ann_by_cy = collections.defaultdict(list)
for url, lst in ann_md.items():
    for p, r in lst:
        ann_by_cy[(r['회사'], int(r['공시연도']) - 1)].append(p)
kitfile = {}
for r in csv.DictReader(open(rel('handoff/연차보고서_파일목록.csv'), encoding='utf-8-sig')):
    if r['지주명'] in CORPS:
        kitfile.setdefault(r['url'], []).append(r)
kit = collections.defaultdict(lambda: collections.defaultdict(list))
for r in csv.DictReader(open(os.path.join(OPS, 'kit56', '연차보고서_섹션.csv'), encoding='utf-8-sig')):
    if r['지주명'] in CORPS:
        kit[r['파일명']][(r['섹션제목_원문'], r['시작페이지'], r['섹션순번'])].append((int(r['chunk_seq']), r['본문']))
_pages = {}


def pages_of(p):
    if p not in _pages:
        t = open(rel(p), encoding='utf-8').read() if os.path.exists(rel(p)) else ''
        parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
        d = {}
        for i in range(1, len(parts), 2):
            d[int(parts[i])] = parts[i + 1]
        _pages[p] = d
    return _pages[p]


def in_pages(p, n, text):
    """text 가 p 의 n 쪽에서 시작해(다음 쪽으로 넘어가도 됨) 이어서 있는가."""
    P = pages_of(p)
    if n not in P:
        return False
    w = ws(text)
    a, b = ws(P[n]), ws(P.get(n + 1, ''))
    if w in a:
        return True
    return (w in a + b) and (a + b).find(w) < len(a)


# 13차 FY2025 본문 PDF 글
z13 = {}
zp = rel('handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip')
if os.path.exists(zp):
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            m = re.search(r'사업보고서__(.+)\.md$', n)
            if m:
                t = z.read(n).decode('utf-8')
                parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
                z13[m.group(1)] = {int(parts[i]): ws(parts[i + 1]) for i in range(1, len(parts), 2)}


def z13_pages(label):
    for k, v in z13.items():
        if label.replace('금융지주', '') in k or k in label:
            return v
    return None


# ------------------------------------------------------------------ 표 풀기(내 규칙)
def unit_of(Rp, ts):
    """표 머리 앞 8줄·표 첫 2줄의 「단위」."""
    a, b = Rp.tab[ts]
    for k in list(range(a + 1, min(b, a + 3))) + list(range(a - 1, max(0, a - 9), -1)):
        m = re.search(r'단위\s*:?\s*(천원|백만원|원)', Rp.L[k])
        if m:
            return m.group(1)
    return None


def parse_table(Rp, ts):
    """→ dict(kind, leaves, rows=[(line idx, lead cells, tail cells, cp, item, marker)], hdr)"""
    a, b = Rp.tab[ts]
    lines = list(range(a + 1, b))
    hdr, data = [], []
    for k in lines:
        c = cells(Rp.L[k])
        if not c:
            continue
        if any(numcell(x) for x in c) or data or re.match(r'^<(수익|비용)>$', ws(' '.join(c))):
            data.append(k)
        else:
            hdr.append(k)
    # 데이터 줄 뒤에 나온 숫자 없는 줄(「<비용>」·기술 줄)은 data 에 그대로 둠(표지)
    H = [[x for x in cells(Rp.L[k]) if x != ''] for k in hdr]
    H = [h for h in H if h and not re.search(r'단위', ' '.join(h))]
    flat = ' '.join(' '.join(h) for h in H)
    out = dict(hdr=H, rows=[], kind=None, leaves=None)
    tails = []
    for k in data:
        c = cells(Rp.L[k])
        j = len(c)
        while j > 0 and tailable(c[j - 1]):
            j -= 1
        tails.append((k, c[:j], c[j:]))
    ntail = collections.Counter(len(t) for _, l, t in tails if t and l).most_common(1)
    ntail = ntail[0][0] if ntail else 0
    per = re.search(r'당\s*기|\(당\)', flat) and re.search(r'전\s*기|\(전\)', flat)
    if per and ntail == 2:
        out['kind'] = 'V2'
        out['leaves'] = ['당기', '전기']
    elif per and ntail == 4 and H and len(H[-1]) == 4 and all(re.match(r'^(수\s*익|비\s*용)$', x) for x in H[-1]):
        out['kind'] = 'V4'
        out['leaves'] = ['당기 ' + ws(x) for x in H[-1][:2]] + ['전기 ' + ws(x) for x in H[-1][2:]]
    elif ntail == 1 and not per:
        out['kind'] = 'V1'  # 한 기간 열(표 앞 「당기」)
        out['leaves'] = ['당기']
    else:
        last = H[-1] if H else []
        if len(last) == ntail:
            out['kind'], out['leaves'] = 'W', [ws(x) for x in last]
        elif len(H) >= 3 and len(H[-1]) + len([x for x in H[-2] if not ws(x).endswith('거래')]) == ntail and \
                all(ws(x).endswith('거래') for x in H[-2][:len(H[-2]) - len([x for x in H[-2] if not ws(x).endswith('거래')])]):
            out['kind'] = 'W'
            out['leaves'] = [ws(x) for x in H[-1]] + [ws(x) for x in H[-2] if not ws(x).endswith('거래')]
        elif len(H) >= 2 and len(H[-2]) + len(H[-1]) - 1 == ntail:
            par = [i for i, x in enumerate(H[-2]) if any(base(ch).endswith(base(x)) for ch in H[-1])]
            if len(par) == 1:
                i = par[0]
                out['kind'] = 'W'
                out['leaves'] = [ws(x) for x in H[-2][:i]] + [ws(H[-2][i]) + '>' + ws(ch) for ch in H[-1]] + [ws(x) for x in H[-2][i + 1:]]
    cp, marker = None, None
    for k, lead, tail in tails:
        if not tail or not any(numcell(x) for x in tail):
            t = ws(' '.join(lead))
            if re.match(r'^<(수익|비용)>$', t):
                marker = t.strip('<>')
            continue
        if any(is_sum(x) for x in lead):
            continue
        if out['kind'] in ('V2', 'V4', 'V1'):
            lead2 = [x for x in lead if x]
            if out['kind'] == 'V4':  # 구분 | 회사명 | 거래내역  (칸 합침이면 앞 칸이 빠짐)
                item = lead2[-1] if lead2 else None
                if len(lead2) >= 2:
                    cp = lead2[-2]
            elif len(lead2) >= 2:
                cp, item = lead2[-2], lead2[-1]
            else:
                item = lead2[0] if lead2 else None
            out['rows'].append((k, lead, tail, cp, item, marker))
        else:
            lead2 = [x for x in lead if x]
            if lead2:
                cp = lead2[-1]
            out['rows'].append((k, lead, tail, cp, None, marker))
    out['ntail'] = ntail
    return out


INC = re.compile(r'(수익|이익)')
EXP = re.compile(r'(비용|임차료|관리비|손실|전입|상각비|운용비|급여)')


def dir_by_leaf(leaf, v):
    nm = leaf.split('>')
    if '손익' in nm[-1]:
        return '지주 수입' if v > 0 else '지주 지출', True
    if '취득' in nm[-1]:
        return '지주 지출', True
    if any(EXP.search(x) for x in nm):  # 부모 열(…비용)도 봄
        return '지주 지출', False
    if INC.search(nm[-1]):
        return '지주 수입', False
    return None, True


_pt = {}


def table(Rp, rc, ts):
    k = (rc, ts)
    if k not in _pt:
        _pt[k] = parse_table(Rp, ts)
    return _pt[k]


# ------------------------------------------------------------------ G_g2.csv 읽기
raw_bytes = open(G, 'rb').read()
if not raw_bytes.startswith(b'\xef\xbb\xbf'):
    fail('G_g2: utf-8-sig BOM 없음')
with open(G, encoding='utf-8-sig', newline='') as f:
    rd = csv.DictReader(f)
    hdr = rd.fieldnames
    rows = list(rd)
if hdr != COLS:
    fail('G_g2 머리행·열 순서 다름: %s' % hdr)
checks.append('(b) G_g2 머리행·열 순서 = 사용자 열 + doc_name, collected_at, utf-8-sig')

FORBID = re.compile(r'때문|위하여|위해서|위해|의도|추정|짐작|아마|보인다|보임|듯하|듯이|로 보인|리스크 기능|재무 기능|기능 분류|기능상|이유로|이유는')


def strip_quotes(s):
    s = re.sub(r'「[^」]*」', '', s)
    s = re.sub(r'원문:[^/]*', '', s)
    return s


seen = set()
nnone = collections.Counter()
used_tables = collections.defaultdict(list)  # (rcept, ts) -> [row]
amount_checked = 0
ann_checked = 0
for k, r in enumerate(rows, 2):
    tag = 'G %d행 %s FY%s 「%s」/「%s」' % (k, r.get('corp_label'), r.get('fy'), (r.get('item_kind') or '')[:30], (r.get('counterparty') or '')[:20])
    for c in COLS:
        if not (r.get(c) or '').strip():
            fail('%s: 빈 칸 %s' % (tag, c))
    if r['corp_label'] not in CORPS:
        fail('%s: 회사 밖' % tag)
    if not r['fy'].isdigit() or not (2019 <= int(r['fy']) <= 2025):
        fail('%s: fy 범위 밖' % tag)
        continue
    if r['direction'] not in ('지주 수입', '지주 지출', NONE):
        fail('%s: direction 값 %s' % (tag, r['direction']))
    if r['direction'] != NONE and '방향:' not in r['note'] and '(판단)' not in r['note']:
        fail('%s: direction 기준(방향:/(판단)) note 에 없음' % tag)
    if not re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$', r['collected_at']):
        fail('%s: collected_at KST 꼴 아님' % tag)
    if FORBID.search(strip_quotes(r['note'])):
        fail('%s: note 에 추정·기능 분류 낱말 「%s」' % (tag, FORBID.search(strip_quotes(r['note'])).group(0)))
    key = (r['corp_label'], r['fy'], r['item_kind'], r['counterparty'], r['source_text'], r['direction'], r['amount_krw'])
    if key in seen:
        fail('%s: 같은 행 두 번' % tag)
    seen.add(key)
    if r['source_text'] == NONE:
        nnone['source_text'] += 1
        if '찾은 범위' not in r['note']:
            fail('%s: 문서에 없음 행에 찾은 범위 없음' % tag)
        if r['amount_krw'] != NONE or r['basis_text'] != NONE:
            fail('%s: 문서에 없음 행에 금액·basis 있음' % tag)
        if r['item_kind'] not in PLACEHOLDER:
            fail('%s: 문서에 없음 행 item_kind 가 정한 표지 밖' % tag)
    for c in ('basis_text', 'counterparty', 'direction', 'amount_krw'):
        if r[c] == NONE:
            nnone[c] += 1
    if r['basis_text'] == NONE and r['source_text'] != NONE and '찾은 범위' not in r['note'] and 'basis_text' not in r['note']:
        fail('%s: basis_text 문서에 없음인데 note 에 찾은 범위 없음' % tag)

    # ---------------- 사업보고서
    if r['doc_kind'] == REP:
        rr = rep.get(r['rcept_no_or_url'])
        if not rr or rr['kind'] != '본' or rr['label'] != r['corp_label'] or rr['fy'] != r['fy']:
            fail('%s: rcept 가 그 회사·FY 본 사업보고서 아님' % tag)
            continue
        if r['collected_at'] != rr['fetched_at'] or r['doc_name'] != rr['report_nm']:
            fail('%s: collected_at/doc_name 이 사업보고서_원문.csv 와 다름' % tag)
        Rp = R(r['rcept_no_or_url'])
        if Rp is None:
            fail('%s: 사업보고서 md 없음' % tag)
            continue
        m = re.match(r'^XML \[절 (\d+)\] 「(.+?)」(?: \[표 (\d+)\])?(.*)$', r['page'])
        if not m:
            fail('%s: page 꼴(XML [절 n] 「…」) 아님: %s' % (tag, r['page'][:60]))
            continue
        sn, stitle, ts, rest = m.groups()
        if sn not in Rp.hidx or Rp.hidx[sn][2] != stitle:
            fail('%s: page 의 [절 %s] 「%s」 가 md 제목과 다름' % (tag, sn, stitle))
            continue
        a, b, _ = Rp.hidx[sn]
        if r['section_title'] != NONE:
            ms = re.match(r'^XML \[절 (\d+)\] 「(.+?)」(?: > 주석 「(.+)」)?$', r['section_title'])
            if not ms or ms.group(1) != sn or ms.group(2) != stitle:
                fail('%s: section_title 의 절이 page 와 다름' % tag)
            elif ms.group(3) and nx(ms.group(3)) not in nx('\n'.join(Rp.L[a:b])):
                fail('%s: section_title 주석 제목 「%s」 이 그 절 안에 없음' % (tag, ms.group(3)))
        if r['fy'] == '2025' and r['corp_label'] in ('iM금융지주', '메리츠금융지주', '한국투자금융지주') and r['source_text'] != NONE:
            mp = re.search(r'p\.(\d+)\(본문 PDF, 13차 보관[^)]*\)', rest)
            if not mp:
                fail('%s: FY2025 13차 PDF 쪽 없음' % tag)
            else:
                P = z13_pages(r['corp_label'])
                n13 = int(mp.group(1))
                need = [x for x in [ws(r['counterparty']) if r['counterparty'] != NONE else ''] if x]
                mm = re.search(r'원문 숫자 (\(?-?[\d,]+\)?)', r['note'])
                if mm:
                    need.append(mm.group(1).strip('()'))
                if not r['source_text'].startswith('|'):
                    need = [ws(r['source_text'])[:15]]
                if P is None or n13 not in P:
                    fail('%s: 13차 PDF 글에 p.%d 없음' % (tag, n13))
                elif not all(x in P[n13] for x in need):
                    fail('%s: 13차 PDF p.%d 에 %s 없음' % (tag, n13, need))
        st = r['source_text']
        if st == NONE:
            continue
        if ts:
            if ts not in Rp.tab:
                fail('%s: [표 %s] 가 md 에 없음' % (tag, ts))
                continue
            ta, tb = Rp.tab[ts]
            if not (a <= ta < b):
                fail('%s: [표 %s] 가 [절 %s] 밖' % (tag, ts, sn))
            if not st.startswith('|'):
                fail('%s: page 에 표가 있는데 source_text 가 표 행 아님' % tag)
                continue
            idx = [i for i in range(ta + 1, tb) if Rp.L[i].strip() == st.strip()]
            if not idx:
                fail('%s: source_text 표 행이 [표 %s] 안 md 한 줄과 글자 그대로 같지 않음: %s' % (tag, ts, st[:70]))
                continue
            used_tables[(r['rcept_no_or_url'], ts)].append((k, r, idx))
            # item_kind·counterparty 가 표 안 원문 낱말
            T = nx('\n'.join(Rp.L[ta:tb]))
            if r['item_kind'] not in PLACEHOLDER and nx(r['item_kind']) not in T:
                fail('%s: item_kind 가 그 표 안에 없음' % tag)
            if r['counterparty'] != NONE and nx(r['counterparty']) not in T:
                pre = nx('\n'.join(Rp.L[max(a, ta - 12):ta]))
                if nx(r['counterparty']) not in pre:
                    fail('%s: counterparty 가 그 표·표 앞 문단에 없음' % tag)
        else:
            if st.startswith('|'):
                fail('%s: 표 행인데 page 에 [표 m] 없음' % tag)
                continue
            if ws(st) not in ws('\n'.join(Rp.L[a:b])):
                fail('%s: source_text 문단이 [절 %s] 안에 이어서 없음(공백만 무시, 「|」 지우지 않음)' % (tag, sn))
                continue
            if r['item_kind'] not in PLACEHOLDER and ws(r['item_kind']) not in ws(st):
                fail('%s: item_kind 가 문단 글 안에 없음' % tag)
            if r['counterparty'] != NONE and ws(r['counterparty']) not in ws(st):
                fail('%s: counterparty 가 문단 글 안에 없음' % tag)
        if r['basis_text'] != NONE and ws(r['basis_text']) not in ws('\n'.join(Rp.L[a:b])):
            fail('%s: basis_text 가 [절 %s] 안에 이어서 없음' % (tag, sn))
        # 원문 md
        md = os.path.join(MDDIR, '%s__FY%s__사업보고서.md' % (r['corp_label'], r['fy']))
        if not os.path.exists(md):
            fail('%s: 원문 md 없음' % tag)
        else:
            if md not in _md:
                _md[md] = open(md, encoding='utf-8').read()
            mt = _md[md]
            if (st.strip() not in mt) if st.startswith('|') else (ws(st) not in ws(mt)):
                fail('%s: 원문 md 에 source_text 없음' % tag)
        # 정정판 대조
        for c in cors.get((r['corp_label'], r['fy']), []):
            tp = c['text_path']
            if not tp or not os.path.exists(rel(tp)):
                if c['rcept_no'] not in r['note']:
                    fail('%s: 정정 %s(글 없음)이 note 에 없음' % (tag, c['rcept_no']))
                continue
            Rc = R(c['rcept_no'])
            if Rc and nx(st) not in nx(Rc.raw) and c['rcept_no'] not in r['note']:
                fail('%s: 정정 %s 에 이 글이 그대로 없는데 note 에 없음' % (tag, c['rcept_no']))
        # 금액(문단)
        if not st.startswith('|') and r['amount_krw'] != NONE:
            mm = re.search(r'원문 단위 (천원|백만원|원|억원), 원문 숫자 (\(?-?[\d,]+\)?)', r['note'])
            if not mm or not re.match(r'^-?\d+$', r['amount_krw']):
                fail('%s: 문단 금액 note 꼴·정수 아님' % tag)
            else:
                v = numval(mm.group(2)) * UNIT[mm.group(1)]
                if str(v) != r['amount_krw']:
                    fail('%s: amount_krw ≠ 원문 숫자×단위' % tag)
                if not re.search(re.escape(mm.group(2)) + r'\s*' + mm.group(1), st):
                    fail('%s: 문단에 「%s%s」 글이 없음' % (tag, mm.group(2), mm.group(1)))
                amount_checked += 1
                samples.append('%s FY%s %s | 문단 「…%s%s…」 → %s원' % (r['corp_label'], r['fy'], r['item_kind'], mm.group(2), mm.group(1), r['amount_krw']))
    # ---------------- 연차보고서
    elif r['doc_kind'] == ANN:
        url = r['rcept_no_or_url']
        fy = int(r['fy'])
        if r['source_text'] == NONE:
            if not re.match(r'^전체 \d+쪽', r['page']) and '찾은 범위' not in r['note']:
                fail('%s: 문서에 없음 page·범위 꼴' % tag)
        src_ok = False
        if url in ann_md:
            lst = ann_md[url]
            meta = lst[0][1]
            if r['doc_name'] != meta['제목']:
                fail('%s: doc_name 이 연차보고서 목록 제목과 다름' % tag)
            if r['collected_at'] != meta['fetched_at']:
                fail('%s: collected_at 이 연차보고서 목록 fetched_at 과 다름' % tag)
            if int(meta['공시연도']) - 1 != fy:
                fail('%s: 공시연도-1 ≠ fy' % tag)
            if r['source_text'] != NONE:
                mp = re.match(r'^p\.(\d+)$', r['page'])
                if not mp:
                    fail('%s: page 꼴(p.N) 아님' % tag)
                else:
                    n = int(mp.group(1))
                    for col in ('source_text', 'basis_text'):
                        if r[col] == NONE:
                            continue
                        ok = any(in_pages(p, n, r[col]) for p, _ in lst)
                        if not ok:
                            pm = [q for q in re.findall(r'p\.(\d+)', r['note'])]
                            ok = any(in_pages(p, int(q), r[col]) for p, _ in lst for q in pm) if col == 'basis_text' else False
                        if not ok:
                            fail('%s: %s 가 p.%d 쪽 안에 이어서 없음' % (tag, col, n))
                    T = re.sub(r'[\ue000-\uf8ff]', '', ''.join(ws(pages_of(p).get(n, '')) + ws(pages_of(p).get(n - 1, '')) for p, _ in lst))
                    if r['section_title'] != NONE and ws(r['section_title']) not in T:  # 쪽 글의 PDF 사설 영역 문자(U+E000~F8FF)만 빼고 봄
                        fail('%s: section_title 「%s」 이 p.%d(앞쪽 포함) 글에 없음' % (tag, r['section_title'][:30], n))
            src_ok = True
        elif url in kitfile:
            km = kitfile[url]
            if r['doc_name'] not in [x['제목'] for x in km]:
                fail('%s: doc_name 이 연차보고서_파일목록 제목과 다름' % tag)
            fts = []
            for x in km:
                t = x['fetched_at']
                mt = re.match(r'(\d{4}-\d\d-\d\d)T(\d\d):(\d\d):(\d\d)\+0000', t)
                if mt:
                    d = datetime.datetime.strptime(mt.group(1) + mt.group(2) + mt.group(3) + mt.group(4), '%Y-%m-%d%H%M%S') + datetime.timedelta(hours=9)
                    fts.append(d.strftime('%Y-%m-%dT%H:%M:%S+09:00'))
            if r['collected_at'] not in fts:
                fail('%s: collected_at 이 연차보고서_파일목록 fetched_at(KST) 과 다름' % tag)
            if r['source_text'] != NONE:
                mp = re.match(r'^p\.(\d+)\(6차 섹션 「(.+?)」 시작쪽\) / p\.(\d+)\(gov_old 가 다시 받은 PDF 글 (\S+)\)$', r['page'])
                if not mp:
                    fail('%s: page 꼴(6차 섹션 시작쪽 / gov_old 쪽) 아님' % tag)
                else:
                    sp, stt, gp, gpath = mp.groups()
                    secs = []
                    for x in km:
                        for (tt, s0, sq), ch in kit[x['파일명']].items():
                            if tt == stt and s0 == sp:
                                secs.append(ch)
                    if not secs:
                        fail('%s: 6차 섹션 「%s」 시작쪽 %s 없음' % (tag, stt, sp))
                    for col in ('source_text', 'basis_text'):
                        if r[col] == NONE:
                            continue
                        w = ws(r[col])
                        if not any(w in ws(''.join(t for _, t in sorted(ch))) for ch in secs):
                            fail('%s: %s 가 6차 섹션 「%s」 글 안에 이어서 없음' % (tag, col, stt))
                    w = ws(r['source_text'])
                    G_ = pages_of(gpath)
                    gp = int(gp)
                    if not G_:
                        fail('%s: gov_old PDF 글 없음 %s' % (tag, gpath))
                    else:
                        probe = [w[:12], w[len(w) // 2:len(w) // 2 + 12], w[-12:]]
                        if not any(pz in ws(G_.get(gp, '')) for pz in probe):
                            fail('%s: gov_old PDF 글 p.%d 에 source_text 글이 없음' % (tag, gp))
                    if r['section_title'] != NONE and r['section_title'] != stt:
                        fail('%s: section_title 이 6차 섹션 제목과 다름' % tag)
            src_ok = True
        if not src_ok:
            fail('%s: 연차보고서 URL 이 목록에 없음' % tag)
        if r['source_text'] != NONE:
            ann_checked += 1
            md = os.path.join(MDDIR, '%s__FY%s__연차보고서.md' % (r['corp_label'], r['fy']))
            if not os.path.exists(md) or ws(r['source_text']) not in ws(open(md, encoding='utf-8').read()):
                fail('%s: 원문 md(연차보고서)에 source_text 없음' % tag)
            if r['amount_krw'] != NONE:
                fail('%s: 연차보고서 문단 행에 금액' % tag)
    else:
        fail('%s: doc_kind 값 %s' % (tag, r['doc_kind']))
checks.append('(a)(b) G_g2 %d행: 빈 칸·회사·FY·KST·출처 목록 일치·page 꼴·[절]/[표] 위치 안 표 행 글자 그대로·문단 공백만 무시 이어서·item_kind/counterparty 표 안 원문·section_title·원문 md·정정판 대조·연차보고서 쪽/섹션 위치(%d행)' % (len(rows), ann_checked))

# ------------------------------------------------------------------ 표 다시 풀기: 열·금액·방향·빠짐 (c)(e)(f)
nrow_amt = 0
for (rc, ts), lst in sorted(used_tables.items()):
    Rp = R(rc)
    T = table(Rp, rc, ts)
    unit = unit_of(Rp, ts)
    label, fy = rep[rc]['label'], rep[rc]['fy']
    ttag = '%s FY%s [표 %s]' % (label, fy, ts)
    if not T['kind']:
        fail('%s: 표 머리를 풀지 못함(열 수 %d, 머리 %s)' % (ttag, T['ntail'], T['hdr'][-2:]))
        continue
    if not unit:
        fail('%s: 표 앞·안에 단위 없음' % ttag)
    # 기대 행: 데이터 행 × 당기 칸. 수수료손익 주석 표(G 행이 모두 브랜드·경영자문 이름)는 그 이름 행만
    fee = all(re.search(r'브랜드|경영자문|상표', r['item_kind']) for (_, r, _) in lst)
    expect = collections.Counter()
    info = {}
    for (k, lead, tail, cp, item, marker) in T['rows']:
        if fee and not re.search(r'브랜드|경영자문|상표', item or ''):
            continue
        if T['kind'] in ('V2', 'V1'):
            cand = [(0, item)]
        elif T['kind'] == 'V4':
            cand = [(0, item), (1, item)]
        else:
            if len(tail) != len(T['leaves']):
                fail('%s: md %d줄 숫자 칸 %d ≠ 열 %d' % (ttag, k + 1, len(tail), len(T['leaves'])))
                continue
            cand = [(j, T['leaves'][j]) for j in range(len(tail))]
        for j, nm in cand:
            t = numcell(tail[j]) if j < len(tail) else None
            if t is None or numval(t) == 0:
                continue
            kk = (k, t, ws(nm.split('>')[-1]) if T['kind'] == 'W' else ws(nm or ''))
            expect[kk] += 1
            info[kk] = (cp, marker, j)
    got = collections.Counter()
    for (gk, r, idx) in lst:
        mm = re.search(r'원문 단위 (천원|백만원|원), 원문 숫자 (\(?-?[\d,]+\)?)', r['note'])
        tg = 'G %d행 %s FY%s 「%s」/「%s」' % (gk, label, fy, r['item_kind'][:30], r['counterparty'][:20])
        if not mm:
            fail('%s: note 에 원문 단위·숫자 없음' % tg)
            continue
        if unit and mm.group(1) != unit:
            fail('%s: note 단위 %s ≠ 표 단위 %s' % (tg, mm.group(1), unit))
        v = numval(mm.group(2)) * UNIT[mm.group(1)]
        if not re.match(r'^-?\d+$', r['amount_krw']) or int(r['amount_krw']) != v:
            fail('%s: amount_krw %s ≠ %s×%s' % (tg, r['amount_krw'], mm.group(2), mm.group(1)))
        if v == 0:
            fail('%s: 0 금액 행' % tg)
        nm = ws(r['item_kind'])
        hit = [kk for kk in expect if kk[0] in idx and kk[1] == mm.group(2) and kk[2] == nm]
        hit.sort(key=lambda kk: (got[kk] >= expect[kk], info[kk][0] is None or ws(info[kk][0]) != ws(r['counterparty'])))
        if not hit:
            fail('%s: 내가 다시 푼 표에서 이 칸(행 %s, 숫자 %s, 열/계정 %s)이 당기 칸으로 나오지 않음' % (tg, [i + 1 for i in idx], mm.group(2), r['item_kind'][:30]))
            continue
        kk = hit[0]
        got[kk] += 1
        cp, marker, j = info[kk]
        # counterparty
        if r['counterparty'] != NONE and T['kind'] != 'V1' and cp is not None and ws(r['counterparty']) != ws(cp) and \
                not (r['counterparty'] == '주요 경영진' and T['kind'] == 'V2'):
            fail('%s: counterparty 「%s」 ≠ 내가 다시 푼 상대방 「%s」' % (tg, r['counterparty'], cp))
        # direction
        km = r['counterparty'] in ('주요 경영진',) or '주요 경영진' in r['counterparty'] or '주요 경영진' in r['note']
        if km:
            exp_d, judge = '지주 지출', True
        elif T['kind'] == 'V4':
            exp_d, judge = ('지주 수입' if j == 0 else '지주 지출'), False
        elif T['kind'] == 'V2' and marker:
            exp_d, judge = ('지주 수입' if marker == '수익' else '지주 지출'), False
        elif T['kind'] == 'W':
            exp_d, judge = dir_by_leaf(T['leaves'][j], numval(mm.group(2)))
        else:
            # JB·BNK·JB 수수료 표: 계정 이름 / 표 안 「수수료수익」 묶음
            if re.search(r'브랜드|경영자문', r['item_kind']):
                exp_d, judge = '지주 수입', False
            else:
                exp_d, judge = dir_by_leaf(r['item_kind'], numval(mm.group(2)))
        if exp_d and r['direction'] != exp_d:
            fail('%s: direction %s ≠ 내 기준 %s' % (tg, r['direction'], exp_d))
        if judge and '(판단)' not in r['note']:
            fail('%s: 기계 기준 밖 방향인데 note 에 (판단) 없음' % tg)
        nrow_amt += 1
        if len(samples) < 400:
            samples.append('%s FY%s [표 %s] md %d줄 | 상대방 %s | 열/계정 %s | 원문 칸 %s %s | %s → amount_krw %s' % (
                label, fy, ts, kk[0] + 1, cp, (T['leaves'][j] if T['kind'] == 'W' else r['item_kind'] + ' / ' + T['leaves'][j]),
                mm.group(2), unit, r['direction'], r['amount_krw']))
    for kk, n in expect.items():
        if got[kk] < n:
            fail('%s: md %d줄 숫자 %s(열/계정 %s) 의 G 행 없음(빠짐)' % (ttag, kk[0] + 1, kk[1], kk[2]))
    for kk, n in got.items():
        if n > expect[kk]:
            fail('%s: md %d줄 숫자 %s 의 G 행이 %d번(중복)' % (ttag, kk[0] + 1, kk[1], n))
checks.append('(c)(e)(f) 쓰인 손익 표 %d개를 내 규칙으로 다시 풀어 데이터 행×당기 칸 ↔ G 행 1:1(빠짐·중복 0), 금액 행 %d개 열·숫자·단위·환산·상대방·방향 대조' % (len(used_tables), nrow_amt))

# ------------------------------------------------------------------ 범위·빠짐(c)·반박(d)
by = collections.defaultdict(list)
for r in rows:
    by[(r['corp_label'], r['fy'])].append(r)
for c in CORPS:
    for y in FYS:
        rs = by.get((c, str(y)), [])
        tag = '범위 %s FY%d' % (c, y)
        mr = main_rep[(c, str(y))]
        Rp = R(mr['rcept_no'])
        rr = [r for r in rs if r['doc_kind'] == REP]
        trade = [r for r in rr if r['source_text'].startswith('|') and '주요 경영진' not in r['counterparty']]
        keym = [r for r in rr if '주요 경영진' in r['counterparty']]
        if not trade:
            fail('%s: 별도 주석 특수관계자 거래 행 없음' % tag)
        if not keym:
            fail('%s: 주요 경영진 보상 행 없음' % tag)
        brand = [r for r in rr if re.search(r'브랜드|상표', r['item_kind'])]
        basis = [r for r in rr if r['item_kind'] == '(산정 기준 문단)']
        if not brand and not basis:
            fail('%s: 브랜드 행도 「(산정 기준 문단)」 행도 없음' % tag)
        gy = [r for r in rs if r['item_kind'] == '(겸직 임원 보수 지급·배분 기준)']
        if not gy:
            fail('%s: 「(겸직 임원 보수 지급·배분 기준)」 행 없음' % tag)
        s2 = Rp.sec_range((r'\] (II|Ⅱ)\. 사업의 내용', r'\] (III|Ⅲ)\. 재무에 관한'))
        rev = []
        for r in rr:
            mp_ = re.match(r'^XML \[절 (\d+)\]', r['page'])
            if s2 and mp_ and mp_.group(1) in Rp.hidx and s2[0] <= Rp.hidx[mp_.group(1)][0] < s2[1] and r['item_kind'] != '(산정 기준 문단)':
                rev.append(r)
        if not rev:
            fail('%s: Ⅱ 영업수익 구성 행(또는 「(영업수익 구성 문단)」 문서에 없음 행) 없음' % tag)
        # (c) Ⅱ 직접 grep: 지주 수익원 문단
        if s2:
            a, b = s2
            W2 = ws('\n'.join(Rp.L[a:b]))
            hits = [m.start() for m in re.finditer(r'주요?수[익입]원', W2)]
            hits = [h for h in hits if re.search(r'지주|당사', W2[max(0, h - 40):h]) and '배당' in W2[max(0, h - 30):h + 40]]
            for h in hits:
                piece = W2[h - 2:h + 25]
                if not any(piece in ws(r['source_text']) for r in rev if r['source_text'] != NONE):
                    fail('%s: Ⅱ 「…%s…」 지주 수익원 글이 G 행에 없음' % (tag, piece))
            if not hits and any(r['source_text'] != NONE for r in rev):
                pass
            if not hits and not any(r['item_kind'] == '(영업수익 구성 문단)' for r in rev):
                fail('%s: Ⅱ 수익원 글이 없는데 「(영업수익 구성 문단)」 문서에 없음 행 없음' % tag)
            if hits and any(r['item_kind'] == '(영업수익 구성 문단)' for r in rev):
                fail('%s: Ⅱ 수익원 글이 있는데 「(영업수익 구성 문단)」 문서에 없음 행이 있음' % tag)
        # (d) 산정 기준 반박: 보고서 전체에서 브랜드·상표 + 요율·산정
        if basis or (brand and all(r['basis_text'] == NONE for r in brand)):
            Wall = ws(Rp.raw)
            for m in re.finditer(r'(상표|브랜드)(권)?(사용료|사용수수료|수수료)', Wall):
                ctx = Wall[m.start():m.end() + 80]
                if re.search(r'요율|%|산정|비율|기준으로|에따라', ctx):
                    fail('%s: 산정 기준 문서에 없음인데 「%s」 글 있음' % (tag, ctx[:80]))
        # (c) 별도 주석 직접 grep: 브랜드·경영자문 이름 표 행이 G 에 없는지
        sep = Rp.sec_range((r'\] 5\. 재무제표 주석', r'\] (IV|Ⅳ)\. '))
        if sep:
            a, b = sep
            gl = set(r['source_text'].strip() for r in rr)
            notes = ' '.join(r['note'] for r in rs)
            seenlab = set()
            for i in range(a, b):
                l = Rp.L[i]
                if not l.startswith('|'):
                    continue
                c0 = cells(l)
                lab = tuple(ws(x) for x in c0 if not numcell(x) and x and re.search(r'브랜드|상표권?\s*사용|경영자문', x))
                if not lab:
                    continue
                if lab in seenlab:  # 같은 이름의 뒤 표 = 같은 절 안 전기·전전기 주석 되풀이(첫 표만 당기)
                    continue
                seenlab.add(lab)
                if any(numcell(x) and numval(numcell(x)) != 0 for x in c0) and l.strip() not in gl and l.strip() not in notes:
                    fail('%s: 별도 주석 md %d줄 「%s」 이 G 행에 없고 note 에도 없음' % (tag, i + 1, l[:60]))
            if c == 'BNK금융지주' and y <= 2023:
                for i in range(a, b):
                    l = Rp.L[i]
                    if '배당금수익' in l and re.search(r'부산은행|경남은행|BNK', l) and l.strip() not in gl:
                        fail('%s: 별도 주석 md %d줄 종속기업 배당금수익 글이 있음(배당 행 없음 판단 반박)' % (tag, i + 1))
        # (d) 겸직 보수 문서에 없음 반박
        pat = re.compile(r'겸직[^。]{0,40}?(보수|급여|성과급)[^。]{0,60}?(분담|배분|비율에따라|정산)|(보수|급여)(를|는)?[^。]{0,20}?(분담|배분|정산)[^。]{0,40}?겸직')
        if gy and all(r['source_text'] == NONE for r in gy):
            texts = []
            for p in ann_by_cy.get((c, y), []):
                texts += list(pages_of(p).values())
            for fn in [x for x in os.listdir(rel('dart_out/text/ops15b')) if x.startswith('연차보고서__%s__FY%d' % (c, y))] if os.path.isdir(rel('dart_out/text/ops15b')) else []:
                texts += list(pages_of('dart_out/text/ops15b/' + fn).values())
            for url, kl in kitfile.items():
                for x in kl:
                    if x['지주명'] == c and x['공시연도'].isdigit() and int(x['공시연도']) - 1 == y:
                        texts += [t for ch in kit[x['파일명']].values() for _, t in ch]
            for t in texts:
                m = pat.search(ws(t))
                if m:
                    fail('%s: 겸직 보수 「문서에 없음」인데 연차보고서에 「%s」' % (tag, ws(t)[max(0, m.start() - 20):m.end() + 20]))
                    break
checks.append('(c)(d) 범위 35개(회사×FY): 거래·주요 경영진·산정 기준·겸직 보수·Ⅱ 수익원 행 모두; Ⅱ 「주수익원」 직접 grep, 별도 주석 「브랜드」「상표 사용」「경영자문」 표 행 직접 grep, BNK FY2019~2023 배당금수익 grep, 산정 기준·겸직 보수 「문서에 없음」 넓은 검색어 반박')

# ------------------------------------------------------------------ 확인_G_g2.csv (g)
raw_c = open(CHK, 'rb').read()
if not raw_c.startswith(b'\xef\xbb\xbf'):
    fail('확인: utf-8-sig BOM 없음')
with open(CHK, encoding='utf-8-sig', newline='') as f:
    rd = csv.DictReader(f)
    chdr = rd.fieldnames
    crows = list(rd)
if chdr != CHK_COLS:
    fail('확인 머리행 다름: %s' % chdr)
reqlines = [re.sub(r'^\s*\*\s*', '', l).strip() for l in open(os.path.join(OPS, 'REQUEST15b.md'), encoding='utf-8').read().split('\n')]
need_item = [l for l in reqlines if l.startswith('KB·하나·우리·BNK·iM·JB FY2025')]
CFORBID = re.compile(r'로만 나옴|로만 나온|에 포함|들어 있|보인다|보임|추정|짐작|때문|위해|의도|아마')
cov = collections.Counter()
for k, r in enumerate(crows, 2):
    tag = '확인 %d행 %s FY%s %s' % (k, r.get('corp_label'), r.get('fy'), r.get('item_id'))
    for c in CHK_COLS:
        if not (r.get(c) or '').strip():
            fail('%s: 빈 칸 %s' % (tag, c))
    if r['item_text'] not in reqlines:
        fail('%s: item_text 가 REQUEST15b.md 줄과 글자 그대로 같지 않음' % tag)
    if r['result'] not in ('원문 있음', NONE, '수집 실패'):
        fail('%s: result 값' % tag)
    if len(r['source_excerpt']) > 300:
        fail('%s: source_excerpt 300자 넘음' % tag)
    if CFORBID.search(strip_quotes(r['note'])):
        fail('%s: note 에 추정 낱말 「%s」' % (tag, CFORBID.search(strip_quotes(r['note'])).group(0)))
    mr = main_rep.get((r['corp_label'], r['fy']))
    if not mr:
        fail('%s: 회사·FY 밖' % tag)
        continue
    if r['doc_name'] != mr['report_nm'] or r['collected_at'] != mr['fetched_at']:
        fail('%s: doc_name/collected_at 이 사업보고서_원문.csv 와 다름' % tag)
    mine = by.get((r['corp_label'], r['fy']), [])
    sub = '경영관리' in r['item_id']
    rx = r'경영자문|경영관리|용역' if sub else r'브랜드|상표'
    have = [x for x in mine if x['doc_kind'] == REP and re.search(rx, x['item_kind'])]
    if (r['result'] == '원문 있음') != bool(have):
        fail('%s: result %s 인데 G 행의 「%s」 이름 행 %d개' % (tag, r['result'], rx, len(have)))
    if r['result'] == '원문 있음':
        Rp = R(r['rcept_no_or_url'])
        ex = r['source_excerpt']
        m = re.match(r'^XML \[절 (\d+)\] 「(.+?)」 \[표 (\d+)\]', r['page'])
        if Rp is None or not m or m.group(3) not in Rp.tab:
            fail('%s: rcept·page 위치를 찾지 못함' % tag)
        else:
            ta, tb = Rp.tab[m.group(3)]
            if ex.strip() not in [Rp.L[i].strip() for i in range(ta + 1, tb)]:
                fail('%s: source_excerpt 표 행이 그 표 md 한 줄과 같지 않음' % tag)
            if not any(x['source_text'] == ex for x in have):
                fail('%s: source_excerpt 가 G 행 글과 다름' % tag)
    else:
        if '찾은 범위' not in r['note']:
            fail('%s: 문서에 없음 행에 찾은 범위 없음' % tag)
        # 반박: 별도 주석·보고서 전체 grep
        Rp = R(mr['rcept_no'])
        sep = Rp.sec_range((r'\] 5\. 재무제표 주석', r'\] (IV|Ⅳ)\. '))
        if sep:
            a, b = sep
            for i in range(a, b):
                l = Rp.L[i]
                if not l.startswith('|') or not any(numcell(x) and numval(numcell(x)) != 0 for x in cells(l)):
                    continue
                lab = ' '.join(x for x in cells(l) if not numcell(x))
                if re.search(r'경영자문|경영관리|용역', lab) if sub else re.search(r'브랜드|상표권?\s*(사용|수수료)', lab):
                    if l.strip() not in r['note'] and not any(l.strip() in x['note'] for x in mine):
                        fail('%s: 문서에 없음인데 별도 주석 md %d줄 「%s」' % (tag, i + 1, l[:60]))
    cov[(r['corp_label'], r['fy'], sub)] += 1
for c in ('BNK금융지주', 'iM금융지주', 'JB금융지주'):
    for y in FYS:
        for sub in (False, True):
            if not cov[(c, str(y), sub)]:
                fail('확인: %s FY%d %s 행 없음' % (c, y, '경영관리·용역' if sub else '브랜드'))
if not need_item:
    fail('확인: REQUEST15b 에 「특히 볼 것」 1번 줄을 찾지 못함')
checks.append('(g) 확인_G_g2 %d행: 머리행·BOM·item_text 글자 그대로(REQUEST15b 「특히 볼 것」 1번)·BNK/iM/JB×FY2019~2025×(브랜드, 경영관리·용역) 모두·result ⇔ G 행·source_excerpt 표 행 글자 그대로·「문서에 없음」 별도 주석 grep 반박·note 추정 낱말 없음' % len(crows))

# ------------------------------------------------------------------ 문서목록
with open(DOCS, encoding='utf-8-sig', newline='') as f:
    rd = csv.DictReader(f)
    dhdr = rd.fieldnames
    drows = list(rd)
if dhdr != DOC_COLS:
    fail('문서목록 머리행 다름: %s' % dhdr)
nsha = 0
for r in drows:
    if r['status'] not in ('받음', '014', '없음', '막힘', '실패'):
        fail('문서목록 status 값 %s' % r['status'])
    if r['doc_kind'] == REP:
        rr = rep.get(r['rcept_no_or_url'])
        if not rr:
            fail('문서목록 %s: 사업보고서_원문.csv 에 없음' % r['rcept_no_or_url'])
            continue
        if r['status'] == '받음' and not os.path.exists(rel(r['text_path'])):
            fail('문서목록 text_path 없음 %s' % r['text_path'])
        if r['sha256'] != rr['raw_sha256'] or r['fetched_at'] != rr['fetched_at']:
            fail('문서목록 %s: sha256/fetched_at 이 사업보고서_원문.csv 와 다름' % r['rcept_no_or_url'])
        rp = rel(r['raw_path'])
        if os.path.isfile(rp):
            if hashlib.sha256(open(rp, 'rb').read()).hexdigest() != r['sha256']:
                fail('문서목록 %s: 원본 zip sha256 다름' % r['rcept_no_or_url'])
            nsha += 1
    if not re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$', r['fetched_at']):
        fail('문서목록 %s: fetched_at KST 꼴 아님' % r['rcept_no_or_url'][:40])
used = set(r['rcept_no_or_url'] for r in rows)
listed = set(r['rcept_no_or_url'] for r in drows)
for u in sorted(used - listed):
    fail('문서목록에 없는 출처 %s' % u)
for (c, y), lst in cors.items():
    for x in lst:
        if x['rcept_no'] not in listed:
            fail('문서목록에 정정판 %s 없음' % x['rcept_no'])
checks.append('(b) 문서목록 %d행: 머리행·status·KST·text_path·사업보고서 sha256(원본 zip %d개 다시 계산)·모든 행 출처·정정판 모두 목록에' % (len(drows), nsha))

# 원문 md: 머리 출처 줄
for fn in sorted(os.listdir(MDDIR)):
    if not fn.endswith('.md'):
        fail('원문/G 에 md 아닌 파일 %s' % fn)
        continue
    if not any(fn.startswith(c + '__') for c in CORPS):
        continue
    t = open(os.path.join(MDDIR, fn), encoding='utf-8').read(3000)
    if '출처' not in t:
        fail('원문 md %s 머리에 출처 줄 없음' % fn)
checks.append('(b) 원문/G md: md 만 있음·머리 출처 줄')

# ------------------------------------------------------------------ (h) 비밀·원본
key = os.environ.get('DART_API_KEY', '')
scan = [G, CHK, DOCS, os.path.abspath(__file__), os.path.join(ROOT, 'scripts', 'dart', 'ops15b_G_g2.py')]
scan += [os.path.join(MDDIR, fn) for fn in os.listdir(MDDIR) if any(fn.startswith(c + '__') for c in CORPS)]
for p in scan:
    if not os.path.exists(p):
        continue
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    if key and key in t:
        fail('비밀 값이 %s 에 있음' % os.path.basename(p))
    if re.search(r'(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])', t):
        fail('40자리 16진 토큰이 %s 에 있음' % os.path.basename(p))
    if re.search(r'crtfc_key\s*=\s*[0-9A-Za-z]{8,}', t):
        fail('crtfc_key 값이 %s 에 있음' % os.path.basename(p))
try:
    ign = [subprocess.run(['git', 'check-ignore', '-q', q], cwd=ROOT).returncode for q in ('dart_out/raw/x.zip', 'dart_out/text/x.md')]
    if any(ign):
        fail('dart_out/raw·dart_out/text 가 git 무시 경로가 아님')
    tracked = subprocess.run(['git', 'ls-files', '--', 'dart_out/ops15/원문/G', 'dart_out/ops15/조각'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
    untracked = subprocess.run(['git', 'ls-files', '-o', '--exclude-standard', '--', 'dart_out/ops15/원문/G', 'dart_out/ops15/조각'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
    for p in tracked + untracked:
        if re.search(r'\.(pdf|zip|xml|png|jpg|gz)$', p, re.I):
            fail('git 추적·추적 가능 경로에 원본 %s' % p)
except Exception as e:
    fail('git 확인 실패 %s' % e)
checks.append('(h) 비밀(DART_API_KEY 값·40자리 16진·crtfc_key) 없음(산출·스크립트·원문 md %d개), 원문/G·조각 에 PDF·zip·XML·그림 없음, dart_out/raw·text git 무시' % len(scan))

# ------------------------------------------------------------------ 결과
lines = ['verify15b_G_g2 — G_g2 %d행(source_text 문서에 없음 %d, basis_text %d, counterparty %d, direction %d, amount_krw %d), 확인 %d행, 문서목록 %d행' % (
    len(rows), nnone['source_text'], nnone['basis_text'], nnone['counterparty'], nnone['direction'], nnone['amount_krw'], len(crows), len(drows))]
lines += ['CHECK ' + c for c in checks]
lines += ['SAMPLE ' + s for s in samples[::max(1, len(samples) // 40)][:45]]
lines += ['FAIL ' + x for x in fails]
lines.append('RESULT %s (실패 %d)' % ('PASS' if not fails else 'FAIL', len(fails)))
open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join([lines[0]] + [l for l in lines if l.startswith('FAIL')][:40] + [lines[-1]]))
sys.exit(0 if not fails else 1)
