# -*- coding: utf-8 -*-
"""11차(리스크부문 v0.8 작업 7, 10차 잔여 확인) — 공용 경로와 도구.

9·10차 산출물은 건드리지 않는다. 새 산출물: handoff/원문_11차/, handoff/법령원문_11차/, 작업 기록 dart_out/risk11/,
원본 dart_out/raw/web11/<작업>/(git 무시). 요청 도구는 10차 web10(=9차 web9.Web: UA 고정·1.2초 간격·3회 재시도,
Robots: RFC 9309 판정)을 그대로 쓰고 저장 위치만 web11 로 바꾼다.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import web10  # noqa: E402
from web10 import Web, now, UA, write_csv  # noqa: E402,F401

RAW = os.path.join("dart_out", "raw", "web11")
WORK = os.path.join("dart_out", "risk11")
OUT = os.path.join("handoff", "원문_11차")
LAWOUT = os.path.join("handoff", "법령원문_11차")


def save(task, name, body, meta):
    """원본 바이트를 dart_out/raw/web11/<task>/<name> 에, 메타는 같은 이름 + .meta.json."""
    d = os.path.join(RAW, task)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


class Robots(web10.Robots):
    """web10.Robots 와 같은 판정. robots.txt 원본은 dart_out/raw/web11/<task>/ 에 저장."""

    def __init__(self, web, base, task):
        _save = web10.save
        web10.save = save
        try:
            super().__init__(web, base, task)
        finally:
            web10.save = _save
