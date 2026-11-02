# -*- coding: utf-8 -*-
"""15차 — 지배구조 및 보수체계 연차보고서(그룹 g1: KB·신한·하나·우리·NH농협) 과거 연도(공시연도 2020~2024) 수집.

    python -I scripts/dart/ops15_gov_g1.py robots     # 호스트마다 robots.txt 받아 판정(RFC 9309) → 작업 기록
    python -I scripts/dart/ops15_gov_g1.py get URL [저장이름]  # (탐색용) robots 허용이면 받아 저장

HTTP 는 scripts/dart/web13.py 의 Web(=web9.Web: UA 고정·1.2초 간격·3회 재시도)·Robots(RFC 9309 판정) 를 쓰고,
저장 위치만 dart_out/raw/governance15/<회사>/ 로 바꾼다(web13.RAW 를 쓰지 않음).
robots.txt 가 막는 경로는 받지 않고 사유를 남긴다(우회 없음). API 키 쓰지 않음.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))
os.chdir(ROOT)
import web10  # noqa: E402
import web13  # noqa: E402
from web13 import Web, now  # noqa: E402

RAW = os.path.join("dart_out", "raw", "governance15")
WORK = os.path.join("dart_out", "ops15", "gov15_g1_work")

HOSTS = {
    "KB금융지주": ["https://www.kbfg.com"],
    "신한금융지주": ["https://www.shinhangroup.com"],
    "하나금융지주": ["https://www.hanafn.com", "https://www.hanafn.com:8002"],
    "우리금융지주": ["https://www.woorifg.com"],
    "NH농협금융지주": ["https://www.nhfngroup.com"],
}


def save(co, name, body, meta):
    """원본 바이트를 dart_out/raw/governance15/<co>/<name> 에, 메타는 같은 이름 + .meta.json."""
    d = os.path.join(RAW, co)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


class Robots(web13.Robots):
    """web10.Robots 판정 그대로, robots.txt 원본만 dart_out/raw/governance15/<co>/ 에 저장."""

    def __init__(self, web, base, co):
        _save = web10.save
        web10.save = save
        try:
            web10.Robots.__init__(self, web, base, co)
        finally:
            web10.save = _save


def robots_all():
    w = Web()
    out = {}
    for co, bases in HOSTS.items():
        for b in bases:
            r = Robots(w, b, co)
            host = urllib.parse.urlparse(b).netloc
            out[host] = dict(co=co, base=b, status=r.status, note=r.note, checked_at=now())
            print(co, host, r.status, r.note[:120])
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "robots.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


_ROBOTS = {}


def robots_for(w, url, co):
    pu = urllib.parse.urlparse(url)
    base = "%s://%s" % (pu.scheme, pu.netloc)
    if base not in _ROBOTS:
        _ROBOTS[base] = Robots(w, base, co)
    return _ROBOTS[base]


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "robots":
        robots_all()
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
