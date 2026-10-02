# -*- coding: utf-8 -*-
"""11차 산출물 검증 — 결과는 dart_out/risk11/verify11.txt. 실패가 하나라도 있으면 exit 1.

    python3 scripts/dart/verify11.py

A 법령 md(법령원문_11차): 본문 = 원문 XML 에서 다시 뽑은 글, 머리말 출처(OC=***)·sha256, 작업 기록 CSV 의 sha256 일치.
B 특수관계인_정의대조: 원문·대조_상대원문이 그 판 원문 XML 글에 공백 무시로 그대로 있는가(「문서에 없음」 제외).
C 별표 4·5: md 의 코드 블록 글이 원문 XML 별표내용과 글자까지 같은가.
D 저용량본: 9·10·11차 법령마다 .txt 가 있고 조문마다 연혁 표지만 뺀 원문 글이 그대로(law_compact.check), 00_목록에 모두 있음.
E 보험자회사_지주거래공시(7-2): 모든 행에 출처(url)·수집일, 「지주 본체」 행의 source_text 가 받아 둔 원문 글에 그대로.
F 키 유출: DART_API_KEY·LAW_OC 값이 새 파일 어디에도 없고 「OC=」 뒤는 늘 ***.
G 9·10차 산출물 불변: 3cb5fa6(10-02 저용량본 커밋) 대비 handoff 의 11차 밖 파일이 같은가(저용량본 폴더는 기존 14개 파일 불변,
  00_목록.txt 와 저용량본 기록 CSV 2개만 갱신).
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
import web10_law as L10  # noqa: E402
import web11_law as W  # noqa: E402
import web11_more as M  # noqa: E402
import law_compact as C  # noqa: E402
import leakscan  # noqa: E402

BASE = "3cb5fa6"
OUT, LAWOUT, WORK = W.OUT, W.LAWOUT, W.WORK
NA = ("문서에 없음", "")
log, fails = [], []


def ok(cond, what):
    log.append(("OK  " if cond else "실패 ") + what)
    if not cond:
        fails.append(what)


def nows(s):
    return re.sub(r"\s+", "", s or "")


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if os.path.exists(p) else []


LIST = [r for r in rows(W.LIST_CSV) if r["종류"] != "별표"]


def check_A():
    bad = 0
    for r in LIST:
        if r["상태"] != "OK":
            bad += 1
            log.append("   상태 %s %s" % (r["상태"], r["name"]))
            continue
        md = open(r["텍스트"], encoding="utf-8").read()
        head, body = md.split("\n---\n", 1)
        kind = "rule" if r["kind"] == "행정규칙" else "law"
        same = nows(body) == nows(L10.md_text(open(r["원문XML"], "rb").read(), kind))
        good = (same and "OC=***" in head and r["xml_sha256"] in head
                and hashlib.sha256(open(r["원문XML"], "rb").read()).hexdigest() == r["xml_sha256"] == r["sha256"]
                and hashlib.sha256(md.encode("utf-8")).hexdigest() == r["텍스트_sha256"])
        if not good:
            bad += 1
            log.append("   md 문제 %s (본문 같음 %s)" % (r["텍스트"], same))
    want = {x[0] for x in W.LAWS}
    ok(bad == 0 and {r["name"] for r in LIST} == want,
       "A 법령 md %d개(요청 7 + 은행법): 본문 = 원문 XML 글, 머리말 출처·sha256, 기록 sha256 일치 (문제 %d)" % (len(LIST), bad))
    for r in LIST:
        log.append("   %s %s 일련번호 %s 시행 %s%s" % (r["종류"], r["name"], r["일련번호"], r["시행일자"],
                                                 (" — " + r["note"]) if r["note"] else ""))


def _xml_texts():
    T = {}
    for r in LIST:
        T[r["xml_sha256"]] = nows(L10.md_text(open(r["원문XML"], "rb").read(), "rule" if r["kind"] == "행정규칙" else "law"))
    for p in (M.GOV_D_XML, M.GOV_XML, M.FTC_XML, M.FTC_D_XML):
        b = open(p, "rb").read()
        T[hashlib.sha256(b).hexdigest()] = nows(L10.md_text(b, "law"))
    return T


def check_B():
    T = _xml_texts()
    rr = rows(M.DEF_CSV)
    bad = n = 0
    for r in rr:
        if r["원문"] not in NA:
            n += 1
            if nows(r["원문"]) not in T.get(r["source_sha256"], ""):
                bad += 1
                log.append("   불일치 원문 %s %s" % (r["법령"], r["조문"]))
        if r["대조_상대원문"] not in NA:
            n += 1
            gov = T[hashlib.sha256(open(M.GOV_D_XML, "rb").read()).hexdigest()]
            # 상대 원문은 떨어진 호·목을 줄바꿈으로 이어 붙였다 → 줄마다 대조
            if any(nows(x) not in gov for x in r["대조_상대원문"].split("\n") if x.strip()):
                bad += 1
                log.append("   불일치 대조 %s" % r["대조_상대조문"])
    need = {"제1조의4제1항", "제1조의4제2항"} | {"제1조의4제1항제%d호" % i for i in range(1, 10)}
    have = {r["조문"] for r in rr if r["구분"] == "은행법 시행령 제1조의4"}
    ok(bad == 0 and need <= have and all(r["rcept_no_or_url"] and r["collected_at"] for r in rr if r["원문"] not in NA),
       "B 특수관계인_정의대조 %d행 · 원문 대조 %d칸 (불일치 %d) · 제1조의4 ①②·①1~9호 모두 있음" % (len(rr), n, bad))


def check_C():
    md = open(M.ANNEX_MD, encoding="utf-8").read()
    dec = {r["name"]: r for r in rows(W.LIST_CSV)}[W.FHC_D]
    xb = open(dec["원문XML"], "rb").read()
    blocks = re.findall(r"```\n(.*?)\n```", md, re.S)
    good = len(blocks) == 2
    for no, blk in zip(("0004", "0005"), blocks):
        good = good and blk == C.annex_body(xb, no)[1].rstrip("\n")
    ok(good, "C 별표 4·5 md 코드 블록 = 원문 XML 별표내용(글자까지 같음)")


def check_D():
    n, probs = C.check()
    idx = open(os.path.join(C.OUTDIR, "00_목록.txt"), encoding="utf-8").read()
    listed = [f for f in sorted(os.listdir(C.OUTDIR)) if f.endswith(".txt") and f != "00_목록.txt"]
    missing = [f for f in listed if f not in idx]
    ok(not probs and not missing and n == len(C.entries()) + 1,
       "D 저용량본 %d개 대조(법령 %d + 별표 4·5) 문제 %d · 00_목록에 없는 파일 %d · 전체 txt %d개"
       % (n, len(C.entries()), len(probs), len(missing), len(listed)))
    for x in probs[:20] + missing:
        log.append("   " + x)


def check_E():
    p = os.path.join(OUT, "보험자회사_지주거래공시.csv")
    rr = rows(p)
    if not rr:
        ok(False, "E 보험자회사_지주거래공시.csv 없음")
        return
    miss = [r for r in rr if not r.get("url", "").strip() or not r.get("collected_at", "").strip()]
    hold = [r for r in rr if r.get("상대방 구분") == "지주 본체" and r.get("source_text") not in NA]
    # 「지주 본체」 원문 행: 받아 둔 원본 글(텍스트화 파일)에 공백 무시로 그대로
    texts = ""
    for f in glob.glob(os.path.join("dart_out", "raw", "web11", "**", "*"), recursive=True):
        if f.endswith((".txt", ".html", ".htm", ".json", ".md")) and os.path.isfile(f):
            try:
                texts += nows(open(f, encoding="utf-8", errors="ignore").read())
            except OSError:
                pass
    bad = [r for r in hold if nows(r["source_text"]) not in texts]
    corps = {r["corp_label"] for r in rr}
    need = {"메리츠화재", "NH농협손해보험", "NH농협생명", "신한라이프", "하나생명"}
    ok(not miss and not bad and need <= corps,
       "E 보험자회사_지주거래공시 %d행 · 출처·수집일 빠진 행 %d · 지주 본체 원문 행 %d (원본 대조 불일치 %d) · 필수 5사 모두 있음 %s"
       % (len(rr), len(miss), len(hold), len(bad), need <= corps))
    for r in bad[:10]:
        log.append("   불일치 %s %s %s" % (r["corp_label"], r.get("공시일", ""), r["source_text"][:40]))


def check_F():
    keys = leakscan.secrets()
    files = [f for d in (OUT, LAWOUT, WORK, C.OUTDIR) for f in glob.glob(os.path.join(d, "**", "*"), recursive=True)
             if os.path.isfile(f)] + glob.glob(os.path.join("scripts", "dart", "web11*.py")) + [
        os.path.join("scripts", "dart", "law_compact.py"), __file__]
    hits = []
    for f in files:
        b = open(f, "rb").read()
        for k, v in keys.items():
            if v.encode() in b:
                hits.append((f, k))
        if re.search(rb"OC=(?!\*\*\*)[A-Za-z0-9]", b):
            hits.append((f, "OC 가림 안 됨"))
    ok("LAW_OC" in keys and not hits, "F 키 유출 검사 %d개 파일 — 걸린 곳 %d" % (len(files), len(hits)))
    for f, k in hits:
        log.append("   유출 %s ← %s" % (f, k))


def _at_base(path):
    return subprocess.run(["git", "cat-file", "-e", "%s:%s" % (BASE, path)], capture_output=True).returncode == 0


def _allowed(x):
    """11차 폴더, 저용량본 목록, 저용량본의 새 파일(BASE 에 없던 것)만 바뀌어도 된다."""
    if re.match(r"handoff/(원문_11차|법령원문_11차)/", x) or x in (
            "handoff/법령원문_저용량/00_목록.txt",
            # 저용량본 기록(10-02 에 dart_out/risk10 에 둠) — 저용량본이 늘면 같이 갱신되는 파일
            "dart_out/risk10/법령원문_저용량_목록.csv", "dart_out/risk10/법령원문_저용량_지운표지.csv"):
        return True
    return x.startswith("handoff/법령원문_저용량/") and not _at_base(x)


def check_G():
    cmd = ["git", "-c", "core.quotepath=off", "diff", "--name-only"]
    paths = ["--", "handoff", "dart_out/risk9", "dart_out/risk10"]
    changed = [x for x in subprocess.run(cmd + [BASE] + paths, capture_output=True, text=True, check=True).stdout.splitlines()
               if not _allowed(x)]
    dirty = [x for x in subprocess.run(cmd + paths, capture_output=True, text=True, check=True).stdout.splitlines()
             if not _allowed(x)]
    ok(not changed and not dirty, "G 9·10차 산출물 불변(%s 대비, 저용량본은 00_목록·새 파일만) — 커밋 변경 %d · 작업트리 변경 %d"
       % (BASE, len(changed), len(dirty)))
    for x in changed + dirty:
        log.append("   변경 %s" % x)


def main():
    for f in (check_A, check_B, check_C, check_D, check_E, check_F, check_G):
        try:
            f()
        except Exception as e:                       # noqa: BLE001
            ok(False, "%s 예외 %s: %s" % (f.__name__, type(e).__name__, e))
    out = "\n".join(log + ["", "실패 %d" % len(fails)]) + "\n"
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, "verify11.txt"), "w", encoding="utf-8").write(out)
    print(out)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
