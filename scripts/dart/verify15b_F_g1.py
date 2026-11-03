"""15차 확장 작업 F·F-2·F-3 g1(KB·신한·하나·우리·NH) 독립 검증 — 인자 없음, exit 0 = 통과 / 1 = 실패.
결과: dart_out/ops15/verify15b_F_g1.txt (요약 + FAIL 줄 + 표본 대조 줄).

생성기(ops15b_F_g1.py)를 import 하지 않고 출처 글을 따로 읽어 본다.

(a) 원문 대조(COMMON15b): source_text 와 원문 칸(chair·members·cadence·agenda·agenda_list·duty·concurrent_or_dispatched,
    F2 established, F3 function·unit_name, 확인 source_excerpt)은 「문서에 없음」이 아니면 공백·줄바꿈을 지운 칸 글이
    출처 글(공백·줄바꿈 지움) 안에 이어서 그대로 있어야 함. OpenDART XML md 출처에서만 md 표지 「|」「<br>」를 양쪽에서 지움.
    출처 글 = 사업보고서 md(첫 「### [절」 앞 머리 버림, 「### [절 n] 」 머리표·「[표 n]」「[표 끝]」 줄 지움),
    연차보고서 FY2023 md(「## p.N」 줄 지움), 연차보고서 FY2024·25 = kit56 섹션 본문(섹션순번·chunk_seq 순).
    page 위치 안: 사업보고서 「XML [절 n] … [표 m] ~ …」 → 그 절(표가 적혔으면 그 표)부터 끝 표지까지,
    「p.N(본문 PDF, 13차 보관)」 → 13차 PDF 글 N~M 쪽에 그 칸의 줄이 있는지(표 칸 순서가 달라 줄 단위),
    연차보고서 md 「p.N~M」 → 그 쪽들, kit 「p.N~M (6차 섹션 시작페이지)」 → 시작페이지가 N~M 인 섹션 글.
    page 위치 밖이면 note 에 그 칸이 나온 곳(「[절 n]」 또는 「p.N」)이 적혀 있어야 함.
    kit 행은 같은 sha256 의 PDF 쪽 글(gov_old 다시 받은 md·13차 연차보고서 md)에서 실제 PDF 쪽도 찾아 page 칸의 「PDF p.」와 맞춤.
(b) 열 이름·순서·utf-8-sig BOM, 출처·page·doc_name·collected_at 빈칸 0, collected_at 꼴(+09:00).
(c) 범위: F 회사×FY2023~25×(사업보고서·연차보고서), F2 회사×FY2024·25×5개 위원회, F3 회사×(준법·위험·감사).
    빠짐 훑기: 출처 글의 「협의회|협의체|회의체」 낱말(앞 낱말 붙임)이 F 행 글에 없으면 EXCL(검토해 뺀 것, 사유 적음)에 있어야 함.
(d) 「문서에 없음」 반박: F2 established 「문서에 없음」 칸 — 같은 회사 FY 사업보고서·연차보고서에서 그 위원회 이름 가까이
    「신설|설치」 글이 있으면 FAIL(검토해 뺀 것은 EST_OK). F 의 「문서에 없음」 행은 note 에 찾은 범위가 있어야 함.
(e) 숫자: F held_count ← note 「held_count 원문 「…」」 글이 그 칸·출처에 있고 숫자가 같음, (판단) 셈은 날짜 수 다시 셈.
    F2 held_count ← agenda_list_text 표의 개최일자 행 수·서로 다른 날짜 수를 다시 세고 note 숫자와 맞춤, 연차보고서 「총 N회」 글은
    그 연차보고서에서 다시 찾아 숫자를 맞춤. F3 headcount ← note 의 원문 글이 출처에 있고 숫자(또는 「(판단)」 합)가 같음.
(f) function_kw·subsidiary_related 재계산, note 에 추정 낱말(추정·아마·듯·보인다·짐작·의도·~로 보임) 없음(「…」 인용 밖).
(g) 확인_ CSV: item_text 가 REQUEST15b.md 의 「함께 볼 것」 줄 글 그대로, 그 줄의 g1 대상(NH 내부통제위원회 첫 개최·첫 안건,
    신한 자회사경영관리위원회 시점·사유)마다 행, result 값, source_excerpt 대조·300자 이하.
(h) 비밀: 산출 파일에 DART_API_KEY 값·crtfc_key·40자리 16진 키 꼴 없음. git 추적 파일에 dart_out/raw·dart_out/text·PDF 없음.
"""
import csv, os, re, sys, glob, subprocess, zipfile, bisect

csv.field_size_limit(10 ** 9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'dart_out', 'ops15')
FRAG = os.path.join(OUT, '조각')
NA = '문서에 없음'
G1 = ['KB금융지주', '신한금융지주', '하나금융지주', '우리금융지주', 'NH농협금융지주']
ZIP13 = os.path.join(ROOT, 'handoff', '13차_지주관리유형', '13차_지주관리유형_텍스트.zip')

COLS = {
    'F_g1.csv': ['corp_label', 'fy', 'body_name', 'function_kw', 'chair_text', 'members_text', 'cadence_text', 'held_count', 'agenda_text',
                 'doc_kind', 'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at'],
    'F2_g1.csv': ['corp_label', 'fy', 'committee', 'established', 'held_count', 'agenda_list_text', 'subsidiary_related', 'members_text',
                  'rcept_no', 'page', 'note', 'doc_name', 'collected_at'],
    'F3_g1.csv': ['corp_label', 'fy', 'function', 'unit_name', 'headcount', 'concurrent_or_dispatched', 'duty_text', 'rcept_no_or_url',
                  'page', 'note', 'doc_name', 'collected_at'],
    '확인_F_g1.csv': ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note'],
}
TEXT_COLS = {
    'F_g1.csv': ['source_text', 'chair_text', 'members_text', 'cadence_text', 'agenda_text'],
    'F2_g1.csv': ['agenda_list_text', 'members_text', 'established'],
    'F3_g1.csv': ['function', 'unit_name', 'concurrent_or_dispatched', 'duty_text'],
    '확인_F_g1.csv': ['source_excerpt'],
}
KW_F = ['협의회', '협의체', '회의체', '위원회', '그룹', '리스크', '내부통제', '준법', '감사', '소비자보호', 'ESG', '디지털', 'AI', 'IT',
        '정보보호', '브랜드', '시너지', '개최', '분기', '매월']

# (c) 훑기에서 검토해 뺀 낱말 — (회사, 낱말(공백 지움) 안에 든 글) → 사유(사실만)
EXCL = [
    # 외부 기관·단체·이니셔티브(지주·자회사 회의체 아님)
    ('*', '상장사협의회', '외부 단체(한국상장회사협의회)'), ('*', '상장회사협의회', '외부 단체'), ('*', '재무정보공개협의체', '외부 이니셔티브(TCFD·TNFD)'),
    ('*', '탄소회계금융협의체', '외부 이니셔티브(PCAF)'), ('*', '임팩트공시협의체', '외부 이니셔티브'), ('*', '교회협의회', '외부 단체(기부처)'),
    ('*', '사회복지협의회', '외부 단체(기부처)'), ('*', '혁신협의회', '사외이사 경력란의 외부 기관'), ('*', '발전협의회', '사외이사 경력란의 외부 기관'),
    ('*', '조합운영협의회', '사외이사 경력란의 외부 기관'), ('*', '공동매각협의회', '채권단(외부) 협의회'), ('*', '제22차협의회', '외부 협약 회의(선박 해양)'),
    ('*', '조정협의회', '감사인 의견불일치·재무제표 불일치 조정협의회 서식 항목(「해당사항 없음」)'),
    # 자회사 한 곳의 내부 기구로 적힌 것
    ('KB금융지주', '재무전략협의회', '「㈜국민은행 재무전략협의회(ALCO)」 — 자회사 기구로 적힘'),
    ('*', '여신심사협의회', '「해당 자회사 등의 여신심사협의회」 — 자회사 기구'), ('*', '심사협의체', '은행 여신 승인 서술(자회사 기구)'),
    ('신한금융지주', '출시협의체', '「은행은 사모펀드 선정 출시 및 상품선정 출시협의체」 — 자회사 제재 서술'),
    ('우리금융지주', '인사협의회', '우리은행 제재 표 「인사협의회 결의」 — 자회사 기구'),
    ('KB금융지주', '경영협의회', '사업보고서 FY2025 제재 표(자회사 조치 내역) 「분기별 경영협의회」 — 자회사 기구(원문 표 행의 회사)'),
    # 일반 낱말(이름 아님) — 「협의회를」「협의회는」처럼 앞 이름 없이 나온 것, 「관련 회의체」 등
    ('*', '관련회의체', '일반 낱말'), ('*', '내부협의체', '일반 낱말(「ESG 관련 내부 협의체 운영 현황」 보고사항)'), ('*', '산하협의체', '일반 낱말(하나 내부통제협의체 설치 서술 — 그 행 note)'),
    ('NH농협금융지주', '이사회관련회의체', '일반 낱말'), ('신한금융지주', 'CEO와이사회의협의회', '사외이사 평가 의견 안 「…협의회 개최가 필요」(있는 회의체로 적히지 않음)'),
    ('KB금융지주', '리스크관리협의체', '(판단) 사업보고서 금리리스크(IRRBB) 정성 공시 「리스크관리협의체 결의」 — 어느 회사 기구인지 문단에 없음'),
    ('KB금융지주', '수석심사역협의회', '은행 대출상품 설명 표(자회사 기구)'), ('KB금융지주', '다양한협의체', '외부(대체금리 전환 관련 협의체)'),
    ('KB금융지주', '글로벌협의체', '외부 이니셔티브(TNFD)'), ('KB금융지주', '리스크관련협의체', '(판단) 사업보고서 연결 주석 일반 낱말'),
    ('KB금융지주', '협의를통해협의회', '일반 낱말'), ('KB금융지주', '위원으로하는협의체', '「㈜국민은행」 LIBOR 전환 프로그램 서술(자회사)'),
    ('신한금융지주', '기본정책은리스크관리협의회', '「신한카드의 신용리스크에 관한 기본정책은 리스크관리협의회에서 결정」 — 자회사 기구'),
    ('신한금융지주', '리스크관리협의회', '사업보고서 연결 주석 — 신한카드 등 자회사 기구로 적힘'),
    ('신한금융지주', '리스크회의체', '「각 종속기업의 위험관리위원회 및 경영진차원의 리스크회의체」 — 자회사 기구(일반 낱말)'),
    ('신한금융지주', '모범규준상경영관리협의회', '「그룹경영회의(모범규준 상 경영관리협의회)」 — 그룹경영회의 행의 다른 이름(원문 괄호)'),
    ('신한금융지주', '모범규준상위험관리협의회', '「그룹리스크협의회(모범규준 상 위험관리협의회)」 — 그룹리스크협의회 행의 다른 이름(원문 괄호)'),
    ('신한금융지주', '경영관리및위험관리협의회', '「경영관리 및 위험관리 협의회를 지속 설치·운영」 — 그룹경영회의·그룹리스크협의회 행 서술'),
    ('신한금융지주', '위하여협의회', '그룹리스크협의회규정 조문의 「협의회」(그룹리스크협의회)'),
    ('NH농협금융지주', '공정가액평가협의회', '(판단) 연결재무제표 주석 공정가치 서술 — 어느 회사 기구인지 문단에 없음'),
    ('NH농협금융지주', '판단하여협의회', '최고경영자협의회규정 조문의 「협의회」'), ('NH농협금융지주', '위원장이협의회', '최고경영자협의회규정 조문의 「협의회」'),
    ('NH농협금융지주', '간사로서협의회', '최고경영자협의회규정 조문의 「협의회」'),
    ('우리금융지주', '채권금융기관협의회', '외부(채권단) 협의회'), ('우리금융지주', '일자회의체', '표 머리 칸 글(「일자 | 회의체」)'), ('우리금융지주', '내역회의체', '표 머리 칸 글(승계 내역 표)'),
    ('우리금융지주', '제13차그룹리스크협의회', '리스크관리위원회 안건 목록의 회차 표기 — 원문 이름 「그룹리스크협의회」(같은 해 「그룹리스크관리협의회」 행의 회차 인용인지 원문으로 확인 안 됨)'),
    ('우리금융지주', '기타협의회', '보고사항 목록 낱말(그룹리스크관리협의회 규정 조문)'), ('우리금융지주', '보고사항·협의회', '보고사항 목록 낱말'),
    ('우리금융지주', '보고사항-협의회', '보고사항 목록 낱말'), ('우리금융지주', '하여협의회', '그룹리스크관리협의회 규정 조문의 「협의회」'),
    ('우리금융지주', '부서로하여금협의회', '그룹리스크관리협의회 규정 조문의 「협의회」'), ('우리금융지주', '정한협의회', '조문의 「협의회」'),
    ('우리금융지주', '의한협의회', '조문의 「협의회」'),
    ('하나금융지주', '실무협의회', '「각 관계회사는 자체 리스크관련 위원회 및 실무협의회를 통하여」 — 자회사 기구(일반 낱말)'),
    ('하나금융지주', '거쳐협의회', '경영관리협의회 규정 조문의 「협의회」'),
]
EST_OK = {  # (회사, FY, 위원회) → 사유 : established 반박 후보를 검토해 둔 것(사실만)
    ('KB금융지주', '2024', '감사위원회'): '걸린 글은 「감사위원회 위원의 독립성」·사외이사 경력 칸 — KB 사업보고서에 「감사위원회 설치 여부」 칸 없음',
    ('KB금융지주', '2025', '감사위원회'): '걸린 글은 「감사위원회 위원의 독립성」·사외이사 경력 칸 — KB 사업보고서에 「감사위원회 설치 여부」 칸 없음',
    ('우리금융지주', '2025', '자회사대표이사후보추천위원회'): '걸린 글은 「총 7개의 이사회내 위원회를 설치하여 운영」(날짜 없음)',
    ('우리금융지주', '2025', '감사위원회'): '걸린 글은 「설치가 의무화된 … 감사위원회」(날짜 없음)',
    ('NH농협금융지주', '2024', '임원후보추천위원회'): '걸린 글은 「(2) 사외이사 선출을 위한 별도 위원회 설치 시 내용」 머리(설치일 글 아님)',
    ('NH농협금융지주', '2025', '임원후보추천위원회'): '걸린 글은 「(2) 사외이사 선출을 위한 별도 위원회 설치 시 내용」 머리(설치일 글 아님)',
    ('신한금융지주', '2025', '위험관리위원회'): '걸린 글은 「주) 2025년 3월 내부통제위원회 신설」(다른 위원회)',
    ('신한금융지주', '2024', '내부통제위원회'): 'FY2024 는 설치 전 「문서에 없음」 행 — 2025.3 주총 안건 글은 그 행 note 에',
    ('하나금융지주', '2024', '내부통제위원회'): 'FY2024 는 설치 전 「문서에 없음」 행 — 설치 근거 마련 글은 그 행 note 에',
    ('KB금융지주', '2024', '내부통제위원회'): 'FY2024 는 설치 전 「문서에 없음」 행',
    ('우리금융지주', '2024', '내부통제위원회'): 'FY2024 는 설치 전 「문서에 없음」 행',
    ('하나금융지주', '2025', '리스크관리위원회'): '걸린 글은 이사회 결의 목록(감사부문장 임면 등) — 설치일 글 아님',
    ('하나금융지주', '2024', '리스크관리위원회'): '걸린 글은 이사회 결의 목록 — 설치일 글 아님',
}

_docs = {}


def S(t):
    return re.sub(r'\s+', '', t or '')


def SX(t):
    return re.sub(r'\s+', '', (t or '').replace('<br>', '').replace('|', ''))


def rows_of(path):
    return list(csv.DictReader(open(path, encoding='utf-8-sig')))


BRMETA = {r['rcept_no']: r for r in rows_of(os.path.join(OUT, '사업보고서_원문.csv'))}
ARL = []
for _g in ('g1', 'g2'):
    _p = os.path.join(OUT, f'연차보고서15_목록_{_g}.csv')
    if os.path.exists(_p):
        ARL += rows_of(_p)
KITF = rows_of(os.path.join(ROOT, 'handoff', '연차보고서_파일목록.csv'))
KIT = rows_of(os.path.join(OUT, 'kit56', '연차보고서_섹션.csv'))
GOV = rows_of(os.path.join(OUT, '문서목록15b_gov_old.csv')) if os.path.exists(os.path.join(OUT, '문서목록15b_gov_old.csv')) else []


class Doc:
    def __init__(self, kind, segs, meta):
        """segs: [(label, stripped)] — label: BR=(절, 표|None), AR_md=쪽, kit=시작페이지(int|None), P=쪽."""
        self.kind, self.segs, self.meta = kind, segs, meta
        self.full = ''.join(s for _, s in segs)
        self.off = []
        n = 0
        for _, s in segs:
            self.off.append(n)
            n += len(s)

    def label_at(self, pos):
        i = bisect.bisect_right(self.off, pos) - 1
        return self.segs[max(0, i)][0]

    def find_all(self, v, lim=30):
        out, p = [], self.full.find(v)
        while p >= 0 and len(out) < lim:
            out.append(p)
            p = self.full.find(v, p + 1)
        return out


def load_br(rcept):
    m = BRMETA.get(rcept)
    if not m or not m.get('text_path') or not os.path.exists(os.path.join(ROOT, m['text_path'])):
        return None
    segs, started, sec, tab = [], False, None, None
    for ln in open(os.path.join(ROOT, m['text_path']), encoding='utf-8').read().split('\n'):
        mm = re.match(r'^### \[절 (\d+)\] ?(.*)$', ln)
        if mm:
            started, sec, tab = True, int(mm.group(1)), None
            segs.append(((sec, None), SX(mm.group(2))))
            continue
        if not started:
            continue
        mt = re.fullmatch(r'\s*\[표 (\d+)\]\s*', ln)
        if mt:
            tab = int(mt.group(1))
            continue
        if re.fullmatch(r'\s*\[표 끝\]\s*', ln):
            tab = None
            continue
        s = SX(ln)
        if s:
            segs.append(((sec, tab), s))
    return Doc('BR', segs, dict(m, doc_name=m['report_nm'], collected=m['fetched_at'], corp=m['label'], fy=m['fy']))


def md_pages(text):
    segs, started, pg = [], False, None
    for ln in text.split('\n'):
        mm = re.match(r'^## p\.(\d+)(\s.*)?$', ln)
        if mm:
            started, pg = True, int(mm.group(1))
            continue
        if started:
            s = S(ln)
            if s:
                segs.append((pg, s))
    return segs


def load_ar(url):
    for r in ARL:
        if r['파일_url'].split(' (')[0] == url:
            p = os.path.join(ROOT, 'dart_out', 'text', 'ops15', f"연차보고서__{r['회사']}__{r['공시연도']}__{r['공시유형']}.md")
            if os.path.exists(p):
                return Doc('AR_md', md_pages(open(p, encoding='utf-8').read()),
                           dict(corp=r['회사'], fy=str(int(r['공시연도']) - 1), typ=r['공시유형'], doc_name=r['제목'], collected=r['fetched_at'],
                                sha=r['sha256']))
    for r in KITF:
        if r['url'] == url and '지배구조' in r['파일명']:
            ks = sorted([k for k in KIT if k['파일명'] == r['파일명']], key=lambda k: (int(k['섹션순번']), int(k['chunk_seq'])))
            segs = []
            for k in ks:
                s = S(k['본문'])
                if s:
                    segs.append((int(k['시작페이지']) if k['시작페이지'].strip().isdigit() else None, s))
            return Doc('AR_kit', segs, dict(corp=r['지주명'], fy=str(int(r['공시연도']) - 1), typ=r['공시유형'], doc_name=r['제목'],
                                            collected=r['fetched_at'], sha=r['sha256'], fname=r['파일명']))
    return None


def doc(ref):
    if ref not in _docs:
        _docs[ref] = load_br(ref) if re.fullmatch(r'\d{14}', ref) else load_ar(ref)
    return _docs[ref]


_z = {}


def zip13(member):
    if member not in _z:
        z = zipfile.ZipFile(ZIP13)
        name = f'13차_지주관리유형/텍스트/{member}'
        _z[member] = z.read(name).decode('utf-8') if name in z.namelist() else None
    return _z[member]


def pdf13_br(corp):
    k = 'P13BR:' + corp
    if k not in _docs:
        t = zip13(f'사업보고서__{corp}.md')
        _docs[k] = Doc('P', md_pages(t), {}) if t else None
        if t:
            _docs[k].meta['rcept'] = (re.search(r'dart_out/doc/(\d{14})/', t[:2000]) or [None, ''])[1]
    return _docs[k]


def pdf_ar_by_sha(sha):
    """kit 와 같은 sha256 의 PDF 쪽 글(gov_old md 또는 13차 연차보고서 md) → (Doc, 출처 글)."""
    k = 'PAR:' + sha
    if k in _docs:
        return _docs[k]
    res = None
    for g in GOV:
        if g.get('sha256') == sha and g.get('text_path') and os.path.exists(os.path.join(ROOT, g['text_path'])):
            res = (Doc('P', md_pages(open(os.path.join(ROOT, g['text_path']), encoding='utf-8').read()), {}), g['text_path'])
            break
    if res is None:
        for c in G1:
            t = zip13(f'연차보고서__{c}.md')
            if t and f'sha256 {sha}' in t[:3000]:
                res = (Doc('P', md_pages(t), {}), f'13차 연차보고서__{c}.md')
                break
    _docs[k] = res
    return res


# ───────── page → 구역 ─────────
def br_side(s):
    ms, mt = re.search(r'\[절 (\d+)\]', s), re.search(r'\[표 (\d+)\]', s)
    return (int(ms.group(1)), int(mt.group(1)) if mt else None) if ms else None


def region(d, page):
    """page 글 → 구역 글 목록(공백 지움). 못 읽으면 None."""
    if d.kind == 'BR':
        xml = page.split(' / ')[0]
        sides = [br_side(x) for x in xml.split(' ~ ')]
        sides = [x for x in sides if x]
        if not sides:
            return None
        a, b = sides[0], sides[-1]
        i0 = next((i for i, (lab, _) in enumerate(d.segs) if lab[0] == a[0] and (a[1] is None or lab[1] == a[1])), None)
        i1 = max((i for i, (lab, _) in enumerate(d.segs) if lab[0] == b[0] and (b[1] is None or lab[1] == b[1])), default=None)
        if i0 is None or i1 is None or i1 < i0:
            return None
        return [''.join(s for _, s in d.segs[i0:i1 + 1])]
    m = re.search(r'p\.(\d+)(?:\s*~\s*(\d+))?', page)
    if not m:
        return None
    lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
    runs, cur = [], []
    for lab, s in d.segs:
        if lab is not None and lo <= lab <= hi:
            cur.append(s)
        elif cur:
            runs.append(''.join(cur))
            cur = []
    if cur:
        runs.append(''.join(cur))
    return runs or None


def loc_label(d, pos):
    lab = d.label_at(pos)
    if d.kind == 'BR':
        return f'[절 {lab[0]}]' + (f' [표 {lab[1]}]' if lab[1] else '')
    return f'p.{lab}'


def note_has_loc(note, d, pos):
    lab = d.label_at(pos)
    if d.kind == 'BR':
        return f'[절 {lab[0]}]' in note
    if lab is None:
        return False
    for m in re.finditer(r'p\.(\d+)(?:\s*~\s*(\d+))?', note):
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if lo <= lab <= hi:
            return True
    return False


def refs_in(note):
    out = re.findall(r'(?<!\d)(\d{14})(?!\d)', note or '')
    out += re.findall(r'(https?://[^\s」』)\]]+)', note or '')
    return out


# ───────── 대조 ─────────
STATS = dict(in_page=0, note_loc=0, p13=0, pdfpage=0)
SAMPLES = []


def check_text(key, col, val, row_ref, page, note, fails, xml_ok=True):
    if not val or val == NA:
        return
    d = doc(row_ref)
    if d is None:
        fails.append(f'{key}: {col} 출처 글 못 읽음 {row_ref}')
        return
    v = SX(val) if d.kind == 'BR' else S(val)
    reg = region(d, page)
    if reg and any(v in r for r in reg):
        STATS['in_page'] += 1
        return
    # page 밖 → note 에 위치가 있어야 함
    for ref in [row_ref] + refs_in(note):
        dd = doc(ref)
        if dd is None:
            continue
        vv = SX(val) if dd.kind == 'BR' else S(val)
        pos = dd.find_all(vv)
        if pos:
            if any(note_has_loc(note, dd, p) for p in pos):
                STATS['note_loc'] += 1
                return
            fails.append(f'{key}: {col} 이 page 「{page[:50]}」 밖({loc_label(dd, pos[0])})인데 note 에 위치 없음')
            return
    fails.append(f'{key}: {col} 원문 대조 실패 「{val[:50]}…」')


def check_p13(key, col, val, ref, page, fails):
    m = re.search(r'p\.(\d+)(?:~(\d+))?\(본문 PDF, 13차 보관\)', page)
    if not m:
        return
    d = doc(ref)
    p13 = pdf13_br(d.meta['corp']) if d else None
    if p13 is None or p13.meta.get('rcept') != ref:
        fails.append(f'{key}: 13차 PDF 글 없음·rcept 다름')
        return
    lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
    lines = [SX(x) for x in val.split('\n')]
    lines = [x for x in lines if len(x) >= 8]
    found, inr = 0, 0
    for x in lines:
        pos = p13.find_all(x, 5)
        if pos:
            found += 1
            if any(lo <= p13.label_at(p) <= hi for p in pos):
                inr += 1
    STATS['p13'] += 1
    if found == 0:
        fails.append(f'{key}: 13차 PDF 글에서 {col} 의 줄을 하나도 못 찾음')
    elif inr == 0:
        fails.append(f'{key}: 13차 PDF 쪽 {lo}~{hi} 에 {col} 줄 없음')


def check_pdfpage(key, col, val, ref, page, fails, info, tol=0):
    """kit 행: 같은 sha PDF 글에서 실제 쪽을 찾음. page 칸에 「PDF p.」가 있으면 맞는지 봄."""
    d = doc(ref)
    if d is None or d.kind != 'AR_kit':
        return
    pa = pdf_ar_by_sha(d.meta['sha'])
    m = re.search(r'PDF p\.(\d+)(?:~(\d+))?', page)
    if pa is None:
        if m:
            fails.append(f'{key}: page 에 PDF 쪽이 있으나 같은 sha 의 PDF 글이 없음')
        return
    P, src = pa
    v = S(val)
    pos = P.find_all(v, 5)
    pgs = sorted({P.label_at(p) for p in pos})
    if not pos:
        # 쪽 머리글이 끼면 이어서 안 나옴 → 첫 줄로
        first = next((S(x) for x in val.split('\n') if len(S(x)) >= 10), '')
        pos = P.find_all(first, 5) if first else []
        pgs = sorted({P.label_at(p) for p in pos})
    STATS['pdfpage'] += 1
    if m:
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if not pgs or not any(lo - tol <= g <= hi + tol for g in pgs):
            fails.append(f'{key}: page 「PDF p.{lo}~{hi}」인데 PDF 글에서 찾은 쪽 {pgs}')
    else:
        info.append(f'{key}: kit 행 — 같은 sha PDF 글({src}) 실제 쪽 {pgs}, page 칸 「{page}」')


# ───────── 숫자 ─────────
DATE_CELL = re.compile(r"^'?(?:20)?\d{2}\s*[.\-/]\s*\d{1,2}\s*[.\-/]\s*\d{1,2}\.?\s*(?:\([월화수목금토일]\))?$")


def table_dates(txt):
    rows, dates = 0, set()
    for ln in txt.split('\n'):
        if not ln.strip().startswith('|'):
            continue
        cells = [c.replace('<br>', '').strip() for c in ln.strip().strip('|').split('|')]
        for c in cells[:3]:
            if DATE_CELL.match(c):
                rows += 1
                ds = re.findall(r'\d+', c)
                y = ds[0] if len(ds[0]) == 4 else '20' + ds[0]
                dates.add((int(y), int(ds[1]), int(ds[2])))
                break
    return rows, len(dates)


def ar_doc_for(corp, fy):
    y = str(int(fy) + 1)
    for r in ARL:
        if r['회사'] == corp and r['공시연도'] == y and r['공시유형'] == '본공시' and r['파일_url']:
            return doc(r['파일_url'].split(' (')[0])
    for r in KITF:
        if r['지주명'] == corp and r['공시연도'] == y and r['공시유형'] == '본공시' and '지배구조' in r['파일명']:
            return doc(r['url'])
    return None


def br_doc_for(corp, fy):
    for r in BRMETA.values():
        if r['label'] == corp and r['fy'] == str(fy) and r['kind'] == '본':
            return doc(r['rcept_no'])
    return None


def fkw(*texts):
    t = re.sub(r'\s+', '', ' '.join(texts))
    out = []
    for k in KW_F:
        if k in ('AI', 'IT'):
            if re.search(r'(?<![A-Za-z])' + k + r'(?![A-Za-z])', t):
                out.append(k)
        elif k in t:
            out.append(k)
    return ', '.join(out)


GUESS = re.compile(r'추정|아마|듯하|듯이|보인다|보임|짐작|의도|것으로 보|로 보여')


def unquoted(note):
    return re.sub(r'「[^」]*」|『[^』]*』|“[^”]*”', '', note or '')


def main():
    fails, info, lines = [], [], []
    numchk = []
    data = {}
    # (b) 열·BOM·빈칸
    for fn, cols in COLS.items():
        path = os.path.join(FRAG, fn)
        if not os.path.exists(path):
            fails.append(f'{fn}: 파일 없음')
            continue
        if open(path, 'rb').read(3) != b'\xef\xbb\xbf':
            fails.append(f'{fn}: utf-8-sig BOM 없음')
        hdr = next(csv.reader(open(path, encoding='utf-8-sig')))
        if hdr != cols:
            fails.append(f'{fn}: 열 이름·순서 다름 {hdr}')
        data[fn] = rows_of(path)
    for fn, rows in data.items():
        refcol = 'rcept_no' if fn == 'F2_g1.csv' else 'rcept_no_or_url'
        na_rows = sum(1 for r in rows if any(v == NA for v in r.values()))
        lines.append(f'{fn}: 행 {len(rows)}, 「문서에 없음」 칸이 있는 행 {na_rows}')
        for i, r in enumerate(rows, 2):
            key = f"{fn}:{i} {r.get('corp_label')} FY{r.get('fy')} {r.get('body_name') or r.get('committee') or r.get('unit_name') or r.get('item_id')}"
            need = [refcol, 'page'] + (['doc_name', 'collected_at'] if fn != '확인_F_g1.csv' else ['item_text', 'result', 'where', 'note'])
            for c in need:
                if not (r.get(c) or '').strip():
                    fails.append(f'{key}: {c} 비어 있음')
            if fn != '확인_F_g1.csv' and not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00', r.get('collected_at', '')):
                fails.append(f'{key}: collected_at 꼴 「{r.get("collected_at")}」(KST +09:00 아님)')
            d = doc(r[refcol]) if r.get(refcol) else None
            if fn != '확인_F_g1.csv':
                if d is None:
                    fails.append(f'{key}: 출처 글 못 읽음 {r[refcol]}')
                    continue
                if d.meta.get('doc_name') != r['doc_name']:
                    fails.append(f'{key}: doc_name 「{r["doc_name"]}」 ≠ 출처 목록 「{d.meta.get("doc_name")}」')
                if d.meta.get('corp') != r['corp_label']:
                    fails.append(f'{key}: corp 다름 {d.meta.get("corp")}')
                if fn == 'F2_g1.csv' and r['fy'] != d.meta.get('fy'):
                    fails.append(f'{key}: fy {r["fy"]} ≠ 문서 FY{d.meta.get("fy")}')
            if any(v == NA for v in r.values()) and not (r.get('note') or '').strip():
                fails.append(f'{key}: 「문서에 없음」 칸이 있는데 note 비어 있음')
            if any(v == NA for v in r.values()) and '찾은' not in (r.get('note') or '') and '없음' not in (r.get('note') or ''):
                fails.append(f'{key}: 「문서에 없음」 칸이 있는데 note 에 찾은 범위 글 없음')
            # (a) 원문 대조
            for c in TEXT_COLS[fn]:
                v = r.get(c, '')
                if fn == '확인_F_g1.csv' and r.get('result') != '원문 있음':
                    continue
                check_text(key, c, v, r[refcol], r['page'], r.get('note', ''), fails)
            if fn == 'F_g1.csv' and r['source_text'] != NA:
                check_p13(key, 'source_text', r['source_text'], r[refcol], r['page'], fails)
                check_pdfpage(key, 'source_text', r['source_text'], r[refcol], r['page'], fails, info)
            if fn == 'F2_g1.csv' and r['agenda_list_text'] != NA:
                check_p13(key, 'agenda_list_text', r['agenda_list_text'], r[refcol], r['page'], fails)
            if fn == 'F3_g1.csv' and r['unit_name'] != NA:
                tail = r['note'][r['note'].find('headcount'):] if 'headcount' in r['note'] else ''
                phs = re.findall(r'「([^」]+)」', tail)
                probe = r['duty_text'] if r['duty_text'] != NA else (phs[0] if phs else r['unit_name'])
                check_pdfpage(key, 'F3 근거 글', probe, r[refcol], r['page'], fails, info, tol=1)
            if fn == '확인_F_g1.csv' and r.get('result') == '원문 있음' and d is not None and d.kind == 'AR_kit':
                check_pdfpage(key, 'source_excerpt', r['source_excerpt'], r[refcol], r['page'], fails, info)
            if fn == '확인_F_g1.csv' and r.get('result') == '원문 있음':
                if len(re.sub(r'\s+', ' ', r['source_excerpt']).strip()) > 300:
                    fails.append(f'{key}: source_excerpt 300자 넘음')
            # (f) 추정 낱말
            if GUESS.search(unquoted(r.get('note', ''))):
                fails.append(f'{key}: note 에 추정 낱말 「{GUESS.search(unquoted(r["note"])).group(0)}」')
            if '|' in ''.join(r.get(c, '') for c in TEXT_COLS[fn]) and d is not None and d.kind != 'BR':
                fails.append(f'{key}: 연차보고서 출처 칸에 「|」')
            # F 분류·숫자
            if fn == 'F_g1.csv':
                exp = fkw(r['body_name'], r['source_text'] if r['source_text'] != NA else '')
                if r['function_kw'] != exp:
                    fails.append(f'{key}: function_kw 「{r["function_kw"]}」 ≠ 재계산 「{exp}」')
                h = r['held_count']
                if h != NA:
                    m = re.search(r'held_count 원문 「([^」]+)」\((\w+) 칸\)', r['note'])
                    if m:
                        ph, col = m.group(1), m.group(2)
                        ok = S(ph) in S(r.get(col, '')) and re.search(r'\d+', ph) and int(re.search(r'\d+', ph).group(0)) == int(h)
                        numchk.append(f'F {key}: held_count {h} ← 「{ph}」 {"맞음" if ok else "다름"}')
                        if not ok:
                            fails.append(f'{key}: held_count {h} 와 원문 「{ph}」 안 맞음')
                    elif '(판단)' in r['note'] and '셈' in r['note']:
                        mq = re.search(r'「([^」]*개최[^」]*)」에 적힌 개최일 (\d+)개', r['note'])
                        n = len(re.findall(r'\d{1,2}\.\s?\d{1,2}\.', mq.group(1))) if mq else -1
                        ok = mq and n == int(h) == int(mq.group(2)) and S(mq.group(1)) in S(r['agenda_text'])
                        numchk.append(f'F {key}: held_count {h} ← 개최일 셈 {n} {"맞음" if ok else "다름"}')
                        if not ok:
                            fails.append(f'{key}: held_count (판단) 셈 안 맞음')
                    else:
                        fails.append(f'{key}: held_count {h} 근거 note 없음')
            if fn == 'F2_g1.csv':
                a = r['agenda_list_text']
                exp = NA if a == NA else ('Y' if re.search('자회사|그룹|계열사', S(a)) else 'N')
                if r['subsidiary_related'] != exp:
                    fails.append(f'{key}: subsidiary_related 「{r["subsidiary_related"]}」 ≠ 재계산 「{exp}」')
                if a != NA:
                    nrow, ndis = table_dates(a)
                    mt = re.search(r'개최일자가 적힌 행 (\d+)개\(서로 다른 날짜 (\d+)개\)', r['note'])
                    if not mt or (int(mt.group(1)), int(mt.group(2))) != (nrow, ndis):
                        fails.append(f'{key}: 표 개최일자 행 다시 셈 {nrow}·{ndis} ≠ note {mt.group(0) if mt else "없음"}')
                    ma = re.search(r'held_count 는 연차보고서 「([^」]+)」\(p\.(\d+)\) 원문 「([^」]+)」', r['note'])
                    h = int(r['held_count'])
                    if ma:
                        ad = ar_doc_for(r['corp_label'], r['fy'])
                        # (p.N) 은 위원회 절 머리 쪽 — 그 절 안(시작페이지 N~N+20)에서 찾음
                        reg = region(ad, f'p.{ma.group(2)}~{int(ma.group(2)) + 20}') if ad else None
                        ph = ma.group(3)
                        n = int(re.search(r'\d+', ph).group(0))
                        okp = bool(reg) and any(S(ph) in x for x in reg)
                        ok = okp and n == h
                        numchk.append(f'F2 {key}: held_count {h} ← 연차보고서 p.{ma.group(2)} 「{ph}」({"글 있음" if okp else "글 없음"}) · 표 행 {nrow}·날짜 {ndis} {"맞음" if ok else "다름"}')
                        if not ok:
                            fails.append(f'{key}: held_count {h} — 연차보고서 p.{ma.group(2)} 「{ph}」 확인 실패')
                    else:
                        ok = '(판단)' in r['note'] and h == nrow
                        numchk.append(f'F2 {key}: held_count {h} ← (판단) 표 행 {nrow}(날짜 {ndis}) {"맞음" if ok else "다름"}')
                        if not ok:
                            fails.append(f'{key}: held_count {h} 표 행 셈 {nrow} 과 다름 또는 (판단) 표시 없음')
            if fn == 'F3_g1.csv' and r['headcount'] != NA:
                h = int(r['headcount'])
                tail = r['note'][r['note'].find('headcount'):] if 'headcount' in r['note'] else ''
                phs = re.findall(r'「([^」]+)」', tail)
                ph = phs[0] if phs else ''
                dd = doc(r['rcept_no_or_url'])
                okp = bool(phs) and dd is not None and all(S(x) in dd.full for x in phs)
                nums = []
                for x in phs:
                    nums += [int(y) for y in re.findall(r'(\d+)\s*명', x)] or [int(y) for y in re.findall(r'\d+', x)]
                if '더함' in r['note']:
                    nums = [int(y) for y in re.findall(r'(\d+)\s*명', ph)]
                if '더함' in r['note']:
                    okn = sum(nums) == h and '(판단)' in r['note']
                else:
                    okn = h in nums
                numchk.append(f'F3 {key}: headcount {h} ← {" / ".join("「" + x[:50] + "」" for x in phs)} {"맞음" if okp and okn else "다름"}')
                if not (okp and okn):
                    fails.append(f'{key}: headcount {h} 원문 확인 실패 「{ph[:60]}」')
    # (b) 문서목록 꼴
    F, F2, F3 = data.get('F_g1.csv', []), data.get('F2_g1.csv', []), data.get('F3_g1.csv', [])
    dlp = os.path.join(OUT, '문서목록15b_F_g1.csv')
    dl = rows_of(dlp)
    dcols = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at', 'text_path', 'status', 'note']
    if next(csv.reader(open(dlp, encoding='utf-8-sig'))) != dcols or open(dlp, 'rb').read(3) != b'\xef\xbb\xbf':
        fails.append('문서목록15b_F_g1.csv: 열·BOM 다름')
    for x in dl:
        if x['status'] not in ('받음', '014', '없음', '막힘', '실패') or not x['rcept_no_or_url'] or not x['note']:
            fails.append(f'문서목록: {x["corp_label"]} {x["fy_or_date"]} status·출처·note 빈칸')
        if x['status'] == '받음' and not x['fetched_at'] and '받은 시각' not in x['note']:
            fails.append(f'문서목록: {x["corp_label"]} {x["fy_or_date"]} fetched_at 빈칸(사유 없음)')
    for fn, refcol in (('F_g1.csv', 'rcept_no_or_url'), ('F2_g1.csv', 'rcept_no'), ('F3_g1.csv', 'rcept_no_or_url')):
        for r in data.get(fn, []):
            if not any(x['rcept_no_or_url'] == r[refcol] for x in dl):
                fails.append(f'문서목록: {fn} 행 출처 {r[refcol][:50]} 없음')
                break
    # (c) 범위
    for c in G1:
        for fy in ('2023', '2024', '2025'):
            for kind in ('사업보고서', '지배구조 및 보수체계 연차보고서'):
                have = [r for r in F if r['corp_label'] == c and r['fy'] == fy and r['doc_kind'] == kind]
                listed = [x for x in dl if x['corp_label'] == c and x['fy_or_date'] == f'FY{fy}' and x['doc_kind'] == kind]
                if not have and not listed:
                    fails.append(f'F 범위: {c} FY{fy} {kind} — 행도 문서목록 줄도 없음')
                elif not have:
                    info.append(f'F 범위: {c} FY{fy} {kind} — 이 문서에서 나온 행 없음(문서목록 {listed[0]["status"]}: {listed[0]["note"][:60]})')
        for fy in ('2024', '2025'):
            got = [r for r in F2 if r['corp_label'] == c and r['fy'] == fy]
            kinds = {'자회사CEO': r'대표이사후보추천|최고경영자후보추천|임원후보추천', '내부통제': '내부통제', '감사': '^감사위원회$',
                     'ESG': 'ESG|지속가능', '위험': '리스크관리위원회|위험관리위원회'}
            for kname, rx in kinds.items():
                if not any(re.search(rx, r['committee']) for r in got):
                    fails.append(f'F2 범위: {c} FY{fy} {kname} 위원회 행 없음')
        got3 = ' '.join(r['function'] + r['unit_name'] + r['note'] for r in F3 if r['corp_label'] == c)
        for kname, rx in (('준법', '준법'), ('위험', '위험관리|리스크'), ('감사', '감사')):
            if not re.search(rx, got3):
                fails.append(f'F3 범위: {c} {kname} 행 없음')
    # (c) 빠짐 훑기 — 협의회·협의체·회의체
    covered = {c: S(' '.join(r['body_name'] + r['source_text'] + r['note'] + r['agenda_text'] + r['chair_text'] for r in F
                             if r['corp_label'] == c)) for c in G1}
    sweep = {}
    for c in G1:
        for fy in ('2023', '2024', '2025'):
            for d in (br_doc_for(c, fy), ar_doc_for(c, fy)):
                if d is None:
                    continue
                for m in re.finditer(r'(협의회|협의체|회의체)', d.full):
                    pre = d.full[max(0, m.start() - 10):m.start()]
                    nm = re.sub(r'^.*[^가-힣A-Za-z0-9·\-]', '', pre) + m.group(1)
                    tail = nm[-9:]
                    if tail in covered[c] or nm[-7:] in covered[c]:
                        continue
                    sweep.setdefault((c, nm), set()).add(f'{d.kind}{fy}')
    for (c, nm), where in sorted(sweep.items()):
        hit = [e for e in EXCL if (e[0] in ('*', c)) and e[1] in nm]
        if hit:
            continue
        if re.fullmatch(r'.{0,3}(협의회|협의체|회의체)', nm) or re.search(r'(및|과|와|는|은|의|를|을|로|에|각종|별도의|해당|본|동|위한|하는)(협의회|협의체|회의체)$', nm):
            continue  # 앞에 이름 글이 없는 일반 낱말(「협의회는」「본 협의회」)
        fails.append(f'F 빠짐 후보: {c} 「{nm}」({",".join(sorted(where))}) — 행도 EXCL 도 없음')
    # (d) F2 established 반박
    for r in F2:
        if r['established'] != NA:
            continue
        name = S(r['committee'])
        for d in (br_doc_for(r['corp_label'], r['fy']), ar_doc_for(r['corp_label'], r['fy'])):
            if d is None:
                continue
            for p in d.find_all(name, 60):
                ctx = d.full[max(0, p - 60):p + len(name) + 40]
                if re.search(r'(신설|설치)(?!근거|목적|여부|하여야|할수|하고|된위원회)', ctx) and re.search(r'\d{4}', ctx):
                    k = (r['corp_label'], r['fy'], r['committee'])
                    if k not in EST_OK:
                        fails.append(f'F2 established 반박 후보: {k} {d.kind} 「…{ctx[:110]}…」')
                    break
    # (g) 확인 CSV
    req = open(os.path.join(OUT, 'REQUEST15b.md'), encoding='utf-8').read()
    reqline = next((ln.strip().lstrip('*').strip() for ln in req.split('\n') if '함께 볼 것' in ln and '내부통제위원회 첫 개최일' in ln), None)
    chk = data.get('확인_F_g1.csv', [])
    if not reqline:
        fails.append('확인: REQUEST15b 의 「함께 볼 것」 줄을 못 찾음')
    for r in chk:
        if r['item_text'] != reqline:
            fails.append(f'확인 {r["item_id"]}: item_text 가 REQUEST15b 줄 글과 다름')
        if r['result'] not in ('원문 있음', '문서에 없음', '수집 실패'):
            fails.append(f'확인 {r["item_id"]}: result 값 「{r["result"]}」')
    need = {'NH 내부통제위원회 첫 개최일·첫 안건(FY2024)': lambda r: r['corp_label'] == 'NH농협금융지주' and '제1차 내부통제위원회' in r['where'] + r['source_excerpt'],
            'NH 내부통제위원회 설치(신설)': lambda r: r['corp_label'] == 'NH농협금융지주' and '신설' in r['source_excerpt'],
            '신한 자회사경영관리위원회 시점': lambda r: r['corp_label'] == '신한금융지주' and '정기주주총회' in r['source_excerpt'],
            '신한 자회사경영관리위원회 사유': lambda r: r['corp_label'] == '신한금융지주' and '본연의 기능' in r['source_excerpt'],
            '신한 FY2022 자회사경영관리위원회': lambda r: r['corp_label'] == '신한금융지주' and r['fy'] == '2022'}
    for k, f in need.items():
        if not any(f(r) for r in chk):
            fails.append(f'확인: 「{k}」 행 없음')
    for r in chk:
        if GUESS.search(unquoted(r['note'])) or re.search(r'(?<![가-힣])뒤(?![가-힣])', unquoted(r['note'])):
            fails.append(f'확인 {r["item_id"]}: note 에 추정·선후 해석 낱말')
    # (h) 비밀·git
    key = os.environ.get('DART_API_KEY', '')
    outs = [os.path.join(FRAG, f) for f in COLS] + glob.glob(os.path.join(OUT, '원문', 'F*', '*.md')) + \
        [os.path.join(OUT, '문서목록15b_F_g1.csv'), os.path.join(ROOT, 'scripts', 'dart', 'ops15b_F_g1.py'), os.path.abspath(__file__)]
    nsec = 0
    for p in outs:
        if not os.path.exists(p):
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        nsec += 1
        if (key and len(key) > 8 and key in t) or ('crtfc' + '_key=') in t or re.search(r'(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])', t):
            fails.append(f'{os.path.relpath(p, ROOT)}: 비밀 값 꼴 있음')
    tracked = subprocess.run(['git', '-C', ROOT, 'ls-files'], capture_output=True, text=True).stdout.split('\n')
    bad = [t for t in tracked if t.startswith(('dart_out/raw/', 'dart_out/text/', 'dart_out/ops15/조직도/')) or
           (t.lower().endswith('.pdf') and not t.startswith('handoff/'))]
    if bad:
        fails.append(f'git 추적 경로에 원본·PDF {len(bad)}개 (예 {bad[0]})')
    for p in (os.path.join(FRAG, 'F_g1.csv'), os.path.join(OUT, '원문', 'F'), os.path.join(OUT, '문서목록15b_F_g1.csv')):
        ig = subprocess.run(['git', '-C', ROOT, 'check-ignore', '-q', p]).returncode == 0
        if ig:
            fails.append(f'{os.path.relpath(p, ROOT)}: 산출물이 git 무시 경로')
    # 원문 md: 행마다 회사·FY·문서 md 가 있고 source_text 가 그 안에 있음
    for fn, sub, col in (('F_g1.csv', 'F', 'source_text'), ('F2_g1.csv', 'F2', 'agenda_list_text'), ('F3_g1.csv', 'F3', 'unit_name')):
        for i, r in enumerate(data.get(fn, []), 2):
            if r.get(col, NA) == NA:
                continue
            ref = r.get('rcept_no_or_url') or r.get('rcept_no')
            d = doc(ref)
            fy = d.meta['fy'] if d else r['fy']
            pat = os.path.join(OUT, '원문', sub, f"{r['corp_label']}__FY{fy}__*.md")
            mds = glob.glob(pat)
            v = SX(r[col]) if d and d.kind == 'BR' else S(r[col])
            if not any(v in (SX(open(m, encoding='utf-8').read()) if d and d.kind == 'BR' else S(open(m, encoding='utf-8').read())) for m in mds):
                fails.append(f'{fn}:{i} 원문 md 에 {col} 글 없음({os.path.relpath(pat, ROOT)})')
    lines.append(f"대조: page 안 {STATS['in_page']}칸, page 밖·note 위치 {STATS['note_loc']}칸, 13차 PDF 쪽 대조 {STATS['p13']}행, kit 행 PDF 쪽 찾음 {STATS['pdfpage']}칸")
    lines.append(f'숫자 대조 {len(numchk)}건, 빠짐 훑기 후보(덮인 것 뺀) {len(sweep)}개 중 EXCL·일반 낱말로 뺀 것 외 FAIL, 비밀 점검 파일 {nsec}개')
    lines.append(f'실패 {len(fails)}건')
    txt = '\n'.join(lines + ['FAIL ' + f for f in fails] + ['', '# 숫자 대조'] + numchk + ['', '# 참고(실패 아님)'] + info) + '\n'
    open(os.path.join(OUT, 'verify15b_F_g1.txt'), 'w', encoding='utf-8').write(txt)
    print('\n'.join(lines))
    for f in fails[:60]:
        print('FAIL', f[:300])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
