# -*- coding: utf-8 -*-
"""13차 9-2 의 3·5번 — 세칙 [별표 37] 번호 항목 대조, [별표 22](K-ICS) 위험 분류 제목 줄. 실행은 저장소 루트에서.

    LAW_DELAY=1.0 python3 scripts/dart/web13_law92b.py check    # 세칙 현행 판 재확인(lawSearch admrul 1회)
    python3 scripts/dart/web13_law92b.py extract                 # 9차 세칙 XML 에서 별표 22·22-1·37 별표내용만 떼어 냄
    python3 scripts/dart/web13_law92b.py a37                     # 별표37: 10차 md(hwp) ↔ PDF 텍스트 ↔ XML 별표내용 대조
    python3 scripts/dart/web13_law92b.py a22                     # 별표22: 장·절·항 제목 줄 목록과 위험 분류 줄
    python3 scripts/dart/web13_law92b.py build                   # 산출 md(요청 없음)

원칙(13차 COMMON13.md):
  - 법제처 OC 는 lawclient 가 env/.env 에서 읽고, 원장·메타·산출물에는 OC=*** 로만 남는다.
    원장: dart_out/raw/web13/law92b/_call_log.csv, LAW_DELAY=1.0 이상.
  - 이미 받은 XML(web9)은 다시 받지 않는다. 현행 판이 9차 판(2200000108939)과 다를 때만 새 판을 받는다.
  - 원문은 글자 그대로 옮긴다(공백·줄바꿈 정리 없음). 해설은 md 의 「note:」 줄에만.
  - 큰 중간 결과는 dart_out/raw/web13/law92b/ 에 파일로 두고 화면에는 요약만 찍는다.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
from web13 import RAW, WORK, OUT, save, now, write_csv  # noqa: E402

TASK = "law92b"
D = os.path.join(RAW, TASK)
LEDGER = os.path.join(D, "_call_log.csv")
SEC = "보험업감독업무시행세칙"
SEC_SERIAL9 = "2200000108939"
SEC_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독업무시행세칙_%s.xml" % SEC_SERIAL9)
SIB_HIST = os.path.join(RAW, "law92", "연혁목록_보험업감독업무시행세칙.json")   # 같은 날 다른 에이전트(9-2 1·2번)가 받은 연혁 목록
A37_MD10 = os.path.join("handoff", "원문_10차", "세칙_별표37.md")
A37_PDF10 = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37_pdf.txt")
A37_PDF10_BIN = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37.pdf")
OUT_MD = os.path.join(OUT, "9-2-3_5_별표37_별표22.md")
A37_ITEMS_CSV = os.path.join(WORK, "9-2-3_별표37_항목대조.csv")
A37_DIFF_CSV = os.path.join(WORK, "9-2-3_별표37_줄대조.csv")
A22_CSV = os.path.join(WORK, "9-2-5_별표22_제목줄.csv")
MOBEOM_CSV = os.path.join(WORK, "모범규준_조목록.csv")
CHECK_JSON = os.path.join(D, "현행확인.json")
TODAY = "20261007"


def _t(e, tag):
    return (e.findtext(tag) or "").strip()


def _nosp(s):
    return re.sub(r"\s+", "", s or "")


def sha(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def meta_of(p):
    mp = p + ".meta.json"
    return json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}


# ── 현행 판 재확인 ─────────────────────────────────────────────────────────
def check():
    """lawSearch.do target=admrul query=세칙 (nw 생략 = 현행) 1회. 응답의 상세링크에 실린 OC 는 저장 전 가린다."""
    import lawclient
    client = lawclient.LawClient(LEDGER)
    st, body, murl, host = client.api("lawSearch.do", target="admrul", type="XML", query=SEC, display="20")
    if not body:
        raise SystemExit("현행 확인 실패: %s" % murl)
    n_oc = client.count_oc(body)
    body = client.mask(body)
    p, meta = save(TASK, "현행검색_%s.xml" % SEC, body,
                   dict(출처URL=murl, http_status=st, fetched_at=now(), 호스트=host,
                        질의="lawSearch.do target=admrul query=%s type=XML display=20 (nw 생략)" % SEC,
                        OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈(원 응답 바이트와 sha256 다름)" % n_oc)
                        if n_oc else ""))
    root = ET.fromstring(body)
    rows = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("admrul")]
    same = [r for r in rows if r.get("행정규칙명") == SEC]
    keep = [{k: r.get(k, "") for k in ("행정규칙일련번호", "행정규칙명", "발령일자", "시행일자", "현행연혁구분",
                                         "제개정구분명", "행정규칙ID")} for r in same]
    sib = {}
    if os.path.exists(SIB_HIST):
        h = json.load(open(SIB_HIST, encoding="utf-8"))
        cur = [r for r in h["rows"] if r.get("현행연혁구분") == "현행"]
        sib = dict(파일=SIB_HIST, fetched_at=h.get("fetched_at", ""),
                   현행=[{k: r.get(k, "") for k in ("행정규칙일련번호", "발령일자", "시행일자")} for r in cur])
    out = dict(질의=meta["질의"], 출처URL=murl, fetched_at=meta["fetched_at"], totalCnt=_t(root, "totalCnt"),
               같은이름행=keep, 응답파일=p, 응답sha256=meta["sha256"], 형제연혁목록=sib,
               판정=("현행 = 9차 판 %s" % SEC_SERIAL9) if any(r["행정규칙일련번호"] == SEC_SERIAL9 for r in keep)
               else "현행이 9차 판과 다름 — 새 판 필요")
    json.dump(out, open(CHECK_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("totalCnt %s · 같은 이름 %d행 · %s · 호출 %d회" % (out["totalCnt"], len(keep), out["판정"], client.n_calls))
    for r in keep:
        print("  ", r["행정규칙일련번호"], r["발령일자"], r["시행일자"], r["현행연혁구분"])


# ── 별표내용 떼어 내기 ─────────────────────────────────────────────────────
ANNEX_DUMPS = {("0022", "00"): "별표22_별표내용.txt", ("0022", "01"): "별표22-1_별표내용.txt",
               ("0037", "00"): "별표37_별표내용.txt"}


def extract():
    xb = open(SEC_XML9, "rb").read()
    root = ET.fromstring(xb)
    inf = {c.tag: (c.text or "").strip() for c in root.find("행정규칙기본정보")}
    units = []
    for u in root.iter("별표단위"):
        no, g, k = _t(u, "별표번호"), _t(u, "별표가지번호") or "00", _t(u, "별표구분")
        if no in ("0022", "0037"):
            c = u.findtext("별표내용") or ""
            rec = dict(별표키=u.attrib.get("별표키", ""), 별표번호=no, 별표가지번호=g, 별표구분=k,
                       별표제목=_t(u, "별표제목"), 별표서식파일링크=_t(u, "별표서식파일링크"),
                       별표서식PDF파일링크=_t(u, "별표서식PDF파일링크"), 글자수=len(c), 줄수=len(c.split("\n")))
            name = ANNEX_DUMPS.get((no, g)) if k == "별표" else None
            if name:
                p = os.path.join(D, name)
                os.makedirs(D, exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(c)
                rec.update(파일=p, 파일sha256=sha(c))
            units.append(rec)
    out = dict(원본XML=SEC_XML9, 원본XML_sha256=sha(xb), 원본메타=meta_of(SEC_XML9),
               행정규칙일련번호=inf.get("행정규칙일련번호"), 발령일자=inf.get("발령일자"), 시행일자=inf.get("시행일자"),
               현행여부=inf.get("현행여부"), 떼어낸시각=now(), 별표단위=units,
               방법="xml.etree 로 <별표단위> 중 별표번호 0022·0037 을 찾아 <별표내용> 글(itertext 아님, findtext) 을 "
                    "바꾸지 않고 UTF-8 로 씀(newline='' — 줄바꿈 문자 그대로)")
    json.dump(out, open(os.path.join(D, "별표단위_목록.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in units:
        print(r["별표번호"], r["별표가지번호"], r["별표구분"], r["별표제목"][:40], r["글자수"], r["줄수"], r.get("파일", ""))


# ── 별표37: 세 원본 대조 ──────────────────────────────────────────────────
A37_XML = os.path.join(D, "별표37_별표내용.txt")
A37_JSON = os.path.join(D, "별표37_대조요약.json")
ITEM_RE = re.compile(r"^\s*(\d+)\s*\.\s*\(([^)]*)\)")
CH_RE = re.compile(r"^\s*제\s*(\d+)\s*장")
SEC_RE = re.compile(r"^\s*제\s*(\d+)\s*절")


def load_md():
    """10차 md 의 「## 원문」 아래 줄 → [(파일 줄 번호, 글)]."""
    L = open(A37_MD10, encoding="utf-8").read().split("\n")
    st = next(i for i, l in enumerate(L) if l.strip() == "## 원문")
    return [(i + 1, L[i]) for i in range(st + 1, len(L))]


def load_pdf():
    """pypdf 텍스트 → [(txt 줄 번호, 쪽, 글)] (쪽 표지 줄은 뺌)."""
    out, page = [], 0
    for i, l in enumerate(open(A37_PDF10, encoding="utf-8").read().split("\n")):
        m = re.match(r"^=== p\.(\d+) ===$", l.strip())
        if m:
            page = int(m.group(1))
            continue
        out.append((i + 1, page, l))
    return out


def load_xml37():
    """XML 별표내용(상자 그림 글) → [(별표내용 줄 번호, 글)] — 앞뒤 「│」와 그 안쪽 끝 공백만 떼어 냄."""
    out = []
    for i, l in enumerate(open(A37_XML, encoding="utf-8", newline="").read().split("\n")):
        s = l.rstrip("\r")
        if s.startswith("│") and s.rstrip().endswith("│"):
            s = s[1:s.rstrip().rfind("│")].rstrip()
        elif re.fullmatch(r"\s*[┌└][─]*[┐┘]\s*", s):
            s = ""
        out.append((i + 1, s))
    return out


def flat(rows, keyf):
    """줄 목록 → (공백 뺀 이은 글, 글자마다 출처 키 목록)."""
    chars, keys = [], []
    for r in rows:
        t = _nosp(r[-1])
        chars.append(t)
        keys += [keyf(r)] * len(t)
    return "".join(chars), keys


def items_of(rows, txt=lambda r: r[-1]):
    out, ch, sc = [], "", ""
    for r in rows:
        s = txt(r)
        if CH_RE.match(s):
            ch, sc = s.strip(), ""
        elif SEC_RE.match(s):
            sc = s.strip()
        m = ITEM_RE.match(s)
        if m:
            out.append(dict(번호=int(m.group(1)), 제목=m.group(2), 장=ch, 절=sc, 줄=r[0], 글=s.strip(), row=r))
    return out


def ops(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [o for o in sm.get_opcodes() if o[0] != "equal"], sm.ratio()


def a37():
    md, pdf, xml = load_md(), load_pdf(), load_xml37()
    imd, ipdf, ixml = items_of(md), items_of(pdf), items_of(xml)
    nums = [r["번호"] for r in imd]
    rng = list(range(1, max(nums) + 1))
    miss = [n for n in rng if n not in nums]
    dup = sorted({n for n in nums if nums.count(n) > 1})
    bp = {r["번호"]: r for r in ipdf}
    bx = {r["번호"]: r for r in ixml}
    rows = []
    for r in imd:
        p, x = bp.get(r["번호"]), bx.get(r["번호"])
        rows.append(dict(번호=r["번호"], 제목=r["제목"], 장=r["장"], 절=r["절"], md줄=r["줄"],
                         PDF쪽=p["row"][1] if p else "", PDF_txt줄=p["줄"] if p else "", XML별표내용줄=x["줄"] if x else "",
                         제목_md_PDF_같음="Y" if p and p["제목"] == r["제목"] else "N",
                         제목_md_XML_같음="Y" if x and x["제목"] == r["제목"] else "N"))
    write_csv(A37_ITEMS_CSV, list(rows[0].keys()), rows)
    # 글자 대조(공백 무시)
    smd, kmd = flat(md, lambda r: r[0])
    spdf, kpdf = flat(pdf, lambda r: (r[0], r[1]))
    sxml, kxml = flat(xml, lambda r: r[0])
    drows = []

    def span(keys, i, j):
        if not keys:
            return ""
        k = keys[min(i, len(keys) - 1): max(j, i + 1)] or [keys[min(i, len(keys) - 1)]]
        return "%s~%s" % (k[0], k[-1]) if k[0] != k[-1] else str(k[0])

    res = {}
    for nm, (sa, ka), (sb, kb) in (("md↔PDF", (smd, kmd), (spdf, kpdf)), ("md↔XML", (smd, kmd), (sxml, kxml)),
                                     ("PDF↔XML", (spdf, kpdf), (sxml, kxml))):
        oc, ratio = ops(sa, sb)
        res[nm] = dict(글자수=[len(sa), len(sb)], 같음비율=round(ratio, 6), 다른곳=len(oc))
        for tag, i1, i2, j1, j2 in oc:
            drows.append(dict(대조=nm, 종류=tag, A글=sa[i1:i2], B글=sb[j1:j2], A앞뒤=sa[max(0, i1 - 12):i2 + 12],
                              A위치=span(ka, i1, i2), B위치=span(kb, j1, j2)))
    # 줄 단위: PDF 줄(공백 뺀 글)이 md 이은 글에 차례로 들어 있는지
    cur, notin = 0, []
    for ln, pg, t in pdf:
        n = _nosp(t)
        if not n:
            continue
        k = smd.find(n, cur)
        if k < 0:
            notin.append(dict(PDF_txt줄=ln, 쪽=pg, 글=t))
        else:
            cur = k + len(n)
    cur, notin_md = 0, []
    for ln, t in md:
        n = _nosp(t)
        if not n:
            continue
        k = spdf.find(n, cur)
        if k < 0:
            notin_md.append(dict(md줄=ln, 글=t))
        else:
            cur = k + len(n)
    write_csv(A37_DIFF_CSV, ["대조", "종류", "A글", "B글", "A앞뒤", "A위치", "B위치"], drows)
    # 10차 PDF 텍스트가 별표 PDF 를 지금 다시 읽은 글과 같은지(쪽마다, 공백 무시) + 쪽마다 그림 개수
    from pypdf import PdfReader
    rd = PdfReader(A37_PDF10_BIN)
    pages = []
    for i, pg in enumerate(rd.pages):
        fresh = _nosp(pg.extract_text() or "")
        old = "".join(_nosp(t) for _, p, t in pdf if p == i + 1)
        imgs = []
        rsc = pg.get("/Resources")
        xo = rsc.get_object().get("/XObject") if rsc is not None else None
        if xo is not None:
            for k, v in xo.get_object().items():
                v = v.get_object()
                if v.get("/Subtype") == "/Image":
                    W, H = int(v["/Width"]), int(v["/Height"])
                    dat = v.get_data()
                    px = [(j // 3 % W, j // 3 // W) for j in range(0, len(dat) - 2, 3) if min(dat[j:j + 3]) < 200] \
                        if v.get("/ColorSpace") == "/DeviceRGB" and int(v.get("/BitsPerComponent", 8)) == 8 else []
                    imgs.append(dict(이름=str(k), 너비=W, 높이=H, 어두운화소=len(px),
                                     어두운화소_범위=[min(p[0] for p in px), max(p[0] for p in px), min(p[1] for p in px),
                                                max(p[1] for p in px)] if px else []))
        pages.append(dict(쪽=i + 1, 새로읽은글자수=len(fresh), txt글자수=len(old), 같음=fresh == old, 그림=imgs))
    summ = dict(md=A37_MD10, md_sha256=sha(open(A37_MD10, "rb").read()), pdf_txt=A37_PDF10,
                pdf_txt_sha256=sha(open(A37_PDF10, "rb").read()), xml_별표내용=A37_XML,
                xml_sha256=sha(open(A37_XML, "rb").read()), 원문줄수=dict(md=len(md), pdf=len(pdf), xml=len(xml)),
                항목수=dict(md=len(imd), pdf=len(ipdf), xml=len(ixml)), 번호범위=[min(nums), max(nums)], 빠진번호=miss,
                겹친번호=dup, 항목번호_PDF=[r["번호"] for r in ipdf], 항목번호_XML=[r["번호"] for r in ixml],
                장절_md=[r[1].strip() for r in md if CH_RE.match(r[1]) or SEC_RE.match(r[1])],
                장절_pdf=[r[2].strip() for r in pdf if CH_RE.match(r[2]) or SEC_RE.match(r[2])],
                장절_xml=[r[1].strip() for r in xml if CH_RE.match(r[1]) or SEC_RE.match(r[1])],
                글자대조=res, PDF줄_md에없음=notin, md줄_PDF에없음=notin_md, 다른곳목록=A37_DIFF_CSV, 항목목록=A37_ITEMS_CSV,
                PDF쪽점검=pages, pdf_sha256=sha(open(A37_PDF10_BIN, "rb").read()), 대조시각=now())
    json.dump(summ, open(A37_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("항목 md %d · PDF %d · XML %d · 범위 %s · 빠진 %s · 겹친 %s" % (len(imd), len(ipdf), len(ixml), summ["번호범위"],
                                                                 miss, dup))
    print("장절 같음 md=PDF %s md=XML %s" % (summ["장절_md"] == summ["장절_pdf"], summ["장절_md"] == summ["장절_xml"]))
    for k, v in res.items():
        print(k, v)
    print("PDF줄 md에 없음 %d · md줄 PDF에 없음 %d" % (len(notin), len(notin_md)))
    print("PDF 다시 읽기 쪽마다 같음: %s · 그림 %s" % (all(p["같음"] for p in pages),
                                               [(p["쪽"], len(p["그림"])) for p in pages if p["그림"]]))


# ── 별표22: 위험 분류 제목 줄 ─────────────────────────────────────────────
A22_TXT = os.path.join(D, "별표22_별표내용.txt")
A22_JSON = os.path.join(D, "별표22_제목줄.json")
PART_RE = re.compile(r"^\s*([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ])\s*\.")
NM_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*\.")
N_RE = re.compile(r"^\s*(\d+)\s*\.")
GA_RE = re.compile(r"^\s*([가-하])\s*\.")
PAREN_RE = re.compile(r"^\s*\((\d+)\)")
CIRC_RE = re.compile(r"^\s*([①-⑳])")
# 하위 위험을 나누는 줄(판단으로 고름) — 줄 번호와 그 줄 첫머리(고정 판 2200000108939 에서 확인)
SUBRISK_LINES = [
    (3957, "나.(기본요구자본)"), (5155, "나.(산출방법) 생명·장기손해보험위험액은"), (5463, "나.(충격수준) 장해·질병위험액은"),
    (5529, "나.(충격수준) 해지위험액은"), (5745, "나.(측정방법) 대재해위험액은 전염병"),
    (5911, "나.(산출방법) 일반손해보험위험액은"), (5987, "나.(하위위험) 보험가격·준비금위험액은"),
    (7153, "가.(측정방법) 대재해위험액은 자연재해"), (7573, "나.(산출방법) 시장위험액은"),
    (7663, "①금리상승시나리오"), (7667, "②금리하락시나리오"), (7671, "③금리평탄시나리오"), (7675, "④금리경사시나리오"),
    (7839, "나.(주식유형)"), (8345, "나.(산출방법) 외환위험액은"), (8745, "나.(하위위험) 자산집중위험액은"),
    (9025, "나.(B/S(난내)자산 분류)"), (9217, "다.(난외자산 분류)"),
    (10503, "나.익스포져는"), (10581, "나.일반운영위험액은"), (10629, "다.기초가정위험액은"),
]


def a22_lines():
    return open(A22_TXT, encoding="utf-8", newline="").read().split("\n")


def a22_paths(L):
    """줄마다 (부, 장, 항, 목, 세목, 원숫자) 위치. 상자 그림 줄(│┌├└)은 위치를 바꾸지 않는다."""
    cur = dict(부="", 장="", 항="", 목="", 세목="", 원="")
    order = ["부", "장", "항", "목", "세목", "원"]
    out = []

    def setv(k, v):
        cur[k] = v
        for kk in order[order.index(k) + 1:]:
            cur[kk] = ""

    for l in L:
        s = l.strip()
        if s[:1] in "│┌├└┬┼┴┐┘─":
            out.append(dict(cur))
            continue
        m = PART_RE.match(s)
        if m:
            setv("부", m.group(1) + ".")
        elif re.match(r"^제\s*\d+\s*장", s):
            setv("장", re.match(r"^(제\s*\d+\s*장)", s).group(1))
        elif NM_RE.match(s):
            m = NM_RE.match(s)
            setv("항", "%s-%s." % (m.group(1), m.group(2)))
        elif N_RE.match(s):
            setv("항", N_RE.match(s).group(1) + ".")
        elif GA_RE.match(s):
            setv("목", GA_RE.match(s).group(1) + ".")
        elif PAREN_RE.match(s):
            setv("세목", "(%s)" % PAREN_RE.match(s).group(1))
        elif CIRC_RE.match(s):
            setv("원", CIRC_RE.match(s).group(1))
        out.append(dict(cur))
    return out


def path_str(p):
    return " > ".join(v for v in (p["부"], p["장"], p["항"], p["목"], p["세목"], p["원"]) if v)


def a22():
    L = a22_lines()
    P = a22_paths(L)
    rows = []

    def add(group, i):
        rows.append(dict(묶음=group, 줄=i + 1, 위치=path_str(P[i]), 물음표=("Y" if "?" in L[i] else ""), 글=L[i]))

    add("A 표지", 0)
    add("A 표지", 4)
    parts = [i for i, l in enumerate(L) if PART_RE.match(l.strip())]
    for i in parts:
        add("B 부", i)
    # C: Ⅰ.2.라.(「Ⅳ.지급여력기준금액 산출」 용어 정의) 머리 줄부터 (6) 앞까지
    st = next(i for i, l in enumerate(L) if l.strip().startswith('라."Ⅳ.지급여력기준금액 산출"에서 정한 용어의 정의'))
    en = next(i for i in range(st + 1, len(L)) if re.match(r"^\s*\(6\)", L[i]))
    for i in range(st, en):
        if L[i].strip():
            add("C 정의(Ⅰ.2.라.)", i)
    # D: Ⅳ 의 장·항 제목 줄 + 「가.~하.」 가운데 제목만 있는 「…위험액」 줄
    p4 = next(i for i in parts if L[i].strip().startswith("Ⅳ"))
    p5 = next(i for i in parts if L[i].strip().startswith("Ⅴ"))
    for i in range(p4 + 1, p5):
        s = L[i].strip()
        if s[:1] in "│┌├└":
            continue
        if re.match(r"^제\s*\d+\s*장", s) or NM_RE.match(s) or re.match(r"^[가-하]\.\s*\S*위험액\s*$", s):
            add("D Ⅳ 장·항 제목", i)
    # E: 하위 위험을 나누는 줄
    for n, head in SUBRISK_LINES:
        if not L[n - 1].strip().startswith(head):
            raise SystemExit("줄 %d 첫머리가 「%s」 가 아님 — 판이 바뀌었는지 확인" % (n, head))
        add("E 하위 위험 구분 줄", n - 1)
    write_csv(A22_CSV, ["묶음", "줄", "위치", "물음표", "글"], rows)
    summ = dict(파일=A22_TXT, sha256=sha(open(A22_TXT, "rb").read()), 줄수=len(L), 묶음별=
                {g: sum(1 for r in rows if r["묶음"] == g) for g in dict.fromkeys(r["묶음"] for r in rows)},
                물음표줄=[r["줄"] for r in rows if r["물음표"]], 별표내용_물음표_전체=sum(l.count("?") for l in L),
                제4부범위=[p4 + 1, p5], rows=rows, 시각=now())
    json.dump(summ, open(A22_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("줄 %d · 묶음 %s · 고른 줄 중 ? 있는 줄 %s · 별표내용 ? 전체 %d" % (len(L), summ["묶음별"], summ["물음표줄"],
                                                              summ["별표내용_물음표_전체"]))


# ── 산출 md ───────────────────────────────────────────────────────────────
XML_URL = "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=%s&type=XML" % SEC_SERIAL9
REG_SERIAL9 = "2100000279112"
REG_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독규정_%s.xml" % REG_SERIAL9)
REG_URL = "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=%s&type=XML" % REG_SERIAL9


def reg75_2():
    """감독규정 제7-5조 제2항 줄(글자 그대로) — 조문내용 글을 이어 붙여 「제7-5조(」 부터 다음 조 앞까지에서 「②」 줄."""
    root = ET.fromstring(open(REG_XML9, "rb").read())
    t = "\n".join("".join(e.itertext()) for e in root.iter("조문내용"))
    st = re.search(r"(?m)^[ \t　]*제\s*7\s*-\s*5\s*조(?!\s*의)", t)
    en = re.search(r"(?m)^[ \t　]*(?:제\s*\d+\s*-\s*\d+\s*조|제\s*\d+\s*장|제\s*\d+\s*절)", t[st.end():])
    art = t[st.start(): st.end() + (en.start() if en else len(t))]
    line = next(l for l in art.split("\n") if l.strip().startswith("②"))
    return line
PDF37_URL = "http://www.law.go.kr/LSW/flDownload.do?flSeq=168886133"
HWP37_URL = "https://www.law.go.kr/LSW/flDownload.do?flSeq=168886111"
# 별표37 항목 → 모범규준(2016.8.1 판) 조 — 전부 「(판단)」: 지시서 9-2 에 조 번호가 없어 조 제목 대응으로 붙임
A37_MOBEOM = {1: [37], 2: [44, 45], 3: [36, 3], 4: [37, 38], 5: [39, 8], 6: [39, 10], 7: [39], 8: [42], 9: [43],
              10: [44, 45, 46], 11: [49], 12: [46, 56], 13: [44, 36], 14: [47], 15: [46], 16: [35], 17: [48], 18: [41],
              19: [6], 20: [], 21: []}
A22_MOBEOM = [("Ⅰ.2.라.(1)~(5) 위험 정의 전체 · Ⅳ.1-2.나.(기본요구자본)", [18, 42]),
              ("Ⅳ.1-1.(측정기준) · 1-3.(측정방식)", [19]),
              ("Ⅳ 제5장 신용위험액 · 정의 (4) 신용리스크", [21]),
              ("Ⅳ 제4장 시장위험액 · 정의 (3) 시장리스크", [22]),
              ("Ⅳ 제6장 운영위험액 · 정의 (5) 운영리스크", [23]),
              ("Ⅳ 4-2. 금리위험액 · 정의 (3)① 금리위험", [24]),
              ("Ⅳ 4-6. 자산집중위험액(거래상대방집중위험액·부동산집중위험액) · 정의 (3)⑤ 자산집중위험", [26]),
              ("Ⅳ 제2장 생명·장기손해보험위험액 · 제3장 일반손해보험위험액 · 정의 (1)(2)", [18, 42])]


def mobeom_titles():
    out = {}
    if os.path.exists(MOBEOM_CSV):
        for r in csv.DictReader(open(MOBEOM_CSV, encoding="utf-8-sig")):
            out[int(r["조"])] = r["제목_2016.8.1판"]
    return out


def code(lines):
    return ["```text"] + list(lines) + ["```"]


def build():
    chk = json.load(open(CHECK_JSON, encoding="utf-8"))
    units = json.load(open(os.path.join(D, "별표단위_목록.json"), encoding="utf-8"))
    s37 = json.load(open(A37_JSON, encoding="utf-8"))
    s22 = json.load(open(A22_JSON, encoding="utf-8"))
    items = list(csv.DictReader(open(A37_ITEMS_CSV, encoding="utf-8-sig")))
    diffs = list(csv.DictReader(open(A37_DIFF_CSV, encoding="utf-8-sig")))
    mt = mobeom_titles()
    md = load_md()
    mdd = dict(md)
    pdf = load_pdf()
    pdfd = {ln: (pg, t) for ln, pg, t in pdf}
    xml37 = open(A37_XML, encoding="utf-8", newline="").read().split("\n")
    L22 = a22_lines()
    xmeta = units["원본메타"]

    def mob(nums):
        return " · ".join("제%d조(%s)" % (n, mt.get(n, "?")) for n in nums) + " (판단)" if nums else \
            "대응 조를 붙이지 않음(판단 — 2016.8.1 판 조 제목에 감독당국 점검·조치 조가 없음)"

    c22 = lambda n: "[보험업감독업무시행세칙(일련번호 %s) · %s · [별표 22] 별표내용 %s줄 · 수집 %s, 현행 재확인 %s]" % (  # noqa: E731
        SEC_SERIAL9, XML_URL, n, xmeta.get("fetched_at", "")[:10], chk["fetched_at"][:16])
    c37x = lambda n: "[보험업감독업무시행세칙(일련번호 %s) · %s · [별표 37] 별표내용 %s줄 · 수집 %s]" % (  # noqa: E731
        SEC_SERIAL9, XML_URL, n, xmeta.get("fetched_at", "")[:10])
    c37p = lambda pg: "[보험업감독업무시행세칙 [별표 37] PDF · %s · p.%s · 수집 2026-10-01]" % (PDF37_URL, pg)  # noqa: E731
    c37h = lambda n: ("[보험업감독업무시행세칙 [별표 37] HWP(10차 hwp2md 텍스트 %s) · %s · md %s줄 · 수집 2026-10-01]"  # noqa: E731
                      % (A37_MD10, HWP37_URL, n))
    o = []
    w = o.append
    w("# 9-2 의 3·5번 — 보험업감독업무시행세칙 [별표 37] 번호 항목 대조 · [별표 22](K-ICS) 위험 분류 체계")
    w("")
    w("- 출처: 국가법령정보센터 Open API 세칙 XML(9차에 받은 판 `%s`, sha256 `%s`, 받은 때 %s) · [별표 37] 원본 파일"
      "(HWP %s · PDF %s, 10차에 받음). 요청 URL 의 인증값은 `OC=***`." % (
          SEC_XML9, units["원본XML_sha256"], xmeta.get("fetched_at", ""), HWP37_URL, PDF37_URL))
    w("- 수집일: 이번 작업에서 법제처에 보낸 요청은 현행 판 재확인 1회뿐(%s, 원장 `%s`, LAW_DELAY=1.0). "
      "본문은 9·10차에 받은 파일을 다시 받지 않고 썼다." % (chk["fetched_at"], LEDGER))
    w("- 방법: ① [별표 37] — 10차 hwp 텍스트(`%s` 「## 원문」 아래), 10차 PDF 텍스트(`%s`, `=== p.N ===` 쪽 표지), 세칙 XML 의 "
      "[별표 37] 별표내용(이번에 떼어 냄, `%s`) 세 가지를 번호 항목·장절 목록과 공백을 뺀 글자열로 대조(difflib, autojunk 끔). "
      "PDF 줄마다 hwp 글에 차례로 들어 있는지, hwp 줄마다 PDF 글에 차례로 들어 있는지도 봤다. PDF 텍스트는 별표 PDF 를 pypdf 로 "
      "다시 읽어 쪽마다 같은지 확인했다. ② [별표 22] — 세칙 XML 에서 별표번호 0022 의 별표내용만 `%s` 로 떼어 내고, 부(Ⅰ~Ⅵ)·장·항·목 "
      "위치를 줄마다 매겨 위험 분류 제목 줄과 하위 위험을 나누는 줄을 글자 그대로 옮겼다." % (
          A37_MD10, A37_PDF10, A37_XML, A22_TXT))
    w("- 한계: ① 대조는 공백·줄바꿈을 무시한 글자 대조다(PDF 는 쪽 너비에서 줄이 바뀌고 hwp 는 문단이 한 줄이라 줄 경계가 다름). "
      "② [별표 22] 는 XML 별표내용만 봤고 별표 HWP·PDF 는 받지 않았다(별표내용이 비지 않았고, 옮긴 줄에 깨진 글자가 없음). "
      "③ [별표 22] 의 산식·상관계수 표·충격 수준은 지시서대로 옮기지 않았다. ④ 하위 위험을 나누는 줄은 판단으로 골랐다(2-6절).")
    w("- 표기: 원문 인용은 코드 블록(글자 그대로, 앞뒤 공백 포함). 해설은 「note:」 줄, 해석이 들어간 곳은 「(판단)」. "
      "지시서 9-2 에는 모범규준 조 번호가 없어, 붙인 조 번호는 모두 「(판단)」(2016.8.1 판 조 제목 기준, `%s`)." % MOBEOM_CSV)
    w("- 기록 파일: 스크립트 `scripts/dart/web13_law92b.py` · 항목 대조 `%s` · 글자 대조 `%s` · 별표22 줄 목록 `%s` · "
      "원본·요약 `%s/`(git 무시)." % (A37_ITEMS_CSV, A37_DIFF_CSV, A22_CSV, D))
    w("")
    w("## 0. 현행 판 재확인")
    w("")
    w("| 규정 | 받아 둔 XML(일련번호 · 발령 · 시행) | 오늘 현행(API) | 결과 |")
    w("|---|---|---|---|")
    cur = chk["같은이름행"][0] if chk["같은이름행"] else {}
    w("| 보험업감독업무시행세칙 | %s · %s · %s | %s · %s · %s (%s) | %s |" % (
        units["행정규칙일련번호"], units["발령일자"], units["시행일자"], cur.get("행정규칙일련번호", ""), cur.get("발령일자", ""),
        cur.get("시행일자", ""), cur.get("현행연혁구분", ""), chk["판정"]))
    w("")
    w("- note: 질의 `%s` → totalCnt %s, 응답 원본 `%s`(상세링크의 OC 는 저장 전 *** 로 가림). 같은 날 9-2 1·2번 에이전트가 받은 "
      "연혁 목록(`%s`, %s)에서도 현행은 %s 이다." % (
          chk["질의"], chk["totalCnt"], chk["응답파일"], chk["형제연혁목록"].get("파일", ""),
          chk["형제연혁목록"].get("fetched_at", ""),
          ", ".join(r["행정규칙일련번호"] for r in chk["형제연혁목록"].get("현행", []))))
    w("")
    # ── 1. 별표37
    w("## 1. [별표 37] 번호 항목 목록과 빠진 번호(9-2 의 3번)")
    w("")
    w("- 결론: **빠진 번호 없음 — 대조 방법**: hwp 텍스트·PDF 텍스트·XML 별표내용 세 원본 모두 번호 항목이 %d.~%d. 으로 "
      "%d개, 빠진 번호 %s, 겹친 번호 %s. 장·절 머리 줄 목록: hwp↔PDF %s, hwp↔XML %s." % (
          s37["번호범위"][0], s37["번호범위"][1], s37["항목수"]["md"], s37["빠진번호"] or "없음(1~%d 연속)" % s37["번호범위"][1],
          s37["겹친번호"] or "없음", "같음" if s37["장절_md"] == s37["장절_pdf"] else "다름",
          "같음" if s37["장절_md"] == s37["장절_xml"] else "다름"))
    a = s37["글자대조"]
    w("- 결론: **PDF 에만 있는 글은 찾지 못함(추출 범위에 없음)** — 공백을 뺀 글자열 hwp %d자 · PDF %d자, 다른 곳 %d곳(같음 비율 %s). "
      "PDF 줄 %d개 가운데 hwp 글에 차례로 들어 있지 않은 줄 %d개, hwp 줄 가운데 PDF 글에 없는 줄 %d개. 찾은 범위: PDF 1~10쪽 글 층 전부"
      "(pypdf 로 다시 읽은 글이 10차 텍스트와 쪽마다 %s) ↔ 10차 md 「## 원문」 %d줄." % (
          a["md↔PDF"]["글자수"][0], a["md↔PDF"]["글자수"][1], a["md↔PDF"]["다른곳"], a["md↔PDF"]["같음비율"],
          sum(1 for _, _, t in pdf if _nosp(t)), len(s37["PDF줄_md에없음"]), len(s37["md줄_PDF에없음"]),
          "같음" if all(p["같음"] for p in s37["PDF쪽점검"]) else "다름", len(md)))
    imgs = [(p["쪽"], g) for p in s37["PDF쪽점검"] for g in p["그림"]]
    if imgs:
        w("- note: PDF 에 그림이 %d개 있다(%s). 각각 %s 화소 그림 안에 어두운 화소 %s개가 왼쪽 끝 세로 가운데(가로 0~8, 세로 59~67)에 "
          "모인 점 하나다. 같은 쪽 글 층에 가운뎃점 「‧」이 있어(8쪽 txt 259줄, 9쪽 txt 316줄) 글자 크기 점을 그림으로도 그린 것으로 "
          "보고 빠진 글로 세지 않았다(판단)." % (
              len(imgs), " · ".join("p.%d %s" % (pg, g["이름"]) for pg, g in imgs),
              "/".join("%d×%d" % (g["너비"], g["높이"]) for _, g in imgs), "/".join(str(g["어두운화소"]) for _, g in imgs)))
    w("- note(지시서 대조): 지시서는 「1.~20. 항목 목록」이라 했으나 원문 번호는 1.~21. 이다 — 21. (감독당국의 조치)가 제3장 "
      "20. (감독당국의 점검) 다음에 있다(PDF p.10).")
    w("")
    w("### 1-1 항목 목록(번호 · 제목 · 장/절 · 위치)")
    w("")
    w("| 번호 | 제목(괄호 안 글자 그대로) | 장 | 절 | md 줄 | PDF 쪽(txt 줄) | XML 별표내용 줄 | 세 원본 제목 같음 | 모범규준 조 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in items:
        w("| %s. | %s | %s | %s | %s | p.%s (%s) | %s | %s | %s |" % (
            r["번호"], r["제목"], r["장"], r["절"] or "—", r["md줄"], r["PDF쪽"], r["PDF_txt줄"], r["XML별표내용줄"],
            "Y" if r["제목_md_PDF_같음"] == "Y" and r["제목_md_XML_같음"] == "Y" else "N", mob(A37_MOBEOM[int(r["번호"])])))
    w("")
    w("- note: md 줄은 `%s` 파일의 줄 번호, PDF txt 줄은 `%s` 의 줄 번호, XML 줄은 `%s`(세칙 XML [별표 37] 별표내용을 그대로 쓴 파일)의 "
      "줄 번호다." % (A37_MD10, A37_PDF10, A37_XML))
    w("")
    w("장·절 머리 줄과 항목 머리(「N. (제목)」까지) — PDF 글 층 그대로 %s" % c37p("1~10"))
    w("")
    heads = []
    for ln, pg, t in pdf:
        s = t.strip()
        if CH_RE.match(s) or SEC_RE.match(s):
            heads.append(t)
        else:
            m = ITEM_RE.match(t)
            if m:
                heads.append(m.group(0))
    o += code(heads)
    w("")
    w("- note: 1. (목적)과 7. (이사회와 경영진의 유의 사항)은 머리 줄에 본문이 이어진다(전문은 10차 md 26·73줄).")
    w("")
    w("### 1-2 세 원본이 다른 곳 — XML 별표내용만 다름(%d곳)" % a["md↔XML"]["다른곳"])
    w("")
    w("- note: hwp 와 PDF 는 공백을 빼면 한 글자도 다르지 않다. 세칙 XML 의 [별표 37] 별표내용은 아래 %d곳에서 hwp·PDF 의 "
      "가운뎃점류 글자 대신 ASCII 물음표 `?`(0x3F)를 싣고 있다(XML 별표내용 `?` 전체 %d개 = 이 %d곳). 번호 항목·장절에는 영향이 없다."
      % (a["md↔XML"]["다른곳"], open(A37_XML, encoding="utf-8").read().count("?"), a["md↔XML"]["다른곳"]))
    w("")
    pd = {(r["A앞뒤"]): r for r in diffs if r["대조"] == "PDF↔XML"}
    for k, r in enumerate([r for r in diffs if r["대조"] == "md↔XML"], 1):
        mdl = int(r["A위치"].split("~")[0])
        xl = int(r["B위치"].split("~")[0])
        p = pd.get(r["A앞뒤"])
        pl, pg = (p["A위치"].strip("()").split(",") if p else ("", ""))
        pl = int(pl) if pl else 0
        pg = pg.strip()
        w("**(%d) md %d줄 · PDF p.%s txt %d줄 · XML %d줄** — hwp·PDF 글자 `%s`(U+%04X) ↔ XML `%s`(U+%04X)" % (
            k, mdl, pg, pl, xl, r["A글"], ord(r["A글"][0]), r["B글"], ord(r["B글"][0])))
        w("")
        w("hwp %s" % c37h(mdl))
        o += code([mdd[mdl]])
        w("PDF %s" % c37p(pg))
        o += code([pdfd[pl][1]] + ([pdfd[pl + 1][1]] if pdfd.get(pl, ("", ""))[1].rstrip().endswith(r["A글"]) and
                                    (pl + 1) in pdfd else []))
        w("XML %s" % c37x(xl))
        o += code([xml37[xl - 1]])
        w("")
    # ── 2. 별표22
    w("## 2. [별표 22](K-ICS) 위험 분류 체계와 하위 위험 목록(9-2 의 5번)")
    w("")
    u22 = [u for u in units["별표단위"] if u["별표번호"] == "0022"]
    w("### 2-1 별표 단위 확인(번호 0022, 가지번호)")
    w("")
    w("| 별표키 | 별표번호 | 가지번호 | 구분 | 별표제목(원문) | 별표내용 글자 · 줄 | 별표 파일 링크(받지 않음) |")
    w("|---|---|---|---|---|---|---|")
    for u in u22:
        w("| %s | %s | %s | %s | %s | %s자 · %s줄 | HWP http://www.law.go.kr%s · PDF http://www.law.go.kr%s |" % (
            u["별표키"], u["별표번호"], u["별표가지번호"], u["별표구분"], u["별표제목"], u["글자수"], u["줄수"],
            u["별표서식파일링크"], u["별표서식PDF파일링크"]))
    w("")
    w("- note: 위험 분류는 가지번호 00 인 [별표 22](지급여력금액 및 지급여력기준금액 산출기준, 표준모형)에서 옮겼다. 가지번호 01 "
      "[별표 22-1](내부모형 적용기준)은 이번 범위 밖으로 두었다(판단). 같은 번호의 별지 0022 는 서식이다.")
    w("- note: 별표내용은 비지 않았다(%d줄). 별표내용 전체에 ASCII `?` 가 %d개 있으나(주로 표 칸 — 예: <표3> 머리줄 「생명?장기손해」 "
      "3977줄) 아래에 옮긴 줄에는 하나도 없다(물음표 있는 옮긴 줄: %s)." % (
          s22["줄수"], s22["별표내용_물음표_전체"], s22["물음표줄"] or "없음"))
    w("- note: [별표 37] 2. 마. 의 「표준모형」 정의가 이 [별표 22]를 가리킨다(10차 md 32줄 「<별표22>」).")
    w("")
    rows22 = s22["rows"]

    def block(group, title, cite_note=""):
        rr = [r for r in rows22 if r["묶음"] == group]
        w(title)
        w("")
        w("| 별표내용 줄 | 위치(부 > 장 > 항 > 목 > 세목) |")
        w("|---|---|")
        for r in rr:
            w("| %s | %s |" % (r["줄"], r["위치"] or "(머리)"))
        w("")
        w("원문 %s — 위 표의 줄만 표의 차례대로 옮겼다(그 사이 줄은 뺐다)" % c22("%s~%s" % (rr[0]["줄"], rr[-1]["줄"])))
        o.extend(code([r["글"] for r in rr]))
        if cite_note:
            w(cite_note)
        w("")

    block("A 표지", "### 2-2 별표 표지와 제목")
    block("B 부", "### 2-3 부(Ⅰ~Ⅵ) 구성")
    block("C 정의(Ⅰ.2.라.)", "### 2-4 위험 분류 정의 — Ⅰ.총칙 2.용어의 정의 라.(「Ⅳ.지급여력기준금액 산출」의 용어) (1)~(5)",
          "- note: (6) 이하(요구자본·충격시나리오 방식 등 측정 용어)는 위험 분류가 아니라 옮기지 않았다(판단). (1)(2)(3)은 하위위험 "
          "개수(7개·3개·5개)와 이름을 적고, (4) 신용리스크·(5) 운영리스크 정의 줄에는 하위위험 구분 문구가 없다.")
    block("D Ⅳ 장·항 제목", "### 2-5 Ⅳ.지급여력기준금액 산출 — 장·항 제목 줄(과 「…위험액」 목 제목 줄)",
          "- note: 고른 기준 — Ⅳ 범위(%s~%s줄) 안 상자 그림 밖 줄 가운데 「제N장」, 「N-M.」, 그리고 「가.~하.」 뒤가 「…위험액」으로 끝나는 "
          "제목만 있는 줄. 1-1.·1-3. 은 제목과 본문이 한 줄이라 줄 전체를 옮겼다." % (s22["제4부범위"][0], s22["제4부범위"][1]))
    block("E 하위 위험 구분 줄", "### 2-6 하위 위험을 나누는 줄(Ⅳ, 판단으로 고름)",
          "- note: 고른 기준(판단) — 5개 위험액과 그 하위 위험액의 이름을 「(이하 ‘…위험액’)」 꼴로 정하거나 「구분한다/구분하여」로 "
          "나누는 줄. 계산식 상자·상관계수 표(<표3>·<표6>·<표19> 등)·충격 수준 숫자 줄(예: 4-3.다. 주식 유형별 하락률 8007~8141줄, "
          "2-8.나.(1) 전염병위험액 5757줄)은 지시서(산식 불필요)에 따라 옮기지 않았다. 2-8.나.(2) 대형사고위험액의 세 갈래(사망·장해·"
          "장기재물, 5785줄)는 한 단계 더 아래라 위치만 적는다. 제5장 신용위험액은 하위 「…위험액」 구분이 없어 측정 대상 분류 줄"
          "(5-1.나.·다.)을, 제6장 운영위험액은 익스포져 구분과 위험액 구분 줄(6-1.나., 6-2.나.·다.)을 옮겼다.")
    w("### 2-7 위험 분류 체계 요약(해설 — 원문 아님)")
    w("")
    w("- note: 기본요구자본 = 5개 위험액 — ① 생명·장기손해보험위험액(하위 7: 사망 / 장수 / 장해·질병 / 장기재물·기타 / 해지 / 사업비 / 대재해) "
      "② 일반손해보험위험액(보험가격·준비금위험액[보험가격 / 준비금] + 대재해위험액[자연재해 / 대형사고 / 대형보증]) ③ 시장위험액(하위 5: "
      "금리 / 주식 / 부동산 / 외환 / 자산집중[거래상대방집중 / 부동산집중]) ④ 신용위험액(하위 위험액 구분 없음, 익스포져를 B/S 신용자산·담보부자산, "
      "난외자산으로 나눔) ⑤ 운영위험액(일반운영위험액 + 기초가정위험액[지급금예실차·사업비예실차]). 근거 줄: 213~289, 3957, 5155, "
      "5911, 5987, 7153, 7573, 8745, 9025, 9217, 10503, 10629.")
    w("- note: 「장해·질병」「장기재물·기타」는 한 하위위험의 이름이다(정의 (1)의 「7개의 하위위험」).")
    w("")
    w("### 2-8 지시서 이름과 원문 이름")
    w("")
    w("| 지시서(9-2 의 5번) | 원문 Ⅰ.2.라. 정의(줄) | 원문 Ⅳ 장 제목(줄) | [별표 22] 전체에서 「…위험」 뒤에 「액」이 없는 곳 |")
    w("|---|---|---|---|")
    names = [("생명·장기손해", "(1)‘생명ㆍ장기손해보험리스크’ (213)", "제2장 생명·장기손해보험위험액 (5131)", "생명[·ㆍ?]장기손해보험위험"),
             ("일반손해", "(2)‘일반손해보험리스크’ (245)", "제3장 일반손해보험위험액 (5895)", "일반손해보험위험"),
             ("시장", "(3)‘시장리스크’ (261)", "제4장 시장위험액 (7561)", "시장위험"),
             ("신용", "(4)‘신용리스크’ (285)", "제5장 신용위험액 (8997)", "신용위험"),
             ("운영위험", "(5)‘운영리스크’ (289)", "제6장 운영위험액 (10487)", "운영위험")]
    for a1, b1, c1, pat in names:
        hits = [(i + 1, m.group(0) + L22[i][m.end():m.end() + 5]) for i, l in enumerate(L22)
                for m in re.finditer(pat + r"(?!액)", l)]
        w("| %s | %s | %s | %s |" % (a1, b1, c1, ("%d곳(예: %s)" % (len(hits), ", ".join(
            "%d줄 「%s…」" % h for h in hits[:3]))) if hits else "0곳"))
    w("")
    w("- note: 마지막 칸은 [별표 22] 별표내용 전체에서 「…위험」 뒤에 「액」이 붙지 않은 곳을 정규식으로 찾은 결과다(가운뎃점 「·」「ㆍ」「?」 모두). "
      "[별표 22] 는 다섯 위험을 정의에서 「…리스크」, 측정 장 제목에서 「…위험액」으로 부른다. 「생명·장기손해보험위험」「일반손해보험위험」"
      "「시장위험」 꼴은 한 곳도 없고, 「신용위험」「운영위험」은 대부분 합성어(신용위험스프레드·신용위험경감기법·일반운영위험 익스포져 등)로 "
      "나오며 위험 이름처럼 쓰인 곳은 4065줄(「시장, 신용위험 등」)·4611줄(간편법 산식 설명 「k : 주식위험, 부동산위험, 신용위험」)·"
      "4955줄(「(운영위험)」) 정도다(전체 목록은 스크립트로 다시 뽑을 수 있음).")
    w("- note: 가운뎃점도 다르다 — 정의 (1)·①~⑦은 「ㆍ」(U+318D), Ⅳ 장·항 제목은 「·」(U+00B7).")
    w("- note: 지시서의 다섯 이름은 보험업감독규정 제7-5조 제2항의 위험 이름과 같다(판단 — 조문 연혁은 9-2 1번 산출이 다룸). 아래는 그 항의 글:")
    w("")
    w("[보험업감독규정(일련번호 %s, 오늘 현행 — 9-2 1번 에이전트의 2026-10-07 연혁 목록 기준) · %s · 제7-5조 제2항 · 수집 %s]" % (
        REG_SERIAL9, REG_URL, (meta_of(REG_XML9).get("fetched_at", "") or "")[:10]))
    o.extend(code([reg75_2()]))
    w("")
    # ── 3. 모범규준
    w("## 3. 모범규준 조 번호(전부 판단)")
    w("")
    w("| 자료 | 모범규준 조(2016.8.1 판 제목) |")
    w("|---|---|")
    w("| [별표 37] 전체(자체 위험 및 지급여력 평가 = 내부자본 적정성 평가에 해당한다고 봄) | 제5장 내부자본 적정성 평가 및 관리 "
      "제36조~제49조, 제56조(통합위기상황분석), 제6조(문서화) (판단) — 항목별은 1-1 표 |")
    for k, v in A22_MOBEOM:
        w("| [별표 22] %s | %s |" % (k, mob(v)))
    w("")
    w("- note: 모범규준 제18조 제목(측정 및 관리 대상)·제42조(위험 인식)는 보험위험을 중요 위험으로 함께 적고 있어(9-4_모범규준_원문.md "
      "909·996줄) 생명·장기손해·일반손해보험위험액을 여기에 붙였다(판단). 모범규준에는 보험위험만 다루는 조가 없다(조목록 기준).")
    w("")
    # ── 4. 받은 것 표
    w("## 4. 받은 것 / 받지 못한 것 / 원문과 다른 것을 발견한 곳")
    w("")
    w("| 구분 | 내용 | 위치 |")
    w("|---|---|---|")
    w("| 받은 것 | [별표 37] 번호 항목 1.~21. 목록(장/절·md 줄·PDF 쪽·XML 줄) | 1-1 · `%s` |" % A37_ITEMS_CSV)
    w("| 받은 것 | [별표 37] hwp↔PDF↔XML 글자 대조(빠진 번호 없음, PDF 에만 있는 글 찾지 못함) | 1 · `%s` |" % A37_DIFF_CSV)
    w("| 받은 것 | [별표 22] 표지·부 구성·위험 정의 (1)~(5)·Ⅳ 장/항 제목·하위 위험 구분 줄 | 2-2~2-6 · `%s` |" % A22_CSV)
    w("| 받지 못한 것 | PDF 에만 있는 [별표 37] 글 — 추출 범위에 없음(PDF 1~10쪽 글 층 ↔ hwp 「## 원문」, 공백 무시 글자 대조·줄 포함 대조) | 1 |")
    w("| 받지 못한 것 | [별표 22] 신용리스크·운영리스크의 「하위위험」 이름 — 추출 범위에 없음(정의 (4)(5) 줄, Ⅳ 제5·6장 상자 밖 줄에서 "
      "「(이하 ‘…위험액’)」·「(하위위험)」 검색) | 2-4 · 2-6 |")
    w("| 받지 못한 것 | [별표 22] 산식·상관계수·충격 수준 — 지시서대로 옮기지 않음 | 2-6 note |")
    w("| 다른 곳 | 지시서 「1.~20.」 ↔ 원문 1.~21.(21. (감독당국의 조치)) | 1 |")
    w("| 다른 곳 | XML [별표 37] 별표내용 `?` 3곳 ↔ hwp·PDF 「‧」·「․」 | 1-2 |")
    w("| 다른 곳 | 지시서 위험 이름 「…위험」 ↔ 원문 「…리스크」(정의)·「…위험액」(Ⅳ 장 제목), 가운뎃점 「ㆍ」/「·」 | 2-8 |")
    w("| 다른 곳 | XML [별표 22] 별표내용 `?` %d개(표 칸 등, 옮긴 줄에는 없음) | 2-1 |" % s22["별표내용_물음표_전체"])
    w("")
    os.makedirs(OUT, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(o) + "\n")
    print("썼음 %s (%d줄)" % (OUT_MD, len(o)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"check": check, "extract": extract, "a37": a37, "a22": a22, "build": build}.get(cmd)
    if not fn:
        raise SystemExit(__doc__)
    fn()
