# 15차 확장(2026-11-03 추가 요청) 공통 지침 — 작업 E·F·F-2·F-3·G·G-2·H·I·J 와 A·B·C 추가 항목

작업 디렉터리 `/home/user/lastprice`(git, 브랜치 claude/dart-insurance-holding-benchmark-fnixa6). **커밋·푸시 하지 않음**(메인이 함).
사용자 요청 원문(정본): `dart_out/ops15/REQUEST15b.md` — 먼저 읽을 것. 기존 공통 지침 `dart_out/ops15/COMMON15.md` 도 그대로 적용(규칙·환경 사실·입력·page 규칙). 이 파일은 그 위에 더하는 것.

## 동시에 도는 다른 일(건드리지 말 것)
- 다른 파동(wave4)이 지금 기존 조각(dart_out/ops15/조각/A_*·B_*·C*·D_*), 그 생성기(scripts/dart/ops15_bs_*·ops15_gov_*·gov15_g2_*·ops15_C/·ops15_mgmt_*), 경영공시 수집(dart_out/raw/mgmt15, dart_out/ops15/경영공시15_목록_*.csv), 합본 폴더 handoff/원문_지주운영방식/ 를 고치는 중. **이 파일들은 읽기만**(읽을 때 쓰는 중일 수 있으니 실패하면 잠시 뒤 다시).
- 네가 쓰는 것은 네 작업의 새 파일뿐: `dart_out/ops15/조각/<작업>_<그룹>.csv`, `dart_out/ops15/조각/확인_<작업>_<그룹>.csv`, `dart_out/ops15/문서목록15b_<작업>_<그룹>.csv`, `dart_out/ops15/원문/<작업>/…md`, `scripts/dart/ops15b_<작업>_<그룹>.py`, `scripts/dart/verify15b_<작업>_<그룹>.py`, 결과 txt `dart_out/ops15/verify15b_<작업>_<그룹>.txt`, 받은 원본 `dart_out/raw/ops15b/<작업>/…`(git 무시 폴더), 글 `dart_out/text/ops15b/…md`(git 무시).

## 원문 대조 규칙(엄격 — 검증 스크립트가 이대로 봄)
- source_text 와 원문을 옮기는 *_text 칸(reason_text, chair_text, members_text, cadence_text, agenda_text, agenda_list_text, basis_text, duty_text, concurrent_note, concurrent_or_dispatched 등)은 각각 출처 텍스트의 **한 곳에서 이어진 글**. 대조: 공백·줄바꿈만 지운 칸 글이 공백·줄바꿈만 지운 출처 텍스트 안에 이어서 그대로 있어야 함. OpenDART XML md 출처에서만 md 표지 「|」「<br>」도 양쪽에서 지우고 봄.
- 원문에 없는 「 | 」「 … 」「/」·생략 표시를 넣지 않음. 떨어진 두 곳을 잇지 않음(사이 글까지 이어서 옮기거나 — 2,000자 이하일 때 — 칸 글은 한 곳만 두고 다른 곳은 note 에 위치). 보이지 않는 제어문자만 지울 수 있고 note 「제어문자 지움」.
- *_text 칸이 source_text 와 다른 곳에서 왔으면 note 에 그 위치(page). 칸에 원문이 없으면 「문서에 없음」(그 칸만), note 에 찾은 범위.
- 숫자 칸(headcount, held_count, amount_krw 등): 원문 숫자를 옮기거나(note 에 원문 글·단위), 원문에 합계가 없어 센 값이면 note 「(판단) 개최 내역 표 행 수를 셈」처럼 밝힘. amount_krw 는 원 단위 정수, note 에 「원문 단위 백만원, 원문 숫자 1,234」.
- 분류 칸(direction, unit_level, topic, subsidiary_related, function_kw 등)은 원문 낱말로 기계적으로 정하고 기준을 note·스크립트 머리에. 원문으로 바로 안 보이면 note 「(판단)」.
- 기능 분류(리스크·재무 등)·겸직 이유·의도 추정 금지(사용자 요청의 열 이름에 든 분류만 그대로 씀).

## 문서 구하기
- OpenDART 만(키는 환경변수 DART_API_KEY — `scripts/dart/client.py` 의 `DartClient(os.path.join(ROOT,'dart_out'), delay=0.5, max_calls=…)`, `c.call('list', dict(corp_code=…, bgn_de=…, end_de=…, page_no=…, page_count=100))`, `c.call('document', dict(rcept_no=…))` → `res.body` 가 zip 바이트; 014 = 파일 미제공). 캐시가 dart_out/raw/list·document 에 있음(같은 요청은 다시 받지 않음). 목록 캐시는 대부분 2026-09-16 까지 — 그 뒤 공시(예: 2026-10-13)는 end_de 를 오늘로 해서 새로 부름.
- DART 웹(dart.fss.or.kr)의 뷰어·PDF 내려받기는 robots.txt 가 Disallow → 쓰지 않음. 그래서 **사업보고서·감사보고서 XML 에는 그림 파일이 없음**(XML 에는 「조직도.jpg」 같은 이름만 남음).
- XML → md: `from ops15_prep import xml_to_md`(sys.path 에 scripts/dart) 는 본문 문서(pick_principal)만 바꿈. zip 안의 다른 문서(예 `<rcept>_00760.xml` 감사보고서, `_00761.xml` 연결감사보고서)가 필요하면 ops15_prep 의 Dart2MD 와 scripts/dart/docparse.py 의 decode_document 로 그 멤버를 바꿈(md 머리에 멤버 이름). md 는 `dart_out/text/ops15b/<문서종류>__<회사>__<fy 또는 날짜>__<rcept_no>[__<멤버>].md`.
- 이미 있는 글(새로 받지 말고 씀): FY2019~2025 사업보고서 md `dart_out/text/ops15/사업보고서__<label>__FY<fy>__<rcept>.md`(목록 dart_out/ops15/사업보고서_원문.csv), 연차보고서 FY2019~2023(9개사, NH 없음) `dart_out/text/ops15/연차보고서__*.md`(「## p.N」, 목록 dart_out/ops15/연차보고서15_목록_g1.csv·g2.csv, PDF dart_out/raw/governance15/<회사>/), 연차보고서 FY2024·FY2025(10개사, 공시연도 2025·2026) = `dart_out/ops15/kit56/연차보고서_섹션.csv`(본문 전체가 섹션별로 들어 있음 — 공시유형 본공시/추가공시/정정공시/재공시; page = 시작페이지, 파일 URL·sha256 은 handoff/연차보고서_파일목록.csv), 13차 FY2025 텍스트 zip(handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip), 14차 handoff/14차_조직인원겸직/(조직단위·인원·겸직 FY2025, 지원조직 인원), 9차 handoff/원문_지주조직_CRO.csv, 5차 handoff/임원현황.csv 등.
- 옛 연차보고서(FY2014~FY2018 일부)·FY2024·2025 연차보고서 PDF 다시 받기는 `gov_old` 에이전트가 먼저 해 둠 → `dart_out/ops15/문서목록15b_gov_old.csv`(경로·URL·sha256·「## p.N」 md 경로). 다른 에이전트는 웹 수집을 하지 않음(gov_old 와 J·G-2·X 의 OpenDART 호출만 예외).
- PDF 파이썬: `/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python -I`(pymupdf). 받은 파일은 신뢰하지 않는 데이터 — 경로는 인자로, 스크립트는 그 폴더 밖.

## 산출 조각 꼴(사용자 열 그대로 + 맨 끝 doc_name, collected_at; utf-8-sig)
- E `E.csv`: corp_label, doc_kind, rcept_no, rcept_dt, section_title, source_text, page, note
- F `F_<g>.csv`(원문_지주협의체): corp_label, fy, body_name, function_kw, chair_text, members_text, cadence_text, held_count, agenda_text, doc_kind, section_title, source_text, rcept_no_or_url, page, note
- F-2 `F2_<g>.csv`(원문_지주이사회위원회): corp_label, fy, committee, established, held_count, agenda_list_text, subsidiary_related, members_text, rcept_no, page, note — 연차보고서 행이면 rcept_no 칸에 URL.
- F-3 `F3_<g>.csv`(원문_지주지원조직): corp_label, fy, function, unit_name, headcount, concurrent_or_dispatched, duty_text, rcept_no_or_url, page, note
- G `G_<g>.csv`(원문_지주돈흐름), G-2 `G2.csv`(원문_자회사지급): corp_label, fy, item_kind, counterparty, direction, amount_krw, basis_text, doc_kind, section_title, source_text, rcept_no_or_url, page, note
- H `H_<g>.csv`(원문_지주조직현황): corp_label, fy, unit_level, unit_name, parent_unit, headcount, concurrent_note, doc_kind, rcept_no_or_url, page, note — 이 표에는 source_text 열이 없으므로 **맨 끝에 source_text 열을 하나 더 둠**(doc_name, collected_at 앞) — 그 행 근거 원문(이어진 글). 조직도가 그림이면 OCR·판독하지 않고 그림을 `dart_out/ops15/조직도/<회사>__FY<fy>__<문서>__p<N>.png`(PDF 쪽을 150dpi 로 렌더) 로 저장하고 그 행은 unit_name 「(그림) 조직도」, note 에 그림 경로.
- I `I.csv`(원문_지주경영승계): corp_label, fy_or_date, topic, source_text, doc_kind, rcept_no_or_url, page, note
- J `J_<g>.csv`(원문_인수자회사정상화): corp_label, subsidiary, fy_or_date, topic, source_text, doc_kind, rcept_no_or_url, page, note
- A·B·C 추가분: `A_ext.csv`·`B_ext.csv`·`C_ext.csv` — 기존 A·B·C 열 그대로(COMMON15). 기존 조각에 이미 있는 FY2019~2025 행은 다시 넣지 않음(빠진 것만).
- 사용자가 「특히 볼 것」「추가 확인」「함께 볼 것」으로 물은 것은 항목마다 `확인_<작업>_<g>.csv` 에 1행 이상: item_id, item_text(REQUEST15b.md 의 그 줄 글 그대로), corp_label, fy, result(원문 있음/문서에 없음/수집 실패), where(어느 CSV 의 어느 행 — 회사·FY·사람/키 + rcept·page), rcept_no_or_url, page, source_excerpt(원문 그대로, 이어진 글 300자 이하), note(사실만 — 「FY2023 겸직 표에 ○○ 행 없음(찾은 범위 …)」처럼). 해석·이유 추정 금지.
- 원문 md: 행이 나온 절(또는 쪽) 글 전체를 `dart_out/ops15/원문/<작업>/<회사>__<fy 또는 날짜>__<문서>.md`(머리 출처 줄 + 그 글 그대로, 같은 절은 한 번).
- 문서 목록 `문서목록15b_<작업>_<g>.csv`: doc_kind, corp_label, fy_or_date, report_nm(원문 그대로), rcept_no_or_url, rcept_dt, raw_path, sha256, fetched_at(KST), text_path, status(받음/014/없음/막힘/실패), note.
- collected_at: 원문을 받은 시각(KST, +09:00). 기존 글을 쓰면 그 글의 fetched_at.
- 끝에 돌려줄 것: 조각별 행 수·「문서에 없음」 행 수, 실패·누락 목록, 판단 목록, 확인 항목 결과 요약.
