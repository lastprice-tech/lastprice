# -*- coding: utf-8 -*-
"""13차 정합성 보정 — 그룹 D(웹 자료: 9-2-4 ORSA 보도자료 · 9-5 금감원 검사결과 · 9-3 RAAS · 9-4 모범규준 원문).

    python3 -I scripts/dart/fix13_D.py          # 보정(멱등: 언제나 기준 사본 pre/ 에서 다시 만듦) — md 4개·9-5 CSV 를 다시 쓰고
                                                #   dart_out/raw/web13/fix13_D/fix_log.json · 공개일_재확인.json 을 씀
    python3 -I scripts/dart/fix13_D.py check    # fix_log 「후」가 지금 파일에 다 있는지, 원문 인용 줄(코드 블록·> 블록)이 기준 사본과
                                                #   같은지(출처 줄·표지 줄을 끼운 것 말고는) → 문제 0 이면 exit 0

규칙: 13차 정합성 보정 규칙 R1~R5(비평 dart_out/risk13/critic13.json 의 gaps·contradictions 대응).
  R2 조 번호 칸(연혁·출처 자료 → 조 번호 해당 없음(연혁·출처 자료), 조가 없다는 판단 → 조 번호 해당 없음(판단: 이유), 글 안에만 있던 조 → 조 번호 칸),
  R3 우리 글의 「없음」 단정 → 「추출 범위에 없음」+찾은 방법, R4 인용 블록마다 출처 줄, R5 날짜 라벨 KST·날짜 종류(배포일·보도일·등록일).
기준 사본: 커밋 496ddc4 의 대상 파일 → dart_out/raw/web13/fix13_D/pre/ (없으면 git show 로 만듦).
대상(이 스크립트만 고침): handoff/13차_산출물/{9-2-4_ORSA_보도자료,9-5_금감원_검사결과,9-3_RAAS,9-4_모범규준_원문}.md,
      dart_out/risk13/9-5_검사결과_목록.csv(검증메모 날짜 라벨·「없음」 낱말, 「공개일(지시서 9-5)」 칸 더함, 조제목 칸 R2 꼴),
      dart_out/risk13/9-3_RAAS_낱말문장.csv(조 칸 R2 꼴 — 재비평 보정).
재비평 보정(dart_out/risk13/critic13_2.json new_issues 8·9 + 연관, 2026-10-08 KST): 9-2-4 1절 표 날짜 칸 종류(R5), 9-2-4·9-3·9-5
  지시서 항목 대조 표·9-3 2절 표 상태 칸을 R1 세 단계로, 9-3·9-5 CSV·9-5 색인의 「조가 없다」 칸을 「조 번호 해당 없음(판단: …)」 꼴로(R2).
원문 인용 줄(``` 코드 블록 안·> 줄)은 바꾸지 않는다. 바꿀 글이 예상 횟수만큼 나오지 않으면 멈춘다(SystemExit).
9-4_모범규준_원문.md·9-3_RAAS.md 는 줄을 끼우지 않는다(다른 산출물이 「md N줄」로 가리킴) — 제자리 바꿈과 맨 끝 소절만.
재생성 순서: verify13_web.py fix · verify13_raas.py fix · verify13_mobeom.py fix(검증 보정 — 다시 돌리면 이 보정이 지워짐) → 이 스크립트.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만). 내려받은 HTML 을 읽으므로 `python3 -I` 로 실행.
"""
from __future__ import annotations

import collections
import csv
import glob
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

BASE = "496ddc4"
TODAY = "2026-10-08"
FD = os.path.join("dart_out", "raw", "web13", "fix13_D")
PRE = os.path.join(FD, "pre")
LOGF = os.path.join(FD, "fix_log.json")
SCANF = os.path.join(FD, "공개일_재확인.json")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
FSS = os.path.join("dart_out", "raw", "web13", "fss")
MD = {"P": os.path.join(OUTD, "9-2-4_ORSA_보도자료.md"), "E": os.path.join(OUTD, "9-5_금감원_검사결과.md"),
      "R": os.path.join(OUTD, "9-3_RAAS.md"), "M": os.path.join(OUTD, "9-4_모범규준_원문.md")}
CSV_E = os.path.join(WORK, "9-5_검사결과_목록.csv")
CSV_R = os.path.join(WORK, "9-3_RAAS_낱말문장.csv")
CSVS = (CSV_E, CSV_R)
CRIT2 = "재비평(dart_out/risk13/critic13_2.json new_issues)"
R1_RE = re.compile(r"^(?:받은 글(?:\(.+\))?|일부\(.+\)|추출 범위에 없음(?:\(.+\))?)$")   # R1 세 단계 — 상태 칸 글 전체
VERIFY ={"P": "verify13_web.py", "E": "verify13_web.py", "R": "verify13_raas.py", "M": "verify13_mobeom.py"}
NOART = "조 번호 해당 없음(연혁·출처 자료)"
NEW_VH = "## 검증 기록(2026-10-08 KST)"
OLD_VH = "## 검증 기록(2026-10-07)"
PUB_COL = "공개일(지시서 9-5)"
LOG: list = []


# ───────────────────────────── 문서 ─────────────────────────────
def pre_path(p):
    return os.path.join(PRE, os.path.basename(p))


def ensure_pre():
    os.makedirs(PRE, exist_ok=True)
    for p in list(MD.values()) + list(CSVS):
        q = pre_path(p)
        if not os.path.exists(q):
            b = subprocess.run(["git", "show", f"{BASE}:{p}"], capture_output=True, check=True).stdout
            open(q, "wb").write(b)


def code_lines(L):
    out, incode = [], False
    for ln in L:
        if ln.startswith("```"):
            incode = not incode
            out.append(ln)
            continue
        if incode or ln.startswith(">"):
            out.append(ln)
    return out


class Doc:
    def __init__(self, key, path):
        self.key, self.path = key, path
        raw = open(pre_path(path), "rb").read()
        self.text0 = raw.decode("utf-8")
        self.lines = self.text0.split("\n")
        self.code, self.fixed = set(), set()
        self.ins = {}
        incode = on = False
        for i, ln in enumerate(self.lines):
            if ln.startswith("```"):
                self.code.add(i)
                incode = not incode
                continue
            if incode or ln.startswith(">"):
                self.code.add(i)
            if ln.startswith(("### 고친 곳", "### 1. 고친 곳")):   # 검증 기록 「고친 곳(전·후)」 소절 = 그때 적은 기록 — 고치지 않음
                on = True
                continue
            if on and (ln.startswith("### ") or ln.startswith("## ")):
                on = False
            if on:
                self.fixed.add(i)

    def log(self, i, before, after, rule, why):
        LOG.append(dict(파일=self.path, 줄_기준사본=i + 1, 전=before, 후=after, 규칙=rule, 이유=why))

    def hits(self, old, pred=None, skip_fixed=True):
        return [i for i, ln in enumerate(self.lines) if i not in self.code and old in ln
                and (not skip_fixed or i not in self.fixed) and (pred is None or pred(i, ln))]

    def count(self, old, pred=None, skip_fixed=True):
        return sum(self.lines[i].count(old) for i in self.hits(old, pred, skip_fixed))

    def sub(self, old, new, rule, why, count=1, pred=None, skip_fixed=True):
        hs = self.hits(old, pred, skip_fixed)
        n = sum(self.lines[i].count(old) for i in hs)
        if n != count:
            raise SystemExit(f"[fix13_D {self.key} {os.path.basename(self.path)}] 「{old[:80]}」 {n}번 나옴(기대 {count}) — {why}")
        for i in hs:
            b = self.lines[i]
            a = b.replace(old, new)
            self.lines[i] = a
            self.log(i, b, a, rule, why)

    def idx(self, pred, what):
        hs = [i for i, ln in enumerate(self.lines) if i not in self.code and pred(i, ln)]
        if len(hs) != 1:
            raise SystemExit(f"[fix13_D {self.key}] {what}: {len(hs)}줄(기대 1)")
        return hs[0]

    def set_line(self, i, new, rule, why):
        b = self.lines[i]
        if i in self.code:
            raise SystemExit(f"[fix13_D {self.key}] 인용 줄 {i + 1} 을 바꾸려 함")
        if b != new:
            self.lines[i] = new
            self.log(i, b, new, rule, why)

    def insert_after(self, i, new_lines, rule, why):
        self.ins.setdefault(i, []).extend(new_lines)
        LOG.append(dict(파일=self.path, 줄_기준사본=f"{i + 1} 뒤에 끼움", 전="-", 후=list(new_lines), 규칙=rule, 이유=why))

    def final(self):
        out = []
        for i, ln in enumerate(self.lines):
            out.append(ln)
            out.extend(self.ins.get(i, []))
        return out

    def write(self):
        open(self.path, "wb").write("\n".join(self.final()).encode("utf-8"))

    def nlog(self):
        return sum(1 for x in LOG if x["파일"] == self.path)


# ───────────────────────────── 공통: 날짜 라벨(R5) ─────────────────────────────
R5_WHY = "13차 검증은 KST 2026-10-08(커밋 8c118c8·496ddc4, UTC 2026-10-08 00:49~04:19) — 절 제목·본문 날짜 라벨"


def vh_rename(d):
    d.sub(OLD_VH, NEW_VH, "R5", R5_WHY, count=1, pred=lambda i, ln: ln == OLD_VH)


# ───────────────────────────── 9-5 원본(공개안 PDF meta) ─────────────────────────────
def exam_docs():
    out = {}
    for kind, sub in (("impr", "impr"), ("sanc", "sanc")):
        for mp in sorted(glob.glob(os.path.join(FSS, "exam", sub, "*.pdf.meta.json"))):
            m = json.load(open(mp, encoding="utf-8"))
            out[m["sha256"]] = dict(kind=kind, name=m.get("원파일명") or os.path.basename(mp)[:-10], url=m["출처URL"],
                                    fetched=m["fetched_at"], board=m.get("목록", "검사결과제재" if kind == "sanc" else "금융회사 경영유의사항 등 공시"))
    return out


def kst_day(fa):
    if not fa.endswith("+09:00"):
        raise SystemExit("fetched_at 이 KST(+09:00) 아님: " + fa)
    return fa[:10] + "(KST)"


# ───────────────────────────── 9-5 공개일 다시 확인 ─────────────────────────────
PUB_WORDS = ["등록일", "게시일", "공시일", "공개일", "작성일", "수정일", "게시일자", "등록일자", "공개일자", "공시일자",
             "regDt", "regDate", "registDt", "RegistPnttm", "openDt", "pblicte", "pstgDt", "ntceDt", "writeDt", "updtDt", "Last-Modified"]


def _txt(x):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).replace("&middot;", "·").strip()


def pub_scan():
    """목록·상세 HTML(받은 원본 그대로)·목록 CSV·.meta.json 에서 공개(게시)일 칸이 있는지 다시 본다. 새 웹 요청 없음."""
    lists = sorted(glob.glob(os.path.join(FSS, "exam", "list", "*.html")))
    details = sorted(glob.glob(os.path.join(FSS, "exam", "sanc", "*.html")))
    probes = sorted(glob.glob(os.path.join(FSS, "probe", "openInfo*_list.html")))
    th, words, dt_list, dt_det = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    dt_order = []
    for group, files in (("list", lists), ("detail", details), ("probe", probes)):
        for p in files:
            t = open(p, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r"<th[^>]*>(.*?)</th>", t, re.S):
                th[_txt(m.group(1))] += 1
            dts = [_txt(m.group(1)) for m in re.finditer(r"<dt[^>]*>(.*?)</dt>", t, re.S)]
            (dt_det if group == "detail" else dt_list).update(set(dts))
            if group == "detail":
                dt_order += [x for x in dts if x not in dt_order]
            for w in PUB_WORDS:
                if w in t:
                    words[(group, w)] += t.count(w)
    dt_only = [k for k in dt_order if k not in dt_list]                      # 메뉴 dt(모든 화면 공통)를 뺀 상세 화면 칸(화면 순서)
    csvs = {}
    for name in ("9-5_경영유의공시_전체목록.csv", "9-5_검사결과제재_지주목록.csv"):
        p = os.path.join(WORK, name)
        if os.path.exists(p):
            csvs[name] = next(csv.reader(io.StringIO(open(p, encoding="utf-8-sig").read())))
    mkeys = collections.Counter()
    for mp in glob.glob(os.path.join(FSS, "exam", "*", "*.meta.json")):
        mkeys.update(json.load(open(mp, encoding="utf-8")).keys())
    res = dict(작성=f"{TODAY}(KST) scripts/dart/fix13_D.py — 새 웹 요청 없음(받은 원본만 읽음)",
               목록HTML=len(lists), 상세HTML=len(details), probeHTML=len(probes),
               표머리칸_th=dict(th), 상세화면칸_dt=dt_only, 낱말=[dict(묶음=g, 낱말=w, 수=n) for (g, w), n in sorted(words.items())],
               낱말목록=PUB_WORDS, CSV칸=csvs, meta키=dict(mkeys))
    os.makedirs(FD, exist_ok=True)
    json.dump(res, open(SCANF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if words:
        raise SystemExit("공개일 낱말이 원본에 있음 — md 의 「추출 범위에 없음」을 다시 볼 것: %s" % dict(words))
    if "Last-Modified" in mkeys or any("등록" in k or "게시" in k for k in mkeys):
        raise SystemExit("meta 에 날짜 칸이 있음 — 다시 볼 것")
    return res


def pub_trail(S):
    ths = [k for k in S["표머리칸_th"] if k != "번호"]
    c1 = S["CSV칸"].get("9-5_경영유의공시_전체목록.csv", [])
    return ("받은 목록 HTML %d개(경영유의 공시 전체 72쪽·지주 검색 2쪽, 검사결과제재 지주 검색 2쪽)의 표 머리 칸 「%s」, 검사결과제재 상세 HTML %d개의 칸 「%s」, "
            "화면 안내 HTML %d개, `dart_out/risk13/9-5_경영유의공시_전체목록.csv` 칸 「%s」, 공개안 PDF·HTML 의 .meta.json(응답 머리 날짜 칸 없음) — "
            "낱말 「등록일·게시일·공시일·공개일·작성일·수정일」과 영문 칸 이름(regDt 등) %d개로 찾아 0건(결과 `dart_out/raw/web13/fix13_D/공개일_재확인.json`)"
            % (S["목록HTML"], "·".join(ths), S["상세HTML"], "·".join(S["상세화면칸_dt"]), S["probeHTML"], "·".join(c1), len(PUB_WORDS)))


# ───────────────────────────── 9-2-4 ─────────────────────────────
Q_LABEL = {  # (머리 날짜, 붙일 날짜 종류) — 근거: 각 Q 첫 인용(배포일·제목)의 머리 표, Q6·Q8 은 게시글 줄의 등록일
    "Q1": ("2014-07-31", "(배포일)"),
    "Q2": ("2016-03-30", "(배포일 — 보도 「배포 시부터 즉시」)"),
    "Q3": ("2017-06-28", "(배포일·보도일 같은 날)"),
    "Q4": ("2018-08-01", "(보도일 — 석간; 배포일 2018-07-31)"),
    "Q5": ("2018-12-12", "(배포일; 보도일 2018-12-13 조간)"),
    "Q6": ("2023-03-22", "(게시글 등록일)"),
    "Q7": ("2024-11-06", "(보도일 — 석간; 배포일 2024-11-05)"),
    "Q8": ("2026-03-11", "(게시글 등록일)"),
    "Q9": ("2026-06-29", "(배포일; 보도일 2026-06-30 조간)"),
}
# 재비평 지적 8 — 1절 표 날짜 칸(Q4·Q5·Q7·Q9 는 이미 「… 배포, … 보도」)
P_TAB_HEAD = ("| # | 날짜(배포) | 자료 |", "| # | 날짜(종류는 칸마다 — 배포일·보도일·게시글 등록일) | 자료 |")
P_DATE_CELL = {
    "Q1": ("2014-07-31", "2014-07-31(배포일)"),
    "Q2": ("2016-03-30", "2016-03-30(배포일 — 보도 「배포 시부터 즉시」)"),
    "Q3": ("2017-06-28", "2017-06-28(배포일·보도일 같은 날)"),
    "Q6": ("2023-03-22", "2023-03-22(게시글 등록일 — 보도자료 hwp 머리 표의 배포일·보도일과 같은 날, 아래 note)"),
    "Q8": ("2026-03-11", "2026-03-11(게시글 등록일 — 보도자료 hwp 머리 표의 배포일·보도일과 같은 날, 아래 note)"),
}
P_HWP = {"Q6": "dart_out/raw/web13/fss/press/file/fss_58388_4.hwp.md", "Q8": "dart_out/raw/web13/fss/press/file/fss_214172_4.hwp.md"}
HWP_HEAD_RE = re.compile(r"^\| 보도 \| (\d{4})\.(\d{1,2})\.(\d{1,2})\.\(.\) (\d\d:\d\d) \|.*?\| 배포 \| (\d{4})\.(\d{1,2})\.(\d{1,2})\.\(.\) \|")


def hwp_head(p):
    """받은 hwp 의 hwp2md 글(인용 블록 밖)에서 머리 표 「보도 … | 배포 …」 줄 → 날짜·시각·줄 번호(읽기만)."""
    L = open(p, encoding="utf-8").read().split("\n")
    hs = [(k, m) for k, ln in enumerate(L[:20]) for m in [HWP_HEAD_RE.match(ln)] if m]
    if len(hs) != 1:
        raise SystemExit(f"[fix13_D P] {p}: 머리 표 보도·배포 줄 {len(hs)}개(기대 1)")
    k, m = hs[0]
    g = m.groups()
    return {"줄": k + 1, "보도": "%s-%02d-%02d" % (g[0], int(g[1]), int(g[2])), "시각": g[3], "배포": "%s-%02d-%02d" % (g[4], int(g[5]), int(g[6]))}


def fix_P(d):
    W = R5_WHY
    d.sub("- 검증: 2026-10-07 `python3", "- 검증: 2026-10-08(KST) `python3", "R5", W)
    d.sub("「검증 기록(2026-10-07)」", "「검증 기록(2026-10-08 KST)」", "R5", W)
    d.sub("검증(2026-10-07)", "검증(2026-10-08 KST)", "R5", W, count=2)
    d.sub("(검증 2026-10-07: ", "(검증 2026-10-08 KST: ", "R5", W)
    d.sub("검증 대조(2026-10-07, ", "검증 대조(2026-10-08 KST, ", "R5", W, count=2)
    d.sub("(2026-10-07 15:01 UTC 무렵", "(2026-10-07 15:01 UTC = 2026-10-08 00:01 KST 무렵", "R5", "UTC 시각에 KST 를 함께 적음(요청기록 원장 시각은 KST)")
    vh_rename(d)
    # Q 머리 날짜 종류
    for q, (dt, lab) in Q_LABEL.items():
        i = d.idx(lambda i, ln, q=q, dt=dt: ln.startswith(f"### {q} {dt} "), f"{q} 머리")
        d.set_line(i, d.lines[i].replace(f"### {q} {dt} ", f"### {q} {dt}{lab} ", 1), "R5",
                   "보도자료 날짜 종류가 섞임(보도일·배포일·등록일) — 머리에 종류를 붙임(1절 표 「날짜(배포)」 칸·각 Q 첫 인용의 보도/배포 칸과 대조)")
    # 1절 표 날짜 칸(재비평 지적 8): 칸 머리 「날짜(배포)」인데 Q6·Q8 은 게시글 등록일, Q1~Q3 은 종류 표시 없음 → 칸마다 종류
    W8 = CRIT2 + " 8(R5): 1절 표 「날짜(배포)」 칸에 Q6·Q8 게시글 등록일이 종류 표시 없이 들어 있음 — 칸마다 날짜 종류"
    d.sub(P_TAB_HEAD[0], P_TAB_HEAD[1], "R5", W8, pred=lambda i, ln: ln.startswith(P_TAB_HEAD[0]))
    hh = {q: hwp_head(p) for q, p in P_HWP.items()}
    for q, (old, new) in P_DATE_CELL.items():
        if q in hh and hh[q]["배포"] != old:
            raise SystemExit(f"[fix13_D P] {q} hwp 머리 표 배포일 {hh[q]['배포']} ↔ 게시글 등록일 {old}")
        d.sub(f"| {q} | {old} | ", f"| {q} | {new} | ", "R5", W8, pred=lambda i, ln, q=q: ln.startswith(f"| {q} | "))
    for q in ("Q4", "Q5", "Q7", "Q9"):
        i = d.idx(lambda i, ln, q=q: ln.startswith(f"| {q} | "), f"1절 표 {q} 행")
        c = d.lines[i].split(" | ")[1]
        if not ("배포" in c and "보도" in c):
            raise SystemExit(f"[fix13_D P] 1절 표 {q} 날짜 칸에 배포·보도 표시가 없음: {c}")
    t9 = d.idx(lambda i, ln: ln.startswith("| Q9 | "), "1절 표 Q9 행")
    hw = "; ".join(f"{q} 보도 {h['보도']} {h['시각']}·배포 {h['배포']}(`{P_HWP[q]}` {h['줄']}행)" for q, h in hh.items())
    d.insert_after(t9, ["", "note: 날짜 종류(정합성 보정 2026-10-08 KST — R5): 위 표 「날짜」 칸은 칸마다 종류를 적었다 — Q1·Q2 배포일, Q3 배포일·보도일 같은 날, "
                           "Q4·Q5·Q7·Q9 배포일과 보도일(서로 다른 날이라 둘 다), Q6·Q8 게시글 등록일. 2절 각 Q 머리의 날짜에도 종류를 괄호로 붙였다 — "
                           "Q1·Q2·Q5·Q9 배포일, Q3 배포일·보도일 같은 날, Q4·Q7 보도일(석간 — 배포일은 하루 앞), Q6·Q8 게시글 등록일. 근거: 각 Q 첫 인용(배포일·제목)의 머리 표 「보도」「배포」 칸. "
                           "Q6·Q8 은 인용이 별첨1 PDF 뿐이라 게시글 줄의 등록일을 적었고, 같은 게시글의 보도자료 hwp 머리 표(인용 블록 밖 — hwp2md 글)의 날짜는 "
                           + hw + " — 배포일·보도일 모두 게시글 등록일과 같은 날이다(재비평 지적 8 보정 때 표 칸·이 note 에 줄 번호를 붙임)."],
                   "R5", "1절 표 날짜 칸과 2절 Q 머리 날짜의 종류를 밝힘(Q6·Q8 hwp 머리 표 날짜와 줄 번호)")
    d.sub("1절 날짜순 목록 Q1~Q9(날짜는 각 Q 의 보도·배포일 인용).", "1절 날짜순 목록 Q1~Q9(날짜는 각 Q 의 보도·배포일 인용 — Q6·Q8 은 게시글 등록일, 1절 note).",
          "R5", W8 + " — 지시서 항목 대조 표 근거 칸도 맞춤")
    # R3
    R3 = "우리 글의 「없음」 단정 → 「추출 범위에 없음」+찾은 방법"
    d.sub("## 3. 받아 보았으나 ORSA 낱말 없음(2차 확인 대상)", "## 3. 받아 보았으나 ORSA 낱말은 추출 범위에 없음(첨부 글 정규식 검색 — 2차 확인 대상)", "R3", R3)
    d.sub("「받아 보았으나 ORSA 낱말 없음」", "「받아 보았으나 ORSA 낱말은 추출 범위에 없음」", "R3", "3절 제목을 바꾼 것에 맞춤", count=2)
    d.sub("「도입」으로 쓴 것인지는 자료에 설명 없음 — 판단 보류)",
          "「도입」으로 쓴 것인지에 대한 설명은 이 자료에서 추출 범위에 없음(찾은 곳: 2017-06-28 보도자료 hwp 글) — 판단 보류)", "R3", R3)
    d.sub("4.28 발령분의 관계는 자료에 설명 없음, 판단 보류)",
          "4.28 발령분의 관계에 대한 설명은 이 자료에서 추출 범위에 없음(찾은 곳: 2016-03-30 보도자료 hwp 글), 판단 보류)", "R3", R3)
    d.sub("첨부에도 ORSA 낱말이 없었다.", "첨부에서도 ORSA 낱말은 추출 범위에 없었다(3절 정규식으로 첨부 글 검색).", "R3", R3)
    d.sub("세칙 4월 예고 글은 없음(87205", "세칙 4월 예고 글은 추출 범위에 없음(87205", "R3", R3)
    d.sub("— 제목에 세칙·ORSA 없음.", "— 6건 제목에서 세칙·ORSA 낱말은 추출 범위에 없음.", "R3", R3)
    d.sub("받은 첨부에 ORSA 낱말 없음(3절)", "받은 첨부에서 ORSA 낱말은 추출 범위에 없음(3절 정규식)", "R3", R3)
    d.sub("실패 — 새 ORSA 언급 없음(추출 범위에 없음)", "실패 — 새 ORSA 언급은 추출 범위에 없음", "R3", R3)


def record_P(d, n):
    return ["", "### 정합성 보정(2026-10-08)", "",
            "비평 결과(`dart_out/risk13/critic13.json` 의 gaps·contradictions)에 맞춰 날짜 표지·note 만 고침 — 원문 인용(코드 블록) 줄은 그대로(34개). "
            f"스크립트 `scripts/dart/fix13_D.py`(기준 사본 = 커밋 {BASE} 의 이 파일, `dart_out/raw/web13/fix13_D/pre/`; 언제나 그 사본에서 다시 만듦), "
            f"고친 곳 전부(기준 사본 줄·전·후·규칙·이유)는 `dart_out/raw/web13/fix13_D/fix_log.json`(이 파일 {n}곳). 대조: `python3 -I scripts/dart/fix13_D.py check`.",
            "재생성 순서: `python3 scripts/dart/verify13_web.py fix`(검증 보정 — 다시 돌리면 이 보정이 지워짐) → `python3 -I scripts/dart/fix13_D.py`.",
            "",
            "- R5 날짜 종류 — 2절 Q 머리 날짜 9곳에 종류를 붙임(전: 「Q4 2018-08-01」「Q7 2024-11-06」은 보도일, 「Q5 2018-12-12」「Q9 2026-06-29」는 배포일인데 표지 없이 섞임 → 후: "
            + ", ".join(f"{q} {dt}{lab}" for q, (dt, lab) in Q_LABEL.items())
            + "). 1절 표 아래에 날짜 종류 note 를 더함(근거: 각 Q 첫 인용의 「보도」「배포」 칸, Q6·Q8 은 게시글 등록일).",
            "- R5 날짜 라벨 — 머리·5절 note 의 검증 날짜 2026-10-07 → 2026-10-08 KST(검증은 커밋 8c118c8·496ddc4 — UTC 로도 2026-10-08), 절 제목 「검증 기록(2026-10-07)」 → 「검증 기록(2026-10-08 KST)」, "
            "접속 실패 시각 「2026-10-07 15:01 UTC」에 「= 2026-10-08 00:01 KST」를 덧붙임. 인용 머리의 수집 시각(fetched_at, +09:00)과 요청기록 csv 시각은 원래 KST 라 그대로. 고친 곳(전·후) 소절 안의 날짜는 그때 기록이라 그대로.",
            "- R3 낱말 — 3절 제목 「받아 보았으나 ORSA 낱말 없음」 → 「받아 보았으나 ORSA 낱말은 추출 범위에 없음(첨부 글 정규식 검색 — …)」(가리키는 곳 2곳도), 5절 note 「자료에 설명 없음」 2곳·「ORSA 낱말이 없었다」 1곳, "
            "반박 시도 표 「세칙 4월 예고 글은 없음」「제목에 세칙·ORSA 없음」「받은 첨부에 ORSA 낱말 없음」「새 ORSA 언급 없음」 → 추출 범위에 없음 + 찾은 곳. "
            "그대로 둔 없음: robots 판정 「제한 없음」, 이 작업의 표기(글자 수정 없음·빠진 항목 없음·글자를 고친 인용은 없다), 대조 결과 분류 이름, 「그런 파일은 없음」(저장소 파일 이름 확인 — verify13_web.py 가 이 글을 찾음), "
            "반박 5 「두 PDF 의 pypdf 글에 없다」(그 PDF 글 전체를 대조 스크립트가 다시 셈).",
            "- R2 — 자료 묶음 Q1~Q9 의 조 번호는 note·1절 표에 모두 「(판단)」으로 있음(지시서 9-2 에 조 번호 없음) — 고칠 곳 없음. R4 — 인용 34개 모두 블록 바로 앞 「인용 — … · 게시글 URL · PDF 쪽 · 수집 …」 줄 — 고칠 곳 없음.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_web.py`): 맨 끝 절·지시서 항목 대조 표를 찾을 때 「검증 기록(2026-10-08 KST)」 절 제목도 받아들임. 다른 대조 규칙은 그대로이며 보정 뒤 인자 없이 돌려 문제 0(exit 0).",
            "",
            "#### 재비평 보정(2026-10-08 KST — `dart_out/risk13/critic13_2.json` new_issues 8)",
            "",
            "- R5 1절 표 날짜 칸 — 칸 머리 「날짜(배포)」 → 「" + P_TAB_HEAD[1].split(" | ")[1] + "」. 종류 표시가 없던 칸: "
            + ", ".join(f"{q} 「{o}」 → 「{n}」" for q, (o, n) in P_DATE_CELL.items())
            + ". Q4·Q5·Q7·Q9 칸(「… 배포, … 보도」)은 그대로. 1절 note 를 이에 맞춰 다시 씀 — 전: 「위 표 「날짜(배포)」 칸은 배포일(보도일이 다르면 함께 적음)」(Q6·Q8 은 등록일이라 맞지 않았음) → 후: 칸마다 종류, "
            "Q6·Q8 보도자료 hwp 머리 표의 보도·배포 날짜와 그 줄 번호(받은 hwp 의 hwp2md 글 `fss_58388_4.hwp.md`·`fss_214172_4.hwp.md` 6행 — fix13_D.py 가 그 줄을 읽어 등록일과 같은지 확인). "
            "검증 기록 2 지시서 항목 대조 표 근거 칸 「날짜는 각 Q 의 보도·배포일 인용」에 「— Q6·Q8 은 게시글 등록일, 1절 note」를 덧붙임.",
            "- R1 — 이 파일의 「받은 것」 상태 칸은 검증 기록 2 지시서 항목 대조 표뿐(4행 모두 받은 글 — 도입 발표 원문과 그 날짜(Q1·Q2·Q5·Q9 등 첫 인용의 배포·보도 칸)·로드맵·시행 시기·유예 허용이 인용 블록에 있음; "
            "Q6·Q8 은 업무설명회 별첨이라 날짜는 게시글 등록일) — 세 단계 안이라 상태 낱말은 그대로. 3절 표(받아 본 첨부)·반박 표 「결과」 칸은 받은 것 상태 칸이 아님."]


# ───────────────────────────── 9-5 ─────────────────────────────
OLD_SCOPE = "지시서의 지주(KB·신한·하나·우리·NH농협·iM(DGB)·BNK·JB·메리츠·한국투자) 밖의 금융지주 건은 이 기간 목록에 없었다."
NEW_SCOPE = ("지시서 9-5 는 대상 지주를 정하지 않음 — 이 파일은 금감원 공개 자료(위 경영유의사항 등 공시 목록, 5절 검사결과제재 목록)에서 금융지주회사 전체를 훑었고, "
             "골라진 18건의 지주는 KB·신한·하나·우리·NH농협·iM(DGB)·BNK·JB·메리츠·한국투자 10곳이다. 9-4 대상 8개사(메리츠·한국투자·KB·신한·하나·우리·iM·NH)에 없는 BNK·JB 도 포함했다(판단). "
             "그 밖의 금융지주회사 이름의 건은 이 기간 목록에서 추출 범위에 없음(전체 목록 715행 기관명 「금융지주」「지주회사」「홀딩스」「Holdings」 검색 — 검증 기록 3절 #3).")


# 재비평 보정 — R2 꼴(9-3 과 같은 「조 번호 해당 없음(판단: …)」), R1 상태 칸
CH5_REASON = "판단: 규제자본비율 산출 등 — 제5장 주제이나 한 조에 바로 닿지 않음"
CH5_NOART = "조 번호 해당 없음(%s)" % CH5_REASON                                    # 9-5 4절 색인 칸
CH5_TITLE = ("제5장 내부자본 적정성 평가 및 관리(36조~49조) 가운데 37~49조 주제 — 특정 조 없음(판단)",      # CSV 조제목 칸(전)
             "제5장 내부자본 적정성 평가 및 관리(36조~49조) 가운데 37~49조 주제 — " + CH5_NOART)         # (후) = verify13_web.art_title_cell
E_CITE = ("| 근거로 든 조문 | 받은 글 | ", "넓힌 낱말로도 없는 지적은 「추출 범위에 없음」 |",
          "찾은 방법: 지적 글 전체를 「｢…｣ 제N조」 꼴로 찾고, 그 꼴이 없는 지적은 「제N조」(가림 기호 조 번호 포함)·「§N」·「<별표 N>」·「｢…｣」 꼴로 넓혀 찾음"
          "(검증 기록 3절 #5) — 넓힌 꼴로도 찾지 못한 %(none)d개는 「넓혀 찾은 조문·규정 표기」 줄·CSV 칸에 「추출 범위에 없음(…)」 |")
E_CITE_ST = "일부(리스크관련 지적 가운데 「｢…｣ 제N조」 꼴 인용 %(cite)d개·넓혀 찾은 조문·규정 표기 %(wide)d개 있음, 나머지 %(none)d개는 근거 조문 추출 범위에 없음)"
E_REVIEW = ("| 리스크관리 관련 판정 누락 재검토 | 판단 | 1-1 표(판정 바꿈 3건·조 더함 4건)와 N 으로 둔 지적 목록 |",
            "| 리스크관리 관련 판정 누락 재검토 | 받은 글 | 1-1 표(판정 바꿈 3건·조 더함 4건 — 바꾼 3건의 지적 본문은 위 문서 절 인용 블록)와 N 으로 둔 지적 목록. "
            "note: 판정(Y·경계·N)과 조 대응은 모두 (판단) |")


def cite_counts():
    """기준 사본 CSV 에서 리스크관련(판단 Y·경계) 지적의 근거 조문: 「｢…｣ 제N조」 꼴 인용 / 넓혀 찾은 표기 / 둘 다 추출 범위에 없음."""
    rows = list(csv.DictReader(io.StringIO(open(pre_path(CSV_E), "rb").read().decode("utf-8-sig"))))
    risk = [r for r in rows if r["리스크관련(판단)"] != "N"]
    cite = sum(1 for r in risk if r["인용조문"])
    none = sum(1 for r in risk if not r["인용조문"] and r["넓혀찾은_조문표기(검증)"].startswith("추출 범위에 없음"))
    nc = dict(risk=len(risk), cite=cite, wide=len(risk) - cite - none, none=none)
    if (nc["risk"] - nc["cite"], nc["none"]) != (65, 27):          # md 검증 기록 3절 #5 · 00_목록 4-1 의 65·27
        raise SystemExit(f"[fix13_D E] 근거 조문 수가 검증 기록 3절 #5 와 다름: {nc}")
    return nc


def fix_E(d, S, docs):
    W = R5_WHY
    d.sub("- 검증: 2026-10-07 `python3", "- 검증: 2026-10-08(KST) `python3", "R5", W)
    d.sub("「검증 기록(2026-10-07)」", "「검증 기록(2026-10-08 KST)」", "R5", W)
    d.sub("검증(2026-10-07)", "검증(2026-10-08 KST)", "R5", W, count=4)
    d.sub("(검증 2026-10-07 — 「제N조」", "(검증 2026-10-08 KST — 「제N조」", "R5", W, count=110)
    vh_rename(d)
    # 머리 「범위」 — 지시서 지주 목록(사실과 다름)
    d.sub(OLD_SCOPE, NEW_SCOPE, "R2·R3", "지시서 9-5 에는 지주 목록이 없고 9-4 대상 8개사에는 BNK·JB 가 없음(critic13 contradictions) — 사실대로 고침")
    d.sub("| 3 | 지시서 목록 밖 금융지주 건 |", "| 3 | 지시서 목록 밖 금융지주 건(정합성 보정: 지시서 9-5 에는 지주 목록이 없음 — 머리 「범위」 줄) |", "R2·R3",
          "반박 표의 주장 칸이 없는 지시서 목록을 전제함 — 바로잡는 말을 덧붙임")
    # 공개일(지시서 항목) — 다시 확인
    trail = pub_trail(S)
    i7 = d.idx(lambda i, ln: ln.startswith("- 「공개일」: "), "머리 「공개일」 줄")
    d.set_line(i7, d.lines[i7] + " → 정합성 보정(2026-10-08 KST) 다시 확인: 공개(게시)일 칸은 추출 범위에 없음 — 확인한 원본·칸 이름은 1절 note.", "지시서 공개일",
               "critic13: 9-5 공개일을 받지 못한 것으로 적음 — 받은 원본을 다시 훑어 칸 이름을 적음")
    s2 = d.idx(lambda i, ln: ln.startswith("## 2. 비은행지주"), "2절 머리")
    t18 = d.idx(lambda i, ln: i < s2 and ln.startswith("| 20260723 | 하나금융지주 |"), "1절 표 끝 행")
    d.insert_after(t18, ["", "note: 공개일(지시서 9-5 1번 항목, 정합성 보정 2026-10-08 KST 다시 확인) — 18건 모두 추출 범위에 없음. 확인한 원본·칸 이름: " + trail
                         + ". 위 표와 문서 절 머리의 날짜는 목록의 「제재조치요구일」(날짜 종류: 제재조치요구일)이고, 문서 안 「조치일」「제재조치일」은 문서 머리 인용에 있다. "
                           "CSV 에는 「" + PUB_COL + "」 칸(「추출 범위에 없음(…)」)을 더함. 새 웹 요청은 하지 않음(받은 목록·상세 화면에 공개일 칸 자체가 없어 같은 경로를 다시 받아도 칸이 생기지 않음 — 판단)."],
                   "지시서 공개일", "공개일 다시 확인 결과와 날짜 종류")
    d.sub("| 공개일 | 추출 범위에 없음 | 찾은 방법: 목록·상세 HTML 칸과 「등록일·게시일·공시일·공개일·작성일」 낱말(0건)",
          "| 공개일 | 추출 범위에 없음 | 찾은 방법: 목록·상세 HTML 칸과 「등록일·게시일·공시일·공개일·작성일」 낱말(0건; 정합성 보정 2026-10-08 KST 다시 확인 — 목록 HTML %d개·상세 HTML %d개 표 머리·칸 이름, 전체목록 CSV 칸, 낱말 %d개 0건 — 1절 note)"
          % (S["목록HTML"], S["상세HTML"], len(PUB_WORDS)), "지시서 공개일", "다시 확인한 범위를 덧붙임")
    d.sub("- 공개일은 게시판에 칸이 없어 채우지 못했다(제재조치요구일·문서 안 조치일만).",
          "- 공개일은 받은 목록·상세 화면(HTML)과 목록 CSV 에 공개(게시)일 칸이 없어 추출 범위에 없음(제재조치요구일·문서 안 조치일만 — 정합성 보정 때 다시 확인, 1절 note).",
          "R3·지시서 공개일", "「칸이 없어 채우지 못했다」 → 추출 범위에 없음 + 찾은 곳")
    # R3
    R3 = "우리 글의 「없음」 단정 → 「추출 범위에 없음」+찾은 방법"
    n_a = d.count("문서 글에 「｢…｣ 제N조」 꼴 인용 없음(아래 넓혀 찾은 표기 참조)", pred=lambda i, ln: ln.startswith("- 근거로 든 조문"))
    d.sub("문서 글에 「｢…｣ 제N조」 꼴 인용 없음(아래 넓혀 찾은 표기 참조)",
          "문서 글에서 「｢…｣ 제N조」 꼴 인용은 추출 범위에 없음(문서 글 전체를 그 꼴로 찾음 — 아래 넓혀 찾은 표기 참조)", "R3", R3, count=65,
          pred=lambda i, ln: ln.startswith("- 근거로 든 조문"))
    d.sub("추출 범위에 없음(이 낱말들로 찾았으나 없음)", "추출 범위에 없음(이 꼴들로 이 지적 글 전체를 찾음)", "R3", "괄호 안 「없음」 단정을 찾은 방법으로", count=27)
    d.sub("규제자본비율(BIS·레버리지) 산출 오류는 모범규준에 바로 대응하는 조가 없어 「37~49조(제5장) 주제」로 적었다.",
          "규제자본비율(BIS·레버리지) 산출 오류는 모범규준(2016.8.1판) 조 제목·전문에서 바로 대응하는 조가 추출 범위에 없어(조목록.csv·9-4_모범규준_원문.md 5장 대조, 판단) 「37~49조(제5장) 주제」로 적었다.",
          "R3", R3)
    d.sub("— 특정 조 없음(규제자본비율 산출 등) |", "— " + CH5_NOART + " |", "R2·R3",
          "조가 없다는 판단 → 조 번호 해당 없음(판단: 이유) — 재비평 보정 때 「특정 조 번호 해당 없음(판단: 규제자본비율 산출 등)」을 9-3 과 같은 꼴로(「특정」은 이유 안으로)")
    # R1 — 지시서 항목 대조 표 상태 칸(재비평 지적 9)
    W9 = CRIT2 + " 9(R1): 지시서 항목 대조 표 상태 칸을 세 단계(받은 글 / 일부(…) / 추출 범위에 없음)로 — 판단은 상태 칸이 아니라 note"
    nc = cite_counts()
    i = d.idx(lambda i, ln: ln.startswith(E_CITE[0]), "지시서 항목 「근거로 든 조문」 행")
    if not d.lines[i].endswith(E_CITE[1]):
        raise SystemExit("[fix13_D E] 「근거로 든 조문」 행 근거 칸 끝 글이 다름")
    d.set_line(i, E_CITE[0].replace("| 받은 글 |", "| " + E_CITE_ST % nc + " |") + d.lines[i][len(E_CITE[0]):-len(E_CITE[1])] + E_CITE[2] % nc, "R1",
               W9 + " — 「｢…｣ 제N조」 꼴 인용이 없는 리스크관련 지적 65개 가운데 27개는 넓힌 꼴로도 근거 조문이 추출 범위에 없음(검증 기록 3절 #5) → 일부")
    d.sub(E_REVIEW[0], E_REVIEW[1], "R1", W9 + " — 「판단」 → 받은 글 + note(판단)")

    d.sub("넓힌 낱말로도 없는 행 50개", "넓힌 낱말로도 추출 범위에 없는 행 50개", "R3", R3)
    # R2·R4 — 인용 블록마다(문서 머리 19 · 지적 본문 110 · 반박 발췌 6)
    kinds = collections.Counter()
    blocks = [i for i, ln in enumerate(d.lines) if ln == "```text"]
    for s in blocks:
        kind = page = sha = None
        hline = None
        for k in range(s - 1, -1, -1):
            ln = d.lines[k]
            if kind is None and (ln.startswith("#### [") or ln.startswith("문서 머리") or ln.startswith("인용 —")):
                kind = "k" if ln.startswith("#### [") else "head" if ln.startswith("문서 머리") else "refute"
                pm = re.findall(r"p\.\d+(?:,p\.\d+)*", ln)
                page = pm[-1] if pm else None
                hline = k
            m = re.search(r"sha256 ([0-9a-f]{64})", ln)
            if m:
                sha = m.group(1)
                break
        if not (kind and page and sha in docs) or d.lines[s - 1] != "":
            raise SystemExit(f"[fix13_D E] 줄 {s + 1} 블록의 머리·쪽·sha256 을 찾지 못함")
        kinds[kind] += 1
        doc = docs[sha]
        board = "금감원 검사결과제재 공개안" if doc["kind"] == "sanc" else "금감원 경영유의사항 등 공시 공개안"
        src = f"인용 출처: [{board} 「{doc['name']}」 · {doc['url']} · {page} · 수집 {kst_day(doc['fetched'])}]"
        add = []
        if kind == "refute":
            m = re.search(r"연결 (\d+)조\(([^)]*)\)\(판단\)", d.lines[hline])
            if not m:
                raise SystemExit(f"[fix13_D E] 반박 인용 머리에 연결 조 없음: 줄 {hline + 1}")
            add.append(f"- 모범규준 조: {m.group(1)}조({m.group(2)})(판단 — 반박 시도 6 에서 연결; 이 지적 전체의 조는 위 문서 절 [k] 머리)")
        if kind == "head":
            h = hline
            if d.lines[h - 1] != "" or not d.lines[h - 2].startswith("- "):
                raise SystemExit(f"[fix13_D E] 문서 머리 앞 줄 꼴이 다름: 줄 {h + 1}")
            d.insert_after(h - 2, [f"- 모범규준 조: {NOART} — 문서 머리 인용(조치일·조치내용 건수)은 특정 조에 닿지 않음; 항목별 조(판단)는 아래 항목 표·[k] 머리"],
                           "R2", "문서 머리 인용 19개(조치내용 건수)에 조 번호 칸이 없었음(critic13 gaps)")
        d.insert_after(s - 1, add + [src, ""], "R4" if kind != "refute" else "R2·R4",
                       "인용 블록마다 출처 줄(문서명 줄임 · URL · 쪽 · 수집일) — 문서 머리 「- 문서:」 줄 출처를 블록마다 되풀이" if kind != "refute"
                       else "반박 인용의 조(글 안에만 있던 「연결 N조」)를 조 번호 칸으로, 출처 줄(URL·수집일 더함)")
    if dict(kinds) != {"head": 19, "k": 110, "refute": 6}:
        raise SystemExit(f"[fix13_D E] 블록 종류 수가 다름: {dict(kinds)}")
    return n_a, kinds


def record_E(d, n, S, kinds):
    nc = cite_counts()
    return ["", "### 정합성 보정(2026-10-08)", "",
            "비평 결과(`dart_out/risk13/critic13.json` 의 gaps·contradictions·items)에 맞춰 표지·출처 줄·note 만 고침 — 원문 인용(코드 블록 135개) 줄은 그대로. "
            f"스크립트 `scripts/dart/fix13_D.py`(기준 사본 = 커밋 {BASE} 의 이 파일과 CSV, `dart_out/raw/web13/fix13_D/pre/`; 언제나 그 사본에서 다시 만듦), "
            f"고친 곳 전부(기준 사본 줄·전·후·규칙·이유)는 `dart_out/raw/web13/fix13_D/fix_log.json`(이 파일 {n}곳). 대조: `python3 -I scripts/dart/fix13_D.py check`.",
            "재생성 순서: `python3 scripts/dart/verify13_web.py fix`(검증 보정 — 다시 돌리면 이 보정이 지워짐) → `python3 -I scripts/dart/fix13_D.py`.",
            "",
            "- 머리 「범위」 — 전: 「지시서의 지주(KB·신한·하나·우리·NH농협·iM(DGB)·BNK·JB·메리츠·한국투자) 밖의 금융지주 건은 이 기간 목록에 없었다.」 → 후: 지시서 9-5 는 대상 지주를 정하지 않음 — "
            "금감원 공개 자료에서 금융지주회사 전체를 훑었고 9-4 대상 8개사에 없는 BNK·JB 도 포함(판단), 그 밖의 금융지주회사 건은 추출 범위에 없음 + 찾은 방법. 반박 표 #3 주장 칸에도 바로잡는 말을 덧붙임.",
            "- 지시서 항목 「공개일」 — 받은 원본을 다시 훑음(새 웹 요청 0건): " + pub_trail(S) + ". 결과는 그대로 추출 범위에 없음 — 1절 표 아래 note(날짜 종류: 표·절 머리 날짜는 제재조치요구일), "
            "머리 「공개일」 줄·지시서 항목 대조 표·남은 문제 줄에 다시 확인한 범위를 덧붙이고, CSV 에 「" + PUB_COL + "」 칸(235행 모두 「추출 범위에 없음(…)」)을 더함.",
            f"- R4 출처 줄 — 인용 블록 135개(문서 머리 {kinds['head']} · 지적 본문 {kinds['k']} · 검증 기록 3절 반박 발췌 {kinds['refute']}) 모두 블록 바로 앞에 「인용 출처: [공개안 이름 「원파일명」 · 다운로드 URL · 쪽 · 수집 2026-10-08(KST)]」 줄을 끼움 "
            "(전: 문서 머리 「- 문서:」 줄에 파일명·URL·sha256·수집, [k] 머리에 쪽 — 묶음 출처). 쪽은 [k] 머리·문서 머리·반박 인용 머리의 쪽 표기 그대로(verify13_web.py 가 원본에서 다시 셈).",
            f"- R2 조 번호 칸 — 문서 머리 인용 {kinds['head']}개(조치일·조치내용 건수) 앞에 「- 모범규준 조: {NOART} — …」 줄, 반박 발췌 {kinds['refute']}개에 글 안에만 있던 연결 조를 "
            "「- 모범규준 조: 5조(위험관리 원칙)(판단 — …)」·「8조(이사회)(판단 — …)」 줄로. 4절 색인 「37~49조(제5장) 주제」 행의 「특정 조 없음(규제자본비율 산출 등)」 → 「" + CH5_NOART + "」(재비평 보정 때 9-3 과 같은 꼴로 다시 씀 — 아래). "
            "지적별 조(표·[k] 머리·색인)는 모두 이미 (판단) — 고칠 곳 없음.",
            "- R3 낱말 — 「근거로 든 조문」 줄 65곳 「문서 글에 「｢…｣ 제N조」 꼴 인용 없음」 → 「… 꼴 인용은 추출 범위에 없음(문서 글 전체를 그 꼴로 찾음 …)」, 「넓혀 찾은 조문·규정 표기」 줄 27곳 "
            "「추출 범위에 없음(이 낱말들로 찾았으나 없음)」 → 「추출 범위에 없음(이 꼴들로 이 지적 글 전체를 찾음)」, 판정 기준 줄 「바로 대응하는 조가 없어」, 남은 문제 「공개일 … 칸이 없어」, 반박 5 「넓힌 낱말로도 없는 행」. "
            "CSV 「넓혀찾은_조문표기(검증)」 50행 「추출 범위에 없음(넓힌 낱말로도 없음)」 → 「추출 범위에 없음(넓힌 낱말로 지적 글 전체를 찾음)」. "
            "그대로 둔 없음: 「이 문서에는 리스크관련(판단 Y·경계) 항목이 없다」(이 작업의 판정 결과), robots·로그인 화면 표기, 「(구분 표지 없음)」(문서 글 관찰 — CSV 와 같은 글), "
            "11조 ①이 2016.8.1판에 없다는 note(전문을 옮긴 원문의 조·항 구성), 검증 기록 1절 고친 곳(전·후)·대조 결과 분류 이름(그때 기록). CSV 조제목 칸 「특정 조 없음(판단)」은 재비평 보정에서 고침(아래).",
            "- R5 날짜 라벨 — 머리·note 의 검증 날짜 2026-10-07 → 2026-10-08 KST(머리 「- 검증:」 줄 2곳·note 4곳), 「넓혀 찾은 조문·규정 표기(검증 2026-10-07 — …)」 110곳 → 「(검증 2026-10-08 KST — …)」, 절 제목 「검증 기록(2026-10-07)」 → 「검증 기록(2026-10-08 KST)」, "
            "CSV 「검증메모」 7행 「검증 2026-10-07(판단)」 → 「검증 2026-10-08 KST(판단)」. 수집 시각(fetched_at, +09:00)·요청기록 csv 시각은 원래 KST 라 그대로.",
            "- R1 — 지시서 항목 대조 표 상태 칸: 처음 보정 때는 「받은 글 / 추출 범위에 없음 + 찾은 방법 / 판단」 꼴이라 고칠 곳 없다고 보았으나 재비평에서 세 단계 밖 낱말이 지적됨 — 아래 재비평 보정.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_web.py`): 맨 끝 절·지시서 항목 대조 표를 찾을 때 「검증 기록(2026-10-08 KST)」 절 제목도 받아들임. 「인용 출처:」·「- 모범규준 조:」 줄은 기존 규칙(블록 위 「#### [」·「문서 머리」·「인용 —」 줄의 쪽, 위쪽 첫 sha256)을 바꾸지 않음. "
            "다른 대조 규칙은 그대로이며 보정 뒤 인자 없이 돌려 문제 0(exit 0).",
            "",
            "#### 재비평 보정(2026-10-08 KST — `dart_out/risk13/critic13_2.json` new_issues 9 + 연관)",
            "",
            "- R1 검증 기록 2 「지시서 항목 대조」 표 상태 칸 — 「근거로 든 조문」 전: 「받은 글」(근거 칸 끝 「넓힌 낱말로도 없는 지적은 「추출 범위에 없음」」) → 후: 「" + (E_CITE_ST % nc) + "」, "
            "근거 칸 끝을 「찾은 방법: …(검증 기록 3절 #5) — 넓힌 꼴로도 찾지 못한 %d개는 … 「추출 범위에 없음(…)」」으로(수는 CSV 「인용조문」·「넓혀찾은_조문표기(검증)」 칸에서 셈 — 00_목록 4-1 의 65개 중 27개와 같음). " % nc["none"]
            + "「리스크관리 관련 판정 누락 재검토」 전: 「판단」 → 후: 「받은 글」(근거 칸에 「바꾼 3건의 지적 본문은 위 문서 절 인용 블록」과 「note: 판정(Y·경계·N)과 조 대응은 모두 (판단)」). "
            "나머지 6행(지주 이름·지적 제목·요지·2022년 이후 범위·비은행지주 따로 표시 = 받은 글, 공개일 = 추출 범위에 없음 + 찾은 방법)은 세 단계 안이라 그대로. "
            "이 파일의 다른 표(1절 요약·문서별 항목 표·4절 색인·5절 검사결과제재·1-1 판정 재검토 표·3절 반박 표 「결과」 칸)는 받은 것 상태 칸을 두지 않은 표라 해당 없음.",
            "- R2 꼴 — CSV `dart_out/risk13/9-5_검사결과_목록.csv` 「모범규준_조제목(2016.8.1판)」 칸 6행 전: 「" + CH5_TITLE[0] + "」 → 후: 「" + CH5_TITLE[1] + "」, "
            "4절 색인 「37~49조(제5장) 주제」 행 조 제목 칸 전(처음 보정): 「… — 특정 조 번호 해당 없음(판단: 규제자본비율 산출 등)」 → 후: 「… — " + CH5_NOART + "」(9-3 md·CSV 의 「조 번호 해당 없음(판단: 이유)」와 같은 꼴). "
            "같은 뜻 칸 전수: 이 파일 본문·표에서 「대응 조 없음」「특정 조 없음」 꼴은 이 두 곳뿐(검증 기록 1절 고친 곳 표 안의 옛 글은 그때 기록이라 그대로). 지적별 「37~49조(제5장) 주제(판단)」 표지는 조 범위 표지라 그대로.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_web.py`): 지시서 항목 상태 칸에 「일부(」도 받아들이고 상태 칸에 「추출 범위에 없음」이 들어 있으면 근거 칸에 「찾은 방법」을 요구(전: 「추출 범위에 없음」으로 시작할 때만), "
            "`art_title_cell` 이 내는 CSV 조제목 칸 글을 새 꼴로(fix 모드도 같은 글을 씀). 보정 뒤 인자 없이 돌려 문제 0(exit 0)."]


def fix_csv(S):
    raw = open(pre_path(CSV_E), "rb").read()
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    cols = list(rows[0].keys())

    def dump(rs, cs):
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=cs, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rs)
        return ("﻿" + b.getvalue()).encode("utf-8")
    if dump(rows, cols) != raw:
        raise SystemExit("[fix13_D CSV] csv 모듈로 다시 쓴 바이트가 기준 사본과 다름 — 칸 더하기를 멈춤")
    n1 = n2 = n3 = 0
    for k, r in enumerate(rows, 2):
        v = r["검증메모"]
        if "검증 2026-10-07(판단)" in v:
            r["검증메모"] = v.replace("검증 2026-10-07(판단)", "검증 2026-10-08 KST(판단)")
            LOG.append(dict(파일=CSV_E, 줄_기준사본=k, 전=v, 후=r["검증메모"], 규칙="R5", 이유="검증메모 날짜 라벨 KST(" + R5_WHY + ")"))
            n1 += 1
        v = r["넓혀찾은_조문표기(검증)"]
        if v == "추출 범위에 없음(넓힌 낱말로도 없음)":
            r["넓혀찾은_조문표기(검증)"] = "추출 범위에 없음(넓힌 낱말로 지적 글 전체를 찾음)"
            LOG.append(dict(파일=CSV_E, 줄_기준사본=k, 전=v, 후=r["넓혀찾은_조문표기(검증)"], 규칙="R3", 이유="괄호 안 「없음」 단정을 찾은 방법으로"))
            n2 += 1
        v = r["모범규준_조제목(2016.8.1판)"]
        if v == CH5_TITLE[0]:
            r["모범규준_조제목(2016.8.1판)"] = CH5_TITLE[1]
            LOG.append(dict(파일=CSV_E, 줄_기준사본=k, 전=v, 후=CH5_TITLE[1], 규칙="R2",
                            이유=CRIT2 + " 연관(R2 꼴): 「… 특정 조 없음(판단)」 → md 와 같은 꼴 「조 번호 해당 없음(판단: 이유)」(9-5 4절 색인 칸과 같은 글)"))
            n3 += 1
        r[PUB_COL] = ("추출 범위에 없음(목록 HTML 표 머리 칸 「일련번호·제재대상기관·제재조치요구일·제재조치요구내용·관련부서·조회수」·검사결과제재 상세 HTML 칸·목록 CSV 칸에 "
                      "공개(게시)일 칸 없음 — 9-5 md 1절 note, dart_out/raw/web13/fix13_D/공개일_재확인.json)")
    if (n1, n2, n3) != (7, 50, 6):
        raise SystemExit(f"[fix13_D CSV] 바꾼 칸 수가 다름: 검증메모 {n1}(기대 7) · 넓혀찾은 {n2}(기대 50) · 조제목 {n3}(기대 6)")
    cols2 = cols + [PUB_COL]
    LOG.append(dict(파일=CSV_E, 줄_기준사본="1(머리)", 전=",".join(cols), 후=",".join(cols2), 규칙="지시서 공개일",
                    이유="지시서 9-5 「공개일」 — 건마다 추출 범위에 없음(확인한 원본·칸 이름) 칸을 더함(235행)"))
    open(CSV_E, "wb").write(dump(rows, cols2))
    return len(rows)


# ───────────────────────────── 9-3 RAAS ─────────────────────────────
RA = {
    "toc": ("대응 조 없음 — 목차·번호 체계(자료 위치 안내)",
            "조 번호 해당 없음(판단: 목차·번호 체계 — 자료 위치 안내라 특정 조에 닿지 않음)"),
    "s3": ("편입 문장은 대응 조 없음 — 문장별 조는 CSV 칸",
           "편입 문장은 조 번호 해당 없음(판단: 대주주 지원 가능성·경영개선 계획의 자회사 편입은 모범규준 조 주제와 겹치지 않음) — 문장별 조는 CSV 칸"),
    "grp": ("「그룹」 문단(118·336행)은 대응 조 없음",
            "「그룹」 문단(118·336행)은 조 번호 해당 없음(판단: 등급구간·표본 추출의 「그룹」 — 금융그룹 뜻 아님)"),
    "s6": ("그 밖의 문장은 대응 조 없음(판단)", "그 밖의 문장은 조 번호 해당 없음(판단: 문장별 이유는 CSV 조 칸)"),
}


R_REQ = [  # (행 머리, 전 상태·근거 앞부분, 후, 행에 있어야 할 글) — 재비평 지적 9
    ("| 9-3-3 「금융지주회사」 문장과 항목 번호 | ", "받은 글 + 본문 추출 범위에 없음 | ",
     "일부(별첨 보험업감독규정 2문장 있음, 매뉴얼 본문 Ⅰ~Ⅳ장 문장은 추출 범위에 없음) | ", "| 받은 글 2문장(3-32·3-33, 별첨 보험업감독규정) · 매뉴얼 본문(Ⅰ~Ⅳ장, 1~1402행) 찾은 방법: "),
    ("| 9-3-3 「지주」 문장과 항목 번호 | ", "받은 글 + 본문 추출 범위에 없음 | ",
     "일부(별첨 보험업감독규정 2문장 있음 — 모두 「금융지주회사」 안, 매뉴얼 본문 Ⅰ~Ⅳ장 문장은 추출 범위에 없음) | ", "| 받은 글 2문장(3-32·3-33 — 모두 「금융지주회사」 안) · 본문 찾은 방법: "),
    ("| 끝에 낼 것 — 모범규준 조 번호 | ", "판단 | 지시서 9-3 에는 조 번호 없음 → 5절 표(제목 바로잡음)·5-1절 자료 묶음별 조·CSV 「모범규준_조(판단·2016.8.1판제목)」 칸 |",
     "받은 글 | 자료 묶음마다 조 번호(닿는 조가 없는 묶음은 그 뜻과 까닭) — 5절 표(제목 바로잡음)·5-1절 자료 묶음별 조·CSV 「모범규준_조(판단·2016.8.1판제목)」 칸. "
     "note: 붙인 조는 모두 (판단) — 지시서 9-3 에는 조 번호가 적혀 있지 않음 |", "| 끝에 낼 것 — 모범규준 조 번호 | 판단 |"),
]
# 9-3 CSV 조 칸(재비평 지적 9 연관 — R2 꼴): 전 → 후 (= verify13_raas.csv_art 새 글)
R_CSV_ART = {
    "대응 조 없음(판단 — 󰊱-가-1 대주주의 적정성: 지원 가능성·비전)":
        "조 번호 해당 없음(판단: 󰊱-가-1 대주주의 적정성 — 대주주 지원 가능성·비전은 모범규준 조 주제와 겹치지 않음)",
    "대응 조 없음(판단 — 별첨 보험업감독규정: 경영개선 계획 가운데 금융지주회사 자회사 편입)":
        "조 번호 해당 없음(판단: 별첨 보험업감독규정 — 경영개선 계획 가운데 금융지주회사 자회사 편입은 모범규준 조 주제와 겹치지 않음)",
}
R_CSV_COL = "모범규준_조(판단·2016.8.1판제목)"


def fix_csv_R():
    raw = open(pre_path(CSV_R), "rb").read()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    cols = list(rows[0].keys())

    def dump(rs):
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rs)
        return ("﻿" + b.getvalue()).encode("utf-8")
    if dump(rows) != raw:
        raise SystemExit("[fix13_D CSV 9-3] csv 모듈로 다시 쓴 바이트가 기준 사본과 다름 — 멈춤")
    n = 0
    for k, r in enumerate(rows, 2):
        v = r[R_CSV_COL]
        if v in R_CSV_ART:
            r[R_CSV_COL] = R_CSV_ART[v]
            LOG.append(dict(파일=CSV_R, 줄_기준사본=k, 전=v, 후=r[R_CSV_COL], 규칙="R2",
                            이유=CRIT2 + " 9 연관(R2 꼴): 조 칸 「대응 조 없음(판단 — …)」 → md 와 같은 꼴 「조 번호 해당 없음(판단: 이유)」"))
            n += 1
        elif "조 없음" in v:
            raise SystemExit(f"[fix13_D CSV 9-3] 대응표에 없는 「조 없음」 칸: {r['번호']} {v}")
    if n != 11:
        raise SystemExit(f"[fix13_D CSV 9-3] 바꾼 칸 {n}(기대 11)")
    open(CSV_R, "wb").write(dump(rows))
    return n


def fix_R(d):
    W = R5_WHY
    d.sub("- 작성: 2026-10-07(실행 시각 2026-10-08T00:26:16+09:00)", "- 작성: 2026-10-08(KST)(실행 시각 2026-10-08T00:26:16+09:00)", "R5",
          "작성 라벨이 실행 시각(KST 2026-10-08)과 다름")
    d.sub("옮김 2026-10-07]", "옮김 2026-10-08(KST)]", "R5", "인용 옮김 날짜 — 1차(web13_raas.py 실행 KST 2026-10-08 00:26)·검증 때 더한 인용(KST 2026-10-08 09:49~) 모두 KST 2026-10-08",
          count=68, pred=lambda i, ln: ln.startswith("["))
    d.sub("검증(2026-10-07) 때", "검증(2026-10-08 KST) 때", "R5", W, count=3)
    d.sub("다시 찾은 글(검증 2026-10-07)", "다시 찾은 글(검증 2026-10-08 KST)", "R5", W)
    vh_rename(d)
    R2 = "조가 없다는 판단 → 「조 번호 해당 없음(판단: 이유)」(critic13 gaps — 0절 「대응 조 없음」)"
    d.sub(RA["toc"][0], RA["toc"][1], "R2", R2, count=2)
    d.sub(RA["s3"][0], RA["s3"][1], "R2", R2, count=2)
    d.sub(RA["grp"][0], RA["grp"][1], "R2", R2, count=2)
    d.sub(RA["s6"][0], RA["s6"][1], "R2", R2, count=1)
    R3 = "우리 글의 「없음」 → 이 작업 상태 표기(해당 없음·다른 곳 0)"
    d.sub("| 없음(6개 부문 모두 매뉴얼 Ⅳ장에 있음) |", "| 해당 없음(받지 못한 부문 0 — 6개 부문 모두 매뉴얼 Ⅳ장에 있음, 0절 목차 대조) |", "R3", R3)
    d.sub("| 없음 | 없음(9차 발췌 = 전체 md) |", "| 해당 없음(받지 못한 것 0 — 5개 모두 9차 발췌에 있음) | 다른 곳 0(9차 발췌 = 전체 md, 바이트 대조) |", "R3", R3)
    d.sub("| 없음(9차 발췌 범위 문장은 9차 파일 줄과 같음) |", "| 다른 곳 0(9차 발췌 범위 문장은 9차 파일 줄과 같음) |", "R3", R3)
    # R1 — 지시서 항목 대조 표·2절 표 상태 칸(재비평 지적 9) — 제자리 바꿈(줄을 끼우지 않음)
    W9 = CRIT2 + " 9(R1): 상태 칸을 세 단계(받은 글 / 일부(…) / 추출 범위에 없음)로 — 판단은 상태 칸이 아니라 note"
    for pre_, old, new, must in R_REQ:
        i = d.idx(lambda i, ln, pre_=pre_: ln.startswith(pre_), "지시서 항목 행 " + pre_[:30])
        if not d.lines[i].startswith(pre_ + old) or must not in d.lines[i]:
            raise SystemExit(f"[fix13_D R] 지시서 항목 행 꼴이 다름: {d.lines[i][:80]}")
        d.sub(pre_ + old, pre_ + new, "R1", W9, pred=lambda i, ln, pre_=pre_: ln.startswith(pre_))
    hs = [i for i, ln in enumerate(d.lines) if i not in d.code and re.match(r"^\| 1-(?:나-[1-4]|다-5) \| .* \| 이미 받음\(9차 파일 \d+행\) \|$", ln)]
    if len(hs) != 5:
        raise SystemExit(f"[fix13_D R] 2절 표 「이미 받음」 상태 칸 {len(hs)}줄(기대 5)")
    for i in hs:
        d.set_line(i, re.sub(r"\| 이미 받음\((9차 파일 \d+행)\) \|$", r"| 받은 글(이미 받음 — \1) |", d.lines[i]), "R1",
                   W9 + " — 2절 표 「상태」 칸 「이미 받음(…)」 → 받은 글(이미 받음 — …)")


def record_R(d, n):
    return ["", "### 정합성 보정(2026-10-08)", "",
            "비평 결과(`dart_out/risk13/critic13.json` 의 gaps·contradictions)에 맞춰 날짜 표지·조 번호 칸·표 상태 칸만 제자리에서 고침(줄을 끼우지 않음 — 줄 번호 그대로) — 원문 인용(> 블록·코드 블록) 줄은 그대로. "
            f"스크립트 `scripts/dart/fix13_D.py`(기준 사본 = 커밋 {BASE} 의 이 파일, `dart_out/raw/web13/fix13_D/pre/`; 언제나 그 사본에서 다시 만듦), "
            f"고친 곳 전부(기준 사본 줄·전·후·규칙·이유)는 `dart_out/raw/web13/fix13_D/fix_log.json`(이 파일 {n}곳). 대조: `python3 -I scripts/dart/fix13_D.py check`.",
            "재생성 순서: `python3 -I scripts/dart/verify13_raas.py fix`(검증 보정 — 다시 돌리면 이 보정이 지워짐) → `python3 -I scripts/dart/fix13_D.py`.",
            "",
            "- R2 조 번호 칸 — 0절 자료 묶음 줄·5-1 표 「대응 조 없음 — 목차·번호 체계(자료 위치 안내)」 → 「조 번호 해당 없음(판단: 목차·번호 체계 — 자료 위치 안내라 특정 조에 닿지 않음)」; "
            "3절·5-1 표 「… 편입 문장은 대응 조 없음」, 3-참고·5-1 표 「「그룹」 문단(118·336행)은 대응 조 없음」, 6절 표 「그 밖의 문장은 대응 조 없음(판단)」 → 「조 번호 해당 없음(판단: 이유)」. "
            "나머지 조 대응(5절 표·5-1 표·자료 묶음 줄)은 모두 이미 (판단). `dart_out/risk13/9-3_RAAS_낱말문장.csv` 조 칸의 「대응 조 없음(판단 — …)」 11행(3-04~3-12·3-32·3-33)은 처음 보정 때 대상 밖이라 그대로 두었다가 재비평 보정에서 같은 꼴로 고침(아래).",
            "- R5 날짜 — 머리 「작성: 2026-10-07(실행 시각 2026-10-08T00:26:16+09:00)」 → 「작성: 2026-10-08(KST)(…)」, 인용 출처 줄 68곳 「옮김 2026-10-07」 → 「옮김 2026-10-08(KST)」"
            "(1차 옮김 web13_raas.py 실행 KST 2026-10-08 00:26, 5-2 의 검증 인용 KST 2026-10-08 09:49~), 「검증(2026-10-07) 때」 3곳·5-2 절 제목 「(검증 2026-10-07)」 → 2026-10-08 KST, "
            "절 제목 「검증 기록(2026-10-07)」 → 「검증 기록(2026-10-08 KST)」. 9차 원본 수집일(2026-10-01, fetched_at +09:00)은 그대로. 고친 곳(전·후) 표 안의 날짜는 그때 기록이라 그대로.",
            "- R3 낱말 — 6절 요약 표 「받지 못한 것」·「원문과 다른 것」 칸의 「없음」 3곳 → 「해당 없음(받지 못한 부문 0 …)」·「다른 곳 0(…)」. "
            "그대로 둔 없음: 9차 발췌·저장소 파일에 대한 표기(「9차 발췌에 없음」「.meta.json 이 따로 없고」), hwp 전체를 훑은 결과(「Ⅳ장에는 없다(hwp 레코드 순서로 … 확인)」·「글자 겹치기 누락이 없다」), "
            "지시서에 조 번호가 없다는 사실, 검증 기록의 대조 표·반박 표(대조 스크립트가 다시 계산해 같은 글을 요구)·고친 곳 표(그때 기록).",
            "- R4 — 인용 블록 68개 모두 블록 바로 앞에 [문서명 · URL · 쪽 · 전체 md 줄 · 수집일] 줄이 있음 — 고칠 곳 없음. R1 — 처음 보정 때는 지시서 항목 대조 표(받은 글 / 받은 글 + 본문 추출 범위에 없음 / 판단 꼴)를 고칠 곳 없다고 보았으나 재비평에서 세 단계 밖 낱말이 지적됨 — 아래 재비평 보정.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_raas.py`): 「검증 기록(2026-10-08 KST)」 절 제목을 옛 제목과 같게 받아들이고, 자료 묶음 조 줄은 fix13_D 의 fix_log 「후」이면 그 「전」을 스크립트 대응표와 견줌. "
            "다른 대조 규칙은 그대로이며 보정 뒤 `python3 -I scripts/dart/verify13_raas.py` 문제 0(exit 0).",
            "",
            "#### 재비평 보정(2026-10-08 KST — `dart_out/risk13/critic13_2.json` new_issues 9 + 연관)",
            "",
            "제자리 바꿈만(줄을 끼우지 않음 — 줄 번호 그대로). 고친 곳 전·후는 fix_log.json(규칙 R1·R2, 이유에 「재비평」).",
            "",
            "- R1 검증 기록 「지시서 항목 대조」 표 상태 칸 — "
            + "; ".join("「%s」 전: 「%s」 → 후: 「%s」" % (p.strip("| ").split(" | ")[0], o.split(" | ")[0], n.split(" | ")[0]) for p, o, n, _ in R_REQ)
            + ". 마지막 행 근거 칸은 「자료 묶음마다 조 번호(…) … note: 붙인 조는 모두 (판단) — 지시서 9-3 에는 조 번호가 적혀 있지 않음」으로(판단은 상태 칸이 아니라 note). 나머지 13행은 모두 받은 글이라 그대로.",
            "- R1 2절 표(1-나-1~1-나-4·1-다-5) 「상태」 칸 5행 — 전: 「이미 받음(9차 파일 N행)」 → 후: 「받은 글(이미 받음 — 9차 파일 N행)」(verify13_raas.py 는 이 칸에 「9차 파일 N행」이 있는지만 봄 — 그대로 통과). "
            "그 밖의 표(1절 세부 점검사항·4-1 글자 겹침·5절 조 대응·5-1 자료 묶음·6절 요약·검증 기록 대조·반박 표)는 받은 것 상태 칸을 두지 않은 표라 해당 없음(6절 요약 표는 「받은 것 / 받지 못한 것」 글 칸 — 받지 못한 것은 처음 보정에서 「해당 없음(…)」「추출 범위에 없음(…)」으로 고침).",
            "- R2 꼴 — CSV `dart_out/risk13/9-3_RAAS_낱말문장.csv` 「" + R_CSV_COL + "」 칸 11행(3-04~3-12·3-32·3-33): "
            + "; ".join("전 「%s」 → 후 「%s」" % kv for kv in R_CSV_ART.items())
            + " — md 3절·5-1 표의 「조 번호 해당 없음(판단: 대주주 지원 가능성·경영개선 계획의 자회사 편입은 모범규준 조 주제와 겹치지 않음)」과 같은 꼴. "
            "md 의 같은 뜻 칸 전수: 0절·3절·3-참고 자료 묶음 줄, 5-1 표, 6절 요약 표 조 칸 모두 이미 「조 번호 해당 없음(판단: …)」 꼴(검증 기록 고친 곳 표 18행 「후」 칸의 「대응 조 없음(판단)」은 그때 기록이라 그대로). "
            "1-6 자료 묶음 「직접 대응 조는 찾지 못함 — 가장 가까운 조: …」는 조 번호를 붙인 줄(가장 가까운 조, 판단)이라 그대로.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_raas.py`): `csv_art` 가 내는 CSV 조 칸 글을 새 꼴로(fix 모드도 같은 글을 씀), 지시서 항목 대조(대조 보고 8-1)는 스크립트가 만든 행이 md 에 없으면 fix13_D fix_log 「후」 → 「전」으로 견주고, "
            "상태 칸은 md 에 있는 행에서 보며 「일부(」도 받아들임. 보정 뒤 `python3 -I scripts/dart/verify13_raas.py` 문제 0(exit 0)."]


# ───────────────────────────── 9-4 모범규준 원문 ─────────────────────────────
M_R3 = [
    ("예고·보도자료에도 2016.3.28·2016.4.1 날짜의 개정 기록 없음", "예고·보도자료에서도 2016.3.28·2016.4.1 날짜의 개정 기록은 추출 범위에 없음"),
    ("2018년 행정지도 내역 8건 전부에 2014-017 없음", "2018년 행정지도 내역 8건 전부를 보았으나 2014-017 은 추출 범위에 없음"),
    ("2018 보도자료 본문에 이 모범규준 이름 없음", "2018 보도자료 본문에서 이 모범규준 이름은 추출 범위에 없음"),
    ("이 모범규준 제목 없음(원 수집은 제목만 9건)", "이 모범규준 제목은 추출 범위에 없음(원 수집은 제목만 9건)"),
    ("이름에 지주·모범이 든 행정규칙 없음", "이름에 지주·모범이 든 행정규칙은 추출 범위에 없음"),
]


def fix_M(d):
    W = R5_WHY
    d.sub("- 수집일: 2026-10-07(UTC — 원본 .meta.json 의 fetched_at 은 KST ",
          "- 수집일: 2026-10-08(KST — 정합성 보정 때 「2026-10-07(UTC)」 라벨을 KST 로 고침; 요청기록 csv 시각도 +09:00. 원본 .meta.json 의 fetched_at ", "R5",
          "머리 수집일 라벨이 UTC 날짜 — fetched_at 은 모두 KST 2026-10-08(1차 00:29~01:00, 검증 09:48~09:55)")
    hs = d.hits("수집 2026-10-07(UTC; .meta.json fetched_at ")
    for i in hs:
        ln = d.lines[i]
        fas = re.findall(r"수집 2026-10-07\(UTC; \.meta\.json fetched_at (\S+?)\)", ln)
        if not fas or any(not fa.startswith("2026-10-08T") or not fa.endswith("+09:00") for fa in fas):
            raise SystemExit(f"[fix13_D M] 줄 {i + 1} fetched_at 이 KST 2026-10-08 아님: {fas}")
    d.sub("수집 2026-10-07(UTC; .meta.json fetched_at ", "수집 2026-10-08(KST; .meta.json fetched_at ", "R5",
          "인용 머리 수집 라벨 — fetched_at(+09:00)이 KST 2026-10-08", count=33)
    d.sub("검증(2026-10-07)", "검증(2026-10-08 KST)", "R5", W, count=d.count("검증(2026-10-07)"))
    d.sub("## 10. 지시서 항목별 대조(검증 2026-10-07 추가)", "## 10. 지시서 항목별 대조(검증 2026-10-08 KST 추가)", "R5", W)
    d.sub("(컨테이너 재시작 뒤, 2026-10-07 표기 유지)", "(컨테이너 재시작 뒤, 2026-10-08 KST — 그때 적은 「2026-10-07 표기 유지」는 정합성 보정 때 KST 로 고침)", "R5", W)
    vh_rename(d)
    # R2 — 연혁·출처 자료(2-3·2-5·2-6·2-7 행정지도 예고·내역 화면, 4장 부칙)
    R2 = "연혁·출처 자료 → 조 번호 칸에 「조 번호 해당 없음(연혁·출처 자료)」(critic13 gaps)"
    d.sub("— 모범규준 조: 전체(존속기한 연장 예고)", "— 모범규준 조: " + NOART + " — 모범규준 전체의 존속기한 연장 예고", "R2", R2, count=2)
    d.sub("— 모범규준 조: 전체(개정 통보·명칭 변경)", "— 모범규준 조: " + NOART + " — 모범규준 전체의 개정 통보·명칭 변경", "R2", R2)
    d.sub("— 모범규준 조: 전체(존속기한 연장 통보)", "— 모범규준 조: " + NOART + " — 모범규준 전체의 존속기한 연장 통보", "R2", R2)
    d.sub("— 모범규준 조: 전체(연혁 — KB 리스크관리규정 2012.5.30 개정이 이 모범규준 제정을 반영)",
          "— 모범규준 조: " + NOART + " — 모범규준 전체의 연혁(KB 리스크관리규정 2012.5.30 개정이 이 모범규준 제정을 반영)", "R2", R2 + " — 7장 연혁 인용도 같은 꼴")
    d.sub("| 2장 | 전체 |", "| 2장 | " + NOART + " |", "R2", R2 + " — 9장 표 「연혁 근거」 행 조 칸")
    i = d.idx(lambda i, ln: ln == "### 부칙", "4장 「### 부칙」 머리")
    d.set_line(i, "### 부칙 — 모범규준 조: " + NOART + "(세 판 부칙의 시행일·적용례)", "R2", R2 + " — 줄을 끼우지 않고 절 머리에 붙임(5장 줄 번호를 다른 산출물이 가리킴)")
    # R3 — 9장 표·반박 시도 소절의 「없음」 단정
    for o, n in M_R3:
        d.sub(o, n, "R3", "반박 시도 결과의 「없음」 단정 → 「추출 범위에 없음」(찾은 범위는 같은 줄)", count=2)


def record_M(d, n):
    return ["", "### 정합성 보정(2026-10-08)", "",
            "비평 결과(`dart_out/risk13/critic13.json` 의 gaps·contradictions)에 맞춰 날짜 표지·조 번호 칸·note 만 제자리에서 고침(줄을 끼우지 않음 — 5장·6장 줄 번호를 다른 산출물이 가리킴) — 원문 인용(코드 블록 39개) 줄은 그대로. "
            f"스크립트 `scripts/dart/fix13_D.py`(기준 사본 = 커밋 {BASE} 의 이 파일, `dart_out/raw/web13/fix13_D/pre/`; 언제나 그 사본에서 다시 만듦), "
            f"고친 곳 전부(기준 사본 줄·전·후·규칙·이유)는 `dart_out/raw/web13/fix13_D/fix_log.json`(이 파일 {n}곳). 대조: `python3 -I scripts/dart/fix13_D.py check`.",
            "재생성 순서: `python3 scripts/dart/verify13_mobeom.py fix`(검증 보정 — 이 보정 뒤의 md 에 다시 돌리지 말 것; 기준 사본에서 돌린 뒤) → `python3 -I scripts/dart/fix13_D.py`.",
            "",
            "- R5 날짜 — 머리 「수집일: 2026-10-07(UTC — …)」 → 「수집일: 2026-10-08(KST — …)」(fetched_at 은 1차 KST 2026-10-08 00:29~01:00, 검증 때 더 받은 것 09:48~09:55; 요청기록 csv 시각도 +09:00), "
            "인용 머리 33곳 「수집 2026-10-07(UTC; .meta.json fetched_at …)」 → 「수집 2026-10-08(KST; .meta.json fetched_at …)」(fetched_at 값은 그대로), "
            "「검증(2026-10-07)」(머리·note·9장 표의 「반박 시도[N…]」 표지) → 「검증(2026-10-08 KST)」, 10장 제목 「(검증 2026-10-07 추가)」·절 제목 「검증 기록(2026-10-07)」 → 2026-10-08 KST, "
            "「이어서 한 검증(…, 2026-10-07 표기 유지)」 → KST. 고친 곳(전 → 후) 소절 안의 날짜는 그때 기록이라 그대로.",
            f"- R2 조 번호 칸 — 2-3·2-6(행정지도 예고 화면)·2-5·2-7(행정지도 내역 화면) 인용 머리 「모범규준 조: 전체(…)」 → 「모범규준 조: {NOART} — 모범규준 전체의 …」, "
            f"4장 「### 부칙」 → 「### 부칙 — 모범규준 조: {NOART}(세 판 부칙의 시행일·적용례)」, 7장 KB 연혁 인용 머리 「전체(연혁 — …)」·9장 표 「연혁 근거」 행 조 칸 「전체」도 같은 꼴. "
            "2-1·2-2·2-4·7장 인용 머리의 조(판단)·4장 조문 절 머리의 조 번호는 그대로.",
            "- R3 낱말 — 9장 표와 검증 기록 반박 시도 소절의 「개정 기록 없음」「2014-017 없음」「이 모범규준 이름 없음」「이 모범규준 제목 없음」「행정규칙 없음」(각 2곳) → 「… 추출 범위에 없음」(찾은 범위는 같은 줄). "
            "그대로 둔 없음: 전문을 옮긴 원문의 조·항 구성에 대한 관찰(「단계 수·이름은 모범규준에 없음」「개정 표시가 없음」「조문별 표시가 없음」), 인용한 쪽·글 안의 관찰(「「모범규준」 낱말은 없으나」「4곳에는 조 번호 없음」「인쇄 쪽 번호 텍스트에 없음」), "
            "대조 수(「없음 0」), sha256 같음에서 나온 「별도 본문 변경 없음」, robots 판정 「규칙 없음(제한 없음)」, 8차 기록 「수집 시각 기록 없음」, 이 작업의 표기(내용을 지운 곳 없음·남은 지시서 항목은 없음), 고친 곳 소절(그때 기록).",
            "- R4 — 인용 39개 모두 블록 바로 앞 [문서명 · URL/접수번호 · 쪽/조문 · 수집] 줄 — 고칠 곳 없음. R1 — 9장 「받은 것/받지 못한 것」·10장 지시서 대조 표 상태는 받은 글 / 추출 범위에 없음 + 찾은 방법 꼴 — 고칠 곳 없음.",
            "- 대조 스크립트 최소 수정(`scripts/dart/verify13_mobeom.py`): 절 제목(10장·검증 기록)과 「검증(2026-10-08 KST) 반박 시도[N…]」 표지, 인용 머리 「수집 2026-10-08(KST; .meta.json fetched_at …)」도 받아들이고, "
            "「검증 전 사본 보존」 대조에서 fix13_D fix_log 의 「전」 줄도 바뀐 줄로 받아들임. 다른 대조 규칙은 그대로이며 보정 뒤 인자 없이 돌려 문제 0(exit 0)."]


# ───────────────────────────── 실행 ─────────────────────────────
def append_record(d, rec_fn, *args):
    last = max(i for i, ln in enumerate(d.lines) if ln.strip())
    n = d.nlog() + 1
    rec = rec_fn(d, n, *args)
    d.insert_after(last, rec, "R1~R5", "검증 기록 끝에 정합성 보정 소절")


def fix():
    ensure_pre()
    LOG.clear()
    S = pub_scan()
    docs = exam_docs()
    dP, dE, dR, dM = (Doc(k, MD[k]) for k in ("P", "E", "R", "M"))
    fix_P(dP)
    n_a, kinds = fix_E(dE, S, docs)
    fix_R(dR)
    fix_M(dM)
    append_record(dP, record_P)
    append_record(dE, record_E, S, kinds)
    append_record(dR, record_R)
    append_record(dM, record_M)
    nrows = fix_csv(S)
    nR = fix_csv_R()
    for d in (dP, dE, dR, dM):
        if code_lines(d.final()) != code_lines(d.text0.split("\n")):
            raise SystemExit(f"[fix13_D {d.key}] 원문 인용 줄이 바뀜 — 쓰지 않음")
        if d.key in ("R", "M") and len(d.final()) != len(d.lines) + len(d.ins.get(max(d.ins), [])):
            raise SystemExit(f"[fix13_D {d.key}] 맨 끝 소절 말고 끼운 줄이 있음")
    for d in (dP, dE, dR, dM):
        d.write()
    os.makedirs(FD, exist_ok=True)
    json.dump(dict(기준=f"커밋 {BASE}", 작성=f"{TODAY}(KST)", 규칙="13차 정합성 보정 R1~R5 + 지시서 9-5 공개일 다시 확인",
                   줄="줄_기준사본 = 기준 사본(pre/) 줄 번호(끼운 줄은 「N 뒤에 끼움」, CSV 는 행 번호 — 머리=1)",
                   공개일_재확인=SCANF, 보정=LOG), open(LOGF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = collections.Counter((os.path.basename(x["파일"]), x["규칙"]) for x in LOG)
    for k, v in sorted(by.items()):
        print(f"  {k[0]} {k[1]}: {v}")
    print(f"fix13_D: 고친 곳 {len(LOG)} → {LOGF}; 9-5 블록 {dict(kinds)} · 근거 조문 줄 {n_a} · CSV {nrows}행 · 9-3 CSV 조 칸 {nR}행; 공개일 재확인 → {SCANF}")
    return 0


def check_crit2(cur, rows_e, rows_r):
    """재비평 보정이 지금 파일에 있는지: R1 상태 칸 세 단계, R2 「조 번호 해당 없음(판단: …)」 꼴, R5 9-2-4 1절 표 날짜 종류."""
    out = []

    def body(L):                                             # 인용 줄·「고친 곳」 표(그때 기록) 밖
        res, incode, fixed = [], False, False
        for i, ln in enumerate(L):
            if ln == "### 정합성 보정(2026-10-08)":           # 보정 기록(전·후를 적음) — 여기부터 끝까지 뺌
                break
            if ln.startswith("```"):
                incode = not incode
                continue
            if ln.startswith(("### 고친 곳", "### 1. 고친 곳")):
                fixed = True
                continue
            if fixed and ln.startswith(("### ", "## ")):
                fixed = False
            if not (incode or ln.startswith(">") or fixed):
                res.append((i, ln))
        return res
    for k, p in MD.items():
        if k == "M":
            continue
        L = cur[p]
        # R1 — 「| 지시서 항목 … | 상태 |」 표와 9-3 2절 표 「상태」 칸
        hdr = None
        for i, ln in body(L):
            if ln.startswith("| ") and "| 상태 |" in ln:
                hdr = [c.strip() for c in ln.strip("|").split(" | ")]
                continue
            if hdr and ln.startswith("|---"):
                continue
            if hdr and ln.startswith("| "):
                c = [x.strip() for x in ln.strip().strip("|").split(" | ")]
                st = c[hdr.index("상태")] if len(c) == len(hdr) else ""
                if not R1_RE.match(st):
                    out.append(f"{os.path.basename(p)} {i + 1}줄: 상태 칸이 R1 세 단계 밖 — {st[:40]!r}")
                elif "추출 범위에 없음" in st and "찾은 방법" not in ln:
                    out.append(f"{os.path.basename(p)} {i + 1}줄: 상태에 추출 범위에 없음인데 찾은 방법 없음")
                continue
            hdr = None
        # R2 — 조가 없다는 칸의 꼴
        for i, ln in body(L):
            for bad in ("대응 조 없음", "특정 조 없음", "특정 조 번호 해당 없음"):
                if bad in ln:
                    out.append(f"{os.path.basename(p)} {i + 1}줄: R2 꼴 밖 「{bad}」")
    for r in rows_e:
        v = r["모범규준_조제목(2016.8.1판)"]
        if "조 없음" in v or ("제5장" in r["모범규준_조(판단)"] and v != CH5_TITLE[1]):
            out.append(f"9-5 CSV 조제목 칸 R2 꼴 밖: {v[:60]}")
    for r in rows_r:
        v = r[R_CSV_COL]
        if "조 없음" in v or ("해당 없음" in v and not v.startswith("조 번호 해당 없음(판단: ")):
            out.append(f"9-3 CSV {r['번호']} 조 칸 R2 꼴 밖: {v[:60]}")
    # R5 — 9-2-4 1절 표 날짜 칸마다 종류
    L = cur[MD["P"]]
    if P_TAB_HEAD[1] not in "\n".join(L):
        out.append("9-2-4 1절 표 칸 머리가 날짜 종류를 밝히지 않음")
    for ln in L:
        if re.match(r"^\| Q\d \| ", ln):
            c = ln.split(" | ")[1]
            if not any(w in c for w in ("배포", "보도", "등록일")):
                out.append(f"9-2-4 1절 표 날짜 칸에 종류 없음: {c}")
    return out


def check():
    probs = []
    if not os.path.exists(LOGF):
        print("fix_log.json 없음")
        return 1
    log = json.load(open(LOGF, encoding="utf-8"))["보정"]
    cur = {p: open(p, "rb").read().decode("utf-8-sig").split("\n") for p in list(MD.values())}
    csv_texts = {p: open(p, "rb").read().decode("utf-8-sig") for p in CSVS}
    csv_text = csv_texts[CSV_E]
    last = {}
    for x in log:
        if x["파일"] in CSVS:                    # CSV 는 칸마다 따로 — 모든 「후」 글이 있어야 함
            if x["후"] not in csv_texts[x["파일"]]:
                probs.append(f"{os.path.basename(x['파일'])}: 「후」 글이 지금 파일에 없음 — {x['후'][:70]}")
            continue
        last[(x["파일"], str(x["줄_기준사본"]))] = x
    for x in last.values():
        after = x["후"] if isinstance(x["후"], list) else [x["후"]]
        for a in after:
            if a not in cur[x["파일"]]:
                probs.append(f"{os.path.basename(x['파일'])}: 「후」 줄이 지금 파일에 없음 — {a[:70]}")
    for k, p in MD.items():
        pre = open(pre_path(p), encoding="utf-8").read().split("\n")
        if code_lines(pre) != code_lines(cur[p]):
            probs.append(f"{os.path.basename(p)}: 원문 인용(코드 블록·> 블록) 줄이 기준 사본과 다름")
        heads = [ln for ln in cur[p] if ln.startswith("## ")]
        if not heads or heads[-1] != NEW_VH:
            probs.append(f"{os.path.basename(p)}: 맨 끝 절이 「{NEW_VH}」 아님")
        if "### 정합성 보정(2026-10-08)" not in cur[p]:
            probs.append(f"{os.path.basename(p)}: 정합성 보정 소절 없음")
        if k in ("R", "M"):
            extra = len(cur[p]) - len(pre)
            tail = cur[p][len(pre):] if extra > 0 else []
            if extra <= 0 or "### 정합성 보정(2026-10-08)" not in tail:
                probs.append(f"{os.path.basename(p)}: 줄 수가 맨 끝 소절 말고도 바뀜(줄 번호가 밀림)")
    # 9-5: 인용 블록마다 바로 앞 출처 줄
    L = cur[MD["E"]]
    nb = 0
    for i, ln in enumerate(L):
        if ln == "```text":
            nb += 1
            if not (L[i - 1] == "" and L[i - 2].startswith("인용 출처: [") and "https://www.fss.or.kr/" in L[i - 2] and " · 수집 2026-10-08(KST)]" in L[i - 2]):
                probs.append(f"9-5 md {i + 1}줄 블록 바로 앞에 출처 줄 없음")
    if nb != 135:
        probs.append(f"9-5 인용 블록 {nb}개(기대 135)")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if len(rows) != 235 or any(not r.get(PUB_COL, "").startswith("추출 범위에 없음(") for r in rows):
        probs.append(f"CSV {len(rows)}행 · 「{PUB_COL}」 칸이 모두 「추출 범위에 없음(…)」 아님")
    probs += check_crit2(cur, rows, list(csv.DictReader(io.StringIO(csv_texts[CSV_R]))))
    print(f"fix13_D check: fix_log {len(log)}곳 · md 4개 · CSV {len(rows)}행 — 문제 {len(probs)}건")
    for x in probs[:40]:
        print("  ✗", x)
    return 1 if probs else 0


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "check":
        return check()
    if mode in ("", "fix"):
        return fix()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
