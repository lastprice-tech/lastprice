# -*- coding: utf-8 -*-
"""15차 검증 — 연차보고서 조각 g1(KB·신한·하나·우리·NH농협): A_gov_g1.csv·B_gov_g1.csv.

    python3 scripts/dart/verify15_gov_g1.py      # 인자 없음 → exit 0(통과)/1(실패), 결과 dart_out/ops15/verify15_gov_g1.txt

원문은 생성기(scripts/dart/ops15_gov_g1_extract.py)와 따로 읽어 대조한다(웹 요청·API 키 사용 없음).
  원문: FY2019~2023 = dart_out/text/ops15/연차보고서__<회사>__<공시연도>__<유형>.md(「## p.N」= PDF 쪽, 출처 목록
        dart_out/ops15/gov15_g1_work/download.json), FY2024·2025 = 6차 섹션 글 dart_out/ops15/kit56/연차보고서_섹션.csv
        (출처 목록 handoff/연차보고서_파일목록.csv), FY2025 쪽 대조는 13차 텍스트 zip 의 연차보고서__<회사>.md.
  (a) 모든 행 source_text(그리고 reason_text 가 「문서에 없음」이 아니면 그것도)가 그 행 출처 원문의 한 곳에 이어서 그대로 있는지
      — 15차 새 원문 대조 규칙: 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 텍스트」 안에 이어서 있어야 함.
      PDF·6차 섹션 출처라 「|」는 지우지 않음(원문에 없는 「 | 」를 넣은 행은 실패). 「 … 」 같은 생략·이음 표시가 든 행도 실패.
      PDF 출처 텍스트 = 「## p.N」 쪽 표지 줄만 뺀 쪽 글을 차례로 이은 것.
  (b) page: 「p.N」 → 그 글이 PDF 쪽 N 에서 시작, 「시작페이지 N 섹션 안」 → 시작페이지 N 인 6차 섹션 글 안,
      note 의 「각주 p.N」·「13차 텍스트(같은 PDF sha256) p.N」 도 그 쪽에 있는지. 「문서에 없음」 행은 page 「전체」.
  (c) 열 이름(COMMON15 순서)·utf-8-sig·필수 칸 빈칸 0, doc_name·rcept_no_or_url·collected_at·fy 가 출처 목록과 같음.
  (d) 키·비밀값 문자열 없음(DART_API_KEY 값은 환경변수에서 읽어 들어 있는지만 보고 값은 어디에도 쓰지 않음).
  더해서:
  (e) A 「손으로 고른 A_SPECS」 개별 겸직 54행: 겸직 회사·직위가 source_text 안에 있는지(전수), 사외이사 후보 「현재 겸직 업무」 칸은
      바로 앞 「후보자(의) 인적사항」 머리의 성명·출생연도가 그 행과 같은지(전수), 표본 15개는 사람이 원문을 읽고 근거 글을 적음
      (근거 글이 원문 그 자리에 있는지는 이 스크립트가 다시 찾음).
  (f) reason_text 가 든 행 전부(11행): 글자 대조 + 같은 문단(같은 사람 서술) 안인지(또는 note 「사유 위치 p.N」 쪽인지) + 사람이 읽은 판단.
  (g) B 에서 뺀 630문장(gov15_g1_work/B_제외문장.csv) 표본 30개(seed 20261103): 원문 그 쪽에 있는지 + 사람 판단.
  (h) 「문서에 없음」 반박 시도: A 30행·B 8행을 더 넓은 검색어(공백 무시)로 같은 문서에서 다시 찾음 — 걸린 글은 txt 에, 판단은 REVIEW.
  (i) reason_text 「문서에 없음」 개별 겸직 행(43): note 의 찾은 범위(파일·쪽 범위·검색어)와 걸린 줄 수를 원문에서 다시 셈.
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
A_CSV = os.path.join(FRAG, "A_gov_g1.csv")
B_CSV = os.path.join(FRAG, "B_gov_g1.csv")
WORK = os.path.join("dart_out", "ops15", "gov15_g1_work")
EXCL_CSV = os.path.join(WORK, "B_제외문장.csv")
DL_JSON = os.path.join(WORK, "download.json")
SEC_CSV = os.path.join("dart_out", "ops15", "kit56", "연차보고서_섹션.csv")
FILELIST = os.path.join("handoff", "연차보고서_파일목록.csv")
LIST_CSV = os.path.join("dart_out", "ops15", "연차보고서15_목록_g1.csv")
T13_ZIP = os.path.join("handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
ORIG = os.path.join("dart_out", "ops15", "원문")
GEN = os.path.join("scripts", "dart", "ops15_gov_g1_extract.py")
COLLECTOR = os.path.join("scripts", "dart", "ops15_gov_g1.py")
OUTTXT = os.path.join("dart_out", "ops15", "verify15_gov_g1.txt")
G1 = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]
NONE = "문서에 없음"
KST = timezone(timedelta(hours=9))
DOC_KIND = "지배구조 연차보고서"

COLS = {
    "A": ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
}
REQ_ALL = ["corp_label", "fy", "doc_kind", "source_text", "rcept_no_or_url", "page", "doc_name", "collected_at"]
REQ = {"A": ["reason_text"], "B": ["keyword"]}
TRUE_JEONJEOK = re.compile(r"(?<![가-힣])전적(?!으로|인|합)")

OUT, FAIL = [], []

# ======================================================================================================================
# 사람이 원문을 읽고 적은 것(검증하면서 고친 곳·손 대조·반박 판단). 근거 글이 원문 그 자리에 있는지는 아래 자동 대조가 다시 찾음.
# ======================================================================================================================
FIXES = [
    "### 15차 6파동 고친 곳(새 원문 대조 규칙 — 모두 생성기 scripts/dart/ops15_gov_g1_extract.py 에 넣고 build 를 다시 돌림, 두 번 돌려 md5 같음)",
    "- 원문 PDF 줄바꿈 자리에 원문에 없는 「 | 」를 넣은 38행(A 32: 사외이사 후보 「3) 현재 겸직 업무」 칸 신한 15·우리 12, 하나 리스크관리집행위원회 표 5 / "
    "B 6: 하나 FY2019~2023 「인원수 … 전출자」 표 머리 5·신한 FY2023 「당해년도 … 겸직 포함」 1) → 칸 사이를 원문 줄바꿈 그대로 둠(join table·collect_hits).",
    "- 표 행과 각주 주5 를 「 … 」로 이은 하나 5행(FY2019~2023 황효상·김주성) → 표의 그 사람 행부터 같은 쪽 각주 「주5) … 겸직」까지 원문에 이어진 글 전체"
    "(583~653자, 2,000자 이하 — 사이의 다른 위원 행·주1~주4 포함)를 줄바꿈 그대로 옮김(Doc.span_to). 각주는 겸직 사실(사유 아님)이라 reason_text 는 「문서에 없음」, 위치는 note 「각주 p.N」.",
    "- reason_text 「문서에 없음」 45행: 행 쪽 앞뒤 1쪽과 그 절(6차는 섹션 글 전체)에서 「사유」「겸직」「겸임」「선임」, 문서 전체에서 「겸직·겸임」과 「사유·선임」이 "
    "같은 줄·앞뒤 줄에 함께 있는 곳을 다시 찾음(걸린 줄 841, 판정은 gov15_g1_work/A_사유_재검색.csv). 신한 FY2019 장동기·정운진 2행은 같은 날(2019-12-19) "
    "제8회 임시이사회 결의 문장 「…겸직 사업부문 활성화를 위해 경영진 신규 선임에 관한 사항을 결의하였습니다」(p.25)를 reason_text 로 옮김((판단), note 「사유 위치 p.25」). "
    "남은 43행 note 에 찾은 범위(파일·쪽 범위·절·검색어·걸린 줄 수)를 적음.",
    "- 신한 FY2020 그룹디지털부문장 행 note: 「원문에 성명 없음」 → 이 문장에 성명 없음 + 같은 문서 p.161·p.164 의 「…신한DS 대표이사인 이성용 사장을 그룹 "
    "디지털사업부문장…」 위치(person 칸은 비워 둠).",
    "- 이 스크립트: 대조를 「공백·줄바꿈만 지움, 「|」 안 지움, 행 전체가 원문 한 곳에 이어서」로 바꾸고, 생략·이음 표시 검사·각주 쪽 검사·「사유 위치 p.N」 검사·"
    "(i) 찾은 범위 다시 세기를 더함. 고치기 전 조각(작업 사본)에 돌리면 [실패] 127(「 | 」·「 … 」 38행, 원문에 이어서 없음 34행, reason 찾은 범위 없음 45행 등)으로 잡힘.",
    "### (이전 검증 때) 고친 곳(모두 scripts/dart/ops15_gov_g1_extract.py 에 넣고 build 를 다시 돌림 — 고치기 전 조각 md5 A 335bf8a7… B 07af24f4…, "
    "고치기 전 생성기를 그대로 다시 돌리면 git HEAD 와 바이트까지 같음(결정적) 확인)",
    "- (a)(b)(c)(d) 자동 대조에서는 틀린 행 0 — 글자·쪽·열·출처·비밀값 모두 맞았음. 아래는 대조하면서 찾은 「원문 그대로이지만 문장이 잘렸거나 군더더기가 붙은」 "
    "행과 note 를 고친 것.",
    "- B 4행 source_text 문장 끝 잘림 → 원문 다음 줄까지 넣음(CUT_FIX): KB FY2024·FY2025(6차 섹션, 줄 14·16) 「…제출하는 겸직」 → 「…제출하는 겸직 임직원 제외)」, "
    "신한 FY2019 p.25(줄 17) 「…경영진 신규 선임에 관한」 → 「…선임에 관한 사항을 결의하였습니다」, NH FY2025 본공시(줄 124) 「…: 그룹임직원겸직에관한」 → "
    "「…: 그룹임직원겸직에관한 규정 일부개정규정」. 원인: sentence() 가 12자 미만 다음 줄을 표 칸으로 보고 끊음. 고친 뒤도 글자 대조·쪽 대조 맞음.",
    "- B 1행(NH FY2025 추가공시, 줄 127) source_text 끝에 붙은 쪽 바닥글 「NH농협금융지주 39」를 뗌(FOOTER_RE). 앞 글은 그대로.",
    "- A 4행 note(신한 FY2019·FY2021 성재호, FY2022 성재호·배훈 — 줄 17·28·37·38): 「사외이사 후보 추천 관련 사항 — 후보 본인 소명」 → 「감사위원 후보 추천 관련 사항"
    "(감사위원후보추천위원회 절 — 감사위원이 되는 사외이사 후보) — 「(사) 감사위원후보 본인 소명」…」. 원문 칸 머리가 「(사) 감사위원후보 본인 소명」이기 때문(표본 6).",
    "- gov15_g1_work/B_제외문장.csv 의 sent 칸이 300자에서 잘려 있었음(52행 — 키워드가 잘린 뒤에 있어 안 보이는 행 포함) → 전문으로 씀. 행 수·순서·범주는 같음.",
    "- 고친 뒤 조각: A·B 행 수 그대로(84·126), 바뀐 칸은 위 9행 뿐(git HEAD 와 칸 단위 비교). 원문 md(원문/A·B 의 g1 연차보고서 md)는 바뀌지 않음. "
    "고친 생성기를 두 번 돌려 A·B·제외 CSV md5 같음. 고치기 전 조각(git HEAD)에 이 스크립트를 돌리면 위 9행이 [실패]로 잡힘(대조 규칙 확인).",
]

# 손 대조 표본 15개 — 행 찾기 키: (회사, fy, person, holdco_title, concurrent_company)
#   ev: ("src", 정규식)  = source_text(공백·「|」 뺀 글) 안
#       ("before", 정규식, n) = 원문에서 source_text 시작 앞 n 글자(공백 뺀) 안
#       ("after", 정규식, n)  = 원문에서 source_text 끝 뒤 n 글자 안
#       ("page", 정규식, 쪽)  = 같은 문서 그 PDF 쪽 안
HAND_A = [
    dict(k=("KB금융지주", "2019", "", "데이터 총괄 집행임원", "KB국민은행"),
         ev=[("src", r"지주회사집행임원선임보고:데이터총괄집행임원\(KB국민은행데이터전략본부전무,KB국민카드데이터전략본부전무겸직\)"),
             ("before", r"□제8차이사회", 900)],
         j="KB 이사회 활동내역 「제8차 이사회」 보고 안건 원문이 지주회사 집행임원(데이터 총괄)이 KB국민은행·KB국민카드 데이터전략본부 전무를 "
           "겸직한다고 직접 적음 → 회사(KB국민은행·KB국민카드 2행)·직위 맞음. 성명은 원문에 없음(person 빈칸 맞음)."),
    dict(k=("KB금융지주", "2019", "", "연금본부장", "KB증권"),
         ev=[("src", r"연금본부장\(KB국민은행연금사업본부장,KB증권연금기획부장,KB손해보험연금기획부장겸직\)"),
             ("before", r"□제9차이사회", 1200)],
         j="같은 꼴(제9차 이사회 보고 안건) — 연금본부장이 KB국민은행 연금사업본부장·KB증권·KB손해보험 연금기획부장 겸직 → 3행 회사·직위 맞음."),
    dict(k=("신한금융지주", "2019", "진옥동", "비상임이사", "신한은행"),
         ev=[("before", r"⑬이사진옥동\(비상임이사\)", 1200), ("src", r"진옥동이사는신한은행은행장을겸직하고있습니다")],
         j="「⑬ 이사 진옥동 (비상임이사)」 절 끝 문장 — 지주 비상임이사 진옥동이 신한은행 은행장 겸직 → 사람·회사 맞음."),
    dict(k=("신한금융지주", "2019", "장동기", "부사장", NONE),
         ev=[("before", r"제5회이사회운영위원회", 400), ("src", r"GMS사업부문겸직부사장장동기")],
         j="이사회운영위원회 「이사 아닌 경영진 신규 선임」 추천 결과 목록의 「GMS사업부문겸직 부사장 장동기」 — 지주 부사장, 겸직 대상은 "
           "사업부문(회사명 원문에 없음 → concurrent_company 「문서에 없음」 맞음)."),
    dict(k=("신한금융지주", "2020", "", "그룹디지털부문장", "신한DS"),
         ev=[("src", r"지주회사와신한DS대표이사를겸직하는그룹디지털부문장을선임")],
         j="이사회 결의 안건 원문이 「지주회사와 신한DS 대표이사를 겸직하는 그룹디지털부문장」 → 회사·직위 맞음, 성명 원문에 없음."),
    dict(k=("신한금융지주", "2019", "성재호", "사외이사 후보", "성균관대학교"),
         ev=[("before", r"●성재호\(가\)후보자의인적사항①출생연도:1960년", 1500), ("before", r"\(사\)감사위원후보본인소명", 200)],
         j="감사위원후보추천위원회 「● 성재호」 후보 블록의 「(사) 감사위원후보 본인 소명」 칸 — 사람(1960년생) 맞음. 이 칸은 사외이사후보추천위원회가 "
           "아니라 감사위원후보추천위원회 절의 「감사위원후보 본인 소명」(감사위원이 되는 사외이사 후보 분리선임)이라 같은 꼴 4행의 note 를 고침(위 고친 곳)."),
    dict(k=("신한금융지주", "2020", "최경록", "사외이사 후보", "㈜CYS"),
         ev=[("before", r"4\.최경록가\.후보자의인적사항①출생연도:1966년", 3000), ("before", r"사\.사외이사후보본인소명", 200)],
         j="「4. 최 경 록 / 가. 후보자의 인적사항 ① 출생연도 : 1966년」 블록의 「사. 사외이사후보 본인 소명 3) 현재 겸직 업무」 → 사람·회사 맞음."),
    dict(k=("신한금융지주", "2024", "정상혁", "비상임이사", "신한은행"),
         ev=[("before", r"이사정상혁\(비상임이사\)", 1500), ("after", r"⑨이사진옥동\(사내이사\)", 200)],
         j="6차 섹션 「이사회 및 이사에 대한 평가」 글의 「이사 정상혁 (비상임이사)」 절(다음 절은 「⑨ 이사 진옥동 (사내이사)」) → 사람·회사 맞음."),
    dict(k=("하나금융지주", "2019", "황효상", "하나금융지주 리스크관리 담당임원", "하나은행"),
         ev=[("before", r"<당사리스크관리집행위원회구성주1,주2,주3>성명직위선임일주4비고", 80),
             ("page", r"주5\)하나은행리스크관리담당임원겸직", 228)],
         j="리스크관리집행위원회 구성 표 첫 행 「황효상 | 하나금융지주 리스크관리 담당임원주5 | … | 위원장」과 같은 쪽 각주 「주5) 하나은행 리스크관리담당임원 겸직」 "
           "→ 주5 가 붙은 행은 이 행 하나뿐이라 사람·회사 맞음."),
    dict(k=("하나금융지주", "2023", "김주성", "하나금융지주 리스크관리 담당 임원", "하나은행"),
         ev=[("before", r"<당사리스크관리집행위원회구성주1,주2,주3>성명직위선임일주4비고", 80),
             ("page", r"주5\)하나은행리스크관리담당임원겸직", 262)],
         j="같은 표 FY2023 판 — 「김주성 | 하나금융지주 리스크관리 담당 임원주5」 + 각주 주5 → 맞음(표에 하나은행 행이 따로 없음도 확인)."),
    dict(k=("하나금융지주", "2021", "박성호", "비상임이사 후보", "하나은행"),
         ev=[("src", r"박성호후보를하나은행대표이사은행장으로추천"), ("src", r"박성호후보를비상임이사로추천"),
             ("before", r"가\)후보제안자추천이유", 60)],
         j="그룹임원후보추천위원회 「후보 추천 사유 — 가) 후보 제안자 추천 이유」: 박성호를 하나은행 대표이사 은행장 후보이자 지주 비상임이사 후보로 추천 "
           "→ 사람·회사 맞음(행은 후보 단계 — holdco_title 「비상임이사 후보」 맞음)."),
    dict(k=("우리금융지주", "2021", "김홍태", "비상임이사", "예금보험공사"),
         ev=[("before", r"⑦이사김홍태", 40), ("src", r"現예금보험공사인사지원부\(파견\)부장으로재직중")],
         j="「⑦ 이사 김홍태」 절 — 비상임이사, 「現 예금보험공사 인사지원부 (파견)부장으로 재직 중」 → 사람·기관 맞음. FY2022 판은 2022.2 사임이고 "
           "약력에 「現」이 없어 행이 없는 것이 맞음."),
    dict(k=("우리금융지주", "2022", "박상용", "사외이사 후보", "연세대학교"),
         ev=[("before", r"③사외이사후보본인소명\(바\)임원후보추천위원회검토및의결결과박상용후보자에대한", 1200),
             ("after", r"3\)현재겸직업무해당사항없음", 2600),
             ("page", r"박상용사외이사사외이사\(리스크관리위원회위원\)有연세대학교경영학과명예교수", 177)],
         j="PDF 글 순서로는 이 칸이 「(3) 사외이사 후보 (윤인섭)」 인적사항 뒤에 오지만, 「③ 사외이사 후보 본인 소명」 머리가 박상용 절(「박상용 후보자에 대한 "
           "사외이사 추천…」 앞)에 있고, 윤인섭 자신의 칸은 그 뒤에 「3) 현재 겸직 업무 해당사항 없음」으로 따로 있으며, p.177 이사 표에 박상용 「연세대학교 "
           "경영학과 명예교수」 → 생성기 판단(박상용) 맞음."),
    dict(k=("우리금융지주", "2024", "박선영", "사외이사 후보", "우리벤처파트너스(주)"),
         ev=[("after", r"\(바\)임원후보추천위원회검토및의결결과박선영후보자에대한", 30)],
         j="6차 섹션 「사외이사 후보 추천」 글 — 칸 바로 뒤가 「(바) … 박선영 후보자에 대한 사외이사 추천」이고 앞 머리 「사외이사 후보 (박선영)」 "
           "출생연도 1982 → 사람·회사(동국대학교·우리벤처파트너스 2행) 맞음."),
    dict(k=("우리금융지주", "2025", "윤인섭", "사외이사 후보", "우리아메리카은행"),
         ev=[("after", r"\(바\)임원후보추천위원회검토및의결결과윤인섭후보자에대한", 30)],
         j="6차 섹션(2026 공시) — 칸 뒤 「윤인섭 후보자에 대한」, 앞 머리 「사외이사 후보 (윤인섭)」 출생연도 1956 → 맞음. FY2024 판 윤인섭 칸은 "
           "「해당사항 없음」이라 행 없음도 맞음."),
]

# reason_text 9행 판단(행 찾기 키: 회사, fy, person) — 자동: 글자 대조 + source 와 같은 문단(거리) 확인
HAND_R = {
    ("신한금융지주", "2019", "진옥동"): "source 바로 다음 문장(같은 「이사 진옥동 (비상임이사)」 절) — 은행장을 비상임이사로 선임하는 이유를 원문이 직접 적음.",
    ("신한금융지주", "2020", "진옥동"): "같음(FY2020 판).",
    ("신한금융지주", "2021", "진옥동"): "같음(FY2021 판).",
    ("신한금융지주", "2022", "진옥동"): "같음(FY2022 판, source 는 「2022년 말까지 … 겸직하였습니다」).",
    ("신한금융지주", "2023", "정상혁"): "같은 문장 뒷부분(「…겸직하고 있으며, 창립이래 … 선임하고 있습니다」) — source 가 문장 전체, reason 이 그 안의 이유 부분.",
    ("신한금융지주", "2024", "정상혁"): "같음(6차 섹션 글, 낱말 사이 여러 칸 공백 원문대로).",
    ("신한금융지주", "2025", "정상혁"): "같음(6차 섹션 글, 2026 공시).",
    ("하나금융지주", "2021", "박성호"): "같은 문장 가운데 「그룹 내 회사의 비중 및 이익 측면에서 은행장이 지주회사 비상임이사를 겸직하는 것이 … 판단하여」 "
                                     "— 원문이 겸직 판단 이유를 직접 적음.",
    ("우리금융지주", "2019", ""): "특정 겸직 건이 아닌 이사회 요청 서술 — source 와 reason 이 같은 문장(생성기 (판단) 표시 그대로 둠).",
    ("신한금융지주", "2019", "장동기"): "15차 다시 찾기(「사유」「겸직」「겸임」「선임」)로 더함: source(p.168 이사회운영위원회 2019-12-19 추천 결과 「GMS사업부문겸직 "
                                     "부사장 장동기」)와 같은 날 제8회 임시이사회 「이사 아닌 경영진 선임의 건」 결의 문장(p.25) 「…겸직 사업부문 활성화를 위해 "
                                     "경영진 신규 선임에 관한 사항을 결의하였습니다」 — 같은 선임 건의 목적을 원문이 직접 적음(생성기 (판단) 표시). 같은 문장이 p.51 에도.",
    ("신한금융지주", "2019", "정운진"): "같음(「GIB사업부문겸직 부사장 정운진」).",
}

# B 제외 표본 30(seed 20261103) 판단: 번호(제외 CSV 0부터) → (범주, 판단)
HAND_X = {
    30: ("X규정", "신한 지배구조 내부규범 제77조(준법감시인·위험관리책임자 겸직 금지) 조문"),
    55: ("X자격요건", "사외이사 재선임 후보의 「선임 이후 타회사 추가 겸직 사실 없음」 — 후보 충실성 문구"),
    75: ("X자격요건", "사외이사후보 평가 표의 충실성 칸(「선임 이후 겸직사실 변동 없으며」)"),
    91: ("X자격요건", "사외이사후보 평가 표의 충실성 칸(「다른 회사 겸직사실 없음」)"),
    117: ("X자격요건", "사외이사후보 평가 표 충실성 칸 + 다음 결의 머리(문장 자르기로 붙음) — 조직·인력 서술 아님"),
    120: ("X자격요건", "사외이사 후보 본인 소명 「현재 겸직 업무」 칸 — 개별 겸직은 A 행(신한 FY2020 진현덕 ㈜페도라)으로 들어 있음"),
    136: ("X규정", "규정 단서 「다만, 겸직 비상임이사의 경우에는 그러하지 아니하다.」"),
    147: ("X자격요건", "후보 본인 소명 칸 「겸직사항 없음」"),
    166: ("X규정", "제77조 조문(추가공시 사본)"),
    182: ("X자격요건", "본인 소명 칸 — A 행(신한 FY2021 최경록 ㈜CYS)으로 들어 있음"),
    183: ("X자격요건", "본인 소명 칸 — A 행(신한 FY2021 허용학 First Bridge Strategy Ltd.)으로 들어 있음"),
    193: ("X규정", "정관 부칙 조문(설립 당시 최초 대표이사 회장·사장 1인 겸직)"),
    198: ("X규정", "그룹 내부통제 규정 조문(그룹사 사이 임직원 겸직·업무위탁 평가 의무)"),
    209: ("X자격요건", "본인 소명 칸 「겸직사항 없음」"),
    223: ("X규정", "규정 단서 「다만, 자회사등의 사외이사 겸직의 경우에는 그러하지 아니하다.」"),
    248: ("X자격요건", "사외이사 재선임 후보 충실성 문구"),
    260: ("X규정", "그룹 내부통제 규정 조문(FY2022 판)"),
    318: ("X자격요건", "사외이사 후보 소극적 요건(결격사유) 확인 서술"),
    320: ("X자격요건", "사외이사 후보 직무공정성 요건 칸(「후보자 겸직 사실 없어 이해상충 발생가능성 낮음」)"),
    328: ("X규정", "규정 단서(FY2024 판)"),
    332: ("X규정", "제77조 조문(FY2024 판)"),
    347: ("X자격요건", "직무공정성 요건 칸(추가공시)"),
    463: ("X자격요건", "우리 FY2024 추가공시 본인 소명 칸 — 본공시 A 행(정찬형 우리은행 사외이사)과 같은 글"),
    464: ("X자격요건", "본인 소명 칸 「해당사항 없음」"),
    465: ("X자격요건", "우리 FY2024 추가공시 본인 소명 칸 — 본공시 A 행(이은주)과 같은 글"),
    513: ("X규정", "하나 그룹내부통제규정 제18조 ① 조문"),
    520: ("X규정", "규정 조문 「회사는 임원에 대하여 외부에 위탁하여 파견연수를 실시할 수 있다.」 — 연수이지 인력 파견 아님"),
    535: ("X규정", "성과평가 규정 조문(겸직 임원 장기성과급 부여·평가 원칙)"),
    541: ("X경력", "사외이사 후보 김홍진 경력 속 「OECD 경제국 파견근무」"),
    542: ("X경력", "같은 사람 적격성 서술 속 경력"),
}
EXCL_SEED, EXCL_N = 20261103, 30

REVIEW = [
    "### 손 대조 요약",
    "- A 표본 15개(위 목록): 15개 모두 원문에서 그 사람·그 회사(또는 성명 없는 직위)가 맞음. 근거 글은 자동으로 다시 찾음.",
    "- reason_text 11행: 11행 모두 글자 그대로 원문 한 곳에 있음. 9행은 source 와 같은 문단(같은 사람 서술) 안, 신한 FY2019 장동기·정운진 2행은 같은 날 같은 "
    "선임 건의 이사회 결의 문장(note 「사유 위치 p.25」) — 사유 문장을 다른 사람·다른 겸직에 붙인 행 없음.",
    "- B 제외 표본 30개: 30개 모두 규정 조문·사외이사 자격요건/본인 소명 칸·경력 속 「파견」 — 조직·인력 서술이 아님 → 다시 넣을 문장 없음. "
    "본인 소명 칸 가운데 내용이 있는 것(120·182·183·463·465)은 A 행으로 이미 들어 있음.",
    "- 참고(수집 보고 오기): wave1_results.json g1 의 「사외이사 후보 본인 소명 칸 신한 16행」은 실제 15행(A_SPECS od 15개) — 신한 개별 겸직 합계 25행은 맞음. "
    "개별 겸직 갈래 합계: KB 5 + 신한 25 + 하나 6 + 우리 18 = 54.",
    "- 사외이사 후보 「현재 겸직 업무」 칸 전수(본공시): 내용이 있는 칸은 모두 A 행으로 들어 있음(빠진 칸 0) — 「겸직사항 없음」「해당사항 없음」 칸과 "
    "작성요령(빈 양식)만 행이 없음. 하나 FY2024·2025 리스크관리집행위원회 표에는 주5(겸직) 각주가 없고 은행 리스크 담당(배창욱)이 따로 있어 행 없음이 맞음.",
    "### 「문서에 없음」 반박 시도 판단",
    "- A 30행(「임원 겸직 현황」 표·「겸직 사유」 칸 없음): 반박된 행 없음 → 유지. 넓은 검색어(공백 무시) 겸직현황·겸직사유·겸직이유·겸직승인·임원겸직·"
    "겸임·겸무·겸직내역·타회사임원·다른회사임원·겸직중인 으로 걸린 글은 ① 이미 A 행인 것(하나 리스크관리 담당임원 주5, 우리 FY2019 이사회 요청, "
    "신한 은행장 「겸임」 서술 — FY2022 p.43·FY2023 p.48 「…은행장을 겸임하는 (진옥동) 비상임이사의 의결권은 제한」은 그 FY 의 진옥동·정상혁 A 행과 같은 겸직), "
    "② B 행인 감독당국 지적·내부통제 서술(KB FY2022 「임원 겸직 사전 승인절차 누락」, 신한 FY2020 「고유재산 운용 임원 겸직」, 하나 FY2025 "
    "「내부 겸직현황 관리자료」), ③ 「겸임교수」 직함·이사 경력 「(신한금융지주회사 비상임이사 겸임)」·위원회 위원 겸임 제한 규칙·「사외이사 겸 "
    "임원후보추천위원회 위원장」(겸+임원 낱말 이음) 뿐. 겸직 1건당 행이 있는 「겸직 현황」 표나 「겸직 사유」 칸은 어느 문서에도 없음.",
    "- B 8행(키워드 「없음」): 반박된 행 없음 → 유지. 같은 문서를 공백 무시로 다시 찾으면 「겸직」은 사외이사 후보 본인 소명 칸·작성요령(우리), "
    "「파견」은 김홍태 경력(우리 FY2021·2022 본공시 — A 행으로 들어감), 「전입」은 「준비금의 자본전입」, 「전적」은 「사전적합성」(NH), "
    "NH FY2024 「겸직」 1곳은 내부규정 목록의 이름 「13. 그룹임직원겸직에관한규정」(규정 이름 목록 — 생성기 X규정 판단 유지). 추가공시 3개(우리 FY2021~2023)는 "
    "키워드 0. 참고: 우리 FY2025 본공시에 「자회사간 인력교류가 활발해질 필요가 있음」(키워드 밖 낱말 「인력교류」)이 있으나 요청 키워드(겸직·파견·출향·"
    "전출·전적·겸무)가 아니라 넣지 않음 — 메인이 키워드를 넓힐지 정할 것.",
]


def say(s=""):
    OUT.append(s)


def fail(s):
    FAIL.append(s)
    OUT.append("  [실패] " + s)


def vnorm(t):
    """15차 새 원문 대조 규칙(PDF·6차 섹션 출처): 공백·줄바꿈만 지움 — 「|」는 지우지 않음."""
    return re.sub(r"\s+", "", t or "")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def kst(s):
    if s and s.endswith("+0000"):
        d = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S+0000").replace(tzinfo=timezone.utc)
        return d.astimezone(KST).isoformat(timespec="seconds")
    return s


# ================================================================ 원문 읽기(생성기와 따로)
class PdfDoc:
    src = "pdf"

    def __init__(self, r):
        self.co, self.year, self.kind = r["회사"], int(r["공시연도"]), r["공시유형"]
        self.url, self.fetched_at, self.title = r["실제_url"], r["fetched_at"], r["제목"]
        self.file, self.path = os.path.basename(r["저장경로"]), r["text_path"]
        L = open(self.path, encoding="utf-8").read().split("\n")
        st = next(i for i, l in enumerate(L) if re.match(r"## p\.1\b", l))
        chars, pages, pg = [], [], 0
        self.page_text = {}
        self.lines = []          # [(쪽, 줄)] — 쪽 표지 줄 뺌
        for l in L[st:]:
            m = re.match(r"## p\.(\d+)", l)
            if m:
                pg = int(m.group(1))
                continue
            self.lines.append((pg, l))
            for ch in l:
                if ch.isspace():
                    continue
                chars.append(ch)
                pages.append(pg)
        self.n, self.pg = "".join(chars), pages
        self.npages = pg
        for i, p in enumerate(pages):
            self.page_text.setdefault(p, []).append(chars[i])
        self.page_text = {p: "".join(v) for p, v in self.page_text.items()}

    def find(self, needle):
        """[(시작 위치, 쪽)]"""
        out, i = [], self.n.find(needle)
        while i >= 0 and needle:
            out.append((i, self.pg[i]))
            i = self.n.find(needle, i + 1)
        return out


class SecDoc:
    src = "sec6"

    def __init__(self, key, rows, f):
        self.co, self.year, self.kind = key[0], int(key[1]), key[2]
        self.url, self.fetched_at, self.title, self.file = f["url"], kst(f["fetched_at"]), f["제목"], f["파일명"]
        bysec = {}
        for r in rows:
            bysec.setdefault(int(r["섹션순번"]), []).append(r)
        self.units = []
        for sn in sorted(bysec):
            ch = sorted(bysec[sn], key=lambda x: int(x["chunk_seq"] or 0))
            self.units.append(dict(sn=sn, start=ch[0]["시작페이지"], title=ch[0]["섹션제목_원문"],
                                   n=vnorm("".join(c["본문"] for c in ch)), body="".join(c["본문"] for c in ch)))
        self.n = "".join(u["n"] for u in self.units)

    def find(self, needle):
        """[(유닛 번호, 유닛 안 위치, 시작페이지)]"""
        out = []
        for ui, u in enumerate(self.units):
            i = u["n"].find(needle)
            while i >= 0 and needle:
                out.append((ui, i, u["start"]))
                i = u["n"].find(needle, i + 1)
        return out


def load_docs():
    docs = {}
    for r in json.load(open(DL_JSON, encoding="utf-8")):
        if r.get("text_path"):
            d = PdfDoc(r)
            docs[(d.co, d.year, d.kind)] = d
    fl = {}
    for r in csv.DictReader(open(FILELIST, encoding="utf-8-sig")):
        if r["지주명"] in G1 and r["공시연도"]:
            fl[(r["지주명"], r["공시연도"], r["공시유형"])] = r
    secs = {}
    for r in csv.DictReader(open(SEC_CSV, encoding="utf-8-sig")):
        if r["지주명"] in G1:
            secs.setdefault((r["지주명"], r["공시연도"], r["공시유형"]), []).append(r)
    for k, rows in secs.items():
        d = SecDoc(k, rows, fl[k])
        docs[(d.co, d.year, d.kind)] = d
    return docs


def load_t13():
    z = zipfile.ZipFile(T13_ZIP)
    out = {}
    for co in G1:
        name = next((n for n in z.namelist() if n.endswith("연차보고서__%s.md" % co)), None)
        if not name:
            continue
        pages, cur = {}, None
        for l in z.read(name).decode("utf-8").split("\n"):
            m = re.match(r"## p\.(\d+)", l)
            if m:
                cur = int(m.group(1))
                pages[cur] = []
            elif cur:
                pages[cur].append(l)
        out[co] = {p: vnorm("\n".join(v)) for p, v in pages.items()}
    return out


DN_RE = re.compile(r"^(?P<title>.*) \((?P<kind>본공시|추가공시|정정공시), 파일 (?P<file>.*)\)$")


def parts_of(text):
    """15차 새 규칙: 이은 조각을 따로 찾지 않음 — 행 전체가 원문 한 곳에 이어서 있어야 함(「 … 」 든 행은 아래에서 실패)."""
    return [text]


JOIN_MARK = re.compile(r" … |…| \| ")


# ================================================================ 실행
def main():
    now = datetime.now(KST).isoformat(timespec="seconds")
    say("# 15차 검증 — 연차보고서 조각 g1 (KB금융지주·신한금융지주·하나금융지주·우리금융지주·NH농협금융지주)")
    say("실행: %s (KST) · 스크립트 scripts/dart/verify15_gov_g1.py · 생성기 %s md5 %s" % (now, GEN, md5(GEN)))
    say("대조 정규화(15차 새 원문 대조 규칙): 공백·줄바꿈만 무시(「|」는 지우지 않음), 행 글 전체가 원문 한 곳에 이어서 있어야 함. 그 밖의 글자는 그대로 비교. "
        "원문은 생성기 함수를 쓰지 않고 따로 읽음.")
    say("")
    for line in FIXES:
        say(line)
    say("")
    docs = load_docs()
    t13 = load_t13()
    say("원문 문서: PDF 쪽 텍스트 %d개, 6차 섹션 문서 %d개(g1), 13차 연차보고서 텍스트 %d개사" % (
        sum(1 for d in docs.values() if d.src == "pdf"), sum(1 for d in docs.values() if d.src == "sec6"), len(t13)))
    say("")

    # ---------------------------------------------------------------- (c)
    say("## (c) 열 이름·utf-8-sig·필수 칸·출처 목록 일치")
    tables = {}
    for task, path in (("A", A_CSV), ("B", B_CSV)):
        raw = open(path, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rd = csv.reader(open(path, encoding="utf-8-sig", newline=""))
        head = next(rd)
        rows = [dict(zip(head, r)) for r in rd]
        tables[task] = rows
        say("- %s: %d행, md5 %s, BOM %s, 열 %s" % (os.path.basename(path), len(rows), md5(path), "있음" if bom else "없음",
                                               "COMMON15 과 같음" if head == COLS[task] else "다름 %s" % head))
        if not bom:
            fail("%s BOM 없음" % path)
        if head != COLS[task]:
            fail("%s 열 이름·순서 다름" % path)
        blank = 0
        for i, r in enumerate(rows, 2):
            for c in REQ_ALL + REQ[task]:
                if not (r.get(c) or "").strip():
                    blank += 1
                    fail("%s 줄 %d 필수 칸 %s 빈칸" % (task, i, c))
            if r["corp_label"] not in G1:
                fail("%s 줄 %d 회사 %s 범위 밖" % (task, i, r["corp_label"]))
            if not re.fullmatch(r"20(19|2[0-5])", r["fy"]):
                fail("%s 줄 %d fy %s 범위 밖" % (task, i, r["fy"]))
            if r["doc_kind"] != DOC_KIND:
                fail("%s 줄 %d doc_kind %s" % (task, i, r["doc_kind"]))
            if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00", r["collected_at"]):
                fail("%s 줄 %d collected_at KST 꼴 아님 %s" % (task, i, r["collected_at"]))
        say("  필수 칸(%s) 빈칸 %d" % ("·".join(REQ_ALL + REQ[task]), blank))
        bad = 0
        for i, r in enumerate(rows, 2):
            m = DN_RE.match(r["doc_name"])
            d = docs.get((r["corp_label"], int(r["fy"]) + 1, m.group("kind"))) if m else None
            r["_doc"], r["_line"] = d, i
            if not d:
                bad += 1
                fail("%s 줄 %d doc_name 으로 출처 문서를 못 찾음: %s" % (task, i, r["doc_name"][:80]))
                continue
            errs = [x for x, ok in (("제목", m.group("title") == d.title), ("파일", m.group("file") == d.file),
                                    ("url", r["rcept_no_or_url"] == d.url), ("collected_at", r["collected_at"] == d.fetched_at))
                    if not ok]
            if errs:
                bad += 1
                fail("%s 줄 %d 출처 목록과 다름: %s" % (task, i, ",".join(errs)))
        say("  doc_name(제목·유형·파일)·rcept_no_or_url·collected_at·fy(=공시연도-1) ↔ download.json / 연차보고서_파일목록.csv: 다른 행 %d" % bad)
    say("")

    # ---------------------------------------------------------------- (a)(b)
    say("## (a) source_text·reason_text 원문 대조, (b) page 위치 대조")
    stats = {}
    for task in ("A", "B"):
        st = stats[task] = dict(n=0, none=0, ok=0, bad=0, pok=0, pbad=0, rn=0, rok=0, joined=0, fn=0, fok=0, t13n=0, t13ok=0,
                                ovn=0, ovok=0, mdn=0, mdok=0)
        md_cache = {}
        for r in tables[task]:
            d, i = r["_doc"], r["_line"]
            st["n"] += 1
            if not d:
                continue
            src = r["source_text"]
            if src == NONE:
                st["none"] += 1
                if r["page"] != "전체":
                    fail("%s 줄 %d 「문서에 없음」 행 page 「%s」(전체 아님)" % (task, i, r["page"]))
                if "찾은 범위" not in r["note"]:
                    fail("%s 줄 %d 「문서에 없음」 행 note 에 찾은 범위 없음" % (task, i))
                if task == "A" and r["reason_text"] != NONE:
                    fail("A 줄 %d source 없음인데 reason 있음" % i)
                continue
            ps = parts_of(src)
            if JOIN_MARK.search(src):
                st["joined"] += 1
                fail("%s 줄 %d source_text 에 생략·이음 표시(「 … 」·「 | 」) — 원문에 이어진 글이 아님" % (task, i))
            hits = [d.find(vnorm(p)) for p in ps]
            if not all(hits):
                st["bad"] += 1
                fail("%s 줄 %d source_text 원문에 없음: %s" % (task, i, src[:80]))
                continue
            st["ok"] += 1
            r["_hits"] = hits
            # (b) page
            pg = r["page"]
            if d.src == "pdf":
                m = re.fullmatch(r"p\.(\d+)", pg)
                ok = bool(m) and any(p == int(m.group(1)) for _, p in hits[0])
                pages_found = sorted({p for _, p in hits[0]})
            else:
                m = re.fullmatch(r"시작페이지 (\d+) 섹션 안", pg)
                ok = bool(m) and any(s == m.group(1) for _, _, s in hits[0]) and \
                    all(any(s == m.group(1) for _, _, s in h) for h in hits)
                pages_found = sorted({s for _, _, s in hits[0]})
            if ok:
                st["pok"] += 1
            else:
                st["pbad"] += 1
                fail("%s 줄 %d page 「%s」 — 실제 %s" % (task, i, pg, pages_found))
            # 각주 쪽
            mf = re.search(r"각주 p\.(\d+)", r["note"])
            if mf:
                st["fn"] += 1
                fl = [l for l in src.split("\n") if re.match(r"\s*주\s?\d\)", l)]
                fh = d.find(vnorm(fl[-1])) if (fl and d.src == "pdf") else []
                # 각주 줄이 source 시작 뒤 2,000자 안, note 의 쪽에 있어야 함
                fh = [x for x in fh if any(0 <= x[0] - a < 2000 for a, _ in hits[0])]
                if fh and any(p == int(mf.group(1)) for _, p in fh):
                    st["fok"] += 1
                else:
                    fail("%s 줄 %d 각주 쪽 %s 틀림 — 실제 %s" % (task, i, mf.group(0), sorted({p for _, p in fh})))
            # 13차 쪽
            m13 = re.search(r"13차 텍스트\(같은 PDF sha256\) ((?:p\.\d+,?)+)", r["note"])
            if m13:
                st["t13n"] += 1
                cl = [int(x) for x in re.findall(r"\d+", m13.group(1))]
                pt = t13.get(r["corp_label"], {})
                nv = vnorm(ps[0])
                good = [p for p in cl if nv in pt.get(p, "") + pt.get(p + 1, "")]
                if good and all(nv[:60] in pt.get(p, "") for p in cl):
                    st["t13ok"] += 1
                else:
                    fail("%s 줄 %d 13차 쪽 %s 에 글 없음" % (task, i, m13.group(1)))
            # 같은 FY 다른 공시 표시
            mo = re.search(r"같은 FY 다른 공시: ([^;]+)", r["note"])
            if mo:
                for item in mo.group(1).split(", "):
                    mm = re.match(r"(본공시|추가공시|정정공시) (같은 글|에 이 글 없음)", item.strip())
                    if not mm:
                        continue
                    st["ovn"] += 1
                    o = docs.get((d.co, d.year, mm.group(1)))
                    has = bool(o) and vnorm(ps[0]) in o.n
                    if has == (mm.group(2) == "같은 글"):
                        st["ovok"] += 1
                    else:
                        fail("%s 줄 %d note 「%s」 틀림(실제 %s)" % (task, i, item.strip(), "있음" if has else "없음"))
            if "본공시에 없는 글" in r["note"]:
                st["ovn"] += 1
                o = docs.get((d.co, d.year, "본공시"))
                if o and vnorm(ps[0]) not in o.n:
                    st["ovok"] += 1
                else:
                    fail("%s 줄 %d 「본공시에 없는 글」 인데 본공시에 있음" % (task, i))
            # 원문 md(사용자 산출물)에 source 가 든 절이 있는지
            mdp = os.path.join(ORIG, task, "%s__FY%s__연차보고서.md" % (r["corp_label"], r["fy"]))
            st["mdn"] += 1
            if mdp not in md_cache:
                md_cache[mdp] = vnorm(open(mdp, encoding="utf-8").read().replace("ˋˋˋ", "```")) if os.path.exists(mdp) else None
            if md_cache[mdp] is not None and all(vnorm(p) in md_cache[mdp] for p in ps):
                st["mdok"] += 1
            else:
                fail("%s 줄 %d 원문 md(%s)에 source 없음" % (task, i, mdp))
            # reason
            if task == "A" and r["reason_text"] != NONE:
                st["rn"] += 1
                rh = d.find(vnorm(r["reason_text"]))
                if rh:
                    st["rok"] += 1
                    r["_rhits"] = rh
                else:
                    fail("A 줄 %d reason_text 원문에 없음: %s" % (i, r["reason_text"][:60]))
        say("- %s: %d행(문서에 없음 %d) — 글 대조(한 곳에 이어서 있음) 맞음 %d / 틀림 %d (생략·이음 표시 든 행 %d), page 맞음 %d / 틀림 %d" % (
            task, st["n"], st["none"], st["ok"], st["bad"], st["joined"], st["pok"], st["pbad"]))
        if task == "A":
            say("  reason_text(문서에 없음 아님) %d행 — 원문에 있음 %d; 각주 쪽(note 「각주 p.N」) %d행 맞음 %d" % (
                st["rn"], st["rok"], st["fn"], st["fok"]))
        say("  FY2025 13차 텍스트 쪽(note) %d행 맞음 %d; note 의 「같은 FY 다른 공시: … 같은 글/에 이 글 없음」·「본공시에 없는 글」 표시 %d건 맞음 %d; "
            "원문 md(dart_out/ops15/원문/%s/)에 source 가 든 행 %d/%d" % (
                st["t13n"], st["t13ok"], st["ovn"], st["ovok"], task, st["mdok"], st["mdn"]))
    say("")

    # ---------------------------------------------------------------- (e) A 개별 겸직
    say("## (e) A 「손으로 고른 A_SPECS」 개별 겸직 행 대조")
    A = [r for r in tables["A"] if r["source_text"] != NONE and r.get("_hits")]
    cc_ok = ct_ok = 0
    for r in A:
        ns = vnorm(r["source_text"])
        if r["concurrent_company"] == NONE or vnorm(r["concurrent_company"]) in ns:
            cc_ok += 1
        else:
            fail("A 줄 %d concurrent_company 「%s」 가 source 에 없음" % (r["_line"], r["concurrent_company"]))
        if not r["concurrent_title"] or vnorm(r["concurrent_title"]) in ns:
            ct_ok += 1
        else:
            fail("A 줄 %d concurrent_title 「%s」 가 source 에 없음" % (r["_line"], r["concurrent_title"]))
    say("- 개별 겸직 %d행: concurrent_company 가 source_text 안(또는 「문서에 없음」) %d, concurrent_title 이 source 안(또는 빈칸) %d" % (
        len(A), cc_ok, ct_ok))
    # 사외이사 후보 칸: 바로 앞 인적사항 머리의 성명·출생연도
    od = [r for r in A if r["holdco_title"] == "사외이사 후보"]
    od_ok, od_exc = 0, []
    for r in od:
        d = r["_doc"]
        pg = r["page"]
        pos = None
        for h in r["_hits"][0]:
            if (d.src == "pdf" and "p.%d" % h[1] == pg) or (d.src == "sec6" and "시작페이지 %s 섹션 안" % h[2] == pg):
                pos = h
                break
        text, at = (d.n, pos[0]) if d.src == "pdf" else (d.units[pos[0]]["n"], pos[1])
        # 칸이 든 「본인 소명」 머리(③ 사외이사 후보 본인 소명 / 사. 사외이사후보 본인 소명 / (사) 감사위원후보 본인 소명) →
        # 그 머리 앞의 마지막 「후보자(의) 인적사항」 머리가 이 칸의 사람. (PDF 글 순서로 표가 쪽 끝에 밀려 다음 후보 머리 뒤에 오는 경우 대비)
        anc = [m for m in re.finditer(r"본인소명", text[:at])]
        a0 = anc[-1].start() if anc else at
        heads = [m for m in re.finditer(r"후보자의?인적사항", text[:a0])]
        hd = heads[-1] if heads else None
        win = text[max(0, hd.start() - 25):hd.end() + 25] if hd else ""
        name_ok = bool(hd) and vnorm(r["person"]) in win
        birth_ok = (not r["birth_ym"] or ("출생연도:%s" % r["birth_ym"]) in text[hd.start():a0]) if hd else False
        # 바로 앞 인적사항 머리(소명 머리 무시)와 다르면 따로 셈 — PDF 글 순서가 뒤바뀐 칸
        h2 = [m for m in re.finditer(r"후보자의?인적사항", text[:at])]
        r["_od_moved"] = bool(h2) and vnorm(r["person"]) not in text[max(0, h2[-1].start() - 25):h2[-1].end() + 25]
        r["_od_head"] = win
        audit = bool(anc) and text[max(0, a0 - 8):a0].endswith("감사위원후보")
        want = "감사위원 후보 추천 관련 사항" if audit else "사외이사 후보 추천 관련 사항"
        r["_od_audit"] = audit
        if not r["note"].startswith(want):
            fail("A 줄 %d note 머리가 칸 머리(%s 본인 소명)와 다름" % (r["_line"], "감사위원후보" if audit else "사외이사후보"))
        if name_ok and birth_ok:
            od_ok += 1
        else:
            od_exc.append(r)
    say("- 사외이사 후보 「현재 겸직 업무」 칸 %d행: 칸이 든 「본인 소명」 머리 앞 「후보자(의) 인적사항」 머리의 성명·출생연도가 행과 같음 %d" % (
        len(od), od_ok))
    au = [r for r in od if r.get("_od_audit")]
    say("  칸 머리가 「(사) 감사위원후보 본인 소명」인 행 %d(%s) — note 머리 「감사위원 후보 추천 관련 사항」, 나머지는 「사외이사 후보 추천 관련 사항」: "
        "다른 행 %d" % (len(au), ", ".join("줄 %d %s" % (r["_line"], r["person"]) for r in au),
                       sum(1 for r in od if not r["note"].startswith("감사위원 후보 추천 관련 사항" if r.get("_od_audit") else "사외이사 후보 추천 관련 사항"))))
    mv = [r for r in od if r.get("_od_moved")]
    say("  그 가운데 PDF 글 순서로는 칸이 다음 후보 인적사항 뒤에 오는 행(표가 쪽 끝에 밀림) %d: %s — 소명 머리·「○○ 후보자에 대한」 순서로 "
        "생성기 배정이 맞음(표본 13 박상용 손 대조, 정찬형 칸 뒤 p.58 은 신요환 경력, 신요환 칸 「신영증권 고문」 은 신요환 경력 「신영증권」과 맞음)" % (
            len(mv), ", ".join("줄 %d %s" % (r["_line"], r["person"]) for r in mv)))
    for r in od_exc:
        say("  - 줄 %d %s FY%s %s: 앞 머리 「%s」 → 다름" % (r["_line"], r["corp_label"], r["fy"], r["person"], r["_od_head"][:60]))
        fail("A 줄 %d 사외이사 후보 칸 앞 머리 성명 다름" % r["_line"])
    # 성명이 원문 문장에 든 행(사외이사 후보 칸 제외)
    pn = [r for r in A if r["person"] and r["holdco_title"] != "사외이사 후보"]
    say("- 성명이 있는 그 밖의 행 %d: 성명이 source_text 안 %d" % (len(pn), sum(1 for r in pn if vnorm(r["person"]) in vnorm(r["source_text"]))))
    for r in pn:
        if vnorm(r["person"]) not in vnorm(r["source_text"]):
            fail("A 줄 %d 성명 %s 가 source 에 없음" % (r["_line"], r["person"]))
    say("")
    say("### 표본 15개 손 대조(사람이 원문을 읽음) — 근거 글 자동 재확인")
    for no, h in enumerate(HAND_A, 1):
        rows = [r for r in A if (r["corp_label"], r["fy"], r["person"], r["holdco_title"], r["concurrent_company"]) == h["k"]]
        if not rows:
            fail("표본 %d 행을 못 찾음 %s" % (no, h["k"]))
            continue
        r = rows[0]
        d = r["_doc"]
        res = []
        for ev in h["ev"]:
            kind, rx = ev[0], ev[1]
            ok = False
            if kind == "src":
                ok = bool(re.search(rx, vnorm(r["source_text"])))
            elif kind == "page":
                ok = d.src == "pdf" and bool(re.search(rx, d.page_text.get(ev[2], "")))
            else:
                n_ = ev[2]
                L = len(vnorm(parts_of(r["source_text"])[0]))
                for hh in r["_hits"][0]:
                    text, at = (d.n, hh[0]) if d.src == "pdf" else (d.units[hh[0]]["n"], hh[1])
                    seg = text[max(0, at - n_):at] if kind == "before" else text[at + L:at + L + n_]
                    if re.search(rx, seg):
                        ok = True
                        break
            res.append(ok)
            if not ok:
                fail("표본 %d 근거 글 못 찾음: %s %s" % (no, kind, rx[:50]))
        say("%d. 줄 %s %s FY%s %s / %s → %s — 근거 %d/%d 확인. %s" % (
            no, ",".join(str(x["_line"]) for x in rows), r["corp_label"], r["fy"], r["person"] or "(성명 없음)",
            r["concurrent_company"], "맞음" if all(res) else "확인 실패", sum(res), len(res), h["j"]))
    say("")

    # ---------------------------------------------------------------- (f) reason 9행
    say("## (f) reason_text 가 든 행 전부")
    R = [r for r in tables["A"] if r["reason_text"] != NONE]
    say("- %d행" % len(R))
    for r in R:
        d = r["_doc"]
        key = (r["corp_label"], r["fy"], r["person"])
        dist = None
        if r.get("_rhits") and r.get("_hits"):
            for a in r["_hits"][0]:
                for b in r["_rhits"]:
                    if d.src == "pdf":
                        dd = abs(b[0] - a[0])
                    else:
                        dd = abs(b[1] - a[1]) if a[0] == b[0] else None
                    if dd is not None and (dist is None or dd < dist):
                        dist = dd
        near = dist is not None and dist <= 400
        mp = re.search(r"사유 위치 p\.(\d+)", r["note"])
        if not near and mp and d.src == "pdf":
            # 15차: 같은 문서 다른 쪽의 사유 문장을 옮긴 행 — note 「사유 위치 p.N」 쪽에 reason 이 있어야 함
            near = any(p == int(mp.group(1)) for _, p in (r.get("_rhits") or []))
            if not near:
                fail("A 줄 %d reason 이 note 「사유 위치 p.%s」 쪽에 없음" % (r["_line"], mp.group(1)))
        elif not near:
            fail("A 줄 %d reason 이 source 와 같은 문단이 아님(거리 %s)" % (r["_line"], dist))
        if key not in HAND_R:
            fail("A 줄 %d reason 행 손 판단 없음" % r["_line"])
        say("  - 줄 %d %s FY%s %s: 글자 그대로 %s, source 와 거리 %s 글자(공백 뺀) → %s. %s" % (
            r["_line"], r["corp_label"], r["fy"], r["person"] or "(성명 없음)", "있음" if r.get("_rhits") else "없음", dist,
            ("같은 문단" if not mp else "note 「%s」 쪽에 있음" % mp.group(0)) if near else "멀음", HAND_R.get(key, "")))
    say("")

    # ---------------------------------------------------------------- (i) reason_text 「문서에 없음」 행의 찾은 범위(15차)
    say("## (i) reason_text 「문서에 없음」 개별 겸직 행 — note 의 찾은 범위와 걸린 줄 수를 원문에서 다시 셈")
    RS_RE = re.compile(r"사\s*유|겸\s*직|겸\s*임|선\s*임")
    RA, RB = re.compile(r"겸\s*직|겸\s*임"), re.compile(r"사\s*유|선\s*임")
    RN = [r for r in tables["A"] if r["reason_text"] == NONE and r["source_text"] != NONE]
    rs_ok = 0
    for r in RN:
        d, i = r["_doc"], r["_line"]
        m = re.search(r"reason_text 「문서에 없음」 — 찾은 범위: (.+?) 에서 검색어 「사유」「겸직」「겸임」「선임」\(걸린 줄 (\d+)\), (.+?)에서 「겸직」「겸임」이 "
                      r"「사유」「선임」과 같은 줄이나 앞뒤 줄에 함께 있는 곳\((\d+)\)", r["note"])
        if not m:
            fail("A 줄 %d reason_text 「문서에 없음」인데 note 에 찾은 범위(문서·쪽 범위·검색어) 없음" % i)
            continue
        if d.src == "pdf":
            mp = re.match(r"(.+) p\.(\d+)~p\.(\d+)\(행 쪽", m.group(1))
            if not mp or mp.group(1) != d.file:
                fail("A 줄 %d 찾은 범위 문서 이름이 출처 파일과 다름: %s" % (i, m.group(1)[:60]))
                continue
            a, b = int(mp.group(2)), int(mp.group(3))
            n1 = sum(1 for p, l in d.lines if a <= p <= b and RS_RE.search(l))
            n2 = 0
            for k, (p, l) in enumerate(d.lines):
                if RA.search(l) and RB.search(" ".join(x for _, x in d.lines[max(0, k - 1):k + 2])):
                    n2 += 1
            pg_ok = bool(re.fullmatch(r"p\.(\d+)", r["page"])) and a <= int(r["page"][2:]) <= b
        else:
            mu = re.search(r"6차 섹션 「(.+)」\(시작페이지 (\d+)\) 글 전체", m.group(1))
            us = [u for u in d.units if mu and u["start"] == mu.group(2) and vnorm(mu.group(1)).endswith(vnorm(u["title"]))]
            if not us:
                fail("A 줄 %d 찾은 범위 섹션을 못 찾음: %s" % (i, m.group(1)[:60]))
                continue
            n1 = sum(1 for l in us[0]["body"].split("\n") if l.strip() and RS_RE.search(l))
            n2 = 0
            for u in d.units:
                ls = [l for l in u["body"].split("\n") if l.strip()]
                n2 += sum(1 for k, l in enumerate(ls) if RA.search(l) and RB.search(" ".join(ls[max(0, k - 1):k + 2])))
            pg_ok = vnorm(r["source_text"]) in us[0]["n"]
        if (n1, n2) == (int(m.group(2)), int(m.group(4))) and pg_ok:
            rs_ok += 1
        else:
            fail("A 줄 %d 찾은 범위 다시 세기 다름: note 걸린 줄 %s·%s, 다시 센 것 %d·%d, 행 위치가 범위 안 %s" % (
                i, m.group(2), m.group(4), n1, n2, pg_ok))
    say("- %d행: note 에 찾은 범위가 있고 원문에서 다시 센 걸린 줄 수(범위 안 4낱말, 문서 전체 함께 나옴)와 행 위치가 맞는 행 %d" % (len(RN), rs_ok))
    LOG = list(csv.DictReader(open(os.path.join(WORK, "A_사유_재검색.csv"), encoding="utf-8-sig")))
    import collections as _c
    jc = _c.Counter(x["judge"] for x in LOG)
    say("- 작업 기록 gov15_g1_work/A_사유_재검색.csv %d줄 — 판정별: %s" % (len(LOG), "; ".join("%s %d" % (k, v) for k, v in jc.most_common())))
    if jc.get("판정 없음"):
        fail("A_사유_재검색.csv 에 판정 없는 줄 %d" % jc["판정 없음"])
    moved = [x for x in LOG if "reason_text 로 옮김" in x["judge"]]
    say("  reason_text 로 옮긴 글은 신한 FY2019 「겸직 사업부문 활성화를 위해 경영진 신규 선임」(p.25·p.51 같은 글, 걸린 줄 %d) 하나 — 장동기·정운진 행(위 (f)). "
        "그 밖의 걸린 줄은 후보 「현재 겸직 업무」 칸·충실성 문구·자격요건·선임 사실·규정 조문·다른 사람(은행장) 겸직 서술 등으로, 그 행 겸직의 사유를 적은 글이 아님(사람이 읽음)." % len(moved))
    say("")

    # ---------------------------------------------------------------- (g) B 제외 표본
    say("## (g) B 에서 뺀 문장 표본 30개(seed %d)" % EXCL_SEED)
    X = list(csv.DictReader(open(EXCL_CSV, encoding="utf-8-sig")))
    idx = sorted(random.Random(EXCL_SEED).sample(range(len(X)), EXCL_N))
    say("- 제외 CSV %d행(범주: %s), 표본 번호 %s" % (len(X), ", ".join("%s %d" % (c, sum(1 for x in X if x["cat"] == c))
                                                        for c in sorted({x["cat"] for x in X})), idx))
    nx_ok = 0
    for k in idx:
        x = X[k]
        d = docs.get((x["co"], int(x["year"]), x["kind"]))
        nv = vnorm(x["sent"])
        found = bool(d) and nv in d.n
        if d and d.src == "pdf" and found:
            found = any(str(p) == x["page"] for _, p in d.find(nv))
        if d and d.src == "sec6" and found:
            found = any(s == x["page"] for _, _, s in d.find(nv))
        hj = HAND_X.get(k)
        if not found:
            fail("제외 표본 %d 원문 그 쪽에 없음" % k)
        if not hj or hj[0] != x["cat"]:
            fail("제외 표본 %d 손 판단 없음 또는 범주 다름(%s)" % (k, x["cat"]))
        else:
            nx_ok += 1
        say("  - %d %s 공시연도 %s(FY%d) %s 쪽 %s [%s] 원문 %s · 「%s」 → 빼는 것이 맞음: %s" % (
            k, x["co"], x["year"], int(x["year"]) - 1, x["kind"], x["page"], x["cat"], "있음" if found else "없음",
            " ".join(x["sent"].split())[:70], hj[1] if hj else "?"))
    say("- 30개 중 빼는 것이 맞음 %d, 잘못 뺌 0 → B 에 다시 넣은 문장 없음" % nx_ok)
    say("- 제외 CSV sent 칸 길이: 300자 넘는 행 %d(고치기 전에는 300자에서 잘렸음), 원문에 그대로 있는 행 %d/%d" % (
        sum(1 for x in X if len(x["sent"]) > 300),
        sum(1 for x in X if (lambda d: bool(d) and vnorm(x["sent"]) in d.n)(docs.get((x["co"], int(x["year"]), x["kind"])))), len(X)))
    for x in X:
        d = docs.get((x["co"], int(x["year"]), x["kind"]))
        if not d or vnorm(x["sent"]) not in d.n:
            fail("제외 CSV 문장이 원문에 없음: %s %s %s" % (x["co"], x["year"], x["sent"][:40]))
    say("")

    # ---------------------------------------------------------------- (h) 「문서에 없음」 반박
    say("## (h) 「문서에 없음」 반박 시도(공백 무시 넓은 검색어, 같은 회사·FY 의 본공시·추가공시 전문)")
    TA = ["겸직현황", "겸직사유", "겸직이유", "겸직승인", "임원겸직", "겸임", "겸무", "겸직내역", "타회사임원", "다른회사임원", "겸직중인"]
    for r in tables["A"]:
        if r["source_text"] != NONE or not r.get("_doc"):
            continue
        ds = [d for (co, y, _), d in docs.items() if co == r["corp_label"] and y == int(r["fy"]) + 1]
        cnt, ctx = {}, []
        for d in ds:
            for t in TA:
                for m in re.finditer(t, d.n):
                    cnt[t] = cnt.get(t, 0) + 1
                    c = d.n[max(0, m.start() - 22):m.end() + 22]
                    if d.kind == "본공시" and not any(c == x for x in ctx):
                        ctx.append(c)
        say("- A 줄 %d %s FY%s (%s): %s" % (r["_line"], r["corp_label"], r["fy"], ", ".join(d.kind for d in ds),
                                           ", ".join("%s %d" % kv for kv in sorted(cnt.items())) or "0건"))
        for c in [c for c in ctx if "겸임교수" not in c][:6]:
            say("    · …%s…" % c)
        nlist = sum(1 for c in ctx if "겸임교수" in c)
        if nlist:
            say("    · (「겸임교수」 직함 %d곳 생략)" % nlist)
        if cnt.get("겸직사유") or cnt.get("겸직이유"):
            fail("A 줄 %d 「겸직 사유」 낱말이 있음 — 다시 볼 것" % r["_line"])
    TB = ["겸직", "파견", "출향", "전출", "전적", "겸무", "겸임", "겸업", "인사교류", "인력교류", "전입", "파견직", "지원인력"]
    for r in tables["B"]:
        if r["source_text"] != NONE or not r.get("_doc"):
            continue
        d = r["_doc"]
        cnt, ctx = {}, []
        for t in TB:
            for m in re.finditer(t, d.n):
                cnt[t] = cnt.get(t, 0) + 1
                c = d.n[max(0, m.start() - 22):m.end() + 22]
                if c not in ctx:
                    ctx.append(c)
        tj = [m for m in TRUE_JEONJEOK.finditer(d.n)]
        say("- B 줄 %d %s FY%s %s: %s; 「전적」 중 轉籍 꼴(앞뒤 글자 규칙) %d" % (
            r["_line"], r["corp_label"], r["fy"], d.kind, ", ".join("%s %d" % kv for kv in sorted(cnt.items())) or "0건", len(tj)))
        for c in ctx[:8]:
            say("    · …%s…" % c)
        if len(ctx) > 8:
            say("    · (그 밖 %d곳 생략)" % (len(ctx) - 8))
    say("")

    # ---------------------------------------------------------------- B 그 밖
    say("## B 그 밖 대조")
    B = [r for r in tables["B"] if r["source_text"] != NONE]
    kw_ok = sum(1 for r in B if (TRUE_JEONJEOK.search(r["source_text"]) if r["keyword"] == "전적" else r["keyword"] in vnorm(r["source_text"])))
    for r in B:
        k = r["keyword"]
        if not (TRUE_JEONJEOK.search(r["source_text"]) if k == "전적" else k in vnorm(r["source_text"])):
            fail("B 줄 %d keyword %s 가 source 에 없음" % (r["_line"], k))
    dup = {}
    for r in tables["B"]:
        dup.setdefault((r["corp_label"], r["fy"], r["keyword"], r["rcept_no_or_url"], vnorm(r["source_text"]), r["page"]), []).append(r["_line"])
    dups = [v for v in dup.values() if len(v) > 1]
    say("- 키워드 행 %d: keyword 가 source_text 안 %d; 같은 문서·쪽·키워드·글 중복 %d묶음" % (len(B), kw_ok, len(dups)))
    for v in dups:
        fail("B 중복 행 %s" % v)
    CUT_END = re.compile(r"(관한|하는|대한|위한|및|(?<![결합동회])의|을|를|에|과|와|겸직|파견)$")
    FOOT = re.compile(r"(KB금융지주|신한금융지주|하나금융지주|우리금융지주|NH농협금융지주)\s+\d{1,3}\s*$")
    cut = [r for r in B if CUT_END.search(vnorm(r["source_text"]))]
    foot = [r for r in B if FOOT.search(r["source_text"])]
    say("- source_text 가 조사·관형형(…관한·…하는·…의·…을 등)이나 키워드로 끝나는 행(문장 잘림 의심) %d, 쪽 바닥글(「회사명 쪽번호」)로 끝나는 행 %d" % (
        len(cut), len(foot)))
    for r in cut:
        fail("B 줄 %d 문장 끝 잘림 의심: …%s" % (r["_line"], vnorm(r["source_text"])[-25:]))
    for r in foot:
        fail("B 줄 %d 쪽 바닥글로 끝남" % r["_line"])
    emp = sum(1 for r in tables["B"] if r["employees_total"] or r["regular"] or r["contract"])
    say("- employees_total·regular·contract 칸이 찬 행 %d(연차보고서 조각은 빈칸 — 직원 수는 사업보고서 조각 몫)" % emp)
    cov = {}
    for r in tables["B"]:
        cov.setdefault((r["corp_label"], r["fy"]), 0)
        cov[(r["corp_label"], r["fy"])] += 1
    miss = [(co, str(fy)) for co in G1 for fy in range(2019, 2026)
            if (co, str(fy)) not in cov and any(k[0] == co and k[1] == fy + 1 for k in docs)]
    say("- 원문 문서가 있는 회사×FY 가운데 B 행이 없는 곳: %s" % (miss or "없음"))
    for m in miss:
        fail("B 행 없음 %s" % (m,))
    nodoc = [(co, fy) for co in G1 for fy in range(2019, 2026) if not any(k[0] == co and k[1] == fy + 1 for k in docs)]
    say("- 원문 문서가 없는 회사×FY(수집 실패 — 목록 CSV 실패 행): %s" % nodoc)
    lst = list(csv.DictReader(open(LIST_CSV, encoding="utf-8-sig")))
    for co, fy in nodoc:
        if not any(x["회사"] == co and x["공시연도"] == str(fy + 1) and x["실패사유"] for x in lst):
            fail("수집 실패 %s FY%d 가 목록 CSV 실패 행에 없음" % (co, fy))
    say("")

    # ---------------------------------------------------------------- (d) 비밀값
    say("## (d) 키·비밀값 문자열")
    files = [A_CSV, B_CSV, EXCL_CSV, LIST_CSV, DL_JSON, GEN, COLLECTOR, os.path.abspath(__file__)]
    for t in ("A", "B"):
        files += [os.path.join(ORIG, t, f) for f in sorted(os.listdir(os.path.join(ORIG, t)))
                  if f.split("__")[0] in G1]
    files += [d.path for d in docs.values() if d.src == "pdf"]
    key_name = "crtfc" + "_key"
    env_val = os.environ.get("DART" + "_API_KEY") or ""
    pats = [re.compile(re.escape(key_name) + r"\s*[=:]\s*[0-9A-Za-z]{8,}"),
            re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])"),
            re.compile("DART" + r"_API_KEY\s*=\s*['\"]?[0-9A-Za-z]{8,}")]
    hit = 0
    for p in files:
        s = open(p, encoding="utf-8", errors="replace").read()
        if any(x.search(s) for x in pats) or (len(env_val) >= 20 and env_val in s):
            hit += 1
            fail("비밀값 꼴 문자열: %s" % p)
    body = "\n".join(OUT)
    if any(x.search(body) for x in pats) or (len(env_val) >= 20 and env_val in body):
        hit += 1
        fail("결과 txt 에 비밀값 꼴 문자열")
    say("- 본 파일 %d개(조각 2·제외 CSV·목록 CSV·download.json·생성기·수집기·이 스크립트·원문 md g1·쪽 텍스트 md) + 이 결과 txt: "
        "API 키 꼴(%s=…·40자리 16진수·DART_API_KEY=…) %d건; 환경변수 DART_API_KEY 값 %s" % (
            len(files), key_name, hit, "있음 — 파일에 그 값 없음 확인" if len(env_val) >= 20 else "이 세션에 없음(꼴로만 찾음)"))
    say("")
    for line in REVIEW:
        say(line)
    say("")
    say("## 결과: %s (실패 %d)" % ("통과" if not FAIL else "실패", len(FAIL)))
    open(OUTTXT, "w", encoding="utf-8").write("\n".join(OUT) + "\n")
    print("\n".join(OUT[-3:]))
    print("실패 %d — %s" % (len(FAIL), OUTTXT))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
