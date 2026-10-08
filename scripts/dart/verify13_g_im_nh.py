# -*- coding: utf-8 -*-
"""13차 9-4 iM금융지주·NH농협금융지주 산출물 검증·보정.

    python3 scripts/dart/verify13_g_im_nh.py          # 대조만 — 결과 dart_out/risk13/verify13_g_im_nh.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_g_im_nh.py refute   # 「추출 범위에 없음」 반박 시도(같은 출처 + risk9 다른 기간 정기보고서, 더 넓은 검색어)
                                                      #   결과 dart_out/raw/web13/verify13_g_im_nh/refute_hits.json (요약만 출력)
    python3 scripts/dart/verify13_g_im_nh.py fix      # 보정(멱등: 검증 전 사본 pre/ 에서 다시 만듦) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-4_iM금융지주.md, 9-4_NH농협금융지주.md,
      dart_out/risk13/9-4_iM금융지주_조문목차.csv, 9-4_NH농협금융지주_조문목차.csv.
검증 전 사본: dart_out/raw/web13/verify13_g_im_nh/pre/ (커밋 8c118c8 의 파일 그대로 — 없으면 git show 로 다시 만듦).
      원 생성기 scripts/dart/web13_g_im_nh.py 는 고치지도 import 하지도 않는다(다시 돌리면 보정이 지워지므로 돌리지 말 것).
원문(읽기만): dart_out/text/risk8/ (연차보고서 본공시·추가공시, 사업보고서 원본·정정, 경영공시 — 쪽 표지 「=== p.N ===」),
      dart_out/text/risk9/<접수번호>.txt (DART 정기보고서 — 같은 회사 다른 기간 판, 반박 검색에만),
      메타 dart_out/risk8/텍스트목록.csv·handoff/연차보고서_파일목록.csv·dart_out/doc/<접수번호>/_파일목록.json·
      dart_out/raw/risk8/경영공시/<회사>/meta.json·dart_out/risk9/텍스트목록.csv,
      모범규준 조 목록 dart_out/risk13/모범규준_조목록.csv(2016.8.1 판 제목), 모범규준 원문 handoff/13차_산출물/9-4_모범규준_원문.md.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만).

대조(인자 없이):
  1. md 의 원문 인용(코드 블록·「>」 블록) 전부를 「- 인용:」 줄이 가리킨 문서·쪽의 텍스트와 대조 — ① 줄 그대로(「[표 깨짐: …]」 등
     이 작업이 끼운 표시 줄만 빼고 원본 줄과 글자 그대로 같은지), ② 공백만 무시하고 같은지. 찾은 자리의 쪽이 표기한 쪽과 같은지,
     인쇄 쪽(연차보고서 쪽 머리 번호)·DART 쪽이 맞는지, 문서명·접수번호·URL·방식·원본 수집일·옮김 날짜가 메타와 같은지,
     「· 리스크관리규정 제N조~제M조」 같은 조문 표기가 인용 글의 조 머리와 맞는지.
  2. 「추가공시·정정판 대조」 줄을 다시 계산해 같은지. 0-1 문서 표의 sha256·쪽수·원본 수집 시각.
  3. 조문 목차 CSV — 전문 옮긴 규정은 원문 쪽마다 조·장 머리(삭제 조·「제N조의M」·부칙 조 포함)를 다시 뽑아 CSV 와 하나씩 맞댐
     (빠진 조·남는 조·제목·쪽). 이름만 있는 행은 그 이름이 적힌 쪽에 있는지. md 1-2·1-4 표와 CSV 가 같은지.
  4. 「…」 조각(note·표·판정 줄) — 회사 원문·모범규준 원문·지시서에 공백 무시로 있는지(허용 목록 밖에서 못 찾으면 문제).
  5. 모범규준 조 표기 — 인용마다 「이 글이 닿는 모범규준 조」 줄, 3장 조별 머리, 0장·5장 표의 조 번호에 「N조(조 제목)」이 붙었는지,
     제목이 모범규준_조목록.csv(2016.8.1판)와 같은지, 지시서에 없는 조 번호에 「(판단)」이 붙었는지.
  6. 지시서(REQUEST13) 9-4 항목마다 「7. 지시서 항목별 대조」 표에 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」이 있는지,
     가리킨 인용 번호가 md 에 있는지.
  7. 「추출 범위에 없음」 줄마다 찾은 방법(검색어·범위 또는 그 자리를 가리키는 말)이 있는지, 반박 검색 결과의 조가 검증 기록에 있는지.
  8. 인증값(DART 키·법제처 OC) 문자열 없음, 산출 폴더에 PDF 없음, 맨 끝 「## 검증 기록(2026-10-07)」 절이 하나.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

TODAY = "2026-10-07"
TXT8 = os.path.join("dart_out", "text", "risk8")
TXT9 = os.path.join("dart_out", "text", "risk9")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
VD = os.path.join("dart_out", "raw", "web13", "verify13_g_im_nh")
PRE = os.path.join(VD, "pre")
PRE_COMMIT = "8c118c8"
OUT_TXT = os.path.join(WORK, "verify13_g_im_nh.txt")
REFUTE_JSON = os.path.join(VD, "refute_hits.json")
CHECK_JSON = os.path.join(VD, "check_detail.json")
FIX_JSON = os.path.join(VD, "fix_log.json")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MOBEOM_MD = os.path.join(OUTD, "9-4_모범규준_원문.md")
REQ = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
REQ_COPY = os.path.join(VD, "REQUEST13.txt")   # 지시서 사본(스크래치가 지워져도 대조되게)
CO = {"I": "iM금융지주", "N": "NH농협금융지주"}
MD = {k: os.path.join(OUTD, f"9-4_{v}.md") for k, v in CO.items()}
TOC = {k: os.path.join(WORK, f"9-4_{v}_조문목차.csv") for k, v in CO.items()}
PAGE_RE = re.compile(r"^=== p\.(\d+) ===\s*$")
MARK_RE = re.compile(r"^\s*\[(표 깨짐|추출 깨짐|줄임|생략)[:：]")
VREC = f"## 검증 기록({TODAY})"
# 13차 정합성 보정(scripts/dart/fix13_A.py, 2026-10-08 KST)이 고친 판도 받아들임 — 대조 규칙은 그대로, 받아들이는 글만 넓힘:
#   R5 검증 기록 절 제목 KST·인용 줄 옮김 날짜 KST 라벨, R2 조 태그 줄의 「9-4 조문 대조(대조표 A~C)」 표지,
#   R1 7장 찾은 방법은 같은 행 「받은 글」 칸에서도 찾음, 검증 기록의 「### 정합성 보정」 소절은 「고친 곳」 소절처럼 조각·제목 대조에서 넘김.
VREC_OK = (VREC, "## 검증 기록(2026-10-08 KST)")
MOVED_OK = (f"옮김 {TODAY}", "옮김 2026-10-07~08(KST)", "옮김 2026-10-08(KST)")
# 지시서(REQUEST13 9-4)에 적힌 모범규준 조 번호 — 이 밖의 번호는 「(판단)」. iM 은 28·30 도 지시서에 적힘.
REQ_ARTS = {"I": {3, 4, 5, 17, 21, 22, 24, 27, 28, 30, 34, 53, 55}, "N": {3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55}}


def nows(s):
    return re.sub(r"\s+", "", s)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ───────────────────────────── 문서·메타 ─────────────────────────────
DOCS = {
    "I_AR": dict(co="iM금융지주", kind="연차보고서", file="연차보고서__iM금융지주_지배구조연차보고서_2026.txt",
                 name="iM금융지주 「2025년도 iM금융지주 지배구조 및 보수체계 연차보고서」(본공시, 공시일 2026-03-04)", printed="ar_num"),
    "I_AR_ADD": dict(co="iM금융지주", kind="연차보고서(추가공시)", file="연차보고서__iM금융지주_지배구조연차보고서_2026_추가공시.txt",
                     name="iM금융지주 「2025년도 지배구조 및 보수체계 연차보고서 추가 공시」(공시일 2026-04-14)", printed="ar_num"),
    "I_BR": dict(co="iM금융지주", kind="사업보고서", file="사업보고서__iM금융지주__20260318000971.txt",
                 name="iM금융지주 「사업보고서 (2025.12)」 원본", rcp="20260318000971", printed="br"),
    "I_BR_0720": dict(co="iM금융지주", kind="사업보고서(정정)", file="사업보고서__iM금융지주__20260515000720.txt",
                      name="iM금융지주 「[기재정정]사업보고서 (2025.12)」", rcp="20260515000720", printed="br"),
    "I_MD": dict(co="iM금융지주", kind="경영공시", file="경영공시__iM금융지주.txt",
                 name="iM금융지주 경영공시 「제16기 상반기 아이엠금융지주현황 공시」(2026년 상반기, 게시일 2026-08-31)", printed=None),
    "N_AR": dict(co="NH농협금융지주", kind="연차보고서", file="연차보고서__NH농협금융지주_지배구조연차보고서_2026.txt",
                 name="NH농협금융지주 「(공시) NH농협금융지주 2025년 지배구조 및 보수체계 연차보고서」(본공시, 공시일 2026-03-10)", printed="nh"),
    "N_AR_ADD": dict(co="NH농협금융지주", kind="연차보고서(추가공시)", file="연차보고서__NH농협금융지주_지배구조연차보고서_2026_추가공시.txt",
                     name="NH농협금융지주 「(공시) NH농협금융지주 2025년도 지배구조 및 보수체계 연차보고서 추가공시」(공시일 2026-04-15)", printed="nh"),
    "N_BR": dict(co="NH농협금융지주", kind="사업보고서", file="사업보고서__NH농협금융지주__20260331004252.txt",
                 name="NH농협금융지주 「사업보고서 (2025.12)」 원본", rcp="20260331004252", printed="br"),
    "N_MD": dict(co="NH농협금융지주", kind="경영공시", file="경영공시__NH농협금융지주.txt",
                 name="NH농협금융지주 경영공시 「2026년 상반기 NH농협금융지주현황」", printed=None),
}
for _d in DOCS.values():
    _d["path"] = os.path.join(TXT8, _d["file"])
CORR = {"I_AR": ["I_AR_ADD"], "I_BR": ["I_BR_0720"], "N_AR": ["N_AR_ADD"]}
CORR_LABEL = {"I_AR_ADD": "추가공시", "I_BR_0720": "정정 20260515000720", "N_AR_ADD": "추가공시"}
_META = {"loaded": False}


def load_meta():
    if _META["loaded"]:
        return
    _META["loaded"] = True
    tl = {r["doc_id"]: r for r in read_csv(os.path.join("dart_out", "risk8", "텍스트목록.csv"))}
    ar = {r["파일명"]: r for r in read_csv(os.path.join("handoff", "연차보고서_파일목록.csv"))}
    for k, d in DOCS.items():
        doc_id = d["file"][:-4]
        t = tl.get(doc_id, {})
        d["url"] = t.get("출처", "")
        d["src_sha"] = t.get("원본sha256", "")
        d["txt_sha_list"] = t.get("텍스트sha256", "")
        d["fetched"] = ""
        d["method"] = ""
        if d["kind"].startswith("연차보고서"):
            a = ar.get(doc_id.split("__", 1)[1] + ".pdf", {})
            d["fetched"] = a.get("fetched_at", "")
            d["method"] = a.get("방식", "")
        elif "rcp" in d:
            j = os.path.join("dart_out", "doc", d["rcp"], "_파일목록.json")
            if os.path.exists(j):
                d["fetched"] = json.load(open(j, encoding="utf-8")).get("생성시각", "")
            d["url"] = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + d["rcp"]
        else:
            j = os.path.join("dart_out", "raw", "risk8", "경영공시", d["co"], "meta.json")
            if os.path.exists(j):
                m = json.load(open(j, encoding="utf-8"))
                d["fetched"] = m.get("fetched_at", "") or m.get("수집시각", "")
                d["method"] = m.get("방식", "")
    # risk9: 같은 회사 정기보고서(다른 기간 판) — 반박 검색용
    have = {d.get("rcp") for d in DOCS.values()}
    for r in read_csv(os.path.join("dart_out", "risk9", "텍스트목록.csv")):
        if r["corp_label"] not in CO.values():
            continue
        rcp = r["rcept_no"]
        p = os.path.join(TXT9, rcp + ".txt")
        if not os.path.exists(p) or rcp in have:
            continue                                   # FY2025 판은 risk8 과 같은 텍스트(sha256 같음) — risk8 키로 씀
        fetched = ""
        j = os.path.join("dart_out", "doc", rcp, "_파일목록.json")
        if os.path.exists(j):
            fetched = json.load(open(j, encoding="utf-8")).get("생성시각", "")
        DOCS["R9_" + rcp] = dict(co=r["corp_label"], kind="정기보고서(risk9)", file=rcp + ".txt", path=p, rcp=rcp, printed="br",
                                 name=f"{r['corp_label']} 「{r['report_nm']}」", report_nm=r["report_nm"],
                                 url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rcp, src_sha=r["원본sha256"],
                                 txt_sha_list=r["텍스트sha256"], fetched=fetched, method="")


NH_HEAD = re.compile(r"^\s*(?:NH농협금융지주|2025년 지배구조 및 보수체계 연차보고서)\s*(\d{1,3})\s*$")
IM_HEAD = re.compile(r"^\s*22002255년년")


def skipline(ln):
    """정정판·추가공시 대조 때 빼는 줄(원 생성기와 같은 규칙): 쪽 표지, 쪽 번호만 있는 줄, 쪽 머리말."""
    s = ln.strip()
    return bool(PAGE_RE.match(ln) or "dart.fss.or.kr Page" in ln or re.fullmatch(r"\d{1,3}", s)
                or re.fullmatch(r"- \d+ -", s) or IM_HEAD.match(s) or NH_HEAD.match(s))


class Text:
    def __init__(self, key):
        d = DOCS[key]
        self.key = key
        self.lines = open(d["path"], encoding="utf-8").read().split("\n")
        self.page = []
        p = 0
        for ln in self.lines:
            m = PAGE_RE.match(ln)
            if m:
                p = int(m.group(1))
            self.page.append(p)
        self.npages = max(self.page) if self.page else 0
        self.printed = {}
        mode = d.get("printed")
        cur, seen = None, 0
        for ln in self.lines:
            m = PAGE_RE.match(ln)
            if m:
                cur, seen = int(m.group(1)), 0
                continue
            if cur is None:
                continue
            s = ln.strip()
            if mode == "ar_num" and seen < 3 and re.fullmatch(r"\d{1,3}", s):
                self.printed[cur] = s
            elif mode == "nh" and seen < 2 and NH_HEAD.match(s):
                self.printed[cur] = NH_HEAD.match(s).group(1)
            elif mode == "br":
                m2 = re.search(r"dart\.fss\.or\.kr Page (\d+)", s)
                if m2:
                    self.printed[cur] = m2.group(1)
            if s:
                seen += 1
        self._flat = {}

    def plabel(self, p1, p2=None):
        """원 생성기와 같은 쪽 표기: PDF 쪽, 인쇄·DART 쪽이 PDF 쪽과 하나라도 다르면 괄호로."""
        p2 = p2 or p1
        a = f"p.{p1}" if p1 == p2 else f"p.{p1}~{p2}"
        pr = [(p, self.printed.get(p)) for p in range(p1, p2 + 1) if self.printed.get(p)]
        if pr and any(str(p) != v for p, v in pr):
            vals = [v for _, v in pr]
            lab = vals[0] if len(vals) == 1 or vals[0] == vals[-1] else f"{vals[0]}~{vals[-1]}"
            a += f"({'DART 쪽' if DOCS[self.key]['printed'] == 'br' else '인쇄'} {lab})"
        return a

    def flat(self, skip=False):
        """공백 없이 이어 붙인 글과 글자별 줄 번호, 줄마다 시작 위치."""
        if skip not in self._flat:
            chars, idx, off = [], [], []
            pos = 0
            for i, ln in enumerate(self.lines):
                off.append(pos)
                if skip and skipline(ln):
                    continue
                c = re.sub(r"\s+", "", ln)
                chars.append(c)
                idx.extend([i] * len(c))
                pos += len(c)
            off.append(pos)
            self._flat[skip] = ("".join(chars), idx, off)
        return self._flat[skip]

    def page_lines(self, p1, p2=None):
        p2 = p2 or p1
        return [i for i, p in enumerate(self.page) if p1 <= p <= p2]


TEXTS = {}


def T(key):
    if key not in TEXTS:
        TEXTS[key] = Text(key)
    return TEXTS[key]


def co_keys(c, r9=True):
    load_meta()
    return [k for k, d in DOCS.items() if d["co"] == CO[c] and (r9 or not k.startswith("R9_"))]


# ───────────────────────────── 모범규준 조 목록 ─────────────────────────────
_JO = {}


def jo_titles():
    if not _JO:
        for r in read_csv(JO_CSV):
            _JO[int(r["조"])] = r["제목_2016.8.1판"]
    return _JO


def jt(n, c=None, judge=None):
    """「N조(제목)」 — c 가 주어지면 지시서에 없는 조에 「(판단)」."""
    s = f"{n}조({jo_titles()[n]})"
    if judge is None and c is not None:
        judge = n not in REQ_ARTS[c]
    return s + ("(판단)" if judge else "")


# ───────────────────────────── 반박 검색(refute) ─────────────────────────────
# 조마다 원래 검색어(수집 에이전트 6장)보다 넓힌 정규식(낱말 변형·띄어쓰기 \s*·영문·동의어). 줄 단위 + 줄바꿈으로 갈린 낱말(이 줄 끝+다음 줄 앞),
# ctx 가 있으면 앞뒤 1줄 창에 ctx 낱말이 있을 때만 남긴다. excl 은 먼저 지우는 말. near 는 두 낱말 묶음이 40자 안에 함께 있을 때만.
REFUTE = {
    "3": dict(pat=r"경미|미미한|중요(성|도)이?\s*(낮|작)|중요하지\s*않|적용\s*(을\s*)?(배제|제외|예외|유예)|적용하지\s*(아니|않)|적용\s*대상|"
                  r"적용\s*범위|(측정|관리|한도관리|모니터링|산출|통합관리)\s*대상|대상\s*(자회사|계열사|회사)|제외할\s*수|제외한다|소규모\s*(자회사|계열사|회사)|"
                  r"비중이?\s*(작|낮|미미|미만)|[Mm]ateriality|모든\s*자회사",
              ctx=r"리스크|위험|자회사|계열사|종속", label="경미·미미·적용 배제/제외/예외/범위·측정/관리 대상·소규모·비중·모든 자회사"),
    "4·5": dict(pat=r"철학|원칙|기본\s*방침|기본\s*정책|리스크\s*문화|위험\s*문화|[Rr]isk\s*[Cc]ulture|최상위\s*가치|가치\s*규범|위험\s*성향|"
                    r"리스크\s*성향|[Rr]isk\s*[Aa]ppetite|RAF\b|선언문|(위험|리스크)\s*관리\s*(정책|기준)",
                ctx=r"리스크|위험", label="철학·원칙·기본방침·리스크 문화·위험성향·Risk Appetite·위험관리정책/기준"),
    "17": dict(pat=r"의사\s*전달|정보\s*전달|공문|공식\s*문서|전자\s*문서|서면|문서(로|화|를|에|의)|통보|통지|시달|하달|지시|권고|가이드\s*라인|"
                   r"요청|요구|전달|회신|이행|조정",
               near=r"(자회사|계열사|그룹사|종속).{0,40}(공문|공식\s*문서|전자\s*문서|서면|문서|통보|통지|시달|하달|지시|권고|가이드|요청|요구|전달|회신)|"
                    r"(공문|공식\s*문서|전자\s*문서|서면|문서|통보|통지|시달|하달|지시|권고|가이드|요청|요구|전달|회신).{0,40}(자회사|계열사|그룹사|종속)",
               label="의사전달·공문·공식/전자문서·서면·통보·시달·하달·지시·권고·가이드라인·요청·요구·전달·회신(자회사 낱말과 40자 안)"),
    "21·22·24": dict(pat=r"연결\s*(기준|실체|대상|범위|기업|회사)|통합\s*(측정|관리|리스크|위험|VaR|한도)|그룹\s*(전체|차원|통합|합산|단위|기준|리스크량|VaR)|"
                          r"합산|단순\s*합|[Gg]roup[- ]?wide|[Cc]onsolidat|리스크\s*량|위험\s*량|소요\s*자기?\s*자본|위험\s*자본|요구\s*자본|내부\s*자본|"
                          r"[Ee]conomic\s*[Cc]apital|경제적\s*자본|분산\s*효과|상관관계|신용\s*VaR|부도율|\bPD\b|\bLGD\b|\bEAD\b|표준\s*방법|내부\s*등급법|내부\s*모형",
                     ctx=r"신용|시장|금리|이자율|리스크|위험", label="연결·통합·그룹 단위 측정, 합산·단순합, 위험·내부·소요자본, 분산효과, PD·LGD·EAD, 표준방법·내부등급법·내부모형"),
    "27": dict(pat=r"평판|명성|이미지\s*(리스크|위험|훼손|실추)|[Rr]eputation|전략\s*(리스크|위험)|[Ss]trateg(y|ic)\s*[Rr]isk|사업\s*(리스크|위험)|"
                   r"비재무|비계량|정성\s*(적|평가)|ESG\s*리스크|기후\s*(리스크|위험)|신규\s*리스크|잠재\s*리스크|전략적\s*(의사\s*결정|경영)",
               label="평판·명성·이미지·Reputation·전략/사업리스크·비재무·비계량·정성·ESG·기후·전략적 의사결정"),
    "34": dict(pat=r"해외|글로벌|국외|국가\s*(별|위험|리스크|신용|한도)|[Cc]ountry|현지\s*법인|외국|역외|[Cc]ross[- ]?border|신흥국|외화",
               ctx=r"리스크|위험|한도|점검|검토|보고|관리|진출", label="해외·글로벌·국외·국가별·Country·현지법인·외국·역외·신흥국·외화"),
    "53": dict(pat=r"위기|비상|[Cc]ontingency|컨틴전시|대응\s*(조직|체계|체제|반|단)|대책\s*(반|위원회|본부|회의)|상황\s*(반|실)|태스크|\bTF\b|[Cc]risis|정상화",
               excl=r"비상임|비상장|비상근|비상위험|비상무|비상각|비상환|비상하", label="위기·비상·Contingency·대응조직/체계·대책반·상황실·TF·Crisis·정상화"),
    "55": dict(pat=r"조기\s*(경보|경고|감지|위험\s*감지|대응)|경보|경고|[Ww]arning|EWS|EWI|징후|위기\s*(단계|수준|지표|상황\s*단계)|위험\s*단계|리스크\s*단계|"
                   r"관심\s*[·,ㆍ/]?\s*주의|주의\s*[·,ㆍ/]?\s*경계|경계\s*[·,ㆍ/]?\s*심각|[Tt]rigger|트리거|임계|발령|선행\s*지표|모니터링\s*지표|KRI|"
                   r"[Rr]ed\s*[Ll]ight|신호등|[Aa]lert|알람|판단\s*(지표|기준)",
               excl=r"환경보호", label="조기경보·경보·경고·징후·위기/위험/리스크 단계·관심/주의/경계/심각·Trigger·임계·발령·KRI·Red Light·판단지표"),
    "규정전문": dict(pat=r"(리스크|위험)\s*관리\s*(규정|준칙|지침)|위기\s*관리\s*지침|국가별\s*위험\s*관리\s*지침|적합성\s*검증\s*지침|"
                       r"그룹\s*(리스크|위험)\s*관리\s*(규정|정책)|(규정|준칙|지침)\s*제\s*\d+\s*조|제\s*1\s*조\s*\(\s*목적\s*\)",
                   label="리스크/위험관리 규정·준칙·지침 이름, 「규정·준칙·지침 제N조」 인용, 제1조(목적) 머리"),
}


def quoted_pages(c):
    """md 에 이미 인용한 (문서 키, 쪽) — 반박 검색 맞은 줄을 「이미 옮긴 쪽」과 「새 쪽」으로 나눌 때 씀."""
    load_meta()
    out = set()
    lines = open(os.path.join(PRE, os.path.basename(MD[c])), encoding="utf-8").read().split("\n")
    for ln in lines:
        if not ln.startswith("- 인용: ["):
            continue
        parts = [x.strip() for x in ln[len("- 인용: ["):].rstrip("]").split(" · ")]
        key = doc_key(parts)
        pl = [x for x in parts if PAGE_LAB_RE.match(x)]
        if key and pl:
            m = PAGE_LAB_RE.match(pl[0])
            for p in range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1):
                out.add((key, p))
    return out


def refute():
    load_meta()
    out = {"검색일": TODAY, "방법": "줄 단위 정규식 + 줄바꿈으로 갈린 낱말(이 줄 끝 12자 + 다음 줄 앞 12자), ctx 가 있으면 앞뒤 1줄 창에 ctx 낱말, "
                                 "near 가 있으면 앞뒤 1줄 창에서 두 낱말 묶음이 40자 안", "조": {}}
    for c in CO:
        qp = quoted_pages(c)
        keys = co_keys(c)
        for jo, spec in REFUTE.items():
            pat = re.compile(spec["pat"])
            ctx = re.compile(spec["ctx"]) if spec.get("ctx") else None
            excl = re.compile(spec["excl"]) if spec.get("excl") else None
            near = re.compile(spec["near"]) if spec.get("near") else None
            rec = out["조"].setdefault(jo, {"검색어": spec["pat"], "ctx": spec.get("ctx"), "near": spec.get("near"), "뺀말": spec.get("excl"),
                                            "label": spec["label"], "문서": {}})
            for k in keys:
                t = T(k)
                hits = []
                for i, ln in enumerate(t.lines):
                    if PAGE_RE.match(ln):
                        continue
                    s = ln.strip()
                    body = excl.sub("", s) if excl else s
                    if not pat.search(body):
                        nxt = t.lines[i + 1].strip() if i + 1 < len(t.lines) else ""
                        j = s[-12:] + nxt[:12]
                        if excl:
                            j = excl.sub("", j)
                        m2 = pat.search(j)
                        if not (m2 and m2.start() < len(s[-12:]) < m2.end()):
                            continue
                    win = " ".join(x.strip() for x in t.lines[max(0, i - 1): i + 2] if not PAGE_RE.match(x))
                    if ctx and not ctx.search(win):
                        continue
                    if near and not near.search(win):
                        continue
                    hits.append({"line": i + 1, "page": t.page[i], "quoted": (k, t.page[i]) in qp, "text": s[:220]})
                rec["문서"][k] = {"name": DOCS[k]["name"], "rcp": DOCS[k].get("rcp", ""), "pages": t.npages, "n": len(hits),
                                 "n_new": sum(1 for h in hits if not h["quoted"]), "hits": hits}
    os.makedirs(VD, exist_ok=True)
    json.dump(out, open(REFUTE_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for jo, rec in out["조"].items():
        parts = []
        for c in CO:
            ks = [k for k in rec["문서"] if DOCS[k]["co"] == CO[c]]
            n8 = sum(rec["문서"][k]["n"] for k in ks if not k.startswith("R9_"))
            nn = sum(rec["문서"][k]["n_new"] for k in ks if not k.startswith("R9_"))
            n9 = sum(rec["문서"][k]["n"] for k in ks if k.startswith("R9_"))
            parts.append(f"{c}: risk8 {n8}줄(인용 밖 {nn}) risk9 {n9}줄")
        print(f"{jo}: " + " / ".join(parts))
    print("→", REFUTE_JSON)


# ───────────────────────────── md 읽기 ─────────────────────────────
QID_RE = re.compile(r"^#### \[([A-Z]+-[A-Z]?\d+[a-z]?)\]\s*(.*)$")
PAGE_LAB_RE = re.compile(r"^p\.(\d+)(?:~(\d+))?(?:\((인쇄|DART 쪽) ([\d~]+)\))?$")
TAG_PREFIX = "- 이 글이 닿는 모범규준 조"
CORR_PREFIX = "- 추가공시·정정판 대조"


def doc_key(parts):
    load_meta()
    name = parts[0]
    rcp = ""
    for x in parts[1:]:
        if x.startswith("접수번호 "):
            rcp = x[len("접수번호 "):].strip()
    cands = [k for k, d in DOCS.items() if d["name"] == name and (not rcp or d.get("rcp") == rcp)]
    cands.sort(key=lambda k: k.startswith("R9_"))
    return cands[0] if cands else None


def parse_md(text):
    lines = text.split("\n")
    quotes, blocks = [], []
    cur = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = QID_RE.match(ln)
        if m:
            cur = dict(id=m.group(1), title=m.group(2), hline=i + 1, cite=None, cline=None, corr=None, corrline=None,
                       tag=None, tagline=None, code=None, cstart=None, cend=None)
            quotes.append(cur)
        elif ln.startswith("```"):
            j = i + 1
            body = []
            while j < len(lines) and lines[j].strip() != "```":
                body.append(lines[j])
                j += 1
            owner = cur["id"] if (cur is not None and cur["code"] is None) else None
            blocks.append(dict(start=i + 2, end=j, owner=owner, body=body))
            if owner:
                cur["code"], cur["cstart"], cur["cend"] = body, i + 2, j
            i = j
        elif cur is not None and ln.startswith("- 인용:") and cur["cite"] is None:
            cur["cite"], cur["cline"] = ln, i + 1
        elif cur is not None and ln.startswith(CORR_PREFIX) and cur["corr"] is None:
            cur["corr"], cur["corrline"] = ln, i + 1
        elif cur is not None and ln.startswith(TAG_PREFIX) and cur["tag"] is None:
            cur["tag"], cur["tagline"] = ln, i + 1
        elif ln.startswith("## ") or ln.startswith("### "):
            cur = None
        i += 1
    gt = [i + 1 for i, ln in enumerate(lines) if ln.startswith(">")]
    return lines, quotes, blocks, gt


# ───────────────────────────── 대조: 원문 인용 ─────────────────────────────
class Report:
    def __init__(self):
        self.out = []
        self.problems = []
        self.stats = {}
        self.detail = {}

    def p(self, s=""):
        self.out.append(s)

    def bad(self, s):
        self.problems.append(s)
        self.out.append("  ✗ " + s)


def segments(code):
    segs, cur = [], []
    for ln in code:
        if MARK_RE.match(ln):
            if cur:
                segs.append(cur)
            cur = []
            continue
        cur.append(ln)
    if cur:
        segs.append(cur)
    return segs


def find_exact(t, body, p1, p2):
    """표시 줄을 뺀 인용 줄들이 원본 줄과 글자 그대로(①) 또는 줄 끝 공백만 빼고(②) 이어서 같은 자리 → (모드, 첫 줄, 끝 줄) 또는 None."""
    idx = t.page_lines(p1, p2)
    if not idx:
        return None
    lo, hi = max(0, idx[0] - 1), idx[-1]
    n = len(body)
    for mode, f in (("글자 그대로", lambda x: x), ("줄 끝 공백만 다름", lambda x: x.rstrip())):
        b = [f(x) for x in body]
        for i in range(lo, hi + 1):
            if f(t.lines[i]) == b[0] and [f(x) for x in t.lines[i:i + n]] == b:
                return mode, i, i + n - 1
    return None


def find_nows(t, code, p1=None, p2=None, skip=False):
    """조각을 순서대로 공백 무시로 찾음 → ((첫 쪽, 끝 쪽, 첫 줄, 끝 줄), None) 또는 (None, 실패 조각 번호)."""
    flat, idx, off = t.flat(skip)
    lo, hi = 0, len(flat)
    if p1 is not None:
        ls = t.page_lines(p1, p2 or p1)
        if not ls:
            return None, -1
        lo, hi = off[max(0, ls[0] - 1)], off[ls[-1] + 1]
    segs = []
    for seg in segments(code):
        n = nows("\n".join(x for x in seg if not (skip and skipline(x))))
        if n:
            segs.append(n)
    if not segs:
        return None, -2
    best, worst = None, 0
    start = flat.find(segs[0], lo, hi)
    tries = 0
    while start >= 0 and tries < 300:
        tries += 1
        spans = [(start, start + len(segs[0]))]
        pos, fail = spans[0][1], None
        for k, n in enumerate(segs[1:], 1):
            j = flat.find(n, pos, hi)
            if j < 0:
                fail = k
                break
            spans.append((j, j + len(n)))
            pos = j + len(n)
        if fail is None:
            if best is None or spans[-1][1] - spans[0][0] < best[-1][1] - best[0][0]:
                best = spans
        else:
            worst = max(worst, fail)
        start = flat.find(segs[0], start + 1, hi)
    if best is None:
        return None, worst
    a, b = idx[best[0][0]], idx[best[-1][1] - 1]
    return (t.page[a], t.page[b], a, b), None


def corr_text(key, body_lines):
    """원 생성기와 같은 계산: 쪽 표지·쪽 머리말 줄을 빼고 공백 없이 맞댐."""
    body = nows("\n".join(x for x in body_lines if not skipline(x)))
    head = body[:40]
    res = []
    for ck in CORR.get(key, []):
        ct = T(ck)
        flat, idx, _ = ct.flat(True)
        lab = CORR_LABEL[ck]
        pos = flat.find(body)
        if pos >= 0:
            res.append(f"{lab}: 같은 글 있음({ct.plabel(ct.page[idx[pos]], ct.page[idx[pos + len(body) - 1]])})")
            continue
        hp = flat.find(head)
        if hp >= 0:
            res.append(f"{lab}: 앞 40자는 {ct.plabel(ct.page[idx[hp]])} 에 있으나 전체 글이 같지 않음")
        else:
            res.append(f"{lab}: 이 글 없음(그 판에 이 부분이 실려 있지 않음)")
    return res


ART_HEAD = re.compile(r"^\s*제\s*(\d+)\s*조(?:\s*의\s*(\d+))?\s*(?:\(([^)]*)\)|(삭\s*제))")


def enclosing_article(t, line_i):
    for i in range(line_i, -1, -1):
        m = ART_HEAD.match(t.lines[i])
        if m:
            return i, f"제{m.group(1)}조" + (f"의{m.group(2)}" if m.group(2) else ""), (m.group(3) or "삭제").strip()
    return None


def check_jomun(q, parts, t, body, start_i):
    """인용 줄의 「· <규정> 제A조~제B조」 표기가 인용 글의 조 머리와 맞는지."""
    errs = []
    for x in parts:
        m = re.match(r"^(\S+(?:규정|규범))\s+제(\d+)조(?:~제(\d+)조)?(.*)$", x)
        if not m:
            continue
        a, b = int(m.group(2)), int(m.group(3) or m.group(2))
        heads = [int(mm.group(1)) for mm in (ART_HEAD.match(ln) for ln in body) if mm]
        if a not in heads or b not in heads:
            enc = enclosing_article(t, start_i) if start_i is not None else None
            if enc and a == b and enc[1] == f"제{a}조" and "추정" not in x:
                continue                     # 조 머리는 인용 밖(위쪽)에 있고 감싸는 조가 표기와 같음
            where = f" — 원문에서 인용 첫 줄을 감싸는 조는 {enc[1]}({enc[2]}) (p.{t.page[enc[0]]})" if enc else ""
            heads_s = f"제{a}조" if a == b else f"제{a}조·제{b}조"
            errs.append(f"조문 표기 「{x}」 — 인용 글에 {heads_s} 머리가 없음{where}")
    return errs


def check_quotes(R, c, text, label, record=True):
    load_meta()
    lines, quotes, blocks, gt = parse_md(text)
    n_ok = n_exact = 0
    det = []
    for ln_no in gt:
        R.bad(f"{label}: 「>」 인용 블록 줄 {ln_no} — 이 파일은 코드 블록만 씀(대조 규칙 밖)")
    for b in blocks:
        if b["owner"] is None:
            R.bad(f"{label}: 인용 머리(#### [ID]) 없는 코드 블록 {b['start']}~{b['end']}행")
    ids = [q["id"] for q in quotes]
    for x in sorted(set(ids)):
        if ids.count(x) > 1:
            R.bad(f"{label}: 인용 번호 {x} 가 {ids.count(x)}번 나옴")
    for q in quotes:
        d0 = dict(id=q["id"], line=q["hline"])
        det.append(d0)
        if q["code"] is None or not q["cite"]:
            R.bad(f"{label} [{q['id']}]: 코드 블록 또는 「- 인용:」 줄 없음")
            d0["결과"] = "형식 문제"
            continue
        if not q["tag"]:
            R.bad(f"{label} [{q['id']}]: 「{TAG_PREFIX}…」 줄 없음")
        body = q["cite"][len("- 인용: ["):].rstrip()
        if not body.endswith("]"):
            R.bad(f"{label} [{q['id']}]: 인용 줄 끝 「]」 없음")
        parts = [x.strip() for x in body.rstrip("]").split(" · ")]
        key = doc_key(parts)
        if not key:
            R.bad(f"{label} [{q['id']}]: 인용 줄 문서명·접수번호가 문서 목록과 맞지 않음 — {parts[0][:60]}")
            d0["결과"] = "문서 불명"
            continue
        d = DOCS[key]
        if d["co"] != CO[c]:
            R.bad(f"{label} [{q['id']}]: 다른 회사 문서 인용 — {d['name'][:40]}")
        t = T(key)
        errs = []
        if "rcp" in d:
            if f"접수번호 {d['rcp']}" not in parts or d["url"] not in parts:
                errs.append(f"접수번호·URL 표기(기대 「접수번호 {d['rcp']} · {d['url']}」)")
        else:
            want = f"{d['url']} (방식 {d['method']})" if d.get("method") else d["url"]
            if want not in parts:
                errs.append(f"URL 표기(기대 「{want}」)")
        fet = [x for x in parts if x.startswith("원본 수집 ")]
        if not fet or fet[0] != "원본 수집 " + d["fetched"][:10]:
            errs.append(f"원본 수집일(기대 {d['fetched'][:10]})")
        if not any(x in parts for x in MOVED_OK):
            errs.append("옮김 날짜")
        pl = [x for x in parts if PAGE_LAB_RE.match(x)]
        if not pl:
            R.bad(f"{label} [{q['id']}]: 쪽 표기 없음")
            continue
        m = PAGE_LAB_RE.match(pl[0])
        p1, p2 = int(m.group(1)), int(m.group(2) or m.group(1))
        body_lines = [x for x in q["code"] if not MARK_RE.match(x)]
        ex = find_exact(t, body_lines, p1, p2)
        res, fail = find_nows(t, q["code"], p1, p2)
        d0.update(문서=key, 쪽=pl[0], 줄수=len(q["code"]), 표시줄=len(q["code"]) - len(body_lines))
        start_i = None
        if res is None:
            res2, _ = find_nows(t, q["code"])
            where = f" — 문서 전체에서는 {t.plabel(res2[0], res2[1])}" if res2 else " — 문서 전체에서도 못 찾음"
            errs.append(f"공백 무시 대조 실패(조각 {fail}){where}")
            d0["결과"] = "불일치"
        else:
            start_i = res[2]
            pages = sorted({t.page[i] for i in range(res[2], res[3] + 1) if not PAGE_RE.match(t.lines[i])})
            lab = t.plabel(pages[0], pages[-1])
            if lab != pl[0]:
                errs.append(f"쪽 표기 「{pl[0]}」 ≠ 찾은 쪽 「{lab}」")
            d0["결과"] = "공백 무시 일치"
            if ex:
                n_exact += 1
                d0["결과"] = ex[0]
                d0["원본줄"] = f"{ex[1] + 1}~{ex[2] + 1}"
                start_i = ex[1]
        errs += check_jomun(q, parts, t, body_lines, start_i)
        if key in CORR:
            want = CORR_PREFIX + "(공백·쪽 머리말 무시): " + " / ".join(corr_text(key, body_lines))
            if q["corr"] != want:
                errs.append(f"「추가공시·정정판 대조」 줄이 다시 계산한 값과 다름 — 기대 「{want[len(CORR_PREFIX):]}」")
        if errs:
            R.bad(f"{label} [{q['id']}] ({d['kind']} {pl[0]}): " + "; ".join(errs))
            d0["문제"] = errs
        else:
            n_ok += 1
            R.p(f"  ✓ [{q['id']}] {d['kind']} {pl[0]} — {len(q['code'])}줄(표시 줄 {d0['표시줄']}), {d0['결과']}")
    if record:
        R.stats[c + "_quotes"] = len(quotes)
        R.stats[c + "_ok"] = n_ok
        R.stats[c + "_exact"] = n_exact
        R.detail[c + "_quotes"] = det
    R.p(f"  → 인용 {len(quotes)}건 중 출처·쪽·글 모두 일치 {n_ok}건(줄 그대로 일치 {n_exact}건)")
    return lines, quotes


def doc_name_parts(k):
    """문서명에 들어 있어야 할 메타 표기: 연차보고서 제목·공시일(dart_out/risk8/연차보고서_FY2025.csv), 경영공시 제목·게시일(meta.json),
    사업보고서 보고서명(dart_out/risk9/텍스트목록.csv)."""
    d = DOCS[k]
    out = []
    if d["kind"].startswith("연차보고서"):
        fn = d["file"][:-4].split("__", 1)[1] + ".pdf"
        for r in read_csv(os.path.join("dart_out", "risk8", "연차보고서_FY2025.csv")):
            if r["저장파일명"] == fn:
                out += [f"「{r['제목']}」", f"공시일 {r['공시일']}"]
    elif "rcp" in d:
        for r in read_csv(os.path.join("dart_out", "risk9", "텍스트목록.csv")):
            if r["rcept_no"] == d["rcp"]:
                out.append(f"「{r['report_nm']}」")
    else:
        m = json.load(open(os.path.join("dart_out", "raw", "risk8", "경영공시", d["co"], "meta.json"), encoding="utf-8"))
        out.append(f"「{m['제목']}」")
        if m.get("게시일"):
            out.append(f"게시일 {m['게시일']}")
    return out


def check_doc_table(R, c, lines):
    load_meta()
    rows = [ln for ln in lines if re.match(r"^\| ([IN]_[A-Z_0-9]+) \|", ln)]
    seen = set()
    for ln in rows:
        cells = [x.strip() for x in ln.strip().strip("|").split("|")]
        k = cells[0]
        if k not in DOCS:
            R.bad(f"{CO[c]} 0-1 문서 표: 모르는 키 {k}")
            continue
        seen.add(k)
        d = DOCS[k]
        t = T(k)
        want = [k, d["name"], d.get("rcp") or d["url"], f"`{d['src_sha'][:16]}…`", f"`{sha(d['path'])[:16]}…`", str(t.npages), d["fetched"][:19]]
        if cells[:7] != want:
            R.bad(f"{CO[c]} 0-1 문서 표 {k}: {cells[:7]} ≠ 기대 {want}")
        for w in doc_name_parts(k):
            if w not in d["name"]:
                R.bad(f"{CO[c]} {k}: 문서명 「{d['name']}」 에 메타 표기 「{w}」 가 없음")
        if sha(d["path"]) != d["txt_sha_list"]:
            R.bad(f"{CO[c]} {k}: 텍스트 sha256 이 텍스트목록.csv 와 다름")
    want_keys = {k for k in DOCS if DOCS[k]["co"] == CO[c] and not k.startswith("R9_")}
    if seen != want_keys:
        R.bad(f"{CO[c]} 0-1 문서 표 키 {sorted(seen)} ≠ {sorted(want_keys)}")
    R.p(f"  0-1 문서 표 {len(rows)}행 대조(sha256·쪽수·원본 수집 시각)")


# ───────────────────────────── 대조: 조문 목차 ─────────────────────────────
# 전문을 옮긴 규정: (CSV 규정명, 문서 키, 첫 쪽, 끝 쪽, 제목 줄(이 줄부터), 다음 규정 제목(이 줄 전까지, 없으면 끝 쪽 끝까지))
FULL_REGS = {
    "I": [("리스크관리규정(첨부16 「리스크관리 규정」)", "I_AR", 275, 289, "리스크관리규정", None),
          ("위험관리위원회규정(첨부9)", "I_AR", 244, 248, "위험관리위원회규정", None),
          ("그룹경영관리협의회규정(첨부14)", "I_AR", 268, 271, "그룹경영관리협의회규정", None),
          ("위험관리협의회규정(첨부15)", "I_AR", 272, 274, "위험관리협의회규정", None)],
    "N": [("리스크관리위원회규정([첨부5] 각 위원회 규정 중)", "N_AR", 310, 313, "리스크관리위원회규정", "보수위원회규정"),
          ("최고경영자협의회규정([첨부7])", "N_AR", 333, 334, "최고경영자협의회규정", None)],
}
CH_HEAD = re.compile(r"^\s*제\s*(\d+)\s*장\s+(\S.*?)\s*$")
BUCHIK = re.compile(r"^\s*부\s*칙\s*(\(.*\))?\s*$")


def reg_heads(c, reg):
    """규정 원문에서 장·조 머리(삭제 조·「제N조의M」 포함)와 부칙·부칙 조를 줄 순서대로 뽑음."""
    name, key, p1, p2, title, nxt = reg
    t = T(key)
    idx = t.page_lines(p1, p2)
    s = next(i for i in idx if t.lines[i].strip() == title)
    e = idx[-1]
    if nxt:
        e = next((i - 1 for i in idx if i > s and t.lines[i].strip() == nxt), e)
    out = []
    nb = 0
    for i in range(s, e + 1):
        ln = t.lines[i]
        if BUCHIK.match(ln):
            nb += 1
            out.append(dict(kind="부칙", no=f"부칙{nb}", title=(BUCHIK.match(ln).group(1) or "").strip("()"), page=t.page[i], line=i))
            continue
        m = CH_HEAD.match(ln)
        if m and nb == 0 and len(ln.strip()) < 60:
            out.append(dict(kind="장", no=f"제{m.group(1)}장", title=m.group(2), page=t.page[i], line=i))
            continue
        m = ART_HEAD.match(ln)
        if m:
            no = f"제{m.group(1)}조" + (f"의{m.group(2)}" if m.group(2) else "")
            ttl = (m.group(3) or "삭제").strip()
            out.append(dict(kind="부칙조" if nb else "조", no=no, title=ttl, page=t.page[i], line=i, buchik=nb))
        elif re.search(r"제\s*\d+\s*조\s*(의\s*\d+\s*)?(삭\s*제|<\s*삭제|\[\s*삭제)", ln):
            out.append(dict(kind="삭제조?", no=ln.strip()[:30], title="삭제", page=t.page[i], line=i))
    return out, s, e


def buchik_label(h, heads):
    """부칙 조 행의 조번호 표기: 「부칙(N/총) 제M조」."""
    tot = sum(1 for x in heads if x["kind"] == "부칙")
    return f"부칙({h['buchik']}/{tot}) {h['no']}"


def check_toc(R, c, rows=None, md_lines=None):
    load_meta()
    rows = rows if rows is not None else read_csv(TOC[c])
    R.p(f"## 조문 목차 CSV — {os.path.basename(TOC[c])} ({len(rows)}행)")
    cols = ["회사", "규정명", "조번호", "조제목", "문서", "접수번호또는URL", "쪽", "전문여부", "비고"]
    if rows and list(rows[0].keys()) != cols:
        R.bad(f"{CO[c]} CSV 열 {list(rows[0].keys())} ≠ {cols}")
    pagewise = []
    for reg in FULL_REGS[c]:
        name, key = reg[0], reg[1]
        t = T(key)
        heads, s, e = reg_heads(c, reg)
        mine = [r for r in rows if r["규정명"] == name]
        got = {(r["조번호"], r["조제목"], r["쪽"]) for r in mine}
        want = set()
        nb = sum(1 for h in heads if h["kind"] == "부칙")
        nbj = sum(1 for h in heads if h["kind"] == "부칙조")
        for h in heads:
            if h["kind"] == "삭제조?":
                R.bad(f"{CO[c]} {name}: 삭제 조로 보이는 줄 p.{h['page']} 「{h['no']}」 — 조 머리 규칙으로 못 읽음")
                continue
            if h["kind"] == "부칙":
                continue
            no = buchik_label(h, heads) if h["kind"] == "부칙조" else h["no"]
            want.add((no, h["title"], t.plabel(h["page"])))
        miss = sorted(want - got, key=lambda x: x[2])
        extra = sorted(got - want, key=lambda x: x[2])
        for x in miss:
            R.bad(f"{CO[c]} {name}: 원문 {x[2]} 의 「{x[0]}({x[1]})」 이 CSV 에 없음")
        for x in extra:
            R.bad(f"{CO[c]} {name}: CSV 행 「{x[0]}({x[1]})」 {x[2]} 이 원문 머리와 맞지 않음")
        for r in mine:
            d = DOCS[key]
            if r["문서"] != d["name"] or r["접수번호또는URL"] != (d.get("rcp") or d["url"]) or r["회사"] != CO[c]:
                R.bad(f"{CO[c]} {name} {r['조번호']}: 회사·문서·URL 칸이 메타와 다름")
            if not r["전문여부"].startswith("Y"):
                R.bad(f"{CO[c]} {name} {r['조번호']}: 전문여부 「{r['전문여부']}」")
        # 쪽마다
        for p in range(reg[2], reg[3] + 1):
            hs = [h for h in heads if h["page"] == p and h["kind"] in ("장", "조", "부칙조", "삭제조?")]
            inc = sum(1 for h in hs if ((buchik_label(h, heads) if h["kind"] == "부칙조" else h["no"]), h["title"], t.plabel(p)) in got)
            nbp = sum(1 for h in heads if h["page"] == p and h["kind"] == "부칙")
            pagewise.append(f"    {name[:14]} {t.plabel(p)}: 머리 {len(hs)}개(부칙 {nbp}건) — CSV 에 있음 {inc}개"
                            + ("" if inc == len(hs) else " ✗"))
        R.p(f"  {name}: 원문 장·조 머리 {sum(1 for h in heads if h['kind'] in ('장', '조'))}개, 부칙 {nb}건(부칙 조 {nbj}개), "
            f"CSV {len(mine)}행 — 빠진 것 {len(miss)}, 남는 것 {len(extra)}")
    R.p("  쪽마다(원문 머리 수 / CSV 에 있는 수):")
    R.out += pagewise
    # 이름만 있는 행·일부 행
    for r in rows:
        if any(r["규정명"] == reg[0] for reg in FULL_REGS[c]):
            continue
        key = next((k for k, d in DOCS.items() if d["name"] == r["문서"]), None)
        if not key:
            R.bad(f"{CO[c]} CSV 「{r['규정명']}」: 문서명이 메타와 다름")
            continue
        m = PAGE_LAB_RE.match(r["쪽"])
        if not m:
            R.bad(f"{CO[c]} CSV 「{r['규정명']}」: 쪽 표기 「{r['쪽']}」")
            continue
        t = T(key)
        pg = int(m.group(1))
        if t.plabel(pg) != r["쪽"]:
            R.bad(f"{CO[c]} CSV 「{r['규정명']}」: 쪽 표기 「{r['쪽']}」 ≠ 「{t.plabel(pg)}」")
        names = [x.strip() for x in re.split(r"[()/]|\s/\s", r["규정명"]) if x.strip()]
        names = [re.sub(r"(제\d+조 ?①?|\d{4}\.\d+ 제정|\[첨부\d\]|첨부\d+)", "", x).strip() for x in names]
        names = [x for x in names if len(nows(x)) >= 4]
        pagetxt = nows("\n".join(t.lines[i] for i in t.page_lines(pg)))
        if r["조번호"] not in ("-", "") and r["조번호"].startswith("제"):
            mm = re.match(r"제(\d+)조", r["조번호"])
            heads_on = [ART_HEAD.match(t.lines[i]) for i in t.page_lines(pg)]
            if not any(h and h.group(1) == mm.group(1) and nows(h.group(3) or "") == nows(r["조제목"]) for h in heads_on):
                R.bad(f"{CO[c]} CSV 「{r['규정명']} {r['조번호']}({r['조제목']})」: {r['쪽']} 에 그 조 머리 없음")
        elif not any(nows(x) in pagetxt for x in names):
            R.bad(f"{CO[c]} CSV 「{r['규정명']}」: 이름이 {r['쪽']} 글에 없음(찾은 이름 {names})")
    # md 1-2·1-4 표 ↔ CSV
    if md_lines is not None:
        check_md_toc(R, c, rows, md_lines)


def check_md_toc(R, c, rows, lines):
    """md 1-2(iM: 리스크관리규정 장·조, NH: 첨부 규정)·1-4(iM 위원회·협의회 규정) 표가 CSV 와 같은지."""
    md_set = set()
    for ln in lines:
        m = re.match(r"^\| \*\*(제\d+장)\*\* \| \*\*(.+?)\*\* \| (p\.\d+[^|]*?) \|", ln)
        if m and c == "I":
            md_set.add(("리스크관리규정(첨부16 「리스크관리 규정」)", m.group(1), m.group(2), m.group(3).strip()))
            continue
        m = re.match(r"^\| (제\d+조) \| ([^|]+?) \| (p\.\d+[^|]*?) \| \d+조\(", ln)
        if m and c == "I":
            md_set.add(("리스크관리규정(첨부16 「리스크관리 규정」)", m.group(1), m.group(2).strip(), m.group(3).strip()))
            continue
        m = re.match(r"^\| ([^|]+?규정[^|]*?) \| (제\d+조) \| ([^|]+?) \| (p\.\d+[^|]*?) \|$", ln)
        if m:
            md_set.add((m.group(1).strip(), m.group(2), m.group(3).strip(), m.group(4).strip()))
            continue
        m = re.match(r"^\| ([^|]+?규정[^|]*?) \| (부칙\(\d+/\d+\) 제\d+조) \| ([^|]+?) \| (p\.\d+[^|]*?) \|", ln)
        if m:
            md_set.add((m.group(1).strip(), m.group(2), m.group(3).strip(), m.group(4).strip()))
    csv_set = {(r["규정명"], r["조번호"], r["조제목"], r["쪽"]) for r in rows if r["전문여부"].startswith("Y")}
    miss = csv_set - md_set
    extra = md_set - csv_set
    for x in sorted(miss)[:10]:
        R.bad(f"{CO[c]} md 조문 목차 표에 CSV 행 없음: {x}")
    for x in sorted(extra)[:10]:
        R.bad(f"{CO[c]} md 조문 목차 표 행이 CSV 에 없음: {x}")
    R.p(f"  md 조문 목차 표 ↔ CSV(전문 규정): md {len(md_set)}행, CSV {len(csv_set)}행 — 빠진 것 {len(miss)}, 남는 것 {len(extra)}")


# ───────────────────────────── 대조: 「…」 조각 ─────────────────────────────
def req_text():
    for p in (REQ, REQ_COPY):
        if os.path.exists(p):
            return open(p, encoding="utf-8").read()
    return ""


_CORPUS = {}


def corpus_for(c):
    if c not in _CORPUS:
        load_meta()
        parts = [nows(open(DOCS[k]["path"], encoding="utf-8").read()) for k in co_keys(c, r9=False)]
        parts.append(nows(open(MOBEOM_MD, encoding="utf-8").read()))
        parts.append(nows(req_text()) or nows("\n".join(t for _, t in REQ_ITEMS)))
        for k in co_keys(c, r9=False):
            parts += [nows(x.strip("「」")) for x in doc_name_parts(k)]
        _CORPUS[c] = "\n".join(parts)
    return _CORPUS[c]


def frags(line):
    """바깥 「…」 조각(겹낫표 안 겹낫표 허용)."""
    out, depth, cur = [], 0, []
    for ch in line:
        if ch == "「":
            if depth > 0:
                cur.append(ch)
            depth += 1
        elif ch == "」" and depth > 0:
            depth -= 1
            if depth == 0:
                out.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        elif depth > 0:
            cur.append(ch)
    return out


# 원본 글이 아닌 「…」 표기(조각 대조에서 넘김): 이 작업의 표지·검색 기록 이름·절 이름 등
FRAG_SKIP = re.compile(r"^(추출 범위에 없음|받은 글|note:|\(판단\)|판단|p\.N|인쇄 N|DART 쪽 N|=== p\.N ===|\[표 깨짐: …\]|\[추출 깨짐: …\]|"
                       r"[\d·]+(\([^)]*\))?|목차\(규정명\)|규정전문|21·22·24\(연결·통합\)|목차|전 조|이 글이 닿는 모범규준 조.*|"
                       r"모범규준 조 번호\(조 제목\)|N조\(조 제목\)|7\. 지시서 항목별 대조.*|검증 기록.*|"
                       r"\d+조\([^)]*\).*|[0-9]+조|사용자 표.*|그룹 리스크관리규정|iM 그룹 리스크관리규정|28조\(통합리스크관리시스템\).*|"
                       r"추가공시·정정판 대조.*|같은 글 있음.*|\d+\.?|[가-하]\.|[①-⑳].*?)$")
FRAG_OK = {   # 조각: 사유(원문 글이 아니라 이 작업의 표기·열 이름)
    "전자공시시스템 dart.fss.or.kr Page N": "쪽 표기 설명(사업보고서 쪽 아래 글의 꼴)",
    "대응 조 없음": "1-3 표의 칸 값(이 작업의 표기)",
    "인용으로 옮긴 쪽": "6장 표의 열 이름",
    "[첨부N]": "첨부 표지 꼴(이 작업의 표기)",
    "규정 전문은 추출 범위에 없음": "이 작업의 판정 문구",
    "그룹 위기관리지침": "규정 원문 표기(「“그룹 위기관리지침”」 — 따옴표 안 글)",
    "제N조의M": "조 번호 꼴 표기(이 작업의 설명)",
    "추출 범위에 없음 + 찾은 방법": "지시서·공통 지침의 판정 꼴(이 작업의 설명)",
    "- 인용:": "md 출처 줄 머리(이 작업의 표기)",
    "쪽마다": "대조 결과 파일의 줄 이름",
    "규정·준칙·지침 제N조": "반박 검색 꼴 설명(검증 기록)",
    "제10조(추정)": "검증 전 이 파일 인용 줄의 표기(바로잡은 글을 가리킴)",
    "이사회규정 제10조(추정)": "검증 전 이 파일 인용 줄의 표기(바로잡은 글을 가리킴)",
}


def fixed_lines(lines):
    """검증 기록 「### 고친 곳(전 → 후)」 절의 줄 번호(0부터) — 검증 전 틀린 글을 그대로 적으므로 조각·제목 대조에서 넘김."""
    out = set()
    on = False
    for i, ln in enumerate(lines):
        if ln.startswith("### 고친 곳") or ln.startswith("### 정합성 보정"):
            on = True
            continue
        if on and (ln.startswith("### ") or ln.startswith("## ")):
            on = False
        if on:
            out.add(i)
    return out


def check_frags(R, c, lines, blocks):
    corp = corpus_for(c)
    inblock = set()
    for b in blocks:
        inblock.update(range(b["start"] - 1, b["end"] + 1))
    n = bad = 0
    misses = []
    skip = fixed_lines(lines)
    for i, ln in enumerate(lines):
        if i in skip:
            continue
        if i + 1 in inblock or ln.startswith("- 인용:") or ln.startswith("| 조 |") or re.match(r"^\| (3|4·5|17|21|22|24|27|34|53|55|목차|21·22·24)\S* \| `", ln):
            continue
        for f in frags(ln):
            f0 = f.strip()
            if not f0 or FRAG_SKIP.match(f0) or f0 in FRAG_OK:
                continue
            n += 1
            pieces = [nows(x) for x in re.split(r"…|\.\.\.", f0) if nows(x)]
            if all(p in corp for p in pieces):
                continue
            bad += 1
            misses.append((i + 1, f0))
    for ln_no, f0 in misses:
        R.bad(f"{CO[c]} {ln_no}행 「{f0[:80]}」 — 회사 원문·모범규준 원문·지시서에서 공백 무시로 못 찾음")
    R.p(f"  「…」 조각 {n}개 대조 — 못 찾은 것 {bad}개")
    R.stats[c + "_frags"] = n
    return misses


# ───────────────────────────── 대조: 모범규준 조 표기 ─────────────────────────────
TITLE_RE = re.compile(r"(?<![제\d~])(\d{1,2})조\(([^()]*)\)")


def check_titles(R, c, lines, blocks):
    jo = jo_titles()
    inblock = set()
    for b in blocks:
        inblock.update(range(b["start"] - 1, b["end"] + 1))
    n = 0
    req = nows(req_text())
    skip = fixed_lines(lines)
    for i, ln in enumerate(lines):
        if i + 1 in inblock or ln.startswith("- 인용:") or i in skip:
            continue
        if ln.startswith("| 9-4 "):                       # 7절 — 둘째 칸은 지시서 원문 그대로
            cells = ln.split(" | ")
            ln = " | ".join(cells[:1] + cells[2:])
        if re.match(r"^### \d+조 ", ln):
            R.bad(f"{CO[c]} {i + 1}행 3장 조별 머리에 조 제목 없음: {ln[:40]}")
        reqfr = [f for f in frags(ln) if nows(f) and nows(f) in req]
        for m in TITLE_RE.finditer(ln):
            k, ttl = int(m.group(1)), m.group(2)
            if k not in jo:
                continue
            n += 1
            if not ttl.startswith(jo[k]):
                if re.match(r"^[①-⑳\d]", ttl) or ttl == "판단" or any(m.group(0) in f for f in reqfr):
                    continue
                R.bad(f"{CO[c]} {i + 1}행 「{m.group(0)}」 — 조목록(2016.8.1판) 제목 「{jo[k]}」 와 다름")
    R.p(f"  「N조(제목)」 표기 {n}곳 — 조목록 제목 대조")


def check_tags(R, c, quotes):
    """인용마다 조 태그 줄이 「N조(제목)」 꼴이고, 지시서에 없는 조 번호에 「(판단)」이 붙었는지."""
    jo = jo_titles()
    bad = 0
    for q in quotes:
        tg = q["tag"] or ""
        if not tg.startswith(TAG_PREFIX + "(조 제목은 2016.8.1판): "):
            R.bad(f"{CO[c]} [{q['id']}] 조 태그 줄 꼴이 「{TAG_PREFIX}(조 제목은 2016.8.1판): N조(제목), …」 가 아님")
            bad += 1
            continue
        body = tg.split(": ", 1)[1].split(" — ")[0]
        for m in re.finditer(r"(\d{1,2})조\(([^()]*)\)(\(판단\))?", body):
            k = int(m.group(1))
            if m.group(2) != jo.get(k):
                R.bad(f"{CO[c]} [{q['id']}] 조 태그 「{m.group(0)}」 제목이 조목록과 다름")
                bad += 1
            need = k not in REQ_ARTS[c]
            if need and not m.group(3):
                R.bad(f"{CO[c]} [{q['id']}] 조 태그 「{m.group(0)}」 — 지시서에 없는 조인데 「(판단)」 없음")
                bad += 1
        rest = re.sub(r"\d{1,2}조\([^()]*\)(\(판단\))?|조문 목차\(지시서 9-4 1\.\)|9-4 조문 대조\(대조표 A~C\)|[,·\s]", "", body)
        if rest:
            R.bad(f"{CO[c]} [{q['id']}] 조 태그 줄에 읽지 못한 글 「{rest}」")
            bad += 1
    R.p(f"  조 태그 줄 {len(quotes)}개 — 문제 {bad}")


# ───────────────────────────── 대조: 지시서 항목·추출 범위에 없음 ─────────────────────────────
REQ_ITEMS = [
    ("9-4 1.", "그룹리스크관리규정(이름이 다르면 대응 규정)의 조문 목차 전체(조 번호와 제목). 전문이 있으면 전문"),
    ("9-4 1. iM", "iM 그룹 리스크관리규정은 28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음."),
    ("9-4 1. iM 표", "전체 조문 번호가 모범규준과 얼마나 맞는지 표로"),
    ("9-4 1. 메리츠", "메리츠 그룹리스크관리규정 9조 7항, 57조가 인용되어 있음. 같은 방식으로 대조"),
    ("9-4 2. 21·22·24", "21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부"),
    ("9-4 2. 27", "27조 전략·평판위험: 관리 체제, 측정이나 평가 수단"),
    ("9-4 2. 34", "34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고"),
    ("9-4 2. 3", "3조: 위험이 경미한 자회사를 적용에서 빼는 기준"),
    ("9-4 2. 17", "17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)"),
    ("9-4 2. 55", "55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)"),
    ("9-4 2. 53", "53조 위기대응조직: 구성과 전환 요건"),
    ("9-4 3.", "위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구"),
]
SEC7 = "## 7. 지시서 항목별 대조"


def check_request(R, c, lines, quotes):
    req = nows(req_text())
    if not req:
        R.p("  (지시서 파일 REQUEST13.md·사본 둘 다 없음 — 지시서 원문 칸은 스크립트 안 REQ_ITEMS 와만 대조)")
        req = nows("\n".join(t for _, t in REQ_ITEMS))
    ids = {q["id"] for q in quotes}
    try:
        s = next(i for i, ln in enumerate(lines) if ln.startswith(SEC7))
    except StopIteration:
        R.bad(f"{CO[c]}: 「{SEC7}」 절 없음")
        return
    rows = {}
    for ln in lines[s:]:
        if ln.startswith("## ") and not ln.startswith(SEC7):
            break
        m = re.match(r"^\| (9-4 [^|]+?) \| ([^|]+) \| ([^|]+) \| ([^|]*) \| ([^|]+) \|$", ln)
        if m:
            rows[m.group(1).strip()] = [x.strip() for x in m.groups()]
    for item, txt in REQ_ITEMS:
        if nows(txt) not in req:
            R.bad(f"지시서 원문 대조: 「{txt[:30]}…」 가 지시서에 없음")
        r = rows.get(item)
        if not r:
            R.bad(f"{CO[c]} 7절: 지시서 항목 「{item}」 행 없음")
            continue
        if nows(r[1]) != nows(txt):
            R.bad(f"{CO[c]} 7절 「{item}」 지시서 원문 칸이 지시서 글과 다름")
        st = r[4]
        if not (st.startswith("받은 글") or st.startswith("일부") or st.startswith("추출 범위에 없음") or st.startswith("해당 없음")):
            R.bad(f"{CO[c]} 7절 「{item}」 상태 칸 「{st[:20]}」")
        if "추출 범위에 없음" in st and "찾은 방법" not in r[3] + " " + st:
            R.bad(f"{CO[c]} 7절 「{item}」: 「추출 범위에 없음」에 찾은 방법 없음")
        for x in re.findall(r"\[([A-Z]+-[A-Z]?\d+[a-z]?)\]", r[3] + r[4]):
            if x not in ids:
                R.bad(f"{CO[c]} 7절 「{item}」: 인용 번호 [{x}] 가 md 에 없음")
    R.p(f"  7절 지시서 항목 {len(REQ_ITEMS)}개 대조")


NF_METHOD = re.compile(r"찾은 방법|찾은 범위|찾은 파일|검색어|6장|검색|검증 기록|p\.1~|전체|정규식|대조|지침.{0,6}위임|위임")


def check_notfound(R, c, lines):
    n = bad = 0
    try:
        vrec = next(i for i, ln in enumerate(lines) if ln.startswith(VREC_OK))
    except StopIteration:
        vrec = len(lines)
    for i, ln in enumerate(lines[:vrec]):
        if "추출 범위에 없음" not in ln or ln.startswith("- 인용:") or ln.startswith("| 조 |"):
            continue
        n += 1
        if not NF_METHOD.search(ln):
            ctx = " ".join(lines[max(0, i - 2): i + 3])
            if not NF_METHOD.search(ctx):
                bad += 1
                R.bad(f"{CO[c]} {i + 1}행 「추출 범위에 없음」 — 찾은 방법(검색어·범위) 표시 없음: {ln[:80]}")
    R.p(f"  「추출 범위에 없음」 줄 {n}개 — 찾은 방법 없는 줄 {bad}")
    R.stats[c + "_nf"] = n


# ───────────────────────────── 보안·형식 ─────────────────────────────
def secret_values():
    vals = []
    for k in ("DART_API_KEY", "LAW_OC", "OC", "LAW_API_OC"):
        v = os.environ.get(k)
        if v and len(v) >= 4:
            vals.append(v)
    if os.path.exists(".env"):
        for ln in open(".env", encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*['\"]?([^'\"\s#]+)", ln)
            if m and len(m.group(2)) >= 4 and any(x in m.group(1) for x in ("KEY", "OC", "TOKEN", "SECRET")):
                vals.append(m.group(2))
    return vals


def check_misc(R, paths, texts):
    vals = secret_values()
    for p in paths:
        s = open(p, encoding="utf-8").read()
        for v in vals:
            if v in s:
                R.bad(f"{p}: 인증값 문자열이 들어 있음(값은 출력하지 않음)")
        if re.search(r"crtfc_key=[0-9a-f]{20,}|OC=(?!\*\*\*)[A-Za-z0-9]{3,}", s):
            R.bad(f"{p}: 인증값처럼 보이는 질의 문자열")
    pdfs = [f for f in os.listdir(OUTD) if f.lower().endswith(".pdf")]
    if pdfs:
        R.bad(f"산출 폴더에 PDF {pdfs}")
    for c, s in texts.items():
        vr = next((v for v in VREC_OK if "\n" + v in s), VREC)
        n = sum(s.count("\n" + v) for v in VREC_OK)
        if n != 1:
            R.bad(f"{CO[c]}: 「{VREC}」 절이 {n}개(1개여야 함)")
        else:
            tail = s.split("\n" + vr, 1)[1]
            if re.search(r"^## ", tail, re.M):
                R.bad(f"{CO[c]}: 「{VREC}」 절이 맨 끝이 아님")
    R.p(f"  인증값 {len(vals)}종 대조(값은 출력 안 함), 산출 폴더 PDF {len(pdfs)}개")


# ───────────────────────────── 대조 실행 ─────────────────────────────
def run_check(write=True):
    load_meta()
    R = Report()
    R.p(f"verify13_g_im_nh — {TODAY} 대조 결과 (스크립트 scripts/dart/verify13_g_im_nh.py)")
    R.p("")
    texts = {}
    for c in CO:
        text = open(MD[c], encoding="utf-8").read()
        texts[c] = text
        R.p(f"# {CO[c]} — {MD[c]}")
        R.p("## 1. 원문 인용 대조")
        lines, quotes = check_quotes(R, c, text, CO[c])
        _, _, blocks, _ = parse_md(text)
        check_doc_table(R, c, lines)
        R.p("## 2. 조 태그·조 제목")
        check_tags(R, c, quotes)
        check_titles(R, c, lines, blocks)
        R.p("## 3. 「…」 조각")
        check_frags(R, c, lines, blocks)
        check_toc(R, c, md_lines=lines)
        R.p("## 4. 지시서 항목·추출 범위에 없음")
        check_request(R, c, lines, quotes)
        check_notfound(R, c, lines)
        R.p("")
    R.p("# 보안·형식")
    check_misc(R, list(MD.values()) + list(TOC.values()), texts)
    R.p("")
    R.p(f"문제 {len(R.problems)}건")
    if write:
        os.makedirs(WORK, exist_ok=True)
        open(OUT_TXT, "w", encoding="utf-8").write("\n".join(R.out) + "\n")
        os.makedirs(VD, exist_ok=True)
        json.dump(dict(stats=R.stats, problems=R.problems, detail=R.detail), open(CHECK_JSON, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return R


# ───────────────────────────── 보정(fix) ─────────────────────────────
LOG = {"I": [], "N": []}


def ensure_pre():
    os.makedirs(PRE, exist_ok=True)
    for f in list(MD.values()) + list(TOC.values()):
        dst = os.path.join(PRE, os.path.basename(f))
        if not os.path.exists(dst):
            data = subprocess.run(["git", "show", f"{PRE_COMMIT}:{f}"], capture_output=True, check=True).stdout
            open(dst, "wb").write(data)


def short(s, n=170):
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…"


def diff_window(old, new, ctx=36, lim=320):
    """바뀐 자리 앞뒤 ctx 글자만 — 「…」로 줄인 곳 표시."""
    p = 0
    while p < min(len(old), len(new)) and old[p] == new[p]:
        p += 1
    q = 0
    while q < min(len(old), len(new)) - p and old[-1 - q] == new[-1 - q]:
        q += 1
    a = max(0, p - ctx)

    def win(x):
        e = min(len(x), len(x) - q + ctx)
        w = ("…" if a > 0 else "") + x[a:e] + ("…" if e < len(x) else "")
        return short(w, lim)
    return win(old), win(new)


def rep(c, s, old, new, why, count=1):
    k = s.count(old)
    if k != count:
        raise SystemExit(f"[fix {c}] 바꿀 글이 {k}번 나옴(기대 {count}): {old[:80]!r} — {why}")
    b, a = diff_window(old, new)
    LOG[c].append(dict(why=why + (f"({count}곳)" if count > 1 else ""), before=b, after=a))
    return s.replace(old, new)


def rep_line(c, s, startswith, new_fn, why, count=1):
    """startswith 로 시작하는 줄(들)을 new_fn(줄) 로."""
    lines = s.split("\n")
    hit = [i for i, ln in enumerate(lines) if ln.startswith(startswith)]
    if len(hit) != count:
        raise SystemExit(f"[fix {c}] 줄 머리 {startswith[:50]!r} 가 {len(hit)}번(기대 {count}) — {why}")
    for i in hit:
        old = lines[i]
        lines[i] = new_fn(old)
        LOG[c].append(dict(why=why, before=short(old), after=short(lines[i])))
    return "\n".join(lines)


def tag_tokens(c, raw):
    out = []
    for tok in [x.strip() for x in raw.split(",") if x.strip()]:
        if tok == "목차":
            out.append("조문 목차(지시서 9-4 1.)")
        elif tok == "4·5":
            out.append(f"{jt(4, c)}·{jt(5, c)}")
        elif re.fullmatch(r"\d{1,2}", tok):
            out.append(jt(int(tok), c))
        else:
            raise SystemExit(f"[fix {c}] 조 태그 낱말 {tok!r}")
    return ", ".join(out)


TAG_OLD = re.compile(r"^- 이 글이 닿는 모범규준 조/항목: (.*?) \(조 대응은 판단\)$")
TAG_NEW_HEAD = TAG_PREFIX + "(조 제목은 2016.8.1판): "
TAG_TAIL = " — 글과 조의 대응은 판단(지시서 9-4 에 없는 조 번호는 「(판단)」)"


def fix_tags(c, s):
    lines = s.split("\n")
    n = 0
    first = None
    for i, ln in enumerate(lines):
        m = TAG_OLD.match(ln)
        if not m:
            continue
        new = TAG_NEW_HEAD + tag_tokens(c, m.group(1)) + TAG_TAIL
        if first is None:
            first = (ln, new)
        lines[i] = new
        n += 1
    LOG[c].append(dict(why=f"인용마다 붙은 조 태그 줄 {n}곳을 「N조(조 제목)」 꼴로(지시서 9-4 조 번호는 그대로, 그 밖의 조는 「(판단)」) — 첫 예",
                       before=short(first[0]), after=short(first[1])))
    return "\n".join(lines)


HEADS = [("### 3조 적용대상 — ", "### 3조(적용대상) — "),
         ("### 4조·5조 위험관리 철학·원칙", "### 4조(위험관리 철학)·5조(위험관리 원칙)"),
         ("### 17조 의사전달체계 — ", "### 17조(의사전달체계) — "),
         ("### 21조 신용위험·22조 시장위험·24조 금리위험 — ", "### 21조(신용위험)·22조(시장위험)·24조(금리위험) — "),
         ("### 27조 전략 및 평판위험 — ", "### 27조(전략 및 평판위험) — "),
         ("### 28조·30조 — ", "### 28조(시스템 구축 및 관리)·30조(목적) — "),
         ("### 34조 해외위험 — ", "### 34조(해외위험 관리) — "),
         ("### 53조 위기대응조직 — ", "### 53조(위기대응조직) — "),
         ("### 55조 조기경보 — ", "### 55조(조기경보체계) — ")]


def fix_heads(c, s):
    for old, new in HEADS:
        if old in s:
            s = rep(c, s, old, new, "3장 조별 머리에 조 제목(2016.8.1판)")
    return s


def conv_arts(c, cell):
    cell = cell.strip()
    if cell in ("-", ""):
        return cell
    if cell == "목차":
        return "조문 목차"
    return re.sub(r"(?<![\d조(])(\d{1,2})(?![\d조])", lambda m: jt(int(m.group(1)), c), cell)


def fix_sec5(c, s):
    lines = s.split("\n")
    st = next(i for i, ln in enumerate(lines) if ln.startswith("## 5. 받은 것"))
    en = next(i for i, ln in enumerate(lines) if i > st and ln.startswith("## 6."))
    n = 0
    for i in range(st, en):
        ln = lines[i]
        if not ln.startswith("| ") or ln.startswith("| 구분") or ln.startswith("|---"):
            continue
        cells = ln[2:-2].split(" | ")
        new_last = conv_arts(c, cells[-1])
        if new_last != cells[-1]:
            cells[-1] = new_last
            lines[i] = "| " + " | ".join(cells) + " |"
            n += 1
    lines[st + 2] = lines[st + 2].replace("| 모범규준 조 |", "| 모범규준 조(조 제목, 2016.8.1판) |")
    LOG[c].append(dict(why=f"5장 표 「모범규준 조」 칸 {n}행을 「N조(조 제목)」 꼴로(지시서 밖 조는 「(판단)」)", before="예: 「9·12·27·55」",
                       after="예: 「" + conv_arts(c, "9·12·27·55") + "」"))
    return "\n".join(lines)


# 「추출 범위에 없음」 줄에 붙일 찾은 방법(절·표 행의 조 → 6장 검색어 이름·검증 기록 반박 검색 이름)
NF_KEYS = {"3": ("「3」", "3"), "4·5": ("「4·5」", "4·5"), "17": ("「17」", "17"), "21": ("「21」·「21·22·24(연결·통합)」", "21·22·24"),
           "22": ("「22」·「21·22·24(연결·통합)」", "21·22·24"), "24": ("「24」·「21·22·24(연결·통합)」", "21·22·24"),
           "27": ("「27」", "27"), "34": ("「34」", "34"), "53": ("「53」", "53"), "55": ("「55」", "55"),
           "목차": ("「목차(규정명)」", "규정전문")}


def nf_ptr(key):
    return nf_ptrs([key])


def nf_ptrs(keys):
    a = "·".join(dict.fromkeys(NF_KEYS[k][0] for k in keys))
    b = "·".join(dict.fromkeys(f"「{NF_KEYS[k][1]}」" for k in keys))
    return f"찾은 방법: 6장 {a} 검색어 줄·검증 기록 {b} 반박 검색"


def fix_nf(c, s):
    lines = s.split("\n")
    sec = "목차"
    inblock = False
    n = 0
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            inblock = not inblock
            continue
        if inblock:
            continue
        m = re.match(r"^### (\d+)조", ln)
        if m:
            sec = {"4": "4·5", "28": "목차"}.get(m.group(1), m.group(1))
        elif ln.startswith("## 4.") or ln.startswith("## 1.") or ln.startswith("## 2."):
            sec = "목차"
        if "추출 범위에 없음" not in ln or ln.startswith("- 인용:"):
            continue
        ctx = " ".join(lines[max(0, i - 2): i + 3])
        if NF_METHOD.search(ln) or NF_METHOD.search(ctx):
            continue
        keys = [sec]
        m2 = re.match(r"^\| (3|4·5|17|21|22|24|27|34|53|55) \|", ln)
        named = [x for x in re.findall(r"(?<![\d제~])(\d{1,2})조[,)·]", ln) if x in NF_KEYS]
        if m2:
            keys = [m2.group(1)]
        elif "본문" in ln:
            keys = ["목차"]
        elif named:
            keys = list(dict.fromkeys(named))
        old = ln
        lines[i] = ln.replace("추출 범위에 없음", f"추출 범위에 없음({nf_ptrs(keys)})", 1)
        b, a = diff_window(old, lines[i], ctx=50)
        LOG[c].append(dict(why="「추출 범위에 없음」에 찾은 방법 표시", before=b, after=a))
        n += 1
    return "\n".join(lines)


def cut_lines(key, p1, p2, start, end, start_n=1):
    t = T(key)
    idx = t.page_lines(p1, p2)
    hits = [i for i in idx if start in t.lines[i]]
    if len(hits) < start_n:
        raise SystemExit(f"[cut] 시작 글 없음 {start!r} {key} p.{p1}~{p2}")
    s = hits[start_n - 1]
    e = next((i for i in idx if i >= s and end in t.lines[i]), None)
    if e is None:
        raise SystemExit(f"[cut] 끝 글 없음 {end!r}")
    lines = t.lines[s:e + 1]
    pages = sorted({t.page[i] for i in range(s, e + 1) if not PAGE_RE.match(t.lines[i])})
    return lines, t.plabel(pages[0], pages[-1])


def cite_for(key, plab, jomun=""):
    d = DOCS[key]
    ref = f"접수번호 {d['rcp']} · {d['url']}" if d.get("rcp") else (d["url"] + (f" (방식 {d['method']})" if d.get("method") else ""))
    loc = plab + (f" · {jomun}" if jomun else "")
    return f"- 인용: [{d['name']} · {ref} · {loc} · 원본 수집 {d['fetched'][:10]} · 옮김 {TODAY}]"


def new_quote(c, qid, title, key, p1, p2, start, end, tags, notes, marks=(), start_n=1):
    lines, plab = cut_lines(key, p1, p2, start, end, start_n)
    out = list(lines)
    for anchor, mark in marks:
        j = next(i for i, x in enumerate(out) if anchor in x)
        out.insert(j, mark)
    o = [f"#### [{qid}] {title}", "", cite_for(key, plab),
         TAG_NEW_HEAD + ", ".join(tags) + " — 글과 조의 대응은 판단(검증 2026-10-07 추가 인용)"]
    if key in CORR:
        o.append(CORR_PREFIX + "(공백·쪽 머리말 무시): " + " / ".join(corr_text(key, lines)))
    o += ["", "```text"] + out + ["```", ""] + notes + [""]
    LOG[c].append(dict(why=f"새 인용 [{qid}] 추가(검증 반박 검색에서 찾음)", before="-", after=f"[{qid}] {DOCS[key]['kind']} {plab} — {title}"))
    return "\n".join(o), plab


def insert_before(c, s, anchor, block, why):
    k = s.count(anchor)
    if k != 1:
        raise SystemExit(f"[fix {c}] 끼울 자리 {anchor[:50]!r} 가 {k}번 — {why}")
    return s.replace(anchor, block + "\n" + anchor)


def count_lines(c, pat, r9=True):
    rp = re.compile(pat)
    n8 = n9 = 0
    for k in co_keys(c):
        t = T(k)
        n = sum(1 for ln in t.lines if rp.search(ln))
        if k.startswith("R9_"):
            n9 += n
        else:
            n8 += n
    return n8, n9


def buchik_rows(c, reg):
    """부칙 조 행(CSV 꼴)."""
    name, key = reg[0], reg[1]
    t = T(key)
    d = DOCS[key]
    heads, _, _ = reg_heads(c, reg)
    rows = []
    for h in heads:
        if h["kind"] != "부칙조":
            continue
        body = t.lines[h["line"]].strip()
        note = "부칙 조(검증 2026-10-07 추가) — 모범규준 같은 번호 대조 대상 아님"
        if h["no"] == "제1조":
            note += f"; 본문 「{body[body.index(')') + 1:].strip()}」"
        if h["no"] == "제3조":
            m = re.search(r"제\d+조에서 제\d+조까지", body)
            if m:
                note += f"; 본문 「{m.group(0)}」"
        rows.append(dict(회사=CO[c], 규정명=name, 조번호=buchik_label(h, heads), 조제목=h["title"], 문서=d["name"],
                         접수번호또는URL=d.get("rcp") or d["url"], 쪽=t.plabel(h["page"]), 전문여부="Y(전문 옮김)", 비고=note))
    return rows


def write_toc(c, rows):
    cols = ["회사", "규정명", "조번호", "조제목", "문서", "접수번호또는URL", "쪽", "전문여부", "비고"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\r\n")          # 원 파일과 같은 줄 끝(CRLF)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    open(TOC[c], "w", encoding="utf-8-sig", newline="").write(buf.getvalue())


def fix_csv(c):
    rows = read_csv(os.path.join(PRE, os.path.basename(TOC[c])))
    out = []
    added = 0
    for reg in FULL_REGS[c]:
        pass
    regs = {reg[0]: reg for reg in FULL_REGS[c]}
    i = 0
    while i < len(rows):
        r = rows[i]
        out.append(r)
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if r["규정명"] in regs and (nxt is None or nxt["규정명"] != r["규정명"]):
            br = buchik_rows(c, regs[r["규정명"]])
            out += br
            added += len(br)
            if br:
                LOG[c].append(dict(why=f"조문 목차 CSV — {r['규정명']} 부칙 조 {len(br)}행 추가(원문 쪽마다 대조에서 빠짐)", before="-",
                                   after=f"{br[0]['조번호']}({br[0]['조제목']}) {br[0]['쪽']} … {br[-1]['조번호']}({br[-1]['조제목']}) {br[-1]['쪽']}"))
        i += 1
    if c == "I":
        for r in out:
            if r["규정명"] == "그룹 리스크관리 정책(2025.5 제정)":
                t = T("I_AR")
                pg = [p for p in range(1, t.npages + 1) if "그룹리스크관리정책" in nows("\n".join(t.lines[j] for j in t.page_lines(p)))]
                old = (r["쪽"], r["비고"])
                r["쪽"] = t.plabel(pg[0])
                # 이름이 그대로 적힌 쪽(108·135; p.189 「그룹 리스크관리 정책 및 제도 총괄」은 임원 직무 글이라 뺌)과 「리스크관리 정책 제정」 꼴(28·110·112)
                assert pg[:2] == [108, 135], pg
                r["비고"] = (r["비고"].replace("나오는 쪽 p.28, 110, 112, 135",
                                             "나오는 쪽 p.108·135(「그룹 리스크관리 정책」), p.28·110·112(「리스크관리 정책 제정」 꼴)")
                             + f" (검증 2026-10-07: 쪽 칸을 p.28 → 이름 「그룹 리스크관리 정책」이 그대로 적힌 첫 쪽 {t.plabel(pg[0])} 로)")
                LOG[c].append(dict(why="조문 목차 CSV — 「그룹 리스크관리 정책」 행의 쪽(p.28 에는 「리스크관리 정책 제정(안)」만 있음)",
                                   before=f"{old[0]} · {short(old[1], 80)}", after=f"{r['쪽']} · {short(r['비고'], 160)}"))
    write_toc(c, out)
    return added


def md_buchik_table(c, reg):
    rows = buchik_rows(c, reg)
    o = ["| 규정 | 조 | 조 제목 | 쪽 |", "|---|---|---|---|"]
    for r in rows:
        o.append(f"| {r['규정명']} | {r['조번호']} | {r['조제목']} | {r['쪽']} |")
    return o, rows


# ── 7절·검증 기록 ──
SEC7_I = [
    ("9-4 1.", "조문 목차(1~59조 대응)", "[I-11] 리스크관리규정 전문, 1-2 표(제1장~제10장·제1조~제35조), 1-2-1 부칙 표(검증 추가), [I-8]·[I-9]·[I-10]",
     "받은 글 — 대응 규정 「리스크관리규정」(첨부16) 전문과 전체 조문 목차(본칙 35개 조·10개 장, 부칙 13건 39개 조; 삭제 조 없음 — 검증에서 p.275~289 쪽마다 원문 조 머리와 CSV 를 맞댐)"),
    ("9-4 1. iM", "28조(시스템 구축 및 관리)·30조(목적)", "[I-R7], 1-2 표",
     "받은 글 — 제28조(시스템 구축 및 운영)·제30조(적합성 검증)가 모범규준 28조·30조와 번호가 같음. 원문 규정 이름은 「리스크관리규정」, 제28조 제목은 「시스템 구축 및 운영」(5장)"),
    ("9-4 1. iM 표", "1조~35조 같은 번호 대조", "1-2 표·1-3 표",
     "받은 글 — 같은 번호에 주제도 같은 조 6개(제1·28·29·30·33·34조), 나머지 29개는 번호가 어긋남(판단)"),
    ("9-4 1. 메리츠", "9조(그룹위험관리위원회)·57조(비상계획)", "-", "해당 없음 — 메리츠 파일(9-4_메리츠금융지주.md) 범위"),
    ("9-4 2. 21·22·24", "21조(신용위험)·22조(시장위험)·24조(금리위험)",
     "[I-R3]·[I-R4]·[I-R7]·[I-B2]·[I-B3]·[I-B4]·[I-M1]·[I-M2]·[I-M3](검증 추가)",
     "일부 — 시장(연결실체 바젤Ⅲ 표준방법)·금리(주요 종속기업 IRRBB)·신용(규제자본 표준방법·기본 내부등급법, 검증 추가) 찾은 글. "
     "경제적 자본(위험자본) 기준 통합 신용위험 측정 방법과 「리스크관리지침」 본문은 추출 범위에 없음(찾은 방법: 6장 「21」·「21·22·24(연결·통합)」 줄·검증 기록 「21·22·24」 줄)"),
    ("9-4 2. 27", "27조(전략 및 평판위험)", "[I-R1]·[I-R3]·[I-9]",
     "일부 — 관리대상·정의(제3조·제8조 9·10호), 전략 의사결정 리스크 검토(그룹경영관리협의회규정 제8조 ⑤·⑥, 판단). 측정·평가 수단은 추출 범위에 없음(찾은 방법: 6장 「27」 줄·검증 기록 「27」 줄)"),
    ("9-4 2. 34", "34조(해외위험 관리)", "[I-R9]·[I-R6]·[I-2]",
     "받은 글 — 제34조 ① 총괄 ② 신규 진출 사전 검토·지주 보고 ③ 정기 보고·관리∙감독, 제35조 국가별리스크(「점검」 낱말은 없음, 판단)"),
    ("9-4 2. 3", "3조(적용대상)", "[I-R1]·[I-R4]·[I-R5]",
     "받은 글 — 제2조 단서(리스크가 경미할 경우 그룹위험관리책임자가 적용 배제·일부 적용, 위험관리위원회 보고). 「경미」의 수치 기준은 추출 범위에 없음(찾은 방법: 6장 「3」 줄·검증 기록 「3」 줄)"),
    ("9-4 2. 17", "17조(의사전달체계)", "[I-R6]·[I-7a]", "받은 글 — 제25조 ① 「공식문서(전자문서 포함)로 처리」 1~4호, ② 「서면으로 기록」"),
    ("9-4 2. 55", "55조(조기경보체계)", "[I-R8]·[I-8]·[I-7b]·[I-B1], [I-11](제18조 ② MAT, 검증 note)",
     "일부 — 판단지표·판단기준·위기단계별 조치(제32조), 「위기단계 식별」, 분기 「그룹 리스크단계 보고」, 유동성 조기경보지표 체크리스트. 지표 목록·발령 단계는 추출 범위에 없음(찾은 방법: 6장 「55」 줄·검증 기록 「55」 줄)"),
    ("9-4 2. 53", "53조(위기대응조직)", "[I-R8]·[I-6]·[I-5]·[I-R4]",
     "일부 — 비상조치계획 점검 대상 「위기관리 조직」, 「그룹 위기관리협의회 운영 결과 보고」. 구성·전환 요건은 추출 범위에 없음(찾은 방법: 6장 「53」 줄·검증 기록 「53」 줄; 「그룹 위기관리지침」 위임)"),
    ("9-4 3.", "4조(위험관리 철학)·5조(위험관리 원칙)", "[I-R2]·[I-2]·[I-B2]·[I-3b]·[I-4]",
     "받은 글 — 내규(리스크관리규정 제2장 제5조 리스크 철학·제6조·제7조 리스크관리 원칙 1~7호)에 둠. 2025.5 제정 「그룹 리스크관리 정책」 본문은 추출 범위에 없음(찾은 방법: 6장 「4·5」·「목차(규정명)」 줄·검증 기록 「4·5」·「규정전문」 줄)"),
]
SEC7_N = [
    ("9-4 1.", "조문 목차(1~59조 대응)", "-(대응 규정 아님: [N-9] 리스크관리위원회규정·[N-8] 최고경영자협의회규정 전문, 1-2 표)",
     "추출 범위에 없음 — 그룹 리스크관리 기본 규정 「리스크관리규정」 전문·조문 목차(찾은 방법: 1-1 아래 note·6장 「목차(규정명)」 줄·검증 기록 「규정전문」 줄 — risk9 2023·2024 사업보고서 포함)"),
    ("9-4 1. iM", "28조(시스템 구축 및 관리)·30조(목적)", "-", "해당 없음 — iM 파일(9-4_iM금융지주.md) 범위"),
    ("9-4 1. iM 표", "-", "-", "해당 없음 — iM 파일 범위(NH 는 리스크관리규정 조 번호가 추출 범위에 없어 같은 번호 대조를 못 함)"),
    ("9-4 1. 메리츠", "9조(그룹위험관리위원회)·57조(비상계획)", "-", "해당 없음 — 메리츠 파일(9-4_메리츠금융지주.md) 범위"),
    ("9-4 2. 21·22·24", "21조(신용위험)·22조(시장위험)·24조(금리위험)",
     "[N-B1]~[N-B4]·[N-B7]·[N-B5]·[N-M1]·[N-M2]·[N-M5]·[N-M6]·[N-M7](검증 추가)",
     "일부 — 시장(연결기업 바젤Ⅲ 표준방법 합산, 보험회사 VaR)·금리(자회사별 IRRBB·보험 K-ICS, 비은행 「단순합」)·신용(규제자본 표준방법·내부등급법, 검증 추가) 찾은 글. "
     "경제적 자본(내부자본) 기준 신용위험 측정 방법 서술은 추출 범위에 없음(찾은 방법: 6장 「21」·「21·22·24(연결·통합)」 줄·검증 기록 「21·22·24」 줄)"),
    ("9-4 2. 27", "27조(전략 및 평판위험)", "[N-B5]·[N-8]",
     "일부 — 전략·평판리스크를 계량리스크로 내부자본 관리, 전략 의사결정의 위험관리 검토(판단). 측정 방법·평가 수단은 추출 범위에 없음(찾은 방법: 6장 「27」 줄·검증 기록 「27」 줄)"),
    ("9-4 2. 34", "34조(해외위험 관리)", "[N-B2]·[N-6]·[N-7]·[N-M4]",
     "일부 — 국가별 익스포저 한도, 은행 해외지점 유동성(자회사 수준). 해외진출·해외사업 총괄·사전 검토·정기 점검·보고는 추출 범위에 없음(찾은 방법: 6장 「34」 줄·검증 기록 「34」 줄)"),
    ("9-4 2. 3", "3조(적용대상)", "-(가까운 글 [N-B5] 「내부자본 관리대상은 모든 자회사」)",
     "추출 범위에 없음(찾은 방법: 6장 「3」 줄·검증 기록 「3」 줄)"),
    ("9-4 2. 17", "17조(의사전달체계)", "-(가까운 글 [N-9] 제7조 ⑤·⑥, [N-8] 제6조 ②, [N-12] 리스크관리협의회(검증 추가))",
     "추출 범위에 없음 — 문서 형식(공식문서 등)(찾은 방법: 6장 「17」 줄·검증 기록 「17」 줄)"),
    ("9-4 2. 55", "55조(조기경보체계)", "[N-B6]·[N-7]·[N-M3]",
     "일부 — 유동성 「위험단계 판단지표」, 비상계획 「위험단계 판단 명확화」, NH농협은행 조기경보지표(은행 자회사). 지주 차원 지표 목록·발령 단계는 추출 범위에 없음(찾은 방법: 6장 「55」 줄·검증 기록 「55」 줄)"),
    ("9-4 2. 53", "53조(위기대응조직)", "[N-B6]·[N-5]·[N-5a]·[N-4]·[N-7]",
     "일부 — 유동성 「위험단계별 비상대응 조직」, 자체정상화계획. 지주 위기대응조직의 구성·전환 요건은 추출 범위에 없음(찾은 방법: 6장 「53」 줄·검증 기록 「53」 줄)"),
    ("9-4 3.", "4조(위험관리 철학)·5조(위험관리 원칙)", "-(가까운 글 [N-6]·[N-9]·[N-3a])",
     "추출 범위에 없음 — 철학·원칙 문구(찾은 방법: 6장 「4·5」 줄·검증 기록 「4·5」 줄)"),
]


def section7(c):
    rows = SEC7_I if c == "I" else SEC7_N
    req = dict(REQ_ITEMS)
    o = [f"{SEC7}(검증 {TODAY} 추가)", "",
         "지시서(REQUEST13.md) 9-4 항목마다 이 파일의 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」. 지시서 원문 칸은 지시서 글 그대로.", "",
         "| 지시서 항목 | 지시서 원문(그대로) | 모범규준 조(조 제목) | 이 파일의 받은 글 | 상태 |", "|---|---|---|---|---|"]
    for item, arts, got, st in rows:
        o.append(f"| {item} | {req[item]} | {arts} | {got} | {st} |")
    return o + [""]


# 반박 검색 결과 요약(사람이 맞은 줄을 읽고 적은 판정) — 맞은 줄 수는 refute_hits.json 에서 다시 셈
REFUTE_NOTE = {
    "I": {
        "3": ("실패", "「경미」는 규정 제2조 단서([I-R1])·사업보고서 현금성자산 정의(「가치변동의 위험이 경미한」)뿐, 「미미한」은 제15조 ① 단서. "
                     "수치 기준(자산 비중 등)은 0줄. 판정 그대로(「경미」 수치 기준 추출 범위에 없음)."),
        "4·5": ("해당 없음(이미 찾은 글)", "철학·원칙 문구는 규정 제5조~제7조·연차보고서 p.107·사업보고서 p.442~443 에 이미 옮김. 「그룹 리스크관리 정책」 본문은 다른 기간 정기보고서에도 없음."),
        "17": ("해당 없음(이미 찾은 글)", "제25조 「공식문서(전자문서 포함)」 — 이미 옮김. 다른 문서 형식 서술은 더 없음."),
        "21·22·24": ("성공(신용 — 일부)", "경영공시(2026 상반기) p.67 「신용리스크 … 표준방법 적용 … 기본 내부등급법 적용」 위험가중자산 표와 p.94 「(2) 내부등급법」 "
                                       "(「iM뱅크 기본내부등급법 2021.4.8.」, 「신용평가시스템개발및운영은지주회사리스크관리부에서담당」)을 새 인용 [I-M3]·[I-M2] 로 넣고 21조 판정을 고침. "
                                       "경제적 자본(위험자본) 기준 통합 신용위험 측정 방법은 여전히 추출 범위에 없음."),
        "27": ("실패", "「평판」은 사외이사 평판·평판조회, 「전략적 의사결정」은 그룹경영관리협의회([I-9]), 「비재무」는 ESG·신용평가모형. 측정·평가 수단 0줄."),
        "34": ("해당 없음(이미 찾은 글)", "제34조·제35조·국가별 익스포져 한도는 이미 옮김. 그 밖의 맞은 줄은 해외점포 현황·외화 표·사외이사 경력 등."),
        "53": ("실패", "「위기」·「비상」 줄은 최고경영자 비상계획(경영승계), 그룹 비상조치계획 변경 의결, 「그룹 위기관리협의회 운영 결과 보고」, 통합위기상황분석 — "
                      "위기대응조직의 구성·전환 요건은 0줄(risk9 2023·2024 사업보고서 포함)."),
        "55": ("실패(가까운 글 note 추가)", "새로 본 글은 리스크관리규정 제18조 ② 「손실허용한도에 대해 단계별 관리(MAT: Management Action Triggers)」([I-11] 안) — "
                                       "자회사 트레이딩 손실한도의 단계 관리로 위기 조기경보 지표·발령 단계는 아님(55조 절 note 로 더함, 판단). 그 밖은 리스크단계 보고·위기단계 식별(이미 옮김)·KRI·제재 「경고」."),
        "규정전문": ("해당 없음(전문 있음)", "리스크관리규정 전문은 첨부16 에 있음. 위임 지침(리스크관리지침·그룹위기관리지침 등) 본문은 risk8·risk9 어디에도 0줄 — 이름만."),
    },
    "N": {
        "3": ("실패", "「경미」는 리스크관리위원회규정 제14조 「단순한 자구 수정 등 경미한 사항」, 「적용대상」·「적용범위」는 내부등급법 적용대상·규범 적용범위·윤리강령, "
                     "「모든 자회사」는 내부자본 관리대상([N-B5]). 경미한 자회사 적용 배제 기준 0줄."),
        "4·5": ("실패", "「철학」·「원칙」 줄은 협의회 소집 원칙·자본 산출 원칙 등, 「기본방침」은 위원회 역할([N-6]·[N-9])·risk9 2024 사업보고서 「경영전략에 부합하는 리스크관리 기본방침 및 전략 수립」 — "
                       "위험관리 철학·원칙 문구 0줄."),
        "17": ("실패(가까운 글 추가)", "자회사 낱말과 40자 안의 통보·요구·서면 줄은 감사위원회 자료 요구·이사회 시정권고 권한·위원회규정 제7조 ⑤(이미 옮김) 등. "
                                    "연차보고서 p.217 리스크관리협의회 「자회사 위험관리책임자는 … 구체적인 실행계획을 수립하여 시행」을 가까운 글 [N-12] 로 더함. 「공식문서」·「공문」 0줄, 「전자문서」는 정관 통지·IT보안·소송 자리뿐 — 문서 형식 서술 0줄."),
        "21·22·24": ("성공(신용 — 일부)", "경영공시(2026 상반기) p.71 「신용리스크 … 표준방법 적용 … 기본 내부등급법 적용 … 고급 내부등급법 적용」 위험가중자산 표와 p.95~96 「2) 내부등급법」 "
                                       "(「당사는 2016년말 기업 및 소매 익스포져 등에 대한 기본내부등급법 승인을 획득」, 「내부등급법 적용 대상 자회사는 NH농협은행」, 익스포져별 산출방법 표)을 새 인용 [N-M7]·[N-M6] 로 넣고 21조 판정을 고침. "
                                       "경제적 자본(내부자본) 기준 신용위험 측정 방법은 여전히 추출 범위에 없음."),
        "27": ("실패", "「전략적 경영의사결정」은 최고경영자협의회(이미 옮김 [N-8]), 「비계량」은 보수 평가 지표·비계량리스크(유보자본), 「평판」은 [N-B5]·이사 평판 — 측정 방법 0줄."),
        "34": ("실패", "「해외」·「글로벌」·「외국」·「국가별」 줄은 국가별 익스포저 한도(이미 옮김)·글로벌 사업 서술·외화 표·외국환거래법 제재·2023 이사 교육 「해외사업장 경영현안 점검 및 보고」(사업보고서 p.598, 이사회사무국 내부교육) — "
                      "지주의 해외위험 총괄·사전 검토·정기 점검 0줄."),
        "53": ("실패", "「위기」·「비상」·「정상화」 줄은 자체정상화계획·통합위기상황분석·자본적정성/유동성 비상계획 개정(이미 옮김)·최고경영자 비상계획·PF 정상화펀드 — "
                      "위기대응조직 구성·전환 요건 0줄(risk9 2023·2024 사업보고서의 「위험단계별 비상대응 조직」 문장은 [N-B6] 과 같은 글)."),
        "55": ("실패", "「조기경보모형 모니터링 등급」(사업보고서 p.134·399, 기대신용손실 판단 정보 — 신용 조기경보, 자회사 여신), 「위험단계 판단 명확화」(이미 옮김), 제재 「경고」·손상 「징후」 — "
                      "지주 차원 조기경보 지표 목록·발령 단계 0줄."),
        "규정전문": ("실패", "「리스크관리규정」은 이름(이사회·위원회 안건, 위원회 권한 표)만 — 리스크관리규정 뒤에 조 번호를 붙인 인용도 0줄(규정 이름 + 조 번호 꼴 맞은 줄은 이사회규정·보수위원회규정·감독규정 등). "
                            "첨부 목록 밖 [첨부7] 까지 「제1조 (목적)」 머리를 모두 셈 — 리스크관리규정 없음."),
    },
}


def refute_summary(c):
    if not os.path.exists(REFUTE_JSON):
        raise SystemExit("refute_hits.json 없음 — 먼저 `refute` 실행")
    J = json.load(open(REFUTE_JSON, encoding="utf-8"))
    o = []
    for jo, (res, txt) in REFUTE_NOTE[c].items():
        rec = J["조"][jo]
        ks = [k for k in rec["문서"] if rec["문서"][k]["name"].startswith(CO[c])]
        n8 = sum(rec["문서"][k]["n"] for k in ks if not k.startswith("R9_"))
        nn = sum(rec["문서"][k]["n_new"] for k in ks if not k.startswith("R9_"))
        r9 = [k for k in ks if k.startswith("R9_")]
        n9 = sum(rec["문서"][k]["n"] for k in r9)
        pat = rec["검색어"]
        extra = ""
        if rec.get("ctx"):
            extra += f", 같은 창 낱말 `{rec['ctx']}`"
        if rec.get("near"):
            extra += ", 자회사 낱말과 40자 안"
        if rec.get("뺀말"):
            extra += f", 뺀 말 `{rec['뺀말']}`"
        o.append(f"- 「{jo}」 ({rec['label']}) — **{res}** — {txt} 검색어 `{pat}`{extra} — 맞은 줄 risk8 {n8}줄(이미 인용한 쪽 밖 {nn}줄), "
                 f"risk9 {n9}줄({len(r9)}개 보고서: {', '.join(DOCS[k]['rcp'] for k in r9)}).")
    return o


def verification_record(c, pre_stats, added_csv):
    st = pre_stats
    log = LOG[c]
    o = [VREC, "",
         f"대조 스크립트 `scripts/dart/verify13_g_im_nh.py`(인자 없이 = 대조, `refute` = 반박 검색, `fix` = 이 보정), 결과 `{OUT_TXT}`. "
         f"검증 전 사본은 `{PRE}/`(커밋 {PRE_COMMIT} 의 파일 그대로), 반박 검색 원자료는 같은 폴더 `refute_hits.json`(git 무시 폴더). 웹 요청·API 키·OC 를 쓰지 않음(로컬 텍스트만).", "",
         "### 대조한 인용", "",
         f"- 검증 전 원문 인용 {st['quotes']}건(코드 블록; 「>」 인용 블록 0건)을 「- 인용:」 줄이 가리킨 텍스트(`dart_out/text/risk8/`)의 그 쪽과 대조 — "
         f"「[표 깨짐: …]」 등 이 작업이 끼운 표시 줄만 빼고 원본 줄과 글자 그대로 같은 것 {st['exact']}건, 공백 무시로도 다른 것 0건. "
         f"쪽 표기(PDF 쪽·인쇄 쪽·DART 쪽), 문서명·공시일(dart_out/risk8/연차보고서_FY2025.csv·경영공시 meta.json·dart_out/risk9/텍스트목록.csv), 접수번호·URL·방식, 원본 수집일, 옮김 날짜, "
         f"「추가공시·정정판 대조」 줄(다시 계산), 0-1 문서 표의 sha256·쪽수·수집 시각도 대조 — 틀린 곳 {st['bad']}건" + (f"({st['bad_list']})" if st["bad"] else "") + ".",
         f"- 검증 뒤 원문 인용은 모두 {st['post_quotes']}건(검증 추가 인용 포함) — 같은 방식으로 다시 대조해 모두 일치(대조 결과 파일).",
         f"- 「…」 조각(note·표·판정 줄) {st['frags']}개를 회사 원문·모범규준 원문(9-4_모범규준_원문.md)·지시서·메타 제목과 공백 무시로 대조 — 원문과 다른 조각은 아래 「고친 곳」.",
         f"- 조문 목차 CSV: 전문을 옮긴 규정마다 원문 쪽마다 장·조·부칙 머리(삭제 조·「제N조의M」 꼴 포함)를 다시 뽑아 CSV 와 하나씩 맞댐 — 결과는 대조 결과 파일 「쪽마다」 줄. "
         f"검증 전 CSV 에 빠진 것은 부칙 조뿐(삭제 조·「제N조의M」 조 없음) → {added_csv}행 추가.", "",
         "### 고친 곳(전 → 후)", ""]
    for x in log:
        o.append(f"- {x['why']}: 「{x['before']}」 → 「{x['after']}」")
    o += ["", "### 채운 항목", ""]
    o += FILLED[c]
    o += ["", "### 「추출 범위에 없음」 반박 시도", "",
          f"같은 출처(dart_out/text/risk8 의 이 회사 연차보고서 본공시·추가공시·사업보고서·경영공시 전체)와 `dart_out/text/risk9/` 의 같은 회사 다른 기간 정기보고서 전체를 "
          f"수집 에이전트 6장 검색어보다 넓힌 정규식(낱말 변형·띄어쓰기 `\\s*`·영문·동의어)으로 줄 단위 + 줄바꿈으로 갈린 낱말까지 다시 찾고, 맞은 줄을 읽어 판정함. "
          f"risk9 의 FY2025 사업보고서 텍스트는 risk8 과 sha256 이 같아 risk8 쪽으로만 셈.", ""]
    o += refute_summary(c)
    o += ["", "### 남은 문제", ""]
    o += REMAIN[c]
    return o


FILLED = {
    "I": ["- 「7. 지시서 항목별 대조(검증 2026-10-07 추가)」 절 — 지시서 9-4 항목 12개마다 받은 글 또는 「추출 범위에 없음 + 찾은 방법」.",
          "- 1-2-1 리스크관리규정 부칙 조문 표와 조문 목차 CSV 부칙 39행(부칙 13건 × 제1조~제3조).",
          "- 새 인용 [I-M3](경영공시 p.67 리스크별 위험가중자산 — 표준방법·기본 내부등급법), [I-M2](경영공시 p.94 내부등급법 승인·통제·보고) — 21조.",
          "- 55조 절 note — 제18조 ② MAT(가까운 글, 판단).",
          "- 인용마다 「이 글이 닿는 모범규준 조」를 「N조(조 제목)」으로(지시서 조 번호는 그대로, 그 밖은 「(판단)」), 3장 조별 머리·5장 표에 조 제목."],
    "N": ["- 「7. 지시서 항목별 대조(검증 2026-10-07 추가)」 절 — 지시서 9-4 항목 12개마다 받은 글 또는 「추출 범위에 없음 + 찾은 방법」.",
          "- 조문 목차 CSV·1-2 표에 리스크관리위원회규정 부칙 조 2행(부칙(1/5) 제1조·제2조).",
          "- 새 인용 [N-M7](경영공시 p.71 리스크별 위험가중자산), [N-M6](경영공시 p.95~96 내부등급법 승인·익스포져별 산출방법) — 21조; [N-12](연차보고서 p.217 리스크관리협의회 역할·협의절차) — 17조 가까운 글.",
          "- 인용마다 「이 글이 닿는 모범규준 조」를 「N조(조 제목)」으로(지시서 조 번호는 그대로, 그 밖은 「(판단)」), 3장 조별 머리·5장 표에 조 제목."],
}
REMAIN = {
    "I": ["- 「그룹 리스크관리 정책」(2025.5 제정) 본문과 위임 지침(리스크관리지침·그룹위기관리지침·통합위기상황분석 관리 지침·국가별위험관리지침 등) 본문은 공시 자료에 없음 — "
          "53조 구성·전환 요건, 55조 지표 목록·발령 단계, 21조 경제적 자본 측정 방법, 3조 「경미」 수치 기준은 회사 자료 요청 등 다른 출처가 필요.",
          "- 경영공시 텍스트는 FY2025 말 판이 아니라 2026년 상반기 판([I-M1]~[I-M3]). iM 경영공시 p.94 등은 PDF 글자 간격이 깨져 띄어쓰기가 원본 화면과 다를 수 있음(글자는 텍스트 그대로 옮김).",
          "- 1-2·1-3 표의 주제 대응, 「연결」로 읽은 경영공시 위험가중자산 표, MAT 의 55조 대응은 눈으로 맞댄 판단.",
          "- 원문 PDF 화면과의 대조는 하지 않음(텍스트 추출본 기준)."],
    "N": ["- 그룹 리스크관리 기본 규정 「리스크관리규정」·「리스크관리준칙」·비상계획 본문이 공시 자료(연차보고서 첨부 1~7, 사업보고서, 경영공시, risk9 정기보고서)에 없음 — "
          "모범규준 같은 번호 대조, 3·4·5·17조 문구, 53조 구성·전환 요건, 55조 지표 목록·발령 단계는 회사 자료 요청 등 다른 출처가 필요.",
          "- 경영공시 텍스트는 FY2025 말 판이 아니라 2026년 상반기 판([N-M1]~[N-M7]).",
          "- 원문 PDF 화면과의 대조는 하지 않음(텍스트 추출본 기준)."],
}


# ── 회사별 보정 ──
def fix_im(s):
    c = "I"
    for old in ["제1장~제10장, 제1조~제35조, 부칙 12건. 제정", "리스크관리규정 전문(제1장~제10장, 제1조~제35조, 부칙 12건)",
                "note: 부칙 12건 가운데", "리스크관리규정 전문(제1~35조, 부칙 12건)"]:
        s = rep(c, s, old, old.replace("부칙 12건", "부칙 13건"), "부칙 수 — 원문 p.287~289 「부  칙」 13건(시행일 2011.5.17~2024.1.1, 제정 1 + 개정 12)")
    # 1-2-1 부칙 표
    tbl, rows = md_buchik_table(c, FULL_REGS["I"][0])
    block = ["### 1-2-1 리스크관리규정 부칙 조문(검증 2026-10-07 추가)", "",
             f"원문 p.287~289 의 부칙 13건(각 제1조 시행일·제2조 자회사 등 리스크관리 관련 규정·제3조 리스크 측정에 대한 유예) — 조문 목차 CSV 에 같은 {len(rows)}행을 더함. "
             "본칙(제1장~제10장, 제1조~제35조)은 1-2 표 그대로이며 삭제 조·「제N조의M」 꼴 조는 원문에 없음(쪽마다 대조, 검증 기록).", ""] + tbl + [""]
    s = insert_before(c, s, "### 1-3 모범규준 조(3~58) → iM 리스크관리규정 대응 조(판단)", "\n".join(block), "1-2-1 부칙 표")
    LOG[c].append(dict(why="1-2-1 부칙 조문 표 추가", before="-", after=f"{len(rows)}행(부칙(1/13) 제1조 … 부칙(13/13) 제3조)"))
    # 조 제목 표기
    s = rep(c, s, "57조(비상계획)·55조(판단지표)·58조(정기 점검)", "57조(비상계획)·55조(조기경보체계: 판단지표)·58조(위기관리체계의 정기적 점검)",
            "1-2 표 — 조 제목을 조목록(2016.8.1판) 제목으로")
    s = rep(c, s, "모범규준 제5장(내부자본 적정성, 36~49조)과 21~27조(유형별 측정)는",
            "모범규준 제5장(내부자본 적정성 평가 및 관리, 36~49조)과 제4장 제2절(위험 유형별 측정 및 관리, 21~27조)은", "1-2 note — 장·절 이름을 조목록 표기로")
    s = rep(c, s, "(③ 「연수 등으로 전파」에 해당하는 문구는 없음)", "(③ 「연수 등의 방법을 통해 위험관리 철학을 그룹 전체에 전파」에 해당하는 문구는 없음)",
            "1-3 표 — 모범규준 4조 ③ 인용을 원문 글로(9-4_모범규준_원문.md 5장)")
    s = rep(c, s, "「위기상황분석 주요사항(반기1회 이상) 가. 위기단계 식별 …」", "「위기상황분석 주요사항(반기1회 이상) <신설 2017.03.01.> 가. 위기단계 식별 …」",
            "[I-8] note — 원문에 있는 「<신설 2017.03.01.>」을 빠뜨린 인용을 원문 글로(p.245)")
    s = rep(c, s, "모범규준 34조 ④ 「지주는 자회사의 해외위험 관리실태를 정기적으로 점검」에", "모범규준 34조 ④ 「금융지주회사는 자회사의 해외위험 관리실태를 정기적으로 점검」에",
            "34조 note — 모범규준 34조 ④ 인용을 원문 글로")
    s = rep(c, s, "「임원보상체계운용기준/지침」", "「임원보상체계운용기준」/「임원보상체계운용지침」", "6장 note — 두 낱말을 원문 표기 그대로 나눔")
    # 21조 — 반박 성공: 새 인용 2건
    q3, l3 = new_quote(c, "I-M3", "경영공시 — 사. 리스크별 익스포져 및 위험가중자산, 요구자본 현황 (가) 신용리스크 산출 방법별 행(2026년 반기말)", "I_MD", 67, 67,
                       "사. 리스크별 익스포져 및 위험가중자산, 요구자본 현황", "5 고급 내부등급법 적용", [jt(21, c)],
                       ["note: (검증 추가) 그룹 신용리스크 위험가중자산을 「표준방법 적용」·「기본 내부등급법 적용」으로 나눠 산출 — 지주 경영공시의 BIS 표라 연결(그룹) 기준 규제자본 측정으로 봄(21조 ②·③, 판단). "
                        "「(1) 자본적정성 평가방법」 아래는 「-」만 있음."])
    q2, l2 = new_quote(c, "I-M2", "경영공시 — 리스크관리 (2) 내부등급법 (가)~(아) 승인사항·통제 기준·보고 범위", "I_MD", 94, 94,
                       "(2) 내부등급법", "을 실시하고적 합성검증결과는", [jt(21, c), jt(30, c, judge=True)],
                       ["note: (검증 추가) 내부등급법 적용 자회사는 「iM뱅크 기본내부등급법 2021.4.8.」, 「신용평가시스템개발및운영은지주회사리스크관리부에서담당」, 적합성검증은 「지주회사리스크 검증팀(은행겸직)」 — "
                        "지주가 그룹 신용위험 측정 체계(규제자본)를 운영한다는 서술(21조, 30조 적합성 검증과도 닿음, 판단). 경제적 자본(위험자본) 기준 통합 신용위험 측정 방법은 여기에도 없음."],
                       marks=[("(2) 내부등급법", "[추출 깨짐: 이 쪽은 PDF 글자 간격이 깨져 띄어쓰기가 빠지거나 낱말 안에 끼어 추출됨 — 글자는 텍스트 그대로]"),
                              ("그룹사 BIS 산출방법", "[표 깨짐: 「그룹사/BIS 산출방법/익스포져 구분/승인 날짜」 표의 칸이 줄로 풀려 이어짐 — 표 뒤 (가) 문장의 「아래」가 이 표]")])
    s = insert_before(c, s, "### 27조 전략 및 평판위험 — 관리 체제, 측정·평가 수단", q3 + "\n" + q2, "21조 절 끝에 새 인용")
    old21 = ("신용위험은 사업보고서 (3) ERMS 문장([I-B2], 4조·5조 절에 옮김)과 규정 제15조 ② 8·10호(그룹 신용리스크 내부등급법 통할, 그룹 신용위험요소)뿐 — "
             "「연결기준 신용익스포져로 통합 측정」 서술은 추출 범위에 없음.")
    new21 = ("신용위험은 사업보고서 (3) ERMS 문장([I-B2], 4조·5조 절에 옮김)과 규정 제15조 ② 8·10호(그룹 신용리스크 내부등급법 통할, 그룹 신용위험요소), "
             "그리고 검증(2026-10-07) 반박 검색에서 찾은 경영공시 규제자본 산출 — 그룹 신용리스크 위험가중자산을 「표준방법 적용」·「기본 내부등급법 적용」으로 나눠 산출([I-M3]), "
             "「iM뱅크 기본내부등급법 2021.4.8.」 승인·「신용평가시스템개발및운영은지주회사리스크관리부에서담당」([I-M2]). "
             "모범규준 21조 ③ 「연결기준의 신용익스포져를 대상으로 통합 신용위험을 측정」에 해당하는 경제적 자본(위험자본) 기준 측정 방법 서술은 추출 범위에 없음"
             "(찾은 방법: 6장 「21」·「21·22·24(연결·통합)」 검색어 줄·검증 기록 「21·22·24」 반박 검색).")
    s = rep(c, s, old21, new21, "21조 판정 — 반박 성공(경영공시 규제자본 신용위험 산출 방법), 모범규준 21조 ③ 인용을 원문 글로")
    s = rep(c, s, "[I-B2] ERMS 「규제기준의 신용, 시장, 운영리스크량을 측정.분석」. 연결 기준 통합 신용위험 측정 서술은 추출 범위에 없음 |",
            "[I-B2] ERMS 「규제기준의 신용, 시장, 운영리스크량을 측정.분석」; [I-M3]·[I-M2] 경영공시 신용리스크 위험가중자산 「표준방법 적용」·「기본 내부등급법 적용」, "
            "「iM뱅크 기본내부등급법 2021.4.8.」(검증 추가). 경제적 자본 기준 통합 신용위험 측정 서술은 추출 범위에 없음(찾은 방법: 6장 「21」 검색어 줄·검증 기록 「21·22·24」 반박 검색) |",
            "0장 21조 행 — 반박 성공 반영")
    s = rep(c, s, "| 21 | 신용위험 | iM금융지주 | 일부(측정은 지침 위임, 그룹 시스템 산출) | 연차보고서 p.277~278; 연차보고서 p.280~281; 사업보고서 p.442~443(DART 쪽 440~441) |",
            f"| 21 | 신용위험 | iM금융지주 | 일부(측정은 지침 위임, 그룹 시스템 산출, 규제자본 산출 방법 — 검증 추가) | 연차보고서 p.277~278; 연차보고서 p.280~281; 사업보고서 p.442~443(DART 쪽 440~441); 경영공시 {l3}; 경영공시 {l2} |",
            "0장 21조 행 — 판정·문서 쪽")
    s = rep(c, s, "| 받지 못한 것 | 연결 기준 통합 신용위험 측정 방법, 「리스크관리지침」 본문 |",
            "| 받은 것 | 규제자본(BIS) 신용리스크 위험가중자산 산출 방법(표준방법·기본 내부등급법, iM뱅크 승인)·지주 리스크관리부 신용평가시스템 운영(검증 추가) | "
            f"경영공시 {l3}·{l2} [I-M3]·[I-M2] | 21 |\n| 받지 못한 것 | 경제적 자본(위험자본) 기준 통합 신용위험 측정 방법, 「리스크관리지침」 본문 |",
            "5장 — 반박 성공 반영(받은 것 행 추가, 받지 못한 것 항목 좁힘)")
    # 55조 — MAT note
    s = rep(c, s, "note: 사업보고서·연차보고서의 다른 맞은 줄은 운영위험 「핵심리스크지표 모니터링」(연결 주석 40-5, 운영위험 KRI) 등 — 위기 조기경보 지표 목록이 아님(판단).",
            "note: 사업보고서·연차보고서의 다른 맞은 줄은 운영위험 「핵심리스크지표 모니터링」(연결 주석 40-5, 운영위험 KRI) 등 — 위기 조기경보 지표 목록이 아님(판단).\n"
            "note: (검증 추가) 리스크관리규정 제18조 ② 「손실허용한도에 대해 단계별 관리(MAT: Management Action Triggers)를 시행할 수 있다.」([I-11] p.281) — "
            "자회사 트레이딩 등 관리대상 자산의 손실한도 단계 관리로, 그룹 위기 조기경보 지표·발령 단계는 아님(55조 가까운 글, 판단). 더 넓힌 검색어로도 지표 목록·발령 단계는 찾지 못함(검증 기록 「55」).",
            "55조 note — 반박 검색에서 본 MAT(가까운 글)")
    return s


def fix_nh(s):
    c = "N"
    # [N-11] 조문 표기
    t = T("N_AR")
    i11 = next(i for i, ln in enumerate(t.lines) if re.match(r"^\s*제11조 \(부의사항\)", ln))
    i8 = next(i for i in range(i11, len(t.lines)) if "8. 기타사항(2016.09.30. 개정)" in t.lines[i])
    s = rep(c, s, " · p.288(인쇄 282) · 이사회규정 제10조(추정) · ", " · p.288(인쇄 282) · 이사회규정 제11조 · ",
            f"[N-11] 출처 조문 표기 — 원문 {t.plabel(t.page[i11])} 「제11조 (부의사항)」 ② 결의사항 「8. 기타사항」({t.plabel(t.page[i8])}) 아래 목(「제10조 (회의)」는 한 줄짜리 조)")
    s = rep(c, s, "note: 조 번호는 p.287~288 위쪽에 있어 이 인용에 없음(「8. 기타사항」 아래 목).",
            f"note: 조 번호는 인용 밖 {t.plabel(t.page[i11])} 「제11조 (부의사항)」 ② 「결의사항은 다음 각 호로 한다.」의 「8. 기타사항(2016.09.30. 개정)」({t.plabel(t.page[i8])}) 아래 목 — "
            "검증(2026-10-07)에서 원문 조 머리로 확인해 인용 줄의 「제10조(추정)」을 「제11조」로 바로잡음.", "[N-11] note — 조 번호 자리")
    # 「…」 조각을 원문 글로
    s = rep(c, s, "「역사적 시뮬레이션 모형 VaR」", "「역사적 시뮬레이션 모형에 의하여 VaR를 측정」", "「…」 조각을 원문 글로(사업보고서 p.572)", count=2)
    s = rep(c, s, "「바젤Ⅲ 표준방법 … 다만 보험회사는 VaR」", "「바젤Ⅲ 표준방법 … 다만, 연결기업 중 보험회사의 경우 VaR(Value at Risk)를 적용」", "「…」 조각을 원문 글로(사업보고서 p.282)")
    s = rep(c, s, "「바젤Ⅲ 표준방법 … 보험회사 VaR」", "「바젤Ⅲ 표준방법 … 보험회사의 경우 VaR(Value at Risk)를 적용」", "「…」 조각을 원문 글로(사업보고서 p.282)")
    s = rep(c, s, "관련규정 목록은 「첨부 1~6」인데", "관련규정 목록은 첨부 1~6 뿐인데", "원문 글이 아닌 낫표 표기를 풀어 씀(목록은 [N-1b])")
    s = rep(c, s, "「연결 기준 신용익스포져로 통합 측정」이라는 서술은 추출 범위에 없음(21조, 판단).",
            "모범규준 21조 ③ 「연결기준의 신용익스포져를 대상으로 통합 신용위험을 측정」에 해당하는 경제적 자본 기준 서술은 추출 범위에 없음(21조, 판단; 규제자본 산출 방법은 [N-M7]·[N-M6], 검증 추가).",
            "[N-B2] note — 「…」 조각을 모범규준 원문 글로")
    # 1-2 표 부칙 조
    tbl, rows = md_buchik_table(c, FULL_REGS["N"][0])
    last = "| 리스크관리위원회규정([첨부5] 각 위원회 규정 중) | 제14조 | 규정의 개폐 | p.313(인쇄 307) |"
    s = rep(c, s, last, last + "\n" + "\n".join(tbl[2:]), "1-2 표 — 리스크관리위원회규정 부칙 조 2행(검증 추가)")
    # 21조 — 반박 성공: 새 인용
    q7, l7 = new_quote(c, "N-M7", "경영공시 — 5) 리스크별 익스포저 및 위험가중자산, 요구자본 현황: 신용리스크 산출 방법별 행(2026년 상반기 말)", "N_MD", 71, 71,
                       "5) 리스크별 익스포저 및 위험가중자산, 요구자본 현황", "5 고급 내부등급법 적용", [jt(21, c)],
                       ["note: (검증 추가) 신용리스크 위험가중자산을 「표준방법 적용」·「기본 내부등급법 적용」·「고급 내부등급법 적용」으로 나눠 산출 — 지주 경영공시의 BIS 표라 연결(그룹) 기준 규제자본 측정으로 봄(21조 ②·③, 판단)."])
    q6, l6 = new_quote(c, "N-M6", "경영공시 — 라. 측정방법별 현황 2) 내부등급법 가) 승인받은 산출방법·익스포져별 산출방법 및 승인사항", "N_MD", 95, 96,
                       "2) 내부등급법", "주2) 단계적 적용 대상은 감독당국과 협의 후 내부등급법 적용 가능", [jt(21, c)],
                       ["note: (검증 추가) 「당사는 2016년말 기업 및 소매 익스포져 등에 대한 기본내부등급법 승인을 획득하였으며,」 「내부등급법 적용 대상 자회사는 NH농협은행입니다.」 — "
                        "지주(당사)가 그룹 신용리스크를 규제기준 방법(익스포져별 표준방법·기본 내부등급법)으로 산출한다는 서술(21조 ②, 판단). 경제적 자본(내부자본) 기준 측정 방법은 여기에도 없음."],
                       marks=[("[ 익스포져별 산출방법 및 승인사항 ]", "[표 깨짐: 「익스포져별 산출방법 및 승인사항」 표(익스포져 구분/산출방법 및 승인사항)의 칸이 줄로 풀려 이어짐 — 예: 「대기업 기본 내부등급법중소기업」]")])
    s = insert_before(c, s, "### 27조 전략 및 평판위험 — 관리 체제, 측정·평가 수단", q7 + "\n" + q6, "21조 절 끝에 새 인용")
    s = rep(c, s, "신용위험은 한도 관리 서술만([N-B2]) — 연결 기준 통합 측정 서술은 추출 범위에 없음.",
            "신용위험은 한도 관리 서술([N-B2])과, 검증(2026-10-07) 반박 검색에서 찾은 경영공시 규제자본 산출 — 신용리스크 위험가중자산을 「표준방법 적용」·「기본 내부등급법 적용」·「고급 내부등급법 적용」으로 나눠 산출([N-M7]), "
            "「당사는 2016년말 기업 및 소매 익스포져 등에 대한 기본내부등급법 승인을 획득」·「내부등급법 적용 대상 자회사는 NH농협은행」·익스포져별 산출방법 표([N-M6]). "
            "모범규준 21조 ③ 「연결기준의 신용익스포져를 대상으로 통합 신용위험을 측정」에 해당하는 경제적 자본(내부자본) 기준 측정 방법 서술은 추출 범위에 없음"
            "(찾은 방법: 6장 「21」·「21·22·24(연결·통합)」 검색어 줄·검증 기록 「21·22·24」 반박 검색).",
            "21조 판정 — 반박 성공(경영공시 규제자본 신용위험 산출 방법)")
    s = rep(c, s, "| 21 | 신용위험 | NH농협금융지주 | 일부(한도 관리 서술, 측정 방법 없음) | 사업보고서 p.280(DART 쪽 278); 사업보고서 p.264(DART 쪽 262); 경영공시 p.101 |",
            f"| 21 | 신용위험 | NH농협금융지주 | 일부(한도 관리 서술, 규제자본 산출 방법 — 검증 추가) | 사업보고서 p.280(DART 쪽 278); 사업보고서 p.264(DART 쪽 262); 경영공시 p.101; 경영공시 {l7}; 경영공시 {l6} |",
            "0장 21조 행 — 판정·문서 쪽")
    s = rep(c, s, "[N-M5] 자회사 신용평가시스템 변경을 지주 리스크관리부가 사전협의. 연결 기준 통합 측정 서술은 추출 범위에 없음 |",
            "[N-M5] 자회사 신용평가시스템 변경을 지주 리스크관리부가 사전협의; [N-M7]·[N-M6] 경영공시 신용리스크 위험가중자산 「표준방법 적용」·「기본 내부등급법 적용」, "
            "「내부등급법 적용 대상 자회사는 NH농협은행」(검증 추가). 경제적 자본 기준 통합 측정 서술은 추출 범위에 없음(찾은 방법: 6장 「21」 검색어 줄·검증 기록 「21·22·24」 반박 검색) |",
            "0장 21조 행 — 반박 성공 반영")
    s = rep(c, s, "| 받지 못한 것 | 연결 기준 통합 신용위험 측정 방법 |",
            f"| 받은 것 | 규제자본(BIS) 신용리스크 위험가중자산 산출 방법(표준방법·내부등급법, 내부등급법 적용 자회사 NH농협은행)(검증 추가) | 경영공시 {l7}·{l6} [N-M7]·[N-M6] | 21 |\n"
            "| 받지 못한 것 | 경제적 자본(내부자본) 기준 통합 신용위험 측정 방법 |", "5장 — 반박 성공 반영")
    # 17조 — 가까운 글 [N-12]
    q12, l12 = new_quote(c, "N-12", "리스크관리협의회 — 가. 역할, 나. 협의절차(운영현황)", "N_AR", 217, 217, "가. 역할", "리스크관리협의회에 보고하여야 합니다.",
                         [jt(17, c), jt(12, c)],
                         ["note: (검증 추가) 「자회사 위험관리책임자는 리스크관리협의회에서 실행하기로 한 의결 및 보고 사항에 대해」 「구체적인 실행계획을 수립하여 시행하여야 하며」, "
                          "이행되지 않으면 사유를 협의회에 보고 — 모범규준 17조 ③(자회사의 전달사항 이행·협의)과 닿는 운영 서술(판단). 「부득이한 경우 서면으로 운영」은 협의회 회의 방식이며 "
                          "지주→자회사 전달 문서 형식(17조 ②의 「공식문서」)은 여기에도 없음(판단)."])
    no8, no9 = count_lines(c, r"공식\s*문서|공문")
    ne8, ne9 = count_lines(c, r"전자\s*문서")
    s = insert_before(c, s, "### 21조 신용위험·22조 시장위험·24조 금리위험 — 지주 차원 측정 방법과 연결 측정 여부", q12, "17조 절에 새 인용")
    s = rep(c, s, "6장 「17」 검색 맞은 줄: 연차보고서 29줄(p.16, 98, 153-154, 188, 196, 217, 221, 257-258, 263, 280, 284, 286-287, 303, 306, 308, 312), 사업보고서 19줄(p.150, 261, 278, 306, 405, 445, 510, 577, 642, 644, 646-647, 660).",
            "6장 「17」 검색 맞은 줄: 연차보고서 29줄(p.16, 98, 153-154, 188, 196, 217, 221, 257-258, 263, 280, 284, 286-287, 303, 306, 308, 312), 사업보고서 19줄(p.150, 261, 278, 306, 405, 445, 510, 577, 642, 644, 646-647, 660).\n"
            f"note: (검증 추가) 더 넓힌 검색어(검증 기록 「17」)로 다시 찾아 연차보고서 {l12} 리스크관리협의회 서술을 가까운 글 [N-12] 로 더함 — 문서 형식은 없음. "
            f"모범규준 17조 ② 낱말 「공식문서」·「공문」은 NH risk8 4개 문서 {no8}줄, risk9 정기보고서 2건 {no9}줄. 「전자문서」 {ne8}줄(risk8)·{ne9}줄(risk9)은 "
            "정관의 주주총회 소집·감사 관련 통지(연차보고서 p.257·263, 추가공시 p.265·271), IT보안시스템(사업보고서 p.660), 소송 내용 — 지주→자회사 전달 문서와 무관(판단).",
            "17조 절 — 반박 시도 결과·[N-12]")
    s = rep(c, s, "가까운 글: [N-9] 리스크관리위원회규정 제7조 ⑤ 「자회사에 지체없이 통보」·⑥ 사전 협의; [N-8] 최고경영자협의회규정 제6조 ② 「필요한 조치」 — 문서 형식 없음(판단) |",
            "가까운 글: [N-9] 리스크관리위원회규정 제7조 ⑤ 「자회사에 지체없이 통보」·⑥ 사전 협의; [N-8] 최고경영자협의회규정 제6조 ② 「필요한 조치」; "
            "[N-12] 리스크관리협의회 「구체적인 실행계획을 수립하여 시행하여야 하며」(검증 추가) — 문서 형식 없음(판단) |", "0장 17조 행 — [N-12]")
    s = rep(c, s, "| 17 | 의사전달체계 | NH농협금융지주 | 추출 범위에 없음(문서 형식) | 연차보고서 p.310~313(인쇄 304~307); 연차보고서 p.333~334(인쇄 327~328)(가까운 글) |",
            f"| 17 | 의사전달체계 | NH농협금융지주 | 추출 범위에 없음(문서 형식) | 연차보고서 p.310~313(인쇄 304~307); 연차보고서 p.333~334(인쇄 327~328); 연차보고서 {l12}(가까운 글) |",
            "0장 17조 행 — 문서 쪽")
    return s


def fix_common_head(c, s):
    old = "모범규준 조 번호·제목은 2016.8.1 판(`dart_out/risk13/모범규준_조목록.csv`, 원문은 `9-4_모범규준_원문.md` 5장)."
    new = (old + "\n- 조 태그(검증 2026-10-07 보정): 인용마다 「이 글이 닿는 모범규준 조」를 「N조(조 제목)」으로 적음 — 지시서 9-4 에 적힌 조 번호"
           + ("(3·4·5·17·21·22·24·27·34·53·55, iM 사용자 표 28·30)" if c == "I" else "(3·4·5·17·21·22·24·27·34·53·55)")
           + "는 그대로, 이 작업이 붙인 조는 「(판단)」. 「[추출 깨짐: …]」 줄도 이 작업이 끼운 표시(원문 아님). "
           "검증 기록은 맨 끝 「검증 기록(2026-10-07)」, 대조 스크립트 `scripts/dart/verify13_g_im_nh.py`, 지시서 항목별 대조는 7절.")
    return rep(c, s, old, new, "머리 — 조 태그 규칙·검증 기록 안내")


def fix():
    ensure_pre()
    load_meta()
    for c in CO:
        LOG[c].clear()
    pre_stats = {}
    for c in CO:
        R0 = Report()
        pre_text = open(os.path.join(PRE, os.path.basename(MD[c])), encoding="utf-8").read()
        check_quotes(R0, c, pre_text, CO[c])
        bad = [x.split(" ", 1)[1] for x in R0.problems if "[" in x]
        pre_stats[c] = dict(quotes=R0.stats[c + "_quotes"], exact=R0.stats[c + "_exact"], bad=len(bad), bad_list="; ".join(x[:200] for x in bad))
    for c in CO:
        s = open(os.path.join(PRE, os.path.basename(MD[c])), encoding="utf-8").read()
        s = fix_common_head(c, s)
        s = fix_im(s) if c == "I" else fix_nh(s)
        s = fix_tags(c, s)
        s = fix_heads(c, s)
        s = fix_sec5(c, s)
        s = fix_nf(c, s)
        s = s.rstrip("\n") + "\n\n" + "\n".join(section7(c))
        added = fix_csv(c)
        # 검증 뒤 수(인용·조각)를 먼저 셈
        R1 = Report()
        check_quotes(R1, c, s, CO[c])
        lines1, _, blocks1, _ = parse_md(s)
        check_frags(R1, c, lines1, blocks1)
        pre_stats[c].update(post_quotes=R1.stats[c + "_quotes"], frags=R1.stats[c + "_frags"])
        s = s.rstrip("\n") + "\n\n" + "\n".join(verification_record(c, pre_stats[c], added)) + "\n"
        open(MD[c], "w", encoding="utf-8").write(s)
    os.makedirs(VD, exist_ok=True)
    json.dump(dict(log=LOG, pre=pre_stats), open(FIX_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in CO:
        print(f"{CO[c]}: 고친 곳 {len(LOG[c])}건")


def main(argv):
    if len(argv) > 1 and argv[1] == "refute":
        refute()
        return 0
    if len(argv) > 1 and argv[1] == "fix":
        fix()
    R = run_check()
    print(f"문제 {len(R.problems)}건 — {OUT_TXT}")
    for x in R.problems[:40]:
        print("  ✗", x[:220])
    return 0 if not R.problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
