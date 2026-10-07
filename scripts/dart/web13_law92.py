# -*- coding: utf-8 -*-
"""13차 9-2 ORSA 연혁과 보험 쪽 기준(1·2·3·5번). 실행은 저장소 루트에서.

    LAW_DELAY=1.0 python3 scripts/dart/web13_law92.py hist      # 보험업감독규정·세칙 연혁 판 목록(lawSearch admrul nw=2)
    LAW_DELAY=1.0 python3 scripts/dart/web13_law92.py reg75     # 감독규정 제7-5조: 이분 탐색으로 「자체 위험 및 지급여력 평가」가 처음 든 판
    LAW_DELAY=1.0 python3 scripts/dart/web13_law92.py sec562    # 세칙 제5-6조의2·별표37: 처음 든 판·바뀐 판
    python3 scripts/dart/web13_law92.py build                   # 산출 md·판목록 csv(추가 요청 없음)

원칙(13차 COMMON13.md):
  - 법제처 OC 는 lawclient 가 env/.env 에서 읽고, 원장·메타·산출물에는 OC=*** 로만 남는다.
  - 원장: dart_out/raw/web13/law92/_call_log.csv. 이미 받은 XML(web9/web10/web11)은 다시 받지 않는다.
  - 받은 판 XML 은 dart_out/raw/web13/law92/<이름>_<일련번호>.xml (+ .meta.json, sha256).
  - 원문은 글자 그대로 옮긴다(공백·줄바꿈 정리 없음). 해설은 md 의 「note:」 줄에만.
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

TASK = "law92"
D = os.path.join(RAW, TASK)
LEDGER = os.path.join(D, "_call_log.csv")
REG = "보험업감독규정"
SEC = "보험업감독업무시행세칙"
REG_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독규정_2100000279112.xml")
SEC_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독업무시행세칙_2200000108939.xml")
A37_MD10 = os.path.join("handoff", "원문_10차", "세칙_별표37.md")
A37_CSV10 = os.path.join("handoff", "원문_10차", "세칙_별표37_표시.csv")
A37_PDF10 = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37_pdf.txt")
A37_PDF10_BIN = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37.pdf")
OUT_MD = os.path.join(OUT, "9-2_ORSA_보험기준.md")
VER_CSV = os.path.join(WORK, "9-2_판목록.csv")          # 연혁 판 전부 + 받은 판의 확인 결과(build)
PROBE_CSV = os.path.join(WORK, "9-2_탐색기록.csv")      # 이분 탐색에서 본 판과 판정(reg75·sec562)
TODAY = "20261007"

# 「자체 위험 및 지급여력 평가」 — 띄어쓰기 변형(「자체위험」·「지급여력평가」) 포함
ORSA_RE = re.compile(r"자체\s*위험\s*및\s*지급여력\s*평가")


def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


def _t(e, tag):
    return (e.findtext(tag) or "").strip()


# ── 연혁 판 목록 ──────────────────────────────────────────────────────────
def _hist_path(name):
    return os.path.join(D, "연혁목록_%s.json" % name)


def search_hist(client, name):
    """lawSearch target=admrul query=<name> nw=2 — 모든 페이지(display=100). 원 응답은 페이지마다 저장."""
    rows, page, total = [], 1, None
    while True:
        st, body, murl, host = client.api("lawSearch.do", target="admrul", type="XML", query=name,
                                          display="100", page=str(page), nw="2")
        if not body:
            raise SystemExit("연혁 검색 실패: %s" % murl)
        # 실측(2026-10-07): 검색 응답의 <행정규칙상세링크> 에 OC 값이 그대로 실려 온다 → 저장·파싱 전에 가린다.
        n_oc = client.count_oc(body)
        body = client.mask(body)
        save(TASK, "연혁검색_%s_nw2_p%d.xml" % (name, page), body,
             dict(출처URL=murl, http_status=st, fetched_at=now(), 질의="target=admrul query=%s nw=2 display=100 page=%d"
                  % (name, page), OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈(원 응답 바이트와 sha256 다름)" % n_oc)
                  if n_oc else ""))
        root = ET.fromstring(body)
        total = int((root.findtext("totalCnt") or "0").strip() or 0)
        got = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("admrul")]
        rows += got
        if not got or len(rows) >= total or page >= 30:
            break
        page += 1
    keep = [r for r in rows if r.get("행정규칙명") == name]
    keep.sort(key=lambda r: (r.get("발령일자", ""), r.get("시행일자", ""), r.get("행정규칙일련번호", "")))
    with open(_hist_path(name), "w", encoding="utf-8") as f:
        json.dump(dict(질의="lawSearch.do target=admrul query=%s nw=2 display=100" % name, totalCnt=total,
                       받은행=len(rows), 같은이름행=len(keep), fetched_at=now(), rows=keep), f, ensure_ascii=False,
                  indent=1)
    return keep, total, len(rows)


def hist():
    client = _client()
    for name in (REG, SEC):
        keep, total, n = search_hist(client, name)
        print("%s: totalCnt %s · 받은 %d · 같은 이름 %d · 발령 %s ~ %s" % (
            name, total, n, len(keep), keep[0].get("발령일자") if keep else "", keep[-1].get("발령일자") if keep else ""))
    print("호출 %d회" % client.n_calls)


def load_hist(name):
    return json.load(open(_hist_path(name), encoding="utf-8"))["rows"]


# ── 판 XML ────────────────────────────────────────────────────────────────
OLD_DIRS = [os.path.join("dart_out", "raw", w, "law") for w in ("web9", "web10", "web11")]


def _nosp(s):
    return re.sub(r"\s+", "", s or "")


def ver_file(name, serial):
    """이미 받은 판(9~11차 또는 이번 law92) → 경로, 없으면 None."""
    for d in OLD_DIRS + [D]:
        p = os.path.join(d, "%s_%s.xml" % (_nosp(name), serial))
        if os.path.exists(p):
            return p
    return None


def get_ver(client, name, serial):
    """판 XML 바이트와 (경로, 메타). 없을 때만 lawService.do target=admrul ID=<일련번호> type=XML 로 받는다."""
    p = ver_file(name, serial)
    if p:
        mp = p + ".meta.json"
        meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
        return open(p, "rb").read(), p, meta
    if client is None:
        raise SystemExit("판 %s %s 이 없음 — 요청 없는 build 단계" % (name, serial))
    st, body, murl, host = client.api("lawService.do", target="admrul", ID=serial, type="XML")
    root = ET.fromstring(body)
    got = _t(root.find("행정규칙기본정보"), "행정규칙일련번호") if root.find("행정규칙기본정보") is not None else ""
    if got != serial:
        raise SystemExit("요청 %s 인데 응답 일련번호 %s — %s" % (serial, got, murl))
    n_oc = client.count_oc(body)
    body = client.mask(body)                        # 본문에 OC 가 실려 오면 가린다(판 XML 은 실측 0곳)
    p, meta = save(TASK, "%s_%s.xml" % (_nosp(name), serial), body,
                   dict(출처URL=murl, http_status=st, fetched_at=now(), 호스트=host,
                        OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈" % n_oc) if n_oc else ""))
    print("  받음 %s %s (%d바이트)" % (name, serial, len(body)))
    return body, p, meta


def info(xb):
    b = ET.fromstring(xb).find("행정규칙기본정보")
    return {c.tag: (c.text or "").strip() for c in b} if b is not None else {}


def body_text(xb):
    """조문내용 전부(문서 순서, 글자 그대로). 조문형식여부 Y 판이면 조문단위 아래 글을 이어 붙인다."""
    root = ET.fromstring(xb)
    parts = ["".join(e.itertext()) for e in root.iter("조문내용")]
    return "\n".join(parts)


ART_END = re.compile(r"(?m)^[ \t　]*(?:제\s*\d+\s*-\s*\d+\s*조|제\s*\d+\s*장|제\s*\d+\s*절)")


def find_article(xb, label):
    """「제7-5조」·「제5-6조의2」 조 글(제목 줄부터 다음 조·장·절 표지 앞까지, 글자 그대로). 없으면 ""."""
    t = body_text(xb)
    m = re.match(r"제(\d+)-(\d+)조(?:의(\d+))?$", label)
    a, b, g = m.group(1), m.group(2), m.group(3)
    pat = r"(?m)^[ \t　]*제\s*%s\s*-\s*%s\s*조%s" % (a, b, (r"\s*의\s*%s(?!\d)" % g) if g else r"(?!\s*의\s*\d)")
    s = re.search(pat, t)
    if not s:
        return ""
    st = s.start()
    while st < len(t) and t[st] in " \t　":
        st += 1
    e = ART_END.search(t, s.end())
    return t[st:e.start() if e else len(t)].rstrip("\n")


def annex_units(xb, no, gaji="00", kind="별표"):
    root = ET.fromstring(xb)
    out = []
    for u in root.iter("별표단위"):
        if (_t(u, "별표번호") == no and (_t(u, "별표가지번호") or "00") == gaji and _t(u, "별표구분") == kind):
            out.append({k: _t(u, k) for k in ("별표번호", "별표가지번호", "별표구분", "별표제목", "별표서식파일링크",
                                              "별표서식PDF파일링크")} | {"별표내용": u.findtext("별표내용") or ""})
    return out


def addenda(xb):
    """[(부칙공포일자, 부칙공포번호, 부칙내용)] — 부칙 아래 세 요소가 차례로 나온다(실측)."""
    root = ET.fromstring(xb)
    b = root.find("부칙")
    out = []
    if b is None:
        return out
    cur = {}
    for c in b:
        if c.tag == "부칙공포일자":
            cur = {"일자": (c.text or "").strip()}
        elif c.tag == "부칙공포번호":
            cur["번호"] = (c.text or "").strip()
        elif c.tag == "부칙내용":
            out.append((cur.get("일자", ""), cur.get("번호", ""), "".join(c.itertext())))
            cur = {}
    return out


# ── 이분 탐색 ─────────────────────────────────────────────────────────────
SEEN = {}                     # (이름, 일련번호) → 판 기록(판목록 csv 행)


def probe(client, name, row, label, test, why):
    xb, p, meta = get_ver(client, name, row["행정규칙일련번호"])
    inf = info(xb)
    art = find_article(xb, label)
    ok = bool(test(art))
    k = (name, row["행정규칙일련번호"], label)
    SEEN[k] = dict(규정=name, 행정규칙일련번호=row["행정규칙일련번호"], 발령일자=row.get("발령일자", ""),
                   시행일자=row.get("시행일자", ""), 발령번호=row.get("발령번호", ""),
                   제개정구분=row.get("제개정구분명", ""), 현행연혁구분=row.get("현행연혁구분", ""),
                   XML_발령일자=inf.get("발령일자", ""), XML_시행일자=inf.get("시행일자", ""),
                   조문형식여부=inf.get("조문형식여부", ""), 대상조=label, 조_있음="Y" if art else "N",
                   판정=why, 판정결과="Y" if ok else "N", 조_글자수=len(art),
                   조_sha256=hashlib.sha256(art.encode("utf-8")).hexdigest() if art else "",
                   XML경로=p, XML_sha256=meta.get("sha256", ""), 출처URL=meta.get("출처URL", ""),
                   수집시각=meta.get("fetched_at", ""))
    return ok, art, xb


def bisect_first(client, name, rows, label, test, why):
    """rows(발령일자 순)에서 test 가 처음 참이 되는 위치. 끝은 참, 처음은 거짓임을 먼저 확인한다(단조 가정)."""
    hi = len(rows) - 1
    if not probe(client, name, rows[hi], label, test, why)[0]:
        return None
    lo = 0
    if probe(client, name, rows[lo], label, test, why)[0]:
        return 0
    while hi - lo > 1:                              # rows[lo] 거짓, rows[hi] 참
        mid = (lo + hi) // 2
        if probe(client, name, rows[mid], label, test, why)[0]:
            hi = mid
        else:
            lo = mid
    return hi


def save_seen():
    rows = sorted(SEEN.values(), key=lambda r: (r["규정"], r["대상조"], r["발령일자"], r["행정규칙일련번호"], r["판정"]))
    cols = ["규정", "대상조", "행정규칙일련번호", "발령일자", "시행일자", "발령번호", "제개정구분", "현행연혁구분",
            "XML_발령일자", "XML_시행일자", "조문형식여부", "조_있음", "판정", "판정결과", "조_글자수", "조_sha256",
            "XML경로", "XML_sha256", "출처URL", "수집시각"]
    old = []
    if os.path.exists(PROBE_CSV):
        keys = {(r["규정"], r["행정규칙일련번호"], r["대상조"], r["판정"]) for r in rows}
        old = [r for r in csv.DictReader(open(PROBE_CSV, encoding="utf-8-sig"))
               if (r["규정"], r["행정규칙일련번호"], r["대상조"], r["판정"]) not in keys]
    allr = sorted(old + rows, key=lambda r: (r["규정"], r["대상조"], r["발령일자"], r["행정규칙일련번호"], r["판정"]))
    write_csv(PROBE_CSV, cols, allr)


def reg75():
    client = _client()
    rows = load_hist(REG)
    why = "제7-5조 글에 「자체 위험 및 지급여력 평가」(정규식 %s) 있음" % ORSA_RE.pattern
    k = bisect_first(client, REG, rows, "제7-5조", lambda a: ORSA_RE.search(a), why)
    print("제7-5조 문구 처음 든 판: %s" % (rows[k] if k is not None else None))
    if k is not None:
        for j in (k - 1, k, k + 1):                 # 앞뒤 판(경계 확인 겸)
            if 0 <= j < len(rows):
                ok, art, _ = probe(client, REG, rows[j], "제7-5조", lambda a: ORSA_RE.search(a), why)
                print("  %s %s %s → %s" % (rows[j]["행정규칙일련번호"], rows[j]["발령일자"], rows[j]["시행일자"], ok))
        # 덧붙임: 현행 제2항 개정 표지 「2022. 12. 21.」 확인 — 제2항 위험 목록에 「생명」이 처음 든 판(이분 탐색)
        why2 = "제7-5조 글에 「생명」(제2항 위험 목록: 생명ㆍ장기손해보험위험…) 있음"
        sub = rows[k:]
        k2 = bisect_first(client, REG, sub, "제7-5조", lambda a: "생명" in a, why2)
        if k2 is not None:
            for j in (k + k2 - 1, k + k2):
                probe(client, REG, rows[j], "제7-5조", lambda a: "생명" in a, why2)
            print("제7-5조 제2항 「생명」 처음 든 판: %s %s" % (rows[k + k2]["행정규칙일련번호"], rows[k + k2]["발령일자"]))
    save_seen()
    print("호출 %d회" % client.n_calls)


def sec562():
    client = _client()
    rows = load_hist(SEC)
    cur_xb = open(SEC_XML9, "rb").read()
    cur_art = find_article(cur_xb, "제5-6조의2")
    why1 = "제5-6조의2 조 표지 있음"
    k1 = bisect_first(client, SEC, rows, "제5-6조의2", lambda a: bool(a), why1)
    print("제5-6조의2 처음 나온 판: %s" % (rows[k1] if k1 is not None else None))
    for j in (k1 - 1, k1):
        probe(client, SEC, rows[j], "제5-6조의2", lambda a: bool(a), why1)
    why2 = "제5-6조의2 글이 현행(2200000108939) 글과 같음(공백 무시)"
    same = lambda a: bool(a) and _nosp(a) == _nosp(cur_art)            # noqa: E731
    sub = rows[k1:]
    k2 = bisect_first(client, SEC, sub, "제5-6조의2", same, why2)
    k2 = k1 + k2 if k2 is not None else None
    print("제5-6조의2 현행 글이 처음 나온 판: %s" % (rows[k2] if k2 is not None else None))
    for j in (k2 - 1, k2):
        probe(client, SEC, rows[j], "제5-6조의2", same, why2)
    save_seen()
    print("호출 %d회" % client.n_calls)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"hist": hist, "reg75": reg75, "sec562": sec562}.get(cmd)
    if not fn:
        raise SystemExit(__doc__)
    fn()
