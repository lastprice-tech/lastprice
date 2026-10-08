# -*- coding: utf-8 -*-
"""13차 9-4 메리츠금융지주·한국투자금융지주 산출물 검증·보정.

    python3 scripts/dart/verify13_g_meritz_kis.py          # 대조만 — 결과 dart_out/risk13/verify13_g_meritz_kis.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_g_meritz_kis.py refute   # 「추출 범위에 없음」 반박 시도(같은 출처, 더 넓은 검색어) —
                                                           #   결과 dart_out/raw/web13/verify13_g_meritz_kis/refute_hits.json
    python3 scripts/dart/verify13_g_meritz_kis.py fix      # 보정(멱등: 검증 전 사본 pre/ 에서 다시 만듦) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-4_메리츠금융지주.md, 9-4_한국투자금융지주.md,
      dart_out/risk13/9-4_메리츠금융지주_조문목차.csv, 9-4_한국투자금융지주_조문목차.csv.
검증 전 사본: dart_out/raw/web13/verify13_g_meritz_kis/pre/ (커밋 8c118c8 의 파일 그대로). 원 생성기 scripts/dart/web13_g_meritz_kis.py 는
      고치지도 import 하지도 않는다.
원문(읽기만): dart_out/text/risk8/ (연차보고서·사업보고서(원본·정정)·경영공시, 쪽 표지 「=== p.N ===」), dart_out/text/risk9/<접수번호>.txt
      (DART 정기보고서 — 같은 회사 다른 기간 판), 메타 dart_out/risk8/텍스트목록.csv·handoff/연차보고서_파일목록.csv·
      dart_out/risk9/텍스트목록.csv·dart_out/doc/<접수번호>/_파일목록.json, 모범규준 hwp2md 변환본 dart_out/raw/web13/mobeom/fss/*.hwp.md,
      모범규준 조 목록 dart_out/risk13/모범규준_조목록.csv.

대조(인자 없이):
  1. md 의 원문 인용(코드 블록) 전부를 「- 인용:」 줄이 가리킨 문서·쪽의 텍스트와 공백만 무시하고 대조. 「[표 깨짐: …]」「[추출 깨짐: …]」
     「[줄임: …]」 줄은 이 작업이 끼운 표시라 빼고, 그 자리에서 조각을 나눠 조각마다 순서대로 찾는다. 찾은 자리의 쪽이 표기한 쪽과 같은지,
     인쇄 쪽(연차보고서 쪽 아래 번호)·DART 쪽(「dart.fss.or.kr Page N」)이 맞는지, 문서명·접수번호·URL·원본 수집일이 메타와 같은지.
     모범규준 인용은 hwp2md 변환본(판별)과 대조.
  2. 「정정판·재공시판 대조」 줄의 있음/없음·쪽을 다시 계산해 같은지.
  3. 조문 목차 CSV — 전문 옮긴 규정의 조 번호·제목이 그 쪽 텍스트에 있는지, 인용만 있는 행의 「…」 글이 그 쪽에 있는지, 문서·URL 이 맞는지.
  4. 모범규준 「N조(제목)」·요약표 조 제목이 모범규준_조목록.csv(2016.8.1판, 또는 2012.3.13판이라 적은 곳은 그 판)와 같은지.
  5. 지시서(REQUEST13) 9-4 항목마다 「7. 지시서 항목별 대조」 표에 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」이 있는지,
     가리킨 인용 번호가 md 에 있는지.
  6. 「추출 범위에 없음」 판정 줄마다 찾은 방법(검색어·범위)이 있는지, 반박 검색 결과(refute_hits.json)의 조가 검증 기록에 있는지.
  7. 인증값(DART 키·법제처 OC) 문자열 없음, 산출 폴더에 PDF 없음, 맨 끝 「## 검증 기록(2026-10-07)」 절이 하나.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

TODAY = "2026-10-07"
TXT8 = os.path.join("dart_out", "text", "risk8")
TXT9 = os.path.join("dart_out", "text", "risk9")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
VD = os.path.join("dart_out", "raw", "web13", "verify13_g_meritz_kis")
PRE = os.path.join(VD, "pre")
OUT_TXT = os.path.join(WORK, "verify13_g_meritz_kis.txt")
REFUTE_JSON = os.path.join(VD, "refute_hits.json")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MOBEOM_HWP = {
    "2016.8.1판": os.path.join("dart_out", "raw", "web13", "mobeom", "fss", "모범규준_20160801판_붙임2_통합위험관리_개정후전문.hwp.md"),
    "2012.3.13 제정판": os.path.join("dart_out", "raw", "web13", "mobeom", "fss", "예고29_통합리스크관리_모범규준(게시)F_.hwp.md"),
}
MOBEOM_CITE = {
    "2016.8.1판": ("금감원 행정지도 내역 관리번호 2014-017(감총그룹-388, 시행일 20160801) 첨부 「붙임2_금융지주회사 통합위험관리 모범규준 개정 후 전문.hwp」",
                  "https://www.fss.or.kr/fss/job/admnstgudc/view.do?guGuidanceMgrSeq=20170210165649943&menuNo=200492"),
    "2012.3.13 제정판": ("금감원 행정지도 예고 seqno=29 첨부 「통합리스크관리_모범규준(게시)F_.hwp」",
                       "https://www.fss.or.kr/fss/job/admnPrvntc/view.do?seqno=29&menuNo=200491"),
}
REQ = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
MD = {"M": os.path.join(OUTD, "9-4_메리츠금융지주.md"), "K": os.path.join(OUTD, "9-4_한국투자금융지주.md")}
TOC = {"M": os.path.join(WORK, "9-4_메리츠금융지주_조문목차.csv"), "K": os.path.join(WORK, "9-4_한국투자금융지주_조문목차.csv")}
CO = {"M": "메리츠금융지주", "K": "한국투자금융지주"}
PAGE_RE = re.compile(r"^=== p\.(\d+) ===\s*$")
MARK_RE = re.compile(r"^\s*\[(표 깨짐|추출 깨짐|줄임|생략)[:：]")

# ───────────────────────────── 문서 ─────────────────────────────
DOCS = {
    "M_AR": dict(co="메리츠금융지주", kind="연차보고서", file="연차보고서__메리츠금융지주_지배구조연차보고서_2026.txt",
                 name="메리츠금융지주 「2025년 지배구조 및 보수체계 연차보고서」(표지 2026. 3. 6.)", printed="ar_dash"),
    "M_BR": dict(co="메리츠금융지주", kind="사업보고서", file="사업보고서__메리츠금융지주__20260318001419.txt",
                 name="메리츠금융지주 「사업보고서 (2025.12)」 원본", rcp="20260318001419", printed="br"),
    "M_BR_1549": dict(co="메리츠금융지주", kind="사업보고서(정정)", file="사업보고서__메리츠금융지주__20260318001549.txt",
                      name="메리츠금융지주 「[첨부정정]사업보고서 (2025.12)」", rcp="20260318001549", printed="br"),
    "M_BR_4089": dict(co="메리츠금융지주", kind="사업보고서(정정)", file="사업보고서__메리츠금융지주__20260331004089.txt",
                      name="메리츠금융지주 「[기재정정]사업보고서 (2025.12)」", rcp="20260331004089", printed="br"),
    "M_BR_4202": dict(co="메리츠금융지주", kind="사업보고서(정정)", file="사업보고서__메리츠금융지주__20260331004202.txt",
                      name="메리츠금융지주 「[기재정정]사업보고서 (2025.12)」", rcp="20260331004202", printed="br"),
    "M_BR_4144": dict(co="메리츠금융지주", kind="사업보고서(정정)", file="사업보고서__메리츠금융지주__20260406004144.txt",
                      name="메리츠금융지주 「[첨부정정]사업보고서 (2025.12)」", rcp="20260406004144", printed="br"),
    "M_MD": dict(co="메리츠금융지주", kind="경영공시", file="경영공시__메리츠금융지주.txt",
                 name="메리츠금융지주 경영공시 「2026 1H Report」(제17기 2분기)", printed=None),
    "K_AR": dict(co="한국투자금융지주", kind="연차보고서", file="연차보고서__한국투자금융지주_지배구조연차보고서_2026.txt",
                 name="한국투자금융지주 「2025년 지배구조 및 보수체계 연차보고서」(본공시, 공시일 2026-03-06)", printed="ar_num"),
    "K_AR_RE": dict(co="한국투자금융지주", kind="연차보고서(재공시)",
                    file="연차보고서__한국투자금융지주_지배구조연차보고서_2026_재공시.txt",
                    name="한국투자금융지주 「2025년 지배구조 및 보수체계 연차보고서 재공시」(공시일 2026-05-15)", printed="ar_num"),
    "K_BR": dict(co="한국투자금융지주", kind="사업보고서", file="사업보고서__한국투자금융지주__20260319001006.txt",
                 name="한국투자금융지주 「사업보고서 (2025.12)」 원본", rcp="20260319001006", printed="br"),
    "K_MD": dict(co="한국투자금융지주", kind="경영공시", file="경영공시__한국투자금융지주.txt",
                 name="한국투자금융지주 경영공시 「2026년 2분기 한국투자금융지주 현황」(제25기 2분기)", printed=None),
}
for _k, _d in DOCS.items():
    _d["path"] = os.path.join(TXT8, _d["file"])
CORR = {"M_BR": ["M_BR_1549", "M_BR_4089", "M_BR_4202", "M_BR_4144"], "K_AR": ["K_AR_RE"]}
FY2025_RCP = {"20260318001419", "20260318001549", "20260331004089", "20260331004202", "20260406004144", "20260319001006"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_meta():
    tl = {r["doc_id"]: r for r in csv.DictReader(open(os.path.join("dart_out", "risk8", "텍스트목록.csv"), encoding="utf-8-sig"))}
    ar = {r["파일명"]: r for r in csv.DictReader(open(os.path.join("handoff", "연차보고서_파일목록.csv"), encoding="utf-8-sig"))}
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
    # risk9: 같은 회사 정기보고서(다른 기간 판)
    r9 = list(csv.DictReader(open(os.path.join("dart_out", "risk9", "텍스트목록.csv"), encoding="utf-8-sig")))
    for r in r9:
        if r["corp_label"] not in CO.values():
            continue
        rcp = r["rcept_no"]
        p = os.path.join(TXT9, rcp + ".txt")
        if not os.path.exists(p):
            continue
        key = "R9_" + rcp
        fetched = ""
        j = os.path.join("dart_out", "doc", rcp, "_파일목록.json")
        if os.path.exists(j):
            fetched = json.load(open(j, encoding="utf-8")).get("생성시각", "")
        DOCS[key] = dict(co=r["corp_label"], kind="정기보고서(risk9)", file=rcp + ".txt", path=p, rcp=rcp, printed="br",
                         name=f"{r['corp_label']} 「{r['report_nm']}」", report_nm=r["report_nm"],
                         url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rcp, src_sha=r["원본sha256"],
                         txt_sha_list=r["텍스트sha256"], fetched=fetched, method="")


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
            if mode == "ar_dash" and seen < 3 and re.fullmatch(r"- (\d+) -", s):
                self.printed[cur] = re.fullmatch(r"- (\d+) -", s).group(1)
            elif mode == "ar_num" and seen < 3 and re.fullmatch(r"\d{1,3}", s):
                self.printed[cur] = s
            elif mode == "br":
                m2 = re.search(r"dart\.fss\.or\.kr Page (\d+)", s)
                if m2:
                    self.printed[cur] = m2.group(1)
            if s:
                seen += 1
        # 공백 뺀 글 + 글자별 (쪽, 줄)
        self._raw = None
        self._skip = None

    def plabel(self, p1, p2=None):
        p2 = p2 or p1
        a = f"p.{p1}" if p1 == p2 else f"p.{p1}~{p2}"
        pr = [self.printed.get(p) for p in range(p1, p2 + 1) if self.printed.get(p)]
        if pr:
            lab = pr[0] if (len(pr) == 1 or pr[0] == pr[-1]) else f"{pr[0]}~{pr[-1]}"
            a += f"({'DART 쪽 ' if DOCS[self.key]['printed'] == 'br' else '인쇄 '}{lab})"
        return a

    def flat(self, skip=False):
        """공백 없이 이어 붙인 글과 글자별 줄 번호. skip=True 면 쪽 표지·쪽 번호 줄·DART 쪽 머리말을 뺌(정정판 대조용)."""
        attr = "_skip" if skip else "_raw"
        if getattr(self, attr) is None:
            chars, idx = [], []
            for i, ln in enumerate(self.lines):
                if skip and skipline(ln):
                    continue
                c = re.sub(r"\s+", "", ln)
                chars.append(c)
                idx.extend([i] * len(c))
            setattr(self, attr, ("".join(chars), idx))
        return getattr(self, attr)


def skipline(ln):
    s = ln.strip()
    return bool(PAGE_RE.match(ln) or "dart.fss.or.kr Page" in ln or re.fullmatch(r"\d{1,3}", s) or re.fullmatch(r"- \d+ -", s))


TEXTS = {}


def T(key):
    if key not in TEXTS:
        TEXTS[key] = Text(key)
    return TEXTS[key]


def nows(s):
    return re.sub(r"\s+", "", s)


# ───────────────────────────── 반박 검색(refute) ─────────────────────────────
# 조마다 원래 검색어(수집 에이전트 6장)보다 넓힌 정규식. 줄 단위 + 앞뒤 줄 이어 붙인 창(줄바꿈으로 갈린 낱말)에서 찾는다.
REFUTE = {
    "3": dict(pat=r"경미|중요(성|도)이?\s*(낮|작)|중요하지\s*않|적용\s*(을\s*)?(배제|제외|예외)|적용하지\s*(아니|않)|적용\s*대상|적용대상|"
                  r"(측정|관리|한도관리|모니터링)\s*대상|대상\s*(자회사|계열사|회사)|제외할\s*수|소규모\s*(자회사|계열사)|비중이\s*(작|낮|미미)|미미한",
              ctx=r"리스크|위험|자회사|계열사|종속", label="경미·적용 배제·측정 대상"),
    "4·5": dict(pat=r"철학|원칙|기본\s*방침|기본\s*정책|리스크\s*문화|위험\s*문화|[Rr]isk\s*[Cc]ulture|최상위\s*가치|가치\s*규범|위험\s*성향|"
                    r"리스크\s*성향|[Rr]isk\s*[Aa]ppetite|RAF|선언문|행동\s*강령",
                ctx=r"리스크|위험", label="철학·원칙·기본방침·위험성향·리스크 문화"),
    "17": dict(pat=r"의사\s*전달|정보\s*전달|공문|공식\s*문서|서면|문서(로|화|를|에)|통보|통지|시달|하달|지시|지도|권고|가이드\s*라인|가이드|지침|"
                   r"요청|요구|전달|협조\s*(요청|문)|회신|통할",
               ctx=r"자회사|계열사|그룹사|종속", label="의사전달·공문·서면·통보·지시·권고·가이드라인·요청"),
    "21·22·24": dict(pat=r"연결\s*(기준|실체|대상|범위|익스포|베이스)|통합\s*(측정|관리|리스크|위험|VaR|한도)|그룹\s*(전체|차원|통합|합산|단위|기준|리스크량|VaR)|"
                          r"합산|[Gg]roup[- ]?wide|[Cc]onsolidat|리스크\s*량|위험\s*량|소요\s*자본|위험\s*자본|요구\s*자본|내부\s*자본|"
                          r"[Ee]conomic\s*[Cc]apital|경제적\s*자본|분산\s*효과|상관관계",
                     ctx=r"신용|시장|금리|이자율|리스크|위험", label="연결·통합·그룹 단위 측정, 소요·위험·내부자본, 합산"),
    "27": dict(pat=r"평판|명성|이미지\s*(리스크|위험|훼손|실추)|[Rr]eputation|전략\s*(리스크|위험)|[Ss]trateg(y|ic)\s*[Rr]isk|사업\s*(리스크|위험)|"
                   r"비재무|비계량|정성\s*(적|평가)|ESG\s*리스크|기후\s*(리스크|위험)|[Ee]merging|신규\s*리스크|잠재\s*리스크|전략적\s*의사결정",
               ctx=None, label="평판·명성·전략·사업리스크·비재무·비계량·정성·ESG·기후"),
    "34": dict(pat=r"해외|글로벌|국외|국가\s*(별|위험|리스크|신용|한도)|[Cc]ountry|현지\s*법인|외국|역외|[Cc]ross[- ]?border|신흥국|외화",
               ctx=r"리스크|위험|한도|점검|검토|보고|관리", label="해외·글로벌·국외·국가·현지법인·외국·외화"),
    "53": dict(pat=r"위기|비상|[Cc]ontingency|컨틴전시|대응\s*(조직|체계|체제|반)|대책\s*(반|위원회|본부)|상황\s*반|태스크|TF\b|[Cc]risis",
               ctx=None, excl=r"비상임|비상장|비상근|비상위험|비상무|비상각|비상환", label="위기·비상·컨틴전시·대응조직·대책반·Crisis"),
    "55": dict(pat=r"조기\s*(경보|경고|감지|위험\s*감지|대응)|경보|경고|[Ww]arning|EWS|EWI|징후|위기\s*(단계|수준|지표|상황\s*단계)|"
                   r"관심\s*[·,ㆍ/]\s*주의|주의\s*[·,ㆍ/]\s*경계|경계\s*[·,ㆍ/]\s*심각|[Tt]rigger|트리거|임계|발령|선행\s*지표|모니터링\s*지표|"
                   r"KRI|[Rr]ed\s*[Ll]ight|신호등|[Aa]lert|알람|판단\s*지표",
               ctx=None, excl=r"환경보호", label="조기경보·경보·경고·징후·위기단계·관심/주의/경계/심각·Trigger·발령·KRI·Red Light"),
    "규정전문": dict(pat=r"그룹\s*리스크\s*관리\s*규정|그룹\s*위험\s*관리\s*규정|리스크관리규정|위험관리규정|리스크\s*관리\s*지침|대응\s*지침|업무\s*지침|"
                       r"운영\s*세칙|시행\s*세칙|제\s*1\s*조\s*\(\s*목적\s*\)",
                   ctx=None, label="규정명·시행세칙·지침·제1조(목적)"),
}
NEAR_17 = r"(자회사|계열사|그룹사|종속).{0,40}(공문|문서|서면|통보|통지|시달|하달|지시|지도|권고|가이드|지침|요청|요구|전달)|" \
          r"(공문|문서|서면|통보|통지|시달|하달|지시|지도|권고|가이드|지침|요청|요구|전달).{0,40}(자회사|계열사|그룹사|종속)"


def refute():
    load_meta()
    keys = [k for k in DOCS if DOCS[k]["co"] in CO.values()]
    out = {"검색일": TODAY, "방법": "줄 단위 정규식 + 앞뒤 1줄을 이어 붙인 창(줄바꿈으로 갈린 낱말), ctx 가 있는 조는 같은 창에 ctx 낱말이 있을 때만",
           "조": {}}
    for jo, spec in REFUTE.items():
        pat = re.compile(spec["pat"])
        ctx = re.compile(spec["ctx"]) if spec.get("ctx") else None
        excl = re.compile(spec["excl"]) if spec.get("excl") else None
        near = re.compile(NEAR_17) if jo == "17" else None
        rec = {"검색어": spec["pat"], "ctx": spec.get("ctx"), "뺀말": spec.get("excl"), "label": spec["label"], "문서": {}}
        for k in keys:
            t = T(k)
            hits = []
            seen = set()
            for i, ln in enumerate(t.lines):
                if PAGE_RE.match(ln):
                    continue
                win = " ".join(x.strip() for x in t.lines[max(0, i - 1): i + 2] if not PAGE_RE.match(x))
                s = ln.strip()
                body = s
                if excl:
                    body = excl.sub("", body)
                m = pat.search(body)
                if not m:
                    # 줄바꿈으로 갈린 낱말: 이 줄 끝 + 다음 줄 앞
                    nxt = t.lines[i + 1].strip() if i + 1 < len(t.lines) else ""
                    j = (s[-12:] + nxt[:12])
                    if excl:
                        j = excl.sub("", j)
                    m2 = pat.search(j)
                    if not (m2 and m2.start() < len(s[-12:]) < m2.end()):
                        continue
                if ctx and not ctx.search(win):
                    continue
                if near is not None and not near.search(win):
                    continue
                if i in seen:
                    continue
                seen.add(i)
                hits.append({"line": i + 1, "page": t.page[i], "text": s[:200]})
            rec["문서"][k] = {"name": DOCS[k]["name"], "rcp": DOCS[k].get("rcp", ""), "pages": t.npages, "n": len(hits), "hits": hits}
        out["조"][jo] = rec
    os.makedirs(VD, exist_ok=True)
    json.dump(out, open(REFUTE_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 요약만 출력
    for jo, rec in out["조"].items():
        tot8 = sum(v["n"] for k, v in rec["문서"].items() if not k.startswith("R9_"))
        tot9 = sum(v["n"] for k, v in rec["문서"].items() if k.startswith("R9_"))
        print(f"{jo}: risk8 {tot8}줄, risk9 {tot9}줄 ({len([k for k in rec['문서'] if k.startswith('R9_')])}개 보고서)")
    print("→", REFUTE_JSON)


# ───────────────────────────── md 읽기 ─────────────────────────────
QID_RE = re.compile(r"^#### \[([A-Z]+-\d+)\]\s*(.*)$")
PAGE_LAB_RE = re.compile(r"^p\.(\d+)(?:~(\d+))?(?:\((인쇄|DART 쪽) ([\d~]+)\))?$")
TAG_LINE = "- 이 글이 닿는 모범규준 조"


def parse_md(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    quotes, blocks = [], []
    cur = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = QID_RE.match(ln)
        if m:
            cur = dict(id=m.group(1), title=m.group(2), hline=i + 1, cite=None, cline=None, corr=None, corrline=None,
                       tag=None, tagline=None, code=None, cstart=None)
            quotes.append(cur)
        elif ln.startswith("```") and ln.strip() != "```":
            j = i + 1
            body = []
            while j < len(lines) and lines[j].strip() != "```":
                body.append(lines[j])
                j += 1
            blocks.append(dict(start=i + 2, end=j, owner=cur["id"] if cur is not None and cur["code"] is None else None))
            if cur is not None and cur["code"] is None:
                cur["code"] = body
                cur["cstart"] = i + 2
            i = j
        elif cur is not None and ln.startswith("- 인용:") and cur["cite"] is None:
            cur["cite"], cur["cline"] = ln, i + 1
        elif cur is not None and ln.startswith("- 정정판·재공시판 대조") and cur["corr"] is None:
            cur["corr"], cur["corrline"] = ln, i + 1
        elif cur is not None and ln.startswith(TAG_LINE) and cur["tag"] is None:
            cur["tag"], cur["tagline"] = ln, i + 1
        elif ln.startswith("## ") or ln.startswith("### "):
            cur = None
        i += 1
    gt = [i + 1 for i, ln in enumerate(lines) if ln.startswith(">")]
    return lines, quotes, blocks, gt


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


def text_offsets(t, skip=False):
    """flat 글에서 줄마다 시작 글자 위치."""
    flat, idx = t.flat(skip)
    key = "_off_skip" if skip else "_off"
    if not hasattr(t, key):
        off = [None] * (len(t.lines) + 1)
        pos = 0
        for i, ln in enumerate(t.lines):
            off[i] = pos
            if skip and skipline(ln):
                continue
            pos += len(re.sub(r"\s+", "", ln))
        off[len(t.lines)] = pos
        setattr(t, key, off)
    return getattr(t, key)


def find_segs(key, code, p1=None, p2=None, skip=False):
    """조각을 순서대로 찾음 → (첫 쪽, 끝 쪽, 첫 줄, 끝 줄) 또는 (None, 실패한 조각 번호).
    첫 조각이 여러 곳에 있으면 모든 조각이 이어서 맞는 자리 가운데 가장 짧은 자리를 고른다."""
    t = T(key)
    flat, idx = t.flat(skip)
    off = text_offsets(t, skip)
    lo, hi = 0, len(flat)
    if p1 is not None:
        ls = [i for i, p in enumerate(t.page) if p1 <= p <= (p2 or p1)]
        if not ls:
            return None, -1
        lo, hi = off[ls[0]], off[ls[-1] + 1]
    segs = []
    for seg in segments(code):
        body = [x for x in seg if not (skip and skipline(x))]
        n = nows("\n".join(body))
        if n:
            segs.append(n)
    if not segs:
        return None, -2
    best, worst_fail = None, 0
    start = flat.find(segs[0], lo, hi)
    tries = 0
    while start >= 0 and tries < 200:
        tries += 1
        spans = [(start, start + len(segs[0]))]
        pos = spans[0][1]
        fail = None
        for n_, n in enumerate(segs[1:], 1):
            k = flat.find(n, pos, hi)
            if k < 0:
                fail = n_
                break
            spans.append((k, k + len(n)))
            pos = k + len(n)
        if fail is None:
            if best is None or spans[-1][1] - spans[0][0] < best[-1][1] - best[0][0]:
                best = spans
        else:
            worst_fail = max(worst_fail, fail)
        start = flat.find(segs[0], start + 1, hi)
    if best is None:
        return None, worst_fail
    a, b = idx[best[0][0]], idx[best[-1][1] - 1]
    return (t.page[a], t.page[b], a, b), None


def doc_by_cite(parts):
    name = parts[0]
    rcp = ""
    for x in parts[1:]:
        if x.startswith("접수번호 "):
            rcp = x[len("접수번호 "):].strip()
    cands = [k for k, d in DOCS.items() if d["name"] == name and (not rcp or d.get("rcp") == rcp)]
    cands.sort(key=lambda k: k.startswith("R9_"))
    return cands[0] if cands else None


def mobeom_flat(ver):
    p = MOBEOM_HWP[ver]
    return nows(open(p, encoding="utf-8").read())


def mobeom_meta(ver):
    return json.load(open(MOBEOM_HWP[ver][:-3] + ".meta.json", encoding="utf-8"))


# ───────────────────────────── 대조 ─────────────────────────────
class Report:
    def __init__(self):
        self.out = []
        self.problems = []
        self.stats = {}

    def p(self, s=""):
        self.out.append(s)

    def bad(self, s):
        self.problems.append(s)
        self.out.append("  ✗ " + s)


def check_quotes(R, co, path):
    lines, quotes, blocks, gt = parse_md(path)
    R.p(f"## 1. 원문 인용 대조 — {os.path.basename(path)}")
    n_ok = 0
    if gt:
        R.bad(f"{co}: 「>」 인용 블록 줄 {gt[:5]} — 이 파일은 코드 블록만 씀(대조 대상 아님)")
    orphan = [b for b in blocks if b["owner"] is None]
    for b in orphan:
        R.bad(f"{co}: 인용 머리(#### [ID]) 없는 코드 블록 {b['start']}~{b['end']}행")
    ids = [q["id"] for q in quotes]
    for x in sorted(set(ids)):
        if ids.count(x) > 1:
            R.bad(f"{co}: 인용 번호 {x} 가 {ids.count(x)}번 나옴")
    for q in quotes:
        if q["code"] is None:
            R.bad(f"{q['id']}: 코드 블록 없음")
            continue
        if not q["cite"]:
            R.bad(f"{q['id']}: 「- 인용:」 줄 없음")
            continue
        if not q["tag"]:
            R.bad(f"{q['id']}: 「{TAG_LINE}…」 줄 없음")
        body = q["cite"][len("- 인용: ["):].rstrip()
        if not body.endswith("]"):
            R.bad(f"{q['id']}: 인용 줄 끝 「]」 없음")
        parts = [x.strip() for x in body[:-1].split(" · ")]
        if parts[0].startswith("「금융지주회사 통합"):
            ok = check_mobeom_quote(R, q, parts)
            n_ok += ok
            continue
        key = doc_by_cite(parts)
        if not key:
            R.bad(f"{q['id']}: 인용 줄 문서명·접수번호가 문서 목록과 맞지 않음 — {parts[0][:60]}")
            continue
        d = DOCS[key]
        errs = []
        # 출처 표기
        if "rcp" in d:
            if f"접수번호 {d['rcp']}" not in parts or d["url"] not in parts:
                errs.append(f"접수번호·URL 표기({d['rcp']})")
        else:
            want = f"{d['url']} (방식 {d['method']})" if d.get("method") else d["url"]
            if want not in parts:
                errs.append(f"URL 표기(기대 「{want}」)")
        fet = [x for x in parts if x.startswith("원본 수집 ")]
        if not fet or fet[0] != "원본 수집 " + d["fetched"][:10]:
            errs.append(f"원본 수집일(기대 {d['fetched'][:10]})")
        if f"옮김 {TODAY}" not in parts:
            errs.append("옮김 날짜")
        pl = [x for x in parts if PAGE_LAB_RE.match(x)]
        if not pl:
            errs.append("쪽 표기 없음")
            R.bad(f"{q['id']}: " + "; ".join(errs))
            continue
        m = PAGE_LAB_RE.match(pl[0])
        p1, p2 = int(m.group(1)), int(m.group(2) or m.group(1))
        res, fail = find_segs(key, q["code"], p1, p2)
        if res is None:
            res2, fail2 = find_segs(key, q["code"])
            where = f" — 문서 전체에서는 {T(key).plabel(res2[0], res2[1])}" if res2 else " — 문서 전체에서도 못 찾음"
            errs.append(f"글 대조 실패(조각 {fail}){where}")
        else:
            lab = T(key).plabel(res[0], res[1])
            if lab != pl[0]:
                errs.append(f"쪽 표기 「{pl[0]}」 ≠ 찾은 쪽 「{lab}」")
        # 정정판·재공시판
        if key in CORR:
            if not q["corr"]:
                errs.append("정정판·재공시판 대조 줄 없음")
            else:
                want = corr_line(key, q["code"])
                if q["corr"] != want:
                    errs.append(f"정정판 대조 줄이 다시 계산한 값과 다름 — 기대 「{want[len('- 정정판·재공시판 대조(공백 무시): '):]}」")
        if errs:
            R.bad(f"{q['id']} ({d['kind']} {pl[0]}): " + "; ".join(errs))
        else:
            n_ok += 1
            R.p(f"  ✓ {q['id']} {d['kind']} {pl[0]} — {len(q['code'])}줄, 조각 {len(segments(q['code']))}")
    R.stats[co + "_quotes"] = len(quotes)
    R.stats[co + "_ok"] = n_ok
    R.p(f"  → 인용 {len(quotes)}건 중 일치 {n_ok}건")
    return lines, quotes


def corr_line(key, code):
    out = []
    for ck in CORR[key]:
        lab = DOCS[ck].get("rcp") or "재공시"
        res, fail = find_segs(ck, code, skip=True)
        if res:
            out.append(f"{lab}: 같은 글 있음({T(ck).plabel(res[0], res[1])})")
        else:
            out.append(f"{lab}: 이 글 없음(그 판에 이 부분이 실려 있지 않음)")
    return "- 정정판·재공시판 대조(공백 무시): " + " / ".join(out)


def check_mobeom_quote(R, q, parts):
    ver = "2016.8.1판" if "2016.8.1판" in parts[0] else ("2012.3.13 제정판" if "2012.3.13 제정판" in parts[0] else None)
    if not ver:
        R.bad(f"{q['id']}: 모범규준 판 표기 없음")
        return 0
    src, url = MOBEOM_CITE[ver]
    meta = mobeom_meta(ver)
    errs = []
    if src not in parts or url not in parts:
        errs.append("출처(행정지도 첨부·URL) 표기")
    if f"원본 sha256 {meta['sha256'][:16]}" not in parts:
        errs.append("원본 sha256")
    if f"수집 2026-10-07(UTC; .meta.json fetched_at {meta['fetched_at']})" not in parts:
        errs.append("수집일")
    if f"옮김 {TODAY}" not in parts:
        errs.append("옮김 날짜")
    flat = mobeom_flat(ver)
    pos = 0
    for n_, seg in enumerate(segments(q["code"])):
        n = nows("\n".join(seg))
        k = flat.find(n, pos)
        if k < 0:
            errs.append(f"글 대조 실패(조각 {n_})")
            break
        pos = k + len(n)
    art = [x for x in parts if re.match(r"^제\d+조", x)]
    if not art:
        errs.append("조 표기 없음")
    else:
        a = re.match(r"^제(\d+)조", art[0]).group(1)
        if not any(nows(ln).startswith(f"제{a}조(") for ln in q["code"]):
            errs.append(f"인용 글에 제{a}조 머리가 없음")
    if errs:
        R.bad(f"{q['id']} (모범규준 {ver}): " + "; ".join(errs))
        return 0
    R.p(f"  ✓ {q['id']} 모범규준 {ver} {art[0]} — {len(q['code'])}줄")
    return 1


def load_jo():
    rows = list(csv.DictReader(open(JO_CSV, encoding="utf-8-sig")))
    return {r["조"]: (r["제목_2016.8.1판"], r["제목_2012.3.13제정판"]) for r in rows}


JO_PAT = re.compile(r"(?<![제\d])(\d{1,2})조\(([^()]*?)(?:\(판단\))?\)")


def check_titles(R, co, lines):
    R.p(f"## 4. 모범규준 조 번호(조 제목) — {CO[co]}")
    jo = load_jo()
    n = 0
    incode = False
    sec = ""
    sub = ""
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec, sub = ln, ""
        if ln.startswith("### "):
            sub = ln
        if ln.startswith("```"):
            incode = not incode
            continue
        if incode or sec == VREC:
            continue
        if sec.startswith("## 7.") and ln.startswith("| "):
            c = ln.split("|")
            ln = "|".join(c[:2] + c[3:])
        if sub.startswith("### 1-2-1") and ln.startswith("| ") and "|---" not in ln:
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            for col, k in ((2, 0), (3, 1)):
                mm = re.match(r"(\d+)조 (.+)$", c[col]) if len(c) > col else None
                if mm and mm.group(1) in jo:
                    n += 1
                    if mm.group(2) != jo[mm.group(1)][k]:
                        R.bad(f"{CO[co]} {i + 1}행 1-2-1 소표: {mm.group(1)}조 「{mm.group(2)}」 ≠ 「{jo[mm.group(1)][k]}」")
        for m in JO_PAT.finditer(ln):
            no, title = m.group(1), re.split(r"[,:]| —", m.group(2))[0].strip()
            if no not in jo:
                continue
            n += 1
            if title not in jo[no]:
                R.bad(f"{CO[co]} {i + 1}행: 「{no}조({title})」 — 조목록 제목은 「{jo[no][0]}」(2016.8.1판)/「{jo[no][1]}」(2012.3.13판)")
        if sec.startswith("## 0.") and ln.startswith("| ") and "|---" not in ln:
            c = [x.strip() for x in ln.strip("|").split("|")]
            # 0장 요약표: 조 | 조 제목(2016.8.1판) | …
            if len(c) >= 2 and re.fullmatch(r"[\d·]+(\(인용 조문\))?", c[0]) and c[1] and c[1] != "-":
                nos = re.findall(r"\d+", c[0].split("(")[0])
                ts = c[1].split("·") if len(nos) > 1 else [c[1]]
                for no, t in zip(nos, ts):
                    n += 1
                    if t.strip() != jo[no][0]:
                        R.bad(f"{CO[co]} {i + 1}행 요약표: {no}조 제목 「{t.strip()}」 ≠ 「{jo[no][0]}」")
    # 인용마다 조 태그 줄이 「N조(제목)」 꼴인지
    R.stats[co + "_titles"] = n
    R.p(f"  → 「N조(제목)」·요약표 조 제목 {n}곳 대조")


def check_tags(R, co, quotes):
    jo = load_jo()
    for q in quotes:
        if not q["tag"]:
            continue
        body = q["tag"].split(":", 1)[1]
        for m in re.finditer(r"(?<![제\d])(\d{1,2})조(?!\()", body):
            R.bad(f"{q['id']}: 조 태그 「{m.group(0)}」 에 조 제목 없음")
        if re.search(r"(?:^|[ ,])\d{1,2}(?:[ ,·]|$)", body.split("(글과")[0]):
            R.bad(f"{q['id']}: 조 태그에 「N조(제목)」 꼴이 아닌 숫자 — {body.strip()[:80]}")


# ───────────────────────────── CSV ─────────────────────────────
def check_toc(R, co):
    path = TOC[co]
    R.p(f"## 3. 조문 목차 CSV — {os.path.basename(path)}")
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    names = {d["name"]: k for k, d in DOCS.items() if not k.startswith("R9_")}
    n_ok = 0
    for r in rows:
        errs = []
        key = names.get(r["문서"])
        if r["문서"] and not key:
            k9 = [k for k, d in DOCS.items() if d["name"] == r["문서"] and d.get("rcp") == r["접수번호또는URL"]]
            key = k9[0] if k9 else None
        if not key:
            R.bad(f"{CO[co]} CSV {r['규정명']} {r['조번호']}: 문서명이 목록과 다름")
            continue
        d = DOCS[key]
        if r["접수번호또는URL"] not in (d.get("rcp", ""), d["url"]):
            errs.append("접수번호또는URL")
        m = PAGE_LAB_RE.match(r["쪽"])
        if not m:
            errs.append(f"쪽 표기 「{r['쪽']}」")
        else:
            p1, p2 = int(m.group(1)), int(m.group(2) or m.group(1))
            if T(key).plabel(p1, p2) != r["쪽"]:
                errs.append(f"쪽 표기 「{r['쪽']}」≠「{T(key).plabel(p1, p2)}」")
            pg = nows("\n".join(ln for ln, p in zip(T(key).lines, T(key).page) if p1 <= p <= p2))
            no, title = r["조번호"], r["조제목"]
            if r["전문여부"].startswith("Y"):
                mm = re.fullmatch(r"제(\d+)(조|장)", no)
                if not mm:
                    errs.append(f"조번호 꼴 「{no}」")
                elif "추출 깨짐" in r["전문여부"]:
                    if nows(f"제 조 {title}{mm.group(1)} (") not in pg:
                        errs.append(f"깨진 조 머리 「제 조 {title}{mm.group(1)} (」 가 그 쪽에 없음")
                elif mm.group(2) == "장":
                    if nows(f"제{mm.group(1)}장{title}") not in pg:
                        errs.append(f"「제{mm.group(1)}장 {title}」 가 그 쪽에 없음")
                elif nows(f"제{mm.group(1)}조({title})") not in pg:
                    errs.append(f"「제{mm.group(1)}조({title})」 가 그 쪽에 없음")
            else:
                core = nows(re.split(r"[(（]", r["규정명"])[0])
                art = ""
                m1 = re.fullmatch(r"제(\d+)조 제(\d+)항", no)
                m2 = re.fullmatch(r"제(\d+)조", no)
                if m1:
                    art = f"제{m1.group(1)}조{m1.group(2)}항"
                elif m2:
                    art = f"제{m2.group(1)}조"
                elif no == "제2장·제3장":
                    art = "제2장과제3장"
                if core not in pg:
                    errs.append(f"규정명 「{core}」 이 그 쪽에 없음")
                if art and (core + art) not in pg and not (art in pg and core in pg):
                    errs.append(f"「{core} {art}」 인용이 그 쪽에 없음")
                if title and not title.startswith("추출 범위에 없음") and nows(f"{m2.group(0) if m2 else ''}({title})") not in pg \
                        and nows(f"{m2.group(0) if m2 else ''}({title}") not in pg and nows(title) not in pg:
                    errs.append(f"조 제목 「{title}」 이 그 쪽에 없음")
        if errs:
            R.bad(f"{CO[co]} CSV {r['규정명'][:20]} {r['조번호']}: " + "; ".join(errs))
        else:
            n_ok += 1
    R.stats[co + "_toc"] = len(rows)
    R.stats[co + "_toc_ok"] = n_ok
    R.p(f"  → {len(rows)}행 중 일치 {n_ok}행")


# ───────────────────────────── 지시서 항목·추출 범위에 없음·기타 ─────────────────────────────
REQ_ITEMS = [
    ("9-4 1.", "그룹리스크관리규정(이름이 다르면 대응 규정)의 조문 목차 전체(조 번호와 제목). 전문이 있으면 전문"),
    ("9-4 1. 메리츠", "메리츠 그룹리스크관리규정 9조 7항, 57조가 인용되어 있음. 같은 방식으로 대조"),
    ("9-4 1. iM", "iM 그룹 리스크관리규정은 28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음."),
    ("9-4 2. 21·22·24", "21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부"),
    ("9-4 2. 27", "27조 전략·평판위험: 관리 체제, 측정이나 평가 수단"),
    ("9-4 2. 34", "34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고"),
    ("9-4 2. 3", "3조: 위험이 경미한 자회사를 적용에서 빼는 기준"),
    ("9-4 2. 17", "17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)"),
    ("9-4 2. 55", "55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)"),
    ("9-4 2. 53", "53조 위기대응조직: 구성과 전환 요건"),
    ("9-4 3.", "위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구"),
]
SEC7 = "## 7. 지시서 항목별 대조(검증 2026-10-07 추가)"
VREC = "## 검증 기록(2026-10-07)"
TRAIL = ("검색어", "찾은 범위", "찾은 파일", "찾은 곳", "찾은 방법", "6장", "검색 기록", "검증 기록", "정규식", "p.1~", "같은 범위", "전 범위")


def check_request(R, co, lines, quotes):
    R.p(f"## 5. 지시서 9-4 항목 — {CO[co]}")
    req = open(REQ, encoding="utf-8").read()
    ids = {q["id"] for q in quotes}
    try:
        a = lines.index(SEC7)
    except ValueError:
        R.bad(f"{CO[co]}: 「{SEC7}」 절 없음")
        return
    rows = []
    for ln in lines[a + 1:]:
        if ln.startswith("## "):
            break
        if ln.startswith("| ") and not ln.startswith("| 지시서 항목") and "|---" not in ln:
            rows.append([x.strip() for x in ln.strip().strip("|").split("|")])
    for item, text in REQ_ITEMS:
        if text not in req:
            R.bad(f"지시서 문구 「{text[:30]}…」 가 REQUEST13.md 에 없음(스크립트 목록 오류)")
        r = [x for x in rows if x[0] == item]
        if not r:
            R.bad(f"{CO[co]}: 7장 표에 「{item}」 행 없음")
            continue
        r = r[0]
        if len(r) < 5:
            R.bad(f"{CO[co]}: 7장 「{item}」 행 칸 수 {len(r)}")
            continue
        if r[1] != text:
            R.bad(f"{CO[co]}: 7장 「{item}」 지시서 원문 칸이 지시서와 다름")
        got, state = r[3], r[4]
        refs = re.findall(r"\[([A-Z]+-\d+)\]", got + " " + state)
        for x in refs:
            if x not in ids:
                R.bad(f"{CO[co]}: 7장 「{item}」 가 가리킨 인용 [{x}] 가 md 에 없음")
        if "추출 범위에 없음" in state and not any(t in state for t in TRAIL):
            R.bad(f"{CO[co]}: 7장 「{item}」 추출 범위에 없음인데 찾은 방법이 없음")
        if "추출 범위에 없음" not in state and not refs and "해당 없음" not in state:
            R.bad(f"{CO[co]}: 7장 「{item}」 받은 글 인용 번호 없음")
    R.p(f"  → 지시서 항목 {len(REQ_ITEMS)}개, 7장 표 {len(rows)}행")


def check_notfound(R, co, lines):
    R.p(f"## 6. 「추출 범위에 없음」 찾은 방법 — {CO[co]}")
    incode = False
    n = 0
    para = []
    sec = ""
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if ln.startswith("```"):
            incode = not incode
            continue
        if incode or "추출 범위에 없음" not in ln or sec == VREC:
            continue
        n += 1
        # 같은 줄, 또는 바로 다음 note: 줄, 또는 표 아래 note 를 가리키는 표시
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if any(t in ln for t in TRAIL) or (nxt.startswith("note:") and any(t in nxt for t in TRAIL)):
            continue
        para.append(i + 1)
    for x in para:
        R.bad(f"{CO[co]} {x}행: 「추출 범위에 없음」 줄에 찾은 방법(검색어·범위) 표시 없음")
    R.stats[co + "_nf"] = n
    R.p(f"  → 「추출 범위에 없음」 {n}줄, 찾은 방법 없는 줄 {len(para)}")


def secret_values():
    vals = []
    for k in ("DART_API_KEY", "LAW_OC", "OC", "DART_KEY"):
        v = os.environ.get(k, "").strip()
        if len(v) >= 6:
            vals.append(v)
    if os.path.exists(".env"):
        for ln in open(".env", encoding="utf-8", errors="ignore"):
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if k.strip() in ("DART_API_KEY", "LAW_OC", "OC", "DART_KEY") and len(v) >= 6:
                    vals.append(v)
    return vals


def check_misc(R, mds):
    R.p("## 7. 인증값·PDF·검증 기록 절")
    vals = secret_values()
    files = list(MD.values()) + list(TOC.values()) + [os.path.abspath(__file__), OUT_TXT]
    for f in files:
        if not os.path.exists(f):
            continue
        s = open(f, encoding="utf-8", errors="ignore").read()
        for v in vals:
            if v in s:
                R.bad(f"{f}: 인증값 문자열이 들어 있음(값은 찍지 않음)")
    R.p(f"  인증값 후보 {len(vals)}개로 {len(files)}개 파일 확인(값은 찍지 않음)")
    pdfs = [os.path.join(a, f) for a, _, fs in os.walk(OUTD) for f in fs if f.lower().endswith(".pdf")]
    if pdfs:
        R.bad(f"산출 폴더에 PDF {len(pdfs)}개: {pdfs[:3]}")
    R.p(f"  산출 폴더 PDF {len(pdfs)}개")
    for co, lines in mds.items():
        hs = [i for i, ln in enumerate(lines) if ln.strip() == VREC]
        h2 = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
        if len(hs) != 1:
            R.bad(f"{CO[co]}: 「{VREC}」 절이 {len(hs)}개")
        elif h2[-1] != hs[0]:
            R.bad(f"{CO[co]}: 「{VREC}」 가 맨 끝 절이 아님")
        else:
            body = "\n".join(lines[hs[0]:])
            for sub in ("### 대조한 인용", "### 고친 곳(전 → 후)", "### 채운 항목", "### 「추출 범위에 없음」 반박 시도", "### 남은 문제"):
                if sub not in body:
                    R.bad(f"{CO[co]}: 검증 기록에 「{sub}」 없음")
            sub = body.split("### 「추출 범위에 없음」 반박 시도", 1)[-1].split("### 남은 문제")[0]
            for jo in REFUTE:
                if f"- 「{jo}」" not in sub:
                    R.bad(f"{CO[co]}: 검증 기록 반박 시도에 「{jo}」 줄 없음")


def verify():
    load_meta()
    R = Report()
    R.p(f"# 13차 9-4 메리츠·한국투자 검증 — {TODAY} (scripts/dart/verify13_g_meritz_kis.py)")
    R.p("")
    for k, d in DOCS.items():
        if k.startswith("R9_"):
            continue
        if sha(d["path"]) != d["txt_sha_list"]:
            R.bad(f"{k}: 텍스트 sha256 이 텍스트목록.csv 와 다름")
    mds = {}
    allq = {}
    for co in ("M", "K"):
        lines, quotes = check_quotes(R, co, MD[co])
        mds[co] = lines
        allq[co] = quotes
        R.p("")
    for co in ("M", "K"):
        check_header(R, co, mds[co])
        check_toc(R, co)
        check_titles(R, co, mds[co])
        check_tags(R, co, allq[co])
        check_request(R, co, mds[co], allq[co])
        check_notfound(R, co, mds[co])
        R.p("")
    check_misc(R, mds)
    R.p("")
    R.p(f"문제 {len(R.problems)}건")
    os.makedirs(WORK, exist_ok=True)
    open(OUT_TXT, "w", encoding="utf-8").write("\n".join(R.out) + "\n")
    print(f"인용 메리츠 {R.stats.get('M_ok')}/{R.stats.get('M_quotes')}, 한국투자 {R.stats.get('K_ok')}/{R.stats.get('K_quotes')}; "
          f"CSV 메리츠 {R.stats.get('M_toc_ok')}/{R.stats.get('M_toc')}, 한국투자 {R.stats.get('K_toc_ok')}/{R.stats.get('K_toc')}; 문제 {len(R.problems)}건 → {OUT_TXT}")
    for x in R.problems[:60]:
        print(" ✗", x[:220])
    return R


def check_header(R, co, lines):
    """md 머리 문서 표의 sha256·쪽수·원본 수집이 메타와 같은지."""
    R.p(f"## 2. 머리 문서 표 — {CO[co]}")
    for ln in lines[:40]:
        if not ln.startswith("| ") or "|---" in ln or ln.startswith("| 문서 키"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if c[0] not in DOCS:
            continue
        d = DOCS[c[0]]
        errs = []
        if c[1] != d["name"]:
            errs.append("문서명")
        if c[2] not in (d.get("rcp", ""), d["url"]):
            errs.append("접수번호·URL")
        if c[3].strip("`").rstrip("…") != d["src_sha"][:16]:
            errs.append("원본 sha256")
        if c[4].strip("`").rstrip("…") != sha(d["path"])[:16]:
            errs.append("텍스트 sha256")
        if c[5] != str(T(c[0]).npages):
            errs.append("쪽수")
        if c[6] != d["fetched"][:19]:
            errs.append(f"원본 수집({d['fetched'][:19]})")
        if errs:
            R.bad(f"{CO[co]} 머리 표 {c[0]}: " + ", ".join(errs))
        else:
            R.p(f"  ✓ {c[0]}")

# ───────────────────────────── 보정(fix) ─────────────────────────────
# 검증 전 사본(pre/)에서 시작해 아래 보정을 차례로 적용 → 대상 파일에 씀(몇 번 돌려도 결과가 같음).
DIRECTIVE = {"M": {"3", "4", "5", "17", "21", "22", "24", "27", "34", "53", "55", "9", "57"},
             "K": {"3", "4", "5", "17", "21", "22", "24", "27", "34", "53", "55"}}
HEADINGS = [  # 3장 조별 머리 — 「N조 제목」 → 「N조(제목)」
    ("### 3조 적용대상 — ", "### 3조(적용대상) — "),
    ("### 4조·5조 위험관리 철학·원칙", "### 4조(위험관리 철학)·5조(위험관리 원칙)"),
    ("### 9조·57조 — ", "### 9조(그룹위험관리위원회)·57조(비상계획) — "),
    ("### 17조 의사전달체계 — ", "### 17조(의사전달체계) — "),
    ("### 21조 신용위험·22조 시장위험·24조 금리위험 — ", "### 21조(신용위험)·22조(시장위험)·24조(금리위험) — "),
    ("### 27조 전략 및 평판위험 — ", "### 27조(전략 및 평판위험) — "),
    ("### 34조 해외위험 — ", "### 34조(해외위험 관리) — "),
    ("### 53조 위기대응조직 — ", "### 53조(위기대응조직) — "),
    ("### 55조 조기경보체계 — ", "### 55조(조기경보체계) — "),
]
SEC6_KEY = {"3": "3", "4·5": "4·5", "17": "17", "21": "21", "22": "22", "24": "24", "27": "27", "34": "34", "53": "53",
            "55": "55", "목차": "목차(규정명)"}
REF_KEY = {"3": "3", "4·5": "4·5", "17": "17", "21": "21·22·24", "22": "21·22·24", "24": "21·22·24", "27": "27", "34": "34",
           "53": "53", "55": "55", "목차": "규정전문"}
FIXLOG = {"M": [], "K": []}


def rep(co, s, old, new, count=1, why=""):
    n = s.count(old)
    if n != count:
        raise SystemExit(f"[fix {co}] 바꿀 글이 {n}번 나옴(기대 {count}): {old[:80]}")
    FIXLOG[co].append((why, old, new))
    return s.replace(old, new)


def tag_line(co, old):
    """「- 이 글이 닿는 모범규준 조/항목: 4·5, 목차, 9 (조 대응은 판단)」 → 「N조(제목)」 꼴."""
    jo = load_jo()
    body = old.split(":", 1)[1].replace("(조 대응은 판단)", "").strip()
    out = []
    for it in [x.strip() for x in body.split(",") if x.strip()]:
        if it == "목차":
            out.append("조문 목차(지시서 9-4 1.)")
        elif it == "참고":
            out.append("56조(통합위기상황분석)(판단)·35조(경영에의 활용)(판단) — 9-5 범위 참고")
        else:
            parts = []
            for no in it.split("·"):
                t = jo[no][0]
                parts.append(f"{no}조({t})" + ("" if no in DIRECTIVE[co] else "(판단)"))
            out.append("·".join(parts))
    return f"{TAG_LINE}(조 제목은 2016.8.1판): " + ", ".join(out) + " — 글과 조의 대응은 판단(아래 note)"


def cut(key, p1, p2, start, end, start_n=1, end_exact=False):
    t = T(key)
    idx = [i for i, p in enumerate(t.page) if p1 <= p <= p2]
    c, a = 0, None
    for i in range(idx[0], idx[-1] + 1):
        if start in t.lines[i]:
            c += 1
            if c == start_n:
                a = i
                break
    if a is None:
        raise SystemExit(f"[cut] {key} p.{p1}~{p2} 시작 앵커 없음: {start}")
    for j in range(a, idx[-1] + 1):
        ln = t.lines[j]
        if (ln.strip() == end) if end_exact else (end in ln):
            return t.lines[a:j + 1]
    raise SystemExit(f"[cut] {key} 끝 앵커 없음: {end}")


def cite_line(key, code):
    res, fail = find_segs(key, code)
    if res is None:
        raise SystemExit(f"[cite] {key} 글을 못 찾음")
    d = DOCS[key]
    parts = [d["name"]]
    if "rcp" in d:
        parts += [f"접수번호 {d['rcp']}", d["url"]]
    else:
        parts += [f"{d['url']} (방식 {d['method']})" if d.get("method") else d["url"]]
    parts += [T(key).plabel(res[0], res[1]), f"원본 수집 {d['fetched'][:10]}", f"옮김 {TODAY}"]
    return "- 인용: [" + " · ".join(parts) + "]"


def qblock(co, qid, title, key, code, tags, notes):
    o = [f"#### [{qid}] {title}", "", cite_line(key, code), f"{TAG_LINE}(조 제목은 2016.8.1판): {tags} — 글과 조의 대응은 판단(아래 note)"]
    if key in CORR:
        o.append(corr_line(key, code))
    o += ["", "```text"] + code + ["```", ""] + notes + [""]
    return o


def mob_lines(ver):
    return open(MOBEOM_HWP[ver], encoding="utf-8").read().split("\n")


def mob_cut(ver, start, end=None, after=None):
    L = mob_lines(ver)
    a = next(i for i, ln in enumerate(L) if ln.strip().startswith(start) and (after is None or i > after))
    if end is None:
        return L[a:a + 1], a
    b = next(i for i in range(a, len(L)) if L[i].strip().startswith(end))
    return L[a:b + 1], b


def mob_cite(ver, art):
    src, url = MOBEOM_CITE[ver]
    meta = mobeom_meta(ver)
    nm = "「금융지주회사 통합위험관리 모범규준」 2016.8.1판" if ver == "2016.8.1판" else "「금융지주회사 통합리스크관리 모범규준」 2012.3.13 제정판"
    return "- 인용: [" + " · ".join([nm, src, url, art, f"원본 sha256 {meta['sha256'][:16]}",
                                    f"수집 2026-10-07(UTC; .meta.json fetched_at {meta['fetched_at']})", f"옮김 {TODAY}"]) + "]"


def mblock(qid, title, ver, art, code, tags, notes):
    return [f"#### [{qid}] {title}", "", mob_cite(ver, art), f"{TAG_LINE}(조 제목은 2016.8.1판): {tags} — 모범규준 원문",
            "", "```text"] + code + ["```", ""] + notes + [""]


def meritz_cites():
    """연차보고서 회의 개최내역에서 「그룹리스크관리규정 제N조 …」 인용 자리를 모두 셈."""
    t = T("M_AR")
    meet, kind = None, ""
    out = {}
    for i, ln in enumerate(t.lines):
        m = re.search(r"제2025년도 제(\d+)차 그룹리스크관리위원회 : (\d{4})\.(\d{2})\.(\d{2})", ln)
        if m:
            meet = f"제{m.group(1)}차({m.group(2)}.{m.group(3)}.{m.group(4)})"
        if re.search(r"^\s*1\) 보고안건", ln):
            kind = "보고안건"
        if re.search(r"^\s*2\) 의결안건", ln):
            kind = "의결안건"
        for mm in re.finditer(r"그룹리스크관리규정 (제\d+조)(?: (\d+)항)?((?:, 제\d+조)*)", ln):
            arts = [mm.group(1) + (f" {mm.group(2)}항" if mm.group(2) else "")] + re.findall(r"제\d+조", mm.group(3))
            item = re.match(r"^\s*([가-힣])\.", ln)
            for a in arts:
                out.setdefault(a, []).append((meet, kind, item.group(1) if item else "?", t.page[i]))
    return out


def meritz_table():
    cites = meritz_cites()
    jo = load_jo()
    t = T("M_AR")
    rows = []
    spec = [("제6조 5항", "6", "①~③항뿐(5항 없음) — [MB-1]", "다름 — 메리츠 문맥은 대규모 투자(CPS 인수) 보고, 모범규준 6조는 문서화 체계"),
            ("제9조 6항", "9", "⑥항 결의사항(2호 「부담 가능한 위험수준의 결정」) — [MB-2]·[MB-3]", "같음 — 조·항 번호와 내용(리스크 허용한도 심의·의결)이 맞음"),
            ("제9조 7항", "9", "⑦항 보고사항(2호 「위험관리 상태 및 한도관리 현황」, 3호 「자회사등의 위험관리위원회가 결의한 사항」) — [MB-2]·[MB-3]",
             "같음 — 조·항 번호와 내용(리스크상태·한도관리 현황, 계열사 위원회 결의사항 보고)이 맞음"),
            ("제57조", "57", "①~③항(통합위기상황분석 결과를 활용한 유동성 위기단계별 비상계획, 연 1회 이상 점검·보고) — [MB-4]",
             "일부 — 메리츠 문맥 「그룹 통합 위기상황분석 및 유동성 관리현황 보고」의 「유동성」 쪽과 닿음"),
            ("제58조", "58", "①·②항(자회사등 위기관리체계 연 1회 이상 점검·지주 제출, 지주의 조정 요청) — [MB-4]",
             "일부 — 「위기상황분석 … 보고」의 근거로 함께 인용. 「통합위기상황분석」 자체는 모범규준 56조(통합위기상황분석, [MB-4])")]
    for art, no, hang, judge in spec:
        locs = cites.get(art, [])
        by = {}
        for meet, kind, item, pg in locs:
            by.setdefault((meet, kind, pg), []).append(item)
        where = "; ".join(f"{meet} {kind} {'·'.join(items)} {t.plabel(pg)}" for (meet, kind, pg), items in by.items())
        rows.append(f"| 그룹리스크관리규정 {art} | {len(locs)}회 — {where} | {no}조 {jo[no][0]} | {no}조 {jo[no][1]} | {hang} | {judge}(판단) |")
    rows.append(f"| (참고) 인용 없음 | - | 56조 {jo['56'][0]} | 56조 {jo['56'][1]} | ①항 연 1회 이상 통합위기상황분석·이사회 또는 경영진 보고 — [MB-4] | "
                f"메리츠 보고 이름 「그룹 통합 위기상황분석」과 주제가 같음 — 메리츠는 이 보고 근거로 제57조·제58조를 적음(판단) |")
    return rows, cites


def build_meritz_mobeom():
    """1-2-1 소표 + 모범규준 원문 인용 [MB-1]~[MB-4]."""
    rows, cites = meritz_table()
    n97 = len(cites.get("제9조 7항", []))
    o = ["### 1-2-1 메리츠 인용 조 번호 ↔ 모범규준 같은 번호 조 제목(검증 2026-10-07 추가)", "",
         "인용 자리는 연차보고서 「그룹리스크관리위원회 회의 개최내역」의 「※ 비 고」 칸을 스크립트로 다시 셈(인용 원문은 [M-4]~[M-8]). "
         "모범규준 조 제목은 `dart_out/risk13/모범규준_조목록.csv`, 항 구성은 아래 [MB-1]~[MB-4](hwp 원문).", "",
         "| 메리츠 인용(원문 표기) | 인용 횟수·자리(회의·안건 구분·항목·쪽) | 모범규준 같은 번호 조 — 2016.8.1판 제목 | 같은 번호 조 — 2012.3.13 제정판 제목 | 같은 번호 조의 항 구성 | 주제 대응 |",
         "|---|---|---|---|---|---|"] + rows + [""]
    n9m = sum(1 for k in DOCS if k.startswith("R9_") and DOCS[k]["co"] == "메리츠금융지주")
    o.append(f"note: 재확인(2026-10-07) — 「그룹리스크관리규정 제9조 7항」은 {n97}회(제1·3·5·7·9차), 「제57조」「제58조」는 「제57조, 제58조」로 함께 2회(제1·5차), "
             "「제6조 5항」은 제6차 보고안건 가·나에 같은 글로 2회, 「제9조 6항」은 제9차 의결안건 1회. 연차보고서 밖(사업보고서 원본·정정판 4건, 경영공시, "
             f"dart_out/text/risk9 의 메리츠 정기보고서 {n9m}건)에서는 「그룹리스크관리규정 제N조」 꼴 인용을 찾지 못함(정규식 "
             "`(그룹\\s*리스크\\s*(관리\\s*)?(위원회\\s*)?규정|리스크관리규정|그룹\\s*위험\\s*관리\\s*규정)\\s*(제\\s*\\d+\\s*(조|장))`).")
    o.append("note: 사용자 표의 「9조 7항, 57조」는 원문 「제9조 7항」, 「제57조, 제58조」와 맞음 — 57조는 늘 58조와 함께, 「금융회사 지배구조에 관련 법률 감독규정 제8조」와 나란히 인용됨.")
    o.append("note: 메리츠 첨부6 위원회규정 제5조 ①·제6조의 낱말(「그룹리스크관리규정」, 「그룹리스크협의회」, 「그룹리스크관리최고책임자」, 「리스크」)은 "
             "모범규준 2012.3.13 제정판 9조 ⑥·⑦([MB-3])과 같고 2016.8.1판([MB-2] — 「그룹위험관리규정」, 「그룹위험관리협의회」, 「그룹위험관리책임자」, 「위험」)과는 다름 "
             "— 메리츠 규정 체계는 2012 제정판 낱말을 따름(판단). 조 번호(9·57·58)는 두 판이 같음(모범규준_조목록.csv).")
    o.append("")
    # [MB-1] 2016.8.1판 제6조
    v = "2016.8.1판"
    h6, _ = mob_cut(v, "제6조(문서화)")
    L = mob_lines(v)
    i6 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제6조(문서화)"))
    i7 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제 2 장"))
    two = [ln for ln in L[i6:i7] if ln.strip().startswith(("②", "③"))]
    code = h6 + ["[줄임: ①항 1호~12호(문서화 대상) — 원문은 9-4_모범규준_원문.md 5장]"] + two
    o += mblock("MB-1", "모범규준 2016.8.1판 제6조(문서화) — ①항 머리·②·③항", v, "제6조", code, "6조(문서화)(판단)",
                ["note: 모범규준 6조는 ①~③항뿐 — 메리츠 「그룹리스크관리규정 제6조 5항」(대규모 투자 보고)과 항 번호·주제가 맞지 않음(판단)."])
    # [MB-2] 2016.8.1판 제9조 ⑥·⑦
    i9 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제9조("))
    i6h = next(i for i in range(i9, len(L)) if ln_startswith(L[i], "⑥"))
    i7h = next(i for i in range(i6h, len(L)) if ln_startswith(L[i], "⑦"))
    i7e = next(i for i in range(i7h, len(L)) if L[i].strip().startswith("5. 그 밖에"))
    code = [L[i9], "[줄임: ②~⑤항]"] + L[i6h:i7e + 1]
    o += mblock("MB-2", "모범규준 2016.8.1판 제9조(그룹위험관리위원회) — ⑥항(결의사항)·⑦항(보고사항)", v, "제9조", code,
                "9조(그룹위험관리위원회)", ["note: ⑥ 2호 「부담 가능한 위험수준의 결정」 ↔ 메리츠 제9조 6항 「리스크 허용한도 심의‧의결」, "
                                     "⑦ 2호·3호 ↔ 메리츠 제9조 7항 「리스크상태 및 한도관리 현황보고」「계열사 리스크관리위원회의 결의사항 보고」(판단)."])
    # [MB-3] 2012.3.13 제정판 제9조 ⑥ 5·6호, ⑦ 머리
    v2 = "2012.3.13 제정판"
    L2 = mob_lines(v2)
    j9 = next(i for i, ln in enumerate(L2) if ln.strip().startswith("제9조("))
    j6 = next(i for i in range(j9, len(L2)) if ln_startswith(L2[i], "⑥"))
    j7 = next(i for i in range(j6, len(L2)) if ln_startswith(L2[i], "⑦"))
    j65 = next(i for i in range(j6, j7) if L2[i].strip().startswith("5."))
    code = [L2[j9], "[줄임: ②~⑤항]", L2[j6], "[줄임: ⑥항 1~4호]"] + L2[j65:j65 + 2] + ["[줄임: ⑥항 7호]", L2[j7]]
    o += mblock("MB-3", "모범규준 2012.3.13 제정판 제9조(그룹리스크관리위원회) — ⑥항 5·6호, ⑦항 머리", v2, "제9조", code,
                "9조(그룹위험관리위원회)", ["note: 「｢그룹리스크관리규정｣의 제정 및 개정」「그룹리스크협의회」「그룹리스크관리최고책임자 등을 경유하여 보고」 — "
                                      "메리츠 첨부6 제5조 ① 5·6호, 제6조([M-15])의 낱말과 같음(판단)."])
    # [MB-4] 2016.8.1판 제56조 ①, 제57조, 제58조
    i56 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제56조("))
    i57 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제57조("))
    i59 = next(i for i, ln in enumerate(L) if ln.strip().startswith("제 7 장"))
    code = [L[i56], "[줄임: 제56조 ②~⑥항]"] + L[i57:i59]
    o += mblock("MB-4", "모범규준 2016.8.1판 제56조(통합위기상황분석) ①항, 제57조(비상계획), 제58조(위기관리체계의 정기적 점검)", v,
                "제56조~제58조", code, "56조(통합위기상황분석)(판단), 57조(비상계획), 58조(위기관리체계의 정기적 점검)(판단)",
                ["note: 메리츠 보고 「그룹 통합 위기상황분석 및 유동성 관리현황」은 56조(통합위기상황분석)와 57조(비상계획: 유동성 위기단계별) 주제에 걸침 — "
                 "메리츠 규정 제57·58조가 모범규준 57·58조와 같은 제목인지는 규정 전문이 추출 범위에 없어 확인 못 함(판단; 찾은 범위는 1-1 아래 note·검증 기록 「규정전문」)."])
    return o


def ln_startswith(ln, ch):
    return ln.strip().startswith(ch)


def notfound_pointers(co, lines):
    """「추출 범위에 없음」 줄에 찾은 방법이 안 보이면 해당 조의 6장 검색 기록·검증 기록 반박 줄을 가리키는 표시를 붙임."""
    incode = False
    sec = sub = ""
    head_jo = None
    n = 0
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            incode = not incode
            continue
        if incode:
            continue
        if ln.startswith("## "):
            sec, sub, head_jo = ln, "", None
        elif ln.startswith("### "):
            sub = ln
            m = re.match(r"### (\d+)조", ln)
            head_jo = m.group(1) if m else None
            if head_jo in ("4", "5"):
                head_jo = "4·5"
        if "추출 범위에 없음" not in ln or any(t in ln for t in TRAIL):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.startswith("note:") and any(t in nxt for t in TRAIL):
            continue
        if sec.startswith("## 0.") and ln.startswith("| "):
            k = ln.strip("| ").split("|")[0].strip()
            k = k.split("(")[0]
            ptr = f"찾은 방법: 6장 「{SEC6_KEY.get(k, k)}」 줄·검증 기록 「{REF_KEY.get(k, k)}」 줄"
            if k in ("21", "22", "24"):
                ptr = f"찾은 방법: 6장 「{k}」「21·22·24(연결·통합)」 줄·검증 기록 「21·22·24」 줄"
        elif sec.startswith("## 1."):
            ptr = "찾은 범위: 1-1 아래 note·6장 「목차(규정명)」 줄·검증 기록 「규정전문」 줄"
        elif head_jo:
            k6 = SEC6_KEY.get(head_jo, head_jo)
            if head_jo == "21":
                k6 = "21」「22」「24」「21·22·24(연결·통합)"
            ptr = f"찾은 방법: 6장 「{k6}」 줄·검증 기록 「{REF_KEY.get(head_jo, head_jo)}」 줄"
        else:
            ptr = "찾은 방법: 6장 검색 기록·검증 기록 반박 시도"
        if ln.startswith("| "):
            cells = ln.split("|")
            for j, c in enumerate(cells):
                if "추출 범위에 없음" in c:
                    cells[j] = c.rstrip() + f" ({ptr}) "
                    break
            new = "|".join(cells)
        else:
            new = ln.rstrip() + f" ({ptr})"
        lines[i] = new
        n += 1
    FIXLOG[co].append((f"「추출 범위에 없음」 줄 {n}곳에 찾은 방법 표시를 붙임(예: 「… 추출 범위에 없음 (찾은 방법: 6장 「55」 줄·검증 기록 「55」 줄)」)", "", ""))
    return lines


def apply_common(co, s):
    lines = s.split("\n")
    n = 0
    for i, ln in enumerate(lines):
        if ln.startswith("- 이 글이 닿는 모범규준 조/항목:"):
            new = tag_line(co, ln)
            if n == 0:
                FIXLOG[co].append(("인용마다 붙은 조 태그 줄을 「N조(조 제목)」 꼴로(지시서 조 번호는 그대로, 새로 붙인 조는 「(판단)」) — 첫 예", ln, new))
            lines[i] = new
            n += 1
    FIXLOG[co].append((f"조 태그 줄 {n}곳 모두 같은 방식으로 바꿈", "", ""))
    s = "\n".join(lines)
    for old, new in HEADINGS:
        if old in s:
            s = rep(co, s, old, new, why="3장 조별 머리에 조 제목(2016.8.1판)")
    s = rep(co, s, "줄은 깨진 자리에 이 작업이 끼운 표시(원문 아님).", "줄은 깨진 자리에 이 작업이 끼운 표시(원문 아님). "
            "「[줄임: …]」 줄은 이 작업이 옮기지 않은 줄을 줄인 자리(원문 아님, 검증 추가).", why="머리 — 「[줄임: …]」 표시 설명")
    s = rep(co, s, "모범규준 조 번호·제목은 2016.8.1 판(`dart_out/risk13/모범규준_조목록.csv`, 원문은 `9-4_모범규준_원문.md`).",
            "모범규준 조 번호·제목은 2016.8.1 판(`dart_out/risk13/모범규준_조목록.csv`, 원문은 `9-4_모범규준_원문.md`).\n"
            "- 조 태그(검증 2026-10-07 보정): 인용마다 「이 글이 닿는 모범규준 조」를 「N조(조 제목)」으로 적음 — 지시서 9-4 에 적힌 조 번호"
            f"({'3·4·5·17·21·22·24·27·34·53·55, 메리츠 인용 조문 9·57' if co == 'M' else '3·4·5·17·21·22·24·27·34·53·55'})는 그대로, "
            "이 작업이 붙인 조는 「(판단)」. 검증 기록은 맨 끝 「검증 기록(2026-10-07)」, 대조 스크립트 `scripts/dart/verify13_g_meritz_kis.py`(결과 `dart_out/risk13/verify13_g_meritz_kis.txt`).",
            why="머리에 조 태그 규칙·검증 기록 안내")
    return s


def insert_before(co, s, anchor, block_lines, why):
    if s.count(anchor) != 1:
        raise SystemExit(f"[fix {co}] 끼울 자리 앵커가 {s.count(anchor)}번: {anchor[:60]}")
    FIXLOG[co].append((why, "", ""))
    return s.replace(anchor, "\n".join(block_lines) + "\n" + anchor)


def fix_meritz():
    co = "M"
    s = open(os.path.join(PRE, os.path.basename(MD[co])), encoding="utf-8").read()
    s = apply_common(co, s)
    s = rep(co, s, "「유동성 관리」는 57조(유동성 위기 비상계획)와 닿음", "「유동성 관리」는 57조(비상계획: 유동성 위기단계별 비상계획)와 닿음",
            why="1-2 표 — 57조 괄호 안을 조 제목으로(조목록 제목 「비상계획」)")
    s = rep(co, s, "- 26조(신용편중, 판단)", "- 26조(신용편중위험, 판단)", why="4장 — 26조 제목(조목록 「신용편중위험」)")
    # 0장 요약표
    s = rep(co, s, "| 연차보고서 p.141, 사업보고서 p.278(가까운 글) | 가까운 글: [M-12] 이사회 부의사항 「시정, 권고 및 자료제출 요구」, [M-16] 「가이드라인을 제시」(판단) |",
            "| 연차보고서 p.141·p.100, 사업보고서 p.278(가까운 글) | 가까운 글: [M-12] 이사회 부의사항 「시정, 권고 및 자료제출 요구」, [M-16] 「가이드라인을 제시」, "
            "[M-24] 경영협의회 「지주 및 자회사 간의 원활한 의사소통과 협조체제 구축」(검증 추가)(판단) |", why="0장 17조 행 — 검증에서 찾은 가까운 글 [M-24]")
    s = rep(co, s, "[M-10] 「전략적 의사결정에 대한 리스크를 측정·관리하고자 그룹리스크협의회를 설치」, [M-16] 분류 「비재무리스크」 |",
            "[M-10] 「전략적 의사결정에 대한 리스크를 측정·관리하고자 그룹리스크협의회를 설치」, [M-16] 분류 「비재무리스크」, "
            "[M-24] 경영협의회 「전략적 의사결정 협의」·「리스크협의회에서 검토를 요청」(검증 추가, 판단) |", why="0장 27조 행 — [M-24]")
    s = rep(co, s, "| 연차보고서 p.31, 사업보고서 p.433(가까운 글) | 가까운 글: [M-13]·[M-23] 이사회에 「그룹 비상 상황 대응 현황 보고」(판단) |",
            "| 연차보고서 p.31, 사업보고서 p.433·p.82·p.91(가까운 글) | 가까운 글: [M-13]·[M-23] 이사회에 「그룹 비상 상황 대응 현황 보고」, [M-26] 사업보고서 지주 서술 「선제적인 위기 대응체제를 구축」, [M-25] 자회사 메리츠증권 「위기상황 단계별 대비책」(검증 추가)(판단) |",
            why="0장 53조 행 — [M-25]")
    s = rep(co, s, "| 연차보고서·사업보고서·경영공시 전체(6장 검색어) | 가까운 글: [M-9] 협의회 「그룹 유동성위기 시나리오 설정 및 변경」(57조 쪽, 판단) |",
            "| 연차보고서·사업보고서·경영공시 전체(6장 검색어); 가까운 글 연차보고서 p.102, 사업보고서 p.91 | 가까운 글: [M-9] 협의회 「그룹 유동성위기 시나리오 설정 및 변경」(57조 쪽, 판단), [M-25] 자회사 메리츠증권 「위기상황 단계별 대비책」(검증 추가, 판단) |",
            why="0장 55조 행 — [M-25]")
    # 1-2 소표·모범규준 원문
    s = rep(co, s, "note: 위 넷 가운데 제9조는 모범규준과 조·항 번호가 그대로 맞고, 제6조는 맞지 않음, 제57·58조는 판정 못 함(판단).",
            "note: 위 넷 가운데 제9조는 모범규준과 조·항 번호가 그대로 맞고, 제6조는 맞지 않음, 제57·58조는 판정 못 함(판단). 인용 횟수·자리 재확인과 "
            "모범규준 같은 번호 조 제목(2016.8.1판·2012.3.13 제정판)은 1-2-1 소표.", why="1-2 note — 1-2-1 소표 안내")
    s = insert_before(co, s, "### 1-3 그룹리스크관리위원회규정(첨부6) 조문 목차와 모범규준 대응", build_meritz_mobeom(),
                      "1-2-1 소표(메리츠 인용 조 번호 ↔ 모범규준 같은 번호 조 제목)와 모범규준 원문 인용 [MB-1]~[MB-4] 추가")
    s = rep(co, s, "첨부6 문구가 9조 ⑥·⑦항을 거의 그대로 옮긴 꼴이라 그룹리스크관리규정 제9조 6·7항이 같은 내용을 두고 위원회 규정이 다시 적은 것으로 보임(판단).",
            "첨부6 문구가 9조 ⑥·⑦항을 거의 그대로 옮긴 꼴이라 그룹리스크관리규정 제9조 6·7항이 같은 내용을 두고 위원회 규정이 다시 적은 것으로 보임(판단). "
            "낱말은 2016.8.1판보다 2012.3.13 제정판과 같음(1-2-1 소표 아래 note, [MB-3], 검증 추가).", why="1-3 note — 2012 제정판 낱말 일치")
    # 17조 — [M-24]
    s = rep(co, s, "셋 다 문서 형식은 적혀 있지 않음(판단).",
            "셋 다 문서 형식은 적혀 있지 않음(판단). 검증(2026-10-07)에서 더 넓힌 검색어로 다시 찾아 [M-24] 경영협의회(지주·자회사 의사소통 협의체 — "
            "「자유 토론을 통해 도출된 결론은 각사 CEO에 의해 집행」)를 가까운 글로 더함 — 여기에도 문서 형식(공식문서 등)은 없음(판단). "
            "모범규준 17조 ②항 6호·③항의 「공식문서」 낱말은 세 문서 어디에도 없음(검증 기록 「17」).", why="17조 note — 반박 시도 결과·[M-24]")
    t = T("M_AR")
    code = cut("M_AR", 100, 100, "8. 경영협의회", "습니다.", end_exact=True)
    blk = qblock(co, "M-24", "8. 경영협의회 — 가. 역할, 나. 협의절차(운영현황)(검증 추가)", "M_AR", code,
                 "17조(의사전달체계), 27조(전략 및 평판위험), 12조(그룹위험관리협의회)(판단)",
                 ["note: (검증 추가) 「지주 및 자회사 간의 원활한 의사소통과 협조체제 구축, … 전략적 의사결정 협의를 위하여 경영협의회를 설치」, "
                  "「위험관리와 관련된 사항이 있을 경우 … 리스크협의회에서 검토를 요청할 수 있고, 검토 결과를 경영협의회 안건에 반영」 — "
                  "지주·자회사 의사소통 체계(17조 ①항 쪽)와 전략적 의사결정의 위험 검토 경로(27조 ③항 쪽)에 닿는 가까운 글. 문서 형식·평판위험·측정 수단은 없음(판단)."])
    s = insert_before(co, s, "### 21조(신용위험)·22조(시장위험)·24조(금리위험) — ", blk, "17조 절에 [M-24] 인용 추가")
    # 27조
    s = rep(co, s, "note: [M-16] 41-1-1 은 리스크 분류에 「비재무리스크」를 두나 전략·평판을 따로 이름 붙이지 않음.",
            "note: [M-16] 41-1-1 은 리스크 분류에 「비재무리스크」를 두나 전략·평판을 따로 이름 붙이지 않음.\n"
            "note: (검증 추가) [M-24](17조 절) 경영협의회 — 「전략적 의사결정 협의」를 하고 「위험관리와 관련된 사항」은 「리스크협의회에서 검토를 요청」 "
            "— 전략적 의사결정의 위험 검토 경로로 읽힘(27조, 판단). 평판위험의 관리 체제·측정 수단은 더 넓힌 검색어로도 추출 범위에 없음(검증 기록 「27」).",
            why="27조 note — [M-24]·반박 실패")
    # 53 — [M-26] 지주 서술 「선제적인 위기 대응체제」
    code = cut("M_BR", 82, 82, "- 회사가 경쟁에서 우위를 점하기 위한 주요수단", "강화하여 업계 최고 수준의 수익 달성을 위해 지속적으로 노력하겠습니다.")
    blk = qblock(co, "M-26", "II. 사업의 내용 — 5. 재무건전성 등 기타 참고사항 — 마. 산업의 특성 … — 「회사가 경쟁에서 우위를 점하기 위한 주요수단」(지주 서술, 검증 추가)",
                 "M_BR", code, "53조(위기대응조직)",
                 ["note: (검증 추가) 「메리츠금융그룹 … 선제적인 위기 대응체제를 구축하여 건전성을 강화」 — 지주(그룹) 차원에서 위기 대응체제를 적은 유일한 문장. "
                  "위기대응조직의 구성·전환 요건은 적혀 있지 않음(53조 가까운 글, 판단). 「[주요종속회사에 관한 사항]」 머리(p.83) 앞의 지주 서술."])
    s = insert_before(co, s, "### 55조(조기경보체계) — ", blk, "53조 절 끝에 [M-26] 인용 추가")
    # 53·55 — [M-25]
    code = cut("M_BR", 91, 91, "(4) 유동성위험관리", "체제를 구축하여 운영하고 있습니다.")
    blk = qblock(co, "M-25", "II. 사업의 내용 — [주요종속회사에 관한 사항] <금융투자업 부문_메리츠증권> (4) 유동성위험관리(검증 추가 — 자회사 서술)",
                 "M_BR", code, "55조(조기경보체계), 53조(위기대응조직), 57조(비상계획)",
                 ["note: (검증 추가) 「유동성리스크 발생에 따른 위기상황에 대비하기 위하여 위기상황 단계별 대비책을 마련」 — 자회사 메리츠증권(사업보고서 "
                  "「<금융투자업 부문_메리츠증권>」 머리(p.87) 아래)의 유동성 위기 단계별 대비책. 지주 차원 조기경보 지표·발령 단계·위기대응조직이 아니라 "
                  "가까운 글로만 둠(55·53·57조, 판단). 단계 이름·지표는 이 쪽에 없음."])
    s = insert_before(co, s, "## 4. 참고 — 지시 목록 밖 조에 닿는 글", blk, "55조 절 끝에 [M-25] 인용 추가")
    s = rep(co, s, "note: 가까운 글 — [M-9] 협의회 심의·의결 사항 「그룹 유동성위기 시나리오 설정 및 변경」, [M-4]·[M-6] 그룹리스크관리규정 제57조·제58조에 따른 「그룹 통합 위기상황분석 및 유동성 관리현황」 반기 보고(56·57조 쪽, 판단).",
            "note: 가까운 글 — [M-9] 협의회 심의·의결 사항 「그룹 유동성위기 시나리오 설정 및 변경」, [M-4]·[M-6] 그룹리스크관리규정 제57조·제58조에 따른 「그룹 통합 위기상황분석 및 유동성 관리현황」 반기 보고(56·57조 쪽, 판단). "
            "검증(2026-10-07)에서 더 넓힌 검색어(경보·경고·징후·위기단계·관심/주의/경계/심각·Trigger·발령·신호등 등)와 risk9 메리츠 정기보고서 전체로 다시 찾음 — "
            "지주 차원 지표·발령 단계는 추출 범위에 없음, 자회사 메리츠증권 「위기상황 단계별 대비책」만 더함([M-25], 검증 기록 「55」).",
            why="55조 note — 반박 시도 결과·[M-25]")
    s = rep(co, s, "아래는 가까운 글 — 이사회에 「그룹 비상 상황 대응 현황」이 보고된 사실(판단).",
            "아래는 가까운 글 — 이사회에 「그룹 비상 상황 대응 현황」이 보고된 사실(판단). 검증(2026-10-07) 반박 시도(위기·비상·컨틴전시·대응조직·대책반·Crisis, risk9 정기보고서 포함)에서도 "
            "지주 위기대응조직의 구성·전환 요건은 찾지 못함 — 지주 서술 「선제적인 위기 대응체제를 구축」([M-26], 사업보고서 p.82)과 자회사 메리츠증권의 「비상대책실무」 협의체 이름·「위기상황 단계별 대비책」([M-25])만 있음(검증 기록 「53」).",
            why="53조 판정 줄 — 반박 시도 결과")
    # 5장
    add5 = ["| 받은 것(검증 추가) | 경영협의회 역할·협의절차 — 지주·자회사 의사소통, 전략적 의사결정 협의, 위험관리 사항은 리스크협의회 검토 요청(가까운 글) | 연차보고서 p.100(인쇄 90) [M-24] | 17·27 (가까운 글, 판단) |",
            "| 받은 것(검증 추가) | 자회사 메리츠증권 유동성위험관리 「위기상황 단계별 대비책」(가까운 글) | 사업보고서 p.91(DART 쪽 89) [M-25] | 55·53·57 (판단) |",
            "| 받은 것(검증 추가) | 지주 서술 「선제적인 위기 대응체제를 구축하여 건전성을 강화」(가까운 글 — 구성·전환 요건 없음) | 사업보고서 p.82(DART 쪽 80) [M-26] | 53 (판단) |",
            "| 받은 것(검증 추가) | 메리츠 인용 조 번호 ↔ 모범규준 같은 번호 조 제목 소표, 모범규준 원문 [MB-1]~[MB-4] | 1-2-1 | 6·9·56·57·58 |",
            "| 원문과 다른 것(검증 추가) | 제6차(2025.09.19) 보고안건 가·나가 같은 글(「그룹리스크관리규정 제6조 5항에 의거, 그룹 CPS 인수관련 투자의 건 보고」)로 두 번 적힘 | 연차보고서 p.92(인쇄 82) [M-7] | 15 (판단) |",
            "| 원문과 다른 것(검증 추가) | 첨부6 위원회규정 제5조 ①·제6조 낱말이 모범규준 2016.8.1판이 아니라 2012.3.13 제정판 9조 ⑥·⑦ 낱말과 같음(「그룹리스크관리규정」「그룹리스크협의회」「그룹리스크관리최고책임자」) | 첨부6 p.164 vs [MB-2]·[MB-3] | 9 |"]
    s = insert_before(co, s, "\n## 6. 검색 기록", add5, "5장 표에 검증 추가 행")
    return s


def fix_kis():
    co = "K"
    s = open(os.path.join(PRE, os.path.basename(MD[co])), encoding="utf-8").read()
    s = apply_common(co, s)
    for old, new, why in [
        ("12조 / ③항은 53조(위기 시 구성 확대)", "12조 / ③항은 53조(위기대응조직: 위기 시 구성 확대)", "1-3 표 — 53조 괄호 안을 조 제목으로"),
        ("③항은 53조(비상경영 시 즉시 소집)", "③항은 53조(위기대응조직: 비상경영 시 즉시 소집)", "1-3 표 — 53조 괄호 안을 조 제목으로"),
        ("27조(전략적 의사결정의 리스크 검토)", "27조(전략 및 평판위험: 전략적 의사결정의 리스크 검토)", "1-3 표 — 27조 괄호 안을 조 제목으로"),
        ("17조(자료제출·서류 보존 요구 — 문서 형식 없음)", "17조(의사전달체계: 자료제출·서류 보존 요구 — 문서 형식 없음)", "1-3 표 — 17조 괄호 안을 조 제목으로"),
    ]:
        s = rep(co, s, old, new, why=why)
    s = rep(co, s, "3조(규준 적용 배제)", "3조(적용대상: 규준 적용 배제)", count=s.count("3조(규준 적용 배제)"),
            why="3조 판정 줄·[K-21] note — 3조 괄호 안을 조 제목으로")
    s = rep(co, s, "| 연결 통합 측정(연결 신용익스포져 기준) 서술은 추출 범위에 없음 |",
            "| 연결 통합 측정(연결 신용익스포져 기준) 서술은 추출 범위에 없음; 가까운 글 [K-15] 「원칙적으로 그룹 내 모든 자회사 등을 대상으로 리스크를 측정」"
            "·「통합 내부자본에 반영」(18조 ③·19조 쪽, 검증 추가, 판단) |", why="0장 21조 행 — 가까운 글")
    s = rep(co, s, "| 1장 |\n", "| 1장; [K-28] 그룹리스크관리규정 2026.05.08 다시 일부개정(검증 추가) |\n", why="0장 목차 행 — [K-28]")
    s = rep(co, s, "| 추출 범위에 없음 | 2025.08.21 일부개정. 제2장·제3장",
            "| 추출 범위에 없음 | 2025.08.21 일부개정(2026.05.08 다시 일부개정 — [K-28], 검증 추가). 제2장·제3장", why="1-1 표 — 2026.05.08 개정")
    s = rep(co, s, "| 추출 범위에 없음 | 위기상황·비상경영 정의는 이 지침에 있다고 함 |",
            "| 추출 범위에 없음 | 위기상황·비상경영 정의는 이 지침에 있다고 함. 2022.04.28·2023.10.26 리스크관리위원회 개정 승인([K-30]·[K-29], 검증 추가) |\n"
            "| 그룹외화유동성리스크관리업무시행세칙 | 사업보고서(2023.12) 20240321001204 p.474(DART 쪽 472) [K-29] | 추출 범위에 없음 | 2023.10.26 리스크관리위원회 제정 승인(검증 추가) |",
            why="1-1 표 — 지침 개정·세칙 제정")
    # 1-4 다른 기간 정기보고서
    n9k = sum(1 for k in DOCS if k.startswith("R9_") and DOCS[k]["co"] == "한국투자금융지주")
    sec = ["### 1-4 같은 회사 다른 기간 정기보고서에서 찾은 규정 개정 기록(검증 2026-10-07 추가)", "",
           f"검증 때 반박 검색을 `dart_out/text/risk9/`(한국투자 정기보고서 {n9k}건)까지 넓혀 찾은 글. FY2025 지배구조 연차보고서·사업보고서 밖이라 참고로만 둠. "
           "위원회 활동 표는 칸·머리가 줄로 풀려 추출됨([표 깨짐]).", ""]
    k28 = "R9_20260814002697"
    seg1 = cut(k28, 484, 484, "■ 리스크관리위원회", "■ 리스크관리위원회")
    seg2 = cut(k28, 484, 484, "회차 개최일자 의안내용 가결여부", "6 2026.05.08 그룹리스크관리규정 일부 개정(안) 승인의 건")
    code = seg1 + ["[표 깨짐: 위원회 이름(■ 리스크관리위원회·■ 보상위원회·■ 임원후보추천위원회)이 한데 모여 추출되고 표들이 그 뒤에 이어짐 — 아래 표를 리스크관리위원회 표로 본 것은 의안 내용(그룹 위험한도·통합위기상황분석)에 따른 판단]"] + seg2
    sec += qblock(co, "K-28", "반기보고서(2026.06) — 이사회내 위원회 활동내역: 리스크관리위원회 2026년 제1~6차(2026.05.08 그룹리스크관리규정 일부 개정)",
                  k28, code, "조문 목차(지시서 9-4 1.)",
                  ["note: (검증 추가) 「6 2026.05.08 그룹리스크관리규정 일부 개정(안) 승인의 건 가결」 — FY2025 연차보고서가 적은 2025.08.21 개정([K-4]·[K-7]) 뒤에 "
                   "다시 개정됨(판이 바뀜). 개정 내용은 추출 범위에 없음(찾은 방법: 검증 기록 「규정전문」 줄)."])
    k29 = "R9_20240321001204"
    seg1 = cut(k29, 474, 474, "■ 리스크관리위원회", "■ 리스크관리위원회")
    seg2 = cut(k29, 474, 474, "10 2023.10.26", "그룹위기상황대응지침 개정 승인의 건")
    code = seg1 + ["[표 깨짐: 위원회 이름 뒤에 다른 위원회 표가 먼저 이어져 추출됨 — 아래 줄을 리스크관리위원회 표로 본 것은 의안 내용(그룹 위험한도·통합위기상황분석)에 따른 판단]",
                   "[줄임: 리스크관리위원회 표 1~9회차 줄]"] + seg2
    sec += qblock(co, "K-29", "사업보고서(2023.12) — 이사회내 위원회 활동내역: 리스크관리위원회 제10차(2023.10.26) 그룹위기상황대응지침 개정·그룹외화유동성리스크관리업무시행세칙 제정",
                  k29, code, "53조(위기대응조직), 55조(조기경보체계), 25조(유동성위험)(판단), 조문 목차(지시서 9-4 1.)",
                  ["note: (검증 추가) 「그룹위기상황대응지침 개정 승인의 건」·「그룹외화유동성리스크관리업무시행세칙 제정 승인의 건」(2023.10.26) — "
                   "53조 그룹비상경영위원회 전환의 근거 지침([K-13] 제8조)이 개정되어 온 기록. 지침 본문(위기 단계·지표)은 추출 범위에 없음(찾은 방법: 검증 기록 「53」「55」 줄)."])
    k30 = "R9_20220816001954"
    seg1 = cut(k30, 271, 271, "나) 리스크관리위원회", "나) 리스크관리위원회")
    seg2 = cut(k30, 271, 271, "제2차 2022.04.28", "그룹 위기상황 대응지침 개정에 대한 승인의 건")
    code = seg1 + ["[표 깨짐: 위원회 머리(가) 경영위원회·나) 리스크관리위원회·다) 보상위원회)가 한데 모여 추출되고 표들이 그 뒤에 이어짐 — 아래 줄을 리스크관리위원회 표로 본 것은 판단]",
                   "[줄임: 표 머리·제1차 줄]"] + seg2
    sec += qblock(co, "K-30", "반기보고서(2022.06) — 이사회내 위원회 활동내역: 리스크관리위원회 제2차(2022.04.28) 그룹 위기상황 대응지침 개정",
                  k30, code, "53조(위기대응조직), 55조(조기경보체계), 조문 목차(지시서 9-4 1.)",
                  ["note: (검증 추가) 「그룹 위기상황 대응지침 개정에 대한 승인의 건 가결」(2022.04.28) — 지침 이름 띄어쓰기는 원문대로. 본문은 추출 범위에 없음(찾은 방법: 검증 기록 「53」「55」 줄)."])
    s = insert_before(co, s, "## 2. 원문 인용 — 규정 목록·전문", sec, "1-4 절(다른 기간 정기보고서의 규정 개정 기록 [K-28]~[K-30]) 추가")
    # 21·22·24
    s = rep(co, s, "(조기경보 문장 [K-25] 만 55조에 옮김).",
            "(조기경보 문장 [K-25] 만 55조에 옮김).\n"
            "note: (검증 추가) [K-15] 의 「연결실체는 원칙적으로 그룹 내 모든 자회사 등을 대상으로 리스크를 측정합니다」·「위의 리스크 측정 결과를 통합 내부자본에 반영」 — "
            "그룹 전체 대상 측정과 통합 내부자본 반영(모범규준 18조 ③·19조 ①·44조 쪽)이며, 21조 ③·22조 ③·24조 ③의 「연결기준의 … 를 대상으로 통합 … 위험을 측정」 "
            "또는 ④항 「단순 합산」을 적은 글은 더 넓힌 검색어로도 추출 범위에 없음(검증 기록 「21·22·24」, 판단).", why="21·22·24 note — 반박 시도 결과")
    # 53·55
    s = rep(co, s, "「위기상황」「비상경영」의 단계·판단 기준을 정한 「그룹위기상황대응지침」 본문은 추출 범위에 없음.",
            "「위기상황」「비상경영」의 단계·판단 기준을 정한 「그룹위기상황대응지침」 본문은 추출 범위에 없음(검증 추가: 이 지침은 2022.04.28·2023.10.26 리스크관리위원회에서 "
            "개정 승인됨 — [K-30]·[K-29]; 본문은 risk9 정기보고서까지 넓혀도 찾지 못함, 검증 기록 「53」 줄).", why="53조 판정 줄 — 지침 개정 기록")
    # 5장
    add5 = ["| 받은 것(검증 추가) | 그룹리스크관리규정 2026.05.08 일부 개정(안) 승인(리스크관리위원회) — FY2025 연차보고서 뒤의 개정 | 반기보고서(2026.06) 20260814002697 p.484(DART 쪽 481) [K-28] | 조문 목차 |",
            "| 받은 것(검증 추가) | 그룹위기상황대응지침 개정 승인(2022.04.28·2023.10.26), 그룹외화유동성리스크관리업무시행세칙 제정 승인(2023.10.26) | 반기보고서(2022.06) 20220816001954 p.271 [K-30], 사업보고서(2023.12) 20240321001204 p.474 [K-29] | 53·55, 25(판단) |",
            "| 원문과 다른 것(검증 추가) | 그룹리스크관리규정은 FY2025 연차보고서의 2025.08.21 개정 뒤 2026.05.08 에 다시 개정됨(판이 바뀜) — 9-4 대조는 2025.08.21 이후 판 기준이 아님에 주의 | [K-4]·[K-7] vs [K-28] | 조문 목차 |"]
    s = insert_before(co, s, "\n## 6. 검색 기록", add5, "5장 표에 검증 추가 행")
    return s


def section7(co):
    jo = load_jo()

    def jt(*nos):
        return "·".join(f"{n}조({jo[n][0]})" for n in nos)
    if co == "M":
        rows = [
            ("9-4 1.", "조문 목차(1~59조 대응)", "[M-15] 그룹리스크관리위원회규정 전문(대응 규정, 조문 목차 CSV), [M-4]~[M-8] 인용 조문",
             "일부 — 그룹리스크관리규정 전문·조 제목은 추출 범위에 없음(찾은 범위: 1-1 아래 note·6장 「목차(규정명)」·검증 기록 「규정전문」)"),
            ("9-4 1. 메리츠", jt("9", "57"), "[M-4]~[M-8], 1-2 표·1-2-1 소표, 모범규준 [MB-1]~[MB-4]",
             "받은 글 — 인용 위치 재확인(제9조 7항 9회 p.89~93, 제57조·제58조 2회 p.89·91), 같은 번호 조 제목 소표"),
            ("9-4 1. iM", jt("28", "30"), "-", "해당 없음 — iM 파일(9-4_iM금융지주.md) 범위"),
            ("9-4 2. 21·22·24", jt("21", "22", "24"), "[M-16]~[M-22]",
             "받은 글(종속회사별 측정, 지주 가이드라인·한도·정기 점검). 연결기준 통합 측정 서술은 추출 범위에 없음(찾은 방법: 6장 「21」「22」「24」「21·22·24(연결·통합)」·검증 기록 「21·22·24」)"),
            ("9-4 2. 27", jt("27"), "[M-10], [M-16], [M-24](가까운 글, 검증 추가)",
             "일부(전략 — 협의회 설치 목적·경영협의회). 평판위험·측정 수단은 추출 범위에 없음(찾은 방법: 6장 「27」·검증 기록 「27」)"),
            ("9-4 2. 34", jt("34"), "[M-9]·[M-11]·[M-3]",
             "일부(해외투자 국가별·국가신용등급별 한도). 해외진출·해외사업 총괄·사전 검토·정기 점검·보고는 추출 범위에 없음(찾은 방법: 6장 「34」·검증 기록 「34」)"),
            ("9-4 2. 3", jt("3"), "-(가까운 글 [M-16] 41-1-4 ②)",
             "추출 범위에 없음(찾은 방법: 6장 「3」·검증 기록 「3」)"),
            ("9-4 2. 17", jt("17"), "-(가까운 글 [M-12]·[M-16]·[M-15]·[M-24])",
             "추출 범위에 없음 — 문서 형식(공식문서 등)(찾은 방법: 6장 「17」·검증 기록 「17」)"),
            ("9-4 2. 55", jt("55"), "-(가까운 글 [M-9]·[M-4]·[M-6], 자회사 [M-25])",
             "추출 범위에 없음 — 지표 목록·발령 단계(찾은 방법: 6장 「55」·검증 기록 「55」)"),
            ("9-4 2. 53", jt("53"), "-(가까운 글 [M-13]·[M-23]·[M-26], 자회사 [M-25])",
             "추출 범위에 없음 — 구성·전환 요건(찾은 방법: 6장 「53」·검증 기록 「53」)"),
            ("9-4 3.", jt("4", "5"), "[M-3]·[M-14]", "받은 글 — 내규(그룹리스크관리규정)에 둠: ’13.3 철학·원칙 제정으로 규정 개정, 철학 문구·원칙 ①~⑥"),
        ]
    else:
        rows = [
            ("9-4 1.", "조문 목차(1~59조 대응)", "[K-12]·[K-14]·[K-13] 첨부 규정 3건 전문(대응 규정), [K-4]·[K-7]·[K-28] 개정 기록",
             "일부 — 그룹리스크관리규정 전문·조문 목차는 추출 범위에 없음(찾은 범위: 1-1 아래 note·6장 「목차(규정명)」·검증 기록 「규정전문」); 「제2장과 제3장」 인용만"),
            ("9-4 1. 메리츠", jt("9", "57"), "-", "해당 없음 — 메리츠 파일 범위(한국투자 그룹리스크관리규정의 조 단위 인용은 추출 범위에 없음 — 검증 기록 「규정전문」)"),
            ("9-4 1. iM", jt("28", "30"), "-", "해당 없음 — iM 파일(9-4_iM금융지주.md) 범위"),
            ("9-4 2. 21·22·24", jt("21", "22", "24"), "[K-24]·[K-23]·[K-15]~[K-22]",
             "받은 글(신용·시장), 일부(금리). 연결기준 통합 측정 서술은 추출 범위에 없음(찾은 방법: 6장 「21」「22」「24」「21·22·24(연결·통합)」·검증 기록 「21·22·24」)"),
            ("9-4 2. 27", jt("27"), "-(가까운 글 [K-15]·[K-21]·[K-13])",
             "추출 범위에 없음 — 전략·평판 이름으로 적은 관리 체제·측정 수단(찾은 방법: 6장 「27」·검증 기록 「27」)"),
            ("9-4 2. 34", jt("34"), "-(자회사 내규 [K-26], 감사 [K-8])",
             "추출 범위에 없음 — 지주 차원(찾은 방법: 6장 「34」·검증 기록 「34」)"),
            ("9-4 2. 3", jt("3"), "[K-15]·[K-21]", "받은 글(측정 대상 제외 — 문구는 18조 ③항 쪽, 판단). 「경미」 기준·명단은 추출 범위에 없음(찾은 방법: 6장 「3」·검증 기록 「3」)"),
            ("9-4 2. 17", jt("17"), "-(가까운 글 [K-24]·[K-13]·[K-14])",
             "추출 범위에 없음 — 문서 형식(찾은 방법: 6장 「17」·검증 기록 「17」)"),
            ("9-4 2. 55", jt("55"), "[K-24]·[K-10]·[K-11]·[K-25]",
             "일부 — 지표 이름만. 지표 목록·발령 단계는 추출 범위에 없음(찾은 방법: 6장 「55」·검증 기록 「55」)"),
            ("9-4 2. 53", jt("53"), "[K-13]·[K-14]·[K-9], 지침 개정 기록 [K-29]·[K-30]", "받은 글 — 그룹경영협의회규정 제8조(그룹비상경영위원회 전환·구성)"),
            ("9-4 3.", jt("4", "5"), "[K-3]·[K-6]·[K-5]·[K-15]",
             "일부 — 리스크관리 철학을 담은 「리스크관리정책」(정책 문서)을 이사회가 수립. 철학 문구·내규 반영은 추출 범위에 없음(찾은 방법: 6장 「4·5」·검증 기록 「4·5」)"),
        ]
    txt = dict(REQ_ITEMS)
    o = [SEC7, "", "지시서(REQUEST13.md) 9-4 항목마다 이 파일의 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」. 지시서 원문 칸은 지시서 글 그대로.", "",
         "| 지시서 항목 | 지시서 원문(그대로) | 모범규준 조(조 제목) | 이 파일의 받은 글 | 상태 |", "|---|---|---|---|---|"]
    for item, jt_, got, state in rows:
        o.append(f"| {item} | {txt[item]} | {jt_} | {got} | {state} |")
    o.append("")
    return o


REFUTE_RESULT = {  # 조 → (회사별 결과 설명). 맞은 줄 수는 refute_hits.json 에서 셈.
    "3": {"M": "실패 — 맞은 줄은 관리대상 리스크 유형·자회사 편입 부의 제외·보험위험 측정대상·유동성관리 대상 자산 등 다른 뜻. 판정 그대로(추출 범위에 없음).",
          "K": "실패(「경미」 기준·명단) — 맞은 줄은 이미 인용한 [K-15]·[K-21] 과 연결대상회사 개요 등. 「경미」 수치 기준·명단은 추출 범위에 없음."},
    "4·5": {"M": "해당 없음(이미 찾은 글) — 2021~2026 정기보고서의 「(1) 그룹의 리스크철학」은 [M-14] 와 같은 글(예: 2021 사업보고서 20220316001217 — 철학 문구·원칙 ⑤·⑥ 공백 무시 대조).",
            "K": "실패 — 「철학」은 이사회 리스크관리 정책 수립([K-3])과 보수체계 철학(p.117, 다른 뜻)뿐, 리스크 철학 문구는 추출 범위에 없음. 판정 그대로(일부)."},
    "17": {"M": "실패(문서 형식) — 「공문·공식문서·서면·통보·시달·하달·지시·지도·권고·가이드라인·요청·요구·전달」과 자회사 낱말이 40자 안에 함께 있는 줄은 감사위원회 "
                "자회사 영업보고 요구(정관)·자료제출 요구 등. 가까운 글로 경영협의회 [M-24] 를 더함. 「공식문서」(모범규준 17조 ②6호·③항 낱말)는 0줄.",
           "K": "실패(문서 형식) — 맞은 줄은 협의회 「서면으로 운영」(회의 방식), 감사·준법 자료제출 요구, RM실 가이드라인([K-24]) 등. 「공식문서」 0줄."},
    "21·22·24": {"M": "실패 — 「통합리스크 한도」「요구자본 할당」 등은 이미 인용한 [M-16] 안의 글, 「연결기준 … 통합 측정」「단순 합산」 서술은 0줄.",
                 "K": "실패(연결기준 통합 측정) — [K-15] 「그룹 내 모든 자회사 등을 대상으로 리스크를 측정」「통합 내부자본에 반영」을 가까운 글로 note 에 더함(18조③·19조 쪽, 판단)."},
    "27": {"M": "실패(평판·측정 수단) — 「평판」은 자회사 메리츠증권 업계 설명(사업보고서 p.99)뿐, 「명성」은 사외이사 추천 사유, 「정성평가」는 보수 성과평가, 「이미지 실추」는 윤리강령. 전략 쪽 가까운 글로 경영협의회 [M-24] 를 더함.",
           "K": "실패 — 「평판」은 사외이사 Reference Check, 「비재무」는 운영위험 정의·성과지표, 「전략적」은 부문 보고 회계 문장."},
    "34": {"M": "실패 — 「해외·글로벌·국외·외화」는 해외투자 국가별 한도([M-9]·[M-11])·외화유동성 시행세칙([M-3])·자회사 점포·환산손익 등.",
           "K": "실패 — 맞은 줄은 자회사 내규 제41조([K-26])·감사 점검([K-8])·글로벌사업실 조직명·외국환 제재·해외사업환산손익. 2021 사업보고서(20220317000665) 준법지원실 활동의 「자금세탁행위 방지관련 해외 자회사 관리 강화(금융지주 보고체계 도입」은 준법(자금세탁방지) 쪽이라 34조 근거로 쓰지 않음(판단)."},
    "53": {"M": "실패(구성·전환 요건) — 「위기·비상」 줄은 최고경영자 비상승계, 이사회 「그룹 비상 상황 대응 현황 보고」([M-13]·[M-23]), 사업보고서 지주 서술 「선제적인 위기 대응체제를 구축」(p.82 — 가까운 글 [M-26] 으로 더함), 자회사 메리츠화재 「선제적 위기대응체제 구축」(p.86)·메리츠증권 「비상대책실무」 협의체(p.89)·「위기상황 단계별 대비책」(가까운 글 [M-25] 로 더함).",
           "K": "성공(참고 글을 더함) — 「그룹위기상황대응지침」 개정 승인 기록 2건(2022.04.28·2023.10.26, [K-30]·[K-29])을 더함. 판정(찾은 글) 그대로, 지침 본문은 추출 범위에 없음."},
    "55": {"M": "실패 — 맞은 줄은 일임계약·자산손상 「징후」·제재 「경고」·KRI(메리츠증권 운영위험)·메리츠증권 「위기상황 단계별 대비책」([M-25] 로 더함). 지주 조기경보 지표·발령 단계 0줄.",
           "K": "실패(목록·발령 단계) — 맞은 줄은 이미 인용한 「유동성 위험수준 판단지표」「Red Light」「위기수준판단지표」「조기경보체계 운영」(자회사)와 제재 「경고」 등."},
    "규정전문": {"M": "실패 — 「제1조(목적)」 머리는 첨부 규정 8건(정관·이사회·감사위원회·보수위원회·그룹리스크관리위원회·내부통제위원회·최고경영자경영승계·지배구조내부규범)뿐. "
                     "risk9 정기보고서에는 규정 체계(「그룹리스크관리규정, 그룹리스크관리위원회규정, 그룹리스크협의회운영세칙으로 구성」)와 2021 사업보고서의 「그룹리스크관리규정 개정의 건」 의결 기록만.",
             "K": "성공(참고 글을 더함) — 「그룹리스크관리규정 일부 개정(안) 승인」 2026.05.08(반기보고서 2026.06, [K-28])을 더함. 규정 전문·조 단위 인용은 0줄(「제2장과 제3장」만)."},
}


def verification_record(co, pre_stats, post_quotes):
    rj = json.load(open(REFUTE_JSON, encoding="utf-8")) if os.path.exists(REFUTE_JSON) else None
    o = [VREC, "", f"대조 스크립트 `scripts/dart/verify13_g_meritz_kis.py`(인자 없이 = 대조, `refute` = 반박 검색, `fix` = 이 보정), 결과 `dart_out/risk13/verify13_g_meritz_kis.txt`. "
         "검증 전 사본은 `dart_out/raw/web13/verify13_g_meritz_kis/pre/`(커밋 8c118c8 의 파일 그대로), 반박 검색 원자료는 같은 폴더 `refute_hits.json`(git 무시 폴더).", ""]
    o += ["### 대조한 인용", ""]
    o.append(f"- 검증 전 원문 인용 {pre_stats['n']}건(코드 블록)을 「- 인용:」 줄이 가리킨 텍스트(`dart_out/text/risk8/`)의 그 쪽과 공백만 무시하고 대조 — 일치 {pre_stats['ok']}건, 틀린 인용 0건. "
             "「[표 깨짐: …]」「[추출 깨짐: …]」「[줄임: …]」 줄은 이 작업이 끼운 표시라 빼고 그 자리에서 조각을 나눠 순서대로 찾음. 모범규준 인용은 hwp2md 변환본(dart_out/raw/web13/mobeom/fss/*.hwp.md)과 대조.")
    o.append("- 쪽 표기(PDF 쪽·인쇄 쪽·DART 쪽), 문서명·접수번호·URL·방식, 원본 수집일, 옮김 날짜를 메타(dart_out/risk8/텍스트목록.csv, handoff/연차보고서_파일목록.csv, dart_out/doc/<접수번호>/_파일목록.json)와 대조 — 다른 곳 없음.")
    o.append("- 「정정판·재공시판 대조」 줄을 정정판·재공시판 텍스트에서 다시 계산 — 모두 같음. 머리 문서 표의 sha256·쪽수·원본 수집 시각 — 같음.")
    o.append(f"- 검증 뒤 원문 인용은 모두 {post_quotes}건(검증 추가 인용 포함) — 같은 방식으로 다시 대조해 모두 일치(대조 결과 파일).")
    o.append(f"- 조문 목차 CSV `{os.path.basename(TOC[co])}` 의 행마다 조 번호·제목(또는 인용 글)이 그 쪽 텍스트에 있는지, 문서·접수번호/URL·쪽 표기가 맞는지 대조 — 다른 곳 없음.")
    o.append("")
    o += ["### 고친 곳(전 → 후)", ""]
    o.append("- 원문 인용(코드 블록) 글은 고친 곳 없음(틀린 인용 0건).")
    def short(x, n=420):
        x = x.strip().replace("\n", " ⏎ ")
        return x if len(x) <= n else x[:n] + "…(줄임)"
    for why, old, new in FIXLOG[co]:
        if old or new:
            o.append(f"- {why}: 「{short(old)}」 → 「{short(new)}」")
        else:
            o.append(f"- {why}")
    if co == "M":
        o.append("- 조문 목차 CSV: 그룹리스크관리규정 인용 5행(제6조 제5항·제9조 제6항·제9조 제7항·제57조·제58조)의 비고 끝에 「모범규준 같은 번호 조: N조(제목) …(판단, 검증 추가)」를 덧붙임.")
    else:
        o.append("- 조문 목차 CSV: 「그룹리스크관리규정」·「그룹위기상황대응지침」 행 비고에 개정 기록(검증 추가)을 덧붙이고, 「그룹외화유동성리스크관리업무시행세칙」 행을 더함.")
    o.append("")
    o += ["### 채운 항목", ""]
    o.append(f"- 「{SEC7[3:]}」 절 — 지시서 9-4 항목 {len(REQ_ITEMS)}개마다 받은 글 또는 「추출 범위에 없음 + 찾은 방법」.")
    if co == "M":
        o.append("- 1-2-1 소표 — 메리츠가 인용한 그룹리스크관리규정 조 번호(제6조 5항·제9조 6항·제9조 7항·제57조·제58조)와 모범규준 같은 번호 조 제목(2016.8.1판·2012.3.13 제정판)·항 구성을 나란히, 인용 횟수·자리 재확인. 모범규준 원문 [MB-1]~[MB-4].")
        o.append("- 새 인용 [M-24](경영협의회 — 17·27조 가까운 글), [M-25](자회사 메리츠증권 위기상황 단계별 대비책 — 55·53·57조 가까운 글), [M-26](지주 서술 「선제적인 위기 대응체제」 — 53조 가까운 글).")
    else:
        o.append("- 1-4 절 — 다른 기간 정기보고서(risk9)의 규정 개정 기록 [K-28](그룹리스크관리규정 2026.05.08 개정), [K-29](2023.10.26 그룹위기상황대응지침 개정·그룹외화유동성리스크관리업무시행세칙 제정), [K-30](2022.04.28 지침 개정).")
    o.append("- 인용마다 「이 글이 닿는 모범규준 조」를 「N조(조 제목)」으로(지시서 조 번호는 그대로, 새로 붙인 조는 「(판단)」), 3장 조별 머리에 조 제목.")
    o.append("")
    o += ["### 「추출 범위에 없음」 반박 시도", "",
          "같은 출처(dart_out/text/risk8 의 이 회사 연차보고서·사업보고서(원본·정정판)·경영공시 전체)와 `dart_out/text/risk9/`의 같은 회사 정기보고서 전체(다른 기간 판)를 "
          "더 넓힌 정규식(낱말 변형·띄어쓰기 `\\s*`·영문·동의어)으로 줄 단위 + 앞뒤 줄 이어 붙인 창에서 다시 찾음(ctx 가 있는 조는 같은 창에 ctx 낱말이 있을 때만). "
          "risk9 의 FY2025 사업보고서 텍스트는 risk8 과 바이트가 같음(sha256 같음).", ""]
    for jo, spec in REFUTE.items():
        hits8 = hits9 = n9 = 0
        if rj:
            for k, v in rj["조"][jo]["문서"].items():
                if DOCS.get(k, {}).get("co") != CO[co] and v["name"].split(" ")[0] != CO[co]:
                    continue
                if k.startswith("R9_"):
                    hits9 += v["n"]
                    n9 += 1
                else:
                    hits8 += v["n"]
        res = REFUTE_RESULT[jo][co]
        o.append(f"- 「{jo}」 ({spec['label']}) — {res} 검색어 `{spec['pat']}`"
                 + (f", ctx `{spec['ctx']}`" if spec.get("ctx") else "") + (f", 뺀 말 `{spec['excl']}`" if spec.get("excl") else "")
                 + (", 17조는 자회사 낱말과 40자 안 조합" if jo == "17" else "")
                 + f" — 맞은 줄 risk8 {hits8}줄, risk9 {hits9}줄({n9}개 보고서).")
    o.append("")
    o += ["### 남은 문제", ""]
    if co == "M":
        o += ["- 「그룹리스크관리규정」 전문·조 제목은 공시 자료(연차보고서 첨부·사업보고서·경영공시·정기보고서)에 없음 — 메리츠 규정 제57·58조가 모범규준 57·58조와 같은 제목인지는 확인 못 함(회사 자료 요청 등 다른 출처 필요).",
              "- 첨부6 위원회규정은 PDF 글자 순서가 깨진 추출(조 번호·숫자 밀림) — 원문 PDF 화면 대조는 하지 않음.",
              "- 회의록 인용 「그룹리스크위원회규정 제10조 2항」「제5조 4항」이 첨부6(2016.8.1 개정 표기)과 맞지 않음 — 최신판 위원회규정은 추출 범위에 없음.",
              "- 경영공시 텍스트는 FY2025 말 판이 아닌 2026년 2분기 판.",
              "- [M-24]~[M-26] 과 1-2-1 의 조 대응, 2012 제정판 낱말 일치 판단은 눈으로 맞댄 판단."]
    else:
        o += ["- 「그룹리스크관리규정」 전문·조문 목차, 「그룹위기상황대응지침」·「그룹리스크관리업무지침」·「리스크관리정책」 본문은 공시 자료에 없음(회사 자료 요청 등 다른 출처 필요).",
              "- 그룹리스크관리규정이 2026.05.08 다시 개정됨([K-28]) — FY2025 자료 기준 대조와 현행판이 다를 수 있음.",
              "- [K-28]~[K-30] 은 위원회 표의 머리·칸이 풀려 추출되어 어느 위원회 표인지는 의안 내용으로 판단함.",
              "- 경영공시 텍스트는 FY2025 말 판이 아닌 2026년 2분기 판."]
    o.append("")
    return o


def fix_csv(co):
    path = TOC[co]
    rows = list(csv.DictReader(open(os.path.join(PRE, os.path.basename(path)), encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    jo = load_jo()
    if co == "M":
        add = {"제6조 제5항": "6", "제9조 제6항": "9", "제9조 제7항": "9", "제57조": "57", "제58조": "58"}
        hang = {"제6조 제5항": "①~③항뿐(5항 없음)", "제9조 제6항": "⑥항 결의사항", "제9조 제7항": "⑦항 보고사항",
                "제57조": "①~③항", "제58조": "①·②항"}
        for r in rows:
            if r["규정명"] == "그룹리스크관리규정" and r["조번호"] in add:
                no = add[r["조번호"]]
                r["비고"] += f" / 모범규준 같은 번호 조: {no}조({jo[no][0]}) {hang[r['조번호']]}(판단, 검증 추가 — md 1-2-1)"
    else:
        for r in rows:
            if r["규정명"] == "그룹리스크관리규정" and r["조번호"] == "-":
                r["비고"] += "; 2026.05.08 리스크관리위원회 일부 개정(안) 승인 — 한국투자금융지주 「반기보고서 (2026.06)」 20260814002697 p.484(DART 쪽 481)([K-28], 검증 추가)"
            if r["규정명"] == "그룹위기상황대응지침":
                r["비고"] += "; 2022.04.28·2023.10.26 리스크관리위원회 개정 승인([K-30]·[K-29], 검증 추가)"
        k = "R9_20240321001204"
        new = dict(회사=CO[co], 규정명="그룹외화유동성리스크관리업무시행세칙", 조번호="-", 조제목="추출 범위에 없음", 문서=DOCS[k]["name"],
                   접수번호또는URL=DOCS[k]["rcp"], 쪽=T(k).plabel(474), 전문여부="N(이름만)",
                   비고="2023.10.26 리스크관리위원회 제정 승인([K-29], 검증 추가 — 다른 기간 정기보고서)")
        i = next(j for j, r in enumerate(rows) if r["규정명"] == "그룹위기상황대응지침")
        rows.insert(i + 1, new)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def fix():
    load_meta()
    if not os.path.exists(REFUTE_JSON):
        refute()
    for co in ("M", "K"):
        FIXLOG[co].clear()
    pre_stats = {}
    for co in ("M", "K"):
        R0 = Report()
        _, qs = check_quotes(R0, co, os.path.join(PRE, os.path.basename(MD[co])))
        pre_stats[co] = dict(n=R0.stats[co + "_quotes"], ok=R0.stats[co + "_ok"], problems=len(R0.problems))
    for co, fn in (("M", fix_meritz), ("K", fix_kis)):
        s = fn()
        lines = notfound_pointers(co, s.split("\n"))
        s = "\n".join(lines).rstrip("\n") + "\n\n" + "\n".join(section7(co)) + "\n"
        open(MD[co], "w", encoding="utf-8").write(s)
        R1 = Report()
        check_quotes(R1, co, MD[co])
        s = s.rstrip("\n") + "\n\n" + "\n".join(verification_record(co, pre_stats[co], R1.stats[co + "_quotes"])).rstrip("\n") + "\n"
        open(MD[co], "w", encoding="utf-8").write(s)
        fix_csv(co)
        print(f"fix {CO[co]}: 검증 전 인용 {pre_stats[co]['n']}건(일치 {pre_stats[co]['ok']}), 검증 뒤 {R1.stats[co + '_quotes']}건, 보정 기록 {len(FIXLOG[co])}줄")


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "refute":
        refute()
        return 0
    if mode == "fix":
        fix()
    R = verify()
    return 0 if not R.problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
