# -*- coding: utf-8 -*-
"""C30 — 외국계 대주주 생명보험사의 「대주주(등)와의 거래」 공시(보험업법 제111조) 원문 → CSV.

    python3 scripts/dart/web9_c30.py              # 목록·원문 받기(받은 원본은 재사용) + CSV
    python3 scripts/dart/web9_c30.py --refetch    # 원문 PDF 도 다시 받는다
    python3 scripts/dart/web9_c30.py --offline    # 받지 않고 dart_out/raw/web9/c30/ 에 있는 것만으로 CSV

대상과 출처(robots.txt 를 먼저 받아 User-agent:* 규칙을 따른다. 막혀 있으면 그 사이트는 멈추고 사유만 적는다):
  · 메트라이프생명 — 공시실 brand.metlife.co.kr > 경영공시 > 수시경영공시 (/pn/ocsnMnnt/retrieveOcsnMnntMain.do)
      목록은 POST(pageIndex=n, year=빈칸=전체). 원문은 화면의 fnc_file(seq, 파일명, 실파일명) 과 같은
      POST /pn/ocsnMnnt/ocsnMnntDownloadFile.do. ※ 이 서버는 Content-Type 에 '; charset=UTF-8' 이 붙으면
      오류 화면(255바이트)을 주므로 이 요청만 headers 로 'application/x-www-form-urlencoded' 를 넘긴다.
  · AIA생명 — www.aia.co.kr > 공시실 > 경영공시 > 수시경영공시 (/ko/disclosure/management-information/irregular.html)
      목록 한 화면(HTML 표), 원문은 /content/dam/… PDF GET.
  · 푸본현대생명 — www.fubonhyundai.com, 생명보험협회 공시실 pub.insure.or.kr: 둘 다 robots.txt 가
      User-agent:* Disallow:/ 이면 받지 않는다(우회 없음) → 회사 행 하나에 사유를 적는다.
  · 생명보험협회 공시실(pub.insure.or.kr)은 세 회사 공통 대안 출처지만 같은 이유로 robots.txt 만 받는다.

고르는 공시(목록 제목에 '대주주'가 들어간 것만):
  · 분기공시(보험업법 제111조 제4항 — 신용공여현황, 채권·주식 취득현황): 공시일 2025-10-01 이후
    = 2025.3Q 이후 기준분 (문서 안 「(…기준」 표기로 다시 확인해 fy 에 원문 그대로)
  · 수시공시(제111조 제3항 등 — 신용공여, 주식 취득, 의결권 행사, 공익법인 무상양도): 공시일 2025-07-01 이후
  · 공익법인 무상양도 공시는 지난 거래까지 쌓아 싣는 누적 표라서 표의 마지막 행(같은 일자 포함)만 옮긴다
    (이전 행은 원본·.pages.txt 에 그대로 있고 note 에 행 수를 적는다).
PDF 는 pypdf 로 읽는다. 표 칸은 PDF 가 칸마다 거는 clip 사각형으로 묶어(같은 clip = 같은 칸) 칸 글자를 그대로
' | ' 로 잇는다. 칸 안 줄바꿈은 붙이고(원문 줄바꿈 위치의 공백은 그대로), 연속 공백만 하나로 줄인다.
금액·날짜는 계산·환산하지 않는다.

공용 모듈 web9.py 의 Web(UA·1.2초 간격·재시도)·save(원본+.meta.json)를 그대로 쓴다(web9.py 는 고치지 않음).
원본: dart_out/raw/web9/c30/ (robots.txt, 목록 HTML, 원문 PDF, PDF 쪽 텍스트 .pages.txt)
산출: handoff/원문_외국계보험사_대주주거래.csv (UTF-8 BOM)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.robotparser
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web9 import Web, save, now, RAW, HANDOFF, UA  # noqa: E402
from web9_klia import cd_filename, safe_name  # noqa: E402

TASK = "c30"
DIR = os.path.join(RAW, TASK)
OUT_CSV = os.path.join(HANDOFF, "원문_외국계보험사_대주주거래.csv")
COLS = ["corp_label", "fy", "counterparty", "deal_type", "amount", "board_approval", "source_text",
        "rcept_no_or_url", "page", "collected_at", "note"]
NONE = "문서에 없음"
FROM_SUSI = date(2025, 7, 1)        # 수시공시: 이 날 이후 공시
FROM_QTR = date(2025, 10, 1)        # 분기공시: 이 날 이후 공시(= 2025.3Q 기준분부터)
FORM = "application/x-www-form-urlencoded"

MET = "https://brand.metlife.co.kr"
MET_LIST = MET + "/pn/ocsnMnnt/retrieveOcsnMnntMain.do"
MET_DOWN = MET + "/pn/ocsnMnnt/ocsnMnntDownloadFile.do"
MET_MENU = "메트라이프생명 공시실(brand.metlife.co.kr) > 경영공시 > 수시경영공시"
AIA = "https://www.aia.co.kr"
AIA_LIST = AIA + "/ko/disclosure/management-information/irregular.html"
AIA_MENU = "AIA생명 홈페이지 > 공시실 > 경영공시 > 수시경영공시"
FUBON = "https://www.fubonhyundai.com"
PUB = "https://pub.insure.or.kr"
PUB_MENU = "생명보험협회 공시실(pub.insure.or.kr) > 경영공시(정기·수시·지배구조)"


class Stop(Exception):
    """robots 차단·로그인·캡차 — 우회하지 않고 멈춘다."""


# ── 받기 ────────────────────────────────────────────────────────────────────
def robots(w, base, paths):
    """robots.txt 를 받아 저장하고 paths 가 User-agent:*(우리 UA)로 허용되는지. (허용?, 메모)."""
    url = base + "/robots.txt"
    host = urllib.parse.urlparse(base).netloc
    try:
        fu, st, hd, b = w.get(url)
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        save(TASK, "robots_%s.txt" % host, body, dict(출처URL=url, http_status=e.code, fetched_at=now(),
                                                      비고="robots.txt 없음 → 제한 없음으로 봄"))
        return True, "%s HTTP %s(robots.txt 없음)" % (url, e.code)
    except Exception as e:                                       # noqa: BLE001
        return None, "%s 받기 실패 %r" % (url, e)
    save(TASK, "robots_%s.txt" % host, b, dict(출처URL=url, 최종URL=fu, http_status=st, fetched_at=now()))
    rp = urllib.robotparser.RobotFileParser()
    txt = b.decode("utf-8", "replace")
    rp.parse(txt.splitlines())
    bad = [p for p in paths if not rp.can_fetch(UA, base + p)]
    rule = " ".join(l.strip() for l in txt.splitlines() if l.strip())
    if bad:
        return False, "%s 가 %s 를 막음(원문: %s)" % (url, ", ".join(bad), rule)
    return True, "%s 허용(원문: %s)" % (url, rule[:200])


def ymd(s):
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", s)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def wanted(title, d):
    if "대주주" not in title or not d:
        return False
    return d >= (FROM_QTR if "분기공시" in title else FROM_SUSI)


def cached(src_key):
    for mp in glob.glob(os.path.join(DIR, "*.meta.json")):
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
        if m.get("원문키") == src_key and os.path.exists(mp[:-len(".meta.json")]):
            return mp[:-len(".meta.json")], m
    return None


def check_html(t, what):
    for wd in ("captcha", "CAPTCHA", "자동입력", "보안문자", "로그인이 필요", "로그인 후 이용", "Access Denied"):
        if wd in t:
            raise Stop("%s: 차단/로그인/캡차 신호 %r" % (what, wd))


def metlife_list(w):
    """수시경영공시 전체(year=빈칸) 쪽을 넘기며 FROM_SUSI 이전 글만 나오는 쪽에서 멈춘다."""
    items = []
    w.get(MET_LIST)                                              # 세션 쿠키
    for pg in range(1, 60):
        fu, st, hd, b = w.get(MET_LIST, referer=MET_LIST, headers={"Content-Type": FORM},
                              data={"year": "", "pageIndex": str(pg), "seq": "", "atcgFilePathNm": "",
                                    "atcgFileNm": "", "realAtcgFileNm": ""})
        save(TASK, "metlife_수시경영공시_p%02d.html" % pg, b,
             dict(출처URL=MET_LIST, 요청="POST year=(전체)&pageIndex=%d" % pg, 메뉴=MET_MENU, 최종URL=fu,
                  http_status=st, fetched_at=now()))
        t = b.decode("utf-8", "replace")
        check_html(t, "메트라이프 목록 %d쪽" % pg)
        got = re.findall(r'<span class="date">(.*?)</span>\s*(.*?)\s*</span>.*?fnc_file\(\'(\d+)\'\s*,\s*'
                         r'\'(.*?)\'\s*,\s*\'(.*?)\'\)', t, re.S)
        if not got:
            break
        for dt, title, seq, fn, real in got:
            title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title)).strip()
            items.append(dict(date_txt=dt.strip(), d=ymd(dt), title=title, seq=seq, fname=fn, real=real, page=pg))
        if all(ymd(x[0]) and ymd(x[0]) < FROM_SUSI for x in got):
            break
    return items


def metlife_get(w, it, refetch):
    key = "metlife:seq=%s" % it["seq"]
    if not refetch and cached(key):
        return cached(key)
    data = {"year": "", "pageIndex": str(it["page"]), "seq": it["seq"], "atcgFilePathNm": "",
            "atcgFileNm": it["fname"], "realAtcgFileNm": it["real"]}
    fu, st, hd, b = w.get(MET_DOWN, referer=MET_LIST, data=data, headers={"Content-Type": FORM})
    meta = dict(원문키=key, 출처URL=MET_DOWN, 요청="POST " + urllib.parse.urlencode(data), 목록페이지=MET_LIST,
                메뉴=MET_MENU, 목록제목=it["title"], 목록공시일=it["date_txt"], 최종URL=fu, http_status=st,
                content_type=hd.get("Content-Type", ""), 원파일명=cd_filename(hd.get("Content-Disposition", "")),
                fetched_at=now())
    if not b.startswith(b"%PDF"):
        p, m = save(TASK, "metlife_%s_실패응답.html" % it["seq"], b, meta)
        raise RuntimeError("PDF 대신 %d바이트 응답(%s)" % (len(b), p))
    return save(TASK, "metlife_%s_%s" % (it["seq"], safe_name(it["fname"])), b, meta)


def aia_list(w):
    fu, st, hd, b = w.get(AIA_LIST)
    save(TASK, "aia_수시경영공시.html", b, dict(출처URL=AIA_LIST, 메뉴=AIA_MENU, 최종URL=fu, http_status=st,
                                                fetched_at=now()))
    t = b.decode("utf-8", "replace")
    check_html(t, "AIA 목록")
    items = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        tds = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip()
               for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        href = re.findall(r'href="([^"]+\.pdf)"', tr)
        if len(tds) >= 3 and href:
            items.append(dict(no=tds[0], title=tds[1], date_txt=tds[2], d=ymd(tds[2]),
                              url=urllib.parse.urljoin(AIA_LIST, href[0])))
    return items


def aia_get(w, it, refetch):
    key = "aia:" + it["url"]
    if not refetch and cached(key):
        return cached(key)
    fu, st, hd, b = w.get(it["url"], referer=AIA_LIST)
    meta = dict(원문키=key, 출처URL=it["url"], 목록페이지=AIA_LIST, 메뉴=AIA_MENU, 목록번호=it["no"],
                목록제목=it["title"], 목록공시일=it["date_txt"], 최종URL=fu, http_status=st,
                content_type=hd.get("Content-Type", ""), fetched_at=now())
    if not b.startswith(b"%PDF"):
        save(TASK, "aia_%s_실패응답.html" % safe_name(os.path.basename(it["url"])), b, meta)
        raise RuntimeError("PDF 대신 %d바이트 응답" % len(b))
    return save(TASK, "aia_" + safe_name(os.path.basename(it["url"])), b, meta)


# ── PDF → 칸 ────────────────────────────────────────────────────────────────
def _pt(x, y, cm):
    return x * cm[0] + y * cm[2] + cm[4], x * cm[1] + y * cm[3] + cm[5]


def _mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return [a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F]


def clean(s):
    """칸 글자: 칸 안 줄바꿈은 붙이고(줄 끝 공백은 원문대로 남는다) 연속 공백만 하나로. U+3000(전각 빈칸)은 그대로."""
    return re.sub(r"[ \t]+", " ", s.replace("\r", "").replace("\n", "")).strip(" \t")


def page_cells(page):
    """(칸 목록, 칸 밖 글). 칸 = 같은 clip 사각형에 그려진 글자 묶음 {x0,y0,x1,y1,text}."""
    st = {"clip": None, "stack": [], "path": [], "pending": False}
    runs = []

    def before(op, args, cm, tm):
        if op == b"q":
            st["stack"].append(st["clip"])
        elif op == b"Q":
            st["clip"] = st["stack"].pop() if st["stack"] else None
        elif op in (b"m", b"l"):
            st["path"].append(_pt(float(args[0]), float(args[1]), cm))
        elif op == b"re":
            x, y, wd, ht = [float(a) for a in args]
            st["path"] += [_pt(x, y, cm), _pt(x + wd, y + ht, cm)]
        elif op in (b"W", b"W*"):
            st["pending"] = True
        elif op in (b"n", b"S", b"s", b"f", b"f*", b"F", b"B", b"B*", b"b", b"b*"):
            if st["pending"] and st["path"]:
                xs = [p[0] for p in st["path"]]
                ys = [p[1] for p in st["path"]]
                box = (min(xs), min(ys), max(xs), max(ys))
                c = st["clip"]
                if c:
                    box = (max(box[0], c[0]), max(box[1], c[1]), min(box[2], c[2]), min(box[3], c[3]))
                st["clip"] = box
            st["path"], st["pending"] = [], False

    def vt(text, cm, tm, fd, fs):
        if text:
            m = _mul(tm, cm)
            runs.append((text, m[4], m[5], st["clip"]))

    page.extract_text(visitor_operand_before=before, visitor_text=vt)
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)
    cells, order, free = {}, [], []
    for text, x, y, c in runs:
        if not c or (c[2] - c[0]) * (c[3] - c[1]) >= 0.8 * pw * ph:
            free.append(text)
            continue
        k = tuple(round(v, 1) for v in c)
        if k not in cells:
            cells[k] = []
            order.append(k)
        cells[k].append(text)
    out = []
    for k in order:
        t = clean("".join(cells[k]))
        if t.strip(" "):
            out.append(dict(x0=k[0], y0=k[1], x1=k[2], y1=k[3], text=t))
    return out, "".join(free)


def rows_of(cells, tol=1.0):
    """가장 얇은 가로 띠(행)마다 그 띠를 덮는 칸(병합 칸 포함)을 왼쪽부터. [(y1, [칸…])] 위→아래."""
    bands = sorted({(c["y0"], c["y1"]) for c in cells}, key=lambda b: (-b[1], -b[0]))
    mins = [b for b in bands if not any(o != b and o[0] >= b[0] - tol and o[1] <= b[1] + tol
                                        and (o[1] - o[0]) < (b[1] - b[0]) - tol for o in bands)]
    out = []
    for b in mins:
        rc = sorted([c for c in cells if c["y0"] <= b[0] + tol and c["y1"] >= b[1] - tol], key=lambda c: c["x0"])
        sig = tuple(id(c) for c in rc)
        if out and tuple(id(c) for c in out[-1][1]) == sig:
            continue
        out.append((b[1], rc))
    return out


def xover(a, b):
    w = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
    return w > 0.5 * min(a["x1"] - a["x0"], b["x1"] - b["x0"])


def joinrow(rc):
    return " | ".join(c["text"] for c in rc)


def blank(t):
    return not t.replace("　", "").strip()


def read_pdf(path):
    import pypdf
    r = pypdf.PdfReader(path)
    pages = []
    for i, pg in enumerate(r.pages, 1):
        cells, free = page_cells(pg)
        pages.append(dict(no=i, text=pg.extract_text() or "", cells=cells, free=free))
    txt = "".join("=== %d쪽 (pypdf %s extract_text) ===\n%s\n" % (p["no"], pypdf.__version__, p["text"])
                  for p in pages)
    tp = path + ".pages.txt"
    if not os.path.exists(tp) or open(tp, encoding="utf-8").read() != txt:
        save(TASK, os.path.basename(tp), txt.encode("utf-8"),
             dict(원본=path, 만든방법="pypdf %s PdfReader.pages[i].extract_text() 쪽별" % pypdf.__version__,
                  fetched_at=now()))
    return pages


# ── 양식별 행 만들기 ─────────────────────────────────────────────────────────
def doc_title(pages):
    for p in pages:
        for line in (p["free"] + "\n" + p["text"]).split("\n"):
            s = re.sub(r"\s+", " ", line).strip()
            if "대주주" in s and not s.startswith(("주1", "주2", "주3", "주4", "※", "<")):
                return s
    return ""


def form_code(pages):
    m = re.search(r"\(\s*(제\s*7-\d-\d\s*호)\s*\)", pages[0]["text"])
    return m.group(1).replace(" ", "") if m else ""


def basis(pages):
    m = re.search(r"\(\s*(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?\s*기준)", pages[0]["text"])
    return re.sub(r"\s+", " ", m.group(1)) if m else ""


def unit(pages):
    m = re.search(r"단위\s*:\s*([^,)\n]+)", pages[0]["text"])
    return m.group(1).strip() if m else ""


def table_rows(pages, base, kind):
    """분기공시 표(제7-2-1호 신용공여현황 / 제7-2-2호 채권·주식 취득현황) — 대주주 한 행 = CSV 한 행."""
    out, u, fy, title = [], unit(pages), basis(pages) or NONE, doc_title(pages)
    total_row = ""
    for p in pages:
        rows = rows_of(p["cells"])
        head_i = [i for i, (_, rc) in enumerate(rows) if any(c["text"].replace(" ", "") == "대주주명" for c in rc)]
        if not head_i:
            continue
        hdr_cells = {id(c): c for i in head_i for c in rows[i][1]}.values()
        name_h = next(c for c in hdr_cells if c["text"].replace(" ", "") == "대주주명")

        def hdr(c):
            hs = sorted([h for h in hdr_cells if xover(h, c)], key=lambda h: -h["y1"])
            return " ".join(dict.fromkeys(h["text"] for h in hs))

        for _, rc in rows[head_i[-1] + 1:]:
            names = [c for c in rc if xover(c, name_h)]
            flat = [c["text"].replace(" ", "") for c in rc]
            if any(re.search(r"(소계|합계|총계)$", f) for f in flat):
                if any(f == "총계" for f in flat):
                    total_row = joinrow(rc)
                continue
            if not names or names[0]["text"].strip() in ("-", "") or blank(names[0]["text"]):
                continue
            nm = names[0]
            vals = [c for c in rc if c["x0"] >= name_h["x1"] - 1]
            kinds = [c for c in vals if "종류" in hdr(c).replace(" ", "")]
            money = [c for c in vals if re.search(r"신용공여금액|취득현황", hdr(c)) and "사유" not in hdr(c)
                     and not blank(c["text"])]
            if kind == "7-2-2":
                grp = [g for g in ("채권취득현황", "주식취득현황")
                       if any(g in hdr(c) and c["text"].strip() not in ("-",) for c in money)]
                dtype = "%s / %s" % (title, "·".join(grp) if grp else "채권취득현황·주식취득현황")
            else:
                dtype = "%s / %s" % (title, "; ".join("%s: %s" % (hdr(c), c["text"]) for c in kinds) or
                                     "신용공여종류: " + NONE)
            amount = " / ".join("%s: %s" % (hdr(c), c["text"]) for c in money)
            amount = (amount + " (단위: %s)" % u) if amount and u else (amount or NONE)
            out.append(dict(fy=fy, counterparty=nm["text"], deal_type=dtype, amount=amount, board_approval=NONE,
                            source_text=joinrow(rc), page=str(p["no"]),
                            note_extra="표 머리(칸 순서): %s" % " | ".join(hdr(c) or "?" for c in rc)))
    if not out:
        out.append(dict(fy=fy, counterparty=NONE, deal_type=title or NONE, amount=NONE, board_approval=NONE,
                        source_text=" | ".join(x for x in (title, total_row) if x) or NONE, page="1",
                        note_extra="표에 대주주 행 없음%s" % ("(제목 「%s」)" % title if title else "")
                        + ("; 총계 행: %s" % total_row if total_row else "")))
    return out


def kv(pages):
    """수시공시 서식(제7-1-x호): ([(라벨 경로, 값, 쪽)], 원문 칸 순서). 값 = 행의 맨 오른쪽 칸.
    원문 칸 순서는 위→아래·왼→오른쪽, 여러 행에 걸친 병합 칸은 처음 한 번만."""
    out, seen, src = [], set(), []
    for p in pages:
        for _, rc in rows_of(p["cells"]):
            if len(rc) >= 2:
                out.append((" > ".join(c["text"] for c in rc[:-1]), rc[-1]["text"], p["no"]))
            elif rc:
                out.append((rc[0]["text"], "", p["no"]))
            for c in rc:
                k = (p["no"], c["x0"], c["y0"], c["x1"], c["y1"])
                if k not in seen:
                    seen.add(k)
                    src.append(c["text"])
    return out, src


def find(pairs, pat):
    for lab, val, _ in pairs:
        if re.search(pat, lab.replace(" ", "")):
            return lab.split(" > ")[-1], val
    return None, None


def susi_rows(pages, code):
    pairs, cells = kv(pages)
    title = doc_title(pages)
    src = " | ".join(cells) or NONE
    pg = ",".join(sorted({str(n) for _, _, n in pairs})) or "1"
    _, who = find(pairs, r"대주주명")
    bl, bod = find(pairs, r"이사회(결의|의결)")
    kl, kval = (None, None) if code == "제7-1-4호" else find(pairs, r"(주식의종류|채권의종류|신용공여종류)$")
    al, aval = find(pairs, r"(취득금액|신용공여금액|거래금액)")
    dl, dval = find(pairs, r"(취득일|신용공여일|주주총회일|거래일)")
    return [dict(fy="%s %s" % (dl, dval) if dval else NONE, counterparty=who or NONE,
                 deal_type=title + (" / %s: %s" % (kl, kval) if kval else ""),
                 amount="%s: %s" % (al, aval) if aval else NONE,
                 board_approval="%s: %s" % (bl, bod) if bod else NONE,
                 source_text=src, page=pg,
                 note_extra="의결권 행사 서식 — 금액 칸 없음" if code == "제7-1-4호" else "")]


def gift_rows(pages):
    """대주주의 특수관계인인 공익법인 등에 대한 자산의 무상양도 등 공시 — 「2. 자산의 무상양도등 현황」 표 한 행 = 한 행."""
    out, org = [], None
    for p in pages:
        rows = rows_of(p["cells"])
        for i, (_, rc) in enumerate(rows):
            t = [c["text"].replace(" ", "") for c in rc]
            if "명칭" in t and org is None:
                h = rc[t.index("명칭")]
                for _, rc2 in rows[i + 1:]:
                    hit = [c for c in rc2 if xover(c, h) and c is not h]
                    if hit:
                        org = hit[0]["text"]
                        break
            if "일자" in t and "거래유형" in t and "금액" in t:
                hdr = rc
                for _, rc2 in rows[i + 1:]:
                    if not rc2 or not re.match(r"\d{4}\.\d{1,2}\.\d{1,2}", rc2[0]["text"]):
                        continue
                    col = {}
                    for c in rc2:
                        hh = [h["text"] for h in hdr if xover(h, c)]
                        col[hh[0] if hh else "?"] = c["text"]
                    out.append(dict(fy="일자 %s" % col.get("일자", NONE),
                                    counterparty=org or NONE,
                                    deal_type="%s / 거래유형: %s" % (doc_title(pages), col.get("거래유형", NONE)),
                                    amount="금액: %s" % col["금액"] if col.get("금액") else NONE,
                                    board_approval=NONE, source_text=joinrow(rc2), page=str(p["no"]),
                                    note_extra="표 머리: %s; 거래상대방 = 「1. 공익법인등 현황」 명칭 칸"
                                    % joinrow(hdr)))
    # 이 서식은 지난 거래까지 쌓아 싣는 누적 표 — 표의 마지막 행과 같은 일자의 행만 남긴다(나머지는 .pages.txt)
    n = len(out)
    last = out[-1]["fy"] if out else None
    keep = [(k, r) for k, r in enumerate(out, 1) if r["fy"] == last]
    for k, r in keep:
        r["note_extra"] += ("; 누적 표 %d행 중 %d번째 — 표 마지막 행(같은 일자 포함)만 옮김, 이전 일자 %d행은 "
                            "원본 .pages.txt 에 있음(앞선 무상양도 공시에도 실림)" % (n, k, n - len(keep)))
    out = [r for _, r in keep]
    return out or [dict(fy=NONE, counterparty=org or NONE, deal_type=doc_title(pages), amount=NONE,
                        board_approval=NONE, source_text=NONE, page="", note_extra="무상양도 표를 못 찾음")]


def parse_doc(path):
    pages = read_pdf(path)
    code = form_code(pages)
    title = doc_title(pages)
    if code in ("제7-2-1호", "제7-2-2호"):
        rows = table_rows(pages, path, code[1:6])
    elif "무상양도" in title:
        rows = gift_rows(pages)
    else:
        rows = susi_rows(pages, code)
    return rows, code, title, len(pages)


# ── 실행 ───────────────────────────────────────────────────────────────────
def none_row(corp, url, note):
    return dict(corp_label=corp, fy=NONE, counterparty=NONE, deal_type=NONE, amount=NONE, board_approval=NONE,
                source_text=NONE, rcept_no_or_url=url, page="", collected_at=now(), note=note)


def collect(corp, w, items, getter, url_of, menu, offline, refetch, problems):
    out, ndoc = [], 0
    for it in items:
        try:
            if offline:
                c = cached(("metlife:seq=%s" % it["seq"]) if "seq" in it else "aia:" + it["url"])
                if not c:
                    raise RuntimeError("--offline: 받아 둔 원본 없음")
                p, m = c
            else:
                p, m = getter(w, it, refetch)
        except Stop:
            raise
        except Exception as e:                                   # noqa: BLE001
            problems.append("%s %s: %r" % (corp, it["title"], e))
            out.append(none_row(corp, url_of(it), "원문 받기 실패 %r — 목록 「%s」 %s (%s)"
                                % (e, it["title"], it["date_txt"], menu)))
            continue
        try:
            rows, code, title, npg = parse_doc(p)
        except Exception as e:                                   # noqa: BLE001
            problems.append("%s %s 읽기 실패: %r" % (corp, p, e))
            rows, code, title, npg = [dict(fy=NONE, counterparty=NONE, deal_type=NONE, amount=NONE,
                                           board_approval=NONE, source_text=NONE, page="",
                                           note_extra="PDF 읽기 실패 %r" % e)], "", "", 0
        ndoc += 1
        kind = "분기공시" if "분기공시" in it["title"] else "수시공시"
        for r in rows:
            note = ["%s — 목록 「%s」 공시일 %s" % (kind, it["title"], it["date_txt"]),
                    "서식 %s" % (code or "번호 없음"), "PDF %d쪽" % npg,
                    "원본 %s (sha256 %s…)" % (p, m.get("sha256", "")[:12]), "출처 메뉴: " + menu]
            if r.get("note_extra"):
                note.insert(1, r["note_extra"])
            out.append(dict(corp_label=corp, fy=r["fy"], counterparty=r["counterparty"], deal_type=r["deal_type"],
                            amount=r["amount"], board_approval=r["board_approval"], source_text=r["source_text"],
                            rcept_no_or_url=url_of(it), page=r["page"], collected_at=m.get("fetched_at", ""),
                            note=" / ".join(note)))
    return out, ndoc


def main(argv):
    refetch, offline = "--refetch" in argv, "--offline" in argv
    w = Web()
    os.makedirs(DIR, exist_ok=True)
    rows, problems, summary = [], [], []

    # 생명보험협회 공시실 — 공통 대안 출처. robots 만 확인.
    pub_ok, pub_memo = (None, "--offline: 확인 안 함") if offline else \
        robots(w, PUB, ["/mngtDis/mngtDis/list.do", "/mngtDis/frequentDis/list.do", "/mngtDis/corpGov/list.do"])
    pub_note = "생명보험협회 공시실: " + (pub_memo if pub_ok is not False else "수집 안 함 — " + pub_memo)
    print(pub_note)

    # 메트라이프생명
    corp = "메트라이프생명"
    try:
        ok, memo = (True, "--offline") if offline else robots(w, MET, ["/pn/ocsnMnnt/retrieveOcsnMnntMain.do",
                                                                        "/pn/ocsnMnnt/ocsnMnntDownloadFile.do"])
        if ok is False:
            raise Stop(memo)
        items = [] if offline else metlife_list(w)
        if offline:
            for mp in sorted(glob.glob(os.path.join(DIR, "metlife_*.pdf.meta.json"))):
                m = json.load(open(mp, encoding="utf-8"))
                seq = m["원문키"].split("=")[1]
                items.append(dict(seq=seq, title=m["목록제목"], date_txt=m["목록공시일"], d=ymd(m["목록공시일"])))
        sel = [x for x in items if wanted(x["title"], x["d"])]
        print("%s 수시경영공시 목록 %d건 → 대주주 관련·기간 내 %d건" % (corp, len(items), len(sel)))
        out, nd = collect(corp, w, sel, metlife_get,
                          lambda it: "%s (POST seq=%s; 목록 %s)" % (MET_DOWN, it["seq"], MET_LIST),
                          MET_MENU, offline, refetch, problems)
        if not sel:
            out = [none_row(corp, MET_LIST, "목록에 기간 내 '대주주' 제목 공시 없음 (%s) / %s" % (MET_MENU, pub_note))]
        rows += out
        summary.append((corp, nd, len(out), memo))
    except Stop as e:
        rows.append(none_row(corp, MET_LIST, "수집 중단: %s / %s" % (e, pub_note)))
        summary.append((corp, 0, 1, "중단: %s" % e))

    # AIA생명
    corp = "AIA생명"
    try:
        ok, memo = (True, "--offline") if offline else robots(w, AIA, [
            "/ko/disclosure/management-information/irregular.html",
            "/content/dam/kr-wise/ko/docs/disclosure/management-information/irregular/x.pdf"])
        if ok is False:
            raise Stop(memo)
        if offline:
            items = []
            for mp in sorted(glob.glob(os.path.join(DIR, "aia_*.pdf.meta.json"))):
                m = json.load(open(mp, encoding="utf-8"))
                items.append(dict(no=m.get("목록번호", ""), title=m["목록제목"], date_txt=m["목록공시일"],
                                  d=ymd(m["목록공시일"]), url=m["출처URL"]))
        else:
            items = aia_list(w)
        sel = [x for x in items if wanted(x["title"], x["d"])]
        print("%s 수시경영공시 목록 %d건 → 대주주 관련·기간 내 %d건" % (corp, len(items), len(sel)))
        out, nd = collect(corp, w, sel, aia_get, lambda it: it["url"], AIA_MENU, offline, refetch, problems)
        if not sel:
            out = [none_row(corp, AIA_LIST, "목록에 기간 내 '대주주' 제목 공시 없음 (%s) / %s" % (AIA_MENU, pub_note))]
        rows += out
        summary.append((corp, nd, len(out), memo))
    except Stop as e:
        rows.append(none_row(corp, AIA_LIST, "수집 중단: %s / %s" % (e, pub_note)))
        summary.append((corp, 0, 1, "중단: %s" % e))

    # 푸본현대생명 — 회사 홈페이지 robots 확인
    corp = "푸본현대생명"
    ok, memo = (None, "--offline: 확인 안 함") if offline else robots(w, FUBON, ["/"])
    if ok is False or pub_ok is False:
        rows.append(none_row(corp, "%s/robots.txt ; %s/robots.txt" % (FUBON, PUB),
                             "수집 안 함(우회 없음) — 회사 홈페이지: %s / %s / 찾아본 곳: 회사 홈페이지 공시실(경영공시·"
                             "수시공시 「대주주등과의 거래」), %s" % (memo, pub_note, PUB_MENU)))
        summary.append((corp, 0, 1, "robots 차단: " + memo))
    else:
        rows.append(none_row(corp, FUBON, "홈페이지 robots 허용(%s)이지만 이 스크립트에 공시실 수집기가 없음 — "
                                          "수동 확인 필요 / %s" % (memo, pub_note)))
        summary.append((corp, 0, 1, memo))

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLS)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r.get(k, "") for k in COLS})
    print("CSV %s — %d행" % (OUT_CSV, len(rows)))
    for corp, nd, nr, memo in summary:
        print("  %-8s 공시 %d건 · %d행 · %s" % (corp, nd, nr, memo[:160]))
    for p in problems:
        print("  문제:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
