# -*- coding: utf-8 -*-
"""15차 경영공시 g1(KB·신한·하나·우리·NH농협) FY2019~2025 조각 자체 검증 — 새 원문 대조 규칙.

    python3 -I scripts/dart/verify15_mgmt_g1.py      # exit 0 = 통과, 1 = 문제 있음. 결과 dart_out/ops15/verify15_mgmt_g1.txt

대조 규칙: 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 쪽 글」(경영공시 PDF 글 md 의 그 「## p.N」) 안에
이어서 그대로 있어야 함. PDF 출처라 「|」는 지우지 않음. 출처 쪽 글은 dart_out/text/ops15/경영공시__<회사>__FY<fy>.md(없으면
커밋되는 원문 md dart_out/ops15/원문/<B|D>/<회사>__FY<fy>__경영공시.md 의 같은 쪽)를 씀.
그 밖에: 열·BOM, 필수 칸, 출처 칸이 목록 CSV 와 같은지, page 꼴, 「문서에 없음」 행의 찾은 범위, 받은 FY 마다 B·D 행,
받지 못한 FY 행 없음, 제어문자, 키워드·칸 글이 source_text 안에 있는지, 원문 md 쪽 글이 글 md 와 같은지, 비밀값.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
OPS = os.path.join("dart_out", "ops15")
LIST = os.path.join(OPS, "경영공시15_목록_g1.csv")
FB = os.path.join(OPS, "조각", "B_mgmt_g1.csv")
FD = os.path.join(OPS, "조각", "D_mgmt_g1.csv")
OUT = os.path.join(OPS, "verify15_mgmt_g1.txt")
TEXT = os.path.join("dart_out", "text", "ops15")
RAW = os.path.join("dart_out", "raw", "mgmt15")
COS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]
FYS = [str(y) for y in range(2019, 2026)]
NONE = "문서에 없음"
B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
D_COLS = ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"]
L_COLS = ["corp_label", "fy", "period_원문", "url", "posted_at", "fetched_at", "bytes", "pages", "sha256",
          "robots_verdict", "terms_note", "status", "note"]
B_KWS = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
KST = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$")
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

lines_out, fails = [], []


def say(s):
    lines_out.append(s)


def fail(s):
    fails.append(s)
    lines_out.append("  ✗ " + s)


def nz(s):
    return re.sub(r"\s", "", s or "")


def read(path, cols):
    raw = open(path, "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf"):
        fail("%s: utf-8-sig BOM 없음" % path)
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    hdr = next(csv.reader(open(path, encoding="utf-8-sig", newline="")))
    if hdr != cols:
        fail("%s: 열 이름·순서가 다름 %s" % (path, hdr))
    return rows


def pages_of(path):
    s = open(path, encoding="utf-8").read()
    parts = re.split(r"^## p\.(\d+)( \(글자 없음\))?\n\n", s, flags=re.M)
    out = {}
    for k in range(1, len(parts), 3):
        out[int(parts[k])] = "" if parts[k + 1] else parts[k + 2]
    return out


_cache = {}


def page_text(task, co, fy, n):
    """글 md 의 쪽 글(있으면), 없으면 원문 md 의 같은 쪽. (글, 출처 이름)"""
    tp = os.path.join(TEXT, "경영공시__%s__FY%s.md" % (co, fy))
    op = os.path.join(OPS, "원문", task, "%s__FY%s__경영공시.md" % (co, fy))
    for p in (tp, op):
        if os.path.exists(p):
            if p not in _cache:
                _cache[p] = pages_of(p)
            if n in _cache[p]:
                return _cache[p][n], p
    return None, ""


def main():
    say("verify15_mgmt_g1 — %s" % __import__("datetime").datetime.now(
        __import__("datetime").timezone(__import__("datetime").timedelta(hours=9))).isoformat(timespec="seconds"))
    # ── 목록 CSV
    L = read(LIST, L_COLS)
    keys = [(r["corp_label"], r["fy"]) for r in L]
    want = [(c, f) for c in COS for f in FYS]
    if sorted(keys) != sorted(want):
        fail("목록 CSV 회사×FY 칸이 35칸과 다름(%d행)" % len(L))
    got = {}
    for r in L:
        got[(r["corp_label"], r["fy"])] = r
        if r["status"] not in ("받음", "누리집에 없음", "막힘", "실패", "받음(글 뽑기 실패)"):
            fail("목록 %s FY%s status 이상: %s" % (r["corp_label"], r["fy"], r["status"]))
        for c in ("robots_verdict", "terms_note", "note"):
            if not r[c].strip():
                fail("목록 %s FY%s %s 빈칸" % (r["corp_label"], r["fy"], c))
        if r["status"].startswith("받음"):
            for c in ("period_원문", "url", "fetched_at", "bytes", "sha256", "pages"):
                if not r[c].strip():
                    fail("목록 %s FY%s 받음인데 %s 빈칸" % (r["corp_label"], r["fy"], c))
            if not KST.match(r["fetched_at"]):
                fail("목록 %s FY%s fetched_at 이 KST ISO 꼴 아님: %s" % (r["corp_label"], r["fy"], r["fetched_at"]))
            rp = os.path.join(RAW, r["corp_label"], "%s_경영공시_FY%s.pdf" % (r["corp_label"], r["fy"]))
            if os.path.exists(rp):
                b = open(rp, "rb").read()
                if hashlib.sha256(b).hexdigest() != r["sha256"] or str(len(b)) != r["bytes"]:
                    fail("목록 %s FY%s sha256·bytes 가 받은 파일과 다름" % (r["corp_label"], r["fy"]))
    st = {}
    for r in L:
        st[r["status"]] = st.get(r["status"], 0) + 1
    say("목록 %d행 — %s" % (len(L), ", ".join("%s %d" % kv for kv in sorted(st.items()))))
    ok_fy = {k for k, r in got.items() if r["status"] == "받음"}

    # ── 조각
    nrows = {}
    for task, path, cols in (("B", FB, B_COLS), ("D", FD, D_COLS)):
        R = read(path, cols)
        nm, nn, nsrc = 0, 0, 0
        per = {}
        for i, r in enumerate(R, 2):
            tag = "%s %d행(%s FY%s %s)" % (task, i, r["corp_label"], r["fy"], r["page"])
            k = (r["corp_label"], r["fy"])
            per[k] = per.get(k, 0) + 1
            for c in ("corp_label", "fy", "source_text", "doc_kind", "rcept_no_or_url", "page", "note", "doc_name",
                      "collected_at") + (("keyword",) if task == "B" else ()):
                if not r[c].strip():
                    fail("%s: %s 빈칸" % (tag, c))
            if r["doc_kind"] != "경영공시":
                fail("%s: doc_kind 이상" % tag)
            if k not in ok_fy:
                fail("%s: 목록에서 받음이 아닌 FY 의 행" % tag)
                continue
            lr = got[k]
            if r["rcept_no_or_url"] != lr["url"] or r["doc_name"] != lr["period_원문"] or r["collected_at"] != lr["fetched_at"]:
                fail("%s: 출처 칸(url·doc_name·collected_at)이 목록과 다름" % tag)
            if not KST.match(r["collected_at"]):
                fail("%s: collected_at KST 꼴 아님" % tag)
            if CTRL.search(r["source_text"]):
                fail("%s: source_text 에 제어문자" % tag)
            if task == "B":
                if r["employees_total"] or r["regular"] or r["contract"]:
                    fail("%s: 직원 수 칸이 비어 있지 않음" % tag)
                if "직원 수는 같은 FY 사업보고서 행" not in r["note"]:
                    fail("%s: note 에 「직원 수는 같은 FY 사업보고서 행」 없음" % tag)
            if r["source_text"] == NONE:
                nn += 1
                if not re.fullmatch(r"p\.1~p\.(\d+)\(경영공시 전체 — 찾은 범위\)", r["page"]):
                    fail("%s: 문서에 없음 행 page 꼴" % tag)
                elif r["page"].split("~p.")[1].split("(")[0] != lr["pages"]:
                    fail("%s: 문서에 없음 행 page 끝 쪽(%s)이 목록 쪽수(%s)와 다름" % (tag, r["page"], lr["pages"]))
                if "찾은 범위" not in r["note"]:
                    fail("%s: 문서에 없음 행 note 에 찾은 범위 없음" % tag)
                if task == "B" and r["keyword"] != "없음":
                    fail("%s: 문서에 없음 행 keyword 가 「없음」 아님" % tag)
                continue
            nm += 1
            m = re.fullmatch(r"p\.(\d+)", r["page"])
            if not m:
                fail("%s: page 꼴(p.N) 아님" % tag)
                continue
            src, where = page_text(task, r["corp_label"], r["fy"], int(m.group(1)))
            if src is None:
                fail("%s: 출처 쪽 글을 찾지 못함" % tag)
                continue
            nsrc += 1
            if nz(r["source_text"]) not in nz(CTRL.sub("", src)) and nz(r["source_text"]) not in nz(src):
                fail("%s: source_text 가 출처 쪽 글에 이어서 없음(%s)" % (tag, where))
            if CTRL.sub("", src) != src and "제어문자 지움" not in r["note"] and nz(r["source_text"]) not in nz(src):
                fail("%s: 제어문자를 지웠는데 note 에 밝히지 않음" % tag)
            if len(r["source_text"]) > 2000:
                fail("%s: source_text 2,000자 넘음" % tag)
            if task == "B":
                if r["keyword"] not in B_KWS or r["keyword"] not in nz(r["source_text"]):
                    fail("%s: keyword 「%s」가 source_text 에 없음" % (tag, r["keyword"]))
            else:
                for c in ("counterparty", "contract_type", "amount"):
                    if r[c] and nz(r[c]) not in nz(r["source_text"]):
                        fail("%s: %s 「%s」가 source_text 안에 없음" % (tag, c, r[c]))
            # 원문 md 에 그 쪽이 있고 글 md 와 같은지
            op = os.path.join(OPS, "원문", task, "%s__FY%s__경영공시.md" % (r["corp_label"], r["fy"]))
            if not os.path.exists(op):
                fail("%s: 원문 md 없음 %s" % (tag, op))
            else:
                if op not in _cache:
                    _cache[op] = pages_of(op)
                ot = _cache[op].get(int(m.group(1)))
                if ot is None:
                    fail("%s: 원문 md 에 %s 쪽 없음" % (tag, r["page"]))
                elif nz(ot) != nz(src):
                    fail("%s: 원문 md 의 쪽 글이 글 md 와 다름" % tag)
        for k in sorted(ok_fy):
            if not per.get(k):
                fail("%s: 받은 %s FY%s 의 행이 없음" % (task, k[0], k[1]))
        say("%s %d행 — 원문 대조 %d행(쪽 글 찾음 %d), 「문서에 없음」 %d행" % (task, len(R), nm, nsrc, nn))
        nrows[task] = len(R)

    # ── 비밀값
    key = os.environ.get("DART_API_KEY", "")
    files = [LIST, FB, FD, OUT, "scripts/dart/ops15_mgmt_g1.py", "scripts/dart/verify15_mgmt_g1.py"] + \
        glob.glob(os.path.join(OPS, "원문", "[BD]", "*__FY20*__경영공시.md"))
    nsec = 0
    for p in files:
        if not os.path.exists(p) or p == OUT:
            continue
        s = open(p, encoding="utf-8", errors="replace").read()
        if (key and key in s) or re.search(r"crtfc_key=[0-9a-fA-F]{20,}", s):
            nsec += 1
            fail("비밀값 꼴이 %s 에 있음" % p)
    say("비밀값 검사 %d개 파일 — 걸린 것 %d" % (len(files) - 1, nsec))
    say("결과: %s (문제 %d)" % ("통과" if not fails else "실패", len(fails)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")
    print("\n".join(lines_out[-12:]))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
