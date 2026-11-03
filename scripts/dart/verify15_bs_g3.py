# -*- coding: utf-8 -*-
"""15차 검증 — 사업보고서 조각 g3(BNK금융지주·JB금융지주·한국투자금융지주): A_bs_g3.csv·B_bs_g3.csv·D_bs_g3.csv.

    python3 scripts/dart/verify15_bs_g3.py      # 인자 없음 → exit 0(통과)/1(실패), 결과 dart_out/ops15/verify15_bs_g3.txt

g3 수집 에이전트는 파일을 다 쓴 뒤 보고 전에 멈췄으므로, 이 스크립트가 조각 완결 여부부터 본다.
생성기(scripts/dart/ops15_bs_g3.py)의 함수는 쓰지 않고 원문을 따로 읽어 대조한다(웹 요청·API 키 사용 없음, 입력은 읽기만).
  (0) 완결: 회사×FY2019~2025 마다 A·B·D 행, 원문 md(dart_out/ops15/원문/<작업>/<회사>__FY<fy>__사업보고서.md)가 있고
      그 md 의 절 글이 출처 md 의 그 절과 글자까지 같으며 행 source_text 가 그 md 안에 있음. work json 「written」 파일이 다 있음.
  (a) 모든 행 source_text(그리고 reason_text 가 「문서에 없음」이 아니면 그것도)가 그 행 출처 원문에 글자 그대로 있는지
      — 공백·줄바꿈·「|」만 무시(md 의 칸 안 줄바꿈 표시 <br>·&cr; 도 줄바꿈으로 보아 무시).
      출처 원문: 사업보고서 = 사업보고서_원문.csv 의 text_path md(OpenDART XML 옮김),
                 경영공시 2026.2Q = 13차 텍스트 zip 의 경영공시__<회사>.md(「## p.N」) — g3 에서는 한국투자금융지주만 있음.
  (b) page 가 실제 그 글이 있는 위치인지: 「XML [절 n] 「제목」 [표 m]」 → 그 절 머리·제목이 맞고 글이 그 표(또는 절 문단) 안에 있음,
      「p.N(본문 PDF, 13차 보관)」 → 13차 사업보고서 PDF 텍스트 그 쪽에 같은 글(한국투자 FY2025 본만), 경영공시 「p.N」 → 그 쪽.
      「문서에 없음」 행은 page 에 적은 찾은 범위(절 번호·쪽 범위)가 실제 문서 범위와 맞는지.
  (c) 열 이름(COMMON15 순서 그대로)·utf-8-sig·필수 칸(corp_label·fy·doc_kind·source_text·rcept_no_or_url·page·doc_name·
      collected_at, A 는 reason_text, B 는 keyword) 빈칸 0, doc_name·collected_at·fy·회사가 출처 목록과 같음.
  (d) 키·비밀값 문자열 없음(DART_API_KEY 값은 환경변수에서 읽어 들어 있는지만 보고 값은 어디에도 쓰지 않음).
  더해서(g1 과 같은 표본 대조):
  (e) 회사×FY(2019~2025) 마다 A·B·D 각 1행 이상.
  (f) B 숫자 칸 = 원문 직원 표 합계 행 숫자, 합계 = 정함없음 + 기간제.
  (g) 회사마다 2개 FY 를 골라 겸직 표(Ⅷ·Ⅸ) 모든 행이 A 에 있는지(겸직 표는 이 스크립트가 따로 찾음) + 한국투자 「임원약력」 표 현재 행.
  (h) 출생년월: 전수 자동 대조 + 표본 20행.
  (i) 「문서에 없음」 반박 시도: 더 넓은 검색어(공백 무시)로 같은 범위를 다시 찾음.
  (j) note 에 기능 분류·이유 추정 낱말이 없는지.
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

FRAG = os.path.join("dart_out", "ops15", "조각")
RAWMD = os.path.join("dart_out", "ops15", "원문")
OUTTXT = os.path.join("dart_out", "ops15", "verify15_bs_g3.txt")
LIST_CSV = os.path.join("dart_out", "ops15", "사업보고서_원문.csv")
T13_ZIP = os.path.join("handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
MGMT_CSV = os.path.join("dart_out", "risk8", "경영공시_2026_2Q.csv")
WORK_JSON = os.path.join(FRAG, "bs_g3_work.json")
GEN = os.path.join("scripts", "dart", "ops15_bs_g3.py")
CORPS = ["BNK금융지주", "JB금융지주", "한국투자금융지주"]
SELF = {"BNK금융지주": ["BNK금융지주"], "JB금융지주": ["JB금융지주"], "한국투자금융지주": ["한국투자금융지주", "한국금융지주"]}
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
PICK = {"BNK금융지주": ["2020", "2025"], "JB금융지주": ["2019", "2023"], "한국투자금융지주": ["2019", "2023"]}

OUT = []
FAIL = []

# 검증하면서 고친 곳·반박 결과·손 대조(사람이 원문을 읽고 적은 것). 숫자는 위 자동 대조가 다시 셈.
REVIEW = [
    "### 완결 점검(수집 에이전트 보고가 없어 먼저 봄)",
    "- 고치기 전 조각(커밋된 것) md5: A 088a4bb5ceafddc0ae639385d6334f99 · B 89f8f32960f2269b6a4d79cba746604c · D 668bfe1d09483c5ba3f4594156cc1b93. "
    "생성기를 그대로 다시 돌리면 조각 CSV 3개·원문 md 53개·work json 이 모두 같은 md5 → 생성기와 조각이 맞음(손으로 고친 흔적 없음).",
    "- 회사×FY2019~2025 21칸 모두 A·B·D 행 있음. 원문 md: A 21·B 21(사업보고서) 모두 있음, D 는 행이 있는 11개(BNK 7·JB FY2022·한국투자 FY2023~2025) — "
    "D 「문서에 없음」 10행(JB 6·한국투자 4)은 source_text 가 없어 옮길 절이 없음(규칙 「행의 source_text 가 나온 절」). 빠진 md 없음.",
    "### 고친 곳(모두 생성기 scripts/dart/ops15_bs_g3.py 에 넣고 다시 돌림 — 두 번 돌려 같은 md5). 행 수 A 365→358 · B 114→112 · D 41→39",
    "- (c) BNK·JB 경영공시 2026.2Q 「미수집」 행 4개(B 2·D 2): source_text·rcept_no_or_url·page·doc_name·collected_at 이 빈칸 → 「모든 행에 출처」에 어긋나 "
    "행을 빼고 work json 「missing」(누락 목록)에 적음. 13차 텍스트·경영공시_2026_2Q.csv 에 두 회사 경영공시가 없고 이번 단계는 새 웹 수집이 없음.",
    "- (c) 「문서에 없음」 12행 page 빈칸 → 찾은 범위로 채움(g1·g2 와 같은 꼴): D 사업보고서 10행 「XML [절 a]~[절 b] 「X. …」~「…」 전체(찾은 범위 — 해당 글 없음)」"
    "(range_page), 한국투자 경영공시 B 1·D 1행 「p.1~p.55 전체(찾은 범위, PDF 쪽 — 해당 글 없음)」(mg_range). 바뀐 칸은 page 뿐.",
    "- (h)에서 찾음 — 한국투자 경력 칸 「(현)」 자르기 오류: career_items 가 「(현)」(3글자) 뒤를 s[4:] 로 잘라 회사 이름 첫 글자가 빠졌음"
    "(「(현)한국투자금융지주 부사장, 사장」→ 회사 「국투자금융지주」). 그래서 지주 자신 조각이 걸러지지 않아 지주 자신을 겸직 상대로 한 행 8개"
    "(오태균 FY2021~2025 5·이강행 FY2021~2023 3)가 들어가 있었음 → s[3:] 로 고쳐 8행 빠짐. 다른 회사 이름은 띄어쓰기 덕에 잘리지 않았음(고친 뒤 다른 행 차이 0).",
    "- (g) JB금융지주 FY2023(20240320001709) Ⅷ [표 1881] 「※ 회사와 계열회사간 임원 겸직 현황 (2023.12.31 기준)」을 생성기 basis_of 가 바로 앞 1행 임원 표"
    "(박종춘 출생년월 「1969년 03월」)에서 날짜를 읽어 「지난해 기준 표」로 빼고 있었음(행은 같은 내용의 Ⅸ [표 1908] 에서 들어와 빠진 겸직은 없었으나 "
    "page·note 「넣지 않은 지난해 기준 겸직 표: [표 1881] 1969년 03월」이 틀림). 앞 작은 표는 「기준·현재」 낱말이 있을 때만 쓰게 고침 → [표 1881] 은 "
    "기준일 표, JB FY2023 본 보고서 행의 page 가 Ⅷ [표 1881], note 「같은 행: Ⅸ [표 1908]」 로 바뀜(정정판 2개도 같이). 행 수는 그대로.",
    "- (g) BNK금융지주 FY2025 Ⅸ [표 1467] 「※공시서류작성기준일(2025.12.31) 이후 … 겸직현황(2026.03.17 현재)」의 기준을 첫 날짜 「2025.12.31」로 적던 것 → "
    "「현재·기준」이 바로 붙은 날짜 「2026.03.17」로(note 의 「기준 「…」」만 바뀜, 이후 표로 보는 판단은 같음).",
    "- (g) BNK금융지주 FY2020 Ⅸ [표 1174](2020.12.31 기준)의 「| - | 해당사항없음 | - | - | - |」 자리 행이 person 「-」·concurrent_company 「해당사항없음」인 "
    "겸직 행 1개로 들어가 있던 것 → 행에서 빼고, 그 보고서 A 행 note 에 「(판단) … 「해당사항없음」 자리 행만 있는 겸직 표는 행으로 넣지 않음: Ⅸ [표 1174]…」, work json judg 에 적음.",
    "- (g) JB 경력 칸이 한 경력 줄 안에서도 <br>·&cr; 로 줄을 바꿔(「- 2019 (주)전북은행 <br>부<br>행장보(現)」, 「Ltd.&cr; Managing Partner(現)」, "
    "「법무법인 지안 변호사<br>(<br>現<br>)」) 현직 표시 조각만 떨어져 나오던 것 → 현직 표시 조각에 회사 끝말 낱말이 없으면 같은 경력 줄(「- 」·연도로 시작) 앞 조각을 이어 붙임. "
    "결과: 이승국 FY2021 회사 「행장보」「부행장보」 2행은 겸직 표의 (주)전북은행·(주)광주은행 행과 같은 회사로 묶여 빠짐, 안상균 FY2019·2020 회사 「Managing」→"
    "「Anchor Equity Partners(Asia) Ltd.」, 그리고 놓치던 JB FY2023 정정판 2건(20240328001876·20240507000432)의 새 사외이사 이명상(법무법인 지안 변호사(現))·"
    "이희승(리딩에이스캐피탈 투자본부 이사(現)) 4행이 들어옴.",
    "- 회사·직위 나누기(판단 칸) 다듬기 17행: 「법무법인 태환 대표변호사」→ 회사 「법무법인 태환」(법인 종류 이름뿐인 낱말은 다음 낱말까지, 10행), 회사 끝 쉼표 뺌"
    "(「구글코리아,」·「세계화교학회(ISSCO, UC Berkeley),」 4행), Anchor 2행(위), 「구글코리아, 전무 (디렉터)」→ 회사 「구글코리아」·직위 「전무 (디렉터)」 1행. source_text 는 그대로.",
    "- (h) JB 정재식(서강대학교 사외이사) 출생년월이 FY2019~2022 「1961년 06월」, FY2023 「1961년 05월」 — 원문 그대로 두고 5행 note 에 "
    "「(판단) 같은 회사 다른 해 보고서에 같은 성명이 출생년월 1961.05·1961.06 로 적힘 — … 동일인 여부는 원문으로 가리지 않음」을 더함.",
    "- (i) D JB 6행(FY2020·2021·2022 2행·2023·2024) note 에 Ⅺ 제재 표 「2019년 종합검사 결과 지적사항 - 자회사와의 수수료 거래내역 미공시(금융지주회사법)」 위치를 "
    "(판단) 표시로 더함 — 지주–자회사 거래 언급이나 요청 계약 종류(업무위탁·용역·경영자문·전산 공동사용)가 아니어서 행으로 넣지 않음(g2 tx_note 와 같은 처리, 넣을지는 메인 판단).",
    "### 「문서에 없음」 반박 시도 결과",
    "- D 사업보고서 10행(JB FY2019~2021·2023~2025, 한국투자 FY2019~2022): 반박된 행 없음. 넓은 검색어+계열 낱말 줄은 JB 「IT보안 측면에서는, 자회사인 (주)전북은행, "
    "(주)광주은행, JB우리캐피탈(주)은 각각 차세대 전산개발 진행시 … 암호화 작업을 수행 완료」(자회사 각자의 전산개발 — 지주와의 계약·공동사용 아님), 제재 표 조치 칸 "
    "「업무지도 및 내부통제시스템 강화」「성과평가기준 및 전산시스템 개선」, 위 「자회사와의 수수료 거래내역 미공시」(note 로), 한국투자 「KIARA CAPITAL Ⅱ 계열회사 상환우선주」"
    "(출자 표), 「…위탁관리부동산투자회사」(회사 이름), 「에스케이위탁관리부동산투자회사 임원겸임 건 … 과태료」(자회사 한국투자부동산신탁 등의 공정거래법 기업결합(임원겸임) "
    "신고 제재 표 주석 — 지주 임원 겸직 행·사유가 아니어서 A 에도 넣지 않음, 메인 참고)뿐.",
    "- D·B 한국투자 경영공시 2026.2Q(55쪽): 업무위탁 뜻 검색어 0 — 넓은 낱말은 「(북경)투자자문유한공사」(회사 이름)·「투자자문 등」(업종)·「위탁매매」뿐이라 "
    "D note 의 「위탁매매·투자자문 같은 업종·회사 이름 낱말만 있음」과 같음; B 넓은 검색어(겸직·파견·출향·전출·전적·겸무·겸임·겸업·인사/인력교류·전보·지원인력) 0 → 유지.",
    "- B keyword 「없음」 7행(한국투자 FY2019~2025, 직원 수만): Ⅷ 에서 넓은 검색어로 걸린 것은 임원 경력 칸 「…미디어학부 겸임교수」·「…언론학 겸임교수」뿐"
    "(요청 키워드 아님, 직원 겸직·파견 서술 아님) → 유지. 공백·칸 줄바꿈 때문에 놓친 키워드 줄은 B·D 모두 0.",
    "- A reason_text 358행: 세 회사 사업보고서 31개(본·정정)에서 걸린 줄은 JB FY2022~2025 「…시행령은 2017년 9월 개정, 2017년 12월 시행으로 임원 겸직 승인 및 보고 범위를 "
    "확대하고 …」(법령 개정 서술) 7줄뿐 — 특정 겸직의 사유 글이 아님 → 유지(연차보고서 쪽 사유는 gov 조각 몫).",
    "### 손 대조(g1 과 같은 표본)",
    "- (g) 회사마다 2개 FY 겸직 표 전수(BNK FY2020·2025, JB FY2019·2023, 한국투자 FY2019·2023) 위 표대로 빠진 행 0. JB 표의 「(주)JB금융지주 | 부사장 …」 지주 자기 직위 줄은 "
    "생성기 판단대로 행이 아니고 그 아래 칸 합침 행(「| JB우리캐피탈(주) | 비상임이사 | …」)이 이름 줄과 두 줄로 A source_text 에 있음. JB Ⅸ 의 지난 2개년 표는 앞 글 "
    "「[2018년 12월말 기준]」 등으로 확인해 뺌(그 해 보고서 행에 있음). 한국투자 「임원약력」 표 현재 행도 빠짐 0.",
    "- (15차 wave6에서 고침 — 아래는 이전 판정) (a) 「두 줄 source_text 가운데 두 줄이 md 에서 이어지지 않는 행」 98: JB 겸직 표에서 이름 줄(지주 자기 직위 줄) 아래 둘째·셋째 회사 줄, 한국투자 「임원약력」 "
    "이름 줄(FY2019~2022 「(n) 성명」 글줄, FY2023~ 「| ■ 성명 |」 행) + 그 사람 기간 행 — 두 줄 사이에 다른 줄이 끼어 있을 뿐 줄마다 원문에 글자 그대로 있고 page 는 마지막 줄(그 행) 위치로 맞음.",
    "- (h) 출생년월 표본 20행(seed 1503) 모두 임원 현황 표 같은 성명 행의 출생년월 칸 원문과 같고 지주 직위·담당업무·등기·상근 칸도 같음(공백만 다른 칸: 생성기가 칸 안 겹친 공백을 하나로 줄임).",
    "- (f) B 숫자: 사업보고서 111행 모두 원문 직원 표 합계 행 칸과 같고 합계 = 기간의 정함이 없는 근로자 + 기간제; 한국투자 FY2023~2025 는 9차 값과도 같음(BNK·JB 는 9차에 없음).",
    "- 판단 목록: work json 「judg_rules」(생성기 규칙 15개)·「judg」(보고서별), 행마다는 note 「(판단)」.",
    "### 15차 wave6 고침(2026-11-03)",
    "- A 줄 이음 98행(JB·한국투자): source_text 를 이름 줄부터 그 행까지 사이 줄 포함해 이어서 옮김(모두 2,000자 이하). 한국투자 FY2019·2020 의 「(n) 성명」 머리 글줄은 "
    "표 앞 문단이라 md 표지 「[표 m]」 줄도 그대로 들어가고 page 는 「XML [절 n] 「…」 (문단)~[표 m]」.",
    "- A JB FY2023 정정판 2건(20240328001876·20240507000432)에 같은 새 사외이사 행: 먼저 접수된 정정판 행만 두고 다른 정정판은 note — 이명상·이희승·김기석 3행 뺌.",
    "- A BNK FY2023 김진한 1행: fulltime 은 겸직 표 비고/상근여부 칸 원문 값(상근), registered 「문서에 없음」.",
    "- A 회사·직위 나누기 고침 6행: 허진호 「종합법률사무소 그레이스」/「변호사」(FY2019~2022), 김영재 「부산대」/「경제통상대학장 겸 대학원장」, 함춘승 「㈜루트로닉」/「사업개발 및 리스크관리 본부장」.",
    "- B 「(정정판 합계 행)」 2행 keyword → 그 행 글의 키워드(「없음」), 정정판이라는 것은 note 「정정판 합계 행 — …」. 임원 현황 표 행 21행(BNK 20·한국투자 1) note 에 「(위치) 임원 현황 표 — 작업 A 와 겹침」.",
    "- D 검색어를 「위탁」으로 넓힘: 한국투자 FY2019~2025 Ⅺ 개인정보 글 21행(개인정보 처리방침 「위탁에 관한 사항」, 한국투자저축은행 「제공위탁」, 「위탁기관」). JB 「감독당국이 위탁한 금융보안원」은 넣지 않고 note 에.",
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
    return b


def cells_of(line):
    return [c.strip() for c in line.strip()[1:-1].split("|")]


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

    def sec(self, n):
        for k, (i, nn, t) in enumerate(self.heads):
            if nn == n:
                e = self.heads[k + 1][0] if k + 1 < len(self.heads) else len(self.L)
                return i, e, t
        return None

    def chap(self, roman):
        """로마 숫자 장 범위: 그 장 머리부터 다음 로마 장 또는 【 머리 전까지."""
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

    def table_rows(self, no):
        s, e = self.tabs[no]
        return [(i, cells_of(self.L[i])) for i in range(s + 1, e) if self.L[i].startswith("|")]


_T13 = {}


def t13(kind, corp):
    """13차 PDF 텍스트(「## p.N」). 그 회사 파일이 없으면 None(BNK·JB)."""
    if (kind, corp) not in _T13:
        z = zipfile.ZipFile(T13_ZIP)
        n = next((x for x in z.namelist() if x.endswith("텍스트/%s__%s.md" % (kind, corp))), None)
        if n is None:
            _T13[(kind, corp)] = None
            return None
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
        rows = md.table_rows(no)
        if not rows:
            continue
        h = [vnorm(c) for c in rows[0][1]]
        if not (len(h) > 7 and h[0] == "성명" and h[1] == "성별" and "출생" in h[2]):
            continue
        for i, c in rows[1:]:
            if len(c) >= 8 and not vnorm(c[0]).startswith("의결권"):
                out.append((i, c[0], c, no))
    return out


DATE = re.compile(r"(\d{4})\s*(?:년|\.)\s*(\d{1,2})")


def conc_tables(md, rng):
    """겸직 표: 첫 행에 성명과 대상회사·대상 계열사·회사명이 든 표 → [(표번호, 머리 칸들, 몸 행들, 꼴, 앞 글)].
    꼴 f5 = 「성명|대상회사(계열사)|직책|선임시기|비고」, kis = 「직명|성명|회사명|직책|상근여부」."""
    out = []
    for no, (s, e) in sorted(md.tabs.items(), key=lambda x: x[1][0]):
        if not (rng[0] <= s < rng[1]):
            continue
        rows = md.table_rows(no)
        if len(rows) < 2:
            continue
        h = [vnorm(c) for c in rows[0][1]]
        hj = "".join(h)
        if h[0] == "성명" and re.search(r"대상회사|대상계열사|겸직회사", hj):
            fmt = "f5"
        elif len(h) >= 4 and h[0] == "직명" and h[1] == "성명" and "회사명" in h[2]:
            fmt = "kis"
        elif "성명" in hj and re.search(r"겸직|겸임", hj):
            fmt = "?"
        else:
            continue
        before = []
        k = s - 1
        while k >= 0 and len(before) < 4 and s - k <= 10:
            l = md.L[k].strip()
            if l.startswith("###"):
                break
            if l and l not in ("[표 끝]",) and not re.match(r"\[표 \d+\]$", l) and re.sub(r"(&cr;|\s)", "", l):
                before.insert(0, l)
            k -= 1
        out.append((no, rows[0][1], rows[1:], fmt, before))
    return out


def basis_year(before, fy):
    """앞 글(가까운 것부터)에서 「기준·현재·말」 날짜 → (연, 원문). 생성기와 따로 — 사람이 읽을 수 있게 원문도 돌려줌."""
    for l in reversed(before):
        l2 = re.sub(r"(<br>|&cr;)", " ", l)
        if not re.search(r"기준|현재|말", l2):
            continue
        ms = list(DATE.finditer(l2))
        if not ms:
            continue
        m = next((x for x in ms if re.match(r"[^가-힣]{0,6}\s*(현재|기준|말)", l2[x.end():])), ms[-1])
        return int(m.group(1)), l.strip()[:90]
    return None, ""


# ================================================================ 원문 md(산출물) 읽기
def rawmd_blocks(path):
    """dart_out/ops15/원문/<T>/<회사>__FY<fy>__사업보고서.md → [(rcept, 절 번호, 제목, [줄])]."""
    L = open(path, encoding="utf-8").read().split("\n")
    out, i = [], 0
    while i < len(L):
        m = re.match(r"## .* — \[절 (\d+)\] (.*)$", L[i])
        if m:
            n, title = int(m.group(1)), m.group(2)
            j = i + 1
            rc = None
            while j < len(L) and L[j] != "```text":
                mm = re.match(r"- 출처: 접수번호 (\d+)", L[j])
                if mm:
                    rc = mm.group(1)
                j += 1
            k = j + 1
            while k < len(L) and L[k] != "```":
                k += 1
            out.append((rc, n, title, L[j + 1:k]))
            i = k + 1
            continue
        i += 1
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
    work = json.load(open(WORK_JSON, encoding="utf-8"))
    mds = {}

    def md_of(rc):
        if rc not in mds:
            r = lst.get(rc)
            mds[rc] = MD(r["text_path"]) if r and r["text_path"] and os.path.exists(r["text_path"]) else None
        return mds[rc]

    t13_rcept = {}
    for c in CORPS:
        P = t13("사업보고서", c)
        m = re.search(r"dart_out/doc/(\d+)/", P["head"]) if P else None
        t13_rcept[c] = m.group(1) if m else ""

    now = datetime.now(KST).isoformat(timespec="seconds")
    say("# 15차 검증 — 사업보고서 조각 g3 (BNK금융지주·JB금융지주·한국투자금융지주)")
    say("실행: %s (KST) · 스크립트 scripts/dart/verify15_bs_g3.py · 생성기 %s md5 %s · 웹 요청 없음 · 입력은 읽기만" % (
        now, GEN, hashlib.md5(open(GEN, "rb").read()).hexdigest()))
    say("대조 정규화: 공백·줄바꿈·「|」 무시(md 칸 안 줄바꿈 표시 <br>·&cr; 도 줄바꿈으로 보아 무시). 그 밖의 글자는 그대로 비교.")
    say("13차 본문 PDF 텍스트: 한국투자금융지주만 있음(FY2025 본 %s) — BNK·JB 는 PDF 쪽 없이 XML 위치만." % t13_rcept["한국투자금융지주"])
    say("")

    data = {}
    # ---------------------------------------------------------------- (c) 형식
    say("## (c) 열 이름·utf-8-sig·필수 칸·출처 목록 일치")
    for T in "ABD":
        p = os.path.join(FRAG, "%s_bs_g3.csv" % T)
        raw = open(p, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rd = csv.reader(open(p, encoding="utf-8-sig", newline=""))
        hdr = next(rd)
        rows = [dict(zip(hdr, r)) for r in rd]
        data[T] = rows
        say("- %s_bs_g3.csv: %d행, md5 %s, BOM %s, 열 %s" % (T, len(rows), hashlib.md5(raw).hexdigest(), "있음" if bom else "없음",
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
                fail("%s 줄 %d: g3 밖 회사 %s" % (T, k + 2, r["corp_label"]))
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
    LOC = re.compile(r"XML \[절 (\d+)\] 「(.*?)」 (?:\[표 (\d+)\]|\(문단\))(?:~\[표 (\d+)\])?")
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
                if P is None:
                    fail("%s 줄 %d: 경영공시 원문 텍스트 없음(%s)" % (T, ln, r["corp_label"]))
                    continue
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
                # 여러 줄 행(이름 줄 ~ 그 행)은 마지막 줄(그 행)이 page 표 안에 있어야 함 — 「(문단)~[표 m]」 꼴이면 [표 m] 안
                last = [x for x in src.split("\n") if x.strip()][-1]
                if good and m.group(4):
                    tb2 = md.tabs.get(int(m.group(4)))
                    rng = (tb2[0], tb2[1] + 1) if tb2 else (0, 0)
                if good and not md.find_lines(last, *rng)[0]:
                    good = False
                    fail("%s 줄 %d: source_text 가 page 위치(%s) 안에 없음" % (T, ln, r["page"][:60]))
                if good and not tno:
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
                    cands = ["".join(P["v"].get(p, "") for p in range(ps[0], ps[-1] + 1))]
                else:
                    cands = [P["v"].get(p, "") for p in ps]
                vs = vnorm(last)
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
    say("- 13차 본문 PDF 쪽(한국투자 FY2025): 그 쪽에 글 전체 %d행, 앞 80/40자만(PDF 표 칸 순서·줄바꿈 차이) %d행, 없음 %d행" % (
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
                ok = bool(P) and bool(m) and int(m.group(1)) == min(P["pages"]) and int(m.group(2)) == max(P["pages"])
                say("- %s 줄 %d %s %s: page 「%s」 — 실제 PDF 텍스트 p.%s~p.%s → %s" % (
                    T, ln, r["corp_label"], r["fy"], r["page"], min(P["pages"]) if P else "?", max(P["pages"]) if P else "?",
                    "맞음" if ok else "틀림"))
                if not ok:
                    fail("%s 줄 %d: 문서에 없음 행 page 가 찾은 쪽 범위와 다름" % (T, ln))
            else:
                md = md_of(r["rcept_no_or_url"])
                ns = [int(x) for x in re.findall(r"\[절 (\d+)\]", r["page"])]
                rx = md.chap_x_xi() if T == "D" else md.chap("VIII")
                want = sorted(set(n for i, n, t in md.heads if rx and rx[0] <= i < rx[1]))
                ok = bool(ns) and bool(want) and ns[0] == want[0] and ns[-1] == want[-1]
                say("- %s 줄 %d %s FY%s: page 「%s」 — %s 실제 [절 %s~%s] → %s" % (
                    T, ln, r["corp_label"], r["fy"], r["page"], "Ⅹ~Ⅺ" if T == "D" else "Ⅷ", want[0] if want else "?",
                    want[-1] if want else "?", "맞음" if ok else "틀림"))
                if not ok:
                    fail("%s 줄 %d: 문서에 없음 행 page 가 찾은 절 범위와 다름" % (T, ln))
    say("")

    # ---------------------------------------------------------------- (0) 원문 md 산출물
    say("## (0) 원문 md 산출물(dart_out/ops15/원문/<작업>/<회사>__FY<fy>__사업보고서.md) — 있음·절 글 그대로·행 글 포함")
    written = work.get("written", [])
    miss_w = [f for f in written if not os.path.exists(f)]
    say("- work json 「written」 %d개 — 없는 파일 %d" % (len(written), len(miss_w)))
    for f in miss_w:
        fail("원문 md 없음: " + f)
    blocks_cache = {}
    need = {}
    for T in "ABD":
        for k, r in enumerate(data[T]):
            if r["source_text"] == NONE or r["doc_kind"] != "사업보고서":
                continue
            need.setdefault((T, r["corp_label"], r["fy"]), []).append((k, r))
    blk_ok = blk_bad = row_ok = row_bad = 0
    for (T, c, fy), rows in sorted(need.items()):
        fn = os.path.join(RAWMD, T, "%s__FY%s__사업보고서.md" % (c, fy))
        if not os.path.exists(fn):
            fail("원문 md 없음(행 %d개): %s" % (len(rows), fn))
            row_bad += len(rows)
            continue
        if fn not in written:
            fail("원문 md 가 work json written 목록에 없음: %s" % fn)
        bl = blocks_cache.setdefault(fn, rawmd_blocks(fn))
        for rc, n, title, lines in bl:
            md = md_of(rc)
            sec = md.sec(n) if md else None
            if sec and sec[2] == title.strip() and md.L[sec[0]:sec[1]] == lines:
                blk_ok += 1
            else:
                blk_bad += 1
                fail("원문 md 절 글이 출처 md 와 다름: %s [절 %d] %s" % (fn, n, rc))
        for k, r in rows:
            n = int(re.search(r"\[절 (\d+)\]", r["page"]).group(1))
            b = [x for x in bl if x[0] == r["rcept_no_or_url"] and x[1] == n]
            last = [x for x in r["source_text"].split("\n") if x.strip()][-1]
            if b and vnorm(last) in vnorm("".join(b[0][3])):
                row_ok += 1
            else:
                row_bad += 1
                fail("%s 줄 %d: source_text 가 원문 md(%s)의 [절 %d] 블록에 없음" % (T, k + 2, fn, n))
    extra = []
    for T in "ABD":
        d = os.path.join(RAWMD, T)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.split("__")[0] in CORPS and f.endswith("__사업보고서.md"):
                p = os.path.join(d, f)
                if p not in written:
                    extra.append(p)
    say("- 행이 있는 (작업·회사·FY) %d칸 · md 절 블록 %d개 — 출처 md 그 절과 줄까지 같음 %d / 다름 %d · 행 글이 그 md 의 해당 절 블록에 있음 %d / 없음 %d" % (
        len(need), blk_ok + blk_bad, blk_ok, blk_bad, row_ok, row_bad))
    say("- 원문 폴더의 g3 사업보고서 md 가운데 written 목록 밖 파일 %d %s (연차보고서 md 는 gov 조각 몫이라 보지 않음)" % (
        len(extra), extra[:5]))
    for f in extra:
        fail("written 목록 밖 사업보고서 md(지난 실행 찌꺼기?): " + f)
    nd = sorted(set((r["corp_label"], r["fy"]) for r in data["D"] if r["source_text"] == NONE and r["doc_kind"] == "사업보고서"))
    say("- D 원문 md 가 없는 칸 = D 「문서에 없음」만 있는 칸 %d개(옮길 절 없음): %s" % (len(nd), ", ".join("%s FY%s" % x for x in nd)))
    for c, fy in nd:
        if os.path.exists(os.path.join(RAWMD, "D", "%s__FY%s__사업보고서.md" % (c, fy))) and not any(
                r["corp_label"] == c and r["fy"] == fy and r["source_text"] != NONE for r in data["D"]):
            fail("D 문서에 없음 칸인데 원문 md 가 있음: %s FY%s" % (c, fy))
    say("")

    # ---------------------------------------------------------------- (d) 비밀값
    say("## (d) 키·비밀값 문자열")
    files = [os.path.join(FRAG, "%s_bs_g3.csv" % T) for T in "ABD"] + [GEN, WORK_JSON, os.path.abspath(__file__)] + written
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
    say("- 본 파일 %d개(조각 CSV 3·생성기·work json·이 검증 스크립트·원문 md %d개): DART_API_KEY 값(환경변수 %s) 포함 0건이어야 함 / "
        "키 꼴 문자열(crtfc_key=·40자리 16진·토큰 꼴) — 걸린 것 %d" % (len(files), len(written), "있음" if key else "없음", hits))
    say("")

    # ---------------------------------------------------------------- (e) 회사×FY
    say("## (e) 회사×FY(2019~2025) 마다 A·B·D 각 1행 이상")
    miss = []
    for c in CORPS:
        line = []
        for fy in range(2019, 2026):
            n = [sum(1 for r in data[T] if r["corp_label"] == c and r["fy"] == str(fy)) for T in "ABD"]
            line.append("%d:%s" % (fy, "/".join(map(str, n))))
            for T, x in zip("ABD", n):
                if x == 0:
                    miss.append("%s %s FY%d" % (T, c, fy))
        n26 = [sum(1 for r in data[T] if r["corp_label"] == c and r["fy"] == "2026.2Q") for T in "BD"]
        say("- %s (A/B/D): %s · 2026.2Q 경영공시 B/D %d/%d" % (c, " ".join(line), n26[0], n26[1]))
    for x in miss:
        fail("행 없음: " + x)
    if not miss:
        say("  빠진 칸 없음")
    say("- 누락 목록(work json 「missing」, 행 없음): " + (" / ".join(work.get("missing", [])) or "없음"))
    say("")

    # ---------------------------------------------------------------- (f) B 숫자
    say("## (f) B 숫자 칸 = 원문 직원 표 합계 행 (source_text 또는 note 「합계 행: 「…」」 인용 안 숫자)")
    fb = 0
    seen = {}
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
                ts = [i for i in body if re.fullmatch(r"합계|총계|계", vnorm(cells_of(md.L[i])[0]))]
                if ts:
                    tot = ts[-1]
                    break
        if tot is None:
            fb += 1
            fail("B 줄 %d: 원문 직원 표 합계 행 못 찾음" % (k + 2))
            continue
        cells = cells_of(md.L[tot])
        want = dict(regular=cells[1], contract=cells[3], employees_total=cells[5])
        bad = [c for c in want if r[c] != want[c]]
        if r["keyword"] in ("없음", "(정정판 합계 행)"):
            quote = r["source_text"]
        else:
            quote = (re.search(r"합계 행: 「(.*?)」(?:;|$)", r["note"]) or [None, ""])[1]
        qok = bool(quote) and vnorm(quote) == md.vl[tot] and all(r[c] in quote for c in want)
        try:
            ar = int(want["regular"].replace(",", "")) + int(want["contract"].replace(",", "")) == int(want["employees_total"].replace(",", ""))
        except ValueError:
            ar = False
        if bad or not qok or not ar:
            fb += 1
            fail("B 줄 %d %s FY%s: 숫자 %s / 원문 합계 행 %s / 인용 %s / 합계=정함없음+기간제 %s" % (
                k + 2, r["corp_label"], r["fy"], [r[c] for c in want], [want[c] for c in want], "맞음" if qok else "다름", ar))
        seen[(r["corp_label"], r["fy"], r["rcept_no_or_url"])] = (want["employees_total"], want["regular"], want["contract"])
    say("- 사업보고서 B %d행 대조, 다른 행 %d (보고서 %d개)" % (sum(1 for r in data["B"] if r["doc_kind"] == "사업보고서"), fb, len(seen)))
    say("- 보고서별 합계·정함없음·기간제: " + "; ".join("%s FY%s %s %s" % (c[:2] if c != "한국투자금융지주" else "한투", fy, rc, "/".join(v))
                                              for (c, fy, rc), v in sorted(seen.items())))
    nine = {}
    if os.path.exists(os.path.join("handoff", "원문_지주조직_CRO.csv")):
        for r in csv.DictReader(open(os.path.join("handoff", "원문_지주조직_CRO.csv"), encoding="utf-8-sig")):
            nine.setdefault((r["corp_label"], r["fy"]), set()).add(r["employees"])
    cmp9 = []
    for c in CORPS:
        for fy in ("2023", "2024", "2025"):
            ours = {r["employees_total"] for r in data["B"] if r["corp_label"] == c and r["fy"] == fy and r["doc_kind"] == "사업보고서"
                    and r["keyword"] != "(정정판 합계 행)"}
            v9 = nine.get((c, fy))
            cmp9.append("%s FY%s ours %s / 9차 %s" % (c, fy, "·".join(sorted(ours)), "·".join(sorted(v9)) if v9 else "없음"))
            if v9 and not (ours & v9):
                fail("B %s FY%s 직원 수가 9차와 다름 %s / %s" % (c, fy, ours, v9))
    say("- 9차 원문_지주조직_CRO.csv employees 와 나란히(9차는 한국투자만 있음): " + "; ".join(cmp9))
    say("")

    # ---------------------------------------------------------------- (g) 겸직 표 전수(회사마다 2개 FY)
    say("## (g) 겸직 표 모든 행이 A 에 있는지 — 회사마다 2개 FY (겸직 표는 이 스크립트가 따로 찾음)")
    say("- 덮였다고 보는 경우: ① 그 줄 글이 같은 보고서 A source_text 에 있음(직접), ② 같은 사람·회사 A 행 note 에 그 표 번호(「같은 행: … [표 n]」), "
        "③ 지주 자기 직위 줄(겸직 상대가 지주 자신) — 그 사람의 A 행이 있음. 지난해 기준 표(앞 글 날짜가 보고 FY 보다 이른 것)는 그 해 보고서 몫이라 빼고 앞 글 원문을 적음.")
    summ = []
    for c in CORPS:
        for fy in PICK[c]:
            main_r = next(r for r in lst.values() if r["label"] == c and r["fy"] == fy and r["kind"] == "본")
            rc = main_r["rcept_no"]
            md = md_of(rc)
            r8, rx = md.chap("VIII"), md.chap("X")
            rng = (r8[0], rx[0] if rx else len(md.L))
            arows = [r for r in data["A"] if r["rcept_no_or_url"] == rc]
            av = [vnorm(r["source_text"]) for r in arows]
            T_tot = T_cov = 0
            for no, hdr, rows, fmt, before in conc_tables(md, rng):
                yr, btxt = basis_year(before, int(fy))
                if fmt == "?":
                    fail("겸직 표 꼴을 모름(생성기도 못 읽었을 수 있음): %s FY%s [표 %d] 머리 %s" % (c, fy, no, hdr))
                    continue
                if yr is not None and yr < int(fy):
                    say("- %s FY%s [표 %d] 지난해 기준 표 — 앞 글 「%s」 → 뺌(몸 행 %d) · 이 표를 page 로 쓴 A 행 %d" % (
                        c, fy, no, btxt, len(rows), sum(1 for r in arows if ("[표 %d]" % no) in r["page"])))
                    if any(("[표 %d]" % no) in r["page"] for r in arows):
                        fail("지난해 기준 표를 page 로 쓴 A 행: %s FY%s [표 %d]" % (c, fy, no))
                    continue
                full = len(hdr)
                prev = None
                tot = direct = same = selfrow = empty = 0
                missing = []
                hv = [vnorm(x) for x in hdr]
                for i, cs in rows:
                    if [vnorm(x) for x in cs] == hv:
                        prev = None
                        continue            # 표 안 두 번째 머리 행
                    if all(vnorm(x) in ("-", "해당사항없음", "해당없음", "없음", "") for x in cs):
                        empty += 1
                        if any(md.vl[i] and md.vl[i] in a for a in av):
                            fail("「해당사항없음」 자리 행이 A 행으로 들어감: %s FY%s [표 %d]" % (c, fy, no))
                        continue
                    tot += 1
                    if fmt == "f5":
                        if len(cs) == full:
                            name, comp = cs[0], cs[1]
                            prev = cs[0]
                        else:
                            name, comp = prev, cs[0]
                    else:
                        if len(cs) == 5:
                            name, comp = cs[1], cs[2]
                            prev = cs[1]
                        elif len(cs) == 4:
                            name, comp = cs[0], cs[1]
                            prev = cs[0]
                        else:
                            name, comp = prev, cs[0]
                    if any(ckey(s) in ckey(comp) for s in SELF[c]):
                        selfrow += 1
                        if not any(pkey(r["person"]) == pkey(name or "") for r in arows):
                            missing.append("[표 %d] md 줄 %d 지주 직위 줄인데 이 사람 A 행 없음 「%s」" % (no, i + 1, md.L[i][:70]))
                        continue
                    if any(md.vl[i] and md.vl[i] in a for a in av):
                        direct += 1
                        continue
                    cand = [r for r in arows if pkey(r["person"]) == pkey(name or "") and ckey(r["concurrent_company"]) == ckey(comp)
                            and ("[표 %d]" % no) in r["note"]]
                    if cand:
                        same += 1
                    else:
                        missing.append("[표 %d] md 줄 %d 「%s」" % (no, i + 1, md.L[i][:70]))
                T_tot += tot
                T_cov += tot - len([x for x in missing if "지주 직위 줄" not in x])
                say("- %s FY%s [표 %d](%s꼴, 앞 글 「%s」) 몸 행 %d — A source_text 에 그대로 %d · 같은 사람·회사 행 note 「[표 %d]」 %d · "
                    "지주 자기 직위 줄 %d · 「해당사항없음」 자리 행 %d(행 아님) · 빠짐 %d" % (
                        c, fy, no, fmt, btxt or (before[-1][:60] if before else ""), tot, direct, no, same, selfrow, empty, len(missing)))
                for x in missing:
                    fail("겸직 표 행이 A 에 없음: %s FY%s %s" % (c, fy, x))
            # 겸직 표 밖 A 행(임원 현황 칸·임원약력)
            outside = {}
            for r in arows:
                if "임원 현황 칸에서" in r["note"]:
                    m = re.search(r"\[표 (\d+)\]", r["page"])
                    outside[m.group(1) if m else "?"] = outside.get(m.group(1) if m else "?", 0) + 1
            say("  = %s FY%s 겸직 표 몸 행 %d 중 덮임 %d · 겸직 표 밖 A 행(임원 현황 칸·임원약력 표) 표별 %s" % (
                c, fy, T_tot, T_cov, outside or "없음"))
            summ.append("%s FY%s %d/%d" % (c, fy, T_cov, T_tot))
            # 한국투자 「임원약력」 표의 「현재」 행
            if c == "한국투자금융지주":
                s = next((i for i in range(*r8) if "임원약력" in md.L[i] and not md.L[i].startswith("|")), None)
                cur = None
                bt = bc = bself = 0
                bmiss = []
                if s is not None:
                    for i in range(s + 1, r8[1]):
                        l = md.L[i]
                        ls = re.sub(r"^(?:&cr;|\s)+", "", l)
                        if re.match(r"(나\.|다\.|###)", ls):
                            break
                        if not l.startswith("|"):
                            m = re.match(r"\((\d+)\)\s*(\S.*?)(?:&cr;|\s)*$", ls)
                            if m:
                                cur = pkey(m.group(2))
                            continue
                        cs = cells_of(l)
                        if cs and cs[0].startswith("■"):
                            cur = pkey(cs[0].lstrip("■"))
                            continue
                        if cur and len(cs) == 2 and "현재" in cs[0]:
                            bt += 1
                            body = cellv(cs[1])
                            if any(ckey(x) in ckey(body) for x in SELF[c]):
                                bself += 1
                                continue
                            pr = [r for r in arows if pkey(r["person"]) == cur]
                            if any(md.vl[i] in vnorm(r["source_text"]) for r in pr) or any(
                                    ckey(r["concurrent_company"]) and ckey(r["concurrent_company"]) in ckey(body) for r in pr):
                                bc += 1
                            else:
                                bmiss.append("md 줄 %d %s 「%s」" % (i + 1, cur, body[:50]))
                say("  · 「임원약력」 표 기간 칸 「현재」 행 %d — 지주 자신 %d · A 에 있음(그 줄 또는 같은 사람·회사 행) %d · 빠짐 %d" % (
                    bt, bself, bc, len(bmiss)))
                for x in bmiss:
                    fail("임원약력 현재 행이 A 에 없음: %s FY%s %s" % (c, fy, x))
    say("- 손 대조 요약(덮인 행/몸 행): " + " · ".join(summ))
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
        # 지주 칸(직위·등기·상근·담당업무)은 공백만 무시하고 비교(생성기가 칸 안 겹친 공백을 하나로 줄임 — 글자는 같음)
        good = [x for x in mt if all(vnorm(r[f]) == vnorm(v) for f, v in flds(x).items())]
        x = good[0] if good else mt[0]
        dif = [] if good else [f for f, v in flds(x).items() if vnorm(r[f]) != vnorm(v)]
        if dif:
            fail("A 줄 %d: %s 이 같은 성명·출생년월 임원 표 행 어느 것과도 다름 %s" % (k + 2, dif, [(r[f], flds(x)[f]) for f in dif]))
        if len(births) > 1:
            amb += 1
            if not ("출생년월" in r["note"] and "(판단)" in r["note"]):
                fail("A 줄 %d: 같은 성명 출생년월 %s 인데 note 에 동명이인 표시 없음" % (k + 2, births))
        detail[k] = (x, births, dif)
    say("- birth_ym 찬 행 %d: 임원 표 같은 성명 행 출생년월과 다름 %d, 같은 성명이 출생년월 둘 이상인 행 %d(note 「(판단)」 확인)" % (
        len(detail) + len(bad_b), len(bad_b), amb))
    for k in sorted(detail):
        if len(detail[k][1]) > 1:
            r = data["A"][k]
            say("    줄 %d %s FY%s %s birth_ym %s · 같은 성명 출생년월 %s" % (k + 2, r["corp_label"], r["fy"], r["person"], r["birth_ym"],
                                                                "/".join(detail[k][1])))
    say("- birth_ym 빈칸 행 %d: 같은 보고서 임원 표에 그 성명 없음 %d, 있음(잘못) %d" % (blank_ok + len(blank_bad), blank_ok, len(blank_bad)))
    # 회사 안 같은 성명·다른 출생년월(동명이인 후보, 여러 해)
    pb = {}
    for k, r in rows_b:
        if r["birth_ym"]:
            pb.setdefault((r["corp_label"], pkey(r["person"])), set()).add(bkey(r["birth_ym"]))
    homo = ["%s %s %s" % (c, p, sorted(v)) for (c, p), v in sorted(pb.items()) if len(v) > 1]
    say("- 회사 안 같은 성명·다른 출생년월(여러 해 통틀어, 동명이인 후보): %d %s" % (len(homo), "; ".join(homo)))
    rnd = random.Random(1503)
    samp = rnd.sample(sorted(detail), min(20, len(detail)))
    say("- 표본 20행(seed 1503): csv 줄 · 회사 FY · 성명 · birth_ym ↔ 임원 표 [표 n] 줄 · 출생년월 칸 원문 · 같은 성명 출생년월들 · 지주 칸 일치")
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
            hits, broad = [], {}
            for p, v in sorted(P["v"].items()):
                for w in re.findall(r"업무위탁|위수탁|위탁계약|수탁계약|용역|경영자문|자문계약|자문료|공동사용|공동이용|공동전산|전산공동|"
                                    r"아웃소싱|업무지원|위탁업무|수탁업무", v):
                    pos = v.find(w)
                    hits.append("p.%d「%s」" % (p, v[max(0, pos - 18): pos + 18]))
                for mm in re.finditer(r"위탁|수탁|자문|전산|공동", v):
                    ctx = v[max(0, mm.start() - 6): mm.end() + 6]
                    broad.setdefault(mm.group(0), []).append("p.%d「%s」" % (p, ctx))
            say("- D 줄 %d %s 2026.2Q 경영공시: 업무위탁 뜻 넓은 검색어 걸린 곳 %d %s" % (k + 2, r["corp_label"], len(hits), " / ".join(hits[:8])))
            for w, xs in broad.items():
                say("    넓은 낱말 「%s」 %d곳: %s%s" % (w, len(xs), " / ".join(xs[:6]), " …" if len(xs) > 6 else ""))
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
    WIDE_B = r"겸직|파견|출향|전출|전적|겸무|겸임|겸업|인사교류|인력교류|전보|지원인력"
    for k, r in enumerate(data["B"]):
        if r["source_text"] == NONE:
            P = t13("경영공시", r["corp_label"])
            hits = []
            for p, v in sorted(P["v"].items()):
                for mm in re.finditer(WIDE_B, v):
                    if mm.group(0) == "전보" and re.match(r"보(통주|완자본)", v[mm.start() + 1: mm.start() + 5]):
                        continue        # 「차감전 보통주자본·보완자본」
                    if re.search(r"완전적|전적으로|전적인|사전적|전출입", v[max(0, mm.start() - 1): mm.end() + 2]):
                        continue
                    hits.append("p.%d「%s」" % (p, v[max(0, mm.start() - 18): mm.end() + 18]))
            say("- B 줄 %d %s 2026.2Q 경영공시: 넓은 검색어(%s, 공백 무시) 걸린 곳 %d %s" % (
                k + 2, r["corp_label"], WIDE_B.replace("|", "·"), len(hits), " / ".join(hits[:8])))
            if any(re.search(r"겸직|파견|출향|전출|전적|겸무", h) for h in hits):
                fail("B 줄 %d: 문서에 없음인데 경영공시에 요청 키워드가 있음" % (k + 2))
        elif r["keyword"] == "없음" and r["note"].startswith("정정판 합계 행"):
            # (15차 wave6) 정정판 합계 행: keyword 는 그 행 글의 키워드 — 합계 행 글에 요청 키워드가 없어야 함
            if re.search(r"겸직|파견|출향|전출|전적|겸무", vnorm(r["source_text"])):
                fail("B 줄 %d: 정정판 합계 행 keyword 「없음」인데 그 행 글에 요청 키워드가 있음" % (k + 2))
            say("- B 줄 %d %s FY%s 정정판 합계 행 keyword 「없음」: 그 행 글에 요청 키워드 없음 확인" % (k + 2, r["corp_label"], r["fy"]))
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
                    if re.search(r"전적으로|전적인|사전적|완전적|전출입", md.vl[i]):
                        continue
                    if not any(md.vl[i] in b or b in md.vl[i] for b in brows if b):
                        missed.append("%s FY%s %s md%d %s「%s」" % (L["label"], L["fy"], rc, i + 1, kw, md.vl[i][:50]))
    say("- B: 공백·칸 줄바꿈이 낱말 사이에 끼어 원래 검색에 안 걸렸을 줄(공백 무시 검색으로만 걸리고 B 에 없는 줄): %d" % len(missed))
    for x in missed:
        say("    %s" % x)
        fail("B 키워드 누락 가능: " + x)
    # D 키워드 누락(공백 끼임)
    dmissed = []
    DKW = r"업무위탁|업무수탁|위수탁|위탁계약|수탁계약|용역|경영자문|자문계약|자문료|자문수수료|공동사용|공동이용"
    for rc, L in lst.items():
        md = md_of(rc)
        if md is None:
            continue
        rx = md.chap_x_xi()
        if not rx:
            continue
        drows = [vnorm(r["source_text"]) for r in data["D"] if r["rcept_no_or_url"] == rc]
        for i in range(rx[0], rx[1]):
            mm = re.search(DKW, md.vl[i])
            if mm and not re.search(DKW, md.L[i].replace("ㆍ", "").replace("·", "")):
                if not any(md.vl[i] == b for b in drows):
                    dmissed.append("%s FY%s %s md%d 「%s」" % (L["label"], L["fy"], rc, i + 1, md.vl[i][max(0, mm.start() - 15): mm.end() + 15]))
    say("- D: 공백이 낱말 사이에 끼어 원래 검색에 안 걸렸을 Ⅹ~Ⅺ 줄(공백 무시로만 걸리고 D 에 없는 줄): %d" % len(dmissed))
    for x in dmissed[:20]:
        say("    %s" % x)
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
    na = sum(1 for r in data["A"] if r["reason_text"] == NONE)
    say("- A reason_text(%d행 가운데 「문서에 없음」 %d): 세 회사 사업보고서 %d개(본·정정) 전체를 넓은 검색어(%s, 공백 무시)로 다시 찾음 — 걸린 줄 %d" % (
        len(data["A"]), na, len([1 for rc in lst if md_of(rc)]), REASON.replace("|", "·"), len(rs)))
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

    # ---------------------------------------------------------------- 셈(보고용)
    wave6(data, say, fail, CORPS)          # (15차 wave6) 새 원문 대조 규칙·고침 점검
    say("## 셈 — 작업별·회사별 행 수, 「문서에 없음」 행 수")
    for T in "ABD":
        tot = len(data[T])
        n0 = sum(1 for r in data[T] if r["source_text"] == NONE)
        per = []
        for c in CORPS:
            rr = [r for r in data[T] if r["corp_label"] == c]
            per.append("%s %d(문서에 없음 %d)" % (c, len(rr), sum(1 for r in rr if r["source_text"] == NONE)))
        extra = ""
        if T == "A":
            extra = " · reason_text 「문서에 없음」 %d/%d" % (sum(1 for r in data[T] if r["reason_text"] == NONE), tot)
        if T == "B":
            extra = " · keyword 「없음」(직원 수만) %d · 키워드 행 %d" % (
                sum(1 for r in data[T] if r["keyword"] == "없음"),
                sum(1 for r in data[T] if r["keyword"] not in ("없음", "(정정판 합계 행)")))
        say("- %s: %d행 · 「문서에 없음」 %d (%.1f%%) · %s%s" % (T, tot, n0, 100.0 * n0 / tot if tot else 0, " · ".join(per), extra))
    say("")

    say("## 사람이 읽고 적은 것(검증자 판단, %s KST)" % now[:10])
    for x in REVIEW:
        say(x)
    say("")
    say("## 결과")
    say("실패 %d건 → exit %d" % (len(FAIL), 1 if FAIL else 0))
    return OUT


if __name__ == "__main__":
    main()
    txt = "\n".join(OUT) + "\n"
    open(OUTTXT, "w", encoding="utf-8").write(txt)
    print("verify15_bs_g3: 실패 %d건 → %s" % (len(FAIL), OUTTXT))
    sys.exit(1 if FAIL else 0)
