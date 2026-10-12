"""훅 엔진: 템플릿 15종 + 자동 채점 루브릭 R01-R10.

사용:
    from growth.hooks import score_hook, TEMPLATES
    r = score_hook("Half of the Colosseum is missing.",
                   solution_text="Rome pulled its iron pins. The missing half became palaces.")
    r["total"], r["verdict"], r["breakdown"]

설계 노트:
- R01(격차 개방)·R05(확신 조작)는 휴리스틱이다. 점수는 대본 생성 루프의 1차 필터이고,
  최종 판단은 감독(Claude/사람)이 한다. 휴리스틱이 과하게 깎으면 breakdown을 보고 override.
- 에피소드당 훅 후보 3개(질문형 1 + 단언형 1 + 자유 1) 생성 -> 최고점 채택,
  나머지도 {template_id, score, 실측 3초 유지율}로 DB에 축적해 분기별 가중치 재보정.
- 아이데이션 순서: 주제 -> 훅 5개 -> 최강 훅 -> 에피소드 각도 역산 (훅이 우선한다).
"""
from __future__ import annotations

import re

from . import config, lexicons as lx

# (id, 심리 메커니즘, 템플릿, 예시)
TEMPLATES = [
    ("T01", "정보격차·결손+부정성", "{fraction} of {object} is missing/gone.",
     "Half of the Colosseum is missing."),
    ("T02", "기대위반·베이지안 서프라이즈", "{object} shouldn't {exist/stand/work}.",
     "This bridge shouldn't be standing."),
    ("T03", "금지된 지식·사회적 morbid", "{authority} banned {this object/method}.",
     "Rome banned this machine. Twice."),
    ("T04", "부정성+비반올림 수치", "{object} killed {exact odd N} people before anyone asked why.",
     "This staircase killed 47 people before anyone asked why."),
    ("T05", "스케일 충돌", "This {tiny measure} {holds/stops/carries} {huge measure}.",
     "This 2-gram pin holds a 40,000-ton bridge."),
    ("T06", "날짜 시한폭탄·예기불안", "In {year}, {object} had {N days} left.",
     "In 1907, this bridge had 86 days left."),
    ("T07", "오답 선제 -> 확신 50% 강하", "Everyone thinks {common answer}. {evidence} says otherwise.",
     "Everyone thinks earthquakes did this. The stone says otherwise."),
    ("T08", "자기관련성 you 훅", "You've {walked past/used} {this mistake} {N} times.",
     "You've walked past this 500-year-old mistake a thousand times."),
    ("T09", "질문 직접형·정보격차", "Why does {object} {have/lack} {visible anomaly}?",
     "Why does half of this building not exist?"),
    ("T10", "지각적 호기심·탐정형", "Look at {specific visual detail}. It's a {scar/warning/lie}.",
     "Look at the diagonal line on this wall. It's a scar."),
    ("T11", "반사실·스테이크", "If {this part} were {tiny change}, {city} would have {catastrophe}.",
     "If this bolt were 3mm shorter, London would have lost a bridge."),
    ("T12", "생존자 이상치", "{N} {objects} like this were built. This is the only one left.",
     "500 bridges like this were built. This is the only one left."),
    ("T13", "현재진행 위험+역설", "{object} is {failing} right now — {rate} — and they let it.",
     "This tower is sinking 1mm a year. On purpose."),
    ("T14", "의도성 반전", "These {flaws} were made on purpose.",
     "These holes were drilled on purpose."),
    ("T15", "대명사 제로 대담 단언 (최고 돌파율형)", "{object} has been {lying/hiding} for {N} years.",
     "This dome has been cheating gravity for 1,900 years."),
]

_BANNED_OPENERS = re.compile(
    r"^\s*(hi|hey|hello|welcome|in this video|today (we|i)|i |we |my )", re.I)
_CONVENTION_MARKERS = re.compile(
    r"\b(everyone thinks|people (say|call|think|believe)|you('d| would) think|"
    r"the (story|myth|textbook) (says|goes)|supposedly)\b", re.I)
_COUNTER_MARKERS = re.compile(
    r"\b(on purpose|shouldn'?t|isn'?t|wasn'?t|but |otherwise|wrong|never|not because)\b", re.I)
_ANOMALY_MARKERS = re.compile(
    r"\b(missing|gone|only one|shouldn'?t|banned|killed|collapsed|sinking|holes?|"
    r"scar|crack(ed)?|wrong|hiding|cheating|lying|failed|impossible|on purpose|"
    r"never (built|repaired|finished)|left|disappeared|forbidden)\b", re.I)


def _first_sentence(text: str) -> str:
    s = lx.sentences(text)
    return s[0] if s else text


def score_hook(hook_text: str,
               solution_text: str | None = None,
               title: str | None = None,
               first_frame: dict | None = None) -> dict:
    """루브릭 R01-R10으로 훅을 채점한다.

    first_frame (선택): 렌더 계약 검사용.
      {"hook_noun_visible": bool, "overlay_draw_starts_s": float, "overlay_words": int,
       "overlay_echoes_narration": bool}
    반환: {"total", "verdict"(pass|regen|reject), "breakdown", "auto_reject", "notes"}
    """
    b: dict[str, int] = {}
    notes: list[str] = []
    auto_reject: list[str] = []
    hook = hook_text.strip()
    first = _first_sentence(hook)
    n_first = lx.word_count(first)
    n_to_payoff = lx.word_count(" ".join(lx.sentences(hook)[:2]))

    # R-금지: 인사말 / 'In this video' / 첫 문장 1인칭
    if _BANNED_OPENERS.match(hook):
        auto_reject.append("banned_opener: 인사말/자기소개/1인칭 시작")

    # R01 격차 개방 (+20): 이상·결손·위반 신호가 있는가
    anomaly = bool(_ANOMALY_MARKERS.search(hook)) or hook.rstrip().endswith("?")
    if anomaly:
        b["R01_gap"] = 20
    else:
        b["R01_gap"] = 0
        auto_reject.append("R01: 격차 없음 — 순수 사실 진술 (heuristic, 감독 override 가능)")

    # R02 개방 속도 (+15)
    if n_first <= config.HOOK_FIRST_SENT_MAX_WORDS:
        b["R02_speed"] = 15
    elif n_first <= config.HOOK_PAYOFF_MAX_WORDS:
        b["R02_speed"] = 8
    else:
        b["R02_speed"] = 0
        notes.append(f"R02: 첫 문장 {n_first}단어 — 8단어 내 격차 개방 권장")

    # R03 구체성 밴드 (+10): 1-2개 만점, 0개 0점, 3개+ 감점 (과잉 구체성은 격차를 닫는다)
    spec = lx.specificity_tokens(hook)
    b["R03_specificity"] = 10 if 1 <= spec <= 2 else (0 if spec == 0 else -5)
    if spec >= 3:
        notes.append(f"R03: 구체 토큰 {spec}개 — 답을 훅에서 말해버릴 위험")

    # R04 부정 렉시콘 (+10 / 3개+ -5, 긍정 -5)
    neg = lx.negation_hits(hook)
    pos = lx.positive_hits(hook)
    r04 = min(len(neg), 2) * 5 if len(neg) < 3 else -5
    if pos:
        r04 -= 5
        notes.append(f"R04: 긍정 렉시콘 {pos} — 경이감은 SOLUTION/EFFECT로")
    b["R04_negativity"] = r04

    # R05 확신 조작 (+10): 통념 명시+부정 또는 상식 역행 단언
    b["R05_certainty"] = 10 if (_CONVENTION_MARKERS.search(hook) or _COUNTER_MARKERS.search(hook)) else 0

    # R06 자기관련성 (+10): you/친숙 오브젝트. 첫 문장 1인칭은 위에서 반려됨
    lower = hook.lower()
    b["R06_self"] = 10 if (" you" in f" {lower}" or "your " in lower
                           or lx.has_domain_anchor(hook)) else 0

    # R07 도메인 앵커 (+5): 12단어 안에 역사·공학 토큰 (클러스터 오배포 방지)
    b["R07_anchor"] = 5 if lx.has_domain_anchor(hook, max_words=12) else 0
    if not b["R07_anchor"]:
        notes.append("R07: 무도메인 훅 — 엉뚱한 시청자군 배포 위험")

    # R08 페이오프 계약 (+10): 훅 핵심 명사가 SOLUTION 슬롯에 재등장 — 불일치 반려
    if solution_text is not None:
        hook_kw = set(lx.content_words(hook))
        sol_kw = set(lx.content_words(solution_text))
        shared = hook_kw & sol_kw
        if shared:
            b["R08_contract"] = 10
        else:
            b["R08_contract"] = 0
            auto_reject.append("R08: 훅-SOLUTION 계약 불일치 — 훅의 명사가 해법에 재등장하지 않음")
    else:
        b["R08_contract"] = 0
        notes.append("R08: solution_text 미제공 — 계약 검사 생략")

    # R09 첫 프레임 계약 (+10)
    if first_frame:
        ok = (first_frame.get("hook_noun_visible")
              and first_frame.get("overlay_draw_starts_s", 9.9) <= 0.5
              and first_frame.get("overlay_words", 99) <= 5
              and first_frame.get("overlay_echoes_narration", False))
        b["R09_frame0"] = 10 if ok else 0
    else:
        b["R09_frame0"] = 0
        notes.append("R09: first_frame 미제공 — 렌더 단계에서 검사")

    # R10 수치 정밀성 (+5 보너스) [약 — 재보정 1순위]
    nums = lx.numbers_in(hook)
    b["R10_precision"] = 5 if (nums and not any(lx.is_round_number(n) for n in nums)) else 0
    if any(lx.is_round_number(n) for n in nums):
        notes.append("R10: 반올림 수치 감지 — 검증 가능한 정확값으로 교체하거나 결손형(T01) 폴백")

    total = sum(b.values())
    if auto_reject:
        verdict = "reject"
    elif total >= config.HOOK_PASS:
        verdict = "pass"
    elif total >= config.HOOK_REGEN:
        verdict = "regen"
    else:
        verdict = "reject"
    return {"total": total, "verdict": verdict, "breakdown": b,
            "auto_reject": auto_reject, "notes": notes,
            "first_sentence_words": n_first, "words_to_payoff": n_to_payoff,
            "title_ok": (title is None or len(title) <= config.TITLE_MAX_CHARS)}


def score_candidates(cands: list[dict]) -> list[dict]:
    """훅 후보 리스트 채점 + 정렬. cands: [{"hook":.., "solution":.., "template_id":..}]"""
    out = []
    for c in cands:
        r = score_hook(c["hook"], c.get("solution"), c.get("title"))
        out.append({**c, **r})
    out.sort(key=lambda x: x["total"], reverse=True)
    return out
