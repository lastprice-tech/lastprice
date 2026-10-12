"""shorts_growth_kit — 역사공학 쇼츠 성장 시스템.

모듈 지도 (PLAN.html §8 참조):
  sources/       외부 신호 수집 (자동완성 · Wikipedia pageviews · StackExchange · YouTube Data API)
  item_rubric    아이템 채점 Q/F/V/M/G/S/H + AND 게이트
  scout          주간 발굴 퍼널 → 게이트 0 리포트
  hooks          훅 템플릿 15종 + 루브릭 R01-R10 자동 채점
  script_lint    12슬롯 v2 대본 린터
  db             SQLite episodes/snapshots 스키마
  analytics      리텐션 100pt → 슬롯 귀속, 커브 분류, 판정 프로토콜
  config         모든 임계값(출처 주석 포함) + 세이프존 상수

표준 라이브러리만 사용한다. 의존성 0.
"""

__version__ = "0.1.0"
