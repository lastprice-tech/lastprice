#!/usr/bin/env python3
"""14차 그룹 g1(KB금융지주·신한금융지주) 검증 — 인자 없이 실행, 결과 dart_out/org14/verify14_g1.txt, exit 0(통과)/1(문제).

대조 항목
 1. md 인용 블록(「> 」 줄) ↔ 인용 뒤 출처 줄이 가리키는 텍스트 파일 줄(공백만 무시) · 그 줄이 적힌 쪽 안에 있는지 ·
    「추가공시 텍스트와 같음」 이라 적은 인용은 추가공시 텍스트에도 있는지
 2. md 표(임원·겸직·지원조직·내부회계·직원 표) 칸 글 ↔ 사업보고서 텍스트 그 쪽(공백 무시)
 3. CSV(임원겸직·지원조직·조직단위의 인원 칸·대응 근거·임원 겸직 칸) 원문 칸 ↔ 텍스트 그 쪽
 4. md 「…」 짧은 인용 ↔ 원문 텍스트(같은 회사 문서 전체, 공백 무시). 판독·판단 글은 따로 셈
 5. 대응 방식 「이름 일치」 ↔ 담당업무 원문에 단위 이름이 글자 그대로 있는지(기계 확인)
 6. CSV ↔ md 같은 값(조직도 판독 표·임원 표·지원조직 표·인원 연결 표)
 7. 판독대조 CSV: 판독B 칸 = 판독B JSON, 확정 칸 = 조직단위 CSV, 확정·확정 방법 칸 빈칸 없음, 머리 집계 글 ↔ 확정 단위 수
 8. 인증값(DART_API_KEY·LAW_OC 등) 문자열 없음, 산출 폴더(dart_out/org14·handoff/14차_조직인원겸직)에 PDF·PNG 없음
웹 요청 없음. 원본 파일은 읽기만 함.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TXT = os.path.join(ROOT, "dart_out", "text", "risk8")
OUTD = os.path.join(ROOT, "dart_out", "org14")
MDD = os.path.join(ROOT, "handoff", "14차_조직인원겸직")
REPORT = os.path.join(OUTD, "verify14_g1.txt")
KST = timezone(timedelta(hours=9))

COS = {
    "KB금융지주": {"id": "K", "biz": "20260313001191", "corr": ["20260324000835", "20260619000667"]},
    "신한금융지주": {"id": "S", "biz": "20260318000826", "corr": []},
}


def nows(s):
    return re.sub(r"\s+", "", (s or "").replace("\\|", "|").replace("<br>", ""))


# ───────────────────────────── 텍스트 ─────────────────────────────
class Doc:
    def __init__(self, path):
        self.path = path
        self.lines = open(path, encoding="utf-8").read().split("\n")
        self.page_of = []
        pg = 0
        self.pages = {}
        for ln in self.lines:
            m = re.match(r"^=== p\.(\d+) ===$", ln.strip())
            if m:
                pg = int(m.group(1))
            self.page_of.append(pg)
            if not m:
                self.pages.setdefault(pg, []).append(ln)
        self.pnorm = {p: nows("".join(v)) for p, v in self.pages.items()}
        self.all = nows("".join(ln for ln in self.lines if not ln.startswith("=== p.")))

    def pages_text(self, p0, p1=None):
        p1 = p0 if p1 is None else p1
        return "".join(self.pnorm.get(p, "") for p in range(p0, p1 + 1))


DOCS = {}


def doc(name):
    if name not in DOCS:
        DOCS[name] = Doc(os.path.join(TXT, name))
    return DOCS[name]


def files_of(co):
    c = COS[co]
    return {
        "biz": f"사업보고서__{co}__{c['biz']}.txt",
        "ann": f"연차보고서__{co}_지배구조연차보고서_2026.txt",
        "ann2": f"연차보고서__{co}_지배구조연차보고서_2026_추가공시.txt",
        "mgmt": f"경영공시__{co}.txt",
        "corr": [f"사업보고서__{co}__{n}.txt" for n in c["corr"]],
    }


def file_for_citation(co, cit):
    f = files_of(co)
    if "추가공시" in cit and "연차보고서" in cit:
        return f["ann2"]
    if "연차보고서" in cit:
        return f["ann"]
    if "경영공시" in cit:
        return f["mgmt"]
    if "사업보고서" in cit:
        for n in COS[co]["corr"]:
            if n in cit:
                return f"사업보고서__{co}__{n}.txt"
        return f["biz"]
    return None


def pages_in(cit):
    m = re.search(r"p\.(\d+)(?:~(\d+))?", cit)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2) or m.group(1))


# ───────────────────────────── 결과 모음 ─────────────────────────────
PROBS = []
INFO = []
COUNT = {}


def prob(where, what):
    PROBS.append((where, what))


def cnt(k, n=1):
    COUNT[k] = COUNT.get(k, 0) + n


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def md_lines(co):
    return open(os.path.join(MDD, f"14_{co}.md"), encoding="utf-8").read().split("\n")


# ───────────────────────────── 1. 인용 블록 ─────────────────────────────
CIT_RE = re.compile(r"dart_out/text/risk8/(\S+?\.txt) ([0-9~,]+)행")


def check_blockquotes(co):
    L = md_lines(co)
    f = files_of(co)
    i = 0
    while i < len(L):
        if L[i].startswith(">") and not L[i].startswith("> 「(판단)」 표시가 없는 글은"):
            j = i
            while j < len(L) and L[j].startswith(">"):
                j += 1
            block = [re.sub(r"^>\s?", "", x) for x in L[i:j]]
            cit = None
            for k in range(j, min(j + 4, len(L))):
                if CIT_RE.search(L[k]):
                    cit = L[k]
                    break
                if L[k].startswith(">") or L[k].startswith("#"):
                    break
            where = f"{co} md {i + 1}~{j}줄"
            if not cit:
                prob(where, "인용 블록 뒤 출처 줄(텍스트 파일·행)이 없음")
                i = j
                continue
            m = CIT_RE.search(cit)
            d = doc(m.group(1))
            rng = []
            for part in m.group(2).split(","):
                a, _, b = part.partition("~")
                rng.extend(range(int(a), int(b or a) + 1))
            src = nows("".join(d.lines[n - 1] for n in rng if 0 < n <= len(d.lines)))
            q = nows("".join(block))
            cnt("인용블록")
            if q not in src:
                # 줄 하나씩 찾아 어느 줄이 다른지 알려 줌
                bad = [x for x in block if nows(x) and nows(x) not in src]
                prob(where, f"인용이 {m.group(1)} {m.group(2)}행과 다름(공백 무시) — 다른 줄: {bad[:3]}")
            pr = pages_in(cit)
            if pr:
                pgs = {d.page_of[n - 1] for n in rng if 0 < n <= len(d.lines)}
                if not pgs or not all(pr[0] <= p <= pr[1] for p in pgs):
                    prob(where, f"쪽 표기 p.{pr[0]}~{pr[1]} ↔ 인용 행의 쪽 {sorted(pgs)}")
            else:
                prob(where, "출처 줄에 쪽(p.N) 없음")
            if "추가공시 텍스트와 같음" in cit:
                cnt("추가공시 같음 주장")
                miss = [x for x in block if nows(x) and nows(x) not in doc(f["ann2"]).all]
                if miss:
                    prob(where, f"「추가공시 텍스트와 같음」 이라 했으나 추가공시 텍스트에서 찾지 못한 줄: {miss[:3]}")
            i = j
        else:
            i += 1


# ───────────────────────────── 2. md 표 ─────────────────────────────
def split_row(line):
    """md 표 한 줄을 칸으로 — 백틱(`) 안과 「\\|」 는 칸 구분으로 보지 않음."""
    out, cur, code, k = [], "", False, 0
    while k < len(line):
        ch = line[k]
        if ch == "\\" and k + 1 < len(line) and line[k + 1] == "|":
            cur += "\\|"
            k += 2
            continue
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            out.append(cur)
            cur = ""
        else:
            cur += ch
        k += 1
    out.append(cur)
    return out


def md_table_rows(L, start, header_prefix):
    """start 이후 첫 표(header_prefix 로 시작하는 머리)의 행들을 (줄번호, 칸 목록)으로."""
    rows = []
    i = start
    while i < len(L) and not L[i].startswith(header_prefix):
        i += 1
    if i >= len(L):
        return rows, i
    i += 2
    while i < len(L) and L[i].startswith("|"):
        cells = [c.strip() for c in split_row(L[i])[1:-1]]
        rows.append((i + 1, cells))
        i += 1
    return rows, i


def find_heads(L, pat):
    return [i for i, x in enumerate(L) if re.match(pat, x)]


def in_page(d, text, p, slack=1):
    t = nows(text)
    if not t:
        return True
    if t in d.pnorm.get(p, ""):
        return "p"
    if t in d.pages_text(max(1, p - slack), p + slack):
        return "pm"
    return False


def check_md_tables(co, exec_md, conc_md):
    L = md_lines(co)
    f = files_of(co)
    biz = doc(f["biz"])
    # 임원 표
    for h in find_heads(L, r"^### .*임원.*현황 \(기준일"):
        if "겸직" in L[h]:
            continue
        rows, _ = md_table_rows(L, h, "| 성명 | 직위 |")
        for ln, c in rows:
            name, pos, reg, ft, duty, pg, units, ways = c[:8]
            p = int(pg.replace("p.", ""))
            cnt("md 임원 행")
            for lab, val in (("성명", name), ("직위", pos), ("담당업무", duty)):
                r = in_page(biz, val, p)
                if not r:
                    prob(f"{co} md {ln}줄", f"임원 표 {lab} 「{val}」 가 사업보고서 p.{p}(±1)에 없음")
            exec_md.append((L[h], name, pos, reg, ft, duty, units.split("<br>"), ways.split("<br>")))
            check_name_match(f"{co} md {ln}줄", duty, pos, units.split("<br>"), ways.split("<br>"))
    # 겸직 표
    for h in find_heads(L, r"^### .*겸직.*현황.*\(기준일"):
        rows, _ = md_table_rows(L, h, "| 성명 | 대상 회사 |")
        for ln, c in rows:
            p = int(c[5].replace("p.", ""))
            raw = re.sub(r"^`|`$", "", c[6]).replace("\\|", "|")
            cells = [x.strip() for x in raw.split(" | ")]
            cnt("md 겸직 행")
            r = in_page(biz, "".join(cells), p)
            if not r:
                bad = [x for x in cells if not in_page(biz, x, p)]
                if bad:
                    prob(f"{co} md {ln}줄", f"겸직 행 칸 {bad} 가 p.{p}(±1)에 없음")
                else:
                    INFO.append(f"{co} md {ln}줄 겸직 행: 칸은 모두 p.{p} 에 있으나 이어 붙인 글로는 없음(PDF 줄 꺾임)")
            conc_md.append((L[h], c[0].replace(" (합친 칸)", ""), cells[-4:]))
    # 지원조직 표 3-1
    for h in find_heads(L, r"^### 3-1 "):
        rows, _ = md_table_rows(L, h, "| 조직 종류 |")
        for ln, c in rows:
            p = int(c[5].replace("p.", ""))
            cnt("md 지원조직 행")
            for lab, val in (("부서명", c[1]), ("직원수", c[2]), ("직위", c[3]), ("주요 활동", c[4])):
                for part in val.split("<br>"):
                    if not in_page(biz, part, p):
                        prob(f"{co} md {ln}줄", f"지원조직 표 {lab} 「{part[:40]}」 가 p.{p}(±1)에 없음")
    # 내부회계 표 3-3
    for h in find_heads(L, r"^### 3-3 "):
        rows, _ = md_table_rows(L, h, "| 소속기관 또는 부서 |")
        for ln, c in rows:
            p = int(c[6].replace("p.", ""))
            cnt("md 내부회계 행")
            if not in_page(biz, "".join(c[:6]), p):
                bad = [x for x in c[:6] if not in_page(biz, x, p)]
                if bad:
                    prob(f"{co} md {ln}줄", f"내부회계 표 칸 {bad} 가 p.{p}(±1)에 없음")
    # 직원 표·미등기임원 표(백틱 행)
    for i, x in enumerate(L):
        if x.startswith("  - `") or x.startswith("**미등기임원 보수 현황 표**"):
            segs = re.findall(r"`([^`]+)`", x)
            # 쪽은 위쪽 「기준일 글」 줄 또는 아래 출처 줄
            near = " ".join(L[max(0, i - 8): i + 12])
            m = re.search(r"%s · p\.(\d+)" % COS[co]["biz"], near)
            if not m:
                continue
            p = int(m.group(1))
            for s in segs:
                for cell in s.split(" | "):
                    cnt("md 직원표 칸")
                    if not in_page(biz, cell, p, slack=2):
                        prob(f"{co} md {i + 1}줄", f"직원·미등기임원 표 칸 「{cell}」 가 p.{p}(±2)에 없음")


def check_name_match(where, duty, pos, units, ways):
    for u, w in zip(units, ways):
        cnt("대응 칸")
        if w.startswith("이름 일치"):
            cnt("이름 일치 주장")
            if u not in duty:
                prob(where, f"대응 「이름 일치」 인데 담당업무 「{duty}」 에 단위 이름 「{u}」 가 글자 그대로 없음")
        elif "(판단)" not in w and "대응 단위 없음" not in w and "추출 범위에 없음" not in w:
            prob(where, f"대응 방식 「{w[:40]}」 에 (판단)·이름 일치 표시가 없음")


# ───────────────────────────── 3. CSV 원문 칸 ─────────────────────────────
def check_csv_sources(co):
    f = files_of(co)
    biz = doc(f["biz"])
    rows = read_csv(os.path.join(OUTD, f"{co}_임원겸직.csv"))
    for k, r in enumerate(rows, 2):
        cnt("임원겸직 CSV 행")
        m = re.search(r"p\.(\d+)", r["출처(문서·접수번호·쪽)"])
        p = int(m.group(1))
        only_conc = r["담당업무(원문)"] == "임원 표에 나오지 않음"
        for lab in ("성명",) + (() if only_conc else ("담당업무(원문)",)):
            if not in_page(biz, r[lab], p):
                prob(f"{co}_임원겸직.csv {k}행", f"{lab} 「{r[lab]}」 가 p.{p}(±1)에 없음")
        us = [re.sub(r"\([KS]\d+\)$", "", x) for x in r["대응_조직단위"].split("; ")]
        ws = re.split(r"; (?=이름 일치|\(판단\)|추출 범위에 없음|대응 단위 없음)", r["대응_방식"])
        if len(us) != len(ws):
            prob(f"{co}_임원겸직.csv {k}행", f"대응_조직단위 {len(us)}개 ↔ 대응_방식 {len(ws)}개")
        for uu, w in zip(us, ws):
            if w.startswith("이름 일치"):
                cnt("이름 일치 주장")
                if uu not in r["담당업무(원문)"] or w != f"이름 일치: {uu}":
                    prob(f"{co}_임원겸직.csv {k}행", f"「{w}」 인데 담당업무 「{r['담당업무(원문)']}」 에 단위 「{uu}」 가 글자 그대로 없음")
            elif "(판단)" not in w and "추출 범위에 없음" not in w:
                prob(f"{co}_임원겸직.csv {k}행", f"대응_방식 「{w[:40]}」 에 (판단)·이름 일치 표시 없음")
        mm = re.search(r"겸직: p\.(\d+)", r["출처(문서·접수번호·쪽)"]) or (re.search(r"p\.(\d+)", r["출처(문서·접수번호·쪽)"]) if only_conc else None)
        if mm and r["겸직회사"] and "나오지 않음" not in r["겸직회사"]:
            q = int(mm.group(1))
            for lab in ("겸직회사", "겸직회사_직위", "선임일", "상근여부"):
                if not in_page(biz, r[lab], q):
                    prob(f"{co}_임원겸직.csv {k}행", f"{lab} 「{r[lab]}」 가 겸직 표 p.{q}(±1)에 없음")
    rows = read_csv(os.path.join(OUTD, f"{co}_지원조직.csv"))
    for k, r in enumerate(rows, 2):
        cnt("지원조직 CSV 행")
        cit = r["출처"]
        fn = file_for_citation(co, cit)
        pr = pages_in(cit)
        if not fn or not pr:
            prob(f"{co}_지원조직.csv {k}행", "출처에서 문서·쪽을 읽지 못함")
            continue
        d = doc(fn)
        for lab in ("부서(팀)명", "직원수", "직위(근속연수)", "주요 활동"):
            v = r[lab]
            if "추출 범위에 없음" in v or "(판단)" in v:
                continue
            parts = [re.sub(r"^총원 ", "", x) for x in re.split(r"\n| · ", v)]
            for part in parts:
                part = re.sub(r"^(내부회계담당인력수\(A\)|공인회계사자격증소지자수\(B\)|비율\(B/A\*100\)|내부회계담당인력의평균경력월수) ", "", part)
                if part and not in_page(d, part, pr[0], slack=max(1, pr[1] - pr[0] + 1)):
                    prob(f"{co}_지원조직.csv {k}행", f"{lab} 「{part[:50]}」 가 {fn} p.{pr[0]}~{pr[1]}(±1)에 없음")
    rows = read_csv(os.path.join(OUTD, f"{co}_조직단위.csv"))
    for k, r in enumerate(rows, 2):
        cnt("조직단위 CSV 행")
        det = r["인원_내역(원문)"]
        if det:
            srcs = r["인원_출처"].split("\n")
            dl = det.split("\n")
            if len(srcs) != len(dl):
                prob(f"{co}_조직단위.csv {k}행", f"인원_내역 줄 수 {len(dl)} ↔ 인원_출처 줄 수 {len(srcs)}")
            for x, s in zip(dl, srcs):
                fn, pr = file_for_citation(co, s), pages_in(s)
                if not fn or not pr:
                    prob(f"{co}_조직단위.csv {k}행", f"인원_출처 「{s[:40]}」 에서 문서·쪽을 읽지 못함")
                    continue
                d = doc(fn)
                for part in x.split(" | "):
                    part = re.sub(r"^(총원|내부회계담당인력수\(A\)) ", "", part)
                    cnt("조직단위 인원 칸")
                    if not in_page(d, part, pr[0], slack=1):
                        prob(f"{co}_조직단위.csv {k}행", f"인원_내역 「{part[:50]}」 가 {fn} p.{pr[0]}(±1)에 없음")
            hc = r["공시인원(원문, 없으면 「추출 범위에 없음」)"].split("\n")
            if len(hc) != len(srcs):
                prob(f"{co}_조직단위.csv {k}행", f"공시인원 줄 수 {len(hc)} ↔ 인원_출처 줄 수 {len(srcs)}")
            for x, s in zip(hc, srcs):
                fn, pr = file_for_citation(co, s), pages_in(s)
                if x == "추출 범위에 없음" or not fn or not pr:
                    continue
                cnt("조직단위 공시인원 칸")
                if not in_page(doc(fn), re.sub(r"^총원 ", "", x), pr[0], slack=1):
                    prob(f"{co}_조직단위.csv {k}행", f"공시인원 「{x}」 가 {fn} p.{pr[0]}(±1)에 없음")
        for x in r["대응_근거(담당업무 원문)"].split("\n"):
            m = re.match(r"\[\(기준일[^\]]*\)\] (\S+): (.*) \(p\.(\d+)\)$", x)
            if x and not m:
                prob(f"{co}_조직단위.csv {k}행", f"대응_근거 꼴을 읽지 못함 「{x[:40]}」")
            if m:
                cnt("조직단위 대응근거")
                if not in_page(biz, m.group(2), int(m.group(3))):
                    prob(f"{co}_조직단위.csv {k}행", f"대응_근거 담당업무 「{m.group(2)}」 가 p.{m.group(3)}(±1)에 없음")
        ways = r["대응_방식(이름 일치/(판단)/추출 범위에 없음)"].split("\n")
        duties = r["대응_근거(담당업무 원문)"].split("\n")
        for w, du in zip(ways, duties):
            if re.search(r": 이름 일치", w):
                cnt("이름 일치 주장")
                dd = re.match(r"\[[^\]]*\] \S+: (.*) \(p\.\d+\)$", du)
                if dd and r["조직단위(판독)"] not in dd.group(1):
                    prob(f"{co}_조직단위.csv {k}행", f"「이름 일치」 인데 담당업무 「{dd.group(1)}」 에 「{r['조직단위(판독)']}」 없음")
        cj = r["임원_겸직(원문: 겸직회사·직위·선임일·상근)"]
        if cj and "나오지 않음" not in cj:
            pg = [int(x) for x in re.findall(r"p\.(\d+)", r["겸직_출처"])]
            for x in cj.split("\n"):
                m = re.match(r"\[[^\]]*\] \S+: (.*)$", x)
                if not m:
                    continue
                for part in m.group(1).split(" · "):
                    cnt("조직단위 겸직 칸")
                    if not any(in_page(biz, part, p) for p in pg):
                        prob(f"{co}_조직단위.csv {k}행", f"임원_겸직 「{part}」 가 겸직 표 쪽 {pg}(±1)에 없음")


# ───────────────────────────── 4. 「」 짧은 인용 ─────────────────────────────
LABELS = {"Page N", "인원_출처", "같음(공백 무시)", "(판단)", "판독", "추출 범위에 없음", "나오지 않음", "이름 일치", "없음", "원문 글자 그대로"}


def check_inline_quotes(co, units_all):
    """md 「…」 짧은 인용 대조. 인용 블록(「> 」 줄)은 1. 에서 봄, 7) 검증 기록 뒤는 대상 밖."""
    L = md_lines(co)
    f = files_of(co)
    texts = [doc(f[k]).all for k in ("biz", "ann", "ann2", "mgmt")] + [doc(x).all for x in f["corr"]]
    marks = {"(겸)"}
    unorm = {nows(u) for u in units_all}
    for i, x in enumerate(L):
        if "## 7) 검증 기록" in x:
            break
        if x.startswith(">"):
            continue
        for q in re.findall(r"「([^「」]+)」", x):
            n = nows(q)
            cnt("「」 인용")
            if any(n in t for t in texts):
                cnt("「」 원문 확인")
                continue
            if "…" in q and all(any(nows(p) in t for t in texts) for p in q.split("…") if nows(p)):
                cnt("「」 원문 확인(… 줄임 앞뒤)")
                continue
            qq = q.replace("\\|", "|")
            if " | " in qq and all(any(nows(c) in t for t in texts) for c in qq.split(" | ")):
                cnt("「」 원문 확인(칸 이음)")
                continue
            base = re.sub(r" \(겸\)$", "", q)
            if q in units_all or base in units_all or q in marks or n in unorm:
                cnt("「」 판독 글(조직도 단위·표시)")
                continue
            pos = x.find(q)
            if "판독" in x[max(0, pos - 40): pos + len(q) + 40]:
                cnt("「」 판독 글(문맥)")
                INFO.append(f"{co} md {i + 1}줄 「{q[:40]}」 → 판독 글(문맥)(원문 대조 대상 아님)")
                continue
            if q in LABELS or "(판단)" in q:
                cnt("「」 표지 낱말")
                INFO.append(f"{co} md {i + 1}줄 「{q[:40]}」 → 표지 낱말(원문 대조 대상 아님)")
                continue
            if "검색" in x and len(q) <= 20:
                cnt("「」 검색어")
                INFO.append(f"{co} md {i + 1}줄 「{q[:40]}」 → 검색어(원문 대조 대상 아님)")
                continue
            prob(f"{co} md {i + 1}줄", f"「{q[:60]}」 가 원문 텍스트(사업보고서·정정판·연차보고서 본·추가·경영공시)에서 공백 무시로 나오지 않고 판독·판단·검색어 표시도 없음")


# ───────────────────────────── 6. CSV ↔ md ─────────────────────────────
def check_csv_md(co, exec_md, conc_md):
    L = md_lines(co)
    units = read_csv(os.path.join(OUTD, f"{co}_조직단위.csv"))
    h = find_heads(L, r"^## 1\) 조직도 판독 표")[0]
    rows, _ = md_table_rows(L, h, "| id | 상위단위(판독) |")
    if len(rows) != len(units):
        prob(f"{co} md 1) 표", f"행 수 {len(rows)} ↔ 조직단위 CSV {len(units)}")
    for (ln, c), r in zip(rows, units):
        cnt("md↔CSV 조직도 행")
        pairs = ((c[1], r["상위단위(판독)"], "상위단위"), (c[2], r["조직단위(판독)"], "조직단위"),
                 (c[3], r["단위_층위(판독)"], "층위"), (c[4], r["조직도_겸직표시(판독, 없으면 빈칸)"], "겸직표시"))
        for a, b, lab in pairs:
            if a != b:
                prob(f"{co} md {ln}줄", f"{lab} md 「{a}」 ↔ CSV 「{b}」")
    # 임원 표 ↔ 임원겸직 CSV
    ex = read_csv(os.path.join(OUTD, f"{co}_임원겸직.csv"))
    csv_set = set()
    for r in ex:
        tag = re.search(r"\(기준일 : [^)]*\)", r["출처(문서·접수번호·쪽)"].split(" ‖ ")[0]).group(0)
        if r["담당업무(원문)"] == "임원 표에 나오지 않음":
            continue
        csv_set.add((nows(tag), r["성명"], r["직위"], r["등기"], r["상근"], r["담당업무(원문)"], r["대응_조직단위"]))
    md_set = set()
    for head, name, pos, reg, ft, duty, us, ws in exec_md:
        tag = re.search(r"\(기준일 : [^)]*\)", head).group(0)
        for u in us:
            md_set.add((nows(tag), name, pos, reg, ft, duty, u))
    # CSV 는 임원×대응단위가 「 / 」 로 묶여 있을 수 있음 → 풀어서 비교
    csv_flat = set()
    for t in csv_set:
        for u in t[6].split("; "):
            csv_flat.add(t[:6] + (re.sub(r"\([KS]\d+\)$", "", u),))
    for t in sorted(md_set - csv_flat):
        prob(f"{co} md 4) 표", f"md 에만 있음: {t[1]} {t[5]} → {t[6]} ({t[0]})")
    for t in sorted(csv_flat - md_set):
        prob(f"{co}_임원겸직.csv", f"CSV 에만 있음: {t[1]} {t[5]} → {t[6]} ({t[0]})")
    cnt("md↔CSV 임원 대응", len(md_set))
    # 겸직 표 ↔ 임원겸직 CSV 겸직 칸
    md_c = {(nows(re.search(r"\(기준일 : [^)]*\)", h).group(0)), n) + tuple(c) for h, n, c in conc_md}
    csv_c = set()
    for r in ex:
        if not r["겸직회사"] or "나오지 않음" in r["겸직회사"]:
            continue
        tags = re.findall(r"\(기준일 : [^)]*\)", r["출처(문서·접수번호·쪽)"])
        csv_c.add((nows(tags[-1]), r["성명"], r["겸직회사"], r["겸직회사_직위"], r["선임일"], r["상근여부"]))
    for t in sorted(md_c - csv_c):
        prob(f"{co} md 5) 겸직 표", f"md 에만 있음: {t}")
    for t in sorted(csv_c - md_c):
        prob(f"{co}_임원겸직.csv", f"겸직 칸이 md 겸직 표에 없음: {t}")
    cnt("md↔CSV 겸직 행", len(md_c))
    # 지원조직 표 3-1 ↔ 지원조직 CSV(사업보고서 표 행)
    sup = [r for r in read_csv(os.path.join(OUTD, f"{co}_지원조직.csv")) if "지원조직 현황" in r["출처"]]
    h = find_heads(L, r"^### 3-1 ")[0]
    rows, _ = md_table_rows(L, h, "| 조직 종류 |")
    a = sorted((nows(c[1]), nows(c[2]), nows(c[3]).replace("주)", ""), nows(c[4])) for _, c in rows)
    b = sorted((nows(r["부서(팀)명"]), nows(r["직원수"]), nows(r["직위(근속연수)"]).replace("주)", ""), nows(r["주요 활동"])) for r in sup)
    cnt("md↔CSV 지원조직 행", len(a))
    if a != b:
        prob(f"{co} md 3-1 표", f"지원조직 CSV(사업보고서 표 행)와 다름: md {len(a)}행 / CSV {len(b)}행")
    # 3-6 인원 연결 표 ↔ 조직단위 CSV 공시인원
    h = find_heads(L, r"^### 3-6 ")[0]
    rows, _ = md_table_rows(L, h, "| 단위(판독) |")
    um = {r["조직단위(판독)"]: r for r in units}
    for ln, c in rows:
        cnt("md↔CSV 인원 행")
        r = um.get(c[0])
        if not r:
            prob(f"{co} md {ln}줄", f"3-6 단위 「{c[0]}」 가 조직단위 CSV 에 없음")
            continue
        if nows(c[1]) != nows(r["공시인원(원문, 없으면 「추출 범위에 없음」)"]):
            prob(f"{co} md {ln}줄", f"3-6 공시인원 md 「{c[1][:40]}」 ↔ CSV 「{r['공시인원(원문, 없으면 「추출 범위에 없음」)'][:40]}」")
        if nows(c[2]) != nows(r["인원_내역(원문)"]):
            prob(f"{co} md {ln}줄", f"3-6 인원 내역 md ↔ CSV 다름 (「{c[0]}」)")
    n_hc = sum(1 for r in units if r["공시인원(원문, 없으면 「추출 범위에 없음」)"] != "추출 범위에 없음")
    if n_hc != len(rows):
        prob(f"{co} md 3-6 표", f"인원 연결 표 {len(rows)}행 ↔ 조직단위 CSV 인원 있는 단위 {n_hc}")
    return units


# ───────────────────────────── 7. 판독 대조 ─────────────────────────────
FIELD = {"단위 이름": "조직단위(판독)", "상위단위": "상위단위(판독)", "층위": "단위_층위(판독)", "겸직표시": "조직도_겸직표시(판독, 없으면 빈칸)"}


def check_reading(co, units):
    rec = read_csv(os.path.join(OUTD, f"{co}_판독대조.csv"))
    b = json.load(open(os.path.join(OUTD, f"{co}_판독B.json"), encoding="utf-8"))
    a = json.load(open(os.path.join(OUTD, f"{co}_판독A.json"), encoding="utf-8"))

    def key(n):
        return re.sub(r"\s*\(겸\)$", "", n or "")

    def val(v):
        return "" if v.startswith("(없음") else v

    bmap = {key(u["조직단위(판독)"]): u for u in b["units"]}
    aids = [u["id"] for u in a["units"]]
    if len(b["units"]) != len(a["units"]) or set(bmap) != {key(u["단위"]) for u in a["units"]}:
        prob(f"{co} 판독 B", f"판독 B 단위 {len(b['units'])}개 ↔ 판독 A {len(a['units'])}개, 이름 맞춤이 어긋남")
    pref = COS[co]["id"]
    bkeys = {"단위 이름": "조직단위(판독)", "상위단위": "상위단위(판독)", "층위": "단위_층위(판독)", "겸직표시": "조직도_겸직표시(판독)"}
    ndiff = 0
    for k, r in enumerate(rec, 2):
        cnt("판독대조 칸")
        for lab in ("판독B", "확정", "확정 방법"):
            if not r[lab].strip():
                prob(f"{co}_판독대조.csv {k}행", f"{lab} 칸이 비어 있음")
        differ = val(r["판독A"]) != val(r["판독B"])
        ndiff += differ
        m = re.match(r"^(%s\d+) (.+)$" % pref, r["칸"])
        if m:
            idx = aids.index(m.group(1))
            fld = FIELD[m.group(2)]
            if val(r["확정"]) != units[idx][fld]:
                prob(f"{co}_판독대조.csv {k}행", f"확정 「{r['확정']}」 ↔ 조직단위 CSV {fld} 「{units[idx][fld]}」")
            bu = bmap.get(key(a["units"][idx]["단위"]))
            bv = bu[bkeys[m.group(2)]] if bu else None
            if bv is None or val(r["판독B"]) != bv:
                prob(f"{co}_판독대조.csv {k}행", f"판독B 칸 「{r['판독B']}」 ↔ 판독B JSON 「{bv}」")
            if "dpi" not in r["확정 방법"]:
                prob(f"{co}_판독대조.csv {k}행", "확정 방법에 그림 dpi 기록 없음")
        elif r["칸"].startswith("머리글"):
            mk = "머리_집계글(판독)" if r["칸"] == "머리글_집계" else "각주(판독)"
            if r["판독B"] != b[mk]:
                prob(f"{co}_판독대조.csv {k}행", "머리글 판독B 칸 ↔ 판독B JSON 다름")
        if differ and not r["확정 방법"].startswith(("A=B 같은", "A≠B 다시 봄")):
            prob(f"{co}_판독대조.csv {k}행", "A·B 가 다른 칸인데 확정 방법이 「A=B 같은 …」/「A≠B 다시 봄」 꼴이 아님")
        if not differ and not r["확정 방법"].startswith("A=B 같음"):
            prob(f"{co}_판독대조.csv {k}행", "A·B 가 같은 칸인데 확정 방법이 「A=B 같음」 으로 시작하지 않음")
    cnt(f"{co} 판독 A≠B 칸", ndiff)
    # 조직단위 CSV 판독_대조 칸
    for k, r in enumerate(units, 2):
        if not r["판독_대조"] or "판독 B 전" in r["판독_대조"]:
            prob(f"{co}_조직단위.csv {k}행", "판독_대조 칸을 채우지 않음")
    # 머리 집계 글 ↔ 확정 단위 수
    if co == "KB금융지주":
        lay = [r["단위_층위(판독)"] for r in units]
        n_bm = sum(1 for x in lay if x == "부문")
        n_dd = sum(1 for x in lay if x.startswith("담당"))
        n_bb = sum(1 for x in lay if x == "본부")
        n_dept = sum(1 for x in lay if x in ("부", "센터", "Unit", "연구소", "실", "국"))
        head = [r for r in rec if r["칸"] == "머리글_집계"][0]["확정"]
        m = re.match(r"(\d+)부문 (\d+)담당\(준법감시인 포함\) (\d+)본부 (\d+)부서\*", head)
        got = (n_bm, n_dd, n_bb, n_dept)
        if not m or tuple(int(x) for x in m.groups()) != got:
            prob(f"{co} 머리 집계", f"머리 글 「{head}」 ↔ 확정 단위 수 부문·담당·본부·부서 {got}")
        else:
            INFO.append(f"{co} 머리 집계 「{head}」 = 확정 단위 수 부문 {n_bm} · 담당 {n_dd} · 본부 {n_bb} · 부서 {n_dept}")
    else:
        g = [r for r in units if r["조직도_겸직표시(판독, 없으면 빈칸)"] == "(겸)"]
        INFO.append(f"{co} 확정 단위 {len(units)} · 「(겸)」 {len(g)}곳 · 조직도 집계 글 없음")
    return len(rec)


# ───────────────────────────── 8. 보안·형식 ─────────────────────────────
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


def check_security(paths):
    vals = secret_values()
    for p in paths:
        s = open(p, encoding="utf-8", errors="ignore").read()
        for v in vals:
            if v in s:
                prob(p, "인증값 문자열이 파일에 있음(값은 적지 않음)")
        if re.search(r"crtfc_key=(?!\*\*\*)\w", s) or re.search(r"[?&]OC=(?!\*\*\*)\w", s):
            prob(p, "crtfc_key=/OC= 뒤에 가리지 않은 값")
    for d in (OUTD, MDD):
        for dp, dn, fn in os.walk(d):
            for x in fn:
                if x.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                    prob(os.path.join(dp, x), "산출 폴더에 PDF·그림 파일")
    return len(vals)


# ───────────────────────────── main ─────────────────────────────
def main():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    paths = []
    for co in COS:
        exec_md, conc_md = [], []
        check_blockquotes(co)
        check_md_tables(co, exec_md, conc_md)
        check_csv_sources(co)
        units = check_csv_md(co, exec_md, conc_md)
        b = json.load(open(os.path.join(OUTD, f"{co}_판독B.json"), encoding="utf-8"))
        names = {r["조직단위(판독)"] for r in units} | {r["상위단위(판독)"] for r in units} | {u["조직단위(판독)"] for u in b["units"]}
        check_inline_quotes(co, names)
        n = check_reading(co, units)
        cnt(f"{co} 판독대조 행", n)
        paths += [os.path.join(MDD, f"14_{co}.md")] + sorted(glob.glob(os.path.join(OUTD, f"{co}_*")))
    paths += [os.path.join(OUTD, "g1_검사.json"), os.path.abspath(__file__), os.path.join(ROOT, "scripts", "dart", "org14_g1.py")]
    nsec = check_security([p for p in paths if os.path.exists(p)])
    out = [f"# verify14_g1 — {now}", "", f"대상: {', '.join(COS)}", f"인증값 검사에 쓴 값 개수: {nsec}(값은 적지 않음)", "", "## 대조 수"]
    out += [f"- {k}: {v}" for k, v in COUNT.items()]
    out += ["", "## 참고"] + [f"- {x}" for x in INFO]
    out += ["", f"## 문제 {len(PROBS)}건"] + [f"- {w}: {m}" for w, m in PROBS]
    out += ["", "결과: " + ("통과(exit 0)" if not PROBS else "문제 있음(exit 1)")]
    open(REPORT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"문제 {len(PROBS)}건 · 결과 {os.path.relpath(REPORT, ROOT)}")
    for w, m in PROBS[:40]:
        print(f"  - {w}: {m}")
    return 0 if not PROBS else 1


if __name__ == "__main__":
    sys.exit(main())
