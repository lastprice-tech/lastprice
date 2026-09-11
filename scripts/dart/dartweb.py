# -*- coding: utf-8 -*-
"""dart.fss.or.kr 웹 원본·첨부 수집기.

OpenDART 의 document.xml 로는 첨부서류를 한 건도 받을 수 없다. 실측으로 32건을 전수
조사했더니 ZIP 멤버가 전부 본문 XML 1개뿐이었다 — 정관·이사회의사록·평가의견서는
웹(dart.fss.or.kr)에만 있다. 게다가 OpenDART 가 `014 파일이 존재하지 않습니다` 로
거부한 우리은행 2018 정정 8건은 웹 뷰어로만 본문을 받을 수 있다(실측:
rcpNo=20181115000213). API 구멍을 메우는 유일한 경로다. 단 뷰어는 문서 전체가
아니라 목차 노드 하나씩만 주므로 목차를 전부 받아 이어 붙여야 한다 — 같은 문서도
첫 목차만 받으면 1,147,782바이트(전체 9,946,175바이트 중 12%)에서 끝난다.

client.DartClient 를 쓰지 않는다. 상대가 OpenDART 가 아니라 웹이라 쿼터 원장·키
마스킹은 필요 없는 대신 Referer·cp949 헤더 같은 웹 전용 규율이 붙는다. 그래도
원자적 쓰기·sha256·재실행 가능성·"실패는 삭제가 아니라 기록" 은 client.py 와 똑같이
지킨다.
"""
from __future__ import annotations

import csv
import hashlib
import html as _html
import json
import os
import random
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import config
import docparse

KST = timezone(timedelta(hours=9), "KST")

# User-Agent 는 사람 흉내를 내지 않는다(Mozilla/5.0 위장 금지). 다만 DART 앞단 WAF 가
# UA 문자열에 "collector" 또는 "bot" 이 들어가면 TLS 연결을 그냥 끊어버린다 — 실측:
#   "dart-benchmark-collector/1.0" → 빈 응답(0바이트), "dart-benchmark-research/1.0" → 200 98,488바이트
#   "xyz-collector/1.0" → 0, "dart-benchmark-bot/1.0" → 0,
#   "dart-benchmark-crawler/1.0"·"...scraper/1.0"·"...spider/1.0" → 전부 200
# 차단되는 낱말만 피하고 정체는 그대로 밝힌다.
UA = "dart-benchmark-research/1.0 (research; contact via repo)"

BASE = "https://dart.fss.or.kr"
MAIN_URL = BASE + "/dsaf001/main.do?rcpNo=%s"
VIEWER_URL = BASE + "/report/viewer.do?%s"
PDF_URL = BASE + "/pdf/download/pdf.do?rcp_no=%s&dcm_no=%s"
# Referer 가 없으면 0바이트가 온다(실측: 국민 2008 정관 193,350 → 0). 필수다.
PDF_REFERER = BASE + "/pdf/download/main.do?rcp_no=%s&dcm_no=%s&lang=ko"

# 재시도는 최대 4회에서 끊는다. 네트워크·5xx 만 재시도하고 4xx 는 즉시 실패.
BACKOFF = (2, 4, 8, 16)
DEFAULT_DELAY = 0.5
DEFAULT_TIMEOUT = 180
DEFAULT_SIZE_LIMIT = 500 * 1024 * 1024

# 뷰어 HTML 수집 규약의 판. 규약이 바뀌면(=예전 파일이 잘렸거나 깨졌으면) sha256 이
# 맞아도 캐시를 한 번 미스로 봐야 한다. 그러지 않으면 캐시가 잘못 받은 파일을 영원히
# 붙든다. 1=목차 첫 노드만, 2=목차 전체, 3=목차 인자로만 요청(eleId=0 모지바케 회피).
VIEWER_RULE = 3

# 뷰어가 본문 대신 빈 껍데기를 주는 경계. 이보다 작으면 재시도 사다리를 탄다
# (첨부 자신의 viewDoc 인자 → 본문 dtd). 실측상 실패는 전부 정확히 0바이트였다.
MIN_VIEWER_BYTES = 200

# config.DOC_PURPOSE 가 아직 없을 때만 쓰는 폴백. 정본은 config 다.
FALLBACK_RCEPT_NOS = [
    "20101210000020", "20181108000394", "20181115000213", "20181115000214",
    "20181115000215", "20181115000218", "20181115000219", "20181115000220",
    "20181121000024", "20181126000093", "20221121000209", "20221130001841",
    "20221205000327", "20221220000012", "20230102000239", "20230119000440",
    "20230206000364",
    "20040412001121", "20040511001085", "20050729000361", "20050812000924",
    "20050826000278", "20051004000194", "20051111000534", "20051027000163",
    "20051130000204", "20061103000215", "20061109000245", "20061123000185",
    "20080430001516", "20080716000002", "20080717000216",
]

# rows 의 컬럼. handoff.py 가 이 이름을 그대로 쓰므로 순서·철자를 바꾸지 마라.
ROW_FIELDS = [
    "rcept_no", "corp_label", "rcept_dt", "doc_kind", "doc_purpose",
    "파일종류", "문서종류", "정관판별근거", "원파일명", "저장경로", "바이트",
    "sha256", "수령성공여부", "실패사유", "fetched_at", "source_url", "dcm_no",
]

# ── 목록 파싱 정규식 ──────────────────────────────────────────────────────
# 실측 예: ("20181115000213","6386125","1","843","1212137","dart3.xsd")
VIEWDOC_RE = re.compile(
    r'viewDoc\("(\d+)",\s*"(\d+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"')
ATTACH_MARK = "+첨부선택+"
TAG_RE = re.compile(r"<[^>]+>")

# ── 목차(jsTree treeData) ─────────────────────────────────────────────────
# ★ 뷰어는 '문서 전체'가 아니라 '목차 노드 하나'를 돌려준다. main.do 가 마지막에
# 부르는 viewDoc(...) 은 그 문서의 첫 노드일 뿐이라, 그것만 받으면 문서 대부분이
# 조용히 사라진다. 실측:
#   20080430001516 본문 : 초기 viewDoc length=15,808(표지 1장) / 최상위 노드 3개 합 6,563,163
#                         → 그렇게 받아 둔 본문.html 은 10,670바이트, 문서의 0.16%였다.
#   같은 문서 감사보고서 첨부(dcmNo 1920272) : 초기 2,716 / 최상위 6개 합 458,545
#   20181115000213 본문 : 초기 1,212,137(정정표만) / 최상위 8개 합 9,946,175
# eleId=0&offset=0&length=0 으로 전체를 달라고 하면 0바이트가 온다(dart2·dart3 공통.
# DART 자신이 초기 인자로 0/0/0 을 쓰는 문서만 예외 — 그 문서는 0/0/0 이 곧 전체다).
# offset·length 는 무시되고 eleId 만 먹는다 — 실측: 19/980/2716 · 19/0/461396 ·
# 19/980/999999999 가 전부 같은 2,660바이트. 대신 부모 노드는 자식까지 통째로 준다
# (실측: eleId=5386 length=5,997,125 → 3,841,992바이트). 그래서 '최상위 노드 전부'를
# 받아 이어 붙이면 문서 전체가 된다. 32건 기준 본문 최상위 노드는 문서당 2~8개다.
TOC_BLOCK_RE = re.compile(
    r"var node(\d+) = \{\};(.*?)(?=var node\d+ = \{\};|treeData\.push|$)", re.S)
# 값은 소스에서 항상 큰따옴표다(node1['length'] = "550230";). 제목에 따옴표가 섞여도
# 숫자 필드는 다치지 않게 큰따옴표 짝으로만 읽는다.
TOC_FIELD_RE = re.compile(r"""node\d+\['(\w+)'\]\s*=\s*"([^"]*)"\s*;""")
# 이어 붙인 부분의 경계. 우리가 끼워 넣는 유일한 바이트라 눈에 띄게 표시하고,
# 각 부분의 시작바이트·길이를 인덱스에 남겨 원본을 정확히 다시 잘라낼 수 있게 한다.
PART_SEP = "\n<!-- dartweb:목차 %d/%d eleId=%s %s -->\n"


class WebFetchError(RuntimeError):
    """이 한 건의 요청이 끝내 실패했다. 실행 전체를 죽이지 않는다."""


def now_kst() -> datetime:
    return datetime.now(KST)


def ts_kst() -> str:
    """timezone-aware ISO-8601. client.ts_kst 와 같은 표기를 쓴다."""
    return now_kst().isoformat(timespec="seconds")


# ── 전송 ──────────────────────────────────────────────────────────────────
def _ssl_context():
    """client.py:126 과 같은 방식. TLS 검증은 절대 끄지 않는다."""
    ctx = ssl.create_default_context()
    cab = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    if os.path.exists(cab):
        try:
            ctx.load_verify_locations(cab)
        except Exception:
            pass
    return ctx


class WebSession:
    """요청 간 간격·재시도·TLS 를 한곳에 모은다. 모든 웹 접근은 여기만 통과한다."""

    def __init__(self, delay=DEFAULT_DELAY, timeout=DEFAULT_TIMEOUT, log=print):
        self.delay = delay
        self.timeout = timeout
        self.log = log
        self.ctx = _ssl_context()
        self.requests = 0
        self.elapsed = 0.0
        self._last = 0.0

    def _throttle(self):
        gap = time.monotonic() - self._last
        wait = self.delay - gap
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.15))   # 최소 간격 + 지터
        self._last = time.monotonic()

    def get(self, url, referer=None, timeout=None):
        """(http_status, body, headers, attempts). 끝내 실패하면 WebFetchError."""
        headers = {"User-Agent": UA}
        if referer:
            headers["Referer"] = referer
        last = ""
        attempt = 0
        for attempt in range(1, len(BACKOFF) + 2):      # 최초 1회 + 재시도 4회
            self._throttle()
            t0 = time.time()
            try:
                req = urllib.request.Request(url, headers=headers)
                self.requests += 1
                with urllib.request.urlopen(req, timeout=timeout or self.timeout,
                                            context=self.ctx) as r:
                    body = r.read()
                    hdrs = dict(r.headers)
                    code = r.getcode()
                self.elapsed += time.time() - t0
                clen = hdrs.get("Content-Length")
                if clen and int(clen) != len(body):
                    raise urllib.error.URLError(
                        "Content-Length %s != 수신 %d (전송 중단)" % (clen, len(body)))
                return code, body, hdrs, attempt
            except urllib.error.HTTPError as e:
                last = "HTTP %s %s" % (e.code, e.reason)
                if e.code and 400 <= e.code < 500 and e.code != 429:
                    raise WebFetchError(last + " (재시도 불가)")
            except Exception as e:
                # dart.fss.or.kr 은 간헐적으로 TLS 핸드셰이크를 끊는다
                # (실측: SSLEOFError UNEXPECTED_EOF_WHILE_READING). 재시도로 복구된다.
                last = "%s: %s" % (type(e).__name__, e)
            if attempt <= len(BACKOFF):
                time.sleep(BACKOFF[attempt - 1] + random.random())
        raise WebFetchError("전송 실패 %d회: %s" % (attempt, last))


# ── 목록(main.do) ─────────────────────────────────────────────────────────
def _clean_option_text(s: str) -> str:
    """태그 제거 + 언이스케이프 + 공백 정규화. 예: '2008.05.02 [추가] 정관'"""
    s = TAG_RE.sub("", s)
    return re.sub(r"\s+", " ", _html.unescape(s)).strip()


def parse_main(rcept_no: str, body: bytes):
    """(본문 viewDoc 인자 dict|None, [(dcm_no, 첨부명), ...])

    ★ 각 option 이 HTML 상 정확히 2회 중복 등장한다(실측: 국민 2008 → option 82개,
    고유 dcmNo 41개). dcmNo 로 dedupe 하지 않으면 건수가 통째로 2배가 된다.
    """
    text = body.decode("utf-8", "replace")
    m = VIEWDOC_RE.search(text)
    main_args = None
    if m:
        main_args = dict(rcpNo=m.group(1), dcmNo=m.group(2), eleId=m.group(3),
                         offset=m.group(4), length=m.group(5), dtd=m.group(6))
    parts = text.split(ATTACH_MARK)
    tail = parts[-1] if len(parts) > 1 else ""
    opt_re = re.compile(
        r'<option value="rcpNo=%s&amp;dcmNo=(\d+)"[^>]*>(.*?)</option>'
        % re.escape(rcept_no), re.S)
    seen = {}
    order = []
    for dcm, raw in opt_re.findall(tail):
        if dcm in seen:
            continue
        seen[dcm] = _clean_option_text(raw)
        order.append(dcm)
    return main_args, [(d, seen[d]) for d in order]


def foreign_attachments(rcept_no: str, body: bytes) -> dict:
    """이 페이지에 실린 '남의 접수번호 소유' 첨부 → {rcpNo: 고유건수}.

    ★ main.do 는 그 정정 묶음 전체의 첨부를 보여 주고, option value 의 rcpNo 가
    소유자다. 2000년대 정정 신고서 9건은 자기 소유 첨부가 0건이고 원 접수번호가
    전부 갖고 있다(실측: 20080716000002 → 20080430001516 이 41건 소유).
    32건 전체로 보면 소유자별 합계 212건에서 소유자가 둘인 10건을 빼 고유 202건이고,
    그 202건이 빠짐없이 어느 한 접수번호에 잡힌다 — 그래서 여기서 남의 것을 또
    받지는 않는다. 다만 '첨부 0건'이 아무 설명 없는 0 으로 보이지 않게 사유로 남긴다.
    """
    text = body.decode("utf-8", "replace")
    parts = text.split(ATTACH_MARK)
    tail = parts[-1] if len(parts) > 1 else ""
    out = {}
    for owner, dcm in re.findall(
            r'<option value="rcpNo=(\d+)&amp;dcmNo=(\d+)"', tail):
        if owner == rcept_no:
            continue
        out.setdefault(owner, set()).add(dcm)
    return {k: len(v) for k, v in sorted(out.items())}


def toc_nodes(text: str, dcm_no: str):
    """main.do 의 treeData 에서 이 dcmNo 의 '최상위' 목차 노드를 문서 순서대로.

    최상위는 변수 이름의 깊이가 1(node1)인 것이다 — node1 은 treeData 에, node2
    이하는 부모의 children 에 들어간다. 부모가 자식을 다 품고 오므로 최상위만 받으면
    문서 전체가 된다(모듈 상단 TOC 주석의 실측 참조).
    """
    out = []
    for depth, blk in TOC_BLOCK_RE.findall(text or ""):
        if depth != "1":
            continue
        d = dict(TOC_FIELD_RE.findall(blk))
        if d.get("dcmNo") != str(dcm_no):
            continue
        # 요청 인자가 빠진 노드도 버리지 않고 표시만 해서 넘긴다. 조용히 빼면 그 목차의
        # 분량이 통째로 사라지는데 '목차 3/3 성공'으로 보여 아무도 눈치채지 못한다.
        if not all(k in d for k in ("eleId", "offset", "length")):
            d = dict(d, 인자없음="1")
        out.append(d)
    return out


def viewdoc_args(text: str):
    """viewDoc("...") 인자 dict. 없으면 None — 지어내지 않는다."""
    m = VIEWDOC_RE.search(text or "")
    if not m:
        return None
    return dict(rcpNo=m.group(1), dcmNo=m.group(2), eleId=m.group(3),
                offset=m.group(4), length=m.group(5), dtd=m.group(6))


def viewer_parts(text: str, args: dict):
    """이어 붙여 받을 (제목, 뷰어 URL) 목록. 나눠 받을 필요가 없으면 빈 목록.

    ★ 목차가 1개뿐이어도, 그리고 초기 인자가 0/0/0 이어도 목차 인자로 받는다.
    예전에는 이 둘을 "한 번에 받으면 되는 경우"로 보고 eleId=0 요청을 그대로 썼는데,
    eleId=0 은 같은 내용을 '깨진 인코딩'으로 돌려준다. 실측(20080430001516 첨부
    dcmNo=1920273, 2008년 cp949 문서):
      eleId=0&offset=0&length=0   → 45,704바이트 · U+FFFD 10,754개 (한글 전멸)
      eleId=10&offset=413&length=16318 → 32,051바이트 · U+FFFD 0개
      ("제 1 조 회사명 … 케이비투자증권주식회사라 하고" 가 그대로 읽힌다)
    dart2/dart3/빈 dtd 모두 eleId=0 이면 똑같이 깨진다 — 즉 서버가 깨뜨려 보낸 것이
    아니라 우리가 깨지는 경로로 부른 것이다. 같은 문서의 첨부 41건 중 16건(정관 8 +
    이사회의사록 8)이 이 경로로 저장돼 있었고 전부 '성공' 으로 적혀 있었다.
    0/0/0 이 문서 전체를 주는 것은 맞다(실측: 20181115000214 → 588,441바이트 ≈ 목차
    2개 합 588,932). 양이 아니라 인코딩이 문제라, 양이 같아도 목차 인자로 받는다.

    - 목차를 하나도 못 찾은 문서만 초기 인자로 한 번에 받는다(기존 단일 요청 경로).
    - 목차가 1개이고 그 인자가 초기 인자와 같으면 나눌 것이 없으므로 역시 단일 경로다.
    """
    if not args:
        return []
    nodes = toc_nodes(text, args.get("dcmNo", ""))
    if not nodes:
        return []
    if (len(nodes) == 1 and not nodes[0].get("인자없음") and all(
            (nodes[0].get(k) or "") == (args.get(k) or "") for k in ("eleId", "offset", "length"))):
        return []
    parts = []
    for n in nodes:
        title = " ".join((n.get("text") or "").split())
        if n.get("인자없음"):
            # URL 을 만들 수 없다. 빈 URL 로 넘겨 _fetch_viewer 가 '못 받은 목차'로
            # 세게 한다 — 목록에서 빼 버리면 분량이 준 것을 알 길이 없다.
            parts.append((title, ""))
            continue
        q = dict(rcpNo=n.get("rcpNo") or args.get("rcpNo", ""), dcmNo=n["dcmNo"],
                 eleId=n["eleId"], offset=n["offset"], length=n["length"],
                 dtd=n.get("dtd") or args.get("dtd", ""))
        parts.append((title, VIEWER_URL % urllib.parse.urlencode(q)))
    return parts


def _ele_of(url: str) -> str:
    """뷰어 URL 에서 eleId 만. 경계 주석에 적어 어느 목차인지 남기려는 용도."""
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("eleId", [""])[0]


# ── 첨부 분류 ─────────────────────────────────────────────────────────────
# 사용자 지시 우선순위. 앞에 있을수록 먼저 받는다.
ATTACH_ORDER = ["정관", "이사회의사록", "주식이전(교환)계획서", "평가의견서",
                "예비투자설명서", "감사보고서", "그 외"]

# 용량이 한도의 90% 를 넘으면 이 계열부터 건너뛴다. 부피는 크고 지주 전환 서술과는
# 가장 먼 서류들이다.
BULK_KEYWORDS = ("감사보고서", "검토보고서", "재무제표")


def attachment_kind(name: str) -> str:
    """첨부명 문자열만 보고 문서종류를 정한다 — 파일 내용은 안 본다."""
    n = docparse.normalize_for_match(name)
    if "정관" in n:
        return "정관"
    if "이사회의사록" in n:
        return "이사회의사록"
    # '주식이전계획서'·'주식교환계획서'·'주식의포괄적이전계획서' 표기 변형을 모두 잡는다
    if "계획서" in n and any(k in n for k in ("주식이전", "주식교환", "주식의포괄적")):
        return "주식이전(교환)계획서"
    # "주식교환·이전비율평가의견서", "분석기관평가의견서" 등 변형이 있어 '평가의견' 으로 건다
    if "평가의견" in n:
        return "평가의견서"
    if "예비투자설명서" in n:
        return "예비투자설명서"
    if "감사보고서" in n:
        return "감사보고서"
    return "그 외"


def classify_attachment(name: str):
    """(우선순위, 문서종류). 우선순위는 ATTACH_ORDER 한 곳에서만 온다."""
    kind = attachment_kind(name)
    return ATTACH_ORDER.index(kind), kind


def is_bulk(name: str) -> bool:
    n = docparse.normalize_for_match(name)
    return any(k in n for k in BULK_KEYWORDS)


# ── 완전모회사 정관 구분 ──────────────────────────────────────────────────
# 지주 상호 판별은 낱말로 한다. config.TARGETS 의 group 으로 판별하면 한화생명보험이
# group="지주" 로 들어 있어(금융지주회사법상 지주회사가 아닌데도) 오탐이 난다.
# 낱말 규칙만으로 과제가 지목한 여섯 곳이 전부 걸린다:
#   KB금융지주 · 하나금융지주 · 우리금융지주 · 메리츠금융지주 · 한국투자금융지주 · 신한금융지주
HOLDING_WORDS = ("금융지주", "지주회사")

# 상호 꼬리표. 지주 낱말이 없으면서 이 낱말이 있으면 참여 자회사로 본다.
# (추정이 아니라 파일명·제1조에 실제로 적힌 상호를 읽은 것이다)
SUBSIDIARY_WORDS = ("은행", "증권", "생명", "화재", "손해보험", "보험", "카드",
                    "캐피탈", "자산운용", "투자신탁", "신탁", "저축은행", "선물")


_TARGET_NAMES = None


def _target_names():
    """config.TARGETS 의 label + aliases 를 긴 것부터. 정관 1건마다 부르므로 한 번만 만든다.

    긴 이름부터 보는 이유: '우리금융지주(구)' 처럼 짧은 이름을 품은 상호가 있어
    집합 순회 순서에 따라 다른 이름이 걸리면 같은 입력이 실행마다 달리 판정된다.
    """
    global _TARGET_NAMES
    if _TARGET_NAMES is None:
        out = set()
        for t in getattr(config, "TARGETS", []):
            for nm in [t.get("label", "")] + list(t.get("aliases") or []):
                nm = docparse.normalize_for_match(nm)
                if nm:
                    out.add(nm)
        _TARGET_NAMES = sorted(out, key=len, reverse=True)
    return _TARGET_NAMES


def _company_verdict(text: str):
    """상호 문자열 → '지주'|'자회사'|'' (판단 불가)."""
    n = docparse.normalize_for_match(text)
    if not n:
        return ""
    if any(w in n for w in HOLDING_WORDS):
        return "지주"
    hit = next((nm for nm in _target_names() if nm in n), "")
    if hit:
        return "지주" if any(w in hit for w in HOLDING_WORDS) else "자회사"
    if any(w in n for w in SUBSIDIARY_WORDS):
        return "자회사"
    return ""


# 맨 앞에 연달아 붙는 대괄호 묶음. DART 가 붙이는 이 자리는 '제출인'이지 서류의 주체가 아니다.
FILER_BRACKET_RE = re.compile(r"^\s*(?:\[[^\]]*\]\s*)+")

# 「제1조」의 표제는 '상호' 하나가 아니다. 국민은행 2008 첨부 정관 8건만 봐도
# 세 가지 표기가 나온다(전부 실측):
#   "제 1 조 회사명 회사명은 케이비투자증권주식회사라 하고…"   → 회사명
#   "제 1 조(회사의 상호) 이 회사는 "케이비창업투자 주식회사"라 한다" → 회사의 상호
#   "제1조 (상호) 이 회사는 …"                                  → 상호
# '상호' 만 찾으면 이런 정관은 조문을 한 줄도 못 읽고 '미상' 으로 떨어진다.
ART1_RE = re.compile(
    r"제\s*1\s*조\s*[\(（\[【]?\s*(?:회\s*사\s*의\s*|본\s*회\s*사\s*의\s*)?"
    r"(?:상\s*호|회\s*사\s*명|명\s*칭|商\s*號)\s*[\)）\]】]?")
# 제1조 본문을 어디서 끊을지. 제2조부터는 '목적' 조항이라 "금융지주회사법상의 자회사"
# 같은 문구가 섞여 든다 — 그대로 두면 자회사 정관이 '지주' 로 뒤집힌다(실측: 메리츠
# 금융지주 정관 제1조 본문 130자 뒤에 "자회사등(금융지주회사법상의…" 이 나온다).
ART1_END_RE = re.compile(r"제\s*2\s*조|부\s*칙")


def filename_subject(filename: str) -> str:
    """원 파일명에서 제출인 대괄호를 걷어낸 나머지. 상호 증거로 쓸 수 있는 부분만 남긴다.

    ★ 파일명 맨 앞 대괄호는 서류의 주체가 아니라 제출인이다. 실측(국민은행 2008,
    첨부 41건): 정관·이사회의사록·감사보고서 가릴 것 없이 전부 '[국민은행]…' 으로
    내려오고, 서로 다른 8개 회사의 정관(뷰어 HTML 크기 45,704/23,858/21,801/29,621/
    34,485/41,556/26,542/58,245바이트로 전부 다르다)이 모두 같은 이름을 단다.
    이 대괄호를 상호 근거로 쓰면 새로 세우는 KB금융지주의 정관까지 '자회사 정관'으로
    잘못 찍힌다 — 지어낸 값이 된다. 그래서 걷어내고 나머지만 본다.
    """
    return FILER_BRACKET_RE.sub("", filename or "")


def article1_companies(text: str, limit: int = 0):
    """뷰어 HTML 안의 「제1조 (상호)」 조문 본문들. 없으면 빈 목록.

    실측: 메리츠금융지주 2022 정관 → "제1조 (상호) 이 회사는 주식회사 메리츠금융지주라 한다."

    ★ 하나만 찾고 끝내지 않는다. 정관 첨부는 '파일 1개 = 회사 1개'가 아니다(스캔
    묶음에서 실제로 6개사가 한 파일에 들어 있었다 — embedded_image_names 주석 참조).
    글자로 된 묶음이라면 제1조가 여러 번 나오고, 첫 번째만 보면 파일 전체가 그 회사
    것으로 찍힌다. 그것은 읽어서 안 값이 아니라 지어낸 값이다. 그래서 전부 모아
    호출부가 '전원이 같은 쪽일 때만' 찍게 한다.
    앞 20,000자만 보던 제한도 없앴다 — 목차 전체를 이어 붙이면서 표지가 앞에 붙어
    제1조가 그 뒤로 밀릴 수 있기 때문이다.
    """
    plain = re.sub(r"\s+", " ", _html.unescape(TAG_RE.sub(" ", text or "")))
    out = []
    for m in ART1_RE.finditer(plain):
        seg = plain[m.end():m.end() + 200]
        cut = ART1_END_RE.search(seg)      # 제2조(목적)·부칙이 섞여 들지 않게 끊는다
        out.append((seg[:cut.start()] if cut else seg).strip())
        if limit and len(out) >= limit:    # limit=0 이면 상한 없음 — 조문을 세다 말지 않는다
            break
    return out


def article1_company(text: str) -> str:
    """첫 「제1조 (상호)」 조문 본문. 없으면 빈 문자열. (현재 호출부 없음 — 진단용)"""
    arts = article1_companies(text, limit=1)
    return arts[0] if arts else ""


IMG_ALT_RE = re.compile(r'alt="이미지:\s*([^"]+)"')
IMG_DOC_NAME_RE = re.compile(r"^\s*\d+[.\-_]\s*(.+?)_정관")


def embedded_image_names(text: str):
    """스캔 이미지로 제출된 첨부의 원본 이미지 파일명들.

    실측(우리은행 2018 정관, dcmNo=6374269): 뷰어 HTML 에 본문이 한 글자도 없고
    IMG 태그 목록뿐이다(전체 1,157자). alt 에 '1.우리은행_정관_1' 처럼 제출 당시
    파일명이 그대로 들어 있고, 그 한 파일에 6개사(우리은행·우리에프아이에스·
    우리금융경영연구소·우리신용정보·우리펀드서비스·우리프라이빗에퀴티자산운용)의
    정관이 함께 묶여 있었다. 정관이 '파일 1개 = 회사 1개' 가 아니라는 뜻이다.
    """
    return IMG_ALT_RE.findall(text or "")


def _image_bundle_verdict(viewer_text: str):
    """이미지 묶음 안의 회사들이 전부 같은 쪽일 때만 판정한다. (판정, 상호목록)

    한 파일에 지주와 자회사가 섞여 있으면 어느 쪽으로 찍어도 거짓이 된다 → 미분류.
    정확히는 '판정이 되는 상호들이 모두 같은 쪽일 때'다. 낱말 규칙으로 못 가리는
    상호(실측: 우리 2018 묶음의 우리에프아이에스·우리금융경영연구소·우리신용정보·
    우리펀드서비스)는 표결에서 빠진다 — 판정된 것이 하나도 없으면 그대로 미분류이고,
    빠진 상호도 상호목록에 남아 사람이 나중에 확인할 수 있다.
    """
    names, seen = [], set()
    for alt in embedded_image_names(viewer_text):
        m = IMG_DOC_NAME_RE.match(alt)
        nm = (m.group(1) if m else "").strip()
        if nm and nm not in seen:
            seen.add(nm)
            names.append(nm)
    verdicts = {_company_verdict(nm) for nm in names}
    verdicts.discard("")
    if len(verdicts) == 1:
        return verdicts.pop(), names
    return "", names


def classify_articles(filename: str, viewer_text: str):
    """정관 항목을 (문서종류, 정관판별근거, 상호단서) 로 나눈다.

    ① 원 파일명의 상호(제출인 대괄호는 제외) → ② 뷰어 HTML 제1조(상호) →
    ③ 스캔 첨부라면 이미지 파일명들(전부 같은 쪽일 때만) → ④ 미분류.
    ④ 를 추정으로 메우지 않는다. 상호단서는 근거로 쓰지 못한 상호까지 그대로 적어
    사람이 나중에 손으로 가를 수 있게 남기는 값이다.
    """
    def label(v):
        return "지주 정관" if v == "지주" else "자회사 정관"

    subject = filename_subject(filename)
    v = _company_verdict(subject)
    if v:
        return label(v), "파일명", subject.strip()

    arts = article1_companies(viewer_text or "")
    hint1 = " | ".join(" ".join(a.split())[:120] for a in arts)[:400]
    verdicts = {_company_verdict(a) for a in arts}
    verdicts.discard("")
    if len(verdicts) == 1:
        return label(verdicts.pop()), "제1조", hint1
    if len(verdicts) > 1:
        # 한 파일에 지주 정관과 자회사 정관이 같이 들어 있다. 어느 쪽으로 찍어도
        # 절반은 거짓이 된다 → 미분류로 두고 읽은 상호를 전부 남긴다.
        return "정관(미분류)", "제1조 혼재", hint1

    v, names = _image_bundle_verdict(viewer_text or "")
    hint = ", ".join(names)
    if v:
        return label(v), "이미지목록", hint
    if arts:
        # 상호는 읽었는데 낱말 규칙으로 지주/자회사를 못 가른 경우다(실측: 케이비신용정보·
        # 케이비데이타시스템·케이비창업투자). '미상'(한 글자도 못 읽음)과 같은 칸에 넣으면
        # 사람이 무엇을 손봐야 하는지 구별할 수 없다 — 읽은 상호는 상호단서에 그대로 있다.
        return "정관(미분류)", "제1조 판정불가", hint1
    return "정관(미분류)", "미상", hint1 or hint


# ── 파일명·쓰기 ───────────────────────────────────────────────────────────
# 파일 시스템 한 칸의 상한은 255바이트다. 한글은 UTF-8 로 3바이트라 85자면 찬다.
# 여기서는 앞의 2자리 순번("01_", 3바이트)과 원자적 쓰기의 ".part"(5바이트)까지
# 미리 빼고 240바이트를 예산으로 쓴다. 넘치면 open() 이 OSError 를 내고 collect
# 전체가 죽는다 — 한 건의 긴 이름이 32건 수집을 통째로 날리게 두지 않는다.
FS_NAME_BUDGET = 240


def sanitize_filename(name: str) -> str:
    """원 파일명은 경로 구분자와 NUL 만 바꾸고 나머지는 그대로 둔다.

    이름이 겹쳐도 앞에 2자리 순번이 붙으므로 충돌하지 않는다.
    상한을 넘는 이름만 확장자를 남기고 가운데를 잘라 줄인다. 자른 사실이 이름에
    드러나게 "~절단" 을 넣고, 원래 이름은 레코드의 원파일명에 그대로 남는다.
    """
    out = (name or "").replace("/", "_").replace("\\", "_").replace("\x00", "_")
    out = out.strip()
    if not out:
        return "무제"
    if len(out.encode("utf-8")) <= FS_NAME_BUDGET:
        return out
    stem, ext = os.path.splitext(out)
    ext = ext[:20]
    mark = "~절단"
    keep = FS_NAME_BUDGET - len((ext + mark).encode("utf-8"))
    stem = stem.encode("utf-8")[:max(keep, 1)].decode("utf-8", "ignore")
    return stem + mark + ext


def content_disposition_filename(headers: dict):
    """(원파일명, decode_ok|None). 헤더 자체가 없으면 ("", None).

    바이트가 cp949 인데 urllib 은 헤더를 latin-1 로 준다 → 되살려야 한다.
    실측: 'attachment;filename="[±¹¹ÎÀºÇà][Ãß°¡]Á¤°ü(2008.05.02).pdf";'
          → '[국민은행][추가]정관(2008.05.02).pdf'
    cp949 로 못 읽으면 utf-8 로 한 번 더 본다. 지금 DART 는 cp949 만 보내지만(실측
    119건 전부 cp949 성공), 헤더가 utf-8 로 바뀌면 cp949 디코드는 조용히 성공하는
    게 아니라 예외를 낸다(실측: utf-8 헤더 → UnicodeDecodeError) — 그래서 사다리를
    한 칸 두는 것이 안전하다. 둘 다 실패하면 원문자열을 그대로 두고 False 를
    돌려준다 — 지어내지 않는다.
    """
    cd = ""
    for k, v in (headers or {}).items():
        if k.lower() == "content-disposition":
            cd = v or ""
            break
    if not cd:
        return "", None
    m = re.search(r'filename\s*=\s*"([^"]*)"', cd) or re.search(r"filename\s*=\s*([^;\r\n]+)", cd)
    if not m:
        return "", None
    raw = m.group(1).strip()
    for enc in ("cp949", "utf-8"):
        try:
            return raw.encode("latin-1").decode(enc), True
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            continue
    return raw, False


def _atomic_write(path: str, data: bytes) -> str:
    """`.part` 로 쓰고 os.replace. 인덱스(사이드카)는 본체를 전부 옮긴 뒤에 쓴다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return hashlib.sha256(data).hexdigest()


def _rel(out_dir: str, path: str) -> str:
    return os.path.relpath(path, out_dir).replace(os.sep, "/")


# ── 대상·메타 ─────────────────────────────────────────────────────────────
def _purpose_str(v) -> str:
    if isinstance(v, dict):
        for k in ("purpose", "용도", "목적", "label"):
            if v.get(k):
                return str(v[k])
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return "" if v is None else str(v)


def doc_purposes() -> dict:
    """config.DOC_PURPOSE 가 정본. 아직 없으면(다른 에이전트가 작성 중) 폴백 목록을 쓴다."""
    v = getattr(config, "DOC_PURPOSE", None)
    if isinstance(v, dict) and v:
        return {str(k): _purpose_str(x) for k, x in v.items()}
    return {rc: "" for rc in FALLBACK_RCEPT_NOS}


def _targets(rcept_nos=None):
    purposes = doc_purposes()
    if rcept_nos:
        return [str(r) for r in rcept_nos]
    return list(purposes.keys())


def _doc_kind(report_nm: str) -> str:
    """원본 / 정정 / 첨부추가 / 발행조건확정.

    phase2.doc_kind 와 같은 규칙이고 판정표(config.DOC_KIND_PREFIX)도 공유한다.
    수집 모듈이 emit 까지 끌어오지 않으려고 네 줄만 여기에 둔다 — 규칙을 고칠 때는
    config.DOC_KIND_PREFIX 만 고쳐라.
    """
    nm = docparse.normalize_for_match(report_nm)
    for prefix, label in config.DOC_KIND_PREFIX.items():
        if nm.startswith(docparse.normalize_for_match(prefix)):
            return label
    return "원본"


def load_disclosure_index(out_dir: str) -> dict:
    """02_공시목록.csv → {rcept_no: {corp_label, rcept_dt, doc_kind}}"""
    p = os.path.join(out_dir, "02_공시목록.csv")
    out = {}
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rc = (r.get("rcept_no") or "").strip()
            if not rc or rc in out:
                continue
            out[rc] = {
                "corp_label": r.get("corp_label", ""),
                # corp_label 은 config.TARGETS 의 라벨이라 대상이 아닌 법인은 빈칸이다.
                # 원문 상호(corp_name)는 그 경우에도 CSV 에 있으니 같이 들고 온다.
                "corp_name": r.get("corp_name", ""),
                "rcept_dt": r.get("rcept_dt", ""),
                "doc_kind": _doc_kind(r.get("report_nm", "")),
                "report_nm": r.get("report_nm", ""),
            }
    return out


def load_raw_list_meta(out_dir: str, wanted) -> dict:
    """02_공시목록.csv 에 없는 접수번호만 raw/list/*.json 에서 되찾는다.

    ★ 2차 15건(2004~2008)은 02_공시목록.csv 에 한 줄도 없다. 그 CSV 가
    config.TARGETS 의 법인만 담는데 국민·하나·신한은행과 한국금융지주가 TARGETS 에
    없기 때문이다. 그런데 같은 접수번호가 우리가 이미 받아 둔 OpenDART list 응답
    원본(raw/list/*.json)에는 그대로 있다 — 실측 15/15 전부. 추정이 아니라 받아 둔
    응답을 읽는 것이라 여기서 채운다. 다만 출처가 다르므로 어느 파일에서 읽었는지를
    레코드에 '메타출처' 로 같이 남긴다.

    corp_label 은 config.TARGETS 의 라벨 어휘라, 그 법인이 TARGETS 에 없으면 값 자체가
    존재하지 않는다 — 지어내지 않고 빈칸으로 두고 원문 상호만 corp_name 에 적는다.
    """
    want = {str(w) for w in wanted}
    out = {}
    if not want:
        return out
    import glob as _glob
    for p in sorted(_glob.glob(os.path.join(out_dir, "raw", "list", "*.json"))):
        if not want:
            break
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue          # 깨진 캐시 한 장 때문에 나머지를 못 읽으면 안 된다
        for it in (d.get("list") or []):
            rc = str(it.get("rcept_no") or "")
            if rc not in want:
                continue
            want.discard(rc)
            out[rc] = {
                "corp_label": "",          # TARGETS 에 없는 법인 — 라벨이 존재하지 않는다
                "corp_name": str(it.get("corp_name") or ""),
                "corp_code": str(it.get("corp_code") or ""),
                "rcept_dt": str(it.get("rcept_dt") or ""),
                "report_nm": str(it.get("report_nm") or ""),
                "doc_kind": _doc_kind(str(it.get("report_nm") or "")),
                "메타출처": _rel(out_dir, p),
            }
    return out


def openapi_document_state(out_dir: str, rcept_no: str) -> dict:
    """raw/document/<rcept_no>.zip 과 그 사이드카의 상태. 여기로 본문 XML 을 가리킨다."""
    zp = os.path.join(out_dir, "raw", "document", rcept_no + ".zip")
    mp = zp + ".meta.json"
    st = {"경로": _rel(out_dir, zp), "존재": os.path.exists(zp),
          "openapi_status": "", "openapi_message": "", "바이트": 0, "sha256": "",
          "fetched_at": ""}
    if os.path.exists(mp):
        try:
            with open(mp, encoding="utf-8") as f:
                meta = json.load(f)
            st["openapi_status"] = str(meta.get("api_status") or "")
            st["openapi_message"] = str(meta.get("api_message") or "")
            st["fetched_at"] = str(meta.get("fetched_at") or "")
        except Exception:
            pass
    if st["존재"]:
        with open(zp, "rb") as f:
            data = f.read()
        st["바이트"] = len(data)
        st["sha256"] = hashlib.sha256(data).hexdigest()
    return st


# ── 인덱스(_파일목록.json) ────────────────────────────────────────────────
INDEX_NAME = "_파일목록.json"


def _doc_dir(out_dir: str, rcept_no: str) -> str:
    return os.path.join(out_dir, "doc", rcept_no)


def load_index(out_dir: str, rcept_no: str) -> dict:
    """이전 실행의 인덱스를 (파일종류, dcm_no) → 레코드 로 읽는다. 재실행 캐시의 근거."""
    p = os.path.join(_doc_dir(out_dir, rcept_no), INDEX_NAME)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return {}      # 깨진 인덱스는 캐시 미스로 본다 (삭제하지 않는다)
    out = {}
    for r in d.get("files") or []:
        out[(r.get("파일종류", ""), str(r.get("dcm_no", "")))] = r
    return out


def write_index(out_dir: str, rcept_no: str, header: dict, records: list):
    d = _doc_dir(out_dir, rcept_no)
    os.makedirs(d, exist_ok=True)
    payload = dict(header)
    payload["files"] = records
    p = os.path.join(d, INDEX_NAME)
    tmp = p + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    return p


def _cache_hit(out_dir: str, prev: dict, key, want_bytes=False, require_mode=False):
    """이미 받은 파일은 sha256 이 맞으면 재요청하지 않는다. (레코드, 바이트|None)"""
    rec = prev.get(key)
    if not rec or rec.get("수령성공여부") != "성공":
        return None, None
    # 예전 규약으로 받아 둔 뷰어 HTML 은 파일이 그대로 있어 sha256 은 맞지만 내용이
    # 잘렸거나(규약 1: 목차 첫 노드만) 깨져 있다(규약 2: eleId=0 요청이 준 U+FFFD 범벅).
    # 캐시가 그런 파일을 영원히 붙들지 않도록 규약이 낮으면 한 번은 미스로 본다.
    if require_mode and int(rec.get("수집규약") or 0) < VIEWER_RULE:
        return None, None
    rel = rec.get("저장경로") or ""
    if not rel:
        return None, None
    p = os.path.join(out_dir, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return None, None
    with open(p, "rb") as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != rec.get("sha256"):
        return None, None      # 내용이 달라졌다 — 다시 받는다
    return rec, (data if want_bytes else None)


# ── 레코드 만들기 ─────────────────────────────────────────────────────────
def _on_disk(out_dir: str, old) -> bool:
    """이전 기록이 가리키는 파일이 실제로 디스크에 있는가. 승계 판정의 유일한 기준."""
    rel = (old or {}).get("저장경로") or ""
    return bool(rel) and os.path.exists(os.path.join(out_dir, rel.replace("/", os.sep)))


def _record(base: dict, **kw) -> dict:
    r = dict(base)
    r.update(kw)
    return r


def _row(rec: dict) -> dict:
    """인덱스 레코드에서 원문_파일목록.csv 한 행을 뽑는다(추가 필드는 인덱스에만 남는다)."""
    return {k: rec.get(k, "") for k in ROW_FIELDS}


# 캐시에서 되살릴 값. corp_label·rcept_dt 같은 공시목록 메타는 일부러 빼 둔다 —
# 02_공시목록.csv 가 나중에 채워지면 재실행 때 갱신돼야 하기 때문이다.
CACHE_KEYS = (
    "파일종류", "문서종류", "정관판별근거", "원파일명", "저장경로", "바이트", "sha256",
    "수령성공여부", "fetched_at", "source_url", "dcm_no", "첨부명", "순번",
    "content_type", "encoding_declared", "encoding_used", "decode_replacements",
    "source_replacement_chars", "attempts", "filename_decode_ok", "viewer_recipe",
    "openapi_status", "openapi_message",
    "수집방식", "수집규약", "목차_노드수", "목차_수집수", "목차_노드", "첨부목록_오류",
)


def _reuse(base: dict, hit: dict) -> dict:
    """캐시 적중 레코드를 이번 실행의 메타 위에 다시 얹는다.

    실패사유는 비워서 시작한다 — 캐시 적중은 '성공'뿐이고, 공시목록 비고는
    add() 가 이번 실행 기준으로 다시 붙인다(그래야 같은 문구가 겹치지 않는다).
    """
    rec = dict(base)
    for k in CACHE_KEYS:
        if k in hit:
            rec[k] = hit[k]
    rec["실패사유"] = ""
    rec["캐시"] = True
    return rec


# ── plan ──────────────────────────────────────────────────────────────────
def plan(out_dir, rcept_nos=None):
    """드라이런. 네트워크는 목록(main.do)까지만 쓰고 파일은 받지 않는다.

    → dict(문서수, 첨부수, 예상요청수, 예상소요초, per_doc=[...])
    """
    out_dir = os.path.abspath(out_dir)
    targets = _targets(rcept_nos)
    purposes = doc_purposes()
    disc = load_disclosure_index(out_dir)
    raw_meta = load_raw_list_meta(out_dir, [t for t in targets if t not in disc])
    s = WebSession(delay=DEFAULT_DELAY)

    per_doc = []
    n_attach = 0
    n_body_parts = 0
    for rc in targets:
        _m = disc.get(rc) or raw_meta.get(rc) or {}
        row = {"rcept_no": rc, "corp_label": _m.get("corp_label", ""),
               "corp_name": _m.get("corp_name", ""), "rcept_dt": _m.get("rcept_dt", ""),
               "메타출처": ("02_공시목록.csv" if rc in disc else _m.get("메타출처", "")),
               "doc_purpose": purposes.get(rc, ""), "본문": False, "본문dtd": "",
               "본문목차수": 0, "첨부수": 0, "첨부": [], "첨부비고": "", "오류": ""}
        try:
            _, body, _, _ = s.get(MAIN_URL % rc)
        except WebFetchError as e:
            row["오류"] = str(e)
            per_doc.append(row)
            continue
        main_args, attaches = parse_main(rc, body)
        row["본문"] = bool(main_args)
        row["본문dtd"] = (main_args or {}).get("dtd", "")
        # 본문을 몇 번에 나눠 받아야 하는지는 여기서 이미 알 수 있다(목차가 main.do 안에 있다).
        row["본문목차수"] = max(1, len(viewer_parts(body.decode("utf-8", "replace"), main_args)))
        foreign = foreign_attachments(rc, body)
        if not attaches and foreign:
            row["첨부비고"] = ("이 접수번호 소유 첨부 0건 — 같은 묶음의 %s 이(가) 소유"
                             % ", ".join("%s %d건" % (k, v) for k, v in foreign.items()))
        ordered = sorted(range(len(attaches)),
                         key=lambda i: (classify_attachment(attaches[i][1])[0], i))
        row["첨부수"] = len(attaches)
        row["첨부"] = [{"dcm_no": attaches[i][0], "첨부명": attaches[i][1],
                        "문서종류": classify_attachment(attaches[i][1])[1]} for i in ordered]
        n_attach += len(attaches)
        n_body_parts += row["본문목차수"]
        per_doc.append(row)

    n_doc = len(targets)
    # collect() 가 쓸 요청 수: 목록 1 + 본문 목차부분 k + 본문PDF 1
    #   + 첨부마다 (그 첨부의 main.do 1 + 목차부분 k' + PDF 1).
    # k 는 여기서 실제로 세지만 k' 는 첨부의 main.do 를 받아야만 알 수 있어 1로 잡는다
    # → 이 값은 하한이다. 실측(5개 문서 · 첨부 114건 · 본문 목차 29부분):
    #   이 식은 381회를 내놓는데 실제로는 661회가 들었다(뷰어 542 + PDF 119).
    #   첨부 1건당 목차부분이 평균 3.46개라 k'=1 가정이 그만큼 모자란다 — 1.7배쯤
    #   더 든다고 보면 된다.
    est_req = n_doc + n_body_parts + n_doc + n_attach * 3
    avg = (s.elapsed / s.requests) if s.requests else 0.0
    # 측정값은 main.do(약 100KB) 왕복이라 PDF 가 섞인 실제 수집은 이보다 오래 걸린다.
    est_sec = est_req * (DEFAULT_DELAY + avg)
    return {"문서수": n_doc, "첨부수": n_attach, "본문목차부분수": n_body_parts,
            "예상요청수": est_req, "예상소요초": round(est_sec, 1),
            "평균응답초": round(avg, 3), "per_doc": per_doc}


# ── collect ───────────────────────────────────────────────────────────────
def collect(out_dir, rcept_nos=None, delay=DEFAULT_DELAY,
            size_limit_bytes=DEFAULT_SIZE_LIMIT, skip_pdf=False, log=print):
    """실제 수집. → dict(성공, 실패, 미수집, 누적바이트, 중단여부, rows=[...])"""
    out_dir = os.path.abspath(out_dir)
    targets = _targets(rcept_nos)
    purposes = doc_purposes()
    disc = load_disclosure_index(out_dir)
    raw_meta = load_raw_list_meta(out_dir, [t for t in targets if t not in disc])
    s = WebSession(delay=delay, log=log)

    state = {"bytes": 0, "aborted": False, "abort_reason": ""}
    soft_limit = int(size_limit_bytes * 0.9)
    rows = []
    n_ok = n_fail = n_skip = 0

    def account(nbytes):
        """받은 것도 캐시에서 재사용한 것도 모두 폴더 용량이다 — 같이 센다."""
        state["bytes"] += int(nbytes or 0)

    for rc in targets:
        if state["aborted"]:
            break
        meta = disc.get(rc) or {}
        alt = {} if meta else (raw_meta.get(rc) or {})
        src_meta = meta or alt
        base = {
            "rcept_no": rc,
            "corp_label": src_meta.get("corp_label", ""),
            "rcept_dt": src_meta.get("rcept_dt", ""),
            "doc_kind": src_meta.get("doc_kind", ""),
            "doc_purpose": purposes.get(rc, ""),
            "정관판별근거": "",
            # corp_label 이 빈칸인 법인(TARGETS 밖)도 상호는 있어야 누구 서류인지 안다.
            "corp_name": src_meta.get("corp_name", ""),
            # 어느 파일에서 읽은 메타인지. 02_공시목록.csv 에서 온 값과 원본 list 응답에서
            # 되찾은 값이 한 CSV 에 섞이므로 행마다 출처를 적는다.
            "메타출처": ("02_공시목록.csv" if meta else alt.get("메타출처", "")),
        }
        # 어느 쪽에도 없으면 지어내지 않는다 — 빈칸으로 두고 사유를 적는다.
        if meta:
            meta_note = ""
        elif alt:
            meta_note = ("02_공시목록.csv 에 rcept_no 없음 → rcept_dt·doc_kind·corp_name 은 "
                         "%s 에서 읽음; corp_label 은 config.TARGETS 에 그 법인이 없어 빈칸"
                         % alt.get("메타출처", "raw/list"))
        else:
            meta_note = "02_공시목록.csv 에 rcept_no 없음 → corp_label·rcept_dt·doc_kind 미상"

        doc_dir = _doc_dir(out_dir, rc)
        prev = load_index(out_dir, rc)
        records = []

        touched = set()

        def add(rec):
            key = (rec.get("파일종류", ""), str(rec.get("dcm_no", "")))
            # ★ 이번 실행이 실패·미수집으로 끝난 자리에 지난 실행이 받아 둔 파일이
            #   디스크에 그대로 있을 수 있다(캐시 규약이 올라가 미스가 났는데 재요청이
            #   끊긴 경우가 그렇다). 이 자리는 touched 에 들어가므로 아래 승계 루프가
            #   건너뛴다 — 그대로 두면 파일은 디스크에 있는데 인덱스·CSV 어디에도
            #   가리키는 줄이 없어진다. 지운 것과 구별되지 않으므로 자리를 남긴다.
            if rec.get("수령성공여부") not in ("성공", "부분수집"):
                old = prev.get(key)
                # 이번 레코드가 이미 같은 파일을 가리키고 있으면(본문XML 처럼 경로가
                # 늘 정해져 있는 경우) 같은 말을 두 번 적지 않는다.
                if (old and old.get("저장경로")
                        and old.get("저장경로") != rec.get("저장경로")
                        and _on_disk(out_dir, old)):
                    rec["이전파일_저장경로"] = old.get("저장경로", "")
                    rec["이전파일_바이트"] = old.get("바이트", 0)
                    rec["이전파일_sha256"] = old.get("sha256", "")
                    rec["이전파일_fetched_at"] = old.get("fetched_at", "")
                    rec["이전파일_수령성공여부"] = old.get("수령성공여부", "")
                    why0 = rec.get("실패사유") or ""
                    rec["실패사유"] = ((why0 + " / " if why0 else "")
                                     + "[이전 파일 있음] %s (%s바이트, %s) 는 디스크에 남아 있음"
                                     % (old.get("저장경로", ""), old.get("바이트", 0),
                                        old.get("수령성공여부", "")))
            why = rec.get("실패사유") or ""
            if meta_note and meta_note not in why:
                rec["실패사유"] = (why + " / " if why else "") + meta_note
            touched.add(key)
            records.append(rec)
            rows.append(_row(rec))
            return rec

        log("  [%s] %s %s" % (rc, base["corp_label"] or "(공시목록 없음)", base["doc_purpose"]))

        # ── 1) 본문 XML — 이미 raw/document 에 있다. 복사하지 않고 가리키기만 한다.
        st = openapi_document_state(out_dir, rc)
        if st["존재"] and st["openapi_status"] == "000":
            add(_record(base, 파일종류="본문XML", 문서종류="본문", 원파일명=os.path.basename(st["경로"]),
                        저장경로=st["경로"], 바이트=st["바이트"], sha256=st["sha256"],
                        수령성공여부="성공", 실패사유="", fetched_at=st["fetched_at"],
                        source_url="", dcm_no="",
                        openapi_status=st["openapi_status"], openapi_message=st["openapi_message"]))
            n_ok += 1
            account(st["바이트"])
        else:
            if st["openapi_status"]:
                why = "OpenAPI status %s: %s" % (st["openapi_status"], st["openapi_message"])
            elif st["존재"]:
                # ZIP 은 있는데 사이드카를 못 읽었다. "ZIP 이 없음" 이라고 적으면
                # 디스크에 있는 파일을 없다고 기록하는 셈이다.
                why = ("raw/document 에 ZIP 은 있으나 메타(api_status)를 읽지 못함: %s.meta.json"
                       % st["경로"])
            else:
                why = "raw/document 에 ZIP 이 없음(OpenAPI 미수집)"
            add(_record(base, 파일종류="본문XML", 문서종류="본문", 원파일명="",
                        저장경로=st["경로"] if st["존재"] else "", 바이트=st["바이트"],
                        sha256=st["sha256"], 수령성공여부="미수집", 실패사유=why,
                        fetched_at=st["fetched_at"], source_url="", dcm_no="",
                        openapi_status=st["openapi_status"], openapi_message=st["openapi_message"]))
            n_skip += 1

        # ── 2) 목록
        main_url = MAIN_URL % rc
        main_body = b""
        foreign = {}
        try:
            _, main_body, _, _ = s.get(main_url)
            main_args, attaches = parse_main(rc, main_body)
            foreign = foreign_attachments(rc, main_body)
            list_err = "" if main_args else "main.do 에서 viewDoc 인자를 찾지 못함"
        except WebFetchError as e:
            main_args, attaches, list_err = None, [], str(e)
        main_text = main_body.decode("utf-8", "replace") if main_body else ""

        # 자기 소유 첨부가 0건인데 같은 정정 묶음의 다른 접수번호가 갖고 있는 경우가
        # 있다(2000년대 정정 9건). 설명 없는 0 으로 두지 않고 사유를 남긴다.
        attach_note = ""
        if not attaches and foreign:
            attach_note = ("이 접수번호 소유 첨부 0건 — 같은 묶음의 %s 이(가) 소유"
                           % ", ".join("%s %d건" % (k, v) for k, v in foreign.items()))
        elif not attaches and main_text and ATTACH_MARK not in main_text:
            # 첨부 목록은 '+첨부선택+' 뒤쪽에서만 읽는다. 그 표지가 아예 없으면
            # '첨부가 없는 문서'와 '표지가 바뀌어 못 읽은 문서'가 똑같이 0건으로 보인다.
            # 실측 32건은 전부 표지를 갖고 있다 — 없으면 그것 자체가 이상 신호다.
            attach_note = ("첨부 선택 영역(%s)이 페이지에 없다 — 첨부가 없는 것인지 "
                           "목록을 못 읽은 것인지 확인 필요" % ATTACH_MARK)
        if list_err:
            log("      목록 실패: %s" % list_err)
        log("      첨부 고유 %d건%s" % (len(attaches), "  (%s)" % attach_note if attach_note else ""))

        # ── 3) 본문 HTML
        if main_args:
            url = VIEWER_URL % urllib.parse.urlencode(main_args)
            # 본문 목차는 방금 받은 main.do 안에 있다 — 추가 요청이 필요 없다.
            body_parts = viewer_parts(main_text, main_args)
            key = ("본문HTML", main_args["dcmNo"])
            hit, _ = _cache_hit(out_dir, prev, key, require_mode=True)
            if hit:
                add(_reuse(base, hit))
                n_ok += 1
                account(hit.get("바이트", 0))
            else:
                rec, _ = _fetch_viewer(s, base, out_dir, os.path.join(doc_dir, "본문.html"),
                                       url, 파일종류="본문HTML", 문서종류="본문",
                                       원파일명="", dcm_no=main_args["dcmNo"],
                                       parts=body_parts)
                add(rec)
                log("      본문 HTML %s %d바이트 (목차 %d/%d)"
                    % (rec["수령성공여부"], rec["바이트"],
                       rec.get("목차_수집수", 0), rec.get("목차_노드수", 0)))
                if rec["수령성공여부"] in ("성공", "부분수집"):
                    n_ok += 1
                    account(rec["바이트"])
                else:
                    n_fail += 1
                    log("      본문 HTML 실패: %s" % rec["실패사유"])
        else:
            add(_record(base, 파일종류="본문HTML", 문서종류="본문", 원파일명="", 저장경로="",
                        바이트=0, sha256="", 수령성공여부="실패", 실패사유=list_err,
                        fetched_at=ts_kst(), source_url=main_url, dcm_no=""))
            n_fail += 1

        # ── 4) 본문 PDF
        if main_args and not skip_pdf:
            key = ("본문PDF", main_args["dcmNo"])
            hit, _ = _cache_hit(out_dir, prev, key)
            if hit:
                add(_reuse(base, hit))
                n_ok += 1
                account(hit.get("바이트", 0))
            else:
                rec = _fetch_pdf(s, base, out_dir, doc_dir, rc, main_args["dcmNo"],
                                 파일종류="본문PDF", 문서종류="본문", fixed_name="본문.pdf")
                add(rec)
                if rec["수령성공여부"] == "성공":
                    n_ok += 1
                    account(rec["바이트"])
                else:
                    n_fail += 1
        elif main_args and skip_pdf:
            add(_record(base, 파일종류="본문PDF", 문서종류="본문", 원파일명="", 저장경로="",
                        바이트=0, sha256="", 수령성공여부="미수집", 실패사유="skip_pdf=True",
                        fetched_at="", source_url=PDF_URL % (rc, main_args["dcmNo"]),
                        dcm_no=main_args["dcmNo"]))
            n_skip += 1

        # ── 5) 첨부 — 우선순위로 정렬한 뒤 2자리 순번을 붙인다
        ordered = sorted(range(len(attaches)),
                         key=lambda i: (classify_attachment(attaches[i][1])[0], i))
        body_dtd = (main_args or {}).get("dtd", "")
        for seq, idx in enumerate(ordered, start=1):
            dcm, aname = attaches[idx]
            nn = "%02d" % seq
            _, kind = classify_attachment(aname)
            pdf_url = PDF_URL % (rc, dcm)
            view_args = dict(rcpNo=rc, dcmNo=dcm, eleId="0", offset="0", length="0",
                             dtd="dart3.dtd")
            view_url = VIEWER_URL % urllib.parse.urlencode(view_args)

            # 용량 한도 — 90% 를 넘으면 부피 큰 계열부터 건너뛴다(삭제가 아니라 기록).
            if state["bytes"] >= size_limit_bytes:
                state["aborted"] = True
                state["abort_reason"] = ("누적 %d바이트가 한도 %d 를 넘어 중단"
                                         % (state["bytes"], size_limit_bytes))
                log("      ✗ %s" % state["abort_reason"])
                # 남은 첨부를 '미수집'으로 적어 둔다. 적지 않으면 아직 한 번도 받은
                # 적 없는 첨부는 디스크에도 인덱스에도 없어 통째로 사라진다(승계는
                # 파일이 있는 것만 되살린다). 이미 받아 둔 것은 승계가 맡으므로 건드리지 않는다.
                for seq2, idx2 in list(enumerate(ordered, start=1))[seq - 1:]:
                    dcm2, aname2 = attaches[idx2]
                    _, kind2 = classify_attachment(aname2)
                    va2 = dict(rcpNo=rc, dcmNo=dcm2, eleId="0", offset="0",
                               length="0", dtd="dart3.dtd")
                    for 종류2, surl in (("첨부HTML", VIEWER_URL % urllib.parse.urlencode(va2)),
                                        ("첨부PDF", PDF_URL % (rc, dcm2))):
                        if _on_disk(out_dir, prev.get((종류2, dcm2))):
                            continue
                        r2 = _record(base, 파일종류=종류2, 문서종류=kind2, 원파일명="",
                                     저장경로="", 바이트=0, sha256="",
                                     수령성공여부="미수집", 실패사유=state["abort_reason"],
                                     fetched_at="", source_url=surl, dcm_no=dcm2)
                        r2["첨부명"] = aname2
                        r2["순번"] = "%02d" % seq2
                        add(r2)
                        n_skip += 1
                break
            bulk_skip = state["bytes"] >= soft_limit and is_bulk(aname)

            pdf_rec = html_rec = None
            pdf_name = ""

            # 캐시가 먼저다. 이미 받아 둔 것은 skip_pdf·용량제한과 무관하게 그대로 쓴다
            # (건너뛴다고 기록해 버리면 디스크에 있는 파일이 목록에서 사라진다).
            hit, _ = _cache_hit(out_dir, prev, ("첨부PDF", dcm))
            # 순번이 달라졌으면(첨부 목록이 바뀐 경우) 캐시 미스로 본다. 파일명 앞
            # 2자리와 인덱스의 순번이 어긋난 채로 남는 것을 막기 위한 것이다.
            stale_pdf = ""
            if hit and not os.path.basename(hit.get("저장경로", "")).startswith(nn + "_"):
                # 새 순번으로 다시 받으면 예전 순번의 파일이 디스크에 남는다. 어느
                # 줄에서도 가리키지 않으면 정체불명의 파일이 되므로 자리를 적어 둔다.
                stale_pdf = hit.get("저장경로", "")
                hit = None
            if hit:
                pdf_rec = _reuse(base, hit)
                pdf_name = hit.get("원파일명", "")
            elif bulk_skip or skip_pdf:
                why = ("용량 제한으로 미수집" if bulk_skip else "skip_pdf=True")
                pdf_rec = _record(base, 파일종류="첨부PDF", 문서종류=kind, 원파일명="",
                                  저장경로="", 바이트=0, sha256="", 수령성공여부="미수집",
                                  실패사유=why, fetched_at="", source_url=pdf_url,
                                  dcm_no=dcm)
            else:
                pdf_rec = _fetch_pdf(s, base, out_dir, os.path.join(doc_dir, "첨부"),
                                     rc, dcm, 파일종류="첨부PDF", 문서종류=kind,
                                     prefix=nn + "_", fallback_name=aname + ".pdf")
                pdf_name = pdf_rec.get("원파일명", "")
            pdf_rec["첨부명"] = aname
            pdf_rec["순번"] = nn
            if stale_pdf:
                pdf_rec["직전순번_파일"] = stale_pdf

            html_path = os.path.join(doc_dir, "첨부",
                                     "%s_%s.html" % (nn, sanitize_filename(aname)))
            hit, data = _cache_hit(out_dir, prev, ("첨부HTML", dcm), want_bytes=True,
                                    require_mode=True)
            if hit and hit.get("저장경로") == _rel(out_dir, html_path):
                html_rec = _reuse(base, hit)
                # 정관 판별에 제1조가 필요하니 캐시된 바이트도 똑같이 디코드해 둔다
                viewer_text = docparse.decode_document(data)[0] if data else ""
            elif bulk_skip:
                html_rec = _record(base, 파일종류="첨부HTML", 문서종류=kind, 원파일명=aname,
                                   저장경로="", 바이트=0, sha256="", 수령성공여부="미수집",
                                   실패사유="용량 제한으로 미수집", fetched_at="",
                                   source_url=view_url, dcm_no=dcm)
                viewer_text = ""
            else:
                # 첨부의 목차는 그 첨부 자신의 main.do 에만 있다. 한 번 받아 두고
                # 목차 전체 수집과 (목차가 없을 때의) 사다리에 같이 쓴다 — 예전에는
                # 빈 응답일 때만 받아 왔고, 그래서 목차가 여럿인 첨부(국민 2008 의
                # 감사보고서 24건 + 평가의견서 1건)는 표지 한 장만 받고 '성공'으로
                # 적혀 있었다. 실측: 저장 2,660바이트 / 실제 458,545바이트.
                att_text, att_err = attachment_main_text(s, rc, dcm)
                att_args = viewdoc_args(att_text)
                att_parts = viewer_parts(att_text, att_args)
                # 사다리는 '한 번에 받는 경로로 내려갔을 때'만 탄다(_fetch_viewer 가
                # len(plist)==1 일 때만 본다). 목차를 구했더라도 그 한 부분이 빈 응답일
                # 수 있으니 조건 없이 만들어 둔다 — 만들어 두는 데는 요청이 들지 않는다.
                retries = []
                if att_args:
                    retries.append(("첨부 viewDoc 인자",
                                    lambda a=att_args: VIEWER_URL % urllib.parse.urlencode(a)))
                if body_dtd and body_dtd != view_args["dtd"]:
                    retries.append(("본문 dtd", lambda a=view_args, t=body_dtd:
                                    VIEWER_URL % urllib.parse.urlencode(dict(a, dtd=t))))
                html_rec, viewer_text = _fetch_viewer(
                    s, base, out_dir, html_path, view_url,
                    파일종류="첨부HTML", 문서종류=kind, 원파일명=aname, dcm_no=dcm,
                    retries=retries, parts=att_parts)
                if att_err:
                    # 목차를 못 읽은 채 받은 파일이다. '성공'으로만 적으면 왜 한 부분만
                    # 받았는지가 사라진다 — CSV 로 나가는 칸에 사유를 남긴다.
                    html_rec["첨부목록_오류"] = att_err
                    why0 = html_rec.get("실패사유") or ""
                    html_rec["실패사유"] = ((why0 + " / " if why0 else "")
                                          + "[첨부 목차 미확인] 첨부 main.do 실패: " + att_err)
            html_rec["첨부명"] = aname
            html_rec["순번"] = nn

            # 정관이면 지주/자회사로 나눈다. 근거(파일명|제1조|이미지목록|미상)와
            # 거기서 읽은 상호를 그대로 남긴다 — 미분류로 남은 것도 손으로 가를 수 있게.
            if kind == "정관":
                kind2, basis, hint = classify_articles(pdf_name, viewer_text)
                for r in (pdf_rec, html_rec):
                    r["문서종류"] = kind2
                    r["정관판별근거"] = basis
                    r["정관_상호단서"] = hint

            for r in (pdf_rec, html_rec):
                add(r)
                if r["수령성공여부"] in ("성공", "부분수집"):
                    # 부분수집도 파일은 디스크에 있다 — 용량은 세고, 무엇이 빠졌는지는
                    # 실패사유·목차_노드 에 남는다. 성공으로 뭉개지 않는다.
                    n_ok += 1
                    account(r["바이트"])
                elif r["수령성공여부"] == "미수집":
                    n_skip += 1
                else:
                    n_fail += 1

        # 이번 실행이 손대지 못한 이전 기록은 파일이 디스크에 있는 한 그대로 살려 둔다.
        # 살리지 않으면 디스크에는 있는 파일이 인덱스에서 사라진다 — 삭제와 다를 바 없다.
        #
        # ★ 예전에는 '중단됐을 때만' 살렸다. 그러면 main.do 가 한 번 끊기는 것만으로
        #   (dart.fss.or.kr 은 간헐적으로 TLS 를 끊는다 — 이 파일 위쪽 실측 주석 참조)
        #   첨부 목록이 빈 채로 인덱스가 다시 쓰여 23행짜리 목록이 2행으로 줄어든다.
        #   파일 21개는 디스크에 그대로 있는데 목록에서만 사라진다. 모의 실험으로
        #   재현했다(20101210000020, main.do 만 실패시킴 → 23행 → 2행).
        #   그래서 사유를 붙여 늘 승계하고, 왜 이번에 확인하지 못했는지를 남긴다.
        if state["aborted"]:
            carry_why = "용량 한도로 중단: " + state["abort_reason"]
        elif list_err:
            carry_why = "목록 조회 실패로 이번 실행에서 확인 못 함: " + list_err
        else:
            carry_why = "이번 첨부 목록에 없는 이전 기록 (파일은 디스크에 남아 있음)"
        carried = 0
        for key, old in prev.items():
            if key in touched:
                continue
            if not _on_disk(out_dir, old):
                continue
            rec = dict(old)
            rec["이번실행_미확인"] = True      # sha256 을 다시 확인하지 못했다
            rec["승계사유"] = carry_why
            why0 = old.get("실패사유") or ""
            # CSV(원문_파일목록) 로 나가는 칸에도 티가 나야 한다. 인덱스에만 적으면
            # CSV 만 보는 사람에게는 이번 실행에서 확인된 행처럼 보인다.
            rec["실패사유"] = (why0 + " / " if why0 else "") + "[이번 실행 미확인] " + carry_why
            records.append(rec)
            rows.append(_row(rec))
            carried += 1

        header = {
            "rcept_no": rc, "corp_label": base["corp_label"], "rcept_dt": base["rcept_dt"],
            "doc_kind": base["doc_kind"], "doc_purpose": base["doc_purpose"],
            "report_nm": src_meta.get("report_nm", ""),
            "corp_name": src_meta.get("corp_name", ""),
            "메타출처": ("02_공시목록.csv" if meta else alt.get("메타출처", "")),
            "공시목록_조회": bool(meta), "공시목록_비고": meta_note,
            "본문XML": st["경로"] if st["존재"] else "",
            "openapi_status": st["openapi_status"], "openapi_message": st["openapi_message"],
            "목록_url": main_url, "목록_오류": list_err,
            "첨부_고유건수": len(attaches),
            "첨부_비고": attach_note,
            "첨부_타접수번호소유": foreign,
            "중단": state["aborted"], "중단사유": state["abort_reason"],
            "이전기록_승계": carried,
            "생성시각": ts_kst(),
        }
        write_index(out_dir, rc, header, records)

    return {"성공": n_ok, "실패": n_fail, "미수집": n_skip,
            "누적바이트": state["bytes"], "중단여부": state["aborted"],
            "중단사유": state["abort_reason"], "요청수": s.requests, "rows": rows}


# ── 개별 수집 ─────────────────────────────────────────────────────────────
def attachment_view_url(s, rcept_no, dcm_no):
    """첨부 자신의 viewDoc 인자를 main.do 에서 다시 읽어 뷰어 URL 을 만든다.

    ★ eleId=0&offset=0&length=0 은 만능이 아니다. 실측(국민 2008, 첨부 41건):
      정관 dcmNo=1920273 → 그 첨부의 viewDoc 인자 자체가 ("0","0","0") 이라 0/0/0 이 통했고,
      감사보고서 dcmNo=1920088 → 인자가 ("19","984","2359") 라 0/0/0 은 0바이트가 온다.
      41건 중 25건(감사보고서 24 + 평가의견서 1)이 이 경우였다.
    빈 응답일 때만 이 한 번을 더 쓴다 — 전 건에 쓰면 요청이 212번 늘어난다.
    """
    args = viewdoc_args(attachment_main_text(s, rcept_no, dcm_no)[0])
    return VIEWER_URL % urllib.parse.urlencode(args) if args else ""


def attachment_main_text(s, rcept_no, dcm_no):
    """(본문 문자열, 오류사유). 여기에만 그 첨부의 viewDoc 인자와 목차가 있다.

    ★ 실패를 조용히 삼키면 안 된다. 여기가 비면 호출부는 목차를 못 구해 eleId=0
    단일 요청으로 내려가는데, 그 경로는 구시대 문서를 모지바케로 돌려준다
    (viewer_parts 주석의 실측 참조). dart.fss.or.kr 은 간헐적으로 TLS 를 끊으므로
    그 한 번이 '성공'으로 적힌 깨진 파일이 된다. 그래서 사유를 같이 돌려주고
    호출부가 레코드에 남긴다.
    """
    try:
        _, body, _, _ = s.get(MAIN_URL % rcept_no + "&dcmNo=" + dcm_no)
    except WebFetchError as e:
        return "", str(e)
    return body.decode("utf-8", "replace"), ""


def _fetch_viewer(s, base, out_dir, path, url, 파일종류, 문서종류, 원파일명, dcm_no,
                  retries=(), parts=()):
    """(레코드, 디코드된 본문). 저장은 원본 바이트 그대로, 디코드 결과는 기록만 한다.

    본문 텍스트를 레코드에 넣지 않는다 — 우리은행 2018 본문이 1,007,879자라
    인덱스 JSON 에 실리면 같은 내용이 통째로 두 번 저장된다.

    ★ parts 가 있으면 목차 최상위 노드를 순서대로 전부 받아 이어 붙인다. 뷰어가
    노드 하나씩만 주기 때문이다(모듈 상단 TOC 주석의 실측 참조). 한 부분이라도
    못 받으면 수령성공여부를 '부분수집'으로 내리고 어느 목차가 어떤 사유로 빠졌는지
    실패사유에 적는다 — 잘린 것을 '성공'으로 적는 일이 없어야 한다.
    retries 는 목차를 못 구했을 때(단일 요청 경로)만 타는 사다리로, 빈 응답이면
    차례로 시도할 (이름, URL 을 돌려주는 함수) 목록이다.
    """
    rec = _record(base, 파일종류=파일종류, 문서종류=문서종류, 원파일명=원파일명,
                  저장경로="", 바이트=0, sha256="", 수령성공여부="실패", 실패사유="",
                  fetched_at=ts_kst(), source_url=url, dcm_no=dcm_no)
    plist = list(parts) or [("", url)]
    rec["수집방식"] = "목차전체" if parts else "단일"
    rec["목차_노드수"] = len(plist)
    recipe = "목차전체" if parts else "기본"
    chunks, got, missed = [], [], []
    hdrs, attempts = {}, 0

    for i, (label, purl) in enumerate(plist, start=1):
        name = label or "전체"
        if not purl:
            missed.append("%d.%s: 목차에 eleId/offset/length 가 없어 요청을 만들 수 없음" % (i, name))
            continue
        try:
            _, body, h, attempts = s.get(purl)
        except WebFetchError as e:
            missed.append("%d.%s: %s" % (i, name, e))
            continue
        if len(plist) == 1:
            # 목차를 못 구한 문서에서만 타는 사다리(첨부 자신의 viewDoc 인자 → 본문 dtd).
            for rname, make_url in retries:
                if len(body) >= MIN_VIEWER_BYTES:
                    break
                try:
                    url2 = make_url()
                    if not url2 or url2 == purl:
                        continue
                    _, body2, h2, attempts = s.get(url2)
                except WebFetchError:
                    continue
                if len(body2) > len(body):
                    body, purl, h, recipe = body2, url2, h2, rname
                    rec["source_url"] = url2
        if not body:
            missed.append("%d.%s: 빈 응답(0바이트)" % (i, name))
            continue
        if chunks:
            chunks.append((PART_SEP % (i, len(plist), _ele_of(purl), name)).encode("utf-8"))
        got.append({"순서": i, "제목": label, "시작바이트": sum(len(c) for c in chunks),
                    "바이트": len(body), "url": purl})
        chunks.append(body)
        hdrs = h or hdrs

    rec["viewer_recipe"] = recipe
    rec["수집규약"] = VIEWER_RULE
    rec["목차_수집수"] = len(got)
    rec["목차_노드"] = got

    if not chunks:
        rec["실패사유"] = (" / ".join(missed) if missed
                          else "빈 응답(0바이트) — 뷰어 인자 재조회까지 실패")
        return rec, ""

    body = b"".join(chunks)
    text, declared, used, repl = docparse.decode_document(body)
    digest = _atomic_write(path, body)
    rec.update(저장경로=_rel(out_dir, path), 바이트=len(body), sha256=digest,
               수령성공여부="성공" if not missed else "부분수집", fetched_at=ts_kst())
    if missed:
        rec["실패사유"] = ("목차 %d/%d 를 못 받아 부분수집: %s"
                          % (len(missed), len(plist), " / ".join(missed)))
    rec["content_type"] = (hdrs or {}).get("Content-Type", "")
    rec["encoding_declared"] = declared
    rec["encoding_used"] = used
    rec["decode_replacements"] = repl
    # 서버가 이미 깨뜨려 보낸 U+FFFD 개수. 우리 디코드가 성공해도 원문이 복구 불가인
    # 경우가 있다 — 실측: 국민 2008 정관 뷰어 HTML 에 U+FFFD 10,754개.
    rec["source_replacement_chars"] = body.count(b"\xef\xbf\xbd")
    rec["attempts"] = attempts
    return rec, text


def _fetch_pdf(s, base, out_dir, dest_dir, rcept_no, dcm_no, 파일종류, 문서종류,
               fixed_name="", prefix="", fallback_name=""):
    """pdf.do. Referer 없이는 0바이트가 온다(실측) — 항상 붙인다."""
    url = PDF_URL % (rcept_no, dcm_no)
    ref = PDF_REFERER % (rcept_no, dcm_no)
    rec = _record(base, 파일종류=파일종류, 문서종류=문서종류, 원파일명="", 저장경로="",
                  바이트=0, sha256="", 수령성공여부="실패", 실패사유="",
                  fetched_at=ts_kst(), source_url=url, dcm_no=dcm_no)
    try:
        _, body, hdrs, attempts = s.get(url, referer=ref)
    except WebFetchError as e:
        rec["실패사유"] = str(e)
        return rec

    name, ok = content_disposition_filename(hdrs)
    rec["원파일명"] = name or fallback_name
    rec["filename_decode_ok"] = ok
    rec["attempts"] = attempts

    if not body:
        rec["실패사유"] = "빈 응답(0바이트) — Referer 거부 가능"
        return rec
    if body[:5] != b"%PDF-":
        rec["실패사유"] = "PDF 서명이 아님(앞 5바이트=%r)" % body[:5]
        return rec

    fname = fixed_name or (prefix + sanitize_filename(name or fallback_name))
    path = os.path.join(dest_dir, fname)
    digest = _atomic_write(path, body)
    rec.update(저장경로=_rel(out_dir, path), 바이트=len(body), sha256=digest,
               수령성공여부="성공", fetched_at=ts_kst())
    return rec
