# -*- coding: utf-8 -*-
"""15차 — 지배구조 및 보수체계 연차보고서(그룹 g1: KB·신한·하나·우리·NH농협) 과거 연도(공시연도 2020~2024) 수집.

    python -I scripts/dart/ops15_gov_g1.py robots     # 호스트마다 robots.txt 받아 판정(RFC 9309) → 작업 기록
    python -I scripts/dart/ops15_gov_g1.py get URL [저장이름]  # (탐색용) robots 허용이면 받아 저장

HTTP 는 scripts/dart/web13.py 의 Web(=web9.Web: UA 고정·1.2초 간격·3회 재시도)·Robots(RFC 9309 판정) 를 쓰고,
저장 위치만 dart_out/raw/governance15/<회사>/ 로 바꾼다(web13.RAW 를 쓰지 않음).
robots.txt 가 막는 경로는 받지 않고 사유를 남긴다(우회 없음). API 키 쓰지 않음.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))
os.chdir(ROOT)
import web10  # noqa: E402
import web13  # noqa: E402
from web13 import Web, now  # noqa: E402

RAW = os.path.join("dart_out", "raw", "governance15")
WORK = os.path.join("dart_out", "ops15", "gov15_g1_work")

HOSTS = {
    "KB금융지주": ["https://www.kbfg.com"],
    "신한금융지주": ["https://www.shinhangroup.com"],
    "하나금융지주": ["https://www.hanafn.com", "https://www.hanafn.com:8002"],
    "우리금융지주": ["https://www.woorifg.com"],
    "NH농협금융지주": ["https://www.nhfngroup.com"],
}


def save(co, name, body, meta):
    """원본 바이트를 dart_out/raw/governance15/<co>/<name> 에, 메타는 같은 이름 + .meta.json."""
    d = os.path.join(RAW, co)
    p = os.path.join(d, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


class Robots(web13.Robots):
    """web10.Robots 판정 그대로, robots.txt 원본만 dart_out/raw/governance15/<co>/ 에 저장."""

    def __init__(self, web, base, co):
        _save = web10.save
        web10.save = save
        try:
            web10.Robots.__init__(self, web, base, co)
        finally:
            web10.save = _save


def robots_all():
    w = Web()
    out = {}
    for co, bases in HOSTS.items():
        for b in bases:
            r = Robots(w, b, co)
            host = urllib.parse.urlparse(b).netloc
            out[host] = dict(co=co, base=b, status=r.status, note=r.note, checked_at=now())
            print(co, host, r.status, r.note[:120])
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "robots.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


_ROBOTS = {}


def robots_for(w, url, co):
    pu = urllib.parse.urlparse(url)
    base = "%s://%s" % (pu.scheme, pu.netloc)
    if base not in _ROBOTS:
        _ROBOTS[base] = Robots(w, base, co)
    return _ROBOTS[base]


_WEB = None


def web():
    global _WEB
    if _WEB is None:
        _WEB = Web()
    return _WEB


def fetch(co, url, name, referer="", data=None, headers=None, extra=None):
    """robots 허용일 때만 받는다. 저장: dart_out/raw/governance15/<co>/<name>(+.meta.json). (path, meta) 또는 예외."""
    w = web()
    r = robots_for(w, url, co)
    if not r.allowed(url):
        raise PermissionError("robots 불허(%s): %s" % (r.status, url))
    fu, st, hd, b = w.get(url, referer=referer, data=data, headers=headers)
    meta = dict(url=url, 최종URL=fu, http=st, content_type=hd.get("Content-Type", ""),
                content_disposition=hd.get("Content-Disposition", ""), referer=referer,
                post=(data if isinstance(data, dict) else ""), fetched_at=now(), robots=r.status)
    meta.update(extra or {})
    return save(co, name, b, meta)


def kb_list():
    """KB 이사회공시 게시판(bulbdId=6, /kor/about/governance/board-directors/list.htm) 전 쪽 → 연차보고서 글."""
    co, board = "KB금융지주", "https://www.kbfg.com/kor/about/governance/board-directors/list.htm"
    out, page, total = [], 1, 1
    while page <= total:
        url = "https://www.kbfg.com/api/kbfg/posts?bulbdId=6&page=%d&pageSize=10" % page
        p, m = fetch(co, url, os.path.join("pages", "kb_posts_b6_p%d.json" % page), referer=board)
        d = json.load(open(p, encoding="utf-8"))["result"]
        total = d["paging"]["totalPageCount"]
        for x in d["posts"]:
            files = x.get("files") or []
            out.append(dict(bltcId=x["bltcId"], titl=x["titl"], rgcrYms=x["rgcrYms"], rsrvYms=x.get("rsrvYms"),
                            tgtYr=x.get("tgtYr"), pdfFileId=x.get("pdfFileId"),
                            files=[dict((k, f.get(k)) for k in ("fileId", "fileNm", "orglFileNm", "fileTyp", "fileSize",
                                                                   "rgcrYms", "dataTyp") if k in f)
                                   for f in files] if isinstance(files, list) else str(files)[:300],
                            board=board, list_url=url, list_fetched_at=m["fetched_at"]))
        page += 1
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "kb_board6_all.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    hits = [x for x in out if "연차보고서" in x["titl"] or "지배구조" in x["titl"] and "보수" in x["titl"]]
    with open(os.path.join(WORK, "kb_board6_annual.json"), "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)
    for x in hits:
        print(x["bltcId"], x["rgcrYms"][:10], x["pdfFileId"], x["titl"][:70])


def sh_list(years=range(2019, 2026)):
    """신한 지배구조 공시(/kr/governance/director/disclosure) — POST /api/v1/governance/council_disclosure/list, 연도별."""
    co, board = "신한금융지주", "https://www.shinhangroup.com/kr/governance/director/disclosure"
    api = "https://www.shinhangroup.com/api/v1/governance/council_disclosure/list"
    out = []
    for y in years:
        page, last = 1, 1
        while page <= last:
            body = {"pageType": "FRONT", "lang": "KOR", "current": str(page), "year": str(y)}
            p, m = fetch(co, api, os.path.join("pages", "sh_council_%d_p%d.json" % (y, page)), referer=board, data=body)
            d = json.load(open(p, encoding="utf-8"))["result"]
            last = d.get("last") or 1
            for x in d["list"]:
                out.append(dict(year=y, title=x.get("title"), baseDt=x.get("baseDt"), fileList=x.get("fileList"),
                                board=board, list_url=api, list_post=body, list_fetched_at=m["fetched_at"]))
            page += 1
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "sh_council_all.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for x in out:
        if "연차보고서" in (x["title"] or ""):
            print(x["year"], x["baseDt"], x["title"][:70], [fl.get("originalFileName") for fl in x["fileList"] or []])


def _strip(s):
    import html as _h
    import re as _re
    return _h.unescape(_re.sub(r"<[^>]+>", "", s or "")).strip()


def hana_list(maxpage=30, stop_before="2019.01.01"):
    """하나 지배구조 공시(/governance/disclosure.do) — POST pageNo=N 으로 쪽을 넘김."""
    import re as _re
    co, board = "하나금융지주", "https://www.hanafn.com/governance/disclosure.do"
    out = []
    for page in range(1, maxpage + 1):
        body = {"pageNo": str(page)}
        p, m = fetch(co, board, os.path.join("pages", "hana_disclosure_p%d.html" % page), referer=board, data=body)
        h = open(p, encoding="utf-8", errors="replace").read()
        rows = _re.findall(r'<li role="row">(.*?)</li>', h, _re.S)
        got = 0
        for r in rows:
            cells = _re.findall(r'<div role="cell" class="([^"]*)">(.*?)</div>', r, _re.S)
            c = {k: v for k, v in cells}
            num = _strip(c.get("hide", ""))
            title = _strip(c.get("left title", ""))
            date = _strip(c.get("sub", ""))
            dl = _re.findall(r"downloadFile\('([^']+)'\)", r)
            fn = _re.findall(r'download title="([^"]*)"', r)
            if not title:
                continue
            got += 1
            out.append(dict(num=num, title=title, date=date, file_urls=dl, file_titles=fn, board=board,
                            list_url=board, list_post=body, list_fetched_at=m["fetched_at"]))
        if not got or (out and out[-1]["date"] and out[-1]["date"] < stop_before):
            break
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "hana_disclosure_all.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for x in out:
        if "연차보고서" in x["title"]:
            print(x["num"], x["date"], x["title"][:70], x["file_urls"][:1])


def woori_list(maxpage=10):
    """우리 이사회 공시(/kor/corp-governance/governance-structure/list.do) — GET pageIndex=N."""
    import re as _re
    co = "우리금융지주"
    base = "https://www.woorifg.com/kor/corp-governance/governance-structure/list.do"
    out = []
    for page in range(1, maxpage + 1):
        url = base + "?pageIndex=%d&f=&q=" % page
        p, m = fetch(co, url, os.path.join("pages", "woori_gov_list_p%d.html" % page), referer=base)
        h = open(p, encoding="utf-8", errors="replace").read()
        blocks = h.split('<div class="list">')[1:]
        got = 0
        for b in blocks:
            t = _re.search(r'<a href="\./view\.do\?seq=(\d+)[^"]*">(.*?)</a>', b, _re.S)
            if not t:
                continue
            got += 1
            tip = _re.search(r'<div class="tooltip">(.*?)</div>', b, _re.S)
            fl = _re.findall(r'href="(/cmm/fms/FileDown\.do\?[^"]+)"', b)
            dt = _re.search(r'<div class="date[^"]*">\s*([0-9.]+)\s*</div>', b)
            out.append(dict(seq=t.group(1), title=_strip(t.group(2)), tooltip=_strip(tip.group(1) if tip else ""),
                            files=[("https://www.woorifg.com" + _strip(x)) for x in fl], date=dt.group(1) if dt else "",
                            view_url="https://www.woorifg.com/kor/corp-governance/governance-structure/view.do?seq=%s" % t.group(1),
                            board=base, list_url=url, list_fetched_at=m["fetched_at"]))
        if not got:
            break
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "woori_gov_all.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for x in out:
        if "연차보고서" in x["title"]:
            print(x["seq"], x["date"], x["title"][:70], len(x["files"]))


YEARS = range(2020, 2025)          # 공시연도 2020~2024 = FY2019~FY2023


def kind_of(title):
    t = title or ""
    if "재공시" in t:
        return "재공시"
    if "정정" in t:
        return "정정공시"
    if "추가" in t:
        return "추가공시"
    return "본공시"


def candidates():
    """게시판 목록(작업 기록 JSON·저장한 목록 응답)에서 공시연도 2020~2024 연차보고서 글 → 받을 파일 목록."""
    import glob
    import re as _re
    out = []
    # KB — 저장한 목록 응답(kb_posts_b6_pN.json)에서 직접(dataTyp 필요)
    board = "https://www.kbfg.com/kor/about/governance/board-directors/list.htm"
    seen = set()
    for fp in sorted(glob.glob(os.path.join(RAW, "KB금융지주", "pages", "kb_posts_b6_p[0-9]*.json"))):
        if fp.endswith(".meta.json"):
            continue
        meta = json.load(open(fp + ".meta.json", encoding="utf-8"))
        for x in json.load(open(fp, encoding="utf-8"))["result"]["posts"]:
            t = x["titl"]
            if "연차보고서" not in t or x["bltcId"] in seen:
                continue
            seen.add(x["bltcId"])
            y = int(x["rgcrYms"][:4])
            if y not in YEARS:
                continue
            for f in x.get("files") or []:
                if f.get("dataTyp") == "migration":
                    url = "https://www.kbfg.com/common/jsp/fileDownUtil.jsp?filepath=" + urllib.parse.quote(f["fileNm"])
                else:
                    url = "https://www.kbfg.com/api/download/board/%s" % f["fileId"]
                out.append(dict(회사="KB금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t, 게시판_url=board,
                                게시글="bltcId=%s" % x["bltcId"], 파일_url=url, 공시일=x["rgcrYms"][:10],
                                목록_파일명=f.get("orglFileNm"), 목록_크기=f.get("fileSize"), referer=board,
                                목록_url=meta["url"], 목록_fetched_at=meta["fetched_at"]))
    # 신한
    for x in json.load(open(os.path.join(WORK, "sh_council_all.json"), encoding="utf-8")):
        t = x["title"] or ""
        y = int(x["baseDt"][:4])
        if "연차보고서" not in t or y not in YEARS:
            continue
        for f in x["fileList"] or []:
            url = "https://www.shinhangroup.com/main/downloadAttach?attachNo=%s&seq=%s" % (f["attachNo"], f["fileSeq"])
            out.append(dict(회사="신한금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t, 게시판_url=x["board"],
                            게시글="year=%s" % x["year"], 파일_url=url, 공시일=x["baseDt"].replace(".", "-"),
                            목록_파일명=f.get("originalFileName"), 목록_크기="", referer=x["board"],
                            목록_url=x["list_url"], 목록_fetched_at=x["list_fetched_at"]))
    # 하나
    for x in json.load(open(os.path.join(WORK, "hana_disclosure_all.json"), encoding="utf-8")):
        t = x["title"]
        y = int(x["date"][:4])
        if "연차보고서" not in t or y not in YEARS:
            continue
        for u, fn in zip(x["file_urls"], x["file_titles"] or [""] * len(x["file_urls"])):
            url = urllib.parse.urljoin("https://www.hanafn.com/", u)
            out.append(dict(회사="하나금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t, 게시판_url=x["board"],
                            게시글="num=%s" % x["num"], 파일_url=url, 공시일=x["date"].replace(".", "-"),
                            목록_파일명=fn, 목록_크기="", referer=x["board"],
                            목록_url=x["list_url"] + " (POST pageNo=%s)" % x["list_post"]["pageNo"],
                            목록_fetched_at=x["list_fetched_at"]))
    # 우리
    for x in json.load(open(os.path.join(WORK, "woori_gov_all.json"), encoding="utf-8")):
        t = x["title"]
        y = int(x["date"][:4])
        if "연차보고서" not in t or y not in YEARS:
            continue
        for u in x["files"]:
            out.append(dict(회사="우리금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t, 게시판_url=x["board"],
                            게시글=x["view_url"], 파일_url=u, 공시일=x["date"].replace(".", "-"),
                            목록_파일명=(_re.search(r"saveFileNm=([^&]+)", u) or [None, ""])[1], 목록_크기="",
                            referer=x["list_url"], 목록_url=x["list_url"], 목록_fetched_at=x["list_fetched_at"]))
    with open(os.path.join(WORK, "candidates.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for c in out:
        print(c["회사"], c["공시연도"], c["공시유형"], c["공시일"], c["파일_url"][-60:])
    return out


def _cd_name(cd):
    """Content-Disposition 의 파일 이름(있으면). RFC 5987 filename* 우선, 아니면 filename(UTF-8/EUC-KR 추정)."""
    import re as _re
    if not cd:
        return ""
    m = _re.search(r"filename\*\s*=\s*([^']*)'[^']*'([^;]+)", cd)
    if m:
        return urllib.parse.unquote(m.group(2).strip().strip('"'), encoding=m.group(1) or "utf-8")
    m = _re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
    if not m:
        return ""
    v = m.group(1).strip()
    if "%" in v:
        try:
            return urllib.parse.unquote(v, encoding="utf-8", errors="strict")
        except Exception:                                # noqa: BLE001
            pass
    # http.client 는 머리글을 latin-1 로 읽는다. 서버가 UTF-8 을 두 번 감싼 경우(우리금융지주)도 있어 되풀이해 푼다.
    for _ in range(3):
        try:
            raw = v.encode("latin-1")
        except UnicodeEncodeError:
            break
        nv = None
        for enc in ("utf-8", "cp949"):
            try:
                nv = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if nv is None or nv == v:
            break
        v = nv
    return v


def _safe(name):
    import re as _re
    name = name.replace("/", "_").replace("\\", "_").replace("\x00", "").strip()
    name = _re.sub(r'[<>:"|?*\r\n\t]', "_", name)
    return name[:180] or "file.pdf"


def download():
    """candidates.json 의 파일을 받는다(robots 허용일 때만). 하나 :8002 는 이 환경 릴레이가 끊어 포트를 뗀 443 으로."""
    cands = json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))
    res = []
    for c in cands:
        co = c["회사"]
        urls = [c["파일_url"]]
        pu = urllib.parse.urlparse(c["파일_url"])
        if pu.port:
            urls.append(urllib.parse.urlunparse(pu._replace(netloc=pu.hostname)))
        rec = dict(c, 실제_url="", http="", 크기="", sha256="", 저장경로="", fetched_at="", 실패사유="", content_type="")
        errs = []
        for u in urls:
            w = web()
            r = robots_for(w, u, co)
            if not r.allowed(u):
                errs.append("%s: robots %s — 받지 않음" % (u, r.status))
                continue
            try:
                fu, st, hd, b = w.get(u, referer=c["referer"])
            except Exception as e:                       # noqa: BLE001
                errs.append("%s: %s: %s" % (u, type(e).__name__, str(e)[:150]))
                continue
            name = _cd_name(hd.get("Content-Disposition", "")) or c["목록_파일명"] or ("%s_%s_%s.pdf" % (co, c["공시연도"], c["공시유형"]))
            name = _safe(name)
            if not name.lower().endswith(".pdf"):
                name += ".pdf" if b[:4] == b"%PDF" else ""
            if os.path.exists(os.path.join(RAW, co, name)):
                prev = json.load(open(os.path.join(RAW, co, name + ".meta.json"), encoding="utf-8"))
                if prev.get("url") != u:
                    name = "%s__%s_%s" % (c["공시연도"], c["공시유형"], name)
            meta = dict(url=u, 목록_파일_url=c["파일_url"], 최종URL=fu, 게시판_url=c["게시판_url"], 게시글=c["게시글"],
                        제목=c["제목"], 공시일=c["공시일"], 공시연도=c["공시연도"], 공시유형=c["공시유형"], http=st,
                        content_type=hd.get("Content-Type", ""), content_disposition=hd.get("Content-Disposition", ""),
                        목록_파일명=c["목록_파일명"], 목록_크기=c["목록_크기"], referer=c["referer"],
                        robots=r.status, fetched_at=now())
            p, m = save(co, name, b, meta)
            rec.update(실제_url=u, http=st, 크기=len(b), sha256=m["sha256"], 저장경로=p, fetched_at=meta["fetched_at"],
                       content_type=meta["content_type"])
            if b[:4] != b"%PDF":
                rec["실패사유"] = "받은 내용이 PDF 가 아님(%s, %d bytes)" % (meta["content_type"], len(b))
            if u != c["파일_url"]:
                rec["실패사유"] = (rec["실패사유"] + " " if rec["실패사유"] else "") + "(판단) 목록 URL(%s) 은 이 환경 릴레이가 비표준 포트 터널을 끊어 실패 — 같은 서버 443 의 같은 경로로 받음" % c["파일_url"]
            break
        if not rec["저장경로"]:
            rec["실패사유"] = " / ".join(errs)
        rec["시도"] = errs
        res.append(rec)
        print(co, c["공시연도"], c["공시유형"], rec["http"], rec["크기"], os.path.basename(rec["저장경로"])[:60], rec["실패사유"][:80])
    with open(os.path.join(WORK, "download.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


def fixnames():
    import glob
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    for mp in [x for co in HOSTS for x in glob.glob(os.path.join(RAW, co, "*.meta.json"))]:   # g1 회사 폴더만
        m = json.load(open(mp, encoding="utf-8"))
        if "content_disposition" not in m or not m.get("공시연도"):
            continue
        old = mp[:-len(".meta.json")]
        nm = _cd_name(m["content_disposition"])
        if not nm:
            continue
        nm = _safe(nm)
        cur = os.path.basename(old)
        pre = ""
        if cur.startswith("%s__%s_" % (m["공시연도"], m["공시유형"])):
            pre = "%s__%s_" % (m["공시연도"], m["공시유형"])
        new = os.path.join(os.path.dirname(old), pre + nm)
        if new == old:
            continue
        os.rename(old, new)
        m["저장경로"] = new
        os.remove(mp)
        with open(new + ".meta.json", "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)
        for r in dl:
            if r["저장경로"] == old:
                r["저장경로"] = new
        print("rename", cur[:40], "->", os.path.basename(new))
    with open(os.path.join(WORK, "download.json"), "w", encoding="utf-8") as f:
        json.dump(dl, f, ensure_ascii=False, indent=1)


TEXT = os.path.join("dart_out", "text", "ops15")


def to_text():
    """받은 PDF → 쪽 텍스트 md(「## p.N」 = PDF 쪽, page.get_text() 그대로; 글자 없는 쪽은 「## p.N (글자 없음)」)."""
    import pymupdf
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    os.makedirs(TEXT, exist_ok=True)
    for r in dl:
        r["쪽수"], r["글자없는쪽"], r["text_path"] = "", "", ""
        if not r["저장경로"] or not os.path.exists(r["저장경로"]):
            continue
        with open(r["저장경로"], "rb") as f:
            if f.read(4) != b"%PDF":
                continue
        doc = pymupdf.open(r["저장경로"])
        tp = os.path.join(TEXT, "연차보고서__%s__%s__%s.md" % (r["회사"], r["공시연도"], r["공시유형"]))
        empty = []
        with open(tp + ".part", "w", encoding="utf-8") as f:
            f.write("# 연차보고서 %s 공시연도 %s %s\n\n" % (r["회사"], r["공시연도"], r["공시유형"]))
            f.write("- 제목: %s\n- 파일: %s\n- 파일 url: %s\n- 게시판: %s\n- 공시일: %s\n- sha256: %s\n- 받은 시각: %s\n"
                    "- 변환: pymupdf %s page.get_text() 그대로, 「## p.N」= PDF 쪽 순번\n\n"
                    % (r["제목"], os.path.basename(r["저장경로"]), r["실제_url"], r["게시판_url"], r["공시일"],
                       r["sha256"], r["fetched_at"], pymupdf.VersionBind))
            for i, pg in enumerate(doc, 1):
                t = pg.get_text()
                if not t.strip():
                    empty.append(i)
                    f.write("## p.%d (글자 없음)\n\n" % i)
                else:
                    f.write("## p.%d\n\n%s\n" % (i, t.rstrip("\n") + "\n"))
        os.replace(tp + ".part", tp)
        r["쪽수"], r["글자없는쪽"], r["text_path"] = doc.page_count, ",".join(map(str, empty)), tp
        print(r["회사"], r["공시연도"], r["공시유형"], doc.page_count, "빈쪽", len(empty), tp[-60:])
    with open(os.path.join(WORK, "download.json"), "w", encoding="utf-8") as f:
        json.dump(dl, f, ensure_ascii=False, indent=1)


ROBOTS_NOTE = {
    "KB금융지주": "https://www.kbfg.com/robots.txt HTTP 200 「User-agent: * / Allow:/」 → 허용",
    "신한금융지주": ("https://www.shinhangroup.com/robots.txt HTTP 200 「User-agent: *」 그룹 Allow:/ (Disallow 는 /front/asis/, "
                "/front/kr/governance/etc/sh_evalution.jsp 뿐) → 받은 경로(/api/v1/governance/council_disclosure/list, "
                "/main/downloadAttach) 허용"),
    "하나금융지주": ("https://www.hanafn.com/robots.txt HTTP 404 → RFC 9309 §2.3.1.3 제한 없음. 목록의 :8002 주소는 "
                "https://www.hanafn.com:8002/robots.txt 가 접속 실패(이 환경 릴레이가 비표준 포트 터널을 끊음: "
                "ws_closed_mid_exchange) → :8002 에서는 받지 않고 같은 서버 443 의 같은 경로로 받음 (판단)"),
    "우리금융지주": ("https://www.woorifg.com/robots.txt HTTP 200 「User-agent: * / Allow: /」(Yeti 에만 한 경로 Disallow) → 허용 "
                "(legacy TLS 재협상 허용 OpenSSL 설정으로 접속 — 인증서 검증은 그대로)"),
    "NH농협금융지주": ("https://www.nhfngroup.com/robots.txt HTTP 400 「Request Blocked」 → RFC 9309 상으로는 제한 없음이나, 첫 화면·"
                  "경영공시 화면·6차에 받은 파일 URL 까지 이 환경의 모든 요청이 HTTP 400 「Request Blocked」"),
}
TERMS_NOTE = {
    "KB금융지주": ("첫 화면(/kor/index.jsp) 하단 정책 링크는 개인정보처리방침·고객정보취급방침·신용정보활용체제뿐 — "
                "이용약관·저작권정책 쪽 없음, 자동 수집 금지 문구 확인 안 됨 (판단)"),
    "신한금융지주": ("첫 화면 하단 정책 링크는 개인정보처리방침·신용정보활용체제·고객정보취급방침·신한지킴이뿐 — 이용약관·저작권정책 쪽 "
                "없음, 자동 수집 금지 문구 확인 안 됨 (판단)"),
    "하나금융지주": ("첫 화면(/main/index.do) 하단 「이용약관」 메뉴 안에 개인정보처리방침·신용정보활용체제·고객정보취급방침·하나맵뿐 — "
                "사이트 이용약관·저작권정책 본문 없음, 자동 수집 금지 문구 확인 안 됨 (판단)"),
    "우리금융지주": ("첫 화면(/kor/main/index.do) 하단 정책 링크는 개인정보처리방침·고객정보취급방침·신용정보활용체제뿐 — 이용약관·"
                "저작권정책 쪽 없음, 자동 수집 금지 문구 확인 안 됨 (판단)"),
    "NH농협금융지주": "확인 못 함 — 사이트가 이 환경 요청을 모두 HTTP 400 으로 막음",
}
BOARD = {
    "KB금융지주": "https://www.kbfg.com/kor/about/governance/board-directors/list.htm",
    "신한금융지주": "https://www.shinhangroup.com/kr/governance/director/disclosure",
    "하나금융지주": "https://www.hanafn.com/governance/disclosure.do",
    "우리금융지주": "https://www.woorifg.com/kor/corp-governance/governance-structure/list.do",
    "NH농협금융지주": "https://www.nhfngroup.com/user/indexSub.do?codyMenuSeq=1218157519&siteId=nhfngroup",
}


def listcsv():
    """dart_out/ops15/연차보고서15_목록_g1.csv — 받은 파일과 못 받은 연도."""
    import csv
    cols = ["회사", "공시연도", "공시유형", "제목", "게시판_url", "파일_url", "공시일", "http", "크기", "sha256", "쪽수", "글자없는쪽",
            "robots_판정", "약관_판정", "실패사유", "fetched_at"]
    dl = json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8"))
    rows = []
    for r in dl:
        fail = r.get("실패사유", "")
        if r["실제_url"] and r["실제_url"] != r["파일_url"]:
            fu = "%s (실제로 받은 주소: %s)" % (r["파일_url"], r["실제_url"])
        else:
            fu = r["파일_url"]
        if r["회사"] == "신한금융지주" and r["공시연도"] == 2020 and r["공시유형"] == "추가공시":
            fail = (fail + "; " if fail else "") + "받은 파일 sha256 이 같은 해 본공시 파일과 같음(게시판에 같은 파일이 올라 있음)"
        if r["회사"] == "우리금융지주":
            m = __import__("re").search(r"saveFileNm=(\d{8})", r["파일_url"])
            if m and m.group(1) != r["공시일"].replace("-", ""):
                fail = (fail + "; " if fail else "") + ("(참고) 파일 저장 이름의 날짜(%s)가 게시일(%s)과 다름 — 게시 뒤 파일이 "
                                                       "바뀌었을 수 있음 (판단)") % (m.group(1), r["공시일"])
        rows.append({"회사": r["회사"], "공시연도": r["공시연도"], "공시유형": r["공시유형"], "제목": r["제목"],
                     "게시판_url": r["게시판_url"], "파일_url": fu, "공시일": r["공시일"], "http": r["http"],
                     "크기": r["크기"], "sha256": r["sha256"], "쪽수": r.get("쪽수", ""), "글자없는쪽": r.get("글자없는쪽", ""),
                     "robots_판정": ROBOTS_NOTE[r["회사"]], "약관_판정": TERMS_NOTE[r["회사"]], "실패사유": fail,
                     "fetched_at": r["fetched_at"]})
    for y in YEARS:
        rows.append({"회사": "NH농협금융지주", "공시연도": y, "공시유형": "본공시·추가공시", "제목": "", "게시판_url": BOARD["NH농협금융지주"],
                     "파일_url": "", "공시일": "", "http": "400", "크기": "", "sha256": "", "쪽수": "", "글자없는쪽": "",
                     "robots_판정": ROBOTS_NOTE["NH농협금융지주"], "약관_판정": TERMS_NOTE["NH농협금융지주"],
                     "실패사유": ("못 받음 — 찾은 곳: www.nhfngroup.com robots.txt·첫 화면(/, /user/indexMain.do)·경영공시 게시판"
                                "(indexSub.do?codyMenuSeq=1218157519)·6차 파일 URL(common/downLoad.do?fileSeq=5680657) 모두 "
                                "HTTP 400 「Request Blocked」(2026-11-02 16:07~16:30 KST, 재시도 포함). 차단을 피해 다른 UA·경로로 "
                                "다시 시도하지 않음(우회 금지). 연차보고서 게시판 목록을 못 열어 과거 파일 존재 여부도 확인 못 함"),
                     "fetched_at": ""})
    order = list(HOSTS)
    rows.sort(key=lambda r: (order.index(r["회사"]), int(r["공시연도"]), r["공시유형"]))
    p = os.path.join("dart_out", "ops15", "연차보고서15_목록_g1.csv")
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(p, len(rows))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "kb_list":
        kb_list()
        return 0
    if cmd == "fixnames":            # 우리 파일 이름(머리글 이중 UTF-8) 바로잡기 — 받은 바이트는 그대로
        fixnames()
        return 0
    if cmd == "listcsv":
        listcsv()
        return 0
    if cmd == "text":
        to_text()
        return 0
    if cmd == "candidates":
        candidates()
        return 0
    if cmd == "download":
        download()
        return 0
    if cmd == "sh_list":
        sh_list()
        return 0
    if cmd == "hana_list":
        hana_list()
        return 0
    if cmd == "woori_list":
        woori_list()
        return 0
    if cmd == "robots":
        robots_all()
        return 0
    if cmd == "get":                 # 탐색: get <co> <url> <name> [referer]
        co, url, name = argv[2], argv[3], argv[4]
        ref = argv[5] if len(argv) > 5 else ""
        p, m = fetch(co, url, os.path.join("pages", name), referer=ref)
        print(m["http"], m["바이트"], m["content_type"], m["content_disposition"][:80], p)
        return 0
    if cmd == "post":                # 탐색: post <co> <url> <name> <json-body> [referer]
        co, url, name, body = argv[2], argv[3], argv[4], json.loads(argv[5])
        ref = argv[6] if len(argv) > 6 else ""
        p, m = fetch(co, url, os.path.join("pages", name), referer=ref, data=body)
        print(m["http"], m["바이트"], m["content_type"], p)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
