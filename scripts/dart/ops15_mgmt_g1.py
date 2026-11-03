# -*- coding: utf-8 -*-
"""15차 — 경영공시(그룹 g1: KB·신한·하나·우리·NH농협) FY2019~FY2025 12월말 기준분 수집·글 뽑기·조각 추출.

    python3 -I scripts/dart/ops15_mgmt_g1.py fetch      # robots·약관 확인 → 게시판 목록 → 12월말 기준분 파일 받기 → 목록 CSV
    <venv>/python -I scripts/dart/ops15_mgmt_g1.py text # 받은 PDF → 「## p.N」 md (pymupdf, 받은 파일은 신뢰하지 않는 데이터)
    python3 -I scripts/dart/ops15_mgmt_g1.py extract    # md → 조각 B_mgmt_g1.csv·D_mgmt_g1.csv + 원문 md (다시 돌려도 같은 결과)

탐색용: robots | get <co> <url> <name> [referer] | post <co> <url> <name> <json> [referer]

HTTP 는 scripts/dart/web13.py 의 Web(=web9.Web: UA 고정·1.2초 간격·3회 시도=재시도 2회)·Robots(RFC 9309 판정:
4xx=제한 없음, 5xx·접속 실패=받지 않음)를 쓰고 저장 위치만 dart_out/raw/mgmt15/<회사>/ 로 바꾼다.
robots.txt 가 막는 경로는 받지 않고 사유를 남긴다(우회 없음 — UA 위장·다른 호스트·캐시 사이트 쓰지 않음).
우리금융지주(www.woorifg.com)는 OpenSSL 3 이 기본으로 막는 legacy renegotiation 서버라 governance.py 와 같은
OPENSSL_CONF(UnsafeLegacyRenegotiation, 인증서 검증은 그대로)로 한 번 재실행한다. API 키 쓰지 않음.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))
os.chdir(ROOT)

RAW = os.path.join("dart_out", "raw", "mgmt15")
WORK = os.path.join("dart_out", "ops15", "mgmt15_g1_work")
TEXT = os.path.join("dart_out", "text", "ops15")
LIST_CSV = os.path.join("dart_out", "ops15", "경영공시15_목록_g1.csv")
FRAG = os.path.join("dart_out", "ops15", "조각")
ORIG = os.path.join("dart_out", "ops15", "원문")

COS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]
FYS = list(range(2019, 2026))
HOSTS = {
    "KB금융지주": "https://www.kbfg.com",
    "신한금융지주": "https://www.shinhangroup.com",
    "하나금융지주": "https://www.hanafn.com",
    "우리금융지주": "https://www.woorifg.com",
    "NH농협금융지주": "https://www.nhfngroup.com",
}

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
    """우리금융지주 서버용 — 재협상 방식만 허용(인증서 검증은 그대로). ssl import 전에 한 번 재실행."""
    if os.environ.get("MGMT15_TLS_READY") == "1":
        return
    import tempfile
    cnf = os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "mgmt15_legacy_openssl.cnf")
    with open(cnf, "w", encoding="utf-8") as f:
        f.write(_LEGACY_CNF)
    env = dict(os.environ, OPENSSL_CONF=cnf, MGMT15_TLS_READY="1")
    os.execve(sys.executable, [sys.executable, "-I"] + sys.argv, env)


def _net():
    _ensure_legacy_tls()
    import web10  # noqa: F401
    import web13  # noqa: F401
    return web10, web13


def save(co, name, body, meta):
    """원본 바이트를 dart_out/raw/mgmt15/<co>/<name> 에, 메타는 같은 이름 + .meta.json."""
    p = os.path.join(RAW, co, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


_ROBOTS = {}
_WEB = None


def web():
    global _WEB
    if _WEB is None:
        _, web13 = _net()
        _WEB = web13.Web()
    return _WEB


def robots_for(url, co):
    web10, web13 = _net()
    pu = urllib.parse.urlparse(url)
    base = "%s://%s" % (pu.scheme, pu.netloc)
    if base not in _ROBOTS:
        _save = web10.save
        web10.save = lambda task, name, body, meta: save(task, name, body, meta)
        try:
            r = web13.Robots.__new__(web13.Robots)
            web10.Robots.__init__(r, web(), base, co)
        finally:
            web10.save = _save
        _ROBOTS[base] = r
        os.makedirs(WORK, exist_ok=True)
        rp = os.path.join(WORK, "robots.json")
        d = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
        d[pu.netloc] = dict(co=co, base=base, status=r.status, note=r.note, checked_at=web13.now())
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    return _ROBOTS[base]


def fetch(co, url, name, referer="", data=None, headers=None, extra=None):
    """robots 허용일 때만 받는다(Web.get = 3회 시도). (path, meta) 또는 예외."""
    _, web13 = _net()
    r = robots_for(url, co)
    if not r.allowed(url):
        raise PermissionError("robots 불허(%s): %s" % (r.status, url))
    fu, st, hd, b = web().get(url, referer=referer, data=data, headers=headers)
    meta = dict(url=url, 최종URL=fu, http=st, content_type=hd.get("Content-Type", ""),
                content_disposition=hd.get("Content-Disposition", ""), referer=referer,
                post=(data if isinstance(data, dict) else ""), fetched_at=web13.now(), robots=r.status)
    meta.update(extra or {})
    return save(co, name, b, meta)


# ── 게시판 목록 ─────────────────────────────────────────────────────────────
BOARD = {
    "KB금융지주": "https://www.kbfg.com/kor/ir/disclosure/management/list.htm",
    "신한금융지주": "https://www.shinhangroup.com/kr/ir/disclosure/management",
    "하나금융지주": "https://www.hanafn.com/ir/disclosure/managementList.do",
    "우리금융지주": "https://www.woorifg.com/kor/investor/disclosure/operation/list.do",
    "NH농협금융지주": "https://www.nhfngroup.com/user/indexSub.do?codyMenuSeq=1218157519&siteId=nhfngroup",
}


def _strip(s):
    import html as _h
    return _h.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def _dump(name, obj):
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def kb_list():
    """KB 경영공시 게시판(bulbdId=2) — GET /api/kbfg/posts?bulbdId=2 전 쪽(쪽당 50)."""
    co, board = "KB금융지주", BOARD["KB금융지주"]
    out, page, total = [], 1, 1
    while page <= total:
        url = "https://www.kbfg.com/api/kbfg/posts?bulbdId=2&page=%d&pageSize=50" % page
        p, m = fetch(co, url, os.path.join("pages", "kb_posts_b2_p%d.json" % page), referer=board)
        d = json.load(open(p, encoding="utf-8"))["result"]
        total = d["paging"]["totalPageCount"]
        for x in d["posts"]:
            for fl in (x.get("files") or []):
                out.append(dict(co=co, title=x["titl"], posted_at=(x.get("rgcrYms") or "")[:10], tgtYr=x.get("tgtYr"),
                                post_id=x["bltcId"], file_url="https://www.kbfg.com/api/download/board/%s" % fl["fileId"],
                                file_name=fl.get("orglFileNm") or "", file_size=fl.get("fileSize") or "",
                                board=board, list_url=url, list_post="", list_fetched_at=m["fetched_at"]))
        page += 1
    _dump("kb_list.json", out)
    return out


def sh_list():
    """신한 경영공시 — POST /api/v1/ir/disclosure_management/list current=N 전 쪽."""
    co, board = "신한금융지주", BOARD["신한금융지주"]
    api = "https://www.shinhangroup.com/api/v1/ir/disclosure_management/list"
    out, page, last = [], 1, 1
    while page <= last:
        body = {"pageType": "FRONT", "lang": "KOR", "current": str(page)}
        p, m = fetch(co, api, os.path.join("pages", "sh_mgmt_p%d.json" % page), referer=board, data=body)
        d = json.load(open(p, encoding="utf-8"))["result"]
        last = d.get("last") or 1
        for x in d["list"]:
            for fl in (x.get("fileList") or []):
                out.append(dict(co=co, title=x.get("title"), posted_at=(x.get("baseDt") or "").replace(".", "-"),
                                post_id=x.get("rowNum"), file_seq=fl.get("fileSeq"),
                                file_url="https://www.shinhangroup.com/main/downloadAttach?attachNo=%s&seq=%s"
                                % (fl.get("attachNo"), fl.get("fileSeq")),
                                file_name=fl.get("originalFileName") or "", file_size=fl.get("fileSize") or "",
                                board=board, list_url=api, list_post=json.dumps(body, ensure_ascii=False),
                                list_fetched_at=m["fetched_at"]))
        page += 1
    _dump("sh_list.json", out)
    return out


def hana_list(years=range(2019, 2027)):
    """하나 경영공시(/ir/disclosure/managementList.do) — POST searchYear=Y&pageNo=N(연도 선택 칸)."""
    co, board = "하나금융지주", BOARD["하나금융지주"]
    out = []
    for y in years:
        page, more = 1, True
        while more and page <= 5:
            body = {"pageNo": str(page), "searchYear": str(y)}
            p, m = fetch(co, board, os.path.join("pages", "hana_mgmt_%d_p%d.html" % (y, page)), referer=board, data=body)
            h = open(p, encoding="utf-8", errors="replace").read()
            got = 0
            for r in re.findall(r'<li role="row">(.*?)</li>', h, re.S):
                cells = dict(re.findall(r'<div role="cell" class="([^"]*)">(.*?)</div>', r, re.S))
                title = _strip(cells.get("left title", ""))
                if not title:
                    continue
                got += 1
                dl = re.findall(r"goDownload\('([^']+)'\)", r)
                fn = re.findall(r'title="([^"]*) 다운로드"', r)
                for i, u in enumerate(dl or [""]):
                    out.append(dict(co=co, title=title, posted_at="", searchYear=y, post_id=_strip(cells.get("hide", "")),
                                    affiliate=_strip(cells.get("sub", "")), file_url=u,
                                    file_name=fn[i] if i < len(fn) else "", file_size="", board=board, list_url=board,
                                    list_post=json.dumps(body, ensure_ascii=False), list_fetched_at=m["fetched_at"]))
            npages = re.findall(r"pageLink\((\d+)\)", h)
            more = got > 0 and npages and max(map(int, npages)) > page
            page += 1
    _dump("hana_list.json", out)
    return out


def woori_list(maxpage=12, stop_before="2020.01.01"):
    """우리 경영공시(/kor/investor/disclosure/operation/list.do) — GET pageIndex=N."""
    co, board = "우리금융지주", BOARD["우리금융지주"]
    out = []
    for page in range(1, maxpage + 1):
        url = board + "?pageIndex=%d&f=&q=" % page
        p, m = fetch(co, url, os.path.join("pages", "woori_op_p%d.html" % page), referer=board)
        h = open(p, encoding="utf-8", errors="replace").read()
        got = 0
        for b in h.split('<div class="list">')[1:]:
            t = re.search(r'<a\s+href="\./view\.do\?seq=(\d+)[^"]*">(.*?)</a>', b, re.S)
            if not t:
                continue
            got += 1
            dt = re.search(r'<div class="date[^"]*">\s*([0-9.]+)\s*</div>', b)
            fl = re.findall(r'href="(/cmm/fms/FileDown\.do\?[^"]+)"', b)
            for u in fl or [""]:  # noqa: E501
                out.append(dict(co=co, title=_strip(t.group(2)), posted_at=(dt.group(1) if dt else "").replace(".", "-"),
                                post_id=t.group(1), file_url=("https://www.woorifg.com" + _strip(u)) if u else "",
                                file_name="", file_size="", board=board, list_url=url, list_post="",
                                view_url="https://www.woorifg.com/kor/investor/disclosure/operation/view.do?seq=%s" % t.group(1),
                                list_fetched_at=m["fetched_at"]))
        if not got or (out and out[-1]["posted_at"] and out[-1]["posted_at"].replace("-", ".") < stop_before):
            break
    _dump("woori_list.json", out)
    return out


# ── 12월말 기준분 고르기·받기 ─────────────────────────────────────────────────
_QTR = ("1분기", "2분기", "3분기", "상반기", "반기")


def is_yearend(title, fy):
    """(판단) 제목에 「FY년」이 있고 1·2·3분기·상반기·반기 낱말이 없으면 그 해 12월말 기준(연간)분으로 봄."""
    t = re.sub(r"\s+", " ", title or "")
    if ("%d년" % fy) not in t:
        return False
    if re.search(r"%d년\s*(1분기|2분기|3분기|상반기|반기)" % fy, t):
        return False
    return not any(q in t for q in _QTR) or "4분기" in t


def candidates():
    """회사×FY 마다 12월말 기준분 게시글 하나(같은 FY 게시글이 여럿이면 게시일이 가장 늦은 것 = 정정판)."""
    lists = {}
    for co, fn in (("KB금융지주", "kb_list.json"), ("신한금융지주", "sh_list.json"), ("하나금융지주", "hana_list.json"),
                   ("우리금융지주", "woori_list.json")):
        p = os.path.join(WORK, fn)
        lists[co] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    out = []
    for co in COS[:4]:
        for fy in FYS:
            hits = [x for x in lists[co] if is_yearend(x["title"], fy)]
            posts = {}
            for x in hits:
                posts.setdefault((x["post_id"], x["title"]), []).append(x)
            keys = sorted(posts, key=lambda k: (posts[k][0]["posted_at"], "정정" in k[1], int(re.sub(r"\D", "", str(k[0])) or 0)))
            if not keys:
                out.append(dict(co=co, fy=fy, title="", files=[], others=[]))
                continue
            pick = keys[-1]
            out.append(dict(co=co, fy=fy, title=re.sub(r"\s+", " ", pick[1]).strip(), files=posts[pick],
                            others=[dict(title=k[1], posted_at=posts[k][0]["posted_at"],
                                         file_urls=[f["file_url"] for f in posts[k]]) for k in keys[:-1]]))
    _dump("candidates.json", out)
    return out


def _abs(co, u):
    if u.startswith("/"):
        return HOSTS[co] + u
    return u


def download(force=False):
    """candidates.json 의 파일을 받는다(robots 허용일 때만, Web.get 3회 시도). 이미 받은 파일(같은 url)은 다시 받지 않음."""
    _, web13 = _net()
    cands = json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))
    res = []
    for c in cands:
        co, fy = c["co"], c["fy"]
        for i, f in enumerate(c["files"], 1):
            listed = _abs(co, f["file_url"])
            urls = [listed]
            pu = urllib.parse.urlparse(listed)
            if pu.port:            # 하나 :8002 — 그 포트 robots 가 접속 실패면 같은 호스트 443 의 같은 경로(13차·gov_g1 와 같음)
                urls.append(urllib.parse.urlunparse(pu._replace(netloc=pu.hostname)))
            name = "%s_경영공시_FY%d%s.pdf" % (co, fy, "" if i == 1 else "_file%d" % i)
            p = os.path.join(RAW, co, name)
            rec = dict(co=co, fy=fy, title=c["title"], file_no=i, n_files=len(c["files"]), listed_url=listed, url="",
                       posted_at=f.get("posted_at", ""), list_file_name=f.get("file_name", ""),
                       list_file_size=f.get("file_size", ""), board=f.get("board", ""), list_url=f.get("list_url", ""),
                       list_post=f.get("list_post", ""), list_fetched_at=f.get("list_fetched_at", ""),
                       path="", bytes="", sha256="", fetched_at="", http="", content_type="", content_disposition="",
                       robots="", status="", errors=[])
            if not force and os.path.exists(p) and os.path.exists(p + ".meta.json"):
                m = json.load(open(p + ".meta.json", encoding="utf-8"))
                if m.get("목록_url") == listed:
                    rec.update(url=m["url"], path=p, bytes=m["바이트"], sha256=m["sha256"], fetched_at=m["fetched_at"],
                               http=m["http"], content_type=m["content_type"], content_disposition=m["content_disposition"],
                               robots=m["robots"], status="받음", errors=m.get("시도", []))
                    res.append(rec)
                    print(co, fy, i, "있음", rec["bytes"])
                    continue
            for u in urls:
                r = robots_for(u, co)
                if not r.allowed(u):
                    rec["errors"].append("%s: robots %s — 받지 않음" % (u, r.status))
                    continue
                try:
                    fu, st, hd, b = web().get(u, referer=f.get("board", ""))
                except Exception as e:  # noqa: BLE001
                    rec["errors"].append("%s: %s: %s" % (u, type(e).__name__, str(e)[:150]))
                    continue
                meta = dict(url=u, 목록_url=listed, 최종URL=fu, 게시판_url=f.get("board", ""), 제목=c["title"],
                            게시일=f.get("posted_at", ""), FY=fy, http=st, content_type=hd.get("Content-Type", ""),
                            content_disposition=hd.get("Content-Disposition", ""), 목록_파일명=f.get("file_name", ""),
                            목록_크기=f.get("file_size", ""), robots=r.status, fetched_at=web13.now(), 시도=rec["errors"])
                p, m = save(co, name, b, meta)
                rec.update(url=u, path=p, bytes=len(b), sha256=m["sha256"], fetched_at=meta["fetched_at"], http=st,
                           content_type=meta["content_type"], content_disposition=meta["content_disposition"],
                           robots=r.status, status="받음")
                break
            if not rec["path"]:
                rec["status"] = "실패"
            res.append(rec)
            print(co, fy, i, rec["status"], rec["bytes"], rec["url"][-50:], "; ".join(rec["errors"])[:120])
    _dump("download.json", res)
    return res


NH_TRIES = [("robots.txt", "https://www.nhfngroup.com/robots.txt"),
            ("경영공시 목록", BOARD["NH농협금융지주"])]


def nh_check():
    """NH 사이트를 robots.txt·경영공시 목록 한 번씩만 다시 시도(Web.get 3회 시도). 기록이 있으면 다시 하지 않음."""
    p = os.path.join(WORK, "nh_check.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    _, web13 = _net()
    out = []
    for what, u in NH_TRIES:
        t0 = web13.now()
        rec = dict(what=what, url=u, started_at=t0, result="")
        try:
            fu, st, hd, b = web().get(u)
            rec["result"] = "HTTP %s %d bytes" % (st, len(b))
        except Exception as e:  # noqa: BLE001
            body = b""
            try:
                body = e.read() or b""
            except Exception:  # noqa: BLE001
                pass
            t = re.search(rb"<H1>(.*?)</H1>", body or b"", re.S | re.I)
            rec["result"] = "%s: %s%s" % (type(e).__name__, str(e)[:120],
                                         (" 「%s」" % t.group(1).decode("utf-8", "replace")) if t else "")
        rec["ended_at"] = web13.now()
        out.append(rec)
        print("NH", what, rec["result"])
    _dump("nh_check.json", out)
    return out


ROBOTS_NOTE = {
    "KB금융지주": "https://www.kbfg.com/robots.txt HTTP 200 「User-agent: * / Allow:/」 → 허용",
    "신한금융지주": ("https://www.shinhangroup.com/robots.txt HTTP 200 「User-agent: *」 그룹 Allow:/ (Disallow 는 /front/asis/, "
                "/front/kr/governance/etc/sh_evalution.jsp 뿐) → 받은 경로(/api/v1/ir/disclosure_management/list, "
                "/main/downloadAttach) 허용"),
    "하나금융지주": ("https://www.hanafn.com/robots.txt HTTP 404 → RFC 9309 §2.3.1.3 제한 없음"),
    "우리금융지주": ("https://www.woorifg.com/robots.txt HTTP 200 「User-agent: * / Allow: /」(Yeti 에만 한 경로 Disallow) → 허용"),
    "NH농협금융지주": ("https://www.nhfngroup.com/robots.txt HTTP 400 「Request Blocked」 — RFC 9309 상 4xx 는 제한 없음이나 "
                  "경영공시 목록 쪽도 HTTP 400 「Request Blocked」로 막혀 받지 않음"),
}
TERMS_NOTE = {
    "KB금융지주": ("찾지 못함 — 첫 화면 https://www.kbfg.com/kor/index.jsp 하단 정책 링크는 개인정보처리방침·고객정보취급방침·"
                "신용정보활용체제뿐(이용약관·저작권정책 쪽 없음), 자동 수집 금지 문구 없음"),
    "신한금융지주": ("찾지 못함 — 첫 화면 https://www.shinhangroup.com/kr/ 하단 정책 링크는 개인정보처리방침·신용정보활용체제·"
                "고객정보취급방침·신한지킴이뿐(이용약관·저작권정책 쪽 없음), 자동 수집 금지 문구 없음"),
    "하나금융지주": ("찾지 못함 — 첫 화면 https://www.hanafn.com/main/index.do 하단 「이용약관」 메뉴 안은 개인정보처리방침·"
                "신용정보활용체제·고객정보취급방침·하나맵뿐(사이트 이용약관·저작권정책 본문 없음), 자동 수집 금지 문구 없음"),
    "우리금융지주": ("찾지 못함 — 첫 화면 https://www.woorifg.com/kor/main/index.do 하단 정책 링크는 개인정보처리방침·"
                "고객정보취급방침·신용정보활용체제뿐(이용약관·저작권정책 쪽 없음), 자동 수집 금지 문구 없음"),
    "NH농협금융지주": "확인 못 함 — 사이트가 이 환경 요청을 HTTP 400 「Request Blocked」로 막아 약관 쪽을 열 수 없음",
}
LIST_COLS = ["corp_label", "fy", "period_원문", "url", "posted_at", "fetched_at", "bytes", "pages", "sha256",
             "robots_verdict", "terms_note", "status", "note"]


def listcsv():
    """dart_out/ops15/경영공시15_목록_g1.csv — 회사×FY 35칸(받음·누리집에 없음·막힘·실패)."""
    cands = {(c["co"], c["fy"]): c for c in json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))}
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    tx = {}
    tp = os.path.join(WORK, "text.json")
    if os.path.exists(tp):
        tx = {(t["co"], t["fy"], t["file_no"]): t for t in json.load(open(tp, encoding="utf-8"))}
    nh = nh_check()
    rows = []
    for co in COS:
        for fy in FYS:
            base = dict(corp_label=co, fy=fy, robots_verdict=ROBOTS_NOTE[co], terms_note=TERMS_NOTE[co])
            if co == "NH농협금융지주":
                rows.append(dict(base, period_원문="", url="", posted_at="", fetched_at="", bytes="", pages="", sha256="",
                                 status="막힘",
                                 note=("받지 않음 — 다시 시도(한 번씩): " + "; ".join(
                                     "%s %s → %s (%s)" % (x["what"], x["url"], x["result"], x["started_at"]) for x in nh)
                                     + ". 2026-11-02 16:07~16:30 KST(gov_g1)에도 같은 차단. 다른 UA·호스트·캐시로 우회하지 않음 — "
                                       "게시판 목록을 못 열어 FY%d 12월말 기준분이 누리집에 있는지도 확인 못 함" % fy)))
                continue
            c = cands[(co, fy)]
            recs = [r for r in dl if r["co"] == co and r["fy"] == fy]
            if not c["files"]:
                rows.append(dict(base, period_원문="", url="", posted_at="", fetched_at="", bytes="", pages="", sha256="",
                                 status="누리집에 없음",
                                 note="게시판 %s 전체 목록에 FY%d 12월말(연간) 기준분 게시글 없음" % (BOARD[co], fy)))
                continue
            for r in recs:
                notes = []
                if r["url"] and r["url"] != r["listed_url"]:
                    notes.append("(판단) 목록 링크 %s 의 포트 8002 는 robots.txt 확인 실패(접속 끊김 — RFC 9309 상 받지 않음) → 같은 "
                                 "호스트 443 의 같은 경로(robots.txt 404 = 제한 없음)로 받음(13차·gov_g1 와 같은 방식)" % r["listed_url"])
                if r["n_files"] > 1:
                    notes.append("게시글에 첨부 파일 %d개 — 이 행은 %d번째 파일" % (r["n_files"], r["file_no"]))
                if not r["posted_at"]:
                    notes.append("목록에 게시일 칸 없음(연도 선택 %s 쪽에서 찾음)" % (r.get("list_post") or ""))
                elif r["posted_at"].startswith("1999-12-31"):
                    notes.append("posted_at 은 게시판 API 의 rgcrYms 값 그대로(1999-12-31 은 옛 글 일괄 이관 값으로 보임 — 실제 게시일 아님, 판단)")
                if c["others"]:
                    notes.append("같은 FY 다른 게시글(받지 않음): " + "; ".join(
                        "「%s」 %s %s" % (o["title"], o["posted_at"], " ".join(o["file_urls"])) for o in c["others"]))
                if "정정" in c["title"]:
                    notes.append("(판단) 정정판 게시글을 받음(게시판에 올라 있는 가장 늦은 판)")
                if r["list_file_name"]:
                    notes.append("목록 파일명 「%s」" % r["list_file_name"])
                if r["list_file_size"] and r["bytes"] and str(r["list_file_size"]) != str(r["bytes"]):
                    notes.append("목록 크기 %s ≠ 받은 크기 %s" % (r["list_file_size"], r["bytes"]))
                t = tx.get((co, fy, r["file_no"]), {})
                if t.get("fail"):
                    notes.append("글 뽑기 실패: " + t["fail"])
                if t.get("empty_pages"):
                    notes.append("글자 없는 쪽: " + t["empty_pages"])
                if r["status"] != "받음":
                    notes.append("시도: " + "; ".join(r["errors"]))
                notes.append("게시판 %s · 목록 %s %s(목록 받은 시각 %s)" % (r["board"], r["list_url"], r["list_post"] or "",
                                                                       r["list_fetched_at"]))
                rows.append(dict(base, period_원문=c["title"], url=r["url"] or r["listed_url"], posted_at=r["posted_at"],
                                 fetched_at=r["fetched_at"], bytes=r["bytes"], pages=t.get("pages", ""),
                                 sha256=r["sha256"], status=r["status"] if not t.get("fail") else "받음(글 뽑기 실패)",
                                 note=" · ".join(notes)))
    with open(LIST_CSV + ".tmp", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LIST_COLS)
        w.writeheader()
        w.writerows(rows)
    os.replace(LIST_CSV + ".tmp", LIST_CSV)
    print(LIST_CSV, len(rows))
    return rows


# ── 글 뽑기(PDF → 「## p.N」 md) ─────────────────────────────────────────────
def text_path(co, fy, file_no=1):
    return os.path.join(TEXT, "경영공시__%s__FY%d%s.md" % (co, fy, "" if file_no == 1 else "__file%d" % file_no))


HANGUL = re.compile(r"[가-힣]")
JUNK = re.compile(r"[�-]")


def cmd_text(paths=None):
    """받은 PDF → md(「## p.N」= PDF 쪽 순번, page.get_text() 그대로; 글자 없는 쪽은 「## p.N (글자 없음)」).
    venv 파이썬 -I 로 돌림. paths 를 주면 그 파일만(download.json 의 path 와 같아야 함).
    (판단) 글자층 판정: 글자 있는 쪽이 절반 미만이거나, 글자 가운데 한글 비율 20% 미만·깨진 글자(U+FFFD·사용자 영역) 5% 이상이면 실패."""
    import pymupdf
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    tp_json = os.path.join(WORK, "text.json")
    old = {(t["co"], t["fy"], t["file_no"]): t for t in json.load(open(tp_json, encoding="utf-8"))} if os.path.exists(tp_json) else {}
    os.makedirs(TEXT, exist_ok=True)
    for r in dl:
        key = (r["co"], r["fy"], r["file_no"])
        if r["status"] != "받음" or not r["path"]:
            continue
        if paths and r["path"] not in paths:
            continue
        rec = dict(co=r["co"], fy=r["fy"], file_no=r["file_no"], pdf=r["path"], text_path="", pages="", empty_pages="",
                   hangul_ratio="", junk_ratio="", fail="")
        with open(r["path"], "rb") as f:
            head = f.read(1024)
        if b"%PDF-" not in head:
            rec["fail"] = "받은 내용이 PDF 가 아님(앞 1KB 에 %PDF- 없음, content-type " + r["content_type"] + ")"
            old[key] = rec
            print(*key, rec["fail"])
            continue
        try:
            doc = pymupdf.open(r["path"])
        except Exception as e:  # noqa: BLE001
            rec["fail"] = "PDF 열기 실패: %s: %s" % (type(e).__name__, str(e)[:120])
            old[key] = rec
            continue
        tp = text_path(*key)
        empty, nh, nj, nall = [], 0, 0, 0
        with open(tp + ".part", "w", encoding="utf-8") as f:
            f.write("# 경영공시 %s FY%d — 「%s」\n\n" % (r["co"], r["fy"], r["title"]))
            f.write("- 파일 url: %s\n- 게시판: %s\n- 게시일(목록): %s\n- 받은 시각: %s\n- sha256: %s\n- 바이트: %s\n"
                    "- 변환: pymupdf %s page.get_text() 그대로, 「## p.N」= PDF 쪽 순번\n\n"
                    % (r["url"], r["board"], r["posted_at"] or "(목록에 없음)", r["fetched_at"], r["sha256"], r["bytes"],
                       getattr(pymupdf, "VersionBind", "")))
            for i, pg in enumerate(doc, 1):
                t = pg.get_text()
                if not t.strip():
                    empty.append(i)
                    f.write("## p.%d (글자 없음)\n\n" % i)
                    continue
                s = re.sub(r"\s", "", t)
                nall += len(s)
                nh += len(HANGUL.findall(s))
                nj += len(JUNK.findall(s))
                f.write("## p.%d\n\n%s\n" % (i, t.rstrip("\n") + "\n"))
        os.replace(tp + ".part", tp)
        n = doc.page_count
        rec.update(text_path=tp, pages=n, empty_pages=(",".join(map(str, empty)) if len(empty) < 30 else
                                                        "%d쪽(%s…)" % (len(empty), ",".join(map(str, empty[:10])))),
                   hangul_ratio=round(nh / nall, 3) if nall else 0, junk_ratio=round(nj / nall, 3) if nall else 0)
        if n == 0 or len(empty) * 2 > n:
            rec["fail"] = "글자층 없음 — %d쪽 가운데 %d쪽이 글자 없음(스캔 그림으로 보임)" % (n, len(empty))
        elif rec["hangul_ratio"] < 0.2 or rec["junk_ratio"] >= 0.05:
            rec["fail"] = "글자층 깨짐 — 한글 비율 %s, 깨진 글자 비율 %s" % (rec["hangul_ratio"], rec["junk_ratio"])
        old[key] = rec
        print(*key, n, "빈쪽", len(empty), "한글", rec["hangul_ratio"], "깨짐", rec["junk_ratio"], rec["fail"])
    _dump("text.json", sorted(old.values(), key=lambda t: (COS.index(t["co"]), t["fy"], t["file_no"])))


def cmd_fetch():
    robots_for(HOSTS["KB금융지주"] + "/", "KB금융지주")
    kb_list()
    sh_list()
    hana_list()
    woori_list()
    candidates()
    download()
    nh_check()
    listcsv()


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "fetch":
        cmd_fetch()
        return 0
    if cmd == "text":
        cmd_text([os.path.relpath(os.path.abspath(a), ROOT) for a in argv[2:]] or None)
        listcsv()
        return 0
    if cmd in ("candidates", "download", "listcsv", "nh_check"):
        globals()[cmd]()
        return 0
    if cmd in ("kb_list", "sh_list", "hana_list", "woori_list"):
        out = globals()[cmd]()
        for x in out:
            print(x["posted_at"], x.get("searchYear", ""), x["title"][:50], x["file_url"][-60:], x["file_size"])
        return 0
    if cmd == "robots":
        for co, b in HOSTS.items():
            try:
                r = robots_for(b + "/", co)
                print(co, r.status, r.note[:150])
            except Exception as e:  # noqa: BLE001
                print(co, "ERR", type(e).__name__, str(e)[:150])
        return 0
    if cmd == "get":
        co, url, name = argv[2], argv[3], argv[4]
        ref = argv[5] if len(argv) > 5 else ""
        p, m = fetch(co, url, os.path.join("pages", name), referer=ref)
        print(m["http"], m["바이트"], m["content_type"], m["content_disposition"][:80], p)
        return 0
    if cmd == "post":
        co, url, name, body = argv[2], argv[3], argv[4], json.loads(argv[5])
        ref = argv[6] if len(argv) > 6 else ""
        p, m = fetch(co, url, os.path.join("pages", name), referer=ref, data=body)
        print(m["http"], m["바이트"], m["content_type"], p)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
