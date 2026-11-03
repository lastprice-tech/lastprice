"""15차 확장 작업 I 검증 — dart_out/ops15/조각/I.csv·확인_I.csv·문서목록15b_I.csv·원문/I/*.md.

생성기(ops15b_I.py)를 import 하지 않고 출처 글을 따로 읽어 대조함. 결과: dart_out/ops15/verify15b_I.txt, 실패 0 이면 exit 0.
대조 규칙(COMMON15b 「원문 대조 규칙」): 칸 글과 출처 글에서 공백·줄바꿈(과 보이지 않는 제어문자)만 지우고 이어진 글로 들어 있는지.
  PDF 쪽 md 출처는 「## p.N」 쪽 표지 줄을 빼고 봄. OpenDART XML md 출처만 md 표지 「|」「<br>」도 양쪽에서 지움.
"""
import csv, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = lambda *p: os.path.join(ROOT, *p)
csv.field_size_limit(10 ** 9)
COLS = ['corp_label', 'fy_or_date', 'topic', 'source_text', 'doc_kind', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note']
DOC_COLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at', 'text_path', 'status', 'note']
LABELS = {'KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'NH농협금융지주', '메리츠금융지주', 'iM금융지주', 'BNK금융지주', 'JB금융지주', '한국투자금융지주'}
TOPICS = {'겸직 결정', '분리', '자회사 CEO 평가'}
RESULTS = {'원문 있음', '문서에 없음', '수집 실패'}
PAGE_RE = re.compile(r'^## p\.(\d+)\b.*$', re.M)
CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
fails, checks = [], []


def ok(cond, msg):
    checks.append(msg)
    if not cond:
        fails.append(msg)
    return cond


def rcsv(p):
    with open(p, encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def norm(t, xml=False):
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return re.sub(r'\s+', '', CTRL_RE.sub('', t))


# ── 출처 색인(URL·rcept → 글) ──────────────────────────────────────────────
INDEX = {}
_, gov_old = rcsv(J('dart_out/ops15/문서목록15b_gov_old.csv'))
for x in gov_old:
    if x['status'] == '받음' and x['text_path']:
        INDEX[x['rcept_no_or_url']] = ('pdf', J(x['text_path']))
for g in ('g1', 'g2'):
    _, rows = rcsv(J(f'dart_out/ops15/연차보고서15_목록_{g}.csv'))
    for x in rows:
        p = J(f"dart_out/text/ops15/연차보고서__{x['회사']}__{x['공시연도']}__{x['공시유형']}.md")
        if os.path.exists(p):
            INDEX.setdefault(x['파일_url'], ('pdf', p))
_, handoff = rcsv(J('handoff/연차보고서_파일목록.csv'))
for x in handoff:
    if x['url']:
        INDEX.setdefault(x['url'], ('kit56', (x['지주명'], x['공시연도'], x['공시유형'])))
_TXT = {}
_KIT = None


def source_text(url):
    """(kind, 대조용 원글, 쪽/섹션 목록[(이름, 글)])."""
    if url in _TXT:
        return _TXT[url]
    global _KIT
    if re.fullmatch(r'\d{14}', url):
        fs = glob.glob(J(f'dart_out/text/ops15b/주요경영사항__*__{url}.md'))
        raw = open(fs[0], encoding='utf-8').read() if fs else ''
        res = ('xml', raw, [('XML', raw)])
    elif url in INDEX and INDEX[url][0] == 'pdf':
        raw = open(INDEX[url][1], encoding='utf-8').read()
        parts = PAGE_RE.split(raw)
        pages = [(f'p.{parts[i]}', parts[i + 1]) for i in range(1, len(parts), 2)]
        res = ('pdf', ''.join(b for _, b in pages), pages)
    elif url in INDEX and INDEX[url][0] == 'kit56':
        if _KIT is None:
            _, _KIT = rcsv(J('dart_out/ops15/kit56/연차보고서_섹션.csv'))
        key = INDEX[url][1]
        rows = sorted((x for x in _KIT if (x['지주명'], x['공시연도'], x['공시유형']) == key),
                      key=lambda x: (int(x['섹션순번']), int(x['chunk_seq'])))
        segs = [(f"p.{x['시작페이지']}(6차 섹션 {x['섹션순번']}", x['본문'] + '\n') for x in rows]
        res = ('kit56', ''.join(b for _, b in segs), segs)
    else:
        res = (None, '', [])
    _TXT[url] = res
    return res


def contains(url, text):
    kind, raw, segs = source_text(url)
    if kind is None or not raw:
        return False, kind
    x = kind == 'xml'
    return norm(text, x) in norm(raw, x), kind


def page_ok(url, page, text):
    kind, raw, segs = source_text(url)
    head = norm(text, kind == 'xml')[:12]
    if kind == 'pdf':
        m = re.match(r'p\.(\d+)', page)
        if not m:
            return False
        first = f'p.{m.group(1)}'
        body = ''.join(b for n, b in segs if n == first)
        return head in norm(body) or norm(text)[:6] in norm(body)
    if kind == 'kit56':
        m = re.match(r'p\.(\d+)\(6차 섹션 (\d+)', page)
        if not m:
            return False
        body = ''.join(b for n, b in segs if n == f'p.{m.group(1)}(6차 섹션 {m.group(2)}')
        return head in norm(body)
    if kind == 'xml':
        return page.startswith('XML [절')
    return False


# ── I.csv ─────────────────────────────────────────────────────────────────
cols, rows = rcsv(J('dart_out/ops15/조각/I.csv'))
ok(cols == COLS, f'I.csv 열 = 지정 열 {cols}')
ok(len(rows) > 0, f'I.csv 행 {len(rows)}')
_md = [PAGE_RE.sub('', open(f, encoding='utf-8').read()) for f in sorted(glob.glob(J('dart_out/ops15/원문/I/*.md')))]  # 「## p.N」 쪽 머리 줄은 md 표지라 빼고 봄
md_all = ''.join(norm(m) for m in _md)
md_all_x = ''.join(norm(m, True) for m in _md)
n_na = 0
for i, r in enumerate(rows, 2):
    tag = f"I.csv {i}행 {r['corp_label']} {r['fy_or_date']} {r['page']}"
    ok(r['corp_label'] in LABELS, f'{tag}: corp_label')
    ok(bool(re.fullmatch(r'FY\d{4}|\d{4}-\d\d-\d\d', r['fy_or_date'])), f'{tag}: fy_or_date 꼴')
    ok(r['topic'] in TOPICS, f'{tag}: topic {r["topic"]}')
    for c in ('source_text', 'doc_kind', 'rcept_no_or_url', 'note', 'doc_name'):
        ok(bool(r[c].strip()), f'{tag}: {c} 비어 있지 않음')
    ok(bool(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00', r['collected_at'])), f'{tag}: collected_at KST')
    if r['source_text'] == '문서에 없음':
        n_na += 1
        ok('찾은 범위' in r['note'], f'{tag}: 「문서에 없음」 행 note 에 찾은 범위')
        ok(r['page'] == '', f'{tag}: 「문서에 없음」 행 page 비움')
        ok(source_text(r['rcept_no_or_url'])[0] is not None, f'{tag}: 「문서에 없음」 행 출처 문서 글 있음')
        continue
    good, kind = contains(r['rcept_no_or_url'], r['source_text'])
    ok(good, f'{tag}: source_text 원문 대조({kind})')
    ok(page_ok(r['rcept_no_or_url'], r['page'], r['source_text']), f'{tag}: page 표지가 글 시작 쪽과 맞음')
    if kind == 'xml':
        ok('|' not in r['source_text'] and '<br>' not in r['source_text'], f'{tag}: XML 행에 md 표지 없음')
    ok('…' not in r['source_text'] or '…' in source_text(r['rcept_no_or_url'])[1], f'{tag}: 넣은 「…」 없음')
    ok(norm(r['source_text'], kind == 'xml') in (md_all_x if kind == 'xml' else md_all), f'{tag}: 원문 md(원문/I)에 그 글이 있음')
    if r['topic'] == '분리' and '분리' not in r['source_text']:
        ok('(판단)' in r['note'], f'{tag}: 원문에 「분리」 없는 분리 행은 note (판단)')
    if r['topic'] == '겸직 결정' and not re.search(r'겸직|겸임|兼', r['source_text']):
        ok('(판단)' in r['note'], f'{tag}: 원문에 「겸직」 없는 겸직 결정 행은 note (판단)')
    if CTRL_RE.search(source_text(r['rcept_no_or_url'])[1]) and kind == 'pdf':
        ok(True, f'{tag}: (출처 글에 제어문자 있음 — 칸 글에서 지웠으면 note 「제어문자 지움」)')
        ok(not CTRL_RE.search(r['source_text']), f'{tag}: 칸 글에 제어문자 없음')
# ── 확인_I.csv ────────────────────────────────────────────────────────────
req = open(J('dart_out/ops15/REQUEST15b.md'), encoding='utf-8').read()
ccols, crows = rcsv(J('dart_out/ops15/조각/확인_I.csv'))
ok(ccols == CHK_COLS, f'확인_I.csv 열 {ccols}')
ids = {r['item_id'] for r in crows}
need = ['I1-KB-FY2014', 'I1-KB-FY2015', 'I1-KB-FY2016', 'I1-KB-FY2017', 'I1-W-FY2019', 'I1-DGB-FY2018', 'I1-DGB-FY2019', 'I1-DGB-FY2020', 'I1-BNK-FY2017']
for ab in ('KB', 'SH', 'HN', 'WR', 'NH', 'iM', 'BNK', 'JB'):
    need += [f'I2-{ab}-후보관리', f'I2-{ab}-평가절차', f'I2-{ab}-평가지표']
for ev in ('우리금융지주-2020-03', 'iM금융지주-2020-09', 'iM금융지주-2024-03', 'iM금융지주-2026-01', 'BNK금융지주-2017'):
    need += [f'I3-{ev}-자회사공시', f'I3-{ev}-지주대표이사', f'I3-{ev}-겸직기간']
for n in need:
    ok(n in ids, f'확인 항목 {n} 있음')
for i, r in enumerate(crows, 2):
    tag = f"확인_I {i}행 {r['item_id']}"
    ok(r['result'] in RESULTS, f'{tag}: result')
    ok(r['item_text'] in req, f'{tag}: item_text 가 REQUEST15b.md 글 그대로')
    ok(len(r['source_excerpt']) <= 300, f'{tag}: source_excerpt 300자 이하')
    ok(bool(r['note'].strip()), f'{tag}: note')
    if r['source_excerpt']:
        good, kind = contains(r['rcept_no_or_url'], r['source_excerpt'])
        ok(good, f'{tag}: source_excerpt 원문 대조({kind})')
    if r['result'] == '원문 있음':
        ok(bool(r['where']) and bool(r['source_excerpt']), f'{tag}: 원문 있음 → where·발췌 있음')
# ── 문서목록 ──────────────────────────────────────────────────────────────
dcols, drows = rcsv(J('dart_out/ops15/문서목록15b_I.csv'))
ok(dcols == DOC_COLS, f'문서목록15b_I.csv 열 {dcols}')
used = {r['rcept_no_or_url'] for r in rows}
listed = {d['rcept_no_or_url'] for d in drows}
for u in used:
    ok(u in listed, f'문서목록에 행 출처 {u[:60]} 있음')
# ── 비밀값 ────────────────────────────────────────────────────────────────
key = os.environ.get('DART_API_KEY', '')
mine = [J('dart_out/ops15/조각/I.csv'), J('dart_out/ops15/조각/확인_I.csv'), J('dart_out/ops15/문서목록15b_I.csv'),
        J('scripts/dart/ops15b_I.py'), J('scripts/dart/verify15b_I.py')] + glob.glob(J('dart_out/ops15/원문/I/*.md')) + \
       glob.glob(J('dart_out/text/ops15b/주요경영사항__*.md'))
for f in mine:
    t = open(f, encoding='utf-8', errors='replace').read()
    ok(not (key and key in t), f'비밀값 없음: {os.path.relpath(f, ROOT)}')
    ok(not re.search(r'crtfc_key=(?!\*)[0-9A-Za-z]{20,}', t), f'키 꼴 문자열 없음: {os.path.relpath(f, ROOT)}')

out = [f'verify15b_I — I.csv {len(rows)}행(문서에 없음 {n_na}), 확인_I {len(crows)}행, 문서목록 {len(drows)}행',
       f'검사 {len(checks)}건, 실패 {len(fails)}건'] + ['실패: ' + f for f in fails]
open(J('dart_out/ops15/verify15b_I.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out[:2] + out[2:22]))
sys.exit(1 if fails else 0)
