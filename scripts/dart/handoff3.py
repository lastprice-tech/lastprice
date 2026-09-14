# -*- coding: utf-8 -*-
"""3차 인계 산출물 — "지주 아래 보험사를 두는 구조"의 국내 실물.

handoff.py 와 같은 규율을 따른다: dart_out/ 아래 파일만 읽는 순수 함수이고
네트워크도 API 키도 쓰지 않는다. 못 읽은 값은 빈칸으로 두고 사유를 notes 에 남긴다.

여기서 만드는 것
  1) 한화생명_한화손보_지분추이.csv  — 보통주 지분율 추이 + 증자 이력
  2) 한화_자본총계추이.csv           — 생명이 손보에 출자할 때 생명 자본이 어떻게 움직이나
  3) 겸직_업무위탁.csv               — 세 가지 지배구조의 겸직·수탁 표를 셀 단위로
"""
from __future__ import annotations

import csv
import os
import re

import config
import docparse
import emit

csv.field_size_limit(10 ** 9)

PROV_KEYS = ["fetched_at", "status", "raw_path", "raw_sha256"]


def _read(out_dir, name):
    p = os.path.join(out_dir, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ── 1) 한화생명 → 한화손보 지분율 추이 ────────────────────────────────────
# 실측으로 확인한 함정 4종. 부분일치로 거르면 아래가 전부 섞여 들어온다.
#   '한화손해보험'                  51.36%  ← 이것만 맞다
#   '한화손해보험 (상장)'            51.36%  ← 2017~2019년. 접미사 때문에 정확일치 실패
#   '한화손해보험(유상증자)_전환우선주'  100%  ← 보통주가 아니다
#   '한화손해사정'                  100%   ← 보험사가 아니다. 부분일치로 가장 먼저 걸린다
#   ' 한화손해보험 '                       ← 앞뒤 공백이 연도마다 다르다
# 제외한 행을 숨기지 않는다 — 포함여부/제외사유를 달아 같은 파일에 싣는다.
_SUFFIX_RE = re.compile(r"\((?:상장|비상장|유가증권시장|코스닥|코넥스)\)\s*$")


def norm_child(name):
    """매칭용 정규화. 출력에는 항상 원문(child_name)을 쓴다."""
    n = docparse.normalize_for_match(name or "")
    n = _SUFFIX_RE.sub("", n).strip()
    return n.replace(" ", "")


def _exclude_reason(raw, norm, want):
    if norm == want:
        return ""
    if "전환우선주" in norm or "우선주" in norm:
        return "보통주가 아님(전환우선주)"
    if "손해사정" in norm:
        return "손해사정 법인(보험사 아님)"
    if want in norm:
        return "이름이 %s 를 포함하지만 정확일치가 아님" % want
    return "대상 아님"


def build_stake(out_dir, handoff_dir, result, parent="한화생명보험", child="한화손해보험"):
    rows12 = _read(out_dir, "12_지분관계.csv")
    rows06 = _read(out_dir, "06_증자감자현황.csv")
    if rows12 is None:
        result["skipped"].append("한화생명_한화손보_지분추이.csv: 12_지분관계.csv 가 없음")
        return
    want = norm_child(child)
    out = []

    for r in rows12:
        if (r.get("parent_label") or "") != parent:
            continue
        raw = r.get("child_name") or ""
        n = norm_child(raw)
        # 순진한 부분일치가 잡았을 것을 전부 담는다. 제외한 것도 사유와 함께 보여야
        # "검토하고 뺐다"가 되고, 조용히 사라지면 뺀 줄도 모른다.
        # want[:4] = '한화손해' → '한화손해사정' 도 여기서 걸려 N 으로 기록된다.
        if want not in n and not n.startswith(want[:4]):
            continue
        reason = _exclude_reason(raw, n, want)
        row = dict(
            구분="지분율", corp_label=parent, 상대법인=child,
            bsns_year=r.get("bsns_year", ""), reprt_code=r.get("reprt_code", ""),
            child_name=raw, child_name_norm=n,
            포함여부="Y" if not reason else "N", 제외사유=reason,
            기말지분율=r.get("trmend_qota_rt", ""), 기초지분율=r.get("bsis_qota_rt", ""),
            기말수량=r.get("trmend_qy", ""), 기말장부가=r.get("trmend_acntbk_amount", ""),
            최초취득일=r.get("first_acqs_de", ""), 최초취득금액=r.get("first_acqs_amount", ""),
            child_match_method=r.get("child_match_method", ""),
            발행일="", 증자형태="", 주식종류="", 수량="", 주당발행가액="", 주당액면가액="",
            납입액_계산="", value_source="api",
        )
        row.update({k: r.get(k, "") for k in PROV_KEYS})
        row["rcept_no"] = r.get("rcept_no", "")
        out.append(row)

    # 증자 이력. 같은 이벤트가 연도별 보고서마다 되풀이 보고되므로 (발행일, 종류, 수량)
    # 으로 묶는다. 어느 보고서에서 왔는지는 rcept_no 목록으로 남겨 추적이 끊기지 않게 한다.
    if rows06 is not None:
        seen = {}
        for r in rows06:
            if (r.get("corp_label") or "") != child:
                continue
            de = (r.get("isu_dcrs_de") or "").strip()
            if de in ("", "-"):
                continue
            key = (de, r.get("isu_dcrs_stock_knd", ""), r.get("isu_dcrs_qy", ""))
            if key in seen:
                seen[key]["보고서_rcept_no"] += "|" + (r.get("rcept_no") or "")
                continue
            qty = _num(r.get("isu_dcrs_qy"))
            price = _num(r.get("isu_dcrs_mstvdv_amount"))
            # 수량 × 주당발행가액. 둘 중 하나라도 못 읽으면 계산하지 않고 빈칸으로 둔다.
            calc = str(qty * price) if (qty is not None and price is not None) else ""
            row = dict(
                구분="증자", corp_label=child, 상대법인=parent,
                bsns_year=r.get("bsns_year", ""), reprt_code=r.get("reprt_code", ""),
                child_name="", child_name_norm="", 포함여부="Y", 제외사유="",
                기말지분율="", 기초지분율="", 기말수량="", 기말장부가="",
                최초취득일="", 최초취득금액="", child_match_method="",
                발행일=de, 증자형태=r.get("isu_dcrs_stle", ""),
                주식종류=r.get("isu_dcrs_stock_knd", ""),
                수량=r.get("isu_dcrs_qy", ""),
                주당발행가액=r.get("isu_dcrs_mstvdv_amount", ""),
                주당액면가액=r.get("isu_dcrs_mstvdv_fval_amount", ""),
                납입액_계산=calc,
                value_source="api" if not calc else "api+computed",
                보고서_rcept_no=r.get("rcept_no", ""),
            )
            row.update({k: r.get(k, "") for k in PROV_KEYS})
            row["rcept_no"] = r.get("rcept_no", "")
            seen[key] = row
        out.extend(seen.values())

    out.sort(key=lambda r: (r.get("bsns_year") or "", r["구분"], r.get("발행일") or "",
                            r.get("child_name") or ""))
    cols = ["구분", "corp_label", "상대법인", "bsns_year", "reprt_code",
            "child_name", "child_name_norm", "포함여부", "제외사유",
            "기말지분율", "기초지분율", "기말수량", "기말장부가",
            "최초취득일", "최초취득금액", "child_match_method",
            "발행일", "증자형태", "주식종류", "수량", "주당발행가액", "주당액면가액",
            "납입액_계산", "value_source", "rcept_no", "보고서_rcept_no"] + PROV_KEYS
    path = os.path.join(handoff_dir, "한화생명_한화손보_지분추이.csv")
    _write(path, out, cols)
    result["paths"].append(path)
    result["counts"][os.path.basename(path)] = len(out)
    inc = sum(1 for r in out if r["구분"] == "지분율" and r["포함여부"] == "Y")
    exc = sum(1 for r in out if r["구분"] == "지분율" and r["포함여부"] == "N")
    result["notes"].append(
        "한화생명→한화손보: 보통주 지분율 행 %d개 · 부분일치로 걸렸으나 제외한 행 %d개"
        "(숨기지 않고 제외사유와 함께 수록) · 증자 이벤트 %d건"
        % (inc, exc, sum(1 for r in out if r["구분"] == "증자")))
    # 원문 오기를 고치지 않고 싣는다 — 사실만 기록한다.
    dates = {r["최초취득일"] for r in out if r["포함여부"] == "Y" and r["최초취득일"]}
    if len(dates) > 1:
        result["notes"].append(
            "한화생명→한화손보 최초취득일이 보고서마다 다르다: %s — DART 원문 그대로 싣고 "
            "고치지 않았다" % " / ".join(sorted(dates)))


def _num(v):
    if v is None:
        return None
    t = str(v).replace(",", "").strip()
    if t in ("", "-"):
        return None
    try:
        return int(t)
    except ValueError:
        return None


def _write(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ── 2) 한화 자본총계 추이 ─────────────────────────────────────────────────
# 계정과목명은 회사·연도마다 다르다. 매핑하지 않고 account_nm 원문 그대로 싣고
# distinct 목록을 notes 에 남긴다(브리핑 규칙 ⑤).
EQUITY_KEYWORDS = ("자본총계", "자본금", "자본잉여금", "이익잉여금")


def build_equity(out_dir, handoff_dir, result, labels=("한화생명보험", "한화손해보험")):
    rows = _read(out_dir, "03_재무제표.csv")
    if rows is None:
        result["skipped"].append("한화_자본총계추이.csv: 03_재무제표.csv 가 없음")
        return
    out, seen_nm = [], set()
    for r in rows:
        if (r.get("corp_label") or "") not in labels:
            continue
        nm = r.get("account_nm") or ""
        if not any(k in nm for k in EQUITY_KEYWORDS):
            continue
        # 자본변동표(SCE)는 같은 계정이 여러 줄이라 추이로 읽으면 틀린다. 재무상태표만.
        if (r.get("sj_div") or "") != "BS":
            continue
        seen_nm.add(nm)
        row = {k: r.get(k, "") for k in
               ("corp_label", "bsns_year", "reprt_code", "reprt_nm", "fs_div",
                "accounting_std_inferred", "comparability_break", "sj_div", "sj_nm",
                "account_id", "account_nm", "currency",
                "thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount", "ord")}
        row["value_source"] = "api"
        row.update({k: r.get(k, "") for k in PROV_KEYS})
        row["rcept_no"] = r.get("rcept_no", "")
        out.append(row)
    out.sort(key=lambda r: (r["corp_label"], r["bsns_year"], r["fs_div"],
                            r.get("ord") or "", r["account_nm"]))
    cols = ["corp_label", "bsns_year", "reprt_code", "reprt_nm", "fs_div",
            "accounting_std_inferred", "comparability_break", "sj_div", "sj_nm",
            "account_id", "account_nm", "currency",
            "thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount", "ord",
            "value_source", "rcept_no"] + PROV_KEYS
    path = os.path.join(handoff_dir, "한화_자본총계추이.csv")
    _write(path, out, cols)
    result["paths"].append(path)
    result["counts"][os.path.basename(path)] = len(out)
    result["notes"].append(
        "한화 자본총계: %d행 / 계정과목명 %d종 — 매핑하지 않고 원문 그대로 실었다: %s"
        % (len(out), len(seen_nm), " · ".join(sorted(seen_nm))))


# ── 3) 겸직·업무위탁 ──────────────────────────────────────────────────────
# 세 가지 지배구조를 나란히 본다. 「겸직」·「업무위탁」이라는 제목의 섹션은 없고
# 표 안에만 있다(실측) — 그래서 표 내용 키워드로 고른다.
STRUCTURES = {
    "지주(신한)": ["신한지주", "신한라이프생명보험", "신한이지손해보험"],
    "지주(KB)": ["KB금융", "KB손해보험", "KB라이프생명보험"],
    "비지주 형제(삼성)": ["삼성생명보험", "삼성화재해상보험"],
    "비지주 모자(한화)": ["한화생명보험", "한화손해보험"],
}
JIK_TABLE_KEYWORDS = ("겸직", "수탁", "업무위탁", "위탁계약")
JIK_SECTION_HINTS = ("임원 및 직원", "대주주 등과의 거래", "임원의 보수")
# 상대 회사가 겸직 표에 등장하는지 — 모자 구조에서 이것이 핵심 질문이다.
COUNTERPART = {"한화생명보험": "한화손해보험", "한화손해보험": "한화생명보험",
               "삼성생명보험": "삼성화재", "삼성화재해상보험": "삼성생명"}


def build_interlock(out_dir, handoff_dir, result):
    src = os.path.join(out_dir, "11_원문추출.csv")
    if not os.path.exists(src):
        result["skipped"].append("겸직_업무위탁.csv: 11_원문추출.csv 가 없음")
        return
    label2struct = {l: s for s, ls in STRUCTURES.items() for l in ls}
    # 각 법인의 '가장 최근 보고서' 하나만 본다. 연도별로 다 담으면 같은 표가 반복된다.
    latest = {}
    wanted_tables = {}      # (rcept_no, section_index, table_index) -> 매칭 낱말
    doc_meta = {}
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lab = r.get("corp_label") or ""
            if lab not in label2struct:
                continue
            rc, dt = r.get("rcept_no", ""), r.get("rcept_dt", "")
            if latest.get(lab, ("", ""))[1] < dt:
                latest[lab] = (rc, dt)
            doc_meta.setdefault(rc, dict(corp_label=lab, rcept_dt=dt,
                                         report_nm=r.get("report_nm", "")))
            if r.get("kind") != "table":
                continue
            blob = r.get("cell_text") or ""
            hits = [k for k in JIK_TABLE_KEYWORDS if k in blob]
            if not hits and not any(h in (r.get("section_title") or "")
                                    for h in JIK_SECTION_HINTS):
                continue
            key = (rc, r.get("section_index", ""), r.get("table_index", ""))
            if hits:
                wanted_tables.setdefault(key, set()).update(hits)
            else:
                wanted_tables.setdefault(key, set())

    keep_rc = {rc for rc, _ in latest.values()}
    out = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rc = r.get("rcept_no", "")
            if rc not in keep_rc or r.get("kind") != "table":
                continue
            key = (rc, r.get("section_index", ""), r.get("table_index", ""))
            if key not in wanted_tables:
                continue
            lab = r.get("corp_label") or ""
            cp = COUNTERPART.get(lab, "")
            cell = r.get("cell_text") or ""
            row = {k: r.get(k, "") for k in
                   ("corp_label", "rcept_no", "rcept_dt", "report_nm",
                    "section_index", "section_title", "section_title_raw",
                    "table_index", "table_matched_keyword", "table_n_rows",
                    "row_index", "cell_ord", "cell_tag", "rowspan", "colspan",
                    "unit_hint", "cell_text", "text_path")}
            row["구조"] = label2struct.get(lab, "")
            row["표_매칭낱말"] = "|".join(sorted(wanted_tables[key]))
            row["상대회사"] = cp
            row["상대회사_언급"] = "Y" if (cp and cp in cell) else ""
            row["value_source"] = "api"
            row.update({k: r.get(k, "") for k in PROV_KEYS})
            out.append(row)

    # 한 표도 안 걸린 법인은 빈손으로 두지 않고 전문 경로를 남긴다.
    got = {r["corp_label"] for r in out}
    for lab, (rc, dt) in sorted(latest.items()):
        if lab in got:
            continue
        m = doc_meta.get(rc, {})
        out.append({"구조": label2struct.get(lab, ""), "corp_label": lab,
                    "rcept_no": rc, "rcept_dt": dt,
                    "report_nm": m.get("report_nm", ""),
                    "section_index": "", "section_title": "(겸직·수탁 표 없음)",
                    "표_매칭낱말": "", "cell_text": "",
                    "text_path": "text/%s/_full.txt" % rc, "value_source": "api"})
        result["notes"].append(
            "겸직_업무위탁: %s %s 에 겸직·수탁 표가 한 개도 없음 — 전문 경로만 남김"
            % (lab, rc))

    order = list(STRUCTURES)
    out.sort(key=lambda r: (order.index(r["구조"]) if r["구조"] in order else 99,
                            r["corp_label"], r.get("section_index") or "",
                            r.get("table_index") or "", r.get("row_index") or "",
                            r.get("cell_ord") or ""))
    cols = ["구조", "corp_label", "상대회사", "상대회사_언급", "rcept_no", "rcept_dt",
            "report_nm", "section_index", "section_title", "section_title_raw",
            "table_index", "표_매칭낱말", "table_matched_keyword", "table_n_rows",
            "row_index", "cell_ord", "cell_tag", "rowspan", "colspan",
            "unit_hint", "cell_text", "text_path", "value_source"] + PROV_KEYS
    path = os.path.join(handoff_dir, "겸직_업무위탁.csv")
    _write(path, out, cols)
    result["paths"].append(path)
    result["counts"][os.path.basename(path)] = len(out)

    # ★ 모자 구조에서 상대 회사가 겸직 표에 나오는가 — 없으면 0으로 보고한다.
    for lab, cp in sorted(COUNTERPART.items()):
        n = sum(1 for r in out if r.get("corp_label") == lab and r.get("상대회사_언급") == "Y")
        jik = sum(1 for r in out if r.get("corp_label") == lab
                  and "겸직" in (r.get("표_매칭낱말") or ""))
        result["notes"].append(
            "겸직_업무위탁: %s — 겸직 표 셀 %d개 중 상대(%s) 언급 %d개"
            % (lab, jik, cp, n))


# ── 4) 금감원 정정명령 전후 차이 ──────────────────────────────────────────
# 우리 2026 건에 금감원이 2026-05-26 정정명령을 부과했다(20260526100048).
# 원문 요지: "2026.5.14. 제출된 주요사항보고서(주식교환ㆍ이전 결정)에 대한 심사결과
#   신고서의 내용 중 **기타 투자판단과 관련한 중요사항** 등과 관련하여 중요한 누락
#   (또는 허위의 기재)이 있어" — 근거 자본시장법 제164조.
# 당국이 무엇을 더 쓰라고 했는지는 전후 정정본의 섹션별 분량 차이로 드러난다.
# **어느 쪽이 옳은지 판단하지 않는다.** 글자 수만 나란히 놓는다.
AMEND_PAIRS = [
    dict(사건="우리 2026 동양생명·ABL생명 편입", 축="주요사항보고서(동양생명)",
         before="20260514001231", after="20260703000555", 명령="20260526100048"),
    dict(사건="우리 2026 동양생명·ABL생명 편입", 축="증권신고서(우리금융지주)",
         before="20260514001490", after="20260703000474", 명령="20260526100048"),
]


def _doc_sections(out_dir, rcept_no):
    """{정규화제목: (원문제목, 글자수합, 등장횟수, 표수합)} — 못 읽으면 None."""
    p = os.path.join(out_dir, "raw", "document", "%s.zip" % rcept_no)
    if not os.path.exists(p):
        return None, "raw/document/%s.zip 이 없음" % rcept_no
    try:
        info = docparse.read_zip(open(p, "rb").read(), rcept_no)
    except Exception as e:                                   # noqa: BLE001
        return None, "ZIP 열기 실패(%s)" % type(e).__name__
    if not info.get("text"):
        return None, "본문 없음(%s)" % (info.get("member_selected") or "멤버 없음")
    secs, err = docparse.parse_document(info["text"])
    agg = {}
    for s in secs:
        key = s["title"]
        n = len(docparse.section_body(s))
        cur = agg.get(key)
        if cur:
            agg[key] = (cur[0], cur[1] + n, cur[2] + 1, cur[3] + len(s["tables"]))
        else:
            agg[key] = (s["title_raw"], n, 1, len(s["tables"]))
    return agg, err


def build_amendment_diff(out_dir, handoff_dir, result):
    out = []
    for pair in AMEND_PAIRS:
        a, aerr = _doc_sections(out_dir, pair["before"])
        b, berr = _doc_sections(out_dir, pair["after"])
        if a is None or b is None:
            result["notes"].append(
                "정정명령 전후차이: %s 건너뜀 — 직전 %s / 직후 %s"
                % (pair["축"], aerr or "ok", berr or "ok"))
            continue
        for key in sorted(set(a) | set(b)):
            ba, bb = a.get(key), b.get(key)
            n_a = ba[1] if ba else None
            n_b = bb[1] if bb else None
            # 한쪽에만 있는 섹션은 빈칸이 아니라 (없음) 으로 적어 신설·삭제가 보이게 한다.
            delta = (n_b - n_a) if (n_a is not None and n_b is not None) else ""
            rate = ""
            if n_a:                       # 분모가 0이면 증감률을 계산하지 않는다
                rate = "%.1f%%" % (100.0 * (n_b - n_a) / n_a) if n_b is not None else ""
            out.append(dict(
                사건=pair["사건"], 축=pair["축"],
                섹션제목=key,
                섹션제목_원문=(ba or bb)[0],
                직전_글자수=("(없음)" if ba is None else n_a),
                직후_글자수=("(없음)" if bb is None else n_b),
                증감=delta, 증감률=rate,
                직전_등장횟수=("(없음)" if ba is None else ba[2]),
                직후_등장횟수=("(없음)" if bb is None else bb[2]),
                표_개수_직전=("(없음)" if ba is None else ba[3]),
                표_개수_직후=("(없음)" if bb is None else bb[3]),
                직전_rcept_no=pair["before"], 직후_rcept_no=pair["after"],
                정정명령_rcept_no=pair["명령"], value_source="computed"))
    if not out:
        result["skipped"].append("우리2026_정정명령_전후차이.csv: 비교할 문서가 없음")
        return
    # 증가폭이 큰 섹션이 위로 오게. 숫자가 아닌 칸은 뒤로 보낸다.
    out.sort(key=lambda r: (r["축"], -(r["증감"] if isinstance(r["증감"], int) else -10 ** 9)))
    cols = ["사건", "축", "섹션제목", "섹션제목_원문", "직전_글자수", "직후_글자수",
            "증감", "증감률", "직전_등장횟수", "직후_등장횟수",
            "표_개수_직전", "표_개수_직후",
            "직전_rcept_no", "직후_rcept_no", "정정명령_rcept_no", "value_source"]
    path = os.path.join(handoff_dir, "우리2026_정정명령_전후차이.csv")
    _write(path, out, cols)
    result["paths"].append(path)
    result["counts"][os.path.basename(path)] = len(out)
    for pair in AMEND_PAIRS:
        rows = [r for r in out if r["축"] == pair["축"]]
        if not rows:
            continue
        grew = [r for r in rows if isinstance(r["증감"], int) and r["증감"] > 0]
        new = [r for r in rows if r["직전_글자수"] == "(없음)"]
        result["notes"].append(
            "정정명령 전후차이 [%s]: 섹션 %d개 / 늘어난 섹션 %d개 / 신설 %d개 / 총 증감 %+d자"
            % (pair["축"], len(rows), len(grew), len(new),
               sum(r["증감"] for r in rows if isinstance(r["증감"], int))))


# ── 5) 자본흐름 결합 — 지주의 조달 ↔ 자회사 증자 ─────────────────────────
# 07·08 은 연도말 '미상환잔액' 스냅샷이라 발행일도 발행금액도 없다. 그래서 금액은
# 증권발행실적보고서 원문에서 뽑는다(3차 질문 1 → 2번 채택).
#
# 실측한 서식(신한지주 20210218000902):
#   「2. 발행 개요」        총 발행금액 : | 210,000,000,000
#                          구분|사채의 종류|회차별 발행총액|상환기일
#   「II. 청약 및 배정」    청약개시일|청약종료일|납입기일|비고
#   「V. 조달된 자금의 사용내역」
#       시설자금|영업양수자금|운영자금|채무상환자금|타법인증권취득자금|기타|계
#   ★ 마지막 표의 「타법인증권취득자금」이 곧 '자회사에 넣은 돈'이다.
#
# 라벨로 찾는다 — 열 위치로 집으면 서식이 조금만 달라져도 조용히 엉뚱한 값을 읽는다.
# 못 읽으면 빈칸으로 두고 parse_status 에 사유를 남긴다. 인과는 단정하지 않는다.
FUND_USE_LABELS = ["시설자금", "영업양수자금", "운영자금", "채무상환자금",
                   "타법인증권취득자금", "기타", "계"]


def _cellnorm(x):
    return docparse.normalize_for_match(x or "").replace(" ", "")


def _find_labeled_row(tables, labels, need=2):
    """머리행에 labels 가 다 있는 표를 찾아 {라벨: 다음 행의 같은 칸} 을 돌려준다."""
    want = [_cellnorm(l) for l in labels]
    for t in tables:
        rows = t["rows"]
        for hi, head in enumerate(rows[:2]):
            hv = [_cellnorm(c["text"]) for c in head]
            idx = {}
            for w, orig in zip(want, labels):
                for j, h in enumerate(hv):
                    if h == w:
                        idx[orig] = j
                        break
            if len(idx) >= need and hi + 1 < len(rows):
                data = rows[hi + 1]
                return {k: (data[j]["text"] if j < len(data) else "")
                        for k, j in idx.items()}
    return {}


def _find_pair(tables, label):
    """'총 발행금액 : | 210,000,000,000' 처럼 라벨 옆 칸에 값이 있는 꼴."""
    w = _cellnorm(label)
    for t in tables:
        for row in t["rows"]:
            for j, c in enumerate(row):
                if w in _cellnorm(c["text"]) and j + 1 < len(row):
                    v = row[j + 1]["text"].strip()
                    if v and v != "-":
                        return v
    return ""


def extract_issue(out_dir, rcept_no):
    """증권발행실적보고서 원문 → 발행금액·발행일·증권종류·자금용도. 실패는 사유로."""
    # 「실제 조달금액」칸은 만들지 않는다. 그 표는 2단 헤더 + colspan 이라
    # 격자를 추론해야 열이 맞는데, 이 프로젝트는 격자 추론을 하지 않는다.
    # 같은 값을 「총 발행금액」과 「용도_계」가 정확히 주므로 잃는 것이 없다.
    rec = {"parse_status": "", "총발행금액": "", "납입기일": "",
           "사채의종류": "", "상환기일": "", "회차별발행총액": ""}
    for k in FUND_USE_LABELS:
        rec["용도_" + k] = ""
    p = os.path.join(out_dir, "raw", "document", "%s.zip" % rcept_no)
    if not os.path.exists(p):
        rec["parse_status"] = "원문 ZIP 없음"
        return rec
    try:
        info = docparse.read_zip(open(p, "rb").read(), rcept_no)
    except Exception as e:                                   # noqa: BLE001
        rec["parse_status"] = "ZIP 열기 실패(%s)" % type(e).__name__
        return rec
    if not info.get("text"):
        rec["parse_status"] = "본문 없음"
        return rec
    secs, err = docparse.parse_document(info["text"])
    tables = [t for s in secs for t in s["tables"]]
    if err:
        rec["parse_status"] = "파서 경고: %s" % err

    rec["총발행금액"] = _find_pair(tables, "총 발행금액")
    bond = _find_labeled_row(tables, ["사채의 종류", "회차별 발행총액", "상환기일"], need=2)
    rec["사채의종류"] = bond.get("사채의 종류", "")
    rec["회차별발행총액"] = bond.get("회차별 발행총액", "")
    rec["상환기일"] = bond.get("상환기일", "")
    pay = _find_labeled_row(tables, ["납입기일"], need=1)
    rec["납입기일"] = pay.get("납입기일", "")
    use = _find_labeled_row(tables, FUND_USE_LABELS, need=3)
    for k in FUND_USE_LABELS:
        rec["용도_" + k] = use.get(k, "")

    miss = [n for n, v in (("총발행금액", rec["총발행금액"]),
                           ("납입기일", rec["납입기일"]),
                           ("자금용도", use)) if not v]
    if miss and not rec["parse_status"]:
        rec["parse_status"] = "못 읽음: %s (값을 지어내지 않고 빈칸으로 둠)" % ", ".join(miss)
    return rec


# 사건별 지주와 ±2년 창. 대조군은 제외한다 — 모자 구조라 '지주 조달' 축이 없다.
FUNDING_EVENTS = [
    ("신한 2019 오렌지라이프 완전자회사화", "신한지주", "2017", "2021",
     ["신한라이프생명보험", "오렌지라이프생명보험", "신한이지손해보험"]),
    ("신한 2021 신한라이프 출범", "신한지주", "2019", "2023",
     ["신한라이프생명보험", "신한이지손해보험"]),
    ("KB 2017 KB손해보험 완전자회사화", "KB금융", "2015", "2019",
     ["KB손해보험", "KB생명보험", "KB라이프생명보험"]),
    ("우리 2026 동양생명·ABL생명 편입", "우리금융지주", "2024", "2028",
     ["동양생명보험", "ABL생명보험"]),
    ("iM 2016 iM라이프 주식교환", "iM금융지주", "2014", "2018",
     ["iM라이프생명보험"]),
]
FUND_REPORT_HINTS = ("증권발행실적보고서",)
FUND_MAJOR_HINTS = ("신종자본증권", "조건부자본증권")


def build_capital_flow(out_dir, handoff_dir, result):
    disc = _read(out_dir, "02_공시목록.csv")
    rows06 = _read(out_dir, "06_증자감자현황.csv")
    if disc is None:
        result["skipped"].append("자본흐름_결합.csv: 02_공시목록.csv 가 없음")
        return
    out = []
    for ev, holder, y0, y1, subs in FUNDING_EVENTS:
        # 축 A — 지주의 조달
        for r in disc:
            if (r.get("corp_label") or "") != holder:
                continue
            dt = r.get("rcept_dt", "")
            if not (y0 <= dt[:4] <= y1):
                continue
            nm = r.get("report_nm") or ""
            is_fund = any(h in nm for h in FUND_REPORT_HINTS)
            is_major = "주요사항보고서" in nm and any(h in nm for h in FUND_MAJOR_HINTS)
            if not (is_fund or is_major):
                continue
            rec = extract_issue(out_dir, r.get("rcept_no", "")) if is_fund else {
                "parse_status": "주요사항보고서는 발행 '결정'이라 실적 금액이 없다 — "
                                "금액은 같은 회차의 증권발행실적보고서에서 본다"}
            row = dict(사건=ev, 축="조달(지주)", corp_label=holder,
                       날짜=dt, 보고서명=nm, rcept_no=r.get("rcept_no", ""),
                       증권종류=("신종자본증권" if "신종자본증권" in nm else
                               "조건부자본증권" if "조건부자본증권" in nm else
                               rec.get("사채의종류", "")),
                       공모여부=("사모" if "사모" in nm else "공모" if is_fund else ""),
                       value_source="api+원문추출" if is_fund else "api")
            row.update({k: rec.get(k, "") for k in
                        ["총발행금액", "납입기일", "상환기일",
                         "회차별발행총액", "parse_status"]})
            for k in FUND_USE_LABELS:
                row["용도_" + k] = rec.get("용도_" + k, "")
            out.append(row)
        # 축 B — 자회사 증자
        for r in (rows06 or []):
            if (r.get("corp_label") or "") not in subs:
                continue
            de = (r.get("isu_dcrs_de") or "").strip()
            if de in ("", "-"):
                continue
            y = de[:4]
            if not (y0 <= y <= y1):
                continue
            qty, price = _num(r.get("isu_dcrs_qy")), _num(r.get("isu_dcrs_mstvdv_amount"))
            out.append(dict(
                사건=ev, 축="투입(자회사)", corp_label=r.get("corp_label", ""),
                날짜=de.replace(".", ""), 보고서명=r.get("reprt_nm", ""),
                rcept_no=r.get("rcept_no", ""),
                증권종류=r.get("isu_dcrs_stock_knd", ""), 공모여부=r.get("isu_dcrs_stle", ""),
                수량=r.get("isu_dcrs_qy", ""),
                주당발행가액=r.get("isu_dcrs_mstvdv_amount", ""),
                주당액면가액=r.get("isu_dcrs_mstvdv_fval_amount", ""),
                납입액_계산=(str(qty * price) if (qty is not None and price is not None) else ""),
                parse_status="" if (qty is not None and price is not None)
                             else "수량 또는 주당발행가액이 비어 계산하지 않음",
                value_source="api+computed"))
    # 같은 이벤트가 연도별 보고서마다 되풀이되므로 투입 축은 (날짜, 수량) 으로 묶는다.
    seen, uniq = set(), []
    for r in out:
        k = (r["사건"], r["축"], r["corp_label"], r["날짜"], r.get("수량", ""), r["rcept_no"]
             if r["축"] == "조달(지주)" else "")
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    # 그룹 × 날짜 로 정렬해 같은 분기에 조달과 증자가 있었는지 눈으로 보게 한다.
    # `관계` 컬럼은 두지 않는다 — 인과 판단은 이 파일이 하지 않는다.
    uniq.sort(key=lambda r: (r["사건"], r["날짜"], r["축"], r["corp_label"]))
    cols = (["사건", "축", "corp_label", "날짜", "보고서명", "증권종류", "공모여부",
             "총발행금액", "실제조달금액", "납입기일", "상환기일", "회차별발행총액",
             "수량", "주당발행가액", "주당액면가액", "납입액_계산"]
            + ["용도_" + k for k in FUND_USE_LABELS]
            + ["parse_status", "value_source", "rcept_no"])
    path = os.path.join(handoff_dir, "자본흐름_결합.csv")
    _write(path, uniq, cols)
    result["paths"].append(path)
    result["counts"][os.path.basename(path)] = len(uniq)
    fund = [r for r in uniq if r["축"] == "조달(지주)"]
    okamt = sum(1 for r in fund if r.get("총발행금액"))
    tago = sum(1 for r in fund if (r.get("용도_타법인증권취득자금") or "").strip() not in ("", "-"))
    result["notes"].append(
        "자본흐름_결합: 조달 %d건(금액 확보 %d건) / 투입 %d건 / "
        "조달분 중 「타법인증권취득자금」이 0 이 아닌 건 %d건"
        % (len(fund), okamt, len(uniq) - len(fund), tago))


def build_all(out_dir, handoff_dir, result):
    build_stake(out_dir, handoff_dir, result)
    build_equity(out_dir, handoff_dir, result)
    build_interlock(out_dir, handoff_dir, result)
    build_amendment_diff(out_dir, handoff_dir, result)
    build_capital_flow(out_dir, handoff_dir, result)
