#!/usr/bin/env python3
"""ops15b 작업 G(원문_지주돈흐름) 그룹 g2 — 메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주, FY2019~FY2025.

정본 요청: dart_out/ops15/REQUEST15b.md, 공통 규칙: dart_out/ops15/COMMON15.md·COMMON15b.md.
새로 받는 문서 없음(OpenDART·웹 호출 0) — 이미 있는 글만 씀:
  사업보고서 md  dart_out/text/ops15/사업보고서__<회사>__FY<fy>__<rcept>.md (목록 dart_out/ops15/사업보고서_원문.csv)
  연차보고서 FY2019~2023  dart_out/text/ops15/연차보고서__<회사>__<공시연도>__<유형>.md (목록 dart_out/ops15/연차보고서15_목록_g2.csv)
  연차보고서 FY2024·2025  dart_out/ops15/kit56/연차보고서_섹션.csv (6차 섹션 글; 쪽 확인은 gov_old 가 다시 받은 dart_out/text/ops15b/연차보고서__<회사>__FY<fy>.md)
  FY2025 iM·메리츠·한국투자 사업보고서 PDF 쪽: handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip

산출(네 소유만): dart_out/ops15/조각/G_g2.csv, dart_out/ops15/원문/G/<회사>__FY<fy>__<문서>.md,
  dart_out/ops15/문서목록15b_G_g2.csv  (확인_G_g2.csv 는 이 스크립트 끝 부분에서 씀)

기계 규칙(사용자 요청 (1)~(3)):
 (1) 별도재무제표 주석(사업보고서 Ⅲ 「5. 재무제표 주석」 — 연결 아님)의 「특수관계자」 주석에서
     손익 거래 표(수익·비용 표)의 행마다 counterparty × item_kind(열 또는 행 머리 그대로) × 당기 금액 1행.
     - 전기 열·전기 표는 넣지 않음. 0·「-」·빈 칸은 넣지 않음. 합계·소계 행은 넣지 않음(상대방이 아님).
     - 자금거래(예치·회수·출자·대여)·채권채무 잔액·지급보증·미사용약정·특수관계자 목록 표는 손익 거래가 아니므로 넣지 않음.
     - 주요 경영진 보상 표(같은 특수관계자 주석 안)의 행도 넣음(자회사가 아닌 특수관계자 — 원문 그대로).
     - BNK 의 「(5) 당기 중 특수관계자와 관련하여 지급한 리스료는 총 …」 문단도 1행(상대방 이름 없음 → counterparty 「문서에 없음」).
     - 별도 주석 「순수수료손익」 표에 브랜드·경영자문 수수료 행이 따로 있는 회사(BNK 「브랜드수수료」, JB 「브랜드사용수수료」·「경영자문수수료」)는
       그 행도 1행(그 표에 상대방 칸이 없음 → counterparty 「문서에 없음」).
     - 배당: 특수관계자 거래 표에 배당 열·행이 있으면 그것(메리츠·JB·iM·한국투자·BNK FY2024~). BNK FY2019~2023 은 표에 배당 열이 없고
       별도 주석 안에 종속기업별 배당금수익 표·문단도 없음 → 배당 행 없음(그 해 행 note 에 적음).
     direction: 표 머리로 기계적으로 —
       가로 표(BNK·메리츠·한국투자 FY2025): 열 머리 묶음 「수익거래」「수 익」 아래 열 → 지주 수입, 「비용거래」「비 용」 아래 열 → 지주 지출.
         열 묶음 칸 합침이 md 에 없으므로 열 이름 끝말(…수익/…이익 = 수익 쪽, …비용/임차료/…손실/…전입/…상각비/…운용비 = 비용 쪽)로 묶음을 맞춤.
         BNK 「유형자산 취득」「유무형자산취득」 열은 수익·비용 묶음 밖 → (판단) 지주 지출(자산 취득 대가).
         한국투자 FY2025 「금융자산평가손익」처럼 「손익」 열은 (판단) 원문 숫자 부호로(양수 수입, 괄호 음수 지출).
       세로 표 iM: 표 안 「<수익>」「<비용>」 머리 아래 행 → 수입/지출.
       세로 표 JB(표 제목 「…중요한 수익, 비용」): 계정과목 이름 끝말로(위 규칙).
       세로 표 한국투자 FY2019~2024: 당기 「수 익」 칸 → 지주 수입, 당기 「비 용」 칸 → 지주 지출(칸 기준, 계정 이름과 무관).
       주요 경영진 보상 표: 표 머리에 수익·비용 구분 없음 → (판단) 지주 지출.
     amount_krw: 원문 숫자 × 원문 단위(표 앞 「(단위: …)」), 원 단위 정수. 괄호 숫자는 원문대로 음수. note 에 「원문 단위 …, 원문 숫자 …」.
     source_text: md 의 그 표 행 한 줄(「| … |」) 그대로. 칸 합침으로 상대방이 위 행에 있으면 note 에 적음. 열 머리는 note 「열: …」.
 (2) 사업보고서 Ⅱ(사업의 내용)에서 상표권·브랜드 사용료 산정 기준 문단을 찾음(「상표」「브랜드」「사용료」) — 5개사·7개년 모두 없음.
     → 브랜드 수익 행(BNK·JB)의 basis_text 「문서에 없음」, 브랜드 수익 행이 없는 회사·해(iM·메리츠·한국투자)는 item_kind 「(산정 기준 문단)」 1행(「문서에 없음」).
     그 밖의 행 basis_text 도 「문서에 없음」(note 에 찾은 범위).
 (2-1) Ⅱ 「영업수익 구성」(검증 때 빠짐으로 찾아 더함): Ⅱ 표 밖 글의 지주(당사) 「주(요)수익원」「주수입원」 + 「배당」 문단 1행
     (item_kind 원문 낱말 배당수익/배당금수익/배당금, counterparty 원문 「자회사」, amount_krw 문서에 없음(판단 — 금액 여럿)),
     이어지는 자회사별 「(현금)배당」 문단은 그 자회사 1행씩((판단) 지주 수입). 걸린 것이 없는 해는 「(영업수익 구성 문단)」 문서에 없음 1행. 규칙은 rev_rows().
 (3) 연차보고서에서 겸직 임원 보수 지급 회사·배분 기준 문단 → item_kind 「(겸직 임원 보수 지급·배분 기준)」. 문단이 없는 회사·해는 「문서에 없음」 1행.
     direction: 원문이 지주 보수정책·지주 보수표 안의 지급을 말하면 (판단) 지주 지출, 그 밖(「원소속회사에서 선지급」 등)은 「문서에 없음」.
 기능 분류·이유 추정 없음. DART_API_KEY 안 씀.
"""
import csv, os, re, sys, zipfile, datetime, hashlib, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OPS = os.path.join(ROOT, 'dart_out', 'ops15')
OUT_CSV = os.path.join(OPS, '조각', 'G_g2.csv')
OUT_MD_DIR = os.path.join(OPS, '원문', 'G')
OUT_DOCS = os.path.join(OPS, '문서목록15b_G_g2.csv')
CORPS = ['메리츠금융지주', 'iM금융지주', 'BNK금융지주', 'JB금융지주', '한국투자금융지주']
FYS = list(range(2019, 2026))
COLS = ['corp_label', 'fy', 'item_kind', 'counterparty', 'direction', 'amount_krw', 'basis_text', 'doc_kind',
        'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
NONE = '문서에 없음'
UNIT = {'천원': 1000, '백만원': 1000000, '원': 1}
csv.field_size_limit(10 ** 9)


def rel(p):
    return os.path.join(ROOT, p)


def norm(s):
    return re.sub(r'\s+', '', s.replace('<br>', '').replace('|', ''))


def cells(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


NUMRE = re.compile(r'^\(?-?[\d,]+\)?$')


def numtxt(c):
    """칸 글 → (원문 숫자 글, 정수) 또는 None(빈칸·-·0)."""
    t = c.replace('<br>', '').replace(' ', '').strip()
    if t in ('', '-', '－', '0', '(0)'):
        return None
    if not NUMRE.match(t):
        raise ValueError('숫자 아님: %r' % c)
    neg = t.startswith('(') or t.startswith('-')
    v = int(t.strip('()-').replace(',', ''))
    if v == 0:
        return None
    return t, (-v if neg else v)


def is_numlike(c):
    t = c.replace('<br>', '').replace(' ', '').strip()
    return t in ('', '-', '－') or bool(NUMRE.match(t))


def is_sum(label):
    x = re.sub(r'\s+', '', label)
    return x in ('합계', '소계', '총계')


def clean_name(s):
    return re.sub(r'\s+', ' ', s.replace('&cr;', ' ').replace('<br>', ' ')).strip()


INC = re.compile(r'(수익|이익)$')
EXP = re.compile(r'(비용|임차료|관리비|손실|전입|상각비|운용비|급여)$')


def strip_fn(s):
    return re.sub(r'\((\*\d*|주\d+|\*)\)', '', s).replace(', 특수관계자거래', '').strip()


def dir_by_name(name):
    n = strip_fn(clean_name(name))
    if INC.search(n):
        return '지주 수입', False
    if EXP.search(n):
        return '지주 지출', False
    return None, True


def kst(ts):
    if ts.endswith('+0000'):
        d = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S+0000') + datetime.timedelta(hours=9)
        return d.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    return ts


# ---------------------------------------------------------------- 입력 목록
def load_reports():
    rep = {}
    cor = {}
    for r in csv.DictReader(open(os.path.join(OPS, '사업보고서_원문.csv'), encoding='utf-8-sig')):
        if r['label'] not in CORPS:
            continue
        k = (r['label'], int(r['fy']))
        if r['kind'] == '본':
            rep[k] = r
        else:
            cor.setdefault(k, []).append(r)
    return rep, cor


_cache = {}


def read_lines(p):
    if p not in _cache:
        _cache[p] = open(rel(p), encoding='utf-8').read().split('\n')
    return _cache[p]


def sections(L):
    return [i for i, l in enumerate(L) if l.startswith('### [절')]


def sep_range(L):
    secs = sections(L)
    st = [i for i in secs if re.search(r'\] *\d+\. *재무제표 주석', L[i])][0]
    en = [i for i in secs if i > st and re.search(r'\] *(6\. *(배당|기타)|[IVX]+\.)', L[i])][0]
    return st, en


def sec_of(L, i):
    j = i
    while j >= 0 and not L[j].startswith('### [절'):
        j -= 1
    m = re.match(r'### \[절 (\d+)\] *(.*)$', L[j])
    return int(m.group(1)), m.group(2).strip(), j


def table_of(L, i):
    j = i
    while j >= 0 and not re.match(r'^\[표 \d+\]$', L[j].strip()):
        j -= 1
    return int(re.findall(r'\d+', L[j])[0]), j


def table_lines(L, start):
    """start = '[표 n]' 줄 → [(i, line)] 표 끝 전까지."""
    assert re.match(r'^\[표 \d+\]$', L[start].strip()), L[start][:50]
    out = []
    i = start + 1
    while L[i].strip() != '[표 끝]':
        out.append((i, L[i]))
        i += 1
    return out, i


def next_table(L, i, lim=40):
    for j in range(i, min(len(L), i + lim)):
        if re.match(r'^\[표 \d+\]$', L[j].strip()):
            return j
    raise RuntimeError('표 없음 %d' % i)


def unit_near(L, i, back=14):
    for j in range(i, max(0, i - back), -1):
        m = re.search(r'단위\s*[:：]?\s*(천원|백만원|원)', L[j])
        if m:
            return m.group(1)
    raise RuntimeError('단위 없음 %d %s' % (i, L[i][:60]))


def rp_region(L, st, en):
    hs = [i for i in range(st, en) if re.search(r'^\s*(&cr;)*\s*(### \[절 \d+\] )?\d+\.\s*특수관계자', L[i])]
    h = hs[0]
    N = int(re.search(r'(\d+)\.\s*특수관계자', L[h]).group(1))
    e = h + 1
    while e < en:
        if re.match(r'^\s*(&cr;)*\s*(### \[절 \d+\] )?(&cr;)*\s*%d\.\s*\S' % (N + 1), L[e]):
            break
        e += 1
    head = re.sub(r'^\s*(&cr;)*\s*(### \[절 \d+\] )?', '', L[h])
    head = re.split(r'&cr;|당사는|\(1\)|\s\d+-1\s', head)[0].strip()
    return h, e, head[:40]


# ---------------------------------------------------------------- 13차 PDF 쪽(FY2025, iM·메리츠·한국투자)
_pdf = {}


def pdf_pages(label):
    if label in _pdf:
        return _pdf[label]
    z = zipfile.ZipFile(rel('handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip'))
    name = '13차_지주관리유형/텍스트/사업보고서__%s.md' % label
    pages = []
    if name in z.namelist():
        t = z.read(name).decode('utf-8')
        for m in re.finditer(r'## p\.(\d+)\n(.*?)(?=\n## p\.\d+\n|\Z)', t, re.S):
            pages.append((int(m.group(1)), norm(m.group(2))))
    _pdf[label] = pages
    return pages


def pdf_page(label, needles):
    for kind, nd in needles:
        n = norm(nd)
        if len(n) < 6:
            continue
        hits = [p for p, t in pdf_pages(label) if n in t]
        if hits:
            return 'p.%d(본문 PDF, 13차 보관%s)' % (hits[0], '' if kind == 'row' else ' — ' + kind)
    return ''


# ---------------------------------------------------------------- 행 만들기
class Ctx:
    def __init__(self, label, fy, rep, cors):
        self.label, self.fy, self.rep, self.cors = label, fy, rep, cors
        self.L = read_lines(rep['text_path'])
        self.st, self.en = sep_range(self.L)
        self.h, self.e, self.head = rp_region(self.L, self.st, self.en)
        n, t, _ = sec_of(self.L, self.h)
        self.secno, self.sectitle = n, t
        self.section_title = 'XML [절 %d] 「%s」 > 주석 「%s」' % (n, t, self.head)
        self.md_blocks = {}  # (from,to) -> title
        self.md_blocks[(self.h, self.e)] = 'XML [절 %d] 「%s」 중 주석 「%s」 (md %d~%d줄)' % (n, t, self.head, self.h + 1, self.e)

    def page(self, i, table=True):
        n, t, _ = sec_of(self.L, i)
        p = 'XML [절 %d] 「%s」' % (n, t)
        if table:
            p += ' [표 %d]' % table_of(self.L, i)[0]
        return p

    def row(self, i, item, cp, direction, num, unit, note, basis_note=None, section_title=None, source=None, pdf_needles=None):
        src = source if source is not None else self.L[i].strip()
        if num is not None:
            t, v = num
            amt = str(v * UNIT[unit])
            note = '원문 단위 %s, 원문 숫자 %s / %s' % (unit, t, note)
        else:
            amt = NONE
        page = self.page(i, table=src.startswith('|'))
        if self.fy == 2025 and self.label in ('iM금융지주', '메리츠금융지주', '한국투자금융지주'):
            pp = pdf_page(self.label, [('row', src)] + (pdf_needles or []))
            page += (' / ' + pp) if pp else ''
            if not pp:
                note += ' / 13차 본문 PDF 글에서 쪽을 찾지 못함'
        bn = basis_note or ('basis_text 문서에 없음(찾은 범위: 이 사업보고서 Ⅱ·별도 주석 「상표」「브랜드」「사용료」 — 산정 기준 문단 없음)')
        return dict(corp_label=self.label, fy=str(self.fy), item_kind=item, counterparty=cp, direction=direction,
                    amount_krw=amt, basis_text=NONE, doc_kind='사업보고서', section_title=section_title or self.section_title,
                    source_text=src, rcept_no_or_url=self.rep['rcept_no'], page=page,
                    note=note + ' / ' + bn, doc_name=self.rep['report_nm'], collected_at=self.rep['fetched_at'])


def find_line(L, a, b, rx):
    for i in range(a, b):
        if re.search(rx, L[i]):
            return i
    return None


def footnotes_after(L, tend):
    """표 끝 바로 뒤(빈 표·각주 표·각주 줄)의 「(*n)」「(주n)」 각주 원문."""
    fn = {}
    k = tend + 1
    for _ in range(10):
        if k >= len(L):
            break
        s = L[k].strip()
        if re.match(r'^\[표 \d+\]$', s) or s == '[표 끝]' or not s or s in ('|  |', '&cr;'):
            k += 1
            continue
        t = s.strip('|').strip()
        m = re.match(r'^(&cr;)?\s*\((\*\d*|주\d+)\)', t)
        if m:
            fn.setdefault('(' + m.group(2) + ')', clean_name(t.replace('&cr;', ' ')))
            k += 1
            continue
        break
    return fn


def apply_fn(rows, fn):
    for r in rows:
        for mk in re.findall(r'\((\*\d*|주\d+)\)', r['item_kind'] + ' ' + r['counterparty']):
            t = fn.get('(' + mk + ')')
            if t:
                r['note'] += ' / 표 아래 각주 원문: ' + t[:300]
    return rows


def parse_wide(cx, tstart, leaves, nlead, unit, colpath):
    """가로 표. leaves=[(item, dir, judged)] — 당기 값 열 순서. nlead = 첫 행의 머리 칸 수(구분+이름=2, 3)."""
    L = cx.L
    tl, tend = table_lines(L, tstart)
    N = len(leaves)
    out = []
    cat = None
    ndata = 0
    for i, line in tl:
        c = cells(line)
        if len(c) == nlead + N:
            lab, vals = c[:nlead], c[nlead:]
        elif len(c) == 1 + N:
            lab, vals = c[:1], c[1:]
        else:
            continue
        if not all(is_numlike(v) for v in vals):
            continue  # 머리 행
        ndata += 1
        name = lab[-1]
        carried = False
        if len(lab) > 1:
            cat = lab[-2]
        else:
            carried = True
        if is_sum(name):
            continue
        for (item, d, judged, path), v in zip(leaves, vals):
            n = numtxt(v)
            if n is None:
                continue
            note = '열: %s' % path
            if cat:
                note += ' / 구분 「%s」%s' % (clean_name(cat), '(칸 합침 — 위 행 구분을 이어 봄)' if carried else '')
            if d == 'SIGN':
                d = '지주 수입' if n[1] > 0 else '지주 지출'
                note += ' / (판단) 「손익」 열 — 원문 숫자 부호로 방향을 정함'
            elif judged:
                note += ' / (판단) ' + judged
            else:
                note += ' / 방향: 표 머리 묶음(%s)' % ('수익 쪽' if d == '지주 수입' else '비용 쪽')
            out.append(cx.row(i, item, clean_name(name), d, n, unit, note, pdf_needles=[('표 머리 문단 쪽', L[cx.anchor])] if hasattr(cx, 'anchor') else None))
    assert ndata >= 2, ('data rows', cx.label, cx.fy, ndata)
    return apply_fn(out, footnotes_after(L, tend))


def bnk(cx):
    L = cx.L
    a = find_line(L, cx.h, cx.e, r'특수관계자와의 중요 거래내용')
    cx.anchor = a
    t = a
    while True:
        t = next_table(L, t + 1)
        if '당기' in L[t + 1] and '단위' not in L[t + 1]:
            break
    unit = unit_near(L, t)
    h1, h2 = cells(L[t + 2]), cells(L[t + 3])
    assert h1[0] == '수익거래' and h1[1] == '비용거래', h1
    asset = clean_name(h1[2])
    leaves = []
    for x in h2:
        d, amb = dir_by_name(x)
        assert not amb, x
        leaves.append((x, d, None, '당기 > %s > %s' % ('수익거래' if d == '지주 수입' else '비용거래', x)))
    leaves.append((asset, '지주 지출', '열 「%s」 은 수익거래·비용거래 묶음 밖 — 자산 취득 대가로 보아 지주 지출' % asset, '당기 > %s' % asset))
    rows = parse_wide(cx, t, leaves, 2, unit, None)
    hasdiv = any('배당' in l[0] for l in leaves)
    fn = [clean_name(c) for i, l in table_lines(L, next_table(L, t + 1))[0] for c in cells(l) if c.startswith('(*)')]
    for r in rows:
        if not hasdiv:
            r['note'] += ' / 이 해 표에 배당금수익 열 없음, 별도 주석 안에 종속기업별 배당금수익 표·문단도 없음(찾은 범위: 별도 주석 전체 「배당」)'
        if fn and '투자증권' in r['counterparty'] and r['item_kind'] == '기타수익':
            r['note'] += ' / 표 아래 각주 원문: ' + fn[0]
    # 리스료 문단
    i = find_line(L, cx.h, cx.e, r'지급한 리스료는')
    j = i
    while '입니다' not in L[j]:
        j += 1
    src = ' '.join(x.strip() for x in L[i:j + 1] if x.strip())
    m = re.search(r'총\s*([\d,]+)\s*(천원|원)', src)
    note = '원문 문단 — 상대방 회사 이름 없음(원문 「특수관계자와 관련하여」) / 방향: 원문 「지급한」'
    if m.group(2) == '원':
        note += ' / 원문 글 단위가 「원」(같은 문단 전기 금액은 「천원」) — 원문대로 원으로 옮김'
    rows.append(cx.row(i, '리스료', NONE, '지주 지출', (m.group(1), int(m.group(1).replace(',', ''))), m.group(2), note, source=src))
    rows += key_mgmt(cx)
    rows += fee_note(cx, r'^\|\s*브랜드수수료\s*\|')
    return rows


def key_mgmt(cx, special=False):
    L = cx.L
    a = find_line(L, cx.h, cx.e, r'주요 ?경영진(과의|에 대한)')
    t = next_table(L, a + 1)
    if '단위' in L[t + 1] and len(cells(L[t + 1])) == 1 and L[t + 2].strip() == '[표 끝]':
        t2 = next_table(L, t + 1)
    else:
        t2 = t
    unit = unit_near(L, t2 + 2)
    tl, _ = table_lines(L, t2)
    head = [c for i, l in tl[:2] for c in cells(l)]
    hj = ' '.join(head)
    assert re.search(r'당', hj) and hj.find('당') < hj.find('전'), hj
    cp = re.search(r'주요 ?경영진', L[a]).group(0)
    out = []
    for i, line in tl:
        c = cells(line)
        if len(c) != 3 or not is_numlike(c[1]) or not is_numlike(c[2]):
            continue
        if is_sum(c[0]):
            continue
        n = numtxt(c[1])
        if n is None:
            continue
        out.append(cx.row(i, c[0], cp, '지주 지출', n, unit,
                          '열: 당기 / 주요 경영진 보상 표(머리 문단 원문: %s) / (판단) 표 머리에 수익·비용 구분 없음 — 보상으로 보아 지주 지출' % clean_name(L[a])[:80],
                          pdf_needles=[('표 머리 문단 쪽', L[a])]))
    assert out, ('key mgmt', cx.label, cx.fy)
    return apply_fn(out, footnotes_after(L, table_lines(L, t2)[1]))


def fee_note(cx, rx):
    """별도 주석 「순수수료손익」 표의 브랜드·경영자문 행(첫 해 주석 안 첫 것)."""
    L = cx.L
    out = []
    i0 = find_line(L, cx.st, cx.en, rx)
    if i0 is None:
        raise RuntimeError('fee row 없음 %s %s' % (cx.label, cx.fy))
    t = table_of(L, i0)[1]
    tl, tend = table_lines(L, t)
    hdr = cells(tl[0][1])
    assert hdr[-2].replace(' ', '') == '당기' and hdr[-1].replace(' ', '') == '전기', hdr
    unit = unit_near(L, t)
    # 주석 머리
    j = t
    while j > t - 8 and not re.match(r'^\s*(&cr;)*\s*\d+\.\s*\S', L[j]):
        j -= 1
    nh = re.split(r'당기|&cr;', ''.join(L[j:t]).strip())[0]
    nh = clean_name(nh)[:30]
    n, tt, _ = sec_of(L, i0)
    sect = 'XML [절 %d] 「%s」 > 주석 「%s」' % (n, tt, nh)
    j2 = j
    # 그 주석 표까지 원문 md 블록
    cx.md_blocks[(j, tend + 1)] = 'XML [절 %d] 「%s」 중 주석 「%s」 (md %d~%d줄)' % (n, tt, nh, j + 1, tend + 1)
    for i, line in tl:
        c = cells(line)
        if len(c) < 3:
            continue
        nm = c[-3]
        if not re.search(r'브랜드|상표|경영자문|경영관리|용역', nm):
            continue
        num = numtxt(c[-2])
        if num is None:
            continue
        note = '열: 당기 / 별도 주석 「%s」 표의 「수수료수익」 아래 행 — 이 표에는 상대방(회사) 칸 없음 / 방향: 「수수료수익」 아래 행' % nh
        out.append(cx.row(i, nm, NONE, '지주 수입', num, unit, note, section_title=sect,
                          basis_note='basis_text 문서에 없음(찾은 범위: 이 사업보고서 전체 「상표」「브랜드」「사용료」 — Ⅱ 「사업의 내용」·별도 주석·그 밖의 절에 사용료 산정 기준(요율·기준 수익) 문단 없음)'))
    return out


def meritz(cx):
    L = cx.L
    a = find_line(L, cx.h, cx.e, r'주요 거래내용은')
    cx.anchor = a
    t = next_table(L, a + 1)
    assert '<당기>' in L[t + 1], L[t + 1]
    unit = unit_near(L, t + 1)
    t2 = next_table(L, t + 1)
    h1, h2 = cells(L[t2 + 1]), cells(L[t2 + 2])
    assert re.sub(r'\s', '', h1[2]) == '수익' and re.sub(r'\s', '', h1[3]) == '비용', h1
    leaves = []
    for x in h2:
        d, amb = dir_by_name(x)
        assert not amb, x
        leaves.append((x, d, None, '<당기> > %s > %s' % ('수 익' if d == '지주 수입' else '비 용', x)))
    rows = parse_wide(cx, t2, leaves, 2, unit, None)
    rows += key_mgmt(cx)
    return rows


def vertical(cx, mode):
    """JB·iM 세로 표: 특수관계자 | 계정과목 | 당기 | 전기."""
    L = cx.L
    if mode == 'JB':
        a = find_line(L, cx.h, cx.e, r'특수관계자와의 거래에서 발생한')
    else:
        a = find_line(L, cx.h, cx.e, r'특수관계자와의 거래내역')
    cx.anchor = a
    t = next_table(L, a + 1)
    tl, tend = table_lines(L, t)
    if not any('계정과목' in l for i, l in tl):
        t = next_table(L, t + 1)
        tl, tend = table_lines(L, t)
    unit = unit_near(L, t + 1)
    hi = [k for k, (i, l) in enumerate(tl) if '계정과목' in l][0]
    hdr = cells(tl[hi][1])
    assert ('당' in hdr[2]) and ('전' in hdr[3]), hdr
    out = []
    cp = None
    sect = None
    nd = 0
    for i, line in tl[hi + 1:]:
        c = cells(line)
        if len(c) == 1:
            if re.sub(r'\s', '', c[0]) in ('<수익>', '<비용>'):
                sect = re.sub(r'\s', '', c[0])
            continue
        if len(c) == 4:
            cp, acct, v = c[0], c[1], c[2]
            carried = False
        elif len(c) == 3:
            acct, v = c[0], c[1]
            carried = True
        else:
            raise RuntimeError('칸 수 %d %s' % (len(c), line))
        if not is_numlike(v):
            raise RuntimeError('숫자 아님 %s' % line)
        nd += 1
        if is_sum(acct) or is_sum(cp):
            continue
        n = numtxt(v)
        if n is None:
            continue
        note = '열: %s' % hdr[2]
        if carried:
            note += ' / 상대방은 위 행 「%s」(칸 합침)' % clean_name(cp)
        if mode == 'iM':
            assert sect, line
            d = '지주 수입' if sect == '<수익>' else '지주 지출'
            note += ' / 방향: 표 안 머리 「%s」 아래 행' % sect
        else:
            d, amb = dir_by_name(acct)
            if amb:
                raise RuntimeError('방향 애매 %s' % acct)
            note += ' / 방향: 표 제목 「중요한 수익, 비용」 — 계정과목 이름 끝말(%s)' % ('수익/이익' if d == '지주 수입' else '비용 쪽')
        out.append(cx.row(i, acct, clean_name(cp), d, n, unit, note, pdf_needles=[('표 머리 문단 쪽', L[a])]))
    assert nd >= 3
    apply_fn(out, footnotes_after(L, tend))
    out += key_mgmt(cx)
    if mode == 'JB':
        out += fee_note(cx, r'^\|\s*(수수료수익\s*\|\s*)?(경영자문수수료|브랜드사용수수료)\s*\|')
    return out


def kis_old(cx):
    L = cx.L
    a = find_line(L, cx.h, cx.e, r'\(2\) 당기와 전기 중 발생한 특수관계자와의')
    cx.anchor = a
    t = next_table(L, a + 1)
    tl, tend = table_lines(L, t)
    unit = unit_near(L, t + 2)
    hdr = cells(tl[1][1])
    assert '당' in hdr[3] and '전' in hdr[4], hdr
    h2 = [re.sub(r'\s', '', x) for x in cells(tl[2][1])]
    assert h2 == ['수익', '비용', '수익', '비용'], h2
    out = []
    cat = cp = None
    for i, line in tl[3:]:
        c = cells(line)
        if len(c) == 7:
            cat, cp, acct, vals = c[0], c[1], c[2], c[3:]
            carried_cp = carried_cat = False
        elif len(c) == 6:
            cp, acct, vals = c[0], c[1], c[2:]
            carried_cp, carried_cat = False, True
        elif len(c) == 5:
            acct, vals = c[0], c[1:]
            carried_cp = carried_cat = True
        else:
            raise RuntimeError('칸 수 %d %s' % (len(c), line))
        assert all(is_numlike(v) for v in vals), line
        if is_sum(acct):
            continue
        for k, d in ((0, '지주 수입'), (1, '지주 지출')):
            n = numtxt(vals[k])
            if n is None:
                continue
            note = '열: %s > %s' % (hdr[3], '수 익' if k == 0 else '비 용')
            if carried_cp:
                note += ' / 상대방은 위 행 「%s」(칸 합침)' % clean_name(cp)
            note += ' / 구분 「%s」%s' % (clean_name(cat), '(칸 합침 — 위 행 구분을 이어 봄)' if carried_cat else '')
            note += ' / 방향: 당기 「%s」 칸' % ('수 익' if k == 0 else '비 용')
            out.append(cx.row(i, clean_name(acct), clean_name(cp), d, n, unit, note))
    apply_fn(out, footnotes_after(L, tend))
    out += key_mgmt(cx)
    return out


def kis_2025(cx):
    L = cx.L
    a = find_line(L, cx.h, cx.e, r'^\| 특수관계자거래에 대한 공시 \|$')
    cx.anchor = a
    t = None
    for j in range(a, a + 20):
        if re.match(r'^\| 당기 \| \(단위 : 백만원\) \|$', L[j]):
            t = next_table(L, j)
            break
    unit = unit_near(L, t - 2)
    h1, h2 = cells(L[t + 1]), cells(L[t + 2])
    names = h1[3:]
    subs = [x for x in h2[3:] if x]
    leaves = []
    for x in names:
        if x.startswith('수수료비용'):
            for s in subs:
                leaves.append((s, '지주 지출', None, '당기 > %s > %s' % (x, s)))
            continue
        if strip_fn(x).endswith('손익'):
            leaves.append((x, 'SIGN', None, '당기 > %s' % x))
            continue
        d, amb = dir_by_name(x)
        assert not amb, x
        leaves.append((x, d, None, '당기 > %s' % x))
    assert len(leaves) == 14, len(leaves)
    rows = parse_wide(cx, t, leaves, 3, unit, None)
    for r in rows:
        if r['direction'] == '지주 지출' and '수수료비용' in r['note'] and '방향' in r['note']:
            pass
    # 주요 경영진(XBRL 꼴 표)
    a2 = find_line(L, cx.h, cx.e, r'^\| 주요 경영진에 대한 보상 \|$')
    j = a2
    while not re.match(r'^\| 당기 \| \(단위 : 백만원\) \|$', L[j]):
        j += 1
    unit2 = unit_near(L, j)
    t2 = next_table(L, j)
    tl, _ = table_lines(L, t2)
    hd = [cells(l)[1] for i, l in tl if len(cells(l)) == 2 and cells(l)[0] == '']
    cp = [x for x in hd if '주요 경영진' in x][0]
    path = ' > '.join(hd)
    for i, line in tl[1:]:
        c = cells(line)
        if len(c) == 2 and is_numlike(c[1]) and not is_sum(c[0]):
            n = numtxt(c[1])
            if n is None:
                continue
            rows.append(cx.row(i, c[0], cp, '지주 지출', n, unit2,
                               '열: 당기 > %s / 주요 경영진 보상 표 / (판단) 표 머리에 수익·비용 구분 없음 — 보상으로 보아 지주 지출' % path))
    return rows


def no_basis_row(cx):
    """iM·메리츠·한국투자: 브랜드 수익 행 없음 → (산정 기준 문단) 문서에 없음 1행."""
    secs = sections(cx.L)
    st2 = [i for i in secs if re.search(r'\] *(II|Ⅱ)\. *사업의 내용', cx.L[i])][0]
    n, t, _ = sec_of(cx.L, st2)
    hit, seen = [], set()
    for i in range(cx.st, cx.en):
        l = cx.L[i]
        if not l.startswith('|'):
            continue
        lab = tuple(c for c in cells(l) if re.search(r'상표권\s*사용|상표권사용|브랜드', c))
        if lab and lab not in seen and any(numtxt(c) for c in cells(l) if is_numlike(c)):
            seen.add(lab)
            n2, t2, _ = sec_of(cx.L, i)
            hit.append('별도 주석 md %d줄 표 행 「%s」(XML [절 %d] 「%s」 [표 %d]) 있음 — 표 행이고 산정 기준 문단 아님' % (i + 1, l.strip(), n2, t2, table_of(cx.L, i)[0]))
    return dict(corp_label=cx.label, fy=str(cx.fy), item_kind='(산정 기준 문단)', counterparty=NONE, direction=NONE,
                amount_krw=NONE, basis_text=NONE, doc_kind='사업보고서', section_title='XML [절 %d] 「%s」' % (n, t),
                source_text=NONE, rcept_no_or_url=cx.rep['rcept_no'], page='XML [절 %d] 「%s」 이하 Ⅱ 전체' % (n, t),
                note='문서에 없음 — 찾은 범위: 이 사업보고서 Ⅱ 「사업의 내용」 전체와 Ⅲ 별도 재무제표 주석 전체에서 「상표」「브랜드」「사용료」(상표권 자산 표 행 제외) — 상표권·브랜드 사용료 산정 기준 문단 없음. 이 해 별도 주석 특수관계자 거래 표·수수료손익 주석에도 상표권·브랜드 수익 열·행 없음' + ''.join('. ' + h for h in hit),
                doc_name=cx.rep['report_nm'], collected_at=cx.rep['fetched_at'])


REV_RX = re.compile(r'주요?수[익입]원')
REV_SKIP = ('|', '### ', '[표')
SUBJ_RX = re.compile(r'^\s*(.+?(?:은행|캐피탈|자산운용|인베스트먼트|증권)(?:\(주\))?)(?:은|는|\s또한)[\s,]')


def _ends(x):
    y = re.sub(r'(&cr;|\s)+$', '', x)
    return y.endswith('.') and not re.search(r'\d\.$', y)


def _block_end(L, i, b):
    en = i
    while not _ends(L[en]) and en + 1 < b and en - i < 400 and not L[en + 1].startswith(REV_SKIP):
        en += 1
    while not L[en].strip():
        en -= 1
    return en


def _md_sec(cx, i, what):
    """원문 md 에 실을 범위: 그 절 전체(4만 자 이하) 또는 절이 크면 걸린 문단 앞뒤 30줄(같은 절 안)."""
    n, t, h = sec_of(cx.L, i)
    e = h + 1
    while e < len(cx.L) and not cx.L[e].startswith('### [절'):
        e += 1
    if len('\n'.join(cx.L[h:e])) <= 40000:
        cx.md_blocks[(h, e)] = 'XML [절 %d] 「%s」 전체 (md %d~%d줄) — %s' % (n, t, h + 1, e, what)
    else:
        a, b = max(h, i - 30), min(e, cx._blk_end + 31)
        for k in [k for k in cx.md_blocks if k[0] < b and a < k[1] and h <= k[0] < e]:  # 같은 절 안 겹치는 범위는 합침
            a, b = min(a, k[0]), max(b, k[1])
            del cx.md_blocks[k]
        cx.md_blocks[(a, b)] = 'XML [절 %d] 「%s」 중 걸린 문단 앞뒤 30줄 (md %d~%d줄, 절이 4만 자를 넘어 일부) — 지주 수익원 문단(Ⅱ 영업수익 구성)과 이어지는 자회사별 배당 문단' % (n, t, a + 1, b)


def _sentence(src, pos_rx):
    """한 줄이 1,500자 넘으면 걸린 글이 든 문장만(앞 「. 」·「&cr;」 뒤 ~ 다음 「.」) — 원문 글 그대로 이어진 일부."""
    m = pos_rx.search(src)
    if not m or len(src) <= 1500:
        return src, False
    a = max(src.rfind('. ', 0, m.start()) + 2, src.rfind('&cr;', 0, m.start()) + 4, 0)
    e = src.find('.', m.end())
    e = len(src) if e < 0 else e + 1
    return src[a:e].strip(), True


def rev_rows(cx):
    """(2-1) Ⅱ 「사업의 내용」 지주(당사) 영업수익 구성 문단 — 기계 규칙(검증 때 빠짐으로 찾아 더함, 2026-11-03):
    Ⅱ 범위(「II. 사업의 내용」 머리 ~ 「III. 재무에 관한 사항」 머리)의 표 밖 줄에서 공백을 지운 글에 「주(요)수익원」「주(요)수입원」이 있고
    그 앞 40자 안에 「지주」「당사」, 앞 30자~뒤 40자 안에 「배당」이 있으면 그 문단 1행.
    문단 = 그 줄(앞쪽 4자 이하 조각 줄은 붙임) ~ 「.」로 끝나는 줄까지(XML 글이 낱말마다 줄이 바뀐 해는 빈 줄도 건너 이어 봄).
    item_kind 「배당수익」「배당금수익」「배당금」 중 문단에 있는 원문 낱말, counterparty 원문 낱말 「자회사」, direction 지주 수입(원문 「수익원」「수입원」).
    이어지는 줄이 「(현금)배당」 글이면(자회사별 당사 배당 내역) 그 줄마다 1행: item_kind 「(현금)배당」, counterparty 그 줄 첫 주어(「…은/는」「… 또한」 앞 원문),
    direction (판단) 지주 수입. amount_krw: 문단 안 금액이 해·자회사별로 여럿이라 한 칸 금액이 없음 → 「문서에 없음」(판단, 금액은 source_text 원문).
    걸린 것이 없는 해는 item_kind 「(영업수익 구성 문단)」 「문서에 없음」 1행."""
    L = cx.L
    secs = sections(L)
    a = [i for i in secs if re.search(r'\] *(II|Ⅱ)\. *사업의 내용', L[i])][0]
    b = [i for i in secs if i > a and re.search(r'\] *(III|Ⅲ)\. *재무에 관한', L[i])][0]
    rows, used = [], set()
    amt_note = 'amount_krw: (판단) 문단 안 금액이 해·자회사별로 여럿이라 한 칸 금액이 없음 — 금액은 source_text 원문 그대로, 그 해 자회사별 배당 금액은 같은 FY 별도 주석 특수관계자 거래 행'
    bn = 'basis_text 문서에 없음(이 행은 영업수익 구성 문단 — 산정 기준 문단은 Ⅱ·별도 주석에서 「상표」「브랜드」「사용료」로 찾았으나 없음)'
    for i in range(a + 1, b):
        if i in used or L[i].startswith(REV_SKIP):
            continue
        w = re.sub(r'\s+', '', L[i])
        m = REV_RX.search(w)
        if not m or not re.search(r'지주|당사', w[max(0, m.start() - 40):m.start()]) or '배당' not in w[max(0, m.start() - 30):m.start() + 40]:
            continue
        st = i
        while st - 1 > a and L[st - 1].strip() and len(L[st - 1].strip()) <= 4 and not L[st - 1].startswith(REV_SKIP):
            st -= 1
        en = _block_end(L, i, b)
        used.update(range(st, en + 1))
        src, cut = _sentence('\n'.join(L[st:en + 1]), re.compile(r'주\s*요?\s*수\s*[익입]\s*원'))
        wsrc = re.sub(r'\s+', '', src)
        item = [k for k in ('배당금수익', '배당수익', '배당금') if k in wsrc][0]
        frag = en - st > 3
        n, t, _ = sec_of(L, st)
        sec = 'XML [절 %d] 「%s」' % (n, t)
        lead = re.sub(r'\s+', ' ', L[st].strip())[:30]
        note = ('방향: 원문 「%s」 문단(지주 수익원 서술) / Ⅱ 문단(md %d~%d줄, 첫 글 「%s」)%s%s / %s' % (
            m.group(0), st + 1, en + 1, lead, ' / XML 글이 낱말마다 줄이 바뀜(글 순서 그대로, 공백·줄바꿈만 다름)' if frag else '',
            ' / 한 줄 문단이 1,500자를 넘어 source_text 는 걸린 글이 든 문장만(이어진 원문 일부)' if cut else '', amt_note))
        needle = w[max(0, m.start() - 15):m.start() + 25]
        rows.append(cx.row(st, item, '자회사', '지주 수입', None, None, note, basis_note=bn, section_title=sec, source=src,
                           pdf_needles=[('문단 글 일부', needle)]))
        cx._blk_end = en
        _md_sec(cx, st, '지주 수익원 문단(Ⅱ 영업수익 구성)')
        if frag:
            continue
        j = en + 1
        while j < b and not L[j].startswith(REV_SKIP) and '(현금)배당' in L[j] and SUBJ_RX.match(L[j]) and not REV_RX.search(re.sub(r'\s+', '', L[j])):
            cp = SUBJ_RX.match(L[j]).group(1).strip()
            e2 = _block_end(L, j, b)
            used.update(range(j, e2 + 1))
            sj = '\n'.join(L[j:e2 + 1]).strip()
            rows.append(cx.row(j, '(현금)배당', cp, '지주 수입', None, None,
                               '(판단) 바로 앞 문단(md %d줄 「…%s…」)에 이어 자회사별 배당 내역을 적은 문단(md %d~%d줄) — 지주 수입으로 봄. counterparty 는 문단 첫 주어 원문 / %s' % (
                                   st + 1, m.group(0), j + 1, e2 + 1, amt_note), basis_note=bn, section_title=sec, source=sj,
                               pdf_needles=[('문단 글 일부', re.sub(r'\s+', '', sj)[:40])]))
            cx._blk_end = e2
            _md_sec(cx, j, '지주 수익원 문단에 이어지는 자회사별 배당 문단')
            j = e2 + 1
    if not rows:
        n, t, _ = sec_of(L, a)
        rows.append(dict(corp_label=cx.label, fy=str(cx.fy), item_kind='(영업수익 구성 문단)', counterparty=NONE, direction=NONE,
                         amount_krw=NONE, basis_text=NONE, doc_kind='사업보고서', section_title='XML [절 %d] 「%s」' % (n, t),
                         source_text=NONE, rcept_no_or_url=cx.rep['rcept_no'], page='XML [절 %d] 「%s」 이하 Ⅱ 전체' % (n, t),
                         note='문서에 없음 — 찾은 범위: 이 사업보고서 Ⅱ 「사업의 내용」 전체(md %d~%d줄)의 표 밖 글에서 「수익원」「수입원」「영업수익은」「영업수익의」「수익 구성」「배당수익」「배당금수익」과 앞뒤 40자 안 「당사」「지주」 — 지주(당사) 영업수익 구성 문단 없음' % (a + 1, b),
                         doc_name=cx.rep['report_nm'], collected_at=cx.rep['fetched_at']))
    return rows


def corr_notes(rows, cors):
    for r in rows:
        if r['source_text'] == NONE:
            continue
        add = []
        for c in cors:
            tp = c['text_path']
            if not tp or not os.path.exists(rel(tp)):
                add.append('정정 %s(%s): 정정판 글 없음(OpenDART %s %s) — 대조 못 함' % (c['rcept_no'], c['report_nm'], c['doc_status'], c['doc_message']))
                continue
            T = _ntext(tp)
            if norm(r['source_text']) not in T:
                if norm(r['source_text']).replace('&cr;', '') in T.replace('&cr;', ''):
                    add.append('정정 %s(%s): 같은 글 — 칸 안 줄바꿈 표지(&cr;)만 다름' % (c['rcept_no'], c['report_nm']))
                else:
                    add.append('정정 %s(%s): 이 행 글이 정정판에 그대로 없음(공백·표지 무시 대조, 정정판 글 %d자)' % (c['rcept_no'], c['report_nm'], len(T)))
        if add:
            r['note'] += ' / ' + ' / '.join(add)


_nt = {}


def _ntext(tp):
    if tp not in _nt:
        _nt[tp] = norm(open(rel(tp), encoding='utf-8').read())
    return _nt[tp]


# ---------------------------------------------------------------- (3) 연차보고서
ANN_LIST = os.path.join(OPS, '연차보고서15_목록_g2.csv')


def ann_meta():
    m = {}
    for r in csv.DictReader(open(ANN_LIST, encoding='utf-8-sig')):
        m[(r['회사'], int(r['공시연도']), r['공시유형'])] = r
    k = {}
    for r in csv.DictReader(open(rel('handoff/연차보고서_파일목록.csv'), encoding='utf-8-sig')):
        if r['지주명'] in CORPS and r['공시연도'] in ('2025', '2026'):
            k[r['파일명']] = r
    return m, k


def kit_sections():
    out = {}
    for r in csv.DictReader(open(os.path.join(OPS, 'kit56', '연차보고서_섹션.csv'), encoding='utf-8-sig')):
        if r['지주명'] in CORPS:
            out.setdefault((r['파일명'], r['섹션제목_원문'], r['시작페이지']), []).append(r)
    return out


# 문단 지정: (회사, fy, 출처종류, 키, 줄 범위(1부터, 끝 포함), 쪽, 절 제목, direction, cp, note)
ANN_SPECS = [
    ('BNK금융지주', 2019, 'old', ('BNK금융지주', 2020, '본공시'), (11416, 11419), '(8) 보수위원회 보수정책의 적용 범위', '지주 지출', NONE,
     '(판단) 원문 「① 국내 : 지주회사 경영진에 적용」 아래 「계열사 겸직 경영진의 경우 겸직 비율에 따라 보수 지급」 — 지주 보수정책의 지급으로 보아 지주 지출. 상대방 회사 이름 없음(원문 「계열사」)'),
    ('BNK금융지주', 2019, 'old', ('BNK금융지주', 2020, '본공시'), (7476, 7476), '사외이사 활동보수 등', '지주 지출', NONE,
     '(판단) 지주 사외이사 보수 표 쪽(p.125, 같은 쪽에 사외이사 문일재·김영재 보수 표)의 ※ 줄 — 지주 사외이사 보수 지급으로 보아 지주 지출. 원문 「(부산은행 사외이사 겸직)」. section_title 은 그 쪽 머리 글(원문 「활동」과 「보수」 사이 PDF 사설 영역 문자 U+F08E 지움)'),
    ('BNK금융지주', 2025, 'kit', ('BNK금융지주_지배구조연차보고서_2026.pdf', '보수체계', '278'), (213, 215), '보수체계', '지주 지출', NONE,
     '(판단) 지주 보수위원회의 경영진 장기성과평가 보상 문단 — 지주 지출로 봄. 같은 섹션 앞 문단에 「또한 환수 가이드라인 설정 및 겸직 임원에 대한 장기성과평가 보상 방법을 개선하였습니다.」'),
    ('BNK금융지주', 2025, 'kit', ('BNK금융지주_지배구조연차보고서_2026.pdf', '보수위원회', '266'), (392, 395), '보수위원회', '지주 지출', NONE,
     '(판단) 지주 보수위원회 결의 내용(경영진 장기성과평가 기준) — 지주 지출로 봄'),
    ('iM금융지주', 2019, 'old', ('iM금융지주', 2020, '본공시'), (15156, 15158), '2) 직급별 보수총액 및 성과보수액', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음'),
    ('iM금융지주', 2020, 'old', ('iM금융지주', 2021, '본공시'), (11920, 11922), '2) 직급별 보수총액 및 성과보수액', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음. 원문 주1) 의 기준일은 「2019.12.31일 현재」(FY2020 보고서인데 원문 그대로)'),
    ('iM금융지주', 2021, 'old', ('iM금융지주', 2022, '본공시'), (12065, 12067), '2) 직급별 보수총액 및 성과보수액', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음. 추가공시(같은 해)에도 같은 글'),
    ('iM금융지주', 2022, 'old', ('iM금융지주', 2023, '본공시'), (11942, 11952), '2) 직급별 보수총액 및 성과보수액', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음. PDF 글이 낱말마다 줄이 바뀜(글 순서 그대로)'),
    ('iM금융지주', 2023, 'old', ('iM금융지주', 2024, '본공시'), (12836, 12838), '2) 보수총액 및 성과보수액', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산함」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음'),
    ('iM금융지주', 2024, 'kit', ('iM금융지주_지배구조연차보고서_2025.pdf', '보수체계', '168'), (208, 210), '보수체계', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산함」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음. 같은 보고서 「보수위원회」 섹션(시작 p.158)에 「2024년도 겸직임원의 보수를 결정」, [비고] 「1. 겸직임원의 보수기준 신설」 글이 있으나 기준 내용은 없음. 추가공시에도 같은 글'),
    ('iM금융지주', 2025, 'kit', ('iM금융지주_지배구조연차보고서_2026.pdf', '보수체계', '137'), (1041, 1043), '보수체계', NONE, '원소속회사',
     'counterparty 칸은 원문 낱말 「원소속회사」(지급 회사) — 원문 「원소속회사에서 선지급하고 업무수행비율에 따라 사후 정산함」, 원소속회사가 지주인지 자회사인지 원문에 없음 → direction 문서에 없음. 같은 섹션에 「하반기 겸직 추가된 임원의 보수 결정(안)을 결의」 글, gov_old PDF 글에 「상무 성현탁 지주 겸직 결정으로 인한 보수 및 활동수당 결의」 안건이 있으나 지급·배분 기준 내용은 없음. 추가공시에도 같은 글'),
    ('메리츠금융지주', 2022, 'old', ('메리츠금융지주', 2023, '본공시'), (5373, 5378), '10. 감독당국 권고사항 및 개선계획', NONE, NONE,
     '금융감독원 종합검사 결과 통보 문단(「보수위원회의 겸직임직원 보수배분 관련 역할 강화」) — 지급 회사·배분 기준 내용은 원문에 없음'),
    ('메리츠금융지주', 2023, 'old', ('메리츠금융지주', 2024, '본공시'), (11234, 11238), '감독당국 권고사항 및 개선계획', NONE, NONE,
     '「보수위원회 승인을 통해 겸직임직원 보수 분담기준 수립」 — 분담 기준의 내용(비율 등)은 원문에 없음. PDF 글 순서가 흩어져 문장부호가 다른 줄에 나옴(글 순서 그대로). 같은 보고서 p.105 보수위원회 안건 「그룹 겸직 임직원 보수 분담 기준 수립의 건」(가결)'),
    ('메리츠금융지주', 2024, 'kit', ('메리츠금융지주_지배구조연차보고서_2025.pdf', '회의 개최내역', '115'), (112, 115), '회의 개최내역', NONE, NONE,
     '보수위원회 안건 「그룹 겸직 임직원 보수 분담 기준 개정의 건」 심의·결의 문단 — 분담 기준의 내용은 원문에 없음. 같은 섹션 안건 표에 「나. 2호안건 : 그룹 겸직 임직원 보수 분담기준 개정의 건」 가결'),
]


def ann_rows(md_acc):
    meta, kmeta = ann_meta()
    ks = kit_sections()
    rows = []
    have = set()
    for (label, fy, kind, key, (a, b), stitle, d, cp, note) in ANN_SPECS:
        if kind == 'old':
            r = meta[key]
            p = 'dart_out/text/ops15/연차보고서__%s__%d__%s.md' % key
            L = read_lines(p)
            src = '\n'.join(x.rstrip() for x in L[a - 1:b])
            pg = None
            for j in range(a - 1, -1, -1):
                m = re.match(r'^## p\.(\d+)', L[j])
                if m:
                    pg = int(m.group(1))
                    break
            # 쪽 글 전체(원문 md)
            s = [j for j in range(a - 1, -1, -1) if L[j].startswith('## p.')][0]
            e = s + 1
            while e < len(L) and not L[e].startswith('## p.'):
                e += 1
            md_acc.setdefault((label, fy, '연차보고서'), {})[(p, s, e)] = ('%s %s %s p.%d (md %d~%d줄)' % (r['제목'], r['공시유형'], r['파일_url'], pg, s + 1, e), '\n'.join(L[s:e]))
            url, page, docn, col = r['파일_url'], 'p.%d' % pg, r['제목'], r['fetched_at']
            extra = '연차보고서 PDF 글(%s, 「## p.N」 = PDF 쪽)' % p
            # 같은 해 다른 공시 유형 대조
            for (c2, y2, t2), r2 in meta.items():
                if c2 == label and y2 == key[1] and t2 != key[2]:
                    p2 = 'dart_out/text/ops15/연차보고서__%s__%d__%s.md' % (c2, y2, t2)
                    if os.path.exists(rel(p2)):
                        same = re.sub(r'\s', '', src) in re.sub(r'\s', '', open(rel(p2), encoding='utf-8').read())
                        extra += ' / %s: %s' % (t2, '같은 글 있음' if same else '같은 글 없음(공백 무시 대조)')
        else:
            fn, sec, sp = key
            secrows = [x for x in ks[(fn, sec, sp)] if x['chunk_seq'] == '0']
            assert len(secrows) == 1, (key, len(secrows))
            kr = secrows[0]
            nchunk = len(ks[(fn, sec, sp)])
            L = kr['본문'].split('\n')
            src = '\n'.join(x.rstrip() for x in L[a - 1:b])
            km = kmeta[fn]
            url, docn, col = km['url'], km['제목'], kst(km['fetched_at'])
            page = 'p.%s(6차 섹션 「%s」 시작쪽)' % (sp, sec)
            gp = gov_page(label, fy, src)
            if gp:
                page += ' / %s' % gp
            extra = '6차 섹션 글(dart_out/ops15/kit56/연차보고서_섹션.csv, 파일 %s, 공시유형 %s, 섹션 「%s」 chunk_seq 0 줄 %d~%d)' % (fn, kr['공시유형'], sec, a, b)
            md_acc.setdefault((label, fy, '연차보고서'), {})[(fn, sec, sp)] = ('%s %s 6차 섹션 「%s」 시작 p.%s — chunk_seq 0(섹션 글 %d조각 중 첫 조각, 이 행 글이 있는 조각)' % (docn, url, sec, sp, nchunk), kr['본문'])
        pua = sorted(set('U+%04X' % ord(ch) for ch in src if 0xE000 <= ord(ch) <= 0xF8FF))
        if pua:
            extra += ' / 원문 글에 PDF 사설 영역 문자(%s)가 있어 그대로 둠' % ', '.join(pua)
        rows.append(dict(corp_label=label, fy=str(fy), item_kind='(겸직 임원 보수 지급·배분 기준)', counterparty=cp, direction=d,
                         amount_krw=NONE, basis_text=src, doc_kind='지배구조 및 보수체계 연차보고서', section_title=stitle,
                         source_text=src, rcept_no_or_url=url, page=page,
                         note=note + ' / amount_krw: 금액 없음 / ' + extra, doc_name=docn, collected_at=col))
        have.add((label, fy))
    # 없는 회사·해
    for label in CORPS:
        for fy in FYS:
            if (label, fy) in have:
                continue
            if fy <= 2023:
                docs = [(k, v) for k, v in meta.items() if k[0] == label and k[1] == fy + 1]
                if not docs:
                    continue
                k, v = sorted(docs, key=lambda kv: kv[0][2] != '본공시')[0]
                url, docn, col, page = v['파일_url'], v['제목'], v['fetched_at'], '전체 %s쪽' % v['쪽수']
                rng = '연차보고서 %s %s 전체(%s 포함 같은 해 모든 공시유형 md)' % (fy + 1, '·'.join(sorted(set(x[0][2] for x in docs))), k[2])
            else:
                fns = sorted([fn for fn, km in kmeta.items() if km['지주명'] == label and int(km['공시연도']) == fy + 1],
                             key=lambda x: ('수정' in x or '추가' in x or '재공시' in x or '정정' in x, x))
                km = kmeta[fns[0]]
                url, docn, col, page = km['url'], km['제목'], kst(km['fetched_at']), '전체 %s쪽' % km['페이지수']
                rng = '6차 섹션 글 %s 전체 섹션 + gov_old 다시 받은 PDF 글 dart_out/text/ops15b/연차보고서__%s__FY%d*.md' % ('·'.join(fns), label, fy)
            extra = ''
            if label == 'JB금융지주' and fy == 2025:
                extra = ' / 같은 해 정정공시(gov_old PDF 글 dart_out/text/ops15b/연차보고서__JB금융지주__FY2025__정정공시.md p.1)에 「임·직원의 겸직 보수가 확정된 바」 문장이 있으나 지급 회사·배분 기준은 없음'
            if label == 'BNK금융지주' and fy == 2020:
                extra = ' / 같은 보고서에 「평가 대상 경영진 16명(겸직 경영진 포함)에 대한 평가 결과 및 보상금액, 지급방법 등 결의」(보수위원회 결의 목록) 글은 있으나 지급 회사·배분 기준 문단 없음'
            rows.append(dict(corp_label=label, fy=str(fy), item_kind='(겸직 임원 보수 지급·배분 기준)', counterparty=NONE, direction=NONE,
                             amount_krw=NONE, basis_text=NONE, doc_kind='지배구조 및 보수체계 연차보고서', section_title=NONE,
                             source_text=NONE, rcept_no_or_url=url, page=page,
                             note='문서에 없음 — 찾은 범위: %s 에서 「겸직·겸임·겸무」 앞뒤 2줄 안 「보수·급여·성과급」과 「지급·분담·배분·안분·정산·비율·부담」, 「업무수행비율·업무분담비율·보수 분담·분담기준·인건비 정산·선지급·사후 정산」%s' % (rng, extra),
                             doc_name=docn, collected_at=col))
    return rows


_gov = {}


def gov_page(label, fy, src):
    p = rel('dart_out/text/ops15b/연차보고서__%s__FY%d.md' % (label, fy))
    if not os.path.exists(p):
        return ''
    if p not in _gov:
        t = open(p, encoding='utf-8').read()
        _gov[p] = [(int(m.group(1)), re.sub(r'\s', '', m.group(2))) for m in re.finditer(r'## p\.(\d+)\n(.*?)(?=\n## p\.\d+\n|\Z)', t, re.S)]
    n = re.sub(r'\s', '', src)
    for pg, tx in _gov[p]:
        if n in tx:
            return 'p.%d(gov_old 가 다시 받은 PDF 글 %s)' % (pg, os.path.relpath(p, ROOT))
    # 앞 40자만
    for pg, tx in _gov[p]:
        if n[:40] in tx:
            return 'p.%d(gov_old 가 다시 받은 PDF 글 %s — 앞 40자 일치)' % (pg, os.path.relpath(p, ROOT))
    return ''


# ---------------------------------------------------------------- 쓰기
def write_csv(rows):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in COLS})


def write_md_report(cx):
    os.makedirs(OUT_MD_DIR, exist_ok=True)
    p = os.path.join(OUT_MD_DIR, '%s__FY%d__사업보고서.md' % (cx.label, cx.fy))
    with open(p, 'w', encoding='utf-8') as f:
        f.write('# %s FY%d 사업보고서 — 별도재무제표 주석 원문(작업 G)\n\n' % (cx.label, cx.fy))
        f.write('출처: OpenDART 사업보고서 rcept_no %s, 「%s」, 글 %s(OpenDART XML → md), 받은 시각 %s\n\n' % (
            cx.rep['rcept_no'], cx.rep['report_nm'], cx.rep['text_path'], cx.rep['fetched_at']))
        for (a, b), title in sorted(cx.md_blocks.items()):
            f.write('## %s\n\n' % title)
            f.write('\n'.join(cx.L[a:b]).rstrip() + '\n\n')
    return os.path.relpath(p, ROOT)


def write_md_ann(md_acc):
    out = []
    for (label, fy, doc), blocks in md_acc.items():
        p = os.path.join(OUT_MD_DIR, '%s__FY%d__%s.md' % (label, fy, doc))
        with open(p, 'w', encoding='utf-8') as f:
            f.write('# %s FY%d 지배구조 및 보수체계 연차보고서 — 겸직 임원 보수 문단이 나온 쪽·섹션 원문(작업 G)\n\n' % (label, fy))
            for k, (title, text) in blocks.items():
                f.write('## 출처: %s\n\n%s\n\n' % (title, text.rstrip()))
        out.append(os.path.relpath(p, ROOT))
    return out


def main():
    rep, cor = load_reports()
    rows = []
    md_acc = {}
    docs = []
    for label in CORPS:
        for fy in FYS:
            r = rep[(label, fy)]
            cx = Ctx(label, fy, r, cor.get((label, fy), []))
            if label == 'BNK금융지주':
                rr = bnk(cx)
            elif label == '메리츠금융지주':
                rr = meritz(cx)
            elif label == 'JB금융지주':
                rr = vertical(cx, 'JB')
            elif label == 'iM금융지주':
                rr = vertical(cx, 'iM')
            elif fy <= 2024:
                rr = kis_old(cx)
            else:
                rr = kis_2025(cx)
            if label in ('iM금융지주', '메리츠금융지주', '한국투자금융지주'):
                rr.append(no_basis_row(cx))
            rr += rev_rows(cx)
            corr_notes(rr, cor.get((label, fy), []))
            rows += rr
            mdp = write_md_report(cx)
            docs.append(dict(doc_kind='사업보고서', corp_label=label, fy_or_date='FY%d' % fy, report_nm=r['report_nm'],
                             rcept_no_or_url=r['rcept_no'], rcept_dt=r['rcept_dt'], raw_path='dart_out/' + r['raw_path'],
                             sha256=r['raw_sha256'], fetched_at=r['fetched_at'], text_path=r['text_path'], status='받음',
                             note='본 — 행 출처(별도 주석 특수관계자·수수료손익 주석, Ⅱ 검색) / 원문 md %s' % mdp))
            for c in cor.get((label, fy), []):
                ok = bool(c['text_path']) and os.path.exists(rel(c['text_path']))
                docs.append(dict(doc_kind='사업보고서', corp_label=label, fy_or_date='FY%d' % fy, report_nm=c['report_nm'],
                                 rcept_no_or_url=c['rcept_no'], rcept_dt=c['rcept_dt'], raw_path='dart_out/' + c['raw_path'],
                                 sha256=c['raw_sha256'], fetched_at=c['fetched_at'], text_path=c['text_path'],
                                 status='받음' if ok else '014',
                                 note=('정정 — 본 보고서 행 글과 대조(다르면 행 note)' if ok else '정정 — OpenDART %s %s, 대조 못 함' % (c['doc_status'], c['doc_message']))))
        write_csv(rows)  # 회사마다 중간 저장
        print(label, len(rows), file=sys.stderr)
    rows += ann_rows(md_acc)
    write_md_ann(md_acc)
    write_csv(rows)
    # 연차보고서 문서 목록
    meta, kmeta = ann_meta()
    for (c, y, t), v in sorted(meta.items()):
        p = 'dart_out/text/ops15/연차보고서__%s__%d__%s.md' % (c, y, t)
        docs.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label=c, fy_or_date='FY%d' % (y - 1), report_nm=v['제목'],
                         rcept_no_or_url=v['파일_url'], rcept_dt=v['공시일'], raw_path='dart_out/raw/governance15/%s/' % c,
                         sha256=v['sha256'], fetched_at=v['fetched_at'], text_path=p if os.path.exists(rel(p)) else '',
                         status='받음', note='공시연도 %d %s — (3) 겸직 임원 보수 문단 검색' % (y, t)))
    for fn, km in sorted(kmeta.items()):
        docs.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label=km['지주명'], fy_or_date='FY%d' % (int(km['공시연도']) - 1),
                         report_nm=km['제목'], rcept_no_or_url=km['url'], rcept_dt='', raw_path='(6차 PDF — 이 컨테이너에 없음; gov_old 다시 받음 dart_out/raw/ops15b/gov_old/)',
                         sha256=km['sha256'], fetched_at=kst(km['fetched_at']), text_path='dart_out/ops15/kit56/연차보고서_섹션.csv (파일명 %s)' % fn,
                         status='받음', note='공시연도 %s %s — 6차 섹션 글로 (3) 검색' % (km['공시연도'], km['공시유형'])))
    with open(OUT_DOCS, 'w', encoding='utf-8-sig', newline='') as f:
        cols = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at', 'text_path', 'status', 'note']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in docs:
            w.writerow(d)
    chk = write_check(rows, rep)
    print('rows', len(rows), 'check', len(chk), file=sys.stderr)


# ---------------------------------------------------------------- (4) 확인_G_g2.csv
OUT_CHK = os.path.join(OPS, '조각', '확인_G_g2.csv')
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note', 'doc_name', 'collected_at']


def write_check(rows, rep):
    req = open(os.path.join(OPS, 'REQUEST15b.md'), encoding='utf-8').read().split('\n')
    item = [re.sub(r'^\s*\*\s*', '', l).strip() for l in req if 'KB·하나·우리·BNK·iM·JB FY2025' in l][0]
    out = []
    for label in ('BNK금융지주', 'iM금융지주', 'JB금융지주'):
        for fy in FYS:
            r0 = rep[(label, fy)]
            L = read_lines(r0['text_path'])
            mine = [r for r in rows if r['corp_label'] == label and r['fy'] == str(fy) and r['doc_kind'] == '사업보고서']
            brand = [r for r in mine if re.search(r'브랜드|상표', r['item_kind'])]
            mgmt = [r for r in mine if re.search(r'경영자문|경영관리|용역', r['item_kind'])]
            fee = [r for r in mine if strip_fn(r['item_kind']) in ('수수료수익', '기타수익') and r['counterparty'] != NONE]
            feelist = ', '.join('%s %s %s' % (r['counterparty'], r['item_kind'], r['amount_krw']) for r in fee)
            # 정관·이사회 안건(브랜드)
            extra = []
            for i, l in enumerate(L):
                if re.search(r'브랜드, 라이센스 등의 대여|브랜드 ?사용계약 체결|브랜드사용료 신규계약', l):
                    n, t, _ = sec_of(L, i)
                    c = cells(l)
                    hit = [x for x in c if re.search(r'브랜드, 라이센스 등의 대여|브랜드 ?사용계약 체결|브랜드사용료 신규계약', x)][0]
                    m = re.search(r'(\d+\.\s*브랜드 ?사용계약 체결\(안\)|\d+\.\s*브랜드사용료 신규계약 체결\(안\))', hit)
                    q = m.group(1) if m else hit
                    ctx = '' if not m else '(같은 표 행 앞 칸: %s)' % ' / '.join(c[:2])
                    extra.append('같은 사업보고서 XML [절 %d] 「%s」 [표 %d] 에 「%s」 글 있음%s' % (n, t, table_of(L, i)[0], q.strip(), ctx))
            base = dict(item_id='G-특히볼것-1(브랜드)', item_text=item, corp_label=label, fy=str(fy), doc_name=r0['report_nm'], collected_at=r0['fetched_at'])
            # 브랜드
            if brand:
                b = brand[0]
                note = '브랜드(상표권) 수수료 수익 행 있음: 별도 주석 수수료손익 표 「%s」 당기 %s원(%s). 자회사별 상대방: 그 표에 상대방 칸 없음, 같은 해 별도 주석 특수관계자 거래 표에 브랜드·상표 이름의 열·행 없음(그 표의 %s 금액: %s) — 자회사별 브랜드 수수료 금액은 문서에 없음. 산정 기준(요율·기준 수익) 문단 없음(찾은 범위: 이 사업보고서 전체 「상표」「브랜드」「사용료」)' % (
                    b['item_kind'], b['amount_krw'], b['note'].split(' / ')[0], '「기타수익」' if label == 'BNK금융지주' else '「수수료수익」', feelist or '없음')
                if extra:
                    note += '. ' + '; '.join(extra)
                out.append(dict(base, result='원문 있음', where='G_g2.csv 행 %s FY%d item_kind=%s (rcept %s, %s)' % (label, fy, b['item_kind'], b['rcept_no_or_url'], b['page']),
                                rcept_no_or_url=b['rcept_no_or_url'], page=b['page'], source_excerpt=b['source_text'][:300], note=note))
            else:
                note = '브랜드(상표권) 수수료 수익 문서에 없음 — 찾은 범위: 이 사업보고서 별도 주석 특수관계자 거래 표(계정과목)·수수료손익 주석, 사업보고서 전체 「상표」「브랜드」「사용료」. 특수관계자 거래 표의 수수료 계정은 「수수료수익」(종류 이름 없음): %s' % (feelist or '없음')
                ex = NONE
                if label == 'iM금융지주':
                    k = find_line(L, *sep_range(L), r'^\|\s*\(\*\)(<br>)?\s*전액 (당사와 )?종속(회사|기업)(과의| 간) 거래에서 발생하였으며 외부 고객과의 거래로부터 발생한 수수료수익')
                    if k is not None:
                        n_, t_, _ = sec_of(L, k)
                        note += '. 별도 주석 수수료수익 표 각주 원문(XML [절 %d] 「%s」 [표 %d]): %s' % (n_, t_, table_of(L, k)[0], clean_name(L[k].strip().strip('|').strip()))
                if extra:
                    note += '. ' + '; '.join(extra)
                out.append(dict(base, result='문서에 없음', where='G_g2.csv 해당 행 없음(%s FY%d 특수관계자 거래 표 행 참조)' % (label, fy),
                                rcept_no_or_url=r0['rcept_no'], page='별도 주석 「특수관계자」·「수수료」 주석 + 사업보고서 전체 검색', source_excerpt=ex, note=note))
            # 경영관리·용역
            if mgmt:
                b = mgmt[0]
                out.append(dict(base, item_id='G-특히볼것-1(경영관리·용역)', result='원문 있음',
                                where='G_g2.csv 행 %s FY%d item_kind=%s (rcept %s, %s)' % (label, fy, b['item_kind'], b['rcept_no_or_url'], b['page']),
                                rcept_no_or_url=b['rcept_no_or_url'], page=b['page'], source_excerpt=b['source_text'][:300],
                                note='(판단) 원문 계정명 「%s」 을 「경영관리·용역 수수료」 항목으로 봄 — 원문에 「경영관리」「용역」 낱말은 없음. 당기 %s원(%s). 자회사별 상대방: 수수료손익 표에 상대방 칸 없음, 특수관계자 거래 표에 「경영자문」 이름의 계정 없음(그 표의 「수수료수익」 금액: %s) — 자회사별 경영자문수수료 금액은 문서에 없음' % (
                                    b['item_kind'], b['amount_krw'], b['note'].split(' / ')[0], feelist or '없음')))
            else:
                note = '「경영관리」「용역」「자문」 이름의 수수료 수익 행 문서에 없음 — 찾은 범위: 별도 주석 특수관계자 거래 표 계정과목·열 머리, 수수료손익 주석 행. '
                if label == 'BNK금융지주':
                    note += '수수료손익 주석의 수수료수익 행은 「브랜드수수료」「기타수수료수익」뿐. 특수관계자 거래 표 수익 쪽 열은 이자수익·기타수익%s' % ('·배당금수익' if fy >= 2024 else '')
                else:
                    note += '특수관계자 거래 표의 수수료 계정은 「수수료수익」(종류 이름 없음): %s' % (feelist or '없음')
                seen_l = set()
                s0, e0 = sep_range(L)
                for i in range(s0, e0):
                    l = L[i]
                    if not l.startswith('|'):
                        continue
                    lab = tuple(c for c in cells(l) if re.search(r'용역|경영관리|자문', c) and not is_numlike(c))
                    if lab and lab not in seen_l and any(numtxt(c) for c in cells(l) if is_numlike(c)):
                        seen_l.add(lab)
                        n_, t_, _ = sec_of(L, i)
                        note += '. 별도 주석 md %d줄 표 행 「%s」(XML [절 %d] 「%s」 [표 %d]) — 이름에 「용역」「경영관리」「자문」이 든 행, 수수료수익 행 아님·상대방 칸 없음' % (i + 1, l.strip(), n_, t_, table_of(L, i)[0])
                out.append(dict(base, item_id='G-특히볼것-1(경영관리·용역)', result='문서에 없음',
                                where='G_g2.csv 해당 이름의 행 없음(%s FY%d 특수관계자 거래 표 행 참조)' % (label, fy),
                                rcept_no_or_url=r0['rcept_no'], page='별도 주석 「특수관계자」·「수수료」 주석', source_excerpt=NONE, note=note))
    with open(OUT_CHK, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CHK_COLS)
        w.writeheader()
        for r in out:
            w.writerow({k: r[k] for k in CHK_COLS})
    return out


if __name__ == '__main__':
    main()
