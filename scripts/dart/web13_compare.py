# -*- coding: utf-8 -*-
"""13차 9-4 모범규준 대조표 — 지시서 9-4 의 「전체 조문 번호가 모범규준과 얼마나 맞는지 표로」·「같은 방식으로 대조」.

입력(읽기만 — 고치지 않음):
  handoff/13차_산출물/9-4_모범규준_원문.md  (5장 2016.8.1 판 전문, 6장 2012.3.13 제정판 전문)
  dart_out/risk13/모범규준_조목록.csv       (1~59조 판별 제목·장·절)
  dart_out/risk13/9-4_<회사>_조문목차.csv    8개
  handoff/13차_산출물/9-4_<회사>.md          8개(검증·정합성 보정 끝난 판 — 0장 요약 표, 인용 머리·태그 줄, 1-2·1-3 표, 지시서 항목 대조 표)
  dart_out/risk13/9-4_지시서항목_상태_A.csv·_B.csv  (정합성 보정 그룹 A·B 가 만든 지시서 9-4-2·9-4-3 조별 상태 — R1 세 단계,
                                             D 행렬 지시서 조 칸의 단일 근거)
산출:
  handoff/13차_산출물/9-4_모범규준_대조표.md
  dart_out/risk13/9-4_모범규준_대조표.csv   (행렬: 모범규준 3~58조 × 8개사)
  dart_out/risk13/9-4_조번호대조.csv        (회사 규정 조 ↔ 모범규준 조, 기계 비교)
  dart_out/raw/web13/compare94/             (중간 기록: 파싱 결과·점검 기록)
네트워크 요청 없음(API 키·OC 값 쓰지 않음).

기계 비교: 조(장·절) 제목에서 공백과 가운뎃점(· ㆍ ∙ ・ ‧ • ･)을 지운 글자가 같으면 「같음」.
유사 판정(뜻이 같은 다른 제목)은 이 스크립트에 손으로 적은 표(SIM_IM)이며 산출물에 「(판단)」으로 표시.
실행: python3 -I scripts/dart/web13_compare.py   → 이어서 python3 -I scripts/dart/verify13_compare.py (대조, exit 0/1)

정합성 보정(2026-10-08 KST — 13차 보정 규칙 R1~R5, 비평 dart_out/risk13/critic13.json gaps[1]·contradictions[1]·[5]):
  R1 D 행렬의 지시서 조 칸은 상태 CSV 두 개의 「상태」 글자 그대로(받은 글 / 일부(…) / 추출 범위에 없음) — 회사 md 0장 판정 칸·
     지시서 항목 대조 표(A 그룹 7장, B 그룹 6장) 상태 칸과 한 칸이라도 다르면 아무것도 쓰지 않고 멈춤(SystemExit 1).
     9-4-1 칸(iM 28·30조, 메리츠 9·57조)은 회사 md 지시서 항목 대조 표 「9-4 1. iM」·「9-4 1. 메리츠」 행 상태.
  R2 태그 줄·조번호대조 CSV 「모범규준_조_표지(R2)」 열 — 조문 대조 자료는 「9-4 조문 대조(대조표 A~C)」, 지시서 조는 그대로, 그 밖의 조는 (판단).
  R3 우리 글의 「없음」 단정 → 「찾지 못함」(+ 셈한 범위) / 「추출 범위에 없음」.
  R5 작성일 라벨 KST(1차 실행 2026-10-08T13:01:11+09:00 인데 「2026-10-07」로 적혀 있던 것).
  md 끝 「## 검증 기록」 → 「### 정합성 보정(2026-10-08)」 소절(전·후 — 기준 사본 = 커밋 496ddc4 의 산출물,
     dart_out/raw/web13/compare94/pre/ 에 두고 없으면 git show 로 만듦).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web13 import write_csv, OUT, WORK, RAW, now  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TASK = "compare94"
DATE = "2026-10-08(KST)"
FIRST_RUN = "2026-10-08T13:01:11+09:00"     # 1차 실행(커밋 496ddc4 판 머리) — 그 판 머리 라벨은 「작성일: 2026-10-07」
BASE = "496ddc4"
PRE_DIR = os.path.join("dart_out", "raw", "web13", TASK, "pre")
STATE_A = "dart_out/risk13/9-4_지시서항목_상태_A.csv"
STATE_B = "dart_out/risk13/9-4_지시서항목_상태_B.csv"
TOCLAB = "9-4 조문 대조(대조표 A~C)"
COS = ["메리츠금융지주", "한국투자금융지주", "KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "iM금융지주", "NH농협금융지주"]
SHORT = {"메리츠금융지주": "메리츠", "한국투자금융지주": "한국투자", "KB금융지주": "KB", "신한금융지주": "신한",
         "하나금융지주": "하나", "우리금융지주": "우리", "iM금융지주": "iM", "NH농협금융지주": "NH"}
# 지시서 9-4 가 조사하라고 한 조. 28·30 은 iM 항목(「iM 그룹 리스크관리규정은 28조…, 30조…」), 9(7항)·57 은 메리츠 항목.
LISTED_ALL = [3, 4, 5, 17, 21, 22, 24, 27, 34, 53, 55]
LISTED_CO = {9: ["메리츠금융지주"], 28: ["iM금융지주"], 30: ["iM금융지주"], 57: ["메리츠금융지주"]}
# 9-4-1 칸 — 회사 md 지시서 항목 대조 표의 행 라벨(그룹 A 7장)
DIR941 = {"iM금융지주": ("9-4 1. iM", [28, 30]), "메리츠금융지주": ("9-4 1. 메리츠", [9, 57])}
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
DOTRE = re.compile(r"[\s·ㆍ∙・‧•･]")
MOB_MD = "handoff/13차_산출물/9-4_모범규준_원문.md"
# 6개사 인용 블록에서 그룹 위험관리 규정의 조·장 인용을 찾는 식(위원회·협의회 규정 이름은 「관리」 뒤에 「위원회」 등이 끼어 걸리지 않음)
CITE_RE = re.compile(r"(?:그룹\s*)?(?:리스크|위험)\s*관리\s*(?:규정|정책규정|기준)\s*(?:\(|「)?\s*제\s*\d+\s*(?:조|장)(?:의\s*\d+)?(?:\s*\d+\s*항)?")
MOB_CSV = "dart_out/risk13/모범규준_조목록.csv"
OUT_MD = os.path.join(OUT, "9-4_모범규준_대조표.md")
OUT_MATRIX = os.path.join(WORK, "9-4_모범규준_대조표.csv")
OUT_MAP = os.path.join(WORK, "9-4_조번호대조.csv")
MAP_COLS = ["회사", "규정명", "구분", "회사_조", "회사_조제목(원문)", "쪽", "모범_같은번호_제목_2016.8.1", "기계비교_2016.8.1",
            "같은제목_다른번호_2016.8.1", "모범_같은번호_제목_2012.3.13", "기계비교_2012.3.13", "같은제목_다른번호_2012.3.13",
            "같은제목_장절(기계)", "뜻같은다른제목(판단)", "모범규준_조_표지(R2)", "회사산출물_대응판단(그대로)", "문서", "접수번호또는URL", "근거"]

# iM 리스크관리규정 조 제목 ↔ 모범규준 조 제목 — 뜻이 같거나 비슷한 다른 제목(이 작업의 판단).
# 분류: 같음(뜻 같음) / 비슷(뜻 비슷·두 제목을 합친 꼴·닿음) / 못찾음(뜻이 같은 제목을 찾지 못함) / -(기계 일치가 있어 판단 안 함)
SIM_IM = {
    1: ("-", ""),
    2: ("-", "3조 「적용대상」과 기계 일치 — 주제도 같음(회사 md 1-2)"),
    3: ("비슷", "18조 「측정 및 관리 대상」과 뜻 비슷(「관리대상」)"),
    4: ("같음", "2조 「정의」와 뜻 같음"),
    5: ("같음", "4조 「위험관리 철학」과 뜻 같음 — 「리스크」/「위험관리」 낱말만 다름(2012 판 4조 「리스크 철학」과는 기계 일치)"),
    6: ("비슷", "4조 「위험관리 철학」의 하위 주제(같은 뜻 제목은 찾지 못함)"),
    7: ("같음", "5조 「위험관리 원칙」과 뜻 같음(2012 판 5조 「리스크관리 원칙」과는 기계 일치)"),
    8: ("비슷", "18조 「측정 및 관리 대상」과 닿음(위험 유형 열거)"),
    9: ("비슷", "19조 「위험 측정」·20조 「위험 관리」 두 제목을 합친 꼴"),
    10: ("비슷", "7조 「조직구성」과 뜻 비슷"),
    11: ("비슷", "8조 「이사회」·9조 「그룹위험관리위원회」 두 제목을 합친 꼴"),
    12: ("-", "10조 「경영진」과 기계 일치"),
    13: ("-", "2016.8.1 판 11조 「그룹위험관리책임자」와 기계 일치"),
    14: ("같음", "12조 「그룹위험관리협의회」와 뜻 같음(「그룹」 빠짐)"),
    15: ("비슷", "13조 「그룹위험관리부서」와 뜻 비슷"),
    16: ("비슷", "37조 「자본적정성 평가 및 관리 체제」·47조 「내부자본 한도 관리」와 닿음"),
    17: ("못찾음", "같은 뜻 제목은 찾지 못함 — 주제는 14조 ①·15조 ①(회사 md 1-2)"),
    18: ("못찾음", "같은 뜻 제목은 찾지 못함 — 주제는 9조 ⑥ 3호(적정투자한도·손실허용한도, 회사 md 1-2)"),
    19: ("비슷", "47조 「내부자본 한도 관리」와 뜻 비슷"),
    20: ("못찾음", "같은 뜻 제목은 찾지 못함"),
    21: ("못찾음", "같은 뜻 제목은 찾지 못함 — 주제는 8조 ②·9조 ⑥ 5호(회사 md 1-2)"),
    22: ("비슷", "15조 「승인 및 사전협의」 제목의 일부와 같음"),
    23: ("비슷", "16조 「보고체계」·48조 「보고」와 닿음"),
    24: ("못찾음", "같은 뜻 제목은 찾지 못함 — 주제는 17조 ①·③(회사 md 1-2)"),
    25: ("-", "17조 「의사전달체계」와 기계 일치"),
    26: ("같음", "14조 「위험 통제」와 뜻 같음(2012 판 14조 「리스크 통제」와는 기계 일치)"),
    27: ("못찾음", "같은 뜻 제목은 찾지 못함 — 주제는 11조 ⑨·14조 ④ 4호(회사 md 1-2)"),
    28: ("같음", "28조 「시스템 구축 및 관리」와 뜻 같음 — 「운영」/「관리」 한 낱말 다름"),
    29: ("-", "29조 「자료 수집 및 관리」와 기계 일치(번호도 같음)"),
    30: ("같음", "모범규준 제4장 제4절 「적합성 검증」(30~32조)과 같음 — 절 제목과 기계 일치, 같은 번호 30조 제목은 「목적」"),
    31: ("같음", "52조 「위기관리체계」와 뜻 같음(「그룹」 붙음)"),
    32: ("비슷", "57조 「비상계획」과 뜻 비슷"),
    33: ("비슷", "33조 「그룹내 위험 전이 방지」와 주제 같음(회사 md 1-2) — 제목 낱말은 「그룹내」만 같음"),
    34: ("같음", "34조 「해외위험 관리」와 뜻 같음 — 「리스크」/「위험」 낱말만 다름(2012 판 34조와는 기계 일치)"),
    35: ("못찾음", "같은 뜻 제목은 찾지 못함 — 34조(해외위험 관리)와 닿음(회사 md 1-2)"),
}


# ───────────────────────────── 공통 도구
def norm(s):
    return DOTRE.sub("", s or "")


def strip_ann(s):
    """장·절 제목 뒤 표시(「<삭제 …>」, 「(2016.10.27 신설)」 꼴)를 뗀 글 — 장·절 기계 비교용."""
    s = re.sub(r"<[^>]*>", "", s or "")
    s = re.sub(r"\(\d{4}\.\d{1,2}[.,]\s*\d{1,2}\s*(신설|개정)\)", "", s)
    return s.strip()


def p(rel):
    return os.path.join(ROOT, rel)


def rd(rel):
    with open(p(rel), encoding="utf-8") as f:
        return f.read()


def rcsv(rel):
    with open(p(rel), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha(rel):
    with open(p(rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def md_rel(co):
    return f"handoff/13차_산출물/9-4_{co}.md"


def csv_rel(co):
    return f"dart_out/risk13/9-4_{co}_조문목차.csv"


def cell(s):
    return (s or "").replace("|", "／").replace("\n", " ")


# R3 — 우리 글의 「없음」 단정을 바꾼 낱말(전 → 후). 앞 셋은 이 스크립트가 만드는 글에 그대로 쓰고, 정합성 보정 소절에 전·후로 적음.
NO_SAME_ART = "같은 번호 조 찾지 못함(모범규준 1~59조 — 전문 기계 셈)"
NO_SAME_CH = "같은 번호 장 찾지 못함(모범규준 전문은 제7장까지 — 전문 기계 셈)"
R3_WORDS = [
    ("같은 번호 장 없음(모범규준은 제7장까지 — 전문 기계 셈)", NO_SAME_CH),
    ("같은 번호 조 없음(모범규준 원문에 「조의」 조 없음 — 전문 기계 셈)", "같은 번호 조 찾지 못함(모범규준 전문에서 「제N조의M」 꼴 조를 찾지 못함 — 전문 기계 셈)"),
    ("같은 번호 조 없음(같은 까닭)", "같은 번호 조 찾지 못함(같은 까닭)"),
    ("⑤항 줄 없음(전문 기계 셈)", "⑤항 줄 찾지 못함(전문 기계 셈)"),
    ("새로 받은 자료 없음(네트워크 요청 0건)", "새로 받은 자료 0건(네트워크 요청 0건)"),
    ("「전체 조 번호 ↔ 모범규준」 대조는 6개사 모두 할 수 없음", "「전체 조 번호 ↔ 모범규준」 대조는 6개사 모두 하지 못함(대응 규정 조문 목차가 추출 범위에 없음)"),
    ("요약 표 행 없음", "범주를 뺌 — 지시서 조 칸은 모두 상태 CSV·회사 md 지시서 항목 대조 표에서 채움"),
]


LOG = []


def log(msg):
    LOG.append(msg)


# ───────────────────────────── 모범규준
def sect(L, prefix):
    i = next(k for k, l in enumerate(L) if l.startswith(prefix))
    j = next((k for k in range(i + 1, len(L)) if L[k].startswith("## ")), len(L))
    return i, j


def parse_edition(L, prefix):
    """모범규준 md 의 한 장(5장·6장) 코드 블록에서 조·장·절을 읽음(부칙 앞까지)."""
    i, j = sect(L, prefix)
    cite = next(l for l in L[i + 1:j] if l.startswith("["))
    a = next(k for k in range(i, j) if L[k].startswith("```"))
    b = next(k for k in range(a + 1, j) if L[k].startswith("```"))
    arts, chs, secs = {}, [], []
    cur, ch, se = None, None, None
    for l in L[a + 1:b]:
        if l.replace(" ", "").startswith("부칙"):
            break
        m = re.match(r"^제\s*(\d+)\s*장\s*(.*)$", l)
        if m:
            ch = (int(m.group(1)), m.group(2).strip())
            chs.append(ch)
            se, cur = None, None
            continue
        m = re.match(r"^제\s*(\d+)\s*절\s*(.*)$", l)
        if m:
            se = (int(m.group(1)), m.group(2).strip())
            secs.append((ch[0], se[0], se[1]))
            cur = None
            continue
        m = re.match(r"^제\s*(\d+)\s*조\s*\(([^)]*)\)", l)
        if m:
            cur = int(m.group(1))
            arts[cur] = {"title": m.group(2), "lines": [l], "ch": ch, "se": se}
            continue
        if cur is not None:
            arts[cur]["lines"].append(l)
    return {"cite": cite, "arts": arts, "chs": chs, "secs": secs, "range": (a + 2, b)}


def hang_groups(lines):
    """조 줄들을 항(①…)별로 묶음. 조 머리 줄에 ① 이 없으면 0 으로."""
    g, key = {}, None
    for idx, l in enumerate(lines):
        s = l.strip()
        if idx == 0:
            m = re.match(r"^제\s*\d+\s*조\s*\([^)]*\)\s*(.)", l)
            key = (CIRC.index(m.group(1)) + 1) if (m and m.group(1) in CIRC) else 0
        elif s and s[0] in CIRC:
            key = CIRC.index(s[0]) + 1
        g.setdefault(key, []).append(l)
    return g


def first_sentence(line):
    s = line.strip()
    m = re.search(r"다\.", s)
    return s[:m.end()] if m else s


class Mob:
    def __init__(self):
        rows = rcsv(MOB_CSV)
        self.rows = {int(r["조"]): r for r in rows}
        L = rd(MOB_MD).split("\n")
        self.e16 = parse_edition(L, "## 5.")
        self.e12 = parse_edition(L, "## 6.")
        # 장·절 제목(기계 비교용) — 판별
        self.units = {}
        for ed, e in (("16", self.e16), ("12", self.e12)):
            u = []
            for no, t in e["chs"]:
                u.append((f"제{no}장 「{t}」", norm(strip_ann(t))))
            for cno, sno, t in e["secs"]:
                u.append((f"제{cno}장 제{sno}절 「{t}」", norm(strip_ann(t))))
            self.units[ed] = u
        # 점검: CSV 제목 ↔ 원문 조 머리
        for ed, e, col in (("2016.8.1", self.e16, "제목_2016.8.1판"), ("2012.3.13", self.e12, "제목_2012.3.13제정판")):
            miss = [n for n in self.rows if n not in e["arts"]]
            diff = [n for n in self.rows if n in e["arts"] and norm(e["arts"][n]["title"]) != norm(self.rows[n][col])]
            log(f"모범규준 {ed} 판: 원문 md 조 머리 {len(e['arts'])}개, CSV {len(self.rows)}개 — 원문에 없는 CSV 조 {miss or '0'}, 제목 다름 {diff or '0'}")
        d167 = [n for n in self.rows if norm(self.rows[n]["제목_2016.7개정예고안"]) != norm(self.rows[n]["제목_2016.8.1판"])]
        log(f"2016.7 개정예고안 제목 ↔ 2016.8.1 판 제목 기계 비교: 다른 조 {d167 or '0'}")

    def title(self, n, ed):
        r = self.rows.get(n)
        if not r:
            return ""
        return r["제목_2016.8.1판"] if ed == "16" else r["제목_2012.3.13제정판"]

    def chapter_title(self, n, ed):
        e = self.e16 if ed == "16" else self.e12
        for no, t in e["chs"]:
            if no == n:
                return t
        return ""

    def cmp(self, title, n, ed):
        """같은 번호 조 제목, 기계 비교(같음/다름/같은 번호 없음), 같은 제목의 다른 번호, 같은 제목의 장·절."""
        same = self.title(n, ed) if n else ""
        if not same:
            res = NO_SAME_ART
        else:
            res = "같음" if norm(title) == norm(same) else "다름"
        others = [m for m in sorted(self.rows) if m != n and norm(self.title(m, ed)) == norm(title)]
        units = [lab for lab, t in self.units[ed] if t == norm(strip_ann(title))]
        return same, res, others, units

    def cmp_ch(self, title, n, ed):
        same = self.chapter_title(n, ed)
        res = ("같음" if norm(strip_ann(title)) == norm(strip_ann(same)) else "다름") if same else NO_SAME_CH
        others = [lab for lab, t in self.units[ed] if t == norm(strip_ann(title)) and not lab.startswith(f"제{n}장 「")]
        arts = [m for m in sorted(self.rows) if norm(self.title(m, ed)) == norm(strip_ann(title))]
        return same, res, others, arts


# ───────────────────────────── 회사 md
def quote_blocks(L):
    """인용 머리(#### [ID] … 또는 ### X-NN …)마다 id·제목·출처 줄·조 태그 줄·코드 줄."""
    heads = []
    for k, l in enumerate(L):
        m = re.match(r"^#### \[([A-Z]+-[A-Za-z0-9]+)\]\s*(.*)$", l) or re.match(r"^### ([A-Z]-\d+[a-z]?)\s+(.*)$", l)
        if m:
            heads.append((k, m.group(1), m.group(2)))
    out = []
    for idx, (k, qid, title) in enumerate(heads):
        end = next((t for t in range(k + 1, len(L)) if L[t].startswith("#")), len(L))
        blk = L[k + 1:end]
        src = next((l for l in blk if l.startswith("- 인용:")), None) or next((l for l in blk if l.startswith("[")), "")
        tag = next((l for l in blk if l.startswith("- 이 글이 닿는 모범규준 조") or l.startswith("모범규준 조:")), "")
        code, on = [], False
        for t, l in enumerate(blk):
            if l.startswith("```"):
                on = not on
                continue
            if on:
                code.append((k + 1 + t + 1, l))  # (md 줄 번호(1부터), 글)
        out.append({"id": qid, "title": title, "line": k + 1, "src": src, "tag": tag, "code": code})
    return out


def doc_label(src):
    for kw, lab in (("연차보고서", "연차"), ("반기보고서", "반기"), ("사업보고서", "사업"), ("경영공시", "경영공시"),
                    ("현황", "경영공시"), ("Report", "경영공시"), ("모범규준", "모범규준")):
        if kw in src:
            return lab
    return "문서"


def page_of(src):
    m = re.search(r"(p\.[0-9][^·\]]*?)\s*(?:·|\])", src)
    if not m:
        return ""
    s = re.sub(r"\(인쇄[^)]*\)", "", m.group(1))
    s = re.sub(r"\(DART 쪽[^)]*\)", "", s)
    return s.strip()


def table_after(L, prefix):
    """prefix 로 시작하는 머리 다음의 첫 md 표(머리 줄 + 자료 줄)."""
    i = next(k for k, l in enumerate(L) if l.startswith(prefix))
    rows, started = [], False
    for l in L[i + 1:]:
        if l.startswith("|"):
            started = True
            rows.append([c.strip() for c in l.strip().strip("|").split("|")])
        elif started:
            break
        elif l.startswith("#"):
            break
    return rows[0], rows[2:]


def nums_first_cell(c):
    hit = re.findall(r"(\d+)조", c)          # 「3조(적용대상)」 꼴
    if hit:
        return [int(x) for x in hit]
    return [int(x) for x in re.findall(r"\d+", c.split("(")[0])]   # 「4·5」, 「9(인용 조문)」, 「28·30(사용자 표)」 꼴


def short_places(s, n=2):
    parts = [x.strip() for x in s.split(";") if x.strip()]

    def sh(x):
        x = x.replace("연차보고서", "연차").replace("사업보고서", "사업")
        x = re.sub(r"\(DART 쪽[^)]*\)", "", x)
        x = re.sub(r"\(인쇄[^)]*\)", "", x)
        x = re.sub(r"\s+\(", "(", x)
        return x.strip()

    parts = [sh(x) for x in parts]
    o = "; ".join(parts[:n])
    if len(parts) > n:
        o += f" 외 {len(parts) - n}"
    return o


def r1_kind(s):
    """R1 세 단계 낱말 — 받은 글 / 일부 / 추출 범위에 없음 / 그 밖(None)."""
    s = s or ""
    if s == "받은 글":
        return "받은 글"
    if s.startswith("일부(") and s.endswith(")"):
        return "일부"
    if s.startswith("추출 범위에 없음"):
        return "추출 범위에 없음"
    return None


def section0(co, L):
    """회사 md 0장 요약 표의 판정 칸(정합성 보정 뒤 8개사 모두 「판정」 칸) → {조: {...}}."""
    hdr, data = table_after(L, "## 0.")
    jcol = next((k for k, h in enumerate(hdr) if h == "판정"), None)
    if jcol is None:
        raise SystemExit(f"[web13_compare] {co} 0장 표에 「판정」 칸이 없음 — 정합성 보정(fix13_A·B) 전 판으로 보임")
    dcol = next(k for k, h in enumerate(hdr) if h.startswith("문서·쪽"))
    out = {}
    for r in data:
        if len(r) != len(hdr):
            log(f"{co} 0장 표: 칸 수 다름 {len(r)}≠{len(hdr)} — {r[0]}")
            continue
        ns = nums_first_cell(r[0])
        for n in ns:
            if n in out:
                raise SystemExit(f"[web13_compare] {co} 0장 표에 {n}조 행이 둘")
            out[n] = {"판정": r[jcol], "문서쪽": r[dcol], "first": r[0]}
    return out


def directive_table(co, L):
    """회사 md 「지시서 항목별 대조」 표(그룹 A 7장·그룹 B 6장)의 상태 칸 → {조: (상태, 행 라벨)}.
    「9-4 2. 21·22·24」(A)·「9-4-2 21·22·24」(B)·「9-4 3.」·「9-4-3」 행은 조마다 나눔(B 는 「N조: 상태 / …」 꼴,
    A 는 한 상태이거나 「조별 상태는 아래 세 행」 + 조별 행). 9-4-1 행은 그 회사 항목(DIR941)일 때만."""
    i = next(k for k, l in enumerate(L) if re.match(r"^## [67]\. 지시서 항목별 대조", l))
    j = next((k for k in range(i + 1, len(L)) if L[k].startswith("## ")), len(L))
    hdr, scol, out = None, None, {}
    for l in L[i + 1:j]:
        if l.startswith("### "):
            break
        if not l.startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if hdr is None:
            hdr = c
            scol = next(k for k, h in enumerate(hdr) if h.startswith("상태"))
            continue
        if set(c[0]) <= set("-: "):
            continue
        lab, st = c[0], c[scol]
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
        if multi:
            for a in arts:
                if a not in multi:
                    raise SystemExit(f"[web13_compare] {co} 지시서 항목 대조 「{lab}」 행에 {a}조 상태가 없음")
                out[a] = (multi[a], lab)
        elif "조별 상태는 아래" in st:
            continue
        else:
            for a in arts:
                if a in out and len(arts) > 1:
                    continue            # 조별 행이 이미 있음(조별 행이 우선)
                out[a] = (st, lab)
    return out


def load_status():
    """상태 CSV 두 개 → {(회사, 조): 행}. 회사마다 지시서 조 11개가 다 있어야 함."""
    st = {}
    for rel in (STATE_A, STATE_B):
        for r in rcsv(rel):
            key = (r["회사"], int(r["모범규준_조"]))
            if key in st:
                raise SystemExit(f"[web13_compare] 상태 CSV 에 {key} 행이 둘")
            st[key] = dict(r, _file=rel)
    miss = [(co, n) for co in COS for n in LISTED_ALL if (co, n) not in st]
    if miss or len(st) != len(COS) * len(LISTED_ALL):
        raise SystemExit(f"[web13_compare] 상태 CSV 행 {len(st)}(기대 {len(COS) * len(LISTED_ALL)}), 빠진 칸 {miss}")
    return st


def status_mismatch(ST, S0, DT):
    """상태 CSV ↔ 회사 md 0장 판정 칸 ↔ 지시서 항목 대조 표 상태 칸 — 한 글자라도 다른 칸 목록."""
    bad = []
    for co in COS:
        for n in LISTED_ALL:
            s = ST[(co, n)]["상태"]
            if r1_kind(s) is None:
                bad.append(f"{co} {n}조: 상태 CSV 「{s}」 가 R1 세 단계가 아님")
            z = S0[co].get(n, {}).get("판정")
            d = DT[co].get(n, ("", ""))[0]
            if z != s:
                bad.append(f"{co} {n}조: 상태 CSV 「{s}」 ≠ md 0장 판정 「{z}」")
            if d != s:
                bad.append(f"{co} {n}조: 상태 CSV 「{s}」 ≠ md 지시서 항목 대조 「{d}」")
        if co in DIR941:
            for n in DIR941[co][1]:
                z = S0[co].get(n, {}).get("판정")
                d = DT[co].get(n, ("", ""))[0]
                if not d or z != d or r1_kind(d) is None:
                    bad.append(f"{co} {n}조(9-4-1): md 0장 판정 「{z}」 / 지시서 항목 대조 「{d}」 — 같지 않거나 R1 세 단계가 아님")
    return bad


def cite_ptr(geun, n=3):
    """상태 CSV 「근거」 칸 → 「[인용 번호] 문서 쪽」 앞 n 개(+ 외 k)."""
    out = []
    for s in re.split(r" / |\);\s*", geun or ""):
        m = re.match(r"\s*\[?([A-Z]{1,2}-[A-Za-z]?\d+[a-z]?)\]?", s)
        if not m:
            continue
        pg = re.findall(r"p\.\d+(?:[~–-](?:p\.)?\d+)?", s)
        out.append(f"[{m.group(1)}] {doc_label(s)} {pg[-1] if pg else ''}".strip())
    out = list(dict.fromkeys(out))
    return "; ".join(out[:n]) + (f" 외 {len(out) - n}" if len(out) > n else "")


def tag_nums(tag):
    return sorted({int(x) for x in re.findall(r"(?<![제\d])(\d+)조\(", tag)})


def evidence(co, L, qb, csvrows):
    """지시 목록 밖 조에 대해 회사 md·CSV 에 있는 근거(인용 태그·대응표·CSV 판단 칸)."""
    ev = {}

    def add(n, item):
        if 3 <= n <= 58:
            ev.setdefault(n, [])
            if item not in ev[n]:
                ev[n].append(item)

    if co == "메리츠금융지주":
        hdr, data = table_after(L, "### 1-2-1")
        for r in data:
            m = re.match(r"(\d+)조", r[2])
            if not m:
                continue
            if "인용 없음" in r[0] or "추출 범위에 없음" in r[0]:     # 「(참고) 메리츠 인용은 추출 범위에 없음」(그룹 A 보정 뒤 표기)
                add(int(m.group(1)), "md 1-2-1: 같은 번호 조 인용은 찾지 못함 — 보고 「그룹 통합 위기상황분석」과 주제 같음")
            else:
                add(int(m.group(1)), f"md 1-2-1: {r[0].replace('그룹리스크관리규정 ', '그룹리스크관리규정 ')} 인용 — 주제 {r[-1].split(' — ')[0]}")
    if co == "한국투자금융지주":
        hdr, data = table_after(L, "### 1-2 그룹리스크관리규정")
        for r in data:
            for ch, a, b in re.findall(r"(제\d+장)[^()]*\((\d+)~(\d+)조\)", r[3]):
                for n in range(int(a), int(b) + 1):
                    add(n, f"md 1-2: 그룹리스크관리규정 {ch} 인용(장 단위)")
        hdr, data = table_after(L, "### 1-3 첨부 규정 조문 목차")
        for r in data:
            for x in re.findall(r"(?<![제\d])(\d+)조", r[4]):
                add(int(x), f"md 1-3: {r[0].split('(')[0]} {r[1]}({r[2]})")
    if co == "iM금융지주":
        hdr, data = table_after(L, "### 1-3 모범규준 조(3~58)")
        for r in data:
            ns = re.findall(r"^(\d+)조", r[0])
            if ns:
                t = r[1]
                if t.startswith("대응 조 없음"):
                    add(int(ns[0]), "md 1-3: 본칙에서 대응 조를 찾지 못함(지침 위임 — 지침은 추출 범위에 없음)")
                else:
                    add(int(ns[0]), "md 1-3: 리스크관리규정 " + (t if len(t) <= 34 else t[:33] + "…"))
    if co == "메리츠금융지주":
        hdr, data = table_after(L, "### 1-3 그룹리스크관리위원회규정")
        for r in data:
            for x in re.findall(r"(?<![제\d])(\d+)조", r[3]):
                add(int(x), f"md 1-3: 첨부6 위원회규정 {r[0]}({r[1]})")
    for q in qb:
        if q["id"].startswith("MB-") or doc_label(q["src"]) == "모범규준":
            continue          # 회사 md 안의 모범규준 원문 인용([MB-n])은 회사 근거가 아님
        for n in tag_nums(q["tag"]):
            add(n, f"[{q['id']}] {doc_label(q['src'])} {page_of(q['src'])}".strip())
    if csvrows and "닿는모범규준조(판단)" in csvrows[0]:
        for r in csvrows:
            for x in re.findall(r"(?<![제\d])(\d+)조\(", r["닿는모범규준조(판단)"]):
                add(int(x), f"CSV: {r['규정명']} {r['조번호']}")
    return ev


def directive_row(L):
    """회사 md 「지시서 항목별 대조」 표의 「9-4 1.」(또는 「9-4-1 목차」) 행."""
    for l in L:
        if l.startswith("| 9-4-1 목차") or l.startswith("| 9-4 1."):
            return [c.strip() for c in l.strip().strip("|").split("|")]
    return []


# ───────────────────────────── A. iM
def part_a(mob, L_im, rows_im):
    reg = [r for r in rows_im if r["규정명"].startswith("리스크관리규정(")]
    # 원문 [I-11] 블록의 조 머리와 CSV 대조
    qb = {q["id"]: q for q in quote_blocks(L_im)}
    q11 = qb["I-11"]
    heads = []
    for ln, l in q11["code"]:
        m = re.match(r"^\s*제\s*(\d+)\s*조\s*\(([^)]*)\)(.*)$", l)
        if m:
            heads.append((ln, int(m.group(1)), m.group(2), l))
    body = heads[:35]
    csv_body = [r for r in reg if re.fullmatch(r"제\d+조", r["조번호"])]
    mism = [(r["조번호"], r["조제목"], h[2]) for r, h in zip(csv_body, body) if r["조제목"] != h[2] or r["조번호"] != f"제{h[1]}조"]
    seq = [h[1] for h in body]
    del_cnt = sum(1 for _, l in q11["code"] if "삭제" in l)
    eui = sum(1 for _, l in q11["code"] if re.search(r"제\s*\d+\s*조의\s*\d+", l))
    chk = {"본칙_조머리": len(body), "CSV_본칙": len(csv_body), "번호연속": seq == list(range(1, 36)),
           "CSV제목불일치": mism, "삭제글자": del_cnt, "조의꼴": eui, "부칙_조머리": len(heads) - 35,
           "I11_md줄": q11["line"], "I11_인용": q11["src"]}
    log(f"A 점검: [I-11] 본칙 조 머리 {len(body)}개(번호 1~35 연속={chk['번호연속']}), CSV 본칙 {len(csv_body)}개, 제목 불일치 {len(mism)}, 「삭제」 글자 {del_cnt}건, 「제N조의M」 꼴 {eui}건, 부칙 조 머리 {chk['부칙_조머리']}개")
    head_line = {h[1]: h[3] for h in body}

    rows, chapters, buchik = [], [], []
    cur_ch = ""
    for r in reg:
        no = r["조번호"]
        if re.fullmatch(r"제\d+장", no):
            n = int(re.findall(r"\d+", no)[0])
            cur_ch = f"{no} {r['조제목']}"
            s16, r16, o16, a16 = mob.cmp_ch(r["조제목"], n, "16")
            s12, r12, o12, a12 = mob.cmp_ch(r["조제목"], n, "12")
            chapters.append({"no": no, "n": n, "title": r["조제목"], "page": r["쪽"], "s16": s16, "r16": r16, "o16": o16,
                             "a16": a16, "s12": s12, "r12": r12, "o12": o12, "a12": a12, "src": r})
        elif re.fullmatch(r"제\d+조", no):
            n = int(re.findall(r"\d+", no)[0])
            s16, r16, o16, u16 = mob.cmp(r["조제목"], n, "16")
            s12, r12, o12, u12 = mob.cmp(r["조제목"], n, "12")
            rows.append({"no": no, "n": n, "title": r["조제목"], "page": r["쪽"], "ch": cur_ch, "s16": s16, "r16": r16,
                         "o16": o16, "u16": u16, "s12": s12, "r12": r12, "o12": o12, "u12": u12,
                         "sim": SIM_IM.get(n, ("-", "")), "md12": r.get("비고", ""), "head": head_line.get(n, ""), "src": r})
        else:
            buchik.append(r)

    def cat(rr, ed):
        if rr["r" + ed] == "같음":
            return "번호·제목 일치"
        if rr["o" + ed]:
            return "제목만 일치(번호 다름)"
        return "일치 없음"

    for rr in rows:
        rr["c16"], rr["c12"] = cat(rr, "16"), cat(rr, "12")
        rank = {"번호·제목 일치": 0, "제목만 일치(번호 다름)": 1, "일치 없음": 2}
        rr["cany"] = min((rr["c16"], rr["c12"]), key=lambda c: rank[c])
    stats = {}
    for key in ("c16", "c12", "cany"):
        st = {"번호·제목 일치": [], "제목만 일치(번호 다름)": [], "일치 없음": []}
        for rr in rows:
            st[rr[key]].append(rr["n"])
        stats[key] = st
    simst = {}
    for rr in rows:
        simst.setdefault(rr["sim"][0], []).append(rr["n"])
    unit_hits = [(rr["n"], rr["u16"], rr["u12"]) for rr in rows if rr["u16"] or rr["u12"]]
    return {"rows": rows, "chapters": chapters, "buchik": buchik, "stats": stats, "simst": simst, "chk": chk,
            "unit_hits": unit_hits, "q11": q11}


# ───────────────────────────── B. 메리츠
def part_b(mob, L_m, rows_m):
    qb = quote_blocks(L_m)
    cites = {}
    for q in qb:
        if not re.fullmatch(r"M-\d+", q["id"]):
            continue
        code = q["code"]
        meeting, kind = "", ""
        for t, (ln, l) in enumerate(code):
            mm = re.match(r"^[가-힣]\)\s*(제\d{4}년도 제\d+차) 그룹리스크관리위원회\s*:\s*(\d{4}\.\d{2}\.\d{2})", l.strip())
            if mm:
                meeting = f"{mm.group(1)}({mm.group(2)})"
            mk = re.match(r"^\s*([12])\)\s*(보고안건|의결안건)", l)
            if mk:
                kind = mk.group(2)
            m = re.search(r"그룹리스크관리규정\s*((?:제\s*\d+\s*조(?:\s*\d+\s*항)?[,\s]*)+)", l)
            if not m:
                continue
            text = [l]
            k = t + 1
            while k < len(code):
                nl = code[k][1]
                if re.match(r"^\s{3,}\S", nl) and not re.match(r"^\s*([가-힣]\.|\d\)|※)", nl):
                    text.append(nl)
                    k += 1
                else:
                    break
            item = re.match(r"^\s*([가-힣])\.", l)
            for jo, hang in re.findall(r"제\s*(\d+)\s*조(?:\s*(\d+)\s*항)?", m.group(1)):
                key = (int(jo), int(hang) if hang else 0)
                cites.setdefault(key, []).append({"qid": q["id"], "src": q["src"], "page": page_of(q["src"]),
                                                  "meeting": meeting, "kind": kind,
                                                  "item": item.group(1) if item else "", "lines": text,
                                                  "md_line": code[t][0]})
    # 회사 md 1-2-1 표(주제 대응 판단 — 그대로)
    hdr, data = table_after(L_m, "### 1-2-1")
    judg = {}
    for r in data:
        m = re.match(r"그룹리스크관리규정 제(\d+)조(?:\s*(\d+)항)?", r[0])
        if m:
            judg[(int(m.group(1)), int(m.group(2)) if m.group(2) else 0)] = {"횟수": r[1], "대응": r[-1]}
    csvc = {}
    for r in rows_m:
        if r["규정명"] == "그룹리스크관리규정":
            m = re.match(r"제(\d+)조(?:\s*제(\d+)항)?", r["조번호"])
            if m:
                csvc[(int(m.group(1)), int(m.group(2)) if m.group(2) else 0)] = r
    out = []
    for key in sorted(cites):
        jo, hang = key
        a16, a12 = mob.e16["arts"].get(jo), mob.e12["arts"].get(jo)
        g16, g12 = hang_groups(a16["lines"]), hang_groups(a12["lines"])
        h16 = [k for k in g16 if k > 0]
        h12 = [k for k in g12 if k > 0]
        same16 = g16.get(hang, []) if hang else []
        same12 = g12.get(hang, []) if hang else []
        texts = []
        for c in cites[key]:
            t = "\n".join(c["lines"])
            if t not in [x[0] for x in texts]:
                texts.append((t, c))
        out.append({"key": key, "cites": cites[key], "texts": texts, "a16": a16, "a12": a12, "h16": h16, "h12": h12,
                    "same16": same16, "same12": same12, "judg": judg.get(key, {}), "csv": csvc.get(key),
                    "title_cmp": "비교 불가 — 메리츠 조 제목 추출 범위에 없음(회사 CSV 「조 제목 미기재」)"})
    log("B 점검: 메리츠 md 인용 블록에서 「그룹리스크관리규정 제N조」 인용 " +
        ", ".join(f"제{k[0]}조{(' ' + str(k[1]) + '항') if k[1] else ''} {len(v)}회" for k, v in sorted(cites.items())) +
        f" / 회사 CSV 행 {sorted(csvc)} / md 1-2-1 행 {sorted(judg)}")
    return out


# ───────────────────────────── C·조번호대조 CSV
def map_rows(mob, co, rows, A):
    """회사 CSV 의 모든 행 → 조번호대조 CSV 행."""
    out = []
    for r in rows:
        reg, no, title = r["규정명"], r["조번호"], r["조제목"]
        base = {"회사": co, "규정명": reg, "회사_조": no, "회사_조제목(원문)": title, "쪽": r["쪽"],
                "문서": r["문서"], "접수번호또는URL": r["접수번호또는URL"],
                "회사산출물_대응판단(그대로)": r.get("비고") or r.get("닿는모범규준조(판단)") or "",
                "근거": f"{csv_rel(co)}; {md_rel(co)}"}
        d = dict.fromkeys(["구분", "모범_같은번호_제목_2016.8.1", "기계비교_2016.8.1", "같은제목_다른번호_2016.8.1",
                           "모범_같은번호_제목_2012.3.13", "기계비교_2012.3.13", "같은제목_다른번호_2012.3.13",
                           "같은제목_장절(기계)", "뜻같은다른제목(판단)"], "")
        base.update(d)
        no_ok = re.fullmatch(r"제(\d+)조", no)
        ch_ok = re.fullmatch(r"제(\d+)장", no)
        title_missing = (not title) or title == "-" or "추출 범위에 없음" in title
        if no.startswith("부칙"):
            base["구분"] = "부칙 조 — 모범규준 본칙 같은 번호 대조 대상 아님"
        elif "조문 목차 추출 범위에 없음" in no or (no in ("-", "") and title_missing):
            base["구분"] = "규정 조문 목차 추출 범위에 없음"
        elif ch_ok and not title_missing:
            n = int(ch_ok.group(1))
            s16, r16, o16, a16 = mob.cmp_ch(title, n, "16")
            s12, r12, o12, a12 = mob.cmp_ch(title, n, "12")
            base.update({"구분": "장", "모범_같은번호_제목_2016.8.1": f"제{n}장 {s16}" if s16 else "",
                         "기계비교_2016.8.1": r16, "같은제목_다른번호_2016.8.1": " / ".join(o16 + [f"{m}조" for m in a16]),
                         "모범_같은번호_제목_2012.3.13": f"제{n}장 {s12}" if s12 else "", "기계비교_2012.3.13": r12,
                         "같은제목_다른번호_2012.3.13": " / ".join(o12 + [f"{m}조" for m in a12])})
        elif no_ok and not title_missing:
            n = int(no_ok.group(1))
            s16, r16, o16, u16 = mob.cmp(title, n, "16")
            s12, r12, o12, u12 = mob.cmp(title, n, "12")
            base.update({"구분": "본칙 조" if (co == "iM금융지주" and reg.startswith("리스크관리규정(")) else "조",
                         "모범_같은번호_제목_2016.8.1": f"{n}조 {s16}" if s16 else "", "기계비교_2016.8.1": r16,
                         "같은제목_다른번호_2016.8.1": "·".join(f"{m}조" for m in o16),
                         "모범_같은번호_제목_2012.3.13": f"{n}조 {s12}" if s12 else "", "기계비교_2012.3.13": r12,
                         "같은제목_다른번호_2012.3.13": "·".join(f"{m}조" for m in o12),
                         "같은제목_장절(기계)": " / ".join(sorted(set(u16 + u12)))})
            if co == "iM금융지주" and reg.startswith("리스크관리규정("):
                c, t = SIM_IM.get(n, ("-", ""))
                base["뜻같은다른제목(판단)"] = f"({c}) {t}" if c != "-" else (t and f"(기계 일치) {t}")
        else:
            m2 = re.match(r"제(\d+)조(의\d+)?", no)
            if m2 and m2.group(2) and not title_missing:
                s16, r16, o16, u16 = mob.cmp(title, 0, "16")
                s12, r12, o12, u12 = mob.cmp(title, 0, "12")
                base.update({"구분": "조(「제N조의M」 꼴)", "기계비교_2016.8.1": R3_WORDS[1][1],
                             "같은제목_다른번호_2016.8.1": "·".join(f"{m}조" for m in o16),
                             "기계비교_2012.3.13": R3_WORDS[2][1],
                             "같은제목_다른번호_2012.3.13": "·".join(f"{m}조" for m in o12),
                             "같은제목_장절(기계)": " / ".join(sorted(set(u16 + u12)))})
            else:
                base["구분"] = "인용 조·항 — 조 제목 추출 범위에 없음(기계 비교 불가)"
                if m2:
                    n = int(m2.group(1))
                    base["모범_같은번호_제목_2016.8.1"] = f"{n}조 {mob.title(n, '16')}" if mob.title(n, "16") else ""
                    base["모범_같은번호_제목_2012.3.13"] = f"{n}조 {mob.title(n, '12')}" if mob.title(n, "12") else ""
                    base["기계비교_2016.8.1"] = base["기계비교_2012.3.13"] = "비교 불가"
                elif "장" in no:
                    base["기계비교_2016.8.1"] = base["기계비교_2012.3.13"] = "비교 불가(장 인용 — C-2)"
        base["모범규준_조_표지(R2)"] = r2_label(mob, co, reg, no)
        out.append(base)
    return out


def r2_label(mob, co, reg, no):
    """조번호대조 CSV 의 조 번호 칸(R2) — 조문 대조 자료는 「9-4 조문 대조(대조표 A~C)」, 지시서 9-4-1 조(iM 28·30, 메리츠 9·57)는
    그 조 번호 그대로, 메리츠 그룹리스크관리규정의 그 밖 인용 조(6·58)는 같은 번호 조 (판단)."""
    m = re.match(r"제(\d+)조", no or "")
    n = int(m.group(1)) if m else None
    if co == "iM금융지주" and reg.startswith("리스크관리규정(") and n in LISTED_CO and co in LISTED_CO[n] and re.fullmatch(r"제\d+조", no):
        return f"{TOCLAB} — {n}조({mob.title(n, '16')})(지시서 9-4 1. 조 번호 그대로)"
    if co == "메리츠금융지주" and reg == "그룹리스크관리규정" and n:
        if n in LISTED_CO and co in LISTED_CO[n]:
            return f"{TOCLAB} — {n}조({mob.title(n, '16')})(지시서 9-4 1. 조 번호 그대로)"
        return f"{TOCLAB} — {n}조({mob.title(n, '16')})(판단)"
    return TOCLAB


def reg_summary(maprows):
    """규정별 기계 비교 통계(조 단위 행만)."""
    by = {}
    for r in maprows:
        if r["구분"] not in ("조", "본칙 조", "조(「제N조의M」 꼴)", "인용 조·항 — 조 제목 추출 범위에 없음(기계 비교 불가)"):
            continue
        k = (r["회사"], r["규정명"])
        s = by.setdefault(k, {"n": 0, "same16": [], "same12": [], "other16": [], "other12": [], "none": 0, "na": 0})
        s["n"] += 1
        if r["구분"].startswith("인용 조·항"):
            s["na"] += 1
            continue
        hit = False
        if r["기계비교_2016.8.1"] == "같음":
            s["same16"].append(f"{r['회사_조']}({r['회사_조제목(원문)']})")
            hit = True
        if r["기계비교_2012.3.13"] == "같음":
            s["same12"].append(f"{r['회사_조']}({r['회사_조제목(원문)']})")
            hit = True
        if r["같은제목_다른번호_2016.8.1"] and r["기계비교_2016.8.1"] != "같음":
            s["other16"].append(f"{r['회사_조']}({r['회사_조제목(원문)']})→{r['같은제목_다른번호_2016.8.1']}(2016.8.1)")
            hit = True
        if r["같은제목_다른번호_2012.3.13"] and r["기계비교_2012.3.13"] != "같음":
            s["other12"].append(f"{r['회사_조']}({r['회사_조제목(원문)']})→{r['같은제목_다른번호_2012.3.13']}(2012.3.13)")
            hit = True
        if not hit:
            s["none"] += 1
    return by


# ───────────────────────────── D. 행렬
def listed(n, co):
    return n in LISTED_ALL or co in LISTED_CO.get(n, [])


CATS = ["받은 글", "일부", "추출 범위에 없음", "(판단)", "9-4 검색 범위 밖"]


def d_summary(D):
    tot = {k: sum(D["counts"][co][k] for co in COS) for k in CATS}
    nl = sum(tot[k] for k in CATS[:3])
    return (f"| D. 행렬 56행 × 8개사 = 448칸 | 지시서 조 칸 {nl}(9-4-2·9-4-3 조 11 × 8개사 = 88 + 9-4-1 iM 28·30·메리츠 9·57 = 4): "
            + " · ".join(f"{k} {tot[k]}" for k in CATS[:3]) + f" — 상태 CSV·회사 md 와 같음(R1) / 그 밖의 조: (판단) {tot['(판단)']} · 9-4 검색 범위 밖 {tot['9-4 검색 범위 밖']} |")


def build_matrix(mob, ST, DT, ev, B, iMrows):
    """D 행렬 — 지시서 조 칸 = 상태 CSV 「상태」 글자 그대로(R1), 9-4-1 칸 = 회사 md 지시서 항목 대조 표 「9-4 1.」 행 상태,
    그 밖의 조 = 회사 md·CSV 의 판단 자리((판단)) 또는 「9-4 검색 범위 밖」."""
    rows = []
    counts = {co: dict.fromkeys(CATS, 0) for co in COS}
    bq = {}
    for b in B:
        bq.setdefault(b["key"][0], [])
        for c in b["cites"]:
            if c["qid"] not in bq[b["key"][0]]:
                bq[b["key"][0]].append(c["qid"])
    for n in range(3, 59):
        r = mob.rows[n]
        row = {"조": n, "장": r["장"], "절": r["절"], "제목_2016.8.1판": r["제목_2016.8.1판"],
               "제목_2012.3.13제정판": r["제목_2012.3.13제정판"],
               "지시서9-4조사조": ("Y" if n in LISTED_ALL else ("Y(" + "·".join(SHORT[c] for c in LISTED_CO[n]) + " 항목)" if n in LISTED_CO else "N"))}
        for co in COS:
            if n in LISTED_ALL:
                s = ST[(co, n)]
                txt = s["상태"]
                ptr = cite_ptr(s["근거"])
                if r1_kind(txt) == "추출 범위에 없음" and s["찾은_방법"] not in ("", "-"):
                    fm = s["찾은_방법"]
                    ptr = (ptr + "; " if ptr else "") + "찾은 방법: " + (fm if len(fm) <= 80 else fm[:79] + "…")
                lab = DT[co][n][1]
                src = (f"상태 CSV `{os.path.basename(s['_file'])}` ({co}·{n}조 행 「상태」·「근거」 열) = 회사 md 0장 판정 칸 = "
                       f"지시서 항목 대조 표 「{lab}」 행 상태 칸")
                k = r1_kind(txt)
            elif co in LISTED_CO.get(n, []):
                txt, lab = DT[co][n]
                if co == "iM금융지주":
                    rr = next(x for x in iMrows if x["no"] == f"제{n}조")
                    ptr = f"대조표 A(iM 제{n}조 「{rr['title']}」, 연차 {rr['page']}; [I-11])"
                else:
                    qs = sorted(bq.get(n, []), key=lambda q: int(re.sub(r"\D", "", q) or 0))
                    ptr =f"대조표 B(그룹리스크관리규정 제{n}조 인용, " + "·".join(f"[{q}]" for q in qs) + ")"
                src = f"회사 md 지시서 항목 대조 표 「{lab}」 행 상태 칸 = 0장 판정 칸; 조 대조는 이 파일 {'A' if co == 'iM금융지주' else 'B'}"
                k = r1_kind(txt)
            elif ev[co].get(n):
                items = ev[co][n]
                txt = "(판단) " + "; ".join(items[:2]) + (f" 외 {len(items) - 2}" if len(items) > 2 else "")
                ptr = ""
                src = "회사 md 인용 태그·대응표·CSV 판단 칸(판단)"
                k = "(판단)"
            else:
                txt, ptr, src, k = "9-4 검색 범위 밖", "", "-", "9-4 검색 범위 밖"
            if k is None:
                raise SystemExit(f"[web13_compare] D {n}조 {co} 칸 「{txt}」 이 R1 세 단계가 아님")
            counts[co][k] += 1
            row[SHORT[co]] = txt
            row[SHORT[co] + "_인용"] = ptr
            row[SHORT[co] + "_근거"] = src
        rows.append(row)
    return rows, counts


def mcell(row, co):
    """md D 칸 = 상태(또는 안내) + 「 — 」 + 인용 자리."""
    t, p_ = row[SHORT[co]], row[SHORT[co] + "_인용"]
    return f"{t} — {p_}" if p_ else t


# ───────────────────────────── 정합성 보정 기록(전·후)
def ensure_pre():
    """기준 사본(커밋 496ddc4 의 산출물 3개) — 없으면 git show 로 만듦. 언제나 이 사본과 견줘 전·후를 적음(멱등)."""
    os.makedirs(PRE_DIR, exist_ok=True)
    out = {}
    for rel in (OUT_MD, OUT_MATRIX, OUT_MAP):
        dst = os.path.join(PRE_DIR, os.path.basename(rel))
        if not os.path.exists(dst):
            data = subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
            with open(dst, "wb") as f:
                f.write(data)
        out[rel] = dst
    return out


def head_of(s):
    """1차 판 D 칸의 머리말(「 — 」·「 (」 앞)."""
    return re.split(r" — | \(", s or "", maxsplit=1)[0].strip()


def fix_record(mob, D, maprows, inputs):
    pre = ensure_pre()
    pmd = open(pre[OUT_MD], encoding="utf-8").read()
    pL = pmd.split("\n")
    with open(pre[OUT_MATRIX], encoding="utf-8-sig") as f:
        pmat = {int(r["조"]): r for r in csv.DictReader(f)}
    with open(pre[OUT_MAP], encoding="utf-8-sig") as f:
        pmap = list(csv.DictReader(f))
    rec = {"pre_dir": PRE_DIR}
    rec["date_before"] = next(l for l in pL if l.startswith("- 작성일:"))
    rec["d_before"] = next(l for l in pL if l.startswith("| D. 행렬")).strip().strip("|").split(" | ")[1].strip()
    # 지시서 조 칸 전·후
    cells = []
    for r in D["rows"]:
        n = r["조"]
        for co in COS:
            if n in LISTED_ALL or co in LISTED_CO.get(n, []):
                b = pmat[n][SHORT[co]]
                cells.append((n, SHORT[co], head_of(b), b, r[SHORT[co]]))
    rec["cells"] = cells
    rec["listed_before"] = {n: pmat[n]["지시서9-4조사조"] for n in pmat}
    # 출처 줄 날짜 라벨
    rec["mob_cite_before"] = sorted(set(re.findall(r"수집 2026-10-0\d\([^)]*\)", pmd)))
    rec["cite_date_before"] = len(re.findall(r"옮김 2026-10-07\]", pmd))
    # 태그 줄(R2)
    ptags = [l for l in pL if l.startswith("- 이 글이 닿는 모범규준 조")]
    rec["tags_before"] = ptags
    # 조번호대조 CSV 열별 바뀐 행
    rec["map_n"] = (len(pmap), len(maprows))
    rec["map_cols_before"] = list(pmap[0].keys()) if pmap else []
    diffc = {}
    if len(pmap) == len(maprows):
        for a, b in zip(pmap, maprows):
            for k in a:
                if a[k] != b.get(k, ""):
                    diffc[k] = diffc.get(k, 0) + 1
    rec["map_diff"] = diffc
    # 입력 sha256 — 1차 판 표(앞 16자)와 견줌
    pin = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{16})` \|$", pmd, re.M))
    rec["inputs_changed"] = [(rel, pin.get(rel, "(1차 판 입력 아님)"), h[:16]) for rel, h in inputs if pin.get(rel) != h[:16]]
    rec["inputs_n"] = (len(pin), len(inputs))
    # R3 낱말 — 1차 판(md·CSV)에 「전」 글이 몇 번 있었는지
    pmapt = open(pre[OUT_MAP], encoding="utf-8-sig").read()
    rec["r3"] = [(a, b, pmd.count(a) + pmapt.count(a)) for a, b in R3_WORDS]
    rec["cats_before"] = [" / ".join(x.strip() for x in l.strip().strip("|").split("|")[1:]) for l in pL if l.startswith("| 회사 | 찾은 글")]
    return rec


def write_fix_record(w, rec, D, mob):
    w("## 검증 기록")
    w("")
    w("- 대조 스크립트: `scripts/dart/verify13_compare.py`(인자 없이 → 문제 0 이면 exit 0, 아니면 1; 결과 `dart_out/risk13/verify13_compare.txt` 를 실행마다 다시 씀). "
      "① D 행렬 모든 칸 = 상태 CSV = 회사 md 0장 판정·지시서 항목 대조 표, 그 밖의 칸 꼴(R1·R2) ② 대조표 A~C 의 조 번호·제목 = 회사 조문목차 CSV·`dart_out/risk13/모범규준_조목록.csv`(기계 비교 다시 셈) "
      "③ 대조표의 모든 원문 인용(코드 블록 줄·표 안 「」 발췌)이 회사 md·모범규준 원문 md 에 공백 무시로 글자 그대로(회사 인용은 원본 텍스트 `dart_out/text/risk8|risk9` 쪽에도 찾아 봄) "
      "④ 입력 sha256 표 = 지금 파일 ⑤ API 키·OC 값 문자열 0건 ⑥ R3·R5 낱말(우리 글의 「없음」 단정 0건, 1차 판 작성일 라벨(2026-10-07) 0건)·R2 태그 줄·이 절 꼴.")
    w("- 이 파일·행렬 CSV·조번호대조 CSV 는 `scripts/dart/web13_compare.py` 가 만들고 verify13_compare.py 는 읽기만 함. "
      "재생성 순서: (회사 md·상태 CSV) verify13_g_*.py fix → fix13_A.py·fix13_B.py → `web13_compare.py` → `verify13_compare.py`.")
    w("")
    w("### 정합성 보정(2026-10-08)")
    w("")
    w(f"13차 정합성 보정 규칙 R1~R5(비평 `dart_out/risk13/critic13.json` gaps[1]·contradictions[1]·[5] 대응). 기준 사본(전) = 커밋 {BASE} 의 이 파일·행렬 CSV·조번호대조 CSV(`{rec['pre_dir']}/`). 원문 인용(코드 블록)은 고치지 않았고 다시 옮김(회사 md·모범규준 원문 md 의 인용 줄 그대로 — ③ 대조).")
    w("")
    w("| 규칙 | 곳 | 전(커밋 " + BASE + ") | 후 |")
    w("|---|---|---|---|")
    w(f"| R5 | 머리 작성일 | {cell(rec['date_before'][:120])}… | {cell('- 작성일: ' + DATE + ' — 1차 작성 2026-10-08(KST)(스크립트 실행 ' + FIRST_RUN + ') …')} |")
    mob_after = sorted(set(re.findall(r"수집 2026-10-0\d\([^)]*\)", mob.e16["cite"] + mob.e12["cite"])))
    w(f"| R5 | 모범규준 원문 출처 줄(머리·A-3·B·C-2) | {cell(' / '.join(rec['mob_cite_before']))} | {cell(' / '.join(mob_after))} — 모범규준 원문 md 의 정합성 보정 라벨을 그대로 옮김 |")
    w(f"| R5 | 회사 인용 출처 줄(A-3·B·C-2) | 「옮김 2026-10-07]」 {rec['cite_date_before']}곳 | 회사 md 의 정합성 보정 라벨(「옮김 2026-10-07~08(KST)」) 그대로 |")
    w(f"| R1 | D 행렬 요약(요약 표 D 행) | {cell(rec['d_before'])} | " + cell(d_summary(D).strip().strip("|").split(" | ")[1].strip()) + " |")
    w(f"| R1 | D 행렬 범주 표 | {cell(' '.join(rec['cats_before']))} | 「찾은 글」·「찾은 글*」·「일부*」(기계 분류)·「인용 조문만」·「요약 표 행 없음」 범주를 뺌 — 받은 글 / 일부 / 추출 범위에 없음 / (판단) / 9-4 검색 범위 밖 |")
    w(f"| R1 | D 행렬 9조 「9-4 조사」 칸 | {rec['listed_before'].get(9)} | {next(r for r in D['rows'] if r['조'] == 9)['지시서9-4조사조']}(지시서 「메리츠 그룹리스크관리규정 9조 7항」) |")
    w(f"| R1 | C-1 표 | 칸 4개(찾은 방법만) | 「상태(회사 md 「9-4 1.」 행 상태 칸 그대로 — R1)」 칸을 더함 |")
    w(f"| R2 | 태그 줄(A-3 iM 조 머리 줄, B 메리츠 인용, C-2 한국투자 장 인용) | 「이 글이 닿는 모범규준 조」 줄에 조 번호만 | 앞에 「9-4 조문 대조(대조표 A/B/C-2)」 — 지시서 조(28·30·9·57·34)는 그대로, 그 밖(11·29·6·58조, 제2·3장)은 (판단) |")
    newcols = [c for c in MAP_COLS if c not in rec["map_cols_before"]]
    w(f"| R2 | 조번호대조 CSV | 열 {len(rec['map_cols_before'])}개, 행 {rec['map_n'][0]} | 열 {len(MAP_COLS)}개(새 열 {', '.join(newcols) or '-'}), 행 {rec['map_n'][1]}; 행마다 바뀐 칸 수(열별) {cell(json.dumps(rec['map_diff'], ensure_ascii=False))} — 「회사산출물_대응판단(그대로)」는 회사 조문목차 CSV 비고 칸(그룹 A·B 보정의 날짜·「없음」 낱말)을 그대로 따름 |")
    w("| R2 | 받은 것 표 「모범규준 조」 칸 | 조 번호만 | 지시서 조는 그대로, 그 밖은 (판단), 조문 대조 자료는 「9-4 조문 대조(대조표 …)」 |")
    for a, b, k in rec["r3"]:
        w(f"| R3 | 우리 글 | {cell(a)} ({k}곳) | {cell(b)} |")
    w(f"| ④ | 입력 sha256 표 | 입력 {rec['inputs_n'][0]}개, 앞 16자 | 입력 {rec['inputs_n'][1]}개(상태 CSV 2개 더함), 64자 전부 |")
    w("")
    w("입력 가운데 1차 판 뒤 바뀐 파일(sha256 앞 16자 전 → 후 — 그룹 A·B 와 모범규준 원문 정합성 보정):")
    w("")
    for rel, a, b in rec["inputs_changed"]:
        w(f"- `{rel}`: `{a}` → `{b}`")
    w("")
    w("D 행렬 지시서 조 칸 전·후(전 = 1차 판 칸 머리말, 후 = 상태 CSV·회사 md 상태 그대로):")
    w("")
    w("| 조 | 회사 | 전 | 후 |")
    w("|---|---|---|---|")
    for n, co, hb, b, a in rec["cells"]:
        w(f"| {n} | {co} | {cell(hb)} | {cell(a)} |")
    w("")
    def cat0(h):
        return {"찾은 글*": "찾은 글", "일부*": "일부"}.get(h, h)
    trans = {}
    for n, co, hb, b, a in rec["cells"]:
        trans.setdefault((cat0(hb), r1_kind(a)), []).append(f"{n}{co}")
    w("범주 옮김(전 범주 → 후 R1 범주: 칸 수 — 조·회사): " + "; ".join(
        f"{x} → {y}: {len(v)}칸({', '.join(v)})" for (x, y), v in sorted(trans.items(), key=lambda t: (-len(t[1]), t[0]))))
    w("")
    ch = sum(1 for (x, y), v in trans.items() if x != y for _ in v)
    w(f"note: 지시서 조 칸 {len(rec['cells'])}개 가운데 범주가 바뀐 칸 {ch}개(나머지는 범주는 같고 빠진 핵심을 괄호로 적음). 「전」의 「찾은 글」은 1차 판이 회사 md 0장 판정 칸 머리말(메리츠·한국투자·iM·NH)이나 요지 칸 낱말 기계 분류(「찾은 글*」·「일부*」, KB·신한·하나·우리)를 옮긴 것 — 비평 contradictions[1](22조 8개사 「찾은 글(*)」 ↔ 회사 md 「연결 측정 여부 추출 범위에 없음」)의 원인. 「후」는 그룹 A·B 보정이 정한 R1 상태.")
    w("")


# ───────────────────────────── md 쓰기
def code(lines):
    return ["```text"] + list(lines) + ["```"]


def write_md(mob, A, B, C, D, inputs, maprows, regsum, rec):
    o = []
    w = o.append
    w("# 9-4 모범규준 대조표 — 회사 규정 조 번호·제목 ↔ 「금융지주회사 통합위험관리 모범규준」")
    w("")
    w(f"- 작성일: {DATE} — 1차 작성 2026-10-08(KST)(스크립트 실행 {FIRST_RUN}, 커밋 {BASE}), 정합성 보정 재생성 2026-10-08(KST)(스크립트 실행 {now()}). "
      "**새로 받은 자료 0건(네트워크 요청 0건)** — 이미 만든 13차 산출물(모범규준 원문 md·조 목록 CSV, 8개사 조문 목차 CSV·회사 md, 지시서 항목 상태 CSV 2개)만 읽어 맞댐.")
    w("- 날짜 기준: 이 파일의 날짜는 KST. 옮겨 붙인 출처 줄의 수집·옮김 날짜는 각 원본 md 의 라벨 그대로(그 md 들의 정합성 보정 뒤 KST 라벨; 법제처·DART 원장은 UTC).")
    w("- 스크립트: `scripts/dart/web13_compare.py` (`python3 -I scripts/dart/web13_compare.py`), 대조 `scripts/dart/verify13_compare.py`(인자 없이 → exit 0/1, 결과 `dart_out/risk13/verify13_compare.txt`). 중간 기록(파싱 결과·점검·기준 사본 pre/): `dart_out/raw/web13/compare94/`.")
    w("- 산출: 이 파일, 행렬 CSV `dart_out/risk13/9-4_모범규준_대조표.csv`(모범규준 3~58조 × 8개사, 칸마다 인용·근거 열), 조 대조 CSV `dart_out/risk13/9-4_조번호대조.csv`(8개사 조문 목차 CSV 의 모든 행 ↔ 모범규준 같은 번호 조, 기계 비교, R2 조 번호 표지 열).")
    w("- 상태 표기(R1 세 단계 — 정합성 보정 2026-10-08 KST): 지시서 9-4-2·9-4-3 항목의 조(3·4·5·17·21·22·24·27·34·53·55)와 9-4-1 항목의 조(iM 28·30, 메리츠 9·57)는 「받은 글」(지시서 핵심이 모두 원문 인용으로 있음) / 「일부(있는 것, 빠진 핵심 추출 범위에 없음)」 / 「추출 범위에 없음」(+ 찾은 방법)만 씀. 「찾은 글」 낱말은 쓰지 않음.")
    w(f"- 조 번호 칸(R2): 조문 대조 자료(규정 조 목록·조 머리 줄)는 「{TOCLAB}」, 지시서에 적힌 조(위 R1 조)는 그대로, 그 밖의 조는 「(판단)」.")
    w("- 모범규준 원문(출처): " + MOB_MD + " 5장 2016.8.1 판 전문 " + mob.e16["cite"] + " / 6장 2012.3.13 제정판 전문 " + mob.e12["cite"] + " — 조 제목 목록 `dart_out/risk13/모범규준_조목록.csv`.")
    w("- 회사 원문(출처): 각 회사의 연차보고서·사업보고서·경영공시 글은 `handoff/13차_산출물/9-4_<회사>.md` 인용 블록에서 그대로 가져옴(문서명·URL 또는 접수번호·쪽·수집일은 인용마다 그 md 의 출처 줄을 그대로 붙임). 공시 원본 PDF 는 배포하지 않음.")
    w("- 방법: ① **기계 비교** — 조(장·절) 제목에서 공백과 가운뎃점(· ㆍ ∙ ・ ‧ • ･)을 지운 글자가 같으면 「같음」. 같은 번호 조와 견주고(2016.8.1 판·2012.3.13 제정판 따로), 모범규준 1~59조 전체와 장·절 제목 가운데 같은 제목이 있으면 그 번호를 적음. 장 제목의 「(2016.10.27 신설)」·「<삭제 …>」 꼴 표시는 떼고 견줌. ② **유사 판정** — 뜻이 같거나 비슷한 다른 제목은 이 작업의 판단으로 「(판단)」. ③ **행렬(D)** — 지시서 조 칸은 상태 CSV 두 개(`" + STATE_A + "`·`" + STATE_B + "`)의 「상태」 열을 글자 그대로 옮기고(회사 md 0장 판정 칸·지시서 항목 대조 표 상태 칸과 한 칸이라도 다르면 스크립트가 아무것도 쓰지 않고 멈춤), 9-4-1 칸은 회사 md 지시서 항목 대조 표 「9-4 1.」 행 상태, 지시서 9-4 조 목록 밖 조는 회사 md 의 인용 태그 줄·대응표(1-3)·CSV 판단 칸에 근거가 있을 때만 「(판단)」으로 채움.")
    w("- 한계: ① 회사 규정 전문을 가진 곳은 iM 리스크관리규정뿐 — 나머지는 위원회·협의회 규정 전문이나 인용된 조 번호만 있음(C). ② 기계 비교는 글자 비교라 뜻이 같은 다른 낱말(「리스크」/「위험」)은 「다름」으로 나옴 — 그래서 2012.3.13 제정판(「리스크」 낱말) 열을 함께 둠. 「일치 없음」은 기계 비교에서 같은 글자 제목을 찾지 못했다는 분류(모범규준 1~59조·장·절 제목 전체와 견줌)이며 자료가 없다는 단정이 아님. ③ 메리츠 첨부6 조 제목은 회사 md 가 추출 깨짐을 읽어 붙인 것(판단)이라 그 행의 기계 비교도 그 판단 위에 있음. ④ 「추출 범위에 없음」은 각 회사 md 의 검색 범위(그 md 6장·5장 검색 기록, 검증 기록)에서 찾지 못했다는 뜻이며 「없음」 단정이 아님.")
    w("- 원문 인용은 코드 블록(글자 그대로), 해설·판단은 블록 밖 「note:」 줄과 표의 「(판단)」 칸에만.")
    w("")
    w("### 입력 파일(읽은 판)")
    w("")
    w("| 입력 | sha256 |")
    w("|---|---|")
    for rel, h in inputs:
        w(f"| `{rel}` | `{h}` |")
    w("")
    # ── 요약
    st = A["stats"]
    w("## 요약")
    w("")
    w("| 대조 | 결과 |")
    w("|---|---|")
    w(f"| A. iM 리스크관리규정 본칙 35조 ↔ 모범규준 같은 번호 조(2016.8.1 판, 기계) | 번호·제목 일치 {len(st['c16']['번호·제목 일치'])} · 제목만 일치(번호 다름) {len(st['c16']['제목만 일치(번호 다름)'])} · 일치 없음 {len(st['c16']['일치 없음'])} |")
    w(f"| A. 같은 방식(2012.3.13 제정판, 기계) | 번호·제목 일치 {len(st['c12']['번호·제목 일치'])} · 제목만 일치 {len(st['c12']['제목만 일치(번호 다름)'])} · 일치 없음 {len(st['c12']['일치 없음'])} |")
    w(f"| A. 두 판 가운데 하나라도(기계) | 번호·제목 일치 {len(st['cany']['번호·제목 일치'])} · 제목만 일치 {len(st['cany']['제목만 일치(번호 다름)'])} · 일치 없음 {len(st['cany']['일치 없음'])} |")
    sim = A["simst"]
    w(f"| A. 2016.8.1 판과 기계 일치(같은 번호든 다른 번호든)가 없는 {35 - len(sim.get('-', []))}개 조의 유사 판정(판단) | 뜻이 같은 2016 판 제목 있음 {len(sim.get('같음', []))} · 뜻 비슷·닿음 {len(sim.get('비슷', []))} · 같은 뜻 제목 찾지 못함 {len(sim.get('못찾음', []))} |")
    w(f"| B. 메리츠 그룹리스크관리규정 인용 조 | {len(B)}개(" + ", ".join(f"제{b['key'][0]}조{(' ' + str(b['key'][1]) + '항') if b['key'][1] else ''}" for b in B) + ") — 메리츠 조 제목이 추출 범위에 없어 제목 기계 비교는 못 함; 같은 번호 조·항의 모범규준 원문을 나란히 둠 |")
    w("| C. 나머지 6개사 그룹리스크관리규정(대응 규정) | 6개사 모두 「규정 조문 목차 추출 범위에 없음」; 한국투자는 「제2장과 제3장」 장 인용 1건(C-2). 위원회·협의회 규정 등 조 번호·제목이 잡힌 규정은 같은 방식으로 기계 비교(C-3) |")
    w(d_summary(D))
    w("")
    # ── A
    w("## A. iM 리스크관리규정 전체 조 ↔ 모범규준 같은 번호 조")
    w("")
    c = A["chk"]
    w(f"규정: iM금융지주 「리스크관리규정」(연차보고서 첨부16 「리스크관리 규정」, p.275~289) — 조 목록은 `{csv_rel('iM금융지주')}`, 원문은 `{md_rel('iM금융지주')}` [I-11](md {c['I11_md줄']}행).")
    w("")
    w("note: 지시서의 「iM 그룹 리스크관리규정」은 이 「리스크관리규정」을 가리키는 것으로 봄 — 회사 md 1-1 note(「그룹 리스크관리규정」이라는 이름은 iM 연차보고서 본공시·추가공시, 사업보고서 원본·정정, 경영공시의 검색 범위에서 찾지 못함 — 회사 md 6장 「목차(규정명)」)를 따름(판단).")
    w(f"note: 조 머리 점검(기계) — [I-11] 인용 블록의 본칙 조 머리 {c['본칙_조머리']}개, 번호 1~35 연속={'예' if c['번호연속'] else '아니오'}, 회사 CSV 본칙 {c['CSV_본칙']}행과 제목 불일치 {len(c['CSV제목불일치'])}건; 블록 안 「삭제」 글자 {c['삭제글자']}건, 「제N조의M」 꼴 {c['조의꼴']}건 → 삭제 조·가지 조는 이 원문 범위(p.275~289)에서 찾지 못함. 부칙 조 머리 {c['부칙_조머리']}개(13건×3조, A-4).")
    w("")
    w("### A-1 대조표(본칙 35조)")
    w("")
    w("「같은 번호 조」 칸: 모범규준 같은 번호 조 제목 → 기계 비교. 「같은 제목의 다른 번호」 칸: 모범규준 1~59조 가운데 제목이 기계 일치하는 다른 조. 「장·절」 칸: 제목이 모범규준 장·절 제목과 기계 일치하는 곳. 마지막 칸만 판단.")
    w("")
    w("| iM 장 | iM 조 | iM 조 제목(원문) | 쪽 | 같은 번호 조(2016.8.1) → 기계 | 같은 제목의 다른 번호(2016.8.1) | 같은 번호 조(2012.3.13) → 기계 | 같은 제목의 다른 번호(2012.3.13) | 같은 제목의 모범규준 장·절(기계) | 분류(기계, 두 판) | 뜻이 같거나 비슷한 2016.8.1 판 제목(판단 — 2016 판 기계 일치가 없는 조만) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    last_ch = None
    for rr in A["rows"]:
        chs = rr["ch"].split(" ", 1)[0] if rr["ch"] != last_ch else "〃"
        last_ch = rr["ch"]
        b16 = f"{rr['n']}조 {rr['s16']} → **{rr['r16']}**" if rr["r16"] == "같음" else f"{rr['n']}조 {rr['s16']} → {rr['r16']}"
        b12 = f"{rr['n']}조 {rr['s12']} → **{rr['r12']}**" if rr["r12"] == "같음" else f"{rr['n']}조 {rr['s12']} → {rr['r12']}"
        o16 = "·".join(f"{m}조({mob.title(m, '16')})" for m in rr["o16"]) or "-"
        o12 = "·".join(f"{m}조({mob.title(m, '12')})" for m in rr["o12"]) or "-"
        un = " / ".join(sorted(set(rr["u16"] + rr["u12"]))) or "-"
        simc, simt = rr["sim"]
        simtxt = "-" if simc == "-" else f"(판단) {simt}"
        w(f"| {chs} | {rr['no']} | {cell(rr['title'])} | {rr['page']} | {cell(b16)} | {cell(o16)} | {cell(b12)} | {cell(o12)} | {cell(un)} | {rr['cany']} | {cell(simtxt)} |")
    w("")
    w("note: 「분류(기계, 두 판)」 — 두 판 가운데 더 가까운 쪽(번호·제목 일치 > 제목만 일치 > 일치 없음). 회사 md 1-2 의 「주제가 닿는 모범규준 조·항(판단)」은 조번호대조 CSV 의 「회사산출물_대응판단(그대로)」 열에 그대로 옮김.")
    w("")
    w("### A-2 통계")
    w("")
    w("| 기준 | 번호·제목 모두 일치 | 제목만 일치(번호 다름) | 일치 없음 | 합계 |")
    w("|---|---|---|---|---|")
    for key, lab in (("c16", "2016.8.1 판(기준판)"), ("c12", "2012.3.13 제정판"), ("cany", "두 판 가운데 하나라도")):
        s = st[key]
        fmt = lambda xs: f"{len(xs)}개 — " + ", ".join(f"제{x}조" for x in xs) if xs else "0개"
        w(f"| {lab} | {fmt(s['번호·제목 일치'])} | {fmt(s['제목만 일치(번호 다름)'])} | {len(s['일치 없음'])}개 | {sum(len(v) for v in s.values())} |")
    w("")
    lst = [f"제{rr['n']}조({rr['title']})→" + "·".join(f"{m}조" for m in rr["o16"]) for rr in A["rows"] if rr["c16"] == "제목만 일치(번호 다름)"]
    w("note: 2016.8.1 판 제목만 일치(번호 다름) — " + ", ".join(lst) + ".")
    lst = [f"제{rr['n']}조({rr['title']})→" + "·".join(f"{m}조" for m in rr["o12"]) for rr in A["rows"] if rr["c12"] == "제목만 일치(번호 다름)"]
    w("note: 2012.3.13 제정판 제목만 일치(번호 다름) — " + ", ".join(lst) + ".")
    w("note: 장·절 제목과 기계 일치 — " + (", ".join(f"제{n}조 → " + " / ".join(sorted(set(a + b))) for n, a, b in A["unit_hits"]) or "0건(기계)") + ".")
    w(f"note: (판단) 2016.8.1 판과 기계 일치(같은 번호든 다른 번호든)가 없는 조 가운데 뜻이 같은 2016 판 제목이 있는 조 {len(sim.get('같음', []))}개(" + ", ".join(f"제{x}조" for x in sim.get("같음", [])) +
      f"), 뜻이 비슷하거나 두 제목을 합친 꼴 {len(sim.get('비슷', []))}개(" + ", ".join(f"제{x}조" for x in sim.get("비슷", [])) +
      f"), 같은 뜻 제목을 찾지 못한 조 {len(sim.get('못찾음', []))}개(" + ", ".join(f"제{x}조" for x in sim.get("못찾음", [])) + ").")
    w("note: (판단) 번호까지 같고 제목이 같거나 뜻이 같은 조는 제1조(목적)·제28조·제29조·제30조·제34조, 주제가 같은 조로 넓히면 제33조까지(회사 md 1-2 와 같음) — 모두 iM 규정의 제8장·제10장(2016.10.27 신설)과 제1조. 지시서의 「28조(통합리스크관리시스템), 30조(적합성 검증)가 모범규준과 조 번호가 같음」은 번호로는 맞으나, 글자로는 제28조 「시스템 구축 및 운영」 ↔ 28조 「시스템 구축 및 관리」(한 낱말 다름), 제30조 「적합성 검증」 ↔ 30조 「목적」(「적합성 검증」은 모범규준 제4장 제4절 제목)이라 기계 비교로는 둘 다 「다름」.")
    w("note: (판단) iM 조 제목의 낱말은 대체로 2012.3.13 제정판(「리스크」)을 따름 — 기계 일치가 2012 판 쪽에서 더 많음(제5조·제7조·제26조·제34조). 다만 제13조 「그룹위험관리책임자」는 2016.8.1 판 11조 제목과만 일치하고, 원문 조 머리에 「(2016.10.27 개정)」 표시가 붙어 있음(A-3 인용).")
    w("")
    # A-3 원문
    w("### A-3 원문 — 판별에 쓴 조 머리 줄")
    w("")
    q11 = A["q11"]
    w(f"- 인용(iM): {q11['src'][len('- 인용: '):] if q11['src'].startswith('- 인용: ') else q11['src']} — 회사 md `{md_rel('iM금융지주')}` [I-11]")
    w(f"- 이 글이 닿는 모범규준 조(조 제목은 2016.8.1판): {TOCLAB.replace('A~C', 'A')} — 28조(시스템 구축 및 관리)·30조(목적)(지시서 9-4 1. 조 번호 그대로), 34조(해외위험 관리)(지시서 9-4 2. 조), 11조(그룹위험관리책임자)(판단), 29조(자료 수집 및 관리)(판단)")
    w("")
    sel = [13, 28, 29, 30, 34]
    o.extend(code([A["rows"][n - 1]["head"] for n in sel]))
    w("")
    w("note: 위 줄은 [I-11] 인용 블록에서 조 머리 줄만 골라 옮김(조 본문은 회사 md [I-11]). 「(2016.10.27 개정)」은 원문 표시.")
    w("")
    w(f"- 인용(모범규준 2016.8.1 판): {mob.e16['cite']} — `{MOB_MD}` 5장")
    w("- 이 글이 닿는 모범규준 조: 11조(그룹위험관리책임자), 28조(시스템 구축 및 관리), 29조(자료 수집 및 관리), 30조(목적)·제4장 제4절(적합성 검증), 34조(해외위험 관리)")
    w("")
    lines = []
    for n in [11, 28, 29, 30, 34]:      # iM 제13조 ↔ 모범규준 11조(같은 제목), 나머지는 같은 번호
        a = mob.e16["arts"][n]
        if n == 30:
            lines.append(next(l for l in rd(MOB_MD).split("\n")[mob.e16["range"][0]:mob.e16["range"][1]] if l.startswith("제4절")))
        lines.append(a["lines"][0])
    o.extend(code(lines))
    w("")
    w(f"- 인용(모범규준 2012.3.13 제정판): {mob.e12['cite']} — `{MOB_MD}` 6장")
    w("- 이 글이 닿는 모범규준 조: 11조(그룹위험관리책임자)·34조(해외위험 관리)(2012 판 제목은 「그룹리스크관리최고책임자」·「해외리스크 관리」)")
    w("")
    o.extend(code([mob.e12["arts"][11]["lines"][0], mob.e12["arts"][34]["lines"][0]]))
    w("")
    w("note: 2016.8.1 판 11조 머리 줄의 「<삭제 2016. 8. 1.>」은 ①항 내용 삭제 표시(모범규준 원문 md 3장 「①~⑤·⑦ 삭제 — ⑥·⑧·⑨ 존치」). 조 제목 「그룹위험관리책임자」는 남아 있음.")
    w("")
    # A-4 장·부칙
    w("### A-4 장 제목과 부칙 조(같은 방식, 참고)")
    w("")
    w("| iM 장 | iM 장 제목(원문) | 쪽 | 같은 번호 장(2016.8.1) → 기계 | 같은 번호 장(2012.3.13) → 기계 | 같은 제목의 모범규준 장·절·조(기계) |")
    w("|---|---|---|---|---|---|")
    for ch in A["chapters"]:
        b16 = f"제{ch['n']}장 {ch['s16']} → {ch['r16']}" if ch["s16"] else ch["r16"]
        b12 = f"제{ch['n']}장 {ch['s12']} → {ch['r12']}" if ch["s12"] else ch["r12"]
        oth = " / ".join([f"{x}(2016.8.1)" for x in ch["o16"]] + [f"{x}(2012.3.13)" for x in ch["o12"]] +
                         [f"{m}조 「{mob.title(m, '16')}」(2016.8.1)" for m in ch["a16"]] +
                         [f"{m}조 「{mob.title(m, '12')}」(2012.3.13)" for m in ch["a12"]]) or "-"
        w(f"| {ch['no']} | {cell(ch['title'])} | {ch['page']} | {cell(b16)} | {cell(b12)} | {cell(oth)} |")
    w("")
    bt = {}
    for r in A["buchik"]:
        k = re.sub(r"^부칙\(\d+/\d+\)\s*", "", r["조번호"])
        bt.setdefault((k, r["조제목"]), 0)
        bt[(k, r["조제목"])] += 1
    w("부칙: " + ", ".join(f"{k}({t}) {v}건" for (k, t), v in bt.items()) + " — 부칙 13건이 모두 같은 세 조 꼴(회사 md 1-2-1). 모범규준 본칙 같은 번호 조와는 대조 대상 아님(조번호대조 CSV 「구분」 열).")
    w("note: (참고, 기계) 모범규준 부칙(2012 제정)은 제1조(시행일)·제2조(적용례) 두 조(모범규준 원문 md 4장 「부칙」) — iM 부칙 제1조 「시행일」은 제목이 같고, 제2조 「자회사 등 리스크관리 관련 규정」은 다름.")
    w("")
    # ── B
    w("## B. 메리츠 그룹리스크관리규정 인용 조 ↔ 모범규준 같은 번호 조")
    w("")
    w(f"메리츠 「그룹리스크관리규정」 전문·조 제목은 추출 범위에 없음(찾은 범위: 회사 md `{md_rel('메리츠금융지주')}` 1-1 아래 note·6장 「목차(규정명)」 줄·검증 기록 「규정전문」 줄). 연차보고서 「그룹리스크관리위원회 회의 개최내역」 「※ 비 고」 칸에 인용된 조 번호만 있음 — 스크립트가 회사 md 인용 블록 [M-4]~[M-8] 의 줄에서 「그룹리스크관리규정 제N조(N항)」를 다시 셈.")
    w("")
    w("| 메리츠 인용(원문 표기) | 인용 횟수·자리(스크립트 셈) | 메리츠 인용 글(원문 발췌 — 줄바꿈·연속 공백만 한 칸으로, 원문 줄은 아래 B-절) | 모범규준 같은 번호 조 제목 2016.8.1 / 2012.3.13 | 모범규준 조 머리 줄 첫 문장(2016.8.1 원문 발췌) | 같은 번호 항(2016.8.1 원문, 기계 셈) | 제목 기계 비교 | 주제 대응(판단 — 회사 md 1-2-1 그대로) |")
    w("|---|---|---|---|---|---|---|---|")
    def place_str(cites):
        g = {}
        for c in cites:
            k = (c["meeting"].replace("제2025년도 ", ""), c["kind"], c["page"], c["qid"])
            g.setdefault(k, []).append(c["item"])
        return "; ".join(f"{m} {kd} {'·'.join(it)} {pg} [{q}]" for (m, kd, pg, q), it in g.items())

    for b in B:
        jo, hang = b["key"]
        lab = f"제{jo}조" + (f" {hang}항" if hang else "")
        exs = ["「" + re.sub(r"\s+", " ", t.strip()) + "」" for t, _ in b["texts"]]
        ex = " / ".join(exs[:2]) + (f" 외 {len(exs) - 2}가지(B-{jo}{('-' + str(hang)) if hang else ''})" if len(exs) > 2 else "")
        t16, t12 = mob.title(jo, "16"), mob.title(jo, "12")
        fs = first_sentence(b["a16"]["lines"][0])
        if hang:
            if b["same16"]:
                hs = "「" + b["same16"][0].strip() + "」"
            else:
                hs = f"{jo}조는 " + "".join(CIRC[k - 1] for k in b["h16"]) + f" {len(b['h16'])}개 항 — {CIRC[hang - 1]}항 줄 찾지 못함(전문 기계 셈)"
        else:
            hs = f"조 전체 인용 — {jo}조는 " + "".join(CIRC[k - 1] for k in b["h16"]) + " 항"
        w(f"| 그룹리스크관리규정 {lab} | {len(b['cites'])}회 — {cell(place_str(b['cites']))} | {cell(ex)} | {jo}조 {t16} / {jo}조 {t12} | 「{cell(fs)}」 | {cell(hs)} | {b['title_cmp']} | {cell(b['judg'].get('대응', '-'))} |")
    w("")
    w("note: 「자리」는 회의 차수(날짜)·안건 구분·항목 기호·쪽·회사 md 인용 번호. 쪽은 연차보고서 PDF 쪽(인쇄 쪽은 회사 md 인용 줄).")
    w("note: 제57조·제58조는 늘 한 줄에 「제57조, 제58조」로 함께, 「금융회사 지배구조에 관련 법률 감독규정 제8조」와 나란히 인용됨(원문 표기 그대로). 지시서의 「57조」는 원문 「제57조, 제58조」.")
    w("note: (판단) 같은 번호 조와 주제가 맞는 것은 제9조 6항·7항(모범규준 9조 ⑥ 결의사항·⑦ 보고사항), 일부 맞는 것은 제57조·제58조(위기상황분석·유동성 — 모범규준 56~58조 쪽), 맞지 않는 것은 제6조 5항(모범규준 6조는 ①~③항, 문서화) — 회사 md 1-2·1-2-1 판단과 같음.")
    w("")

    def mob_side(b):
        jo, hang = b["key"]
        w(f"- 인용(모범규준 2016.8.1 판): {mob.e16['cite']} — `{MOB_MD}` 5장 제{jo}조")
        w(f"- 이 글이 닿는 모범규준 조: {jo}조({mob.title(jo, '16')})")
        w("")
        if hang:
            body = [b["a16"]["lines"][0]] + ([f"[줄임: {jo}조 다른 항 — 원문은 {MOB_MD} 5장]"] if b["same16"] and hang != 1 else []) + (b["same16"] if hang != 1 else [])
        else:
            body = b["a16"]["lines"]
        o.extend(code(body))
        w("")
        if hang and not b["same16"]:
            w(f"note: 2016.8.1 판 제{jo}조는 " + "".join(CIRC[k - 1] for k in b["h16"]) + f" {len(b['h16'])}개 항(전문 기계 셈) — 메리츠 인용의 「{hang}항」에 해당하는 줄을 찾지 못함.")
            w("")
        if hang:
            body12 = [b["a12"]["lines"][0]] + ([f"[줄임: {jo}조 다른 항 — 원문은 {MOB_MD} 6장]"] if b["same12"] and hang != 1 else []) + (b["same12"] if hang != 1 else [])
            cmp_src = ([b["a16"]["lines"][0]] + b["same16"], [b["a12"]["lines"][0]] + b["same12"])
        else:
            body12 = b["a12"]["lines"]
            cmp_src = (b["a16"]["lines"], b["a12"]["lines"])
        if norm("".join(cmp_src[0])) == norm("".join(cmp_src[1])):
            w(f"note: 2012.3.13 제정판 제{jo}조(「{mob.title(jo, '12')}」) 같은 자리 글은 위 2016.8.1 판 글과 기계 비교로 같음(공백·가운뎃점 무시) — 되풀이하지 않음({mob.e12['cite'][:60]}… `{MOB_MD}` 6장).")
            w("")
        else:
            w(f"- 인용(모범규준 2012.3.13 제정판): {mob.e12['cite']} — `{MOB_MD}` 6장 제{jo}조")
            w(f"- 이 글이 닿는 모범규준 조: {jo}조({mob.title(jo, '16')}) — 2012 판 제목 「{mob.title(jo, '12')}」")
            w("")
            o.extend(code(body12))
            w("")
            w("note: 2012.3.13 제정판 같은 자리 글은 2016.8.1 판과 기계 비교로 다름(낱말 「리스크」/「위험」 등 — 회사 md 1-2-1 아래 note 는 메리츠 첨부6 낱말이 2012 판을 따른다고 봄(판단)).")
            w("")

    # 같은 인용 글을 공유하는 조(제57조·제58조)는 한 절로 묶음
    groups, i = [], 0
    while i < len(B):
        if (i + 1 < len(B) and [t for t, _ in B[i]["texts"]] == [t for t, _ in B[i + 1]["texts"]]):
            groups.append([B[i], B[i + 1]])
            i += 2
        else:
            groups.append([B[i]])
            i += 1
    for grp in groups:
        labs = [f"제{b['key'][0]}조" + (f" {b['key'][1]}항" if b["key"][1] else "") for b in grp]
        mobs = [f"제{b['key'][0]}조({mob.title(b['key'][0], '16')})" for b in grp]
        sid = "·".join(f"{b['key'][0]}{('-' + str(b['key'][1])) if b['key'][1] else ''}" for b in grp)
        w(f"### B-{sid} 메리츠 그룹리스크관리규정 {', '.join(labs)} ↔ 모범규준 {' · '.join(mobs)}")
        w("")
        b0 = grp[0]
        tags = TOCLAB.replace("A~C", "B") + " — " + ", ".join(
            f"{b['key'][0]}조({mob.title(b['key'][0], '16')})" + ("" if b["key"][0] in LISTED_CO and "메리츠금융지주" in LISTED_CO[b["key"][0]] else "(판단)")
            for b in grp)
        for t, c in b0["texts"]:
            src = c["src"][len("- 인용: "):] if c["src"].startswith("- 인용: ") else c["src"]
            same = [x for x in b0["cites"] if "\n".join(x["lines"]) == t]
            w(f"- 인용(메리츠): {src} — 회사 md `{md_rel('메리츠금융지주')}` [{c['qid']}] (같은 글 {len(same)}회: {place_str(same)})")
            w(f"- 이 글이 닿는 모범규준 조(조 제목은 2016.8.1판): {tags}")
            w("")
            o.extend(code(t.split("\n")))
            w("")
        for b in grp:
            mob_side(b)
    # ── C
    w("## C. 나머지 회사 규정 — 같은 방식")
    w("")
    w("### C-1 그룹리스크관리규정(대응 규정) 조문 목차 — 회사별")
    w("")
    w("| 회사 | 대응 규정 이름(원문) | 조 번호·제목 | 상태(회사 md 「지시서 항목별 대조」 표 「9-4 1.」 행 상태 칸 그대로 — R1) | 찾은 방법(같은 행 그대로) |")
    w("|---|---|---|---|---|")
    for co in ["한국투자금융지주", "KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]:
        info = C["status"][co]
        w(f"| {co} | {cell(info['names'])} | 규정 조문 목차 추출 범위에 없음 | {cell(info['state'])} | {cell(info['trail'])} |")
    w("")
    hits = C["cite_hits"]
    w("note: 그래서 iM(A) 같은 「전체 조 번호 ↔ 모범규준」 대조는 6개사 모두 하지 못함(대응 규정 조문 목차가 추출 범위에 없음). 메리츠(B)처럼 인용된 번호를 맞댈 수 있는 곳은 한국투자의 장(章) 인용 1건(C-2). "
      "스크립트 검색 — 6개사 회사 md 인용 블록(코드 블록 줄)에서 정규식 `" + CITE_RE.pattern + "`: " +
      ("; ".join(f"{SHORT[co]} [{q}] 「{t}」" for co, q, t in hits) if hits else "걸린 줄 0") +
      " — 한국투자 「리스크관리규정 제N조」는 자회사 한국투자증권 내규(회사 CSV 규정명 「리스크관리규정(한국투자증권 내규)」)라 그룹 규정 대조에서 뺌(조번호대조 CSV 에는 있음).")
    w("")
    w("### C-2 한국투자 그룹리스크관리규정 「제2장과 제3장」 ↔ 모범규준 같은 번호 장")
    w("")
    k = C["kis"]
    w(f"- 인용(한국투자): {k['src']} — 회사 md `{md_rel('한국투자금융지주')}` [{k['qid']}]")
    w(f"- 이 글이 닿는 모범규준 조(조 제목은 2016.8.1판): {TOCLAB.replace('A~C', 'C-2')} — 제2장 위험관리조직(7~13조)·제3장 금융지주회사와 자회사등의 위험관리 업무분장(14~17조)(판단)")
    w("")
    o.extend(code(k["lines"]))
    w("")
    w(f"- 인용(모범규준 2016.8.1 판·2012.3.13 제정판 장 머리 줄): `{MOB_MD}` 5장·6장 — {mob.e16['cite']} / {mob.e12['cite']}")
    w("- 이 글이 닿는 모범규준 조: 제2장(7~13조)·제3장(14~17조)")
    w("")
    o.extend(code(k["mob_lines"]))
    w("")
    w(f"note: 기계 — 한국투자 장 제목은 추출 범위에 없음(인용 글에 장 번호만) → 제목 비교 불가. 낱말 포함(기계, 공백 무시): 인용 글에 2012 판 제2장 제목 「{k['ch2_12']}」 포함={k['inc2_12']}, 2016 판 제2장 「{k['ch2_16']}」 포함={k['inc2_16']}, 「업무분장」(두 판 제3장 제목 끝 낱말) 포함={k['inc3']}.")
    w("note: (판단) 「제2장과 제3장에 규정된 금융지주 리스크관리조직 구조 및 업무 분장」은 모범규준 제2장(위험관리조직)·제3장(금융지주회사와 자회사등의 위험관리 업무분장)과 장 번호·주제가 같음 — 회사 md 1-2 판단과 같음. 조 번호는 추출 범위에 없음.")
    w("")
    w("### C-3 조 번호·제목이 잡힌 다른 규정(위원회·협의회 규정 등) — 기계 비교 요약")
    w("")
    w("8개사 조문 목차 CSV 의 행 가운데 iM 리스크관리규정(A)·메리츠 그룹리스크관리규정 인용(B)을 뺀 조 행. 행마다의 결과는 `dart_out/risk13/9-4_조번호대조.csv`.")
    w("")
    w("| 회사 | 규정(원문) | 대조한 조 | 번호·제목 일치 2016.8.1 | 번호·제목 일치 2012.3.13 | 제목만 일치(다른 번호) | 일치 없음 | 제목 추출 범위에 없음(비교 불가) |")
    w("|---|---|---|---|---|---|---|---|")
    for (co, reg), s in regsum.items():
        if co == "iM금융지주" and reg.startswith("리스크관리규정("):
            continue
        if co == "메리츠금융지주" and reg == "그룹리스크관리규정":
            continue
        oth = sorted(set(s["other16"] + s["other12"]))
        w(f"| {SHORT[co]} | {cell(reg)} | {s['n']} | {cell(', '.join(s['same16']) or '0')} | {cell(', '.join(s['same12']) or '0')} | {cell(', '.join(oth) or '0')} | {s['none']} | {s['na']} |")
    w("")
    w("note: (판단) 위원회·협의회 규정은 위원회 운영 규정이라 모범규준(그룹 위험관리 기준)과 조 번호 체계가 다름 — 번호·제목이 맞는 것은 「목적」·「정의」 같은 총칙 조뿐. 내용이 모범규준 9조 ⑥·⑦·12조 문구와 거의 같은 조(결의사항·보고사항·협의회 조)는 회사 CSV 의 판단 칸(조번호대조 CSV 「회사산출물_대응판단(그대로)」)에 있음.")
    w("note: 메리츠 첨부6 그룹리스크관리위원회규정 조 제목은 회사 md 가 추출 깨짐(「제 조 목적1 (」 꼴)을 읽어 붙인 판단 — 그 위의 기계 비교임. 회의록의 「그룹리스크위원회규정 제2조 2항·제10조 2항·제5조 4항」 인용은 조 제목이 없어 비교 불가(회사 md 는 제10조·제5조 인용이 첨부6 내용과 맞지 않는다고 적음).")
    w("")
    # ── D
    w("## D. 행렬 — 모범규준 3~58조 × 8개사")
    w("")
    w("칸 글은 상태와 짧은 안내이며 **원문은 각 회사 md**(인용 블록)에 있음. 「 — 」 뒤는 인용 자리([ID] = 회사 md 인용 번호, 「연차」=지배구조 및 보수체계 연차보고서, 「사업」=사업보고서).")
    w("")
    w(f"- 지시서 9-4-2·9-4-3 조(3·4·5·17·21·22·24·27·34·53·55) × 8개사 = 88칸: 「 — 」 앞은 상태 CSV(`{STATE_A}`·`{STATE_B}`) 「상태」 열 글자 그대로(R1 세 단계 — 받은 글 / 일부(있는 것, 빠진 핵심 추출 범위에 없음) / 추출 범위에 없음). 스크립트가 회사 md 0장 판정 칸·지시서 항목 대조 표(메리츠·한국투자·iM·NH 7장, KB·신한·하나·우리 6장) 상태 칸과 한 글자씩 맞대고, 한 칸이라도 다르면 멈춤. 「 — 」 뒤는 상태 CSV 「근거」 열의 인용 번호·쪽 앞 세 개.")
    w("- 9-4-1 칸(iM 28·30조, 메리츠 9·57조 — 지시서 「iM … 28조…, 30조…」·「메리츠 … 9조 7항, 57조」): 회사 md 지시서 항목 대조 표 「9-4 1. iM」·「9-4 1. 메리츠」 행 상태 칸(= 0장 판정 칸) 그대로, 「 — 」 뒤는 이 파일의 조 대조 자리(A·B).")
    w("- 「(판단) …」: 지시서 9-4 조 목록 밖 조(또는 그 회사 항목이 아닌 9·28·30·57조) — 회사 md 에 근거가 있을 때만, 이 순서로 앞 두 개: 메리츠 md 1-2-1(인용 조 ↔ 같은 번호 조)·한국투자 md 1-2(장 인용), iM·메리츠·한국투자 md 1-3 대응표, 회사 md 인용의 「이 글이 닿는 모범규준 조」·「모범규준 조:」 태그 줄([ID] = 인용 번호), 하나·우리 CSV 「닿는모범규준조(판단)」 칸. 모두 회사 md·CSV 가 붙인 판단이며 이 칸은 그 자리만 가리킴(R2).")
    w("- 「9-4 검색 범위 밖」: 지시서 9-4 가 그 회사에 조사하라고 한 조(3·4·5·17·21·22·24·27·34·53·55, iM 28·30, 메리츠 9·57)가 아니고, 스크립트가 본 회사 md 의 표·인용 태그·CSV 판단 칸에서도 그 조를 가리키는 자리를 찾지 못함 — 찾지 않은 것이며 「없음」 단정 아님.")
    w("")
    w("| 조 | 조 제목(2016.8.1) | 9-4 조사 | " + " | ".join(SHORT[c] for c in COS) + " |")
    w("|---|---|---|" + "---|" * len(COS))
    for r in D["rows"]:
        w(f"| {r['조']} | {cell(r['제목_2016.8.1판'])} | {r['지시서9-4조사조']} | " + " | ".join(cell(mcell(r, c)) for c in COS) + " |")
    w("")
    w("| 회사 | " + " | ".join(CATS) + " | 합계 |")
    w("|---|---|---|---|---|---|---|")
    for co in COS:
        cc = D["counts"][co]
        w(f"| {SHORT[co]} | " + " | ".join(str(cc[k]) for k in CATS) + f" | {sum(cc.values())} |")
    tot = {k: sum(D["counts"][co][k] for co in COS) for k in CATS}
    w("| 합계 | " + " | ".join(str(tot[k]) for k in CATS) + f" | {sum(tot.values())} |")
    w("")
    # 조별 R1 상태 모음(지시서 조) — 같은 상태 글을 쓰는 회사 수
    w("조별 상태 모음(지시서 9-4-2·9-4-3 조 — 상태 CSV 그대로, 회사 수):")
    w("")
    w("| 조 | 받은 글 | 일부 | 추출 범위에 없음 | 일부 칸의 빠진 핵심(상태 괄호 안 「… 추출 범위에 없음」 그대로, 회사) |")
    w("|---|---|---|---|---|")
    for n in LISTED_ALL:
        r = next(x for x in D["rows"] if x["조"] == n)
        ks = {k: [SHORT[c] for c in COS if r1_kind(r[SHORT[c]]) == k] for k in CATS[:3]}
        miss = {}
        for c in COS:
            s = r[SHORT[c]]
            if r1_kind(s) == "일부":
                mm = re.search(r",\s*([^,]*?추출 범위에 없음)\)$", s)
                miss.setdefault(mm.group(1) if mm else s, []).append(SHORT[c])
        w(f"| {n} | {len(ks['받은 글'])}" + (f"({'·'.join(ks['받은 글'])})" if ks["받은 글"] else "") +
          f" | {len(ks['일부'])} | {len(ks['추출 범위에 없음'])}" + (f"({'·'.join(ks['추출 범위에 없음'])})" if ks["추출 범위에 없음"] else "") +
          " | " + cell("; ".join(f"{k}({'·'.join(v)})" for k, v in miss.items()) or "-") + " |")
    w("")
    rel = []
    for n in (21, 22, 24):
        r = next(x for x in D["rows"] if x["조"] == n)
        nf = [SHORT[c] for c in COS if "연결 측정 여부 추출 범위에 없음" in r[SHORT[c]]]
        gt = [SHORT[c] for c in COS if r[SHORT[c]] == "받은 글"]
        rel.append(f"{n}조 — 연결 측정 여부 추출 범위에 없음 {len(nf)}개사({'·'.join(nf) or '-'}), 받은 글 {len(gt)}개사({'·'.join(gt) or '-'})")
    w("note: 21·22·24조(상태 CSV 그대로): " + "; ".join(rel) + ". 「받은 글」 칸의 연결 측정 근거를 어떻게 읽었는지는 상태 CSV 「있는_핵심」·「비고」 열과 회사 md 3장 note(판단 표시 포함)에 있음. "
      "1차 판(커밋 " + BASE + ")의 「찾은 글(*)」 칸은 이 상태로 바뀜(맨 끝 「검증 기록」 → 「정합성 보정(2026-10-08)」 소절).")
    w("")
    # ── 받은 것 등
    w("## 받은 것 / 받지 못한 것 / 원문과 다른 것")
    w("")
    w("| 구분 | 항목 | 모범규준 조 | 내용 |")
    w("|---|---|---|---|")
    for g in C["got_rows"]:
        w("| " + " | ".join(cell(x) for x in g) + " |")
    w("")
    w("## 대조 기록(스크립트 점검)")
    w("")
    for l in LOG:
        w(f"- {l}")
    w("")
    write_fix_record(w, rec, D, mob)
    with open(p(OUT_MD), "w", encoding="utf-8") as f:
        f.write("\n".join(o) + "\n")


# ───────────────────────────── main
def main():
    os.chdir(ROOT)
    rawd = os.path.join(RAW, TASK)
    os.makedirs(rawd, exist_ok=True)
    mob = Mob()
    inputs = [(MOB_MD, sha(MOB_MD)), (MOB_CSV, sha(MOB_CSV)), (STATE_A, sha(STATE_A)), (STATE_B, sha(STATE_B))]
    ST = load_status()
    Ls, CSVs, QB, S0, EV, DT = {}, {}, {}, {}, {}, {}
    for co in COS:
        Ls[co] = rd(md_rel(co)).split("\n")
        CSVs[co] = rcsv(csv_rel(co))
        inputs += [(csv_rel(co), sha(csv_rel(co))), (md_rel(co), sha(md_rel(co)))]
        QB[co] = quote_blocks(Ls[co])
        S0[co] = section0(co, Ls[co])
        DT[co] = directive_table(co, Ls[co])
        EV[co] = evidence(co, Ls[co], QB[co], CSVs[co])
        log(f"{co}: 0장 요약 표 조 {sorted(S0[co])}, 지시서 항목 대조 표 조 {sorted(DT[co])}, 인용 블록 {len(QB[co])}개(태그 줄 있음 {sum(1 for q in QB[co] if q['tag'])}), 조문 목차 CSV {len(CSVs[co])}행")
    # R1 — 상태 CSV ↔ 회사 md(0장 판정 칸·지시서 항목 대조 표) 한 칸이라도 다르면 아무것도 쓰지 않고 멈춤
    bad = status_mismatch(ST, S0, DT)
    if bad:
        print(f"[web13_compare] 상태 CSV ↔ 회사 md 다른 칸 {len(bad)}개 — 산출물을 쓰지 않고 멈춤:")
        for x in bad:
            print("  ✗", x[:300])
        sys.exit(1)
    log(f"R1 점검: 상태 CSV {len(ST)}칸(8개사 × 지시서 조 {len(LISTED_ALL)}) = 회사 md 0장 판정 칸 = 지시서 항목 대조 표 상태 칸 — 다른 칸 0; "
        "9-4-1 칸 4개(iM 28·30, 메리츠 9·57) 0장 판정 칸 = 지시서 항목 대조 표 「9-4 1.」 행 — 다른 칸 0")
    A = part_a(mob, Ls["iM금융지주"], CSVs["iM금융지주"])
    B = part_b(mob, Ls["메리츠금융지주"], CSVs["메리츠금융지주"])

    # C: 회사별 대응 규정 상태
    status = {}
    for co in ["한국투자금융지주", "KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]:
        names = [f"{r['규정명']}({r['쪽']})" for r in CSVs[co]
                 if ("조문 목차 추출 범위에 없음" in r["조번호"] or r["조번호"] in ("-",)) and
                 re.search(r"(그룹\s*)?리스크관리규정$|그룹\s*리스크관리규정|^리스크관리규정$", r["규정명"]) and "한국투자증권" not in r["규정명"]]
        dr = directive_row(Ls[co])
        trail = next((x for x in dr if "찾은 방법" in x or "찾은 범위" in x), "") if dr else ""
        state = next((x for x in dr[1:] if r1_kind(x)), "") if dr else ""
        if not state:
            raise SystemExit(f"[web13_compare] {co} 지시서 항목 대조 「9-4 1.」 행에 R1 상태 칸이 없음")
        status[co] = {"names": "; ".join(dict.fromkeys(names)) or "-", "trail": trail, "state": state}
    # 한국투자 장 인용
    kis = None
    for q in QB["한국투자금융지주"]:
        for t, (ln, l) in enumerate(q["code"]):
            if "그룹리스크관리규정 제2장과 제3장" in l:
                lines = [l] + ([q["code"][t + 1][1]] if t + 1 < len(q["code"]) else [])
                src = q["src"][len("- 인용: "):] if q["src"].startswith("- 인용: ") else q["src"]
                kis = {"qid": q["id"], "src": src, "lines": lines}
                break
        if kis:
            break
    mlines = [l for l in rd(MOB_MD).split("\n")[mob.e16["range"][0]:mob.e16["range"][1]] if re.match(r"^제\s*[23]\s*장", l)]
    mlines += [l for l in rd(MOB_MD).split("\n")[mob.e12["range"][0]:mob.e12["range"][1]] if re.match(r"^제\s*[23]\s*장", l)]
    joined = norm("".join(kis["lines"]))
    kis.update({"mob_lines": mlines, "ch2_12": mob.chapter_title(2, "12"), "ch2_16": mob.chapter_title(2, "16"),
                "inc2_12": norm(mob.chapter_title(2, "12")) in joined, "inc2_16": norm(mob.chapter_title(2, "16")) in joined,
                "inc3": "업무분장" in joined})
    log(f"C-2 점검: 한국투자 [{kis['qid']}] 「제2장과 제3장」 줄 찾음; 2012 제2장 제목 포함={kis['inc2_12']}, 2016 제2장 제목 포함={kis['inc2_16']}, 「업무분장」 포함={kis['inc3']}")

    # 조번호대조 CSV
    maprows = []
    for co in COS:
        maprows += map_rows(mob, co, CSVs[co], A)
    regsum = reg_summary(maprows)

    # D 행렬
    mrows, counts = build_matrix(mob, ST, DT, EV, B, A["rows"])
    mcols = ["조", "장", "절", "제목_2016.8.1판", "제목_2012.3.13제정판", "지시서9-4조사조"]
    for co in COS:
        mcols += [SHORT[co], SHORT[co] + "_인용", SHORT[co] + "_근거"]
    D = {"rows": mrows, "counts": counts}
    rec = fix_record(mob, D, maprows, inputs)
    write_csv(OUT_MAP, MAP_COLS, maprows)
    write_csv(OUT_MATRIX, mcols, mrows)

    # 받은 것 / 받지 못한 것 / 원문과 다른 것
    st = A["stats"]
    got_rows = [
        ["받은 것", "iM 리스크관리규정 본칙 35조·장 10개·부칙 39조 ↔ 모범규준 같은 번호 조(2016.8.1·2012.3.13) 기계 대조와 통계", TOCLAB.replace("A~C", "A") + " — 28·30조(지시서 9-4 1. 조 번호 그대로)", "A — 조번호대조 CSV iM 행"],
        ["받은 것", "메리츠 그룹리스크관리규정 인용 조 5개(제6조 5항·제9조 6항·제9조 7항·제57조·제58조) ↔ 모범규준 같은 번호 조 원문 나란히", TOCLAB.replace("A~C", "B") + " — 9·57조(지시서 그대로), 6·58조(판단)", "B"],
        ["받은 것", "한국투자 그룹리스크관리규정 「제2장과 제3장」 인용 ↔ 모범규준 제2·3장", TOCLAB.replace("A~C", "C-2") + " — 제2·3장(7~17조)(판단)", "C-2"],
        ["받은 것", "위원회·협의회 규정 등 조 번호·제목이 잡힌 규정의 기계 대조", TOCLAB.replace("A~C", "C-3"), "C-3 — 조번호대조 CSV"],
        ["받은 것", "행렬 3~58조 × 8개사 — 지시서 조 칸은 상태 CSV(R1) 그대로: " + d_summary(D).split(" | ")[1].split(" — ")[0], "3~58조(지시서 조는 그대로, 그 밖의 조 칸은 (판단))", "D — 행렬 CSV"],
        ["받지 못한 것", "KB·신한·하나·우리·NH·한국투자 그룹리스크관리규정(대응 규정) 조문 목차", TOCLAB.replace("A~C", "C-1"), "규정 조문 목차 추출 범위에 없음 — 상태·찾은 방법은 C-1 표(회사 md 「9-4 1.」 행)"],
        ["받지 못한 것", "메리츠 그룹리스크관리규정 조 제목(인용 조 5개 포함)", "9·57조(지시서 그대로), 6·58조(판단)", "추출 범위에 없음 — 제목 기계 비교 불가(회사 md 1-1 note·6장·검증 기록)"],
        ["받지 못한 것", "한국투자 그룹리스크관리규정 장 제목·조 번호", "제2·3장(판단)", "추출 범위에 없음(회사 md 1-2·6장)"],
        ["원문과 다른 것", "지시서 「28조(통합리스크관리시스템)」", "28조", "iM 원문 제28조 제목은 「시스템 구축 및 운영」(「통합리스크관리시스템」은 ① 본문 낱말, 회사 md 1-2 note) — 모범규준 28조 「시스템 구축 및 관리」와 기계 비교 「다름」(한 낱말)"],
        ["원문과 다른 것", "지시서 「30조(적합성 검증)」", "30조", "iM 제30조 제목 「적합성 검증」은 모범규준 30조 제목 「목적」과 다르고, 모범규준 제4장 제4절 제목 「적합성 검증」과 같음(기계)"],
        ["원문과 다른 것", "지시서 「메리츠 그룹리스크관리규정 9조 7항, 57조」", "9·57조", "원문은 「제9조 7항」(9회), 「제57조, 제58조」(늘 함께, 2회) — 그 밖에 「제9조 6항」(1회)·「제6조 5항」(2회)도 인용됨"],
        ["원문과 다른 것", "메리츠 「그룹리스크관리규정 제6조 5항」", "6조(판단)", "모범규준 6조(문서화)는 ①~③ 3개 항(전문 기계 셈) — 같은 번호 항이 맞지 않음"],
        ["원문과 다른 것", "iM 제34조 「해외리스크 관리」", "34조", "2016.8.1 판 34조 「해외위험 관리」와는 기계 「다름」, 2012.3.13 제정판 34조 「해외리스크 관리」와는 「같음」"],
        ["원문과 다른 것", "iM 제13조 「그룹위험관리책임자」(2016.10.27 개정)", "11조(판단)", "2016.8.1 판 11조 제목과 같고 2012 판 11조 「그룹리스크관리최고책임자」와 다름 — 번호는 두 칸 밀림"],
    ]
    cite_hits = []
    for co in ["한국투자금융지주", "KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]:
        for q in QB[co]:
            for ln, l in q["code"]:
                for m in CITE_RE.finditer(l):
                    t = (co, q["id"], m.group(0).strip())
                    if t not in cite_hits:
                        cite_hits.append(t)
    log("C-1 점검: 6개사 인용 블록의 그룹 위험관리 규정 조·장 인용 " + (", ".join(f"{SHORT[a]}[{b}] {c}" for a, b, c in cite_hits) or "0건"))
    C = {"status": status, "kis": kis, "got_rows": got_rows, "cite_hits": cite_hits}
    write_md(mob, A, B, C, D, inputs, maprows, regsum, rec)

    # 중간 기록
    dump = {"생성": now(), "section0": {co: S0[co] for co in COS}, "directive": {co: DT[co] for co in COS}, "evidence": EV,
            "A_stats": st, "A_chk": {k: v for k, v in A["chk"].items()},
            "B": [{"key": b["key"], "cites": [{k: v for k, v in c.items() if k != "src"} for c in b["cites"]],
                   "h16": b["h16"], "h12": b["h12"]} for b in B],
            "tags": {co: [{"id": q["id"], "tag": q["tag"], "src": q["src"][:200]} for q in QB[co]] for co in COS},
            "log": LOG}
    with open(os.path.join(rawd, "compare94_parse.json"), "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1, default=list)
    with open(os.path.join(rawd, "compare94_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    print(f"md {OUT_MD} / matrix {OUT_MATRIX} {len(mrows)}행 / map {OUT_MAP} {len(maprows)}행")
    print("A 2016:", {k: len(v) for k, v in st["c16"].items()}, "2012:", {k: len(v) for k, v in st["c12"].items()},
          "any:", {k: len(v) for k, v in st["cany"].items()})
    for l in LOG:
        print(" -", l[:240])


if __name__ == "__main__":
    main()
