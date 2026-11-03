#!/usr/bin/env python3
"""15차 합본 — 조각 CSV 를 작업별 합본 CSV 4개로 잇고, 원문 md 를 옮기고, 보고(15차_보고.md)를 씀.

    python3 scripts/dart/ops15_merge.py        (인자 없음, 웹 요청·API 키 안 씀)

입력(읽기만): dart_out/ops15/조각/{A,B,D}_{bs_g1..g3,gov_g1..g2}.csv · C.csv, dart_out/ops15/원문/{A,B,C,D}/*.md,
             dart_out/ops15/사업보고서_원문.csv, 연차보고서15_목록_g1/g2.csv(보고의 문서 수·실패 행).
출력(이 스크립트 몫): handoff/원문_지주운영방식/ 아래
    원문_지주임원겸직.csv · 원문_지주직원현황.csv · 원문_지주설립_인력계획.csv · 원문_지주위수탁.csv
    원문/A|B|C|D/*.md (dart_out/ops15/원문 그대로 복사) · 원문_지주운영방식_원문md.zip · 15차_보고.md

합본 규칙(메인 지시):
  - 열은 사용자 지정 열 그대로 + 맨 끝 doc_name, collected_at(조각과 같음). utf-8-sig.
  - 회사 순서 KB·신한·하나·우리·NH·메리츠·iM·BNK·JB·한국투자, 그 안에서 fy·doc_kind 순(조각 안 순서 유지 — 안정 정렬).
    C 는 fy 칸이 없어 회사 순서만(조각 안 순서 유지).
  - 작업 A 겸직 사유 잇기: 사업보고서 행과 같은 회사·FY·사람(띄어쓰기 무시; 출생년월이 둘 다 있으면 같아야 함 —
    한쪽이 연도만이면 연도가 같아야 함)·겸직 회사(앞뒤 ㈜·(주)·주식회사 무시)를 가진 지배구조 연차보고서 행에
    reason_text 원문이 있으면 사업보고서 행 reason_text 에 그 원문을 그대로 넣고 note 에
    「reason_text 출처: 지배구조 연차보고서 <url> <page> (같은 겸직)」. 연차보고서 행도 그대로 남김.
    사업보고서 행에 이미 그 보고서 원문 사유가 있으면 덮지 않고 note 에 연차보고서 위치만 적음.
  - 작업 B 연차보고서 행: 직원 수 칸은 비우고 note 「직원 수는 같은 FY 사업보고서 행」.
같은 입력이면 바이트까지 같은 결과(보고의 작성 시각 줄만 다름 — 그 줄은 조각 CSV 의 최신 수정 시각을 씀).
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import shutil
import sys
import zipfile
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
csv.field_size_limit(10 ** 9)
KST = timezone(timedelta(hours=9))

OPS = os.path.join("dart_out", "ops15")
FRAG = os.path.join(OPS, "조각")
SRC_MD = os.path.join(OPS, "원문")
OUT = os.path.join("handoff", "원문_지주운영방식")
OUT_MD = os.path.join(OUT, "원문")
ZIP_NAME = "원문_지주운영방식_원문md.zip"
REPORT = "15차_보고.md"
NONE = "문서에 없음"
ZIP_TIME = (2026, 11, 3, 0, 0, 0)

CORPS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주", "메리츠금융지주",
         "iM금융지주", "BNK금융지주", "JB금융지주", "한국투자금융지주"]
KIND_ORDER = {"사업보고서": 0, "지배구조 연차보고서": 1, "경영공시": 2}
GOV = "지배구조 연차보고서"
BS = "사업보고서"

COLS = {
    "A": ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"],
    "C": ["corp_label", "doc_kind", "rcept_no", "rcept_dt", "section_title", "keyword", "source_text", "page", "note",
          "doc_name", "collected_at"],
    "D": ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"],
}
TASKS = OrderedDict([
    ("A", dict(out="원문_지주임원겸직.csv", frags=["A_bs_g1", "A_bs_g2", "A_bs_g3", "A_gov_g1", "A_gov_g2"])),
    ("B", dict(out="원문_지주직원현황.csv", frags=["B_bs_g1", "B_bs_g2", "B_bs_g3", "B_gov_g1", "B_gov_g2"])),
    ("C", dict(out="원문_지주설립_인력계획.csv", frags=["C"])),
    ("D", dict(out="원문_지주위수탁.csv", frags=["D_bs_g1", "D_bs_g2", "D_bs_g3"])),
])
EMP_NOTE = "직원 수는 같은 FY 사업보고서 행"


def corp_idx(label):
    for i, c in enumerate(CORPS):
        if label == c or label.startswith(c + "("):
            return i
    raise SystemExit("모르는 회사 이름: %r" % label)


def read_frag(name, task):
    path = os.path.join(FRAG, name + ".csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != COLS[task]:
            raise SystemExit("%s 열이 COMMON15 와 다름: %r" % (path, rd.fieldnames))
        rows = [dict(r) for r in rd]
    for r in rows:
        r["_frag"] = name
    return rows


# ---------------------------------------------------------------- 사유 잇기
def pkey(s):
    return re.sub(r"\s+", "", s or "")


_CO_AFFIX = re.compile(r"^(?:㈜|\(주\)|주식회사)+|(?:㈜|\(주\)|주식회사)+$")


def ckey(s):
    s = re.sub(r"\s+", "", s or "")
    prev = None
    while prev != s:
        prev, s = s, _CO_AFFIX.sub("", s)
    return s


def bkey(s):
    return re.sub(r"\D", "", s or "")


def birth_ok(a, b):
    a, b = bkey(a), bkey(b)
    if not a or not b:
        return True
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def link_reasons(rows):
    gov = defaultdict(list)
    for g in rows:
        if g["doc_kind"] != GOV or g["reason_text"] in ("", NONE):
            continue
        if not pkey(g["person"]) or ckey(g["concurrent_company"]) in ("", NONE):
            continue
        gov[(g["corp_label"], g["fy"], pkey(g["person"]), ckey(g["concurrent_company"]))].append(g)
    linked, kept = [], []
    for b in rows:
        if b["doc_kind"] != BS:
            continue
        k = (b["corp_label"], b["fy"], pkey(b["person"]), ckey(b["concurrent_company"]))
        cand = [g for g in gov.get(k, []) if birth_ok(b["birth_ym"], g["birth_ym"])]
        if not cand:
            continue
        g = cand[0]
        where = "지배구조 연차보고서 %s %s" % (g["rcept_no_or_url"], g["page"])
        if b["reason_text"] == NONE:
            b["reason_text"] = g["reason_text"]
            add = "reason_text 출처: %s (같은 겸직)" % where
            linked.append((b, g))
        else:
            add = ("같은 겸직의 연차보고서 사유 원문도 있음: %s — reason_text 는 이 사업보고서 원문 그대로 둠(합본 규칙)"
                   % where)
            kept.append((b, g))
        if len(cand) > 1:
            add += " · 같은 키의 연차보고서 행 %d개 중 첫 행" % len(cand)
        b["note"] = (b["note"] + "; " + add) if b["note"] else add
    return linked, kept


def blank_gov_emp(rows):
    n = 0
    for r in rows:
        if r["doc_kind"] == GOV:
            for c in ("employees_total", "regular", "contract"):
                r[c] = ""
            if EMP_NOTE not in r["note"]:
                r["note"] = (r["note"] + "; " + EMP_NOTE) if r["note"] else EMP_NOTE
            n += 1
    return n


def sort_rows(task, rows):
    if task == "C":
        return sorted(rows, key=lambda r: corp_idx(r["corp_label"]))
    return sorted(rows, key=lambda r: (corp_idx(r["corp_label"]), r["fy"], KIND_ORDER[r["doc_kind"]]))


def write_csv(path, task, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(COLS[task])
        for r in rows:
            w.writerow([r[c] for c in COLS[task]])


# ---------------------------------------------------------------- 원문 md
def copy_md():
    if os.path.isdir(OUT_MD):
        shutil.rmtree(OUT_MD)
    files = []
    for t in "ABCD":
        os.makedirs(os.path.join(OUT_MD, t))
        for fn in sorted(os.listdir(os.path.join(SRC_MD, t))):
            if not fn.endswith(".md"):
                continue
            shutil.copyfile(os.path.join(SRC_MD, t, fn), os.path.join(OUT_MD, t, fn))
            files.append((t, fn))
    zp = os.path.join(OUT, ZIP_NAME)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for t, fn in files:
            zi = zipfile.ZipInfo("원문/%s/%s" % (t, fn), date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zi.flag_bits |= 0x800
            z.writestr(zi, open(os.path.join(OUT_MD, t, fn), "rb").read())
    return files, zp


# ---------------------------------------------------------------- 셈
def pct(a, b):
    return "%.1f%%" % (100.0 * a / b) if b else "-"


def count_task(task, rows):
    c = dict(rows=len(rows))
    c["none_src"] = sum(r["source_text"] == NONE for r in rows)
    c["judg"] = sum("(판단)" in r["note"] for r in rows)
    c["corp"] = Counter(r["corp_label"] for r in rows)
    if task != "C":
        c["kind"] = Counter(r["doc_kind"] for r in rows)
        c["corp_kind"] = Counter((r["corp_label"], r["doc_kind"]) for r in rows)
        c["corp_fy"] = Counter((r["corp_label"], r["fy"]) for r in rows)
        c["corp_fy_kind"] = Counter((r["corp_label"], r["fy"], r["doc_kind"]) for r in rows)
        c["docs"] = Counter()
        for k in {(r["doc_kind"], r["rcept_no_or_url"], r["doc_name"]) for r in rows}:
            c["docs"][k[0]] += 1
    if task == "A":
        c["none_reason"] = sum(r["reason_text"] == NONE for r in rows)
        c["none_reason_kind"] = Counter(r["doc_kind"] for r in rows if r["reason_text"] == NONE)
        c["reason_txt"] = Counter(r["doc_kind"] for r in rows if r["reason_text"] not in ("", NONE))
        c["birth"] = sum(bool(r["birth_ym"]) for r in rows)
        c["person_blank"] = Counter(r["doc_kind"] for r in rows if not r["person"].strip())
    if task == "B":
        kw = Counter()
        for r in rows:
            for k in re.split(r"[·,]", r["keyword"]):
                kw[k.strip()] += 1
        c["kw"] = kw
        c["emp"] = sum(bool(r["employees_total"]) for r in rows)
    if task == "C":
        c["docs_n"] = len({r["rcept_no"] for r in rows if re.match(r"^\d{14}$", r["rcept_no"])})
        kw = Counter()
        for r in rows:
            for k in re.split(r"[·,]", r["keyword"]):
                if k.strip():
                    kw[k.strip()] += 1
        c["kw"] = kw
        c["pdfpage"] = sum("본문 PDF" in r["page"] for r in rows)
    if task == "D":
        c["cp"] = sum(bool(r["counterparty"]) for r in rows)
        c["amt"] = sum(bool(r["amount"]) for r in rows)
    return c


# ---------------------------------------------------------------- 보고
# 실패·누락·판단 글은 수집·검증 에이전트 보고(dart_out/ops15/wave1_results.json · wave2_results.json ·
# 검증 결과 verify15_*.txt · 조각/bs_g3_work.json)를 옮긴 것. 여기서 새 판단을 만들지 않음. [ ] 안은 출처 묶음.
SRC_TAG = "[bs_g1]=사업보고서 KB·신한·하나·우리, [bs_g2]=NH·메리츠·iM, [bs_g3]=BNK·JB·한국투자, " \
          "[gov_g1]=연차보고서 KB·신한·하나·우리·NH, [gov_g2]=연차보고서 메리츠·iM·BNK·JB·한국투자, [C]=설립·전환 신고서"

FAIL_COMMON = [
    "[gov_g1] NH농협금융지주 지배구조 연차보고서 FY2019~2023(공시연도 2020~2024) 수집 실패: www.nhfngroup.com 이 robots.txt·첫 화면·"
    "경영공시 게시판·6차에 받았던 파일 URL 까지 이 환경의 모든 요청에 HTTP 400 「Request Blocked」(2026-11-02 16:07~16:30 KST, 재시도 포함). "
    "다른 UA·경로로 우회하지 않음. 그래서 NH 연차보고서 행은 FY2024·2025(6차 섹션 글)만 있음. 실패 행 5개는 "
    "`dart_out/ops15/연차보고서15_목록_g1.csv`.",
    "[gov_g1] KB금융지주 FY2020 추가공시(2021-04-15, bltcId=414): 서버가 PDF 대신 6바이트(줄바꿈 3개)를 돌려줌. 다시 받지 않았고 이 FY 는 본공시만 원문으로 씀(해당 행 note).",
    "[gov_g2] JB금융지주 FY2019 연차보고서(2020-03-05, 312쪽): PDF 글꼴 글자 대응(ToUnicode)이 깨져 글자층으로 찾을 수 없음. "
    "「?직」 꼴로 찾은 자리만 쪽 그림을 보고 옮김(판독 — note 「판독(PDF 글자층 깨짐 — 쪽 그림을 보고 옮김)」). "
    "파견·출향·전출·전적·겸무와 「?직」 꼴이 아닌 자리는 가릴 수 없음. 312쪽 전부를 그림으로 읽지는 않았고 OCR 도 없음.",
    "[gov_g1·gov_g2] FY2024·2025 연차보고서는 6차 섹션 글(`dart-kit-5차6차.zip` 연차보고서_섹션.csv, PDF 원본은 이번 컨테이너에 없음)만 봄. "
    "섹션 밖 쪽은 확인하지 못함. page 는 「시작페이지 N 섹션 안」, FY2025 는 13차 텍스트의 쪽 번호를 note 에 덧붙임.",
]

A_FAIL = [
    "[gov_g2] iM FY2025 사외이사 후보 「(3) 현재 겸직 업무」 5건, 한국투자 FY2024·2025 「…사외이사를 겸직할 예정」 칸: 6차 섹션 글(과 13차 PDF 글)에 "
    "후보 성명이 없어 person 빈칸. 메리츠 FY2024 는 사외이사 후보 칸이 섹션 글에 없어 A 행이 주석 2건과 리스크협의회 1건뿐.",
    "[gov_g2] PDF 글자 순서가 섞이거나 같은 글이 두 겹으로 추출된 쪽(메리츠 FY2023 p.25·85·96·97·105, JB FY2022·FY2023 p.174·153·p.49~59): "
    "source_text 는 추출 글 그대로이고 note 에 표시. 6차 JB FY2025 본공시 섹션은 글자가 겹쳐 같은 내용을 정정공시(2026-04-07) 섹션에서 옮김.",
    "[gov_g2] PDF 추출 글에 섞인 제어문자(U+0001 등)를 지운 source_text 35행(A 32 · B 3) — 보이는 글자는 같음.",
    "[gov_g1] 연차보고서 행의 holdco_duty 「문서에 없음」·registered·fulltime 빈칸·concurrent_since 「문서에 없음」: 연차보고서의 겸직 서술·표에 "
    "그 칸이 없음. 같은 사람의 사업보고서 행에서 볼 것. 연차보고서 birth_ym 은 사외이사 후보 칸에만 출생연도(월 없음)가 있음.",
    "[gov_g2] 한국투자 FY2023 p.51·p.53 과 6차 FY2024·2025 오태균 경력란 「(겸) 한국투자증권 기타 비상무이사」는 기존 오태균 행 note 에 쪽을 적지 않음.",
]

A_JUDG = [
    "[bs 공통] 겸직 1건 = 1행: 같은 보고서 Ⅷ 겸직 표·Ⅸ 겸직 표·작성기준일 이후 표에 같은 사람×회사(직위 또는 선임시기가 같음)가 거듭 나오면 1행만 두고 "
    "note 「같은 행: [표 n]」. 글(선임일·병합 칸·<br>)이 다르면 그 글도 note 에 옮김([bs_g1] 41행). 이후 표에만 있는 행은 따로 1행.",
    "[bs 공통] 겸직 표 고르기: 표 앞 제목 줄·머리행의 「타회사」「겸직」과 기준일 날짜로 기준일 표와 이후 표를 가름. [bs_g3] 날짜가 둘이면 「현재·기준」이 붙은 날짜, "
    "표 안에 머리행이 다시 나오면 그 뒤는 이후 행(BNK FY2025 [표 1411]). 지난해 기준 표(JB Ⅸ 의 지난 2개년 표 등, 보고서 7개에 14개)는 그 해 보고서 몫이라 넣지 않음.",
    "[bs_g1] 병합 칸: 겸직 표 행의 칸 수가 머리행보다 적으면 앞 칸(성명·회사)을 윗줄 값으로 채움 — note 「(판단) 병합 칸」(KB 53 · 신한 205 · 하나 26 · 우리 24행). "
    "[bs_g2] 메리츠 표·iM 그룹 표의 칸 합침 행은 이름 줄과 그 행 두 줄을 source_text 로 씀.",
    "[bs_g2] iM 그룹 겸직 표의 지주 자기 직위 줄(「(주)DGB금융지주 상무」 등 14개)은 겸직 상대가 아니라 행으로 만들지 않음. [bs_g3] JB 겸직 표의 지주 자기 직위 줄은 "
    "이름 줄로만 두고(source_text 에 함께 옮김) 다른 회사 줄이 없는 사람만 그 줄을 행으로 둠. 「해당사항없음」 자리 행(BNK FY2020 [표 1174])은 행 아님.",
    "[bs 공통] 임원 현황 표 주요경력 칸의 현직 표시(現·(現)·현재·~현재) 조각도 겸직 행으로 넣음(지주 자신과 겸직 표에 이미 있는 회사는 뺌). "
    "[bs_g1] 현직 조각 가운데 그룹사 이름, 「겸」 표시, 회사·기관 이름과 직함(이사·대표·사장·회장·은행장 등)이 있는 것을 넣음(사외이사의 외부 현직 포함). "
    "지주 자신·학력·교수·위원(겸임교수 포함)·회사 이름 없는 조각은 뺌(5차 경력란서술 23행과 다른 판단). "
    "[bs_g2] 현직 표시가 붙은 경력은 모두 1행씩(사외이사의 교수·변호사 같은 본업 포함, 156행). "
    "[bs_g3] 한국투자 「임원약력」 표의 「현재」 행도 넣음, 담당업무 칸에 「겸직·겸무」가 있으면 회사 빈칸 1행.",
    "[bs 공통] 회사·직위 나누기(concurrent_company/concurrent_title): 경력 조각을 회사 끝말(은행·증권·㈜·재단 등)이나 마지막 띄어쓰기에서 나눈 휴리스틱 값. "
    "source_text·note 에 원문이 있음. 어색한 값이 남음(예 「부산대 경제통상대학장 겸 / 대학원장」).",
    "[bs 공통] 지주 칸(holdco_title·holdco_duty·registered·fulltime·birth_ym): 같은 보고서 임원 현황 표에서 같은 성명(띄어쓰기·괄호 표시 뺌) 행의 값을 씀. "
    "registered·fulltime 은 원문 값(사내이사·사외이사·기타비상무이사·미등기 / 상근·비상근 등)을 그대로 두고 등기/미등기로 바꾸지 않음. "
    "임원 표에 없는 겸직자(자회사 임원끼리의 겸직 등)는 빈칸(신한 89 · 우리 40 · NH 35행 등).",
    "[bs 공통] 동명이인·출생년월: 출생년월로 가름. NH FY2021 김용기(1960.07·1965.08)는 note 에 출생년월로 구분했음을 적음([bs_g2] 검증). "
    "같은 성명인데 보고서마다 출생년월이 다른 사람은 그 보고서 값을 두고 note 에 「애매」·(판단): 하나 박병준(FY2019·2020 1965.07 / FY2021~2025 1966.03), "
    "JB 정재식(FY2019~2022 1961.06 / FY2023 1961.05), iM FY2020 최태곤(기준일 표 1965.01 / 이후 표 1963.01). 동일인 여부는 가리지 않음.",
    "[bs_g3] 정정판: 본 보고서를 기준으로 옮기고 정정판과 다른 행만 정정 접수번호로 따로 1행. 그래서 JB FY2023 정정 2건(20240328001876·20240507000432)에 "
    "새 사외이사 이명상·이희승 행이 정정판마다 1행씩(4행).",
    "[bs_g1 검증] reason_text: 하나 FY2021·FY2022 박성호, FY2023 이승열은 같은 보고서 Ⅵ 「1. 이사회에 관한 사항」 이사 현황 표 「선임 배경」 칸을 겸직 사유로 옮김"
    "(기준: 같은 표 행 첫 칸이 성명, 그 칸에 「겸직」과 사유 표현이 함께 있고 겸직 회사 이름도 나옴). 「겸직」 낱말이 없는 다른 회사의 이사 선임 배경 글은 넣지 않음.",
    "[bs 공통] 사람이 정해지지 않은 겸직 목적·법령 글(KB FY2019 Ⅳ 「…계열사 유관조직과 겸직체계를 활용…」, 신한 금융지주회사법 개정 설명 「…임직원의 겸직범위를 확대…」, "
    "NH·JB 「…임원 겸직 승인 및 보고 범위를 확대…」)은 reason_text 에 넣지 않고 note 에만 적거나 「문서에 없음」 유지.",
    "[gov_g1] 연차보고서에는 「임원 겸직 현황」 표(겸직 1건당 행)나 「겸직 사유」 칸이 없다고 보고 회사×FY 마다 「문서에 없음」 1행(30행)을 둠. 그와 별도로 서술 문장·위원회 표·"
    "사외이사 후보 본인 소명 「현재 겸직 업무」 칸처럼 원문이 「겸직」이라고 직접 적은 개별 건을 행으로 넣음. 이사 현황의 경력·약력 칸(現 직위)은 넣지 않음.",
    "[gov_g1] 「○○ 외 겸직사항 없음」은 ○○을 겸직 기관으로 봄. 칸 하나를 concurrent_company 와 concurrent_title 로 나눔(예 ㈜CYS / 대표이사). 「겸직사항 없음」「해당사항 없음」은 행 아님.",
    "[gov_g1] reason_text: 은행장의 지주 비상임이사 겸직 바로 옆의 선임 이유 문장(신한 「창립 이래 … 은행장을 비상임이사로 선임하고 있습니다」, 하나 「은행장이 지주회사 비상임이사를 "
    "겸직하는 것이 … 판단하여」)을 원문 그대로 옮김. 우리 FY2019 「일부 임원 … 지주사와 일부 계열사를 겸직 …」은 특정 겸직 건이 아니지만 사유 문장으로 1행에 넣음.",
    "[gov_g1] 신한 「GMS/GIB사업부문겸직 부사장」은 지주 부사장의 사업부문 겸직으로 읽고 겸직 회사 「문서에 없음」. 하나 리스크관리집행위원회 표 행과 각주 주5를 「 … 」로 이어 "
    "source_text 1개로 만들고, 표의 선임일은 위원 선임일이라 concurrent_since 로 보지 않음.",
    "[gov_g1] 우리 FY2022 박상용·정찬형·신요환: PDF 글 순서로는 겸직 칸이 다음 후보 인적사항 뒤에 오지만 「③ 본인 소명」 머리 위치·p.177 이사 표·경력을 근거로 생성기 배정이 맞다고 봄(검증). "
    "김홍태(예금보험공사 인사지원부 파견 부장)는 「現 … 재직 중」이 적힌 FY2021 만 넣음.",
    "[gov_g2] 사외이사의 계열 밖 겸직(대학·법무법인 등)도 넣음. 지주 안 직위끼리의 겸직(대표이사의 이사회 의장 겸직 등), 지난 경력란, 「겸임교수」 직함, 「겸직하지 않고 있어」 같은 "
    "겸직 없음 문장, 법령·작성기준 인용은 뺌. 같은 문서에 같은 사람·겸직처가 여러 쪽 나오면 처음 나온 곳 1행, 다른 쪽은 note. 한 칸에 겸직처가 여럿이면 겸직처마다 행.",
    "[gov_g2] 성명을 문장 밖에서 읽은 곳: 메리츠 「▣ 후보자 : 이름」, BNK 뒤따르는 「이름 후보자에 대한」, 한국투자 앞쪽 「▶ 이름 사외이사」·「후보자 이름은」, JB 6차 앞 섹션 끝 후보 머리글, "
    "JB 2021~2024 「이름후보자는」, BNK FY2020·2021 김지완과 FY2022 안감찬·이두호는 같은 보고서 다른 쪽 주석, JB FY2019 이광철은 p.23 머리글 그림.",
    "[gov_g2] 사람이 특정되지 않는 행: 메리츠 「CEO(메리츠화재 CEO 겸임)」 4년, 메리츠 FY2023 「겸직 대표이사…의결권 제한」, BNK FY2019 자회사 경영진 6명 겸직 해제, "
    "JB 「지주회사 및 은행자회사 CRO 겸직」(FY2019 판독 포함), iM FY2019 김택동 「겸직수당」(겸직처 미상). 메리츠 홍기표는 자회사 부서장이지만 비고에 「겸직」이 있어 note 를 달아 넣음.",
    "[gov_g2 검증] 「추천사유」(사외이사 후보 칸)는 이사 후보 추천 사유로 보고 겸직 사유로 넣지 않음. JB 「CRO 겸직에 따라 … 원활한 회의진행을 위하여」는 겸직의 결과를 적은 글로 봄. "
    "「(겸)」 약자 자리(이승국 「지주사/전북/광주은행CRO(겸)」 FY2020·2021 4행)는 A 에만 넣음. 이광철 「(JB우리캐피탈 겸직 2014. 03. 19)」 날짜는 겸직 시작일인지 글만으로 "
    "가릴 수 없어 concurrent_since 를 비움. 이승국 선임일은 협의회 위원 선임일로 보고 비움. 한국투자 오태균 「(겸) 한국투자증권 기타 비상무이사」는 기존 행과 같은 겸직으로 봄.",
]

A_OPEN = [
    "[bs_g1·bs_g3] 작업 A 범위(Ⅷ·Ⅸ) 밖이라 행으로 넣지 않은 겸직 관련 원문: 신한 FY2025 Ⅺ 제재 「…당사의 직원은 업무상 사유로 다른 회사의 임원을 겸직하였음에도…」(기업결합신고 누락), "
    "KB FY2022~2025 Ⅺ 제재 「임원 겸직 사전승인 절차 누락」「임직원 겸직에 대한 금융위원회 사전승인 및 보고 누락」, 한국투자 Ⅺ 「…위탁관리부동산투자회사 임원겸임 건 과태료」(자회사 제재 주석).",
    "[bs_g3] JB FY2023 정정판 2건에 같은 새 사외이사 행이 정정판마다 1행씩(이명상·이희승 각 2행) — 중복으로 정리할지.",
    "[bs 공통] 경력 칸에서 나눈 concurrent_company·concurrent_title 은 휴리스틱 값(어색한 값 남음). 임원 현황 칸 행을 넣는 기준이 묶음마다 조금 다름(위 판단 참고).",
]

B_FAIL = [
    "[bs_g3] BNK금융지주·JB금융지주 경영공시 2026.2Q 미수집: 13차 경영공시 텍스트(8개사)와 `dart_out/risk8/경영공시_2026_2Q.csv` 에 없고, 이번 단계는 새 웹 수집을 하지 않음 → "
    "B·D 행을 만들지 않음(빈칸 행이던 4행은 검증 때 빼서 `조각/bs_g3_work.json` missing 에 적음).",
    "[gov_g2] 한국투자 FY2024·2025(6차 섹션)에는 경영지원실 인원(「계열사 겸직 (임)직원 제외」) 문장이 나오지 않음 — 6차 섹션 나눔이 그 쪽을 담지 못했을 수 있음.",
    "[bs_g1] 신한 FY2019 정정 20200515002127: 직원 표 합계 행의 연간급여총액(18,393 → 22,028)과 1인평균(115 → 128)만 바뀌고 직원 수는 같음 — B note.",
]

B_JUDG = [
    "[bs 공통] 직원 수: 사업보고서 Ⅷ 직원 등 현황 표의 마지막 합계 행에서 「기간의 정함이 없는 근로자 전체」(regular)·「기간제 근로자 전체」(contract)·「합계」(employees_total) 칸 원문 숫자. 「-」는 그대로.",
    "[bs 공통] 키워드 행이 있는 연도에는 직원 수 행을 따로 두지 않고 키워드 행마다 직원 수 칸을 채우며 note 에 합계 행 원문을 적음. 키워드가 없는 연도는 합계 행 1행(keyword 「없음」).",
    "[bs_g2] 「키워드마다 1행」을 키워드 × 줄(표 행·문단 줄)로 풀어 같은 키워드라도 줄이 다르면 따로 행. [bs_g2·bs_g3] 300자가 넘는 문단은 키워드가 든 문장만. "
    "[bs_g1] 글 줄은 같은 문단 앞뒤 줄(최대 3줄)을 줄바꿈 그대로 이어 붙임 — 원문 줄 조각이 일부 남음.",
    "[공통] 「전적」 오탐(전적으로·전적인·사전적·발전적·도전적·완전적용·사전적합성 등)과 「전출입」은 키워드에서 뺌. 轉籍 뜻은 앞이 한글이 아닐 때만 셈.",
    "[bs 공통] 경영공시 2026.2Q 행: 13차 PDF 텍스트의 줄바꿈만 붙여 문장으로 만듦. 직원 수 칸은 비움.",
    "[bs_g2] 정정판 글이 다르면 정정판 행을 따로 둠(메리츠 FY2023 정정 20240314001248·20240430000957 보수 표 김용범 「겸직 적용하여 7월 이전」 → 「11월 이전」 4행).",
    "[gov_g1] 연차보고서 B 범위: 조직·인력 서술만. 사외이사·비상임이사 자격요건·결격·겸직 여부 문구, 정관·규정·윤리강령 조문, 이사·후보 경력 속 「파견」「겸직」, 이사회 위원장 겸임, "
    "A 로 옮긴 문장은 뺌(뺀 630문장과 범주: `dart_out/ops15/gov15_g1_work/B_제외문장.csv`). 겸직 사업부문장 성과평가, 「겸직 비상임이사」 평가기준, 감독당국 지적(KB 임원 겸직 사전승인 누락, "
    "하나 겸직임원 인건비 배분, 우리 사외이사 지주·은행 겸직구조 해소) 같은 임원 관련 서술은 넓게 넣음. 본공시 기준, 추가공시에만 있는 글은 따로 행.",
    "[gov_g2] 연차보고서 B 범위: 감사조직 파견, 협의회 구성, 지원부서 인원, 보수 표의 겸직 인원 주석, 보수위원회의 겸직 임직원 보수 안건, BNK 내부규범 「임직원 겸직 및 업무위탁」, "
    "한국투자 규정 「외부위탁 파견연수」를 넣음. 사외이사 후보군 관리·평가대상 제외·위원회 구성 규정·경력란 「파견」은 뺌. 인원 숫자가 든 줄은 원문 그대로 source_text 에 넣음. "
    "BNK 2024-04-26 보수체계 수정공시 3건은 원래 보고서 FY(2021·2022·2023)에 맞춤. 「(겸)」 약자 자리는 사용자 키워드 낱말이 아니라 B 에 넣지 않음.",
]

B_OPEN = [
    "[bs_g1 검증] B 숫자 칸 꼴: 지금은 키워드 행에 직원 수를 채우고 합계 행 원문은 note 에 있음. 「숫자 칸 = source_text 안 숫자」로 맞추려면 회사×FY 마다 합계 행을 source_text 로 하는 "
    "직원 수 행을 따로 두도록 bs_g1·g2·g3 를 함께 바꿔야 함.",
    "[gov_g1] 우리 FY2025 본공시 「자회사간 인력교류가 활발해질 필요가 있음」은 「인력교류」가 요청 키워드가 아니라 넣지 않음 — 키워드를 넓힐지.",
    "[gov_g1] 하나 FY2020~2022 각주 행 일부는 원문 줄 나눔 때문에 「2)」 번호 없이 본문만 있고, NH FY2025 본공시 한 행은 6차 레이아웃 표 행이라 「(의안 제23 호)」 머리가 빠짐 — 글자는 원문 그대로라 둠.",
]

C_FAIL = [
    "[C] OpenDART document.xml 이 014(파일 없음)를 돌려준 문서 10건: 부산은행 [첨부정정] 20101229000364 · 전북은행 [첨부정정] 20130320000306 은 원문이 없어 「문서에 없음」. "
    "우리은행 2018 정정 8건(20181115000213/214/215/218/219/220, 20181121000024, 20181126000093)은 이전 차수(2026-09)에 웹 뷰어에서 회수해 둔 글"
    "(`handoff/dart-benchmark-kit.zip` 원문_지주전환_서술.csv)을 다시 씀 — note 「이전 차수 웹 회수본 — 이번에 새로 받지 않음」, 표 칸·줄바꿈·쪽 번호 없음.",
    "[C] BNK·DGB·JB 2011/2013: 공시목록에 「원본」 증권신고서는 없고 가장 이른 것이 [첨부추가]. 받아 둔 것은 목록에 있는 그대로.",
    "[C] 본문 PDF 는 하나 2005·KB 2008·메리츠 2010·우리 2018 원본 4건만 로컬에 있음 → 그 밖의 문서는 PDF 쪽 없이 XML 위치만. 하나 2005 「(5) 조직도」·「조직도(2005.07.29).jpg…」 2행은 그림 파일 이름이라 PDF 글에 없음.",
    "[C] 신한 2001: 신한은행(구) 00137571 · 조흥은행 00149293 · 신한지주 00382199 의 공시목록에 주식이전 신고서·투자설명서 없음(00137571 에는 「주식교환ㆍ이전결정」 20010628000184 만 있음). "
    "하나 2005 투자설명서(하나은행 세 corp_code 목록), KB 2008 투자설명서(국민은행 2008-03~10)도 목록에 없음 — 사건 단위 「문서에 없음」 3행.",
    "[C] 「주식교환ㆍ이전결정」·주요사항보고서·「분할종료보고서」·신한지주 「등록법인신청서」는 신고서·투자설명서가 아니라 넣지 않음.",
    "[C] 새로 받은 OpenDART 원문 25건(`dart_out/raw/document/`)과 신고서 md(`dart_out/text/ops15/`)는 .gitignore 대상이라 커밋되지 않음.",
]

C_JUDG = [
    "[C] 「전적」: 원문의 「전적」 237곳이 모두 금전적·사전적·발전적·도전적·전적으로·전적인 같은 다른 낱말 → 轉籍 뜻 0건.",
    "[C] 문서당 60행 상한: 후보가 60행을 넘은 문서 20건(KB 3 · 우리 5 · 메리츠 12)은 (1) 절 제목에 기본사항·목적·배경·사업계획·이해관계·지주·설립·완전모회사·이전의/교환의/분할의, "
    "(2) 절 제목에 조직·인력·임원 및 직원·직원·겸직, (3) 원 문단에 「지주」 중 하나인 행만 남김. 뺀 행 1,884개, 문서별 후보·뺀 수는 note.",
    "[C] 1,200자 넘는 문단(정관 전문·웹 회수본 목차 글 등)은 키워드가 든 문장만 원문 부분 문자열로(이웃 문장은 이어 붙임, 131행). DART XML 의 「&cr;&cr;」「<br><br>」를 문단 경계로, "
    "표는 행 하나를 1단위로(1,500자 넘는 표 행은 칸 안 문단으로) 봄.",
    "[C] PDF 쪽: 같은 글이 여러 곳이면 문서 순서상 다음 위치(17행). 쪽을 넘는 글은 「p.시작~끝」. 머리말·표에 끊긴 8행은 첫 20자가 시작 쪽에 있는지로 맞다고 봄.",
    "[C] 우리 2018 정정 웹 회수본은 첫 신고서 XML 의 절 제목이 회수본 글에 나오는 위치로 나눠 section_title 을 붙임(26행). 정정본·투자설명서 행마다 첫 신고서 XML 에도 같은 글이 있는지 "
    "note 에 적음(첫 신고서에 없는 글 105행).",
    "[C] 겸직 표처럼 머리 줄에만 키워드가 있는 표는 머리 줄만 행(108행, note 「표 나머지는 원문 md 같은 절」). 메리츠 2022 「계열회사 임원 겸직 현황」 표 본문은 원문 md 에만 있음.",
    "[C] 사건 범위: 「메리츠금융지주 2022 주식교환」에 2023-01 메리츠증권 교환 신고서(2차분)도 넣음. 「한투 2003」에 동원산업 인적분할 신고서와 동원파이낸스 유상증자 신고서·투자설명서를 넣음"
    "(이전 차수의 「신고서 0건」과 다름). DGB 는 corp_label 「iM금융지주(DGB)」. 이름만 「투자설명서」인 공시는 같은 법인이 바로 앞에 낸 신고서가 사건 서류일 때만 사건 서류로 봄.",
    "[C 검증] 00137571 은 신한은행(구), 00149293 은 조흥은행(현 신한은행)으로 봄(보고자 이름·company.json 설립일·종목코드·2004 신고서 표지). 사건 단위 「문서에 없음」 3행은 C 열에 URL 칸이 없어 "
    "rcept_no 칸에 조회한 공시목록 API 주소(인증키 칸 뺌)를 적음. 웹 회수본 「문서에 없음」 2행은 넓은 검색어에 걸린 글(퇴직급여 회계 주석, 「첨부서류」)을 읽고 유지.",
    "[C] 원문 md 에서 앞 파일과 글자가 같은 절(112개)은 글 대신 그 파일을 가리키는 줄만 둠(19MB → 11MB).",
]

C_OPEN = [
    "[C 검증] C 생성기가 저장소 밖에 있음(`/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/C/scripts/build.py` 등 9개 + manifest.json·kit). "
    "15차 검증 고침도 거기에 넣었음 — 컨테이너가 다시 만들어지면 사라지므로 저장소로 옮길지 메인이 정할 것.",
]

D_FAIL = [
    "[bs_g3] BNK·JB 경영공시 2026.2Q 미수집(작업 B 와 같음) — D 행 없음.",
    "[bs_g1] 4개사(KB·신한·하나·우리) 모두 Ⅹ장(대주주 등과의 거래)에는 D 검색어가 없음. 행은 모두 Ⅺ장 또는 경영공시에서 나옴.",
]

D_JUDG = [
    "[bs_g1] 검색어: 업무위탁·업무수탁·위수탁·위ㆍ수탁·위탁계약·수탁계약·용역(계약/거래/비/료/제공)·상품용역·경영자문·자문(계약/용역/료)·공동(사용/이용/활용)·시스템/전산/IT 공동. "
    "「위탁」「수탁」「자문」「전산」「IT」 낱말 하나만 있는 것(위탁매매·수탁고 등)은 뺌. [bs_g2] 업무위탁·위수탁·위탁/수탁계약·용역·경영자문·자문계약·자문료·공동사용·공동이용·"
    "시스템/전산/IT 공동, 계약·거래 뜻 낱말이 있는 줄만(매매주문 수탁·위탁자예수금·「업무수탁자」·내규 이름·전산시스템 제재·자기주식 신탁계약 위탁투자중개업자는 note 에만). "
    "[bs_g3] 업무위탁·위수탁·용역·경영자문·자문료·자문수수료·공동사용 등, 「…」 안 법규·내규 이름 속 낱말은 뺌.",
    "[bs 공통] 제재·소송·보안 서술 속 언급도 행으로 넣음(지주–계열사 계약이 아닌 행이 많음 — note 에 적음, 기능은 나누지 않음).",
    "[bs 공통] contract_type: 검색어가 든 낱말 덩어리에서 앞뒤 조사·어미를 뗀 것. counterparty: 표에 상대방·거래처(소송은 원고·피고) 칸이 있으면 그 칸, 없으면 문장 「…는 <상대방>과/와 …」의 "
    "회사 꼴 낱말(여럿이면 나눠 1행씩). amount: 금액·가액·수수료 칸이 있을 때만 — 소송가액은 계약 금액이 아니라 비우고 note.",
    "[bs_g1] 같은 보고서의 같은 (상대방·유형)은 1행으로 묶고 note 에 다른 위치(「N개 더: …」).",
    "[bs_g2·bs_g3] 넓은 낱말만 있는 줄과 지주–자회사 수수료 거래 줄은 note 에만: 메리츠 Ⅹ장 거래 표의 「수수료수익」(FY2019·2020)·「브랜드사용료」(FY2021~2023)·「부동산임대차 등」(FY2023), "
    "JB Ⅺ 제재 표 「자회사와의 수수료 거래내역 미공시(금융지주회사법)」.",
    "[bs_g1 검증] 우리 FY2021~2024 Ⅺ 의 고객정보 처리 위탁 글은 D 검색어 꼴이 아니고 KB·신한의 같은 꼴 글도 행이 아니므로 「문서에 없음」 유지(note 에 넓은 낱말 검색 결과).",
]

D_OPEN = [
    "[bs_g1 검증] 같은 보고서의 같은 (상대방·유형) 가운데 글이 다른 43곳이 1행으로 묶여 위치만 note 에 있음(하나대체투자자산운용 제재 표의 사람별 행, KB 업무위탁수수료 미공시 제재, "
    "신한 리츠 업무위탁계약서 제재 등). 원문 md 에는 그 글이 있음 — 행으로 풀지.",
    "[bs_g2] 메리츠 Ⅹ장 지주–자회사 거래 표(수수료수익·브랜드사용료·부동산임대차 등)를 작업 D 범위에 넣을지. 지금은 note 에 (판단)으로 원문 낱말만.",
    "[bs_g3] D 의 「문서에 없음」이 아닌 행 대부분이 소송·제재 표 행(금융자문수수료 소송, 업무위탁 보고 지연 제재 등)으로 지주–계열사 위수탁 계약이 아님 — 범위 판단.",
    "[bs_g1] D 검색어 밖의 고객·개인(신용)정보 처리 위탁 글(우리 FY2019~2025, KB FY2021~2025, 신한 FY2024·2025 Ⅺ) — 넣으려면 검색어를 넓혀야 함.",
]

ROBOTS = [
    ("DART 웹 dart.fss.or.kr", "robots.txt(2026-11-02 확인)가 /dsaf001/main.do · /report/viewer.do · /report/download.do · /pdf/download/ 를 Disallow",
     "뷰어·PDF 내려받기 쓰지 않음 → 새로 받은 사업보고서·신고서는 OpenDART XML 위치(「XML [절 n] …」)만, PDF 쪽 없음"),
    ("OpenDART API opendart.fss.or.kr/api", "API(인증키) — 자동 조회용", "사용. 키는 환경변수로만 읽고 로그·파일에 남기지 않음(meta 는 crtfc_key=*** 로 가림)"),
    ("KB금융지주 www.kbfg.com", "HTTP 200 「User-agent: * / Allow:/」", "수집. 이용약관 쪽 없음(개인정보·고객정보·신용정보 방침만)"),
    ("신한금융지주 www.shinhangroup.com", "HTTP 200, User-agent:* 는 Allow:/ (Disallow 는 /front/asis/·sh_evalution.jsp 뿐)", "수집. 이용약관 쪽 없음"),
    ("하나금융지주 www.hanafn.com", "HTTP 404 → 제한 없음. :8002 는 robots 확인 불가(릴레이가 끊음)",
     "수집. :8002 로는 받지 않고 443 의 같은 경로로 3건(판단). 이용약관 메뉴에는 개인정보·신용정보·고객정보 방침만"),
    ("우리금융지주 www.woorifg.com", "HTTP 200 「User-agent: * / Allow: /」(Yeti 에만 한 경로 Disallow)", "수집. 이용약관 쪽 없음"),
    ("NH농협금융지주 www.nhfngroup.com", "robots.txt 자체가 HTTP 400 「Request Blocked」(RFC 9309 상 4xx 는 제한 없음이지만 사이트 전체가 이 환경 요청을 막음)",
     "수집 못 함 — 우회하지 않음. 이용약관 확인 못 함. FY2019~2023 연차보고서 없음"),
    ("메리츠금융지주 www.meritzgroup.com", "HTTP 200 「User-agent: * / Allow:/」", "수집. 이용약관 화면 없음"),
    ("iM금융지주 www.imfngroup.com", "HTTP 200 「User-agent: * / Allow:/」", "수집. 이용약관 화면 없음"),
    ("BNK금융지주 www.bnkfg.com", "HTTP 404 → 제한 없음", "수집. 이용약관 화면 없음"),
    ("JB금융지주 www.jbfg.com", "HTTP 200 이나 본문이 규칙이 아닌 HTML(meta refresh) → 규칙 0개, 제한 없음(판단)", "수집. 이용약관 화면 없음"),
    ("한국투자금융지주 www.koreaholdings.com", "HTTP 404 → 제한 없음", "수집. 이용약관 화면 없음"),
]

REUSE = [
    "`handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip`(13차, 2026-10 수집): FY2025 사업보고서 본문 PDF 텍스트 8개사(BNK·JB 없음) → 「p.N(본문 PDF, 13차 보관)」 쪽 번호. "
    "경영공시 2026.2Q 텍스트 8개사 → B·D 경영공시 행의 원문(이번에 새로 받지 않음, 수집 시각은 `dart_out/risk8/경영공시_2026_2Q.csv` fetched_at 을 KST 로). 연차보고서 FY2025 텍스트 → 쪽 대조.",
    "`handoff/dart-kit-5차6차.zip` 안 연차보고서_섹션.csv(6차) → FY2024·2025 연차보고서 원문(PDF 원본 없음). URL·sha256·수집 시각은 `handoff/연차보고서_파일목록.csv`.",
    "5차 `handoff/임원현황.csv`·`겸직현황_정리.csv`·`임원_겸직_결합.csv` → 사업보고서 겸직 행 대조용(source_text 는 원문 md 에서 다시 옮김). 9차 `handoff/원문_지주조직_CRO.csv` → FY2023~2025 직원 수 대조(값 같음).",
    "`handoff/원본_주요신고서본문.zip` 본문.pdf 4건(하나 2005·KB 2008·메리츠 2010·우리 2018) → 작업 C PDF 쪽 번호(sha256 같음 확인).",
    "`handoff/dart-benchmark-kit.zip` 원문_지주전환_서술.csv(1~3차) → 우리 2018 정정 8건의 웹 회수본(2026-09 회수, status 014→웹회수). `dart_out/11_원문추출.csv.gz` → 접수번호 찾기에만.",
    "커밋해 둔 OpenDART 원문 묶음(raw_part*.tar.gz) → `dart_out/raw` 로 다시 풀어 사업보고서·신고서 XML 로 씀. 기존 `scripts/dart/*`(client.py·ops15_prep.xml_to_md·web13 의 Web/Robots)는 import 만.",
]

LOST = [
    "컨테이너가 다시 만들어져 git 밖 파일(옛 `dart_out/raw/governance`·`doc`·`text`, `.env`)이 사라졌고 커밋한 것만 남음. DART_API_KEY 는 `.env` 없이 환경변수로만 씀.",
    "6차 연차보고서 PDF 원본이 없어 FY2024·2025 는 6차 섹션 글을 원문으로 씀(page 는 시작페이지 기준, 섹션 밖은 못 봄).",
    "이번 차수에 새로 받은 것도 .gitignore 경로에 있어 컨테이너가 다시 만들어지면 사라짐: 연차보고서 PDF·meta(`dart_out/raw/governance15/`), OpenDART 새 원문 25건(`dart_out/raw/document/`), "
    "쪽 텍스트·XML md(`dart_out/text/ops15/`), 6차 섹션 CSV 풀어 둔 것(`dart_out/ops15/kit56/`), 작업 C 생성기(scratchpad). 원문 md(행이 나온 절)는 이 폴더 `원문/` 과 zip 에 있음.",
    "[gov_g1 사고 기록] 우리 파일 이름 고치기를 처음 돌릴 때 대상 폴더를 g1 으로 제한하지 않아 g2 의 iM·한국투자 PDF 17개 이름이 바뀌었다가 약 5분 안에 meta 의 원래 파일명대로 되돌림"
    "(받은 바이트는 같음, meta 17개는 같은 내용으로 다시 써서 들여쓰기가 다를 수 있음).",
]

COLDOC = OrderedDict([
    ("A", ("원문_지주임원겸직.csv — 겸직 1건당 1행", [
        ("corp_label", "지주 이름(보고용 이름 10곳)"), ("fy", "사업연도(연차보고서는 공시연도-1)"),
        ("person", "겸직한 사람(원문 성명, 괄호 표시 뗌). 원문에 성명이 없으면 빈칸"),
        ("birth_ym", "출생년월(사업보고서 임원 현황 표 원문, 동명이인 구분용). 연차보고서는 후보 칸 출생연도만"),
        ("holdco_title", "지주 직위(임원 현황 표)"), ("holdco_duty", "담당업무 원문(연차보고서 행은 「문서에 없음」)"),
        ("registered", "등기 여부 원문 값(사내이사·사외이사·기타비상무이사·미등기 등 — 등기/미등기로 바꾸지 않음)"),
        ("fulltime", "상근 여부 원문 값(상근·비상근 등)"), ("concurrent_company", "겸직 회사(원문에서 나눈 값)"),
        ("concurrent_title", "겸직 직위"), ("concurrent_since", "겸직 시작(선임시기 칸·경력 기간 원문, 없으면 빈칸이나 「문서에 없음」)"),
        ("reason_text", "겸직 사유 원문. 없으면 「문서에 없음」. 사업보고서 행에 연차보고서 사유를 이은 경우 note 에 출처"),
        ("doc_kind", "사업보고서 / 지배구조 연차보고서"), ("source_text", "원문 그대로(겸직 표 행은 「| 칸 | 칸 |」 꼴, <br>·&cr; 는 원문 칸 안 줄바꿈 표지)"),
        ("rcept_no_or_url", "사업보고서는 DART 접수번호, 연차보고서는 파일 URL"),
        ("page", "사업보고서 「XML [절 n] 「절 제목」 [표 m]」(FY2025 8개사는 「; p.N(본문 PDF, 13차 보관)」 덧붙임), 연차보고서 「p.N」(PDF 쪽) 또는 「시작페이지 N 섹션 안」(6차)"),
        ("note", "해석·대조·찾은 범위. 판단이 들어간 곳은 「(판단)」"),
    ])),
    ("B", ("원문_지주직원현황.csv — 키워드 줄마다 1행, 키워드 없는 연도는 직원 수 1행(keyword 「없음」)", [
        ("corp_label", "지주 이름"), ("fy", "사업연도, 경영공시는 「2026.2Q」"),
        ("employees_total", "직원 수 합계(사업보고서 직원 표 합계 행 원문 숫자). 연차보고서·경영공시 행은 빈칸"),
        ("regular", "기간의 정함이 없는 근로자 전체"), ("contract", "기간제 근로자 전체"),
        ("keyword", "겸직·파견·출향·전출·전적·겸무 중 걸린 낱말, 없으면 「없음」"),
        ("source_text", "키워드가 든 원문 줄(표 행·문단·문장) 그대로, 키워드 없는 직원 수 행은 합계 행 원문, 없으면 「문서에 없음」"),
        ("doc_kind", "사업보고서 / 지배구조 연차보고서 / 경영공시"), ("rcept_no_or_url", "접수번호 또는 파일 URL"),
        ("page", "A 와 같은 꼴, 경영공시는 「p.N」(13차 PDF 쪽)"), ("note", "직원 표 합계 행 원문·각주, 대조, (판단)"),
    ])),
    ("C", ("원문_지주설립_인력계획.csv — 설립·전환 신고서·투자설명서의 키워드 문단마다 1행", [
        ("corp_label", "지주 이름(DGB 는 「iM금융지주(DGB)」)"),
        ("doc_kind", "공시 서류 이름(DART 보고서명 그대로, [첨부추가]·[기재정정] 포함)"),
        ("rcept_no", "DART 접수번호(사건 단위 「문서에 없음」 행은 조회한 공시목록 API 주소, 인증키 칸 뺌)"),
        ("rcept_dt", "접수일"), ("section_title", "원문 절 제목"), ("keyword", "인력·임직원·조직·겸직·파견·전적·채용 중 걸린 낱말(여럿이면 「·」)"),
        ("source_text", "원문 그대로(긴 문단은 키워드 문장만)"),
        ("page", "「p.N(본문 PDF)」(PDF 4건) · 「XML [절 n] …」 · 웹 회수본은 목차 위치"), ("note", "사건 설명·대조·60행 상한·(판단)"),
    ])),
    ("D", ("원문_지주위수탁.csv — 업무위탁·용역·경영자문·전산 공동사용 언급마다 1행", [
        ("corp_label", "지주 이름"), ("fy", "사업연도, 경영공시는 「2026.2Q」"),
        ("counterparty", "상대방(표의 상대방·원고·피고 칸이나 문장의 회사 이름, 없으면 빈칸)"),
        ("contract_type", "원문 표현(검색어가 든 낱말 덩어리)"), ("amount", "금액 칸이 있을 때만(이번에는 거의 빈칸)"),
        ("source_text", "원문 그대로, 없으면 「문서에 없음」"), ("doc_kind", "사업보고서 / 경영공시"),
        ("rcept_no_or_url", "접수번호 또는 파일 URL"), ("page", "A 와 같은 꼴"), ("note", "같은 묶음의 다른 위치, 넓혀 찾은 결과, (판단)"),
    ])),
])

VERIFY = [
    ("bs_g1", "scripts/dart/verify15_bs_g1.py", "1,186(A 980 · B 110 · D 96)", "하나 FY2021~2023 reason_text 3행 반박 성공, 경영공시 「문서에 없음」 page 4칸 채움, note 보강"),
    ("bs_g2", "scripts/dart/verify15_bs_g2.py", "482(A 353 · B 104 · D 25)", "「문서에 없음」 page 19칸 채움, NH 김용기 동명이인 note, 메리츠 거래 표 note"),
    ("bs_g3", "scripts/dart/verify15_bs_g3.py", "509(A 358 · B 112 · D 39)", "BNK·JB 경영공시 미수집 빈칸 행 4개 뺌, 한국투자 지주 자신 8행 뺌, JB 정정판 4행 더함 등"),
    ("gov_g1", "scripts/dart/verify15_gov_g1.py", "210(A 84 · B 126)", "잘린 문장 4행·바닥글 1행·note 머리 4행 고침"),
    ("gov_g2", "scripts/dart/verify15_gov_g2.py", "272(A 170 · B 102)", "JB FY2019 판독 행 note, 「확인 불가」 → p.187 판독 행, JB·이승국 「(겸)」 4행 더함, page 제어문자 지움"),
    ("C", "scripts/dart/verify15_C.py", "769", "웹 회수본 30행 note 문구, 「문서에 없음」 page·rcept_no 채움, 신한 2001 법인 이름 바로잡음, PDF 쪽 범위 6행"),
]


def _bul(L, items):
    for s in items:
        L.append("- " + s)
    L.append("")


def _matrix(L, c, corps, fys, kinds, label):
    L.append("| 회사 | " + " | ".join(fys) + " | 합계 |")
    L.append("|---" * (len(fys) + 2) + "|")
    for co in corps:
        cells = []
        for fy in fys:
            ks = ["경영공시"] if fy == "2026.2Q" else [k for k in kinds if k != "경영공시"]
            parts = [c["corp_fy_kind"].get((co, fy, k), 0) for k in ks]
            cells.append("+".join(str(p) for p in parts) if any(parts) else "0")
        tot = c["corp"].get(co, 0)
        L.append("| %s | %s | %d |" % (co, " | ".join(cells), tot))
    L.append("")
    L.append(label + ".")
    L.append("")


def build_report(ctx):
    cnt, ex, pct, CO, frag_n = ctx["cnt"], ctx["extra"], ctx["pct"], ctx["CORPS"], ctx["frag_n"]
    rows = ctx["rows"]
    L = []
    P = L.append
    P("# 15차 보고 — 지주 운영방식 원문(겸직·파견·전적·위수탁)")
    P("")
    P("- 합본 기준: 조각 CSV 최신 수정 %s. 생성 `python3 scripts/dart/ops15_merge.py`, 합본 검증 `python3 scripts/dart/verify15.py` → `dart_out/ops15/verify15.txt`." % ctx["stamp"])
    P("- 요청 원문 `dart_out/ops15/REQUEST15.md`, 공통 지침 `dart_out/ops15/COMMON15.md`. 숫자는 합본 CSV 에서 다시 센 값이고, 실패·누락·판단은 수집·검증 에이전트 보고"
      "(`dart_out/ops15/wave1_results.json`·`wave2_results.json`, 검증 결과 `dart_out/ops15/verify15_*.txt`, `조각/bs_g3_work.json`)를 옮긴 것(이 보고에서 새로 만든 판단은 없음).")
    P("- 출처 묶음 표시: " + SRC_TAG + ".")
    P("- 기능 분류(리스크·재무 등)나 겸직 이유 추정은 하지 않음. 원문은 source_text·reason_text, 해석은 note 에만.")
    P("")
    P("## 0. 산출물(`handoff/원문_지주운영방식/`)")
    P("")
    P("| 파일 | 내용 | 행 |")
    P("|---|---|---|")
    for t, spec in ctx["TASKS"].items():
        P("| %s | 작업 %s (조각 %s) | %d |" % (spec["out"], t, " · ".join(spec["frags"]), cnt[t]["rows"]))
    md_n = ctx["md_n"]
    P("| 원문/A·B·C·D/*.md | 행의 source_text 가 나온 절 전체(절 머리·출처 줄 + 그 절 글 그대로), `dart_out/ops15/원문/` 과 같은 파일 | A %d · B %d · C %d · D %d개 |"
      % (md_n["A"], md_n["B"], md_n["C"], md_n["D"]))
    P("| %s | 위 원문 md 전체 묶음(UTF-8 파일 이름) | %s 바이트 |" % (ctx["zip_name"], format(ctx["zip_size"], ",")))
    P("| 15차_보고.md | 이 보고 | |")
    P("")
    P("CSV 는 UTF-8(BOM)·머리행 포함, 열은 사용자 지정 열 그대로 + 맨 끝 `doc_name`(문서 이름)·`collected_at`(그 원문을 받은 시각, KST). "
      "회사 순서 KB·신한·하나·우리·NH·메리츠·iM·BNK·JB·한국투자, 그 안에서 fy·doc_kind(사업보고서 → 지배구조 연차보고서 → 경영공시) 순.")
    P("")
    P("## 1. 한눈에 — 작업별 행 수와 「문서에 없음」 비율")
    P("")
    P("| 작업 | 기준 | 행 | 「문서에 없음」 | 비율 |")
    P("|---|---|---|---|---|")
    for t in "ABCD":
        c = cnt[t]
        P("| %s | source_text | %d | %d | %s |" % (t, c["rows"], c["none_src"], pct(c["none_src"], c["rows"])))
    a = cnt["A"]
    P("| A reason_text | reason_text(겸직 사유) | %d | %d | %s |" % (a["rows"], a["none_reason"], pct(a["none_reason"], a["rows"])))
    P("")
    P("- 「문서에 없음」 행은 note 에 찾은 범위(문서·절·검색어)를, page 에 찾은 범위(「…전체(찾은 범위 — 해당 글 없음)」 꼴)를 적음.")
    P("- note 에 「(판단)」이 있는 행: " + " · ".join("%s %d" % (t, cnt[t]["judg"]) for t in "ABCD") + ".")
    P("- 조각별 행 수(「문서에 없음」): " + " · ".join("%s %d(%d)" % (k, v[0], v[1]) for k, v in frag_n.items()) + ".")
    P("")

    # ---------- A
    P("## 2. 작업 A — 지주 임원 겸직(원문_지주임원겸직.csv)")
    P("")
    P("### 수집 건수")
    P("")
    P("- %d행: 사업보고서 %d행(문서 %d건) · 지배구조 연차보고서 %d행(문서 %d건)." % (
        a["rows"], a["kind"][BS], a["docs"][BS], a["kind"][GOV], a["docs"][GOV]))
    P("- birth_ym 이 있는 행 %d. person 빈칸 %d행(사업보고서 %d · 연차보고서 %d)." % (
        a["birth"], a["person_blank"][BS] + a["person_blank"][GOV], a["person_blank"][BS], a["person_blank"][GOV]))
    P("")
    _matrix(L, a, CO, [str(y) for y in range(2019, 2026)], [BS, GOV], "칸은 사업보고서 행+연차보고서 행")
    P("### 겸직 사유(reason_text)와 합본 때 사유 잇기")
    P("")
    P("- reason_text 에 원문이 있는 행: 사업보고서 %d · 연차보고서 %d. 「문서에 없음」 %d/%d(%s) — 잇기 전 %d." % (
        a["reason_txt"][BS], a["reason_txt"][GOV], a["none_reason"], a["rows"], pct(a["none_reason"], a["rows"]), ex["A"]["pre_none"]))
    P("- 사유 잇기(메인 지시 규칙): 같은 회사·FY·사람(띄어쓰기 무시, 출생년월이 둘 다 있으면 같아야 함)·겸직 회사(앞뒤 ㈜·(주)·주식회사 무시)를 가진 연차보고서 행에 사유 원문이 있으면 "
      "사업보고서 행 reason_text 에 그대로 넣고 note 에 「reason_text 출처: 지배구조 연차보고서 <url> <page> (같은 겸직)」. 연차보고서 행도 그대로 남김. 이은 행 %d:" % len(ex["A"]["linked"]))
    for b, g in ex["A"]["linked"]:
        P("  - %s FY%s %s(%s) %s %s ← %s" % (b["corp_label"], b["fy"], b["person"], b["birth_ym"] or "출생년월 없음",
                                          b["concurrent_company"], b["concurrent_title"], g["page"]))
    for b, g in ex["A"]["kept"]:
        P("- 덮지 않음 1: %s FY%s %s — 사업보고서 행에 이미 그 보고서 원문 사유(「선임 배경」 칸)가 있어 그대로 두고 note 에 연차보고서 위치만 적음(합본 규칙)."
          % (b["corp_label"], b["fy"], b["person"]))
    P("- 이어지지 않은 연차보고서 사유 행: 사람이 정해지지 않은 우리 FY2019 일반 서술 1행.")
    P("")
    P("### 실패·누락")
    P("")
    _bul(L, FAIL_COMMON[:4] + ["[bs] 사업보고서 정정판 원문이 OpenDART 에 없음(014 「파일이 존재하지 않습니다」) %d건: %s — 본 보고서와 비교하지 못하고 해당 연도 행 note 에 적음."
                                % (len(ctx["c014"]), "; ".join(ctx["c014"]))] + A_FAIL)
    P("### 「문서에 없음」")
    P("")
    P("- source_text 「문서에 없음」 %d행: 연차보고서에 「임원 겸직 현황」 표(겸직 1건당 행)가 없는 회사×FY 마다 1행([gov_g1] KB·신한·하나·우리 FY2019~2025, NH FY2024·2025). "
      "사업보고서 행에는 없음." % a["none_src"])
    P("- reason_text 「문서에 없음」 %d행(사업보고서 %d · 연차보고서 %d). 사업보고서 Ⅷ·Ⅸ 와 보고서 전체, 연차보고서 전체를 넓은 검색어(겸직·겸임·겸무 근처의 사유·목적·이유·배경·필요성·위하여 등)로 "
      "다시 찾아 반박을 시도함 — 하나 「선임 배경」 칸 3곳만 반박 성공, 나머지는 법령 설명·일반 서술·제재 글이라 유지(검증 보고)." % (
          a["none_reason"], a["none_reason_kind"][BS], a["none_reason_kind"][GOV]))
    P("")
    P("### 판단이 들어간 곳")
    P("")
    _bul(L, A_JUDG + ["[합본] 사유 잇기 규칙(위). 사업보고서 행에 이미 원문 사유가 있으면 덮지 않음."])
    P("### 메인·사용자가 정할 것(검증 보고의 남은 일)")
    P("")
    _bul(L, A_OPEN)

    # ---------- B
    b = cnt["B"]
    P("## 3. 작업 B — 지주 직원 수와 겸직·파견 언급(원문_지주직원현황.csv)")
    P("")
    P("### 수집 건수")
    P("")
    P("- %d행: 사업보고서 %d · 지배구조 연차보고서 %d · 경영공시 2026.2Q %d. 키워드별(한 행에 하나): %s." % (
        b["rows"], b["kind"][BS], b["kind"][GOV], b["kind"]["경영공시"],
        " · ".join("%s %d" % (k, v) for k, v in b["kw"].most_common())))
    P("- 직원 수 칸이 있는 행 %d(사업보고서만). 연차보고서 행 %d개는 직원 수 칸을 비우고 note 「%s」(합본 규칙)." % (b["emp"], ex["B"]["gov_blank"], EMP_NOTE))
    P("")
    _matrix(L, b, CO, [str(y) for y in range(2019, 2026)] + ["2026.2Q"], [BS, GOV, "경영공시"], "FY 칸은 사업보고서 행+연차보고서 행, 2026.2Q 칸은 경영공시 행")
    P("- 회사×FY 직원 수(합계 / 기간의 정함이 없는 근로자 / 기간제, 사업보고서 직원 표 합계 행):")
    P("")
    P("| 회사 | " + " | ".join("FY%d" % y for y in range(2019, 2026)) + " |")
    P("|---" * 8 + "|")
    for co in CO:
        cells = []
        for y in range(2019, 2026):
            v = ctx["emp"].get((co, str(y)))
            cells.append("/".join(v) if v else "-")
        P("| %s | %s |" % (co, " | ".join(cells)))
    P("")
    P("### 실패·누락")
    P("")
    _bul(L, FAIL_COMMON + B_FAIL)
    P("### 「문서에 없음」")
    P("")
    P("- source_text 「문서에 없음」 %d/%d(%s):" % (b["none_src"], b["rows"], pct(b["none_src"], b["rows"])))
    for r in ctx["none_rows"]["B"]:
        P("  - %s %s %s — %s" % (r["corp_label"], r["fy"], r["doc_kind"], r["doc_name"]))
    kwnone = [r for r in rows["B"] if r["keyword"] == "없음" and r["source_text"] != NONE]
    P("- 키워드가 없어 직원 수 합계 행만 둔 행(keyword 「없음」, 문서에 없음 아님) %d: %s." % (
        len(kwnone), ", ".join("%s FY%s" % (r["corp_label"], r["fy"]) for r in kwnone)))
    P("")
    P("### 판단이 들어간 곳")
    P("")
    _bul(L, B_JUDG + ["[합본] 연차보고서 행의 직원 수 칸은 비우고 note 「%s」." % EMP_NOTE])
    P("### 메인·사용자가 정할 것")
    P("")
    _bul(L, B_OPEN)

    # ---------- C
    c = cnt["C"]
    P("## 4. 작업 C — 지주 설립·전환 때 인력 운용 계획(원문_지주설립_인력계획.csv)")
    P("")
    P("### 수집 건수")
    P("")
    P("- %d행, 문서 %d건(신고서·투자설명서·정정·첨부 포함)과 사건 단위 「문서에 없음」 3행. 회사별: %s." % (
        c["rows"], c["docs_n"], " · ".join("%s %d" % (k, c["corp"][k]) for k in sorted(c["corp"], key=lambda x: CO.index(x.split("(")[0])))))
    P("- 키워드별(여러 키워드 행은 키워드마다 셈): %s. 전적(轉籍) 0." % " · ".join("%s %d" % (k, v) for k, v in c["kw"].most_common()))
    P("- page 에 본문 PDF 쪽이 붙은 행 %d. 나머지는 XML [절 n] [표 m] 또는 웹 회수본 목차 위치." % c["pdfpage"])
    P("- 사건별 문서(검증 (e)): 하나 2005 5건 · KB 2008 3 · BNK 2011 3 · DGB 2011 2 · 메리츠 2010 분할 2 · JB 2013 4 · 우리 2018 10 · 메리츠 2022(2차 포함) 12 · 한국투자 2003 9 · 신한 2001 0 = 50건.")
    P("")
    P("### 실패·누락")
    P("")
    _bul(L, C_FAIL)
    P("### 「문서에 없음」")
    P("")
    P("- %d/%d(%s), 모두 반박 시도 후 유지:" % (c["none_src"], c["rows"], pct(c["none_src"], c["rows"])))
    for r in ctx["none_rows"]["C"]:
        P("  - %s — %s (%s)" % (r["corp_label"], r["doc_kind"], r["rcept_no"] if re.match(r"^\d{14}$", r["rcept_no"]) else "공시목록 조회"))
    P("")
    P("### 판단이 들어간 곳")
    P("")
    _bul(L, C_JUDG)
    P("### 메인·사용자가 정할 것")
    P("")
    _bul(L, C_OPEN)

    # ---------- D
    d = cnt["D"]
    P("## 5. 작업 D(선택) — 지주와 계열사 사이 업무위탁·용역·공동사용(원문_지주위수탁.csv)")
    P("")
    P("### 수집 건수")
    P("")
    P("- %d행: 사업보고서 %d · 경영공시 2026.2Q %d. counterparty 가 있는 행 %d, amount 가 있는 행 %d." % (
        d["rows"], d["kind"][BS], d["kind"]["경영공시"], d["cp"], d["amt"]))
    P("- 상대방이 원문에 나온 그룹 안 계약([bs_g1]): KB국민카드–(주)국민은행·(주)KB손해보험·KB생명보험(주)/KB라이프생명 「업무위ㆍ수탁에 관한 계약」(FY2019~2025), "
      "우리카드–우리은행 「업무위탁에 관한 계약」(FY2019·2020). 경영공시 2026.2Q 신한 p.62·하나 p.65 「…전산시스템…시설을 공동사용할 수 있다」 조문. 나머지는 대부분 제재·소송·보안 서술 속 언급.")
    P("")
    _matrix(L, d, CO, [str(y) for y in range(2019, 2026)] + ["2026.2Q"], [BS, "경영공시"], "FY 칸은 사업보고서 행, 2026.2Q 칸은 경영공시 행")
    P("### 실패·누락")
    P("")
    _bul(L, D_FAIL + ["[bs] 사업보고서 정정판 014 %d건(작업 A 와 같음)." % len(ctx["c014"])])
    P("### 「문서에 없음」")
    P("")
    P("- %d/%d(%s):" % (d["none_src"], d["rows"], pct(d["none_src"], d["rows"])))
    byco = OrderedDict()
    for r in ctx["none_rows"]["D"]:
        byco.setdefault(r["corp_label"], []).append(r["fy"])
    for co, fys in byco.items():
        P("  - %s: %s" % (co, ", ".join(("FY" + f) if f[:4].isdigit() and len(f) == 4 else ("경영공시 " + f) for f in fys)))
    P("- 넓은 낱말(위탁·수탁·용역·자문·공동·전산·IT·수수료·브랜드 등)로 다시 찾아 반박을 시도함 — 반박된 행 없음(검증 보고).")
    P("")
    P("### 판단이 들어간 곳")
    P("")
    _bul(L, D_JUDG)
    P("### 메인·사용자가 정할 것")
    P("")
    _bul(L, D_OPEN)

    # ---------- 공통
    P("## 6. 수집 경로와 robots·이용약관 판정")
    P("")
    P("| 곳 | robots.txt·약관 | 처리 |")
    P("|---|---|---|")
    for a1, a2, a3 in ROBOTS:
        P("| %s | %s | %s |" % (a1, a2, a3))
    P("")
    P("- 회사 사이트 robots 확인은 2026-11-02 16:06 KST 무렵, 원본은 `dart_out/raw/governance15/<회사>/robots_*`. 받은 경로는 robots 가 허용한 경로만, HTTP 는 web13.Web(UA 고정, 1.2초 간격, 3회 재시도).")
    P("- 하나 :8002 목록 URL 3건은 실패사유 칸과 파일_url 칸에 실제로 받은 주소를 적음. 우리 파일 저장 이름 날짜가 게시일과 다른 5건은 목록 CSV 에 「게시 뒤 파일이 바뀌었을 수 있음」.")
    P("- 경영공시 2026.2Q 는 이번에 새로 받지 않음(13차 보관 텍스트).")
    P("")
    P("## 7. 이전 차수 파일 재사용")
    P("")
    _bul(L, REUSE)
    P("## 8. 컨테이너 재생성으로 사라진 것과 남는 위험")
    P("")
    _bul(L, LOST)
    P("## 9. 열 설명")
    P("")
    for t, (title, cols) in COLDOC.items():
        P("### " + title)
        P("")
        P("| 열 | 뜻 |")
        P("|---|---|")
        for k, v in cols:
            P("| %s | %s |" % (k, v))
        P("| doc_name | 문서 이름(DART 보고서명, 연차보고서는 「제목 (본공시/추가공시…, 파일 …)」) |")
        P("| collected_at | 그 원문을 받은 시각(KST). OpenDART 는 사업보고서_원문.csv fetched_at, 6차 섹션은 연차보고서_파일목록.csv, 경영공시는 13차 수집 시각 |")
        P("")
    P("## 10. 검증")
    P("")
    P("| 조각 | 검증 스크립트(인자 없이, exit 0/1) | 검증한 행 | 검증 때 고친 것 |")
    P("|---|---|---|---|")
    for k, s, n, f in VERIFY:
        P("| %s | `%s` → `dart_out/ops15/verify15_%s.txt` | %s | %s |" % (k, s, k, n, f))
    P("")
    P("- 여섯 조각 검증 모두 exit 0(실패 0). 원문 글자 그대로·page 위치·열·BOM·필수 칸·출처 목록·비밀값·회사×FY 행 유무·직원 수·겸직 표 손 대조·출생년월 대조·「문서에 없음」 반박을 봄. "
      "고친 것은 모두 각 생성기에 넣고 다시 돌려 같은 md5 를 확인함.")
    P("- 합본 검증 `scripts/dart/verify15.py`: 조각 검증 6개 exit 모음, 합본 = 조각 이어 붙임(사유 잇기로 바뀐 칸만 다름 — 그 칸은 연차보고서 행 원문과 같음), "
      "합본 모든 행 source_text·reason_text 가 출처 텍스트에 그대로(전수), 이 보고의 「문서에 없음」 수·비율이 합본과 같음, 키·비밀값 없음, 이 폴더에 PDF 없음 → `dart_out/ops15/verify15.txt`.")
    P("")
    return "\n".join(L) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    merged, cnt, frag_n = {}, {}, {}
    extra = {}
    for task, spec in TASKS.items():
        rows = []
        for fr in spec["frags"]:
            part = read_frag(fr, task)
            frag_n[fr] = (len(part), sum(r["source_text"] == NONE for r in part))
            rows += part
        if task == "A":
            pre_none = sum(r["reason_text"] == NONE for r in rows)
            linked, kept = link_reasons(rows)
            extra["A"] = dict(pre_none=pre_none, linked=linked, kept=kept)
        if task == "B":
            extra["B"] = dict(gov_blank=blank_gov_emp(rows))
        rows = sort_rows(task, rows)
        write_csv(os.path.join(OUT, spec["out"]), task, rows)
        merged[task] = rows
        cnt[task] = count_task(task, rows)
    files, zp = copy_md()
    newest = max(os.path.getmtime(os.path.join(FRAG, fr + ".csv")) for s in TASKS.values() for fr in s["frags"])
    stamp = datetime.fromtimestamp(newest, KST).strftime("%Y-%m-%d %H:%M KST")
    md_n = Counter(t for t, _ in files)
    with open(os.path.join(OPS, "사업보고서_원문.csv"), encoding="utf-8-sig", newline="") as f:
        c014 = ["%s FY%s %s %s" % (r["label"], r["fy"], r["report_nm"], r["rcept_no"])
                for r in csv.DictReader(f) if r["doc_status"] == "014"]
    emp = {}
    for r in merged["B"]:
        if r["doc_kind"] == BS and r["employees_total"] and (r["corp_label"], r["fy"]) not in emp:
            emp[(r["corp_label"], r["fy"])] = (r["employees_total"], r["regular"], r["contract"])
    none_rows = {t: [r for r in merged[t] if r["source_text"] == NONE] for t in "ABCD"}
    txt = build_report(dict(cnt=cnt, extra=extra, frag_n=frag_n, md_n=md_n, stamp=stamp, CORPS=CORPS, NONE=NONE,
                            TASKS=TASKS, pct=pct, zip_name=ZIP_NAME, rows=merged, c014=c014, emp=emp,
                            none_rows=none_rows, zip_size=os.path.getsize(zp)))
    with open(os.path.join(OUT, REPORT), "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    for task, spec in TASKS.items():
        p = os.path.join(OUT, spec["out"])
        print("%s %s %d행 md5 %s" % (task, p, len(merged[task]), hashlib.md5(open(p, "rb").read()).hexdigest()))
    print("원문 md %d개 (A %d · B %d · C %d · D %d) → %s, zip %s md5 %s" % (
        len(files), md_n["A"], md_n["B"], md_n["C"], md_n["D"], OUT_MD, zp,
        hashlib.md5(open(zp, "rb").read()).hexdigest()))
    print("사유 잇기: 채움 %d행 · 덮지 않음 %d행 · B 연차보고서 행 직원 수 비움 %d행" % (
        len(extra["A"]["linked"]), len(extra["A"]["kept"]), extra["B"]["gov_blank"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
