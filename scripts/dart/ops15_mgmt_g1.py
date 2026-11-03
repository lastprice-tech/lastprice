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
    "KB금융지주": "https://www.kbfg.com/kor/ir/disclosure/mgt/list.htm",
    "신한금융지주": "https://www.shinhangroup.com/kr/ir/disclosure/pillarDisclosure",
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


def cd_name(cd):
    """Content-Disposition 의 파일 이름(filename* 우선)."""
    m = re.search(r"filename\*\s*=\s*([^']*)'[^']*'([^;]+)", cd or "")
    if m:
        return urllib.parse.unquote(m.group(2).strip().strip('"'), encoding=m.group(1) or "utf-8")
    m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd or "")
    return urllib.parse.unquote(m.group(1)) if m else ""


def _role(cd):
    """(판단) 첨부 파일 이름에 「정정내역」이 있으면 정정 안내 파일, 아니면 본문."""
    return "정정내역" if "정정내역" in cd_name(cd) else "본문"


def _existing(co, listed):
    """dart_out/raw/mgmt15/<co>/ 에서 목록_url 이 같은 받은 파일(경로, meta)."""
    import glob
    for mp in glob.glob(os.path.join(RAW, co, "*_경영공시_FY*.meta.json")):
        m = json.load(open(mp, encoding="utf-8"))
        if m.get("목록_url") == listed and os.path.exists(mp[:-len(".meta.json")]):
            return mp[:-len(".meta.json")], m
    return None, None


def _place(co, fy, items):
    """한 게시글의 받은 파일들을 역할 이름으로 옮김: 본문 → <co>_경영공시_FY<fy>.pdf, 정정 안내 → …_정정내역.pdf."""
    want, nmain = {}, 0
    for rec in items:
        if not rec["path"]:
            continue
        if rec["role"] == "정정내역":
            nm = "%s_경영공시_FY%d_정정내역.pdf" % (co, fy)
        else:
            nmain += 1
            nm = "%s_경영공시_FY%d%s.pdf" % (co, fy, "" if nmain == 1 else "_file%d" % rec["file_no"])
        want[rec["path"]] = os.path.join(RAW, co, nm)
    if all(k == v for k, v in want.items()):
        return
    tmp = {}
    for src in want:
        os.replace(src, src + ".mv")
        os.replace(src + ".meta.json", src + ".mv.meta.json")
        tmp[src] = src + ".mv"
    for rec in items:
        if rec["path"] in want:
            src, dst = tmp[rec["path"]], want[rec["path"]]
            os.replace(src, dst)
            m = json.load(open(src + ".meta.json", encoding="utf-8"))
            m["저장경로"] = dst
            with open(dst + ".meta.json", "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=1)
            os.remove(src + ".meta.json")
            rec["path"] = dst


def download(force=False):
    """candidates.json 의 파일을 받는다(robots 허용일 때만, Web.get 3회 시도). 이미 받은 파일(같은 목록 url)은 다시 받지 않음."""
    _, web13 = _net()
    cands = json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))
    dj = os.path.join(WORK, "download.json")
    prev_fail = {r["listed_url"]: r for r in (json.load(open(dj, encoding="utf-8")) if os.path.exists(dj) else [])
                 if r.get("status") == "실패"}
    res = []
    for c in cands:
        co, fy = c["co"], c["fy"]
        items = []
        for i, f in enumerate(c["files"], 1):
            listed = _abs(co, f["file_url"])
            urls = [listed]
            pu = urllib.parse.urlparse(listed)
            if pu.port:            # 하나 :8002 — 그 포트 robots 가 접속 실패면 같은 호스트 443 의 같은 경로(13차·gov_g1 와 같음)
                urls.append(urllib.parse.urlunparse(pu._replace(netloc=pu.hostname)))
            rec = dict(co=co, fy=fy, title=c["title"], file_no=i, n_files=len(c["files"]), role="", listed_url=listed,
                       url="", posted_at=f.get("posted_at", ""), list_file_name=f.get("file_name", ""),
                       list_file_size=f.get("file_size", ""), board=f.get("board", ""), list_url=f.get("list_url", ""),
                       list_post=f.get("list_post", ""), list_fetched_at=f.get("list_fetched_at", ""),
                       path="", bytes="", sha256="", fetched_at="", http="", content_type="", content_disposition="",
                       robots="", status="", errors=[])
            p, m = (None, None) if force else _existing(co, listed)
            if not p and not force and listed in prev_fail:
                # 같은 파일 재시도는 2회까지(Web.get 1회 = 3번 시도) — 앞서 실패한 파일은 다시 받지 않고 기록을 이어 씀
                rec.update(status="실패", errors=prev_fail[listed]["errors"],
                           fetched_at=prev_fail[listed].get("fetched_at", ""))
                items.append(rec)
                print(co, fy, i, "앞서 실패 — 다시 받지 않음")
                continue
            if p:
                rec.update(url=m["url"], path=p, bytes=m["바이트"], sha256=m["sha256"], fetched_at=m["fetched_at"],
                           http=m["http"], content_type=m["content_type"], content_disposition=m["content_disposition"],
                           robots=m["robots"], status="받음", errors=m.get("시도", []), role=_role(m["content_disposition"]))
                items.append(rec)
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
                p, m = save(co, "%s_경영공시_FY%d_file%d.pdf.dl" % (co, fy, i), b, meta)
                rec.update(url=u, path=p, bytes=len(b), sha256=m["sha256"], fetched_at=meta["fetched_at"], http=st,
                           content_type=meta["content_type"], content_disposition=meta["content_disposition"],
                           robots=r.status, status="받음", role=_role(meta["content_disposition"]))
                break
            if not rec["path"]:
                rec["status"] = "실패"
            items.append(rec)
            print(co, fy, i, rec["status"], rec["bytes"], rec["url"][-50:], "; ".join(rec["errors"])[:160], flush=True)
        _place(co, fy, items)
        res.extend(items)
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
def _nh_robots_at():
    try:
        return json.load(open(os.path.join(WORK, "robots.json"), encoding="utf-8"))["www.nhfngroup.com"]["checked_at"]
    except Exception:  # noqa: BLE001
        return "?"


NH_ROBOTS_AT = _nh_robots_at()
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
    nhp = os.path.join(WORK, "nh_check.json")
    nh = json.load(open(nhp, encoding="utf-8")) if os.path.exists(nhp) else []   # 네트워크는 fetch 단계에서만
    rows = []
    for co in COS:
        for fy in FYS:
            base = dict(corp_label=co, fy=fy, robots_verdict=ROBOTS_NOTE[co], terms_note=TERMS_NOTE[co])
            if co == "NH농협금융지주":
                rows.append(dict(base, period_원문="", url="", posted_at="", fetched_at="", bytes="", pages="", sha256="",
                                 status="막힘",
                                 note=("받지 않음 — 다시 시도(요청마다 Web.get 3번 시도): ① 탐색 단계 robots.txt 2회(2026-11-03 "
                                       "10:19·%s KST)·경영공시 목록 쪽 1회(10:20 KST 무렵) 모두 HTTP 400 「Request Blocked」; "
                                       "② nh_check: " % NH_ROBOTS_AT[11:19] + "; ".join(
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
            side = [r for r in recs if r.get("role") == "정정내역"]
            for r in [r for r in recs if r.get("role") != "정정내역"]:
                notes = []
                if r["url"] and r["url"] != r["listed_url"]:
                    notes.append("(판단) 목록 링크 %s 의 포트 8002 는 robots.txt 확인 실패(접속 끊김 — RFC 9309 상 받지 않음) → 같은 "
                                 "호스트 443 의 같은 경로(robots.txt 404 = 제한 없음)로 받음(13차·gov_g1 와 같은 방식)" % r["listed_url"])
                if r["n_files"] > 1:
                    notes.append("게시글에 첨부 파일 %d개 — 이 행은 %d번째 파일(본문, 첨부 이름 「%s」)"
                                 % (r["n_files"], r["file_no"], cd_name(r["content_disposition"])))
                for x in side:
                    tx2 = tx.get((co, fy, x["file_no"]), {})
                    notes.append("(판단) %d번째 첨부는 정정 안내 파일(첨부 이름 「%s」에 「정정내역」) — 따로 받아 둠(%s, %s bytes, "
                                 "sha256 %s, %s쪽, 받은 시각 %s, dart_out/raw/mgmt15/%s/%s); 조각은 본문 파일에서만 뽑음"
                                 % (x["file_no"], cd_name(x["content_disposition"]), x["url"], x["bytes"], x["sha256"],
                                    tx2.get("pages", ""), x["fetched_at"], co, os.path.basename(x["path"])))
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
                sm = re.search(r"saveFileNm=(\d{8})", r["listed_url"])
                if sm and r["posted_at"] and sm.group(1) != r["posted_at"].replace("-", ""):
                    notes.append("(참고) 파일 저장 이름의 날짜(%s)가 게시일(%s)과 다름 — 게시 뒤 파일이 바뀌었을 수 있음(판단)"
                                 % (sm.group(1), r["posted_at"]))
                if r["list_file_size"] and r["bytes"] and str(r["list_file_size"]) != str(r["bytes"]):
                    notes.append("목록 크기 %s ≠ 받은 크기 %s" % (r["list_file_size"], r["bytes"]))
                t = tx.get((co, fy, r["file_no"]), {})
                if t.get("fail"):
                    notes.append("글 뽑기 실패: " + t["fail"])
                if t.get("empty_pages"):
                    notes.append("글자 없는 쪽(pymupdf 글 0자): " + t["empty_pages"] + " — 그 쪽은 글을 뽑지 못해 찾지 못함(글을 지어내지 않음)")
                if r["status"] != "받음":
                    nxt = [x["fetched_at"] for x in dl if x["co"] == co and x["fetched_at"] and x["fy"] > fy]
                    notes.append("받지 못함 — Web.get 1회(3번 시도 = 재시도 2회) 모두 실패: " + "; ".join(r["errors"])
                                 + " · 시도 시각은 따로 남기지 않음(%s 파일 목록 받은 %s 뒤, 다음 FY 파일 받은 %s 앞) · "
                                   "재시도 한도(2회)를 써서 다시 받지 않음, 다른 주소·캐시로 돌지 않음"
                                 % (co, r["list_fetched_at"], min(nxt) if nxt else "?"))
                notes.append("게시판 %s · 목록 %s %s(목록 받은 시각 %s)" % (BOARD[co], r["list_url"], r["list_post"] or "",
                                                                       r["list_fetched_at"]))
                if r["board"] and r["board"] != BOARD[co]:
                    notes.append("(참고) 2026-11-03 목록·파일 요청의 Referer 머리에는 게시판 주소를 잘못 짐작한 값(%s)을 보냄 — "
                                 "UA 는 그대로, 받은 내용과 robots 판정에는 영향 없음" % r["board"])
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
def text_path(co, fy, role="본문"):
    return os.path.join(TEXT, "경영공시__%s__FY%d%s.md" % (co, fy, "" if role == "본문" else "__" + role))


HANGUL = re.compile(r"[가-힣]")
JUNK = re.compile(r"[�-]")


def cmd_text(paths=None):
    """받은 PDF → md(「## p.N」= PDF 쪽 순번, page.get_text() 그대로; 글자 없는 쪽은 「## p.N (글자 없음)」).
    venv 파이썬 -I 로 돌림. paths 를 주면 그 파일만(download.json 의 path 와 같아야 함).
    (판단) 글자층 판정: 모든 쪽에 글자가 없거나, 글자 가운데 한글 비율 20% 미만·깨진 글자(U+FFFD·사용자 영역) 5% 이상이면 실패.
    일부 쪽만 글자가 없으면(그림 쪽) 글자 있는 쪽만 쓰고 글자 없는 쪽을 목록·「문서에 없음」 행 note 에 밝힘(글을 지어내지 않음)."""
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
        tp = text_path(r["co"], r["fy"], r.get("role") or "본문")
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
        if n == 0 or len(empty) == n:
            rec["fail"] = "글자층 없음 — %d쪽 모두 글자 없음(스캔 그림으로 보임)" % n
        elif rec["hangul_ratio"] < 0.2 or rec["junk_ratio"] >= 0.05:
            rec["fail"] = "글자층 깨짐 — 한글 비율 %s, 깨진 글자 비율 %s" % (rec["hangul_ratio"], rec["junk_ratio"])
        old[key] = rec
        print(*key, n, "빈쪽", len(empty), "한글", rec["hangul_ratio"], "깨짐", rec["junk_ratio"], rec["fail"])
    _dump("text.json", sorted(old.values(), key=lambda t: (COS.index(t["co"]), t["fy"], t["file_no"])))


# ── 조각 추출 ──────────────────────────────────────────────────────────────
NONE = "문서에 없음"
B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
D_COLS = ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"]
B_KWS = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
D_TERMS = ["업무위탁", "경영자문", "공동사용", "위탁", "용역", "전산"]
AFFIL = re.compile(r"자회사|손자회사|계열사|그룹사")
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
END_RE = re.compile(r"(다\.|요\.|음\.|함\.|됨\.|임\.|\.|(임|다|음|함)\))\s*$")
BULLET_RE = re.compile(r"^\s*(\d{4}\.\s?\d{1,2}\.|[-*•·ㆍ□■○●▶◦※]|주\s?\d+\)|\(?\d{1,2}\)|[①-⑳]|[가-하]\.|\([가-하]\)|\d{1,2}\.|\([가-하IVX]+\))\s*")


def load_pages(tp):
    """text md → [(쪽 번호, 그 쪽 글)] — 「## p.N」 머리 다음 빈 줄부터 다음 머리 앞까지(쓴 그대로)."""
    s = open(tp, encoding="utf-8").read()
    out = []
    parts = re.split(r"^## p\.(\d+)( \(글자 없음\))?\n\n", s, flags=re.M)
    for k in range(1, len(parts), 3):
        n, empty, body = int(parts[k]), parts[k + 1], parts[k + 2]
        out.append((n, "" if empty else body))
    return out


def _flat(lines):
    """공백·줄바꿈을 지운 글과, 그 글자마다의 줄 번호."""
    chars, idx = [], []
    for i, l in enumerate(lines):
        for ch in l:
            if not ch.isspace():
                chars.append(ch)
                idx.append(i)
    return "".join(chars), idx


def find_terms(lines, terms, check=None):
    """줄 넘김·공백을 무시하고 terms 를 찾음 → [(낱말, 시작 줄, 끝 줄)]. 긴 낱말이 먼저 — 겹친 짧은 낱말은 뺌."""
    S, idx = _flat(lines)
    taken, out = set(), []
    for t in terms:
        for m in re.finditer(re.escape(t), S):
            span = set(range(m.start(), m.end()))
            if span & taken:
                continue
            if check and not check(t, S, m):
                continue
            taken |= span
            out.append((t, idx[m.start()], idx[m.end() - 1], m.start()))
    out.sort(key=lambda x: x[3])
    return [(t, a, b) for t, a, b, _ in out]


def b_check(t, S, m):
    """(판단) 「전적」은 앞이 한글이 아니고 뒤가 「으로·인·합」이 아닐 때만(「완전적용」「전적으로」 제외)."""
    if t != "전적":
        return True
    if m.start() > 0 and re.match(r"[가-힣]", S[m.start() - 1]):
        return False
    return not re.match(r"으로|인|합", S[m.end():m.end() + 2])


def unit(lines, i0, i1, maxback=4, maxfwd=4):
    """검색어가 든 문장(PDF 줄 단위로 앞뒤로 넓힘) → (s, e, kind). 문장이 아니고 짧은 줄(표 칸)이면 앞뒤 2줄 창."""
    s = i0
    for _ in range(maxback):
        if s == 0:
            break
        prev = lines[s - 1]
        if not prev.strip() or END_RE.search(prev) or BULLET_RE.match(lines[s] or "") or len(prev.strip()) < 20:
            break
        s -= 1
    e = i1
    for _ in range(maxfwd):
        cur = lines[e]
        if END_RE.search(cur) or e + 1 >= len(lines):
            break
        if BULLET_RE.match(cur) and len(cur.strip()) < 45:
            break
        nxt = lines[e + 1]
        if not nxt.strip() or BULLET_RE.match(nxt) or nxt.strip().startswith("(") \
                or (len(nxt.strip()) < 12 and not nxt.strip().endswith(".")):
            break
        e += 1
    txt = " ".join(lines[s:e + 1])
    if s == e and len(lines[s].strip()) < 25 and not END_RE.search(lines[s]):
        if len(re.sub(r"\s", "", " ".join(lines[i0:i1 + 1]))) >= 12:
            return i0, i1, "cell"           # 글이 충분한 표 칸·목록 줄은 그 줄만
        a, b = max(0, i0 - 2), min(len(lines) - 1, i1 + 2)
        while a < i0 and not lines[a].strip():
            a += 1
        while b > i1 and not lines[b].strip():
            b -= 1
        return a, b, "cell"
    return s, e, ("sent" if END_RE.search(lines[e]) or len(txt) >= 40 else "cell")


def clean(txt):
    """보이지 않는 제어문자(줄바꿈·탭 말고)만 지움 → (글, 지웠는지)."""
    t2 = CTRL.sub("", txt)
    return t2, t2 != txt


def docs_for_extract():
    """받고 글 뽑기에 성공한 본문 파일 → [(co, fy, dl rec, text rec)]."""
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    tx = {(t["co"], t["fy"], t["file_no"]): t for t in json.load(open(os.path.join(WORK, "text.json"), encoding="utf-8"))}
    out = []
    for r in dl:
        if r["status"] != "받음" or r.get("role") == "정정내역":
            continue
        t = tx.get((r["co"], r["fy"], r["file_no"]))
        if not t or t.get("fail") or not t.get("text_path"):
            continue
        out.append((r["co"], r["fy"], r, t))
    return out


def _base(co, fy, r, t):
    return dict(corp_label=co, fy=str(fy), doc_kind="경영공시", rcept_no_or_url=r["url"], doc_name=r["title"],
                collected_at=r["fetched_at"])


def _ranges(ns):
    """[348, 349, 350, 651] → 「348~350,651」."""
    out, ns = [], sorted(ns)
    for n in ns:
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ",".join(("%d~%d" % (a, b)) if a != b else str(a) for a, b in out)


def garbled_pages(pages):
    """(판단) 글자층이 깨진 쪽(검증 15차 g1 추가): 글자는 있으나 공백 뺀 글자 가운데 한글이 20% 미만이고 보이지 않는
    제어문자가 5자 이상인 쪽 — 글꼴 부호가 깨져 낱말을 찾을 수 없는 쪽(KB FY2024 감사보고서 부분 등). 글을 지어내지 않고 note 에 밝힘."""
    out = []
    for n, body in pages:
        s = re.sub(r"\s", "", body)
        if s and len(HANGUL.findall(s)) / len(s) < 0.2 and len(CTRL.findall(body)) >= 5:
            out.append(n)
    return out


def _garble_note(pages):
    g = garbled_pages(pages)
    return ("%d쪽(p.%s)" % (len(g), _ranges(g))) if g else ""


def _common(co, fy, t, pages=None):
    c = "FY%d 경영공시 PDF 글(%s, pymupdf page.get_text() 그대로 — 「## p.N」= PDF 쪽)" % (fy, os.path.basename(t["text_path"]))
    m = re.match(r"(\d+)쪽\(", t.get("empty_pages") or "")
    if m and int(m.group(1)) >= 10:
        c += "; 이 문서의 글자 없는 쪽 %s 은 그림이라 찾지 못함" % t["empty_pages"]
    gn = _garble_note(pages) if pages else ""
    if gn:
        c += ("; 이 문서의 글자층이 깨진 쪽 %s 은 글자는 있으나 한글 20%% 미만·제어문자 5자 이상이라(글꼴 부호 깨짐) 낱말을 "
              "찾을 수 없어 찾지 못함" % gn)
    return c


def extract_B(docs, sect):
    rows = []
    for co, fy, r, t in docs:
        pages = load_pages(t["text_path"])
        base, common = _base(co, fy, r, t), _common(co, fy, t, pages)
        seen = {}
        mine = []
        for n, body in pages:
            lines = body.split("\n")
            units = {}
            for kw, a, b in find_terms(lines, B_KWS, b_check):
                units.setdefault(kw, []).append(list(unit(lines, a, b)))
            merged = []
            for kw, us in units.items():
                us.sort()
                mk = []
                for u in us:            # 겹치거나(같은 문장) 바로 붙은 표 칸 줄은 한 행으로 합침(이어진 글 그대로)
                    if mk and (u[0] <= mk[-1][1] or (u[2] == mk[-1][2] == "cell" and u[0] == mk[-1][1] + 1)) \
                            and len(" ".join(lines[mk[-1][0]:u[1] + 1])) < 1500:
                        mk[-1][1] = max(mk[-1][1], u[1])
                        mk[-1][2] = "cell" if mk[-1][2] == u[2] == "cell" else "sent"
                    else:
                        mk.append(u)
                merged.extend((s_, e_, k_, kw) for s_, e_, k_ in mk)
            merged.sort()
            for s, e, kind, kw in merged:
                raw = "\n".join(lines[s:e + 1]).strip()
                txt, cut = clean(raw)
                key = (kw, re.sub(r"\s", "", txt))
                if key in seen:
                    if ("p.%d" % n) not in seen[key]["_also"] and ("p.%d" % n) != seen[key]["page"]:
                        seen[key]["_also"].append("p.%d" % n)
                    continue
                notes = [common]
                if kind == "cell":
                    notes.append("(판단) 문장이 아닌 표 칸·목록 줄 — 검색어가 든 줄(바로 붙은 같은 검색어 줄은 합침; 글이 12자 "
                                 "미만이면 앞뒤 2줄까지)을 PDF 줄바꿈 그대로 옮김")
                if cut:
                    notes.append("제어문자 지움")
                notes.append("직원 수는 같은 FY 사업보고서 행")
                row = dict(base, employees_total="", regular="", contract="", keyword=kw, source_text=txt,
                           page="p.%d" % n, note="", _notes=notes, _also=[])
                seen[key] = row
                mine.append(row)
                sect.setdefault(("B", co, fy), set()).add(n)
        for row in mine:
            if row["_also"]:
                row["_notes"].insert(1, "같은 글이 %s 에도 있음(한 번만 옮김)" % ",".join(row["_also"]))
            row["note"] = "; ".join(row.pop("_notes"))
            row.pop("_also")
        if not mine:
            mine.append(dict(base, employees_total="", regular="", contract="", keyword="없음", source_text=NONE,
                             page="p.1~p.%d(경영공시 전체 — 찾은 범위)" % len(pages),
                             note="; ".join([common, "찾은 범위: FY%d 경영공시 전체 %d쪽(글자 없는 쪽 %s%s) · 검색어 %s(공백·줄바꿈 무시, "
                                                     "「전적으로」「완전적용」 같은 다른 낱말 속 「전적」은 뺌) · 없음"
                                             % (fy, len(pages), t.get("empty_pages") or "없음",
                                                (" · 글자층 깨진 쪽 " + _garble_note(pages)) if _garble_note(pages) else "",
                                                "·".join(B_KWS)),
                                             _b_wider(pages),
                                             "직원 수는 같은 FY 사업보고서 행"])))
        rows.extend(mine)
    return rows


B_WIDER = ["겸임", "겸업", "兼", "인사교류", "인력지원", "지원인력", "인력교류", "순환근무"]


def _b_wider(pages):
    """(검증 15차 g1 추가) 「문서에 없음」 반박 시도 — 더 넓은 검색어로 찾은 쪽(위치만; 6개 검색어가 아니라 행으로 넣지 않음)."""
    hits = {}
    for n, body in pages:
        S = re.sub(r"\s", "", body)
        for w in B_WIDER:
            if w in S:
                hits.setdefault(w, []).append(n)
        if re.search(r"(?:^|\s)겸(?=\s)", body):
            hits.setdefault("홀로 쓴 「겸」", []).append(n)
    found = " · ".join("%s p.%s" % (w, _ranges(ns)) for w, ns in hits.items()) or "없음"
    return ("더 넓은 검색어(%s·홀로 쓴 「겸」, 공백·줄바꿈 무시)로도 찾음 — 찾은 곳: %s; (판단) 이 낱말들은 사용자 지정 검색어 6개가 "
            "아니라 행으로 넣지 않고 위치만 적음" % ("·".join(B_WIDER), found))


HOLDCO = {
    "KB금융지주": r"KB금융지주|KB금융그룹|케이비금융지주",
    "신한금융지주": r"신한금융지주",
    "하나금융지주": r"하나금융지주",
    "우리금융지주": r"우리금융지주",
}
TOK_RE = re.compile(r"^\s*(채권\s*[·ㆍ]?\s*채무|수익\s*[·ㆍ]?\s*비용|매매\s*거래|자산\s*매매|신용\s*공여|기타\s*거래|자산\s*양수도)"
                    r"\s*(\(.*\))?\s*$")
ROW_END_RE = re.compile(r"^\s*(합\s*계|소\s*계|주\s*\d?\)|\(주\)|※|\(단위|[가-하]\.\s|[①-⑳]|\(\d+\)|\d\.\s)")
AMT_RE = re.compile(r"^\s*(\(?[△▲\-]?\s*\d[\d,]*(\.\d+)?\)?|-)\s*$")   # 금액 칸(날짜 「2020-06-16」 꼴은 아님)
PROSE_HOLD = r"지주|당사|당\s?그룹"


def _nb(lines, k, step, lim):
    """k 에서 step 방향으로 빈 줄(공백만 있는 표 칸)을 건너뛴 다음 글 줄 번호(lim 줄 안), 없으면 None."""
    for _ in range(lim):
        k += step
        if k < 0 or k >= len(lines):
            return None
        if lines[k].strip():
            return k
    return None


def _party(line):
    """(판단) 당사자 칸 꼴: 금액·거래구분 칸이 아니고, 숫자·괄호로 시작하지 않고, 글자 2자 이상, 30자 미만."""
    t = line.strip()
    return (not AMT_RE.match(t) and not TOK_RE.match(t) and not re.match(r"[\d(]", t)
            and re.search(r"[가-힣A-Za-z]{2}", t) is not None and len(t) < 30)


HDR_AMT_RE = re.compile(r"^\s*(거래금액|금액|금엑)\s*$")
HDR_TAIL_RE = re.compile(r"^\s*(비고|계정과목|거래항목?|목|\(?\s*단위)")


def _label_first_header(lines, h):
    """검색어 줄 위에서 가장 가까운 「거래금액」 머리 칸이 [거래내용, 채권자…, 채무자…, 거래금액] 4칸 머리의 끝이고
    그 다음 줄이 계정과목·비고 머리 칸이 아닌지(= 행 끝이 금액 칸인 표)."""
    for k in range(h - 1, max(-1, h - 400), -1):
        if HDR_AMT_RE.match(lines[k]):
            if k < 3:
                return False
            a, b, c = (lines[k - 3].strip(), re.sub(r"\s", "", lines[k - 2]), re.sub(r"\s", "", lines[k - 1]))
            nxt = _nb(lines, k, 1, 3)
            return (a == "거래내용" and re.search(r"채권자|매도자", b) is not None and re.search(r"채무자|매수자", c) is not None
                    and nxt is not None and not HDR_TAIL_RE.match(lines[nxt]))
    return False


def table_row(lines, h):
    """(판단) 거래 표의 한 행 → (s, e, 방식) 또는 None. 셋 가운데 처음 맞는 것:
    ① 거래구분 칸(채권·채무·수익·비용·매매거래 등)이 행마다 있는 표 — 검색어 줄 위 8줄 안의 거래구분 칸부터 다음 거래구분 칸·합계·주석 줄 앞까지
    ② 거래구분 칸이 합쳐진 표의 [당사자, 당사자, 금액, 계정과목] 행 — 검색어 줄 바로 위가 금액 칸, 그 위 두 줄이 당사자 칸 꼴
    ③ [당사자, 당사자, 계정과목, 금액] 행 — 검색어 줄 바로 아래가 금액 칸, 위 두 줄이 당사자 칸 꼴
    ④(검증 15차 g1 추가, 가장 먼저 봄) 표 머리가 [거래내용, 채권자·매도자, 채무자·매수자, 거래금액] 4칸(금액 뒤 칸 없음)인 표
       (KB) — 검색어 줄이 거래내용 칸이고 아래 두 줄이 당사자 칸, 그 다음 줄이 금액 칸. ②는 이 표에서 앞 행의 금액과 다음 행의
       거래내용을 한 행으로 잘못 묶었으므로 ④를 먼저 봄.
    (빈 줄 = 공백만 있는 표 칸은 건너뜀)"""
    if _label_first_header(lines, h):
        p1 = _nb(lines, h, 1, 3)
        p2 = _nb(lines, p1, 1, 3) if p1 is not None else None
        am = _nb(lines, p2, 1, 3) if p2 is not None else None
        if am is not None and _party(lines[p1]) and _party(lines[p2]) and AMT_RE.match(lines[am]):
            return h, am, "④"
    st, k = None, h
    for _ in range(9):
        if k is None:
            break
        if TOK_RE.match(lines[k]):
            st = k
            break
        if k < h and ROW_END_RE.match(lines[k]):
            break
        k = _nb(lines, k, -1, 3)
    if st is not None:
        en = st + 1
        while en < len(lines) and en - st < 10 and not TOK_RE.match(lines[en]) and not ROW_END_RE.match(lines[en]):
            en += 1
        if en > h:
            e = en - 1
            while e > h and not lines[e].strip():
                e -= 1
            return st, e, "①"
    up1 = _nb(lines, h, -1, 3)
    if up1 is not None and AMT_RE.match(lines[up1]):
        p2 = _nb(lines, up1, -1, 3)
        p1 = _nb(lines, p2, -1, 3) if p2 is not None else None
        if p1 is not None and all(_party(lines[x]) for x in (p1, p2)):
            return p1, h, "②"
    dn1 = _nb(lines, h, 1, 3)
    if dn1 is not None and AMT_RE.match(lines[dn1]):
        p2 = _nb(lines, h, -1, 3)
        p1 = _nb(lines, p2, -1, 3) if p2 is not None else None
        if p1 is not None and all(_party(lines[x]) for x in (p1, p2)):
            return p1, dn1, "③"
    return None


ROW_HOW = {"①": "거래구분 칸부터 다음 거래구분 칸 앞까지", "②": "거래구분 칸이 합쳐진 표의 [당사자, 당사자, 금액, 계정과목] 줄",
           "③": "[당사자, 당사자, 계정과목, 금액] 줄",
           "④": "머리가 [거래내용, 채권자·매도자, 채무자·매수자, 거래금액] 4칸인 표의 [거래내용, 당사자, 당사자, 금액] 줄"}
# (판단) 지주·계열사 사이 글이 아니라고 본 문장 — 검색어·계열사 낱말·지주 낱말이 한 문장에 있으나 뜻이 다른 것. 빼고 work 의
# D_제외문장.csv 에 남김. (공백 지운 글의 앞부분, 사유)
D_EXCLUDE = [
    ("신한리츠운용주식회사는", "자회사 소개 글 — 「위탁」은 부동산투자회사(REITs)가 그 자회사에 맡긴 업무(지주·계열사 사이 거래 아님)"),
    ("신한신용정보주식회사는", "자회사 소개 글 — 「용역」은 그 자회사가 하는 민원용역 대행 업무(지주·계열사 사이 거래 아님)"),
]


def _excluded(txt0):
    for k, why in D_EXCLUDE:
        if txt0.startswith(k) or k in txt0[:60]:
            return why
    return ""


# (검증 15차 g1 추가, 판단) 지주 이름은 없으나 계열사가 「그룹사」를 상대로 자문·용역 등을 준다는 글 — 지주가 「그룹사」에
# 드는지 원문에 없어 애매하므로 넣음(지시: 지주–계열사 사이인지 애매하면 넣고 note (판단)). (공백 지운 문장 정규식, contract_type 을
# 뽑는 원문 정규식(첫 묶음), note)
D_AMBIG_TERMS = ["자문", "위탁", "용역", "전산"]
D_AMBIG = [
    (r"그룹사(를)?상대로.*(자문|위탁|용역|전산).*제공", r"그룹사\s*상대로\s*([\s\S]+?)를\s*제공",
     "(판단) 계열사(문장 주어)가 「그룹사 상대로」 서비스를 제공한다는 자회사 소개 글 — 지주가 「그룹사」에 드는지는 원문에 없어 "
     "애매하므로 넣음; counterparty 는 문장 주어, contract_type 은 「그룹사 상대로」 뒤 「…를 제공」 앞 글(줄바꿈은 공백으로)"),
]
HOLD_CELL = {"KB금융지주":r"㈜?KB금융지주|케이비금융지주", "신한금융지주": r"신한금융지주(회사)?", "하나금융지주": r"하나금융지주",
             "우리금융지주": r"우리금융지주"}
SERIAL_RE = re.compile(r"^\s*\d{1,3}\s*$")


def joint_ad_rows(lines, co):
    """(검증 15차 g1 추가, 판단) 「공동광고 현황」 표에서 공동광고 회사명 칸(한 줄 전체)이 지주 이름인 행 →
    [(s, e, 행 첫 줄, 지주 말고 회사명 칸들)]. 행 = 연번 줄(숫자만, 다음 글 줄이 「20xx」로 시작)부터 다음 연번 줄 앞까지.
    s 는 표 제목 줄(「…공동광고 현황」, 없으면 「공동광고」가 든 가장 가까운 위 줄)이고, 거기서 행 끝까지 2,000자가 넘으면 행 첫 줄."""
    flat = [re.sub(r"\s", "", ln) for ln in lines]
    tops = [i for i, f in enumerate(flat) if "공동광고" in f]
    if not tops:
        return []
    t0 = next((i for i in tops if "공동광고현황" in flat[i]), tops[0])
    t1 = next((i for i in range(t0 + 1, len(lines)) if "시설물" in flat[i]), len(lines))
    cell = re.compile(r"^(%s)$" % HOLD_CELL[co])
    starts = [i for i in range(t0, t1) if SERIAL_RE.match(lines[i]) and
              (lambda nx: nx is not None and re.match(r"\s*20\d\d", lines[nx]))(_nb(lines, i, 1, 2))]
    out = []
    for i in range(t0, t1):
        if not cell.match(flat[i]):
            continue
        rs = max([x for x in starts if x < i], default=None)
        if rs is None:
            continue
        nxt = [x for x in starts if x > i]
        e = (nxt[0] - 1) if nxt else t1 - 1
        while e > i and not lines[e].strip():
            e -= 1
        heads = [x for x in tops if x <= rs]
        s = max([x for x in heads if "공동광고현황" in flat[x]] or heads or [rs])
        if len("\n".join(lines[s:e + 1])) > 2000:
            s = rs
        names = [flat[x] for x in range(rs, e + 1) if re.fullmatch(r"[가-힣A-Za-z&]{2,14}", flat[x])
                 and lines[x].strip() == flat[x] and not cell.match(flat[x]) and not re.search(r"홍보관|박람회|골프|광고|매체|대회", flat[x])]
        out.append((s, e, rs, names))
    return out


D_WIDER = ["자문", "공동"]


def _d_wider(rows):
    """(검증 15차 g1 추가) D 「문서에 없음」 반박 시도 — note 에 위치만 더함(행으로 넣지 않음).
    ① 더 넓은 검색어 「자문」「공동」이 지주 이름 앞뒤 3줄 안에 있는 쪽.
    ② 같은 회사의 다른 FY 3개 이상에서 거래 표 행 counterparty 였던 회사가 이 문서에서도 지주와 붙은 표 행으로 있는 곳(칸 글 그대로)."""
    cps = {}
    for r in rows:
        if r["source_text"] != NONE and r.get("counterparty"):
            cps.setdefault((r["corp_label"], r["counterparty"]), set()).add(r["fy"])
    for r in rows:
        pages = r.pop("_pages", None)
        if pages is None:
            continue
        co = r["corp_label"]
        hold = re.compile(HOLDCO[co])
        hits, same = {}, []
        for n, body in pages:
            lines = body.split("\n")
            flat = [re.sub(r"\s", "", ln) for ln in lines]
            for i, f in enumerate(flat):
                for w in D_WIDER:
                    if w in f and any(hold.search(x) for x in flat[max(0, i - 3):i + 4]):
                        hits.setdefault(w, set()).add(n)
            for (c2, cp), fys in sorted(cps.items()):
                if c2 != co or len(fys) < 3 or r["fy"] in fys:
                    continue
                for i, f in enumerate(flat):
                    if f != re.sub(r"\s", "", cp):
                        continue
                    j = _nb(lines, i, 1, 2)
                    if j is None or not hold.search(flat[j]):
                        continue
                    a = _nb(lines, j, 1, 3)
                    if a is None or not AMT_RE.match(lines[a]):
                        continue
                    b = _nb(lines, a, 1, 3)
                    same.append("p.%d 「%s」·「%s」·금액 칸 「%s」·다음 칸 「%s」(다른 FY %s 에 행이 있던 상대방)"
                                % (n, lines[i].strip(), lines[j].strip(), lines[a].strip(),
                                   lines[b].strip() if b is not None else "", "·".join(sorted(fys))))
        add = ["더 넓은 검색어 「자문」「공동」(지주 이름 앞뒤 3줄 안 — 쪽 머리글의 지주 이름 포함)으로도 찾음 — 찾은 곳: %s"
               % (" · ".join("%s p.%s" % (w, _ranges(ns)) for w, ns in hits.items()) or "없음")
               + ("; (판단) 원문을 보니 연혁·회계정책(관계기업 및 공동기업)·자회사끼리의 공동이용 표 등이라 지주가 당사자인 "
                  "업무위탁·용역·공동사용 글이 아님" if hits else "")]
        if same:
            add.append("같은 상대방 표 행: %s — 이 칸들에 검색어가 없어 행으로 넣지 않음(위치·칸 글만)" % " ; ".join(same[:4]))
        r["note"] = "; ".join([r["note"]] + add)


def extract_D(docs, sect):
    rows, excl = [], []
    for co, fy, r, t in docs:
        pages = load_pages(t["text_path"])
        base, common = _base(co, fy, r, t), _common(co, fy, t, pages)
        hold = re.compile(HOLDCO[co])
        seen, mine = {}, []
        for n, body in pages:
            lines = body.split("\n")
            for term, a, b in find_terms(lines, D_TERMS):
                tr = table_row(lines, a)
                if tr:
                    s, e, how = tr
                    cells = [x.strip() for x in lines[s:e + 1] if x.strip()]
                    body_c = cells[1:] if how in ("①", "④") else cells
                    nonamt = [x for x in body_c if not AMT_RE.match(x)]
                    parties = nonamt[:2]
                    if not any(hold.search(re.sub(r"\s", "", x)) for x in parties):
                        if any(hold.search(re.sub(r"\s", "", x)) for x in cells):
                            excl.append(dict(co=co, fy=fy, page="p.%d" % n, term=term, how=how,
                                             text="\n".join(lines[s:e + 1]).strip(),
                                             why="표 행에 지주 이름이 있으나 당사자 칸(앞 두 칸)이 아님"))
                        continue
                    ctl = [cells[0]] if how == "④" else [x for x in nonamt[2:]]
                    ct = "\n".join(ctl) if any(term in re.sub(r"\s", "", x) for x in ctl) else ""
                    amts = [x for x in body_c if AMT_RE.match(x)]
                    others = [x for x in parties if not hold.search(re.sub(r"\s", "", x))]
                    extra = {"counterparty": others[0] if len(others) == 1 else "", "contract_type": ct,
                             "amount": amts[0] if len(amts) == 1 else ""}
                    xn = ["(판단) 표 행 %s = %s(PDF 줄 그대로); counterparty 는 지주가 아닌 당사자 칸, contract_type 은 "
                          "검색어가 든 %s 칸(줄이 나뉜 칸은 줄바꿈 그대로), amount 는 금액 칸(원문 글 그대로)"
                          % (how, ROW_HOW[how], "거래내용" if how == "④" else "계정과목·비고")]
                    if cells and how == "①":
                        xn.append("거래구분 칸 「%s」" % cells[0])
                    if how == "④":
                        xn.append("표 머리 「거래내용 / 채권자, 매도자 등 / 채무자, 매수자 등 / 거래금액」 순서대로 읽음(검증 15차 g1: "
                                  "전에는 ②로 읽어 앞 행의 금액·당사자와 다음 행의 거래내용을 한 행으로 묶었던 것을 고침)")
                    if len(others) != 1:
                        xn.append("상대방 칸을 하나로 못 정해 counterparty 비움")
                    if not ct:
                        xn.append("검색어가 계정과목·비고 칸 밖에 있어 contract_type 비움")
                else:
                    s, e, kind = unit(lines, a, b)
                    txt0 = re.sub(r"\s", "", " ".join(lines[s:e + 1]))
                    if kind == "cell":
                        if not hold.search(txt0):
                            continue
                        xn = ["(판단) 거래 표 행 꼴이 아닌 표 칸·짧은 줄 — 검색어 줄의 앞뒤 2줄까지 이어 옮김(지주 이름이 그 안에 있음)"]
                    else:
                        if not (AFFIL.search(txt0) or "금융지주회사등" in txt0) or not re.search(PROSE_HOLD + "|" + HOLDCO[co], txt0):
                            continue
                        why = _excluded(txt0)
                        if why:
                            excl.append(dict(co=co, fy=fy, page="p.%d" % n, term=term, how="문장",
                                             text="\n".join(lines[s:e + 1]).strip(), why=why))
                            continue
                        xn = ["(판단) 검색어 「%s」와 계열사 낱말(자회사·손자회사·계열사·그룹사·금융지주회사등)과 지주 낱말(지주·당사·"
                              "당그룹·회사 이름)이 한 문장에 있음" % term]
                        if "금융지주회사등은" in txt0 and "대통령령으로" in txt0:
                            xn.append("(판단) 법 조문을 옮긴 글(경영공시의 관련 법규 부분)")
                    extra = {"counterparty": "", "contract_type": "", "amount": ""}
                raw = "\n".join(lines[s:e + 1]).strip()
                txt, cut = clean(raw)
                key = re.sub(r"\s", "", txt)
                if key in seen:
                    if ("p.%d" % n) != seen[key]["page"] and ("p.%d" % n) not in seen[key]["_also"]:
                        seen[key]["_also"].append("p.%d" % n)
                    continue
                notes = [common, "검색어 「%s」" % term] + xn + (["제어문자 지움"] if cut else [])
                row = dict(base, source_text=txt, page="p.%d" % n, _notes=notes, _also=[], **extra)
                seen[key] = row
                mine.append(row)
                sect.setdefault(("D", co, fy), set()).add(n)
            for term, a, b in find_terms(lines, D_AMBIG_TERMS):
                s, e, kind = unit(lines, a, b)
                raw = "\n".join(lines[s:e + 1]).strip()
                txt0 = re.sub(r"\s", "", raw)
                hit = next(((rx, cap, why) for rx, cap, why in D_AMBIG if re.search(rx, txt0)), None)
                if not hit:
                    continue
                txt, cut = clean(raw)
                key = re.sub(r"\s", "", txt)
                if key in seen:
                    continue
                subj = re.match(r"\s*([^\s]+?)는\s", txt)
                ctm = re.search(hit[1], txt)
                notes = [common, "검색어 「%s」(검증 15차 g1 에서 「%s」 grep 으로 찾아 넣음)" % (term, term), hit[2]] \
                    + (["제어문자 지움"] if cut else [])
                row = dict(base, source_text=txt, page="p.%d" % n, _notes=notes, _also=[],
                           counterparty=subj.group(1) if subj else "",
                           contract_type=re.sub(r"\s+", " ", ctm.group(1)).strip() if ctm else "", amount="")
                seen[key] = row
                mine.append(row)
                sect.setdefault(("D", co, fy), set()).add(n)
            for s, e, rs, names in joint_ad_rows(lines, co):
                raw = "\n".join(lines[s:e + 1]).strip()
                txt, cut = clean(raw)
                key = re.sub(r"\s", "", txt)
                if key in seen:
                    continue
                notes = [common, "검색어 「공동」(표 「공동광고 현황」 — 검증 15차 g1 에서 「공동」 grep 으로 찾아 넣음)",
                         "(판단) 「공동광고 현황」 표의 한 행 — 공동광고 회사명 칸에 지주 이름이 있어 넣음. 「공동광고」가 업무위탁·용역·"
                         "공동사용 가운데 무엇인지는 원문에 없음(같은 문서의 금융지주회사법 조문 「④ 금융지주회사등은 … 공동광고를 하거나 … "
                         "공동사용할 수 있다」 행과 함께 봄)",
                         ("표 제목 줄부터 그 행 끝까지 PDF 줄 그대로 이어 옮김(사이의 앞 행은 지주가 없는 행이나 이어진 글이라 함께 옮김)"
                          if s < rs else "그 행만 PDF 줄 그대로 옮김(표 제목 「공동광고 현황」은 같은 쪽 위)"),
                         "공동광고 회사명 칸(지주 말고): %s — 여럿이라 counterparty 비움" % "·".join(names)] \
                    + (["제어문자 지움"] if cut else [])
                row = dict(base, source_text=txt, page="p.%d" % n, _notes=notes, _also=[], counterparty="",
                           contract_type="공동광고", amount="")
                seen[key] = row
                mine.append(row)
                sect.setdefault(("D", co, fy), set()).add(n)
        for row in mine:
            if row["_also"]:
                row["_notes"].insert(1, "같은 글이 %s 에도 있음(한 번만 옮김)" % ",".join(row["_also"]))
            row["note"] = "; ".join(row.pop("_notes"))
            row.pop("_also")
        if not mine:
            gn = _garble_note(pages)
            mine.append(dict(base, counterparty="", contract_type="", amount="", source_text=NONE,
                             page="p.1~p.%d(경영공시 전체 — 찾은 범위)" % len(pages),
                             note="; ".join([common, "찾은 범위: FY%d 경영공시 전체 %d쪽(글자 없는 쪽 %s%s) · 검색어 %s"
                                                     "(공백·줄바꿈 무시) · 지주가 당사자인 거래 표 행이나 지주·계열사 사이 문장 없음"
                                             % (fy, len(pages), (t["empty_pages"] + " — 그림이라 찾지 못함")
                                                if t.get("empty_pages") else "없음",
                                                (" · 글자층 깨진 쪽 %s — 낱말을 찾을 수 없음" % gn) if gn else "",
                                                "·".join(D_TERMS))]
                                            + _none_hint(co, fy, excl)),
                             _pages=pages))
        rows.extend(mine)
    _d_wider(rows)
    with open(os.path.join(WORK, "D_제외문장.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["co", "fy", "page", "term", "how", "text", "why"], lineterminator="\n")
        w.writeheader()
        w.writerows(excl)
    return rows


def _none_hint(co, fy, excl):
    x = [e for e in excl if e["co"] == co and e["fy"] == fy]
    if not x:
        return []
    return ["(판단) 뺀 글 %d곳(%s) — %s/D_제외문장.csv" % (len(x), ",".join(sorted({e["page"] for e in x})), WORK)]


def write_frag(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    os.replace(path + ".tmp", path)


def write_orig(sect, docs):
    """원문 md: dart_out/ops15/원문/<B|D>/<회사>__FY<fy>__경영공시.md — 머리 출처 줄 + 행이 나온 쪽 글 그대로(같은 쪽은 한 번)."""
    dmap = {(co, fy): (r, t) for co, fy, r, t in docs}
    for task in ("B", "D"):
        d0 = os.path.join(ORIG, task)
        os.makedirs(d0, exist_ok=True)
        for fn in os.listdir(d0):     # 이 스크립트 몫(g1 4개사 FY 경영공시)만 지우고 다시 씀
            if re.fullmatch(r"(%s)__FY20\d\d__경영공시\.md" % "|".join(COS), fn):
                os.remove(os.path.join(d0, fn))
    n = 0
    for (task, co, fy), pgs in sorted(sect.items(), key=lambda x: (x[0][0], COS.index(x[0][1]), x[0][2])):
        r, t = dmap[(co, fy)]
        pages = dict(load_pages(t["text_path"]))
        out = ["# %s FY%d 경영공시 — 작업 %s 원문(행이 나온 쪽 전체)" % (co, fy, task), "",
               "- 출처: 「%s」 · %s · 받은 시각 %s(KST) · 원본 sha256 %s" % (r["title"], r["url"], r["fetched_at"], r["sha256"]),
               "- 글: `%s`(pymupdf page.get_text() 그대로) — 쪽 「## p.N」= PDF 쪽" % t["text_path"], ""]
        for p in sorted(pgs):
            out.append("## p.%d" % p)
            out.append("")
            out.append(pages[p].rstrip("\n"))
            out.append("")
        with open(os.path.join(ORIG, task, "%s__FY%d__경영공시.md" % (co, fy)), "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        n += 1
    return n


def cmd_extract():
    docs = docs_for_extract()
    sect = {}
    B = extract_B(docs, sect)
    D = extract_D(docs, sect)
    write_frag(os.path.join(FRAG, "B_mgmt_g1.csv"), B, B_COLS)
    write_frag(os.path.join(FRAG, "D_mgmt_g1.csv"), D, D_COLS)
    n = write_orig(sect, docs)
    print("docs", len(docs), "B", len(B), "B 없음", sum(r["source_text"] == NONE for r in B),
          "D", len(D), "D 없음", sum(r["source_text"] == NONE for r in D), "원문 md", n)


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
    if cmd == "extract":
        cmd_extract()
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
