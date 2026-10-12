"""모든 임계값과 상수. 각 값에 출처 등급을 주석으로 남긴다.

출처 등급:
  [강] 공식 발표·RCT·학술 — 신뢰하고 하드코딩 가능
  [중] 업계 실측·교차 확인 — 초기값으로 사용
  [약] 벤더 집계·방향성만 — 초기값일 뿐, 자기 데이터로 최우선 재보정

원칙: 외부 수치는 전부 '초기값'이다. 에피소드 20편 누적 후
자기 채널 분위수(median ± MAD)로 교체한다 (analytics.recalibrate 참조).
"""

# ---------------------------------------------------------------- 대본
WORD_BUDGET = (145, 170)          # [중] 135-155 WPM 밴드. 구 120-190은 상단 과속
TARGET_SECONDS = (62, 68)         # [중] 50-60초대가 완주율 최고 버킷과 정합
WPM_BAND = (135, 155)             # [중]
HOOK_FIRST_SENT_MAX_WORDS = 8     # [중] 2.5초 내 격차 개방 (병합: 8단어 개방 + 12단어 페이오프)
HOOK_PAYOFF_MAX_WORDS = 12        # [중]
HOOK_FIRST_SENT_MAX_AUDIO_S = 2.6 # [중] TTS 렌더 후 실측으로 검증
PUNCH_SENT_MAX_WORDS = 6          # 작법 원리 (Provost) — 슬롯 끝 펀치 문장
STAKES_MAX_WORDS = 12
YOU_COUNT_RANGE = (2, 6)          # 2인칭 투입 지점 2곳 고정 (OR_ELSE, EFFECT)
PRECISE_NUMBER_RANGE = (2, 4)     # [강] precision effect — 반올림 금지
TRAILING_SILENCE_MAX_S = 0.3      # 루프 보호: 데드에어 금지

# 12슬롯 v2. (id, 이전 이름, 기능 요약)
SLOTS_V2 = [
    ("HERE_IS",      "HERE IS",      "훅: <=12단어 페이오프, SOLUTION 키워드 금지"),
    ("NOT_BECAUSE",  "NOT BECAUSE",  "오해 부정 = 열린 루프 #1"),
    ("OR_ELSE",      "OR ELSE",      "위험 2인칭 — you 1/2"),
    ("TRAP",         "EASY PART",    "쉬운 부분을 함정으로. 끝문장 <=6단어 + X 동기화"),
    ("PROBLEM_1",    "PROBLEM 1",    "재훅 #1: 의문문/반전 + 새 명사"),
    ("WHAT_IF_NO",   "WHAT IF->NO",  "런타임 45-55%, 에피소드 최대 시각 이벤트"),
    ("PROBLEM_2",    "PROBLEM 2",    "재훅 #2: 스테이크 증가"),
    ("STAKES",       "SUMMARY",      "요약 금지. 3항 압축 <=12단어"),
    ("PIVOT",        "PIVOT",        "재훅 #3"),
    ("SOLUTION",     "SOLUTION",     "최저 속도, 정밀 숫자+치수선 1:1, you 금지"),
    ("EFFECT",       "EFFECT",       "논쟁 씨앗 1개 + you 2/2"),
    ("CLOSING_LOOP", "CLOSING",      "시그니처 즉시 컷 + 마지막 프레임 = 첫 프레임"),
]
REHOOK_SLOTS = ("PROBLEM_1", "PROBLEM_2", "PIVOT")
SIGNATURE_PREFIX = "that is the"

# ---------------------------------------------------------------- 훅 루브릭
HOOK_PASS = 70          # 100점 만점: 70+ 통과 / 50-69 재생성 / <50 반려
HOOK_REGEN = 50

# ---------------------------------------------------------------- 아이템 루브릭 (Q/F/V/M/G/S/H)
ITEM_WEIGHTS = {"Q": 0.25, "F": 0.15, "V": 0.15, "M": 0.15, "G": 0.15, "S": 0.10, "H": 0.05}
PAGEVIEWS_HARD_GATE = 5_000       # [중] 월간. 미만이면 총점 무관 탈락 (콜드 피드 1초 인식 불가)
PAGEVIEWS_TIER_HIGH = 50_000      # [중] 직전 3개월 평균
OUTLIER_MODERATE = 3.0            # [강] vidIQ/1of10 공통 관행: 3x=중간 5x=강 10x=예외적
OUTLIER_STRONG = 5.0
OUTLIER_EXCEPTIONAL = 10.0
GAP_VIRAL_VIEWS = 1_000_000       # 24개월 내 1M+ 쇼츠 존재 = 공급 포화
GAP_MONTHS = 24
WEEKLY_CANDIDATE_TARGET = 100     # [중] 넓은 깔때기: 주 100후보 -> 상위 10 -> 5편
WILDCARD_QUOTA = 0.2              # 주 5편 중 1편은 인접 도메인
SERIES_REUSE_MIN = 50             # 새 소재군은 "50편 뽑을 수 있는가" 통과 시에만

# ---------------------------------------------------------------- 지표 (초기값 — 20편 후 자기 분위수로 교체)
STAY_RATE_GOOD = 0.70             # [약] engagedViews/views. 루프 성공작 왜곡 주의
STAY_RATE_ALERT = 0.60
APV_GOOD = 0.70                   # [약] 평균 시청 비율
APV_ALERT = 0.50
FIRST3S_RETENTION_TARGET = 0.75   # [약]
MIDPOINT_RETENTION_TARGET = 0.60  # [약]
CLIFF_DROP_3S = 0.30              # 3초 내 -30%p 초과 = cliff형 (훅 책임)
MID_DROP_FACTOR = 2.0             # 슬롯 낙차 > 전체 평균 x2 = mid_drop형
MIN_ENGAGED_FOR_VERDICT = 500     # 직접 계산 (2-비율 검정 하한): 판정은 이 이후에만
MIN_EPISODES_PER_HOOK_TYPE = 8    # 훅 '유형' 단위 결론 최소 표본
RECALIBRATE_AFTER_EPISODES = 20
SNAPSHOT_HORIZONS = ("48h", "7d", "28d")  # 48h/7d 주력, 28d 보관용. 비교는 같은 나이끼리

# ---------------------------------------------------------------- 렌더/오버레이
INTRA_SLOT_EVENT_INTERVAL_S = (2.0, 2.5)  # [중] 5초 클립당 오버레이 이벤트 >=2
OVERLAY_DRAW_DURATION_S = (0.7, 1.2)      # 완성 상태 즉시 표시 금지 — 드로잉만
STILL_FREEZE_MAX_S = 2.5                  # 정지(모션·오버레이 無) 초과 = QC 실패
OVERLAY_COVERAGE_MIN = 0.70               # 도면 요소 화면 존재 시간 비율
GRAIN_OPACITY = (0.08, 0.15)              # 에피소드 전체 동일 시드

# 3플랫폼 세이프존 교집합 (1080x1920 기준, 서드파티 실측 — 분기별 재측정)
# YT Shorts: top 130 / bottom 484 / right 140, TikTok: bottom 320 / right 120,
# Reels: top 220 / bottom 420. 교집합 = 중앙 880x1216 박스.
SAFE_ZONE_1080x1920 = {"top": 220, "bottom": 484, "left": 60, "right": 140}

def safe_box(w: int = 1080, h: int = 1920) -> dict:
    """해상도를 스케일해 오버레이 허용 박스를 돌려준다 (skia 렌더러에서 import)."""
    sx, sy = w / 1080.0, h / 1920.0
    z = SAFE_ZONE_1080x1920
    return {
        "x0": round(z["left"] * sx), "y0": round(z["top"] * sy),
        "x1": round(w - z["right"] * sx), "y1": round(h - z["bottom"] * sy),
    }

# ---------------------------------------------------------------- 패키징
TITLE_MAX_CHARS = 40              # 완결형 질문이 40자 안에 (셸프 말줄임)
HASHTAG_COUNT = 3                 # 그 이상은 non-goal
MLA_LOCALIZE_TRIGGER = 0.15       # 비주언어 워치타임 >15% 4주 지속 -> 2단계 재렌더
BACKLOG_BUFFER_MIN = 5            # 버퍼 미달이면 실험보다 본편 생산 우선
