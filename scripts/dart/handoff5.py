# -*- coding: utf-8 -*-
"""5차 인계 산출물 — 지주의 조직 운영(임원 구성·담당업무·겸직·인원·위원회).

handoff.py·handoff3.py·handoff4.py 와 같은 규율: dart_out/ 아래 파일만 읽는 순수
함수이고 네트워크도 API 키도 쓰지 않는다. 못 읽은 값은 빈칸 + 사유이고 지어내지 않는다.

여기서 만드는 것
  1) 임원현황.csv               — 임원 1인 1행. 담당업무는 **원문 그대로**, 머리행 전문 병기
  2) 직원현황.csv               — 직원 수 표 + 「자회사 소속 겸직임원 N명 포함」 주석 원문
  3) 겸직현황_정리.csv           — 겸직 표 + 경력란 서술 두 갈래, 판별어휘·출처섹션 병기
  4) 위원회현황.csv              — 이사회 내 위원회 구성표
  5) 임원_겸직_결합.csv          — 겸직 행 ↔ 임원 행 조인(성명 + 출생년월)
  6) 지주_자회사_임원명부교집합.csv  — 같은 사람이 지주·자회사 양쪽 임원표에 실린 건
  7) 설립첫해_임원구성.csv        — 출범 첫 사업보고서의 임원 전원과 담당업무 원문

■ 이 파일이 판단하지 않는 것
  - 담당업무 표기를 회사 간에 표준화하지 않는다. 표기가 다르면 다른 값이다(요청서 지시).
  - 격자를 추론하지 않는다. 머리행 칸 수와 데이터행 칸 수가 다르면(병합셀) 이름 붙은
    컬럼을 **비우고 사유를 적는다** — 위치로 밀어 넣으면 값이 한 칸씩 밀려 조용히 틀린다.
  - 겸직 대상이 금융회사가 아니어도 자동으로 버리지 않는다. Y/N 만 남기고 판단은 사용자 몫.
  - 어느 정정본이 최종인지 판단하지 않는다. 접수번호별로 따로 싣는다.

■ 단일 출처
  머리행 판별은 config.interlock_header / config.committee_header 하나만 쓴다. emit 이
  표를 전개할지 고르는 것과 여기서 표를 집는 것이 **같은 함수**여야 한다. 4차에서 이
  둘이 갈라져 겸직_업무위탁.csv 가 7개 법인에서 7,161행 줄어든 적이 있다.
"""
from __future__ import annotations

import collections
import csv
import os
import re

import config
import docparse

csv.field_size_limit(10 ** 9)

# 단일 출처. selftest 가 `is` 로 단언한다 — 여기서 따로 적으면 안 된다.
INTERLOCK_HEADER = config.interlock_header
COMMITTEE_HEADER = config.committee_header

PROV_KEYS = ["fetched_at", "status", "raw_path", "raw_sha256"]
SRC_NAME = "11_원문추출.csv"
N = docparse.normalize_for_match

# 5차가 보는 법인. 지주 10곳 + 보험 자회사 6곳 + 신한은행(매트릭스 양방향 관측).
BANK_COUNTERPART = ("신한은행(구)",)
TARGET_CORPS = tuple(config.HOLDING_10) + tuple(config.INSURER_SUB_5CHA) + BANK_COUNTERPART


def corp_kind(label):
    if label in config.HOLDING_10:
        return "지주"
    if label in config.INSURER_SUB_5CHA:
        return "보험자회사"
    if label in BANK_COUNTERPART:
        return "은행"
    return "기타"


# ── 입출력 ────────────────────────────────────────────────────────────────
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


def _fy(report_nm, rcept_dt):
    """사업연도. '(YYYY.MM)' 의 **연도만** 본다.

    메리츠금융지주는 설립 당시 3월 결산이라 첫 사업보고서가 '(2011.03)' 이다.
    12월 결산을 전제하고 월로 사업연도를 계산하면 이 문서가 통째로 어긋난다.
    """
    m = re.search(r"\((\d{4})\.\d{1,2}\)", report_nm or "")
    if m:
        return m.group(1)
    dt = (rcept_dt or "")
    return str(int(dt[:4]) - 1) if dt[:4].isdigit() else ""


# ── 문서 스캔 ─────────────────────────────────────────────────────────────
class Doc(object):
    __slots__ = ("rcept_no", "corp_label", "kind", "rcept_dt", "report_nm", "fy",
                 "sections", "tables", "prov")

    def __init__(self, rcept_no):
        self.rcept_no = rcept_no
        self.corp_label = self.kind = self.rcept_dt = self.report_nm = self.fy = ""
        self.sections = {}      # section_index -> {title, title_raw, text_path}
        self.tables = {}        # (section_index, table_index) -> [[row_index, [cell,...]], ...]
        self.prov = {}


def is_5cha_source(report_nm, rcept_dt, rcept_no, corp_label):
    """5차 산출물이 읽을 문서인가.

    FY2023~25 사업보고서(정정 포함) + 5차 지정 문서 + 설립 첫해 문서. 주주총회소집공고는
    임원표·위원회표가 없으므로 제외한다 — 읽어도 0행이고 스캔만 무거워진다.
    """
    if corp_label not in TARGET_CORPS and corp_label not in config.NEW_CORPS_5CHA:
        return False
    rc = rcept_no or ""
    if rc in config.DOC_5CHA or rc in config.DOC_5CHA_HEADER_ONLY:
        return True
    nm = docparse.normalize_for_match(report_nm or "")
    if "사업보고서" not in nm or "반기보고서" in nm or "분기보고서" in nm:
        return False
    return bool(re.search(r"\(\d{4}\.\d{1,2}\)", report_nm or ""))


def scan(out_dir):
    """11_원문추출.csv 에서 5차 대상 문서만 Doc 으로 묶는다.

    표 셀은 (row_index, cell_ord) 로 격자를 다시 세우지 않는다 — 원문 순서대로 행에
    담을 뿐이다. rowspan/colspan 은 셀에 붙어 있고 여기서 풀지 않는다.
    """
    src = os.path.join(out_dir, SRC_NAME)
    docs = {}
    if not os.path.exists(src):
        return docs
    cur_key, cur_doc, cur_rows = None, None, []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lab = r.get("corp_label") or ""
            if not lab:
                continue
            rc = r.get("rcept_no", "")
            nm, dt = r.get("report_nm", ""), r.get("rcept_dt", "")
            if rc not in docs and not is_5cha_source(nm, dt, rc, lab):
                continue
            d = docs.get(rc)
            if d is None:
                d = docs[rc] = Doc(rc)
                d.corp_label, d.kind = lab, corp_kind(lab)
                d.rcept_dt, d.report_nm = dt, nm
                d.fy = _fy(nm, dt)
                d.prov = {k: r.get(k, "") for k in PROV_KEYS}
            si = r.get("section_index", "")
            if si not in d.sections:
                d.sections[si] = {"title": r.get("section_title", ""),
                                  "title_raw": r.get("section_title_raw", ""),
                                  "text_path": r.get("text_path", "")}
            if r.get("kind") != "table":
                continue
            key = (si, r.get("table_index", ""))
            if cur_key is not None and key != cur_key:
                _finish(cur_doc, cur_key, cur_rows)
                cur_rows = []
            cur_key, cur_doc = key, d
            ri = r.get("row_index", "")
            if not cur_rows or cur_rows[-1][0] != ri:
                cur_rows.append([ri, []])
            # rowspan/colspan 을 버리지 않는다 — 머리행이 몇 칸을 덮는지가 여기 있다.
            cur_rows[-1][1].append({"text": r.get("cell_text", "") or "",
                                    "rowspan": r.get("rowspan", ""),
                                    "colspan": r.get("colspan", "")})
        if cur_key is not None:
            _finish(cur_doc, cur_key, cur_rows)
    return docs


def _wanted(rows):
    """5차가 쓰는 표인가. 아니면 메모리에 들고 있지 않는다.

    11_원문추출.csv 는 2.8 GB 이고 대상 문서만 해도 표 셀이 수백만 개다. 전부 들고
    있으면 1 GB 를 넘기므로, 표가 끝나는 즉시 머리행을 보고 버린다. 버린 표는
    원문 표 CSV(조직운영_표_5차.csv)에 그대로 남아 있으므로 삭제가 아니다.
    """
    if not rows:
        return False
    tbl = {"rows": rows}
    if INTERLOCK_HEADER(tbl, N) or COMMITTEE_HEADER(tbl, N):
        return True
    for row in rows[:config.HEADER_SCAN_ROWS]:
        cells = [N(c["text"]) for c in row]
        if OFFICER_HEADER_KEY in cells:
            return True
        if any(k in cells for k in EMPLOYEE_HEADER_KEYS):
            return True
    return False


def _finish(doc, key, rows):
    grid = [cells for _ri, cells in rows]
    if doc is not None and _wanted(grid):
        doc.tables[key] = grid


def _grid(doc, key):
    return doc.tables.get(key, [])


def _as_table(rows):
    return {"rows": rows}


def _int(v, dflt=1):
    try:
        n = int(str(v).strip())
        return n if n > 0 else dflt
    except (TypeError, ValueError):
        return dflt


def header_slots(rows, keys):
    """(데이터 시작 행, 컬럼별 이름 후보) 또는 None.

    **격자를 추론하지 않는다.** rowspan/colspan 은 원문 XML 이 직접 적어 둔 값이고,
    여기서는 그 선언을 읽어 머리행 칸과 데이터행 칸을 맞출 뿐이다. 실측(신한지주
    FY2025 임원표): 머리행 12칸(대부분 rowspan=2, 「소유주식수」만 colspan=2),
    둘째 행 2칸(의결권있는/없는 주식), 데이터행 13칸. span 을 안 보면 12≠13 이라
    **모든 행이 열수불일치가 되어 성명·담당업무가 통째로 빈칸이 된다.**

    colspan>1 인 칸이 있으면 그 아래에 하위 머리행이 반드시 있으므로 머리행은 2줄이다.
    하위 이름은 부모 이름과 함께 후보로 남긴다 — 메리츠 겸직표는 부모가
    「계열회사 겸직내역」이고 자식이 「회사명」·「직 책」이라 둘 다 쓸 수 있어야 한다.
    """
    for i, row in enumerate(rows[:config.HEADER_SCAN_ROWS]):
        if not any(k in [N(c["text"]) for c in row] for k in keys):
            continue
        slots, need = [], []
        for c in row:
            cs, rs = _int(c.get("colspan")), _int(c.get("rowspan"))
            for _ in range(cs):
                slots.append([c.get("text", "")])
                if cs > 1 and rs < 2:
                    need.append(len(slots) - 1)
        data_start = i + 1
        if need and i + 1 < len(rows):
            sub = rows[i + 1]
            for j, ci in enumerate(need):
                if j < len(sub):
                    child = sub[j].get("text", "")
                    slots[ci].append(child)
                    slots[ci].append(slots[ci][0] + "·" + child)
            data_start = i + 2
        return data_start, slots
    return None


# ── 머리행 → 컬럼 매핑 ────────────────────────────────────────────────────
# 회사마다 컬럼이 다르다(실측): KB금융 10개, 신한지주는 거기에 재직기간·임기만료일 2개 더.
# 그래서 **머리행 전문을 원문헤더 컬럼에 그대로 싣고**, 아는 이름만 따로 뽑는다.
OFFICER_FIELDS = (
    ("성명", ("성명", "성 명", "이름", "임원명")),
    ("성별", ("성별", "성 별")),
    ("출생년월", ("출생년월", "생년월", "출생년월일", "생년월일", "출생년월 일")),
    ("직위", ("직위", "직 위", "직책", "직 책", "직위명", "직책명", "직명")),
    ("등기임원여부", ("등기임원여부", "등기임원 여부", "등기임원", "등기여부")),
    ("상근여부", ("상근여부", "상근 여부", "상근", "상근/비상근 여부", "상근·비상근")),
    ("담당업무", ("담당업무", "담당 업무")),
    ("주요경력", ("주요경력", "주요 경력", "경력", "주요경력 및 이력")),
    ("소유주식수", ("소유주식수", "소유 주식수", "소유주식 수", "보유주식수")),
    ("최대주주와의관계", ("최대주주와의 관계", "최대주주와의관계", "최대주주와의 관계 등")),
    ("재직기간", ("재직기간", "재직 기간")),
    ("임기만료일", ("임기만료일", "임기 만료일", "임기만료")),
)
OFFICER_HEADER_KEY = "담당업무"        # 임원현황 표를 가르는 칸

EMPLOYEE_HEADER_KEYS = ("사업부문", "직원수", "직원 수", "정규직", "기간제근로자",
                        "1인평균급여액", "연간급여총액", "평균근속연수")

COMMITTEE_FIELDS = (
    ("위원회명", ("위원회명",)),
    ("구성", ("구성", "구 성", "구성 및 소속이사명")),
    ("소속이사명", ("소속이사명", "소속 이사명", "소속이사", "소속 이사")),
    ("설치목적및권한사항", ("설치목적 및 권한사항", "설치목적및권한사항", "설치목적",
                            "설치목적 및 권한")),
    ("비고", ("비고", "비 고")),
    ("구분", ("구분", "구 분")),
)

INTERLOCK_FIELDS = (
    ("겸직자", ("성명", "성 명", "겸직자", "겸직대상자", "겸직 대상자", "임원명")),
    ("겸직회사", ("대상회사", "대상 회사", "대상계열사", "대상 계열사", "겸임회사",
                  "겸직회사", "겸직 회사", "회사명", "임원 겸직 회사명")),
    ("겸직회사_직위", ("직위", "직 위", "직책", "직 책", "직위명", "직책명",
                       "소속회사 직위")),
    ("겸직일자", ("겸임일자", "선임일자", "선임일", "선임시기", "선임시기*", "겸직일자")),
    ("상근여부", ("상근여부", "상근 여부", "상근/비상근 여부", "상근·비상근", "비고", "비 고")),
)


def _map_columns(slots, fields):
    """컬럼별 이름 후보 → {필드명: 열 번호}. 먼저 나온 열이 이긴다."""
    out = {}
    norm = [[N(x) for x in cand] for cand in slots]
    for field, names in fields:
        for ci, cand in enumerate(norm):
            if field in out:
                break
            if any(c in names for c in cand):
                out[field] = ci
    return out


def _pick(row, colmap, field):
    ci = colmap.get(field)
    if ci is None or ci >= len(row):
        return ""
    return row[ci].get("text", "")


def _txt(row):
    return [c.get("text", "") for c in row]


def _label(slots):
    """산출물의 원문헤더 컬럼. 하위 머리행이 있으면 '부모·자식' 으로 적는다."""
    return " | ".join(c[-1] if len(c) > 1 else c[0] for c in slots)


# ── 1) 임원현황 ───────────────────────────────────────────────────────────
OFFICER_COLS = (["corp_label", "구분", "fy", "rcept_no", "report_nm", "rcept_dt",
                 "section_title", "table_index", "row_index"]
                + [f for f, _ in OFFICER_FIELDS]
                + ["동일인키", "문서내중복", "열수일치", "미매핑사유",
                   "원문헤더", "원문행"] + PROV_KEYS)


def _officer_rows(docs):
    """임원현황 표에서 임원 1인 1행. 담당업무는 손대지 않는다."""
    out, stats, seen_person = [], collections.Counter(), set()
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti) in sorted(d.tables):
            rows = _grid(d, (si, ti))
            hs = header_slots(rows, (OFFICER_HEADER_KEY,))
            if not hs:
                continue
            data_start, slots = hs
            colmap = _map_columns(slots, OFFICER_FIELDS)
            if "성명" not in colmap:
                stats[(d.corp_label, "성명칸없음")] += 1
                continue
            stats[(d.corp_label, "표")] += 1
            sec = d.sections.get(si, {})
            head = _label(slots)
            for row in rows[data_start:]:
                if not any((c.get("text") or "").strip() for c in row):
                    continue
                same = len(row) == len(slots)
                rec = dict(corp_label=d.corp_label, 구분=d.kind, fy=d.fy, rcept_no=rc,
                           report_nm=d.report_nm, rcept_dt=d.rcept_dt,
                           section_title=sec.get("title", ""), table_index=ti,
                           row_index=len(out), 열수일치="Y" if same else "N",
                           미매핑사유="" if same else
                           "머리행 %d칸 ≠ 데이터행 %d칸(병합셀) — 원문행을 보세요"
                           % (len(slots), len(row)),
                           원문헤더=head, 원문행=" | ".join(_txt(row)), **d.prov)
                for f, _ in OFFICER_FIELDS:
                    rec[f] = _pick(row, colmap, f) if same else ""
                if same and not (rec.get("성명") or "").strip():
                    continue          # 소계·구분 행
                # 한 문서가 같은 임원표를 두 번 싣는 일이 있다(실측: 신한지주 FY2025 는
                # 표2·표5 가 같은 20명이다). 등기·미등기 표가 따로인 경우(메리츠·우리)와
                # 구별해야 하므로 **행을 지우지 않고** 표시만 한다 — 지우면 그건 삭제다.
                key = (rc, (rec.get("성명") or "").strip(),
                       (rec.get("출생년월") or "").strip(),
                       (rec.get("직위") or "").strip())
                rec["동일인키"] = "%s|%s" % (rec.get("성명", ""), rec.get("출생년월", ""))
                rec["문서내중복"] = "Y" if key in seen_person else "N"
                seen_person.add(key)
                out.append(rec)
                stats[(d.corp_label, "행" if same else "열수불일치행")] += 1
    return out, stats


# ── 2) 직원현황 ───────────────────────────────────────────────────────────
EMP_COLS = ["corp_label", "구분", "fy", "rcept_no", "report_nm", "rcept_dt",
            "section_title", "table_index", "row_index",
            "원문헤더", "원문행", "비고_원문", "겸직인원_언급"] + PROV_KEYS

# 「자회사 소속 겸직임원 4명 : 인원수 포함 …」 / 「겸직임원 2명, 겸직직원 25명 포함」
_JIK_NOTE = re.compile(r"[^。.]*?겸직(?:임원|직원|자)[^。.]*")


def _employee_rows(docs):
    out = []
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti) in sorted(d.tables):
            rows = _grid(d, (si, ti))
            hs = header_slots(rows, EMPLOYEE_HEADER_KEYS)
            if not hs:
                continue
            data_start, slots = hs
            sec = d.sections.get(si, {})
            # 겸직 주석은 표 안의 어느 칸에나 있을 수 있다(대개 마지막 전폭 행).
            notes = []
            for row in rows:
                for c in row:
                    t = c.get("text") or ""
                    if "겸직" in t:
                        notes.extend(m.group(0).strip() for m in _JIK_NOTE.finditer(t))
            note = " / ".join(dict.fromkeys(n for n in notes if n))
            head = _label(slots)
            for row in rows[data_start:]:
                if not any((c.get("text") or "").strip() for c in row):
                    continue
                out.append(dict(corp_label=d.corp_label, 구분=d.kind, fy=d.fy, rcept_no=rc,
                                report_nm=d.report_nm, rcept_dt=d.rcept_dt,
                                section_title=sec.get("title", ""), table_index=ti,
                                row_index=len(out), 원문헤더=head,
                                원문행=" | ".join(_txt(row)), 비고_원문=note,
                                겸직인원_언급="Y" if note else "N", **d.prov))
    return out


# ── 3) 겸직현황 ───────────────────────────────────────────────────────────
JIK_COLS = ["corp_label", "구분", "fy", "rcept_no", "report_nm", "rcept_dt",
            "출처유형", "판별어휘", "출처섹션", "중복여부", "출처표수",
            "겸직자", "겸직회사", "겸직회사_직위", "겸직일자", "상근여부",
            "본인직위", "담당업무", "현직판별패턴", "겸직대상_금융회사여부",
            "원문헤더", "원문행"] + PROV_KEYS

_CURRENT = [(name, re.compile(pat)) for name, pat in config.CURRENT_POSITION_PATTERNS]
# 「신한은행 부행장 겸직, 2023.07~현재」 / 「○○ 겸임(2024.01~현재)」
_CAREER_JIK = re.compile(r"([^()（）,、;·]{2,40}?)\s*"
                         r"(?:부행장|행장|사장|부사장|전무|상무|대표이사|이사|감사|"
                         r"본부장|그룹장|단장|실장|부문장|위원|고문)?\s*"
                         r"(겸직|겸임)")


def _is_financial(name):
    return "Y" if any(h in (name or "") for h in config.FINANCIAL_COMPANY_HINTS) else "N"


def _interlock_from_tables(docs):
    """⑴ 머리행이 겸직 표인 것. 판별어휘를 행마다 남긴다."""
    out, vocab = [], collections.Counter()
    all_names = set()
    for _f, names in INTERLOCK_FIELDS:
        all_names |= set(names)
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti) in sorted(d.tables):
            rows = _grid(d, (si, ti))
            if not rows:
                continue
            v = INTERLOCK_HEADER(_as_table(rows), N)
            if not v:
                continue
            vocab[(d.corp_label, v)] += 1
            hs = header_slots(rows, tuple(all_names))
            if not hs:
                continue
            data_start, slots = hs
            colmap = _map_columns(slots, INTERLOCK_FIELDS)
            sec = d.sections.get(si, {})
            head = _label(slots)
            for row in rows[data_start:]:
                if not any((c.get("text") or "").strip() for c in row):
                    continue
                same = len(row) == len(slots)
                rec = dict(corp_label=d.corp_label, 구분=d.kind, fy=d.fy, rcept_no=rc,
                           report_nm=d.report_nm, rcept_dt=d.rcept_dt,
                           출처유형="겸직표", 판별어휘=v,
                           출처섹션=sec.get("title", ""), 중복여부="", 출처표수=1,
                           본인직위="", 담당업무="", 현직판별패턴="",
                           원문헤더=head, 원문행=" | ".join(_txt(row)), **d.prov)
                for f, _ in INTERLOCK_FIELDS:
                    rec[f] = _pick(row, colmap, f) if same else ""
                if not (rec.get("겸직자") or "").strip():
                    rec["겸직자"] = rec["겸직회사"] = rec["겸직회사_직위"] = ""
                    rec["중복여부"] = "미매핑"
                rec["겸직대상_금융회사여부"] = _is_financial(rec.get("겸직회사"))
                out.append(rec)
    return out, vocab


def _interlock_from_career(officers):
    """⑵ 임원현황 「주요경력」 칸의 현직 겸직 서술.

    신한지주처럼 겸직을 표가 아니라 칸 안 서술로만 쓰는 곳이 있다. 前職 오탐(한국금융
    지주의 '국민대학교 … 겸임교수')을 막으려고 두 겹으로 거른다 — ⑴ 현직 패턴에
    걸릴 것, ⑵ 겸직 대상이 금융회사인지 Y/N 을 남길 것. **N 을 자동으로 버리지 않는다.**
    """
    out = []
    for o in officers:
        career = o.get("주요경력") or ""
        if "겸직" not in career and "겸임" not in career:
            continue
        pats = [name for name, rx in _CURRENT if rx.search(career)]
        if not pats:
            continue                   # 현직 표기가 없으면 前職이다 — 세지 않는다
        for m in _CAREER_JIK.finditer(career):
            comp = (m.group(1) or "").strip(" ('\"‘’“”[]")
            if not comp or len(comp) < 2:
                continue
            out.append(dict(
                corp_label=o["corp_label"], 구분=o["구분"], fy=o["fy"],
                rcept_no=o["rcept_no"], report_nm=o["report_nm"], rcept_dt=o["rcept_dt"],
                출처유형="경력란서술", 판별어휘=m.group(2), 출처섹션=o["section_title"],
                중복여부="", 출처표수=1,
                겸직자=o.get("성명", ""), 겸직회사=comp, 겸직회사_직위="",
                겸직일자="", 상근여부="",
                본인직위=o.get("직위", ""), 담당업무=o.get("담당업무", ""),
                현직판별패턴="|".join(pats),
                겸직대상_금융회사여부=_is_financial(comp),
                원문헤더=o.get("원문헤더", ""), 원문행=career,
                **{k: o.get(k, "") for k in PROV_KEYS}))
    return out


def _dedupe_interlock(rows):
    """겸직자·겸직회사·겸직회사_직위가 **셋 다 같을 때만** 한 행으로 합친다.

    하나라도 다르면 별도 행으로 둔다(사용자 결정, 2026-09-22) — 두 섹션의 기준일이 달라
    직위가 바뀌었을 수 있는데 그걸 합쳐 버리면 변화가 사라진다. 합친 행은 출처섹션에
    둘 다 적고, 합친 건수와 한쪽에만 있던 건수를 법인별로 센다.
    """
    merged, order, stat = {}, [], collections.Counter()
    for r in rows:
        if r.get("출처유형") != "겸직표":
            continue
        key = (r["corp_label"], r["rcept_no"],
               (r.get("겸직자") or "").strip(),
               (r.get("겸직회사") or "").strip(),
               (r.get("겸직회사_직위") or "").strip())
        if key in merged:
            m = merged[key]
            secs = [s for s in m["출처섹션"].split(" | ") if s]
            if r["출처섹션"] and r["출처섹션"] not in secs:
                secs.append(r["출처섹션"])
            m["출처섹션"] = " | ".join(secs)
            m["출처표수"] = int(m["출처표수"]) + 1
            if r.get("판별어휘") and r["판별어휘"] not in m["판별어휘"].split(" | "):
                m["판별어휘"] += " | " + r["판별어휘"]
        else:
            merged[key] = dict(r)
            order.append(key)
    out = []
    for key in order:
        m = merged[key]
        nsec = len([s for s in m["출처섹션"].split(" | ") if s])
        m["중복여부"] = m["중복여부"] or ("병합" if nsec > 1 else "단독")
        stat[(m["corp_label"], "병합" if nsec > 1 else "단독")] += 1
        if nsec <= 1:
            stat[(m["corp_label"], "단독:" + (m["출처섹션"] or "(무)"))] += 1
        out.append(m)
    return out, stat


# ── 4) 위원회 ─────────────────────────────────────────────────────────────
CMT_COLS = ["corp_label", "구분", "fy", "rcept_no", "report_nm", "rcept_dt",
            "section_title", "table_index", "row_index"] \
    + [f for f, _ in COMMITTEE_FIELDS] \
    + ["열수일치", "원문헤더", "원문행"] + PROV_KEYS


def _committee_rows(docs):
    out = []
    for rc in sorted(docs):
        d = docs[rc]
        for (si, ti) in sorted(d.tables):
            rows = _grid(d, (si, ti))
            if not rows or not COMMITTEE_HEADER(_as_table(rows), N):
                continue
            hs = header_slots(rows, ("위원회명",))
            if not hs:
                continue
            data_start, slots = hs
            colmap = _map_columns(slots, COMMITTEE_FIELDS)
            sec = d.sections.get(si, {})
            head = _label(slots)
            for row in rows[data_start:]:
                if not any((c.get("text") or "").strip() for c in row):
                    continue
                same = len(row) == len(slots)
                rec = dict(corp_label=d.corp_label, 구분=d.kind, fy=d.fy, rcept_no=rc,
                           report_nm=d.report_nm, rcept_dt=d.rcept_dt,
                           section_title=sec.get("title", ""), table_index=ti,
                           row_index=len(out), 열수일치="Y" if same else "N",
                           원문헤더=head, 원문행=" | ".join(_txt(row)), **d.prov)
                for f, _ in COMMITTEE_FIELDS:
                    rec[f] = _pick(row, colmap, f) if same else ""
                out.append(rec)
    return out


# ── 5) 임원 ↔ 겸직 결합 ───────────────────────────────────────────────────
JOIN_COLS = ["corp_label", "구분", "fy", "rcept_no", "조인방식",
             "겸직자", "겸직회사", "겸직회사_직위", "출처유형", "판별어휘",
             "임원_성명", "임원_출생년월", "임원_직위", "임원_담당업무", "임원_등기임원여부",
             "겸직대상_금융회사여부", "미결합사유"]


def _join(officers, jiks):
    """겸직 행 ↔ 임원 행. 성명 + 출생년월이 둘 다 맞으면 완전일치, 성명만 맞으면 성명만.

    **겸직 표에는 출생년월이 없다** — 그래서 대부분 '성명만' 이 된다. 동명이인이 있으면
    결합하지 않고 사유를 적는다(보조 키가 없으므로 고르는 것은 추정이다).
    """
    by_name = collections.defaultdict(list)
    for o in officers:
        nm = (o.get("성명") or "").strip()
        if nm:
            by_name[(o["corp_label"], o["rcept_no"], nm)].append(o)
    out = []
    for j in jiks:
        nm = (j.get("겸직자") or "").strip()
        cands = by_name.get((j["corp_label"], j["rcept_no"], nm), [])
        rec = dict(corp_label=j["corp_label"], 구분=j["구분"], fy=j["fy"],
                   rcept_no=j["rcept_no"], 겸직자=nm,
                   겸직회사=j.get("겸직회사", ""), 겸직회사_직위=j.get("겸직회사_직위", ""),
                   출처유형=j.get("출처유형", ""), 판별어휘=j.get("판별어휘", ""),
                   겸직대상_금융회사여부=j.get("겸직대상_금융회사여부", ""),
                   임원_성명="", 임원_출생년월="", 임원_직위="", 임원_담당업무="",
                   임원_등기임원여부="", 미결합사유="")
        if not nm:
            rec["조인방식"] = "미결합"
            rec["미결합사유"] = "겸직자 성명 미매핑(병합셀) — 겸직현황_정리.csv 원문행 참조"
        elif len(cands) == 1:
            o = cands[0]
            rec["조인방식"] = "완전일치" if (o.get("출생년월") or "").strip() else "성명만"
            rec.update(임원_성명=o.get("성명", ""), 임원_출생년월=o.get("출생년월", ""),
                       임원_직위=o.get("직위", ""), 임원_담당업무=o.get("담당업무", ""),
                       임원_등기임원여부=o.get("등기임원여부", ""))
        elif len(cands) > 1:
            rec["조인방식"] = "미결합"
            rec["미결합사유"] = ("같은 문서에 동명 임원 %d명 — 겸직 표에 출생년월이 없어 "
                                 "고를 수 없다(고르면 추정이다)" % len(cands))
        else:
            rec["조인방식"] = "미결합"
            rec["미결합사유"] = "같은 문서의 임원현황 표에 해당 성명이 없다"
        out.append(rec)
    return out


# ── 6) 지주 ↔ 자회사 임원 명부 교집합 ─────────────────────────────────────
ROSTER_COLS = ["지주", "자회사", "fy", "성명", "출생년월", "조인키",
               "지주_직위", "지주_담당업무", "지주_등기임원여부",
               "자회사_직위", "자회사_담당업무", "자회사_등기임원여부",
               "지주_rcept_no", "자회사_rcept_no", "겸직낱말_지주경력란"]

# 지주 ↔ 자회사 짝. 낱말이 아니라 명부로 재기 위한 관측 대상이다.
ROSTER_PAIRS = (
    ("신한지주", "신한은행(구)"),
    ("신한지주", "신한라이프생명보험"),
    ("KB금융", "KB손해보험"),
    ("KB금융", "KB라이프생명보험"),
    ("메리츠금융지주", "메리츠화재해상보험"),
    ("우리금융지주", "동양생명보험"),
    ("하나금융지주", "하나생명보험"),
)


def _roster_intersection(officers):
    """같은 사람이 지주·자회사 양쪽 임원표에 실린 건.

    **낱말 매칭으로는 규모를 잴 수 없다**(실측): 신한은행 임원표에 '겸직·겸임' 낱말은
    FY2023~25 전부 0회인데, 박현주·최혁재는 양쪽에 다 실려 있다. 같은 사람이 양쪽에
    다른 직위·다른 담당업무명으로 실리고, 겸직이라는 사실은 지주 쪽 경력란에만 적힌다.
    낱말 기준 2명 vs 명부 교집합 5명 — 2.5배 차이다.
    """
    idx = collections.defaultdict(list)
    for o in officers:
        nm = (o.get("성명") or "").strip()
        if nm:
            idx[(o["corp_label"], o["fy"])].append(o)
    out, seen_pair = [], set()
    for hold, sub in ROSTER_PAIRS:
        fys = {o["fy"] for o in officers if o["corp_label"] in (hold, sub)}
        for fy in sorted(fys):
            hs = idx.get((hold, fy), [])
            ss = idx.get((sub, fy), [])
            if not hs or not ss:
                continue
            sub_by = collections.defaultdict(list)
            for o in ss:
                sub_by[((o.get("성명") or "").strip(),
                        (o.get("출생년월") or "").strip())].append(o)
            sub_by_name = collections.defaultdict(list)
            for o in ss:
                sub_by_name[(o.get("성명") or "").strip()].append(o)
            for h in hs:
                nm = (h.get("성명") or "").strip()
                bd = (h.get("출생년월") or "").strip()
                hit, key = [], ""
                if bd and sub_by.get((nm, bd)):
                    hit, key = sub_by[(nm, bd)], "성명+출생년월"
                elif sub_by_name.get(nm):
                    hit, key = sub_by_name[nm], "성명만"
                for s in hit:
                    dk = (hold, sub, fy, nm, bd, s.get("직위", ""))
                    if dk in seen_pair:
                        continue     # 같은 임원표가 문서 안에 두 번 실린 경우
                    seen_pair.add(dk)
                    out.append(dict(
                        지주=hold, 자회사=sub, fy=fy, 성명=nm, 출생년월=bd, 조인키=key,
                        지주_직위=h.get("직위", ""), 지주_담당업무=h.get("담당업무", ""),
                        지주_등기임원여부=h.get("등기임원여부", ""),
                        자회사_직위=s.get("직위", ""), 자회사_담당업무=s.get("담당업무", ""),
                        자회사_등기임원여부=s.get("등기임원여부", ""),
                        지주_rcept_no=h["rcept_no"], 자회사_rcept_no=s["rcept_no"],
                        겸직낱말_지주경력란="Y" if ("겸직" in (h.get("주요경력") or "")
                                                   or "겸임" in (h.get("주요경력") or ""))
                        else "N"))
    return out


# ── 7) 설립 첫해 임원 구성 ────────────────────────────────────────────────
FIRST_COLS = ["corp_label", "fy", "rcept_no", "report_nm", "rcept_dt", "설립첫해구분",
              "성명", "직위", "등기임원여부", "상근여부", "담당업무_원문", "주요경력",
              "출생년월", "성별", "원문헤더", "원문행"] + PROV_KEYS


def _first_year_rows(officers, docs):
    """출범 첫 사업보고서의 임원 전원과 담당업무 원문.

    라이나가 출범 시점에 어떤 임원 구성으로 시작할지 정할 때 가장 직접적인 참고다 —
    어떤 자리를 먼저 만들고 무엇을 겸하게 했는지가 이 한 표에 다 있다.
    """
    first = {}
    for rc, d in docs.items():
        want = config.FIRST_YEAR_5CHA.get(d.corp_label)
        if want and d.fy in want:
            first[rc] = "설립첫해(지정)"
    # 신규 지주 4곳은 phase2 가 '출범 직후 첫 사업보고서' 로 받아 둔다 — 법인별 최소 연도.
    by_corp = collections.defaultdict(list)
    for rc, d in docs.items():
        if d.corp_label in config.NEW_CORPS_5CHA and d.fy:
            by_corp[d.corp_label].append((d.fy, rc))
    for lab, items in by_corp.items():
        items.sort()
        if items:
            first.setdefault(items[0][1], "설립첫해(최소연도)")
    out = []
    for o in officers:
        tag = first.get(o["rcept_no"])
        if not tag:
            continue
        rec = {k: o.get(k, "") for k in ("corp_label", "fy", "rcept_no", "report_nm",
                                         "rcept_dt", "성명", "직위", "등기임원여부",
                                         "상근여부", "주요경력", "출생년월", "성별",
                                         "원문헤더", "원문행")}
        rec["설립첫해구분"] = tag
        rec["담당업무_원문"] = o.get("담당업무", "")
        rec.update({k: o.get(k, "") for k in PROV_KEYS})
        out.append(rec)
    return out


# ── 진입점 ────────────────────────────────────────────────────────────────
def build(out_dir, handoff_dir, result=None):
    result = result if result is not None else {"paths": [], "counts": {}, "notes": []}
    docs = scan(out_dir)
    result["notes"].append("5차 대상 문서 %d건 (법인 %d곳)"
                           % (len(docs), len({d.corp_label for d in docs.values()})))

    officers, ostat = _officer_rows(docs)
    _emit(result, handoff_dir, "임원현황.csv", officers, OFFICER_COLS)

    _emit(result, handoff_dir, "직원현황.csv", _employee_rows(docs), EMP_COLS)

    tbl_jik, vocab = _interlock_from_tables(docs)
    deduped, dstat = _dedupe_interlock(tbl_jik)
    career_jik = _interlock_from_career(officers)
    jiks = deduped + career_jik
    _emit(result, handoff_dir, "겸직현황_정리.csv", jiks, JIK_COLS)

    _emit(result, handoff_dir, "위원회현황.csv", _committee_rows(docs), CMT_COLS)
    _emit(result, handoff_dir, "임원_겸직_결합.csv", _join(officers, jiks), JOIN_COLS)
    _emit(result, handoff_dir, "지주_자회사_임원명부교집합.csv",
          _roster_intersection(officers), ROSTER_COLS)
    _emit(result, handoff_dir, "설립첫해_임원구성.csv",
          _first_year_rows(officers, docs), FIRST_COLS)

    result["stats_5cha"] = {"officer": ostat, "vocab": vocab, "dedupe": dstat}
    return result
