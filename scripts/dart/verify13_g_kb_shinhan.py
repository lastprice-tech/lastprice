# -*- coding: utf-8 -*-
"""13차 9-4 KB금융지주·신한금융지주 산출물 검증·보정.

    python3 scripts/dart/verify13_g_kb_shinhan.py          # 대조만 — 결과 dart_out/risk13/verify13_g_kb_shinhan.txt, 문제 0 이면 exit 0
    python3 scripts/dart/verify13_g_kb_shinhan.py refute   # 「추출 범위에 없음」 반박 시도(같은 출처, 더 넓은 검색어) —
                                                           #   결과 dart_out/raw/web13/verify13_g_kb_shinhan/refute_hits.json (요약만 출력)
    python3 scripts/dart/verify13_g_kb_shinhan.py fix      # 보정(멱등: 검증 전 사본 pre/ 에서 다시 만듦) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-4_KB금융지주.md, 9-4_신한금융지주.md,
      dart_out/risk13/9-4_KB금융지주_조문목차.csv, 9-4_신한금융지주_조문목차.csv.
검증 전 사본: dart_out/raw/web13/verify13_g_kb_shinhan/pre/ (커밋 8c118c8 의 파일 그대로). 원 생성기 scripts/dart/web13_g_kb_shinhan.py 는
      고치지도 import 하지도 않는다(다시 돌리면 보정이 지워지므로 돌리지 말 것).
원문(읽기만): dart_out/text/risk8/ (연차보고서·추가공시, 사업보고서 원본·정정, 경영공시 — 쪽 표지 「=== p.N ===」),
      dart_out/text/risk9/<접수번호>.txt (DART 정기보고서 — 같은 회사 다른 기간 판, 반박 검색에만),
      메타 dart_out/risk8/텍스트목록.csv·handoff/연차보고서_파일목록.csv·dart_out/risk8/경영공시_2026_2Q.csv·
      dart_out/raw/risk8/경영공시/<회사>/meta.json·dart_out/doc/<접수번호>/_파일목록.json·dart_out/risk9/텍스트목록.csv,
      모범규준 hwp2md 변환본 dart_out/raw/web13/mobeom/fss/*.hwp.md, 모범규준 조 목록 dart_out/risk13/모범규준_조목록.csv.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만). dart_out/raw/ 는 git 밖이라, 검증 전 사본이 없으면 fix 가 `git show 8c118c8:<경로>` 로 만들고,
지시서 사본이 없으면 이 파일의 REQ_FALLBACK(지시서 공통 규칙·9-4·끝에 낼 것 원문)을 쓴다. refute_hits.json 이 없으면 fix 가 refute 를 먼저 돌린다.

대조(인자 없이):
  1. md 의 원문 인용(코드 블록·> 블록) 전부를 바로 앞 출처 줄 [문서 · 접수번호/URL · 쪽 · 줄 · 파일 · 원본 수집 · 인용] 이 가리킨 텍스트
     줄과 대조 — 글자 그대로(줄 끝 공백만 무시)인지, 아니면 공백만 무시하고 같은지. 출처 줄의 쪽·줄 번호가 실제 자리와 같은지,
     문서명·접수번호/URL·원본 수집일이 메타와 같은지, 인용이 글머리 목록 중간에서 끊겼는지(다음 원본 줄이 같은 글머리로 시작).
  2. 4장 「추가공시·정정판 문구 대조」 표의 결과를 다시 계산해 같은지.
  3. 5장 검색 기록 표의 걸린 수·걸린 쪽을 다시 계산해 같은지.
  4. 조문 목차 CSV·1-2 표 — 전문 옮긴 규정의 조 번호·제목이 그 쪽 텍스트에 있는지, 인용만 있는 행의 규정명이 그 쪽에 있는지,
     CSV 와 md 1-2 표가 같은지, 문서·URL 이 메타와 같은지.
  5. note·표 줄의 「…」 조각이 원본(회사 텍스트·모범규준 변환본·지시서)에 있는지(공백 무시) — 못 찾은 것은 목록(허용 목록 밖이면 문제).
  6. 「모범규준 조:」 줄과 0장 표의 조 번호마다 ‘N조(조 제목)’이 붙었는지, 제목이 모범규준_조목록.csv(2016.8.1 판)과 같은지,
     지시서에 없는 조 번호에 「(판단)」이 붙었는지.
  7. 지시서(REQUEST13) 9-4 항목마다 「6. 지시서 항목별 대조」 표에 받은 글(인용 번호) 또는 「추출 범위에 없음 + 찾은 방법」이 있는지,
     가리킨 인용 번호가 md 에 있는지.
  8. 「추출 범위에 없음」 줄마다 찾은 방법(검색어·범위)이 있는지(같은 줄·같은 절), 반박 검색 기록이 검증 기록에 있는지.
  9. 인증값(DART 키·법제처 OC) 문자열 없음, 산출 폴더에 PDF 없음, 맨 끝 「## 검증 기록(2026-10-07)」 절이 하나.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

TODAY = "2026-10-07"
# 13차 정합성 보정(scripts/dart/fix13_B.py, R5 날짜 라벨) 뒤의 꼴도 받음 — 절 제목 「## 검증 기록(2026-10-08 KST)」, 검증 때 더한 인용의 인용일 2026-10-08.
FIX13_VREC = "## 검증 기록(2026-10-08 KST)"
FIX13_QD = "2026-10-08"
TXT8 = os.path.join("dart_out", "text", "risk8")
TXT9 = os.path.join("dart_out", "text", "risk9")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
VD = os.path.join("dart_out", "raw", "web13", "verify13_g_kb_shinhan")
PRE = os.path.join(VD, "pre")
OUT_TXT = os.path.join(WORK, "verify13_g_kb_shinhan.txt")
REFUTE_JSON = os.path.join(VD, "refute_hits.json")
CHECK_JSON = os.path.join(VD, "check_detail.json")
JO_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MOBEOM_HWP = [os.path.join("dart_out", "raw", "web13", "mobeom", "fss", f) for f in
              ("모범규준_20160801판_붙임2_통합위험관리_개정후전문.hwp.md", "예고29_통합리스크관리_모범규준(게시)F_.hwp.md")]
MOBEOM_MD = os.path.join(OUTD, "9-4_모범규준_원문.md")
REQ = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
REQ_COPY = os.path.join(VD, "REQUEST13_9-4.txt")   # 지시서 9-4 부분 사본(스크래치가 지워져도 대조되게)
CO = {"K": "KB금융지주", "S": "신한금융지주"}
MD = {k: os.path.join(OUTD, f"9-4_{v}.md") for k, v in CO.items()}
TOC = {k: os.path.join(WORK, f"9-4_{v}_조문목차.csv") for k, v in CO.items()}
PAGE_RE = re.compile(r"^=== p\.(\d+) ===\s*$")
SHORT = {"연차": "AR", "사업": "BR", "경영공시": "MD"}
# 지시서(REQUEST13 9-4)에 적힌 모범규준 조 번호 — 이 밖의 번호는 「(판단)」
REQ_ARTS = {3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55}


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
    "K_AR": dict(co="K", kind="연차", file="연차보고서__KB금융지주_지배구조연차보고서_2026.txt", pdf="KB금융지주_지배구조연차보고서_2026.pdf"),
    "K_AR2": dict(co="K", kind="연차(추가공시)", file="연차보고서__KB금융지주_지배구조연차보고서_2026_추가공시.txt",
                  pdf="KB금융지주_지배구조연차보고서_2026_추가공시.pdf"),
    "K_BR": dict(co="K", kind="사업", file="사업보고서__KB금융지주__20260313001191.txt", rcp="20260313001191"),
    "K_BR_0835": dict(co="K", kind="사업(정정)", file="사업보고서__KB금융지주__20260324000835.txt", rcp="20260324000835"),
    "K_BR_0667": dict(co="K", kind="사업(정정)", file="사업보고서__KB금융지주__20260619000667.txt", rcp="20260619000667"),
    "K_MD": dict(co="K", kind="경영공시", file="경영공시__KB금융지주.txt"),
    "S_AR": dict(co="S", kind="연차", file="연차보고서__신한금융지주_지배구조연차보고서_2026.txt", pdf="신한금융지주_지배구조연차보고서_2026.pdf"),
    "S_AR2": dict(co="S", kind="연차(추가공시)", file="연차보고서__신한금융지주_지배구조연차보고서_2026_추가공시.txt",
                  pdf="신한금융지주_지배구조연차보고서_2026_추가공시.pdf"),
    "S_BR": dict(co="S", kind="사업", file="사업보고서__신한금융지주__20260318000826.txt", rcp="20260318000826"),
    "S_MD": dict(co="S", kind="경영공시", file="경영공시__신한금융지주.txt"),
}
for _k, _d in DOCS.items():
    _d["path"] = os.path.join(TXT8, _d["file"])
VARIANTS = {"K_AR": ["K_AR2"], "K_BR": ["K_BR_0835", "K_BR_0667"], "S_AR": ["S_AR2"],
            # risk9 다른 기간 판(검증 때 새 인용의 출처) — 원본 → 정정판
            "R9_20240314001585": ["R9_20240326000894"], "R9_20250314001704": ["R9_20250526000370", "R9_20260324000822"]}
MAIN = {"K": ["K_AR", "K_BR", "K_MD"], "S": ["S_AR", "S_BR", "S_MD"]}
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
            d["name"] = a["제목"]
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
            d["name"] = f"{co} 「{m['제목']}」(경영공시, 게시 {m['게시일']})"
            d["loc"] = mj.get("실제url") or m["url"]
            d["locs_ok"] = {m["url"], mj.get("url", ""), mj.get("실제url", "")}
            d["fetched"] = m["fetched_at"]
            d["src_sha_list"] = m["sha256"]
    # risk9: 같은 회사 정기보고서(다른 기간 판) — 반박 검색에만
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


BULLET_RE = re.compile(r"^\s*(ㆍ|·|-|•|①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩|\d{1,2}\.\s|[가-하]\.\s)")


def bullet_of(s):
    m = BULLET_RE.match(s)
    if not m:
        return None
    b = m.group(1).strip()
    if re.fullmatch(r"\d{1,2}\.", b):
        return "번호"
    if re.fullmatch(r"[가-하]\.", b):
        return "가나다"
    if b in "①②③④⑤⑥⑦⑧⑨⑩":
        return "원문자"
    return b


def check_quote(co, b, probs, detail):
    """인용 한 개 대조. 문제는 probs 에 (위치, 내용)."""
    load_meta()
    where = f"{CO[co]} md {b['body_start']}줄 {b['qid']}"
    rec = dict(co=co, qid=b["qid"], md_line=b["body_start"], kind=b["kind"])
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
    # 문서명·위치·수집일
    if m.group("doc") != d["name"]:
        probs.append((where, f"문서명 다름: 「{m.group('doc')}」 / 메타 「{d['name']}」"))
    if m.group("loc") not in d["locs_ok"]:
        probs.append((where, f"URL/접수번호 다름: {m.group('loc')} / 메타 {sorted(d['locs_ok'])}"))
    if m.group("fetched") != d["fetched"][:10]:
        probs.append((where, f"원본 수집일 다름: {m.group('fetched')} / 메타 {d['fetched']}"))
    if m.group("qd") not in (TODAY, FIX13_QD):
        probs.append((where, f"인용일 다름: {m.group('qd')}"))
    t = T(key)
    l1, l2 = int(m.group("l1")), int(m.group("l2"))
    src = t.lines[l1 - 1:l2]
    body = list(b["body"])
    # 끝 빈 줄
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
        # 다른 자리에 있는지
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
    # 쪽
    p1, p2 = t.page[l1 - 1], t.page[l2 - 1]
    lab = f"p.{p1}" if p1 == p2 else f"p.{p1}–p.{p2}"
    rec["real_pages"] = lab
    if lab != m.group("pages"):
        probs.append((where, f"쪽 표기 다름: {m.group('pages')} / 실제 {lab}"))
    # 글머리 목록 중간에서 끊겼는지
    nxt = l2
    while nxt < len(t.lines) and not t.lines[nxt].strip():
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
            out.append((vid, "줄 단위로는 모두 있음(배치·이어짐이 다름)", ""))
        else:
            out.append((vid, f"다름 — 공백을 빼고도 없는 줄 {len(miss)}개", " ‖ ".join(miss[:3])))
    return out


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
TOC_COLS = ["회사", "규정명", "조번호", "조제목", "문서", "접수번호또는URL", "쪽", "전문여부"]


def check_toc(co, md_lines, probs):
    load_meta()
    rows = read_csv(TOC[co])
    ar = DOCS[f"{co}_AR"]
    t = T(f"{co}_AR")
    pt = t.pages_text()
    for r in rows:
        w = f"{CO[co]} CSV {r['규정명']} {r['조번호']}"
        if r["접수번호또는URL"] not in ar["locs_ok"]:
            probs.append((w, f"URL 다름: {r['접수번호또는URL']}"))
        pg = []
        for a, b in re.findall(r"p\.(\d+)(?:–p\.(\d+))?", r["쪽"]):
            pg.extend(range(int(a), int(b or a) + 1))
        txt = "".join(pt.get(p, "") for p in pg)
        ntxt = nows(txt)
        m = re.fullmatch(r"제(\d+)조", r["조번호"])
        if r["전문여부"].startswith("Y") and m:
            pat = re.compile(r"제\s*" + m.group(1) + r"\s*조\s*\(\s*" + r"\s*".join(map(re.escape, nows(r["조제목"]))) + r"\s*\)")
            if not pat.search(txt):
                probs.append((w, f"조 번호·제목이 {r['쪽']} 에 없음"))
        elif r["조번호"] == "부칙":
            if "부칙" not in ntxt:
                probs.append((w, f"부칙이 {r['쪽']} 에 없음"))
        else:
            if nows(r["규정명"]) not in ntxt:
                probs.append((w, f"규정명이 {r['쪽']} 에 없음"))
            if m and not re.search(r"제\s*" + m.group(1) + r"\s*조", txt):
                probs.append((w, f"조 번호가 {r['쪽']} 에 없음"))
    # md 1-2 표와 같은지
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
    csv_cells = [[r["규정명"], r["조번호"], r["조제목"], r["쪽"], r["전문여부"]] for r in rows]
    if tab != csv_cells:
        diff = [x for x in difflib.unified_diff([" | ".join(x) for x in csv_cells], [" | ".join(x) for x in tab], lineterm="", n=0)][:6]
        probs.append((f"{CO[co]} md 1-2 표", "CSV 와 다름: " + " ‖ ".join(diff)[:500]))
    return len(rows)


# ───────────────────────────── 「…」 조각 ─────────────────────────────
FRAG_RE = re.compile(r"「([^「」]{2,}?)」")


def corpus_for(co):
    load_meta()
    parts = []
    for k in MAIN[co] + [v for x in MAIN[co] for v in VARIANTS.get(x, [])] + \
            [x for x in DOCS if x.startswith("R9_") and DOCS[x]["co"] == co]:
        parts.append(T(k).flat("raw")[0])
    for p in MOBEOM_HWP:
        parts.append(nows(open(p, encoding="utf-8").read()))
    parts.append(nows(req_text()))
    return parts


def req_text():
    if os.path.exists(REQ):
        full = open(REQ, encoding="utf-8").read()
        # 대조에 쓰는 부분만(공통 규칙·9-4·끝에 낼 것) 사본으로 둔다
        keep, on = [], False
        for ln in full.split("\n"):
            if ln.startswith("## "):
                on = ln.startswith("## 공통 규칙") or ln.startswith("## 9-4") or ln.startswith("## 끝에 낼 것")
            if on:
                keep.append(ln)
        txt = "\n".join(keep) + "\n"
        os.makedirs(VD, exist_ok=True)
        if not os.path.exists(REQ_COPY) or open(REQ_COPY, encoding="utf-8").read() != txt:
            open(REQ_COPY, "w", encoding="utf-8").write(txt)
        return txt
    if os.path.exists(REQ_COPY):
        return open(REQ_COPY, encoding="utf-8").read()
    return REQ_FALLBACK


# 지시서 사본(공통 규칙·9-4·끝에 낼 것 — REQUEST13 원문 그대로). dart_out/raw/ 는 git 에 올라가지 않으므로 스크래치·사본이 모두 없을 때 쓴다.
REQ_FALLBACK = """## 공통 규칙
- DART_API_KEY와 법제처 OC 값은 환경변수로만 쓰고 출력, 로그, 산출물 파일 어디에도 적지 않음
- 원문은 글자 그대로 옮김. 요약하거나 고쳐 쓰지 않음. 표가 깨지면 깨진 자리를 표시
- 찾지 못한 것은 "추출 범위에 없음"으로 적고 어디를 어떻게 찾았는지 남김. "없음"으로 단정하지 않음
- 산출물: 13차_산출물/ 아래 작업 번호별 md, 끝에 00_목록.md(파일, 출처, 수집일, 한계)
- 공시 원본 PDF는 배포하지 않고 해당 쪽의 글만 옮김(문서명, 접수번호, 쪽 표기)

## 9-4 타사 그룹리스크관리규정(모범규준 조항과 맞대기)
대상: 메리츠, 한국투자, KB, 신한, 하나, 우리, iM, NH의 지배구조 및 보수체계 연차보고서 FY2025 첨부 규정과 사업보고서
1. 그룹리스크관리규정(이름이 다르면 대응 규정)의 조문 목차 전체(조 번호와 제목). 전문이 있으면 전문
   - iM 그룹 리스크관리규정은 28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음.
     전체 조문 번호가 모범규준과 얼마나 맞는지 표로
   - 메리츠 그룹리스크관리규정 9조 7항, 57조가 인용되어 있음. 같은 방식으로 대조
2. 아래 조항에 닿는 타사 서술(근거가 거의 비어 있는 곳)
   - 21조 신용위험, 22조 시장위험, 24조 금리위험: 지주 차원의 유형별 측정 방법과 연결 측정 여부
   - 27조 전략·평판위험: 관리 체제, 측정이나 평가 수단
   - 34조 해외위험: 해외진출·해외사업 리스크의 총괄, 사전 검토, 정기 점검·보고
   - 3조: 위험이 경미한 자회사를 적용에서 빼는 기준
   - 17조: 지주가 자회사에 의사를 전달하는 문서 형식(메리츠, 한국투자는 추출 범위에 없었음)
   - 55조 조기경보: 지표 목록과 발령 단계(메리츠, 한국투자)
   - 53조 위기대응조직: 구성과 전환 요건
3. 위험관리 철학·원칙(4조·5조)을 내규에 둔 회사와 문구

## 끝에 낼 것
- 작업별로 "받은 것 / 받지 못한 것 / 원문과 다른 것을 발견한 곳"을 한 표로
- 01 엑셀판 '주제1_모범규준기준'의 어느 조 행에 넣을 자료인지 조 번호를 붙임

"""


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


def check_frags(co, lines, blocks, allow, probs):
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
            if fr in allow:
                continue
            miss.append((i + 1, fr))
    for ln_no, fr in miss:
        probs.append((f"{CO[co]} md {ln_no}줄", f"「…」 조각을 원본에서 못 찾음: 「{fr[:100]}」"))
    return n, miss


# ───────────────────────────── 모범규준 조 표기 ─────────────────────────────
ART_TOKEN_RE = re.compile(r"(\d{1,2})조\((?!판단\))([^()]+)\)(\(판단\))?")


def check_art_lines(co, lines, probs):
    titles = jo_titles()
    n = 0
    for i, ln in enumerate(lines):
        targets = []
        if ln.startswith("모범규준 조:"):
            targets.append(ln[len("모범규준 조:"):])
        if ln.startswith("| ") and re.match(r"^\| \d", ln) and "| " + CO[co] + " |" in ln:   # 0장 표 첫 칸
            targets.append(ln.split("|")[1])
        for s in targets:
            n += 1
            # 제목 없는 「N조」·「N·M조」 가 남았는지
            bare = re.findall(r"(?<![\d(제])(\d{1,2}(?:·\d{1,2})*)조(?:\(판단\)|(?!\())", s)
            if bare:
                probs.append((f"{CO[co]} md {i + 1}줄", f"조 제목 없는 조 번호: {bare}"))
            for m in ART_TOKEN_RE.finditer(s):
                no, tt, pd = int(m.group(1)), m.group(2), m.group(3)
                if titles.get(no) != tt:
                    probs.append((f"{CO[co]} md {i + 1}줄", f"{no}조 제목 다름: 「{tt}」 / 조목록 「{titles.get(no)}」"))
                if no not in REQ_ARTS and not pd:
                    probs.append((f"{CO[co]} md {i + 1}줄", f"{no}조 는 지시서에 없는 조 — 「(판단)」 없음"))
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


def check_req(co, lines, blocks, probs):
    req = req_text()
    for lab, s in REQ_ITEMS:
        if s not in req:
            probs.append(("지시서", f"지시서 원문에 없는 문구(대조표 기준 문구 확인): {lab}"))
    ids = {b["qid"] for b in blocks if b["qid"]}
    heads = {re.match(r"^### (\S+) ", ln).group(1) for ln in lines if re.match(r"^### (\S+) ", ln)}
    sec = None
    rows = {}
    for i, ln in enumerate(lines):
        if ln.startswith("## ") or ln.startswith("### "):
            sec = ln       # 「### 6-1」 표는 대상 아님
        if sec and sec.startswith("## 6. 지시서 항목별 대조") and ln.startswith("| ") and not ln.startswith("| 지시서 항목") \
                and not ln.startswith("|---"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows[cells[0]] = (i + 1, cells)
    if not rows:
        probs.append((f"{CO[co]} md", "「## 6. 지시서 항목별 대조」 표 없음"))
        return 0
    for lab, s in REQ_ITEMS:
        if lab not in rows:
            probs.append((f"{CO[co]} md 6장", f"지시서 항목 행 없음: {lab}"))
            continue
        ln_no, cells = rows[lab]
        if s not in cells[1]:
            probs.append((f"{CO[co]} md {ln_no}줄", f"지시서 원문 칸이 지시서와 다름: {lab}"))
        joined = " ".join(cells[2:])
        if not ("받은 글" in joined or "추출 범위에 없음" in joined or "해당 없음" in joined or "있음" in joined):
            probs.append((f"{CO[co]} md {ln_no}줄", f"받은 글/추출 범위에 없음 표시 없음: {lab}"))
        if "추출 범위에 없음" in joined and "찾은 방법" not in joined and "검색" not in joined and "5장" not in joined:
            probs.append((f"{CO[co]} md {ln_no}줄", f"추출 범위에 없음인데 찾은 방법 없음: {lab}"))
        for q in re.findall(r"\b([KS]-\d+b?)\b", joined):
            if q not in ids and q not in heads:
                probs.append((f"{CO[co]} md {ln_no}줄", f"없는 인용 번호: {q}"))
    return len(rows)


def check_notfound(co, lines, probs):
    """「추출 범위에 없음」 줄마다 찾은 방법 — 같은 줄, 같은 인용 절(검색 기록 5장을 가리킴), 3장 「찾은 범위」 줄."""
    n = 0
    sec, sub = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sec, sub = ln, None
        if ln.startswith("### "):
            sub = ln
        if "추출 범위에 없음" not in ln or sec is None:    # 머리(한계 ③ — 낱말 뜻 풀이)는 대상 아님
            continue
        n += 1
        if sec and (sec.startswith("## 검증 기록") or sec.startswith("## 6. 지시서")):
            continue
        ok = any(w in ln for w in ("검색", "찾은 범위", "찾은 방법", "5장", "훑", "첨부"))
        if not ok:
            # 같은 3장 소절의 「찾은 범위」 줄, 또는 머리 한계 ③(세 문서 범위) + 5장
            blk = lines[i:i + 8]
            ok = any("찾은 범위" in x for x in blk) or (sec and (sec.startswith("## 0.") or sec.startswith("## 1.") or sec.startswith("## 2.")))
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
        m = re.match(r"^### ([KS]-\d+b?) ", ln)
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
            t0.append((i, art_numbers(cells[1]), re.findall(r"\(([KS]-\d+b?)\)", cells[4])))
        if sec and sec.startswith("## 3."):
            m = re.match(r"^### (\d+(?:·\d+)?)조 ", ln)
            if m:
                cur = {int(x) for x in m.group(1).split("·")}
            if cur and ln.startswith(f"- {CO[co]}:"):
                s3.append((i, cur, re.findall(r"([KS]-\d+b?)\(", ln)))
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
    """1-1 첨부 표: 첫 쪽에 첨부 이름이 있고 앞 쪽에는 그 첨부 머리가 없는지."""
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
        head = f"첨부{no}.{name}" if co == "K" else f"{no}.{name}"
        if head not in pt.get(pg, ""):
            probs.append((f"{CO[co]} md {i + 1}줄 1-1 표", f"첨부 {no} 머리 「{head}」 가 p.{pg} 에 없음"))
        elif co == "K" and head + "(소관부서" in pt.get(pg - 1, ""):   # p.236 같은 첨부 목차 쪽은 대상 아님
            probs.append((f"{CO[co]} md {i + 1}줄 1-1 표", f"첨부 {no} 머리가 p.{pg - 1} 에도 있음(첫 쪽이 아님)"))
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


# ───────────────────────────── 대조 실행 ─────────────────────────────
def run_check(write=True, md_override=None, quiet=False):
    load_meta()
    probs, detail, stats = [], [], {}
    out_lines = []
    allow = FRAG_ALLOW
    for co in ("K", "S"):
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
        # 4장
        vt_rows = 0
        for i, ln in enumerate(lines):
            m = re.match(r"^\| ([KS]-\d+b?) \| `([^`]+)` \| ([^|]+) \| ([^|]*) \|\s*$", ln)
            if not m:
                continue
            vt_rows += 1
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
        # 인용마다 대조판 행이 다 있는지
        for b in blocks:
            cm = CITE_RE.match(b["cite"] or "")
            key = key_for_path(cm.group("path")) if cm else None
            for vid in VARIANTS.get(key, []):
                pat = f"| {b['qid']} | `{DOCS[vid]['file'][:-4]}` |"
                if not any(ln.startswith(pat) for ln in lines):
                    probs.append((f"{CO[co]} 4장", f"대조판 행 없음: {b['qid']} × {DOCS[vid]['file'][:-4]}"))
        st["variant_rows"] = vt_rows
        st["search_rows"] = check_search(co, lines, probs)
        st["toc_rows"] = check_toc(co, lines, probs)
        nfr, miss = check_frags(co, lines, blocks, allow, probs)
        st["frags"] = nfr
        st["frags_allowed"] = [f for f in allow if any(f in ln for ln in lines)]
        st["art_lines"] = check_art_lines(co, lines, probs)
        st["index_rows"] = check_index(co, lines, probs)
        st["attach_rows"] = check_attach(co, lines, probs)
        st["req_rows"] = check_req(co, lines, blocks, probs)
        st["notfound_lines"] = check_notfound(co, lines, probs)
        # 검증 기록 절
        nrec = sum(1 for ln in lines if ln.startswith("## 검증 기록"))
        vrec = FIX13_VREC if FIX13_VREC in lines else f"## 검증 기록({TODAY})"
        if nrec != 1 or not any(ln == vrec for ln in lines):
            probs.append((f"{CO[co]} md", f"「{vrec}」 절 수 {nrec}"))
        else:
            last_h2 = [ln for ln in lines if ln.startswith("## ")][-1]
            if last_h2 != vrec:
                probs.append((f"{CO[co]} md", "검증 기록 절이 맨 끝이 아님"))
            rec_txt = "\n".join(lines[lines.index(vrec):])
            for jo in ("3조", "4·5조", "17조", "21조", "22조", "24조", "27조", "34조", "53조", "55조"):
                if jo not in rec_txt:
                    probs.append((f"{CO[co]} 검증 기록", f"반박 시도 기록에 {jo} 없음"))
        stats[co] = st
    nsec = check_secrets([MD["K"], MD["S"], TOC["K"], TOC["S"], os.path.abspath(__file__)] +
                         [x for x in (OUT_TXT, REFUTE_JSON, CHECK_JSON, REQ_COPY) if os.path.exists(x)], probs)
    # 텍스트 sha256
    for k in [x for c in MAIN.values() for x in c] + [v for x in VARIANTS.values() for v in x]:
        if not DOCS[k]["txt_sha_ok"]:
            probs.append((k, "텍스트 sha256 가 텍스트목록.csv 와 다름"))
    if write:
        W = out_lines.append
        W(f"# verify13_g_kb_shinhan — 대조 결과 ({TODAY} 표기; 실행 환경 날짜와 무관)")
        W("대상: " + ", ".join([MD["K"], MD["S"], TOC["K"], TOC["S"]]))
        W("원문: " + ", ".join(sorted({DOCS[k]['path'] for k in [x for c in MAIN.values() for x in c] + [v for x in VARIANTS.values() for v in x]})))
        W(f"인증값 대조용 값 수(환경변수·.env, 값은 적지 않음): {nsec}")
        for co in ("K", "S"):
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
                    W(f"  - {d['qid']} (md {d['md_line']}줄) {d.get('doc', '')} {d.get('cite_pages', '')} 줄 {d.get('l1', '')}–{d.get('l2', '')}: {d.get('result')}")
        W("")
        W(f"## 문제 {len(probs)}개")
        for w, s in probs:
            W(f"- {w}: {s}")
        os.makedirs(WORK, exist_ok=True)
        open(OUT_TXT, "w", encoding="utf-8").write("\n".join(out_lines) + "\n")
        os.makedirs(VD, exist_ok=True)
        json.dump(dict(stats=stats, detail=detail, problems=probs), open(CHECK_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not quiet:
        print(f"인용 블록 KB {stats['K']['blocks']}·신한 {stats['S']['blocks']} — 문제 {len(probs)}개 → {OUT_TXT}")
        for w, s in probs[:40]:
            print(f"  - {w}: {s[:220]}")
        if len(probs) > 40:
            print(f"  … (+{len(probs) - 40})")
    return probs, detail, stats


# 원본 글이 아닌 「…」 표기(조각 대조에서 넘김) — 사유는 검증 기록에 적음
FRAG_ALLOW = {
    "연결기준 측정 / 단순 합산": "찾는 대상을 풀어 쓴 말(지시서 「연결 측정 여부」) — 원문 인용 아님(수집 에이전트 0장·3장 요지)",
    "근거조항": "원문 「근기조항」의 바른 꼴을 짐작한 말(K-02 note) — 원문 인용 아님",
    "N 2025년 지배구조 및 보수체계 연차보고서": "쪽 머리글의 꼴(N=첨부 안 쪽 번호)을 적은 말(K-14 note) — 원문 인용 아님",
    "=== p.N ===": "텍스트 쪽 표지의 꼴(머리 자료 줄) — 원문 인용 아님",
    "(판단)": "판단 표시 규칙(머리 방법·조 표기 줄) — 원문 인용 아님",
    "모범규준 조:": "이 파일의 인용 머리 줄 이름 — 원문 인용 아님",
    "4·5조": "5장 검색 기록 표의 행 이름(3장 「찾은 범위」 줄) — 원문 인용 아님",
}
# 글머리 목록 중간에서 끊겨도 되는 인용(사유)
CUT_LIST_OK = {}


# ───────────────────────────── 반박 검색(refute) ─────────────────────────────
# 조마다 원래 검색어(수집 에이전트 5장)보다 넓힌 정규식(낱말 변형·띄어쓰기·영문·동의어). 줄 단위 + 앞뒤 1줄을 이어 붙인 창에서 찾고,
# ctx 가 있으면 같은 창에 ctx 낱말이 있을 때만 남긴다. excl 은 먼저 지우는 말(예: 「비상임」).
REFUTE = {
    "3": dict(pat=r"경미|미미|중요(성|도)\s*(이|가)?\s*(낮|작)|중요하지\s*않|소규모|규모가\s*작|비중이\s*(작|낮)|"
                  r"적용\s*(을\s*)?(배제|제외|예외)|적용하지\s*(아니|않)|적용\s*대상|(측정|관리|한도|모니터링|산출|통제)\s*대상\s*(에서|으로|은|이|자회사|계열사)|"
                  r"대상\s*(자회사|계열사|종속기업)|제외(한다|하며|하고|되며|되어|됨|할\s*수)|[Mm]ateriality|[Ii]mmaterial|비중요",
              ctx=r"리스크|위험", ctx2=r"자회사|계열사|종속|그룹사", label="경미·소규모·중요성·적용 배제/제외/예외·측정/관리 대상"),
    "4·5": dict(pat=r"철학|원칙|기본\s*방침|기본\s*정책|리스크\s*문화|위험\s*문화|[Rr]isk\s*[Cc]ulture|최상위|가치\s*규범|"
                    r"위험\s*성향|리스크\s*성향|[Rr]isk\s*[Aa]ppetite|RAF\b|선언문|리스크\s*관리\s*정책|위험\s*관리\s*정책|정책\s*규정",
                ctx=r"리스크|위험", label="철학·원칙·기본방침·리스크 문화·위험성향·리스크관리정책·정책규정"),
    "17": dict(pat=r"의사\s*(전달|소통)|정보\s*전달|공문|공식\s*문서|서면|문서\s*(로|화|를|에)|전자\s*(문서|결재)|통보|통지|시달|하달|"
                   r"지시|요청|요구|권고|가이드\s*라인|송부|회신|협조\s*(요청|문)|업무\s*연락|커뮤니케이션",
               ctx=r"리스크|위험|경영관리|내부통제", near=r"자회사|계열사|그룹사|종속", label="의사전달·공문·서면·문서·통보·지시·요청·권고·가이드라인"),
    "21·22·24": dict(pat=r"(그룹|연결|통합|지주).{0,25}(신용|시장|금리|이자율).{0,25}(측정|산출|합산|VaR|내부\s*자본|위험\s*자본|리스크\s*량|위험\s*량|한도)|"
                          r"(신용|시장|금리|이자율).{0,25}(그룹|연결|통합).{0,25}(측정|산출|합산|VaR|내부\s*자본|위험\s*자본|리스크\s*량|위험\s*량)|"
                          r"단순\s*(합|합산)|합산|[Gg]roup[- ]?wide|[Cc]onsolidat|분산\s*효과|상관\s*관계|통합\s*(VaR|내부\s*자본|위험\s*자본|리스크\s*량)",
                     ctx=r"신용|시장|금리|이자율|리스크|위험", label="그룹·연결·통합 + 신용/시장/금리 + 측정·산출·합산, 단순합, 분산효과"),
    "27": dict(pat=r"평판|명성|이미지\s*(리스크|위험|훼손|실추|제고)|[Rr]eputation|전략\s*(리스크|위험)|[Ss]trateg(y|ic)\s*[Rr]isk|"
                   r"사업\s*(리스크|위험)|[Bb]usiness\s*[Rr]isk|비재무\s*(리스크|위험)|비계량\s*(리스크|위험)|[Ee]merging\s*[Rr]isk|신규\s*리스크|잠재\s*리스크|"
                   r"[Tt]op\s*[Rr]isk|중요\s*리스크|기후\s*(리스크|위험)|ESG\s*리스크|여론|언론\s*보도|민원",
               ctx=None, excl=r"평판\s*조회|평판조회|평판 조회", label="평판·명성·이미지·전략/사업/비재무/잠재/신규/중요 리스크·기후·ESG·여론·언론"),
    "34": dict(pat=r"해외|글로벌|국외|국가\s*(별|위험|리스크|신용|한도|익스포)|국별|[Cc]ountry|현지\s*(법인|금융|규제|당국)|외국|역외|"
                   r"[Cc]ross[- ]?[Bb]order|신흥국|[Gg]lobal|[Oo]verseas|진출",
               ctx=r"리스크|위험|한도|점검|검토|보고|모니터링|심의", label="해외·글로벌·국외·국가·국별·현지·외국·역외·신흥국·Global·Overseas·진출"),
    "53": dict(pat=r"위기|비상|[Cc]ontingency|컨틴전시|대응\s*(조직|체계|체제|반|위원회)|대책\s*(반|위원회|본부|조직)|상황\s*반|태스크|TF\b|"
                   r"[Cc]risis|자체\s*정상화|[Rr]ecovery|정리\s*계획|[Rr]esolution",
               ctx=None, excl=r"비상임|비상장|비상근|비상무|비상각|비상환|비상업", label="위기·비상·컨틴전시·대응/대책 조직·Crisis·자체정상화·Recovery"),
    "55": dict(pat=r"조기\s*(경보|경고|감지|대응|인식)|경보|경고|[Ww]arning|EWS|EWI|징후|위기\s*(단계|수준|지표|상황\s*단계|인식)|"
                   r"관심\s*단계|주의\s*단계|경계\s*단계|심각\s*단계|['‘]주\s*의['’]|[Tt]rigger|트리거|임계|발령|선행\s*지표|모니터링\s*지표|KRI\b|"
                   r"[Rr]ed\s*[Ll]ight|신호등|[Aa]lert|판단\s*지표|한도\s*관리\s*지표|[Rr]isk\s*[Mm]ap|리스크\s*맵|상황판|[Dd]ash\s*[Bb]oard|이상\s*징후",
               ctx=None, excl=r"환경보호|경고\s*조치|경고장", label="조기경보·경보·경고·징후·위기단계·관심/주의/경계/심각 단계·Trigger·임계·발령·KRI·Risk Map·상황판"),
    "규정전문": dict(pat=r"그룹\s*리스크\s*관리\s*규정|그룹\s*위험\s*관리\s*규정|리스크\s*관리\s*규정|위험\s*관리\s*규정|리스크\s*관리\s*지침|위험\s*관리\s*지침|"
                       r"위기\s*관리\s*규정|리스크\s*관리\s*정책\s*규정|리스크\s*관리\s*협의회\s*규정|자체\s*정상화\s*계획\s*위원회\s*규정|내부\s*통제\s*규정|"
                       r"리스크\s*관리\s*기본\s*규정|리스크\s*관리\s*세칙|위험\s*관리\s*기준",
                   ctx=None, label="규정명(리스크관리규정·지침·위기관리규정·정책규정·협의회규정·자체정상화계획위원회규정·내부통제규정·세칙·위험관리기준)"),
}


def refute():
    """같은 출처(그 회사의 risk8 연차·사업·경영공시·대조판 + risk9 다른 기간 정기보고서)에서 넓힌 검색어로 다시 찾는다.
    결과 전부는 REFUTE_JSON(줄·쪽·글), 화면에는 조별 건수만. risk9 판은 FY2025 사업보고서에 같은 줄이 있으면 「중복」으로 따로 셈."""
    load_meta()
    out = {"검색일": TODAY, "방법": "줄 단위 정규식 + 앞뒤 1줄을 이어 붙인 창(줄바꿈으로 갈린 낱말도 잡음) — ctx/near 가 있는 조는 같은 창에 "
                                     "그 낱말이 있을 때만; excl 은 먼저 지움; risk9 판 줄이 같은 회사 FY2025 사업보고서에 공백 무시로 그대로 있으면 dup=1",
           "조": {}}
    for jo, spec in REFUTE.items():
        pat = re.compile(spec["pat"])
        ctx = re.compile(spec["ctx"]) if spec.get("ctx") else None
        ctx2 = re.compile(spec["ctx2"]) if spec.get("ctx2") else None
        near = re.compile(spec["near"]) if spec.get("near") else None
        excl = re.compile(spec["excl"]) if spec.get("excl") else None
        rec = {"검색어": spec["pat"], "ctx": spec.get("ctx"), "ctx2": spec.get("ctx2"), "near": spec.get("near"), "뺀말": spec.get("excl"),
               "label": spec["label"], "문서": {}}
        for co in ("K", "S"):
            br_flat = T(f"{co}_BR").flat("raw")[0]
            keys = [k for k in DOCS if DOCS[k]["co"] == co]
            for k in keys:
                t = T(k)
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
                    dup = 0
                    if k.startswith("R9_") and len(nows(s)) >= 8 and nows(s) in br_flat:
                        dup = 1
                    hits.append({"line": i + 1, "page": t.page[i], "text": s[:240], "dup": dup})
                rec["문서"][k] = {"name": DOCS[k]["name"], "loc": DOCS[k]["loc"], "pages": t.npages, "n": len(hits),
                                 "n_new": sum(1 for h in hits if not h["dup"]), "hits": hits}
        out["조"][jo] = rec
    os.makedirs(VD, exist_ok=True)
    json.dump(out, open(REFUTE_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for jo, rec in out["조"].items():
        parts = []
        for co in ("K", "S"):
            a = sum(v["n"] for k, v in rec["문서"].items() if DOCS[k]["co"] == co and not k.startswith("R9_"))
            b = sum(v["n_new"] for k, v in rec["문서"].items() if DOCS[k]["co"] == co and k.startswith("R9_"))
            parts.append(f"{CO[co]} risk8 {a}줄·risk9(새 줄) {b}줄")
        print(f"{jo}: " + " / ".join(parts))
    print("→", REFUTE_JSON)


# ───────────────────────────── 보정(fix) 자료 ─────────────────────────────
# 「모범규준 조:」 줄 바꾸기(인용 번호 → 새 줄(조 제목은 나중에 자동으로 붙임), 사유)
ART_SET = {
    "K": {
        "K-06": ("34조; 21·26·47조(판단)",
                 "(판단) 26조(신용편중위험: 「Total Exposure 한도」)·47조(내부자본 한도 관리: 「계열사별 총 한도와 리스크 유형별 한도」) 추가"),
        "K-08": ("53조; 57조(판단)", "(판단) 「그룹 유동성 비상조달계획」 → 57조(비상계획) 추가"),
        "K-09": ("53·55조; 56·57조(판단)", "(판단) 「그룹 통합위기상황 분석」 → 56조(통합위기상황분석) 추가"),
        "K-10": ("53·55조; 3·12조(판단)", "(판단) 리스크관리협의회의 역할·구성 → 12조(그룹위험관리협의회) 추가"),
        "K-14": ("조문목차(전문); 34·53·55조 관련 조항; 9·12·47·56·57조(판단)",
                 "3·17조는 인용 글(제1~12조)·note·0장 표·3장 목록 어디에도 닿는 조항이 없어 뺌; note 의 (판단) 9·12·47·56·57조를 조 줄로 옮김"),
    },
    "S": {
        "S-02": ("조문목차; 4·5조; (원문과 다른 곳)",
                 "0장 표·3장 목록의 4·5조 행에 올라 있으나 조 줄에 없었음 — 인용 끝 단락(「그룹리스크관리정책규정에 명시」)이 4·5조 자료"),
        "S-14": ("3조(판단); 12조(판단)", "12조는 지시서에 없는 조 — 「(판단)」 붙임"),
        "S-11b": ("조문목차; 12조(판단)", "(판단) 제75조③~⑥ 그룹리스크협의회 설치·구성 → 12조(그룹위험관리협의회) 추가"),
        "S-12": ("조문목차(전문); 34·53조 관련 조항; 9·21·56·57조(판단)",
                 "56조는 지시서에 없는 조 — 「(판단)」; note 의 57조(제6조①10호 자금조달 계획)·9조(위원회 규정)를 붙이고, 0장 표·3장 21조 행에 올라 있어 21조(판단: 제6조①8호 그룹 내부등급법) 추가"),
        "S-13": ("조문목차(전문); 34·55조 관련 조항; 12·17·21·56조(판단)",
                 "56조는 지시서에 없는 조 — 「(판단)」; 협의회 규정 → 12조(판단); 0장 표·3장 21조 행에 올라 있어 21조(판단: 제5조3호 그룹 비소매 신용평가시스템) 추가"),
        "S-17": ("4·5조; 9·12·14·16조(판단); 3·21조(판단)",
                 "0장 표·3장 21조 행에 올라 있으나 조 줄에 없었음 → 21조(판단); 그룹위험관리위원회 → 9조(판단) 추가"),
        "S-18": ("21·22·24조(판단); 16·20·33조(판단); 34·55조(판단)",
                 "0장 표·3장 34·55조 행에 올라 있고 note 도 34조③·55조라 적었으나 조 줄에 없었음 → 34·55조(판단) 추가"),
    },
}

# 인용 늘리기: 인용 번호 → (문서 키, 새 끝 줄, 사유)
EXTEND = {
    "K": {"K-19": ("K_BR", 80705, "「모범규준 조:」의 23조(운영위험)(판단)이 가리키는 「3) 운영리스크」 단락이 인용 밖이었음 — 원문 줄 80700–80705 를 더함")},
    "S": {},
}

# 그 밖의 글 바꾸기: (회사, 위치, 전, 후, 사유) — 전 글이 꼭 한 번 있어야 함
def text_edits():
    load_meta()
    k_ar, k_br, k_md = DOCS["K_AR"], DOCS["K_BR"], DOCS["K_MD"]
    s_ar, s_br, s_md = DOCS["S_AR"], DOCS["S_BR"], DOCS["S_MD"]
    E = []
    for co, ar, br, md in (("K", k_ar, k_br, k_md), ("S", s_ar, s_br, s_md)):
        old = "- 수집일(인용 정리): 2026-10-07. 원본 수집: 연차보고서 2026-09-22, 사업보고서 2026-10-01, 경영공시 2026-09-30 (8차)."
        E.append((co, "머리 수집일 기준", old,
                  old + f" 날짜 기준(검증 2026-10-07 덧붙임): 연차보고서·경영공시는 수집 기록 fetched_at 의 UTC 날짜(연차 `handoff/연차보고서_파일목록.csv` "
                        f"{ar['fetched']}, 경영공시 `dart_out/risk8/경영공시_2026_2Q.csv` {md['fetched']} = KST 2026-10-01), 사업보고서는 "
                        f"`dart_out/doc/{br['rcp']}/_파일목록.json` 생성시각 {br['fetched']}(KST).",
                  "원본 수집일의 기준(UTC·KST)이 섞여 있어 밝힘 — 날짜 자체는 메타와 같음"))
        old = "- 모범규준 원문(대조 기준): `handoff/13차_산출물/9-4_모범규준_원문.md` (2016.8.1 판 전문, 5장)."
        E.append((co, "머리 모범규준 조 표기", old,
                  old + "\n- 모범규준 조 표기(검증 2026-10-07 보정): ‘N조(조 제목)’ — 조 제목은 `dart_out/risk13/모범규준_조목록.csv` 의 2016.8.1 판 제목. "
                        "지시서(REQUEST13 9-4)에 적힌 조 번호(3·4·5·17·21·22·24·27·34·53·55)는 그대로 두고 그 밖의 조는 「(판단)」. 지시서에 적힌 조라도 "
                        "수집·검증 때 추론으로 이 자료에 붙인 것은 「(판단)」을 둠. 검증 때 더한 인용은 출처 줄 끝에 ‘(검증 때 추가)’, 다른 기간 정기보고서"
                        "(`dart_out/text/risk9/<접수번호>.txt`)에서 온 인용은 제목에 ‘(다른 기간 판)’.",
                  "지시서 (4) — 조 제목·(판단) 표기 규칙을 머리에 적음"))
    for co in ("K", "S"):
        old = "note: 공백·줄바꿈을 모두 빼고 글자열이 대조판 전체에 들어 있는지 봄(쪽 표지 줄 제외). 쪽 번호는 판마다 다를 수 있어 대조하지 않음."
        E.append((co, "4장 note", old,
                  old + " 검증(2026-10-07): ‘같음(공백·DART 쪽 머리말 줄 무시)’은 ‘전자공시시스템 dart.fss.or.kr Page N’ 줄까지 빼면 같다는 뜻(정정판은 쪽이 밀려 "
                        "그 줄 자리가 다름). 검증 때 더한 인용의 대조판 행도 이 표에 더함(risk9 판은 원본 → 정정판).",
                  "4장 결과 문구 하나를 새로 쓰게 되어 뜻을 적음"))
    E.append(("K", "K-15 note 조각", "「내부자본 또는 VaR 형태로 계량화」", "「내부자본(Internal Capital) 또는 VaR(Value at Risk) 형태로 계량화」",
              "note 가 원문의 괄호 글을 빼고 「」로 옮겼음 — 원문(사업 p.796 줄 80504–80506) 글자대로"))
    E.append(("K", "K-19 제목", "### K-19 (7) Basel III — 그룹 신용리스크 내부등급법·시장리스크 표준방법",
              "### K-19 (7) Basel III — 그룹 신용리스크 내부등급법·시장리스크 표준방법·운영리스크 표준방법", "인용을 「3) 운영리스크」 단락까지 늘림(EXTEND)"))
    return E


# 새 인용: 회사 → [(인용 번호, 앞에 넣을 머리(### 번호 또는 ## 제목), 문서 키, 시작 줄, 끝 줄, 제목, 모범규준 조, [note 줄])]
NEW_QUOTES = {
    "K": [
        ("K-30", "### K-05 ", "K_AR", 5565, 5580,
         "사외이사(리스크관리위원회 위원장) 평가 — 「글로벌 진출 등 주요 현안에 대해 법률 리스크를 검토하고 사전 예방적 차원에서 의견을 제시」",
         "34조(판단)",
         ["note: (검증 2026-10-07 반박 일부) 34조③(해외진출 사전 검토)에 닿는 글 — 리스크관리위원회 위원장인 사외이사(p.119 「6) 사외이사 김성용」) 평가의 "
          "「- 기여도」. 사외이사 활동이며, 해외진출 사전 검토를 정한 내규 문구는 여전히 추출 범위에 없음(반박 검색 ‘34’, 검증 기록)."]),
        ("K-30b", "### K-05 ", "R9_20250314001704", 38883, 38906,
         "(다른 기간 판) 2024.12 사업보고서 — 사외이사 후보 추천 사유: 「그룹 해외 진출 시 복수 법무법인 검토를 통한 현지 법률 리스크 제거 필요성을 제안」",
         "34조(판단)",
         ["note: (검증 2026-10-07 반박 일부) FY2024 사업보고서(원본)의 사외이사 후보 추천 사유 표 칸 — 같은 글이 정정판 20250526000370·20260324000822 에도 "
          "있음(4장). (판단) 34조③ 해외진출 사전 검토를 사외이사가 제안한 글이며 내규 문구는 아님.",
          "note: [표 깨짐: 표 칸의 글이 몇 글자씩 줄바꿈되어 나옴 — 글자는 그대로]"]),
        ("K-32", "### K-06 ", "K_AR", 7545, 7556,
         "리스크관리위원회 — 「② 리스크관리 전략 수립」(위험 성향·위험 자본 한도)",
         "5조(판단); 47조(판단)",
         ["note: (검증 2026-10-07 추가) K-05(① 리스크관리 기본방침) 바로 뒤 단락. (판단) 5조②1호(「사전 설정된 위험성향 내에서」)와 47조(내부자본 한도 관리)에 "
          "닿는 전략 방향 목록이며 「리스크관리정책」의 원칙 목록은 아님 — 원칙 목록은 여전히 추출 범위에 없음."]),
        ("K-29", "### K-10 ", "K_AR", 9094, 9100,
         "그룹 경영관리위원회 협의절차 — 부의 사항을 「문서로 요청」받고 심의 의견은 「문서로 통보」",
         "17조(판단); 12조(판단)",
         ["note: (검증 2026-10-07 반박 일부) 17조 — 지주(그룹 경영관리위원회)와 계열사 사이 의사전달을 문서로 한다는 글. 리스크 검토가 필요한 부의 사항은 "
          "「지주회사의 리스크관리협의회에 의견을」 요청(12조(판단)). 위험관련 사항의 문서 형식을 정한 내규(「내부통제규정」의 「의사전달방법 관련 조문」, K-02)는 "
          "여전히 추출 범위에 없음."]),
        ("K-31", "## 3. ", "R9_20240314001585", 36008, 36036,
         "(다른 기간 판) 2023.12 사업보고서 — 2023년 리스크관리위원회 주요 활동: 「그룹 자체정상화계획 주요 현안 보고」(「통합 LCR 임계치 변경 및 모의훈련 실시 결과보고」)",
         "55조(판단); 56·57조(판단)",
         ["note: (검증 2026-10-07 반박 일부) 55조 — 그룹 자체정상화계획에 지표 「통합 LCR」의 「임계치」가 있고 2023년에 바꿨다는 보고 안건(지표 이름 하나·변경 사실). "
          "지표 목록·임계치 값·발령 단계는 여전히 추출 범위에 없음. FY2025 연차보고서·사업보고서·2026 상반기 경영공시와 FY2024 사업보고서에는 「임계치」가 나오지 않음"
          "(반박 검색 ‘55’).",
          "note: FY2023 사업보고서(원본) II장 — 같은 글이 정정판 20240326000894 에도 있음(4장; 정정판 p.711 표에는 「통합 LCR임계치 변」으로 줄바꿈)."]),
    ],
    "S": [
        ("S-29", "### S-16 ", "S_AR", 1585, 1588,
         "이사회(2025.3.4 제2회 임시이사회) — 「내부통제 및 리스크관리 정책 규정 제정의 건」",
         "4·5조(판단); 조문목차",
         ["note: (검증 2026-10-07 추가) p.39 「(다) 2025년 제2회 임시이사회 : 2025.3.4 (화)」 회차의 결의. 철학·원칙을 「명시」한 「그룹리스크관리정책규정」(S-02)의 "
          "제정 경위 — 규정 본문은 여전히 추출 범위에 없음."]),
        ("S-33", "### S-16 ", "S_AR", 1813, 1816,
         "이사회(2025.6.23 제5회 임시이사회) — 「그룹 인도네시아 지배구조 변경에 관한 사항」(현지 법인을 통할할 현지 금융지주회사 설립 검토)",
         "34조(판단)",
         ["note: (검증 2026-10-07 반박 일부) p.45 「(사) 2025년 제5회 임시이사회 : 2025.6.23 (월)」 회차의 보고. (판단) 34조①(해외사업 위험 총괄)에 닿는 "
          "해외 현지법인 통할 구조 검토 — 해외진출 사전 검토·정기 점검을 정한 내규 문구는 여전히 추출 범위에 없음."]),
        ("S-29b", "### S-08 ", "S_AR", 6738, 6743,
         "제4회 위험관리위원회(2025.3.4) — 「그룹리스크관리정책규정 제정(안)」 사전 심의",
         "4·5조(판단); 조문목차",
         ["note: (검증 2026-10-07 추가) 「그룹 전체에 적용되는 “그룹리스크관리정책규정” 제정 건」을 위험관리위원회가 사전 심의(이사회 결의는 S-29). "
          "규정 본문은 여전히 추출 범위에 없음."]),
        ("S-30", "### S-11 ", "S_AR", 7679, 7682,
         "그룹리스크협의회 협의절차 — 위임 사항 결의를 「자회사 리스크관리부서에 전자문서로 통지」",
         "17조(판단); 12조(판단)",
         ["note: (검증 2026-10-07 반박 일부) 17조② 위험관련 의사전달의 문서 형식 사례 — 지주의 그룹리스크협의회 결의를 자회사 리스크관리부서에 「전자문서로 통지」. "
          "그룹내부통제규정 제13조③의 「관련 내규」(공식문서로 전달할 사항)는 여전히 추출 범위에 없음."]),
        ("S-31", "### S-25 ", "S_MD", 3943, 3953,
         "그룹 자본적정성 평가방법 — 바젤3 신용·시장·운영리스크 위험가중자산 산출(그룹 BIS자기자본비율)",
         "21·22조(판단); 37조(판단)",
         ["note: (검증 2026-10-07 반박 일부) 21조 — 그룹(신한금융그룹) 단위 신용리스크 측정을 규제자본(위험가중자산) 기준으로 적은 글. 감독목적 연결 범위는 S-27. "
          "내부자본(위험자본) 기준의 그룹 신용위험 측정 방법·연결/단순 합산 여부는 여전히 추출 범위에 없음."]),
        ("S-32", "### S-26 ", "S_MD", 5360, 5376,
         "(2) 내부등급법 — 「내부등급법 적용범위」(신한은행·신한카드·제주은행)",
         "21조(판단)",
         ["note: (검증 2026-10-07 추가) 21조 — 그룹 신용리스크 위험가중자산 산출에서 내부등급법을 쓰는 자회사·익스포저·승인 날짜. 그 밖의 자회사는 「표준방법」(p.102 「[표준방법 적용범위]」).",
          "note: [표 깨짐: 「그룹사 / BIS 비율 산출방법 / 익스포저 구분 / 승인 날짜」 칸이 줄 단위로 풀려 나옴 — 신한은행·신한카드(기본내부등급법, 2016.12.30), 제주은행(기본내부등급법, 2021.07.12) 순으로 보임(판단)]"]),
    ],
}

# 새 인용 뒤에 붙일 note(기존 인용 아래, 맨 마지막 note 다음): 인용 번호 → note 줄
ADD_NOTES = {
    "K": {
        "K-02": "note: (검증 2026-10-07) 의사전달 문서 형식에 닿는 글을 반박 검색으로 하나 더 찾음 — 그룹 경영관리위원회의 「문서로 요청」·「문서로 통보」(K-29).",
        "K-19": "note: (검증 2026-10-07) 인용 끝을 「3) 운영리스크」 단락(줄 80700–80705)까지 늘림 — 「모범규준 조:」의 23조(운영위험)(판단)이 가리키는 글.",
        "K-05": "note: (검증 2026-10-07) 바로 뒤 「② 리스크관리 전략 수립」 단락은 K-32.",
    },
    "S": {
        "S-15": "note: (검증 2026-10-07) 위험 관련 의사전달의 문서 형식 사례를 반박 검색으로 더 찾음 — 그룹리스크협의회 결의를 「자회사 리스크관리부서에 전자문서로 통지」(S-30).",
        "S-20": "note: (검증 2026-10-07) 그룹 단위 신용리스크 측정(규제자본 기준) 글을 경영공시에서 더 찾음 — S-31(그룹 자본적정성 평가방법)·S-32(내부등급법 적용범위).",
        "S-02": "note: (검증 2026-10-07) 「그룹리스크관리정책규정」 제정 결의·사전 심의는 S-29(이사회)·S-29b(위험관리위원회).",
    },
}

# 「추출 범위에 없음」 반박 결과: 회사 → 조 → (결과, 새 인용, 0장·3장에 덧붙일 글)
REFUTE_RESULT = {
    "K": {
        "3": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 넓힌 검색어(검증 기록 ‘3’)로도 「위험이 경미한 자회사」 적용 배제 기준은 추출 범위에 없음. 「경미」는 현금성자산 정의·제재 기재 생략 문구뿐."),
        "4·5": ("반박 실패(관련 글 추가)", ["K-32"], "검증(2026-10-07): 원칙 목록은 반박 실패. 리스크관리위원회의 「② 리스크관리 전략 수립」 목록(K-32)을 관련 글로 더함."),
        "17": ("일부 반박", ["K-29"], "검증(2026-10-07) 반박 일부: 그룹 경영관리위원회가 계열사 부의 사항을 「문서로 요청」받고 심의 의견을 「문서로 통보」(K-29). 「내부통제규정」의 의사전달 조문은 여전히 추출 범위에 없음."),
        "21": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 경영공시 p.145·p.150 의 그룹 신용리스크 위험가중자산 산출 방법(국민은행·국민카드 내부등급법, 그 밖 표준방법)은 K-19 와 같은 글; 연결/단순 합산을 직접 적은 글은 여전히 추출 범위에 없음."),
        "27": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — FY2023·FY2024 사업보고서도 「전략리스크 및 평판리스크를 중요한 리스크로 인식」 같은 글뿐(관리 체제·평가 수단은 여전히 추출 범위에 없음)."),
        "34": ("일부 반박", ["K-30", "K-30b"], "검증(2026-10-07) 반박 일부: 리스크관리위원회 위원장(사외이사)이 「글로벌 진출 등 주요 현안에 대해 법률 리스크를 검토하고 사전 예방적 차원에서 의견을 제시」(K-30), FY2024 사업보고서의 「그룹 해외 진출 시 복수 법무법인 검토를 통한 현지 법률 리스크 제거 필요성을 제안」(K-30b) — 사외이사 활동이며 내규 문구는 여전히 추출 범위에 없음."),
        "53": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 자체정상화계획·유동성 비상조달계획 안건만 더 나옴; 그룹 위기대응조직의 구성·전환 요건은 여전히 추출 범위에 없음."),
        "55": ("일부 반박", ["K-31"], "검증(2026-10-07) 반박 일부: FY2023 사업보고서의 2023년 리스크관리위원회 보고 안건 「그룹 자체정상화계획 주요 현안 보고」(「통합 LCR 임계치 변경 및 모의훈련 실시 결과보고」, K-31) — 지표 이름 하나·임계치 변경 사실만. 지표 목록·발령 단계는 여전히 추출 범위에 없음."),
        "규정전문": ("반박 실패", [], "「리스크관리규정」·「리스크관리협의회규정」·「리스크관리정책」·「그룹자체정상화계획위원회규정」·「내부통제규정」 조문은 FY2023·FY2024 사업보고서에도 없음(「리스크관리협의회규정」 제2조·제6조 인용뿐)."),
    },
    "S": {
        "3": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 넓힌 검색어(검증 기록 ‘3’)로도 「위험이 경미한 자회사」 적용 배제 기준은 추출 범위에 없음(국외소재 종속기업 산출 제외 S-23 은 FY2024 사업보고서에도 같은 글)."),
        "4·5": ("반박 실패(관련 글 추가)", ["S-29", "S-29b"], "검증(2026-10-07): 「그룹리스크관리정책규정」 본문은 반박 실패. 제정 결의·사전 심의 글(S-29·S-29b)을 더함."),
        "17": ("일부 반박", ["S-30"], "검증(2026-10-07) 반박 일부: 그룹리스크협의회 결의를 「자회사 리스크관리부서에 전자문서로 통지」(S-30). 제13조③의 「관련 내규」는 여전히 추출 범위에 없음."),
        "21": ("일부 반박", ["S-31", "S-32"], "검증(2026-10-07) 반박 일부: 경영공시의 그룹 자본적정성 평가방법(바젤3 신용리스크 위험가중자산, S-31)·내부등급법 적용범위(S-32) — 규제자본 기준의 그룹 측정. 내부자본(위험자본) 기준 측정 방법·연결/단순 합산 여부는 여전히 추출 범위에 없음."),
        "27": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 「평판」·「명성」은 사외이사 후보·평가 문구, 「기후리스크」는 교육·ESG 문구뿐; 전략·평판위험 관리 체제·측정 수단은 여전히 추출 범위에 없음."),
        "34": ("일부 반박", ["S-33"], "검증(2026-10-07) 반박 일부: 이사회 보고 「그룹 인도네시아 지배구조 변경에 관한 사항」(현지 법인을 통할할 현지 금융지주회사 설립 검토, S-33). 해외진출 사전 검토 내규 문구는 여전히 추출 범위에 없음."),
        "53": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 「그룹 위기관리위원회」·「위기관리협의회」의 구성원은 FY2023·FY2024 사업보고서에도 없음(위기관리체계 문단은 S-19 와 같은 글)."),
        "55": ("반박 실패", [], "검증(2026-10-07) 반박 실패 — 그룹 단위 조기경보 지표 목록은 여전히 추출 범위에 없음(신한EZ손해보험 「통합 조기경보체계」는 자회사 사업계획 문구, 사업 p.78)."),
        "규정전문": ("반박 실패", [], "「그룹리스크관리규정」·「그룹리스크관리정책규정」·「그룹 위기관리규정」 조문은 FY2023·FY2024 사업보고서에도 없음."),
    },
}

# 6장 지시서 항목별 대조 — 회사별 칸(받은 글 칸은 「모범규준 조:」 줄에서 자동)
REQ_TABLE = {
    "K": {
        "9-4-1 목차": ("전체(1조(목적)~59조(위임사항)) — 조 번호 맞대기는 6-1 표(판단)",
                     "받은 글: 「리스크관리위원회규정」 제1~12조 전문(K-14, 1-2 표·CSV), 「리스크관리규정」 제정·개정 연혁(K-01), 이사회부의대상 주요규정 목록(K-13)",
                     "「리스크관리규정」(그룹 위험관리기준)·「리스크관리협의회규정」(제2조·제6조 인용만)·「리스크관리정책」·「그룹자체정상화계획위원회규정」·「내부통제규정」의 조문 목차·전문, 리스크관리위원회규정 부칙 — 찾은 방법: 연차보고서 첨부 목차(p.236)와 첨부 1~14(p.237~p.328 끝)를 모두 훑음(1-1 표), 5장 ‘규정 이름’ 검색, 반박 검색 ‘규정전문’(검증 기록)",
                     "지시서 「그룹리스크관리규정」 ↔ KB 이름 「리스크관리규정」(K-01, 첨부 없음); 첨부된 위험관리 내규는 「리스크관리위원회규정」뿐"),
        "9-4-1 iM": ("28조(시스템 구축 및 관리)·30조(목적)", "해당 없음(iM 항목) — KB 전문 규정의 조 번호 맞대기는 6-1 표(판단)", "-", "-"),
        "9-4-1 메리츠": ("9조(그룹위험관리위원회)·57조(비상계획)", "해당 없음(메리츠 항목) — 같은 방식의 맞대기는 6-1 표(판단)", "-", "-"),
        "9-4-2 21·22·24": ("21조(신용위험)·22조(시장위험)·24조(금리위험)", "@21,22,24",
                          "지주가 그룹 신용·시장위험을 연결 기준으로 측정하는지 단순 합산하는지 직접 적은 글(금리위험은 비은행 계열사 「단순합」, K-27) — 찾은 방법: 5장 21·22·24조·‘21·22·24 연결’ 검색, 반박 검색 ‘21·22·24’(그룹·연결·통합 + 신용/시장/금리 + 측정·산출·합산, 단순합, 분산효과; FY2023·FY2024 사업보고서 포함)",
                          "사업보고서 II장(K-15) 중요 리스크 9개 / 연결 주석(K-20) 10개(「외환결제리스크」 추가); II장 「내부자본(Internal Capital)」 / 주석 「경제적자본(Economic Capital)」(K-16·K-21)"),
        "9-4-2 27": ("27조(전략 및 평판위험)", "@27",
                     "전략·평판위험만의 관리 체제(조직·절차)·측정/평가 수단 — 찾은 방법: 5장 27조 검색, 반박 검색 ‘27’(평판·명성·이미지·전략/사업/비재무/잠재/신규/중요 리스크·기후·ESG·여론·언론, 「평판조회」 뺌; FY2023·FY2024 사업보고서 포함)", "-"),
        "9-4-2 34": ("34조(해외위험 관리)", "@34",
                     "해외위험을 총괄·사전 검토·정기 점검하는 내규 문구 — 찾은 방법: 5장 34조 검색, 반박 검색 ‘34’(해외·글로벌·국외·국가·국별·현지·외국·역외·신흥국·Global·Overseas·진출 + 리스크/위험/한도/점검/검토/보고/모니터링/심의; FY2023·FY2024 사업보고서 포함)", "-"),
        "9-4-2 3": ("3조(적용대상)", "@3",
                    "「위험이 경미한 자회사」를 적용에서 빼는 내규 기준 — 찾은 방법: 5장 3조 검색, 반박 검색 ‘3’(경미·소규모·중요성·적용 배제/제외/예외·측정/관리 대상 + 리스크/위험 + 자회사/계열사/종속; FY2023·FY2024 포함), 세 문서·대조판·risk9 전체에서 「경미」·「적용배제」 grep", "-"),
        "9-4-2 17": ("17조(의사전달체계)", "@17",
                     "「내부통제규정」의 「의사전달방법 관련 조문」(문서 형식) — 찾은 방법: 5장 17조 검색, 반박 검색 ‘17’(의사전달·공문·서면·문서·통보·지시·요청·권고·가이드라인 + 자회사/계열사/그룹사/종속; FY2023·FY2024 포함)", "-"),
        "9-4-2 55": ("55조(조기경보체계)", "@55",
                     "그룹 조기경보 지표 목록·임계치 값·발령 단계 전체 — 찾은 방법: 5장 55조 검색, 반박 검색 ‘55’(조기경보·경보·경고·징후·위기단계·관심/주의/경계/심각 단계·Trigger·임계·발령·KRI·Risk Map·상황판; FY2023·FY2024 포함)", "-"),
        "9-4-2 53": ("53조(위기대응조직)", "@53",
                     "그룹 위기대응조직의 구성·전환 요건(유동성 위기 때 「유동성 비상대책 조직」 가동만, K-25) — 찾은 방법: 5장 53조 검색, 반박 검색 ‘53’(위기·비상·컨틴전시·대응/대책 조직·Crisis·자체정상화·Recovery; FY2023·FY2024 포함)", "-"),
        "9-4-3": ("4조(위험관리 철학)·5조(위험관리 원칙)", "@4,5",
                  "「리스크관리정책」 본문(철학·원칙 조문) — 찾은 방법: 5장 4·5조 검색, 반박 검색 ‘4·5’(철학·원칙·기본방침·리스크 문화·위험성향·리스크관리정책·정책규정; FY2023·FY2024 포함)", "-"),
    },
    "S": {
        "9-4-1 목차": ("전체(1조(목적)~59조(위임사항)) — 조 번호 맞대기는 6-1 표(판단)",
                     "받은 글: 「위험관리위원회규정」 제1~10조·부칙 전문(S-12), 「그룹리스크협의회규정」 제1~12조·부칙 전문(S-13), 지배구조 내부규범 제44조·제75조(S-11·S-11b), 그룹내부통제규정 제12·13조(S-15) — 1-2 표·CSV",
                     "「그룹리스크관리규정」(그룹 위험관리기준, 지배구조 내부규범 제75조②)·「그룹리스크관리정책규정」·「그룹 위기관리규정」의 조문 목차·전문 — 찾은 방법: 연차보고서 첨부1~16(p.217~p.316 끝)을 모두 훑음(1-1 표), 5장 ‘규정 이름’ 검색, 반박 검색 ‘규정전문’(검증 기록)",
                     "위험관리위원회규정 제6조③5호의 「제43조제4항 … 제43조제3항」 ↔ 지배구조 내부규범 제44조(S-12 note); 연차 p.24 본문 인용 제6조②는 1~7호, 첨부 전문은 1~8호(S-02 note)"),
        "9-4-1 iM": ("28조(시스템 구축 및 관리)·30조(목적)", "해당 없음(iM 항목) — 신한 전문 규정의 조 번호 맞대기는 6-1 표(판단)", "-", "-"),
        "9-4-1 메리츠": ("9조(그룹위험관리위원회)·57조(비상계획)", "해당 없음(메리츠 항목) — 같은 방식의 맞대기는 6-1 표(판단)", "-", "-"),
        "9-4-2 21·22·24": ("21조(신용위험)·22조(시장위험)·24조(금리위험)", "@21,22,24",
                          "내부자본(위험자본) 기준의 지주 차원 신용위험 측정 방법, 신용·시장위험의 연결 기준 측정/단순 합산 여부(금리위험은 은행 자회사 「단순합」, S-26) — 찾은 방법: 5장 21·22·24조·‘21·22·24 연결’ 검색, 반박 검색 ‘21·22·24’(FY2023·FY2024 사업보고서 포함)", "-"),
        "9-4-2 27": ("27조(전략 및 평판위험)", "@27",
                     "전략·평판위험 관리 체제·측정/평가 수단 전부(사외이사 제언 S-16 만) — 찾은 방법: 5장 27조 검색, 반박 검색 ‘27’(FY2023·FY2024 포함)", "-"),
        "9-4-2 34": ("34조(해외위험 관리)", "@34",
                     "해외진출 사전 검토를 해외로 특정한 내규 문구 — 찾은 방법: 5장 34조 검색, 반박 검색 ‘34’(FY2023·FY2024 포함)", "-"),
        "9-4-2 3": ("3조(적용대상)", "@3",
                    "「위험이 경미한 자회사」를 적용에서 빼는 내규 기준 — 찾은 방법: 5장 3조 검색, 반박 검색 ‘3’(FY2023·FY2024 포함), 「경미」·「적용배제」 grep(「적용배제」는 장기근무 직원 순환근무 표뿐)", "-"),
        "9-4-2 17": ("17조(의사전달체계)", "@17",
                     "그룹내부통제규정 제13조③의 「관련 내규」(공식문서로 전달할 사항) — 찾은 방법: 5장 17조 검색, 반박 검색 ‘17’(FY2023·FY2024 포함)", "-"),
        "9-4-2 55": ("55조(조기경보체계)", "@55",
                     "그룹(지주) 단위 조기경보 지표 목록·임계치(Risk Map 지표 목록 포함) — 찾은 방법: 5장 55조 검색, 반박 검색 ‘55’(FY2023·FY2024 포함)", "-"),
        "9-4-2 53": ("53조(위기대응조직)", "@53",
                     "「그룹 위기관리위원회」·「위기관리협의회」의 구성원 — 찾은 방법: 5장 53조 검색, 반박 검색 ‘53’(FY2023·FY2024 포함)",
                     "사업 p.794 위기관리 전환 요건(「2개 이상의 종속기업이 '주의' 이상 단계에 진입하는 등」)은 모범규준 53조①과 거의 같음(S-19 note, 판단)"),
        "9-4-3": ("4조(위험관리 철학)·5조(위험관리 원칙)", "@4,5",
                  "「그룹리스크관리정책규정」 전문 — 찾은 방법: 5장 4·5조 검색, 반박 검색 ‘4·5’(FY2023·FY2024 포함)",
                  "원칙 ② 연차 「회사는 리스크관리 모범규준을 제시하고」 / 사업 「지배기업은 그룹리스크관리모범규준을 제시하고」(S-03 note)"),
    },
}


# ───────────────────────────── 보정(fix) 실행 ─────────────────────────────
def short_doc(key):
    d = DOCS[key]
    if key.endswith("_AR"):
        return "연차"
    if key.endswith("_BR"):
        return "사업"
    if key.endswith("_MD"):
        return "경영공시"
    m = re.search(r"\((\d{4}\.\d{2})\)", d["name"])
    return f"사업({m.group(1) if m else d['rcp']})"


def cite_line(key, l1, l2, added=False):
    t = T(key)
    d = DOCS[key]
    p1, p2 = t.page[l1 - 1], t.page[l2 - 1]
    pages = f"p.{p1}" if p1 == p2 else f"p.{p1}–p.{p2}"
    tail = " (검증 때 추가)" if added else ""
    return (f"[{d['name']} · {d['loc']} · 쪽 {pages} · 줄 {l1}–{l2} · `{d['path']}` · 원본 수집 {d['fetched'][:10]} · "
            f"인용 {TODAY}{tail}]"), pages


def expand_arts(s, titles):
    def rep(m):
        nums, pd = m.group(1).split("·"), m.group(2) or ""
        return "·".join(f"{n}조({titles[int(n)]}){pd}" for n in nums)
    return re.sub(r"(?<![\d(제])(\d{1,2}(?:·\d{1,2})*)조(\(판단\))?(?!\()", rep, s)


def short(s, n=160):
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n // 2] + f"…({len(s) - n}자)…" + s[-n // 2:]


def diff_snip(a, b):
    """전·후 글의 다른 부분만 짧게."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    parts = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        ctx_a = a[max(0, i1 - 12):i1]
        parts.append(f"「…{ctx_a}[{short(a[i1:i2], 120)}]…」 → 「…{ctx_a}[{short(b[j1:j2], 160)}]…」")
    return " ; ".join(parts[:3]) + (f" (+{len(parts) - 3}곳)" if len(parts) > 3 else "")


def block_range(lines, qid):
    """### qid 머리부터 다음 ### / ## 머리 앞까지."""
    a = next(i for i, ln in enumerate(lines) if ln.startswith(f"### {qid} "))
    b = next((i for i in range(a + 1, len(lines)) if lines[i].startswith("### ") or lines[i].startswith("## ")), len(lines))
    return a, b


def fix():
    load_meta()
    titles = jo_titles()
    log = []           # (회사, 위치, 전, 후, 사유)
    filled = {"K": [], "S": []}
    ensure_pre()
    if not os.path.exists(REFUTE_JSON):
        refute()
    pre_md = {co: open(os.path.join(PRE, os.path.basename(MD[co])), encoding="utf-8").read() for co in CO}
    pre_toc = {co: read_csv(os.path.join(PRE, os.path.basename(TOC[co]))) for co in CO}
    # 검증 전 대조(기록용)
    pre_stats = {}
    for co in CO:
        _, blocks = parse_md(pre_md[co])
        pr, det = [], []
        recs = [check_quote(co, b, pr, det) for b in blocks]
        pre_stats[co] = dict(n=len(blocks), exact=sum(1 for r in recs if r.get("exact")), probs=list(pr))
    md = dict(pre_md)
    # 1) 글 바꾸기
    for co, where, old, new, why in text_edits():
        if md[co].count(old) != 1:
            raise SystemExit(f"[{co}] 바꿀 글이 한 번이 아님({md[co].count(old)}): {where}")
        md[co] = md[co].replace(old, new)
        log.append((co, where, old, new, why))
    for co in CO:
        lines = md[co].split("\n")
        # 2) 「모범규준 조:」 줄 바꾸기
        for qid, (new, why) in ART_SET[co].items():
            a, b = block_range(lines, qid)
            k = next(i for i in range(a, b) if lines[i].startswith("모범규준 조:"))
            old = lines[k]
            lines[k] = "모범규준 조: " + new
            log.append((co, f"{qid} 「모범규준 조:」 줄", old, "모범규준 조: " + expand_arts(new, titles), why))
        # 3) 인용 늘리기
        for qid, (key, l2new, why) in EXTEND[co].items():
            a, b = block_range(lines, qid)
            ci = next(i for i in range(a, b) if lines[i].startswith("[") and " · 쪽 p." in lines[i])
            m = CITE_RE.match(lines[ci])
            l1 = int(m.group("l1"))
            newcite, _ = cite_line(key, l1, l2new)
            f1 = next(i for i in range(ci, b) if lines[i].startswith("```"))
            f2 = next(i for i in range(f1 + 1, b) if lines[i].startswith("```"))
            oldbody = lines[f1 + 1:f2]
            newbody = [x.rstrip() for x in T(key).lines[l1 - 1:l2new]]
            added = [x for x in newbody[len(oldbody):] if x.strip()]
            log.append((co, f"{qid} 인용 늘림", lines[ci],
                        newcite + f" — 코드 블록 끝에 원문 {len(newbody) - len(oldbody)}줄 더함(「{added[0]}」 … 「{added[-1]}」)", why))
            lines[ci] = newcite
            lines[f1 + 1:f2] = newbody
        # 4) 기존 인용 아래 note 덧붙임
        for qid, note in ADD_NOTES[co].items():
            a, b = block_range(lines, qid)
            k = b
            while k > a and not lines[k - 1].strip():
                k -= 1
            lines.insert(k, note)
            log.append((co, f"{qid} note 덧붙임", "", note, "반박 검색으로 찾은 글·보정 사실을 그 자리에서 가리킴"))
        # 5) 새 인용
        for qid, anchor, key, l1, l2, title, arts, notes in NEW_QUOTES[co]:
            pos = next(i for i, ln in enumerate(lines) if ln.startswith(anchor))
            cite, pages = cite_line(key, l1, l2, added=True)
            body = [x.rstrip() for x in T(key).lines[l1 - 1:l2]]
            while body and not body[-1].strip():
                body.pop()
            blk = [f"### {qid} {title}", "", f"모범규준 조: {arts}", "", cite, "", "```text"] + body + ["```", ""] + notes + [""]
            lines[pos:pos] = blk
            filled[co].append(f"새 인용 {qid} — {short_doc(key)} {pages} 줄 {l1}–{l2}: {title}")
            log.append((co, f"새 인용 {qid}", "", f"{short_doc(key)} {pages} 줄 {l1}–{l2} ({len(body)}줄)", "반박 검색으로 찾은 원문 — 지시서 (3)"))
        # 6) 「모범규준 조:」 줄·0장 표 첫 칸에 조 제목
        sec = None
        nt = 0
        for i, ln in enumerate(lines):
            if ln.startswith("## "):
                sec = ln
            if ln.startswith("모범규준 조:"):
                new = "모범규준 조: " + expand_arts(ln[len("모범규준 조:"):].strip(), titles)
                if new != ln:
                    lines[i] = new
                    nt += 1
            elif sec and sec.startswith("## 0.") and re.match(r"^\| \d", ln):
                cells = ln.split("|")
                cells[1] = " " + expand_arts(cells[1].strip(), titles) + " "
                lines[i] = "|".join(cells)
                nt += 1
        filled[co].append(f"「모범규준 조:」 줄·0장 표 첫 칸 {nt}곳에 ‘N조(조 제목)’(모범규준_조목록.csv 2016.8.1 판)")
        # 7) 0장 표·3장 목록을 「모범규준 조:」 줄과 맞춤(빠진 인용 번호를 뒤에 더함) + 반박 결과 덧붙임
        md_lines = lines
        arts = quote_arts(md_lines)
        cites = {}
        for b in parse_md("\n".join(md_lines))[1]:
            m = CITE_RE.match(b["cite"] or "")
            if m and b["qid"] not in cites:
                cites[b["qid"]] = (short_doc(key_for_path(m.group("path"))), m.group("pages"))
        t0, s3 = index_rows(md_lines, co)
        for i, js, ids in t0:
            miss = [q for q, a in arts.items() if a & js and q not in ids]
            cells = md_lines[i].split("|")
            if miss:
                add = "; ".join(f"{cites[q][0]} {cites[q][1]} ({q})" for q in miss)
                cells[4] = cells[4].rstrip() + "; " + add + " "
                log.append((co, f"0장 표 {sorted(js)}조 행", "", add, "「모범규준 조:」 줄에 이 조가 있는 인용을 빠짐없이(색인 맞춤)"))
            jo = "4·5" if js == {4, 5} else str(min(js))
            rr = REFUTE_RESULT[co].get(jo)
            if rr:
                cells[5] = cells[5].rstrip() + " " + rr[2] + " "
            md_lines[i] = "|".join(cells)
        for i, js, ids in s3:
            miss = [q for q, a in arts.items() if a & js and q not in ids]
            if miss:
                add = ", ".join(f"{q}({cites[q][0]} {cites[q][1]})" for q in miss)
                md_lines[i] = md_lines[i].rstrip() + ", " + add
                log.append((co, f"3장 {sorted(js)}조 목록", "", add, "「모범규준 조:」 줄에 이 조가 있는 인용을 빠짐없이(색인 맞춤)"))
            jo = "4·5" if js == {4, 5} else str(min(js))
            rr = REFUTE_RESULT[co].get(jo)
            # 같은 소절의 note 줄·찾은 범위 줄
            j = i + 1
            while j < len(md_lines) and not md_lines[j].startswith("### ") and not md_lines[j].startswith("## "):
                if rr and md_lines[j].startswith("- note:"):
                    md_lines[j] = md_lines[j].rstrip() + " " + rr[2]
                if rr and md_lines[j].startswith("- 찾은 범위:"):
                    spec = REFUTE["21·22·24" if jo == "21" else jo]
                    md_lines[j] = (md_lines[j].rstrip() + f" 반박 검색(검증 2026-10-07): 검색어 {spec['label']} — 같은 세 문서·대조판과 같은 회사 "
                                   f"FY2023·FY2024 사업보고서(`dart_out/text/risk9/`)의 모든 줄, 결과 ‘{rr[0]}’(정규식 전문은 맨 끝 검증 기록 표).")
                j += 1
        filled[co].append("0장 표·3장 목록의 「추출 범위에 없음」 칸·note·찾은 범위 줄에 반박 검색 결과·검색어를 덧붙임")
        lines = md_lines
        # 8) 4장 대조판 표: 다시 셈 + 새 인용 행
        text_now = "\n".join(lines)
        _, blocks = parse_md(text_now)
        bmap = {}
        for b in blocks:
            bmap.setdefault(b["qid"], b)
        last4 = None
        for i, ln in enumerate(lines):
            m = re.match(r"^\| ([KS]-\d+b?) \| `([^`]+)` \| ([^|]+) \| ([^|]*) \|\s*$", ln)
            if not m:
                continue
            last4 = i
            qid, vfile, res = m.group(1), m.group(2), m.group(3).strip()
            b = bmap[qid]
            key = key_for_path(CITE_RE.match(b["cite"]).group("path"))
            got = {DOCS[v]["file"][:-4]: (r, extra) for v, r, extra in variant_result(key, b["body"])}
            if vfile in got and got[vfile][0] != res:
                new = f"| {qid} | `{vfile}` | {got[vfile][0]} | {got[vfile][1] or '-'} |"
                log.append((co, f"4장 {qid}×{vfile}", ln, new, "결과를 다시 셈 — 다른 줄은 DART 쪽 머리말(「전자공시시스템 dart.fss.or.kr Page N」) 줄뿐이라 그 줄을 빼면 공백 무시로 같음"))
                lines[i] = new
        add_rows = []
        for qid, *_ in NEW_QUOTES[co]:
            for b in [x for x in blocks if x["qid"] == qid]:
                key = key_for_path(CITE_RE.match(b["cite"]).group("path"))
                for v, r, extra in variant_result(key, b["body"]):
                    add_rows.append(f"| {qid} | `{DOCS[v]['file'][:-4]}` | {r} | {extra or '-'} |")
        if add_rows:
            lines[last4 + 1:last4 + 1] = add_rows
            filled[co].append(f"4장 대조판 표에 새 인용 행 {len(add_rows)}개")
            log.append((co, "4장 대조판 표", "", " ; ".join(add_rows), "새 인용의 추가공시·정정판 대조"))
        md[co] = "\n".join(lines)
    # 9) CSV(신한 그룹리스크관리정책규정 행)
    toc = {co: [dict(r) for r in pre_toc[co]] for co in CO}
    for r in toc["S"]:
        if r["규정명"] == "그룹리스크관리정책규정":
            old = dict(r)
            r["쪽"] = "p.24; p.164"
            r["전문여부"] = "N — 철학·원칙 등을 「명시」한다는 서술(p.24)과 제정 사전 심의 사실(p.164, S-29b; 이사회 결의 p.40, S-29)만"
            log.append(("S", "조문목차 CSV·1-2 표 그룹리스크관리정책규정 행", f"{old['쪽']} | {old['전문여부']}", f"{r['쪽']} | {r['전문여부']}",
                        "검증 때 찾은 제정 결의·사전 심의 글(S-29·S-29b)을 가리킴"))
            old_md = f"| 그룹리스크관리정책규정 | (조문 목차 추출 범위에 없음) | - | {old['쪽']} | {old['전문여부']} |"
            new_md = f"| 그룹리스크관리정책규정 | (조문 목차 추출 범위에 없음) | - | {r['쪽']} | {r['전문여부']} |"
            assert md["S"].count(old_md) == 1
            md["S"] = md["S"].replace(old_md, new_md)
    # 10) 6장 지시서 항목별 대조 + 6-1 표, 11) 검증 기록
    for co in CO:
        lines = md[co].rstrip("\n").split("\n")
        arts = quote_arts(lines)
        cites = {}
        for b in parse_md("\n".join(lines))[1]:
            m = CITE_RE.match(b["cite"] or "")
            if m and b["qid"] not in cites:
                cites[b["qid"]] = (short_doc(key_for_path(m.group("path"))), m.group("pages"))
        sec6 = build_sec6(co, arts, cites, toc[co], titles)
        filled[co].append("6장 지시서 항목별 대조 표(지시서 9-4 항목 13행 — 받은 글 / 추출 범위에 없음 + 찾은 방법 / 원문과 다른 것) 와 6-1 조 번호 맞대기 표(판단)")
        lines += [""] + sec6
        md[co] = "\n".join(lines) + "\n"
    # 쓰기(검증 기록은 대조 결과를 보고 만든다)
    for co in CO:
        open(MD[co], "w", encoding="utf-8").write(md[co])
        write_toc(TOC[co], toc[co])
    probs, detail, stats = run_check(write=False, quiet=True)
    probs = [p for p in probs if "검증 기록" not in p[1] and p[0] not in (f"{CO['K']} 검증 기록", f"{CO['S']} 검증 기록")]
    for co in CO:
        rec = build_record(co, log, filled[co], pre_stats[co], stats[co], detail, probs)
        md[co] = md[co].rstrip("\n") + "\n\n" + "\n".join(rec) + "\n"
        open(MD[co], "w", encoding="utf-8").write(md[co])
    probs, _, _ = run_check()
    return 0 if not probs else 1


PRE_COMMIT = "8c118c8"


def ensure_pre():
    """검증 전 사본이 없으면(dart_out/raw/ 는 git 밖) 커밋 8c118c8 의 파일로 만든다."""
    import subprocess
    os.makedirs(PRE, exist_ok=True)
    for path in list(MD.values()) + list(TOC.values()):
        dst = os.path.join(PRE, os.path.basename(path))
        if os.path.exists(dst):
            continue
        data = subprocess.run(["git", "show", f"{PRE_COMMIT}:{path}"], capture_output=True, check=True).stdout
        open(dst, "wb").write(data)


def write_toc(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TOC_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in TOC_COLS})


def build_sec6(co, arts, cites, toc_rows, titles):
    out = ["## 6. 지시서 항목별 대조(검증 2026-10-07 추가)", "",
           "지시서(REQUEST13 「9-4 타사 그룹리스크관리규정(모범규준 조항과 맞대기)」와 「끝에 낼 것」)의 항목마다 이 파일의 받은 글(인용 번호 — 2장) 또는 "
           "「추출 범위에 없음」과 찾은 방법을 적었다. 받은 글 칸은 각 인용의 「모범규준 조:」 줄에서 뽑은 것(조 번호 뒤 「(판단)」이 붙은 인용 포함).", "",
           "| 지시서 항목 | 지시서 원문(그대로) | 모범규준 조(조 제목) | 받은 글(인용 번호) | 추출 범위에 없음 + 찾은 방법 | 원문과 다른 것을 발견한 곳 |",
           "|---|---|---|---|---|---|"]
    for lab, s in REQ_ITEMS:
        if lab in ("끝 표", "끝 조 번호"):
            if lab == "끝 표":
                row = ("—", "있음 — 이 6장 표(받은 글 / 추출 범위에 없음 + 찾은 방법 / 원문과 다른 것 칸)", "-", "-")
            else:
                row = ("—", "있음 — 2장 각 인용의 「모범규준 조:」 줄(조 제목·(판단) 포함), 0장 표 첫 칸, 이 표의 셋째 칸", "-", "-")
        else:
            jo, got, nf, df = REQ_TABLE[co][lab]
            if got.startswith("@"):
                nums = [int(x) for x in got[1:].split(",")]
                parts = []
                for n in nums:
                    ids = [q for q, a in arts.items() if n in a]
                    parts.append(f"{n}조: " + ", ".join(f"{q}({cites[q][0]} {cites[q][1]})" for q in ids))
                got = "받은 글 — " + " / ".join(parts)
            row = (jo, got, ("추출 범위에 없음 — " + nf) if nf != "-" else "-", df)
        out.append(f"| {lab} | 「{s}」 | {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
    out += ["", "note: 「추출 범위에 없음」은 위 찾은 방법의 범위(연차보고서·사업보고서·경영공시와 그 추가공시·정정판, 반박 검색은 같은 회사 FY2023·FY2024 사업보고서까지)에서 "
                "찾지 못했다는 뜻이며 「없음」 단정이 아님.", ""]
    # 6-1 조 번호 맞대기(판단)
    out += ["### 6-1 전문 규정 조 번호 ↔ 모범규준 같은 번호 조(판단)", "",
            "지시서 9-4-1 의 iM(「28조…30조…가 모범규준과 조 번호가 같음」)·메리츠(「같은 방식으로 대조」) 항목과 같은 방식으로, 이 회사 연차보고서에 전문이 실린 규정의 "
            "조 번호를 모범규준(2016.8.1 판) 같은 번호 조와 맞대어 봄. 조 제목은 1-2 표·CSV, 모범규준 제목은 `dart_out/risk13/모범규준_조목록.csv`.", "",
            "| 규정 | 조(제목) | 모범규준 같은 번호 조(제목) | 제목 같음 |", "|---|---|---|---|"]
    same = 0
    total = 0
    for r in toc_rows:
        m = re.fullmatch(r"제(\d+)조", r["조번호"])
        if not (m and r["전문여부"].startswith("Y")):
            continue
        n = int(m.group(1))
        t = titles.get(n, "(모범규준에 없는 번호)")
        eq = "같음" if nows(t) == nows(r["조제목"]) else "다름"
        same += eq == "같음"
        total += 1
        out.append(f"| {r['규정명']} | 제{n}조({r['조제목']}) | {n}조({t}) | {eq} |")
    out += ["", f"note: (판단) 맞대어 본 {total}개 조 가운데 번호·제목이 같은 조는 {same}개(「목적」 조). 이 규정들은 위원회·협의회 운영 규정이라 모범규준(그룹 위험관리 기준)과 "
                f"조 번호 체계가 다름 — 모범규준에 대응하는 {'「리스크관리규정」(K-01)' if co == 'K' else '「그룹리스크관리규정」(S-05·S-11b)'}의 조문은 추출 범위에 없음(6장 ‘9-4-1 목차’ 행의 찾은 방법).", ""]
    return out


def build_record(co, log, filled, pre_st, st, detail, probs):
    R = [f"## 검증 기록({TODAY})", ""]
    ext = [x for x in log if x[0] == co]
    n_new = sum(1 for x in ext if x[1].startswith("새 인용"))
    R.append(f"- 스크립트: `scripts/dart/verify13_g_kb_shinhan.py` — 인자 없이(대조 — 결과 `{OUT_TXT}`, 문제 0 이면 exit 0), `refute`(반박 검색 — 결과 "
             f"`{REFUTE_JSON}`), `fix`(검증 전 사본 `{PRE}/`(커밋 8c118c8 의 파일 그대로)에서 이 파일·조문목차 CSV 를 다시 만듦, 멱등). 로컬 텍스트만 읽음(웹 요청·API 키·OC 없음). "
             f"원 생성기 `scripts/dart/web13_g_kb_shinhan.py` 를 다시 돌리면 이 보정이 지워짐.")
    R.append(f"- 대조한 인용(검증 전): 코드 블록 {pre_st['n']}개 — {pre_st['exact']}개가 출처 줄이 가리킨 텍스트 줄과 글자까지 같음(줄 끝 공백만 무시), "
             f"출처 표기(문서명·URL/접수번호·쪽·줄 번호·원본 수집일) 문제 {len(pre_st['probs'])}개. 원문과 다른 인용은 없음 — 고친 인용 글 없음.")
    R.append(f"- 대조한 인용(검증 뒤): 코드 블록 {st['blocks']}개(새 인용 {n_new}개·늘린 인용 {len(EXTEND[co])}개 포함) — 글자까지 같음 {st['exact']}, 공백만 다름 {st['same_ws']}; "
             f"4장 대조판 행 {st['variant_rows']}개·5장 검색 기록 {st['search_rows']}행·조문목차 CSV {st['toc_rows']}행·1-1 첨부 표 {st['attach_rows']}행을 다시 계산·대조, "
             f"note·표의 「…」 조각 {st['frags']}개를 원본(회사 텍스트·모범규준 변환본·지시서)과 공백 무시로 대조.")
    al = [f"「{f}」({FRAG_ALLOW[f]})" for f in st["frags_allowed"]]
    R.append("- 「…」 조각 가운데 원본 글이 아닌 표기(대조에서 넘김): " + ("; ".join(al) if al else "없음") + ".")
    R += ["", "### 고친 곳(전 → 후)", ""]
    for _, where, old, new, why in ext:
        if where.startswith("새 인용") or where.endswith("note 덧붙임") or where.startswith("0장 표") or where.startswith("3장") or where == "4장 대조판 표":
            continue
        if old and new.startswith(old) and len(new) > len(old):
            R.append(f"- {where}: 끝에 덧붙임 「{short(new[len(old):].strip(), 420)}」 — {why}")
        elif old and len(old) <= 260 and len(new) <= 360 and "\n" not in old + new:
            R.append(f"- {where}: 「{old}」 → 「{new}」 — {why}")
        else:
            R.append(f"- {where}: {diff_snip(old, new) if old else short(new)} — {why}")
    R += ["", "### 채운 항목", ""]
    R.append("- 지시서 대조(검증 전): 9-4-1 목차, 9-4-2 의 21·22·24·27·34·3·17·55·53조, 9-4-3(4·5조)은 0장 표·3장에 받은 글 또는 「추출 범위에 없음」+찾은 범위(5장 검색어)가 "
             "있었음. 빠졌던 것 — ① 「끝에 낼 것」의 한 표(받은 것 / 받지 못한 것 / 원문과 다른 것) ② 9-4-1 의 iM·메리츠 항목과 같은 방식의 조 번호 맞대기(이 회사엔 직접 해당 "
             "없음) ③ 조 번호의 조 제목 — 6장 표·6-1 표(판단)·「N조(조 제목)」 표기로 채움.")
    for f in filled:
        R.append(f"- {f}")
    for _, where, old, new, why in ext:
        if where.startswith("0장 표") or where.startswith("3장"):
            R.append(f"- {where}에 더한 인용: {new} — {why}")
        elif where.endswith("note 덧붙임"):
            R.append(f"- {where}: {short(new, 200)}")
    R += ["", "### 「추출 범위에 없음」 반박 시도", "",
          "같은 출처(이 회사의 연차보고서·사업보고서·경영공시와 추가공시·정정판 텍스트, 그리고 `dart_out/text/risk9/` 의 같은 회사 FY2023·FY2024 사업보고서와 정정판)의 "
          "모든 줄을 수집 에이전트 5장보다 넓힌 정규식(낱말 변형·띄어쓰기·영문·동의어)으로 다시 찾음. 결과 전부(줄·쪽·글): "
          f"`{REFUTE_JSON}`. 걸린 줄은 이미 인용한 쪽을 빼고 읽어 판정.", "",
          "| 조 | 결과 | 새 인용 | 걸린 줄(이 회사 risk8 / risk9 새 줄) | 판정 근거 |", "|---|---|---|---|---|"]
    rj = json.load(open(REFUTE_JSON, encoding="utf-8")) if os.path.exists(REFUTE_JSON) else {"조": {}}
    for jo, (res, ids, txt) in REFUTE_RESULT[co].items():
        key = "21·22·24" if jo == "21" else jo
        rec = rj["조"].get(key, {"문서": {}})
        a = sum(v["n"] for k, v in rec["문서"].items() if DOCS.get(k, {}).get("co") == co and not k.startswith("R9_"))
        b = sum(v["n_new"] for k, v in rec["문서"].items() if DOCS.get(k, {}).get("co") == co and k.startswith("R9_"))
        lab = {"규정전문": "규정 전문(조문 목차)", "4·5": "4·5조", "21": "21조·22조·24조"}.get(jo, f"{jo}조")
        R.append(f"| {lab} | {res} | {', '.join(ids) if ids else '-'} | {a} / {b} | {txt} |")
    R += ["", "반박 검색 정규식(「¦」는 「|」, ctx·near 는 같은 창(앞뒤 1줄)에 있어야 하는 말, 뺀말은 먼저 지운 말):", "",
          "| 조 | 검색어(낱말) | 정규식 | ctx·near·뺀말 |", "|---|---|---|---|"]
    for jo, spec in REFUTE.items():
        extra = "; ".join(f"{k}={spec[k]}" for k in ("ctx", "ctx2", "near", "excl") if spec.get(k)).replace("|", "¦")
        R.append(f"| {jo} | {spec['label']} | `{spec['pat'].replace('|', '¦')}` | {extra or '-'} |")
    R += ["", "### 남은 문제", ""]
    rest = [p for p in probs if p[0].startswith(CO[co])]
    if rest:
        for w, s in rest:
            R.append(f"- {w}: {s}")
    else:
        R.append("- 대조 문제 0(이 절을 쓴 뒤 스크립트를 다시 돌려 확인 — 결과 파일 참조).")
    R.append("- 「추출 범위에 없음」으로 남은 것은 위 반박 표의 「반박 실패」와 「일부 반박」의 나머지 — 회사 홈페이지 내규 게시판 등 이 범위 밖 자료는 찾지 않음(작업 범위 밖).")
    R.append("- 다른 기간 판(FY2023·FY2024) 인용(제목 ‘(다른 기간 판)’)은 FY2025 판에 같은 글이 없는 것 — 지금도 그런지는 FY2025 판에서 확인되지 않음.")
    return R


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "refute":
        refute()
        return 0
    if mode == "fix":
        return fix()
    probs, _, _ = run_check()
    return 0 if not probs else 1




if __name__ == "__main__":
    sys.exit(main(sys.argv))
