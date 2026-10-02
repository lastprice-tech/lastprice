# -*- coding: utf-8 -*-
"""10차 산출물 검증 — 결과는 dart_out/risk10/verify10.txt. 실패가 하나라도 있으면 exit 1.

    python3 scripts/dart/verify10.py

A 법령 인용(금산법_확인·금산법_인용대조·계열회사_정의대조): source_text 가 그 판 원문 XML 글에 공백 무시로 그대로 있는가.
  연차보고서 행은 8차 쪽 텍스트(dart_out/text/risk8)의 그 쪽에 있는가.
B 별표37: 표시 CSV 의 source_text 가 세칙_별표37.md 「원문」에 있는가, pdf_page 쪽 PDF 텍스트에 있는가,
  md 「원문」이 hwp2md 출력과 글자가 같은가(<br>·\\| 변환만), 부칙 행은 세칙 XML 에 있는가.
C 법령 md: 본문이 원문 XML 에서 다시 뽑은 글과 같은가, 머리말에 출처(OC=***)·sha256 이 있는가.
D 웹 대조 CSV(제3자가이드라인·작성기준): 원문 열이 해당 md 에 그대로 있는가(「문서에 없음」·「확인 불가」 제외).
E 법령해석_대주주거래: related 행의 body_md 파일이 있고, 폴더의 md 가 모두 목록에 있는가.
  우선 질문(①②③) 인용 문장이 그 회신 원문 md 에 그대로 있는가.
F 모든 CSV 행에 출처(URL/접수번호)와 수집일이 있는가.
G 키 유출: DART_API_KEY·LAW_OC 값이 새 파일 어디에도 없고, 「OC=」 뒤는 늘 *** 인가.
H 9차까지의 산출물(handoff/ 의 10차 폴더 밖)이 9차 마지막 커밋(25909e2)과 같은가.
K 법령원문 저용량본: 법령마다 파일이 있고 조문마다 연혁 표지만 뺀 원문 글이 그대로 들어 있는가.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "law"))
import web10_law as L  # noqa: E402
import leakscan  # noqa: E402

OUT, LAWOUT, WORK = L.OUT, L.LAWOUT, L.WORK
BASE9 = "25909e2"
NA = ("문서에 없음", "확인 불가", "확인 불가(원문 미수집)", "")
log, fails = [], []


def ok(cond, what):
    log.append(("OK  " if cond else "실패 ") + what)
    if not cond:
        fails.append(what)


def nows(s):
    return re.sub(r"\s+", "", s or "")


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig"))) if os.path.exists(path) else []


# ── 원문 XML 글(일련번호 → 공백 없앤 전체 글) ─────────────────────────────
LIST = rows(L.LIST_CSV)
XTEXT = {}
for r in LIST:
    if r["상태"] == "OK":
        # 조문(조문내용·항내용·호내용·목내용)·부칙·별표제목 글을 문서 순서대로 — 전체 itertext 는 항번호·호번호
        # 요소가 끼어 「①①」처럼 겹치므로 쓰지 않는다. 법령 md 본문(C1 에서 따로 대조)과 같은 글이다.
        xb = open(r["원문XML"], "rb").read()
        XTEXT[r["일련번호"]] = nows(L.md_text(xb, "rule" if r["kind"].startswith("행정규칙") else "law"))


def xml_for(doc_name):
    """doc_name 의 「일련번호 N」들 → 그 판들의 글."""
    return [XTEXT.get(s, "") for s in re.findall(r"일련번호 (\d+)", doc_name)]


def page_text(path, page):
    s = open(path, encoding="utf-8").read()
    m = re.search(r"^=== p\.%d ===[^\n]*\n(.*?)(?=^=== p\.|\Z)" % page, s, re.S | re.M)
    return m.group(1) if m else ""


# ── A 법령 인용 ───────────────────────────────────────────────────────────
def check_A():
    bad = n = 0
    for r in rows(L.CHECK_CSV):
        if r["source_text"] in NA:
            continue
        n += 1
        if r["법령"] == "연차보고서":
            co = r["조문"]
            t = page_text(L.AR_TEXT % (co, ""), int(r["page"].replace("p.", "")))
            good = nows(r["source_text"]) in nows(t)
        else:
            good = any(nows(r["source_text"]) in x for x in xml_for(r["doc_name"]))
        if not good:
            bad += 1
            log.append("   불일치 금산법_확인 %s %s" % (r["구분"], r["조문"]))
    ok(bad == 0, "A1 금산법_확인 인용 %d건 원문 대조 (불일치 %d)" % (n, bad))
    bad = n = 0
    for r in rows(L.CITE_CSV):
        texts = xml_for(r["doc_name"])
        n += 1
        g1 = nows(r["감독규정_source_text"]) in texts[0]
        g2 = r["인용단위_source_text"] in NA or any(nows(r["인용단위_source_text"]) in x for x in texts[1:])
        if not (g1 and g2):
            bad += 1
            log.append("   불일치 인용대조 %s %s" % (r["감독규정_조항"], r["인용표기"]))
    req = [r for r in rows(L.CITE_CSV) if r["요청범위"] == "Y"]
    ok(bad == 0, "A2 금산법_인용대조 %d행 감독규정·인용 조문 원문 대조 (불일치 %d)" % (n, bad))
    ok(sorted(r["사용자_표기"] for r in req) == sorted(L.ASKED.values()),
       "A3 요청한 인용 4개(§9의2·시행령 §5의4②·§5의5①5호·§9의4)가 모두 있음")
    bad = n = 0
    for r in rows(L.DEF_CSV):
        if r["source_text"] in NA:
            continue
        n += 1
        if not any(nows(r["source_text"]) in x for x in xml_for(r["doc_name"])):
            bad += 1
            log.append("   불일치 계열회사_정의대조 %s %s" % (r["법령"], r["조문"]))
    ok(bad == 0, "A4 계열회사_정의대조 인용 %d건 원문 대조 (불일치 %d)" % (n, bad))


# ── B 별표37 ──────────────────────────────────────────────────────────────
def check_B():
    md = open(L.A37_MD, encoding="utf-8").read()
    body = md.split("\n## 원문\n", 1)[1]
    raw = open(os.path.join(L.RAW, "annex37", "세칙_별표37_hwp2md.md"), encoding="utf-8").read()
    conv = "\n".join(L.cell_lines(raw.rstrip("\n")))
    # 변환은 <br>·\|·칸 테두리 「|」·구분줄만 건드린다 → 그것들을 다 빼면 글자가 같아야 한다
    strip = lambda t: nows(t).replace("<br>", "").replace("\\", "").replace("|", "").replace("---", "")  # noqa: E731
    ok(nows(body) == nows(conv) and strip(body) == strip(raw),
       "B1 별표37 md 「원문」 = hwp2md 출력(<br>·\\|·표 구분줄 변환만, 글자 같음)")
    pdf = open(os.path.join(L.RAW, "annex37", "세칙_별표37_pdf.txt"), encoding="utf-8").read()
    sec = nows("".join(ET.fromstring(open(L.SEC_XML, "rb").read()).itertext()))
    bad = n = 0
    for r in rows(L.A37_CSV):
        if r["source_text"] in NA:
            continue
        n += 1
        if r["md_줄"]:
            good = nows(r["source_text"]) in nows(body)
            pg = [int(x) for x in r["pdf_page"].split(",") if x.isdigit()]
            first = nows(r["source_text"].split("\n")[0])[:20]
            good = good and pg and any(first in nows(page_text(os.path.join(L.RAW, "annex37", "세칙_별표37_pdf.txt"), p))
                                       for p in pg)
        else:
            good = nows(r["source_text"]) in sec
        if not good:
            bad += 1
            log.append("   불일치 별표37 %s %s" % (r["표시"], r["md_줄"] or r["위치"]))
    ok(bad == 0 and pdf, "B2 별표37 표시 %d건 md·PDF 쪽·세칙 XML 대조 (불일치 %d)" % (n, bad))
    marks = {r["표시"] for r in rows(L.A37_CSV) if r["source_text"] not in NA}
    ok(marks >= {m for m, _ in L.MARKS}, "B3 표시 4항목 모두 있음: %s" % sorted(marks))


# ── C 법령 md ─────────────────────────────────────────────────────────────
def check_C():
    bad = n = 0
    for r in LIST:
        if r["상태"] != "OK" or not r["텍스트"]:
            continue
        n += 1
        md = open(r["텍스트"], encoding="utf-8").read()
        kind = "rule" if r["kind"].startswith("행정규칙") else "law"
        body = md.split("\n---\n", 1)[1]
        same = nows(body) == nows(L.md_text(open(r["원문XML"], "rb").read(), kind))
        head = md.split("\n---\n", 1)[0]
        good = same and "OC=***" in head and r["xml_sha256"] in head and \
            hashlib.sha256(md.encode("utf-8")).hexdigest() == r["텍스트_sha256"]
        if not good:
            bad += 1
            log.append("   md 문제 %s (본문 같음 %s)" % (r["텍스트"], same))
    ok(bad == 0 and n >= 9, "C1 법령 md %d개: 본문 = 원문 XML 글, 머리말 출처·sha256, 목록 sha256 일치 (문제 %d)" % (n, bad))
    for want in ("금산법.md", "금산법시행령.md", "공정거래법.md", "공정거래법시행령.md"):
        ok(os.path.exists(os.path.join(LAWOUT, want)), "C2 요청 파일 있음: 법령원문_10차/%s" % want)


# ── D 웹 대조 CSV ─────────────────────────────────────────────────────────
def _in_md(text, md_path):
    return nows(text) in nows(open(md_path, encoding="utf-8").read())


def check_D():
    life9 = glob.glob(os.path.join("handoff", "생보협회_자율규제_원문", "원문_21297-1_*.md"))
    nonlife = os.path.join(OUT, "손보협회_제3자가이드라인.md")
    p = os.path.join(OUT, "제3자가이드라인_대조.csv")
    if os.path.exists(p) and life9 and os.path.exists(nonlife):
        bad = n = 0
        for r in rows(p):
            for col, md in (("생보_source_text", life9[0]), ("손보_source_text", nonlife)):
                v = r.get(col, "")
                if v in NA:
                    continue
                n += 1
                if not _in_md(v, md):
                    bad += 1
                    log.append("   불일치 제3자 %s %s" % (col, r.get("조문", "")))
        ok(bad == 0, "D1 제3자가이드라인_대조 원문 열 %d칸 md 대조 (불일치 %d)" % (n, bad))
    else:
        ok(False, "D1 제3자가이드라인 대조 파일·원문 md 있음")
    p = os.path.join(OUT, "작성기준_대조.csv")
    md = os.path.join(OUT, "작성기준_생보협회.md")
    bad = n = 0
    for r in rows(p):
        v = r.get("생보협회_source_text", "")
        if v in NA:
            continue
        n += 1
        if not _in_md(v, md):
            bad += 1
            log.append("   불일치 작성기준 %s" % r.get("항목", ""))
    ok(n > 0 and bad == 0, "D2 작성기준_대조 생보협회 원문 열 %d칸 md 대조 (불일치 %d)" % (n, bad))


# ── E 법령해석 ────────────────────────────────────────────────────────────
def check_E():
    p = os.path.join(OUT, "목록_법령해석_대주주거래.csv")
    d = os.path.join(OUT, "법령해석_대주주거래")
    rr = rows(p)
    listed = {os.path.basename(r.get("body_md", "")) for r in rr if r.get("body_md")}
    have = {os.path.basename(x) for x in glob.glob(os.path.join(d, "*.md"))}
    missing = [r.get("title", "")[:30] for r in rr if r.get("related") and r.get("body_md")
               and not os.path.exists(r["body_md"] if os.path.isabs(r["body_md"]) else r["body_md"])
               and os.path.basename(r["body_md"]) not in have]
    ok(bool(rr) and not missing and have <= listed,
       "E1 법령해석_대주주거래 목록 %d행 · 원문 md %d개 · 목록에 없는 md %d · 없는 파일 %d"
       % (len(rr), len(have), len(have - listed), len(missing)))


    bad = n = 0
    for r in rows(os.path.join(WORK, "법령해석_대주주거래_우선.csv")):
        if r["source_text"] in NA:
            continue
        n += 1
        md = os.path.join(d, "%s.md" % r["일련번호"])
        if not (os.path.exists(md) and _in_md(r["source_text"], md)):
            bad += 1
            log.append("   불일치 우선 %s" % r["일련번호"])
    ok(n > 0 and bad == 0, "E2 우선 질문 인용 %d건이 그 회신 원문 md 에 그대로 있음 (불일치 %d)" % (n, bad))


# ── F 출처·수집일 ─────────────────────────────────────────────────────────
SRC = ("rcept_no_or_url", "url", "출처URL", "생보_출처", "손보_출처", "생보협회_출처")
WHEN = ("collected_at", "checked_at", "수집일", "fetched_at")


def check_F():
    for p in sorted(glob.glob(os.path.join(OUT, "*.csv"))):
        rr = rows(p)
        cols = rr[0].keys() if rr else []
        sc = [c for c in SRC if c in cols]
        wc = [c for c in WHEN if c in cols]
        miss = sum(1 for r in rr if not any(r[c].strip() for c in sc) or not any(r[c].strip() for c in wc))
        ok(rr and sc and wc and miss == 0, "F %s %d행 — 출처 열 %s · 수집일 열 %s · 빠진 행 %d"
           % (os.path.basename(p), len(rr), sc or "없음", wc or "없음", miss))


# ── G 키 유출 ─────────────────────────────────────────────────────────────
def check_G():
    keys = leakscan.secrets()
    files = [f for d in (OUT, LAWOUT, WORK, os.path.join("handoff", "법령원문_저용량")) for f in glob.glob(os.path.join(d, "**", "*"), recursive=True)
             if os.path.isfile(f)] + glob.glob(os.path.join("scripts", "dart", "web10*.py")) + [os.path.join("scripts", "dart", "law_compact.py")] + [__file__]
    hits = []
    for f in files:
        b = open(f, "rb").read()
        for k, v in keys.items():
            if v.encode() in b:
                hits.append((f, k))
        if re.search(rb"OC=(?!\*\*\*)[A-Za-z0-9]", b):
            hits.append((f, "OC 가림 안 됨"))
    ok("LAW_OC" in keys and not hits, "G 키 유출 검사 %d개 파일(키 %s) — 걸린 곳 %d" % (len(files), ",".join(keys), len(hits)))
    for f, k in hits:
        log.append("   유출 %s ← %s" % (f, k))


# ── H 9차까지 산출물 ──────────────────────────────────────────────────────
def check_H():
    r = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--name-only", BASE9, "--", "handoff", "dart_out/risk9", "dart_out/risk8"],
                       capture_output=True, text=True, check=True)
    changed = [x for x in r.stdout.splitlines() if not re.match(r"handoff/(원문_10차|법령원문_10차|법령원문_저용량)/", x)]
    r2 = subprocess.run(["git", "-c", "core.quotepath=off", "status", "--porcelain", "--", "handoff", "dart_out/risk9", "dart_out/risk8"],
                        capture_output=True, text=True, check=True)
    dirty = [x for x in r2.stdout.splitlines() if not re.search(r"(원문_10차|법령원문_10차|법령원문_저용량)", x)]
    ok(not changed and not dirty, "H 9차까지 산출물 변경 없음(%s 대비 커밋 변경 %d · 작업트리 변경 %d)"
       % (BASE9, len(changed), len(dirty)))
    for x in changed + dirty:
        log.append("   변경 %s" % x)


# ── K 법령원문 저용량본(2026-10-02 추가) ──────────────────────────────────
def check_K():
    import law_compact
    n, probs = law_compact.check()
    ok(n >= 13 and not probs, "K 법령원문 저용량본 %d개: 조문마다 연혁 표지만 뺀 원문 글이 그대로, BOM·CRLF 없음 (문제 %d)"
       % (n, len(probs)))
    for x in probs[:20]:
        log.append("   " + x)


def main():
    for f in (check_A, check_B, check_C, check_D, check_E, check_F, check_G, check_H, check_K):
        try:
            f()
        except Exception as e:                       # noqa: BLE001
            ok(False, "%s 예외 %s: %s" % (f.__name__, type(e).__name__, e))
    out = "\n".join(log + ["", "실패 %d" % len(fails)]) + "\n"
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, "verify10.txt"), "w", encoding="utf-8").write(out)
    print(out)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
