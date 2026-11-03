# 15차 wave6 계획(메인 메모, 2026-11-03 11:05 KST)

- 사용 한도(5시간) — 2026-11-03 03:50 UTC 에 풀림. wave4(고침·검증·합본) 6개, wave5(확장 작업 전부)가 한도로 실패.
- wave6 = 한 워크플로에 우선순위 순서의 작업 줄(동시 2개, 한 에이전트라도 null 이면 멈춤 → 다음 한도가 풀리면 resumeFromRunId 로 이어감):
  1. gov_old(옛 연차보고서·FY2024~25 PDF 다시 받기)
  2. fix_bs, fix_gc(wave4 와 같은 지시)
  3. vmgmt_g1, vmgmt_g2(경영공시 조각 독립 검증 — 수집 보고는 dart_out/ops15/wave4_results.json)
  4. F_g1, F_g2, G_g2, G_g1, I, X2, A_ext, H_g1, H_g2, J_g1, J_g2, G2(각각 수집 → 독립 검증)
- 그 뒤 wave7 = 전체 합본(13 CSV + 원문 md zip + 조직도 그림 + 보고) → 비평.
