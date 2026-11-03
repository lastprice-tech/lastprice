# -*- coding: utf-8 -*-
"""15차 경영공시 g1(KB·신한·하나·우리·NH농협) FY2019~2025 조각 검증 — 새 원문 대조 규칙 + 독립 검증(검증 에이전트 15차 g1).

    python3 -I scripts/dart/verify15_mgmt_g1.py                 # 글 md 로 대조(PDF 다시 뽑기는 건너뜀)
    <venv>/python -I scripts/dart/verify15_mgmt_g1.py           # pymupdf 가 있으면 받은 PDF 를 다시 뽑아 그 글로 대조(독립 검증)
    ... [--dump <dir>]                                          # 빠짐 후보 전체를 <dir>/verify15_mgmt_g1_후보_<B|D>.csv 로
    exit 0 = 통과, 1 = 문제 있음. 결과 dart_out/ops15/verify15_mgmt_g1.txt

(a) 원문 대조: 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 쪽 글」 안에 이어서 그대로 있어야 함.
    PDF 출처라 「|」는 지우지 않음. 보이지 않는 제어문자(줄바꿈·탭 말고)를 지운 행은 note 에 「제어문자 지움」.
    출처 쪽 글 = pymupdf 로 받은 PDF 를 다시 뽑은 글(있으면) → 없으면 글 md(dart_out/text/ops15/경영공시__…md) → 없으면 원문 md.
    다시 뽑은 글과 글 md 의 쪽 글도 (공백 무시) 같아야 함. 같은 글을 다른 쪽에도 있다고 note 에 적은 쪽도 대조.
(b) 열·utf-8-sig·필수 칸·출처 칸(url·doc_name·collected_at)이 목록과 같은지, sha256(목록 = PDF = 글 md 머리 = 원문 md 머리).
(c) 빠짐: B 는 쪽마다 6개 검색어 자리가 모두 어떤 행의 source_text 안에 있어야 함(다른 낱말 속 「전적」만 뺌).
    D 는 「위탁」「용역」「자문」「전산」「공동」이 지주 이름 앞뒤 3줄 안에 있는 자리가 행에 없으면, 아래 REVIEWED(원문을 보고
    뺀 꼴과 사유)에 맞아야 함. 맞지 않는 새 자리가 있으면 실패.
    D 표 행은 그 쪽 표 머리 칸 순서(거래내용·당사자·당사자·금액·계정과목 …)와 행 칸 순서가 맞아야 함.
(d) 「문서에 없음」 행: page 꼴·찾은 범위·글자 없는/깨진 쪽·더 넓은 검색어 기록이 note 에 있어야 함.
(e) 목록: 회사×FY 35칸, status 와 파일 있음/없음이 맞는지, robots·이용약관 기록.
(f) 비밀값 꼴 없음, PDF 가 git 추적 경로에 없음(git ls-files·check-ignore).
"""
from __future__ import annotations

import csv
import datetime
import glob
import hashlib
import os
import re
import subprocess
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
WORK = os.path.join(OPS, "mgmt15_g1_work")
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
D_GREP = ["위탁", "용역", "자문", "전산", "공동"]
HOLDCO = {"KB금융지주": r"KB금융지주|KB금융그룹|케이비금융지주", "신한금융지주": r"신한금융지주", "하나금융지주": r"하나금융지주",
          "우리금융지주": r"우리금융지주"}
KST = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$")
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
HANGUL = re.compile(r"[가-힣]")
AMT_RE = re.compile(r"^\s*(\(?[△▲\-]?\s*\d[\d,]*(\.\d+)?\)?|-)\s*$")

# (판단) D 빠짐 후보 가운데 원문을 보고 뺀 꼴 — (공백 지운 앞뒤 글에 대한 정규식, 사유). 검증 에이전트가 후보 전체를 읽고 정함.
REVIEWED = [
    (r"공동기업|공동지배|관계기업", "회계 낱말(관계기업 및 공동기업 등) — 지주·계열사 사이 거래 글 아님"),
    (r"공동모금|공동기금|공동상담|공동주택", "사회공헌 기부처·기금·상담실 이름 — 지주·계열사 사이 거래 글 아님"),
    (r"용역제공조건|용역의제공|용역을제공|근무용역|재화나용역|용역제공기간|용역제공", "회계정책(주식기준보상·종업원급여·수익인식) 낱말"),
    (r"사무공간을공동사용|공동사용영업점|공동이용회사명|공동이용자회사|시설물의공동이용|시설물등공동|공동사용개시일|공동사용공간|"
     r"공동사용현황|공동이용현황|공동이용형태|공동광고회사명|공동광고계약|공동광고명|공동광고현황|공동광고·|공동광고☞",
     "자회사끼리의 영업점·사무공간 공동사용(복합점포)·공동광고 표나 그 목차 — 지주가 당사자가 아님(지주가 당사자인 공동광고 행은 따로 넣음)"),
    (r"업무위탁수수료|위탁수수료", "자회사등끼리의 거래 표 행 — 지주가 당사자 칸에 없음"),
    (r"공동으로JSC|설립공동출자|공동출자|그룹공동|그룹 공동|공동클라우드|공동통합결제|전산실|전산시스템구축|카드전산|공동망|위탁운용",
     "연혁 줄(회사·자회사 연혁) — 지주·계열사 사이 계약 글 아님"),
    (r"자문위원|자문회의|정책자문|자문단|투자자문대표|자문인력|투자자문㈜|투자자문\(주\)|이룸투자자문", "사외이사·임원 경력이나 제재 사유의 직함"),
    (r"리츠운용|신용정보주식회사|신용정보전산|민원용역|투자자문서비스|투자자문업|금융자문㈜|맥쿼리금융자문|영업양도|대체투자운용|"
     r"펀드파트너스|일반사무관리|위탁관리REITs|위탁관리리츠|신한신용정보매각|신용정보매각|위탁매매|REITs\)가위탁",
     "자회사 소개·연혁·제재 내역 글 — 지주·계열사 사이 계약 글 아님"),
    (r"업무위탁리스크|제3자업무위탁", "리스크관리 체계 설명 글"),
    (r"토지신탁|책임준공", "자회사 사업(토지신탁) 우발 상황 글"),
    (r"공동영업수수료", "거래 표의 「공동영업수수료 — 해당사항 없음」 칸(거래 없음)"),
    (r"전산업에서", "인사말 글(「전 산업」)"),
    (r"운용역량|운용역", "다른 낱말 속 「용역」(운용역량)"),
    (r"금융지주회사등은다른법령에도불구하고공동광고", "금융지주회사법 조문 — 같은 조문 행이 다른 쪽에 있음"),
]

lines_out, fails, warns = [], [], []


def say(s):
    lines_out.append(s)


def fail(s):
    fails.append(s)
    lines_out.append("  ✗ " + s)


def warn(s):
    warns.append(s)
    lines_out.append("  △ " + s)


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


def ranges(ns):
    out = []
    for n in sorted(ns):
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ",".join(("%d~%d" % (a, b)) if a != b else str(a) for a, b in out)


try:
    import pymupdf  # noqa: E402 — venv 파이썬에서만 있음
except Exception:  # noqa: BLE001
    pymupdf = None

_md, _fresh = {}, {}


def md_pages(co, fy):
    tp = os.path.join(TEXT, "경영공시__%s__FY%s.md" % (co, fy))
    if tp not in _md:
        _md[tp] = pages_of(tp) if os.path.exists(tp) else None
    return _md[tp]


def fresh_pages(co, fy):
    """받은 PDF 를 pymupdf 로 다시 뽑은 쪽 글(없으면 None). 글 md 를 쓸 때 \\r 이 \\n 으로 바뀌므로 그 꼴로 맞춤."""
    k = (co, fy)
    if k not in _fresh:
        p = os.path.join(RAW, co, "%s_경영공시_FY%s.pdf" % (co, fy))
        if pymupdf is None or not os.path.exists(p):
            _fresh[k] = None
        else:
            doc = pymupdf.open(p)
            _fresh[k] = {i: pg.get_text().replace("\r\n", "\n").replace("\r", "\n") for i, pg in enumerate(doc, 1)}
    return _fresh[k]


def src_pages(task, co, fy):
    """(쪽 글 dict, 출처 이름) — 다시 뽑은 PDF 글 > 글 md > 원문 md."""
    f = fresh_pages(co, fy)
    if f is not None:
        return f, "PDF 다시 뽑은 글"
    m = md_pages(co, fy)
    if m is not None:
        return m, "글 md"
    op = os.path.join(OPS, "원문", task, "%s__FY%s__경영공시.md" % (co, fy))
    return (pages_of(op), "원문 md") if os.path.exists(op) else ({}, "")


def garbled(pages):
    out = []
    for n, body in pages.items():
        s = nz(body)
        if s and len(HANGUL.findall(s)) / len(s) < 0.2 and len(CTRL.findall(body)) >= 5:
            out.append(n)
    return sorted(out)


def check_list():
    L = read(LIST, L_COLS)
    keys = [(r["corp_label"], r["fy"]) for r in L]
    want = [(c, f) for c in COS for f in FYS]
    if sorted(keys) != sorted(want) or len(keys) != 35:
        fail("목록 CSV 회사×FY 칸이 35칸과 다름(%d행)" % len(L))
    got, st, npdf, nmiss = {}, {}, 0, 0
    for r in L:
        k = (r["corp_label"], r["fy"])
        got[k] = r
        st[r["status"]] = st.get(r["status"], 0) + 1
        if r["status"] not in ("받음", "누리집에 없음", "막힘", "실패", "받음(글 뽑기 실패)"):
            fail("목록 %s FY%s status 이상: %s" % (k[0], k[1], r["status"]))
        for c in ("robots_verdict", "terms_note", "note"):
            if not r[c].strip():
                fail("목록 %s FY%s %s 빈칸" % (k[0], k[1], c))
        if "robots.txt" not in r["robots_verdict"]:
            fail("목록 %s FY%s robots_verdict 에 robots.txt 확인 기록 없음" % k)
        rp = os.path.join(RAW, k[0], "%s_경영공시_FY%s.pdf" % k)
        tp = os.path.join(TEXT, "경영공시__%s__FY%s.md" % k)
        if r["status"].startswith("받음"):
            for c in ("period_원문", "url", "fetched_at", "bytes", "sha256", "pages"):
                if not r[c].strip():
                    fail("목록 %s FY%s 받음인데 %s 빈칸" % (k[0], k[1], c))
            if not KST.match(r["fetched_at"]):
                fail("목록 %s FY%s fetched_at 이 KST ISO 꼴 아님: %s" % (k[0], k[1], r["fetched_at"]))
            if os.path.exists(rp):
                npdf += 1
                b = open(rp, "rb").read()
                if hashlib.sha256(b).hexdigest() != r["sha256"] or str(len(b)) != r["bytes"]:
                    fail("목록 %s FY%s sha256·bytes 가 받은 PDF 와 다름" % k)
                if pymupdf is not None and str(pymupdf.open(rp).page_count) != r["pages"]:
                    fail("목록 %s FY%s pages 가 PDF 쪽 수와 다름" % k)
            else:
                nmiss += 1
                warn("목록 %s FY%s 받음인데 PDF 가 이 컨테이너에 없음(git 밖) — sha256 대조 건너뜀" % k)
            if os.path.exists(tp):
                head = open(tp, encoding="utf-8").read(2000)
                m = re.search(r"^- sha256: ([0-9a-f]{64})$", head, flags=re.M)
                m2 = re.search(r"^- 받은 시각: (\S+)$", head, flags=re.M)
                if not m or m.group(1) != r["sha256"]:
                    fail("글 md %s 머리 sha256 이 목록과 다름" % tp)
                if not m2 or m2.group(1) != r["fetched_at"]:
                    fail("글 md %s 머리 받은 시각이 목록 fetched_at 과 다름" % tp)
                if len(md_pages(*k) or {}) != int(r["pages"] or 0):
                    fail("글 md %s 쪽 수가 목록 pages 와 다름" % tp)
            else:
                warn("목록 %s FY%s 받음인데 글 md 가 이 컨테이너에 없음(git 밖)" % k)
        else:
            if os.path.exists(rp) or os.path.exists(tp):
                fail("목록 %s FY%s status=%s 인데 PDF·글 md 가 있음" % (k[0], k[1], r["status"]))
            for c in ("sha256", "bytes", "pages", "fetched_at"):
                if r[c].strip():
                    fail("목록 %s FY%s status=%s 인데 %s 칸이 차 있음" % (k[0], k[1], r["status"], c))
    say("목록 %d행 — %s · 받은 PDF sha256 대조 %d건(PDF 없어 건너뜀 %d)" %
        (len(L), ", ".join("%s %d" % kv for kv in sorted(st.items())), npdf, nmiss))
    return got


# ── D 표 행 머리 칸 순서 대조
HDR_UP = re.compile(r"거래내용|거래구분|매도자|매수자|채권자|채무자|계정과목|^\s*\(|^\s*\)\s*$")
PARTY = re.compile(r"KB|신한|하나|우리|케이비|푸르덴셜|DS|에프아이에스|데이타|연구소|은행|증권|카드|생명|보험|캐피탈|운용|저축|"
                   r"금융지주|금융투자|신탁|벤처|핀크")
NOT_PARTY = re.compile(r"수익|비용|매출|수수료|용역|이자|배당|매매|채권·채무|채권채무|거래|기타")


def header_kinds(lines, i0):
    for k in range(i0 - 1, max(-1, i0 - 400), -1):
        if re.fullmatch(r"\s*(거래금액|금액|금엑)\s*", lines[k]):
            a = k
            while a - 1 >= 0 and k - (a - 1) <= 8 and HDR_UP.search(lines[a - 1]):
                a -= 1
            b = k
            while b + 1 < len(lines) and b + 1 - k <= 3 and re.fullmatch(r"\s*(계정과목|비고|거래항목?|목|\))\s*", lines[b + 1]):
                b += 1
            kinds = []
            for x in (y.strip() for y in lines[a:b + 1]):
                if re.search(r"거래내용|거래구분", x):
                    kinds.append("T")
                elif re.search(r"매도자|채권자|매수자|채무자", x):
                    if x.startswith("("):
                        continue
                    kinds.append("P")
                elif re.fullmatch(r"거래금액|금액|금엑", x):
                    kinds.append("A")
                elif re.fullmatch(r"계정과목|비고|거래항목?", x):
                    kinds.append("T")
            return kinds
    return None


def collapse(ks):
    out = []
    for k in ks:
        if not (out and out[-1] == k == "T"):
            out.append(k)
    return out


def row_kinds(src):
    ks = []
    for c in (x.strip() for x in src.split("\n")):
        if not c:
            continue
        if AMT_RE.match(c):
            ks.append("A")
        elif PARTY.search(c) and not NOT_PARTY.search(c):
            ks.append("P")
        else:
            ks.append("T")
    return collapse(ks)


def find_line(lines, src):
    first = nz(src.split("\n")[0])
    want = nz(src)
    for i, l in enumerate(lines):
        if nz(l) == first and nz("".join(lines[i:i + len(src.split("\n")) + 6])).startswith(want):
            return i
    return None


def main(argv):
    dump = argv[argv.index("--dump") + 1] if "--dump" in argv else ""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    say("verify15_mgmt_g1 — %s (출처 쪽 글: %s)" % (now, "pymupdf %s 로 받은 PDF 를 다시 뽑은 글" % pymupdf.__version__
                                                if pymupdf else "글 md(pymupdf 없어 PDF 다시 뽑기 건너뜀)"))
    got = check_list()
    ok_fy = {k for k, r in got.items() if r["status"] == "받음"}

    # ── 다시 뽑은 PDF 글 = 글 md 인지
    if pymupdf is not None:
        ndoc, ndiff = 0, 0
        for k in sorted(ok_fy):
            f, m = fresh_pages(*k), md_pages(*k)
            if f is None or m is None:
                continue
            ndoc += 1
            bad = [n for n in f if nz(f[n]) != nz(m.get(n, ""))] + [n for n in m if n not in f]
            if bad:
                ndiff += 1
                fail("%s FY%s: 글 md 쪽 글이 PDF 다시 뽑은 글과 다름(쪽 %s)" % (k[0], k[1], ranges(bad)[:80]))
        say("PDF 다시 뽑기 %d건 — 글 md 와 공백 빼고 같음 %d건" % (ndoc, ndoc - ndiff))

    # ── 조각
    cover = {}          # (task, co, fy, page) -> [nz(source_text)]
    for task, path, cols in (("B", FB, B_COLS), ("D", FD, D_COLS)):
        R = read(path, cols)
        nm, nn, nsrc, ntab = 0, 0, 0, 0
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
            if " | " in r["source_text"] or "…" in r["source_text"]:
                fail("%s: source_text 에 원문에 없는 「 | 」·「…」 꼴" % tag)
            pages, where = src_pages(task, *k)
            gb = garbled(pages)
            if gb and "글자층" not in r["note"]:
                fail("%s: 이 문서의 글자층 깨진 쪽(p.%s)을 note 에 밝히지 않음" % (tag, ranges(gb)[:40]))
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
                if "찾은 범위" not in r["note"] or "더 넓은 검색어" not in r["note"]:
                    fail("%s: 문서에 없음 행 note 에 찾은 범위·더 넓은 검색어 기록 없음" % tag)
                if task == "B" and r["keyword"] != "없음":
                    fail("%s: 문서에 없음 행 keyword 가 「없음」 아님" % tag)
                if task == "D" and (r["counterparty"] or r["contract_type"] or r["amount"]):
                    fail("%s: 문서에 없음 행인데 counterparty·contract_type·amount 가 차 있음" % tag)
                continue
            nm += 1
            m = re.fullmatch(r"p\.(\d+)", r["page"])
            if not m:
                fail("%s: page 꼴(p.N) 아님" % tag)
                continue
            pn = int(m.group(1))
            pgs = [pn] + [int(x[2:]) for x in (re.search(r"같은 글이 ([p.\d,]+) 에도", r["note"]) or [None, ""])[1].split(",") if x]
            for q in pgs:
                src = pages.get(q)
                if src is None:
                    fail("%s: 출처 쪽 p.%d 글을 찾지 못함(%s)" % (tag, q, where))
                    continue
                if q == pn:
                    nsrc += 1
                if nz(r["source_text"]) in nz(src):
                    pass
                elif nz(r["source_text"]) in nz(CTRL.sub("", src)):
                    if "제어문자 지움" not in r["note"]:
                        fail("%s: 제어문자를 지웠는데 note 에 「제어문자 지움」 없음" % tag)
                else:
                    fail("%s: source_text 가 출처 p.%d 글(%s)에 이어서 그대로 없음" % (tag, q, where))
                cover.setdefault((task, k[0], k[1], q), []).append(nz(r["source_text"]))
            if len(r["source_text"]) > 2000:
                fail("%s: source_text 2,000자 넘음" % tag)
            if task == "B":
                if r["keyword"] not in B_KWS or r["keyword"] not in nz(r["source_text"]):
                    fail("%s: keyword 「%s」가 source_text 에 없음" % (tag, r["keyword"]))
            else:
                for c in ("counterparty", "contract_type", "amount"):
                    if r[c] and nz(r[c]) not in nz(r["source_text"]):
                        fail("%s: %s 「%s」가 source_text 안에 없음" % (tag, c, r[c]))
                hm = re.search(r"표 행 ([①②③④])", r["note"])
                if hm:
                    ntab += 1
                    lines = (pages.get(pn) or "").split("\n")
                    li = find_line(lines, r["source_text"])
                    hk = header_kinds(lines, li) if li is not None else None
                    rk = row_kinds(r["source_text"])
                    if hk is None:
                        fail("%s: 표 행인데 그 쪽에서 표 머리 칸을 찾지 못함" % tag)
                    elif rk not in (collapse(hk), collapse(hk[1:])):
                        fail("%s: 표 행 칸 순서 %s 가 표 머리 칸 순서 %s 와 맞지 않음(앞뒤 행을 섞어 묶었을 수 있음)"
                             % (tag, "".join(rk), "".join(hk)))
                    else:
                        ak = [c.strip() for c in r["source_text"].split("\n") if c.strip() and AMT_RE.match(c)]
                        if r["amount"] and ak and r["amount"].strip() != ak[0]:
                            fail("%s: amount 가 행의 금액 칸과 다름" % tag)
            op = os.path.join(OPS, "원문", task, "%s__FY%s__경영공시.md" % k)
            if not os.path.exists(op):
                fail("%s: 원문 md 없음 %s" % (tag, op))
            else:
                if op not in _md:
                    _md[op] = pages_of(op)
                    head = open(op, encoding="utf-8").read(600)
                    if lr["sha256"] not in head or lr["url"] not in head or lr["fetched_at"] not in head:
                        fail("원문 md %s 머리 출처 줄(url·받은 시각·sha256)이 목록과 다름" % op)
                ot = _md[op].get(pn)
                if ot is None:
                    fail("%s: 원문 md 에 %s 쪽 없음" % (tag, r["page"]))
                elif nz(ot) != nz(pages.get(pn, "")):
                    fail("%s: 원문 md 의 쪽 글이 출처 쪽 글(%s)과 다름" % (tag, where))
        for k in sorted(ok_fy):
            if not per.get(k):
                fail("%s: 받은 %s FY%s 의 행이 없음" % (task, k[0], k[1]))
        say("%s %d행 — 원문 대조 %d행(쪽 글 찾음 %d%s), 「문서에 없음」 %d행" %
            (task, len(R), nm, nsrc, (", 표 행 칸 순서 대조 %d" % ntab) if task == "D" else "", nn))

    # ── 빠짐(c)
    dump_rows = {"B": [], "D": []}
    nb_occ, nb_other, nd_cand, nd_rev = 0, 0, 0, {}
    for k in sorted(ok_fy):
        pages, _ = src_pages("B", *k)
        hold = re.compile(HOLDCO[k[0]])
        for n, body in sorted(pages.items()):
            F = nz(CTRL.sub("", body))
            # B
            spans = [(mm.start(), mm.end()) for st in cover.get(("B", k[0], k[1], n), []) for mm in re.finditer(re.escape(st), F)]
            taken = set()
            for kw in B_KWS:
                for mm in re.finditer(kw, F):
                    if set(range(mm.start(), mm.end())) & taken:
                        continue
                    taken |= set(range(mm.start(), mm.end()))
                    if kw == "전적" and ((mm.start() > 0 and HANGUL.match(F[mm.start() - 1])) or
                                        re.match(r"으로|인|합", F[mm.end():mm.end() + 2])):
                        nb_other += 1
                        continue
                    nb_occ += 1
                    if not any(a <= mm.start() and mm.end() <= b for a, b in spans):
                        ctx = F[max(0, mm.start() - 30):mm.end() + 30]
                        fail("B 빠짐: %s FY%s p.%d 「%s」 자리가 어느 행에도 없음 — …%s…" % (k[0], k[1], n, kw, ctx))
                        dump_rows["B"].append(dict(co=k[0], fy=k[1], page=n, term=kw, ctx=ctx))
            # D
            lines = CTRL.sub("", body).split("\n")
            flat = [nz(x) for x in lines]
            pos, acc = [], 0
            for x in flat:
                pos.append(acc)
                acc += len(x)
            dsp = [(mm.start(), mm.end()) for st in cover.get(("D", k[0], k[1], n), []) for mm in re.finditer(re.escape(st), F)]
            # 공동광고·공동이용 표(머리 줄 뒤 120줄 안, 다른 「…현황」 절이 끼기 전)의 회사명 칸에 지주 이름이 있으면 행이 있어야 함
            heads = [h for h, x in enumerate(flat) if re.search(r"공동광고|공동이용|공동사용", x)
                     and not any("해당사항없" in y for y in flat[h:h + 3])]
            for li, x in enumerate(flat):
                if not heads or not re.fullmatch(r"㈜?(%s)(회사)?" % HOLDCO[k[0]], x):
                    continue
                inside = any(h < li <= h + 120 and not any("현황" in y and not re.search(r"공동광고|공동이용|공동사용", y)
                                                             for y in flat[h + 1:li]) for h in heads)
                if inside and not any(s <= pos[li] and pos[li] + len(x) <= e for s, e in dsp):
                    fail("D 빠짐: %s FY%s p.%d 공동광고·공동이용 표의 지주 이름 칸이 어느 행에도 없음 — …%s…"
                         % (k[0], k[1], n, F[max(0, pos[li] - 40):pos[li] + len(x) + 40]))
            for li, x in enumerate(flat):
                for w in D_GREP:
                    for mm in re.finditer(w, x):
                        if not any(hold.search(y) for y in flat[max(0, li - 3):li + 4]):
                            continue
                        a = pos[li] + mm.start()
                        if any(s <= a and a + len(w) <= e for s, e in dsp):
                            continue
                        nd_cand += 1
                        ctx = F[max(0, a - 40):a + len(w) + 40]
                        why = next((y for rx, y in REVIEWED if re.search(rx, F[max(0, a - 25):a + len(w) + 25])), "")
                        dump_rows["D"].append(dict(co=k[0], fy=k[1], page=n, term=w, ctx=ctx, why=why))
                        if why:
                            nd_rev[why] = nd_rev.get(why, 0) + 1
                        else:
                            fail("D 빠짐 후보(검토 안 된 꼴): %s FY%s p.%d 「%s」 — …%s…" % (k[0], k[1], n, w, ctx))
    say("B 빠짐 검사 — 6개 검색어 자리 %d곳 모두 행 안에 있음 여부 확인(다른 낱말 속 「전적」 %d곳은 뺌)" % (nb_occ, nb_other))
    say("D 빠짐 검사 — 「위탁·용역·자문·전산·공동」이 지주 이름 앞뒤 3줄 안에 있는데 행에 없는 자리 %d곳: 검토한 꼴 %d곳(%s)" %
        (nd_cand, sum(nd_rev.values()), " · ".join("%s %d" % (y.split(" — ")[0], c) for y, c in nd_rev.items())))
    if dump:
        for t, rows in dump_rows.items():
            with open(os.path.join(dump, "verify15_mgmt_g1_후보_%s.csv" % t), "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["co", "fy", "page", "term", "ctx", "why"], extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)

    # ── git 추적·비밀값(f)
    try:
        tracked = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout.decode("utf-8").split("\0")
        pdfs = [p for p in tracked if p.lower().endswith(".pdf")]
        if pdfs:
            fail("git 이 추적하는 PDF %d개(예: %s)" % (len(pdfs), pdfs[0]))
        ign = subprocess.run(["git", "check-ignore", "-q", RAW]).returncode == 0
        if not ign:
            fail("%s 가 git 무시 폴더가 아님" % RAW)
        say("git — 추적하는 PDF %d개, 받은 PDF 폴더 %s 무시됨 %s" % (len(pdfs), RAW, "예" if ign else "아니오"))
    except Exception as e:  # noqa: BLE001
        warn("git 확인 못 함: %s" % type(e).__name__)
    key = os.environ.get("DART_API_KEY", "")
    files = [LIST, FB, FD, "scripts/dart/ops15_mgmt_g1.py", "scripts/dart/verify15_mgmt_g1.py"] + \
        glob.glob(os.path.join(OPS, "원문", "[BD]", "*__FY20*__경영공시.md")) + glob.glob(os.path.join(WORK, "*"))
    nsec = 0
    for p in files:
        if not os.path.isfile(p):
            continue
        s = open(p, encoding="utf-8", errors="replace").read()
        if (key and key in s) or re.search(r"crtfc_key=[0-9a-fA-F]{20,}|DART_API_KEY\s*[=:]\s*['\"]?[0-9a-fA-F]{20,}"
                                           r"|(?i:api[_-]?key|secret|token|password)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}", s):
            nsec += 1
            fail("비밀값 꼴이 %s 에 있음" % p)
    say("비밀값 검사 %d개 파일(조각·목록·원문 md·work·스크립트) — 걸린 것 %d" % (len(files), nsec))
    say("결과: %s (문제 %d, 알림 %d)" % ("통과" if not fails else "실패", len(fails), len(warns)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")
    print("\n".join(lines_out[:4] + ["…"] + lines_out[-14:]) if len(lines_out) > 20 else "\n".join(lines_out))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
