# -*- coding: utf-8 -*-
"""15차 g2 — 지배구조 및 보수체계 연차보고서에서 작업 A(임원 겸직)·B(겸직·파견 등 언급) 조각 행 만들기.

원문:
  FY2019~2023 → gov15_g2_collect.py 가 받은 PDF 의 쪽 텍스트 md(dart_out/text/ops15/연차보고서__<회사>__<공시연도>__<유형>.md)
  FY2024·2025 → 6차 섹션 글(dart_out/ops15/kit56/연차보고서_섹션.csv)
source_text 는 원문에서 잘라 낸 글자 그대로(줄 끝 공백만 지움). 잘라 낼 자리는 아래 SPEC 의 닻(anchor) 글자로 찾는다
(공백·줄바꿈 차이는 무시하고 찾되, 잘라 낸 글은 원문 그대로).
  S(...)  닻이 든 문장(앞뒤 「다.」·빈 줄·글머리표 경계)
  R(...)  끝 닻(end)이 처음 나오는 자리와, 그 앞에서 마지막으로 나오는 시작 닻(start) 사이(양끝 포함)
`python3 scripts/dart/gov15_g2_extract.py`
"""
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

csv.field_size_limit(10 ** 9)
OPS = os.path.join("dart_out", "ops15")
TXT = os.path.join("dart_out", "text", "ops15")
LIST15 = os.path.join(OPS, "연차보고서15_목록_g2.csv")
SEC6 = os.path.join(OPS, "kit56", "연차보고서_섹션.csv")
FILES6 = os.path.join("handoff", "연차보고서_파일목록.csv")
GOVLIST = os.path.join("scripts", "dart", "data", "governance_list.csv")
OUT_A = os.path.join(OPS, "조각", "A_gov_g2.csv")
OUT_B = os.path.join(OPS, "조각", "B_gov_g2.csv")
RAW_A = os.path.join(OPS, "원문", "A")
RAW_B = os.path.join(OPS, "원문", "B")
DOCKIND = "지배구조 연차보고서"
KST = timezone(timedelta(hours=9))
COLS_A = ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
COLS_B = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
NONE = "문서에 없음"
N6 = "6차 섹션 글(PDF 원본은 이번 컨테이너에 없음)"
BUL = re.compile(r'\n(?=\s*(?:[○●■□◦·•※\-–▶▣]|[①-⑳]|[㉮-㉿]|주\s?\d\)|\(\d+\)|\d+\)|[가-하]\.|\d+\.\s))')


# ───────────────────────────── 원문 읽기 ─────────────────────────────
def kst(s):
    """'2026-09-22T02:44:33+0000' → KST ISO."""
    if not s:
        return ""
    if s.endswith("+0000"):
        d = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S+0000").replace(tzinfo=timezone.utc)
        return d.astimezone(KST).isoformat(timespec="seconds")
    return s


class Docs:
    def __init__(self):
        self.meta = {}      # doc key → dict(url, name, collected, fy, co)
        self.pages = {}     # M key → {page: text}
        self.sec = {}       # S key → {(start, chunk): row}
        for r in csv.DictReader(open(LIST15, encoding="utf-8-sig")):
            k = "M:%s:%s:%s" % (r["회사"], r["공시연도"], r["공시유형"])
            self.meta[k] = dict(co=r["회사"], fy=int(r["공시연도"]) - 1, url=r["파일_url"],
                                name="%s (%s, %s 게시)" % (r["제목"], r["공시유형"], r["공시일"]),
                                collected=r["fetched_at"], pdfpages=r["쪽수"], title=r["제목"], date=r["공시일"],
                                kind=r["공시유형"])
        f6 = {}
        for r in csv.DictReader(open(FILES6, encoding="utf-8-sig")):
            if r["공시연도"]:
                f6[r["파일명"]] = r
        gl = {}
        for r in csv.DictReader(open(GOVLIST, encoding="utf-8-sig")):
            gl[r["저장 파일명"]] = r
        for r in csv.DictReader(open(SEC6, encoding="utf-8-sig")):
            if r["지주명"] not in ("메리츠금융지주", "iM금융지주", "BNK금융지주", "JB금융지주", "한국투자금융지주"):
                continue
            k = "S:%s:%s:%s" % (r["지주명"], r["공시연도"], r["공시유형"])
            if "보수체계연차보고서" in r["파일명"]:
                k += ":보수체계"
            self.sec.setdefault(k, {}).setdefault((r["시작페이지"], r["chunk_seq"]), []).append(r)
            if k not in self.meta:
                fr = f6.get(r["파일명"], {})
                url = fr.get("url", "")
                g = gl.get(r["파일명"], {})
                if "fildDownload" in url and "real_filename" in g.get("URL", ""):
                    url = g["URL"]
                self.meta[k] = dict(co=r["지주명"], fy=int(r["공시연도"]) - 1, url=url,
                                    name="%s (%s, %s 게시; 파일 %s)" % (fr.get("제목", ""), r["공시유형"], g.get("공시일", ""), r["파일명"]),
                                    collected=kst(fr.get("fetched_at", "")), title=fr.get("제목", ""),
                                    date=g.get("공시일", ""), kind=r["공시유형"], file=r["파일명"])

    def page(self, k, p):
        if k not in self.pages:
            m = self.meta[k]
            path = os.path.join(TXT, "연차보고서__%s__%d__%s.md" % (m["co"], m["fy"] + 1, m["kind"]))
            s = open(path, encoding="utf-8").read()
            parts = re.split(r"^(## p\.\d+(?: \(글자 없음\))?)\n", s, flags=re.M)
            self.pages[k] = {int(re.match(r"## p\.(\d+)", parts[i]).group(1)): parts[i + 1] for i in range(1, len(parts), 2)}
        return self.pages[k][int(p)]

    def texts(self, k, p):
        """[(본문, 섹션행 또는 None)] — 6차는 같은 시작페이지·chunk 에 섹션이 여럿일 수 있다."""
        if k.startswith("M:"):
            return [(self.page(k, p), None)]
        st, ch = str(p).split("/")
        return [(r["본문"], r) for r in self.sec[k][(st, ch)]]


def flex(a):
    """닻 글자 → 공백 무시 정규식."""
    a = re.sub(r"[\s\x00-\x1f⏎]+", "", a)
    return r"[\s\x00-\x1f]*".join(re.escape(c) for c in a)


def sent_bounds(t, pos):
    cands = [0]
    i = t.rfind("다.", 0, pos)
    if i >= 0:
        cands.append(i + 2)
    i = t.rfind("\n\n", 0, pos)
    if i >= 0:
        cands.append(i + 2)
    for m in BUL.finditer(t, 0, pos):
        cands.append(m.start() + 1)
    st = max(cands)
    ends = [len(t)]
    i = t.find("다.", pos)
    if i >= 0:
        ends.append(i + 2)
    i = t.find("\n\n", pos)
    if i >= 0:
        ends.append(i)
    m = BUL.search(t, pos)
    if m:
        ends.append(m.start())
    return st, min(ends)


def clean(s):
    s = re.sub(r"[\x00-\x08\x0b-\x1f]", "", s)     # PDF 추출 글에 섞인 제어문자(U+0001 등) 지움
    return "\n".join(l.rstrip() for l in s.strip().split("\n"))


def extract(D, k, p, a=None, start=None, end=None):
    errs = []
    for t, row in D.texts(k, p):
        try:
            return _extract(t, k, p, a, start, end), t, row
        except ValueError as e:
            errs.append(str(e))
    raise ValueError(errs[0])


def _extract(t, k, p, a=None, start=None, end=None):
    if a is not None:
        m = re.search(flex(a), t)
        if not m:
            raise ValueError("닻 없음: %s p.%s %r" % (k, p, a))
        st, en = sent_bounds(t, m.start())
        en = max(en, m.end())
        return clean(t[st:en])
    allst = list(re.finditer(flex(start), t))
    if not allst:
        raise ValueError("시작 닻 없음: %s p.%s %r" % (k, p, start))
    me = re.search(flex(end), t)
    if not me:
        raise ValueError("끝 닻 없음: %s p.%s %r" % (k, p, end))
    ss = [m for m in allst if m.start() <= me.start()]
    if len(allst) > 1 and ss:
        s0 = ss[-1].start()                      # 끝 닻 앞의 마지막 시작 닻
        return clean(t[s0:me.end()])
    s0 = allst[0].start()                        # 시작 닻이 하나뿐 → 그 뒤 첫 끝 닻
    me = re.search(flex(end), t[s0 + 1:])
    if not me:
        raise ValueError("시작 닻 뒤 끝 닻 없음: %s p.%s %r" % (k, p, end))
    return clean(t[s0:s0 + 1 + me.end()])


# ───────────────────────────── 스펙 ─────────────────────────────
A_SPEC = []
B_SPEC = []


def A(d, p, a=None, start=None, end=None, **f):
    A_SPEC.append(dict(d=d, p=p, a=a, start=start, end=end, **f))


def B(d, p, kw, a=None, start=None, end=None, note=""):
    B_SPEC.append(dict(d=d, p=p, kw=kw, a=a, start=start, end=end, note=note))


CAND = "사외이사후보 본인 소명 「3) 현재 겸직 업무」 칸"
EXT = "타회사(계열 밖) 겸직 — 사외이사 개인 겸직"
NOR = "사유·이유·필요성을 적은 글 없음(같은 쪽·같은 후보 양식 안에서 찾음)"

# ── 메리츠금융지주 ──
d = "M:메리츠금융지주:2020:본공시"
A(d, 125, "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", person="", holdco_title="CEO", concurrent_company="메리츠화재", concurrent_title="CEO",
  note="그룹 경영협의회 구성 서술 — 성명 없이 직위만 적힘")
A(d, 128, start="장원재", end="화재 CRO 겸직", person="장원재", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄(성명·직위·선임일·임기만료일·비고). 선임일 칸 「2016.8.1.」「2015.2.2」 두 값 — 어느 직위 것인지 표 글로는 구분 안 됨")
A(d, 128, start="홍기표", end="겸직", person="홍기표", holdco_title="", concurrent_company="메리츠대체투자운용", concurrent_title="리스크관리담당부서장",
  note="(판단) 지주 임원이 아님(자회사 부서장이 지주 그룹리스크협의회 위원) — 비고 「자회사 리스크관리담당부서장 겸직」을 그대로 옮김. 무엇과 겸직인지 표에 없음")
A(d, 190, start="3) 현재 겸직 업무", end="SK텔레콤 사외이사", person="오대식", birth_ym="1954(출생년도만)", holdco_title="사외이사(감사위원) 후보",
  concurrent_company="SK텔레콤", concurrent_title="사외이사", note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 오대식」, 출생년도는 p.188 「· 출생년도 : 1954년」")
A(d, 190, start="3) 현재 겸직 업무", end="세무법인 제일티앤엠 이사", person="오대식", birth_ym="1954(출생년도만)", holdco_title="사외이사(감사위원) 후보",
  concurrent_company="세무법인 제일티앤엠", concurrent_title="이사", note=CAND + "; 같은 칸 두 번째 겸직")
A(d, 194, start="3) 현재 겸직 업무", end="김앤장 법률사무소 고문", person="전광수", holdco_title="사외이사(감사위원) 후보",
  concurrent_company="김앤장 법률사무소", concurrent_title="고문", note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 전광수」")
B(d, 113, "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직(감사팀 총3명) 서술")
B(d, 125, "겸임", "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", note="그룹 경영협의회 구성 서술")

d = "M:메리츠금융지주:2021:본공시"
A(d, 109, "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", person="", holdco_title="CEO", concurrent_company="메리츠화재", concurrent_title="CEO",
  note="그룹 경영협의회 구성 서술 — 성명 없이 직위만 적힘")
A(d, 112, start="장원재", end="위원장, 화재 CRO 겸직", person="장원재", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄(2020.12.31. 기준)")
A(d, 112, start="홍기표", end="자회사 리스크관리담당부서장 겸직", person="홍기표", holdco_title="", concurrent_company="메리츠대체투자운용", concurrent_title="리스크관리담당부서장",
  note="(판단) 지주 임원이 아님(자회사 부서장) — 비고 「겸직」 그대로. 무엇과 겸직인지 표에 없음")
A(d, 204, start="3) 현재 겸직 업무", end="연세대학교 교수", person="한순구", holdco_title="사외이사(감사위원) 후보", concurrent_company="연세대학교", concurrent_title="교수",
  note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 한순구」")
A(d, 204, start="3) 현재 겸직 업무", end="현대삼호중공업 사외이사", person="한순구", holdco_title="사외이사(감사위원) 후보", concurrent_company="현대삼호중공업", concurrent_title="사외이사",
  note=CAND + "; 같은 칸 두 번째 겸직")
A(d, 206, start="3) 현재 겸직 업무", end="서울대학교 교수", person="안동현", holdco_title="사외이사 후보", concurrent_company="서울대학교", concurrent_title="교수",
  note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 안동현」")
A(d, 206, start="3) 현재 겸직 업무", end="삼성증권 사외이사", person="안동현", holdco_title="사외이사 후보", concurrent_company="삼성증권", concurrent_title="사외이사",
  note=CAND + "; 같은 칸 두 번째 겸직")
A(d, 208, start="3) 현재 겸직 업무", end="법무법인 삼우 대표변호사", person="이상훈", holdco_title="사외이사 후보", concurrent_company="법무법인 삼우", concurrent_title="대표변호사",
  note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 이상훈」")
B(d, 101, "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직(감사팀 총2명) 서술")
B(d, 109, "겸임", "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", note="그룹 경영협의회 구성 서술")

d = "M:메리츠금융지주:2022:본공시"
A(d, 90, "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", person="", holdco_title="CEO", concurrent_company="메리츠화재", concurrent_title="CEO",
  note="그룹 경영협의회 구성 서술 — 성명 없이 직위만 적힘")
A(d, 93, start="오종원", end="위원장, 화재 CRO 겸직", person="오종원", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄(2021.12.31. 기준)")
A(d, 93, start="홍기표", end="자회사 리스크관리담당부서장 겸직", person="홍기표", holdco_title="", concurrent_company="메리츠대체투자운용", concurrent_title="리스크관리담당부서장",
  note="(판단) 지주 임원이 아님(자회사 부서장) — 비고 「겸직」 그대로. 무엇과 겸직인지 표에 없음")
B(d, 82, "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직(감사팀 총3명) 서술")
B(d, 90, "겸임", "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", note="그룹 경영협의회 구성 서술")

d = "M:메리츠금융지주:2023:본공시"
A(d, 45, start="주1) 이상훈 사외이사는", end="단합니다.", person="이상훈", holdco_title="사외이사(감사위원)", concurrent_company="법무법인 삼우", concurrent_title="대표변호사",
  concurrent_since="2012", note="감사위원 자격요건 표 주석. 같은 겸직이 " + CAND + " p.203·p.212 에도 「법무법인 삼우 대표변호사」")
A(d, 51, start="주1) 조홍희 사외이사는", end="판단합니다.", person="조홍희", holdco_title="사외이사(감사위원)", concurrent_company="SK케미칼", concurrent_title="사외이사",
  note="감사위원 자격요건 표 주석(같은 주석에 「법무법인 태평양 고문으로 해당 법무법인의 임원 내지 변호사는 아닙니다」). 같은 겸직이 p.218 현재 겸직 업무 칸에도")
A(d, 107, "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", person="", holdco_title="CEO", concurrent_company="메리츠화재", concurrent_title="CEO",
  note="그룹 경영협의회 구성 서술 — 성명 없이 직위만 적힘")
A(d, 110, start="오종원", end="위원장, 화재 CRO 겸직", person="오종원", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄")
A(d, 206, start="3) 현재 겸직 업무", end="서울대학교 경제학 교수", person="안동현", holdco_title="사외이사 후보", concurrent_company="서울대학교", concurrent_title="경제학 교수",
  note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 안동현」. 같은 칸 p.215(감사위원 후보 양식)에도")
A(d, 206, start="3) 현재 겸직 업무", end="삼성증권 사외이사", person="안동현", holdco_title="사외이사 후보", concurrent_company="삼성증권", concurrent_title="사외이사",
  note=CAND + "; 같은 칸 두 번째 겸직. p.215 에도")
A(d, 209, start="3) 현재 겸직 업무", end="대신증권 사외이사", person="조홍희", holdco_title="사외이사 후보", concurrent_company="대신증권", concurrent_title="사외이사",
  note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 조홍희」. p.218(감사위원 후보 양식) 같은 칸에는 「대신증권 사외이사 (* 대신증권 겸직해소 예정)」")
A(d, 209, start="3) 현재 겸직 업무", end="법무법인 유한 태평양 고문", person="조홍희", holdco_title="사외이사 후보", concurrent_company="법무법인 유한 태평양", concurrent_title="고문",
  note=CAND + "; 같은 칸 두 번째 겸직. p.218 에도")
B(d, 98, "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조기구(감사팀 총3명) 서술")
B(d, 107, "겸임", "메리츠금융지주 CEO(메리츠화재 CEO 겸임)", note="그룹 경영협의회 구성 서술")
B(d, 112, "겸직", "겸직임직원 보수배분 관련", note="감독당국 권고사항(금융감독원 종합검사 결과 경영유의사항)")

d = "M:메리츠금융지주:2024:본공시"
A(d, 25, start="겸직 대표이사의", end="의결권 제한", person="", holdco_title="대표이사", concurrent_company="", concurrent_title="",
  note="이사회 활동 표의 주석(상법 제368조 제3항) — 성명·겸직 회사 이름 없음. 같은 주석 p.28·p.29(두 번)에도. 이 쪽 글은 PDF 글자 순서가 섞여 추출됨")
A(d, 96, start="오종원", end="겸직", person="오종원", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 — 이 쪽 PDF 글은 칸 순서가 섞여 추출됨(직위 「메리츠금융지주 / 메리츠화재 / CRO / / CRO」, 비고 「위원장화재 / 겸직」)")
A(d, 206, start="3) 현재 겸직 업무", end="메리츠화재 사외이사", person="김명애", birth_ym="1967(출생년도만)", holdco_title="사외이사 후보",
  concurrent_company="메리츠화재", concurrent_title="사외이사", note=CAND + "; 성명은 같은 양식 「▣ 후보자 : 김명애」, 「· 출생년도 : 1967년」. 지주 사외이사 후보가 자회사 사외이사")
B(d, 85, "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직 서술(이 쪽 PDF 글은 숫자가 떨어져 추출됨 — 「감사팀총명」 뒤 「5」)")
B(d, 97, "겸직", "보수위원회의 겸직임직원 보수배분 관련 역할 강화", note="감독당국 권고사항 — 이 쪽 PDF 글은 쉼표·괄호가 떨어져 추출됨")
B(d, 97, "겸직", "겸직임직원 보수 분담기준", note="권고에 따른 조치 이행 서술")
B(d, 105, "겸직", start="그룹 겸직 임직원 보수 분담 기", end="준 수립의 건", note="보수위원회 결의 안건 표(3호안건)")

d = "S:메리츠금융지주:2025:본공시"
A(d, "43/0", start="주) 이상훈 사외이사는", end="판단합니다.", person="이상훈", holdco_title="사외이사(감사위원)", concurrent_company="법무법인 삼우", concurrent_title="대표변호사",
  concurrent_since="2012", note="감사위원 자격요건 표 주석")
A(d, "43/0", start="주) 조홍희", end="판단합니다.", person="조홍희", holdco_title="사외이사(감사위원)", concurrent_company="SK케미칼", concurrent_title="사외이사",
  note="감사위원 자격요건 표 주석")
A(d, "108/0", start="오종원", end="위원장, 화재 CRO 겸직", person="오종원", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄")
B(d, "96/0", "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직(감사팀 총5명) 서술")
B(d, "115/0", "겸직", start="나. 2호안건", end="분담기준 개정의     건", note="보수위원회 결의 안건 표")
B(d, "115/0", "겸직", "그룹 겸직   임직원   보수  분담 기준   개정의   건을 심의하고", note="보수위원회 결의 서술")

d = "S:메리츠금융지주:2026:본공시"
A(d, "103/0", start="오종원", end="위원장, 화재 CRO 겸직", person="오종원", holdco_title="메리츠금융지주 CRO", concurrent_company="메리츠화재", concurrent_title="CRO",
  note="그룹리스크협의회 구성 표 한 줄")
A(d, "118/3", start="3) 현재 겸직 업무", end="사외이사 및 감사위원", person="김명애", birth_ym="1967(출생년도만)", holdco_title="사외이사 후보",
  concurrent_company="메리츠화재", concurrent_title="사외이사 및 감사위원",
  note=CAND + "; 성명·출생년도는 같은 섹션 글 「▣ 후보자 : 김명애」「출생년도 : 1967년」. 섹션 제목은 「이연보수의 조정」이지만 6차 섹션 나눔이 부록 양식까지 이어 담은 것")
B(d, "85/0", "파견", "계열사의 인력을 파견 받아", note="감사위원회 감사보조조직(감사팀 총4명) 서술")

# ── iM금융지주(옛 DGB금융지주) ──
d = "M:iM금융지주:2020:본공시"
A(d, 15, start="현재", end="대구은행장을 겸임하고 있습니다.", person="김태오", holdco_title="회장(상임이사)", concurrent_company="대구은행", concurrent_title="은행장",
  concurrent_since="2019-01-29", note="이사회 구성원 서술 「나) 회장 김태오」 아래 문장")
A(d, 126, start="1,667천원 겸직수당", end="겸직수당 500천원 X 3회", person="김택동", holdco_title="사외이사", concurrent_company="", concurrent_title="",
  note="사외이사 김택동(재직 2019.03.28~2019.7.10) 보수 산출내역의 「겸직수당」 — 무엇을 겸직했는지는 이 글에 없음(판단: 겸직 대상 미상으로 둠)")
B(d, 175, "겸직", start="당해년도", end="사후 정산하였음", note="직급별 보수총액 및 성과보수액 표(당해년도 2019년 「인원」 줄 포함)와 주1)")

d = "M:iM금융지주:2021:본공시"
A(d, 14, start="현재 DGB금융지주 회장이며", end="겸임하였습니다.", person="김태오", holdco_title="회장(상임이사)", concurrent_company="대구은행", concurrent_title="은행장",
  concurrent_since="2019-01-29", note="겸임 기간 2019.1.29~2020.9.28(문장). 같은 보고서 p.56 후보 경력란 「2019.01 대구은행 은행장(2020.09월까지 겸임)」")
B(d, 151, "겸직", start="당해년도", end="사후 정산하였음", note="직급별 보수총액 및 성과보수액 표(당해년도 「인원」 줄 포함)와 주1). 주1)의 기준일 글자는 원문대로 「2019.12.31일」")

d = "M:iM금융지주:2022:본공시"
A(d, 16, start="현재", end="대구은행장을 겸임하였습니다.", person="김태오", holdco_title="회장(상임이사)", concurrent_company="대구은행", concurrent_title="은행장",
  concurrent_since="2019-01-29", note="겸임 기간 2019.1.29~2020.9.28(문장) — 이 연도에는 이미 끝난 겸임")
B(d, 157, "겸직", start="당해년도", end="사후 정산하였음", note="직급별 보수총액 및 성과보수액 표(당해년도 「인원」 줄 포함)와 주1)")

d = "M:iM금융지주:2023:본공시"
A(d, 16, start="현재", end="대구은행장을 겸임하였습니다.", person="김태오", holdco_title="회장(상임이사)", concurrent_company="대구은행", concurrent_title="은행장",
  concurrent_since="2019-01-29", note="겸임 기간 2019.1.29~2020.9.28(문장) — 이 연도에는 이미 끝난 겸임")
B(d, 154, "겸직", start="당해년도", end="사후 정산하였음", note="직급별 보수총액 및 성과보수액 표(당해년도 「인원」 줄 포함)와 주1) — PDF 글이 낱말마다 줄바뀜으로 추출됨")

d = "M:iM금융지주:2024:본공시"
A(d, 15, start="현재", end="대구은행장을 겸임하였습니다.", person="김태오", holdco_title="회장(상임이사)", concurrent_company="대구은행", concurrent_title="은행장",
  concurrent_since="2019-01-29", note="겸임 기간 2019.1.29~2020.9.28(문장) — 이 연도에는 이미 끝난 겸임")
B(d, 161, "겸직", start="당해년도", end="퇴직위로금이 포함됨.", note="임직원 보수 표(당해년도 「인원」 줄 포함)와 주2)")
B(d, 161, "겸직", "겸직 임직원에 대한 보수는 원소속회사에서 선지급하고", note="같은 표 주 3)")

d = "S:iM금융지주:2025:본공시"
A(d, "8/0", start="현재  DGB금융지주     회장이며,   2023년", end="겸임하고    있습니다.", person="황병우", holdco_title="회장(상임이사)",
  concurrent_company="아이엠뱅크", concurrent_title="은행장", concurrent_since="2023-01-01", note="이사회 구성원 서술 「나) 회장 황병우」 아래 문장")
A(d, "8/0", "2020년 9월 30일까지   대구은행장을    겸임한", person="김태오", holdco_title="회장(상임이사, 2024.3.28 퇴임)", concurrent_company="대구은행",
  concurrent_title="은행장", concurrent_since="2019-01-29", note="겸임 기간 2019.1.29~2020.9.30(문장) — 앞 연도 보고서들의 「9월 28일」과 글자가 다름(원문대로)")
B(d, "158/0", "겸직", "2024년도  겸직임원의    보수를  결정하고", note="보수위원회 활동 서술")
B(d, "158/0", "겸직", "1. 2024년도 겸직임원 보수 결정(안)", note="보수위원회 결의 안건 표")
B(d, "158/0", "겸직", start="1. 겸직임원의", end="신설", note="보수위원회 결의 안건 표(비고 칸)")
B(d, "158/0", "전적", start="1. 부사장  강정훈", end="보상결정", note="보수위원회 결의 안건 표 — 지주 부사장이 은행으로 전적")
B(d, "168/0", "겸직", start="주 2)  2024.12.31", end="퇴직위로금이 포함됨.", note="임직원 보수 표 주2)")
B(d, "168/0", "겸직", "겸직 임직원에   대한  보수는", note="임직원 보수 표 주 3)")

d = "S:iM금융지주:2026:본공시"
A(d, "12/1", "황병우 회장 iM뱅크 은행장 겸직 중으로", person="황병우", holdco_title="회장", concurrent_company="iM뱅크", concurrent_title="은행장",
  note="이사회 활동 표 주석(의결권 행사하지 않음)")
A(d, "12/1", "황병우 회장 UNGC 한국협회 이사직 겸직 중으로", person="황병우", holdco_title="회장", concurrent_company="UNGC 한국협회", concurrent_title="이사",
  note="이사회 활동 표 주석(의결권 행사하지 않음)")
A(d, "134/0", start="박병수", end="CRO) 겸직", person="박병수", holdco_title="위험관리책임자(CRO)", concurrent_company="iM뱅크", concurrent_title="CRO",
  note="위험관리협의회 구성 표 「의장 박병수 iM뱅크 CRO1)」 + 주 「1) 지주, 은행 위험관리책임자(CRO) 겸직」 — 표의 2025.01.01·2026.12.31 은 협의회 임기 칸(판단)")
A(d, "137/0", start="1. 상무 진영수", end="보상 결정", person="진영수", holdco_title="상무", concurrent_company="", concurrent_title="",
  note="보수위원회 결의 안건 표 — 겸직 해제. 원소속·겸직 회사 이름은 이 줄에 없음")
A(d, "137/0", start="1. 상무 성현탁 지주 겸직", end="활동수당 결의", person="성현탁", holdco_title="(지주 겸직)", concurrent_company="", concurrent_title="상무",
  note="보수위원회 결의 안건 표 — 「지주 겸직 결정」. 원소속 회사 이름은 이 줄에 없음. 같은 사람 다음 안건 「ICT총괄 본부MBO 과제 변경」")
for anc, cc, ct, extra in (
        ("현재 겸직 업무 : 에이비즈파트너스 부회장", "에이비즈파트너스", "부회장", ""),
        ("현재 겸직 업무 : 공인회계사 조동환 사무소 대표", "공인회계사 조동환 사무소", "대표", " 같은 칸이 감사위원후보 양식(시작페이지 58)에도. 사무소 이름에 「조동환」이 들어 있음"),
        ("현재 겸직 업무 : 정재수변호사사무소 대표변호사", "정재수변호사사무소", "대표변호사", " 칸 글에 「(재선임 당시 겸직 업무)」. 사무소 이름에 「정재수」가 들어 있음"),
        ("현재 겸직 업무 : 창신 INC 부사장", "창신 INC", "부사장", " 칸 글에 「(최초 선임일 기준)」"),
        ("현재 겸직 업무 : 동국대학교 회계학과 교수", "동국대학교", "회계학과 교수", " 칸 글에 「(최초 선임일 기준)」")):
    A(d, "35/1" if ("창신" in anc or "동국" in anc) else "35/0", anc, person="", holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note="사외이사후보 본인 소명 「(3) 현재 겸직 업무」 칸 — 후보 성명은 6차 섹션 글·13차 PDF 글 어디에도 이 칸 근처에 없음(성명 확인 못 함)." + extra)
B(d, "134/0", "겸직", start="박병수", end="CRO) 겸직", note="위험관리협의회 구성 표와 주")
B(d, "137/0", "겸직", "겸직해제   경영진   장기성과평가를     확정하고    보상을   결정하였습니다.", note="보수위원회 활동 서술")
B(d, "137/0", "겸직", "하반기   겸직  추가된    임원의   보수  결정(안)을   결의하였습니다.", note="보수위원회 활동 서술")
B(d, "137/0", "겸직", start="1. 상무 진영수", end="보상 결정", note="보수위원회 결의 안건 표")
B(d, "137/0", "겸직", start="1. 상무 성현탁 지주 겸직", end="활동수당 결의", note="보수위원회 결의 안건 표")
B(d, "137/0", "겸직", start="주2) 2025.12.31", end="포함됨.", note="임직원 보수 표 주2) — 「2024년 귀속연도」는 원문 글자대로")
B(d, "137/0", "겸직", start="주3) 겸직 임직원에 대한", end="사후 정산함.", note="임직원 보수 표 주3)")

# ── BNK금융지주 ──
SO = "이사회 구성원 서술(「(n)구성원」 아래 이사별 문단)"
d = "M:BNK금융지주:2020:본공시"
A(d, 26, "부산차이나비즈니스 포럼 회장을", person="김영재", holdco_title="사외이사", concurrent_company="부산대학교", concurrent_title="경제통상학부 교수",
  concurrent_since="2002.9", note=SO + " 「③ 이사 김영재(現)」")
A(d, 26, "부산차이나비즈니스 포럼 회장을", person="김영재", holdco_title="사외이사", concurrent_company="부산차이나비즈니스 포럼", concurrent_title="회장",
  note=SO + "; 같은 문장 두 번째 겸직")
A(d, 70, "당사의 자회사인 부산은행의 사외이사를 겸직 중", person="김영재", holdco_title="사외이사 후보", concurrent_company="부산은행", concurrent_title="사외이사",
  note="임원후보 추천 관련 「㉱ 충실성」 문단(뒤따르는 「김영재 후보자에 대한 사외이사 후보 추천」으로 성명 확인). 같은 사람 사외이사 보수 표 p.125 주석 「※ 임원보수규정 제4조에 의거, 기본급의 60% 범위 내에서 보수 지급(부산은행 사외이사 겸직)」, 후보 관계 칸 주석 p.69 「주)지배구조법 제6조 및 동법 시행령 제8조에 의거 당사의 자회사 사외이사는 겸직 가능」")
A(d, 26, "계명대학교 회계학과 명예교수(2009.3월~현재)를 겸직", person="정기영", holdco_title="사외이사", concurrent_company="계명대학교", concurrent_title="회계학과 명예교수",
  concurrent_since="2009.3", note=SO + " 「⑤ 이사 정기영(現)」")
A(d, 27, "신한회계법인 공인회계사(2013.3월~현재)를 겸직", person="유정준", holdco_title="사외이사", concurrent_company="신한회계법인", concurrent_title="공인회계사",
  concurrent_since="2013.3", note=SO + " 「⑥ 이사 유정준(現)」")
A(d, 27, "이스트드림시노펙스㈜ 회장(2017.7월~현재)을 겸직", person="손광익", holdco_title="사외이사", concurrent_company="이스트드림시노펙스㈜", concurrent_title="회장",
  concurrent_since="2017.7", note=SO + " 「⑦ 이사 손광익(現)」")
A(d, 27, "종합법률사무소 그레이스의 변호사(2016.3월~현재)를 겸직", person="허진호", holdco_title="사외이사", concurrent_company="종합법률사무소 그레이스", concurrent_title="변호사",
  concurrent_since="2016.3", note=SO + " 「⑧이사 허진호(現)」")
A(d, 28, "법무법인 해인의 대표 변호사(2017.2월~ )를 겸직하였", person="윤인태", holdco_title="사외이사(퇴임)", concurrent_company="법무법인 해인", concurrent_title="대표 변호사",
  concurrent_since="2017.2", note=SO + " 「⑨ 이사 윤인태(前)」 — 퇴임일 기준 겸직")
A(d, 66, "코스닥시장위원회의 위원을 겸직하고 있으나", person="문일재", holdco_title="사외이사 후보", concurrent_company="코스닥시장위원회", concurrent_title="위원(비상근)",
  note="임원후보 추천 관련 「㉱ 충실성」 문단(뒤따르는 「문일재 후보자에 대한」으로 성명 확인)")
A(d, 36, start="아울러, 당사 그룹D-IT부문", end="보고하였습니다.", person="", holdco_title="그룹D-IT부문·그룹G-IB부문·그룹WM부문(겸직)", concurrent_company="부산은행·경남은행",
  concurrent_title="경영진", note="이사회 보고 서술 — 자회사 경영진 6명이 지주 부문을 겸직하다 2019년 하반기 조직 개편으로 겸직 해제. 성명 없음(인원 6명). 이사회 안건 「바.경영진 겸직 해제 보고」 p.35·p.84")
B(d, 36, "겸직", start="아울러, 당사 그룹D-IT부문", end="보고하였습니다.", note="이사회 보고 서술(조직 개편에 따른 겸직 해제)")
B(d, 202, "겸직", "계열사 겸직 경영진의 경우 겸직 비율에 따라 보수 지급", note="보수체계 — 적용 대상")
B(d, 202, "겸직", "계열사 겸직 경영진 6명을 포함한", note="보수위원회 활동 서술")
B(d, 203, "겸직", start="2019년 7월 지주 조직개편에 따라", end="아래와 같습니다.", note="보수위원회 활동 서술")
B(d, 214, "겸직", start="임직원 총보수", end="주4)계열사와 겸직 22명 포함, 기중 퇴직인원 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주4)")
B(d, 214, "겸직", "주2)계열사와 겸직인 임직원 포함", note="직급별 보수총액 표 주2)")
B(d, 312, "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="지주사의 소관부서에 보고하", note="부록 관련 규정(지배구조 내부규범) 조문 — 쪽 끝까지(다음 쪽으로 이어짐)")

d = "M:BNK금융지주:2021:본공시"
A(d, 23, "계명대학교 회계학과 명예교수(2009.3월~현재)를 겸직", person="정기영", holdco_title="사외이사(이사회 의장)", concurrent_company="계명대학교", concurrent_title="회계학과 명예교수",
  concurrent_since="2009.3", note=SO + " 「(가)이사회 의장 정기영(現)」")
A(d, 24, "신한회계법인 공인회계사(2013.3월~현재)를 겸직", person="유정준", holdco_title="사외이사", concurrent_company="신한회계법인", concurrent_title="공인회계사",
  concurrent_since="2013.3", note=SO + "; 같은 겸직이 후보 충실성 문단 p.83 에도")
A(d, 25, "한국면세연구원㈜ 회장(2019.12월~현재)을 겸직", person="손광익", holdco_title="사외이사", concurrent_company="한국면세연구원㈜", concurrent_title="회장",
  concurrent_since="2019.12", note=SO + "; 같은 겸직이 후보 직무공정성·충실성 문단 p.87 에도")
A(d, 87, "후보자는 현재 이스트드림시노펙스㈜ 및 한국면세연구원㈜ 회장을", person="손광익", holdco_title="사외이사 후보", concurrent_company="이스트드림시노펙스㈜", concurrent_title="회장",
  note="임원후보 추천 관련 「라충실성」 문단(뒤따르는 「손광익 후보자에 대한」으로 성명 확인). 같은 쪽 「나직무공정성」 문단에도")
A(d, 25, "종합법률사무소 그레이스의 변호사(2016.3월~현재)를 겸직", person="허진호", holdco_title="사외이사", concurrent_company="종합법률사무소 그레이스", concurrent_title="변호사",
  concurrent_since="2016.3", note=SO)
A(d, 26, "부산차이나비즈니스 포럼 회장을 겸직하였으며", person="김영재", holdco_title="사외이사(퇴임)", concurrent_company="부산대학교", concurrent_title="경제통상학부 교수",
  concurrent_since="2002.9", note=SO + " — 퇴임일 기준 겸직")
A(d, 26, "부산차이나비즈니스 포럼 회장을 겸직하였으며", person="김영재", holdco_title="사외이사(퇴임)", concurrent_company="부산차이나비즈니스 포럼", concurrent_title="회장",
  note=SO + " — 퇴임일 기준 겸직, 같은 문장 두 번째")
A(d, 74, "코스닥시장위원회 위원을 겸직하고 있으나", person="문일재", holdco_title="사외이사 후보", concurrent_company="코스닥시장위원회", concurrent_title="위원(비상근)",
  note="임원후보 추천 관련 「라충실성」 문단(뒤따르는 「문일재 후보자에 대한」으로 성명 확인)")
A(d, 38, start="가.(사)2030부산월드엑스포 유치위원회 후원(안)", end="출연 승인", person="김지완", holdco_title="대표이사 회장", concurrent_company="(사)2030부산월드엑스포 유치위원회",
  concurrent_title="이사", note="이사회 결의안건 서술. (판단) 성명은 문장에 없음 — 같은 보고서 이사회 구성원 서술의 대표이사 회장 김지완. 같은 내용 p.20 「당사 대표이사 회장이 해당 법인의 이사 겸임에 따른 이해상충행위 감독」")
A(d, 38, start="가.(사)2030부산월드엑스포 유치위원회 후원(안)", end="출연 승인", person="김지완", holdco_title="대표이사 회장", concurrent_company="(재)BNK금융그룹희망나눔재단",
  concurrent_title="이사", note="이사회 결의안건 서술 두 번째 법인. (판단) 성명은 문장에 없음 — 대표이사 회장 김지완")
B(d, 226, "겸직", "평가 대상 경영진 16명(겸직 경영진 포함)", note="보수위원회 결의안건 서술")
B(d, 238, "겸직", start="임직원 총보수", end="주4)계열사와 겸직 7명 포함, 기중 퇴직인원 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주4)")
B(d, 238, "겸직", "주2)직원 : 계열사와 겸직인 직원 포함", note="직급별 보수총액 표 주2)")
B(d, 342, "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="내부통제기준에 위반되는 경우", note="부록 관련 규정(지배구조 내부규범) 조문 — 쪽 끝까지(②③항은 p.343)")

d = "M:BNK금융지주:2022:본공시"
A(d, 25, "계명대학교 회계학과 명예교수(2009.3월~현재)를 겸직", person="정기영", holdco_title="사외이사(이사회 의장)", concurrent_company="계명대학교", concurrent_title="회계학과 명예교수",
  concurrent_since="2009.3", note=SO)
A(d, 26, "신한회계법인 공인회계사(2013.3월~현재)를 겸직", person="유정준", holdco_title="사외이사", concurrent_company="신한회계법인", concurrent_title="공인회계사",
  concurrent_since="2013.3", note=SO + "; 같은 겸직이 후보 충실성 문단 p.73 에도")
A(d, 26, "종합법률사무소 그레이스의 변호사(2016.3월~현재)를 겸직", person="허진호", holdco_title="사외이사", concurrent_company="종합법률사무소 그레이스", concurrent_title="변호사",
  concurrent_since="2016.3", note=SO + "; 같은 겸직이 후보 직무공정성·충실성 문단 p.77·p.78 에도")
A(d, 27, "삼일세무법인의 비상근 고문(2017.04월~현재)을 겸직", person="최경수", holdco_title="사외이사", concurrent_company="삼일세무법인", concurrent_title="비상근 고문",
  concurrent_since="2017.04", note=SO + "; 같은 겸직이 후보 직무공정성·충실성 문단 p.82 에도")
A(d, 28, "(재)ProQ장학회 이사", person="문일재", holdco_title="사외이사(퇴임)", concurrent_company="코스닥시장위원회", concurrent_title="위원",
  note=SO + " — 퇴임일 기준 겸직")
A(d, 28, "(재)ProQ장학회 이사", person="문일재", holdco_title="사외이사(퇴임)", concurrent_company="(재)ProQ장학회", concurrent_title="이사장",
  note=SO + " — 퇴임일 기준 겸직, 같은 문장 두 번째")
A(d, 29, "한국면세연구원㈜", person="손광익", holdco_title="사외이사(퇴임)", concurrent_company="이스트드림시노펙스㈜", concurrent_title="회장", note=SO + " — 퇴임일 기준 겸직")
A(d, 29, "한국면세연구원㈜", person="손광익", holdco_title="사외이사(퇴임)", concurrent_company="한국면세연구원㈜", concurrent_title="회장", note=SO + " — 퇴임일 기준 겸직, 같은 문장 두 번째")
A(d, 21, "당사 대표이사 회장이 해당 법인의 이사 겸임", person="김지완", holdco_title="대표이사 회장", concurrent_company="(사)2030부산월드엑스포 범시민유치위원회",
  concurrent_title="이사", note="이사회 운영 서술. (판단) 성명은 문장에 없음 — 같은 보고서의 대표이사 회장 김지완. 결의안건 p.38 「당사 대표이사 회장이 이사로 겸임 중인」")
B(d, 231, "겸직", start="임직원 총보수", end="주4)계열사와 겸직 7명 포함, 기중 퇴직인원 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주4)")
B(d, 231, "겸직", "주2)직원 : 계열사와 겸직인 직원 포함", note="직급별 보수총액 표 주2)")
B(d, 337, "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="지주사의 소관부서에 보고하", note="부록 관련 규정(지배구조 내부규범) 조문")

d = "M:BNK금융지주:2023:본공시"
A(d, 12, "BNK캐피탈 대표이사가 당사 비상임이사를 겸직하며", person="안감찬", holdco_title="비상임이사", concurrent_company="부산은행", concurrent_title="은행장",
  note="이사회 구성 서술(2022년 말 현재) — 자회사 CEO 가 지주 비상임이사 겸직. 성명은 같은 보고서 이사회 결의 주석 p.37 「부산은행장을 겸직하고 있는 안감찬 이사의 의결권 제한」(p.94 에도)")
A(d, 12, "BNK캐피탈 대표이사가 당사 비상임이사를 겸직하며", person="이두호", holdco_title="비상임이사", concurrent_company="BNK캐피탈", concurrent_title="대표이사",
  note="이사회 구성 서술(2022년 말 현재). 성명은 같은 보고서 주석 p.38 「BNK캐피탈 대표이사를 겸직 중인 이두호 이사의 의결권 제한」(p.40·p.94·p.95 에도), p.44·p.98 「해당 계열사 CEO를 겸직하고 있는 안감찬 이사 및 이두호 이사」")
A(d, 70, "후보자는 현재 신한회계법인 공인회계사를 겸직하고 있으나", person="유정준", holdco_title="사외이사 후보", concurrent_company="신한회계법인", concurrent_title="공인회계사",
  note="임원후보 추천 관련 「라충실성」 문단(뒤따르는 「유정준 후보자에 대한」으로 성명 확인)")
A(d, 74, "후보자는 종합법률사무소 그레이스 변호사를 겸직 중이나", person="허진호", holdco_title="사외이사 후보", concurrent_company="종합법률사무소 그레이스", concurrent_title="변호사",
  note="임원후보 추천 관련 「나직무공정성」 문단(같은 쪽 「라충실성」 문단에도; 뒤따르는 「허진호 후보자에 대한」으로 성명 확인)")
A(d, 84, "㈜오아시스 대외법무이사 등을 겸직하고 있으나", person="김수희", holdco_title="사외이사 후보", concurrent_company="㈜오아시스", concurrent_title="대외법무이사",
  note="임원후보 추천 관련 「라충실성」 문단(뒤따르는 「김수희 후보자에 대한」으로 성명 확인). 원문 「등」 — 나머지 겸직은 이 문단에 없음. 같은 문단에 「2021년 중 ㈜부산은행 사외이사직을 역임」")
B(d, 231, "겸직", start="(1)임직원 총보수", end="주3)계열사 겸직 및 퇴직자 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주3)")
B(d, 232, "겸직", "주2)직원 : 계열사 겸직 및 퇴직자 포함", note="직급별 보수총액 표 주2)")
B(d, 338, "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="평가하여야 한다.", note="부록 관련 규정(지배구조 내부규범) 조문 — 제1항 머리")

d = "M:BNK금융지주:2023:수정공시"
B(d, 1, "겸직", start="[수정 후]", end="주3)계열사 겸직 및 퇴직자 포함", note="2022년도 보수체계 연차보고서 수정 공시(2024-04-26 게시) — 임직원 총보수 표 [수정 후](임직원수 칸 포함)와 주3)")
B(d, 2, "겸직", start="[수정 후]", end="주2)직원 : 계열사 겸직 및 퇴직자 포함", note="수정 공시 — 직급별 보수총액 표 [수정 후]와 주2)")

d = "M:BNK금융지주:2024:본공시"
A(d, 71, "후보자는 세무법인 두리 고문을 겸직 중이나", person="최경수", holdco_title="사외이사 후보", concurrent_company="세무법인 두리", concurrent_title="고문",
  note="임원후보 추천 관련 「나직무공정성」 문단(같은 쪽 「라충실성」 문단에도; 뒤따르는 「최경수 후보자에 대한」으로 성명 확인)")
A(d, 136, "당사 사외이사 겸직에 대한 승인을 득하였으며", person="정영석", holdco_title="사외이사", concurrent_company="한국해양대학교", concurrent_title="(재직, 직위 글에 없음)",
  note="사외이사 평가 「②직무공정성」 문단 — 소속 국립대학교가 당사 사외이사 겸직을 승인(교육공무원법 근거). 겸직의 방향이 학교 쪽에서 본 것임")
B(d, 243, "겸직", start="(1)임직원 총보수", end="주3)계열사 겸직 및 퇴직자 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주3)")
B(d, 244, "겸직", "주2)직원 : 계열사 겸직 및 퇴직자 포함", note="직급별 보수총액 표 주2)")
B(d, 357, "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="소관부서는 이를 적절히 관리하여야 한다.", note="부록 관련 규정(지배구조 내부규범) 조문")

d = "M:BNK금융지주:2024:수정공시"
B(d, 1, "겸직", start="[수정 후]", end="주2)직원 : 계열사 겸직 및 퇴직자 포함", note="2023년도 보수체계 연차보고서 수정 공시(2024-04-26 게시) — 직급별 보수총액 표 [수정 후]와 주2)")

d = "S:BNK금융지주:2025:본공시"
A(d, "50/0", "후보자는  세무법인    두리  고문을  겸직  중이나", person="최경수", holdco_title="사외이사 후보", concurrent_company="세무법인 두리", concurrent_title="고문",
  note="임원후보 추천 관련 「나직무공정성」 문단(같은 섹션 「라충실성」 문단에도). (판단) 성명은 FY2023 보고서의 같은 문단(최경수)과 글이 같아 그대로 둠 — 6차 섹션 글에서 성명을 따로 확인하지 못함")
A(d, "50/4", "당사  사외이사    겸직에  대한   승인을   득하였으며", person="정영석", holdco_title="사외이사", concurrent_company="한국해양대학교", concurrent_title="(재직, 직위 글에 없음)",
  note="사외이사 평가 「②직무공정성」 문단")
B(d, "243/0", "겸직", start="(1)임직원  총보수", end="주3)계열사 겸직 및  퇴직자  포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주3)")
B(d, "243/0", "겸직", "주2)직원 : 계열사   겸직  및  퇴직자 포함", note="직급별 보수총액 표 주2)")
B(d, "243/6", "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="평가하여야 한다.", note="부록 관련 규정(지배구조 내부규범) 조문 — 제1항 머리")

d = "S:BNK금융지주:2026:본공시"
A(d, "54/5", "당사  사외이사    겸직에   대한  승인을   득하였으며", person="정영석", holdco_title="사외이사", concurrent_company="한국해양대학교", concurrent_title="(재직, 직위 글에 없음)",
  note="사외이사 평가 「②직무공정성」 문단")
B(d, "266/0", "겸직", "겸직 경영진에 대해 ⏎ 업무수행비율에      따라  평가   및 보상하는", note="보수위원회 결의 내용 서술")
B(d, "278/0", "겸직", "겸직  임원에   대한  장기성과평가     보상  방법을   개선하였습니다.", note="보수체계 주요 변경 사항")
B(d, "278/0", "겸직", "겸직   임원의   업무  수행  비율에   따라  평가", note="보수체계 주요 변경 사항")
B(d, "278/0", "겸직", start="(1)임직원  총보수", end="주3)계열사 겸직 및  퇴직자 포함", note="임직원 총보수 표(임직원수 칸 포함)와 주1)~주3)")
B(d, "278/0", "겸직", "주2)계열사 겸직     및  퇴직자 포함, 사외이사", note="보수 표 주2)")
B(d, "278/6", "겸직", start="제28조(임직원 겸직 및 업무위탁에 대한 평가ㆍ관리)", end="평가하여야 한다.", note="부록 관련 규정(지배구조 내부규범) 조문 — 제1항 머리")

# ── JB금융지주 ──
# 15차 검증에서 더함: 리스크관리운영위원회 구성 표의 「(겸)」 약자 표기(앞선 검색어 겸직·겸임·겸무에 걸리지 않던 자리)
JBKYUM = ("리스크관리운영위원회 구성 표(성명·직위·선임일·비고) 「지주사/전북/광주은행CRO(겸)」 — 「(겸)」 약자 표기라 처음 찾기(겸직·겸임·겸무)에 "
          "걸리지 않던 것을 15차 검증(verify15_gov_g2)에서 더함. 한 칸의 겸직처 둘을 행으로 나눔. 선임일 2019.04.30 은 협의회 위원 선임일로 보아 "
          "concurrent_since 를 비움(판단)")
d = "M:JB금융지주:2021:본공시"
for p, nm, end, cc, ct, extra in (
        (49, "정재식", "서강대경제학부교수", "서강대", "경제학부교수", ""),
        (51, "김우진", "한국금융연구원선임연구위원/", "한국금융연구원", "선임연구위원", ""),
        (51, "김우진", "한마음금융사외이사/", "한마음금융", "사외이사", " 같은 칸 두 번째"),
        (51, "김우진", "희망모아이사", "희망모아", "이사", " 같은 칸 세 번째"),
        (53, "박종일", "법무법인태환대표변호사", "법무법인태환", "대표변호사", " 같은 칸이 감사위원 후보 양식 p.58 에도"),
        (56, "유관우", "김․장법률사무소고문(現)", "김․장법률사무소", "고문", "")):
    A(d, p, start="3) 현재겸직업무", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND.replace("3) 현재 겸직 업무", "3) 현재겸직업무") + "; 성명은 같은 양식 「%s후보자는 …」 문단.%s" % (nm, extra))
A(d, 151, start="2016년 2월", end="개정을 결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사", concurrent_title="리스크관리책임자(CRO)",
  note="리스크관리위원회 연혁 서술(2016년 2월 제2차 리스크관리위원회) — 성명 없음")
B(d, 151, "겸직", start="2016년 2월", end="개정을 결의하였", note="리스크관리위원회 연혁 서술(리스크관리운영위원회 구성 보강)")
B(d, 185, "전적", "중도퇴사자(자회사 전적 및 퇴직)", note="직급별 보수 표 주석 — 임직원 보수총액 산정 범위")
for cc in ("전북은행", "광주은행"):
    A(d, 167, start="이승국", end="위원장, 리스크관리책임자", person="이승국", holdco_title="지주사 CRO(리스크관리운영위원회 위원장)",
      concurrent_company=cc, concurrent_title="CRO", note=JBKYUM)

d = "M:JB금융지주:2022:본공시"
for p, nm, end, cc, ct, extra in (
        (55, "유관우", "김ㆍ장법률사무소고문(現)", "김ㆍ장법률사무소", "고문", " 같은 칸이 감사위원 후보 양식 p.62 에도"),
        (57, "이상복", "동아송강회계법인파트너(現)", "동아송강회계법인", "파트너", " 같은 칸 p.64 에도"),
        (59, "성제환", "한국IT직업전문학교석좌교수", "한국IT직업전문학교", "석좌교수", " 같은 칸 p.66 에도")):
    A(d, p, start="3) 현재겸직업무", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND.replace("3) 현재 겸직 업무", "3) 현재겸직업무") + "; 성명은 같은 양식 「%s후보자는 …」 문단.%s" % (nm, extra))
A(d, 177, start="2016년 2월", end="개정을 결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사", concurrent_title="리스크관리책임자(CRO)",
  note="리스크관리위원회 연혁 서술(2016년 2월 제2차 리스크관리위원회) — 성명 없음")
B(d, 177, "겸직", start="2016년 2월", end="개정을 결의하였", note="리스크관리위원회 연혁 서술")
for cc in ("전북은행", "광주은행"):
    A(d, 195, start="이승국", end="위원장, 리스크관리책임자", person="이승국", holdco_title="지주사 CRO(리스크관리운영위원회 위원장)",
      concurrent_company=cc, concurrent_title="CRO", note=JBKYUM)

d = "M:JB금융지주:2023:본공시"
for p, nm, end, cc, ct, extra in (
        (49, "정재식", "서강대경제학부교수(現)", "서강대", "경제학부교수", ""),
        (51, "김우진", "한국금융연구원선임연구위원(現)", "한국금융연구원", "선임연구위원", ""),
        (53, "박종일", "법무법인제이엘대표변호사(現)", "법무법인제이엘", "대표변호사", " 같은 칸 p.58 에도"),
        (55, "이성엽", "우리회계법인회계사(現)", "우리회계법인", "회계사", "")):
    A(d, p, start="3) 현재겸직업무", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND.replace("3) 현재 겸직 업무", "3) 현재겸직업무") + "; 이 쪽 PDF 글은 같은 글이 두 번(띄어쓰기 없이/「現」 괄호 없이) 겹쳐 추출됨 — 둘째 줄까지 실음. 성명은 같은 양식 「…%s후보자는」 문단(이름 앞 글자가 앞 줄 끝에 있는 경우 있음).%s" % (nm, extra))
A(d, 174, start="차 리스크관리위원회에서는 지주회사 및 은행자회사", end="개정을 결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사", concurrent_title="리스크관리책임자(CRO)",
  note="리스크관리위원회 연혁 서술(2016년 2월 제2차 리스크관리위원회) — 성명 없음. 이 쪽 PDF 글은 같은 글이 두 겹으로 섞여 추출됨(「(CRO)」 글자 빠짐 등)")
B(d, 174, "겸직", start="차 리스크관리위원회에서는 지주회사 및 은행자회사", end="개정을 결의하였", note="리스크관리위원회 연혁 서술 — 이 쪽 PDF 글은 같은 글이 두 겹으로 섞여 추출됨")

d = "M:JB금융지주:2024:본공시"
for p, nm, end, cc, ct, extra in (
        (48, "유관우", "김앤장법률사무소고문(現)", "김앤장법률사무소", "고문", " 같은 칸 p.55 에도"),
        (50, "이상복", "동아송강회계법인파트너(現)", "동아송강회계법인", "파트너", " 같은 칸 p.57 에도"),
        (52, "성제환", "익산시문화도시추진위원회위원장(現)", "익산시문화도시추진위원회", "위원장", " 같은 칸 p.59 에도")):
    A(d, p, start="3) 현재겸직업무", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND.replace("3) 현재 겸직 업무", "3) 현재겸직업무") + "; 이 쪽 PDF 글은 같은 글이 두 번 겹쳐 추출됨. 성명은 같은 양식 「…%s후보자는」 문단(이름 앞 글자가 앞 줄 끝에 있는 경우 있음).%s" % (nm, extra))

A(d, 153, start="차 리스크관리위원회에서는 지주회사 및 은행자회사", end="개정을 결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사", concurrent_title="리스크관리책임자(CRO)",
  note="리스크관리위원회 연혁 서술(2016년 2월 제2차 리스크관리위원회) — 성명 없음. 이 쪽 PDF 글은 같은 글이 두 겹으로 섞여 추출됨(「(CRO)」 글자 빠짐 등)")
B(d, 153, "겸직", start="차 리스크관리위원회에서는 지주회사 및 은행자회사", end="개정을 결의하였", note="리스크관리위원회 연혁 서술 — 이 쪽 PDF 글은 같은 글이 두 겹으로 섞여 추출됨")

d = "S:JB금융지주:2025:본공시"
for p, nm, end, cc, ct, extra in (
        ("58/0", "유관우", "고문(現)", "김앤장 법률사무소", "고문", " 같은 칸이 감사위원 후보(시작페이지 75)에도"),
        ("60/0", "이상복", "동아송강회계법인)(現)", "동성회계계법인(舊 동아송강회계법인)", "(칸에 직위 없음)", " 감사위원 후보(시작페이지 77) 같은 칸에는 「… 파트너(現)」"),
        ("62/0", "김우진", "선임연구위원(現)", "한국금융연구원", "선임연구위원", ""),
        ("64/0", "박종일", "대표  변호사(現)", "법무법인 제이엘", "대표 변호사", ""),
        ("66/0", "이성엽", "회계사(現)", "우리회계법인", "회계사", " 같은 칸이 감사위원 후보(시작페이지 79)에도"),
        ("68/0", "이명상", "대표변호사(現)", "법무법인 지안", "대표변호사", ""),
        ("70/0", "김기석", "대표(現)", "크라우디", "창업 대표", "")):
    A(d, p, start="3) 현재", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND + "; (판단) 성명은 6차 섹션 나눔에서 이 후보 양식 바로 앞 섹션 끝의 후보 머리글(「가) 유관우」「나) 이상복」 …)로 읽음." + extra)
A(d, "210/0", start="제2차  리스크관리위원회에서는", end="개정을   결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사",
  concurrent_title="리스크관리책임자(CRO)", note="리스크관리위원회 연혁 서술(2016년 2월) — 성명 없음")
B(d, "210/0", "겸직", start="제2차  리스크관리위원회에서는", end="개정을   결의하였", note="리스크관리위원회 연혁 서술")

d = "S:JB금융지주:2026:정정공시"
JB26 = (" (판단) 본공시(2026-03-05) 6차 섹션 글은 글자가 겹쳐 추출되어(예: 「현재현재겸직겸직업무업무」) 같은 내용을 정정공시(2026-04-07) 섹션 글에서 옮김;"
        " 성명은 6차 섹션 나눔에서 이 후보 양식 바로 앞 섹션 끝의 후보 머리글(「가) 성제환」「나) 김용환」「다) 강창훈」)로 읽음.")
for p, nm, end, cc, ct, extra in (
        ("60/0", "성제환", "석좌교수(現)", "한국IT직업전문학교", "석좌교수", " 같은 칸이 감사위원 후보(시작페이지 67)에도"),
        ("62/0", "김용환", "고문(現)", "법무법인 세종", "고문", " 같은 칸이 감사위원 후보(시작페이지 69)에도"),
        ("64/0", "강창훈", "고문(現)", "법무법인 케이원챔버", "고문", "")):
    A(d, p, start="3) 현재", end=end, person=nm, holdco_title="사외이사 후보", concurrent_company=cc, concurrent_title=ct,
      note=CAND + ";" + JB26 + extra)
A(d, "167/0", start="제2차 리스크관리위원회에서는", end="개정을   결의하였", person="", holdco_title="리스크관리책임자(CRO)", concurrent_company="은행자회사",
  concurrent_title="리스크관리책임자(CRO)", note="리스크관리위원회 연혁 서술(2016년 2월) — 성명 없음." + JB26.split(";")[0])
B(d, "167/0", "겸직", start="제2차 리스크관리위원회에서는", end="개정을   결의하였", note="리스크관리위원회 연혁 서술." + JB26.split(";")[0])

# ── 한국투자금융지주 ──
d = "M:한국투자금융지주:2020:본공시"
A(d, 14, start="이사회 의장인 김남구", end="부회장을 겸임하고 있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="부회장", note="이사회 구성 서술")
A(d, 15, start="이강행 이사는", end="겸임하고 있습니다.", person="이강행", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  concurrent_since="2016", note="이사회 구성 서술. since 는 같은 보고서 후보제안자 경력란 p.38·p.45 「2016 ~ 현재 / 한국투자증권 기타비상무이사 겸직」")
d0 = d
d = "M:한국투자금융지주:2021:본공시"
A(d, 15, start="이사회 의장인 김남구", end="회장을 겸임하고 있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술")
A(d, 15, start="이강행 이사는", end="겸임하고 있습니다.", person="이강행", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  concurrent_since="2016", note="이사회 구성 서술. since 는 후보제안자 경력란 p.35·p.37·p.39 「2016 ~ 현재 / 한국투자증권 기타비상무이사 겸직」")
d = "M:한국투자금융지주:2022:본공시"
A(d, 15, start="이사회 의장인 김남구", end="회장을 겸임하고 있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술")
A(d, 15, start="이강행 이사는", end="겸임하고 있습니다.", person="이강행", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  concurrent_since="2016", note="이사회 구성 서술. since 는 후보제안자 경력란 p.39·p.41·p.49 「2016 ~ 현재 / 한국투자증권 기타비상무이사 겸직」")
d = "M:한국투자금융지주:2023:본공시"
A(d, 15, start="이사회 의장인 김남구", end="회장을 겸임하고 있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술")
A(d, 15, start="오태균 이사는", end="겸임하고 있습니다.", person="오태균", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  note="이사회 구성 서술")
d = "M:한국투자금융지주:2024:본공시"
A(d, 15, start="이사회 의장인 김남구", end="회장을 겸임하고 있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술")
A(d, 15, start="오태균 이사는", end="겸임하고 있습니다.", person="오태균", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  note="이사회 구성 서술")
# 사외이사 — 「①회사 또는 계열회사와의 관계」 칸(현재 겸직 / 선임 후 겸직 예정). 성명은 앞쪽 「▶ 이름」·「후보자 이름은」 머리글(판단)
KREL = "사외이사 후보 「다. 금융회사등과 관계 ①회사 또는 계열회사와의 관계」 칸. (판단) 성명은 이 칸 앞쪽 후보 머리글(「▶ 이름 사외이사」 또는 「후보자 이름은」)에서 읽음"
for dd, p, nm, now in (
        ("2020", 38, "김정기", True), ("2020", 41, "조영태", False), ("2020", 43, "윤대희", False), ("2020", 45, "김태원", False),
        ("2021", 37, "정영록", True),
        ("2022", 41, "정영록", True), ("2022", 43, "김정기", False), ("2022", 45, "조영태", False), ("2022", 47, "윤대희", False), ("2022", 49, "김태원", False), ("2022", 51, "함춘승", False),
        ("2023", 45, "정영록", True), ("2023", 48, "김정기", False), ("2023", 50, "조영태", False), ("2023", 52, "김태원", False), ("2023", 54, "최수미", False),
        ("2024", 41, "정영록", True), ("2024", 43, "김정기", False), ("2024", 45, "조영태", False), ("2024", 47, "김태원", False), ("2024", 49, "함춘승", False)):
    A("M:한국투자금융지주:%s:본공시" % dd, p, start="①회사 또는 계열회사와의", end="없음", person=nm, holdco_title="사외이사 후보",
      concurrent_company="한국투자증권", concurrent_title="사외이사",
      note=KREL + (" — 「현재 … 겸직하고 있으나」" if now else " — 「선임 후 … 겸직할 예정이나」(겸직 예정)") + ". 법령 근거·이해상충 판단 문구는 사유 문단으로 보지 않음(판단)"
      + {("2020", 38): ". 같은 사람의 사외이사 후보 양식 p.40 같은 칸에는 「선임 후 당사 및 한국투자증권 사외이사를 겸직할 예정이나」",
         ("2021", 37): ". 같은 사람의 다른 후보 양식 p.40 같은 칸에도 같은 글"}.get((dd, p), ""))
for dd, p, kw, a, note in (
        ("2020", 49, "겸직", "실장 1 명(총괄) 실원 9 명 (계열사 겸직 임직원 제외)", "사외이사 지원부서(경영지원실) 설치 현황"),
        ("2020", 61, "겸직", "실장(총괄)외 9 명 (총10 명, 계열사 겸직 직원 제외)", "사외이사 지원부서 표"),
        ("2020", 73, "겸직", "경영지원실 인원은 총 10 명(계열사 겸직", "최고경영자 승계업무 지원부서 서술"),
        ("2020", 177, "파견", "외부위탁 파견연수", "부록 관련 규정 조문(임원 연수)"),
        ("2022", 56, "겸직", "실장 1 명(총괄) 실원 13 명 (계열사 겸직 임직원 제외)", "사외이사 지원부서(경영지원실) 설치 현황"),
        ("2022", 67, "겸직", "실장(총괄)외 12 명 (총13 명, 계열사 겸직 직원 제외)", "사외이사 지원부서 표"),
        ("2022", 77, "겸직", "경영지원실 인원은 총 13 명(계열사 겸직", "최고경영자 승계업무 지원부서 서술"),
        ("2022", 181, "파견", "외부위탁 파견연수", "부록 관련 규정 조문(임원 연수)"),
        ("2024", 58, "겸직", "실장 1 명(총괄) 실원 11 명 (계열사 겸직 임직원 제외)", "사외이사 지원부서(경영지원실) 설치 현황"),
        ("2024", 73, "겸직", "실장(총괄)외 11 명 (총12 명, 계열사 겸직 직원 제외)", "사외이사 지원부서 표"),
        ("2024", 85, "겸직", "경영지원실 인원은 총 12 명(계열사 겸직", "최고경영자 승계업무 지원부서 서술"),
        ("2024", 199, "파견", "외부위탁 파견연수", "부록 관련 규정 조문(임원 연수)"),
        ("2021", 44, "겸직", "(계열사 겸직 임직원 제외)", "사외이사 지원부서(경영지원실) 설치 현황"),
        ("2021", 56, "겸직", "계열사 겸직 직원 제외)", "사외이사 지원부서 표"),
        ("2021", 66, "겸직", "경영지원실 인원은 총", "최고경영자 승계업무 지원부서 서술"),
        ("2021", 167, "파견", "외부위탁 파견연수", "부록 관련 규정 조문(임원 연수)"),
        ("2023", 61, "겸직", "(계열사 겸직 임직원 제외)", "사외이사 지원부서(경영지원실) 설치 현황"),
        ("2023", 73, "겸직", "계열사 겸직 직원 제외)", "사외이사 지원부서 표"),
        ("2023", 84, "겸직", "경영지원실 인원은 총", "최고경영자 승계업무 지원부서 서술"),
        ("2023", 191, "파견", "외부위탁 파견연수", "부록 관련 규정 조문(임원 연수) — 재공시에서는 조문 번호가 제27조로 바뀜")):
    B("M:한국투자금융지주:%s:본공시" % dd, p, kw, a, note=note)
d = "M:한국투자금융지주:2021:재공시"
B(d, 104, "전출", "사간전출 등 퇴직 임직원에 대한 성과급 지급분을 포함하여 기재", note="재공시(2021-04-15)에만 있는 글 — 임직원 총보수 표 주1). 본공시(2021-03-05)에는 이 주석 없음")
d = "S:한국투자금융지주:2025:본공시"
A(d, "14/0", start="주력  자회사인", end="겸임하고    있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술 — 6차 섹션 글의 이 문장에는 성명이 없음(앞 문장 「…김남구 대표이사는…」으로 판단)", _pre="임기는")
A(d, "14/0", start="오태균  이사는", end="겸임하고 있습니다.", person="오태균", holdco_title="사내이사", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  note="이사회 구성 서술")
A(d, "39/0", "선임 후 당사 및 한국투자증권 사외이사를 겸직할 예정이나", person="", holdco_title="사외이사 후보", concurrent_company="한국투자증권",
  concurrent_title="사외이사", note="사외이사 후보 「금융회사등과 관계」 칸 — 선임 후 겸직 예정. 6차 섹션 글에 성명 없음(성명 확인 못 함). 같은 글 시작페이지 39 chunk 1 에도")
B(d, "130/2", "파견", "외부위탁 파견연수", note="부록 관련 규정 조문(임원 연수)")
d = "S:한국투자금융지주:2026:본공시"
A(d, "15/0", start="주력   자회사인", end="겸임하고   있습니다.", person="김남구", holdco_title="대표이사(이사회 의장)", concurrent_company="한국투자증권",
  concurrent_title="회장", note="이사회 구성 서술 — 6차 섹션 글의 이 문장에는 성명이 없음(앞 문장으로 판단)")
A(d, "15/0", start="오태균  이사는", end="겸임하고   있습니다.", person="오태균", holdco_title="사내이사(사장)", concurrent_company="한국투자증권", concurrent_title="비상임이사",
  note="이사회 구성 서술")
A(d, "40/0", "선임 후  당사 및  한국투자증권 사외이사를       겸직할 예정이나", person="", holdco_title="사외이사 후보", concurrent_company="한국투자증권",
  concurrent_title="사외이사", note="사외이사 후보 「금융회사등과 관계」 칸 — 선임 후 겸직 예정. 6차 섹션 글에 성명 없음(성명 확인 못 함)")
B(d, "131/3", "파견", "외부위탁 파견연수", note="부록 관련 규정 조문(임원 연수)")

# 같은 글 판정(본공시 행에 붙일 note) — 키워드 문맥 대조 결과(쪽 번호만 다른 경우 포함)
SAME = {
    "M:iM금융지주:2022:본공시": "추가공시(2022-04-15) 같은 글",
    "M:iM금융지주:2023:본공시": "추가공시(2023-04-14) 같은 글",
    "M:JB금융지주:2023:본공시": "추가공시(2023-04-12) 같은 글",
    "M:한국투자금융지주:2021:본공시": "재공시(2021-04-15) 같은 글(재공시에만 「사간전출」 주석 — 따로 행)",
    "M:한국투자금융지주:2022:본공시": "재공시(2022-04-15) 같은 글(쪽 번호만 다름)",
    "M:한국투자금융지주:2023:본공시": "재공시(2023-04-14) 같은 글(쪽 번호·부록 조문 번호만 다름)",
    "M:한국투자금융지주:2024:본공시": "재공시(2024-04-15) 같은 글(쪽 번호만 다름)",
    "S:iM금융지주:2025:본공시": "추가공시 같은 글(6차 섹션 글 대조)",
    "S:iM금융지주:2026:본공시": "추가공시 같은 글(6차 섹션 글 대조)",
    "S:한국투자금융지주:2025:본공시": "재공시 같은 글(6차 섹션 글 대조)",
    "S:한국투자금융지주:2026:본공시": "재공시 같은 글(6차 섹션 글 대조)",
}
# 문서마다 찾은 범위(「문서에 없음」 행 note 용)
SCOPE = "찾은 범위: 문서 전체 쪽 글에서 「겸직·겸임·겸무·파견·출향·전출·전적」 글자 검색 후 문장 단위로 확인"
SCOPE6 = "찾은 범위: 6차 섹션 글(해당 문서의 모든 섹션 본문)에서 같은 글자 검색"
REBUT_B = ("15차 검증(verify15_gov_g2.py): 더 넓은 검색어(겸·파견·출향·전출·전적·전입·전보·인사교류·인력·인원·「N명」)로 다시 찾아도 "
           "겸직·파견 등을 말하는 조직·인력 서술 없음(인원 숫자만 있는 표는 키워드 문장이 아님)")

# JB FY2019 — PDF 글꼴 대응 깨짐: 쪽 이미지를 보고 옮겨 적은 칸(판단)
JB19 = []
for p, nm, txt, cc, ct in (
        (62, "최정수", "3) 현재 겸직 업무 법무법인 세줄 대표변호사\n전북은행(자회사) 사외이사", "법무법인 세줄", "대표변호사"),
        (62, "최정수", "3) 현재 겸직 업무 법무법인 세줄 대표변호사\n전북은행(자회사) 사외이사", "전북은행", "사외이사(자회사)"),
        (65, "김상국", "3) 현재 겸직 업무 광주은행(자회사) 사외이사", "광주은행", "사외이사(자회사)"),
        (68, "유관우", "3) 현재 겸직 업무 김·장 법률사무소 고문(現)", "김·장 법률사무소", "고문"),
        (74, "이상복", "3) 현재 겸직 업무 동아회계법인 파트너(現)", "동아회계법인", "파트너")):
    JB19.append(dict(p=p, person=nm, text=txt, cc=cc, ct=ct))
# 판독 표지(15차 검증 verify15_gov_g2.py 가 이 글이 note 에 있는지 봄)
PANDOK = "판독(PDF 글자층 깨짐 — 쪽 그림을 보고 옮김)"
# 같은 사람·같은 겸직처가 다른 쪽에도 있음(15차 검증 때 글자층 「?직」 꼴로 찾아 쪽 그림으로 확인)
JB19_MORE = {
    ("최정수", "전북은행"): "같은 겸직이 p.20 사외이사 소개 「- 전북은행 사외이사 겸직」, p.136 충실성 문단 「(자회사등은 제외/現 전북은행 사외이사 겸직)」에도 있음(판독)",
    ("김상국", "광주은행"): "같은 겸직이 p.20 사외이사 소개 「- 광주은행 사외이사 겸직」, p.138 충실성 문단 「(자회사등은 제외/現 광주은행 사외이사 겸직)」에도 있음(판독)",
}
# p.187 위험관리위원회 연혁 서술 — FY2020~2025 보고서의 「지주회사 및 은행자회사 리스크관리책임자(CRO) 겸직에 따라」와 같은 글(15차 검증에서 찾아 판독)
JB19_CRO = dict(p=187, lay=r"위험관리책임자\(C\S?O\)\s*\S직에",
                text="2016년 지주회사\n및 은행자회사 위험관리책임자(CRO) 겸직에 따라 리스크관리협의회의 원활한 회의진행을 위\n"
                     "하여 은행자회사 리스크관리부장을 동 협의회 위원으로 보강하는 리스크관리협의회규정 개정\n"
                     "을 2016년 2월 개최된 2016년도 제2차 위험관리위원회에서 결의하였으며,")
# p.23~24 퇴임 이사 소개 「(카) 사외이사 이광철 : 2019. 3. 23 퇴임」의 「- 재임기간」 값(15차 검증에서 찾아 판독). 「ㆍ」는 글자층 그대로(그림에서는 가운뎃점)
JB19_LEE = dict(p=24, lay=r"직\s*2014\.\s*03\.\s*19\)", person="이광철",
                text="ㆍ2018. 03. 23(JB우리캐피탈 겸직 2014. 03. 19) ~ 2019. 03. 39.")
JB19_NOTE = ("(판단) 이 PDF 는 글꼴 글자 대응이 깨져 추출 글이 원문과 다름(예: 「현재 t직 업무」, 「겸」 글자 0회, 쪽마다 다른 글자로 깨짐) — "
             "source_text 는 쪽 그림(pymupdf 110~200dpi)을 눈으로 보고 옮겨 적은 것(줄바꿈은 그림의 줄 끝, 표 칸 사이는 공백·줄바꿈으로 둠). "
             "15차 검증에서 쪽 그림과 다시 맞대 확인")
JB19_SCOPE = ("같은 문서의 다른 겸직 서술: 글자층에서 「겸」 자리에 깨진 글자가 오는 「?직」 꼴을 찾아 쪽 그림으로 본 것 — "
              "p.20·p.136·p.138(위 후보와 같은 겸직), p.24 이광철 재임기간 「JB우리캐피탈 겸직」(따로 행), p.187 CRO 겸직(따로 행),p.14·p.30·p.127 감사위원의 위험관리위원회 겸직 제한·금지(위원회끼리), "
              "p.55 법 「제10조(겸직제한)」 칸(p.88·p.90·p.92 는 글자층 꼴만 보고 같은 칸으로 봄), "
              "p.286 위원회 구성 조문(자회사 상근임원을 겸직하는 이사 제외) — 그 밖은 글자 깨짐으로 다 확인하지 못함(312쪽 전부를 그림으로 읽지는 않음)")


# ───────────────────────────── 만들기 ─────────────────────────────
def page_label(D, k, p, r=None):
    if k.startswith("M:"):
        return "p.%s" % p
    # 섹션 제목에 섞인 제어문자(U+0000 등)는 지움(15차 검증 — CSV 칸에 NUL 이 들어가던 것 고침)
    return "시작페이지 %s 섹션 안(「%s」, chunk %s)" % (r["시작페이지"], re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f]", " ", r["섹션제목_원문"])).strip(), r["chunk_seq"])


def base_note(D, k):
    n = []
    if k.startswith("S:"):
        n.append(N6)
    if k in SAME:
        n.append(SAME[k])
    return n


def build():
    D = Docs()
    rowsA, rowsB, secs = [], [], {}

    def keep_sec(kind, k, p, label, text):
        m = D.meta[k]
        key = (kind, m["co"], m["fy"], k, label)
        if key not in secs:
            secs[key] = (label, text, str(p))

    ERR = []
    for s in A_SPEC:
        k, m = s["d"], D.meta[s["d"]]
        try:
            src, t, row = extract(D, k, s["p"], s["a"], s["start"], s["end"])
        except ValueError as e:
            ERR.append("A " + str(e)); continue
        if s.get("_pre"):
            mm = re.search(flex(s["start"]), t)
            j = t.rfind(s["_pre"], 0, mm.start())
            src = _extract(t, k, s["p"], None, s["_pre"], s["end"]) if j >= 0 else src
        note = [s.get("note", "")] + base_note(D, k)
        rowsA.append(dict(corp_label=m["co"], fy=m["fy"], person=s.get("person", ""), birth_ym=s.get("birth_ym", ""),
                          holdco_title=s.get("holdco_title", ""), holdco_duty="", registered="", fulltime="",
                          concurrent_company=s.get("concurrent_company", ""), concurrent_title=s.get("concurrent_title", ""),
                          concurrent_since=s.get("concurrent_since", ""), reason_text=NONE, doc_kind=DOCKIND, source_text=src,
                          rcept_no_or_url=m["url"], page=page_label(D, k, s["p"], row),
                          note=" / ".join(x for x in note if x) + " / reason_text: " + NOR,
                          doc_name=m["name"], collected_at=m["collected"]))
        keep_sec("A", k, s["p"], page_label(D, k, s["p"], row), t)
    # JB FY2019
    kj = "M:JB금융지주:2020:본공시"
    mj = D.meta[kj]
    for r in JB19:
        more = JB19_MORE.get((r["person"], r["cc"]))
        rowsA.append(dict(corp_label=mj["co"], fy=mj["fy"], person=r["person"], birth_ym="", holdco_title="사외이사 후보", holdco_duty="",
                          registered="", fulltime="", concurrent_company=r["cc"], concurrent_title=r["ct"], concurrent_since="",
                          reason_text=NONE, doc_kind=DOCKIND, source_text=r["text"], rcept_no_or_url=mj["url"], page="p.%d" % r["p"],
                          note=PANDOK + " / " + JB19_NOTE + ". 성명은 추출 글에서 읽히는 「%s 사외이사 후보자는 …」 문단. " % r["person"] + CAND +
                               (" / " + more if more else "") +
                               " / " + JB19_SCOPE + "(p.59 김대곤·p.71 표현명 후보 칸은 「해당사항 없음」) / reason_text: " + NOR,
                          doc_name=mj["name"], collected_at=mj["collected"]))
        keep_sec("A", kj, r["p"], "p.%d" % r["p"], D.page(kj, r["p"]))
    c = JB19_LEE
    if not re.search(c["lay"], D.page(kj, c["p"])):
        ERR.append("A JB FY2019 p.%d 글자층에 재임기간 겸직 자리 없음" % c["p"])
    rowsA.append(dict(corp_label=mj["co"], fy=mj["fy"], person=c["person"], birth_ym="", holdco_title="사외이사(2019. 3. 23 퇴임)", holdco_duty="",
                      registered="", fulltime="", concurrent_company="JB우리캐피탈", concurrent_title="", concurrent_since="",
                      reason_text=NONE, doc_kind=DOCKIND, source_text=c["text"], rcept_no_or_url=mj["url"], page="p.%d" % c["p"],
                      note=PANDOK + " / " + JB19_NOTE + " / 이사 소개 「(카) 사외이사 이광철 : 2019. 3. 23 퇴임」(p.23, 판독)의 「- 재임기간」 값(p.24 첫 줄). "
                           "성명은 p.23 머리글에서 읽음(판단). 겸직 직위는 글에 없음. 괄호 안 「2014. 03. 19」가 겸직 시작일인지 글만으로 가릴 수 없어 "
                           "concurrent_since 를 비움(판단). 「2019. 03. 39.」는 그림 그대로 / " + JB19_SCOPE + " / reason_text: " + NOR,
                      doc_name=mj["name"], collected_at=mj["collected"]))
    keep_sec("A", kj, c["p"], "p.%d" % c["p"], D.page(kj, c["p"]))
    c = JB19_CRO
    if not re.search(c["lay"], D.page(kj, c["p"])):
        ERR.append("A JB FY2019 p.%d 글자층에 CRO 겸직 자리 없음" % c["p"])
    rowsA.append(dict(corp_label=mj["co"], fy=mj["fy"], person="", birth_ym="", holdco_title="위험관리책임자(CRO)", holdco_duty="",
                      registered="", fulltime="", concurrent_company="은행자회사", concurrent_title="위험관리책임자(CRO)", concurrent_since="",
                      reason_text=NONE, doc_kind=DOCKIND, source_text=c["text"], rcept_no_or_url=mj["url"], page="p.%d" % c["p"],
                      note=PANDOK + " / " + JB19_NOTE + " / 위험관리위원회 연혁 서술(2016년 2월 2016년도 제2차 위험관리위원회) — 성명 없음 / "
                           + JB19_SCOPE + " / reason_text: " + NOR,
                      doc_name=mj["name"], collected_at=mj["collected"]))
    rowsB.append(dict(corp_label=mj["co"], fy=mj["fy"], employees_total="", regular="", contract="", keyword="겸직",
                      source_text=c["text"], doc_kind=DOCKIND, rcept_no_or_url=mj["url"], page="p.%d" % c["p"],
                      note=PANDOK + " / " + JB19_NOTE + " / 위험관리위원회 연혁 서술(리스크관리협의회 구성 보강) / "
                           "15차 검증에서 「확인 불가」 행을 이 행으로 바꿈 — " + JB19_SCOPE.replace("같은 문서의 다른 겸직 서술", "찾은 범위")
                           + "; 파견·출향·전출·전적·겸무는 글자가 쪽마다 다르게 깨져 글자 검색으로 가릴 수 없음",
                      doc_name=mj["name"], collected_at=mj["collected"]))
    keep_sec("A", kj, c["p"], "p.%d" % c["p"], D.page(kj, c["p"]))
    keep_sec("B", kj, c["p"], "p.%d" % c["p"], D.page(kj, c["p"]))
    for s in B_SPEC:
        k, m = s["d"], D.meta[s["d"]]
        try:
            src, t, row = extract(D, k, s["p"], s["a"], s["start"], s["end"])
        except ValueError as e:
            ERR.append("B " + str(e)); continue
        note = [s.get("note", "")] + base_note(D, k)
        rowsB.append(dict(corp_label=m["co"], fy=m["fy"], employees_total="", regular="", contract="", keyword=s["kw"],
                          source_text=src, doc_kind=DOCKIND, rcept_no_or_url=m["url"], page=page_label(D, k, s["p"], row),
                          note=" / ".join(x for x in note if x), doc_name=m["name"], collected_at=m["collected"]))
        keep_sec("B", k, s["p"], page_label(D, k, s["p"], row), t)

    if ERR:
        print("\n".join(ERR)); raise SystemExit("닻 오류 %d" % len(ERR))
    # 문서마다 빠짐 행
    docsA = {r["fy"] for r in rowsA}
    allk = sorted(D.meta)
    for k in allk:
        m = D.meta[k]
        sc = SCOPE6 if k.startswith("S:") else SCOPE
        same_as = None
        for kk, v in SAME.items():
            if kk.split(":")[1:3] == k.split(":")[1:3] and kk != k and m["kind"] in v:
                same_as = kk
        if same_as:
            continue   # 같은 글 — 본공시 행에 note 로 적음
        # (JB FY2019 「확인 불가」 행은 15차 검증에서 p.187 판독 행으로 바꿈 — 위 JB19_CRO)
        if not any(r["doc_name"] == m["name"] for r in rowsB):
            if k.startswith("S:") and k in ("S:JB금융지주:2026:본공시",):
                continue
            if k.startswith("S:"):
                sp = sorted({int(st) for st, _ch in D.sec[k]})
                pg = "6차 섹션 글 전체(찾은 범위, 시작페이지 %s — 해당 글 없음)" % (
                    str(sp[0]) if sp[0] == sp[-1] else "%d~%d" % (sp[0], sp[-1]))
            else:
                pg = "p.1~p.%s 전체(찾은 범위, PDF 쪽 — 해당 글 없음)" % m["pdfpages"]
            rowsB.append(dict(corp_label=m["co"], fy=m["fy"], employees_total="", regular="", contract="", keyword="없음",
                              source_text=NONE, doc_kind=DOCKIND, rcept_no_or_url=m["url"], page=pg,
                              note=sc + " — 조직·인력 서술에 해당하는 키워드 문장 없음" + (" / " + N6 if k.startswith("S:") else "")
                                   + " / " + REBUT_B,
                              doc_name=m["name"], collected_at=m["collected"]))
    return D, rowsA, rowsB, secs


def write(D, rowsA, rowsB, secs):
    for path, cols, rows in ((OUT_A, COLS_A, rowsA), (OUT_B, COLS_B, rowsB)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rows.sort(key=lambda r: (r["corp_label"], int(r["fy"]), r["doc_name"], r.get("page", "")))
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    # 원문 md
    byfile = {}
    for (kind, co, fy, k, _lab), (label, text, p) in secs.items():
        byfile.setdefault((kind, co, fy), []).append((k, p, label, text))
    for (kind, co, fy), items in byfile.items():
        d = RAW_A if kind == "A" else RAW_B
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "%s__FY%d__연차보고서.md" % (co, fy))
        out = ["# %s FY%d 지배구조 및 보수체계 연차보고서 — 작업 %s 원문" % (co, fy, kind), "",
               "source_text 가 나온 자리의 글 전체를 그대로 옮김. 새로 받은 PDF(FY2019~2023)는 그 쪽(PDF 쪽 번호) 글 전체, "
               "6차 섹션 글(FY2024·2025)은 그 섹션(chunk) 본문 전체. 글자는 추출 그대로(줄 끝 공백과 PDF 추출 글에 섞인 제어문자 U+0001 등만 지움).", ""]
        for k, p, label, text in sorted(items, key=lambda x: (x[0], int(str(x[1]).split("/")[0]), str(x[1]))):
            m = D.meta[k]
            out.append("## %s — %s" % (m["name"], label))
            out.append("")
            out.append("- 출처: %s · 문서: %s · 위치: %s · 수집: %s" % (m["url"], m["name"], label, m["collected"]))
            if k.startswith("S:"):
                out.append("- %s (6차 파일 %s)" % (N6, m.get("file", "")))
            if k == "M:JB금융지주:2020:본공시":
                out.append("- 주의: 이 PDF 는 글꼴 글자 대응이 깨져 아래 추출 글이 원문과 다름. 이 쪽에서 나온 A·B 행 source_text 는 쪽 그림을 보고 옮겨 적음"
                           "(note 「" + PANDOK + "」).")
            out.append("")
            out.append("```text")
            out.append(clean(text))
            out.append("```")
            out.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))


if __name__ == "__main__":
    D, ra, rb, secs = build()
    write(D, ra, rb, secs)
    print("A", len(ra), "B", len(rb), "secs", len(secs))
