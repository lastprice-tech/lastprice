"""15차 확장 작업 I — 경영승계·겸직 결정 이유와 자회사 CEO 평가 (원문_지주경영승계 조각).

정본: dart_out/ops15/REQUEST15b.md(작업 I), 규칙: COMMON15.md·COMMON15b.md.
산출(이 스크립트 소유):
  dart_out/ops15/조각/I.csv          — corp_label, fy_or_date, topic, source_text, doc_kind, rcept_no_or_url, page, note, doc_name, collected_at
  dart_out/ops15/조각/확인_I.csv      — 사건·연도마다 1행(원문 있음/문서에 없음/수집 실패)
  dart_out/ops15/원문/I/*.md         — 행이 나온 쪽(PDF)·절(XML)·섹션(6차) 글 전체
  dart_out/ops15/문서목록15b_I.csv   — 쓴 문서 목록
  dart_out/text/ops15b/주요경영사항__*.md — OpenDART XML → md(ops15_prep.xml_to_md)

하위 명령: `python3 scripts/dart/ops15b_I.py fetch-list` / `fetch-doc <rcept>...`(OpenDART, 키는 환경변수 DART_API_KEY 만)
          `python3 scripts/dart/ops15b_I.py build`(기본) — 네트워크 없이 표·md 를 만듦.

원문 옮기기(엄격): 각 행은 SPEC 의 (시작 글, 끝 글)로 출처 텍스트에서 한 곳의 이어진 글을 잘라 옮김.
  비교는 공백·줄바꿈을 지운 글끼리. PDF 쪽 md 의 「## p.N」 줄(우리가 넣은 쪽 표지)은 출처에서 빼고 봄.
  OpenDART XML md 는 md 표지 「|」「<br>」도 양쪽에서 빼고 봄. 옮긴 글은 공백 덩어리를 한 칸으로 바꾼 것 말고는 그대로.
  쪽을 넘는 글은 그 사이 쪽 머리글·쪽 번호 글자도 그대로 들어감(note 에 표시).
topic 기준(기계적): 옮긴 글에 「분리」가 있으면 「분리」, 「겸직」「겸임」「兼」이 있으면 「겸직 결정」(둘 다면 「분리」);
  자회사 CEO 후보 관리·경영성과 평가 행은 「자회사 CEO 평가」. 원문 낱말이 결정 이유를 직접 말하지 않는 행(겸임 기간·후보 추천 사실 문장)은
  note 앞에 「(판단)」과 그 까닭을 적음. 이유·의도 추정은 하지 않음.
"""
import csv, glob, io, json, os, re, sys, zipfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'dart'))
csv.field_size_limit(10 ** 9)
KST = timezone(timedelta(hours=9))
J = lambda *p: os.path.join(ROOT, *p)
OUT_CSV = J('dart_out/ops15/조각/I.csv')
OUT_CHK = J('dart_out/ops15/조각/확인_I.csv')
OUT_DOCS = J('dart_out/ops15/문서목록15b_I.csv')
OUT_MD_DIR = J('dart_out/ops15/원문/I')
TXT_DIR = J('dart_out/text/ops15b')
COLS = ['corp_label', 'fy_or_date', 'topic', 'source_text', 'doc_kind', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at']
CHK_COLS = ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note']
DOC_COLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at', 'text_path', 'status', 'note']
GOV = '지배구조 및 보수체계 연차보고서'
MAIN_DISC = '자회사의 주요경영사항 등 공시(OpenDART)'


def to_kst(s):
    """'2026-09-22T02:45:52+0000' 같은 시각을 KST(+09:00) ISO 로."""
    if not s:
        return ''
    s2 = re.sub(r'([+-]\d\d)(\d\d)$', r'\1:\2', s.strip())
    try:
        d = datetime.fromisoformat(s2)
    except ValueError:
        return s
    if d.tzinfo is None:
        d = d.replace(tzinfo=KST)
    return d.astimezone(KST).isoformat(timespec='seconds')


def rcsv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


# ── 출처 메타 ──────────────────────────────────────────────────────────────
GOV_OLD = rcsv(J('dart_out/ops15/문서목록15b_gov_old.csv'))
OPS15_GOV = rcsv(J('dart_out/ops15/연차보고서15_목록_g1.csv')) + rcsv(J('dart_out/ops15/연차보고서15_목록_g2.csv'))
HANDOFF_GOV = rcsv(J('handoff/연차보고서_파일목록.csv'))


def src_gov_old(label, text_name):
    tp = f'dart_out/text/ops15b/{text_name}'
    for x in GOV_OLD:
        if x['corp_label'] == label and x['text_path'] == tp:
            return dict(kind='pdf', path=J(tp), rel=tp, doc_kind=GOV, doc_name=x['report_nm'], url=x['rcept_no_or_url'],
                        rcept_dt=x['rcept_dt'], collected_at=to_kst(x['fetched_at']), sha256=x['sha256'], raw_path=x['raw_path'],
                        corp=label, fy=x['fy_or_date'],
                        note_src=f'gov_old 가 다시 받은 PDF 의 쪽 텍스트({tp}, 「## p.N」= PDF 쪽)')
    raise KeyError((label, text_name))


def src_ops15(label, year, typ):
    tp = f'dart_out/text/ops15/연차보고서__{label}__{year}__{typ}.md'
    for x in OPS15_GOV:
        if x['회사'] == label and x['공시연도'] == year and x['공시유형'] == typ:
            return dict(kind='pdf', path=J(tp), rel=tp, doc_kind=GOV, doc_name=x['제목'], url=x['파일_url'], rcept_dt=x['공시일'],
                        collected_at=to_kst(x['fetched_at']), sha256=x['sha256'], raw_path=f'dart_out/raw/governance15/{label}/',
                        corp=label, fy='FY%d' % (int(year) - 1),
                        note_src=f'15차 연차보고서 쪽 텍스트({tp}, 「## p.N」= PDF 쪽)')
    raise KeyError((label, year, typ))


def src_kit56(label, year, typ):
    for x in HANDOFF_GOV:
        if x['지주명'] == label and x['공시연도'] == year and x['공시유형'] == typ and '통합' in x['구분']:
            return dict(kind='kit56', key=(label, year, typ), rel='dart_out/ops15/kit56/연차보고서_섹션.csv', doc_kind=GOV,
                        doc_name=x['제목'], url=x['url'], rcept_dt='', collected_at=to_kst(x['fetched_at']), sha256=x['sha256'],
                        raw_path='(PDF 원본은 이번 컨테이너에 없음)', corp=label, fy='FY%d' % (int(year) - 1),
                        note_src='6차 섹션 글(PDF 원본은 이번 컨테이너에 없음; gov_old 다시 받기 「막힘」)')
    raise KeyError((label, year, typ))


def src_xml(label, rcept, date, report_nm):
    meta = json.load(open(J(f'dart_out/raw/document/{rcept}.zip.meta.json'), encoding='utf-8'))
    tp = f'dart_out/text/ops15b/주요경영사항__{label}__{date}__{rcept}.md'
    return dict(kind='xml', rcept=rcept, path=J(tp), rel=tp, doc_kind=MAIN_DISC, doc_name=report_nm, url=rcept, rcept_dt=date,
                collected_at=to_kst(meta.get('fetched_at', '')), sha256=meta.get('raw_sha256', meta.get('sha256', '')),
                raw_path=f'dart_out/raw/document/{rcept}.zip', corp=label, fy=date, note_src='OpenDART document.xml → md(ops15_prep.xml_to_md)')


SRC = {
    'KB17': lambda: src_gov_old('KB금융지주', '연차보고서__KB금융지주__FY2017.md'),
    'W19': lambda: src_ops15('우리금융지주', '2020', '본공시'),
    'W20': lambda: src_ops15('우리금융지주', '2021', '본공시'),
    'D18': lambda: src_gov_old('iM금융지주', '연차보고서__iM금융지주__FY2018.md'),
    'D19': lambda: src_ops15('iM금융지주', '2020', '본공시'),
    'D20': lambda: src_ops15('iM금융지주', '2021', '본공시'),
    'B17': lambda: src_gov_old('BNK금융지주', '연차보고서__BNK금융지주__FY2017.md'),
    'iM24': lambda: src_gov_old('iM금융지주', '연차보고서__iM금융지주__FY2024.md'),
    'iM25': lambda: src_gov_old('iM금융지주', '연차보고서__iM금융지주__FY2025.md'),
    'iM25A': lambda: src_gov_old('iM금융지주', '연차보고서__iM금융지주__FY2025__추가공시.md'),
    'KB25': lambda: src_gov_old('KB금융지주', '연차보고서__KB금융지주__FY2025.md'),
    'KB25A': lambda: src_gov_old('KB금융지주', '연차보고서__KB금융지주__FY2025__추가공시.md'),
    'JB25C': lambda: src_gov_old('JB금융지주', '연차보고서__JB금융지주__FY2025__정정공시.md'),
    'SH25': lambda: src_gov_old('신한금융지주', '연차보고서__신한금융지주__FY2025.md'),
    'HN25': lambda: src_gov_old('하나금융지주', '연차보고서__하나금융지주__FY2025.md'),
    'WR25': lambda: src_gov_old('우리금융지주', '연차보고서__우리금융지주__FY2025.md'),
    'BNK25': lambda: src_gov_old('BNK금융지주', '연차보고서__BNK금융지주__FY2025.md'),
    'JB25': lambda: src_gov_old('JB금융지주', '연차보고서__JB금융지주__FY2025.md'),
    'NH25': lambda: src_kit56('NH농협금융지주', '2026', '본공시'),
    # 찾기만 한 문서(검증 15b_I 에서 범위 보충 — 같은 검색어로 찾았고 행은 없음)
    'KB17A': lambda: src_gov_old('KB금융지주', '연차보고서__KB금융지주__FY2017__추가공시.md'),
    'W19A': lambda: src_ops15('우리금융지주', '2020', '추가공시'),
    'SH25A': lambda: src_gov_old('신한금융지주', '연차보고서__신한금융지주__FY2025__추가공시.md'),
    'HN25A': lambda: src_gov_old('하나금융지주', '연차보고서__하나금융지주__FY2025__추가공시.md'),
    'WR25A': lambda: src_gov_old('우리금융지주', '연차보고서__우리금융지주__FY2025__추가공시.md'),
    'NH25A': lambda: src_kit56('NH농협금융지주', '2026', '추가공시'),
    'X_BNK170927': lambda: src_xml('BNK금융지주', '20170927800281', '2017-09-27', '대표이사(대표집행임원)변경(안내공시)'),
    'X_iM240328': lambda: src_xml('iM금융지주', '20240328803378', '2024-03-28', '대표이사(대표집행임원)변경(안내공시)'),
}
SEARCH_ONLY = {'KB17A', 'W19A', 'SH25A', 'HN25A', 'WR25A', 'NH25A', 'JB25', 'iM25A'}  # 행 없이 찾기만 한 글
_SRC_CACHE = {}


def source(key):
    if key not in _SRC_CACHE:
        _SRC_CACHE[key] = SRC[key]()
    return _SRC_CACHE[key]


# ── 출처 글 읽기(대조용 글과 쪽 위치) ─────────────────────────────────────
_TXT_CACHE = {}
PAGE_RE = re.compile(r'^## p\.(\d+)\b.*$', re.M)


def ensure_xml_md(s):
    if os.path.exists(s['path']):
        return
    from ops15_prep import xml_to_md
    z = open(J(s['raw_path']), 'rb').read()
    md, member, enc = xml_to_md(z, s['rcept'])
    os.makedirs(TXT_DIR, exist_ok=True)
    with open(s['path'], 'w', encoding='utf-8') as f:
        f.write(f'<!-- {s["rcept"]} 멤버 {member} 글자 {enc} -->\n' + md)


def load_text(key):
    """(clean, segs) — clean: 대조용 글(쪽 표지 줄 뺌), segs: [(clean 안 시작 위치, 쪽/절 이름, 그 쪽 원문)]."""
    if key in _TXT_CACHE:
        return _TXT_CACHE[key]
    s = source(key)
    segs, buf, pos = [], [], 0
    if s['kind'] == 'pdf':
        raw = open(s['path'], encoding='utf-8').read()
        parts = PAGE_RE.split(raw)
        for i in range(1, len(parts), 2):
            body = parts[i + 1]
            segs.append((pos, f'p.{parts[i]}', body))
            buf.append(body)
            pos += len(body)
    elif s['kind'] == 'kit56':
        rows = [x for x in rcsv(J('dart_out/ops15/kit56/연차보고서_섹션.csv'))
                if (x['지주명'], x['공시연도'], x['공시유형']) == s['key']]
        rows.sort(key=lambda x: (int(x['섹션순번']), int(x['chunk_seq'])))
        for x in rows:
            body = x['본문'] + '\n'
            segs.append((pos, f"p.{x['시작페이지']}(6차 섹션 {x['섹션순번']} 「{x['섹션제목_원문'].strip()}」 시작페이지)", body))
            buf.append(body)
            pos += len(body)
    elif s['kind'] == 'xml':
        ensure_xml_md(s)
        raw = open(s['path'], encoding='utf-8').read()
        k = raw.find('### [절 1]')
        segs.append((0, 'XML [절 1]', raw[k:]))
        buf.append(raw[k:])
    clean = ''.join(buf)
    _TXT_CACHE[key] = (clean, segs)
    return clean, segs


CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')  # 보이지 않는 제어문자(지우면 note 「제어문자 지움」)


def norm(t, xml=False):
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return re.sub(r'\s+', '', CTRL_RE.sub('', t))


def strip_map(clean, xml=False):
    """공백(과 XML 표지)을 뺀 글과, 그 글자 → clean 위치 표."""
    out, idx = [], []
    i, n = 0, len(clean)
    while i < n:
        if xml and clean.startswith('<br>', i):
            i += 4
            continue
        c = clean[i]
        if c.isspace() or (xml and c == '|') or CTRL_RE.match(c):
            i += 1
            continue
        out.append(c)
        idx.append(i)
        i += 1
    return ''.join(out), idx


_SM_CACHE = {}


def cut(key, start, end, after=None, first=False):
    """출처에서 start…end(공백 무시) 이어진 글을 잘라 (source_text, page, seg_names) 로."""
    s = source(key)
    xml = s['kind'] == 'xml'
    clean, segs = load_text(key)
    if key not in _SM_CACHE:
        _SM_CACHE[key] = strip_map(clean, xml)
    st, idx = _SM_CACHE[key]
    a0 = 0
    if after:
        a0 = st.find(norm(after, xml))
        if a0 < 0:
            raise ValueError(f'{key}: after 못 찾음 {after[:30]}')
    ns, ne = norm(start, xml), norm(end, xml)
    a = st.find(ns, a0)
    if a < 0:
        raise ValueError(f'{key}: 시작 못 찾음 {start[:40]}')
    if st.find(ns, a + 1) >= 0 and not after and not first:
        raise ValueError(f'{key}: 시작 글이 두 곳 이상 — after 필요 {start[:40]}')
    b = st.find(ne, a)
    if b < 0 or b - a > 6000:
        raise ValueError(f'{key}: 끝 못 찾음/너무 멂 {end[:40]}')
    b_end = b + len(ne)
    ca, cb = idx[a], idx[b_end - 1] + 1
    text = clean[ca:cb]
    ctrl = bool(CTRL_RE.search(text))
    text = CTRL_RE.sub('', text)
    if xml:
        text = text.replace('<br>', ' ')
        text = re.sub(r'\s*\|\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    names = [nm for (p0, nm, body) in segs if p0 < cb and p0 + len(body) > ca]
    return text, names, ctrl


def na_page(key):
    """「문서에 없음」 행 page — 찾은 범위(그 문서 전체 쪽·섹션)."""
    s = source(key)
    clean, segs = load_text(key)
    if s['kind'] == 'kit56':
        pg = sorted({int(re.match(r'p\.(\d+)', nm).group(1)) for _, nm, _ in segs})
        return f'p.{pg[0]}~p.{pg[-1]} 6차 섹션 전체 {len(segs)}조각(찾은 범위, 섹션 시작페이지 — 해당 글 없음)'
    return f'{segs[0][1]}~{segs[-1][1]} 전체(찾은 범위, PDF 쪽 — 해당 글 없음)'


def page_label(key, names, extra=''):
    s = source(key)
    if s['kind'] == 'xml':
        return names[0] + (' ' + extra if extra else '')
    if s['kind'] == 'kit56':
        return names[0] + (f' ~ {names[-1]}' if len(names) > 1 else '')
    if len(names) == 1:
        return names[0] + '(PDF 쪽)'
    return f'{names[0]}~{names[-1][2:]}(PDF 쪽, 쪽 넘김)'


# ── 행 정의 ────────────────────────────────────────────────────────────────
# S: 원문 행 / NA: 「문서에 없음」 행.  topic=None 이면 옮긴 글 낱말로 기계적으로 정함.
SPECS = []


def S(rid, key, start, end, topic=None, note='', after=None, fy=None, extra_page='', first=False):
    SPECS.append(dict(rid=rid, kind='S', key=key, start=start, end=end, topic=topic, note=note, after=after, fy=fy, extra_page=extra_page, first=first))


def NA(rid, key, topic, note, fy=None):
    SPECS.append(dict(rid=rid, kind='NA', key=key, topic=topic, note=note, fy=fy))


SEARCH_REASON = ('찾은 범위: 보고서 본문 전체(쪽 텍스트), 검색어 「겸직」「겸임」「兼」「분리」「은행장」「행장」「회장과」 '
                 '및 「최고경영자 후보추천 및 경영승계 내역」·후보추천위원회 활동 절')
# (1) 회장·은행장 겸직·분리 이유 — 연차보고서
NA('I1-KB17-na', 'KB17', '분리', '회장·은행장 분리를 정한 이유 문단 문서에 없음. ' + SEARCH_REASON +
   '. 「분리」 3곳은 지배구조위원회를 「회장후보추천위원회」·「계열사대표이사후보추천위원회」로 분리(예정, p.16·p.38)와 사외이사 후보 추천 주체 분리(p.48)뿐')
S('I1-KB17-a', 'KB17', '2017 년 제1 차 ‘상시 지배구조위원회’는 KB 캐피탈의 대표이사', 'KB 데이타시스템 대표이사 후보를 결의하였습니다.',
  topic='분리', note='(판단) 원문에 「분리」·이유 낱말 없음 — 제6차 상시 지배구조위원회가 「KB 국민은행장 후보」를 결의한 사실 문장(지배구조위원회 활동내역 개요(상시))')
S('I1-KB17-b', 'KB17', '(아) 대표이사 회장 윤종규 - 직위', 'KB 금융지주 회장 겸 국민은행 은행장', topic='겸직 결정',
  note='(판단) 원문 「겸」(경력 줄) — 결정 이유 아님, 대표이사 회장 경력 기재(임기 2014. 11. 21 ~ 2020. 11. 20)')
# 검증 15b_I 에서 보충(키워드 「은행장」 grep 으로 찾은 자리)
S('I1-KB17-c', 'KB17', '(자) 비상임이사 허인 - 직위', 'KB 국민은행 경영기획그룹대표 * KB 국민은행 여신심사본보장', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 비상임이사 허인(임기 2017. 11. 20 ~)의 경력 첫 줄 「KB 국민은행 은행장」(이사회 구성원 소개). '
       '쪽 넘김(p.26→p.27) 사이 쪽 번호·머리글 글자 포함, 「본보장」은 원문 글자 그대로')
S('I1-KB17-d', 'KB17', '<KB 금융지주 그룹경영관리위원회 구성> (2017.12.31 기준)', 'KB 국민은행장 17.11.21 19.11.20', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 그룹경영관리위원회 구성 표에서 대표이사 회장(윤종규, 선임일 17.11.21·임기만료일 20.11.20)과 '
       'KB 국민은행장(허 인, 선임일 17.11.21·임기만료일 19.11.20)이 다른 사람으로 적힌 두 행')
NA('I1-W19-na', 'W19', '겸직 결정', '회장·은행장 겸직(또는 분리)을 정한 이유 문단 문서에 없음. ' + SEARCH_REASON +
   '. 「겸직」 문단은 임원 겸직 비용분담·보상기준·지주-계열사 임원 겸직(사외이사 활동 서술 중 1차 임시이사회 2019.1.11, p.37) 관련뿐이고 회장·은행장 겸직 이유는 없음')
S('I1-W19-a', 'W19', '손태승 이사는 대표이사로서 임기는 1년', '부문장<2017>을 역임하였습니다.', topic='겸직 결정',
  note='(판단) 원문 「회장 겸 우리은행 은행장」 — 결정 이유 아님, 재직 사실 문장. 쪽 넘김(p.13→p.14) 사이 쪽 번호 「- 11 -」 글자 포함. '
       '같은 사실이 p.14 이사 현황 표 「19~ 우리금융그룹 회장 兼 우리은행 은행장(現)」에도 있음')
S('I1-W19-b', 'W19', '(1) 대표이사 후보 (손태승)', '2019년 ~ 현재 우리금융지주 대표이사 (우리금융그룹 회장)', topic='겸직 결정',
  note='(판단) 원문에 「겸」 낱말 없음 — 임원후보 추천 관련사항의 대표이사 후보 경력 줄(「2017년 ~ 현재 우리은행 은행장」과 「2019년 ~ 현재 우리금융지주 대표이사」가 함께 적힘)')
NA('I1-D18-na', 'D18', '겸직 결정', '회장·은행장 겸직(2019.1.29 시작)을 정한 이유 문단 문서에 없음. ' + SEARCH_REASON +
   '. 김태오 회장의 대구은행장 겸임 기재도 이 보고서(2019.3.7 게시)에는 없음')
S('I1-D18-a', 'D18', '상임이사로 이사회 의장(~2018.02.13일)', '대경TMS 대표이사를 역임하였습니다.', topic='겸직 결정',
  note='(판단) 원문 「회장 겸 대구은행 은행장」 — 전임 회장 박인규의 사임 당시 겸직 사실 문장(이유 아님). 같은 사람 경력이 p.18 요약 표 「前 DGB금융지주 회장 겸 대구은행장」에도 있음')
S('I1-D18-b', 'D18', '<DGB금융지주 그룹경영관리협의회 구성> (2018년 12월말 기준)', '대구은행장 직무대행 2016.12.27 2019.12.26', topic='겸직 결정',
  note='(판단) 원문에 「겸직」 낱말 없음 — 2018년 12월말 기준 그룹경영관리협의회 구성 표: 회장 김태오(2018.05.31~2021.03.31)와 '
       '「대구은행장 직무대행」 김윤국(2016.12.27~2019.12.26) 두 행. 이 보고서에 2019.1.29 겸임 시작 기재는 없음')
NA('I1-D19-na', 'D19', '겸직 결정', '회장·은행장 겸직이나 분리를 정한 이유 문단 문서에 없음. ' + SEARCH_REASON)
S('I1-D19-a', 'D19', '상임이사로 위험관리위원회 위원, 그룹임원후보추천위원회 위원을 맡고', '2019년 01월 29일부터 대구은행장을 겸임하고 있습니다.',
  topic='겸직 결정', note='(판단) 원문 「겸임」 — 겸임 시작일 문장(결정 이유 아님)')
S('I1-D19-b', 'D19', '2019년 12월 23일 제7차 그룹임원후보추천위원회에서는 대구은행 최고경영자',
  'DGB신용정보(박대면)의 대표이사 후보를 추천하였습니다.', topic='분리',
  note='(판단) 원문에 「분리」·이유 낱말 없음 — 대구은행 최고경영자 임기만료(2020.12.31일) 예정에 따른 경영승계 절차 개시·최종후보군 선정 사실 문장(그룹임원후보추천위원회 활동내역 개요)')
NA('I1-D20-na', 'D20', '분리', '회장·은행장 분리(2020.9 대구은행장 선임)를 정한 이유 문단 문서에 없음. ' + SEARCH_REASON)
S('I1-D20-a', 'D20', '상임이사로 그룹임원후보추천위원회 위원을 맡고 있으며 임기는 2018년 5월 31일', '2020년 9월 28일까지 대구은행장을 겸임하였습니다.',
  topic='겸직 결정', note='(판단) 원문 「겸임」 — 겸임 시작·종료일 문장(결정 이유 아님). iM FY2024 연차보고서 p.17 은 종료일을 「2020년 9월 30일」로 적음(I1-iM24-b 행)')
S('I1-D20-b', 'D20', '2020년 9월 제5차 그룹임원후보추천위원회에서는', '임성훈 후보자를 대구은행 대표이사 최종후보자로 추천하였습니다.',
  topic='분리', note='(판단) 원문에 「분리」·이유 낱말 없음 — 대구은행 대표이사 최종후보자 추천 사실 문장. 원문은 최종후보군 결의를 「2019년 11월 개최된」으로 적고, FY2019 보고서(I1-D19-b)는 2019년 12월 27일 제8차로 적음. 쪽 넘김 사이 쪽 번호 글자 포함')
S('I1-D20-c', 'D20', '2018.05 現 DGB금융지주 대표이사 회장', '대구은행 은행장(2020.09월까지 겸임)', topic='겸직 결정',
  note='(판단) 원문 「겸임」 — 회장 후보(김태오) 경력 표의 마지막 두 줄(대표이사 회장 2018.05~, 대구은행 은행장 2019.01~2020.09)')
S('I1-D20-d', 'D20', '<DGB금융지주 그룹경영관리협의회 구성> (2020년 12월말 기준)', '대구은행장 2020.09.29 2022.12.31', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 2020년 12월말 기준 그룹경영관리협의회 구성 표: 회장 김태오(2018.05.31~2021.03.31)와 '
       '대구은행장 임성훈(선임일 2020.09.29·임기만료일 2022.12.31) 두 행')
NA('I1-B17-na', 'B17', '분리', '회장·은행장 분리를 정한 이유 문단 문서에 없음. ' + SEARCH_REASON +
   '. 「분리 여부」는 제12차 임시이사회(2017.7.13) 「보류」 기재만 있음(I1-B17-a·c 행)')
S('I1-B17-a', 'B17', '제12차 이사회는 전체 이사 7명 중 6명이 참석하여 성원이 되었으며', '은행장 분리 여부에 관한 논의는 보류 결정되었습니다.',
  note='원문 낱말 「분리」 — 이사회 활동내역(2017년도 제12차 임시이사회 2017.7.13) 설명 문단. 분리 결정 이유는 없음')
S('I1-B17-c', 'B17', '1)지주 회장 및 부산은행장 분리 여부 결정 : 보류', '최고경영자 경영승계 절차 진행 여부 : 진행',
  note='원문 낱말 「분리」 — 사외이사 활동 절의 제12차 임시이사회(2017.7.13) 표 아래 주석')
S('I1-B17-b', 'B17', '성세환 이사는 사내이사(회장)로 당사 재임기간은', '2017.9.12)을 겸임하였습니다.',
  note='(판단) 원문 「겸임」 — 전 회장의 부산은행 은행장 겸임 기간 문장(결정 이유 아님)')
S('I1-B17-d', 'B17', '2017년도 제18차 임시이사회 : 2017. 9. 8(금) 14:40 ~ 15:00', '후보 추천 사전협의 특이의견 없음 접수', topic='분리', first=True,
  note='(판단) 원문에 「분리」 낱말 없음 — 이사회 개최내역 제18차 임시이사회(2017.9.8) 표: 심의안건 「부산은행 사내이사 은행장 후보 추천 사전협의」. '
       '같은 표가 사외이사 활동 절(p.89)에도 있음(첫 번째 나온 곳을 씀)')
S('I1-B17-e', 'B17', '2017년도 제19차 임시이사회 : 2017. 9. 11(월) 15:00 ~ 15:30', '후보 확정 사전협의 특이의견 없음 접수', topic='분리', first=True,
  note='(판단) 원문에 「분리」 낱말 없음 — 이사회 개최내역 제19차 임시이사회(2017.9.11) 표: 심의안건 「부산은행 사내이사 은행장 후보 확정 사전협의」. '
       '같은 표가 사외이사 활동 절(p.90)에도 있음(첫 번째 나온 곳을 씀)')
S('I1-B17-f', 'B17', '<BNK금융지주 그룹경영관리협의회 구성(당연직 위원)>', '빈대인 부산은행 은행장 2017.09.12 2020.03월 위원', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 그룹경영관리협의회 구성 표: 회장 김지완(선임일 2017.09.27·임기만료일 2020.03월)과 '
       '부산은행 은행장 빈대인(선임일 2017.09.12·임기만료일 2020.03월) 두 행')
S('I1-B17-g', 'B17', '※성세환 의장의 유고상황에 따라', '부산은행장 직무대행 참석', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 2017년 제2차 그룹경영관리협의회(2017.4.19) 표 아래 주석(회장 직무대행·부산은행장 직무대행 참석)')

# (3) 자회사의 주요경영사항 공시(은행장 선임)·지주 대표이사 변경 — OpenDART
S('I3-BNK170927', 'X_BNK170927', '1. 변경 전ㆍ후 대표이사(대표집행임원)', '-상기 변경일자는 이사회 결의일임', topic='분리',
  note='(판단) 원문에 「분리」 낱말 없음 — 지주 자신의 대표이사 변경 공시(같은 달 자회사 은행장 공시는 목록에 없음). 변경전 성세환은 FY2017 연차보고서에 부산은행 은행장(2012.3.22~2017.9.12) 겸임으로 기재(I1-B17-b)',
  extra_page='[표 1]')
S('I3-iM240328-a', 'X_iM240328', '1. 변경 전ㆍ후 대표이사(대표집행임원)', "상기 '변경일자'는 이사회 결의일임", topic='겸직 결정',
  note='(판단) 원문에 「겸직」 낱말 없음 — 지주 자신의 대표이사 변경 공시. 변경후 대표이사 약력에 「現)대구은행장」(I3-iM240328-b)', extra_page='[표 1]')
S('I3-iM240328-b', 'X_iM240328', '황병우 - - 대구은행 기업경영컨설팅센터장', '現)대구은행장', topic='겸직 결정',
  note='(판단) 원문 「現)대구은행장」 — 변경 후 대표이사 약력 표(겸직 기재로 봄)', extra_page='[표 2]')
# (3) 보충 — 같은 사건의 겸임 기간을 적은 연차보고서 문장(주요경영사항 공시가 목록에 없어서)
S('I3-W20-a', 'W20', '20~ 우리금융그룹 회장', '17~19 우리은행 은행장', topic='겸직 결정', fy='FY2020',
  note='(판단) 원문 「兼」 — 이사 현황 표의 손태승 경력 칸(19~20 회장 兼 은행장). 2020.3 자회사 은행장 공시가 목록에 없어 연차보고서로 보충')
S('I3-W20-b', 'W20', '제2차 자회사대표이사후보추천위원회는 우리은행 은행장 후보추천을 위한', '은행장 최종 후보로 권광석 후보를 추천하는 것으로 결의하였습니다.',
  topic='분리', fy='FY2020',
  note='(판단) 원문에 「분리」 낱말 없음 — 우리은행 은행장 후보 추천 사실 문장(자회사대표이사후보추천위원회 활동내역 개요, 2020년). 2020.3 자회사 은행장 공시가 목록에 없어 연차보고서로 보충')
S('I3-iM24-a', 'iM24', '상임이사로 그룹임원후보추천위원회 위원, ESG위원회 위원을 맡고 있습니다.', '현재까지 아이엠뱅크 은행장을 겸임하고 있습니다.',
  topic='겸직 결정', fy='FY2024',
  note='(판단) 원문 「겸임」 — 황병우 회장(2024.3.28 대표이사 회장 최초 선임)의 은행장 겸임 시작일 문장. 2024.3 자회사 은행장 공시가 목록에 없어 연차보고서로 보충')
S('I3-iM24-b', 'iM24', '2018년 5월 31일 대표이사 회장으로 최초 선임되어 2021년 정기주주총회에서 상임이사로 재선임되었으며',
  '2024년 3월 28일 퇴임하였습니다.', topic='겸직 결정', fy='FY2024',
  note='(판단) 원문 「겸임」 — 김태오 전 회장의 대구은행장 겸임 기간과 퇴임일. 종료일 「2020년 9월 30일」은 FY2020 보고서(I1-D20-a)의 「2020년 9월 28일」과 다름')
S('I3-iM25-a', 'iM25', '주) 황병우 회장 iM뱅크 은행장 겸직 중으로', '9호 안건에 대해 의결권 행사하지 않음', topic='겸직 결정', fy='FY2025',
  note='(판단) 원문 「겸직」 — 2025년도 이사회 개최내역 표 주석(제12차 이사회 쪽). 2026.1 자회사 은행장 공시가 목록에 없어 연차보고서로 보충')
S('I3-iM25-b', 'iM25', '2025년 3월 26일 개최된 제1차 그룹임원후보추천위원회에서는 그룹임원후보추천위원회 위원장을', 'iM뱅크 강정훈 은행장을 최종후보자로 추천하였습니다.',
  topic='분리', fy='FY2025',
  note='(판단) 원문에 「분리」 낱말 없음 — iM뱅크 최고경영자 선임 절차(제2~5차, 2025.9.19~12.19)와 최종후보자 추천 사실 문장. 2026.1 자회사 은행장 공시가 목록에 없어 연차보고서로 보충')

# (2) 8개 은행지주 FY2025 — 자회사 CEO 후보 관리·경영성과 평가(아래 FY2025 절)
T2 = '자회사 CEO 평가'
NA2 = ('찾은 범위: {rng}, 검색어 「자회사」「계열사」「관계회사」「CEO」「대표이사」「최고경영자」「후보군」「성과평가」「경영성과」「평가지표」「KPI」「평가항목」'
       '(공백 무시, 쪽 단위). {got}')
# KB — 본공시(KB25)·추가공시(KB25A). 6차 섹션과 같은 PDF(sha256 같음)
S('I2-KB-a', 'KB25', '계열사대표이사후보추천위원회는 전문성과 리더십을 겸비한 역량 있는 계열사 대표이사 후보자를', '제4조 및 제5조에서 서술하고 있습니다.', topic=T2,
  note='계열사대표이사후보추천위원회 「가. 역할(권한과 책임)」 문단(후보자 자격요건 검증·심사·선정)')
S('I2-KB-b', 'KB25', '2025년 중 계열사대표이사후보추천위원회는 총 4회 개최되었습니다.', 'KB저축은행 대표이사 후보를 선정하여 결의하였습니다.', topic=T2,
  note='계열사대표이사후보추천위원회 「(1) 활동내역 개요」(후보자군 보완·확정, 은행장 경영승계 계획 적정성 점검)')
S('I2-KB-c', 'KB25', '또한, 매 반기마다 ‘사외이사 후보자군 관리현황’', '후보자군 관리의 적정성을 점검하였습니다.', topic=T2,
  note='이사회 활동 서술 — 계열사 대표이사 후보자군 관리현황 반기 보고')
S('I2-KB-d', 'KB25', '이사회는 매 분기 ‘경영성과’를 보고 받고', '계열사 차원의 실행력을 제고하고 있습니다.', topic=T2,
  note='이사회 활동 서술 — 경영계획을 계열사 대표이사 성과평가·보수 체계와 연계')
S('I2-KB-e', 'KB25A', '라. [보고] 2024년 자회사 경영진 보상결과:', '성과보상의 지급방법 보고', topic=T2,
  note='추가공시 — 보상위원회 회의 「주요 안건에 대한 세부내용」. 「자회사 경영진」에 계열사 대표이사가 드는지는 이 문장에 없음')
S('I2-KB-f', 'KB25', '나. 2024년 자회사 성과평가 결과(안): 2024년 자회사 종합 득점 현황', '각 회사 KPI별 실적 평가결과 현황 결의', topic=T2,
  note='평가보상위원회 회의 「주요 안건에 대한 세부내용」(결의) — 2024년 자회사(회사) 종합 득점·KPI별 실적 평가결과. KPI 이름과 계열사 대표이사 평가인지는 이 문장에 없음(검증 15b_I 보충)')
NA('I2-KB-na', 'KB25A', T2, '계열사 대표이사 경영성과 평가지표(KPI·평가항목) 문서에 없음. ' + NA2.format(
    rng='본공시·추가공시 전체(더 넓힌 검색어 「KPI」「지표」「가중치」「비중」「계량」「종합 득점」 포함)',
    got='경영계획을 계열사 대표이사 성과평가와 연계한다는 문장(I2-KB-d), 보상위원회의 자회사 경영진 성과평가·보상 결과 보고(I2-KB-e), '
        '「2024년 자회사 종합 득점 현황 및 각 회사 KPI별 실적 평가결과 현황 결의」(I2-KB-f, KPI 이름 없음)만 있음'))
# 신한 — 본공시(SH25)
S('I2-SH-a', 'SH25', '당사는 자회사 대표이사의 자격요건 설정, 대표이사 후보자 추천, 자회사 CEO 리더십 평가에 관한 사항',
  '자회사최고경영자후보추천위원회를 구성하여 상시 운영하고 있습니다.', topic=T2, note='자회사최고경영자후보추천위원회 「가. 역할」')
S('I2-SH-b', 'SH25', '자회사최고경영자후보추천위원회는 현임 자회사 대표이사, 육성후보군, 퇴임후보군', '추천을 활용할 수 있도록 하고 있습니다.', topic=T2,
  note='「(2) 자회사 대표이사 후보추천 및 경영승계 절차」 중 승계후보군 선정 문단')
S('I2-SH-c', 'SH25', '또한, 당사는 지속가능 경영체계를 강화하기 위해 내부 경영진을 대상으로 자회사 대표이사 육성후보군을',
  '중요한 요소로 고려되고 있습니다.', topic=T2, note='육성후보군 선정·개발 프로그램과 경영성과·개발활동 결과 심의·평가 문단')
S('I2-SH-d', 'SH25', '자회사최고경영자후보추천위원회는 자회사 경영승계계획에 따라 내부후보와 그룹에 소속되지 않은 외부후보를 포함한',
  '압축후보군 중에서 최종 후보를 추천합니다.', topic=T2, note='「(3) 자회사 대표이사 후보군 관리 현황」 문단')
S('I2-SH-e', 'SH25', '(가) 2025년도 제1회 자회사최고경영자후보추천위원회 : 2025.3.4', '서술형 평가 등으로 구성됩니다.', topic=T2,
  note='회의 개최내역 (가)·(나) — 2025년 자회사 CEO 리더십 평가체계 수립, 육성후보군 평가 구성')
S('I2-SH-f', 'SH25', '(바) 2025년도 제6회 자회사최고경영자후보추천위원회 : 2025.11.18', '2025년 자회사 대표이사 리더십 평가의 건을 심의 · 의결하였습니다.',
  topic=T2, note='회의 개최내역 (바) — 자회사 대표이사 리더십 평가 의결')
S('I2-SH-g', 'SH25', '(가) 2025년도 제1회 회장후보추천위원회 : 2025.3.4', '그룹 CEO 적합성 평가로 구성됩니다.', topic=T2,
  note='회장후보추천위원회 회의 개최내역 — 그룹 경영승계 육성후보군 평가 구성에 「자회사 CEO에 대한 경영리더십 평가」가 듦')
S('I2-SH-h', 'SH25', '(나) 자회사에 대한 주요 성과지표', '그룹KPI, 회사KPI, 전략과제를 성과지표로 사용하고 있습니다.', topic=T2,
  note='보수 절 성과측정 「(나) 자회사에 대한 주요 성과지표」 — 자회사(회사) 성과측정 지표 구분. 지표 세부 이름·비중과 자회사 대표이사 개인 지표는 이 문단에 없음(검증 15b_I 보충)')
S('I2-SH-i', 'SH25', '4. 자회사 경영진의 평가 및 보수와 관련한 사항', '4. 자회사 경영진의 평가 및 보수와 관련한 사항', topic=T2,
  note='지배구조 일반 표 — 보수위원회 주요 역할 4호(검증 15b_I 보충)')
S('I2-SH-j', 'SH25', '③ 대표이사 회장은 위원회에서 수립된 자회사 경영승계계획에 따라', '위원회의 심의를 받아야 한다. (2023.3.23 개정)', topic=T2,
  note='첨부 자회사최고경영자후보추천위원회규정 제7조(자회사 경영승계계획) ③ — 자회사 대표이사 후보군 평가결과 심의(검증 15b_I 보충)')
NA('I2-SH-na', 'SH25', T2, '자회사 CEO 리더십 평가체계의 평가지표·평가항목과 자회사 CEO 경영성과(KPI) 평가지표(지표 이름·비중) 문서에 없음. ' + NA2.format(
    rng='본공시 전체(자회사최고경영자후보추천위원회 절 p.183~189, 회장후보추천위원회 절, 보수 절)와 추가공시(2026-04-08) 전체, 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함',
    got='평가체계 수립·평가 의결 사실(I2-SH-e·f), 육성후보군 평가 구성(I2-SH-e·g), 자회사(회사) 성과지표 구분 「그룹KPI, 회사KPI, 전략과제」(I2-SH-h)만 있음'))
# 하나 — 본공시(HN25). 하나는 「관계회사」 낱말
S('I2-HN-a', 'HN25', '그룹임원후보추천위원회는 주요 관계회사 최고경영자 후보 또는', '관계회사경영관리위원회에서 심의합니다.', topic=T2,
  note='그룹임원후보추천위원회 「가. 역할(권한과 책임)」 — 주요 관계회사 6개사 최고경영자 후보 심의·추천, 후보군 관리')
S('I2-HN-b', 'HN25', '2025년도에 그룹임원후보추천위원회는 총 6회 개최되었고', '총 35명의 후보군(Long List)을 선정하였습니다.', topic=T2,
  note='그룹임원후보추천위원회 「1) 활동내역 개요」 앞부분(제4회까지)')
S('I2-HN-c', 'HN25', '마. 경영발전보상위원회 규정 개정', '규정 개정(안)이 가결되었습니다.', topic=T2,
  note='이사회 활동 서술 — 경영발전보상위원회 결의사항에 주요 관계회사 연간 성과평가기준 수립 및 평가 신설')
S('I2-HN-d', 'HN25', '라) 지주 자추위의 자회사 대표이사 후보 검증 강화', '심사할 수 있도록 개선할 필요가 있음.', topic=T2,
  note='「15. 감독당국 권고사항 및 개선계획」 개선사항 라)')
S('I2-HN-e', 'HN25', '차) 자회사 성과평가기준 수립업무 개선', '자회사 성과평가기준 수립업무를 개선할 필요가 있음.', topic=T2,
  note='「15. 감독당국 권고사항 및 개선계획」 개선사항 차)')
S('I2-HN-f', 'HN25', '아울러 주요 관계회사(하나은행, 하나증권', '하나금융지주 임원의 직급별 보수 수준에 대해 심의하였습니다.', topic=T2,
  note='보수위원회(경영발전보상위원회) 절 — 주요 관계회사 6개사 성과평가 기준 수립 및 평가(검증 15b_I 보충)')
S('I2-HN-g', 'HN25', '2025년 2월 개최된 제1회 경영발전보상위원회에서는', '그룹 전체의 목표를 달성할 수 있도록 성과목표가 수립되었는지 점검하였습니다.', topic=T2,
  note='경영발전보상위원회 「2) 활동내역 개요」 — 관계회사 성과평가 실시, 2026년도 성과평가기준 수립, 관계회사 평가보상위원회 결의사항 보고. 쪽 넘김(p.325→p.326) 사이 쪽 번호·머리글 포함(검증 15b_I 보충)')
S('I2-HN-h', 'HN25', '가. 2024 년 주요 관계회사 성과평가 : 주요 관계회사(하나은행 포함 6 개 자회사)의 2024 년',
  '리스크관리, 감사 부문 평가를 실시하였습니다.', topic=T2,
  note='경영발전보상위원회 회의 「주요 의안 세부 내용」(결의) — 2024년 주요 관계회사 경영성과평가·부문 평가 실시(검증 15b_I 보충)')
S('I2-HN-i', 'HN25', '다. 2026 년 주요 관계회사 성과평가 기준 수립 : 주요 관계회사(하나은행 포함 6 개 자회사)의',
  '감사 부문의 성과평가기준(KPI)을 수립하였습니다.', topic=T2,
  note='경영발전보상위원회 회의 「주요 의안 세부 내용」(결의) — 2026년 주요 관계회사 성과평가기준(KPI) 부문(경영성과·내부통제·리스크관리·감사). 지표 이름은 이 문장에 없음(검증 15b_I 보충)')
NA('I2-HN-na', 'HN25', T2, '주요 관계회사 최고경영자 개인 경영성과 평가지표(지표 이름·비중) 문서에 없음. ' + NA2.format(
    rng='본공시 전체와 추가공시(2026-04-08) 전체, 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함',
    got='경영발전보상위원회의 주요 관계회사 성과평가·성과평가기준 수립 문장(I2-HN-c·f·g·h), 2026년 관계회사 성과평가기준(KPI) 부문 문장(I2-HN-i, 지표 이름 없음), 감독당국 권고 개선사항(I2-HN-e)만 있음'))
# 우리 — 본공시(WR25)
S('I2-WR-a', 'WR25', '(1) 총괄 자회사대표이사후보추천위원회는 자회사 대표이사 후보자 자격요건 검증', '보완·개선 하여 매년 이사회에 보고함', topic=T2,
  note='자회사대표이사후보추천위원회 「가. 역할(권한과 책무)」(총괄·구체적 역할 표 포함)')
S('I2-WR-b', 'WR25', '2025년 자회사대표이사후보추천위원회는 총 5회 개최되었으며', '후보군 관리 및 자격요건 충족 여부 검증을 결의하였습니다. 성명', topic=T2,
  note='「(1) 활동내역 개요」 — 끝의 「성명」은 바로 뒤 표 머리 글자')
S('I2-WR-c', 'WR25', '(나) 제2025년도 2차 보상위원회 : 2025.3.18.', '2) 2025년 자회사 성과평가기준(안)에 대하여 승인을 받기 위함', topic=T2,
  note='보상위원회 회의 개최내역 — 2025년 자회사 성과평가기준(안) 가결')
S('I2-WR-d', 'WR25', '(다) 제2025년도 3차 보상위원회 : 2025.7.25.', '성과평가기준(안)에 대하여 승인을 받기 위함', topic=T2,
  note='보상위원회 회의 개최내역 — 2025년 동양생명보험/ABL생명보험 성과평가기준(안) 가결')
S('I2-WR-e', 'WR25', '신규 편입 보험사의 성과평가기준 수립 時, 자회사의 의견을 충분하게 청취하여 수립', '하여야 함', topic=T2,
  note='사외이사 이강행 주요 발언 및 토의 내용(경영관리) 표')
S('I2-WR-f', 'WR25', '가. 1호안건1) (2024년 지주사 경영실적 평가(안))', '2) 2024년 자회사 경영실적 평가(안)에 대하여 승인을 받기 위함', topic=T2,
  note='보상위원회 회의 개최내역 (가) 제2025년도 1차 보상위원회 표 — 2024년 자회사 경영실적 평가(안) 가결과 승인 목적(검증 15b_I 보충)')
S('I2-WR-g', 'WR25', '▪의결안건 가) 자회사 경영성과 Review를 통해 우리벤처파트너스', '임기는 1년을 부여하는 것으로 결의하였습니다.', topic=T2,
  note='자회사대표이사후보추천위원회 회의 (나) 제2차(2025.03.18) 「주요 안건에 대한 세부내용」 — 자회사 경영성과 Review 후 연임 추천(검증 15b_I 보충)')
S('I2-WR-h', 'WR25', '▪의결안건 다) 자회사 경영성과 Review를 통해 우리금융경영연구소', '임기는 1년을 부여하는 것으로 결의하였습니다.', topic=T2,
  note='자회사대표이사후보추천위원회 회의 「주요 안건에 대한 세부내용」 — 자회사 경영성과 Review 후 연임 추천(검증 15b_I 보충)')
NA('I2-WR-na', 'WR25', T2, '자회사 대표이사 경영성과 평가지표(KPI·평가항목) 문서에 없음. ' + NA2.format(
    rng='본공시 전체와 추가공시(2026-03-13) 전체, 더 넓힌 검색어 「지표」「가중치」「비중」「계량」「Review」 포함',
    got='보상위원회의 「자회사 경영실적 평가(안)」「자회사 성과평가기준(안)」 가결과 승인 목적 문장(I2-WR-c·d·f), 자추위의 「자회사 경영성과 Review」 문장(I2-WR-g·h)만 있고 기준·지표 내용은 없음'))
# iM — 본공시(iM25)
S('I2-iM-a', 'iM25', '그룹임원후보추천위원회에서는 그룹임원후보추천위원회규정 및 최고경영자경영승계', '이사회에 보고하게 됩니다.', topic=T2,
  note='그룹임원후보추천위원회 「가. 역할」 — 자회사 대표이사 자격요건 설정·후보군 관리·최종 후보자 추천')
S('I2-iM-b', 'iM25', 'iM금융지주는 자회사의 최고경영자 후보추천과 관련한 절차를', 'iM뱅크 주주총회 결의로 최고경영자를 선임하여 경영승계 절차를 종료한다.', topic=T2,
  note='「2) 후보 추천절차」 <iM뱅크>(최종 후보군 육성·검증 포함)')
S('I2-iM-c', 'iM25', '1. 자회사 최고경영자 후보군 연간활동내용', '특이의견 없음', topic=T2,
  note='그룹임원후보추천위원회 회의 표의 보고 안건 칸')
S('I2-iM-d', 'iM25', '이 회사는 다음의 사업을 영위함을 목적으로 한다.', '2. 자회사등의 경영성과의 평가 및 보상의 결정', topic=T2,
  note='(판단) 첨부 정관 제2조(목적) 사업 목록 — 「자회사등의 경영성과의 평가 및 보상의 결정」. 자회사 최고경영자 평가 절차 문단은 아님(검증 15b_I 보충)')
NA('I2-iM-na', 'iM25', T2, '자회사 최고경영자 경영성과 평가 절차·평가지표(KPI·평가항목) 문서에 없음. ' + NA2.format(
    rng='본공시·추가공시 전체, 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함',
    got='후보군 관리·추천 절차(I2-iM-a·b)와 정관 사업 목록의 「자회사등의 경영성과의 평가 및 보상의 결정」(I2-iM-d)만 있음'))
# BNK — 본공시(BNK25)
S('I2-BNK-a', 'BNK25', '(2)구체적 역할 위원회는 자회사 CEO 경영승계계획의 수립 및 변경', '자회사 CEO 후보자 심사 및 추천 등의 역할을 수행합니다.', topic=T2,
  note='자회사CEO후보추천위원회 「가. 역할(권한과 책임)」 (2)')
S('I2-BNK-b', 'BNK25', '자회사CEO후보추천위원회는 자회사 CEO 경영승계계획의 적정성을 연 1회 이상 점검하고', 'CEO 후보 통합 Pool로 운용', topic=T2,
  note='자회사 CEO 경영승계 계획 점검과 「(2)자회사 CEO 후보군 관리 현황」(후보군 표 포함)')
S('I2-BNK-c', 'BNK25', '2024년 7월 제6차 이사회에서 최고경영자 경영승계 계획 적정성 점검 시 최고', '1on1 코칭으로 진행되었습니다.', topic=T2,
  note='최고경영자 경영승계 절 — 지주 및 자회사 CEO 후보군 대상 육성후보군 연수')
S('I2-BNK-d', 'BNK25', '9.자회사 성과평가 기준 수립 및 결과 확정에 관한 사항(2026.3.1 신설)', '9.자회사 성과평가 기준 수립 및 결과 확정에 관한 사항(2026.3.1 신설)',
  topic=T2, note='첨부 보수위원회규정 제6조(심의ㆍ결의사항 등) ① 9호')
NA('I2-BNK-na', 'BNK25', T2, '자회사 CEO 경영성과 평가 절차·평가지표(KPI·평가항목) 문서에 없음. ' + NA2.format(
    rng='본공시 전체(추가공시 없음), 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함', got='보수위원회규정의 「자회사 성과평가 기준 수립 및 결과 확정」 조항(2026.3.1 신설, I2-BNK-d)만 있음'))
# JB — 정정공시(JB25C). 본공시 쪽 텍스트는 글자층이 겹쳐(같은 줄이 두 번, 숫자 빠진 줄) 정정공시 글을 씀
S('I2-JB-a', 'JB25C', 'JB금융지주 자회사CEO후보추천위원회에서는 자회사CEO 경영승계 계획을 수립하여', '경영승계 절차의 간소화가 가능합니다.', topic=T2,
  note='「2) 자회사 CEO 후보추천 및 경영승계 절차」(내부평가 적극적 요건·다면평가)')
S('I2-JB-b', 'JB25C', '3) 후보군 관리 당사는 자회사CEO 후보군 관리를 위하여', '그룹임원 3, 외부자문기관 추천 2', topic=T2,
  note='「3) 후보군 관리」와 <자회사 CEO 후보군 현황> 표')
S('I2-JB-c', 'JB25C', '2025년 중 자회사CEO후보추천위원회는 총 9회 개최되어', '최종 선정하였습니다.', topic=T2,
  note='「1) 활동내역 개요」')
S('I2-JB-d', 'JB25C', '이 회사는 다음의 사업을 영위함을 목적으로 한다.', '2. 자회사등의 경영성과의 평가 및 보상의 결정', topic=T2,
  note='(판단) 첨부 정관 제2조(목적) 사업 목록 — 「자회사등의 경영성과의 평가 및 보상의 결정」. 자회사 CEO 평가 절차 문단은 아님(검증 15b_I 보충)')
S('I2-JB-e', 'JB25C', '② 자회사CEO 경영승계 계획에는 다음 각 호의 사항을 포함하여야 한다.', '4. 자회사CEO 후보군 평가기준 및 평가방법', topic=T2,
  note='첨부 자회사CEO후보추천위원회규정 제5조(자회사CEO 경영승계계획) ② — 경영승계계획에 들어갈 사항(후보군 평가기준 및 평가방법). 평가기준 내용은 없음(검증 15b_I 보충)')
NA('I2-JB-na', 'JB25C', T2, '자회사 CEO 경영성과 평가 절차·평가지표(KPI·평가항목) 문서에 없음. ' + NA2.format(
    rng='정정공시 전체(본공시는 같은 쪽 글자층 겹침으로 정정공시로 찾음), 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함',
    got='후보군 관리·추천 절차(I2-JB-a·b·c·e)와 정관 사업 목록의 「자회사등의 경영성과의 평가 및 보상의 결정」(I2-JB-d)만 있음'))
# NH — 6차 섹션(NH25, gov_old 다시 받기 막힘)
S('I2-NH-a', 'NH25', '또한 위원회는 금융지주 대표이사 회장 및 완전자회사 대표이사', '완전자회사 대표이사 후보를 해당 회사 임원후보추천위원회(이사회)에 추천합니다.',
  topic=T2, note='임원후보추천위원회 「가. 역할(권한과 책임)」 — 완전자회사 대표이사 후보 추천')
S('I2-NH-b', 'NH25', '동 규범에서는 임원후보추천위원회의 추천 대상을', '위원회에서 개시시기를 변경 할 수 있습니다.', topic=T2,
  note='「2) 후보 추천 절차」 — 완전자회사 경영승계절차 개시 시기')
S('I2-NH-c', 'NH25', '2. 자회사 대표이사에 대한 경영성과 평가 3. 자회사 경영진(대표이사 제외)에 대한 성과평가·보상체계의 적정성 검토',
  '2. 자회사 대표이사에 대한 경영성과 평가 3. 자회사 경영진(대표이사 제외)에 대한 성과평가·보상체계의 적정성 검토', topic=T2, first=True,
  note='보수위원회 역할 목록(첫 번째 나온 곳 — 같은 글이 뒤 규정 첨부(시작페이지 272·315)에도 있음)')
S('I2-NH-d', 'NH25', '(의안 제2호 ) 자회사 대표이사 성과평가 방안', 'NH농협리츠운용 , NH벤처투자', topic=T2,
  note='보수위원회 회의 「주요 안건 내용」 — 2025년도 자회사 대표이사 9명 경영목표 설정·성과평가 방안·보상체계 의결(같은 쪽 뒤에 「2025년도 제2차 보수위원회 : 2025. 3. 7.」)')
S('I2-NH-e', 'NH25', '(의안 제 6호) 2024 년도 자회사 대표이사 성과평가', 'NH농협리츠운용 , NH벤처투자', topic=T2,
  note='보수위원회 회의 「주요 안건 내용」 — 2024년도 자회사 대표이사 9명 계량평가·역량평가')
S('I2-NH-f', 'NH25', '(의안 제10 호 ) 2025 년도 자회사 대표이사 역량평가', 'NH농협리츠운용 , NH벤처투자', topic=T2,
  note='보수위원회 회의 「주요 안건 내용」 — 2025년도 자회사 대표이사 9명 계량평가·역량평가')
S('I2-NH-g', 'NH25', '보수위원회는 성과보상체계가 리스크·경영목표와 연계하여 관리될 수 있도록', '보상체계 적정성을 검토하는 역할을 수행합니다.', topic=T2,
  note='지배구조 일반 — 보수위원회 역할 서술(자회사 대표이사의 경영성과 평가 및 보상체계 적정성 검토)(검증 15b_I 보충)')
S('I2-NH-h', 'NH25', '특히, 보수위원회 위원장으로서 금융지주 대표이사 회장과 자회사 대표이사의 성과평가', '내실있는 금융회사 성장을 위한 기반 을 다졌습니다.',
  topic=T2, first=True,
  note='사외이사(길재욱) 활동 서술 — 2025년도 자회사 대표이사 역량평가에 재무성과 외 전략·리더십·인재육성·소비자보호·고객신뢰 제고 등을 포함. '
       '섹션 글 안 쪽 번호 「90 2025년 지배구조 및 보수체계 연차보고서」 글자 포함(검증 15b_I 보충)')
S('I2-NH-i', 'NH25', '당사 보수위원회는 이사회에서 위임한 사항에 대하여 심의·의결하며', '총 11건의 안건을 처리하였습니다.', topic=T2,
  note='보수위원회 「2) 활동내역 개요」(지주회사 및 자회사 경영진 성과평가·보상체계 관리)(검증 15b_I 보충)')
NA('I2-NH-na', 'NH25', T2, '자회사 대표이사 계량평가 지표(KPI) 이름·비중 문서에 없음. ' + NA2.format(
    rng='6차 섹션 글 전체(본공시 683 조각)와 추가공시 6차 섹션 글(682 조각), 더 넓힌 검색어 「지표」「가중치」「비중」「계량」 포함',
    got='보수위원회의 성과평가 방안·계량평가 및 역량평가 실시 안건 문장(I2-NH-d·e·f)과 역량평가 포함 요소 서술(I2-NH-h: 재무성과 외 전략·리더십·인재육성·소비자보호·고객신뢰 제고 등)만 있음'))


def req_line(prefix):
    for ln in open(J('dart_out/ops15/REQUEST15b.md'), encoding='utf-8'):
        s = ln.strip()
        if s.startswith('* ' + prefix):
            return s[2:]
    raise KeyError(prefix)


def list_rows(corp_code, pattern):
    seen, metas = {}, []
    for f in sorted(glob.glob(J(f'dart_out/raw/list/{corp_code}_{pattern}_p*.json'))):
        if f.endswith('.meta.json'):
            continue
        for x in json.load(open(f, encoding='utf-8')).get('list', []):
            seen[x['rcept_no']] = x
        m = f + '.meta.json'
        if os.path.exists(m):
            metas.append(json.load(open(m, encoding='utf-8')))
    return seen, metas


LIST_SPEC = {  # 사건 → (corp_code, 캐시 꼴, 기간)
    '우리금융지주': ('01350869', '19990101_20260831'),
    'iM금융지주': ('00878915', '19990101_20260831'),
    'BNK금융지주': ('00858364', '20170101_20171231'),
}
KW_RE = re.compile(r'자회사의 ?주요경영사항|대표이사|은행장|임원')
EXCL_RE = re.compile(r'소유상황보고서|대량보유')


def scan_list(label, a, b):
    """기간 [a,b](YYYYMMDD) 목록에서 보고서명 키워드 행. 반환: (전체 건수, 키워드 행, 소유상황 제외 건수, 목록 출처 글, 받은 시각)."""
    cc, pat = LIST_SPEC[label]
    seen, metas = list_rows(cc, pat)
    rows = [x for x in seen.values() if a <= x['rcept_dt'] <= b]
    hit = [x for x in rows if KW_RE.search(x['report_nm']) and not EXCL_RE.search(x['report_nm'])]
    excl = [x for x in rows if KW_RE.search(x['report_nm']) and EXCL_RE.search(x['report_nm'])]
    src = (f'OpenDART list.json corp_code={cc} bgn_de={pat[:8]} end_de={pat[9:]} 거래소공시 포함(pblntf_ty 없음) — '
           f'캐시 dart_out/raw/list/{cc}_{pat}_p*.json')
    fetched = max((to_kst(m.get('fetched_at', '')) for m in metas), default='')
    return len(rows), sorted(hit, key=lambda x: x['rcept_no']), len(excl), src, fetched


def write_check_and_docs(rows):
    by = {r['_rid']: r for r in rows}
    LA = req_line('지배구조 및 보수체계 연차보고서: 회장·은행장')
    LB = req_line('자회사의 주요경영사항 공시(은행장 선임)')
    chk = []

    def where(*rids):
        out = []
        for rid in rids:
            r = by[rid]
            out.append(f"I.csv {r['corp_label']}·{r['fy_or_date']}·{r['topic']}·{r['page'] or '문서에 없음'}")
        return '; '.join(out)

    def add(iid, text, corp, fy, result, rids=(), note='', url=None, page=None, excerpt_rid=None):
        r0 = by[excerpt_rid] if excerpt_rid else (by[rids[0]] if rids else None)
        ex = ''
        if result == '원문 있음' and r0 is not None and r0['source_text'] != '문서에 없음':
            ex = r0['source_text'][:300]
        chk.append(dict(item_id=iid, item_text=text, corp_label=corp, fy=fy, result=result, where=where(*rids) if rids else '',
                        rcept_no_or_url=url if url is not None else (r0['rcept_no_or_url'] if r0 is not None else ''),
                        page=page if page is not None else (r0['page'] if r0 is not None and result == '원문 있음' else ''),
                        source_excerpt=ex, note=note))

    # (1) 회장·은행장 겸직·분리 이유
    for x in GOV_OLD:
        if x['corp_label'] == 'KB금융지주' and x['fy_or_date'] in ('FY2014', 'FY2015', 'FY2016') and x['status'] == '실패':
            fy = x['fy_or_date']
            if any(c['item_id'] == f'I1-KB-{fy}' for c in chk):
                chk[-1]['rcept_no_or_url'] += ' ; ' + x['rcept_no_or_url']
                chk[-1]['note'] += f" / {x['report_nm']}({x['rcept_dt']}) 도 같은 사유로 실패"
                continue
            chk.append(dict(item_id=f'I1-KB-{fy}', item_text=LA, corp_label='KB금융지주', fy=fy, result='수집 실패', where='',
                            rcept_no_or_url=x['rcept_no_or_url'], page='(수집 실패 — 받은 글 없음)', source_excerpt='',
                            note=f"{x['report_nm']}({x['rcept_dt']}) — gov_old 문서목록(dart_out/ops15/문서목록15b_gov_old.csv) status 「실패」: "
                                 '누리집 게시판 첨부 내려받기에서 목록 경로는 200·6바이트(PDF 아님), 게시판 내려받기 주소는 HTTP 500. 이 작업에서는 웹 수집하지 않음(COMMON15b)'))
    add('I1-KB-FY2017', LA, 'KB금융지주', 'FY2017', '문서에 없음', ('I1-KB17-na', 'I1-KB17-a', 'I1-KB17-b', 'I1-KB17-c', 'I1-KB17-d'),
        note='겸직·분리를 정한 이유 문단 없음(본공시·추가공시 2018-04-13). 국민은행장 후보 결의 사실(p.39)·회장 경력 「회장 겸 국민은행 은행장」(p.26)·'
             '비상임이사 허인 경력 「KB 국민은행 은행장」(p.26~27)·그룹경영관리위원회 구성 표의 회장·국민은행장 두 행(p.142)만 있음',
        url=by['I1-KB17-na']['rcept_no_or_url'], page=by['I1-KB17-na']['page'])
    add('I1-W-FY2019', LA, '우리금융지주', 'FY2019', '문서에 없음', ('I1-W19-na', 'I1-W19-a', 'I1-W19-b'),
        note='겸직을 정한 이유 문단 없음(본공시·추가공시 2020-05-14). 이사 소개의 「회장 겸 우리은행 은행장으로 재직중」(p.13~14)과 대표이사 후보 경력 줄(p.28)만 있음',
        url=by['I1-W19-na']['rcept_no_or_url'], page=by['I1-W19-na']['page'])
    add('I1-DGB-FY2018', LA, 'iM금융지주', 'FY2018', '문서에 없음', ('I1-D18-na', 'I1-D18-a', 'I1-D18-b'),
        note='겸직을 정한 이유 문단 없음. 전임 회장 박인규 「사임 당시 DGB금융지주 회장 겸 대구은행 은행장」(p.16)과 2018년 12월말 그룹경영관리협의회 구성 표의 「대구은행장 직무대행」(p.158)만 있음',
        url=by['I1-D18-na']['rcept_no_or_url'], page=by['I1-D18-na']['page'])
    add('I1-DGB-FY2019', LA, 'iM금융지주', 'FY2019', '문서에 없음', ('I1-D19-na', 'I1-D19-a', 'I1-D19-b'),
        note='겸직·분리를 정한 이유 문단 없음. 김태오 회장 「2019년 01월 29일부터 대구은행장을 겸임」(p.15)과 대구은행 최고경영자 경영승계 개시·최종후보군 선정(p.32)만 있음',
        url=by['I1-D19-na']['rcept_no_or_url'], page=by['I1-D19-na']['page'])
    add('I1-DGB-FY2020', LA, 'iM금융지주', 'FY2020', '문서에 없음', ('I1-D20-na', 'I1-D20-a', 'I1-D20-b', 'I1-D20-c', 'I1-D20-d'),
        note='분리를 정한 이유 문단 없음. 겸임 기간 「2019년 1월 29일부터 2020년 9월 28일까지」(p.14)·회장 후보 경력 「대구은행 은행장(2020.09월까지 겸임)」(p.56), '
             '임성훈 대구은행 대표이사 최종후보자 추천(p.127~128), 그룹경영관리협의회 구성 표의 대구은행장 임성훈 선임일 2020.09.29·임기만료일 2022.12.31(p.134)만 있음',
        url=by['I1-D20-na']['rcept_no_or_url'], page=by['I1-D20-na']['page'])
    add('I1-BNK-FY2017', LA, 'BNK금융지주', 'FY2017', '문서에 없음', ('I1-B17-na', 'I1-B17-a', 'I1-B17-c', 'I1-B17-b', 'I1-B17-d', 'I1-B17-e', 'I1-B17-f', 'I1-B17-g'),
        note='분리를 정한 이유 문단 없음. 제12차 임시이사회(2017.7.13) 「지주 회장 및 부산은행장 분리 여부」 보류 기재(p.37·p.86), 전 회장 겸임 기간(p.24), '
             '이사회 심의안건 「부산은행 사내이사 은행장 후보 추천 사전협의」(제18차 2017.9.8, p.40)·「후보 확정 사전협의」(제19차 2017.9.11, p.41), '
             '그룹경영관리협의회 구성 표의 회장 김지완·부산은행 은행장 빈대인(p.172), 회장·부산은행장 직무대행 주석(p.173)만 있음',
        url=by['I1-B17-na']['rcept_no_or_url'], page=by['I1-B17-na']['page'])
    # (2) FY2025 자회사 CEO 평가
    plan = {
        '신한금융지주': ('SH', ['I2-SH-a', 'I2-SH-b', 'I2-SH-c', 'I2-SH-d', 'I2-SH-j'], ['I2-SH-e', 'I2-SH-f', 'I2-SH-g', 'I2-SH-i'], 'I2-SH-na'),
        'KB금융지주': ('KB', ['I2-KB-a', 'I2-KB-b', 'I2-KB-c'], ['I2-KB-d', 'I2-KB-e', 'I2-KB-f'], 'I2-KB-na'),
        '하나금융지주': ('HN', ['I2-HN-a', 'I2-HN-b', 'I2-HN-d'], ['I2-HN-c', 'I2-HN-e', 'I2-HN-f', 'I2-HN-g', 'I2-HN-h'], 'I2-HN-na'),
        '우리금융지주': ('WR', ['I2-WR-a', 'I2-WR-b'], ['I2-WR-c', 'I2-WR-d', 'I2-WR-e', 'I2-WR-f', 'I2-WR-g', 'I2-WR-h'], 'I2-WR-na'),
        'NH농협금융지주': ('NH', ['I2-NH-a', 'I2-NH-b'], ['I2-NH-c', 'I2-NH-d', 'I2-NH-e', 'I2-NH-f', 'I2-NH-g', 'I2-NH-i'], 'I2-NH-na'),
        'iM금융지주': ('iM', ['I2-iM-a', 'I2-iM-b', 'I2-iM-c'], [], 'I2-iM-na'),
        'BNK금융지주': ('BNK', ['I2-BNK-a', 'I2-BNK-b', 'I2-BNK-c'], ['I2-BNK-d'], 'I2-BNK-na'),
        'JB금융지주': ('JB', ['I2-JB-a', 'I2-JB-b', 'I2-JB-c', 'I2-JB-e'], [], 'I2-JB-na'),
    }
    # 평가지표 — 원문에 지표 구분·평가 요소 낱말이 있는 회사(검증 15b_I 에서 찾음). 나머지는 「문서에 없음」
    kpi = {
        'SH': ('I2-SH-h', '자회사(회사) 성과측정 지표 구분 「그룹KPI, 회사KPI, 전략과제」만 있음 — 지표 이름·비중과 자회사 대표이사 개인 지표는 문서에 없음(I.csv 「문서에 없음」 행)'),
        'HN': ('I2-HN-i', '2026년 주요 관계회사 성과평가기준(KPI)의 부문(경영성과·내부통제·리스크관리·감사)만 있음 — 지표 이름·비중은 문서에 없음; 관계회사 최고경영자 평가인지는 원문에 없음'),
        'NH': ('I2-NH-h', '사외이사 활동 서술에 2025년도 자회사 대표이사 역량평가 포함 요소(재무성과 외 전략·리더십·인재육성·소비자보호·고객신뢰 제고 등)만 있음 — 계량평가 지표(KPI) 이름·비중은 문서에 없음'),
    }
    na_where = {'iM': ('I2-iM-d',), 'JB': ('I2-JB-d',)}
    proc_note = {
        'KB': '경영계획을 계열사 대표이사 성과평가·보수 체계와 연계한다는 문장, 보상위원회의 자회사 경영진 성과평가·보상 결과 보고, 평가보상위원회의 「2024년 자회사 성과평가 결과(안)」(종합 득점·KPI별 실적) 결의',
        'SH': '자회사 CEO 리더십 평가체계 수립(2025.3.4)·자회사 대표이사 리더십 평가 의결(2025.11.18)과 육성후보군 평가 구성 문장, 보수위원회 역할 「자회사 경영진의 평가 및 보수와 관련한 사항」',
        'HN': '원문 낱말은 「주요 관계회사의 연간 성과평가기준 수립 및 평가」「주요 관계회사 성과평가」「자회사 성과평가기준」 — 관계회사 최고경영자 평가인지는 원문에 없음',
        'WR': '원문 낱말은 「자회사 경영실적 평가(안)」「자회사 성과평가기준(안)」「자회사 경영성과 Review」 — 자회사 대표이사 평가인지는 앞의 둘은 원문에 없음',
        'NH': '보수위원회 역할 「자회사 대표이사에 대한 경영성과 평가」「자회사 대표이사의 경영성과 평가 및 보상체계 적정성을 검토」와 자회사 대표이사 9명 성과평가 방안·계량평가 및 역량평가 안건',
        'BNK': '원문 낱말은 보수위원회규정 「자회사 성과평가 기준 수립 및 결과 확정」(2026.3.1 신설) — 자회사 CEO 평가인지는 원문에 없음',
    }
    for corp, (ab, cand, proc, na) in plan.items():
        add(f'I2-{ab}-후보관리', LA, corp, 'FY2025', '원문 있음', tuple(cand), note=f'자회사 CEO 후보 관리 문단 {len(cand)}행')
        if proc:
            add(f'I2-{ab}-평가절차', LA, corp, 'FY2025', '원문 있음', tuple(proc), note=proc_note[ab])
        else:
            ex = na_where.get(ab, ())
            add(f'I2-{ab}-평가절차', LA, corp, 'FY2025', '문서에 없음', (na,) + ex,
                note='자회사 CEO 경영성과 평가 절차 문단 없음(찾은 범위는 I.csv 「문서에 없음」 행 note)' +
                     ('. 정관 제2조(목적) 사업 목록에 「자회사등의 경영성과의 평가 및 보상의 결정」 한 줄만 있음(I.csv 행)' if ex else ''),
                url=by[na]['rcept_no_or_url'], page=by[na]['page'])
        if ab in kpi:
            add(f'I2-{ab}-평가지표', LA, corp, 'FY2025', '원문 있음', (kpi[ab][0], na), note=kpi[ab][1])
        else:
            add(f'I2-{ab}-평가지표', LA, corp, 'FY2025', '문서에 없음', (na,), note='자회사 CEO 경영성과 평가지표(KPI·평가항목) 없음(찾은 범위는 I.csv 「문서에 없음」 행 note)',
                url=by[na]['rcept_no_or_url'], page=by[na]['page'])
    # (3) 자회사의 주요경영사항 공시(은행장 선임)·같은 달 지주 대표이사 변경·겸직 기간
    events = [
        ('우리금융지주', '2020-03', '20200301', '20200331', None, ('I3-W20-a', 'I3-W20-b'), '원문 있음',
         '이사 현황 표 손태승 경력 「19~20 우리금융그룹 회장 兼 우리은행 은행장」(연 단위)과 권광석 은행장 최종후보 추천(2020.1.29 제4차 자추위, 속개 1.31·2.11) — 겸직 종료 일자는 연 단위(19~20)만'),
        ('iM금융지주', '2020-09', '20200901', '20200930', None, ('I1-D20-a', 'I1-D20-b', 'I3-iM24-b', 'I1-D20-c', 'I1-D20-d'), '원문 있음',
         '겸임 종료일이 FY2020 보고서 「2020년 9월 28일」(p.14)·「2020.09월까지 겸임」(p.56), FY2024 보고서 「2020년 9월 30일」로 다름(행 모두 I.csv). '
         '새 대구은행장 임성훈 선임일 2020.09.29·임기만료일 2022.12.31(FY2020 보고서 p.134 그룹경영관리협의회 구성 표)'),
        ('iM금융지주', '2024-03', '20240301', '20240331', 'I3-iM240328-a', ('I3-iM24-a', 'I3-iM240328-b'), '원문 있음',
         '황병우: 지주 대표이사 변경일 2024-03-28(이사회 결의일), 은행장 겸임 「2023년 1월 1일부터 현재까지」(FY2024 보고서 p.16), 대표이사 회장 임기 「2027년 정기주주총회까지」'),
        ('iM금융지주', '2026-01', '20260101', '20260131', None, ('I3-iM25-a', 'I3-iM25-b'), '문서에 없음',
         'FY2025 보고서에 「황병우 회장 iM뱅크 은행장 겸직 중」(2025년 제12차 이사회 표 주석, p.32)과 「現 iM뱅크 강정훈 은행장을 최종후보자로 추천」(p.122)만 있고 겸직 종료 일자·은행장 임기 없음'),
        ('BNK금융지주', '2017', '20170101', '20171231', 'I3-BNK170927', ('I1-B17-b', 'I1-B17-f'), '원문 있음',
         '전 회장 성세환 「부산은행 은행장(2012.3.22~2017.9.12)을 겸임」(FY2017 보고서 p.24), 지주 대표이사 변경일 2017-09-27(이사회 결의일), '
         '새 부산은행 은행장 빈대인 선임일 2017.09.12·임기만료일 2020.03월과 회장 김지완 선임일 2017.09.27(FY2017 보고서 p.172)'),
    ]
    for corp, ym, a, b, own_rid, period_rids, period_res, period_note in events:
        n, hit, excl, src, fetched = scan_list(corp, a.replace('-', ''), b.replace('-', ''))
        dt = lambda x: f"{x['rcept_dt'][:4]}-{x['rcept_dt'][4:6]}-{x['rcept_dt'][6:]}"
        sub = [x for x in hit if '자회사의' in x['report_nm']]
        bank = [x for x in hit if re.search(r'대표이사|은행장|임원', x['report_nm']) and '자회사의' in x['report_nm']]
        names = '; '.join(sorted({re.sub(r'\s+', '', x['report_nm']) for x in sub}))
        add(f'I3-{corp}-{ym}-자회사공시', LB, corp, ym, '원문 있음' if bank else '문서에 없음', (),
            note=(f'목록 {a[:4]}-{a[4:6]}-{a[6:]}~{b[:4]}-{b[4:6]}-{b[6:]} 보고서 {n}건 중 「자회사의 주요경영사항」 든 것 {len(sub)}건'
                  f'({names or "없음"}) — 은행장·대표이사 선임 보고서 0건; 「임원」이 든 소유상황보고서 {excl}건은 제외. 받은 시각 {fetched}'),
            url=src, page='list.json 공시목록(쪽 없음)')
        own = [x for x in hit if '대표이사' in x['report_nm'] and '자회사의' not in x['report_nm']]
        if own_rid:
            add(f'I3-{corp}-{ym}-지주대표이사', LB, corp, ym, '원문 있음', (own_rid,),
                note='같은 기간 지주 자신의 대표이사 변경 공시: ' + '; '.join(dt(x) + ' ' + x['rcept_no'] + ' ' + re.sub(r'\s+', '', x['report_nm']) for x in own))
        else:
            add(f'I3-{corp}-{ym}-지주대표이사', LB, corp, ym, '문서에 없음', (),
                note=f'같은 기간 목록에 지주 대표이사 변경 공시 없음(보고서명 「대표이사」 0건). 받은 시각 {fetched}', url=src, page='list.json 공시목록(쪽 없음)')
        add(f'I3-{corp}-{ym}-겸직기간', LB, corp, ym, period_res, period_rids, note=period_note + ' — 주요경영사항 공시가 없어 연차보고서 문장으로 확인',
            page=None if period_res == '원문 있음' else na_page({('iM금융지주', '2026-01'): 'iM25'}[(corp, ym)]))
    os.makedirs(os.path.dirname(OUT_CHK), exist_ok=True)
    with open(OUT_CHK, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CHK_COLS)
        w.writeheader()
        w.writerows(chk)
    # 문서 목록
    docs = []
    for key in SRC:
        s = source(key)
        if s['kind'] == 'xml':
            docs.append(dict(doc_kind=s['doc_kind'], corp_label=s['corp'], fy_or_date=s['fy'], report_nm=s['doc_name'],
                             rcept_no_or_url=s['rcept'], rcept_dt=s['rcept_dt'], raw_path=s['raw_path'], sha256=s['sha256'], fetched_at=s['collected_at'],
                             text_path=s['rel'], status='받음', note='OpenDART document(이번 작업에서 받음), XML → md'))
        else:
            docs.append(dict(doc_kind=s['doc_kind'], corp_label=s['corp'], fy_or_date=s['fy'], report_nm=s['doc_name'], rcept_no_or_url=s['url'],
                             rcept_dt=s['rcept_dt'], raw_path=s['raw_path'], sha256=s['sha256'], fetched_at=s['collected_at'], text_path=s['rel'],
                             status='받음', note=s['note_src'] + ' — 기존 글 재사용(이 작업은 웹 수집 안 함)' +
                             ('; 같은 검색어로 찾기만 함(행 없음 — 같은 해 다른 공시유형 글로 행을 만듦)' if key in SEARCH_ONLY else '')))
    for x in GOV_OLD:
        if x['corp_label'] == 'KB금융지주' and x['fy_or_date'] in ('FY2014', 'FY2015', 'FY2016'):
            docs.append(dict(doc_kind=GOV, corp_label=x['corp_label'], fy_or_date=x['fy_or_date'], report_nm=x['report_nm'], rcept_no_or_url=x['rcept_no_or_url'],
                             rcept_dt=x['rcept_dt'], raw_path='', sha256='', fetched_at='', text_path='', status='실패',
                             note='gov_old 문서목록 status 실패(목록 경로 200·6바이트 PDF 아님, 게시판 내려받기 HTTP 500) — 이 작업은 다시 받지 않음'))
    for label, (cc, pat) in LIST_SPEC.items():
        seen, metas = list_rows(cc, pat)
        fetched = max((to_kst(m.get('fetched_at', '')) for m in metas), default='')
        new = '이번 작업에서 새로 부름' if label == 'BNK금융지주' else '캐시 재사용'
        docs.append(dict(doc_kind='OpenDART 공시목록(list.json)', corp_label=label, fy_or_date=f'{pat[:8]}~{pat[9:]}', report_nm=f'공시목록 {len(seen)}건',
                         rcept_no_or_url=f'list.json corp_code={cc} bgn_de={pat[:8]} end_de={pat[9:]}', rcept_dt='',
                         raw_path=f'dart_out/raw/list/{cc}_{pat}_p*.json', sha256='', fetched_at=fetched, text_path='', status='받음', note=new))
    with open(OUT_DOCS, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=DOC_COLS)
        w.writeheader()
        w.writerows(docs)
    print('확인_I 행', len(chk), '문서목록 행', len(docs))


# ── 만들기 ────────────────────────────────────────────────────────────────
def topic_of(text):
    if '분리' in text:
        return '분리'
    if re.search(r'겸직|겸임|兼', text):
        return '겸직 결정'
    return ''


def build():
    rows, md_pages, used = [], {}, {}
    errors = []
    for sp in SPECS:
        s = source(sp['key'])
        fy = sp.get('fy') or s['fy']
        if sp['kind'] == 'NA':
            rows.append(dict(corp_label=s['corp'], fy_or_date=fy, topic=sp['topic'], source_text='문서에 없음', doc_kind=s['doc_kind'],
                             rcept_no_or_url=s['url'], page=na_page(sp['key']), note=sp['note'] + f'. 출처 글: {s["note_src"]}', doc_name=s['doc_name'],
                             collected_at=s['collected_at'], _rid=sp['rid']))
            used.setdefault(sp['key'], set())
            continue
        try:
            text, names, ctrl = cut(sp['key'], sp['start'], sp['end'], sp.get('after'), sp.get('first', False))
        except ValueError as e:
            errors.append(f'{sp["rid"]}: {e}')
            continue
        topic = sp['topic'] or topic_of(text)
        if not topic:
            errors.append(f'{sp["rid"]}: topic 못 정함')
            continue
        page = page_label(sp['key'], names, sp.get('extra_page', ''))
        note = sp['note'] + ('. 제어문자 지움(출처 글의 \\x01)' if ctrl else '') + f'. 출처 글: {s["note_src"]}'
        rows.append(dict(corp_label=s['corp'], fy_or_date=fy, topic=topic, source_text=text, doc_kind=s['doc_kind'],
                         rcept_no_or_url=s['url'], page=page, note=note, doc_name=s['doc_name'], collected_at=s['collected_at'], _rid=sp['rid']))
        used.setdefault(sp['key'], set()).update(names)
    if errors:
        print('\n'.join(errors))
        raise SystemExit('행 만들기 실패 %d' % len(errors))
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    # 원문 md — 행이 나온 쪽·절·섹션 글 전체(같은 쪽은 한 번)
    os.makedirs(OUT_MD_DIR, exist_ok=True)
    for key, names in used.items():
        if not names:
            continue
        s = source(key)
        clean, segs = load_text(key)
        tag = {'pdf': '연차보고서', 'kit56': '연차보고서6차섹션', 'xml': '주요경영사항'}[s['kind']]
        base = os.path.splitext(os.path.basename(s['rel']))[0] if s['kind'] != 'kit56' else f'{s["corp"]}__{s["fy"]}'
        sub = base.split('__')[-1] if s['kind'] == 'pdf' and base.split('__')[-1] in ('추가공시', '정정공시', '본공시') else ''
        fn = f'{s["corp"]}__{s["fy"]}__{tag}{("_" + sub) if sub else ""}{("_" + s["rcept"]) if s["kind"] == "xml" else ""}.md'
        out = [f'# {s["corp"]} {s["fy"]} {s["doc_kind"]} — 작업 I 원문(행이 나온 쪽·절 전체)', '',
               f'- 문서: {s["doc_name"] or s["doc_kind"]}', f'- 출처: {s["url"]}', f'- 글: {s["rel"]} ({s["note_src"]})',
               f'- 받은 시각: {s["collected_at"]}', f'- sha256: {s["sha256"]}', '']
        for p0, nm, body in segs:
            if nm in names:
                out += [f'## {nm}', '', body.strip('\n'), '']
        with open(os.path.join(OUT_MD_DIR, fn), 'w', encoding='utf-8') as f:
            f.write('\n'.join(out) + '\n')
    return rows


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if cmd in ('fetch-list', 'fetch-doc'):
        from client import DartClient
        c = DartClient(J('dart_out'), delay=0.5, max_calls=40)
        if cmd == 'fetch-list':
            page = 1
            while True:
                r = c.call('list', dict(corp_code='00858364', bgn_de='20170101', end_de='20171231', page_no=page, page_count=100), phase='ops15b_I')
                d = r.data or {}
                print('list p', page, r.status, d.get('total_count'), r.raw_path)
                if not d or page >= int(d.get('total_page') or 1):
                    break
                page += 1
        else:
            for rc in sys.argv[2:]:
                r = c.call('document', dict(rcept_no=rc), phase='ops15b_I')
                print('doc', rc, r.status, r.raw_path, r.fetched_at)
    else:
        rows = build()
        write_check_and_docs(rows)
        print('I.csv 행', len(rows), '문서에 없음', sum(r['source_text'] == '문서에 없음' for r in rows))
