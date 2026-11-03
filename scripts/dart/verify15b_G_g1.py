"""15차 확장 작업 G 그룹 g1(KB·신한·하나·우리·NH농협) 독립 검증 — 인자 없음. exit 0 = FAIL 0건, exit 1 = FAIL 있음.
결과: dart_out/ops15/verify15b_G_g1.txt (요약 · FAIL 줄 · 검사별 표본 줄). 생성기 ops15b_G_g1.py 를 import 하지 않고, 출처 글을 따로 읽어 봄.
네트워크 안 씀(이미 있는 글만). 비밀값을 읽거나 쓰지 않음(DART_API_KEY 는 값 비교만 — 출력에 내지 않음).

(b) 꼴: 조각·확인·문서목록 CSV 의 utf-8-sig BOM, 열 이름·순서(COMMON15b), 모든 칸 빈칸 0(특히 rcept_no_or_url·page·doc_name·collected_at),
    collected_at 꼴 YYYY-MM-DDTHH:MM:SS+09:00, collected_at·doc_name 이 출처 목록(사업보고서_원문.csv fetched_at·report_nm / 연차보고서 목록 fetched_at·제목)과 같음.
(a) 원문 대조(COMMON15b 대조 규칙): source_text 와 원문 칸(basis_text)은 「문서에 없음」이 아니면 출처 텍스트 한 곳의 이어진 글.
    대조 = 공백·줄바꿈을 지운 칸 글이 공백·줄바꿈을 지운 출처 글 안에 있음. OpenDART XML md 출처에서만 md 표지 「|」「<br>」와
    XML 줄바꿈 표지 「&cr;」(OpenDART 문서의 줄바꿈 글자)를 양쪽에서 지움. 위치: page 의 「XML [절 n] 「제목」 [표 m]」 → 그 절 안의 그 표(표가 없으면 그 절),
    절 제목이 md 의 「### [절 n] 제목」과 같아야 함. 「p.N(본문 PDF, 13차 보관)」 → 13차 PDF 글 N 쪽에 그 행의 계정명과 원문 숫자(문단 행이면 글)가 있어야 함.
    연차보고서 → 그 URL 의 글(「## p.N」 md 또는 6차 섹션 본문)의 page 쪽(p.N 또는 p.N~p.M, 6차 섹션은 섹션순번·chunk) 안,
    「PDF p.K(gov_old …)」가 있으면 그 md 의 K 쪽에도 있어야 함.
    item_kind(괄호로 시작하는 항목 이름 빼고)·counterparty(「문서에 없음」 빼고)는 그 행의 표 안 글이어야 함.
(c) 빠짐: ① 회사×FY(2019~2025)마다 별도 주석 특수관계자 손익 행, (산정 기준 문단) 또는 브랜드 행, FY2025 Ⅷ 행, 연차보고서 회사×FY(KB·신한·하나 2017~,
    우리·NH 2019~)마다 (겸직 임원 보수 지급·배분 기준) 행·(KB·신한·하나) (겸직 부문장 성과평가·보수) 행이 있음.
    ② 특수관계자 손익 표 다시 뽑기(생성기와 따로): 별도 주석(「5. 재무제표 주석」~「6. 기타 재무」/「IV.」 앞) 안에서 특수관계자 문단의 마지막 소항목 글
    (「(n)」「n-n」 뒤)이나 바로 앞 표지 표(「…공시 | 당기」)에 「손익」「거래내역」「특수관계자거래에 대한 공시」가 있고 기간이 당기인 표(글 없이 바로 이어진 표 포함)를
    찾아, 표 머리로 열 역할(계정·회사·당기 열)을 정해 당기 칸 중 0·「-」·빈칸 아닌 칸(합계·소계·「… 계」 행, 합계 열 빼고)을 모두 뽑고,
    (회사, 계정, 금액) 묶음을 조각 행과 1:1 로 맞춤 — 남거나 모자라면 FAIL.
    ③ 키워드 직접 grep: 별도 주석·Ⅱ 의 「브랜드」「상표」「로열티」「경영관리」「경영자문」「용역」 줄, Ⅷ 「임원의 보수 등」의 「겸직」「겸임」「분담」「원소속」「배분」 줄,
    연차보고서 전체의 「겸직」「겸임」「겸무」「원소속」 근처(앞뒤 120자) 보수 낱말 글, (KB·신한·하나) 「부문장」「사업그룹장」「Matrix」 근처(앞뒤 60자)
    「성과평가」「평가체계」「KPI」「비중」 글 → 조각에 없는 곳은 BR_RULES(사업보고서)·REVIEWED(연차보고서; 검토 결과를 사실로 적음)에 없으면 FAIL.
    정정판: 같은 FY 정정 md 에 행 글이 없으면 note 에 「정정 <rcept>」, XML 없는 정정판은 note 에 그 rcept. 원문 md(원문/G) 안에 행 글이 있어야 함.
(d) 「문서에 없음」 행: note 에 「찾은 범위」 또는 「수집 실패」. 더 넓은 낱말(③의 낱말 + 「Brand」「브랜드사용」「사용수수료」「KPI」「가중치」「비중」)로
    그 범위를 다시 훑어 걸린 글이 REVIEWED 에 없으면 FAIL.
(e) 숫자: 특수관계자·배당·브랜드 행 전부 — amount_krw = note 「원문 숫자 X」 × 1,000,000(괄호 = 음수), X 가 ②에서 다시 뽑은 당기 칸과 같음,
    표 앞 글·표지 표·표 안에 「백만원」. 표본 30개 이상을 결과 파일에 그대로 찍음.
(f) direction: 표의 수익·비용 묶음 머리(신한 「<수익>」「<비용>」, NH 구분 칸 「수익」「비용」, 하나 「수익」「비용」 열 묶음)가 있으면 그대로,
    없으면 계정명 끝말(「…수익」(…손익 아님) → 지주 수입, 「…비용」「…관리비」「…상각비」 → 지주 지출). 둘 다 아니면 note 에 「(판단)」이 있어야 함.
    note·section_title 에 기능 분류·이유 추정 낱말(「때문」「위하여」「위해」「목적」「이유」「추정」「보임」「듯」「의도」「리스크 기능」「재무 기능」)이 없어야 함.
    section_title 은 빈칸이거나 note 글(「같은 문단이」 …)이면 FAIL.
(g) 확인_G_g1.csv: REQUEST15b.md 작업 G 「특히 볼 것」 4줄이 item_text 에 글 그대로, g1 대상 회사·FY 마다 행(G-1 KB·하나·우리 FY2025,
    G-2 신한 FY2025, G-3 KB·신한·하나·우리·NH FY2025, G-4 신한·KB·하나 FY2017~FY2025 각 해), result ∈ {원문 있음, 문서에 없음, 수집 실패},
    result 가 조각의 같은 회사·FY 행과 맞음, source_excerpt 300자 이하이고 「문서에 없음」이 아니면 조각 같은 회사 행 source_text 안의 글,
    note 에 추정 낱말 없음.
(h) 비밀: 산출 파일·스크립트에 DART_API_KEY 값(환경변수에 있으면 값 비교, 출력 안 함)·「crtfc_key=」·40자리 16진 글 없음.
    PDF·zip 원본이 git 추적 파일 목록에 새로 들어가지 않음(dart_out/raw·dart_out/text·dart_out/ops15/조직도 는 무시 폴더 — 검사).
"""
import csv, os, re, sys, zipfile, subprocess, collections

csv.field_size_limit(10 ** 9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'dart_out', 'ops15')
NA = '문서에 없음'
G1 = ['KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'NH농협금융지주']
F_G = os.path.join(OUT, '조각', 'G_g1.csv')
F_C = os.path.join(OUT, '조각', '확인_G_g1.csv')
F_D = os.path.join(OUT, '문서목록15b_G_g1.csv')
F_TXT = os.path.join(OUT, 'verify15b_G_g1.txt')
ZIP13 = os.path.join(ROOT, 'handoff', '13차_지주관리유형', '13차_지주관리유형_텍스트.zip')
COLS = {F_G: ['corp_label', 'fy', 'item_kind', 'counterparty', 'direction', 'amount_krw', 'basis_text', 'doc_kind', 'section_title',
              'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at'],
        F_C: ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note'],
        F_D: ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at',
              'text_path', 'status', 'note']}
I_PAY = '(겸직 임원 보수 지급·배분 기준)'
I_DIV = '(겸직 부문장 성과평가·보수)'
I_BASIS = '(산정 기준 문단)'
BAD_WORDS = ['때문', '위하여', '위해', '목적', '이유', '추정', '보임', '듯', '의도', '리스크 기능', '재무 기능']

fails, info = [], collections.defaultdict(list)


def F(msg):
    fails.append(msg)


def I(sec, msg):
    info[sec].append(msg)


def sq(s):
    return re.sub(r'\s+', '', s or '')


def sqm(s):
    """OpenDART XML md 표지(「|」「<br>」「&cr;」)와 공백을 지움."""
    return re.sub(r'\s+', '', (s or '').replace('<br>', '').replace('&cr;', '').replace('|', ''))


def cells(line):
    s = line.strip()
    return [c.strip() for c in s[1:-1].split('|')]


def num(v):
    s = sqm(v)
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    if s.startswith('-') and len(s) > 1:
        neg, s = True, s[1:]
    if not re.fullmatch(r'\d{1,3}(,\d{3})*|\d+', s):
        return None
    n = int(s.replace(',', ''))
    return -n if neg else n


def isnumcell(v):
    return num(v) is not None or sqm(v) in ('-', '')


def read_csv(p):
    raw = open(p, 'rb').read()
    if not raw.startswith(b'\xef\xbb\xbf'):
        F(f'(b) BOM 없음 {os.path.relpath(p, ROOT)}')
    rd = csv.reader(open(p, encoding='utf-8-sig', newline=''))
    head = next(rd)
    if head != COLS[p]:
        F(f'(b) 열 이름·순서 다름 {os.path.relpath(p, ROOT)}: {head}')
    rows = [dict(zip(head, x)) for x in rd]
    return rows


# ---------------------------------------------------------------- 출처 목록
REP = {}      # rcept → 사업보고서_원문.csv 행
REPS = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(OUT, '사업보고서_원문.csv'), encoding='utf-8-sig')):
    if r['label'] in G1:
        REP[r['rcept_no']] = r
        REPS[(r['label'], int(r['fy']))].append(r)
BON = {k: [x for x in v if x['kind'] == '본'][0] for k, v in REPS.items()}


class MD:
    def __init__(self, path):
        self.lines = open(os.path.join(ROOT, path), encoding='utf-8').read().split('\n')
        self.heads = {}
        self.hlist = []
        for i, l in enumerate(self.lines):
            m = re.match(r'### \[절 (\d+)\] ?(.*)$', l)
            if m:
                self.heads[int(m.group(1))] = (i, m.group(2).strip())
                self.hlist.append(i)
        self.tables = {}
        for i, l in enumerate(self.lines):
            m = re.fullmatch(r'\[표 (\d+)\]', l)
            if m:
                j = i + 1
                while j < len(self.lines) and self.lines[j] != '[표 끝]':
                    j += 1
                self.tables[int(m.group(1))] = (i, j)

    def sec_range(self, n):
        a = self.heads[n][0]
        b = ([x for x in self.hlist if x > a] or [len(self.lines)])[0]
        return a, b

    def text(self, a, b):
        return '\n'.join(self.lines[a:b])


_MD = {}


def md_of(rcept):
    if rcept not in _MD:
        _MD[rcept] = MD(REP[rcept]['text_path'])
    return _MD[rcept]


_Z = {}


def pdf13(label, n):
    if label not in _Z:
        z = zipfile.ZipFile(ZIP13)
        t = z.read(f'13차_지주관리유형/텍스트/사업보고서__{label}.md').decode('utf-8')
        parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
        _Z[label] = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
    return _Z[label].get(n)


# 연차보고서: URL → 글
ANN_MD = {}   # url → (md 경로, fetched_at, 제목, label, fy)
for r in csv.DictReader(open(os.path.join(OUT, '연차보고서15_목록_g1.csv'), encoding='utf-8-sig')):
    p = f'dart_out/text/ops15/연차보고서__{r["회사"]}__{r["공시연도"]}__{r["공시유형"]}.md'
    if r['파일_url'] and os.path.exists(os.path.join(ROOT, p)):
        ANN_MD[r['파일_url']] = (p, r['fetched_at'], r['제목'], r['회사'], int(r['공시연도']) - 1)
for r in csv.DictReader(open(os.path.join(OUT, '문서목록15b_gov_old.csv'), encoding='utf-8-sig')):
    if r['corp_label'] in G1 and r['status'] == '받음' and r['text_path']:
        ANN_MD.setdefault(r['rcept_no_or_url'], (r['text_path'], r['fetched_at'], r['report_nm'], r['corp_label'], int(r['fy_or_date'][2:])))
GOV_OLD_MD = {}  # (label, fy) → [md 경로]
for r in csv.DictReader(open(os.path.join(OUT, '문서목록15b_gov_old.csv'), encoding='utf-8-sig')):
    if r['corp_label'] in G1 and r['status'] == '받음' and r['text_path']:
        GOV_OLD_MD.setdefault((r['corp_label'], int(r['fy_or_date'][2:])), []).append(r['text_path'])
KIT = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(OUT, 'kit56', '연차보고서_섹션.csv'), encoding='utf-8-sig')):
    if r['지주명'] in G1:
        KIT[(r['지주명'], r['공시연도'], r['공시유형'])].append(r)
ANN_KIT = {}  # url → (key, fetched_at, 제목)
for r in csv.DictReader(open(os.path.join(ROOT, 'handoff', '연차보고서_파일목록.csv'), encoding='utf-8-sig')):
    if r['지주명'] in G1 and (r['지주명'], r['공시연도'], r['공시유형']) in KIT:
        ANN_KIT[r['url']] = ((r['지주명'], r['공시연도'], r['공시유형']), r['fetched_at'], r['제목'])


def md_pages(path):
    t = open(os.path.join(ROOT, path), encoding='utf-8').read()
    parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


_PG = {}


def pages(path):
    if path not in _PG:
        _PG[path] = md_pages(path)
    return _PG[path]


def ann_docs(lab, fy):
    """그 회사·FY 연차보고서의 모든 판 글: [(판 이름, 쪽 사전 또는 섹션 목록, url)]"""
    out = []
    for url, (p, fa, t, l, f) in ANN_MD.items():
        if l == lab and f == fy:
            out.append((t, pages(p), url))
    for url, (k, fa, t) in ANN_KIT.items():
        if k[0] == lab and int(k[1]) - 1 == fy:
            secs = sorted(KIT[k], key=lambda r: (int(r['섹션순번']), int(r['chunk_seq'])))
            out.append((t, {('s', int(s['섹션순번']), int(s['chunk_seq'])): s['본문'] for s in secs}, url))
    return out


def kst_of(ts):
    from datetime import datetime, timezone, timedelta
    if ts.endswith('Z') or ts.endswith('+0000') or ts.endswith('+00:00'):
        d = datetime.strptime(ts.replace('Z', '+0000').replace('+00:00', '+0000'), '%Y-%m-%dT%H:%M:%S%z')
        return d.astimezone(timezone(timedelta(hours=9))).isoformat(timespec='seconds')
    return ts


# ---------------------------------------------------------------- 읽기·꼴 (b)
G = read_csv(F_G)
C = read_csv(F_C)
D = read_csv(F_D)
for name, rows in (('G_g1', G), ('확인_G_g1', C), ('문서목록15b_G_g1', D)):
    for i, r in enumerate(rows):
        for k, v in r.items():
            if v is None or not v.strip():
                # 문서목록: 받지 못한 문서(status ≠ 받음)는 경로·sha256·시각 칸이 빌 수 있음, 받은 문서는 raw_path(원본)·rcept_dt 가 없으면 note 에 사유
                if name == '문서목록15b_G_g1' and k in ('raw_path', 'sha256', 'text_path', 'rcept_dt', 'fetched_at') and r['status'] != '받음':
                    continue
                if name == '문서목록15b_G_g1' and k in ('raw_path', 'rcept_dt') and re.search(r'원본|게시일|공시일|PDF', r['note']):
                    continue
                if name == '문서목록15b_G_g1' and k == 'note':
                    continue
                F(f'(b) 빈칸 {name} #{i + 2} {k} ({r.get("corp_label")} {r.get("fy", r.get("fy_or_date"))} {r.get("item_kind", "")[:20]})')
for i, r in enumerate(G):
    if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00', r['collected_at']):
        F(f'(b) collected_at 꼴 G#{i + 2}: {r["collected_at"]}')
    if r['corp_label'] not in G1:
        F(f'(b) g1 밖 회사 G#{i + 2}: {r["corp_label"]}')
I('b', f'G_g1 {len(G)}행 · 확인 {len(C)}행 · 문서목록 {len(D)}행 — 열 순서·BOM·빈칸 검사')

# ---------------------------------------------------------------- (a) 원문 대조
PAGE_RX = re.compile(r'XML \[절 (\d+)\](?:~\[절 (\d+)\])? 「([^」]*)」(?: \[표 (\d+)\])?')
nmatch = collections.Counter()
for i, r in enumerate(G):
    rid = f'G#{i + 2} {r["corp_label"]} FY{r["fy"]} {r["item_kind"][:24]}'
    texts = [(k, r[k]) for k in ('source_text', 'basis_text') if r[k] != NA]
    if r['source_text'] == NA:
        if not re.search(r'찾은 범위|수집 실패', r['note']):
            F(f'(d) 문서에 없음 행 note 에 찾은 범위·수집 실패 없음 {rid}')
        if r['basis_text'] != NA:
            F(f'(a) source_text 문서에 없음인데 basis_text 있음 {rid}')
    if r['doc_kind'] == '사업보고서':
        rc = r['rcept_no_or_url']
        if rc not in REP:
            F(f'(a) rcept 목록에 없음 {rid} {rc}')
            continue
        rep = REP[rc]
        if r['collected_at'] != rep['fetched_at']:
            F(f'(b) collected_at ≠ 사업보고서_원문.csv fetched_at {rid}')
        if r['doc_name'] != rep['report_nm']:
            F(f'(b) doc_name ≠ report_nm {rid}: {r["doc_name"]}')
        md = md_of(rc)
        m = PAGE_RX.search(r['page'])
        if not m:
            F(f'(a) page 꼴 {rid}: {r["page"]}')
            continue
        n1, n2, title, tn = int(m.group(1)), int(m.group(2) or m.group(1)), m.group(3), m.group(4)
        if n1 not in md.heads or sq(md.heads[n1][1]) != sq(title):
            F(f'(a) page 절 제목 다름 {rid}: [절 {n1}] 「{title}」 vs md 「{md.heads.get(n1, ("", "없음"))[1]}」')
            continue
        a = md.heads[n1][0]
        b = md.sec_range(n2)[1]
        if tn:
            tn = int(tn)
            if tn not in md.tables or not (a < md.tables[tn][0] < b):
                F(f'(a) 표 {tn} 가 [절 {n1}] 안에 없음 {rid}')
                continue
            a, b = md.tables[tn]
            b += 1
        src = sqm(md.text(a, b))
        for k, t in texts:
            if sqm(t) not in src:
                F(f'(a) {k} 가 page 위치 글에 없음 {rid}: 「{t[:60]}」')
            else:
                nmatch['사업보고서'] += 1
                if '&cr;' in md.text(a, b) and sq(t.replace('|', '').replace('<br>', '')) not in sq(md.text(a, b).replace('|', '').replace('<br>', '')):
                    nmatch['&cr; 지우고 맞음'] += 1
        if tn:
            ttxt = sqm(md.text(a, b))
            if not r['item_kind'].startswith('(') and sqm(r['item_kind']) not in ttxt:
                F(f'(a) item_kind 가 표 안에 없음 {rid}')
            if r['counterparty'] != NA and sqm(r['counterparty']) not in ttxt:
                F(f'(a) counterparty 가 표 안에 없음 {rid}: {r["counterparty"]}')
        # 13차 PDF 쪽
        m13 = re.search(r'p\.(\d+)\(본문 PDF, 13차 보관\)', r['page'])
        if m13:
            pg = pdf13(r['corp_label'], int(m13.group(1)))
            if pg is None:
                F(f'(a) 13차 PDF 쪽 없음 {rid} p.{m13.group(1)}')
            else:
                spg = sq(pg)
                mo = re.search(r'원문 숫자 ([\d,()\-]+)', r['note'])
                if mo and '(회사명·원문 숫자)만 있고' in r['note']:
                    if sqm(r['counterparty']) + sq(mo.group(1)) not in spg:
                        F(f'(a) 13차 PDF p.{m13.group(1)} 에 회사명+원문 숫자 없음 {rid}')
                    else:
                        nmatch['13차 쪽(회사명+숫자)'] += 1
                elif mo:
                    if sq(mo.group(1)) not in spg or (not r['item_kind'].startswith('(') and sqm(r['item_kind'])[:8] not in spg):
                        F(f'(a) 13차 PDF p.{m13.group(1)} 에 계정명·원문 숫자 없음 {rid}')
                    else:
                        nmatch['13차 쪽'] += 1
                else:
                    if sqm(r['source_text'])[:40] not in spg:
                        F(f'(a) 13차 PDF p.{m13.group(1)} 에 글 없음 {rid}')
                    else:
                        nmatch['13차 쪽'] += 1
        elif r['fy'] == '2025' and r['source_text'] != NA:
            if '쪽을 못 찾' not in r['note'] and '13차' not in r['note']:
                F(f'(a) FY2025 행에 13차 PDF 쪽 없음·사유도 없음 {rid}')
    else:  # 연차보고서
        url = r['rcept_no_or_url']
        if r['source_text'] == NA:
            continue
        doc = None
        if url in ANN_MD and not re.search(r'섹션순번', r['page']):
            p, fa, t, l, f = ANN_MD[url]
            pg = pages(p)
            if r['collected_at'] != kst_of(fa):
                F(f'(b) collected_at ≠ 연차보고서 목록 fetched_at {rid}: {r["collected_at"]} vs {fa}')
            if not r['doc_name'].startswith(t):
                F(f'(b) doc_name ≠ 제목 {rid}: {r["doc_name"]} vs {t}')
            mp = re.match(r'p\.(\d+)(?:~p\.(\d+))?', r['page'])
            if not mp:
                F(f'(a) 연차 page 꼴 {rid}: {r["page"]}')
                continue
            a, b = int(mp.group(1)), int(mp.group(2) or mp.group(1))
            src = sq(' '.join(pg.get(n, '') for n in range(a, b + 1)))
        elif url in ANN_KIT:
            k, fa, t = ANN_KIT[url]
            if r['collected_at'] != kst_of(fa):
                F(f'(b) collected_at ≠ 연차보고서_파일목록 fetched_at {rid}')
            if not r['doc_name'].startswith(t):
                F(f'(b) doc_name ≠ 제목 {rid}: {r["doc_name"]} vs {t}')
            ms = re.findall(r'섹션순번 (\d+)·chunk (\d+)', r['page'])
            mp = re.match(r'p\.(\d+)', r['page'])
            if not ms or not mp:
                F(f'(a) 6차 섹션 page 꼴 {rid}: {r["page"]}')
                continue
            secs = {(int(s['섹션순번']), int(s['chunk_seq'])): s for s in KIT[k]}
            keys = [(int(x), int(y)) for x, y in ms]
            if any(kk not in secs for kk in keys):
                F(f'(a) 6차 섹션 없음 {rid} {keys}')
                continue
            if secs[keys[0]]['시작페이지'] != mp.group(1):
                F(f'(a) 6차 섹션 시작페이지 다름 {rid}: {secs[keys[0]]["시작페이지"]} vs {mp.group(1)}')
            src = sq(' '.join(secs[kk]['본문'] for kk in keys))
            mg = re.search(r'PDF p\.(\d+)\(gov_old 다시 받은 PDF 쪽 글 ([^)]+\.md)\)', r['page'])
            if mg:
                gp = pages(mg.group(2)).get(int(mg.group(1)), '')
                for kk, tt in texts:
                    if sq(tt) not in sq(gp):
                        F(f'(a) {kk} 가 gov_old PDF p.{mg.group(1)} 에 없음 {rid}')
                    else:
                        nmatch['gov_old PDF 쪽'] += 1
        else:
            F(f'(a) 연차보고서 URL 출처 글 없음 {rid}: {url[:80]}')
            continue
        for kk, tt in texts:
            if sq(tt) not in src:
                F(f'(a) {kk} 가 page 쪽 글에 없음 {rid} ({r["page"][:30]}): 「{tt[:50]}」')
            else:
                nmatch['연차보고서'] += 1
I('a', '원문 대조 맞음 수: ' + ', '.join(f'{k} {v}' for k, v in nmatch.items()))

# 정정판: 같은 FY 정정 md 에 그 행 글이 없으면 note 에 「정정 <rcept>」 이 있어야 함(XML 없는 정정판은 note 에 그 rcept)
njj = collections.Counter()
for i, r in enumerate(G):
    if r['doc_kind'] != '사업보고서' or r['source_text'] == NA:
        continue
    rid = f'G#{i + 2} {r["corp_label"]} FY{r["fy"]} {r["item_kind"][:20]}'
    for x in REPS[(r['corp_label'], int(r['fy']))]:
        if x['kind'] != '정정':
            continue
        if x['text_path'] and os.path.exists(os.path.join(ROOT, x['text_path'])):
            if x['rcept_no'] not in _MD:
                _MD[x['rcept_no']] = MD(x['text_path'])
            if sqm(r['source_text']) not in sqm('\n'.join(_MD[x['rcept_no']].lines)):
                njj['정정 글 다름'] += 1
                if f'정정 {x["rcept_no"]}' not in r['note']:
                    F(f'(a) 정정 {x["rcept_no"]} md 에 같은 글 없는데 note 에 없음 {rid}')
            else:
                njj['정정 같은 글'] += 1
        else:
            njj['정정 XML 없음'] += 1
            if x['rcept_no'] not in r['note']:
                F(f'(a) 정정 {x["rcept_no"]}(XML 없음)이 note 에 없음 {rid}')
I('a', '정정판 대조: ' + ', '.join(f'{k} {v}' for k, v in njj.items()))
# 원문 md: 행 글이 원문/G/<회사>__FY<fy>__<문서>.md 안에 있어야 함
nmd = 0
for i, r in enumerate(G):
    if r['source_text'] == NA:
        continue
    kind = '사업보고서' if r['doc_kind'] == '사업보고서' else '연차보고서'
    pth = os.path.join(OUT, '원문', 'G', f'{r["corp_label"]}__FY{r["fy"]}__{kind}.md')
    if not os.path.exists(pth):
        F(f'(b) 원문 md 없음 G#{i + 2} {os.path.relpath(pth, ROOT)}')
        continue
    if pth not in _PG:
        _PG[pth] = open(pth, encoding='utf-8').read()
    if sqm(r['source_text']) not in sqm(_PG[pth]):
        F(f'(b) 원문 md 에 행 글 없음 G#{i + 2} {r["corp_label"]} FY{r["fy"]} {r["item_kind"][:20]}')
    else:
        nmd += 1
I('b', f'원문 md(dart_out/ops15/원문/G) 안에 행 글 있음 {nmd}행')

# ---------------------------------------------------------------- (c)② 특수관계자 손익 표 다시 뽑기 · (e) 숫자 · (f) direction
TOT0 = re.compile(r'합\s*계|소\s*계|총\s*계|^계$|\s계$')


class _Tot:
    @staticmethod
    def search(x):
        return TOT0.search(x) or sq(x) in ('수익계', '비용계', '채권계', '채무계')


TOT = _Tot
PERIOD = re.compile(r'당기|전기|\(당\)|\(전\)|당\)기|전\)기')


def rp_note_range(md):
    s = [i for i in md.hlist if re.search(r'\] 5\. ?재무제표 ?주석', md.lines[i])][0]
    e = [i for i in md.hlist if i > s and re.search(r'\] \d+\. ?(배당에 ?관한|기타 ?재무에|증권의 ?발행)|\] (IV|Ⅳ)\.', md.lines[i])][0]
    return s, e


INC = re.compile(r'손익내역|손익거래|거래내역|특수관계자거래에대한공시')
EXC = re.compile(r'채권ㆍ채무내역|채권·채무잔액에대한|자금|지분|출자|보증|미사용약정|경영진|리스|사채|고정자산')
RESET = re.compile(r'공시|^<|^당기|^전기')


def candidates(md):
    """별도 주석 안 당기 특수관계자 손익 표 번호 목록(생성기 설정을 쓰지 않음).
    표 앞 글(마지막 「(n)」「n-n」 소항목 뒤)과 표지 표(2줄 이하·숫자 없음)를 이어 「chain」 글로 보고,
    글 없이 바로 이어진 표는 앞 chain 을 이어받음. 표지 표 글이 「…공시」「<…」「당기」「전기」로 시작하면 chain 을 새로 시작."""
    s, e = rp_note_range(md)
    out = []
    prev_end, chain = s, ''
    tabs = sorted((a, b, n) for n, (a, b) in md.tables.items() if s < a < e)
    for a, b, n in tabs:
        prose = sqm(md.text(prev_end + 1, a))
        tbody = [cells(l) for l in md.lines[a + 1:b] if l.startswith('|')]
        is_label = len(tbody) <= 2 and not any(num(c) is not None for row in tbody for c in row)
        label = sqm(md.text(a + 1, b)) if is_label else ''
        if prose:
            chain = re.split(r'\(\d+\)|\d+-\d+\.?', prose)[-1] + label
        elif is_label and RESET.search(label):
            chain = label
        else:
            chain = chain + label
        ctx = sqm(md.text(max(s, a - 150), a))
        cand = '특수관계' in ctx and bool(INC.search(chain)) and (not EXC.search(chain) or '채권ㆍ채무잔액과당기및전기중거래내역' in chain)
        cur = not (re.search(r'<전기[^<]*$', chain) or label.startswith('전기') or label.startswith('<전기'))
        if cand and cur and not is_label:
            out.append(n)
        prev_end = b
    return out


def header_and_rows(md, n):
    a, b = md.tables[n]
    rows = [cells(l) for l in md.lines[a + 1:b] if l.startswith('|')]
    k = 0
    while k < len(rows) and not any(num(c) is not None or sqm(c) == '-' for c in rows[k]):
        k += 1
    head, data = rows[:k], rows[k:]
    # 머리 끝의 한 칸 줄(「<수익>」「종속기업(*1)」 등 묶음 줄)은 data 로
    while head and len(head[-1]) == 1 and len(head) > 1 and not PERIOD.search(head[-1][0]) and '단위' not in head[-1][0]:
        data.insert(0, head.pop())
    return head, data, md.text(a, b + 1)


def parse_rp(md, n):
    """→ [(counterparty, item, 원문 칸, 금액, group, 줄 글)] 당기만, 0·-·빈칸·합계 제외."""
    head, data, ttxt = header_and_rows(md, n)
    out = []
    H = [c for c in (head[-1] if head else [])]
    Hall = ' '.join(' '.join(h) for h in head)
    lines = [l for l in ttxt.split('\n') if l.startswith('|')][len(head):]
    def keylen(row):
        k = 0
        while k < len(row) and not isnumcell(row[k]):
            k += 1
        return k
    if H and any(PERIOD.search(c) for c in H) and not (H and H[0] == ''):
        # long: 머리 = 키 열들 + 기간 열들
        keys = [c for c in H if not PERIOD.search(c)]
        nv = len(H) - len(keys)
        roles = ['item' if '계정' in c else 'cp' if ('회사' in c or '특수관계자' in c) else 'grp' for c in keys]
        cur = {x: '' for x in roles}
        grp = ''
        for row, line in zip(data, lines):
            if len(row) == 1 and num(row[0]) is None:
                grp = row[0].strip('<>')
                continue
            if TOT.search(row[0].replace('<br>', ' ')):
                continue
            kl = keylen(row)
            vals = row[kl:]
            if len(vals) != nv or kl > len(keys):
                if any(num(c) for c in row):
                    I('c', f'칸 수 다른 줄(건너뜀 — 확인) 표 {n}: {line[:80]}')
                continue
            for role, v in zip(roles[len(roles) - kl:], row[:kl]):
                cur[role] = v
            idx_roles = roles[len(roles) - kl:]
            if 'cp' in idx_roles and 'item' not in idx_roles and kl:
                pass
            g = cur.get('grp', '') or grp
            if any(TOT.search(cur.get(x, '').replace('<br>', ' ')) for x in ('cp', 'item', 'grp')):
                continue
            v = vals[0]
            x = num(v)
            if x:
                out.append((cur.get('cp', ''), cur.get('item', ''), v, x, g or grp, line))
        return out
    if H and '금액' in H:
        # NH: 구분 | 계정과목 | 특수관계자 | 금액 (금액 1열, 기간은 표지 표)
        keys = H[:-1]
        roles = ['grp' if '구분' in c else 'item' if '계정' in c else 'cp' for c in keys]
        cur = {x: '' for x in roles}
        for row, line in zip(data, lines):
            kl = keylen(row)
            vals = row[kl:]
            if len(vals) != 1:
                continue
            for role, v in zip(roles[len(roles) - kl:], row[:kl]):
                cur[role] = v
            if any(TOT.search(cur.get(x, '').replace('<br>', ' ')) for x in ('cp', 'item', 'grp')):
                continue
            if sq(cur['grp']) not in ('수익', '비용'):
                continue
            x = num(vals[0])
            if x:
                out.append((cur['cp'], cur['item'], vals[0], x, cur['grp'], line))
        return out
    if head and head[-1] and head[-1][0] == '' and len(head) >= 3 and not any('수익' in c and ',' in c for c in head[-1]):
        # wide: 마지막 머리 줄 = 회사 열, 행 머리 = 계정
        comps = head[-1][1:]
        total_col = '합계' in sq(Hall)
        for row, line in zip(data, lines):
            item, vals = row[0], row[1:]
            if TOT.search(item.replace('<br>', ' ')):
                continue
            if len(vals) != len(comps) + (1 if total_col else 0):
                I('c', f'칸 수 다른 줄(건너뜀 — 확인) 표 {n}: {line[:80]}')
                continue
            for cp, v in zip(comps, vals[:len(comps)]):
                x = num(v)
                if x:
                    out.append((cp, item, v, x, '', line))
        return out
    # acct(하나): 열 = 계정, 행 = 회사
    if len(head) >= 2 and head[0][0] in ('특수관계자', ''):
        top, leaf = head[0], head[1]
        if top[0] == '특수관계자':
            nkey = 2
            singles = [c for c in top[nkey:]]
            lv = [c for c in leaf if c]
            cols = []
            rev = [c for c in lv if c.endswith('수익')]
            cst = [c for c in lv if not c.endswith('수익')]
            for c in singles:
                if sq(c) == '수익':
                    cols += [(x, '수익') for x in rev]
                elif sq(c) == '비용':
                    cols += [(x, '비용') for x in cst]
                else:
                    cols.append((c, ''))
        else:
            nkey = sum(1 for c in leaf if c == '')
            cols = [(c, '') for c in leaf[nkey:]]
        for row, line in zip(data, lines):
            if TOT.search(row[0].replace('<br>', ' ')):
                continue
            kl = keylen(row)
            vals = row[kl:]
            if kl == 0 or len(vals) != len(cols):
                if any(num(c) for c in row):
                    I('c', f'칸 수 다른 줄(건너뜀 — 확인) 표 {n}: {line[:80]}')
                continue
            cp = row[kl - 1] if top[0] == '' else row[0]
            if any(TOT.search(c.replace('<br>', ' ')) for c in row[:kl]):
                continue
            for (item, g), v in zip(cols, vals):
                if TOT.search(item.replace('<br>', ' ')):
                    continue
                x = num(v)
                if x:
                    out.append((cp, item, v, x, g, line))
        return out
    I('c', f'표 꼴을 모름 — 표 {n} 머리 {Hall[:80]}')
    return out


def unit_ok(md, n):
    a, b = md.tables[n]
    return '백만원' in sq(md.text(max(0, a - 40), b))


def exp_direction(item, amount, group):
    g = sq(group)
    if g in ('수익',):
        return '지주 수입', False
    if g in ('비용',):
        return '지주 지출', False
    it = re.sub(r'\(\*\d*\)|\(\*\)', '', sqm(item))
    it = it.split(',')[0]
    if it.endswith('수익') and not it.endswith('손익'):
        return '지주 수입', False
    if re.search(r'(비용|관리비|상각비)$', it):
        return '지주 지출', False
    return None, True


rp_rows = [(i, r) for i, r in enumerate(G) if r['doc_kind'] == '사업보고서' and re.search(r'\[표 \d+\]', r['page'])
           and r['amount_krw'] not in (NA, '') and '특수관계' in r['section_title']]
by_table = collections.defaultdict(list)
for i, r in rp_rows:
    tn = int(re.search(r'\[표 (\d+)\]', r['page']).group(1))
    by_table[(r['rcept_no_or_url'], tn)].append((i, r))
num_samples = []
num_checked = [0]
cand_all = set()
for (lab, fy), rep in sorted(BON.items()):
    if not (2019 <= fy <= 2025):
        continue
    md = md_of(rep['rcept_no'])
    cands = candidates(md)
    for n in cands:
        cand_all.add((rep['rcept_no'], n))
    claimed = sorted(t for (rc, t) in by_table if rc == rep['rcept_no'])
    cands = [n for n in cands if parse_rp(md, n) or n in claimed]
    if sorted(cands) != claimed:
        F(f'(c) 표 고름 다름 {lab} FY{fy}: 다시 찾은 당기 손익 표 {cands} · 조각 {claimed}')
    if not cands:
        F(f'(c) 특수관계자 손익 표를 못 찾음 {lab} FY{fy}')
    for n in cands:
        exp = parse_rp(md, n)
        if not unit_ok(md, n):
            F(f'(e) 표 {n} 앞뒤에 「백만원」 없음 {lab} FY{fy}')
        got = by_table.get((rep['rcept_no'], n), [])
        ek = collections.Counter((sqm(cp), sqm(it), x) for cp, it, v, x, g, l in exp)
        gk = collections.Counter((sqm(r['counterparty']), sqm(r['item_kind']), int(r['amount_krw']) // 1000000 if int(r['amount_krw']) >= 0 else -(-int(r['amount_krw']) // 1000000))
                                 for i, r in got)
        miss = ek - gk
        extra = gk - ek
        for k in list(miss)[:10]:
            F(f'(c) 조각에 없는 당기 칸 {lab} FY{fy} 표 {n}: {k}')
        for k in list(extra)[:10]:
            F(f'(c) 다시 뽑은 칸에 없는 조각 행 {lab} FY{fy} 표 {n}: {k}')
        I('c', f'{lab} FY{fy} 표 {n}: 다시 뽑은 당기 칸 {sum(ek.values())} · 조각 행 {len(got)}' + (' OK' if not miss and not extra else ' 다름'))
        emap = collections.defaultdict(list)
        for cp, it, v, x, g, l in exp:
            emap[(sqm(cp), sqm(it), x)].append((v, g, l))
        for i, r in got:
            rid = f'G#{i + 2} {lab} FY{fy} {r["counterparty"]} {r["item_kind"]}'
            amt = int(r['amount_krw'])
            mo = re.search(r'원문 숫자 ([\d,()\-]+)', r['note'])
            if not mo or '원문 단위 백만원' not in r['note']:
                F(f'(e) note 에 원문 단위·원문 숫자 없음 {rid}')
                continue
            if num(mo.group(1)) is None or num(mo.group(1)) * 1000000 != amt:
                F(f'(e) amount_krw ≠ 원문 숫자 × 1,000,000 {rid}: {amt} vs {mo.group(1)}')
            key = (sqm(r['counterparty']), sqm(r['item_kind']), num(mo.group(1)) or 0)
            if key in emap:
                v, g, l = emap[key][0]
                if sqm(v) != sqm(mo.group(1)):
                    F(f'(e) 원문 숫자 칸 글 다름 {rid}: {v} vs {mo.group(1)}')
                if sqm(r['source_text']) != sqm(l):
                    F(f'(a) source_text 가 그 칸의 표 줄과 다름 {rid}')
                d, judge = exp_direction(r['item_kind'], amt, g)
                if d is None:
                    if '(판단)' not in r['note']:
                        F(f'(f) direction 기준 밖인데 (판단) 없음 {rid}: {r["direction"]}')
                    else:
                        # (판단) 규칙: 손익·전입(환입) → 부호
                        it = sqm(r['item_kind'])
                        exp_d = None
                        if '손익' in it:
                            exp_d = '지주 수입' if amt > 0 else '지주 지출'
                        elif re.search(r'전입\(환입|전입액|전\(환\)입|전입$', it):
                            exp_d = '지주 지출' if amt > 0 else '지주 수입'
                        elif re.search(r'환입\(전입|환\(전\)입', it):
                            exp_d = '지주 수입' if amt > 0 else '지주 지출'
                        elif it.endswith('환입') or it.endswith('환입액'):
                            exp_d = '지주 수입' if amt > 0 else '지주 지출'
                        elif '제공받은용역' in it:
                            exp_d = '지주 지출'
                        if exp_d and exp_d != r['direction']:
                            F(f'(f) (판단) direction 이 스크립트 머리 규칙과 다름 {rid}: {r["direction"]} vs {exp_d}')
                        if exp_d is None:
                            I('f', f'(판단) 규칙 밖 계정 — 눈으로 봄 {rid}: {r["direction"]}')
                elif d != r['direction']:
                    F(f'(f) direction 다름 {rid}: {r["direction"]} vs 기준 {d}(묶음 「{g}」)')
                num_checked[0] += 1
                if len(num_samples) < 400:
                    num_samples.append(f'{lab} FY{fy} 표 {n} {r["counterparty"]}·{r["item_kind"]}: 원문 칸 「{v}」 백만원 → amount_krw {amt} OK')
missing_tables = [k for k in by_table if k not in cand_all]
for k in missing_tables:
    F(f'(c) 조각이 쓴 표가 다시 찾은 당기 손익 표 목록에 없음 {k}')

# 배당·브랜드 행(특수관계자 표 밖)
for i, r in enumerate(G):
    if r['doc_kind'] != '사업보고서' or r['amount_krw'] in (NA, '') or '특수관계' in r['section_title']:
        continue
    rid = f'G#{i + 2} {r["corp_label"]} FY{r["fy"]} {r["item_kind"]}'
    mo = re.search(r'원문 숫자 ([\d,()\-]+)', r['note'])
    vals = [c for c in cells(r['source_text']) if num(c) is not None]
    if not mo or not vals or num(vals[0]) != num(mo.group(1)) or num(mo.group(1)) * 1000000 != int(r['amount_krw']):
        F(f'(e) 배당·브랜드 행 금액 {rid}: {r["amount_krw"]} / {mo.group(1) if mo else "-"} / {vals[:2]}')
    else:
        md = md_of(r['rcept_no_or_url'])
        tn = int(re.search(r'\[표 (\d+)\]', r['page']).group(1))
        a, b = md.tables[tn]
        pre = sq(md.text(max(0, a - 30), a + 2))
        tb = [cells(l) for l in md.lines[a + 1:b] if l.startswith('|')]
        hd = ' '.join(' '.join(x) for x in tb[:2])
        # 당기 열이 첫 금액 열인지(머리에 당기가 전기보다 먼저 또는 표지 「당기」)
        ok_period = ('당기' in pre[-60:] and '전기' not in pre[-12:]) or re.search(r'당\s*기.*전\s*기', hd) or re.search(r'\(당\)', hd)
        if not ok_period:
            F(f'(e) 배당·브랜드 행 당기 열 확인 못 함 {rid}')
        if not unit_ok(md, tn):
            F(f'(e) 배당·브랜드 행 표 앞뒤 「백만원」 없음 {rid}')
        if r['direction'] != '지주 수입':
            F(f'(f) 배당·브랜드 행 direction {rid}')
        num_checked[0] += 1
        num_samples.insert(0, f'{r["corp_label"]} FY{r["fy"]} [표 {tn}] {r["item_kind"]}: 원문 칸 「{vals[0]}」 백만원 → amount_krw {r["amount_krw"]} OK')
I('e', f'숫자 대조 {num_checked[0]}행(특수관계자 표 칸 전부 + 배당·브랜드 행) — 표본 40개는 아래(배당·브랜드 행 먼저)')

# ---------------------------------------------------------------- (f) note·section_title 낱말
for i, r in enumerate(G):
    rid = f'G#{i + 2} {r["corp_label"]} FY{r["fy"]} {r["item_kind"][:24]}'
    unq = re.sub(r'「[^」]*」', '', r['note'] + ' ' + r['section_title']).replace('사업목적', '')
    for w in BAD_WORDS:
        if w in unq:
            F(f'(f) note·section_title 에 추정 낱말 「{w}」 {rid}')
    if not r['section_title'].strip() or r['section_title'].startswith('같은 문단'):
        F(f'(f) section_title 이 비었거나 note 글 {rid}: 「{r["section_title"][:40]}」')
    if r['direction'] not in ('지주 수입', '지주 지출', NA):
        F(f'(f) direction 값 {rid}: {r["direction"]}')
    if r['direction'] != NA and r['item_kind'].startswith('(') and '(판단)' not in r['note']:
        F(f'(f) 문단 행 direction 에 (판단) 없음 {rid}')
    if r['amount_krw'] != NA and not re.fullmatch(r'-?\d+', r['amount_krw']):
        F(f'(e) amount_krw 꼴 {rid}: {r["amount_krw"]}')

# ---------------------------------------------------------------- (c)① 범위
have = collections.defaultdict(set)
for r in G:
    have[(r['corp_label'], int(r['fy']))].add((r['doc_kind'], r['item_kind'] if r['item_kind'].startswith('(') else ('RP' if '특수관계' in r['section_title'] else r['item_kind'])))
for lab in G1:
    for fy in range(2019, 2026):
        h = have[(lab, fy)]
        if ('사업보고서', 'RP') not in h:
            F(f'(c) 특수관계자 손익 행 없음 {lab} FY{fy}')
        if ('사업보고서', I_BASIS) not in h and not (lab == '신한금융지주' and ('사업보고서', '브랜드수수료') in h):
            F(f'(c) (산정 기준 문단) 행·브랜드 행 없음 {lab} FY{fy}')
    if ('사업보고서', I_PAY) not in have[(lab, 2025)]:
        F(f'(c) FY2025 Ⅷ 행 없음 {lab}')
    for fy in (range(2017, 2026) if lab in ('KB금융지주', '신한금융지주', '하나금융지주') else range(2019, 2026)):
        h = have[(lab, fy)]
        if ('지배구조 및 보수체계 연차보고서', I_PAY) not in h:
            F(f'(c) 연차보고서 (겸직 임원 보수 지급·배분 기준) 행 없음 {lab} FY{fy}')
        if lab in ('KB금융지주', '신한금융지주', '하나금융지주') and ('지배구조 및 보수체계 연차보고서', I_DIV) not in h:
            F(f'(c) 연차보고서 (겸직 부문장 성과평가·보수) 행 없음 {lab} FY{fy}')
    for fy in range(2019, 2026):
        if not ann_docs(lab, fy) and lab != 'NH농협금융지주':
            F(f'(c) 연차보고서 글 없음 {lab} FY{fy}')

# ---------------------------------------------------------------- (c)③·(d) 키워드 직접 grep·반박
# REVIEWED: (회사, fy 또는 '*', 글 조각(공백 지운 글 안에 있으면 걸림)) → 검토 결과(사실). 조각에 없는 걸림 글은 여기 있어야 통과.
REVIEWED = [
    ('*', '*', 'BoardSkillMatrix', '이사회 역량 표(Board Skill Matrix) — 부문장 평가·보수 글 아님'),
    ('*', '*', 'BoardSkillsMatrix', '이사회 역량 표(Board Skills Matrix) — 부문장 평가·보수 글 아님'),
    ('*', '*', '주요경력', '이사·후보 주요 경력 서술(부문장 경력) — 평가·보수 글 아님'),
    ('*', '*', '부문장및담당경영진등과미팅', '사외이사 활동(경영진 미팅) — 평가·보수 글 아님'),
    ('KB금융지주', '*', '당사(원소속회사기준)의성과보상대상자', '성과보상 대상자 수의 기준 「당사(원소속회사 기준)」 — 같은 쪽 「이와 별도로 원소속회사가 자회사인 겸직 경영진…」 주석은 조각 행에 있음'),
    ('신한금융지주', '*', '비상임이사(겸직비상임이사는제외)에대한평가기준', '비상임이사 평가기준 서술 — 보수 지급 회사·배분 글 아님(보수 조항은 그 해 지배구조 내부규범 행)'),
    ('신한금융지주', 2017, '그룹겸직경영진평가및보수체계에관한사항', '보수위원회 의결안건 표 — 같은 회의 서술(「그룹 GIB, 글로벌 사업부문 겸직구조 확대…」)은 그 해 (겸직 부문장 성과평가·보수) 행에 있음'),
    ('*', '*', '감사겸직여부', '사외이사 자격요건 확인 표(다른 회사 임원 겸직 여부)'),
    ('*', '*', '현재겸직업무', '사외이사 후보 소명 항목(현재 겸직 업무)'),
    ('*', '*', '추가로겸직한사실', '사외이사 겸직 변동 서술'),
    ('*', '*', '다른회사의사외이사를겸직하', '사외이사 자격요건 서술'),
    ('*', '*', '겸직하지않아', '사외이사 자격요건 서술'),
    ('신한금융지주', 2025, '사외이사결격요건', '사외이사 자격요건 확인 표 — 보수 글 아님'),
    ('신한금융지주', '*', '겸직사업부문활성화를위한', '경영진 선임 결의 — 보수 글 아님'),
    ('신한금융지주', '*', '겸직부사장보', '경영진 선임 결의 내역 — 보수 글 아님'),
    ('신한금융지주', '*', '이사회사무국장이타부서장을겸직하는경우', '이사회사무국 직원 평가등급 기준(지주 안 부서장 겸직) — 그룹사 간 겸직 부문장 글 아님'),
    ('*', '*', '임직원겸직및업무위탁에대한평가', '그룹 내부통제 규정의 겸직·업무위탁 평가·관리 조항 — 보수 글 아님'),
    ('*', '*', '임직원겸직또는업무위탁을하고자하는경우', '그룹 내부통제 규정의 겸직·업무위탁 조항 — 보수 글 아님'),
    ('신한금융지주', '*', '그룹Matrix운영현황이사회보고요청', '사외이사 활동(그룹 Matrix 운영현황 보고 요청) — 평가·보수 글 아님'),
    ('신한금융지주', '*', '신한DS대표이사를겸직하는그룹디지털부문장을선임', '경영진 선임 결의 — 보수 글 아님'),
    ('신한금융지주', '*', '그룹디지털사업부문장후보로추천', '경영진 후보 추천 결의 — 보수 글 아님'),
    ('신한금융지주', '*', '고유재산운용임원겸직', '금감원 검사 지적 서술(겸직 이해상충 내부통제) — 보수 글 아님'),
    ('신한금융지주', '*', '겸직사업그룹장을거친', '경영승계 후보군 요건 서술 — 보수 글 아님'),
    ('신한금융지주', '*', '지주회사경영진및겸직사업그룹장선임', '경영진 선임 결의 — 보수 글 아님'),
    ('신한금융지주', '*', '은행장을겸임하는비상임이사의의결권', '이사회 의결권 제한 서술 — 보수 글 아님'),
    ('*', '*', '겸임교수', '사외이사 경력(겸임교수)'),
    ('*', '*', '회계기준원소속', '기부 내역 표(「한국회계기준원 소속」 글자) — 겸직 글 아님'),
    ('*', '*', '임원제외/겸직포함', '준법감시 직원 비율 표(겸직 포함 인원) — 보수 글 아님'),
    ('하나금융지주', '*', '관계사겸직직원', '부서 인원 표 주석(관계사 겸직 직원 포함) — 보수 글 아님'),
    ('하나금융지주', '*', '관계회사겸직직원', '부서 인원 표 주석(관계회사 겸직 직원 포함) — 보수 글 아님'),
    ('하나금융지주', '*', '전결권자가부문장이상', '일상감사 대상 업무 서술 — 평가·보수 글 아님'),
    ('하나금융지주', '*', '부문장이상인경우와전결권자가', '일상감사 대상 업무 서술 — 평가·보수 글 아님'),
    ('하나금융지주', 2020, '그룹임직원겸직제도운영절차강화', '금감원 검사 결과 개선요구사항 목록 항목 — 보수 지급 회사·배분 글 아님'),
    ('*', '*', '사외이사는본인이겸직하고있는외부기관', '사외이사 직무 규정(겸직 외부기관 거래) — 보수 글 아님'),
    ('하나금융지주', 2021, '은행장이지주회사비상임이사를겸직', '이사 후보 추천 서술 — 보수 글 아님'),
    ('*', '*', '감사부문장', '감사부문장 위임·임면 서술 — 겸직 부문장 평가·보수 글 아님'),
    ('*', '*', '위원장을겸직하며', '사외이사 위원장 겸직 서술'),
    ('우리금융지주', 2019, '다.임직원겸직時비용분담', '같은 회의(2019.7.25 제8차 이사회) 사외이사 찬반 표의 안건 이름 — 안건 글은 같은 쪽 (H) 문단 행에 있음'),
    ('우리금융지주', 2024, '사외이사의지주·은행겸직구조해소', '금감원 지배구조 경영유의사항 목록 — 보수 글 아님'),
    ('*', '*', '감사위원회위원은리스크관리위원회위원을겸임', '위원회 구성 규정(겸임 제한) — 보수 글 아님'),
]
REV_HIT = collections.Counter()


def reviewed(lab, fy, ctx):
    for (l, f, frag, why) in REVIEWED:
        if (l in ('*', lab)) and (f in ('*', fy)) and sq(frag) in ctx:
            REV_HIT[(l, f, frag)] += 1
            return why
    return None


G_SRC = collections.defaultdict(str)
G_SRCM = collections.defaultdict(str)
for r in G:
    G_SRC[(r['corp_label'], int(r['fy']))] += sq(r['source_text']) + '¶' + sq(r['basis_text']) + '¶'
    G_SRCM[(r['corp_label'], int(r['fy']))] += sqm(r['source_text']) + '¶' + sqm(r['basis_text']) + '¶' + sqm(r['note']) + '¶'
# 사업보고서 걸림 줄 검토 규칙(줄 글 sqm 에 정규식) — 사유는 사실만. 「사용료·사용수수료·브랜드수수료·산정·요율」이 함께 있는 줄은 규칙으로 넘기지 않음.
BR_RULES = [
    ('Ⅱ', r'^(?!.*(사용료|사용수수료|브랜드수수료|산정|요율)).*(브랜드|로열티|Brand|BRAND)', '자회사 영업·상품·수상·연혁 서술 — 지주 수익·사용료 산정 기준 글 아님'),
    ('Ⅱ', r'장관상표창|상표창', '수상 서술(「장관상 표창」의 글자) — 상표권 글 아님'),
    ('Ⅱ', r'자신의상표,상호등을사용하여', 'KB스타플랫폼 간편결제 서비스 설명(제휴사 상표) — 지주 수익 글 아님'),
    ('Ⅱ', r'^\(4\)경영자문수수료수익[\d,\-]+$', '자회사 KB인베스트먼트 영업수익 표의 계정(같은 절 「KB인베스트먼트」 서술 안) — 지주(별도) 수익 아님'),
    ('Ⅱ', r'경영자문서비스|필요한경영자문', '자회사(벤처캐피탈) 업무 서술 — 지주 수익 글 아님'),
    ('Ⅱ', r'국제브랜드수수료', '카드 상품 서술(해외 결제 국제브랜드수수료 면제) — 지주 수익 글 아님'),
    ('Ⅱ', r'브랜드사용수수료손익', '연결 영업실적 산식의 계정 낱말 — 산정 기준 문단 아님(같은 해 (산정 기준 문단) 행 note 에 적음)'),
    ('별도 주석', r'^상표권[\d(),\-]+$|소프트웨어상표권|^상표권$', '무형자산(상표권) 장부금액·변동 표 — 수익 계정 아님'),
    ('별도 주석', r'^총수수료수익브랜드수수료71,038$', 'FY2025 순수수료손익 전기 표의 행(전기 금액) — 당기 표 행(71,037)은 조각에 있음'),
    ('별도 주석', r'금융용역수수료를그수수료의부과목적|용역을제공함으로써가득되는수수료|용역제공이완료된시점|하나의용역|용역의제공', '수수료 수익 인식 회계정책 서술 — 특수관계자 거래 계정 아님'),
    ('Ⅷ', r'개인성과평가결과에따라차등배분', '성과급 개인별 차등 배분 서술 — 「겸직」 낱말 없음'),
    ('Ⅷ', r'근로소득지급명세서대상자기준\(원소속기준\)으로작성', '주식기준보상 부여 인원 수 산정 기준 주석(「원소속 기준」) — 「겸직」 낱말·보수 지급 회사 글 없음(KB FY2025 Ⅷ 행 note 에 적음)'),
]


def br_rule(where, line):
    t = sqm(line)
    for w, rx, why in BR_RULES:
        if w == where and re.search(rx, t):
            return why
    return None


grep_lines = []
BR_KW = re.compile(r'브랜드|상표|로열티|Brand|BRAND|경영관리수수료|경영관리용역|경영자문|용역수수료|용역수익|사용수수료')
for (lab, fy), rep in sorted(BON.items()):
    if not (2019 <= fy <= 2025):
        continue
    md = md_of(rep['rcept_no'])
    s, e = rp_note_range(md)
    sec2 = [i for i in md.hlist if re.search(r'\] (II|Ⅱ)\. ?사업의 ?내용', md.lines[i])][0]
    sec3 = [i for i in md.hlist if i > sec2 and re.search(r'\] (III|Ⅲ)\. ?재무에 ?관한', md.lines[i])][0]
    s8 = [i for i in md.hlist if re.search(r'임원의 ?보수', md.lines[i])][0]
    e8 = [x for x in md.hlist if x > s8][0]
    for (a, b, where, kw) in ((s, e, '별도 주석', BR_KW), (sec2, sec3, 'Ⅱ', BR_KW), (s8, e8, 'Ⅷ', re.compile(r'겸직|겸임|분담|원소속|배분'))):
        for j in range(a, b):
            l = md.lines[j]
            t = sqm(l)
            ms = list(kw.finditer(t))
            if not ms:
                continue
            in_g = all(t[max(0, m.start() - 6):m.end() + 6] in G_SRCM[(lab, fy)] for m in ms)
            why = None if in_g else br_rule(where, l)
            grep_lines.append(f'{lab} FY{fy} {where} md {j + 1}: {"조각에 있음" if in_g else ("검토: " + why) if why else "검토 없음"} — 「{l.strip()[:120]}」')
            if not in_g and not why:
                F(f'(c) 조각에 없는 키워드 줄(검토 안 됨) {lab} FY{fy} {where} md {j + 1}: 「{l.strip()[:80]}」')

PAYW = r'보수|보상|성과급|인건비|분담|배분|정산|지급|급여|부담|평가|KPI|가중치|비중|수당'
for lab in G1:
    for fy in range(2017, 2026):
        if lab in ('우리금융지주', 'NH농협금융지주') and fy < 2019:
            continue
        seen = set()
        for (t, pg, url) in ann_docs(lab, fy):
            for key, body in pg.items():
                flat = sq(body)
                for m in re.finditer(r'겸직|겸임|겸무|원소속|사업그룹장|사업부문장|부문장|Matrix|매트릭스', flat):
                    a, b = max(0, m.start() - 120), m.end() + 120
                    ctx = flat[a:b]
                    if m.group() in ('겸직', '겸임', '겸무', '원소속'):
                        if not re.search(PAYW, ctx):
                            continue
                    elif lab not in ('KB금융지주', '신한금융지주', '하나금융지주') or not re.search(r'성과평가|평가체계|KPI|평가지표|보수체계|비중|가중치', flat[max(0, m.start() - 60):m.end() + 60]):
                        continue
                    frag = flat[max(0, m.start() - 30):m.end() + 30]
                    if frag in seen:
                        continue
                    seen.add(frag)
                    in_g = (flat[m.start():m.end() + 12] in G_SRC[(lab, fy)]) or (flat[max(0, m.start() - 12):m.end()] in G_SRC[(lab, fy)])
                    why = None if in_g else reviewed(lab, fy, ctx)
                    pgl = f'p.{key}' if isinstance(key, int) else f'섹션 {key[1]}·{key[2]}'
                    grep_lines.append(f'{lab} FY{fy} 연차 {pgl}: {"조각에 있음" if in_g else ("검토: " + why) if why else "검토 없음"} — 「{flat[max(0, m.start() - 70):m.end() + 90]}」')
                    if not in_g and not why:
                        F(f'(d) 연차보고서 겸직·보수 근처 글이 조각에 없음(검토 안 됨) {lab} FY{fy} {pgl}: 「{ctx[60:200]}」')
for (l, f, frag, why) in REVIEWED:
    if not REV_HIT[(l, f, frag)]:
        I('d', f'REVIEWED 안 쓰인 줄: {l} {f} {frag[:30]}')

# ---------------------------------------------------------------- (g) 확인 CSV
REQ = open(os.path.join(OUT, 'REQUEST15b.md'), encoding='utf-8').read().split('\n')
gi = [i for i, l in enumerate(REQ) if l.startswith('작업 G.')][0]
gj = [i for i, l in enumerate(REQ) if i > gi and l.startswith('* G-2')][0]
ki = [i for i in range(gi, gj) if '특히 볼 것' in REQ[i]][0]
ITEMS = [REQ[i].strip().lstrip('*').strip() for i in range(ki + 1, gj) if REQ[i].strip()]
if len(ITEMS) != 4:
    F(f'(g) REQUEST 「특히 볼 것」 줄 수 {len(ITEMS)}')
need = {ITEMS[0]: [(l, 2025) for l in ('KB금융지주', '하나금융지주', '우리금융지주')],
        ITEMS[1]: [('신한금융지주', 2025)],
        ITEMS[2]: [(l, 2025) for l in G1],
        ITEMS[3]: [(l, fy) for l in ('신한금융지주', 'KB금융지주', '하나금융지주') for fy in range(2017, 2026)]}
for it in ITEMS:
    if not any(c['item_text'] == it for c in C):
        F(f'(g) 확인 CSV 에 item_text 없음: {it[:40]}')
for it, lst in need.items():
    for (lab, fy) in lst:
        if not any(c['item_text'] == it and c['corp_label'] == lab and str(fy) in re.findall(r'\d{4}', c['fy']) or
                   (c['item_text'] == it and c['corp_label'] == lab and c['fy'] == str(fy)) for c in C):
            F(f'(g) 확인 행 없음 {it[:20]} {lab} FY{fy}')
for i, c in enumerate(C):
    cid = f'확인#{i + 2} {c["item_id"]} {c["corp_label"]} {c["fy"]}'
    if c['item_text'] not in ITEMS:
        F(f'(g) item_text 가 REQUEST 줄 글 그대로가 아님 {cid}')
    if c['result'] not in ('원문 있음', NA, '수집 실패'):
        F(f'(g) result 값 {cid}: {c["result"]}')
    if len(c['source_excerpt']) > 300:
        F(f'(g) source_excerpt 300자 넘음 {cid}')
    for w in BAD_WORDS:
        if w in re.sub(r'「[^」]*」', '', c['note']).replace('사업목적', ''):
            F(f'(g) note 에 추정 낱말 「{w}」 {cid}')
    fys = [int(x) for x in re.findall(r'\d{4}', c['fy'])]
    fyr = range(fys[0], fys[-1] + 1) if fys else []
    rows = [r for r in G if r['corp_label'] == c['corp_label'] and int(r['fy']) in fyr]
    if c['result'] == '원문 있음':
        if not any(sq(c['source_excerpt']) and sq(c['source_excerpt']) in sq(r['source_text']) for r in rows):
            F(f'(g) 원문 있음인데 source_excerpt 가 조각 같은 회사·FY 행 글 안에 없음 {cid}')
    else:
        if c['source_excerpt'] != NA:
            F(f'(g) 문서에 없음인데 source_excerpt 있음 {cid}')
# 항목별 result ↔ 조각
for i, c in enumerate(C):
    cid = f'확인#{i + 2} {c["item_id"]} {c["corp_label"]} {c["fy"]}'
    fys = [int(x) for x in re.findall(r'\d{4}', c['fy'])]
    fyr = range(fys[0], fys[-1] + 1) if fys else []
    rows = [r for r in G if r['corp_label'] == c['corp_label'] and int(r['fy']) in fyr]
    if c['item_text'] == ITEMS[2]:
        rr = [r for r in rows if r['doc_kind'] == '사업보고서' and r['item_kind'] == I_PAY]
        exp = '원문 있음' if any(r['source_text'] != NA for r in rr) else NA
        if c['result'] != exp:
            F(f'(g) G-3 result 가 조각과 다름 {cid}: {c["result"]} vs {exp}')
    if c['item_text'] == ITEMS[3]:
        rr = [r for r in rows if r['doc_kind'] != '사업보고서' and r['item_kind'] == I_DIV]
        exp = '원문 있음' if any(r['source_text'] != NA for r in rr) else NA
        if c['result'] != exp:
            F(f'(g) G-4 result 가 조각과 다름 {cid}: {c["result"]} vs {exp}')
    if c['item_text'] == ITEMS[0]:
        brand = [r for r in rows if re.search(r'브랜드|상표', r['item_kind'])]
        mg = [r for r in rows if re.search(r'경영관리|용역', r['item_kind']) and r['direction'] == '지주 수입']
        exp = '원문 있음' if (brand if c['item_id'] == 'G-1' else mg) else NA
        if c['result'] != exp:
            F(f'(g) G-1 result 가 조각과 다름 {cid}: {c["result"]} vs {exp}')

# ---------------------------------------------------------------- (h) 비밀·추적 경로
key = os.environ.get('DART_API_KEY', '')
mine = [F_G, F_C, F_D, os.path.join(ROOT, 'scripts', 'dart', 'ops15b_G_g1.py')]
mdd = os.path.join(OUT, '원문', 'G')
mine += [os.path.join(mdd, x) for x in os.listdir(mdd) if x.split('__')[0] in G1]
HEX40 = re.compile(r'(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])')
for p in mine:
    t = open(p, encoding='utf-8', errors='replace').read()
    if key and key in t:
        F(f'(h) DART_API_KEY 값이 파일에 있음 {os.path.relpath(p, ROOT)}')
    if 'crtfc_key=' in t:
        F(f'(h) crtfc_key= 글 {os.path.relpath(p, ROOT)}')
    if HEX40.search(t):
        F(f'(h) 40자리 16진 글 {os.path.relpath(p, ROOT)}')
try:
    tracked = subprocess.run(['git', '-C', ROOT, 'ls-files'], capture_output=True, text=True).stdout.split('\n')
    bad = [x for x in tracked if re.search(r'\.(pdf|PDF)$', x) and ('ops15' in x or 'ops15b' in x)]
    for x in bad:
        F(f'(h) PDF 가 git 추적 경로에 있음 {x}')
    for d in ('dart_out/raw/x', 'dart_out/text/x', 'dart_out/ops15/조직도/x'):
        rc = subprocess.run(['git', '-C', ROOT, 'check-ignore', '-q', d]).returncode
        if rc != 0:
            F(f'(h) 무시 폴더가 아님 {d[:-2]}')
    for p in mine:
        rel = os.path.relpath(p, ROOT)
        if rel.startswith('dart_out/raw') or rel.startswith('dart_out/text'):
            F(f'(h) 산출이 무시 폴더 안 {rel}')
except Exception as ex:
    F(f'(h) git 검사 못 함 {ex}')
I('h', f'비밀·경로 검사 파일 {len(mine)}개')

# ---------------------------------------------------------------- 쓰기
na = sum(1 for r in G if r['source_text'] == NA)
lines = [f'verify15b_G_g1 — G_g1 {len(G)}행(source_text 문서에 없음 {na}), 확인_G_g1 {len(C)}행, 문서목록15b_G_g1 {len(D)}행',
         f'FAIL {len(fails)}건']
lines += ['FAIL ' + x for x in fails]
for sec in ('a', 'b', 'c', 'd', 'e', 'f', 'h'):
    for x in info[sec]:
        lines.append(f'[{sec}] {x}')
lines.append('--- (e) 숫자 표본(앞 40개)')
lines += num_samples[:40]
lines.append(f'--- (c)③ 키워드 grep 걸림 {len(grep_lines)}줄(조각에 있음 {sum(1 for x in grep_lines if "조각에 있음" in x)}, 검토 {sum(1 for x in grep_lines if "검토:" in x)})')
lines += grep_lines
open(F_TXT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print(f'FAIL {len(fails)}건 → {os.path.relpath(F_TXT, ROOT)}')
sys.exit(1 if fails else 0)
