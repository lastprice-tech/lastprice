# -*- coding: utf-8 -*-
"""13차 9-4 기준(폐지된 「금융지주회사 통합위험관리 모범규준」 원문) 산출물 검증·보정.

    python3 scripts/dart/verify13_mobeom.py          # 대조만 — 결과 dart_out/risk13/verify13_mobeom.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_mobeom.py refute   # 「추출 범위에 없음」 반박 시도(같은 출처, 더 넓은 검색어). 받은 원본은
                                                     #   dart_out/raw/web13/verify13_mobeom/ (+ .meta.json), 결과 refute13.json
    python3 scripts/dart/verify13_mobeom.py fix      # 보정(멱등) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-4_모범규준_원문.md, dart_out/risk13/모범규준_조목록.csv.
결과 기록: dart_out/risk13/verify13_mobeom.txt. 원 생성기 scripts/dart/web13_mobeom.py 는 고치지 않는다(읽지도 import 하지도 않음).
원본(읽기만): dart_out/raw/web13/mobeom/ — 모범규준 hwp 4개·보도자료 hwp 2개의 hwp2md 변환본(*.hwp.md), 금감원 행정지도 화면 HTML,
      .meta.json(sha256·URL·fetched_at), 요청기록 dart_out/risk13/9-4_모범규준_요청기록.csv. 로컬 공시 텍스트 dart_out/text/risk8·risk9.

대조(인자 없이):
  1. 원문 인용(코드 블록·> 블록) 전부를 출처와 공백만 무시하고 대조 — 보도자료 hwp2md(<br>→줄바꿈), 행정지도 화면(태그 뺀 글),
     모범규준 판별 조문(조 머리부터 다음 조 머리 앞까지 — 조 전체인지도 봄), 전문(파일 전체), 로컬 텍스트(줄 번호·쪽 표지 「=== p.N ===」·
     인쇄 쪽). 「[생략: …]」 자리는 원본에서 담당 직원 이름·연락처 줄만 빠졌는지(빠진 글자 수·자리)만 보고 내용은 찍지 않는다.
     hwp 변환본은 hwp2md 를 다시 돌린 결과와 바이트 대조하고, hwp 안 미리보기 글(PrvText) 조각이 변환본에 있는지도 본다.
  2. 출처 표기 — 인용마다 문서명·URL(또는 접수번호)·쪽/조문·수집일이 있는지, URL·sha256·fetched_at 이 .meta.json 과 같은지.
  3. 조 목록 — CSV 1~59조의 번호·장·절·제목(2016.8.1판·2012.3.13판·2016.7예고안)·개정/삭제 표시가 세 판 변환본의 조 머리와 같은지,
     md 3장 표가 CSV 와 같은지, 2012 제정판 제목과 다른 조 목록.
  4. 조 번호(조 제목) — 자료 묶음(2장·7장 인용 머리, 9·10장 표)마다 「N조(제목)」이 붙었는지, md 의 「N조(제목)」이 CSV 제목과 같은지.
  5. 지시서(REQUEST13) 9-4 항목마다 10장 표에 받은 글 위치 또는 「추출 범위에 없음 + 찾은 방법」이 있는지, 가리킨 줄이 맞는지.
  6. 「추출 범위에 없음」마다 찾은 방법이 적혔는지, 반박 시도(refute13.json) 결과가 md 와 검증 기록에 있는지.
  7. 인증값(키·OC) 문자열 없음, 산출 폴더에 PDF 없음, 맨 끝 「## 검증 기록(2026-10-07)」 절.
  참고(문제로 세지 않음): note 줄 안 「…」 조각이 원본 글에 있는지(없으면 사람이 볼 목록으로).
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)

TODAY = "2026-10-07"
D = os.path.join("dart_out", "raw", "web13", "mobeom")
VD = os.path.join("dart_out", "raw", "web13", "verify13_mobeom")
OUT = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
MD = os.path.join(OUT, "9-4_모범규준_원문.md")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
OUT_TXT = os.path.join(WORK, "verify13_mobeom.txt")
REQLOG = os.path.join(WORK, "9-4_모범규준_요청기록.csv")
LOCAL_CSV = os.path.join(WORK, "9-4_모범규준_로컬인용.csv")
ADMIN_CSV = os.path.join(WORK, "9-4_모범규준_행정지도검색.csv")
PRESS_CSV = os.path.join(WORK, "9-4_모범규준_보도자료검색.csv")
LAW_CSV = os.path.join(WORK, "9-4_모범규준_법제처검색.csv")
KOFIA_CSV = os.path.join(WORK, "9-4_모범규준_kofia검색.csv")
REFUTE_JSON = os.path.join(VD, "refute13.json")
REQ13 = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
VERIFY_HEAD = "## 검증 기록(2026-10-07)"
SEC10_HEAD = "## 10. 지시서 항목별 대조(검증 2026-10-07 추가)"
T8 = os.path.join("dart_out", "text", "risk8")
T9 = os.path.join("dart_out", "text", "risk9")

FSS = "https://www.fss.or.kr"
ADMV = FSS + "/fss/job/admnstgudc/view.do?guGuidanceMgrSeq=%s&menuNo=200492"
PRVV = FSS + "/fss/job/admnPrvntc/view.do?seqno=%s&menuNo=200491"
BODO_VIEW = FSS + "/fss/bbs/B0000188/view.do?nttId=%s&menuNo=200218"

# ── 원본 등록부 ───────────────────────────────────────────────────────────────
F2016 = os.path.join(D, "fss", "모범규준_20160801판_붙임2_통합위험관리_개정후전문.hwp")
F2017 = os.path.join(D, "fss", "모범규준_20170401판_붙임2_통합위험관리_전문.hwp")
F2012 = os.path.join(D, "fss", "예고29_통합리스크관리_모범규준(게시)F_.hwp")
F2016P = os.path.join(D, "fss", "예고51_지배구조법시행_개정안(홈피공시).hwp")
PR2011 = os.path.join(D, "press", "fss_8584_통합리스크관리모범규준(보도자료)_지주회사팀F.hwp")
PR2012 = os.path.join(D, "press", "fss_9084_120320_조간_통합리스크모범규준마련.hwp")
VER = {  # 판 이름(md 4장 머리) → (파일, 문서 표기, 게시 URL)
    "2012.3.13 제정판": (F2012, "금감원 행정지도 예고 seqno=29 첨부 「통합리스크관리_모범규준(게시)F_.hwp」", PRVV % "29"),
    "2016.7 개정 예고안": (F2016P, "금감원 행정지도 예고 seqno=51 첨부 「지배구조법 시행에 따른「금융지주회사 통합리스크관리 모범규준」및"
                                "「금융지주회사의 그룹내부통제기준 모범규준」 개정안(홈피공시).hwp」", PRVV % "51"),
    "2016.8.1 판": (F2016, "금감원 행정지도 내역 관리번호 2014-017(감총그룹-388, 시행일 20160801) 첨부 「붙임2_금융지주회사 통합위험관리 "
                         "모범규준 개정 후 전문.hwp」", ADMV % "20170210165649943"),
}
VIEWS = {  # md 2장 인용 머리의 원본 상대경로 → 게시 URL
    "fss/admnPrvntc_view_29.html": PRVV % "29", "fss/admnPrvntc_view_51.html": PRVV % "51",
    "fss/admnPrvntc_view_67.html": PRVV % "67", "fss/admin_view_20170210165649943.html": ADMV % "20170210165649943",
    "fss/admin_view_20170328150222228.html": ADMV % "20170328150222228",
}
PRESS = {os.path.basename(PR2011): (PR2011, "8584", os.path.join(D, "press", "fss_view_8584.html")),
         os.path.basename(PR2012): (PR2012, "9084", os.path.join(D, "press", "fss_view_9084.html"))}
ANNUAL_LIST = os.path.join("handoff", "연차보고서_파일목록.csv")
DART_LISTS = [os.path.join("dart_out", "risk8", "DART_문서목록.csv"), os.path.join("dart_out", "risk9", "DART_목록.csv"),
              os.path.join("handoff", "공시_정기보고서.csv")]


# ── 공용 ─────────────────────────────────────────────────────────────────────
def ns(x):
    return re.sub(r"\s+", "", x)


_C = {}


def read(p):
    if p not in _C:
        with open(p, encoding="utf-8") as f:
            _C[p] = f.read()
    return _C[p]


def read_now(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def rbytes(p):
    with open(p, "rb") as f:
        return f.read()


def meta(p):
    with open(p + ".meta.json", encoding="utf-8") as f:
        return json.load(f)


def sha_file(p):
    return hashlib.sha256(rbytes(p)).hexdigest()


def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def strip_tags(h):
    """금감원 화면 HTML → 줄(태그 뺌). 원 생성기와 같은 규칙: script·style 제거, <br>·블록 끝 → 줄바꿈, 엔티티 풂, 빈 줄 뺌."""
    h = re.sub(r"<script\b.*?</script>", "", h, flags=re.S | re.I)
    h = re.sub(r"<style\b.*?</style>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|tr|h\d|dt|dd|table)>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return "\n".join(x.strip() for x in h.split("\n") if x.strip())


def view_text(rel):
    return strip_tags(rbytes(os.path.join(D, rel)).decode("utf-8", "replace"))


def press_text(p):
    return read(p + ".md").replace("<br>", "\n")


def kst(fa):
    return "수집 %s(UTC; .meta.json fetched_at %s)" % (TODAY, fa)


class Report:
    def __init__(self):
        self.lines, self.n_ng, self.n_ok, self.ngs = [], 0, 0, []

    def h(self, s):
        self.lines += ["", "## " + s]

    def ok(self, s):
        self.n_ok += 1
        self.lines.append("  OK  " + s)

    def ng(self, s):
        self.n_ng += 1
        self.ngs.append(s)
        self.lines.append("  NG  " + s)

    def info(self, s):
        self.lines.append("  ..  " + s)


# ── 모범규준 본문 파서(원 생성기와 따로 짬) ─────────────────────────────────────
def parse_rule(text):
    """→ (조 dict{n: dict(장, 절, 제목, 머리줄, 줄들)}, 부칙 줄들). 장 「제 N 장」, 절 「제N절」, 조 「제N조(제목)」."""
    arts, sup, chap, sec, cur = {}, [], "", "", None
    for ln in text.split("\n"):
        s = ln.strip()
        m = re.match(r"^제\s*(\d+)\s*장\s*(.*)$", s)
        if m and not re.match(r"^제\s*\d+\s*장의", s):
            chap, sec, cur = "제%s장 %s" % (m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()), "", None
            continue
        m = re.match(r"^제\s*(\d+)\s*절\s*(.*)$", s)
        if m:
            sec, cur = "제%s절 %s" % (m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()), None
            continue
        if re.match(r"^부\s*칙", s):
            cur = "부칙"
            sup.append(ln)
            continue
        m = re.match(r"^제(\d+)조\s*\(([^)]*)\)", s)
        if m and cur != "부칙":
            n = int(m.group(1))
            arts[n] = dict(장=chap, 절=sec, 제목=m.group(2).strip(), 머리줄=ln, 줄=[ln])
            cur = n
            continue
        if cur == "부칙":
            sup.append(ln)
        elif cur is not None:
            arts[cur]["줄"].append(ln)
    for a in arts.values():
        a["표시"] = sorted(set(re.findall(r"<(?:개정|삭제|신설)\s*[\d.\s]+>", "\n".join(a["줄"]))))
        # 표시가 붙은 항(①~⑳) — 조 머리줄의 표시는 ① 로 봄
        pos = []
        for ln in a["줄"]:
            mk = re.findall(r"<(?:개정|삭제|신설)\s*[\d.\s]+>", ln)
            if not mk:
                continue
            m2 = re.search(r"([①-⑳])", ln)
            pos.append(m2.group(1) if m2 else "조")
        a["표시항"] = pos
    return arts, sup


def rule_text(p):
    t = read(p + ".md")
    if p == F2016P:                                                  # 예고안 hwp 는 그룹내부통제 모범규준과 합본 — 통합위험관리 모범규준 부분부터
        lines = t.split("\n")
        k = lines.index("금융지주회사 통합위험관리 모범규준")
        t = "\n".join(lines[k:])
    return t


_RULES = {}


def rule(p):
    if p not in _RULES:
        _RULES[p] = parse_rule(rule_text(p))
    return _RULES[p]


def titles():
    return {int(r["조"]): r["제목_2016.8.1판"] for r in read_csv(JO_CSV)}


def titles12():
    return {int(r["조"]): r["제목_2012.3.13제정판"] for r in read_csv(JO_CSV)}


def jo(n, T=None, mark=""):
    T = T or titles()
    return "%d조(%s)%s" % (n, T[n], mark)


# ── md 해부 ──────────────────────────────────────────────────────────────────
def md_blocks(lines):
    """코드 블록(```)·인용 블록(>) → dict(시작줄, 끝줄(1-기준, 울타리 포함), 줄들, 머리(앞의 빈 줄 아닌 줄), 머리줄번호, 절)."""
    out, i, sec, sub = [], 0, "", ""
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("## "):
            sec = ln
        if ln.startswith("### "):
            sub = ln
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            out.append(dict(kind="code", s=i + 1, e=j + 1, lines=lines[i + 1:j], head=lines[k] if k >= 0 else "", hn=k + 1,
                            sec=sec, sub=sub))
            i = j + 1
            continue
        if ln.startswith(">"):
            j = i
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            out.append(dict(kind="quote", s=i + 1, e=j, lines=[re.sub(r"^> ?", "", x) for x in lines[i:j]],
                            head=lines[k] if k >= 0 else "", hn=k + 1, sec=sec, sub=sub))
            i = j
            continue
        i += 1
    return out


def outside_code(lines):
    """코드 블록 밖 줄 (줄번호, 글)."""
    inc = False
    for i, ln in enumerate(lines, 1):
        if ln.startswith("```"):
            inc = not inc
            continue
        if not inc:
            yield i, ln


# ── 1. 인용 대조 ─────────────────────────────────────────────────────────────
GAP_MAX = {"책임자": 400, "담당 직원 이름·전화": 120, "담당 직원 이름": 60, "접수부서": 260}


def seg_match(block_lines, src, R, where, gap_kind):
    """「[생략: …]」 줄로 나뉜 조각을 원본 글(공백 뺌)에서 차례로 찾는다. 빠진 자리 = 생략 자리만인지. → (ok, 정보)"""
    S = ns(src)
    segs, cur, kinds = [], [], []
    for ln in block_lines:
        if "[생략:" in ln:
            pre = ln[:ln.index("[생략:")]
            cur.append(pre)
            segs.append(ns("\n".join(cur)))
            kinds.append(ln[ln.index("[생략:"):])
            cur = []
        else:
            cur.append(ln)
    segs.append(ns("\n".join(cur)))
    pos, starts, gaps = 0, [], []
    for k, sg in enumerate(segs):
        if not sg:
            starts.append(pos)
            continue
        j = S.find(sg, pos)
        if j < 0:
            # 어디까지 맞는지
            lo = 0
            while lo < len(sg) and S.find(sg[:lo + 1], pos) >= 0:
                lo += 1
            return False, "조각 %d/%d 원본에 없음 — 앞에서 %d자까지만 맞음: 「%s」 다음" % (k + 1, len(segs), lo, sg[max(0, lo - 30):lo])
        if k > 0:
            gaps.append((kinds[k - 1], j - pos))
        elif j != 0 and gap_kind == "press":
            return False, "첫 조각이 원본 처음이 아님(앞 %d자 빠짐)" % j
        starts.append(j)
        pos = j + len(sg)
    tail = len(S) - pos
    info = []
    for kind, n in gaps:
        lim = next((v for k2, v in GAP_MAX.items() if k2 in kind), 200)
        info.append("%s %d자" % (kind.split(":")[1].strip(" ]")[:20], n))
        if n > lim:
            return False, "생략 자리(%s)에서 빠진 글이 %d자 — 이름·연락처 줄보다 김(한도 %d)" % (kind, n, lim)
        if n == 0:
            return False, "생략 표시(%s)가 있으나 원본에서 빠진 글 없음" % kind
    return True, dict(gaps=info, tail=tail, start=starts[0] if starts else 0)


def check_quotes(R, lines):
    R.h("1. 원문 인용 대조(코드 블록·> 블록) — 공백만 무시")
    blocks = md_blocks(lines)
    R.info("인용 블록 %d개(코드 %d, > %d)" % (len(blocks), sum(b["kind"] == "code" for b in blocks),
                                        sum(b["kind"] == "quote" for b in blocks)))
    n_ok = 0
    T = titles()
    per_label = []
    for b in blocks:
        head, where = b["head"], "md %d-%d줄" % (b["s"], b["e"])
        txt = "\n".join(b["lines"])
        res = None
        # (가) 보도자료 hwp
        m = re.search(r"보도자료 · (\S+) · 첨부 `([^`]+)`", head)
        if m:
            p, ntt, vp = PRESS[m.group(2)]
            ok, inf = seg_match(b["lines"], press_text(p), R, where, "press")
            if ok and inf["tail"]:
                ok, inf = False, "원본 끝 %d자 빠짐(「전문」 표기와 다름)" % inf["tail"]
            res = ("보도자료 %s" % ntt, ok, inf)
            per_label.append((b, "press", p))
        # (나) 행정지도 화면
        m = m or None
        if res is None:
            m = re.search(r"원본 `(fss/[^`]+\.html)`", head)
            if m:
                src = view_text(m.group(1))
                ok, inf = seg_match(b["lines"], src, R, where, "view")
                if ok:
                    # 끝: 마지막 조각 뒤(생략 자리 포함) 바로 「목록」 — 화면 본문을 끝까지 옮겼는지
                    S = ns(src)
                    last = [ns(x) for x in b["lines"] if ns(x) and "[생략:" not in x][-1]
                    j = S.find(last, inf["start"]) + len(last)
                    rest = S[j:j + 300]
                    k = rest.find("목록")
                    if k < 0 or (b["lines"][-1].startswith("[생략:") and k > GAP_MAX["접수부서"]) or \
                            (not b["lines"][-1].startswith("[생략:") and k != 0):
                        ok, inf = False, "화면 본문 끝(「목록」 앞)까지 옮기지 않음 — 뒤에 %s자" % (k if k >= 0 else "300+")
                res = ("화면 %s" % m.group(1), ok, inf)
                per_label.append((b, "view", m.group(1)))
        # (다) 4장 판별 조문·부칙
        if res is None:
            m = re.match(r"^(2012\.3\.13 제정판|2016\.7 개정 예고안|2016\.8\.1 판)(?: \[|$)", head)
            if m:
                p = VER[m.group(1)][0]
                arts, sup = rule(p)
                first = b["lines"][0].strip() if b["lines"] else ""
                mm = re.match(r"^제(\d+)조\(", first)
                if mm:
                    n = int(mm.group(1))
                    want = [ns(x) for x in arts[n]["줄"] if x.strip()]
                    got = [ns(x) for x in b["lines"] if x.strip()]
                    ok = want == got
                    inf = "제%d조 전체(%d줄)" % (n, len(got)) if ok else "제%d조 원본과 다름(원본 %d줄·md %d줄)" % (n, len(want), len(got))
                    res = ("%s 제%d조" % (m.group(1), n), ok, inf)
                    per_label.append((b, "art", (m.group(1), n)))
                elif first.startswith("부"):
                    want = [ns(x) for x in sup if x.strip()]
                    got = [ns(x) for x in b["lines"] if x.strip()]
                    ok = want == got
                    res = ("%s 부칙" % m.group(1), ok, "부칙 전체(%d줄)" % len(got) if ok else "부칙 원본과 다름")
                    per_label.append((b, "sup", m.group(1)))
        # (라) 전문
        if res is None and "· 전문 ·" in head:
            p = F2016 if "통합위험관리 모범규준 개정 후 전문" in head else F2012 if "통합리스크관리_모범규준(게시)F_" in head else None
            if p:
                src = read(p + ".md").rstrip("\n").split("\n")
                exact = src == b["lines"]
                ok = exact or ns("\n".join(src)) == ns(txt)
                res = ("전문 %s" % os.path.basename(p), ok, "파일 전체 %d줄 %s" % (len(src), "글자까지 같음" if exact else "공백만 다름")
                       if ok else "파일 전체와 다름")
                per_label.append((b, "full", p))
        # (마) 로컬 텍스트
        if res is None:
            m = re.search(r"줄 (\d+)-(\d+) · `(dart_out/text/[^`]+)`", head)
            if m:
                i, j, path = int(m.group(1)), int(m.group(2)), m.group(3)
                src = read(path).split("\n")
                exact = src[i - 1:j] == b["lines"]
                ok = exact or ns("\n".join(src[i - 1:j])) == ns(txt)
                inf = "줄 %d-%d %s" % (i, j, "글자까지 같음" if exact else "공백만 다름") if ok else "줄 %d-%d 원본과 다름" % (i, j)
                res = ("로컬 %s" % os.path.basename(path), ok, inf)
                per_label.append((b, "local", (path, i, j)))
        if res is None:
            R.ng("%s: 출처를 알 수 없는 인용(머리 「%s」)" % (where, head[:60]))
            continue
        name, ok, inf = res
        if ok:
            n_ok += 1
            R.ok("%s %s — %s" % (where, name, inf if isinstance(inf, str) else "생략 %s ; 끝 뒤 %d자" % (
                ", ".join(inf["gaps"]) or "없음", inf["tail"])))
        else:
            R.ng("%s %s — %s" % (where, name, inf))
    R.info("대조한 인용 %d개 중 맞음 %d개" % (len(blocks), n_ok))
    return blocks, per_label


def check_labels(R, per_label):
    R.h("2. 출처 표기(문서명·URL/접수번호·쪽/조문·수집일)와 .meta.json")
    for b, kind, x in per_label:
        head, where = b["head"], "md %d줄 머리" % b["hn"]
        miss = []
        if kind in ("press", "view", "full", "art", "sup"):
            if "https://" not in head:
                miss.append("URL")
            if not re.search(r"수집 %s\(UTC; \.meta\.json fetched_at [0-9T:+-]+\)" % TODAY, head):
                miss.append("수집일(fetched_at)")
        if kind == "press":
            p, ntt, vp = PRESS[re.search(r"첨부 `([^`]+)`", head).group(1)]
            mt, mv = meta(p), meta(vp)
            if BODO_VIEW % ntt not in head or mv["출처URL"] != BODO_VIEW % ntt:
                miss.append("게시글 URL")
            if "sha256 %s" % mt["sha256"][:16] not in head or mt["sha256"] != sha_file(p):
                miss.append("sha256")
            if "fetched_at %s" % mt["fetched_at"] not in head:
                miss.append("fetched_at≠meta")
            if "전문" not in head:
                miss.append("범위(전문)")
        elif kind == "view":
            p = os.path.join(D, x)
            mt = meta(p)
            if VIEWS[x] not in head or mt["출처URL"] != VIEWS[x]:
                miss.append("URL≠meta")
            if "sha256 %s" % mt["sha256"][:16] not in head or mt["sha256"] != sha_file(p):
                miss.append("sha256")
            if "fetched_at %s" % mt["fetched_at"] not in head:
                miss.append("fetched_at≠meta")
            if "화면 본문" not in head:
                miss.append("범위")
        elif kind in ("full", "art", "sup"):
            p = x if kind == "full" else VER[x[0] if kind == "art" else x][0]
            mt = meta(p)
            url = mt.get("행정지도상세") or mt.get("행정지도예고상세")
            if url not in head:
                miss.append("게시 URL(%s)" % url)
            if mt["sha256"] != sha_file(p) or (mt["sha256"][:16] not in head and kind == "full"):
                miss.append("sha256")
            if "fetched_at %s" % mt["fetched_at"] not in head:
                miss.append("fetched_at≠meta")
            if kind == "art" and "제%d조" % x[1] not in head:
                miss.append("조문")
            if kind == "sup" and "부칙" not in head:
                miss.append("부칙 표기")
            if os.path.basename(p) not in head:
                miss.append("원본 파일 이름")
        elif kind == "local":
            path, i, j = x
            src = read(path).split("\n")
            pg = None
            for k in range(i - 1, -1, -1):
                mm = re.match(r"=== p\.(\d+) ===", src[k])
                if mm:
                    pg = int(mm.group(1))
                    break
            inside = [s for s in src[i - 1:j] if s.startswith("=== p.")]
            mm = re.search(r"쪽 p\.(\d+)", head)
            if not mm or int(mm.group(1)) != pg or inside:
                miss.append("쪽(텍스트 표지 p.%s%s)" % (pg, ", 인용 안에 쪽 바뀜" if inside else ""))
            # 쪽 전체 글(표지~다음 표지)
            a = next(k for k in range(i - 1, -1, -1) if src[k].startswith("=== p."))
            z = next((k for k in range(j, len(src)) if src[k].startswith("=== p.")), len(src))
            page = "\n".join(src[a:z])
            pm = re.search(r"인쇄 「Page (\d+)」", head)
            if pm and not re.search(r"Page %s\s*$" % pm.group(1), page, re.M):
                miss.append("인쇄 Page %s 가 그 쪽에 없음" % pm.group(1))
            pm = re.search(r"인쇄 쪽 (\d+)", head)
            if pm and not re.search(r"^\s*%s(\s|$)" % pm.group(1), page, re.M):
                miss.append("인쇄 쪽 %s 가 그 쪽에 없음" % pm.group(1))
            if "다음 쪽" in head:
                miss.append("인쇄 쪽 「다음 쪽」 표기(그 쪽 바닥글 번호로 적을 것)")
            mr = re.search(r"접수번호 (\d{14})", head)
            if mr and mr.group(1) not in path:
                miss.append("접수번호≠파일")
            if "연차보고서__" in path:
                fn = os.path.basename(path).split("__", 1)[1].replace(".txt", ".pdf")
                row = next((r for r in read_csv(ANNUAL_LIST) if r["파일명"] == fn), None)
                if not row or row["url"] not in head:
                    miss.append("URL≠연차보고서_파일목록")
                elif "수집 %s" % row["fetched_at"] not in head:
                    miss.append("원본 PDF 수집 시각(연차보고서_파일목록 fetched_at)")
            elif "접수번호" not in head:
                miss.append("접수번호")
            if not re.search(r"수집", head):
                miss.append("수집일")
        if miss:
            R.ng("%s(%s): 출처 표기 문제 — %s" % (where, kind, ", ".join(miss)))
        else:
            R.ok("%s(%s): 문서명·URL/접수번호·위치·수집일·sha256/fetched_at" % (where, kind))


def prv_count(p):
    """hwp 안 미리보기 글(PrvText) 조각 수와 변환본에 없는 조각 수."""
    import olefile  # noqa: WPS433
    ole = olefile.OleFileIO(p)
    prv = ole.openstream("PrvText").read().decode("utf-16-le", "replace") if ole.exists("PrvText") else ""
    ole.close()
    pieces = [ns(x) for x in re.split(r"[<>\r\n]+", prv) if len(ns(x)) >= 4]
    S = ns(press_text(p) if p in (PR2011, PR2012) else read(p + ".md")).replace("\\|", "|")
    return len(pieces), len([x for x in pieces if x not in S and x.rstrip(".…") not in S])


def check_conversion(R):
    R.h("1-2. hwp 변환본 재현(hwp2md 다시 돌림)·미리보기 글(PrvText)·sha256")
    files = [F2016, F2017, F2012, F2016P, PR2011, PR2012]
    tmp = tempfile.mkdtemp(prefix="v13m_")
    try:
        import olefile  # noqa: WPS433
    except Exception:                                                 # noqa: BLE001
        olefile = None
    for p in files:
        mt = meta(p)
        sh = sha_file(p)
        if sh != mt["sha256"]:
            R.ng("%s: sha256 %s ≠ meta %s" % (os.path.basename(p), sh[:16], mt["sha256"][:16]))
            continue
        out = os.path.join(tmp, "x.md")
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "hwp2md.py"), p, out], capture_output=True, text=True)
        same = r.returncode == 0 and rbytes(out) == rbytes(p + ".md")
        msg = "hwp2md 재실행 결과와 변환본 바이트 같음" if same else "hwp2md 재실행 결과가 변환본과 다름(rc=%s)" % r.returncode
        if olefile:
            ole = olefile.OleFileIO(p)
            prv = ole.openstream("PrvText").read().decode("utf-16-le", "replace") if ole.exists("PrvText") else ""
            ole.close()
            pieces = [ns(x) for x in re.split(r"[<>\r\n]+", prv) if len(ns(x)) >= 4]
            S = ns(press_text(p) if p in (PR2011, PR2012) else read(p + ".md")).replace("\\|", "|")
            miss = [x for x in pieces if x not in S and x.rstrip(".…") not in S]
            msg += " ; PrvText 조각 %d개 중 변환본에 없는 것 %d개" % (len(pieces), len(miss))
            if miss and p not in (PR2011, PR2012):
                same = False
        (R.ok if same else R.ng)("%s: sha256 = meta, %s" % (os.path.basename(p), msg))
    if sha_file(F2016) == sha_file(F2017):
        R.ok("2016.8.1 판 첨부와 2017.4.1 판 첨부 sha256 같음(md 1장 note 와 맞음)")
    else:
        R.ng("2016.8.1 판·2017.4.1 판 첨부 sha256 다름 — md 1장 note 와 어긋남")


# ── 3. 조 목록 ────────────────────────────────────────────────────────────────
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def _runs(cs):
    idx = sorted(CIRC.index(c) for c in cs)
    out, st = [], None
    for k, v in enumerate(idx):
        if st is None:
            st = v
        if k + 1 == len(idx) or idx[k + 1] != v + 1:
            out.append(CIRC[st] if st == v else "%s~%s" % (CIRC[st], CIRC[v]))
            st = None
    return "·".join(out)


def mark_with_pos(a):
    """CSV 「2016.8.1판_본문표시」 칸(검증 보정 뒤 꼴): 표시 + 붙은 자리. 예) <삭제 2016. 8. 1.>(①~⑤·⑦ — ⑥·⑧·⑨ 존치)"""
    if not a["표시"]:
        return ""
    if len([x for x in a["줄"] if x.strip()]) == 1:
        return " ".join(a["표시"]) + "(조 전체)"
    pos = [c for c in a["표시항"] if c in CIRC]
    tail = ""
    if any("삭제" in m for m in a["표시"]):
        present = [c for c in CIRC if any(re.match(r"^\s*(?:제\d+조\s*\([^)]*\)\s*)?%s" % c, x) for x in a["줄"])]
        keep = [c for c in present if c not in pos]
        tail = " — %s 존치" % "·".join(keep) if keep else ""
    return " ".join(a["표시"]) + "(%s%s)" % (_runs(pos), tail)


def check_jo_csv(R, lines):
    R.h("3. 조 목록 CSV ↔ 세 판 변환본 조 머리 ↔ md 3장 표")
    rows = read_csv(JO_CSV)
    a16, s16 = rule(F2016)
    a12, s12 = rule(F2012)
    a16p, s16p = rule(F2016P)
    for nm, a in (("2016.8.1판", a16), ("2012.3.13판", a12), ("2016.7예고안", a16p)):
        if sorted(a) != list(range(1, 60)):
            R.ng("%s 변환본 조 머리: 1~59 아님(%s)" % (nm, sorted(set(range(1, 60)) ^ set(a))))
        else:
            R.ok("%s 변환본 조 머리 1~59조 빠짐·겹침 없음" % nm)
    if [int(r["조"]) for r in rows] != list(range(1, 60)):
        R.ng("CSV 조 번호가 1~59 순서가 아님")
    bad = []
    for r in rows:
        n = int(r["조"])
        x, y, z = a16[n], a12[n], a16p[n]
        if ns(r["장"]) != ns(x["장"]) or ns(r["절"]) != ns(x["절"]):
            bad.append("%d조 장·절 %s/%s ↔ 원문 %s/%s" % (n, r["장"], r["절"], x["장"], x["절"]))
        if r["제목_2016.8.1판"] != x["제목"]:
            bad.append("%d조 제목_2016.8.1판 「%s」 ↔ 원문 「%s」" % (n, r["제목_2016.8.1판"], x["제목"]))
        if r["제목_2012.3.13제정판"] != y["제목"]:
            bad.append("%d조 제목_2012 「%s」 ↔ 원문 「%s」" % (n, r["제목_2012.3.13제정판"], y["제목"]))
        if r["제목_2016.7개정예고안"] != z["제목"]:
            bad.append("%d조 제목_2016.7 「%s」 ↔ 원문 「%s」" % (n, r["제목_2016.7개정예고안"], z["제목"]))
        if r["2016.8.1판_본문표시"] != mark_with_pos(x):
            bad.append("%d조 본문표시 「%s」 ↔ 원문 「%s」" % (n, r["2016.8.1판_본문표시"], mark_with_pos(x)))
        if r["사용자시트범위(3~58조)"] != ("Y" if 3 <= n <= 58 else "N"):
            bad.append("%d조 시트범위 칸" % n)
        # 조 머리줄 글(2016판) 그대로인지: 「제N조(제목)」이 머리줄 맨 앞
        if not ns(x["머리줄"]).startswith(ns("제%d조(%s)" % (n, r["제목_2016.8.1판"]))):
            bad.append("%d조 머리줄이 「제%d조(%s)」로 시작하지 않음" % (n, n, r["제목_2016.8.1판"]))
        elif not x["머리줄"].strip().startswith("제%d조(%s)" % (n, r["제목_2016.8.1판"])):
            R.info("%d조 원문 머리 띄어쓰기: 「%s」(CSV 는 공백 없이 「제%d조(%s)」 꼴의 제목만 둠)" % (
                n, re.match(r"^\s*(제\d+조\s*\([^)]*\))", x["머리줄"]).group(1), n, r["제목_2016.8.1판"]))
        if "https://" not in r["출처"] or "fetched_at" not in r["출처"]:
            bad.append("%d조 출처 칸에 URL·수집 시각 없음" % n)
    for b in bad:
        R.ng("CSV: " + b)
    if not bad:
        R.ok("CSV 59행 — 조 번호·장·절·세 판 제목·본문 개정/삭제 표시(자리 포함)·시트 범위·출처(URL·fetched_at)가 변환본과 같음")
    sheet = [r for r in rows if r["사용자시트범위(3~58조)"] == "Y"]
    R.info("시트 범위 3~58조 %d행 — 그중 본문 표시 있는 조: %s" % (len(sheet), ", ".join(
        "%s조 %s" % (r["조"], r["2016.8.1판_본문표시"]) for r in sheet if r["2016.8.1판_본문표시"])))
    chg = [(int(r["조"]), r["제목_2012.3.13제정판"], r["제목_2016.8.1판"]) for r in rows if r["제목_2012.3.13제정판"] != r["제목_2016.8.1판"]]
    R.info("2012.3.13 제정판 ↔ 2016.8.1 판 제목이 다른 조 %d개: %s" % (len(chg), " ; ".join("%d조 %s→%s" % c for c in chg)))
    same16p = all(r["제목_2016.7개정예고안"] == r["제목_2016.8.1판"] for r in rows)
    (R.ok if same16p else R.ng)("2016.7 예고안 제목 = 2016.8.1 판 제목(59조 모두)" if same16p else "2016.7 예고안 제목이 2016.8.1 판과 다른 조 있음")
    # 장 머리 원문(공백 그대로) — 59조 장 표기 「제 7 장 보칙<삭제 2016. 3. 28.>」
    heads16 = [ln.strip() for ln in rule_text(F2016).split("\n") if re.match(r"^제\s*\d+\s*장", ln.strip())]
    R.info("2016.8.1 판 장 머리(원문 글자): %s" % " | ".join(heads16))
    # md 3장 표
    tbl, in3 = [], False
    for ln in lines:
        if ln.startswith("## 3."):
            in3 = True
            continue
        if in3 and ln.startswith("## "):
            break
        if in3 and re.match(r"^\| \d+ \|", ln):
            tbl.append([c.strip() for c in ln.strip("|").split("|")])
    bad = []
    for r, c in zip(rows, tbl):
        want = [r["조"], r["장"], r["절"] or "-", r["제목_2016.8.1판"], r["제목_2012.3.13제정판"], r["2016.8.1판_본문표시"] or "-",
                r["사용자시트범위(3~58조)"]]
        if c != want:
            bad.append("%s조: md %s ↔ CSV %s" % (r["조"], c, want))
    if len(tbl) != 59:
        bad.append("md 3장 표 행 수 %d" % len(tbl))
    for b in bad:
        R.ng("md 3장 표: " + b)
    if not bad:
        R.ok("md 3장 표 59행 = CSV")
    return chg


# ── 4. 조 번호(조 제목) ───────────────────────────────────────────────────────
def check_jo_tags(R, lines):
    R.h("4. 조 번호(조 제목) — 자료 묶음마다 붙었는지, 제목이 CSV(2016.8.1판)와 같은지")
    T, T12 = titles(), titles12()
    bad, n = [], 0
    for i, ln in outside_code(lines):
        body = re.sub(r"「[^」]*」", "", ln)                          # 지시서·원문 인용 조각 안의 「N조(…)」(타사 규정 제목 등)는 뺌
        for m in re.finditer(r"(?<![\d.])(?:제)?(\d{1,2})조\(([^)]+)\)", body):
            k, t = int(m.group(1)), m.group(2)
            if not 1 <= k <= 59 or t in ("판단", "지시서"):
                continue
            n += 1
            if t != T[k] and t != T12[k] and not t.startswith(T[k] + " —"):
                bad.append("%d줄 %d조(%s) ↔ CSV 「%s」" % (i, k, t, T[k]))
    for b in bad:
        R.ng("조 제목 다름: " + b)
    R.ok("md 본문(코드 밖)의 「N조(제목)」 %d곳 제목 대조, 다른 곳 %d" % (n, len(bad))) if not bad else None
    # 자료 묶음 머리
    blocks = md_blocks(lines)
    for b in blocks:
        if b["sec"].startswith(("## 2.", "## 7.")):
            if "모범규준 조:" not in b["head"] or not re.search(r"\d+조\([^)]+\)|전체", b["head"].split("모범규준 조:")[-1]):
                R.ng("md %d줄 자료 묶음 머리에 「모범규준 조: N조(제목)」 없음" % b["hn"])
            else:
                R.ok("md %d줄 자료 묶음 머리 — %s" % (b["hn"], b["head"].split("모범규준 조:")[-1].strip()[:110]))
    # 9장·10장 표 조 칸
    for sec in ("## 9.", "## 10."):
        rows, ins = [], False
        for i, ln in enumerate(lines, 1):
            if ln.startswith(sec):
                ins = True
                continue
            if ins and ln.startswith("## "):
                break
            if ins and ln.startswith("| ") and not ln.startswith("| 구분") and not ln.startswith("| 지시서") and not ln.startswith("|---"):
                rows.append((i, [c.strip() for c in ln.strip().strip("|").split("|")]))
        if not rows:
            R.ng("%s 절 표가 없음" % sec)
            continue
        badr = []
        for i, c in rows:
            cell = c[-1] if sec == "## 9." else c[2]
            nums = re.findall(r"(?<![\d.])(\d{1,2})조(?!\()", re.sub(r"「[^」]*」", "", cell))
            if nums:
                badr.append("%d줄 「%s」" % (i, cell[:60]))
        if badr:
            R.ng("%s 표 조 칸에 제목 없는 조 번호: %s" % (sec, " ; ".join(badr)))
        else:
            R.ok("%s 표 %d행 — 조 칸의 조 번호마다 제목" % (sec, len(rows)))


# ── 5. 지시서 항목 ────────────────────────────────────────────────────────────
# (항목 열쇠, 지시서 원문 줄(REQUEST13.md 그대로), 모범규준 조, 이 md 의 받은 글, 상태)
REQ_ITEMS = [
    ("배경", "폐지된 금융지주회사 통합위험관리 모범규준(3조~58조)을 행으로,", list(range(3, 59)), "5장 전문", "받은 글"),
    ("9-4-1 목차", "그룹리스크관리규정(이름이 다르면 대응 규정)의 조문 목차 전체(조 번호와 제목). 전문이 있으면 전문",
     list(range(1, 60)), "3장 표·CSV", "받은 글"),
    ("9-4-1 iM", "iM 그룹 리스크관리규정은 28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음.", [28, 30],
     "5장", "받은 글"),
    ("9-4-1 메리츠", "메리츠 그룹리스크관리규정 9조 7항, 57조가 인용되어 있음. 같은 방식으로 대조", [9, 57], "5장·7장", "받은 글"),
    ("9-4-2 21·22·24", "21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부", [21, 22, 24], "5장",
     "받은 글"),
    ("9-4-2 27", "27조 전략·평판위험: 관리 체제, 측정이나 평가 수단", [27], "5장", "받은 글"),
    ("9-4-2 34", "34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고", [34], "5장", "받은 글"),
    ("9-4-2 3", "3조: 위험이 경미한 자회사를 적용에서 빼는 기준", [3], "5장", "받은 글"),
    ("9-4-2 17", "17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)", [17], "5장", "받은 글"),
    ("9-4-2 55", "55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)", [55], "5장", "받은 글"),
    ("9-4-2 53", "53조 위기대응조직: 구성과 전환 요건", [53], "5장", "받은 글"),
    ("9-4-3", "위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구", [4, 5], "5장·4장·7장", "받은 글"),
    ("끝 표", "작업별로 \"받은 것 / 받지 못한 것 / 원문과 다른 것을 발견한 곳\"을 한 표로", [], "9장", "있음"),
    ("끝 조 번호", "01 엑셀판 '주제1_모범규준기준'의 어느 조 행에 넣을 자료인지 조 번호를 붙임", [], "각 묶음 머리·3·9·10장", "있음"),
]
# 조별로 함께 볼 조(판단) — 지시서 항목 설명에 맞닿은 다른 조문
REQ_EXTRA = {"9-4-2 3": [18, 36], "9-4-2 55": [52], "9-4-1 메리츠": [56]}


def art_line(lines, n):
    """md 5장 전문 코드 블록 안의 「제N조(」 줄 번호."""
    in5, inc = False, False
    for i, ln in enumerate(lines, 1):
        if ln.startswith("## 5."):
            in5 = True
            continue
        if in5 and ln.startswith("## "):
            break
        if in5 and ln.startswith("```"):
            inc = not inc
            continue
        if in5 and inc and ln.startswith("제%d조(" % n):
            return i
    return None


def check_request(R, lines):
    R.h("5. 지시서(REQUEST13) 9-4 항목 ↔ 10장 표")
    if os.path.exists(REQ13):
        rq = read(REQ13)
        for key, src, *_ in REQ_ITEMS:
            if ns(src) not in ns(rq):
                R.ng("지시서 원문에 없는 항목 글(스크립트 상수): %s" % key)
        R.ok("스크립트의 지시서 항목 글 %d개가 REQUEST13.md 에 그대로 있음" % len(REQ_ITEMS))
    else:
        R.info("REQUEST13.md 가 없어(세션 임시 폴더) 항목 글 대조는 건너뜀 — 스크립트 상수로 10장 표만 봄")
    sec = [(i, ln) for i, ln in enumerate(lines, 1)]
    try:
        a = next(i for i, ln in sec if ln.startswith(SEC10_HEAD))
    except StopIteration:
        R.ng("10장(지시서 항목별 대조) 절이 없음")
        return
    body = []
    for i, ln in sec[a:]:
        if ln.startswith("## "):
            break
        body.append((i, ln))
    T = titles()
    for key, src, arts, where, st in REQ_ITEMS:
        row = next(((i, ln) for i, ln in body if ln.startswith("| %s |" % key)), None)
        if not row:
            R.ng("10장 표에 「%s」 행 없음" % key)
            continue
        i, ln = row
        if "받은 글" not in ln and "추출 범위에 없음" not in ln and "있음" not in ln:
            R.ng("10장 %d줄 「%s」: 상태(받은 글 / 추출 범위에 없음+찾은 방법) 없음" % (i, key))
            continue
        badl = []
        for n in arts if len(arts) < 10 else []:
            if jo(n, T) not in ln:
                badl.append("조 %s" % jo(n, T))
            L = art_line(lines, n)
            if not L or ("md %d줄" % L) not in ln:
                badl.append("5장 줄 번호(제%d조 = md %s줄)" % (n, L))
        if badl:
            R.ng("10장 %d줄 「%s」: %s" % (i, key, ", ".join(badl)))
        else:
            R.ok("10장 %d줄 「%s」 — %s" % (i, key, st))


# ── 6. 「추출 범위에 없음」 ───────────────────────────────────────────────────
HOW = re.compile(r"검색|찾|질의|요청|robots|HTTP|방화벽|낱말|검색어|전수")


def check_notfound(R, lines):
    R.h("6. 「추출 범위에 없음」 — 찾은 방법·반박 시도")
    occ = [(i, ln) for i, ln in outside_code(lines) if "추출 범위에 없음" in ln and not ln.startswith(("- 한계", "| 「추출 범위에 없음」"))]
    # 검증 기록 절 안의 줄은 빼고 셈
    vh = next((i for i, ln in enumerate(lines, 1) if ln.startswith(VERIFY_HEAD)), len(lines) + 1)
    s10 = next((i for i, ln in enumerate(lines, 1) if ln.startswith(SEC10_HEAD)), len(lines) + 1)
    occ = [(i, ln) for i, ln in occ if i < min(vh, s10)]
    for i, ln in occ:
        if not HOW.search(ln.replace("추출 범위에 없음", "")):
            R.ng("%d줄: 「추출 범위에 없음」에 찾은 방법이 없음" % i)
    R.ok("「추출 범위에 없음」 %d곳(검증 절 앞) — 같은 줄에 찾은 방법" % len(occ))
    if not os.path.exists(REFUTE_JSON):
        R.ng("반박 시도 결과 %s 없음 — `refute` 를 먼저 돌릴 것" % REFUTE_JSON)
        return occ
    rf = json.load(open(REFUTE_JSON, encoding="utf-8"))
    md = "\n".join(lines)
    for c in build_claims(rf):
        tag = "검증(2026-10-07) 반박 시도[%s]" % c["id"]
        if tag not in md:
            R.ng("반박 시도 [%s] 결과가 md 에 없음" % c["id"])
        else:
            R.ok("반박 시도 [%s] %s — md 에 덧붙임" % (c["id"], c["결과"]))
    return occ


# ── 7. 공통 ──────────────────────────────────────────────────────────────────
def secrets():
    vals = []
    for k in ("DART_API_KEY", "LAW_OC"):
        v = os.environ.get(k, "").strip()
        if v:
            vals.append(v)
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*(DART_API_KEY|LAW_OC)\s*=\s*(.+)$", line)
                if m:
                    vals.append(m.group(2).strip().strip('"').strip("'"))
    return [v for v in vals if len(v) >= 6]


def check_common(R, lines):
    R.h("7. 인증값·PDF·검증 기록 절")
    vals = secrets()
    files = [MD, JO_CSV, OUT_TXT, os.path.abspath(__file__)]
    if os.path.isdir(VD):
        files += [os.path.join(dp, f) for dp, _, fs in os.walk(VD) for f in fs if not f.endswith((".hwp", ".pdf"))]
    for p in files:
        if not os.path.exists(p):
            continue
        t = rbytes(p).decode("utf-8", "replace")
        if any(v in t for v in vals):
            R.ng("인증값 문자열이 들어 있음: %s" % p)
        for pat in (r"OC=(?!\*\*\*)[A-Za-z0-9]", r"crtfc_key=[0-9a-f]{20,}", r"DART_API_KEY\s*=\s*\w{10,}", r"LAW_OC\s*=\s*\w{4,}"):
            if re.search(pat, t):
                R.ng("인증값 꼴 문자열(%s): %s" % (pat, p))
    R.ok("인증값 값 %d개·꼴 4개로 %d개 파일 확인(값은 찍지 않음)" % (len(vals), len(files)))
    pdfs = [os.path.join(dp, f) for dp, _, fs in os.walk(OUT) for f in fs if f.lower().endswith(".pdf")]
    (R.ng if pdfs else R.ok)("산출 폴더에 PDF: %s" % pdfs if pdfs else "산출 폴더(handoff/13차_산출물)에 PDF 없음")
    heads = [ln for ln in lines if ln.startswith("## ")]
    if not heads or heads[-1] != VERIFY_HEAD:
        R.ng("md 맨 끝 절이 「%s」 아님" % VERIFY_HEAD)
    else:
        R.ok("md 맨 끝 「%s」" % VERIFY_HEAD)
    # md 의 게시글·첨부 URL 이 요청기록(원 수집 + 검증 수집)에 있는지
    urls = set(r["URL"] for r in read_csv(REQLOG))
    for p in [os.path.join(dp, f) for dp, _, fs in os.walk(D) for f in fs if f.endswith(".meta.json")]:
        m = json.load(open(p, encoding="utf-8"))
        urls.add(m.get("출처URL", ""))
    found = set(re.findall(r"https://www\.fss\.or\.kr/fss/[^\s·|)\]`]+", "\n".join(lines)))
    miss = sorted(u for u in found if u not in urls)
    (R.ng if miss else R.ok)("md 의 금감원 URL 이 요청기록·meta 에 없음: %s" % miss if miss else
                             "md 의 금감원 URL %d개 모두 요청기록·.meta.json 에 있음" % len(found))


def check_inline(R, lines):
    R.h("참고. note·표 줄 안 「…」 조각 ↔ 원본 글(문제로 세지 않음)")
    srcs = [read(p + ".md") for p in (F2016, F2012, F2016P, PR2011, PR2012)] + [press_text(p) for p in (PR2011, PR2012)]
    srcs += [view_text(r) for r in VIEWS] + [view_text("fss/admnPrvntc_view_1.html"), view_text("fss/admin_view_20120320105719564.html")]
    for f in ("증권신고서__우리금융지주__20181108000394.txt", "연차보고서__KB금융지주_지배구조연차보고서_2026.txt",
              "연차보고서__신한금융지주_지배구조연차보고서_2026.txt", "사업보고서__신한금융지주__20260318000826.txt",
              "연차보고서__메리츠금융지주_지배구조연차보고서_2026.txt"):
        srcs.append(read(os.path.join(T8, f)))
    for f in ("etoday_454869.html", "kofia_seq156_h451.html", "kofia_seq155_h1800_full.html", "kofia_seq155.html", "kiri_docId3403.bin.txt",
              "kcmi_fid4882.bin.txt", "robots_www.kfb.or.kr.txt"):
        p = os.path.join(D, f)
        if os.path.exists(p):
            t = rbytes(p).decode("utf-8", "replace")
            srcs.append(strip_tags(t) if f.endswith(".html") else t)
    srcs += [read_now(REQLOG), read_now(os.path.join(WORK, "9-2-4_9-5_정책확인.csv"))]
    if os.path.exists(REQ13):
        srcs.append(read(REQ13))
    ALL = ns("\n".join(srcs))
    tot, nf = 0, []
    vh = next((i for i, ln in enumerate(lines, 1) if ln.startswith(VERIFY_HEAD)), len(lines) + 1)
    for i, ln in outside_code(lines):
        if i >= vh:
            break
        for q in re.findall(r"「([^」]+)」", ln):
            for part in re.split(r"…|\.\.\.", q):
                p = ns(part)
                if len(p) < 4:
                    continue
                tot += 1
                if p not in ALL:
                    nf.append((i, part[:50]))
    R.info("「…」 조각 %d개 중 원본 글에서 못 찾은 것 %d개(표 이름·검색어·md 안 이름 등 — 사람이 봄):" % (tot, len(nf)))
    for i, p in nf:
        R.info("    %d줄 「%s」" % (i, p))
    return tot, nf


def run_checks():
    R = Report()
    lines = read_now(MD).split("\n")
    blocks, per_label = check_quotes(R, lines)
    check_conversion(R)
    check_labels(R, per_label)
    chg = check_jo_csv(R, lines)
    check_jo_tags(R, lines)
    check_request(R, lines)
    occ = check_notfound(R, lines)
    check_common(R, lines)
    tot, nf = check_inline(R, lines)
    return R, dict(blocks=blocks, chg=chg, occ=occ, inline=(tot, nf))


def write_report(R, mode):
    head = ["# 13차 9-4 모범규준 원문 검증(verify13_mobeom.py, 모드 %s)" % mode,
            "대상: %s, %s" % (MD, JO_CSV), "결과: 문제 %d, 통과 %d" % (R.n_ng, R.n_ok)]
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(head + R.lines) + "\n")


# ── 반박 시도(refute) ─────────────────────────────────────────────────────────
class Stop(Exception):
    pass


ADMIN = FSS + "/fss/job/admnstgudc/list.do"
PRVNTC = FSS + "/fss/job/admnPrvntc/list.do"
BODO = FSS + "/fss/bbs/B0000188/list.do"
FSCB = "https://www.fsc.go.kr/no010101"
HIT = re.compile(r"지주|통합|그룹|모범규준|리스크관리|위험관리")
TARGET = re.compile(r"통합\s*(리스크|위험)\s*관리|그룹\s*(리스크|위험)\s*관리\s*모범")


def _rows_admin(t):
    out = []
    j = t.find("<tbody")
    k = t.find("</tbody>", j)
    for tr in re.findall(r"<tr>(.*?)</tr>", t[j:k], re.S):
        a = re.search(r'<td class="title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        if not a:
            continue
        no = re.search(r'<td class="no">(.*?)</td>', tr, re.S)
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        files = [strip_tags(n) for n in re.findall(r'<span class="name">(.*?)</span>', tr, re.S)]
        seq = re.search(r"guGuidanceMgrSeq=(\d+)", html.unescape(a.group(1)))
        out.append(dict(관리번호=strip_tags(no.group(1)) if no else "", 제목=strip_tags(a.group(2)),
                        시행일=strip_tags(tds[1]) if len(tds) > 1 else "", 시행여부=strip_tags(tds[2]) if len(tds) > 2 else "",
                        첨부=" ; ".join(files), 상세=ADMV % seq.group(1) if seq else ""))
    return out


def _rows_prvntc(t):
    out = []
    j = t.find("<tbody")
    k = t.find("</tbody>", j)
    for tr in re.findall(r"<tr>(.*?)</tr>", t[j:k], re.S):
        a = re.search(r'<a href="([^"]*seqno=(\d+)[^"]*)"[^>]*>(.*?)</a>', tr, re.S)
        cells = re.sub(r"\s+", " ", strip_tags(tr).replace("\n", " "))
        d = re.search(r"(\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2})", cells)
        if a:
            out.append(dict(제목=strip_tags(a.group(3)), 기간=d.group(1) if d else "", 상세=PRVV % a.group(2)))
    return out


def _rows_bodo(t):
    out = []
    for m in re.finditer(r'<td class="title"><a href="([^"]+)">(.*?)</a></td>\s*<td>(.*?)</td>\s*<td>\s*([\d-]+)\s*</td>', t, re.S):
        ntt = re.search(r"nttId=(\d+)", html.unescape(m.group(1)))
        out.append(dict(제목=strip_tags(m.group(2)), 등록일=m.group(4), 상세=BODO_VIEW % ntt.group(1) if ntt else ""))
    return out


def _rows_fsc(t):
    out = []
    for li in re.findall(r'<div class="subject">\s*<a href="/no010101/(\d+)[^"]*"[^>]*>(.*?)</a>.*?<div class="day">([\d-]+)</div>', t, re.S):
        out.append(dict(제목=strip_tags(li[1]), 등록일=li[2], 상세=FSCB + "/" + li[0]))
    return out


def refute():
    from web13 import Web, Robots, save, now, write_csv           # noqa: WPS433
    os.makedirs(VD, exist_ok=True)
    W = Web()
    rob, log = {}, []

    def fetch(name, url, extra):
        p = os.path.join(VD, name)
        if os.path.exists(p) and os.path.exists(p + ".meta.json"):
            return rbytes(p).decode("utf-8", "replace"), meta(p)
        base = "%s://%s" % urllib.parse.urlparse(url)[:2]
        if base not in rob:
            rob[base] = Robots(W, base, "verify13_mobeom")
            log.append(dict(시각=now(), URL=base + "/robots.txt", 결과="robots " + rob[base].status, 사유=rob[base].note))
        if not rob[base].allowed(url):
            log.append(dict(시각=now(), URL=url, 결과="요청 안 함", 사유="robots.txt %s" % rob[base].status))
            raise Stop("robots 불허")
        try:
            fu, st, hd, b = W.get(url)
        except Exception as e:                                       # noqa: BLE001
            log.append(dict(시각=now(), URL=url, 결과="실패", 사유="%s: %s" % (type(e).__name__, str(e)[:200])))
            raise Stop("접속 실패 %s" % type(e).__name__)
        low = b[:30000].decode("utf-8", "replace").lower()
        if "/login" in fu.lower() or "captcha" in low or "자동입력방지" in low:
            log.append(dict(시각=now(), URL=url, 결과="멈춤", 사유="로그인/캡차 화면"))
            raise Stop("로그인/캡차")
        sub, bn = os.path.split(name)
        p, m = save("verify13_mobeom" + ("/" + sub if sub else ""), bn, b,
                    dict(출처URL=url, 최종URL=fu, http_status=st, fetched_at=now(), **extra))
        log.append(dict(시각=now(), URL=url, 결과="HTTP %s" % st, 사유=""))
        return b.decode("utf-8", "replace"), m

    res = dict(실행=now(), queries=[], claims=[])

    def run(site, label, url_of, parse, tot_re, name_of, maxpage, extra):
        q = dict(곳=site, 질의=label, 쪽=0, 총건수=None, 행=[], 멈춤="")
        for page in range(1, maxpage + 1):
            try:
                t, m = fetch(name_of(page), url_of(page), dict(extra, 쪽=page))
            except Stop as e:
                q["멈춤"] = str(e)
                break
            mm = re.search(tot_re, t)
            q["총건수"] = int(mm.group(1).replace(",", "")) if mm else 0
            rows = parse(t)
            q["쪽"] = page
            q["행"] += rows
            if not rows or page * 10 >= q["총건수"]:
                break
        q["관련행"] = [r for r in q["행"] if HIT.search(r["제목"])]
        q["대상행"] = [r for r in q["행"] if TARGET.search(r["제목"])]
        q["다 봄"] = q["총건수"] is not None and len(q["행"]) >= q["총건수"]
        res["queries"].append(q)
        print("%s %s — 총 %s건, 받은 쪽 %s, 관련 %d, 대상 %d%s" % (site, label, q["총건수"], q["쪽"], len(q["관련행"]),
                                                       len(q["대상행"]), " 멈춤:" + q["멈춤"] if q["멈춤"] else ""))
        return q

    # A. 금감원 「행정지도 내역」(시행여부=전체) — 연도별 전체(검색어 없음) + 넓은 주제어
    for yr in ("2012", "2016", "2017", "2018"):
        run("행정지도 내역", "연도 %s 전체(주제어 없음)" % yr,
            lambda pg, yr=yr: ADMIN + "?" + urllib.parse.urlencode(dict(menuNo="200492", pageIndex=str(pg), searchRegn="",
                                                                        searchYear=yr, searchCecYn="T", searchWrd="")),
            _rows_admin, r"전체\s*<em>([\d,]+)</em>", lambda pg, yr=yr: "fss/admin_year%s_p%02d.html" % (yr, pg), 12,
            dict(검색=yr + "년 전체"))
    for kw in ("금융지주", "내부통제기준", "통합", "그룹", "존속기한"):
        run("행정지도 내역", "주제어 「%s」(전 연도)" % kw,
            lambda pg, kw=kw: ADMIN + "?" + urllib.parse.urlencode(dict(menuNo="200492", pageIndex=str(pg), searchRegn="",
                                                                        searchYear="", searchCecYn="T", searchWrd=kw)),
            _rows_admin, r"전체\s*<em>([\d,]+)</em>", lambda pg, kw=kw: "fss/admin_kw_%s_p%02d.html" % (kw, pg), 6, dict(검색어=kw))
    # B. 금감원 「행정지도 예고」 — 제목 검색(사이트는 제목만 지원)
    for kw in ("모범규준", "금융지주", "존속기한", "그룹", "내부통제"):
        run("행정지도 예고", "제목 「%s」" % kw,
            lambda pg, kw=kw: PRVNTC + "?" + urllib.parse.urlencode(dict(menuNo="200491", pageIndex=str(pg), searchCnd="1",
                                                                         searchWrd=kw)),
            _rows_prvntc, r"전체\s*<em>([\d,]+)</em>", lambda pg, kw=kw: "fss/prvntc_kw_%s_p%02d.html" % (kw, pg), 4, dict(검색어=kw))
    # C. 금감원 보도자료 — 기간·범위를 넓힘
    for kw, cnd, sd, ed in (("모범규준", "3", "2011-01-01", "2015-12-31"), ("모범규준", "3", "2016-01-01", "2018-12-31"),
                            ("통합위험관리", "3", "2017-01-01", "2021-12-31"),
                            ("그룹리스크", "3", "2011-01-01", "2016-12-31"), ("금융지주회사", "1", "2012-03-01", "2012-04-30"),
                            ("금융지주회사", "1", "2016-03-01", "2016-08-31")):
        run("금감원 보도자료", "「%s」(%s) %s~%s" % (kw, "제목+내용" if cnd == "3" else "제목", sd, ed),
            lambda pg, kw=kw, cnd=cnd, sd=sd, ed=ed: BODO + "?" + urllib.parse.urlencode(dict(
                menuNo="200218", pageIndex=str(pg), sdate=sd, edate=ed, searchCnd=cnd, searchWrd=kw)),
            _rows_bodo, r"전체\s*<em>([\d,]+)</em>", lambda pg, kw=kw, sd=sd: "press/fss_%s_%s_%s_p%02d.html" % (kw, cnd, sd[:4], pg),
            10, dict(검색어=kw, 기간="%s~%s" % (sd, ed)))
    # D. 금융위 보도자료 — 「모범규준」 제목+내용(원 수집은 제목만), 「그룹리스크」
    for kw in ("모범규준", "그룹리스크"):
        run("금융위 보도자료", "「%s」(제목+내용) 2011-01-01~2016-12-31" % kw,
            lambda pg, kw=kw: FSCB + "?" + urllib.parse.urlencode(dict(srchCtgry="", curPage=str(pg), srchKey="all", srchText=kw,
                                                                       srchBeginDt="2011-01-01", srchEndDt="2016-12-31")),
            _rows_fsc, r"전체\s*<strong>([\d,]+)</strong>", lambda pg, kw=kw: "press/fsc_%s_all_p%02d.html" % (kw, pg), 8,
            dict(검색어=kw))
    # C2. 위 보도자료 검색에서 나온 2016~2018 지주·통합위험관리 관련 글 본문 — 이 모범규준(연장·폐지)을 적었는지
    pv = []
    for q in res["queries"]:
        if q["곳"] != "금감원 보도자료":
            continue
        for r in q["관련행"]:
            if r["등록일"] >= "2016-01-01" and re.search(r"금융지주|통합감독 관련 업계", r["제목"]) and r["상세"]:
                ntt = re.search(r"nttId=(\d+)", r["상세"]).group(1)
                try:
                    t, m = fetch("press/fss_view_%s.html" % ntt, r["상세"], dict(검색="본문 확인"))
                except Stop as e:
                    pv.append(dict(글=r["상세"], 제목=r["제목"], 멈춤=str(e)))
                    continue
                tt = strip_tags(t)
                pv.append(dict(글=r["상세"], 제목=r["제목"], 등록일=r["등록일"],
                               대상낱말=[tt[max(0, x.start() - 60):x.end() + 60] for x in re.finditer(
                                   r"통합\s*(?:리스크|위험)\s*관리\s*모범규준|그룹\s*내부통제\s*기준\s*모범규준", tt)][:5],
                               첨부=re.findall(r'<span class="name">(.*?)</span>', t)[:6]))
    res["press_views"] = pv
    for x in pv:
        print("보도자료 본문", x.get("등록일"), x["제목"][:40], "— 이 모범규준 낱말 %d곳" % len(x.get("대상낱말", [])))
    # E. 법제처 행정규칙(연혁 포함) — 더 넓은 이름
    law = []
    try:
        sys.path.insert(0, os.path.join(ROOT, "scripts", "law"))
        from lawclient import LawClient                              # noqa: WPS433
        os.environ.setdefault("LAW_DELAY", "1.0")
        lc = LawClient(os.path.join(VD, "law", "_call_log.csv"))
        for kw in ("위험관리", "리스크관리", "그룹"):
            p = os.path.join(VD, "law", "admrul_%s_nw2.xml" % kw)
            if os.path.exists(p):
                body = rbytes(p)
            else:
                st, body, murl, host = lc.api("lawSearch.do", target="admrul", type="XML", query=kw, nw="2", display="100")
                body = lc.mask(body)
                save("verify13_mobeom/law", os.path.basename(p), body, dict(출처URL=murl, http_status=st, fetched_at=now(),
                                                                          검색어=kw, nw="2"))
            t = body.decode("utf-8", "replace")
            names = re.findall(r"<행정규칙명><!\[CDATA\[(.*?)\]\]></행정규칙명>", t) or re.findall(r"<행정규칙명>(.*?)</행정규칙명>", t)
            tot = re.search(r"<totalCnt>(\d+)</totalCnt>", t)
            hit = sorted(set(x for x in names if re.search(r"지주|모범|금융", x)))
            law.append(dict(검색어=kw, 총건수=int(tot.group(1)) if tot else None, 받은이름=len(names), 관련=hit))
            print("법제처 admrul 「%s」 nw=2 — 총 %s건, 받은 %d, 지주·통합·모범 이름 %s" % (kw, tot.group(1) if tot else "?", len(names), hit))
    except SystemExit as e:
        law.append(dict(오류="LAW_OC 없음: %s" % e))
    except Exception as e:                                           # noqa: BLE001
        law.append(dict(오류="%s: %s" % (type(e).__name__, str(e)[:200])))
    res["law"] = law
    # F. 로컬 — 자본시장연구원 2011 제도동향 텍스트, 8·9차 공시 텍스트(조 번호 인용 꼴), 금융투자협회 저장본
    kc = read(os.path.join(D, "kcmi_fid4882.bin.txt"))
    kcj = re.sub(r"\s+", "", kc)
    kterms = ["통합위험", "통합리스크", "통합 위험", "통합 리스크", "그룹리스크", "그룹 리스크", "그룹위험", "모범규준", "위험관리모범",
              "리스크관리모범", "지주회사", "integrated risk", "group risk"]
    res["kcmi"] = {k: (kcj.lower().count(re.sub(r"\s+", "", k).lower())) for k in kterms}
    res["kcmi_모범규준_문맥"] = [kcj[max(0, m.start() - 40):m.end() + 20] for m in re.finditer("모범규준", kcj)][:12]
    pats = {"모범규준 + 제N조": r"모범규준[^\n]{0,15}?제?\d+조", "규준§N": r"규준§\d", "규준 제N조": r"규준제\d+조",
            "통합위험관리모범규준": r"통합위험관리모범규준", "통합리스크관리모범규준": r"통합리스크관리모범규준",
            "그룹위험관리모범규준": r"그룹위험관리모범규준", "영문 best practice·model": r"(?i)bestpractice|modelcode|modelguideline"}
    hits = {k: [] for k in pats}
    nf = 0
    for d in (T8, T9):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".txt"):
                continue
            nf += 1
            t = re.sub(r"\s+", "", read(os.path.join(d, f)))
            for k, pt in pats.items():
                for m in re.finditer(pt, t):
                    hits[k].append(dict(파일=f, 문맥=t[max(0, m.start() - 50):m.end() + 30]))
    res["local"] = dict(파일수=nf, 건수={k: len(v) for k, v in hits.items()},
                        통합모범규준_조번호=[h for k in ("통합위험관리모범규준", "통합리스크관리모범규준", "그룹위험관리모범규준")
                                     for h in hits[k] if re.search(r"모범규준[^가-힣]{0,3}제?\d+조", h["문맥"])],
                        모범규준_조번호_문맥=[h["파일"] + " … " + h["문맥"][-60:] for h in hits["모범규준 + 제N조"]][:20])
    ko = []
    for f in sorted(os.listdir(D)):
        if f.startswith("kofia_") and f.endswith(".html"):
            t = strip_tags(rbytes(os.path.join(D, f)).decode("utf-8", "replace"))
            ko.append(dict(파일=f, 지주=t.count("지주"), 통합=t.count("통합"), 차단="web-firewall" in t))
    res["kofia"] = ko
    # G. 원 수집 저장본(행정지도 내역·예고·보도자료 목록)에서 날짜로 다시 봄
    loc = []
    for f in sorted(os.listdir(os.path.join(D, "fss"))):
        if f.endswith(".html") and (f.startswith("admin_") and "_p" in f or f.startswith("admnPrvntc_") and "_p" in f):
            t = rbytes(os.path.join(D, "fss", f)).decode("utf-8", "replace")
            rows = _rows_admin(t) if f.startswith("admin_") else _rows_prvntc(t)
            for r in rows:
                dt = r.get("시행일") or r.get("기간", "")
                if re.search(r"2012|2016|2018|2019", dt) and HIT.search(r["제목"]):
                    loc.append("%s: %s %s" % (f, dt, r["제목"]))
    res["저장본_날짜"] = sorted(set(loc))
    with open(os.path.join(VD, "_요청기록.csv"), "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["시각", "URL", "결과", "사유"])
        if f.tell() == 0:
            w.writeheader()
        w.writerows(log)
    with open(REFUTE_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("→", REFUTE_JSON, "요청", len(log))


# ── 반박 결과 → 「추출 범위에 없음」 항목별 기록 ───────────────────────────────
def _q(rf, site, label_part):
    for q in rf["queries"]:
        if q["곳"] == site and label_part in q["질의"]:
            return q
    return None


def _qs(rf, site, label_part):
    q = _q(rf, site, label_part)
    if not q:
        return "%s %s(기록 없음)" % (site, label_part)
    n = q["총건수"]
    seen = len(q["행"])
    return "%s %s %s건%s" % (site, q["질의"], n, "" if q["다 봄"] else "(앞 %d건만 봄)" % seen)


def build_claims(rf):
    """refute13.json → [dict(id, 대상, md 고리(그 줄에 붙일 낱말), 검색, 결과, 찾은 것)]."""
    A = "행정지도 내역"
    P = "행정지도 예고"
    B = "금감원 보도자료"
    C = []
    tgt_rows = lambda labs: [r for site, lab in labs for q in [_q(rf, site, lab)] if q for r in q["대상행"]]  # noqa: E731
    # N1 2016.3.28 개정
    labs = [(A, "연도 2016"), (A, "「금융지주」"), (A, "「내부통제기준」"), (A, "「통합」"), (A, "「그룹」"), (A, "「존속기한」"),
            (P, "「모범규준」"), (P, "「금융지주」"), (P, "「그룹」"), (P, "「내부통제」"), (P, "「존속기한」"),
            (B, "「금융지주회사」(제목) 2016"), (B, "「모범규준」(제목+내용) 2016")]
    hits = [r for r in tgt_rows(labs) if re.search(r"2016[.-]?0?3|201603|2016-0[34]", r.get("시행일", "") + r.get("기간", "") + r.get("등록일", ""))]
    C.append(dict(id="N1", 대상="2016.3.28 개정 때의 공문·신구대비표", 고리="| 받지 못한 것 | 2016.3.28 개정 공문·신구대비표 |",
                  검색=[_qs(rf, s_, l_) for s_, l_ in labs], 결과="반박 실패" if not hits else "반박 성공",
                  찾은것=[r["제목"] for r in hits],
                  요약="2016년 행정지도 내역은 5건 전부 보고(이 모범규준은 2014-017 시행일 20160801 한 건), 예고·보도자료에도 2016.3.28·2016.4.1 날짜의 개정 기록 없음"))
    labs = [(A, "연도 2012"), (A, "「금융지주」"), (A, "「내부통제기준」"), (A, "「그룹」"), (B, "「금융지주회사」(제목) 2012"),
            (B, "「모범규준」(제목+내용) 2011")]
    hits = [r for r in tgt_rows(labs) if "2012" in (r.get("시행일", "") + r.get("등록일", "")) and "nttId=9084" not in r.get("상세", "")]
    C.append(dict(id="N2", 대상="2012.3.13 제정 당시 송부 공문(행정지도 기록)", 고리="| 받지 못한 것 | 2012.3.13 제정 당시 송부 공문 |",
                  검색=[_qs(rf, s_, l_) for s_, l_ in labs], 결과="반박 실패" if not hits else "반박 성공", 찾은것=[r["제목"] for r in hits],
                  요약="2012년 행정지도 내역 21건 전부 — 지주 관련은 2014-018 「금융지주회사의그룹내부통제기준모범규준」(시행일 20120401)뿐; "
                       "보도자료는 이미 받은 2012-03-19 「｢금융지주회사 통합리스크관리 모범규준｣ 마련」(nttId=9084)뿐"))
    labs = [(A, "연도 2017"), (A, "연도 2018"), (A, "「존속기한」"), (A, "「그룹」"), (A, "「금융지주」"), (P, "「모범규준」"), (P, "「금융지주」"),
            (P, "「그룹」"), (P, "「내부통제」"), (B, "「모범규준」(제목+내용) 2016"), (B, "「통합위험관리」")]
    hits = [r for r in tgt_rows(labs) if re.search(r"201[89]|202", r.get("시행일", "") + r.get("기간", "") + r.get("등록일", ""))]
    pv = [x for x in rf.get("press_views", []) if x.get("대상낱말")]
    C.append(dict(id="N3", 대상="2018.3.31 이후 존속기한 연장 여부", 고리="| 받지 못한 것 | 2018.3.31 이후 연장 여부 |",
                  검색=[_qs(rf, s_, l_) for s_, l_ in labs] + ["금감원 보도자료 본문 %d건(%s)" % (
                      len(rf.get("press_views", [])), ", ".join(sorted(set("%s %s" % (x.get("등록일", ""), x["제목"][:24])
                                                                     for x in rf.get("press_views", [])))))],
                  결과="반박 실패" if not hits and not pv else "반박 성공", 찾은것=[r["제목"] for r in hits] + [x["제목"] for x in pv],
                  요약="2018년 행정지도 내역 8건 전부에 2014-017 없음, 예고는 2017-02-15~03-07 연장 예고가 마지막, 2018 보도자료 본문에 이 모범규준 이름 없음"))
    q = _q(rf, "금융위 보도자료", "「모범규준」")
    hits = [r for r in (q["행"] if q else []) if TARGET.search(r["제목"])]
    C.append(dict(id="N4", 대상="금융위원회 보도자료 가운데 이 모범규준 발표", 고리="| 받지 못한 것 | 금융위 보도자료 가운데 이 모범규준 발표 |",
                  검색=[_qs(rf, "금융위 보도자료", "「모범규준」"), _qs(rf, "금융위 보도자료", "「그룹리스크」")],
                  결과="반박 실패" if not hits else "반박 성공", 찾은것=[r["제목"] for r in hits],
                  요약="「모범규준」 제목+내용 65건 제목을 전부 봄 — 이 모범규준 제목 없음(원 수집은 제목만 9건)"))
    law = rf.get("law", [])
    C.append(dict(id="N5", 대상="법제처 행정규칙으로 등록된 모범규준", 고리="| 받지 못한 것 | 법제처 행정규칙으로 등록된 모범규준 |",
                  검색=["법제처 lawSearch target=admrul nw=2 「%s」 %s건(이름 %s개 전부 봄)" % (x["검색어"], x["총건수"], x["받은이름"])
                       for x in law if "검색어" in x] + [x["오류"] for x in law if "오류" in x],
                  결과="반박 실패" if not any(re.search(r"지주|모범", n) for x in law for n in x.get("관련", [])) else "반박 성공",
                  찾은것=[n for x in law for n in x.get("관련", []) if re.search(r"지주|모범", n)],
                  요약="이름에 지주·모범이 든 행정규칙 없음(「그룹」 결과의 「금융그룹감독혁신단의 설치 및 운영에 관한 규정」은 다른 규정)"))
    lo = rf["local"]
    C.append(dict(id="N6", 대상="조 번호를 들어 이 모범규준을 인용한 공시 문장(「모범규준 제N조」 꼴)",
                  고리="| 받지 못한 것 | 조 번호를 들어 이 모범규준을 인용한 공시 문장",
                  검색=["dart_out/text/risk8·risk9 txt %d개(공백·줄바꿈 뺀 글) 정규식: %s" % (lo["파일수"], " ; ".join(
                      "「%s」 %d곳" % (k, v) for k, v in lo["건수"].items()))],
                  결과="반박 실패" if not lo["통합모범규준_조번호"] else "반박 성공", 찾은것=lo["통합모범규준_조번호"],
                  요약="「모범규준 + 제N조」 17곳은 모두 사외이사 자격요건·정관 조문(다른 모범규준), 「규준§」 2곳은 신한 p.200 보수·인력 항목, "
                       "이 모범규준 이름(통합리스크관리 모범규준) 4곳에는 조 번호 없음"))
    kc = rf["kcmi"]
    C.append(dict(id="N7", 대상="자본시장연구원 「2011년 자본시장 제도동향」(kcmi fid=4882)의 이 모범규준 언급",
                  고리="| 자본시장연구원 kcmi.re.kr fid=4882(pdf, 560쪽) |",
                  검색=["kcmi_fid4882.bin.txt(공백 뺀 글) 낱말: %s" % " ; ".join("「%s」 %d" % (k, v) for k, v in kc.items())],
                  결과="반박 실패" if not (kc.get("통합위험") or kc.get("통합리스크") or kc.get("그룹리스크") or kc.get("그룹위험")) else "반박 성공",
                  찾은것=[], 요약="「모범규준」 78곳·「리스크관리모범」 5곳·「위험관리모범」 2곳은 금융투자협회 모범규준 목록(적격투자자·신용거래·유동성리스크 등)"))
    ko = rf["kofia"]
    C.append(dict(id="N8", 대상="금융투자협회 법규정보시스템 「모범규준」 연혁 2쪽 이후", 고리="| 받지 못한 것 | 금융투자협회 법규정보시스템",
                  검색=["저장본 %d개(차단 응답 %d개) 화면 글에서 「지주」·「통합」 다시 셈: %s" % (
                      len(ko), sum(x["차단"] for x in ko), " ; ".join("%s 지주%d·통합%d" % (x["파일"].replace("kofia_", "")[:28], x["지주"], x["통합"])
                                                                  for x in ko if not x["차단"] and (x["지주"] or x["통합"])))],
                  결과="반박 시도 안 함(네트워크)", 찾은것=[],
                  요약="사이트 방화벽 차단 응답이라 다시 요청하지 않음(우회 금지) — 저장본의 「지주」·「통합」은 메뉴·검색창 글자"))
    C.append(dict(id="N9", 대상="은행연합회(kfb.or.kr) 자료", 고리="| 받지 못한 것 | 은행연합회 자료 |", 검색=["robots.txt 「Disallow: /」"],
                  결과="반박 시도 안 함", 찾은것=[], 요약="robots.txt 가 전부 막음 — 수집하지 않음(규칙대로)"))
    C.append(dict(id="N10", 대상="한국경제 2012-03-19 기사", 고리="| 받지 못한 것 | 한국경제 2012-03-19 기사 |", 검색=["HTTP 403"],
                  결과="반박 시도 안 함", 찾은것=[], 요약="403 응답 — 다른 주소로 다시 시도하지 않음(우회 금지). 같은 내용은 금감원 보도자료 2-2 원문으로 받음"))
    return C


# ── 보정(fix) ────────────────────────────────────────────────────────────────
FIXLOG = os.path.join(VD, "fix13_log.json")


def _trim(a, b, ctx=12, cap=160):
    """두 글의 같은 앞·뒤를 빼고 다른 가운데만(앞뒤 ctx 자 곁들임)."""
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    q = 0
    while q < min(len(a), len(b)) - p and a[len(a) - 1 - q] == b[len(b) - 1 - q]:
        q += 1
    am, bm = a[p:len(a) - q], b[p:len(b) - q]
    cut = lambda x: x if len(x) <= cap else x[:cap // 2] + "…(%d자)…" % len(x) + x[-cap // 2:]  # noqa: E731
    pre, post = a[max(0, p - ctx):p], a[len(a) - q:len(a) - q + ctx]
    return "「…%s[%s]%s…」 → 「…%s[%s]%s…」" % (pre, cut(am), post, pre, cut(bm), post)


def _diff(a, b):
    """칸(「 · 」·「 | 」·「 — 」) 단위로 바뀐 곳을 찾아 칸마다 「전」 → 「후」."""
    import difflib
    sp = re.compile(r"( · | \| | — |\] — )")
    ta, tb = sp.split(a), sp.split(b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        x, y = "".join(ta[i1:i2]), "".join(tb[j1:j2])
        out.append(_trim(x, y) if x and y else ("덧붙임 「%s」" % (y if len(y) <= 200 else y[:100] + "…(%d자)…" % len(y) + y[-60:])
                                                  if y else "지움 「%s」" % x))
    return " ; ".join(out)


def fix():
    if not os.path.exists(REFUTE_JSON):
        raise SystemExit("먼저 `refute` 를 돌릴 것(%s 없음)" % REFUTE_JSON)
    rf = json.load(open(REFUTE_JSON, encoding="utf-8"))
    claims = build_claims(rf)
    T = titles()
    J = lambda *ns_: "·".join(jo(n, T) for n in ns_)  # noqa: E731
    log = json.load(open(FIXLOG, encoding="utf-8")) if os.path.exists(FIXLOG) else []
    seen = set((x["무엇"], x["전"]) for x in log)
    lines = read_now(MD).rstrip("\n").split("\n")
    cut = next((i for i, ln in enumerate(lines) if ln.startswith((SEC10_HEAD, VERIFY_HEAD))), len(lines))
    lines = lines[:cut]
    while lines and not lines[-1].strip():
        lines.pop()

    def put(i, new, what):
        old = lines[i]
        if old == new:
            return
        key = (what, old)
        if key not in seen:
            log.append(dict(무엇=what, 줄=i + 1, 전=old, 후=new, 차이=_diff(old, new)))
            seen.add(key)
        lines[i] = new

    def fa(p):
        return meta(p)["fetched_at"]

    # (1) 머리 수집일 — 원 수집·검증 수집의 fetched_at 범위(KST)
    def rng(d):
        v = [json.load(open(os.path.join(dp, f), encoding="utf-8")).get("fetched_at", "") for dp, _, fs in os.walk(d) for f in fs
             if f.endswith(".meta.json")]
        v = [x for x in v if x]
        return "%s~%s" % (min(v), max(v)[11:]) if v else "?"
    for i, ln in enumerate(lines[:12]):
        m = re.match(r"^- 수집일: 2026-10-07(?:\(UTC — [^)]*\))? (\(요청 시각은.*)$", ln)
        if m:
            put(i, "- 수집일: 2026-10-07(UTC — 원본 .meta.json 의 fetched_at 은 KST %s, 검증 때 더 받은 것(`%s/`)은 %s) %s" % (
                rng(D), VD, rng(VD), m.group(1)), "머리 수집일(UTC/KST)")
    for i, ln in enumerate(lines[:12]):
        if ln.startswith("- 변환 확인:") and "검증(2026-10-07)" not in ln:
            (a1, m1), (a2, m2) = prv_count(PR2011), prv_count(PR2012)
            put(i, ln + " 검증(2026-10-07): 보도자료 hwp 2개도 미리보기 글을 줄 대신 조각(표 칸 「<…>」·줄바꿈으로 자름, 4자 이상) 단위로 대조 — "
                         "8584 %d개 중 없음 %d, 9084 %d개 중 없음 %d; hwp6개 모두 `hwp2md.py` 를 다시 돌린 결과와 변환본이 바이트까지 같음." % (a1, m1, a2, m2),
                "머리 변환 확인(보도자료 hwp 한계 보완)")
    # (2) 인용 머리 — 수집 시각·조 번호
    sec, sub, art = "", "", None
    tag2 = {
        "2-1": " — 모범규준 조: 전체(추진 배경) ; (판단) 실태조사 4개 영역 = 제2장 %s~%s · 제4장 %s~%s · 제5장 %s~%s · %s·%s"
               % (jo(7, T), jo(13, T), jo(18, T), jo(35, T), jo(36, T), jo(49, T), jo(16, T), jo(56, T)),
        "2-2": " — 모범규준 조: (판단) %s(사외이사 과반수·위원장 전문성 — 2012판 ①) · %s②(M&A 등 사전 심의) · %s(CRO 해임 제한 — 2012판 ①·⑤) · "
               "%s(협의회) · %s~%s(역할과 책임) · %s(자회사간 신용공여 검토) · %s · %s · %s · %s · %s" % (
                   jo(9, T), jo(10, T), jo(11, T), jo(12, T), jo(14, T), jo(17, T), jo(33, T), jo(4, T), jo(5, T), jo(55, T),
                   jo(56, T), jo(57, T)),
        "2-3": " — 모범규준 조: 전체(존속기한 연장 예고)",
        "2-4": " — 모범규준 조: %s(원문이 든 「제9조제1항제1호」·「제9조제6항제5호」) ; 전체(「리스크」→「위험」 용어 정비)" % jo(9, T),
        "2-5": " — 모범규준 조: 전체(개정 통보·명칭 변경)",
        "2-6": " — 모범규준 조: 전체(존속기한 연장 예고)",
        "2-7": " — 모범규준 조: 전체(존속기한 연장 통보)",
    }
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if ln.startswith("### "):
            sub = ln
            m = re.match(r"^### 제(\d+)조\(", ln)
            art = int(m.group(1)) if m else ("부칙" if ln.startswith("### 부칙") else None)
            continue
        m = re.match(r"^\[금융감독원 보도자료 · \S+ · 첨부 `([^`]+)`", ln)
        if m:
            p = PRESS[m.group(1)][0]
            new = ln.replace("· 수집 2026-10-07]", "· %s]" % kst(fa(p)))
            no = sub.split()[1]
            new = re.sub(r" — 모범규준 조: .*$", "", new) + tag2[no]
            put(i, new, "%s 인용 머리(수집 시각·모범규준 조)" % no)
            continue
        m = re.match(r"^\[금융감독원 금융행정지도 · \S+ · 화면 본문 · 수집 2026-10-07 · 원본 `([^`]+)`", ln)
        if m:
            p = os.path.join(D, m.group(1))
            new = ln.replace("· 수집 2026-10-07 ·", "· %s ·" % kst(fa(p)))
            no = sub.split()[1]
            new = re.sub(r" — 모범규준 조: .*$", "", new) + tag2[no]
            put(i, new, "%s 인용 머리(수집 시각·모범규준 조)" % no)
            continue
        if sec.startswith("## 3.") and ln.startswith("[금감원 행정지도 내역 2014-017(감총그룹-388) 첨부") and "fetched_at" not in ln:
            put(i, ln.replace("· 조 제목 · 수집 2026-10-07]", "· 조 제목 · %s · 원본 `%s`]" % (kst(fa(F2016)), os.path.basename(F2016))),
                "3장 표 머리(수집 시각·원본)")
            continue
        if sec.startswith(("## 5.", "## 6.")) and ln.startswith("[금감원 행정지도") and "· 전문 · 수집 2026-10-07 ·" in ln:
            p = F2016 if sec.startswith("## 5.") else F2012
            new = ln.replace("· 전문 · 수집 2026-10-07 ·", "· 전문 · %s ·" % kst(fa(p)))
            new = new[:-1] + " · 원본 `%s`] — 모범규준 조: 전체(%s~%s·부칙)" % (os.path.basename(p), jo(1, T), jo(59, T))
            put(i, new, "%s 전문 머리(수집 시각·원본·조)" % sec[3:5].strip("."))
            continue
        if sec.startswith("## 4."):
            m = re.match(r"^(2012\.3\.13 제정판|2016\.7 개정 예고안|2016\.8\.1 판)(?: \[`[^`]+`\])?$", ln)
            if m:
                p, doc, url = VER[m.group(1)]
                where = "제%d조" % art if isinstance(art, int) else "부칙"
                new = "%s [%s · %s · %s · %s · 원본 `%s` sha256 %s]" % (m.group(1), doc, url, where, kst(fa(p)), os.path.basename(p),
                                                                    meta(p)["sha256"][:16])
                put(i, new, "4장 %s %s 인용 머리(문서명·URL·조문·수집일)" % (where, m.group(1)))
                continue
        if sec.startswith("## 7.") and ln.startswith("[") and "`dart_out/text/" in ln:
            new = ln
            path = re.search(r"`(dart_out/text/[^`]+)`", ln).group(1)
            if "연차보고서__" in path:
                fn = os.path.basename(path).split("__", 1)[1].replace(".txt", ".pdf")
                row = next(r for r in read_csv(ANNUAL_LIST) if r["파일명"] == fn)
                if "수집 %s" % row["fetched_at"] not in new:
                    new = new.replace("· 수집(텍스트화) 8차]", "· 원본 PDF 수집 %s(`handoff/연차보고서_파일목록.csv`, sha256 %s) · 텍스트화 8차]"
                                      % (row["fetched_at"], row["sha256"][:16]))
            elif "20260318000826" in path:
                dr = next(r for r in read_csv(DART_LISTS[0]) if r["rcept_no"] == "20260318000826")
                new = new.replace("· 수집(텍스트화) 8차]", "· 원본 DART 문서 수집 %s(`dart_out/risk8/DART_문서목록.csv`) · 텍스트화 8차]"
                                  % dr["document_at"])
            elif "20181108000394" in path and "DART_문서목록" not in new:
                new = new.replace("· 수집(텍스트화) 8차]", "· 원본 `dart_out/doc/20181108000394/본문.pdf`(8차 2차 수집 본문 zip 복원, "
                                                      "`dart_out/risk8/DART_문서목록.csv` — 수집 시각 기록 없음) · 텍스트화 8차]")
            new = new.replace("쪽 p.16  · 줄 405-409", "쪽 p.16 (인쇄 쪽 14) · 줄 405-410")
            new = new.replace("(인쇄 「Page 787」 다음 쪽)", "(인쇄 「Page 788」 — 그 쪽 바닥글)")
            new = new.replace("쪽 p.89  · 줄 2931-2934", "쪽 p.89 (인쇄 쪽 번호 텍스트에 없음) · 줄 2931-2934")
            tags = {
                "모범규준 조: 7·9·14·19·37조(판단)": None,
                "모범규준 조: 연혁(전체)": "모범규준 조: 전체(연혁 — KB 리스크관리규정 2012.5.30 개정이 이 모범규준 제정을 반영)",
                "모범규준 조: 7조②·12조(판단)": "모범규준 조: (판단) %s②·%s" % (jo(7, T), jo(12, T)),
                "모범규준 조: 4·5조": "모범규준 조: %s·%s(지시서 9-4-3 의 조 번호)" % (jo(4, T), jo(5, T)),
                "모범규준 조: 9조⑦·56~58조(판단)": "모범규준 조: %s⑦·%s(지시서 9-4-1 의 조 번호) ; (판단) %s·%s·%s" % (
                    jo(9, T), jo(57, T), jo(56, T), jo(58, T), jo(25, T)),
            }
            for o, nw in tags.items():
                if new.endswith(o):
                    if nw is None:
                        box = "본문 옆 상자글" in new
                        nw = "모범규준 조: (판단) %s" % (J(7, 9, 14, 19, 37) if box else J(7, 9, 13, 14, 19, 37))
                    new = new[:-len(o)] + nw
            put(i, new, "7장 인용 머리(%s)" % os.path.basename(path)[:30])
    # (3) 신한 p.16 인용 — 문장 끝까지(줄 410)
    for i, ln in enumerate(lines):
        if ln.startswith("[신한금융지주 「2025 지배구조 및 보수체계 연차보고서」") and "줄 405-410" in ln:
            j = i + 2
            assert lines[j] == "```text"
            k = j + 1
            while not lines[k].startswith("```"):
                k += 1
            src = read(os.path.join(T8, "연차보고서__신한금융지주_지배구조연차보고서_2026.txt")).split("\n")
            want = src[404:410]
            assert not any(x.startswith("=== p.") for x in want)
            if lines[j + 1:k] != want:
                old = "\n".join(lines[j + 1:k])
                lines[j + 1:k] = want
                if ("7장 신한 p.16 인용 줄 405-409 → 405-410", old) not in seen:
                    log.append(dict(무엇="7장 신한 p.16 인용 줄 405-409 → 405-410", 줄=j + 2, 전=old.split("\n")[-1],
                                    후=want[-1], 차이="문장 중간(「그룹리스크협의회는 2009년 11월부터」)에서 끊긴 인용을 문장 끝 줄 410 「%s」까지 늘림" % want[-1].strip()))
            break
    # (4) note·표의 「…」 조각 — 원문과 다른 것
    rep = [
        ("「제9조제6항제5호 삭제」라고 적었으나", "「…모범규준 규정(제9조제6항제5호) 삭제」라고 적었으나", "2장 note 「…」 조각을 원문(2-4 화면) 글자대로"),
        ("| 2016.7 예고 「제9조제6항제5호 삭제」 ↔", "| 2016.7 예고 「…모범규준 규정(제9조제6항제5호) 삭제」 ↔", "9장 표 「…」 조각을 원문(2-4 화면) 글자대로"),
        ("「모범규준 상 경영관리협의회 / 위험관리협의회」", "「모범규준 상 경영관리협의회」·「모범규준 상 위험관리협의회」", "7장 note 「…」 조각을 원문 두 곳 글자대로"),
        ("지시서 「iM 28조(통합리스크관리시스템), 30조(적합성 검증)」", "지시서(iM 그룹 리스크관리규정) 「28조(통합리스크관리시스템), 30조(적합성 검증)」",
         "9장 표 지시서 인용 조각을 지시서 글자대로"),
    ]
    for o, nw, what in rep:
        for i, ln in enumerate(lines):
            if o in ln:
                put(i, ln.replace(o, nw), what)
    notes_add = [
        ("note: 상자글 「나. 그룹리스크관리위원회」의", " 검증(2026-10-07) (판단): 첫 인용(리스크관리 개요)의 i)~iii) 업무(그룹 표준리스크 측정기준, 그룹 위험자본 및 "
         "리스크 한도, 리스크 수반 중요 결정 검토)는 %s②1·3호와 %s에 맞아 첫 인용 머리에 13조를 더함." % (jo(13, T), jo(19, T)), "7장 note 판단 덧붙임(13조)"),
        ("note: 메리츠 인용 「그룹리스크관리규정 제9조 7항」", " 검증(2026-10-07) (판단): 「유동성 관리현황」은 %s 쪽 내용이라 메리츠 인용 머리에 25조를 더하고, "
         "지시서가 든 9조 7항·57조는 지시서 조 번호로 적음." % jo(25, T), "7장 note 판단 덧붙임(25조)"),
    ]
    for key, add_, what in notes_add:
        for i, ln in enumerate(lines):
            if ln.startswith(key) and "검증(2026-10-07) (판단)" not in ln:
                put(i, ln + add_, what)
    # (5) 2-3 뒤 note — seqno=1
    v1, v29 = view_text("fss/admnPrvntc_view_1.html"), view_text("fss/admnPrvntc_view_29.html")
    body = lambda t: ns(t[t.index("첨부파일"):t.index("목록\n행정지도에 대한 의견제출")])  # noqa: E731
    same = body(v1) == body(v29)
    i23 = next(i for i, ln in enumerate(lines) if ln.startswith("### 2-3 "))
    i24 = next(i for i, ln in enumerate(lines) if ln.startswith("### 2-4 "))
    old_notes = [k for k in range(i23, i24) if lines[k].startswith("note: 검증(2026-10-07): 같은 기간(2016-01-12")]
    for k in reversed(old_notes[1:]):                               # 앞 실행에서 두 번 들어간 것 지움(한 벌만 둠)
        del lines[k:k + 2]
    i24 = next(i for i, ln in enumerate(lines) if ln.startswith("### 2-4 "))
    if same and not old_notes:
        note = ("note: 검증(2026-10-07): 같은 기간(2016-01-12 ~ 2016-02-01)의 행정지도 예고 seqno=1 게시글(원본 `fss/admnPrvntc_view_1.html`, "
                "원 수집 때 받아 둠)은 제목이 「「금융지주회사 통합리스크관리 모범규준」존속기한 연장」(끝에 「예고」 없음)이고, 「첨부파일」부터 「목록」 앞까지의 "
                "화면 글이 seqno=29 와 같음(공백 무시 대조, 스크립트) — 따로 옮기지 않음.")
        lines[i24:i24] = [note, ""]
        log.append(dict(무엇="2-3 뒤 note 추가(seqno=1 게시글)", 줄=i24 + 1, 전="(없음)", 후=note, 차이="채움"))
    # (6) 9장 표 — 조 칸 제목·빠진 「받지 못한 것」 행·반박 시도
    cellmap = {
        "3~58조 전부": "%s~%s 전부" % (jo(3, T), jo(58, T)),
        "3~58조 전부(9·11조 옛 문구)": "%s~%s 전부(%s·%s 옛 문구)" % (jo(3, T), jo(58, T), jo(9, T), jo(11, T)),
        "4·5·7·9·11조 등": J(4, 5, 7, 9, 11, 47),
        "1~59조": "%s~%s" % (jo(1, T), jo(59, T)),
        "4·5·7·9·12·14·19·37조(판단)": "%s(지시서 9-4-3) ; (판단) %s" % (J(4, 5), J(7, 9, 12, 13, 14, 19, 37)),
        "59조": jo(59, T), "9조": jo(9, T), "11조": jo(11, T), "4·5·7조": J(4, 5, 7), "7·12조": J(7, 12),
        "28·30조": J(28, 30), "7·9·14·19·37조": "(판단) " + J(7, 9, 13, 14, 19, 37),
    }
    i9 = next(i for i, ln in enumerate(lines) if ln.startswith("## 9."))
    for i in range(i9, len(lines)):
        ln = lines[i]
        if not ln.startswith("| ") or ln.startswith(("| 구분", "|---")):
            continue
        cells = ln.strip().strip("|").split("|")
        last = cells[-1].strip()
        if last in cellmap:
            cells[-1] = " %s " % cellmap[last]
            put(i, "|" + "|".join(cells) + "|", "9장 표 조 칸(조 제목)")
    add = [("| 받지 못한 것 | 법제처 행정규칙으로 등록된 모범규준 |", "| 받지 못한 것 | 법제처 행정규칙으로 등록된 모범규준 | 법제처 Open API lawSearch "
            "target=admrul nw=1·2, 질의 모범규준·통합위험관리·통합리스크관리·리스크관리 모범규준·위험관리 모범규준 0건(8-2) — 추출 범위에 없음 | — |"),
           ("| 받지 못한 것 | 조 번호를 들어 이 모범규준을 인용한 공시 문장", "| 받지 못한 것 | 조 번호를 들어 이 모범규준을 인용한 공시 문장(「모범규준 제N조」 꼴)·"
            "학술·용역 보고서의 조문 인용 | risk8·risk9 텍스트 전수 검색(7장 note), KIRI docId=3403·KCMI fid=4882 텍스트 검색(8-2) — 추출 범위에 없음 | — |")]
    last_ng = max(i for i in range(i9, len(lines)) if lines[i].startswith("| 받지 못한 것"))
    for k, (key, row) in enumerate(add):
        if not any(ln.startswith(key) for ln in lines):
            lines.insert(last_ng + 1 + k, row)
            log.append(dict(무엇="9장 표 「받지 못한 것」 행 채움", 줄=last_ng + 2 + k, 전="(없음 — 수집 보고 not_got 에만 있었음)", 후=row, 차이="채움"))
    for c in claims:
        tag = "검증(2026-10-07) 반박 시도[%s]: %s → %s%s" % (
            c["id"], " ; ".join(c["검색"]), c["결과"], ("(추출 범위에 없음 유지 — %s)" % c["요약"]) if c["결과"] != "반박 성공" else
            " — 찾은 것: %s" % " ; ".join(c["찾은것"]))
        for i, ln in enumerate(lines):
            if ln.startswith(c["고리"]) and "반박 시도[%s]" % c["id"] not in ln:
                cells = ln.rstrip().rstrip("|").split("|")
                # 표 행: 끝에서 둘째 칸(출처·근거 / 결과)에 덧붙임
                cells[-2 if c["고리"].startswith("| 받지") else -1] = cells[-2 if c["고리"].startswith("| 받지") else -1].rstrip() + " ; " + tag + " "
                put(i, "|".join(cells) + "|", "반박 시도[%s] 기록" % c["id"])
                break
    ptr = [("note: 같은 관리번호 2014-017 의 두 기록이 폐지일자를 다르게 적음", "N3"),
           ("note: 조문 번호를 들어 이 모범규준을 인용한 공시 문장", "N6"),
           ("| 학술·용역 보고서·지주사 연차보고서의 조문 인용 |", "N6")]
    for key, cid in ptr:
        for i, ln in enumerate(lines):
            if ln.startswith(key) and "반박 시도[%s]" % cid not in ln:
                s_ = " (검증(2026-10-07) 반박 시도[%s] — 9장 표 「받지 못한 것」 행)" % cid
                put(i, ln[:-2] + s_ + " |" if ln.endswith(" |") else ln + s_, "반박 시도[%s] 가리킴" % cid)
    # (7) 3장 표 본문표시 칸 ← CSV(아래 (8) 에서 고친 값)
    a16, _ = rule(F2016)
    i3 = next(i for i, ln in enumerate(lines) if ln.startswith("## 3."))
    for i in range(i3, i9):
        m = re.match(r"^\| (\d+) \|", lines[i])
        if m:
            n = int(m.group(1))
            cells = lines[i].split("|")
            mk = mark_with_pos(a16[n]) or "-"
            if cells[6].strip() != mk:
                cells[6] = " %s " % mk
                put(i, "|".join(cells), "3장 표 본문 표시 칸(자리 덧붙임)")
    # (8) CSV — 본문표시 자리, 출처 URL·수집 시각
    rows = read_csv(JO_CSV)
    cols = list(rows[0].keys())
    src = ("2016.8.1판: 금감원 행정지도 내역 관리번호 2014-017(문서번호 감총그룹-388, 시행일 20160801) 첨부 「붙임2_금융지주회사 통합위험관리 모범규준 "
           "개정 후 전문.hwp」 %s sha256 %s fetched_at %s ; 2012.3.13 제정판 제목은 금감원 행정지도 예고(seqno=29) 첨부 「통합리스크관리_모범규준(게시)F_.hwp」 "
           "%s sha256 %s fetched_at %s ; 2016.7 개정 예고안 제목은 금감원 행정지도 예고(seqno=51) 첨부 「…개정안(홈피공시).hwp」 %s sha256 %s "
           "fetched_at %s ; 조 머리 대조 scripts/dart/verify13_mobeom.py(2026-10-07)" % (
               ADMV % "20170210165649943", meta(F2016)["sha256"][:16], fa(F2016), PRVV % "29", meta(F2012)["sha256"][:16], fa(F2012),
               PRVV % "51", meta(F2016P)["sha256"][:16], fa(F2016P)))
    changed = []
    for r in rows:
        n = int(r["조"])
        mk = mark_with_pos(a16[n])
        if r["2016.8.1판_본문표시"] != mk:
            changed.append(("CSV %d조 2016.8.1판_본문표시" % n, r["2016.8.1판_본문표시"], mk))
            r["2016.8.1판_본문표시"] = mk
        if r["출처"] != src:
            if n == 1:
                changed.append(("CSV 1~59조 출처(59행 같은 글)", r["출처"], src))
            r["출처"] = src
    if changed:
        with open(JO_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        for what, o, nw in changed:
            if (what, o) not in seen:
                log.append(dict(무엇=what, 줄=0, 전=o, 후=nw, 차이=_diff(o, nw)))
    # (9) 10장 — 지시서 항목별 대조
    tmp = lines + [""]
    L5 = lambda n: art_line(tmp, n)  # noqa: E731
    i5 = next(i for i, ln in enumerate(tmp, 1) if ln.startswith("## 5."))
    i6 = next(i for i, ln in enumerate(tmp, 1) if ln.startswith("## 6."))
    sec10 = [SEC10_HEAD, "",
             "지시서(사용자 지시서 REQUEST13 「9-4 타사 그룹리스크관리규정(모범규준 조항과 맞대기)」와 「배경」·「끝에 낼 것」) 가운데 이 파일(모범규준 원문 쪽)에 "
             "닿는 항목마다 받은 글 자리를 적었다. 「md N줄」은 5장 전문 코드 블록 안 그 조의 머리 줄. 타사 규정·서술 쪽은 9-4 회사별 md 몫. "
             "지시서에 적힌 조 번호는 그대로, 더 붙인 조는 「(판단)」.", "",
             "| 지시서 항목 | 지시서 원문(그대로) | 모범규준 조(조 제목) | 이 파일의 받은 글 | 상태 |", "|---|---|---|---|---|"]
    for key, srcq, arts, where, st in REQ_ITEMS:
        if len(arts) >= 10:
            jcell = "%s~%s" % (jo(arts[0], T), jo(arts[-1], T))
            got = "5장 전문(md %d~%d줄)·3장 표·`%s`" % (i5, i6 - 1, JO_CSV) if key == "배경" else "3장 표(1~59조, 장·절·2012판 제목)·`%s`" % JO_CSV
        elif arts:
            mk = {9: "⑦"} if key == "9-4-1 메리츠" else {}
            jcell = "·".join(jo(n_, T) + mk.get(n_, "") for n_ in arts)
            ex = REQ_EXTRA.get(key)
            if ex:
                jcell += " ; (판단) " + "·".join(jo(n_, T) + {18: "③ 단서", 36: " 단서", 52: "③"}.get(n_, "") for n_ in ex)
            got = "5장 " + " · ".join("%s md %d줄" % (jo(n, T), L5(n)) for n in arts)
            if key == "9-4-1 iM":
                got += " (제4장 「제3절 그룹위험관리시스템 구축 및 관리」·「제4절 적합성 검증」 아래)"
            if key == "9-4-1 메리츠":
                got += " ; 7장 메리츠 연차보고서 p.89 인용(「그룹리스크관리규정 제9조 7항」·「제57조, 제58조」)"
            if key == "9-4-3":
                got += " ; 4장 판 대조(2012·2016.7·2016.8.1) ; 7장 신한 연차보고서 p.160·사업보고서 p.792(신한 자체 규준 문구)"
            if ex:
                got += " ; (판단) " + " · ".join("%s md %d줄" % (jo(n, T), L5(n)) for n in ex)
        else:
            jcell = "—"
            got = "9장 표" if key == "끝 표" else "2장·7장 인용 머리 「모범규준 조:」, 3장 표, 9장·10장 표"
        state = {"받은 글": "받은 글(모범규준 원문)" + ("" if key in ("배경", "9-4-1 목차") else " — 타사 쪽은 9-4 회사별 md"),
                 "있음": "있음"}[st]
        if key == "9-4-1 iM":
            state += " ; 지시서 제목(통합리스크관리시스템·적합성 검증)과 모범규준 조 제목이 다름(9장)"
        if key == "9-4-2 55":
            state += " ; 지표 목록·발령 단계 수·이름은 모범규준 글에 없음(55조②는 「조기경보 발령에 따른 대응방안」, 52조③은 「위기상황단계」)"
        sec10.append("| %s | 「%s」 | %s | %s | %s |" % (key, srcq, jcell, got, state))
    sec10 += ["", "note: 9-4-2 「3조」의 (판단) 18조③·36조 단서, 「55조」의 (판단) 52조③, 9-4-1 메리츠의 (판단) 56조는 3장 note 와 같은 판단(조 제목은 CSV).", ""]
    lines = lines + [""] + sec10
    changed_ = True                                                  # 앞 실행의 보정을 다시 고친 사슬(전→중→후)은 한 줄로 합침
    while changed_:
        changed_ = False
        for x in log:
            nxt = next((y for y in log if y is not x and y["무엇"] == x["무엇"] and y["전"] == x["후"]), None)
            if nxt:
                x["후"] = nxt["후"]
                log.remove(nxt)
                changed_ = True
                break
    uniq, keys = [], set()
    for x in log:
        if (x["무엇"], x["후"]) not in keys:
            keys.add((x["무엇"], x["후"]))
            uniq.append(x)
    log[:] = uniq
    for x in log:
        if x["차이"] != "채움" and not x["무엇"].startswith("7장 신한 p.16"):
            x["차이"] = _diff(x["전"], x["후"])
    for x in log:                                                    # 줄 번호는 마지막 md 기준으로 다시 셈
        if x["줄"] and "\n" not in x["후"]:
            x["줄"] = next((k + 1 for k, ln in enumerate(lines) if ln == x["후"]),
                          next((k + 1 for k, ln in enumerate(lines) if ln.startswith(x["후"][:40])), x["줄"]))
    with open(FIXLOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    # (10) 검증 기록 — 대조를 돌려 결과를 넣고, 그 기록을 넣은 md 로 한 번 더 대조
    with open(MD, "w", encoding="utf-8") as f:                       # 1차: 검증 기록 자리만(대조가 읽을 md)
        f.write("\n".join(lines + ["", VERIFY_HEAD, ""]) + "\n")
    for _ in range(2):                                               # 2·3차: 대조 결과를 넣은 기록 → 그 md 로 다시 대조
        sec = verify_section(log, claims)
        with open(MD, "w", encoding="utf-8") as f:
            f.write("\n".join(lines + [""] + sec) + "\n")
        _C.clear()


def verify_section(log, claims):
    R, st = run_checks()
    ngs = [x for x in R.ngs if "검증 기록" not in x]
    blocks = st["blocks"]
    kinds = {}
    for b in blocks:
        h = b["head"]
        k = ("보도자료 hwp" if "보도자료 ·" in h else "행정지도 화면" if "금융행정지도 ·" in h else
             "판별 조문·부칙(4장)" if re.match(r"^(2012\.3\.13|2016\.7|2016\.8\.1)", h) else "전문(5·6장)" if "· 전문 ·" in h else
             "로컬 공시 텍스트(7장)" if "dart_out/text/" in h else "기타")
        kinds[k] = kinds.get(k, 0) + 1
    tot, nf = st["inline"]
    out = [VERIFY_HEAD, "",
           "- 스크립트: `scripts/dart/verify13_mobeom.py` — `refute`(같은 출처에서 더 넓은 검색어로 다시 찾기, 받은 원본 `%s/`, 요청기록 `%s/_요청기록.csv`, "
           "법제처 원장 `%s/law/_call_log.csv`(OC=***)) → `fix`(이 절과 아래 고친 곳) → 인자 없이 대조(결과 `%s`)." % (VD, VD, VD, OUT_TXT),
           "- 대조한 인용: 코드 블록 %d개(%s) — 전부 원문과 같음(공백만 무시; 전문 2개·로컬 7개는 글자까지 같음). 「[생략: …]」 자리는 원본에서 담당 직원 "
           "이름·연락처 줄만 빠졌는지 글자 수로 확인(내용은 적지 않음). hwp 6개는 sha256 = .meta.json, `hwp2md.py` 를 다시 돌린 결과와 변환본이 바이트까지 같고, "
           "hwp 미리보기 글(PrvText) 조각이 변환본에 모두 있음." % (len(blocks), ", ".join("%s %d" % kv for kv in sorted(kinds.items()))),
           "- note·표 줄의 「…」 조각 %d개를 원본 글과 대조 — 원문과 다르게 옮긴 3곳(+같은 글 1곳)을 원문 글자대로 고침(아래). 원본에서 못 찾은 나머지 %d개는 "
           "표 이름·검색어·스크립트 표기·다른 사이트 이름(대상 아님) 등이라 그대로 둠(결과 파일 「참고」 절에 목록)." % (tot, max(0, len(nf))),
           "- 조 목록 CSV 재확인: 2016.8.1 판 변환본의 조 머리 1~59조 — 시트 범위 3~58조 56개 포함 — 와 번호·제목·장·절이 하나도 빠짐없이 같음. 삭제·개정 표시: "
           "9조 「<개정 2016. 8. 1.>」(①), 11조 「<삭제 2016. 8. 1.>」(①~⑤·⑦ — ⑥·⑧·⑨ 존치, 조 전체 삭제 아님), 59조 「<삭제 2016. 3. 28.>」(조 전체, "
           "장 머리 「제 7 장 보칙<삭제 2016. 3. 28.>」) — 자리를 CSV·3장 표에 덧붙임. 원문 38조 머리는 「제38조 (기본 원칙)」(조와 괄호 사이 띄어 씀). "
           "CSV 장 칸은 원문 「제 1 장  총 칙」을 「제1장 총 칙」으로 공백만 줄인 꼴. 2016.7 예고안 제목은 59조 모두 2016.8.1 판과 같음.",
           "- 2012.3.13 제정판 ↔ 2016.8.1 판 제목이 다른 조 %d개(전부 「리스크」→「위험」 용어 바꿈, 번호·순서는 같음): %s." % (
               len(st["chg"]), " ; ".join("%d조 %s→%s" % c for c in st["chg"])),
           "", "### 고친 곳(전 → 후)", ""]
    g4 = [x for x in log if x["무엇"].startswith("4장 ")]
    rf_ = [x for x in log if x["무엇"].startswith("반박 시도[")]
    for x in log:
        if x in g4 or x in rf_:
            continue
        if x["차이"] == "채움":
            out.append("- %s (md %s줄): 채움 — 「%s」" % (x["무엇"], x["줄"] or "—", x["후"][:200] + ("…" if len(x["후"]) > 200 else "")))
        elif x["무엇"].startswith("CSV 1~59조 출처"):
            out.append("- %s: 원래 글은 그대로 두고 앞에 「2016.8.1판: 」, 뒤에 게시 URL·sha256·fetched_at 과 2012 제정판·2016.7 예고안 출처(URL·sha256·"
                       "fetched_at)·대조 스크립트를 덧붙임. 전 「%s」" % (x["무엇"], x["전"]))
        else:
            out.append("- %s (md %s줄): %s" % (x["무엇"], x["줄"] or "—", _diff(x["전"], x["후"])))
    if g4:
        ex = g4[0]
        out.append("- 4장 판별 조문·부칙 인용 머리 %d곳(md %s줄): 판 이름 + 원본 파일 이름만 있던 머리(부칙 3곳은 판 이름만)에 문서명·게시 URL·조문(제N조/부칙)·"
                   "수집 시각·sha256 을 넣음. 예) 전 「%s」 → 후 「%s」" % (len(g4), ", ".join(str(x["줄"]) for x in g4), ex["전"], ex["후"]))
    if rf_:
        out.append("- 「추출 범위에 없음」 행·줄 %d곳(md %s줄): 그 칸 끝에 「검증(2026-10-07) 반박 시도[N…]: 쓴 검색어 → 결과」를 덧붙임(글은 그 자리, 요약은 아래)." % (
            len(rf_), ", ".join(str(x["줄"]) for x in rf_)))
    out += ["", "### 채운 항목", "",
            "- 10장 「지시서 항목별 대조」(지시서 9-4 항목·배경·끝에 낼 것 14행 — 모범규준 조(조 제목)·5장 줄 번호·상태).",
            "- 9장 「받지 못한 것」에 빠져 있던 2행(법제처 행정규칙 등록, 조 번호 인용 공시 문장 — 수집 보고 not_got 에만 있었음).",
            "- 2장 인용 머리 7곳·7장 인용 머리 7곳에 「모범규준 조: N조(제목)」, 4장 인용 머리 %d곳에 문서명·게시 URL·조문·수집 시각, 9장 표 조 칸에 조 제목." % len(g4),
            "- 지시서 항목마다 받은 글이 있음(10장) — 「추출 범위에 없음」으로 남은 지시서 항목은 없음(이 파일 범위). 타사 규정·서술은 9-4 회사별 md 몫.",
            "", "### 「추출 범위에 없음」 반박 시도", ""]
    for c in claims:
        out.append("- [%s] %s — %s. %s. (쓴 검색어·건수는 md 의 「반박 시도[%s]」 자리)" % (c["id"], c["대상"], c["결과"], c["요약"], c["id"]))
    ok_ = [c for c in claims if c["결과"] == "반박 성공"]
    out += ["", "반박 성공 %d건, 반박 실패 %d건, 반박 시도 안 함 %d건(robots·403·방화벽 — 우회 금지)." % (
        len(ok_), sum(c["결과"] == "반박 실패" for c in claims), sum(c["결과"].startswith("반박 시도 안 함") for c in claims)), "",
            "### 남은 문제", ""]
    if ngs:
        out += ["- 대조 문제 %d건: %s" % (len(ngs), " ; ".join(ngs[:20]))]
    else:
        out += ["- 대조 문제 0건(`python3 scripts/dart/verify13_mobeom.py` exit 0)."]
    out += ["- 2016.3.28 개정 공문·신구대비표, 2012.3.13 제정 송부 공문, 2018.3.31 이후 연장 기록은 넓혀 찾아도 추출 범위에 없음 — 폐지 시점은 판단으로 남음(2장 note).",
            "- 이 md 는 `scripts/dart/web13_mobeom.py build` 로 다시 만들면 검증 보정이 사라짐 — 다시 만들면 `verify13_mobeom.py fix` 를 다시 돌릴 것.",
            "- 7장 인용 머리의 인쇄 쪽: 메리츠 연차보고서 p.89 는 텍스트에 인쇄 쪽 번호가 없어 적지 못함."]
    return out



def main(argv):
    mode = argv[1] if len(argv) > 1 else "check"
    if mode == "refute":
        refute()
        return 0
    if mode == "fix":
        fix()
    R, st = run_checks()
    write_report(R, mode)
    print("문제 %d, 통과 %d → %s" % (R.n_ng, R.n_ok, OUT_TXT))
    for s in R.ngs[:40]:
        print("  NG", s[:200])
    return 0 if R.n_ng == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
