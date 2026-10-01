# -*- coding: utf-8 -*-
"""9차 작업 — 생명보험협회 「자율규제 규정정보」 전체 목록 + 관련 건 원문 파일.

    python3 scripts/dart/web9_klia.py              # 목록 전수 + 관련 건 원문 받기 + hwp 텍스트화
    python3 scripts/dart/web9_klia.py --no-files   # 목록만(원문 파일은 받지 않는다)
    python3 scripts/dart/web9_klia.py --refetch    # 이미 받은 원문 파일도 다시 받는다

목록 페이지: https://www.klia.or.kr/member/insurRegul/selfRegul/list.do
  (메뉴: 회원사 > 자율규제운영 > 자율규제 규정정보). 목록은 서버가 HTML 로 그린다(XHR 없음).
  1쪽은 GET, 2쪽부터는 화면의 fn_page(n) 와 같은 POST(pageIndex=n, search_text=빈칸).
  원문보기 = commonUtil.js 의 gfn_fileDown(no, seq) → /FileDown.do?fileNo=no&seq=seq

공용 모듈 web9.py 의 Web(UA·1.2초 간격·재시도)·save(원본+.meta.json)를 그대로 쓴다(web9.py 는 고치지 않음).
원본: dart_out/raw/web9/klia/ (git 무시) — robots.txt, 목록 각 쪽 HTML, 받은 원문 파일, hwp 텍스트(.md)
산출: handoff/목록_생보협회_자율규제.csv (UTF-8 BOM)
로봇 차단·로그인·캡차가 보이면 우회하지 않고 멈추고 사유를 CSV note 에 남긴다.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web9 import Web, save, now, RAW, HANDOFF  # noqa: E402

TASK = "klia"
DIR = os.path.join(RAW, TASK)
BASE = "https://www.klia.or.kr"
LIST = BASE + "/member/insurRegul/selfRegul/list.do"
MENU = "회원사 > 자율규제운영 > 자율규제 규정정보"
OUT_CSV = os.path.join(HANDOFF, "목록_생보협회_자율규제.csv")
COLS = ["name", "enacted_or_amended", "category", "url", "related", "file_saved",
        "file_sha256", "collected_at", "note"]
MAX_PAGES = 200            # 안전장치(쪽 번호가 끝없이 늘면 멈춘다)

# 관련 판정: 제목(규제명)에 아래 낱말이 그대로 들어 있으면 해당. 사이트 목록에는 분류 열이 없어 제목만 본다.
# 낱말 → 판정 근거로 note 에 그대로 적는다(추정 없음, 낱말 일치만).
RELATED = [
    ("위험관리", ["위험관리", "리스크"]),
    # '운용' 단독은 「…모범규준 운용에 관한…」(규정 운용)에도 걸려 빼고 '자산운용'만 둔다.
    # 대출·여신은 보험회사 자산운용(대출채권) 낱말로 본다 — note 에 낱말이 남으니 검토 때 걸러 볼 수 있다.
    ("투자", ["투자", "자산운용", "대출", "여신", "PF", "프로젝트 파이낸싱", "유가증권", "파생"]),
    ("위탁", ["위탁", "아웃소싱", "제3자"]),          # '제3자'(제3자 리스크) — 외부 위탁·제휴 상대
    ("재보험", ["재보험"]),
    ("내부통제", ["내부통제", "준법"]),
]

OLE = bytes.fromhex("d0cf11e0a1b11ae1")
BLOCK_WORDS = ["captcha", "CAPTCHA", "자동입력", "보안문자", "로봇이 아닙니다", "접근이 차단",
               "로그인이 필요", "로그인 후 이용", "Access Denied", "Too Many Requests"]


class Stop(Exception):
    """차단·로그인·캡차·구조 이상 — 우회하지 않고 멈춘다."""


def _text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def check_page(fu, st, hd, b, what):
    """차단·로그인·캡차 신호가 있으면 Stop. 원본은 호출한 쪽에서 이미 저장한다."""
    t = b.decode("utf-8", "replace")
    if st != 200:
        raise Stop("%s HTTP %s" % (what, st))
    if "login" in urllib.parse.urlparse(fu).path.lower():
        raise Stop("%s 로그인 페이지로 이동됨(%s)" % (what, fu))
    hit = [w for w in BLOCK_WORDS if w in t]
    if hit and "board_list_table04" not in t:
        raise Stop("%s 차단/로그인/캡차 신호 %s" % (what, hit))
    return t


def parse_list(t, page):
    """표 한 쪽 → 행 목록. 열: 번호(displayNum) · 규제명 · 제·개정월 · 원문보기."""
    m = re.search(r'<table class="board_list_table04">(.*?)</table>', t, re.S)
    if not m:
        raise Stop("%d쪽: 목록 표(board_list_table04)가 없음 — 구조 변경 또는 차단 의심" % page)
    tb = m.group(1)
    head = [_text(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
    cap = _text((re.search(r"<caption>(.*?)</caption>", tb, re.S) or [None, ""])[1] or "")
    body = re.search(r"<tbody>(.*?)</tbody>", tb, re.S).group(1)
    rows = []
    for k, tr in enumerate(re.findall(r"<tr>(.*?)</tr>", body, re.S), 1):
        num = re.search(r'class="hidden-xs sumRow" displayNum="([^"]*)"\s*>(.*?)</td>', tr, re.S)
        name = re.search(r'<p class="hidden-xs">(.*?)</p>', tr, re.S)
        tds = re.findall(r'<td class="hidden-xs">(.*?)</td>', tr, re.S)
        mob = re.search(r"<li>제·개정월\s*:\s*(.*?)</li>", tr, re.S)
        date = _text(tds[0]) if tds else ""
        cell = tds[1] if len(tds) > 1 else ""
        cell = re.sub(r"<!--.*?-->", "", cell, flags=re.S)
        links = []
        for fn, args in re.findall(r'onclick="(\w+)\(([^)]*)\)', cell):
            a = [x.strip().strip("'\"") for x in args.split(",")]
            if fn == "gfn_fileDown" and len(a) == 2:
                links.append(("file", BASE + "/FileDown.do?fileNo=%s&seq=%s" % (a[0], a[1]), a))
            elif fn == "linkOpen" and a:
                links.append(("link", a[0], a))
            else:
                links.append(("other", "%s(%s)" % (fn, args), a))
        for href in re.findall(r'href="([^"#][^"]*)"', cell):
            if not href.startswith("javascript"):
                links.append(("href", urllib.parse.urljoin(LIST, html.unescape(href)), [href]))
        rows.append(dict(page=page, row=k, num=_text(num.group(2)) if num else "",
                         displayNum=num.group(1) if num else "",
                         name=_text(name.group(1)) if name else "", date=date,
                         date_mobile=_text(mob.group(1)) if mob else "", links=links,
                         cell_text=_text(cell)))
    pages = set(int(x) for x in re.findall(r'title="(\d+)페이지"', t))
    pages |= set(int(x) for x in re.findall(r"fn_page\((\d+)\)", t))
    bc = t[t.find('<div class="board_contents">'):t.find("<!-- //paginate -->")]
    total = re.search(r"총\s*(?:<[^>]+>\s*)*([\d,]+)\s*(?:<[^>]+>\s*)*건", bc)
    return rows, pages, head, cap, (total.group(1) if total else "")


def judge(name, category=""):
    got, why = [], []
    for lab, words in RELATED:
        hit = [w for w in words if w in name or (category and w in category)]
        if hit:
            got.append(lab)
            why.append("%s←%s" % (lab, "·".join("'%s'" % w for w in hit)))
    return "|".join(got), "; ".join(why)


def cd_filename(cd):
    """Content-Disposition 의 파일명(원문). urllib 은 헤더를 latin-1 로 풀어 주므로 되돌려 디코딩한다."""
    if not cd:
        return ""
    m = re.search(r"filename\*\s*=\s*([\w-]*)'[^']*'([^;]+)", cd, re.I)
    if m:
        return urllib.parse.unquote(m.group(2).strip().strip('"'), encoding=m.group(1) or "utf-8")
    # 이 사이트는 filename=""<UTF-8 바이트>.hwp"" 처럼 따옴표를 겹쳐 보낸다 → 앞뒤 따옴표를 모두 떼어 낸다
    m = re.search(r'filename\s*=\s*"*(.*?)"*\s*(?:;|$)', cd, re.I)
    if not m:
        return ""
    raw = m.group(1).strip()
    try:
        b = raw.encode("latin-1")
        for enc in ("utf-8", "cp949"):
            try:
                raw = b.decode(enc)
                break
            except UnicodeDecodeError:
                continue
    except UnicodeEncodeError:
        pass
    if re.search(r"%[0-9A-Fa-f]{2}", raw):
        raw = urllib.parse.unquote_plus(raw, encoding="utf-8")   # 자바 URLEncoder: 공백 → '+'
    return raw


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s).strip().strip(".")
    return s[:150] or "noname"


def cached(url):
    """같은 출처URL 로 이미 받은 원문(.meta.json)이 있으면 (경로, meta)."""
    for mp in glob.glob(os.path.join(DIR, "원문_*.meta.json")):
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:                            # noqa: BLE001
            continue
        if m.get("출처URL") == url and os.path.exists(mp[:-len(".meta.json")]):
            return mp[:-len(".meta.json")], m
    return None


def to_md(path):
    """hwp(OLE) → scripts/dart/hwp2md.py 로 텍스트화(글자 변경 없음). (md 경로, 메모)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    dst = os.path.join(os.path.dirname(path), stem + ".md")
    r = subprocess.run([sys.executable, os.path.join(HERE, "hwp2md.py"), path, dst],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst):
        return "", "hwp2md 실패: %s" % (r.stderr.strip().splitlines() or [r.stdout.strip()])[-1]
    return dst, "hwp→md %s" % dst


def fetch_file(w, url, rec, refetch):
    """원문 파일 1건. (경로, meta, 메모). HTML 이 오면(로그인·오류 페이지) 저장만 하고 실패로 둔다."""
    if not refetch:
        c = cached(url)
        if c:
            return c[0], c[1], "이전 실행에서 받은 원본 재사용(%s)" % c[1].get("fetched_at", "")
    fu, st, hd, body = w.get(url, referer=LIST)
    ct = hd.get("Content-Type", "")
    cd = hd.get("Content-Disposition", "")
    fname = cd_filename(cd)
    meta = dict(출처URL=url, 목록페이지=LIST, 메뉴=MENU, 규제명=rec["name"], 최종URL=fu, http_status=st,
                content_type=ct, content_disposition=cd, 원파일명=fname, fetched_at=now())
    if "text/html" in ct.lower() or body[:200].lstrip().lower().startswith((b"<!doctype", b"<html", b"<script")):
        t = body.decode("utf-8", "replace")
        p, _ = save(TASK, "실패응답_%s.html" % safe_name(url.split("?")[1]), body, meta)
        hit = [x for x in BLOCK_WORDS if x in t] + (["login"] if "login" in fu.lower() else [])
        alert = re.search(r"alert\(['\"](.*?)['\"]\)", t)
        why = "파일 대신 HTML 응답(%s)%s%s" % (p, " 신호 %s" % hit if hit else "",
                                          " alert=%s" % alert.group(1) if alert else "")
        if hit:
            raise Stop(why)
        return "", None, why
    a = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    pre = "원문_%s-%s_" % (a.get("fileNo", ["?"])[0], a.get("seq", ["?"])[0])
    if not fname:
        ext = ".hwp" if body.startswith(OLE) else ".pdf" if body.startswith(b"%PDF") else \
              ".zip" if body.startswith(b"PK") else ".bin"
        fname_s = "이름없음" + ext
        meta["원파일명"] = ""
        meta["비고"] = "Content-Disposition 에 파일명 없음 — 확장자는 파일 시그니처로만 붙임"
    else:
        fname_s = safe_name(fname)
    p, meta = save(TASK, pre + fname_s, body, meta)
    return p, meta, ""


def write_csv(rows):
    os.makedirs(HANDOFF, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLS)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r.get(k, "") for k in COLS})
    print("CSV %s — %d행" % (OUT_CSV, len(rows)))


def main(argv):
    no_files = "--no-files" in argv
    refetch = "--refetch" in argv
    w = Web()
    os.makedirs(DIR, exist_ok=True)
    stop, pages_meta, allrows = "", {}, []
    head = cap = total = ""
    # robots.txt — 기록용(차단 규칙이 있으면 멈춘다)
    try:
        fu, st, hd, b = w.get(BASE + "/robots.txt")
        save(TASK, "robots.txt", b, dict(출처URL=BASE + "/robots.txt", 최종URL=fu, http_status=st,
                                         fetched_at=now()))
        rt = b.decode("utf-8", "replace")
        ua_star = re.split(r"(?im)^user-agent\s*:", rt)
        for blk in ua_star[1:]:
            agent, _, rules = blk.partition("\n")
            if agent.strip() == "*" and re.search(r"(?im)^disallow\s*:\s*/(member|FileDown|\s*$)", rules):
                raise Stop("robots.txt 가 User-agent:* 에 대해 해당 경로를 막음")
    except Stop as e:
        stop = str(e)
    except Exception as e:                           # noqa: BLE001
        print("robots.txt 못 받음:", e)
    # 목록 전 쪽
    page, last_seen, seen_sig = 1, 1, set()
    while not stop and page <= MAX_PAGES:
        try:
            if page == 1:
                fu, st, hd, b = w.get(LIST)
                how = "GET"
            else:
                fu, st, hd, b = w.get(LIST, referer=LIST, data={"pageIndex": str(page), "search_text": ""})
                how = "POST pageIndex=%d&search_text=" % page
        except Exception as e:                       # noqa: BLE001
            stop = "%d쪽 접속 실패: %r" % (page, e)
            break
        p, m = save(TASK, "목록_selfRegul_p%02d.html" % page, b,
                    dict(출처URL=LIST, 요청=how, 메뉴=MENU, 최종URL=fu, http_status=st, fetched_at=now()))
        try:
            t = check_page(fu, st, hd, b, "%d쪽" % page)
            rows, pages, head, cap, tot = parse_list(t, page)
        except Stop as e:
            stop = str(e)
            break
        total = total or tot
        sig = tuple((r["displayNum"], r["name"]) for r in rows)
        if sig in seen_sig:
            stop = "%d쪽이 앞 쪽과 같은 내용 — 쪽 넘김이 먹지 않음(전수 미확인)" % page
            break
        seen_sig.add(sig)
        for r in rows:
            r["collected_at"] = m["fetched_at"]
            r["raw"] = p
        pages_meta[page] = dict(rows=len(rows), path=p, sha256=m["sha256"])
        allrows.extend(rows)
        print("%d쪽 %d행 (쪽 번호 최대 %s)" % (page, len(rows), max(pages) if pages else "-"))
        last_seen = max([last_seen] + list(pages))
        if not rows or page >= last_seen:
            break
        page += 1

    # 건수 대조 — 사이트에 '총 N건' 표시가 있으면 그것과, 없으면 쪽수·번호와 대조
    nums = [r["displayNum"] for r in allrows if r["displayNum"]]
    ints = sorted(set(int(x) for x in nums if x.isdigit()))
    gaps = [i for i in range(1, (ints[-1] if ints else 0) + 1) if i not in set(ints)]
    if total:
        cnt = "사이트 표시 총 %s건 vs 수집 %d행" % (total, len(allrows))
    else:
        cnt = ("사이트에 총건수 표시 없음 — 쪽 %d/%d(paginate 최대) 모두 받음, 수집 %d행, "
               "목록 번호 %s~%s 고유 %d개%s" % (len(pages_meta), last_seen, len(allrows),
                                          ints[0] if ints else "-", ints[-1] if ints else "-", len(ints),
                                          ", 빠진 번호 %s" % gaps if gaps else "·빠진 번호 없음"))
    if stop:
        cnt += " — 중단: " + stop
    print(cnt)
    print("표 머리:", head, "| caption:", cap)

    out = []
    for r in allrows:
        rel, why = judge(r["name"])
        files = [l for l in r["links"] if l[0] == "file"]
        others = [l for l in r["links"] if l[0] != "file"]
        url = files[0][1] if files else (others[0][1] if others else "")
        note = ["%d쪽 %d행·목록 번호 %s(같은 번호는 사이트가 한 칸으로 묶어 보임)" % (r["page"], r["row"], r["num"]),
                "분류: 사이트 목록에 분류 열 없음(열: %s) — 빈칸" % "·".join(head)]
        if r["date_mobile"] and r["date_mobile"] != r["date"]:
            note.append("제·개정월 PC칸 %r ≠ 모바일칸 %r" % (r["date"], r["date_mobile"]))
        if not r["date"]:
            note.append("제·개정월 칸 비어 있음")
        if not r["links"]:
            note.append("원문보기 칸에 링크 없음(칸 글자: %r) — url 빈칸" % r["cell_text"])
        if len(r["links"]) > 1:
            note.append("원문보기 링크 %d개: %s" % (len(r["links"]), " , ".join(l[1] for l in r["links"])))
        if others and not files:
            note.append("원문보기가 파일이 아닌 %s" % others[0][0])
        note.append("관련 판정: %s" % (why if why else "해당 낱말 없음"))
        o = dict(name=r["name"], enacted_or_amended=r["date"], category="", url=url, related=rel,
                 file_saved="", file_sha256="", collected_at=r["collected_at"])
        if rel and not no_files and not stop:
            if not files:
                note.append("관련 건이지만 내려받을 파일 링크 없음")
            for kind, furl, _ in files[:1]:
                try:
                    p, meta, memo = fetch_file(w, furl, r, refetch)
                except Stop as e:
                    stop = "원문 받기 중 %s" % e
                    note.append("원문 미수집: " + stop)
                    break
                except Exception as e:               # noqa: BLE001
                    note.append("원문 받기 실패: %r" % e)
                    continue
                if not p:
                    note.append("원문 미수집: " + memo)
                    continue
                o["file_saved"], o["file_sha256"] = p, meta["sha256"]
                note.append("원문 %s(원파일명 %r, %s바이트, HTTP %s, 받은 시각 %s)%s" % (
                    os.path.basename(p), meta.get("원파일명", ""), meta.get("바이트", ""),
                    meta.get("http_status", ""), meta.get("fetched_at", ""), "; " + memo if memo else ""))
                b = open(p, "rb").read(8)
                if b.startswith(OLE) and p.lower().endswith(".hwp"):
                    md, memo2 = to_md(p)
                    note.append(memo2)
                elif p.lower().endswith(".hwpx") or (b.startswith(b"PK") and ".hwp" in p.lower()):
                    note.append("hwpx(zip) — hwp2md(olefile) 대상 아님, 텍스트화 안 함")
        elif rel and no_files:
            note.append("원문 미수집(--no-files 실행)")
        elif rel and stop:
            note.append("원문 미수집: 앞서 중단(%s)" % stop)
        note.append("전수확인: " + cnt)
        o["note"] = " / ".join(note)
        out.append(o)

    if not allrows:
        out.append(dict(name="", enacted_or_amended="", category="", url=LIST, related="", file_saved="",
                        file_sha256="", collected_at=now(),
                        note="목록을 받지 못함 — %s (목록 페이지 %s, 메뉴 %s)" % (stop or "행 0개", LIST, MENU)))
    write_csv(out)
    nrel = sum(1 for o in out if o["related"])
    nfile = sum(1 for o in out if o["file_saved"])
    nmd = sum(1 for o in out if "hwp→md" in o["note"])
    print("전체 %d행 · 관련 %d건 · 원문 저장 %d건 · hwp→md %d건%s" % (
        len(allrows), nrel, nfile, nmd, " · 중단: " + stop if stop else ""))
    return 0 if not stop else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
