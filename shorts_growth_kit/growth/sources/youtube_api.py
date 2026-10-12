"""YouTube Data API v3 — 아웃라이어 스캔 · 공급 공백 검사 · 댓글 질문 채굴.

환경변수 YT_API_KEY 필요 (https://console.cloud.google.com 에서 발급, 무료).
없으면 모든 함수가 None을 돌려주고 파이프라인은 해당 신호를 결측 처리한다.

쿼터 예산 (일 10,000 units 기본):
  search.list = 100u  -> 공백 검사는 하루 ~40건 상한으로 설계
  videos.list / channels.list / playlistItems.list = 1u
  commentThreads.list = 1u (100댓글) -> 댓글 채굴은 사실상 공짜

아웃라이어 원리 [강 — vidIQ/1of10 공통 관행]:
  outlier = 영상 조회수 / 그 채널 최근 90일 쇼츠 조회수 '중앙값' (평균 금지)
  3x=중간, 5x=강, 10x=예외적. >=3x가 서로 다른 채널 2곳 이상에서 같은 주제로
  발생하면 '검증된 수요 + 약한 공급' — 형식이 아니라 '질문'만 추출해 이식한다.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import statistics

from . import http_get_json
from .. import config

API = "https://www.googleapis.com/youtube/v3"
_QUESTION_RE = re.compile(r"\b(why|how|what about|didn'?t|still don'?t|is it true)\b", re.I)


def _key() -> str | None:
    return os.environ.get("YT_API_KEY")


def _get(path: str, params: dict) -> dict | None:
    if not _key():
        return None
    params = {**params, "key": _key()}
    return http_get_json(f"{API}/{path}", params)


# ------------------------------------------------------------------ 검색/공백
def search_shorts(query: str, max_results: int = 20,
                  published_after_months: int | None = None) -> list[dict] | None:
    """search.list (100u). 쇼츠 근사: videoDuration=short (<4분)."""
    params = {"part": "snippet", "q": query, "type": "video",
              "videoDuration": "short", "maxResults": min(max_results, 50),
              "relevanceLanguage": "en", "order": "viewCount"}
    if published_after_months:
        after = dt.datetime.utcnow() - dt.timedelta(days=30 * published_after_months)
        params["publishedAfter"] = after.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = _get("search", params)
    if not data or "items" not in data:
        return None
    ids = [it["id"]["videoId"] for it in data["items"] if it.get("id", {}).get("videoId")]
    stats = video_stats(ids) or {}
    out = []
    for it in data["items"]:
        vid = it.get("id", {}).get("videoId")
        if not vid:
            continue
        s = stats.get(vid, {})
        out.append({"video_id": vid,
                    "title": it["snippet"]["title"],
                    "channel_id": it["snippet"]["channelId"],
                    "channel_title": it["snippet"]["channelTitle"],
                    "published_at": it["snippet"]["publishedAt"],
                    "views": s.get("views", 0),
                    "duration_s": s.get("duration_s", 0)})
    return out


def video_stats(video_ids: list[str]) -> dict[str, dict] | None:
    """videos.list (1u/50개) -> {id: {views, duration_s}}."""
    if not video_ids:
        return {}
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = _get("videos", {"part": "statistics,contentDetails", "id": ",".join(chunk)})
        if not data:
            return None
        for it in data.get("items", []):
            out[it["id"]] = {
                "views": int(it.get("statistics", {}).get("viewCount", 0)),
                "duration_s": _iso_duration_s(it.get("contentDetails", {}).get("duration", "")),
            }
    return out


def gap_check(question: str) -> dict | None:
    """루브릭 G: 24개월 내 1M+ 쇼츠(<=180s) 존재 여부 + 최고 경쟁작.

    G 채점: 부재=2 (단 Q>=1일 때만 — 수요 없어서 없는 것과 구별),
            롱폼만 존재=1, 바이럴 쇼츠 존재=0.
            소형채널(<10만 구독) 5x+ 아웃라이어 존재 시 +1 보너스.
    """
    results = search_shorts(question, max_results=20,
                            published_after_months=config.GAP_MONTHS)
    if results is None:
        return None
    shorts = [r for r in results if 0 < r["duration_s"] <= 180]
    viral = [r for r in shorts if r["views"] >= config.GAP_VIRAL_VIEWS]
    best = max(shorts, key=lambda r: r["views"], default=None)
    return {"score": 0 if viral else 2,
            "viral_shorts": viral[:3],
            "best_short": best,
            "checked": len(results)}


# ------------------------------------------------------------------ 아웃라이어
def channel_uploads_playlist(channel_id: str) -> str | None:
    data = _get("channels", {"part": "contentDetails", "id": channel_id})
    if not data or not data.get("items"):
        return None
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def channel_recent_shorts(channel_id: str, days: int = 90,
                          max_videos: int = 100) -> list[dict] | None:
    """채널 최근 N일 쇼츠 목록 (playlistItems 1u/50개 + videos 1u/50개)."""
    pl = channel_uploads_playlist(channel_id)
    if not pl:
        return None
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
    items, page = [], None
    while len(items) < max_videos:
        params = {"part": "snippet,contentDetails", "playlistId": pl, "maxResults": 50}
        if page:
            params["pageToken"] = page
        data = _get("playlistItems", params)
        if not data:
            break
        stop = False
        for it in data.get("items", []):
            pub = it["snippet"].get("publishedAt", "")
            if pub and dt.datetime.strptime(pub[:19], "%Y-%m-%dT%H:%M:%S") < cutoff:
                stop = True
                break
            items.append({"video_id": it["contentDetails"]["videoId"],
                          "title": it["snippet"]["title"],
                          "published_at": pub})
        page = data.get("nextPageToken")
        if stop or not page:
            break
    stats = video_stats([i["video_id"] for i in items]) or {}
    out = []
    for i in items:
        s = stats.get(i["video_id"], {})
        if 0 < s.get("duration_s", 0) <= 180:  # 쇼츠만
            out.append({**i, **s})
    return out


def outlier_scan(channel_ids: list[str], days: int = 90,
                 threshold: float = config.OUTLIER_MODERATE) -> list[dict]:
    """채널들의 최근 쇼츠에서 중앙값 대비 >=threshold 배 영상을 수집.

    반환 항목: {channel_id, video_id, title, views, median, multiplier}
    2개 이상 채널에서 같은 주제 엔티티가 겹치면 최우선 후보 — 주제 겹침 판정은
    호출자(Claude/사람)가 title들을 보고 한다 (개체명 추출은 판단 작업).
    """
    found = []
    for cid in channel_ids:
        vids = channel_recent_shorts(cid, days=days)
        if not vids or len(vids) < 5:
            continue
        med = statistics.median(v["views"] for v in vids)
        if med <= 0:
            continue
        for v in vids:
            mult = v["views"] / med
            if mult >= threshold:
                found.append({"channel_id": cid, "video_id": v["video_id"],
                              "title": v["title"], "views": v["views"],
                              "median": round(med), "multiplier": round(mult, 1)})
    found.sort(key=lambda x: -x["multiplier"])
    return found


# ------------------------------------------------------------------ 댓글 채굴
def mine_comment_questions(video_id: str, max_comments: int = 300) -> list[dict] | None:
    """벤치 영상 댓글에서 미해소 질문 후보 채굴 (commentThreads 1u/100개).

    1차 필터는 정규식(why|how|what about|didn't...)이고, '영상이 답하지 않은
    새 질문인지'의 2차 분류는 Claude가 한다 — 결과의 needs_llm_review를 채울 것.
    """
    out, page = [], None
    while len(out) < max_comments:
        params = {"part": "snippet", "videoId": video_id, "maxResults": 100,
                  "order": "relevance", "textFormat": "plainText"}
        if page:
            params["pageToken"] = page
        data = _get("commentThreads", params)
        if not data:
            return out or None
        for it in data.get("items", []):
            top = it["snippet"]["topLevelComment"]["snippet"]
            text = top.get("textDisplay", "")
            if _QUESTION_RE.search(text) and len(text) < 300:
                out.append({"text": text.strip(),
                            "likes": top.get("likeCount", 0),
                            "needs_llm_review": True})
        page = data.get("nextPageToken")
        if not page:
            break
    out.sort(key=lambda c: -c["likes"])
    return out


def _iso_duration_s(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(g) if g else 0 for g in m.groups())
    return h * 3600 + mi * 60 + s
