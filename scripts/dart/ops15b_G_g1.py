"""15차 확장 작업 G 그룹 g1(KB·신한·하나·우리·NH농협) — 원문_지주돈흐름 조각 생성기. 인자 없음. 네트워크 안 씀(이미 있는 글만 읽음).

산출: dart_out/ops15/조각/G_g1.csv, dart_out/ops15/조각/확인_G_g1.csv, dart_out/ops15/원문/G/<회사>__<fy>__<문서>.md,
      dart_out/ops15/문서목록15b_G_g1.csv

(1) 별도재무제표 주석 특수관계자 손익 거래 표(사업보고서 md 의 「5. 재무제표 주석」 안 「특수관계자」 절 — 연결 주석 아님).
    - 표마다 RP 설정(TABLES)에 표 번호·꼴을 적고, 표 머리 글이 기대와 같은지 확인(다르면 멈춤).
    - 행 = counterparty(원문 회사명) × item_kind(원문 계정명 — 행 머리 또는 열 머리 글 그대로, md <br> 는 빈칸 하나로) × 당기 금액.
      전기 열·전기 표는 넣지 않음. 금액 칸이 비었거나 「-」 또는 0 인 칸은 넣지 않음. 합계·소계 행(「합 계」「수익 계」「전체 특수관계자 합계」 열 등)은 넣지 않음.
      숫자 아닌 설명 행(「특수관계자거래에 대한 기술」)은 넣지 않음.
    - 합친 칸(rowspan)으로 행에 회사명·구분이 없으면 위 행 값을 이어 씀 → note 「회사명 칸은 위 행(합친 칸)에서 이어짐」.
    - amount_krw = 원문 숫자 × 1,000,000(원문 단위 백만원 — 표 안 또는 표 바로 앞 15줄 안 「단위」 글로 확인). 괄호 숫자는 음수.
    - direction(기계적):
        a) 표에 수익·비용 묶음 머리가 있으면(신한 「<수익>」「<비용>」 행, 하나 「수익」「비용」 열 묶음, NH 「구분」 칸 수익·비용) 그대로
           수익 → 「지주 수입」, 비용 → 「지주 지출」.
        b) 묶음 머리가 없으면 계정명 끝말: 「…수익」(…손익 아님) → 지주 수입, 「…비용」「…관리비」「…상각비」 → 지주 지출.
        c) 그 밖(「…손익」「전입(환입)」「환입」「제공받은용역」 등)과 a)의 하나 「신용손실충당금 전입(환입)」 열은 (판단):
           손익·전입(환입) 계정은 금액 부호(양수 = 이익·전입)로 정함 — 손익 양수 → 지주 수입, 손익 음수 → 지주 지출,
           전입(환입) 양수(전입) → 지주 지출, 음수(환입) → 지주 수입, 「환입」만 → 지주 수입, 「제공받은용역」 → 지주 지출. note 「(판단)」.
    - source_text = 그 표 행 한 줄(md 의 「| … |」 줄 그대로). 열 머리는 note 「열: …」.
    - page = 「XML [절 n] 「절 제목」 [표 m]」, FY2025 는 13차 보관 본문 PDF 글에서 같은 표 첫 행들의 숫자가 다 있는 쪽을 찾아 「p.N(본문 PDF, 13차 보관)」.
    - 정정판(사업보고서_원문.csv kind=정정) md 가 있으면 같은 행 글이 정정판에 있는지 보고, 없으면 note 「정정 <rcept>: 같은 행 글 없음」.
    - 배당: KB 는 특수관계자 표에 배당 계정이 따로 없고 「기타영업손익(*1)」(주석 「자회사로부터의 배당금 수익이 포함」)이라,
      별도 주석 기타영업손익 표의 「종속기업투자 배당금수익」 행(회사별 없음, counterparty 「문서에 없음」)을 1행 더함.
    - 신한: 별도 주석 순수수료손익 표의 「브랜드수수료」 행(회사별 없음)을 1행 더함(상표권·브랜드 수익 행).
(2) 사업보고서 Ⅱ(「II. 사업의 내용」 절부터 「III. 재무에 관한 사항」 앞까지)에서 「상표」「브랜드 사용」「브랜드수수료」「브랜드사용료」「로열티」「사용료」
    「영업수익 구성」 낱말로 찾음. 지주(별도) 영업수익 구성 표·상표권 사용료 산정 기준 문단이 없으면:
    상표권·브랜드 수익 행(신한 브랜드수수료)의 basis_text 「문서에 없음」, 그런 수익 행이 없는 해는 item_kind 「(산정 기준 문단)」 1행(「문서에 없음」).
    다른 행 basis_text 는 「문서에 없음」(note 에 찾은 범위는 스크립트 머리 — 행마다 되풀이하지 않고 (산정 기준 문단) 행 note 에 적음).
(3) 연차보고서·사업보고서 Ⅷ 임원 보수: 겸직 임원 보수를 어느 회사가 주는지·나누는 기준 문단, 겸직 부문장 성과평가 지표·보수 지급 회사 문단 →
    ANN 목록(회사·FY·문서·쪽·시작 글·끝 글)으로 원문을 잘라 냄(잘린 글은 출처 글 한 곳의 이어진 글). 없으면 「문서에 없음」 행.
(4) 확인_G_g1.csv — REQUEST15b 작업 G 「특히 볼 것」 g1 항목.
"""
import csv, os, re, sys, glob, zipfile, hashlib
from datetime import datetime, timezone, timedelta

csv.field_size_limit(10 ** 9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'dart_out', 'ops15')
FRAG = os.path.join(OUT, '조각')
MDDIR = os.path.join(OUT, '원문', 'G')
NA = '문서에 없음'
G1 = ['KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'NH농협금융지주']
ZIP13 = os.path.join(ROOT, 'handoff', '13차_지주관리유형', '13차_지주관리유형_텍스트.zip')
KST = timezone(timedelta(hours=9))
COLS = ['corp_label', 'fy', 'item_kind', 'counterparty', 'direction', 'amount_krw', 'basis_text', 'doc_kind', 'section_title',
        'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
CCOLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note']
DCOLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at',
         'text_path', 'status', 'note']

# ---------------------------------------------------------------- 특수관계자 손익 표 설정
# mode: long(행 = 회사·계정, 값 열 nv개, 당기 = 첫 값), wide(열 = 회사, 행 = 계정), acct(열 = 계정, 행 = 회사), nh(구분·계정·회사·금액)
# hdr: 표 첫 줄부터 머리 줄 수, expect: 머리 줄들에 있어야 하는 글
TABLES = {
    ('KB금융지주', 2019): [dict(t=1216, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2020): [dict(t=1255, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2021): [dict(t=1240, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2022): [dict(t=1285, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2023): [dict(t=1243, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2024): [dict(t=1224, mode='long', hdr=1, nkey=3, nv=2, expect='구분 | 회사명 | 계정과목명 | 당기 | 전기')],
    ('KB금융지주', 2025): [dict(t=3787, mode='wide', hdr=4, expect='전체 특수관계자', period_table=3786)],
    ('신한금융지주', 2019): [dict(t=749, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제 19(당) 기'),
                         dict(t=750, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제 19(당) 기')],
    ('신한금융지주', 2020): [dict(t=792, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제20(당) 기'),
                         dict(t=793, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 |')],
    ('신한금융지주', 2021): [dict(t=806, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제21(당) 기'),
                         dict(t=807, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 |')],
    ('신한금융지주', 2022): [dict(t=855, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제22(당) 기'),
                         dict(t=856, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제 22(당)기')],
    ('신한금융지주', 2023): [dict(t=814, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제23(당) 기'),
                         dict(t=815, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제 23(당)기')],
    ('신한금융지주', 2024): [dict(t=798, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제24(당) 기'),
                         dict(t=799, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자명 | 계정과목 | 제 24(당)기')],
    ('신한금융지주', 2025): [dict(t=2647, mode='wide', hdr=4, expect='전체 특수관계자', period_table=2646)],
    ('우리금융지주', 2019): [dict(t=798, mode='long', hdr=2, nkey=2, nv=1, expect='특수관계자 | 계정과목명 | 제1(당)기')],
    ('우리금융지주', 2020): [dict(t=885, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자 | 계정과목명 | 당기 | 전기')],
    ('우리금융지주', 2021): [dict(t=802, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자 | 계정과목명 | 당기 | 전기')],
    ('우리금융지주', 2022): [dict(t=830, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자 | 계정과목명 | 당기 | 전기')],
    ('우리금융지주', 2023): [dict(t=838, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자 | 계정과목명 | 당기 | 전기')],
    ('우리금융지주', 2024): [dict(t=839, mode='long', hdr=2, nkey=2, nv=2, expect='특수관계자 | 계정과목명 | 당기 | 전기')],
    ('우리금융지주', 2025): [dict(t=3056, mode='wide', hdr=4, expect='전체 특수관계자', period_table=3055)],
    ('하나금융지주', 2019): [dict(t=789, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2020): [dict(t=890, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2021): [dict(t=989, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2022): [dict(t=1021, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2023): [dict(t=1075, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2024): [dict(t=1085, mode='acct', hdr=2, spans=[3, 1, 2], expect='특수관계자 | 유형 | 수익', period_text='<당기>')],
    ('하나금융지주', 2025): [dict(t=3073, mode='acct', hdr=2, spans=None, expect='특수관계자거래', period_table=3072)],
    ('NH농협금융지주', 2019): [dict(t=924, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=923)],
    ('NH농협금융지주', 2020): [dict(t=928, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=927)],
    ('NH농협금융지주', 2021): [dict(t=936, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=935)],
    ('NH농협금융지주', 2022): [dict(t=943, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=942)],
    ('NH농협금융지주', 2023): [dict(t=993, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=992)],
    ('NH농협금융지주', 2024): [dict(t=1005, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=1004)],
    ('NH농협금융지주', 2025): [dict(t=1016, mode='nh', hdr=1, nkey=3, nv=1, expect='구분 | 계정과목 | 특수관계자 | 금액', period_table=1015)],
}
TOTAL_RE = re.compile(r'^(합\s*계|소\s*계|총\s*계|.+\s계|.*합\s*계)$')


def now_kst():
    return datetime.now(KST).isoformat(timespec='seconds')


def cells(line):
    s = line.strip()
    assert s.startswith('|') and s.endswith('|'), line[:80]
    return [c.strip() for c in s[1:-1].split('|')]


def clean_head(s):
    """칸 글 → item_kind·counterparty 값: md 칸 안 줄바꿈 표지(<br>, &cr;)만 지우고 빈칸 정리."""
    return re.sub(r'\s+', ' ', s.replace('<br>', '').replace('&cr;', '')).strip()


def nrm(s):
    return re.sub(r'\s+', '', s.replace('<br>', '').replace('|', '').replace('&cr;', ''))


def parse_num(v):
    """원문 금액 글 → 정수(백만원) 또는 None(빈칸·「-」·0). 숫자 아니면 ValueError."""
    s = v.replace('<br>', '').strip()
    if s in ('', '-', '－', '0', '(0)'):
        return None
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg, s = True, s[1:-1].strip()
    elif s.startswith('△') or s.startswith('-'):
        neg, s = True, s[1:].strip()
    if not re.fullmatch(r'\d{1,3}(,\d{3})*|\d+', s):
        raise ValueError(v)
    n = int(s.replace(',', ''))
    if n == 0:
        return None
    return -n if neg else n


def reports():
    out = {}
    for r in csv.DictReader(open(os.path.join(OUT, '사업보고서_원문.csv'), encoding='utf-8-sig')):
        if r['label'] in G1:
            out.setdefault((r['label'], int(r['fy'])), []).append(r)
    return out


class MD:
    def __init__(self, path):
        self.path = path
        self.lines = open(os.path.join(ROOT, path), encoding='utf-8').read().split('\n')
        self.heads = [i for i, l in enumerate(self.lines) if l.startswith('### [절')]
        self.tidx = {}
        for i, l in enumerate(self.lines):
            m = re.fullmatch(r'\[표 (\d+)\]', l)
            if m:
                self.tidx[int(m.group(1))] = i

    def table(self, t):
        i = self.tidx[t]
        j = i + 1
        rows = []
        while self.lines[j] != '[표 끝]':
            rows.append((j, self.lines[j]))
            j += 1
        return i, rows

    def head_of(self, i):
        h = [k for k in self.heads if k <= i][-1]
        m = re.match(r'### \[절 (\d+)\] ?(.*)$', self.lines[h])
        return int(m.group(1)), m.group(2).strip(), h

    def sep_range(self):
        s = [i for i in self.heads if re.search(r'재무제표 ?주석', self.lines[i]) and '연결' not in self.lines[i]][0]
        e = [i for i in self.heads if i > s and re.search(r'배당에 관한|IV\. |증권의 발행', self.lines[i])][0]
        return s, e

    def section(self, a, b):
        return '\n'.join(self.lines[a:b])


def unit_near(md, ti, rows, period_table=None):
    txt = ' '.join(l for _, l in rows[:3])
    if period_table:
        txt += ' ' + ' '.join(l for _, l in md.table(period_table)[1])
    for k in range(max(0, ti - 15), ti):
        txt += ' ' + md.lines[k]
    m = re.findall(r'단위\s*:\s*([^)|]+?)\s*[)|]', txt)
    return [u.strip() for u in m]


def direction_for(item, amount, group=None, judge_group=False):
    """(direction, 판단 note 또는 '')"""
    if group in ('수익', '비용') and not judge_group:
        return ('지주 수입' if group == '수익' else '지주 지출'), ''
    it = re.sub(r'\(\*\d*\)|\(주\d*\)|\s|, 특수관계자거래', '', item)
    if not judge_group:
        if it.endswith('수익') and '손익' not in it:
            return '지주 수입', ''
        if re.search(r'(비용|관리비|상각비)$', it):
            return '지주 지출', ''
    if re.search(r'환입\(전입\)|환\(전\)입', it):
        return ('지주 수입' if amount > 0 else '지주 지출'), '(판단) direction: 「환입(전입)」 계정 — 양수(환입)는 지주 수입, 음수(전입)는 지주 지출로 봄'
    if re.search(r'전입|전\(환\)입', it):
        return ('지주 지출' if amount > 0 else '지주 수입'), '(판단) direction: 「전입(환입)」 계정 — 양수(전입)는 지주 지출, 음수(환입)는 지주 수입으로 봄'
    if '환입' in it:
        return '지주 수입', '(판단) direction: 「환입」 계정을 지주 수입으로 봄(표에 수익·비용 묶음 머리 없음)'
    if '손익' in it or '이익' in it or '손실' in it:
        return ('지주 수입' if amount > 0 else '지주 지출'), '(판단) direction: 「손익」 계정 — 양수는 지주 수입, 음수는 지주 지출로 봄'
    if '제공받은용역' in it:
        return '지주 지출', '(판단) direction: 「제공받은용역」 열을 지주 지출로 봄(표에 수익·비용 묶음 머리 없음)'
    raise ValueError('direction? ' + item)


def parse_rp_table(md, cfg):
    """→ list of dict(cp, item, val_text, amount, group, line_no, line, carried, col_note, cat), anomalies"""
    ti, rows = md.table(cfg['t'])
    hdr = rows[:cfg['hdr']]
    htxt = ' '.join(l for _, l in hdr)
    if cfg['expect'] not in htxt:
        raise SystemExit(f"표 머리 다름 {md.path} [표 {cfg['t']}]: {htxt[:200]}")
    data = rows[cfg['hdr']:]
    out, anom = [], []
    mode = cfg['mode']
    if mode in ('long', 'nh'):
        nk, nv = cfg['nkey'], cfg['nv']
        keys = [''] * nk
        group = cat = None
        for ln, l in data:
            c = cells(l)
            if len(c) == 1:
                t = c[0]
                m = re.fullmatch(r'<(수익|비용)>', t)
                if m:
                    group = m.group(1)
                else:
                    cat = t
                continue
            if len(c) < nv + 1 or len(c) > nk + nv:
                anom.append((ln, 'cells', l[:100]))
                continue
            vals = c[-nv:]
            kc = c[:-nv]
            carried = len(kc) < nk
            keys = keys[:nk - len(kc)] + kc
            if any(TOTAL_RE.match(k) for k in kc) or any('합계' in k.replace(' ', '') for k in kc):
                continue
            vt = vals[0]
            try:
                amt = parse_num(vt)
            except ValueError:
                anom.append((ln, 'num', l[:100]))
                continue
            if amt is None:
                continue
            if mode == 'nh':
                g = keys[0]
                if g not in ('수익', '비용'):
                    continue
                item, cp = keys[1], keys[2]
                carried_cp = len(kc) < 1 + 0  # cp 칸은 늘 있음(오른쪽 맞춤 — 값 바로 앞)
                out.append(dict(cp=cp, item=item, vt=vt, amount=amt, group=g, ln=ln, line=l, carried=len(kc) < 3,
                                carried_what=('구분' if len(kc) == 2 else '구분·계정과목' if len(kc) == 1 else ''), cat=None,
                                col=f"열: 구분·계정과목·특수관계자·금액(당기 표)"))
            else:
                item, cp = keys[-1], keys[-2]
                cw = ''
                if len(kc) < nk:
                    cw = '회사명' if nk - len(kc) >= 1 else ''
                    if nk == 3 and len(kc) == 1:
                        cw = '구분·회사명'
                    elif nk == 3 and len(kc) == 2:
                        cw = '구분'
                out.append(dict(cp=cp, item=item, vt=vt, amount=amt, group=group, ln=ln, line=l, carried=bool(cw),
                                carried_what=cw, cat=(keys[0] if nk == 3 else cat),
                                col=f"열: {' · '.join(cells(hdr[-1][1]) if cfg['hdr'] == 1 else cells([h for h in hdr if '계정과목' in h[1]][0][1]))}"))
    elif mode == 'wide':
        cprow = cells(hdr[-1][1])
        assert cprow[0] == '', hdr[-1][1][:80]
        cps = cprow[1:]
        n = len(cps)
        for ln, l in data:
            c = cells(l)
            item = c[0]
            if len(c) < 1 + n:
                anom.append((ln, 'cells', l[:100]))
                continue
            for k, cp in enumerate(cps):
                vt = c[1 + k]
                try:
                    amt = parse_num(vt)
                except ValueError:
                    if item.endswith('기술'):
                        break
                    anom.append((ln, 'num', vt[:40]))
                    continue
                if amt is None:
                    continue
                out.append(dict(cp=cp, item=item, vt=vt, amount=amt, group=None, ln=ln, line=l, carried=False, carried_what='',
                                cat=None, col=f"열: {cp}(표 머리 {cfg['hdr']}번째 줄의 {k + 1}번째 회사 열; 행 머리 = 계정)"))
    elif mode == 'acct':
        if cfg['spans']:
            r1, r2 = cells(hdr[0][1]), cells(hdr[1][1])
            groups_hdr = r1[2:]
            items, groups, judge = [], [], []
            sub = iter(r2)
            for gname, sp in zip(groups_hdr, cfg['spans']):
                if sp == 1 and gname not in ('수익', '비용'):
                    items.append(gname); groups.append(None); judge.append(True)
                else:
                    for _ in range(sp):
                        items.append(next(sub)); groups.append(gname); judge.append(False)
        else:
            r2 = cells(hdr[1][1])
            items = [x for x in r2 if x]
            groups = [None] * len(items)
            judge = [False] * len(items)
        ni = len(items)
        for ln, l in data:
            c = cells(l)
            if len(c) < ni + 1:
                anom.append((ln, 'cells', l[:100]))
                continue
            vals, kc = c[-ni:], c[:-ni]
            if cfg['spans']:
                cp = kc[0] if kc else ''
                cat = kc[1] if len(kc) > 1 else ''
            else:
                cp = kc[-1]
                cat = kc[-2] if len(kc) > 1 else ''
            if '합계' in cp.replace(' ', '') or TOTAL_RE.match(cp):
                continue
            for k in range(ni):
                try:
                    amt = parse_num(vals[k])
                except ValueError:
                    anom.append((ln, 'num', vals[k][:40]))
                    continue
                if amt is None:
                    continue
                out.append(dict(cp=cp, item=clean_head(items[k]), vt=vals[k], amount=amt, group=groups[k], judge=judge[k], ln=ln,
                                line=l, carried=False, carried_what='', cat=cat,
                                col=f"열: {clean_head(items[k])}({k + 1}번째 금액 열" + (f", 묶음 머리 「{groups[k]}」" if groups[k] else '') + ")"))
    return ti, rows, out, anom


def unit_of(md, ti, rows, period_table=None):
    """가장 가까운 「단위」 글: 표 안 → (period_table) → 표 앞 15줄(가까운 것부터)."""
    def f(txt):
        return [u.strip() for u in re.findall(r'단위\s*:\s*([^)|]+?)\s*[)|]', txt)]
    u = f(' '.join(l for _, l in rows[:3]))
    if u:
        return u[0], '표 안'
    if period_table:
        u = f(' '.join(l for _, l in md.table(period_table)[1]))
        if u:
            return u[0], f'[표 {period_table}]'
    for k in range(ti - 1, max(0, ti - 15), -1):
        u = f(md.lines[k])
        if u:
            return u[-1], '표 앞 글'
    return None, ''


def note_heading(md, ti):
    """FY2019~2024(절 하나에 주석 전체): 표 앞의 「n. 특수관계자…」 줄 → (그 줄 번호, 글, 다음 주석 머리 줄 번호)."""
    s, e = md.sep_range()
    starts = [i for i in range(s, ti) if re.match(r'^(### \[절 \d+\] )?\s*\d+\s*\.\s*특수관계자', md.lines[i])
              or (md.lines[i].strip() == '. 특수관계자 거래')]
    a = starts[-1]
    m = re.match(r'^(?:### \[절 \d+\] )?\s*(\d+)\s*\.', md.lines[a])
    if m:
        n = int(m.group(1))
        nxt = [i for i in range(ti, e) if re.match(rf'^\s*{n + 1}\s*\.\s*\S', md.lines[i])]
        b = nxt[0] if nxt else e
    else:  # 신한 FY2019~2021: 번호가 앞 줄에 떨어져 있음(「34」 줄 + 「. 특수관계자 거래」 줄)
        if md.lines[a - 1].strip().isdigit():
            a -= 1
            n = int(md.lines[a].strip())
            nxt = [i for i in range(ti, e) if re.match(rf'^\s*{n + 1}\s*(\.|$)', md.lines[i])]
        else:
            nxt = []
        b = nxt[0] if nxt else e
    return a, b


def rp_section_bounds(md, ti):
    num, title, h = md.head_of(ti)
    nexth = [k for k in md.heads if k > h]
    if '특수관계' in title:
        return h, (nexth[0] if nexth else len(md.lines)), num, title, None
    a, b = note_heading(md, ti)
    sub = re.sub(r'\s+', ' ', md.lines[a].replace('&cr;', ' ')).strip()
    if sub.isdigit():
        sub += re.sub(r'\s+', ' ', md.lines[a + 1].replace('&cr;', ' ')).strip()
    m = re.match(r'^\d+\s*\.\s*특수관계자(?:와의)?\s?(?:거래)?', sub)
    if m:
        sub = m.group(0).strip()
    return a, b, num, title, sub


_Z13 = {}


def pdf13_pages(label):
    if label not in _Z13:
        z = zipfile.ZipFile(ZIP13)
        t = z.read(f'13차_지주관리유형/텍스트/사업보고서__{label}.md').decode('utf-8')
        parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
        _Z13[label] = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
    return _Z13[label]


def pdf13_table_page(label, out_rows):
    """표 첫 행(값 3개 이상)들의 숫자가 다 있는 쪽 → 쪽 번호(여럿이면 뒤쪽 — 별도 주석이 연결 주석 뒤)."""
    pages = pdf13_pages(label)
    lines = []
    for o in out_rows:
        if o['line'] not in lines:
            lines.append(o['line'])
    nums = []
    for l in lines[:6]:
        nums += [c for c in cells(l) if re.fullmatch(r'\(?[\d,]{3,}\)?', c)]
        if len(nums) >= 6:
            break
    cand = [p for p, t in pages.items() if all(n in t for n in nums)]
    return sorted(cand), nums


def build_rp(reps, rows, docs, mdouts, log):
    for (lab, fy), cfgs in sorted(TABLES.items(), key=lambda x: (G1.index(x[0][0]), x[0][1])):
        rr = reps[(lab, fy)]
        r = [x for x in rr if x['kind'] == '본'][0]
        md = MD(r['text_path'])
        corr = []
        for x in rr:
            if x['kind'] == '정정':
                if x['text_path'] and os.path.exists(os.path.join(ROOT, x['text_path'])):
                    corr.append((x['rcept_no'], nrm(open(os.path.join(ROOT, x['text_path']), encoding='utf-8').read())))
                else:
                    corr.append((x['rcept_no'], None, x['doc_message'] or x['report_nm']))
        for cfg in cfgs:
            ti, trows, out, anom = parse_rp_table(md, cfg)
            if anom:
                raise SystemExit(f'표 읽기 이상 {lab} {fy} {cfg["t"]}: {anom[:3]}')
            unit, uwhere = unit_of(md, ti, trows, cfg.get('period_table'))
            if unit != '백만원':
                raise SystemExit(f'단위 {lab} {fy} {cfg["t"]}: {unit}')
            a, b, num, title, sub = rp_section_bounds(md, ti)
            mdouts.setdefault((lab, fy, '사업보고서'), []).append((a, b, md, r, f'[절 {num}] {title}' + (f' — {sub}' if sub else '')))
            page = f'XML [절 {num}] 「{title}」 [표 {cfg["t"]}]'
            p13 = ''
            if fy == 2025:
                cand, nums = pdf13_table_page(lab, out)
                if cand:
                    p13 = f'p.{cand[-1]}(본문 PDF, 13차 보관)'
                    if len(cand) > 1:
                        log.append(f'{lab} FY{fy} [표 {cfg["t"]}] 13차 PDF 후보 쪽 {cand} → 뒤쪽 p.{cand[-1]}')
                else:
                    log.append(f'{lab} FY{fy} [표 {cfg["t"]}] 13차 PDF 쪽 못 찾음({nums})')
            period = '당기'
            p0 = int(re.match(r'p\.(\d+)', p13).group(1)) if p13 else None
            p13note = ''
            for o in out:
                cp, item = clean_head(o['cp']), clean_head(o['item'])
                if p0:  # 행마다: 표 첫 쪽부터 3쪽 안에서 계정명(앞 8자)·원문 숫자가 다 있는 첫 쪽
                    pages = pdf13_pages(lab)
                    hit = [q for q in range(p0, p0 + 3) if q in pages and o['vt'] in pages[q]
                           and re.sub(r'\s+', '', item)[:8] in re.sub(r'\s+', '', pages[q])]
                    p13 = f'p.{hit[0]}(본문 PDF, 13차 보관)' if hit else ''
                    p13note = ''
                    if not hit:
                        # 계정명 칸이 앞 쪽(합친 칸)에 있고 「회사명+원문 숫자」만 다음 쪽에 있는 경우
                        hit2 = [q for q in range(p0, p0 + 3) if q in pages
                                and re.sub(r'\s+', '', cp) + o['vt'] in re.sub(r'\s+', '', pages[q])]
                        if hit2:
                            p13 = f'p.{hit2[0]}(본문 PDF, 13차 보관)'
                            p13note = (f'13차 PDF p.{hit2[0]} 에는 「{re.sub(chr(92) + "s+", "", cp)}{o["vt"]}」(회사명·원문 숫자)만 있고 '
                                       f'계정명 칸은 앞 쪽(표가 쪽을 넘김)')
                            log.append(f'{lab} FY{fy} [표 {cfg["t"]}] {item} {o["vt"]} 13차 PDF 쪽: 회사명+숫자로 p.{hit2[0]}')
                        else:
                            p13note = '13차 PDF 쪽: 계정명·원문 숫자가 함께 있는 쪽을 못 찾아 page 에 안 붙임'
                            log.append(f'{lab} FY{fy} [표 {cfg["t"]}] {item} {o["vt"]} 13차 PDF 쪽 못 찾음 — page 에 안 붙임')
                d, dn = direction_for(item, o['amount'], o['group'], o.get('judge', False))
                notes = [f'원문 단위 백만원({uwhere} 「단위」), 원문 숫자 {o["vt"]}', o['col'] + f' — {period} 금액']
                if o['carried']:
                    notes.append(f'{o["carried_what"]} 칸은 위 행(합친 칸)에서 이어짐')
                if o.get('cat'):
                    notes.append(f'구분: {clean_head(o["cat"])}')
                if o['group'] and not o.get('judge'):
                    notes.append(f'direction: 표의 「{o["group"]}」 묶음 머리')
                elif not dn:
                    notes.append('direction: 계정명 끝말(…수익 → 지주 수입, …비용·관리비·상각비 → 지주 지출)')
                if dn:
                    notes.append(dn)
                if cp != o['cp'] or item != o['item']:
                    notes.append('item_kind·counterparty 는 md 칸 안 줄바꿈 표지(<br>·&cr;)만 지운 글')
                if p0 and p13note:
                    notes.append(p13note)
                for c in corr:
                    if c[1] is None:
                        notes.append(f'정정 {c[0]}: XML 본문 없음({c[2]}) — 대조 못 함')
                    elif nrm(o['line']) not in c[1]:
                        notes.append(f'정정 {c[0]}: 같은 행 글 없음')
                rows.append(dict(corp_label=lab, fy=fy, item_kind=item, counterparty=cp, direction=d,
                                 amount_krw=o['amount'] * 1000000, basis_text=NA, doc_kind='사업보고서',
                                 section_title=f'Ⅲ. 재무에 관한 사항 > {title}' + (f' > {sub}' if sub else ''),
                                 source_text=o['line'], rcept_no_or_url=r['rcept_no'],
                                 page=page + (f' · {p13}' if p13 else ''), note=' / '.join(notes),
                                 doc_name=r['report_nm'], collected_at=r['fetched_at']))
        docs[(lab, fy, '사업보고서')] = r


def find_line(md, a, b, pat):
    for i in range(a, b):
        if re.search(pat, md.lines[i]):
            return i
    return None


def build_extra(reps, rows, mdouts):
    """KB 종속기업투자 배당금수익(기타영업손익 주석), 신한 브랜드수수료(순수수료손익 주석)."""
    for lab, pat, item_re, what in (('KB금융지주', r'^\|.*종속기업투자 배당금수익 \|', r'종속기업투자 배당금수익', '기타영업손익'),
                                     ('신한금융지주', r'^\|.*\| 브랜드수수료 \|', r'브랜드수수료', '순수수료손익')):
        for fy in range(2019, 2026):
            r = [x for x in reps[(lab, fy)] if x['kind'] == '본'][0]
            md = MD(r['text_path'])
            s, e = md.sep_range()
            i = find_line(md, s, e, pat)
            if i is None:
                raise SystemExit(f'{lab} {fy} {what} 행 없음')
            c = cells(md.lines[i])
            k = [j for j, x in enumerate(c) if x == item_re][0]
            vt = c[k + 1]
            amt = parse_num(vt)
            tnum = [int(re.fullmatch(r'\[표 (\d+)\]', md.lines[j]).group(1)) for j in range(i, s, -1) if re.fullmatch(r'\[표 \d+\]', md.lines[j])][0]
            ti, trows = md.table(tnum)
            unit, uwhere = unit_of(md, ti, trows, tnum - 1 if fy == 2025 else None)
            if unit != '백만원':
                raise SystemExit(f'단위 {lab} {fy} {what}: {unit}')
            num, title, h = md.head_of(i)
            if fy == 2025:
                a = h
                b = [x for x in md.heads if x > h][0]
                sub = None
                hdr = cells(trows[0][1])
                coln = '당기 표 「공시금액」 열'
            else:
                nm = '기타영업손익' if lab == 'KB금융지주' else '순수수료손익'
                a = [j for j in range(ti - 1, s, -1) if re.match(r'^\s*(\d+\s*\.)?\s*' + nm + r'(?!의)', md.lines[j])][0]
                head = re.sub(r'&cr;.*$', '', md.lines[a]).strip()
                head = head.split(nm)[0] + nm
                if not re.match(r'^\d+\s*\.', head):
                    prev = [md.lines[j].strip() for j in range(a - 1, a - 4, -1) if md.lines[j].strip() and md.lines[j].strip() != '&cr;']
                    if prev and re.fullmatch(r'\d+\s*\.', prev[0]):
                        head = prev[0] + ' ' + head
                        a = [j for j in range(a - 1, a - 4, -1) if md.lines[j].strip() == prev[0]][0]
                b = i + 1
                while md.lines[b] != '[표 끝]':
                    b += 1
                b += 1
                sub = re.sub(r'\s+', ' ', head).strip()
                hdr = [cells(l) for _, l in trows if re.search(r'당\)? ?기', l)][0]
                coln = '열: ' + ' · '.join(hdr) + ' — 당기(첫 금액 열)'
            mdouts.setdefault((lab, fy, '사업보고서'), []).append((a, b, md, r, f'[절 {num}] {title}' + (f' — {sub}' if sub else '')))
            page = f'XML [절 {num}] 「{title}」 [표 {tnum}]'
            if lab == 'KB금융지주':
                note = (f'원문 단위 백만원({uwhere} 「단위」), 원문 숫자 {vt} / {coln} / 특수관계자 거래 표에는 배당 계정이 따로 없고 「기타영업손익(*1)」 칸에 '
                        f'「자회사로부터의 배당금 수익이 포함」(표 주석) — 회사별 배당금은 별도 주석에 없음(종속기업 전체 합계 1행) / direction: 계정명 「…수익」')
                cp = NA
            else:
                note = (f'원문 단위 백만원({uwhere} 「단위」), 원문 숫자 {vt} / {coln} / 회사별 내역은 이 표에 없음 — 같은 해 특수관계자 거래 표의 '
                        f'「수수료수익」 행이 회사별 금액(그 표에 「브랜드」 낱말 없음) / direction: 계정명 「브랜드수수료」가 「수수료수익」 아래 항목'
                        f' / basis_text: Ⅱ. 사업의 내용·Ⅲ 별도 주석에서 「브랜드」「상표」「사용료」「로열티」 검색 — 산정 기준(요율·기준 수익) 문단 없음')
                cp = NA
            if fy == 2025:
                cand = [p for p, t in pdf13_pages(lab).items() if item_re in t and vt in t]
                if cand:
                    page += f' · p.{cand[-1]}(본문 PDF, 13차 보관)'
            for x in reps[(lab, fy)]:
                if x['kind'] != '정정':
                    continue
                if x['text_path'] and os.path.exists(os.path.join(ROOT, x['text_path'])):
                    if nrm(md.lines[i]) not in nrm(open(os.path.join(ROOT, x['text_path']), encoding='utf-8').read()):
                        note += f' / 정정 {x["rcept_no"]}: 같은 행 글 없음'
                else:
                    note += f' / 정정 {x["rcept_no"]}: XML 본문 없음({x["doc_message"] or x["report_nm"]}) — 대조 못 함'
            rows.append(dict(corp_label=lab, fy=fy, item_kind=item_re, counterparty=cp, direction='지주 수입',
                             amount_krw=amt * 1000000, basis_text=NA, doc_kind='사업보고서',
                             section_title=f'Ⅲ. 재무에 관한 사항 > {title}' + (f' > {sub}' if sub else ''),
                             source_text=md.lines[i], rcept_no_or_url=r['rcept_no'], page=page, note=note,
                             doc_name=r['report_nm'], collected_at=r['fetched_at']))


BASIS_KW = r'상표|브랜드 ?사용|브랜드 ?수수료|브랜드사용료|로열티|사용료|영업수익 ?구성|수익 ?구성'


def build_basis(reps, rows):
    """Ⅱ. 사업의 내용에서 상표권·브랜드 사용료 산정 기준·지주 영업수익 구성 문단 찾기 — 없으면 (산정 기준 문단) 「문서에 없음」 행."""
    found = []
    for lab in G1:
        for fy in range(2019, 2026):
            r = [x for x in reps[(lab, fy)] if x['kind'] == '본'][0]
            md = MD(r['text_path'])
            s = [i for i in md.heads if re.search(r'I+\. *사업의 내용', md.lines[i])][0]
            e = [i for i in md.heads if re.search(r'I+\. *재무에 관한', md.lines[i])][0]
            hits = [(i, md.lines[i]) for i in range(s, e) if re.search(BASIS_KW, md.lines[i])]
            found.append((lab, fy, [(i + 1, re.search(r'.{0,30}(' + BASIS_KW + r').{0,30}', l).group(0)) for i, l in hits]))
            has_brand_row = lab == '신한금융지주'
            if has_brand_row:
                continue
            hl = '; '.join(f'md {i}행 「{t}」' for i, t in found[-1][2][:4])
            rows.append(dict(corp_label=lab, fy=fy, item_kind='(산정 기준 문단)', counterparty=NA, direction=NA, amount_krw=NA,
                             basis_text=NA, doc_kind='사업보고서', section_title='Ⅱ. 사업의 내용', source_text=NA,
                             rcept_no_or_url=r['rcept_no'],
                             page=f'XML [절 {md.head_of(s)[0]}]~[절 {md.head_of(e - 1)[0]}] 「II. 사업의 내용」 전체',
                             note=('찾은 범위: 사업보고서 「II. 사업의 내용」 절 전체(md ' + f'{s + 1}~{e}행), 낱말 「상표」「브랜드 사용」「브랜드수수료」「브랜드사용료」'
                                   '「로열티」「사용료」「영업수익 구성」「수익 구성」 — 지주(별도) 영업수익 구성 표·상표권(브랜드) 사용료 산정 기준 문단 없음'
                                   + (f' (걸린 글은 자회사 상품·영업 설명 또는 부문 손익 산식: {hl})' if hl else '')
                                   + ' / 같은 해 Ⅲ 별도 주석에도 상표권·브랜드 「수익·수수료·사용료」 계정 없음'),
                             doc_name=r['report_nm'], collected_at=r['fetched_at']))
    return found


# ---------------------------------------------------------------- (3) 연차보고서·사업보고서 Ⅷ 겸직 보수 문단
I_PAY = '(겸직 임원 보수 지급·배분 기준)'
I_DIV = '(겸직 부문장 성과평가·보수)'
ANN_FY = {'KB금융지주': range(2017, 2026), '신한금융지주': range(2017, 2026), '하나금융지주': range(2017, 2026),
          '우리금융지주': range(2019, 2026), 'NH농협금융지주': range(2019, 2026)}
DIV_CORPS = ('KB금융지주', '신한금융지주', '하나금융지주')
SEARCH_NOTE = ('찾은 범위: 그 해 연차보고서 전체 쪽(본공시·추가공시·정정공시), 낱말 「겸직」「겸임」 근처 80자 안의 「보수」「성과보상」「성과급」「보상」「인건비」'
               '「분담」「배분」「정산」「지급」「급여」「부담」「KPI」「성과평가」「평가지표」, 「부문장」「사업부문장」「Matrix」「매트릭스」 근처의 「KPI」「성과평가」'
               '「평가지표」「평가체계」「보수체계」「비중」')
KB_A1 = r'\*? ?이와 별도로 원소속회사가 자회사인 겸직 경영진.{0,200}?분담하기로 결의'
KB_A2 = r'주3\) [^주]{0,160}?원소속회사 ?인 ?자회사에서.{0,300}?겸직 ?임직원 ?제외\)'
KB_M = r'평가보상위원회 위원으로서 매트릭스 조직에 대한 성과평가 체계 구축에 대해 조언하였습 ?니다\.'
SH17 = r'본 위원회는 그룹 GIB, 글로벌 사업부문 겸직구조 확대 및 신설에 따라 담당 경영진의 평가 및 보수체계 및 장기보수에 관한 사항을 논의하고 심의하였습니다\.'
SH18 = r'결의-다\.이사 보수에 관한 사항 : .{0,300}?비상임이사는 자회사 경영진 직무를 겸직하는 점을 감안하여, 별도의 보수를 지급하지 않기로 결의하였습니다\.'
SH19A = r'본 위원회는 그룹 퇴직연금 사업부문제 도입에 ?따라 신규 선임되는 그룹 겸직 사업부문장의 성과평가체계 및 보수체계에 대해 심의하고 결의하였습니다\.'
SH19B = r'본 위원회는 2019년도 신규 편입 자회사인 ?아시아신탁 및 신한AI의 ?성과평가체계에 대해 심의하고 결의하였으며 그룹 겸직 사업부문장의 부문 전략과제 설정에 대해 논의하고 ?심의하였습니다\.'
SH20 = r'본 위원회는 오렌지라이프의 그룹 GMS사업부문 편입에 따라 GMS 사업부문장의 성과평가체계에 대해 심의하고 결의하였습니다\.'
SH23 = r'제5회 보수위원회는 위원 전원이 참석하여 성원이 되었으며, 2023\.7\.1\. 신규 선임된 그룹 소비자보호부문장의 성과평가 및 보수체계에 대해 심의 및 결의하였습니다\.'
SH25 = r'제4회 보수위원회는 위원 전원이 참석하여 성원이 되었으며, 2025\.10\.1\. 신규 선임된 그룹 AX·디지털부문장 등의 성과평가 및 보수체계에 대해 심의 및 결의하였습니다\.'
H1 = r'주2\) 겸직 임원의 경우,? 겸직 비율에 따라 보수총액 배분(?:함|하였습니다)\.'
H2A = r'2\. 겸직 임원의 경우에는 주된 업무를 하는 그룹사를 기준으로 부여하는 것을 원칙으로 하되, 필요시 경 ?발위에서 별도로 정할 수 있다\.'
H2B = r'③ 겸직 임원의 경우에는 원소속사에서 부여 및 평가하는 것을 원칙으로 하되, 필요시 경발위 또는 평보위 ?에 ?서 별도로 정할 수 있다\.'
H3 = r'☞4 ?호 결의 \(하나금융그룹 임원 보수 기준 개정\): 그룹 임원 보수 기준을 일부 개정하였습니다\. \(관계회사 보수 결정의 자율권 강화, 겸직임원 비용 분담 기준 변경\)'
H4 = r'버\) 겸직임원 인건비 배분 부적정 임원의 활동수당, 장기성과급도 관련 협약에서 정하는 바에 따라 원소속회사·겸직회사가 분담하고, 겸직 등 인력교류 형태의 내부거래 현황 및 관련 내부기준 제 ?· ?개정사항에 대한 준법감시부서의 점검을 강화할 필요가 있음\.'
W1 = r'\(H\) 2019년도 제8차 정기이사회 : 2019\.7\.25.{0,260}?3\) 임직원 겸직 時 비용분담 기준 승인 \(손태승 이사는 특별 이해관계자로 의결권 제한\)'
W2 = r'또한 2019\.7\.25\. 보상위원회 결의에 의거하여 경영진의 그룹 내 겸직 시 보상기준\(안\)을 결의하였으며, 2019\.9\.20\. 보상위원회 결의에 의거 ?하여 지주사 내 겸직 임원에 대한 보상기준\(안\)을 결의하였습니다\.'
W3 = r'주3\) 연말 금융감독원 업무보고서 공시기준에 따른 재직인원 대상 기재\(연중 퇴직자 제외, 자회사 소속 겸직 임직원[^)]*\)[^)]*\)'
H5 = r'또한, 2020년 12월 28일 제 ?7회 경영발전보상위원회에서는 관계회사의 자율성 강화를 위해 .{0,120}?그룹 ?내 겸직임원의 총보수를 겸직회사간 겸직비율에 따라 분담하도록 하였습니다\.'
H6 = r'나\. ?회사 임원 보수 보고 ?: ?사전에 경영발전보상위원회에서 결의한 .{0,80}?원소속사의 보수가 변경된 임원에 대한 보수 변경 내용을 보고 받았습니다\.'
SH_R = r'④ ?비상임이사의 ?보수는 ?사외이사의 ?보수를 ?따른다\. ?다만, ?겸직 ?비상임이사의 ?경우에는 ?그러하지 ?아니하다\.'
SH22 = r'제5회 보수위원회는 위원 전원이 참석하여 성원이 되었으며, ?GMS 사업그룹에서 신한라이프가 편입 제외됨에 따라 GMS 사업그룹장에 대한 성과평가 비중 변경에 대해 심의 및 결의하였습니다\.'
SH_AG = r'4\. 의결안건 가\. 그룹 겸직 경영진 성과평가체계 변경의 건'
NH1 = r'\* 부사장\(전략기획부문장.{0,120}?\) : 겸직 부사장의 경우, 원 ?소속사 성과평가 및 보상체계에 따라 산출된 성과 보상을 겸직 비율 등에 따라 회사 간 분담'

# (회사, fy) → [(item, regex, note, direction, dnote, counterparty)]
ANN = {}
for fy in range(2019, 2026):
    ANN.setdefault(('KB금융지주', fy), []).append((I_PAY, KB_A1, '성과보상 대상자 표 주석', None, '', None))
    ANN[('KB금융지주', fy)].append((I_PAY, KB_A2, '「임직원 총 보상」 표 주석', None, '', None))
for fy in (2019, 2020, 2021, 2022, 2023):
    ANN[('KB금융지주', fy)].append((I_DIV, KB_A1, '성과보상 대상자 표 주석', None, '', None,
                                    '같은 문단이 (겸직 임원 보수 지급·배분 기준) 행에도 있음 — 문단의 겸직 경영진 내역에 「부문장」이 있음'))
for fy in (2021, 2022):
    ANN[('KB금융지주', fy)].append((I_DIV, KB_M, '사외이사 활동 서술', None, '', None))
ANN[('신한금융지주', 2017)] = [(I_DIV, SH17, '보수위원회 활동 서술', None, '', None)]
ANN[('신한금융지주', 2018)] = [(I_PAY, SH18, '이사회 결의 서술', None, '', None)]
ANN[('신한금융지주', 2019)] = [(I_DIV, SH19A, '보수위원회 활동 서술', None, '', None), (I_DIV, SH19B, '보수위원회 활동 서술', None, '', None)]
ANN[('신한금융지주', 2020)] = [(I_DIV, SH20, '보수위원회 활동 서술', None, '', None, '문장에 「겸직」 낱말 없음 — 같은 쪽 의결안건 표의 안건은 따로 행'),
                              (I_DIV, SH_AG, '보수위원회 활동내역 표(의결안건)', None, '', None)]
ANN[('신한금융지주', 2022)] = [(I_DIV, SH22, '보수위원회 활동 서술', None, '', None, '문장에 「겸직」 낱말 없음 — 같은 쪽 의결안건 표의 안건은 따로 행'),
                              (I_DIV, SH_AG, '보수위원회 활동내역 표(의결안건)', None, '', None)]
ANN[('신한금융지주', 2023)] = [(I_DIV, SH23, '보수위원회 활동 서술', None, '', None, '문장에 「겸직」 낱말 없음')]
ANN[('신한금융지주', 2025)] = [(I_DIV, SH25, '보수위원회 활동 서술', None, '', None, '문장에 「겸직」 낱말 없음')]
for fy in range(2017, 2026):
    ANN.setdefault(('신한금융지주', fy), []).append((I_PAY, SH_R, '지배구조 내부규범 이사의 보수 조항', None, '', None))
for fy in range(2017, 2020):
    ANN.setdefault(('하나금융지주', fy), []).append((I_PAY, H2A, '장기성과(보상) 부여 기준 내규 조항', None, '', None))
for fy in range(2020, 2026):
    ANN.setdefault(('하나금융지주', fy), []).append((I_PAY, H2B, '장기성과급 부여 기준 내규 조항', None, '', None))
for fy in range(2018, 2026):
    ANN[('하나금융지주', fy)].append((I_PAY, H1, '성과보수 표 주석', None, '', None))
ANN[('하나금융지주', 2020)].append((I_PAY, H3, '이사회(경영발전보상위원회) 결의 서술', None, '', None))
ANN[('하나금융지주', 2022)].append((I_PAY, H4, '금융감독원 검사 결과 조치요구사항 서술', None, '', None))
ANN[('하나금융지주', 2020)].append((I_PAY, H5, '보수체계상 주요 변경 사항 서술', None, '', None))
ANN[('하나금융지주', 2025)].append((I_PAY, H6, '경영발전보상위원회 주요 의안 세부 내용(보고)', None, '', None, '문장에 「겸직」 낱말 없음 — 「원소속사」 낱말'))
ANN[('우리금융지주', 2019)] = [(I_PAY, W1, '이사회 개최 내역(결의 안건)', None, '', None), (I_PAY, W2, '보상위원회 결의 서술', None, '', None),
                              (I_PAY, W3, '「임직원 총보상」 표 주석', None, '', None)]
ANN[('우리금융지주', 2020)] = [(I_PAY, W3, '「임직원 총보상」 표 주석', None, '', None)]
ANN[('NH농협금융지주', 2025)] = [(I_PAY, NH1, '변동보상 대상자 표 주석', None, '', None)]

# 사업보고서 Ⅷ 2. 임원의 보수 등(겸직 보수 문구) — (회사, fy) → [(regex(md 한 줄 안), direction, dnote, counterparty)]
BIZ8_SH = r'^\| \(?주\) \| 기타비상무이사의 경우, 사외이사 보수체계를 동일 적용하되 자회사 경영진 직무를 겸직하는 경우 별도 보수 지급 없음\.? \|$'
BIZ8 = {('신한금융지주', fy): [(BIZ8_SH, NA, '', NA)] for fy in range(2020, 2026)}
BIZ8[('우리금융지주', 2019)] = [(r'2\) 우리은행 겸직임원\(4명\)의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행'),
                              (r'주\) 상기 보수는 원소속회사\(지주사\)에서 일괄 지급 후 겸직회사\(우리은행\)과 비용 분담', '지주 지출',
                               '(판단) direction: 원문 「원소속회사(지주사)에서 일괄 지급」 — 지급하는 쪽이 지주(비용 분담 뒤 몫은 문서에 없음)', '우리은행')]
BIZ8[('우리금융지주', 2020)] = [(r'2\) 우리은행 겸직임원\(3명\)의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행'),
                              (r'※ 상기 보수에는 그룹사간 겸직 관련 보수를 포함하여, 원소속회사\(지주사\)에서 일괄 지급 후 겸직회사\(우리은행\)과 비용 분담', '지주 지출',
                               '(판단) direction: 원문 「원소속회사(지주사)에서 일괄 지급」 — 지급하는 쪽이 지주(비용 분담 뒤 몫은 문서에 없음)', '우리은행')]
BIZ8[('우리금융지주', 2021)] = [(r'주2\) 우리은행 겸직임원\(3명\)의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행')]
BIZ8[('우리금융지주', 2022)] = [(r'주2\) 우리은행 겸직임원\(2명\)의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행')]
BIZ8[('우리금융지주', 2023)] = [(r'주5\) 우리은행 겸직임원의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행')]
BIZ8[('우리금융지주', 2024)] = [(r'주5\) 우리은행 겸직임원의 경우 지주사 지급분에 대해서만 작성함', NA, '', '우리은행')]
BIZ8[('하나금융지주', 2023)] = [(r'계량지표와 비계량지표의 실적을 종합하여 경영발전보상위원회의 최종 평가 및 심의를 거친 후 겸직비율 감안하여[^|]*', NA, '', NA)]


def kst(ts):
    if not ts:
        return ''
    if ts.endswith('+0000') or ts.endswith('Z'):
        d = datetime.strptime(ts.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z')
        return d.astimezone(KST).isoformat(timespec='seconds')
    return ts


class AnnDoc:
    """연차보고서 한 건: flat(빈칸 하나로 접은 글) + 쪽/섹션 경계."""
    def __init__(self, kind, lab, fy, variant, path=None, meta=None, secs=None):
        self.kind, self.lab, self.fy, self.variant, self.path, self.meta = kind, lab, fy, variant, path, meta
        self.flat, self.bounds = '', []  # bounds: (start, end, label, raw)
        pieces = []
        if kind == 'md':
            t = open(os.path.join(ROOT, path), encoding='utf-8').read()
            parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
            for i in range(1, len(parts), 2):
                pieces.append((f'p.{parts[i]}', parts[i + 1]))
        else:
            for r in secs:
                pieces.append((f'p.{r["시작페이지"]}(6차 섹션 시작페이지, 섹션순번 {r["섹션순번"]}·chunk {r["chunk_seq"]})', r['본문']))
        out = []
        pos = 0
        for lab_, raw in pieces:
            f = re.sub(r'\s+', ' ', raw).strip()
            self.bounds.append((pos, pos + len(f), lab_, raw))
            out.append(f)
            pos += len(f) + 1
        self.flat = ' '.join(out)

    def find(self, rx):
        m = re.search(rx, self.flat)
        if not m:
            return None
        a, b = m.start(), m.end()
        labs = [x[2] for x in self.bounds if x[0] < b and x[1] > a]
        raws = [x[3] for x in self.bounds if x[0] < b and x[1] > a]
        return m.group(0).strip(), labs, raws


_KIT = None


def kit_rows():
    global _KIT
    if _KIT is None:
        _KIT = [r for r in csv.DictReader(open(os.path.join(OUT, 'kit56', '연차보고서_섹션.csv'), encoding='utf-8-sig')) if r['지주명'] in G1]
    return _KIT


def ann_docs(lab, fy):
    """그 해 연차보고서 판(본공시 먼저) 목록."""
    docs = []
    if fy <= 2018:
        for r in csv.DictReader(open(os.path.join(OUT, '문서목록15b_gov_old.csv'), encoding='utf-8-sig')):
            if r['corp_label'] == lab and r['fy_or_date'] == f'FY{fy}' and r['status'] == '받음':
                v = '추가공시' if '추가' in r['report_nm'] else '정정공시' if '정정' in r['report_nm'] else '본공시'
                docs.append(AnnDoc('md', lab, fy, v, r['text_path'], dict(url=r['rcept_no_or_url'], title=r['report_nm'], fetched_at=r['fetched_at'],
                                                                         sha256=r['sha256'], src='문서목록15b_gov_old.csv')))
    elif fy <= 2023:
        for r in csv.DictReader(open(os.path.join(OUT, '연차보고서15_목록_g1.csv'), encoding='utf-8-sig')):
            if r['회사'] == lab and r['공시연도'] == str(fy + 1):
                pth = f'dart_out/text/ops15/연차보고서__{lab}__{fy + 1}__{r["공시유형"]}.md'
                if os.path.exists(os.path.join(ROOT, pth)):
                    docs.append(AnnDoc('md', lab, fy, r['공시유형'], pth, dict(url=r['파일_url'], title=r['제목'], fetched_at=r['fetched_at'],
                                                                              sha256=r['sha256'], src='연차보고서15_목록_g1.csv')))
    else:
        flist = {(r['지주명'], r['공시연도'], r['공시유형']): r for r in csv.DictReader(open(os.path.join(ROOT, 'handoff', '연차보고서_파일목록.csv'), encoding='utf-8-sig'))}
        vs = sorted({r['공시유형'] for r in kit_rows() if r['지주명'] == lab and r['공시연도'] == str(fy + 1)}, key=lambda v: (v != '본공시', v))
        for v in vs:
            secs = sorted([r for r in kit_rows() if r['지주명'] == lab and r['공시연도'] == str(fy + 1) and r['공시유형'] == v],
                          key=lambda r: (int(r['섹션순번']), int(r['chunk_seq'])))
            fm = flist[(lab, str(fy + 1), v)]
            docs.append(AnnDoc('kit', lab, fy, v, None, dict(url=fm['url'], title=fm['제목'], fetched_at=kst(fm['fetched_at']), sha256=fm['sha256'],
                                                             src='kit56/연차보고서_섹션.csv · handoff/연차보고서_파일목록.csv', file=fm['파일명']), secs))
        # 6차 섹션 글 다음 차례: gov_old 가 다시 받은 PDF 쪽 글(6차 섹션에 없는 부록 쪽을 찾을 때만 쓰임)
        for r in csv.DictReader(open(os.path.join(OUT, '문서목록15b_gov_old.csv'), encoding='utf-8-sig')):
            if r['corp_label'] == lab and r['fy_or_date'] == f'FY{fy}' and r['status'] == '받음' and r['text_path']:
                v = '추가공시' if '추가' in r['report_nm'] else '정정공시' if '정정' in r['report_nm'] else '본공시'
                docs.append(AnnDoc('md', lab, fy, 'gov_old ' + v, r['text_path'], dict(url=r['rcept_no_or_url'], title=r['report_nm'], fetched_at=r['fetched_at'],
                                                                                     sha256=r['sha256'], src='문서목록15b_gov_old.csv')))
    docs.sort(key=lambda d: (d.variant.startswith('gov_old'), d.variant != '본공시', d.variant))
    return docs


def gov_old_pdf_page(lab, fy, text):
    """FY2024·25: gov_old 가 다시 받은 PDF 쪽 글(md)에서 같은 글이 있는 쪽."""
    p = os.path.join(ROOT, f'dart_out/text/ops15b/연차보고서__{lab}__FY{fy}.md')
    if not os.path.exists(p):
        return None
    t = open(p, encoding='utf-8').read()
    parts = re.split(r'^## p\.(\d+)\s*$', t, flags=re.M)
    key = re.sub(r'\s+', '', text)[:60]
    for i in range(1, len(parts), 2):
        if key in re.sub(r'\s+', '', parts[i + 1]):
            return int(parts[i])
    return None


def build_ann(reps, rows, docs, mdouts, log):
    for lab in G1:
        for fy in ANN_FY[lab]:
            items = [I_PAY] + ([I_DIV] if lab in DIV_CORPS else [])
            dl = ann_docs(lab, fy)
            specs = ANN.get((lab, fy), [])
            got = {it: 0 for it in items}
            for spec in specs:
                (item, rx, where, dirn, dnote, cp), extra = spec[:6], (spec[6] if len(spec) > 6 else '')
                hit = None
                for d in dl:
                    hit = d.find(rx)
                    if hit:
                        break
                if not hit:
                    raise SystemExit(f'연차보고서 글 못 찾음 {lab} FY{fy} {item} {rx[:40]}')
                text, labs, raws = hit
                others = [x.variant for x in dl if x is not d and not x.variant.startswith('gov_old') and x.find(rx) is None]
                page = labs[0] if len(labs) == 1 else f'{labs[0]}~{labs[-1]}'
                notes = ([where] if where else []) + ([extra] if extra else [])
                if d.kind == 'kit':
                    notes.append('6차 섹션 글(PDF 원본은 이번 컨테이너에 없음)')
                    pp = gov_old_pdf_page(lab, fy, text)
                    if pp:
                        page += f' · PDF p.{pp}(gov_old 다시 받은 PDF 쪽 글 dart_out/text/ops15b/연차보고서__{lab}__FY{fy}.md)'
                if others:
                    notes.append(f'같은 해 {"·".join(others)} 판에는 이 글 없음')
                notes.append('source_text 는 PDF 글의 줄바꿈·빈칸을 빈칸 하나로 접은 것')
                notes.append('direction: 문단이 지주 수입·지출 어느 쪽인지 정하지 않음' if dirn is None else dnote)
                if item == I_DIV:
                    notes.append('부문 KPI·법인 KPI 비중 숫자는 이 보고서에 없음(' + SEARCH_NOTE.replace('찾은 범위: ', '') + ')')
                rows.append(dict(corp_label=lab, fy=fy, item_kind=item, counterparty=cp or NA, direction=dirn or NA, amount_krw=NA,
                                 basis_text=text, doc_kind='지배구조 및 보수체계 연차보고서', section_title=where or NA,
                                 source_text=text, rcept_no_or_url=d.meta['url'], page=page, note=' / '.join(n for n in notes if n),
                                 doc_name=d.meta['title'] + (f' ({d.variant})' if d.variant not in ('본공시',) and not d.variant.startswith('gov_old') else ''),
                                 collected_at=d.meta['fetched_at']))
                got[item] += 1
                key = (lab, fy, '연차보고서')
                mdouts.setdefault(key, []).append(('ann', d, labs, raws))
                docs.setdefault(('ann', lab, fy, d.variant), d)
            for d in dl:
                docs.setdefault(('ann', lab, fy, d.variant), d)
            for item in items:
                if got[item]:
                    continue
                if not dl:
                    if lab == 'NH농협금융지주':
                        why = '연차보고서 수집 실패 — dart_out/ops15/연차보고서15_목록_g1.csv 실패사유 「못 받음」(www.nhfngroup.com) — 원문 없음'
                    else:
                        why = '연차보고서 글 없음'
                    url, dn, ca = NA, f'{fy}년 지배구조 및 보수체계 연차보고서(수집 실패)', ''
                    for r in csv.DictReader(open(os.path.join(OUT, '연차보고서15_목록_g1.csv'), encoding='utf-8-sig')):
                        if r['회사'] == lab and r['공시연도'] == str(fy + 1):
                            url = r['게시판_url'] or NA
                    note = why
                    ca = FAIL_AT
                    note += f' / collected_at = 수집 실패를 적은 목록(연차보고서15_목록_g1.csv)의 git 마지막 커밋 시각'
                else:
                    d0 = dl[0]
                    url, dn, ca = d0.meta['url'], d0.meta['title'], d0.meta['fetched_at']
                    note = SEARCH_NOTE + f' — 판: {"·".join(x.variant for x in dl)}'
                    if item == I_DIV and lab == 'KB금융지주' and fy in (2024, 2025):
                        note += ' / 같은 해 「원소속회사가 자회사인 겸직 경영진」 문단(그 해 (겸직 임원 보수 지급·배분 기준) 행)의 내역에 「부문장」 없음'
                rows.append(dict(corp_label=lab, fy=fy, item_kind=item, counterparty=NA, direction=NA, amount_krw=NA, basis_text=NA,
                                 doc_kind='지배구조 및 보수체계 연차보고서', section_title=NA, source_text=NA, rcept_no_or_url=url or NA,
                                 page='전체 쪽' if dl else NA, note=note, doc_name=dn, collected_at=ca or NOW))
    # 사업보고서 Ⅷ
    for lab in G1:
        for fy in range(2019, 2026):
            r = [x for x in reps[(lab, fy)] if x['kind'] == '본'][0]
            md = MD(r['text_path'])
            s = [i for i in md.heads if re.search(r'임원의 보수', md.lines[i])][0]
            e = [i for i in md.heads if i > s][0]
            num, title, _ = md.head_of(s)
            specs = BIZ8.get((lab, fy), [])
            for rx, dirn, dnote, cp in specs:
                hit = None
                for i in range(s, e):
                    m = re.search(rx, md.lines[i])
                    if m:
                        hit = (i, m.group(0))
                        break
                if not hit:
                    raise SystemExit(f'Ⅷ 글 못 찾음 {lab} {fy} {rx[:40]}')
                i, text = hit
                tn = [int(re.fullmatch(r'\[표 (\d+)\]', md.lines[j]).group(1)) for j in range(i, s, -1) if re.fullmatch(r'\[표 \d+\]', md.lines[j])]
                in_table = md.lines[i].startswith('|')
                page = f'XML [절 {num}] 「{title}」' + (f' [표 {tn[0]}]' if in_table and tn else '')
                notes = ['사업보고서 「VIII. 임원 및 직원 등에 관한 사항 > 2. 임원의 보수 등」', dnote or 'direction: 문구가 지주 수입·지출 어느 쪽인지 정하지 않음']
                if fy == 2025:
                    cand = [p for p, t in pdf13_pages(lab).items() if re.sub(r'\s+', '', text.replace('|', ''))[:40] in re.sub(r'\s+', '', t)]
                    if cand:
                        page += f' · p.{cand[0]}(본문 PDF, 13차 보관)'
                for x in reps[(lab, fy)]:
                    if x['kind'] == '정정':
                        if x['text_path'] and os.path.exists(os.path.join(ROOT, x['text_path'])):
                            if nrm(text) not in nrm(open(os.path.join(ROOT, x['text_path']), encoding='utf-8').read()):
                                notes.append(f'정정 {x["rcept_no"]}: 같은 글 없음')
                        else:
                            notes.append(f'정정 {x["rcept_no"]}: XML 본문 없음 — 대조 못 함')
                rows.append(dict(corp_label=lab, fy=fy, item_kind=I_PAY, counterparty=cp, direction=dirn, amount_krw=NA, basis_text=text,
                                 doc_kind='사업보고서', section_title=f'VIII. 임원 및 직원 등에 관한 사항 > {title}', source_text=text,
                                 rcept_no_or_url=r['rcept_no'], page=page, note=' / '.join(notes), doc_name=r['report_nm'],
                                 collected_at=r['fetched_at']))
                mdouts.setdefault((lab, fy, '사업보고서'), []).append((s, e, md, r, f'[절 {num}] {title}'))
            if not specs and fy == 2025:
                ref = ''
                for i in range(s, e):
                    if '원소속' in md.lines[i] and '겸직' not in md.lines[i]:
                        seg = [x for x in re.split(r'(?=주\d\))', md.lines[i].replace('&cr;', '')) if '원소속' in x][0].strip()
                        tn = [int(re.fullmatch(r'\[표 (\d+)\]', md.lines[j]).group(1)) for j in range(i, s, -1) if re.fullmatch(r'\[표 \d+\]', md.lines[j])]
                        ref += (f' / (참고 사실) 같은 절 md {i + 1}행' + (f'([표 {tn[0]}] 안)' if md.lines[i].startswith('|') and tn else '')
                                + f' 주석 「{seg.strip("| ")}」 — 「겸직」 낱말·보수 지급 회사 글 없음')
                rows.append(dict(corp_label=lab, fy=fy, item_kind=I_PAY, counterparty=NA, direction=NA, amount_krw=NA, basis_text=NA,
                                 doc_kind='사업보고서', section_title=f'VIII. 임원 및 직원 등에 관한 사항 > {title}', source_text=NA,
                                 rcept_no_or_url=r['rcept_no'], page=f'XML [절 {num}] 「{title}」 전체',
                                 note=f'찾은 범위: 사업보고서 「2. 임원의 보수 등」 절 전체(md {s + 1}~{e}행), 낱말 「겸직」「겸임」「분담」「업무분담」「지급」 — '
                                      '「겸직 임원 보수는 ○○가 지급」·업무분담비율 정산 문구 없음' + ref,
                                 doc_name=r['report_nm'], collected_at=r['fetched_at']))


NOW = now_kst()


def _fail_at():
    import subprocess
    try:
        t = subprocess.run(['git', '-C', ROOT, 'log', '-1', '--format=%cI', '--', 'dart_out/ops15/연차보고서15_목록_g1.csv'],
                           capture_output=True, text=True).stdout.strip()
        return datetime.fromisoformat(t).astimezone(KST).isoformat(timespec='seconds') if t else NOW
    except Exception:
        return NOW


FAIL_AT = _fail_at()
REQ_LINES = None


def req_line(prefix):
    global REQ_LINES
    if REQ_LINES is None:
        REQ_LINES = open(os.path.join(OUT, 'REQUEST15b.md'), encoding='utf-8').read().split('\n')
    hits = [l.strip()[2:] if l.strip().startswith('* ') else l.strip() for l in REQ_LINES if l.strip().lstrip('* ').startswith(prefix)]
    assert len(hits) == 1, prefix
    return hits[0]


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})
    os.replace(tmp, path)


def ex300(t):
    t = t.strip()
    return t if len(t) <= 300 else t[:300]


def where_of(r):
    return f"G_g1.csv {r['corp_label']} FY{r['fy']} item_kind={r['item_kind']} counterparty={r['counterparty']} · {r['rcept_no_or_url'][:80]} · {r['page'][:80]}"


def checks(rows, reps):
    out = []
    t89 = req_line('KB·하나·우리·BNK·iM·JB FY2025')
    t90 = req_line('신한 FY2025: 브랜드수수료')
    t91 = req_line('KB·신한·하나·우리·NH FY2025 사업보고서 임원 보수 주석')
    t92 = req_line('신한·KB·하나 FY2017~FY2025 지배구조·보수체계 연차보고서')
    # G-1 브랜드·경영관리 수수료(KB·하나·우리; BNK·iM·JB 는 g2)
    for lab in ('KB금융지주', '하나금융지주', '우리금융지주'):
        for fyl in ('2025', '2019~2024'):
            fys = [2025] if fyl == '2025' else list(range(2019, 2025))
            rr = [r for r in rows if r['corp_label'] == lab and int(r['fy']) in fys and r['doc_kind'] == '사업보고서']
            fee = [r for r in rr if re.search(r'수수료수익', r['item_kind'])]
            b = [r for r in rr if r['item_kind'] == '(산정 기준 문단)']
            r0 = [r for r in rows if r['corp_label'] == lab and int(r['fy']) == fys[-1] and r['item_kind'] == '(산정 기준 문단)'][0]
            feetxt = '; '.join(f"FY{r['fy']} {r['counterparty']} {r['item_kind']} {int(r['amount_krw']) // 1000000:,}백만원" for r in fee if int(r['fy']) == fys[-1])
            extra = ''
            if lab == 'KB금융지주':
                extra = (' / (참고 사실) 사업보고서 「I. 5. 정관에 관한 사항」 사업목적 표에 「자회사등에 대한 상표권 및 특허권 등 지적재산권의 제공 | 영위」 행(FY2023~2025), '
                         '「XI. 그 밖에 투자자 보호… 우발부채」 소송 서술에 「상표권 사용료에 대한 익금불산입」(2013~15년도 법인세 경정청구 소송, FY2020~2024) — '
                         '지주 수익 계정·금액은 아님')
            if lab == '우리금융지주':
                extra = (' / (참고 사실) 사업보고서 「II. 2. 영업의 현황」 그룹 영업실적 표 주석(「K-IFRS 연결재무제표 기준」)에 「주2) 수수료 부문 : … + 브랜드사용수수료손익 + …」 '
                         '산식 글(FY2019~FY2024, FY2025 없음) — 지주 별도 금액·상대방 없음')
            out.append(dict(item_id='G-1', item_text=t89, corp_label=lab, fy=fyl, result='문서에 없음',
                            where=f"G_g1.csv {lab} FY{fyl} item_kind=(산정 기준 문단)" + (f" · 수수료수익 행 {len([r for r in fee])}건" if fee else ''),
                            rcept_no_or_url=r0['rcept_no_or_url'], page=r0['page'], source_excerpt=NA,
                            note=('브랜드(상표권) 수수료 수익: 별도 주석 특수관계자 거래 표·수수료 주석에 「브랜드」「상표」 계정 없음, Ⅱ에 산정 기준 문단 없음'
                                  + (f' / 특수관계자 표의 수수료 계정(FY{fys[-1]}): {feetxt}' if feetxt else ' / 특수관계자 표에 수수료수익 계정 없음') + extra)))
            out.append(dict(item_id='G-1b', item_text=t89, corp_label=lab, fy=fyl, result='문서에 없음',
                            where=f"G_g1.csv {lab} FY{fyl} 특수관계자 거래 행", rcept_no_or_url=r0['rcept_no_or_url'], page=r0['page'], source_excerpt=NA,
                            note='경영관리·용역 수수료 수익: 별도 주석 특수관계자 거래 표에 「경영관리」「용역」 수익 계정 없음(찾은 범위: 그 해 특수관계자 표·수수료 주석·Ⅱ)'
                                 + (f' / 수수료 계정: {feetxt}' if feetxt else '')))
    # G-2 신한 FY2025
    sh = [r for r in rows if r['corp_label'] == '신한금융지주' and r['fy'] == 2025]
    bf = [r for r in sh if r['item_kind'] == '브랜드수수료'][0]
    fee = [r for r in sh if r['item_kind'] == '수수료수익']
    out.append(dict(item_id='G-2', item_text=t90, corp_label='신한금융지주', fy='2025', result='원문 있음', where=where_of(bf),
                    rcept_no_or_url=bf['rcept_no_or_url'], page=bf['page'], source_excerpt=ex300(bf['source_text']),
                    note=('「브랜드수수료」는 별도 주석 순수수료손익 표에 합계 1행(원문 숫자 ' + bf['note'].split('원문 숫자 ')[1].split(' ')[0] + ')만 — 자회사별 「브랜드수수료」 내역 없음'
                          f' / 같은 해 특수관계자 거래 표의 「수수료수익」 행 회사별 {len(fee)}건(' + '; '.join(f"{r['counterparty']} {int(r['amount_krw']) // 1000000:,}" for r in fee)
                          + ' 백만원) — 그 표에 「브랜드」 낱말 없음')))
    out.append(dict(item_id='G-2b', item_text=t90, corp_label='신한금융지주', fy='2025', result='문서에 없음', where=where_of(bf),
                    rcept_no_or_url=bf['rcept_no_or_url'], page='XML 사업보고서 전체(II·III·별도 주석)', source_excerpt=NA,
                    note='산정 기준(요율·기준 수익): 사업보고서 전체에서 「브랜드」 낱말은 순수수료손익 표 2줄(당기·전기)뿐, 요율·기준 수익 글 없음'))
    # G-3 사업보고서 Ⅷ 임원 보수 FY2025
    for lab in G1:
        rr = [r for r in rows if r['corp_label'] == lab and r['fy'] == 2025 and r['doc_kind'] == '사업보고서' and r['item_kind'] == I_PAY]
        for r in rr:
            ok = r['source_text'] != NA
            prev = ''
            if not ok and lab == '우리금융지주':
                p = [x for x in rows if x['corp_label'] == lab and x['fy'] == 2024 and x['doc_kind'] == '사업보고서' and x['item_kind'] == I_PAY]
                if p:
                    prev = f' / FY2024 사업보고서에는 「{p[0]["source_text"]}」(G_g1.csv 우리금융지주 FY2024 행)'
            out.append(dict(item_id='G-3', item_text=t91, corp_label=lab, fy='2025', result='원문 있음' if ok else '문서에 없음', where=where_of(r),
                            rcept_no_or_url=r['rcept_no_or_url'], page=r['page'], source_excerpt=ex300(r['source_text']) if ok else NA,
                            note=(('「겸직 임원 보수는 ○○가 지급」 꼴 문구는 없고 이 주석 1줄; 업무분담비율 정산 문구 없음' if ok else r['note']) + prev)))
    # G-4 신한·KB·하나 FY2017~2025 연차보고서 겸직 부문장
    for lab in ('신한금융지주', 'KB금융지주', '하나금융지주'):
        for fy in range(2017, 2026):
            rr = [r for r in rows if r['corp_label'] == lab and r['fy'] == fy and r['item_kind'] == I_DIV]
            pay = [r for r in rows if r['corp_label'] == lab and r['fy'] == fy and r['item_kind'] == I_PAY and r['doc_kind'] != '사업보고서' and r['source_text'] != NA]
            for r in rr:
                ok = r['source_text'] != NA
                out.append(dict(item_id='G-4', item_text=t92, corp_label=lab, fy=str(fy), result='원문 있음' if ok else '문서에 없음', where=where_of(r),
                                rcept_no_or_url=r['rcept_no_or_url'], page=r['page'], source_excerpt=ex300(r['source_text']) if ok else NA,
                                note=('부문 KPI·법인 KPI 비중 숫자 없음' + ('' if ok else '; 겸직 부문장 성과평가·보수 지급 회사 글 없음')
                                      + (f' / 같은 해 겸직 임원 보수 지급·배분 문단 {len(pay)}건(G_g1.csv {lab} FY{fy} item_kind={I_PAY})' if pay else ''))))
    return out


def write_mds(mdouts):
    os.makedirs(MDDIR, exist_ok=True)
    n = 0
    for (lab, fy, kind), parts in sorted(mdouts.items(), key=lambda x: (G1.index(x[0][0]), x[0][1], x[0][2])):
        path = os.path.join(MDDIR, f'{lab}__FY{fy}__{kind}.md')
        out = []
        seen = set()
        if kind == '사업보고서':
            r = parts[0][3]
            out.append(f'# {lab} FY{fy} 사업보고서 — 작업 G 원문(절·주석 글 그대로)')
            out.append('')
            out.append(f'- 문서: {r["report_nm"]} · rcept_no {r["rcept_no"]} · 접수 {r["rcept_dt"]} · 받은 시각 {r["fetched_at"]}')
            out.append(f'- 글: {r["text_path"]} (OpenDART XML → md, 줄 번호는 이 md 기준)')
            out.append('')
            for a, b, md, rr, title in sorted(parts, key=lambda x: x[0]):
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                out.append(f'## {title} (md {a + 1}~{b}행)')
                out.append('')
                out.extend(md.lines[a:b])
                out.append('')
        else:
            d0 = parts[0][1]
            out.append(f'# {lab} FY{fy} 지배구조 및 보수체계 연차보고서 — 작업 G 원문(쪽·섹션 글 그대로)')
            out.append('')
            for _, d, labs, raws in parts:
                for lb, raw in zip(labs, raws):
                    k = (d.variant, lb)
                    if k in seen:
                        continue
                    seen.add(k)
                    out.append(f'## {d.meta["title"]} ({d.variant}) · {lb}')
                    out.append(f'- 출처: {d.meta["url"]} · sha256 {d.meta["sha256"]} · 받은 시각 {d.meta["fetched_at"]} · 글 {d.path or d.meta["src"]}')
                    out.append('')
                    out.append(raw.strip('\n'))
                    out.append('')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out) + '\n')
        n += 1
    return n


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


def doclist(reps, docs):
    out = []
    for lab in G1:
        for fy in range(2019, 2026):
            for r in sorted(reps[(lab, fy)], key=lambda x: (x['kind'] != '본', x['rcept_no'])):
                st = '014' if r['doc_status'] == '014' else ('받음' if r['text_path'] and os.path.exists(os.path.join(ROOT, r['text_path'])) else '실패')
                out.append(dict(doc_kind='사업보고서', corp_label=lab, fy_or_date=f'FY{fy}', report_nm=r['report_nm'], rcept_no_or_url=r['rcept_no'],
                                rcept_dt=r['rcept_dt'], raw_path=('dart_out/' + r['raw_path']) if r['raw_path'] else '', sha256=r['raw_sha256'],
                                fetched_at=r['fetched_at'], text_path=r['text_path'], status=st,
                                note=('본 보고서 — 별도 주석 특수관계자·기타영업손익·순수수료손익, II, VIII 2 사용' if r['kind'] == '본'
                                      else '정정판 — 같은 행 글이 있는지 대조' + ('' if st == '받음' else f' ({r["doc_message"] or r["report_nm"]}, 대조 못 함)'))))
    # 연차보고서 원본 PDF 경로: sha256 이 같은 파일(dart_out/raw/governance15/<회사>/*.pdf, gov_old raw_path)
    sha2raw, sha2dt = {}, {}
    for lab in G1:
        for pth in sorted(glob.glob(os.path.join(ROOT, 'dart_out', 'raw', 'governance15', lab, '*.pdf'))):
            sha2raw.setdefault(sha_file(pth), os.path.relpath(pth, ROOT))
    for r in csv.DictReader(open(os.path.join(OUT, '문서목록15b_gov_old.csv'), encoding='utf-8-sig')):
        if r['status'] == '받음' and r['sha256']:
            if r['raw_path'] and os.path.exists(os.path.join(ROOT, r['raw_path'])):
                sha2raw.setdefault(r['sha256'], r['raw_path'])
            sha2dt.setdefault(r['sha256'], r['rcept_dt'])
    for r in csv.DictReader(open(os.path.join(OUT, '연차보고서15_목록_g1.csv'), encoding='utf-8-sig')):
        if r['sha256']:
            sha2dt.setdefault(r['sha256'], r['공시일'])
    for key, d in sorted(((k, v) for k, v in docs.items() if k[0] == 'ann'), key=lambda x: (G1.index(x[0][1]), x[0][2], x[0][3])):
        _, lab, fy, v = key
        raw = sha2raw.get(d.meta['sha256'], '')
        dt = sha2dt.get(d.meta['sha256'], '')
        nt = f'목록: {d.meta["src"]}' + (f' · 파일 {d.meta.get("file")}' if d.meta.get('file') else '')
        if not raw:
            nt += ' · 원본 PDF: 이번 컨테이너에 sha256 이 같은 파일 없음(글은 text_path)'
        if not dt:
            nt += ' · 게시일: 목록에 없음'
        out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label=lab, fy_or_date=f'FY{fy}',
                        report_nm=d.meta['title'] + (f' ({v})' if v != '본공시' and not v.startswith('gov_old') else ''),
                        rcept_no_or_url=d.meta['url'], rcept_dt=dt, raw_path=raw, sha256=d.meta['sha256'], fetched_at=d.meta['fetched_at'],
                        text_path=d.path or 'dart_out/ops15/kit56/연차보고서_섹션.csv', status='받음', note=nt))
    # 목록에 있으나 글이 없는 판(받기 실패) — NH 는 아래 따로
    for r in csv.DictReader(open(os.path.join(OUT, '연차보고서15_목록_g1.csv'), encoding='utf-8-sig')):
        pth = f'dart_out/text/ops15/연차보고서__{r["회사"]}__{r["공시연도"]}__{r["공시유형"]}.md'
        if r['회사'] in G1 and r['회사'] != 'NH농협금융지주' and not os.path.exists(os.path.join(ROOT, pth)):
            out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label=r['회사'], fy_or_date=f'FY{int(r["공시연도"]) - 1}',
                            report_nm=r['제목'] + f' ({r["공시유형"]})', rcept_no_or_url=r['파일_url'] or r['게시판_url'] or NA, rcept_dt=r['공시일'],
                            raw_path='', sha256=r['sha256'], fetched_at=r['fetched_at'], text_path='', status='실패',
                            note=f'연차보고서15_목록_g1.csv 실패사유: {r["실패사유"]} — 이번 작업은 웹 수집 안 함(같은 해 다른 판만 봄)'))
    for fy in range(2019, 2024):
        out.append(dict(doc_kind='지배구조 및 보수체계 연차보고서', corp_label='NH농협금융지주', fy_or_date=f'FY{fy}', report_nm=f'{fy}년 지배구조 및 보수체계 연차보고서',
                        rcept_no_or_url=NA, rcept_dt='', raw_path='', sha256='', fetched_at='', text_path='', status='없음',
                        note='dart_out/ops15/연차보고서15_목록_g1.csv 에 「못 받음」(공시연도 ' + str(fy + 1) + ') — 이번 작업은 웹 수집 안 함'))
    out.append(dict(doc_kind='사업보고서 본문 PDF 텍스트(13차 보관)', corp_label='·'.join(G1), fy_or_date='FY2025', report_nm='13차_지주관리유형_텍스트.zip 텍스트/사업보고서__<회사>.md',
                    rcept_no_or_url='handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip', rcept_dt='', raw_path='handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip',
                    sha256=sha_file(ZIP13), fetched_at='2026-10-29T14:01:29+09:00', text_path='(zip 안)', status='받음',
                    note='FY2025 행 page 의 「p.N(본문 PDF, 13차 보관)」 찾기에만 씀 · fetched_at = 이 zip 이 저장소에 들어간 커밋 시각(git a3c4c31) · 게시일 칸 해당 없음(묶음 파일)'))
    return out


def write_rest(reps, rows, docs, mdouts, log, basis_found):
    ck = checks(rows, reps)
    write_csv(os.path.join(FRAG, '확인_G_g1.csv'), ck, CCOLS)
    n = write_mds(mdouts)
    dl = doclist(reps, docs)
    write_csv(os.path.join(OUT, '문서목록15b_G_g1.csv'), dl, DCOLS)
    print('확인 rows', len(ck), 'md files', n, '문서목록 rows', len(dl))


def main():
    reps = reports()
    rows, docs, mdouts, log = [], {}, {}, []
    build_rp(reps, rows, docs, mdouts, log)
    build_extra(reps, rows, mdouts)
    basis_found = build_basis(reps, rows)
    build_ann(reps, rows, docs, mdouts, log)
    order = {g: i for i, g in enumerate(G1)}
    rows.sort(key=lambda r: (order[r['corp_label']], int(r['fy']), 0 if r['doc_kind'] == '사업보고서' else 1))
    write_csv(os.path.join(FRAG, 'G_g1.csv'), rows, COLS)
    write_rest(reps, rows, docs, mdouts, log, basis_found)
    for l in log:
        print('LOG', l)
    print('G_g1 rows', len(rows), '문서에 없음 source_text', sum(r['source_text'] == NA for r in rows))


if __name__ == '__main__':
    main()
