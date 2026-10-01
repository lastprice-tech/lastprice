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
    python3 scripts/dart/risk8.py extract         # 받은 PDF → dart_out/text/risk8/*.txt (=== p.N ===)
    python3 scripts/dart/risk8.py candidates      # 인용 범위 안 문장을 항목 어휘로 태깅 → 후보문장·검색기록
    python3 scripts/dart/risk8.py emit            # data/risk8_선별.json → handoff/원문_지주리스크체계(_근거).csv
    python3 scripts/dart/verify8.py               # 검증

선별(risk8_선별.json)은 후보와 원문 쪽을 읽고 사람이(이 작업에서는 Claude 가) 고른 인용이다.
인용은 텍스트 파일의 해당 쪽 글자 그대로이고(줄바꿈만 공백), verify8 이 쪽마다 대조한다.
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


# ── 4. 텍스트화(쪽 번호 보존) ─────────────────────────────────────────────
TEXT = os.path.join(OUT, "text", "risk8")


def _sources():
    """(doc_id, corp_label, doc_kind, 설명, PDF 경로, 비고) — 받은 원본 PDF 전부."""
    src = []
    p = os.path.join(WORK, "연차보고서_FY2025.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            if r.get("성공") != "Y":
                continue
            fn = r["저장파일명"]
            src.append(("연차보고서__" + os.path.splitext(fn)[0], r["지주명"], "연차보고서",
                        "%s (공시일 %s)" % (r["제목"], r["공시일"]),
                        os.path.join(OUT, "raw", "governance", r["지주명"], fn), r.get("url", "")))
    p = os.path.join(WORK, "DART_문서목록.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            if not r["rcept_no"]:
                continue
            pdf = os.path.join(OUT, "doc", r["rcept_no"], "본문.pdf")
            src.append(("%s__%s__%s" % (r["doc_kind"], r["corp_label"], r["rcept_no"]),
                        r["corp_label"], r["doc_kind"],
                        "%s %s (접수 %s)" % (r.get("사건") or "", r["report_nm"], r["rcept_dt"] or r["rcept_no"]),
                        pdf, "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + r["rcept_no"]))
    p = os.path.join(WORK, "경영공시_2026_2Q.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            if r.get("성공") != "Y":
                continue
            src.append(("경영공시__" + r["corp_label"], r["corp_label"], "경영공시", r["제목"],
                        r["저장파일"], r["실제url"] or r["url"]))
    return src


def extract():
    """PDF 를 쪽마다 `=== p.N ===` 표지와 함께 텍스트로. 원본 sha256 이 같으면 다시 하지 않는다.
    스캔본(글자 없음)은 표시만 하고 OCR 하지 않는다."""
    import hashlib
    import pypdf
    os.makedirs(TEXT, exist_ok=True)
    idx_p = os.path.join(WORK, "텍스트목록.csv")
    prev = {}
    if os.path.exists(idx_p):
        prev = {r["doc_id"]: r for r in csv.DictReader(open(idx_p, encoding="utf-8-sig"))}
    out = []
    for doc_id, lab, kind, desc, pdf, url in _sources():
        rec = dict(doc_id=doc_id, corp_label=lab, doc_kind=kind, 설명=desc, 원본=pdf, 출처=url,
                   원본sha256="", 쪽수="", 글자수="", 빈쪽수="", 스캔추정="", 텍스트="",
                   텍스트sha256="", 상태="")
        if not os.path.exists(pdf):
            rec["상태"] = "원본 PDF 없음"
            out.append(rec)
            continue
        h = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
        tp = os.path.join(TEXT, doc_id + ".txt")
        old = prev.get(doc_id)
        if old and old.get("원본sha256") == h and os.path.exists(tp) and old.get("상태") == "추출":
            out.append(old)
            continue
        rec["원본sha256"] = h
        try:
            reader = pypdf.PdfReader(pdf)
            parts, empty, total = [], 0, 0
            for i, pg in enumerate(reader.pages, 1):
                try:
                    t = pg.extract_text() or ""
                except Exception as e:                # noqa: BLE001
                    t = ""
                    parts.append("=== p.%d === [추출 실패 %s]" % (i, type(e).__name__))
                    empty += 1
                    continue
                if not t.strip():
                    empty += 1
                total += len(t)
                parts.append("=== p.%d ===\n%s" % (i, t))
            body = "\n".join(parts) + "\n"
            with open(tp + ".part", "w", encoding="utf-8") as f:
                f.write(body)
            os.replace(tp + ".part", tp)
            n = len(reader.pages)
            rec.update(쪽수=str(n), 글자수=str(total), 빈쪽수=str(empty),
                       스캔추정="Y" if total / max(1, n) < 60 else "N", 텍스트=tp,
                       텍스트sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(), 상태="추출")
        except Exception as e:                        # noqa: BLE001
            rec["상태"] = "PDF 열기 실패: %s: %s" % (type(e).__name__, e)
        print("  %-60s %s쪽 %s자 %s" % (doc_id[:60], rec["쪽수"], rec["글자수"], rec["상태"]))
        out.append(rec)
    _w(idx_p, out, list(out[0].keys()))
    print("텍스트 — 문서 %d · 추출 %d · 스캔추정 %d · 원본없음 %d"
          % (len(out), sum(r["상태"] == "추출" for r in out), sum(r["스캔추정"] == "Y" for r in out),
             sum(r["상태"] == "원본 PDF 없음" for r in out)))
    return out


# ── 5. 후보 문장 ──────────────────────────────────────────────────────────
# 항목별 어휘(정규식). 태깅은 후보를 좁히는 용도일 뿐, 인용 여부는 사람이(내가) 읽고 정한다.
FIELDS = [
    ("risk_committee", r"위험관리\s*위원회|리스크\s*관리\s*위원회|리스크위원회|Risk\s*Management\s*Committee"),
    ("group_council", r"(리스크|위험)\s*(관리)?\s*(실무)?\s*(협의회|협의체|심의회)|리스크정책위원회|실무\s*위원회|실무\s*협의회"),
    ("cro", r"CRO|위험관리\s*책임자|리스크\s*관리\s*책임자|최고\s*리스크|Chief\s*Risk"),
    ("raf", r"위험\s*선호|리스크\s*선호|Risk\s*Appetite|RAF|위험\s*성향|리스크\s*성향|(위험|리스크)\s*한도|허용\s*한도|한도\s*(관리|설정|배분)|(위험)?자본\s*배분|위험\s*자본\s*(한도|배분)"),
    ("measurement", r"요구\s*자본|내부\s*자본|가용\s*자본|통합\s*(위험|리스크)|VaR|자본\s*적정성|ICAAP|위험\s*자본|경제적\s*자본|Risk\s*Capital|위험\s*측정|리스크\s*측정"),
    ("reporting", r"(리스크|위험)[^.。]{0,40}보고|보고[^.。]{0,20}(리스크|위험)|MIS|모니터링|리스크\s*관리\s*시스템"),
    ("stress", r"위기\s*상황\s*분석|스트레스\s*테스트|Stress|위기\s*상황\s*시나리오|비상\s*(조달|자금|계획)|컨틴전시|Contingency|위기\s*관리"),
    ("oprisk", r"운영\s*(리스크|위험)|손실\s*사건|손실\s*데이터|BCP|업무\s*연속성|위탁|IT\s*리스크|정보\s*보호|사이버"),
    ("compensation", r"성과\s*보수|이연\s*지급|환수|Clawback|클로백|(리스크|위험)\s*(를|을)?\s*(고려|반영|조정)[^.。]{0,20}(성과|보수|평가)|(성과|보수)[^.。]{0,30}(리스크|위험)\s*(조정|반영|고려)|보수\s*체계|보수\s*정책|리스크\s*조정"),
    ("org", r"리스크\s*관리\s*(부|팀|본부|부문|실|총괄|그룹|센터|조직)|위험\s*관리\s*(부|팀|본부|부문|실|조직|전담)|리스크\s*총괄|리스크\s*검증|전담\s*조직|리스크\s*관리\s*인력"),
    # 9차 추가 열(리스크부문 v0.4, 2026-10-01)
    ("subsidiary_control", r"사전\s*협의|사전\s*승인|협의\s*사항|승인\s*사항|공문|공식\s*문서|자회사[^.。]{0,30}(평가|지시|요청|통보)|(CRO|위험관리\s*책임자|리스크\s*관리\s*책임자)[^.。]{0,30}평가"),
    ("model_validation", r"모형\s*검증|모델\s*검증|검증\s*(조직|부서|팀|결과|주기)|독립적\s*(인\s*)?검증|적합성\s*검증|사후\s*검증|백\s*테스팅|Back\s*-?\s*testing|Validation"),
    ("internal_capital", r"내부\s*자본|자본\s*버퍼|완충\s*자본|목표\s*(비율|수준)|내부\s*목표|자본\s*적정성\s*평가|ICAAP|경제적\s*자본|위험\s*자본"),
    ("early_warning", r"조기\s*경보|Early\s*Warning|EWS|위기\s*단계|위기\s*상황\s*(단계|등급|판단)|비상\s*(대응|대책)|위기\s*대응|컨틴전시|Contingency"),
    ("contagion", r"(위험|리스크)[^.。]{0,10}전이|전이\s*(위험|리스크|효과)|전염|교차\s*판매|공동\s*(상품|개발|영업|마케팅)|계열\s*(사)?\s*(판매|거래)\s*비중|평판\s*(리스크|위험)|그룹\s*내\s*(거래|위험)|복합\s*점포|이해\s*상충"),
    ("related_party", r"대주주|특수\s*관계|계열\s*(회사|사)?\s*(간|와의)?\s*거래|자회사\s*등?\s*과의\s*거래|내부\s*거래|신용\s*공여"),
    ("icfr", r"내부\s*회계|연결\s*내부\s*회계|ICFR"),
    # 증권신고서(지주 전환)용 보조 태그 — CSV 의 열이 아니라 근거 파일·source_text 에만 쓴다.
    ("internal_control", r"내부\s*통제|준법\s*감시|내부\s*감사"),
    ("holding_plan", r"지주\s*회사[^.。]{0,40}(운영|체제|계획|역할|기능|전략)|(경영|운영)\s*계획|자회사\s*(관리|편입)|그룹\s*(통합|시너지)"),
]
MAIN_FIELDS = [f for f, _ in FIELDS[:17]]     # 8차 10개 + 9차 7개

# 사업보고서의 「실제 위험관리 절」(사용자 결정 2026-09-30). (시작 표제, 끝 표제) — 공백을 뺀
# 글자로 찾는다. 메리츠·한국투자는 Ⅱ. 사업의 내용, 나머지는 Ⅳ. 이사의 경영진단 및 분석의견.
BIZ_SCOPE = {
    "KB금융지주": ("Ⅳ-6", "라.파생상품및위험관리정책에관한사항", r"(V|Ⅴ)\.회계감사인의감사의견등"),
    "신한금융지주": ("Ⅳ-6", "마.위험관리정책에관한사항", r"(V|Ⅴ)\.회계감사인의감사의견등"),
    "하나금융지주": ("Ⅳ-6", "라.파생상품및위험관리정책에관한사항", r"(V|Ⅴ)\.회계감사인의감사의견등"),
    "우리금융지주": ("Ⅳ-6", "라.파생상품및위험관리정책에관한사항", r"7\.우리은행주요연결종속회사에대한이사의경영진단및분석"),
    "메리츠금융지주": ("Ⅱ-5 [메리츠증권]", "나.위험관리에관한사항", r"다\.수수료현황"),
    "iM금융지주": ("Ⅳ-6", "다.파생상품및위험관리정책에관한사항", r"(V|Ⅴ)\.회계감사인의감사의견등"),
    "NH농협금융지주": ("Ⅳ-6", "라.파생상품및위험관리정책에관한사항", r"(V|Ⅴ)\.회계감사인의감사의견등"),
    "한국투자금융지주": ("Ⅱ-5 [한국투자증권]", "라.위험관리에관한사항", r"2\)한국투자저축은행"),
}


def re_split_pages(s):
    import re
    out, cur = [], None
    for m in re.finditer(r"^=== p\.(\d+) ===[^\n]*\n?", s, flags=re.M):
        if cur is not None:
            out.append((cur[0], s[cur[1]:m.start()]))
        cur = (int(m.group(1)), m.end())
    if cur is not None:
        out.append((cur[0], s[cur[1]:]))
    return out


def _nows(s):
    import re
    return re.sub(r"\s+", "", s)


def _scope(doc, pages):
    """(절 이름, [(쪽, 절 안의 글)]). 사업보고서는 BIZ_SCOPE, 나머지는 문서 전체."""
    import re
    if doc["doc_kind"] != "사업보고서":
        return "문서 전체", pages
    loc, start, end = BIZ_SCOPE[doc["corp_label"]]
    # 표제는 **줄 맨 앞**에 있을 때만 인정한다 — 본문 속 참조(「…마. 위험관리정책에 관한
    # 사항 - (3)시장위험을 참고하시기 바랍니다」, 신한 p.773)를 표제로 잡지 않기 위해서다.
    # 목차 쪽(줄표 .....)도 건너뛴다.
    out = []
    for n, t in pages:
        if not out and "....." in t:
            continue
        lines = t.split("\n")
        if not out:
            k = next((i for i, l in enumerate(lines) if _nows(l).startswith(start)), None)
            if k is None:
                continue
            lines = lines[k:]
            body = lines[1:]
            head = [lines[0]]
        else:
            body, head = lines, []
        e = next((i for i, l in enumerate(body) if re.match(end, _nows(l))), None)
        if e is not None:
            out.append((n, "\n".join(head + body[:e])))
            break
        out.append((n, "\n".join(head + body)))
    if not out:
        return "절 못 찾음(%s %s)" % (loc, start), []
    return "%s %s" % (loc, start), out


def _sentences(text):
    """쪽 안의 글을 문장·항목 단위로 자른다. 줄바꿈은 공백으로 잇고 글자는 바꾸지 않는다."""
    import re
    lines = [l.rstrip() for l in text.split("\n")]
    out, buf = [], []
    bullet = re.compile(r"^\s*([-•ㅇ○◦■□▶▷※·∙]|\(?\d{1,2}\)|[①-⑳]|[가-하]\.|[가-하]\)|\([가-하]\)|\d{1,2}\.\s)")
    for l in lines:
        if not l.strip():
            if buf:
                out.append(" ".join(buf)); buf = []
            continue
        if bullet.match(l) and buf:
            out.append(" ".join(buf)); buf = []
        buf.append(l.strip())
        if re.search(r"(다|음|함|임|됨|요)\.\s*$", l):
            out.append(" ".join(buf)); buf = []
    if buf:
        out.append(" ".join(buf))
    res = []
    for s in out:
        # 한 줄 안에 문장이 여럿이면 「다. 」에서 더 자른다
        for p in re.split(r"(?<=다\.)\s+(?=\S)", s):
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                res.append(p)
    return res


def candidates():
    import re
    idx = list(csv.DictReader(open(os.path.join(WORK, "텍스트목록.csv"), encoding="utf-8-sig")))
    comp = [(f, re.compile(rx, re.I)) for f, rx in FIELDS]
    cand, log = [], []
    for doc in idx:
        if doc["상태"] != "추출":
            continue
        pages = re_split_pages(open(doc["텍스트"], encoding="utf-8").read())
        sec, scoped = _scope(doc, pages)
        pr = "%s~%s" % (scoped[0][0], scoped[-1][0]) if scoped else ""
        hits = {f: 0 for f, _ in FIELDS}
        for n, t in scoped:
            for s in _sentences(t):
                tags = [f for f, c in comp if c.search(s)]
                for f in tags:
                    hits[f] += 1
                if tags:
                    cand.append(dict(doc_id=doc["doc_id"], corp_label=doc["corp_label"],
                                     doc_kind=doc["doc_kind"], section=sec, page=n,
                                     fields="|".join(tags), sentence=s))
        for f, rx in FIELDS:
            log.append(dict(doc_id=doc["doc_id"], corp_label=doc["corp_label"], doc_kind=doc["doc_kind"],
                            section=sec, pages=pr, field=f, regex=rx, hits=hits[f]))
        print("  %-58s %-40s p.%-9s 후보 %d" % (doc["doc_id"][:58], sec[:40], pr,
                                                sum(1 for c in cand if c["doc_id"] == doc["doc_id"])))
    _w(os.path.join(WORK, "후보문장.csv"), cand, ["doc_id", "corp_label", "doc_kind", "section", "page",
                                                "fields", "sentence"])
    _w(os.path.join(WORK, "검색기록.csv"), log, ["doc_id", "corp_label", "doc_kind", "section", "pages",
                                               "field", "regex", "hits"])
    print("후보 문장 %d · 검색기록 %d" % (len(cand), len(log)))
    return cand


# ── 6. CSV 작성 ───────────────────────────────────────────────────────────
SELECTION = os.path.join(HERE, "data", "risk8_선별.json")
HANDOFF = "handoff"
NOT_FOUND = "문서에 없음"
SEP = " ‖ "

# 행(회사×문서) — 인용 기준 문서 doc_id 와, 같은 문서의 추가·재·정정본(대조만, 판정 없음).
# 메리츠 2022 정정본 묶음은 표지 앞 20,000자(공백 제외)에 나오는 완전자회사 상호로 나눴다
# (메리츠화재해상보험주식회사 / 메리츠증권주식회사).
ROW_FY = {"연차보고서": "FY2025", "사업보고서": "FY2025", "경영공시": "2026.2Q(2026.6.30 기준)"}
CONVERSION_ROWS = {
    "증권신고서__메리츠금융지주__20101210000020": ("2010(접수 2010-12-10)", []),
    "증권신고서__우리금융지주__20181108000394": ("2018(접수 2018-11-08)", []),
    "증권신고서__메리츠금융지주__20221121000209": (
        "2022(접수 2022-11-21)",
        ["20221130001841", "20221205000327", "20221220000012", "20230102000239"]),
    "증권신고서__메리츠금융지주__20230119000440": ("2023(접수 2023-01-19)", ["20230206000364"]),
}


def _amendments(doc_id, idx):
    """같은 회사·같은 문서의 다른 본(추가공시·재공시·정정). 판정 없이 대조 대상만 고른다."""
    me = idx[doc_id]
    if me["doc_kind"] == "증권신고서":
        rcs = CONVERSION_ROWS.get(doc_id, ("", []))[1]
        return ["증권신고서__%s__%s" % (me["corp_label"], rc) for rc in rcs]
    return [d for d, r in idx.items() if d != doc_id and r["corp_label"] == me["corp_label"]
            and r["doc_kind"] == me["doc_kind"]]


def _source_meta(d):
    """행의 출처 — rcept_no_or_url · doc_name · collected_at(원본 수집 시각). 텍스트목록 한 줄 → dict."""
    import zipfile
    kind, rc = d["doc_kind"], d["doc_id"].split("__")[-1]
    out = dict(rcept_no_or_url="", doc_name="", collected_at="")
    if kind == "연차보고서":
        fn = os.path.basename(d["원본"])
        r = next((x for x in csv.DictReader(open(os.path.join(WORK, "연차보고서_FY2025.csv"),
                                                 encoding="utf-8-sig")) if x["저장파일명"] == fn), {})
        url = r.get("실제url") or r.get("url", "")
        mp = d["원본"] + ".meta.json"
        m = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
        if m.get("real_filename"):          # 한국투자: POST 다운로드 — 그 파일을 가리키는 값까지 적는다
            url = "%s (POST real_filename=%s; 게시글 %s)" % (url, m["real_filename"], m.get("게시글url", ""))
        out.update(rcept_no_or_url=url,
                   doc_name="%s (공시일 %s)" % (r.get("제목", ""), r.get("공시일", "")),
                   collected_at=r.get("fetched_at", ""))
    elif kind == "경영공시":
        r = next((x for x in csv.DictReader(open(os.path.join(WORK, "경영공시_2026_2Q.csv"),
                                                 encoding="utf-8-sig")) if x["corp_label"] == d["corp_label"]), {})
        url = r.get("실제url") or r.get("url", "")
        post = next((x[6] for x in DISCLOSURE if x[0] == d["corp_label"] and x[3] == "POST"), None)
        if post:
            url = "%s (POST real_filename=%s; 목록 %s)" % (url, post.get("real_filename", ""), r.get("목록", ""))
        out.update(rcept_no_or_url=url, doc_name=r.get("제목", ""), collected_at=r.get("fetched_at", ""))
    else:                                   # DART 사업보고서·증권신고서 — 인용 쪽은 뷰어 본문 PDF
        out["rcept_no_or_url"] = rc
        names = {x["rcept_no"]: x["report_nm"] for x in csv.DictReader(
            open(os.path.join(WORK, "DART_문서목록.csv"), encoding="utf-8-sig")) if x["rcept_no"]}
        conv = os.path.join(OUT, "risk9", "전환신고서_문서명.csv")
        if os.path.exists(conv):
            for x in csv.DictReader(open(conv, encoding="utf-8-sig")):
                if x.get("report_nm"):
                    names[x["rcept_no"]] = x["report_nm"]
        out["doc_name"] = names.get(rc, "")
        ix = os.path.join(OUT, "doc", rc, "_파일목록.json")
        if os.path.exists(ix):
            rec = next((f for f in json.load(open(ix, encoding="utf-8")).get("files", [])
                        if f.get("파일종류") == "본문PDF"), {})
            out["collected_at"] = rec.get("fetched_at", "")
        else:                               # 2차 수집 본문(handoff/원본_주요신고서본문.zip) — zip 안 파일 시각
            with zipfile.ZipFile(os.path.join(HANDOFF, "원본_주요신고서본문.zip")) as z:
                t = z.getinfo("doc/%s/본문.pdf" % rc).date_time
            out["collected_at"] = "%04d-%02d-%02dT%02d:%02d:%02d (원본_주요신고서본문.zip 안 파일 시각, 2차 수집)" % t
    return out


ROW_MD_DIR = os.path.join(HANDOFF, "원문_지주리스크체계_원문")


def _row_md(row, d, meta, pages_cited):
    """행마다 인용한 쪽의 전문(텍스트 파일 그대로)을 .md 로. 인용 대조용 원문 텍스트."""
    os.makedirs(ROW_MD_DIR, exist_ok=True)
    P = dict(re_split_pages(open(d["텍스트"], encoding="utf-8").read()))
    lines = ["# %s · %s · %s" % (row["corp_label"], row["doc_kind"], meta["doc_name"]), "",
             "- doc_id: %s" % row["doc_id"],
             "- 출처: %s" % meta["rcept_no_or_url"],
             "- 수집일: %s" % meta["collected_at"],
             "- 원본 sha256: %s · 텍스트 sha256: %s" % (d["원본sha256"], d["텍스트sha256"]),
             "- 아래는 이 행에서 인용한 쪽의 추출 텍스트 전문이다(pypdf, 글자 수정 없음).", ""]
    for n in sorted(pages_cited):
        lines += ["## p.%d" % n, "", "```text", P.get(n, "(쪽 없음)").rstrip("\n"), "```", ""]
    p = os.path.join(ROW_MD_DIR, row["doc_id"] + ".md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return p


def emit():
    sel = json.load(open(SELECTION, encoding="utf-8"))
    idx = {r["doc_id"]: r for r in csv.DictReader(open(os.path.join(WORK, "텍스트목록.csv"),
                                                          encoding="utf-8-sig"))}
    log = list(csv.DictReader(open(os.path.join(WORK, "검색기록.csv"), encoding="utf-8-sig")))
    rnm = {r["rcept_no"]: r["report_nm"] for r in csv.DictReader(
        open(os.path.join(WORK, "DART_문서목록.csv"), encoding="utf-8-sig")) if r["rcept_no"]}
    texts = {}

    def nows_text(doc_id):
        if doc_id not in texts:
            texts[doc_id] = _nows(open(idx[doc_id]["텍스트"], encoding="utf-8").read()) \
                if idx.get(doc_id, {}).get("상태") == "추출" else None
        return texts[doc_id]

    wide, long_ = [], []
    order = {lab: i for i, lab in enumerate(LABELS)}
    kinds = {"연차보고서": 0, "사업보고서": 1, "경영공시": 2, "증권신고서": 3}
    rows = sorted(sel["rows"], key=lambda r: (kinds[r["doc_kind"]], order[r["corp_label"]], r["doc_id"]))
    for row in rows:
        d = idx[row["doc_id"]]
        fy = ROW_FY.get(row["doc_kind"]) or CONVERSION_ROWS[row["doc_id"]][0]
        meta = _source_meta(d)
        src = dict(rcept_no_or_url=meta["rcept_no_or_url"], doc_name=meta["doc_name"],
                   collected_at=meta["collected_at"], source_file=d["원본"],
                   source_sha256=d["원본sha256"], text_sha256=d["텍스트sha256"])
        # 정정·추가공시 대조: 인용 문구가 그 본에도 (공백 무시) 그대로 있는가
        amends = _amendments(row["doc_id"], idx)
        allq = [(f, q) for f, qs in list(row["fields"].items()) + list((row.get("extra") or {}).items())
                for q in qs]
        amend_notes = []
        for a in amends:
            name = a.split("__")[-1] + (" " + rnm[a.split("__")[-1]] if a.split("__")[-1] in rnm else "")
            t = nows_text(a)
            if t is None:
                amend_notes.append("%s: 텍스트 없음(%s)" % (name, idx.get(a, {}).get("상태", "목록 없음")))
                continue
            sec = next((x["section"] for x in log if x["doc_id"] == a), "")
            if sec.startswith("절 못 찾음"):
                amend_notes.append("%s: 이 본에는 위험관리 절이 없어 대조 불가(%s)" % (name, sec))
                continue
            diff = ["%s p.%d" % (f, int(q["page"])) for f, q in allq if _nows(q["quote"]) not in t]
            amend_notes.append("%s: 인용 %d개 중 %d개 같은 문구 있음%s"
                               % (name, len(allq), len(allq) - len(diff),
                                  " (이 본에 없는 문구: %s)" % ", ".join(diff) if diff else ""))
        out = dict(corp_label=row["corp_label"], fy=fy, doc_kind=row["doc_kind"],
                   section_title=row["section_title"])
        src_text, pages = [], set()
        for f in MAIN_FIELDS:
            qs = row["fields"].get(f, [])
            if qs:
                out[f] = SEP.join("[p.%d] %s" % (int(q["page"]), q["quote"]) for q in qs)
            else:
                out[f] = NOT_FOUND
        for f, qs in list(row["fields"].items()) + list((row.get("extra") or {}).items()):
            for q in qs:
                src_text.append("[%s p.%d] %s" % (f, int(q["page"]), q["quote"]))
                pages.add(int(q["page"]))
                long_.append(dict(corp_label=row["corp_label"], fy=fy, doc_kind=row["doc_kind"],
                                  doc_id=row["doc_id"], section_title=row["section_title"], field=f,
                                  page=int(q["page"]), quote=q["quote"], 검색="", **src))
        # 「문서에 없음」 칸의 검색 근거 — 어느 범위를 어떤 어휘로 찾았고 몇 건이었는가
        for f in MAIN_FIELDS + (["internal_control", "holding_plan"] if row["doc_kind"] == "증권신고서" else []):
            has = row["fields"].get(f) if f in MAIN_FIELDS else (row.get("extra") or {}).get(f)
            if has:
                continue
            lg = [x for x in log if x["doc_id"] == row["doc_id"] and x["field"] == f]
            how = ("범위 %s p.%s · 정규식 %s · 후보 %s건 — 읽고 해당 서술 없음으로 판단"
                   % (lg[0]["section"], lg[0]["pages"], lg[0]["regex"], lg[0]["hits"])) if lg else "검색기록 없음"
            long_.append(dict(corp_label=row["corp_label"], fy=fy, doc_kind=row["doc_kind"],
                              doc_id=row["doc_id"], section_title=row["section_title"], field=f,
                              page="", quote=NOT_FOUND, 검색=how, **src))
        out["source_text"] = SEP.join(src_text) if src_text else NOT_FOUND
        out["page"] = ", ".join(str(p) for p in sorted(pages))
        note = row.get("note", "").strip()
        if amend_notes:
            note = (note + " / " if note else "") + "다른 본 대조(판정 없음): " + "; ".join(amend_notes)
        out["note"] = note
        out.update(doc_id=row["doc_id"], **src)
        out["원문_md"] = _row_md(row, d, meta, pages)
        wide.append(out)
    cols = (["corp_label", "fy", "doc_kind", "section_title"] + MAIN_FIELDS +
            ["source_text", "rcept_no_or_url", "doc_name", "page", "note", "collected_at",
             "doc_id", "원문_md", "source_file", "source_sha256", "text_sha256"])
    _w(os.path.join(HANDOFF, "원문_지주리스크체계.csv"), wide, cols)
    _w(os.path.join(HANDOFF, "원문_지주리스크체계_근거.csv"), long_,
       ["corp_label", "fy", "doc_kind", "doc_id", "section_title", "field", "page", "quote", "검색",
        "rcept_no_or_url", "doc_name", "collected_at", "source_file", "source_sha256", "text_sha256"])
    nq = sum(1 for r in long_ if r["quote"] != NOT_FOUND)
    print("원문_지주리스크체계.csv %d행 · 근거 %d행(인용 %d · 문서에 없음 %d)"
          % (len(wide), len(long_), nq, len(long_) - nq))
    return wide, long_


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "emit":
        emit()
        return 0
    if cmd == "candidates":
        candidates()
        return 0
    if cmd == "extract":
        extract()
        return 0
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
