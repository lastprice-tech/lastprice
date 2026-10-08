# -*- coding: utf-8 -*-
"""13차 9-4 모범규준 대조표 대조(검증) — scripts/dart/web13_compare.py 의 산출물을 읽기만 한다(고치지 않음).

    python3 -I scripts/dart/verify13_compare.py
        → 문제 0 이면 exit 0, 아니면 exit 1. 결과는 dart_out/risk13/verify13_compare.txt (실행마다 다시 씀).

대상: handoff/13차_산출물/9-4_모범규준_대조표.md, dart_out/risk13/9-4_모범규준_대조표.csv(D 행렬), dart_out/risk13/9-4_조번호대조.csv
견주는 곳: dart_out/risk13/9-4_지시서항목_상태_A.csv·_B.csv(R1 상태의 단일 근거), handoff/13차_산출물/9-4_<회사>.md 8개(0장 판정 칸,
          지시서 항목 대조 표, 인용 블록), dart_out/risk13/9-4_<회사>_조문목차.csv 8개, dart_out/risk13/모범규준_조목록.csv,
          handoff/13차_산출물/9-4_모범규준_원문.md(5장 2016.8.1 판·6장 2012.3.13 제정판 전문), dart_out/text/risk8/(회사 원본 텍스트 쪽)

점검(web13_compare.py 의 코드를 쓰지 않고 따로 다시 읽고 다시 셈):
 ① D 행렬 — md D 표의 모든 칸 = 행렬 CSV(상태 + 「 — 」 + 인용 자리). 지시서 9-4-2·9-4-3 조 88칸 = 상태 CSV 「상태」 = 회사 md 0장 판정 칸
    = 지시서 항목 대조 표(그룹 A 7장·그룹 B 6장) 상태 칸. 9-4-1 칸(iM 28·30, 메리츠 9·57) = 회사 md 0장 판정 = 지시서 항목 대조 표
    「9-4 1. iM」·「9-4 1. 메리츠」 행. 그 밖의 칸은 「(판단) …」 또는 「9-4 검색 범위 밖」. R1 세 단계 낱말만(「찾은 글」 없음).
    칸이 가리키는 인용 번호([ID])가 그 회사 md 인용 머리에 있음. 범주 수 표·요약 D 행 = 다시 센 값. 조 제목·장·절·「9-4 조사」 칸.
 ② A~C 조 번호·제목 — A-1·A-4 = iM 조문목차 CSV + 모범규준_조목록.csv(+ 모범규준 원문 md 장·절 머리), 기계 비교(공백·가운뎃점 무시)
    다시 셈; A-2 통계 다시 셈; B 표·B 절 제목 = 메리츠 조문목차 CSV·조목록, 인용 횟수 = 메리츠 md 코드 블록 다시 셈;
    C-1 상태 칸 = 회사 md 「9-4 1.」 행; C-3 = 조번호대조 CSV 다시 셈; 조번호대조 CSV 행 = 8개사 조문목차 CSV 행(순서·조번호·조제목·쪽·
    문서·접수번호·비고), 같은 번호 조 제목·기계 비교 다시 셈, 「모범규준_조_표지(R2)」 열.
 ③ 원문 인용 — 대조표 코드 블록 줄(「[줄임: …]」 표시 줄 빼고)과 B 표의 「」 발췌가 회사 md 인용 블록·모범규준 원문 md 코드 블록에
    공백 무시로 글자 그대로. 회사 인용은 원본 텍스트 dart_out/text/risk8 의 그 쪽(=== p.N ===)에서도 찾아 봄(회사 md 에서 못 찾으면
    원본 쪽에서 찾았을 때만 통과).
 ④ 입력 sha256 — 대조표 「입력 파일(읽은 판)」 표(64자) = 지금 파일, 입력 20개.
 ⑤ API 키·OC — 환경변수·.env 의 DART_API_KEY·LAW_OC 값(화면·파일에 찍지 않음)이 산출물·스크립트·중간 기록·이 결과 txt 에 없음;
    가리지 않은 「crtfc_key=」·「OC=」 꼴 없음.
 ⑥ 낱말·절 — R5(「작성일: 2026-10-07」 라벨 없음), R3(코드 블록·정합성 보정 소절 밖 우리 글의 「없음」 — 허용 꼴 밖 0),
    R2(회사 인용 태그 줄: 「9-4 조문 대조(대조표 …)」 표지, 지시서 조에는 (판단) 없음·그 밖의 조에는 (판단)),
    「## 검증 기록」이 끝 절이고 「### 정합성 보정(2026-10-08)」 소절이 있음.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만).
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_MD = "handoff/13차_산출물/9-4_모범규준_대조표.md"
OUT_MATRIX = "dart_out/risk13/9-4_모범규준_대조표.csv"
OUT_MAP = "dart_out/risk13/9-4_조번호대조.csv"
OUT_TXT = "dart_out/risk13/verify13_compare.txt"
STATE = ["dart_out/risk13/9-4_지시서항목_상태_A.csv", "dart_out/risk13/9-4_지시서항목_상태_B.csv"]
MOB_MD = "handoff/13차_산출물/9-4_모범규준_원문.md"
MOB_CSV = "dart_out/risk13/모범규준_조목록.csv"
RAW_DIR = "dart_out/raw/web13/compare94"
COS = ["메리츠금융지주", "한국투자금융지주", "KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "iM금융지주", "NH농협금융지주"]
SHORT = {"메리츠금융지주": "메리츠", "한국투자금융지주": "한국투자", "KB금융지주": "KB", "신한금융지주": "신한",
         "하나금융지주": "하나", "우리금융지주": "우리", "iM금융지주": "iM", "NH농협금융지주": "NH"}
LISTED_ALL = [3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55]
DIR941 = {"iM금융지주": ("9-4 1. iM", [28, 30]), "메리츠금융지주": ("9-4 1. 메리츠", [9, 57])}
TOCLAB = "9-4 조문 대조(대조표 A~C)"
CATS = ["받은 글", "일부", "추출 범위에 없음", "(판단)", "9-4 검색 범위 밖"]
DOTRE = re.compile(r"[\s·ㆍ∙・‧•･]")
QID = r"[A-Z]{1,2}-[A-Za-z]?\d+[a-z]?"
SECRET_KEYS = ("DART_API_KEY", "LAW_OC", "OC", "DART_KEY")


# ───────────────────────────── 도구
class Rep:
    def __init__(self):
        self.lines, self.probs, self.sec = [], [], ""

    def p(self, s):
        self.lines.append(s)

    def bad(self, s):
        self.probs.append(f"[{self.sec}] {s}")
        self.lines.append(f"  ✗ {s}")

    def head(self, s):
        self.sec = s.split(" ")[0]
        self.lines.append("")
        self.lines.append(f"## {s}")


def rd(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def rcsv(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def nows(s):
    return re.sub(r"\s+", "", s or "")


def dn(s):
    return DOTRE.sub("", s or "")


def strip_ann(s):
    s = re.sub(r"<[^>]*>", "", s or "")
    s = re.sub(r"\(\d{4}\.\d{1,2}[.,]\s*\d{1,2}\s*(신설|개정)\)", "", s)
    return s.strip()


def cellf(s):
    return (s or "").replace("|", "／").replace("\n", " ")


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_rel(co):
    return f"handoff/13차_산출물/9-4_{co}.md"


def csv_rel(co):
    return f"dart_out/risk13/9-4_{co}_조문목차.csv"


def table_at(L, start):
    """start 줄 뒤의 첫 md 표 → (머리 칸, 자료 줄 [(줄 번호, 칸)])."""
    rows, on = [], False
    for k in range(start + 1, len(L)):
        l = L[k]
        if l.startswith("|"):
            on = True
            rows.append((k + 1, cells(l)))
        elif on or l.startswith("#"):
            break
    if not rows:
        return [], []
    return rows[0][1], [r for r in rows[1:] if not set(r[1][0]) <= set("-: ")]


def find(L, pred, what):
    for k, l in enumerate(L):
        if pred(l):
            return k
    raise SystemExit(f"[verify13_compare] {what} 를 찾지 못함")


def code_blocks(L):
    """[(시작 줄 번호(1부터), [줄 글])] — ``` 사이."""
    out, on, cur, st = [], False, [], 0
    for k, l in enumerate(L):
        if l.startswith("```"):
            if on:
                out.append((st, cur))
                cur = []
            else:
                st = k + 1
            on = not on
            continue
        if on:
            cur.append(l)
    return out


def r1_kind(s):
    if s == "받은 글":
        return "받은 글"
    if s.startswith("일부(") and s.endswith(")"):
        return "일부"
    if s.startswith("추출 범위에 없음"):
        return "추출 범위에 없음"
    return None


def nums_first(c):
    hit = re.findall(r"(\d+)조", c)
    if hit:
        return [int(x) for x in hit]
    return [int(x) for x in re.findall(r"\d+", c.split("(")[0])]


# ───────────────────────────── 회사 md 읽기
def sec0(L):
    i = find(L, lambda l: l.startswith("## 0."), "0장")
    hdr, data = table_at(L, i)
    j = hdr.index("판정")
    out = {}
    for _, c in data:
        for n in nums_first(c[0]):
            out[n] = c[j]
    return out


def directive(co, L):
    i = find(L, lambda l: re.match(r"^## [67]\. 지시서 항목별 대조", l) is not None, f"{co} 지시서 항목 대조 절")
    hdr, data = table_at(L, i)
    scol = next(k for k, h in enumerate(hdr) if h.startswith("상태"))
    out, toc = {}, None
    for _, c in data:
        lab, st = c[0], c[scol]
        if lab in ("9-4 1.", "9-4-1 목차"):
            toc = st
            continue
        m = re.fullmatch(r"9-4(?: |-)2\.? ?([\d·]+)", lab)
        if lab in ("9-4 3.", "9-4-3"):
            arts = [4, 5]
        elif m:
            arts = [int(x) for x in m.group(1).split("·")]
        elif co in DIR941 and lab == DIR941[co][0]:
            arts = DIR941[co][1]
        else:
            continue
        multi = dict((int(a), s.strip()) for a, s in re.findall(r"(\d+)조: (.+?)(?= / \d+조: |$)", st))
        for a in arts:
            if multi:
                out[a] = multi.get(a)
            elif "조별 상태는 아래" in st:
                continue
            elif a in out and len(arts) > 1:
                continue
            else:
                out[a] = st
    return out, toc


def quote_ids(L):
    ids = set()
    for l in L:
        m = re.match(r"^#{3,4} \[?(" + QID + r")\]?(?:\s|$)", l)
        if m:
            ids.add(m.group(1))
    return ids


def code_text(L):
    return "\n".join("\n".join(b) for _, b in code_blocks(L))


# ───────────────────────────── 모범규준
def mob_parse(L, prefix):
    i = find(L, lambda l: l.startswith(prefix), prefix)
    j = next((k for k in range(i + 1, len(L)) if L[k].startswith("## ")), len(L))
    a = next(k for k in range(i, j) if L[k].startswith("```"))
    b = next(k for k in range(a + 1, j) if L[k].startswith("```"))
    chs, secs, arts = {}, [], {}
    ch = None
    for l in L[a + 1:b]:
        if l.replace(" ", "").startswith("부칙"):
            break
        m = re.match(r"^제\s*(\d+)\s*장\s*(.*)$", l)
        if m:
            ch = int(m.group(1))
            chs[ch] = m.group(2).strip()
            continue
        m = re.match(r"^제\s*(\d+)\s*절\s*(.*)$", l)
        if m:
            secs.append((ch, int(m.group(1)), m.group(2).strip()))
            continue
        m = re.match(r"^제\s*(\d+)\s*조\s*\(([^)]*)\)", l)
        if m:
            arts[int(m.group(1))] = m.group(2)
    units = [(f"제{c}장 「{t}」", dn(strip_ann(t))) for c, t in chs.items()] + \
            [(f"제{c}장 제{s}절 「{t}」", dn(strip_ann(t))) for c, s, t in secs]
    return {"chs": chs, "arts": arts, "units": units}


# ───────────────────────────── ① D 행렬
def check_d(R, M, mat, ST, S0, DT, QIDS, MOBR):
    R.head("① D 행렬 = 상태 CSV = 회사 md")
    i = find(M, lambda l: l.startswith("## D. 행렬"), "D 절")
    hdr, data = table_at(M, i)
    if hdr[:3] != ["조", "조 제목(2016.8.1)", "9-4 조사"] or hdr[3:] != [SHORT[c] for c in COS]:
        R.bad(f"D 표 머리 칸 다름: {hdr}")
        return
    if len(data) != 56 or len(mat) != 56:
        R.bad(f"D 표 {len(data)}행·행렬 CSV {len(mat)}행(기대 56)")
    matd = {int(r["조"]): r for r in mat}
    n_cell = n_listed = n_941 = n_other = 0
    counts = {co: dict.fromkeys(CATS, 0) for co in COS}
    for ln, c in data:
        n = int(c[0])
        r = matd.get(n)
        mr = MOBR.get(n)
        if not r or not mr:
            R.bad(f"D {n}조: 행렬 CSV·조목록 행 없음")
            continue
        for k in ("장", "절", "제목_2016.8.1판", "제목_2012.3.13제정판"):
            if r[k] != mr[k]:
                R.bad(f"D {n}조: 행렬 CSV {k} 「{r[k]}」 ≠ 조목록 「{mr[k]}」")
        if c[1] != cellf(mr["제목_2016.8.1판"]):
            R.bad(f"D {n}조(md {ln}행): 조 제목 「{c[1]}」 ≠ 조목록 「{mr['제목_2016.8.1판']}」")
        exp = "Y" if n in LISTED_ALL else ("Y(" + "·".join(SHORT[co] for co, (_, a) in DIR941.items() if n in a) + " 항목)"
                                          if any(n in a for _, a in DIR941.values()) else "N")
        if c[2] != exp or r["지시서9-4조사조"] != exp:
            R.bad(f"D {n}조: 「9-4 조사」 md 「{c[2]}」·CSV 「{r['지시서9-4조사조']}」 ≠ 기대 「{exp}」")
        for k, co in enumerate(COS):
            n_cell += 1
            s, ptr = r[SHORT[co]], r[SHORT[co] + "_인용"]
            md_cell = c[3 + k]
            want = cellf(f"{s} — {ptr}" if ptr else s)
            if md_cell != want:
                R.bad(f"D {n}조 {SHORT[co]}(md {ln}행): md 칸 ≠ 행렬 CSV 칸(상태+인용) — md 「{md_cell[:80]}」 / CSV 「{want[:80]}」")
            if "찾은 글" in s or "찾은 글" in md_cell:
                R.bad(f"D {n}조 {SHORT[co]}: 「찾은 글」 낱말(R1)")
            ids = re.findall(r"\[(" + QID + r")\]", ptr + " " + s)
            for q in ids:
                if q not in QIDS[co]:
                    R.bad(f"D {n}조 {SHORT[co]}: 인용 번호 [{q}] 가 회사 md 인용 머리에 없음")
            if n in LISTED_ALL:
                n_listed += 1
                st = ST.get((co, n), {}).get("상태")
                z, d = S0[co].get(n), DT[co].get(n)
                if not (s == st == z == d):
                    R.bad(f"D {n}조 {SHORT[co]}: 행렬 「{s}」 / 상태 CSV 「{st}」 / md 0장 「{z}」 / 지시서 항목 대조 「{d}」 — 같지 않음")
                kd = r1_kind(s)
                if kd is None:
                    R.bad(f"D {n}조 {SHORT[co]}: 상태 「{s}」 가 R1 세 단계가 아님")
                elif kd == "추출 범위에 없음" and "찾은 방법" not in ptr:
                    R.bad(f"D {n}조 {SHORT[co]}: 「추출 범위에 없음」 칸에 찾은 방법 없음")
                if " — " in s or "(판단)" in s:
                    R.bad(f"D {n}조 {SHORT[co]}: 상태 글에 「 — 」·「(판단)」(R1·R2)")
                if kd:
                    counts[co][kd] += 1
            elif co in DIR941 and n in DIR941[co][1]:
                n_941 += 1
                z, d = S0[co].get(n), DT[co].get(n)
                if not (s == z == d) or r1_kind(s) is None:
                    R.bad(f"D {n}조 {SHORT[co]}(9-4-1): 행렬 「{s}」 / md 0장 「{z}」 / 지시서 항목 대조 「{d}」 — 같지 않거나 R1 아님")
                if r1_kind(s):
                    counts[co][r1_kind(s)] += 1
            else:
                n_other += 1
                if s == "9-4 검색 범위 밖" and not ptr:
                    counts[co]["9-4 검색 범위 밖"] += 1
                elif s.startswith("(판단) ") and not ptr:
                    counts[co]["(판단)"] += 1
                else:
                    R.bad(f"D {n}조 {SHORT[co]}: 지시서 밖 칸 꼴이 「(판단) …」·「9-4 검색 범위 밖」 아님 — 「{s[:60]}」")
    R.p(f"  D 표 {len(data)}행 × 8개사 = {n_cell}칸 — 지시서 조 {n_listed}·9-4-1 {n_941}·그 밖 {n_other}")
    # 상태 CSV 쪽에서도 빠진 칸 없는지
    if len(ST) != 88:
        R.bad(f"상태 CSV 칸 {len(ST)}(기대 88)")
    # 범주 수 표
    k = next((x for x in range(i, len(M)) if M[x].startswith("| 회사 | 받은 글 |")), None)
    if k is None:
        R.bad("D 범주 수 표 없음")
    else:
        hh, rows = table_at(M, k - 1)
        tot = dict.fromkeys(CATS, 0)
        for _, c in rows:
            name = c[0]
            if name == "합계":
                got = [int(x) for x in c[1:6]]
                want = [sum(counts[co][kk] for co in COS) for kk in CATS]
            else:
                co = next((x for x in COS if SHORT[x] == name), None)
                if not co:
                    R.bad(f"범주 수 표 행 「{name}」")
                    continue
                got = [int(x) for x in c[1:6]]
                want = [counts[co][kk] for kk in CATS]
            if got != want:
                R.bad(f"범주 수 표 「{name}」 {got} ≠ 다시 셈 {want}")
        for kk in CATS:
            tot[kk] = sum(counts[co][kk] for co in COS)
        R.p("  범주 다시 셈(합계): " + " · ".join(f"{kk} {tot[kk]}" for kk in CATS))
        summ = next((l for l in M if l.startswith("| D. 행렬")), "")
        m1 = re.search(r"받은 글 (\d+) · 일부 (\d+) · 추출 범위에 없음 (\d+)", summ)
        m2 = re.search(r"\(판단\) (\d+) · 9-4 검색 범위 밖 (\d+)", summ)
        if not (m1 and m2) or [int(x) for x in m1.groups() + m2.groups()] != [tot[kk] for kk in CATS]:
            R.bad(f"요약 표 D 행 수 ≠ 다시 셈 — 「{summ[:200]}」")
    # 「찾은 글」 낱말: 요약·D 절·받은 것 표(정합성 보정 소절의 「전」 칸은 1차 판 글이라 뺌)
    j = find(M, lambda l: l.startswith("## 검증 기록"), "검증 기록 절")
    for x in range(0, j):
        l = M[x]
        if "찾은 글" in l and not l.startswith("- 상태 표기") and not l.startswith("note: 21·22·24조"):
            R.bad(f"md {x + 1}행: 「찾은 글」 낱말(R1) — 「{l[:80]}」")
    for r in mat:
        for kk, v in r.items():
            if "찾은 글" in (v or ""):
                R.bad(f"행렬 CSV {r['조']}조 {kk}: 「찾은 글」 낱말")


# ───────────────────────────── ② A~C 조 번호·제목
def check_abc(R, M, MOBR, E16, E12, CSVS, MAP, QIDS, MDS):
    R.head("② A~C 조 번호·제목 = 조문목차 CSV·모범규준_조목록")

    def t(n, ed):
        r = MOBR.get(n)
        return (r["제목_2016.8.1판"] if ed == "16" else r["제목_2012.3.13제정판"]) if r else ""

    def others(title, n, ed):
        return [m for m in sorted(MOBR) if m != n and dn(t(m, ed)) == dn(title)]

    # A-1
    im_rows = [r for r in CSVS["iM금융지주"] if r["규정명"].startswith("리스크관리규정(")]
    body = [r for r in im_rows if re.fullmatch(r"제\d+조", r["조번호"])]
    i = find(M, lambda l: l.startswith("### A-1"), "A-1")
    hdr, data = table_at(M, i)
    if len(data) != len(body):
        R.bad(f"A-1 {len(data)}행 ≠ iM CSV 본칙 {len(body)}행")
    cls = {"16": {}, "12": {}, "any": {}}
    rank = {"번호·제목 일치": 0, "제목만 일치(번호 다름)": 1, "일치 없음": 2}
    for (ln, c), r in zip(data, body):
        n = int(re.findall(r"\d+", r["조번호"])[0])
        if c[1] != r["조번호"] or c[2] != cellf(r["조제목"]) or c[3] != r["쪽"]:
            R.bad(f"A-1 md {ln}행: 「{c[1]} {c[2]} {c[3]}」 ≠ iM CSV 「{r['조번호']} {r['조제목']} {r['쪽']}」")
        cat = {}
        for ed, bi, oi in (("16", 4, 5), ("12", 6, 7)):
            same = dn(r["조제목"]) == dn(t(n, ed))
            want = f"{n}조 {t(n, ed)} → " + ("**같음**" if same else "다름")
            if c[bi] != cellf(want):
                R.bad(f"A-1 md {ln}행 {ed}: 「{c[bi]}」 ≠ 다시 셈 「{want}」")
            o = others(r["조제목"], n, ed)
            wo = "·".join(f"{m}조({t(m, ed)})" for m in o) or "-"
            if c[oi] != cellf(wo):
                R.bad(f"A-1 md {ln}행 {ed} 같은 제목 다른 번호: 「{c[oi]}」 ≠ 「{wo}」")
            cat[ed] = "번호·제목 일치" if same else ("제목만 일치(번호 다름)" if o else "일치 없음")
            cls[ed][n] = cat[ed]
        un = sorted({lab for lab, tt in E16["units"] + E12["units"] if tt == dn(strip_ann(r["조제목"]))})
        if c[8] != (cellf(" / ".join(un)) or "-"):
            R.bad(f"A-1 md {ln}행 장·절: 「{c[8]}」 ≠ 「{' / '.join(un) or '-'}」")
        ca = min(cat.values(), key=lambda x: rank[x])
        cls["any"][n] = ca
        if c[9] != ca:
            R.bad(f"A-1 md {ln}행 분류 「{c[9]}」 ≠ 다시 셈 「{ca}」")
    R.p(f"  A-1 본칙 {len(data)}조 — 조 번호·제목·쪽 = iM CSV, 같은 번호 조 제목 = 조목록(2016.8.1·2012.3.13), 기계 비교 다시 셈")
    # A-2
    i = find(M, lambda l: l.startswith("### A-2"), "A-2")
    hdr, data = table_at(M, i)
    for (ln, c), key in zip(data, ("16", "12", "any")):
        for col, cat in ((1, "번호·제목 일치"), (2, "제목만 일치(번호 다름)")):
            xs = [n for n, v in cls[key].items() if v == cat]
            want = (f"{len(xs)}개 — " + ", ".join(f"제{x}조" for x in xs)) if xs else "0개"
            if c[col] != want:
                R.bad(f"A-2 md {ln}행 {key} {cat}: 「{c[col]}」 ≠ 「{want}」")
        none = sum(1 for v in cls[key].values() if v == "일치 없음")
        if c[3] != f"{none}개" or c[4] != str(len(cls[key])):
            R.bad(f"A-2 md {ln}행 {key}: 일치 없음 「{c[3]}」/합계 「{c[4]}」 ≠ {none}개/{len(cls[key])}")
    R.p("  A-2 통계 3행 다시 셈")
    # A-4 장
    chs = [r for r in im_rows if re.fullmatch(r"제\d+장", r["조번호"])]
    i = find(M, lambda l: l.startswith("### A-4"), "A-4")
    hdr, data = table_at(M, i)
    if len(data) != len(chs):
        R.bad(f"A-4 {len(data)}행 ≠ iM CSV 장 {len(chs)}행")
    for (ln, c), r in zip(data, chs):
        n = int(re.findall(r"\d+", r["조번호"])[0])
        if c[0] != r["조번호"] or c[1] != cellf(r["조제목"]) or c[2] != r["쪽"]:
            R.bad(f"A-4 md {ln}행: 「{c[0]} {c[1]} {c[2]}」 ≠ iM CSV 「{r['조번호']} {r['조제목']} {r['쪽']}」")
        for E, col in ((E16, 3), (E12, 4)):
            same = E["chs"].get(n)
            if same:
                want = f"제{n}장 {same} → " + ("같음" if dn(strip_ann(r["조제목"])) == dn(strip_ann(same)) else "다름")
                if c[col] != cellf(want):
                    R.bad(f"A-4 md {ln}행: 「{c[col]}」 ≠ 「{want}」")
            elif not c[col].startswith("같은 번호 장 찾지 못함"):
                R.bad(f"A-4 md {ln}행: 모범규준에 제{n}장이 없는데 「{c[col]}」")
    R.p(f"  A-4 장 {len(data)}행 = iM CSV, 같은 번호 장 제목 = 모범규준 원문 md 5·6장 장 머리 줄")
    # B 표
    L_m = MDS["메리츠금융지주"]
    cnt = {}
    for st, blk in code_blocks(L_m):
        for l in blk:
            m = re.search(r"그룹리스크관리규정\s*((?:제\s*\d+\s*조(?:\s*\d+\s*항)?[,\s]*)+)", l)
            if m:
                for jo, hg in re.findall(r"제\s*(\d+)\s*조(?:\s*(\d+)\s*항)?", m.group(1)):
                    key = (int(jo), int(hg) if hg else 0)
                    cnt[key] = cnt.get(key, 0) + 1
    mcsv = {}
    for r in CSVS["메리츠금융지주"]:
        if r["규정명"] == "그룹리스크관리규정":
            m = re.match(r"제(\d+)조(?:\s*제(\d+)항)?", r["조번호"])
            if m:
                mcsv[(int(m.group(1)), int(m.group(2)) if m.group(2) else 0)] = r
    i = find(M, lambda l: l.startswith("| 메리츠 인용(원문 표기)"), "B 표")
    hdr, data = table_at(M, i - 1)
    seen = []
    for ln, c in data:
        m = re.fullmatch(r"그룹리스크관리규정 제(\d+)조(?: (\d+)항)?", c[0])
        if not m:
            R.bad(f"B 표 md {ln}행 첫 칸 「{c[0]}」")
            continue
        key = (int(m.group(1)), int(m.group(2)) if m.group(2) else 0)
        seen.append(key)
        if key not in mcsv:
            R.bad(f"B 표 {c[0]}: 메리츠 조문목차 CSV 에 행 없음")
        k = int(re.match(r"(\d+)회", c[1]).group(1)) if re.match(r"(\d+)회", c[1]) else -1
        if k != cnt.get(key, 0):
            R.bad(f"B 표 {c[0]}: 인용 횟수 {k} ≠ 메리츠 md 코드 블록 다시 셈 {cnt.get(key, 0)}")
        want = f"{key[0]}조 {t(key[0], '16')} / {key[0]}조 {t(key[0], '12')}"
        if c[3] != cellf(want):
            R.bad(f"B 표 {c[0]}: 모범규준 제목 「{c[3]}」 ≠ 조목록 「{want}」")
    if sorted(seen) != sorted(cnt):
        R.bad(f"B 표 조 {sorted(seen)} ≠ 메리츠 md 인용 조 {sorted(cnt)}")
    for k2, l in enumerate(M):
        m = re.match(r"^### B-\S+ 메리츠 그룹리스크관리규정 .+ ↔ 모범규준 (.+)$", l)
        if m:
            for jo, tt in re.findall(r"제(\d+)조\(([^)]*)\)", m.group(1)):
                if tt != t(int(jo), "16"):
                    R.bad(f"md {k2 + 1}행 B 절 제목: 제{jo}조({tt}) ≠ 조목록 「{t(int(jo), '16')}」")
    R.p(f"  B 표 {len(data)}행 — 인용 조 = 메리츠 md 다시 셈 {dict(sorted(cnt.items()))}, 메리츠 CSV 행·조목록 제목 맞음")
    # C-1 상태
    i = find(M, lambda l: l.startswith("### C-1"), "C-1")
    hdr, data = table_at(M, i)
    for ln, c in data:
        co = c[0]
        if co not in MDS:
            R.bad(f"C-1 md {ln}행 회사 「{co}」")
            continue
        _, toc = directive(co, MDS[co])
        if c[3] != cellf(toc or "") or r1_kind(c[3]) is None:
            R.bad(f"C-1 {co}: 상태 「{c[3][:60]}」 ≠ 회사 md 「9-4 1.」 행 「{(toc or '')[:60]}」 또는 R1 아님")
    R.p(f"  C-1 {len(data)}개사 상태 칸 = 회사 md 「9-4 1.」 행 상태(R1)")
    # 조번호대조 CSV
    src = []
    for co in COS:
        for r in CSVS[co]:
            src.append((co, r))
    if len(src) != len(MAP):
        R.bad(f"조번호대조 CSV {len(MAP)}행 ≠ 조문목차 CSV 합 {len(src)}행")
    nm = 0
    for (co, r), x in zip(src, MAP):
        if (x["회사"], x["규정명"], x["회사_조"], x["회사_조제목(원문)"], x["쪽"], x["문서"], x["접수번호또는URL"]) != \
                (co, r["규정명"], r["조번호"], r["조제목"], r["쪽"], r["문서"], r["접수번호또는URL"]):
            R.bad(f"조번호대조 CSV 행 ≠ {co} 조문목차 CSV 행 「{r['규정명']} {r['조번호']}」")
            continue
        jd = r.get("비고") or r.get("닿는모범규준조(판단)") or ""
        if x["회사산출물_대응판단(그대로)"] != jd:
            R.bad(f"조번호대조 CSV {co} {r['조번호']}: 대응판단 칸 ≠ 조문목차 CSV")
        m = re.fullmatch(r"제(\d+)조", r["조번호"])
        if m and x["구분"] in ("조", "본칙 조"):
            n = int(m.group(1))
            for ed, a, b in (("16", "모범_같은번호_제목_2016.8.1", "기계비교_2016.8.1"), ("12", "모범_같은번호_제목_2012.3.13", "기계비교_2012.3.13")):
                if t(n, ed):
                    if x[a] != f"{n}조 {t(n, ed)}" or x[b] != ("같음" if dn(r["조제목"]) == dn(t(n, ed)) else "다름"):
                        R.bad(f"조번호대조 CSV {co} {r['조번호']}: {a}·{b} 「{x[a]} / {x[b]}」 다시 셈과 다름")
                elif not x[b].startswith("같은 번호 조 찾지 못함"):
                    R.bad(f"조번호대조 CSV {co} {r['조번호']}: 모범규준에 {n}조가 없는데 「{x[b]}」")
                o = "·".join(f"{mm}조" for mm in others(r["조제목"], n, ed))
                cc = "같은제목_다른번호_2016.8.1" if ed == "16" else "같은제목_다른번호_2012.3.13"
                if x[cc] != o:
                    R.bad(f"조번호대조 CSV {co} {r['조번호']}: {cc} 「{x[cc]}」 ≠ 「{o}」")
            nm += 1
        # R2 표지
        lab = x.get("모범규준_조_표지(R2)")
        mm = re.match(r"제(\d+)조", r["조번호"])
        n = int(mm.group(1)) if mm else None
        if co == "iM금융지주" and r["규정명"].startswith("리스크관리규정(") and re.fullmatch(r"제\d+조", r["조번호"]) and n in (28, 30):
            want = f"{TOCLAB} — {n}조({t(n, '16')})(지시서 9-4 1. 조 번호 그대로)"
        elif co == "메리츠금융지주" and r["규정명"] == "그룹리스크관리규정" and n:
            want = f"{TOCLAB} — {n}조({t(n, '16')})" + ("(지시서 9-4 1. 조 번호 그대로)" if n in (9, 57) else "(판단)")
        else:
            want = TOCLAB
        if lab != want:
            R.bad(f"조번호대조 CSV {co} {r['조번호']}: R2 표지 「{lab}」 ≠ 「{want}」")
    R.p(f"  조번호대조 CSV {len(MAP)}행 = 조문목차 CSV 합 {len(src)}행(회사·규정명·조번호·조제목·쪽·문서·접수번호·비고), 조 행 {nm}개 기계 비교 다시 셈, R2 표지 열")
    # C-3
    by = {}
    for x in MAP:
        if x["구분"] not in ("조", "본칙 조", "조(「제N조의M」 꼴)", "인용 조·항 — 조 제목 추출 범위에 없음(기계 비교 불가)"):
            continue
        k = (x["회사"], x["규정명"])
        s = by.setdefault(k, {"n": 0, "s16": [], "s12": [], "none": 0, "na": 0})
        s["n"] += 1
        if x["구분"].startswith("인용 조·항"):
            s["na"] += 1
            continue
        hit = False
        for ed in ("16", "12"):
            col = "기계비교_2016.8.1" if ed == "16" else "기계비교_2012.3.13"
            if x[col] == "같음":
                s["s" + ed].append(f"{x['회사_조']}({x['회사_조제목(원문)']})")
                hit = True
        if (x["같은제목_다른번호_2016.8.1"] and x["기계비교_2016.8.1"] != "같음") or (x["같은제목_다른번호_2012.3.13"] and x["기계비교_2012.3.13"] != "같음"):
            hit = True
        if not hit:
            s["none"] += 1
    i = find(M, lambda l: l.startswith("### C-3"), "C-3")
    hdr, data = table_at(M, i)
    n3 = 0
    for ln, c in data:
        co = next((x for x in COS if SHORT[x] == c[0]), None)
        s = by.get((co, c[1].replace("／", "|")))
        if not s:
            R.bad(f"C-3 md {ln}행: 조번호대조 CSV 에 「{c[0]} {c[1]}」 없음")
            continue
        n3 += 1
        want = [str(s["n"]), ", ".join(s["s16"]) or "0", ", ".join(s["s12"]) or "0", str(s["none"]), str(s["na"])]
        got = [c[2], c[3], c[4], c[6], c[7]]
        if [cellf(w) for w in want] != got:
            R.bad(f"C-3 md {ln}행 {c[0]} {c[1]}: {got} ≠ 다시 셈 {want}")
    R.p(f"  C-3 {n3}행 = 조번호대조 CSV 다시 셈")


# ───────────────────────────── ③ 원문 인용
def raw_pages(co, src):
    """출처 줄의 문서·쪽 → 원본 텍스트(dart_out/text/risk8) 그 쪽 글(앞뒤 1쪽 포함)."""
    m = re.search(r"· p\.(\d+)(?:~(\d+))?", src)
    if not m or "연차보고서" not in src:
        return None
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "dart_out", "text", "risk8", f"연차보고서__{co}_지배구조연차보고서_2026*.txt"))):
        with open(f, encoding="utf-8", errors="ignore") as fh:
            txt = fh.read()
        parts = re.split(r"^=== p\.(\d+) ===$", txt, flags=re.M)
        for k in range(1, len(parts) - 1, 2):
            if a - 1 <= int(parts[k]) <= b + 1:
                out.append(parts[k + 1])
    return nows("\n".join(out)) if out else None


def check_quotes(R, M, MDS, MOBT):
    R.head("③ 원문 인용 글자 그대로(공백 무시)")
    LAB = {"iM": "iM금융지주", "메리츠": "메리츠금융지주", "한국투자": "한국투자금융지주"}
    ctext = {co: nows(code_text(L)) for co, L in MDS.items()}
    mob = nows(MOBT)
    label, src = None, ""
    n_blk = n_line = n_raw = n_raw_try = 0
    on = False
    for k, l in enumerate(M):
        m = re.match(r"^- 인용\(([^)]*)\)", l)
        if m and not on:
            label, src = m.group(1), l
            continue
        if l.startswith("```"):
            on = not on
            if on:
                n_blk += 1
                if label is None:
                    R.bad(f"md {k + 1}행 코드 블록 앞에 「- 인용(…)」 출처 줄 없음(R4)")
            continue
        if not on or not l.strip() or l.startswith("[줄임:"):
            continue
        n_line += 1
        w = nows(l)
        if label and label.startswith("모범규준"):
            if w not in mob:
                R.bad(f"md {k + 1}행: 모범규준 원문 md 코드 블록에서 찾지 못함 — 「{l.strip()[:60]}」")
            continue
        co = LAB.get(label)
        if not co:
            R.bad(f"md {k + 1}행: 출처 라벨 「{label}」 을 모름")
            continue
        raw = raw_pages(co, src)
        okraw = None
        if raw is not None:
            n_raw_try += 1
            okraw = w in raw
            n_raw += 1 if okraw else 0
        if w not in ctext[co] and not okraw:
            R.bad(f"md {k + 1}행: {co} md 인용 블록·원본 텍스트 쪽에서 찾지 못함 — 「{l.strip()[:60]}」")
    R.p(f"  코드 블록 {n_blk}개·줄 {n_line}개 — 회사 md·모범규준 원문 md 대조; 회사 인용 줄 가운데 원본 텍스트 쪽(risk8)에서도 찾은 줄 {n_raw}/{n_raw_try}(참고)")
    # B 표 「」 발췌
    i = find(M, lambda l: l.startswith("| 메리츠 인용(원문 표기)"), "B 표")
    hdr, data = table_at(M, i - 1)
    nq = 0
    for ln, c in data:
        for col, base, what in ((2, ctext["메리츠금융지주"], "메리츠 md"), (4, mob, "모범규준 원문 md"), (5, mob, "모범규준 원문 md")):
            for q in re.findall(r"「(.+?)」(?= / |$| 외 )", c[col]):
                nq += 1
                if nows(q) not in base:
                    R.bad(f"B 표 md {ln}행 칸 {col + 1}: 「{q[:50]}」 를 {what}에서 찾지 못함")
    R.p(f"  B 표 「」 발췌 {nq}개 — 메리츠 md·모범규준 원문 md 대조")


# ───────────────────────────── ④ 입력 sha256
def check_inputs(R, M):
    R.head("④ 입력 sha256 = 지금 파일")
    i = find(M, lambda l: l.startswith("### 입력 파일"), "입력 파일 표")
    hdr, data = table_at(M, i)
    want = {MOB_MD, MOB_CSV} | set(STATE) | {csv_rel(c) for c in COS} | {md_rel(c) for c in COS}
    got = {}
    for ln, c in data:
        m1, m2 = re.fullmatch(r"`([^`]+)`", c[0]), re.fullmatch(r"`([0-9a-f]{64})`", c[1])
        if not (m1 and m2):
            R.bad(f"입력 표 md {ln}행 꼴(경로·64자 sha256) 아님")
            continue
        got[m1.group(1)] = m2.group(1)
    if set(got) != want:
        R.bad(f"입력 목록 다름 — 빠짐 {sorted(want - set(got))}, 더 있음 {sorted(set(got) - want)}")
    same = 0
    for rel, h in got.items():
        if not os.path.exists(os.path.join(ROOT, rel)):
            R.bad(f"{rel}: 파일 없음")
        elif sha(rel) != h:
            R.bad(f"{rel}: sha256 다름(기록 {h[:16]}… / 지금 {sha(rel)[:16]}…)")
        else:
            same += 1
    R.p(f"  입력 {len(got)}개 가운데 sha256 같음 {same}")


# ───────────────────────────── ⑤ 키·OC
def secret_values():
    vals = []
    for k in SECRET_KEYS:
        v = os.environ.get(k, "").strip()
        if len(v) >= 6:
            vals.append(v)
    envp = os.path.join(ROOT, ".env")
    if os.path.exists(envp):
        with open(envp, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if "=" in ln and not ln.lstrip().startswith("#"):
                    k, v = ln.split("=", 1)
                    v = v.strip().strip('"').strip("'")
                    if k.strip() in SECRET_KEYS and len(v) >= 6:
                        vals.append(v)
    return sorted(set(vals))


def check_secrets(R, extra_txt):
    R.head("⑤ API 키·OC 문자열 없음")
    vals = secret_values()
    files = [OUT_MD, OUT_MATRIX, OUT_MAP, "scripts/dart/web13_compare.py", "scripts/dart/verify13_compare.py"]
    files += [os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, RAW_DIR, "*")) if os.path.isfile(f)]
    n = 0
    for rel in files + ["(이 결과 txt)"]:
        if rel == "(이 결과 txt)":
            s = extra_txt
        else:
            with open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore") as f:
                s = f.read()
        n += 1
        for v in vals:
            if v in s:
                R.bad(f"{rel}: 인증값 문자열이 들어 있음(값은 찍지 않음)")
        if re.search(r"crtfc_key=(?!\*)[A-Za-z0-9]", s):
            R.bad(f"{rel}: 가리지 않은 「crtfc_key=」 꼴")
        if re.search(r"(?<![A-Za-z_])OC=(?!\*\*\*)[A-Za-z0-9]", s):
            R.bad(f"{rel}: 가리지 않은 「OC=」 꼴")
    R.p(f"  인증값 후보 {len(vals)}개(값은 찍지 않음)로 {n}개 파일·글 확인")


# ───────────────────────────── ⑥ 낱말·절
R3_BEFORE = ["같은 번호 장 없음", "같은 번호 조 없음", "⑤항 줄 없음", "새로 받은 자료 없음", "6개사 모두 할 수 없음", "요약 표 행 없음"]
OK_NONE = [r"추출 범위에 없음", r"일치 없음", r"「없음」"]


def check_words(R, M, MDS):
    R.head("⑥ R5·R3·R2 낱말과 검증 기록 절")
    fk0 = next((k for k, l in enumerate(M) if l.strip() == "### 정합성 보정(2026-10-08)"), len(M))
    if any("작성일: 2026-10-07" in l for l in M[:fk0]):     # 정합성 보정 소절의 「전」 칸은 1차 판 글
        R.bad("「작성일: 2026-10-07」 라벨이 남아 있음(R5)")
    head = next((l for l in M if l.startswith("- 작성일:")), "")
    if not head.startswith("- 작성일: 2026-10-08(KST)"):
        R.bad(f"작성일 라벨이 KST 꼴이 아님 — 「{head[:60]}」")
    h2 = [k for k, l in enumerate(M) if l.startswith("## ")]
    vk = [k for k in h2 if M[k].strip() == "## 검증 기록"]
    if len(vk) != 1 or h2[-1] != vk[0]:
        R.bad("「## 검증 기록」 절이 하나가 아니거나 끝 절이 아님")
        return
    fk = [k for k, l in enumerate(M) if l.strip() == "### 정합성 보정(2026-10-08)"]
    if len(fk) != 1 or fk[0] < vk[0]:
        R.bad("「### 정합성 보정(2026-10-08)」 소절이 검증 기록 절 안에 하나가 아님")
        return
    # R3 — 코드 블록·정합성 보정 소절 밖
    on, n_none, bad = False, 0, 0
    for k, l in enumerate(M[:fk[0]]):
        if l.startswith("```"):
            on = not on
            continue
        if on:
            continue
        for a in R3_BEFORE:
            if a in l:
                R.bad(f"md {k + 1}행: R3 「전」 낱말 「{a}」 이 남아 있음")
        s = l
        for pat in OK_NONE:
            s = re.sub(pat, "", s)
        # 회사 md 의 「9-4 1.」 행을 그대로 옮긴 C-1 칸·원문 인용 「」 안은 원문·회사 md 글
        s = re.sub(r"「[^」]*」", "", s)
        k2 = s.count("없음")
        n_none += l.count("없음")
        if k2:
            bad += k2
            R.bad(f"md {k + 1}행: 허용 꼴 밖 「없음」 {k2}곳 — 「{l[:90]}」")
    R.p(f"  코드 블록·정합성 보정 소절 밖 「없음」 {n_none}곳 — 허용 꼴(추출 범위에 없음·일치 없음·「없음」·인용 「」 안) 밖 {bad}")
    # R2 — 회사 인용 태그 줄
    LAB = {"iM": "iM금융지주", "메리츠": "메리츠금융지주", "한국투자": "한국투자금융지주"}
    label, nt = None, 0
    for k, l in enumerate(M):
        m = re.match(r"^- 인용\(([^)]*)\)", l)
        if m:
            label = m.group(1)
            continue
        if not l.startswith("- 이 글이 닿는 모범규준 조") or not label or label.startswith("모범규준"):
            continue
        nt += 1
        co = LAB.get(label)
        if "9-4 조문 대조(대조표 " not in l:
            R.bad(f"md {k + 1}행: 태그 줄에 「9-4 조문 대조(대조표 …)」 표지 없음(R2)")
        listed = set(LISTED_ALL) | set(DIR941.get(co, ("", []))[1])
        body = l.split(" — ", 1)[1] if " — " in l else l
        toks = re.findall(r"(\d+)조\(([^()]+)\)((?:\([^()]*\))?)", body)
        if not toks and "(판단)" not in body:
            R.bad(f"md {k + 1}행: 조 번호 없는 태그 줄에 (판단) 없음")
        for n, tt, suf in toks:
            n = int(n)
            if n in listed and "판단" in suf:
                R.bad(f"md {k + 1}행: 지시서 조 {n}조에 (판단)(R2)")
            if n not in listed and "판단" not in suf:
                R.bad(f"md {k + 1}행: 지시서 밖 조 {n}조에 (판단) 없음(R2)")
    R.p(f"  회사 인용 태그 줄 {nt}개 R2 확인")


# ───────────────────────────── main
def main():
    os.chdir(ROOT)
    R = Rep()
    R.p("# verify13_compare — 9-4 모범규준 대조표 대조 결과")
    R.p(f"대상: {OUT_MD}, {OUT_MATRIX}, {OUT_MAP} (web13_compare.py 산출물 — 읽기만)")
    M = rd(OUT_MD).split("\n")
    mat = rcsv(OUT_MATRIX)
    MAP = rcsv(OUT_MAP)
    MOBR = {int(r["조"]): r for r in rcsv(MOB_CSV)}
    MOBL = rd(MOB_MD).split("\n")
    E16, E12 = mob_parse(MOBL, "## 5."), mob_parse(MOBL, "## 6.")
    MOBT = code_text(MOBL)
    for ed, E, col in (("2016.8.1", E16, "제목_2016.8.1판"), ("2012.3.13", E12, "제목_2012.3.13제정판")):
        diff = [n for n in MOBR if E["arts"].get(n) is None or dn(E["arts"][n]) != dn(MOBR[n][col])]
        if diff:
            R.probs.append(f"[준비] 조목록 CSV {ed} 제목 ↔ 원문 md 조 머리 다름 {diff}")
    ST = {}
    for rel in STATE:
        for r in rcsv(rel):
            ST[(r["회사"], int(r["모범규준_조"]))] = r
    MDS, CSVS, S0, DT, QIDS = {}, {}, {}, {}, {}
    for co in COS:
        MDS[co] = rd(md_rel(co)).split("\n")
        CSVS[co] = rcsv(csv_rel(co))
        S0[co] = sec0(MDS[co])
        DT[co], _ = directive(co, MDS[co])
        QIDS[co] = quote_ids(MDS[co])
    R.p(f"입력: 상태 CSV {len(ST)}칸, 회사 md 8개(인용 머리 {sum(len(v) for v in QIDS.values())}개), 조문목차 CSV {sum(len(v) for v in CSVS.values())}행, 조목록 {len(MOBR)}조")
    check_d(R, M, mat, ST, S0, DT, QIDS, MOBR)
    check_abc(R, M, MOBR, E16, E12, CSVS, MAP, QIDS, MDS)
    check_quotes(R, M, MDS, MOBT)
    check_inputs(R, M)
    check_words(R, M, MDS)
    check_secrets(R, "\n".join(R.lines))
    R.head("결과")
    R.p(f"문제 {len(R.probs)}건" + (" — exit 1" if R.probs else " — exit 0"))
    for x in R.probs:
        R.p(f"  ✗ {x}")
    with open(os.path.join(ROOT, OUT_TXT), "w", encoding="utf-8") as f:
        f.write("\n".join(R.lines) + "\n")
    print(f"verify13_compare: 문제 {len(R.probs)}건 → {OUT_TXT}")
    for x in R.probs[:25]:
        print("  ✗", x[:200])
    return 1 if R.probs else 0


if __name__ == "__main__":
    sys.exit(main())
