# -*- coding: utf-8 -*-
"""15차 경영공시 g2 — 메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주 FY2019~FY2025
정기 경영공시(12월말 기준분) 수집·쪽 텍스트·작업 B(겸직·파견 등)·작업 D(업무위탁 등) 조각.

    python3 scripts/dart/ops15_mgmt_g2.py robots   # 5개 호스트 robots.txt(web13.Robots, RFC 9309) + 첫 화면(약관 링크 찾기)
    python3 scripts/dart/ops15_mgmt_g2.py page <회사> <url> <이름> [--post k=v&..] [--referer URL]   # 목록 화면 하나(robots 확인 뒤)
    python3 scripts/dart/ops15_mgmt_g2.py fetch    # 저장한 목록 화면에서 FY 별 12월말 기준분 고르고 PDF 받기 → 목록 CSV
    python3 scripts/dart/ops15_mgmt_g2.py text     # 받은 PDF → 「## p.N」 md (venv 파이썬 -I, 경로는 인자)
    python3 scripts/dart/ops15_mgmt_g2.py extract  # md 에서 B·D 조각 + 원문 md (네트워크 없음, 다시 돌리면 같은 결과)
    python3 scripts/dart/ops15_mgmt_g2.py list     # 목록 CSV 만 다시 씀(네트워크 없음 — fetch·text 끝에도 자동)

HTTP 는 web13.Web(UA 고정 「lastprice-research/1.0 …」·요청 간 1.2초·같은 요청 3회까지 = 재시도 2회). 우회 없음.
원본: dart_out/raw/mgmt15/<회사>/ (git 무시). 목록 화면은 dart_out/raw/mgmt15/<회사>/_pages/.
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
import urllib.robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import web13  # noqa: E402
web13.RAW = os.path.join("dart_out", "raw", "mgmt15")
from web13 import Web, Robots, now, save  # noqa: E402

RAW = web13.RAW
TXT = os.path.join("dart_out", "text", "ops15")
OPS = os.path.join("dart_out", "ops15")
LIST = os.path.join(OPS, "경영공시15_목록_g2.csv")
FRAG = os.path.join(OPS, "조각")
ORIG = os.path.join(OPS, "원문")
VENV = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python"
PDF2MD = os.path.join(HERE, "ops15_mgmt_g2_pdf2md.py")
FYS = range(2019, 2026)
COS = ["메리츠금융지주", "iM금융지주", "BNK금융지주", "JB금융지주", "한국투자금융지주"]
HOSTS = {"메리츠금융지주": "https://www.meritzgroup.com", "iM금융지주": "https://www.imfngroup.com",
         "BNK금융지주": "https://www.bnkfg.com", "JB금융지주": "https://www.jbfg.com",
         "한국투자금융지주": "https://www.koreaholdings.com"}
TEXTFAIL = os.path.join(RAW, "text_fail.json")      # 글 추출 실패(글자층 없음·깨짐) — 목록 status 에 반영
TEXTSTAT = os.path.join(RAW, "text_stats.json")
LIST_COLS = ["corp_label", "fy", "period_원문", "url", "posted_at", "fetched_at", "bytes", "pages", "sha256",
             "robots_verdict", "terms_note", "status", "note"]


def P(co, name):
    return os.path.join(RAW, co, "_pages", name)


def rd(path):
    return open(path, encoding="utf-8", errors="replace").read()


# ── robots ────────────────────────────────────────────────────────────────
def robots_rp(co, url):
    """저장한 robots 판정으로 url 허용 여부. (허용, 설명)."""
    d = os.path.join(RAW, co)
    host = urllib.parse.urlparse(url).netloc
    rob = sorted(f for f in os.listdir(d) if f.startswith("robots_" + host) and not f.endswith(".meta.json"))
    if not rob:
        return False, "robots 판정 없음(받지 않음)"
    if not rob[0].endswith(".txt"):
        return True, "robots.txt 4xx — 제한 없음(RFC 9309 §2.3.1.3)"
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(rd(os.path.join(d, rob[0])).splitlines())
    return rp.can_fetch(web13.UA, url), "robots.txt 규칙"


def cmd_robots():
    w = Web()
    out = {}
    for co in COS:
        base = HOSTS[co]
        r = Robots(w, base, co)
        out[co] = dict(base=base, status=r.status, note=r.note, checked_at=now())
        print(co, r.status, r.note[:100])
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(os.path.join(RAW, "robots_판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


_IM_POST = ("IN_DATA_JSON=%257B%2522bbs_no%2522%253A%252213%2522%252C%2522col_nm%2522%253A%2522putup_writ_tit_nm%2522%252C"
            "%2522col_val%2522%253A%2522%2522%252C%2522in_table_page%2522%253A%257B%2522in_table_paging%2522%253Atrue%252C"
            "%2522in_table_pageSize%2522%253A200%252C%2522in_table_pageNo%2522%253A1%257D%257D")
_KIS_READ = "https://www.koreaholdings.com/kr/bbs/manage/read?act=&seq=%s&cpage=1&lang=kr&bcode=manage&key=&keyword="
# 목록 화면(2026-11-03 받음) — fetch 가 없는 것만 먼저 받음: (회사, URL, 저장 이름, POST 본문, Referer)
LIST_PAGES = (
    [("메리츠금융지주", "https://www.meritzgroup.com/web/ko/ir/ir2.do", "ir2.html", None, "")]
    + [("메리츠금융지주", "https://www.meritzgroup.com/web/ir2_search.do", "ir2_IR003_p%d.json" % i,
        "bd_div_cd=IR003&currentPage=%d" % i, "https://www.meritzgroup.com/web/ko/ir/ir2.do") for i in range(1, 9)]
    + [("iM금융지주", "https://www.imfngroup.com/ir0202.fg", "ir0202.html", None, ""),
       ("iM금융지주", "https://www.imfngroup.com/ybbsR1.fg", "ybbsR1_bbs13_all.json", _IM_POST, "https://www.imfngroup.com/ir0202.fg"),
       ("BNK금융지주", "https://www.bnkfg.com/04/05.jsp", "0405.html", None, ""),
       ("BNK금융지주", "https://www.bnkfg.com/10/sitemap.jsp", "sitemap.html", None, ""),
       ("JB금융지주", "https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do", "pillarDisclosure.html", None, "")]
    + [("JB금융지주", "https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do?year=&pageNum=%d" % i, "pillarDisclosure_p%d.html" % i,
        None, "https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do") for i in range(2, 7)]
    + [("한국투자금융지주", "https://www.koreaholdings.com/kr/bbs/manage/list", "manage_list.html", None, "")]
    + [("한국투자금융지주", "https://www.koreaholdings.com/kr/bbs/manage/list?act=&seq=&cpage=%d&lang=kr&bcode=manage&key=&keyword=" % i,
        "manage_list_p%d.html" % i, None, "https://www.koreaholdings.com/kr/bbs/manage/list") for i in range(2, 5)]
    + [("한국투자금융지주", _KIS_READ % q, "read_%s.html" % q, None, "https://www.koreaholdings.com/kr/bbs/manage/list")
       for q in ("403", "1161", "1313", "1425", "1546", "1615", "1702")]
)


def cmd_page(argv):
    co, url, name = argv[:3]
    a = argv[3:]
    data = a[a.index("--post") + 1] if "--post" in a else None
    ref = a[a.index("--referer") + 1] if "--referer" in a else ""
    return get_page(co, url, name, data, ref)


def get_page(co, url, name, data, ref):
    ok, why = robots_rp(co, url)
    if not ok:
        print("robots 금지 또는 판정 없음 —", why, url)
        return 1
    w = Web()
    try:
        fu, st, hd, b = w.get(url, referer=ref, data=(data.encode() if data else None),
                              headers=({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"} if data else None))
    except Exception as e:                           # noqa: BLE001
        print("ERR", type(e).__name__, getattr(e, "code", ""), str(e)[:200])
        return 1
    p, m = save(os.path.join(co, "_pages"), name, b, dict(출처URL=url, POST=data or "", Referer=ref, 최종URL=fu,
                                                         http_status=st, content_type=hd.get("Content-Type", ""),
                                                         content_disposition=hd.get("Content-Disposition", ""),
                                                         fetched_at=now()))
    print(st, fu, len(b), hd.get("Content-Type", ""), hd.get("Content-Disposition", "")[:120], p)
    return 0


# ── 목록 화면 → FY 별 대상 ────────────────────────────────────────────────
# 이용약관: 각 누리집 바닥글·사이트맵(2026-11-03 받은 목록 화면)에서 「약관」 링크·자동 수집 금지 문구를 찾음.
TERMS = {
    "메리츠금융지주": "이용약관 화면 찾지 못함(https://www.meritzgroup.com/web/ko/ir/ir2.do 바닥글: 공시정보관리지침·개인정보처리방침·고객정보취급방침) — 자동 수집 금지 문구 찾지 못함",
    "iM금융지주": "이용약관 화면 찾지 못함(https://www.imfngroup.com/ir0202.fg 바닥글: 개인정보처리방침 /ug01.fg·고객정보취급방침 /ug02.fg) — 자동 수집 금지 문구 찾지 못함",
    "BNK금융지주": "이용약관 화면 찾지 못함(https://www.bnkfg.com/04/05.jsp 바닥글: 개인정보처리방침·고객정보취급방침, https://www.bnkfg.com/10/sitemap.jsp 에 「약관」 0회) — 자동 수집 금지 문구 찾지 못함",
    "JB금융지주": "이용약관 화면 찾지 못함(https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do 바닥글: 개인정보처리방침·고객정보취급방침 /ko/main/policy/customer.do) — 자동 수집 금지 문구 찾지 못함",
    "한국투자금융지주": "이용약관 화면 찾지 못함(https://www.koreaholdings.com/kr/bbs/manage/list 바닥글: 고객정보취급방침 /kr/util/private·개인정보처리방침 /kr/util/private2) — 자동 수집 금지 문구 찾지 못함",
}
BOARD = {
    "메리츠금융지주": "https://www.meritzgroup.com/web/ko/ir/ir2.do",
    "iM금융지주": "https://www.imfngroup.com/ir0202.fg",
    "BNK금융지주": "https://www.bnkfg.com/04/05.jsp",
    "JB금융지주": "https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do",
    "한국투자금융지주": "https://www.koreaholdings.com/kr/bbs/manage/list",
}


def _cells(row):
    return [html.unescape(re.sub(r"<[^>]+>|\s+", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]


def targets():
    """{(회사, fy): dict(title, url, method, post, referer, posted, file_name, list_ref, note)} — 12월말 기준 연간분만."""
    T = {}
    # 메리츠: POST /web/ir2_search.do bd_div_cd=IR003 (경영공시) currentPage=1..8 — 「제n기 경영공시」(분기·상반기 뺌)
    for p in range(1, 9):
        d = json.load(open(P("메리츠금융지주", "ir2_IR003_p%d.json" % p), encoding="utf-8"))
        for r in d["result"]:
            t = r["title_ko"].strip()
            m = re.fullmatch(r"제(\d+)기 경영공시", t)
            if not m:
                continue
            fs = [f for f in r["fileMap"] if "감사보고서" not in f["file_nm"]]
            fy = 2009 + int(m.group(1))                     # 제16기 = CY2025 (파일 이름의 CY 연도로 확인)
            if fy not in FYS:
                continue
            cy = re.search(r"CY ?(\d{4})", fs[0]["file_nm"])
            assert cy and int(cy.group(1)) == fy, (t, fs[0]["file_nm"])
            T[("메리츠금융지주", fy)] = dict(
                title=t, url="https://www.meritzgroup.com/commfiles" + fs[0]["file_url"], method="GET", post=None,
                referer=BOARD["메리츠금융지주"], posted="20%s-%s-%s" % tuple(r["reg_ymd"].split(".")),
                file_name=fs[0]["file_nm"],
                list_ref="목록 POST https://www.meritzgroup.com/web/ir2_search.do bd_div_cd=IR003 currentPage=%d" % p,
                note="게시물 첨부 %d개 중 경영공시 파일 「%s」(감사보고서 첨부는 받지 않음)" % (len(r["fileMap"]), fs[0]["file_nm"]))
    # iM: POST /ybbsR1.fg BBS_NO 13 한 번에 59건 — 「제n기 (DGB|아이엠)금융지주현황 공시」(상반기·분기 뺌), CRI_YR = 기준연도
    d = json.load(open(P("iM금융지주", "ybbsR1_bbs13_all.json"), encoding="utf-8"))
    for r in d["OUT_DATA"]:
        t = html.unescape(r["PUTUP_WRIT_TIT_NM"]).strip()
        if not re.fullmatch(r"제\d+기 (DGB|아이엠)금융지주현황 공시", t):
            continue
        fy = int(r["CRI_YR"])
        if fy not in FYS:
            continue
        T[("iM금융지주", fy)] = dict(
            title=t, url="https://www.imfngroup.com/ybbsR3.fg?putup_writ_seq=%s&file_seq=%s" % (r["PUTUP_WRIT_SEQ"], r["FILE_SEQ"]),
            method="GET", post=None, referer=BOARD["iM금융지주"],
            posted="%s-%s-%s" % (r["RGDT"][:4], r["RGDT"][4:6], r["RGDT"][6:]), file_name=r["ATC_FILE_NM"],
            list_ref="목록 POST https://www.imfngroup.com/ybbsR1.fg (IN_DATA_JSON bbs_no=13)",
            note="게시물 기준연도(CRI_YR) %s · 첨부 「%s」" % (r["CRI_YR"], r["ATC_FILE_NM"]))
    # BNK: /04/05.jsp 한 화면(연도 머리 아래 목록, 게시일 표시 없음) — 「YYYY년 BNK금융지주 현황」
    s = rd(P("BNK금융지주", "0405.html"))
    for blk in re.finditer(r'<div class="zemu_info">\s*<h2>(\d+)</h2>(.*?)</ul>', s, re.S):
        for li in re.findall(r"<li>(.*?)</li>", blk.group(2), re.S):
            a = re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', li, re.S)
            t = html.unescape(re.sub(r"<[^>]+>", "", a[0][1])).strip()
            m = re.fullmatch(r"(\d{4})년 BNK금융지주 현황", t)
            if not m or int(m.group(1)) not in FYS:
                continue
            fy = int(m.group(1))
            alt = re.findall(r'alt="([^"]*)"', li)
            fn = alt[0].replace(" 다운로드 받기", "") if alt else ""
            T[("BNK금융지주", fy)] = dict(
                title=t, url=html.unescape(a[0][0]), method="GET", post=None, referer=BOARD["BNK금융지주"],
                posted="", file_name=fn, list_ref="목록 https://www.bnkfg.com/04/05.jsp (연도 머리 %s)" % blk.group(1),
                note="목록에 게시일 표시 없음 · 첨부 「%s」" % fn)
    # JB: /ko/ir/disclosure/pillarDisclosure.do?pageNum=1..6 — 「[YYYY] YYYY년 JB금융지주 현황」(반기 뺌)
    for p in range(1, 7):
        s = rd(P("JB금융지주", "pillarDisclosure.html" if p == 1 else "pillarDisclosure_p%d.html" % p))
        for m in re.finditer(r'<td class="__title">(.*?)</tr>', s, re.S):
            row = m.group(1)
            t = html.unescape(re.sub(r"<[^>]+>|\s+", " ", row.split("</td>")[0])).strip()
            mm = re.match(r"\[(\d{4})\] (\d{4})년 JB금융지주 현황", t)
            if not mm or "반기" in t or int(mm.group(1)) not in FYS:
                continue
            fy = int(mm.group(1))
            fs = re.findall(r'href="(/ko/file/download\.do\?id=[^"]+)"[^>]*?download="([^"]*)"', row, re.S)
            main_f = [f for f in fs if "표지" not in f[1]]
            dt = re.findall(r'class="__date"[^>]*>\s*<small>(.*?)</small>', row, re.S)
            T[("JB금융지주", fy)] = dict(
                title=t, url="https://www.jbfg.com" + html.unescape(main_f[0][0]), method="GET", post=None,
                referer=BOARD["JB금융지주"], posted=dt[0].strip(), file_name=html.unescape(main_f[0][1]),
                list_ref="목록 https://www.jbfg.com/ko/ir/disclosure/pillarDisclosure.do?year=&pageNum=%d" % p,
                note="게시물 첨부 %d개 중 「%s」%s" % (len(fs), html.unescape(main_f[0][1]),
                                              ("(「%s」 는 받지 않음)" % "·".join(html.unescape(f[1]) for f in fs if f not in main_f))
                                              if len(fs) > len(main_f) else ""))
    # 한국투자: /kr/bbs/manage/list?cpage=1..3 — 「제n기 경영공시(자료) (YYYY.12.31)」 → read?seq=N → POST /common/fildDownload
    for fn in ("manage_list.html", "manage_list_p2.html", "manage_list_p3.html"):
        s = rd(P("한국투자금융지주", fn))
        for m in re.finditer(r"<tr>(.*?)</tr>", s, re.S):
            row = m.group(1)
            sq = re.findall(r"goRead\('(\d+)'", row)
            if not sq:
                continue
            c = _cells(row)
            t = c[1].replace("​", "").strip()
            mm = re.search(r"\((\d{4})\.12\.31\)", t)
            if "분기" in t or "상반기" in t or not mm or int(mm.group(1)) not in FYS:
                continue
            fy = int(mm.group(1))
            rp = P("한국투자금융지주", "read_%s.html" % sq[0])
            dl = re.findall(r"downloadFile\('([^']*)','([^']*)'\)", rd(rp))
            main_f = [x for x in dl if "감사보고서" not in x[0]]
            read_url = "https://www.koreaholdings.com/kr/bbs/manage/read?act=&seq=%s&cpage=1&lang=kr&bcode=manage&key=&keyword=" % sq[0]
            T[("한국투자금융지주", fy)] = dict(
                title=t, url="https://www.koreaholdings.com/common/fildDownload", method="POST",
                post=dict(real_filename=main_f[0][1], filename=main_f[0][0]), referer=read_url, posted=c[3],
                file_name=main_f[0][0], list_ref="목록 https://www.koreaholdings.com/kr/bbs/manage/list (cpage) → " + read_url,
                note="게시물 첨부 %d개 중 경영공시 파일 「%s」(POST real_filename=%s; 감사보고서 첨부는 받지 않음)"
                     % (len(dl), main_f[0][0], main_f[0][1]))
    return T


def url_label(t):
    if t["method"] == "POST":
        return "%s (POST real_filename=%s)" % (t["url"], t["post"]["real_filename"])
    return t["url"]


def dest_of(co, fy):
    return os.path.join(RAW, co, "%s_경영공시_FY%d.pdf" % (co, fy))


def cmd_fetch():
    for co, url, name, data, ref in LIST_PAGES:            # 목록 화면이 없으면 먼저(있으면 그대로 — 같은 날 받은 화면으로 고름)
        if not os.path.exists(P(co, name)):
            get_page(co, url, name, data, ref)
    T = targets()
    rob = json.load(open(os.path.join(RAW, "robots_판정.json"), encoding="utf-8"))
    w = Web()
    for co in COS:
        for fy in FYS:
            t = T.get((co, fy))
            if not t:
                print(co, fy, "누리집 목록에 없음")
                continue
            dest = dest_of(co, fy)
            if os.path.exists(dest) and os.path.exists(dest + ".meta.json"):
                continue
            if os.path.exists(dest + ".fail.json"):
                # Web.get 은 한 번 부를 때 3번(첫 시도 + 재시도 2회)까지 시도 — 「같은 파일 재시도 2회까지」라 다시 부르지 않음
                print(co, fy, "이미 3회 시도해 실패 — 다시 받지 않음")
                continue
            ok, why = robots_rp(co, t["url"])
            if not ok:
                json.dump(dict(url=url_label(t), status="robots 금지", why=why, checked_at=now()),
                          open(dest + ".fail.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(co, fy, "robots 금지")
                continue
            try:
                if t["method"] == "POST":
                    w.get(t["referer"])                     # 게시글 화면 먼저(쿠키·Referer)
                    fu, st, hd, b = w.get(t["url"], referer=t["referer"], data=t["post"])
                else:
                    fu, st, hd, b = w.get(t["url"], referer=t["referer"])
            except Exception as e:                           # noqa: BLE001
                json.dump(dict(url=url_label(t), status="실패", why="%s %s" % (type(e).__name__, getattr(e, "code", "") or e),
                               checked_at=now()), open(dest + ".fail.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(co, fy, "FAIL", type(e).__name__, str(e)[:100])
                continue
            if not b.startswith(b"%PDF"):
                json.dump(dict(url=url_label(t), status="실패", why="PDF 시그니처 아님(앞 %r, http %s, %s)" % (b[:16], st, hd.get("Content-Type", "")),
                               checked_at=now()), open(dest + ".fail.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(co, fy, "FAIL not pdf", b[:16])
                continue
            with open(dest + ".part", "wb") as f:
                f.write(b)
            os.replace(dest + ".part", dest)
            meta = dict(url=url_label(t), 최종url=fu, 제목=t["title"], 원래파일명=t["file_name"], 게시일=t["posted"],
                        목록=t["list_ref"], http=st, content_type=hd.get("Content-Type", ""),
                        content_disposition=hd.get("Content-Disposition", ""), 크기=len(b),
                        sha256=hashlib.sha256(b).hexdigest(), fetched_at=now(), 저장경로=dest,
                        robots=rob[co]["status"])
            json.dump(meta, open(dest + ".meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            if os.path.exists(dest + ".fail.json"):
                os.remove(dest + ".fail.json")
            print(co, fy, len(b), meta["fetched_at"])
    write_list(T)


ROBOTS_TXT = {
    "메리츠금융지주": "https://www.meritzgroup.com/robots.txt HTTP 200 「User-agent: * / Allow:/」 → 허용",
    "iM금융지주": "https://www.imfngroup.com/robots.txt HTTP 200 「User-agent: * / Allow:/」 → 허용",
    "BNK금융지주": "https://www.bnkfg.com/robots.txt HTTP 404 → RFC 9309 §2.3.1.3 Unavailable, 제한 없음",
    "JB금융지주": ("https://www.jbfg.com/robots.txt HTTP 200 이지만 본문이 robots 규칙이 아닌 HTML(meta refresh → "
                  "http://www.jbbank.co.kr/9999.html) → 규칙 0개로 파싱, 제한 없음(판단)"),
    "한국투자금융지주": "https://www.koreaholdings.com/robots.txt HTTP 404 → RFC 9309 §2.3.1.3 Unavailable, 제한 없음",
}


def md_of(co, fy):
    return os.path.join(TXT, "경영공시__%s__FY%d.md" % (co, fy))


def md_pages(path):
    """md 의 쪽 수와 글자 없는 쪽."""
    if not os.path.exists(path):
        return "", ""
    s = rd(path)
    n = len(re.findall(r"^## p\.\d+", s, re.M))
    empty = re.findall(r"^## p\.(\d+) \(글자 없음\)", s, re.M)
    return str(n), ",".join(empty)


def write_list(T=None):
    T = T or targets()
    rob = json.load(open(os.path.join(RAW, "robots_판정.json"), encoding="utf-8"))
    rows = []
    for co in COS:
        for fy in FYS:
            t = T.get((co, fy))
            dest = dest_of(co, fy)
            row = dict(corp_label=co, fy=fy, robots_verdict="%s (확인 %s)" % (ROBOTS_TXT[co], rob[co]["checked_at"]),
                       terms_note=TERMS[co])
            if not t:
                row.update(status="누리집에 없음", note="경영공시 게시판 %s 목록 전체에 FY%d 12월말 기준분 없음" % (BOARD[co], fy))
                rows.append(row)
                continue
            row.update(period_원문=t["title"], url=url_label(t), posted_at=t["posted"] or "목록에 게시일 표시 없음")
            late = (" · 게시일(게시판 등록일 값 그대로)이 FY 다음 해보다 늦음"
                    if t["posted"] and int(t["posted"][:4]) > fy + 1 else "")
            if os.path.exists(dest + ".meta.json"):
                m = json.load(open(dest + ".meta.json", encoding="utf-8"))
                n, empty = md_pages(md_of(co, fy))
                tf = json.load(open(TEXTFAIL, encoding="utf-8")) if os.path.exists(TEXTFAIL) else {}
                st = "받음"
                note = t["note"] + " · " + t["list_ref"] + late
                if "%s|%d" % (co, fy) in tf:
                    st = "받음(글 추출 실패)"
                    note += " · 글 추출 실패: " + tf["%s|%d" % (co, fy)]
                elif empty:
                    note += " · 글자 없는 쪽: p." + empty.replace(",", ",p.")
                row.update(fetched_at=m["fetched_at"], bytes=m["크기"], pages=n, sha256=m["sha256"], status=st, note=note)
            elif os.path.exists(dest + ".fail.json"):
                f = json.load(open(dest + ".fail.json", encoding="utf-8"))
                extra = ""
                if "Connection reset" in f["why"]:
                    extra = (" — 첫 시도 + 재시도 2회(요청 간 1.2초 이상) 모두 응답 본문 전에 연결 끊김. 이 환경의 나가는 프록시 기록"
                             "(recentRelayFailures, www.imfngroup.com: ws_closed_mid_exchange 「tunnel closed (code 1006) after 10~16s; "
                             "517 B sent, 39 B received」 — dart_out/raw/mgmt15/iM금융지주/proxy_relay_failures.json)에 같은 시각 끊김이 남음. "
                             "「같은 파일 재시도 2회까지」라 더 받지 않음. 사이트가 거부했다는 응답은 없음(판단: 서버 응답 지연 또는 중계 끊김)")
                row.update(status="실패", note=f["why"] + extra + " (마지막 시도 %s) · " % f["checked_at"] + t["note"] + " · " + t["list_ref"] + late)
            else:
                row.update(status="받지 않음", note="fetch 미실행")
            rows.append(row)
    with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=LIST_COLS)
        wr.writeheader()
        wr.writerows(rows)
    print("목록", LIST, len(rows), "행 · 받음", sum(r["status"].startswith("받음") for r in rows))


def cmd_text():
    """받은 PDF → md. 글자층 점검: 한글 글자 수·서로 다른 한글 수가 너무 적으면(깨진 ToUnicode·그림뿐) 실패 목록에."""
    T = targets()
    os.makedirs(TXT, exist_ok=True)
    fails, stats = {}, {}
    for co in COS:
        for fy in FYS:
            dest = dest_of(co, fy)
            if not os.path.exists(dest + ".meta.json"):
                continue
            m = json.load(open(dest + ".meta.json", encoding="utf-8"))
            t = T[(co, fy)]
            head = "%s FY%d · 「%s」 · 파일 「%s」 · 수집 %s · sha256 %s" % (co, fy, t["title"], t["file_name"], m["fetched_at"], m["sha256"])
            r = subprocess.run([VENV, "-I", PDF2MD, dest, md_of(co, fy), head, m["url"]], capture_output=True, text=True)
            if r.returncode != 0:
                fails["%s|%d" % (co, fy)] = "pymupdf 변환 오류: " + r.stderr.strip()[-200:]
                print(co, fy, "변환 실패")
                continue
            st = json.loads(r.stdout.strip().splitlines()[-1])
            stats["%s|%d" % (co, fy)] = st
            # 판단 기준: 한국어 경영공시는 서로 다른 한글이 수백 자 — 300 자 미만이거나 글자 없는 쪽이 절반 넘으면 글자층 깨짐으로 봄
            if st["hangul_distinct"] < 300 or len(st["empty"]) * 2 > st["pages"]:
                fails["%s|%d" % (co, fy)] = ("글자층 점검 실패(서로 다른 한글 %d자, 한글 %d자, 글자 없는 쪽 %d/%d) — 글을 지어내지 않고 조각에서 뺌"
                                            % (st["hangul_distinct"], st["hangul"], len(st["empty"]), st["pages"]))
            print(co, fy, st["pages"], "쪽 · 한글", st["hangul"], "· 서로 다른", st["hangul_distinct"], "· 빈 쪽", len(st["empty"]),
                  "· FFFD", st["fffd"])
    json.dump(fails, open(TEXTFAIL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(stats, open(TEXTSTAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_list(T)


# ── extract: md → 조각 B·D ─────────────────────────────────────────────────
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")      # 줄바꿈(\n·\r)·탭 말고 보이지 않는 제어문자
B_KW = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
# 오탐(낱말 조각): 「전적」 = 완전적용·전적인·사전적·도전적·금전적 …, 「전출」 = 버전출시
B_FALSE = {"전적": re.compile(r"완전적|전적인|전적으로|사전적|도전적|금전적|안전적|발전적"), "전출": re.compile(r"버전출")}
# 작업 D 검색어(사용자: 업무위탁·위탁·용역·경영자문·전산·공동사용) + 같은 뜻의 꼴(위수탁·수탁·공동이용) — (판단)
D_RE = re.compile(r"업무위탁|위[ㆍ·․・]?수탁|공동사용|공동이용|경영자문|위탁|수탁|용역|전산")
BUL = re.compile(r"^\s*(?:[-–—·∙•※○◦□■▶▷◆◇◎●*ㅇ]|\(?\d{1,2}\)|[①-⑳]|[가-하]\.|\([가-하]\)|주\s?\d*\)|\d+\.(?!\d)|[A-Z]\.)")
END = re.compile(r"(?:[다요음함임됨]\s*\.|[.。])\s*$")
NAME = re.compile(r"^[가-힣]{2,4}$")
TITLE = re.compile(r"^(?:회장|부회장|사장|부사장|전무|상무|상무보|부행장|부행장보|대표이사|사외이사|비상임이사|기타비상무이사|감사|"
                   r"상임감사|본부장|이사|상임이사|전무이사|상무이사|그룹장|부문장|고문|위원)$")


HEAD = re.compile(r"^(?:구\s*분|회\s*사\s*명|성\s*명|등기구분|직위(?:\(직책\))?명?|직\s*책|담당업무|겸직회사명?|겸\s*직\s*현\s*황|"
                  r"겸직\s*직위|상근\s*여부|비\s*고)$")


CELL_CO = re.compile(r"^(?:[가-힣A-Za-z]*(?:금융지주|지주|은행|증권|캐피탈|저축은행|자산운용|투자|시스템|생명|화재|보험|신용정보|파트너스|"
                     r"인베스트먼트|벤처캐피탈|프라이빗에쿼티|리츠|운용|코어오피스|뱅크|페이|유페이|라이프생명보험|이노베이션센터)|"
                     r"채권채무|수익비용|매매거래|자산부채|상표권사용료)$")
CELL_CAT = ("채권채무", "수익비용", "매매거래", "자산부채", "상표권사용료")
CELL_NUM = re.compile(r"^(?:[-–]|\(?[\d,.]+\)?|[\d,.]+\s*백만원)$")
DATE = re.compile(r"^\d{4}\s?\.\s?\d{1,2}\.?(?:\s?\d{1,2}\.?)?$")


def ns(s):
    return re.sub(r"\s", "", CTRL.sub("", s))


def load_pages(co, fy):
    """md → [(쪽 번호, 쪽 글)] — 「## p.N」 아래 pymupdf 글 그대로(머리 줄과 쪽 사이 빈 줄 둘만 뗌)."""
    s = rd(md_of(co, fy))
    out = []
    for m in re.finditer(r"^## p\.(\d+)( \(글자 없음\))?\n\n(.*?)(?=^## p\.\d+|\Z)", s, re.S | re.M):
        body = m.group(3)
        if body.endswith("\n\n"):
            body = body[:-2]
        out.append((int(m.group(1)), body))
    return out


def hits(lines, rx):
    """쪽 줄들에서 rx 를 공백 무시하고 찾음 → [(낱말, 시작 줄, 끝 줄, ns 시작, ns 끝, ns 전체)]."""
    nsl = [ns(l) for l in lines]
    flat, idx = "", []
    for i, l in enumerate(nsl):
        flat += l
        idx += [i] * len(l)
    out = []
    for m in rx.finditer(flat):
        out.append((m.group(0), idx[m.start()], idx[m.end() - 1], m.start(), m.end(), flat))
    return out


# 작업 D — 지주와 계열사 사이인지: 같은 문장·표 행에 지주 쪽 말(「지주」)과 계열사 쪽 말이 함께 있을 때만(판단 규칙).
# 「금융지주회사등」(법령 낱말: 금융지주회사와 그 자회사 등)은 두 쪽을 함께 가리키는 말로 봄.
AFF = {
    "메리츠금융지주": r"메리츠(?!금융지주|금융그룹)[가-힣A-Za-z]+",
    "iM금융지주": r"대구은행|하이투자증권|하이자산운용|(?:DGB|iM)(?!금융지주|금융그룹)[가-힣A-Za-z]+",
    "BNK금융지주": r"부산은행|경남은행|BNK(?!금융지주|금융그룹)[가-힣A-Za-z]+",
    "JB금융지주": r"전북은행|광주은행|프놈펜상업은행|JB(?!금융지주|금융그룹)[가-힣A-Za-z]+",
    "한국투자금융지주": r"한국투자(?!금융지주)[가-힣A-Za-z]+|카카오뱅크",
}
D_EXCL = re.compile(r"위탁매매|위탁자|위탁관리|위탁증거|위탁중개|투자위탁|위탁운용|선물위탁|추심위탁|위탁거래|신탁위탁|"
                    r"근무용역|재화나용역|용역을제공|용역의제공|용역제공조건|용역이제공|용역기사|용역청원|용역/파견|용역,파견|"
                    r"경영자문위|경영자문부문|수탁고|수탁회사|수탁은행|수탁자산|수탁액")


def d_relevant(co, t):
    """(관련 여부, 사유)."""
    n = ns(t)
    m = D_EXCL.search(n)
    if m:
        return False, "제외 낱말(" + m.group(0) + ")"
    hold = "지주" in n
    aff = bool(re.search(r"자회사|손자회사|계열|그룹사|금융지주회사등|" + AFF[co], n))
    if hold and aff:
        return True, ""
    return False, "지주·계열사 함께 없음(지주 %s, 계열사 %s)" % ("O" if hold else "X", "O" if aff else "X")


def span(lines, L1, L2):
    """키워드가 든 문장·표 행의 줄 범위(이어진 줄 a~b).
    · 문장: 키워드 줄이 30자 이상이거나 줄을 걸치면 — 앞뒤로 문장 끝(…다.)·글머리표·날짜 칸·짧은 줄(10자 미만)까지(각 6줄 한도).
    · 표 머리행 칸(회사명·성명·…·겸직회사명): 이어진 머리행 칸 줄 전체.
    · 표 칸(성명·직위·담당업무): 앞 두 줄이 성명·직위 칸이면 같은 표 행으로 붙임.
    · 거래 표 칸(계정 이름): 앞 회사·구분 칸(3칸 한도)이 있으면 뒤 금액 칸(2칸), 계정 칸이 행 머리(12자 이하)면 뒤 회사 칸(3칸)·금액 칸(2칸).
    · 연혁 표 칸: 앞 칸이 날짜면 같은 행."""
    cl = [CTRL.sub("", l) for l in lines]           # 판정은 제어문자 뗀 줄로

    def ln(i):
        return len(cl[i].strip())

    def stop(i):
        return not cl[i].strip() or ln(i) < 10 or DATE.match(cl[i].strip())
    prose = L1 != L2 or ln(L1) >= 30 or (ln(L1) >= 15 and not END.search(cl[L1]) and L1 + 1 < len(cl) and ln(L1 + 1) >= 30)
    a, b = L1, L2
    if prose:
        while a > 0 and L1 - a < 6 and not BUL.match(cl[a]) and not stop(a - 1) and not END.search(cl[a - 1]):
            a -= 1
        while (b < len(cl) - 1 and b - L2 < 6 and not END.search(cl[b]) and not BUL.match(cl[b + 1])
               and (not stop(b + 1) or (cl[b + 1].strip() and END.search(cl[b + 1]) and not DATE.match(cl[b + 1].strip())))):
            b += 1
    elif HEAD.match(cl[a].strip()):
        while a > 0 and HEAD.match(cl[a - 1].strip()):
            a -= 1
        while b < len(cl) - 1 and HEAD.match(cl[b + 1].strip()):
            b += 1
    elif a >= 2 and NAME.match(cl[a - 2].strip()) and TITLE.match(cl[a - 1].strip()):
        a -= 2
    else:
        while a > 0 and L1 - a < 3 and CELL_CO.match(cl[a - 1].strip()):
            a -= 1
        if a < L1:
            while b < len(cl) - 1 and b - L2 < 2 and CELL_NUM.match(cl[b + 1].strip()):
                b += 1
        elif ln(L1) <= 12 and b < len(cl) - 1 and CELL_CO.match(cl[b + 1].strip()):
            while b < len(cl) - 1 and b - L2 < 3 and CELL_CO.match(cl[b + 1].strip()):
                b += 1
            c = b
            while b < len(cl) - 1 and b - c < 2 and CELL_NUM.match(cl[b + 1].strip()):
                b += 1
        if a == L1 and a > 0 and DATE.match(cl[a - 1].strip()):
            a -= 1
    return a, b


def text_of(lines, a, b):
    """줄 a~b 를 PDF 줄바꿈 그대로 이어 옮김(줄 앞뒤 공백만 뗌). 보이지 않는 제어문자는 지우고 그 사실을 돌려줌."""
    had_ctrl = bool(CTRL.search("\n".join(lines[a:b + 1])))
    t = "\n".join(CTRL.sub("", l).strip() for l in lines[a:b + 1] if CTRL.sub("", l).strip())
    return t, had_ctrl


# 글자층 순서가 흩어진 쪽(JB FY2019 PDF: 글자는 맞으나 괄호·기호가 따로 줄에 나옴)의 산식 — 산식 줄 묶음 전체를 한 행으로(판단)
SPAN_FIX = {("JB금융지주", 2019, 121, 79): (75, 87, "(판단) 글자층 순서가 흩어진 쪽(괄호·기호가 따로 줄)이라 산식 줄 묶음 전체를 한 행으로 옮김"),
            ("BNK금융지주", 2022, 218, 139): (139, 139, "(판단) 다음 줄은 다른 주석(사외이사 취업승인)이라 이 줄만 옮김")}
TOC = re.compile(r"[·…]{3,}|…|\.{6,}")
# 계열사 이름이 같은 칸에 없는 연혁 표 칸 — 지주 이름 + 검색어가 든 칸만, 표 주인 회사는 같은 쪽 이름 칸에서(판단)
D_CONTEXT = {"iM금융지주": (re.compile(r"(?:DGB|iM)금융지주(?:고객정보전송시스템수탁운영|전산시스템유지보수|홈페이지수탁운영)"),
                           re.compile(r"^(?:DGB|iM)데이터시스템$"))}

# ── 검증(verify15_mgmt_g2, 2026-11-03 KST)에서 찾은 D 빠짐 — 위 자동 규칙으로 못 잡은 곳을 줄 범위로 정해 더함(판단) ──
# 검증이 md 마다 「위탁」「수탁」「용역」「자문」「전산」「공동」을 직접 찾아, 조각 행이 덮지 않고 같은 문장·표 행에 지주 쪽 말이 있는 곳을 원문으로 봄.
# anchor = 첫 줄(제어문자·공백 뗀 줄) 꼴, nxt = 바로 다음 줄 꼴(있으면). rows = [(첫 줄에서 시작 오프셋, 끝 오프셋, 칸 자리, note)]
# 칸 자리: cp·am = 그 행 안 칸 순번, ct = (시작, 끝) 칸 순번(PDF 줄로 나뉜 한 칸을 공백 하나로 이음). 문장 행은 ct 에 검색어 낱말.
_MERGED = ("(판단) 표 병합 칸: 이 행의 거래내용 「미수수익」·채권자(매도자) 「JB금융지주」 칸은 이 묶음 첫 행(같은 쪽 「미수수익⏎JB금융지주⏎전북은행」)과 "
           "함께 쓰는 병합 칸이라 이 행 글에는 없음")
_JB_MISU = [(0, 5, dict(cp=2, am=3, ct=(4, 5)), ""),
            (6, 9, dict(cp=0, am=1, ct=(2, 3)), _MERGED),
            (10, 13, dict(cp=0, am=1, ct=(2, 3)), _MERGED)]
_JB_NOTE = ("; 표 한 행(칸 줄 그대로) — counterparty·contract_type·amount 는 그 행의 칸 글 그대로(contract_type 은 비고 칸, PDF 두 줄을 공백 하나로 이음, "
            "amount 는 거래금액 칸)")
_ADD_NOTE = "(판단) 검증 단계에서 더함(자동 규칙 「같은 문장·표 행에 지주·계열사」가 놓친 곳 — %s)"
_BNK_ROW = [(0, 1, dict(ct="공동"), "(판단) 같은 문장에 지주사(지주회사)·자회사와 검색어 「공동」(검증 단계 검색어)이 있음 — 업무위탁·용역·공동사용 같은 계약 "
                                    "이름은 없는 글이라 애매해서 넣고 표시")]
_IM_ROW = [(0, 1, dict(ct="전산", ctx=r"^현재당사의유동화익스포져는자회사인"),
            "(판단) 같은 쪽 「나. 관리방법」 문단 첫 줄 %s 에 따라 이 문장은 자회사가 지주회사에 보고하는 글로 봄 — 업무위탁·용역·공동사용 같은 계약 "
            "이름은 없는 글이라 애매해서 넣고 표시")]
D_ADD = [
    dict(co="JB금융지주", fy=2022, page=135, anchor=r"^미수수익$", nxt=r"^JB금융지주$", rows=_JB_MISU, why="비고 칸 줄만 잡고 지주 칸을 묶지 못함"),
    dict(co="JB금융지주", fy=2023, page=137, anchor=r"^미수수익$", nxt=r"^JB금융지주$", rows=_JB_MISU, why="비고 칸 줄만 잡고 지주 칸을 묶지 못함"),
    dict(co="BNK금융지주", fy=2021, page=125, anchor=r"^신용평가시스템의설계및운영은지주", rows=_BNK_ROW, why="검색어 「공동」이 자동 규칙 검색어에 없음"),
    dict(co="BNK금융지주", fy=2022, page=127, anchor=r"^신용평가시스템의설계및운영은지주", rows=_BNK_ROW, why="검색어 「공동」이 자동 규칙 검색어에 없음"),
    dict(co="BNK금융지주", fy=2024, page=69, anchor=r"^신용평가시스템의설계및운영은지주", rows=_BNK_ROW, why="검색어 「공동」이 자동 규칙 검색어에 없음"),
    dict(co="BNK금융지주", fy=2025, page=72, anchor=r"^신용평가시스템의설계및운영은지주", rows=_BNK_ROW, why="검색어 「공동」이 자동 규칙 검색어에 없음"),
    dict(co="iM금융지주", fy=2019, page=123, anchor=r"^신규유동화익스포져발생시매월지주회사에문서및전산을통하여보고", rows=_IM_ROW,
         why="같은 문장에 계열사 쪽 말이 없음"),
    dict(co="iM금융지주", fy=2020, page=124, anchor=r"^신규유동화익스포져발생시매월지주회사에문서및전산을통하여보고", rows=_IM_ROW,
         why="같은 문장에 계열사 쪽 말이 없음"),
    dict(co="iM금융지주", fy=2023, page=150, anchor=r"^신규유동화익스포져발생시매월지주회사에문서및전산을통하여보고", rows=_IM_ROW,
         why="같은 문장에 계열사 쪽 말이 없음"),
]


def added_units(co, fy):
    """D_ADD 의 (회사, FY) 행 → 단위 dict(page·a·b·text·ctrl·cp·ct·am·note). 첫 줄을 못 찾으면 멈춤(조용히 빠지지 않게)."""
    out = []
    pages = None
    for e in D_ADD:
        if (e["co"], e["fy"]) != (co, fy):
            continue
        pages = pages or dict(load_pages(co, fy))
        lines = pages[e["page"]].split("\n")
        cl = [ns(l) for l in lines]
        at = [i for i in range(len(cl)) if re.search(e["anchor"], cl[i])
              and (not e.get("nxt") or (i + 1 < len(cl) and re.search(e["nxt"], cl[i + 1])))]
        if len(at) != 1:
            raise SystemExit("D_ADD 첫 줄을 하나로 못 찾음: %s FY%d p.%d %s → %s" % (co, fy, e["page"], e["anchor"], at))
        i0 = at[0]
        for s0, e0, cells, extra in e["rows"]:
            a, b = i0 + s0, i0 + e0
            t, c = text_of(lines, a, b)
            cs = [CTRL.sub("", l).strip() for l in lines[a:b + 1] if CTRL.sub("", l).strip()]
            if "cp" in cells:
                cp, am, ct = cs[cells["cp"]], cs[cells["am"]], " ".join(cs[cells["ct"][0]:cells["ct"][1] + 1])
            else:
                cp, am, ct = "", "", cells["ct"]
            note = _ADD_NOTE % e["why"]
            if "ctx" in cells:
                q = [CTRL.sub("", l).strip() for l in lines if re.search(cells["ctx"], ns(l))]
                if len(q) != 1:
                    raise SystemExit("D_ADD 문맥 줄을 하나로 못 찾음: %s FY%d p.%d" % (co, fy, e["page"]))
                extra = extra % ("「" + q[0] + "」")
            out.append(dict(page=e["page"], a=a, b=b, text=t, ctrl=c, cp=cp, ct=ct, am=am, table="cp" in cells,
                            note=note + ("; " + extra if extra else ""), lines=lines))
    return out


def units(co, fy, which):
    """문장·표 행 단위 후보. B: 오탐 뺀 키워드 행(같은 쪽·같은 낱말에서 다른 행 안에 든 것은 하나로). D: 관련 판정 붙임."""
    out, fps = [], {}
    prev_body = ""
    for pn, body in load_pages(co, fy):
        lines = body.split("\n")
        rx = re.compile("|".join(B_KW)) if which == "B" else D_RE
        raw = []
        for kw, L1, L2, s0, e0, flat in hits(lines, rx):
            if which == "B" and kw in B_FALSE and B_FALSE[kw].search(flat[max(0, s0 - 3):e0 + 3]):
                fps[kw] = fps.get(kw, 0) + 1
                continue
            a, b = SPAN_FIX[(co, fy, pn, L1)][:2] if (co, fy, pn, L1) in SPAN_FIX else span(lines, L1, L2)
            raw.append((kw if which == "B" else "D", a, b, kw))
        keep = []
        for k, a, b, kw in sorted(raw, key=lambda x: (x[0], x[1], -x[2])):
            if any(k == k2 and a2 <= a and b <= b2 for k2, a2, b2, _ in keep):
                if which == "D":
                    for i, x in enumerate(keep):
                        if x[0] == k and x[1] <= a and b <= x[2] and kw not in x[3].split("·"):
                            keep[i] = (x[0], x[1], x[2], x[3] + "·" + kw)
                continue
            keep.append((k, a, b, kw))
        fixes = {(v[0], v[1]): v[2] for k, v in SPAN_FIX.items() if k[:3] == (co, fy, pn)}
        for k, a, b, kws in keep:
            t, c = text_of(lines, a, b)
            u = dict(page=pn, kw=kws, a=a, b=b, text=t, ctrl=c, lines=lines, fix=fixes.get((a, b), ""))
            if which == "D":
                u["rel"], u["why"] = d_relevant(co, t)
                if TOC.search(t):
                    u["rel"], u["why"] = False, "목차 줄"
                cells = [CTRL.sub("", l).strip() for l in lines[a:b + 1] if CTRL.sub("", l).strip()]
                if not u["rel"] and not u["why"].startswith("제외") and len(cells) >= 3:
                    # 거래 표 한 행: 지주 칸(「…금융지주」·「지주」)과 다른 회사 칸이 함께 있으면(약칭 「시스템」 등도 칸 글로)
                    hold = [x for x in cells if re.fullmatch(r"[가-힣A-Za-z]*지주", x)]
                    oth = [x for x in cells if CELL_CO.match(x) and x not in hold and x not in CELL_CAT]
                    if hold and oth:
                        u["rel"], u["why"] = True, "거래 표 행"
                ctx = D_CONTEXT.get(co)
                if not u["rel"] and ctx and ctx[0].search(ns(t)):
                    # 표 회사 이름 칸: 같은 쪽, 없으면 앞 쪽(표가 쪽을 넘어 이어짐)
                    u["rel"], u["why"], u["ctx_label"], u["ctx_page"] = True, "연혁 표 칸", "", None
                    for qn, qb in ((pn, body), (pn - 1, prev_body)):
                        lab = [CTRL.sub("", l).strip() for l in qb.split("\n") if ctx[1].match(CTRL.sub("", l).strip())]
                        if lab:
                            u["ctx_label"], u["ctx_page"] = lab[0], qn
                            break
            out.append(u)
        prev_body = body
    return out, fps


DOC_NOTE = "경영공시 PDF 쪽 글(%s, pymupdf page.get_text() 그대로 — 「## p.N」= PDF 쪽, PDF 줄바꿈 그대로)"


def doc_meta(T, co, fy):
    m = json.load(open(dest_of(co, fy) + ".meta.json", encoding="utf-8"))
    t = T[(co, fy)]
    name = "%s 경영공시 「%s」 (파일 「%s」, %s)" % (co, t["title"], t["file_name"],
                                            ("%s 게시" % t["posted"]) if t["posted"] else "게시일 표시 없음")
    return dict(url=url_label(t), name=name, at=m["fetched_at"], title=t["title"], posted=t["posted"])


def units_note(co, t):
    m = re.findall(r"\(단위\s*:\s*([^)]+)\)", t)
    return m


def cell_parts(co, u):
    """거래 표 행에서 counterparty(지주 아닌 회사 칸)·contract_type(검색어 칸)·amount(금액 칸) — 칸 글 그대로."""
    cl = [CTRL.sub("", l).strip() for l in u["lines"][u["a"]:u["b"] + 1]]
    cl = [x for x in cl if x]
    kwcell = [x for x in cl if D_RE.search(ns(x))]
    cos = [x for x in cl if CELL_CO.match(x) and not re.fullmatch(r"[가-힣A-Za-z]*지주", x) and x not in CELL_CAT]
    nums = [x for x in cl if CELL_NUM.match(x) and x not in ("-", "–")]
    return ("·".join(cos), kwcell[0] if kwcell else "", nums[0] if nums else "")


def build(T=None):
    """B·D 조각 행과 원문 md 쪽 목록을 만들어 돌려줌(파일 쓰기 없음 — 검증 스크립트가 다시 불러 같은지 봄)."""
    T = T or targets()
    tf = json.load(open(TEXTFAIL, encoding="utf-8")) if os.path.exists(TEXTFAIL) else {}
    B, D, cited = [], [], {"B": {}, "D": {}}
    for co in COS:
        for fy in FYS:
            if not os.path.exists(dest_of(co, fy) + ".meta.json") or "%s|%d" % (co, fy) in tf or not os.path.exists(md_of(co, fy)):
                continue
            dm = doc_meta(T, co, fy)
            npages, empty = md_pages(md_of(co, fy))
            mdname = os.path.basename(md_of(co, fy))
            base_note = DOC_NOTE % mdname
            scope = "p.1~p.%s 전체(찾은 범위, PDF 쪽 — 해당 글 없음)" % npages
            emp = (", 글자 없는 쪽 p.%s" % empty.replace(",", ",p.")) if empty else ""
            # ── B ──
            ub, fps = units(co, fy, "B")
            for u in ub:
                note = base_note + "; 직원 수는 같은 FY 사업보고서 행"
                if u["ctrl"]:
                    note += "; 제어문자 지움"
                others = sorted({x["kw"] for x in ub if x["page"] == u["page"] and x["a"] == u["a"] and x["b"] == u["b"]} - {u["kw"]})
                if others:
                    note += "; 같은 글에 다른 검색어(%s)도 있어 그 낱말 행을 따로 둠" % "·".join(others)
                if u["fix"]:
                    note += "; " + u["fix"]
                B.append(dict(corp_label=co, fy=str(fy), employees_total="", regular="", contract="", keyword=u["kw"],
                              source_text=u["text"], doc_kind="경영공시", rcept_no_or_url=dm["url"], page="p.%d" % u["page"],
                              note=note, doc_name=dm["name"], collected_at=dm["at"]))
                cited["B"].setdefault((co, fy), set()).add(u["page"])
            if not ub:
                fp = "; ".join("「%s」 %d곳은 다른 낱말 조각(%s)이라 뺌" % (k, v, B_FALSE[k].pattern.replace("|", "·")) for k, v in sorted(fps.items()))
                B.append(dict(corp_label=co, fy=str(fy), employees_total="", regular="", contract="", keyword="없음",
                              source_text="문서에 없음", doc_kind="경영공시", rcept_no_or_url=dm["url"], page=scope,
                              note=base_note + "; 직원 수는 같은 FY 사업보고서 행; 찾은 범위: 경영공시 FY%d PDF 글 전 쪽(%s쪽%s, 공백·줄바꿈 무시), "
                                   "검색어 겸직·파견·출향·전출·전적·겸무 — 없음%s" % (fy, npages, emp, ("(" + fp + ")") if fp else ""),
                              doc_name=dm["name"], collected_at=dm["at"]))
            # ── D ──
            ud, _ = units(co, fy, "D")
            rel = [u for u in ud if u["rel"]]
            adds = [x for x in added_units(co, fy)
                    if not any(u["page"] == x["page"] and u["a"] <= x["b"] and x["a"] <= u["b"] for u in rel)]  # 자동 규칙이 이미 잡았으면 더하지 않음
            drows = []
            for x in adds:
                note = base_note
                if x["ctrl"]:
                    note += "; 제어문자 지움"
                if x["table"]:
                    note += _JB_NOTE
                    un = sorted(set(units_note(co, CTRL.sub("", "\n".join(x["lines"])))))     # 단위 표기 사이 제어문자(U+0001)는 떼고 찾음
                    if un:
                        note += "; 같은 쪽 단위 표기: " + "·".join("(단위: %s)" % y.strip() for y in un)
                else:
                    note += "; (판단) 문장 행의 contract_type 은 원문에서 맞은 검색어 낱말"
                note += "; " + x["note"]
                drows.append((x["page"], x["a"], dict(corp_label=co, fy=str(fy), counterparty=x["cp"], contract_type=x["ct"], amount=x["am"],
                                                     source_text=x["text"], doc_kind="경영공시", rcept_no_or_url=dm["url"],
                                                     page="p.%d" % x["page"], note=note, doc_name=dm["name"], collected_at=dm["at"])))
                cited["D"].setdefault((co, fy), set()).add(x["page"])
            for u in rel:
                note = base_note
                if u["ctrl"]:
                    note += "; 제어문자 지움"
                if u["fix"]:
                    note += "; " + u["fix"]
                cp, ct, am = "", "", ""
                if u["why"] == "연혁 표 칸":
                    cp = u.get("ctx_label", "")
                    ct = u["kw"]
                    note += "; (판단) 계열사 연혁 표 칸 — 지주 이름과 검색어가 든 칸만 옮김(표 회사 이름은 같은 칸에 없음)"
                    if cp:
                        note += ("; counterparty 는 %s 그 표 회사 이름 칸 글" % ("같은 쪽" if u["ctx_page"] == u["page"] else "앞 쪽 p.%d(표가 쪽을 넘어 이어짐)의" % u["ctx_page"]))
                elif any(CELL_CO.match(CTRL.sub("", l).strip()) for l in u["lines"][u["a"]:u["b"] + 1]) and u["b"] > u["a"]:
                    cp, ct, am = cell_parts(co, u)
                    un = sorted(set(units_note(co, "\n".join(u["lines"]))))
                    note += "; 표 한 행(칸 줄 그대로) — counterparty·contract_type·amount 는 그 행의 칸 글 그대로"
                    if un:
                        note += "; 같은 쪽 단위 표기: " + "·".join("(단위: %s)" % x for x in un)
                else:
                    ct = u["kw"]
                    note += "; (판단) 문장 행의 contract_type 은 원문에서 맞은 검색어 낱말"
                    if "금융지주회사등" in ns(u["text"]) and not re.search(AFF[co] + r"|자회사|계열", ns(u["text"])):
                        note += "; (판단) 「금융지주회사 등」(법령 낱말)을 지주와 자회사 등을 함께 이르는 말로 보아 넣음"
                drows.append((u["page"], u["a"], dict(corp_label=co, fy=str(fy), counterparty=cp, contract_type=ct, amount=am, source_text=u["text"],
                                                     doc_kind="경영공시", rcept_no_or_url=dm["url"], page="p.%d" % u["page"], note=note,
                                                     doc_name=dm["name"], collected_at=dm["at"])))
                cited["D"].setdefault((co, fy), set()).add(u["page"])
            D += [x[2] for x in sorted(drows, key=lambda x: (x[0], x[1]))]      # 쪽·줄 순서(자동 규칙 행끼리의 차례는 그대로)
            if not rel and not adds:
                ex = {}
                for u in ud:
                    k = "목차 줄" if u["why"] == "목차 줄" else ("제외 낱말" if u["why"].startswith("제외") else "지주·계열사 함께 없음")
                    ex[k] = ex.get(k, 0) + 1
                sec = [(pn, len(re.findall("해당사항없음", ns(body)))) for pn, body in load_pages(co, fy)
                       if re.search(r"공동이용현황|공동사용현황", ns(body)) and not TOC.search(body)]
                D.append(dict(corp_label=co, fy=str(fy), counterparty="", contract_type="", amount="", source_text="문서에 없음",
                              doc_kind="경영공시", rcept_no_or_url=dm["url"], page=scope,
                              note=base_note + "; 찾은 범위: 경영공시 FY%d PDF 글 전 쪽(%s쪽%s, 공백·줄바꿈 무시), 검색어 업무위탁·위탁·위수탁·수탁·용역·"
                                   "경영자문·전산·공동사용·공동이용 — 「업무위탁 현황」 표 없음, 검색어가 든 문장·표 행 %d곳 중 지주와 계열사 사이의 것 없음(%s)%s"
                                   % (fy, npages, emp, len(ud), ", ".join("%s %d" % kv for kv in sorted(ex.items())) or "검색어 없음",
                                      ("; 「공동광고·시설물 등 공동이용 현황」 절 " + ", ".join("p.%d(쪽 안 「해당사항 없음」 %d곳)" % x for x in sec)
                                       + " — 지주가 든 행 없음(판단)") if sec else ""),
                              doc_name=dm["name"], collected_at=dm["at"]))
    return B, D, cited


B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"]
D_COLS = ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url", "page",
          "note", "doc_name", "collected_at"]


def orig_md(T, which, co, fy, pages):
    dm = doc_meta(T, co, fy)
    pg = dict(load_pages(co, fy))
    o = ["# %s FY%d 경영공시 — 작업 %s 원문" % (co, fy, which), "",
         "조각 행의 source_text 가 나온 쪽(PDF 쪽 번호)의 글 전체를 그대로 옮김(pymupdf page.get_text(), 줄 앞뒤 공백·PDF 추출 글에 섞인 "
         "보이지 않는 제어문자 U+0001 등만 지움). 같은 쪽은 한 번만.", ""]
    for pn in sorted(pages):
        body = "\n".join(CTRL.sub("", l).rstrip() for l in pg[pn].split("\n"))
        o += ["## %s — p.%d" % (dm["name"], pn), "",
              "- 출처: %s · 문서: %s · 위치: p.%d · 수집: %s" % (dm["url"], dm["name"], pn, dm["at"]), "",
              "```text", body.strip("\n"), "```", ""]
    return "\n".join(o)


def cmd_extract():
    T = targets()
    B, D, cited = build(T)
    os.makedirs(FRAG, exist_ok=True)
    for path, cols, rows in ((os.path.join(FRAG, "B_mgmt_g2.csv"), B_COLS, B), (os.path.join(FRAG, "D_mgmt_g2.csv"), D_COLS, D)):
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    n = 0
    for which in ("B", "D"):
        d = os.path.join(ORIG, which)
        os.makedirs(d, exist_ok=True)
        for (co, fy), pages in sorted(cited[which].items()):
            with open(os.path.join(d, "%s__FY%d__경영공시.md" % (co, fy)), "w", encoding="utf-8") as f:
                f.write(orig_md(T, which, co, fy, pages))
            n += 1
    print("B %d행(없음 %d) · D %d행(문서에 없음 %d) · 원문 md %d개" % (
        len(B), sum(r["keyword"] == "없음" for r in B), len(D), sum(r["source_text"] == "문서에 없음" for r in D), n))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "extract":
        return cmd_extract() or 0
    if cmd == "list":
        return write_list() or 0
    if cmd == "text":
        return cmd_text() or 0
    if cmd == "robots":
        return cmd_robots() or 0
    if cmd == "page":
        return cmd_page(argv[2:])
    if cmd == "fetch":
        return cmd_fetch() or 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
