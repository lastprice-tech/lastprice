# -*- coding: utf-8 -*-
"""15차 g2 — 연차보고서 호스트 5곳 robots.txt 판정(RFC 9309, web10.Robots 그대로). 저장: dart_out/raw/governance15/<회사>/"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import web13
web13.RAW = os.path.join("dart_out", "raw", "governance15")
from web13 import Web, Robots, now

HOSTS = {"메리츠금융지주": "https://www.meritzgroup.com", "iM금융지주": "https://www.imfngroup.com",
         "BNK금융지주": "https://www.bnkfg.com", "JB금융지주": "https://www.jbfg.com",
         "한국투자금융지주": "https://www.koreaholdings.com"}
w = Web()
out = {}
for co, base in HOSTS.items():
    r = Robots(w, base, co)
    out[co] = dict(base=base, status=r.status, note=r.note, checked_at=now())
    print(co, r.status, r.note)
json.dump(out, open(os.path.join(web13.RAW, "robots_판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
