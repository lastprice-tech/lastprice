export const meta = {
  name: 'ops15-wave6',
  description: '15차 6차 파동(사용 한도 뒤 다시): 옛 연차보고서 수집 → A~D 고침·경영공시 검증 → 확장 작업 F·G·I·X2·A_ext·H·J·G-2 수집과 독립 검증. 한 에이전트라도 실패하면 멈추고 다음에 이어 돌림',
  phases: [{ title: 'Collect', detail: '수집·고침' }, { title: 'Verify', detail: '독립 검증' }],
}
const HEAD = `You are a sub-agent in /home/user/lastprice (Korean financial-holding-company disclosure research). FIRST read dart_out/ops15/REQUEST15b.md (the user's request, verbatim — the 정본), dart_out/ops15/COMMON15.md (binding rules, environment facts, inputs, page rule) and dart_out/ops15/COMMON15b.md (rules for this extension: strict verbatim rule, file ownership, output formats, where documents are). Key rules: source_text and every *_text column = exact contiguous copy from the source text (no edits, no inserted 「|」/「…」), interpretation only in note, 「문서에 없음」 when absent (+ where searched in note), every row has source (rcept_no or URL, doc_name, page) and collected_at, NO function classification or reason guessing, same-name people distinguished by birth year-month, never print/write DART_API_KEY or secrets, do NOT git commit, write only your own files (another wave is editing the existing A–D fragments and handoff/원문_지주운영방식/ at the same time — read-only for you). Keep tool outputs small (grep -n / sed ranges; big intermediates to files) — agents have died from oversized outputs and from usage limits, so work efficiently and write outputs incrementally (per company) so partial work survives; at start check whether a previous attempt left partial outputs of yours and continue from them. Get time via \`date\` (write KST). Answer in Korean via structured output.

YOUR TASK:
`
const RSCHEMA = { type: 'object', properties: { checker: { type: 'string' }, exit: { type: 'integer' }, rows: { type: 'array', items: { type: 'string' } }, fixed: { type: 'array', items: { type: 'string' } }, failures: { type: 'array', items: { type: 'string' } }, not_in_doc: { type: 'array', items: { type: 'string' } }, judgments: { type: 'array', items: { type: 'string' } }, checks: { type: 'array', items: { type: 'string' } }, remaining: { type: 'array', items: { type: 'string' } } }, required: ['checker', 'exit', 'rows', 'fixed', 'failures', 'not_in_doc', 'judgments', 'checks', 'remaining'] }
const G1 = 'KB금융지주·신한금융지주·하나금융지주·우리금융지주·NH농협금융지주'
const G2C = '메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주'

const GOV_OLD = `옛 연차보고서와 FY2024·2025 연차보고서 PDF 받기(이 파동의 웹 수집 담당). 네 소유: scripts/dart/ops15b_gov_old.py, dart_out/raw/ops15b/gov_old/, dart_out/text/ops15b/연차보고서__*.md, dart_out/ops15/문서목록15b_gov_old.csv.
 (1) 받을 것: 지배구조 연차보고서(이름은 해마다 다름 — 「지배구조 및 보수체계 연차보고서」「지배구조 연차보고서」 등; 공시연도 = FY+1): KB금융지주 FY2014~FY2018, 신한금융지주 FY2017·FY2018, 하나금융지주 FY2017·FY2018, BNK금융지주 FY2017·FY2018, iM금융지주(옛 DGB금융지주) FY2018. 그리고 FY2024·FY2025 10개사 연차보고서 PDF(본공시, 그리고 추가·정정공시가 목록에 있으면 그것도)를 handoff/연차보고서_파일목록.csv 의 URL 로 다시 받아 sha256 이 목록과 같은지 기록(다르면 둘 다 기록하고 그대로 둠). 이 PDF 들은 작업 H 의 조직도 쪽 그림과 F·G·I 의 쪽 확인에 씀.
 (2) 규칙: robots.txt — scripts/dart/web13.py 의 Robots(RFC 9309: 4xx = 제한 없음, 5xx·연결 실패 = 받지 않음); 2026-11-02 판정이 dart_out/raw/governance15/robots_판정.json 에 있음(다시 확인해 기록). 이용약관의 자동 수집 금지 문구 확인·기록. 우회 금지(UA 위장·다른 호스트·캐시·미러·검색엔진 캐시 쓰지 않음). NH nhfngroup.com 은 2026-11-02 에 HTTP 400 차단 — 한 번 다시 시도, 막히면 기록만. 요청 사이 1초 이상, 같은 파일 재시도 2회까지. 옛 해가 누리집에 없으면 「누리집에 없음」(찾아본 게시판 URL 기록). 방법 참고: scripts/dart/ops15_gov_g1.py·scripts/dart/gov15_g2_*.py(15차에 FY2019~2023 을 받은 스크립트), dart_out/ops15/연차보고서15_목록_g1.csv·g2.csv(그때 URL·게시판).
 (3) 글: PDF 마다 「## p.N」 md(pymupdf, COMMON15 의 venv, -I, 경로는 인자로) → dart_out/text/ops15b/연차보고서__<회사>__FY<fy>[__<공시유형>].md. 글자층이 없거나 깨지면 실패 목록(그림으로 읽지 않음).
 (4) dart_out/ops15/문서목록15b_gov_old.csv(COMMON15b 의 문서 목록 열 + robots_verdict, terms_note, board_url): 대상 칸(회사×FY×공시유형)마다 1행 — 받음/누리집에 없음/막힘/실패.
 rows: 받은 수와 대상별 status. failures: 회사·FY·사유·URL.`

const F = (g, corps) => `작업 F·F-2·F-3 그룹 ${g}(${corps}). 네 소유: dart_out/ops15/조각/F_${g}.csv·F2_${g}.csv·F3_${g}.csv·확인_F_${g}.csv, dart_out/ops15/원문/F/·F2/·F3/ 의 이 그룹 회사 md, scripts/dart/ops15b_F_${g}.py, scripts/dart/verify15b_F_${g}.py 와 결과 txt, dart_out/ops15/문서목록15b_F_${g}.csv(쓴 문서).
 F(FY2023~FY2025): 출처 — 연차보고서 FY2023(dart_out/text/ops15/연차보고서__… md, 목록 dart_out/ops15/연차보고서15_목록_g1.csv·g2.csv; NH 는 FY2019~2023 이 없음 — 기록), FY2024·FY2025(dart_out/ops15/kit56/연차보고서_섹션.csv, 공시연도 2025·2026; 본공시를 기준으로, 추가·정정·재공시가 다르면 note), 사업보고서 FY2023~FY2025 md(dart_out/text/ops15/사업보고서__…)의 Ⅱ(자회사 경영관리 방식 서술)·Ⅵ(위원회 밖 회의체)·내부통제 관련 서술. 협의체 = 이사회 내 위원회가 아닌 경영진·그룹 회의체(원문 이름 그대로 body_name — 협의회·협의체·회의·위원회 등). 협의체 1개 × 연도 1행. 같은 협의체가 연차보고서와 사업보고서 둘 다에 있으면 연차보고서 글을 기준 1행으로 하고, 사업보고서에만 있는 칸은 그쪽에서 옮기고 note 에 위치. function_kw = REQUEST15b 작업 F 키워드 중 body_name·source_text 에 든 낱말(기계적, 「, 」로). chair_text·members_text·cadence_text·agenda_text 는 원문 글(없으면 그 칸 「문서에 없음」). held_count 는 원문 횟수 또는 개최 내역 행 수(판단 note), 없으면 「문서에 없음」. 이사회 내 위원회는 F 에 넣지 않음.
 F-2(FY2024·FY2025): 이사회 내 위원회 중 자회사대표이사후보추천위원회(원문 이름은 회사마다 — 자회사최고경영자후보추천위원회·자회사CEO후보추천위원회 등), 내부통제위원회, 감사위원회, ESG위원회(지속가능경영위원회 등 원문 이름), 위험관리위원회(리스크관리위원회 등). 회사×FY×위원회 1행(없는 위원회는 「문서에 없음」 행). 출처: 사업보고서 Ⅵ 위원회 활동 표(개최일자·의안) — 연차보고서 위원회 활동 내역이 더 자세하면 그것(어느 쪽인지 note). agenda_list_text = 그 위원회 개최 내역 표 글(이어진 글 그대로, 길어도). held_count = 원문 횟수 또는 표의 개최일 수(판단 note). subsidiary_related = agenda_list_text 에 「자회사」「그룹」「계열사」가 있으면 Y 아니면 N(기계적). established = 원문 설치일(없으면 「문서에 없음」). members_text = 위원 구성 원문.
 ${g === 'g1' ? '함께 볼 것: NH 내부통제위원회 첫 개최일·첫 안건(FY2024 — NH 연차보고서 FY2024 는 6차 섹션, 사업보고서 FY2024 md), 신한 「자회사경영관리위원회」가 없어지거나 자회사최고경영자후보추천위원회로 합쳐진 시점과 사유(FY2022·FY2023 사업보고서 md·연차보고서 md) → 그 해 F-2 행과 확인_F_g1.csv.' : '함께 볼 것: BNK 내부통제위원회 첫 개최일·첫 안건(FY2024) → F-2 행과 확인_F_g2.csv.'}
 F-3(FY2025): 연차보고서 FY2025(6차 섹션 공시연도 2026)의 「준법감시인·위험관리책임자 지원조직 현황」·「감사위원회 지원조직(내부감사부서) 현황」 표 — 표 행(부서)마다 1행. function = 표 제목·칸의 원문 표현, unit_name·headcount·duty_text 원문, concurrent_or_dispatched = 겸직·파견 표시 원문(없으면 「문서에 없음」). 14차 handoff/14차_조직인원겸직/14_지원조직_인원.csv(사업보고서 기준)와 맞대어 다르면 note 에 사실만. 연차보고서에 그 표가 없으면 「문서에 없음」 행 + note(사업보고서에 있으면 그 위치).
 검증 스크립트 scripts/dart/verify15b_F_${g}.py(인자 없이 exit 0/1, 결과 dart_out/ops15/verify15b_F_${g}.txt — 대조 규칙대로 모든 *_text 칸·source_text 전수)를 만들어 exit 0 확인.`

const G = (g, corps) => `작업 G 그룹 ${g}(${corps}), FY2019~FY2025. 네 소유: dart_out/ops15/조각/G_${g}.csv·확인_G_${g}.csv, dart_out/ops15/원문/G/ 의 이 그룹 md, scripts/dart/ops15b_G_${g}.py, scripts/dart/verify15b_G_${g}.py 와 결과 txt, dart_out/ops15/문서목록15b_G_${g}.csv.
 (1) 별도재무제표 주석의 특수관계자 거래(사업보고서 md 의 Ⅲ 「재무제표 주석」 — 연결이 아니라 별도. 본문 md 에 별도 주석이 없으면 zip 의 감사보고서 멤버를 md 로 바꿔 씀 — COMMON15b). 특수관계자와의 손익 거래 표의 행마다: counterparty(원문) × item_kind(원문 계정명 — 열 또는 행 머리 그대로) × 금액 1행. direction: 표의 수익 쪽 계정 「지주 수입」, 비용 쪽 「지주 지출」(표 머리로 기계적, 애매하면 (판단)). amount_krw 원 단위 정수(note 「원문 단위 백만원, 원문 숫자 …」). 당기 금액만(전기 열 넣지 않음). 0·「-」 칸은 넣지 않음(스크립트 머리에 밝힘). 배당: 특수관계자 거래 표에 없으면 별도 주석의 종속기업 배당금수익 표·문단에서. 자회사가 아닌 특수관계자(관계기업·주요 경영진 등) 행도 원문 그대로. source_text = 그 표 행 한 줄(XML md 의 「| … |」 줄), 열 머리는 note 「열: …」. 표 꼴이 해마다 다르면(가로·세로, 칸 합침, 대분류 행) 회사·해마다 확인해 맞춤.
 (2) 사업보고서 Ⅱ: 영업수익 구성 표·문단, 상표권(브랜드) 사용료 산정 기준 문단 → 그 해 상표권·브랜드 수익 행의 basis_text 에 원문(위치 note). 수익 행이 없으면 item_kind 「(산정 기준 문단)」 1행. 다른 행의 basis_text 는 산정 기준 원문이 없으면 「문서에 없음」.
 (3) 연차보고서(FY2019~FY2023 dart_out/text/ops15, FY2024·2025 6차 섹션${g === 'g1' ? ', 신한·KB·하나 FY2017·FY2018 은 dart_out/ops15/문서목록15b_gov_old.csv 의 md' : ''}): 겸직 임원 보수를 어느 회사가 주는지·나누는 기준 문단 → item_kind 「(겸직 임원 보수 지급·배분 기준)」, direction 은 원문으로 정해지면 그것(판단 note) 아니면 「문서에 없음」, basis_text·source_text 원문.${g === 'g1' ? ' 신한·KB·하나 FY2017~FY2025: 겸직 부문장의 성과평가 지표(부문 KPI·법인 KPI 비중)와 보수 지급 회사 문단도 같은 꼴(item_kind 「(겸직 부문장 성과평가·보수)」).' : ''}
 (4) 확인_G_${g}.csv — REQUEST15b 작업 G 「특히 볼 것」 중 이 그룹 항목마다: ${g === 'g1' ? 'KB·하나·우리 FY2025(필요하면 FY2019~) 브랜드(상표권) 수수료 수익 유무·금액·자회사별 상대방, 경영관리·용역 수수료 수익 유무; 신한 FY2025 브랜드수수료 자회사별 내역·산정 기준(요율·기준 수익) 기재 여부; KB·신한·하나·우리·NH FY2025 사업보고서 임원 보수 주석의 「겸직 임원 보수는 ○○가 지급」·업무분담비율 정산 문구; 신한·KB·하나 FY2017~FY2025 연차보고서의 겸직 부문장 성과평가 지표·보수 지급 회사' : 'BNK·iM·JB FY2025(필요하면 FY2019~) 브랜드(상표권) 수수료 수익 유무·금액·자회사별 상대방, 경영관리·용역 수수료 수익 유무'}.
 검증 스크립트 scripts/dart/verify15b_G_${g}.py(exit 0/1; 대조 규칙 + amount_krw = 원문 숫자×단위)로 exit 0 확인.`

const G2T = `작업 G-2(선택) — 자회사 쪽에서 본 FY2025 흐름. 네 소유: dart_out/ops15/조각/G2.csv·확인_G2.csv, dart_out/ops15/원문/G2/, scripts/dart/ops15b_G2.py, scripts/dart/verify15b_G2.py 와 결과 txt, dart_out/ops15/문서목록15b_G2.csv, dart_out/raw/ops15b/G2/.
 대상(FY2025 = 2025.12 결산): 은행 — 국민은행·하나은행·우리은행·부산은행·iM뱅크(옛 대구은행)·전북은행; 보험 — KB손해보험·KB라이프생명·신한라이프생명·하나생명·하나손해보험·동양생명·ABL생명; IT — KB데이타시스템·신한DS·하나금융티아이·우리FIS·농협정보시스템·BNK시스템·iM데이터시스템(옛 DGB데이터시스템). corp_code 는 dart_out/raw/corpCode 캐시(CORPCODE.xml)에서 이름으로(옛 이름 주의, 찾은 근거 note). OpenDART 목록에서 FY2025 사업보고서(있으면) 또는 감사보고서(공시유형 F)를 찾아 document → md(감사보고서 멤버).
 뽑을 것: 별도 재무제표 주석의 특수관계자 거래 중 상대방이 그 지주(○○금융지주)인 손익 행 — 지급수수료(브랜드·용역)·임차료·인건비 정산 등 자회사 비용 쪽 → direction 「자회사 지출」; 지주에게서 받은 수익 행이 있으면 direction 「자회사 수입」으로 넣고 note (판단). 열은 G 와 같음(amount_krw 원 단위, 원문 단위 note). IT 법인: 용역 대가 산정 방식(원가가산·종량제·정액 등 원문 표현)과 계약 상대방이 지주인지 각 자회사인지 — 수익인식·특수관계자 주석 원문 → item_kind 「(용역 대가 산정 방식)」 행.
 확인_G2.csv: 회사마다 1행 이상(지주에 낸 것 — 원문 있음/문서에 없음/수집 실패). 검증 스크립트 verify15b_G2.py exit 0.`

const H = (g, corps) => `작업 H 그룹 ${g}(${corps}), FY2019~FY2025. 네 소유: dart_out/ops15/조각/H_${g}.csv·확인_H_${g}.csv, dart_out/ops15/원문/H/ 의 이 그룹 md, dart_out/ops15/조직도/<이 그룹 회사>__*.png, scripts/dart/ops15b_H_${g}.py, scripts/dart/verify15b_H_${g}.py 와 결과 txt, dart_out/ops15/문서목록15b_H_${g}.csv.
 출처: (a) 사업보고서 md FY2019~2025 — 조직 관련 서술·표, 직원 현황의 부서별 인원 표(예 BNK — 부서·인원·겸직/파견 구분). 「조직도.jpg」처럼 그림 이름만 있는 자리는 그림이 없음(OpenDART XML 에 그림 파일 없음, DART 뷰어·PDF 는 robots 로 쓰지 않음) → 그 해 행 unit_name 「(그림) 조직도」, source_text 그 줄, note 「XML 에 그림 이름만 — 그림 받을 수 없음」. (b) 연차보고서 FY2019~2023 PDF(dart_out/raw/governance15/<회사>/, md dart_out/text/ops15/연차보고서__…)와 FY2024·2025 PDF(dart_out/ops15/문서목록15b_gov_old.csv 의 raw_path·text_path) — 조직 서술 문단, 조직도 쪽, 조직·인력 표. (c) (요청 문서 밖, 판단) 경영공시 PDF(dart_out/raw/mgmt15/<회사>/, 목록 dart_out/ops15/경영공시15_목록_g1.csv·g2.csv — 다른 파동이 받은 것, 있는 것만)의 조직도·조직 현황 쪽 — note 「(판단) 요청 문서 밖 — 사업보고서 조직도 그림을 받을 수 없어 덧붙임」. (d) 14차 handoff/14차_조직인원겸직/14_조직단위_인원_겸직.csv(FY2025, 판독 포함)는 대조용만 — 원문에서 다시 옮기고, 14차와 다르면 note.
 조직도 쪽: PDF 쪽에 글자층(벡터 글)이 있으면 그 쪽 글에서 부문·본부·부서 이름을 옮김(source_text = 그 쪽 글의 이어진 부분). parent_unit 은 원문 글이 위계를 말할 때만(표 열, 「○○부문 산하」 등); 그림 배치로만 알 수 있으면 「문서에 없음」 + note 「배치는 그림 참조: <그림 경로>」. 쪽이 래스터 그림뿐이면 OCR·판독하지 않음 — 그림만 저장하고 행 1개(unit_name 「(그림) 조직도」). 조직도 쪽은 어느 경우든 150dpi PNG 로 dart_out/ops15/조직도/<회사>__FY<fy>__<문서>__p<N>.png 에 저장(경로 note).
 unit_level: 이름 끝 낱말로 기계적(…부문·…그룹·…총괄 → 「부문」, …본부·…센터·…실·…단 → 「본부」, …부·…팀 → 「부서」 — 기준을 스크립트 머리에; 애매하면 원문 표현 + (판단)). headcount = 원문 인원(없으면 「문서에 없음」). concurrent_note = 겸직·파견 표시 원문(예 「(겸)」「은행 겸직」, 없으면 빈칸이 아니라 「문서에 없음」). 열 끝에 source_text 를 더함(COMMON15b).
 확인_H_${g}.csv — REQUEST15b 작업 B 의 부서별 인원 항목 중 이 그룹 것: ${g === 'g1' ? 'FY2025 하나·우리·NH 가 BNK 처럼 부서별 인원과 겸직·파견 구분을 적었는지(사업보고서·연차보고서·경영공시 각각)' : 'FY2025 iM·JB 가 BNK 처럼 부서별 인원과 겸직·파견 구분을 적었는지; BNK FY2022~FY2024 준법감시부·감사·윤리경영부 인원; iM FY2023~FY2024 그룹감사총괄·그룹준법감시인 산하 인원'}.
 검증 스크립트 verify15b_H_${g}.py exit 0.`

const I = `작업 I(10개사). 네 소유: dart_out/ops15/조각/I.csv·확인_I.csv, dart_out/ops15/원문/I/, scripts/dart/ops15b_I.py, scripts/dart/verify15b_I.py 와 결과 txt, dart_out/ops15/문서목록15b_I.csv, dart_out/raw/ops15b/I/.
 (1) 연차보고서: 회장·은행장 겸직이나 분리를 정한 이유 문단 — KB FY2014~FY2017(dart_out/ops15/문서목록15b_gov_old.csv 의 md), 우리 FY2019(dart_out/text/ops15 연차보고서 md), DGB(iM) FY2018(gov_old)·FY2019·FY2020(text/ops15), BNK FY2017(gov_old). topic 은 원문 낱말로 「겸직 결정」 또는 「분리」(애매하면 (판단)). 문서가 없으면(누리집에 없음 등) 확인 행에 「수집 실패」와 사유.
 (2) 8개 은행지주(KB·신한·하나·우리·NH·iM·BNK·JB) FY2025 연차보고서(6차 섹션 공시연도 2026): 자회사 CEO 후보 관리와 경영성과 평가 절차·평가지표 문단·표 → topic 「자회사 CEO 평가」.
 (3) 자회사의 주요경영사항 공시(은행장 선임): 지주 corp_code(dart_out/ops15/targets.csv) 의 OpenDART 목록(캐시 dart_out/raw/list 에 있으면 그것, 없으면 새로; 거래소공시 포함)에서 우리 2020-03, DGB 2020-09, iM 2024-03·2026-01, BNK 2017(한 해) 기간 보고서명에 「자회사의 주요경영사항」「대표이사」「은행장」「임원」 등이 든 것 → document → 겸직 시작·종료 일자와 임기 문장·표(topic 원문 낱말로, 판단 note). 같은 달 지주 자신의 대표이사 변경 공시도. fy_or_date = 공시일(YYYY-MM-DD) 또는 FY.
 (4) 확인_I.csv: 위 사건·연도마다 1행(원문 있음/문서에 없음/수집 실패). 검증 스크립트 verify15b_I.py exit 0.`

const J = (g) => `작업 J 그룹 ${g}. 네 소유: dart_out/ops15/조각/J_${g}.csv·확인_J_${g}.csv, dart_out/ops15/원문/J/ 의 이 그룹 md, scripts/dart/ops15b_J_${g}.py, scripts/dart/verify15b_J_${g}.py 와 결과 txt, dart_out/ops15/문서목록15b_J_${g}.csv, dart_out/raw/ops15b/J_${g}/. 문서는 OpenDART(목록 캐시는 2026-09-16 까지 — 그 뒤는 end_de 오늘로 새로). 자회사 corp_code 는 dart_out/raw/corpCode 캐시에서 이름으로(옛 이름 주의, 근거 note). topic = 겸직/이사회/증자/지분/합병/기타 중 원문 낱말로 기계적(애매하면 (판단)). subsidiary = 원문 회사명. fy_or_date = FY 또는 공시일.
${g === 'g1' ? ` - 신한지주 사업보고서 FY2022~FY2025(dart_out/text/ops15 md): 임원 겸직 현황의 신한EZ손해보험 비상임이사(이름·직책·기간) 행, 타법인 출자 현황의 EZ 지분율 행.
 - 신한EZ손해보험(옛 BNP파리바카디프손해보험) 감사보고서 FY2021~FY2025: 증자(사용자가 적은 2021 200억·2022 800억·2025 1,000억은 확인 대상 — 원문 수치를 옮기고 맞는지는 확인 행 note 에 사실로), KT·더존 신주 인수 금액(자본금·주주·유상증자 주석).
 - 신한지주 주요사항보고서(2026-10-13 전후): 롯데손해보험 주식 취득, 잔여 지분 처리와 EZ 통합 문구.
 - 하나금융지주 「자회사 주식 취득 결정」 등(2025-09 전후): 교직원공제회 잔여 10.41% 매입 금액.
 - 하나금융지주 사업보고서 FY2020~FY2025(md): 임원 겸직의 하나손해보험 비상임이사 행.
 - 하나손해보험(옛 더케이손해보험) 감사보고서 FY2020~FY2025: 증자 세부와 당기순이익(2023·2024 수치 원문).` : ` - 우리금융지주 사업보고서 FY2025(dart_out/text/ops15 md): 조직도의 보험 관련 조직(XML 에 그림 없음 — 글로 있는 것만, 없으면 확인 행에 그 사실), 동양생명·ABL생명 비상임이사 겸직 행, 종속기업 취득의 인수가·염가매수차익(사업결합 주석).
 - 우리금융지주 포괄적 주식교환 주요사항보고서(2026-04-24~04-29, 정정 포함): 교환 목적, ABL 합병 계획 문구.
 - 동양생명·ABL생명 FY2025 사업보고서 또는 감사보고서: 이사회 구성, 임원 변동, K-ICS(지급여력비율) 원문.
 - DGB금융지주(iM금융지주 00878915) 주요사항보고서·자회사 편입 공시(2015-01 전후): DGB생명 편입·취득가액.
 - DGB생명(현 iM라이프생명, 옛 우리아비바생명) 감사보고서 FY2015~FY2025: 증자 이력, 지주 겸직 이사.
 - KB금융 사업보고서 FY2015~FY2017(OpenDART — 다른 에이전트가 FY2016~2018 를 같은 캐시로 받을 수 있음)·FY2020~FY2022(md 있음): KB손해보험·푸르덴셜생명·KB생명보험 비상임이사와 대표 겸직 표기 행.
 - 금융위 의결서의 편입 승인 부대조건(2020-04-29 하나·더케이손보, 2022-06-09 신한·BNP카디프손보, 2020-08-26 KB·푸르덴셜)은 사용자가 「DART 밖(채팅에서 확인)」이라 함 → 수집하지 않고 확인 행에 그 사실만.`}
 확인_J_${g}.csv: 위 줄마다 1행 이상(원문 있음/문서에 없음/수집 실패). 검증 스크립트 verify15b_J_${g}.py exit 0.`

const X1 = `작업 A 추가분. 네 소유: dart_out/ops15/조각/A_ext.csv·확인_A_ext.csv, dart_out/ops15/원문/A/ 에 새 문서 md(기존 파일과 이름이 겹치지 않게 — 새 FY·새 문서만), scripts/dart/ops15b_A_ext.py, scripts/dart/verify15b_A_ext.py 와 결과 txt, dart_out/ops15/문서목록15b_A_ext.csv, dart_out/raw/ops15b/A_ext/.
 (1) 사업보고서(11011) 옛 해: 신한 FY2017·FY2018, KB FY2016~FY2018, 하나 FY2017·FY2018, BNK FY2018 — 목록 캐시(dart_out/raw/list/<corp_code>_…json)에서 rcept_no(정정판도) → document → md(ops15_prep.xml_to_md). Ⅷ 임원 현황·타회사 임원 겸직 현황 표 → 기존 A 와 같은 꼴(겸직 1건당 1행 — 생성 방식은 scripts/dart/ops15_bs_g1.py 를 읽어 따르되 import 하지 말고 네 스크립트로). 그 해 연차보고서(dart_out/ops15/문서목록15b_gov_old.csv 의 md)의 임원 겸직 현황·겸직 사유 문단도 기존 연차보고서 꼴(scripts/dart/ops15_gov_g1_extract.py 참고).
 (2) 우리투자증권 FY2025 사업보고서(corp_code 는 corpCode 캐시 — 이름 확인, 근거 note): 은행 IB 부행장의 CIB시너지본부장 겸직 기재 → A_ext 행(corp_label 「우리투자증권」, note 「자회사 문서」).
 (3) 2026 반기보고서(보고서코드 11012, 2026.06 기준, 2026-08 공시 — 목록은 end_de 오늘로 새로): KB·우리·NH·신한·BNK 의 Ⅷ 임원 현황·겸직 표 → A_ext 행(fy 「2026 반기」).
 (4) 확인_A_ext.csv — REQUEST15b 작업 A 「추가 확인」 줄마다(신한 FY2017~18 GIB 5개사·GID·GMS 4개사·퇴직연금 부문장 겸직 대상; KB FY2016~18 WM·CIB 총괄 3사 겸직·연금기획부 부서 단위 4사 겸직 표기 여부; 하나 FY2017~19 은행↔금투 WM·IB 그룹장 겸직; 신한 FY2023·FY2024 GIB·글로벌 사업그룹장이 지주 겸직에서 빠졌는지·은행↔증권 겸직으로 바뀌었는지 — 해마다 원문 행을 맞대어 사실만; 우리 FY2019~FY2022 WM·글로벌·CIB·디지털 총괄·연금기획부의 은행·카드·종금 겸직; 우리투자증권 FY2025; BNK FY2018~FY2022 G-IB·D-IT·그룹CIB·WM 부문장 겸직과 종료 시점; DGB FY2019~FY2021 CIB협의체 관련 겸직; 2026 반기 5개 항목). FY2019~2025 항목은 기존 A 조각(dart_out/ops15/조각/A_bs_g1~g3.csv·A_gov_g1~g2.csv — 읽기만, 다른 파동이 고치는 중일 수 있음)에서 행을 찾아 where 에 회사·FY·사람·rcept·page 로 적고, 기존 조각에 없는데 원문(사업보고서 md·연차보고서)에 있으면 A_ext 에 행을 더함(note 「기존 조각에 없어 더함」).
 검증 스크립트 verify15b_A_ext.py exit 0.`

const X2 = `작업 B 추가분·C 추가분·E. 네 소유: dart_out/ops15/조각/B_ext.csv·C_ext.csv·E.csv·확인_B_ext.csv·확인_C_ext.csv·확인_E.csv, dart_out/ops15/원문/B/·C/·E/ 의 새 문서 md(기존 이름과 겹치지 않게), scripts/dart/ops15b_X2.py(나눠도 됨: ops15b_B_ext.py·ops15b_C_ext.py·ops15b_E.py), scripts/dart/verify15b_X2.py 와 결과 txt, dart_out/ops15/문서목록15b_X2.csv, dart_out/raw/ops15b/X2/.
 B 추가: KB FY2014·FY2016·FY2017 사업보고서(목록 캐시 → document → md) Ⅷ 직원 현황 표·각주 + 키워드(겸직, 파견, 출향, 전출, 전적, 겸무) 행 — 기존 B 꼴(scripts/dart/ops15_bs_g1.py 의 B 부분 참고; 키워드 없는 해도 직원 수 행 keyword 「없음」). 그 해 KB 연차보고서(dart_out/ops15/문서목록15b_gov_old.csv 의 md)의 조직·인력 서술 키워드 행. NH FY2012 사업보고서(NH농협금융지주 00908021, 2012.12 — 없으면 기록): 직원 현황과 각주, 키워드, 「전적」「파견」 원문, 평균근속(10개월) 산정 기준 원문.
 확인_B_ext.csv — REQUEST15b 작업 B 「추가 연도·항목」 줄마다: KB FY2014·FY2016·FY2017·FY2023·FY2024, 신한·하나·BNK FY2022~FY2024, DGB·iM FY2019·FY2020·FY2023·FY2024, 우리 FY2022·FY2023(FY2023 에 「자회사 소속 겸직인원」 주석이 있는지 — 두 해 원문 대조, 2023 감축 인원의 은행 전출 언급), NH FY2012. FY2019~2025 는 기존 B 조각(B_bs_g1~g3·B_gov_g1~g2 — 읽기만)의 행을 where 로, 기존 조각에 없는데 원문에 있으면 B_ext 에 더함(note). 부서별 인원 항목(FY2025 하나·우리·NH·iM·JB, BNK·iM 부서 인원)은 작업 H 가 맡음 — 여기서는 하지 않음.
 C 추가: 우리금융지주(01350869) 2025.5 동양생명·ABL생명 편입 관련 공시 — OpenDART 목록(2024-08~2025-07; 보고서명에 「자회사」「편입」「주식」「취득」「동양」「ABL」 등) → document → 내부통제 개선계획(준법조직 확대 개편, 자회사 성과평가의 내부통제 평가) 서술 → C_ext 행(C 열; keyword = C 키워드(인력, 임직원, 조직, 겸직, 파견, 전적, 채용) 또는 「내부통제」「준법」「성과평가」 중 걸린 것, note 「(판단) 11.3 추가 항목 낱말」). 없으면 「문서에 없음」 + 찾은 목록 범위. 확인_C_ext.csv.
 E: 20140514005150(한국씨티은행·한국씨티금융지주 합병 주요사항보고서), 20150507001778(한국스탠다드차타드은행·한국SC금융지주 합병) → document → 합병 목적·배경 문단 전문(지주 존립 의의, 지주 유지 비용, 추가 보고 건수, 업무위탁 부가세, 감사 중복, 해외 본사·지역본부 관리 언급 — 문단 통째로, 문단마다 1행), 두 지주(한국씨티금융지주·한국SC금융지주 — corp_code 는 corpCode 캐시) FY2013 사업보고서 Ⅷ 임원 겸직 표(표 행마다 1행). 확인_E.csv: 사용자가 든 6가지 언급(존립 의의·유지 비용·추가 보고 건수·업무위탁 부가세·감사 중복·해외 본사·지역본부 관리) × 2건 마다 원문 있음/문서에 없음.
 검증 스크립트 verify15b_X2.py exit 0.`

const VB = (key, desc) => `작업 ${desc} 독립 검증 — 수집 에이전트 보고(맨 아래)는 믿지 말고 파일로 확인. 새 웹 수집 금지(OpenDART·웹 캐시에 이미 있는 것만 봄; 없으면 remaining). 네 소유: scripts/dart/verify15b_${key}.py(수집 에이전트가 만든 것이 있으면 고쳐서 씀)와 결과 dart_out/ops15/verify15b_${key}.txt, 그리고 이 작업의 조각·확인 CSV·원문 md 의 고침(고침은 생성기 scripts/dart/ops15b_${key}*.py 에 넣고 다시 돌려 같은 결과가 나오게; 시간이 모자라면 조각만 고치고 remaining 에).
 검사: (a) 모든 행의 source_text 와 원문 칸(*_text, concurrent_note, concurrent_or_dispatched 등)을 COMMON15b 대조 규칙으로 출처 텍스트에서 전수 대조(이어서 그대로, page 위치 안). (b) 열 이름·순서·utf-8-sig, 출처·page·doc_name·collected_at 빈칸 0. (c) 빠짐: 범위(회사×FY×문서)마다 행이 있거나 「문서에 없음」 행이 있는지; 출처 텍스트를 이 작업 키워드로 직접 grep 해 조각에 없는 자리 찾기(있으면 행 추가). (d) 「문서에 없음」 행은 더 넓은 검색어로 반박. (e) 숫자 칸(금액 환산·인원·개최 횟수) 표본 30개 이상 원문과 맞대기. (f) 분류 칸 기준이 기계적인지, 기능 분류·이유 추정 낱말이 note 에 없는지. (g) 확인_ CSV: REQUEST15b 의 해당 항목 줄이 모두 있는지, result 가 원문과 맞는지, note 가 사실만인지. (h) 비밀값 꼴 없음, PDF·원본이 git 추적 경로에 없음(dart_out/raw·dart_out/text·dart_out/ops15/조직도 는 무시 폴더). exit 0 까지.
 수집 보고: `

const HEAD4 = `You are a sub-agent in /home/user/lastprice (Korean financial-holding-company disclosure research). FIRST read dart_out/ops15/REQUEST15.md (the user's request, verbatim) and dart_out/ops15/COMMON15.md (binding rules, environment facts, inputs, fragment formats, page rule). Key rules: source_text = exact copy from the source text (no edits), interpretation only in note, 「문서에 없음」 when absent (+ where searched in note), every row has source (rcept_no or URL, doc_name, page) and collected_at, NO function classification or reason guessing, same-name people distinguished by birth year-month, never print/write DART_API_KEY or secrets, do NOT git commit, write only your own files (other agents are editing other fragments at the same time). Keep tool outputs small (grep -n / sed ranges; big intermediates to files) — agents have died from oversized outputs and from usage limits, so work efficiently. Get time via \`date\` (write KST). Answer in Korean via structured output.
The previous critic (dart_out/ops15/critic15.json) and verify reports (dart_out/ops15/wave3_results.json) list the problems; read the parts relevant to you.

새 원문 대조 규칙(이번 파동부터 — 모든 조각에 적용): source_text(와 「문서에 없음」이 아닌 reason_text)는 출처 텍스트의 한 곳에서 이어진 글이어야 함. 대조는 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 텍스트」 안에 이어서 그대로 있는지로 봄. 다만 OpenDART XML md 출처에서는 md 표지인 「|」와 「<br>」도 양쪽에서 지우고 봄(PDF·6차 섹션·경영공시 출처에서는 「|」를 지우지 않음). 그래서: 원문에 없는 「 | 」·「 … 」·생략 표시를 넣지 않음, 떨어진 두 곳을 잇지 않음 — 둘 다 필요하면 그 사이 글까지 이어서 옮기거나(2,000자 이하일 때) 행을 나누고 다른 곳은 note 에 위치만. PDF 줄바꿈은 줄바꿈 그대로(또는 공백) 둠. 보이지 않는 제어문자(U+0000~U+001F 중 줄바꿈·탭 말고)만은 지워도 되고 그 행 note 에 「제어문자 지움」.

YOUR TASK:
`

const FIX_BS = `사업보고서 조각 고침(네 소유: scripts/dart/ops15_bs_g1.py·ops15_bs_g2.py·ops15_bs_g3.py, dart_out/ops15/조각/A|B|D_bs_g1~g3.csv, bs_g2_work.json·bs_g3_work.json, scripts/dart/verify15_bs_g1~g3.py 와 그 결과 txt, dart_out/ops15/원문/ 아래 이 조각들의 md). 고침은 생성기에 넣고 다시 돌려 조각을 만듦.
 (1) 작업 A fulltime: 사업보고서 행 중 fulltime 빈칸 165행(신한 89·우리 40·NH 35·BNK 1 — 겸직 표에는 있으나 임원 현황 표에 같은 이름이 없는 사람)은 그 행이 나온 겸직 표의 상근 여부 칸 원문 값(지금 note 에만 있음)을 fulltime 에 그대로 넣음. 겸직 표에도 임원 현황에도 없으면 fulltime 「문서에 없음」, note 에 찾은 범위. registered 도 같은 방식(원문 값 그대로, 없으면 「문서에 없음」).
 (2) 작업 A 줄 이음 100행(JB 37·한국투자 63 — 표 안에서 떨어진 이름 줄과 그 행을 생략 없이 이어 붙인 것): 위 새 대조 규칙에 맞게 — 이름 줄부터 그 행까지 사이 줄을 모두 포함해 이어서 옮기거나, 그 행만 옮기고 이름 줄 위치는 note 에. 한국투자 FY2019·2020 19행처럼 이름 머리(「(5) 정영록」 등)가 page 가 가리키는 [표 m] 밖에 있으면 page 를 실제 범위(예 「XML [절 n] 「…」 [표 m-1]~[표 m]」)로.
 (3) JB FY2023 정정판 2건에 같은 새 사외이사 행이 각각 들어간 중복(이명상·이희승 각 2행): 1행만 두고(먼저 접수된 정정판), 다른 정정판에도 같은 글이 있음을 note 에 rcept_no 와 함께.
 (4) concurrent_company/concurrent_title 나누기 오류: 전 행 훑어 고침. 예 BNK 허진호 「종합법률사무소 그레이스 변호사(現)」→ company 「종합법률사무소 그레이스」 title 「변호사」, NH 이종백 「서울고등검찰청장 김앤장법률사무소」 류. 두 칸은 각각 source_text 의 이어진 부분 글이어야 하고, 어디서 나눌지 확신이 없으면 company 에 통째로 넣고 title 「(나누지 않음)」, note (판단).
 (5) 작업 B keyword 칸은 요청 키워드 6개(겸직, 파견, 출향, 전출, 전적, 겸무) 또는 「없음」만. 「겸임」 4행은 keyword 「겸임(요청 키워드 밖)」으로 바꾸고 note (판단), 「(정정판 합계 행)」 2행은 그 행의 실제 keyword(「없음」 등)로 바꾸고 정정판이라는 것은 note 로. Ⅷ 임원 현황 표에서 나온 B 39행은 note 에 「(위치) 임원 현황 표 — 작업 A 와 겹침」.
 (6) 작업 D: (a) 같은 보고서 같은 (상대방·유형)인데 글이 다른 43곳이 1행으로 묶여 있음 → 원문이 다른 글마다 1행으로 풀고 각자 page. (b) 검색어를 「위탁」까지 넓혀 Ⅹ·Ⅺ 에서 지주와 계열사(자회사·손자회사·그룹사) 사이 위탁 언급(고객·개인(신용)정보 처리 위탁 포함 — 우리 FY2019~2025, KB FY2021~2025, 신한 FY2024·2025 Ⅺ 등)을 넣고 contract_type 은 원문 표현, note 「(판단) 검색어 「위탁」으로 넓혀 넣음」. (c) 메리츠 Ⅹ 지주–자회사 거래 표(부동산임대차·브랜드사용료·수수료수익)는 행으로 넣지 않고 지금처럼 note 에만 — 위치를 정확히.
 (7) 검증 스크립트 verify15_bs_g1~g3.py 를 위 새 대조 규칙(이어서 그대로, XML md 만 「|」「<br>」 무시)으로 고치고 셋 다 exit 0 이 될 때까지. 결과 txt 다시.
 rows 에는 조각별 행 수(A/B/D × g1~g3)와 그중 「문서에 없음」 행 수.`


const FIX_GC = `연차보고서 조각과 작업 C 조각 고침(네 소유: scripts/dart/ops15_gov_g1_extract.py 와 g1 의 다른 gov 스크립트, scripts/dart/gov15_g2_*.py, dart_out/ops15/조각/A_gov_g1·B_gov_g1·A_gov_g2·B_gov_g2.csv, dart_out/ops15/gov15_g1_work/, dart_out/ops15/조각/C.csv, dart_out/ops15/원문/C/ 와 연차보고서 행의 원문 md, scripts/dart/verify15_gov_g1.py·verify15_gov_g2.py·verify15_C.py 와 결과 txt, 새 폴더 scripts/dart/ops15_C/). 고침은 생성기에 넣고 다시 돌림.
 연차보고서(A_gov·B_gov):
 (1) PDF 줄바꿈 자리에 원문에 없는 「 | 」를 넣은 38행(A 32·B 6, 신한·우리·하나 — 예 A 신한 FY2021 최경록 p.77, 우리 FY2022 신요환 p.60)과 「 … 」로 두 곳을 이은 5행(예 하나 FY2021 황효상 p.300 표 행+각주 주5)을 새 대조 규칙대로 고침(줄바꿈 그대로 이어 옮기거나 행 나눔. 각주가 겸직 사유 원문이면 reason_text 에 각주 글 그대로, 위치는 note).
 (2) reason_text 「문서에 없음」 45행(우리 FY2021~2025 17·신한 FY2019~2022 18·KB FY2019 5·하나 FY2019~2023 5)에 note 로 찾은 범위(문서·쪽 범위·검색어) 덧붙임. 덧붙이기 전에 그 범위에서 「사유」「겸직」「겸임」「선임」으로 한 번 더 찾아 사유 원문이 있으면 넣음.
 (3) 제어문자를 지운 35행은 note 에 「제어문자 지움」이 있는지 확인. JB FY2019 판독 행(글자층 깨짐 — 그림으로 읽은 것)은 모두 note 앞머리 「(판독)」. 한국투자 FY2023 p.51·p.53·6차 FY2024·2025 의 오태균 「(겸) 한국투자증권 기타 비상무이사」 행 note 에 쪽.
 (4) verify15_gov_g1·g2 를 새 대조 규칙(PDF 출처는 공백·줄바꿈만 무시, 「|」 무시 안 함)으로 고치고 exit 0 까지.
 작업 C:
 (5) 생성기가 저장소 밖(/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/C/scripts/build.py 등 + manifest.json·kit)에 있음 → scripts/dart/ops15_C/ 로 옮기고(입력 경로는 저장소 상대 경로, 저장소 밖 파일에 기대는 곳은 그 파일을 어떻게 다시 만드는지 README 한 쪽), 다시 돌려 C.csv 가 같은 행을 내는지 확인. 원본 PDF·zip 같은 큰 파일·비밀값은 옮기지 않음.
 (6) BNK 20101229000364·JB 20130320000306 [첨부정정](OpenDART 014 — 원문 못 받음)은 지금 「문서에 없음」 → source_text 「수집 실패」, note 「OpenDART document.xml 014(파일 미제공) — 원문을 볼 수 없어 내용 확인 못함; '문서에 없음' 아님」. 다른 014 행도 같게.
 (7) NH농협금융지주 설립(2012-03-02, 농협중앙회 신용사업 분리)의 신고서: OpenDART list.json(scripts/dart/client.py DartClient — 키는 환경변수, 로그에서 가려짐)으로 NH농협금융지주 00908021 과 농협은행(corp_code 는 dart_out/raw/corpCode 또는 targets 로 찾음)의 2011-07~2012-12 발행공시(C)·주요사항(B)·기타(I) 목록을 보고 지주 설립·전환 신고서(증권신고서·투자설명서·주식이전·분할)가 있는지 확인. 있으면 다른 사건과 같은 방식으로 키워드 문단을 C 에 넣고, 없으면 C 에 「문서에 없음」 1행(note 에 찾은 목록 범위·검색한 보고서명) — corp_label NH농협금융지주.
 (8) wave1 c 보고 글의 틀린 곳 4가지(wave3_results.json 의 C remaining 참고)를 바로잡은 수치를 rows/fixed 에 적어 메인이 보고서에 쓰게.
 (9) verify15_C.py 를 새 대조 규칙으로, exit 0 까지(저장소 밖 파일 의존은 README 와 같은 내용으로 스크립트 머리에).
 rows 에는 조각별 행 수와 「문서에 없음」·「수집 실패」 행 수.`


const MG = [
  { g: 'g1', corps: 'KB금융지주·신한금융지주·하나금융지주·우리금융지주·NH농협금융지주', hint: 'scripts/dart/web13_g_kb_shinhan.py·web13_g_hana_woori.py·web13_g_im_nh.py' },
  { g: 'g2', corps: '메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주', hint: 'scripts/dart/web13_g_meritz_kis.py·web13_g_im_nh.py (BNK·JB 는 13차에 받지 않음 — 누리집에서 경영공시 게시판을 찾음)' },
]

const VMGMT = (m) => `경영공시 조각 그룹 ${m.g}(${m.corps}) 독립 검증 — 수집 에이전트 보고는 아래에 있지만 믿지 말고 파일로 확인. 새 웹 수집 금지(목록 쪽 확인 포함 — 받은 파일만 봄). 네 소유: scripts/dart/verify15_mgmt_${m.g}.py 를 고치는 것과 결과 txt, 그리고 조각 B_mgmt_${m.g}.csv·D_mgmt_${m.g}.csv·dart_out/ops15/원문/B|D/*__경영공시.md 의 고침(고침은 생성기 scripts/dart/ops15_mgmt_${m.g}.py 의 extract 에 넣고 다시 돌림).
 (a) 모든 행 source_text 가 경영공시 md(dart_out/text/ops15/경영공시__…md)의 page 쪽에 새 대조 규칙대로 이어서 그대로 있는지 전수. (b) 열·utf-8-sig·출처/page/doc_name/collected_at 빈칸 0, sha256 이 목록과 파일이 같은지. (c) 키워드 빠짐: md 마다 6개 키워드를 직접 grep 해서 조각에 없는 자리 찾기(있으면 행 추가). D 도 「위탁」「용역」「자문」「전산」「공동」 grep 으로 빠짐 확인(지주–계열사 사이인지는 원문으로만 판단, 애매하면 넣고 note (판단)). (d) 「문서에 없음」 행은 더 넓은 검색어로 반박 시도. (e) 목록: 회사×FY 35칸이 모두 있고 status 가 사실과 맞는지(파일 있음/없음), robots·이용약관 기록이 있는지. (f) 비밀값 꼴 없음, PDF 를 커밋 경로(git 추적 폴더)에 두지 않았는지.
 수집 보고: `


const PARTIAL = `\n 덧붙임(2026-11-03): 이 일의 이전 시도가 사용 한도로 중간에 멈췄을 수 있음 — 먼저 git status·git diff 로 네 소유 파일에 남은 이전 시도의 변경을 보고 이어서 함. 지금 다른 에이전트들(15차 확장 작업 E~J·A/B/C 추가분)이 dart_out/ops15/조각/ 에 새 조각(F_*, G_*, H_*, I, J_*, A_ext, B_ext, C_ext, E, 확인_*)을 쓰고 있고 기존 A~D 조각은 읽기만 함 — 그 파일들은 건드리지 말 것.`
const VMG2 = (m) => VMGMT(m) + '(수집 보고는 dart_out/ops15/wave4_results.json 의 res 배열에서 key 가 mgmt_' + m.g + ' 인 항목의 collect — 파일을 읽을 것)' + PARTIAL

let halted = false
const run = async (label, phase, prompt) => {
  if (halted) return null
  const r = await agent(prompt, { label, phase, schema: RSCHEMA, agentType: 'general-purpose' })
  if (!r) { halted = true; log('멈춤: ' + label + ' 실패(사용 한도 등) — 남은 일은 시작하지 않음. resumeFromRunId 로 이어 돌릴 것') }
  return r
}
let resolveGov
const govPromise = new Promise(res => { resolveGov = res })
const chainT = (key, desc, prompt, needsGov) => ({ key, needsGov, fn: async () => {
  const c = await run('c:' + key, 'Collect', HEAD + prompt)
  if (!c) return { key, collect: null }
  const v = await run('v:' + key, 'Verify', HEAD + VB(key, desc) + JSON.stringify(c).slice(0, 20000))
  return { key, collect: c, verify: v }
} })
const tasks = [
  { key: 'gov_old', fn: async () => { const g = await run('c:gov_old', 'Collect', HEAD + GOV_OLD); resolveGov(g); return { key: 'gov_old', r: g } } },
  { key: 'fix_bs', fn: async () => ({ key: 'fix_bs', r: await run('fix:bs', 'Collect', HEAD4 + FIX_BS + PARTIAL) }) },
  { key: 'fix_gc', fn: async () => ({ key: 'fix_gc', r: await run('fix:gov+C', 'Collect', HEAD4 + FIX_GC + PARTIAL) }) },
  ...MG.map(m => ({ key: 'vmgmt_' + m.g, fn: async () => ({ key: 'vmgmt_' + m.g, r: await run('vmgmt:' + m.g, 'Verify', HEAD4 + VMG2(m)) }) })),
  chainT('F_g1', 'F·F-2·F-3 그룹 g1(' + G1 + ')', F('g1', G1), false),
  chainT('F_g2', 'F·F-2·F-3 그룹 g2(' + G2C + ')', F('g2', G2C), false),
  chainT('G_g2', 'G 그룹 g2(' + G2C + ')', G('g2', G2C), false),
  chainT('G_g1', 'G 그룹 g1(' + G1 + ')', G('g1', G1), true),
  chainT('I', 'I(10개사)', I, true),
  chainT('X2', 'B 추가·C 추가·E', X2, true),
  chainT('A_ext', 'A 추가분', X1, true),
  chainT('H_g1', 'H 그룹 g1(' + G1 + ')', H('g1', G1), true),
  chainT('H_g2', 'H 그룹 g2(' + G2C + ')', H('g2', G2C), true),
  chainT('J_g1', 'J 그룹 g1(신한·하나)', J('g1'), false),
  chainT('J_g2', 'J 그룹 g2(우리·DGB(iM)·KB)', J('g2'), false),
  chainT('G2', 'G-2(자회사 쪽)', G2T, false),
]
const out = []
let idx = 0
const worker = async () => {
  while (!halted && idx < tasks.length) {
    const t = tasks[idx++]
    if (t.needsGov) { await govPromise }
    if (halted) { out.push({ key: t.key, skipped: true }); break }
    out.push(await t.fn())
  }
}
phase('Collect')
await Promise.all([worker(), worker()])
for (let k = idx; k < tasks.length; k++) out.push({ key: tasks[k].key, skipped: true })
if (halted) resolveGov(null)
return { halted, out }
