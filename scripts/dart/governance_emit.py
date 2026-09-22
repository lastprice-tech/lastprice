# -*- coding: utf-8 -*-
"""6차 — 지배구조·보수체계 연차보고서 PDF 에서 텍스트·섹션·표·주제를 뽑는다.

1~5차와 같은 규율: raw/ 만 읽는 순수 함수이고 네트워크·API 키를 쓰지 않는다.
못 뽑은 것은 빈칸 + 사유이고 지어내지 않는다.

■ DART 원문과 다른 점 하나를 먼저 적어 둔다
  DART 원문은 XML 이라 표의 행·열·rowspan/colspan 을 **문서가 선언한다**. PDF 에는
  그런 선언이 없다 — 글자와 좌표만 있다. 그래서 표의 셀은 좌표 군집으로 세울 수밖에
  없고, 그것은 1~5차에서 금지한 '격자 추론' 과 성격이 같다. 숨기지 않는다:
  추출방법 컬럼에 `좌표군집` 을 적고 x·y 를 그대로 실어 사람이 되짚을 수 있게 한다.
  rowspan/colspan 은 **빈칸**이다(모르는 것을 1 로 적지 않는다).

■ 섹션은 문서가 선언한 목차를 쓴다
  연차보고서는 법정 양식이라 앞쪽에 목차 페이지가 있다. 목차의 제목을 **원문 그대로**
  들고 본문에서 그 줄을 찾아 경계를 잡는다. 목차의 쪽 번호는 쓰지 않는다 — 인쇄 쪽과
  PDF 인덱스의 차이가 문서마다 달라서(메리츠 2025 는 +1) 어긋나기 때문이다.
  못 찾은 항목은 버리지 않고 `본문위치=미발견` 으로 남긴다.
"""
from __future__ import annotations

import collections
import csv
import glob
import hashlib
import json
import os
import re
import sys

csv.field_size_limit(10 ** 9)

try:
    import pypdf
except ImportError:                      # openpyxl 과 같은 취급 — 없으면 사유를 남긴다
    pypdf = None

OUT = "dart_out"
RAW_SUB = os.path.join("raw", "governance")
TEXT_SUB = os.path.join("text", "governance")

# 셀 한 칸 32,767자 상한(엑셀)과 같은 규율. 자르지 않고 나눈다.
CHUNK = 30000


# ── 목차 ──────────────────────────────────────────────────────────────────
# 「제1절  지배구조 연차보고서 ......... 8」 / 「가. 지배구조 원칙과 정책   8」
#
# **줄 단위로 고정하면 안 된다.** JB금융지주 목차는 2단 조판이라 한 줄에 좌·우
# 항목이 같이 있다("가. 지배구조 원칙과 정책 ·····6   라. 최고경영자 후보추천 ···146").
# ^...$ 로 묶으면 그 줄 전체가 항목 하나로 잡혀 제목이 통째로 망가진다(실측: JB
# 304쪽 문서가 목차 3항목·본문 발견 0). 그래서 줄에 고정하지 않고 **항목 단위로**
# 훑는다. 리더 문자는 회사마다 다르다 — 메리츠는 공백, BNK 는 ‥(U+2025), JB 는 ·.
_LEAD = r"[\s.·…‥ㆍ∙•∙·_\-]"
_TOC_ITEM = re.compile(
    r"(제\s*\d+\s*절|\d+\.|[가-힣]\.|\d+\)|[①-⑳]|[IVXivx]+\.)\s*"
    r"([^\n]{2,60}?)" + _LEAD + r"{3,}(\d{1,4})(?=\s|$)")
_TOC_HINT = re.compile(r"목\s*차|CONTENTS|Contents")
_LEADER_TAIL = re.compile(_LEAD + r"+$")


def _clean_title(s):
    return _LEADER_TAIL.sub("", re.sub(r"\s+", " ", s or "").strip()).strip()


def _norm(s):
    return re.sub(r"\s+", "", s or "")


def parse_toc(pages_text, max_scan=14, min_items=5):
    """앞쪽 페이지에서 목차 항목을 뽑는다. [(번호, 제목_원문, 목차쪽, 목차PDF인덱스)].

    한 쪽에서 min_items 개 이상 잡히거나, 「목차」·CONTENTS 표기가 있으면 목차 쪽으로 본다.
    """
    items, toc_pages = [], []
    for i, t in enumerate(pages_text[:max_scan]):
        hits = list(_TOC_ITEM.finditer(t))
        if len(hits) >= min_items or (_TOC_HINT.search(t) and hits):
            toc_pages.append(i)
            for m in hits:
                title = _clean_title(m.group(2))
                if title and not title.isdigit():
                    items.append((re.sub(r"\s+", " ", m.group(1)).strip(),
                                  title, m.group(3), i))
    return items, toc_pages


# 본문 표제 직접 검출. 목차를 기계가 못 읽는 문서용 2단계 폴백이다.
# NH농협금융지주는 목차 쪽이 이미지라 텍스트가 0자다(본문은 42.9만 자로 멀쩡하다).
# 표제는 번호 + 짧은 제목이고, 끝에 쪽 번호가 붙지 않는다는 점으로 목차 줄과 갈린다.
_BODY_HEAD = re.compile(
    r"^[ \t]*(제\s*\d+\s*절|\d{1,2}\.|[가-힣]\.|\d{1,2}\)|[①-⑳])[ \t]*"
    r"([^\s\d][^\n]{1,38}?)[ \t]*$", re.M)


def detect_body_headings(pages_text, start_page=0):
    """[(번호, 제목_원문, 쪽, 줄)]. 목차가 없을 때만 쓴다."""
    out = []
    for pi in range(start_page, len(pages_text)):
        lines = pages_text[pi].split("\n")
        for li, line in enumerate(lines):
            m = _BODY_HEAD.match(line)
            if not m:
                continue
            title = _clean_title(m.group(2))
            # 숫자만 많은 줄(표의 한 행)과 리더가 남은 줄은 표제가 아니다.
            if not title or sum(c.isdigit() for c in title) > len(title) / 3:
                continue
            out.append((re.sub(r"\s+", " ", m.group(1)).strip(), title, pi, li))
    return out


def locate_sections(toc, pages_text, start_page):
    """목차 제목을 본문에서 순서대로 찾는다. 쪽 번호는 쓰지 않는다.

    반환: [(번호, 제목_원문, 발견PDF인덱스 또는 -1, 줄번호 또는 -1)]
    """
    out = []
    p, ln = start_page, 0
    for num, title, _pg, _tp in toc:
        key = _norm(num) + _norm(title)
        found = (-1, -1)
        pp, ll = p, ln
        while pp < len(pages_text):
            lines = pages_text[pp].split("\n")
            for j in range(ll, len(lines)):
                if _norm(lines[j]).startswith(key):
                    found = (pp, j)
                    break
            if found[0] >= 0:
                break
            pp, ll = pp + 1, 0
        if found[0] >= 0:
            p, ln = found[0], found[1] + 1
        out.append((num, title, found[0], found[1]))
    return out


def section_bodies(located, pages_text):
    """각 섹션의 본문. 다음으로 **발견된** 섹션의 시작 직전까지."""
    pos = [(i, p, l) for i, (_n, _t, p, l) in enumerate(located) if p >= 0]
    bodies = {}
    for k, (i, p, l) in enumerate(pos):
        if k + 1 < len(pos):
            ep, el = pos[k + 1][1], pos[k + 1][2]
        else:
            ep, el = len(pages_text) - 1, None
        buf = []
        for pg in range(p, ep + 1):
            lines = pages_text[pg].split("\n")
            a = l if pg == p else 0
            b = el if (pg == ep and el is not None) else len(lines)
            buf.extend(lines[a:b])
        bodies[i] = "\n".join(buf).strip()
    return bodies


# ── 표(좌표 군집) ─────────────────────────────────────────────────────────
def page_words(page):
    """(x, y, 글자) 목록. pypdf 의 visitor 로 텍스트 매트릭스 좌표를 그대로 받는다."""
    words = []

    def visit(text, _cm, tm, _fd, _fs):
        t = (text or "").strip()
        if t and len(tm) >= 6:
            words.append((round(float(tm[4]), 1), round(float(tm[5]), 1), t))
    try:
        page.extract_text(visitor_text=visit)
    except Exception:                    # noqa: BLE001 — 한 쪽이 깨져도 문서를 버리지 않는다
        return []
    return words


def cluster_rows(words, ytol=2.5):
    rows = []
    for x, y, t in sorted(words, key=lambda w: (-w[1], w[0])):
        if rows and abs(rows[-1][0] - y) <= ytol:
            rows[-1][1].append((x, t))
        else:
            rows.append([y, [(x, t)]])
    for r in rows:
        r[1].sort()
    return rows


def merge_cells(row_cells, xgap=6.0):
    """같은 줄에서 x 간격이 벌어지는 지점을 칸 경계로 본다."""
    out = []
    for x, t in row_cells:
        if out and x - out[-1][1] <= xgap:
            out[-1][2] += t
            out[-1][1] = x + len(t) * 4.0
        else:
            out.append([x, x + len(t) * 4.0, t])
    return [(round(c[0], 1), c[2].strip()) for c in out if c[2].strip()]


def detect_tables(pages, min_cols=3, min_rows=2):
    """연속한 다칸 줄을 한 표로 묶는다. [(시작쪽, [ [(x, 셀), ...], ... ])]"""
    tables = []
    for pi, page in enumerate(pages):
        rows = cluster_rows(page_words(page))
        cur = []
        for _y, cells in rows:
            merged = merge_cells(cells)
            if len(merged) >= min_cols:
                cur.append(merged)
            else:
                if len(cur) >= min_rows:
                    tables.append((pi, cur))
                cur = []
        if len(cur) >= min_rows:
            tables.append((pi, cur))
    return tables


# ── 주제 ──────────────────────────────────────────────────────────────────
# 요청서 4절의 9개 주제. 낱말은 **찾기용**이고, 실리는 것은 원문 문장 그대로다.
TOPICS = (
    ("이사회 구성", ("사외이사", "사내이사", "기타비상무이사", "이사회 의장",
                     "이사회의 구성", "전문분야", "이사 총수")),
    ("이사회 내 위원회", ("위원회", "감사위원회", "보수위원회", "위험관리위원회",
                          "임원후보추천", "개최", "안건")),
    ("최고경영자 경영승계", ("경영승계", "승계", "후보군", "CEO", "최고경영자",
                             "자격요건", "자격 요건", "경영승계규정")),
    ("보수체계", ("성과보수", "이연", "환수", "clawback", "말우스", "보수위원회",
                  "고정보수", "변동보수", "지급률")),
    ("임원 겸직", ("겸직", "겸임", "겸영")),
    ("부서 단위 겸직", ("겸)", "(겸)", "겸직 부서", "겸영 부서", "공동 운영", "겸직부서")),
    ("내부통제·책무구조도", ("책무구조도", "내부통제", "책무", "준법감시", "내부통제위원회")),
    ("고객정보·데이터 조직", ("고객정보관리인", "개인정보보호책임자", "데이터 거버넌스",
                              "데이터거버넌스", "CPO", "정보보호최고책임자", "CISO")),
    ("지주 인원·부문업무", ("임직원", "직원 수", "인원", "부문", "부서", "조직",
                            "정원", "담당업무")),
)
_SENT = re.compile(r"[^.。\n]{10,400}[.。]")


def topic_hits(title, body, names):
    out = []
    for m in _SENT.finditer(body):
        s = m.group(0).strip()
        if any(k in s for k in names):
            out.append(s)
    if not out and any(k in title for k in names):
        out.append("(섹션 제목만 일치: %s)" % title)
    return out


# ── 산출 ──────────────────────────────────────────────────────────────────
FILE_COLS = ["지주명", "공시연도", "공시유형", "구분", "제목", "파일명", "방식",
             "다운로드성공", "실패사유", "목록크기", "실제크기", "크기차이",
             "페이지수", "텍스트추출", "텍스트글자수", "스캔본추정", "목차항목수",
             "본문발견섹션수", "섹션출처", "목차없음", "표수", "sha256", "url", "fetched_at"]

SEC_COLS = ["지주명", "공시연도", "공시유형", "파일명", "섹션출처", "섹션번호", "섹션순번",
            "섹션제목_원문", "본문위치", "시작페이지", "chunk_seq", "본문글자수",
            "본문", "text_path", "sha256"]

TBL_COLS = ["corp_label", "rcept_no", "rcept_dt", "doc_kind", "doc_purpose",
            "section_index", "section_title", "section_title_raw",
            "table_index", "table_matched_keyword",
            "table_extracted", "table_n_rows",
            "row_index", "cell_ord", "cell_tag", "rowspan", "colspan",
            "unit_hint", "unit_hint_source", "cell_text", "fetched_at", "status",
            "raw_path", "raw_sha256",
            # PDF 에만 있는 것. 앞 24칸은 1~5차와 같고 뒤에 덧붙인다.
            "원천", "페이지", "cell_x", "추출방법"]

TOPIC_COLS = ["지주명", "공시연도", "공시유형", "파일명", "주제", "추출결과",
              "섹션번호", "섹션제목_원문", "원문", "출처페이지", "sha256"]


def _chunks(s, n=CHUNK):
    if not s:
        return [""]
    return [s[i:i + n] for i in range(0, len(s), n)] or [""]


def process(meta, out_dir, verbose=True):
    path = meta["_path"]
    name = meta["저장파일명"]
    rec = {
        "지주명": meta["지주명"], "공시연도": meta.get("공시연도", ""),
        "공시유형": meta.get("공시유형", ""), "구분": meta.get("구분", ""),
        "제목": meta.get("제목", ""), "파일명": name, "방식": meta.get("방식", ""),
        "다운로드성공": meta.get("성공", ""), "실패사유": meta.get("실패사유", ""),
        "목록크기": meta.get("목록크기", ""), "실제크기": meta.get("실제크기", ""),
        "크기차이": meta.get("크기차이", ""), "sha256": meta.get("sha256", ""),
        "url": meta.get("url", ""), "fetched_at": meta.get("fetched_at", ""),
        "페이지수": "", "텍스트추출": "N", "텍스트글자수": "", "스캔본추정": "",
        "목차항목수": "", "본문발견섹션수": "", "섹션출처": "", "목차없음": "N", "표수": "",
    }
    secs, tbls, tops = [], [], []
    if not name.lower().endswith(".pdf") or meta.get("성공") != "Y":
        rec["텍스트추출"] = "-"
        return rec, secs, tbls, tops
    if pypdf is None:
        rec["실패사유"] = "pypdf 없음 — `pip install pypdf` 후 다시 실행"
        return rec, secs, tbls, tops
    try:
        reader = pypdf.PdfReader(path)
        pages = reader.pages
        rec["페이지수"] = str(len(pages))
        ptext = []
        for pg in pages:
            try:
                ptext.append(pg.extract_text(extraction_mode="layout") or "")
            except Exception:                 # noqa: BLE001
                try:
                    ptext.append(pg.extract_text() or "")
                except Exception:             # noqa: BLE001
                    ptext.append("")
    except Exception as e:                    # noqa: BLE001
        rec["실패사유"] = "PDF 열기 실패: %s: %s" % (type(e).__name__, e)
        return rec, secs, tbls, tops

    full = "\n".join(ptext)
    rec["텍스트글자수"] = str(len(full))
    rec["텍스트추출"] = "Y" if full.strip() else "N"
    # 스캔본은 쪽당 글자가 극단적으로 적다. 판정이 아니라 '추정' 이라고 적는다.
    per = len(full) / max(1, len(ptext))
    rec["스캔본추정"] = "Y" if per < 60 else "N"

    tp = os.path.join(out_dir, TEXT_SUB, name + ".txt")
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    with open(tp, "w", encoding="utf-8") as f:
        f.write(full)

    toc, toc_pages = parse_toc(ptext)
    rec["목차항목수"] = str(len(toc))
    start = (max(toc_pages) + 1) if toc_pages else 0
    located = locate_sections(toc, ptext, start)
    found = sum(1 for _n, _t, p, _l in located if p >= 0)
    rec["섹션출처"] = "목차"
    # 목차를 기계가 못 읽거나(NH농협: 목차 쪽이 이미지) 목차 제목이 본문과 어긋나
    # 절반도 못 찾으면(JB 정정공시) 본문 표제를 직접 찾는다. 어느 방식으로 나눴는지
    # 를 섹션출처 컬럼에 남긴다 — 방법이 다르면 결과도 다르게 읽어야 한다.
    if not toc or found < max(3, len(located) * 0.5):
        alt = detect_body_headings(ptext, start)
        if len(alt) > found:
            located = [(n, t, p, l) for n, t, p, l in alt]
            rec["섹션출처"] = "본문표제"
            found = len(alt)
    bodies = section_bodies(located, ptext)
    rec["본문발견섹션수"] = str(found)
    # 목차가 없는 짧은 문서(예: BNK 보수체계 연차보고서 6쪽)는 섹션이 0이 된다.
    # 그대로 두면 본문이 통째로 산출물에서 사라진다 — 그건 삭제다. 문서 전체를
    # 한 섹션으로 싣고, 제목 자리에 '목차 없음' 이라는 **사실**을 적는다.
    if not any(p >= 0 for _n, _t, p, _l in located):
        located = [("", "(목차 없음 — 문서 전체)", 0, 0)]
        bodies = {0: full}
        rec["본문발견섹션수"] = "1"
        rec["목차없음"] = "Y"

    base = dict(지주명=rec["지주명"], 공시연도=rec["공시연도"],
                공시유형=rec["공시유형"], 파일명=name, sha256=rec["sha256"],
                섹션출처=rec["섹션출처"])
    for i, (num, title, p, _l) in enumerate(located):
        body = bodies.get(i, "")
        for ci, ch in enumerate(_chunks(body)):
            secs.append(dict(base, 섹션번호=num, 섹션순번=i, 섹션제목_원문=title,
                             본문위치="발견" if p >= 0 else "미발견",
                             시작페이지=(p + 1) if p >= 0 else "",
                             chunk_seq=ci, 본문글자수=len(ch), 본문=ch,
                             text_path=os.path.relpath(tp, out_dir)))
        if p < 0:
            continue
        for tname, kws in TOPICS:
            hits = topic_hits(title, body, kws)
            if hits:
                for h in hits[:40]:
                    tops.append(dict(base, 주제=tname, 추출결과="찾음",
                                     섹션번호=num, 섹션제목_원문=title,
                                     원문=h, 출처페이지=p + 1))

    tables = detect_tables(pages)
    rec["표수"] = str(len(tables))
    for ti, (pi, rows) in enumerate(tables):
        # 이 표가 어느 섹션에 속하는지는 시작 페이지로 정한다(가장 가까운 앞 섹션).
        sec_i, sec_t, sec_n = "", "", ""
        for i, (num, title, p, _l) in enumerate(located):
            if 0 <= p <= pi:
                sec_i, sec_t, sec_n = i, title, num
        for ri, cells in enumerate(rows):
            for ci, (x, txt) in enumerate(cells):
                tbls.append({
                    "corp_label": rec["지주명"], "rcept_no": name, "rcept_dt": "",
                    "doc_kind": rec["공시유형"], "doc_purpose": "지배구조 연차보고서",
                    "section_index": sec_i, "section_title": sec_t,
                    "section_title_raw": sec_n, "table_index": ti,
                    "table_matched_keyword": "", "table_extracted": "Y",
                    "table_n_rows": len(rows), "row_index": ri, "cell_ord": ci,
                    "cell_tag": "", "rowspan": "", "colspan": "",
                    "unit_hint": "", "unit_hint_source": "", "cell_text": txt,
                    "fetched_at": rec["fetched_at"], "status": "000",
                    "raw_path": os.path.relpath(path, out_dir),
                    "raw_sha256": rec["sha256"],
                    "원천": "홈페이지PDF", "페이지": pi + 1, "cell_x": x,
                    "추출방법": "좌표군집",
                })
    if verbose:
        print("    %-14s %-46s %4s쪽 목차%3s 섹션%3s 표%4s %s"
              % (rec["지주명"], name[:46], rec["페이지수"], rec["목차항목수"],
                 rec["본문발견섹션수"], rec["표수"],
                 "스캔본추정" if rec["스캔본추정"] == "Y" else ""))
    return rec, secs, tbls, tops


def _write(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def load_metas(out_dir):
    out = []
    for m in sorted(glob.glob(os.path.join(out_dir, RAW_SUB, "*", "*.meta.json"))):
        try:
            d = json.load(open(m, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        d["_path"] = m[: -len(".meta.json")]
        out.append(d)
    return out


def build(out_dir=OUT, handoff_dir="handoff", only=None, verbose=True):
    metas = load_metas(out_dir)
    if only:
        keep = {s.strip() for s in only}
        metas = [m for m in metas if m.get("지주명") in keep]
    files, secs, tbls, tops = [], [], [], []
    for m in metas:
        a, b, c, d = process(m, out_dir, verbose)
        files.append(a)
        secs.extend(b)
        tbls.extend(c)
        tops.extend(d)

    # 주제별로 '없음' 도 적는다 — 찾은 것만 실으면 안 나온 주제가 사라진다.
    have = {(t["파일명"], t["주제"]) for t in tops}
    for f in files:
        if f["텍스트추출"] != "Y":
            continue
        for tname, _k in TOPICS:
            if (f["파일명"], tname) not in have:
                tops.append({"지주명": f["지주명"], "공시연도": f["공시연도"],
                             "공시유형": f["공시유형"], "파일명": f["파일명"],
                             "주제": tname,
                             "추출결과": "없음" if f["본문발견섹션수"] not in ("", "0")
                             else "판단불가",
                             "섹션번호": "", "섹션제목_원문": "", "원문": "",
                             "출처페이지": "", "sha256": f["sha256"]})

    p1 = _write(os.path.join(handoff_dir, "연차보고서_파일목록.csv"), files, FILE_COLS)
    p2 = _write(os.path.join(handoff_dir, "연차보고서_섹션.csv"), secs, SEC_COLS)
    p3 = _write(os.path.join(handoff_dir, "연차보고서_표.csv"), tbls, TBL_COLS)
    p4 = _write(os.path.join(handoff_dir, "연차보고서_주제추출.csv"), tops, TOPIC_COLS)
    if verbose:
        print("  파일 %d / 섹션 %d / 표 셀 %d / 주제 %d"
              % (len(files), len(secs), len(tbls), len(tops)))
    return {"paths": [p1, p2, p3, p4],
            "counts": {"파일": len(files), "섹션": len(secs),
                       "표셀": len(tbls), "주제": len(tops)}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--handoff-dir", default="handoff")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    build(a.out, a.handoff_dir, [s for s in a.only.split(",") if s.strip()] or None)
