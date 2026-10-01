# -*- coding: utf-8 -*-
"""10차 6-6(나) — 금융지주 소속 보험 자회사의 「대주주와의 거래」 공시(보험업법 §111③④) 중 거래 상대방이 지주 또는
지주의 다른 자회사인 건.

    python3 scripts/dart/web10_insdeal.py robots     # 호스트별 robots.txt → dart_out/risk10/보험자회사_robots.csv

대상: 메리츠화재, KB손해보험, KB라이프, 신한라이프, 하나생명.
출처 후보: 각 사 누리집 공시실, 생명보험협회 공시실(pub.insure.or.kr). 손해보험협회(knia.or.kr 와 하위 도메인)는
다른 에이전트가 쓰고 있어 요청하지 않는다(행 note 에 「다른 작업이 맡음 — 이번에 미확인」).
규율(COMMON.md): web10.Web(UA 고정·1.2초 간격·3회 재시도)만 쓴다. 호스트마다 web10.Robots 로 확인하고 막힌 URL 은
요청하지 않는다. 로그인·캡차·차단 화면이 나오면 우회하지 않고 멈춘다.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))

from web10 import Web, Robots, now, write_csv, WORK, RAW   # noqa: E402

TASK = "insdeal"
HOSTS = [
    ("메리츠화재", "https://www.meritzfire.com"),
    ("KB손해보험", "https://www.kbinsure.co.kr"),
    ("KB라이프", "https://www.kblife.co.kr"),
    ("신한라이프", "https://www.shinhanlife.co.kr"),
    ("하나생명", "https://www.hanalife.co.kr"),
    ("생명보험협회 공시실", "https://pub.insure.or.kr"),
]


def robots():
    w = Web()
    rows = []
    for label, base in HOSTS:
        r = Robots(w, base, TASK)
        host = base.split("//")[1]
        p = os.path.join(RAW, TASK, "robots_%s.txt" % host)
        txt = open(p, encoding="utf-8", errors="replace").read() if r.status == "OK" and os.path.exists(p) else ""
        rows.append(dict(label=label, host=host, status=r.status, note=r.note,
                         root_allowed=r.allowed(base + "/"), robots_text=" ".join(txt.split())[:1500],
                         checked_at=now()))
        print(label, host, r.status, r.allowed(base + "/"), " ".join(txt.split())[:300], flush=True)
    write_csv(os.path.join(WORK, "보험자회사_robots.csv"), list(rows[0].keys()), rows)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"robots": robots}.get(cmd, lambda: print(__doc__))()
