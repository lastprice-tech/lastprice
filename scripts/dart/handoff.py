# -*- coding: utf-8 -*-
"""11_원문추출.csv → handoff/ 인계용 CSV.

1차 산출물(원문_지주전환_서술.csv 461행)은 임시 스크립트로 만들어 재현이 안 됐다.
그 임시 스크립트를 저장된 순수 함수로 옮긴 것이 이 모듈이다. 입력은 dart_out/ 아래
파일뿐이고 네트워크도 API 키도 쓰지 않는다 — 같은 dart_out 을 주면 몇 번을 돌려도
같은 CSV 가 나오고, 1차·2차를 같은 코드로 낸다.

지키는 것:
  - 추정·보간·삭제 금지. 못 읽은 본문은 빈칸으로 두고 사유를 반환값의 notes 에 남긴다.
  - 정정본은 접수일 순으로 나열만 한다. 어느 것이 최종본인지 여기서 판단하지 않는다.
  - 표는 격자로 추론하지 않는다. rowspan/colspan/단위를 원문 그대로 옮긴다.
"""
from __future__ import annotations

import csv
import json
import os

import config
import emit
from phase2 import doc_kind   # 접두 판정은 phase2 것을 그대로 쓴다 (재구현 금지)

# Excel 셀 한도. 이걸 넘는 섹션은 '자르지 않고' chunk_seq 로 나눠 여러 행에 담는다.
# 실측: 1차 대상 434개 섹션 중 10개가 한도를 넘고, 최장은 메리츠금융지주 20230206000364
# 의 "VI. 투자위험요소" 114,702자(→ 4청크)다.
EXCEL_CELL_LIMIT = 32767

# 섹션이 한 행도 안 잡힌 문서를 위한 표지값. 실제 섹션 번호(0 이상)와 섞이면 안 되므로 -1.
FULL_SECTION_INDEX = -1
FULL_SECTION_TITLE = "(문서전문)"

DEFAULT_HANDOFF_DIR = "./handoff"
SOURCE_CSV = "11_원문추출.csv"

# 컬럼 순서는 인계 스키마 그 자체다. union-of-keys 를 쓰는 emit.write_csv 와 달리
# 여기서는 고정 목록으로 쓰고, 목록에 없는 키가 섞이면 DictWriter 가 예외를 던지게 둔다
# (조용히 버려지는 쪽이 더 나쁘다).
NARRATIVE_COLS = [
    "corp_label", "rcept_no", "rcept_dt", "doc_kind", "doc_purpose", "report_nm",
    "section_index", "section_title", "chunk_seq", "text_chars", "section_text",
    "text_path", "fetched_at", "status", "raw_path", "raw_sha256",
]

TABLE_COLS = [
    "corp_label", "rcept_no", "rcept_dt", "doc_kind", "doc_purpose",
    "section_index", "section_title", "table_index", "table_matched_keyword",
    "table_extracted", "table_n_rows",
    "row_index", "cell_ord", "cell_tag", "rowspan", "colspan",
    "unit_hint", "unit_hint_source", "cell_text", "fetched_at", "status",
    "raw_path", "raw_sha256",
]

# _파일목록.json 안에서 '파일 행 목록'이 들어 있을 수 있는 키. dartweb 은 "files" 를
# 쓰지만 형태가 바뀌어도 조용히 1행짜리 요약으로 뭉개지지 않게 목록을 한곳에 둔다.
FILELIST_LIST_KEYS = ("rows", "files", "목록", "파일목록")

# dartweb.py 가 _파일목록.json 에 내놓는 필드명과 같다.
FILELIST_COLS = [
    "rcept_no", "corp_label", "rcept_dt", "doc_kind", "doc_purpose",
    "파일종류", "문서종류", "정관판별근거", "원파일명", "저장경로", "바이트", "sha256",
    "수령성공여부", "실패사유", "fetched_at", "source_url", "dcm_no",
]

# 출처 4컬럼은 11_원문추출.csv 의 prov 컬럼에서 그대로 옮긴다.
PROV_KEYS = ["fetched_at", "status", "raw_path", "raw_sha256"]

NARRATIVE_NAME = {"1차": "원문_지주전환_서술.csv", "2차": "원문_지주전환_서술_2차.csv"}
TABLE_NAME = {"1차": "원문_지주전환_표.csv", "2차": "원문_지주전환_표_2차.csv"}
FILELIST_NAME = "원문_파일목록.csv"


# ── 설정 조회 ─────────────────────────────────────────────────────────────
def doc_purpose_map():
    """rcept_no → '설립' | '편입·완전자회사화'. 없으면 빈 표(= 대상 0건)."""
    return getattr(config, "DOC_PURPOSE", {}) or {}


def batch_map():
    """corp_label → '1차' | '2차'."""
    return getattr(config, "HANDOFF_BATCH", {}) or {}


def _batch_of(corp_label, batches, warned, notes):
    """표에 없는 라벨은 2차로 넣고 경고를 찍는다. 라벨이 없다고 행을 버리지는 않는다."""
    b = batches.get(corp_label)
    if b in ("1차", "2차"):
        return b
    if corp_label not in warned:
        warned.add(corp_label)
        msg = ("경고: HANDOFF_BATCH 에 없는 corp_label %r — 2차로 넣음 "
               "(config.HANDOFF_BATCH 에 추가할 것)" % (corp_label or "",))
        notes.append(msg)
        print("  " + msg)
    return "2차"


# ── 입출력 도우미 ─────────────────────────────────────────────────────────
def _open_source(out_dir):
    """11_원문추출.csv 리더. 셀 한 칸이 기본 한도(131,072자)를 넘을 수 있어 미리 올린다."""
    try:
        csv.field_size_limit(10 ** 9)
    except OverflowError:                      # 32bit 빌드 방어
        csv.field_size_limit(2 ** 31 - 1)
    path = os.path.join(out_dir, SOURCE_CSV)
    if not os.path.exists(path):
        raise SystemExit("  입력이 없습니다: %s\n"
                         "  먼저 `python3 scripts/dart/run.py emit` 을 실행하세요." % path)
    f = open(path, encoding="utf-8-sig", newline="")
    return f, csv.DictReader(f)


class _LazyWriter:
    """행이 생길 때 파일을 연다. 빈 CSV 를 만들지 않는 emit.write_csv 의 관례를 따른다.

    1차 표 CSV 는 실측 41.8만 행(34MB)이라 전량을 메모리에 모았다가 쓰면 수백 MB 가
    든다. 그래서 스트리밍으로 흘려 쓴다.
    """

    def __init__(self, path, cols):
        self.path, self.cols = path, cols
        self._f = self._w = None
        self.n = 0

    def write(self, row):
        if self._w is None:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            self._f = open(self.path, "w", encoding="utf-8-sig", newline="")
            self._w = csv.DictWriter(self._f, fieldnames=self.cols, extrasaction="raise")
            self._w.writeheader()
        self._w.writerow(row)
        self.n += 1

    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = self._w = None


def chunks(text, limit=EXCEL_CELL_LIMIT):
    """Excel 셀 한도를 넘는 본문을 '자르지 않고' 나눈다.

    반환값을 순서대로 이으면 원문과 글자 단위로 같다. 빈 본문도 [""] 를 돌려주므로
    섹션 하나가 행 하나로는 반드시 남는다(빈 섹션이 조용히 사라지지 않게).
    """
    if len(text) <= limit:
        return [text]
    return [text[i:i + limit] for i in range(0, len(text), limit)]


# ── 본문 읽기 ─────────────────────────────────────────────────────────────
def read_section_body(out_dir, text_path, title_raw, title, notes, rcept_no=""):
    """text/<rcept_no>/NNN_*.txt 에서 본문만 꺼낸다.

    11_원문추출.csv 의 context 는 200자로 잘린 미리보기라 인계에 쓰면 안 된다.
    파일은 emit.emit_documents 가 "제목\\n\\n본문" 으로 쓴 것이므로 제목 줄과 빈 줄을
    떼어낸다. 제목으로 시작하지 않으면 떼지 않고 전문을 그대로 담은 뒤 사유를 남긴다
    (모르는 형식을 만났다고 앞을 잘라내면 그게 곧 삭제다).
    """
    if not text_path:
        notes.append("%s: text_path 가 비어 있어 본문 미수록" % rcept_no)
        return "", False
    p = os.path.join(out_dir, text_path.replace("/", os.sep))
    if not os.path.exists(p):
        notes.append("%s: 본문 파일 없음 — %s (빈칸으로 둠)" % (rcept_no, text_path))
        return "", False
    # newline="" 필수. 기본값(newline=None)은 범용 개행 변환이라 원문의 "\r\n"·"\r" 을
    # 말없이 "\n" 한 글자로 줄인다. 실측: text/*/_full.txt 83개 전부에 CR 이 있고
    # 합계 19,820자였다 — 변환하면 그만큼이 조용히 사라진다(= 삭제).
    # 파일 하나가 안 읽힌다고 인계본 전체를 못 내면 그게 더 큰 손실이다. 실측으로
    # 확인: 본문 하나가 cp949 로 남아 있으면 UnicodeDecodeError 로 build 전체가 죽어
    # 정상인 433개 섹션까지 한 줄도 안 나왔다. 사유를 남기고 그 행만 빈칸으로 둔다.
    try:
        with open(p, encoding="utf-8", newline="") as f:
            raw = f.read()
    except (UnicodeDecodeError, OSError) as e:
        notes.append("%s: 본문 파일을 읽지 못함 — %s (%s) — 빈칸으로 둠"
                     % (rcept_no, text_path, type(e).__name__))
        return "", False
    for head in (title_raw, title):
        pre = (head or "") + "\n\n"
        if head and raw.startswith(pre):
            return raw[len(pre):], True
    notes.append("%s: %s 가 제목으로 시작하지 않아 전문을 그대로 담음" % (rcept_no, text_path))
    return raw, True


# ── 문서 메타 ─────────────────────────────────────────────────────────────
def _disclosure_index(out_dir):
    """02_공시목록.csv → rcept_no 별 (corp_label, rcept_dt, report_nm).

    11_원문추출.csv 에 행이 한 줄도 없는 문서(= 섹션도 표도 안 잡힌 문서)의 라벨·접수일을
    메울 때만 쓴다. 없으면 빈칸으로 둔다.
    """
    path = os.path.join(out_dir, "02_공시목록.csv")
    idx = {}
    if not os.path.exists(path):
        return idx
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rc = r.get("rcept_no") or ""
            if rc and rc not in idx:
                idx[rc] = {"corp_label": r.get("corp_label", ""),
                           "rcept_dt": r.get("rcept_dt", ""),
                           "report_nm": r.get("report_nm", "")}
    return idx


def _prov_from_sidecar(out_dir, rcept_no):
    """raw/document/<rcept_no>.zip.meta.json 에서 출처 4컬럼. 없으면 빈칸."""
    body = os.path.join(out_dir, "raw", "document", "%s.zip" % rcept_no)
    mp = body + ".meta.json"
    blank = {k: "" for k in PROV_KEYS}
    if not os.path.exists(mp):
        return blank
    try:
        with open(mp, encoding="utf-8") as f:
            m = json.load(f)
    except Exception:
        return blank
    return {"fetched_at": m.get("fetched_at", ""),
            "status": m.get("api_status", ""),
            "raw_path": emit.rel(out_dir, body) if os.path.exists(body) else "",
            "raw_sha256": m.get("sha256", "")}


# ── 1패스: 서술행 + 문서 메타 수집 ────────────────────────────────────────
def _scan_text(out_dir, purpose):
    """11_원문추출.csv 를 한 번 훑어 kind=='text' 행과 문서별 메타를 모은다.

    표 셀은 여기서 만지지 않는다(1차만 41.8만 행이라 메모리에 쌓으면 안 된다).
    seen 에는 kind 를 가리지 않고 '그 문서의 행을 본 적이 있다'는 사실과 메타를 담는다.
    """
    text_rows, meta = [], {}
    f, rd = _open_source(out_dir)
    with f:
        for r in rd:
            rc = r.get("rcept_no") or ""
            if rc not in purpose:
                continue
            if rc not in meta:
                m = {"corp_label": r.get("corp_label", ""),
                     "rcept_dt": r.get("rcept_dt", ""),
                     "report_nm": r.get("report_nm", "")}
                m.update({k: r.get(k, "") for k in PROV_KEYS})
                meta[rc] = m
            if r.get("kind") == "text":
                text_rows.append(r)
    return text_rows, meta


def _narrative_rows(out_dir, purpose, text_rows, meta, notes, stats):
    """섹션 행 → 청크 행. 섹션이 0건인 문서는 _full.txt 로 최소 1행을 만든다."""
    rows = []
    have_text = set()

    for r in text_rows:
        rc = r["rcept_no"]
        have_text.add(rc)
        body, ok = read_section_body(out_dir, r.get("text_path", ""),
                                     r.get("section_title_raw", ""),
                                     r.get("section_title", ""), notes, rc)
        # 조용한 절삭 감시: 11_원문추출.csv 의 text_chars 는 emit 이 기록한 본문 길이다.
        # 파일에서 다시 읽은 길이와 다르면 어딘가에서 잘린 것이므로 세어서 보고한다.
        declared = r.get("text_chars", "")
        if ok and str(declared).strip().isdigit() and int(declared) != len(body):
            stats["len_mismatch"] += 1
            notes.append("%s 섹션 %s: 본문 길이 불일치 (11_원문추출 %s자 vs 파일 %d자)"
                         % (rc, r.get("section_index", ""), declared, len(body)))
        parts = chunks(body)
        if len(parts) > 1:
            stats["chunked_sections"] += 1
            stats["chunk_extra_rows"] += len(parts) - 1
        base = dict(corp_label=r.get("corp_label", ""), rcept_no=rc,
                    rcept_dt=r.get("rcept_dt", ""),
                    doc_kind=doc_kind(r.get("report_nm", "")),
                    doc_purpose=purpose.get(rc, ""),
                    report_nm=r.get("report_nm", ""),
                    section_index=r.get("section_index", ""),
                    section_title=r.get("section_title", ""),
                    text_path=r.get("text_path", ""))
        base.update({k: r.get(k, "") for k in PROV_KEYS})
        for i, part in enumerate(parts, 1):
            rows.append(dict(base, chunk_seq=i, text_chars=len(part), section_text=part))

    # ★ 섹션이 한 행도 안 잡힌 문서 — 문서 전문만이라도 남긴다.
    # emit.emit_documents 는 섹션 매칭 전에 text/<rcept_no>/_full.txt 를 먼저 쓰므로,
    # 키워드에 하나도 안 걸린 문서는 CSV 행이 0개여도 전문 파일은 남아 있다.
    disc = None
    for rc in sorted(purpose):
        if rc in have_text:
            continue
        full = os.path.join(out_dir, "text", rc, "_full.txt")
        if not os.path.exists(full):
            # 전문 파일조차 없으면 지어낼 것이 없다. 사유만 남기고 행은 만들지 않는다.
            pv = _prov_from_sidecar(out_dir, rc)
            notes.append("%s(%s): 섹션 0건 + 전문 파일 없음 (raw status=%s) — "
                         "원문 ZIP 수령/파싱 후 emit 재실행 필요"
                         % (rc, purpose.get(rc, ""), pv.get("status") or "미수령"))
            stats["docs_without_body"] += 1
            continue
        m = meta.get(rc)
        if m is None:
            if disc is None:
                disc = _disclosure_index(out_dir)
            d = disc.get(rc, {})
            m = {"corp_label": d.get("corp_label", ""), "rcept_dt": d.get("rcept_dt", ""),
                 "report_nm": d.get("report_nm", "")}
            m.update(_prov_from_sidecar(out_dir, rc))
            if not m["corp_label"]:
                notes.append("%s: 11_원문추출·02_공시목록 어디에도 메타가 없어 "
                             "corp_label/rcept_dt 를 빈칸으로 둠" % rc)
        try:
            with open(full, encoding="utf-8", newline="") as f:   # 개행 변환 금지(위 주석 참조)
                body = f.read()
        except (UnicodeDecodeError, OSError) as e:
            notes.append("%s(%s): 전문 파일을 읽지 못함 — text/%s/_full.txt (%s) — "
                         "행을 만들지 않음(지어낼 것이 없다)"
                         % (rc, purpose.get(rc, ""), rc, type(e).__name__))
            stats["docs_without_body"] += 1
            continue
        parts = chunks(body)
        if len(parts) > 1:
            stats["chunked_sections"] += 1
            stats["chunk_extra_rows"] += len(parts) - 1
        stats["full_fallback_docs"] += 1
        notes.append("%s(%s): 섹션 0건 — 전문 %d자를 %d행으로 수록(section_index=%d)"
                     % (rc, purpose.get(rc, ""), len(body), len(parts), FULL_SECTION_INDEX))
        base = dict(corp_label=m.get("corp_label", ""), rcept_no=rc,
                    rcept_dt=m.get("rcept_dt", ""),
                    doc_kind=doc_kind(m.get("report_nm", "")),
                    doc_purpose=purpose.get(rc, ""),
                    report_nm=m.get("report_nm", ""),
                    section_index=FULL_SECTION_INDEX, section_title=FULL_SECTION_TITLE,
                    text_path="text/%s/_full.txt" % rc)
        base.update({k: m.get(k, "") for k in PROV_KEYS})
        for i, part in enumerate(parts, 1):
            rows.append(dict(base, chunk_seq=i, text_chars=len(part), section_text=part))

    # 정정본을 접수일 순으로 나열할 뿐이다. 어느 것이 최종본인지는 판단하지 않는다.
    # section_index 는 문자열이라 정렬 전에 정수로 바꾼다(-1 이 0 보다 앞에 오게).
    def key(r):
        si = r["section_index"]
        try:
            si = int(si)
        except (TypeError, ValueError):
            si = 10 ** 9
        return (r["corp_label"] or "", r["rcept_dt"] or "", r["rcept_no"] or "",
                si, r["chunk_seq"])
    rows.sort(key=key)
    return rows


# ── 산출 1: 서술 ──────────────────────────────────────────────────────────
def build_narrative(out_dir, handoff_dir, purpose, batches, result, warned):
    text_rows, meta = _scan_text(out_dir, purpose)
    stats = {"chunked_sections": 0, "chunk_extra_rows": 0, "len_mismatch": 0,
             "full_fallback_docs": 0, "docs_without_body": 0}
    rows = _narrative_rows(out_dir, purpose, text_rows, meta, result["notes"], stats)

    writers = {b: _LazyWriter(os.path.join(handoff_dir, NARRATIVE_NAME[b]), NARRATIVE_COLS)
               for b in ("1차", "2차")}
    try:
        for r in rows:
            writers[_batch_of(r["corp_label"], batches, warned, result["notes"])].write(r)
    finally:
        for w in writers.values():
            w.close()
    for b, w in writers.items():
        if w.n:
            result["paths"].append(w.path)
            result["counts"][NARRATIVE_NAME[b]] = w.n
        else:
            result["skipped"].append("%s: 대상 행 0건 — 파일을 만들지 않음" % NARRATIVE_NAME[b])
            _warn_stale(w.path, result)
    result["narrative_stats"] = dict(stats, sections=len(text_rows), rows=len(rows))
    return meta


# ── 산출 2: 표 ────────────────────────────────────────────────────────────
def build_tables(out_dir, handoff_dir, purpose, batches, result, warned):
    """kind=='table' 셀 + 셀을 전개하지 않은 표의 색인 행을 원문 그대로 옮긴다.

    격자로 추론하지 않는다 — rowspan/colspan 과 unit_hint 를 그대로 두고, 병합 해제나
    단위 환산은 하지 않는다. 정렬은 입력 파일 순서를 그대로 따른다: emit 이
    (corp_label, rcept_no, section_index) 로 정렬해 두고 그 안은 table_index →
    row_index → cell_ord 순으로 쌓아 두므로 이미 원하는 순서이고, rcept_no 는 접수일이
    앞에 붙으므로 접수일 순과 같다. 41.8만 행을 다시 정렬하려고 전량을 메모리에 올리는
    대신 스트리밍으로 쓰고, 순서가 어긋나면 경고를 남긴다.

    ★ kind=='table_index' 를 버리면 안 된다. emit 은 키워드에 안 걸린 표의 셀 전개를
    생략하면서 "색인 행은 남긴다 — 삭제가 아니다"라고 해 뒀다. 실측: 1차 대상 9개 문서의
    표 18,103개 중 5,176개(28.6%)가 table_extracted='N' 이라 셀이 한 줄도 없다. 셀만
    옮기면 그 5,176개 표는 인계본에서 통째로 사라지고, 받는 쪽은 원문에 표가 12,927개뿐인
    줄 안다. 그래서 미전개 표는 cell 컬럼을 빈칸으로 둔 색인 1행으로 남긴다
    (table_extracted='N' + row_index 빈칸으로 셀 행과 구별된다).
    전개된 표(Y)는 셀 행이 이미 table_extracted='Y' 를 달고 있으므로 색인 행을 또 쓰면
    같은 표를 두 번 세게 된다 — 쓰지 않고, 대신 셀이 실제로 따라왔는지만 대조한다.
    """
    writers = {b: _LazyWriter(os.path.join(handoff_dir, TABLE_NAME[b]), TABLE_COLS)
               for b in ("1차", "2차")}
    last = {}
    unordered = 0
    index_only = 0                   # 셀 미전개 표 = 색인 1행만 남긴 표
    y_index, cell_tables = set(), set()
    f, rd = _open_source(out_dir)
    try:
        for r in rd:
            rc = r.get("rcept_no") or ""
            if rc not in purpose:
                continue
            kind = r.get("kind")
            if kind not in ("table", "table_index"):
                continue
            tkey = (rc, r.get("section_index", ""), r.get("table_index", ""))
            if kind == "table_index":
                if (r.get("table_extracted") or "").strip().upper() == "Y":
                    y_index.add(tkey)
                    continue
                index_only += 1
            else:
                cell_tables.add(tkey)
            b = _batch_of(r.get("corp_label", ""), batches, warned, result["notes"])
            k = (r.get("corp_label", ""), r.get("rcept_dt", ""), rc,
                 _as_int(r.get("section_index")), _as_int(r.get("table_index")),
                 _as_int(r.get("row_index")), _as_int(r.get("cell_ord")))
            if b in last and k < last[b]:
                unordered += 1
            last[b] = k
            row = dict(corp_label=r.get("corp_label", ""), rcept_no=rc,
                       rcept_dt=r.get("rcept_dt", ""),
                       doc_kind=doc_kind(r.get("report_nm", "")),
                       doc_purpose=purpose.get(rc, ""),
                       section_index=r.get("section_index", ""),
                       section_title=r.get("section_title", ""),
                       table_index=r.get("table_index", ""),
                       table_matched_keyword=r.get("table_matched_keyword", ""),
                       table_extracted=r.get("table_extracted", ""),
                       table_n_rows=r.get("table_n_rows", ""),
                       row_index=r.get("row_index", ""), cell_ord=r.get("cell_ord", ""),
                       cell_tag=r.get("cell_tag", ""), rowspan=r.get("rowspan", ""),
                       colspan=r.get("colspan", ""), unit_hint=r.get("unit_hint", ""),
                       unit_hint_source=r.get("unit_hint_source", ""),
                       cell_text=r.get("cell_text", ""))
            row.update({key: r.get(key, "") for key in PROV_KEYS})
            writers[b].write(row)
    finally:
        f.close()
        for w in writers.values():
            w.close()
    if unordered:
        result["notes"].append(
            "표 CSV: 입력 순서가 %d곳에서 역행 — 11_원문추출.csv 의 정렬이 바뀐 듯하다. "
            "행은 전부 보존됐고 순서만 입력을 따른다." % unordered)
    if index_only:
        result["notes"].append(
            "표 CSV: 셀 미전개 표 %d개를 색인 1행씩으로 보존 "
            "(table_extracted=N, row_index·cell_text 빈칸). 셀이 필요하면 emit 을 "
            "--extract-all-tables 로 다시 돌릴 것 — 값을 지어내지 않았다." % index_only)
    ghost = y_index - cell_tables
    if ghost:
        result["notes"].append(
            "표 CSV: table_extracted=Y 인데 셀 행이 한 줄도 없는 표 %d개 — "
            "11_원문추출.csv 가 중간에 잘렸을 수 있다. 예: %s"
            % (len(ghost), ", ".join("%s 섹션%s 표%s" % t for t in sorted(ghost)[:5])))
    orphan = cell_tables - y_index
    if orphan:
        result["notes"].append(
            "표 CSV: 색인 행 없이 셀만 있는 표 %d개 — 입력 형식 확인 필요" % len(orphan))
    result["table_stats"] = {"cells": sum(w.n for w in writers.values()) - index_only,
                             "tables_with_cells": len(cell_tables),
                             "index_only_tables": index_only}
    for b, w in writers.items():
        if w.n:
            result["paths"].append(w.path)
            result["counts"][TABLE_NAME[b]] = w.n
        else:
            result["skipped"].append("%s: 대상 행 0건 — 파일을 만들지 않음" % TABLE_NAME[b])
            _warn_stale(w.path, result)


def _warn_stale(path, result):
    """이번 실행이 0행이라 쓰지 않은 자리에 지난 실행의 파일이 남아 있으면 알린다.

    지우지는 않는다(삭제 금지). 그대로 두면 옛 파일이 이번 결과인 것처럼 읽히는데,
    그게 바로 조용한 오류다. 사실만 알리고 처분은 사람이 정한다.
    """
    if os.path.exists(path):
        result["notes"].append(
            "%s: 이번 실행은 대상 0건인데 지난 실행이 만든 파일이 그 자리에 남아 있다 — "
            "내용이 이번 실행과 다르므로 직접 확인할 것 (지우지 않았음)" % os.path.basename(path))


def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 10 ** 9      # 빈칸은 뒤로


# ── 산출 3: 파일목록 ──────────────────────────────────────────────────────
def _filelist_records(obj):
    """_파일목록.json 의 모양을 가리지 않고 행 목록을 꺼낸다. dartweb 의 출력 형태가
    리스트일 수도, {"rows": [...]} 형태일 수도 있어 둘 다 받는다."""
    if isinstance(obj, list):
        return [r for r in obj if isinstance(r, dict)]
    if isinstance(obj, dict):
        for k in FILELIST_LIST_KEYS:
            v = obj.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
        return [obj]
    return []


def build_filelist(out_dir, handoff_dir, purpose, result):
    """dart_out/doc/*/_파일목록.json 을 한 CSV 로 모은다.

    dartweb.py(다른 모듈)가 만드는 디렉토리다. 아직 없으면 에러가 아니라 '건너뜀'이다.
    """
    doc_root = os.path.join(out_dir, "doc")
    if not os.path.isdir(doc_root):
        result["skipped"].append(
            "%s: %s 가 없어 건너뜀 (dartweb 수집 전) — 에러 아님" % (FILELIST_NAME, doc_root))
        _warn_stale(os.path.join(handoff_dir, FILELIST_NAME), result)
        return
    rows, extra_keys = [], set()
    for rc in sorted(os.listdir(doc_root)):
        d = os.path.join(doc_root, rc)
        if not os.path.isdir(d):
            continue
        p = os.path.join(d, "_파일목록.json")
        if not os.path.exists(p):
            # 받다 만 디렉토리다. 조용히 넘기면 '수집 안 한 것'과 구별이 안 되므로 남긴다.
            result["notes"].append("%s: doc/ 는 있는데 _파일목록.json 이 없음 — "
                                   "dartweb 수집이 중단된 문서 (파일목록 CSV 에서 빠짐)" % rc)
            continue
        try:
            with open(p, encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as e:
            result["notes"].append("%s: _파일목록.json 읽기 실패 (%s) — 건너뜀"
                                   % (rc, type(e).__name__))
            continue
        # 문서 단위 표시는 파일 행에 실리지 않는다. 여기서 안 옮기면 '받다 만 목록'이
        # 완전한 목록처럼 보인다 — 중단 사실이 사라지는 것이 곧 조용한 손실이다.
        if isinstance(obj, dict):
            if obj.get("중단"):
                result["notes"].append("%s: dartweb 수집이 중단됨 (%s) — 파일목록이 불완전"
                                       % (rc, obj.get("중단사유") or "사유 미기재"))
            if obj.get("목록_오류"):
                result["notes"].append("%s: 첨부 목록 조회 오류 (%s) — 파일목록이 불완전"
                                       % (rc, obj.get("목록_오류")))
            if not any(isinstance(obj.get(k), list) for k in FILELIST_LIST_KEYS):
                result["notes"].append("%s: _파일목록.json 에 파일 목록 키(%s)가 없어 문서 "
                                       "요약 1행만 수록 — dartweb 출력 형식 확인 필요"
                                       % (rc, "/".join(FILELIST_LIST_KEYS)))
        for rec in _filelist_records(obj):
            row = dict(rec)
            row.setdefault("rcept_no", rc)
            # dartweb 이 안 채웠을 수 있는 것만 메운다. 이미 값이 있으면 덮어쓰지 않는다.
            if not row.get("doc_purpose"):
                row["doc_purpose"] = purpose.get(row.get("rcept_no", ""), "")
            if not row.get("doc_kind") and row.get("report_nm"):
                row["doc_kind"] = doc_kind(row.get("report_nm", ""))
            extra_keys |= set(row) - set(FILELIST_COLS)
            rows.append(row)
    if not rows:
        result["skipped"].append("%s: _파일목록.json 0건 — 파일을 만들지 않음" % FILELIST_NAME)
        _warn_stale(os.path.join(handoff_dir, FILELIST_NAME), result)
        return
    # 지정 컬럼 뒤에 관측된 여분 키를 붙인다. 스키마를 고정하되 키 손실은 만들지 않는다.
    cols = FILELIST_COLS + sorted(extra_keys)
    if extra_keys:
        result["notes"].append("%s: 지정 외 컬럼 %d개를 뒤에 붙임 (%s)"
                               % (FILELIST_NAME, len(extra_keys),
                                  ", ".join(sorted(extra_keys))))
    rows.sort(key=lambda r: (str(r.get("rcept_no") or ""), str(r.get("파일종류") or ""),
                             str(r.get("원파일명") or "")))
    path = os.path.join(handoff_dir, FILELIST_NAME)
    os.makedirs(handoff_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    result["paths"].append(path)
    result["counts"][FILELIST_NAME] = len(rows)


# ── 진입점 ────────────────────────────────────────────────────────────────
def build(out_dir, handoff_dir=None):
    """11_원문추출.csv(+ text/, doc/) → handoff/ CSV. 네트워크·API 키 불필요.

    반환값: {"paths": [...], "counts": {파일명: 행수}, "skipped": [...], "notes": [...],
             "narrative_stats": {...}}
    """
    handoff_dir = handoff_dir or DEFAULT_HANDOFF_DIR
    os.makedirs(handoff_dir, exist_ok=True)
    purpose, batches = doc_purpose_map(), batch_map()
    result = {"paths": [], "counts": {}, "skipped": [], "notes": [],
              "narrative_stats": {}, "table_stats": {}}
    if not purpose:
        result["skipped"].append(
            "config.DOC_PURPOSE 가 비어 있어 대상 문서 0건 — 서술·표 CSV 를 만들지 않음")
        build_filelist(out_dir, handoff_dir, purpose, result)
        return result
    # 미등록 라벨 경고는 서술·표에서 같은 라벨로 두 번 나오므로 집합을 공유한다.
    warned = set()
    build_narrative(out_dir, handoff_dir, purpose, batches, result, warned)
    build_tables(out_dir, handoff_dir, purpose, batches, result, warned)
    build_filelist(out_dir, handoff_dir, purpose, result)
    return result
