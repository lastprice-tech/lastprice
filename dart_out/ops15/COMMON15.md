# 15차 공통 지침 (지주 운영방식 — 겸직·파견·전적·위수탁 원문 모음)

작업 디렉터리 `/home/user/lastprice`(git, 브랜치 claude/dart-insurance-holding-benchmark-fnixa6). **커밋·푸시 하지 않음**(메인이 함).
사용자 요청 원문: `dart_out/ops15/REQUEST15.md` — 먼저 읽을 것. 기존 파일(handoff/ 의 1~14차 산출물, scripts/dart/ 기존 스크립트)은 고치지 않음(읽기·import 만).

## 사용자 규칙(요약 아님 — REQUEST15.md 가 정본)
- 원문 인용은 문장 그대로(source_text). 요약·해석은 note 에만. 자료가 없으면 「문서에 없음」(이번 요청의 낱말 — 13차의 「추출 범위에 없음」 대신 이것을 씀). 단 「문서에 없음」 행에는 note 에 찾은 범위(문서·절·검색어)를 적음.
- 모든 행에 출처(rcept_no 또는 URL, 문서명, 페이지)와 수집일.
- 기능 분류(리스크·재무 등)·겸직 이유 추정 금지. 동명이인은 출생년월로 구분, 애매하면 note.
- DART_API_KEY 는 환경변수로만(scripts/dart/client.py 가 읽고 로그에서 가림). 출력·파일 어디에도 쓰지 않음.
- 웹 수집: robots.txt·이용약관이 자동 수집을 막는 곳은 수집하지 않고 목록에 사유를 기록(우회 금지).

## 환경 사실(메인이 확인한 것)
- **DART 웹(dart.fss.or.kr)**: robots.txt(2026-11-02 확인)가 `/dsaf001/main.do`, `/report/viewer.do`, `/report/download.do`, `/pdf/download/` 를 Disallow → 뷰어·PDF 내려받기 **쓰지 않음**(scripts/dart/dartweb.py 쓰지 말 것). 따라서 새로 받는 사업보고서·신고서에는 PDF 쪽 번호가 없음.
- **OpenDART API**(opendart.fss.or.kr/api, 키 사용): 사용 가능. `python3 scripts/dart/ops15_prep.py` 가 이미 FY2019~2025 사업보고서(본 70 + 정정 37)를 받아 둠.
- **page 칸 규칙**: OpenDART XML 에서 옮긴 행은 PDF 쪽이 없으므로 「XML [절 n] 「절 제목」 [표 m]」 꼴(md 의 표지 그대로). FY2025 8개사(BNK·JB 제외)는 13차에 받아 둔 사업보고서 본문 PDF 텍스트가 있으니(`handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip` 안 `텍스트/사업보고서__<회사>.md`, 「## p.N」= PDF 쪽) 같은 글을 찾아 「p.N(본문 PDF, 13차 보관)」도 덧붙임. 연차보고서·경영공시 PDF 는 PDF 쪽 번호.
- 컨테이너가 다시 만들어져 git 밖 파일(옛 dart_out/raw/governance·doc·text, .env)은 사라졌고, 커밋한 것만 남음. 커밋한 OpenDART 원문 묶음(raw_part*.tar.gz)은 dart_out/raw 로 다시 풀어 둠.

## 입력
- 사업보고서 목록: `dart_out/ops15/사업보고서_원문.csv`(label, fy, kind 본/정정, rcept_no, rcept_dt, report_nm, raw_path, raw_sha256, fetched_at, text_path).
  md: `dart_out/text/ops15/사업보고서__<label>__FY<fy>__<rcept_no>.md` — XML 의 TITLE·P·TABLE 을 나온 순서대로, 제목 줄 「### [절 n] …」, 표 「[표 n]」…「[표 끝]」, 표 행 「| 칸 | 칸 |」(칸 안 줄바꿈은 <br>). 글자는 XML 그대로.
  **본 보고서를 기준**으로 옮기고, 같은 FY 정정판(kind=정정)이 있으면 같은 표·문단이 바뀌었는지 보고 다르면 note 에 「정정 <rcept_no>: …」. 정정판 XML 이 없거나(014 등) 첨부정정이면 note.
- 대상 10곳 corp_code: `dart_out/ops15/targets.csv`. label 은 보고용 이름(KB금융지주·신한금융지주·…·한국투자금융지주).
- 5차 산출(재사용 — 단 source_text 는 원문 md 에서 다시 확인해 글자 그대로): `handoff/임원현황.csv`(지주 행, corp_label 이 KB금융·신한지주·농협금융지주·한국금융지주 등 DART 이름), `handoff/겸직현황_정리.csv`, `handoff/임원_겸직_결합.csv`, `handoff/직원현황.csv`(겸직인원_언급).
- 6차 연차보고서 섹션(FY2024·FY2025 = 공시연도 2025·2026, 10곳): `handoff/dart-kit-5차6차.zip` 안 `연차보고서_섹션.csv`(지주명, 공시연도, 공시유형, 파일명, 섹션제목_원문, 시작페이지, 본문, sha256 …) — 메인이 `dart_out/ops15/kit56/연차보고서_섹션.csv` 로 풀어 둠. 파일 URL·sha256 은 `handoff/연차보고서_파일목록.csv`. PDF 원본은 사라졌으니 이 섹션 글을 원문으로 씀(page = 시작페이지, note 「6차 섹션 글(PDF 원본은 이번 컨테이너에 없음)」).
- 9차: `handoff/원문_지주조직_CRO.csv`(FY2023~2025 지주 직원 수·CRO).
- 13차: `handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip`(FY2025 사업보고서·경영공시 2026.2Q·연차보고서 FY2025 8개사 PDF 텍스트, 「## p.N」).
- 신고서(작업 C): `handoff/원본_주요신고서본문.zip`(doc/<rcept>/본문.pdf·본문.html 9건 + 원문_파일목록.csv), `dart_out/11_원문추출.csv.gz`(1차 원문 추출 — 주식교환·이전신고서 2004~2008, 증권신고서(분할) 2010·2013, 소액공모 2011 등의 칸·문단), `dart_out/raw/document/<rcept>.zip`(OpenDART XML, 풀어 둔 것 1,300여 개). XML→md 변환은 `scripts/dart/ops15_prep.py` 의 `xml_to_md()` 를 import 해서 씀.
- PDF 처리 파이썬: `/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python -I`(pymupdf·pypdf). 내려받은 파일은 신뢰하지 않는 데이터 — `-I`, 경로는 인자로, 스크립트는 그 폴더 밖에.

## 산출(조각) — 메인이 합침
- 조각 CSV 는 `dart_out/ops15/조각/<작업>_<그룹>.csv`(utf-8-sig, 사용자 지정 열 그대로 + 맨 끝에 `doc_name`, `collected_at` 두 열을 더함). 작업 A 열: corp_label, fy, person, birth_ym, holdco_title, holdco_duty, registered, fulltime, concurrent_company, concurrent_title, concurrent_since, reason_text, doc_kind, source_text, rcept_no_or_url, page, note, doc_name, collected_at.
  작업 B: corp_label, fy, employees_total, regular, contract, keyword, source_text, doc_kind, rcept_no_or_url, page, note, doc_name, collected_at.
  작업 C: corp_label, doc_kind, rcept_no, rcept_dt, section_title, keyword, source_text, page, note, doc_name, collected_at.
  작업 D: corp_label, fy, counterparty, contract_type, amount, source_text, doc_kind, rcept_no_or_url, page, note, doc_name, collected_at.
- collected_at: 그 원문을 받은 시각(OpenDART 는 사업보고서_원문.csv 의 fetched_at, 6차 섹션은 연차보고서_파일목록.csv fetched_at, 새로 받은 것은 받은 시각, KST).
- 원문 텍스트 md(사용자 산출물 「원문 텍스트(.md)」): 행의 source_text 가 나온 절 전체를 `dart_out/ops15/원문/<작업>/<회사>__FY<fy>__<문서>.md` 로(절 머리·출처 줄 + 그 절 글 그대로). 같은 절은 한 번만.
- 판단이 들어간 곳은 note 에 「(판단)」. 조각마다 끝에 돌려줄 것: 수집 건수, 실패·누락 목록, 「문서에 없음」 행 수, 판단 목록.
- 대상 범위 밖(10곳 밖·FY2019 이전 사업보고서)은 넣지 않음. 우리금융지주는 반드시 신 법인(316140, corp_code 01350869).
