# -*- coding: utf-8 -*-
"""10차(리스크부문 v0.7 작업 6, 9차 잔여 확인) — 공용 도구와 법령·별표 수집.

    python3 scripts/dart/web10.py laws       # 6-1 금산법·시행령·금융지주회사감독규정 현행 → 법령원문_10차/
    python3 scripts/dart/web10.py laws "주식회사 등의 외부감사에 관한 법률"   # 이름을 주면 그 법령만
    python3 scripts/dart/web10.py cite       # 6-1 금산법_인용대조.csv · 금산법_확인.csv
    python3 scripts/dart/web10.py define     # 6-6 계열회사_정의대조.csv (공정거래법·연결 조문)
    python3 scripts/dart/web10.py annex37    # 6-2 보험업감독업무시행세칙 별표37 → 원문_10차/세칙_별표37.md
    python3 scripts/dart/web10.py posting    # 6-4 목록_연차보고서_게시처.csv (사이트별 확인 결과 합치기)

9차 산출물(handoff/ 아래 9차 파일)은 건드리지 않는다. 새 산출물은 handoff/원문_10차/, handoff/법령원문_10차/.
원본: dart_out/raw/web10/<작업>/ (git 무시) — 받은 바이트 그대로 + .meta.json(출처·시각·HTTP·sha256).
웹 요청은 9차 web9.Web 과 같다(UA·1.2초 간격·3회 재시도). 법제처는 7차 lawclient(OC 는 env/.env, 기록은 OC=***).
robots.txt 가 막는 경로는 받지 않고 사유를 남긴다(우회 없음).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web9 import Web, now, UA  # noqa: E402,F401  — 9차 공용 모듈 그대로

RAW = os.path.join("dart_out", "raw", "web10")
WORK = os.path.join("dart_out", "risk10")
OUT = os.path.join("handoff", "원문_10차")
LAWOUT = os.path.join("handoff", "법령원문_10차")


def save(task, name, body, meta):
    """원본 바이트를 dart_out/raw/web10/<task>/<name> 에, 메타는 같은 이름 + .meta.json."""
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


class Robots(object):
    """사이트의 robots.txt 를 한 번 받아 저장하고, 우리 UA 로 경로 허용 여부를 답한다.

    판정은 RFC 9309 §2.3.1 그대로:
      · 2xx → 규칙대로(우리 UA 기준 can_fetch)
      · 4xx(429 제외) → 「Unavailable」: 제한 없음으로 본다(§2.3.1.3). 상태·응답 본문 첫머리는 기록.
        실측(2026-10-01) knia.or.kr 은 /robots.txt 를 보안장비가 403 으로 막는다(「Requested URL is in
        the Block URL List」) — 이 경우도 여기에 해당. 이용약관 확인은 수집 스크립트가 따로 한다.
      · 429·5xx·접속 실패 → 「Unreachable」: 전부 막힌 것으로 보고 **받지 않는다**(§2.3.1.4).
    """

    def __init__(self, web, base, task):
        self.base = base.rstrip("/")
        url = self.base + "/robots.txt"
        host = urllib.parse.urlparse(self.base).netloc
        self.status, self.note, self.rp = "", "", None
        try:
            fu, st, hd, b = web.get(url)
            save(task, "robots_%s.txt" % host, b,
                 dict(출처URL=url, 최종URL=fu, http_status=st, fetched_at=now()))
            self.rp = urllib.robotparser.RobotFileParser()
            self.rp.parse(b.decode("utf-8", "replace").splitlines())
            self.status = "OK"
        except Exception as e:                       # noqa: BLE001
            code = getattr(e, "code", None)
            if code and 400 <= code < 500 and code != 429:
                body = b""
                try:
                    body = e.read() or b""
                except Exception:                    # noqa: BLE001
                    pass
                if body:
                    save(task, "robots_%s_HTTP%d.html" % (host, code), body,
                         dict(출처URL=url, http_status=code, fetched_at=now(),
                              비고="robots.txt 응답이 %d — RFC 9309 §2.3.1.3 Unavailable(제한 없음)" % code))
                self.status = "없음(HTTP %d)" % code
                self.note = ("robots.txt 가 HTTP %d — RFC 9309 §2.3.1.3 에 따라 제한 없음으로 봄" % code)
            else:
                self.status, self.note = "확인 불가", "robots.txt 확인 실패(%s: %s) — 수집 안 함" % (type(e).__name__, e)

    def allowed(self, url):
        if self.status.startswith("없음("):
            return True
        if self.rp is None:
            return False
        return self.rp.can_fetch(UA, url)


def write_csv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    import web10_law                                  # noqa: E402 — 6-1·6-2·게시처 합치기
    fn = {"laws": web10_law.laws, "cite": web10_law.cite, "define": web10_law.define, "annex37": web10_law.annex37,
          "posting": web10_law.posting}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    if cmd == "laws" and len(argv) > 2:
        fn(argv[2:])                                # 이름을 주면 그 법령만 받는다
    else:
        fn()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
