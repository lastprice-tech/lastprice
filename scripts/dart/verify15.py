#!/usr/bin/env python3
"""15차 합본 검증 — 인자 없이 `python3 scripts/dart/verify15.py` → exit 0(통과)/1(실패), 결과 dart_out/ops15/verify15.txt.

보는 것
  (1) 조각 검증 6개(verify15_bs_g1~g3 · verify15_gov_g1~g2 · verify15_C)를 돌려 exit 를 모음(각 스크립트가 자기 결과 txt 를 다시 씀).
  (2) 합본 CSV 4개 = 조각 CSV 를 이어 붙인 것: BOM·열 이름, 행 수, 행마다 짝이 되는 조각 행이 하나씩 있고 다른 칸이 없음.
      예외는 합본 규칙으로 바뀐 칸뿐 — A 사업보고서 행 reason_text(조각은 「문서에 없음」, 합본은 같은 회사·FY·사람·겸직 회사의
      연차보고서 행 reason_text 원문과 글자까지 같음)와 그 note 덧붙임, B 연차보고서 행 직원 수 칸(빈칸)과 note 덧붙임.
      정렬: 회사 순서 → fy → doc_kind, 같은 키 안에서는 조각 순서.
  (3) 합본 모든 행(표본 아님)의 source_text·reason_text 가 출처 텍스트에 그대로 있음(공백·줄바꿈·「|」·<br>·&cr;·제어문자만 무시).
      출처 텍스트: 사업보고서 = dart_out/text/ops15 의 OpenDART XML md(사업보고서_원문.csv), 연차보고서 = 쪽 텍스트 md(목록 CSV·download.json)
      또는 6차 섹션 글(kit56/연차보고서_섹션.csv, doc_name 의 파일 이름), 경영공시 = 13차 텍스트 zip, 작업 C = 신고서 XML md 또는
      kit zip 의 웹 회수본. JB FY2019 판독 행(글자층 깨짐)은 verify15_gov_g2.VISUAL(쪽 그림을 보고 적은 글)과 대조.
  (4) 15차_보고.md 의 「문서에 없음」 수·비율·사유 잇기 수가 합본에서 다시 센 값과 같음.
  (5) 키·비밀값 없음(DART_API_KEY 값, crtfc_key=값, 40자리 16진), handoff/원문_지주운영방식 에 PDF 없음,
      원문 md 사본·zip 이 dart_out/ops15/원문 과 바이트까지 같음.
웹 요청·API 키 사용 없음(키 값은 환경변수에서 읽어 비교만 하고 어디에도 쓰지 않음).
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(10 ** 9)
KST = timezone(timedelta(hours=9))

OPS = os.path.join(ROOT, "dart_out", "ops15")
FRAG = os.path.join(OPS, "조각")
OUTDIR = os.path.join(ROOT, "handoff", "원문_지주운영방식")
OUTTXT = os.path.join(OPS, "verify15.txt")
TXT = os.path.join(ROOT, "dart_out", "text", "ops15")
T13_ZIP = os.path.join(ROOT, "handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
KITZIP = os.path.join(ROOT, "handoff", "dart-benchmark-kit.zip")
SEC6 = os.path.join(OPS, "kit56", "연차보고서_섹션.csv")
NONE = "문서에 없음"
PANDOK = "판독(PDF 글자층 깨짐 — 쪽 그림을 보고 옮김)"
CHECKERS = ["bs_g1", "bs_g2", "bs_g3", "gov_g1", "gov_g2", "C"]

sys.path.insert(0, HERE)
import ops15_merge as M  # noqa: E402  (열·회사 순서·합본 규칙 상수만 씀 — main 은 부르지 않음)

os.chdir(ROOT)
OUT, FAIL = [], []


def say(s=""):
    OUT.append(s)


def fail(s):
    FAIL.append(s)
    OUT.append("  [실패] " + s)


_CC = re.compile(r"[\s|｜ 　﻿\x00-\x1f\x7f]+")


def norm(s):
    return _CC.sub("", (s or "").replace("<br>", "").replace("&cr;", ""))


def pieces(s):
    return [p for p in s.split(" … ")] if " … " in s else [s]


def read_csv(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    rd = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    return bom, rd.fieldnames, [dict(r) for r in rd]


# ================================================================ (1) 조각 검증
def run_checkers():
    say("## (1) 조각 검증 6개 실행")
    res = {}
    for k in CHECKERS:
        p = os.path.join(HERE, "verify15_%s.py" % k)
        t0 = datetime.now()
        cp = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True, text=True)
        last = (cp.stdout.strip().split("\n") or [""])[-1][:160]
        res[k] = cp.returncode
        say("- verify15_%s.py exit %d (%.0f초) — %s" % (k, cp.returncode, (datetime.now() - t0).total_seconds(), last))
        if cp.returncode != 0:
            fail("verify15_%s.py exit %d: %s" % (k, cp.returncode, cp.stderr.strip()[-300:]))
    say("")
    return res


# ================================================================ (2) 합본 = 조각 이어 붙임
def link_key(r):
    return (r["corp_label"], r["fy"], M.pkey(r["person"]), M.ckey(r["concurrent_company"]))


def check_concat():
    say("## (2) 합본 CSV = 조각 이어 붙임")
    merged, frags = {}, {}
    stats = {}
    for t, spec in M.TASKS.items():
        path = os.path.join(OUTDIR, spec["out"])
        bom, hdr, rows = read_csv(path)
        if not bom:
            fail("%s BOM 없음" % spec["out"])
        if hdr != M.COLS[t]:
            fail("%s 열 이름이 COMMON15 와 다름: %r" % (spec["out"], hdr))
        fr = []
        for fn in spec["frags"]:
            b2, h2, rs = read_csv(os.path.join(FRAG, fn + ".csv"))
            if h2 != M.COLS[t]:
                fail("조각 %s 열 이름 다름" % fn)
            for i, r in enumerate(rs):
                r["_frag"], r["_i"] = fn, i
            fr += rs
        merged[t], frags[t] = rows, fr
        if len(rows) != len(fr):
            fail("작업 %s 행 수: 합본 %d · 조각 합 %d" % (t, len(rows), len(fr)))
        # 바뀔 수 있는 칸을 뺀 키로 짝 맞춤(같은 키는 조각 순서대로)
        loose = {"A": {"reason_text", "note"}, "B": {"employees_total", "regular", "contract", "note"}}.get(t, set())
        cols = [c for c in M.COLS[t] if c not in loose]
        pool = defaultdict(list)
        for r in fr:
            pool[tuple(r[c] for c in cols)].append(r)
        pairs, unmatched = [], 0
        for r in rows:
            k = tuple(r[c] for c in cols)
            if pool.get(k):
                pairs.append((r, pool[k].pop(0)))
            else:
                unmatched += 1
        left = sum(len(v) for v in pool.values())
        if unmatched or left:
            fail("작업 %s 짝 없는 행: 합본 %d · 조각 %d" % (t, unmatched, left))
        # 다른 칸 검사
        changed = Counter()
        gov_by = defaultdict(list)
        if t == "A":
            for r in rows:
                if r["doc_kind"] == M.GOV and r["reason_text"] not in ("", NONE):
                    gov_by[link_key(r)].append(r)
        for m, f in pairs:
            diff = [c for c in M.COLS[t] if m[c] != f[c]]
            if not diff:
                continue
            if t == "A" and m["doc_kind"] == M.BS and set(diff) <= {"reason_text", "note"}:
                cands = [g for g in gov_by.get(link_key(m), []) if M.birth_ok(m["birth_ym"], g["birth_ym"])]
                if not cands:
                    fail("A 바뀐 행에 짝 연차보고서 행 없음: %s FY%s %s" % (m["corp_label"], m["fy"], m["person"]))
                    continue
                g = cands[0]
                where = "지배구조 연차보고서 %s %s" % (g["rcept_no_or_url"], g["page"])
                if "reason_text" in diff:
                    ok = (f["reason_text"] == NONE and m["reason_text"] == g["reason_text"]
                          and m["note"].startswith(f["note"]) and ("reason_text 출처: %s (같은 겸직)" % where) in m["note"][len(f["note"]):])
                    changed["A reason_text 이음"] += 1
                else:
                    ok = (f["reason_text"] not in ("", NONE) and m["note"].startswith(f["note"])
                          and ("같은 겸직의 연차보고서 사유 원문도 있음: %s" % where) in m["note"][len(f["note"]):])
                    changed["A note 만(사유 덮지 않음)"] += 1
                if not ok:
                    fail("A 사유 잇기 칸이 규칙과 다름: %s FY%s %s" % (m["corp_label"], m["fy"], m["person"]))
            elif t == "B" and m["doc_kind"] == M.GOV and set(diff) <= {"employees_total", "regular", "contract", "note"}:
                ok = (not (m["employees_total"] or m["regular"] or m["contract"])
                      and m["note"].startswith(f["note"]) and m["note"][len(f["note"]):] in ("; " + M.EMP_NOTE, M.EMP_NOTE))
                changed["B 연차보고서 note"] += 1
                if not ok:
                    fail("B 연차보고서 행 바뀐 칸이 규칙과 다름: %s FY%s" % (m["corp_label"], m["fy"]))
            else:
                fail("작업 %s 규칙 밖에서 바뀐 칸 %s: %s FY%s" % (t, diff, m["corp_label"], m.get("fy", "")))
        if t == "B":
            for m, f in pairs:
                if m["doc_kind"] == M.GOV and (m["employees_total"] or m["regular"] or m["contract"] or M.EMP_NOTE not in m["note"]):
                    fail("B 연차보고서 행 직원 수 칸/ note 규칙 어김: %s FY%s" % (m["corp_label"], m["fy"]))
        # 정렬
        order = {fn: i for i, fn in enumerate(spec["frags"])}

        def skey(m_f):
            m, f = m_f
            base = (M.corp_idx(m["corp_label"]),) if t == "C" else (M.corp_idx(m["corp_label"]), m["fy"], M.KIND_ORDER[m["doc_kind"]])
            return base + (order[f["_frag"]], f["_i"])
        keys = [skey(p) for p in pairs]
        if keys != sorted(keys):
            fail("작업 %s 정렬이 회사·fy·doc_kind·조각 순서와 다름" % t)
        stats[t] = dict(rows=len(rows), changed=changed)
        say("- 작업 %s %s: 합본 %d행 = 조각 %s 합 %d행, 짝 없음 0, 바뀐 칸 %s, 정렬 맞음" % (
            t, spec["out"], len(rows), "+".join("%s" % fn for fn in spec["frags"]), len(fr),
            dict(changed) if changed else "없음"))
    say("")
    return merged, stats


# ================================================================ (3) 출처 텍스트 전수 대조
class Sources:
    def __init__(self):
        self.cache = {}
        self.bs = {}
        for r in csv.DictReader(open(os.path.join(OPS, "사업보고서_원문.csv"), encoding="utf-8-sig")):
            if r["text_path"]:
                self.bs[r["rcept_no"]] = os.path.join(ROOT, r["text_path"])
        self.gov_url = {}
        for g in ("g1", "g2"):
            for r in csv.DictReader(open(os.path.join(OPS, "연차보고서15_목록_%s.csv" % g), encoding="utf-8-sig")):
                p = os.path.join(TXT, "연차보고서__%s__%s__%s.md" % (r["회사"], r["공시연도"], r["공시유형"]))
                if r["파일_url"] and os.path.exists(p):
                    self.gov_url.setdefault(r["파일_url"], p)
        for r in json.load(open(os.path.join(OPS, "gov15_g1_work", "download.json"), encoding="utf-8")):
            if r.get("text_path"):
                for u in (r.get("실제_url"), r.get("파일_url")):
                    if u:
                        self.gov_url.setdefault(u, os.path.join(ROOT, r["text_path"]))
        self.sec6 = defaultdict(list)
        for r in csv.DictReader(open(SEC6, encoding="utf-8-sig")):
            self.sec6[r["파일명"]].append(r)
        self.t13 = zipfile.ZipFile(T13_ZIP)
        self.web = defaultdict(list)
        with zipfile.ZipFile(KITZIP) as z:
            t = z.read("원문_지주전환_서술.csv").decode("utf-8-sig")
        for r in csv.DictReader(io.StringIO(t, newline="")):
            if r["status"].startswith("014"):
                self.web[r["rcept_no"]].append(r)
        sys.path.insert(0, HERE)
        import verify15_gov_g2 as G2  # VISUAL(판독 글)만 씀
        os.chdir(ROOT)
        self.visual = [norm(v[0]) for v in G2.VISUAL.values()]

    def _get(self, key, loader):
        if key not in self.cache:
            self.cache[key] = norm(loader())
        return self.cache[key]

    @staticmethod
    def _strip_pages(s):
        return re.sub(r"(?m)^## p\.\d+.*$", "", s)

    def bs_text(self, rcept):
        p = self.bs.get(rcept)
        if not p:
            return None
        return self._get(("bs", rcept), lambda: open(p, encoding="utf-8").read())

    def mgmt_text(self, corp):
        n = next((x for x in self.t13.namelist() if x.endswith("텍스트/경영공시__%s.md" % corp)), None)
        if not n:
            return None
        return self._get(("t13", corp), lambda: self._strip_pages(self.t13.read(n).decode("utf-8")))

    def gov_text(self, row):
        m = re.search(r"파일 (.+?)\)$", row["doc_name"])
        if m and m.group(1) in self.sec6:
            fn = m.group(1)

            def ld():
                rs = sorted(self.sec6[fn], key=lambda x: (int(x["섹션순번"] or 0), int(x["chunk_seq"] or 0)))
                return "\n".join(x["본문"] for x in rs)
            return "sec6", self._get(("sec6", fn), ld)
        p = self.gov_url.get(row["rcept_no_or_url"])
        if p:
            return "pdf", self._get(("pdf", p), lambda: self._strip_pages(open(p, encoding="utf-8").read()))
        return None, None

    def c_text(self, rcept):
        p = os.path.join(TXT, "신고서__%s.md" % rcept)
        if os.path.exists(p):
            return "신고서 XML md", self._get(("c", rcept), lambda: open(p, encoding="utf-8").read())
        if rcept in self.web:
            return "웹 회수본(kit zip)", self._get(("web", rcept), lambda: "\n".join(
                r["section_text"] for r in sorted(self.web[rcept], key=lambda x: (int(x["section_index"]), int(x["chunk_seq"])))))
        return None, None


def found(text, s):
    """→ 'whole'(글 전체가 이어서 있음) | 'lines'(「 … 」·줄로 나눈 조각이 차례대로 있음) | None."""
    if text is None:
        return None
    ps = [norm(p) for p in pieces(s)]
    if all(p and p in text for p in ps):
        return "whole"
    parts = [norm(x) for p in pieces(s) for x in p.split("\n")]
    parts = [x for x in parts if x]
    pos = 0
    for x in parts:
        j = text.find(x, pos)
        if j < 0:
            return None
        pos = j + len(x)
    return "lines" if parts else None


def check_sources(merged):
    say("## (3) 합본 모든 행의 source_text·reason_text 가 출처 텍스트에 그대로(전수)")
    S = Sources()
    tally = Counter()
    for t in "ABCD":
        rows = merged[t]
        for i, r in enumerate(rows, 2):
            st = r["source_text"]
            if st == NONE:
                tally[(t, "문서에 없음(대조 없음)")] += 1
                continue
            kind = r.get("doc_kind", "")
            if t == "C":
                how, text = S.c_text(r["rcept_no"])
            elif kind == M.BS:
                how, text = "사업보고서 XML md", S.bs_text(r["rcept_no_or_url"])
            elif kind == "경영공시":
                how, text = "13차 경영공시 텍스트", S.mgmt_text(r["corp_label"])
            elif kind == M.GOV:
                how, text = S.gov_text(r)
                how = {"sec6": "6차 섹션 글", "pdf": "연차보고서 쪽 텍스트"}.get(how, how)
            else:
                how, text = None, None
            if PANDOK in r.get("note", "") and t in "AB" and kind == M.GOV:
                ok = any(norm(st) in v or v in norm(st) for v in S.visual) and norm(st)
                tally[(t, "판독 글(VISUAL 대조)")] += 1
                if not ok:
                    fail("%s 줄 %d 판독 행이 VISUAL 글과 다름: %s FY%s" % (t, i, r["corp_label"], r["fy"]))
                continue
            if text is None:
                fail("%s 줄 %d 출처 텍스트를 못 찾음: %s %s %s" % (t, i, r["corp_label"], kind, r.get("rcept_no_or_url", r.get("rcept_no"))[:80]))
                continue
            fd = found(text, st)
            if fd:
                tally[(t, how + ("" if fd == "whole" else " — 줄·조각별로 차례대로"))] += 1
            else:
                fail("%s 줄 %d source_text 가 출처(%s)에 없음: %s %s %s" % (t, i, how, r["corp_label"], r.get("fy", ""), st[:60]))
        if t == "A":
            gov_by = defaultdict(list)
            for r in rows:
                if r["doc_kind"] == M.GOV and r["reason_text"] not in ("", NONE):
                    gov_by[link_key(r)].append(r)
            for i, r in enumerate(rows, 2):
                rt = r["reason_text"]
                if rt in ("", NONE):
                    continue
                if r["doc_kind"] == M.GOV:
                    _, text = S.gov_text(r)
                    src = "연차보고서(자기 행)"
                elif "reason_text 출처: 지배구조 연차보고서" in r["note"]:
                    g = next((g for g in gov_by.get(link_key(r), []) if g["reason_text"] == rt), None)
                    text = S.gov_text(g)[1] if g else None
                    src = "연차보고서(이은 행)"
                else:
                    text = S.bs_text(r["rcept_no_or_url"])
                    src = "사업보고서(자기 행)"
                fd = found(text, rt)
                if fd:
                    tally[("A reason_text", src + ("" if fd == "whole" else " — 줄·조각별로 차례대로"))] += 1
                else:
                    fail("A 줄 %d reason_text 가 출처에 없음(%s): %s FY%s %s" % (i, src, r["corp_label"], r["fy"], r["person"]))
    for (t, how), n in sorted(tally.items()):
        say("- %s · %s: %d행 맞음" % (t, how, n))
    say("")
    return tally


# ================================================================ (4) 보고 숫자
def check_report(merged, stats):
    say("## (4) 15차_보고.md 숫자 = 합본에서 다시 센 값")
    rp = open(os.path.join(OUTDIR, "15차_보고.md"), encoding="utf-8").read()
    tab = {}
    for m in re.finditer(r"(?m)^\| (A|B|C|D|A reason_text) \| [^|]+ \| (\d+) \| (\d+) \| ([\d.]+%|-) \|$", rp):
        tab[m.group(1)] = (int(m.group(2)), int(m.group(3)), m.group(4))
    for t in ["A", "B", "C", "D", "A reason_text"]:
        rows = merged[t[0]]
        col = "reason_text" if t == "A reason_text" else "source_text"
        n, k = len(rows), sum(r[col] == NONE for r in rows)
        want = (n, k, M.pct(k, n))
        got = tab.get(t)
        if got != want:
            fail("보고 표 %s: 보고 %s · 합본 %s" % (t, got, want))
        else:
            say("- %s: %d행 중 「문서에 없음」 %d (%s) — 보고와 같음" % (t, n, k, want[2]))
    m = re.search(r"이은 행 (\d+)", rp)
    n_link = stats["A"]["changed"].get("A reason_text 이음", 0)
    if not m or int(m.group(1)) != n_link:
        fail("보고의 사유 잇기 수(%s)와 합본(%d)이 다름" % (m.group(1) if m else "없음", n_link))
    else:
        say("- 사유 잇기 %d행 — 보고와 같음" % n_link)
    for t, spec in M.TASKS.items():
        if not re.search(r"\| %s \| 작업 %s .*\| %d \|" % (re.escape(spec["out"]), t, len(merged[t])), rp):
            fail("보고 산출물 표의 %s 행 수가 합본(%d)과 다름" % (spec["out"], len(merged[t])))
    say("")


# ================================================================ (5) 비밀값·PDF·md 사본
HEX40 = re.compile(rb"(?<![0-9A-Fa-f])[0-9a-f]{40}(?![0-9A-Fa-f])")
CRTFC = re.compile(rb"crtfc_key=[0-9A-Za-z]{16,}")


def check_files():
    say("## (5) 키·비밀값, PDF, 원문 md 사본")
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        say("- (참고) 환경변수 DART_API_KEY 가 없어 값 대조는 건너뛰고 꼴(crtfc_key=·40자리 16진)만 봄")
    files = []
    for dp, dn, fn in os.walk(OUTDIR):
        for f in fn:
            files.append(os.path.join(dp, f))
    files += [os.path.join(HERE, "ops15_merge.py"), os.path.join(HERE, "verify15.py")]
    blobs = []
    for p in files:
        b = open(p, "rb").read()
        blobs.append((os.path.relpath(p, ROOT), b))
        if p.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for zi in z.infolist():
                    blobs.append(("%s!%s" % (os.path.relpath(p, ROOT), zi.filename), z.read(zi)))
    hits = 0
    for label, b in blobs:
        if key and key.encode() in b:
            hits += 1
            fail("키 값이 들어 있음: %s" % label)
        if CRTFC.search(b):
            hits += 1
            fail("crtfc_key=값 꼴: %s" % label)
        if HEX40.search(b):
            hits += 1
            fail("40자리 16진 문자열: %s" % label)
    say("- 검사한 파일·zip 항목 %d개(합본 폴더 전체 + ops15_merge.py·verify15.py): 걸린 것 %d" % (len(blobs), hits))
    pdf = [l for l, b in blobs if l.lower().endswith(".pdf") or b[:5] == b"%PDF-"]
    if pdf:
        fail("PDF 가 있음: %s" % pdf[:5])
    say("- PDF(확장자·%%PDF- 머리): %d개" % len(pdf))
    # 원문 md 사본·zip
    src = os.path.join(OPS, "원문")
    want = {}
    for t in "ABCD":
        for fn in os.listdir(os.path.join(src, t)):
            if fn.endswith(".md"):
                want["원문/%s/%s" % (t, fn)] = open(os.path.join(src, t, fn), "rb").read()
    have = {}
    for t in "ABCD":
        d = os.path.join(OUTDIR, "원문", t)
        for fn in (os.listdir(d) if os.path.isdir(d) else []):
            have["원문/%s/%s" % (t, fn)] = open(os.path.join(d, fn), "rb").read()
    if want != have:
        fail("원문 md 사본이 dart_out/ops15/원문 과 다름(없는 것 %d · 남는 것 %d · 다른 것 %d)" % (
            len(set(want) - set(have)), len(set(have) - set(want)), sum(1 for k in want if k in have and want[k] != have[k])))
    zp = os.path.join(OUTDIR, M.ZIP_NAME)
    with zipfile.ZipFile(zp) as z:
        zin = {zi.filename: z.read(zi) for zi in z.infolist()}
        utf8 = all(zi.flag_bits & 0x800 for zi in z.infolist() if not zi.filename.isascii())
    if zin != want:
        fail("zip 내용이 원문 md 와 다름")
    if not utf8:
        fail("zip 파일 이름 UTF-8 표시 없음")
    say("- 원문 md 사본 %d개·zip 항목 %d개가 dart_out/ops15/원문 과 바이트까지 같음, zip 이름 UTF-8 표시 있음" % (len(have), len(zin)))
    say("")


def main():
    t0 = datetime.now(KST)
    say("# 15차 합본 검증(verify15.py)")
    say("")
    say("- 실행 %s KST · 합본 폴더 handoff/원문_지주운영방식 · 조각 dart_out/ops15/조각" % t0.strftime("%Y-%m-%d %H:%M"))
    say("")
    res = run_checkers()
    merged, stats = check_concat()
    check_sources(merged)
    check_report(merged, stats)
    check_files()
    say("## 결과")
    say("")
    say("- 조각 검증 exit: " + " · ".join("%s %d" % (k, v) for k, v in res.items()))
    say("- 실패 %d건 → %s" % (len(FAIL), "exit 1" if FAIL else "exit 0"))
    with open(OUTTXT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(OUT) + "\n")
    print("verify15: 실패 %d건 → %s" % (len(FAIL), os.path.relpath(OUTTXT, ROOT)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
