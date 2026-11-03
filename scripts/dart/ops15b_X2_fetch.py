"""15차 확장 작업 B 추가분·C 추가분·E — OpenDART 목록·문서 받기와 md 바꾸기(단계 1).

키는 환경변수 DART_API_KEY 만(scripts/dart/client.py 가 읽고 로그에서 가림). 어떤 파일에도 남기지 않음.
캐시: dart_out/raw/list·document(같은 요청은 다시 받지 않음). 목록 결과 정리는 dart_out/raw/ops15b/X2/lists.json.
md: dart_out/text/ops15b/<문서종류>__<회사>__<fy 또는 날짜>__<rcept_no>.md (ops15_prep.xml_to_md — 본문 문서만).

목록 범위(사용자 요청 REQUEST15b.md 작업 B·C·E):
- KB금융지주 00688996: 캐시 19990101~20260831 → 사업보고서 (2014.12)·(2016.12)·(2017.12) 본·정정.
- NH농협금융지주 00908021: 캐시는 20110701~20121231·20200101~ 뿐 → 20130101~20131231 새로 부름(사업보고서 (2012.12)).
- 우리금융지주 01350869: 캐시 19990101~20260831 → 2024-08-01~2025-07-31 접수분.
- 한국씨티금융지주 00859707·한국스탠다드차타드금융지주 00776486(corpCode 캐시): 20140101~20151231 새로 부름(사업보고서 (2013.12)).
- 작업 E 주요사항보고서 20140514005150·20150507001778 은 접수번호로 바로 document.

쓰는 법: python3 scripts/dart/ops15b_X2_fetch.py list|docs
"""
import csv
import glob
import hashlib
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))

RAWX = os.path.join(ROOT, "dart_out", "raw", "ops15b", "X2")
TXT = os.path.join(ROOT, "dart_out", "text", "ops15b")
LISTS = os.path.join(RAWX, "lists.json")
DOCS = os.path.join(RAWX, "docs.json")

CORPS = {
    "KB금융지주": "00688996",
    "NH농협금융지주": "00908021",
    "우리금융지주": "01350869",
    "한국씨티금융지주": "00859707",
    "한국SC금융지주": "00776486",   # corpCode 이름 「한국스탠다드차타드금융지주」
    "한국씨티은행": "00161444",      # 작업 E 합병 주요사항보고서(사용자 지정 접수번호) 제출인 — 정정판 찾기용
    "한국스탠다드차타드은행": "00148504",
}
NEW_LISTS = [  # (label, bgn, end) — 캐시에 없는 범위만 새로 부름
    ("NH농협금융지주", "20130101", "20131231"),
    ("한국씨티금융지주", "20140101", "20151231"),
    ("한국SC금융지주", "20140101", "20151231"),
    ("한국씨티은행", "20140501", "20141231"),
    ("한국스탠다드차타드은행", "20150501", "20151231"),
]
C_NAME_RE = re.compile(r"편입|타법인주식|동양|ABL|에이비엘")  # 우리 목록에서 문서를 받을 보고서명(자회사·주식·취득 낱말 결과는 lists.json 에 전부)
C_EXTRA_RE = re.compile(r"증권신고서\(채무증권\)|^투자설명서$|분기보고서 \(2025\.03\)")  # 2025.5 전후 지주 자체 신고서·분기보고서(판단: 편입 승인 시기 서술 확인용)


def client(max_calls=60):
    from client import DartClient
    return DartClient(os.path.join(ROOT, "dart_out"), delay=0.5, max_calls=max_calls)


def cached_list(cc):
    out, seen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT, "dart_out", "raw", "list", cc + "_*.json"))):
        if f.endswith(".meta.json"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        meta = {}
        try:
            meta = json.load(open(f + ".meta.json", encoding="utf-8"))
        except Exception:
            pass
        for r in d.get("list", []) or []:
            if r["rcept_no"] in seen:
                continue
            seen.add(r["rcept_no"])
            out.append(dict(rcept_no=r["rcept_no"], rcept_dt=r.get("rcept_dt", ""), report_nm=r.get("report_nm", "").strip(),
                            flr_nm=r.get("flr_nm", ""), rm=r.get("rm", ""), corp_name=r.get("corp_name", ""),
                            list_raw=os.path.relpath(f, ROOT), list_fetched_at=meta.get("fetched_at", "")))
    return out


def cmd_list():
    c = client(20)
    for label, bgn, end in NEW_LISTS:
        page = 1
        while True:
            res = c.call("list", dict(corp_code=CORPS[label], bgn_de=bgn, end_de=end, page_no=page, page_count=100), phase="ops15b_X2")
            d = res.data or {}
            print("list", label, bgn, end, "p", page, res.status, "total", d.get("total_count"), "cached", res.cached)
            if res.status not in ("000",) or page >= int(d.get("total_page") or 1):
                break
            page += 1
    res = {}
    for label, cc in CORPS.items():
        rows = cached_list(cc)
        res[label] = rows
    os.makedirs(RAWX, exist_ok=True)
    json.dump(res, open(LISTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in res.items():
        print(k, len(v))


def picks():
    L = json.load(open(LISTS, encoding="utf-8"))
    out = []
    # 작업 B — KB FY2014·2016·2017, NH FY2012
    for label, fys in (("KB금융지주", ("2014", "2016", "2017")), ("NH농협금융지주", ("2012",))):
        for r in L[label]:
            m = re.search(r"사업보고서\s*\((\d{4})\.12\)", r["report_nm"])
            if m and m.group(1) in fys:
                out.append(dict(task="B", doc_kind="사업보고서", label=label, fy=m.group(1),
                                kind="정정" if r["report_nm"].startswith("[") else "본", **r))
    # 작업 C — 우리 2024-08~2025-07
    for r in L["우리금융지주"]:
        if not ("20240801" <= r["rcept_dt"] <= "20250731"):
            continue
        if C_NAME_RE.search(r["report_nm"]) or C_EXTRA_RE.search(r["report_nm"]):
            out.append(dict(task="C", doc_kind="공시", label="우리금융지주", fy=r["rcept_dt"],
                            kind="정정" if r["report_nm"].startswith("[") else "본", **r))
    # 작업 E — 두 지주 FY2013 사업보고서 + 합병 주요사항보고서 2건
    for label in ("한국씨티금융지주", "한국SC금융지주"):
        for r in L[label]:
            if re.search(r"사업보고서\s*\(2013\.12\)", r["report_nm"]):
                out.append(dict(task="E", doc_kind="사업보고서", label=label, fy="2013",
                                kind="정정" if r["report_nm"].startswith("[") else "본", **r))
    known = {r["rcept_no"] for r in out}
    for rc, label in (("20140514005150", "한국씨티금융지주"), ("20150507001778", "한국SC금융지주")):
        if rc in known:
            continue
        hit = None
        for lab in ("한국씨티금융지주", "한국SC금융지주", "한국씨티은행", "한국스탠다드차타드은행"):
            for r in L.get(lab, []):
                if r["rcept_no"] == rc:
                    hit = r
        base = hit or dict(rcept_no=rc, rcept_dt=rc[:8], report_nm="", flr_nm="", rm="", corp_name="", list_raw="", list_fetched_at="")
        out.append(dict(task="E", doc_kind="주요사항보고서", label=label, fy=base["rcept_dt"], kind="본", **base))
    # 참고: 지주 쪽이 따로 낸 같은 날 합병 주요사항보고서(본)와 양쪽 [기재정정] — 사용자 지정 접수번호와 글이 같은지 대조용
    known = {r["rcept_no"] for r in out}
    for label in ("한국씨티금융지주", "한국SC금융지주", "한국씨티은행", "한국스탠다드차타드은행"):
        for r in L.get(label, []):
            if re.search(r"주요사항보고서\(합병결정\)", r["report_nm"]) and r["rcept_no"] not in known:
                kind = ("정정" if r["report_nm"].startswith("[") else "본") + ("(지주 제출·참고)" if "지주" in label else "(은행 제출·참고)")
                lab = label if "지주" in label else ("한국씨티금융지주" if "씨티" in label else "한국SC금융지주")
                out.append(dict(task="E", doc_kind="주요사항보고서", label=lab, fy=r["rcept_dt"], kind=kind, filer=label, **r))
    return out


def cmd_docs():
    from ops15_prep import xml_to_md
    c = client(60)
    os.makedirs(TXT, exist_ok=True)
    rows = []
    for p in picks():
        res = c.call("document", dict(rcept_no=p["rcept_no"]), phase="ops15b_X2")
        row = dict(p)
        row.update(doc_status=res.status, doc_message=(res.message or "")[:80],
                   raw_path=("dart_out/" + res.raw_path) if res.raw_path else "", raw_sha256=res.raw_sha256 or "",
                   cached="Y" if res.cached else "N", fetched_at=res.fetched_at or "", text_path="", member="", note="")
        if res.status == "000" and res.body:
            try:
                md, member, enc = xml_to_md(res.body, p["rcept_no"])
                dk = p["doc_kind"] if p["doc_kind"] != "공시" else re.sub(r"[\[\]\s()/]", "", p["report_nm"])[:30]
                fyd = ("FY" + p["fy"]) if p["doc_kind"] == "사업보고서" else p["rcept_dt"]
                path = os.path.join(TXT, f"{dk}__{p['label']}__{fyd}__{p['rcept_no']}.md")
                head = (f"# {p['report_nm'] or p['doc_kind']} — {p['label']} ({fyd})\n\n- 접수번호 {p['rcept_no']} · 접수일 {p['rcept_dt']} · "
                        f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={p['rcept_no']}\n- 원문: OpenDART document.xml `{row['raw_path']}` "
                        f"(sha256 {res.raw_sha256}) · 멤버 {member} · 받은 시각 {res.fetched_at}\n"
                        "- 쪽 번호 없음(XML). 위치는 「[절 n]」(제목 순번)·「[표 n]」(표 순번). 글자는 XML 그대로(태그만 걷어냄).\n\n")
                with open(path, "w", encoding="utf-8", newline="\n") as w:
                    w.write(head + md)
                row.update(text_path=os.path.relpath(path, ROOT), member=member)
                # 받은 원본 사본(작업 폴더)
                dst = os.path.join(RAWX, "document", p["rcept_no"] + ".zip")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                src = os.path.join(ROOT, row["raw_path"])
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copyfile(src, dst)
            except Exception as e:
                row["note"] = f"변환 실패 {type(e).__name__}: {e}"
        rows.append(row)
        print(p["task"], p["label"], p["fy"], p["kind"], p["rcept_no"], p["report_nm"][:40], res.status, "cache" if res.cached else "net")
    json.dump(rows, open(DOCS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    {"list": cmd_list, "docs": cmd_docs}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
