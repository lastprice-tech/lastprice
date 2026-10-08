# -*- coding: utf-8 -*-
"""13차 9-2-4(ORSA 보도자료)·9-5(금감원 검사결과 공개자료) 산출물 검증·보정.

    python3 scripts/dart/verify13_web.py        # 대조만 — 결과 dart_out/risk13/verify13_web.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_web.py fix    # 보정(멱등: 원 생성기 web13_fss 의 build 를 고친 설정으로 다시 돌린 뒤 덧붙임) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-2-4_ORSA_보도자료.md, handoff/13차_산출물/9-5_금감원_검사결과.md,
      dart_out/risk13/9-5_검사결과_목록.csv. 결과 기록: dart_out/risk13/verify13_web.txt.
원본(읽기만, 새로 받지 않음): dart_out/raw/web13/fss/ — 보도자료 첨부 hwp 의 hwp2md 글(*.hwp.md), PDF 의 pypdf 글(*.pdf.txt,
      쪽 표지 「=== p.N ===」)·layout/merged 글, .meta.json(sha256·URL·fetched_at). 모범규준 조 제목: dart_out/risk13/모범규준_조목록.csv(2016.8.1판).

대조(인자 없이):
  1. md 의 원문 인용(코드 블록)마다 출처 원본과 공백만 무시하고 글자 대조(hwp2md 표기 <br>→줄바꿈, \\|→| 만 되돌림).
  2. 쪽 표기 — 9-2-4: 인용 머리의 「PDF 쪽」을 같은 게시글 PDF 의 pypdf 글로 다시 셈(줄마다 ① 줄 글 그대로 ② 가운데 10자 ③ 2자 이상 낱말 80%
     이상 — ③으로만 찾은 쪽은 「낱말 대조」 표시). 9-5: 인용 글이 걸친 쪽(쪽 번호 줄 「- N -」·숫자만 있는 줄은 원본에서도 뺌)과 머리 쪽 표기 대조.
  3. 출처 표기 — 9-2-4 인용 머리의 원파일·sha256·게시글 URL·수집 시각이 .meta.json 과 같은지. 9-5 문서 칸의 sha256·URL·수집 시각.
  4. 모범규준 조 번호(조 제목) — md 의 「N조(제목)」·색인 표 제목이 조목록.csv(2016.8.1판)와 같은지, 9-2-4 자료 묶음(Q1~Q9)마다 조 번호가 있는지.
  5. CSV — sha256(파일 바이트), 제목·인용조문·관련규정이 원본 글에 있는지, 제목 쪽, md 표와 판정·조·주제가 같은지, 조 제목 칸.
  6. 지시서(REQUEST13) 항목 대조 표·「검증 기록」 절이 있는지, md 의 게시글·첨부 URL 이 요청기록에 있는지, 인증값(키·OC) 문자열이 없는지,
     산출 폴더에 PDF 가 없는지. 참고로 보정 전 판(커밋 ec4a426)에 같은 검사를 돌린 결과도 결과 파일 끝에 덧붙인다(통과 여부와 무관).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)

TODAY = "2026-10-07"
D = os.path.join("dart_out", "raw", "web13", "fss")
PF = os.path.join(D, "press", "file")
PV = os.path.join(D, "press", "view")
EXI = os.path.join(D, "exam", "impr")
EXS = os.path.join(D, "exam", "sanc")
OUT = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
MD_P = os.path.join(OUT, "9-2-4_ORSA_보도자료.md")
MD_E = os.path.join(OUT, "9-5_금감원_검사결과.md")
CSV_E = os.path.join(WORK, "9-5_검사결과_목록.csv")
OUT_TXT = os.path.join(WORK, "verify13_web.txt")
ART_CSV = os.path.join(WORK, "모범규준_조목록.csv")
IMPR_ALL = os.path.join(WORK, "9-5_경영유의공시_전체목록.csv")
SANC_LIST = os.path.join(WORK, "9-5_검사결과제재_지주목록.csv")
CAND_CSV = os.path.join(WORK, "9-2-4_보도자료_후보.csv")
REQLOG = os.path.join(WORK, "9-2-4_9-5_요청기록.csv")
VERIFY_HEAD = "## 검증 기록(2026-10-07)"
FOOT_RE = re.compile(r"^(?:-\s*\d+\s*-|\d{1,3})$")
NEW_CSV_COLS = ["모범규준_조제목(2016.8.1판)", "넓혀찾은_조문표기(검증)", "PDF문서정보_작성일(참고·공개일아님)", "검증메모"]


# ── 공용 ────────────────────────────────────────────────────────────────────
def ns(x):
    return re.sub(r"\s+", "", x)


def nsb(x):
    return re.sub(r"[\s|\\]+", "", x)


_C = {}


def read(p):
    if p not in _C:
        with open(p, encoding="utf-8") as f:
            _C[p] = f.read()
    return _C[p]


def meta(p):
    with open(p + ".meta.json", encoding="utf-8") as f:
        return json.load(f)


def metas(d):
    out = []
    for x in sorted(os.listdir(d)):
        if x.endswith(".meta.json"):
            p = os.path.join(d, x[:-len(".meta.json")])
            out.append((p, meta(p)))
    return out


def pages_of(txt):
    parts = re.split(r"=== p\.(\d+) ===[^\n]*\n?", read(txt))
    return [(int(parts[k]), parts[k + 1]) for k in range(1, len(parts), 2)]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def show_hwp(t):
    return t.replace("<br>", "\n").replace("\\|", "|")


def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def titles2016():
    return {int(r["조"]): r["제목_2016.8.1판"] for r in read_csv(ART_CSV)}


def art_list(spec):
    """「37·44」「42~46」「30~32·41」 → [37, 44] … 장 번호(제5장)는 빼고 괄호 밖 숫자만."""
    spec = re.sub(r"제\d+장(?:\([^)]*\))?", "", spec)
    out = []
    for part in re.findall(r"\d+~\d+|\d+", spec):
        if "~" in part:
            a, b = map(int, part.split("~"))
            out += list(range(a, b + 1))
        else:
            out.append(int(part))
    return out


def art_label(spec, T):
    """「37·44」 → 「37조(자본적정성 평가 및 관리 체제)·44조(통합 내부자본 산출)」 — 범위는 한 조씩 펼침."""
    return "·".join("%d조(%s)" % (a, T[a]) for a in art_list(spec))


CH5 = "37~49조(제5장) 주제"                                              # 규제자본비율 산출 등 — 제5장(36~49조) 안 특정 조 없음(판단)
CH5_OLD = "제5장(37~49) 주제"


def art_title_cell(spec, T):
    """CSV 「모범규준_조제목(2016.8.1판)」 칸."""
    if not spec:
        return ""
    if "제5장" in spec:
        return "제5장 내부자본 적정성 평가 및 관리(36조~49조) 가운데 37~49조 주제 — 특정 조 없음(판단)"
    return art_label(spec, T)


def code_blocks(lines):
    """md 줄 목록 → [(시작 줄, 끝 줄, 글)] — 「```text」 … 「```」."""
    out, i = [], 0
    while i < len(lines):
        if lines[i] == "```text":
            j = lines.index("```", i + 1)
            out.append((i, j, "\n".join(lines[i + 1:j])))
            i = j
        i += 1
    return out


class Report:
    def __init__(self):
        self.lines, self.bad = [], 0

    def h(self, s):
        self.lines += ["", "== " + s]

    def ok(self, s):
        self.lines.append("  ok  " + s)

    def ng(self, s):
        self.bad += 1
        self.lines.append("  !!  " + s)

    def note(self, s):
        self.lines.append("      " + s)


# ── 9-2-4 원본 ────────────────────────────────────────────────────────────────
def press_sources():
    out = []
    for p, m in metas(PF):
        mm = re.match(r"(fss|fsc)_(\d+)_\d+\.(pdf|hwp|hwpx)$", os.path.basename(p))
        if mm:
            out.append(dict(path=p, meta=m, site=mm.group(1), no=mm.group(2), ext=mm.group(3)))
    return out


def board_label(site, no):
    return "%s %s" % ("금감원" if site == "fss" else "금융위", no)


def board_of_url(url):
    m = re.search(r"fsc\.go\.kr/no010101/(\d+)", url)
    if m:
        return ("fsc", m.group(1))
    m = re.search(r"nttId=(\d+)", url)
    return ("fss", m.group(1)) if m else None


def press_text(src):
    p = src["path"]
    if src["ext"] == "pdf":
        q = p + ".merged.txt" if os.path.exists(p + ".merged.txt") else p + ".txt"
        return read(q)
    return show_hwp(read(p + ".md"))


TOK_RE = re.compile(r"[가-힣]{2,}|[0-9][0-9.]*[0-9]|[A-Za-z]{2,}")


def pdf_line_pages(quote, pdf_path):
    """hwp 에서 옮긴 인용의 줄마다 PDF(pypdf 기본 모드 글) 쪽을 찾는다. → (쪽 목록, 낱말 대조만으로 찾은 쪽, 대조한 줄 수, 못 찾은 줄 수)."""
    P = [(n, nsb(t)) for n, t in pages_of(pdf_path + ".txt")]
    hits, weak, tot, miss = [], set(), 0, 0
    for ln in quote.split("\n"):
        k = nsb(ln)
        if len(k) < 6:
            continue
        tot += 1
        hit = None
        for n, t in P:
            if k in t:
                hit = (n, "strong")
                break
        if hit is None and len(k) >= 10:
            key = k[(len(k) - 10) // 2:][:10]
            for n, t in P:
                if key in t:
                    hit = (n, "strong")
                    break
        if hit is None:
            toks = TOK_RE.findall(ln)
            if len(toks) >= 3:
                best = max(((sum(1 for x in toks if x in t) / len(toks), -n) for n, t in P), default=(0, 0))
                if best[0] >= 0.8:
                    hit = (-best[1], "weak")
        if hit is None:
            miss += 1
            continue
        hits.append(hit)
    pages = sorted(set(n for n, _ in hits))
    weak_only = {n for n in pages if all(k == "weak" for m, k in hits if m == n)}
    return pages, weak_only, tot, miss


def page_spans(text_pages, quote):
    """(쪽, 글) 목록에서 공백 뺀 인용 글이 걸친 쪽. 쪽 번호 줄은 뺀다. 못 찾으면 None."""
    S, at = [], []
    for n, t in text_pages:
        for ln in t.split("\n"):
            if FOOT_RE.match(ln.strip()):
                continue
            k = ns(ln)
            S.append(k)
            at += [n] * len(k)
    s = "".join(S)
    q = ns(quote)
    i = s.find(q)
    if i < 0 or not q:
        return None
    return sorted(set(at[i:i + len(q)]))


def press_expected(quote, src, boards, srcs):
    """인용 머리에 들어갈 쪽 글(새 형식)."""
    if src["ext"] == "pdf":
        pg = page_spans(pages_of(src["path"] + ".merged.txt"), quote) or page_spans(pages_of(src["path"] + ".txt"), quote)
        return "PDF 쪽: %s 첨부 「%s」 %s" % (board_label(src["site"], src["no"]), src["meta"].get("원파일명", ""),
                                         ",".join("p.%d" % n for n in pg) if pg else "찾지 못함")
    pdfs = [s for s in srcs if s["ext"] == "pdf" and (s["site"], s["no"]) in boards]
    pdfs.sort(key=lambda s: (boards.index((s["site"], s["no"])), s["path"]))
    if not pdfs:
        return "PDF 쪽: (같은 게시글에 PDF 첨부 없음)"
    parts, tot, miss_all = [], 0, []
    for s in pdfs:
        pages, weak, tot, miss = pdf_line_pages(quote, s["path"])
        miss_all.append(miss)
        if pages:
            parts.append("%s 첨부 「%s」 %s" % (board_label(s["site"], s["no"]), s["meta"].get("원파일명", ""),
                                             ",".join("p.%d%s" % (n, "(낱말 대조)" if n in weak else "") for n in pages)))
    if not parts:
        return "PDF 쪽: 찾지 못함(같은 게시글 PDF %d개의 pypdf 글에 인용 줄 %d개가 줄·가운데 10자·낱말로 걸리지 않음)" % (len(pdfs), tot)
    tail = " · PDF 글에서 못 찾은 줄 %d/%d" % (min(miss_all), tot) if min(miss_all) else ""
    return "PDF 쪽: " + " ; ".join(parts) + tail


HDR_NEW = re.compile(r"^인용 — (?P<label>.*?) · 원파일 「(?P<name>.*?)」\((?P<blabel>[^)]*) 첨부\) · sha256 (?P<sha>[0-9a-f]{16})… · "
                     r"게시글 (?P<url>\S+) · (?P<pages>.*?) · 수집 (?P<fa>\S+)$")
HDR_OLD = re.compile(r"^인용 — (?P<label>.*?) · 원파일 「(?P<name>.*?)」 · sha256 (?P<sha>[0-9a-f]{16})… · (?P<pages>.*?) · 수집 (?P<fa>\S+)$")


def press_quotes(lines):
    """9-2-4 md → 인용 목록(머리 줄 번호·머리·Q·게시판·글)."""
    out, q, boards, hdr = [], None, [], None
    blocks = {s: (e, t) for s, e, t in code_blocks(lines)}
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and not ln.startswith("## 2."):
            q = None
        if ln.startswith("### Q"):
            q, boards = ln.split()[1], []
        m = re.match(r"- (금융위|금감원) 게시글 (\S+) — ", ln)
        if m and q:
            b = board_of_url(m.group(2))
            if b:
                boards.append(b)
        if ln.startswith("인용 — "):
            hdr = i
        if i in blocks:
            out.append(dict(q=q, boards=list(boards), hdr_i=hdr, hdr=lines[hdr] if hdr is not None else "", start=i,
                            end=blocks[i][0], text=blocks[i][1]))
            hdr = None
    return out


def find_press_src(name, sha16, srcs):
    for s in srcs:
        if s["meta"].get("원파일명") == name and s["meta"]["sha256"].startswith(sha16):
            return s
    return None


def check_press(md_path, R, T):
    lines = read_now(md_path).split("\n")
    srcs = press_sources()
    qs = press_quotes(lines)
    R.h("9-2-4 인용 대조 — %s (인용 블록 %d개)" % (md_path, len(qs)))
    nok = 0
    for x in qs:
        where = "%s 줄 %d" % (x["q"], x["start"] + 1)
        m = HDR_NEW.match(x["hdr"])
        old = None if m else HDR_OLD.match(x["hdr"])
        if not (m or old):
            R.ng("%s: 인용 머리 꼴을 읽지 못함 — %r" % (where, x["hdr"][:80]))
            continue
        g = (m or old).groupdict()
        src = find_press_src(g["name"], g["sha"], srcs)
        if not src:
            R.ng("%s: 원파일 「%s」 sha256 %s… 원본 없음" % (where, g["name"], g["sha"]))
            continue
        text = press_text(src)
        if ns(x["text"]) in ns(text):
            nok += 1
        else:
            R.ng("%s: 원본 글과 다름(공백 무시) — %s · %r" % (where, os.path.basename(src["path"]), x["text"][:80]))
        if g["fa"] != src["meta"]["fetched_at"]:
            R.ng("%s: 수집 시각 다름 %s ↔ meta %s" % (where, g["fa"], src["meta"]["fetched_at"]))
        if not m:
            R.ng("%s: 인용 머리에 게시글 URL·게시판 표기 없음(옛 꼴)" % where)
        else:
            if g["url"] != src["meta"].get("게시글URL"):
                R.ng("%s: 게시글 URL 다름 %s ↔ meta %s" % (where, g["url"], src["meta"].get("게시글URL")))
            if g["blabel"] != board_label(src["site"], src["no"]):
                R.ng("%s: 게시판 표기 다름 %s" % (where, g["blabel"]))
        exp = press_expected(x["text"], src, x["boards"], srcs)
        if g["pages"] != exp:
            R.ng("%s: 쪽 표기 다름 — 적힌 것 「%s」 ↔ 다시 셈 「%s」" % (where, g["pages"][:160], exp[:160]))
    R.ok("원본 글 일치 %d/%d" % (nok, len(qs)))
    return qs


def check_press_articles(md_path, R, T):
    t = read_now(md_path)
    lines = t.split("\n")
    R.h("9-2-4 모범규준 조 번호(조 제목) — 조목록.csv 2016.8.1판")
    seen_q, cur, n = {}, None, 0
    for ln in lines:
        if ln.startswith("### Q"):
            cur = ln.split()[1]
            seen_q.setdefault(cur, 0)
        if ln.startswith("## ") and not ln.startswith("## 2."):
            cur = None
        if ln.startswith("note: 모범규준 대응") or (ln.startswith("| Q") and "|" in ln):
            for a, ttl in re.findall(r"(\d+)조\((?!판단)([^()]*)\)", ln):
                n += 1
                if T.get(int(a)) != ttl:
                    R.ng("조 제목 다름: %s조(%s) ↔ 조목록 %r — %s" % (a, ttl, T.get(int(a)), ln[:80]))
            if ln.startswith("note: 모범규준 대응") and cur:
                if not re.search(r"\d+조\(", ln) or "(판단" not in ln:
                    R.ng("%s: 조 번호(조 제목)·(판단) 표시 없음 — %s" % (cur, ln[:80]))
                seen_q[cur] += 1
            if ln.startswith("| Q"):
                q = ln.split("|")[1].strip()
                last = ln.rstrip("|").split("|")[-1].strip()
                if not re.search(r"\d+조\(", last):
                    R.ng("1절 표 %s: 모범규준 조 칸에 「N조(제목)」 없음 — %r" % (q, last))
    for q, c in sorted(seen_q.items()):
        if not c:
            R.ng("자료 묶음 %s: 모범규준 대응 note 없음" % q)
    R.ok("「N조(제목)」 %d곳 대조, 자료 묶음 %d개" % (n, len(seen_q)))
    if "9-2_ORSA_보험기준.md" in t and "그런 파일은 없음" not in t:
        R.ng("없는 파일 이름 `9-2_ORSA_보험기준.md` 를 가리킴")
    for ref in re.findall(r"handoff/13차_산출물/([^`\s)]+\.md)", t):
        if not os.path.exists(os.path.join(OUT, ref)) and ref != "9-2_ORSA_보험기준.md":
            R.ng("가리킨 산출 파일 없음: %s" % ref)


# ── 9-5 원본 ──────────────────────────────────────────────────────────────────
def exam_docs():
    out = {}
    for d, kind in ((EXI, "impr"), (EXS, "sanc")):
        for p, m in metas(d):
            if p.endswith(".pdf"):
                out[m["sha256"]] = dict(path=p, meta=m, kind=kind)
    return out


def doc_pages(doc):
    return pages_of(doc["path"] + ".txt")


def check_exam_md(md_path, R, T, rows):
    lines = read_now(md_path).split("\n")
    docs = exam_docs()
    R.h("9-5 인용 대조 — %s" % md_path)
    blocks = code_blocks(lines)
    nok = 0
    for s, e, text in blocks:
        sha, claim, where = None, None, "줄 %d" % (s + 1)
        for k in range(s - 1, -1, -1):
            ln = lines[k]
            if claim is None and (ln.startswith("#### [") or ln.startswith("문서 머리") or ln.startswith("인용 —")):
                mm = re.findall(r"p\.\d+(?:,p\.\d+)*", ln)
                claim = mm[-1] if mm else ""
            m = re.search(r"sha256 ([0-9a-f]{64})", ln)
            if m:
                sha = m.group(1)
                break
        if not sha or sha not in docs:
            R.ng("%s: 출처 sha256 을 찾지 못함" % where)
            continue
        doc = docs[sha]
        pg = page_spans(doc_pages(doc), text)
        if pg is None:
            R.ng("%s: 원본 글과 다름(공백 무시) — %s · %r" % (where, os.path.basename(doc["path"]), text[:80]))
            continue
        nok += 1
        want = ",".join("p.%d" % n for n in pg)
        if not claim:
            R.ng("%s: 쪽 표기 없음(원본 %s)" % (where, want))
        elif claim != want:
            R.ng("%s: 쪽 표기 %s ↔ 원본 %s" % (where, claim, want))
    R.ok("인용 블록 %d개 중 원본 글 일치 %d" % (len(blocks), nok))
    # 문서 칸(sha256·URL·수집)
    R.h("9-5 문서 출처 표기")
    n = 0
    for ln in lines:
        m = re.match(r"- 문서: 「(.*?)」 · (\S+) · sha256 ([0-9a-f]{64}) · 수집 (\S+)", ln)
        if not m:
            continue
        n += 1
        doc = docs.get(m.group(3))
        if not doc:
            R.ng("문서 sha256 원본 없음: %s" % m.group(1))
            continue
        if doc["meta"].get("원파일명") != m.group(1) or doc["meta"]["출처URL"] != m.group(2) or doc["meta"]["fetched_at"] != m.group(4):
            R.ng("문서 칸이 meta 와 다름: %s" % m.group(1))
        if sha_file(doc["path"]) != m.group(3):
            R.ng("파일 바이트 sha256 다름: %s" % doc["path"])
    R.ok("문서 칸 %d개 대조" % n)
    # 표 ↔ CSV
    R.h("9-5 md 항목 표 ↔ CSV")
    by_sha = {}
    for r in rows:
        by_sha.setdefault(r["sha256"], []).append(r)
    sha, k_tab, n = None, 0, 0
    for ln in lines:
        m = re.search(r"^- 문서: .* sha256 ([0-9a-f]{64})", ln)
        if m:
            sha = m.group(1)
            continue
        m = re.match(r"^\| (\d+) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (Y|N|경계) \| (.*?) \| (.*?) \|$", ln)
        if m and sha in by_sha:
            k = int(m.group(1))
            rr = by_sha[sha]
            if k > len(rr):
                R.ng("표 행 %d 이 CSV 에 없음(%s)" % (k, sha[:12]))
                continue
            r = rr[k - 1]
            n += 1
            got = (m.group(2), m.group(3), m.group(4), m.group(6), m.group(7), m.group(8))
            want = (r["구분"], r["번호"], r["제목"].replace("|", "｜"), r["리스크관련(판단)"], r["모범규준_조(판단)"], r["주제(판단)"])
            if got != want:
                R.ng("md 표 ↔ CSV 다름(%s %s): %s ↔ %s" % (r["지주"], r["번호"], got, want))
    R.ok("md 표 %d행 ↔ CSV 대조" % n)
    # 근거 조문·관련규정·넓혀 찾은 표기 ↔ 원본
    R.h("9-5 근거로 든 조문·관련규정 칸 ↔ 원본 글")
    sha, n = None, 0
    for ln in lines:
        m = re.search(r"sha256 ([0-9a-f]{64})", ln)
        if m:
            sha = m.group(1)
        for head in ("- 근거로 든 조문", "- 문서의 「< 관련규정 >」 칸", "- 넓혀 찾은 조문·규정 표기"):
            if ln.startswith(head) and sha in docs:
                body = ln.split("): ", 1)[-1] if head != "- 문서의 「< 관련규정 >」 칸" else ln.split("칸: ", 1)[-1]
                if body.startswith("문서 글에") or body.startswith("추출 범위에 없음"):
                    continue
                whole = ns("".join(t for _, t in doc_pages(docs[sha])))
                for c in re.split(r" ; | · ", body):
                    c = re.sub(r"^(조문 표기|규정·법규 이름|별표|§ 표기): ", "", c.strip())
                    if not c:
                        continue
                    n += 1
                    if ns(c) not in whole:
                        R.ng("원본 글에 없음(%s): 「%s」" % (head[2:], c[:60]))
    R.ok("칸 글 %d개 대조" % n)
    # 조 제목
    R.h("9-5 모범규준 조 제목 — 조목록.csv 2016.8.1판")
    n = 0
    for ln in lines:
        if ln.startswith("- note: 모범규준 조 제목"):
            if "(2016.8.1판" not in ln:
                R.ng("조 제목 판 표기가 2016.8.1판 아님: %s" % ln[:70])
            for a, ttl in re.findall(r"(\d+)조\((?!판단)([^()]*)\)", ln):
                n += 1
                if T.get(int(a)) != ttl:
                    R.ng("조 제목 다름: %s조(%s) ↔ %r" % (a, ttl, T.get(int(a))))
        m = re.match(r"^\| (\d+)조 \| ([^|]*) \|", ln)
        if m:
            n += 1
            if T.get(int(m.group(1))) != m.group(2).strip():
                R.ng("색인 조 제목 다름: %s조 %r ↔ %r" % (m.group(1), m.group(2), T.get(int(m.group(1)))))
        if "2017.4.1판)" in ln and "조 제목" in ln and not ln.startswith("- note: 모범규준 조 제목"):
            R.ng("조 제목 판 표기가 2016.8.1판 아님(2017.4.1판으로 적힘): %s" % ln[:80])
    R.ok("조 제목 %d곳 대조" % n)
    # 색인 ↔ CSV
    R.h("9-5 4절 색인 ↔ CSV")
    idx = {}
    for ln in lines:
        m = re.match(r"^\| (\d+조|[^|]*주제) \| [^|]* \| (.*) \|$", ln)
        if m:
            idx[m.group(1)] = m.group(2)
    n = 0
    for r in rows:
        if r["리스크관련(판단)"] == "N" or not r["모범규준_조(판단)"]:
            continue
        spec = r["모범규준_조(판단)"]
        keys = []
        if "제5장" in spec:
            keys.append([k for k in idx if k.endswith("주제")][0] if any(k.endswith("주제") for k in idx) else "?")
        rest = re.sub(r"\d+~\d+조\(제\d+장\)\s*주제|제\d+장\([^)]*\)\s*주제", "", spec)
        for part in re.findall(r"\d+~\d+|\d+", rest):
            keys.append("%d조" % int(part.split("~")[0]))
        entry = "%s %s %s %s 「%s」(%s)" % (r["지주"], r["제재조치요구일(목록)"], r["구분"], r["번호"], r["제목"], r["리스크관련(판단)"])
        for k in sorted(set(keys)):
            n += 1
            if entry not in idx.get(k, "").split("<br>"):
                R.ng("색인 %s 행에 없음: %s" % (k, entry[:80]))
    R.ok("색인 항목 %d개 대조" % n)
    # 비은행 절
    R.h("9-5 비은행지주(메리츠·한국투자) 따로 표시")
    t = "\n".join(lines)
    sec2 = t.split("## 2. 비은행지주")[1].split("\n## 3.")[0] if "## 2. 비은행지주" in t else ""
    for nm, dt in (("메리츠금융지주", "20221223"), ("한국투자금융지주", "20241126")):
        if ("### %s — 제재조치요구일 %s" % (nm, dt)) in sec2:
            R.ok("2절에 %s %s" % (nm, dt))
        else:
            R.ng("2절에 %s %s 없음" % (nm, dt))
    for r in rows:
        want = "Y" if re.search(r"메리츠|한국투자", r["제재대상기관(목록)"]) else "N"
        if r["비은행지주"] != want:
            R.ng("CSV 비은행지주 칸 다름: %s %s" % (r["지주"], r["번호"]))


def check_exam_csv(R, T):
    rows = read_csv(CSV_E)
    docs = exam_docs()
    R.h("9-5 CSV — %s (%d행)" % (CSV_E, len(rows)))
    cols = list(rows[0].keys()) if rows else []
    for c in NEW_CSV_COLS:
        if c not in cols:
            R.ng("CSV 칸 없음: %s" % c)
    shaok = {}
    n_t = n_c = 0
    for i, r in enumerate(rows, 2):
        doc = docs.get(r["sha256"])
        if not doc:
            R.ng("CSV %d행: sha256 원본 없음" % i)
            continue
        if r["sha256"] not in shaok:
            shaok[r["sha256"]] = sha_file(doc["path"]) == r["sha256"]
            if not shaok[r["sha256"]]:
                R.ng("CSV %d행: 파일 바이트 sha256 다름" % i)
        if r["url"] != doc["meta"]["출처URL"] or r["파일"] != doc["meta"].get("원파일명", ""):
            R.ng("CSV %d행: url·파일 칸이 meta 와 다름" % i)
        P = [(n, ns(t)) for n, t in doc_pages(doc)]
        L = [(n, ns(t)) for n, t in pages_of(doc["path"] + ".layout.txt")] if os.path.exists(doc["path"] + ".layout.txt") else []
        tk = ns(r["제목"])
        tp = [n for n, t in P if tk in t] or [n for n, t in L if tk in t]
        want_pages = [int(x) for x in re.findall(r"p\.(\d+)", r["쪽"])]
        if not tp:
            R.ng("CSV %d행: 제목이 원본 글에 없음 — %r" % (i, r["제목"][:50]))
        elif not set(tp) & set(want_pages):
            R.ng("CSV %d행: 제목 쪽 %s ↔ 쪽 칸 %s" % (i, tp, r["쪽"]))
        else:
            n_t += 1
        whole = ns("".join(t for _, t in doc_pages(doc)))
        for col in ("인용조문", "관련규정"):
            for c in [x for x in r[col].split(" ; ") if x.strip()]:
                n_c += 1
                if ns(c) not in whole:
                    R.ng("CSV %d행: %s 「%s」 이 원본 글에 없음" % (i, col, c[:60]))
        if "모범규준_조제목(2016.8.1판)" in r:
            want = art_title_cell(r["모범규준_조(판단)"], T)
            if r["모범규준_조제목(2016.8.1판)"] != want:
                R.ng("CSV %d행: 조 제목 칸 %r ↔ %r" % (i, r["모범규준_조제목(2016.8.1판)"], want))
        for a in art_list(r["모범규준_조(판단)"]):
            if not 3 <= a <= 58:
                R.ng("CSV %d행: 모범규준 조 번호가 시트 범위(3~58) 밖 — %d" % (i, a))
    R.ok("제목 원본·쪽 일치 %d/%d, 인용조문·관련규정 %d개 대조" % (n_t, len(rows), n_c))
    # 조치내용 건수 ↔ CSV 구분별 수
    R.h("9-5 조치내용 칸 건수 ↔ CSV 항목 수(경영유의 공시 문서)")
    by = {}
    for r in rows:
        if r["목록"].startswith("금융회사 경영유의"):
            by.setdefault(r["sha256"], []).append(r)
    for sha, rr in by.items():
        head = "".join(t for _, t in doc_pages(docs[sha]))[:1500]
        dec = {}
        for k, pat in (("경영유의사항", r"경영\s*유의\s*(?:사항)?\s*:?\s*(\d+)\s*건"), ("개선사항", r"개선\s*사항\s*:?\s*(\d+)\s*건")):
            m = re.search(pat, head)
            if m:
                dec[k] = int(m.group(1))
        cnt = {}
        for r in rr:
            kk = "경영유의사항" if "경영유의" in r["구분"] else "개선사항" if "개선" in r["구분"] else r["구분"]
            cnt[kk] = cnt.get(kk, 0) + 1
        if not dec or any(cnt.get(k) != v for k, v in dec.items()):
            R.ng("%s %s: 조치내용 %s ↔ CSV %s" % (rr[0]["지주"], rr[0]["제재조치요구일(목록)"], dec, cnt))
    R.ok("문서 %d건 건수 대조" % len(by))
    return rows


# ── 공통 점검 ─────────────────────────────────────────────────────────────────
def secrets():
    vals = []
    for k in ("DART_API_KEY", "LAW_OC"):
        v = os.environ.get(k, "").strip()
        if v:
            vals.append(v)
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*(DART_API_KEY|LAW_OC)\s*=\s*(.+)$", line)
                if m:
                    vals.append(m.group(2).strip().strip('"').strip("'"))
    return [v for v in vals if len(v) >= 6]


def check_common(R, files):
    R.h("인증값·PDF·검증 기록 절")
    vals = secrets()
    for p in files:
        if not os.path.exists(p):
            continue
        t = read_now(p)
        if any(v in t for v in vals):
            R.ng("인증값 문자열이 들어 있음: %s" % p)
        for pat in (r"OC=(?!\*\*\*)[A-Za-z0-9]", r"crtfc_key=[0-9a-f]{20,}", r"DART_API_KEY\s*=\s*\w{10,}", r"LAW_OC\s*=\s*\w{4,}"):
            if re.search(pat, t):
                R.ng("인증값 꼴 문자열(%s): %s" % (pat, p))
    R.ok("인증값 값 %d개·꼴 4개로 %d개 파일 확인" % (len(vals), len(files)))
    pdfs = [os.path.join(dp, f) for dp, _, fs in os.walk(OUT) for f in fs if f.lower().endswith(".pdf")]
    if pdfs:
        R.ng("산출 폴더에 PDF: %s" % pdfs)
    else:
        R.ok("산출 폴더(handoff/13차_산출물)에 PDF 없음")
    for md in (MD_P, MD_E):
        heads = [ln for ln in read_now(md).split("\n") if ln.startswith("## ")]
        if not heads or heads[-1] != VERIFY_HEAD:
            R.ng("%s: 맨 끝 절이 「%s」 아님" % (md, VERIFY_HEAD))
        else:
            R.ok("%s: 맨 끝 「%s」" % (os.path.basename(md), VERIFY_HEAD))


def check_urls(R):
    """md 에 적은 게시글·첨부 URL 이 요청기록(9-2-4_9-5_요청기록.csv)에 있는지 — 게시판 목록 주소(list.do·no010101)는 출처 설명용이라 뺌."""
    R.h("출처 URL ↔ 요청기록")
    log = {r["URL"] for r in read_csv(REQLOG)}
    n = 0
    for md in (MD_P, MD_E):
        for u in sorted(set(re.findall(r"https://www\.(?:fss\.or\.kr|fsc\.go\.kr)[^\s)」|`]+", read_now(md)))):
            if "list.do" in u or u.rstrip("/") == "https://www.fsc.go.kr/no010101":
                continue
            n += 1
            if u not in log:
                R.ng("요청기록에 없는 URL(%s): %s" % (os.path.basename(md), u))
    R.ok("게시글·첨부 URL %d개가 요청기록에 있음" % n)


REQ_P = ["ORSA 도입 발표 원문과 날짜", "도입 로드맵", "시행 시기", "유예 허용"]
REQ_E = ["지주 이름", "공개일", "지적 제목", "요지", "근거로 든 조문", "2022년 이후 범위", "비은행지주(메리츠, 한국투자) 따로 표시",
         "리스크관리 관련 판정 누락 재검토"]


def check_coverage(R):
    R.h("지시서 항목 대조 표(「받은 글」 또는 「추출 범위에 없음 + 찾은 방법」)")
    for md, req in ((MD_P, REQ_P), (MD_E, REQ_E)):
        t = read_now(md)
        sec = t.split(VERIFY_HEAD)[-1] if VERIFY_HEAD in t else ""
        quotes = ns("\n".join(b for _, _, b in code_blocks(t.split("\n"))))
        for item in req:
            m = re.search(r"^\| %s \| ([^|]+) \| ([^|]+) \|$" % re.escape(item), sec, re.M)
            if not m:
                R.ng("%s: 지시서 항목 「%s」 행 없음" % (os.path.basename(md), item))
                continue
            st, ev = m.group(1).strip(), m.group(2)
            if not (st.startswith("받은 글") or st.startswith("추출 범위에 없음") or st.startswith("판단")):
                R.ng("%s: 「%s」 상태 칸 %r" % (os.path.basename(md), item, st))
            if st.startswith("추출 범위에 없음") and "찾은 방법" not in ev:
                R.ng("%s: 「%s」 추출 범위에 없음인데 찾은 방법 없음" % (os.path.basename(md), item))
            if md == MD_P and st.startswith("받은 글"):
                for ph in re.findall(r"「([^」]{4,})」", ev):
                    if ns(ph) not in quotes:
                        R.ng("%s: 「%s」 근거 글 「%s」 이 인용 블록에 없음" % (os.path.basename(md), item, ph))
        R.ok("%s: 지시서 항목 %d개 확인" % (os.path.basename(md), len(req)))


_NOW = {}


def read_now(p):
    if p in _NOW:
        return _NOW[p]
    with open(p, encoding="utf-8") as f:
        return f.read()


def verify(write=True, files=None, quiet=False):
    """대조. files 를 주면 그 경로 쌍(md_p, md_e, csv)을 대조(보정 전 상태 셈에 씀)."""
    global MD_P, MD_E, CSV_E
    saved = (MD_P, MD_E, CSV_E)
    if files:
        MD_P, MD_E, CSV_E = files
    try:
        R = Report()
        T = titles2016()
        R.lines.append("verify13_web — 13차 9-2-4·9-5 산출물 검증(%s, scripts/dart/verify13_web.py)" % TODAY)
        R.lines.append("대상: %s · %s · %s" % (MD_P, MD_E, CSV_E))
        for p in (MD_P, MD_E, CSV_E):
            if os.path.exists(p):
                R.lines.append("  sha256 %s  %s" % (sha_file(p), p))
        check_press(MD_P, R, T)
        check_press_articles(MD_P, R, T)
        rows = check_exam_csv(R, T)
        check_exam_md(MD_E, R, T, rows)
        check_coverage(R)
        check_urls(R)
        check_common(R, [MD_P, MD_E, CSV_E, OUT_TXT, os.path.abspath(__file__)])
        R.lines += ["", "문제 %d" % R.bad]
        if not files:                                                   # 참고: 보정 전(커밋 판) 같은 검사
            tmp = tempfile.mkdtemp(prefix="verify13_base_")
            paths = []
            for p in (MD_P, MD_E, CSV_E):
                b = git_base(p)
                q = os.path.join(tmp, os.path.basename(p))
                if b is not None:
                    with open(q, "wb") as f:
                        f.write(b)
                paths.append(q)
            if all(os.path.exists(q) for q in paths):
                R0 = verify(write=False, files=tuple(paths), quiet=True)
                R.lines += ["", "== 참고: 보정 전 판(커밋 %s)에 같은 검사 — 문제 %d (지금 판의 통과 여부와 무관)" % (BASE_COMMIT, R0.bad)]
                R.lines += ["  분류: " + ", ".join("%s %d" % (k, v) for k, v in sorted(_cats(R0).items(), key=lambda kv: -kv[1]))]
                R.lines += [ln.replace(tmp + os.sep, "(커밋 %s)/" % BASE_COMMIT).replace("  !!", "  전!!", 1)
                            for ln in R0.lines if ln.startswith("  !!")]
            for q in paths:
                if os.path.exists(q):
                    os.remove(q)
            os.rmdir(tmp)
        if write:
            with open(OUT_TXT, "w", encoding="utf-8") as f:
                f.write("\n".join(R.lines) + "\n")
        if not quiet:
            print("\n".join(l for l in R.lines if l.startswith("==") or l.startswith("  !!"))[:6000])
            print("문제", R.bad, "→", OUT_TXT if write else "(기록 안 함)")
        return R
    finally:
        MD_P, MD_E, CSV_E = saved


# ── 보정(fix) ──────────────────────────────────────────────────────────────────
# 9-5 판정 보정(판단): (CLASS 날짜 키, 문서 안 항목 순번, 기대하는 옛 값(판정, 조) — None 이면 N, 새 판정, 새 조, 주제 덧말)
PATCH_CLASS = [
    ("20240620", 8, None, "경계", "35·5", "경영진 장기성과지표 건전성 비중(고위험·고수익 추구 유인) [검증: N→경계]"),
    ("20250318", 15, None, "경계", "35·5", "경영진 성과평가 건전성 지표 비중(과도한 위험추구 통제) [검증: N→경계]"),
    ("20250318", 11, None, "Y", "33·21", "소개여신 건전성 사후관리 — 고위험 차주 자회사간 소개(위험 전이) [검증: N→Y]"),
    ("20241126", 3, ("경계", "35"), "경계", "35·5", " [검증: 5조 더함]"),
    ("20250317", 14, ("경계", "35"), "경계", "35·5", " [검증: 5조 더함]"),
    ("20260723", 19, ("Y", "37~47·18~27"), "Y", "37~47·18~27·5", " [검증: 5조 더함]"),
    ("20250318", 17, ("Y", "9·33"), "Y", "9·33·8", " [검증: 8조 더함]"),
]
# 「닿지 않은 조」 반박 인용(판단 연결): (날짜 키, 항목 순번, 찾을 글(공백 뺀), 연결한 조, 까닭)
REFUTE_ARTS = [
    ("20260723", 19, "위험성향", 5, "5조 ②1호 「사전 설정된 위험성향 내에서 위험과 수익의 균형」 — 지주 등 위험성향 Target 비율 부재 지적"),
    ("20241126", 3, "리스크관리지표", 5, "5조 ②4호 「성과관리체계는 영업 의사결정시 위험이 명확히 고려되도록」 — 성과지표에 리스크관리 지표"),
    ("20250317", 14, "리스크연계", 5, "5조 ②4호 — 임원 장기성과 지표의 건전성(리스크 연계) 비중"),
    ("20240620", 8, "건전성지표의비중", 5, "5조 ②4호 — 장기성과평가 건전성 지표 비중 20%, 고위험·고수익 추구 유인"),
    ("20250318", 15, "과도한위험추구", 5, "5조 ②4호 — 건전성 지표 비중 상향으로 과도한 위험추구 통제"),
    ("20250318", 17, "충분히보고되지않을위험", 8, "8조 ③ 「이사회는 … 위험의 수준 및 관리현황에 대해 충분히 이해」 — 자회사 출자·자금지원 리스크가 이사회에 충분히 보고되지 않음"),
]
# 판정 누락 재검토에서 걸렸으나 N 으로 둔 지적(판단) — 기록용
KEPT_N = [
    ("20240221", 1, "자회사 금융사고·검사·준법감시 지적 — 「PF대출 등 고위험 업무에 대한 적정성 점검」은 준법감시 테마점검 안의 글(내부통제)"),
    ("20220729", 23, "자회사 검사계획에 위험·문제점 반영 — 감사(검사) 기능 지적"),
    ("20220729", 22, "준법감시계획에 위험요인 반영 — 준법감시 지적"),
    ("20221214", 6, "복합점포 금융사고 보고 절차 — 33조 ①4호(평판위험 전이) 글귀 없음"),
    ("20240726", 9, "겸직 위험평가(징계 사실 검토) — 겸직 승인 내부통제"),
    ("20260723", 10, "최고경영자 성과보상 유보·환수 기준 — 위험 글귀는 법 취지 인용뿐"),
    ("20220729", 29, "배당가능이익 한도 산정 — 상법 배당 계산(자본계획 지적 아님)"),
]
ART_RE = re.compile(r"제\s*[0-9◉▣◈●○□■▲△▽▼◇◆☆★♤♧♠♣⊙⊜◎◑▨▩◐▦▧▤▥▢▯XＸ]+\s*조(?:\s*의\s*\d+)?(?:\s*제?\s*[0-9①-⑳]+\s*항)?"
                    r"(?:\s*제?\s*\d+\s*호)?")
SEC_SIGN_RE = re.compile(r"§\s*\d+(?:\s*[①-⑳])?(?:\s*\d+\.)?")
ANNEX_RE = re.compile(r"[<\[［]\s*별\s*표\s*[0-9][0-9\-의]*\s*[>\]］]")
NAME_RE = re.compile(r"[｢「]\s*[^｣」\n]{1,60}?\s*[｣」]|[’‘][^’‘\n]{1,40}[’‘](?=\s*제\s*[0-9◉▣◈●○□■▲△▽▼◇◆☆★♤♧♠♣⊙⊜◎◑▨▩◐▦▧▤▥▢▯XＸ]+\s*조)")


def wide_cites(body):
    """지적 글(줄바꿈은 한 칸) → 넓혀 찾은 조문·규정 표기 글. 원문 글자(공백만 한 칸으로)."""
    b = re.sub(r"\s*\n\s*", " ", body)
    parts = []
    for lab, rx in (("조문 표기", ART_RE), ("§ 표기", SEC_SIGN_RE), ("별표", ANNEX_RE), ("규정·법규 이름", NAME_RE)):
        got = []
        for m in rx.finditer(b):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            if s not in got:
                got.append(s)
        if got:
            parts.append("%s: %s" % (lab, " ; ".join(got)))
    return " · ".join(parts)


def fix_bracket(c, whole):
    if ns(c) in whole:
        return c
    for a, b in (("｢", "「"), ("｣", "」")):
        c2 = c.replace(a, b)
        c = c2 if ns(c2) in whole else c
    c3 = c.replace("｢", "「").replace("｣", "」")
    return c3 if ns(c3) in whole else c


def pdf_created(path):
    from pypdf import PdfReader
    v = str((PdfReader(path).metadata or {}).get("/CreationDate", ""))
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", v)
    return "%s-%s-%s %s:%s:%s" % m.groups() if m else ""


BASE_COMMIT = "ec4a426"                                                # 13차 1차 수집 커밋 — 보정 전 산출물


def git_base(path):
    import subprocess
    try:
        return subprocess.run(["git", "show", "%s:%s" % (BASE_COMMIT, path)], capture_output=True, check=True).stdout
    except Exception:
        return None


def _same(v):
    return "같음" if v else "확인 못 함" if v is None else "**다름**"


def _gen(F, out_dir, tag):
    F.OUT_PRESS = os.path.join(out_dir, tag + "_press.md")
    F.OUT_EXAM = os.path.join(out_dir, tag + "_exam.md")
    F.LIST_CSV = os.path.join(out_dir, tag + "_list.csv")
    with redirect_stdout(io.StringIO()):
        F.build_press()
        F.build_exam()
    return F.OUT_PRESS, F.OUT_EXAM, F.LIST_CSV


def _rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


CATS = [("원본 글과 다름", "인용 글이 원본과 다름"), ("게시글 URL·게시판 표기 없음", "9-2-4 인용 머리에 게시판·게시글 URL 없음"),
        ("쪽 표기 다름 —", "9-2-4 인용 머리 쪽 표기가 다시 센 쪽과 다름(「대조 못 함」 포함)"), ("쪽 표기 없음", "9-5 문서 머리 인용에 쪽 표기 없음"),
        ("쪽 표기 p.", "9-5 쪽 표기가 원본과 다름"), ("판 표기가 2016.8.1판 아님", "9-5 조 제목 출처가 2017.4.1판으로 적힘(note 줄·색인 머리)"),
        ("조 번호(조 제목)·(판단) 표시 없음", "9-2-4 note 의 조 번호에 조 제목 없음"), ("1절 표", "9-2-4 1절 표 조 칸에 조 제목 없음"),
        ("모범규준 대응 note 없음", "9-2-4 자료 묶음(Q3·Q7·Q8)에 조 번호 없음"), ("없는 파일 이름", "9-2-4 없는 파일 이름을 가리킴"),
        ("CSV 칸 없음", "CSV 에 조 제목·넓혀 찾은 표기 등 칸 없음"), ("인용조문", "CSV·md 인용조문 낫표가 원문과 다름"),
        ("원본 글에 없음(근거", "md 근거 조문 칸 낫표가 원문과 다름"), ("지시서 항목", "지시서 항목 대조 표 없음"),
        ("맨 끝 절", "「검증 기록」 절 없음"), ("조 제목 다름", "조 제목이 조목록과 다름")]


def _cats(R):
    """문제 줄 → 분류별 수."""
    c = {}
    for ln in R.lines:
        if not ln.startswith("  !!"):
            continue
        k = next((lab for key, lab in CATS if key in ln), "기타")
        c[k] = c.get(k, 0) + 1
    return c


def fix():
    import web13_fss as F                                            # 원 생성기 — import 만(고치지 않음)
    T = titles2016()
    tmp = tempfile.mkdtemp(prefix="verify13_web_")
    # 0. 보정 전: 원 생성기 그대로 다시 만든 판(보정 전 파일과 바이트 같아야 함)
    before = _gen(F, tmp, "before")
    same = {p: (None if git_base(p) is None else git_base(p) == open(b, "rb").read()) for p, b in zip((MD_P, MD_E, CSV_E), before)}
    R0 = verify(write=False, files=before, quiet=True)
    # 1. 고친 설정으로 다시 만들기
    PQ0 = list(F.PQ)
    add_art = {("Q3", "리스크 중심 감독체계 구축 계획 — 추진 경과 상자"):
               "제5장 내부자본 적정성 평가 및 관리 — 36조(%s)~49조(%s)(판단 — 검증 때 붙임: Q1·Q2 와 같은 ORSA 도입 주제)" % (T[36], T[49]),
               ("Q7", "2. 내부모형 점검항목 및 평가기준 󰊴"):
               art_label("37·44", T) + "(판단 — 검증 때 붙임: Q4 와 같은 ORSA·내부모형 연계 주제)",
               ("Q8", "별첨1 26년 보험 감독 부문 업무설명회 자료 p.17(슬라이드 쪽 번호 16)"):
               art_label("36·48", T) + "(판단 — 검증 때 붙임: ORSA 도입 확대는 적용대상, ORSA 보고서는 보고)"}
    PQ1 = []
    for q in PQ0:
        qid, boards, fn, st, en, art, note = q
        if art:
            if art.startswith("제5장"):
                art = "제5장 내부자본 적정성 평가 및 관리 — 36조(%s)~49조(%s)(판단)" % (T[36], T[49])
            else:
                art = art_label(re.match(r"([\d·~]+)조", art).group(1), T) + "(판단)"
        art = add_art.get((qid, note), art)
        PQ1.append((qid, boards, fn, st, en, art, note))
    CL0 = F.CLASS
    CL1 = json.loads(json.dumps(CL0))
    CL1 = {d: {int(k): tuple(v) for k, v in m.items()} for d, m in CL1.items()}
    memo = {}
    for d, k, old, pj, art, topic in PATCH_CLASS:
        cur = CL1.get(d, {}).get(k)
        if (cur[:2] if cur else None) != (tuple(old) if old else None):
            raise SystemExit("PATCH_CLASS 기대값 다름: %s %d %r" % (d, k, cur))
        CL1.setdefault(d, {})[k] = (pj, art, (cur[2] + topic) if cur else topic)
        memo[(d, k)] = "검증 2026-10-07(판단): " + ("판정 N→%s, 조 %s" % (pj, art) if not cur else "조 %s→%s" % (cur[1], art))
    MT0 = F._mobeom_titles
    F.PQ, F.CLASS, F._mobeom_titles = PQ1, CL1, (lambda: T)
    try:
        after = _gen(F, tmp, "after")
        # 문서별 항목(넓혀 찾은 표기·발췌용) — 원 생성기의 항목 나누기 그대로
        docs = exam_docs()
        items_by_sha = {sha: F.parse_items(doc["path"] + ".merged.txt") for sha, doc in docs.items()}
    finally:
        F.PQ, F.CLASS, F._mobeom_titles = PQ0, CL0, MT0
    srcs = press_sources()
    p_text, p_changes = post_press(_rd(after[0]), T, srcs)
    rows, csv_changes = post_csv(after[2], T, docs, items_by_sha, memo)
    e_text, e_changes = post_exam(_rd(after[1]), T, docs, items_by_sha, rows)
    # 2. 검증 기록 절
    stats = dict(R0=R0, same=same)
    p_text = p_text.rstrip("\n") + "\n\n" + press_record(_rd(before[0]), p_text, p_changes, stats, srcs, T) + "\n"
    e_text = e_text.rstrip("\n") + "\n\n" + exam_record(_rd(before[1]), e_text, e_changes, csv_changes, stats, rows, docs,
                                                          items_by_sha, read_csv(before[2]), T) + "\n"
    with open(MD_P, "w", encoding="utf-8") as f:
        f.write(p_text)
    with open(MD_E, "w", encoding="utf-8") as f:
        f.write(e_text)
    cols = list(rows[0].keys())
    with open(CSV_E, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    for p in after + before:
        os.remove(p)
    os.rmdir(tmp)
    print("fix →", MD_P, MD_E, CSV_E, "· 보정 전 문제", R0.bad)


# ── 9-2-4 보정 ────────────────────────────────────────────────────────────────
TAB_P = {"Q1": "ch5", "Q2": "ch5", "Q3": "ch5+", "Q4": "37·44", "Q5": "36·37·39·41", "Q6": "36", "Q7": "37·44+", "Q8": "36·48+",
         "Q9": "36·39·41"}


def post_press(text, T, srcs):
    L = text.split("\n")
    ch = []
    ch5 = "제5장 내부자본 적정성 평가 및 관리(36조(%s)~49조(%s))" % (T[36], T[49])
    for i, ln in enumerate(L):
        if ln.startswith("| Q") and ln.count("|") >= 7:
            cells = ln.split(" | ")
            q = cells[0].strip("| ")
            spec = TAB_P[q]
            plus = spec.endswith("+")
            spec = spec.rstrip("+")
            new = (ch5 if spec == "ch5" else art_label(spec, T)) + (" — 검증 때 붙임" if plus else "")
            old_cell = cells[-1].rstrip(" |")
            cells[-1] = new + " |"
            L[i] = " | ".join(cells)
            ch.append(("1절 표 %s 모범규준 조 칸" % q, old_cell, new))
    for x in press_quotes(L):
        m = HDR_OLD.match(x["hdr"])
        if not m:
            continue
        g = m.groupdict()
        src = find_press_src(g["name"], g["sha"], srcs)
        exp = press_expected(x["text"], src, x["boards"], srcs)
        new = "인용 — %s · 원파일 「%s」(%s 첨부) · sha256 %s… · 게시글 %s · %s · 수집 %s" % (
            g["label"], g["name"], board_label(src["site"], src["no"]), g["sha"], src["meta"].get("게시글URL", ""), exp, g["fa"])
        L[x["hdr_i"]] = new
        ch.append(("hdr", x["q"], g["label"], g["pages"], exp))
    out = []
    for ln in L:
        if ln.startswith("- 쪽: 인용마다 같은 게시글의 PDF 첨부에서"):
            ln += (" → 검증(2026-10-07): 쪽을 `scripts/dart/verify13_web.py` 로 다시 셌다 — 같은 게시글의 PDF(pypdf 기본 모드 글)에서 인용 줄마다 "
                   "① 공백·「|」 뺀 줄 글 그대로 ② 가운데 10자 ③ 2자 이상 낱말의 80% 이상이 한 쪽에 있음 순서로 찾고, ③으로만 찾은 쪽은 「(낱말 대조)」, "
                   "PDF 글에서 못 찾은 줄 수는 「못 찾은 줄 n/전체」로 적었다. 인용 머리마다 게시판·글번호와 게시글 URL 을 넣었다. "
                   "2016-03-30 PDF(금융위 72075·금감원 12368)는 PDF 한 쪽에 인쇄 쪽 2개가 든 모아찍기 판이라 p.N 은 PDF 쪽 순서다(인쇄 쪽 번호와 다름).")
        elif ln.startswith("- 한계: 사이트 게시판 검색") and "9-2_ORSA_보험기준.md" in ln:
            ln = ln.replace("`handoff/13차_산출물/9-2_ORSA_보험기준.md` 몫이다.",
                            "`handoff/13차_산출물/9-2-1_2_ORSA_연혁.md`(제7-5조·제5-6조의2·[별표 37] 연혁)·`handoff/13차_산출물/9-2-3_5_별표37_별표22.md` "
                            "몫이다(검증 2026-10-07: 원래 `9-2_ORSA_보험기준.md` 로 적혀 있었으나 그런 파일은 없음 — 실제 9-2 산출물 이름으로 바로잡음).")
            ch.append(("한계 줄 파일 이름", "`handoff/13차_산출물/9-2_ORSA_보험기준.md`",
                       "`handoff/13차_산출물/9-2-1_2_ORSA_연혁.md`·`handoff/13차_산출물/9-2-3_5_별표37_별표22.md`"))
        elif ln.startswith("- 모범규준 조 번호: 사용자 지시서가 9-2 에"):
            ln += (" → 검증(2026-10-07): 조 제목 기준을 기준판 2016.8.1판(`dart_out/risk13/모범규준_조목록.csv`, 원문 "
                   "`handoff/13차_산출물/9-4_모범규준_원문.md`)으로 바꾸고 조 번호마다 「N조(조 제목)」으로 적었다. 2017.4.1판 첨부 hwp 는 2016.8.1판과 "
                   "sha256 이 같아(9-4_모범규준_원문.md 1절) 제목은 같다. 조 번호가 없던 Q3·Q7·Q8 에도 붙였다(판단 — 「검증 때 붙임」).")
            ch.append(("모범규준 조 번호 머리 줄", "조 제목 2017.4.1판 원본 기준", "2016.8.1판 조목록 기준 + 「N조(조 제목)」 + Q3·Q7·Q8 붙임"))
        elif ln.startswith("- note: 2016-03-30 자료는 개정 경과를"):
            ln += (" → 검증 대조(2026-10-07, `handoff/13차_산출물/9-2-1_2_ORSA_연혁.md` 0절 요약): 감독규정 제7-5조에 「자체 위험 및 지급여력 평가 체제」 "
                   "문구가 처음 든 판은 2016.04.01 발령·시행(금융위원회고시 제2016-15호 — 제7-5조제1항 개정 규정은 부칙 제1조로 2017.1.1 시행)이라 이 자료의 "
                   "「4.1일부터 시행」·「‘17.1.1일」과 맞는다. 다만 세칙 제5-6조의2 가 처음 나온 판은 2016.04.28 발령(부칙상 2017.1.1 시행)으로, 이 자료의 "
                   "「보험업감독업무시행세칙(3.30일 확정)」과 날짜가 다르다(원문과 다른 곳 — 3.30 확정분과 4.28 발령분의 관계는 자료에 설명 없음, 판단 보류).")
        elif ln.startswith("- note: 2026-06-29 자료의 적용 시기 표현이 두 곳에서 다르다"):
            ln += (" → 검증 대조(2026-10-07, 9-2-1_2_ORSA_연혁.md 3-5): 세칙 부칙(2026.6.29) 제1조 시행일 2026.6.30, 제2조 계리적 가정 일부 "
                   "2026.12.31부터 시행할 수 있음, 제3조 「‘자체 위험 및 지급여력평가체제’를 처음 도입하는 보험회사는 자체 위험 및 지급여력 평가를 2027년 1월 1일부터 "
                   "시행」. 보도자료 두 문구에는 2027.1.1 이 나오지 않는다(원문과 다른 곳; 상자의 「’26년 12월말부터 적용」은 부칙 제2조·제4조 쪽으로 보임 — 판단).")
        out.append(ln)
        if ln.startswith("- 작업: 13차 9-2-4"):
            out.append("- 검증: 2026-10-07 `python3 scripts/dart/verify13_web.py fix` 로 원본(같은 폴더의 hwp2md·pypdf 글, .meta.json)과 다시 대조·보정 "
                       "— 인용 머리에 게시판·게시글 URL 을 넣고 쪽을 다시 셌으며, 모범규준 조 번호에 2016.8.1판 조 제목을 붙였다. 바뀐 곳(전·후)·지시서 항목 대조·"
                       "「추출 범위에 없음」 반박 결과는 맨 끝 「검증 기록(2026-10-07)」 절. 대조만 다시 하려면 인자 없이 실행.")
    return "\n".join(out), ch


def _excerpt(q, rx):
    m = re.search(rx, q, re.S)
    return m.group(0) if m else ""


def press_record(before, after, ch, stats, srcs, T):
    L = [VERIFY_HEAD, ""]
    qs_after = press_quotes(after.split("\n"))
    R0 = stats["R0"]
    cats = _cats(R0)
    L += ["- 방법: `python3 scripts/dart/verify13_web.py fix`(보정) → 인자 없이 실행(대조). 원본은 새로 받지 않았다(`dart_out/raw/web13/fss/press/` 의 "
          "hwp2md 글·pypdf 글·.meta.json 만 읽음). 대조 결과 전문 `dart_out/risk13/verify13_web.txt`.",
          "- 보정은 원 생성기(`scripts/dart/web13_fss.py` 의 build-press, 파일은 고치지 않음)를 고친 설정(인용 note 의 조 번호)으로 다시 돌린 뒤 덧붙이는 "
          "방식이다. 원 생성기를 설정 그대로 다시 돌린 판과 보정 전 파일(커밋 %s 의 판)을 바이트로 견줌: %s." % (BASE_COMMIT, _same(stats["same"].get(MD_P))),
          "- 대조한 인용: 코드 블록 %d개. 인용 머리의 원파일·sha256 으로 찾은 출처(hwp 는 hwp2md 글 — 표기 「<br>」→줄바꿈·「\\|」→「|」만 되돌림, "
          "pdf 는 merged 글)와 공백만 무시하고 글자 대조 — %d개 모두 일치(보정 전·후 같음). 글자를 고친 인용은 없다." % (len(qs_after), len(qs_after)),
          "- 보정 전 대조(이 절의 검사 기준으로 두 md·CSV 를 함께 셈): 문제 %d — %s." % (
              R0.bad, ", ".join("%s %d" % (k, v) for k, v in sorted(cats.items(), key=lambda kv: -kv[1]))), ""]
    pchg = [c for c in ch if c[0] == "hdr" and set(re.findall(r"p\.(\d+)", re.sub(r"「[^」]*」", "", c[3]))) !=
            set(re.findall(r"p\.(\d+)", re.sub(r"「[^」]*」", "", c[4])))]
    L += ["### 1. 고친 곳(전·후)", "", "#### 1-1 인용 머리 — 출처 표기(게시판·게시글 URL)와 쪽", "",
          "모든 인용 머리에 「(게시판 글번호 첨부)」와 「게시글 URL」을 넣었다(전: 원파일·sha256·쪽·수집만 — 공통 규칙의 [문서명 · URL · 쪽 · 수집일] 가운데 "
          "URL 이 빠져 있었음). 쪽 표기는 아래처럼 바뀌었다(전 → 후). 쪽 번호 자체가 바뀐 인용 %d개: %s. 보정 전 「대조 못 함」 %d개 가운데 %d개는 다시 세어도 "
          "「찾지 못함」. 나머지는 게시판·파일 이름 표기와 「낱말 대조」「못 찾은 줄」 덧말만 바뀌었다." % (
              len(pchg), "; ".join("%s %s(전 %s → 후 %s%s)" % (
                  c[1], c[2], ",".join("p." + x for x in sorted(set(re.findall(r"p\.(\d+)", re.sub(r"「[^」]*」", "", c[3]))), key=int)) or "대조 못 함",
                  ",".join("p." + x for x in sorted(set(re.findall(r"p\.(\d+)", re.sub(r"「[^」]*」", "", c[4]))), key=int)),
                  "" if "대조 못 함" in c[3] else " — 보정 전 쪽은 줄 가운데 10자가 1쪽 요약 상자의 비슷한 글에 먼저 걸린 것으로 보임(판단), 줄 글 전체는 뒤 쪽에만 있음")
                  for c in pchg),
              sum(1 for c in ch if c[0] == "hdr" and "대조 못 함" in c[3]),
              sum(1 for c in ch if c[0] == "hdr" and "대조 못 함" in c[3] and "찾지 못함" in c[4])), "",
          "| # | Q | 인용 | 전(쪽 표기) | 후(쪽 표기) |", "|---|---|---|---|---|"]
    k = 0
    for c in ch:
        if c[0] == "hdr":
            k += 1
            L.append("| %d | %s | %s | %s | %s |" % (k, c[1], c[2].replace("|", "｜"), c[3].replace("|", "｜"), c[4].replace("|", "｜")))
    L += ["", "#### 1-2 그 밖의 줄", ""]
    for c in ch:
        if c[0] != "hdr":
            L.append("- %s — 전: %s → 후: %s" % c)
    L += ["- 머리 bullet 「쪽」「모범규준 조 번호」, 5절 note 2개(2016-03-30 개정 경과, 2026-06-29 적용 시기)는 지우지 않고 끝에 「→ 검증 …」 글을 덧붙였다.",
          "- 「- 검증:」 머리 bullet 1줄을 새로 넣었다.", ""]
    # 지시서 항목
    qtxt = {x["q"]: [] for x in qs_after}
    for x in qs_after:
        qtxt[x["q"]].append(x["text"])

    def ev(q, rx):
        for t in qtxt.get(q, []):
            s = _excerpt(t, rx)
            if s:
                return "「%s」(%s)" % (s.replace("|", "｜").replace("\n", " "), q)
        return "(못 찾음 %s)" % q

    L += ["### 2. 지시서 항목 대조(REQUEST13 「9-2 ORSA 연혁과 보험 쪽 기준」 4번)", "",
          "| 지시서 항목 | 상태 | 근거(인용 블록의 글) 또는 찾은 방법 |", "|---|---|---|",
          "| ORSA 도입 발표 원문과 날짜 | 받은 글 | 1절 날짜순 목록 Q1~Q9(날짜는 각 Q 의 보도·배포일 인용). 예: %s, %s |" % (
              ev("Q1", r"보험회사의 자체적인 리스크관리 수준[^\n]*도입 추진"), ev("Q5", r"’17년부터 “자체위험 및 지급여력 평가제도”\(ORSA\)를 도입")),
          "| 도입 로드맵 | 받은 글 | %s, %s, %s |" % (ev("Q1", r"재무건전성 감독제도 선진화 종합로드맵"), ev("Q1", r"자체위험․지급여력평가제도"),
                                                 ev("Q1", r"\(추진일정\)[^\n]*방안을 마련하여")),
          "| 시행 시기 | 받은 글 | %s, %s, %s, %s |" % (ev("Q1", r"시범운영\(‘15∼’16년\)을 거쳐 ‘17년 시행"), ev("Q2", r"‘17\.1\.1일"),
                                                   ev("Q9", r"’26년 6월말 결산부터 적용하는 것을 원칙으로"), ev("Q9", r"’26년 2분기 결산시부터 적용")),
          "| 유예 허용 | 받은 글 | %s, %s, %s |" % (ev("Q5", r"필요시 이사회 승인절차를 거쳐 제도시행을 유예 가능"),
                                                 ev("Q5", r"42개사는 ’18년 이후로 도입을 유예"), ev("Q9", r"소형\(수입보험료 5천억원 이하\) 및 외국계 지점 회사는 시행 유예 가능")),
          "", "note: 근거 칸의 「」 글은 스크립트가 인용 블록에서 그대로 잘라 넣었다(대조 때 인용 블록 안에 있는지 다시 확인).",
          "", "채운 항목: 지시서 4개 항목은 보정 전에도 받은 글이 있었다(빠진 항목 없음). 이번에 채운 것 — 자료 묶음 Q3·Q7·Q8 의 모범규준 조 번호(판단), "
          "모든 조 번호의 조 제목(2016.8.1판), 인용 머리 34개의 게시판·게시글 URL, 2016-03-30 PDF 쪽 2곳(대조 못 함 → p.1·p.3), Q9 향후 계획 인용의 쪽 바로잡음, "
          "5절 note 2개의 9-2-1_2 산출물 대조 결과.", ""]
    # 반박
    cand = read_csv(CAND_CSV)
    win = lambda a, b: [r for r in cand if a <= r["등록일"][:7] <= b]
    texts = [x for x in os.listdir(PF) if x.endswith(".txt") or x.endswith(".hwp.md")]
    WIDE = re.compile(r"ORSA|O\.R\.S\.A|자\s*체\s*위\s*험|자\s*체\s*리\s*스\s*크|지\s*급\s*여\s*력\s*평\s*가|Own\s*Risk|위험\s*및\s*지급|리스크\s*및\s*지급|"
                      r"리스크와\s*지급|내부\s*자본\s*적정성|자본\s*적정성\s*평가|자체\s*평가")
    quoted_boards = {b for x in qs_after for b in x["boards"]}
    new_hits = []
    for x in sorted(texts):
        mm = re.match(r"(fss|fsc)_(\d+)_", x)
        if not mm or (mm.group(1), mm.group(2)) in quoted_boards:
            continue
        t = read(os.path.join(PF, x))
        hs = sorted(set(ns(m.group(0)) for m in WIDE.finditer(t)))
        if hs:
            new_hits.append("%s(%s)" % (x, ",".join(hs)))
    views = [x for x in os.listdir(PV) if x.endswith(".body.txt")]
    yego = [x.split(".")[0] for x in sorted(views) if re.search(r"사전\s*예고|변경\s*예고|입법\s*예고", read(os.path.join(PV, x)))]
    art_hits = [x for x in sorted(texts) if re.search(r"5-6\s*조의\s*2|별표\s*37", read(os.path.join(PF, x)))]
    q2 = [x for x in qs_after if x["q"] == "Q2"]
    q2pages = "; ".join("%s → %s" % (HDR_NEW.match(x["hdr"]).group("label"), HDR_NEW.match(x["hdr"]).group("pages")) for x in q2
                        if HDR_NEW.match(x["hdr"]) and "보도·배포일" not in x["hdr"])
    L += ["### 3. 「추출 범위에 없음」 반박 시도", "",
          "| # | 주장(보정 전 md·수집 보고) | 결과 | 다시 찾은 방법·검색어(같은 출처, 새로 받지 않음) |", "|---|---|---|---|",
          "| 1 | 2026.4 세칙 개정 사전예고(‘26.4.8~5.18)를 알리는 별도 보도자료 | 실패 — 추출 범위에 없음 | 후보 CSV(%d건) 등록일 2026-04~2026-05: %d건. "
          "받은 게시글 본문 %d건에서 「사전예고」「변경예고」「입법예고」(띄어쓰기 변형 포함): %s — 세칙 4월 예고 글은 없음(87205 는 이 2026-06-29 자료 자체, "
          "87701 은 감독규정 9.11 예고) |" % (len(cand), len(win("2026-04", "2026-05")), len(views), " ".join(yego)),
          "| 2 | 세칙 제5-6조의2·[별표 37] 신설 시점에 맞춘 보도자료(2026-06-29 건 외) | 실패 — 추출 범위에 없음 | 9-2-1_2 산출물의 신설 판 발령일 2016.04.28 "
          "앞뒤로 후보 CSV 등록일 2016-04~2016-05: %d건(%s) — 제목에 세칙·ORSA 없음. 받은 첨부 글 %d개에서 「5-6조의2」「별표 37」(띄어쓰기 변형): %d개 |" % (
              len(win("2016-04", "2016-05")), "; ".join("%s %s" % (r["등록일"], r["제목"][:24]) for r in win("2016-04", "2016-05")),
              len(texts), len(art_hits)),
          "| 3 | 2024-03 언론 보도(소형사 ORSA 면제 개편)에 대응하는 당국 보도자료 | 실패 — 추출 범위에 없음 | 후보 CSV 등록일 2024-02~2024-04: %d건(%s) — 받은 "
          "첨부에 ORSA 낱말 없음(3절). 받은 첨부 글에서 「소형」「면제」가 ORSA·자체위험과 같은 줄에 나오는 곳: 0 |" % (
              len(win("2024-02", "2024-04")), "; ".join("%s %s" % (r["등록일"], r["제목"][:24]) for r in win("2024-02", "2024-04"))),
          "| 4 | 3절 「받아 보았으나 ORSA 낱말 없음」 보도자료와 그 밖의 받은 첨부의 ORSA 언급 | 실패 — 새 ORSA 언급 없음(추출 범위에 없음) | 인용하지 않은 "
          "게시글의 첨부 글 전부를 넓힌 정규식 `%s` 로 다시 찾음 — 걸린 곳: %s. 걸린 「자본적정성평가」는 「경영실태평가(RAAS) 자본적정성 평가 등급구간」으로 "
          "ORSA 가 아님(판단). 후보 192건 가운데 첨부를 받지 않은 글은 여전히 범위 밖 |" % (WIDE.pattern.replace("|", "｜"), "; ".join(new_hits) or "없음"),
          "| 5 | 2016-03-30 자료 3개 인용(개정 경과·시행 일정·시행일 표)의 PDF 쪽(보정 전 「PDF 쪽 대조 못 함」) | 일부 성공 | 줄 대조에 낱말 대조(2자 이상 "
          "낱말 80%%)를 더함 — %s. 「시행 일정」 두 줄(「□ 관보게재 …」「<보험업법 시행령 등 …>」)은 두 PDF 의 pypdf 글에 없다(PDF p.3 에는 「시행 일정」 "
          "제목 글자만 있음 — 해당 줄은 PDF 글로 뽑히지 않음, 그림 등으로 보임: 판단) |" % q2pages,
          ""]
    L += ["### 4. 남은 문제", "",
          "- 게시판 검색은 첨부 안을 찾지 않는다 — 후보 %d건 가운데 게시글·첨부를 받아 본 것은 %d건(인용한 게시글 %d + 3절 %d)뿐이다(추출 범위 한계, 그대로 남음)." % (
              len(cand), len({(s["site"], s["no"]) for s in srcs}), len(quoted_boards), len({(s["site"], s["no"]) for s in srcs}) - len(quoted_boards)),
          "- 「시행 일정」 두 줄은 hwp 글로만 확인되고 PDF 쪽을 붙이지 못했다.",
          "- 모범규준 조 번호는 모두 판단이다(보험 ORSA 를 금융지주 모범규준 제5장 내부자본 적정성 평가 및 관리에 대응시킨 것).",
          "- 금감원 저작권 정책의 「직접 링크 시 통지」 문구 — 이 md 를 웹에 게시할 때 유의(머리 bullet 그대로).",
          "- 원 생성기(`web13_fss.py build`)를 다시 돌리면 이 보정이 지워진다 — 그 뒤에는 `python3 scripts/dart/verify13_web.py fix` 를 다시 돌릴 것."]
    return "\n".join(L)


# ── 9-5 보정 ──────────────────────────────────────────────────────────────────
def post_csv(path, T, docs, items_by_sha, memo):
    rows = read_csv(path)
    ch = []
    k_of = {}
    created = {}
    for r in rows:
        sha = r["sha256"]
        k_of[sha] = k_of.get(sha, 0) + 1
        k = k_of[sha]
        it = items_by_sha[sha][k - 1]
        whole = ns("".join(t for _, t in doc_pages(docs[sha])))
        for col in ("인용조문", "관련규정"):
            parts = [x for x in r[col].split(" ; ") if x.strip()]
            fixed = [fix_bracket(x, whole) for x in parts]
            if fixed != parts:
                ch.append(("CSV %s %s %s %s" % (r["지주"], r["제재조치요구일(목록)"], r["번호"], col), " ; ".join(parts), " ; ".join(fixed)))
                r[col] = " ; ".join(fixed)
                r.setdefault("_memo", []).append("%s 낫표를 원문대로(｢｣→「」)" % col)
        if CH5_OLD in r["모범규준_조(판단)"]:
            r["모범규준_조(판단)"] = r["모범규준_조(판단)"].replace(CH5_OLD, CH5)
        r["모범규준_조제목(2016.8.1판)"] = art_title_cell(r["모범규준_조(판단)"], T)
        r["넓혀찾은_조문표기(검증)"] = wide_cites("\n".join(it["본문"])) or "추출 범위에 없음(넓힌 낱말로도 없음)"
        if sha not in created:
            created[sha] = pdf_created(docs[sha]["path"])
        r["PDF문서정보_작성일(참고·공개일아님)"] = created[sha]
        d = r["제재조치요구일(목록)"] if r["목록"].startswith("금융회사 경영유의") else None
        m = memo.get((d, k)) if d else None
        r["검증메모"] = " ; ".join(([m] if m else []) + r.pop("_memo", []))
    return rows, ch


def post_exam(text, T, docs, items_by_sha, rows):
    L = text.split("\n")
    out, ch = [], []
    n_lab = n_ch5 = n_head = n_cite = n_none = 0
    n_wide = {True: 0, False: 0}
    sha = None
    blocks = {s: t for s, e, t in code_blocks(L)}
    i = 0
    nb = {"메리츠": [], "한국투자": []}
    allrows = read_csv(IMPR_ALL)
    for r in allrows:
        for key in nb:
            if key in r["제재대상기관"]:
                nb[key].append(r["제재대상기관"])
    sanc = read_csv(SANC_LIST)
    while i < len(L):
        ln = L[i]
        m = re.search(r"sha256 ([0-9a-f]{64})", ln)
        if m:
            sha = m.group(1)
        if CH5_OLD in ln:
            ln = ln.replace(CH5_OLD + "조(판단)", CH5 + "(판단)").replace(CH5_OLD, CH5)
            n_ch5 += 1
        if ln.startswith("- note: 모범규준 조 제목(2017.4.1판) — "):
            ln = ln.replace("- note: 모범규준 조 제목(2017.4.1판) — ", "- note: 모범규준 조 제목(2016.8.1판 — `dart_out/risk13/모범규준_조목록.csv`) — ")
            n_lab += 1
            if "11조(" in ln:
                ln += (" · 11조는 2016.8.1판에서 ①~⑤·⑦항이 <삭제 2016. 8. 1.>, ⑥(업무)·⑧(평가권한 등으로 위험관리 통할)·⑨(개선권고)만 남음"
                       "(9-4_모범규준_원문.md 4절 제11조) — 선임 자격을 정한 ①(2012.3.13 제정판 「리스크관리에 대한 지식과 경험을 갖춘 자」, 2016.7 예고안 "
                       "「위험관리에 대한 지식과 경험을 갖춘 자」)은 2016.8.1판에 없다(판단: 전문성 지적은 삭제된 ①의 주제, 성과평가·통할 지적은 남은 ⑧의 주제)")
        if ln.startswith("| 모범규준 조 | 조 제목(2017.4.1판) |"):
            ln = ln.replace("조 제목(2017.4.1판)", "조 제목(2016.8.1판)")
            n_lab += 1
        if ln.startswith("| %s | " % CH5):
            ln = ln.replace("| 내부자본 적정성 평가 및 관리(특정 조 없음 — 규제자본비율 산출 등) |",
                            "| 제5장 내부자본 적정성 평가 및 관리(36조~49조) 가운데 37~49조 — 특정 조 없음(규제자본비율 산출 등) |")
        if ln == "문서 머리(조치내용) — 글자 그대로:" and (i + 2) in blocks and sha in docs:
            pg = page_spans(doc_pages(docs[sha]), blocks[i + 2])
            ln = "문서 머리(조치내용) — 글자 그대로 · 쪽 %s:" % ",".join("p.%d" % n for n in pg)
            n_head += 1
        if ln.startswith("- 근거로 든 조문(문서 글에서") and sha in docs:
            whole = ns("".join(t for _, t in doc_pages(docs[sha])))
            head, body = ln.split("): ", 1)
            if body == "문서 글에 조문 인용 없음":
                new_body = "문서 글에 「｢…｣ 제N조」 꼴 인용 없음(아래 넓혀 찾은 표기 참조)"
            else:
                new_body = " ; ".join(fix_bracket(x, whole) for x in body.split(" ; "))
            if body == "문서 글에 조문 인용 없음":
                n_none += 1
            elif new_body != body:
                ch.append(("(근거로 든 조문 줄) 낫표를 원문대로", body, new_body))
                n_cite += 1
            ln = head + "): " + new_body
            # 넓혀 찾은 표기 — 다음 코드 블록 글에서
            j = i + 1
            while j < len(L) and L[j] != "```text":
                j += 1
            wc = wide_cites(blocks.get(j, "")) if j in blocks else ""
            out.append(ln)
            n_wide[bool(wc)] += 1
            out.append("- 넓혀 찾은 조문·규정 표기(검증 2026-10-07 — 「제N조」(가림 기호 조 번호 「제▣▣조」 포함)·「§N」·「<별표 N>」·「｢…｣」 꼴, "
                       "원문 글자 그대로): %s" % (wc or "추출 범위에 없음(이 낱말들로 찾았으나 없음)"))
            i += 1
            continue
        if ln.startswith("- 문서의 「< 관련규정 >」 칸: ") and sha in docs:
            whole = ns("".join(t for _, t in doc_pages(docs[sha])))
            body = ln.split("칸: ", 1)[1]
            nbd = " ; ".join(fix_bracket(x, whole) for x in body.split(" ; "))
            if nbd != body:
                ch.append(("(관련규정 칸 줄) 낫표를 원문대로", body, nbd))
            ln = ln.split("칸: ", 1)[0] + "칸: " + nbd
        if ln.startswith("- 「공개일」: 게시판에는 공개(게시)일 칸이 없고"):
            ln += (" → 검증(2026-10-07): 받은 목록 화면(경영유의 공시 전체 72쪽·지주 검색 2쪽, 검사결과제재 지주 검색 2쪽)의 칸은 「일련번호(번호)·제재대상기관·"
                   "제재조치요구일·제재조치요구내용·관련부서·조회수」뿐이고, 목록·상세 HTML 에서 「등록일」「게시일」「공시일」「공개일」「작성일」 낱말 0건(검사결과제재 "
                   "상세 화면 칸은 「금융기관명·제재조치일·관련부서·기관/임원/직원제재대상·첨부파일·제재대상사실」) — 공개일은 추출 범위에 없음. 참고로 공개안 PDF 의 "
                   "문서정보 작성일(CreationDate)을 검증 기록 4절 표와 CSV 칸에 적었다(공개일이 아님).")
        if ln.startswith("- 모범규준 조 번호: 지시서가 9-5 에 조 번호를 주지 않았으므로"):
            ln += (" → 검증(2026-10-07): 조 제목 기준을 기준판 2016.8.1판(`dart_out/risk13/모범규준_조목록.csv`)으로 적었다(제목은 2017.4.1판과 같음). "
                   "규제자본비율 산출 지적의 표기 「%s」는 「%s」로 바꿨다 — 제5장은 36~49조(조목록)이고 이 표기는 그 가운데 37~49조를 뜻한다." % (CH5_OLD, CH5))
        if ln.startswith("note: 위 판정에서 어느 지적도 닿지 않은 조(판단):"):
            ln += (" → 검증(2026-10-07): 보정 전 이 목록에는 5조(위험관리 원칙)·8조(이사회)도 있었으나, 두 조는 지적 글에서 찾아 판단으로 연결했다(검증 기록 3절, "
                   "인용 포함 — 그래서 위 목록에서 빠짐). 나머지 조는 218개 지적 글 "
                   "전체를 3절 표의 낱말로 다시 찾았으나 조 주제와 맞는 지적이 없었다(추출 범위에 없음).")
        out.append(ln)
        if ln.startswith("- 작업: 13차 9-5"):
            out.append("- 검증: 2026-10-07 `python3 scripts/dart/verify13_web.py fix` 로 원본 PDF 글과 다시 대조·보정 — 리스크관련 판정 누락 3건 바꿈(N→Y 1·N→경계 2), "
                       "「추출 범위에 없음」 반박으로 5조·8조 연결 4건 더함, 모범규준 조 제목을 2016.8.1판 기준으로, 문서 머리에 쪽, 근거 조문에 넓혀 찾은 표기를 붙임. "
                       "바뀐 곳(전·후)·지시서 항목 대조·반박 결과는 맨 끝 「검증 기록(2026-10-07)」 절. 바뀐 판정·조는 주제 칸 끝 「[검증: …]」 표시.")
        if ln.startswith("경영유의사항 등 공시 목록(") and "비은행지주 건은 아래" in ln:
            out += ["", "note: 검증(2026-10-07) 다시 확인 — 전체 목록 %d행에서 「메리츠」가 든 기관 %d행(%s), 「한국투자」가 든 기관 %d행(%s) 가운데 금융지주회사는 "
                    "「주식회사 메리츠금융지주」 20221223 1행·「한국투자금융지주 주식회사」 20241126 1행뿐이다. 검사결과제재 지주 목록 %d건 가운데 두 지주 건은 "
                    "메리츠 %s·한국투자 %s(5절, 리스크관련 판정 모두 N)." % (
                        len(allrows), len(nb["메리츠"]), ", ".join(sorted(set(nb["메리츠"]))), len(nb["한국투자"]),
                        ", ".join(sorted(set(nb["한국투자"]))), len(sanc),
                        ",".join(r["제재조치요구일"] for r in sanc if "메리츠" in r["제재대상기관"]),
                        ",".join(r["제재조치요구일"] for r in sanc if "한국투자" in r["제재대상기관"]))]
        i += 1
    ch += [("(조 제목 판 표기) note 줄·색인 머리", "「2017.4.1판」 %d곳" % n_lab, "「2016.8.1판 — 조목록.csv」"),
           ("(규제자본비율 지적의 조 표기) 표·제목·색인·판정 기준 줄", "「%s」 %d곳" % (CH5_OLD, n_ch5), "「%s」" % CH5),
           ("(문서 머리 쪽 표기)", "없음", "%d곳에 「쪽 p.N」" % n_head),
           ("(근거로 든 조문 줄) 「문서 글에 조문 인용 없음」", "%d곳" % n_none, "「문서 글에 「｢…｣ 제N조」 꼴 인용 없음(아래 넓혀 찾은 표기 참조)」"),
           ("(넓혀 찾은 조문·규정 표기 줄)", "없음", "%d곳 새로 넣음 — 찾음 %d · 추출 범위에 없음 %d" % (n_wide[True] + n_wide[False], n_wide[True], n_wide[False]))]
    return "\n".join(out), ch


UNTOUCHED_KW = [(3, r"적용\s*배제|적용\s*제외|경미"), (4, r"철학|위험\s*선호|리스크\s*선호|Risk\s*Appetite"),
                (7, r"위험관리\s*조직|리스크관리\s*조직"), (10, r"경영진[^.。]{0,30}(?:위험|리스크)|(?:위험|리스크)[^.。]{0,30}경영진|목표\s*자기자본"),
                (36, r"자산\s*비중|비중이\s*미미"), (50, r"위기\s*상황\s*대응|위기\s*대응"), (51, r"위기[^.。]{0,20}원칙|공통된\s*위기관리"),
                (58, r"(?:위기|비상)[^.。]{0,40}(?:정기적|주기적)[^.。]{0,10}점검|위기관리\s*체계의?\s*(?:적정성|정기)")]


def untouched_scan(docs, items_by_sha, rows):
    """4절 「닿지 않은 조」마다 낱말로 모든 지적 글을 다시 찾아 걸린 지적을 적는다."""
    T = titles2016()
    lab = {r["sha256"]: "%s %s" % (r["지주"], r["제재조치요구일(목록)"]) for r in rows}
    out = []
    for a, rx in UNTOUCHED_KW:
        hits = []
        for sha, its in items_by_sha.items():
            for it in its:
                if re.search(rx, re.sub(r"\s*\n\s*", " ", "\n".join(it["본문"]))):
                    hits.append("%s %s%s" % (lab.get(sha, "?"), it["번호"], "(검사결과제재)" if docs[sha]["kind"] == "sanc" else ""))
        out.append("%d조(%s) 낱말 `%s` → 걸린 지적 %d개%s" % (a, T[a], rx.replace("|", "｜"), len(hits),
                                                         ("(" + ", ".join(sorted(set(hits))[:8]) + (" 등" if len(set(hits)) > 8 else "") + ")") if hits else ""))
    return "; ".join(out)


def exam_record(before, after, ch, csv_ch, stats, rows, docs, items_by_sha, rows0, T):
    R0 = stats["R0"]
    L = [VERIFY_HEAD, ""]
    blocks = code_blocks(after.split("\n"))
    n_heads = sum(1 for ln in after.split("\n") if ln.startswith("문서 머리(조치내용)"))
    L += ["- 방법: `python3 scripts/dart/verify13_web.py fix`(보정) → 인자 없이 실행(대조). 원본은 새로 받지 않았다(`dart_out/raw/web13/fss/exam/` 의 공개안 "
          "PDF 와 pypdf 글·.meta.json, 목록 CSV 만 읽음). 대조 결과 전문 `dart_out/risk13/verify13_web.txt`.",
          "- 보정은 원 생성기(`scripts/dart/web13_fss.py` 의 build-exam, 파일은 고치지 않음)를 고친 판정표·조 제목(2016.8.1판)으로 다시 돌린 뒤 덧붙이는 방식이다. "
          "원 생성기를 설정 그대로 다시 돌린 판과 보정 전 md·CSV(커밋 %s 의 판)를 바이트로 견줌: md %s · CSV %s." % (
              BASE_COMMIT, _same(stats["same"].get(MD_E)), _same(stats["same"].get(CSV_E))),
          "- 대조한 인용: 코드 블록 %d개(문서 머리 %d · 지적 본문 %d · 이 절의 반박 발췌 %d; 보정 전 %d개). 각 블록 위 「sha256」으로 찾은 공개안 PDF 의 pypdf 글"
          "(쪽 번호 줄 「- N -」·숫자만 있는 줄은 뺌)과 공백만 무시하고 글자 대조 — 모두 일치(보정 전 블록도 모두 일치). 인용 글이 걸친 쪽과 머리의 쪽 표기도 대조"
          "(문서 머리에는 쪽 표기가 없어 붙임). 글자를 고친 인용은 없다(늘어난 블록은 판정을 바꾼 3건의 본문과 반박 발췌)." % (
              len(blocks) + len(REFUTE_ARTS), n_heads, len(blocks) - n_heads, len(REFUTE_ARTS), len(code_blocks(before.split("\n")))),
          "- CSV(%d행): 파일 바이트 sha256, 제목·인용조문·관련규정이 원본 글에 있는지, 제목 쪽, md 표와 판정·조·주제가 같은지 대조." % len(rows),
          "- 보정 전 대조(두 md·CSV 를 함께 셈 — 9-2-4 md 몫 포함): 문제 %d — %s." % (
              R0.bad, ", ".join("%s %d" % (k, v) for k, v in sorted(_cats(R0).items(), key=lambda kv: -kv[1]))), ""]
    # 1. 고친 곳
    L += ["### 1. 고친 곳(전·후)", "", "#### 1-1 리스크관련 판정·모범규준 조(판단) — 지시 「판정이 빠뜨린 건」 재검토", "",
          "전체 218개 지적 가운데 판정 N 인 128개(검사결과제재 포함)를 「리스크·위험·한도·스트레스·위기·자본·유동성·익스포·충당금·건전성·해외·사전협의·사전보고·공동투자·"
          "신용공여·자금지원·편중·내부거래·모형·측정·비상·조기경보·PF·투자·담보·손실」 낱말로 다시 훑고, 걸린 지적의 본문을 읽어 판정 기준(머리 bullet)에 맞춰 다시 판단했다.",
          "", "| 지주 · 제재조치요구일 · 번호 · 제목 | 전(판정 · 조) | 후(판정 · 조 · 주제) | 까닭(판단) — 원문은 위 문서 절의 해당 [k] 블록 |", "|---|---|---|---|"]
    for i, r in enumerate(rows):
        r0 = rows0[i]
        if (r0["리스크관련(판단)"], r0["모범규준_조(판단)"].replace(CH5_OLD, CH5)) != (r["리스크관련(판단)"], r["모범규준_조(판단)"]):
            why = {"20240620": "장기성과평가지표 건전성 비중 20% — 「고위험・고수익을 추구하는 경영 유인」(성과평가 안 리스크 요소 → 경계, 35조·5조 ②4호)",
                   "20250318": None}.get(r["제재조치요구일(목록)"])
            if r["제재조치요구일(목록)"] == "20250318":
                why = {"(11)": "소개여신 부실·「고위험 차주를 다른 자회사에게 소개」 — 자회사 사이 위험 전이(33조)·신용위험(21조) → Y",
                       "(4)": "「건전성 관련 지표의 평가비중을 상향하여 과도한 위험추구를 통제」 — 성과평가 안 리스크 요소 → 경계(35조·5조 ②4호)",
                       "(6)": "「리스크가 이사회 등에 충분히 보고되지 않을 위험」·위험성향 상승 — 8조 ③(이사회의 위험 이해) 더함"}.get(r["번호"], "")
            elif r["제재조치요구일(목록)"] in ("20241126", "20250317"):
                why = "성과평가지표에 리스크·건전성 지표 — 5조 ②4호(성과관리체계에 위험 고려) 더함(「닿지 않은 조」 반박)"
            elif r["제재조치요구일(목록)"] == "20260723":
                why = "「위험성향* Target비율이 존재하지 않아」 — 5조 ②1호(위험성향) 더함(「닿지 않은 조」 반박)"
            L.append("| %s %s %s %s %s | %s · %s | %s · %s · %s | %s |" % (
                r["지주"], r["제재조치요구일(목록)"], r["구분"], r["번호"], r["제목"].replace("|", "｜"), r0["리스크관련(판단)"],
                r0["모범규준_조(판단)"] or "—", r["리스크관련(판단)"], r["모범규준_조(판단)"], r["주제(판단)"], why or ""))
    ny0 = sum(1 for r in rows0 if r["목록"].startswith("금융회사 경영유의") and r["리스크관련(판단)"] == "Y")
    nk0 = sum(1 for r in rows0 if r["목록"].startswith("금융회사 경영유의") and r["리스크관련(판단)"] == "경계")
    ny1 = sum(1 for r in rows if r["목록"].startswith("금융회사 경영유의") and r["리스크관련(판단)"] == "Y")
    nk1 = sum(1 for r in rows if r["목록"].startswith("금융회사 경영유의") and r["리스크관련(판단)"] == "경계")
    L += ["", "note: 경영유의 공시 218개 집계 — 보정 전 Y %d · 경계 %d · N %d → 보정 후 Y %d · 경계 %d · N %d(1절 요약·4절 색인은 다시 만든 판에 반영)." % (
        ny0, nk0, 218 - ny0 - nk0, ny1, nk1, 218 - ny1 - nk1), ""]
    L += ["다시 읽었으나 N 으로 둔 지적(판단 — 기록):", ""]
    for d, k, why in KEPT_N:
        for sha, doc in docs.items():
            if os.path.basename(doc["path"]).startswith(d) and doc["kind"] == "impr":
                it = items_by_sha[sha][k - 1]
                L.append("- %s %s %s %s — %s" % (d, it["구분"], it["번호"], it["제목"], why))
    L += ["", "#### 1-2 표기·출처", ""]
    for c in ch:
        L.append("- %s — 전: %s → 후: %s" % c)
    for c in csv_ch:
        L.append("- %s — 전: %s → 후: %s" % c)
    L += ["- CSV 에 칸 4개를 더함: 「모범규준_조제목(2016.8.1판)」, 「넓혀찾은_조문표기(검증)」, 「PDF문서정보_작성일(참고·공개일아님)」, 「검증메모」(바뀐 행).",
          "- 머리 bullet 「공개일」「모범규준 조 번호」, 4절 「닿지 않은 조」 note 는 지우지 않고 끝에 「→ 검증 …」 글을 덧붙였다. 2절에 비은행지주 재확인 note, "
          "머리에 「- 검증:」 bullet 을 새로 넣었다.", ""]
    # 2. 지시서 항목
    nb = [r for r in rows if r["비은행지주"] == "Y"]
    L += ["### 2. 지시서 항목 대조(REQUEST13 「9-5 금감원 검사 결과 공개자료」 1·2번)", "",
          "| 지시서 항목 | 상태 | 근거 또는 찾은 방법 |", "|---|---|---|",
          "| 지주 이름 | 받은 글 | 1절 요약 표 18건(목록 칸 「제재대상기관」 원문 + 줄인 이름), 각 문서 절 「목록 칸」·「문서 머리」 인용의 「금융회사명」 |",
          "| 공개일 | 추출 범위에 없음 | 찾은 방법: 목록·상세 HTML 칸과 「등록일·게시일·공시일·공개일·작성일」 낱말(0건) — 대신 제재조치요구일(목록)·문서 안 "
          "조치일(문서 머리 인용)·PDF 문서정보 작성일(참고, 4절 표) |",
          "| 지적 제목 | 받은 글 | 문서마다 항목 표(경영유의 218·검사결과제재 17), CSV 「제목」 칸(제목이 원본 글에 있음을 대조) |",
          "| 요지 | 받은 글 | 리스크관련(판단 Y·경계) 지적은 본문을 글자 그대로 옮김(요약 대신 원문 — 규칙상 요약은 note 만). 「주제(판단)」 칸에 한 줄 주제 |",
          "| 근거로 든 조문 | 받은 글 | 「근거로 든 조문」(｢…｣ 제N조 꼴)·「< 관련규정 >」 칸·「넓혀 찾은 조문·규정 표기」(검증 추가). 내규 이름·조 번호가 가림 기호(◈·▣ 등)인 곳은 "
          "원문 그대로. 넓힌 낱말로도 없는 지적은 「추출 범위에 없음」 |",
          "| 2022년 이후 범위 | 받은 글 | 제재조치요구일 2022-01-01~2026-10-08 전체 목록 715행(6절 검색기록) |",
          "| 비은행지주(메리츠, 한국투자) 따로 표시 | 받은 글 | 2절(메리츠 20221223 · 한국투자 20241126, 지적 %d개), 1절 표 「비은행」, CSV 「비은행지주」 칸, 5절 "
          "검사결과제재 두 지주 건 「**비은행**」 |" % len([r for r in nb if r["목록"].startswith("금융회사 경영유의")]),
          "| 리스크관리 관련 판정 누락 재검토 | 판단 | 1-1 표(판정 바꿈 3건·조 더함 4건)와 N 으로 둔 지적 목록 |", "",
          "채운 항목: 판정을 바꾼 3건의 지적 본문(인용 블록 3개 — 위 문서 절), 문서 머리 인용 %d곳의 쪽, Y·경계 지적 %d개의 「넓혀 찾은 조문·규정 표기」 줄, "
          "CSV 칸 4개(조 제목·넓혀 찾은 표기·PDF 문서정보 작성일·검증메모), 비은행지주 재확인 note, 이 지시서 항목 대조 표. 공개일은 추출 범위에 없음 그대로(찾은 방법은 3절)." % (
              n_heads, sum(1 for r in rows if r["리스크관련(판단)"] != "N")), ""]
    # 3. 반박
    L += ["### 3. 「추출 범위에 없음」 반박 시도", ""]
    L += ["| # | 주장(보정 전 md·수집 보고) | 결과 | 다시 찾은 방법·검색어 |", "|---|---|---|---|"]
    allrows = read_csv(IMPR_ALL)
    im = sorted(set(r["제재대상기관"] for r in allrows if re.search(r"아이엠|iM|IM|DGB|디지비|대구", r["제재대상기관"])))
    conglo = sorted(set(r["제재대상기관"] for r in allrows if "금융복합기업집단" in r["제재대상기관"]))
    holds = sorted(set(r["제재대상기관"] for r in allrows if re.search(r"금융지주|지주회사|홀딩스|Holdings", r["제재대상기관"])))
    nwide = sum(1 for r in rows if r["넓혀찾은_조문표기(검증)"].startswith("추출 범위에 없음"))
    nwide_risk = [r for r in rows if r["리스크관련(판단)"] != "N" and not r["인용조문"]]
    nwide_hit = [r for r in nwide_risk if not r["넓혀찾은_조문표기(검증)"].startswith("추출 범위에 없음")]
    holds_note = " 「(주)바리움홀딩스대부」는 이름에 「홀딩스」가 든 대부업자로 금융지주회사가 아님(판단)." if any("바리움" in h for h in holds) else ""
    L += ["| 1 | 「공개일」 칸 없음 | 실패 — 추출 범위에 없음 | 목록 HTML(경영유의 전체 72쪽·지주 2쪽, 검사결과제재 지주 2쪽) 칸 이름과 상세 HTML 11건의 dt 칸 이름, "
          "낱말 「등록일」「게시일」「공시일」「공개일」「작성일」(0건). 참고로 PDF 문서정보 작성일을 4절에 적음 |",
          "| 2 | iM금융지주(2024 사명 변경) 이름의 경영유의 공시 | 실패 — 추출 범위에 없음 | 전체 목록 715행 기관명 「아이엠」「iM」「IM」「DGB」「디지비」「대구」: %s |" % (
              ", ".join(im)),
          "| 3 | 지시서 목록 밖 금융지주 건 | 실패 — 없음이 아니라 이 목록 범위에서 18건뿐 | 기관명 「금융지주」「지주회사」「홀딩스」「Holdings」: %d종(%s). "
          "「금융복합기업집단」 %d종(%s)은 금융지주회사가 아니어서 넣지 않음(판단).%s |" % (len(holds), ", ".join(holds), len(conglo), ", ".join(conglo), holds_note),
          "| 4 | 검사결과제재 상세 화면의 기관·임원·직원 제재 칸 | 실패 — 화면 칸이 빈 건 7건 그대로 | 상세 HTML 의 「기관제재대상」「임원제재대상」「직원제재대상」 dd 글 |",
          "| 5 | 지적별 「문서 글에 조문 인용 없음」 | 일부 성공 | 「제N조」(가림 기호 조 번호 포함)·「§N」·「<별표 N>」·「｢…｣」 꼴로 넓혀 찾음 — 리스크관련 지적 가운데 "
          "「｢…｣ 제N조」 꼴이 없던 %d개 가운데 %d개에서 가림 기호 조 번호·내규 이름 등을 찾아 「넓혀 찾은 조문·규정 표기」 줄을 붙임(나머지 %d개는 추출 범위에 없음). "
          "CSV 전체 %d행 가운데 넓힌 낱말로도 없는 행 %d개 |" % (len(nwide_risk), len(nwide_hit), len(nwide_risk) - len(nwide_hit), len(rows), nwide),
          "| 6 | 4절 「어느 지적도 닿지 않은 조」 3·4·5·7·8·10·36·50·51·58조 | 5조·8조 성공(판단 연결), 나머지 실패 — 추출 범위에 없음 | 지적 글 %d개 전체(검사결과제재 포함)를 "
          "조마다 낱말로 다시 찾음 — %s. 걸린 지적은 이미 다른 조로 연결됐거나(예: 위기상황분석=56조, 위기대응체계=52~54조) 조 주제와 맞지 않아 새로 연결하지 않음(판단). "
          "5조는 「위험성향」「성과」+「건전성·리스크 지표」, 8조는 「이사회」+「리스크·위험」 보고로 찾아 아래 인용처럼 연결 |" % (
              sum(len(v) for v in items_by_sha.values()), untouched_scan(docs, items_by_sha, rows)), ""]
    L += ["반박에 성공한 곳의 원문(5조·8조 연결, 판단) — 지적 본문 전체는 위 문서 절의 해당 [k] 블록:", ""]
    for d, k, key, art, why in REFUTE_ARTS:
        sha = [s for s, doc in docs.items() if doc["kind"] == "impr" and os.path.basename(doc["path"]).startswith(d)][0]
        it = items_by_sha[sha][k - 1]
        bl = it["본문"]
        j = next((j for j in range(len(bl)) if key in ns(bl[j])), None)
        if j is None:
            j = next((j for j in range(len(bl) - 1) if key in ns(bl[j] + bl[j + 1])), 0)
        ex = "\n".join(bl[j:j + 3])
        pg = page_spans(doc_pages(docs[sha]), ex)
        doc = docs[sha]
        L += ["인용 — %s %s %s %s · 「%s」 · sha256 %s · %s · 연결 %d조(%s)(판단): %s" % (
            d, it["구분"], it["번호"], it["제목"], doc["meta"].get("원파일명", ""), sha, ",".join("p.%d" % n for n in pg), art, T[art], why),
              "", "```text", ex, "```", ""]
    # 4. PDF 문서정보 작성일
    L += ["### 4. 참고: 공개안 PDF 문서정보 작성일(CreationDate) — 공개일이 아님", "",
          "| 제재조치요구일(목록) | 지주 | 목록 | PDF 문서정보 작성일 | 원파일 |", "|---|---|---|---|---|"]
    seen = set()
    for r in rows:
        if r["sha256"] in seen:
            continue
        seen.add(r["sha256"])
        L.append("| %s | %s | %s | %s | %s |" % (r["제재조치요구일(목록)"], r["지주"], r["목록"], r["PDF문서정보_작성일(참고·공개일아님)"], r["파일"]))
    L += ["", "note: 작성일은 PDF 파일 안 문서정보(pypdf metadata)의 값이다 — 게시판 공개(게시)일을 뜻하지 않는다(판단으로도 공개일로 쓰지 않음).", ""]
    L += ["### 5. 남은 문제", "",
          "- 공개일은 게시판에 칸이 없어 채우지 못했다(제재조치요구일·문서 안 조치일만).",
          "- 리스크관련 판정·모범규준 조 번호는 모두 판단이다. 이번 검증에서 바꾼 판정 3건·더한 조 4건도 판단이며 주제 칸 「[검증: …]」으로 표시했다.",
          "- 공개안의 내규 이름·조 번호 상당수가 가림 기호(◈·▣·◉ 등)라 지주 내규 조문과 맞댈 수 없다(원문 그대로).",
          "- PDF 글은 pypdf 로 뽑은 것이라 띄어쓰기가 원문과 다를 수 있다(공백 뺀 글자는 원본과 같음을 대조).",
          "- 원 생성기(`web13_fss.py build`)를 다시 돌리면 이 보정이 지워진다 — 그 뒤에는 `python3 scripts/dart/verify13_web.py fix` 를 다시 돌릴 것."]
    return "\n".join(L)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd not in ("", "fix"):
        print(__doc__)
        return 2
    if cmd == "fix":
        fix()
    R = verify()
    return 0 if R.bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
