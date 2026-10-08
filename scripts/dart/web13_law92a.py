# -*- coding: utf-8 -*-
"""13차 9-2 의 1·2번 — ORSA(자체 위험 및 지급여력 평가) 연혁. 실행은 저장소 루트에서.

    LAW_DELAY=1.0 python3 scripts/dart/web13_law92a.py current   # 오늘 현행 재확인(lawSearch admrul 현행 목록)
    LAW_DELAY=1.0 python3 scripts/dart/web13_law92a.py probe     # 받은 판에서 조 글 떼기 + 경계가 안 닫힌 곳만 이분 탐색(필요할 때만 받음)
    python3 scripts/dart/web13_law92a.py build                   # 산출 md·판목록 csv(요청 없음)

이어받기: 이전 에이전트(9-2 전체)가 요청 시간 초과로 멈췄다. 그 흔적 scripts/dart/web13_law92.py(읽기·import 만,
고치지 않음), dart_out/raw/web13/law92/(연혁 목록 json·판 XML), dart_out/risk13/9-2_탐색기록.csv 를 그대로 쓰고,
이미 받은 판은 다시 받지 않는다. 새로 받는 판·검색 응답은 dart_out/raw/web13/law92a/, 원장은 law92a/_call_log.csv.

원칙(13차 COMMON13.md):
  - 법제처 OC 는 lawclient 가 env/.env 에서 읽고, 원장·메타·산출물에는 OC=*** 로만 남는다(검색 응답 본문의
    <행정규칙상세링크> 에 실려 오는 OC 도 저장 전에 가린다).
  - 원문은 글자 그대로 옮긴다(XML 글의 문자 참조·물음표·공백도 고치지 않음). 해설은 md 의 「note:」 줄에만.
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
import web13_law92 as P  # noqa: E402  이전 에이전트 스크립트 — 연혁 목록·부칙·별표 파서만 빌려 씀

TASK = "law92a"
D = os.path.join(RAW, TASK)
LEDGER = os.path.join(D, "_call_log.csv")
ART_DIR = os.path.join(D, "조문")                       # 판마다 떼어 둔 조·별표 글(비교용)
CUR_JSON = os.path.join(D, "현행재확인.json")
REG, SEC = P.REG, P.SEC
OUT_MD = os.path.join(OUT, "9-2-1_2_ORSA_연혁.md")
VER_CSV = os.path.join(WORK, "9-2-1_2_판목록.csv")
PREV_PROBE = P.PROBE_CSV                                 # dart_out/risk13/9-2_탐색기록.csv(이전 에이전트)
A37_CSV10 = os.path.join("handoff", "원문_10차", "세칙_별표37_표시.csv")
TODAY = "2026-10-07"
ORSA_RE = P.ORSA_RE                                      # 자체\s*위험\s*및\s*지급여력\s*평가
TARGETS = [(REG, "제7-5조"), (SEC, "제5-6조의2"), (SEC, "[별표 37]")]
OLD_DIRS = [os.path.join("dart_out", "raw", w, "law") for w in ("web9", "web10", "web11")] + [
    os.path.join(RAW, "law92"), D]


def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


def _nosp(s):
    return re.sub(r"\s+", "", s or "")


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest() if s else ""


# ── 판 XML ────────────────────────────────────────────────────────────────
def ver_path(name, serial):
    for d in OLD_DIRS:
        p = os.path.join(d, "%s_%s.xml" % (_nosp(name), serial))
        if os.path.exists(p):
            return p
    return None


def meta_of(p):
    mp = p + ".meta.json"
    return json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}


def fetch_ver(client, name, serial):
    """없을 때만 lawService.do target=admrul ID=<일련번호> type=XML 로 받아 law92a/ 에 둔다."""
    p = ver_path(name, serial)
    if p:
        return p
    st, body, murl, host = client.api("lawService.do", target="admrul", ID=serial, type="XML")
    b = ET.fromstring(body).find("행정규칙기본정보")
    got = (b.findtext("행정규칙일련번호") or "").strip() if b is not None else ""
    if got != serial:
        raise SystemExit("요청 %s 인데 응답 일련번호 %s — %s" % (serial, got, murl))
    n_oc = client.count_oc(body)
    body = client.mask(body)
    p, _ = save(TASK, "%s_%s.xml" % (_nosp(name), serial), body,
                dict(출처URL=murl, http_status=st, fetched_at=now(), 호스트=host,
                     OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈" % n_oc) if n_oc else ""))
    print("  받음 %s %s (%d바이트)" % (name, serial, len(body)))
    return p


# ── 조 위치 찾기(조문형식여부 Y·N 모두) ───────────────────────────────────────
JO_END = re.compile(r"(?m)^[ \t　]*(?:제\s*\d+\s*-\s*\d+\s*조|제\s*\d+\s*조|제\s*\d+\s*장|제\s*\d+\s*절|제\s*\d+\s*관)")


def jo_pat(label):
    m = re.match(r"제(\d+)-(\d+)조(?:의(\d+))?$", label)
    a, b, g = m.groups()
    tail = (r"\s*의\s*%s(?!\d)" % g) if g else r"(?!\s*의\s*\d)"
    return re.compile(r"(?m)^[ \t　]*제\s*%s\s*-\s*%s\s*조%s" % (a, b, tail))


def find_jo(xb, label):
    """행정규칙 XML 에서 「제7-5조」·「제5-6조의2」 글 → (글, 조문내용 요소 순번, 맞은 요소 수).

    감독규정·세칙은 조문형식여부 N 판이 대부분이라 조문단위·조문번호 칸이 없고, 조문내용 요소 하나에 조 하나(또는
    장·절 표제)가 통째로 들어 있다(실측). 그래서 요소마다 줄 머리의 조 표지(「제7-5조」, 띄어쓰기 변형 허용, 「제7-5조의2」는
    제외)를 찾고, 같은 요소 안에서 다음 조·장·절·관 표지 앞까지 자른다. 글자는 고치지 않고 끝의 공백만 뗀다. 없으면 ("", None, 0).
    """
    root = ET.fromstring(xb)
    pat = jo_pat(label)
    hits = []
    for i, e in enumerate(root.iter("조문내용")):
        t = "".join(e.itertext())
        m = pat.search(t)
        if not m:
            continue
        st = m.start()
        while st < len(t) and t[st] in " \t　\n":
            st += 1
        n = JO_END.search(t, m.end())
        hits.append((i, t[st:n.start() if n else len(t)].rstrip()))
    if not hits:
        return "", None, 0
    return hits[0][1], hits[0][0], len(hits)


def annex37(xb):
    u = [x for x in P.annex_units(xb, "0037", "00", "별표")]
    return (u[0]["별표내용"], u[0]["별표제목"], u[0].get("별표서식파일링크", ""), u[0].get("별표서식PDF파일링크", "")) \
        if u else ("", "", "", "")


def norm(s):
    """비교용(판단 기준): 공백·가운뎃점(· ㆍ ․ 와 문자참조 &#8228;)·물음표·마침표·따옴표(“ ” " ‘ ’ ')를 지운 글.
    이것이 같으면 「표기만 다름」."""
    s = (s or "").replace("&#8228;", "")
    return re.sub(r"[\s·ㆍ․?.“”\"‘’']", "", s)


def gaejeongmun(xb, key):
    """<개정문> 글에서 key 가 든 단락(빈 줄로 나눔) — 글자 그대로. 개정문 요소가 없으면 None."""
    g = ET.fromstring(xb).find("개정문")
    if g is None:
        return None
    t = "".join(g.itertext())
    return [p.strip("\n") for p in re.split(r"\n[ \t]*\n", t) if key in p]


# ── 판별 조 글 떼기 ─────────────────────────────────────────────────────────
def _label_file(label):
    return re.sub(r"[\[\]\s]", "", label)


def scan():
    """연혁 목록(이전 에이전트가 오늘 받은 nw=2 목록)의 판마다: 받아 둔 XML 이 있으면 조 글을 떼어 파일로 두고 앞 판과 비교."""
    os.makedirs(ART_DIR, exist_ok=True)
    out = {}
    for name, label in TARGETS:
        rows = P.load_hist(name)
        res, prev = [], None
        for i, r in enumerate(rows):
            s = r["행정규칙일련번호"]
            row = dict(규정=name, 대상=label, 연혁순번=i, 행정규칙일련번호=s, 발령일자=r.get("발령일자", ""),
                       시행일자=r.get("시행일자", ""), 발령번호=r.get("발령번호", ""), 제개정구분=r.get("제개정구분명", ""),
                       현행연혁구분=r.get("현행연혁구분", ""))
            p = ver_path(name, s)
            if not p:
                row.update(판_받음="N", 비고="받지 않음 — 이분 탐색에서 고르지 않은 판")
                res.append(row)
                continue
            xb = open(p, "rb").read()
            meta = meta_of(p)
            inf = P.info(xb)
            if label.startswith("[별표"):
                txt, title, l1, l2 = annex37(xb)
                pos = ""
            else:
                txt, pos, nhit = find_jo(xb, label)
                m = re.match(r"제[\d\s\-]+조(?:의\d+)?\s*\(([^)]*)\)", txt)
                title = m.group(1) if m else ""
            fn = os.path.join(ART_DIR, "%s_%s_%03d_%s_%s.txt" % (_nosp(name), _label_file(label), i,
                                                                 row["발령일자"], s))
            with open(fn, "w", encoding="utf-8") as f:
                f.write(txt)
            if prev is None:
                cmpr = "처음 받은 판"
            elif not prev["_txt"] and not txt:
                cmpr = "같음(둘 다 없음)"
            elif not prev["_txt"]:
                cmpr = "없음→있음"
            elif not txt:
                cmpr = "있음→없음"
            elif prev["_txt"] == txt:
                cmpr = "같음"
            elif norm(prev["_txt"]) == norm(txt):
                cmpr = "표기만 다름(판단)"
            else:
                cmpr = "글 바뀜"
            row.update(판_받음="Y", XML경로=p, XML_sha256=meta.get("sha256", ""), 출처URL=meta.get("출처URL", ""),
                       수집시각=meta.get("fetched_at", ""), XML_발령일자=inf.get("발령일자", ""),
                       XML_시행일자=inf.get("시행일자", ""), XML_발령번호=inf.get("발령번호", ""),
                       조문형식여부=inf.get("조문형식여부", ""), 있음="Y" if txt else "N", 제목=title,
                       ORSA문구="Y" if ORSA_RE.search(txt or "") else "N", 글자수=len(txt), 글_sha256=_sha(txt),
                       정규화_sha256=_sha(norm(txt)), 조문내용_순번="" if pos is None else pos,
                       앞받은판=prev["행정규칙일련번호"] if prev else "",
                       앞받은판과_인접=("Y" if prev and prev["연혁순번"] == i - 1 else ("N" if prev else "")),
                       앞판대비=cmpr, 글파일=fn, _txt=txt)
            res.append(row)
            prev = row
        out[(name, label)] = res
    return out


def open_gaps(res):
    """앞 받은 판과 글이 실질적으로 다른데(없음↔있음·글 바뀜) 사이에 받지 않은 판이 있는 곳 → [(앞 순번, 뒤 순번)]."""
    return [(int([x for x in res if x["행정규칙일련번호"] == r["앞받은판"]][0]["연혁순번"]), r["연혁순번"])
            for r in res if r.get("판_받음") == "Y" and r.get("앞받은판과_인접") == "N"
            and r["앞판대비"] in ("없음→있음", "있음→없음", "글 바뀜")]


def probe():
    """경계(실질 변화)가 인접 판 사이로 닫힐 때까지 가운데 판을 받는다(단조 가정). 닫혀 있으면 요청 0회."""
    client = None
    for _ in range(40):
        res_all = scan()
        todo = []
        for (name, label), res in res_all.items():
            for lo, hi in open_gaps(res):
                todo.append((name, label, lo, hi))
        if not todo:
            break
        name, label, lo, hi = todo[0]
        mid = (lo + hi) // 2
        row = P.load_hist(name)[mid]
        print("경계 열림 %s %s: 순번 %d~%d → 순번 %d(%s %s) 받음" % (name, label, lo, hi, mid,
                                                              row["행정규칙일련번호"], row["발령일자"]))
        client = client or _client()
        fetch_ver(client, name, row["행정규칙일련번호"])
    res_all = scan()
    for (name, label), res in res_all.items():
        got = [r for r in res if r.get("판_받음") == "Y"]
        ch = [r for r in got if r["앞판대비"] not in ("같음", "처음 받은 판", "같음(둘 다 없음)")]
        print("%s %s: 목록 %d판 · 받은 판 %d · 변화 %d(%s)" % (
            name, label, len(res), len(got), len(ch),
            "; ".join("%s %s %s 인접%s" % (r["연혁순번"], r["발령일자"], r["앞판대비"], r["앞받은판과_인접"]) for r in ch)))
    print("요청 %d회" % (client.n_calls if client else 0))


# ── 현행 재확인 ─────────────────────────────────────────────────────────────
def current():
    client = _client()
    rec = {}
    for name, xml9 in ((REG, P.REG_XML9), (SEC, P.SEC_XML9)):
        rows, page = [], 1
        while True:
            st, body, murl, host = client.api("lawSearch.do", target="admrul", type="XML", query=name,
                                              display="100", page=str(page))
            n_oc = client.count_oc(body)
            body = client.mask(body)
            save(TASK, "현행검색_%s_p%d.xml" % (_nosp(name), page), body,
                 dict(출처URL=murl, http_status=st, fetched_at=now(),
                      질의="lawSearch.do target=admrul query=%s display=100 page=%d (nw 없음 = 현행)" % (name, page),
                      OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈(원 응답 바이트와 sha256 다름)" % n_oc)
                      if n_oc else ""))
            root = ET.fromstring(body)
            total = int((root.findtext("totalCnt") or "0").strip() or 0)
            got = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("admrul")]
            rows += got
            if not got or len(rows) >= total or page >= 10:
                break
            page += 1
        keep = [{k: r.get(k, "") for k in ("행정규칙일련번호", "행정규칙명", "발령일자", "시행일자", "발령번호",
                                            "현행연혁구분", "제개정구분명", "소관부처명")}
                for r in rows if r.get("행정규칙명") == name]
        inf9 = P.info(open(xml9, "rb").read())
        rec[name] = dict(질의="lawSearch.do target=admrul query=%s (현행 목록)" % name, 조회시각=now(), totalCnt=total,
                         같은이름행=keep, 받아둔XML=xml9, 받아둔XML_일련번호=inf9.get("행정규칙일련번호", ""),
                         받아둔XML_발령일자=inf9.get("발령일자", ""), 받아둔XML_시행일자=inf9.get("시행일자", ""),
                         같은판=any(k["행정규칙일련번호"] == inf9.get("행정규칙일련번호") for k in keep))
        print("%s: 현행 목록 같은 이름 %d행 %s · 받아 둔 9차 XML %s → 같은 판 %s" % (
            name, len(keep), [(k["행정규칙일련번호"], k["발령일자"], k["시행일자"], k["현행연혁구분"]) for k in keep],
            inf9.get("행정규칙일련번호"), rec[name]["같은판"]))
    with open(CUR_JSON, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("요청 %d회" % client.n_calls)


# ── 산출 ───────────────────────────────────────────────────────────────────
def _fmt(d):
    return "%s.%s.%s" % (d[:4], d[4:6], d[6:8]) if len(d) == 8 else d


def cite(r, where):
    return "[%s · 일련번호 %s(발령 %s · 시행 %s · 발령번호 %s) · %s · %s · 수집 %s]" % (
        r["규정"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["발령번호"],
        r.get("출처URL", ""), where, r.get("수집시각", ""))


def block(t):
    t = t if t.endswith("\n") else t + "\n"
    assert "```" not in t
    return "```text\n" + t + "```\n"


def addendum(xb, date=None, num=None):
    for d, n, t in P.addenda(xb):
        if (date and d == date) or (num and n == num):
            return d, n, t
    return None


def article_of(xb, n):
    """부칙 글에서 「제n조(…)」 한 조(다음 「제k조(」 앞까지)."""
    m = re.search(r"(?m)^제%d조\(" % n, xb)
    if not m:
        return ""
    e = re.search(r"(?m)^제%d조\(" % (n + 1), xb[m.end():])
    return xb[m.start(): m.end() + e.start() if e else len(xb)].rstrip()


def by_serial(res, s):
    return [r for r in res if r["행정규칙일련번호"] == s][0]


def build():
    res_all = scan()
    cur = json.load(open(CUR_JSON, encoding="utf-8")) if os.path.exists(CUR_JSON) else {}
    R = res_all[(REG, "제7-5조")]
    S = res_all[(SEC, "제5-6조의2")]
    A = res_all[(SEC, "[별표 37]")]
    gotR = [r for r in R if r.get("판_받음") == "Y"]
    gotS = [r for r in S if r.get("판_받음") == "Y"]
    gotA = [r for r in A if r.get("판_받음") == "Y"]

    # 경계 판(모두 인접 판 사이로 닫혔는지 확인)
    firstR = [r for r in gotR if r["ORSA문구"] == "Y" and r["앞받은판과_인접"] == "Y"
              and by_serial(R, r["앞받은판"])["ORSA문구"] == "N"]
    assert len(firstR) == 1 and not open_gaps(R) and not open_gaps(S) and not open_gaps(A)
    fR = firstR[0]
    k = fR["연혁순번"]
    beforeR, afterR = R[k - 1], R[k + 1]
    assert beforeR.get("판_받음") == "Y" and afterR.get("판_받음") == "Y"
    chR = [r for r in gotR if r["앞판대비"] == "글 바뀜"]
    curR = [r for r in R if r["현행연혁구분"] == "현행"][0]
    firstS = [r for r in gotS if r["앞판대비"] == "없음→있음"][0]
    chS = [r for r in gotS if r["앞판대비"] == "글 바뀜"]
    curS = [r for r in S if r["현행연혁구분"] == "현행"][0]
    firstA = [r for r in gotA if r["앞판대비"] == "없음→있음"][0]
    chA = [r for r in gotA if r["앞판대비"] == "글 바뀜"]
    curA = [r for r in A if r["현행연혁구분"] == "현행"][0]

    # 판정 칸
    for res in (R, S, A):
        for r in res:
            if r.get("판_받음") != "Y":
                continue
            j = []
            if r["앞판대비"] in ("없음→있음", "글 바뀜"):
                j.append("%s(앞 받은 판 %s 와 %s)" % ("처음 나온 판" if r["앞판대비"] == "없음→있음" else "글 바뀐 판",
                                                 r["앞받은판"], "인접 — 경계 확정" if r["앞받은판과_인접"] == "Y" else "사이 판 있음"))
            if r["앞판대비"] == "표기만 다름(판단)":
                j.append("표기만 다름 — %s" % ("인접" if r["앞받은판과_인접"] == "Y" else
                                           "사이 판은 받지 않아 표기가 바뀐 정확한 판은 추출 범위에 없음"))
            if r["현행연혁구분"] == "현행":
                j.append("현행(연혁 목록)")
            r["판정"] = "; ".join(j)
    fR["판정"] = "「자체 위험 및 지급여력 평가」 문구가 제7-5조에 처음 든 판(앞 판과 인접 — 경계 확정); " + fR["판정"]
    beforeR["판정"] = "문구가 처음 든 판의 앞 판(문구 없음)" + ("; " + beforeR["판정"] if beforeR.get("판정") else "")
    afterR["판정"] = "문구가 처음 든 판의 뒤 판" + ("; " + afterR["판정"] if afterR.get("판정") else "")

    cols = ["규정", "대상", "연혁순번", "행정규칙일련번호", "발령일자", "시행일자", "발령번호", "제개정구분", "현행연혁구분",
            "판_받음", "XML_발령일자", "XML_시행일자", "XML_발령번호", "조문형식여부", "있음", "제목", "ORSA문구", "글자수",
            "글_sha256", "정규화_sha256", "조문내용_순번", "앞받은판", "앞받은판과_인접", "앞판대비", "판정", "글파일",
            "XML경로", "XML_sha256", "출처URL", "수집시각", "비고"]
    rows = [{c: r.get(c, "") for c in cols} for res in (R, S, A) for r in res]
    write_csv(VER_CSV, cols, rows)

    xb = {s: open(ver_path(n, s), "rb").read() for n, s in
          [(REG, x["행정규칙일련번호"]) for x in gotR] + [(SEC, x["행정규칙일련번호"]) for x in gotS]}

    L = []
    w = L.append
    nR, nS = len(gotR), len(gotS)
    law92_files = sorted(f for f in os.listdir(os.path.join(RAW, "law92")) if f.endswith(".xml") and "_2" in f)
    law92a_files = sorted(f for f in os.listdir(D) if f.endswith(".xml") and not f.startswith("현행검색"))
    w("# 9-2 의 1·2 — ORSA(자체 위험 및 지급여력 평가) 연혁: 보험업감독규정 제7-5조, 보험업감독업무시행세칙 제5-6조의2·[별표 37]\n")
    w("- 출처: 국가법령정보센터 Open API — 연혁 판 목록 `lawSearch.do target=admrul query=<이름> nw=2 display=100`(쪽 넘김), "
      "판 본문 `lawService.do target=admrul ID=<행정규칙일련번호> type=XML`, 현행 목록 `lawSearch.do target=admrul query=<이름>`"
      "(요청 URL 의 인증값은 `OC=***`).")
    w("- 수집일: %s. 연혁 목록과 판 XML %d개(보험업감독규정 %d · 세칙 %d)는 같은 날 앞선 에이전트(9-2 전체, 요청 시간 초과로 멈춤)가 "
      "받아 둔 것(`dart_out/raw/web13/law92/`, 원장 `law92/_call_log.csv`, 탐색 기록 `dart_out/risk13/9-2_탐색기록.csv`)을 다시 받지 "
      "않고 그대로 썼고, 현행 판은 9차 XML(`dart_out/raw/web9/law/`)을 썼다. 이번 실행(law92a)에서 새로 받은 판 XML %d개"
      "(제7-5조가 처음 나온 판의 경계를 닫는 이분 탐색, 2003~2006 판), 현행 재확인 검색 %d건(원장 `dart_out/raw/web13/law92a/_call_log.csv`, "
      "LAW_DELAY=1.0). 시각 표기: 메타·인용의 수집 시각은 KST(+09:00), 원장은 UTC — 이번 실행은 2026-10-07 23:58~ UTC(= 2026-10-08 KST 오전)." % (
          TODAY, len(law92_files), len([f for f in law92_files if f.startswith(_nosp(REG) + "_")]),
          len([f for f in law92_files if f.startswith(_nosp(SEC) + "_")]), len(law92a_files),
          len([f for f in os.listdir(D) if f.startswith("현행검색") and f.endswith(".xml")])))
    w("- 방법: ① 연혁 목록(발령일자 순)에서 이분 탐색으로 고른 판만 받아(판 XML 하나가 0.2~5MB) ② 판마다 「제7-5조」·「제5-6조의2」 "
      "글을 떼어 파일로 두고(`dart_out/raw/web13/law92a/조문/`, 판목록 csv 의 「글파일」) ③ 받은 판끼리 앞 판과 비교했다. "
      "감독규정·세칙 XML 은 조문형식여부 N(조문단위·조문번호 칸 없음)이라, 조문내용 요소마다 줄 머리의 「제7-5조」 표지(띄어쓰기 변형 "
      "허용, 「제7-5조의2」 제외)를 찾아 다음 조·장·절·관 표지 앞까지 자르는 함수(`find_jo`)를 새로 만들었다. [별표 37]은 별표단위"
      "(별표번호 0037·가지번호 00·별표구분 별표)의 별표내용을 비교했다. 「자체 위험 및 지급여력 평가」는 정규식 `%s`(띄어쓰기 변형 "
      "포함)로 찾았다." % ORSA_RE.pattern)
    w("- 비교 기준: 글이 글자 그대로 같으면 「같음」, 공백·가운뎃점(`·` `ㆍ` `․` 과 문자참조 `&#8228;`)·물음표·마침표·따옴표 모양만 지워 같으면 "
      "「표기만 다름(판단)」, 그 밖은 「글 바뀜」. 「없음→있음」·「글 바뀜」 경계는 모두 연혁 목록에서 바로 붙은 두 판 사이로 닫혔다"
      "(아래 표). 「표기만 다름」 경계는 사이 판을 받지 않았다.")
    w("- 한계: ① 이분 탐색은 단조 가정(한 번 들어간 문구·글이 사이 판에서 빠졌다 다시 들어가지 않음)에 기댄다 — 받지 않은 사이 판의 "
      "글은 추출 범위에 없음. ② 법제처 XML 글의 글자 오류(문자참조 `&#8228;` 가 풀리지 않은 채 실림, ASCII `?`)는 고치지 않았다. "
      "③ 행정규칙 XML 에 제·개정 이유 칸이 없어 개정 취지는 옮기지 않았다. ④ 관보·금융위원회 고시 원본(PDF/HWP)과의 대조는 하지 않았다. "
      "⑤ 세칙 판의 발령번호는 연혁 목록·XML 모두 「9999」로 실려 있다(법제처 표기 그대로).")
    w("- 표기: 원문 인용은 코드 블록(글자 그대로, 끝 공백만 뗌). 해설은 「note:」 줄, 해석이 들어간 곳은 「(판단)」. 인용 꼬리표는 "
      "[규정 · 일련번호(발령·시행·발령번호) · 요청 URL · 위치 · 수집 시각].")
    w("- 모범규준 조 번호: 지시서 9-2 에는 조 번호가 없다. 4절의 조 번호는 전부 「(판단)」(기준: `dart_out/risk13/모범규준_조목록.csv`, "
      "`handoff/13차_산출물/9-4_모범규준_원문.md` 5절 2016.8.1 판 전문).\n")

    # 0. 요약
    w("## 0. 요약\n")
    w("| 항목 | 판(일련번호) | 발령일 | 판 시행일 | 부칙상 시행일 | 근거 |")
    w("|---|---|---|---|---|---|")
    w("| 감독규정 제7-5조에 「자체 위험 및 지급여력 평가 체제」 문구가 처음 든 판 | %s(금융위원회고시 제%s호, %s) | %s | %s | "
      "제7-5조제1항 개정 규정 2017.1.1(부칙 제1조) | 2-1·2-4·2-5 |" % (fR["행정규칙일련번호"], fR["발령번호"], fR["제개정구분"],
                                                         _fmt(fR["발령일자"]), _fmt(fR["시행일자"])))
    for r in [x for x in gotR if x["앞판대비"] == "없음→있음"]:
        w("| (참고) 감독규정 제7-5조(위험관리체제 등) 자체가 처음 나온 판 | %s(제%s호, %s) | %s | %s | — | 2-1 note |" % (
            r["행정규칙일련번호"], r["발령번호"], r["제개정구분"], _fmt(r["발령일자"]), _fmt(r["시행일자"])))
    for r in chR:
        if r is fR:
            continue
        w("| 감독규정 제7-5조 글 바뀜 | %s(제%s호, %s) | %s | %s | 2-6·2-7 참조 | 2-6·2-7 |" % (
            r["행정규칙일련번호"], r["발령번호"], r["제개정구분"], _fmt(r["발령일자"]), _fmt(r["시행일자"])))
    w("| 세칙 제5-6조의2 신설(처음 나온 판) | %s(%s) | %s | %s | 제5-6조의2 2017.1.1(부칙 제1조) | 3-1·3-3 |" % (
        firstS["행정규칙일련번호"], firstS["제개정구분"], _fmt(firstS["발령일자"]), _fmt(firstS["시행일자"])))
    for r in chS:
        w("| 세칙 제5-6조의2 글 바뀜([별표 37] 로 넘김) | %s(%s) | %s | %s | 2026.6.30(부칙 제1조); 처음 도입하는 보험회사의 평가 시행 2027.1.1(부칙 제3조) | 3-4·3-5 |" % (
            r["행정규칙일련번호"], r["제개정구분"], _fmt(r["발령일자"]), _fmt(r["시행일자"])))
    w("| 세칙 [별표 37] 신설(처음 나온 판) | %s(%s) | %s | %s | 2026.6.30(부칙 제1조); 처음 도입 회사 2027.1.1(부칙 제3조) | 3-6 |" % (
        firstA["행정규칙일련번호"], firstA["제개정구분"], _fmt(firstA["발령일자"]), _fmt(firstA["시행일자"])))
    w("| 현행 감독규정(오늘 재확인) | %s | %s | %s | — | 1·2-8 |" % (curR["행정규칙일련번호"], _fmt(curR["발령일자"]),
                                                             _fmt(curR["시행일자"])))
    w("| 현행 세칙(오늘 재확인) | %s | %s | %s | — | 1·3-7 |\n" % (curS["행정규칙일련번호"], _fmt(curS["발령일자"]),
                                                           _fmt(curS["시행일자"])))

    # 1. 현행 재확인
    w("## 1. 현행 판 재확인(%s UTC — 조회 시각 칸은 KST)\n" % TODAY)
    w("| 규정 | 오늘 현행 목록(일련번호 · 발령 · 시행 · 발령번호 · 구분) | 받아 둔 XML(일련번호 · 발령 · 시행) | 결과 | 조회 시각 |")
    w("|---|---|---|---|---|")
    for name in (REG, SEC):
        c = cur.get(name)
        if not c:
            w("| %s | 추출 범위에 없음(현행 재확인 검색을 돌리지 못함) | | | |" % name)
            continue
        ks = "; ".join("%s · %s · %s · %s · %s" % (k["행정규칙일련번호"], _fmt(k["발령일자"]), _fmt(k["시행일자"]),
                                                k["발령번호"], k["현행연혁구분"] or "(칸 없음)") for k in c["같은이름행"])
        w("| %s | %s | %s · %s · %s (`%s`) | %s | %s |" % (
            name, ks, c["받아둔XML_일련번호"], _fmt(c["받아둔XML_발령일자"]), _fmt(c["받아둔XML_시행일자"]), c["받아둔XML"],
            "같은 판 — 9차 XML 사용" if c["같은판"] else "다름 — 확인 필요", c["조회시각"]))
    w("")
    w("- note: 연혁 목록(nw=2, 같은 날 23:46 KST 조회)에서도 「현행」 표시 판은 보험업감독규정 %s, 세칙 %s 였다." % (
        curR["행정규칙일련번호"], curS["행정규칙일련번호"]))
    w("- note: 현행 목록 검색 응답(`dart_out/raw/web13/law92a/현행검색_*.xml`)은 <행정규칙상세링크> 에 실려 오는 인증값을 저장 전 `***` 로 가렸다"
      "(메타의 「OC가림」).\n")

    # 2. 감독규정 제7-5조
    w("## 2. 보험업감독규정 제7-5조(위험관리체제 등)\n")
    w("### 2-1 「자체 위험 및 지급여력 평가」 문구가 처음 든 판\n")
    w("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | 발령번호 | 제개정 | 제7-5조 | 문구 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for tag, r in (("앞 판", beforeR), ("처음 든 판", fR), ("뒤 판", afterR)):
        w("| %s | %s | %s | %s | %s | 제%s호 | %s | %s(%s자) | %s |" % (
            tag, r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["발령번호"],
            r["제개정구분"], "있음" if r["있음"] == "Y" else "없음", r["글자수"], r["ORSA문구"]))
    w("")
    w("- note: 이분 탐색 경로 — 연혁 목록 %d판(보험업감독규정, 2000.12.29~%s) 가운데 받은 판 %d개: %s. 문구는 순번 %d(%s)에 없고 바로 "
      "다음 순번 %d(%s)에 있다." % (
          len(R), _fmt(R[-1]["발령일자"]), nR, ", ".join("%s(%s, %s)" % (r["연혁순번"], _fmt(r["발령일자"]), r["ORSA문구"])
                                                        for r in gotR),
          beforeR["연혁순번"], beforeR["행정규칙일련번호"], fR["연혁순번"], fR["행정규칙일련번호"]))
    newR = [r for r in gotR if r["앞판대비"] == "없음→있음"]
    if newR:
        n0 = newR[0]
        same = [r for r in gotR if n0["연혁순번"] < r["연혁순번"] <= beforeR["연혁순번"]]
        w("- note: 제7-5조(위험관리체제 등) 자체는 순번 %d(%s, 발령 %s, 제%s호, %s) 판에서 처음 나온다(앞 판 순번 %d(%s)에는 「제7-5조」 표지 없음 "
          "— 인접, 경계 확정). 연혁 목록 첫 판(2000.12.29, 조문형식여부 Y)은 조 번호 체계가 달라 「제61조(위험관리)」 등으로 실려 있다. "
          "그 뒤 받은 판 %s 의 제7-5조 글은 처음 나온 판과 %s." % (
              n0["연혁순번"], n0["행정규칙일련번호"], _fmt(n0["발령일자"]), n0["발령번호"], n0["제개정구분"],
              n0["연혁순번"] - 1, by_serial(R, n0["앞받은판"])["행정규칙일련번호"],
              ", ".join("%s(%s)" % (r["연혁순번"], _fmt(r["발령일자"])) for r in same),
              "글자 그대로 같다" if all(r["글_sha256"] == n0["글_sha256"] for r in same) else "다른 곳이 있다(2-9 표)"))
    w("- note: 처음 든 판의 판 시행일은 %s 이지만, 그 판 부칙 제1조는 「제7-5조제1항 … 의 개정 규정은 2017년 1월 1일부터」 시행한다고 "
      "적었다(2-5). 문구가 든 곳이 제1항이므로 문구의 시행일은 2017.1.1 로 읽힌다(판단).\n" % _fmt(fR["시행일자"]))

    def jo_quote(r, where="제7-5조(조문내용)"):
        w("- 인용: " + cite(r, where))
        w(block(r["_txt"]))

    w("### 2-2 앞 판(%s, 발령 %s) 제7-5조 전문\n" % (beforeR["행정규칙일련번호"], _fmt(beforeR["발령일자"])))
    jo_quote(beforeR)
    w("### 2-3 처음 든 판(%s, 발령 %s) 제7-5조 전문\n" % (fR["행정규칙일련번호"], _fmt(fR["발령일자"])))
    jo_quote(fR)
    w("- note: 제1항의 「평가&#8228;관리」 는 원문 XML 글에 문자참조 여섯 글자 `&#8228;` 가 그대로 실린 것이다(고치지 않음). 같은 자리가 "
      "뒤 판(2016.7.28)에서는 ASCII `?`, 2017.8.28 판부터 `·`, 2022.2.17 판부터 `ㆍ` 로 실려 있다(받은 판 기준).")
    w("- note: 앞 판과 견주면 제1항에 「위험을 적절히 관리하고 내부 자본적정성을 평가…관리할 수 있는 체제(이하 \"자체 위험 및 지급여력 평가 "
      "체제\"라고 한다)를 갖추어야 하며, 세부사항은 감독원장이 정한다」가, 제2항 위험 목록에 「운영위험」이 들어갔다(두 항 모두 "
      "「<개정 2016.4.1>」 표지).\n")
    gm = gaejeongmun(xb[fR["행정규칙일련번호"]], "제7-5조")
    ad_first = addendum(xb[fR["행정규칙일련번호"]], num=fR["발령번호"])
    w("### 2-4 처음 든 판의 개정문 가운데 제7-5조 부분\n")
    if gm:
        for j, g in enumerate(gm, 1):
            w("- 인용(단락 %d/%d): " % (j, len(gm)) + cite(fR, "<개정문> 가운데 「제7-5조」가 든 단락(빈 줄로 나눈 단락)"))
            w(block(g))
        for j, g in enumerate(gm, 1):
            if g.startswith("제1조(시행일)") and g in ad_first[2]:
                w("- note: %d번째 단락은 개정문 끝에 실린 부칙 제1조로, 2-5 의 부칙 제1조와 글자 그대로 같다.\n" % j)
    else:
        w("- 추출 범위에 없음: %s XML 의 <개정문> 에서 「제7-5조」 단락을 찾지 못함.\n" % fR["행정규칙일련번호"])
    ad = addendum(xb[fR["행정규칙일련번호"]], num=fR["발령번호"])
    w("### 2-5 처음 든 판의 부칙(시행일·적용례) 전문\n")
    w("- 인용: " + cite(fR, "<부칙> 부칙공포일자 %s · 부칙공포번호 %s · 부칙내용" % (ad[0], ad[1])))
    w(block(ad[2]))
    curxbR = open(P.REG_XML9, "rb").read()
    ad_c = addendum(curxbR, num=fR["발령번호"])
    w("- note: 현행 판(%s) XML 에 실린 같은 부칙(부칙공포번호 %s)과 견주면: %s." % (
        curR["행정규칙일련번호"], fR["발령번호"],
        "글자 그대로 같음" if ad_c and ad_c[2] == ad[2] else
        ("표기(공백·가운뎃점·마침표·따옴표 모양)만 다름(판단)" if ad_c and norm(ad_c[2]) == norm(ad[2]) else "다름 — 현행 판 부칙은 추출 범위 확인 필요")))
    w("- note: 현행 판 XML 부칙 %d건을 「7-5조|자체\\s*위험|지급여력\\s*평가|ORSA」 로 찾으면 맞는 부칙은 %s 이다." % (
        len(P.addenda(curxbR)), ", ".join("%s(%s)" % (n, _fmt(d)) for d, n, t in P.addenda(curxbR)
                                          if re.search(r"7-5조|자체\s*위험|지급여력\s*평가|ORSA", t))))
    w("")

    w("### 2-6 뒤 판(%s, 발령 %s · %s) 제7-5조 전문과 그 판의 개정 글\n" % (afterR["행정규칙일련번호"], _fmt(afterR["발령일자"]),
                                                            afterR["제개정구분"]))
    jo_quote(afterR)
    gm2 = gaejeongmun(xb[afterR["행정규칙일련번호"]], "제7-5조")
    if gm2:
        for j, g in enumerate(gm2, 1):
            w("- 인용(단락 %d/%d): " % (j, len(gm2)) + cite(afterR, "<개정문> 가운데 「제7-5조」가 든 단락"))
            w(block(g))
    ad2 = addendum(xb[afterR["행정규칙일련번호"]], num=afterR["발령번호"])
    if ad2:
        w("- 인용: " + cite(afterR, "<부칙> 부칙공포일자 %s · 부칙공포번호 %s · 부칙내용" % (ad2[0], ad2[1])))
        w(block(ad2[2]))
    w("- note: 이 판은 부칙 머리줄대로 「금융회사 지배구조 감독규정」(제2016-30호) 부칙 제2조제2항의 다른 규정 개정(타법개정)으로 생긴 판이다. "
      "제1항 근거가 「영 제65조제2항제3호」 에서 「「금융회사의 지배구조에 관한 법률」 제27조」 로 바뀌었고, 그 결과 이 판부터 현행까지 "
      "제1항에 「보험회사는」 이 두 번 나온다(원문 그대로). 제7-5조 글에는 이 개정의 표지가 붙어 있지 않다.\n")

    later = [r for r in chR if r is not fR and r is not afterR]
    for r in later:
        pv = by_serial(R, r["앞받은판"])
        w("### 2-7 제2항 위험 목록이 바뀐 판(%s, 발령 %s · 시행 %s)\n" % (r["행정규칙일련번호"], _fmt(r["발령일자"]),
                                                            _fmt(r["시행일자"])))
        w("- 앞 판(%s, 발령 %s) 제7-5조 전문" % (pv["행정규칙일련번호"], _fmt(pv["발령일자"])))
        jo_quote(pv)
        w("- 바뀐 판(%s) 제7-5조 전문" % r["행정규칙일련번호"])
        jo_quote(r)
        gm3 = gaejeongmun(xb[r["행정규칙일련번호"]], "제7-5조")
        if gm3 is None:
            w("- note: 이 판 XML 에는 <개정문> 요소가 없다.")
        ad3 = addendum(xb[r["행정규칙일련번호"]], num=r["발령번호"])
        if ad3:
            a1 = article_of(ad3[2], 1)
            hd = ad3[2].split("\n", 1)[0]
            w("- 인용(발췌: 부칙 머리줄과 제1조): " + cite(r, "<부칙> 부칙공포번호 %s · 부칙내용" % ad3[1]))
            w(block(hd + "\n" + a1))
            w("- note: 이 부칙(%d자)의 제2조 이하에서 「7-5」·「자체 위험」·「위험관리체제」 글자를 찾으면 %d곳 — 제1조만 옮겼다." % (
                len(ad3[2]), len(re.findall(r"7-5|자체\s*위험|위험관리체제", ad3[2][len(hd) + len(a1) + 1:]))))
        w("- note: 제2항 끝 개정 표지는 「2022. 12. 21.」 인데 연혁 목록·XML 의 발령일자와 부칙 머리줄은 2022.12.22 이다(원문과 다른 곳).")
        w("- note: 제2항의 「보험위험, 금리위험」 이 「생명ㆍ장기손해보험위험, 일반손해보험위험」 으로 바뀌었다. 판 시행일 2023.1.1 은 "
          "지급여력제도(K-ICS) 시행과 같은 날이다(판단, 9-2-5 별표22 쪽 자료와 대조 필요).\n")

    w("### 2-8 현행 제7-5조 전문(%s, 발령 %s · 시행 %s — 오늘 현행)\n" % (curR["행정규칙일련번호"], _fmt(curR["발령일자"]),
                                                                _fmt(curR["시행일자"])))
    jo_quote(curR)
    w("- note: 현행 글은 %s 판(발령 %s)의 제7-5조와 글자 그대로 같다(sha256 %s…).\n" % (
        later[-1]["행정규칙일련번호"] if later else "", _fmt(later[-1]["발령일자"]) if later else "", curR["글_sha256"][:12]))

    w("### 2-9 받은 판별 제7-5조 글 대조(판목록 csv 요약)\n")
    w("| 연혁순번 | 일련번호 | 발령 | 시행 | 제개정 | 글자수 | 문구 | 앞 받은 판 대비 | 인접 | 글 sha256(앞 12자) |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in gotR:
        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["제개정구분"], r["글자수"],
            r["ORSA문구"], r["앞판대비"], r["앞받은판과_인접"], r["글_sha256"][:12]))
    w("")
    w("- note: 「표기만 다름(판단)」 칸은 가운뎃점 바꿈(`&#8228;`→`?`→`·`→`ㆍ`)·공백·개정 표지 띄어쓰기(「<개정 2016.4.1>」→「<개정 2016. 4. 1.>」)"
      "·줄바꿈 차이다. 「인접」이 N 인 경계는 사이 판을 받지 않아 표기가 바뀐 정확한 판은 추출 범위에 없음.\n")

    # 3. 세칙
    w("## 3. 보험업감독업무시행세칙 제5-6조의2(자체 위험 및 지급여력 평가)·[별표 37]\n")
    pS = by_serial(S, firstS["앞받은판"])
    w("### 3-1 제5-6조의2가 처음 나온 판(신설)\n")
    w("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | 제개정 | 제5-6조의2 |")
    w("|---|---|---|---|---|---|---|")
    for tag, r in (("앞 판", pS), ("처음 나온 판", firstS)):
        w("| %s | %s | %s | %s | %s | %s | %s |" % (tag, r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]),
                                               _fmt(r["시행일자"]), r["제개정구분"],
                                               "있음(%s자)" % r["글자수"] if r["있음"] == "Y" else "없음"))
    w("")
    w("- note: 이분 탐색 경로 — 연혁 목록 %d판(세칙) 가운데 받은 판 %d개: %s." % (
        len(S), nS, ", ".join("%s(%s, %s)" % (r["연혁순번"], _fmt(r["발령일자"]), r["있음"]) for r in gotS)))
    w("- note: 처음 나온 판의 판 시행일은 %s 이지만 그 판 부칙은 「제5-3조의2, 제5-6조의2, 별표 33의 규정은 2017년 1월 1일부터 시행」 한다고 "
      "적었다(3-3). 조 끝 표지는 「<신설 2016.4.28>」.\n" % _fmt(firstS["시행일자"]))
    w("### 3-2 신설 당시 제5-6조의2 전문(%s, 발령 %s)\n" % (firstS["행정규칙일련번호"], _fmt(firstS["발령일자"])))
    w("- 인용: " + cite(firstS, "제5-6조의2(조문내용)"))
    w(block(firstS["_txt"]))
    w("- note: 제2항이 이사회 결정에 따른 「자체 위험 및 지급여력 평가체제 구축」 유예를 두었다(원문 「유예할 수 있다」).\n")
    adS = addendum(xb[firstS["행정규칙일련번호"]], date=firstS["발령일자"])
    w("### 3-3 신설 판(2016.4.28)의 부칙 전문\n")
    w("- 인용: " + cite(firstS, "<부칙> 부칙공포일자 %s · 부칙공포번호 %s · 부칙내용" % (adS[0], adS[1])))
    w(block(adS[2]))
    curxbS = open(P.SEC_XML9, "rb").read()
    adS_c = addendum(curxbS, date=firstS["발령일자"])
    w("- note: 현행 판(%s) XML 에 실린 같은 날짜 부칙과 견주면: %s.\n" % (
        curS["행정규칙일련번호"], "글자 그대로 같음" if adS_c and adS_c[2] == adS[2] else
        ("표기만 다름 — 제2조의 겹따옴표 모양(“ ” ↔ \" \")만 다르고 나머지 글자는 같음(판단)" if adS_c and norm(adS_c[2]) == norm(adS[2])
         else "다름 — 아래 원문 둘 다 확인 필요")))
    for r in chS:
        pv = by_serial(S, r["앞받은판"])
        w("### 3-4 제5-6조의2 글이 바뀐 판(%s, 발령 %s · 시행 %s)\n" % (r["행정규칙일련번호"], _fmt(r["발령일자"]),
                                                            _fmt(r["시행일자"])))
        w("- 앞 판(%s, 발령 %s — 바로 앞 판) 제5-6조의2 전문" % (pv["행정규칙일련번호"], _fmt(pv["발령일자"])))
        w("- 인용: " + cite(pv, "제5-6조의2(조문내용)"))
        w(block(pv["_txt"]))
        w("- 바뀐 판(%s) 제5-6조의2 전문" % r["행정규칙일련번호"])
        w("- 인용: " + cite(r, "제5-6조의2(조문내용)"))
        w(block(r["_txt"]))
        w("- note: 신설 당시(3-2)와 앞 판의 차이는 가운뎃점(`·`→`ㆍ`)·공백·신설 표지 띄어쓰기뿐이다(표기만 다름, 판단). 신설 뒤 글이 실질적으로 "
          "바뀐 판은 받은 판 가운데 이 판 하나다(조 끝 표지 「<신설 2016. 4. 28., 개정 2026. 6. 29.>」 와 맞음).\n")
        adX = addendum(xb[r["행정규칙일련번호"]], date=r["발령일자"])
        w("### 3-5 바뀐 판(2026.6.29)의 부칙 전문(제1조·제2조·제3조)\n")
        w("- 인용: " + cite(r, "<부칙> 부칙공포일자 %s · 부칙공포번호 %s · 부칙내용" % (adX[0], adX[1])))
        w(block(adX[2]))
        adX_c = addendum(curxbS, date=r["발령일자"])
        w("- note: 현행 판(%s) XML 의 같은 날짜 부칙과 견주면: %s." % (
            curS["행정규칙일련번호"], "글자 그대로 같음" if adX_c and adX_c[2] == adX[2] else
            ("표기(공백·가운뎃점·마침표·따옴표 모양)만 다름(판단)" if adX_c and norm(adX_c[2]) == norm(adX[2]) else "다름")))
        w("- note: 이 판의 판 시행일(연혁 목록·XML)은 %s 이다.\n" % _fmt(r["시행일자"]))

    w("### 3-6 [별표 37] 신설과 연혁\n")
    pA = by_serial(A, firstA["앞받은판"])
    w("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | [별표 37] 제목(별표제목 칸) | 별표내용 글자수 | sha256(앞 12자) |")
    w("|---|---|---|---|---|---|---|---|")
    for tag, r in (("앞 판", pA), ("처음 나온 판", firstA), ("현행", curA)):
        w("| %s | %s | %s | %s | %s | %s | %s | %s |" % (tag, r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]),
                                                    _fmt(r["시행일자"]), r["제목"] or "(별표 37 없음)", r["글자수"],
                                                    r["글_sha256"][:12]))
    w("")
    w("- note: 받은 세칙 판 %d개 가운데 [별표 37](별표구분 「별표」)이 있는 판은 %s 뿐이고, 처음 나온 판과 현행 판의 별표내용은 글자 그대로 같다"
      "(사이 판 %s 은 받지 않음). 앞 판에 [별표 37] 은 없다(같은 번호의 「별지 37」(수습연기신청서)은 별개)." % (
          len(gotA), ", ".join(r["행정규칙일련번호"] for r in gotA if r["있음"] == "Y"),
          ", ".join(r["행정규칙일련번호"] for r in A[firstA["연혁순번"] + 1:curA["연혁순번"]])))
    if chA:
        w("- note: [별표 37] 글이 바뀐 판: %s" % ", ".join(r["행정규칙일련번호"] for r in chA))
    a37, t37, l1, l2 = annex37(curxbS)
    hl, nn = [], 0
    for x in a37.split("\n"):                       # 빈 줄까지 그대로, 글이 든 줄 4개째에서 멈춤(이어진 앞부분)
        hl.append(x)
        nn += 1 if x.strip() else 0
        if nn == 4:
            break
    w("- 인용(발췌: 별표내용 앞부분 — 글이 든 줄 4개까지, 빈 줄 포함): " + cite(curA, "[별표 37] 별표내용"))
    w(block("\n".join(hl)))
    w("- note: 별표내용 첫 줄의 신설 표지(「<신설 2026.06.29.>」)가 연혁 목록의 처음 나온 판 발령일(2026.6.29)과 맞는다.\n")
    lines = a37.split("\n")
    st = [i for i, x in enumerate(lines) if "3. (적용 대상)" in x]
    if st:
        en = [i for i in range(st[0] + 1, len(lines)) if re.search(r"│\s*4\.\s*\(|제\s*2\s*장", lines[i])]
        seg = "\n".join(lines[st[0]: en[0] if en else min(len(lines), st[0] + 40)])
        w("- 인용(발췌: 제1장 3.(적용 대상) — 2026.6.29 부칙 제3조가 가리키는 곳): " + cite(curA, "[별표 37] 별표내용 제1장 3."))
        w(block(seg))
        w("- note: XML 별표내용은 한 칸짜리 표를 상자 그리기 문자(│ 등)로 옮긴 글이라 줄이 표 너비로 잘려 있다(원문 그대로). 같은 부분의 "
          "PDF 글은 10차 `%s` 의 「적용 대상(제1장 3.)」 행(flSeq=168886111 · 168886133)에 있다." % A37_CSV10)
    else:
        w("- 추출 범위에 없음: 현행 [별표 37] 별표내용에서 「3. (적용 대상)」 줄을 찾지 못함.")
    w("- note: 원본 파일 링크(받지 않음): HWP http://www.law.go.kr%s · PDF http://www.law.go.kr%s . [별표 37] 전문과 1.~20. 항목 대조는 "
      "9-2 의 3번 작업 몫이다.\n" % (l1, l2))

    w("### 3-7 현행 제5-6조의2 전문(%s, 발령 %s · 시행 %s — 오늘 현행)\n" % (curS["행정규칙일련번호"], _fmt(curS["발령일자"]),
                                                                 _fmt(curS["시행일자"])))
    w("- 인용: " + cite(curS, "제5-6조의2(조문내용)"))
    w(block(curS["_txt"]))
    w("### 3-8 받은 판별 제5-6조의2·[별표 37] 대조(판목록 csv 요약)\n")
    w("| 연혁순번 | 일련번호 | 발령 | 시행 | 제5-6조의2 글자수 | 앞 받은 판 대비 | 인접 | [별표 37] | 별표 앞 판 대비 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in gotS:
        a = by_serial(A, r["행정규칙일련번호"])
        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["글자수"], r["앞판대비"],
            r["앞받은판과_인접"], "있음(%s자)" % a["글자수"] if a["있음"] == "Y" else "없음", a["앞판대비"]))
    w("")
    w("### 3-9 부칙의 유예·적용례 — 찾은 범위\n")
    pat = r"5-6조의2|별표\s*37|자체\s*위험|지급여력\s*평가|ORSA|내부모형"
    hitS = [(d, n) for d, n, t in P.addenda(curxbS) if re.search(pat, t)]
    w("- 현행 세칙 XML(%s) 부칙 %d건을 정규식 `%s` 로 찾은 결과: %s. 3-3·3-5 에 두 부칙 전문을 옮겼다." % (
        curS["행정규칙일련번호"], len(P.addenda(curxbS)), pat, ", ".join("부칙공포일자 %s" % _fmt(d) for d, n in hitS)))
    w("- 유예 규정이 든 곳(원문 위치만): 신설 당시 제5-6조의2 제2항(3-2), 2016.4.28 부칙(3-3, 2017.1.1 시행), 2026.6.29 부칙 제1조·제3조(3-5), "
      "[별표 37] 제1장 3.(적용 대상) 가.~라.(3-6).\n")

    # 4. 모범규준 조 대응
    w("## 4. 모범규준 조 번호(모두 판단)\n")
    w("| 자료 | 닿는 모범규준 조(2016.8.1 판 제목) | 근거(판단) |")
    w("|---|---|---|")
    w("| 감독규정 제7-5조제1항(위험 관리 + 내부 자본적정성 평가·관리 체제 = 「자체 위험 및 지급여력 평가 체제」) | 제37조(자본적정성 평가 및 관리 체제)"
      " · 제5장(제36~49조) 전반 (판단) | 내부 자본적정성 평가·관리 체제 구축 의무가 제37조제1항과 같은 짜임 |")
    w("| 감독규정 제7-5조제2항(위험 종류별 측정·관리: 생명ㆍ장기손해보험·일반손해보험·시장·신용·운영위험) | 제18조(측정 및 관리 대상) · 제19조(위험 측정)"
      " · 제21조(신용위험) · 제22조(시장위험) · 제23조(운영위험) (판단) | 위험 유형별 측정·관리 |")
    w("| 감독규정 제7-5조제3항·제4항(측정결과의 경영목표 반영, 위험부담한도·거래한도) | 제20조(위험 관리) · 제35조(경영에의 활용) (판단) | "
      "측정 결과를 한도·경영의사결정에 반영 |")
    w("| 감독규정 제7-5조제6항(주요 위험의 변동상황을 자회사와 연결하여 인식·감시) | 제19조(위험 측정) · 제33조(그룹내 위험 전이 방지) (판단) | "
      "자회사와 연결한 위험 인식 — 지주 통합위험 측정과 닿음 |")
    w("| 세칙 제5-6조의2(2016판) 제1항 제1호(연 1회 이상, 이사회 승인) | 제39조(이사회 및 경영진의 감독) · 제48조(보고) (판단) | 이사회 감독·정기 보고 |")
    w("| 세칙 제5-6조의2(2016판) 제1항 제2호(중요한 리스크 모두 식별·평가) | 제42조(위험 인식) · 제43조(위험 평가) (판단) | 모든 중요 위험 감안 |")
    w("| 세칙 제5-6조의2(2016판) 제1항 제3호·제4호(필요 지급여력 수준 평가, 내부모형) | 제44조(통합 내부자본 산출) · 제45조(가용자본 산출) · "
      "제46조(평가 및 관리) (판단) | 소요 자본 산출·가용자본 비교 |")
    w("| 세칙 제5-6조의2(2016판) 제1항 제5호(한도설정·자본계획·성과평가·배당결정에 활용) | 제47조(내부자본 한도 관리) · 제49조(자본계획) · "
      "제35조(경영에의 활용) (판단) | 한도·자본계획 |")
    w("| 세칙 제5-6조의2 제2항(이사회 결정으로 구축 유예), 2016.4.28·2026.6.29 부칙, [별표 37] 제1장 3.(적용 대상·유예) | "
      "제36조(적용대상) · 제3조(적용대상) (판단) | 적용 대상·제외 기준 |")
    w("| 세칙 제5-6조의2(2016판) 제3항(감독원장이 경영실태평가로 적정성 평가) | 맞는 조를 조목록 제목에서 찾지 못함 — 주제1 표의 「자회사 평가·기준(RAAS 등)」 칸 "
      "자료로 봄 (판단) | 감독당국 평가는 모범규준(지주 내부 기준)의 조 범위 밖 |")
    w("| 현행 세칙 제5-6조의2(세부사항은 [별표 37]) | 제5장(제36~49조) 전반 (판단) | [별표 37] 의 항목별 대응은 9-2 의 3번 몫 |")
    w("")
    w("- note: 감독규정·세칙은 보험회사에 적용되는 기준이라 주제1 표에서는 「자회사 평가·기준(RAAS 등)」 칸 자료다(판단).\n")

    # 5. 받은 것 / 받지 못한 것 / 다른 곳
    w("## 5. 받은 것 / 받지 못한 것 / 원문과 다른 것\n")
    w("| 구분 | 항목 | 위치·사유 |")
    w("|---|---|---|")
    w("| 받은 것 | 감독규정 제7-5조 문구가 처음 든 판: %s(발령 %s · 시행 %s · 금융위원회고시 제%s호), 앞뒤 판 제7-5조 전문, 그 판 개정문·부칙 전문, "
      "현행 제7-5조 전문 | 2-1~2-8 |" % (fR["행정규칙일련번호"], _fmt(fR["발령일자"]), _fmt(fR["시행일자"]), fR["발령번호"]))
    w("| 받은 것 | 세칙 제5-6조의2 신설 판 %s(발령 %s), 바뀐 판 %s(발령 %s), 2016.4.28·2026.6.29 부칙 전문, 현행 전문, [별표 37] 신설 판·제1장 3. | 3-1~3-7 |" % (
        firstS["행정규칙일련번호"], _fmt(firstS["발령일자"]), chS[0]["행정규칙일련번호"] if chS else "", _fmt(chS[0]["발령일자"]) if chS else ""))
    w("| 받은 것 | 현행 판 재확인(감독규정·세칙 모두 9차 XML 과 같은 판) | 1 |")
    w("| 추출 범위에 없음 | 표기만 바뀐 경계(가운뎃점·공백)의 정확한 판 | 사이 판을 받지 않음(판목록 csv 「판정」 칸) |")
    w("| 추출 범위에 없음 | 받지 않은 사이 판의 제7-5조·제5-6조의2 글 | 단조 가정으로 건너뜀 — 판목록 csv 「판_받음」 N |")
    w("| 추출 범위에 없음 | 개정 이유(제·개정 이유서) | 행정규칙 XML 에 칸 없음; 다른 경로(관보·금융위 보도자료)는 이번 범위 밖 — 보도자료는 9-2 의 4번 몫 |")
    w("| 원문과 다른 곳 | 처음 든 판의 판 시행일(%s)과 부칙상 제7-5조제1항 시행일(2017.1.1)이 다름 | 2-5 |" % _fmt(fR["시행일자"]))
    w("| 원문과 다른 곳 | 세칙 2016.4.28 판 시행일(2016.4.28)과 부칙상 제5-6조의2 시행일(2017.1.1)이 다름 | 3-3 |")
    w("| 원문과 다른 곳 | 현행 제7-5조제2항 개정 표지 「2022. 12. 21.」 ↔ 연혁 목록·XML 발령일자·부칙 머리줄 2022.12.22 | 2-7 |")
    w("| 원문과 다른 곳 | 2016.4.1 판 XML 의 「평가&#8228;관리」(문자참조가 풀리지 않음), 2016.7.28 판의 「평가?관리」 | 2-3 |")
    w("| 원문과 다른 곳 | 현행 제7-5조제1항 「보험회사는 … 제27조의 규정에 의하여 보험회사는」(「보험회사는」 두 번 — 2016.7.28 타법개정 글 그대로) | 2-6 |")
    w("| 원문과 다른 곳 | 지시서 「'자체 위험 및 지급여력 평가 체제' 문구」 — 제7-5조 원문은 「(이하 \"자체 위험 및 지급여력 평가 체제\"라고 한다)」, "
      "세칙은 「평가체제」(붙여 씀)·[별표 37] 제목 「지급여력평가체제」·2026 부칙 「지급여력평가」 로 띄어쓰기가 섞임 | 2-3·3-2·3-5·3-6 |")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L).rstrip("\n") + "\n")
    print("md %s (%d줄) · csv %s (%d행)" % (OUT_MD, len(L), VER_CSV, len(rows)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"current": current, "probe": probe, "build": build}.get(cmd)
    if not fn:
        raise SystemExit(__doc__)
    fn()
