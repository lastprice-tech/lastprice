#!/usr/bin/env python3
"""15차 사업보고서 조각 g1(KB·신한·하나·우리금융지주) 검증 — 인자 없이 실행, 결과 dart_out/ops15/verify15_bs_g1.txt, exit 0(통과)/1(문제).

대상: dart_out/ops15/조각/A_bs_g1.csv · B_bs_g1.csv · D_bs_g1.csv (생성기 scripts/dart/ops15_bs_g1.py)
대조 항목
 (a) 모든 행 source_text(그리고 reason_text 가 「문서에 없음」이 아니면 그것도) ↔ 그 행 출처 원문
     (사업보고서 = dart_out/text/ops15 md, 경영공시 = 13차 텍스트 zip) — 공백·줄바꿈·「|」만 무시하고 글자 그대로
 (b) page ↔ 실제 위치: 「XML [절 n] 「제목」 [표 m]」 = 그 글이 그 절(제목 같음)·그 표 안에 있음,
     「; p.N(본문 PDF, 13차 보관)」 = 13차 본문 PDF 텍스트 N쪽에서 그 글(앞 40·20·12자)이 시작,
     경영공시 「p.N[,p.M]」 = 13차 경영공시 텍스트 그 쪽들 안, 「문서에 없음」 행 = 찾은 범위(절 제목 또는 쪽 범위)가 실제 있음
 (c) 열 이름(COMMON15 그대로)·utf-8-sig·필수 칸(corp_label·fy·source_text·doc_kind·rcept_no_or_url·page·doc_name·collected_at) 빈칸 0,
     doc_name·collected_at·fy·corp_label 이 사업보고서_원문.csv(경영공시는 risk8 경영공시_2026_2Q.csv)와 같음, collected_at KST 꼴
 (d) 키·비밀값 문자열 없음(환경변수 DART_API_KEY 값·crtfc_key=값·40자리 16진) — 조각 CSV·생성기·원문 md(g1 몫)·이 결과 txt
 (e) 회사 × FY2019~2025 마다 A·B·D 각 1행 이상
 (f) B 숫자 칸(employees_total·regular·contract) ↔ 원문 숫자: source_text 가 합계 행이면 그 칸,
     아니면 note 에 옮긴 직원 표 합계 행 원문(그 md 의 Ⅷ 표 안에 있는지 확인)의 2·4·6번째 칸
 (g) 손 대조: 회사마다 2개 FY 의 겸직 표(Ⅷ·Ⅸ, 표 앞 제목에 겸직·겸임)를 따로 읽어 모든 자료 행이 A source_text 에 있는지
 (h) 출생년월: A 의 birth_ym 이 같은 보고서 임원 현황 표(출생년월 칸) 같은 성명 행 값인지(전수) + 표본 20행 옮겨 적기,
     birth_ym 빈 행이 임원 표에 같은 성명으로 있지 않은지, 회사 안 같은 성명 다른 출생년월(동명이인 후보)
 (i) 「문서에 없음」 반박: 더 넓은 검색어·줄 넘김 무시(공백 뺀 글) 검색 — A 겸직 사유, B·D 경영공시, D 우리 FY2021~2024 Ⅹ~Ⅺ
 (j) 줄 넘김 누락 점검: 공백 뺀 글에서 B 검색어(Ⅷ)·D 검색어(Ⅹ~Ⅺ)가 어느 행 source_text 에도 덮이지 않은 곳
웹 요청 없음. 입력 파일은 읽기만 함.
"""
from __future__ import annotations

import bisect
import csv
import os
import random
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "dart_out", "ops15")
FRAG = os.path.join(WORK, "조각")
ORIG = os.path.join(WORK, "원문")
REPORT = os.path.join(WORK, "verify15_bs_g1.txt")
GEN = os.path.join(ROOT, "scripts", "dart", "ops15_bs_g1.py")
T13_ZIP = os.path.join(ROOT, "handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
MGMT_CSV = os.path.join(ROOT, "dart_out", "risk8", "경영공시_2026_2Q.csv")
COS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주"]
FYS = list(range(2019, 2026))
NONE = "문서에 없음"
KST = timezone(timedelta(hours=9))

COLS = {
    "A": ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "D": ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"],
}
REQ = ["corp_label", "fy", "source_text", "doc_kind", "rcept_no_or_url", "page", "doc_name", "collected_at"]

# 손 대조 FY(회사마다 2개) — 정정판이 있는 해·기준일 이후 표가 많은 해를 섞어 고름
HAND_FY = {"KB금융지주": [2019, 2024], "신한금융지주": [2020, 2025], "하나금융지주": [2021, 2023], "우리금융지주": [2019, 2025]}

# 이번 검증에서 고친 곳(생성기 scripts/dart/ops15_bs_g1.py 에 넣고 다시 돌림) — 아래 검사로 고친 상태를 다시 확인
FIXES = [
    "B·D 경영공시 2026.2Q 「문서에 없음」 행 4개(B 하나·우리, D KB·우리) page 빈칸 → 「p.1~p.N(경영공시 전체 — 찾은 범위)」(필수 칸 page 빈칸 0).",
    "A 겸직 사유 「문서에 없음」 반박 성공 3행: 하나금융지주 FY2021 박성호·FY2022 박성호·FY2023 이승열(겸직 하나은행) — 같은 보고서 Ⅵ 「1. 이사회에 관한 사항」"
    " 이사 현황 표 「선임 배경」 칸 「그룹 내 자산 및 이익 비중 등을 고려하여 하나은행 대표이사 은행장이 하나금융지주 비상임이사를 겸직하는 것이 …」를"
    " reason_text 로 옮김(칸 글 그대로, 위치는 note). 생성기에 Ⅷ·Ⅸ 밖 사람별 표 칸 찾기를 넣음.",
    "A note: 사람 없는 「…위해 … 겸직」 글(KB FY2019 Ⅳ 「…책임경영 강화를 위해 계열사 유관조직과 겸직체계를 활용하고 있습니다.」, 신한 FY2019~2025 Ⅳ·6. 금융지주회사법 개정 설명"
    " 「…임직원의 겸직범위를 확대한 반면 …」)은 reason_text 에 넣지 않고 그 보고서 A 행 note 「넓혀 찾음」에 문장 그대로 적음(434행). 나머지 「문서에 없음」 행 note 에"
    " 「보고서 전체의 사람별 표 칸·「위해 … 겸직」 글로 넓혀 찾아도 없음」을 덧붙임.",
    "A note: Ⅷ 겸직 표와 Ⅸ 겸직 표·작성기준일 이후 표의 같은 (사람·회사·직위) 묶음에서 글이 다른 행(선임일·병합 칸·<br> 차이)을 「같은 행」이라고만 적던 것을"
    " 그 글을 옮겨 적게 고침(「같은 사람·회사·직위 행(글 다름)이 [표 n] 에도 「…」」, 「이후 표([표 n](글 다름: 「…」))」) — 같은지 비교는 공백·「|」만 무시(&cr;·<br> 은 글자로 셈).",
    "A note: 하나금융지주 박병준 출생년월 원문이 보고서마다 다름(FY2019·2020 1965.07, FY2021~2025 1966.03) — 7행 note 에 「(판단) 동명이인 확인 … (애매)」.",
    "D 우리금융지주 FY2021~2024 「문서에 없음」 4행 note 에 넓은 낱말(위탁·수탁·용역·자문·아웃소싱·외주·대행·공동) 다시 찾기 결과와 낱말별 첫 곳·정보 처리 위탁 글을 덧붙임.",
    "모든 고침은 생성기 scripts/dart/ops15_bs_g1.py 에 넣고 다시 돌려 조각·원문 md 를 새로 씀(행 수 A 980·B 110·D 96 그대로).",
]
# (i) 반박 검색 결과를 읽고 내린 판정(사람 판단) — 검색 결과 자체는 위 표에 그대로 나옴
REFUTE_JUDGE = [
    "A reason_text: 사람별 사유 칸은 하나 FY2021~2023 이사 현황 「선임 배경」 3곳뿐 → reason_text 로 옮김(반박 성공). 나머지 맞은 곳은 금융지주회사법 개정 설명(신한)·"
    "사업부문 겸직체계 일반 글(KB FY2019)·겸직 사전승인 누락 제재(KB FY2022~2025)·겸임 표기(「글로벌부문장 겸임」+「고려대」) — 사람별 겸직 사유가 아님, 「문서에 없음」 유지.",
    "B 하나·우리 경영공시 2026.2Q: 넓은 검색어로 맞은 곳은 「예상손실충당금모델 완전적용」(전적)·충당금 전입(환입)액·손상차손전입(전입)뿐 — 직원 겸직·파견 글 아님, 「문서에 없음」 유지.",
    "D KB·우리 경영공시 2026.2Q: 같은 검색어 줄 넘김 무시 0곳. 넓은 낱말은 업무 범위 표의 「위탁매매」, 레버리지비율 「수탁자산」, 유동화 「자문」, 자회사 업무 「IT서비스업무」 — 위수탁 계약 글 아님, 「문서에 없음」 유지.",
    "D 우리 FY2021~2024 Ⅹ~Ⅺ: 같은 검색어 줄 넘김 무시 0곳. 넓은 낱말은 소송(위탁자·수탁자·공동소송)·리츠 회사 이름·투자권유자문인력·수탁고·판매대행·고객정보 처리 위탁(위탁업체 점검·보안관리 약정서) — "
    "고객정보 처리 위탁 글은 계약(약정서) 언급이나 D 검색어 꼴이 아니고 KB(FY2021~)·신한(FY2024·2025) 같은 꼴 글도 행이 아니라 같은 기준으로 「문서에 없음」 유지(판단, note 에 적음).",
]
# 참고(실패 아님) — 검증 중 본 것으로 메인이 합칠 때 판단할 것
REMARKS = [
    "B 숫자 칸(employees_total·regular·contract)은 키워드 행에도 채워져 있으나 그 행 source_text 는 키워드 문단이라 숫자가 없음 — 숫자 원문은 note 「[표 n] 합계 행 「…」」"
    "(md Ⅷ 그 표 안에 있음 확인, 2·4·6번째 칸 = regular·contract·employees_total). g2·g3 조각도 같은 꼴이라 g1 만 바꾸지 않음.",
    "D 는 같은 보고서의 같은 (상대방·유형)을 1행으로 묶고 나머지 위치만 note 「같은 상대방·유형 언급 글 N개 더: …」에 적음 — 글이 다른데 묶인 곳 43(하나 FY2019~2023"
    " 하나대체투자자산운용 제재 표의 사람별 행, KB FY2021~2025 업무위탁수수료 미공시 제재의 사람별 행, 신한 FY2023~2025 리츠 업무위탁계약서 제재 행 등). 그 글은 원문 md 에 있음.",
    "작업 범위(A=Ⅷ·Ⅸ, B=Ⅷ, D=Ⅹ~Ⅺ) 밖이라 행으로 넣지 않은 겸직 관련 글: 신한 FY2025 Ⅺ 「3. 제재 등과 관련된 사항」 「… 당사의 직원은 업무상 사유로 다른 회사의 임원을 겸직하였음에도 …」"
    "(기업결합신고 누락 제재), KB FY2022~2025 Ⅺ 제재 「임원 겸직 사전승인 절차 누락」「임직원 겸직에 대한 금융위원회 사전승인 및 보고 누락」.",
    "D 검색어 밖 고객·개인(신용)정보 처리 위탁 글(위탁업체 점검·「개인(신용)정보 위탁(제공) 보안관리 약정서」): 우리 FY2019~2025, KB FY2021~2025, 신한 FY2024·2025 Ⅺ — 행 아님(넣으려면 D 검색어 확장).",
]

out_lines = []
problems = []
notes = []


def say(s=""):
    out_lines.append(s)


def prob(sec, s):
    problems.append("[%s] %s" % (sec, s))


def nzv(s):
    """(a) 규칙 — 공백·줄바꿈·「|」만 무시."""
    return re.sub(r"[\s|]", "", s or "")


def nzp(s):
    """PDF 대조용 — md 표지(&cr;·<br>)도 뺌."""
    return re.sub(r"[\s|]|&cr;|<br>", "", s or "")


def cells(line):
    t = line.strip()
    if not (t.startswith("|") and t.endswith("|")):
        return None
    return [c.strip() for c in t[1:-1].split("|")]


def namek(s):
    return re.sub(r"\(?주\d+\)|[*※]", "", nzv(s).replace("&cr;", "").replace("<br>", ""))


# ---------------------------------------------------------------- 원문
class MD:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            self.L = f.read().split("\n")
        self.heads, self.allheads, self.tables = [], [], {}
        self.tab_of = [None] * len(self.L)
        cur = None
        for i, l in enumerate(self.L):
            if cur is None:
                m = re.match(r"### \[절 (\d+)\] ?(.*)$", l)
                if m:
                    t = m.group(2).strip()
                    self.allheads.append((i, int(m.group(1)), t))
                    if t:
                        self.heads.append((i, int(m.group(1)), t))
                    continue
                m = re.fullmatch(r"\[표 (\d+)\]", l)
                if m:
                    cur, s = int(m.group(1)), i
                continue
            if l == "[표 끝]":
                self.tables[cur] = (s, i)
                cur = None
                continue
            self.tab_of[i] = cur
        self.hidx = [h[0] for h in self.heads]
        self.off, parts, o = [], [], 0
        for l in self.L:
            self.off.append(o)
            t = nzv(l)
            parts.append(t)
            o += len(t)
        self.off.append(o)
        self.buf = "".join(parts)

    def line_at(self, pos):
        return bisect.bisect_right(self.off, pos) - 1

    def head_at(self, i):
        k = bisect.bisect_right(self.hidx, i) - 1
        return self.heads[k] if k >= 0 else None

    def occ(self, needle):
        out, p = [], self.buf.find(needle)
        while p >= 0 and needle:
            out.append((p, p + len(needle)))
            p = self.buf.find(needle, p + 1)
        return out

    def chapter(self, roman):
        hs = self.heads
        for k, h in enumerate(hs):
            if re.match(r"^%s\.\s" % roman, h[2]):
                for j in range(k + 1, len(hs)):
                    if re.match(r"^(?:[IVX]+)\.\s", hs[j][2]):
                        return h[0], hs[j][0]
                return h[0], len(self.L)
        return None


class PDFT:
    """13차 텍스트(「## p.N」 쪽) — 쪽 머리 줄은 글에서 뺌."""

    def __init__(self, text):
        self.pg_of_line, self.lines, pg = [], [], 0
        self.npages = 0
        for l in text.split("\n"):
            m = re.match(r"## p\.(\d+)\s*$", l)
            if m:
                pg = int(m.group(1))
                self.npages = max(self.npages, pg)
                continue
            self.lines.append(l)
            self.pg_of_line.append(pg)
        self.off, parts, o = [], [], 0
        for l in self.lines:
            self.off.append(o)
            t = nzv(l)
            parts.append(t)
            o += len(t)
        self.off.append(o)
        self.buf = "".join(parts)

    def page_at(self, pos):
        return self.pg_of_line[bisect.bisect_right(self.off, pos) - 1]

    def occ(self, needle):
        out, p = [], self.buf.find(needle)
        while p >= 0 and needle:
            out.append((p, p + len(needle)))
            p = self.buf.find(needle, p + 1)
        return out


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def kst_iso(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d.astimezone(KST).isoformat()


def main():
    now = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    _, reps = read_csv(os.path.join(WORK, "사업보고서_원문.csv"))
    rep = {r["rcept_no"]: r for r in reps if r["label"] in COS}
    _, mrows = read_csv(MGMT_CSV)
    mg = {r["corp_label"]: r for r in mrows if r["corp_label"] in COS and r["성공"] == "Y"}
    z = zipfile.ZipFile(T13_ZIP)
    t13 = {}
    for n in z.namelist():
        m = re.search(r"텍스트/(사업보고서|경영공시)__(.+)\.md$", n)
        if m and m.group(2) in COS:
            t13[(m.group(1), m.group(2))] = PDFT(z.read(n).decode("utf-8"))
    mds = {}

    def md(rc):
        if rc not in mds:
            mds[rc] = MD(os.path.join(ROOT, rep[rc]["text_path"]))
        return mds[rc]

    data = {}
    say("# 15차 g1 사업보고서 조각 검증 (verify15_bs_g1.py)")
    say("실행: %s KST · 웹 요청 없음 · 입력은 읽기만" % now)
    say("")

    # ------------------------------------------------ (c) 열·인코딩·필수 칸
    say("## (c) 열 이름·utf-8-sig·필수 칸·출처 칸 일치")
    for t in "ABD":
        p = os.path.join(FRAG, "%s_bs_g1.csv" % t)
        with open(p, "rb") as f:
            bom = f.read(3) == b"\xef\xbb\xbf"
        hdr, rows = read_csv(p)
        data[t] = rows
        if not bom:
            prob("c", "%s utf-8-sig BOM 없음" % t)
        if hdr != COLS[t]:
            prob("c", "%s 열 이름 다름: %s" % (t, hdr))
        empty = 0
        mism = 0
        for k, r in enumerate(rows, 2):
            for c in REQ:
                if not (r.get(c) or "").strip():
                    empty += 1
                    prob("c", "%s %d행 %s 빈칸 (%s %s)" % (t, k, c, r["corp_label"], r["fy"]))
            if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00", r["collected_at"]):
                prob("c", "%s %d행 collected_at 꼴 %r" % (t, k, r["collected_at"]))
            if r["doc_kind"] == "사업보고서":
                m = rep.get(r["rcept_no_or_url"])
                if not m:
                    prob("c", "%s %d행 rcept %s 사업보고서_원문.csv 에 없음" % (t, k, r["rcept_no_or_url"]))
                    continue
                exp = dict(corp_label=m["label"], fy=m["fy"], doc_name=m["report_nm"], collected_at=m["fetched_at"])
            elif r["doc_kind"] == "경영공시":
                m = mg[r["corp_label"]]
                exp = dict(corp_label=r["corp_label"], fy="2026.2Q", doc_name=m["제목"], collected_at=kst_iso(m["fetched_at"]),
                           rcept_no_or_url=m["실제url"] or m["url"])
            else:
                prob("c", "%s %d행 doc_kind 모름 %r" % (t, k, r["doc_kind"]))
                continue
            for c, v in exp.items():
                if r[c] != v:
                    mism += 1
                    prob("c", "%s %d행 %s=%r ≠ 출처 목록 %r" % (t, k, c, r[c], v))
        say("- %s: %d행 · BOM %s · 열 %s · 필수 칸 빈칸 %d · 출처 목록과 다른 칸 %d"
            % (t, len(rows), "있음" if bom else "없음", "같음" if hdr == COLS[t] else "다름", empty, mism))
    say("")

    # ------------------------------------------------ (a)(b) 원문·위치
    say("## (a) source_text·reason_text ↔ 원문 글자 그대로(공백·줄바꿈·「|」 무시) · (b) page ↔ 실제 위치")
    spans = {}            # (task, rcept) -> [(s,e)] 행 글이 덮는 곳(정규화 위치)
    stat = {}
    pdf_weak = []
    for t in "ABD":
        st = stat.setdefault(t, dict(rows=0, none=0, a_ok=0, b_ok=0, pdf_ok=0, pdf_weak=0, mg_ok=0))
        for k, r in enumerate(data[t], 2):
            st["rows"] += 1
            src = r["source_text"]
            tag = "%s %d행(%s %s)" % (t, k, r["corp_label"], r["fy"])
            if t == "A" and r["reason_text"] != NONE:
                st["reason"] = st.get("reason", 0) + 1
                d0 = md(r["rcept_no_or_url"])
                oc0 = d0.occ(nzv(r["reason_text"]))
                if not oc0:
                    prob("a", "%s reason_text 원문에 없음" % tag)
                mm = re.search(r"reason_text: 같은 보고서 XML \[절 (\d+)\] 「(.*?)」 \[표 (\d+)\]", r["note"])
                if not mm:
                    prob("b", "%s reason_text 위치가 note 에 없음" % tag)
                elif not any((d0.head_at(d0.line_at(a0)) or (0, 0, ""))[1:] == (int(mm.group(1)), mm.group(2))
                             and d0.tab_of[d0.line_at(a0)] == int(mm.group(3)) for a0, _ in oc0):
                    prob("b", "%s reason_text 위치(note) ≠ 실제 위치" % tag)
                else:
                    st["reason_ok"] = st.get("reason_ok", 0) + 1
            if t == "A" and "넓혀 찾음:" in r["note"]:
                mm = re.search(r"넓혀 찾음: XML \[절 (\d+)\] 「(.*?)」 글 「(.*?)」이 있으나", r["note"])
                d0 = md(r["rcept_no_or_url"])
                if not mm or not any((d0.head_at(d0.line_at(a0)) or (0, 0, ""))[1:] == (int(mm.group(1)), mm.group(2))
                                     for a0, _ in d0.occ(nzv(mm.group(3)))):
                    prob("a", "%s note 「넓혀 찾음」 인용이 원문 그 절에 없음" % tag)
                else:
                    st["wide_ok"] = st.get("wide_ok", 0) + 1
            if t == "A" and r["reason_text"] == NONE and "겸직 사유" not in r["note"]:
                prob("c", "%s reason_text 「문서에 없음」인데 note 에 찾은 범위(겸직 사유 글) 없음" % tag)
            page = r["page"]
            if src == NONE:
                st["none"] += 1
                if "찾은 범위" not in r["note"]:
                    prob("c", "%s 「문서에 없음」 행 note 에 「찾은 범위」 없음" % tag)
                if t == "D" and "넓은 낱말" not in r["note"] and r["doc_kind"] == "사업보고서":
                    prob("c", "%s D 「문서에 없음」 행 note 에 넓은 낱말 다시 찾기 결과 없음" % tag)
                if r["doc_kind"] == "사업보고서":
                    d = md(r["rcept_no_or_url"])
                    secs = re.findall(r"\[절 (\d+)\] 「(.*?)」", page)
                    hs = {(h[1], h[2]) for h in d.heads}
                    if not secs or any((int(n), ti) not in hs for n, ti in secs):
                        prob("b", "%s 「문서에 없음」 page 절 %r 이 md 제목과 다름" % (tag, page))
                    else:
                        st["b_ok"] += 1
                else:
                    pdf = t13[("경영공시", r["corp_label"])]
                    m = re.fullmatch(r"p\.1~p\.(\d+)\(경영공시 전체 — 찾은 범위\)", page)
                    if not m or int(m.group(1)) != pdf.npages:
                        prob("b", "%s 「문서에 없음」 page %r ≠ 찾은 범위 p.1~p.%d" % (tag, page, pdf.npages))
                    else:
                        st["b_ok"] += 1
                continue
            needle = nzv(src)
            if r["doc_kind"] == "경영공시":
                pdf = t13[("경영공시", r["corp_label"])]
                oc = pdf.occ(needle)
                if not oc:
                    prob("a", "%s 경영공시 source_text 원문에 없음: %r" % (tag, src[:80]))
                    continue
                st["a_ok"] += 1
                pg = [int(x) for x in re.findall(r"p\.(\d+)", page)]
                okp = any(pdf.page_at(s) == pg[0] and {pdf.page_at(x) for x in (s, e - 1)} <= set(pg) for s, e in oc) if pg else False
                if okp:
                    st["b_ok"] += 1
                    st["mg_ok"] += 1
                else:
                    prob("b", "%s 경영공시 page %r ≠ 실제 쪽 %s" % (tag, page, sorted({pdf.page_at(s) for s, _ in oc})))
                continue
            d = md(r["rcept_no_or_url"])
            oc = d.occ(needle)
            if not oc:
                prob("a", "%s source_text 원문 md 에 없음: %r" % (tag, src[:80]))
                continue
            st["a_ok"] += 1
            m = re.fullmatch(r"XML \[절 (\d+)\] 「(.*?)」(?: \[표 (\d+)\])?(?:; p\.(\d+)\(본문 PDF, 13차 보관\))?", page)
            if not m:
                prob("b", "%s page 꼴 모름 %r" % (tag, page))
                continue
            sn, sti, tb, pp = int(m.group(1)), m.group(2), m.group(3), m.group(4)
            good = []
            for s, e in oc:
                ls, le = d.line_at(s), d.line_at(e - 1)
                h = d.head_at(ls)
                if not h or (h[1], h[2]) != (sn, sti):
                    continue
                if tb is not None and not (d.tab_of[ls] == int(tb) and d.tab_of[le] == int(tb)):
                    continue
                if tb is None and d.tab_of[ls] is not None:
                    continue
                good.append((s, e))
            if good:
                st["b_ok"] += 1
                spans.setdefault((t, r["rcept_no_or_url"]), []).extend(good)
            else:
                where = []
                for s, e in oc[:3]:
                    ls = d.line_at(s)
                    h = d.head_at(ls)
                    where.append("[절 %s] [표 %s]" % (h[1] if h else "-", d.tab_of[ls]))
                prob("b", "%s page %r 와 실제 위치 다름 — 실제 %s" % (tag, page, ", ".join(where)))
            fy = int(r["fy"]) if r["fy"].isdigit() else 0
            is_bon = rep[r["rcept_no_or_url"]]["kind"] == "본"
            if fy == 2025 and is_bon and pp is None:
                prob("b", "%s FY2025 본 행인데 13차 본문 PDF 쪽 없음" % tag)
            if pp is not None:
                pdf = t13[("사업보고서", r["corp_label"])]
                pn = int(pp)
                full = nzp(src)
                ok = weak = False
                for L in (40, 20, 12):
                    nd = full[:L]
                    pos = pdf.occ(nd)
                    if not pos:
                        continue
                    pages = sorted({pdf.page_at(s) for s, _ in pos})
                    if pn in pages:
                        ok = True
                        weak = L < 40 and len(full) > L
                    else:
                        prob("b", "%s 본문 PDF p.%d 인데 앞 %d자는 %s쪽에 있음" % (tag, pn, L, pages[:6]))
                    break
                else:
                    prob("b", "%s 본문 PDF 텍스트에서 앞 12자도 못 찾음" % tag)
                if ok:
                    st["pdf_ok"] += 1
                    if weak:
                        st["pdf_weak"] += 1
                        pdf_weak.append("%s p.%d — 앞 40자는 PDF 에 없음(표 칸 차례 등) · 더 짧은 앞부분으로 확인" % (tag, pn))
        say("- %s: %d행 · 「문서에 없음」 %d · (a) 원문에 있음 %d/%d · (b) page 맞음 %d/%d · 13차 본문 PDF 쪽 맞음 %d(짧은 앞부분으로 맞춘 것 %d) · 경영공시 쪽 맞음 %d"
            % (t, st["rows"], st["none"], st["a_ok"], st["rows"] - st["none"], st["b_ok"], st["rows"],
               st["pdf_ok"], st["pdf_weak"], st["mg_ok"]))
        if t == "A":
            say("  · A reason_text 가 「문서에 없음」이 아닌 행 %d — 원문 글자 그대로·note 위치(절·표) 맞음 %d · note 「넓혀 찾음」 인용(Ⅷ·Ⅸ 밖 사람 없는 글)이 원문 그 절에 있음 %d행"
                % (st.get("reason", 0), st.get("reason_ok", 0), st.get("wide_ok", 0)))
    for x in pdf_weak[:12]:
        say("  · 참고: " + x)
    if len(pdf_weak) > 12:
        say("  · 참고: … 그 밖 %d행" % (len(pdf_weak) - 12))
    say("")

    # ------------------------------------------------ (e) 회사×FY
    say("## (e) 회사 × FY2019~2025 마다 A·B·D 각 1행 이상")
    for co in COS:
        cnt = []
        for fy in FYS:
            c = [sum(1 for r in data[t] if r["corp_label"] == co and r["fy"] == str(fy)) for t in "ABD"]
            cnt.append("%d:%d/%d/%d" % (fy % 100, c[0], c[1], c[2]))
            for t, n in zip("ABD", c):
                if n == 0:
                    prob("e", "%s FY%d %s 행 0" % (co, fy, t))
        say("- %s (FY:A/B/D) %s" % (co, " ".join(cnt)))
    say("")

    # ------------------------------------------------ (f) B 숫자
    say("## (f) B 숫자 칸 ↔ 원문 숫자")
    fin = fnote = fbad = fblank = 0
    for k, r in enumerate(data["B"], 2):
        tag = "B %d행(%s %s)" % (k, r["corp_label"], r["fy"])
        nums = [r["employees_total"], r["regular"], r["contract"]]
        if not any(x.strip() for x in nums):
            fblank += 1
            if r["doc_kind"] == "사업보고서":
                prob("f", "%s 사업보고서 행인데 숫자 칸 빈칸" % tag)
            continue
        c = cells(r["source_text"]) if "\n" not in r["source_text"] else None
        if c and len(c) > 5 and nzv(c[0]) in ("합계", "총계"):
            if [c[5], c[1], c[3]] == nums:
                fin += 1
            else:
                fbad += 1
                prob("f", "%s 숫자 %s ≠ source_text 합계 행 칸 %s" % (tag, nums, [c[5], c[1], c[3]]))
            continue
        m = re.search(r"\[표 (\d+)\] 합계 행 「(\|.*?\|)」", r["note"])
        if not m:
            fbad += 1
            prob("f", "%s 숫자 칸이 있는데 source_text·note 어디에도 합계 행 원문 없음" % tag)
            continue
        d = md(r["rcept_no_or_url"])
        q, tb = m.group(2), int(m.group(1))
        ok_pos = [s for s, e in d.occ(nzv(q)) if d.tab_of[d.line_at(s)] == tb]
        ch = d.chapter("VIII")
        if not ok_pos or not (ch and ch[0] <= d.line_at(ok_pos[0]) < ch[1]):
            fbad += 1
            prob("f", "%s note 합계 행이 md [표 %d](Ⅷ) 안에 없음" % (tag, tb))
            continue
        qc = cells(q)
        if [qc[5], qc[1], qc[3]] != nums:
            fbad += 1
            prob("f", "%s 숫자 %s ≠ 합계 행 칸 %s" % (tag, nums, [qc[5], qc[1], qc[3]]))
            continue
        fnote += 1
    say("- 숫자 칸 있는 행: source_text 가 합계 행이고 칸이 같음 %d · source_text 는 키워드 글이고 note 에 옮긴 합계 행(md Ⅷ 그 표 안에 있음 확인) 칸과 같음 %d · 다름 %d · 숫자 칸 빈 행 %d(경영공시)"
        % (fin, fnote, fbad, fblank))
    say("- 참고: 키워드 행의 source_text 는 키워드 문단이라 숫자가 그 안에 없음. 숫자의 원문은 note 의 「[표 n] 합계 행 「…」」(g2·g3 조각도 같은 꼴). 위 대조는 그 합계 행 원문으로 함.")
    say("")

    # ------------------------------------------------ (g) 손 대조
    say("## (g) 겸직 표 손 대조 — 회사마다 2개 FY, 겸직 표(Ⅷ·Ⅸ) 모든 자료 행 ↔ A")
    say("- 덮였다고 보는 경우: ① 그 줄 글이 A source_text 이고 그 A 행 page 또는 note(「같은 행이 [표 n]」·「이후 표([표 n])에도 같은 행」)에 그 표 번호가 있음,"
        " ② 사람·회사·직위가 같아 묶인 행 — A note 에 「[표 n] … 「그 줄 글」」로 옮겨 있음")
    HDR_CELLS = {"성명", "겸직자", "겸직회사", "겸직회사명", "대상회사", "대상계열사", "회사명", "직책", "직위", "직위명", "선임시기",
                 "선임일", "겸임일자", "비고", "상근여부", "상근/비상근여부", "상근/비상근", "재임기간", "겸직현황", "겸임현황", "회사",
                 "겸직내용", "직무", "지분보유현황", "겸직회사의주된사업목적"}
    QRE = re.compile(r"\[표 (\d+)\](?:\(XML [^)]*\))? ?(?:\(글 다름: )?「(\|[^」]*\|)」")
    hand_sum = []
    for co in COS:
        for fy in HAND_FY[co]:
            rc = next(x for x, m in rep.items() if m["label"] == co and m["fy"] == str(fy) and m["kind"] == "본")
            d = md(rc)
            arows = [r for r in data["A"] if r["rcept_no_or_url"] == rc]
            same_tab, quoted, a_tabs = set(), set(), {}
            for r in arows:
                pt = int(re.search(r"\[표 (\d+)\]", r["page"]).group(1))
                a_tabs[pt] = a_tabs.get(pt, 0) + 1
                tabs = {pt} | {int(x) for x in re.findall(r"\[표 (\d+)\]", re.sub(r"「\|[^」]*\|」", "", r["note"]))}
                for tno in tabs:
                    same_tab.add((tno, nzv(r["source_text"])))
                for tno, q in QRE.findall(r["note"]):
                    quoted.add((int(tno), nzv(q)))
            spans8 = [d.chapter("VIII"), d.chapter("IX")]
            found_tabs, hdrs, tot, hit, via_q = [], set(), 0, 0, 0
            for no, (s, e) in sorted(d.tables.items(), key=lambda x: x[1][0]):
                if not any(sp and sp[0] <= s < sp[1] for sp in spans8):
                    continue
                rows = [(i, cells(d.L[i])) for i in range(s + 1, e) if cells(d.L[i]) is not None]
                if len(rows) <= 1:
                    continue
                cap, i = [], s - 1
                while i >= 0 and len(cap) < 8:
                    l = d.L[i]
                    if l.startswith("### "):
                        break
                    if l == "[표 끝]":
                        ps = [x for x in d.tables.values() if x[1] == i]
                        if ps and sum(1 for j in range(ps[0][0] + 1, i) if cells(d.L[j]) is not None) <= 1:
                            i = ps[0][0] - 1
                            continue
                        break
                    if l.strip():
                        cap.append(l)
                    i -= 1
                capt = nzv(" ".join(reversed(cap)))
                hdr = nzv(" ".join(rows[0][1])).replace("&cr;", "").replace("<br>", "")
                if "출생" in hdr or "직원" in hdr[:6] or not re.search(r"성명|겸직자|이름", hdr) or not re.search(r"회사|계열사", hdr):
                    continue
                if not (re.search(r"겸직|겸임", capt + hdr) or hdr in hdrs):
                    continue
                hdrs.add(hdr)
                drows = [(i, c) for i, c in rows if not any(nzv(x).replace("&cr;", "").replace("<br>", "") in HDR_CELLS for x in c)]
                miss, nq = [], 0
                for i, c in drows:
                    key = (no, nzv(d.L[i]))
                    if key in same_tab:
                        continue
                    if key in quoted:
                        nq += 1
                        continue
                    miss.append(d.L[i])
                found_tabs.append(no)
                tot += len(drows)
                hit += len(drows) - len(miss)
                via_q += nq
                say("- %s FY%d [표 %d] 「%s」 자료 행 %d · A 에 있음 %d(그 가운데 묶인 행 note 인용 %d)"
                    % (co, fy, no, capt[-36:], len(drows), len(drows) - len(miss), nq))
                for x in miss:
                    if re.fullmatch(r"(-|해당사항없음|해당없음|없음)+", nzv(x)):
                        say("    · 사람 행 아님(A 에 넣지 않는 것이 맞음): %s" % x[:100])
                    else:
                        prob("g", "%s FY%d [표 %d] 자료 행이 A 에 없음: %s" % (co, fy, no, x[:120]))
            other = {k: v for k, v in a_tabs.items() if k not in found_tabs}
            say("  = %s FY%d 겸직 표 %d개 자료 행 %d 중 A 에 있음 %d(묶인 행 note 인용 %d) · 겸직 표 밖 A 행(임원 현황 칸에서 찾은 행) 표별 %s"
                % (co, fy, len(found_tabs), tot, hit, via_q, other or "없음"))
            hand_sum.append("%s FY%d %d/%d" % (co, fy, hit, tot))
            for k in other:
                hdr0 = next((cells(d.L[i]) for i in range(d.tables[k][0] + 1, d.tables[k][1]) if cells(d.L[i])), [])
                if "출생년월" not in [nzv(x).replace("&cr;", "").replace("<br>", "") for x in hdr0]:
                    prob("g", "%s FY%d A 행이 겸직 표도 임원 현황 표도 아닌 [표 %d]에서 나옴" % (co, fy, k))
    say("- 손 대조 요약(덮인 행/자료 행): " + " · ".join(hand_sum))
    say("")

    # ------------------------------------------------ (h) 출생년월
    say("## (h) 출생년월 — 임원 현황 표(출생년월 칸) 같은 성명 행과 맞춤")
    offi = {}

    def officers(rc):
        if rc not in offi:
            d = md(rc)
            res = []
            for no, (s, e) in d.tables.items():
                hdr = None
                for i in range(s + 1, e):
                    c = cells(d.L[i])
                    if c is None:
                        continue
                    if hdr is None:
                        hdr = [nzv(x).replace("&cr;", "").replace("<br>", "") for x in c]
                        if "출생년월" not in hdr:
                            break
                        continue
                    res.append((no, i, [namek(x) for x in c], [nzv(x) for x in c]))
            offi[rc] = res
        return offi[rc]

    hb_ok, hb_bad, blank_in = 0, 0, []
    for k, r in enumerate(data["A"], 2):
        offs = officers(r["rcept_no_or_url"])
        pk = namek(r["person"])
        if r["birth_ym"]:
            if any(pk in nm and nzv(r["birth_ym"]) in raw for _, _, nm, raw in offs):
                hb_ok += 1
            else:
                hb_bad += 1
                prob("h", "A %d행(%s %s %s) birth_ym %s 가 임원 현황 표 같은 성명 행에 없음" % (k, r["corp_label"], r["fy"], r["person"], r["birth_ym"]))
        else:
            if pk and any(pk in nm for _, _, nm, _ in offs):
                blank_in.append("A %d행 %s %s %s" % (k, r["corp_label"], r["fy"], r["person"]))
    say("- birth_ym 있는 행 %d: 임원 표 같은 성명·같은 출생년월 행 있음 %d · 없음 %d" % (hb_ok + hb_bad, hb_ok, hb_bad))
    say("- birth_ym 빈 행 %d 중 같은 보고서 임원 현황 표에 같은 성명이 있는 행 %d%s"
        % (sum(1 for r in data["A"] if not r["birth_ym"]), len(blank_in), (" — " + "; ".join(blank_in[:10])) if blank_in else ""))
    for x in blank_in:
        prob("h", "birth_ym 빈칸인데 임원 표에 같은 성명: " + x)
    same = {}
    for r in data["A"]:
        if r["birth_ym"]:
            same.setdefault((r["corp_label"], namek(r["person"])), set()).add(r["birth_ym"])
    dup = {k: v for k, v in same.items() if len(v) > 1}
    say("- 회사 안 같은 성명·다른 출생년월 원문: %d명%s" % (len(dup), (" — " + "; ".join("%s %s %s" % (k[0], k[1], sorted(v)) for k, v in dup.items())) if dup else ""))
    for (co, pk), v in dup.items():
        rows = [r for r in data["A"] if r["corp_label"] == co and namek(r["person"]) == pk and r["birth_ym"]]
        if len({x.rstrip(".") for x in v}) == 1:
            say("    · %s %s: 끝 점만 다른 표기(%s) — 같은 값으로 봄, note 표시 없음" % (co, pk, " / ".join(sorted(v))))
            continue
        nn = sum(1 for r in rows if "동명이인" in r["note"])
        say("    · %s %s: 출생년월 %s — 행 %d 중 note 에 「동명이인 확인 … (애매)」 %d" % (co, pk, " / ".join(sorted(v)), len(rows), nn))
        if nn != len(rows):
            prob("h", "동명이인 후보 %s %s %s — note 표시 없는 행 %d" % (co, pk, sorted(v), len(rows) - nn))
    # 다른 회사 사이 같은 성명(자회사 임원 겸직이 서로 다른 지주에 나올 일은 없음 — 참고)
    rnd = random.Random(1520)
    say("- 표본 20행(회사마다 5행, 난수 씨앗 1520) — A 행 ↔ 임원 현황 표 행(앞 110자):")
    for co in COS:
        pool = [(k, r) for k, r in enumerate(data["A"], 2) if r["corp_label"] == co and r["birth_ym"]]
        for k, r in rnd.sample(pool, 5):
            pk = namek(r["person"])
            hitl = next(((no, i) for no, i, nm, raw in officers(r["rcept_no_or_url"]) if pk in nm and nzv(r["birth_ym"]) in raw), None)
            d = md(r["rcept_no_or_url"])
            say("    · A %d행 %s FY%s %s %s → %s" % (k, co, r["fy"], r["person"], r["birth_ym"],
                                                 ("[표 %d] %s" % (hitl[0], d.L[hitl[1]][:110])) if hitl else "못 찾음"))
    say("")

    # ------------------------------------------------ (i) 「문서에 없음」 반박
    say("## (i) 「문서에 없음」 반박 — 더 넓은 검색어, 공백·줄 넘김 뺀 글에서 검색")

    def ctx(buf, s, e, w=30):
        return buf[max(0, s - w):e + w]

    # A 겸직 사유 — Ⅷ·Ⅸ 그리고 보고서 전체(공백 뺀 글)
    RS = re.compile(r"겸(?:직|임|무)[^|\[]{0,40}?(?:사유|목적|이유|배경|필요성|취지|승인|고려|위하여|위해|위한|가능할것으로)"
                    r"|(?:사유|목적|이유|배경|필요성|취지|고려하여|위하여|위해)[^|\[]{0,30}?겸(?:직|임|무)")
    BOIL = re.compile(r"겸직하고있지않|겸직제한|겸직현황선임배경|겸직회사의&cr;주된사업목적|겸직회사의주된사업목적")
    a_rows_reason = [r for r in data["A"] if r["reason_text"] != NONE]
    tot_hits, boil = [], 0
    for rc, m in sorted(rep.items()):
        if m["kind"] != "본":
            continue
        d = md(rc)
        r8, r9 = d.chapter("VIII"), d.chapter("IX")
        for mm in RS.finditer(d.buf):
            c = ctx(d.buf, mm.start(), mm.end())
            if BOIL.search(d.buf[max(0, mm.start() - 12):mm.end() + 12]):
                boil += 1
                continue
            ln = d.line_at(mm.start())
            h = d.head_at(ln)
            inr = any(x and x[0] <= ln < x[1] for x in (r8, r9))
            tot_hits.append((m["label"], m["fy"], ln, "Ⅷ·Ⅸ" if inr else "Ⅷ·Ⅸ 밖 「%s」" % (h[2] if h else "-"), c))
    say("- A reason_text: 28개 본 보고서 전체(공백 뺀 글)에서 「겸직·겸임·겸무」 앞뒤 40자 안 사유·목적·이유·배경·필요성·취지·승인·고려·위하여·위해 — %d곳"
        " (그 밖 표 머리 「겸직현황|선임배경」「겸직회사의 주된 사업목적」·「대표이사를 겸직하고 있지 않습니다」·「겸직제한」 %d곳은 뺌)" % (len(tot_hits), boil))
    for co, fy, ln, where, c in tot_hits[:40]:
        say("    · %s FY%s md %d행 %s: …%s…" % (co, fy, ln + 1, where, c))
    say("  → 이번 보정 뒤 reason_text 가 채워진 A 행 %d: %s" % (len(a_rows_reason), "; ".join(
        "%s FY%s %s(%s)" % (r["corp_label"], r["fy"], r["person"], r["concurrent_company"]) for r in a_rows_reason)))
    # B·D 경영공시
    BW = re.compile(r"겸직|겸임|겸무|兼|파견|출향|전출|전적|전입|원소속|인사교류|인력교류|인적교류|교류근무")
    for co in ("하나금융지주", "우리금융지주"):
        p = t13[("경영공시", co)]
        hs, noise = [], 0
        for mm in BW.finditer(p.buf):
            c = ctx(p.buf, mm.start(), mm.end(), 25)
            if mm.group(0) == "전입" and re.search(r"충당금전입|전입액", p.buf[max(0, mm.start() - 3):mm.end() + 1]):
                noise += 1                       # 「제충당금전입액」(손익 표 항목)
                continue
            hs.append((p.page_at(mm.start()), mm.group(0), c))
        bc = {}
        for _, w, _c in hs:
            bc[w] = bc.get(w, 0) + 1
        say("- B %s 경영공시 2026.2Q(%d쪽) 넓은 검색어(겸직·겸임·겸무·兼·파견·출향·전출·전적·전입·원소속·인사/인력/인적교류·교류근무, 줄 넘김 무시): "
            "%d곳 %s (그 밖 「제충당금전입액」 손익 표 항목 %d곳은 뺌)" % (co, p.npages, len(hs), bc or "", noise))
        for pg, w, c in hs[:12]:
            say("    · p.%d 「%s」 …%s…" % (pg, w, c))
    DW = re.compile(r"위탁|수탁|용역|자문|공동(?:사용|이용|활용|운영|구매|개발|이용)|전산|아웃소싱|대행|IT서비스|정보기술|SLA|서비스수수료|업무지원")
    D_NZ = re.compile(r"업무위?[·ㆍ]?수탁|위[·ㆍ]수탁|위수탁|업무위탁|업무수탁|위탁계약|수탁계약|용역(?:계약|거래|비|료|대가|제공|수수료)|용역을제공|상품용역"
                      r"|경영자문|자문(?:계약|용역|료|수수료|서비스)|공동(?:사용|이용|활용)|시스템공동|전산공동|IT공동")
    for co in ("KB금융지주", "우리금융지주"):
        p = t13[("경영공시", co)]
        strict = [(p.page_at(mm.start()), mm.group(0), ctx(p.buf, mm.start(), mm.end(), 25)) for mm in D_NZ.finditer(p.buf)]
        broad = [(p.page_at(mm.start()), mm.group(0)) for mm in DW.finditer(p.buf)]
        bc = {}
        for pg, w in broad:
            bc[w] = bc.get(w, 0) + 1
        say("- D %s 경영공시 2026.2Q(%d쪽): 같은 검색어를 줄 넘김 무시로 %d곳 · 넓은 낱말(위탁·수탁·용역·자문·공동○○·전산·아웃소싱·대행 등) %s"
            % (co, p.npages, len(strict), dict(sorted(bc.items(), key=lambda x: -x[1]))))
        for pg, w, c in strict[:10]:
            say("    · 같은 검색어 p.%d 「%s」 …%s…" % (pg, w, c))
        seen = set()
        for mm in DW.finditer(p.buf):
            w = mm.group(0)
            if w in seen:
                continue
            seen.add(w)
            say("    · 넓은 낱말 첫 곳 p.%d 「%s」 …%s…" % (p.page_at(mm.start()), w, ctx(p.buf, mm.start(), mm.end(), 25)))
    for fy in (2021, 2022, 2023, 2024):
        rc = next(x for x, m in rep.items() if m["label"] == "우리금융지주" and m["fy"] == str(fy) and m["kind"] == "본")
        d = md(rc)
        x, xi = d.chapter("X"), d.chapter("XI")
        s, e = x[0], (xi[1] if xi else x[1])
        bs, be = d.off[s], d.off[e]
        strict = [ctx(d.buf, mm.start(), mm.end()) for mm in D_NZ.finditer(d.buf, bs, be)]
        bc = {}
        firsts = {}
        for mm in DW.finditer(d.buf, bs, be):
            bc[mm.group(0)] = bc.get(mm.group(0), 0) + 1
            firsts.setdefault(mm.group(0), (d.line_at(mm.start()) + 1, ctx(d.buf, mm.start(), mm.end(), 25)))
        say("- D 우리금융지주 FY%d Ⅹ~Ⅺ(md %d~%d행): 같은 검색어 줄 넘김 무시 %d곳 · 넓은 낱말 %s" % (fy, s + 1, e, len(strict), bc or "0"))
        for c in strict[:5]:
            say("    · 같은 검색어 …%s…" % c)
        for w, (ln, c) in firsts.items():
            say("    · 넓은 낱말 「%s」 첫 곳 md %d행 …%s…" % (w, ln, c))
    for x in REFUTE_JUDGE:
        say("- 판정: " + x)
    say("")

    # ------------------------------------------------ (j) 줄 넘김 누락
    say("## (j) 줄 넘김 누락 점검 — 공백 뺀 글의 검색어가 어느 행 글에도 덮이지 않은 곳(본 보고서)")
    BK = re.compile(r"겸직|파견|출향|전출|겸무|전적(?!으로|인|합)")
    unc_b, unc_d, d_grouped, d_trunc = [], [], [], []
    for rc, m in sorted(rep.items()):
        if m["kind"] != "본":
            continue
        d = md(rc)
        ch = d.chapter("VIII")
        sp = sorted(spans.get(("B", rc), []))
        for mm in BK.finditer(d.buf, d.off[ch[0]], d.off[ch[1]]):
            if mm.group(0) == "전적" and d.buf[max(0, mm.start() - 1):mm.start()] == "완":
                continue
            if not any(s <= mm.start() and mm.end() <= e for s, e in sp):
                ln = d.line_at(mm.start())
                unc_b.append("%s FY%s md %d행 「%s」 …%s…" % (m["label"], m["fy"], ln + 1, mm.group(0), ctx(d.buf, mm.start(), mm.end(), 20)))
        x, xi = d.chapter("X"), d.chapter("XI")
        s, e = x[0], (xi[1] if xi else x[1])
        sp = sorted(spans.get(("D", rc), []))
        drs = [r for r in data["D"] if r["rcept_no_or_url"] == rc]
        for mm in D_NZ.finditer(d.buf, d.off[s], d.off[e]):
            if not any(a <= mm.start() and mm.end() <= b for a, b in sp):
                ln = d.line_at(mm.start())
                h = d.head_at(ln)
                loc = "[절 %d] 「%s」" % (h[1], h[2]) + (" [표 %d]" % d.tab_of[ln] if d.tab_of[ln] is not None else "")
                if any(re.search(r"개 더: [^;]*" + re.escape(loc) + r"(?![0-9])", r["note"]) for r in drs):
                    d_grouped.append("%s FY%s md %d행 %s" % (m["label"], m["fy"], ln + 1, loc))
                    continue
                if any("개 더:" in r["note"] and " …" in r["note"] for r in drs):
                    d_trunc.append("%s FY%s md %d행 %s" % (m["label"], m["fy"], ln + 1, loc))
                    continue
                unc_d.append("%s FY%s md %d행 「%s」 …%s…" % (m["label"], m["fy"], ln + 1, mm.group(0), ctx(d.buf, mm.start(), mm.end(), 20)))
    say("- B(Ⅷ) 덮이지 않은 검색어 %d곳" % len(unc_b))
    for x in unc_b[:30]:
        say("    · " + x)
    say("- D(Ⅹ~Ⅺ) 행 source_text 밖 검색어 가운데 같은 (상대방·유형) 묶음으로 D 행 note 「같은 상대방·유형 언급 글 N개 더: …」에 위치가 있는 곳 %d"
        " · note 위치 목록이 잘려(…) 확인 못 한 곳 %d" % (len(d_grouped), len(d_trunc)))
    for x in d_trunc[:10]:
        say("    · 잘린 목록: " + x)
    say("- D(Ⅹ~Ⅺ) 덮이지 않은 검색어(행도 note 위치도 없음) %d곳" % len(unc_d))
    for x in unc_d[:30]:
        say("    · " + x)
    for x in unc_b:
        prob("j", "B 누락 후보 " + x)
    for x in unc_d:
        prob("j", "D 누락 후보 " + x)
    say("")

    # ------------------------------------------------ (k) 원문 텍스트 md
    say("## (k) 원문 텍스트 md(dart_out/ops15/원문/<작업>/<회사>__FY<fy>__사업보고서.md · <회사>__2026.2Q__경영공시.md)에 행 글이 있는지")
    omd = {}
    for t in "ABD":
        ok = miss = 0
        for k, r in enumerate(data[t], 2):
            if r["source_text"] == NONE:
                continue
            fn = os.path.join(ORIG, t, "%s__%s__%s.md" % (r["corp_label"], ("FY" + r["fy"]) if r["fy"].isdigit() else r["fy"], r["doc_kind"]))
            if fn not in omd:
                omd[fn] = nzv(open(fn, encoding="utf-8").read()) if os.path.exists(fn) else None
            buf = omd[fn]
            texts = [r["source_text"]] + ([r["reason_text"]] if t == "A" and r["reason_text"] != NONE else [])
            if buf is not None and all(nzv(x) in buf for x in texts):
                ok += 1
            else:
                miss += 1
                prob("k", "%s %d행(%s %s) 글이 원문 md %s 에 없음" % (t, k, r["corp_label"], r["fy"], os.path.relpath(fn, ROOT)))
        say("- %s: 원문 md 에 있음 %d · 없음 %d" % (t, ok, miss))
    say("")

    # ------------------------------------------------ (d) 비밀값
    say("## (d) 키·비밀값 문자열")
    key = os.environ.get("DART_API_KEY", "")
    files = [os.path.join(FRAG, "%s_bs_g1.csv" % t) for t in "ABD"] + [GEN]
    pat = re.compile(r"^(%s)__(FY20\d\d__사업보고서|2026\.2Q__경영공시)\.md$" % "|".join(COS))
    for sub in ("A", "B", "D"):
        dd = os.path.join(ORIG, sub)
        if os.path.isdir(dd):
            files += [os.path.join(dd, f) for f in sorted(os.listdir(dd)) if pat.match(f)]
    hexre = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])")
    kre = re.compile(r"crtfc_key\s*[=:]\s*[0-9A-Za-z]{8,}")
    bad = 0
    for p in files:
        with open(p, encoding="utf-8", errors="replace") as f:
            s = f.read()
        n = (s.count(key) if len(key) >= 8 else 0) + len(hexre.findall(s)) + len(kre.findall(s))
        if n:
            bad += 1
            prob("d", "비밀값 꼴 문자열 %d건: %s" % (n, os.path.relpath(p, ROOT)))
    say("- 본 파일 %d개(조각 CSV 3 · 생성기 1 · 원문 md %d) — 환경변수 키 값 %s · crtfc_key=값 · 40자리 16진: 걸린 파일 %d"
        % (len(files), len(files) - 4, "대조함" if len(key) >= 8 else "(환경변수 없음 — 꼴 검사만)", bad))
    say("")

    # ------------------------------------------------ 고친 곳·결과
    say("## 고친 곳(이번 검증)")
    for x in FIXES:
        say("- " + x)
    say("")
    say("## 참고(실패로 세지 않음)")
    for x in notes + REMARKS:
        say("- " + x)
    say("")
    say("## 결과: %s — 문제 %d건" % ("통과" if not problems else "문제 있음", len(problems)))
    for x in problems[:300]:
        say("- " + x)
    if len(problems) > 300:
        say("- … 그 밖 %d건" % (len(problems) - 300))
    txt = "\n".join(out_lines) + "\n"
    if len(key) >= 8 and key in txt:
        txt = txt.replace(key, "[가림]")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(txt)
    print("verify15_bs_g1: %s — 문제 %d건 → %s" % ("통과" if not problems else "문제 있음", len(problems), os.path.relpath(REPORT, ROOT)))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
