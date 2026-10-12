"""에피소드 메타데이터 + 성과 스냅샷 SQLite 스키마.

원칙 (PLAN.html §6):
- 성과는 API로 언제든 다시 뽑을 수 있지만, 제작 변수(훅 유형·슬롯 타이밍·프롬프트
  버전)는 제작 순간에 기록하지 않으면 영원히 소실된다 — 조립 단계에서 upsert할 것.
- 스냅샷은 고정 호라이즌(48h/7d/28d) — 에피소드 비교는 반드시 같은 나이끼리.
- 판정은 비율 지표로만, engagedViews >= 500 이후 (analytics.verdict_allowed).
- n=20 수준에서는 회귀가 아니라 '큰 효과의 방향'만 — 가설은 사전 등록 2-3개.
"""
from __future__ import annotations

import json
import sqlite3
import statistics

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  episode_id       TEXT PRIMARY KEY,
  video_id         TEXT,
  upload_ts        TEXT,
  dow              INTEGER,          -- 0=월
  object_category  TEXT,             -- roman/bridges/cathedrals/industrial/wildcard...
  era              TEXT,
  region           TEXT,
  question_type    TEXT,             -- why_missing/why_shape/how_survived/what_if_removed
  hook_open_type   TEXT,             -- danger/date/number/counterfactual/scale
  hook_template_id TEXT,             -- hooks.TEMPLATES T01-T15
  hook_text        TEXT,
  hook_word_count  INTEGER,
  hook_score       INTEGER,          -- hooks.score_hook total
  first_frame_desc TEXT,
  loop_design      INTEGER,          -- 0/1: 마지막 프레임=첫 프레임
  duration_s       REAL,
  word_count       INTEGER,
  tts_wpm          REAL,
  slot_timings     TEXT,             -- JSON [{"slot","start","end"}] (analytics 귀속의 전제)
  debate_seed      TEXT,             -- JSON {"kind","text","pinned_comment"}
  sources          TEXT,             -- JSON 수치·연도별 출처 (사실 오류 프로토콜)
  prompt_version   TEXT,
  image_model      TEXT,
  video_model      TEXT,
  cost_usd         REAL
);
CREATE TABLE IF NOT EXISTS snapshots (
  episode_id        TEXT NOT NULL,
  horizon           TEXT NOT NULL,   -- '48h' | '7d' | '28d'
  captured_ts       TEXT,
  views             INTEGER,         -- 2025-03 이후 인플레이트 지표 — 판정에 쓰지 말 것
  engaged_views     INTEGER,         -- 판정 기준 지표
  stay_rate         REAL,            -- engaged/views (루프 성공작 왜곡 주의)
  apv               REAL,            -- 평균 시청 비율
  avd_s             REAL,
  retention_curve   TEXT,            -- JSON 100pt audienceWatchRatio
  slot_drops        TEXT,            -- JSON [{"slot","drop"}] (analytics.slot_attribution)
  curve_shape       TEXT,            -- cliff | mid_drop | plateau_loop | normal
  subs_gained       INTEGER,
  likes             INTEGER,
  shares            INTEGER,
  comments          INTEGER,
  shorts_feed_share REAL,
  search_share      REAL,
  us_share          REAL,
  PRIMARY KEY (episode_id, horizon)
);
"""

_JSON_FIELDS = {"slot_timings", "debate_seed", "sources", "retention_curve", "slot_drops"}


def connect(path: str = "episodes.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _encode(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        out[k] = json.dumps(v, ensure_ascii=False) if (k in _JSON_FIELDS and v is not None
                                                       and not isinstance(v, str)) else v
    return out


def upsert_episode(conn: sqlite3.Connection, ep: dict) -> None:
    ep = _encode(ep)
    cols = ", ".join(ep)
    marks = ", ".join("?" * len(ep))
    updates = ", ".join(f"{k}=excluded.{k}" for k in ep if k != "episode_id")
    conn.execute(
        f"INSERT INTO episodes ({cols}) VALUES ({marks}) "
        f"ON CONFLICT(episode_id) DO UPDATE SET {updates}", list(ep.values()))
    conn.commit()


def add_snapshot(conn: sqlite3.Connection, snap: dict) -> None:
    snap = _encode(snap)
    cols = ", ".join(snap)
    marks = ", ".join("?" * len(snap))
    updates = ", ".join(f"{k}=excluded.{k}" for k in snap
                        if k not in ("episode_id", "horizon"))
    conn.execute(
        f"INSERT INTO snapshots ({cols}) VALUES ({marks}) "
        f"ON CONFLICT(episode_id, horizon) DO UPDATE SET {updates}", list(snap.values()))
    conn.commit()


# ------------------------------------------------------------------ 리포트
def hook_type_report(conn: sqlite3.Connection, horizon: str = "48h",
                     min_episodes: int = 8) -> list[dict]:
    """훅 오프너 유형별 stay_rate 집계. n < min_episodes면 '잠정' 라벨 (표본 규율)."""
    rows = conn.execute(
        "SELECT e.hook_open_type AS t, s.stay_rate AS r FROM episodes e "
        "JOIN snapshots s ON s.episode_id = e.episode_id "
        "WHERE s.horizon = ? AND s.stay_rate IS NOT NULL", (horizon,)).fetchall()
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["t"] or "unknown", []).append(row["r"])
    out = []
    for t, vals in groups.items():
        out.append({"hook_open_type": t, "n": len(vals),
                    "median_stay_rate": round(statistics.median(vals), 3),
                    "provisional": len(vals) < min_episodes})
    out.sort(key=lambda x: -x["median_stay_rate"])
    return out


def slot_drop_leaderboard(conn: sqlite3.Connection, horizon: str = "7d",
                          last_n: int = 10) -> list[dict]:
    """최근 N편 이동 집계에서 이탈 1위 슬롯 — 해당 슬롯 초수 감축/시각 이벤트 추가 대상."""
    rows = conn.execute(
        "SELECT s.slot_drops AS d FROM snapshots s JOIN episodes e "
        "ON e.episode_id = s.episode_id WHERE s.horizon = ? AND s.slot_drops IS NOT NULL "
        "ORDER BY e.upload_ts DESC LIMIT ?", (horizon, last_n)).fetchall()
    agg: dict[str, list[float]] = {}
    for row in rows:
        for item in json.loads(row["d"]):
            agg.setdefault(item["slot"], []).append(item["drop"])
    out = [{"slot": s, "n": len(v), "mean_drop": round(sum(v) / len(v), 4)}
           for s, v in agg.items()]
    out.sort(key=lambda x: -x["mean_drop"])
    return out


def recalibration_ready(conn: sqlite3.Connection, min_episodes: int = 20) -> bool:
    n = conn.execute("SELECT COUNT(*) AS c FROM episodes").fetchone()["c"]
    return n >= min_episodes
