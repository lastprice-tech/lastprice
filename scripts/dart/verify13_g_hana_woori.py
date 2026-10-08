# -*- coding: utf-8 -*-
"""13차 9-4 하나금융지주·우리금융지주 산출물 검증·보정.

    python3 scripts/dart/verify13_g_hana_woori.py          # 대조만 — 결과 dart_out/risk13/verify13_g_hana_woori.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_g_hana_woori.py refute   # 「추출 범위에 없음」 반박 시도(같은 출처, 더 넓은 검색어) —
                                                           #   결과 dart_out/raw/web13/verify13_g_hana_woori/refute_hits.json (요약만 출력)
    python3 scripts/dart/verify13_g_hana_woori.py fix      # 보정(멱등: 검증 전 사본 pre/ 에서 다시 만듦) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-4_하나금융지주.md, 9-4_우리금융지주.md,
      dart_out/risk13/9-4_하나금융지주_조문목차.csv, 9-4_우리금융지주_조문목차.csv.
검증 전 사본: dart_out/raw/web13/verify13_g_hana_woori/pre/ (커밋 8c118c8 의 파일 그대로 — 없으면 git show 로 다시 만듦).
      원 생성기 scripts/dart/web13_g_hana_woori.py 는 고치지도 import 하지도 않는다(다시 돌리면 보정이 지워지므로 돌리지 말 것).
원문(읽기만): dart_out/text/risk8/ (연차보고서·추가공시, 사업보고서 원본·정정, 경영공시 — 쪽 표지 「=== p.N ===」),
      dart_out/text/risk9/<접수번호>.txt (DART 정기보고서 — 같은 회사 다른 기간 판, 반박 검색에만),
      메타 dart_out/risk8/텍스트목록.csv·handoff/연차보고서_파일목록.csv·dart_out/risk8/경영공시_2026_2Q.csv·
      dart_out/raw/risk8/경영공시/<회사>/meta.json·dart_out/doc/<접수번호>/_파일목록.json·dart_out/risk9/텍스트목록.csv,
      모범규준 조 목록 dart_out/risk13/모범규준_조목록.csv(2016.8.1 판 제목), 모범규준 원문 handoff/13차_산출물/9-4_모범규준_원문.md.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만).

대조(인자 없이):
  1. md 의 원문 인용(코드 블록·> 블록) 전부를 바로 앞 출처 줄 [문서 · 접수번호/URL · 쪽 · 줄 · 파일 · 원본 수집 · 인용] 이 가리킨 텍스트
     줄과 대조 — 글자 그대로(줄 끝 공백만 무시)인지, 아니면 공백만 무시하고 같은지. 출처 줄의 쪽·줄 번호가 실제 자리와 같은지,
     문서명·접수번호/URL·원본 수집일이 메타와 같은지, 인용이 글머리 목록 중간에서 끊겼는지(다음 원본 줄이 같은 글머리로 시작).
  2. 4장 「추가공시·정정판 문구 대조」 표의 결과를 다시 계산해 같은지.
  3. 5장 검색 기록 표의 걸린 수·걸린 쪽을 다시 계산해 같은지.
  4. 조문 목차 CSV·1-2 표 — 전문 옮긴 규정의 조 번호·제목이 그 쪽 텍스트에 있는지, 인용만 있는 행의 규정명이 그 쪽에 있는지,
     CSV 와 md 1-2 표가 같은지, 문서·URL 이 메타와 같은지.
  5. note·표 줄의 「…」 조각이 원본(회사 텍스트·모범규준 원문·지시서)에 있는지(공백 무시) — 못 찾은 것은 문제(허용 목록 밖이면).
  6. 「모범규준 조:」 줄과 0장 표의 조 번호마다 「N조(조 제목)」이 붙었는지, 제목이 모범규준_조목록.csv(2016.8.1 판)과 같은지,
     지시서에 없는 조 번호에 「(판단)」이 붙었는지.
  7. 지시서(REQUEST13) 9-4 항목마다 「6. 지시서 항목별 대조」 표에 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」이 있는지,
     가리킨 인용 번호가 md 에 있는지.
  8. 「추출 범위에 없음」 줄마다 찾은 방법(검색어·범위)이 있는지, 반박 검색 기록이 검증 기록에 있는지.
  9. 인증값(DART 키·법제처 OC) 문자열 없음, 산출 폴더에 PDF 없음, 맨 끝 「## 검증 기록(2026-10-07)」 절이 하나.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

TODAY = "2026-10-07"
TXT8 = os.path.join("dart_out", "text", "risk8")
TXT9 = os.path.join("dart_out", "text", "risk9")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
VD = os.path.join("dart_out", "raw", "web13", "verify13_g_hana_woori")
PRE = os.path.join(VD, "pre")
PRE_COMMIT = "8c118c8"
OUT_TXT = os.path.join(WORK, "verify13_g_hana_woori.txt")
REFUTE_JSON = os.path.join(VD, "refute_hits.json")
CHECK_JSON = os.path.join(VD, "check_detail.json")
FIX_JSON = os.path.join(VD, "fix_log.json")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MOBEOM_MD = os.path.join(OUTD, "9-4_모범규준_원문.md")
REQ = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
REQ_COPY = os.path.join(VD, "REQUEST13.txt")   # 지시서 사본(스크래치가 지워져도 대조되게)
CO = {"H": "하나금융지주", "W": "우리금융지주"}
MD = {k: os.path.join(OUTD, f"9-4_{v}.md") for k, v in CO.items()}
TOC = {k: os.path.join(WORK, f"9-4_{v}_조문목차.csv") for k, v in CO.items()}
PAGE_RE = re.compile(r"^=== p\.(\d+) ===\s*$")
SHORT = {"연차": "AR", "사업": "BR", "경영공시": "MD"}
QID = r"[HW]-\d+b?"
# 지시서(REQUEST13 9-4)에 적힌 모범규준 조 번호 — 이 밖의 번호는 「(판단)」
REQ_ARTS = {3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55}
VREC = f"## 검증 기록({TODAY})"


def nows(s):
    return re.sub(r"\s+", "", s)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ───────────────────────────── 문서·메타 ─────────────────────────────
DOCS = {
    "H_AR": dict(co="H", kind="연차", file="연차보고서__하나금융지주_지배구조연차보고서_2026.txt", pdf="하나금융지주_지배구조연차보고서_2026.pdf",
                 tag="본공시"),
    "H_AR2": dict(co="H", kind="연차(추가공시)", file="연차보고서__하나금융지주_지배구조연차보고서_2026_추가공시.txt",
                  pdf="하나금융지주_지배구조연차보고서_2026_추가공시.pdf", tag="추가공시"),
    "H_BR": dict(co="H", kind="사업", file="사업보고서__하나금융지주__20260316001292.txt", rcp="20260316001292"),
    "H_BR_4019": dict(co="H", kind="사업(정정)", file="사업보고서__하나금융지주__20260814004019.txt", rcp="20260814004019"),
    "H_MD": dict(co="H", kind="경영공시", file="경영공시__하나금융지주.txt"),
    "W_AR": dict(co="W", kind="연차", file="연차보고서__우리금융지주_지배구조연차보고서_2026.txt", pdf="우리금융지주_지배구조연차보고서_2026.pdf",
                 tag="본공시"),
    "W_AR2": dict(co="W", kind="연차(추가공시)", file="연차보고서__우리금융지주_지배구조연차보고서_2026_추가공시.txt",
                  pdf="우리금융지주_지배구조연차보고서_2026_추가공시.pdf", tag="추가공시"),
    "W_BR": dict(co="W", kind="사업", file="사업보고서__우리금융지주__20260313001235.txt", rcp="20260313001235"),
    "W_MD": dict(co="W", kind="경영공시", file="경영공시__우리금융지주.txt"),
}
for _k, _d in DOCS.items():
    _d["path"] = os.path.join(TXT8, _d["file"])
VARIANTS = {"H_AR": ["H_AR2"], "H_BR": ["H_BR_4019"], "W_AR": ["W_AR2"],
            # risk9 다른 기간 판(검증 때 새 인용의 출처) — 원본 → 정정판
            "R9_20240314001383": ["R9_20240516001472"], "R9_20240314001628": ["R9_20240516001695"]}
MAIN = {"H": ["H_AR", "H_BR", "H_MD"], "W": ["W_AR", "W_BR", "W_MD"]}
_META_DONE = False


def load_meta():
    """문서별 표기(문서명)·위치(URL 또는 접수번호)·원본 수집일·sha256 을 메타 파일에서 만든다."""
    global _META_DONE
    if _META_DONE:
        return
    _META_DONE = True
    tl = {r["doc_id"]: r for r in read_csv(os.path.join("dart_out", "risk8", "텍스트목록.csv"))}
    ar = {r["파일명"]: r for r in read_csv(os.path.join("handoff", "연차보고서_파일목록.csv"))}
    md26 = {r["corp_label"]: r for r in read_csv(os.path.join("dart_out", "risk8", "경영공시_2026_2Q.csv"))}
    for k, d in DOCS.items():
        t = tl[d["file"][:-4]]
        d["src_sha"] = t["원본sha256"]
        d["txt_sha"] = t["텍스트sha256"]
        d["txt_sha_ok"] = sha(d["path"]) == t["텍스트sha256"]
        d["npages_meta"] = t["쪽수"]
        co = CO[d["co"]]
        if d["kind"].startswith("연차"):
            a = ar[d["pdf"]]
            d["name"] = f"{co} 「{a['제목']}」({d['tag']})"
            d["loc"] = a["url"]
            d["locs_ok"] = {a["url"], t["출처"]}
            d["fetched"] = a["fetched_at"]
            d["src_sha_list"] = a["sha256"]
        elif "rcp" in d:
            j = json.load(open(os.path.join("dart_out", "doc", d["rcp"], "_파일목록.json"), encoding="utf-8"))
            d["name"] = f"{co} {j.get('report_nm', '')}"
            d["loc"] = f"접수번호 {d['rcp']}"
            d["locs_ok"] = {d["loc"]}
            d["fetched"] = j.get("생성시각", "")
            d["src_sha_list"] = t["원본sha256"]
        else:
            m = md26[co]
            mj = json.load(open(os.path.join("dart_out", "raw", "risk8", "경영공시", co, "meta.json"), encoding="utf-8"))
            d["name"] = f"{co} 「{m['제목']}」(경영공시)"
            d["loc"] = mj.get("실제url") or m["url"]
            d["locs_ok"] = {m["url"], mj.get("url", ""), mj.get("실제url", "")}
            d["fetched"] = m["fetched_at"]
            d["src_sha_list"] = m["sha256"]
    # risk9: 같은 회사 정기보고서(다른 기간 판) — 반박 검색에만(risk8 과 같은 텍스트면 뺌)
    for r in read_csv(os.path.join("dart_out", "risk9", "텍스트목록.csv")):
        if r["corp_label"] not in CO.values():
            continue
        rcp = r["rcept_no"]
        p = os.path.join(TXT9, rcp + ".txt")
        if not os.path.exists(p) or any(DOCS[x].get("rcp") == rcp for x in list(DOCS)):
            continue
        co = [k for k, v in CO.items() if v == r["corp_label"]][0]
        fetched = ""
        j = os.path.join("dart_out", "doc", rcp, "_파일목록.json")
        if os.path.exists(j):
            fetched = json.load(open(j, encoding="utf-8")).get("생성시각", "")
        DOCS["R9_" + rcp] = dict(co=co, kind="정기보고서(risk9)", file=rcp + ".txt", path=p, rcp=rcp,
                                 name=f"{r['corp_label']} {r['report_nm']}", loc=f"접수번호 {rcp}", locs_ok={f"접수번호 {rcp}"},
                                 fetched=fetched, src_sha=r["원본sha256"], txt_sha=r["텍스트sha256"],
                                 txt_sha_ok=(sha(p) == r["텍스트sha256"]))


class Text:
    def __init__(self, key):
        self.key = key
        self.lines = open(DOCS[key]["path"], encoding="utf-8").read().split("\n")
        self.page = []
        p = 0
        for ln in self.lines:
            m = PAGE_RE.match(ln.strip())
            if m:
                p = int(m.group(1))
            self.page.append(p)
        self.npages = max(self.page) if self.page else 0
        self._flat = {}

    def flat(self, mode="raw"):
        """공백 없이 이어 붙인 글과 글자별 줄 번호(0부터). mode: raw(전부) / nopage(쪽 표지 뺌) / nohead(쪽 표지·DART 쪽 머리말 뺌)."""
        if mode not in self._flat:
            chars, idx = [], []
            for i, ln in enumerate(self.lines):
                if mode != "raw" and PAGE_RE.match(ln.strip()):
                    continue
                if mode == "nohead" and "dart.fss.or.kr Page" in ln:
                    continue
                c = nows(ln)
                chars.append(c)
                idx.extend([i] * len(c))
            self._flat[mode] = ("".join(chars), idx)
        return self._flat[mode]

    def pages_text(self):
        """쪽 번호 → 그 쪽 글(줄바꿈을 빼고 이어 붙임) — 수집 에이전트 5장 검색 기록과 같은 방식."""
        out = {}
        for ln, p in zip(self.lines, self.page):
            if PAGE_RE.match(ln.strip()):
                continue
            out.setdefault(p, []).append(ln.strip())
        return {p: "".join(v) for p, v in out.items()}


TEXTS = {}


def T(key):
    if key not in TEXTS:
        TEXTS[key] = Text(key)
    return TEXTS[key]


def key_for_path(path):
    for k, d in DOCS.items():
        if os.path.normpath(d["path"]) == os.path.normpath(path):
            return k
    return None


# ───────────────────────────── 모범규준 조 목록 ─────────────────────────────
def jo_titles():
    out = {}
    for r in read_csv(JO_CSV):
        out[int(r["조"])] = r["제목_2016.8.1판"].strip()
    return out


# ───────────────────────────── md 파싱 ─────────────────────────────
CITE_RE = re.compile(r"^\[(?P<doc>.+?) · (?P<loc>접수번호 \d{14}|https?://\S+) · 쪽 (?P<pages>p\.\d+(?:–p\.\d+)?) · "
                     r"줄 (?P<l1>\d+)–(?P<l2>\d+) · `(?P<path>[^`]+)` · 원본 수집 (?P<fetched>\d{4}-\d{2}-\d{2})"
                     r"(?P<fetched_note>[^·\]]*) · 인용 (?P<qd>\d{4}-\d{2}-\d{2})(?P<tail>[^\]]*)\]\s*$")


def parse_md(text):
    """코드 블록(```)·> 블록 → [{qid, head_line, art_line, cite, cite_line, body, body_start}]"""
    lines = text.split("\n")
    blocks = []
    qid, head_ln, art, art_ln, cite, cite_ln = None, None, None, None, None, None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^### (\S+) ", ln)
        if m:
            qid, head_ln, art, art_ln, cite, cite_ln = m.group(1), i, None, None, None, None
        elif ln.startswith("## "):
            qid, head_ln, art, art_ln, cite, cite_ln = None, None, None, None, None, None
        elif ln.startswith("모범규준 조:"):
            art, art_ln = ln, i
        elif ln.startswith("[") and " · 쪽 p." in ln:
            cite, cite_ln = ln, i
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            blocks.append(dict(kind="code", qid=qid, head_line=head_ln, art=art, art_line=art_ln, cite=cite, cite_line=cite_ln,
                               body=lines[i + 1:j], body_start=i + 1, fence=ln))
            cite, cite_ln = None, None
            i = j + 1
            continue
        if ln.startswith(">"):
            j = i
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            blocks.append(dict(kind="quote", qid=qid, head_line=head_ln, art=art, art_line=art_ln, cite=cite, cite_line=cite_ln,
                               body=[re.sub(r"^> ?", "", x) for x in lines[i:j]], body_start=i, fence=">"))
            cite, cite_ln = None, None
            i = j
            continue
        i += 1
    return lines, blocks


BULLET_RE = re.compile(r"^\s*(ㆍ|·|-|•|①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩|\d{1,2}\.\s|[가-하]\.\s|\d{1,2}\)\s|[가-하]\)\s)")


def bullet_of(s):
    m = BULLET_RE.match(s)
    if not m:
        return None
    b = m.group(1).strip()
    if re.fullmatch(r"\d{1,2}\.", b):
        return "번호"
    if re.fullmatch(r"[가-하]\.", b):
        return "가나다"
    if re.fullmatch(r"\d{1,2}\)", b):
        return "번호)"
    if re.fullmatch(r"[가-하]\)", b):
        return "가나다)"
    if b in "①②③④⑤⑥⑦⑧⑨⑩":
        return "원문자"
    return b


def check_quote(co, b, probs, detail):
    """인용 한 개 대조. 문제는 probs 에 (위치, 내용)."""
    load_meta()
    where = f"{CO[co]} md {b['body_start']}줄 {b['qid']}"
    rec = dict(co=co, qid=b["qid"], md_line=b["body_start"], kind=b["kind"], nlines=len(b["body"]))
    if b["cite"] is None:
        probs.append((where, "출처 줄 없음"))
        rec["result"] = "출처 없음"
        detail.append(rec)
        return rec
    m = CITE_RE.match(b["cite"])
    if not m:
        probs.append((where, f"출처 줄 형식 다름: {b['cite'][:120]}"))
        rec["result"] = "출처 형식"
        detail.append(rec)
        return rec
    path = m.group("path")
    key = key_for_path(path)
    rec.update(path=path, cite_pages=m.group("pages"), l1=int(m.group("l1")), l2=int(m.group("l2")))
    if key is None or not os.path.exists(path):
        probs.append((where, f"출처 파일 없음/목록 밖: {path}"))
        rec["result"] = "파일 없음"
        detail.append(rec)
        return rec
    d = DOCS[key]
    rec["doc"] = key
    if m.group("doc") != d["name"]:
        probs.append((where, f"문서명 다름: 「{m.group('doc')}」 / 메타 「{d['name']}」"))
    if m.group("loc") not in d["locs_ok"]:
        probs.append((where, f"URL/접수번호 다름: {m.group('loc')} / 메타 {sorted(d['locs_ok'])}"))
    if m.group("fetched") != d["fetched"][:10]:
        probs.append((where, f"원본 수집일 다름: {m.group('fetched')} / 메타 {d['fetched']}"))
    if m.group("qd") != TODAY:
        probs.append((where, f"인용일 다름: {m.group('qd')}"))
    t = T(key)
    l1, l2 = int(m.group("l1")), int(m.group("l2"))
    src = t.lines[l1 - 1:l2]
    body = list(b["body"])
    while body and not body[-1].strip():
        body.pop()
    exact = [x.rstrip() for x in body] == [x.rstrip() for x in src]
    same_ws = nows("".join(body)) == nows("".join(src))
    rec["exact"] = exact
    rec["same_ws"] = same_ws
    if exact:
        rec["result"] = "글자까지 같음(줄 끝 공백만 무시)"
    elif same_ws:
        rec["result"] = "공백만 다름"
    else:
        flat, idx = t.flat("raw")
        nq = nows("".join(body))
        pos = flat.find(nq) if nq else -1
        if pos >= 0:
            a, z = idx[pos] + 1, idx[pos + len(nq) - 1] + 1
            rec["result"] = f"줄 번호 다름(실제 줄 {a}–{z})"
            rec["real_l1"], rec["real_l2"] = a, z
            probs.append((where, f"출처 줄 번호 다름: 표기 {l1}–{l2} / 실제 {a}–{z}"))
            l1, l2 = a, z
            src = t.lines[l1 - 1:l2]
        else:
            sm = difflib.SequenceMatcher(None, [x.strip() for x in src], [x.strip() for x in body], autojunk=False)
            diffs = []
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op != "equal":
                    diffs.append(f"{op}: 원본 {src[i1:i2][:2]} / 인용 {body[j1:j2][:2]}")
            rec["result"] = "원문과 다름"
            rec["diffs"] = diffs[:6]
            probs.append((where, "인용이 원문과 다름: " + " ‖ ".join(diffs[:3])[:600]))
            detail.append(rec)
            return rec
    p1, p2 = t.page[l1 - 1], t.page[l2 - 1]
    lab = f"p.{p1}" if p1 == p2 else f"p.{p1}–p.{p2}"
    rec["real_pages"] = lab
    if lab != m.group("pages"):
        probs.append((where, f"쪽 표기 다름: {m.group('pages')} / 실제 {lab}"))
    # 글머리 목록 중간에서 끊겼는지
    nxt = l2
    while nxt < len(t.lines) and (not t.lines[nxt].strip() or PAGE_RE.match(t.lines[nxt].strip())):
        nxt += 1
    last = next((x for x in reversed(src) if x.strip()), "")
    if nxt < len(t.lines):
        bn, bl = bullet_of(t.lines[nxt]), bullet_of(last)
        if bn and bl and bn == bl and bn not in ("-",):
            rec["cut_list"] = t.lines[nxt].strip()[:80]
    detail.append(rec)
    return rec


# ───────────────────────────── 4장 대조판 ─────────────────────────────
def variant_result(key, body):
    """수집 에이전트 방식(쪽 표지 줄 빼고 공백 무시) + DART 쪽 머리말 줄도 빼고 한 번 더."""
    out = []
    b1 = [ln for ln in body if not PAGE_RE.match(ln.strip())]
    nq = nows("".join(b1))
    b2 = [ln for ln in b1 if "dart.fss.or.kr Page" not in ln]
    nq2 = nows("".join(b2))
    for vid in VARIANTS.get(key, []):
        vt = T(vid)
        nv = vt.flat("nopage")[0]
        if nq in nv:
            out.append((vid, "같음(공백 무시)", ""))
            continue
        nv2 = vt.flat("nohead")[0]
        if nq2 in nv2:
            out.append((vid, "같음(공백·DART 쪽 머리말 줄 무시)", ""))
            continue
        miss = [ln.strip() for ln in b1 if len(nows(ln)) >= 6 and nows(ln) not in nv]
        if not miss:
            out.append((vid, "줄 단위로는 모두 있음(배치·이어짐이 다름 — 쪽 머리글·쪽 번호 줄 차이 포함)", ""))
        else:
            out.append((vid, f"다름 — 공백을 빼고도 없는 줄 {len(miss)}개", " ‖ ".join(miss[:3])))
    return out


def check_variants(co, lines, blocks, probs):
    n = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^\| (" + QID + r") \| `([^`]+)` \| ([^|]+) \| ([^|]*) \|\s*$", ln)
        if not m:
            continue
        n += 1
        qid, vfile, res = m.group(1), m.group(2), m.group(3).strip()
        b = next((x for x in blocks if x["qid"] == qid), None)
        if b is None:
            probs.append((f"{CO[co]} md {i + 1}줄", f"4장 표의 인용 {qid} 없음"))
            continue
        cm = CITE_RE.match(b["cite"] or "")
        key = key_for_path(cm.group("path")) if cm else None
        got = {vid: r for vid, r, _ in variant_result(key, b["body"])} if key else {}
        vid = next((k for k in DOCS if DOCS[k]["file"] == vfile + ".txt"), None)
        if vid not in got:
            probs.append((f"{CO[co]} md {i + 1}줄", f"4장 대조판 {vfile} 는 {qid} 의 대조판이 아님"))
        elif got[vid] != res:
            probs.append((f"{CO[co]} md {i + 1}줄", f"4장 {qid}×{vfile}: 표 「{res}」 / 다시 셈 「{got[vid]}」"))
    for b in blocks:
        cm = CITE_RE.match(b["cite"] or "")
        key = key_for_path(cm.group("path")) if cm else None
        for vid in VARIANTS.get(key, []):
            pat = f"| {b['qid']} | `{DOCS[vid]['file'][:-4]}` |"
            if not any(ln.startswith(pat) for ln in lines):
                probs.append((f"{CO[co]} 4장", f"대조판 행 없음: {b['qid']} × {DOCS[vid]['file'][:-4]}"))
    return n


# ───────────────────────────── 5장 검색 기록 ─────────────────────────────
SEARCH_ROW_RE = re.compile(r"^\| (?P<lab>[^|]+?) \| (?P<doc>연차|사업|경영공시) \| p\.1–p\.(?P<np>\d+) \| (?P<n>\d+) \| (?P<npg>\d+) \| "
                           r"(?P<pages>[^|]*?) \| `(?P<rx>[^`]+)` \|\s*$")


def check_search(co, lines, probs):
    n = 0
    for i, ln in enumerate(lines):
        m = SEARCH_ROW_RE.match(ln)
        if not m:
            continue
        n += 1
        key = f"{co}_{SHORT[m.group('doc')]}"
        t = T(key)
        rx = re.compile(m.group("rx").replace("¦", "|"))
        pt = t.pages_text()
        hits = {p: len(rx.findall(s)) for p, s in pt.items()}
        hits = {p: c for p, c in hits.items() if c}
        pl = sorted(hits)
        short = ", ".join(str(p) for p in pl[:30]) + (f" … (+{len(pl) - 30})" if len(pl) > 30 else "")
        if not pl:
            short = "-"
        got = (str(t.npages), str(sum(hits.values())), str(len(pl)), short)
        want = (m.group("np"), m.group("n"), m.group("npg"), m.group("pages").strip())
        if got != want:
            probs.append((f"{CO[co]} md {i + 1}줄 5장", f"검색 기록 다름: 표 {want} / 다시 셈 {got}"))
    return n


# ───────────────────────────── 조문 목차 ─────────────────────────────
TOC_ART = "닿는모범규준조(판단)"
TOC_COLS = ["회사", "규정명", "조번호", "조제목", "문서", "접수번호또는URL", "쪽", "전문여부", TOC_ART]


def toc_rows_md(md_lines):
    tab = []
    in12 = False
    for ln in md_lines:
        if ln.startswith("### 1-2 "):
            in12 = True
            continue
        if in12 and ln.startswith("#"):
            break
        if in12 and ln.startswith("| ") and not ln.startswith("| 규정명") and not ln.startswith("|---"):
            tab.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return tab


def doc_by_loc(co, loc):
    load_meta()
    for k, d in DOCS.items():
        if d["co"] == co and loc in d["locs_ok"] and k not in [v for x in VARIANTS.values() for v in x]:
            return k
    return None


def check_toc(co, md_lines, probs, rows=None):
    load_meta()
    rows = rows if rows is not None else read_csv(TOC[co])
    pts = {}
    for r in rows:
        w = f"{CO[co]} CSV {r['규정명']} {r['조번호']}"
        if r["회사"] != CO[co]:
            probs.append((w, f"회사 칸 다름: {r['회사']}"))
        key = doc_by_loc(co, r["접수번호또는URL"])
        if key is None:
            probs.append((w, f"URL/접수번호가 메타에 없음: {r['접수번호또는URL']}"))
            continue
        d = DOCS[key]
        if not r["문서"].startswith(d["name"]):
            probs.append((w, f"문서 칸 다름: 「{r['문서']}」 / 메타 「{d['name']}」"))
        if key not in pts:
            pts[key] = T(key).pages_text()
        pg = []
        for a, b in re.findall(r"p\.(\d+)(?:–p\.(\d+))?", r["쪽"]):
            pg.extend(range(int(a), int(b or a) + 1))
        txt = "".join(pts[key].get(p, "") for p in pg)
        ntxt = nows(txt)
        m = re.fullmatch(r"제(\d+)조(의\d+)?", r["조번호"])
        if r["전문여부"].startswith("Y") and m:
            pat = re.compile(r"제\s*" + m.group(1) + r"\s*조" + (r"\s*의\s*" + m.group(2)[1:] if m.group(2) else "") +
                             r"\s*\(\s*" + r"\s*".join(map(re.escape, nows(r["조제목"]))) + r"\s*\)")
            if not pat.search(txt):
                probs.append((w, f"조 번호·제목이 {r['쪽']} 에 없음"))
        elif r["조번호"] == "부칙":
            if "부칙" not in ntxt:
                probs.append((w, f"부칙이 {r['쪽']} 에 없음"))
        else:
            nm = nows(r["규정명"])
            if nm not in ntxt and not any(nm in nows(x) for x in [r["전문여부"]]):
                probs.append((w, f"규정명이 {r['쪽']} 에 없음"))
            if m and not re.search(r"제\s*" + m.group(1) + r"\s*조", txt):
                probs.append((w, f"조 번호가 {r['쪽']} 에 없음"))
    tab = toc_rows_md(md_lines)
    csv_cells = [[r["규정명"], r["조번호"], r["조제목"], r["쪽"], r["전문여부"]] + ([r[TOC_ART]] if TOC_ART in r else []) for r in rows]
    tabn = [x[:len(csv_cells[0])] for x in tab] if csv_cells else tab
    if tabn != csv_cells:
        diff = [x for x in difflib.unified_diff([" | ".join(x) for x in csv_cells], [" | ".join(x) for x in tabn], lineterm="", n=0)][:6]
        probs.append((f"{CO[co]} md 1-2 표", "CSV 와 다름: " + " ‖ ".join(diff)[:500]))
    if rows and TOC_ART not in rows[0]:
        probs.append((f"{CO[co]} CSV", f"「{TOC_ART}」 칸 없음(모범규준 조 번호)"))
    return len(rows)


# ───────────────────────────── 「…」 조각 ─────────────────────────────
FRAG_RE = re.compile(r"「([^「」]{2,}?)」")
_CORPUS = {}


def req_text():
    if os.path.exists(REQ):
        txt = open(REQ, encoding="utf-8").read()
        os.makedirs(VD, exist_ok=True)
        if not os.path.exists(REQ_COPY) or open(REQ_COPY, encoding="utf-8").read() != txt:
            open(REQ_COPY, "w", encoding="utf-8").write(txt)
        return txt
    if os.path.exists(REQ_COPY):
        return open(REQ_COPY, encoding="utf-8").read()
    return ""


def corpus_for(co):
    if co in _CORPUS:
        return _CORPUS[co]
    load_meta()
    parts = []
    for k in [k for k in DOCS if DOCS[k]["co"] == co]:
        parts.append(T(k).flat("raw")[0])
        parts.append(nows(DOCS[k]["name"]))
    parts.append(nows(open(MOBEOM_MD, encoding="utf-8").read()))
    parts.append(nows(req_text()))
    parts.append(nows(open(JO_CSV, encoding="utf-8-sig").read()))
    _CORPUS[co] = parts
    return parts


def frag_found(frag, corpus):
    pieces = [nows(x) for x in re.split(r"…|\.\.\.| / ", frag)]
    pieces = [x for x in pieces if len(x) >= 2]
    if not pieces:
        return True
    for c in corpus:
        pos = 0
        ok = True
        for pc in pieces:
            j = c.find(pc, pos)
            if j < 0:
                ok = False
                break
            pos = j + len(pc)
        if ok:
            return True
    return False


def check_frags(co, lines, blocks, probs):
    inside = set()
    for b in blocks:
        for k in range(len(b["body"])):
            inside.add(b["body_start"] + k)
    corpus = corpus_for(co)
    n, miss = 0, []
    skip_sec = False
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            skip_sec = ln.startswith("## 검증 기록")    # 검증 기록 절의 전→후 조각은 대상 아님
        if i in inside or skip_sec or ln.startswith("```"):
            continue
        for fr in FRAG_RE.findall(ln):
            n += 1
            if frag_found(fr, corpus):
                continue
            if fr in FRAG_ALLOW:
                continue
            miss.append((i + 1, fr))
    for ln_no, fr in miss:
        probs.append((f"{CO[co]} md {ln_no}줄", f"「…」 조각을 원본에서 못 찾음: 「{fr[:100]}」"))
    return n, miss


# ───────────────────────────── 모범규준 조 표기 ─────────────────────────────
ART_TOKEN_RE = re.compile(r"(\d{1,2})조\((?!판단\))([^()]+)\)((?:[①-⑳](?:[\d~·]*호)?)*)(\(판단\))?")


def check_art_lines(co, lines, probs):
    titles = jo_titles()
    n = 0
    sec, sub = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec, sub = ln, None
        if ln.startswith("### "):
            sub = ln
        targets = []
        if ln.startswith("모범규준 조:"):
            targets.append((ln[len("모범규준 조:"):], False))
        if sec and sec.startswith("## 0.") and re.match(r"^\| \d", ln):   # 0장 표 첫 칸
            targets.append((ln.split("|")[1], False))
        if sec and sec.startswith("## 3.") and re.match(r"^### \d", ln):    # 3장 머리
            targets.append((ln[4:].split(" — ")[0], False))
        if sub and sub.startswith("### 1-2 ") and ln.startswith("| ") and not ln.startswith("| 규정명") and not ln.startswith("|---"):
            targets.append((ln.strip().strip("|").split("|")[5], True))   # 1-2 표 마지막 칸 — 모두 판단
        for s, all_judg in targets:
            n += 1
            bare = re.findall(r"(?<![\d(제])(\d{1,2}(?:·\d{1,2})*)조(?:\(판단\)|(?!\())", s)
            if bare:
                probs.append((f"{CO[co]} md {i + 1}줄", f"조 제목 없는 조 번호: {bare}"))
            for m in ART_TOKEN_RE.finditer(s):
                no, tt, pd = int(m.group(1)), m.group(2), m.group(4)
                if titles.get(no) != tt:
                    probs.append((f"{CO[co]} md {i + 1}줄", f"{no}조 제목 다름: 「{tt}」 / 조목록 「{titles.get(no)}」"))
                if (no not in REQ_ARTS or all_judg) and not pd:
                    probs.append((f"{CO[co]} md {i + 1}줄", f"{no}조 는 지시서에 없는 조(또는 판단 칸) — 「(판단)」 없음"))
    return n


# ───────────────────────────── 지시서 항목 대조 ─────────────────────────────
REQ_ITEMS = [
    ("9-4-1 목차", "그룹리스크관리규정(이름이 다르면 대응 규정)의 조문 목차 전체(조 번호와 제목). 전문이 있으면 전문"),
    ("9-4-1 iM", "iM 그룹 리스크관리규정은 28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음."),
    ("9-4-1 메리츠", "메리츠 그룹리스크관리규정 9조 7항, 57조가 인용되어 있음. 같은 방식으로 대조"),
    ("9-4-2 21·22·24", "21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부"),
    ("9-4-2 27", "27조 전략·평판위험: 관리 체제, 측정이나 평가 수단"),
    ("9-4-2 34", "34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고"),
    ("9-4-2 3", "3조: 위험이 경미한 자회사를 적용에서 빼는 기준"),
    ("9-4-2 17", "17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)"),
    ("9-4-2 55", "55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)"),
    ("9-4-2 53", "53조 위기대응조직: 구성과 전환 요건"),
    ("9-4-3", "위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구"),
    ("끝 표", "작업별로 \"받은 것 / 받지 못한 것 / 원문과 다른 것을 발견한 곳\"을 한 표로"),
    ("끝 조 번호", "01 엑셀판 '주제1_모범규준기준'의 어느 조 행에 넣을 자료인지 조 번호를 붙임"),
]
REQ6 = "## 6. 지시서 항목별 대조"


def check_req(co, lines, blocks, probs):
    req = req_text()
    if req:
        for lab, s in REQ_ITEMS:
            if s not in req:
                probs.append(("지시서", f"지시서 원문에 없는 문구(대조표 기준 문구 확인): {lab}"))
    ids = {b["qid"] for b in blocks if b["qid"]}
    heads = {re.match(r"^### (\S+) ", ln).group(1) for ln in lines if re.match(r"^### (\S+) ", ln)}
    sec = None
    rows = {}
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if sec and sec.startswith(REQ6) and ln.startswith("| ") and not ln.startswith("| 지시서 항목") \
                and not ln.startswith("|---"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows[cells[0]] = (i + 1, cells)
    if not rows:
        probs.append((f"{CO[co]} md", f"「{REQ6}」 표 없음"))
        return 0
    for lab, s in REQ_ITEMS:
        if lab not in rows:
            probs.append((f"{CO[co]} md 6장", f"지시서 항목 행 없음: {lab}"))
            continue
        ln_no, cells = rows[lab]
        if s not in cells[1]:
            probs.append((f"{CO[co]} md {ln_no}줄", f"지시서 원문 칸이 지시서와 다름: {lab}"))
        joined = " ".join(cells[2:])
        if not ("받은 글" in joined or "추출 범위에 없음" in joined or "해당 없음" in joined):
            probs.append((f"{CO[co]} md {ln_no}줄", f"받은 글/추출 범위에 없음 표시 없음: {lab}"))
        if "추출 범위에 없음" in joined and not any(w in joined for w in ("찾은 방법", "검색", "5장", "훑")):
            probs.append((f"{CO[co]} md {ln_no}줄", f"추출 범위에 없음인데 찾은 방법 없음: {lab}"))
        for q in re.findall(r"\b(" + QID + r")\b", joined):
            if q not in ids and q not in heads:
                probs.append((f"{CO[co]} md {ln_no}줄", f"없는 인용 번호: {q}"))
    return len(rows)


def check_notfound(co, lines, probs):
    """「추출 범위에 없음」 줄마다 찾은 방법 — 같은 줄, 같은 인용 절(검색 기록 5장을 가리킴), 3장 「찾은 범위」 줄."""
    n = 0
    sec = None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if "추출 범위에 없음" not in ln or sec is None:    # 머리(한계 ③ — 낱말 뜻 풀이)는 대상 아님
            continue
        n += 1
        if sec.startswith("## 검증 기록") or sec.startswith(REQ6):
            continue
        ok = any(w in ln for w in ("검색", "찾은 범위", "찾은 방법", "5장", "훑", "첨부", "반박"))
        if not ok:
            blk = lines[i:i + 8]
            ok = any("찾은 범위" in x for x in blk) or sec.startswith("## 0.") or sec.startswith("## 1.") or sec.startswith("## 2.")
        if not ok:
            probs.append((f"{CO[co]} md {i + 1}줄", "「추출 범위에 없음」에 찾은 방법 없음"))
    return n


# ───────────────────────────── 0장 표·3장 목록 ↔ 「모범규준 조:」 줄 ─────────────────────────────
def art_numbers(s):
    out = set()
    for g in re.finditer(r"(?<![\d제])(\d{1,2}(?:·\d{1,2})*)조", s):
        out.update(int(x) for x in g.group(1).split("·"))
    return out


def quote_arts(lines):
    arts, cur = {}, None
    for ln in lines:
        m = re.match(r"^### (" + QID + r") ", ln)
        if m:
            cur = m.group(1)
        elif ln.startswith("## "):
            cur = None
        if cur and ln.startswith("모범규준 조:"):
            arts[cur] = art_numbers(ln[len("모범규준 조:"):])
    return arts


def index_rows(lines, co):
    """0장 표 행: (줄 번호, 조 번호 집합, 인용 번호 목록), 3장 목록 줄: 같은 꼴."""
    t0, s3 = [], []
    sec, cur = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if sec and sec.startswith("## 0.") and re.match(r"^\| \d", ln):
            cells = ln.split("|")
            t0.append((i, art_numbers(cells[1]), re.findall(r"\((" + QID + r")\)", cells[4])))
        if sec and sec.startswith("## 3."):
            if re.match(r"^### \d", ln):
                cur = art_numbers(ln[4:].split(" — ")[0])
            if cur and ln.startswith(f"- {CO[co]}:"):
                s3.append((i, cur, re.findall(r"(" + QID + r")\(", ln)))
    return t0, s3


def check_index(co, lines, probs):
    arts = quote_arts(lines)
    t0, s3 = index_rows(lines, co)
    for lab, rows in (("0장 표", t0), ("3장 목록", s3)):
        for i, js, ids in rows:
            for q in ids:
                if q not in arts:
                    probs.append((f"{CO[co]} md {i + 1}줄 {lab}", f"없는 인용 {q}"))
                elif not (arts[q] & js):
                    probs.append((f"{CO[co]} md {i + 1}줄 {lab}", f"{q} 의 「모범규준 조:」 줄에 {sorted(js)}조 없음"))
            for q, a in arts.items():
                if a & js and q not in ids:
                    probs.append((f"{CO[co]} md {i + 1}줄 {lab}", f"{q} 는 {sorted(a & js)}조 인데 이 행에 없음"))
    return len(t0) + len(s3)


def check_attach(co, lines, probs):
    """1-1 첨부 표: 첫 쪽에 첨부 머리(「N. 이름」)가 있는지."""
    t = T(f"{co}_AR")
    pt = {p: nows(x) for p, x in t.pages_text().items()}
    n = 0
    in11 = False
    for i, ln in enumerate(lines):
        if ln.startswith("### 1-1 "):
            in11 = True
            continue
        if in11 and ln.startswith("#"):
            break
        m = re.match(r"^\| (\d+) \| ([^|]+?) \| p\.(\d+) \|", ln)
        if not (in11 and m):
            continue
        n += 1
        no, name, pg = m.group(1), nows(m.group(2)), int(m.group(3))
        head = f"{no}.{name}"
        if head not in pt.get(pg, ""):
            probs.append((f"{CO[co]} md {i + 1}줄 1-1 표", f"첨부 {no} 머리 「{head}」 가 p.{pg} 에 없음"))
        elif pg - 1 in pt and pt[pg - 1].startswith(head):      # 앞 쪽 머리글이 같은 첨부면 첫 쪽이 아님
            probs.append((f"{CO[co]} md {i + 1}줄 1-1 표", f"첨부 {no} 머리가 p.{pg - 1} 머리에도 있음(첫 쪽이 아님)"))
    return n


# ───────────────────────────── 보안·형식 ─────────────────────────────
def secret_values():
    vals = []
    for name in ("DART_API_KEY", "LAW_OC", "OC", "LAW_API_OC"):
        v = os.environ.get(name)
        if v and len(v) >= 4:
            vals.append(v)
    envp = os.path.join(ROOT, ".env")
    if os.path.exists(envp):
        for ln in open(envp, encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*['\"]?([^'\"\s]+)", ln)
            if m and ("KEY" in m.group(1) or "OC" in m.group(1)) and len(m.group(2)) >= 4:
                vals.append(m.group(2))
    return vals


def check_secrets(paths, probs):
    vals = secret_values()
    for p in paths:
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        for v in vals:
            if v in s:
                probs.append((p, "인증값 문자열이 파일에 있음(값은 적지 않음)"))
        if re.search(r"crtfc_key=(?!\*\*\*)\w", s) or re.search(r"[?&]OC=(?!\*\*\*)\w", s):
            probs.append((p, "crtfc_key=/OC= 뒤에 가리지 않은 값"))
    for dp, dn, fn in os.walk(OUTD):
        for f in fn:
            if f.lower().endswith(".pdf"):
                probs.append((os.path.join(dp, f), "산출 폴더에 PDF"))
    return len(vals)


# 원본 글이 아닌 「…」 표기(조각 대조에서 넘김) — 사유는 검증 기록에 적음
FRAG_ALLOW = {
    "닿는 모범규준 조": "md 1-2 표의 칸 이름(원본 글 아님)",
    "21·22·24 연결": "md 5장 검색 기록 표의 행 이름(원본 글 아님)",
}
# 글머리 목록 중간에서 끊겨도 되는 인용(사유)
CUT_LIST_OK = {}


# ───────────────────────────── 대조 실행 ─────────────────────────────
def run_check(write=True, md_override=None, csv_override=None, quiet=False):
    load_meta()
    probs, detail, stats = [], [], {}
    for co in ("H", "W"):
        text = md_override[co] if md_override else open(MD[co], encoding="utf-8").read()
        lines, blocks = parse_md(text)
        st = dict(blocks=len(blocks))
        recs = [check_quote(co, b, probs, detail) for b in blocks]
        st["exact"] = sum(1 for r in recs if r.get("exact"))
        st["same_ws"] = sum(1 for r in recs if r.get("same_ws") and not r.get("exact"))
        st["cut_list"] = [(r["qid"], r["cut_list"]) for r in recs if r.get("cut_list")]
        for qid, nx in st["cut_list"]:
            if qid not in CUT_LIST_OK:
                probs.append((f"{CO[co]} {qid}", f"인용이 글머리 목록 중간에서 끊김 — 다음 원본 줄 「{nx}」"))
        st["variant_rows"] = check_variants(co, lines, blocks, probs)
        st["search_rows"] = check_search(co, lines, probs)
        st["toc_rows"] = check_toc(co, lines, probs, rows=(csv_override[co] if csv_override else None))
        nfr, miss = check_frags(co, lines, blocks, probs)
        st["frags"] = nfr
        st["frags_allowed"] = [f for f in FRAG_ALLOW if any(f in ln for ln in lines)]
        st["art_lines"] = check_art_lines(co, lines, probs)
        st["index_rows"] = check_index(co, lines, probs)
        st["attach_rows"] = check_attach(co, lines, probs)
        st["req_rows"] = check_req(co, lines, blocks, probs)
        st["notfound_lines"] = check_notfound(co, lines, probs)
        nrec = sum(1 for ln in lines if ln.startswith("## 검증 기록"))
        if nrec != 1 or VREC not in lines:
            probs.append((f"{CO[co]} md", f"「{VREC}」 절 수 {nrec}"))
        else:
            last_h2 = [ln for ln in lines if ln.startswith("## ")][-1]
            if last_h2 != VREC:
                probs.append((f"{CO[co]} md", "검증 기록 절이 맨 끝이 아님"))
            rec_txt = "\n".join(lines[lines.index(VREC):])
            for jo in ("3조", "4·5조", "17조", "21조", "22조", "24조", "27조", "34조", "53조", "55조"):
                if jo not in rec_txt:
                    probs.append((f"{CO[co]} 검증 기록", f"반박 시도 기록에 {jo} 없음"))
        stats[co] = st
    nsec = check_secrets([MD["H"], MD["W"], TOC["H"], TOC["W"], OUT_TXT, __file__], probs)
    used = sorted({d["doc"] for d in detail if d.get("doc")} | {x for c in MAIN.values() for x in c} | {v for x in VARIANTS.values() for v in x})
    for k in used:
        if not DOCS[k]["txt_sha_ok"]:
            probs.append((k, "텍스트 sha256 가 텍스트목록.csv(risk8·risk9) 와 다름"))
    if write:
        out_lines = []
        W = out_lines.append
        W(f"# verify13_g_hana_woori — 대조 결과 ({TODAY} 표기; 실행 환경 날짜와 무관)")
        W("대상: " + ", ".join([MD["H"], MD["W"], TOC["H"], TOC["W"]]))
        W("원문(텍스트 sha256 을 텍스트목록.csv 와 대조): " + ", ".join(sorted({DOCS[k]['path'] for k in used})))
        W(f"인증값 대조용 값 수(환경변수·.env, 값은 적지 않음): {nsec}")
        for co in ("H", "W"):
            st = stats[co]
            W("")
            W(f"## {CO[co]}")
            W(f"- 인용 블록 {st['blocks']}개 — 글자까지 같음(줄 끝 공백만 무시) {st['exact']}, 공백만 다름 {st['same_ws']}")
            W(f"- 글머리 목록 중간에서 끊긴 인용(허용 목록 포함): {st['cut_list'] or '없음'}")
            W(f"- 4장 대조판 행 {st['variant_rows']}개, 5장 검색 기록 행 {st['search_rows']}개 다시 계산, 조문 목차 CSV {st['toc_rows']}행")
            W(f"- 「…」 조각 {st['frags']}개 대조 — 허용 목록(원본 글이 아닌 표기)으로 넘긴 것: {len(st['frags_allowed'])}개")
            W(f"- 「모범규준 조:」 줄·0장 표 조 칸 {st['art_lines']}개, 0장 표·3장 목록 {st['index_rows']}행(인용 번호 ↔ 조 줄 양방향), "
              f"1-1 첨부 표 {st['attach_rows']}행, 6장 지시서 항목 행 {st['req_rows']}개, 「추출 범위에 없음」 줄 {st['notfound_lines']}개")
            for d in detail:
                if d["co"] == co:
                    W(f"  - {d['qid']} (md {d['md_line']}줄, {d.get('nlines')}줄) {d.get('doc', '')} {d.get('cite_pages', '')} "
                      f"줄 {d.get('l1', '')}–{d.get('l2', '')}: {d.get('result')}")
        W("")
        W(f"## 문제 {len(probs)}개")
        for w, s in probs:
            W(f"- {w}: {s}")
        os.makedirs(WORK, exist_ok=True)
        open(OUT_TXT, "w", encoding="utf-8").write("\n".join(out_lines) + "\n")
        os.makedirs(VD, exist_ok=True)
        json.dump(dict(stats=stats, detail=detail, problems=probs), open(CHECK_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not quiet:
        print(f"인용 블록 하나 {stats['H']['blocks']}·우리 {stats['W']['blocks']} — 문제 {len(probs)}개 → {OUT_TXT}")
        for w, s in probs[:40]:
            print(f"  - {w}: {s[:220]}")
        if len(probs) > 40:
            print(f"  … (+{len(probs) - 40})")
    return probs, detail, stats


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "refute":
        refute()
        return 0
    if mode == "fix":
        return fix()
    probs, _, _ = run_check()
    return 0 if not probs else 1


# ───────────────────────────── 반박 검색(refute) ─────────────────────────────
# 조마다 원래 검색어(수집 에이전트 5장)보다 넓힌 정규식(낱말 변형·띄어쓰기·영문·동의어). 줄 단위 + 앞뒤 1줄을 이어 붙인 창에서 찾고,
# ctx 가 있으면 같은 창에 ctx 낱말이 있을 때만 남긴다. excl 은 먼저 지우는 말(예: 「비상임」).
REFUTE = {
    "3": dict(pat=r"경미|미미|중요(성|도)\s*(이|가)?\s*(낮|작)|중요하지\s*않|소규모|규모가\s*작|비중이\s*(작|낮)|"
                  r"적용\s*(을\s*)?(배제|제외|예외|범위|대상)|적용하지\s*(아니|않)|적용을\s*받지|"
                  r"(측정|관리|한도|모니터링|산출|통제|배분|설정)\s*대상\s*(에서|으로|은|이|자회사|계열사|회사)|"
                  r"대상\s*(자회사|계열사|종속기업|관계회사|그룹사)|제외(한다|하며|하고|되며|되어|됨|할\s*수)|[Mm]ateriality|[Ii]mmaterial|비중요|"
                  r"간편법|표준방법|약식|간이|특례|달리\s*정할|따로\s*정|별도로\s*(정|적용)",
              ctx=r"리스크|위험|내부통제|한도|자본", ctx2=r"자회사|계열사|종속|그룹사|관계회사|회사",
              label="경미·미미·소규모·중요성·적용 배제/제외/예외/범위/대상·측정/관리/한도/배분 대상·간편법·약식·특례·달리 정할·별도 적용"),
    "4·5": dict(pat=r"철학|원칙|기본\s*방침|기본\s*정책|리스크\s*문화|위험\s*문화|[Rr]isk\s*[Cc]ulture|최상위|가치\s*규범|핵심\s*가치|"
                    r"위험\s*성향|리스크\s*성향|[Rr]isk\s*[Aa]ppetite|RAF\b|선언문|리스크\s*관리\s*정책|위험\s*관리\s*정책|정책\s*규정|"
                    r"금융업의\s*본질|리스크\s*정책|위험\s*정책|[Pp]hilosophy|[Pp]rinciple",
                ctx=r"리스크|위험", label="철학·원칙·기본방침·리스크 문화·위험성향·리스크관리정책·리스크정책·정책규정·핵심가치·Philosophy·Principle"),
    "17": dict(pat=r"의사\s*(전달|소통|결정\s*사항)|정보\s*(전달|공유|교류)|공문|공식\s*(문서|적인\s*문서)|서면|문서\s*(로|화|를|에|형식|형태)|"
                   r"전자\s*(문서|결재|우편|메일)|통보|통지|시달|하달|지시|요청|요구|권고|가이드\s*라인|지침\s*(을|를)?\s*(시달|송부|전달)|"
                   r"송부|회신|협조\s*(요청|문)|업무\s*연락|커뮤니케이션|사전\s*(협의|보고|승인)|협의\s*(절차|사항)",
               ctx=r"리스크|위험|경영관리|내부통제|경영\s*의사", near=r"자회사|계열사|그룹사|종속|관계회사",
               label="의사전달·정보공유·공문·공식문서·서면·문서·전자문서/결재·통보·통지·시달·하달·지시·요청·권고·가이드라인·송부·사전협의/보고/승인"),
    "21·22·24": dict(pat=r"(그룹|연결|통합|지주).{0,25}(신용|시장|금리|이자율).{0,25}(측정|산출|합산|VaR|내부\s*자본|위험\s*자본|리스크\s*량|위험\s*량|한도|위험액)|"
                          r"(신용|시장|금리|이자율).{0,25}(그룹|연결|통합).{0,25}(측정|산출|합산|VaR|내부\s*자본|위험\s*자본|리스크\s*량|위험\s*량|위험액)|"
                          r"단순\s*(합|합산)|합산|[Gg]roup[- ]?wide|[Cc]onsolidat|분산\s*효과|상관\s*(관계|계수)|통합\s*(VaR|내부\s*자본|위험\s*자본|리스크\s*량|위험\s*량)|"
                          r"그룹\s*(차원|전체|통합|공통|일관)|일관된\s*(방법|기준)|동일한\s*(방법|기준|방식|척도)|공통\s*(방법|기준|척도|모형)|"
                          r"통합\s*리스크\s*관리\s*시스템|통합\s*위험\s*관리\s*시스템|내부\s*자본\s*(한도|배분|산출)",
                     ctx=r"신용|시장|금리|이자율|리스크|위험|자본", label="그룹·연결·통합 + 신용/시장/금리 + 측정·산출·합산, 단순합, 분산효과, 상관계수, 그룹 차원·일관된/동일한/공통 방법, 통합리스크관리시스템, 내부자본 한도·배분"),
    "27": dict(pat=r"평판|명성|이미지\s*(리스크|위험|훼손|실추|제고|손상)|[Rr]eputation|전략\s*(리스크|위험)|[Ss]trateg(y|ic)\s*[Rr]isk|"
                   r"사업\s*(리스크|위험)|[Bb]usiness\s*[Rr]isk|비재무\s*(리스크|위험|적)|비계량\s*(리스크|위험)|[Ee]merging\s*[Rr]isk|신규\s*리스크|잠재\s*리스크|"
                   r"[Tt]op\s*[Rr]isk|중요\s*리스크|기후\s*(리스크|위험)|ESG\s*리스크|여론|언론\s*보도|민원|신뢰도\s*(저하|하락|훼손)|"
                   r"기타\s*(리스크|위험)|비계량\s*위험|[Cc]onduct\s*[Rr]isk",
               ctx=None, excl=r"평판\s*조회|평판조회|평판 조회", label="평판·명성·이미지·전략/사업/비재무/잠재/신규/중요/기타 리스크·기후·ESG·여론·언론·신뢰도 저하"),
    "34": dict(pat=r"해외|글로벌|국외|국가\s*(별|위험|리스크|신용|한도|익스포)|국별|[Cc]ountry|현지\s*(법인|금융|규제|당국|점포)|외국|역외|"
                   r"[Cc]ross[- ]?[Bb]order|신흥국|[Gg]lobal|[Oo]verseas|진출|지역별",
               ctx=r"리스크|위험|한도|점검|검토|보고|모니터링|심의|관리", label="해외·글로벌·국외·국가·국별·현지·외국·역외·신흥국·Global·Overseas·진출·지역별"),
    "53": dict(pat=r"위기|비상|[Cc]ontingency|컨틴전시|대응\s*(조직|체계|체제|반|위원회|본부|팀)|대책\s*(반|위원회|본부|조직|회의)|상황\s*(반|실)|태스크|TF\b|"
                   r"[Cc]risis|자체\s*정상화|[Rr]ecovery|정리\s*계획|[Rr]esolution|전환\s*(요건|기준|조건)|비상\s*경영",
               ctx=None, excl=r"비상임|비상장|비상근|비상무|비상각|비상환|비상업|비상주",
               label="위기·비상·컨틴전시·대응/대책 조직·상황반·TF·Crisis·자체정상화·Recovery·전환 요건"),
    "55": dict(pat=r"조기\s*(경보|경고|감지|대응|인식|경계)|경보|경고|[Ww]arning|EWS|EWI|징후|위기\s*(단계|수준|지표|상황\s*단계|인식)|"
                   r"관심\s*단계|주의\s*단계|경계\s*단계|심각\s*단계|정상\s*단계|['‘]주\s*의['’]|[Tt]rigger|트리거|임계|발령|선행\s*지표|모니터링\s*지표|KRI\b|"
                   r"[Rr]ed\s*[Ll]ight|신호등|[Aa]lert|판단\s*지표|관리\s*지표|[Rr]isk\s*[Mm]ap|리스크\s*맵|상황판|[Dd]ash\s*[Bb]oard|이상\s*징후|"
                   r"단계별\s*(대응|조치|관리)|위기\s*상황\s*(단계|구분|판단)",
               ctx=None, excl=r"환경보호|경고\s*조치|경고장|주의\s*조치|기관\s*경고",
               label="조기경보·경보·경고·징후·위기단계·관심/주의/경계/심각 단계·Trigger·임계·발령·KRI·관리지표·Risk Map·상황판·단계별 대응"),
    "규정전문": dict(pat=r"그룹\s*리스크\s*관리\s*(규정|정책|지침|시행\s*세칙|세칙|기준)|그룹\s*위험\s*관리\s*(규정|정책|지침|기준)|리스크\s*관리\s*(규정|지침|세칙|기준)|"
                       r"위험\s*관리\s*(규정|지침|기준|정책)|위기\s*관리\s*규정|리스크\s*관리\s*정책\s*규정|리스크\s*관리\s*협의회\s*규정|리스크\s*관리\s*집행\s*위원회\s*규정|"
                       r"트레이딩\s*정책\s*규정|국가별\s*리스크\s*관리\s*지침|내부\s*통제\s*규정|리스크\s*정책|규정\s*제\s*\d+\s*조",
                   ctx=r"리스크|위험|내부통제", label="규정명(그룹리스크관리 규정·정책·지침·시행세칙·기준, 위험관리기준, 집행위원회규정, 트레이딩정책규정, 국가별리스크관리지침, 내부통제규정) + 「규정 제N조」 인용"),
}


def quoted_ranges(co):
    """md 에 이미 인용된 (문서 키, 시작 줄, 끝 줄) — 반박 결과에서 「이미 인용됨」 표시용."""
    out = []
    for path in (MD[co], os.path.join(PRE, os.path.basename(MD[co]))):
        if not os.path.exists(path):
            continue
        _, blocks = parse_md(open(path, encoding="utf-8").read())
        for b in blocks:
            m = CITE_RE.match(b["cite"] or "")
            if m:
                out.append((key_for_path(m.group("path")), int(m.group("l1")), int(m.group("l2"))))
    return out


def refute():
    """같은 출처(그 회사의 risk8 연차·사업·경영공시·대조판 + risk9 다른 기간 정기보고서)에서 넓힌 검색어로 다시 찾는다.
    결과 전부는 REFUTE_JSON(줄·쪽·글), 화면에는 조별 건수만. risk9 판은 FY2025 사업보고서에 같은 줄이 있으면 「중복」(dup=1),
    대조판(추가공시·정정) 줄이 본공시·원본에 그대로 있으면 dup=1, 이미 md 에 인용된 줄은 quoted=1."""
    load_meta()
    out = {"검색일": TODAY, "방법": "줄 단위 정규식 + 앞뒤 1줄을 이어 붙인 창(줄바꿈으로 갈린 낱말도 잡음) — ctx/ctx2/near 가 있는 조는 같은 창에 "
                                     "그 낱말이 있을 때만; excl 은 먼저 지움; risk9 판·대조판 줄이 같은 회사 FY2025 본 문서에 공백 무시로 그대로 있으면 dup=1; "
                                     "md 에 이미 인용된 줄은 quoted=1",
           "조": {}}
    qr = {co: quoted_ranges(co) for co in CO}
    for jo, spec in REFUTE.items():
        pat = re.compile(spec["pat"])
        ctx = re.compile(spec["ctx"]) if spec.get("ctx") else None
        ctx2 = re.compile(spec["ctx2"]) if spec.get("ctx2") else None
        near = re.compile(spec["near"]) if spec.get("near") else None
        excl = re.compile(spec["excl"]) if spec.get("excl") else None
        rec = {"검색어": spec["pat"], "ctx": spec.get("ctx"), "ctx2": spec.get("ctx2"), "near": spec.get("near"), "뺀말": spec.get("excl"),
               "label": spec["label"], "문서": {}}
        for co in CO:
            base = {"R9": T(f"{co}_BR").flat("raw")[0]}
            for k in [k for k in DOCS if DOCS[k]["co"] == co]:
                t = T(k)
                if k.startswith("R9_"):
                    ref = base["R9"]
                elif k in [v for x in VARIANTS.values() for v in x]:
                    src = [x for x, vs in VARIANTS.items() if k in vs][0]
                    ref = T(src).flat("raw")[0]
                else:
                    ref = None
                hits = []
                for i, ln in enumerate(t.lines):
                    if PAGE_RE.match(ln.strip()):
                        continue
                    s = ln.strip()
                    if not s:
                        continue
                    prev = t.lines[i - 1].strip() if i > 0 else ""
                    nxt = t.lines[i + 1].strip() if i + 1 < len(t.lines) else ""
                    win = f"{prev} {s} {nxt}"
                    body = excl.sub("", s) if excl else s
                    m = pat.search(body)
                    if not m:
                        j = body[-15:] + (excl.sub("", nxt) if excl else nxt)[:15]
                        m2 = pat.search(j)
                        if not (m2 and m2.start() < len(body[-15:]) < m2.end()):
                            continue
                    if ctx and not ctx.search(win):
                        continue
                    if ctx2 and not ctx2.search(win):
                        continue
                    if near and not near.search(win):
                        continue
                    dup = 1 if (ref is not None and len(nows(s)) >= 8 and nows(s) in ref) else 0
                    quoted = 1 if any(qk == k and a <= i + 1 <= z for qk, a, z in qr[co]) else 0
                    hits.append({"line": i + 1, "page": t.page[i], "text": s[:300], "dup": dup, "quoted": quoted})
                rec["문서"][k] = {"name": DOCS[k]["name"], "loc": DOCS[k]["loc"], "pages": t.npages, "n": len(hits),
                                 "n_new": sum(1 for h in hits if not h["dup"] and not h["quoted"]), "hits": hits}
        out["조"][jo] = rec
    os.makedirs(VD, exist_ok=True)
    json.dump(out, open(REFUTE_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for jo, rec in out["조"].items():
        parts = []
        for co in CO:
            a = sum(v["n"] for k, v in rec["문서"].items() if DOCS[k]["co"] == co)
            b = sum(v["n_new"] for k, v in rec["문서"].items() if DOCS[k]["co"] == co)
            parts.append(f"{CO[co]} 걸린 줄 {a}(새 줄 {b})")
        print(f"{jo}: " + " / ".join(parts))
    print("→", REFUTE_JSON)


# ───────────────────────────── 보정(fix) ─────────────────────────────
# 모든 보정은 검증 전 사본(pre/)에서 다시 만든다(멱등). 고친 곳은 FIXLOG 에 (회사, 전, 후, 사유)로 남겨 검증 기록 절에 적는다.
FIXLOG = {"H": [], "W": []}
SHORT_DOC = {"H_AR": "연차", "H_BR": "사업", "H_MD": "경영공시", "W_AR": "연차", "W_BR": "사업", "W_MD": "경영공시",
             "R9_20250317000894": "사업(2024.12)", "R9_20240314001383": "사업(2023.12)"}
# 0장 표·3장 목록과 맞추려고 「모범규준 조:」 줄에 더하는 조(수집 에이전트가 0장·3장에는 그 조 자리에 적었으나 조 줄에 빠뜨린 것)
TAG_ADD = {"H-04": [21, 22], "H-11": [21], "H-28": [53], "W-05": [21], "W-10": [21], "W-11": [17], "W-15": [17, 53], "W-28": [53]}
# 글머리 목록 중간에서 끊긴 인용 → 그 조 끝까지 늘림 (qid: (새 끝 줄, 새 머리 문구 전, 후))
EXTEND = {
    "H-14": (15485, "### H-14 첨부 3. 이사회 규정 제7조(결의사항 등) ① 1~12호 — ",
             "### H-14 첨부 3. 이사회 규정 제7조(결의사항 등) 조 전문(①1~15호·②) — "),
    "W-17": (9091, "### W-17 첨부3. 이사회규정 제7조(결의사항 등) ① 1~10호 — ",
             "### W-17 첨부3. 이사회규정 제7조(결의사항 등) 조 전문(①1~13호·②·③) — "),
}
# 「…」 안이 원본 글자와 다른 곳(md 설명 줄) → 원본 글자로
FRAG_FIX = {
    "H": [("「<하나금융지주> (연결기준) (1)·(2)」", "「<하나금융지주>」 「(연결기준)」 (1)·(2)"),
          ("텍스트의 탭 문자(「1.→BIS→자기자본의→적용범위」)는 PDF 글 뽑기 그대로.",
           "텍스트의 탭 문자(1.→BIS→자기자본의→적용범위 — →가 탭)는 PDF 글 뽑기 그대로.")],
    "W": [("「지주회사와 자회사등간 원활한 의사소통 및 협조체제」", "「우리금융지주(이하“지주회사”라 한다)와 자회사등간 원활한 의사소통 및 협조체제」"),
          ("「(라) 제4차」 머리 다음의 「마. 2025년 1분기 그룹리스크관리협의회 …」·「4. 의결안건 가.·나.」",
           "「(라) 2025년도 제4차 리스크관리위원회」 머리 다음의 「마. 2025년 1분기 그룹리스크관리협의회 …」·「4. 의결안건」 가.·나."),
          ("「(하) 제14차」 머리 다음의 「4. 심의안건 가.~다.」", "「(하) 2025년도 제14차 그룹리스크관리협의회」 머리 다음의 「4. 심의안건」 가.~다."),
          ("「2025 지배구조 및 보수체계 연차보고서 │ 27N │」", "「2025 지배구조 및 보수체계 연차보고서 │  273 │」(쪽마다 숫자만 다름)")],
}

NEW_QUOTES = {
    "H": [
        dict(qid="H-34", before="### H-10 ", key="H_AR", l1=11766, l2=11795,
             title="(검증 추가) 15. 감독당국 권고사항 — 금융감독원 정기검사(2023년 실시) 경영유의사항 3건·개선사항 가) — 「해외 자회사 여신을 포함」(중복차주 점검), 위기상황 내부유보자본",
             tags="34조(해외위험 관리)(판단); 21조(신용위험)(판단); 49조(자본계획)(판단); 56조(통합위기상황분석)(판단)",
             notes=["note: (검증 2026-10-07 추가) 반박 검색(34조·21·22·24조)에서 걸린 쪽 — H-10(리스크부문검사, p.291–p.292) 앞 절. 다)는 지주의 중복차주 점검 범위에 해외 자회사 여신을 넣으라는 지적(34조 해외위험 총괄과 닿는다고 판단).",
                    "note: 개선사항 13건 가운데 가) 만 옮김 — 나)~아)(p.290)와 자)~타)(p.291)는 자본비율 검증·이사회 운영·소개영업·성과평가·위험가중자산 관리 등, 파)(p.291)는 H-35. 이 문서의 「☞」는 가운뎃점 자리(H-02 note)."]),
        dict(qid="H-35", before="### H-10 ", key="H_AR", l1=11854, l2=11861,
             title="(검증 추가) 금융감독원 정기검사 개선사항 파) 「그룹 공동투자 리스크관리체계 개선」 — 「국내외 대체투자까지 확대」, 「비은행 합산 200억 이상의 투자로 한정」, 사전협의 절차·리스크관리위원회 사후보고",
             tags="34조(해외위험 관리)(판단) — 국내외 대체투자; 3조(적용대상)(판단) — 관리대상을 업무·금액 기준으로 한정했던 예; 15조(승인 및 사전협의)(판단); 16조(보고체계)(판단); 33조(그룹내 위험 전이 방지)(판단)",
             notes=["note: (판단) 그룹 공동투자 리스크의 관리대상이 부동산금융·비은행 합산 금액 기준으로 한정돼 있었다는 지적 — 경미한 자회사를 적용에서 빼는 기준(3조)과 꼴은 다르나 적용 범위를 정하는 기준의 예로 붙임. 해외 대체투자를 관리대상에 넣으라는 부분은 34조 자리."]),
        dict(qid="H-36", before="### H-16 ", key="H_AR", l1=17843, l2=17855,
             title="(검증 추가) 첨부 18. 그룹내부통제 규정 제6조(내부통제위원회) — ③ 「지배구조법 제3조 제3항에 해당하는 그룹사의 경우에는 본 조를 적용하지 아니한다」",
             tags="3조(적용대상)(판단) — 내부통제 쪽 적용 제외 조항",
             notes=["note: (판단) H-17(제2조③)과 같이 내부통제 규정 안의 적용 제외 — 위험관리 규정에서 위험이 경미한 자회사를 빼는 기준은 아님. 지배구조법 제3조 제3항의 내용은 이 문서에 없음(9-1 법령 원문 범위)."]),
        dict(qid="H-37", before="### H-16 ", key="H_AR", l1=17861, l2=17882,
             title="(검증 추가) 첨부 18. 그룹내부통제 규정 제7조(조직구조 및 업무분장) — ⑥ 「조언, 시정권고 및 자료제출요구」 권한, ⑧ 「사전에 해당 관계회사로부터 의견을 청취하는 등 그룹 내부의 의사소통을 원활하게」",
             tags="17조(의사전달체계)(판단); 14조(위험 통제)(판단)",
             notes=["note: (판단) 지주가 관계회사에 뜻을 전하는 수단(조언·시정권고·자료제출요구)과 사전 의견청취를 정한 조문 — 전달 문서의 형식은 같은 규정 제9조⑥(H-16).",
                    "note: 쪽이 바뀌는 자리(줄 17872–17875)의 쪽 표지·머리글 줄은 텍스트 그대로."]),
        dict(qid="H-39", before="### H-25 ", key="H_BR", l1=29588, l2=29599,
             title="(검증 추가) 연결 주석 「내부자본 적정성에 대한 기술」 — 「위험 유형별 및 관계기업별 내부자본 한도는 매년 1회 이상 그룹리스크관리위원회의 결의로 배분」, 한도 초과 예상 시 사전 승인",
             tags="21조(신용위험)(판단)·22조(시장위험)(판단)·24조(금리위험)(판단) — 위험 유형별 내부자본 한도; 47조(내부자본 한도 관리)(판단); 44조(통합 내부자본 산출)(판단)",
             notes=["note: (판단) 유형별·관계기업별 내부자본 한도를 그룹리스크관리위원회가 배분한다는 글 — 유형별 측정 방법이나 연결 기준 통합 측정·단순 합산 여부는 적혀 있지 않음(추출 범위에 없음, 검증 반박 21·22·24조 검색)."]),
        dict(qid="H-41", before="### H-25 ", key="H_BR", l1=75070, l2=75072,
             title="(검증 추가) 이사의 경영진단 및 분석의견(자산건전성) — 「당 그룹은」 「조기경보시스템 및 신용감리시스템을 통하여 잠재 부실 우려 차주들을 선제적 포착」",
             tags="55조(조기경보체계)(판단); 21조(신용위험)(판단)",
             notes=["note: (판단) 그룹 단위로 신용 조기경보시스템을 운영한다는 서술 — 지표 목록·발령 단계는 적혀 있지 않음. H-26(p.757)의 조기 경보 시스템과 같은 갈래. 첫 줄은 앞 문장의 끝부터 텍스트 줄 그대로."]),
        dict(qid="H-40", before="### H-33 ", key="H_MD", l1=3380, l2=3385,
             title="(검증 추가) 경영공시 「(1) 자본적정성 평가방법」 — 「리스크 종류별로 내부자본 한도를 설정」, 매월 신용·시장·운영위험가중자산 산출",
             tags="21조(신용위험)(판단)·22조(시장위험)(판단)·24조(금리위험)(판단); 47조(내부자본 한도 관리)(판단); 37조(자본적정성 평가 및 관리 체제)(판단)",
             notes=["note: 제목 줄의 탭 문자는 PDF 글 뽑기 그대로.",
                    "note: (판단) 규제자본(BIS 비율, 위험가중자산 매월 산출)과 내부자본(리스크 종류별 한도·한도소진율 매월) 두 측면 — 리스크 종류별 측정 방법·합산 방식은 적혀 있지 않음."]),
        dict(qid="H-38", before="## 3. 모범규준 조별", key="R9_20250317000894", l1=26988, l2=27003,
             title="(검증 추가, 다른 기간 판) 사업보고서(2024.12) 이사의 경영진단 — 「해외대체투자 자산에 대한 리스크관리」, 「한도 관리대상을 확대하고 관계회사별 한도 배분」",
             tags="34조(해외위험 관리)(판단); 26조(신용편중위험)(판단)",
             notes=["note: [표 깨짐: 문장 가운데(줄 26991–27000)에 자산건전성 표 줄과 DART 쪽 머리말·쪽 표지가 끼어 나옴 — 문장은 p.493 첫 줄 「도 등 관리 기준을 강화하였습니다.」로 이어짐(판단)]",
                    "note: (검증 2026-10-07 추가) FY2025 사업보고서의 같은 절(사업 p.733, H-41 근처)에는 이 문장이 없음 — 반박 검색에서 같은 회사 risk9 2024.12 판에서 찾음. 지주 내규 문구가 아니라 경영진단 서술.",
                    "note: (판단) 해외 대체투자 리스크를 평가위원회 평가대상 확대와 관계회사별 한도 배분으로 관리했다는 글 — 34조(해외위험 총괄·사전 검토) 자리. 해외위험 관리를 정한 내규 문구는 추출 범위에 없음."]),
    ],
    "W": [
        dict(qid="W-39", before="### W-03 ", key="W_AR", l1=1517, l2=1518,
             title="(검증 추가) 이사회 의결안건 — 「은행 국외영업점 Credit Risk 개선 진행현황」(LA지점, 美 감독당국 경과보고서)",
             tags="34조(해외위험 관리)(판단)",
             notes=["note: 같은 이름의 의안이 2025년 이사회 의결안건에 네 번 나옴 — p.40 줄 1517(이 인용), p.44 줄 1675, p.48 줄 1820(「은행 국외 영업점 Credit Risk 개선 진행현황(案)」), p.49 줄 1868.",
                    "note: (판단) 자회사(은행) 해외점포의 리스크 개선을 지주 이사회가 되풀이해 결의·점검한 사례 — 34조④⑤(정기 점검·보고) 자리. 해외위험 총괄을 정한 내규 문구는 아님."]),
        dict(qid="W-40", before="### W-04 ", key="W_AR", l1=3444, l2=3448,
             title="(검증 추가) 사외이사 발언(글로벌) — 「리스크 관리가 미흡한 해외 현지법인의 경우 비즈니스 비중을 조정하는 것이 우선적으로 고려되어야 함」",
             tags="34조(해외위험 관리)(판단)",
             notes=["note: p.95 「(다) 사외이사 김춘수」 절(줄 3424 이하)의 「관련 분야 주요 발언 및 토의 내용」 표 속 글로벌 칸.",
                    "note: (판단) 사외이사 의견 — 해외위험 관리 내규 문구는 아님."]),
        dict(qid="W-35", before="### W-04 ", key="W_AR", l1=3602, l2=3606,
             title="(검증 추가) 사외이사 발언(리스크관리) — 「자체정상화 계획의 자회사 유형 분류를 '대외적/대내적 중요도' 기준으로 재분류」, 「뱅크런 발동 지표인 '예수금 잔액 변동률 5% 초과'를 '잔액 감소율'로 변경」",
             tags="55조(조기경보체계)(판단) — 자체정상화계획의 발동 지표; 3조(적용대상)(판단) — 자회사 유형 분류(중요도); 57조(비상계획)(판단)",
             notes=["note: p.99 「(사) 사외이사 이은주」 절(줄 3579 이하)의 「관련 분야 주요 발언 및 토의 내용」 표 속 리스크관리 칸.",
                    "note: (판단) 자체정상화계획(금융산업구조개선법 체계) 안의 지표 하나·발동 기준 하나와 자회사 분류 기준을 다룬 사외이사 의견 — 지주 내규의 조기경보 지표 목록·발령 단계나 적용 배제 기준 문구는 아님(추출 범위에 없음)."]),
        dict(qid="W-36", before="### W-04 ", key="W_AR", l1=5607, l2=5610,
             title="(검증 추가) 감사위원회 보고안건 — 「지주 및 자회사 間 사전협의에 대한 지주 내규 일괄 개정」, 「자회사등경영관리규정」",
             tags="17조(의사전달체계)(판단); 15조(승인 및 사전협의)(판단)",
             notes=["note: (판단) 지주·자회사 사이 사전협의는 자회사등경영관리규정에 모아 두고 다른 지침의 중복 조항을 지웠다는 뜻으로 읽힘 — W-08(그룹리스크관리규정 일부 개정, 타 규정 사전협의 사항과 중복 항목 정비)과 같은 갈래. 자회사등경영관리규정 본문은 연차보고서에 첨부되지 않음 — 추출 범위에 없음(1-1 표, 검증 반박 규정전문 검색)."]),
        dict(qid="W-42", before="### W-11 ", key="W_AR", l1=6739, l2=6753,
             title="(검증 추가) 11. 그룹경영협의회 다. 운영현황·라. 활동내역 — 「목적사항을 각 위원 및 참석자에게 사전에 통지」, 이행상황 점검·보고, 「리스크관리/재무관리/ 내부통제 등 그룹의 중점과제」",
             tags="17조(의사전달체계)(판단)",
             notes=["note: (판단) 지주와 자회사 대표이사 협의체의 운영 방식(안건 사전 파악·사전 통지·이행상황 점검) — 의사전달의 문서 형식은 적혀 있지 않음. 규정 본문은 W-19."]),
        dict(qid="W-41", before="### W-32 ", key="W_MD", l1=5380, l2=5385,
             title="(검증 추가) 경영공시 「(1) 그룹의 자본적정성 평가방법」 — 바젤Ⅲ 자본규제 기준 BIS 자기자본비율(매분기)",
             tags="21조(신용위험)(판단)·22조(시장위험)(판단)·24조(금리위험)(판단); 37조(자본적정성 평가 및 관리 체제)(판단)",
             notes=["note: (판단) 그룹 자본적정성 평가를 BIS 비율(연결 규제자본)로만 적음 — 하나 경영공시의 같은 절(내부자본 리스크 종류별 한도)과 달리 내부자본 서술은 이 절에 없음. 리스크 유형별 연결 측정·단순 합산 여부는 추출 범위에 없음."]),
        dict(qid="W-37", before="## 3. 모범규준 조별", key="R9_20240314001383", l1=26386, l2=26410,
             title="(검증 추가, 다른 기간 판) 사업보고서(2023.12) 리스크관리위원회 2023.03.03 — 보고 「건전성 관리 위기대응체계 강화 운영(안)」",
             tags="53조(위기대응조직)(판단); 52조(위기관리체계)(판단)",
             notes=["note: [표 깨짐: 위원별 찬반 칸(찬성·선임전)이 의안 줄 사이에 끼어 나옴 — 위원 이름 칸은 줄 26375–26385]",
                    "note: (판단) 위기대응체계를 다룬 의안 이름만 — 체계의 구성·전환 요건 본문은 추출 범위에 없음(검증 반박 53조 검색). FY2025 세 문서에는 이 의안 이름이 걸리지 않음."]),
        dict(qid="W-38", before="## 3. 모범규준 조별", key="R9_20240314001383", l1=26543, l2=26545,
             title="(검증 추가, 다른 기간 판) 사업보고서(2023.12) 리스크관리위원회 2023.06.22 결의 — 「자체정상화위원회규정 일부 개정(案)」",
             tags="53조(위기대응조직)(판단); 57조(비상계획)(판단)",
             notes=["note: (판단) 자체정상화계획을 다루는 위원회 규정(자체정상화위원회규정)이 있다는 근거 — 규정 본문·위원회 구성·소집(전환) 요건은 추출 범위에 없음. FY2025 연차·사업보고서·경영공시와 2024.12 사업보고서에는 이 규정 이름이 걸리지 않음(검증 반박 규정전문·53조 검색)."]),
    ],
}

# 1-2 표·CSV 에 더하는 행 (규정명, 조번호, 조제목, 문서 키, 쪽, 전문여부, 모범규준 조(판단), 앞에 넣을 행의 (규정명, 조번호))
TOC_ADD = {
    "H": [("그룹내부통제 규정", "제6조", "내부통제위원회", "H_AR", "p.438", "Y(해당 조 전문 — 검증 추가 H-36)",
           "3조(적용대상)(판단) — ③ 적용 제외", ("그룹내부통제 규정", "제9조")),
          ("그룹내부통제 규정", "제7조", "조직구조 및 업무분장", "H_AR", "p.438", "Y(해당 조 전문 — 검증 추가 H-37)",
           "17조(의사전달체계)(판단)·14조(위험 통제)(판단) — ⑥⑧", ("그룹내부통제 규정", "제9조"))],
    "W": [("자회사등경영관리규정", "(조문 목차 추출 범위에 없음)", "-", "W_AR", "p.156",
           "N — 이름만(감사위원회 보고안건: 지주 및 자회사 間 사전협의 지주 내규 일괄 개정 — 검증 추가 W-36)",
           "17조(의사전달체계)(판단)·15조(승인 및 사전협의)(판단)", None),
          ("자체정상화위원회규정", "(조문 목차 추출 범위에 없음)", "-", "R9_20240314001383", "p.633",
           "N — 이름만(2023.06.22 리스크관리위원회 일부 개정 결의 — 검증 추가 W-38, 다른 기간 판)",
           "53조(위기대응조직)(판단)", None)],
}
DOC_SUFFIX = {("그룹내부통제 규정", "제6조"): " — 첨부 18", ("그룹내부통제 규정", "제7조"): " — 첨부 18",
              ("자회사등경영관리규정", "(조문 목차 추출 범위에 없음)"): " p.156 감사위원회 보고안건",
              ("자체정상화위원회규정", "(조문 목차 추출 범위에 없음)"): " p.633 리스크관리위원회 활동내역(다른 기간 판)"}
# 1-2 표 행의 전문여부 칸 고침(인용을 조 끝까지 늘린 행)
TOC_FIX = {
    "H": {("이사회 규정", "제7조"): "Y(해당 조 전문 — 검증 때 ①13~15호·② 까지 늘림, 규정 전문은 첨부 3 p.376–p.382)"},
    "W": {("이사회규정", "제7조"): "Y(해당 조 전문 — 검증 때 ①11~13호·②·③ 까지 늘림, 규정 전문은 첨부3 p.262–p.267)"},
}

ART_ORDER = ["3", "4·5", "17", "21", "22", "24", "27", "34", "53", "55"]
S3_HEAD = {
    "3": ("### 3조 적용대상 — ", "### 3조(적용대상) — "),
    "4·5": ("### 4·5조 위험관리 철학·원칙을 내규에 둔 회사와 문구", "### 4조(위험관리 철학)·5조(위험관리 원칙) — 위험관리 철학·원칙을 내규에 둔 회사와 문구"),
    "17": ("### 17조 의사전달체계 — ", "### 17조(의사전달체계) — "),
    "21": ("### 21조 신용위험 — ", "### 21조(신용위험) — "),
    "22": ("### 22조 시장위험 — ", "### 22조(시장위험) — "),
    "24": ("### 24조 금리위험 — ", "### 24조(금리위험) — "),
    "27": ("### 27조 전략 및 평판위험 — ", "### 27조(전략 및 평판위험) — "),
    "34": ("### 34조 해외위험 관리 — ", "### 34조(해외위험 관리) — "),
    "53": ("### 53조 위기대응조직 — ", "### 53조(위기대응조직) — "),
    "55": ("### 55조 조기경보체계 — ", "### 55조(조기경보체계) — "),
}
REF_KEY = {"3": "3", "4·5": "4·5", "17": "17", "21": "21·22·24", "22": "21·22·24", "24": "21·22·24", "27": "27", "34": "34",
           "53": "53", "55": "55"}

# 0장 요지 칸 끝에 붙이는 검증 보강 문구, 3장 조마다 붙이는 반박 결과 줄(결과만 — 검색어·건수는 검증 기록 표)
ZERO_ADD = {
    "H": {
        "3": "검증 보강(2026-10-07): 그룹내부통제 규정 제6조③ 적용 제외(H-36), 금감원 정기검사 개선사항 파) — 그룹 공동투자 리스크 관리대상을 업무·금액 기준으로 한정했던 것을 넓히라는 지적(H-35). 둘 다 경미 자회사 적용 배제 기준은 아님(판단) — 기준은 여전히 추출 범위에 없음.",
        "17": "검증 보강(2026-10-07): 그룹내부통제 규정 제7조⑥⑧ — 조언·시정권고·자료제출요구 권한, 사전 의견청취(H-37).",
        "21": "검증 보강(2026-10-07): 연결 주석 내부자본 적정성 — 위험 유형별·관계기업별 내부자본 한도 배분(H-39), 경영공시 자본적정성 평가방법 — 리스크 종류별 내부자본 한도(H-40), 금감원 정기검사 — 중복차주 점검에 해외 자회사 여신 포함(H-34), 경영진단 — 그룹 조기경보시스템(H-41).",
        "22": "검증 보강(2026-10-07): H-39·H-40(위험 유형별 내부자본 한도).",
        "24": "검증 보강(2026-10-07): H-39·H-40(위험 유형별 내부자본 한도).",
        "34": "검증 보강(2026-10-07): 금감원 정기검사 — 중복차주 점검에 해외 자회사 여신 포함(H-34), 그룹 공동투자 리스크 관리대상을 국내외 대체투자까지 확대(H-35); 2024.12 사업보고서 — 해외대체투자 한도 관리대상 확대·관계회사별 한도 배분(H-38). 해외위험 총괄 내규 문구는 여전히 추출 범위에 없음.",
        "55": "검증 보강(2026-10-07): 경영진단 — 그룹 조기경보시스템·신용감리시스템(H-41).",
    },
    "W": {
        "3": "검증 보강(2026-10-07): 사외이사 발언 — 자체정상화 계획의 자회사 유형 분류를 대외적/대내적 중요도 기준으로 재분류(W-35, 판단: 중요도에 따른 자회사 구분 사례). 적용 배제 기준은 여전히 추출 범위에 없음.",
        "17": "검증 보강(2026-10-07): 감사위원회 보고안건 — 지주 및 자회사 間 사전협의 지주 내규 일괄 개정(자회사등경영관리규정, W-36), 그룹경영협의회 운영현황 — 목적사항 사전 통지·이행상황 점검(W-42). 문서 형식은 여전히 추출 범위에 없음.",
        "21": "검증 보강(2026-10-07): 경영공시 그룹 자본적정성 평가방법 — BIS 비율만(W-41).",
        "22": "검증 보강(2026-10-07): W-41(경영공시 그룹 자본적정성 평가방법 — BIS 비율만).",
        "24": "검증 보강(2026-10-07): W-41(경영공시 그룹 자본적정성 평가방법 — BIS 비율만).",
        "34": "검증 보강(2026-10-07): 지주 이사회 의결안건 — 은행 국외영업점(LA지점) Credit Risk 개선 진행현황 네 번(W-39), 사외이사 발언 — 리스크 관리가 미흡한 해외 현지법인의 비즈니스 비중 조정(W-40). 해외위험 총괄 내규 문구는 여전히 추출 범위에 없음.",
        "53": "검증 보강(2026-10-07, 다른 기간 판 2023.12 사업보고서): 리스크관리위원회 보고 건전성 관리 위기대응체계 강화 운영(안)(W-37), 결의 자체정상화위원회규정 일부 개정(案)(W-38) — 의안 이름만. 구성·전환 요건은 여전히 추출 범위에 없음.",
        "55": "검증 보강(2026-10-07): 사외이사 발언 — 자체정상화계획의 뱅크런 발동 지표(예수금 잔액 변동률 5% 초과 → 잔액 감소율로 변경 제안, W-35) — 지표 하나·발동 기준 하나뿐. 그룹 조기경보 지표 목록·발령 단계는 여전히 추출 범위에 없음.",
    },
}
S3_ADD = {
    "H": {
        "3": "실패 — 부분 보강 H-36(그룹내부통제 규정 제6조③)·H-35(공동투자 관리대상 한정 지적). 위험이 경미한 자회사를 적용에서 빼는 기준은 추출 범위에 없음.",
        "4·5": "실패 — 걸린 것은 그룹 소비자리스크관리 정책, 연결 주석의 유동성 관리 원칙, 하나은행 파생상품 기본 원칙 등. 그룹 위험관리 원칙 문구(그룹 위험관리 정책 본문)는 추출 범위에 없음.",
        "17": "부분 성공 — H-37(그룹내부통제 규정 제7조⑥⑧) 추가. 제9조⑦의 관련 내규(공식문서로 전달할 사항)는 추출 범위에 없음.",
        "21": "실패 — 부분 보강 H-39·H-40(유형별 내부자본 한도)·H-34·H-41. 걸린 분산효과·상관관계는 보험자회사 K-ICS·공정가치 평가 주석. 그룹 유형별 연결 측정·단순 합산 여부는 추출 범위에 없음.",
        "22": "실패 — 부분 보강 H-39·H-40. 그룹 시장위험의 연결 측정 여부는 H-23(일관된 방법으로 산출) 밖에 추출 범위에 없음.",
        "24": "실패 — 부분 보강 H-39·H-40. 금리위험 합산값·연결 측정 여부는 추출 범위에 없음.",
        "27": "실패 — 걸린 것은 하나은행 정보보호 위험 서술(사업 p.852 평판저하), ELS 판매 중단에 따른 평판 악화(사업 p.102), 사외이사·최고경영자 후보 평판 등. 전략·평판위험 관리 체제·측정 수단은 추출 범위에 없음.",
        "34": "실패 — 부분 보강 H-34·H-35·H-38. 해외위험 총괄·사전 검토·정기 점검을 정한 내규 문구는 추출 범위에 없음.",
        "53": "실패 — 걸린 것은 자체정상화계획 갱신·모의훈련, 통합위기상황분석, 유동성 비상조달계획, 최고경영자 비상계획(경영승계), 하나은행 멕시코 법인 Contingency Plan 제재(사업 p.840·p.842). 위기대응조직 구성·전환 요건은 추출 범위에 없음.",
        "55": "실패 — 부분 보강 H-41. 걸린 손상징후·트리거 조항은 회계·유동화 주석. 지표 목록·발령 단계는 추출 범위에 없음.",
    },
    "W": {
        "3": "실패 — 부분 보강 W-35(자체정상화 계획의 자회사 유형 분류). 위험이 경미한 자회사를 적용에서 빼는 기준은 추출 범위에 없음.",
        "4·5": "새 문구 없음 — 원래 받은 글(W-04·W-21) 그대로. 철학·원칙이 실린 내규 이름은 추출 범위에 없음.",
        "17": "부분 보강 — W-36(자회사등경영관리규정 이름)·W-42(그룹경영협의회 운영). 지주가 자회사에 뜻을 전하는 문서 형식은 추출 범위에 없음.",
        "21": "실패 — 부분 보강 W-41(그룹 자본적정성은 BIS 비율로 평가). 그룹 유형별 연결 측정·단순 합산 여부는 추출 범위에 없음.",
        "22": "실패 — 부분 보강 W-41. 그룹 시장위험 합산 방식은 추출 범위에 없음.",
        "24": "실패 — 부분 보강 W-41. 금리위험 합산값·연결 측정 여부는 추출 범위에 없음.",
        "27": "실패 — 걸린 것은 우리금융캐피탈 정보보호(W-29), 회사 이미지·투명성 등. 전략·평판위험 관리 체제·측정 수단은 추출 범위에 없음.",
        "34": "실패 — 부분 보강 W-39(지주 이사회의 국외영업점 Credit Risk 개선 진행현황 결의)·W-40(사외이사 발언). 해외위험 총괄·사전 검토·정기 점검을 정한 내규 문구는 추출 범위에 없음.",
        "53": "부분 보강 — W-37·W-38(2023.12 사업보고서의 위기대응체계 의안·자체정상화위원회규정 이름). 위기대응조직의 구성·전환 요건은 추출 범위에 없음.",
        "55": "부분 보강 — W-35(뱅크런 발동 지표 하나). 걸린 조기경보 등급·KRI 는 연결 주석의 신용위험 유의적 증가 판단 요소·운영리스크 지표. 그룹 조기경보 지표 목록·발령 단계는 추출 범위에 없음.",
    },
}

REQ6_ROWS = {
    "H": [
        ("9-4-1 목차", "그룹리스크관리규정 조문 목차·전문: 추출 범위에 없음. 받은 글: 대응 규정 리스크관리위원회 규정 전문(H-11), 경영관리협의회 규정 전문(H-15), 그룹내부통제 규정 제2조·제6조·제7조·제9조(H-17·H-36·H-37·H-16), 지배구조 내부규범 제17조(H-12), 이사회 규정 제4조·제7조(H-13·H-14), 규정 이름·연혁(H-02·H-03·H-04·H-06)",
         "찾은 방법: 연차보고서 첨부 1~19 끝까지 훑음(1-1 표), 5장 규정 이름 검색, 검증 반박 규정전문 검색(검증 기록 표)"),
        ("9-4-1 iM", "해당 없음(iM 항목) — 하나는 그룹리스크관리규정 전문이 추출 범위에 없어 조 번호 맞대기 표를 만들지 못함(1-2 표 note)", "1-2 표"),
        ("9-4-1 메리츠", "해당 없음(메리츠 항목) — 같은 방식의 대조는 전문을 받은 리스크관리위원회 규정·경영관리협의회 규정 조문으로만 1-2 표 마지막 칸에 적음", "1-2 표"),
        ("9-4-2 21·22·24", "받은 글: H-22·H-23·H-24·H-26·H-27·H-28·H-32·H-10·H-39·H-40 (유형별 측정·한도·통합 내부자본). 연결 기준 통합 측정 / 단순 합산 여부를 적은 글: 추출 범위에 없음",
         "5장 21조·22조·24조·21·22·24 연결 줄, 검증 반박 21·22·24조 검색"),
        ("9-4-2 27", "받은 글: H-24b(운영위험 손실사건 정의 속 평판손실)뿐. 관리 체제·측정 수단: 추출 범위에 없음", "5장 27조 줄, 검증 반박 27조 검색"),
        ("9-4-2 34", "받은 글: H-04·H-05·H-08·H-09·H-11·H-15·H-26·H-33·H-34·H-35·H-38. 해외위험 총괄·사전 검토·정기 점검·보고를 정한 내규 문구: 추출 범위에 없음", "5장 34조 줄, 검증 반박 34조 검색"),
        ("9-4-2 3", "받은 글(유사 문구): H-17·H-36(내부통제 규정 적용 범위·적용 제외)·H-21·H-31·H-32·H-35. 위험이 경미한 자회사를 적용에서 빼는 기준: 추출 범위에 없음", "5장 3조 줄, 검증 반박 3조 검색"),
        ("9-4-2 17", "받은 글: H-16(제9조⑥ 공식문서·전자문서), H-37(제7조 조언·시정권고·자료제출요구·의견청취), H-09(전자문서로 통지), H-15·H-10. 제9조⑦의 관련 내규: 추출 범위에 없음", "5장 17조 줄, 검증 반박 17조 검색"),
        ("9-4-2 55", "받은 글: H-26·H-27·H-28·H-33·H-41 (조기경보 시스템·지표가 있다는 서술). 지표 목록·발령 단계: 추출 범위에 없음", "5장 55조 줄, 검증 반박 55조 검색"),
        ("9-4-2 53", "받은 글: H-07·H-08·H-14·H-25·H-28 (통합위기상황분석·비상조달계획·자체정상화계획). 위기대응조직의 구성·전환 요건: 추출 범위에 없음", "5장 53조 줄, 검증 반박 53조 검색"),
        ("9-4-3", "받은 글: H-02(그룹 위험관리 정책 — 최상위 규범, 핵심 원칙 제시), H-03, H-04(금융업의 본질 인식), H-21, H-25. 원칙 문구 자체(정책 본문): 추출 범위에 없음", "5장 4·5조 줄, 검증 반박 4·5조 검색"),
        ("끝 표", "받은 글: 0장 표(조별 받은 것 / 추출 범위에 없음)·3장·4장(원문과 다른 곳)·검증 기록 — 작업 전체를 묶는 한 표는 00_목록(메인)", "0장·3장·4장, 5장 검색 기록·검증 기록 반박 표"),
        ("끝 조 번호", "받은 글: 인용마다 모범규준 조 줄(N조(조 제목), 지시서에 없는 조는 (판단)), 0장 표 첫 칸, 1-2 표 마지막 칸·CSV 닿는모범규준조(판단) 칸", "모범규준_조목록.csv(2016.8.1 판 제목)"),
    ],
    "W": [
        ("9-4-1 목차", "그룹리스크관리규정 조문 목차·전문: 추출 범위에 없음. 받은 글: 대응 규정 리스크관리위원회규정 전문(W-15), 그룹경영협의회규정 전문(W-19), 지배구조 내부규범 제18조(W-16), 이사회규정 제7조(W-17), 규정 이름·연혁(W-02·W-03·W-06·W-08·W-13·W-14), 자회사등경영관리규정 이름(W-36), 자체정상화위원회규정 이름(W-38)",
         "찾은 방법: 연차보고서 첨부1~12·중임 사외이사 검토보고서까지 훑음(1-1 표), 5장 규정 이름 검색, 검증 반박 규정전문 검색(검증 기록 표)"),
        ("9-4-1 iM", "해당 없음(iM 항목) — 우리는 그룹리스크관리규정 전문이 추출 범위에 없어 조 번호 맞대기 표를 만들지 못함(1-2 표 note)", "1-2 표"),
        ("9-4-1 메리츠", "해당 없음(메리츠 항목) — 같은 방식의 대조는 전문을 받은 리스크관리위원회규정·그룹경영협의회규정 조문으로만 1-2 표 마지막 칸에 적음", "1-2 표"),
        ("9-4-2 21·22·24", "받은 글: W-22·W-23·W-26·W-32·W-34·W-08·W-05·W-10·W-41 (유형별 측정 방법·간편법 대상·내부자본 배분·BIS). 연결 기준 통합 측정 / 단순 합산 여부를 적은 글: 추출 범위에 없음",
         "5장 21조·22조·24조·21·22·24 연결 줄, 검증 반박 21·22·24조 검색"),
        ("9-4-2 27", "받은 글: W-29(우리금융캐피탈 정보보호 서술 속 평판 리스크)뿐. 관리 체제·측정 수단: 추출 범위에 없음", "5장 27조 줄, 검증 반박 27조 검색"),
        ("9-4-2 34", "받은 글: W-05·W-07·W-10·W-11·W-14·W-15·W-21·W-25·W-28·W-33·W-39·W-40. 해외위험 총괄·사전 검토·정기 점검·보고를 정한 내규 문구: 추출 범위에 없음", "5장 34조 줄, 검증 반박 34조 검색"),
        ("9-4-2 3", "받은 글(유사 문구): W-23·W-26·W-31·W-32·W-05·W-11·W-35. 위험이 경미한 자회사를 적용에서 빼는 기준: 추출 범위에 없음", "5장 3조 줄, 검증 반박 3조 검색"),
        ("9-4-2 17", "받은 글: W-19·W-42(그룹경영협의회), W-36(자회사등경영관리규정 이름), W-15·W-11. 지주가 자회사에 뜻을 전하는 문서 형식: 추출 범위에 없음", "5장 17조 줄, 검증 반박 17조 검색"),
        ("9-4-2 55", "받은 글: W-28·W-33(우리은행 단위), W-35(뱅크런 발동 지표 하나). 그룹 지표 목록·발령 단계: 추출 범위에 없음", "5장 55조 줄, 검증 반박 55조 검색"),
        ("9-4-2 53", "받은 글: W-06·W-07·W-09·W-15·W-28·W-37·W-38 (통합위기상황분석·위기대응계획·비상조달계획·자체정상화). 위기대응조직의 구성·전환 요건: 추출 범위에 없음", "5장 53조 줄, 검증 반박 53조 검색"),
        ("9-4-3", "받은 글: W-04(그룹 리스크관리 철학·원칙 1~5), W-21(사업보고서 원칙 1~5). 실린 내규 이름: 추출 범위에 없음(그룹리스크관리정책으로 추정 — 판단)", "5장 4·5조 줄, 검증 반박 4·5조 검색"),
        ("끝 표", "받은 글: 0장 표(조별 받은 것 / 추출 범위에 없음)·3장·4장(원문과 다른 곳)·검증 기록 — 작업 전체를 묶는 한 표는 00_목록(메인)", "0장·3장·4장, 5장 검색 기록·검증 기록 반박 표"),
        ("끝 조 번호", "받은 글: 인용마다 모범규준 조 줄(N조(조 제목), 지시서에 없는 조는 (판단)), 0장 표 첫 칸, 1-2 표 마지막 칸·CSV 닿는모범규준조(판단) 칸", "모범규준_조목록.csv(2016.8.1 판 제목)"),
    ],
}


def ensure_pre():
    os.makedirs(PRE, exist_ok=True)
    for co in CO:
        for path in (MD[co], TOC[co]):
            dst = os.path.join(PRE, os.path.basename(path))
            if not os.path.exists(dst):
                data = subprocess.run(["git", "show", f"{PRE_COMMIT}:{path}"], capture_output=True, check=True).stdout
                open(dst, "wb").write(data)


def rep(co, s, old, new, why, count=1, log=True):
    n = s.count(old)
    if n != count:
        raise SystemExit(f"보정 실패({CO[co]}): 「{old[:80]}」 {n}곳(기대 {count})")
    if log:
        FIXLOG[co].append((old, new, why))
    return s.replace(old, new)


def cite_line(key, l1, l2):
    load_meta()
    d, t = DOCS[key], T(key)
    p1, p2 = t.page[l1 - 1], t.page[l2 - 1]
    lab = f"p.{p1}" if p1 == p2 else f"p.{p1}–p.{p2}"
    path = d["path"].replace(os.sep, "/")
    return f"[{d['name']} · {d['loc']} · 쪽 {lab} · 줄 {l1}–{l2} · `{path}` · 원본 수집 {d['fetched'][:10]} · 인용 {TODAY}]", lab


def code_body(key, l1, l2):
    return [x.rstrip() for x in T(key).lines[l1 - 1:l2]]


def quote_section(q):
    cite, _ = cite_line(q["key"], q["l1"], q["l2"])
    out = [f"### {q['qid']} {q['title']}", "", f"모범규준 조: {q['tags']}", "", cite, "", "```text"]
    out += code_body(q["key"], q["l1"], q["l2"])
    out += ["```", ""]
    for n in q["notes"]:
        out += [n, ""]
    return "\n".join(out) + "\n"


# ── 모범규준 조 표기 바꾸기: 「N조」 → 「N조(조 제목)」, 지시서 밖 조·판단 묶음은 「(판단)」 ──
GROUP_ART_RE = re.compile(r"(\d{1,2}(?:·\d{1,2})*)조((?:[①-⑳](?:[\d~·]*호)?)*)")


def conv_group(g, titles, force_judg, logs):
    if not GROUP_ART_RE.search(g):
        return g
    if any(m.group(1) in titles.values() for m in re.finditer(r"\d{1,2}조\(([^()]*)\)", g)):
        return g      # 이미 「N조(제목)」 꼴
    judg = force_judg or ("판단" in g)
    toks, last = [], 0
    for m in GROUP_ART_RE.finditer(g):
        between = g[last:m.start()]
        if between.strip("·") .strip():
            toks.append(("text", between))
        nums = [int(x) for x in m.group(1).split("·")]
        for i, n in enumerate(nums):
            hang = m.group(2) if i == len(nums) - 1 else ""
            j = judg or n not in REQ_ARTS
            if j and not judg:
                logs.append(f"{n}조 — 지시서에 없는 조인데 (판단) 표시가 없었음 → (판단)")
            toks.append(("art", f"{n}조({titles[n]}){hang}{'(판단)' if j else ''}"))
        last = m.end()
    tail = g[last:]
    # 꼬리: (판단 — X) / (판단, X) / (판단: X) / (판단) / (X) / 「 관련 조항」 등
    tail2 = tail
    m = re.match(r"^(?P<pre>[^()]*)\((?P<par>[^()]*)\)(?P<post>.*)$", tail)
    extra = ""
    if m:
        par = m.group("par")
        par = re.sub(r"^판단\s*(—|,|:)?\s*", "", par).strip()
        extra = f" — {par}" if par else ""
        tail2 = m.group("pre") + m.group("post")
    out = []
    for i, (kind, v) in enumerate(toks):
        if kind == "art":
            if out and toks[i - 1][0] == "art":
                out.append("·")
            out.append(v)
        else:
            out.append(v)
    return "".join(out) + tail2.rstrip() + extra


def conv_tags(s, titles, force_judg=False, logs=None):
    logs = logs if logs is not None else []
    return "; ".join(conv_group(g, titles, force_judg, logs) for g in s.split("; "))


def fix():
    ensure_pre()
    load_meta()
    titles = jo_titles()
    if not os.path.exists(REFUTE_JSON):
        refute()
    ref = json.load(open(REFUTE_JSON, encoding="utf-8"))
    for co in CO:
        FIXLOG[co].clear()
    out_md, out_csv = {}, {}
    pre_stats = {}
    pre_md = {co: open(os.path.join(PRE, os.path.basename(MD[co])), encoding="utf-8").read() for co in CO}
    pre_csv = {co: read_csv(os.path.join(PRE, os.path.basename(TOC[co]))) for co in CO}
    pre_probs, pre_detail, pre_st = run_check(write=False, md_override=pre_md, csv_override=pre_csv, quiet=True)
    for co in CO:
        s = open(os.path.join(PRE, os.path.basename(MD[co])), encoding="utf-8").read()
        pre_lines, pre_blocks = parse_md(s)
        pre_frag = sum(len(FRAG_RE.findall(ln)) for ln in pre_lines)
        pre_stats[co] = dict(blocks=len(pre_blocks), frags=pre_frag, lines=len(pre_lines), exact=pre_st[co]["exact"],
                             same_ws=pre_st[co]["same_ws"], probs=[x for x in pre_probs if x[0].startswith(CO[co])])
        # (1) 「…」 조각을 원본 글자로
        for old, new in FRAG_FIX[co]:
            s = rep(co, s, old, new, "「…」 안이 원본 글자와 다름(조각 대조) → 원본 글자로", count=s.count(old) or 1)
        # (2) 글머리 목록 중간에서 끊긴 인용 → 조 끝까지
        lines, blocks = parse_md(s)
        for qid, (new_l2, h_old, h_new) in EXTEND.items():
            if not qid.startswith(co):
                continue
            b = next(x for x in blocks if x["qid"] == qid)
            m = CITE_RE.match(b["cite"])
            key = key_for_path(m.group("path"))
            l1 = int(m.group("l1"))
            new_cite, _ = cite_line(key, l1, new_l2)
            old_block = b["cite"] + "\n\n```text\n" + "\n".join(b["body"]) + "\n```"
            new_block = new_cite + "\n\n```text\n" + "\n".join(code_body(key, l1, new_l2)) + "\n```"
            s = rep(co, s, old_block, new_block, f"{qid} 인용이 글머리 목록 중간에서 끊김 → 그 조 끝까지 늘림(줄 {m.group('l1')}–{m.group('l2')} → {l1}–{new_l2})", log=False)
            FIXLOG[co].append((f"{qid} 줄 {m.group('l1')}–{m.group('l2')}({m.group('pages')})", f"{qid} 줄 {l1}–{new_l2}({cite_line(key, l1, new_l2)[1]})",
                               "인용이 글머리 목록 중간에서 끊김(다음 원본 줄이 같은 꼴의 다음 호) → 그 조 끝(다음 조 앞)까지 늘림"))
            s = rep(co, s, h_old, h_new, f"{qid} 머리 — 인용 범위를 늘린 데 맞춤")
        if co == "H":
            s = rep(co, s, "| 이사회 규정 | 제7조 | 결의사항 등 | p.378 | 부분(①1~12호 — ①13~15호·② 는 인용 밖, 규정 전문은 첨부 3 p.376–p.382) |",
                    "| 이사회 규정 | 제7조 | 결의사항 등 | p.378 | " + TOC_FIX["H"][("이사회 규정", "제7조")] + " |", "H-14 인용을 늘린 데 맞춤")
        else:
            s = rep(co, s, "| 이사회규정 | 제7조 | 결의사항 등 | p.263 | 부분(①1~10호 — 11호 이하·② 는 인용 밖, 규정 전문은 첨부3 p.262–p.267) |",
                    "| 이사회규정 | 제7조 | 결의사항 등 | p.263 | " + TOC_FIX["W"][("이사회규정", "제7조")] + " |", "W-17 인용을 늘린 데 맞춤")
        s = rep(co, s, "(문서·URL 칸 포함; 「닿는 모범규준 조」 칸은 md 에만)",
                "(문서·URL 칸 포함; 「닿는 모범규준 조」 칸은 검증 때 CSV 에도 닿는모범규준조(판단) 칸으로 더함)", "CSV 에 모범규준 조 칸을 더한 데 맞춤")
        # (3) 새 인용 넣기
        for q in NEW_QUOTES[co]:
            anchor = q["before"]
            idx = s.find("\n" + anchor)
            if idx < 0:
                raise SystemExit(f"앵커 없음: {anchor}")
            s = s[:idx + 1] + quote_section(q) + s[idx + 1:]
        # (4) 「모범규준 조:」 줄 — 0장·3장과 맞추려고 조 더하기, 「N조(제목)」 꼴로
        lines = s.split("\n")
        cur = None
        new_ids = {q["qid"] for q in NEW_QUOTES[co]}
        for i, ln in enumerate(lines):
            m = re.match(r"^### (" + QID + r") ", ln)
            if m:
                cur = m.group(1)
            elif ln.startswith("## "):
                cur = None
            if cur and ln.startswith("모범규준 조: ") and cur not in new_ids:
                body = ln[len("모범규준 조: "):]
                add = TAG_ADD.get(cur, [])
                logs = []
                nb = conv_tags(body, titles, logs=logs)
                if add:
                    nb += "; " + "·".join(f"{n}조({titles[n]})(판단)" for n in add) + " — 0장·3장 목록에 있던 자리(검증 때 조 줄에 더함)"
                newln = "모범규준 조: " + nb
                if newln != ln:
                    why = "조 번호에 조 제목(2016.8.1 판) 붙임" + ("; " + "; ".join(logs) if logs else "") + \
                          (f"; 0장·3장 목록에 있던 {'·'.join(str(x) for x in add)}조를 조 줄에 더함(판단)" if add else "")
                    FIXLOG[co].append((f"{cur} {ln}", newln, why))
                    lines[i] = newln
        s = "\n".join(lines)
        # (5) 1-2 표 마지막 칸 — 「N조(제목)(판단)」, 새 행
        lines = s.split("\n")
        in12, rows12 = False, []
        for i, ln in enumerate(lines):
            if ln.startswith("### 1-2 "):
                in12 = True
                continue
            if in12 and ln.startswith("#"):
                break
            if in12 and ln.startswith("| ") and not ln.startswith("| 규정명") and not ln.startswith("|---"):
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if cells[5] != "-":
                    nc = conv_tags(cells[5], titles, force_judg=True)
                    if nc != cells[5]:
                        cells[5] = nc
                lines[i] = "| " + " | ".join(cells) + " |"
                rows12.append(i)
        for (nm, jo, tt, key, pg, full, art, before) in TOC_ADD[co]:
            row = f"| {nm} | {jo} | {tt} | {pg} | {full} | {art} |"
            if before:
                at = next(i for i in rows12 if lines[i].startswith(f"| {before[0]} | {before[1]} |"))
            else:
                at = rows12[-1] + 1
            lines.insert(at, row)
            rows12 = [x + 1 if x >= at else x for x in rows12] + [at]
            rows12.sort()
            FIXLOG[co].append(("(행 없음)", row, "검증 때 찾은 규정 이름·조문을 1-2 표·CSV 에 더함"))
        FIXLOG[co].append(("1-2 표 「닿는 모범규준 조(판단)」 칸 「N조」", "「N조(조 제목)(판단)」", "조 제목(2016.8.1 판)과 판단 표시 — 칸 전체가 판단"))
        s = "\n".join(lines)
        # CSV
        rows = read_csv(os.path.join(PRE, os.path.basename(TOC[co])))
        tab = toc_rows_md(s.split("\n"))
        by = {(r["규정명"], r["조번호"]): r for r in rows}
        new_rows = []
        for cells in tab:
            k = (cells[0], cells[1])
            if k in by:
                r = dict(by[k])
            else:
                add = next(x for x in TOC_ADD[co] if (x[0], x[1]) == k)
                d = DOCS[add[3]]
                r = {"회사": CO[co], "규정명": add[0], "조번호": add[1], "조제목": add[2], "문서": d["name"] + DOC_SUFFIX.get(k, ""),
                     "접수번호또는URL": d["loc"], "쪽": add[4], "전문여부": add[5]}
            r["조제목"], r["쪽"], r["전문여부"] = cells[2], cells[3], cells[4]
            r[TOC_ART] = cells[5]
            new_rows.append(r)
        out_csv[co] = new_rows
        # (6) 0장 표·3장 목록·3장 머리
        s = rebuild_index(co, s, titles)
        # (7) 4장 표 다시 셈
        s = rebuild_variants(co, s)
        # (8) 머리 — 검증 줄
        s = rep(co, s, "\n\n## 0. 모범규준 조 → 찾은 곳 (요약)",
                "\n" + header_add(co) + "\n## 0. 모범규준 조 → 찾은 곳 (요약)", "머리에 검증 보정 안내 줄 더함", log=False)
        # (9) 6장 지시서 항목별 대조
        s = s.rstrip("\n") + "\n\n" + section6(co) + "\n"
        out_md[co] = s
    # 검증 기록: 보정한 글을 한 번 대조해 수를 셈
    for co in CO:
        out_md[co] = out_md[co].rstrip("\n") + "\n\n" + VREC + "\n\n(작성 중)\n"
    probs, detail, stats = run_check(write=False, md_override=out_md, csv_override=out_csv, quiet=True)
    for co in CO:
        rec = verification_record(co, pre_stats[co], stats[co], [d for d in detail if d["co"] == co], ref, probs)
        out_md[co] = out_md[co].split("\n" + VREC + "\n")[0].rstrip("\n") + "\n\n" + rec
    for co in CO:
        open(MD[co], "w", encoding="utf-8").write(out_md[co])
        write_toc(TOC[co], out_csv[co])
    json.dump({CO[co]: [dict(전=a, 후=b, 사유=c) for a, b, c in FIXLOG[co]] for co in CO},
              open(FIX_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    probs, _, _ = run_check(write=False, quiet=True)
    for co in CO:     # 남은 문제 수를 보정 뒤 대조 결과로 채움
        n = sum(1 for w, _ in probs if w.startswith(CO[co]))
        out_md[co] = out_md[co].replace("@@NPROB@@", f"{n}개" + ("(문제 0 — 대조 exit 0)" if not probs else ""))
        open(MD[co], "w", encoding="utf-8").write(out_md[co])
    probs, _, _ = run_check()
    return 0 if not probs else 1


def write_toc(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TOC_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in TOC_COLS})


def quote_index(lines):
    """인용 번호 → (모범규준 조 집합, 문서 짧은 이름, 쪽 표기), md 차례."""
    out, order, cur = {}, [], None
    for ln in lines:
        m = re.match(r"^### (" + QID + r") ", ln)
        if m:
            cur = m.group(1)
            order.append(cur)
            out[cur] = [set(), "", ""]
        elif ln.startswith("## "):
            cur = None
        if cur and ln.startswith("모범규준 조:"):
            out[cur][0] = art_numbers(ln[len("모범규준 조:"):])
        if cur and ln.startswith("[") and " · 쪽 p." in ln and not out[cur][1]:
            cm = CITE_RE.match(ln)
            if cm:
                k = key_for_path(cm.group("path"))
                out[cur][1] = SHORT_DOC.get(k, k)
                out[cur][2] = cm.group("pages")
    return out, order


def rebuild_index(co, s, titles):
    lines = s.split("\n")
    qi, order = quote_index(lines)
    sec, cur_arts = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec = ln
        if sec and sec.startswith("## 0.") and re.match(r"^\| \d", ln):
            cells = ln.split("|")
            lab = cells[1].strip()
            arts = art_numbers(lab)
            key = lab.replace("조", "")
            new_lab = "·".join(f"{n}조({titles[n]})" for n in sorted(arts))
            have = re.findall(r"\((" + QID + r")\)", cells[4])
            want = [q for q in order if qi[q][0] & arts]
            add = [q for q in want if q not in have]
            c4 = cells[4].rstrip()
            if add:
                c4 = c4 + "".join(f"; {qi[q][1]} {qi[q][2]} ({q})" for q in add)
            c5 = cells[5].rstrip()
            za = ZERO_ADD[co].get(key)
            if za:
                c5 = c5 + " " + za
            cells[1] = f" {new_lab} "
            cells[4] = c4 + " "
            cells[5] = c5 + " "
            lines[i] = "|".join(cells)
            FIXLOG[co].append((f"0장 {lab} 행", f"{new_lab} 행" + (f" + 인용 {', '.join(add)}" if add else "") + (" + 검증 보강 문구" if za else ""),
                               "조 제목 붙임; 「모범규준 조:」 줄에 그 조가 있는 인용을 행에 모두 적음" + ("; 반박 검색에서 찾은 글 요지" if za else "")))
        if sec and sec.startswith("## 3."):
            for k, (old, new) in S3_HEAD.items():
                if ln.startswith(old):
                    lines[i] = ln.replace(old, new, 1)
                    cur_arts = (k, art_numbers(new[4:].split(" — ")[0]))
            if cur_arts and ln.startswith(f"- {CO[co]}:"):
                have = re.findall(r"(" + QID + r")\(", ln)
                want = [q for q in order if qi[q][0] & cur_arts[1]]
                add = [q for q in want if q not in have]
                if add:
                    lines[i] = ln.rstrip() + "".join(f", {q}({qi[q][1]} {qi[q][2]})" for q in add)
            if cur_arts and ln.startswith("- 찾은 범위:"):
                k = cur_arts[0]
                rk = REF_KEY[k]
                lines[i] = ln + "\n" + f"- 검증 반박(2026-10-07): 넓힌 검색어로 같은 출처(risk8 세 문서·대조판)와 risk9 같은 회사 다른 기간 정기보고서 전 쪽을 다시 검색 — 검색어·걸린 줄 수는 맨 끝 검증 기록 표의 {rk}조 행. 결과: {S3_ADD[co][k]}"
    s = "\n".join(lines)
    FIXLOG[co].append(("3장 머리 「### N조 제목 — …」", "「### N조(조 제목) — …」", "조 제목 표기 통일"))
    FIXLOG[co].append(("3장 조마다 찾은 범위 줄까지", "+ 「검증 반박(2026-10-07)」 줄", "「추출 범위에 없음」 반박 시도 결과"))
    return s


def rebuild_variants(co, s):
    lines, blocks = parse_md(s)
    start = next(i for i, ln in enumerate(lines) if ln.startswith("## 4. "))
    hdr = next(i for i in range(start, len(lines)) if lines[i].startswith("| 인용 |"))
    end = hdr + 2
    while end < len(lines) and lines[end].startswith("| "):
        end += 1
    old_rows = {ln.split("|")[1].strip() + "|" + ln.split("|")[2].strip(): ln for ln in lines[hdr + 2:end]}
    rows = []

    def qkey(q):
        m = re.match(r"[HW]-(\d+)(b?)", q)
        return (int(m.group(1)), m.group(2))

    for b in sorted([b for b in blocks if b["qid"]], key=lambda x: qkey(x["qid"])):
        cm = CITE_RE.match(b["cite"] or "")
        key = key_for_path(cm.group("path")) if cm else None
        for vid, res, miss in variant_result(key, b["body"]):
            row = f"| {b['qid']} | `{DOCS[vid]['file'][:-4]}` | {res} | {miss or '-'} |"
            k = f"{b['qid']}|`{DOCS[vid]['file'][:-4]}`"
            if k in old_rows and old_rows[k] != row:
                FIXLOG[co].append((old_rows[k], row, "대조판 결과 다시 셈 — DART 쪽 머리말 줄까지 빼면 공백 무시로 같음"))
            elif k not in old_rows:
                FIXLOG[co].append(("(행 없음)", row, "새 인용·늘린 인용의 대조판 행"))
            rows.append(row)
    lines[hdr + 2:end] = rows
    # 표 아래 note 에 방법 한 줄 더함
    j = hdr + 2 + len(rows)
    while j < len(lines) and not lines[j].startswith("note:"):
        j += 1
    lines.insert(j + 1, "note: (검증 2026-10-07) 표의 결과는 스크립트로 다시 셈 — 쪽 표지 줄을 뺀 공백 무시 대조로 안 맞으면 DART 쪽 머리말 줄(전자공시시스템 dart.fss.or.kr Page …)도 빼고 한 번 더 대조(같음(공백·DART 쪽 머리말 줄 무시)). 다른 기간 판(risk9) 인용은 같은 기간 정정판과 대조.")
    return "\n".join(lines)


def header_add(co):
    nq = len(NEW_QUOTES[co])
    r9 = sorted({q["key"] for q in NEW_QUOTES[co] if q["key"].startswith("R9_")})
    r9txt = "; ".join(f"{DOCS[k]['name']} — 접수번호 {DOCS[k]['rcp']} · 텍스트 `{DOCS[k]['path']}` (텍스트 sha256 {'일치' if DOCS[k]['txt_sha_ok'] else '불일치'}, risk9 텍스트목록.csv 대조)" for k in r9)
    out = [f"- 검증(2026-10-07): `scripts/dart/verify13_g_hana_woori.py` 로 인용 전부를 원문 텍스트 줄과 대조하고 보정함(내용·전후는 맨 끝 검증 기록 절). 검증 때 반박 검색으로 찾은 인용 {nq}개는 머리에 (검증 추가) 를 달아 더함.",
           f"- 검증 때 더한 자료(반박 검색에서 찾은 다른 기간 판): {r9txt}." if r9 else "",
           "- 모범규준 조 표기(검증 보정): 인용마다 모범규준 조 줄·0장 표·1-2 표 마지막 칸·3장 머리에 N조(조 제목) 꼴 — 조 제목은 `dart_out/risk13/모범규준_조목록.csv`(2016.8.1 판). 지시서 9-4 에 적힌 조(3·4·5·17·21·22·24·27·34·53·55)는 그대로, 그 밖의 조와 이 작업이 판단으로 붙인 조는 (판단) 표시."]
    return "\n".join(x for x in out if x) + "\n"


def section6(co):
    out = [REQ6, "", f"지시서(REQUEST13) 9-4 항목마다 이 파일({CO[co]})에서 받은 글(인용 번호) 또는 추출 범위에 없음 + 찾은 방법. (검증 2026-10-07 추가)", "",
           "| 지시서 항목 | 지시서 원문 | 결과(받은 글 / 추출 범위에 없음 / 해당 없음) | 찾은 방법·자리 |", "|---|---|---|---|"]
    req = dict(REQ_ITEMS)
    for lab, res, how in REQ6_ROWS[co]:
        out.append(f"| {lab} | {req[lab]} | {res} | {how} |")
    return "\n".join(out) + "\n"


def problem_cat(m):
    for keys, lab in ((("조 제목 없는 조 번호",), "모범규준 조 표기에 조 제목 없음"), (("제목 다름",), "조 제목이 조목록과 다름"),
                      (("「(판단)」 없음",), "지시서 밖 조에 (판단) 없음"),
                      (("없는 인용", "조:」 줄에", "인데 이 행에 없음"), "0장 표·3장 목록과 인용의 조 줄이 어긋남"),
                      (("「…」 조각",), "「…」 조각이 원본 글자와 다름"), (("4장",), "4장 대조판 결과가 다시 셈과 다름"),
                      (("글머리 목록",), "인용이 글머리 목록 중간에서 끊김"), (("지시서",), "6장 지시서 항목별 대조 없음"),
                      (("검증 기록",), "검증 기록 절 없음"), (("칸 없음",), "CSV 모범규준 조 칸 없음"),
                      (("문서 칸", "URL"), "CSV 문서·URL 칸")):
        if any(k in m for k in keys):
            return lab
    return "기타"


def verification_record(co, pre, post, detail, ref, probs):
    W = []
    a = W.append
    a(VREC)
    a("")
    a("- 스크립트: `scripts/dart/verify13_g_hana_woori.py` (인자 없이 = 대조, `refute` = 반박 검색, `fix` = 보정 — 검증 전 사본 `dart_out/raw/web13/verify13_g_hana_woori/pre/`(커밋 8c118c8)에서 다시 만듦). 대조 결과 `dart_out/risk13/verify13_g_hana_woori.txt`, 반박 검색 결과 전부 `dart_out/raw/web13/verify13_g_hana_woori/refute_hits.json`, 고친 곳 전부 `fix_log.json`.")
    a("- 웹 요청·API 키·OC 는 쓰지 않음(로컬 텍스트만). 공시 원본 PDF 는 산출 폴더에 두지 않음.")
    a("")
    a("### 대조한 인용")
    a("")
    srcp = [x for x in pre["probs"] if any(k in x[1] for k in ("인용이 원문과 다름", "출처 줄", "문서명 다름", "URL/접수번호 다름", "원본 수집일 다름", "쪽 표기 다름", "인용일 다름"))]
    a(f"- 검증 전 원문 인용(코드 블록) {pre['blocks']}개 — 출처 줄이 가리킨 텍스트 줄과 글자까지 같음(줄 끝 공백만 무시) {pre['exact']}개, 공백만 다름 {pre['same_ws']}개. "
      f"문서명·URL/접수번호·쪽·줄·원본 수집일·인용일을 메타(텍스트목록.csv·연차보고서_파일목록.csv·경영공시_2026_2Q.csv·경영공시 meta.json·_파일목록.json)와 대조한 문제 {len(srcp)}개" +
      (" — 고칠 인용 글자·출처 표기는 없었음." if not srcp and pre["exact"] == pre["blocks"] else "."))
    cats = {}
    for w, m in pre["probs"]:
        cats[problem_cat(m)] = cats.get(problem_cat(m), 0) + 1
    a(f"- 검증 전 사본을 같은 스크립트로 대조한 문제 {len(pre['probs'])}개 — " + "; ".join(f"{k} {v}" for k, v in sorted(cats.items(), key=lambda x: -x[1])) + ". 모두 아래 표대로 고침.")
    a(f"- 검증 후 원문 인용 {post['blocks']}개(검증 추가 {len(NEW_QUOTES[co])}개, 범위를 늘린 인용 1개 포함) — 글자까지 같음 {post['exact']}개, 공백만 다름 {post['same_ws']}개.")
    a(f"- note·표 줄의 「…」 조각 {post['frags']}개를 원본(같은 회사 텍스트·대조판·risk9 판, 모범규준 원문, 지시서, 조목록)과 공백 무시로 대조 — 원본 글자와 달라 고친 것은 아래 표, 원본 글이 아닌 md 칸·행 이름이라 넘긴 것 {len(post['frags_allowed'])}개(" +
      "; ".join(f"{k} — {v}" for k, v in FRAG_ALLOW.items() if k in post["frags_allowed"]) + ").")
    a(f"- 4장 대조판 행 {post['variant_rows']}개·5장 검색 기록 행 {post['search_rows']}개를 다시 계산, 조문 목차 CSV {post['toc_rows']}행을 그 쪽 텍스트와 대조, 1-1 첨부 표 {post['attach_rows']}행의 첫 쪽 확인.")
    a("")
    a("### 고친 곳(전 → 후)")
    a("")
    a("| # | 전 | 후 | 사유 |")
    a("|---|---|---|---|")
    for i, (o, n, why) in enumerate(FIXLOG[co], 1):
        o1 = o.replace("|", "¦").replace("\n", " ")
        n1 = n.replace("|", "¦").replace("\n", " ")
        if len(o1) > 220:
            o1 = o1[:220] + " …"
        if len(n1) > 260:
            n1 = n1[:260] + " …"
        a(f"| {i} | {o1} | {n1} | {why.replace('|', '¦')} |")
    a("")
    a("### 채운 항목")
    a("")
    a(f"- {REQ6[3:]} 표를 새로 만듦(지시서 9-4 의 13개 항목마다 받은 글 인용 번호 또는 추출 범위에 없음 + 찾은 방법).")
    a("- 검증 추가 인용: " + "; ".join(f"{q['qid']}({SHORT_DOC.get(q['key'], q['key'])} {cite_line(q['key'], q['l1'], q['l2'])[1]}, {q['tags'].split(';')[0]})" for q in NEW_QUOTES[co]) + ".")
    a("- 조문 목차 CSV 에 닿는모범규준조(판단) 칸을 더하고(md 1-2 표 마지막 칸과 같은 글), 검증 때 찾은 규정 이름·조문 행을 더함(위 표).")
    a("- 0장 표·3장 목록: 「모범규준 조:」 줄에 그 조가 있는 인용을 모두 적음(양방향 대조).")
    a("")
    a("### 「추출 범위에 없음」 반박 시도")
    a("")
    a("방법: 조마다 수집 때(5장)보다 넓힌 정규식(낱말 변형·띄어쓰기·영문·동의어)으로 같은 출처를 줄 단위(앞뒤 한 줄을 이은 창 포함)로 다시 찾음. 찾은 범위 — risk8 세 문서(연차·사업·경영공시) 전 쪽과 대조판(추가공시·정정), risk9 같은 회사 다른 기간 정기보고서 전 쪽(" +
      ", ".join(f"{DOCS[k]['name']} {DOCS[k]['rcp']}" for k in DOCS if k.startswith("R9_") and DOCS[k]["co"] == co) + "). 걸린 줄에서 이미 인용한 줄·대조판·다른 기간 판의 중복 줄을 뺀 것이 새 줄. 새 줄은 조의 핵심 낱말로 한 번 더 걸러 읽음(회계 주석의 손상징후·해외사업장 환산, 사외이사 후보 평판조회, 기후위기 대응처럼 뜻이 다른 줄은 뺌) — 걸린 줄 전부(줄·쪽·글)는 refute_hits.json.")
    a("")
    a("| 조 | 넓힌 검색어(요약) | 걸린 줄(risk8) | 걸린 줄(risk9) | 새 줄 | 결과 | 넣은 인용 |")
    a("|---|---|---|---|---|---|---|")
    res_map = {"3": "3", "4·5": "4·5", "17": "17", "21·22·24": "21", "27": "27", "34": "34", "53": "53", "55": "55"}
    for jo, rec in ref["조"].items():
        d8 = sum(v["n"] for k, v in rec["문서"].items() if DOCS.get(k, {}).get("co") == co and not k.startswith("R9_"))
        d9 = sum(v["n"] for k, v in rec["문서"].items() if DOCS.get(k, {}).get("co") == co and k.startswith("R9_"))
        nn = sum(v["n_new"] for k, v in rec["문서"].items() if DOCS.get(k, {}).get("co") == co)
        if jo == "규정전문":
            result = ("실패 — 그룹리스크관리규정의 조문이나 그 조 번호 인용은 걸리지 않음. 걸린 조 번호 인용은 이미 받은 그룹리스크관리협의회규정 제5조·그룹경영협의회규정 제1·2조뿐; 새 규정 이름: 자회사등경영관리규정(W-36), 자체정상화위원회규정(W-38, 2023.12 판)"
                      if co == "W" else
                      "실패 — 그룹리스크관리규정·그룹리스크관리시행세칙·트레이딩정책규정의 조문이나 그 조 번호 인용은 걸리지 않음. 걸린 조 번호 인용은 이미 받은 리스크관리집행위원회 규정 제6조의2(와 제2조)뿐; 새 규정 이름 없음")
            qs = "W-36·W-38" if co == "W" else "-"
            lab = "규정 전문"
        else:
            result = S3_ADD[co][res_map[jo]]
            qs = "·".join(q["qid"] for q in NEW_QUOTES[co] if any(
                str(x) in [y.strip() for y in re.findall(r"(\d+)조", q["tags"])] for x in jo.split("·")))
            qs = qs or "-"
            lab = "·".join(f"{x}조" for x in jo.split("·"))
        a(f"| {lab} | {rec['label']} | {d8} | {d9} | {nn} | {result} | {qs} |")
    a("")
    a("검색어(정규식 — 표와 헷갈리지 않게 「|」를 「¦」로 적음; ctx/near 는 같은 창에 있어야 하는 말, 뺀말은 먼저 지운 말):")
    a("")
    for jo, rec in ref["조"].items():
        extra = []
        for kk, lab in (("ctx", "ctx"), ("ctx2", "ctx2"), ("near", "near"), ("뺀말", "뺀말")):
            if rec.get(kk):
                extra.append(f"{lab} `{rec[kk].replace('|', '¦')}`")
        a(f"- {jo if jo == '규정전문' else '·'.join(x + '조' for x in jo.split('·'))}: `{rec['검색어'].replace('|', '¦')}`" + (" — " + ", ".join(extra) if extra else ""))
    a("")
    a("### 남은 문제")
    a("")
    a("- 대조 문제: @@NPROB@@(보정 뒤 `python3 scripts/dart/verify13_g_hana_woori.py` 대조 기준 — 결과 파일 `dart_out/risk13/verify13_g_hana_woori.txt`).")
    a("- 그룹리스크관리규정(그룹 위험관리기준) 전문·조문 목차는 세 문서에 첨부되지 않아 추출 범위에 없음 — 모범규준 3~58조와 조 번호를 맞대는 표(iM·메리츠 식)는 만들 수 없음. 회사 홈페이지 내규 게시판은 이번 범위 밖.")
    if co == "W":
        a("- 우리 FY2025 사업보고서 정정판은 risk8·risk9 어디에도 텍스트가 없어 대조하지 않음(risk9 텍스트목록.csv 의 우리금융지주 2025.12 판은 원본 20260313001235 하나).")
        a("- 검증 추가 인용 가운데 W-37·W-38 은 2023.12 사업보고서(다른 기간 판) — FY2025 내규 상태를 보여 주지 않음.")
    else:
        a("- 검증 추가 인용 가운데 H-38 은 2024.12 사업보고서(다른 기간 판) — FY2025 사업보고서에는 같은 문장이 없음.")
    a("- 경영공시는 2026년 상반기 판(2026.6말 기준)이라 FY2025 보고서보다 뒤 시점(머리 한계 ④).")
    return "\n".join(W) + "\n"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
