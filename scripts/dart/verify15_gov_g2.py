# -*- coding: utf-8 -*-
"""15차 검증 — 연차보고서 조각 g2(메리츠·iM·BNK·JB·한국투자): dart_out/ops15/조각/A_gov_g2.csv·B_gov_g2.csv.

인자 없이 실행 → 결과 dart_out/ops15/verify15_gov_g2.txt. 문제 없으면 exit 0, 하나라도 있으면 exit 1.
`python3 scripts/dart/verify15_gov_g2.py`

대조:
 (a) source_text(와 reason_text 가 「문서에 없음」이 아니면 그것도)가 그 행 원문(새로 받은 PDF 쪽 텍스트 md 「## p.N」,
     또는 6차 섹션 글 kit56/연차보고서_섹션.csv 본문)의 한 곳에 이어서 그대로 있는지 — 15차 새 원문 대조 규칙:
     「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 텍스트」 안에 이어서 있어야 함(PDF·6차 섹션 출처라 「|」는 지우지 않음).
     「 … 」·「 | 」 같은 생략·이음 표시가 든 행은 실패.
     PDF 추출 글에 섞인 보이지 않는 제어문자(U+0000~U+001F 중 줄바꿈·탭 말고)만은 생성기가 지울 수 있음 — 그런 행(「제어문자만 다름」)은
     note 에 「제어문자 지움」이 있어야 함(없으면 실패).
     JB FY2019(PDF 글자층 깨짐)의 판독 행은 글자층과 대조할 수 없으므로 note 의 판독 표지·아래 VISUAL(쪽 그림을 보고 적은 글)·
     글자층에서 그 자리를 가리키는 꼴(layer)로 대조.
 (b) page 가 그 글이 있는 위치인지(「p.N」 쪽, 「시작페이지 n 섹션 안(「제목」, chunk c)」). 틀리면 실제 위치를 찾아 적음.
 (c) 열 이름·utf-8-sig·필수 칸(출처·page·collected_at·doc_name 등) 빈칸 0, 출처·문서명·수집일이 목록과 같은지, 제어문자 없는지,
     원문 md(dart_out/ops15/원문/A|B/<회사>__FY<fy>__연차보고서.md)에 그 글이 있고 원문 md 의 각 절이 원문과 같은지.
 (d) 키·비밀값 문자열 없음.
 그리고 「문서에 없음」 반박 시도(A reason_text, B keyword 없음 행, JB FY2019 글자층 「?직」 꼴)를 다시 돌려 판정표와 맞댐.
"""
import csv
import functools
import glob
import hashlib
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
csv.field_size_limit(10 ** 9)
KST = timezone(timedelta(hours=9))

OPS = os.path.join("dart_out", "ops15")
FRAG = {"A": os.path.join(OPS, "조각", "A_gov_g2.csv"), "B": os.path.join(OPS, "조각", "B_gov_g2.csv")}
LIST15 = os.path.join(OPS, "연차보고서15_목록_g2.csv")
SEC6 = os.path.join(OPS, "kit56", "연차보고서_섹션.csv")
FILES6 = os.path.join("handoff", "연차보고서_파일목록.csv")
GOVLIST = os.path.join("scripts", "dart", "data", "governance_list.csv")
TXT = os.path.join("dart_out", "text", "ops15")
RAW = {"A": os.path.join(OPS, "원문", "A"), "B": os.path.join(OPS, "원문", "B")}
GEN = os.path.join("scripts", "dart", "gov15_g2_extract.py")
OUT = os.path.join(OPS, "verify15_gov_g2.txt")
CO = ("메리츠금융지주", "iM금융지주", "BNK금융지주", "JB금융지주", "한국투자금융지주")
COLS = {
    "A": ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime", "concurrent_company",
          "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text", "rcept_no_or_url", "page", "note",
          "doc_name", "collected_at"],
    "B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"],
}
REQ = {"A": ["corp_label", "fy", "reason_text", "doc_kind", "source_text", "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
       "B": ["corp_label", "fy", "keyword", "doc_kind", "source_text", "rcept_no_or_url", "page", "doc_name", "collected_at"]}
NONE = "문서에 없음"
PANDOK = "(판독)"     # 15차 새 규칙: JB FY2019 판독 행 note 맨 앞
JB19_URL_KEY = ("JB금융지주", "2020", "본공시")

# ── JB FY2019 판독 행: 15차 검증 때 쪽 그림(pymupdf 110~200dpi, venv python -I)을 눈으로 보고 적은 글 ──
#    (page, person, concurrent_company) → (그림에서 읽은 글, 글자층에서 그 자리를 가리키는 꼴)
VISUAL = {
    (62, "최정수", "법무법인 세줄"): ("3) 현재 겸직 업무 법무법인 세줄 대표변호사 전북은행(자회사) 사외이사", r"3\) 현재 \S직 업무"),
    (62, "최정수", "전북은행"): ("3) 현재 겸직 업무 법무법인 세줄 대표변호사 전북은행(자회사) 사외이사", r"3\) 현재 \S직 업무"),
    (65, "김상국", "광주은행"): ("3) 현재 겸직 업무 광주은행(자회사) 사외이사", r"3\) 현재 \S직 업무"),
    (68, "유관우", "김·장 법률사무소"): ("3) 현재 겸직 업무 김·장 법률사무소 고문(現)", r"3\) 현재 \S직 업무"),
    (74, "이상복", "동아회계법인"): ("3) 현재 겸직 업무 동아회계법인 파트너(現)", r"3\) 현재 \S직 업무"),
    (24, "이광철", "JB우리캐피탈"): ("ㆍ2018. 03. 23(JB우리캐피탈 겸직 2014. 03. 19) ~ 2019. 03. 39.", r"직\s*2014\.\s*03\.\s*19\)"),
    (187, "", "은행자회사"): ("2016년 지주회사 및 은행자회사 위험관리책임자(CRO) 겸직에 따라 리스크관리협의회의 원활한 회의진행을 위하여 "
                          "은행자회사 리스크관리부장을 동 협의회 위원으로 보강하는 리스크관리협의회규정 개정을 2016년 2월 개최된 "
                          "2016년도 제2차 위험관리위원회에서 결의하였으며,", r"위험관리책임자\(C\S?O\)\s*\S직에"),
}
# 후보 칸의 성명 대조: 그 쪽 앞 후보 양식(글자층에서 성명은 읽힘)
VISUAL_NAME_PAGES = {"최정수": 61, "김상국": 64, "유관우": 67, "이상복": 73}

# ── 「문서에 없음」 반박 판정표(15차 검증 때 후보 글을 읽고 정함). 판정이 없는 후보가 나오면 exit 1 ──
REASON_RULES = [
    (r"사외이사는겸직가능", "자회사 사외이사 겸직 가능 여부(허용) 서술 — 겸직 사유 글 아님"),
    (r"겸직위반사례|겸직사유발생시", "겸직 위반 사례 보고·「겸직사유 발생 시 사전통지」 요구 — 「겸직사유 발생」은 겸직이 생긴다는 뜻, 사유 글 아님"),
    (r"현재겸직업무.{0,3}는영리를목적으로", "작성기준(「현재 겸직 업무」의 뜻) — 사유 글 아님"),
    (r"임직원겸직및업무위탁|임직원겸직또는업무위탁", "내부규범 조문(임직원 겸직·업무위탁 평가·관리) — 사유 글 아님"),
    (r"겸직하고있는비상임이사제외", "평가 대상에서 겸직 비상임이사 제외 — 사유 글 아님"),
    (r"위원회겸직제한|겸직제한내용", "감사위원의 위험관리위원회 겸직 제한(위원회끼리) — 사유 글 아님"),
    (r"\(CRO\)겸직에(겸직에)?따라|리스크관리책임자겸직에따라", "CRO 겸직에 따른 협의회 위원 보강 — 겸직의 결과 서술, 겸직 사유 아님(6차 JB FY2025 본공시는 글자가 겹쳐 「겸직에겸직에따라따라」)"),
    (r"겸직제한요건|임직원을겸직하는경우", "법령 조문·겸직제한요건 심사표 — 사유 글 아님"),
    (r"겸직사항에대해위반|겸직사항없으며", "관련법 겸직사항 위반 없음 확인 — 사유 글 아님"),
    (r"겸직임직원보수배분", "보수위원회의 겸직 임직원 보수 배분 역할 — 사유 글 아님"),
    (r"겸직대표이사의이해상충방지를위하여의결권제한", "의결권 제한의 이유 — 겸직 사유 아님"),
    (r"이사회의장을겸직함에따라", "대표이사의 이사회 의장 겸직(지주 안 직위끼리)에 따른 선임사외이사 선임 — 겸직 사유 아님"),
    (r"기타비상무이사겸직.{0,120}추천사유", "(판단) 「추천사유」는 이사 후보 추천 사유 — 겸직 사유로 보지 않음"),
    (r"겸직임원의업무수행비율", "성과평가에서 겸직 임원 업무수행비율 반영 — 사유 글 아님"),
    (r"겸직추가된임원평가대상자추가|겸직추가된임원", "평가 대상 추가(규정 개정 내용) — 사유 글 아님"),
    (r"자회사간겸직중인이사", "이해상충 방지 장치 서술 — 사유 글 아님"),
    (r"\(불참\)사유|불참사유", "이사회·위원회 참석표의 「참석여부 및 (불참)사유」 칸과 「겸직임원 보수결정(안)」·「겸직해제 경영진 …」 안건 — 사유 글 아님"),
]
REASON_NEAR = re.compile(r"(겸직|겸임|겸무).{0,45}(위하|위해|위한|통해|통하|목적|필요|사유|이유|효율|시너지|일관|연계|제고|강화|때문|취지)"
                         r"|(위하여|위해|위한|목적으로|필요|사유|이유|효율|시너지|일관성|연계|제고|강화|취지).{0,45}(겸직|겸임|겸무)")
B_BROAD = re.compile(r"겸|파\s*견|출\s*향|전\s*출|전\s*적|전\s*입|전\s*보|인사\s*교류|인\s*력|인\s*원|직\s*원\s*수|임직원\s*수|\d+\s*명")
B_RULES = [
    (r"^(인원|인원수|임직원수|\d+명)$", "인원 숫자 표(변동보상 대상자 인원·임직원수(C)) — 겸직·파견 등 키워드 문장 아님"),
    (r"^전보$", "「전보」 = 통지 수단(모사전송, 전보, 등기우편) — 오검출"),
]
# JB FY2019 글자층 「?직」 꼴 — 쪽마다 판정(그림으로 확인한 쪽은 「그림 확인」)
JB19_LAYER = re.compile(r"[^\s가-힣0-9.,()\-·:;]직(?!금|보수|업)|겸|파견|출향|전출|전적")
JB19_PAGES = {
    14: "그림 확인: 감사위원회 위원의 위험관리위원회 겸직 제한(위원회끼리) — 행 아님",
    20: "그림 확인: 사외이사 소개 「- 전북은행 사외이사 겸직」(최정수)·「- 광주은행 사외이사 겸직」(김상국) — 후보 칸 행 note 에 적음",
    24: "그림 확인: 「(카) 사외이사 이광철 : 2019. 3. 23 퇴임」 재임기간 「JB우리캐피탈 겸직」 — A 판독 행",
    30: "그림 확인: 의결안건 주석 「감사위원회 위원의 위험관리위원 겸직 금지」 — 행 아님",
    55: "그림 확인: 자격요건 표 「금융사지배구조법 제10조(겸직제한)」 칸 — 법 조문 제목, 행 아님",
    59: "그림 확인: 김대곤 후보 「3) 현재 겸직 업무 해당사항 없음」 — 행 아님",
    62: "그림 확인: 최정수 후보 「3) 현재 겸직 업무」 — A 판독 행 2",
    65: "그림 확인: 김상국 후보 「3) 현재 겸직 업무」 — A 판독 행",
    68: "그림 확인: 유관우 후보 「3) 현재 겸직 업무」 — A 판독 행",
    71: "그림 확인: 표현명 후보 「3) 현재 겸직 업무 해당사항 없음」 — 행 아님",
    74: "그림 확인: 이상복 후보 「3) 현재 겸직 업무」 — A 판독 행",
    88: "글자층 꼴만 봄: 「제10조 (?직제한)」 — p.55 와 같은 법 조문 제목 칸으로 봄(판단)",
    90: "글자층 꼴만 봄: 「제10조 (?직제한)」 — 법 조문 제목 칸으로 봄(판단)",
    92: "글자층 꼴만 봄: 「제10조 (?직제한)」 — 법 조문 제목 칸으로 봄(판단)",
    127: "그림 확인: 김대곤 사외이사 활동 서술 「감사위원의 위험관리위원회 겸직 제한 사항」 — 위원회끼리, 행 아님",
    136: "그림 확인: 최정수 충실성 문단 「(자회사등은 제외/現 전북은행 사외이사 겸직)」 — 후보 칸 행 note 에 적음",
    138: "그림 확인: 김상국 충실성 문단 「(자회사등은 제외/現 광주은행 사외이사 겸직)」 — 후보 칸 행 note 에 적음",
    187: "그림 확인: 「지주회사 및 은행자회사 위험관리책임자(CRO) 겸직에 따라」 — A·B 판독 행",
    286: "그림 확인: 위원회 구성 조문 「자회사 상근임원을 겸직하고 있는 이사는 제외한다」 — 위원회 구성 규정, 행 아님",
    303: "그림 확인: 「중도퇴직」 — 오검출",
}
# 이번 검증에서 고친 것(생성기 scripts/dart/gov15_g2_extract.py 에 넣고 다시 돌림)
FIXES = [
    "(15차 6파동) PDF 추출 글의 보이지 않는 제어문자(U+0001 등)를 생성기가 지운 35행(A 32·B 3) note 에 「제어문자 지움(…)」을 넣음(clean() 이 지웠는지 표시).",
    "(15차 6파동) JB FY2019 판독 8행(A 7·B 1) note 맨 앞을 「(판독) PDF 글자층 깨짐 — 쪽 그림을 보고 옮김」으로 바꿈.",
    "(15차 6파동) 한국투자 오태균 FY2023(p.51·p.53)·FY2024(6차 시작페이지 39)·FY2025(6차 시작페이지 40, 4곳) 행 note 에 후보제안자 경력란 "
    "「2022.03 ~ 현재 / (겸) 한국투자증권 기타 비상무이사」 위치를 적고, 이강행 행처럼 concurrent_since 를 그 경력란의 「2022.03」으로 채움((판단) 같은 겸직이라 행은 더하지 않음).",
    "(15차 6파동) 이 스크립트를 새 원문 대조 규칙(공백·줄바꿈만 무시, 「|」 안 지움, 생략·이음 표시 실패, 제어문자 지운 행은 note 「제어문자 지움」 필수, "
    "판독 표지는 note 맨 앞 「(판독)」)으로 고침.",
    "JB FY2019 판독 5행 note 맨 앞에 「판독(PDF 글자층 깨짐 — 쪽 그림을 보고 옮김)」을 넣음(전에는 「(판단) … 쪽 그림을 눈으로 보고 옮겨 적은 것」만 있었음). "
    "5행 모두 쪽 그림(p.62·65·68·74, 150~200dpi)과 다시 맞대 글자가 같음을 확인.",
    "JB FY2019 B 「확인 불가」(source_text 「문서에 없음」, page 빈칸) 1행을 반박: 글자층에서 「겸」 자리가 깨진 「?직」 꼴을 찾아 쪽 그림으로 보니 p.187 에 "
    "「지주회사 및 은행자회사 위험관리책임자(CRO) 겸직에 따라 …」(FY2020~2025 보고서와 같은 연혁 글)가 있어 B 「겸직」 판독 행으로 바꿈.",
    "같은 p.187 글을 A 에도 판독 행으로 더함(FY2020~2025 의 같은 CRO 겸직 행과 같은 꼴, 성명 없음).",
    "같은 찾기에서 p.24 퇴임 사외이사 이광철 재임기간 「(JB우리캐피탈 겸직 2014. 03. 19)」을 찾아 A 판독 행으로 더함(겸직 직위·시작일은 비움, note (판단)).",
    "JB FY2019 후보 칸 행 note 의 「같은 문서의 다른 겸직 서술은 글자 깨짐으로 확인 못 함」을 찾은 쪽 목록(p.20·24·136·138·187 등)과 남은 한계로 바꿈. "
    "최정수·김상국 행에 같은 겸직이 p.20·p.136/138 에도 있음(판독)을 적음.",
    "B 「문서에 없음」 행 page 빈칸 3행(BNK FY2021 보수체계 수정공시, BNK FY2024 보수체계 수정공시(6차), 한국투자 FY2019 보수체계 추가공시)에 "
    "찾은 범위(「p.1~p.N 전체(찾은 범위, PDF 쪽 — 해당 글 없음)」, 「6차 섹션 글 전체(…)」)를 넣고 note 에 넓은 검색어 반박 결과를 덧붙임.",
    "6차 섹션 행 page 칸의 섹션 제목에 섞여 있던 제어문자 U+0000(NUL)을 지움(JB FY2024·FY2025 「리스크관리위원회」 섹션 등).",
    "「(겸)」 약자 표기를 찾다가 JB FY2020 p.167·FY2021 p.195 리스크관리운영위원회 구성 표의 이승국 「지주사/전북/광주은행CRO(겸)」을 찾아 "
    "A 4행(겸직처 전북은행·광주은행 × 2개 연도)으로 더함(원문 대조는 위 (a)(b) 에 포함).",
]
# 고치지 않고 남긴 것
REMAIN = [
    "(a) 의 「제어문자만 다름」 행은 원문 쪽 글에 섞인 제어문자(U+0001 등)를 생성기가 지운 것만 다름 — 보이는 글자는 같아 그대로 둠(note 「제어문자 지움」).",
    "JB FY2019 PDF 는 글자층이 쪽마다 다르게 깨져 「겸」 자리 꼴로만 찾았음 — 파견·출향·전출·전적·겸무 및 「겸」 자리 꼴이 아닌 깨짐은 가릴 수 없음(312쪽 전부를 그림으로 읽지 않음; OCR 없음).",
    "한국투자 FY2023 p.51·p.53(2024 공시)과 6차 FY2024·FY2025 섹션의 사외이사 후보 「후보제안자 : 오태균 사장」 주요경력란 「2022.03 ~ 현재 (겸) 한국투자증권 기타 비상무이사」는 "
    "같은 해 오태균 「한국투자증권 비상임이사 겸임」 행(이사회 구성 서술)과 같은 겸직으로 보아(판단) 행을 더하지 않음(15차 6파동에서 그 위치는 note 에 적음).",
    "B 에는 「(겸)」 약자 자리(JB 이승국)를 더하지 않음 — 사용자 키워드(겸직·파견·출향·전출·전적·겸무) 낱말 그대로가 아니어서(판단).",
]


@functools.lru_cache(maxsize=None)
def norm(s):
    """15차 새 원문 대조 규칙(PDF·6차 섹션 출처): 공백·줄바꿈만 지움(「|」·<br> 는 지우지 않음)."""
    return re.sub(r"\s+", "", s or "")


@functools.lru_cache(maxsize=None)
def norm_cc(s):
    """공백·줄바꿈과 보이지 않는 제어문자(U+0000~U+001F)만 지움."""
    return re.sub(r"[\s\x00-\x1f]+", "", s or "")


JOIN_MARK = re.compile(r" … |…| \| ")


def md_blocks(s):
    """원문 md → [(문서명, 위치, 글)]. 「## 문서명 — 위치」 다음 첫 ```text … ``` 가 그 절 글."""
    lines = s.split("\n")
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("## ") and " — " in lines[i]:
            try:
                j = lines.index("```text", i)
                k = lines.index("```", j + 1)
            except ValueError:
                break
            out.append((lines[i][3:], "\n".join(lines[j + 1:k])))
            i = k + 1
        else:
            i += 1
    return out


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def kst(s):
    if s and s.endswith("+0000"):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S+0000").replace(tzinfo=timezone.utc).astimezone(KST).isoformat(timespec="seconds")
    return s or ""


class Src:
    def __init__(self):
        self.list15 = list(csv.DictReader(open(LIST15, encoding="utf-8-sig")))
        self.by_url = {r["파일_url"]: r for r in self.list15}
        self.pages = {}
        self.f6 = {r["파일명"]: r for r in csv.DictReader(open(FILES6, encoding="utf-8-sig")) if r["공시연도"]}
        self.gl = {r["저장 파일명"]: r for r in csv.DictReader(open(GOVLIST, encoding="utf-8-sig"))}
        self.sec = {}
        for r in csv.DictReader(open(SEC6, encoding="utf-8-sig")):
            if r["지주명"] in CO:
                self.sec.setdefault(r["파일명"], []).append(r)

    def md_path(self, lr):
        return os.path.join(TXT, "연차보고서__%s__%s__%s.md" % (lr["회사"], lr["공시연도"], lr["공시유형"]))

    def mpages(self, lr):
        p = self.md_path(lr)
        if p not in self.pages:
            s = open(p, encoding="utf-8").read()
            parts = re.split(r"^## p\.(\d+)(?: \(글자 없음\))?\n", s, flags=re.M)
            self.pages[p] = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
        return self.pages[p]

    @staticmethod
    def mname(lr):
        return "%s (%s, %s 게시)" % (lr["제목"], lr["공시유형"], lr["공시일"])

    def s_url(self, fn):
        u = self.f6.get(fn, {}).get("url", "")
        g = self.gl.get(fn, {})
        if "fildDownload" in u and "real_filename" in g.get("URL", ""):
            u = g["URL"]
        return u


def resolve(S, row):
    """→ ('M', 목록행) | ('S', 파일명) | (None, 이유)."""
    m = re.search(r"; 파일 (.+?)\)$", row["doc_name"])
    if m:
        fn = m.group(1)
        return ("S", fn) if fn in S.sec else (None, "6차 파일 %s 섹션 없음" % fn)
    lr = S.by_url.get(row["rcept_no_or_url"])
    return ("M", lr) if lr else (None, "URL 이 목록에 없음")


def find_in(text, src):
    if norm(src) in norm(text):
        return "strict"
    if norm_cc(src) in norm_cc(text):
        return "cc"
    return None


def main():
    S = Src()
    L = []          # 결과 줄
    bad = []        # 문제 목록
    now = datetime.now(KST).isoformat(timespec="seconds")
    L.append("# 15차 검증 — 연차보고서 조각 g2 (메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주)")
    L.append("실행: %s (KST) · 스크립트 scripts/dart/verify15_gov_g2.py · 생성기 %s md5 %s" % (now, GEN, md5(GEN)))
    L.append("대조 정규화(15차 새 원문 대조 규칙): 공백·줄바꿈만 무시(「|」 안 지움), 행 글 전체가 원문 한 곳에 이어서 있어야 함. 그 밖의 글자는 그대로 비교"
             "(PDF 추출 글의 보이지 않는 제어문자 U+0001 등을 생성기가 지운 행은 「제어문자만 다름」으로 따로 세고 note 「제어문자 지움」을 봄).")
    L.append("")
    rows = {}
    # ── (c) ──
    L.append("## (c) 열 이름·utf-8-sig·필수 칸·출처 목록 일치·제어문자")
    for t in ("A", "B"):
        raw = open(FRAG[t], "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rr = list(csv.DictReader(open(FRAG[t], encoding="utf-8-sig")))
        rows[t] = rr
        cols = list(rr[0].keys()) if rr else []
        L.append("- %s: %d행, md5 %s, BOM %s, 열 %s" % (os.path.basename(FRAG[t]), len(rr), md5(FRAG[t]), "있음" if bom else "없음",
                                                       "COMMON15 과 같음" if cols == COLS[t] else "다름 %s" % cols))
        if not bom:
            bad.append("%s BOM 없음" % t)
        if cols != COLS[t]:
            bad.append("%s 열 다름" % t)
        empty, meta_bad, ctrl, rng = [], [], [], []
        for i, r in enumerate(rr, 2):
            for c in REQ[t]:
                if not (r.get(c) or "").strip():
                    empty.append("%d행 %s" % (i, c))
            for c, v in r.items():
                if re.search(r"[\x00-\x08\x0b-\x1f\x7f]", v or ""):
                    ctrl.append("%d행 %s" % (i, c))
            if r["corp_label"] not in CO or not (2019 <= int(r["fy"] or 0) <= 2025):
                rng.append("%d행 %s FY%s" % (i, r["corp_label"], r["fy"]))
            if not re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$", r["collected_at"]):
                meta_bad.append("%d행 collected_at 꼴 %r" % (i, r["collected_at"]))
            kind, x = resolve(S, r)
            if kind == "M":
                exp = dict(corp_label=x["회사"], fy=str(int(x["공시연도"]) - 1), doc_name=S.mname(x), collected_at=x["fetched_at"])
            elif kind == "S":
                s0 = S.sec[x][0]
                exp = dict(corp_label=s0["지주명"], fy=str(int(s0["공시연도"]) - 1), rcept_no_or_url=S.s_url(x),
                           collected_at=kst(S.f6.get(x, {}).get("fetched_at", "")))
                if not r["doc_name"].startswith(S.f6.get(x, {}).get("제목", "\x00")):
                    meta_bad.append("%d행 doc_name 제목 다름" % i)
            else:
                meta_bad.append("%d행 출처 못 찾음(%s)" % (i, x)); continue
            for c, v in exp.items():
                if r[c] != v:
                    meta_bad.append("%d행 %s %r ≠ 목록 %r" % (i, c, r[c][:60], v[:60]))
        L.append("  필수 칸 빈칸 %d%s" % (len(empty), (" — " + ", ".join(empty[:10])) if empty else ""))
        L.append("  제어문자 든 칸 %d%s" % (len(ctrl), (" — " + ", ".join(ctrl[:10])) if ctrl else ""))
        L.append("  범위 밖 회사·FY %d%s" % (len(rng), (" — " + ", ".join(rng[:10])) if rng else ""))
        L.append("  rcept_no_or_url·doc_name·collected_at·회사·FY ↔ 연차보고서15_목록_g2.csv / 연차보고서_파일목록.csv: 다른 행 %d%s"
                 % (len(meta_bad), (" — " + "; ".join(meta_bad[:10])) if meta_bad else ""))
        dup = {}
        for i, r in enumerate(rr, 2):
            k = tuple(r[c] for c in COLS[t] if c != "note")
            dup.setdefault(k, []).append(i)
        dups = [v for v in dup.values() if len(v) > 1]
        L.append("  note 만 다른 겹친 행 %d묶음%s" % (len(dups), (" — " + str(dups[:5])) if dups else ""))
        bad += ["%s 필수빈칸 %s" % (t, e) for e in empty] + ["%s 제어문자 %s" % (t, e) for e in ctrl] + \
               ["%s 범위 %s" % (t, e) for e in rng] + ["%s 출처 %s" % (t, e) for e in meta_bad] + ["%s 겹침 %s" % (t, d) for d in dups]
    L.append("")

    # ── (a)(b) ──
    L.append("## (a) source_text·reason_text 원문 대조, (b) page 위치 대조")
    detail = []
    pand_rows = []
    for t in ("A", "B"):
        ok = cc = none = wrong = pg_ok = pg_bad = rs_n = rs_ok = 0
        pand = 0
        for i, r in enumerate(rows[t], 2):
            kind, x = resolve(S, r)
            if kind is None:
                continue
            if r["source_text"] == NONE:
                none += 1
                if kind == "M":
                    m = re.match(r"^p\.1~p\.(\d+) 전체", r["page"])
                    good = bool(m) and m.group(1) == x["쪽수"]
                else:
                    good = r["page"].startswith("6차 섹션 글 전체")
                if not good:
                    pg_bad += 1; bad.append("%s %d행 「문서에 없음」 page %r" % (t, i, r["page"]))
                else:
                    pg_ok += 1
                if "찾은 범위" not in r["note"]:
                    bad.append("%s %d행 「문서에 없음」 note 에 찾은 범위 없음" % (t, i))
                continue
            if kind == "M" and (x["회사"], x["공시연도"], x["공시유형"]) == JB19_URL_KEY:
                pand += 1
                pand_rows.append((t, i, r))
                continue
            texts = []
            if kind == "M":
                m = re.match(r"^p\.(\d+)$", r["page"])
                pages = S.mpages(x)
                if m and int(m.group(1)) in pages:
                    texts = [pages[int(m.group(1))]]
                others = lambda: ["p.%d" % p for p, tx in pages.items() if find_in(tx, r["source_text"])]
            else:
                m = re.match(r"^시작페이지 (\d+) 섹션 안\(「(.*)」, chunk (\d+)\)$", r["page"])
                if m:
                    texts = [s["본문"] for s in S.sec[x] if s["시작페이지"] == m.group(1) and s["chunk_seq"] == m.group(3)
                             and norm_cc(s["섹션제목_원문"]) == norm_cc(m.group(2))]
                others = lambda: ["시작페이지 %s chunk %s" % (s["시작페이지"], s["chunk_seq"]) for s in S.sec[x] if find_in(s["본문"], r["source_text"])]
            res = [find_in(tx, r["source_text"]) for tx in texts]
            if JOIN_MARK.search(r["source_text"]):
                bad.append("%s %d행 source_text 에 생략·이음 표시(「 … 」·「 | 」)" % (t, i))
            if "strict" in res:
                ok += 1; pg_ok += 1
            elif "cc" in res:
                cc += 1; pg_ok += 1
                if "제어문자 지움" not in r["note"]:
                    bad.append("%s %d행 제어문자를 지운 행인데 note 에 「제어문자 지움」 없음" % (t, i))
            else:
                wh = others()
                if wh:
                    pg_bad += 1
                    bad.append("%s %d행 page %r 에 없고 %s 에 있음" % (t, i, r["page"], ", ".join(wh[:3])))
                else:
                    wrong += 1
                    bad.append("%s %d행 source_text 원문에 없음(%s %s)" % (t, i, r["corp_label"], r["page"]))
            if t == "A" and r["reason_text"] != NONE:
                rs_n += 1
                if any(find_in(tx, r["reason_text"]) for tx in texts):
                    rs_ok += 1
                else:
                    bad.append("A %d행 reason_text 원문에 없음" % i)
        L.append("- %s: %d행(문서에 없음 %d, JB FY2019 판독 %d) — 글 대조 맞음 %d(그 가운데 제어문자만 다름 %d) / 틀림 %d, "
                 "page 맞음 %d / 틀림 %d, reason_text 대조 %d행 중 맞음 %d"
                 % (t, len(rows[t]), none, pand, ok + cc, cc, wrong, pg_ok, pg_bad, rs_n, rs_ok))
    L.append("")

    # ── JB FY2019 판독 ──
    L.append("## JB금융지주 FY2019(2020-03-05 본공시, PDF 글자층 깨짐) 판독 행")
    lr = [x for x in S.list15 if (x["회사"], x["공시연도"], x["공시유형"]) == JB19_URL_KEY][0]
    pages = S.mpages(lr)
    seen = set()
    for t, i, r in pand_rows:
        p = int(r["page"][2:]) if re.match(r"^p\.\d+$", r["page"]) else -1
        key = (p, r.get("person", ""), r.get("concurrent_company", ""))
        if t == "B":
            key = (p, "", "은행자회사")
        vis = VISUAL.get(key)
        msgs = []
        if not r["note"].startswith(PANDOK):
            msgs.append("note 맨 앞에 「(판독)」 없음")
        if not vis:
            msgs.append("VISUAL 판정 없음")
        else:
            if norm(vis[0]) != norm(r["source_text"]):
                msgs.append("그림에서 읽은 글과 다름")
            if not re.search(vis[1], pages.get(p, "")):
                msgs.append("글자층에 그 자리 꼴 없음")
            seen.add(key)
        nm = r.get("person", "")
        if nm in VISUAL_NAME_PAGES and nm not in pages.get(VISUAL_NAME_PAGES[nm], ""):
            msgs.append("앞 후보 양식(p.%d) 글자층에 성명 없음" % VISUAL_NAME_PAGES[nm])
        L.append("- %s %d행 %s %s %s: %s" % (t, i, r["page"], nm or "(성명 없음)", r.get("concurrent_company", r.get("keyword", "")),
                                            "맞음(그림 대조·판독 표지·글자층 자리)" if not msgs else "틀림 — " + "; ".join(msgs)))
        bad += ["JB19 %s %d행 %s" % (t, i, m) for m in msgs]
    L.append("  (그림: pymupdf 로 p.20·23·24·59·62·65·68·71·74·136·138·187·286 등을 110~200dpi 로 그려 눈으로 봄. 「3) 현재 겸직 업무」 칸 5건은 "
             "그림의 글과 source_text 가 공백·줄바꿈 말고 같음. 이광철 행의 「ㆍ」는 글자층 글자 그대로(그림에서는 가운뎃점).)")
    L.append("")

    # ── 원문 md ──
    L.append("## 원문 md(dart_out/ops15/원문/A|B/<회사>__FY<fy>__연차보고서.md) 대조")
    for t in ("A", "B"):
        miss, files = [], {}
        for i, r in enumerate(rows[t], 2):
            if r["source_text"] == NONE:
                continue
            path = os.path.join(RAW[t], "%s__FY%s__연차보고서.md" % (r["corp_label"], r["fy"]))
            if path not in files:
                files[path] = norm_cc(open(path, encoding="utf-8").read()) if os.path.exists(path) else None
            if files[path] is None:
                miss.append("%d행 파일 없음" % i)
            elif norm_cc(r["source_text"]) not in files[path]:
                kind, x = resolve(S, r)
                if not (kind == "M" and (x["회사"], x["공시연도"], x["공시유형"]) == JB19_URL_KEY):
                    miss.append("%d행 글 없음" % i)
                elif "## %s — %s" % (r["doc_name"], r["page"]) not in open(path, encoding="utf-8").read():
                    miss.append("%d행 판독 쪽 절 없음" % i)
        # 절 글 = 원문 글?
        blk_n = blk_bad = 0
        for path in sorted(set(glob.glob(os.path.join(RAW[t], "*__FY*__연차보고서.md")))):
            if not os.path.basename(path).split("__")[0] in CO:
                continue
            s = open(path, encoding="utf-8").read()
            for head, body in md_blocks(s):
                blk_n += 1
                src = None
                cut = [m.start() for m in re.finditer(" — ", head)]
                for c in cut[::-1]:
                    name, label = head[:c], head[c + 3:]
                    f = re.search(r"; 파일 (.+?)\)$", name)
                    if f:
                        lm = re.match(r"^시작페이지 (\d+) 섹션 안\(「(.*)」, chunk (\d+)\)$", label)
                        if lm:
                            cand = [x["본문"] for x in S.sec.get(f.group(1), []) if x["시작페이지"] == lm.group(1) and x["chunk_seq"] == lm.group(3)
                                    and norm_cc(x["섹션제목_원문"]) == norm_cc(lm.group(2))]
                            src = next((c2 for c2 in cand if norm_cc(c2) == norm_cc(body)), None)
                    else:
                        lr2 = [x for x in S.list15 if S.mname(x) == name]
                        if lr2 and re.match(r"^p\.\d+$", label):
                            src = S.mpages(lr2[0]).get(int(label[2:]))
                            src = src if src is not None and norm_cc(src) == norm_cc(body) else None
                    if src is not None:
                        break
                name, label = head, ""
                if src is None:
                    blk_bad += 1; bad.append("원문 md %s 절 「%s — %s」 글이 원문과 다름" % (os.path.basename(path), name[:40], label))
        L.append("- %s: source_text 가 원문 md 에 없는 행 %d%s; g2 원문 md 절 %d개 중 원문과 다른 절 %d"
                 % (t, len(miss), (" — " + ", ".join(miss[:10])) if miss else "", blk_n, blk_bad))
        bad += ["원문md %s %s" % (t, m) for m in miss]
    L.append("")

    # ── (d) ──
    L.append("## (d) 키·비밀값 문자열")
    scan = [FRAG["A"], FRAG["B"], GEN] + sorted(p for t in ("A", "B") for p in glob.glob(os.path.join(RAW[t], "*.md"))
                                               if os.path.basename(p).split("__")[0] in CO)
    pats = [r"crtfc_key\s*=\s*\w{8,}", r"DART_API_KEY\s*[=:]\s*['\"]?\w{8,}", r"(?<![0-9A-Fa-f])[0-9a-f]{40}(?![0-9A-Fa-f])",
            r"sk-ant-[\w-]{10,}", r"ghp_\w{20,}", r"github_pat_\w{20,}", r"AKIA[0-9A-Z]{16}", r"(?i)bearer\s+[\w.\-]{20,}",
            r"(?i)(api[_-]?key|secret|password|passwd|token)\s*[=:]\s*['\"]?[\w\-]{12,}"]
    envkey = os.environ.get("DART_API_KEY", "")
    hits = []
    for p in scan:
        s = open(p, encoding="utf-8-sig", errors="replace").read()
        for pat in pats:
            if re.search(pat, s):
                hits.append("%s: 꼴 %s" % (p, pat[:20]))
        if len(envkey) >= 8 and envkey in s:
            hits.append("%s: 환경변수 DART_API_KEY 값과 같은 글자" % p)
    L.append("- 검사 파일 %d개(조각 2·생성기·원문 md %d), 꼴 %d가지%s → 걸린 것 %d"
             % (len(scan), len(scan) - 3, len(pats), " + 환경변수 값 대조" if envkey else " (환경변수 DART_API_KEY 는 이 셸에 없음)", len(hits)))
    for h in hits:
        L.append("  " + h)
    bad += ["비밀값 " + h for h in hits]
    L.append("")

    # ── 「문서에 없음」 반박 ──
    L.append("## 「문서에 없음」 반박 시도")
    # A reason_text
    docs = []
    for lr in S.list15:
        for p, tx in S.mpages(lr).items():
            docs.append((S.mname(lr), "p.%d" % p, tx))
    for fn, secs in S.sec.items():
        for s in secs:
            docs.append((fn, "시작페이지 %s chunk %s" % (s["시작페이지"], s["chunk_seq"]), s["본문"]))
    cands = {}
    for dn, loc, tx in docs:
        c = re.sub(r"[\s\x00-\x1f]+", "", tx)
        for m in REASON_NEAR.finditer(c):
            w = c[max(0, m.start() - 60): m.end() + 60]
            key = re.sub(r"[^가-힣]", "", c[max(0, m.start() - 10): m.end() + 10])[:50]
            cands.setdefault(key, []).append((dn, loc, w))
    verdicts = {}
    unj = []
    for key, v in cands.items():
        vd = next((d for pat, d in REASON_RULES if any(re.search(pat, w) for _dn, _loc, w in v)), None)
        if vd is None:
            unj.append((key, v[0]))
        verdicts.setdefault(vd or "미판정", []).append((key, v))
    nA = sum(1 for r in rows["A"] if r["reason_text"] == NONE)
    L.append("- A reason_text 「문서에 없음」 %d/%d행: 5개사 연차보고서 전체(새 PDF 36건 쪽 글 + 6차 섹션 글)에서 「겸직·겸임·겸무」 앞뒤 45자 안에 "
             "「위하·위해·통해·목적·필요·사유·이유·효율·시너지·일관·연계·제고·강화·때문·취지」가 오는 글을 찾음 → 자리 %d곳, 글 묶음 %d개. 판정:"
             % (nA, len(rows["A"]), sum(len(v) for v in cands.values()), len(cands)))
    for vd, items in sorted(verdicts.items(), key=lambda x: -sum(len(v) for _k, v in x[1])):
        ex = items[0][1][0]
        L.append("  · %s — %d묶음 %d곳 (예: %s %s 「…%s…」)" % (vd, len(items), sum(len(v) for _k, v in items), ex[0][:30], ex[1], ex[2][40:110]))
    L.append("  → 겸직의 사유·이유·필요성을 적은 글은 없음: reason_text 「문서에 없음」 유지(반박 안 됨).")
    bad += ["A reason 미판정 후보 %s %s" % (k, v[:2]) for k, v in unj]
    # B 없음 행
    for i, r in enumerate(rows["B"], 2):
        if r["source_text"] != NONE:
            continue
        kind, x = resolve(S, r)
        texts = list(S.mpages(x).items()) if kind == "M" else [("시작페이지 %s chunk %s" % (s["시작페이지"], s["chunk_seq"]), s["본문"]) for s in S.sec[x]]
        hits_b = {}
        for loc, tx in texts:
            for m in B_BROAD.finditer(tx):
                k = re.sub(r"\s", "", m.group())
                k = re.sub(r"^\d+명$", "N명", k)
                hits_b.setdefault(k, []).append(loc if isinstance(loc, str) else "p.%d" % loc)
        judged = []
        for k, locs in hits_b.items():
            vd = next((d for pat, d in B_RULES if re.match(pat, k if k != "N명" else "1명")), None)
            if vd is None:
                bad.append("B %d행 반박 미판정 낱말 %s" % (i, k))
            judged.append("「%s」 %d곳(%s) → %s" % (k, len(locs), ",".join(sorted(set(locs))[:3]), vd or "미판정"))
        L.append("- B %d행 %s FY%s %s (keyword %s): 넓은 검색어 「겸·파견·출향·전출·전적·전입·전보·인사교류·인력·인원·직원수·임직원수·N명」 → %s"
                 % (i, r["corp_label"], r["fy"], r["doc_name"][:50], r["keyword"], "; ".join(judged) if judged else "걸린 것 없음")
                 + " → 「문서에 없음」 유지")
    # JB FY2019 글자층
    lr = [x for x in S.list15 if (x["회사"], x["공시연도"], x["공시유형"]) == JB19_URL_KEY][0]
    hp = sorted(p for p, tx in S.mpages(lr).items() if JB19_LAYER.search(tx))
    L.append("- JB FY2019 글자층 「?직」 꼴(「겸」 자리가 쪽마다 다른 글자로 깨짐; 퇴직금·직보수·직업 제외) 걸린 쪽 %d: %s"
             % (len(hp), ", ".join("p.%d" % p for p in hp)))
    for p in hp:
        vd = JB19_PAGES.get(p)
        L.append("  · p.%d %s" % (p, vd or "미판정"))
        if vd is None:
            bad.append("JB19 글자층 p.%d 미판정" % p)
    L.append("  → 전에 「확인 불가」(문서에 없음)였던 B 행은 p.187 판독 행으로 반박됨. 파견·출향·전출·전적·겸무는 글자가 쪽마다 다르게 깨져 "
             "글자 검색으로 가릴 수 없고 312쪽 전부를 그림으로 읽지는 않음(남은 한계).")
    L.append("")

    # ── 한국투자 오태균 경력란 「(겸)」 쪽(15차 6파동) ──
    L.append("## 한국투자 오태균 행 note 의 후보제안자 경력란 「(겸) 한국투자증권 기타 비상무이사」 위치")
    OT = re.compile(r"\(겸\)\s*한국투자증권\s*기타\s*비상무이사")
    for i, r in enumerate(rows["A"], 2):
        if r["person"] != "오태균" or r["fy"] not in ("2023", "2024", "2025"):
            continue
        kind, x = resolve(S, r)
        if kind == "M":
            pg = [p for p, tx in S.mpages(x).items() if OT.search(tx)]
            want = "p.%s(PDF 쪽)" % "·p.".join(str(p) for p in sorted(pg))
            ok = want in r["note"]
        else:
            hit = [(sx["시작페이지"], sx["chunk_seq"], len(OT.findall(sx["본문"]))) for sx in S.sec[x] if OT.search(sx["본문"])]
            want = "; ".join("시작페이지 %s, chunk %s) %d곳" % h for h in hit)
            ok = len(hit) == 1 and ("(시작페이지 %s, chunk %s) %d곳" % hit[0]) in r["note"]
        ok = ok and r["concurrent_since"] == "2022.03"
        L.append("- A %d행 FY%s %s: 원문에서 찾은 곳 %s — note·concurrent_since(2022.03) %s" % (i, r["fy"], r["page"][:40], want, "맞음" if ok else "틀림"))
        if not ok:
            bad.append("A %d행 오태균 note 의 (겸) 쪽 %s 또는 since 틀림" % (i, want))
    L.append("")

    # ── 고친 곳 ──
    L.append("## 이번 검증에서 고친 곳(생성기에 넣고 다시 돌려 조각·원문 md 를 새로 씀)")
    for f in FIXES:
        L.append("- " + f)
    L.append("")
    L.append("## 고치지 않고 남긴 것")
    for f in REMAIN:
        L.append("- " + f)
    L.append("")
    L.append("## 결과")
    if bad:
        L.append("문제 %d건 — exit 1" % len(bad))
        for b in bad[:200]:
            L.append("- " + b)
    else:
        L.append("문제 0건 — exit 0")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("문제 %d건 → %s" % (len(bad), OUT))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
