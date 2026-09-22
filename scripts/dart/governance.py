# -*- coding: utf-8 -*-
"""6차 — 금융지주 10곳의 지배구조·보수체계 연차보고서 수집.

원천이 DART 가 아니라 각 지주 홈페이지다. 1~5차와 같은 규율을 그대로 쓴다:
받은 파일은 손대지 않고 그대로 저장하고, 파일마다 URL·방식·HTTP 상태·바이트·sha256·
받은 시각을 .meta.json 으로 남긴다. 실패는 지어내지 않고 사유를 적는다.

`python3 scripts/dart/governance.py --dry-run`   URL 방식·도메인 분류만
`python3 scripts/dart/governance.py`             실제 다운로드
`python3 scripts/dart/governance.py --only 메리츠금융지주,신한금융지주`

■ 회사마다 다른 세 가지 방식(목록 실측)
  GET 직링크      36건 — 8곳
  GET 포트 :8002   5건 — 하나금융지주. 파일명이 URL 에 없어 목록의 저장 파일명을 쓴다
  게시글→POST      5건 — 한국투자금융지주. /kr/bbs/disclosure/read?seq=… 를 먼저 열어
                        쿠키·Referer 를 얻고 POST /common/fildDownload 로 첨부를 받는다
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ── 레거시 TLS 재협상 ─────────────────────────────────────────────────────
# 우리금융지주(www.woorifg.com)는 OpenSSL 3 이 기본으로 막는 legacy renegotiation 을
# 쓴다: [SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED]. 이건 인증서 검증을 끄는 것과
# 다르다 — 서버 신원 검증은 그대로 하고 재협상 방식만 옛 방식을 허용하는 것이다.
# OpenSSL 은 이 설정을 프로세스 시작 시 OPENSSL_CONF 에서 읽으므로, 파이썬이 ssl 을
# import 한 뒤에는 바꿀 수 없다. 그래서 설정 파일을 만들고 **한 번만 재실행**한다.
_LEGACY_CNF = """openssl_conf = openssl_init
[openssl_init]
ssl_conf = ssl_sect
[ssl_sect]
system_default = system_default_sect
[system_default_sect]
Options = UnsafeLegacyRenegotiation
CipherString = DEFAULT:@SECLEVEL=1
"""


def _ensure_legacy_tls():
    if os.environ.get("GOVERNANCE_TLS_READY") == "1":
        return
    import tempfile
    d = os.environ.get("TMPDIR") or tempfile.gettempdir()
    cnf = os.path.join(d, "governance_legacy_openssl.cnf")
    try:
        with open(cnf, "w", encoding="utf-8") as f:
            f.write(_LEGACY_CNF)
    except OSError:
        return                      # 못 쓰면 그냥 기본 설정으로 간다(사유는 실패행에 남는다)
    env = dict(os.environ, OPENSSL_CONF=cnf, GOVERNANCE_TLS_READY="1")
    os.execve(sys.executable, [sys.executable] + sys.argv, env)


HERE = os.path.dirname(os.path.abspath(__file__))
LIST_CSV = os.path.join(HERE, "data", "governance_list.csv")
DEFAULT_OUT = "dart_out"
RAW_SUB = os.path.join("raw", "governance")

# 식별 가능한 User-Agent. 익명 크롤러로 위장하지 않는다.
UA = ("lastprice-research/1.0 (financial-holding governance report collector; "
      "contact: byangsup@gmail.com)")
DELAY = 1.2          # 요청 간격(초) — 요청서는 1초 이상
ATTEMPTS = 3         # 3회 실패하면 멈추고 사유를 남긴다
TIMEOUT = 120

KIS_HOST = "www.koreaholdings.com"
KIS_POST_PATH = "/common/fildDownload"
# 목록 URL 칸의 「(첨부: POST /common/fildDownload, real_filename=/attach/…pdf)」
_REAL = re.compile(r"real_filename\s*=\s*([^\s)]+)")

MAGIC = {
    ".pdf": (b"%PDF",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".svg": (b"<svg", b"<?xml"),
}


def _ctx():
    """SSL_CERT_FILE 이 이 환경의 프록시 CA 를 가리킨다. 검증을 끄지 않는다."""
    ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    return ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()


def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=_ctx())), jar


def load_list(path=LIST_CSV):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def disclosure_type(row):
    """본공시 / 추가공시 / 정정공시 / 재공시 / 조직도.

    구분 칸에는 '지배구조·보수체계 통합' 같은 문서 종류만 있고 공시 유형은 제목과
    저장 파일명에 있다. 회사마다 표기가 달라 원문 낱말을 그대로 본다.
    """
    if (row.get("구분") or "").strip() == "조직도":
        return "조직도"
    s = "%s %s" % (row.get("저장 파일명") or "", row.get("제목") or "")
    if "재공시" in s:
        return "재공시"
    if "정정" in s:
        return "정정공시"
    if "추가" in s:
        return "추가공시"
    return "본공시"


def classify(row):
    """(방식, 다운로드 URL, 게시글 URL, real_filename). 네트워크를 쓰지 않는다."""
    raw = (row.get("URL") or "").strip()
    url = raw.split(" ")[0]
    host = urllib.parse.urlparse(url).netloc
    if host == KIS_HOST and "/bbs/" in url:
        m = _REAL.search(raw)
        return "POST", urllib.parse.urljoin(url, KIS_POST_PATH), url, (m.group(1) if m else "")
    if ":8002" in host:
        return "GET:8002", url, "", ""
    return "GET", url, "", ""


def _sig_ok(path, name):
    ext = os.path.splitext(name)[1].lower()
    want = MAGIC.get(ext)
    if not want:
        return True, ""
    with open(path, "rb") as f:
        head = f.read(1024)
    if any(head.lstrip()[:len(w)] == w for w in want):
        return True, ""
    # HTML 오류 페이지가 가장 흔한 실패 모습이다. 무엇이 왔는지 그대로 적는다.
    peek = head[:80].decode("utf-8", "replace").replace("\n", " ")
    return False, "시그니처 불일치(%s 기대) — 앞부분: %r" % (ext, peek)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _req(url, referer="", data=None):
    r = urllib.request.Request(url, data=data)
    r.add_header("User-Agent", UA)
    r.add_header("Accept", "*/*")
    r.add_header("Accept-Language", "ko,en;q=0.8")
    if referer:
        r.add_header("Referer", referer)
    if data is not None:
        r.add_header("Content-Type", "application/x-www-form-urlencoded")
    return r


def fetch_one(opener, row, out_dir, verbose=True):
    corp = (row.get("지주명") or "").strip()
    name = (row.get("저장 파일명") or "").strip()
    method, url, page, real = classify(row)
    d = os.path.join(out_dir, RAW_SUB, corp)
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, name)
    meta_p = dest + ".meta.json"

    rec = {
        "지주명": corp, "저장파일명": name, "구분": row.get("구분", ""),
        "공시유형": disclosure_type(row), "공시연도": row.get("공시연도", ""),
        "공시일": row.get("공시일", ""), "제목": row.get("제목", ""),
        "방식": method, "url": url, "게시글url": page, "real_filename": real,
        "목록크기": (row.get("크기(bytes)") or "").strip(),
        "실제url": "", "http_status": "", "content_type": "", "실제크기": "", "sha256": "",
        "성공": "N", "실패사유": "", "시도횟수": 0,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    # 이미 제대로 받아 둔 것은 다시 받지 않는다(쿼터가 아니라 예의의 문제다).
    if os.path.exists(meta_p):
        try:
            old = json.load(open(meta_p, encoding="utf-8"))
            if old.get("성공") == "Y" and os.path.exists(dest):
                if verbose:
                    print("    %-16s %-52s 이미 보유" % (corp, name[:52]))
                return old
        except (OSError, ValueError):
            pass

    last = ""
    for attempt in range(1, ATTEMPTS + 1):
        rec["시도횟수"] = attempt
        try:
            if method == "POST":
                # 게시글을 먼저 연다 — 쿠키·Referer 를 요구하는 서버가 있다.
                try:
                    opener.open(_req(page), timeout=TIMEOUT).read(1 << 16)
                except urllib.error.URLError as e:
                    last = "게시글 열기 실패: %s" % e
                time.sleep(DELAY)
                body = urllib.parse.urlencode({"real_filename": real,
                                               "filename": name}).encode()
                resp = opener.open(_req(url, referer=page, data=body), timeout=TIMEOUT)
            else:
                # 하나금융지주는 목록 URL 에 :8002 가 붙어 있는데 이 환경의 릴레이가
                # 비표준 포트 터널을 끊는다(프록시 로그: ws_closed_mid_exchange,
                # host www.hanafn.com:8002). **포트를 떼면 443 에서 같은 경로가
                # 그대로 응답한다**(실측 HTTP 200, 10,125,304 bytes). 그래서 원래
                # URL 을 먼저 시도하고, 실패하면 포트를 뗀 URL 로 한 번 더 시도한다.
                # 어느 쪽으로 받았는지는 실제url 에 적는다 — 목록과 다르면 알아야 한다.
                cands = [url]
                pr = urllib.parse.urlparse(url)
                if pr.port:
                    cands.append(urllib.parse.urlunparse(
                        pr._replace(netloc=pr.hostname)))
                resp, err = None, ""
                for cu in cands:
                    ref = "https://%s/" % urllib.parse.urlparse(cu).netloc
                    try:
                        resp = opener.open(_req(cu, referer=ref), timeout=TIMEOUT)
                        rec["실제url"] = cu
                        break
                    except Exception as ex:      # noqa: BLE001
                        err = "%s: %s" % (type(ex).__name__, ex)
                if resp is None:
                    raise urllib.error.URLError(err)

            rec["http_status"] = str(getattr(resp, "status", "") or resp.getcode())
            rec["content_type"] = resp.headers.get("Content-Type", "")
            tmp = dest + ".part"
            total = 0
            with open(tmp, "wb") as f:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
            resp.close()
            ok, why = _sig_ok(tmp, name)
            if not ok:
                os.remove(tmp)
                last = why
                raise ValueError(why)
            os.replace(tmp, dest)
            rec["실제크기"] = str(total)
            rec["sha256"] = _sha256(dest)
            rec["성공"] = "Y"
            rec["실패사유"] = ""
            break
        except Exception as e:                      # noqa: BLE001 — 사유를 남기고 재시도
            last = last or "%s: %s" % (type(e).__name__, e)
            rec["실패사유"] = last
            if attempt < ATTEMPTS:
                time.sleep(DELAY * attempt * 2)
            last = ""

    # 목록 크기와 실제 크기 대조. 보정하지 않고 사실만 적는다.
    rec["크기차이"] = ""
    if rec["성공"] == "Y" and rec["목록크기"].isdigit() and rec["실제크기"].isdigit():
        exp, got = int(rec["목록크기"]), int(rec["실제크기"])
        if exp and abs(got - exp) > max(1024, exp * 0.02):
            rec["크기차이"] = "목록 %d ≠ 실제 %d (%+d)" % (exp, got, got - exp)

    with open(meta_p, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    if verbose:
        print("    %-16s %-52s %s %s%s"
              % (corp, name[:52], rec["방식"],
                 "OK %s bytes" % rec["실제크기"] if rec["성공"] == "Y"
                 else "실패(%d회): %s" % (rec["시도횟수"], rec["실패사유"][:70]),
                 ("  [" + rec["크기차이"] + "]") if rec.get("크기차이") else ""))
    return rec


def run(out_dir=DEFAULT_OUT, only=None, dry_run=False, verbose=True):
    rows = load_list()
    if only:
        keep = {s.strip() for s in only}
        rows = [r for r in rows if (r.get("지주명") or "").strip() in keep]
    if dry_run:
        import collections
        by = collections.Counter()
        for r in rows:
            m, u, _p, _f = classify(r)
            by[(m, urllib.parse.urlparse(u).netloc)] += 1
        print("  대상 %d건" % len(rows))
        for k in sorted(by):
            print("    %-9s %-32s %d" % (k[0], k[1], by[k]))
        print("  공시유형:", dict(__import__("collections").Counter(
            disclosure_type(r) for r in rows)))
        return []
    opener, _jar = make_opener()
    out = []
    for i, r in enumerate(rows):
        out.append(fetch_one(opener, r, out_dir, verbose))
        if i + 1 < len(rows):
            time.sleep(DELAY)
    ok = sum(1 for r in out if r.get("성공") == "Y")
    if verbose:
        print("  수집 완료: 성공 %d / 실패 %d" % (ok, len(out) - ok))
    return out


def main(argv=None):
    _ensure_legacy_tls()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    run(a.out, [s for s in a.only.split(",") if s.strip()] or None, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
