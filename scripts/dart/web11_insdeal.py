# -*- coding: utf-8 -*-
"""11차 7-2 — 금융지주 소속 보험 자회사의 「대주주와의 거래」 공시(보험업법 §111③ 수시·§111④ 분기) 중 거래 상대방이
지주 본체인 건(원문 행)과 지주의 다른 자회사인 건(건수만). 10차 web10_insdeal(C24·C30) 보완.

    python3 scripts/dart/web11_insdeal.py probe <url> <저장이름> [k=v ...]   # (점검) 한 화면 받기 — robots 확인·원본 저장
    python3 scripts/dart/web11_insdeal.py collect            # 수집 → handoff/원문_11차/보험자회사_지주거래공시.csv
    python3 scripts/dart/web11_insdeal.py collect --offline  # 받지 않고 저장된 원본만으로 CSV

규율(COMMON.md·AGENT_11_INS.md): web11.Web(=web10/web9 Web: UA 고정·1.2초 간격·3회 재시도)만 쓴다. 호스트마다 web11.Robots
(RFC 9309 판정)로 확인하고 막힌 URL 은 요청하지 않는다. 로그인·캡차·보안장비 차단 화면이 나오면 우회하지 않고 멈춘다.
생명보험협회 공시실(pub.insure.or.kr)은 요청하지 않는다(10차 robots 「User-agent:* Disallow:/」 확인 — 행 note 에 사유만).
10차 web10_insdeal(PDF layout 텍스트화·서식 칸 읽기·이름 정규화)과 web10_knia(손보협회 공시실 화면 도구)를 import 해서
쓰고 고치지 않는다. 원본: dart_out/raw/web11/insdeal/ (받은 바이트 그대로 + .meta.json, sha256).
"""
from __future__ import annotations

import csv
import glob
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))

import web11                                                       # noqa: E402
from web11 import Web, save, Robots, now, write_csv, OUT, WORK, RAW   # noqa: E402
import web10_insdeal as W10                                        # noqa: E402  — 10차 보험 자회사 도구(import 만)
import web10_knia as K10                                           # noqa: E402  — 10차 손보협회 도구(import 만)

# web10_insdeal.read_layout 은 쪽 글(.layout.txt)을 모듈 전역 save(TASK, …)로 남긴다. 11차 원본은 dart_out/raw/web11/ 에
# 두어야 하므로 이 실행 안에서만 그 모듈의 save 이름을 web11.save 로 돌린다(파일은 고치지 않음, TASK 이름은 같은 "insdeal").
W10.save = web11.save

TASK = "insdeal"
DIR = os.path.join(RAW, TASK)
DIR10 = os.path.join(web11.web10.RAW, "insdeal")          # 10차 원본(같은 요청이면 다시 받지 않고 이것을 쓴다)
DIR10K = os.path.join(web11.web10.RAW, "knia")
NONE = "문서에 없음"
OFFLINE = "--offline" in sys.argv
BLOCK_WORDS = K10.BLOCK_WORDS + ["보안정책", "로그인 후 이용"]


class Stop(Exception):
    """차단·로그인·캡차·robots 금지 — 우회하지 않고 멈춘다."""


_W = None
_ROB = {}


def web():
    global _W
    if _W is None:
        _W = Web()
    return _W


def robots(base):
    """호스트(서브도메인)마다 한 번 — web11.Robots(RFC 9309, robots 원본은 dart_out/raw/web11/insdeal/)."""
    if base not in _ROB:
        if OFFLINE:
            _ROB[base] = _OfflineRobots(base)
        else:
            _ROB[base] = Robots(web(), base, TASK)
    return _ROB[base]


class _OfflineRobots(object):
    """--offline: 마지막으로 저장된 robots 원본으로 판정(받지 않음)."""

    def __init__(self, base):
        import urllib.robotparser
        self.base = base
        host = urllib.parse.urlparse(base).netloc
        p = os.path.join(DIR, "robots_%s.txt" % host)
        e = sorted(glob.glob(os.path.join(DIR, "robots_%s_HTTP*.html" % host)))
        self.rp, self.note = None, ""
        if os.path.exists(p):
            self.rp = urllib.robotparser.RobotFileParser()
            self.rp.parse(open(p, encoding="utf-8", errors="replace").read().splitlines())
            self.status = "OK"
        elif e:
            code = int(re.search(r"_HTTP(\d+)\.html$", e[-1]).group(1))
            self.status = "없음(HTTP %d)" % code
            self.note = "robots.txt 가 HTTP %d — RFC 9309 §2.3.1.3 에 따라 제한 없음으로 봄(저장본)" % code
        else:
            self.status, self.note = "확인 불가", "robots.txt 저장본 없음 — 수집 안 함"

    def allowed(self, url):
        if self.status.startswith("없음("):
            return True
        if self.rp is None:
            return False
        return self.rp.can_fetch(web11.UA, url)


def base_of(url):
    pu = urllib.parse.urlparse(url)
    return "%s://%s" % (pu.scheme, pu.netloc)


def fetch(url, name, meta=None, data=None, referer="", headers=None, enc="utf-8"):
    """robots 확인 → 받기 → 원본 저장(dart_out/raw/web11/insdeal/<name>) → 차단 신호 확인. (경로, meta, 바이트).
    robots 금지면 요청하지 않고 Stop. HTTP 오류는 응답 본문을 저장하고 Stop. --offline 이면 저장본만."""
    p0 = os.path.join(DIR, name)
    if OFFLINE:
        if os.path.exists(p0) and os.path.exists(p0 + ".meta.json"):
            return p0, json.load(open(p0 + ".meta.json", encoding="utf-8")), open(p0, "rb").read()
        raise Stop("--offline: 저장된 원본 없음 — %s" % name)
    rb = robots(base_of(url))
    if not rb.allowed(url):
        raise Stop("robots.txt(%s, 판정 %s)가 %s 를 막음 — 요청하지 않음 %s" % (base_of(url), rb.status, url, rb.note))
    req = dict(meta or {}, 출처URL=url, method="POST" if data is not None else "GET")
    if data is not None:
        req["요청본문"] = data if isinstance(data, str) else (data.decode("utf-8", "replace") if isinstance(data, bytes)
                                                          else urllib.parse.urlencode(data))
        if isinstance(data, str):
            data = data.encode("utf-8")
    try:
        fu, st, hd, b = web().get(url, referer=referer, data=data, headers=headers)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:                                # noqa: BLE001
            pass
        p, m = save(TASK, "실패응답_" + name + ".html", body,
                    dict(req, http_status=e.code, fetched_at=now(), 비고="HTTP 오류 응답 본문"))
        t = body.decode("utf-8", "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        raise Stop("%s HTTP %s%s (응답 저장 %s)" % (url, e.code, " 차단 신호 %s" % hit if hit else "", p))
    except Exception as e:                               # noqa: BLE001
        raise Stop("%s 접속 실패 %s: %s" % (url, type(e).__name__, e))
    ct = hd.get("Content-Type", "")
    cd = hd.get("Content-Disposition", "")
    p, m = save(TASK, name, b, dict(req, 최종URL=fu, http_status=st, content_type=ct, content_disposition=cd,
                                    원파일명=K10.cd_filename(cd), fetched_at=now()))
    if "html" in ct.lower():
        t = b[:60000].decode(enc, "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        if hit or "login" in urllib.parse.urlparse(fu).path.lower():
            raise Stop("%s 차단/로그인/캡차 신호 %s 최종URL %s (저장 %s)" % (url, hit, fu, p))
    return p, m, b


def probe(argv):
    url, name = argv[0], argv[1]
    data = dict(x.split("=", 1) for x in argv[2:]) or None
    try:
        p, m, b = fetch(url, name, dict(확인목적="점검(probe)"), data=data, referer=base_of(url) + "/")
    except Stop as e:
        print("Stop:", e)
        return
    print(m["http_status"], m["content_type"], m["바이트"], m["최종URL"], p)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "probe":
        probe(sys.argv[2:])
    else:
        print(__doc__)
