"""외부 신호 수집 공통 유틸 — 표준 라이브러리 HTTP 클라이언트.

모든 소스는 실패 시 예외 대신 None/빈 값을 돌려준다(파이프라인은 신호 결측을
'unknown'으로 다루지 소스 장애로 죽지 않는다). 프록시는 환경변수(HTTPS_PROXY)를
그대로 따르고, 회사/에이전트 프록시의 사설 CA는 아래 후보 경로에서 자동 탐색한다.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "shorts-growth-kit/0.1 (research tool; contact: channel owner)"
_CA_CANDIDATES = [
    os.environ.get("REQUESTS_CA_BUNDLE"),
    os.environ.get("SSL_CERT_FILE"),
    "/root/.ccr/ca-bundle.crt",
]
_ctx_cache: dict[str, ssl.SSLContext | None] = {}


def _ssl_context() -> ssl.SSLContext | None:
    if "ctx" in _ctx_cache:
        return _ctx_cache["ctx"]
    ctx = None
    for cand in _CA_CANDIDATES:
        if cand and os.path.exists(cand):
            try:
                ctx = ssl.create_default_context(cafile=cand)
                break
            except ssl.SSLError:
                ctx = None
    _ctx_cache["ctx"] = ctx
    return ctx


def http_get(url: str, params: dict | None = None, timeout: float = 15.0,
             retries: int = 2, backoff: float = 1.5,
             headers: dict | None = None) -> bytes | None:
    """GET -> bytes. 실패 시 None (마지막 에러는 stderr가 아니라 조용히 무시 — 결측 처리)."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    if headers:
        hdrs.update(headers)
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=hdrs)
        try:
            try:
                resp = urllib.request.urlopen(req, timeout=timeout)
            except urllib.error.URLError as e:
                # 사설 CA 프록시 폴백
                if isinstance(getattr(e, "reason", None), ssl.SSLError) and _ssl_context():
                    resp = urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())
                else:
                    raise
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
            return data
        except Exception as e:  # noqa: BLE001 — 소스 장애는 결측으로 다룬다
            last_err = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    _ctx_cache.setdefault("last_error", None)
    _ctx_cache["last_error"] = f"{url.split('?')[0]}: {last_err}"  # type: ignore[assignment]
    return None


def last_error() -> str | None:
    return _ctx_cache.get("last_error")  # type: ignore[return-value]


def http_get_json(url: str, params: dict | None = None, **kw):
    data = http_get(url, params, **kw)
    if data is None:
        return None
    for enc in ("utf-8", "iso-8859-1"):
        try:
            return json.loads(data.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None
