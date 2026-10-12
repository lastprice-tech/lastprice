"""Google/YouTube 자동완성 하베스터 — 수요 신호 Q의 1차 소스.

실측(2026-09): suggestqueries.google.com 무인증 200 OK. "why does the colosseum
have a chunk missing"이 verbatim 서제스트로 존재 — 채택작의 수요가 검증돼 있었다.

주의: 비공식·비문서화 엔드포인트다. 언제든 차단·형식 변경될 수 있으므로
(1) 실패는 결측으로 처리되고, (2) 헬스체크(healthcheck)를 주간 크론 첫 단계에 두고,
(3) 폴백은 YouTube 검색창 자동완성 수동 캡처 또는 Google Trends API(승인 후)다.

시드 패턴 x 객체명 x A-Z 1글자 확장으로 롱테일까지 수집한다.
요청 간 sleep(기본 1.0s) — 예의 있는 속도 유지.
"""
from __future__ import annotations

import time

from . import http_get_json

ENDPOINT = "https://suggestqueries.google.com/complete/search"

SEED_PATTERNS = [
    "why is the {x}", "why was the {x}", "why does the {x} have",
    "how did the {x}", "what's inside the {x}", "what's under the {x}",
    "why did the {x}",
]


def get_suggestions(query: str, youtube: bool = False,
                    hl: str = "en", gl: str = "us") -> list[str] | None:
    """단일 쿼리의 서제스트. 실패 시 None(결측), 성공 시 리스트(빈 리스트 가능)."""
    params = {"client": "firefox", "hl": hl, "gl": gl, "q": query}
    if youtube:
        params["ds"] = "yt"
    data = http_get_json(ENDPOINT, params)
    if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
        return None
    return [s for s in data[1] if isinstance(s, str)]


def healthcheck() -> bool:
    s = get_suggestions("why is the colosseum")
    return bool(s)


def harvest(objects: list[str], youtube: bool = False, expand_az: bool = False,
            sleep_s: float = 1.0, patterns: list[str] | None = None) -> dict[str, list[str]]:
    """객체명 리스트 -> {쿼리: [서제스트...]}. expand_az=True면 각 시드에 a-z 1글자 확장."""
    out: dict[str, list[str]] = {}
    pats = patterns or SEED_PATTERNS
    for obj in objects:
        for pat in pats:
            seeds = [pat.format(x=obj)]
            if expand_az:
                seeds += [f"{pat.format(x=obj)} {c}" for c in "abcdefghijklmnopqrstuvwxyz"]
            for seed in seeds:
                sug = get_suggestions(seed, youtube=youtube)
                if sug:
                    out[seed] = sug
                time.sleep(sleep_s)
    return out


def verbatim_score(question: str, suggestions_pool: list[str]) -> int:
    """루브릭 Q 항목: verbatim 존재=2, 유사형(내용어 60%+ 겹침)=1, 부재=0."""
    qn = _norm(question)
    pool = [_norm(s) for s in suggestions_pool]
    if qn in pool:
        return 2
    q_words = set(qn.split())
    for s in pool:
        s_words = set(s.split())
        if q_words and len(q_words & s_words) / len(q_words) >= 0.6:
            return 1
    return 0


def _norm(s: str) -> str:
    return " ".join(s.lower().replace("'", "'").split())
