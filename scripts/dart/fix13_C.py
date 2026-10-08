# -*- coding: utf-8 -*-
"""13차 정합성 보정 — 그룹 C(법령: 9-1 법령 원문 · 9-2 의 1·2 ORSA 연혁 · 9-2 의 3·5 [별표 37]·[별표 22]).

    python3 -I scripts/dart/fix13_C.py          # 보정(멱등 — 언제나 기준 사본 pre/ 에서 다시 만듦) → fix_log → check
                                                #   → 대조 스크립트 verify13_law91.py·verify13_law92.py(인자 없이) 실행, 모두 exit 0 이어야 함
    python3 -I scripts/dart/fix13_C.py check    # 확인만 — 문제 0 이면 exit 0:
                                                #   fix_log 의 「후」가 지금 파일에 다 있는지,
                                                #   원문 인용 줄(코드 블록 안·「>」 줄)이 기준 사본과 한 줄도 다르지 않은지(출처 줄을 끼운 것 말고는),
                                                #   고친 뒤 남으면 안 되는 글(「검증 기록(2026-10-07)」 등)이 없는지.

기준 사본: 커밋 496ddc4 의 파일 → dart_out/raw/web13/fix13_C/pre/<파일 이름> (없으면 `git show 496ddc4:<경로>` 로 만듦).
고치는 파일: handoff/13차_산출물/9-1_법령원문.md · 9-2-1_2_ORSA_연혁.md · 9-2-3_5_별표37_별표22.md,
             dart_out/risk13/9-1_법령판.csv(note 칸의 R3 낱말·R5 시각만).
기록: dart_out/raw/web13/fix13_C/fix_log.json (파일·줄·전·후·규칙 R1~R5·이유) — md 마다 「## 검증 기록」 끝 「### 정합성 보정(2026-10-08)」 소절에도 적음.
규칙: 13차 정합성 보정 규칙 R1~R5(비평 dart_out/risk13/critic13.json 의 gaps·contradictions 가운데 그룹 C 몫).
  - 모순: 9-2-1_2 3-6 note(「받은 세칙 판 15개 … 사이 판 2200000108867 은 받지 않음」) ↔ 판목록 csv·6-4·검증 기록 → 검증 뒤 사실로.
  - R2 조 번호 칸: 9-1·9-2 의 조 대응은 모두 새로 붙인 것 → 조 번호 칸 바로 뒤 「(판단)」. 9-1 8-6절 「1-1·1-3·1-4절과 같음」 → 실제 조.
    연혁 판 목록·출처 묶음 → 「조 번호 해당 없음(연혁·출처 자료)」.
  - R3 우리 글의 「없음」 단정 → 「추출 범위에 없음」/「찾지 못함」 + 찾은 방법. 지시서·표 칸 표기·글자 차이 표기는 그대로(소절에 갈래·수).
  - R4 9-1 1-4·1-5·8-2·8-3절에서 절 머리 출처 줄 하나에 묶인 인용 블록마다 바로 앞에 출처 줄.
  - R5 날짜 라벨 KST(원장은 UTC): 검증(verify13_law91 KST 2026-10-08 09:10~09:26, verify13_law92 KST 12:23~12:42)·9-2 재수집(KST 10-08 08:50~08:59).
원문 인용 줄(코드 블록 안)은 바꾸지 않는다. 바꿀 글이 예상 횟수만큼 나오지 않으면 멈춘다(SystemExit).
재생성 순서: verify13_law91.py fix · verify13_law92.py fix(검증 보정 — 다시 돌리면 검증 전 사본에서 만들어 이 보정이 지워짐) → 이 스크립트.
대조 스크립트 최소 수정(이 보정과 함께): verify13_law91.py — 「## 8. 검증 보충」「## 검증 기록」 앵커가 (2026-10-08 KST) 제목도 받음;
  verify13_law92.py — 「## 검증 기록」「## 5./6. 검증 보충」 앵커가 (2026-10-08 KST) 제목도 받음, 「- 모범규준 조」 줄의 (판단) 검사가
  「조 번호 해당 없음(연혁·출처 자료)」 줄을 받음.
웹 요청·API 키·OC 를 쓰지 않는다(로컬 파일만).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)

BASE = "496ddc4"
FIXD = "2026-10-08"
FD = os.path.join("dart_out", "raw", "web13", "fix13_C")
PRE = os.path.join(FD, "pre")
LOGF = os.path.join(FD, "fix_log.json")
OUTD = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
MD91 = os.path.join(OUTD, "9-1_법령원문.md")
MD921 = os.path.join(OUTD, "9-2-1_2_ORSA_연혁.md")
MD923 = os.path.join(OUTD, "9-2-3_5_별표37_별표22.md")
CSV91 = os.path.join(WORK, "9-1_법령판.csv")
FILES = [MD91, MD921, MD923, CSV91]
VERIFY = ["scripts/dart/verify13_law91.py", "scripts/dart/verify13_law92.py"]
NOART = "조 번호 해당 없음(연혁·출처 자료)"
SEC_TITLE = "### 정합성 보정(2026-10-08)"
FENCE = re.compile(r"^\s*```")
LOG = []

# 모범규준 조 제목(2016.8.1 판, dart_out/risk13/모범규준_조목록.csv 와 같은 글자)
T = {3: "적용대상", 7: "조직구성", 8: "이사회", 9: "그룹위험관리위원회", 10: "경영진", 13: "그룹위험관리부서", 14: "위험 통제",
     16: "보고체계", 19: "위험 측정", 20: "위험 관리", 21: "신용위험", 22: "시장위험", 23: "운영위험", 25: "유동성위험",
     28: "시스템 구축 및 관리", 33: "그룹내 위험 전이 방지", 37: "자본적정성 평가 및 관리 체제", 56: "통합위기상황분석", 57: "비상계획"}


def arts(nos, sep=" · "):
    return sep.join("제%d조(%s)" % (n, T[n]) for n in nos)


def pre_path(p):
    return os.path.join(PRE, os.path.basename(p))


def ensure_pre():
    os.makedirs(PRE, exist_ok=True)
    for p in FILES:
        q = pre_path(p)
        if not os.path.exists(q):
            b = subprocess.run(["git", "show", "%s:%s" % (BASE, p)], capture_output=True, check=True).stdout
            with open(q, "wb") as f:
                f.write(b)


def check_jo_titles():
    import csv
    rows = {r["조"]: r["제목_2016.8.1판"] for r in csv.DictReader(open(os.path.join(WORK, "모범규준_조목록.csv"), encoding="utf-8-sig"))}
    bad = [n for n, t in T.items() if rows.get(str(n)) != t]
    if bad:
        raise SystemExit("[fix13_C] 조 제목이 조목록과 다름: %s" % bad)


class Doc:
    def __init__(self, path, md=True):
        self.path, self.md = path, md
        raw = open(pre_path(path), "rb").read()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.crlf = (not md) and "\r\n" in text
        if self.crlf:
            text = text.replace("\r\n", "\n")
        self.lines = text.split("\n")
        self.code, self.fixed = set(), set()
        self.before, self.after = {}, {}
        if md:
            incode = on = False
            for i, ln in enumerate(self.lines):
                if FENCE.match(ln):
                    self.code.add(i)
                    incode = not incode
                    continue
                if incode or ln.startswith(">"):
                    self.code.add(i)
                if ln.startswith("### 고친 곳"):
                    on = True
                    continue
                if on and (ln.startswith("### ") or ln.startswith("## ")):
                    on = False
                if on:
                    self.fixed.add(i)

    def name(self):
        return os.path.basename(self.path)

    def log(self, i, before, after, rule, why, kind="줄", key=None, frag=None):
        LOG.append(dict(파일=self.path, 줄_기준사본=i + 1, 종류=kind, 전=before, 후=after, 규칙=rule, 이유=why, 묶음=key, _frag=frag))

    def sub(self, old, new, rule, why, count=1, pred=None, group=False):
        hits = [i for i, ln in enumerate(self.lines) if i not in self.code and i not in self.fixed and old in ln
                and (pred is None or pred(i, ln))]
        n = sum(self.lines[i].count(old) for i in hits)
        if n != count:
            raise SystemExit("[fix13_C %s] 「%s」 %d번 나옴(기대 %d) — %s" % (self.name(), old[:90], n, count, why))
        for i in hits:
            b = self.lines[i]
            a = b.replace(old, new)
            self.lines[i] = a
            self.log(i, b, a, rule, why, key=("%s\x00%s" % (old, new)) if group else None, frag=(old, new))

    def idx(self, pred, what):
        hits = [i for i, ln in enumerate(self.lines) if i not in self.code and pred(i, ln)]
        if len(hits) != 1:
            raise SystemExit("[fix13_C %s] %s: %d줄(기대 1)" % (self.name(), what, len(hits)))
        return hits[0]

    def head(self, prefix):
        return self.idx(lambda i, ln: ln.startswith(prefix), "머리 「%s」" % prefix)

    def section(self, prefix):
        s = self.head(prefix)
        lvl = len(prefix) - len(prefix.lstrip("#"))
        e = len(self.lines)
        for j in range(s + 1, len(self.lines)):
            m = re.match(r"^(#+) ", self.lines[j])
            if m and j not in self.code and len(m.group(1)) <= lvl:
                e = j
                break
        return s, e

    def set_line(self, i, new, rule, why, key=None):
        if i in self.code:
            raise SystemExit("[fix13_C %s] %d줄은 원문 인용 줄 — 고치지 않음" % (self.name(), i + 1))
        b = self.lines[i]
        if b != new:
            self.lines[i] = new
            self.log(i, b, new, rule, why, key=key)

    def insert_after(self, i, new_lines, rule, why):
        self.after.setdefault(i, []).extend(new_lines)
        LOG.append(dict(파일=self.path, 줄_기준사본="%d 뒤에 끼움" % (i + 1), 종류="끼움", 전="", 후=list(new_lines), 규칙=rule,
                        이유=why, 묶음=None, _i=i, _side="after"))

    def insert_before(self, i, new_lines, rule, why, key=None):
        self.before.setdefault(i, []).extend(new_lines)
        LOG.append(dict(파일=self.path, 줄_기준사본="%d 앞에 끼움" % (i + 1), 종류="끼움", 전="", 후=list(new_lines), 규칙=rule,
                        이유=why, 묶음=key, _i=i, _side="before"))

    def fences(self, s, e):
        """[s, e) 안의 코드 블록 여는 줄."""
        out, inc = [], False
        for j in range(s, e):
            if FENCE.match(self.lines[j]):
                if not inc:
                    out.append(j)
                inc = not inc
        return out

    def final(self):
        out, pos = [], {}
        for i, ln in enumerate(self.lines):
            out.extend(self.before.get(i, []))
            pos[i] = len(out) + 1
            out.append(ln)
            out.extend(self.after.get(i, []))
        return out, pos

    def write(self, extra=None):
        out, _ = self.final()
        while out and out[-1] == "" and extra:
            out.pop()
        if extra:
            out += [""] + extra + [""]
        s = "\n".join(out)
        if self.crlf:
            s = s.replace("\n", "\r\n")
        data = s.encode("utf-8")
        if self.bom:
            data = b"\xef\xbb\xbf" + data
        with open(self.path, "wb") as f:
            f.write(data)


# ───────────────────────────── R2 공통: 조 번호 칸 바로 뒤 (판단) ─────────────────────────────
def add_judge(d, skip=()):
    n = 0
    for i, ln in enumerate(d.lines):
        if i in d.code or i in d.fixed or i in skip or not ln.startswith("- 모범규준 조(판단"):
            continue
        ci = ln.find("): ")
        if ci < 0:
            continue
        ci += 3
        rest = ln[ci:]
        di = rest.find(" — ")
        lst = rest[:di] if di >= 0 else rest
        if not re.search(r"제\d+조\(", lst) or "판단" in lst:
            continue
        new = ln
        if di >= 0 and new.endswith(" (판단)"):
            new = new[:-len(" (판단)")]
        if di >= 0:
            new = new[:ci + di] + " (판단)" + new[ci + di:]
        else:
            new = new.rstrip(".") + " (판단)" + ("." if ln.endswith(".") else "")
        d.set_line(i, new, "R2", "조 번호 칸 바로 뒤에 「(판단)」 — 9-1·9-2 의 조 대응은 모두 새로 붙인 것(지시서 9-1·9-2 에 조 번호 없음). "
                                 "줄 머리의 「모범규준 조(판단」만으로는 조 번호 칸에 표지가 없어 보였음(critic13 by_article)", key=JUDGE_KEY)
        n += 1
    return n


JUDGE_KEY = "R2-judge"
JUDGE_SHOW = ("「- 모범규준 조(판단…): 제N조(제목) · … — 해설」(조 번호 칸 뒤 표지 없음; 끝의 (판단)은 해설 뒤에 있었음)",
              "「- 모범규준 조(판단…): 제N조(제목) · … (판단) — 해설」(조 번호 칸 바로 뒤로)")


def noart_line(desc):
    return "- 모범규준 조: %s — %s" % (NOART, desc)


# ───────────────────────────── 9-1 ─────────────────────────────
SEC = "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2200000107297&type=XML"
GOV = "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2100000285614&type=XML"


def cite_sec(loc, extra=""):
    return ("- 출처: [금융지주회사감독규정시행세칙 · 일련번호 2200000107297 · %s · %s · 수집 2026-10-02(KST, 11차 원본 "
            "dart_out/raw/web11/law/금융지주회사감독규정시행세칙_2200000107297.xml)%s]" % (SEC, loc, extra))


def fix_91(d):
    W = "R5"
    # ── R5 날짜 라벨 ──
    d.sub("- 수집일: 2026-10-07(현행 판 재확인 2026-10-07T23:50:17+09:00 · 금융지주회사감독규정 연혁 판 받기).",
          "- 수집일: 2026-10-07(KST — 1차 수집: 현행 판 재확인 2026-10-07T23:50:17+09:00 · 금융지주회사감독규정 연혁 판 받기, "
          "원장 law91/_call_log.csv 는 UTC 2026-10-07 14:48~14:51). 검증 때 더 받은 원본(별표 3·4·5 PDF, 지배구조 감독규정 연혁 목록·판 XML, "
          "띄어 쓴 이름 연혁 목록)은 2026-10-08(KST 09:10~09:11 — 8절, 원장 `dart_out/raw/web13/verify13_law91/_call_log.csv` 는 UTC).",
          W, "1차 수집 원장 UTC 14:48~14:51 = KST 2026-10-07 23:48~23:51(라벨 맞음), 검증 수집 UTC 2026-10-08 00:10~00:11 = KST 09:10~09:11 — 라벨이 없던 검증 수집 날짜를 적음")
    d.sub("검증(2026-10-07)", "검증(2026-10-08 KST)", W,
          "검증(verify13_law91 — 원장 UTC 2026-10-08 00:10~00:11, md 보정 2026-10-08T09:26 KST)은 KST 2026-10-08", count=19, group=True)
    d.sub("검증 재사용 2026-10-07]", "검증 재사용 2026-10-08(KST)]", W, "검증 때 다시 쓴 날 = KST 2026-10-08", count=5, group=True)
    d.sub("## 0. 현행 판 재확인(2026-10-07)", "## 0. 현행 판 재확인(2026-10-07 KST)", W,
          "현행 재확인은 1차 수집 KST 2026-10-07 23:48~23:51(라벨 맞음) — 시간대만 밝힘")
    d.sub("## 8. 검증 보충(2026-10-07)", "## 8. 검증 보충(2026-10-08 KST)", W, "검증 보충은 KST 2026-10-08(원장 UTC 2026-10-08 00:10~)")
    d.sub("## 검증 기록(2026-10-07)", "## 검증 기록(2026-10-08 KST)", W,
          "검증 실행 2026-10-08T09:26:21+09:00 — 대조 스크립트 앵커는 두 제목을 다 받도록 최소 수정")
    d.sub("13차 1차 실행(2026-10-07 14:48 UTC)", "13차 1차 실행(2026-10-07 14:48 UTC = 23:48 KST)", W, "원장 UTC 에 KST 를 함께 적음")

    # ── R3 「없음」 단정 → 추출 범위에 없음/찾지 못함 + 찾은 방법 ──
    R = "R3"
    d.sub("법령(법률·시행령)의 시행예정 판: 금융회사의 지배구조에 관한 법률 없음 · 금융회사의 지배구조에 관한 법률 시행령 없음 · 금융지주회사법 없음.",
          "법령(법률·시행령)의 시행예정 판: 금융회사의 지배구조에 관한 법률 · 같은 법 시행령 · 금융지주회사법 모두 추출 범위에 없음"
          "(질의: `lawSearch.do target=eflaw query=금융회사의 지배구조에 관한 법률 nw=2 display=100`(법률·시행령 함께) · "
          "`lawSearch.do target=eflaw query=금융지주회사법 nw=2 display=100` — nw=2 는 시행예정 목록(`scripts/law/resolve.py`), "
          "응답 295·271바이트에서 resolve_law 가 고른 같은 이름 시행예정 행 0건; 2026-10-07 23:48 KST, 원장 "
          "`dart_out/raw/web13/law91/_call_log.csv` 5·9행(UTC 14:48), 목록 응답 원본은 저장하지 않음).",
          R, "critic13 gaps 5 — API 조회 결과를 「없음」으로 단정. 질의·응답 크기·원장 행을 적고 「추출 범위에 없음」으로")
    d.sub("(자산건전성·수익성·유동성 칸에는 각주 표시가 없다)",
          "(자산건전성·수익성·유동성 칸에서는 각주 표시를 찾지 못했다 — 별표 전문을 「숫자+)」·「주)」·「*」·「※」로 찾으면 각주 표시는 "
          "「보통주자본비율1)」과 끝의 각주 줄뿐이고, 나머지 「숫자+)」는 개정 날짜 괄호)",
          R, "원문에 대한 「없다」 단정 → 찾은 방법과 결과")
    d.sub("감독 계량지표의 산정식이라 직접 대응 조는 없고", "감독 계량지표의 산정식이라 직접 대응하는 조는 붙이지 않고", R,
          "조 대응 판단을 「없고」로 단정하지 않음(가장 가까운 조를 적음)")
    d.sub("4-2·4-4·4-5 는 직접 대응 조 없음(판단).", "4-2·4-4·4-5 는 직접 대응하는 조를 붙이지 않음(판단).", R,
          "조 대응 판단 — 「없음」 단정 대신 붙이지 않았다고 적음")
    d.sub("계량지표 등급구분기준)은 직접 대응 조 없음. 보충", "계량지표 등급구분기준)은 직접 대응하는 조를 붙이지 않음(판단). 보충", R,
          "조 대응 판단 — 「없음」 단정 대신 붙이지 않았다고 적음")
    d.sub("위험관리위원회에 대한 그런 문구는 제16조에 없다.",
          "위험관리위원회에 대한 그런 문구는 제16조 글(3-5절에 옮긴 법 제16조 전문)에서 찾지 못했다(추출 범위에 없음 — 제16조 전문 대조).",
          R, "원문에 대한 「없다」 단정 → 찾은 범위")
    d.sub("인용하는 곳을 찾았으나 없었다(정규식", "인용하는 곳을 찾았으나 0건이었다(정규식", R, "검색 결과를 「없었다」 대신 건수로")
    d.sub("근거에도 영 제6조·제20조는 없음(8-1절)", "근거에도 영 제6조·제20조는 0곳(8-1절 위임 문구 20곳 대조)", R, "대조 결과를 건수와 범위로")
    d.sub("근거에도 영 제20조·제6조는 없음(8-1절)", "근거에도 영 제20조·제6조는 0곳(8-1절 위임 문구 20곳 대조)", R, "대조 결과를 건수와 범위로")
    d.sub("검증에서도 감독규정 전 판에 제5호 위임을 받는 조가 없었다",
          "검증에서도 감독규정 전 판에서 제5호 위임을 받는 조를 찾지 못했다(추출 범위에 없음 — 8-1절 검색어 23개)", R,
          "「없었다」 단정 → 찾은 범위", count=2, group=True)
    d.sub("XML 어디에든 「제30조」 낱말: 없음", "XML 어디에든 「제30조」 낱말: 0곳(XML 전체 글 검색)", R, "검색 결과를 건수와 범위로")
    d.sub("「제30조」 낱말 없음", "「제30조」 낱말 0곳(XML 전체 글 검색)", R, "검색 결과를 건수와 범위로", count=3, group=True)
    d.sub("1~4호에 없어", "1~4호에 들지 않아", R, "법령 글 읽기(판단) — 「없어」 대신 「들지 않아」(3-1·3-2절 전문 대조)", count=2, group=True)
    d.sub("영 제6조·제20조를 받는 문구는 없다.", "영 제6조·제20조를 받는 문구는 위 20곳에서 찾지 못했다(추출 범위에 없음 — 위 표 대조).", R,
          "「없다」 단정 → 찾은 범위")
    d.sub("감독규정 8판 어디에도 시행령 제6조제3항제5호·제20조제2항제5호를 받는 조가 없으므로,",
          "감독규정 8판에서 시행령 제6조제3항제5호·제20조제2항제5호를 받는 조를 찾지 못했으므로(추출 범위에 없음 — 위 검색어 23개),", R,
          "「없으므로」 단정 → 찾은 범위")
    d.sub("「금리」 칸이 없다 — 상자 글이", "「금리」 칸을 찾지 못했다(상자 글 전체 대조) — 상자 글이", R, "「없다」 단정 → 찾은 방법")
    d.sub("— 2016년 8월 1일 날짜가 없다.", "— 이 부칙에서 2016년 8월 1일 날짜 문구는 찾지 못했다(8-5절 ② 정규식 — 추출 범위에 없음).", R,
          "「없다」 단정 → 찾은 방법")
    d.sub("(판단 — 직접 대응 조 없음, 1-2절)", "(판단 — 가장 가까운 조, 직접 대응하는 조는 정하지 않음, 1-2절)", R, "조 대응 판단을 「없음」으로 단정하지 않음")
    d.sub("· 제6·8항은 직접 대응 조 없음(판단, 1-5절)", "· 제6·8항은 직접 대응하는 조를 정하지 않음(판단, 1-5절)", R, "조 대응 판단을 「없음」으로 단정하지 않음")
    # 5-1 표 읽기(표 칸 「없음」은 스크립트 표기 — 칸은 그대로 두고 뜻을 적음)
    i = d.idx(lambda i, ln: ln.startswith("- note: 제30조 제목은 38판 모두 「리스크관리조직」."), "5-1 표 뒤 note")
    d.insert_after(i, ["- note(표 읽기 — 정합성 보정 2026-10-08 KST): 「개정문에 제30조」 칸의 「없음」은 그 판 XML 의 제개정이유·마지막 부칙 글에서 "
                       "「제30조」 낱말을 찾지 못했다는 뜻이다(추출 범위에 없음 — 5절 한계 ③의 대조 범위, `scripts/dart/web13_law91.py` 의 개정문30 칸). "
                       "「달라진 글자」 칸의 「U+0020→없음」 꼴은 글자가 빠졌다는 글자 차이 표기다."],
                   R, "표 칸의 「없음」(스크립트 표기)은 고치지 않고 뜻(찾지 못함)과 찾은 범위를 적음")

    # ── R2 조 번호 칸 ──
    Q = "R2"
    i0 = d.head("## 0. 현행 판 재확인(")
    d.insert_after(i0 + 1, [noart_line("쓴 XML 의 현행 여부 확인 표(출처 자료)"), ""], Q, "출처 자료 묶음 — 조 번호 칸이 비어 있었음")
    i53 = d.head("### 5-3 판 전체 목록(38판")
    d.insert_after(i53 + 1, [noart_line("판 목록(연혁 자료 — 제30조 글의 조 대응은 5절 머리 줄, 판단)"), ""], Q, "연혁 판 목록 묶음 — 조 번호 칸이 비어 있었음")
    s85, e85 = d.section("### 8-5 ")
    i = d.idx(lambda i, ln: s85 < i < e85 and ln.startswith("- 모범규준 조(판단): 제8조(이사회) · 제9조(그룹위험관리위원회) — 5절 보충."), "8-5 조 줄")
    d.set_line(i, noart_line("API 목록 밖 판을 다시 찾은 기록(연혁 자료, 5절 보충 — 제30조 글의 조 대응은 5절 머리 줄, 판단)."), Q,
               "연혁 판 찾기 기록 — 특정 조에 닿지 않는 묶음")
    s13, e13 = d.section("### 1-3 [별표 4]")
    i = d.idx(lambda i, ln: s13 < i < e13 and ln.startswith("- 모범규준 조(판단): 직접 대응 조 없음"), "1-3 조 줄")
    d.set_line(i, "- 모범규준 조(판단): %s (판단) — [별표 3] 평가항목의 등급별 정의라 1-1절과 같은 조 행의 「지주 평가·검사·공시」 칸 보조 자료(판단). "
                  "이 별표에 직접 대응하는 조를 따로 정하지는 않음." % arts([8, 10, 21, 25, 28, 37, 56, 57]), Q,
               "R2·R3: 조 번호 칸이 「직접 대응 조 없음」이었음 — 수집 때 괄호에 적은 조(제8·10·21·25·28·37·56·57조)를 조 번호 칸에 실제로 적음")
    s86, e86 = d.section("### 8-6 ")
    i = d.idx(lambda i, ln: s86 < i < e86 and ln.startswith("- 모범규준 조(판단): 1-1·1-3·1-4절과 같음"), "8-6 조 줄")
    union = [7, 8, 10, 13, 14, 16, 19, 20, 21, 22, 23, 25, 28, 33, 37, 56, 57]
    d.set_line(i, "- 모범규준 조(판단): %s (판단) — 1-1·1-3·1-4절과 같은 조(1-1절 15개 조 + 1-4절의 제22조·제23조; "
                  "이 절은 그 절 인용의 물음표 글자 확인용)." % arts(union), Q,
               "critic13 gaps 3 — 「1-1·1-3·1-4절과 같음」 대신 그 절들과 같은 조 번호를 칸에 실제로 적음")
    # 7절 표의 조 번호 칸
    d.sub("모범규준 직접 대응 조 없음(판단, 1-3절)",
          "모범규준 %s(판단 — 1-1절과 같은 조 행의 보조 자료, 1-3절)" % arts([8, 10, 21, 25, 28, 37, 56, 57], "·"), Q,
          "R2·R3: 7절 표 조 번호 칸 — 1-3절 조 줄과 같게")
    d.sub("| 1-1·1-3·1-4절 보조(판단) |", "| 모범규준 %s(판단 — 1-1·1-3·1-4절과 같은 조, 8-6절) |" % arts(union, "·"), Q,
          "7절 표 조 번호 칸 — 8-6절 조 줄과 같게")
    d.sub("· 모범규준 제8조(이사회)·제9조(그룹위험관리위원회)(판단) |",
          "· %s(제30조 글의 조 대응은 5절: 모범규준 제8조(이사회)·제9조(그룹위험관리위원회), 판단) |" % NOART, Q,
          "7절 표 — API 목록 밖 판(연혁 자료) 행의 조 번호 칸",
          pred=lambda i, ln: "금융지주회사감독규정 연혁 가운데 API 목록에 없는 판" in ln)
    d.sub("— 24조는 사용자 9-4 표기 조 번호, 나머지는 판단.", "— 24조는 사용자 9-4 에 적힌 조 번호(9-1 자료에 붙인 대응은 모두 판단).", Q,
          "9-1 의 조 대응은 새로 붙인 것 — 모두 판단")
    d.sub("— 사용자 9-4 표기 조 번호.", "— 사용자 9-4 에 적힌 조 번호(9-1 자료에 붙인 대응은 판단).", Q, "9-1 의 조 대응은 새로 붙인 것 — 판단",
          pred=lambda i, ln: ln.startswith("- 모범규준 조(판단): 제27조(전략 및 평판위험)"))
    n = add_judge(d)
    if n != 19:
        raise SystemExit("[fix13_C 9-1] (판단) 붙인 조 줄 %d(기대 19)" % n)
    d.sub("— 9-1 의 조 대응은 전부 「(판단)」(사용자 9-4 에 적힌 조 번호는 그 번호 그대로).",
          "— 9-1 의 조 대응은 전부 「(판단)」(사용자 9-4 에 적힌 조 번호는 그 번호 그대로). 정합성 보정(2026-10-08 KST): 자료 묶음마다 조 번호 칸 "
          "바로 뒤에 「(판단)」을 붙였고, 연혁·출처 묶음(0절·5-3·8-5)은 「조 번호 해당 없음(연혁·출처 자료)」, 8-6절은 1-1·1-3·1-4절과 같은 조를 실제로 적었다.",
          Q, "머리말에 R2 표기 방식")

    # ── R4 인용 블록마다 출처 줄 ──
    P = "R4"
    s, e = d.section("### 1-4 [별표 5]")
    fs = d.fences(s, e)
    if len(fs) != 12:
        raise SystemExit("[fix13_C 9-1] 1-4절 코드 블록 %d(기대 12)" % len(fs))
    for f in fs:
        k = f - 1
        while not d.lines[k].strip():
            k -= 1
        m = re.search(r"「([^」]+)」", d.lines[k])
        loc = ("[별표 5] 별표내용 「%s」 행" % m.group(1)) if m else "[별표 5] 별표내용 첫머리(개정 연혁 줄·제목·표 머리 행)"
        d.insert_before(f, [cite_sec(loc)], P, "critic13 gaps 4 — 1-4절 머리 「인용:」 줄 하나에 묶인 블록, 블록마다 출처를 짧게 되풀이",
                        key="R4-1-4")
    s, e = d.section("### 1-5 세칙 제12조")
    fs = d.fences(s, e)
    locs = ["제12조 제6항", "제12조 제8항", "제12조 제2항(보충)"]
    if len(fs) != 3:
        raise SystemExit("[fix13_C 9-1] 1-5절 코드 블록 %d(기대 3)" % len(fs))
    for f, loc in zip(fs, locs):
        d.insert_before(f, [cite_sec(loc)], P, "critic13 gaps 4 — 1-5절 머리 「인용:」 줄 하나에 묶인 블록", key="R4-1-5")
    s, e = d.section("### 8-2 ")
    fs = d.fences(s, e)
    if len(fs) != 2:
        raise SystemExit("[fix13_C 9-1] 8-2절 코드 블록 %d(기대 2)" % len(fs))
    d.insert_before(fs[1], [cite_sec("[별표 8] 별표내용 상자 글 「4. (계량지표 산정기준)」", ", 검증 재사용 2026-10-08(KST)")], P,
                    "critic13 gaps 4 — 8-2절 둘째 블록(절 머리 인용 줄에 묶임)")
    s, e = d.section("### 8-3 ")
    fs = d.fences(s, e)
    if len(fs) != 2:
        raise SystemExit("[fix13_C 9-1] 8-3절 코드 블록 %d(기대 2)" % len(fs))
    d.insert_before(fs[1], ["- 출처: [금융회사 지배구조 감독규정 · 일련번호 2100000285614 · %s · [별표 3] 별표내용 보험회사 항목 바.(지급여력비율 관리업무) 줄 · "
                            "수집 2026-10-01(KST, 9차 원본 dart_out/raw/web9/law/금융회사지배구조감독규정_2100000285614.xml), 검증 재사용 2026-10-08(KST)]" % GOV],
                    P, "critic13 gaps 4 — 8-3절 둘째 블록(절 머리 인용 줄에 묶임)")


def fix_csv91(d):
    d.sub("시행예정판: 없음 · 13차 1차 실행(2026-10-07 14:48 UTC)",
          "시행예정판: 추출 범위에 없음(lawSearch.do target=eflaw nw=2 display=100 질의 — 같은 이름 시행예정 행 0건 · 9-1 md 0절 note) · "
          "13차 1차 실행(2026-10-07 14:48 UTC = 23:48 KST)", "R3·R5", "md 0절 note 와 같게 — API 조회 결과를 「없음」으로 단정하지 않음, UTC 에 KST 를 함께",
          count=3, group=True)
    d.sub("「제30조」 낱말 없음", "「제30조」 낱말 0곳(XML 전체 글 검색)", "R3", "md 5-1 제외 표와 같게", count=3, group=True)


# ───────────────────────────── 9-2 의 1·2 ─────────────────────────────
def fix_921(d):
    W = "R5"
    d.sub("- 수집일: 2026-10-07. 연혁 목록과 판 XML 28개(보험업감독규정 14 · 세칙 14)는 같은 날 앞선 에이전트",
          "- 수집일: 2026-10-07~08(KST — 앞선 에이전트 law92 2026-10-07 23:46~23:50 · 이번 실행 law92a 2026-10-08 08:58~08:59 · "
          "현행 재확인 law92b 2026-10-08 08:50 · 검증 verify13_law92 2026-10-08 12:23~12:36; 원장은 모두 UTC). "
          "연혁 목록과 판 XML 28개(보험업감독규정 14 · 세칙 14)는 앞선 에이전트",
          W, "원장 UTC law92 14:46~14:50(=KST 10-07 23:46~23:50), law92a 23:58~23:59(=KST 10-08 08:58~08:59), verify13_law92 03:23~03:36(=KST 12:23~12:36) — "
             "「2026-10-07」 하나로는 실제 날짜와 다름, 「같은 날」도 KST 로는 다른 날")
    d.sub("[검증 보충 2026-10-07", "[검증 보충 2026-10-08(KST)", W, "검증(verify13_law92 fix)은 KST 2026-10-08(파일 보정 12:42 KST)", count=4, group=True)
    d.sub("검증 보정 2026-10-07)", "검증 보정 2026-10-08(KST))", W, "검증 보정은 KST 2026-10-08")
    d.sub("검증(2026-10-07)", "검증(2026-10-08 KST)", W, "검증은 KST 2026-10-08", count=2, group=True)
    d.sub("note(검증 2026-10-07)", "note(검증 2026-10-08 KST)", W, "검증은 KST 2026-10-08")
    d.sub("note(검증 보충 2026-10-07)", "note(검증 보충 2026-10-08 KST)", W, "검증은 KST 2026-10-08")
    d.sub("## 1. 현행 판 재확인(2026-10-07 UTC — 조회 시각 칸은 KST)", "## 1. 현행 판 재확인(2026-10-08 KST — 원장은 UTC 2026-10-07 23:58)", W,
          "조회 시각 2026-10-08T08:59 KST — 제목 날짜를 KST 로")
    d.sub("(nw=2, 같은 날 23:46 KST 조회)", "(nw=2, 2026-10-07 23:46 KST 조회 — 앞선 에이전트)", W, "현행 재확인(10-08 KST)과 다른 날")
    d.sub("## 6. 검증 보충(2026-10-07)", "## 6. 검증 보충(2026-10-08 KST)", W, "검증 요청 UTC 2026-10-08 03:23~ = KST 12:23~ — 대조 스크립트 앵커는 두 제목을 다 받도록 최소 수정")
    d.sub("(2-1 note 의 nw=2 목록, 같은 날 받은 것)", "(2-1 note 의 nw=2 목록, 2026-10-07 23:46 KST 에 받은 것)", W, "검증(10-08 KST)과 다른 날")
    d.sub("요청 시각 2026-10-08 03:23~ UTC)", "요청 시각 2026-10-08 03:23~ UTC = 12:23~ KST)", W, "원장 UTC 에 KST 를 함께")
    d.sub("## 검증 기록(2026-10-07)", "## 검증 기록(2026-10-08 KST)", W, "검증은 KST 2026-10-08 — 대조 스크립트 앵커는 두 제목을 다 받도록 최소 수정")
    d.sub("2016.3.30 보도자료", "2016.3.30(배포일) 보도자료", W, "보도자료 날짜 종류(인용 꼬리표의 「배포 2016.3.30」)를 붙임", count=5, group=True)
    d.sub("보도자료(2016.3.30)", "보도자료(2016.3.30 배포)", W, "보도자료 날짜 종류를 붙임")

    R = "R3"
    d.sub("2016.06.10·2016.06.23 판에 없다가 2016.06.30 판에 다시 있다(있음→없음→있음 — 6-1 note·6-4)",
          "2016.06.10·2016.06.23 판 XML 에서는 찾지 못하고 2016.06.30 판에 다시 있다(판목록 csv 표기 있음→없음→있음 — 조문내용 표지 검색, 6-1 note·6-4)",
          R, "「없다가」 단정 → 찾은 방법")
    d.sub("세칙 판에는 없어 그 개정 취지는", "세칙 판 XML 에서는 찾지 못해(요소 이름 검색 — 6-6) 그 개정 취지는", R, "「없어」 단정 → 찾은 방법")
    d.sub("로 다시 확인했다 — 바뀐 곳 없음.", "로 다시 확인했다 — 결론 같음.", R, "대조 결과 — 「없음」 단정 대신 결론이 같다고 적음")
    d.sub("16(2000000080470)에는 「제7-5조」 표지 없음 — 인접", "16(2000000080470)에서는 「제7-5조」 표지를 찾지 못함(조문내용 표지 검색 find_jo) — 인접",
          R, "「없음」 단정 → 찾은 방법")
    d.sub("문구는 순번 70(2100000041346)에 없고 바로 다음 순번 71(2100000044084)에 있다.",
          "문구는 순번 70(2100000041346)의 제7-5조에서는 찾지 못했고(정규식) 바로 다음 순번 71(2100000044084)에 있다.", R, "「없고」 단정 → 찾은 방법")
    d.sub("검증 뒤 받은 판 127 · 받지 않은 순번 없음 ·", "검증 뒤 받은 판 127 · 받지 않은 순번 0개 ·", R, "받지 않은 판 수를 건수로")
    d.sub("- note: 이 판 XML 에는 <개정문> 요소가 없다.", "- note: 이 판 XML 의 요소 이름에서 <개정문> 은 찾지 못했다(추출 범위에 없음 — 이 판 XML 요소 이름 전체 대조).",
          R, "「없다」 단정 → 찾은 범위")
    d.sub("판 XML 에는 제5-6조의2 가 없다 — 6-1 note·6-4]", "판 XML 에서는 제5-6조의2 를 찾지 못했다 — 조문내용 표지 검색, 6-1 note·6-4]", R, "「없다」 단정 → 찾은 방법")
    d.sub("판과 세칙 판에는 <제개정이유> 없음(6-6)", "판과 세칙 판 XML 에서는 <제개정이유> 를 찾지 못함(6-6 요소 이름 검색)", R, "「없음」 단정 → 찾은 방법")
    d.sub("세칙 판(2200000047377)에 제5-6조의2 없음, 처음 나온 판은", "세칙 판(2200000047377) XML 에서 제5-6조의2 를 찾지 못함(조문내용 표지·정규식 검색), 처음 나온 판은",
          R, "「없음」 단정 → 찾은 방법")
    d.sub("— 제7-5조·제5-6조의2·[별표 37]·문구 모두 없음 |", "— 제7-5조·제5-6조의2·[별표 37]·문구 모두 찾지 못함(판 XML 전체 대조) |", R, "「없음」 단정 → 찾은 방법")
    d.sub("판 XML 에 제5-6조의2·제5-3조의2 가 없음(앞", "판 XML 에서 제5-6조의2·제5-3조의2 를 찾지 못함(조문내용 표지 검색; 앞", R, "「없음」 단정 → 찾은 방법")
    d.sub("의 어느 판의 제7-5조에도 없고", "의 어느 판의 제7-5조에서도 찾지 못했고(127판 전수 정규식 대조)", R, "「없고」 단정 → 찾은 방법")
    d.sub("판 XML 에는 제5-6조의2 가 없다. 두 판에서는", "판 XML 에서는 제5-6조의2 를 찾지 못했다(조문내용 표지 검색). 두 판에서는", R, "「없다」 단정 → 찾은 방법")
    d.sub("정규식이 맞는 곳이 없다.", "정규식이 맞는 곳은 0곳이다.", R, "검색 결과를 건수로")
    d.sub("까닭은 법제처 자료에 설명 없음(판단 보류)", "까닭은 법제처 자료(판 XML 제개정이유·부칙)에서 찾지 못함(판단 보류)", R, "「없음」 단정 → 찾은 범위")
    d.sub("XML 에는 <제개정이유> 요소가 없다(검증 search", "XML 에서는 <제개정이유> 요소를 찾지 못했다(검증 search", R, "「없다」 단정 → 찾은 방법")
    d.sub("에는 제5-6조의2 가 없고,", "에서는 제5-6조의2 를 찾지 못했고,", R, "「없고」 단정 → 찾지 못함")
    d.sub("정규식이 맞는 곳도 없다(검증 scan)", "정규식이 맞는 곳도 0곳이다(검증 scan)", R, "검색 결과를 건수로")
    d.sub("두 자료에 설명 없음, 판단 보류", "두 자료에서 설명을 찾지 못함, 판단 보류", R, "「없음」 단정 → 찾지 못함")
    d.sub("— 요소 없음)", "— 요소를 찾지 못함)", R, "「없음」 단정 → 찾지 못함")
    d.sub("문구·조·별표가 없음을 확인(6-2)", "문구·조·별표를 찾지 못함을 확인(6-2 — 판 XML 전체 대조)", R, "「없음」 단정 → 찾은 범위")
    d.sub("「표기만 다름(판단)」, 그 밖은 「글 바뀜」.",
          "「표기만 다름(판단)」, 그 밖은 「글 바뀜」. 표의 「없음」·「없음→있음」·「있음→없음」·「같음(둘 다 없음)」(판목록 csv 표기 — 칸은 그대로 둠)은 "
          "그 판 XML 에서 해당 조 표지(find_jo)나 [별표 37] 별표단위(별표번호 0037)를 찾지 못했다는 뜻이다(추출 범위에 없음 — 그 판 XML 전체를 찾음; "
          "정합성 보정 2026-10-08 KST).",
          R, "표 칸의 「없음」(판목록 csv·대조 스크립트가 같은 글자를 요구) — 칸은 그대로 두고 뜻을 비교 기준 줄에 적음")

    # 모순(contradictions 0): 3-6 note
    s36, e36 = d.section("### 3-6 [별표 37]")
    i = d.idx(lambda i, ln: s36 < i < e36 and ln.startswith("- note: 받은 세칙 판 15개 가운데 [별표 37]"), "3-6 note")
    d.set_line(i, "- note: 판목록 csv(`dart_out/risk13/9-2-1_2_판목록.csv` 「검증_」 열) 기준 — 연혁 목록 184판 가운데 받은 세칙 판 155개(수집 때 15개 + 검증 때 140개; "
                  "받지 않은 순번 139~142·147~148·150·155~159·161~170·172~176·178~179 는 모두 [별표 37] 이 처음 나온 순번 181 보다 앞) 가운데 "
                  "[별표 37](별표구분 「별표」)이 있는 판은 2200000108841(순번 181, 처음 나온 판) · 2200000108867(순번 182, 발령 2026.07.13 · 시행 2026.07.15, "
                  "검증 때 받음) · 2200000108939(순번 183, 현행) 셋이고, 세 판의 별표내용은 글자 그대로 같다(41229자, 판목록 csv 검증_글_sha256 앞 12자 a1386075bda3 — 6-4 변화 표에 순번 182 가 없는 것은 앞 판과 「같음」이기 때문). "
                  "앞 판(순번 180, 2200000108697) XML 의 별표단위에서는 [별표 37] 을 찾지 못했다(추출 범위에 없음 — 별표번호 0037·별표구분 「별표」로 찾음; "
                  "같은 번호의 「별지 37」(수습연기신청서)은 별개). 위 표는 수집 때 받은 판만 싣는다(순번 182 는 판목록 csv 행).",
               "모순·R3", "critic13 contradictions 0 — 수집 때 note(받은 판 15개, 108867 받지 않음)가 검증 뒤(판목록 csv 108867 검증_판_받음 Y·검증_있음 Y, "
                          "[별표 37] 있는 판 3개, 세칙 155판 받음; 6-4·검증 기록) 고쳐지지 않았음 — 검증 뒤 사실로 고침")
    s38, e38 = d.section("### 3-8 받은 판별")
    last = max(j for j in range(s38, e38) if d.lines[j].startswith("| 183 |"))
    d.insert_after(last, ["", "- note(표 읽기 — 정합성 보정 2026-10-08 KST): 이 표는 수집 때 받은 15판만 싣는다. 검증 때 받은 판까지 보면(판목록 csv 「검증_」 열) "
                              "순번 182(2200000108867, 발령 2026.07.13 · 시행 2026.07.15)에도 [별표 37] 이 있고(41229자, 181·183 과 같은 글), 제5-6조의2 글도 181 과 같다(101자). "
                              "「[별표 37]」 칸 「없음」은 그 판 XML 별표단위에서 [별표 37] 을 찾지 못했다는 뜻이다(추출 범위에 없음 — 별표번호 0037·별표구분 별표로 찾음)."],
                   "모순·R3", "3-6 note 와 같은 사실을 3-8 표 아래에도 — 수집 때 15판 표와 검증 뒤 155판 결론이 어긋나 보이지 않게")

    Q = "R2"
    i1 = d.head("## 1. 현행 판 재확인(")
    d.insert_after(i1 + 1, [noart_line("현행 판 확인 표(출처 자료)"), ""], Q, "출처 자료 묶음 — 조 번호 칸이 비어 있었음")
    for prefix, desc in (("### 2-9 ", "받은 판별 제7-5조 글 대조 표(연혁 자료 — 제7-5조 글의 조 대응은 2-2~2-8절, 판단)"),
                         ("### 3-8 ", "받은 판별 제5-6조의2·[별표 37] 대조 표(연혁 자료 — 조 글의 조 대응은 3-2~3-7절, 판단)"),
                         ("### 6-1 ", "덮은 범위·처음 든 판 재확인 표(연혁 자료 — 조 글의 조 대응은 2·3절, 판단)"),
                         ("### 6-2 ", "옛 이름 판 목록(연혁 자료)"),
                         ("### 6-3 ", "제7-5조 127판 변화 표(연혁 자료 — 제7-5조 글의 조 대응은 2-2~2-8절, 판단)"),
                         ("### 6-4 ", "제5-6조의2·[별표 37] 받은 판 변화 표(연혁 자료 — 조 글의 조 대응은 3-2~3-7절, 판단)"),
                         ("### 6-6 ", "개정 표지·<제개정이유> 요소 대조(출처 자료)")):
        s, e = d.section(prefix)
        i = d.idx(lambda i, ln: s < i < e and ln.startswith("- 모범규준 조(판단"), "%s 조 줄" % prefix)
        d.set_line(i, noart_line(desc), Q, "연혁 판 목록·출처 묶음 — 특정 조에 닿지 않는 묶음(%s)" % prefix.strip("# "))
    n = add_judge(d)
    if n != 3:
        raise SystemExit("[fix13_C 9-2-1_2] (판단) 붙인 조 줄 %d(기대 3)" % n)
    d.sub("2·3·6절 자료 묶음마다 「- 모범규준 조」 줄을 같은 기준으로 붙였다(전부 판단).",
          "2·3·6절 자료 묶음마다 「- 모범규준 조」 줄을 같은 기준으로 붙였다(전부 판단). 정합성 보정(2026-10-08 KST): 조 번호 칸 바로 뒤에 「(판단)」, "
          "연혁 판 목록·출처 묶음(1절·2-9·3-8·6-1~6-4·6-6)은 「조 번호 해당 없음(연혁·출처 자료)」.", Q, "머리말에 R2 표기 방식")


# ───────────────────────────── 9-2 의 3·5 ─────────────────────────────
def fix_923(d):
    W = "R5"
    d.sub("- 검증(2026-10-07):", "- 검증(2026-10-08 KST):", W, "검증(verify13_law92)은 KST 2026-10-08")
    d.sub("[검증 2026-10-07:", "[검증 2026-10-08(KST):", W, "검증은 KST 2026-10-08")
    d.sub("검증 2026-10-07:", "검증 2026-10-08(KST):", W, "검증은 KST 2026-10-08", count=2, group=True)
    d.sub("## 5. 검증 보충(2026-10-07)", "## 5. 검증 보충(2026-10-08 KST)", W, "검증은 KST 2026-10-08")
    d.sub("## 검증 기록(2026-10-07)", "## 검증 기록(2026-10-08 KST)", W, "검증은 KST 2026-10-08 — 대조 스크립트 앵커는 두 제목을 다 받도록 최소 수정")
    d.sub("같은 날 9-2 1·2번 에이전트가 받은 연혁 목록", "앞서(2026-10-07 23:46 KST) 9-2 1·2번 에이전트가 받은 연혁 목록", W,
          "이 파일의 현행 재확인(2026-10-08T08:50 KST)과 KST 로는 다른 날")

    R = "R3"
    d.sub("옮긴 줄에 깨진 글자가 없음)", "옮긴 줄에서 깨진 글자(ASCII `?`)는 찾지 못함 — 2-1 note)", R, "「없음」 단정 → 찾은 방법")
    d.sub("아래에 옮긴 줄에는 하나도 없다(물음표 있는 옮긴 줄: 없음).", "아래에 옮긴 줄에서는 하나도 찾지 못했다(물음표 있는 옮긴 줄 0줄 — 제목줄 csv 「물음표」 칸).",
          R, "「없다」 단정 → 건수와 찾은 곳")
    d.sub("정의 줄에는 하위위험 구분 문구가 없다.", "정의 줄에서는 하위위험 구분 문구를 찾지 못했다(추출 범위에 없음 — 5-2절 검색어 12개).", R, "「없다」 단정 → 찾은 범위")
    d.sub("제5장 신용위험액은 하위 「…위험액」 구분이 없어", "제5장 신용위험액에서는 하위 「…위험액」 구분을 찾지 못해(5-2절 검색어)", R, "「없어」 단정 → 찾은 방법")
    d.sub("④ 신용위험액(하위 위험액 구분 없음,", "④ 신용위험액(하위 위험액 구분은 5-2절 검색어로 찾지 못함 — 추출 범위에 없음,", R, "「없음」 단정 → 찾은 방법")
    d.sub("모범규준에는 보험위험만 다루는 조가 없다(조목록 기준).", "모범규준 조목록(1~59조 제목)에서 보험위험만 다루는 조는 찾지 못했다.", R, "「없다」 단정 → 찾은 범위")
    d.sub("(표 칸 등, 옮긴 줄에는 없음)", "(표 칸 등, 옮긴 줄에서는 0개)", R, "「없음」 단정 → 건수")
    d.sub("「생명·장기손해보험위험」「일반손해보험위험」「시장위험」 꼴은 한 곳도 없고,",
          "「생명·장기손해보험위험」「일반손해보험위험」「시장위험」 꼴은 0곳이고(같은 정규식, [별표 22] 별표내용 전체),", R, "「없고」 단정 → 건수와 찾은 범위")
    d.sub("주석(/Annots) 있는 쪽 없음, 서식(/AcroForm) 없음,", "주석(/Annots) 있는 쪽 0쪽, 서식(/AcroForm) 0개,", R, "PDF 구조 검사 결과를 건수로")
    d.sub("신용·운영리스크의 하위위험 이름은 여기에도 없다(", "신용·운영리스크의 하위위험 이름은 여기에서도 찾지 못했다(추출 범위에 없음 — 같은 검색어; ", R,
          "「없다」 단정 → 찾은 방법")
    d.sub("2016.8.1 판 조 제목에 감독당국 점검·조치 조가 없음)", "2016.8.1 판 조 제목 목록(1~59조)에서 감독당국 점검·조치 조를 찾지 못함)", R,
          "「없음」 단정 → 찾은 범위(1-1 표 조 번호 칸 — 대조 스크립트는 앞 8칸만 봄)", count=2, group=True)

    Q = "R2"
    i0 = d.head("## 0. 현행 판 재확인")
    d.insert_after(i0 + 1, [noart_line("현행 판 확인 표(출처 자료)"), ""], Q, "출처 자료 묶음 — 조 번호 칸이 비어 있었음")
    for prefix, desc in (("### 2-1 ", "[별표 22] 별표 단위 목록(출처 자료 — 위험 분류 글의 조 대응은 2-2~2-8절, 판단)"),
                         ("### 5-1 ", "[별표 37] PDF·hwp 원본 대조 기록(출처 자료)")):
        s, e = d.section(prefix)
        i = d.idx(lambda i, ln: s < i < e and ln.startswith("- 모범규준 조(판단"), "%s 조 줄" % prefix)
        d.set_line(i, noart_line(desc), Q, "출처 묶음 — 특정 조에 닿지 않는 묶음(%s)" % prefix.strip("# "))
    n = add_judge(d)
    if n != 2:
        raise SystemExit("[fix13_C 9-2-3_5] (판단) 붙인 조 줄 %d(기대 2)" % n)
    d.sub("붙인 조 번호는 모두 「(판단)」(2016.8.1 판 조 제목 기준, `dart_out/risk13/모범규준_조목록.csv`).",
          "붙인 조 번호는 모두 「(판단)」(2016.8.1 판 조 제목 기준, `dart_out/risk13/모범규준_조목록.csv`). 정합성 보정(2026-10-08 KST): 조 번호 칸 바로 뒤에 "
          "「(판단)」, 출처 묶음(0절·2-1·5-1)은 「조 번호 해당 없음(연혁·출처 자료)」. 우리 글의 「없음」 단정은 「찾지 못함/추출 범위에 없음」+찾은 방법으로 고쳤다.",
          Q, "머리말에 R2·R3 표기 방식")


# ───────────────────────────── 정합성 보정 소절 ─────────────────────────────
KEEP_CATS = [
    ("R2 조 번호 칸 표기 「조 번호 해당 없음(연혁·출처 자료)」", re.compile(re.escape(NOART))),
    ("지시서·사용자 표기에 대한 서술(지시서 전문을 읽은 사실 — 예: 「지시서 9-2 에 조 번호 없음」「사용자 9-4 에 없음」)", re.compile(r"지시서|사용자 9-4")),
    ("글자 차이 표기(「U+0020→없음」 꼴)", re.compile(r"→없음|없음→U")),
    ("표 칸·판목록 csv 표기(「같음(둘 다 없음)」·「없음→있음」·「있음→없음」·「없음」 칸 — 뜻은 표 읽기 note 에 적음)", re.compile(r"^\|")),
    ("「추출 범위에 없음」 뜻풀이·판단 표지 안의 말(예: 「없다는 단정이 아니다」「변화 없음으로 봄(판단)」)", re.compile(r"단정|\(판단|판단\)")),
    ("XML·문서 꼴 서술·원본 전체 대조 결과·옛 글 인용과 그 밖(예: 「법령에는 쪽이 없어」「조문번호 칸 없음」「영향이 없다」「보장은 없다」"
     "「빠진 번호 없음(1~21 연속)」「API 목록에 없는 판」)", re.compile(r".")),
]
EOP = re.compile(r"없음|없다|없었|없어|없는|없고|없으")


def keep_eops(d, out):
    """보정 뒤에도 우리 글에 남은 「없음」류 — 갈래별 수와 줄(보정 뒤)."""
    _, pos = d.final()
    cats = [[] for _ in KEEP_CATS]
    for i, ln in enumerate(d.lines):
        if i in d.code or i in d.fixed:
            continue
        t = re.sub(r"추출 범위에 없음", "", ln)
        if not EOP.search(t):
            continue
        for k, (nm, rx) in enumerate(KEEP_CATS):
            if rx.search(t):
                cats[k].append(pos[i])
                break
    rows = []
    for (nm, _), ls in zip(KEEP_CATS, cats):
        if ls:
            rows.append("  - %s: %d줄(줄마다 대조해 확인) — %s" % (nm, len(ls), "·".join(str(x) for x in ls[:40]) + (" …" if len(ls) > 40 else "")))
    return rows


def short(s, n=170):
    s = (" ⏎ ".join(s) if isinstance(s, list) else s).replace("|", "｜").replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…"


def record(d, regen, extra_lines):
    _, pos = d.final()
    mine = [x for x in LOG if x["파일"] == d.path]
    rows, seen = [], {}
    for x in mine:
        if x["종류"] == "끼움":
            ln = pos[x["_i"]]
            where = "%d 앞" % ln if x["_side"] == "before" else "%d 뒤" % ln
        else:
            where = str(pos[x["줄_기준사본"] - 1])
        key = x.get("묶음")
        if key:
            if key in seen:
                seen[key]["줄"].append(where)
                continue
            r = dict(규칙=x["규칙"], 줄=[where], 이유=x["이유"])
            if x["종류"] == "끼움":
                r.update(전="(새 줄)", 후=x["후"][0])
            elif key == JUDGE_KEY:
                r.update(전=JUDGE_SHOW[0], 후=JUDGE_SHOW[1])
            else:
                old, new = key.split("\x00")
                r.update(전="「%s」" % old, 후="「%s」" % new)
            seen[key] = r
            rows.append(r)
        elif x.get("_frag"):
            rows.append(dict(규칙=x["규칙"], 줄=[where], 이유=x["이유"], 전="「%s」" % x["_frag"][0], 후="「%s」" % x["_frag"][1]))
        else:
            rows.append(dict(규칙=x["규칙"], 줄=[where], 이유=x["이유"], 전=("(새 줄)" if x["종류"] == "끼움" else x["전"]),
                             후=(x["후"] if x["종류"] != "끼움" else [y for y in x["후"] if y] or [""]),
                             full=x["규칙"].startswith("모순")))
    out = [SEC_TITLE, "",
           "- 무엇: critic13(`dart_out/risk13/critic13.json`) 의 그룹 C(법령) 항목 — 13차 정합성 보정 규칙 R1~R5 로 상태·표지·출처 줄·note 만 고침. "
           "원문 인용(코드 블록 안 글)은 한 글자도 바꾸지 않음(출처 줄을 블록 앞에 끼운 것만 — `scripts/dart/fix13_C.py check` 가 기준 사본과 인용 줄을 대조).",
           "- 스크립트: `scripts/dart/fix13_C.py`(인자 없이 = 보정, `check` = 확인). 기준 사본 = 커밋 496ddc4 의 이 파일(`dart_out/raw/web13/fix13_C/pre/`) — "
           "언제나 그 사본에서 다시 만듦(멱등). 고친 곳 전부(전·후 전문): `dart_out/raw/web13/fix13_C/fix_log.json`. 실행 %s(KST)." % FIXD,
           "- 재생성 순서: %s → `fix13_C.py`(대조 스크립트의 fix 는 검증 전 사본에서 다시 만들어 이 보정을 지움)." % regen,
           "- 대조 스크립트 최소 수정: `verify13_law91.py` — 「## 8. 검증 보충」·「## 검증 기록」 앵커가 「(2026-10-08 KST)」 제목도 받음. "
           "`verify13_law92.py` — 「## 검증 기록」·「## 5./6. 검증 보충」 앵커가 「(2026-10-08 KST)」 제목도 받고, 「- 모범규준 조」 줄의 (판단) 검사가 "
           "「조 번호 해당 없음(연혁·출처 자료)」 줄을 받음. 보정 뒤 두 스크립트(인자 없이) 모두 문제 0 · exit 0."] + extra_lines + [
           "- 그대로 둔 「없음」(R3 판단 — 원문이 아닌 우리 글 가운데 「없음」으로 무엇이 없다고 단정하지 않는 것, 보정 뒤 줄 번호; 「고친 곳(전·후)」 지난 기록 안의 글은 셈하지 않음 — 대조로 확인):"]
    out += keep_eops(d, out)
    out += ["", "| 규칙 | 줄(보정 뒤) | 이유 | 전 | 후 |", "|---|---|---|---|---|"]
    for r in rows:
        ls = r["줄"]
        lab = "·".join(ls[:25]) + (" 외 %d곳" % (len(ls) - 25) if len(ls) > 25 else "") + (" (%d곳)" % len(ls) if len(ls) > 1 else "")
        n = 100000 if r.get("full") else 200
        out.append("| %s | %s | %s | %s | %s |" % (r["규칙"], lab, short(r["이유"], 260), short(r["전"], n), short(r["후"], n)))
    return out


# ───────────────────────────── 확인 ─────────────────────────────
def quote_lines(text):
    out, inc = [], False
    for ln in text.split("\n"):
        if FENCE.match(ln):
            inc = not inc
            out.append(ln)
            continue
        if inc or ln.startswith(">"):
            out.append(ln)
    return out


def check():
    probs = []
    if not os.path.exists(LOGF):
        print("fix_log 없음 — 먼저 보정")
        return 1
    log = json.load(open(LOGF, encoding="utf-8"))
    cur = {}
    for p in FILES:
        t = open(p, "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
        cur[p] = (t, set(t.split("\n")))
    last = {}
    for x in log["고친곳"]:
        if x["종류"] == "끼움" or x["종류"] == "소절":
            for y in (x["후"] if isinstance(x["후"], list) else [x["후"]]):
                if y and y not in cur[x["파일"]][1]:
                    probs.append("%s: 끼운 줄이 없음 — %s" % (os.path.basename(x["파일"]), y[:80]))
        else:
            last[(x["파일"], x["줄_기준사본"])] = x["후"]
    for (p, ln), after in last.items():
        if after not in cur[p][1]:
            probs.append("%s 기준 %s줄: 「후」가 지금 파일에 없음 — %s" % (os.path.basename(p), ln, after[:80]))
    for p in (MD91, MD921, MD923):
        a = quote_lines(open(pre_path(p), encoding="utf-8").read())
        b = quote_lines(cur[p][0])
        if a != b:
            k = next((j for j, (u, v) in enumerate(zip(a, b)) if u != v), min(len(a), len(b)))
            probs.append("%s: 원문 인용 줄이 기준 사본과 다름(%d번째 인용 줄)" % (os.path.basename(p), k + 1))
        t = cur[p][0]
        tl = t.split("\n")
        for bad in ("## 검증 기록(2026-10-07)", "## 8. 검증 보충(2026-10-07)", "## 6. 검증 보충(2026-10-07)", "## 5. 검증 보충(2026-10-07)",
                    "- note: 받은 세칙 판 15개 가운데 [별표 37]", "- 모범규준 조(판단): 1-1·1-3·1-4절과 같음",
                    "- 모범규준 조(판단): 직접 대응 조 없음"):
            if any(ln.startswith(bad) for ln in tl):
                probs.append("%s: 고쳤어야 할 줄이 남음 — %s" % (os.path.basename(p), bad))
        if t.count(SEC_TITLE) != 1:
            probs.append("%s: 「%s」 소절 %d개" % (os.path.basename(p), SEC_TITLE, t.count(SEC_TITLE)))
    if "시행예정판: 없음" in cur[CSV91][0]:
        probs.append("9-1_법령판.csv: 「시행예정판: 없음」이 남음")
    n_q = sum(len(quote_lines(open(pre_path(p), encoding="utf-8").read())) for p in (MD91, MD921, MD923))
    print("fix_log %d건 · 줄 「후」 %d곳 · 원문 인용 줄 %d줄 대조 · 문제 %d건" % (len(log["고친곳"]), len(last), n_q, len(probs)))
    for x in probs[:20]:
        print("  " + x)
    return 0 if not probs else 1


def run_verify():
    rc = 0
    for v in VERIFY:
        r = subprocess.run([sys.executable, "-I", v], capture_output=True, text=True)
        tail = [ln for ln in r.stdout.strip().split("\n") if ln.startswith("문제")]
        print("%s → exit %d · %s" % (v, r.returncode, tail[-1] if tail else r.stdout.strip()[-200:]))
        rc |= r.returncode
    return rc


def main():
    ensure_pre()
    check_jo_titles()
    d91, d921, d923, dcsv = Doc(MD91), Doc(MD921), Doc(MD923), Doc(CSV91, md=False)
    fix_91(d91)
    fix_csv91(dcsv)
    fix_921(d921)
    fix_923(d923)
    regen = {MD91: "`verify13_law91.py fix`", MD921: "`verify13_law92.py fix`", MD923: "`verify13_law92.py fix`"}
    extra = {
        MD91: ["- 비평 대응: gaps 3(8-6절 「1-1·1-3·1-4절과 같음」 → 조 번호 칸에 실제 조), gaps 4(1-4절 블록 11개·1-5절 2개·8-2·8-3절 각 1개 — "
               "블록마다 출처 줄; 1-4절 표 머리 블록·1-5절 제6항 블록에도 같은 꼴로 더함), gaps 5(0절 「시행예정 판: … 없음」 → 추출 범위에 없음 + 질의), "
               "contradictions 5(「검증(2026-10-07)」 라벨 ↔ 실제 2026-10-08T09:11 KST).",
               "- 날짜 라벨(R5) 결정: 원장 시각(UTC)을 KST 로 바꿔 정함 — 1차 수집 law91 UTC 2026-10-07 14:48~14:51 = KST 2026-10-07 23:48~23:51 → "
               "「현행 재확인 2026-10-07」「수집 2026-10-07」은 맞아 그대로(시간대만 머리에 적음). 검증 verify13_law91 UTC 2026-10-08 00:10~00:11 "
               "(md 보정 09:26 KST) → 「검증(…)」「검증 재사용」「8. 검증 보충」「검증 기록」은 2026-10-08 KST. 9·10·11차 원본의 「수집 2026-10-01/02」는 "
               "meta fetched_at(+09:00) 그대로 맞음."],
        MD921: ["- 비평 대응: contradictions 0(3-6 note 「받은 세칙 판 15개 … 2200000108867 은 받지 않음」 → 판목록 csv 「검증_」 열·6-4·검증 기록과 같게: "
                "세칙 155판 받음, [별표 37] 있는 판 108841·108867·108939 셋, 세 판 별표내용 같음 — 아래 표 「모순·R3」 행에 전·후), "
                "R2(연혁 판 목록 묶음 → 조 번호 해당 없음, 나머지 조 번호 칸 바로 뒤 (판단)), R3·R5.",
                "- 날짜 라벨(R5) 결정: law92 UTC 2026-10-07 14:46~14:50 = KST 10-07 23:46~23:50 · law92a UTC 23:58~23:59 = KST 10-08 08:58~08:59 · "
                "law92b UTC 23:50 = KST 10-08 08:50 · verify13_law92 UTC 10-08 03:23~03:36 = KST 12:23~12:36 → 수집일 「2026-10-07~08(KST)」, "
                "검증 라벨 「2026-10-08(KST)」. 인용 꼬리표의 「수집 …+09:00」 시각은 KST 그대로 맞아 두었다."],
        MD923: ["- 비평 대응: R2(출처 묶음 0절·2-1·5-1 → 조 번호 해당 없음, 나머지 조 번호 칸 바로 뒤 (판단)), R3(우리 글의 「없음」 단정 — 아래 표 R3 행), "
                "R5(검증 라벨 → 2026-10-08 KST, 「같은 날」 → 실제 KST 시각).",
                "- 날짜 라벨(R5) 결정: 현행 재확인 law92b 2026-10-08T08:50:18+09:00(KST) 그대로, 9-2 1·2번 에이전트의 연혁 목록 2026-10-07T23:46:09+09:00(KST), "
                "검증 verify13_law92 KST 2026-10-08 12:23~12:42 → 검증 라벨 2026-10-08(KST). 「수집 2026-10-01」(9·10차 원본)은 그대로 맞음."],
    }
    docs = [d91, d921, d923]
    secs = {}
    for d in docs:
        secs[d.path] = record(d, regen[d.path], extra[d.path])
    # 기록 쓰기
    os.makedirs(FD, exist_ok=True)
    out_log = []
    for x in LOG:
        y = {k: v for k, v in x.items() if not k.startswith("_") and k != "묶음"}
        out_log.append(y)
    for d in docs:
        out_log.append(dict(파일=d.path, 줄_기준사본="끝", 종류="소절", 전="", 후=secs[d.path], 규칙="기록",
                            이유="「## 검증 기록」 끝 「%s」 소절" % SEC_TITLE))
    json.dump(dict(스크립트="scripts/dart/fix13_C.py", 기준="커밋 %s" % BASE, 날짜="%s(KST)" % FIXD,
                   규칙="13차 정합성 보정 R1~R5(그룹 C)", 고친곳=out_log),
              open(LOGF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for d in docs:
        d.write(extra=secs[d.path])
    dcsv.write()
    from collections import Counter
    c = Counter((os.path.basename(x["파일"]), x["규칙"]) for x in LOG)
    for k in sorted(c):
        print("%s %s %d" % (k[0], k[1], c[k]))
    rc = check()
    rc |= run_verify()
    return rc


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(check())
    sys.exit(main())
