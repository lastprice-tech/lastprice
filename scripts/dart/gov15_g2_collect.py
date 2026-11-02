# -*- coding: utf-8 -*-
"""15차 g2 — 지배구조 및 보수체계 연차보고서 공시연도 2020~2024(FY2019~2023) 수집.

대상: 메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주(각 회사 공식 누리집 지배구조 공시 게시판).
목록은 gov15_g2_fetch.py 로 받아 둔 게시판 화면(dart_out/raw/governance15/<회사>/_pages/)에서 다시 읽는다.
HTTP 는 web13.Web(UA 고정·1.2초 간격·3회 재시도). robots 는 gov15_g2_robots.py 가 받아 둔 판정을 따른다.
받은 PDF: dart_out/raw/governance15/<회사>/<원래 파일 이름> + .meta.json.
PDF→쪽 텍스트 md 는 venv 파이썬(-I)으로 gov15_g2_pdf2md.py 를 부른다.
`python3 scripts/dart/gov15_g2_collect.py`
"""
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
web13.RAW = os.path.join("dart_out", "raw", "governance15")
from web13 import Web, now  # noqa: E402

RAW = web13.RAW
TXT = os.path.join("dart_out", "text", "ops15")
LIST = os.path.join("dart_out", "ops15", "연차보고서15_목록_g2.csv")
VENV = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python"
YEARS = range(2020, 2025)
COLS = ["회사", "공시연도", "공시유형", "제목", "게시판_url", "파일_url", "공시일", "http", "크기", "sha256", "쪽수",
        "글자없는쪽", "robots_판정", "약관_판정", "실패사유", "fetched_at"]

ROBOTS = {
    "메리츠금융지주": "https://www.meritzgroup.com/robots.txt HTTP 200(2026-11-02T16:06 KST) 「User-agent: * / Allow:/」 → 허용",
    "iM금융지주": "https://www.imfngroup.com/robots.txt HTTP 200(2026-11-02T16:06 KST) 「User-agent: * / Allow:/」 → 허용",
    "BNK금융지주": "https://www.bnkfg.com/robots.txt HTTP 404(2026-11-02T16:06 KST) → RFC 9309 §2.3.1.3 Unavailable, 제한 없음",
    "JB금융지주": ("https://www.jbfg.com/robots.txt HTTP 200(2026-11-02T16:06 KST) 이지만 본문이 robots 규칙이 아닌 HTML"
                  "(meta refresh → http://www.jbbank.co.kr/9999.html) → 규칙 0개로 파싱, 제한 없음(판단)"),
    "한국투자금융지주": "https://www.koreaholdings.com/robots.txt HTTP 404(2026-11-02T16:06 KST) → RFC 9309 §2.3.1.3 Unavailable, 제한 없음",
}
TERMS = {
    "메리츠금융지주": "이용약관 화면 없음(본 화면 바닥글: 공시정보관리지침·개인정보처리방침·고객정보취급방침·신용정보활용체제) — 자동 수집 금지 문구 확인 안 됨 → 수집",
    "iM금융지주": "이용약관 화면 없음(바닥글: 개인정보처리방침·고객정보취급방침) — 자동 수집 금지 문구 확인 안 됨 → 수집",
    "BNK금융지주": "이용약관 화면 없음(바닥글·사이트맵: 고객정보취급방침·개인정보처리방침·신용정보활용체제) — 자동 수집 금지 문구 확인 안 됨 → 수집",
    "JB금융지주": "이용약관 화면 없음(바닥글: 개인정보처리방침·고객정보취급방침) — 자동 수집 금지 문구 확인 안 됨 → 수집",
    "한국투자금융지주": "이용약관 화면 없음(바닥글: /kr/util/private·private2·private3 방침) — 자동 수집 금지 문구 확인 안 됨 → 수집",
}


def P(co, name):
    return os.path.join(RAW, co, "_pages", name)


def rd(path):
    return open(path, encoding="utf-8", errors="replace").read()


def kind_of(title):
    for k, v in (("추가", "추가공시"), ("재공시", "재공시"), ("수정", "수정공시"), ("정정", "정정공시")):
        if k in title:
            return v
    return "본공시"


def targets():
    T = []
    # 메리츠: /web/gr_search.do (POST bd_div_cd=GR002&currentPage=N) JSON 21쪽
    board = "https://www.meritzgroup.com/web/ko/group/group4_7.do"
    for p in range(1, 22):
        d = json.load(open(P("메리츠금융지주", "gr_search_GR002_p%d.json" % p), encoding="utf-8"))
        for r in d["result"]:
            t = r["title_ko"]
            y = 2000 + int(r["reg_ymd"][:2])
            if "연차" in t and y in YEARS:
                for f in r["fileMap"]:
                    if "연차" not in f["file_nm"]:
                        continue
                    T.append(dict(회사="메리츠금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t,
                                  게시판_url=board + " (목록 POST /web/gr_search.do bd_div_cd=GR002 currentPage=%d)" % p,
                                  파일_url="https://www.meritzgroup.com/commfiles" + f["file_url"],
                                  공시일="20%s-%s-%s" % tuple(r["reg_ymd"].split(".")), 파일명=f["file_nm"]))
    # iM: /nbbsR1.fg (BBS_NO 17) JSON 한 번에 92건
    d = json.load(open(P("iM금융지주", "nbbsR1_bbs17_all.json"), encoding="utf-8"))
    for r in d["OUT_DATA"]:
        t = html.unescape(r["PUTUP_WRIT_TIT_NM"])
        y = int(r["RGDT"][:4])
        if "연차" in t and y in YEARS:
            T.append(dict(회사="iM금융지주", 공시연도=y, 공시유형=kind_of(t), 제목=t,
                          게시판_url="https://www.imfngroup.com/ir0204.fg (목록 POST /nbbsR1.fg BBS_NO=17)",
                          파일_url="https://www.imfngroup.com/nbbsR3.fg?putup_writ_seq=%s&file_seq=%s" % (r["PUTUP_WRIT_SEQ"], r["FILE_SEQ"]),
                          공시일="%s-%s-%s" % (r["RGDT"][:4], r["RGDT"][4:6], r["RGDT"][6:]), 파일명=r["ATC_FILE_NM"]))
    # BNK: /01/0607.jsp?dataPageNo=N 10쪽
    seen = set()
    for p in range(1, 11):
        s = rd(P("BNK금융지주", "0607_p%d.html" % p))
        for m in re.finditer(r'<tr>\s*<td>(\d+)</td>\s*<td class="subject"><a href="([^"]+)"[^>]*>(.*?)</a></td>\s*<td>(.*?)</td>\s*<td>([^<]*)</td>', s, re.S):
            no, href, t, fcell, dt = m.groups()
            t = html.unescape(t).strip()
            if no in seen:
                continue
            seen.add(no)
            alt = re.findall(r'alt="([^"]*)"', fcell)
            y = int(dt[:4])
            if "연차" not in t:
                continue
            # 공시연도: 보고서 대상 연도 + 1 (수정 공시는 게시 연도가 아니라 원 보고서의 공시연도로 둠 — 판단)
            fy = re.search(r"(20\d\d)년", t)
            py = int(fy.group(1)) + 1 if fy else y
            if py not in YEARS:
                continue
            T.append(dict(회사="BNK금융지주", 공시연도=py, 공시유형=kind_of(t), 제목=t,
                          게시판_url="https://www.bnkfg.com/01/0607.jsp?dataPageNo=%d&dataWhere=" % p,
                          파일_url=href, 공시일=dt.replace(".", "-"),
                          파일명=(alt[0].replace(" 다운로드 받기", "") if alt else "")))
    # JB: /ko/governance/disclosure.do?postStartDateYMD=Y&searchText=연차
    for y in YEARS:
        s = rd(P("JB금융지주", "disclosure_%d.html" % y))
        for m in re.finditer(r'<tr>\s*<td class="__title">(.*?)</tr>', s, re.S):
            row = m.group(1)
            t = re.findall(r'detail/(\d+)\.do"[^>]*>(.*?)</a>', row)
            f = re.findall(r'href="(/ko/file/download\.do\?id=[^"]+)"[^>]*>(.*?)</a>', row, re.S)
            d = re.findall(r'class="__date"[^>]*>\s*<small>(.*?)</small>', row, re.S)
            for href, fn in f:
                title = html.unescape(t[0][1]).strip()
                T.append(dict(회사="JB금융지주", 공시연도=y, 공시유형=kind_of(title), 제목=title,
                              게시판_url="https://www.jbfg.com/ko/governance/disclosure/detail/%s.do (목록 https://www.jbfg.com/ko/governance/disclosure.do?postStartDateYMD=%d&searchText=연차)" % (t[0][0], y),
                              파일_url="https://www.jbfg.com" + href, 공시일=d[0].strip(),
                              파일명=html.unescape(re.sub(r"<[^>]+>|\s+", " ", fn).strip())))
    # 한국투자: /kr/bbs/disclosure/list?keyword=연차보고서 → read?seq=N → POST /common/fildDownload
    for fn in ("disclosure_q.html", "disclosure_q_p2.html", "disclosure_q_p3.html"):
        s = rd(P("한국투자금융지주", fn))
        for m in re.finditer(r"<tr>(.*?)</tr>", s, re.S):
            row = m.group(1)
            sq = re.findall(r"loadBbsView\('(\d+)'", row)
            if not sq:
                continue
            cells = [html.unescape(re.sub(r"<[^>]+>|\s+", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            title, dt = cells[1], cells[3]
            y = int(dt[:4])
            if y not in YEARS:
                continue
            h = rd(P("한국투자금융지주", "read_%s.html" % sq[0]))
            for fname, real in re.findall(r"downloadFile\('([^']*)','([^']*)'\)", h):
                T.append(dict(회사="한국투자금융지주", 공시연도=y, 공시유형=kind_of(title), 제목=title,
                              게시판_url="https://www.koreaholdings.com/kr/bbs/disclosure/read?seq=%s&lang=kr&bcode=disclosure" % sq[0],
                              파일_url="https://www.koreaholdings.com/common/fildDownload (POST real_filename=%s)" % real,
                              공시일=dt, 파일명=fname, _post=dict(filename=fname, real_filename=real)))
    return T


def allowed(co, url):
    rdir = os.path.join(RAW, co)
    host = urllib.parse.urlparse(url).netloc
    rob = [f for f in os.listdir(rdir) if f.startswith("robots_" + host)]
    if not rob:
        return False
    if not rob[0].endswith(".txt"):
        return True                      # 4xx → 제한 없음
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(rd(os.path.join(rdir, rob[0])).splitlines())
    return rp.can_fetch(web13.UA, url)


def main():
    T = targets()
    w = Web()
    rows = []
    os.makedirs(TXT, exist_ok=True)
    for t in T:
        co = t["회사"]
        row = {k: t.get(k, "") for k in COLS}
        row["robots_판정"], row["약관_판정"] = ROBOTS[co], TERMS[co]
        name = os.path.basename(t["파일명"].replace("\\", "/")) or "file.pdf"
        dest = os.path.join(RAW, co, name)
        url = t["파일_url"].split(" (")[0]
        if not allowed(co, url):
            row["실패사유"] = "robots 금지 — 받지 않음"
            rows.append(row)
            continue
        meta_p = dest + ".meta.json"
        if os.path.exists(dest) and os.path.exists(meta_p):
            meta = json.load(open(meta_p, encoding="utf-8"))
        else:
            post = t.get("_post")
            ref = t["게시판_url"].split(" (")[0]
            try:
                if post:
                    w.get(ref)          # 게시글 먼저(쿠키·Referer)
                    fu, st, hd, b = w.get(url, referer=ref, data=post)
                else:
                    fu, st, hd, b = w.get(url, referer=ref)
            except Exception as e:      # noqa: BLE001
                row["실패사유"] = "내려받기 실패 %s %s" % (type(e).__name__, getattr(e, "code", "") or e)
                print(co, t["공시연도"], t["공시유형"], "FAIL", row["실패사유"][:120])
                rows.append(row)
                continue
            if not b.startswith(b"%PDF"):
                row["실패사유"] = "PDF 시그니처 아님(앞 %r, http %s, %s)" % (b[:20], st, hd.get("Content-Type", ""))
                row["http"] = st
                print(co, t["공시연도"], t["공시유형"], "FAIL", row["실패사유"][:120])
                rows.append(row)
                continue
            with open(dest + ".part", "wb") as f:
                f.write(b)
            os.replace(dest + ".part", dest)
            meta = dict(url=t["파일_url"], 최종url=fu, 게시판_url=t["게시판_url"], 제목=t["제목"], 원래파일명=t["파일명"],
                        공시연도=t["공시연도"], 공시유형=t["공시유형"], 공시일=t["공시일"], http=st,
                        content_type=hd.get("Content-Type", ""), content_disposition=hd.get("Content-Disposition", ""),
                        크기=len(b), sha256=hashlib.sha256(b).hexdigest(), fetched_at=now(), 저장경로=dest)
            json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        row.update(http=meta["http"], 크기=meta["크기"], sha256=meta["sha256"], fetched_at=meta["fetched_at"])
        md = os.path.join(TXT, "연차보고서__%s__%s__%s.md" % (co, t["공시연도"], t["공시유형"]))
        r = subprocess.run([VENV, "-I", os.path.join(HERE, "gov15_g2_pdf2md.py"), dest, md,
                            "%s %s %s · %s · %s" % (co, t["공시연도"], t["공시유형"], t["제목"], t["파일_url"])],
                           capture_output=True, text=True)
        if r.returncode != 0:
            row["실패사유"] = "텍스트 변환 실패: " + r.stderr.strip()[-200:]
        else:
            n, empty = r.stdout.rstrip("\n").split("\t")
            row["쪽수"], row["글자없는쪽"] = n, empty
        if co == "JB금융지주" and t["공시연도"] == 2020:
            row["실패사유"] = ("내려받기·쪽 텍스트 변환은 성공. 다만 이 PDF 는 글꼴 글자 대응(ToUnicode)이 깨져 추출 글이 원문과 다름"
                            "(「겸」 글자 0회, 예: 「현재 t직 업무」, 한글 서로 다른 글자 217자뿐) — 키워드 검색 불가. 겸직 칸 5곳만 쪽 그림을 보고 옮겨 적음")
        rows.append(row)
        print(co, t["공시연도"], t["공시유형"], row["크기"], row["쪽수"], row["실패사유"][:60])
    with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLS)
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    main()
