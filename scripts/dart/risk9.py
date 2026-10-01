# -*- coding: utf-8 -*-
"""9차 — 리스크부문 v0.4 위임(2026-10-01). DART 수집 부분.

작업 1 추가 산출물(FY2023~FY2025 사업보고서 Ⅵ 위험관리위원회 활동·Ⅷ 직원/CRO), 작업 2
(메리츠·한국투자 2021.1Q~최신 분기 자본 지표), 작업 3(FY2023~FY2025 내부회계), 작업 4
(보험 자회사 FY2025 사업보고서 위험관리 절)에 쓸 DART 원문을 받는다. 8차(risk8)와 같은
규율: 원본은 손대지 않고 출처·시각·sha256 을 남기며, 정정본은 모두 받고 어느 것이 최종인지
판정하지 않는다. API 키는 환경변수(DART_API_KEY)에서만 읽고 출력하지 않는다.

    python3 scripts/dart/risk9.py fetch-list     # 대상 보고서 목록(OpenDART list) → dart_out/risk9/DART_목록.csv
    python3 scripts/dart/risk9.py fetch-doc      # 목록의 document.xml
    python3 scripts/dart/risk9.py fetch-viewer   # 쪽 번호용 DART 뷰어 본문 PDF(+ 지주 사업보고서는 첨부까지)
"""
from __future__ import annotations

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import risk8  # noqa: E402

OUT = risk8.OUT
WORK = os.path.join(OUT, "risk9")

# 지주 8개 — risk8.CORPS 의 고유번호(메리츠·한국금융지주는 8차에서 종목코드로 확정한 값)
HOLDINGS = {
    "KB금융지주": "00688996", "신한금융지주": "00382199", "하나금융지주": "00547583",
    "우리금융지주": "01350869", "메리츠금융지주": "00860332", "iM금융지주": "00878915",
    "NH농협금융지주": "00908021", "한국투자금융지주": "00432102",
}
# 작업 2 — 비은행지주 후보(해당 여부는 원문으로 확인한다)
NONBANK = ["메리츠금융지주", "한국투자금융지주"]
NONBANK_FROM = ("20210401", "2021.03")      # 2021년 1분기 보고서(2021.03)부터
# 작업 4 — 보험 자회사(사업보고서 제출 대상인지 목록으로 확인)
INSURERS = {
    "KB손해보험": ("00120216", "KB금융지주"),
    "KB라이프생명": ("00160393", "KB금융지주"),
    "신한라이프생명": ("00137517", "신한금융지주"),
    "하나생명": ("00187123", "하나금융지주"),
    "메리츠화재": ("", "메리츠금융지주"),           # 종목코드 000060 으로 찾는다
    "동양생명": ("00117267", "우리금융지주"),
    "ABL생명": ("00148391", "우리금융지주"),
}
END = "20260930"


def _client():
    import client as dclient
    return dclient.DartClient(OUT, delay=0.5)


def _meritz_fire(c):
    import corpcode
    idx, _res = corpcode.load_corp_index(c, phase="risk9")
    hits = [e for e in idx if (e.get("stock_code") or "").strip() == "000060"]
    if len(hits) != 1:
        raise SystemExit("메리츠화재 종목코드 000060 으로 corp_code 를 하나로 못 찾음: %s" % hits)
    return hits[0]["corp_code"]


def fetch_list():
    c = _client()
    rows = []

    def add(group, lab, code, want, bgn, note=""):
        got = risk8._list_all(c, {"corp_code": code, "bgn_de": bgn, "end_de": END, "pblntf_ty": "A"})
        hit = [r for r in got if want(r.get("report_nm", ""))]
        for r in hit:
            rows.append(dict(group=group, corp_label=lab, corp_code=code, rcept_no=r["rcept_no"],
                             rcept_dt=r["rcept_dt"], report_nm=r["report_nm"].strip(),
                             corp_name=r.get("corp_name", ""), list_raw=r["_raw"],
                             list_sha256=r["_sha"], list_at=r["_at"], note=note))
        if not hit:
            rows.append(dict(group=group, corp_label=lab, corp_code=code, rcept_no="", rcept_dt="",
                             report_nm="", note="목록(정기공시 %s~%s)에 해당 보고서 없음" % (bgn, END)))
        return hit

    # A. 지주 사업보고서 FY2023·FY2024 (FY2025 는 8차에 있음 — 같은 목록 규칙으로 다시 적는다)
    for lab, code in HOLDINGS.items():
        add("A_지주사업보고서", lab, code,
            lambda n: "사업보고서" in n and re.search(r"\((2023|2024|2025)\.12\)", n), "20240101")
    # B. 비은행지주 분기·반기·사업보고서 2021.03~
    for lab in NONBANK:
        def want(n):
            m = re.search(r"(분기|반기|사업)보고서\s*\((\d{4})\.(\d{2})\)", n)
            return bool(m) and (m.group(2), m.group(3)) >= tuple(NONBANK_FROM[1].split("."))
        add("B_비은행지주정기", lab, HOLDINGS[lab], want, NONBANK_FROM[0])
    # C. 보험 자회사 FY2025 사업보고서
    for lab, (code, parent) in INSURERS.items():
        code = code or _meritz_fire(c)
        add("C_보험자회사", lab, code, lambda n: "사업보고서" in n and "(2025.12)" in n, "20260101",
            note="지주 " + parent)
    os.makedirs(WORK, exist_ok=True)
    cols = ["group", "corp_label", "corp_code", "rcept_no", "rcept_dt", "report_nm", "corp_name",
            "list_raw", "list_sha256", "list_at", "note"]
    risk8._w(os.path.join(WORK, "DART_목록.csv"), rows, cols)
    for g in sorted({r["group"] for r in rows}):
        rs = [r for r in rows if r["group"] == g]
        print("%s — 보고서 %d건, 목록 없음 %d" % (g, sum(1 for r in rs if r["rcept_no"]),
                                           sum(1 for r in rs if not r["rcept_no"])))
    print("API 호출 %d" % c.network_calls)


def fetch_conv_names():
    """2차에서 본문만 받아 둔 지주 전환 신고서 2건의 DART 공식 보고서명(목록 API). 8·9차 CSV 의 문서명 칸용."""
    import corpcode
    c = _client()
    idx, _res = corpcode.load_corp_index(c, phase="risk9")
    want = [("메리츠화재", "000060", "20101210000020"), ("우리은행", None, "20181108000394")]
    rows = []
    for lab, stock, rc in want:
        if stock:
            cands = [e for e in idx if (e.get("stock_code") or "").strip() == stock]
        else:
            cands = [e for e in idx if (e.get("corp_name") or "").strip() == lab]
        found = None
        for e in cands:
            got = risk8._list_all(c, {"corp_code": e["corp_code"], "bgn_de": rc[:8], "end_de": rc[:8]})
            found = next((r for r in got if r["rcept_no"] == rc), None)
            if found:
                rows.append(dict(rcept_no=rc, corp_code=e["corp_code"], corp_name=found.get("corp_name", ""),
                                 report_nm=found["report_nm"].strip(), rcept_dt=found["rcept_dt"],
                                 list_raw=found["_raw"], list_sha256=found["_sha"], list_at=found["_at"]))
                break
        if not found:
            rows.append(dict(rcept_no=rc, corp_code="", corp_name=lab, report_nm="",
                             note="목록 API 에서 이 접수번호를 못 찾음(후보 %d곳)" % len(cands)))
    risk8._w(os.path.join(WORK, "전환신고서_문서명.csv"), rows,
             ["rcept_no", "corp_code", "corp_name", "report_nm", "rcept_dt", "list_raw", "list_sha256",
              "list_at", "note"])
    for r in rows:
        print(r["rcept_no"], r.get("corp_name"), r.get("report_nm") or r.get("note"))
    # 지주 8개 기업개황(상장 여부 corp_cls·종목코드) — 작업 3 의 listed 칸 근거
    comp = []
    for lab, code in HOLDINGS.items():
        x = c.call("company", {"corp_code": code}, phase="risk9")
        d = x.data or {}
        comp.append(dict(corp_label=lab, corp_code=code, corp_name=d.get("corp_name", ""),
                         stock_code=d.get("stock_code", ""), corp_cls=d.get("corp_cls", ""),
                         status=x.status, raw_path=x.raw_path, raw_sha256=x.raw_sha256, fetched_at=x.fetched_at))
    risk8._w(os.path.join(WORK, "지주_기업개황.csv"), comp, list(comp[0].keys()))
    print("기업개황 %d · %s" % (len(comp), ", ".join("%s=%s" % (r["corp_label"], r["corp_cls"]) for r in comp)))


def _targets():
    p = os.path.join(WORK, "DART_목록.csv")
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    seen, out = set(), []
    for r in rows:                       # A → B → C 순서(우선순위) 그대로, 중복 접수번호는 한 번
        if r["rcept_no"] and r["rcept_no"] not in seen:
            seen.add(r["rcept_no"])
            out.append(r)
    return out


def fetch_doc():
    c = _client()
    res = []
    for r in _targets():
        x = c.call("document", {"rcept_no": r["rcept_no"]}, phase="risk9")
        res.append(dict(group=r["group"], corp_label=r["corp_label"], rcept_no=r["rcept_no"],
                        report_nm=r["report_nm"], document_status=x.status,
                        document_message=getattr(x, "message", ""), document_raw=x.raw_path,
                        document_sha256=x.raw_sha256, document_at=x.fetched_at))
        print("  %-10s %s %-28s %s" % (r["corp_label"], r["rcept_no"], r["report_nm"][:28], x.status))
        risk8._w(os.path.join(WORK, "DART_원문.csv"), res, list(res[0].keys()))
    print("document %d건 · 000 %d · API 호출 %d" % (len(res), sum(1 for x in res if x["document_status"] == "000"),
                                                 c.network_calls))


def fetch_viewer():
    """본문 PDF(쪽 번호용). 지주 사업보고서(작업 1·3)는 첨부(감사보고서 등)까지, 나머지는 본문만."""
    import dartweb
    t = _targets()
    a = [r["rcept_no"] for r in t if r["group"] == "A_지주사업보고서"]
    rest = [r["rcept_no"] for r in t if r["group"] != "A_지주사업보고서"]
    out = os.path.abspath(OUT)
    r1 = dartweb.collect(out, rcept_nos=a, size_limit_bytes=6 << 30)
    print("뷰어(지주 사업보고서, 첨부 포함) — 성공 %s · 실패 %s · 미수집 %s"
          % (r1.get("성공"), r1.get("실패"), r1.get("미수집")))
    r2 = dartweb.collect(out, rcept_nos=rest, size_limit_bytes=6 << 30, bulk_skip_always=True)
    print("뷰어(분기보고서·보험 자회사, 감사·검토보고서 제외) — 성공 %s · 실패 %s · 미수집 %s"
          % (r2.get("성공"), r2.get("실패"), r2.get("미수집")))


# ── 쪽 번호용 텍스트 ───────────────────────────────────────────────────────
TEXT = os.path.join(OUT, "text", "risk9")


def _extract_one(rc):
    """dart_out/doc/<rc>/본문.pdf → dart_out/text/risk9/<rc>.txt (=== p.N === 표지). 원본 sha 같으면 건너뜀."""
    import hashlib
    import pypdf
    pdf = os.path.join(OUT, "doc", rc, "본문.pdf")
    rec = dict(rcept_no=rc, 원본=pdf, 원본sha256="", 쪽수="", 글자수="", 빈쪽수="", 텍스트="",
               텍스트sha256="", 상태="")
    if not os.path.exists(pdf):
        rec["상태"] = "본문 PDF 없음"
        return rec
    h = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    tp = os.path.join(TEXT, rc + ".txt")
    side = tp + ".src"
    if os.path.exists(tp) and os.path.exists(side) and open(side).read().strip() == h:
        body = open(tp, encoding="utf-8").read()
        n = body.count("\n=== p.") + (1 if body.startswith("=== p.") else 0)
        rec.update(원본sha256=h, 쪽수=str(n), 텍스트=tp,
                   텍스트sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(), 상태="추출(재사용)")
        return rec
    try:
        reader = pypdf.PdfReader(pdf)
        parts, empty, total = [], 0, 0
        for i, pg in enumerate(reader.pages, 1):
            try:
                t = pg.extract_text() or ""
            except Exception as e:                    # noqa: BLE001
                t = ""
                parts.append("=== p.%d === [추출 실패 %s]" % (i, type(e).__name__))
                empty += 1
                continue
            empty += 0 if t.strip() else 1
            total += len(t)
            parts.append("=== p.%d ===\n%s" % (i, t))
        body = "\n".join(parts) + "\n"
        os.makedirs(TEXT, exist_ok=True)
        with open(tp + ".part", "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tp + ".part", tp)
        with open(side, "w") as f:
            f.write(h)
        rec.update(원본sha256=h, 쪽수=str(len(reader.pages)), 글자수=str(total), 빈쪽수=str(empty),
                   텍스트=tp, 텍스트sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(), 상태="추출")
    except Exception as e:                            # noqa: BLE001
        rec["상태"] = "PDF 열기 실패: %s: %s" % (type(e).__name__, e)
    return rec


def extract(groups=None, workers=2):
    from concurrent.futures import ProcessPoolExecutor
    t = [r for r in _targets() if not groups or r["group"] in groups]
    rcs = [r["rcept_no"] for r in t]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        recs = list(ex.map(_extract_one, rcs))
    meta = {r["rcept_no"]: r for r in t}
    for r in recs:
        m = meta[r["rcept_no"]]
        r.update(group=m["group"], corp_label=m["corp_label"], report_nm=m["report_nm"])
    p = os.path.join(WORK, "텍스트목록.csv")
    old = {r["rcept_no"]: r for r in csv.DictReader(open(p, encoding="utf-8-sig"))} if os.path.exists(p) else {}
    old.update({r["rcept_no"]: r for r in recs})
    cols = ["group", "corp_label", "rcept_no", "report_nm", "원본", "원본sha256", "쪽수", "글자수",
            "빈쪽수", "텍스트", "텍스트sha256", "상태"]
    risk8._w(p, list(old.values()), cols)
    import collections
    print("텍스트 %d건 — %s" % (len(recs), dict(collections.Counter(r["상태"][:8] for r in recs))))


# ── 원문 XML 파싱 공용 ─────────────────────────────────────────────────────
def main_xml(rc):
    """document.xml zip 의 본문 XML(접수번호.xml, 없으면 가장 큰 것) → 글. 없으면 None."""
    import zipfile
    p = os.path.join(OUT, "raw", "document", rc + ".zip")
    if not os.path.exists(p):
        return None
    try:
        z = zipfile.ZipFile(p)
    except zipfile.BadZipFile:
        return None
    names = [n for n in z.namelist() if n == rc + ".xml"]
    if not names:
        return None                       # 첨부정정 등 — 본문 XML 이 없다
    import docparse                       # 2021년 이전 원문은 EUC-KR 이다 — 선언을 보고 utf-8·cp949 순으로
    return docparse.decode_document(z.read(names[0]))[0]


def part(x, roman_from, roman_to_pat):
    """「Ⅵ. 이사회…」 같은 장(TITLE)부터 다음 장 앞까지. (시작, 글) 또는 (None, '')."""
    m1 = re.search(r"<TITLE[^>]*>\s*(%s)\.\s*" % roman_from, x)
    if not m1:
        return None, ""
    m2 = re.search(r"<TITLE[^>]*>\s*(%s)\.\s*" % roman_to_pat, x[m1.end():])
    return m1.start(), x[m1.start(): m1.end() + m2.start() if m2 else len(x)]


def grid(tbl):
    """docparse 표 → 병합셀을 펼친 격자. 칸 = (글, 병합으로 이어받은 칸인가)."""
    cells, maxc = {}, 0
    for r, row in enumerate(tbl["rows"]):
        c = 0
        for cell in row:
            while (r, c) in cells:
                c += 1
            rs = int(cell["rowspan"]) if str(cell.get("rowspan") or "").isdigit() else 1
            cs = int(cell["colspan"]) if str(cell.get("colspan") or "").isdigit() else 1
            for i in range(max(rs, 1)):
                for j in range(max(cs, 1)):
                    cells[(r + i, c + j)] = (cell["text"], i > 0 or j > 0)
            c += max(cs, 1)
            maxc = max(maxc, c)
    nr = max([k[0] for k in cells] + [-1]) + 1
    return [[cells.get((r, c), ("", False)) for c in range(maxc)] for r in range(nr)]


def _ptexts(xml_slice):
    import html as _h
    return [_h.unescape(re.sub(r"<[^>]+>|\s+", " ", p)).strip()
            for p in re.findall(r"<P[^>]*>(.*?)</P>", xml_slice, re.S)]


DATE_RE = re.compile(r"((?:19|20)\d{2}|\d{2})\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2}")
# 위험관리위원회 이름 판정 — 글 안의 마지막 「…위원회」 낱말이 (그룹)리스크관리·위험관리위원회인가.
# 「소비자리스크관리위원회」는 다른 위원회라 빠진다(낱말 전체를 보므로).
COMMITTEE_TOKEN = re.compile(r"[가-힣A-Za-z]*위원회")
RISK_COMMITTEE = re.compile(r"^(그룹)?(리스크|위험)관리위원회$")


def committee_token(text):
    toks = COMMITTEE_TOKEN.findall(re.sub(r"\s+", "", text or ""))
    return toks[-1] if toks else ""


def is_risk_committee(text):
    return bool(RISK_COMMITTEE.match(committee_token(text)))


HEADING = re.compile(r"^\s*(\(?[가-하0-9]{1,2}\)|[가-하0-9]{1,2}\.|■|□|○|●|◆|▶|\[|<|【)")


def committee_activity(rc):
    """Ⅵ 장의 위원회 활동표(머리행에 개최일자·의안) 중 위험관리(리스크관리)위원회 행 전수.
    위원회 이름은 표의 「위원회명」 열, 없으면 표 바로 앞 문단(소제목)에서 읽는다(원문 그대로)."""
    import docparse
    x = main_xml(rc)
    if x is None:
        return None, "본문 XML 없음"
    off, sl = part(x, "VI|Ⅵ", "VII|Ⅶ")
    if off is None:
        return None, "Ⅵ 장 없음"
    secs, err = docparse.parse_document(sl)
    out = []
    for s in secs:
        for ti, t in enumerate(s["tables"]):
            g = grid(t)
            if not g:
                continue
            # 머리행: 날짜가 처음 나오는 행 앞까지
            first = next((i for i, row in enumerate(g)
                          if any(DATE_RE.search(c[0]) for c in row)), None)
            if first is None or first == 0:
                continue
            head = [" ".join(dict.fromkeys(g[i][j][0] for i in range(first) if g[i][j][0])).strip()
                    for j in range(len(g[0]))]
            hj = lambda *keys: [j for j, h in enumerate(head) if any(k in re.sub(r"\s+", "", h) for k in keys)]
            c_date, c_agenda = hj("개최일", "일자"), hj("의안", "안건")
            if not c_date or not c_agenda:
                continue
            c_res, c_sess, c_comm = hj("가결", "결과"), hj("회차"), hj("위원회명")
            before = _ptexts(sl[max(0, t["start"] - 4000): t["start"]])
            ctx = [p for p in before if "위원회" in p and len(p) < 120]
            heads = [p for p in ctx if HEADING.match(p) or "활동" in p]
            ctx_name = (heads or ctx or [""])[-1]
            for i in range(first, len(g)):
                row = g[i]
                date = row[c_date[0]][0]
                if not DATE_RE.search(date or ""):
                    continue
                comm = row[c_comm[0]][0] if c_comm else ""
                name = comm or ctx_name
                if not is_risk_committee(name):
                    continue
                agenda = " | ".join(dict.fromkeys(row[j][0] for j in c_agenda if row[j][0]))
                merged = [head[j] for j in [c_date[0]] + c_sess[:1] + c_comm[:1] if row[j][1]]
                out.append(dict(
                    committee=name, committee_src="표 「위원회명」 열" if comm else "표 앞 소제목",
                    meeting_date=date, session=row[c_sess[0]][0] if c_sess else "",
                    agenda=agenda, resolution=row[c_res[0]][0] if c_res else "",
                    table_section=s.get("title", ""), table_index=ti, row_index=i,
                    header=" | ".join(head), merged_cells=", ".join(merged)))
    return out, err


# ── 쪽 찾기·출처 공용 ──────────────────────────────────────────────────────
_PAGES = {}


def pages_of(rc):
    """{쪽: 공백 뺀 글} — risk9 텍스트(뷰어 본문 PDF). 없으면 {}."""
    if rc not in _PAGES:
        p = os.path.join(TEXT, rc + ".txt")
        _PAGES[rc] = ({n: risk8._nows(t) for n, t in risk8.re_split_pages(open(p, encoding="utf-8").read())}
                      if os.path.exists(p) else {})
    return _PAGES[rc]


def find_page(rc, *keys, within=None):
    """keys(공백 무시)가 모두 들어 있는 첫 쪽. within=(시작쪽, 끝쪽) 범위 우선. 못 찾으면 ''."""
    P = pages_of(rc)
    ks = [risk8._nows(k) for k in keys if k and risk8._nows(k)]
    if not P or not ks:
        return ""
    order = sorted(P)
    if within:          # 장 범위를 찾았으면 그 안에서만 — 정정본 앞머리의 「정정 후」 표 등과 섞이지 않게
        order = [n for n in order if within[0] <= n <= within[1]]
    return next((n for n in order if all(k in P[n] for k in ks)), "")


def part_pages(rc, start_pat, end_pat):
    """본문 PDF 에서 장 범위(쪽). 장 제목 바로 뒤에 첫 절(「1.」·「가.」)이 이어지는 쪽을 시작으로 본다 —
    목차(줄표)·정정본 앞머리·본문 속 참조(「… 'VI. 이사회 등 …' 참조」)는 그렇게 이어지지 않는다."""
    P = pages_of(rc)
    if not P:
        return None
    head = re.compile("(%s)(1\\.|가\\.|\\(1\\))" % start_pat)
    S = [n for n in sorted(P) if head.search(P[n]) and "....." not in P[n]]
    if not S:                                     # 그런 쪽이 없으면 예전 방식(목차 제외 첫 쪽)
        S = [n for n in sorted(P) if re.search(start_pat, P[n]) and "....." not in P[n]][:1]
        if not S:
            return None
    s_ = S[-1] if len(S) > 1 else S[0]
    endh = re.compile("(%s)(1\\.|가\\.|\\(1\\))" % end_pat)
    e_ = next((n for n in sorted(P) if n > s_ and endh.search(P[n]) and "....." not in P[n]), None)
    if e_ is None:
        e_ = next((n for n in sorted(P) if n > s_ and re.search(end_pat, P[n]) and "....." not in P[n]), max(P))
    return (s_, e_)


MD_ROOT = os.path.join(risk8.HANDOFF, "원문텍스트_9차")


def cited_md(task, rc, pages, title=""):
    """인용한 쪽의 추출 텍스트 전문(뷰어 본문 PDF, pypdf, 글자 수정 없음)을 문서별 .md 로. 경로를 돌려준다."""
    pages = sorted({int(p) for p in pages if str(p).strip().isdigit()})
    if not pages:
        return ""
    p = os.path.join(TEXT, rc + ".txt")
    if not os.path.exists(p):
        return ""
    P = dict(risk8.re_split_pages(open(p, encoding="utf-8").read()))
    name, at = doc_meta(rc)
    d = os.path.join(MD_ROOT, task)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, rc + ".md")
    lines = ["# %s · %s" % (title or rc, name), "", "- 접수번호: %s (DART 뷰어 본문 PDF)" % rc,
             "- 수집일: %s" % at, "- 아래는 이 문서에서 인용한 쪽의 추출 텍스트 전문이다(글자 수정 없음).", ""]
    for n in pages:
        lines += ["## p.%d" % n, "", "```text", P.get(n, "(쪽 없음)").rstrip("\n"), "```", ""]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out


def _attach_md(task, rows, page_cols, rc_col="rcept_no"):
    """행들이 인용한 쪽을 문서별로 모아 .md 를 만들고 각 행에 경로(원문_md)를 붙인다."""
    by = {}
    for o in rows:
        for c in page_cols:
            if str(o.get(c, "")).strip().isdigit():
                by.setdefault(o[rc_col], set()).add(int(o[c]))
    paths = {}
    for rc, pg in by.items():
        lab = next((o["corp_label"] for o in rows if o[rc_col] == rc), "")
        paths[rc] = cited_md(task, rc, pg, lab)
    for o in rows:
        o["원문_md"] = paths.get(o[rc_col], "")


def doc_meta(rc):
    """(보고서명, 수집일) — 목록·원문 XML·뷰어 PDF 수집 시각."""
    import json
    t = {r["rcept_no"]: r for r in _targets()}.get(rc, {})
    dx = {}
    p = os.path.join(WORK, "DART_원문.csv")
    if os.path.exists(p):
        dx = {r["rcept_no"]: r for r in csv.DictReader(open(p, encoding="utf-8-sig"))}.get(rc, {})
    pdf_at = ""
    ix = os.path.join(OUT, "doc", rc, "_파일목록.json")
    if os.path.exists(ix):
        rec = next((f for f in json.load(open(ix, encoding="utf-8")).get("files", [])
                    if f.get("파일종류") == "본문PDF"), {})
        pdf_at = rec.get("fetched_at", "")
    at = "원문XML %s · 뷰어PDF %s" % (dx.get("document_at", "") or "-", pdf_at or "-")
    return t.get("report_nm", ""), at


def _fy(report_nm):
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    return m.group(1) if m else ""


def activity_page(rc, date, agenda, rng):
    """(쪽, 근거). 표 칸 글이 PDF 에서 줄로 갈라져도 찾도록 단계적으로 느슨하게 — 근거를 함께 남긴다."""
    core = re.sub(r"^[\s\-·ㅇｏo•▶]*([<\[(（【][^>\])）】]{1,8}[>\])）】])?\s*(\d+[).]|[-·ㅇｏ])?\s*", "", agenda or "")
    tail = (agenda or "").split(" | ")[-1]          # 의안이 두 칸(구분 | 내용)이면 PDF 에서 이어지지 않는다
    for keys, why in (((date, agenda[:30]), "개최일+의안30자"), ((date, tail[:30]), "개최일+의안끝칸30자"),
                      ((date, core[:12]), "개최일+의안핵심12자"), ((agenda[:30],), "의안30자"),
                      ((tail[:30],), "의안끝칸30자"), ((core[:20],), "의안핵심20자")):
        pg = find_page(rc, *keys, within=rng)
        if pg:
            return pg, why
    P = pages_of(rc)
    if rng and date:
        hits = [n for n in range(rng[0], rng[1] + 1) if risk8._nows(date) in P.get(n, "")]
        if len(hits) == 1:
            return hits[0], "개최일(Ⅵ 장에서 유일)"
    return "", ""


# ── 작업 1 추가 산출물 ──────────────────────────────────────────────────────
def build_activity():
    """원문_위험관리위원회_활동.csv — FY2023~FY2025 사업보고서(정정본 포함) Ⅵ 의 위험관리위원회 활동 전수."""
    t = [r for r in _targets() if r["group"] == "A_지주사업보고서"]
    out, docs = [], []
    by_fy_orig = {}
    for r in t:
        rc = r["rcept_no"]
        rows, err = committee_activity(rc)
        name, at = doc_meta(rc)
        fy = _fy(r["report_nm"])
        docs.append(dict(corp_label=r["corp_label"], fy=fy, rcept_no=rc, report_nm=name,
                         rows=len(rows) if rows is not None else "", 상태=err or ("본문 없음" if rows is None else "")))
        if rows is None:
            continue
        rng = part_pages(rc, r"(VI|Ⅵ)\.이사회등회사의기관에관한사항", r"(VII|Ⅶ)\.주주에관한사항")
        for x in rows:
            sess, ssrc = x["session"], "표 「회차」 열" if x["session"] else ""
            if not sess:
                m = re.search(r"제\s*\d+\s*차", x["agenda"])
                if m:
                    sess, ssrc = m.group(0), "의안내용 칸 안의 표기"
            pg, basis = activity_page(rc, x["meeting_date"], x["agenda"], rng)
            out.append(dict(corp_label=r["corp_label"], fy=fy, meeting_date=x["meeting_date"], session=sess,
                            agenda=x["agenda"], resolution=x["resolution"], rcept_no=rc, doc_name=name,
                            page=pg, page_basis=basis, collected_at=at, committee=x["committee"],
                            committee_src=x["committee_src"], session_src=ssrc,
                            merged_cells=x["merged_cells"], table_section=x["table_section"],
                            table_index=x["table_index"], row_index=x["row_index"], header=x["header"],
                            note=""))
    # 같은 사업연도의 정정본: 원본(접수번호가 가장 이른 본)의 행과 같은 (개최일·의안)이 있는지 — 판정 없이 적기만
    for fy_key in {(o["corp_label"], o["fy"]) for o in out}:
        rs = [o for o in out if (o["corp_label"], o["fy"]) == fy_key]
        first = min(o["rcept_no"] for o in rs)
        base = {(risk8._nows(o["meeting_date"]), risk8._nows(o["agenda"])) for o in rs if o["rcept_no"] == first}
        for o in rs:
            if o["rcept_no"] != first:
                same = (risk8._nows(o["meeting_date"]), risk8._nows(o["agenda"])) in base
                o["note"] = "같은 사업연도 다른 본(원본 %s) — %s" % (first, "같은 행 있음" if same else "원본에 없는 행")
            if not o["page"]:
                o["note"] = (o["note"] + " / " if o["note"] else "") + "뷰어 PDF 에서 쪽을 못 찾음(텍스트 없음 또는 표기 차이)"
    _attach_md("위험관리위원회_활동", out, ["page"])
    cols = ["corp_label", "fy", "meeting_date", "session", "agenda", "resolution", "rcept_no", "doc_name", "page",
            "page_basis", "collected_at", "committee", "committee_src", "session_src", "merged_cells", "note", "원문_md",
            "table_section", "table_index", "row_index", "header"]
    risk8._w(os.path.join(risk8.HANDOFF, "원문_위험관리위원회_활동.csv"), out, cols)
    risk8._w(os.path.join(WORK, "위원회활동_문서별.csv"), docs, list(docs[0].keys()))
    print("원문_위험관리위원회_활동.csv %d행 · 문서 %d(본문 없음 %d) · 쪽 못 찾음 %d"
          % (len(out), len(docs), sum(1 for d in docs if d["rows"] == ""), sum(1 for o in out if not o["page"])))
    return out


CRO_EXPLICIT = re.compile(r"위험관리\s*책임자|리스크\s*관리\s*책임자|\bCRO\b|Chief\s*Risk", re.I)
CRO_HEAD = re.compile(r"리스크|위험관리")
HOLD_5CHA = {"KB금융지주": "KB금융", "신한금융지주": "신한지주", "하나금융지주": "하나금융지주",
             "우리금융지주": "우리금융지주", "메리츠금융지주": "메리츠금융지주", "iM금융지주": "iM금융지주",
             "NH농협금융지주": "농협금융지주", "한국투자금융지주": "한국금융지주"}


def build_cro():
    """원문_지주조직_CRO.csv — 5차 임원현황·직원현황·겸직현황(같은 원문 XML, sha256 대조)에서 지주 본체 직원 수와
    CRO. CRO 는 담당업무·직위에 위험관리책임자/CRO 가 **명시된** 임원, 없으면 리스크 담당 임원(사외이사·위원회
    위원 제외)을 「담당업무로 식별」로 따로 표시한다."""
    import hashlib
    rd = lambda f: list(csv.DictReader(open(os.path.join(risk8.HANDOFF, f), encoding="utf-8-sig")))
    off, emp, jik = rd("임원현황.csv"), rd("직원현황.csv"), rd("겸직현황_정리.csv")
    t = [r for r in _targets() if r["group"] == "A_지주사업보고서"]
    out = []
    for r in t:
        rc, lab = r["rcept_no"], r["corp_label"]
        name, at = doc_meta(rc)
        fy = _fy(r["report_nm"])
        o = dict(corp_label=lab, fy=fy, employees="", cro_name="", cro_title="", cro_career="",
                 cro_concurrent="", rcept_no=rc, doc_name=name, cro_basis="", cro_duty="",
                 page_employees="", page_cro="", collected_at=at, employees_source_text="",
                 cro_source_text="", note="", source_5cha_sha256="")
        offs = [x for x in off if x["rcept_no"] == rc]
        emps = [x for x in emp if x["rcept_no"] == rc]
        if not offs and not emps:
            o["note"] = ("본문 XML 없음(첨부정정 등) — 임원·직원 표 없음" if main_xml(rc) is None
                         else "5차 임원·직원 표에 이 접수번호 행 없음")
            for k in ("employees", "cro_name", "cro_title", "cro_career", "cro_concurrent"):
                o[k] = "문서에 없음"
            out.append(o)
            continue
        # 5차 행의 원문 sha256 = 지금 받은 zip 의 sha256 인지(같은 원문에서 나온 값인지)
        zp = os.path.join(OUT, "raw", "document", rc + ".zip")
        cur = hashlib.sha256(open(zp, "rb").read()).hexdigest() if os.path.exists(zp) else ""
        src = {x["raw_sha256"] for x in offs + emps}
        o["source_5cha_sha256"] = ", ".join(sorted(src))
        if cur and src != {cur}:
            o["note"] = "주의: 5차 행의 원문 sha256 이 지금 받은 원문과 다름"
        rngv = part_pages(rc, r"(VIII|Ⅷ)\.임원및직원등에관한사항", r"(IX|Ⅸ)\.계열회사등에관한사항")
        # 직원 수 — 직원 표의 「합 계」 행 여섯째 칸(직원 수 합계). 정규+기간제와 맞는지 대조만 한다
        tot = [x for x in emps if re.sub(r"\s+", "", x["원문행"].split("|")[0]) == "합계"]
        if tot:
            cells = [c.strip() for c in tot[0]["원문행"].split("|")]
            o["employees"] = cells[5] if len(cells) > 5 else ""
            o["employees_source_text"] = "[머리] %s ‖ [합계 행] %s" % (tot[0]["원문헤더"], tot[0]["원문행"])
            num = lambda v: 0 if v in ("-", "") else int(v.replace(",", "")) if v.replace(",", "").isdigit() else None
            a, b, s = num(cells[1]), num(cells[3]), num(o["employees"])
            if None not in (a, b, s) and a + b != s:
                o["note"] += " / 직원 합계 칸이 정규·기간제 합과 다름(원문 그대로 둠)"
            notes = [x["비고_원문"] for x in emps if x.get("비고_원문") and x["비고_원문"] != "-"]
            notes += [c for x in emps for c in [x["원문행"].split("|")[-1].strip()] if "겸직" in c]
            if notes:
                o["note"] += " / 직원 표 비고 원문: " + " ‖ ".join(dict.fromkeys(notes))
            o["page_employees"] = find_page(rc, "합계", *cells[1:6], within=rngv)
        else:
            o["employees"] = "문서에 없음"
        # CRO
        ex = [x for x in offs if CRO_EXPLICIT.search(x["담당업무"] + " " + x["직위"])]
        basis = "명시(담당업무·직위에 위험관리책임자/CRO)"
        if not ex:
            ex = [x for x in offs if CRO_HEAD.search(x["담당업무"]) and "소비자" not in x["담당업무"]
                  and "위원회" not in x["담당업무"] and "사외" not in x["직위"]]
            basis = "담당업무로 식별(위험관리책임자·CRO 표기 없음)"
        seen, picks = set(), []
        for x in ex:
            k = (x["성명"], x["담당업무"])
            if k not in seen:
                seen.add(k)
                picks.append(x)
        if not picks:
            for k in ("cro_name", "cro_title", "cro_career", "cro_concurrent"):
                o[k] = "문서에 없음"
        else:
            J = " ‖ ".join
            o.update(cro_name=J(x["성명"] for x in picks), cro_title=J(x["직위"] for x in picks),
                     cro_career=J(x["주요경력"] for x in picks), cro_duty=J(x["담당업무"] for x in picks),
                     cro_basis=basis,
                     cro_source_text=J("[머리] %s ‖ [행] %s" % (x["원문헤더"], x["원문행"]) for x in picks))
            names = {x["성명"] for x in picks}
            # 겸직자 칸은 「양재영 (주)」·「오종원(미등기임원)」처럼 이름 뒤에 글자가 붙기도 한다 — 이름으로 시작하면 같은 사람
            js = [x for x in jik if x["rcept_no"] == rc and x["겸직회사"]
                  and any(re.sub(r"\s+", "", x["겸직자"]).startswith(n) for n in names)]
            o["cro_concurrent"] = J(dict.fromkeys("%s: %s %s%s [%s]" % (x["겸직자"], x["겸직회사"],
                                                                     x["겸직회사_직위"],
                                                                     " (%s)" % x["겸직일자"] if x["겸직일자"] else "",
                                                                     x["출처유형"]) for x in js)) or "문서에 없음"
            if len(picks) > 1:
                o["note"] += " / CRO 후보 %d명(기간 중 교체·표 중복 가능) — 모두 적음" % len(picks)
            o["page_cro"] = find_page(rc, picks[0]["성명"], picks[0]["담당업무"][:12], within=rngv)
            if not o["page_cro"] and rngv:       # 담당업무 글이 PDF 에서 끊긴 경우 — Ⅷ 장에서 이름이 한 쪽뿐이면 그 쪽
                hits = [n for n in range(rngv[0], rngv[1] + 1)
                        if risk8._nows(picks[0]["성명"]) in pages_of(rc).get(n, "")]
                if len(hits) == 1:
                    o["page_cro"] = hits[0]
                    o["note"] += " / CRO 쪽은 Ⅷ 장에서 성명이 나오는 유일한 쪽"
        o["note"] = o["note"].strip(" /")
        out.append(o)
    _attach_md("지주조직_CRO", out, ["page_employees", "page_cro"])
    cols = ["corp_label", "fy", "employees", "cro_name", "cro_title", "cro_career", "cro_concurrent", "rcept_no",
            "doc_name", "page_employees", "page_cro", "collected_at", "cro_basis", "cro_duty",
            "employees_source_text", "cro_source_text", "note", "원문_md", "source_5cha_sha256"]
    risk8._w(os.path.join(risk8.HANDOFF, "원문_지주조직_CRO.csv"), out, cols)
    print("원문_지주조직_CRO.csv %d행 · CRO 명시 %d · 담당업무 식별 %d · 없음 %d"
          % (len(out), sum(1 for o in out if o["cro_basis"].startswith("명시")),
             sum(1 for o in out if o["cro_basis"].startswith("담당업무")),
             sum(1 for o in out if o["cro_name"] == "문서에 없음")))
    return out


# ── 작업 3 — 내부회계 ─────────────────────────────────────────────────────
def rel_year(cell):
    """「제18기(당기)」·「제5(당)기」·「제17기(전기)」·「제3(전전)기」 → 0/1/2. 아니면 None."""
    n = re.sub(r"\s+", "", cell or "")
    if not re.search(r"당기|\(당\)|전기|\(전\)|전전", n):
        return None
    if "전전" in n:
        return 2
    if "전기" in n or "(전)" in n:
        return 1
    return 0


NO_OPINION = re.compile(r"^(-|해당사항없음|해당없음|없음|—)?$")


def icfr_rows(rc):
    """Ⅴ 장의 감사인 내부회계관리제도 의견 표 → [(사업연도칸, 구분, 감사인, 유형, 의견, 원문행, 서식)].
    서식 A(FY2024~): 사업연도|구분|감사인|유형(감사/검토)|감사의견 또는 검토결론|…
    서식 B(FY2023 등): 사업연도|감사인|감사의견|중대한 취약점… — 의견 문장 하나에 별도·연결을 함께 적는다."""
    import docparse
    x = main_xml(rc)
    if x is None:
        return None
    off, sl = part(x, "V|Ⅴ", "VI|Ⅵ")
    if off is None:
        return []
    secs, _err = docparse.parse_document(sl)
    out = []
    for s in secs:
        for t in s["tables"]:
            g = grid(t)
            if not g:
                continue
            txt = " ".join(c[0] for row in g for c in row)
            if "내부회계" not in txt or "보수" in txt and "시간" in txt:
                continue
            kisu = lambda cell: (int(re.search(r"제\s*(\d+)\s*(?:\(.{0,3}\))?\s*기", cell).group(1))
                                 if re.search(r"제\s*(\d+)\s*(?:\(.{0,3}\))?\s*기", cell or "") else None)
            first = next((i for i, row in enumerate(g)
                          if rel_year(row[0][0]) is not None or kisu(row[0][0]) is not None), None)
            if first is None or first == 0:
                continue
            head = [" ".join(dict.fromkeys(g[i][j][0] for i in range(first) if g[i][j][0])).strip()
                    for j in range(len(g[0]))]
            hn = [re.sub(r"\s+", "", h) for h in head]
            col = lambda *ks: next((j for j, h in enumerate(hn) if any(k in h for k in ks)), None)
            c_aud, c_op = col("감사인"), col("감사의견", "검토결론", "의견")
            if c_aud is None or c_op is None:
                continue
            c_kind, c_type = col("구분"), col("유형")
            fmt = "A" if c_kind is not None and c_type is not None else "B"
            # 「당기·전기」 표시가 없고 「제14기」처럼 기수만 있으면, 표 안 가장 큰 기수를 당기로 보고 차이를 센다
            ks = [kisu(row[0][0]) for row in g[first:] if kisu(row[0][0]) is not None]
            for row in g[first:]:
                yr = row[0][0]
                rel = rel_year(yr)
                if rel is None and kisu(yr) is not None and ks:
                    rel = max(ks) - kisu(yr)
                if rel is None:
                    continue
                out.append(dict(yr=yr, rel=rel, kind=row[c_kind][0] if c_kind is not None else "",
                                auditor=row[c_aud][0], type=row[c_type][0] if c_type is not None else "",
                                opinion=row[c_op][0], fmt=fmt, header=" | ".join(head),
                                rowtext=" | ".join(dict.fromkeys(c[0] for c in row if c[0]))))
    return out


def _attach_text(pdf):
    """첨부 PDF → {쪽: 글}(캐시 dart_out/text/risk9/첨부/). 실패하면 {}."""
    import hashlib
    import pypdf
    if not pdf or not os.path.exists(pdf):
        return {}
    d = os.path.join(TEXT, "첨부")
    os.makedirs(d, exist_ok=True)
    h = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    tp = os.path.join(d, h[:16] + ".txt")
    if not os.path.exists(tp):
        try:
            parts = []
            for i, pg in enumerate(pypdf.PdfReader(pdf).pages, 1):
                try:
                    parts.append("=== p.%d ===\n%s" % (i, pg.extract_text() or ""))
                except Exception:                     # noqa: BLE001
                    parts.append("=== p.%d === [추출 실패]" % i)
            with open(tp, "w", encoding="utf-8") as f:
                f.write("\n".join(parts) + "\n")
        except Exception:                             # noqa: BLE001
            return {}
    return {n: t for n, t in risk8.re_split_pages(open(tp, encoding="utf-8").read())}


def icfr_attach(rc):
    """본문 Ⅴ 장에 의견 표가 없을 때 — 첨부 감사보고서(별도 _00760)·연결감사보고서(_00761)의
    「내부회계관리제도 감사의견 또는 검토의견」 절에서 「우리의 의견으로는 … 내부회계관리제도는 …」 문장(원문 그대로)."""
    import html as _h
    import zipfile
    zp = os.path.join(OUT, "raw", "document", rc + ".zip")
    if not os.path.exists(zp):
        return []
    z = zipfile.ZipFile(zp)
    adir = os.path.join(OUT, "doc", rc, "첨부")
    files = os.listdir(adir) if os.path.isdir(adir) else []
    out = []
    for member, scope, pdf_pat in ((rc + "_00760.xml", "별도", r"^\d+_\[.*\](?!연결)감사보고서.*\.pdf$"),
                                   (rc + "_00761.xml", "연결", r"^\d+_\[.*\]연결감사보고서.*\.pdf$")):
        if member not in z.namelist():
            continue
        import docparse
        t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", docparse.decode_document(z.read(member))[0])))
        heads = [m.start() for m in re.finditer(r"내부회계관리제도\s*(감사의견|검토의견|감사보고서|검토보고서)", t)]
        body = [h for h in heads if "‥" not in t[h:h + 80]]          # 목차 줄(‥‥ 쪽번호) 제외
        if not body:
            continue
        seg = t[body[0]:]
        m = re.search(r"우리의\s*의견으로는[^.]*?내부회계관리제도는[^.]*?(있습니다|않습니다|못합니다)\.", seg)
        if not m:
            continue
        sent = m.group(0)
        ty = ("감사" if re.search(r"내부회계관리제도\s*감사(보고서|의견)", seg[:3000]) else
              "검토" if re.search(r"내부회계관리제도\s*검토(보고서|의견)", seg[:3000]) else "")
        pdf = next((os.path.join(adir, f) for f in sorted(files) if re.match(pdf_pat, f)), "")
        P = _attach_text(pdf)
        pg = next((n for n in sorted(P) if risk8._nows(sent[:40]) in risk8._nows(P[n])), "")
        out.append(dict(scope=scope, type=ty, opinion=sent, member=member,
                        pdf=os.path.basename(pdf), page=pg))
    return out


def build_icfr():
    """원문_지주내부회계.csv — FY2023~FY2025 사업보고서(정정본 포함) 각 본의 「당기」 행. 전기·전전기 행은
    연결 내부회계 첫 적용연도 관찰에만 쓴다(값을 옮기지 않는다)."""
    t = [r for r in _targets() if r["group"] == "A_지주사업보고서"]
    comp = {}
    p = os.path.join(WORK, "지주_기업개황.csv")
    if os.path.exists(p):
        comp = {r["corp_label"]: r for r in csv.DictReader(open(p, encoding="utf-8-sig"))}
    cls_name = {"Y": "상장(유가증권시장)", "K": "상장(코스닥)", "N": "상장(코넥스)", "E": "비상장(기타법인)"}
    out, seen_cons = [], {}
    for r in t:
        rc, lab = r["rcept_no"], r["corp_label"]
        fy = _fy(r["report_nm"])
        name, at = doc_meta(rc)
        cm = comp.get(lab, {})
        listed = ("%s — 기업개황 corp_cls=%s, 종목코드 %s" % (cls_name.get(cm.get("corp_cls"), cm.get("corp_cls")),
                                                         cm.get("corp_cls"), cm.get("stock_code") or "없음")
                  if cm else "")
        rows = icfr_rows(rc)
        base = dict(corp_label=lab, fy=fy, listed=listed, rcept_no=rc, doc_name=name, collected_at=at)
        if rows is None:
            out.append(dict(base, icfr_scope="문서에 없음", opinion_type="문서에 없음", opinion="문서에 없음",
                            source_text="문서에 없음", page="", note="본문 XML 없음(첨부정정 등)"))
            continue
        # 연결 첫 적용 관찰: 이 본의 모든 행(당기·전기·전전기)을 사업연도로 바꿔, 연결 의견이 실제로 있는가
        for x in rows:
            has_op = not NO_OPINION.match(re.sub(r"\s+", "", x["opinion"]))
            cons = has_op and ("연결" in x["kind"] if x["fmt"] == "A" else "연결" in x["opinion"])
            seen_cons.setdefault(lab, []).append((int(fy) - x["rel"], cons, rc, x["yr"]))
        cur = [x for x in rows if x["rel"] == 0]
        rng = part_pages(rc, r"(V|Ⅴ)\.회계감사인의감사의견등", r"(VI|Ⅵ)\.이사회등회사의기관에관한사항")
        if not cur:
            att = icfr_attach(rc)
            for a_ in att:
                out.append(dict(base, icfr_scope=a_["scope"], opinion_type=a_["type"] or "문서에 없음",
                                opinion=a_["opinion"], doc_name=base["doc_name"] + " 첨부 " + a_["pdf"],
                                source_text="[첨부 %s · %s] %s" % (a_["pdf"], a_["member"], a_["opinion"]),
                                page=a_["page"],
                                note="본문 Ⅴ 장에 감사인 내부회계 의견 표 없음 — 첨부 %s 의 「내부회계관리제도 "
                                     "감사의견 또는 검토의견」 절 문장(쪽은 첨부 PDF 쪽)" % a_["pdf"]))
                seen_cons.setdefault(lab, []).append((int(fy), a_["scope"] == "연결", rc, "첨부 " + a_["scope"]))
            if not att:
                out.append(dict(base, icfr_scope="문서에 없음", opinion_type="문서에 없음", opinion="문서에 없음",
                                source_text="문서에 없음", page="",
                                note="Ⅴ 장에서 감사인의 내부회계 의견 표(당기 행)를 못 찾음 — 찾은 표 %d행, 첨부 감사보고서에도 "
                                     "내부회계 의견 문장 없음" % len(rows)))
            continue
        for x in cur:
            if x["fmt"] == "A":
                scopes = [("연결" if "연결" in x["kind"] else "별도", x["type"], "표 「유형」 열")]
            else:
                ty = ("감사" if re.search(r"감사의견", x["opinion"]) else
                      "검토" if re.search(r"검토(의견|결론|결과)", x["opinion"]) else "")
                # 의견 문장이 어느 제도를 말하는가: 「회사의 내부회계관리제도」(별도)·「연결…내부회계관리제도」(연결)
                op = re.sub(r"\s+", "", x["opinion"])
                scopes = []
                if re.search(r"회사의내부회계관리제도|\[내부회계관리제도|\[감사의견\]회사의내부회계", op):
                    scopes.append(("별도", ty, "의견 문구(「회사의 내부회계관리제도」)"))
                if re.search(r"연결(내부회계|회사의연결|기업의연결)", op) or "연결내부회계관리제도" in op:
                    scopes.append(("연결", ty, "의견 문구(「연결…내부회계관리제도」)"))
                if not scopes:
                    scopes = [("문서에 없음", ty, "의견 문구에 별도·연결 표기 없음")]
            for sc, ty, tsrc in scopes:
                pg = find_page(rc, x["yr"], x["auditor"], x["opinion"][:25], within=rng) or \
                     find_page(rc, x["opinion"][:25], within=rng)
                note = "서식 %s · 유형 근거: %s" % (x["fmt"], tsrc)
                if not ty:
                    note += (" · 의견 표·문구에 감사/검토 표기 없음 — 참고: Ⅴ-1 감사용역 표 「%s」"
                             % ("별도/연결내부회계관리제도감사" if "내부회계관리제도감사" in (main_xml(rc) or "") else "기재 없음"))
                if x["fmt"] == "B" and len(scopes) > 1:
                    note += " · 의견 칸 하나가 별도·연결을 함께 적음(같은 원문을 두 행에)"
                out.append(dict(base, icfr_scope=sc, opinion_type=ty or "문서에 없음", opinion=x["opinion"],
                                source_text="[머리] %s ‖ [행] %s" % (x["header"], x["rowtext"]),
                                page=pg, note=note))
    # 연결 내부회계 첫 적용 사업연도(관찰): FY2023~FY2025 본들의 당기·전기·전전기 행을 사업연도로 바꿔,
    # 연결 의견이 처음 나오는 해와 그 직전 해(연결 의견 없음)가 둘 다 표에 있을 때만 그 해를 적는다.
    for lab, obs in seen_cons.items():
        yrs = {}
        for y, cons, rc, cell in obs:
            yrs.setdefault(y, []).append((cons, rc, cell))
        firsts = sorted(y for y, v in yrs.items() if any(c for c, _r, _cl in v))
        if not firsts:
            val = "문서에 없음 — FY%d~FY%d 행에 연결 내부회계 의견 없음" % (min(yrs), max(yrs))
        else:
            f = firsts[0]
            prev = yrs.get(f - 1)
            # 근거는 그 사업연도 본의 「당기」 행을 먼저 든다
            evs = sorted([(rel_year(cl) if rel_year(cl) is not None else 9, r, cl) for c, r, cl in yrs[f] if c])
            ev = "%s 「%s」" % (evs[0][1], evs[0][2]) if evs else ""
            if prev and not any(c for c, _r, _cl in prev):
                pev = "%s 「%s」" % (prev[0][1], prev[0][2])
                val = "FY%d (관찰: %s 에 연결 의견, 직전 FY%d 행 %s 에는 없음)" % (f, ev, f - 1, pev)
            else:
                val = "FY%d 이전일 수 있음(표에 그 앞 해가 없음 — 관찰: %s)" % (f, ev)
        for o in out:
            if o["corp_label"] == lab:
                o["first_consolidated_fy"] = val
    _attach_md("지주내부회계", out, ["page"])
    cols = ["corp_label", "fy", "listed", "icfr_scope", "opinion_type", "opinion", "first_consolidated_fy",
            "source_text", "rcept_no", "doc_name", "page", "collected_at", "note", "원문_md"]
    for o in out:
        o.setdefault("first_consolidated_fy", "문서에 없음")
    risk8._w(os.path.join(risk8.HANDOFF, "원문_지주내부회계.csv"), out, cols)
    print("원문_지주내부회계.csv %d행 · 쪽 못 찾음 %d" % (len(out), sum(1 for o in out if not o["page"] and o["opinion"] != "문서에 없음")))
    return out


# ── 작업 2 — 비은행지주 자본 지표 ──────────────────────────────────────────
NONBANK_EVIDENCE = {
    # 비은행지주 해당 여부 — 원문 문장(사업보고서 FY2025). 판정이 아니라 회사 스스로 적은 문장이다.
    "메리츠금융지주": ("20260318001419", "국내 금융지주회사는 은행을 자회사로 지배하는 은행지주회사와 은행을 지배하지 않는 비은행지주회사로 크게 구분되며, 비은행지주회사는 다시 보험회사를 지배하는보험지주회사와 보험회사를 지배하지 않는 금융투자지주회사 등으로 구분됩니다. 국내 금융지주회사는 대부분 은행지주회사 형태이며, 보험지주회사는 당사가 유일합니다."),
    "한국투자금융지주": ("20260319001006", "그러나 2019년 11월 보유한 한국카카오은행 지분을 매각하여 비은행금융지주로 다시 전환됨에 따라 자본적정성 지표를 BIS비율에서 필요자본대비 자기자본비율로 적용하여 산정하고 있습니다."),
}
METRICS = [
    # (metric, 행 이름 판정, 제외)
    ("필요자본 대비 자기자본비율", re.compile(r"필요자본.*(대비|에대한).*자기자본.*비율|자기자본비율.*필요자본"), None),
    ("부채비율", re.compile(r"^부채비율"), re.compile(r"자산부채")),
    ("이중레버리지비율", re.compile(r"이중레버리지"), None),
]
SUB_HEAD = re.compile(r"주요\s*종속회사|주요\s*자회사|종속회사에\s*관한\s*사항")


def _period(report_nm):
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    return ("%s-Q%d" % (m.group(1), int(m.group(2)) // 3)) if m else ""


def _num(v):
    v = (v or "").strip().replace(",", "").replace("%", "")
    return bool(re.match(r"^[△\-]?\d+(\.\d+)?$", v))


def capital_rows(rc):
    """Ⅱ 장 표에서 지주 본체의 자본 지표와 보험 자회사 지급여력비율. 표의 첫 값 열(당기)을 그 머리와 함께."""
    import docparse
    x = main_xml(rc)
    if x is None:
        return None
    off, sl = part(x, "II|Ⅱ", "III|Ⅲ")
    if off is None:
        return []
    secs, _ = docparse.parse_document(sl)
    # 지주 본체 / 자회사 경계: 「재무건전성 등 기타 참고사항」 절 안의 대괄호 표제 「[주요종속회사…]」·「[주요 자회사…]」
    mt = re.search(r"<TITLE[^>]*>[^<]*재무건전성", sl)
    base = mt.start() if mt else 0
    # 「[지배회사에 관한 사항…]」 표제 중 뒤에 자본 지표가 이어지는 것(사업 개요의 같은 표제는 건너뜀)
    # 표제는 「[지배회사에 관한 사항…]」 또는 지주 이름 「[한국투자금융지주]」(옛 서식)
    for hb in re.finditer(r"\[\s*(지배회사에\s*관한\s*사항|한국투자금융지주|한국금융지주|메리츠금융지주)", sl[base:]):
        nxt = re.sub(r"<[^>]+>", " ", sl[base + hb.start(): base + hb.start() + 3000])
        if re.search(r"필요자본|자본적정성|부채비율|자기자본", nxt):
            base = base + hb.start()
            break
    # 자회사 구간 시작: 「[주요종속회사…]」·「[주요 자회사…]」 또는 자회사 이름 대괄호(옛 서식 「[한국투자증권]」 등)
    m2 = re.search(r"\[\s*(주요\s*(종속\s*회사|자회사)|[^\]\[]{0,20}(증권|저축은행|캐피탈|화재|해상|자산운용|신탁|파트너스|생명)\s*\])",
                   sl[base + 20:])                      # +20: 지주 표제 자신은 건너뛴다
    sub_at = base + 20 + m2.start() if m2 else None
    out = []
    for s in secs:
        for ti, t in enumerate(s["tables"]):
            g = grid(t)
            if not g or len(g) < 2:
                continue
            flat = " ".join(c[0] for row in g for c in row)
            if "소속회사수" in re.sub(r"\s+", "", flat):          # 금융지주 업계 현황표 — 회사 수치 아님
                continue
            holding = t["start"] >= base and (sub_at is None or t["start"] < sub_at)
            ctx = _ptexts(sl[max(0, t["start"] - 1500): t["start"]])
            # 단위: 표 자신의 단위 칸 → 바로 앞의 칸 하나짜리 「(단위 : …)」 표 → 앞 문단
            pt = s["tables"][ti - 1] if ti > 0 else None
            pt_txt = " ".join(c["text"] for row in (pt or {}).get("rows", []) for c in row) if pt else ""
            unit = (t.get("unit_hint", "")
                    or (pt_txt if pt and len(pt_txt) < 60 and "단위" in pt_txt and t["start"] - pt["start"] < 3000 else "")
                    or next((c for c in reversed(ctx[-3:]) if "단위" in c), ""))
            t = dict(t, unit_hint=unit)
            head = [c[0] for c in g[0]]
            for r_i, row in enumerate(g[1:], 1):
                label = re.sub(r"\s+", "", row[0][0])
                cands = []
                for metric, ok_re, ex_re in METRICS:
                    if ok_re.search(label) and not (ex_re and ex_re.search(label)) and holding:
                        cands.append(metric)
                if "지급여력비율" in label and not holding:
                    cands.append("지급여력비율(보험 자회사)")
                for metric in cands:
                    # 당기 칸 = 행 이름 다음의 첫 값 열(머리가 「구분」인 칸은 건너뜀). 숫자가 아니어도(예: 「주3)」)
                    # 그 칸을 그대로 쓴다 — 옆 칸(전기)으로 넘어가면 지난 값이 이번 분기 값으로 둔갑한다.
                    j = next((j for j in range(1, len(row)) if "구분" not in re.sub(r"\s+", "", head[j] if j < len(head) else "")), None)
                    if j is None:
                        continue
                    out.append(dict(metric=metric, value=row[j][0], col_header=head[j] if j < len(head) else "",
                                    row_label=row[0][0], unit=t.get("unit_hint", ""),
                                    context=" / ".join(c for c in ctx[-3:] if c)[:200],
                                    row_text=" | ".join(c[0] for c in row), head_text=" | ".join(head),
                                    table=ti, holding=holding))
            # 원화유동성비율 — 회사명 행(지주회사) × 「원화 유동성비율」 열, 또는 「원화유동성비율」 소제목 뒤 표의 비율 행
            hn = [re.sub(r"\s+", "", " ".join(dict.fromkeys(g[i][j][0] for i in range(min(2, len(g))))))
                  for j in range(len(g[0]))]
            ctx_txt = re.sub(r"\s+", "", " ".join(ctx[-3:]))
            if holding and (any("원화유동성비율" in h for h in hn) or "원화유동성비율" in ctx_txt
                            or "원화유동성비율" in re.sub(r"\s+", "", flat[:200])):
                cols = [j for j, h in enumerate(hn) if "유동성비율" in h]
                for row in g[1:]:
                    lab = re.sub(r"\s+", "", " ".join(c[0] for c in row[:2]))
                    if cols and ("지주" in lab or "합계" in lab or "지주회사" in lab):
                        j = cols[0]
                        if True:                                   # 숫자가 아니어도 그 칸 그대로(아래에서 표시)
                            out.append(dict(metric="원화유동성비율", value=row[j][0], col_header=hn[j],
                                            row_label=" ".join(c[0] for c in row[:2]), unit=t.get("unit_hint", ""),
                                            context=" / ".join(ctx[-3:])[:200],
                                            row_text=" | ".join(c[0] for c in row),
                                            head_text=" | ".join(hn), table=ti, holding=True))
                            break
                    elif not cols and re.search(r"유동성비율", lab):
                        j = 1 if len(row) > 1 else None
                        if j is not None:
                            out.append(dict(metric="원화유동성비율", value=row[j][0],
                                            col_header=g[0][j][0], row_label=row[0][0],
                                            unit=t.get("unit_hint", ""), context=" / ".join(ctx[-3:])[:200],
                                            row_text=" | ".join(c[0] for c in row),
                                            head_text=" | ".join(c[0] for c in g[0]), table=ti, holding=True))
                            break
    return out


def build_capital():
    """원문_비은행지주_자본지표.csv — 2021.1Q~최신 분기 분기·반기·사업보고서(정정본 포함) 각 본의 당기 값."""
    # B 그룹 목록 그대로(지주 사업보고서 묶음 A 와 겹치는 FY2023~25 사업보고서도 여기 포함)
    t = [r for r in csv.DictReader(open(os.path.join(WORK, "DART_목록.csv"), encoding="utf-8-sig"))
         if r["group"] == "B_비은행지주정기" and r["rcept_no"]]
    out = []
    for r in t:
        rc, lab = r["rcept_no"], r["corp_label"]
        name, at = doc_meta(rc)
        per = _period(r["report_nm"])
        kind = re.search(r"(분기|반기|사업)보고서", r["report_nm"]).group(0)
        rows = capital_rows(rc)
        base = dict(corp_label=lab, period=per, doc_kind=kind, rcept_no_or_url=rc, doc_name=name,
                    collected_at=at)
        if rows is None:
            for m, _a, _b in METRICS + [("원화유동성비율", None, None)]:
                out.append(dict(base, metric=m, value="문서에 없음", unit="", page="", source_text="",
                                note="본문 XML 없음(첨부정정 등)"))
            continue
        rng = part_pages(rc, r"(II|Ⅱ)\.사업의내용", r"(III|Ⅲ)\.재무에관한사항")
        import html as _h
        xx = main_xml(rc) or ""
        plain = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", xx)))
        narr = re.findall(r"[^.]*필요자본\s*대비\s*자기자본\s*비율은[^.]*?\d+\.\d+\s*%[^.]*\.", plain)[:3]
        got = {}
        for x in rows:
            got.setdefault(x["metric"], []).append(x)
        for m in [m for m, _a, _b in METRICS] + ["원화유동성비율"] + \
                 (["지급여력비율(보험 자회사)"] if lab == "메리츠금융지주" else []):
            xs = got.get(m, [])
            if not xs:
                why = "Ⅱ 장 표에서 「%s」 행을 못 찾음(업계 현황표·자회사 표 제외)" % m
                if m == "이중레버리지비율":
                    why += "; 같은 회사 2026.2Q 경영공시(dart_out/text/risk8/경영공시__*.txt)에도 「이중레버리지」 어휘 0건"
                out.append(dict(base, metric=m, value="문서에 없음", unit="", page="", source_text="", note=why))
                continue
            seen = set()
            for x in xs:
                k = (x["value"], x["col_header"], x["row_label"])
                if k in seen:
                    continue
                seen.add(k)
                val, extra = x["value"], ""
                if not _num(val):                      # 당기 칸이 숫자가 아님 — 값은 비우고 원문 칸을 note 에
                    extra = " · 당기 칸 원문 「%s」(숫자 아님 — 옆 칸 값은 옮기지 않음)" % val
                    val = risk8.NOT_FOUND
                pg = find_page(rc, x["row_label"], x["value"], within=rng)
                note = "값 열 머리 「%s」(당기 칸) · 맥락: %s%s" % (x["col_header"], x["context"][:120], extra)
                if m == "필요자본 대비 자기자본비율":     # 같은 본 서술문에 다른 값이 있으면 원문 그대로 적는다(판정 없음)
                    for sent in narr:
                        nums = re.findall(r"(\d+\.\d+)\s*%", sent)
                        if nums and val not in nums:
                            note += " · 같은 본 서술문(값 다름): 「%s」" % sent[:160]
                if len(xs) > 1:
                    note += " · 같은 본에 이 지표 행이 %d개" % len(xs)
                out.append(dict(base, metric=m, value=val, unit=x["unit"], page=pg,
                                source_text="[머리] %s ‖ [행] %s" % (x["head_text"], x["row_text"]),
                                note=note))
    for lab, (rc, sent) in NONBANK_EVIDENCE.items():
        for o in out:
            if o["corp_label"] == lab:
                o["note"] = ("비은행지주 해당(원문 %s: 「%s」) / " % (rc, sent[:60] + "…")) + o["note"]
    _attach_md("비은행지주_자본지표", out, ["page"], rc_col="rcept_no_or_url")
    cols = ["corp_label", "period", "metric", "value", "unit", "doc_kind", "rcept_no_or_url", "doc_name", "page",
            "collected_at", "source_text", "note", "원문_md"]
    risk8._w(os.path.join(risk8.HANDOFF, "원문_비은행지주_자본지표.csv"), out, cols)
    import collections
    print("원문_비은행지주_자본지표.csv %d행 · 문서에 없음 %d · %s"
          % (len(out), sum(1 for o in out if o["value"] == "문서에 없음"),
             dict(collections.Counter((o["corp_label"], o["metric"]) for o in out if o["value"] != "문서에 없음"))))
    return out


# ── 작업 4 — 보험 자회사 ───────────────────────────────────────────────────
INS_SELECTION = os.path.join(HERE, "data", "risk9_보험자회사_선별.json")


def build_insurers():
    """원문_보험자회사_지주연계.csv — 선별(risk9_보험자회사_선별.json: 원문 그대로 인용) → CSV. 제출 대상 확인은
    OpenDART 목록(DART_목록.csv, C_보험자회사)."""
    import json
    sel = json.load(open(INS_SELECTION, encoding="utf-8"))["rows"]
    lst = [r for r in _targets() if r["group"] == "C_보험자회사"]
    nolist = [r for r in csv.DictReader(open(os.path.join(WORK, "DART_목록.csv"), encoding="utf-8-sig"))
              if r["group"] == "C_보험자회사" and not r["rcept_no"]]
    out = []
    for x in sel:
        rc = x.get("doc_id", "")
        name, at = doc_meta(rc) if rc else ("", "")
        out.append(dict(corp_label=x["corp_label"], parent=x.get("parent", ""), fy=x.get("fy", "FY2025"),
                        topic=x.get("topic", ""), source_text=x["quote"], rcept_no_or_url=rc, doc_name=name,
                        section=x.get("section", ""), page=x.get("page", ""), collected_at=at,
                        note=x.get("note", "")))
    for r in nolist:                 # 제출 없음(목록 확인) — 선별에 없으면 여기서 채운다
        if not any(o["corp_label"] == r["corp_label"] for o in out):
            out.append(dict(corp_label=r["corp_label"], parent=INSURERS.get(r["corp_label"], ("", ""))[1], fy="FY2025", topic="",
                            source_text=risk8.NOT_FOUND, rcept_no_or_url="", doc_name="", section="", page="",
                            collected_at=r.get("list_at", ""),
                            note="사업보고서 제출 없음 — " + r["note"]))
    # 정정본 대조(판정 없이): 같은 회사의 다른 본에도 같은 문구가 있는가
    for o in out:
        if o["source_text"] == risk8.NOT_FOUND or not o["rcept_no_or_url"]:
            continue
        others = [r["rcept_no"] for r in lst if r["corp_label"] == o["corp_label"] and r["rcept_no"] != o["rcept_no_or_url"]]
        res = []
        rnm = {r["rcept_no"]: r["report_nm"] for r in lst}
        for rc in others:
            P = pages_of(rc)
            if not P:
                res.append("%s: 텍스트 없음" % rc)
                continue
            if "첨부정정" in rnm.get(rc, "") or main_xml(rc) is None:
                res.append("%s %s: 본문 없는 정정(첨부만) — 대조 불가" % (rc, rnm.get(rc, "")))
                continue
            res.append("%s: %s" % (rc, "같은 문구 있음" if any(risk8._nows(o["source_text"]) in t for t in P.values())
                                   else "같은 문구 없음"))
        if res:
            o["note"] = (o["note"] + " / " if o["note"] else "") + "다른 본 대조(판정 없음): " + "; ".join(res)
    _attach_md("보험자회사_지주연계", out, ["page"], rc_col="rcept_no_or_url")
    cols = ["corp_label", "parent", "fy", "topic", "source_text", "rcept_no_or_url", "doc_name", "section", "page",
            "collected_at", "note", "원문_md"]
    risk8._w(os.path.join(risk8.HANDOFF, "원문_보험자회사_지주연계.csv"), out, cols)
    print("원문_보험자회사_지주연계.csv %d행 · 문서에 없음 %d" % (len(out), sum(1 for o in out if o["source_text"] == risk8.NOT_FOUND)))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    fn = {"fetch-list": fetch_list, "fetch-doc": fetch_doc, "fetch-viewer": fetch_viewer,
          "fetch-conv-names": fetch_conv_names,
          "build-activity": build_activity, "build-cro": build_cro, "build-icfr": build_icfr,
          "build-capital": build_capital, "build-insurers": build_insurers,
          "extract": lambda: extract(argv[2].split(",") if len(argv) > 2 else None)}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    fn()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
