# -*- coding: utf-8 -*-
"""13차 9-4 기준표 — 폐지된 「금융지주회사 통합위험관리 모범규준」 원문(조 번호·제목) 찾기.
실행은 저장소 루트에서(스크립트가 chdir 함).

    python3 scripts/dart/web13_mobeom.py robots              # 후보 호스트 robots.txt 확인(web13.Robots) → 요청기록
    python3 scripts/dart/web13_mobeom.py get <이름> <URL>     # 한 건 받기(robots 허용일 때만) → dart_out/raw/web13/mobeom/<이름>
    python3 scripts/dart/web13_mobeom.py kofia               # 금융투자협회 법규정보시스템 통합검색(규정명·규정내용, 연혁 포함)
    python3 scripts/dart/web13_mobeom.py law                 # 법제처 Open API 행정규칙 검색(현행·연혁) — 모범규준 등록 여부
    python3 scripts/dart/web13_mobeom.py press               # 금감원·금융위 보도자료 게시판 낱말 검색(2011~2016)
    python3 scripts/dart/web13_mobeom.py admin               # 금감원 「행정지도 내역」 검색(시행여부=전체, 폐지 포함)
    python3 scripts/dart/web13_mobeom.py local               # dart_out/text/risk8·risk9 에서 모범규준 인용 문장(쪽 표기) → CSV
    python3 scripts/dart/web13_mobeom.py build               # 산출 md·csv(요청 없음, 받은 원본만)
  (보도자료·행정지도 상세·첨부는 get 으로 한 건씩 받았다 — 받은 목록은 dart_out/raw/web13/mobeom/**/*.meta.json)
  hwp → md 는 scripts/dart/hwp2md.py(수정 없이 python -I), pdf → txt 는 pypdf(쪽 표지 「=== p.N ===」).

원칙(13차 COMMON13.md):
  - 요청은 web13.Web(UA 고정·1.2초 간격·3회 재시도). robots.txt 는 web13.Robots(RFC 9309)로 보고, 막힌 경로·접속 불가
    호스트는 받지 않는다. 401·403·429·로그인·캡차 화면이 나오면 우회하지 않고 멈춘다(사유는 요청기록에).
  - 원본은 save() 로 dart_out/raw/web13/mobeom/ 에 바이트 그대로 + .meta.json(sha256). 이미 받은 원본은 다시 받지 않는다.
  - md 에 옮기는 글은 받은 원본(HTML→텍스트)·로컬 텍스트에서 **글자 그대로** 잘라 온다. 해설은 「note:」 줄에만.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))                    # 저장소 루트
from web13 import Web, save, Robots, now, write_csv, OUT, WORK, RAW  # noqa: E402

TASK = "mobeom"
D = os.path.join(RAW, TASK)
TODAY = "2026-10-07"
LOG_CSV = os.path.join(WORK, "9-4_모범규준_요청기록.csv")


class Stop(Exception):
    """차단·로그인·캡차·robots 차단·접속 불가 — 우회하지 않고 멈춘다."""


W = None
ROBOTS = {}
LOG = []


def web():
    global W
    if W is None:
        W = Web()
    return W


def robots(base):
    if base not in ROBOTS:
        r = Robots(web(), base, TASK)
        LOG.append(dict(시각=now(), URL=base + "/robots.txt", 결과="robots " + r.status, 사유=r.note))
        ROBOTS[base] = r
    return ROBOTS[base]


def blocked(b):
    """금융투자협회 법규정보시스템 방화벽 차단 화면(실측 2026-10-07: 쪽 넘김 POST·seq 만 준 전체화면 요청에서 나옴)."""
    return b"web-firewall security policies" in b[:2000]


def fetch(url, referer="", data=None):
    base = "%s://%s" % urllib.parse.urlparse(url)[:2]
    r = robots(base)
    if not r.allowed(url):
        LOG.append(dict(시각=now(), URL=url, 결과="요청 안 함", 사유="robots.txt %s %s" % (r.status, r.note)))
        raise Stop("robots.txt 가 허용하지 않음(%s) — 요청 안 함: %s" % (r.status, url))
    try:
        fu, st, hd, b = web().get(url, referer=referer, data=data)
    except urllib.error.HTTPError as e:
        LOG.append(dict(시각=now(), URL=url, 결과="HTTP %s" % e.code, 사유=""))
        raise Stop("HTTP %s — %s" % (e.code, url))
    except Exception as e:                                          # noqa: BLE001
        LOG.append(dict(시각=now(), URL=url, 결과="접속 실패", 사유="%s: %s" % (type(e).__name__, e)))
        raise Stop("접속 실패 — %s: %s" % (url, e))
    if blocked(b):
        LOG.append(dict(시각=now(), URL=url, 결과="멈춤", 사유="사이트 방화벽 차단 응답(web-firewall) — 우회하지 않음"))
        raise Stop("사이트 방화벽 차단 응답 — %s" % url)
    low = b[:30000].decode("utf-8", "replace").lower()
    if "/login" in fu.lower() or "captcha" in low or "자동입력방지" in low:
        LOG.append(dict(시각=now(), URL=url, 결과="멈춤", 사유="로그인/캡차 화면 → %s" % fu))
        raise Stop("로그인/캡차 화면 — %s → %s" % (url, fu))
    LOG.append(dict(시각=now(), URL=url, 결과="HTTP %s" % st, 사유=""))
    return fu, st, hd, b


def cached(name, url, referer="", data=None, extra=None):
    """dart_out/raw/web13/mobeom/<name> 이 있으면 읽고, 없으면 받아서 save. (bytes, meta, path)"""
    p = os.path.join(D, name)
    if os.path.exists(p) and os.path.exists(p + ".meta.json"):
        with open(p, "rb") as f, open(p + ".meta.json", encoding="utf-8") as g:
            b = f.read()
            if blocked(b):                                          # 앞서 받은 차단 응답 — 다시 요청하지 않는다
                raise Stop("사이트 방화벽 차단 응답(저장본 %s) — %s" % (p, url))
            return b, json.load(g), p
    fu, st, hd, b = fetch(url, referer, data)
    meta = dict(출처URL=url, 최종URL=fu, http_status=st, content_type=hd.get("Content-Type", ""),
                content_disposition=hd.get("Content-Disposition", ""), fetched_at=now())
    if data:
        meta["POST"] = data if isinstance(data, dict) else ""
    meta.update(extra or {})
    sub, base = os.path.split(name)
    path, meta = save(TASK + ("/" + sub if sub else ""), base, b, meta)
    return b, meta, path


def flush_log():
    if not LOG:
        return
    new = not os.path.exists(LOG_CSV)
    os.makedirs(WORK, exist_ok=True)
    with open(LOG_CSV, "a", encoding="utf-8-sig" if new else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["시각", "URL", "결과", "사유"])
        if new:
            w.writeheader()
        w.writerows(LOG)
    del LOG[:]


def strip_tags(h):
    h = re.sub(r"<script\b.*?</script>", "", h, flags=re.S | re.I)
    h = re.sub(r"<style\b.*?</style>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|tr|h\d|dt|dd|table)>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return "\n".join(x.strip() for x in h.split("\n") if x.strip())


HOSTS = []

# ── 금융투자협회 법규정보시스템(law.kofia.or.kr) ──────────────────────────────
KOFIA = "https://law.kofia.or.kr"
KOFIA_SEARCH = KOFIA + "/service/search/searchTotal.do"
KOFIA_Q = [  # (검색 구분, 현행/연혁, 검색어) — 사이트 통합검색 폼 그대로(searchType·searchTimeType·searchValue)
    ("title", "past", "모범규준"),
    ("title", "past", "지주"),
    ("title", "past", "통합"),
    ("title", "past", "위험관리"),
    ("content", "past", "금융지주회사 통합"),
    ("content", "past", "통합위험관리"),
    ("content", "past", "통합리스크관리"),
]
KOFIA_CSV = os.path.join(WORK, "9-4_모범규준_kofia검색.csv")


def kofia_rows(t):
    """통합검색 목록 표 → [{번호, 제목, 구분, 제개정일, seq, historySeq}]"""
    i = t.find('<caption>통합검색 목록</caption>')
    j = t.find("</table>", i)
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t[i:j], re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        cell = [strip_tags(x) for x in tds]
        m = re.search(r"popfullscreenEx3\('(\d+)',\s*'(\d+)'", tr)
        title = cell[1].split("\n")
        rows.append(dict(번호=cell[0], 제목=title[0], 구분=" ".join(title[1:]), 제개정일=cell[2],
                         seq=m.group(1) if m else "", historySeq=m.group(2) if m else ""))
    return rows


def cmd_kofia():
    out = []
    for st, tt, q in KOFIA_Q:
        page, last = 1, 1
        while page <= last:
            nm = "kofia_search_%s_%s_%s_p%d.html" % (st, tt, re.sub(r"\s+", "_", q), page)
            data = dict(page=str(page), searchValue=q, searchType=st, searchTimeType=tt)
            try:
                b, m, p = cached(nm, KOFIA_SEARCH, referer=KOFIA + "/service/main/main.do", data=data)
            except Stop as e:
                out.append(dict(검색구분=st, 현행연혁=tt, 검색어=q, 쪽=page, 번호="", 제목="(멈춤) %s" % e, 구분="",
                                제개정일="", seq="", historySeq="", 원본=""))
                break
            t = b.decode("utf-8", "replace")
            mm = re.search(r"페이지 : <strong[^>]*>(\d+)/(\d+)</strong>", t)
            last = int(mm.group(2)) if mm else 1
            cnt = re.search(r"전체 : (\d+)건", strip_tags(t))
            rs = kofia_rows(t)
            if not rs:
                out.append(dict(검색구분=st, 현행연혁=tt, 검색어=q, 쪽=page, 번호="", 제목="(결과 없음 — 전체 %s건)" %
                                (cnt.group(1) if cnt else "?"), 구분="", 제개정일="", seq="", historySeq="", 원본=p))
            for r in rs:
                out.append(dict(검색구분=st, 현행연혁=tt, 검색어=q, 쪽=page, 원본=p, **r))
            page += 1
    write_csv(KOFIA_CSV, ["검색구분", "현행연혁", "검색어", "쪽", "번호", "제목", "구분", "제개정일", "seq", "historySeq", "원본"], out)
    print(KOFIA_CSV, len(out))


# ── 법제처 Open API 행정규칙 검색(폐지·연혁 포함) ──────────────────────────
LAW_Q = ["모범규준", "통합위험관리", "통합리스크관리", "리스크관리 모범규준", "위험관리 모범규준", "금융지주회사"]
LAW_CSV = os.path.join(WORK, "9-4_모범규준_법제처검색.csv")


def cmd_law():
    sys.path.insert(0, os.path.join("scripts", "law"))
    os.environ.setdefault("LAW_DELAY", "1.0")
    from lawclient import LawClient                                 # OC 는 env/.env, 기록은 OC=***
    import xml.etree.ElementTree as ET
    lc = LawClient(os.path.join(RAW, "law", "_call_log.csv"))
    out = []
    for q in LAW_Q:
        for nw in ("1", "2"):                                       # 1=현행, 2=연혁(폐지 판 포함)
            page, total = 1, None
            while True:
                nm = "law/admrul_%s_nw%s_p%d.xml" % (re.sub(r"\s+", "_", q), nw, page)
                p = os.path.join(D, nm)
                if os.path.exists(p):
                    body = open(p, "rb").read()
                    murl = json.load(open(p + ".meta.json", encoding="utf-8")).get("출처URL", "")
                else:
                    st, body, murl, host = lc.api("lawSearch.do", type="XML", target="admrul", query=q,
                                                  display=100, page=page, nw=nw)
                    n_oc = lc.count_oc(body)                        # 응답이 요청 링크(OC 포함)를 되돌려 줌 → 가리고 저장
                    body = lc.mask(body)
                    assert lc.count_oc(body) == 0
                    save(TASK + "/law", os.path.basename(nm), body,
                         dict(출처URL=murl, http_status=st, fetched_at=now(), 비고="응답 안 OC %d곳을 ***로 가림" % n_oc))
                root = ET.fromstring(body)
                total = int(root.findtext("totalCnt") or 0)
                items = root.findall("admrul")
                if not items:
                    out.append(dict(검색어=q, nw=nw, 전체건수=total, 행정규칙명="(결과 없음)", 행정규칙일련번호="",
                                    발령일자="", 시행일자="", 소관부처명="", 현행연혁구분="", 행정규칙종류="", 요청=murl))
                for it in items:
                    out.append(dict(검색어=q, nw=nw, 전체건수=total, 행정규칙명=it.findtext("행정규칙명") or "",
                                    행정규칙일련번호=it.findtext("행정규칙일련번호") or "", 발령일자=it.findtext("발령일자") or "",
                                    시행일자=it.findtext("시행일자") or "", 소관부처명=it.findtext("소관부처명") or "",
                                    현행연혁구분=it.findtext("현행연혁구분") or "", 행정규칙종류=it.findtext("행정규칙종류") or "",
                                    요청=murl))
                if page * 100 >= total or page >= 5:
                    break
                page += 1
    write_csv(LAW_CSV, ["검색어", "nw", "전체건수", "행정규칙명", "행정규칙일련번호", "발령일자", "시행일자", "소관부처명",
                        "현행연혁구분", "행정규칙종류", "요청"], out)
    print(LAW_CSV, len(out))


# ── 금감원·금융위 보도자료 게시판 검색(모범규준 제정 무렵) ────────────────────
FSS = "https://www.fss.or.kr"
FSC = "https://www.fsc.go.kr"
BODO = FSS + "/fss/bbs/B0000188/list.do"
BODO_VIEW = FSS + "/fss/bbs/B0000188/view.do?nttId=%s&menuNo=200218"
FSCB = FSC + "/no010101"
PRESS_TERMS = [  # (낱말, 검색구분) 금감원 searchCnd 1=제목 3=제목+내용 / 금융위 srchKey sj=제목 all=제목+내용
    ("통합위험관리", "all"), ("통합리스크관리", "all"), ("통합 리스크관리", "all"), ("통합 위험관리", "all"),
    ("리스크관리 모범규준", "all"), ("위험관리 모범규준", "all"), ("지주회사 리스크", "all"),
    ("모범규준", "title"),
]
PRESS_FROM, PRESS_TO = "2011-01-01", "2016-12-31"                   # 추진(2011.7)·제정(KB 인용 2012)·지배구조법 시행(2016.8) 무렵
PRESS_CSV = os.path.join(WORK, "9-4_모범규준_보도자료검색.csv")


def bodo_rows(page):
    rows = []
    for m in re.finditer(r'<tr>\s*<td class="num">\s*(\d+)\s*</td>\s*<td class="title"><a href="([^"]+)">(.*?)</a></td>'
                         r'\s*<td>(.*?)</td>\s*<td>\s*([\d-]+)\s*</td>(.*?)</tr>', page, re.S):
        ntt = re.search(r"nttId=(\d+)", html.unescape(m.group(2))).group(1)
        files = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
                 for x in re.findall(r'<span class="name">(.*?)</span>', m.group(6), re.S)]
        rows.append(dict(게시판="금감원 보도자료", 글번호=ntt, 제목=html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip(),
                         담당부서=strip_tags(m.group(4)), 등록일=m.group(5), 첨부=" ; ".join(files), URL=BODO_VIEW % ntt))
    return rows


def fscb_rows(page):
    rows = []
    for li in re.findall(r'<li>\s*<div class="inner">(.*?)<div class="day">([\d-]+)</div>', page, re.S):
        body, day = li
        a = re.search(r'<div class="subject">\s*<a href="/no010101/(\d+)[^"]*"[^>]*>(.*?)</a>', body, re.S)
        if not a:
            continue
        dept = re.search(r"담당부서\s*:\s*([^<]*)</span>", body)
        files = [html.unescape(x).strip() for x in re.findall(r'<a href="/comm/getFile[^"]*" title="([^"]*)"><span class="name">', body)]
        rows.append(dict(게시판="금융위 보도자료", 글번호=a.group(1), 제목=html.unescape(re.sub(r"<[^>]+>", "", a.group(2))).strip(),
                         담당부서=(dept.group(1).strip() if dept else ""), 등록일=day, 첨부=" ; ".join(files),
                         URL=FSCB + "/" + a.group(1)))
    return rows


def cmd_press():
    out = []
    for site in ("fss", "fsc"):
        stopped = ""
        for kw, scope in PRESS_TERMS:
            if stopped:
                out.append(dict(게시판=site, 낱말=kw, 검색구분=scope, 사이트총건수="", 쪽=0, 등록일="", 글번호="", 제목="",
                                담당부서="", 첨부="", URL="", 비고="요청 안 함 — 앞 요청에서 멈춤: " + stopped))
                continue
            page = 1
            while True:
                if site == "fss":
                    url = BODO + "?" + urllib.parse.urlencode(dict(menuNo="200218", pageIndex=str(page), sdate=PRESS_FROM,
                                                                   edate=PRESS_TO, searchCnd="1" if scope == "title" else "3",
                                                                   searchWrd=kw))
                    tot_re, parse = r"전체\s*<em>([\d,]+)</em>", bodo_rows
                else:
                    url = FSCB + "?" + urllib.parse.urlencode(dict(srchCtgry="", curPage=str(page), srchKey="sj" if scope == "title"
                                                                   else "all", srchText=kw, srchBeginDt=PRESS_FROM,
                                                                   srchEndDt=PRESS_TO))
                    tot_re, parse = r"전체\s*<strong>([\d,]+)</strong>", fscb_rows
                nm = "press/%s_%s_%s_p%02d.html" % (site, re.sub(r"\s+", "_", kw), scope, page)
                try:
                    b, m, p = cached(nm, url, extra=dict(검색어=kw, 검색구분=scope, 쪽=page))
                except Stop as e:
                    stopped = str(e)
                    out.append(dict(게시판=site, 낱말=kw, 검색구분=scope, 사이트총건수="", 쪽=page, 등록일="", 글번호="", 제목="",
                                    담당부서="", 첨부="", URL=url, 비고="멈춤: %s" % e))
                    break
                t = b.decode("utf-8", "replace")
                mm = re.search(tot_re, t)
                total = int(mm.group(1).replace(",", "")) if mm else 0
                rows = parse(t)
                if not rows:
                    out.append(dict(게시판=site, 낱말=kw, 검색구분=scope, 사이트총건수=total, 쪽=page, 등록일="", 글번호="",
                                    제목="(결과 없음)", 담당부서="", 첨부="", URL=url, 비고=""))
                for r in rows:
                    out.append(dict(게시판=site, 낱말=kw, 검색구분=scope, 사이트총건수=total, 쪽=page, 비고="", **{
                        k: r[k] for k in ("등록일", "글번호", "제목", "담당부서", "첨부", "URL")}))
                if not rows or page * 10 >= total or page >= 10:
                    break
                page += 1
            flush_log()
    write_csv(PRESS_CSV, ["게시판", "낱말", "검색구분", "사이트총건수", "쪽", "등록일", "글번호", "제목", "담당부서", "첨부", "URL",
                          "비고"], out)
    print(PRESS_CSV, len(out))


# ── 금감원 금융행정지도 「행정지도 내역」(폐지 포함) ─────────────────────────
ADMIN = FSS + "/fss/job/admnstgudc/list.do"
ADMIN_TERMS = ["통합리스크", "통합위험", "리스크관리 모범규준", "위험관리 모범규준", "지주회사", "지주", "그룹리스크", "모범규준"]
ADMIN_CSV = os.path.join(WORK, "9-4_모범규준_행정지도검색.csv")


def admin_rows(t):
    rows = []
    j = t.find("<tbody")
    k = t.find("</tbody>", j)
    for tr in re.findall(r"<tr>(.*?)</tr>", t[j:k], re.S):
        no = re.search(r'<td class="no">(.*?)</td>', tr, re.S)
        a = re.search(r'<td class="title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        if not a:
            continue
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        files = [(html.unescape(h), strip_tags(n)) for h, n in
                 re.findall(r'<a href="(/fss\.hpdownload[^"]+)"[^>]*>.*?<span class="name">(.*?)</span>', tr, re.S)]
        rows.append(dict(관리번호=strip_tags(no.group(1)) if no else "", 제목=strip_tags(a.group(2)),
                         상세=FSS + "/fss/job/admnstgudc/" + html.unescape(a.group(1)).lstrip("./"),
                         부서=strip_tags(tds[0]) if tds else "", 시행일=strip_tags(tds[1]) if len(tds) > 1 else "",
                         시행여부=strip_tags(tds[2]) if len(tds) > 2 else "",
                         첨부=" ; ".join(n for h, n in files), 첨부URL=" ; ".join(FSS + h for h, n in files)))
    return rows


def cmd_admin():
    out = []
    for kw in ADMIN_TERMS:
        page = 1
        while True:
            url = ADMIN + "?" + urllib.parse.urlencode(dict(menuNo="200492", pageIndex=str(page), searchRegn="", searchYear="",
                                                            searchCecYn="T", searchWrd=kw))
            try:
                b, m, p = cached("fss/admin_%s_p%02d.html" % (re.sub(r"\s+", "_", kw), page), url,
                                 extra=dict(검색어=kw, 시행여부="T(전체)", 쪽=page))
            except Stop as e:
                out.append(dict(검색어=kw, 사이트총건수="", 쪽=page, 관리번호="", 제목="", 부서="", 시행일="", 시행여부="",
                                첨부="", 첨부URL="", 상세=url, 비고="멈춤: %s" % e))
                break
            t = b.decode("utf-8", "replace")
            mm = re.search(r"전체\s*<em>([\d,]+)</em>", t)
            total = int(mm.group(1).replace(",", "")) if mm else 0
            rows = admin_rows(t)
            if not rows:
                out.append(dict(검색어=kw, 사이트총건수=total, 쪽=page, 관리번호="", 제목="(결과 없음)", 부서="", 시행일="",
                                시행여부="", 첨부="", 첨부URL="", 상세=url, 비고=""))
            for r in rows:
                out.append(dict(검색어=kw, 사이트총건수=total, 쪽=page, 비고="", **r))
            if not rows or page * 10 >= total or page >= 15:
                break
            page += 1
        flush_log()
    write_csv(ADMIN_CSV, ["검색어", "사이트총건수", "쪽", "관리번호", "제목", "부서", "시행일", "시행여부", "첨부", "첨부URL", "상세",
                          "비고"], out)
    print(ADMIN_CSV, len(out))


# ── 로컬 텍스트(8·9차)에서 「모범규준」 인용 문장 ─────────────────────────────
LOCAL_DIRS = [os.path.join("dart_out", "text", "risk8"), os.path.join("dart_out", "text", "risk9")]
LOCAL_CSV = os.path.join(WORK, "9-4_모범규준_로컬인용.csv")
# 「모범규준」 바로 앞(공백·줄바꿈 뺀) 글자로 어느 모범규준인지 가른다. 앞에서부터 처음 맞는 것.
KINDS = [
    ("대상", r"(통합리스크관리|통합위험관리)$"),
    ("그룹리스크관리모범규준(회사 자체 규준)", r"그룹리스크관리$"),
    ("다른 모범규준: 내부회계관리제도", r"내부회계관리제도(평가및보고)?$|계관리제도(평가및보고)?$|평가및보고$"),
    ("다른 모범규준: 지배구조", r"지배구조$|금융회사지배구조$|기업지배구조$|지배구조모범규준"),
    ("다른 모범규준: 그룹 내부통제기준", r"내부통제기준$"),
    ("다른 모범규준: 감사위원회", r"감사위원회$"),
    ("다른 모범규준: 성과보상·보수", r"성과보상체계$"),
    ("다른 모범규준: 환경·사회 리스크관리(ESRM)", r"사회리스크관리$|환경ㆍ사회리스크관리$|환경·사회리스크관리$"),
    ("다른 모범규준: 금융투자·대체투자·부동산 등", r"(금융투자회사리스크관리|대체투자리스크관리|대체투자펀드리스크관리|부동산신탁사영업행위|"
                                       r"회계처리업무|여신심사선진화를위한|보상에관한|BestPractice\(|분실,도난사고보상에관한)$"),
    ("리스크관리 모범규준(문맥 확인)", r"리스크관리$"),
]


def doc_meta():
    """파일 이름 → (문서 표기, 접수번호 또는 URL)."""
    m = {}
    with open(os.path.join("handoff", "연차보고서_파일목록.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            m[r["파일명"]] = r
    d = {}
    with open(os.path.join("dart_out", "risk9", "DART_목록.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            d[r["rcept_no"]] = r
    return m, d


def cmd_local():
    annual, dart = doc_meta()
    out = []
    for dd in LOCAL_DIRS:
        for fn in sorted(os.listdir(dd)):
            if not fn.endswith(".txt"):
                continue
            p = os.path.join(dd, fn)
            with open(p, encoding="utf-8") as f:
                lines = f.read().split("\n")
            # 정규화 문자열(공백·줄바꿈 제거)과 글자→줄 번호 대응
            norm, pos = [], []
            page_of_line, pg = [], ""
            for i, ln in enumerate(lines):
                mm = re.match(r"=== p\.(\d+) ===", ln)
                if mm:
                    pg = mm.group(1)
                page_of_line.append(pg)
                for ch in ln:
                    if not ch.isspace():
                        norm.append(ch)
                        pos.append(i)
            s = "".join(norm)
            if fn.startswith("연차보고서__"):
                pdf = fn[len("연차보고서__"):-4] + ".pdf"
                r = annual.get(pdf, {})
                doc, src = "%s (%s)" % (r.get("제목", pdf), pdf), r.get("url", "")
            else:
                rc = re.search(r"(\d{14})", fn)
                rc = rc.group(1) if rc else ""
                r = dart.get(rc, {})
                if r:
                    doc = "%s %s" % (r.get("corp_label", ""), r.get("report_nm", ""))
                else:
                    doc = fn[:-4].replace("__", " ")
                src = "접수번호 " + rc if rc else ""
            for m in re.finditer("모범규준", s):
                pre = s[max(0, m.start() - 40):m.start()]
                kind = "기타·불명(문맥 확인)"
                for k, rx in KINDS:
                    if re.search(rx, pre):
                        kind = k
                        break
                a = pos[max(0, m.start() - 25)]
                b = pos[min(len(pos) - 1, m.end() + 25)]
                quote = " / ".join(lines[a:b + 1])
                out.append(dict(폴더=dd, 파일=fn, 문서=doc, 출처=src, 쪽=page_of_line[pos[m.start()]], 줄="%d-%d" % (a + 1, b + 1),
                                분류=kind, 앞글자=pre[-30:], 원문줄=quote))
    write_csv(LOCAL_CSV, ["폴더", "파일", "문서", "출처", "쪽", "줄", "분류", "앞글자", "원문줄"], out)
    from collections import Counter
    print(LOCAL_CSV, len(out))
    for k, v in Counter(r["분류"] for r in out).most_common():
        print("  ", v, k)


# ── 금감원 「행정지도 예고」 제목 검색 ─────────────────────────────────────
PRVNTC = FSS + "/fss/job/admnPrvntc/list.do"
PRVNTC_TERMS = ["지주", "통합", "위험관리", "리스크"]


def cmd_prvntc():
    for kw in PRVNTC_TERMS:
        url = PRVNTC + "?" + urllib.parse.urlencode(dict(menuNo="200491", pageIndex="1", searchCnd="1", searchWrd=kw))
        try:
            b, m, p = cached("fss/admnPrvntc_%s_p01.html" % kw, url, extra=dict(검색어=kw))
        except Stop as e:
            print("STOP", e)
            continue
        mm = re.search(r"전체\s*<em>([\d,]+)</em>", b.decode("utf-8", "replace"))
        print(kw, mm.group(1) if mm else "?", p)
    flush_log()


# ── 게시글·행정지도 상세·첨부(한 건씩) ───────────────────────────────────────
ADMV = FSS + "/fss/job/admnstgudc/view.do?guGuidanceMgrSeq=%s&menuNo=200492"
PRVV = FSS + "/fss/job/admnPrvntc/view.do?seqno=%s&menuNo=200491"
FILEDOWN = FSS + "/fss/cmmn/file/fileDown.do?menuNo=200218&atchFileId=%s&fileSn=%s&bbsId="
DOCS = [  # (저장 이름, URL, referer)
    ("press/fss_view_9084.html", BODO_VIEW % "9084", ""),
    ("press/fss_view_8584.html", BODO_VIEW % "8584", ""),
    ("press/fss_9084_120320_조간_통합리스크모범규준마련.pdf", FILEDOWN % ("505b0384d2281b32d0c7deb4b422532c", "2"), BODO_VIEW % "9084"),
    ("press/fss_9084_120320_조간_통합리스크모범규준마련.hwp", FILEDOWN % ("505b0384d2281b32d0c7deb4b422532c", "1"), BODO_VIEW % "9084"),
    ("press/fss_8584_통합리스크관리모범규준(보도자료)_지주회사팀F.pdf", FILEDOWN % ("c680e5ac78503b9ceb330675e0014ace", "1"),
     BODO_VIEW % "8584"),
    ("press/fss_8584_통합리스크관리모범규준(보도자료)_지주회사팀F.hwp", FILEDOWN % ("c680e5ac78503b9ceb330675e0014ace", "2"),
     BODO_VIEW % "8584"),
    ("fss/admin_view_20170210165649943.html", ADMV % "20170210165649943", ""),
    ("fss/admin_view_20170328150222228.html", ADMV % "20170328150222228", ""),
    ("fss/admin_view_20120320105719564.html", ADMV % "20120320105719564", ""),
    ("fss/모범규준_20160801판_붙임2_통합위험관리_개정후전문.hwp",
     FSS + "/fss.hpdownload?path=/law/ptl/&file=2150753_20170213145817413_1.hwp&filere=%EB%B6%99%EC%9E%842_%EA%B8%88%EC%9C%B5"
     "%EC%A7%80%EC%A3%BC%ED%9A%8C%EC%82%AC+%ED%86%B5%ED%95%A9%EC%9C%84%ED%97%98%EA%B4%80%EB%A6%AC+%EB%AA%A8%EB%B2%94%EA%B7"
     "%9C%EC%A4%80+%EA%B0%9C%EC%A0%95+%ED%9B%84+%EC%A0%84%EB%AC%B8.hwp", ADMV % "20170210165649943"),
    ("fss/모범규준_20170401판_붙임2_통합위험관리_전문.hwp",
     FSS + "/fss.hpdownload?path=/law/ptl/&file=2150753_20170328150222208_1.hwp&filere=%28%EB%B6%99%EC%9E%842%29+%EA%B8%88"
     "%EC%9C%B5%EC%A7%80%EC%A3%BC%ED%9A%8C%EC%82%AC+%ED%86%B5%ED%95%A9%EC%9C%84%ED%97%98%EA%B4%80%EB%A6%AC+%EB%AA%A8%EB%B2"
     "%94%EA%B7%9C%EC%A4%80.hwp", ADMV % "20170328150222228"),
    ("fss/admnPrvntc_view_1.html", PRVV % "1", ""),
    ("fss/admnPrvntc_view_29.html", PRVV % "29", ""),
    ("fss/admnPrvntc_view_51.html", PRVV % "51", ""),
    ("fss/admnPrvntc_view_67.html", PRVV % "67", ""),
    ("fss/예고29_통합리스크관리_모범규준(게시)F_.hwp",
     FSS + "/fss.hpdownload?path=/law/bgn/&file=%ED%86%B5%ED%95%A9%EB%A6%AC%EC%8A%A4%ED%81%AC%EA%B4%80%EB%A6%AC_%EB%AA%A8"
     "%EB%B2%94%EA%B7%9C%EC%A4%80%28%EA%B2%8C%EC%8B%9C%29F_.hwp", PRVV % "29"),
    ("fss/예고51_지배구조법시행_개정안(홈피공시).hwp",
     FSS + "/fss.hpdownload?path=/law/bgn/&file=%EC%A7%80%EB%B0%B0%EA%B5%AC%EC%A1%B0%EB%B2%95+%EC%8B%9C%ED%96%89%EC%97%90+"
     "%EB%94%B0%EB%A5%B8%E3%80%8C%EA%B8%88%EC%9C%B5%EC%A7%80%EC%A3%BC%ED%9A%8C%EC%82%AC+%ED%86%B5%ED%95%A9%EB%A6%AC%EC%8A"
     "%A4%ED%81%AC%EA%B4%80%EB%A6%AC+%EB%AA%A8%EB%B2%94%EA%B7%9C%EC%A4%80%E3%80%8D%EB%B0%8F%E3%80%8C%EA%B8%88%EC%9C%B5%EC"
     "%A7%80%EC%A3%BC%ED%9A%8C%EC%82%AC%EC%9D%98+%EA%B7%B8%EB%A3%B9%EB%82%B4%EB%B6%80%ED%86%B5%EC%A0%9C%EA%B8%B0%EC%A4%80"
     "+%EB%AA%A8%EB%B2%94%EA%B7%9C%EC%A4%80%E3%80%8D+%EA%B0%9C%EC%A0%95%EC%95%88%28%ED%99%88%ED%94%BC%EA%B3%B5%EC%8B%9C%29.hwp",
     PRVV % "51"),
]
PDF_PY = ("import sys\nfrom pypdf import PdfReader\nrd = PdfReader(sys.argv[1])\nparts = []\n"
          "for i, pg in enumerate(rd.pages, 1):\n    parts.append('=== p.%d ===\\n%s' % (i, pg.extract_text() or ''))\n"
          "open(sys.argv[2], 'w', encoding='utf-8').write('\\n'.join(parts))\n")


def cmd_docs():
    """DOCS 를 받고(저장본 있으면 요청 안 함), hwp→md(hwp2md.py)·pdf→txt(pypdf) 변환. 인터프리터는 -I, cwd 는 저장소 루트."""
    import subprocess
    for name, url, ref in DOCS:
        try:
            b, m, p = cached(name, url, referer=ref, extra=dict(게시글=ref) if ref else None)
        except Stop as e:
            print("STOP", e)
            continue
        if p.endswith(".hwp") and not os.path.exists(p + ".md"):
            subprocess.run([sys.executable, "-I", os.path.join(HERE, "hwp2md.py"), p, p + ".md"], check=True)
        if p.endswith(".pdf") and not os.path.exists(p + ".txt"):
            subprocess.run([sys.executable, "-I", "-c", PDF_PY, p, p + ".txt"], check=True)
        print(p, m.get("sha256", "")[:16])
    flush_log()


# ── 산출(md·csv) ─────────────────────────────────────────────────────────
OUT_MD = os.path.join(OUT, "9-4_모범규준_원문.md")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
F2016 = os.path.join(D, "fss", "모범규준_20160801판_붙임2_통합위험관리_개정후전문.hwp")
F2017 = os.path.join(D, "fss", "모범규준_20170401판_붙임2_통합위험관리_전문.hwp")
F2012 = os.path.join(D, "fss", "예고29_통합리스크관리_모범규준(게시)F_.hwp")
F2016P = os.path.join(D, "fss", "예고51_지배구조법시행_개정안(홈피공시).hwp")
PR2012 = os.path.join(D, "press", "fss_9084_120320_조간_통합리스크모범규준마련.hwp")
PR2011 = os.path.join(D, "press", "fss_8584_통합리스크관리모범규준(보도자료)_지주회사팀F.hwp")
WEBSEARCH = [  # 이 작업에서 쓴 WebSearch 질의(도구 호출, 스크립트 밖) — 결과에서 후보 URL 만 골라 스크립트로 받음
    '"금융지주회사 통합위험관리 모범규준"',
    "law.kofia.or.kr 금융지주회사 통합위험관리 모범규준",
    "금융지주회사 통합리스크관리 모범규준 제정 금융감독원 2012",
    "금감원 금융지주회사 통합위험관리 모범규준 2012년 3월 시행 그룹위험관리 (extended)",
    '"통합위험관리 모범규준" 금융지주회사 제3조 적용범위',
    "law.kofia.or.kr lawFullScreenContent.do seq=155",
    '금융감독원 모범규준 목록 폐지 행정지도 "금융지주회사" 위험관리 모범규준 fss.or.kr',
    "이투데이 금감원 금융지주사 리스크관리 모범규준 추진",
    '2012년 금융지주회사 "리스크관리 모범규준" 금감원 그룹리스크관리위원회 분기 1회 자본적정성 평가 (extended)',
    '금융규제·법령해석포털 행정지도 목록 "통합위험관리" 모범규준',
    '"그룹위험관리 모범규준" OR "통합위험관리 모범규준" 금융지주 2012 금융감독원 보도자료',
]
TERM_MAP = [("그룹리스크관리최고책임자", "그룹위험관리책임자"), ("리스크관리최고책임자", "위험관리책임자"),
            ("그룹리스크협의회", "그룹위험관리협의회"), ("리스크 철학", "위험관리 철학"), ("리스크", "위험"),
            ("위험를", "위험을"), ("위험가 ", "위험이 "), ("위험와", "위험과"), ("위험는", "위험은"), ("위험로", "위험으로")]


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def meta(p):
    with open(p + ".meta.json", encoding="utf-8") as f:
        return json.load(f)


def parse_rule(lines):
    """모범규준 본문 줄 → (조 목록, 조별 본문 줄). 조 목록: dict(조, 장, 절, 제목, 표시)."""
    arts, body, cur = [], {}, None
    chap = sec = ""
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^제\s*(\d+)\s*장\s*(.*)$", s)
        if m:
            chap, sec, cur = "제%s장 %s" % (m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()), "", None
            continue
        m = re.match(r"^제(\d+)절\s*(.*)$", s)
        if m:
            sec, cur = "제%s절 %s" % (m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()), None
            continue
        if re.match(r"^부\s*칙", s):
            cur = "부칙:" + s
            body.setdefault(cur, []).append(ln)
            continue
        m = re.match(r"^제(\d+)조\s*\(([^)]*)\)", s)
        if m and not str(cur or "").startswith("부칙"):
            n = int(m.group(1))
            cur = n
            arts.append(dict(조=n, 장=chap, 절=sec, 제목=m.group(2).strip()))
            body[n] = [ln]
            continue
        if cur is not None:
            body.setdefault(cur, []).append(ln)
    for a in arts:
        a["표시"] = " ".join(sorted(set(re.findall(r"<(?:개정|삭제|신설)\s*[\d.\s]+>", "\n".join(body[a["조"]])))))
    return arts, body


def norm_old(s):
    for x, y in TERM_MAP:
        s = s.replace(x, y)
    return re.sub(r"\s+", " ", s).strip()


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


def page_lines(path, start, ends):
    """저장한 HTML → 태그 뺀 줄. start 표지 다음부터 ends 중 처음 나오는 표지 앞까지(글자 그대로)."""
    t = strip_tags(rd_bytes(path).decode("utf-8", "replace"))
    i = t.index(start) + len(start)
    j = min([t.find(e, i) for e in ends if t.find(e, i) >= 0])
    return t[i:j].strip("\n").split("\n")


def rd_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def redact(lines):
    """담당 직원 이름·전화·이메일 줄을 가린다(금감원 「이메일무단수집거부」·개인정보 최소화). 가린 자리는 표시."""
    out, skip_to_end, hide_next = [], False, False
    for ln in lines:
        if skip_to_end:
            continue
        if hide_next:
            out.append("[생략: 담당 직원 이름·전화]")
            hide_next = False
            continue
        if ln.strip() in ("담당자", "자료문의"):
            out.append(ln)
            hide_next = True
            continue
        if ln.startswith("- [담당자]"):
            out.append("- [담당자] [생략: 담당 직원 이름]")
            continue
        if ln.startswith("6. 접수부서"):
            out.append(ln)
            out.append("[생략: 접수부서 담당 직원 이름·전화·팩스·이메일]")
            skip_to_end = True
            continue
        out.append(ln)
    return out


def press_lines(p):
    """보도자료 hwp2md 변환본 → 줄. 머리 표의 책임자·담당자 줄은 가리고, 표 칸 안 <br> 은 줄바꿈으로."""
    out = []
    for ln in rd(p + ".md").split("\n"):
        if "책 임 자" in ln:
            out.append("[생략: 책임자·담당자 이름·전화 줄]")
            continue
        out.extend(ln.replace("<br>", "\n").split("\n"))
    return out


def local_block(path, start, end):
    """로컬 텍스트에서 start 가 든 줄부터 end 가 든 줄까지(글자 그대로) + 쪽 표지."""
    lines = rd(path).split("\n")
    i = next(k for k, x in enumerate(lines) if start in x)
    j = next(k for k in range(i, len(lines)) if end in lines[k])
    pg = ""
    for k in range(i, -1, -1):
        m = re.match(r"=== p\.(\d+) ===", lines[k])
        if m:
            pg = m.group(1)
            break
    return lines[i:j + 1], pg, i + 1, j + 1


def code(lines):
    return ["```text"] + list(lines) + ["```"]


def cmd_build():
    from collections import Counter
    L = []
    w = L.append
    m16, m17, m12, m16p = meta(F2016), meta(F2017), meta(F2012), meta(F2016P)
    a16, b16 = parse_rule(rd(F2016 + ".md").split("\n"))
    a12, b12 = parse_rule(rd(F2012 + ".md").split("\n"))
    t16p = rd(F2016P + ".md").split("\n")
    k = t16p.index("금융지주회사 통합위험관리 모범규준")
    a16p, b16p = parse_rule(t16p[k:])
    A16, A12, A16P = {a["조"]: a for a in a16}, {a["조"]: a for a in a12}, {a["조"]: a for a in a16p}
    assert sorted(A16) == list(range(1, 60)) and sorted(A12) == list(range(1, 60)) and sorted(A16P) == list(range(1, 60))

    # ── 조 목록 CSV
    rows = []
    for n in range(1, 60):
        x, y, z = A16[n], A12[n], A16P[n]
        rows.append({"조": n, "장": x["장"], "절": x["절"], "제목_2016.8.1판": x["제목"], "제목_2012.3.13제정판": y["제목"],
                     "제목_2016.7개정예고안": z["제목"], "2016.8.1판_본문표시": x["표시"],
                     "사용자시트범위(3~58조)": "Y" if 3 <= n <= 58 else "N",
                     "출처": "금감원 행정지도 내역 관리번호 2014-017(문서번호 감총그룹-388, 시행일 20160801) 첨부 「붙임2_금융지주회사 통합위험관리 "
                           "모범규준 개정 후 전문.hwp」 sha256 %s ; 2012.3.13 제정판 제목은 금감원 행정지도 예고(seqno=29) 첨부 "
                           "「통합리스크관리_모범규준(게시)F_.hwp」" % m16["sha256"][:16]})
    write_csv(JO_CSV, list(rows[0].keys()), rows)

    # ── 판 사이 조문 차이(자동 대조)
    def art_text(body, n):
        return [l for l in body.get(n, []) if l.strip()]
    diff12 = [n for n in range(1, 60) if [norm_old(l) for l in art_text(b12, n)] != [ws(l) for l in art_text(b16, n)]]
    diffp = [n for n in range(1, 60) if [ws(l) for l in art_text(b16p, n)] != [ws(l) for l in art_text(b16, n)]]

    # ── 머리
    w("# 9-4 기준: 폐지된 「금융지주회사 통합위험관리 모범규준」 원문(조 번호·제목·전문)")
    w("")
    w("- 수집일: %s (요청 시각은 각 원본 .meta.json 의 fetched_at, 요청기록 `%s`)" % (TODAY, LOG_CSV))
    w("- 스크립트: `scripts/dart/web13_mobeom.py` (robots → kofia·law·press·admin·prvntc 검색 → docs 받기·변환 → local → build)")
    w("- 원본: `dart_out/raw/web13/mobeom/` (git 무시) — 받은 바이트 그대로 + `.meta.json`(출처 URL·HTTP·sha256). "
      "hwp 는 `scripts/dart/hwp2md.py`(수정 없이 `python -I`)로 `.hwp.md`, pdf 는 pypdf 로 `.pdf.txt`.")
    w("- 조 목록 CSV: `%s` (1~59조, 판별 제목·장·절·개정표시·출처)" % JO_CSV)
    w("- 방법: 웹 검색(WebSearch)으로 후보를 찾고, 받는 곳마다 robots.txt 를 `web13.Robots`(RFC 9309)로 확인한 뒤 `web13.Web`(UA 고정·1.2초 "
      "간격)으로 받음. 금감원 「금융행정지도 > 행정지도 내역」(시행여부=전체)·「행정지도 예고」에서 모범규준 전문(첨부 hwp)을 받음. "
      "법제처 Open API 행정규칙(현행·연혁), 금융투자협회 법규정보시스템 통합검색(연혁 포함), 금감원·금융위 보도자료 게시판도 찾음(아래 「찾은 경로」).")
    w("- 원문 옮기는 방식: hwp2md 변환본의 줄을 **글자 그대로** 코드 블록에 옮김(오탈자·띄어쓰기도 원문대로, 예: 2조 2호 「“통합위험”란」). "
      "해설·판단은 코드 블록 밖 `note:` 줄에만 적고, 판단이 들어간 곳은 「(판단)」.")
    w("- 변환 확인: hwp 안의 미리보기 글(PrvText, 앞쪽 약 1,000자)의 줄이 모두 변환본에 들어 있음을 확인(모범규준 세 판 모두 누락 0줄). "
      "보도자료 hwp 는 머리 표가 칸 단위로 쪼개져 줄 대조가 맞지 않아 이 확인을 하지 못함(한계).")
    w("- 한계: ① 2016.3.28 개정 때의 공문·신구대비표, 2012.3.13 제정 당시 송부 공문은 추출 범위에 없음(아래 「받지 못한 것」). "
      "② 2017.4.1 판(존속기한 연장) 첨부는 2016.8.1 판 첨부와 바이트가 같음(sha256 동일) — 별도 본문 변경 없음. "
      "③ 금감원 페이지·보도자료의 담당 직원 이름·전화·이메일은 「[생략: …]」으로 가림(금감원 「이메일무단수집거부」 고지, 개인정보 최소화). "
      "④ 금감원 저작권 정책(dart_out/risk13/9-2-4_9-5_정책확인.csv 에 원문)은 「보도·비평·교육·연구 등을 위하여는 정당한 범위 안에서 "
      "공정한 관행에 합치되게 … 인용할 수 있습니다」, 「단순한 오류 정정 이외에 내용의 무단변경을 금지」 — 출처를 적고 바꾸지 않고 옮김.")
    w("")

    # ── 1. 찾은 원문과 판
    w("## 1. 찾은 원문과 판(版)")
    w("")
    w("| 판 | 이름(원문 표기) | 받은 곳 | 원본 파일(sha256 앞 16자) |")
    w("|---|---|---|---|")
    w("| 2012.3.13 제정(2012.4.1 시행) | 금융지주회사 통합리스크관리 모범규준 | 금감원 행정지도 예고 seqno=29(2016-01-12~02-01, 존속기한 연장 예고) 첨부 "
      "%s | `%s` (%s) |" % (PRVV % "29", os.path.basename(F2012), m12["sha256"][:16]))
    w("| 2016.7 개정 예고안 | 금융지주회사 통합위험관리 모범규준 | 금감원 행정지도 예고 seqno=51(2016-07-08~07-28) 첨부 %s | `%s` (%s) |"
      % (PRVV % "51", os.path.basename(F2016P), m16p["sha256"][:16]))
    w("| 2016.3.28·2016.8.1 개정(2016.8.1 시행) — **기준판** | 금융지주회사 통합위험관리 모범규준 | 금감원 행정지도 내역 관리번호 2014-017, "
      "문서번호 감총그룹-388, 시행일 20160801 첨부 %s | `%s` (%s) |" % (ADMV % "20170210165649943", os.path.basename(F2016), m16["sha256"][:16]))
    w("| 2017.4.1 존속기한 연장(~2018.3.31) | 금융지주회사 통합위험관리 모범규준 | 금감원 행정지도 내역 관리번호 2014-017, 문서번호 감총그룹-192, "
      "시행일 20170401 첨부 %s | `%s` (%s — 위와 같음) |" % (ADMV % "20170328150222228", os.path.basename(F2017), m17["sha256"][:16]))
    w("")
    w("note: 사용자 시트의 「금융지주회사 통합위험관리 모범규준(3조~58조)」은 2016.8.1 판 이름·조 범위와 맞음 — 1조(목적)·2조(정의)는 총칙, "
      "59조(위임사항)는 2016.3.28 삭제(판단: 시트가 3~58조만 행으로 둔 까닭).")
    w("note: 2016.8.1 판과 2017.4.1 판 첨부 hwp 는 sha256 이 같다(%s) — 아래 전문은 한 벌만 옮김." % m16["sha256"])
    w("")

    # ── 2. 연혁 근거 원문
    w("## 2. 제정·개정·폐지 연혁 — 근거 원문")
    w("")
    w("| 날짜 | 일 | 근거(아래 인용) |")
    w("|---|---|---|")
    w("| 2011.7.4 | 「금융지주회사 통합리스크관리 모범규준」 마련 추진(11개 지주회사·금감원 T/F, 5.25~11월 예정) | 2-1 |")
    w("| 2012.3.13 | 제정(본문 머리 「2012. 3. 13. 제정」) | 6장 부록 원문 머리 |")
    w("| 2012.3.19 배포(3.20 조간) | 「금융지주회사 통합리스크관리 모범규준」 마련 — 2012.4.1 시행 예정 | 2-2 |")
    w("| 2012.4.1 | 시행(부칙 제1조) | 5장 전문 부칙 |")
    w("| 2016.1.12~2.1 | 존속기한(2016.4.1.~2017.3.31) 연장 예고 | 2-3 |")
    w("| 2016.3.28 (시행 2016.4.1) | 개정 — 2016.8.1 판 본문에 「제 7 장 보칙<삭제 2016. 3. 28.>」·「제59조(위임사항) <삭제 2016. 3. 28.>」 표시 | 5장 전문 |")
    w("| 2016.7.8~7.28 | 지배구조법 시행에 따른 개정안 예고 | 2-4 |")
    w("| 2016.8.1 | 개정·시행, 이름을 「금융지주회사 통합위험관리 모범규준」으로 변경(행정지도 내역 감총그룹-388) | 2-5 |")
    w("| 2017.2.15~3.7 | 존속기한(2017.4.1.~2018.3.31.) 연장 예고 | 2-6 |")
    w("| 2017.4.1 | 존속기한 연장 통보(감총그룹-192), 유효기간 ’17.4.1~’18.3.31 | 2-7 |")
    w("| 2018.4.1 | [폐지일자](감총그룹-192 건) — 존속기한 도래 | 2-7 |")
    w("| 2021.9.18 | [폐지일자](감총그룹-388 건) — 존속기한 도래 | 2-5 |")
    w("")
    w("note: 같은 관리번호 2014-017 의 두 기록이 폐지일자를 다르게 적음(2018.4.1 / 2021.9.18). 2017.4.1 통보가 존속기한을 2018.3.31 까지로 "
      "연장했고 이후 연장 예고·통보는 「행정지도 예고」·「행정지도 내역」 검색에서 찾지 못함(추출 범위에 없음) — (판단) 실제 효력은 2018.3.31 로 끝났고 "
      "2021.9.18 은 앞 기록(2016.8.1 시행분)의 전산상 정리일로 보임. 단정하지 않음.")
    w("")
    # 2-1, 2-2 보도자료
    for no, p, ntt, title in (("2-1", PR2011, "8584", "2011.7.4(월) 조간 — 「금융지주회사 통합리스크관리 모범규준」 마련 추진"),
                              ("2-2", PR2012, "9084", "2012.3.20(화) 조간(배포 2012.3.19) — 「금융지주회사 통합리스크관리 모범규준」 마련")):
        mp = meta(p)
        w("### %s 금감원 보도자료 %s" % (no, title))
        w("")
        w("[금융감독원 보도자료 · %s · 첨부 `%s`(hwp, sha256 %s) · 전문(책임자·담당자 줄만 가림) · 수집 %s]" % (BODO_VIEW % ntt, os.path.basename(p),
                                                                           mp["sha256"][:16], TODAY))
        w("")
        L.extend(code(press_lines(p)))
        w("")
        if ntt == "8584":
            w("note: [표 깨짐: 「<금융지주회사법상 지주회사의 업무범위>」·「<실태조사 대상>」 안쪽 표를 hwp2md 가 `[내부표] | … |` 로 한 칸에 펼침 — 칸 구분 "
              "`|`·`/` 는 변환기 표시이고 원문 글자는 그대로]")
        else:
            w("note: (판단) 보도자료의 「사외이사가 과반수」·「위원장은 리스크 전문성」 = 2012 판 9조①, 「그룹 CRO … 임기내 해임을 금지」 = 2012 판 11조①⑤, "
              "「M&A 등 … GRMC의 사전심의」 = 10조②, 「통합위기상황분석」·「조기경보체계 및 비상계획」 = 55~57조, 「그룹리스크협의회 설치를 의무화」 = 12조, "
              "「그룹 리스크 철학」 = 4·5조.")
            w("note: 보도자료는 「그룹리스크협의회 설치를 의무화」라고 적었으나 본문 7조②는 「구성할 수 있다」, 12조①은 「설치하고 … 위임할 수 있다」 "
              "(원문과 다른 곳 목록에 올림).")
        w("")
    # 2-3 ~ 2-7 금감원 행정지도 화면
    PAGES = [
        ("2-3", "fss/admnPrvntc_view_29.html", PRVV % "29", "행정지도 예고 — 「금융지주회사 통합리스크관리 모범규준」존속기한 연장 예고(2016-01-12 ~ 2016-02-01)",
         "의견을 제출하고자 하시는", ["목록\n행정지도에 대한 의견제출", "행정지도에 대한 의견제출"]),
        ("2-4", "fss/admnPrvntc_view_51.html", PRVV % "51", "행정지도 예고 — 지배구조법 시행에 따른 개정안(2016-07-08 ~ 2016-07-28)",
         "의견을 제출하고자 하시는", ["목록\n행정지도에 대한 의견제출", "행정지도에 대한 의견제출"]),
        ("2-5", "fss/admin_view_20170210165649943.html", ADMV % "20170210165649943", "행정지도 내역 — 관리번호 2014-017, 감총그룹-388, 시행일 20160801",
         "해당 페이지 인쇄", ["\n목록\n"]),
        ("2-6", "fss/admnPrvntc_view_67.html", PRVV % "67", "행정지도 예고 — 존속기한 연장 예고(2017-02-15 ~ 2017-03-07)",
         "의견을 제출하고자 하시는", ["목록\n행정지도에 대한 의견제출", "행정지도에 대한 의견제출"]),
        ("2-7", "fss/admin_view_20170328150222228.html", ADMV % "20170328150222228", "행정지도 내역 — 관리번호 2014-017, 감총그룹-192, 시행일 20170401",
         "해당 페이지 인쇄", ["\n목록\n"]),
    ]
    for no, rel, url, title, start, ends in PAGES:
        p = os.path.join(D, rel)
        lines = page_lines(p, start, ends)
        if start.startswith("의견을"):
            lines = lines[1:]                                       # 안내문 둘째 줄(「…서면으로 제출하여 주시기 바랍니다.」)은 빼고 제목부터
        w("### %s 금감원 %s" % (no, title))
        w("")
        w("[금융감독원 금융행정지도 · %s · 화면 본문 · 수집 %s · 원본 `%s` sha256 %s]" % (url, TODAY, rel, meta(p)["sha256"][:16]))
        w("")
        L.extend(code(redact(lines)))
        w("")
    w("note: 2-4 의 「3. 행정지도의 내용」은 「제9조제6항제5호 삭제」라고 적었으나, 2016.8.1 판 본문 9조⑥5호는 「｢그룹위험관리규정｣의 제정 및 개정」으로 남아 "
      "있다. 또 2-4 는 11조(그룹위험관리책임자) ①~⑤·⑦ 삭제를 적지 않았으나 2016.8.1 판은 이를 「<삭제 2016. 8. 1.>」로 표시(아래 4장).")
    w("")

    # ── 3. 조 번호·제목
    w("## 3. 조 번호·제목 목록(기준판 2016.8.1 + 2012.3.13 제정판 제목)")
    w("")
    w("[금감원 행정지도 내역 2014-017(감총그룹-388) 첨부 「붙임2_금융지주회사 통합위험관리 모범규준 개정 후 전문.hwp」 · %s · 조 제목 · 수집 %s]"
      % (ADMV % "20170210165649943", TODAY))
    w("")
    w("| 조 | 장 | 절 | 제목(2016.8.1 판) | 제목(2012.3.13 제정판) | 2016.8.1 판 본문 개정·삭제 표시 | 시트 행(3~58) |")
    w("|---|---|---|---|---|---|---|")
    for r in rows:
        w("| %d | %s | %s | %s | %s | %s | %s |" % (r["조"], r["장"], r["절"] or "-", r["제목_2016.8.1판"], r["제목_2012.3.13제정판"],
                                                 r["2016.8.1판_본문표시"] or "-", r["사용자시트범위(3~58조)"]))
    w("")
    w("note: 장 제목 「제 7 장 보칙<삭제 2016. 3. 28.>」은 2016.8.1 판 원문 표기. 2016.7 예고안의 조 제목은 2016.8.1 판과 모두 같음(CSV 의 "
      "「제목_2016.7개정예고안」 칸).")
    w("note: 지시서에 나온 조 번호와 원문 제목 대조 — 3조(적용대상), 4조(위험관리 철학), 5조(위험관리 원칙), 9조(그룹위험관리위원회) ⑦=보고사항, "
      "17조(의사전달체계), 21조(신용위험), 22조(시장위험), 24조(금리위험), 27조(전략 및 평판위험), 28조(시스템 구축 및 관리), "
      "30조(목적 — 제4절 적합성 검증의 첫 조), 34조(해외위험 관리), 53조(위기대응조직), 55조(조기경보체계), 57조(비상계획).")
    w("note: (판단) 「위험이 경미한 자회사를 적용에서 빼는 기준」(지시서 3조)은 3조 단서 외에 18조③ 단서(통합위험 측정 제외)와 36조 단서"
      "(「비중이 미미(예: 자산비중 5% 미만)하거나 비금융회사인 자회사등」 내부자본 적정성 평가 제외)에도 있음.")
    w("note: (판단) 「발령 단계」(지시서 55조)는 55조②가 「조기경보 발령에 따른 대응방안」을, 52조③이 「위기상황단계」 설정을 정함 — 단계 수·이름은 "
      "모범규준에 없음(각 사 내규 몫).")
    w("")

    # ── 4. 판 사이 달라진 조문
    w("## 4. 판 사이 달라진 조문(원문 대조)")
    w("")
    w("방법: 2012 판 본문에서 「리스크」→「위험」 등 용어만 바꾼 뒤(그룹리스크관리최고책임자→그룹위험관리책임자, 리스크관리최고책임자→위험관리책임자, "
      "그룹리스크협의회→그룹위험관리협의회, 리스크 철학→위험관리 철학, 조사 맞춤) 2016.8.1 판과 줄마다 비교. 용어 말고도 달라진 조: %s. "
      "2016.7 예고안과 2016.8.1 판이 다른 조: %s." % (", ".join("%d조" % n for n in diff12), ", ".join("%d조" % n for n in diffp)))
    w("")
    for n in sorted(set(diff12) | set(diffp)):
        w("### 제%d조(%s)" % (n, A16[n]["제목"]))
        w("")
        w("2012.3.13 제정판 [`%s`]" % os.path.basename(F2012))
        w("")
        L.extend(code(art_text(b12, n)))
        w("")
        if n in diffp:
            w("2016.7 개정 예고안 [`%s`]" % os.path.basename(F2016P))
            w("")
            L.extend(code(art_text(b16p, n)))
            w("")
        w("2016.8.1 판 [`%s`]" % os.path.basename(F2016))
        w("")
        L.extend(code(art_text(b16, n)))
        w("")
    w("### 부칙")
    w("")
    for lab, body in (("2012.3.13 제정판", b12), ("2016.7 개정 예고안", b16p), ("2016.8.1 판", b16)):
        w(lab)
        w("")
        ls = []
        for kk, v in body.items():
            if isinstance(kk, str) and kk.startswith("부칙"):
                ls.extend(l for l in v if l.strip())
        L.extend(code(ls))
        w("")
    w("note: 2016.8.1 판 부칙 제2조는 「그룹리스크관리위원회」(옛 용어)를 그대로 두었고, 2016.7 예고안은 「그룹위험관리위원회」로 고쳤음. "
      "9조①은 2016.8.1 판에서 한 항(위원장 요건)으로 줄었는데 부칙 제2조는 여전히 「제9조제1항부터 제4항까지」라고 적음.")
    w("note: 2016.8.1 판에서 조문별 「<개정 …>」 표시는 9조①에만 있고, 「리스크」→「위험」 용어 변경(이름 포함)에는 조문별 표시가 없음.")
    w("")

    # ── 5. 전문
    w("## 5. 전문 — 2016.8.1 판(기준판, 「금융지주회사 통합위험관리 모범규준」)")
    w("")
    w("[금감원 행정지도 내역 2014-017(감총그룹-388, 시행일 20160801) 첨부 「붙임2_금융지주회사 통합위험관리 모범규준 개정 후 전문.hwp」 · %s · "
      "전문 · 수집 %s · sha256 %s]" % (ADMV % "20170210165649943", TODAY, m16["sha256"]))
    w("")
    L.extend(code(rd(F2016 + ".md").rstrip("\n").split("\n")))
    w("")
    w("## 6. 부록 — 2012.3.13 제정판 전문(「금융지주회사 통합리스크관리 모범규준」)")
    w("")
    w("[금감원 행정지도 예고 seqno=29(2016-01-12 게시, 존속기한 연장 예고) 첨부 「통합리스크관리_모범규준(게시)F_.hwp」 · %s · 전문 · 수집 %s · "
      "sha256 %s]" % (PRVV % "29", TODAY, m12["sha256"]))
    w("")
    L.extend(code(rd(F2012 + ".md").rstrip("\n").split("\n")))
    w("")
    w("note: 이 판은 본문 머리에 「2012. 3. 13. 제정」만 있고 개정 표시가 없음 — 2016.1 게시 시점(2016.3.28 개정 전)의 본문(판단: 제정판 그대로).")
    w("")

    # ── 7. 로컬 텍스트 인용
    w("## 7. 로컬 텍스트(8·9차 공시 텍스트)에서 이 모범규준을 인용한 문장")
    w("")
    lc = list(csv.DictReader(open(LOCAL_CSV, encoding="utf-8-sig")))
    cnt = Counter(r["분류"] for r in lc)
    w("검색: `dart_out/text/risk8/*.txt`(%d개), `dart_out/text/risk9/*.txt`(%d개) 전부에서 공백·줄바꿈을 뺀 글자열로 「모범규준」을 찾고(줄 끝에서 끊긴 "
      "「모\\n범규준」도 잡음), 바로 앞 글자로 갈랐다. 전부 %d곳 — 목록은 `%s`." % (
          len([f for f in os.listdir(LOCAL_DIRS[0]) if f.endswith(".txt")]),
          len([f for f in os.listdir(LOCAL_DIRS[1]) if f.endswith(".txt")]), len(lc), LOCAL_CSV))
    w("")
    w("| 분류(앞 글자 기준) | 곳 |")
    w("|---|---|")
    for kk, v in cnt.most_common():
        w("| %s | %d |" % (kk, v))
    w("")
    w("쪽 = 텍스트 파일의 「=== p.N ===」 표지(PDF 쪽 순번). 인쇄 쪽 번호가 다르면 함께 적음.")
    w("")
    T8 = LOCAL_DIRS[0]
    QUOTES = [
        ("우리금융지주 증권신고서(주식이전) · 접수번호 20181108000394", os.path.join(T8, "증권신고서__우리금융지주__20181108000394.txt"),
         "우리금융그룹의 리스크관리 개요", "범규준” 상에서 요구하는 내용을 충분히 반영하여 구축할 계획입니다.", "(인쇄 「Page 220」)", "7·9·14·19·37조(판단)"),
        ("우리금융지주 증권신고서(주식이전) · 접수번호 20181108000394", os.path.join(T8, "증권신고서__우리금융지주__20181108000394.txt"),
         "[금융지주회사의 통합리스크관리 모범규준의 주요 내용]", "부자본 적정성 평가 및 관리 체제를 구축·운영하여야 함", "(인쇄 「Page 220」, 본문 옆 상자글)",
         "7·9·14·19·37조(판단)"),
        ("KB금융지주 「2025년 지배구조 및 보수체계 연차보고서」 · https://www.kbfg.com/api/download/board/14406",
         os.path.join(T8, "연차보고서__KB금융지주_지배구조연차보고서_2026.txt"), "지주회사 및 계열사의 리스크 관리에 대한 기본적인 절차와 기준을 정한",
         "[2025.3.26. 개정사항]", "(인쇄 쪽 25)", "연혁(전체)"),
        ("신한금융지주 「2025 지배구조 및 보수체계 연차보고서」 · https://www.shinhangroup.com/main/downloadAttach?attachNo=55653e68caad4dffa2f2e55c8401e6cb&seq=1",
         os.path.join(T8, "연차보고서__신한금융지주_지배구조연차보고서_2026.txt"), "당사는 금융회사의 지배구조에 관한 법률에서는 별도로 규정하지 않았으나",
         "제반 리스크 관련 세부사항을 자회사 위험관리책임자들과 협의하는 통로로", "", "7조②·12조(판단)"),
        ("신한금융지주 「2025 지배구조 및 보수체계 연차보고서」 · https://www.shinhangroup.com/main/downloadAttach?attachNo=55653e68caad4dffa2f2e55c8401e6cb&seq=1",
         os.path.join(T8, "연차보고서__신한금융지주_지배구조연차보고서_2026.txt"), "당사는 “지속 가능한 성장을 위해",
         "⑦ 평상시에도 상황 악화가능성에 대비하는 신중한 시각을 공유한다.", "(인쇄 쪽 158)", "4·5조"),
        ("신한금융지주 사업보고서(2025.12) · 접수번호 20260318000826", os.path.join(T8, "사업보고서__신한금융지주__20260318000826.txt"),
         "1) 그룹 위험관리 원칙", "ㆍ 선제적이고 실용적인 위험 관리 기능을 지향한다.", "(인쇄 「Page 787」 다음 쪽)", "4·5조"),
        ("메리츠금융지주 「2025년 지배구조 및 보수체계 연차보고서」 · https://www.meritzgroup.com/commfiles/hld/attach/2026/20260311/202603111712088150009U.pdf (참고 — 「모범규준」 낱말은 없으나 지시서가 든 9조 7항·57조 인용)",
         os.path.join(T8, "연차보고서__메리츠금융지주_지배구조연차보고서_2026.txt"), "가. 그룹리스크관리규정 제9조 7항에 의거, 2024년 4분기",
         "다. 그룹리스크관리규정 제9조 7항에 의거, 그룹리스크협의회 및 계열사 리스크관리위원회의 결의사항 보고", "", "9조⑦·56~58조(판단)"),
    ]
    for doc, path, s0, s1, extra, jo in QUOTES:
        lines, pg, i, j = local_block(path, s0, s1)
        w("[%s · 쪽 p.%s %s · 줄 %d-%d · `%s` · 수집(텍스트화) 8차] — 모범규준 조: %s" % (doc, pg, extra, i, j, path, jo))
        w("")
        L.extend(code(lines))
        w("")
    w("note: 우리금융지주 2018.11 증권신고서는 「금융지주회사 통합리스크관리 모범규준」(2016.8.1 이전 이름)과 2012 판 용어(리스크관리 최고책임자·"
      "그룹리스크관리위원회)로 적었음 — 이 신고서 접수(2018.11.8) 때는 모범규준 존속기한(2018.3.31)이 이미 지난 뒤(원문과 다른 곳 목록에 올림).")
    w("note: 상자글 「나. 그룹리스크관리위원회」의 「분기 1회 이상 회의」 = 9조⑤, 「위원장은 … 전문적인 판단」 = 2012 판 9조①2호(2016 판 9조①); "
      "「다. 리스크통제」 = 14조①; 「라. 리스크측정」 = 19조①; 「마. 자본적정성 평가 및 관리체제」 = 37조①; 「가. 리스크관리조직」 = 7조①(판단). "
      "상자글의 「라.」 아래 빈 「ㆍ」 줄은 원문 텍스트 그대로.")
    w("note: KB 연차보고서의 「통합 리스크관리 모범규준」은 정식 이름(「금융지주회사 통합리스크관리 모범규준」)과 띄어쓰기·앞부분이 다름; "
      "KB 리스크관리규정 2012.5.30 개정이 이 모범규준(2012.3.13 제정, 4.1 시행)을 반영했다는 기록.")
    w("note: 신한의 「그룹리스크관리모범규준」·「리스크관리 모범규준」은 지주가 자회사에 제시하는 신한 자체 규준(판단: 문장 주어가 「지배기업은」·「회사는」). "
      "다만 신한의 리스크 철학은 모범규준 4조①의 「최상위 가치규범」 자리에, 원칙 ①·⑦은 5조②1호·5호와 글이 거의 같고, ③·④·⑤·②는 5조②2호·3호·4호·6호와 뜻이 맞음(판단 — 대조는 9-4-3 몫). 같은 문장이 신한 사업보고서 "
      "FY2023(20240318000635, 정정 20240502000081)·FY2024(20250318000993)·FY2025(20260318000826)의 여러 쪽에 되풀이됨(목록 CSV).")
    w("note: 신한 연차보고서의 「이전 모범규준」·「모범규준 상 경영관리협의회 / 위험관리협의회」가 어느 모범규준인지는 글에 없음. 「위험관리협의회」라는 "
      "이름은 이 모범규준(2012 판 「그룹리스크협의회」, 2016 판 「그룹위험관리협의회」)과 다름 — (판단) 2014.12 「금융회사 지배구조 모범규준」을 가리킬 수 있음.")
    w("note: 메리츠 인용 「그룹리스크관리규정 제9조 7항」(리스크상태·한도관리 현황, 협의회·계열사 위원회 결의사항 보고)은 모범규준 9조⑦2·3호와 내용이 맞고, "
      "「제57조, 제58조」(그룹 통합 위기상황분석 및 유동성 관리현황 보고)는 모범규준 56조(통합위기상황분석)·57조(비상계획) 쪽 내용 — 번호가 하나 "
      "어긋날 수 있음(판단, 메리츠 규정 원문 확인은 9-4-1 몫).")
    w("note: 조문 번호를 들어 이 모범규준을 인용한 공시 문장(「모범규준 제N조」 꼴)은 risk8·risk9 텍스트에서 찾지 못함 — 추출 범위에 없음 "
      "(신한 연차보고서 p.200 「근거(모범규준§3)」는 보수·인력 항목의 다른 모범규준으로 보임, 판단).")
    w("")

    # ── 8. 찾은 경로
    w("## 8. 찾은 경로·검색어(전부)")
    w("")
    w("### 8-1 웹 검색(WebSearch 도구) 질의")
    w("")
    for q in WEBSEARCH:
        w("- %s" % q)
    w("")
    w("note: 검색 결과에서 고른 후보 — law.kofia.or.kr seq=156(·155), etoday 454869(2011-07-03), hankyung 2012031942166(2012-03-19), "
      "inews24 1104180(2018-06-26), kiri.or.kr docId=3403, kcmi.re.kr fid=4882. 결과는 아래 8-2.")
    w("")
    w("### 8-2 받은 곳별 결과")
    w("")
    rl = list(csv.DictReader(open(LOG_CSV, encoding="utf-8-sig"))) if os.path.exists(LOG_CSV) else []
    rob = {}
    for r in rl:
        if r["URL"].endswith("/robots.txt"):
            rob[r["URL"]] = r["결과"]
    w("robots.txt(web13.Robots) 판정: " + " ; ".join("%s → %s" % (u, v) for u, v in sorted(rob.items())))
    w("")
    w("note: law.kofia.or.kr·www.kiri.or.kr 의 /robots.txt 는 HTTP 200 으로 HTML 오류·첫 화면을 돌려줌 → 규칙 없음(제한 없음)으로 판정됨. "
      "www.kfb.or.kr(은행연합회)은 「User-agent: * / Disallow: /」 → 받지 않음.")
    w("")
    kf = list(csv.DictReader(open(KOFIA_CSV, encoding="utf-8-sig")))
    lw = list(csv.DictReader(open(LAW_CSV, encoding="utf-8-sig")))
    pr = list(csv.DictReader(open(PRESS_CSV, encoding="utf-8-sig")))
    ad = list(csv.DictReader(open(ADMIN_CSV, encoding="utf-8-sig")))
    w("| 곳 | 찾은 방법 | 결과 |")
    w("|---|---|---|")
    w("| 금융투자협회 법규정보시스템 law.kofia.or.kr | 검색 결과의 seq=156(historySeq=451) 전체화면, seq=155(historySeq=1800) 전체화면, 통합검색(POST "
      "searchTotal.do) 연혁 포함 규정명 「모범규준」「지주」「통합」「위험관리」, 규정내용 「금융지주회사 통합」「통합위험관리」「통합리스크관리」 | "
      "seq=156 = 「금융투자회사의 금융사고 방지를 위한 모범규준」, seq=155 = 「금융투자회사의 리스크관리 모범규준」(운영부서 자율규제기획부, 2012-10-26~2026-07-09 판). "
      "규정명 「지주」·「통합」 0건, 규정내용 3개 낱말 0건, 「위험관리」 1건(단기금융간접투자기구 위험관리기준 표준안). 「모범규준」 연혁 106건 중 1쪽(10건)만 — "
      "2쪽 요청은 사이트 방화벽 차단 응답(「KOFIA web-firewall security policies …」)이 와서 멈춤(우회 안 함). seq 만 준 요청도 같은 차단 응답. 목록 `%s` |" % KOFIA_CSV)
    lawn = Counter((r["검색어"], r["nw"], r["전체건수"]) for r in lw)
    w("| 법제처 Open API(행정규칙) | lawSearch.do target=admrul, nw=1(현행)·2(연혁), 질의 %s | %s. 「금융지주회사」 연혁 88건은 감독규정·시행세칙·일괄개정·등기예규뿐. "
      "→ 모범규준은 법제처 행정규칙으로 등록되지 않음(판단: 행정지도라서). 목록 `%s`, ledger `dart_out/raw/web13/law/_call_log.csv`(OC=***) |"
      % (" · ".join(LAW_Q), " ; ".join("%s nw=%s %s건" % k for k in sorted(lawn) if k[0] != "금융지주회사"), LAW_CSV))
    prs = {}
    for r in pr:
        st = r["사이트총건수"] + "건" if r["사이트총건수"] != "" else ("멈춤(접속 실패)" if r["비고"].startswith("멈춤") else "요청 안 함(앞에서 멈춤)")
        prs[(r["게시판"], r["낱말"], r["검색구분"])] = st
    w("| 금감원 보도자료(B0000188)·금융위 보도자료(/no010101) | 2011-01-01~2016-12-31, 낱말: %s | %s. 금감원에서 8584(2011-07-04)·9084(2012-03-19) 두 건을 "
      "받음(2-1·2-2). 금융위 게시판은 첫 실행 때 「통합 리스크관리」에서 접속 실패(프록시 ws_closed_mid_exchange)로 멈췄고, 다시 실행해 나머지를 받음 — 통합·리스크관리 낱말 0건, 제목 「모범규준」 9건(금융소비자보호·지배구조·커버드본드 등) 가운데 이 모범규준 없음 → 금융위 보도자료에서는 추출 범위에 없음. 목록 `%s` |"
      % (" · ".join(k for k, s in PRESS_TERMS), " ; ".join("%s 「%s」(%s) %s" % (a, b, {"all": "제목+내용", "title": "제목"}[c], v)
                                                       for (a, b, c), v in sorted(prs.items())), PRESS_CSV))
    ads = Counter((r["검색어"], r["사이트총건수"]) for r in ad)
    w("| 금감원 금융행정지도 「행정지도 내역」 | 시행여부=전체(T), 주제어: %s | %s. 관리번호 2014-017 두 건(2-5·2-7)과 첨부 전문을 받음. 목록 `%s` |"
      % (" · ".join(ADMIN_TERMS), " ; ".join("%s %s건" % k for k in sorted(ads)), ADMIN_CSV))
    pv = []
    for kw in PRVNTC_TERMS:
        p = os.path.join(D, "fss", "admnPrvntc_%s_p01.html" % kw)
        if os.path.exists(p):
            mm = re.search(r"전체\s*<em>([\d,]+)</em>", rd_bytes(p).decode("utf-8", "replace"))
            pv.append("%s %s건" % (kw, mm.group(1) if mm else "?"))
    w("| 금감원 금융행정지도 「행정지도 예고」 | 제목 검색: %s | %s. 「지주」 6건 중 이 모범규준 관련 4건(seqno 1·29·51·67) — 2-3·2-4·2-6 과 첨부(seqno 29·51)를 받음. "
      "seqno 67 첨부(두 모범규준 합본 hwp)는 2017.4.1 판 첨부와 같은 시기 자료라 받지 않음 |" % (" · ".join(PRVNTC_TERMS), " ; ".join(pv)))
    w("| 금감원 「행정지도 내역」 2014-018 | 「지주회사」 검색 결과 | 「금융지주회사의그룹내부통제기준모범규준」(시행일 20120401, 폐지 2016.4.1) — 다른 모범규준이라 첨부를 받지 않음(상세 화면만) |")
    w("| 은행연합회 www.kfb.or.kr | robots.txt | 「Disallow: /」 — 수집 안 함 |")
    w("| 한국경제 hankyung.com/article/2012031942166 | 검색 결과 기사(2012-03-19) | HTTP 403 — 멈춤(amp 등 다른 주소로 다시 시도하지 않음) |")
    w("| 이투데이 etoday.co.kr/news/view/454869 | 검색 결과 기사 | 2011-07-03 「금감원, 금융지주사 리스크관리 모범규준 추진」 — 금감원 2011.7.4 보도자료와 같은 내용(2차 자료라 인용 안 함) |")
    w("| 아이뉴스24 inews24.com/view/1104180 | 검색 결과 기사 | 2018-06-26 금융그룹 통합감독(다른 모범규준) — 대상 아님 |")
    w("| 보험연구원 kiri.or.kr docId=3403(pdf) | 검색 결과 | 2010.2 「금융지주회사의 그룹 내부통제 모범규준」 동향(1쪽) — 대상 아님 |")
    w("| 자본시장연구원 kcmi.re.kr fid=4882(pdf, 560쪽) | 검색 결과 「2011년 자본시장 제도동향」 | 「통합위험」「통합리스크」 0곳, 「지주」는 금융지주회사감독규정 개정만 — 추출 범위에 없음 |")
    w("| 학술·용역 보고서·지주사 연차보고서의 조문 인용 | 위 검색, 로컬 텍스트 검색(7장) | 조 번호를 든 인용은 추출 범위에 없음 |")
    w("")

    # ── 9. 받은 것 / 받지 못한 것 / 원문과 다른 곳
    w("## 9. 받은 것 / 받지 못한 것 / 원문과 다른 것을 발견한 곳")
    w("")
    w("| 구분 | 항목 | 출처·근거 | 모범규준 조 |")
    w("|---|---|---|---|")
    w("| 받은 것 | 2016.8.1 판 전문(1~59조·부칙, 기준판) | 행정지도 내역 2014-017 감총그룹-388 첨부 | 3~58조 전부 |")
    w("| 받은 것 | 2012.3.13 제정판 전문 | 행정지도 예고 seqno=29 첨부 | 3~58조 전부(9·11조 옛 문구) |")
    w("| 받은 것 | 2016.7 개정 예고안 본문·예고 사유 | 행정지도 예고 seqno=51 | 4·5·7·9·11조 등 |")
    w("| 받은 것 | 2017.4.1 존속기한 연장 첨부(2016.8.1 판과 같은 파일) | 행정지도 내역 2014-017 감총그룹-192 | — |")
    w("| 받은 것 | 연혁 근거(추진·마련 보도자료, 연장·개정 예고, 행정지도 내역 2건) | 2장 | 전체 |")
    w("| 받은 것 | 조 번호·제목 목록 CSV | `%s` | 1~59조 |" % JO_CSV)
    w("| 받은 것 | 로컬 공시 텍스트 인용(우리 2018 증권신고서, KB·신한 연차보고서, 신한 사업보고서) | 7장 | 4·5·7·9·12·14·19·37조(판단) |")
    w("| 받지 못한 것 | 2016.3.28 개정 공문·신구대비표 | 행정지도 내역·예고 검색(8-2) — 추출 범위에 없음 | 59조 |")
    w("| 받지 못한 것 | 2012.3.13 제정 당시 송부 공문 | 행정지도 내역 검색(「통합리스크」 1건뿐, 2016 기록) — 추출 범위에 없음 | — |")
    w("| 받지 못한 것 | 2018.3.31 이후 연장 여부 | 행정지도 예고(「지주」 6건)·내역 검색 — 추출 범위에 없음 | — |")
    w("| 받지 못한 것 | 금융위 보도자료 가운데 이 모범규준 발표 | 2011~2016 낱말 검색 0건(8-2) — 추출 범위에 없음(금감원 보도자료로 대신) | — |")
    w("| 받지 못한 것 | 은행연합회 자료 | robots.txt Disallow | — |")
    w("| 받지 못한 것 | 한국경제 2012-03-19 기사 | HTTP 403 | — |")
    w("| 받지 못한 것 | 금융투자협회 법규정보시스템 「모범규준」 연혁 2쪽 이후 | 방화벽 차단 응답 | — |")
    w("| 원문과 다른 곳 | 이름: 지시서 「금융지주회사 통합위험관리 모범규준」은 2016.8.1 이후 이름. 제정 이름은 「금융지주회사 통합리스크관리 모범규준」 | 2-5 「2016.8.1. … 명칭 변경」 | 전체 |")
    w("| 원문과 다른 곳 | 폐지일자 두 기록(2018.4.1 / 2021.9.18) | 2-5·2-7 | — |")
    w("| 원문과 다른 곳 | 2016.7 예고 「제9조제6항제5호 삭제」 ↔ 2016.8.1 판 9조⑥5호 존치 | 2-4, 4장 | 9조 |")
    w("| 원문과 다른 곳 | 2016.7 예고·예고안에 없던 11조①~⑤·⑦ 삭제가 2016.8.1 판에 있음 | 4장 | 11조 |")
    w("| 원문과 다른 곳 | 예고안 「위험관리전담조직」 ↔ 2016.8.1 판 「위험관리부서」(4조③·5조②3호·7조①) | 4장 | 4·5·7조 |")
    w("| 원문과 다른 곳 | 2016.8.1 판 부칙 제2조 「그룹리스크관리위원회」(옛 용어), 「제9조제1항부터 제4항까지」(9조①은 한 항으로 줄어듦) | 4장 부칙 | 9조 |")
    w("| 원문과 다른 곳 | 2012 보도자료 「그룹리스크협의회 설치를 의무화」 ↔ 본문 7조② 「구성할 수 있다」·12조① 「설치하고 … 위임할 수 있다」 | 2-2 | 7·12조 |")
    w("| 원문과 다른 곳 | 2011 보도자료 「11월말까지 관련 작업을 마칠 계획」 ↔ 제정 2012.3.13 | 2-1 | — |")
    w("| 원문과 다른 곳 | 지시서 「iM 28조(통합리스크관리시스템), 30조(적합성 검증)」 ↔ 모범규준 28조 제목 「시스템 구축 및 관리」, 30조 제목 「목적」(제4절 적합성 검증) | 3장 | 28·30조 |")
    w("| 원문과 다른 곳 | KB 연차보고서 「통합 리스크관리 모범규준」(이름 줄여 씀) | 7장 | — |")
    w("| 원문과 다른 곳 | 우리 2018.11 증권신고서가 존속기한(2018.3.31) 지난 모범규준을 옛 이름·옛 용어로 인용 | 7장 | 7·9·14·19·37조 |")
    w("| 원문과 다른 곳 | 금융투자협회 seq=155·156 은 「금융투자회사의 리스크관리 모범규준」·「금융투자회사의 금융사고 방지를 위한 모범규준」 — 이 모범규준 아님 | 8-2 | — |")
    w("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(OUT_MD, len(L), "줄 ;", JO_CSV, len(rows), "행 ; diff12", diff12, "diffp", diffp)


def cmd_robots(hosts):
    for h in hosts:
        r = robots(h)
        print(h, r.status, r.note[:200])


def cmd_get(name, url):
    b, m, p = cached(name, url)
    print(p, m.get("http_status"), m.get("content_type"), len(b))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    try:
        if cmd == "robots":
            cmd_robots(argv[2:])
        elif cmd == "get":
            cmd_get(argv[2], argv[3])
        elif cmd == "kofia":
            cmd_kofia()
        elif cmd == "law":
            cmd_law()
        elif cmd == "press":
            cmd_press()
        elif cmd == "admin":
            cmd_admin()
        elif cmd == "local":
            cmd_local()
        elif cmd == "prvntc":
            cmd_prvntc()
        elif cmd == "docs":
            cmd_docs()
        elif cmd == "build":
            cmd_build()
        else:
            print(__doc__)
            return 1
    except Stop as e:
        print("STOP:", e)
    finally:
        flush_log()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
