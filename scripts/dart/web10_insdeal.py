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
PDF 는 pypdf layout 모드로 글자를 위치대로 뽑는다(아래 LAYOUT_NOTE) — 9차 web9_c30 의 clip 칸 묶기는 이 두 회사
  PDF 에 칸 clip 이 없어 듣지 않았다(1차 실행에서 확인). 쪽 글은 <원본>.layout.txt.
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
SITE_OF = dict(HOSTS)                   # 회사 → 누리집 주소(「문서에 없음」 행의 출처)
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
TERMS_NOTE = {   # `terms` 결과(dart_out/risk10/보험자회사_약관.csv) — 자동 수집 금지 문구 없음, 재배포 제한 문구는 있음
    "KB라이프": "이용약관(/customer-center/termsOfUse.do): 자동 수집 금지 문구 없음 · 제11조 2) 「사전 승낙 없이 … 영리목적으로 "
               "이용하거나 제3자에게 이용하게 하여서는 안됩니다」(재배포 때 유의)",
    "KB손해보험": "이용약관(CU106000001.ec): 자동 수집 금지 문구 없음 · 제13조 ② 「사전 승낙없이 … 영리목적으로 이용하거나 "
                "제3자에게 이용하게 하여서는 안됩니다」(재배포 때 유의)",
}


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
        subs2 = [s for s in subs if norm(s) != norm(corp_name(corp))]          # 공시한 회사 자신은 뺌
        hit = [s for s in subs2 if norm(s) == n or ("KB" + norm(s)) == n or norm(s) == "KB" + n]
        if hit:
            out.append(("지주의 자회사", "「%s」= %s 의 「%s」" % (part, src, hit[0])))
            continue
        pre = [s for s in subs2 if len(norm(s)) >= 3 and (n.startswith(norm(s)) or n.startswith("KB" + norm(s)))]
        if pre:
            out.append(("지주의 자회사(이름 앞부분 일치)",
                        "「%s」 앞부분 = %s 의 「%s」(채권 종목명 등 — 발행인 여부는 문서 표기만)" % (part, src, pre[0])))
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


# ── PDF (pypdf layout 모드) ────────────────────────────────────────────────
# 두 회사 PDF 는 칸마다 clip 사각형이 없어 9차 C30 의 칸 묶기가 듣지 않고, 기본 extract_text 는 칸 순서가 뒤섞인다
# (KB라이프 서식은 라벨·값이 따로 나옴). 그래서 pypdf extract_text(extraction_mode="layout") 로 글자를 화면 위치대로
# 줄 맞춰 뽑는다. 글자는 그대로이고, layout 모드가 위치를 맞추려 넣은 공백만 정리한다: 4칸 이상 공백 = 칸 경계(' | '),
# 2~3칸 공백 = 낱말 사이 한 칸. 줄은 그대로 줄바꿈. (원본 PDF·쪽별 layout 글은 dart_out/raw/web10/insdeal/)
LAYOUT_NOTE = ("pypdf %s extract_text(extraction_mode='layout') — 글자 그대로, 위치 맞춤 공백만 정리(4칸 이상=칸 경계 ' | ', "
               "2~3칸=한 칸)")


def cells_of(line):
    """[(시작 위치, 끝 위치, 글)] — 4칸 이상 공백으로 칸을 가르고, 칸 안 2~3칸 공백은 한 칸으로."""
    out = []
    for m in re.finditer(r"\S+(?: {1,3}\S+)*", line):
        out.append((m.start(), m.end(), re.sub(r" {2,3}", " ", m.group(0))))
    return out


def read_layout(path):
    import pypdf
    r = pypdf.PdfReader(path)
    pages = []
    for i, pg in enumerate(r.pages, 1):
        t = pg.extract_text(extraction_mode="layout") or ""
        lines = [ln.rstrip() for ln in t.split("\n") if ln.strip()]
        pages.append(dict(no=i, lines=lines))
    txt = "".join("=== p.%d ===\n%s\n" % (p["no"], "\n".join(p["lines"])) for p in pages)
    lp = path + ".layout.txt"
    if not os.path.exists(lp) or open(lp, encoding="utf-8").read() != txt:
        save(TASK, os.path.basename(lp), txt.encode("utf-8"),
             dict(원본=path, 만든방법=LAYOUT_NOTE % pypdf.__version__, fetched_at=now()))
    return pages, LAYOUT_NOTE % pypdf.__version__


def body_lines(pages):
    """서식 본문 줄(기재상 주의 앞까지) — (쪽, 칸 목록, 원 줄)."""
    out = []
    for p in pages:
        for ln in p["lines"]:
            if re.match(r"\s*<\s*기재\s*상", ln):
                break
            out.append((p["no"], cells_of(ln), ln))
    return out


def src_text(bl):
    return "\n".join(" | ".join(c[2] for c in cs) for _, cs, _ in bl if cs)


def form_code(bl):
    for _, cs, _ in bl:
        for c in cs:
            m = re.search(r"\(\s*(제\s*7\s*-\s*\d\s*-\s*\d\s*호)\s*\)", c[2])
            if m:
                return re.sub(r"\s+", "", m.group(1))
    return ""


def doc_title(bl):
    """서식 제목 줄(‘대주주’가 든 첫 줄, 라벨·법 조문 줄 제외) — 줄의 칸을 한 칸 띄어 잇는다."""
    for _, cs, _ in bl:
        t = " ".join(c[2] for c in cs)
        if "대주주" in t and not re.match(r"\s*\d\.", t) and "보험업법" not in t \
                and "대주주명" not in t.replace(" ", ""):
            return t
    return ""


def value_after(bl, pat):
    """라벨 칸(pat) 오른쪽 칸들의 글. 같은 줄에 값이 없으면 다음 줄의 마지막 칸. (값, 쪽)"""
    for k, (pg, cs, _) in enumerate(bl):
        for i, c in enumerate(cs):
            if re.search(pat, c[2].replace(" ", "")):
                rest = [x[2] for x in cs[i + 1:]]
                if rest:
                    return " ".join(rest), pg
                if k + 1 < len(bl) and bl[k + 1][1]:
                    return bl[k + 1][1][-1][2], pg
                return "", pg
    return "", ""


def susi_rows(bl, code, title):
    name, pg = "", ""
    for k, (p, cs, _) in enumerate(bl):
        idx = [i for i, c in enumerate(cs) if re.fullmatch(r"(1\.)?대주주명", c[2].replace(" ", ""))]
        if idx:
            name, pg = " ".join(c[2] for c in cs[idx[0] + 1:]), p
            for p2, cs2, _ in bl[k + 1:]:                          # 다음 줄로 넘친 이름(칸 하나뿐인 줄)
                if len(cs2) == 1 and not re.match(r"\d\.", cs2[0][2]):
                    name = (name + " " + cs2[0][2]).strip()
                    continue
                break
            break
    bod, _ = value_after(bl, r"이사회(결의|의결)일")
    kind, _ = value_after(bl, r"(주식의종류|채권의종류|신용공여종류)$")
    amt_lab = next((lab for lab in ("취득금액(원)", "신용공여금액", "거래금액")
                    if value_after(bl, re.escape(lab.replace(" ", "")))[0]), "")
    amt = value_after(bl, re.escape(amt_lab))[0] if amt_lab else ""
    day_lab = next((lab for lab in ("취득일", "신용공여일", "거래일", "주주총회일", "(의결권행사일)")
                    if value_after(bl, "^" + re.escape(lab) + "$")[0]), "")
    day = value_after(bl, "^" + re.escape(day_lab) + "$")[0] if day_lab else ""
    return [dict(fy="%s %s" % (day_lab, day) if day else NONE, counterparty=name or NONE,
                 deal_type=(title or NONE) + (" / 종류: %s" % kind if kind else ""),
                 amount="%s: %s" % (amt_lab, amt) if amt else (NONE if code != "제7-1-4호" else "의결권 행사 서식 — 금액 칸 없음"),
                 board_approval=bod or NONE, source_text=src_text(bl) or NONE, page=str(pg or 1), note_extra="")]


def table_rows(pages, code, title):
    """분기공시 표(제7-2-1호·제7-2-2호): 대주주 행마다. 값 칸은 머리 칸(전분기말 등)에 위치(가운데)로 붙인다."""
    out, basis, unit = [], "", ""
    for p in pages:
        lines = p["lines"]
        for ln in lines:
            m = re.search(r"\(\s*(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?\s*기준)", ln)
            if m and not basis:
                basis = m.group(1)
            m = re.search(r"단위\s*:\s*([^)]+?)\s*\)", ln)
            if m and not unit:
                unit = re.sub(r"\s+", " ", m.group(1))
        hi = next((i for i, ln in enumerate(lines) if "전분기말" in ln), None)
        if hi is None:
            continue
        sub = cells_of(lines[hi])
        grp = cells_of(lines[hi - 1]) if hi > 0 else []
        name_col = next((c for c in grp if c[2].replace(" ", "") in ("대주주명", "대주주")), None)
        # 한글 머리 줄과 숫자 줄은 layout 글자 위치가 어긋나므로(한글 폭) 칸 위치는 숫자 줄끼리 맞춘다:
        # 값 칸이 가장 많은 줄(소계 줄 등)의 칸 오른쪽 끝 = 열 기준, 열 이름 = 머리 줄 칸을 왼쪽부터 순서대로.
        body = []
        for ln in lines[hi + 1:]:
            if re.search(r"총\s*계", ln) or re.match(r"\s*(\*|<|주\s*\d)", ln):
                break
            body.append(ln)
        subl = [c[2] for c in sub]
        groups = [c[2] for c in grp if c[2].replace(" ", "") not in ("계정구분", "대주주명", "대주주")]
        per = len(subl) // len(groups) if groups and len(subl) % len(groups) == 0 else 0
        labels = [("%s %s" % (groups[i // per], s)) if per else s for i, s in enumerate(subl)]
        # 값 칸 수가 머리 칸 수와 같은 행만 순서대로 머리 이름을 붙인다. 회계식 음수(「-   1,300」)·빈 칸 때문에 칸 수가
        # 다르면 어느 칸이 어느 열인지 글자 위치로는 확정할 수 없어(한글 머리와 숫자 줄의 layout 위치 어긋남) 행 원문 그대로.
        for ln in body:
            cs = [c for c in cells_of(ln) if c[2] not in ("일반계정", "특별계정")]
            if not cs or re.search(r"(소계|합계)$", cs[0][2].replace(" ", "")) or re.fullmatch(r"[\d,.\-\s]+", cs[0][2]):
                continue
            nm, vals = cs[0][2], [c[2] for c in cs[1:]]
            if labels and len(vals) == len(labels) and all(re.fullmatch(r"-|[\d,.]+", v) for v in vals):
                amount = "; ".join("%s: %s" % (lab, v) for lab, v in zip(labels, vals) if v != "-")
            else:
                amount = "표 행 원문(칸 배치 모호 — 값 칸 %d개 · 머리 칸 %d개): %s" % (len(vals), len(labels),
                                                                           " | ".join(vals))
            out.append(dict(fy=basis or NONE, counterparty=nm, deal_type=title or NONE,
                            amount=(amount + " (단위: %s — 문서 표기)" % unit) if amount and unit else (amount or NONE),
                            board_approval=NONE, source_text=re.sub(r" {4,}", " | ", ln.strip()), page=str(p["no"]),
                            note_extra="표 머리: %s / %s" % (" | ".join(c[2] for c in grp), " | ".join(c[2] for c in sub))))
    if not out:
        out.append(dict(fy=basis or NONE, counterparty=NONE, deal_type=title or NONE, amount=NONE, board_approval=NONE,
                        source_text=NONE, page="1", note_extra="표에 대주주 이름 행 없음(0 또는 빈 표)"))
    return out


def parse_doc(path):
    pages, how = read_layout(path)
    bl = body_lines(pages)
    code = form_code(bl)
    title = doc_title(bl)
    if not any(cs for _, cs, _ in bl if any(re.search(r"대주주\s*명|전분기말", c[2]) for c in cs)):
        rows = [dict(fy=NONE, counterparty=NONE, deal_type=title or NONE, amount=NONE, board_approval=NONE,
                     source_text=src_text(bl) or NONE, page="1",
                     note_extra="PDF 글자 층에 표 본문(대주주명·금액)이 없음 — 표가 그림·도형으로 그려진 듯(글자 추출 불가, "
                                "OCR 하지 않음)")]
    elif code in ("제7-2-1호", "제7-2-2호") or "분기" in title:
        rows = table_rows(pages, code, title)
    else:
        rows = susi_rows(bl, code, title)
    return rows, code, title, len(pages), how


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
        else:                                           # 받지 않음 — 마지막으로 저장된 robots.txt 로 판정
            import urllib.robotparser
            from web10 import UA
            rp_path = os.path.join(DIR, "robots_%s.txt" % base.split("//")[1])
            if not os.path.exists(rp_path):
                cover.append((corp, "robots.txt 확인 실패(저장본 없음 — 온라인 실행에서 받지 못함) — 수집 안 함"))
                continue
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(open(rp_path, encoding="utf-8", errors="replace").read().splitlines())
            if not rp.can_fetch(UA, base + "/"):
                cover.append((corp, "robots.txt(저장본)가 / 를 막음"))
                continue
            rob = type("R", (), {"allowed": lambda self, u, _rp=rp: _rp.can_fetch(UA, u)})()
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
            fname = cd_name(meta.get("content_disposition", "")) or it["title"]
            if not b.startswith(b"%PDF"):
                why = ("문서보안(DRM) 암호화 파일(파일 머리 %r) — 열거나 풀지 않음(우회 금지)" % b[:8].decode("latin-1")
                       if b.startswith(b"SCDSA") else "PDF 아님(%d바이트, %s)" % (len(b), meta.get("content_type")))
                all_rows.append(dict(corp_label=corp, 공시일=it["date_txt"], **{
                    "거래 상대방": NONE, "거래 유형": it["title"], "금액": NONE, "이사회 의결일": NONE}, url=it["url"],
                    source_text=NONE, doc_name=fname, page="", collected_at=meta.get("fetched_at", ""),
                    note="%s / 목록 「%s」 공시일 %s / 원본 %s (sha256 %s…) / 출처 화면·기간: %s"
                         % (why, it["title"], it["date_txt"], p, meta.get("sha256", "")[:12], scope),
                    판정="미확인(문서 읽기 불가)" if is_qtr(it["title"]) else ""))
                continue
            try:
                rows, code, title, npg, how = parse_doc(p)
            except Exception as e:                       # noqa: BLE001
                rows, code, title, npg, how = [dict(fy=NONE, counterparty=NONE, deal_type=NONE, amount=NONE,
                                                    board_approval=NONE, source_text=NONE, page="",
                                                    note_extra="PDF 읽기 실패 %r" % e)], "", "", 0, ""
            for r in rows:
                kind, why = classify(r["counterparty"], corp)
                unread = ("글자 추출 불가" in r.get("note_extra", "") or "읽기 실패" in r.get("note_extra", ""))
                if not kind and unread and (is_qtr(it["cat"] + it["title"]) or "읽기 실패" in r["note_extra"]):
                    kind, why = "미확인(문서 읽기 불가)", "거래 상대방을 문서에서 읽지 못함 — 지주·자회사 거래가 있는지 이 행으로는 모름"
                note = ["목록 「%s%s」 공시일 %s%s" % (("[%s] " % it["cat"]) if it.get("cat") else "", it["title"],
                                                  it["date_txt"], (" 발생일 %s" % it["occ"]) if it.get("occ") else ""),
                        "문서 일자: %s" % r["fy"], "서식 %s" % (code or "번호 없음"), "PDF %d쪽" % npg,
                        "원본 %s (sha256 %s…, 쪽 글 %s.layout.txt)" % (p, meta.get("sha256", "")[:12], p),
                        "텍스트화: " + how, "출처 화면·기간: " + scope, TERMS_NOTE.get(corp, "")]
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
                out.append(none_row(corp, "고른 기간 공시에서 거래 상대방이 지주·지주 자회사(이름 일치)인 행 없음",
                                    {"KB라이프": KBL_PAGE, "KB손해보험": KBI_LIST}.get(corp, SITE_OF.get(corp, ""))))
            continue
        if why is None:
            why = {"메리츠화재": "누리집 첫 화면이 JS(/common/index.js)로만 그려져 공시실 목록 주소를 화면 원본에서 "
                                 "확인하지 못함 — 미확인(시간)",
                   "신한라이프": "robots.txt 는 받았으나 공시실 목록 주소를 확인하지 않음 — 미확인(시간)",
                   "하나생명": hana_note()}.get(corp, "")
        out.append(none_row(corp, why, (SITE_OF[corp] + ("/" if corp == "메리츠화재" else "/robots.txt"))
                            if corp in SITE_OF else ""))
    out += [{k: r.get(k, "") for k in COLS} for r in all_rows if r.get("판정")]
    out.append(none_row("(손해보험협회 공시실)", "다른 작업이 맡음 — 이번에 미확인(knia.or.kr 요청 안 함)",
                        "https://kpub.knia.or.kr/ (요청 안 함)"))
    out.append(none_row("(생명보험협회 공시실)", "robots.txt(pub.insure.or.kr) 가 User-agent:* Disallow:/ — 요청 안 함"
                                           "(robots.txt 만 받음)", "https://pub.insure.or.kr/robots.txt"))
    write_csv(OUT_CSV, COLS, out)
    write_csv(ALL_CSV, COLS + ["판정"], [{k: r.get(k, "") for k in COLS + ["판정"]} for r in all_rows])
    print("handoff %d행 → %s · 전체 %d행 → %s" % (len(out), OUT_CSV, len(all_rows), ALL_CSV))


def hana_note():
    p = os.path.join(DIR, "robots_www.hanalife.co.kr.txt")
    t = open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
    if "시스템 점검" in t:
        m = json.load(open(p + ".meta.json", encoding="utf-8"))
        return ("robots.txt 요청이 %s 로 넘어가 「시스템 점검 | 하나생명」 화면(「시스템 개선작업 중입니다.」, %s) — 누리집 "
                "점검 중이라 공시실 받지 않음(robots 규칙 없음)" % (m.get("최종URL"), m.get("fetched_at")))
    return "공시실 목록 주소를 확인하지 않음 — 미확인(시간)"


def none_row(corp, why, url=""):
    """「문서에 없음」 행 — url 은 찾아본(또는 robots 로 막혀 요청하지 않은) 곳."""
    return dict(corp_label=corp, 공시일=NONE, **{"거래 상대방": NONE, "거래 유형": NONE, "금액": NONE,
                                                 "이사회 의결일": NONE}, url=url, source_text=NONE, doc_name=NONE,
                page="", collected_at=now(), note=why)


BAN = re.compile(r"(자동|프로그램|크롤|스크래|스크랩|로봇|봇|기계적|매크로).{0,60}(수집|복제|추출|접근|이용)|"
                 r"(수집|복제|추출).{0,60}(자동|프로그램|크롤|스크래|스크랩|로봇|기계적|매크로)")


def terms():
    """수집한 두 누리집의 이용약관 화면 — 자동 수집 금지 문구(이메일 주소 수집 금지는 해당 아님)."""
    w = Web()
    rows = []
    for corp, base, path, enc in [("KB라이프", KBL, "/customer-center/termsOfUse.do", "utf-8"),
                                  ("KB손해보험", KBI, "/CU106000001.ec?mdmn=0301", "euc-kr")]:
        rob = _robots_for(w, base)
        url = base + path
        try:
            fu, st, hd, b, p, meta = get(w, rob, url, "%s_이용약관.html" % corp)
        except Exception as e:                           # noqa: BLE001
            rows.append(dict(corp=corp, url=url, status="실패 %r" % e, 자동수집금지_문구="", 관련문장="", 원본="",
                             checked_at=now()))
            continue
        t = b.decode(enc, "replace")
        t = re.sub(r"<(script|style)\b.*?</\1>", "", t, flags=re.S | re.I)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
        import html as _h
        t = _h.unescape(t)
        sents = [s.strip() for s in re.split(r"(?<=[.다])\s+", t) if s.strip()]
        ban = [s for s in sents if BAN.search(s) and not re.search(r"이메일|전자우편", s)]
        rel = [s for s in sents if re.search(r"무단|수집|크롤|로봇|복제|저작권", s)]
        rows.append(dict(corp=corp, url=url, status="HTTP %s · %d자" % (st, len(t)), 자동수집금지_문구=" / ".join(ban)[:2000],
                         관련문장=" / ".join(rel)[:3000], 원본=p, checked_at=meta.get("fetched_at", "")))
        print(corp, st, len(t), "금지 문구 %d" % len(ban), flush=True)
        for s in ban[:5]:
            print("   BAN:", s[:300])
        for s in rel[:12]:
            print("   REL:", s[:300])
    write_csv(os.path.join(WORK, "보험자회사_약관.csv"), list(rows[0].keys()), rows)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"robots": robots, "explore": explore, "collect": collect, "terms": terms}.get(cmd, lambda: print(__doc__))()
