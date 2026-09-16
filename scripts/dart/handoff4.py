# -*- coding: utf-8 -*-
"""4차 인계 산출물 — ① 계열사 간 데이터 활용·결합 ② 겸영·부수업무.

handoff.py·handoff3.py 와 같은 규율: dart_out/ 아래 파일만 읽는 순수 함수이고
네트워크도 API 키도 쓰지 않는다. 못 읽은 값은 빈칸 + 사유이고, 지어내지 않는다.

여기서 만드는 것
  1) 겸영부수업무_목록.csv          — 업무명 단위 행 분해(+ 자른 방법 + 자르기 전 원문 문장)
  2) 마이데이터_영위업무.csv         — 허가·등록 기재 여부와 문구
  3) 정관_사업목적.csv              — 사업목적 변경 이력 + 소집공고 본문의 조항
  4) 계열사_데이터거래.csv           — 데이터·전산·플랫폼 관련 계열사 거래 (+ 안건결과)
  5) 이사회_정보거버넌스_안건.csv     — 이사회 의안 중 고객정보·정보관리·지침 건
  6) 고객정보_제재.csv              — 금융지주회사법 §48조의2 등 정보 관련 제재

■ 이 파일이 판단하지 않는 것
  - 업무명을 회사 간에 대응시키지 않는다. 표기가 다르면 다른 행이다(요청서 지시).
  - 안건이 '중요한지' 판단하지 않는다. 결과 표기를 원문 그대로 옮길 뿐이다.
  - 제재의 경중을 판단하지 않는다.
"""
from __future__ import annotations

import collections
import csv
import os
import re

import config

csv.field_size_limit(10 ** 9)

PROV_KEYS = ["fetched_at", "status", "raw_path", "raw_sha256"]
SRC_NAME = "11_원문추출.csv"


def _write(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _emit(result, handoff_dir, name, rows, cols, note=""):
    path = os.path.join(handoff_dir, name)
    _write(path, rows, cols)
    result["paths"].append(path)
    result["counts"][name] = len(rows)
    if note:
        result["notes"].append(note)
    return path


def _fy_of(report_nm, rcept_dt):
    """사업연도. 사업보고서는 '(YYYY.MM)' 표기를, 소집공고는 접수연도를 쓴다."""
    fy = config.annual_fy_4cha(report_nm)
    if fy:
        return fy
    return (rcept_dt or "")[:4]


def _read_section_text(out_dir, text_path):
    """emit 이 남긴 섹션 txt 전문. 없으면 ''(사유는 호출부가 남긴다)."""
    if not text_path:
        return ""
    p = text_path if os.path.isabs(text_path) else os.path.join(out_dir, text_path)
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


# ── 4차 문서 스캔 ─────────────────────────────────────────────────────────
class Doc(object):
    """한 문서의 4차용 뷰. 서술 행(text)과 표 셀 행(table)을 따로 들고 있는다."""

    __slots__ = ("rcept_no", "corp_label", "rcept_dt", "report_nm", "fy",
                 "sections", "tables", "prov")

    def __init__(self, rcept_no):
        self.rcept_no = rcept_no
        self.corp_label = self.rcept_dt = self.report_nm = self.fy = ""
        self.sections = {}          # section_index -> {title, title_raw, text_path}
        self.tables = {}            # (section_index, table_index) -> [[cell, ...], ...]
        self.prov = {}


def scan_4cha(out_dir):
    """11_원문추출.csv 에서 4차 문서만 뽑아 Doc 으로 묶는다.

    표 셀은 (row_index, cell_ord) 로 다시 격자를 세우지 않는다 — 원문 순서대로
    행에 담을 뿐이다. rowspan/colspan 은 원문 그대로 셀에 붙어 있고 여기서 풀지 않는다.
    """
    src = os.path.join(out_dir, SRC_NAME)
    docs = {}
    if not os.path.exists(src):
        return docs
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            nm, dt = r.get("report_nm", ""), r.get("rcept_dt", "")
            if not r.get("corp_label"):
                continue
            if not config.is_4cha_doc(nm, dt):
                continue
            rc = r.get("rcept_no", "")
            d = docs.get(rc)
            if d is None:
                d = docs[rc] = Doc(rc)
                d.corp_label = r.get("corp_label", "")
                d.rcept_dt, d.report_nm = dt, nm
                d.fy = _fy_of(nm, dt)
                d.prov = {k: r.get(k, "") for k in PROV_KEYS}
            si = r.get("section_index", "")
            if si not in d.sections:
                d.sections[si] = {"title": r.get("section_title", ""),
                                  "title_raw": r.get("section_title_raw", ""),
                                  "text_path": r.get("text_path", "")}
            if r.get("kind") != "table":
                continue
            key = (si, r.get("table_index", ""))
            rows = d.tables.setdefault(key, [])
            ri = r.get("row_index", "")
            if not rows or rows[-1][0] != ri:
                rows.append([ri, []])
            rows[-1][1].append(r.get("cell_text", "") or "")
    return docs


def _table_rows(doc, key):
    return [cells for _ri, cells in doc.tables.get(key, [])]


# ── 1) 겸영·부수업무 ──────────────────────────────────────────────────────
# ■ 실측이 요청서의 전제와 다르다(사업보고서 22건 전수, 본문+셀).
#   보험사는 0/0 이다 — 삼성생명·삼성화재·신한라이프·메리츠화재·DB생명·DB손해·
#   ABL생명·동양생명 전부 「겸영업무」·「부수업무」가 0회다. 있는 곳은 은행·지주다
#   (국민은행 5/18 · 우리은행 7/10 · 신한은행 6/7 · iM금융지주 4/6).
#   그리고 있는 곳도 *표가 아니라 서술 문장*이고 **신고일은 어느 문서에도 없다.**
#
#   국민은행 — `※「은행법 제27조 2항」에 의거 '가상이동통신망 사업'을 부수업무로
#               영위하고 있음` (※ 로 나열)
#   우리은행 — `주요 부수업무로는 국고수납업무, 정부보관금 수납업무, … 등이`
#               (쉼표 한 문장, '등'으로 끝나 완결 목록이 아니다)
#   한화생명 — `겸영 가능한 보험종목, 겸영업무, 부수업무 및 일체의 사업을 영위하고
#               있습니다` (업무명이 하나도 없다)
#
# 그래서 "업무명 단위로 행 분해" 는 문장을 기계적으로 자르는 일이 된다. 자른 결과만
# 실으면 검증이 불가능하므로 **자르기 전 원문 문장과 자른 방법을 같은 행에 싣는다.**
# 정규화는 하지 않는다 — 회사마다 다른 표기를 통일하지 않는다(요청서 지시).
KIND_WORDS = (("겸영", "겸영업무"), ("부수", "부수업무"))

# 문장 경계. 본문은 공백만 접혀 있어 줄바꿈이 없다. 마침표 뒤 공백과 ※ 앞에서 자른다.
_SENT = re.compile(r"(?<=[.])\s+|(?=※)|(?<=니다)\s+(?=[가-힣(])")
# 따옴표·괄호 안의 이름. DART 원문은 '…' 「…」 『…』 "…" 를 섞어 쓴다.
_QUOTED = re.compile(r"['‘’\"“”]([^'‘’\"“”]{2,60})"
                     r"['‘’\"“”]"
                     r"|[「『]([^」』]{2,60})[」』]")
# 「…로는 A, B, C 및 D 등이」 꼴의 나열.
#
# 트리거를 「로는」·「에는」으로 좁힌다. 「로서」·「는」까지 받으면 서술문이 나열로 오인돼
# 문장 조각이 업무명으로 잘렸다(실측 오탐):
#   '인가를 받아 부수업무를 운영할 수'
#   '또는 사회ㆍ경제적 필요에 따라 수행하게 되는 업무이며 은행법에서 정하는 …'
#   '영위하던「여신전문금융업법」에 의한 신용카드업무는 취소(2011'
_LIST_SPAN = re.compile(r"(겸영업무|부수업무)(?:로는|에는)\s*(.{4,300}?)"
                        r"(?:\s*등(?:이|은|을|의|과|이며|이 있)|\s*있습니다|\s*있음|[.])")
# 업무명으로 받아들일 수 있는 꼴인가. 통과 못 하는 항목이 하나라도 있으면 **그 문장의
# 나열 자체를 버리고** 문장전체로 떨어진다 — 절반만 자르는 것은 안 자르는 것보다 나쁘다.
_NOT_A_NAME = re.compile(r"(습니다|하였|하며|이며|되는|따라|이외|그리고|경우|위하여|"
                         r"통하여|취소|가능|받아|할 수|에서 정하는|에 의한|영위하|"
                         r"수행하|있는|입니다|됩니다|말합니다|인정되는)")
# 근거법령 — 「…법」·「…규정」·「…특별법」 표기와 '○○법 제N조' 를 둘 다 본다.
_LAW_BR = re.compile(r"[「『]([^」』]{2,60}?(?:법|법률|규정|특별법|시행령|시행규칙)[^」』]{0,20})[」』]")
_LAW_ART = re.compile(r"([가-힣A-Za-z·\s]{2,30}?법)\s*(제\s*\d+\s*조(?:의\s*\d+)?"
                      r"(?:\s*제?\s*\d+\s*항)?)")
# 쉼표로만 자른다. 「및」로도 자르면 '수납 및 지급대행'(은행법 부수업무의 한 항목)이
# '수납' / '지급대행' 둘로 쪼개진다 — 원문에 없는 업무명을 만들어 내는 것이다.
# 'A, B, C 및 D' 의 마지막이 'C 및 D' 로 남는 것은 감수한다(원문 그대로다).
_SPLIT_ITEM = re.compile(r"\s*[,、]\s*")


def _IS_LAW_NAME(name):
    """인용부호 안이 업무명이 아니라 법령명인가.

    처음에는 '(법|규정|…)\\s*(제\\d|$)' 로만 봤는데 '…에 관한 **법률**' 이 빠져나가
    '정보통신망 이용촉진 및 정보보호 등에 관한 법률'·'자본시장과 금융투자업에 관한
    법률' 이 업무명으로 실렸다(실측). 꼬리를 법률까지 넓힌다.
    """
    return bool(re.search(r"(법|법률|규정|특별법|시행령|시행규칙)\s*(제\s*\d|$)",
                          (name or "").strip()))


def _IS_OWN_NAME(name, corp_label):
    """인용부호 안이 그 회사 자신의 이름인가. '신한은행' 같은 것이 업무명으로 샜다."""
    a = (name or "").replace(" ", "")
    b = (corp_label or "").replace(" ", "").replace("(구)", "")
    return bool(a and b and (a in b or b in a))


def _laws_in(text):
    out = []
    for m in _LAW_BR.finditer(text or ""):
        out.append(m.group(1).strip())
    for m in _LAW_ART.finditer(text or ""):
        out.append((m.group(1).strip() + " " + m.group(2).strip()).strip())
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _split_sentences(text):
    return [s.strip() for s in _SENT.split(text or "") if s and s.strip()]


def _names_from_sentence(sent, kind_word, corp_label=""):
    """(업무명_원문, 추출방법) 목록. 못 자르면 [] 를 돌려주고 호출부가 문장 전체를 싣는다."""
    out = []
    # (a) 나열형: 「주요 부수업무로는 A, B, C 및 D 등이」
    for m in _LIST_SPAN.finditer(sent):
        if m.group(1) != kind_word:
            continue
        span = m.group(2)
        items = [i.strip().strip("'‘’\"“”「」『』")
                 for i in _SPLIT_ITEM.split(span)]
        items = [i for i in items if i]
        if len(items) < 2:                       # 쉼표가 없으면 나열이 아니다
            continue
        if any(not (2 <= len(i) <= 60) or _NOT_A_NAME.search(i) for i in items):
            continue                             # 하나라도 이상하면 통째로 버린다
        out.extend((i, "쉼표나열") for i in items)
    if out:
        return out
    # (b) ※ 항목형: 「※「은행법 제27조 2항」에 의거 '가상이동통신망 사업'을 부수업무로 영위」
    if sent.lstrip().startswith("※"):
        for m in _QUOTED.finditer(sent):
            name = (m.group(1) or m.group(2) or "").strip()
            # 법령 표기는 업무명이 아니다 — 근거법령 컬럼으로 간다
            if name and not _IS_LAW_NAME(name) and not _IS_OWN_NAME(name, corp_label):
                out.append((name, "※항목"))
        if out:
            return out
    # (c) 따옴표가 하나만 있는 평서문
    q = [(m.group(1) or m.group(2) or "").strip() for m in _QUOTED.finditer(sent)]
    q = [x for x in q if x and not _IS_LAW_NAME(x) and not _IS_OWN_NAME(x, corp_label)]
    if len(q) == 1:
        return [(q[0], "인용부호")]
    return []


def build_concurrent_business(out_dir, docs, handoff_dir, result):
    rows = []
    seen_corp = {}
    for rc in sorted(docs):
        d = docs[rc]
        seen_corp.setdefault((d.corp_label, d.fy), 0)
        base = dict(법인=d.corp_label, 사업연도=d.fy, rcept_no=rc, 보고서명=d.report_nm,
                    접수일=d.rcept_dt, **d.prov)
        # (1) 표 안에 있는 경우 — 셀 단위로 그대로 옮긴다
        for (si, ti), _rows in sorted(d.tables.items()):
            for cells in _table_rows(d, (si, ti)):
                line = " | ".join(cells)
                for short, kind in KIND_WORDS:
                    if kind not in line:
                        continue
                    sec = d.sections.get(si, {})
                    rows.append(dict(base, 구분=short, 업무명_원문="", 추출방법="표행",
                                     원문문장=line[:2000],
                                     근거법령_원문=" / ".join(_laws_in(line)),
                                     신고일="", 신고일_비고="원문에 신고일 기재 없음",
                                     섹션번호=si, 섹션제목=sec.get("title", ""),
                                     section_title_raw=sec.get("title_raw", ""),
                                     text_path=sec.get("text_path", "")))
                    seen_corp[(d.corp_label, d.fy)] += 1
        # (2) 서술 문장 — 실측상 이쪽이 대부분이다
        for si, sec in sorted(d.sections.items()):
            body = _read_section_text(out_dir, sec.get("text_path", ""))
            if not body:
                continue
            for sent in _split_sentences(body):
                for short, kind in KIND_WORDS:
                    if kind not in sent:
                        continue
                    laws = " / ".join(_laws_in(sent))
                    names = _names_from_sentence(sent, kind, d.corp_label)
                    if not names:
                        names = [("", "문장전체")]
                    for name, how in names:
                        rows.append(dict(base, 구분=short, 업무명_원문=name, 추출방법=how,
                                         원문문장=sent[:2000], 근거법령_원문=laws,
                                         신고일="", 신고일_비고="원문에 신고일 기재 없음",
                                         섹션번호=si, 섹션제목=sec.get("title", ""),
                                         section_title_raw=sec.get("title_raw", ""),
                                         text_path=sec.get("text_path", "")))
                        seen_corp[(d.corp_label, d.fy)] += 1
    # 0건 법인·연도는 0 으로 남긴다(요청서 검증 항목). text_path 만 채운다.
    for (lab, fy), n in sorted(seen_corp.items()):
        if n:
            continue
        rc = next((k for k, v in docs.items() if v.corp_label == lab and v.fy == fy), "")
        d = docs.get(rc)
        tp = ""
        if d:
            tp = next((s.get("text_path", "") for _si, s in sorted(d.sections.items())
                       if s.get("text_path")), "")
        rows.append(dict(법인=lab, 사업연도=fy, rcept_no=rc,
                         보고서명=d.report_nm if d else "", 접수일=d.rcept_dt if d else "",
                         구분="(없음)", 업무명_원문="", 추출방법="",
                         원문문장="", 근거법령_원문="", 신고일="",
                         신고일_비고="이 사업보고서에 「겸영업무」·「부수업무」 낱말이 0회",
                         섹션번호="", 섹션제목="", section_title_raw="", text_path=tp,
                         **(d.prov if d else {})))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], r["구분"], r["추출방법"],
                             r["업무명_원문"]))
    cols = ["법인", "사업연도", "구분", "업무명_원문", "추출방법", "원문문장",
            "근거법령_원문", "신고일", "신고일_비고", "섹션번호", "섹션제목",
            "section_title_raw", "text_path", "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    hit_corps = sorted({r["법인"] for r in rows if r["구분"] != "(없음)"})
    zero_corps = sorted({r["법인"] for r in rows if r["구분"] == "(없음)"} - set(hit_corps))
    _emit(result, handoff_dir, "겸영부수업무_목록.csv", rows, cols,
          "겸영부수업무_목록: 추출 법인 %d곳 / 0건 법인 %d곳 / 총 %d행. "
          "신고일은 전량 빈칸 — 사업보고서 원문에 신고일 기재가 없다(실측)."
          % (len(hit_corps), len(zero_corps), len(rows)))
    return {"hit": hit_corps, "zero": zero_corps}


# ── 2) 마이데이터·허가/등록 기재 ──────────────────────────────────────────
MYDATA_WORDS = ["마이데이터", "본인신용정보관리업", "전자금융업", "신용정보업",
                "혁신금융서비스", "규제샌드박스"]


def build_mydata(out_dir, docs, handoff_dir, result):
    rows = []
    per_corp = collections.defaultdict(set)
    for rc in sorted(docs):
        d = docs[rc]
        base = dict(법인=d.corp_label, 사업연도=d.fy, rcept_no=rc,
                    보고서명=d.report_nm, 접수일=d.rcept_dt, **d.prov)
        found = False
        for si, sec in sorted(d.sections.items()):
            body = _read_section_text(out_dir, sec.get("text_path", ""))
            blobs = [("본문", s) for s in _split_sentences(body)]
            for (tsi, ti), _r in sorted(d.tables.items()):
                if tsi != si:
                    continue
                for cells in _table_rows(d, (tsi, ti)):
                    blobs.append(("표 %s행" % ti, " | ".join(cells)))
            for where, text in blobs:
                hits = [w for w in MYDATA_WORDS if w in text]
                if not hits:
                    continue
                found = True
                per_corp[d.corp_label].update(hits)
                rows.append(dict(base, 기재여부="있음", 근거낱말="|".join(hits),
                                 위치=where, 문구_원문=text[:2000],
                                 근거법령_원문=" / ".join(_laws_in(text)),
                                 섹션번호=si, 섹션제목=sec.get("title", ""),
                                 section_title_raw=sec.get("title_raw", ""),
                                 text_path=sec.get("text_path", "")))
        if not found:
            tp = next((s.get("text_path", "") for _si, s in sorted(d.sections.items())
                       if s.get("text_path")), "")
            rows.append(dict(base, 기재여부="없음", 근거낱말="", 위치="", 문구_원문="",
                             근거법령_원문="", 섹션번호="", 섹션제목="",
                             section_title_raw="", text_path=tp))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], r["기재여부"], r["위치"]))
    cols = ["법인", "사업연도", "기재여부", "근거낱말", "위치", "문구_원문",
            "근거법령_원문", "섹션번호", "섹션제목", "section_title_raw", "text_path",
            "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    _emit(result, handoff_dir, "마이데이터_영위업무.csv", rows, cols,
          "마이데이터_영위업무: 기재 있음 법인 %d곳 / 전체 행 %d"
          % (len(per_corp), len(rows)))
    return per_corp


# ── 3) 정관 사업목적 ──────────────────────────────────────────────────────
CHARTER_SECTION_HINTS = ("정관에 관한 사항", "사업목적")
CHARTER_TABLE_HINTS = ("정관변경일", "사업목적", "변경 전", "변경 후", "신구조문",
                       "변경전", "변경후", "개정", "현행")


def build_charter_purpose(out_dir, docs, handoff_dir, result):
    rows = []
    notice_docs, notice_with_purpose = set(), set()
    for rc in sorted(docs):
        d = docs[rc]
        is_notice = config.is_meeting_notice_4cha(d.report_nm, d.rcept_dt)
        if is_notice:
            notice_docs.add(rc)
        src = "주주총회소집공고" if is_notice else "사업보고서"
        base = dict(법인=d.corp_label, 사업연도=d.fy, 출처유형=src, rcept_no=rc,
                    보고서명=d.report_nm, 접수일=d.rcept_dt, **d.prov)
        for (si, ti), _r in sorted(d.tables.items()):
            sec = d.sections.get(si, {})
            title = sec.get("title", "")
            cells_all = _table_rows(d, (si, ti))
            blob = " ".join(" | ".join(c) for c in cells_all)
            in_sec = any(h in title for h in CHARTER_SECTION_HINTS)
            in_tab = any(h in blob for h in CHARTER_TABLE_HINTS)
            if not (in_sec or in_tab):
                continue
            if "사업목적" not in blob and not in_sec:
                continue
            has_text = "사업목적" in blob
            if is_notice and has_text:
                notice_with_purpose.add(rc)
            for ri, cells in enumerate(cells_all):
                rows.append(dict(base, 섹션번호=si, 섹션제목=title,
                                 section_title_raw=sec.get("title_raw", ""),
                                 표번호=ti, 행번호=ri,
                                 행_원문=" | ".join(cells)[:4000],
                                 조항전문_확보여부="사업목적 문구 있음" if has_text
                                 else "표는 있으나 「사업목적」 문구 없음",
                                 text_path=sec.get("text_path", "")))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], r["출처유형"],
                             str(r["섹션번호"]), str(r["표번호"]), r["행번호"]))
    cols = ["법인", "사업연도", "출처유형", "조항전문_확보여부", "행_원문",
            "섹션번호", "섹션제목", "section_title_raw", "표번호", "행번호",
            "text_path", "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    miss = sorted(notice_docs - notice_with_purpose)
    _emit(result, handoff_dir, "정관_사업목적.csv", rows, cols,
          "정관_사업목적: 총 %d행 / 소집공고 %d건 중 본문에서 「사업목적」이 잡힌 건 %d, "
          "안 잡힌 건 %d (웹 첨부 수집 여부는 이 수치를 보고 사용자가 판단)"
          % (len(rows), len(notice_docs), len(notice_with_purpose), len(miss)))
    return {"notice": len(notice_docs), "with_purpose": len(notice_with_purpose),
            "missing": miss}


# ── 4)·5) 이사회 안건 / 계열사 데이터 거래 ────────────────────────────────
# 안건 결과 표기. 원문 그대로 옮기고, 분류는 첫 일치 낱말 하나만 쓴다.
# 부결·보류가 있으면 그게 가결보다 중요한 정보다(사용자 지시) — 별도로 센다.
RESULT_WORDS = ["부결", "보류", "재논의", "철회", "수정가결", "원안가결", "조건부",
                "가결", "결의", "보고", "이의 없음", "이의없음"]
NEGATIVE_RESULTS = ("부결", "보류", "재논의", "철회")
BOARD_SECTION_HINT = "이사회"
GOV_WORDS = ["고객정보", "정보관리", "지침", "정보보호", "개인신용정보", "신용정보",
             "전산", "공동사용", "정보제공", "마이데이터", "데이터", "플랫폼"]
DEAL_WORDS = ["데이터", "전산", "플랫폼", "시스템", "정보처리", "클라우드", "마이데이터",
              "공동사용", "고객정보", "위수탁", "위·수탁", "업무위탁"]
DEAL_SECTION_HINTS = ("대주주 등과의 거래", "특수관계자", "계열회사", "이사회")


def _result_of(line):
    for w in RESULT_WORDS:
        if w in line:
            return w
    return "(표기없음)"


def _is_agenda_table(cells_all):
    if not cells_all:
        return False
    hdr = " ".join(cells_all[0])
    return ("의안" in hdr or "안건" in hdr or "의안내용" in hdr
            or ("개최일자" in hdr and "가결" in hdr))


def build_board_governance(out_dir, docs, handoff_dir, result):
    rows = []
    res_count = collections.Counter()
    per_corp = collections.Counter()
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti), _r in sorted(d.tables.items()):
            sec = d.sections.get(si, {})
            if BOARD_SECTION_HINT not in sec.get("title", ""):
                continue
            cells_all = _table_rows(d, (si, ti))
            if not _is_agenda_table(cells_all):
                continue
            for ri, cells in enumerate(cells_all[1:], start=1):
                line = " | ".join(cells)
                hits = [w for w in GOV_WORDS if w in line]
                if not hits:
                    continue
                rr = _result_of(line)
                res_count[rr] += 1
                per_corp[d.corp_label] += 1
                rows.append(dict(법인=d.corp_label, 사업연도=d.fy, rcept_no=rc,
                                 보고서명=d.report_nm, 접수일=d.rcept_dt,
                                 안건_원문=line[:4000], 안건결과=rr,
                                 매칭낱말="|".join(hits),
                                 근거법령_원문=" / ".join(_laws_in(line)),
                                 섹션번호=si, 섹션제목=sec.get("title", ""),
                                 section_title_raw=sec.get("title_raw", ""),
                                 표번호=ti, 행번호=ri,
                                 text_path=sec.get("text_path", ""), **d.prov))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], str(r["섹션번호"]),
                             str(r["표번호"]), r["행번호"]))
    cols = ["법인", "사업연도", "안건_원문", "안건결과", "매칭낱말", "근거법령_원문",
            "섹션번호", "섹션제목", "section_title_raw", "표번호", "행번호",
            "text_path", "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    neg = sum(res_count[w] for w in NEGATIVE_RESULTS)
    _emit(result, handoff_dir, "이사회_정보거버넌스_안건.csv", rows, cols,
          "이사회_정보거버넌스_안건: %d행 / 법인 %d곳 / 결과 분포 %s / 부결·보류·재논의·철회 %d건"
          % (len(rows), len(per_corp), dict(res_count.most_common()), neg))
    return {"rows": len(rows), "per_corp": per_corp, "results": res_count, "negative": neg,
            "negative_rows": [r for r in rows if r["안건결과"] in NEGATIVE_RESULTS]}


def build_affiliate_data_deals(out_dir, docs, handoff_dir, result):
    rows = []
    res_count = collections.Counter()
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti), _r in sorted(d.tables.items()):
            sec = d.sections.get(si, {})
            title = sec.get("title", "")
            if not any(h in title for h in DEAL_SECTION_HINTS):
                continue
            cells_all = _table_rows(d, (si, ti))
            for ri, cells in enumerate(cells_all):
                line = " | ".join(cells)
                hits = [w for w in DEAL_WORDS if w in line]
                if not hits:
                    continue
                rr = _result_of(line)
                res_count[rr] += 1
                # 금액은 '있을 때만' 싣는다. 실측상 특수관계자 표는 「전체 특수관계자
                # 합계」로 묶여 있어 건별 금액이 없는 경우가 많다 — 지어내지 않는다.
                amt = [c for c in cells if re.fullmatch(r"[\d,\.\-]{2,20}", (c or "").strip())]
                rows.append(dict(법인=d.corp_label, 사업연도=d.fy, rcept_no=rc,
                                 보고서명=d.report_nm, 접수일=d.rcept_dt,
                                 거래_원문=line[:4000], 안건결과=rr,
                                 매칭낱말="|".join(hits),
                                 금액_원문후보=" | ".join(amt[:6]),
                                 금액_비고="" if amt else "표에 건별 금액 없음(합계 표기 등)",
                                 근거법령_원문=" / ".join(_laws_in(line)),
                                 섹션번호=si, 섹션제목=title,
                                 section_title_raw=sec.get("title_raw", ""),
                                 표번호=ti, 행번호=ri,
                                 text_path=sec.get("text_path", ""), **d.prov))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], str(r["섹션번호"]),
                             str(r["표번호"]), r["행번호"]))
    cols = ["법인", "사업연도", "거래_원문", "안건결과", "매칭낱말", "금액_원문후보",
            "금액_비고", "근거법령_원문", "섹션번호", "섹션제목", "section_title_raw",
            "표번호", "행번호", "text_path", "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    neg = sum(res_count[w] for w in NEGATIVE_RESULTS)
    _emit(result, handoff_dir, "계열사_데이터거래.csv", rows, cols,
          "계열사_데이터거래: %d행 / 결과 분포 %s / 부결·보류·재논의·철회 %d건"
          % (len(rows), dict(res_count.most_common(8)), neg))
    return {"rows": len(rows), "results": res_count, "negative": neg}


# ── 6) 고객정보 관련 제재 ─────────────────────────────────────────────────
# 계획에 없던 발견. KB손해보험 FY2025 「3. 제재 등과 관련된 사항」에
#   2024.09.06 | 금융위원회 | 과태료 60백만원
#   | 금융지주회사에 대한 고객정보의 제공 및 관리 절차 위반
#   | 금융지주회사법 제48조의2, 시행령 제27조의2 제1항
# 이 있다. "지주에 고객정보를 넘길 때 무엇을 잘못하면 제재받는가" 의 실물이다.
SANCTION_SECTION_HINT = "제재"
SANCTION_WORDS = ["고객정보", "개인신용정보", "신용정보", "정보보호", "전산",
                  "정보처리", "마이데이터", "데이터", "금융지주회사법"]


def build_sanctions(out_dir, docs, handoff_dir, result):
    rows = []
    per_corp = collections.Counter()
    holding_law = 0
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti), _r in sorted(d.tables.items()):
            sec = d.sections.get(si, {})
            if SANCTION_SECTION_HINT not in sec.get("title", ""):
                continue
            for ri, cells in enumerate(_table_rows(d, (si, ti))):
                line = " | ".join(cells)
                hits = [w for w in SANCTION_WORDS if w in line]
                if not hits:
                    continue
                laws = _laws_in(line)
                is_holding = "금융지주회사법" in line
                if is_holding:
                    holding_law += 1
                per_corp[d.corp_label] += 1
                rows.append(dict(법인=d.corp_label, 사업연도=d.fy, rcept_no=rc,
                                 보고서명=d.report_nm, 접수일=d.rcept_dt,
                                 제재행_원문=line[:4000], 매칭낱말="|".join(hits),
                                 근거법령_원문=" / ".join(laws),
                                 금융지주회사법_해당="Y" if is_holding else "",
                                 섹션번호=si, 섹션제목=sec.get("title", ""),
                                 section_title_raw=sec.get("title_raw", ""),
                                 표번호=ti, 행번호=ri,
                                 text_path=sec.get("text_path", ""), **d.prov))
    rows.sort(key=lambda r: (r["법인"], r["사업연도"], str(r["섹션번호"]),
                             str(r["표번호"]), r["행번호"]))
    cols = ["법인", "사업연도", "제재행_원문", "금융지주회사법_해당", "매칭낱말",
            "근거법령_원문", "섹션번호", "섹션제목", "section_title_raw",
            "표번호", "행번호", "text_path", "보고서명", "접수일", "rcept_no"] + PROV_KEYS
    _emit(result, handoff_dir, "고객정보_제재.csv", rows, cols,
          "고객정보_제재: %d행 / 법인 %d곳 / 그중 금융지주회사법 근거 %d행"
          % (len(rows), len(per_corp), holding_law))
    return {"rows": len(rows), "per_corp": per_corp, "holding_law": holding_law}


def build_all(out_dir, handoff_dir, result):
    docs = scan_4cha(out_dir)
    if not docs:
        result["skipped"].append(
            "4차 산출물: 11_원문추출.csv 에 4차 문서 행이 0건 — 파일을 만들지 않음")
        return {}
    corps = sorted({d.corp_label for d in docs.values()})
    result["notes"].append("4차 대상 문서 %d건 / 법인 %d곳" % (len(docs), len(corps)))
    stats = {"docs": len(docs), "corps": corps}
    stats["concurrent"] = build_concurrent_business(out_dir, docs, handoff_dir, result)
    stats["mydata"] = build_mydata(out_dir, docs, handoff_dir, result)
    stats["charter"] = build_charter_purpose(out_dir, docs, handoff_dir, result)
    stats["board"] = build_board_governance(out_dir, docs, handoff_dir, result)
    stats["deals"] = build_affiliate_data_deals(out_dir, docs, handoff_dir, result)
    stats["sanctions"] = build_sanctions(out_dir, docs, handoff_dir, result)
    return stats
