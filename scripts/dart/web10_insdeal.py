# -*- coding: utf-8 -*-
"""10차 6-6(나) — 금융지주 소속 보험 자회사의 「대주주와의 거래」 공시(보험업법 §111③④) 중 거래 상대방이 지주 또는
지주의 다른 자회사인 건.

    python3 scripts/dart/web10_insdeal.py robots     # 호스트별 robots.txt → dart_out/risk10/보험자회사_robots.csv
    python3 scripts/dart/web10_insdeal.py explore    # (점검) 첫 화면·사이트맵에서 공시실 링크 찾기
    python3 scripts/dart/web10_insdeal.py collect    # 목록·원문 PDF → handoff/원문_10차/보험자회사_대주주거래공시.csv
    python3 scripts/dart/web10_insdeal.py collect --offline   # 받지 않고 저장된 원본만으로 CSV

대상: 메리츠화재, KB손해보험, KB라이프, 신한라이프, 하나생명.
출처 후보: 각 사 누리집 공시실, 생명보험협회 공시실(pub.insure.or.kr). 손해보험협회(knia.or.kr 와 하위 도메인)는
다른 에이전트가 쓰고 있어 요청하지 않는다(행 note 에 「다른 작업이 맡음 — 이번에 미확인」).
규율(COMMON.md): web10.Web(UA 고정·1.2초 간격·3회 재시도)만 쓴다. 호스트마다 web10.Robots 로 확인하고 막힌 URL 은
요청하지 않는다. 로그인·캡차·차단 화면이 나오면 우회하지 않고 멈춘다.

게시처(2026-10-01 실측, 누리집 화면 그대로):
  · KB라이프 — www.kblife.co.kr 공시실 > 경영공시실(/customer-common/managementPublicNoticeOffice.do) > 수시공시 >
      KB라이프생명 탭. 목록은 화면 JS(managementPublicNoticeOffice.js doSearch_tab2)와 같은 POST JSON
      /customer-common/API/CUCO30390.do {pageSize:10, paGroupCnt:5, pageIndex:n, corpTpCd:"3", tabIdx:"tab2_1"}.
      원문 = /api/archive/archives/download/<UPFILE>/<SEQNO>/0 (화면의 data-file 그대로, GET, PDF).
  · KB손해보험 — www.kbinsure.co.kr 공시실 > 경영ㆍ사외이사공시 > 수시공시/공고(/CG801020001.ec). 연도 선택은 화면
      goSearchA() 와 같은 POST(selectSeqA=연도). 원문 = /CG801020002.ec?seq=N (GET, PDF).
고르는 공시(9차 C30 과 같은 기간): 목록 제목·구분에 '대주주' 가 있거나 구분이 「의결권행사」·「채권,주식 취득」인 것 중
  분기공시(제7-2-1호·제7-2-2호 = 제목에 '분기'·'현황')는 공시일 2025-10-01 이후, 그 밖(수시)은 2025-07-01 이후.
PDF 는 9차 web9_c30 의 표 읽기(parse_doc: clip 사각형으로 칸 묶기, 글자 그대로)를 고치지 않고 가져다 쓴다
  (그 모듈의 save·TASK 만 이 작업 폴더로 바꿔 쪽 텍스트 .pages.txt 를 dart_out/raw/web10/insdeal/ 에 둔다).
거래 상대방 판정(추정 없음): handoff/12_지분관계.csv 의 지주 타법인출자현황(DART, 가장 최근 보고서) 자회사 이름과
  공백·(주)·주식회사·(비상장)을 뗀 이름이 같으면 「지주의 자회사」, 지주 이름(KB금융지주 등)과 같으면 「지주」.
  그 밖의 상대방(펀드·조합·손자회사 등)은 handoff CSV 에 넣지 않고 작업 기록 CSV(전체 행)에만 둔다.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))

from web10 import Web, Robots, save, now, write_csv, OUT, WORK, RAW   # noqa: E402

TASK = "insdeal"
DIR = os.path.join(RAW, TASK)
NONE = "문서에 없음"
FROM_SUSI = date(2025, 7, 1)
FROM_QTR = date(2025, 10, 1)
OUT_CSV = os.path.join(OUT, "보험자회사_대주주거래공시.csv")
ALL_CSV = os.path.join(WORK, "보험자회사_대주주거래_전체행.csv")
COLS = ["corp_label", "공시일", "거래 상대방", "거래 유형", "금액", "이사회 의결일", "url", "source_text", "doc_name",
        "page", "collected_at", "note"]
HOSTS = [
    ("메리츠화재", "https://www.meritzfire.com"),
    ("KB손해보험", "https://www.kbinsure.co.kr"),
    ("KB라이프", "https://www.kblife.co.kr"),
    ("신한라이프", "https://www.shinhanlife.co.kr"),
    ("하나생명", "https://www.hanalife.co.kr"),
    ("생명보험협회 공시실", "https://pub.insure.or.kr"),
]
KBL = "https://www.kblife.co.kr"
KBL_PAGE = KBL + "/customer-common/managementPublicNoticeOffice.do"
KBL_API = KBL + "/customer-common/API/CUCO30390.do"
KBL_MENU = "KB라이프생명 누리집 > 공시실 > 경영공시실 > 수시공시 > KB라이프생명 탭"
KBI = "https://www.kbinsure.co.kr"
KBI_LIST = KBI + "/CG801020001.ec"
KBI_MENU = "KB손해보험 누리집 > 공시실 > 경영ㆍ사외이사공시 > 수시공시/공고"
HOLD = {"KB라이프": "KB금융", "KB손해보험": "KB금융", "신한라이프": "신한지주", "메리츠화재": "메리츠금융지주",
        "하나생명": "하나금융지주"}
HOLD_NAMES = {"KB금융": ["KB금융지주", "케이비금융지주"], "신한지주": ["신한금융지주", "신한금융지주회사"],
              "메리츠금융지주": ["메리츠금융지주"], "하나금융지주": ["하나금융지주"]}
BLOCK_WORDS = ("captcha", "CAPTCHA", "자동입력", "보안문자", "로그인이 필요", "로그인 후 이용", "Access Denied",
               "Block URL List", "보안정책")
OFFLINE = "--offline" in sys.argv


class Stop(Exception):
    pass


def _robots_for(w, base):
    return Robots(w, base, TASK)


def get(w, rob, url, name, referer="", data=None, headers=None, extra=None):
    """robots 허용 URL 만 받아 save. HTML 응답이 로그인·캡차·차단 화면이면 멈춘다."""
    if not rob.allowed(url):
        raise Stop("robots.txt 가 막음 — 요청 안 함: %s" % url)
    fu, st, hd, b = w.get(url, referer=referer, data=data, headers=headers)
    meta = dict(출처URL=url, method="POST" if data is not None else "GET", 최종URL=fu, http_status=st,
                content_type=hd.get("Content-Type", ""), content_disposition=hd.get("Content-Disposition", ""),
                fetched_at=now())
    if data is not None:
        meta["요청본문"] = dict(data) if not isinstance(data, bytes) else data.decode("utf-8", "replace")
    meta.update(extra or {})
    p, meta = save(TASK, name, b, meta)
    if "html" in (hd.get("Content-Type", "") or "").lower():   # JS·JSON·PDF 안의 안내 문구는 차단 화면이 아님
        low = b[:30000].decode("utf-8", "replace")
        for wd in BLOCK_WORDS:
            if wd in low:
                raise Stop("차단/로그인/캡차 신호 %r — %s (%s)" % (wd, url, p))
    return fu, st, hd, b, p, meta


def cached_or_get(w, rob, url, name, **k):
    p = os.path.join(DIR, name)
    if os.path.exists(p) and os.path.exists(p + ".meta.json"):
        with open(p, "rb") as f, open(p + ".meta.json", encoding="utf-8") as g:
            return f.read(), json.load(g), p
    if OFFLINE:
        raise Stop("--offline: 저장된 원본 없음 — %s" % name)
    fu, st, hd, b, p, meta = get(w, rob, url, name, **k)
    return b, meta, p


def robots():
    w = Web()
    rows = []
    for label, base in HOSTS:
        r = Robots(w, base, TASK)
        host = base.split("//")[1]
        p = os.path.join(RAW, TASK, "robots_%s.txt" % host)
        txt = open(p, encoding="utf-8", errors="replace").read() if r.status == "OK" and os.path.exists(p) else ""
        rows.append(dict(label=label, host=host, status=r.status, note=r.note,
                         root_allowed=r.allowed(base + "/"), robots_text=" ".join(txt.split())[:1500],
                         checked_at=now()))
        print(label, host, r.status, r.allowed(base + "/"), " ".join(txt.split())[:300], flush=True)
    write_csv(os.path.join(WORK, "보험자회사_robots.csv"), list(rows[0].keys()), rows)


def explore():
    """첫 화면·사이트맵에서 공시실 링크를 찾는다(받은 화면은 원본 저장)."""
    w = Web()
    targets = [("KB라이프", KBL, ["/sitemap/sitemap.xml"]), ("KB손해보험", KBI, ["/"]),
               ("메리츠화재", "https://www.meritzfire.com", ["/"])]
    for label, base, paths in targets:
        rob = _robots_for(w, base)
        for pth in paths:
            url = base + pth
            try:
                fu, st, hd, b, p, meta = get(w, rob, url, "%s_%s" % (label, re.sub(r"[^\w.]+", "_", pth).strip("_")
                                                                     or "home"))
            except Exception as e:                          # noqa: BLE001
                print(label, url, "실패", repr(e)[:200], flush=True)
                continue
            print(label, url, st, len(b), fu, flush=True)


# ── 판정 도구 ───────────────────────────────────────────────────────────────
def norm(s):
    s = re.sub(r"\(비상장\)|\(상장\)|\(주\)|㈜|주식회사|\s+", "", s or "")
    return s.replace("케이비", "KB")


_GL = {}


def group_list(hold):
    if hold not in _GL:
        _GL[hold] = _group_list(hold)
    return _GL[hold]


def _group_list(hold):
    """handoff/12_지분관계.csv — 지주의 가장 최근 보고서 타법인출자 목록. (자회사 이름들, 출처 설명)"""
    p = os.path.join("handoff", "12_지분관계.csv")
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8-sig")) if r["parent_label"] == hold]
    if not rows:
        return [], "handoff/12_지분관계.csv 에 %s 행 없음" % hold
    key = max((r["bsns_year"], r["reprt_code"]) for r in rows)
    rs = [r for r in rows if (r["bsns_year"], r["reprt_code"]) == key and r["child_name"].strip() != "합계"]
    names = [re.sub(r"\s+", "", r["child_name"]) for r in rs]
    return names, "handoff/12_지분관계.csv %s %s %s(rcept_no %s) 지주 타법인출자현황 %d곳" % (
        hold, key[0], {"11011": "사업보고서", "11012": "반기보고서", "11013": "1분기", "11014": "3분기"}
        .get(key[1], key[1]), rs[0]["rcept_no"], len(names))


def classify(cp, corp):
    """('지주'|'지주의 자회사'|'', 근거). 이름 일치만."""
    hold = HOLD.get(corp, "")
    subs, src = group_list(hold)
    out = []
    for part in re.split(r"\s*[,/·]\s*|\s+및\s+", cp or ""):
        n = norm(part)
        if not n or n in ("-", NONE):
            continue
        if any(n == norm(h) for h in HOLD_NAMES.get(hold, [])):
            out.append(("지주", "「%s」= 지주 이름" % part))
            continue
        hit = [s for s in subs if norm(s) == n or ("KB" + norm(s)) == n or norm(s) == "KB" + n]
        if hit and norm(hit[0]) != norm(corp_name(corp)):
            out.append(("지주의 자회사", "「%s」= %s 의 「%s」" % (part, src, hit[0])))
    kinds = list(dict.fromkeys(k for k, _ in out))
    return "·".join(kinds), "; ".join(x for _, x in out)


def corp_name(corp):
    return {"KB라이프": "KB라이프생명", "KB손해보험": "KB손해보험", "신한라이프": "신한라이프생명보험"}.get(corp, corp)


def ymd(s):
    m = re.search(r"(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})", s or "")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def is_qtr(title):
    return "분기" in title or "현황" in title


def wanted(title, d):
    if not d:
        return False
    return d >= (FROM_QTR if is_qtr(title) else FROM_SUSI)


# ── KB라이프 ───────────────────────────────────────────────────────────────
def kblife_list(w, rob):
    items = []
    if not OFFLINE:
        get(w, rob, KBL_PAGE, "KB라이프_경영공시실.html")                    # 세션·Referer 를 화면과 같게
    for pg in range(1, 40):
        data = {"pageSize": 10, "paGroupCnt": 5, "pageIndex": str(pg), "corpTpCd": "3", "tabIdx": "tab2_1"}
        b, meta, p = cached_or_get(
            w, rob, KBL_API, "KB라이프_수시공시_p%02d.json" % pg, referer=KBL_PAGE,
            data=json.dumps(data).encode(), headers={"Content-Type": "application/json; charset=UTF-8",
                                                     "X-Requested-With": "XMLHttpRequest",
                                                     "Accept": "application/json, text/javascript, */*; q=0.01"},
            extra=dict(메뉴=KBL_MENU, 쪽=pg))
        j = json.loads(b.decode("utf-8"))
        lst = j.get("list") or []
        for r in lst:
            items.append(dict(title=r.get("SUBJECT", ""), date_txt=r.get("VIEW_DATE", ""), d=ymd(r.get("VIEW_DATE")),
                              url="%s/api/archive/archives/download/%s/%s/0" % (KBL, r.get("UPFILE"), r.get("SEQNO")),
                              key="SEQNO%s" % r.get("SEQNO"), cat="", page=pg))
        if not lst or all(ymd(r.get("VIEW_DATE")) and ymd(r.get("VIEW_DATE")) < FROM_SUSI for r in lst):
            break
    return items, "%s — 목록 %d쪽(%d건) 받음, 공시일 %s 이후 수시·%s 이후 분기공시 중 제목에 '대주주'" % (
        KBL_MENU, pg, len(items), FROM_SUSI, FROM_QTR)


# ── KB손해보험 ─────────────────────────────────────────────────────────────
def kbins_list(w, rob):
    items = []
    for yr in ("2026", "2025"):
        b, meta, p = cached_or_get(w, rob, KBI_LIST, "KB손해보험_수시공시_%s.html" % yr,
                                   referer=KBI + "/CG801010001.ec?mdmn=0301",
                                   data={"selectSeqA": yr}, extra=dict(메뉴=KBI_MENU, 연도=yr))
        t = b.decode("euc-kr", "replace")
        i = t.find("<table")
        j = t.find("</table>", i)
        cat = ""
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t[i:j], re.S)[1:]:
            th = re.findall(r"<th[^>]*>(.*?)</th>", tr, re.S)
            if th:
                cat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", th[0])).strip()
            tds = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()
                   for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            href = re.findall(r'href="(/CG801020002\.ec\?seq=\d+)"', tr)
            if len(tds) < 3 or not href:
                continue
            items.append(dict(title=tds[0], cat=cat, occ=tds[1], date_txt=tds[2], d=ymd(tds[2]),
                              url=KBI + href[0], key="seq%s" % href[0].split("=")[1], page=yr))
    uniq = {}
    for it in items:
        uniq.setdefault(it["key"], it)
    items = list(uniq.values())
    return items, "%s — 2026·2025년 목록(연도 선택 POST) %d건, 등록일 %s 이후 수시·%s 이후 분기 중 구분이 " \
                  "「대주주등에 대한 신용공여 등」·「의결권행사」·「채권,주식 취득」" % (KBI_MENU, len(items), FROM_SUSI,
                                                                       FROM_QTR)


# ── PDF ───────────────────────────────────────────────────────────────────
def c30():
    import web9_c30 as C
    C.save, C.TASK = save, TASK                   # 쪽 텍스트(.pages.txt)를 이 작업 폴더에(9차 폴더는 건드리지 않음)
    return C


def cd_name(hd_cd):
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', hd_cd or "")
    if not m:
        return ""
    s = m.group(1)
    try:
        s = s.encode("latin-1").decode("utf-8")
    except Exception:                                # noqa: BLE001
        pass
    import urllib.parse
    return urllib.parse.unquote(s)


def collect():
    w = Web()
    C = c30()
    all_rows, out, cover = [], [], []
    for corp, base in HOSTS:
        if corp == "생명보험협회 공시실":
            continue
        rob = None
        if not OFFLINE:
            rob = _robots_for(w, base)
            if not rob.allowed(base + "/"):
                why = rob.note or "robots.txt 가 / 를 막음"
                cover.append((corp, why))
                continue
        else:
            rob = type("R", (), {"allowed": lambda self, u: True})()
        try:
            if corp == "KB라이프":
                items, scope = kblife_list(w, rob)
                pick = [it for it in items if "대주주" in it["title"] and wanted(it["title"], it["d"])]
            elif corp == "KB손해보험":
                items, scope = kbins_list(w, rob)
                pick = [it for it in items if ("대주주" in it["cat"] or it["cat"] in ("의결권행사", "채권,주식 취득"))
                        and wanted(it["cat"] + it["title"], it["d"])]
            else:
                cover.append((corp, None))
                continue
        except Stop as e:
            cover.append((corp, "멈춤: %s" % e))
            continue
        cover.append((corp, "OK"))
        print(corp, scope, "→ 고른 공시 %d건" % len(pick), flush=True)
        for it in sorted(pick, key=lambda x: (x["d"], x["key"])):
            name = "%s_%s.pdf" % (corp, it["key"])
            ref = KBL_PAGE if corp == "KB라이프" else KBI_LIST
            try:
                b, meta, p = cached_or_get(w, rob, it["url"], name, referer=ref,
                                           extra=dict(목록제목=it["title"], 목록구분=it.get("cat", ""),
                                                      목록공시일=it["date_txt"], 메뉴=scope.split(" — ")[0]))
            except Exception as e:                       # noqa: BLE001
                all_rows.append(dict(corp_label=corp, 공시일=it["date_txt"], url=it["url"], note="원문 받기 실패 %r" % e))
                continue
            if not b.startswith(b"%PDF"):
                all_rows.append(dict(corp_label=corp, 공시일=it["date_txt"], url=it["url"],
                                     note="PDF 아님(%d바이트, %s)" % (len(b), meta.get("content_type"))))
                continue
            fname = cd_name(meta.get("content_disposition", "")) or it["title"]
            try:
                rows, code, title, npg = C.parse_doc(p)
            except Exception as e:                       # noqa: BLE001
                rows, code, title, npg = [dict(fy=NONE, counterparty=NONE, deal_type=NONE, amount=NONE,
                                               board_approval=NONE, source_text=NONE, page="",
                                               note_extra="PDF 읽기 실패 %r" % e)], "", "", 0
            for r in rows:
                kind, why = classify(r["counterparty"], corp)
                note = ["목록 「%s%s」 공시일 %s%s" % (("[%s] " % it["cat"]) if it.get("cat") else "", it["title"],
                                                  it["date_txt"], (" 발생일 %s" % it["occ"]) if it.get("occ") else ""),
                        "문서 일자: %s" % r["fy"], "서식 %s" % (code or "번호 없음"), "PDF %d쪽" % npg,
                        "원본 %s (sha256 %s…, 쪽 텍스트 %s.pages.txt)" % (p, meta.get("sha256", "")[:12], p),
                        "출처 화면·기간: " + scope]
                if r.get("note_extra"):
                    note.insert(2, r["note_extra"])
                note.insert(0, ("거래 상대방 판정: %s — %s" % (kind, why)) if kind else
                            "거래 상대방 판정: 지주·지주 자회사 목록과 이름 불일치(%s)" % group_list(HOLD[corp])[1])
                all_rows.append(dict(corp_label=corp, 공시일=it["date_txt"], **{
                    "거래 상대방": r["counterparty"], "거래 유형": r["deal_type"], "금액": r["amount"],
                    "이사회 의결일": r["board_approval"]}, url=it["url"], source_text=r["source_text"],
                    doc_name=fname, page=r["page"], collected_at=meta.get("fetched_at", ""), note=" / ".join(note),
                    판정=kind))
    for corp, why in cover:
        if why == "OK":
            n = sum(1 for r in all_rows if r["corp_label"] == corp and r.get("판정"))
            if n == 0:
                out.append(none_row(corp, "고른 기간 공시에서 거래 상대방이 지주·지주 자회사(이름 일치)인 행 없음"))
            continue
        if why is None:
            why = {"메리츠화재": "누리집 첫 화면이 JS(/common/index.js)로만 그려져 공시실 목록 주소를 화면 원본에서 "
                                 "확인하지 못함 — 미확인(시간)",
                   "신한라이프": "robots.txt 확인 실패(응답 시간 초과) — RFC 9309 에 따라 받지 않음",
                   "하나생명": "robots.txt 요청이 /index.html 로 넘어가 「시스템 점검」 화면(시스템 개선작업 중) — 공시실 "
                               "받지 않음"}.get(corp, "")
        out.append(none_row(corp, why))
    out += [{k: r.get(k, "") for k in COLS} for r in all_rows if r.get("판정")]
    out.append(none_row("(손해보험협회 공시실)", "다른 작업이 맡음 — 이번에 미확인(knia.or.kr 요청 안 함)"))
    out.append(none_row("(생명보험협회 공시실)", "robots.txt(pub.insure.or.kr) 가 User-agent:* Disallow:/ — 요청 안 함"
                                           "(robots.txt 만 받음)"))
    write_csv(OUT_CSV, COLS, out)
    write_csv(ALL_CSV, COLS + ["판정"], [{k: r.get(k, "") for k in COLS + ["판정"]} for r in all_rows])
    print("handoff %d행 → %s · 전체 %d행 → %s" % (len(out), OUT_CSV, len(all_rows), ALL_CSV))


def none_row(corp, why):
    return dict(corp_label=corp, 공시일=NONE, **{"거래 상대방": NONE, "거래 유형": NONE, "금액": NONE,
                                                 "이사회 의결일": NONE}, url="", source_text=NONE, doc_name=NONE,
                page="", collected_at=now(), note=why)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"robots": robots, "explore": explore, "collect": collect}.get(cmd, lambda: print(__doc__))()
