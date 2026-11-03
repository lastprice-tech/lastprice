# -*- coding: utf-8 -*-
"""15차 검증 — 사업보고서 조각 g2(NH농협금융지주·메리츠금융지주·iM금융지주): A_bs_g2.csv·B_bs_g2.csv·D_bs_g2.csv.

    python3 scripts/dart/verify15_bs_g2.py      # 인자 없음 → exit 0(통과)/1(실패), 결과 dart_out/ops15/verify15_bs_g2.txt

생성기(scripts/dart/ops15_bs_g2.py)의 함수는 쓰지 않고 원문을 따로 읽어 대조한다(웹 요청·API 키 사용 없음).
  (a) 모든 행 source_text(그리고 reason_text 가 「문서에 없음」이 아니면 그것도)가 그 행 출처 원문에 글자 그대로 있는지
      — 공백·줄바꿈·「|」만 무시(md 의 칸 안 줄바꿈 표시 <br>·&cr; 도 줄바꿈으로 보아 무시).
      출처 원문: 사업보고서 = 사업보고서_원문.csv 의 text_path md(OpenDART XML 옮김),
                 경영공시 2026.2Q = 13차 텍스트 zip 의 경영공시__<회사>.md(「## p.N」).
  (b) page 가 실제 그 글이 있는 위치인지: 「XML [절 n] 「제목」 [표 m]」 → 그 절 머리·제목이 맞고 글이 그 표(또는 절 문단) 안에 있음,
      「p.N(본문 PDF, 13차 보관)」 → 13차 사업보고서 PDF 텍스트 그 쪽에 같은 글, 경영공시 「p.N」 → 그 쪽.
      「문서에 없음」 행은 page 에 찾은 범위(절 번호·쪽 범위)가 실제 문서 범위와 맞는지.
  (c) 열 이름(COMMON15 순서 그대로)·utf-8-sig·필수 칸(corp_label·fy·doc_kind·source_text·rcept_no_or_url·page·doc_name·
      collected_at, A 는 reason_text, B 는 keyword) 빈칸 0, doc_name·collected_at·fy·회사가 출처 목록과 같음.
  (d) 키·비밀값 문자열 없음(DART_API_KEY 값은 환경변수에서 읽어 들어 있는지만 보고 값은 어디에도 쓰지 않음).
  더해서(g1 과 같은 표본 대조):
  (e) 회사×FY(2019~2025) 마다 A·B·D 각 1행 이상.
  (f) B 숫자 칸(employees_total·regular·contract) = 원문 직원 표 합계 행 숫자이고 source_text 또는 note 의 「합계 행」 인용 안 숫자;
      합계 = 정함없음 + 기간제.
  (g) 회사마다 2개 FY 를 골라 겸직 표 모든 행이 A 에 있는지 대조(겸직 표는 이 스크립트가 따로 찾음).
  (h) 출생년월 맞춤 표본 20행(+ 전수 자동 대조): 임원 현황 표의 같은 성명 행 출생년월과 같은지, 동명이인 표시.
  (i) 「문서에 없음」 반박 시도: 더 넓은 검색어(공백 무시)로 같은 범위를 다시 찾음 — 결과는 txt 에(판단은 사람이 읽고 적음).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
csv.field_size_limit(10 ** 9)

FRAG = os.path.join("dart_out", "ops15", "조각")
OUTTXT = os.path.join("dart_out", "ops15", "verify15_bs_g2.txt")
LIST_CSV = os.path.join("dart_out", "ops15", "사업보고서_원문.csv")
T13_ZIP = os.path.join("handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
MGMT_CSV = os.path.join("dart_out", "risk8", "경영공시_2026_2Q.csv")
WORK_JSON = os.path.join(FRAG, "bs_g2_work.json")
GEN = os.path.join("scripts", "dart", "ops15_bs_g2.py")
CORPS = ["NH농협금융지주", "메리츠금융지주", "iM금융지주"]
SELF = {"NH농협금융지주": ["농협금융지주"], "메리츠금융지주": ["메리츠금융지주"], "iM금융지주": ["iM금융지주", "DGB금융지주"]}
NONE = "문서에 없음"
KST = timezone(timedelta(hours=9))

COLS = {
    "A": ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "D": ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
}
REQ = {"A": ["reason_text"], "B": ["keyword"], "D": []}
REQ_ALL = ["corp_label", "fy", "doc_kind", "source_text", "rcept_no_or_url", "page", "doc_name", "collected_at"]

OUT = []
FAIL = []

# 검증하면서 고친 곳·반박 결과·손 대조(사람이 원문을 읽고 적은 것). 숫자는 위 자동 대조가 다시 셈.
REVIEW = [
    "### 고친 곳(생성기 scripts/dart/ops15_bs_g2.py 에 넣고 다시 돌림 — 고치기 전 조각 md5 A 0ddac06c… B 206e32fd… D dccc45e1…, "
    "고친 뒤 두 번 돌려 같은 md5)",
    "- (c) 「문서에 없음」 19행 page 빈칸 → 찾은 범위로 채움: D 사업보고서 14행 「XML [절 a]~[절 b] 「X. …」~「(Ⅺ 끝 절)」 전체(찾은 범위 — 해당 글 없음)」"
    "(range_page), B 2행·D 3행 경영공시 「p.1~p.N 전체(찾은 범위, PDF 쪽 — 해당 글 없음)」(mg_range). 바뀐 칸은 page 뿐.",
    "- (h) A 2행(NH농협금융지주 FY2021 김용기 1960.07, 줄 62·63 — 주요경력 칸 행): 같은 보고서 임원 표에 같은 성명 김용기 1965.08(부사장, "
    "작성기준일 이후 표)이 있어 note 에 「같은 성명이 … 출생년월 1960.07·1965.08 로 나옴 — 이 행은 출생년월 1960.07 인 임원 표 행의 칸에서 나옴"
    "(출생년월로 구분)」을 더함. 각주 행에도 같은 규칙(해당 행 없음). birth_ym 등 다른 칸은 그대로(맞았음).",
    "- (i) D 5행 note 에 Ⅹ 장 계열사 거래 표의 거래 종류 칸 원문을 (판단) 표시로 더함: 메리츠 FY2019 「수수료수익」[표 964]·FY2020 「수수료수익」[표 1005]"
    "(문서에 없음 행), FY2021 「브랜드사용료」[표 1112]·FY2022 [표 1118](용역비 소송 행), FY2023 「브랜드사용료」·「부동산임대차 등」[표 1103]"
    "(문서에 없음 행). 행으로는 넣지 않음(요청 낱말 업무위탁·용역·경영자문·전산 공동사용이 아님).",
    "### 「문서에 없음」 반박 시도 결과",
    "- D 17행: 반박된 행 없음. 넓은 검색어와 계열·자회사 낱말이 같은 줄은 지주 목적 서술(「…지배 내지 경영관리를 주목적으로…」·「…경영관리업무와 "
    "이에 부수하는…」), 계열사 지분 매각·유상감자(메리츠 FY2019 메리츠금융서비스), 고객정보 조회 시스템·「IT보안규칙」 내규 이름(NH FY2020), "
    "온실가스 보고범위 서술(iM FY2025)뿐 — 계약·거래 뜻이 아님(처음엔 「약정」「공동」도 넣어 보았으나 대출·인수 약정, 공동기업·공동피고만 걸려 뺌). 단 메리츠 FY2023 Ⅹ 「나. 지주회사와 종속기업간 거래」 표의 "
    "「메리츠증권 (자회사) | 부동산임대차 등 | 3,916」 과 브랜드사용료 행은 지주–자회사 거래이므로 메인이 범위에 넣을지 정할 것(note 에 원문 낱말 적어 둠).",
    "- B 2행(NH·메리츠 2026.2Q 경영공시): 공백 무시 넓은 검색어(겸직·파견·출향·전출·전적·겸무·겸임·겸업·인사교류·인력교류·전보·지원인력) — "
    "NH 는 「차감전 보통주자본/보완자본」 속 「전보」·「완전적용」 속 「전적」(빼 둠)과 p.88 「…2.전 보고기간 이후 발생한…」 속 「전보」 1곳뿐(모두 오탐), "
    "메리츠 0 → 유지.",
    "- B keyword 「없음」 6행(메리츠 FY2019~2022·2024·2025): Ⅷ 전체 공백 무시 넓은 검색어 0 → 유지. 공백·칸 줄바꿈 때문에 놓친 키워드 줄도 세 회사 0.",
    "- A reason_text 353행: 사업보고서 32개(본·정정) 전체에서 걸린 줄은 NH FY2019~2024 「IV. 이사의 경영진단 및 분석의견」·FY2025 "
    "「6. 그 밖에 투자의사결정에 필요한 사항」의 법령 개정 서술 "
    "「…시행령은 2017년 9월 개정, 2017년 12월 시행으로 임원 겸직 승인 및 보고 범위를 확대하고 …」 7줄뿐 — 특정 겸직의 사유 글이 아님 → 유지"
    "(연차보고서 쪽 사유는 gov 조각 몫).",
    "### 손 대조(g1 과 같은 표본)",
    "- (g) 겸직 표 전수: NH FY2019 [표 1193] 11행·FY2023 [표 1310] 8행, 메리츠 FY2021 [표 1105] 5행(칸 합침 한정원 메리츠증권 행 포함)·FY2024 [표 1102] 13행, "
    "iM FY2020 표 6개 46행·FY2025 표 6개 30행 — 원문 md 를 직접 열어 행마다 A 를 찾음: 빠진 행 0. iM 「DGB금융그룹 임원 겸직현황」[표 847] 의 "
    "「(주)DGB금융지주 | 상 무」 같은 지주 자기 직위 줄 14개는 생성기 판단대로 행이 아니고 그 아래 「(주)대구은행 | 상 무」 등 칸 합침 행은 이름 줄과 함께 A 에 있음.",
    "- (h) 출생년월 표본 20행(seed 1502) 모두 임원 현황 표 같은 성명 행의 출생년월 칸 원문과 같고, 지주 직위·담당업무·등기·상근 칸도 같은 행과 같음. "
    "같은 성명 출생년월 둘 이상 4행: iM FY2020 최태곤(기준일 표 1965년 01월 / 이후 표 1963년 01월 — 생성기 note 에 (판단)·동일인 여부 안 가림), "
    "NH FY2021 김용기 2행(위 고친 곳).",
    "- (f) B 숫자: 사업보고서 101행 모두 원문 직원 표 합계 행 칸과 같고 합계 = 기간의 정함이 없는 근로자 + 기간제; 9차 값(FY2023~2025)과도 같음.",
    "### 15차 wave6 고침(2026-11-03)",
    "- A NH 35행(임원 현황 표에 같은 성명 없는 겸직 표 행): fulltime 은 겸직 표 비고/상근여부 칸 원문 값(비상근), registered 「문서에 없음」(note 에 찾은 범위).",
    "- A 회사·직위 나누기 고침 6행: 이종백 「서울고등검찰청장 김앤장법률사무소」/「변호사」→「김앤장법률사무소」/「변호사」(앞 낱말은 두 칸에서 뺌), 이순호 「한국금융연구원」/「은행보험연구&cr;2실장」, "
    "이윤석 「금융정보분석원」/「자금세탁방지 정책자문위원」, 메리츠 김종민 「메리츠증권」/「대표이사 부사장·사장」, 서수동 「메리츠화재」/「ESG경영실장 부사장」.",
    "- A 칸 합침 행: source_text 를 이름 줄부터 그 행까지 사이 줄 포함해 이어서(g2 는 모두 붙은 줄이라 글은 그대로, note 만 고침).",
    "- B 임원 현황 표 행 6행(NH 5·iM 1) note 에 「(위치) 임원 현황 표 — 작업 A 와 겹침」.",
    "- D 검색어를 「위탁」으로 넓힘: 메리츠 FY2024·2025 Ⅺ 개인정보 글 2행(「…금융회사에 그 관리를 위탁한 것…」). NH 「개인정보처리 위탁업체 관리 준칙」은 내규 이름이라 넣지 않고 note 에.",
    "- D 메리츠 Ⅹ 지주–자회사 거래 표(수수료수익·브랜드사용료·부동산임대차 등)는 행이 아니고 note 에 절·표·md 줄과 그 표 행 원문(병합 칸이면 거래상대방 칸 윗줄부터) 그대로.",
    '- (15차 wave6, 2026-11-03) 새 원문 대조 규칙 점검 블록 「(wave6)」을 더함: source_text·reason_text 가 출처 한 곳에서 이어진 글인지(공백·줄바꿈만 지움, XML md 는 「|」「<br>」도 — &cr; 은 글자), page 가 이어진 글의 첫 줄·끝 줄 절·표와 맞는지(「(문단)~[표 m]」 범위 꼴 포함), A registered·fulltime 빈칸 0·「문서에 없음」이면 찾은 범위, 회사·직위 두 칸이 source_text 의 이어진 부분 글인지와 나누기 꼴(법인 종류 낱말뿐인 회사·회사 끝/앞 직함·부서 이름에서 끊김), 정정판 사이 같은 행, B keyword 6개·「없음」만·임원 현황 표 행 note, D 묶음 note·「글자까지 같은 글」 위치, 「위탁」 넓혀 넣은 행 꼴과 덮임, Ⅹ 거래 표 위치 인용(md 줄 글 그대로). 커밋된 이전 조각에 이 블록을 돌리면 g1 309·g2 85·g3 148건 실패(fulltime/registered 빈칸, 줄 이음 98, 묶음 15, 임원 현황 표 note 39, 정정판 중복 3, 「위탁」 누락 후보 등) — 검사력 확인.',
    '- (15차 wave6) 이전 lines 모드(줄마다 따로 있으면 통과)는 없앰 — 여러 줄 source_text 도 md 에서 이어서 있어야 함.',
]


def say(s=""):
    OUT.append(s)


def fail(s):
    FAIL.append(s)
    OUT.append("  [실패] " + s)


# ================================================================ 정규화
def vnorm(t):
    """대조용: 공백·줄바꿈·「|」(그리고 md 의 칸 안 줄바꿈 표시 <br>·&cr;)만 지운 글."""
    t = (t or "").replace("<br>", "").replace("&cr;", "").replace("\ufeff", "")
    return re.sub(r"[\s|\u00a0\u3000]+", "", t)


def pkey(t):
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    t = re.sub(r"\(.*?\)", "", t)
    return re.sub(r"\s+", "", t)


def ckey(t):
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    t = re.sub(r"\(주\)|㈜|주식회사|\(비상장\)|\(상장\)", "", t)
    return re.sub(r"[\s·ㆍ]+", "", t)


def cellv(t):
    return re.sub(r"(<br>|&cr;)", " ", t or "").strip()


def bkey(b):
    b = (b or "").strip()
    m = re.search(r"(\d{4})\D+(\d{1,2})", b)
    if m:
        return "%s.%02d" % (m.group(1), int(m.group(2)))
    m = re.search(r"'(\d{2})\.(\d{1,2})", b)
    if m:
        return "19%s.%02d" % (m.group(1), int(m.group(2)))
    return b


# ================================================================ 원문 읽기
class MD:
    def __init__(self, path):
        self.path = path
        self.L = open(path, encoding="utf-8").read().split("\n")
        self.heads = []
        for i, l in enumerate(self.L):
            m = re.match(r"### \[절 (\d+)\] (.*)$", l)
            if m:
                self.heads.append((i, int(m.group(1)), m.group(2).strip()))
        self.tabs = {}
        cur = None
        for i, l in enumerate(self.L):
            m = re.match(r"\[표 (\d+)\]$", l)
            if m:
                cur = [int(m.group(1)), i]
            elif l == "[표 끝]" and cur:
                self.tabs[cur[0]] = (cur[1], i)
                cur = None
        self.vl = [vnorm(l) for l in self.L]
        self.vall = "".join(self.vl)

    def sec(self, n):
        for k, (i, nn, t) in enumerate(self.heads):
            if nn == n:
                e = self.heads[k + 1][0] if k + 1 < len(self.heads) else len(self.L)
                return i, e, t
        return None

    def chap(self, roman):
        """로마 숫자 장(VIII 등) 범위: 그 장 머리부터 다음 로마 장 또는 【 머리 전까지."""
        R = {"VIII": r"(VIII|Ⅷ)\.", "IX": r"(IX|Ⅸ)\.", "X": r"(X|Ⅹ)\.", "XI": r"(XI|Ⅺ)\.", "XII": r"(XII|Ⅻ)\."}
        s = next((i for i, n, t in self.heads if re.match(R[roman], t)), None)
        if s is None:
            return None
        e = next((i for i, n, t in self.heads if i > s and (re.match(r"(VIII|IX|XII|XI|X|Ⅷ|Ⅸ|Ⅹ|Ⅺ|Ⅻ)\.", t) or t.startswith("【"))
                  and not re.match(R[roman], t)), len(self.L))
        return s, e

    def chap_x_xi(self):
        """작업 D 범위: Ⅹ 머리부터 Ⅻ 또는 【 머리 전까지(Ⅹ·Ⅺ)."""
        x = self.chap("X")
        if x is None:
            return None
        e = next((i for i, n, t in self.heads if i > x[0] and (re.match(r"(XII|Ⅻ)\.", t) or t.startswith("【"))), len(self.L))
        return x[0], e

    def find_lines(self, txt, a=0, b=None):
        """txt(vnorm)가 줄 a..b 범위 이어 붙인 글 안에 있는지. → (있음, 시작 줄)"""
        b = len(self.L) if b is None else b
        v = vnorm(txt)
        if not v:
            return False, None
        joined, starts = "", []
        for i in range(a, b):
            starts.append((len(joined), i))
            joined += self.vl[i]
        p = joined.find(v)
        if p < 0:
            return False, None
        line = max(i for off, i in starts if off <= p)
        return True, line


_T13 = {}


def t13(kind, corp):
    if (kind, corp) not in _T13:
        z = zipfile.ZipFile(T13_ZIP)
        n = next(x for x in z.namelist() if x.endswith("텍스트/%s__%s.md" % (kind, corp)))
        t = z.read(n).decode("utf-8")
        pages, cur, head = {}, None, ""
        for l in t.split("\n"):
            m = re.match(r"## p\.(\d+)", l)
            if m:
                cur = int(m.group(1))
                pages[cur] = []
            elif cur is not None:
                pages[cur].append(l)
            elif l.startswith("- 원본:"):
                head = l
        _T13[(kind, corp)] = dict(pages=pages, v={p: vnorm("".join(ls)) for p, ls in pages.items()}, head=head)
    return _T13[(kind, corp)]


def kst(s):
    if s and (s.endswith("+00:00") or s.endswith("Z")):
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(KST).isoformat(timespec="seconds")
    return s


# ================================================================ 표 찾기(생성기와 따로)
def exec_rows(md, rng):
    """임원 현황 표(머리 성명|성별|출생년월…) 행: [(줄, 성명칸, 칸들, 표번호)]."""
    out = []
    for no, (s, e) in sorted(md.tabs.items(), key=lambda x: x[1][0]):
        if not (rng[0] <= s < rng[1]):
            continue
        rows = [(i, [c.strip() for c in md.L[i].strip()[1:-1].split("|")]) for i in range(s + 1, e) if md.L[i].startswith("|")]
        if not rows:
            continue
        h = [vnorm(c) for c in rows[0][1]]
        if not (len(h) > 7 and h[0] == "성명" and h[1] == "성별" and "출생" in h[2]):
            continue
        for i, c in rows[1:]:
            if len(c) >= 8 and not vnorm(c[0]).startswith("의결권"):
                out.append((i, c[0], c, no))
    return out


def conc_tables(md, rng):
    """겸직 표: 머리 줄에 「대상 계열사·대상 회사·겸직 대상자·겸직회사」 등이 든 표 → [(표번호, 머리, [(줄, 칸들)])]."""
    out = []
    for no, (s, e) in sorted(md.tabs.items(), key=lambda x: x[1][0]):
        if not (rng[0] <= s < rng[1]):
            continue
        rows = [(i, [c.strip() for c in md.L[i].strip()[1:-1].split("|")]) for i in range(s + 1, e) if md.L[i].startswith("|")]
        if len(rows) < 2:
            continue
        h = vnorm("".join(rows[0][1]))
        if re.search(r"대상계열|대상회사|겸직대상|겸직회사|계열회사겸직|겸직내역|겸임회사", h) and ("성명" in h or "겸직대상자" in h):
            out.append((no, rows[0][1], rows[1:]))
    return out


# ================================================================ 실행
# ================================================================ (15차 wave6) 새 원문 대조 규칙·고침 점검 — verify15_bs_g1·g2·g3 같은 블록
# 대조 규칙: source_text(와 「문서에 없음」이 아닌 reason_text)는 출처 텍스트의 한 곳에서 이어진 글이어야 함.
#   「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 텍스트」 안에 이어서 그대로 있는지로 봄.
#   OpenDART XML md 출처는 md 표지 「|」「<br>」도 양쪽에서 지움(&cr; 은 글자로 셈). 경영공시(13차 PDF 텍스트)는 「|」를 지우지 않음
#   (13차 텍스트의 쪽 머리 줄 「## p.N」은 출처 글이 아니라 뺌). 줄마다 따로 있는 것(떨어진 두 곳)은 실패.
import bisect as _w6_bisect

W6_LIST = os.path.join(ROOT, "dart_out", "ops15", "사업보고서_원문.csv")
W6_T13 = os.path.join(ROOT, "handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
W6_KW = ("겸직", "파견", "출향", "전출", "전적", "겸무")
W6_NONE = "문서에 없음"
W6_INFO = re.compile(r"(?:고객|개인|신용)\S{0,8}정보")
W6_AFF = re.compile(r"자회사|손자회사|그룹사|계열사|계열회사")
W6_NOISE = re.compile(r"위탁(?=\s?(?:자|관리|매매|증거금|계좌|투자중개|금\s?반환))")


def w6_xml(s):
    """OpenDART XML md 출처 대조 꼴: 공백·줄바꿈과 md 표지 「|」「<br>」만 지움."""
    return re.sub(r"\s+", "", (s or "").replace("<br>", "").replace("|", ""))


def w6_ws(s):
    """PDF·경영공시 출처 대조 꼴: 공백·줄바꿈만 지움(「|」는 남김)."""
    return re.sub(r"\s+", "", s or "")


class W6Doc:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            self.L = f.read().split("\n")
        self.off, parts, o = [], [], 0
        for l in self.L:
            self.off.append(o)
            t = w6_xml(l)
            parts.append(t)
            o += len(t)
        self.off.append(o)
        self.buf = "".join(parts)
        self.heads, self.tab_of, self.tabs, cur = [], [None] * len(self.L), {}, None
        for i, l in enumerate(self.L):
            if cur is None:
                m = re.match(r"### \[절 (\d+)\] ?(.*)$", l)
                if m:
                    self.heads.append((i, int(m.group(1)), m.group(2).strip()))
                    continue
                m = re.fullmatch(r"\[표 (\d+)\]", l)
                if m:
                    cur, s0 = int(m.group(1)), i
                continue
            if l == "[표 끝]":
                self.tabs[cur] = (s0, i)
                cur = None
                continue
            self.tab_of[i] = cur
        self.hidx = [h[0] for h in self.heads]

    def line_at(self, pos):
        return _w6_bisect.bisect_right(self.off, pos) - 1

    def head_at(self, i):
        k = _w6_bisect.bisect_right(self.hidx, i) - 1
        return self.heads[k] if k >= 0 else None

    def heads_at(self, i):
        """줄 i 의 절 머리 후보: 바로 앞 머리(제목 빈 것 포함)와 제목 있는 머리 — 생성기마다 빈 제목 절을 다르게 다룸."""
        k = _w6_bisect.bisect_right(self.hidx, i) - 1
        out = []
        if k >= 0:
            out.append(self.heads[k][1:])
        while k >= 0 and not self.heads[k][2]:
            k -= 1
        if k >= 0:
            out.append(self.heads[k][1:])
        return out

    def occ(self, needle):
        out, p = [], self.buf.find(needle) if needle else -1
        while p >= 0:
            out.append((p, p + len(needle)))
            p = self.buf.find(needle, p + 1)
        return out

    def chap(self, roman):
        R = {"VIII": r"(?:VIII|Ⅷ)\.", "X": r"(?:X|Ⅹ)\.", "XI": r"(?:XI|Ⅺ)\.", "XII": r"(?:XII|Ⅻ)\."}
        s = next((i for i, n, t in self.heads if re.match(R[roman], t)), None)
        if s is None:
            return None
        e = next((i for i, n, t in self.heads if i > s and (re.match(r"(?:VIII|IX|XII|XI|X|Ⅷ|Ⅸ|Ⅹ|Ⅺ|Ⅻ)\.", t) or t.startswith("【"))
                  and not re.match(R[roman], t)), len(self.L))
        return s, e


W6_PAGE = re.compile(r"XML \[절 (\d+)\] 「(.*?)」(?: (\(문단\)|\[표 (\d+)\]))?"
                     r"(?:~(?:\[절 (\d+)\] 「(.*?)」 )?(\(문단\)|\[표 (\d+)\]))?(?:; (p\.\d+(?:[,~]p\.\d+)*)\(본문 PDF, 13차 보관\))?$")


def wave6(data, say, fail, cos):
    """data = {"A": [행], "B": [행], "D": [행]} (조각 CSV dict). fail(글) 은 실패로 셈."""
    rep = {r["rcept_no"]: r for r in csv.DictReader(open(W6_LIST, encoding="utf-8-sig"))}
    docs = {}

    def doc(rc):
        if rc not in docs:
            m = rep.get(rc)
            docs[rc] = W6Doc(os.path.join(ROOT, m["text_path"])) if m and m.get("text_path") else None
        return docs[rc]

    mg = {}
    with zipfile.ZipFile(W6_T13) as z:
        for co in cos:
            nm = next((n for n in z.namelist() if n.endswith("/경영공시__%s.md" % co)), None)
            if nm:
                txt = z.read(nm).decode("utf-8")
                mg[co] = w6_ws("".join(l for l in txt.split("\n") if not re.match(r"## p\.\d+\s*$", l)))
    say("## (wave6) 새 원문 대조 규칙과 15차 wave6 고침 점검")
    say("- 규칙: source_text·reason_text(「문서에 없음」 아님)는 출처 한 곳에서 이어진 글 — 공백·줄바꿈만 지우고(XML md 는 「|」「<br>」도) 출처 글 안에 이어서 있어야 함. "
        "&cr; 은 글자로 셈. 줄마다 따로 있는 것·「 | 」「 … 」를 넣은 것은 실패.")
    n_ok = {"A": 0, "B": 0, "D": 0}
    n_all = {"A": 0, "B": 0, "D": 0}
    n_page = 0
    for T in "ABD":
        for k, r in enumerate(data[T], 2):
            tag = "%s 줄 %d(%s FY%s)" % (T, k, r["corp_label"], r["fy"])
            texts = [("source_text", r["source_text"])]
            if T == "A" and r.get("reason_text") and r["reason_text"] != W6_NONE:
                texts.append(("reason_text", r["reason_text"]))
            for col, tx in texts:
                if tx == W6_NONE:
                    continue
                n_all[T] += 1
                if re.search(r"[\x00-\x08\x0b-\x1f]", tx):
                    fail("%s %s 에 보이지 않는 제어문자가 있음" % (tag, col))
                ctrl = "제어문자 지움" in r["note"]      # 규칙: 보이지 않는 제어문자만은 지워도 됨(note 에 적음) — 그 행은 출처 쪽 제어문자도 빼고 대조
                if r["doc_kind"] == "경영공시":
                    buf = mg.get(r["corp_label"])
                    if buf is not None and ctrl:
                        buf = re.sub(r"[\x00-\x08\x0b-\x1f]", "", buf)
                    if buf is None or w6_ws(tx) not in buf:
                        fail("%s %s 이 13차 경영공시 텍스트에 이어서 그대로 없음(공백만 지움) 「%s」" % (tag, col, tx[:60]))
                    else:
                        n_ok[T] += 1
                    continue
                d = doc(r["rcept_no_or_url"])
                if d is None:
                    fail("%s 원문 md 없음 %s" % (tag, r["rcept_no_or_url"]))
                    continue
                oc = d.occ(w6_xml(tx))
                if not oc and ctrl:
                    oc = [(0, 0)] if w6_xml(tx) in re.sub(r"[\x00-\x08\x0b-\x1f]", "", d.buf) else []
                if not oc:
                    fail("%s %s 이 원문 md 에 이어서 그대로 없음(공백·「|」·<br> 만 지움) 「%s」" % (tag, col, tx[:60].replace("\n", "⏎")))
                    continue
                n_ok[T] += 1
                if col != "source_text":
                    continue
                # page ↔ 이어진 글의 첫 줄·끝 줄 위치
                m = W6_PAGE.match(r["page"])
                if not m:
                    fail("%s page 꼴 모름 「%s」" % (tag, r["page"][:80]))
                    continue
                n1, t1, p1, tb1, n2, t2, p2, tb2 = m.group(1, 2, 3, 4, 5, 6, 7, 8)
                good = False
                for s, e in oc:
                    ls, le = d.line_at(s), d.line_at(e - 1)
                    if (int(n1), t1) not in d.heads_at(ls):
                        continue
                    if p2 is None:
                        if tb1 is not None and not (d.tab_of[ls] == int(tb1) and d.tab_of[le] == int(tb1)):
                            continue
                        if tb1 is None and (d.tab_of[ls] is not None or d.tab_of[le] is not None):
                            continue
                    else:
                        if (tb1 is None) != (d.tab_of[ls] is None) or (tb1 is not None and d.tab_of[ls] != int(tb1)):
                            continue
                        if (tb2 is None) != (d.tab_of[le] is None) or (tb2 is not None and d.tab_of[le] != int(tb2)):
                            continue
                        if (int(n2 or n1), t2 if n2 else t1) not in d.heads_at(le):
                            continue
                    good = True
                    break
                if good:
                    n_page += 1
                else:
                    fail("%s page 「%s」 ≠ 이어진 글의 실제 위치" % (tag, r["page"][:80]))
    say("- 원문에 이어서 있음: A %d/%d · B %d/%d · D %d/%d · page(첫 줄·끝 줄 절·표) 맞음 %d"
        % (n_ok["A"], n_all["A"], n_ok["B"], n_all["B"], n_ok["D"], n_all["D"], n_page))

    # A: registered·fulltime 칸, 회사·직위 칸, 정정판 사이 같은 행
    A = data["A"]
    nreg = sum(1 for r in A if r["registered"] == W6_NONE)
    nft = sum(1 for r in A if r["fulltime"] == W6_NONE)
    for k, r in enumerate(A, 2):
        if r["source_text"] == W6_NONE:
            continue
        tag = "A 줄 %d(%s FY%s %s)" % (k, r["corp_label"], r["fy"], r["person"])
        for f in ("registered", "fulltime"):
            if not r[f].strip():
                fail("%s %s 빈칸" % (tag, f))
            elif r[f] == W6_NONE and "찾은 범위" not in r["note"]:
                fail("%s %s 「문서에 없음」인데 note 에 찾은 범위 없음" % (tag, f))
        src = w6_xml(r["source_text"])
        if r["concurrent_title"] == "(나누지 않음)":
            if w6_xml(r["concurrent_company"]) not in src:
                fail("%s 나누지 않은 company 가 source_text 의 이어진 글이 아님" % tag)
            if "(판단)" not in r["note"]:
                fail("%s title 「(나누지 않음)」인데 note 에 (판단) 없음" % tag)
        else:
            for f in ("concurrent_company", "concurrent_title"):
                if r[f] and w6_xml(r[f]) not in src:
                    fail("%s %s 「%s」가 source_text 의 이어진 부분 글이 아님" % (tag, f, r[f][:40]))
            # 나누기 꼴 점검(15차 비평의 허진호·이종백 류): 법인 종류 낱말뿐인 회사, 회사 끝·앞에 붙은 직함, 부서 이름에서 끊긴 회사
            c, toks = r["concurrent_company"], r["concurrent_company"].split()
            why = ""
            if re.fullmatch(r"(?:법무법인|사단법인|재단법인|종합법률사무소|세무법인|회계법인)(?:\((?:유|유한)\))?", c) and r["concurrent_title"]:
                why = "회사 칸이 법인 종류 낱말뿐(이름이 직위 칸으로 감)"
            elif len(toks) >= 2 and re.search(r"(?:대표이사|부사장|사장|실장|청장|겸)$", toks[-1]):
                why = "회사 칸 끝에 직함"
            elif len(toks) >= 2 and re.search(r"(?:청장|원장|총장|학장)$", toks[0]):
                why = "회사 칸 앞에 직함"
            elif len(toks) >= 2 and re.search(r"(?:연구|본부|사업개발)$", c):
                why = "회사 칸이 부서 이름 중간에서 끊김"
            if why:
                fail("%s 회사·직위 나누기 꼴 의심(%s): 「%s」/「%s」" % (tag, why, c, r["concurrent_title"]))
    seen = {}
    ndup = 0
    for k, r in enumerate(A, 2):
        if r["source_text"] == W6_NONE or rep.get(r["rcept_no_or_url"], {}).get("kind") != "정정":
            continue
        key = (r["corp_label"], r["fy"], r["person"], w6_xml(r["source_text"]))
        if key in seen and seen[key][1] != r["rcept_no_or_url"]:
            ndup += 1
            fail("A 줄 %d: 같은 FY 다른 정정판(%s·%s)에 같은 행이 두 번 — %s %s" % (k, seen[key][1], r["rcept_no_or_url"], r["person"], r["fy"]))
        seen.setdefault(key, (k, r["rcept_no_or_url"]))
    say("- A: registered 「문서에 없음」 %d · fulltime 「문서에 없음」 %d · registered/fulltime 빈칸 %d · 「(나누지 않음)」 %d · 정정판 사이 같은 행 %d"
        % (nreg, nft, sum(1 for r in A if r["source_text"] != W6_NONE and (not r["registered"].strip() or not r["fulltime"].strip())),
           sum(1 for r in A if r["concurrent_title"] == "(나누지 않음)"), ndup))

    # B: keyword 값, 임원 현황 표 행 표시
    nb_off = 0
    for k, r in enumerate(data["B"], 2):
        tag = "B 줄 %d(%s FY%s)" % (k, r["corp_label"], r["fy"])
        kw = r["keyword"]
        if not (kw == "없음" or all(x in W6_KW for x in kw.split("·"))):
            fail("%s keyword 「%s」가 요청 키워드 6개·「없음」 밖" % (tag, kw))
        if r["doc_kind"] != "사업보고서" or r["source_text"] == W6_NONE:
            continue
        d = doc(r["rcept_no_or_url"])
        oc = d.occ(w6_xml(r["source_text"])) if d else []
        in_off = False
        for s, _ in oc[:1]:
            tno = d.tab_of[d.line_at(s)]
            if tno is not None:
                s0, e0 = d.tabs[tno]
                hdr = w6_xml(d.L[s0 + 1]) if s0 + 1 < e0 else ""
                in_off = hdr.startswith("성명") and "출생" in hdr
        mark = "(위치) 임원 현황 표 — 작업 A 와 겹침" in r["note"]
        nb_off += in_off
        if in_off != mark:
            fail("%s 임원 현황 표 행 %s — note 표시 %s" % (tag, "임" if in_off else "아님", "있음" if mark else "없음"))
    say("- B: keyword 값 「%s」 · 임원 현황 표 행(note 「(위치) 임원 현황 표 — 작업 A 와 겹침」) %d"
        % (" · ".join("%s %d" % (x, sum(1 for r in data["B"] if r["keyword"] == x)) for x in sorted(set(r["keyword"] for r in data["B"]))), nb_off))

    # D: 묶음 풀기, 「위탁」 넓혀 넣은 행, Ⅹ 거래 표 위치 인용
    D = data["D"]
    nwt = ngrp = 0
    keyset = set()
    for k, r in enumerate(D, 2):
        tag = "D 줄 %d(%s FY%s)" % (k, r["corp_label"], r["fy"])
        if "같은 상대방·유형 언급 글" in r["note"]:
            fail("%s 글이 다른 곳을 같은 (상대방·유형)으로 묶은 note 가 남음" % tag)
        if r["source_text"] != W6_NONE:
            key = (r["rcept_no_or_url"], w6_xml(r["source_text"]), r["counterparty"], r["contract_type"])
            if key in keyset:
                fail("%s 같은 보고서·같은 글·같은 (상대방·유형) 행이 두 번" % tag)
            keyset.add(key)
        mm = re.search(r"글자까지 같은 글이 (\d+)곳 더: ([^;]*)", r["note"])
        if mm and r["doc_kind"] == "사업보고서":
            ngrp += 1
            d = doc(r["rcept_no_or_url"])
            locs = re.findall(r"\[절 (\d+)\] 「(.*?)」(?: \[표 (\d+)\])?", mm.group(2))
            for n, ti, tb in locs:
                if not any((int(n), ti) in d.heads_at(d.line_at(s)) and
                           (tb == "" or d.tab_of[d.line_at(s)] == int(tb)) for s, _ in d.occ(w6_xml(r["source_text"]))):
                    fail("%s note 「글자까지 같은 글」 위치 [절 %s] [표 %s] 에 같은 글 없음" % (tag, n, tb or "-"))
        if "검색어 「위탁」으로 넓혀 넣음" in r["note"]:
            nwt += 1
            s = r["source_text"]
            if "위탁" not in s or "위탁" not in r["contract_type"] or w6_xml(r["contract_type"]) not in w6_xml(s):
                fail("%s 「위탁」 행인데 source_text·contract_type 꼴이 맞지 않음" % tag)
            if not (W6_INFO.search(s) or W6_AFF.search(s)):
                fail("%s 「위탁」 행인데 같은 글에 정보·계열 낱말 없음" % tag)
            if "(판단)" not in r["note"]:
                fail("%s 「위탁」 행 note 에 (판단) 없음" % tag)
        for seg in re.findall(r"지주–자회사 거래 표[^;]*", r["note"]):
            d = doc(r["rcept_no_or_url"])
            for a, b, q in re.findall(r"md (\d+)(?:~(\d+))?행 ((?:「[^」]*」)+)", seg):
                qs = re.findall(r"「([^」]*)」", q)
                ln = list(range(int(a) - 1, int(b or a)))
                if d is None or len(qs) != len(ln) or any(d.L[i].strip() != x for i, x in zip(ln, qs)):
                    fail("%s note Ⅹ 거래 표 위치 인용(md %s행)이 원문 줄과 다름" % (tag, a))
    # 「위탁」 넓혀 찾기 덮임 — 본 보고서 Ⅹ~Ⅺ 의 「위탁」(위탁자·위탁매매 등 낱말 뺌) 가운데 같은 줄에 정보·계열 낱말이 있는 곳
    unc, noted = [], 0
    for rc, m in rep.items():
        if m["label"] not in cos or m["kind"] != "본" or not m.get("text_path"):
            continue
        d = doc(rc)
        x, xi = d.chap("X"), d.chap("XI")
        if not x:
            continue
        s0, e0 = x[0], (xi[1] if xi else x[1])
        drs = [r for r in D if r["rcept_no_or_url"] == rc and r["source_text"] != W6_NONE]
        spans = [sp for r in drs for sp in d.occ(w6_xml(r["source_text"]))]
        for i in range(s0, e0):
            l = d.L[i]
            if "위탁" not in l or l.startswith("### "):
                continue
            ctxt = " ".join(d.L[max(s0, i - 2):min(e0, i + 3)])
            for mm in re.finditer("위탁", l):
                if W6_NOISE.match(l, mm.start()):
                    continue
                if not (W6_INFO.search(l) or W6_AFF.search(l) or (len(l) < 40 and (W6_INFO.search(ctxt) or W6_AFF.search(ctxt)))):
                    continue
                pos = d.off[i] + len(w6_xml(l[:mm.start()]))
                if any(a <= pos < b for a, b in spans):
                    continue
                locs = ["[절 %d] 「%s」" % hh for hh in d.heads_at(i)]
                loc = locs[-1] if locs else "-"
                if any("넣지 않은 글" in r["note"] and any(lc in r["note"] for lc in locs) for r in D if r["rcept_no_or_url"] == rc):
                    noted += 1
                    continue
                unc.append("%s FY%s md %d행 %s 「…%s…」" % (m["label"], m["fy"], i + 1, loc, l[max(0, mm.start() - 20):mm.end() + 20]))
    say("- D: 「위탁」 넓혀 넣은 행 %d · 「글자까지 같은 글」로 묶은 행 %d(위치마다 같은 글 확인) · 「위탁」+정보·계열 낱말 줄 가운데 행에 없고 note 「넣지 않은 글」 절에 있는 곳 %d · 어디에도 없는 곳 %d"
        % (nwt, ngrp, noted, len(unc)))
    for x in unc[:20]:
        fail("D 「위탁」 넓혀 찾기 누락 후보 " + x)
    say("- 조각별 행 수: " + " · ".join("%s %d(「문서에 없음」 %d)" % (T, len(data[T]), sum(1 for r in data[T] if r["source_text"] == W6_NONE)) for T in "ABD"))
    say("")


def main():
    lst = {r["rcept_no"]: r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig")) if r["label"] in CORPS}
    mgmt = {r["corp_label"]: r for r in csv.DictReader(open(MGMT_CSV, encoding="utf-8-sig")) if r["corp_label"] in CORPS}
    mds = {}

    def md_of(rc):
        if rc not in mds:
            r = lst.get(rc)
            mds[rc] = MD(r["text_path"]) if r and r["text_path"] and os.path.exists(r["text_path"]) else None
        return mds[rc]

    t13_rcept = {}
    for c in CORPS:
        m = re.search(r"dart_out/doc/(\d+)/", t13("사업보고서", c)["head"])
        t13_rcept[c] = m.group(1) if m else ""

    now = datetime.now(KST).isoformat(timespec="seconds")
    say("# 15차 검증 — 사업보고서 조각 g2 (NH농협금융지주·메리츠금융지주·iM금융지주)")
    say("실행: %s (KST) · 스크립트 scripts/dart/verify15_bs_g2.py · 생성기 %s md5 %s" % (
        now, GEN, hashlib.md5(open(GEN, "rb").read()).hexdigest()))
    say("대조 정규화: 공백·줄바꿈·「|」 무시(md 칸 안 줄바꿈 표시 <br>·&cr; 도 줄바꿈으로 보아 무시). 그 밖의 글자는 그대로 비교.")
    say("")

    data = {}
    # ---------------------------------------------------------------- (c) 형식
    say("## (c) 열 이름·utf-8-sig·필수 칸·출처 목록 일치")
    for T in "ABD":
        p = os.path.join(FRAG, "%s_bs_g2.csv" % T)
        raw = open(p, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rd = csv.reader(open(p, encoding="utf-8-sig", newline=""))
        hdr = next(rd)
        rows = [dict(zip(hdr, r)) for r in rd]
        data[T] = rows
        say("- %s_bs_g2.csv: %d행, md5 %s, BOM %s, 열 %s" % (T, len(rows), hashlib.md5(raw).hexdigest(), "있음" if bom else "없음",
                                                       "COMMON15 과 같음" if hdr == COLS[T] else "다름"))
        if not bom:
            fail("%s: utf-8-sig BOM 없음" % T)
        if hdr != COLS[T]:
            fail("%s: 열 이름/순서 다름 %s" % (T, hdr))
        blanks = {}
        for k, r in enumerate(rows):
            for c in REQ_ALL + REQ[T]:
                if not (r.get(c) or "").strip():
                    blanks.setdefault(c, []).append(k + 2)
        for c, ks in blanks.items():
            fail("%s: 필수 칸 %s 빈칸 %d행(csv 줄 %s)" % (T, c, len(ks), ks[:10]))
        if not blanks:
            say("  필수 칸 빈칸 0")
        bad = 0
        for k, r in enumerate(rows):
            if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00", r["collected_at"]):
                bad += 1
                fail("%s 줄 %d: collected_at 꼴이 KST ISO 가 아님 「%s」" % (T, k + 2, r["collected_at"]))
            if r["corp_label"] not in CORPS:
                fail("%s 줄 %d: g2 밖 회사 %s" % (T, k + 2, r["corp_label"]))
            if r["doc_kind"] == "사업보고서":
                L = lst.get(r["rcept_no_or_url"])
                if not L:
                    fail("%s 줄 %d: rcept %s 가 사업보고서_원문.csv 에 없음" % (T, k + 2, r["rcept_no_or_url"]))
                    continue
                for col, want in (("doc_name", L["report_nm"]), ("collected_at", L["fetched_at"]), ("fy", L["fy"]),
                                  ("corp_label", L["label"])):
                    if r[col] != want:
                        bad += 1
                        fail("%s 줄 %d: %s 「%s」 ≠ 목록 「%s」" % (T, k + 2, col, r[col], want))
            elif r["doc_kind"] == "경영공시":
                M = mgmt.get(r["corp_label"])
                if not M or r["rcept_no_or_url"] != M["url"] or r["collected_at"] != kst(M["fetched_at"]) or r["fy"] != "2026.2Q":
                    bad += 1
                    fail("%s 줄 %d: 경영공시 url/collected_at/fy 가 경영공시_2026_2Q.csv 와 다름" % (T, k + 2))
            else:
                fail("%s 줄 %d: doc_kind 「%s」" % (T, k + 2, r["doc_kind"]))
        say("  doc_name·collected_at·fy·회사 ↔ 사업보고서_원문.csv / 경영공시_2026_2Q.csv: 다른 행 %d" % bad)
    say("")

    # ---------------------------------------------------------------- (a)(b) 원문·위치
    say("## (a) source_text·reason_text 원문 대조, (b) page 위치 대조")
    LOC = re.compile(r"XML \[절 (\d+)\] 「(.*?)」 (?:\[표 (\d+)\]|\(문단\))")
    P13 = re.compile(r"(p\.\d+(?:[,~]p\.\d+)*)\(본문 PDF, 13차 보관\)")
    stat = {}
    p13stat = {"full": 0, "prefix": 0, "none": 0}
    multi_nc = []
    for T in "ABD":
        st = stat.setdefault(T, dict(rows=0, none=0, text_ok=0, text_bad=0, page_ok=0, page_bad=0, reason_checked=0, p13=0))
        for k, r in enumerate(data[T]):
            st["rows"] += 1
            src = r["source_text"]
            ln = k + 2
            if src == NONE:
                st["none"] += 1
                continue
            texts = [("source_text", src)]
            if T == "A" and r["reason_text"] != NONE:
                texts.append(("reason_text", r["reason_text"]))
                st["reason_checked"] += 1
            if r["doc_kind"] == "경영공시":
                P = t13("경영공시", r["corp_label"])
                m = re.fullmatch(r"p\.(\d+)", r["page"])
                for col, tx in texts:
                    hit = [p for p, v in P["v"].items() if vnorm(tx) in v]
                    if not hit:
                        st["text_bad"] += 1
                        fail("%s 줄 %d: %s 이 경영공시 PDF 텍스트에 없음" % (T, ln, col))
                        continue
                    st["text_ok"] += 1
                    if m and int(m.group(1)) in hit:
                        st["page_ok"] += 1
                    else:
                        st["page_bad"] += 1
                        fail("%s 줄 %d: page 「%s」 ≠ 글이 있는 쪽 %s" % (T, ln, r["page"], hit))
                continue
            md = md_of(r["rcept_no_or_url"])
            if md is None:
                fail("%s 줄 %d: 원문 md 없음 %s" % (T, ln, r["rcept_no_or_url"]))
                continue
            for col, tx in texts:
                ok, line = md.find_lines(tx)
                parts = [x for x in tx.split("\n") if x.strip()]
                if not ok and len(parts) > 1 and all(md.find_lines(x)[0] for x in parts):
                    # (15차 wave6) 새 대조 규칙: 줄마다 따로 있어도 이어서 있지 않으면 실패
                    multi_nc.append("%s 줄 %d %s FY%s %s" % (T, ln, r["corp_label"], r["fy"], r["person"] if T == "A" else ""))
                if ok:
                    st["text_ok"] += 1
                else:
                    st["text_bad"] += 1
                    fail("%s 줄 %d: %s 이 원문 md(%s)에 글자 그대로 없음 「%s」" % (T, ln, col, r["rcept_no_or_url"], tx[:80]))
            # (b) page
            m = LOC.match(r["page"])
            if not m:
                st["page_bad"] += 1
                fail("%s 줄 %d: page 꼴 「%s」" % (T, ln, r["page"]))
                continue
            n, title, tno = int(m.group(1)), m.group(2), m.group(3)
            sec = md.sec(n)
            good = True
            if not sec or sec[2] != title:
                good = False
                fail("%s 줄 %d: [절 %d] 제목 「%s」 ≠ md 「%s」" % (T, ln, n, title, sec[2] if sec else None))
            else:
                if tno:
                    tb = md.tabs.get(int(tno))
                    if not tb or not (sec[0] <= tb[0] < sec[1]):
                        good = False
                        fail("%s 줄 %d: [표 %s] 가 [절 %d] 안에 없음" % (T, ln, tno, n))
                    rng = (tb[0], tb[1] + 1) if tb else (0, 0)
                else:
                    rng = (sec[0], sec[1])
                for x in [x for x in src.split("\n") if x.strip()]:
                    if good and not md.find_lines(x, *rng)[0]:
                        good = False
                        fail("%s 줄 %d: source_text 가 page 위치(%s) 안에 없음" % (T, ln, r["page"][:60]))
                if good and not tno:
                    # 문단 행: 글이 표 밖 줄인지
                    _, li = md.find_lines(src, *rng)
                    if li is not None and any(a <= li <= b for a, b in md.tabs.values()):
                        good = False
                        fail("%s 줄 %d: page 는 (문단)인데 글이 표 안에 있음" % (T, ln))
            # 13차 PDF 쪽
            m2 = P13.search(r["page"])
            is25 = r["fy"] == "2025" and r["rcept_no_or_url"] == t13_rcept[r["corp_label"]]
            if is25 and not m2:
                good = False
                fail("%s 줄 %d: FY2025 본 보고서 행인데 13차 PDF 쪽 없음" % (T, ln))
            if m2 and not is25:
                good = False
                fail("%s 줄 %d: 13차 PDF(본 %s)가 아닌 보고서 행에 PDF 쪽" % (T, ln, t13_rcept[r["corp_label"]]))
            if m2 and is25:
                st["p13"] += 1
                P = t13("사업보고서", r["corp_label"])
                ps = [int(x) for x in re.findall(r"p\.(\d+)", m2.group(1))]
                if "~" in m2.group(1):
                    v = "".join(P["v"].get(p, "") for p in range(ps[0], ps[-1] + 1))
                    cands = [v]
                else:
                    cands = [P["v"].get(p, "") for p in ps]
                vs = vnorm(src)
                if any(vs in c for c in cands):
                    p13stat["full"] += 1
                elif any(len(vs) >= 8 and (vs[:80] in c or vs[:40] in c) for c in cands):
                    p13stat["prefix"] += 1
                else:
                    p13stat["none"] += 1
                    good = False
                    fail("%s 줄 %d: 13차 PDF %s 에 같은 글(앞 40자도) 없음" % (T, ln, m2.group(1)))
            if good:
                st["page_ok"] += 1
            else:
                st["page_bad"] += 1
    for T in "ABD":
        s = stat[T]
        say("- %s: %d행(문서에 없음 %d) — 글 대조 맞음 %d / 틀림 %d (reason_text 대조 %d행), page 맞음 %d / 틀림 %d, 13차 PDF 쪽 붙은 행 %d" % (
            T, s["rows"], s["none"], s["text_ok"], s["text_bad"], s["reason_checked"], s["page_ok"], s["page_bad"], s["p13"]))
    say("- 13차 본문 PDF 쪽: 그 쪽에 글 전체 %d행, 앞 80/40자만(PDF 표 칸 순서·줄바꿈 차이) %d행, 없음 %d행" % (
        p13stat["full"], p13stat["prefix"], p13stat["none"]))
    say("- 여러 줄 source_text 가운데 md 에서 이어지지 않는 행(줄마다는 있음 — 새 대조 규칙으로 실패): %d" % len(multi_nc))
    for x in multi_nc[:40]:
        say("    %s" % x)
    say("")

    # ---------------------------------------------------------------- 「문서에 없음」 행 page(찾은 범위)
    say("## (b') 「문서에 없음」 행 page(찾은 범위) 대조")
    for T in "ABD":
        for k, r in enumerate(data[T]):
            if r["source_text"] != NONE:
                continue
            ln = k + 2
            if r["doc_kind"] == "경영공시":
                P = t13("경영공시", r["corp_label"])
                m = re.match(r"p\.(\d+)~p\.(\d+)", r["page"])
                ok = bool(m) and int(m.group(1)) == min(P["pages"]) and int(m.group(2)) == max(P["pages"])
                say("- %s 줄 %d %s %s: page 「%s」 — 실제 PDF 텍스트 p.%d~p.%d → %s" % (
                    T, ln, r["corp_label"], r["fy"], r["page"], min(P["pages"]), max(P["pages"]), "맞음" if ok else "틀림"))
                if not ok:
                    fail("%s 줄 %d: 문서에 없음 행 page 가 찾은 쪽 범위와 다름" % (T, ln))
            else:
                md = md_of(r["rcept_no_or_url"])
                ns = [int(x) for x in re.findall(r"\[절 (\d+)\]", r["page"])]
                rx = md.chap_x_xi()
                want = sorted(set(n for i, n, t in md.heads if rx and rx[0] <= i < rx[1]))
                ok = bool(ns) and want and ns[0] == want[0] and ns[-1] == want[-1]
                say("- %s 줄 %d %s FY%s: page 「%s」 — Ⅹ~Ⅺ 실제 [절 %s~%s] → %s" % (
                    T, ln, r["corp_label"], r["fy"], r["page"], want[0] if want else "?", want[-1] if want else "?", "맞음" if ok else "틀림"))
                if not ok:
                    fail("%s 줄 %d: 문서에 없음 행 page 가 찾은 절 범위와 다름" % (T, ln))
    say("")

    # ---------------------------------------------------------------- (d) 비밀값
    say("## (d) 키·비밀값 문자열")
    files = [os.path.join(FRAG, "%s_bs_g2.csv" % T) for T in "ABD"] + [GEN, WORK_JSON]
    try:
        files += json.load(open(WORK_JSON, encoding="utf-8")).get("written", [])
    except Exception:
        pass
    key = os.environ.get("DART_API_KEY", "")
    pats = [re.compile(r"crtfc" + r"_key\s*=\s*\w{8,}"), re.compile(r"(?<![0-9A-Fa-f])[0-9a-f]{40}(?![0-9A-Fa-f])"),
            re.compile(r"DART" + r"_API_KEY\s*[=:]\s*['\"]?\w{16,}"), re.compile(r"gh" + r"p_[A-Za-z0-9]{20,}"),
            re.compile(r"s" + r"k-[A-Za-z0-9_-]{20,}"), re.compile(r"AK" + r"IA[0-9A-Z]{16}")]
    hits = 0
    for f in files:
        if not os.path.exists(f):
            continue
        t = open(f, encoding="utf-8", errors="replace").read()
        if len(key) >= 16 and key in t:
            hits += 1
            fail("비밀값: %s 에 DART_API_KEY 값이 들어 있음(값은 쓰지 않음)" % f)
        for p in pats:
            if p.search(t):
                hits += 1
                fail("비밀값 꼴 문자열: %s (패턴 %d)" % (f, pats.index(p)))
    say("- 본 파일 %d개(조각 CSV 3·생성기·work json·원문 md %d개): DART_API_KEY 값(환경변수 %s) 포함 0건이어야 함 / 키 꼴 문자열 — 걸린 것 %d" % (
        len(files), len(files) - 5, "있음" if key else "없음", hits))
    say("")

    # ---------------------------------------------------------------- (e) 회사×FY
    say("## (e) 회사×FY(2019~2025) 마다 A·B·D 각 1행 이상")
    miss = []
    tab = []
    for c in CORPS:
        line = []
        for fy in range(2019, 2026):
            n = [sum(1 for r in data[T] if r["corp_label"] == c and r["fy"] == str(fy)) for T in "ABD"]
            line.append("%d:%s" % (fy, "/".join(map(str, n))))
            for T, x in zip("ABD", n):
                if x == 0:
                    miss.append("%s %s FY%d" % (T, c, fy))
        n26 = [sum(1 for r in data[T] if r["corp_label"] == c and r["fy"] == "2026.2Q") for T in "BD"]
        tab.append("- %s (A/B/D): %s · 2026.2Q 경영공시 B/D %d/%d" % (c, " ".join(line), n26[0], n26[1]))
    for x in tab:
        say(x)
    for x in miss:
        fail("행 없음: " + x)
    if not miss:
        say("  빠진 칸 없음")
    say("")

    # ---------------------------------------------------------------- (f) B 숫자
    say("## (f) B 숫자 칸 = 원문 직원 표 합계 행 (source_text 또는 note 「합계 행: 「…」」 인용 안 숫자)")
    fb = 0
    seen = set()
    for k, r in enumerate(data["B"]):
        if r["doc_kind"] != "사업보고서":
            if r["employees_total"] or r["regular"] or r["contract"]:
                fail("B 줄 %d: 경영공시 행인데 직원 수 칸이 차 있음" % (k + 2))
            continue
        md = md_of(r["rcept_no_or_url"])
        r8 = md.chap("VIII")
        tot = None
        for no, (s, e) in sorted(md.tabs.items(), key=lambda x: x[1][0]):
            if not (r8[0] <= s < r8[1]):
                continue
            body = [i for i in range(s + 1, e) if md.L[i].startswith("|")]
            h = "".join(md.vl[i] for i in body[:4])
            if "기간의정함" in h and "기간제" in h:
                ts = [i for i in body if re.fullmatch(r"합계|총계|계", vnorm(md.L[i].strip()[1:-1].split("|")[0]))]
                if ts:
                    tot = ts[-1]
                    break
        if tot is None:
            fb += 1
            fail("B 줄 %d: 원문 직원 표 합계 행 못 찾음" % (k + 2))
            continue
        cells = [c.strip() for c in md.L[tot].strip()[1:-1].split("|")]
        nums = [c for c in cells[1:]]
        want = dict(regular=nums[0], contract=nums[2], employees_total=nums[4])
        bad = [c for c in want if r[c] != want[c]]
        quote = r["source_text"] if r["keyword"] == "없음" else (re.search(r"합계 행: 「(.*?)」(?:;|$)", r["note"]) or [None, ""])[1]
        qok = bool(quote) and vnorm(quote) == md.vl[tot] and all(r[c] in quote for c in want)
        try:
            ar = int(want["regular"].replace(",", "")) + int(want["contract"].replace(",", "")) == int(want["employees_total"].replace(",", ""))
        except ValueError:
            ar = False
        if bad or not qok or not ar:
            fb += 1
            fail("B 줄 %d %s FY%s: 숫자 %s / 원문 합계 행 %s / 인용 %s / 합계=정함없음+기간제 %s" % (
                k + 2, r["corp_label"], r["fy"], [r[c] for c in want], [want[c] for c in want], "맞음" if qok else "다름", ar))
        key2 = (r["corp_label"], r["fy"], r["rcept_no_or_url"])
        if key2 not in seen:
            seen.add(key2)
    say("- 사업보고서 B %d행 대조, 다른 행 %d (보고서 %d개)" % (sum(1 for r in data["B"] if r["doc_kind"] == "사업보고서"), fb, len(seen)))
    nine = {}
    if os.path.exists(os.path.join("handoff", "원문_지주조직_CRO.csv")):
        for r in csv.DictReader(open(os.path.join("handoff", "원문_지주조직_CRO.csv"), encoding="utf-8-sig")):
            nine[(r["corp_label"], r["fy"])] = r["employees"]
    cmp9 = []
    for c in CORPS:
        for fy in ("2023", "2024", "2025"):
            ours = {r["employees_total"] for r in data["B"] if r["corp_label"] == c and r["fy"] == fy and r["doc_kind"] == "사업보고서"}
            v9 = next((v for (cc, f), v in nine.items() if f == fy and (cc == c or cc.replace("NH", "") == c.replace("NH", ""))), None)
            cmp9.append("%s FY%s ours %s / 9차 %s" % (c, fy, "·".join(sorted(ours)), v9))
    say("- 9차 원문_지주조직_CRO.csv employees 와 나란히(참고): " + "; ".join(cmp9))
    say("")

    # ---------------------------------------------------------------- (g) 겸직 표 전수(회사마다 2개 FY)
    say("## (g) 겸직 표 모든 행이 A 에 있는지 — 회사마다 2개 FY (겸직 표는 이 스크립트가 따로 찾음)")
    PICK = {"NH농협금융지주": ["2019", "2023"], "메리츠금융지주": ["2021", "2024"], "iM금융지주": ["2020", "2025"]}
    for c in CORPS:
        for fy in PICK[c]:
            main_r = next(r for r in lst.values() if r["label"] == c and r["fy"] == fy and r["kind"] == "본")
            md = md_of(main_r["rcept_no"])
            r8, r9, rx = md.chap("VIII"), md.chap("IX"), md.chap("X")
            rng = (r8[0], rx[0] if rx else len(md.L))
            arows = [r for r in data["A"] if r["rcept_no_or_url"] == main_r["rcept_no"]]
            av = [vnorm(r["source_text"]) for r in arows]
            tot = direct = same = selfrow = 0
            missing = []
            tabs = conc_tables(md, rng)
            for no, hdr, rows in tabs:
                prev = None
                full = max(len(cs) for i, cs in rows)
                for i, cs in rows:
                    if len(cs) < full - 1 or vnorm(cs[0]) in ("성명", "회사명", "겸직대상자"):
                        continue        # 둘째 머리 줄(「회사명 | 직 책 | 상근여부」 등)
                    tot += 1
                    v = md.vl[i]
                    name = cs[0] if len(cs) == full else prev
                    if len(cs) == full:
                        prev = cs[0]
                    comp = cs[1] if len(cs) == full else cs[0]
                    if any(ckey(s) in ckey(comp) for s in SELF[c]):
                        selfrow += 1
                        continue
                    if any(v and v in a for a in av):
                        direct += 1
                        continue
                    cand = [r for r in arows if pkey(r["person"]) == pkey(name or "") and ckey(r["concurrent_company"]) == ckey(comp)
                            and ("[표 %d]" % no) in r["note"]]
                    if cand:
                        same += 1
                    else:
                        missing.append("[표 %d] 줄 %d 「%s」" % (no, i + 1, md.L[i][:70]))
            say("- %s FY%s (%s): 겸직 표 %d개(%s) 몸 행 %d — A source_text 에 그대로 %d, 같은 사람·회사 행 note 「같은 행: [표 n]」 %d, "
                "지주 자기 직위 줄(그룹 표, 생성기 판단으로 뺌) %d, 빠짐 %d" % (
                    c, fy, main_r["rcept_no"], len(tabs), ",".join("표%d" % t[0] for t in tabs), tot, direct, same, selfrow, len(missing)))
            for x in missing:
                fail("겸직 표 행이 A 에 없음: %s FY%s %s" % (c, fy, x))
    say("")

    # ---------------------------------------------------------------- (h) 출생년월
    say("## (h) 출생년월 맞춤 — 전수 자동 대조 + 표본 20행")
    rows_b = [(k, r) for k, r in enumerate(data["A"]) if r["source_text"] != NONE]
    bad_b, amb, blank_ok, blank_bad = [], 0, 0, []
    detail = {}
    for k, r in rows_b:
        md = md_of(r["rcept_no_or_url"])
        r8 = md.chap("VIII")
        ex = [x for x in exec_rows(md, r8) if pkey(x[1]) == pkey(r["person"])]
        births = sorted(set(bkey(cellv(x[2][2])) for x in ex))
        if not r["birth_ym"]:
            if ex:
                blank_bad.append(k + 2)
                fail("A 줄 %d: birth_ym 빈칸인데 임원 표에 같은 성명 %s 있음" % (k + 2, r["person"]))
            else:
                blank_ok += 1
            continue
        mt = [x for x in ex if cellv(x[2][2]) == r["birth_ym"]]
        if not mt:
            bad_b.append(k + 2)
            fail("A 줄 %d: birth_ym %s 이 임원 표 같은 성명 행(%s)과 다름" % (k + 2, r["birth_ym"], births))
            continue
        def flds(x):
            return dict(holdco_title=cellv(x[2][3]), registered=cellv(x[2][4]), fulltime=cellv(x[2][5]), holdco_duty=cellv(x[2][6]))
        good = [x for x in mt if all(r[f] == v for f, v in flds(x).items())]
        x = good[0] if good else mt[0]
        dif = [] if good else [f for f, v in flds(x).items() if r[f] != v]
        if dif:
            fail("A 줄 %d: %s 이 같은 성명·출생년월 임원 표 행 어느 것과도 다름 %s" % (k + 2, dif, [(r[f], flds(x)[f]) for f in dif]))
        if len(births) > 1:
            amb += 1
            if not ("출생년월" in r["note"] and ("(판단)" in r["note"] or "출생년월로 구분" in r["note"])):
                fail("A 줄 %d: 같은 성명 출생년월 %s 인데 note 에 동명이인 표시 없음" % (k + 2, births))
        detail[k] = (x, births, dif)
    say("- birth_ym 찬 행 %d: 임원 표 같은 성명 행 출생년월과 다름 %d, 같은 성명이 출생년월 둘 이상인 행 %d(note 「(판단)」 확인)" % (
        len(detail) + len(bad_b), len(bad_b), amb))
    say("- birth_ym 빈칸 행 %d: 같은 보고서 임원 표에 그 성명 없음 %d, 있음(잘못) %d" % (blank_ok + len(blank_bad), blank_ok, len(blank_bad)))
    rnd = random.Random(1502)
    samp = rnd.sample(sorted(detail), min(20, len(detail)))
    say("- 표본 20행(seed 1502): csv 줄 · 회사 FY · 성명 · birth_ym ↔ 임원 표 [표 n] 줄 · 출생년월 칸 원문 · 같은 성명 출생년월들 · 지주 칸 일치")
    for k in sorted(samp):
        r = data["A"][k]
        x, births, dif = detail[k]
        say("    줄 %d · %s FY%s · %s · %s ↔ [표 %d] md 줄 %d 「%s」 · %s · %s" % (
            k + 2, r["corp_label"], r["fy"], r["person"], r["birth_ym"], x[3], x[0] + 1, x[2][2], "/".join(births),
            "직위·담당·등기·상근 같음" if not dif else "다름 %s" % dif))
    say("")

    # ---------------------------------------------------------------- (i) 「문서에 없음」 반박 시도
    say("## (i) 「문서에 없음」 반박 시도(더 넓은 검색어, 공백·줄바꿈 무시)")
    WIDE_D = r"위탁|수탁|용역|자문(?!책)|공동사용|공동이용|공유|전산|IT|시스템|아웃소싱|업무지원|경영관리|지원업무|수수료|임대차|브랜드|상표|명칭사용|서비스"
    WITH = r"자회사|계열|대주주|특수관계|이해관계자|지주|그룹|종속"
    for k, r in enumerate(data["D"]):
        if r["source_text"] != NONE:
            continue
        if r["doc_kind"] == "경영공시":
            P = t13("경영공시", r["corp_label"])
            hits = []
            for p, v in sorted(P["v"].items()):
                for w in re.findall(r"업무위탁|위수탁|위탁계약|수탁계약|용역|경영자문|자문계약|자문료|공동사용|공동이용|공동전산|전산공동|"
                                    r"아웃소싱|업무지원|위탁업무|수탁업무", v):
                    pos = v.find(w)
                    hits.append("p.%d「%s」" % (p, v[max(0, pos - 18): pos + 18]))
            say("- D 줄 %d %s 2026.2Q 경영공시: 넓은 검색어 걸린 곳 %d %s" % (k + 2, r["corp_label"], len(hits), " / ".join(hits[:8])))
            continue
        md = md_of(r["rcept_no_or_url"])
        rx = md.chap_x_xi()
        hits = []
        for i in range(rx[0], rx[1]):
            v = md.vl[i]
            if md.L[i].startswith("### "):
                continue
            if re.search(WIDE_D, v) and re.search(WITH, v):
                w = re.search(WIDE_D, v).group(0)
                pos = v.find(w)
                hits.append("md%d「%s」" % (i + 1, v[max(0, pos - 20): pos + 20]))
        say("- D 줄 %d %s FY%s: Ⅹ~Ⅺ 넓은 검색어(%s)와 계열·자회사·대주주·지주·그룹·종속 낱말이 같은 줄 %d" % (
            k + 2, r["corp_label"], r["fy"], WIDE_D.replace("(?!책)", "").replace("|", "·"), len(hits)))
        for h in hits[:12]:
            say("    %s" % h)
        if len(hits) > 12:
            say("    … 외 %d줄" % (len(hits) - 12))
    WIDE_B = r"겸직|파견|출향|전출|전적|겸무|겸임|겸업|인사교류|인력교류|전보|지원인력|겸무"
    for k, r in enumerate(data["B"]):
        if r["source_text"] == NONE:
            P = t13("경영공시", r["corp_label"])
            hits = []
            for p, v in sorted(P["v"].items()):
                for mm in re.finditer(WIDE_B, v):
                    if mm.group(0) == "전보" and re.match(r"보(통주|완자본)", v[mm.start() + 1: mm.start() + 5]):
                        continue        # 「차감전 보통주자본·보완자본」
                    if re.search(r"완전적|전적으로|전적인|사전적|전출입", v[max(0, mm.start() - 1): mm.end() + 2]):
                        continue        # 「완전적용」 등 — 생성기와 같은 오탐 빼기
                    hits.append("p.%d「%s」" % (p, v[max(0, mm.start() - 18): mm.end() + 18]))
            say("- B 줄 %d %s 2026.2Q 경영공시: 넓은 검색어(%s, 공백 무시) 걸린 곳 %d %s" % (
                k + 2, r["corp_label"], WIDE_B.replace("|", "·"), len(hits), " / ".join(hits[:8])))
        elif r["keyword"] == "없음":
            md = md_of(r["rcept_no_or_url"])
            r8 = md.chap("VIII")
            hits = []
            for i in range(r8[0], r8[1]):
                for mm in re.finditer(WIDE_B, md.vl[i]):
                    ctx = md.vl[i][max(0, mm.start() - 15): mm.end() + 15]
                    if re.search(r"전적으로|전적인|사전적|완전적|전출입", ctx):
                        continue
                    hits.append("md%d「%s」" % (i + 1, ctx))
            say("- B 줄 %d %s FY%s keyword 「없음」: Ⅷ 전체 넓은 검색어(공백 무시) 걸린 곳 %d %s" % (
                k + 2, r["corp_label"], r["fy"], len(hits), " / ".join(hits[:6])))
            if any(re.search(r"겸직|파견|출향|전출|전적|겸무", h) for h in hits):
                fail("B 줄 %d: keyword 「없음」인데 Ⅷ 에 요청 키워드(공백 끼어 있는 꼴 포함)가 있음" % (k + 2))
    # B 키워드 누락(공백·칸 줄바꿈이 끼어 생성기 낱말 검색에 안 걸린 줄)
    missed = []
    for rc, L in lst.items():
        md = md_of(rc)
        if md is None:
            continue
        r8 = md.chap("VIII")
        if not r8:
            continue
        brows = [vnorm(r["source_text"]) for r in data["B"] if r["rcept_no_or_url"] == rc]
        for i in range(r8[0], r8[1]):
            for kw in ("겸직", "파견", "출향", "전출", "전적", "겸무"):
                if kw in md.vl[i] and kw not in md.L[i]:
                    ctx = md.vl[i]
                    if re.search(r"전적으로|전적인|사전적|완전적|전출입", ctx):
                        continue
                    if not any(md.vl[i] in b or b in md.vl[i] for b in brows if b):
                        missed.append("%s FY%s %s md%d %s「%s」" % (L["label"], L["fy"], rc, i + 1, kw, ctx[:50]))
    say("- B: 공백·칸 줄바꿈이 낱말 사이에 끼어 원래 검색에 안 걸렸을 줄(공백 무시 검색으로만 걸리고 B 에 없는 줄): %d" % len(missed))
    for x in missed:
        say("    %s" % x)
        fail("B 키워드 누락 가능: " + x)
    # A reason_text
    rs = []
    REASON = r"겸직사유|겸직의사유|겸직이유|겸직목적|겸임사유|겸직하는사유|겸직승인|겸직을통해|겸직함으로|위하여겸직|위해겸직|겸직하게된|겸직배경|겸직의필요"
    for rc, L in lst.items():
        md = md_of(rc)
        if md is None:
            continue
        for i, v in enumerate(md.vl):
            mm = re.search(REASON, v)
            if mm:
                rs.append("%s FY%s %s md%d「%s」" % (L["label"], L["fy"], rc, i + 1, v[max(0, mm.start() - 20): mm.end() + 30]))
    say("- A reason_text(353행 모두 「문서에 없음」): 세 회사 사업보고서 %d개(본·정정) 전체를 넓은 검색어(%s, 공백 무시)로 다시 찾음 — 걸린 줄 %d" % (
        len([1 for rc in lst if md_of(rc)]), REASON.replace("|", "·"), len(rs)))
    for x in rs[:20]:
        say("    %s" % x)
    say("")

    # ---------------------------------------------------------------- (j) 금지 낱말
    say("## (j) 기능 분류·겸직 이유 추정 낱말(note 전수 — source_text 는 원문 그대로라 대상 아님)")
    BAN = re.compile(r"때문|으로 보임|것으로 보|추정|기능 분류|리스크 기능|재무 기능|위해 겸직|목적으로 겸직|이유로")
    nb = 0
    for T in "ABD":
        for k, r in enumerate(data[T]):
            m = BAN.search(r["note"])
            if m:
                nb += 1
                fail("%s 줄 %d: note 에 추정·분류 낱말 「%s」" % (T, k + 2, m.group(0)))
    say("- 걸린 행 %d (검색어 때문·으로 보임·것으로 보·추정·기능 분류·리스크 기능·재무 기능·위해 겸직·목적으로 겸직·이유로)" % nb)
    say("")

    wave6(data, say, fail, CORPS)          # (15차 wave6) 새 원문 대조 규칙·고침 점검
    say("## 사람이 읽고 적은 것(검증자 판단, 2026-11-03 KST)")
    for x in REVIEW:
        say(x)
    say("")
    say("## 결과")
    say("실패 %d건 → exit %d" % (len(FAIL), 1 if FAIL else 0))
    os.makedirs(os.path.dirname(OUTTXT), exist_ok=True)
    return OUT


if __name__ == "__main__":
    main()
    txt = "\n".join(OUT) + "\n"
    open(OUTTXT, "w", encoding="utf-8").write(txt)
    print("verify15_bs_g2: 실패 %d건 → %s" % (len(FAIL), OUTTXT))
    sys.exit(1 if FAIL else 0)
