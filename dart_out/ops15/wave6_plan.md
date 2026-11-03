# 15차 wave6 계획(메인 메모, 2026-11-03 11:05 KST)

- 사용 한도(5시간) — 2026-11-03 03:50 UTC 에 풀림. wave4(고침·검증·합본) 6개, wave5(확장 작업 전부)가 한도로 실패.
- wave6 = 한 워크플로에 우선순위 순서의 작업 줄(동시 2개, 한 에이전트라도 null 이면 멈춤 → 다음 한도가 풀리면 resumeFromRunId 로 이어감):
  1. gov_old(옛 연차보고서·FY2024~25 PDF 다시 받기)
  2. fix_bs, fix_gc(wave4 와 같은 지시)
  3. vmgmt_g1, vmgmt_g2(경영공시 조각 독립 검증 — 수집 보고는 dart_out/ops15/wave4_results.json)
  4. F_g1, F_g2, G_g2, G_g1, I, X2, A_ext, H_g1, H_g2, J_g1, J_g2, G2(각각 수집 → 독립 검증)
- 그 뒤 wave7 = 전체 합본(13 CSV + 원문 md zip + 조직도 그림 + 보고) → 비평.

- 2026-11-03 03:54 UTC 시작: task wpn09m9dt, run wf_24f59e4e-764, 스크립트 사본 dart_out/ops15/wf/ops15-wave6.js(원본 scratchpad/ops15-wave6.js). 멈추면 Workflow({scriptPath, resumeFromRunId: "wf_24f59e4e-764"}).
- 2026-11-03 07:09 UTC 사용자 요청(「일단 멈추자」)으로 멈춤. 끝난 것(결과 dart_out/ops15/wave6_results.json): gov_old, fix_bs, fix_gc, vmgmt_g1·g2, F_g1·F_g2(수집+검증), G_g1·G_g2(수집+검증), I(수집+검증). 하던 것: X2(목록·문서 받기까지 — B_ext·C_ext·E 행은 아직). 남은 것: X2, A_ext, H_g1, H_g2, J_g1, J_g2, G2, 그 뒤 wave7 합본·비평. 이어 돌리면 끝난 에이전트는 캐시로 넘어감(resumeFromRunId wf_24f59e4e-764).
