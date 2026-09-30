# -*- coding: utf-8 -*-
"""8차 — 금융지주 리스크관리 체계 원문 추출(원문_지주리스크체계.csv).

대상: KB·신한·하나·우리·메리츠·iM 금융지주, 가능하면 NH농협·한국투자금융지주.
문서: FY2025 지배구조·보수체계 연차보고서(각사 IR, 6차 목록), FY2025 사업보고서
(OpenDART 11011, 기재정정 포함) Ⅱ. 사업의 내용 중 위험관리 절, 경영공시 최신 분기,
그리고 지주 전환 증권신고서 3건(메리츠화재 2010-12 인적분할, 우리은행 2018 주식이전,
메리츠금융지주 2022 주식교환)의 위험관리·내부통제·지주 운영계획 문단.

1~7차와 같은 규율: 받은 원본은 손대지 않고 그대로 두고 출처·시각·sha256 을 남긴다.
인용은 원문 그대로, 요약·해석은 note 에만, 없으면 「문서에 없음」. 정정본은 모두 받고
어느 것이 최종인지 판정하지 않는다.

    python3 scripts/dart/risk8.py fetch-reports   # 연차보고서 FY2025(공시연도 2026) 다시 받기
    python3 scripts/dart/risk8.py fetch-dart      # 사업보고서 FY2025·증권신고서 원문(document.xml)
    python3 scripts/dart/risk8.py fetch-viewer    # 같은 문서의 DART 뷰어 본문 PDF(쪽 번호용)
    python3 scripts/dart/risk8.py fetch-disclosure  # 경영공시 2026.6월말(DISCLOSURE 목록)
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

OUT = "dart_out"
WORK = os.path.join(OUT, "risk8")

# (출력 라벨, DART 등록명, corp_code, 종목코드). corp_code 가 없으면 corpCode.xml 에서
# 종목코드로 찾는다(메리츠·한국금융지주는 설정에 고유번호가 없다).
CORPS = [
    ("KB금융지주", "KB금융", "00688996", "105560"),
    ("신한금융지주", "신한지주", "00382199", "055550"),
    ("하나금융지주", "하나금융지주", "00547583", "086790"),
    ("우리금융지주", "우리금융지주", "01350869", "316140"),
    ("메리츠금융지주", "메리츠금융지주", "", "138040"),
    ("iM금융지주", "iM금융지주", "00878915", "139130"),
    ("NH농협금융지주", "농협금융지주", "00908021", ""),
    ("한국투자금융지주", "한국금융지주", "", "071050"),
]
LABELS = [c[0] for c in CORPS]

# 지주 전환 증권신고서 — 2차에서 받은 본문 PDF 가 handoff/원본_주요신고서본문.zip 에 있다.
CONVERSION = [
    # (출력 라벨, 사건, 접수번호 또는 None(목록으로 찾음), 비고)
    ("메리츠금융지주", "메리츠화재 인적분할(2011 지주 설립)", "20101210000020", "zip"),
    ("우리금융지주", "우리은행 주식이전(2019 지주 설립)", "20181108000394", "zip"),
    ("메리츠금융지주", "메리츠금융지주 주식교환(2022 완전자회사화)", None, "dart"),
]
MERITZ_2022_WINDOW = ("20221101", "20230228")

# 경영공시 최신 분기(2026.6월말) — 각사 IR 경영공시 메뉴에서 찾은 파일(2026-09-30 확인).
# 응답 헤더만 먼저 확인했다(본문 미수신). 크기 칸은 그때 헤더의 Content-Length(없으면 빈칸).
# (라벨, 게시 제목, 게시일(보이는 곳만), 방식, 다운로드 URL, Referer/목록, POST 본문, 헤더 크기, 찾은 곳)
DISCLOSURE = [
    ("KB금융지주", "2026년 상반기 KB금융지주 현황", "2026-08-31", "GET",
     "https://www.kbfg.com/api/download/board/14863", "https://www.kbfg.com/", None, "3665070",
     "GET https://www.kbfg.com/api/kbfg/posts?bulbdId=2&page=1&pageSize=10 → fileId 14863"),
    ("신한금융지주", "2026년 상반기 신한금융지주회사 현황", "2026-08-31", "GET",
     "https://www.shinhangroup.com/main/downloadAttach?attachNo=952cc7137d344eaebd5df5a8191a45bf&seq=1",
     "https://www.shinhangroup.com/", None, "",
     "POST /api/v1/ir/disclosure_management/list (pageType=FRONT&lang=KOR&current=1)"),
    ("하나금융지주", "2026년 2분기 하나금융지주회사 현황", "", "GET:8002",
     "https://www.hanafn.com:8002/download/10080193/crossDownload.do", "https://www.hanafn.com/", None, "",
     "hanafn 경영공시 목록 — :8002 가 끊기면 포트를 뗀 443 으로(6차와 같음)"),
    ("우리금융지주", "2026년 상반기 우리금융지주 현황", "", "GET",
     "https://www.woorifg.com/cmm/fms/FileDown.do?fileId=FILE_000000000004555&saveFileNm=202608310428140410.pdf&fileSeq=0",
     "https://www.woorifg.com/", None, "7218755", "woorifg 경영공시 게시판(legacy TLS)"),
    ("메리츠금융지주", "제17기 2분기 경영공시", "2026-08-31", "GET",
     "https://www.meritzgroup.com/commfiles/hld/attach/2026/20260831/202608311425251450031U.pdf",
     "https://www.meritzgroup.com/", None, "451171",
     "POST /web/ir2_search.do (bd_div_cd=IR003) → file_url /hld/attach/2026/20260831/202608311425251450031U.pdf"),
    ("iM금융지주", "제16기 상반기 아이엠금융지주현황 공시", "2026-08-31", "GET",
     "https://www.imfngroup.com/ybbsR3.fg?putup_writ_seq=4421&file_seq=1",
     "https://www.imfngroup.com/ir0202.fg", None, "2313695",
     "POST /ybbsR1.fg (IN_DATA_JSON, bbs_no=13) → PUTUP_WRIT_SEQ 4421, RGDT 20260831"),
    ("NH농협금융지주", "2026년 상반기 NH농협금융지주현황", "", "GET",
     "https://www.nhfngroup.com/user/disclosureDown.do?siteId=nhfngroup&disclosureSeq=339",
     "https://www.nhfngroup.com/user/indexSub.do?codyMenuSeq=1218157519&siteId=nhfngroup", None, "4175444",
     "indexSub.do?codyMenuSeq=1218157519 (경영공시) → disclosureSeq 339"),
    ("한국투자금융지주", "제25기 2분기 경영공시자료", "", "POST",
     "https://www.koreaholdings.com/common/fildDownload", "https://www.koreaholdings.com/kr/bbs/manage/list",
     {"real_filename": "/attach/2026/08/31/Up_admin_1_20260831163102.pdf",
      "filename": "FY2026 2Q 한국투자금융지주 경영공시_vf.pdf"}, "1097560",
     "/kr/bbs/manage/list goRead('1729') → downloadFile(…, /attach/2026/08/31/Up_admin_1_20260831163102.pdf)"),
]


def _w(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(path + ".tmp", path)


# ── 1. 연차보고서 ─────────────────────────────────────────────────────────
def fetch_reports():
    """6차 목록(scripts/dart/data/governance_list.csv) 중 공시연도 2026(=FY2025) 행만,
    6차와 같은 방식(governance.fetch_one)으로 받고 6차 기록 sha256 과 대조한다."""
    import governance
    rows = [r for r in governance.load_list()
            if (r.get("공시연도") or "").strip() == "2026"
            and (r.get("구분") or "").strip() != "조직도"
            and (r.get("지주명") or "").strip() in LABELS]
    prev = {}
    p = os.path.join("handoff", "연차보고서_파일목록.csv")
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        prev[r["파일명"]] = r.get("sha256", "")
    opener, _jar = governance.make_opener()
    out = []
    for i, r in enumerate(rows):
        rec = governance.fetch_one(opener, r, OUT, verbose=True)
        want = prev.get(rec.get("저장파일명", ""), "")
        rec["6차sha256"] = want
        rec["6차와동일"] = ("Y" if want and want == rec.get("sha256") else
                         "N(원본 변경 — 새 파일 보존)" if want else "6차 기록 없음")
        out.append(rec)
        if i + 1 < len(rows):
            import time
            time.sleep(governance.DELAY)
    cols = ["지주명", "저장파일명", "공시유형", "공시연도", "공시일", "제목", "방식", "url",
            "실제url", "http_status", "실제크기", "sha256", "6차sha256", "6차와동일", "성공",
            "실패사유", "fetched_at"]
    _w(os.path.join(WORK, "연차보고서_FY2025.csv"), out, cols)
    ok = sum(1 for r in out if r.get("성공") == "Y")
    same = sum(1 for r in out if r["6차와동일"] == "Y")
    print("연차보고서 FY2025 — 대상 %d · 성공 %d · 6차와 sha256 동일 %d" % (len(out), ok, same))
    return out


# ── 2. DART ───────────────────────────────────────────────────────────────
def _corp_codes(c):
    need = [x for x in CORPS if not x[2]]
    codes = {x[0]: x[2] for x in CORPS if x[2]}
    if need:
        import corpcode
        idx, _res = corpcode.load_corp_index(c, phase="risk8")
        by_stock = {}
        for e in idx:
            if e.get("stock_code"):
                by_stock.setdefault(e["stock_code"].strip(), []).append(e)
        for lab, dname, _cc, stock in need:
            hits = by_stock.get(stock, [])
            if len(hits) != 1:
                raise SystemExit("%s 종목코드 %s 로 corp_code 를 하나로 못 찾음: %s"
                                 % (lab, stock, [h.get("corp_name") for h in hits]))
            codes[lab] = hits[0]["corp_code"]
            print("  corp_code %s = %s (%s, 종목 %s)" % (lab, codes[lab], hits[0].get("corp_name"), stock))
    return codes


def _list_all(c, params):
    rows, page = [], 1
    while True:
        res = c.call("list", dict(params, page_no=str(page), page_count="100"), phase="risk8")
        if res.status == "013":          # 조회된 데이터 없음
            break
        if not res.ok:
            raise SystemExit("list 실패 %s %s %s" % (params, res.status, res.message))
        rows += [dict(r, _raw=res.raw_path, _sha=res.raw_sha256, _at=res.fetched_at)
                 for r in res.rows()]
        total = int((res.data or {}).get("total_page") or 1)
        if page >= total:
            break
        page += 1
    return rows


def fetch_dart():
    import client as dclient
    c = dclient.DartClient(OUT, delay=0.5)
    codes = _corp_codes(c)
    docs = []
    # FY2025 사업보고서 — 기재정정·첨부정정까지 모두
    for lab, dname, _cc, _st in CORPS:
        rows = _list_all(c, {"corp_code": codes[lab], "bgn_de": "20260101",
                             "end_de": "20260930", "pblntf_ty": "A"})
        hit = [r for r in rows if "사업보고서" in r.get("report_nm", "")
               and "2025.12" in r.get("report_nm", "")]
        if not hit:
            docs.append(dict(corp_label=lab, doc_kind="사업보고서", rcept_no="", report_nm="",
                             rcept_dt="", 상태="없음", 비고="list(A, 2026-01-01~09-30)에 사업보고서 (2025.12) 없음"))
        for r in hit:
            docs.append(dict(corp_label=lab, doc_kind="사업보고서", rcept_no=r["rcept_no"],
                             report_nm=r["report_nm"], rcept_dt=r["rcept_dt"], corp_name=r.get("corp_name"),
                             list_raw=r["_raw"], list_sha256=r["_sha"], 상태="목록확인"))
    # 메리츠금융지주 2022 주식교환 증권신고서 — 기재정정 포함 전부
    rows = _list_all(c, {"corp_code": codes["메리츠금융지주"], "bgn_de": MERITZ_2022_WINDOW[0],
                         "end_de": MERITZ_2022_WINDOW[1]})
    for r in rows:
        if "증권신고서" in r.get("report_nm", ""):
            docs.append(dict(corp_label="메리츠금융지주", doc_kind="증권신고서",
                             사건="메리츠금융지주 주식교환(2022 완전자회사화)", rcept_no=r["rcept_no"],
                             report_nm=r["report_nm"], rcept_dt=r["rcept_dt"], corp_name=r.get("corp_name"),
                             list_raw=r["_raw"], list_sha256=r["_sha"], 상태="목록확인"))
    # 원문 XML(document.xml) — 절 구조용
    for d in docs:
        if not d.get("rcept_no"):
            continue
        res = c.call("document", {"rcept_no": d["rcept_no"]}, phase="risk8")
        d.update(document_status=res.status, document_raw=res.raw_path,
                 document_sha256=res.raw_sha256, document_at=res.fetched_at)
    # 2010·2018 전환 신고서 — git 에 있는 본문 PDF 를 그대로 푼다(다시 받지 않는다)
    zp = os.path.join("handoff", "원본_주요신고서본문.zip")
    with zipfile.ZipFile(zp) as z:
        for lab, ev, rc, src in CONVERSION:
            if src != "zip":
                continue
            member = "doc/%s/본문.pdf" % rc
            dest = os.path.join(OUT, "doc", rc, "본문.pdf")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            data = z.read(member)
            with open(dest, "wb") as f:
                f.write(data)
            import hashlib
            docs.append(dict(corp_label=lab, doc_kind="증권신고서", 사건=ev, rcept_no=rc,
                             report_nm="(2차 수집 본문)", 상태="zip에서 복원",
                             pdf=dest, pdf_sha256=hashlib.sha256(data).hexdigest(),
                             비고="handoff/원본_주요신고서본문.zip!" + member))
    cols = ["corp_label", "doc_kind", "사건", "rcept_no", "report_nm", "rcept_dt", "corp_name",
            "상태", "list_raw", "list_sha256", "document_status", "document_raw",
            "document_sha256", "document_at", "pdf", "pdf_sha256", "비고"]
    _w(os.path.join(WORK, "DART_문서목록.csv"), docs, cols)
    print("DART 문서 %d건(사업보고서 %d · 증권신고서 %d) · API 호출 %d"
          % (len(docs), sum(d["doc_kind"] == "사업보고서" for d in docs),
             sum(d["doc_kind"] == "증권신고서" for d in docs), c.network_calls))
    return docs


def fetch_viewer_pdfs():
    """DART 뷰어의 본문 PDF(쪽 번호용) — dartweb.collect 를 그대로 쓴다."""
    import dartweb
    rows = list(csv.DictReader(open(os.path.join(WORK, "DART_문서목록.csv"), encoding="utf-8-sig")))
    want = [r["rcept_no"] for r in rows if r["rcept_no"] and r["상태"] != "zip에서 복원"]
    res = dartweb.collect(os.path.abspath(OUT), rcept_nos=want)
    print("뷰어 PDF — 성공 %s · 실패 %s · 미수집 %s" % (res.get("성공"), res.get("실패"), res.get("미수집")))
    return res


# ── 3. 경영공시 ───────────────────────────────────────────────────────────
def fetch_disclosure():
    """DISCLOSURE 의 파일을 받아 dart_out/raw/risk8/경영공시/<라벨>/ 에 그대로 둔다.
    파일마다 meta json(출처·방식·시각·HTTP 상태·헤더·크기·sha256). 실패는 사유와 함께 남긴다."""
    import hashlib
    import time
    import urllib.error
    import urllib.parse
    import governance
    from datetime import datetime, timezone
    opener, _jar = governance.make_opener()
    out = []
    for i, (lab, title, posted, how, url, ref, post, hlen, found) in enumerate(DISCLOSURE):
        d = os.path.join(OUT, "raw", "risk8", "경영공시", lab)
        os.makedirs(d, exist_ok=True)
        rec = dict(corp_label=lab, 제목=title, 게시일=posted, 방식=how, url=url, 목록=ref,
                   찾은곳=found, 헤더크기=hlen, 실제url="", http_status="", content_type="",
                   content_disposition="", 저장파일="", 실제크기="", sha256="", 성공="N",
                   실패사유="", fetched_at="")
        last = ""
        for attempt in range(1, governance.ATTEMPTS + 1):
            try:
                if how == "POST":
                    opener.open(governance._req(ref), timeout=governance.TIMEOUT).read(1 << 16)
                    time.sleep(governance.DELAY)
                    body = urllib.parse.urlencode(post).encode()
                    cands = [(url, body)]
                else:
                    cands = [(url, None)]
                    pr = urllib.parse.urlparse(url)
                    if pr.port:                      # 하나 :8002 → 443 (6차와 같은 이유)
                        cands.append((urllib.parse.urlunparse(pr._replace(netloc=pr.hostname)), None))
                resp, err = None, ""
                for cu, body in cands:
                    try:
                        resp = opener.open(governance._req(cu, referer=ref, data=body),
                                           timeout=governance.TIMEOUT)
                        rec["실제url"] = cu
                        break
                    except Exception as ex:          # noqa: BLE001
                        err = "%s: %s" % (type(ex).__name__, ex)
                if resp is None:
                    raise urllib.error.URLError(err)
                rec["http_status"] = str(resp.status)
                rec["content_type"] = resp.headers.get("Content-Type", "")
                rec["content_disposition"] = resp.headers.get("Content-Disposition", "")
                data = resp.read()
                resp.close()
                rec["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                if not data.lstrip()[:5] == b"%PDF-":
                    raise ValueError("PDF 시그니처 아님 — 앞부분: %r" % data[:80])
                name = "%s_경영공시_2026_2Q.pdf" % lab
                p = os.path.join(d, name)
                with open(p + ".part", "wb") as f:
                    f.write(data)
                os.replace(p + ".part", p)
                rec.update(저장파일=p, 실제크기=str(len(data)),
                           sha256=hashlib.sha256(data).hexdigest(), 성공="Y", 실패사유="")
                break
            except Exception as e:                   # noqa: BLE001 — 사유를 남기고 재시도
                last = "%s: %s" % (type(e).__name__, e)
                rec["실패사유"] = last
                if attempt < governance.ATTEMPTS:
                    time.sleep(governance.DELAY * attempt * 2)
        if rec["성공"] == "Y" and hlen and hlen != rec["실제크기"]:
            rec["실패사유"] = "헤더 크기 %s ≠ 실제 %s (보존, 판정 없음)" % (hlen, rec["실제크기"])
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        print("  %-10s %s %s" % (lab, "OK %s bytes" % rec["실제크기"] if rec["성공"] == "Y"
                                  else "실패", rec["실패사유"][:80]))
        out.append(rec)
        if i + 1 < len(DISCLOSURE):
            time.sleep(governance.DELAY)
    _w(os.path.join(WORK, "경영공시_2026_2Q.csv"), out, list(out[0].keys()))
    print("경영공시 — 대상 %d · 성공 %d" % (len(out), sum(r["성공"] == "Y" for r in out)))
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "fetch-disclosure":
        import governance
        governance._ensure_legacy_tls()      # 우리·iM legacy renegotiation — 한 번 재실행
        fetch_disclosure()
        return 0
    if cmd == "fetch-reports":
        import governance
        governance._ensure_legacy_tls()      # 우리금융 legacy renegotiation — 한 번 재실행
        fetch_reports()
        return 0
    if cmd == "fetch-dart":
        fetch_dart()
        return 0
    if cmd == "fetch-viewer":
        fetch_viewer_pdfs()
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
