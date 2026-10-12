"""아이템 채점 루브릭 Q/F/V/M/G/S/H + AND 게이트.

핵심 한 줄: candidate.pass = (Q>=1) AND (F>=1) AND (G>=1).
OR로 하면 '유명하지만 포화' 또는 '참신하지만 무명'이 올라와
벤치마크 모방과 같은 결과가 된다. 총점은 통과자 간 순위용일 뿐이다.

항목 (0-2점, config.ITEM_WEIGHTS 가중):
  Q 질문강도 25%  : 자동완성 verbatim=2, 유사형=1, 부재=0   [sources.autocomplete]
  F 인지도   15%  : pageviews >=50k/월=2, 5k-50k=1, <5k=0(하드게이트) [sources.wiki_pageviews]
  V 시각화   15%  : 이상(異常)이 실루엣에 보임=2, 도해로만=1, 추상=0   [판단 — Claude/사람]
  M 메커니즘 15%  : 힘·재료·구조 인과사슬이 PROBLEM 1·2+SOLUTION을 채움=2 [판단]
  G 공급공백 15%  : 24개월 내 1M+ 쇼츠 부재=2, 롱폼만=1, 바이럴 쇼츠=0 [sources.youtube_api]
                    + 소형채널(<10만) 5x+ 아웃라이어 존재 시 보너스 +5점
  S 시리즈   10%  : 형제 질문 >=3개=2, 1-2개=1, 0개=0                 [판단]
  H 훅 자산   5%  : 위험·연도·숫자 중 2종 이상 자연 보유=2             [판단]

신호가 None이면 결측(needs_review) — 게이트 통과로 치지 않는다.
백테스트: 콜로세움 9후보(재구성)에서 채택작이 1위로 나와야 루브릭 동결.
가중치 수정은 '한 번에 한 항목 + 사유 기록' 원칙 (반복 조정 금지).
"""
from __future__ import annotations

import json
import os

from . import config

SIGNAL_KEYS = ("Q", "F", "V", "M", "G", "S", "H")
JUDGMENT_KEYS = ("V", "M", "S", "H")  # 코드가 못 재는 판단 항목 — Claude/사람이 채움
OUTLIER_BONUS_POINTS = 5


def score_candidate(cand: dict) -> dict:
    """cand = {"id", "question", "object", "signals": {Q,F,V,M,G,S,H, outlier_bonus?}, ...}

    반환: {"total", "pass", "gate", "needs_review", "breakdown"}
    """
    sig = cand.get("signals", {})
    breakdown: dict[str, float] = {}
    needs_review: list[str] = []
    for k in SIGNAL_KEYS:
        v = sig.get(k)
        if v is None:
            needs_review.append(k)
            breakdown[k] = 0.0
        else:
            breakdown[k] = (min(max(v, 0), 2) / 2.0) * config.ITEM_WEIGHTS[k] * 100
    total = sum(breakdown.values())
    if sig.get("outlier_bonus"):
        total += OUTLIER_BONUS_POINTS
        breakdown["outlier_bonus"] = OUTLIER_BONUS_POINTS

    q, f, g = sig.get("Q"), sig.get("F"), sig.get("G")
    gate = {
        "Q": q is not None and q >= 1,
        "F": f is not None and f >= 1,   # F=0은 pageviews 하드게이트 탈락
        "G": g is not None and g >= 1,
    }
    return {
        "id": cand.get("id"),
        "total": round(total, 1),
        "pass": all(gate.values()),
        "gate": gate,
        "needs_review": needs_review,
        "breakdown": breakdown,
    }


def rank(cands: list[dict]) -> list[dict]:
    """통과자 먼저, 총점 내림차순. 결측 있는 후보는 통과자 뒤에 needs_review로."""
    scored = [{**c, **score_candidate(c)} for c in cands]
    scored.sort(key=lambda s: (not s["pass"], bool(s["needs_review"]), -s["total"]))
    return scored


def run_backtest(path: str | None = None, verbose: bool = False) -> bool:
    """콜로세움 9후보 백테스트: 채택작('why_half_missing')이 1위인지 확인.

    불일치 시 루브릭 가중치를 '한 번에 한 항목'만 조정하고 사유를 기록할 것.
    """
    path = path or os.path.join(os.path.dirname(__file__), "..", "examples",
                                "candidates_colosseum.json")
    with open(path, encoding="utf-8") as fh:
        cands = json.load(fh)
    ranked = rank(cands)
    if verbose:
        for i, r in enumerate(ranked, 1):
            flag = "PASS" if r["pass"] else "fail"
            print(f"{i:2d}. [{flag}] {r['total']:5.1f}  {r['id']}  gate={r['gate']}")
    top_pass = next((r for r in ranked if r["pass"]), None)
    return bool(top_pass and top_pass["id"] == "why_half_missing")


if __name__ == "__main__":
    ok = run_backtest(verbose=True)
    print("\n백테스트:", "OK — 채택작 1위, 루브릭 동결" if ok else "FAIL — 가중치 1항목 조정 필요")
