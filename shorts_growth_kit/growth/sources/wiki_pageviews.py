"""Wikipedia Pageviews — 인지도 신호 F. 무인증, 학술 검증된 attention proxy.

실측(2026-09): Colosseum ~130k/월, Great Wall 91.8k, Hagia Sophia 75.5k,
Roman aqueduct 9.6k — 13배 스프레드로 변별력 충분.

루브릭 앵커 (config): 직전 3개월 평균 >=50k/월 = 2점, 5k-50k = 1점,
<5k = 0점(하드게이트 탈락 — 콜드 피드에서 첫 프레임 1초 인식 불가).

주의: 문서명 특수문자는 URL 인코딩 필수, 연속 호출 간 sleep 권장(간헐 실패 실측).
"""
from __future__ import annotations

import datetime as dt
import urllib.parse

from . import http_get_json
from .. import config

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews"


def monthly_views(article: str, months: int = 3, project: str = "en.wikipedia",
                  today: dt.date | None = None) -> list[int] | None:
    """직전 N개 완결 월의 월간 조회수 리스트(오름차순). 실패 시 None."""
    today = today or dt.date.today()
    first_this_month = today.replace(day=1)
    end = first_this_month - dt.timedelta(days=1)          # 지난달 말일
    start = _shift_months(first_this_month, -months)        # N개월 전 1일
    title = urllib.parse.quote(article.replace(" ", "_"), safe="")
    url = (f"{API}/per-article/{project}/all-access/user/{title}/monthly/"
           f"{start:%Y%m%d}00/{end:%Y%m%d}00")
    data = http_get_json(url)
    if not data or "items" not in data:
        return None
    return [item.get("views", 0) for item in data["items"]]


def avg_monthly(article: str, months: int = 3) -> int | None:
    v = monthly_views(article, months)
    if not v:
        return None
    return round(sum(v) / len(v))


def recognition_score(article: str) -> tuple[int | None, int | None]:
    """루브릭 F: (점수, 월평균). 조회 실패 시 (None, None) — 결측은 needs_review."""
    avg = avg_monthly(article)
    if avg is None:
        return None, None
    if avg >= config.PAGEVIEWS_TIER_HIGH:
        return 2, avg
    if avg >= config.PAGEVIEWS_HARD_GATE:
        return 1, avg
    return 0, avg  # 하드게이트 탈락


def top_articles(year: int, month: int, project: str = "en.wikipedia",
                 limit: int = 100) -> list[dict] | None:
    """월간 최다 조회 문서 — 신규 객체 역발굴용."""
    url = f"{API}/top/{project}/all-access/{year}/{month:02d}/all-days"
    data = http_get_json(url)
    if not data or "items" not in data or not data["items"]:
        return None
    return data["items"][0].get("articles", [])[:limit]


def _shift_months(d: dt.date, delta: int) -> dt.date:
    m = d.month - 1 + delta
    return d.replace(year=d.year + m // 12, month=m % 12 + 1, day=1)
