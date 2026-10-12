"""12슬롯 v2 대본 린터.

입력 스키마 (examples/script_example.json 참조):
{
  "title": "Why is half the Colosseum missing?",
  "target_seconds": 65,
  "debate_seed": {"kind": "defensible_superlative", "text": "...", "pinned_comment": "..."},
  "slots": [{"id": "HERE_IS", "text": "..."}, ... 12개, config.SLOTS_V2 순서]
}

반환: {"ok": bool, "errors": [...], "warnings": [...], "stats": {...}}
error = 게이트 반려, warning = 감독 판단.

린트 항목 (PLAN.html §3):
  단어수 145-170 / 예상 WPM 135-155
  훅: 첫 문장 <=8단어, 페이오프 <=12단어, SOLUTION 키워드 금지, 정밀 숫자·날짜 1개
  재훅(슬롯 5/7/9): 의문문 or 반전 접속 + 미등장 명사 >=1
  각 슬롯 끝 펀치 문장 <=6단어 (warn)
  you/your 2-6개, SOLUTION에 0
  정밀 숫자 2-4개, 반올림 금지
  STAKES <=12단어, 앞 슬롯 문장 재사용 금지
  CLOSING_LOOP 시그니처 "That is the ___"
  문장 길이 분산: 연속 3문장 +-3단어 균일 시 warn
  제목 <=40자 완결형 질문
  debate_seed 존재
"""
from __future__ import annotations

from . import config, lexicons as lx

_CONTRAST_OPENERS = ("but", "except", "here's", "heres", "and yet", "yet", "until",
                     "instead", "worse", "what nobody", "the answer", "so they")


def _slot_map(script: dict) -> dict[str, str]:
    return {s["id"]: s.get("text", "") for s in script.get("slots", [])}


def lint(script: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    slots = _slot_map(script)
    order = [sid for sid, _, _ in config.SLOTS_V2]

    # 슬롯 구성
    missing = [sid for sid in order if sid not in slots]
    if missing:
        errors.append(f"슬롯 누락: {missing}")
    extra = [sid for sid in slots if sid not in order]
    if extra:
        warnings.append(f"알 수 없는 슬롯: {extra} (v2 id: {order})")

    full_text = " ".join(slots.get(sid, "") for sid in order)
    total_words = lx.word_count(full_text)
    target_s = script.get("target_seconds", sum(config.TARGET_SECONDS) / 2)

    # 단어 예산 & WPM
    lo, hi = config.WORD_BUDGET
    if not (lo <= total_words <= hi):
        errors.append(f"단어수 {total_words} — 예산 {lo}-{hi} (구 120-190 상단은 과속)")
    wpm = total_words / (target_s / 60.0) if target_s else 0
    wlo, whi = config.WPM_BAND
    if wpm and not (wlo <= wpm <= whi):
        warnings.append(f"예상 {wpm:.0f} WPM — 밴드 {wlo}-{whi}. 슬롯별 speed/갭으로 조정")

    # 훅
    hook = slots.get("HERE_IS", "")
    if hook:
        sents = lx.sentences(hook)
        first_n = lx.word_count(sents[0]) if sents else 0
        if first_n > config.HOOK_FIRST_SENT_MAX_WORDS:
            errors.append(f"훅 첫 문장 {first_n}단어 — <= {config.HOOK_FIRST_SENT_MAX_WORDS} (2.5초 내 격차 개방)")
        payoff_n = lx.word_count(" ".join(sents[:2]))
        if payoff_n > config.HOOK_PAYOFF_MAX_WORDS:
            warnings.append(f"훅 페이오프까지 {payoff_n}단어 — <= {config.HOOK_PAYOFF_MAX_WORDS} 권장")
        if not (lx.numbers_in(hook) or lx.years_in(hook)):
            warnings.append("훅에 정밀 숫자/날짜 없음 — 결손형(T01)이면 허용")

    # SOLUTION 키워드가 훅/제목에 등장 금지 (구체성 예산: 답은 은폐)
    sol = slots.get("SOLUTION", "")
    if sol and hook:
        sol_kw = [w for w, _ in _top_keywords(sol, 3)]
        leak = [w for w in sol_kw if w in set(lx.content_words(hook))]
        title_leak = [w for w in sol_kw if w in set(lx.content_words(script.get("title", "")))]
        # 훅-SOLUTION '계약'(공유 명사)은 필요하므로, 유출 판정은 해법 고유 키워드가
        # 훅 명사와 전부 겹칠 때만 — 상위 키워드 3개가 모두 훅에 있으면 답이 새는 것.
        if len(leak) >= 3:
            errors.append(f"SOLUTION 키워드가 훅에 유출: {leak} — 격차가 닫힘")
        if len(title_leak) >= 2:
            warnings.append(f"SOLUTION 키워드가 제목에 유출: {title_leak}")

    # 재훅 슬롯: 의문문 or 반전 접속 + 미등장 명사
    seen_words: set[str] = set()
    for sid in order:
        text = slots.get(sid, "")
        if sid in config.REHOOK_SLOTS and text:
            first = lx.sentences(text)[0] if lx.sentences(text) else ""
            is_q = first.rstrip().endswith("?")
            starts_contrast = first.lower().lstrip().startswith(_CONTRAST_OPENERS)
            new_nouns = [w for w in lx.content_words(first) if w not in seen_words]
            if not (is_q or starts_contrast):
                errors.append(f"{sid}: 재훅 실패 — 첫 문장이 의문문/반전 접속이 아님: \"{first[:60]}\"")
            if not new_nouns:
                warnings.append(f"{sid}: 새 명사 없음 — 새 미지수를 열어야 재훅이 작동")
        seen_words |= set(lx.content_words(text))

    # 펀치 문장 (슬롯 끝 <=6단어) — TRAP/WHAT_IF_NO는 오버레이 X와 동기되므로 error급
    for sid in order:
        text = slots.get(sid, "")
        if not text:
            continue
        sents = lx.sentences(text)
        last_n = lx.word_count(sents[-1]) if sents else 0
        if last_n > config.PUNCH_SENT_MAX_WORDS:
            level = errors if sid in ("TRAP", "WHAT_IF_NO") else warnings
            level.append(f"{sid}: 끝문장 {last_n}단어 — 펀치(<= {config.PUNCH_SENT_MAX_WORDS}) 권장, 오버레이 비트와 동기")

    # you 배치: 총 2-6, SOLUTION 0
    you_total = sum(_you_count(slots.get(sid, "")) for sid in order)
    ylo, yhi = config.YOU_COUNT_RANGE
    if not (ylo <= you_total <= yhi):
        warnings.append(f"you/your {you_total}회 — {ylo}-{yhi} 범위 (투입 지점: OR_ELSE, EFFECT)")
    if _you_count(sol) > 0:
        errors.append("SOLUTION에 you 사용 — 해법의 주인공은 오브젝트/엔지니어")

    # 정밀 숫자 2-4개, 반올림 금지
    nums = lx.numbers_in(full_text)
    plo, phi = config.PRECISE_NUMBER_RANGE
    if not (plo <= len(nums) <= phi + 2):  # 상한은 느슨하게(오버레이 에코 포함 감안)
        warnings.append(f"수치 {len(nums)}개 — 권장 {plo}-{phi}개 (각 수치는 오버레이 라벨과 1:1)")
    rounded = [int(n) for n in nums if lx.is_round_number(n)]
    if rounded:
        warnings.append(f"반올림 수치 {rounded} — 사료 검증 가능한 정확값으로 (precision effect)")

    # STAKES: <=12단어, 앞 슬롯 문장 재사용 금지
    stakes = slots.get("STAKES", "")
    if stakes:
        if lx.word_count(stakes) > config.STAKES_MAX_WORDS:
            errors.append(f"STAKES {lx.word_count(stakes)}단어 — <= {config.STAKES_MAX_WORDS} (요약 아님, 3항 압축)")
        earlier = " ".join(slots.get(sid, "") for sid in order[:order.index("STAKES")]).lower()
        for s in lx.sentences(stakes):
            if len(s) > 12 and s.lower() in earlier:
                errors.append(f"STAKES 문장 재사용: \"{s[:40]}\" — 반복은 문서화된 이탈 원인")

    # CLOSING_LOOP: 시그니처
    closing = slots.get("CLOSING_LOOP", "")
    if closing and config.SIGNATURE_PREFIX not in closing.lower():
        errors.append('CLOSING_LOOP에 시그니처 "That is the ___" 없음')

    # 문장 길이 분산 (연속 3문장 +-3단어 균일 -> warn)
    lens = [lx.word_count(s) for s in lx.sentences(full_text)]
    for i in range(len(lens) - 2):
        trio = lens[i:i + 3]
        if max(trio) - min(trio) <= 3 and min(trio) >= 8:
            warnings.append(f"문장 리듬 단조: 연속 3문장 {trio}단어 — 펀치 문장으로 완급")
            break

    # 제목: <=40자 완결형 질문
    title = script.get("title", "")
    if title:
        if len(title) > config.TITLE_MAX_CHARS:
            errors.append(f"제목 {len(title)}자 — <= {config.TITLE_MAX_CHARS}자에서 완결 (셸프 말줄임)")
        if "?" not in title:
            warnings.append("제목이 질문형이 아님 — 검색 질의 일치(질문형)가 기본")

    # debate_seed
    if not script.get("debate_seed"):
        warnings.append("debate_seed 없음 — EFFECT에 방어 가능한 최상급 단정 1개 권장")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {"total_words": total_words, "projected_wpm": round(wpm, 1),
                  "numbers": nums, "you_count": you_total,
                  "sentence_lengths": lens},
    }


def _you_count(text: str) -> int:
    lower = f" {text.lower()} "
    return lower.count(" you ") + lower.count(" you'") + lower.count(" your ") \
        + lower.count(" you.") + lower.count(" you,") + lower.count(" you?")


def _top_keywords(text: str, k: int) -> list[tuple[str, int]]:
    freq: dict[str, int] = {}
    for w in lx.content_words(text):
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: -x[1])[:k]


def format_report(result: dict) -> str:
    lines = ["PASS" if result["ok"] else "FAIL",
             f"  단어 {result['stats']['total_words']} · {result['stats']['projected_wpm']} WPM · "
             f"수치 {len(result['stats']['numbers'])}개 · you {result['stats']['you_count']}회"]
    for e in result["errors"]:
        lines.append(f"  [E] {e}")
    for w in result["warnings"]:
        lines.append(f"  [W] {w}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json, sys
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/script_example.json"
    with open(path, encoding="utf-8") as f:
        print(format_report(lint(json.load(f))))
