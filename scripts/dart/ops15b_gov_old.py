# -*- coding: utf-8 -*-
"""15차 확장(gov_old) — 지배구조 연차보고서 웹 수집: 옛 해(KB FY2014~FY2018, 신한·하나·BNK FY2017·FY2018,
iM(옛 DGB) FY2018)와 FY2024·FY2025 10개사 PDF 다시 받기(handoff/연차보고서_파일목록.csv 의 URL, sha256 대조).

    python3 -I scripts/dart/ops15b_gov_old.py robots      # 호스트마다 robots.txt 다시 판정 → _work/robots.json
    python3 -I scripts/dart/ops15b_gov_old.py terms       # 첫 화면을 받아 약관·저작권 링크 글을 찾음 → _work/terms.json
    python3 -I scripts/dart/ops15b_gov_old.py lists       # 게시판 목록을 받아 받을 파일 → _work/targets.json
    python3 -I scripts/dart/ops15b_gov_old.py download    # 받기(이미 받은 칸은 건너뜀) → _work/download.json
    python3 -I scripts/dart/ops15b_gov_old.py kbfix       # KB 옛 해 6바이트 칸 → 게시판 boardFileDownload() 주소로(그 뒤 download KB금융지주)
    python3 -I scripts/dart/ops15b_gov_old.py dates       # FY2024·FY2025 행의 게시일(게시판 목록의 같은 제목 글) → _work/dates.json
    python3 -I scripts/dart/ops15b_gov_old.py text        # PDF → 「## p.N」 md(venv pymupdf 를 하위 프로세스로)
    python3 -I scripts/dart/ops15b_gov_old.py csv         # dart_out/ops15/문서목록15b_gov_old.csv
    <venv python> -I scripts/dart/ops15b_gov_old.py pdf2md <pdf> <md> <머리줄>   # (text 가 부름)

규칙
- HTTP 는 scripts/dart/web13.py 의 Web(=web9.Web: UA 고정 「lastprice-research/1.0 …」, 요청 사이 1.2초, 한 요청 3번까지
  = 같은 파일 재시도 2회)과 web10.Robots(RFC 9309: 2xx 규칙대로, 4xx = 제한 없음, 429·5xx·접속 실패 = 받지 않음)를 쓰고,
  저장 위치만 dart_out/raw/ops15b/gov_old/<회사>/ 로 바꾼다. UA 위장·다른 호스트·캐시·미러·검색엔진 캐시 쓰지 않음.
- NH농협금융지주(www.nhfngroup.com)는 2026-11-02 에 모든 요청이 HTTP 400 — 이번에는 robots·첫 화면·파일 URL 을 각 1번만(재시도 없음).
- 우리금융지주 서버는 OpenSSL 3 이 기본으로 막는 legacy renegotiation 서버라 15차 mgmt 와 같은 OPENSSL_CONF
  (UnsafeLegacyRenegotiation, SECLEVEL=1 — 인증서 검증은 그대로)로 한 번 재실행한다 — 「--legacy 우리금융지주」 로 따로 돌림
  (이 설정을 모든 호스트에 쓰면 www.imfngroup.com 접속이 끊김, 2026-11-03 실측).
- 회사 이름을 인자로 주면 그 회사만(robots·terms·download).
- 하나금융지주: handoff 목록 URL 은 https://www.hanafn.com:8002/… — :8002 의 robots.txt 를 판정할 수 없으면(접속 실패) :8002 에서는
  받지 않고, 지금 게시판(https://www.hanafn.com/governance/disclosure.do) 글에 걸린 링크(상대경로 /download/…, 게시판 쪽 기준 443)로 받음 (판단).
- 공시유형은 게시글 제목 낱말로 기계적으로: 「재공시」→재공시, 「정정」→정정공시, 「수정」→수정공시, 「추가」→추가공시, 그 밖 본공시.
- FY = 보고서 대상 연도(제목의 「20xx년」), 공시연도 = FY+1.
- 글자층 판정(pdf2md): 글자 없는 쪽 수, 한글 글자 수·서로 다른 한글 수, 「이사회」 횟수, U+FFFD·사용자 영역 글자 수를 셈.
  실패 = 글자 있는 쪽 0 / 글자 없는 쪽이 절반 넘음 / 「이사회」·「보수」·「지배구조」·「위원회」 모두 0회 / 깨진 글자 비율 5% 넘음 /
  50쪽 넘는 문서에 서로 다른 한글이 300자 미만(15차 JB FY2019 같은 글꼴 대응 깨짐) (기계 기준, 그림으로 읽지 않음).
API 키 쓰지 않음.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HERE = os.path.join(ROOT, "scripts", "dart")
os.chdir(ROOT)
RAW = os.path.join("dart_out", "raw", "ops15b", "gov_old")
WORK = os.path.join(RAW, "_work")
TXT = os.path.join("dart_out", "text", "ops15b")
LIST = os.path.join("dart_out", "ops15", "문서목록15b_gov_old.csv")
HANDOFF_LIST = os.path.join("handoff", "연차보고서_파일목록.csv")
REUSE = "--reuse" in sys.argv
VENV = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python"

HOSTS = {
    "KB금융지주": ["https://www.kbfg.com"],
    "신한금융지주": ["https://www.shinhangroup.com"],
    "하나금융지주": ["https://www.hanafn.com", "https://www.hanafn.com:8002"],
    "우리금융지주": ["https://www.woorifg.com"],
    "NH농협금융지주": ["https://www.nhfngroup.com"],
    "메리츠금융지주": ["https://www.meritzgroup.com"],
    "iM금융지주": ["https://www.imfngroup.com"],
    "BNK금융지주": ["https://www.bnkfg.com"],
    "JB금융지주": ["https://www.jbfg.com"],
    "한국투자금융지주": ["https://www.koreaholdings.com"],
}
HOME = {
    "KB금융지주": "https://www.kbfg.com/kor/index.jsp",
    "신한금융지주": "https://www.shinhangroup.com/kr/main",
    "하나금융지주": "https://www.hanafn.com/main/index.do",
    "우리금융지주": "https://www.woorifg.com/kor/main/index.do",
    "NH농협금융지주": "https://www.nhfngroup.com/",
    "메리츠금융지주": "https://www.meritzgroup.com/web/ko/main/main.do",
    "iM금융지주": "https://www.imfngroup.com/",
    "BNK금융지주": "https://www.bnkfg.com/main/main.jsp",
    "JB금융지주": "https://www.jbfg.com/",
    "한국투자금융지주": "https://www.koreaholdings.com/",
}
BOARD = {
    "KB금융지주": "https://www.kbfg.com/kor/about/governance/board-directors/list.htm",
    "신한금융지주": "https://www.shinhangroup.com/kr/governance/director/disclosure",
    "하나금융지주": "https://www.hanafn.com/governance/disclosure.do",
    "우리금융지주": "https://www.woorifg.com/kor/corp-governance/governance-structure/list.do",
    "NH농협금융지주": "https://www.nhfngroup.com/user/indexSub.do?codyMenuSeq=1218157519&siteId=nhfngroup",
    "메리츠금융지주": "https://www.meritzgroup.com/web/ko/group/group4_7.do",
    "iM금융지주": "https://www.imfngroup.com/ir0204.fg",
    "BNK금융지주": "https://www.bnkfg.com/01/0607.jsp",
    "JB금융지주": "https://www.jbfg.com/ko/governance/disclosure.do",
    "한국투자금융지주": "https://www.koreaholdings.com/kr/bbs/disclosure/list?lang=kr&bcode=disclosure",
}
# 옛 해 대상 칸(회사, FY)
OLD = [("KB금융지주", fy) for fy in range(2014, 2019)] + [
    ("신한금융지주", 2017), ("신한금융지주", 2018), ("하나금융지주", 2017), ("하나금융지주", 2018),
    ("BNK금융지주", 2017), ("BNK금융지주", 2018), ("iM금융지주", 2018)]

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
    """「--legacy」 를 준 실행(우리금융지주만)에서만 OPENSSL_CONF 로 재실행 — 다른 호스트(iM 등)는 이 설정에서 접속이 끊김."""
    if "--legacy" not in sys.argv or os.environ.get("GOVOLD15B_TLS_READY") == "1":
        return
    os.makedirs(WORK, exist_ok=True)
    cnf = os.path.join(WORK, "legacy_openssl.cnf")
    with open(cnf, "w", encoding="utf-8") as f:
        f.write(_LEGACY_CNF)
    env = dict(os.environ, OPENSSL_CONF=os.path.abspath(cnf), GOVOLD15B_TLS_READY="1")
    os.execve(sys.executable, [sys.executable, "-I", os.path.abspath(__file__)] + sys.argv[1:], env)


def net():
    _ensure_legacy_tls()
    sys.path.insert(0, HERE)
    import web10  # noqa: F401
    import web13  # noqa: F401
    return web10, web13


def now():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def jdump(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".part", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(p + ".part", p)


def save(co, name, body, meta):
    """원본 바이트를 dart_out/raw/ops15b/gov_old/<co>/<name> 에, 메타는 같은 이름 + .meta.json."""
    p = os.path.join(RAW, co, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


# ---------------------------------------------------------------- HTTP
_W = {}


def web(co):
    """NH 는 재시도 없는 1번 요청(Once), 나머지는 web9.Web(3번까지)."""
    _, web13 = net()
    key = "once" if co == "NH농협금융지주" else "web"
    if key not in _W:
        if key == "once":
            class Once(web13.Web):
                def get(self, url, referer="", data=None, headers=None):
                    import time
                    import urllib.request
                    h = {"User-Agent": web13.UA, "Accept": "*/*", "Accept-Language": "ko,en;q=0.8"}
                    if referer:
                        h["Referer"] = referer
                    h.update(headers or {})
                    wait = 1.2 - (time.time() - self.last)
                    if wait > 0:
                        time.sleep(wait)
                    try:
                        r = self.op.open(urllib.request.Request(url, data=data, headers=h), timeout=60)
                        return r.geturl(), r.status, dict(r.headers.items()), r.read()
                    finally:
                        self.last = time.time()
            _W[key] = Once()
        else:
            _W[key] = web13.Web()
    return _W[key]


_ROB = {}


def robots_for(co, url):
    web10, _ = net()
    pu = urllib.parse.urlparse(url)
    base = "%s://%s" % (pu.scheme, pu.netloc)
    if base not in _ROB:
        class R(web10.Robots):
            pass
        _save = web10.save
        web10.save = save
        try:
            _ROB[base] = R(web(co), base, co)
        finally:
            web10.save = _save
        _ROB[base].checked_at = now()
    return _ROB[base]


def fetch(co, url, name, referer="", data=None, headers=None, extra=None):
    """robots 허용일 때만 받아 저장. 「--reuse」 실행이면 이미 저장한 같은 이름 파일을 그대로 씀(목록 다시 만들기용)."""
    p0 = os.path.join(RAW, co, name)
    if REUSE and os.path.exists(p0) and os.path.exists(p0 + ".meta.json"):
        return p0, jload(p0 + ".meta.json")
    r = robots_for(co, url)
    if not r.allowed(url):
        raise PermissionError("robots 불허(%s): %s" % (r.status, url))
    if isinstance(data, str):
        data = data.encode()
        headers = dict(headers or {}, **{"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    fu, st, hd, b = web(co).get(url, referer=referer, data=data, headers=headers)
    meta = dict(url=url, 최종URL=fu, http=st, content_type=hd.get("Content-Type", ""),
                content_disposition=hd.get("Content-Disposition", ""), referer=referer,
                post=(data.decode("utf-8", "replace") if isinstance(data, bytes) else (data or "")),
                fetched_at=now(), robots=r.status)
    meta.update(extra or {})
    return save(co, name, b, meta)


# ---------------------------------------------------------------- robots / terms
def robots_all(cos=None):
    out = jload(os.path.join(WORK, "robots.json"), {})
    for co, bases in HOSTS.items():
        if cos and co not in cos:
            continue
        for b in bases:
            r = robots_for(co, b + "/")
            host = urllib.parse.urlparse(b).netloc
            out[host] = dict(co=co, base=b, status=r.status, note=r.note, checked_at=r.checked_at)
            print(co, host, r.status, r.note[:100])
    prev = jload(os.path.join("dart_out", "raw", "governance15", "robots_판정.json"), {})
    out["_2026-11-02_governance15"] = prev
    jdump(os.path.join(WORK, "robots.json"), out)


TERM_RE = re.compile(r"<a\b[^>]*>(?:(?!</a>).){0,300}?(약관|저작권|무단|수집|법적고지|이용정책|크롤)(?:(?!</a>).){0,300}?</a>", re.S)


def terms_all(cos=None):
    out = jload(os.path.join(WORK, "terms.json"), {})
    for co, url in HOME.items():
        if cos and co not in cos:
            continue
        if co in out and out[co].get("http"):
            continue
        rec = dict(url=url, fetched_at=now())
        try:
            p, m = fetch(co, url, os.path.join("_pages", "home.html"))
            s = open(p, encoding="utf-8", errors="replace").read()
            links = []
            for mm in TERM_RE.finditer(s):
                a = mm.group(0)
                href = re.search(r'href="([^"]*)"', a)
                txt = html.unescape(re.sub(r"<[^>]+>|\s+", " ", a)).strip()
                links.append((txt[:60], href.group(1)[:150] if href else ""))
            words = {w: len(re.findall(w, s)) for w in ("이용약관", "저작권", "무단", "자동", "수집", "크롤", "robot")}
            rec.update(http=m["http"], 최종URL=m["최종URL"], 바이트=m["바이트"], links=links[:15], words=words, 저장경로=p)
        except Exception as e:                       # noqa: BLE001
            rec.update(http="", error="%s %s" % (type(e).__name__, str(e)[:200]))
        out[co] = rec
        jdump(os.path.join(WORK, "terms.json"), out)
        print(co, rec.get("http"), rec.get("error", "")[:80], rec.get("words"), rec.get("links", [])[:6])


# ---------------------------------------------------------------- 목록
def kind_of(title):
    t = title or ""
    if "재공시" in t:
        return "재공시"
    if "정정" in t:
        return "정정공시"
    if "수정" in t:
        return "수정공시"
    if "추가" in t:
        return "추가공시"
    return "본공시"


def fy_of(title):
    m = re.search(r"(20\d\d)\s*년", title or "") or re.search(r"(20\d\d)", title or "")
    return int(m.group(1)) if m else None


def _strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def is_annual(t):
    return "연차보고서" in (t or "") or ("지배구조" in (t or "") and "연차" in (t or ""))


def list_kb():
    co, board = "KB금융지주", BOARD["KB금융지주"]
    posts, page, total = [], 1, 1
    while page <= total:
        url = "https://www.kbfg.com/api/kbfg/posts?bulbdId=6&page=%d&pageSize=10" % page
        p, m = fetch(co, url, os.path.join("_pages", "kb_posts_b6_p%d.json" % page), referer=board)
        d = json.load(open(p, encoding="utf-8"))["result"]
        total = d["paging"]["totalPageCount"]
        for x in d["posts"]:
            posts.append(dict(x, _list_url=url, _list_fetched_at=m["fetched_at"]))
        page += 1
    T = []
    for x in posts:
        t = x["titl"]
        if not is_annual(t):
            continue
        fy = fy_of(t)
        if fy is None or not 2014 <= fy <= 2018:
            continue
        for f in x.get("files") or []:
            if f.get("dataTyp") == "migration":
                url = "https://www.kbfg.com/common/jsp/fileDownUtil.jsp?filepath=" + urllib.parse.quote(f["fileNm"])
            else:
                url = "https://www.kbfg.com/api/download/board/%s" % f["fileId"]
            T.append(dict(회사=co, fy=fy, 공시유형=kind_of(t), 구분="", 제목=t, board_url=board, 게시글="bltcId=%s" % x["bltcId"],
                          파일_url=url, method="GET", post="", referer=board, 공시일=x["rgcrYms"][:10],
                          목록_파일명=f.get("orglFileNm") or "", 목록_url=x["_list_url"], 목록_fetched_at=x["_list_fetched_at"]))
    jdump(os.path.join(WORK, "list_kb_all.json"), [dict(bltcId=x["bltcId"], titl=x["titl"], rgcrYms=x["rgcrYms"]) for x in posts])
    print(co, "게시글", len(posts), "대상 파일", len(T))
    return T


def list_sh():
    co, board = "신한금융지주", BOARD["신한금융지주"]
    api = "https://www.shinhangroup.com/api/v1/governance/council_disclosure/list"
    T, allp = [], []
    for y in (2015, 2016, 2017, 2018, 2019):
        page, last = 1, 1
        while page <= last:
            body = {"pageType": "FRONT", "lang": "KOR", "current": str(page), "year": str(y)}
            p, m = fetch(co, api, os.path.join("_pages", "sh_council_%d_p%d.json" % (y, page)), referer=board,
                         data=urllib.parse.urlencode(body))
            d = json.load(open(p, encoding="utf-8"))["result"]
            last = d.get("last") or 1
            for x in d["list"]:
                t = x.get("title") or ""
                allp.append(dict(year=y, title=t, baseDt=x.get("baseDt")))
                if not is_annual(t):
                    continue
                fy = fy_of(t)
                if fy not in (2017, 2018):
                    continue
                for f in x.get("fileList") or []:
                    T.append(dict(회사=co, fy=fy, 공시유형=kind_of(t), 구분="", 제목=t, board_url=board, 게시글="year=%d" % y,
                                  파일_url="https://www.shinhangroup.com/main/downloadAttach?attachNo=%s&seq=%s" % (f["attachNo"], f["fileSeq"]),
                                  method="GET", post="", referer=board, 공시일=(x.get("baseDt") or "").replace(".", "-"),
                                  목록_파일명=f.get("originalFileName") or "",
                                  목록_url=api + " (POST %s)" % urllib.parse.urlencode(body), 목록_fetched_at=m["fetched_at"]))
            page += 1
    jdump(os.path.join(WORK, "list_sh_all.json"), allp)
    print(co, "게시글", len(allp), "대상 파일", len(T))
    return T


def list_hana(stop_before="2018.01.01", maxpage=40):
    co, board = "하나금융지주", BOARD["하나금융지주"]
    out = []
    for page in range(1, maxpage + 1):
        body = {"pageNo": str(page)}
        p, m = fetch(co, board, os.path.join("_pages", "hana_disclosure_p%d.html" % page), referer=board,
                     data=urllib.parse.urlencode(body))
        h = open(p, encoding="utf-8", errors="replace").read()
        got = 0
        for r in re.findall(r'<li role="row">(.*?)</li>', h, re.S):
            c = {k: v for k, v in re.findall(r'<div role="cell" class="([^"]*)">(.*?)</div>', r, re.S)}
            title = _strip(c.get("left title", ""))
            if not title:
                continue
            got += 1
            out.append(dict(num=_strip(c.get("hide", "")), title=title, date=_strip(c.get("sub", "")),
                            file_urls=re.findall(r"downloadFile\('([^']+)'\)", r),
                            file_titles=re.findall(r'download title="([^"]*)"', r),
                            list_post="pageNo=%d" % page, list_fetched_at=m["fetched_at"]))
        if not got or (out and out[-1]["date"] and out[-1]["date"] < stop_before):
            break
    jdump(os.path.join(WORK, "list_hana_all.json"), out)
    T = []
    for x in out:
        t = x["title"]
        if not is_annual(t):
            continue
        fy = fy_of(t)
        for u, fn in zip(x["file_urls"], x["file_titles"] or [""] * len(x["file_urls"])):
            T.append(dict(회사=co, fy=fy, 공시유형=kind_of(t), 구분="", 제목=t, board_url=board, 게시글="num=%s" % x["num"],
                          파일_url=urllib.parse.urljoin(board, u), method="GET", post="", referer=board,
                          공시일=x["date"].replace(".", "-"), 목록_파일명=fn,
                          목록_url=board + " (POST %s)" % x["list_post"], 목록_fetched_at=x["list_fetched_at"],
                          _board_link=u))
    print(co, "게시글", len(out), "연차보고서 파일", len(T), "마지막 날짜", out[-1]["date"] if out else "")
    return T


def list_bnk(maxpage=12):
    co = "BNK금융지주"
    seen, allp, T = set(), [], []
    for p in range(1, maxpage + 1):
        url = "https://www.bnkfg.com/01/0607.jsp?dataPageNo=%d&dataWhere=" % p
        path, m = fetch(co, url, os.path.join("_pages", "0607_p%d.html" % p), referer=BOARD[co])
        s = open(path, encoding="utf-8", errors="replace").read()
        got = 0
        for mm in re.finditer(r'<tr>\s*<td>(\d+)</td>\s*<td class="subject"><a href="([^"]+)"[^>]*>(.*?)</a></td>\s*<td>(.*?)</td>\s*<td>([^<]*)</td>', s, re.S):
            no, href, t, fcell, dt = mm.groups()
            if no in seen:
                continue
            seen.add(no)
            got += 1
            t = html.unescape(t).strip()
            allp.append(dict(no=no, title=t, date=dt, href=href, page=p))
            if not is_annual(t):
                continue
            fy = fy_of(t)
            if fy not in (2017, 2018):
                continue
            alt = re.findall(r'alt="([^"]*)"', fcell)
            T.append(dict(회사=co, fy=fy, 공시유형=kind_of(t), 구분=("보수체계" if "보수체계 연차" in t and "지배구조" not in t else ""),
                          제목=t, board_url=url, 게시글="no=%s" % no, 파일_url=urllib.parse.urljoin(url, href), method="GET",
                          post="", referer=url, 공시일=dt.replace(".", "-"),
                          목록_파일명=(alt[0].replace(" 다운로드 받기", "") if alt else ""), 목록_url=url, 목록_fetched_at=m["fetched_at"]))
        if not got:
            break
    jdump(os.path.join(WORK, "list_bnk_all.json"), allp)
    print(co, "게시글", len(allp), "대상 파일", len(T))
    return T


IM_POST = ("IN_DATA_JSON=%257B%2522bbs_no%2522%253A%252217%2522%252C%2522col_nm%2522%253A%2522putup_writ_tit_nm%2522%252C"
           "%2522col_val%2522%253A%2522%2522%252C%2522in_table_page%2522%253A%257B%2522in_table_paging%2522%253Atrue%252C"
           "%2522in_table_pageSize%2522%253A200%252C%2522in_table_pageNo%2522%253A1%257D%257D")


def list_im():
    co, board = "iM금융지주", BOARD["iM금융지주"]
    url = "https://www.imfngroup.com/nbbsR1.fg"
    p, m = fetch(co, url, os.path.join("_pages", "nbbsR1_bbs17_all.json"), referer=board, data=IM_POST)
    d = json.load(open(p, encoding="utf-8"))
    T = []
    for r in d["OUT_DATA"]:
        t = html.unescape(r["PUTUP_WRIT_TIT_NM"])
        if not is_annual(t):
            continue
        fy = fy_of(t)
        if fy != 2018:
            continue
        T.append(dict(회사=co, fy=fy, 공시유형=kind_of(t), 구분="", 제목=t, board_url=board + " (목록 POST /nbbsR1.fg BBS_NO=17)",
                      게시글="putup_writ_seq=%s" % r["PUTUP_WRIT_SEQ"],
                      파일_url="https://www.imfngroup.com/nbbsR3.fg?putup_writ_seq=%s&file_seq=%s" % (r["PUTUP_WRIT_SEQ"], r["FILE_SEQ"]),
                      method="GET", post="", referer=board, 공시일="%s-%s-%s" % (r["RGDT"][:4], r["RGDT"][4:6], r["RGDT"][6:]),
                      목록_파일명=r["ATC_FILE_NM"], 목록_url=url + " (POST IN_DATA_JSON bbs_no=17 pageSize=200)",
                      목록_fetched_at=m["fetched_at"]))
    print(co, "게시글", len(d["OUT_DATA"]), "대상 파일", len(T))
    return T


def list_ki():
    """한국투자: 목록(keyword=연차보고서) → 공시일 2025·2026 글 read?seq → downloadFile('이름','real') (POST /common/fildDownload)."""
    co = "한국투자금융지주"
    url = ("https://www.koreaholdings.com/kr/bbs/disclosure/list?lang=kr&bcode=disclosure&key=&keyword=%s&cpage=1"
           % urllib.parse.quote("연차보고서"))
    p, m = fetch(co, url, os.path.join("_pages", "disclosure_q_p1.html"), referer=BOARD[co])
    s = open(p, encoding="utf-8", errors="replace").read()
    out = []
    for mm in re.finditer(r"<tr>(.*?)</tr>", s, re.S):
        row = mm.group(1)
        sq = re.findall(r"loadBbsView\('(\d+)'", row)
        if not sq:
            continue
        cells = [_strip(re.sub(r"\s+", " ", c)) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        title, dt = cells[1], cells[3]
        if dt[:4] not in ("2025", "2026"):
            continue
        rurl = "https://www.koreaholdings.com/kr/bbs/disclosure/read?seq=%s&lang=kr&bcode=disclosure" % sq[0]
        rp, rm = fetch(co, rurl, os.path.join("_pages", "read_%s.html" % sq[0]), referer=url)
        h = open(rp, encoding="utf-8", errors="replace").read()
        for fname, real in re.findall(r"downloadFile\('([^']*)','([^']*)'\)", h):
            out.append(dict(title=title, date=dt, seq=sq[0], read_url=rurl, filename=fname, real_filename=real,
                            fetched_at=rm["fetched_at"]))
    jdump(os.path.join(WORK, "list_ki_2025_2026.json"), out)
    print(co, "2025·2026 글 파일", len(out))
    return out


def new_targets(ki):
    """handoff/연차보고서_파일목록.csv 의 FY2024·FY2025(공시연도 2025·2026) PDF 행(구분 조직도 제외)."""
    T = []
    rows = list(csv.DictReader(open(HANDOFF_LIST, encoding="utf-8-sig")))
    for x in rows:
        if x["구분"] == "조직도" or x["공시연도"] not in ("2025", "2026"):
            continue
        co, py = x["지주명"], int(x["공시연도"])
        t = dict(회사=co, fy=py - 1, 공시유형=kind_of(x["제목"]), 구분=("보수체계" if x["구분"] == "보수체계" else ""),
                 제목=x["제목"], board_url=BOARD[co], 게시글="", 파일_url=x["url"], method="GET", post="", referer=BOARD[co],
                 공시일="", 목록_파일명=x["파일명"], 목록_url=HANDOFF_LIST, 목록_fetched_at=x["fetched_at"],
                 handoff_공시연도=x["공시연도"], handoff_공시유형=x["공시유형"], handoff_구분=x["구분"], handoff_방식=x["방식"],
                 handoff_sha256=x["sha256"], handoff_url=x["url"], handoff_크기=x["실제크기"], handoff_쪽수=x["페이지수"],
                 handoff_fetched_at=x["fetched_at"])
        if x["방식"] == "POST" and co == "한국투자금융지주":
            # 같은 공시연도·공시유형의 게시글(2025·2026 목록) 파일을 짝지음 — 제목이 같은 글
            cand = [k for k in ki if k["title"].replace(" ", "") == x["제목"].replace(" ", "")]
            if len(cand) == 1:
                k = cand[0]
                t.update(method="POST", post=urllib.parse.urlencode(dict(filename=k["filename"], real_filename=k["real_filename"])),
                         referer=k["read_url"], 게시글=k["read_url"], 공시일=k["date"], board_url=k["read_url"],
                         목록_파일명=k["filename"])
            else:
                t.update(method="POST?", 비고="게시판에서 같은 제목 글 %d건 — POST 값을 못 정함" % len(cand))
        T.append(t)
    return T


def lists():
    T = []
    for fn in (list_kb, list_sh, list_hana, list_bnk, list_im):
        try:
            T += [dict(t, kind="old") for t in fn() if t["fy"] in [fy for c, fy in OLD if c == t["회사"]]]
        except Exception as e:                       # noqa: BLE001
            print("목록 실패", fn.__name__, type(e).__name__, str(e)[:200])
            T.append(dict(kind="old_list_error", 회사=fn.__name__, error="%s %s" % (type(e).__name__, str(e)[:300])))
    try:
        ki = list_ki()
    except Exception as e:                           # noqa: BLE001
        print("목록 실패 list_ki", type(e).__name__, str(e)[:200])
        ki = []
    hana_new = jload(os.path.join(WORK, "list_hana_all.json"), [])
    for t in new_targets(ki):
        t["kind"] = "new"
        if t["회사"] == "하나금융지주":
            # 지금 게시판 글(제목 같음)의 링크 — :8002 에서 못 받을 때 씀
            c = [x for x in hana_new if x["title"].replace(" ", "") == t["제목"].replace(" ", "")]
            if len(c) == 1 and c[0]["file_urls"]:
                t["board_link"] = urllib.parse.urljoin(BOARD["하나금융지주"], c[0]["file_urls"][0])
                t["공시일"] = c[0]["date"].replace(".", "-")
                t["게시글"] = "num=%s" % c[0]["num"]
        T.append(t)
    jdump(os.path.join(WORK, "targets.json"), T)
    for t in T:
        if t.get("kind") == "old":
            print("old", t["회사"], t["fy"], t["공시유형"], t["공시일"], t["제목"][:50])


def _norm(t):
    return re.sub(r"\s+", "", html.unescape(t or ""))


def dates():
    """FY2024·FY2025 행의 공시일(게시일) — 게시판 목록에서 제목이 같은 글. → _work/dates.json {tkey: 「YYYY-MM-DD (목록 URL, 받은 시각)」}"""
    T = [t for t in jload(os.path.join(WORK, "targets.json"), []) if t.get("kind") == "new" and not t.get("공시일")]
    got = {}                                   # 회사 → [(제목, 날짜, 목록 URL, 받은 시각)]
    kb = jload(os.path.join(WORK, "list_kb_all.json"), [])
    got["KB금융지주"] = [(x["titl"], x["rgcrYms"][:10], "https://www.kbfg.com/api/kbfg/posts?bulbdId=6", "") for x in kb]
    got["BNK금융지주"] = [(x["title"], x["date"].replace(".", "-"), "https://www.bnkfg.com/01/0607.jsp?dataPageNo=%d&dataWhere=" % x["page"], "")
                         for x in jload(os.path.join(WORK, "list_bnk_all.json"), [])]
    d = jload(os.path.join(RAW, "iM금융지주", "_pages", "nbbsR1_bbs17_all.json"), {"OUT_DATA": []})
    got["iM금융지주"] = [(r["PUTUP_WRIT_TIT_NM"], "%s-%s-%s" % (r["RGDT"][:4], r["RGDT"][4:6], r["RGDT"][6:]),
                         "https://www.imfngroup.com/nbbsR1.fg (POST BBS_NO=17)", "") for r in d["OUT_DATA"]]
    # 신한 2025·2026
    co, board = "신한금융지주", BOARD["신한금융지주"]
    api = "https://www.shinhangroup.com/api/v1/governance/council_disclosure/list"
    got[co] = []
    for y in (2025, 2026):
        page, last = 1, 1
        while page <= last:
            body = {"pageType": "FRONT", "lang": "KOR", "current": str(page), "year": str(y)}
            p, m = fetch(co, api, os.path.join("_pages", "sh_council_%d_p%d.json" % (y, page)), referer=board,
                         data=urllib.parse.urlencode(body))
            dd = json.load(open(p, encoding="utf-8"))["result"]
            last = dd.get("last") or 1
            got[co] += [(x.get("title") or "", (x.get("baseDt") or "").replace(".", "-"), api + " (POST year=%d current=%d)" % (y, page),
                         m["fetched_at"]) for x in dd["list"]]
            page += 1
    # 메리츠 gr_search GR002 1~2쪽
    co = "메리츠금융지주"
    got[co] = []
    for pg in range(1, 6):                          # 2024년 보고서(2025.3 게시)가 나올 때까지 5쪽까지
        p, m = fetch(co, "https://www.meritzgroup.com/web/gr_search.do", os.path.join("_pages", "gr_search_GR002_p%d.json" % pg),
                     referer=BOARD[co], data="bd_div_cd=GR002&currentPage=%d" % pg)
        rs = json.load(open(p, encoding="utf-8")).get("result", [])
        for r in rs:
            got[co].append((r.get("title_ko", ""), "20%s-%s-%s" % tuple(r["reg_ymd"].split(".")),
                            "https://www.meritzgroup.com/web/gr_search.do (POST bd_div_cd=GR002 currentPage=%d)" % pg, m["fetched_at"]))
        if not rs or any("2024년 지배구조" in (r.get("title_ko") or "") for r in rs):
            break
    # JB 2025·2026
    co = "JB금융지주"
    got[co] = []
    for y in (2025, 2026):
        url = "https://www.jbfg.com/ko/governance/disclosure.do?postStartDateYMD=%d&searchText=%s" % (y, urllib.parse.quote("연차"))
        p, m = fetch(co, url, os.path.join("_pages", "disclosure_%d.html" % y), referer=BOARD[co])
        sx = open(p, encoding="utf-8", errors="replace").read()
        for mm in re.finditer(r'<tr>\s*<td class="__title">(.*?)</tr>', sx, re.S):
            row = mm.group(1)
            tt = re.findall(r'detail/(\d+)\.do"[^>]*>(.*?)</a>', row)
            dt = re.findall(r'class="__date"[^>]*>\s*<small>(.*?)</small>', row, re.S)
            if tt and dt:
                got[co].append((_strip(tt[0][1]), dt[0].strip().replace(".", "-"), url, m["fetched_at"]))
    # 우리 1~2쪽
    co = "우리금융지주"
    got[co] = []
    try:
        for pg in (1, 2):
            url = BOARD[co] + "?pageIndex=%d&f=&q=" % pg
            p, m = fetch(co, url, os.path.join("_pages", "woori_gov_list_p%d.html" % pg), referer=BOARD[co])
            sx = open(p, encoding="utf-8", errors="replace").read()
            for b in sx.split('<div class="list">')[1:]:
                tt = re.search(r'<a href="\./view\.do\?seq=(\d+)[^"]*">(.*?)</a>', b, re.S)
                dt = re.search(r'<div class="date[^"]*">\s*([0-9.]+)\s*</div>', b)
                if tt and dt:
                    got[co].append((_strip(tt.group(2)), dt.group(1).replace(".", "-"), url, m["fetched_at"]))
    except Exception as e:                           # noqa: BLE001
        print("우리 목록 실패(--legacy 로 따로)", type(e).__name__, str(e)[:120])
    out = jload(os.path.join(WORK, "dates.json"), {}) or {}
    for t in T:
        c = [g for g in got.get(t["회사"], []) if _norm(g[0]) == _norm(t["제목"])]
        if len(c) >= 1:
            out[tkey(t)] = c[0][1]
            out[tkey(t) + "|src"] = "게시판 목록 %s 의 같은 제목 글%s" % (c[0][2], (" (받은 시각 %s)" % c[0][3]) if c[0][3] else "")
        print(tkey(t), out.get(tkey(t), "못 찾음"), len(c))
    jdump(os.path.join(WORK, "dates.json"), out)


# ---------------------------------------------------------------- 받기
def _safe(name):
    name = name.replace("/", "_").replace("\\", "_").replace("\x00", "").strip()
    name = re.sub(r'[<>:"|?*\r\n\t]', "_", name)
    return name[:150] or "file.pdf"


def tkey(t):
    return "%s|FY%s|%s|%s" % (t["회사"], t["fy"], t["공시유형"], t.get("구분", ""))


def download(only=None, cos=None):
    T = jload(os.path.join(WORK, "targets.json"), [])
    res = jload(os.path.join(WORK, "download.json"), {})
    for t in T:
        if t.get("kind") not in ("old", "new"):
            continue
        if only and t["kind"] != only:
            continue
        if cos and t["회사"] not in cos:
            continue
        k = tkey(t)
        prev = res.get(k) or {}
        if prev.get("저장경로") and os.path.exists(prev["저장경로"]) and not prev.get("실패사유"):
            continue
        if prev.get("받기횟수", 1 if prev else 0) >= 3 or (cos is None and prev.get("실패사유")):
            continue                                 # 같은 파일 재시도 2회까지 / 실패 칸 재시도는 회사를 콕 집어서만
        co = t["회사"]
        rec = dict(key=k, 시도=[], 저장경로="", sha256="", http="", fetched_at="", 실제_url="", 실패사유="",
                   받기횟수=prev.get("받기횟수", 1 if prev else 0) + 1, 이전=prev.get("이전", []) + ([dict(
                       (a, prev.get(a)) for a in ("http", "크기", "sha256", "fetched_at", "실제_url", "실패사유", "저장경로"))] if prev else []))
        urls = []
        if t["method"] == "POST?":
            rec["실패사유"] = t.get("비고", "")
        elif t.get("prefer_board_link") and t.get("board_link"):
            urls.append(t["board_link"])                 # kbfix: 게시판 쪽 boardFileDownload() 주소만(목록 경로는 이미 2번 6바이트)
        else:
            urls.append(t["파일_url"])
            if t.get("board_link") and t["board_link"] != t["파일_url"]:
                urls.append(t["board_link"])
            for u in list(urls):
                pu = urllib.parse.urlparse(u)
                if pu.port:      # 하나 :8002 — robots 판정 불가면 같은 호스트 443 의 같은 경로 (판단)
                    urls.append(urllib.parse.urlunparse(pu._replace(netloc=pu.hostname)))
        for u in urls:
            r = robots_for(co, u)
            if not r.allowed(u):
                rec["시도"].append("%s: robots %s — 받지 않음 (%s)" % (u, r.status, r.note[:150]))
                continue
            try:
                if t["method"] == "POST":
                    web(co).get(t["referer"])           # 게시글 먼저(쿠키)
                    fu, st, hd, b = web(co).get(u, referer=t["referer"], data=t["post"].encode(),
                                                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
                else:
                    fu, st, hd, b = web(co).get(u, referer=t["referer"])
            except Exception as e:                   # noqa: BLE001
                rec["시도"].append("%s: %s %s" % (u, type(e).__name__, str(e)[:150]))
                print(co, t["fy"], t["공시유형"], "ERR", type(e).__name__, str(e)[:100])
                continue
            name = "FY%s__%s%s__%s" % (t["fy"], t["공시유형"], ("__" + t["구분"]) if t.get("구분") else "",
                                       _safe(os.path.basename((t.get("목록_파일명") or "file.pdf").replace("\\", "/"))))
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            meta = dict(url=u, 목록_파일_url=t["파일_url"], method=t["method"], post=t["post"], 최종URL=fu, http=st,
                        content_type=hd.get("Content-Type", ""), content_disposition=hd.get("Content-Disposition", ""),
                        board_url=t["board_url"], 게시글=t["게시글"], 제목=t["제목"], fy=t["fy"], 공시유형=t["공시유형"],
                        공시일=t["공시일"], referer=t["referer"], robots=r.status, fetched_at=now())
            p, m = save(co, name, b, meta)
            rec.update(저장경로=p, sha256=m["sha256"], http=st, fetched_at=meta["fetched_at"], 실제_url=u, 크기=len(b),
                       content_type=meta["content_type"])
            if b[:4] != b"%PDF":
                rec["실패사유"] = "받은 내용이 PDF 가 아님(%s, %d bytes, 앞 %r)" % (meta["content_type"], len(b), b[:16])
            break
        if not rec["저장경로"] and not rec["실패사유"]:
            rec["실패사유"] = " / ".join(rec["시도"])
        res[k] = rec
        jdump(os.path.join(WORK, "download.json"), res)
        hs = t.get("handoff_sha256", "")
        print(k, rec["http"], rec.get("크기", ""), ("sha 같음" if hs and hs == rec["sha256"] else ("sha 다름" if hs and rec["sha256"] else "")),
              rec["실패사유"][:90])


# ---------------------------------------------------------------- 글
def md_path(t):
    suf = ""
    if t.get("구분"):
        suf = "__" + t["구분"] + t["공시유형"]
    elif t["공시유형"] != "본공시":
        suf = "__" + t["공시유형"]
    return os.path.join(TXT, "연차보고서__%s__FY%s%s.md" % (t["회사"], t["fy"], suf))


def text(cos=None):
    """받은 PDF → md. 결과(쪽·글자층 판정)는 _work/text.json(받기 기록과 따로 — 받기와 같이 돌아도 겹치지 않게)."""
    T = jload(os.path.join(WORK, "targets.json"), [])
    res = jload(os.path.join(WORK, "download.json"), {})
    tx = jload(os.path.join(WORK, "text.json"), {})
    os.makedirs(TXT, exist_ok=True)
    for t in T:
        k = tkey(t) if t.get("kind") in ("old", "new") else None
        if not k or (cos and t["회사"] not in cos):
            continue
        rec = res.get(k) or {}
        if not rec.get("저장경로") or rec.get("실패사유"):
            continue
        md = md_path(t)
        old = tx.get(k) or {}
        if old.get("md") == md and os.path.exists(md) and old.get("sha256") == rec["sha256"] and old.get("text_stats"):
            continue
        head = "%s FY%s %s%s · %s · %s · 받은 시각 %s · sha256 %s" % (
            t["회사"], t["fy"], t["공시유형"], (" " + t["구분"]) if t.get("구분") else "", t["제목"], rec["실제_url"],
            rec["fetched_at"], rec["sha256"])
        r = subprocess.run([VENV, "-I", os.path.abspath(__file__), "pdf2md", rec["저장경로"], md, head],
                           capture_output=True, text=True)
        out = dict(md=md, sha256=rec["sha256"])
        if r.returncode != 0:
            out["text_error"] = r.stderr.strip()[-300:]
            print(k, "글 실패", out["text_error"][-120:])
        else:
            out["text_stats"] = json.loads(r.stdout.strip().splitlines()[-1])
            print(k, out["text_stats"]["pages"], out["text_stats"]["verdict"], out["text_stats"]["reason"][:80])
        tx[k] = out
        jdump(os.path.join(WORK, "text.json"), tx)


def pdf2md(pdf, md, head):
    import pymupdf
    doc = pymupdf.open(pdf)
    empty, total, hang, bad = [], 0, 0, 0
    hs = set()
    board = core = 0
    with open(md + ".part", "w", encoding="utf-8") as f:
        f.write("# 연차보고서 쪽 텍스트 — %s\n\n원본: %s\n\n" % (head, pdf))
        for i, page in enumerate(doc, 1):
            t = page.get_text()
            if not t.strip():
                empty.append(i)
                f.write("## p.%d (글자 없음)\n\n" % i)
                continue
            f.write("## p.%d\n\n%s\n\n" % (i, t))
            for ch in t:
                if ch.isspace():
                    continue
                total += 1
                o = ord(ch)
                if 0xAC00 <= o <= 0xD7A3:
                    hang += 1
                    hs.add(ch)
                elif o == 0xFFFD or 0xE000 <= o <= 0xF8FF:
                    bad += 1
            board += t.count("이사회")
            core += sum(t.count(w) for w in ("이사회", "보수", "지배구조", "위원회"))
    os.replace(md + ".part", md)
    n = doc.page_count
    reason = []
    if n - len(empty) == 0:
        reason.append("글자 있는 쪽 0")
    if len(empty) > n / 2:
        reason.append("글자 없는 쪽 %d/%d" % (len(empty), n))
    if core == 0:
        reason.append("「이사회」·「보수」·「지배구조」·「위원회」 0회")
    if n > 50 and len(hs) < 300:
        reason.append("50쪽 넘는데 서로 다른 한글 %d자뿐" % len(hs))
    if total and bad / total > 0.05:
        reason.append("깨진 글자 비율 %.1f%%" % (100 * bad / total))
    st = dict(pages=n, empty_pages=empty, chars=total, hangul=hang, hangul_distinct=len(hs), bad_chars=bad,
              board_count=board, core_count=core, verdict=("실패" if reason else "글자층 있음"), reason="; ".join(reason))
    print(json.dumps(st, ensure_ascii=False))


# ---------------------------------------------------------------- 목록 CSV
COLS = ["doc_kind", "corp_label", "fy_or_date", "report_nm", "rcept_no_or_url", "rcept_dt", "raw_path", "sha256",
        "fetched_at", "text_path", "status", "note", "robots_verdict", "terms_note", "board_url"]


def main(argv):
    argv = [a for a in argv if a not in ("--legacy", "--reuse")]
    cmd = argv[1] if len(argv) > 1 else ""
    rest = argv[2:]
    only = [a for a in rest if a in ("old", "new")]
    cos = [a for a in rest if a in HOSTS] or None
    if cmd == "pdf2md":
        pdf2md(*argv[2:5])
        return 0
    if cmd == "robots":
        robots_all(cos)
    elif cmd == "terms":
        terms_all(cos)
    elif cmd == "lists":
        lists()
    elif cmd == "download":
        download(only[0] if only else None, cos)
    elif cmd == "text":
        text(cos)
    elif cmd == "dates":
        dates()
    elif cmd == "kbfix":
        kbfix()
    elif cmd == "csv":
        write_csv()
    else:
        print(__doc__)
        return 1
    return 0


def kbfix():
    """KB 옛 해: 목록 API 의 migration 경로(fileDownUtil.jsp)가 6바이트(PDF 아님)를 준 칸만, 게시판 쪽 스크립트
    boardFileDownload(fileId) 가 만드는 /api/download/board/<fileId>(같은 호스트)를 board_link 로 두고 그것만 받게 표시.
    fileId·fileSize 는 이미 저장한 목록 응답(_pages/kb_posts_b6_p*.json)의 그 글(bltcId) files[]."""
    import glob
    T = jload(os.path.join(WORK, "targets.json"), [])
    res = jload(os.path.join(WORK, "download.json"), {})
    files = {}
    for f in glob.glob(os.path.join(RAW, "KB금융지주", "_pages", "kb_posts_b6_p*.json")):
        if f.endswith(".meta.json"):
            continue
        for x in (json.load(open(f, encoding="utf-8")).get("result") or {}).get("posts", []):
            files[str(x["bltcId"])] = x.get("files") or []
    n = 0
    for t in T:
        if t.get("kind") != "old" or t["회사"] != "KB금융지주":
            continue
        rec = res.get(tkey(t)) or {}
        if not str(rec.get("실패사유", "")).startswith("받은 내용이 PDF 가 아님"):
            continue
        fl = [f for f in files.get(t["게시글"].split("=")[-1], []) if f.get("orglFileNm") == t["목록_파일명"]]
        if len(fl) != 1:
            print(tkey(t), "fileId 못 정함", len(fl))
            continue
        t.update(board_link="https://www.kbfg.com/api/download/board/%s" % fl[0]["fileId"], prefer_board_link=True,
                 kb_fileId=fl[0]["fileId"], kb_fileSize=fl[0].get("fileSize"))
        n += 1
        print(tkey(t), t["board_link"], fl[0].get("fileSize"))
    jdump(os.path.join(WORK, "targets.json"), T)
    print("kbfix", n)


def _robots_text(co, url):
    """그 URL 에 대한 robots 판정 글(이번 2026-11-03 판정 + 2026-11-02 판정)."""
    import urllib.robotparser
    sys.path.insert(0, HERE)
    from web9 import UA
    rob = jload(os.path.join(WORK, "robots.json"), {})
    prev = dict(jload(os.path.join("dart_out", "ops15", "gov15_g1_work", "robots.json"), {}))
    for c, v in (jload(os.path.join("dart_out", "raw", "governance15", "robots_판정.json"), {}) or {}).items():
        prev[urllib.parse.urlparse(v["base"]).netloc] = v
    host = urllib.parse.urlparse(url).netloc
    r = rob.get(host) or {}
    st = r.get("status", "판정 없음")
    if st == "OK":
        rp = urllib.robotparser.RobotFileParser()
        body = open(os.path.join(RAW, co, "robots_%s.txt" % host), encoding="utf-8", errors="replace").read()
        rp.parse(body.splitlines())
        ok = rp.can_fetch(UA, url)
        rules = sum(1 for ln in body.splitlines() if ln.strip().lower().startswith(("allow", "disallow")))
        t = "https://%s/robots.txt HTTP 200(%s) 규칙 %d줄 → 이 URL %s" % (host, r.get("checked_at", ""), rules, "허용(can_fetch)" if ok else "불허")
        if rules == 0:
            t += " — 본문이 robots 규칙이 아닌 HTML(meta refresh)이라 규칙 0개로 파싱, 제한 없음 (판단)"
    elif st.startswith("없음("):
        t = "https://%s/robots.txt %s(%s) → RFC 9309 §2.3.1.3 Unavailable, 제한 없음" % (host, st.replace("없음(", "").rstrip(")"), r.get("checked_at", ""))
    else:
        t = "https://%s/robots.txt %s(%s) %s → RFC 9309 §2.3.1.4 받지 않음" % (host, st, r.get("checked_at", ""), r.get("note", "")[:120])
    pv = prev.get(host)
    if pv:
        t += " / 2026-11-02 판정: %s" % pv.get("status", "")
    return t


def _terms_text(co):
    tm = (jload(os.path.join(WORK, "terms.json"), {}) or {}).get(co) or {}
    if not tm.get("http"):
        return "이용약관 확인 못 함 — 첫 화면 %s 요청 실패(%s)" % (tm.get("url", HOME[co]), tm.get("error", "요청 안 함"))
    s = open(tm["저장경로"], encoding="utf-8", errors="replace").read()
    pol = [w for w in ("개인정보처리방침", "고객정보취급방침", "신용정보활용체제", "공시정보관리지침", "이메일무단수집거부", "저작권정책",
                       "이용약관", "사이트맵") if w in s]
    w = tm.get("words", {})
    t = ("첫 화면 %s(HTTP %s, %s) 바닥글 정책 낱말: %s — 「이용약관」 %d회·「저작권」 %d회·「무단」 %d회·「크롤」 %d회"
         % (tm["url"], tm["http"], tm["fetched_at"], "·".join(pol) or "없음", w.get("이용약관", 0), w.get("저장권", w.get("저작권", 0)),
            w.get("무단", 0), w.get("크롤", 0)))
    t += TERMS_EXTRA.get(co, "") + " → 자동 수집 금지 문구 확인 안 됨, 수집 (판단)"
    return t


TERMS_EXTRA = {
    "하나금융지주": "(「이용약관」은 바닥글 선택 상자 이름, 안에는 개인정보처리방침·고객정보취급방침·신용정보활용체제뿐)",
    "메리츠금융지주": "(「자동」·「수집」 낱말은 설문 화면 스크립트 주석뿐)",
    "신한금융지주": "(「크롤」은 「스크롤」 주석)",
    "한국투자금융지주": "",
}


def write_csv():
    T = jload(os.path.join(WORK, "targets.json"), [])
    res = jload(os.path.join(WORK, "download.json"), {})
    dates = jload(os.path.join(WORK, "dates.json"), {}) or {}
    tx = jload(os.path.join(WORK, "text.json"), {}) or {}
    rows = []
    for t in T:
        if t.get("kind") not in ("old", "new"):
            continue
        co, k = t["회사"], tkey(t)
        rec = dict(res.get(k) or {})
        txr = (tx.get(k) or {}) if rec.get("sha256") and (tx.get(k) or {}).get("sha256") == rec.get("sha256") else {}
        rec.update({a: txr[a] for a in ("md", "text_stats", "text_error") if a in txr})
        url = rec.get("실제_url") or t["파일_url"]
        st = rec.get("text_stats") or {}
        notes = []
        if t["kind"] == "old":
            notes.append("옛 해 — 게시판 %s 글 %s, 목록 %s(받은 시각 %s)" % (t["board_url"], t["게시글"], t["목록_url"], t["목록_fetched_at"]))
        else:
            notes.append("FY2024·FY2025 다시 받기 — handoff/연차보고서_파일목록.csv 행(공시연도 %s·공시유형 %s·구분 %s·방식 %s)"
                         % (t["handoff_공시연도"], t["handoff_공시유형"], t["handoff_구분"], t["handoff_방식"]))
        status = "실패"
        if rec.get("저장경로") and not rec.get("실패사유"):
            status = "받음"
        if co == "NH농협금융지주" and not rec.get("저장경로"):
            status = "막힘"
        notes.append("공시유형 %s%s(게시글 제목 낱말로 기계적으로)" % (t["공시유형"], (" · 구분 " + t["구분"]) if t.get("구분") else ""))
        if rec.get("실패사유") and not t.get("prefer_board_link"):
            notes.append("실패: " + rec["실패사유"])
        if rec.get("시도") and not t.get("prefer_board_link") and rec.get("시도") != [rec.get("실패사유")]:
            notes.append("시도: " + " / ".join(rec["시도"]))
        if co == "NH농협금융지주" and status == "막힘":
            rb = (jload(os.path.join(WORK, "robots.json"), {}) or {}).get("www.nhfngroup.com", {})
            tm = (jload(os.path.join(WORK, "terms.json"), {}) or {}).get(co, {})
            notes.append("2026-11-02(15차)에도 www.nhfngroup.com 모든 요청 HTTP 400. 이번에 한 번만 다시 시도(재시도 없음): robots.txt %s(%s), "
                         "첫 화면 %s %s(%s), 이 파일 URL 1번 HTTP 400(2026-11-03 12:59:45~12:59:59 KST 사이 실행) — 막힘, 기록만(다른 호스트·캐시·미러 쓰지 않음)"
                         % (rb.get("status", ""), rb.get("checked_at", ""), tm.get("url", HOME[co]), tm.get("error", ""), tm.get("fetched_at", "")))
        if rec.get("받기횟수", 1) > 1 and not t.get("prefer_board_link"):
            notes.append("받기 %d번(재시도 %d번)" % (rec["받기횟수"], rec["받기횟수"] - 1))
        if t.get("handoff_sha256") and rec.get("sha256") and status == "받음":
            if rec["sha256"] == t["handoff_sha256"]:
                notes.append("sha256 이 handoff 목록과 같음(handoff 받은 때 %s)" % t["handoff_fetched_at"])
            else:
                notes.append("sha256 이 handoff 목록과 다름 — handoff %s(크기 %s, 쪽 %s, 받은 때 %s) / 이번 %s(크기 %s) — 둘 다 기록, 이번 파일 그대로 둠"
                             % (t["handoff_sha256"], t["handoff_크기"], t["handoff_쪽수"], t["handoff_fetched_at"], rec["sha256"], rec.get("크기")))
        if t.get("prefer_board_link"):
            prev_try = ["%s %sB(%s)" % (p.get("http"), p.get("크기"), p.get("fetched_at")) for p in rec.get("이전", []) if p.get("http")]
            notes.append("(판단) 게시판 글에 첨부(목록 API posts?bulbdId=6 의 files[]: %s, fileSize %s)가 있으나 — ① 목록의 migration 경로 %s "
                         "(fileDownUtil.jsp) 2번: %s — PDF 아님; ② 게시판 쪽(%s) 스크립트 boardFileDownload() 가 만드는 같은 호스트 주소 %s "
                         "1번(web9.Web 한 요청 안 3번 시도): %s. 요청 수 합 %d번 — 더 받지 않음"
                         % (t.get("목록_파일명", ""), t.get("kb_fileSize", ""), t["파일_url"], " / ".join(prev_try) or "기록 없음",
                            t["board_url"], t["board_link"],
                            ("HTTP %s %sB 받음" % (rec.get("http"), rec.get("크기"))) if rec.get("저장경로") and rec.get("실제_url") == t["board_link"]
                            else "; ".join(rec.get("시도", [])) or rec.get("실패사유", ""), len(prev_try) + 3))
            bad = [p.get("저장경로") for p in rec.get("이전", []) if p.get("저장경로")]
            if bad and not rec.get("저장경로"):
                notes.append("① 의 마지막 6바이트 응답은 %s 에 남겨 둠(이름은 .pdf 지만 PDF 아님 — 쓰지 말 것)" % bad[-1])
        elif rec.get("실제_url") and rec["실제_url"] != t["파일_url"]:
            notes.append("(판단) handoff 목록 URL·지금 게시판 글 링크(%s)는 모두 %s — 그 호스트:포트의 robots.txt 가 접속 끊김(이 환경 릴레이가 "
                         "비표준 포트 터널을 끊음)으로 판정할 수 없어 그 주소에서는 받지 않고, 같은 서버 443 의 같은 경로 %s(https://www.hanafn.com/robots.txt "
                         "HTTP 404 = 제한 없음)로 받음 — 15차 ops15_gov_g1 과 같은 처리"
                         % (t.get("게시글", ""), t["파일_url"], rec["실제_url"]))
        if st:
            notes.append("쪽 %d, 글자 없는 쪽 %s, 한글 %d자(서로 다른 %d자), 「이사회」 %d회, 깨진 글자 %d — 판정 %s%s"
                         % (st["pages"], (",".join(map(str, st["empty_pages"])) or "없음"), st["hangul"], st["hangul_distinct"],
                            st["board_count"], st["bad_chars"], st["verdict"], (" (" + st["reason"] + ")") if st["reason"] else ""))
            if t.get("handoff_쪽수") and str(st["pages"]) != str(t["handoff_쪽수"]):
                notes.append("쪽수가 handoff 목록(%s)과 다름" % t["handoff_쪽수"])
            if st["verdict"] == "실패":
                status = "실패"
                notes.append("글자층 실패 — 그림으로 읽지 않음")
        if rec.get("text_error"):
            status = "실패"
            notes.append("글 변환 실패: " + rec["text_error"][-200:])
        if t.get("구분"):
            notes.append("구분 %s(보수체계 연차보고서 단독 문서)" % t["구분"])
        notes += NOTE_EXTRA.get(k, [])
        post = (" (POST %s)" % urllib.parse.unquote_plus(t["post"])) if t.get("method") == "POST" else ""
        rows.append(dict(
            doc_kind="보수체계 연차보고서" if t.get("구분") == "보수체계" else "지배구조 연차보고서",
            corp_label=co, fy_or_date="FY%s" % t["fy"], report_nm=t["제목"], rcept_no_or_url=url + post,
            rcept_dt=t.get("공시일") or dates.get(k, ""), raw_path=(rec.get("저장경로", "") if status != "실패" or rec.get("text_stats") else rec.get("저장경로", "")),
            sha256=rec.get("sha256", ""), fetched_at=rec.get("fetched_at", ""),
            text_path=(rec.get("md", "") if rec.get("md") and os.path.exists(rec["md"]) else ""), status=status,
            note="; ".join(notes), robots_verdict=_robots_text(co, url), terms_note=_terms_text(co),
            board_url=t["board_url"]))
    rows += EXTRA_ROWS
    order = {c: i for i, c in enumerate(HOSTS)}
    rows.sort(key=lambda r: (0 if r["fy_or_date"] < "FY2024" else 1, order.get(r["corp_label"], 99), r["fy_or_date"], r["rcept_dt"]))
    with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(len(rows), Counter(r["status"] for r in rows))


NOTE_EXTRA = {}
EXTRA_ROWS = []


if __name__ == "__main__":
    sys.exit(main(sys.argv))
