# -*- coding: utf-8 -*-
"""15차 경영공시 g2 — 메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주 FY2019~FY2025
정기 경영공시(12월말 기준분) 수집·쪽 텍스트·작업 B(겸직·파견 등)·작업 D(업무위탁 등) 조각.

    python3 scripts/dart/ops15_mgmt_g2.py robots   # 5개 호스트 robots.txt(web13.Robots, RFC 9309) + 첫 화면(약관 링크 찾기)
    python3 scripts/dart/ops15_mgmt_g2.py page <회사> <url> <이름> [--post k=v&..] [--referer URL]   # 목록 화면 하나(robots 확인 뒤)
    python3 scripts/dart/ops15_mgmt_g2.py fetch    # 저장한 목록 화면에서 FY 별 12월말 기준분 고르고 PDF 받기 → 목록 CSV
    python3 scripts/dart/ops15_mgmt_g2.py text     # 받은 PDF → 「## p.N」 md (venv 파이썬 -I, 경로는 인자)
    python3 scripts/dart/ops15_mgmt_g2.py extract  # md 에서 B·D 조각 + 원문 md (네트워크 없음, 다시 돌리면 같은 결과)

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


def cmd_page(argv):
    co, url, name = argv[:3]
    a = argv[3:]
    data = a[a.index("--post") + 1] if "--post" in a else None
    ref = a[a.index("--referer") + 1] if "--referer" in a else ""
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
            if os.path.exists(dest + ".meta.json"):
                m = json.load(open(dest + ".meta.json", encoding="utf-8"))
                n, empty = md_pages(md_of(co, fy))
                fail = os.path.join(OPS, "_mgmt_g2_textfail.json")
                tf = json.load(open(fail, encoding="utf-8")) if os.path.exists(fail) else {}
                st = "받음"
                note = t["note"] + " · " + t["list_ref"]
                if "%s|%d" % (co, fy) in tf:
                    st = "받음(글 추출 실패)"
                    note += " · 글 추출 실패: " + tf["%s|%d" % (co, fy)]
                elif empty:
                    note += " · 글자 없는 쪽: p." + empty.replace(",", ",p.")
                row.update(fetched_at=m["fetched_at"], bytes=m["크기"], pages=n, sha256=m["sha256"], status=st, note=note)
            elif os.path.exists(dest + ".fail.json"):
                f = json.load(open(dest + ".fail.json", encoding="utf-8"))
                row.update(status=f["status"], note=f["why"] + " (확인 %s) · " % f["checked_at"] + t["list_ref"])
            else:
                row.update(status="받지 않음", note="fetch 미실행")
            rows.append(row)
    with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=LIST_COLS)
        wr.writeheader()
        wr.writerows(rows)
    print("목록", LIST, len(rows), "행 · 받음", sum(r["status"].startswith("받음") for r in rows))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
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
