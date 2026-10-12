"""StackExchange API — 보조 수요 신호. 무인증 즉시 동작 (votes + view_count).

실측(2026-09): api.stackexchange.com/2.3/questions?site=history 200 OK,
최상위 질문 view_count 19만 확인. Reddit이 무인증 차단(403/429)이라
OAuth 승인(2-4주) 전까지 이쪽이 즉시 쓸 수 있는 커뮤니티 수요 소스다.

쿼터: 무인증 IP당 300/일 — 주간 크론 1-2콜이면 충분.
"""
from __future__ import annotations

from . import http_get_json

API = "https://api.stackexchange.com/2.3"


def top_questions(site: str = "history", pagesize: int = 50,
                  sort: str = "votes", tagged: str | None = None) -> list[dict] | None:
    params = {"site": site, "pagesize": min(pagesize, 100), "sort": sort,
              "order": "desc", "filter": "default"}
    if tagged:
        params["tagged"] = tagged
    data = http_get_json(f"{API}/questions", params)
    if not data or "items" not in data:
        return None
    return [{
        "title": q.get("title", ""),
        "score": q.get("score", 0),
        "view_count": q.get("view_count", 0),
        "link": q.get("link", ""),
        "tags": q.get("tags", []),
    } for q in data["items"]]


def demand_signal(question_keywords: list[str], pool: list[dict]) -> dict:
    """후보 질문 키워드가 SE 상위 질문과 겹치는지 — 로그 스케일 보조 점수용."""
    kw = {k.lower() for k in question_keywords}
    hits = []
    for q in pool:
        title_words = set(q["title"].lower().split())
        if len(kw & title_words) >= 2:
            hits.append(q)
    best = max(hits, key=lambda q: q["view_count"], default=None)
    return {"hits": len(hits), "best_views": best["view_count"] if best else 0,
            "best_link": best["link"] if best else None}
