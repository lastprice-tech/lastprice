# -*- coding: utf-8 -*-
"""13차 9-2-4(ORSA 보도자료)·9-5(금감원 검사결과 공개자료 — 금융지주회사 경영유의·개선사항) 웹 수집.
실행은 저장소 루트에서(스크립트가 chdir 함).

    python3 scripts/dart/web13_fss.py policy        # robots.txt(fss.or.kr·fsc.go.kr)·금감원 저작권 정책 확인
    python3 scripts/dart/web13_fss.py press-search  # 금감원 보도자료 게시판 낱말 검색(제목+내용, 끝 쪽까지) → 검색기록·후보
    python3 scripts/dart/web13_fss.py press-fetch   # PRESS 에 고른 게시글 HTML·첨부(pdf 우선, 없으면 hwp) → 텍스트
    python3 scripts/dart/web13_fss.py impr          # 「금융회사 경영유의사항 등 공시」 2022-01-01~ 전 목록 → 지주 건 PDF → 텍스트
    python3 scripts/dart/web13_fss.py sanc          # 「검사결과제재」 2022-01-01~ 금융회사명 「지주」 목록 → 상세 화면·첨부 PDF
    python3 scripts/dart/web13_fss.py review        # 공개안 PDF → 지적 항목(조치내용 건수 대조) → dart_out/risk13/9-5_항목검토.txt
    python3 scripts/dart/web13_fss.py build         # 산출 md·csv(요청 없음, 받은 원본만) — build-press / build-exam 따로도 됨
    python3 scripts/dart/web13_fss.py verify        # md 인용 블록 ↔ 원본 텍스트(공백 무시) 대조, 인증값 문자열 검사

산출: handoff/13차_산출물/9-2-4_ORSA_보도자료.md, handoff/13차_산출물/9-5_금감원_검사결과.md,
      dart_out/risk13/9-5_검사결과_목록.csv(지적 항목별) 외 작업 기록 csv(dart_out/risk13/9-2-4_*·9-5_*).

원칙(13차 COMMON13.md):
  - 요청은 web13.Web(UA 고정·1.2초 간격·3회 재시도). robots.txt 는 web13.Robots(RFC 9309)로 보고, 막힌 경로·접속 불가
    호스트는 받지 않는다. 401·403·429·로그인·캡차 화면이 나오면 우회하지 않고 멈춘다(사유는 검색기록에).
  - 원본은 save() 로 dart_out/raw/web13/fss/<묶음>/ 에 바이트 그대로 + .meta.json(sha256). 이미 받은 원본은 다시 받지 않는다.
  - PDF 텍스트는 pypdf(쪽 표지 「=== p.N ===」), hwp 는 scripts/dart/hwp2md.py(수정 없이, python -I 로)로 만든다.
    md 에 옮기는 글은 이 텍스트에서 **글자 그대로** 잘라 온다 — QUOTES 의 시작·끝 표지로 잘라 오고, 표지를 못 찾으면 멈춘다.
  - 판단(리스크관리 관련 여부·모범규준 조 번호 추정)은 md 의 「note:」 줄과 CSV 의 판단 칸에만, 「(판단)」 표시.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))                    # 저장소 루트
from web13 import Web, save, Robots, now, write_csv, OUT, WORK, RAW  # noqa: E402

TASK = "fss"
D = os.path.join(RAW, TASK)
FSS = "https://www.fss.or.kr"
FSC = "https://www.fsc.go.kr"
TODAY = "2026-10-07"
SDATE, EDATE = "2022-01-01", "2026-10-08"                           # 9-5 범위(2022년 이후) — 목록 화면 기본 종료일과 같게
LOG_CSV = os.path.join(WORK, "9-2-4_9-5_요청기록.csv")
SEARCH_CSV = os.path.join(WORK, "9-2-4_보도자료_검색기록.csv")
CAND_CSV = os.path.join(WORK, "9-2-4_보도자료_후보.csv")
IMPR_ALL_CSV = os.path.join(WORK, "9-5_경영유의공시_전체목록.csv")
SANC_CSV = os.path.join(WORK, "9-5_검사결과제재_지주목록.csv")
LIST_CSV = os.path.join(WORK, "9-5_검사결과_목록.csv")
OUT_PRESS = os.path.join(OUT, "9-2-4_ORSA_보도자료.md")
OUT_EXAM = os.path.join(OUT, "9-5_금감원_검사결과.md")


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
    """web13.Robots. 접속 실패(「확인 불가」)면 30·60초 쉬고 두 번 더 본다 — 그래도 안 되면 그 호스트는 받지 않는다.
    실측(2026-10-07): www.fsc.go.kr 은 이 환경에서 TLS 접속이 간헐적으로 끊긴다(프록시 기록 ws_closed_mid_exchange)."""
    if base not in ROBOTS:
        for k in range(3):
            r = Robots(web(), base, TASK)
            if r.status != "확인 불가":
                break
            LOG.append(dict(시각=now(), URL=base + "/robots.txt", 결과="확인 불가", 사유=r.note))
            if k < 2:
                time.sleep(30 * (k + 1))
        ROBOTS[base] = r
    return ROBOTS[base]


def fetch(url, referer="", data=None):
    base = "%s://%s" % urllib.parse.urlparse(url)[:2]
    r = robots(base)
    if not r.allowed(url):
        LOG.append(dict(시각=now(), URL=url, 결과="요청 안 함", 사유="robots.txt %s %s" % (r.status, r.note)))
        raise Stop("robots.txt 가 허용하지 않음(%s) — 요청 안 함: %s" % (r.status, url))
    for k in range(3):                                              # 접속 끊김만 30·60초 쉬고 다시(차단 응답은 바로 멈춤)
        try:
            fu, st, hd, b = web().get(url, referer=referer, data=data)
            break
        except urllib.error.HTTPError as e:
            LOG.append(dict(시각=now(), URL=url, 결과="HTTP %s" % e.code, 사유=""))
            if e.code in (401, 403, 429):
                raise Stop("HTTP %s (차단 의심) — %s" % (e.code, url))
            raise
        except Exception as e:                                      # noqa: BLE001
            LOG.append(dict(시각=now(), URL=url, 결과="접속 실패", 사유="%s: %s" % (type(e).__name__, e)))
            if k == 2:
                raise Stop("접속 실패(web13.Web 3회 재시도 × 3번) — %s: %s" % (url, e))
            time.sleep(30 * (k + 1))
    low = b[:30000].decode("utf-8", "replace").lower()
    if "/login" in fu.lower() or "captcha" in low or "자동입력방지" in low:
        LOG.append(dict(시각=now(), URL=url, 결과="멈춤", 사유="로그인/캡차 화면 → %s" % fu))
        raise Stop("로그인/캡차 화면 — %s → %s" % (url, fu))
    LOG.append(dict(시각=now(), URL=url, 결과="HTTP %s" % st, 사유=""))
    return fu, st, hd, b


def cached(sub, name, url, referer="", data=None, extra=None):
    """dart_out/raw/web13/fss/<sub>/<name> 이 있으면 읽고, 없으면 받아서 save. (bytes, meta, path)"""
    p = os.path.join(D, sub, name)
    if os.path.exists(p) and os.path.exists(p + ".meta.json"):
        with open(p, "rb") as f, open(p + ".meta.json", encoding="utf-8") as g:
            return f.read(), json.load(g), p
    fu, st, hd, b = fetch(url, referer, data)
    meta = dict(출처URL=url, 최종URL=fu, http_status=st, content_type=hd.get("Content-Type", ""),
                content_disposition=hd.get("Content-Disposition", ""), fetched_at=now())
    meta.update(extra or {})
    path, meta = save(TASK + "/" + sub, name, b, meta)
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


def slug(s, n=60):
    return re.sub(r"[^\w가-힣]+", "_", s).strip("_")[:n]


def strip_tags(h):
    h = re.sub(r"<script\b.*?</script>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|tr|h\d)>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return "\n".join(x.strip() for x in h.split("\n") if x.strip())


# ── 텍스트화 ─────────────────────────────────────────────────────────────
def pdf_text(path):
    """pypdf extract_text — 쪽마다 「=== p.N ===」 표지. 결과는 원본 옆 .txt(같은 폴더, 신뢰하지 않는 데이터와 같이 둠)."""
    out = path + ".txt"
    if os.path.exists(out):
        return out
    from pypdf import PdfReader
    rd = PdfReader(path)
    parts = []
    for i, pg in enumerate(rd.pages, 1):
        parts.append("=== p.%d ===\n%s" % (i, pg.extract_text() or ""))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out


def pdf_layout(path):
    """pypdf extract_text(extraction_mode="layout") — 글자 위치로 띄어쓰기를 되살린 글. 쪽 표지 「=== p.N ===」.
    줄마다 앞뒤 공백을 떼고 연속 공백은 한 칸으로 줄인다(정렬용 공백). 기본 모드(pdf_text)와 공백을 뺀 글자열이 쪽마다 같은지
    대조해 다르면 그 쪽 표지에 「[대조 다름]」을 붙인다. 결과는 원본 옆 .layout.txt."""
    out = path + ".layout.txt"
    if os.path.exists(out):
        return out
    from pypdf import PdfReader
    rd = PdfReader(path)
    parts = []
    for i, pg in enumerate(rd.pages, 1):
        lay = pg.extract_text(extraction_mode="layout") or ""
        plain = pg.extract_text() or ""
        lines = [re.sub(r"[ \t]{2,}", " ", ln).strip() for ln in lay.split("\n")]
        lines = [ln for ln in lines if ln]
        a, b = re.sub(r"\s+", "", "".join(lines)), re.sub(r"\s+", "", plain)
        tag = ("" if a == b else " [대조: 글자는 같고 순서만 다름(표·칸 배치)]" if sorted(a) == sorted(b)
               else " [대조 다름: 기본 모드와 공백 뺀 글자 구성이 다름]")
        parts.append("=== p.%d ===%s\n%s" % (i, tag, "\n".join(lines)))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out


def _pages(t):
    parts = re.split(r"=== p\.(\d+) ===[^\n]*\n?", t)
    return [(int(parts[k]), parts[k + 1]) for k in range(1, len(parts), 2)]


def _slice_keep_spaces(line, start, end):
    """line 에서 공백을 뺀 글자 기준 [start, end) 구간을 공백 그대로 잘라 온다."""
    out, n = [], 0
    for ch in line:
        if ch.isspace():
            if start < n < end:
                out.append(ch)
            continue
        if start <= n < end:
            out.append(ch)
        n += 1
    return "".join(out).strip()


SPARSE = 0.06                                                           # 공백 비율이 이보다 낮고
SPARSE_MIN = 15                                                         # 공백 뺀 글자가 이만큼 이상인 줄


def pdf_merged(path):
    """옮길 글: pypdf 기본 모드(pdf_text) 줄을 쓰되, (가) 띄어쓰기가 거의 없는 줄(공백 비율 6%% 미만·15자 이상 — PDF 가 공백
    글자 없이 글자 간격으로만 띄운 줄)이나 (나) layout 모드에서 같은 글자열의 공백이 2개 이상 많은 줄은 layout 모드(pdf_layout)의
    같은 글자열 부분(공백 뺀 글자열이 같거나 그 일부)으로 바꾼다.
    공백을 뺀 글자는 바꾸지 않는다(대조). 바꾼 줄 수·못 바꾼 줄 수는 쪽 표지 뒤에 적는다. 결과는 원본 옆 .merged.txt."""
    out = path + ".merged.txt"
    if os.path.exists(out):
        return out
    P = _pages(open(pdf_text(path), encoding="utf-8").read())
    L = dict(_pages(open(pdf_layout(path), encoding="utf-8").read()))
    res = []
    for n, pt in P:
        lay = [ln for ln in L.get(n, "").split("\n") if ln.strip()]
        lay_ns = [re.sub(r"\s+", "", ln) for ln in lay]
        lines, rep, miss = [], 0, 0
        for pl in pt.split("\n"):
            st = pl.strip()
            ns = re.sub(r"\s+", "", st)
            if not ns:
                continue
            sparse = len(ns) >= SPARSE_MIN and st.count(" ") / len(st) < SPARSE
            new = None
            for ln, lns in zip(lay, lay_ns):
                k = lns.find(ns)
                if k >= 0:
                    new = _slice_keep_spaces(ln, k, k + len(ns))
                    break
            ok = new is not None and re.sub(r"\s+", "", new) == ns
            if ok and (sparse or new.count(" ") >= st.count(" ") + 2):
                lines.append(new)
                rep += 1
                continue
            if sparse:
                miss += 1
            lines.append(st)
        res.append("=== p.%d === (layout 줄로 바꿈 %d · 못 바꿈 %d)\n%s" % (n, rep, miss, "\n".join(lines)))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(res))
    return out


def hwp_text(path):
    out = path + ".md"
    if not os.path.exists(out):
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "hwp2md.py"), path, out], check=True)
    return out


# ── policy ───────────────────────────────────────────────────────────────
POLICY = {
    "저작권정책": FSS + "/fss/main/contents.do?menuNo=200701",
    "이메일무단수집거부": FSS + "/fss/main/contents.do?menuNo=200702",
}


def policy():
    rows = []
    for base in (FSS, FSC):
        r = robots(base)
        rows.append(dict(대상=base + "/robots.txt", 상태=r.status, note=r.note))
    for nm, u in POLICY.items():
        try:
            b, m, p = cached("policy", nm + ".html", u)
            t = b.decode("utf-8", "replace")
            i = t.find('class="contents"')
            j = t.find("산하기관 및 관련사이트", i)
            seg = strip_tags(t[i + 17:j]) if i >= 0 else ""
            rows.append(dict(대상=u, 상태="HTTP %s" % m["http_status"], note=seg[:1500]))
        except Stop as e:
            rows.append(dict(대상=u, 상태="멈춤", note=str(e)))
    for r in rows:
        print(r["대상"], r["상태"], r["note"][:200].replace("\n", " / "))
    write_csv(os.path.join(WORK, "9-2-4_9-5_정책확인.csv"), ["대상", "상태", "note"], rows)
    flush_log()


# ── 9-2-4 보도자료 검색 ───────────────────────────────────────────────────
# 두 게시판: 금감원 보도자료(B0000188, 금융위·금감원 공동 자료도 올라옴)와 금융위 보도자료(/no010101).
BODO = FSS + "/fss/bbs/B0000188/list.do"
BODO_VIEW = FSS + "/fss/bbs/B0000188/view.do?nttId=%s&menuNo=200218"
FSCB = FSC + "/no010101"
FSCB_VIEW = FSC + "/no010101/%s"
# 낱말. 사이트 검색은 공백 포함 문자열을 한 덩어리로 찾는다. 넓은 낱말(PRESS_TITLE_ONLY)은 제목에서만 찾는다.
PRESS_TERMS = ["ORSA", "자체위험", "자체 위험", "지급여력 평가", "지급여력평가", "위험 및 지급여력",
               "리스크 및 지급여력", "K-ICS", "킥스", "신지급여력", "보험업감독업무시행세칙", "보험업감독규정",
               "리스크관리 선진화", "위험관리 선진화", "계리 감독 선진화", "계리감독 선진화",
               "Own Risk", "재무건전성 제도 선진화", "경쟁력 강화 로드맵", "지급여력제도", "건전성 제도",
               "보험 부문 금융감독 업무설명회", "보험회사 CEO", "내부모형"]
PRESS_TITLE_ONLY = {"보험업감독규정", "보험업감독업무시행세칙", "K-ICS", "킥스", "신지급여력", "지급여력제도", "건전성 제도",
                    "보험 부문 금융감독 업무설명회", "보험회사 CEO", "내부모형"}
MAX_PAGES = 30


def bodo_rows(page):
    rows = []
    for m in re.finditer(r'<tr>\s*<td class="num">\s*(\d+)\s*</td>\s*<td class="title"><a href="([^"]+)">(.*?)</a></td>'
                         r'\s*<td>(.*?)</td>\s*<td>\s*([\d-]+)\s*</td>(.*?)</tr>', page, re.S):
        href = html.unescape(m.group(2))
        ntt = re.search(r"nttId=(\d+)", href).group(1)
        files = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
                 for x in re.findall(r'<span class="name">(.*?)</span>', m.group(6), re.S)]
        rows.append(dict(게시판="금감원 보도자료", 글번호=ntt, 제목=html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip(),
                         담당부서=strip_tags(m.group(4)), 등록일=m.group(5), 첨부=" ; ".join(files),
                         URL=BODO_VIEW % ntt))
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
                         URL=FSCB_VIEW % a.group(1)))
    return rows


SITES = {
    "fss": dict(이름="금감원 보도자료", url=lambda kw, cnd, pg: BODO + "?" + urllib.parse.urlencode(
        dict(menuNo="200218", pageIndex=str(pg), sdate="", edate="", searchCnd=cnd, searchWrd=kw)),
        cnd=lambda kw: "1" if kw in PRESS_TITLE_ONLY else "3", cndname={"1": "제목", "3": "제목+내용"},
        total=r"전체\s*<em>([\d,]+)</em>", rows=bodo_rows),
    "fsc": dict(이름="금융위 보도자료", url=lambda kw, cnd, pg: FSCB + "?" + urllib.parse.urlencode(
        dict(srchCtgry="", curPage=str(pg), srchKey=cnd, srchText=kw, srchBeginDt="", srchEndDt="")),
        cnd=lambda kw: "sj" if kw in PRESS_TITLE_ONLY else "all", cndname={"sj": "제목", "all": "제목+내용"},
        total=r"전체\s*<strong>([\d,]+)</strong>", rows=fscb_rows),
}


def press_search():
    log, cand = [], {}
    for site, S in SITES.items():
        stopped = ""
        for kw in PRESS_TERMS:
            cnd = S["cnd"](kw)
            if stopped:
                log.append(dict(게시판=S["이름"], 낱말=kw, 검색구분=S["cndname"][cnd], 사이트총건수="", 받은행=0, 쪽수=0,
                                비고="요청 안 함 — 앞 요청에서 멈춤: %s" % stopped))
                continue
            page, total, got, note = 1, None, 0, ""
            while True:
                url = S["url"](kw, cnd, page)
                try:
                    b, m, p = cached("press/search", "%s_%s_%s_p%02d.html" % (site, slug(kw), cnd, page), url,
                                     extra=dict(검색어=kw, 검색구분=cnd, 쪽=page))
                except Stop as e:
                    stopped = note = "멈춤: %s" % e
                    break
                t = b.decode("utf-8", "replace")
                mm = re.search(S["total"], t)
                total = int(mm.group(1).replace(",", "")) if mm else 0
                rows = S["rows"](t)
                for r in rows:
                    c = cand.setdefault((site, r["글번호"]), dict(r, 걸린낱말=[]))
                    c["걸린낱말"].append(kw)
                got += len(rows)
                if not rows or got >= total:
                    break
                if page >= MAX_PAGES:
                    note = "%d쪽에서 멈춤(넓음)" % MAX_PAGES
                    break
                page += 1
            log.append(dict(게시판=S["이름"], 낱말=kw, 검색구분=S["cndname"][cnd], 사이트총건수=total if total is not None else "",
                            받은행=got, 쪽수=page, 비고=note))
            print("  %s %-14s 총 %s · 받은 %d %s" % (site, kw, total, got, note[:80]))
            flush_log()
    write_csv(SEARCH_CSV, ["게시판", "낱말", "검색구분", "사이트총건수", "받은행", "쪽수", "비고"], log)
    rows = sorted(cand.values(), key=lambda r: (r["등록일"], r["게시판"]))
    for r in rows:
        r["걸린낱말"] = " ; ".join(r["걸린낱말"])
    write_csv(CAND_CSV, ["등록일", "게시판", "글번호", "제목", "담당부서", "걸린낱말", "첨부", "URL"], rows)
    print("후보 %d건 → %s" % (len(rows), CAND_CSV))


# ── 9-2-4 게시글·첨부 받기 ────────────────────────────────────────────────
# (게시판, 글번호, 구분). 구분: 1차 = 검색에서 ORSA 낱말이 걸렸거나 2차로 받은 첨부에서 ORSA 낱말이 나온 글(pdf·hwp 모두 받음),
# 2차 = K-ICS·감독규정 개정 등 첨부에 ORSA 언급이 있는지 확인하려고 받은 글(검색기록 csv 참조) — 첨부에 ORSA 낱말이 없으면
# md 에는 「받아 보았으나 ORSA 낱말 없음」 목록으로만.
PRESS = [
    ("fsc", "71215", "1차"), ("fss", "11138", "1차"),        # 2014-07-31 재무건전성 (감독)제도 선진화 종합로드맵
    ("fsc", "71775", "2차"), ("fss", "11964", "2차"),        # 2015-10-19 보험산업 경쟁력 강화 로드맵
    ("fsc", "71823", "2차"),                                # 2015-11-24 보험업감독규정 개정안 공포 및 시행
    ("fsc", "72075", "1차"), ("fss", "12368", "1차"),        # 2016-03-30/31 경쟁력 강화 로드맵 후속 보험업법령 개정·시행
    ("fsc", "72110", "2차"),                                # 2016-04-25 보험업감독규정 개정안 규정변경 예고
    ("fsc", "72435", "2차"), ("fss", "12921", "2차"),        # 2016-11-14/15 보험업감독규정 개정안 규정변경 예고
    ("fsc", "72740", "1차"),                                # 2017-06-28 IFRS17 대비 단계적 책임준비금 추가적립
    ("fss", "13591", "2차"),                                # 2017-08-28 보험업감독규정 및 세칙 개정
    ("fsc", "73104", "2차"),                                # 2018-04-05 新지급여력제도 도입초안
    ("fss", "14375", "1차"),                                # 2018-08-01 K-ICS 내부모형 승인 예비신청
    ("fss", "14706", "1차"), ("fsc", "73453", "1차"),        # 2018-12-12 ORSA 운영
    ("fss", "57414", "2차"),                                # 2022-12-05 시가평가 기반 지급여력제도 시행 예정
    ("fss", "57841", "2차"),                                # 2023-01-09 K-ICS 해설서
    ("fss", "58388", "1차"),                                # 2023-03-22 2023년 보험 부문 금융감독 업무설명회
    ("fsc", "81186", "2차"),                                # 2023-12-06 금융위-금감원-보험회사 CEO 간담회
    ("fsc", "81321", "2차"), ("fss", "132504", "2차"),       # 2023-12-22 보험업감독규정 개정안
    ("fss", "134241", "2차"),                               # 2024-02-28 2024년 보험 부문 금융감독 업무설명회
    ("fss", "136362", "2차"),                               # 2024-05-30 금감원장 보험회사 CEO 간담회
    ("fss", "188048", "1차"),                               # 2024-11-06 K-ICS 내부모형 승인신청 매뉴얼
    ("fss", "191523", "2차"),                               # 2025-02-27 금감원장 보험회사 CEO 간담회
    ("fss", "191698", "2차"),                               # 2025-03-05 2025년 보험 부문 금융감독 업무설명회
    ("fsc", "84128", "2차"), ("fss", "191865", "2차"),       # 2025-03-12 보험업권 자본규제 고도화
    ("fsc", "84742", "2차"), ("fss", "194839", "2차"),       # 2025-06-11 보험업감독규정 주요 개정사항
    ("fsc", "85446", "2차"), ("fss", "205410", "2차"),       # 2025-10-20 단계적 할인율 조정·듀레이션갭
    ("fsc", "86032", "2차"),                                # 2026-01-13 기본자본 K-ICS
    ("fsc", "86099", "2차"),                                # 2026-01-20 계리가정 관리·감독 체계
    ("fss", "212467", "2차"),                               # 2026-02-26 금감원장 보험회사 CEO 간담회
    ("fss", "214172", "1차"),                               # 2026-03-11 2026년 보험 부문 금융감독 업무설명회
    ("fss", "218927", "1차"), ("fsc", "87205", "1차"),       # 2026-06-29 감독규정·세칙 개정(별표37 등)
    ("fsc", "87701", "2차"),                                # 2026-09-11 계리가정 보고서 도입
]
ORSA_TERMS = re.compile(r"ORSA|자체\s*위험\s*및\s*지급여력|자체\s*위험\s*(?:및\s*지급여력\s*)?평가|자체\s*리스크|"
                        r"Own\s*Risk|위험\s*및\s*지급여력\s*평가|리스크와\s*지급여력")


def view_meta(site, page):
    """게시글 화면 → (제목, 등록일, 담당부서, 본문 글, [(첨부 URL, 파일명)])."""
    if site == "fss":
        title = re.search(r'<h3 class="subject">(.*?)</h3>', page, re.S)
        day = re.search(r"<dt>등록일</dt>\s*<dd>\s*([\d-]+)", page)
        dept = re.search(r"<dt>담당부서</dt>\s*<dd>(.*?)</dd>", page, re.S)
        body = re.search(r'<div class="n-dbdata">(.*?)</div>', page, re.S)
        files = [(FSS + html.unescape(h),
                  re.sub(r"\s*\(파일크기:[^)]*\)\s*$", "", html.unescape(re.sub(r"<[^>]+>", "", n)).strip()))
                 for h, n in re.findall(r'<a href="(/fss/cmmn/file/fileDown\.do\?[^"]+)" class="btn-attach-download">(.*?)</a>',
                                        page, re.S)]
    else:
        k = page.find('<div class="board-view-wrap')
        page = page[k:] if k >= 0 else page
        title = re.search(r'<div class="subject">\s*(.*?)\s*</div>', page, re.S)
        day = re.search(r'<div class="day">\s*<span>\s*([\d-]+)', page)
        dept = re.search(r"<strong>담당부서</strong>\s*([^<]*)</span>", page)
        body = re.search(r'<div class="cont">(.*?)</div>\s*<div class="file">', page, re.S) or re.search(
            r'<div class="cont">(.*?)</div>\s*<div class="btn-board">', page, re.S)
        files, seen = [], set()
        for h, n in re.findall(r'<a href="(/comm/getFile\?[^"]+)" title="([^"]*)"', page):
            h = html.unescape(h)
            if h in seen or "다운로드" in n:
                continue
            seen.add(h)
            files.append((FSC + h, html.unescape(n).strip()))
    g = lambda m: html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    return g(title), (day.group(1) if day else ""), g(dept), (strip_tags(body.group(1)) if body else ""), files


def hwpx_text(path):
    """hwpx(zip 안 Contents/section*.xml)의 <hp:t> 글을 문단(<hp:p>)마다 한 줄로. 글자는 그대로."""
    out = path + ".txt"
    if os.path.exists(out):
        return out
    import zipfile
    z = zipfile.ZipFile(path)
    secs = sorted([n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)],
                  key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
    lines = []
    for n in secs:
        x = z.read(n).decode("utf-8", "replace")
        for para in re.findall(r"<hp:p\b.*?</hp:p>", x, re.S):
            t = "".join(html.unescape(m) for m in re.findall(r"<hp:t\b[^>]*>(.*?)</hp:t>", para, re.S))
            t = re.sub(r"<[^>]+>", "", t)
            if t.strip():
                lines.append(t)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out


def attach_text(path, name):
    low = name.lower()
    if low.endswith(".pdf"):
        return pdf_text(path)
    if low.endswith(".hwp"):
        return hwp_text(path)
    if low.endswith(".hwpx"):
        return hwpx_text(path)
    return ""


def pick_files(files, role):
    """1차: pdf·hwp/hwpx 모두(글은 hwp 쪽이 정확 — pypdf 는 한글 PDF 에서 띄어쓰기를 빠뜨리는 곳이 있어 hwp 글을 옮기고
    PDF 는 쪽 번호를 찾는 데 쓴다). 2차: pdf 가 있으면 pdf 만, 없으면 hwp/hwpx."""
    pdfs = [f for f in files if f[1].lower().endswith(".pdf")]
    hwps = [f for f in files if f[1].lower().endswith((".hwp", ".hwpx"))]
    if role == "1차":
        return pdfs + hwps
    return pdfs or hwps


def press_fetch():
    rows = []
    for site, no, role in PRESS:
        url = (BODO_VIEW if site == "fss" else FSCB_VIEW) % no
        rec = dict(게시판=SITES[site]["이름"], 글번호=no, 구분=role, URL=url, 제목="", 등록일="", 담당부서="",
                   본문글자수=0, 첨부="", 받은첨부="", 텍스트="", sha256="", ORSA낱말쪽="", 상태="")
        try:
            b, m, p = cached("press/view", "%s_%s.html" % (site, no), url)
            title, day, dept, body, files = view_meta(site, b.decode("utf-8", "replace"))
            rec.update(제목=title, 등록일=day, 담당부서=dept, 본문글자수=len(body), 첨부=" ; ".join(n for _, n in files))
            with open(p + ".body.txt", "w", encoding="utf-8") as f:
                f.write(body)
            got, txts, shas, hits = [], [], [], []
            for k, (furl, fname) in enumerate(pick_files(files, role), 1):
                ext = os.path.splitext(fname)[1].lower()
                fb, fm, fp = cached("press/file", "%s_%s_%d%s" % (site, no, k, ext), furl, referer=url,
                                    extra=dict(게시글URL=url, 원파일명=fname))
                tp = attach_text(fp, fname)
                got.append(fname)
                txts.append(tp)
                shas.append(fm["sha256"])
                if tp:
                    t = open(tp, encoding="utf-8").read()
                    pg = "1"
                    for ln in t.split("\n"):
                        mm = re.match(r"=== p\.(\d+) ===", ln)
                        if mm:
                            pg = mm.group(1)
                        elif ORSA_TERMS.search(ln):
                            hits.append("%s:p.%s" % (k, pg) if ext == ".pdf" else "%s:%s" % (k, ORSA_TERMS.search(ln).group(0)))
            if ORSA_TERMS.search(body):
                hits.insert(0, "본문")
            rec.update(받은첨부=" ; ".join(got), 텍스트=" ; ".join(txts), sha256=" ; ".join(shas),
                       ORSA낱말쪽=" ".join(sorted(set(hits), key=hits.index)), 상태="OK")
        except Stop as e:
            rec["상태"] = "멈춤: %s" % e
        print("  %s %s %s %s %s · ORSA %s" % (site, no, rec["등록일"], rec["제목"][:40], rec["상태"][:60], rec["ORSA낱말쪽"][:80]))
        rows.append(rec)
        flush_log()
    write_csv(os.path.join(WORK, "9-2-4_보도자료_받은글.csv"), list(rows[0].keys()), rows)


# ── 9-5 금융회사 경영유의사항 등 공시 ───────────────────────────────────────
IMPR = FSS + "/fss/job/openInfoImpr/list.do"
SANC = FSS + "/fss/job/openInfo/list.do"
HOLD_RE = re.compile(r"지주")                                           # 기관명에 「지주」(금융지주회사) — 판정 근거는 md 머리에
NONBANK = re.compile(r"메리츠|한국투자")                                 # 비은행지주(지시서): 메리츠금융지주·한국투자금융지주


def impr_rows(page):
    rows = []
    for m in re.finditer(r'<tr>\s*<td class="no">\s*(\d+)\s*</td>\s*<td>(.*?)</td>\s*<td>\s*(\d{8})\s*</td>\s*<td>(.*?)</td>'
                         r'\s*<td>(.*?)</td>', page, re.S):
        a = re.search(r'<a href="(/fss\.hpdownload\?[^"]+)"', m.group(4))
        href = html.unescape(a.group(1)) if a else ""
        fname = urllib.parse.unquote_plus(re.search(r"file=([^&]+)", href).group(1)) if "file=" in href else ""
        rows.append(dict(일련번호=m.group(1), 제재대상기관=strip_tags(m.group(2)), 제재조치요구일=m.group(3),
                         관련부서=strip_tags(m.group(5)), 파일명=fname, url=(FSS + href) if href else ""))
    return rows


def list_all(base, menu, tag, rows_fn, extra_q=None, max_pages=200):
    """목록 전 쪽(SDATE~EDATE). (총건수, 행, 쪽수, 비고)"""
    out, page, total, note = [], 1, None, ""
    while True:
        q = dict(menuNo=menu, pageIndex=str(page), sdate=SDATE, edate=EDATE, searchCnd="4", searchWrd="")
        q.update(extra_q or {})
        url = base + "?" + urllib.parse.urlencode(q)
        try:
            b, m, p = cached("exam/list", "%s_p%03d.html" % (tag, page), url, extra=dict(쪽=page, 질의=q))
        except Stop as e:
            note = "멈춤: %s" % e
            break
        t = b.decode("utf-8", "replace")
        mm = re.search(r"전체\s*<em>([\d,]+)</em>", t)
        total = int(mm.group(1).replace(",", "")) if mm else 0
        rows = rows_fn(t)
        out += rows
        if not rows or len(out) >= total:
            break
        if page >= max_pages:
            note = "%d쪽에서 멈춤" % max_pages
            break
        page += 1
    return total, out, page, note


def impr():
    log = []
    total, rows, pages, note = list_all(IMPR, "200483", "impr_all", impr_rows)
    print("경영유의사항 등 공시 %s~%s 총 %s건 · 받은 행 %d · %d쪽 %s" % (SDATE, EDATE, total, len(rows), pages, note))
    log.append(dict(목록="금융회사 경영유의사항 등 공시(menuNo=200483)", 질의="sdate=%s edate=%s searchCnd=4(전체) searchWrd=(빈칸)"
                    % (SDATE, EDATE), 사이트총건수=total, 받은행=len(rows), 쪽수=pages, 비고=note))
    # 대조: 사이트의 금융회사명 검색 「지주」
    t2, r2, p2, n2 = list_all(IMPR, "200483", "impr_jiju", impr_rows, dict(searchCnd="1", searchWrd="지주"))
    log.append(dict(목록="금융회사 경영유의사항 등 공시(menuNo=200483)", 질의="sdate=%s edate=%s searchCnd=1(금융회사명) searchWrd=지주"
                    % (SDATE, EDATE), 사이트총건수=t2, 받은행=len(r2), 쪽수=p2, 비고=n2))
    write_csv(IMPR_ALL_CSV, ["일련번호", "제재대상기관", "제재조치요구일", "관련부서", "파일명", "url"], rows)
    hold = [r for r in rows if HOLD_RE.search(r["제재대상기관"])]
    a = {(r["제재대상기관"], r["제재조치요구일"], r["파일명"]) for r in hold}
    b = {(r["제재대상기관"], r["제재조치요구일"], r["파일명"]) for r in r2}
    print("  기관명 「지주」: 전체목록에서 %d건 · 사이트 검색 %d건 · 차이 %s / %s" % (len(hold), len(r2), sorted(a - b), sorted(b - a)))
    log.append(dict(목록="대조", 질의="전체목록 중 기관명에 「지주」 vs 사이트 금융회사명 검색 「지주」", 사이트총건수="",
                    받은행="%d / %d" % (len(hold), len(r2)), 쪽수="", 비고="차이: %s / %s" % (sorted(a - b), sorted(b - a))))
    for r in hold:
        print("   ", r["제재조치요구일"], r["제재대상기관"], r["관련부서"], r["파일명"])
        try:
            ext = os.path.splitext(r["파일명"])[1].lower() or ".pdf"
            fb, fm, fp = cached("exam/impr", "%s_%s_%s%s" % (r["제재조치요구일"], slug(r["제재대상기관"], 20), r["일련번호"], ext),
                                r["url"], referer=IMPR + "?menuNo=200483",
                                extra=dict(제재대상기관=r["제재대상기관"], 제재조치요구일=r["제재조치요구일"], 원파일명=r["파일명"],
                                           목록="금융회사 경영유의사항 등 공시"))
            if not fb[:5] == b"%PDF-":
                print("     ! PDF 아님: %r" % fb[:60])
            else:
                pdf_merged(fp)
        except Stop as e:
            print("     멈춤:", e)
    write_csv(os.path.join(WORK, "9-5_검색기록.csv"), ["목록", "질의", "사이트총건수", "받은행", "쪽수", "비고"], log)


# ── 9-5 참고: 검사결과제재(제재내용 공시) 가운데 금융회사명 「지주」 ─────────────────
def sanc_rows(page):
    rows = []
    for m in re.finditer(r'<tr>\s*<td>(\d+)</td>\s*<td>(.*?)</td>\s*<td>(\d{8})</td>\s*<td><a href="([^"]+)"[^>]*>.*?</a></td>'
                         r'\s*<td>(.*?)</td>', page, re.S):
        href = html.unescape(m.group(4))
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(href).query))
        rows.append(dict(번호=m.group(1), 제재대상기관=strip_tags(m.group(2)), 제재조치요구일=m.group(3), 관련부서=strip_tags(m.group(5)),
                         examMgmtNo=q.get("examMgmtNo", ""), emOpenSeq=q.get("emOpenSeq", ""),
                         url=FSS + "/fss/job/openInfo/view.do?menuNo=200476&examMgmtNo=%s&emOpenSeq=%s"
                         % (q.get("examMgmtNo", ""), q.get("emOpenSeq", ""))))
    return rows


def sanc_view(page):
    def dd(label):
        m = re.search(r'<dt class="form-tit">%s</dt>\s*<dd class="form-conts">(.*?)</dd>' % re.escape(label), page, re.S)
        return strip_tags(m.group(1)) if m else ""
    files = [(FSS + html.unescape(h), html.unescape(n).strip()) for h, n in
             re.findall(r'<a href="(/fss\.hpdownload\?[^"]+)"[^>]*>.*?<span class="name">(.*?)</span>', page, re.S)]
    return dict(기관제재=dd("기관 제재대상"), 임원제재=dd("임원 제재대상"), 직원제재=dd("직원 제재대상"),
                제재대상사실=dd("제재대상사실")), files


def sanc():
    total, rows, pages, note = list_all(SANC, "200476", "sanc_jiju", sanc_rows, dict(searchCnd="1", searchWrd="지주"))
    print("검사결과제재 %s~%s 금융회사명 「지주」 총 %s건 · 받은 행 %d %s" % (SDATE, EDATE, total, len(rows), note))
    out = []
    for r in rows:
        rec = dict(r, 기관제재="", 임원제재="", 직원제재="", 제재대상사실="", 파일="", 파일명="", sha256="", 상태="")
        try:
            b, m, p = cached("exam/sanc", "sanc_%s_%s.html" % (r["examMgmtNo"], r["emOpenSeq"]), r["url"],
                             referer=SANC + "?menuNo=200476")
            info, files = sanc_view(b.decode("utf-8", "replace"))
            rec.update(info)
            for k, (furl, fname) in enumerate(files, 1):
                fb, fm, fp = cached("exam/sanc", "sanc_%s_%s_%d.pdf" % (r["examMgmtNo"], r["emOpenSeq"], k), furl,
                                    referer=r["url"], extra=dict(원파일명=fname, 제재대상기관=r["제재대상기관"]))
                if fb[:5] == b"%PDF-":
                    pdf_merged(fp)
                rec.update(파일=fp, 파일명=fname, sha256=fm["sha256"])
            rec["상태"] = "OK"
        except Stop as e:
            rec["상태"] = "멈춤: %s" % e
        print("  ", r["제재조치요구일"], r["제재대상기관"], rec["기관제재"], "|", rec["임원제재"], "|", rec["직원제재"], "|", rec["파일명"])
        out.append(rec)
    write_csv(SANC_CSV, list(out[0].keys()), out)
    with open(os.path.join(WORK, "9-5_검색기록.csv"), "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["검사결과제재(menuNo=200476)", "sdate=%s edate=%s searchCnd=1(금융회사명) searchWrd=지주" % (SDATE, EDATE),
                                total, len(rows), pages, note])


# ── 9-5 공개안 PDF → 지적 항목 ─────────────────────────────────────────────
SEC_RE = re.compile(r"^(?:[가-하]|\d+)\.\s*((?:경영\s*유의\s*사항|개선\s*사항|(?=[^\n]{0,40}사항\s*$)(?:문책|자율처리|주의|준법교육)[^\n]*)\s*)$")
ITEM_RE = re.compile(r"^(\(\d+\)(?!-)|\d+\)|[⑴-⒇]|[가-하]\.)\s*(\S.*)$")
SUB_RE = re.compile(r"^\(\d+\)-\d+")
FOOT_RE = re.compile(r"^(?:-\s*\d+\s*-|\d{1,3})$")                     # 쪽 번호 줄(「- N -」·숫자만 있는 줄)
CITE_RE = re.compile(r"[｢「]([^｣」\n]{2,60})[｣」]\s*((?:제\s*\d+\s*조(?:\s*의\s*\d+)?(?:\s*제?\s*\d+\s*항)?(?:\s*제?\s*\d+\s*호)?"
                     r"(?:\s*[가-하]\s*목)?(?:\s*[,ㆍ·및]\s*)?)+|\[?<?별표\s*\d+\]?>?|<별지\s*\d+>)")
REL_RE = re.compile(r"^<\s*관련\s*(?:규정|법규)\s*>$")


def declared(text):
    """조치내용 칸의 건수(경영유의사항 N건·개선사항 N건 등)."""
    head = text[:1500]
    d = {}
    for k, pat in (("경영유의사항", r"경영유의(?:사항)?\s*:?\s*(\d+)\s*건"), ("개선사항", r"개선\s*사항\s*:?\s*(\d+)\s*건")):
        m = re.search(pat, head)
        if m:
            d[k] = int(m.group(1))
    return d


def _style(marker):
    return ("(n)" if marker.startswith("(") else "n)" if marker[0].isdigit() else "⑴" if marker[0] in "⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇"
            else "가.")


def parse_items(merged_path):
    """merged 글 → 항목 목록. 각 항목: 구분·번호·제목·쪽·본문(글자 그대로, 쪽 번호 줄 「- N -」 만 뺌)·관련규정·인용조문.
    항목 번호 꼴은 문서마다 다르다(「(1)」·「1)」·「⑴」·「가.」) — 구분 표지 다음 첫 항목의 꼴만 그 문서의 항목 번호로 보고,
    다른 꼴(예: 「(7)」 안의 「1) 2) 3)」)은 본문으로 둔다. 「(1)-1」 은 본문(소항목). 제목은 layout 글의 같은 줄에서 가져온다
    (기본 모드가 제목 줄을 「‧」 등에서 끊는 곳이 있음)."""
    text = open(merged_path, encoding="utf-8").read()
    lay = [re.sub(r"[ \t]{2,}", " ", x).strip() for x in
           open(merged_path.replace(".merged.txt", ".layout.txt"), encoding="utf-8").read().split("\n")]
    lay_ns = [re.sub(r"\s+", "", x) for x in lay]
    items, sec, cur, page, style = [], "", None, 1, None
    in_rel = False
    for ln in text.split("\n"):
        m = re.match(r"=== p\.(\d+) ===", ln)
        if m:
            page = int(m.group(1))
            continue
        st = ln.strip()
        if FOOT_RE.match(st):
            continue
        ms = SEC_RE.match(st)
        if ms:
            sec = re.sub(r"\s+", "", ms.group(1))
            cur, in_rel = None, False
            continue
        mi = ITEM_RE.match(st)
        if mi and not SUB_RE.match(st) and (style is None or _style(mi.group(1)) == style):
            style = style or _style(mi.group(1))
            ns = re.sub(r"\s+", "", st)
            title = mi.group(2).strip()
            for x, xn in zip(lay, lay_ns):
                if xn.startswith(ns) and len(xn) > len(ns):
                    mm = ITEM_RE.match(x)
                    if mm:
                        title = mm.group(2).strip()
                    break
            cur = dict(구분=sec or "(구분 표지 없음)", 번호=mi.group(1), 제목=title, 쪽=[page], 본문=[st], 관련규정=[])
            items.append(cur)
            in_rel = False
            continue
        if cur is None:
            continue
        if page not in cur["쪽"]:
            cur["쪽"].append(page)
        cur["본문"].append(st)
        if REL_RE.match(re.sub(r"\s+", "", st).replace("<관련", "< 관련").replace(">", " >")) or \
                re.match(r"^<\s*관련\s*(규정|법규)\s*>$", st):
            in_rel = True
            continue
        if in_rel and st:
            cur["관련규정"].append(st)
    for it in items:
        rel = " ".join(it["관련규정"])
        it["관련규정"] = [x.strip() for x in re.split(r"\s*(?=(?:\d+\.|-)\s*[｢「])", rel) if x.strip()]
        body = "\n".join(it["본문"])
        cites = []
        for m in CITE_RE.finditer(re.sub(r"\s*\n\s*", " ", body)):
            c = "｢%s｣ %s" % (m.group(1).strip(), re.sub(r"\s+", " ", m.group(2)).strip(" ,ㆍ·및"))
            if c not in cites:
                cites.append(c)
        it["인용조문"] = cites
    return items


def head_info(merged_path):
    t = open(merged_path, encoding="utf-8").read()
    t1 = t.split("4. 제재대상사실")[0].split("4.제재대상사실")[0].split("4. 조치대상사실")[0].split("4.조치대상사실")[0]
    t1 = t1.split("Ⅳ.조치대상사실")[0].split("Ⅳ. 조치대상사실")[0]
    t1 = re.sub(r"=== p\.\d+ ===[^\n]*\n", "", t1)
    return "\n".join(x for x in t1.split("\n") if not FOOT_RE.match(x.strip())).strip(), declared(t)


def review():
    """판정용 덤프(dart_out/risk13/9-5_항목검토.txt) — 항목 수와 조치내용 건수 대조."""
    out = []
    for sub in ("impr", "sanc"):
        for f in sorted(os.listdir(os.path.join(D, "exam", sub))):
            if not f.endswith(".merged.txt"):
                continue
            mp = os.path.join(D, "exam", sub, f)
            items = parse_items(mp)
            head, dec = head_info(mp)
            cnt = {}
            for it in items:
                k = "경영유의사항" if "경영유의" in it["구분"] else "개선사항" if "개선" in it["구분"] else it["구분"]
                cnt[k] = cnt.get(k, 0) + 1
            flag = "" if all(cnt.get(k) == v for k, v in dec.items()) else "  !!! 건수 다름"
            out.append("##### %s/%s  조치내용 %s · 파싱 %s%s" % (sub, f, dec, cnt, flag))
            for k, it in enumerate(items, 1):
                out.append("[%d] %s %s %s (p.%s) 규정:%s 인용:%s" % (k, it["구분"], it["번호"], it["제목"],
                           ",".join(map(str, it["쪽"])), it["관련규정"], it["인용조문"]))
                out.append("     " + " ".join(it["본문"][1:])[:500])
    with open(os.path.join(WORK, "9-5_항목검토.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("\n".join(l for l in out if l.startswith("#####")))


# ── build: 산출 md·csv ─────────────────────────────────────────────────────
PF = os.path.join(D, "press", "file")
PV = os.path.join(D, "press", "view")
MOBEOM = os.path.join(RAW, "mobeom", "fss", "모범규준_20170401판_붙임2_통합위험관리_전문.hwp.md")   # 9-4 작업이 받은 원본(읽기만)

# 9-2-4 인용: (번호, 게시판·글번호 목록, 인용 원본 파일(press/file 아래), 시작 표지, 끝 표지(포함), 모범규준 조(판단), note)
# 시작·끝 표지는 원본 텍스트(hwp2md 결과 또는 PDF merged 글)에 글자 그대로 있어야 한다 — 없으면 멈춘다.
PQ = [
    ("Q1", [("fsc", "71215"), ("fss", "11138")], "fsc_71215_1.hwp.md", "| 배포일 | 2014. 7. 31.(목)", "제 목: 보험회사의 재무건전성 제도 선진화 종합로드맵 마련",
     "", "배포일·제목"),
    ("Q1", [("fsc", "71215"), ("fss", "11138")], "fsc_71215_1.hwp.md", "□ (자체 위험 및 지급여력 평가제도)", "‘17년 시행",
     "제5장(36~49조) 내부자본 적정성 평가·관리(판단)", "도입 발표·추진일정(시범운영 '15~'16 → '17 시행)"),
    ("Q1", [("fsc", "71215"), ("fss", "11138")], "fsc_71215_1.hwp.md", "재무건전성 감독제도 선진화 종합로드맵<br>[내부표] \\| 구 분",
     "\\| 재무건전성 공시 개선 \\| (방안수립) \\| 시행 \\|", "", "로드맵 표(Pillar 2 줄) — [표 깨짐: hwp2md 가 표 안의 표를 한 칸에 펼침. 칸 구분 「\\|」, 행 구분 「 / 」]"),
    ("Q1", [("fsc", "71215"), ("fss", "11138")], "fsc_71215_1.hwp.md", "□ (자본공시 강화)", "위험공시 기능을 강화", "", "참고1 기타 선진화 종합로드맵 내용"),
    ("Q1", [("fsc", "71215"), ("fss", "11138")], "fsc_71215_1.hwp.md", "◦ ‘14년 하반기 중 보험업감독규정", "규정화 작업을 우선 완료할 예정",
     "", "향후 계획"),
    ("Q2", [("fsc", "72075"), ("fss", "12368")], "fsc_72075_2.hwp.md", "|  | 보도 | 배포 시부터 즉시 |", "보험업법령 개정·시행", "", "보도·배포일·제목"),
    ("Q2", [("fsc", "72075"), ("fss", "12368")], "fsc_72075_2.hwp.md", " ㅇ  '15.12.18일부터 순차적으로", "보험업감독업무시행세칙(3.30일 확정)",
     "", "개정 경과(시행령·감독규정·세칙 의결·확정일과 시행일)"),
    ("Q2", [("fsc", "72075"), ("fss", "12368")], "fsc_72075_2.hwp.md", " 자체 위험 및 지급여력 평가제도 도입\n", "자체위험 및 지급여력 평가제도 세부기준 마련",
     "제5장(36~49조)(판단)", "개정안 주요내용 2. 사후적 건전성 감독 시스템 강화"),
    ("Q2", [("fsc", "72075"), ("fss", "12368")], "fsc_72075_2.hwp.md", "□ 관보게재 등을 거쳐 공포일(4.1일)부터 단계적으로 시행", "<보험업법 시행령 등 개정 보험업법령의 시행일>",
     "", "시행 일정"),
    ("Q2", [("fsc", "72075"), ("fss", "12368")], "fsc_72075_2.hwp.md", "| 자체 위험 및 지급여력 평가제도 도입 | ‘17.1.1일 |", "| 위기상황분석 관련 체계 마련 | ‘17.1.1일 |",
     "", "시행일 표 가운데 두 줄"),
    ("Q3", [("fsc", "72740")], "fsc_72740_2.hwp.md", "|  | 보도 | 2017.6.28.(수) 9시부터 |", "보험권 국제회계기준 도입준비위원회 제2차 회의 개최", "", "보도일·제목"),
    ("Q3", [("fsc", "72740")], "fsc_72740_2.hwp.md", "| < 그간의 보험권 재무건전성 제도 선진화 주요과제* 추진 경과 >", "'16년 도입 |", "",
     "리스크 중심 감독체계 구축 계획 — 추진 경과 상자"),
    ("Q4", [("fss", "14375")], "fss_14375_2.hwp.md", "|  |  | 보 도 자 료 |", "| 배포 | 2018. 7. 31.(화) |", "", "보도·배포일"),
    ("Q4", [("fss", "14375")], "fss_14375_2.hwp.md", "□ (ORSA*제도 연계)", "지급여력비율 산출을 위한 내부모형 사용 유인이 증가", "37·44조(판단)",
     "2. 내부모형 승인제도의 필요성"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", "|  | 보도 | 2018. 12. 13.(목) 조간", "역량을 키울 수 있도록 지원하겠습니다.", "", "보도·배포일·제목"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", "| ◈ 그간 보험회사는 지급여력제도(RBC)와 별도로", "동 평가에도 대비할 필요", "", "요약 상자"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", " □ 이에 따라 보험회사의 재무건전성 제도 선진화의 일환", "지원하기 위한 제도(참고1)",
     "제5장(36~49조)(판단)", "1. 추진 배경 — '17년 도입"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", " □ 보험회사는 ‘17년 제도 시행에 따라", "필요시 이사회 승인절차를 거쳐 제도시행을 유예 가능",
     "36조(적용대상)(판단)", "유예 허용(현행 제도)"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", "2. 주요 내용", "해당 보험회사에 개별 제공", "41조(독립적인 제3자 점검)(판단)",
     "2. 주요 내용(운영실태 평가·공표, 내부모형 승인기준 반영, 피드백)"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", "□ (정의) 보험회사가 스스로", "리스크중심의 경영으로 전환 유도",
     "37·39·42~46조(판단)", "참고1 ORSA 개요"),
    ("Q5", [("fsc", "73453"), ("fss", "14706")], "fsc_73453_2.hwp.md", "□ 53개* 보험회사 중 11개사가", "| 도입비율<br>(누적) | 20.8% | 26.4% | 41.5% | 45.3%% | 71.7% | 100.0% |  |",
     "", "참고2 운영현황(시행·유예 회사 수)"),
    ("Q6", [("fss", "58388")], "fss_58388_2.pdf", "1 – ① 리스크 중심의 건전성 감독 역량 강화", "• 시장변동성 확대에 대비한 보험권 외환리스크 요인 점검", "",
     "별첨1 2023년 보험부문 감독방향 p.13(슬라이드 쪽 번호 12)"),
    ("Q6", [("fss", "58388")], "fss_58388_2.pdf", "1 – ② 新 건전성 제도 안착 지원 및 후속 제도개선", "1 – ② 新 건전성 제도 안착 지원 및 후속 제도개선", "",
     "별첨1 p.14 슬라이드 제목(pypdf 가 쪽 끝에 뽑음 — 그 앞 세로 글 「IFRS17 및 K-ICS의 원활한 안착 지원」 등은 글자마다 줄이 나뉘어 [표 깨짐])"),
    ("Q6", [("fss", "58388")], "fss_58388_2.pdf", "• K-ICS 기반 내부모형 승인절차 구축 추진", "• 회사 규모별 ORSA 평가기준 차등화 등 실효성 제고 방안 마련", "36조(판단)",
     "별첨1 p.14(슬라이드 쪽 번호 13)"),
    ("Q7", [("fss", "188048")], "fss_188048_2.hwp.md", "| 보도 | 2024.11.6.(수) 석간 |", "| 배포 | 2024.11.5.(화) |", "", "보도·배포일"),
    ("Q7", [("fss", "188048")], "fss_188048_2.hwp.md", "󰊴 (자체위험 및 지급여력 평가체제) 자체위험", "‘경영관리리스크’, ‘보험리스크’의 보험회사 자체 평가결과",
     "", "2. 내부모형 점검항목 및 평가기준 󰊴"),
    ("Q8", [("fss", "214172")], "fss_214172_2.pdf", "• 리스크 공시제도의 효과적 운영을 위해", "개선사항을 보험회사에 전파", "",
     "별첨1 26년 보험 감독 부문 업무설명회 자료 p.17(슬라이드 쪽 번호 16)"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "| 보도시점 | 2026.6.30.(화) 조간 |", "｢보험업감독업무시행세칙｣ 개정안 시행 |", "",
     "보도시점·배포·제목"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "◈  (자체위험 및 지급여력 평가체제(ORSA*) 도입 의무화)", "’26년 12월말부터 적용 |",
     "36·39·41조(판단)", "주요 개선 내용 상자(ORSA 의무화·적용대상·유예·시행일)"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "  이에 금융위원회(위원장 이억원)", "진행(40일)", "",
     "Ⅰ 배경 — 계리감독 선진화 방안(’26.1.20.)·사전예고 기간"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "또한, 보험회사가 스스로 위험 전반과 지급여력을", "2) 소형(수입보험료 5천억원 이하) 및 외국계 지점 회사는 시행 유예 가능",
     "36조(판단)", "Ⅰ 배경 — ORSA('17년 도입) 의무화"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "| 3. ORSA 제도 개선을 통한 자체 리스크관리 강화 |", "❹ 공시 강화를 통한 시장 규율 확립[공시기준 정비] |",
     "36·39·41조(판단)", "Ⅱ 3. ORSA 제도 개선(적용대상·역할·점검·공시)"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "  금번 보험업감독업무시행세칙 개정사항은", "일부 사항은 ’26년말부터 적용한다.", "",
     "Ⅲ 향후 계획 — 적용 시기"),
    ("Q9", [("fsc", "87205"), ("fss", "218927")], "fsc_87205_2.hwp.md", "| 참고 |  | ORSA 제도 개요 |", "④ (평가결과 활용) ORSA 평가결과를 전략수립, 가격결정, 자본계획 수립, 투자정책 수립, 성과 평가 등에 활용",
     "35·37·39·42~49조(판단)", "참고 ORSA 제도 개요"),
]
PQ_TITLE = {
    "Q1": "2014-07-31 「보험회사의 재무건전성 제도 선진화 종합로드맵 마련」(금융위·금감원)",
    "Q2": "2016-03-30 「｢보험산업 경쟁력 강화 로드맵｣ 후속 조치를 위한 ｢보험업법 시행령｣ 등 보험업법령 개정·시행」(금융위·금감원)",
    "Q3": "2017-06-28 「‘21년 새로운 보험 국제회계기준(IFRS17) 시행에 대비한 단계적 책임준비금 추가적립 방안 마련」(금융위·금감원·생보협회·손보협회)",
    "Q4": "2018-08-01 「新지급여력제도(K-ICS) 도입대비 내부모형 승인 예비신청절차 착수」(금감원)",
    "Q5": "2018-12-12 「보험회사가 스스로 리스크와 지급여력을 평가하고 관리할 수 있는 역량을 키울 수 있도록 지원하겠습니다.」(금융위·금감원)",
    "Q6": "2023-03-22 「2023년 보험 부문 금융감독 업무설명회 개최」 별첨1(금감원)",
    "Q7": "2024-11-06 「K-ICS 내부모형 승인신청 매뉴얼 마련 및 홈페이지 게시」(금감원)",
    "Q8": "2026-03-11 「2026년 보험 부문 금융감독 업무설명회 개최」 별첨1(금감원)",
    "Q9": "2026-06-29 「보험부채 평가기준의 합리성과 신뢰성이 제고되고, IFRS17(‘23년 시행) 체계하 보험업권도 리스크 관리를 위한 K-ICS 내부모형을 활용할 수 있게 되는 등 보험회사의 리스크관리 역량이 더욱 고도화됩니다.」(금융위·금감원)",
}


def _cut(text, start, end, where):
    i = text.find(start)
    if i < 0:
        raise SystemExit("시작 표지를 못 찾음(%s): %r" % (where, start))
    k = text.find(end, i)
    if k < 0:
        raise SystemExit("끝 표지를 못 찾음(%s): %r" % (where, end))
    return text[i:k + len(end)], i


def _show(x):
    """hwp2md 표기 → 읽는 꼴: 칸 안 줄바꿈 <br> 은 줄바꿈으로, 칸 구분 \\| 는 | 로(글자는 그대로)."""
    return x.replace("<br>", "\n").replace("\\|", "|")


def _norm(x):
    return re.sub(r"[\s|\\]+", "", x)


def _pdf_pages_for(quote, pdf_paths):
    """인용 글이 든 PDF 쪽(pypdf 기본 모드 글, 공백·「|」 무시). 줄마다 가운데 10자를 찾아 걸린 쪽을 모은다. 못 찾으면 ''."""
    out = []
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            continue
        P = [(n, _norm(t)) for n, t in _pages(open(pdf_text(pdf_path), encoding="utf-8").read())]
        hits = []
        for ln in _show(quote).split("\n"):
            ln = _norm(ln)
            if len(ln) < 10:
                continue
            k = (len(ln) - 10) // 2
            key = ln[k:k + 10]
            for n, t in P:
                if key in t:
                    if n not in hits:
                        hits.append(n)
                    break
        if hits:
            out.append("%s %s" % (_meta(pdf_path).get("원파일명", os.path.basename(pdf_path)),
                                  ",".join("p.%d" % n for n in sorted(hits))))
    return " ; ".join(out)


def _meta(path):
    with open(path + ".meta.json", encoding="utf-8") as f:
        return json.load(f)


def _press_rows():
    with open(os.path.join(WORK, "9-2-4_보도자료_받은글.csv"), encoding="utf-8-sig") as f:
        return {(("fss" if r["게시판"].startswith("금감원") else "fsc"), r["글번호"]): r for r in csv.DictReader(f)}


def _csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_press():
    rows = _press_rows()
    sl = _csv(SEARCH_CSV)
    fa = []
    for sub in ("press/view", "press/file", "press/search"):
        dd = os.path.join(D, sub)
        for x in os.listdir(dd):
            if x.endswith(".meta.json"):
                with open(os.path.join(dd, x), encoding="utf-8") as g:
                    fa.append(json.load(g)["fetched_at"])
    L = ["# 9-2-4 금감원·금융위 보도자료의 ORSA(자체위험 및 지급여력 평가) 도입 발표 — 원문 발췌", "",
         "- 작업: 13차 9-2-4(사용자 지시서 「9-2 ORSA 연혁과 보험 쪽 기준」 4번). 수집 %s ~ %s(KST, `.meta.json` 의 fetched_at — "
         "UTC 로는 %s). 스크립트 `scripts/dart/web13_fss.py`(policy → press-search → press-fetch → build)." % (min(fa), max(fa), TODAY),
         "- 출처: 금융감독원 보도자료 게시판(https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218)과 금융위원회 보도자료 게시판"
         "(https://www.fsc.go.kr/no010101). 원본(게시글 HTML·첨부 hwp/pdf)은 `dart_out/raw/web13/fss/press/`(git 무시)에 바이트 그대로 + `.meta.json`(sha256).",
         "- 수집 허용 확인: robots.txt — www.fss.or.kr 는 `User-agent : Yeti`(네이버) 묶음만 있어 우리 UA 에는 제한 없음, www.fsc.go.kr 는 "
         "`User-agent: * / Allow: /`(원본 `dart_out/raw/web13/fss/robots_*.txt`). 이용약관: 금감원 「저작권 정책」은 무단 복제·배포를 금하되 "
         "「보도·비평·교육·연구 등을 위하여는 정당한 범위 안에서 공정한 관행에 합치되게」 인용할 수 있다고 하고, 금융위 「저작권정책」은 "
         "「『저작권법』 제24조의2에 따라 금융위원회에서 저작재산권의 전부를 보유한 저작물의 경우에는 별도의 이용허락 없이 무료로 자유이용이 "
         "가능」하다고 한다. 두 곳 모두 자동 수집을 금지하는 문구는 없다(이메일 주소 무단수집 거부만 있음). 연구용으로 해당 문단만 옮기고 출처를 적는다. "
         "다만 금감원 정책은 「다른 인터넷 사이트에서 금융감독원 홈페이지의 저작물을 직접 링크하는 경우 링크사실을 금융감독원에게 반드시 통지하여야 합니다」라고 "
         "한다 — 이 md 의 URL 은 출처 표기용이며, 웹에 게시할 때는 이 문구를 고려해야 한다(판단).",
         "- 접속: www.fsc.go.kr 는 이 환경에서 TLS 접속이 간헐적으로 끊겼다(2026-10-07 15:01 UTC 무렵 3회 연속 실패 → 몇 분 뒤 정상). "
         "스크립트는 접속 실패 때 30·60초 쉬고 다시 시도하며, 로그인·캡차·차단 화면은 나오지 않았다. 요청 기록 `dart_out/risk13/9-2-4_9-5_요청기록.csv`.",
         "- 옮긴 방식: 첨부 hwp 를 `scripts/dart/hwp2md.py`(수정 없이, `python -I`)로 글로 바꾼 뒤 아래 시작·끝 표지 사이를 **글자 그대로** 잘라 왔다. "
         "hwp2md 표기 가운데 표 칸 안 줄바꿈 `<br>` 은 줄바꿈으로, 칸 구분 `\\|` 는 `|` 로만 바꿔 보였다(글자 수정 없음). "
         "hwp 가 없는 별첨(슬라이드 PDF)은 pypdf 글(기본 모드 + 띄어쓰기가 빠진 줄은 layout 모드 같은 글자열로 바꿈 — 9-5 md 머리의 설명과 같음)에서 잘라 왔다.",
         "- 쪽: 인용마다 같은 게시글의 PDF 첨부에서 그 글이 든 쪽을 찾아 적었다(공백 무시 대조). 금감원·금융위가 같은 자료를 함께 올린 경우 "
         "두 게시판의 hwp 글은 hwp2md 결과가 글자 하나 다르지 않았다(대조 결과는 각 항목에).",
         "- 한계: 사이트 게시판 검색(제목+내용)은 게시글 본문 칸만 찾고 첨부 파일 안은 찾지 않는다. 그래서 K-ICS·감독규정 개정 등 관련 보도자료 "
         "(아래 「받아 보았으나 ORSA 낱말 없음」)는 첨부를 받아 ORSA 낱말이 있는지 따로 보았다. 그 밖의 보도자료에 ORSA 언급이 더 있을 수 있다 — "
         "「추출 범위에 없음」은 아래 검색 범위 안에서의 결과다. 보험업감독규정 제7-5조·세칙 제5-6조의2·별표37 의 개정 연혁 자체는 9-2(법령) 산출물 "
         "`handoff/13차_산출물/9-2_ORSA_보험기준.md` 몫이다.",
         "- 모범규준 조 번호: 사용자 지시서가 9-2 에 조 번호를 적지 않았으므로 아래 조 번호는 모두 「(판단)」이다. 대응 근거는 「금융지주회사 통합위험관리 "
         "모범규준」(2017.4.1판) 조 제목 — 9-4 작업이 받은 원본 `%s`(읽기만 함)." % MOBEOM,
         "", "## 1. 날짜순 목록", "",
         "| # | 날짜(배포) | 자료 | 게시판·글번호 | ORSA 관련 내용(note: 요약 — 판단) | 모범규준 조(판단) |", "|---|---|---|---|---|---|"]
    summ = {
        "Q1": ("2014-07-31", "질적규제 체계(ORSA) 도입 추진 발표. 추진일정 '14년 방안 → 시범운영 '15~'16 → '17 시행", "제5장(36~49)"),
        "Q2": ("2016-03-30", "보험업법령(시행령·감독규정·세칙) 개정 — 자체 위험 및 지급여력 평가제도 도입, 시행일 '17.1.1", "제5장(36~49)"),
        "Q3": ("2017-06-28", "추진 경과 상자에 「보험회사 내부 자본적정성 평가(ORSA) 제도 : '16년 도입」", "—"),
        "Q4": ("2018-07-31 배포, 08-01 보도", "「'17년 ORSA 제도 시행」 — 내부모형 승인제도 필요성", "37·44"),
        "Q5": ("2018-12-12 배포, 12-13 보도", "'17년 도입·시행, 이사회 승인으로 시행 유예 가능(53개사 중 42개사 유예), 운영실태 평가·공표 계획", "36·37·39·41"),
        "Q6": ("2023-03-22", "감독방향: 기후리스크의 ORSA 반영 검토, 회사 규모별 ORSA 평가기준 차등화", "36"),
        "Q7": ("2024-11-05 배포, 11-06 보도", "K-ICS 내부모형 승인 평가기준에 ORSA 운영 여부(미운영사는 적용일까지 운영 조건)", "—"),
        "Q8": ("2026-03-11", "업무설명회: ORSA 도입 확대 방안, ORSA 보고서 작성 요구", "—"),
        "Q9": ("2026-06-29 배포, 06-30 보도", "세칙 개정 시행 — ORSA 도입 의무화, 소형(수입보험료 5천억원 이하)·외국계 지점 유예 가능, '26.6월말 결산 원칙·일부 '26.12월말", "36·39·41"),
    }
    seen = []
    for q in PQ:
        if q[0] in seen:
            continue
        seen.append(q[0])
        boards = " · ".join("%s %s" % ("금감원" if s_ == "fss" else "금융위", n) for s_, n in q[1])
        d, sm, art = summ[q[0]]
        L.append("| %s | %s | %s | %s | note: %s | %s |" % (q[0], d, PQ_TITLE[q[0]].split(" ", 1)[1], boards, sm, art))
    L += ["", "## 2. 원문 발췌(날짜순)", ""]
    cur = None
    for q in PQ:
        qid, boards, fn, st, en, art, note = q
        if qid != cur:
            cur = qid
            L += ["### %s %s" % (qid, PQ_TITLE[qid]), ""]
            for s_, n in boards:
                r = rows[(s_, n)]
                L.append("- %s 게시글 %s — 제목 「%s」 · 등록일 %s · 담당부서 %s · 첨부 %s" % (
                    "금감원" if s_ == "fss" else "금융위", r["URL"], r["제목"], r["등록일"], r["담당부서"], r["첨부"]))
            # 두 게시판 hwp 글 대조
            if len(boards) == 2:
                a = [x for x in os.listdir(PF) if x.startswith("%s_%s_" % boards[0]) and x.endswith(".hwp.md")]
                b = [x for x in os.listdir(PF) if x.startswith("%s_%s_" % boards[1]) and x.endswith(".hwp.md")]
                if a and b:
                    same = open(os.path.join(PF, a[0]), encoding="utf-8").read() == open(os.path.join(PF, b[0]), encoding="utf-8").read()
                    L.append("- note: 두 게시판의 hwp 첨부(hwp2md 결과) 대조 — %s" % ("글자까지 같음" if same else "**다름** — 아래 인용은 첫 게시판 것"))
            L.append("")
        src = os.path.join(PF, fn)
        if fn.endswith(".pdf"):
            tp = pdf_merged(src)
            text = open(tp, encoding="utf-8").read()
            quote, i = _cut(text, st, en, fn)
            pg = re.findall(r"=== p\.(\d+) ===", text[:i])
            pages = "p.%s" % (pg[-1] if pg else "1")
            m = _meta(src)
            quote = re.sub(r"=== p\.\d+ ===[^\n]*\n", "", quote)
            shown = quote
        else:
            text = open(src, encoding="utf-8").read()
            quote, i = _cut(text, st, en, fn)
            m = _meta(src[:-3])
            shown = _show(quote)
            pdfs = sorted(os.path.join(PF, x) for x in os.listdir(PF) if x.endswith(".pdf") and
                          any(x.startswith("%s_%s_" % b) for b in boards))
            pages = _pdf_pages_for(quote, pdfs) if pdfs else ""
            pages = ("PDF 쪽: %s" % pages) if pages else ("(같은 게시글에 PDF 첨부 없음)" if not pdfs else "(PDF 쪽 대조 못 함 — pypdf 가 뽑은 PDF 글의 글자 순서·기호가 hwp 와 달라 공백 무시 대조 실패)")
        L.append("인용 — %s · 원파일 「%s」 · sha256 %s… · %s · 수집 %s" % (note, m.get("원파일명", ""), m["sha256"][:16], pages, m["fetched_at"]))
        if art:
            L.append("")
            L.append("note: 모범규준 대응 %s" % art)
        L += ["", "```text", shown.strip("\n"), "```", ""]
    # 2차
    L += ["## 3. 받아 보았으나 ORSA 낱말 없음(2차 확인 대상)", "",
          "첨부(pdf 가 있으면 pdf, 없으면 hwp)의 글에서 정규식 `%s` 로 찾았으나 걸리지 않은 보도자료. 「없음」이 아니라 이 정규식·이 첨부 범위의 "
          "결과다(추출 범위에 없음)." % ORSA_TERMS.pattern, "", "| 등록일 | 게시판 | 글번호 | 제목 | 받은 첨부 |", "|---|---|---|---|---|"]
    for k, r in sorted(rows.items(), key=lambda kv: kv[1]["등록일"]):
        if r["구분"] == "2차":
            L.append("| %s | %s | %s | %s | %s |" % (r["등록일"], r["게시판"], r["글번호"], r["제목"].replace("|", "｜"),
                                                  r["받은첨부"].replace("|", "｜")))
    L += ["", "## 4. 찾은 방법(검색기록)", "",
          "두 게시판에서 낱말마다 끝 쪽까지 받았다(넓은 낱말은 제목만). 결과 행 합집합은 `dart_out/risk13/9-2-4_보도자료_후보.csv`(%d건)." % len(
              _csv(CAND_CSV)), "", "| 게시판 | 낱말 | 검색구분 | 사이트 총건수 | 받은 행 | 비고 |", "|---|---|---|---|---|---|"]
    for r in sl:
        L.append("| %s | %s | %s | %s | %s | %s |" % (r["게시판"], r["낱말"], r["검색구분"], r["사이트총건수"], r["받은행"], r["비고"]))
    L += ["", "## 5. 원문과 다른 것·눈여겨볼 곳(note)", "",
          "- note: ORSA 「도입(시행) 시점」 표현이 자료마다 다르다 — 2014 로드맵 「‘17년 시행」(시범운영 '15~'16), 2016-03-30 시행일 표 "
          "「‘17.1.1일」, 2017-06-28 상자 「보험회사 내부 자본적정성 평가(ORSA) 제도 : '16년 도입」, 2018-12-12 「’17년부터 … 도입」·"
          "「‘17년 제도 시행」, 2026-06-29 「ORSA1) 제도(‘17년 도입)」·「국내에는 ’17년 시행되었으나」. 2017-06-28 의 「'16년 도입」만 다르다"
          "(감독규정 개정이 '16.4.1 시행된 것을 「도입」으로 쓴 것인지는 자료에 설명 없음 — 판단 보류).",
          "- note: 제도 이름이 자료마다 다르다 — 「자체 위험 및 지급여력 평가제도」(2014·2016), 「자체위험․지급여력평가제도」(2014 로드맵 표), "
          "「보험회사 내부 자본적정성 평가(ORSA) 제도」(2017), 「자체위험 및 지급여력 평가제도」(2018), 「자체위험 및 지급여력 평가체제」(2024·2026), "
          "첨부 파일명 「자체리스크관리기준(ORSA)운영」(2018). 지시서 표현 「자체 위험 및 지급여력 평가 체제」(감독규정 제7-5조 문구)와 띄어쓰기가 다른 곳이 있다.",
          "- note: 2016-03-30 자료는 개정 경과를 「보험업법 시행령 개정안(3.29일 국무회의 의결), 보험업감독규정(3.30일 금융위원회 의결), "
          "보험업감독업무시행세칙(3.30일 확정)」, 시행을 「4.1일부터」로 적는다 — 9-2-1(감독규정 제7-5조 연혁)·9-2-2(세칙 제5-6조의2) 판 목록과 대조할 곳.",
          "- note: 2026-06-29 자료의 적용 시기 표현이 두 곳에서 다르다 — 상자 「’26년 6월말 결산부터 … 일부 사항은 … ’26년 12월말부터」, "
          "Ⅲ 향후 계획 「’26년 2분기 결산시부터 … 일부 사항은 ’26년말부터」(뜻은 같아 보이나 글자가 다름). 세칙 부칙(9-2-2)과 대조할 곳.",
          "- note: 2026-06-29 자료는 사전예고 기간을 「‘26.4.8일~’26.5.18일간 진행(40일)」로 적는다. 이 예고를 알리는 별도 보도자료는 두 게시판 검색 범위에서 "
          "찾지 못했다(추출 범위에 없음 — 낱말 「보험업감독업무시행세칙」 제목 검색 금감원 3건·금융위 0건, 「ORSA」 제목+내용 검색 금감원 2건·금융위 4건).",
          "- note: 2014-07-31 자료는 금융위 게시판에는 hwp 만, 금감원 게시판에는 pdf·hwp 가 있다. 2018-12-12 금감원 게시글은 hwp 만 있다.",
          "- note: 세칙 제5-6조의2·별표37 의 신설·개정 시점(9-2 산출물 몫)에 맞춘 별도 보도자료는 위 검색 범위에서 2026-06-29 건 말고는 찾지 못했다"
          "(추출 범위에 없음 — 2016-03-30 자료가 「보험업감독업무시행세칙(3.30일 확정)」을 함께 적을 뿐 세칙 조문 번호는 적지 않음).",
          "- note: 2024-03 언론 보도(전자신문 「금감원, 보험사 '자체 위험평가' 개편…소형사 면제 가닥」, WebSearch 결과 제목)에 대응하는 금감원·금융위 보도자료는 "
          "위 검색 범위에서 찾지 못했다(추출 범위에 없음). 2024-02-28 「2024년 보험 부문 금융감독 업무설명회 개최」 첨부에도 ORSA 낱말이 없었다.",
          ""]
    with open(OUT_PRESS, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("→", OUT_PRESS, len("\n".join(L)))


# ── 9-5 판정(판단) ─────────────────────────────────────────────────────────
# 「리스크관련」: Y = 지적 주제가 모범규준(2017.4.1판) 3~58조 가운데 어느 조의 주제(위험관리 조직·한도·사전협의·보고·의사전달·
# 유형별 위험·적합성 검증·위험 전이·해외위험·내부자본·자본계획·위기관리)와 겹치는 것, 경계 = 보수·성과평가·내부통제·경영관리
# 지적 안에 리스크관리 요소가 일부 들어간 것, N = 지배구조(경영승계·이사회·사외이사)·보수·준법감시·감사·소비자보호·문서관리 등.
# 값: (판정, 모범규준 조(판단), 주제(판단)). 표에 없는 항목은 N. 모두 판단이다.
CLASS = {
    "20220429": {5: ("경계", "35", "자본비율 성과평가지표(KPI) 목표"), 6: ("Y", "14·20", "그룹 리스크 한도 관리"),
                 7: ("Y", "33·14", "자회사 공동투자 리스크(전이)"), 8: ("Y", "13", "지주 리스크관리 조직·인력"),
                 9: ("Y", "49", "자본계획·자본관리 절차"), 10: ("Y", "45", "자본공제항목(가용자본)"),
                 11: ("Y", "25", "자회사 유동성리스크"), 14: ("Y", "34", "국가리스크 분석"),
                 15: ("Y", "21·22", "신용·시장리스크 위험가중자산 산출"), 16: ("Y", "30~32·41", "측정모형 적합성 검증·제3자 점검"),
                 17: ("Y", "37~47", "그룹 내부자본적정성 관리체제"), 18: ("Y", "56", "통합위기상황분석"),
                 19: ("Y", "15·16", "자회사 사전협의·보고"), 20: ("Y", "55·57", "조기경보지표·비상조달계획"),
                 21: ("Y", "25", "유동성리스크 한도"), 22: ("Y", "21", "중복차주 자산건전성 분류(신용)")},
    "20220729": {8: ("Y", "17", "의사전달 공식문서"), 10: ("Y", "14·15", "자회사 리스크관리 점검·사전협의"),
                 11: ("Y", "22·30~32", "그룹 시장리스크 산출 정합성 검증"), 12: ("Y", "28·30~32", "리스크 측정 시스템 적합성 검증"),
                 13: ("Y", "34", "해외투자 사전검토"), 15: ("Y", "49", "중장기 자본계획"), 17: ("Y", "37~47", "내부자본적정성"),
                 18: ("Y", "56", "위기상황분석"), 25: ("Y", "21", "집합투자증권 위험가중치"), 26: ("Y", "25", "그룹 유동성리스크"),
                 27: ("Y", "26", "산업별 신용공여한도(편중)"), 28: ("Y", "12", "리스크관리집행위원회 구성")},
    "20221214": {4: ("Y", "49", "신종자본증권 발행 자본관리 계획"), 5: ("Y", "24", "금리리스크 관리 체계")},
    "20221223": {2: ("Y", "11", "위험관리책임자 성과평가"), 9: ("Y", "34", "해외투자 리스크관리"),
                 11: ("경계", "33·15", "공동투자 비공식 회의체(내부통제)"), 12: ("Y", "15·26", "대규모 투자 사전심의 기준(총익스포져)"),
                 13: ("Y", "15·16·6", "자회사 사전보고 대상·리스크 내규")},
    "20231013": {2: ("경계", "33·15·16", "그룹 내부거래 사전협의·보고"), 4: ("Y", "21", "중복차주 자산건전성·충당금"),
                 12: ("Y", "49·35", "자본적정성 목표·성과평가 반영"), 13: ("Y", "56·57", "비상조달계획·위기상황분석")},
    "20240520": {1: ("Y", "9", "그룹위험관리위원회 사외이사 전문성"), 3: ("Y", "49·56", "위기상황 대비 자본관리 계획"),
                 5: ("Y", "56", "통합 위기상황분석"), 7: ("경계", "33", "자회사 자금지원(신용공여)"),
                 8: ("Y", "제5장(37~49) 주제", "자본비율 산출 정확성 검증"), 14: ("Y", "25·9", "조건부자본증권 만기편중·위험관리위원회 심의")},
    "20240620": {2: ("Y", "21", "중복기업차주 자산건전성·충당금"), 3: ("Y", "21·26", "자회사 부동산 PF대출"),
                 4: ("Y", "56", "위기상황분석"), 5: ("Y", "57·25", "비상조달계획 자금조달 수단"),
                 7: ("Y", "33", "자회사 신용공여 사후관리"), 12: ("Y", "21", "신용평가등급-자산건전성 연계"),
                 13: ("Y", "21", "대손충당금 리스크요소")},
    "20240726": {4: ("Y", "11", "리스크관리책임자(CRO)·준법감시인 전문성"), 6: ("Y", "49", "전략적 자본계획"),
                 7: ("Y", "44·47", "그룹 내부자본 측정·한도"), 12: ("Y", "30~32·41", "내부자본 측정모형 적합성 검증"),
                 13: ("Y", "21·22", "신용·시장리스크 위험가중자산 산출"), 14: ("Y", "56", "통합위기상황분석")},
    "20241007": {1: ("경계", "17", "중앙회 요청의 비공식 전달·문서화")},
    "20241126": {1: ("Y", "56·26", "부동산 PF 스트레스테스트·그룹리스크관리위원회 보고"), 3: ("경계", "35", "성과지표에 리스크관리 지표")},
    "20250317": {2: ("Y", "49", "자본관리계획"), 3: ("Y", "21", "중복차주 자산건전성·충당금"),
                 4: ("Y", "37~47·56", "위기상황 대비 내부자본적정성"), 5: ("Y", "제5장(37~49) 주제", "자본비율 산출 정확성 검증"),
                 14: ("경계", "35", "임원 장기성과 건전성 지표"), 15: ("Y", "21", "위험가중자산(RWA) 관리"),
                 16: ("Y", "26·33·15", "그룹 공동투자 편중·사전협의")},
    "20250318": {2: ("Y", "17·15", "의사전달 공식문서·사전협의"), 3: ("Y", "15·18·19", "자회사 M&A 리스크 평가·보고"),
                 4: ("경계", "49", "목표 보통주자본비율 임의 변경"), 6: ("Y", "52~54·14·15", "그룹 위기대응체계·자회사 리스크관리 평가"),
                 7: ("Y", "제5장(37~49) 주제", "지주 자기자본비율 산출"), 8: ("Y", "26·20", "책임준공형 토지신탁"),
                 9: ("Y", "23", "운영리스크 손실사건"), 10: ("Y", "33·26", "그룹 공동투자"),
                 17: ("Y", "9·33", "자회사 출자·자금지원 리스크관리위원회 심의"), 18: ("Y", "제5장(37~49) 주제", "자본비율 산출체계"),
                 19: ("Y", "21·33", "공동투자 대손충당금"), 20: ("Y", "21", "충당금 미래경기전망"),
                 21: ("Y", "33", "자회사간 신용공여 담보비율")},
    "20250609": {1: ("Y", "21", "대손충당금 방법론 통할"), 2: ("Y", "26·20", "책임준공형 토지신탁"),
                 3: ("Y", "15·26·14", "자회사 리스크 사전협의·한도"), 5: ("Y", "15·33", "신종자본증권 인수 리스크관리부서 사전협의"),
                 6: ("Y", "57", "비상조달계획 자금조달 규모")},
    "20251208": {1: ("Y", "49", "자본계획"), 5: ("경계", "14", "자회사 리스크관리 실태평가 범위(②)"),
                 6: ("Y", "25", "자금조달·운용(유동성)"), 7: ("Y", "56", "통합위기상황분석 지표")},
    "20260723": {4: ("Y", "49", "자본관리계획"), 5: ("Y", "21", "자산건전성·대손충당금"), 6: ("Y", "33·26", "그룹 공동투자"),
                 7: ("경계", "33", "관계회사 금융상품·그룹 내부거래 사전검토"), 16: ("Y", "제5장(37~49) 주제", "자기자본비율 산출"),
                 17: ("Y", "제5장(37~49) 주제", "레버리지비율 산출"), 18: ("경계", "22", "Level3 공정가치 평가 통할"),
                 19: ("Y", "37~47·18~27", "내부자본·유형별 리스크 관리체계"), 20: ("경계", "33·49", "지분 상호보유 리스크 사전검토"),
                 21: ("Y", "17", "의사전달 공식문서"), 22: ("Y", "20", "전략적 투자주식 손실한도"),
                 23: ("Y", "15·16", "Sell-Down 사후관리·리스크관리집행위원회 보고"), 24: ("Y", "56", "통합위기상황분석"),
                 25: ("Y", "21·30~32", "신용리스크측정요소 적합성 검증"), 26: ("Y", "29", "리스크 데이터 검증"),
                 27: ("Y", "26", "신용공여한도")},
}
SANC_CLASS = {"202000208_1": {1: ("경계", "33·17", "펀드 위험 전이 정보 미전달(내부통제기준 마련의무)")}}
SHORT = [(r"케이비|KB", "KB금융지주"), (r"신한", "신한금융지주"), (r"하나", "하나금융지주"), (r"우리", "우리금융지주"),
         (r"농협", "NH농협금융지주"), (r"디지비|DGB|아이엠", "DGB금융지주(현 iM금융지주)"), (r"BNK", "BNK금융지주"),
         (r"JB", "JB금융지주"), (r"메리츠", "메리츠금융지주"), (r"한국투자", "한국투자금융지주")]


def short(name):
    for pat, nm in SHORT:
        if re.search(pat, name):
            return nm
    return name


def _mobeom_titles():
    if not os.path.exists(MOBEOM):
        return {}
    t = open(MOBEOM, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"제(\d+)조\s*\(([^)]{1,40})\)", t):
        out.setdefault(int(m.group(1)), m.group(2))
    return out


def _arts(spec):
    """「14·20」「30~32·41」 → [14, 20, 30, 31, 32, 41]. 「제5장(37~49) 주제」 → 37~49."""
    out = []
    spec = re.sub(r"제\d+장", "", spec)                                # 「제5장(37~49) 주제」의 장 번호는 조가 아님
    for part in re.findall(r"\d+~\d+|\d+", spec):
        if "~" in part:
            a, b = map(int, part.split("~"))
            out += list(range(a, b + 1))
        else:
            out.append(int(part))
    return out


def build_exam():
    titles = _mobeom_titles()
    allrows = _csv(IMPR_ALL_CSV)
    hold = [r for r in allrows if HOLD_RE.search(r["제재대상기관"])]
    sanc_rows_ = _csv(SANC_CSV)
    search_log = _csv(os.path.join(WORK, "9-5_검색기록.csv")) if os.path.exists(os.path.join(WORK, "9-5_검색기록.csv")) else []
    docs = []
    for r in sorted(hold, key=lambda x: x["제재조치요구일"]):
        ext = os.path.splitext(r["파일명"])[1].lower() or ".pdf"
        fp = os.path.join(D, "exam", "impr", "%s_%s_%s%s" % (r["제재조치요구일"], slug(r["제재대상기관"], 20), r["일련번호"], ext))
        mp = pdf_merged(fp)
        items = parse_items(mp)
        head, dec = head_info(mp)
        m = _meta(fp)
        from pypdf import PdfReader
        npg = len(PdfReader(fp).pages)
        cls = CLASS.get(r["제재조치요구일"], {})
        for k, it in enumerate(items, 1):
            it["판정"], it["조"], it["주제"] = cls.get(k, ("N", "", ""))
        docs.append(dict(row=r, path=fp, meta=m, items=items, head=head, dec=dec, npg=npg, 목록="금융회사 경영유의사항 등 공시",
                         key=r["제재조치요구일"], 지주=short(r["제재대상기관"]), merged=mp))
    sdocs = []
    for r in sanc_rows_:
        if not r.get("파일"):
            continue
        mp = pdf_merged(r["파일"])
        items = parse_items(mp)
        head, dec = head_info(mp)
        key = "%s_%s" % (r["examMgmtNo"], r["emOpenSeq"])
        cls = SANC_CLASS.get(key, {})
        for k, it in enumerate(items, 1):
            it["판정"], it["조"], it["주제"] = cls.get(k, ("N", "", ""))
        sdocs.append(dict(row=r, path=r["파일"], meta=_meta(r["파일"]), items=items, head=head, dec=dec, 목록="검사결과제재",
                          key=key, 지주=short(r["제재대상기관"]), merged=mp))
    # CSV
    cols = ["목록", "지주", "제재대상기관(목록)", "비은행지주", "제재조치요구일(목록)", "관련부서", "구분", "번호", "제목", "리스크관련(판단)",
            "모범규준_조(판단)", "주제(판단)", "쪽", "인용조문", "관련규정", "url", "파일", "sha256"]
    out = []
    for d in docs + sdocs:
        r = d["row"]
        for it in d["items"]:
            out.append({"목록": d["목록"], "지주": d["지주"], "제재대상기관(목록)": r["제재대상기관"],
                        "비은행지주": "Y" if NONBANK.search(r["제재대상기관"]) else "N",
                        "제재조치요구일(목록)": r["제재조치요구일"], "관련부서": r["관련부서"], "구분": it["구분"], "번호": it["번호"],
                        "제목": it["제목"], "리스크관련(판단)": it["판정"], "모범규준_조(판단)": it["조"], "주제(판단)": it["주제"],
                        "쪽": ",".join("p.%d" % x for x in it["쪽"]), "인용조문": " ; ".join(it["인용조문"]),
                        "관련규정": " ; ".join(it["관련규정"]), "url": d["meta"]["출처URL"], "파일": d["meta"].get("원파일명", ""),
                        "sha256": d["meta"]["sha256"]})
    write_csv(LIST_CSV, cols, out)
    # md
    def item_table(d):
        T = ["| # | 구분 | 번호 | 지적 제목 | 쪽 | 리스크관련(판단) | 모범규준 조(판단) | 주제(판단) |", "|---|---|---|---|---|---|---|---|"]
        for k, it in enumerate(d["items"], 1):
            T.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (k, it["구분"], it["번호"], it["제목"].replace("|", "｜"),
                     ",".join(str(x) for x in it["쪽"]), it["판정"], it["조"], it["주제"]))
        return T

    def doc_block(d, quote_all_risk=True):
        r, m = d["row"], d["meta"]
        B = ["### %s — 제재조치요구일 %s (%s)" % (d["지주"], r["제재조치요구일"], d["목록"]), "",
             "- 목록 칸: 제재대상기관 「%s」 · 제재조치요구일 %s · 관련부서 %s%s" % (r["제재대상기관"], r["제재조치요구일"], r["관련부서"],
                                                                 (" · 목록 일련번호 %s" % r.get("일련번호")) if r.get("일련번호") else ""),
             "- 문서: 「%s」 · %s · sha256 %s · 수집 %s%s" % (m.get("원파일명", ""), m["출처URL"], m["sha256"], m["fetched_at"],
                                                      (" · %d쪽" % d["npg"]) if d.get("npg") else ""),
             ]
        if d["목록"] == "검사결과제재":
            if r["기관제재"] or r["임원제재"] or r["직원제재"]:
                B.append("- 게시 화면: %s · 화면 칸 — 기관 「%s」 · 임원 「%s」 · 직원 「%s」" % (r["url"], r["기관제재"], r["임원제재"], r["직원제재"]))
            else:
                B.append("- 게시 화면: %s · 화면의 기관·임원·직원 제재대상 칸은 비어 있음(첨부 PDF 참조)" % r["url"])
        if d["dec"]:
            cnt = {}
            for it in d["items"]:
                kk = "경영유의사항" if "경영유의" in it["구분"] else "개선사항" if "개선" in it["구분"] else it["구분"]
                cnt[kk] = cnt.get(kk, 0) + 1
            ok = all(cnt.get(k) == v for k, v in d["dec"].items())
            B.append("- note: 조치내용 칸의 건수 %s ↔ 항목으로 나눈 수 %s — %s" % (d["dec"], cnt, "일치" if ok else "**불일치**"))
        B += ["", "문서 머리(조치내용) — 글자 그대로:", "", "```text", d["head"], "```", ""]
        B += item_table(d)
        B.append("")
        risk = [(k, it) for k, it in enumerate(d["items"], 1) if it["판정"] in ("Y", "경계")]
        if not risk:
            B += ["note: 이 문서에는 리스크관련(판단 Y·경계) 항목이 없다.", ""]
        for k, it in risk:
            B += ["#### [%d] %s %s %s — %s(판단) · 모범규준 %s조(판단) · %s" % (k, it["구분"], it["번호"], it["제목"], it["판정"],
                                                                     it["조"], ",".join("p.%d" % x for x in it["쪽"])), ""]
            B.append("- 근거로 든 조문(문서 글에서 「｢…｣ 제N조」 꼴로 뽑음): %s" % (" ; ".join(it["인용조문"]) or "문서 글에 조문 인용 없음"))
            if it["관련규정"]:
                B.append("- 문서의 「< 관련규정 >」 칸: %s" % " ; ".join(it["관련규정"]))
            arts = _arts(it["조"]) if it["조"] else []
            if arts and titles:
                B.append("- note: 모범규준 조 제목(2017.4.1판) — %s" % ", ".join("%d조(%s)" % (a, titles.get(a, "?")) for a in arts))
            B += ["", "```text", "\n".join(it["본문"]), "```", ""]
        return B

    nb = [d for d in docs if NONBANK.search(d["row"]["제재대상기관"])]
    bk = [d for d in docs if not NONBANK.search(d["row"]["제재대상기관"])]
    nitems = sum(len(d["items"]) for d in docs)
    ny = sum(1 for d in docs for it in d["items"] if it["판정"] == "Y")
    nk = sum(1 for d in docs for it in d["items"] if it["판정"] == "경계")
    first = min(d["meta"]["fetched_at"] for d in docs + sdocs)
    last = max(d["meta"]["fetched_at"] for d in docs + sdocs)
    L = ["# 9-5 금감원 검사결과 공개자료 — 금융지주회사 경영유의·개선사항(2022년 이후) 가운데 리스크관리 관련 지적", "",
         "- 작업: 13차 9-5(사용자 지시서 1·2번). 수집 %s ~ %s(KST, `.meta.json` 의 fetched_at). 스크립트 `scripts/dart/web13_fss.py`"
         "(policy → impr → sanc → review → build)." % (first, last),
         "- 출처(실제 메뉴): 금융감독원 > 검사·제재 > 경영유의사항 등 공시 > 「금융회사 경영유의사항 등 공시」"
         "(https://www.fss.or.kr/fss/job/openInfoImpr/list.do?menuNo=200483). 화면 안내문: 「비징계적 성격의 조치인 경영유의·개선사항('14.7월부터 공시)은 "
         "'16.6월 이전의 내역은 「검사결과제재」에, '16.6월(제재조치일 기준)부터 「경영유의사항 등 공시」에 공시하고 있습니다.」(검사결과제재 화면 "
         "「정보이용시 유의사항」, 원본 `dart_out/raw/web13/fss/probe/openInfo_list.html`). 참고로 같은 기간 「검사결과제재」(문책·과태료 등, "
         "https://www.fss.or.kr/fss/job/openInfo/list.do?menuNo=200476)의 금융지주 건도 받아 5절에 따로 적었다.",
         "- 범위: 제재조치요구일 %s ~ %s 의 **전체 목록**(검색어 없이 %s건)을 끝 쪽까지 받아, 제재대상기관 이름에 「지주」가 든 행 %d건을 골랐다"
         "(사이트의 금융회사명 검색 「지주」 결과와 같음 — 검색기록 6절). 지시서의 지주(KB·신한·하나·우리·NH농협·iM(DGB)·BNK·JB·메리츠·한국투자) 밖의 "
         "금융지주 건은 이 기간 목록에 없었다." % (SDATE, EDATE, len(allrows), len(hold)),
         "- 「공개일」: 게시판에는 공개(게시)일 칸이 없고 「제재조치요구일」만 있다. 아래 날짜는 모두 목록의 제재조치요구일이며, 문서 안 「조치일」 "
         "「제재조치일」「조치요구일」은 문서 머리 인용에 그대로 있다. 일부 파일 이름의 날짜(예: BNK 「230324_…」, JB 「20240628 …」)는 공개안 작성·게시 "
         "무렵으로 보이나 판단하지 않았다.",
         "- 원본: 공개안 PDF 는 `dart_out/raw/web13/fss/exam/`(git 무시)에 바이트 그대로 + `.meta.json`(sha256). PDF 는 배포하지 않고 글만 옮긴다.",
         "- PDF 글 뽑기(한계): pypdf %s 기본 모드는 공백 글자 없이 글자 간격으로 띄운 줄에서 띄어쓰기를 빠뜨린다. 그래서 (가) 공백 비율 6%% 미만·15자 이상인 줄, "
         "(나) layout 모드에서 같은 글자열의 공백이 2개 이상 많은 줄은 layout 모드의 같은 글자열 부분으로 바꿨다(`*.merged.txt`). 공백을 뺀 글자는 "
         "두 모드가 쪽마다 같음을 대조했다(다른 쪽 0). layout 모드는 글자 간격으로 띄어쓰기를 되살린 것이라 원문과 띄어쓰기가 다를 수 있고"
         "(예: 「｢금융지주회사법 ｣」처럼 낫표 앞 공백), 바꾸지 못한 줄은 띄어쓰기가 빠진 채 남아 있다. 쪽 번호 줄(「- N -」·숫자만 있는 줄)은 뺐다. "
         "표(조치내용 칸)는 칸 순서가 섞여 나올 수 있다 — 문서 머리 인용은 [표 깨짐 가능]으로 본다." % __import__("pypdf").__version__,
         "- 항목 나누기: 문서의 「가. 경영유의사항」「나. 개선사항」 등 구분 표지와 첫 항목 번호 꼴(「(1)」「1)」「⑴」「가.」)로 나눴다. "
         "경영유의 공시 18건 모두 조치내용 칸의 건수와 나눈 항목 수가 일치했다(문서마다 note). 비식별 기호(●·◇·▯·○ 등)는 공개안 원문 그대로다.",
         "- 판정 기준(판단): 「리스크관련」 Y = 지적 주제가 모범규준 3~58조 가운데 어느 조의 주제(위험관리 조직·위원회·책임자, 한도, 사전협의·보고·"
         "의사전달, 유형별 위험, 측정·적합성 검증, 그룹내 위험 전이, 해외위험, 내부자본 적정성·자본계획, 위기관리·위기상황분석·비상계획)와 겹치는 것 · "
         "경계 = 보수·성과평가·내부통제·경영관리 지적 안에 리스크관리 요소가 일부 들어간 것 · N = 지배구조(경영승계·이사회·사외이사)·보수·준법감시·감사·"
         "소비자보호·문서관리 등. 규제자본비율(BIS·레버리지) 산출 오류는 모범규준에 바로 대응하는 조가 없어 「제5장(37~49) 주제」로 적었다.",
         "- 모범규준 조 번호: 지시서가 9-5 에 조 번호를 주지 않았으므로 모두 「(판단)」. 조 제목은 「금융지주회사 통합위험관리 모범규준」 2017.4.1판 "
         "(9-4 작업이 받은 원본 `%s`, 읽기만 함; 2016.8.1판과 조 제목 같음)." % MOBEOM,
         "", "## 1. 요약", "",
         "경영유의사항 등 공시 — 금융지주 문서 %d건 · 지적 항목 %d개 · 리스크관련(판단) Y %d · 경계 %d · N %d." % (
             len(docs), nitems, ny, nk, nitems - ny - nk), "",
         "| 제재조치요구일 | 지주 | 비은행 | 관련부서 | 항목(경영유의/개선) | Y | 경계 | 원파일 |", "|---|---|---|---|---|---|---|---|"]
    for d in docs:
        c1 = sum(1 for it in d["items"] if "경영유의" in it["구분"])
        c2 = sum(1 for it in d["items"] if "개선" in it["구분"])
        L.append("| %s | %s | %s | %s | %d (%d/%d) | %d | %d | %s |" % (
            d["row"]["제재조치요구일"], d["지주"], "**비은행**" if NONBANK.search(d["row"]["제재대상기관"]) else "", d["row"]["관련부서"],
            len(d["items"]), c1, c2, sum(1 for it in d["items"] if it["판정"] == "Y"),
            sum(1 for it in d["items"] if it["판정"] == "경계"), d["meta"].get("원파일명", "")))
    L += ["", "## 2. 비은행지주(메리츠금융지주·한국투자금융지주) — 따로 표시", "",
          "경영유의사항 등 공시 목록(%s~%s)에서 비은행지주 건은 아래 %d건이다. 같은 기간 「검사결과제재」 목록의 두 지주 건은 5절." % (SDATE, EDATE, len(nb)), ""]
    for d in nb:
        L += doc_block(d)
    L += ["## 3. 은행지주 문서별(제재조치요구일 순)", ""]
    for d in bk:
        L += doc_block(d)
    # 색인
    L += ["## 4. 모범규준 조 번호별 색인(판단)", "", "01 엑셀판 「주제1_모범규준기준」 시트의 조 행에 넣을 때 쓰는 색인. 조 번호는 모두 판단.", "",
          "| 모범규준 조 | 조 제목(2017.4.1판) | 지적(지주 · 제재조치요구일 · 번호 · 제목 · 판정) |", "|---|---|---|"]
    idx = {}
    for d in docs + sdocs:
        for k, it in enumerate(d["items"], 1):
            if it["판정"] == "N" or not it["조"]:
                continue
            keys = []                                                   # 범위(「37~47」)는 첫 조 행에 한 번만, 「제5장 주제」는 따로
            if "제5장" in it["조"]:
                keys.append(99)
            for part in re.findall(r"\d+~\d+|\d+", re.sub(r"제\d+장\([^)]*\)", "", it["조"])):
                keys.append(int(part.split("~")[0]))
            for a in sorted(set(keys)):
                idx.setdefault(a, []).append("%s %s %s %s 「%s」(%s)" % (d["지주"], d["row"]["제재조치요구일"], it["구분"], it["번호"],
                                                                        it["제목"], it["판정"]))
    for a in sorted(idx):
        if a == 99:
            L.append("| 제5장(37~49) 주제 | 내부자본 적정성 평가 및 관리(특정 조 없음 — 규제자본비율 산출 등) | %s |" % "<br>".join(idx[a]))
        else:
            L.append("| %d조 | %s | %s |" % (a, titles.get(a, ""), "<br>".join(idx[a])))
    L += ["", "note: 범위로 적은 판정(예: 「37~47」「30~32」「52~54」)은 범위의 첫 조 행에만 넣었다 — 그 조 하나가 아니라 범위 전체에 닿는다는 뜻(판단)."]
    covered = set()
    for d in docs + sdocs:
        for it in d["items"]:
            if it["판정"] != "N" and it["조"]:
                covered |= set(_arts(it["조"]))
    none = [a for a in range(3, 59) if a not in covered]
    L += ["", "note: 위 판정에서 어느 지적도 닿지 않은 조(판단): %s. 「없음」이 아니라 이 18건 공개안 범위의 결과다(추출 범위에 없음)." % ", ".join(
        "%d조(%s)" % (a, titles.get(a, "")) for a in none), ""]
    # 검사결과제재
    L += ["## 5. 참고: 검사결과제재(문책·과태료 등) 가운데 금융지주 건", "",
          "경영유의·개선사항은 아니지만 같은 검사에서 함께 나온 제재다. 금융회사명 검색 「지주」, %s~%s, %d건. 리스크관련(판단) 경계 1건만 본문을 옮긴다." % (
              SDATE, EDATE, len(sdocs)), "",
          "| 제재조치요구일 | 지주 | 비은행 | 항목(번호 · 제목 · 판정) | 원파일 |", "|---|---|---|---|---|"]
    for d in sdocs:
        L.append("| %s | %s | %s | %s | %s |" % (d["row"]["제재조치요구일"], d["지주"],
                 "**비은행**" if NONBANK.search(d["row"]["제재대상기관"]) else "",
                 "<br>".join("%s %s(%s)" % (it["번호"], it["제목"], it["판정"]) for it in d["items"]), d["meta"].get("원파일명", "")))
    L.append("")
    for d in sdocs:
        if any(it["판정"] != "N" for it in d["items"]):
            L += doc_block(d)
    # 검색기록
    L += ["## 6. 찾은 방법(검색기록)", "", "| 목록 | 질의 | 사이트 총건수 | 받은 행 | 쪽수 | 비고 |", "|---|---|---|---|---|---|"]
    for r in search_log:
        L.append("| %s | %s | %s | %s | %s | %s |" % tuple(r.get(k, "") for k in ["목록", "질의", "사이트총건수", "받은행", "쪽수", "비고"]))
    L += ["",
          "- 전체 목록 CSV: `dart_out/risk13/9-5_경영유의공시_전체목록.csv`(%d행). 항목별 목록: `dart_out/risk13/9-5_검사결과_목록.csv`(%d행 — 경영유의 공시 "
          "%d + 검사결과제재 %d)." % (len(allrows), len(out), nitems, len(out) - nitems),
          "- 이름 확인: 전체 목록에서 「아이엠」「iM」은 아이엠증권(2025-09-26)만, 「DGB」「디지비」는 디지비금융지주(2022-04-29)·DGB생명보험(2023-05-26)만 "
          "나온다 — iM금융지주(2024년 사명 변경) 이름의 경영유의 공시는 이 기간 목록에 없다(추출 범위에 없음). 메리츠·한국투자 계열은 지주 외에 증권·화재·"
          "저축은행·운용·신탁 건이 있으나 지주가 아니어서 넣지 않았다.",
          "- 요청: robots.txt(www.fss.or.kr — 우리 UA 제한 없음) 확인 뒤 web13.Web(1.2초 간격)으로 받았다. 로그인·캡차·차단 화면 없음. "
          "요청 기록 `dart_out/risk13/9-2-4_9-5_요청기록.csv`.",
          "- 금감원 「저작권 정책」: 「보도·비평·교육·연구 등을 위하여는 정당한 범위 안에서 공정한 관행에 합치되게 본 사이트의 자료들을 인용할 수 있습니다」"
          "(원본 `dart_out/raw/web13/fss/policy/저작권정책.html`). 자동 수집 금지 문구 없음. 같은 정책의 「다른 인터넷 사이트에서 금융감독원 홈페이지의 "
          "저작물을 직접 링크하는 경우 링크사실을 금융감독원에게 반드시 통지하여야 합니다」 — 이 md 의 URL 은 출처 표기용(웹 게시 때 유의, 판단).", ""]
    with open(OUT_EXAM, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("→", OUT_EXAM, len("\n".join(L)), "· CSV", LIST_CSV, len(out), "· Y", ny, "경계", nk, "/", nitems)


def build():
    build_press()
    build_exam()


def verify():
    """산출 md 의 코드 블록(원문 인용)마다 공백을 뺀 글자열이 원본 텍스트(pypdf 기본 모드 글 또는 hwp2md 글)의 공백 뺀 글자열 안에
    그대로 있는지 대조한다(쪽 표지·쪽 번호 줄은 원본에서도 뺀다). 하나라도 없으면 멈춘다. 인증값 문자열이 들어 있지 않은지도 본다."""
    def ns(x):
        return re.sub(r"\s+", "", x)

    def plain_pdf(path):
        t = open(pdf_text(path), encoding="utf-8").read()
        lines = [x for x in t.split("\n") if not re.match(r"=== p\.\d+ ===", x) and not FOOT_RE.match(x.strip())]
        return ns("\n".join(lines))

    def hwp(path):
        return ns(open(path, encoding="utf-8").read().replace("<br>", "\n").replace("\\|", "|"))

    srcs = []
    for sub in ("exam/impr", "exam/sanc", "press/file"):
        dd = os.path.join(D, sub)
        for x in sorted(os.listdir(dd)):
            fp = os.path.join(dd, x)
            if x.endswith(".pdf"):
                srcs.append(plain_pdf(fp))
            elif x.endswith(".hwp.md"):
                srcs.append(hwp(fp))
    bad = 0
    for md in (OUT_PRESS, OUT_EXAM):
        t = open(md, encoding="utf-8").read()
        blocks = re.findall(r"```text\n(.*?)\n```", t, re.S)
        ok = 0
        for b in blocks:
            k = ns(b)
            if any(k in x for x in srcs):
                ok += 1
            else:
                bad += 1
                print("  ! 원본에서 못 찾음(%s): %r" % (os.path.basename(md), b[:120]))
        print("%s: 인용 블록 %d개 중 원본 대조 일치 %d" % (md, len(blocks), ok))
        for pat in (r"OC=(?!\*\*\*)[A-Za-z0-9]", r"crtfc_key=[0-9a-f]{20,}", r"DART_API_KEY\s*=\s*\w{10,}"):
            if re.search(pat, t):
                bad += 1
                print("  ! 인증값 꼴 문자열:", pat)
    if bad:
        raise SystemExit("verify 실패 %d" % bad)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    fn = {"policy": policy, "press-search": press_search, "press-fetch": press_fetch, "impr": impr, "sanc": sanc, "review": review, "build-press": build_press, "build-exam": build_exam, "build": build, "verify": verify}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    try:
        fn()
    finally:
        flush_log()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
