# -*- coding: utf-8 -*-
"""법제처 국가법령정보 공동활용 Open API 통신 계층.

1~6차의 DART 수집기와 같은 규율을 지킨다:
  - 인증값(OC)은 코드에 쓰지 않는다. 환경변수 LAW_OC → 없으면 저장소 루트 .env.
  - OC 는 요청 URL 에 실리므로 **로그·manifest·예외 메시지 어디에도 원문으로 남기지
    않는다.** 남길 때는 전부 `OC=***` 로 가린다(mask).
  - 요청 간격 0.6초(요청서: 0.5초 이상), 실패 시 3회 재시도 후 기록하고 다음으로.

■ http 를 먼저 쓴다 (실측)
  이 환경의 릴레이는 www.law.go.kr:443 터널을 자주 끊는다(urllib 3/3 리셋, 프록시
  로그 ws_closed_mid_exchange). 80번은 안정적이고, 법제처 공식 예제도
  http://www.law.go.kr/DRF/… 다. 그래서 http 를 먼저 시도하고 실패할 때만 https 로
  한 번 더 간다. 어느 쪽으로 받았는지는 원장에 남긴다.
"""
from __future__ import annotations

import csv
import os
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HOSTS = ("http://www.law.go.kr", "https://www.law.go.kr")
UA = ("lastprice-research/1.0 (law archive collector for holding-company "
      "minimum-duty analysis; contact: byangsup@gmail.com)")
DELAY = 0.6
RETRIES = 3
TIMEOUT = 90


def load_oc():
    """LAW_OC 환경변수, 없으면 저장소 루트 .env. 값은 절대 출력하지 않는다."""
    v = os.environ.get("LAW_OC", "").strip()
    if v:
        return v
    p = os.path.join(REPO, ".env")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LAW_OC="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("LAW_OC 가 없습니다 — 환경변수나 저장소 루트 .env 에 LAW_OC=… 를 넣으세요")


class AuthError(RuntimeError):
    """인증 실패. 요청서 지시: 첫 호출에서 나면 멈추고 오류 원문을 보고한다."""


class LawClient(object):
    def __init__(self, ledger_path, delay=DELAY):
        self.oc = load_oc()
        self.delay = delay
        self.ledger_path = ledger_path
        self._last = 0.0
        self.n_calls = 0
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        self._new_ledger = not os.path.exists(ledger_path)

    # ── 가림 ──────────────────────────────────────────────────────────────
    def mask(self, s):
        if isinstance(s, bytes):
            return s.replace(self.oc.encode(), b"***")
        return (s or "").replace(self.oc, "***")

    def count_oc(self, b):
        return b.count(self.oc.encode()) if isinstance(b, bytes) else b.count(self.oc)

    # ── 원장 ──────────────────────────────────────────────────────────────
    def _log(self, kind, url, status, nbytes, attempts, host, err=""):
        with open(self.ledger_path, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            if self._new_ledger:
                w.writerow(["시각", "종류", "URL(OC 가림)", "HTTP", "바이트", "시도", "호스트", "오류"])
                self._new_ledger = False
            w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S%z"), kind, self.mask(url), status,
                        nbytes, attempts, host, self.mask(err)[:300]])

    def _wait(self):
        dt = time.time() - self._last
        if dt < self.delay:
            time.sleep(self.delay - dt)
        self._last = time.time()

    # ── 호출 ──────────────────────────────────────────────────────────────
    def _fetch(self, path_qs, kind):
        """(HTTP상태, 바이트, Content-Type, 가린URL, 사용호스트). 실패하면 상태 0."""
        last_err, attempts = "", 0
        for host in HOSTS:
            url = host + path_qs
            for i in range(RETRIES):
                attempts += 1
                self._wait()
                self.n_calls += 1
                try:
                    r = urllib.request.urlopen(
                        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=TIMEOUT)
                    body = r.read()
                    ct = r.headers.get("Content-Type", "")
                    # 재시도 끝에 받았으면 직전 실패 사유도 남긴다(성공 행의 오류 칸).
                    self._log(kind, url, r.status, len(body), attempts, host,
                              ("재시도 전 오류: " + last_err) if last_err else "")
                    return r.status, body, ct, self.mask(url), host
                except urllib.error.HTTPError as e:
                    last_err = "HTTP %s %s" % (e.code, e.reason)
                    if e.code in (400, 401, 403, 404):
                        break                       # 재시도해도 같다
                except Exception as e:              # noqa: BLE001 — 사유를 남기고 재시도
                    last_err = "%s: %s" % (type(e).__name__, e)
                time.sleep(2 ** (i + 1))
        self._log(kind, HOSTS[0] + path_qs, 0, 0, attempts, "", last_err)
        return 0, b"", "", self.mask(HOSTS[0] + path_qs), ""

    def api(self, service, **params):
        """DRF lawSearch.do / lawService.do. 응답 본문의 인증 오류를 감지한다."""
        qs = urllib.parse.urlencode(dict(OC=self.oc, **params))
        st, body, ct, murl, host = self._fetch("/DRF/%s?%s" % (service, qs), "api")
        head = body[:600].decode("utf-8", "replace")
        # 법제처는 오류도 HTTP 200 으로 주고 본문에 <Response><result>…</result> 를 싣는다
        # (실측: OC 없이 부르면 「필수입력요소 검증에 실패하였습니다.」). 오류 봉투일 때만
        # 본다 — 법령 본문에 「인증」·「실패」 같은 낱말이 있어도 오탐하지 않도록.
        if "<Response>" in head and "<result>" in head:
            msg = self.mask(head.strip())
            if "사용자" in head or "미승인" in head or "IP" in head or "도메인" in head:
                raise AuthError(msg)
            raise RuntimeError("API 오류 응답: " + msg)
        return st, body, murl, host

    def file(self, path):
        """/LSW/flDownload.do?flSeq=… 같은 첨부 경로. OC 는 붙지 않는다."""
        st, body, ct, murl, host = self._fetch(path, "file")
        return st, body, ct, murl, host
