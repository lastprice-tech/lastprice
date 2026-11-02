# -*- coding: utf-8 -*-
"""15차 g2 — 페이지 하나를 robots 확인 뒤 받아 dart_out/raw/governance15/<회사>/_pages/<name> 에 저장(+meta).
사용: python3 gov15_g2_fetch.py <회사> <url> <name> [--post k=v&k=v] [--referer URL]"""
import json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import web13
web13.RAW = os.path.join("dart_out", "raw", "governance15")
from web13 import Web, now, save
import urllib.robotparser
co, url, name = sys.argv[1:4]
data = ref = None
a = sys.argv[4:]
if "--post" in a: data = a[a.index("--post") + 1]
if "--referer" in a: ref = a[a.index("--referer") + 1]
host = urllib.parse.urlparse(url).netloc
rd = os.path.join(web13.RAW, co)
rob = [f for f in os.listdir(rd) if f.startswith("robots_" + host)]
if not rob: sys.exit("robots 판정 없음: " + host)
if rob[0].endswith(".txt"):
    rp = urllib.robotparser.RobotFileParser(); rp.parse(open(os.path.join(rd, rob[0]), encoding="utf-8", errors="replace").read().splitlines())
    if not rp.can_fetch(web13.UA, url): sys.exit("robots 금지: " + url)
w = Web()
try:
    fu, st, hd, b = w.get(url, referer=ref or "", data=(data.encode() if data else None),
                          headers=({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"} if data else None))
except Exception as e:
    print("ERR", type(e).__name__, getattr(e, "code", ""), e); sys.exit(1)
p, m = save(os.path.join(co, "_pages"), name, b, dict(출처URL=url, POST=data or "", 최종URL=fu, http_status=st,
           content_type=hd.get("Content-Type", ""), content_disposition=hd.get("Content-Disposition", ""), fetched_at=now()))
print(st, fu, len(b), hd.get("Content-Type", ""), hd.get("Content-Disposition", ""), p)
