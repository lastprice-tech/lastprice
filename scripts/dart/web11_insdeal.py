# -*- coding: utf-8 -*-
"""11차 7-2 — 금융지주 소속 보험 자회사의 「대주주와의 거래」 공시(보험업법 §111③ 수시·§111④ 분기) 중 거래 상대방이
지주 본체인 건(원문 행)과 지주의 다른 자회사인 건(건수만). 10차 web10_insdeal(C24·C30) 보완.

    python3 scripts/dart/web11_insdeal.py probe <url> <저장이름> [k=v ...]   # (점검) 한 화면 받기 — robots 확인·원본 저장
    python3 scripts/dart/web11_insdeal.py list [회사…]       # (점검) 목록만 받아 고른 공시 출력
    python3 scripts/dart/web11_insdeal.py download [회사…]   # (점검) 고른 공시 원문 받기
    python3 scripts/dart/web11_insdeal.py terms              # 회사 이용약관 → dart_out/risk11/보험자회사_약관.csv
    python3 scripts/dart/web11_insdeal.py collect            # 전부 → handoff/원문_11차/보험자회사_지주거래공시.csv,
                                                             #   dart_out/risk11/보험자회사_지주거래_전체행.csv·_robots.csv·_약관.csv
    python3 scripts/dart/web11_insdeal.py collect --offline  # 받지 않고 저장된 원본만으로 CSV(robots 는 저장본으로 판정)

출처(2026-10-02 실측): 손보협회 공시실 > 경영공시 > 수시경영공시(kpub.knia.or.kr/managementDisc/spot/spotDisclosure.do)는
  회사별 누리집 링크 모음 — 손보사는 그 링크(메리츠화재·농협손보·신한EZ, 하나손보는 같은 경로의 현 주소 www.hanainsure.co.kr),
  생보사는 각 사 누리집 공시실(NH농협생명 /ho/on/HOON0002M00.nhl, 하나생명 /home/publicAnn/listPublicAnn.do?gubun=A).
  NH농협생명 원문 다운로드(/ho/zz/FileDwld.nhl)는 robots.txt 「Disallow: /ho/zz/」라 받지 않는다(목록만).

규율(COMMON.md·AGENT_11_INS.md): web11.Web(=web10/web9 Web: UA 고정·1.2초 간격·3회 재시도)만 쓴다. 호스트마다 web11.Robots
(RFC 9309 판정)로 확인하고 막힌 URL 은 요청하지 않는다. 로그인·캡차·보안장비 차단 화면이 나오면 우회하지 않고 멈춘다.
생명보험협회 공시실(pub.insure.or.kr)은 요청하지 않는다(10차 robots 「User-agent:* Disallow:/」 확인 — 행 note 에 사유만).
10차 web10_insdeal(PDF layout 텍스트화·서식 칸 읽기·이름 정규화)과 web10_knia(손보협회 공시실 화면 도구)를 import 해서
쓰고 고치지 않는다. 원본: dart_out/raw/web11/insdeal/ (받은 바이트 그대로 + .meta.json, sha256).
"""
from __future__ import annotations

import csv
import glob
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))

import web11                                                       # noqa: E402
from web11 import Web, save, Robots, now, write_csv, OUT, WORK, RAW   # noqa: E402
import web10_insdeal as W10                                        # noqa: E402  — 10차 보험 자회사 도구(import 만)
import web10_knia as K10                                           # noqa: E402  — 10차 손보협회 도구(import 만)

# web10_insdeal.read_layout 은 쪽 글(.layout.txt)을 모듈 전역 save(TASK, …)로 남긴다. 11차 원본은 dart_out/raw/web11/ 에
# 두어야 하므로 이 실행 안에서만 그 모듈의 save 이름을 web11.save 로 돌린다(파일은 고치지 않음, TASK 이름은 같은 "insdeal").
W10.save = web11.save

TASK = "insdeal"
DIR = os.path.join(RAW, TASK)
DIR10 = os.path.join(web11.web10.RAW, "insdeal")          # 10차 원본(같은 요청이면 다시 받지 않고 이것을 쓴다)
DIR10K = os.path.join(web11.web10.RAW, "knia")
NONE = "문서에 없음"
OFFLINE = "--offline" in sys.argv
BLOCK_WORDS = K10.BLOCK_WORDS + ["보안정책", "로그인 후 이용"]


class Stop(Exception):
    """차단·로그인·캡차·robots 금지 — 우회하지 않고 멈춘다."""


_W = None
_ROB = {}


def web():
    global _W
    if _W is None:
        _W = Web()
    return _W


def robots(base):
    """호스트(서브도메인)마다 한 번 — web11.Robots(RFC 9309, robots 원본은 dart_out/raw/web11/insdeal/)."""
    if base not in _ROB:
        if OFFLINE:
            _ROB[base] = _OfflineRobots(base)
        else:
            _ROB[base] = Robots(web(), base, TASK)
    return _ROB[base]


class _OfflineRobots(object):
    """--offline: 마지막으로 저장된 robots 원본으로 판정(받지 않음)."""

    def __init__(self, base):
        import urllib.robotparser
        self.base = base
        host = urllib.parse.urlparse(base).netloc
        p = os.path.join(DIR, "robots_%s.txt" % host)
        e = sorted(glob.glob(os.path.join(DIR, "robots_%s_HTTP*.html" % host)))
        self.rp, self.note = None, ""
        if os.path.exists(p):
            self.rp = urllib.robotparser.RobotFileParser()
            self.rp.parse(open(p, encoding="utf-8", errors="replace").read().splitlines())
            self.status = "OK"
        elif e:
            code = int(re.search(r"_HTTP(\d+)\.html$", e[-1]).group(1))
            self.status = "없음(HTTP %d)" % code
            self.note = "robots.txt 가 HTTP %d — RFC 9309 §2.3.1.3 에 따라 제한 없음으로 봄(저장본)" % code
        else:
            self.status, self.note = "확인 불가", "robots.txt 저장본 없음 — 수집 안 함"

    def allowed(self, url):
        if self.status.startswith("없음("):
            return True
        if self.rp is None:
            return False
        return self.rp.can_fetch(web11.UA, url)


def base_of(url):
    pu = urllib.parse.urlparse(url)
    return "%s://%s" % (pu.scheme, pu.netloc)


def fetch(url, name, meta=None, data=None, referer="", headers=None, enc="utf-8", cache=False):
    """robots 확인 → 받기 → 원본 저장(dart_out/raw/web11/insdeal/<name>) → 차단 신호 확인. (경로, meta, 바이트).
    robots 금지면 요청하지 않고 Stop. HTTP 오류는 응답 본문을 저장하고 Stop. --offline 이면 저장본만.
    cache=True(공시 원문 파일): 같은 이름 저장본이 있으면 다시 받지 않는다."""
    p0 = os.path.join(DIR, name)
    if OFFLINE or (cache and os.path.exists(p0) and os.path.exists(p0 + ".meta.json")):
        if os.path.exists(p0) and os.path.exists(p0 + ".meta.json"):
            return p0, json.load(open(p0 + ".meta.json", encoding="utf-8")), open(p0, "rb").read()
        raise Stop("--offline: 저장된 원본 없음 — %s" % name)
    rb = robots(base_of(url))
    if not rb.allowed(url):
        raise Stop("robots.txt(%s, 판정 %s)가 %s 를 막음 — 요청하지 않음 %s" % (base_of(url), rb.status, url, rb.note))
    req = dict(meta or {}, 출처URL=url, method="POST" if data is not None else "GET")
    if data is not None:
        req["요청본문"] = data if isinstance(data, str) else (data.decode("utf-8", "replace") if isinstance(data, bytes)
                                                          else urllib.parse.urlencode(data))
        if isinstance(data, str):
            data = data.encode("utf-8")
    try:
        fu, st, hd, b = web().get(url, referer=referer, data=data, headers=headers)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:                                # noqa: BLE001
            pass
        p, m = save(TASK, "실패응답_" + name + ".html", body,
                    dict(req, http_status=e.code, fetched_at=now(), 비고="HTTP 오류 응답 본문"))
        t = body.decode("utf-8", "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        raise Stop("%s HTTP %s%s (응답 저장 %s)" % (url, e.code, " 차단 신호 %s" % hit if hit else "", p))
    except Exception as e:                               # noqa: BLE001
        raise Stop("%s 접속 실패 %s: %s" % (url, type(e).__name__, e))
    ct = hd.get("Content-Type", "")
    cd = hd.get("Content-Disposition", "")
    p, m = save(TASK, name, b, dict(req, 최종URL=fu, http_status=st, content_type=ct, content_disposition=cd,
                                    원파일명=K10.cd_filename(cd), fetched_at=now()))
    if "html" in ct.lower():
        t = b[:60000].decode(enc, "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        if hit or "login" in urllib.parse.urlparse(fu).path.lower():
            raise Stop("%s 차단/로그인/캡차 신호 %s 최종URL %s (저장 %s)" % (url, hit, fu, p))
    return p, m, b


# ── 기간 ────────────────────────────────────────────────────────────────────
# 수시공시(§111③): 공시일 2025-01-01 이후. 분기공시(§111④): 최근 4개 분기 = 2025.3분기~2026.2분기(수집일 2026-10-02 기준
# 2026.3분기분은 아직 게시 전 — 분기 끝난 뒤 1개월 안 공시). 분기공시는 목록 제목의 분기 표기로 고르고, 표기가 없으면
# 공시일 2025-10-01 이후로 고른다(10차 FROM_QTR 와 같은 날짜).
FROM_SUSI = date(2025, 1, 1)
FROM_QTR = date(2025, 10, 1)
QTRS = [(2025, 3), (2025, 4), (2026, 1), (2026, 2)]
TODAY = date(2026, 10, 2)


def ymd(s):
    s = s or ""
    m = re.search(r"(20\d{2})\s*[.\-/년]?\s*(\d{1,2})\s*[.\-/월]?\s*(\d{1,2})", s)
    if m and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(3)) <= 31:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def is_qtr(title):
    t = title.replace(" ", "")
    return "분기" in t or "현황" in t or "4/4" in t or re.search(r"\d\s*Q", title) is not None


def qtr_of(title):
    """제목의 분기 표기 → (연, 분기) 또는 None. 예: 「(26.2분기)」「_26.1Q」「2026년 2분기」「25.3분기 현황」「2025년 4/4분기」."""
    t = title.replace(" ", "")
    for pat in (r"(20\d{2})년(\d)분기", r"(20\d{2})\.?(\d)분기", r"(?<!\d)(\d{2})\.(\d)분기", r"(?<!\d)(\d{2})년(\d)분기",
                r"(?<!\d)(\d{2})\.(\d)Q", r"(20\d{2})(\d)Q", r"(20\d{2})년(\d)/4분기", r"(?<!\d)(\d{2})(\d)Q"):
        m = re.search(pat, t)
        if m:
            y = int(m.group(1))
            return (y + 2000 if y < 100 else y, int(m.group(2)))
    return None


def is_deal(title):
    """대주주와의 거래 공시(§111③④) 제목인가 — 제목에 「대주주」가 있는 것(10차 KB라이프와 같은 규칙)."""
    return "대주주" in title


def wanted(title, d, file=""):
    """(고름 여부, 공시 구분, 사유). 분기 표기는 제목에 없으면 목록의 첨부 파일명에서 찾는다(하나생명)."""
    if not is_deal(title):
        return False, "", "제목에 대주주 없음"
    if is_qtr(title):
        q = qtr_of(title)
        if q:
            return (q in QTRS), "분기", "제목 분기 표기 %d.%d분기" % q
        q = qtr_of(file)
        if q:
            return (q in QTRS), "분기", "제목에 분기 표기 없음 — 목록 첨부 파일명 분기 표기 %d.%d분기" % q
        return bool(d and d >= FROM_QTR), "분기", "제목·파일명에 분기 표기 없음 — 공시일 %s 이후로 고름" % FROM_QTR
    return bool(d and d >= FROM_SUSI), "수시", "공시일 %s 이후" % FROM_SUSI


def text_of(s):
    return K10.text_of(s)


# ── 메리츠화재 (www.meritzfire.com) ───────────────────────────────────────
MRZ = "https://www.meritzfire.com"
MRZ_PAGE = MRZ + "/disclosure/managerial-announcement/occasional.do?vMode=PC"
MRZ_API = MRZ + "/json.smart?v=2.1.11"
MRZ_MENU = ("메리츠화재 누리집 > 공시실 > 경영공시 > 수시경영공시(%s — 손보협회 공시실 > 경영공시 > 수시경영공시의 「메리츠화재 링크」와 "
            "같은 주소)" % MRZ_PAGE)


def _mrz_body(srv, body):
    from datetime import datetime
    hd = {k: "" for k in ("globId", "resultRcvmsgSrvId", "esbIntfId", "exsIntfId", "ipv6Addr1", "ipv6Addr2",
                          "teleMsgMacAdr", "envirInfoDivCd", "firstTranssLcatgBizafairCd", "transsLcatgBizafairCd",
                          "prcesResultDivCd", "teleMsgRespnsDttm", "clienTrespnsDttm", "handcapLcatgBizafairCd",
                          "teleMsgVerDivCd", "belongGrpCd", "empNo", "empId", "dptCd", "hgrkDptCd", "nxupDptCd",
                          "resveLet")}
    hd.update(encryDivCd="0", rcvmsgSrvId=srv, reqRespnsDivCd="Q", syncDivCd="S", langDivCd="KR", transGrpCd="F",
              teleMsgReqDttm=datetime.now().strftime("%Y%m%d%H%M%S%f")[:17],
              screenId="/disclosure/managerial-announcement/occasional.do", lowrnkScreenId="/")
    return json.dumps({"header": hd, "body": body}, ensure_ascii=False).encode("utf-8")


def meritz_list():
    """화면 aytmMgbzPban.js retrievePbanLst 와 같은 POST JSON(/json.smart, 서비스 f.cg.he.cu.ua.o.bc.PbanBc.retrievePbanLst,
    ntbdIdn=3 수시경영공시, 쪽당 10건 — 화면 기본값). 등록일이 2025-01-01 앞인 쪽까지."""
    items, pages = [], []
    for pg in range(1, 60):
        body = {"pageNo": pg, "pageSize": 10, "searchType": "title", "keyWord": "", "ntbdIdn": "3",
                "cmNtbdCtgCd": "0000", "bcType": "AYTMMGBZPBAN_LST"}
        p, m, b = fetch(MRZ_API, "메리츠화재_수시경영공시_p%02d.json" % pg,
                        dict(메뉴=MRZ_MENU, 쪽=pg, 화면함수="aytmMgbzPban.js retrievePbanLst"),
                        data=_mrz_body("f.cg.he.cu.ua.o.bc.PbanBc.retrievePbanLst", body), referer=MRZ_PAGE,
                        headers={"Content-Type": "application/json; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
                                 "Accept": "application/json, text/javascript, */*; q=0.01"})
        j = json.loads(b.decode("utf-8"))
        if j.get("header", {}).get("prcesResultDivCd") != "0":
            raise Stop("메리츠화재 목록 응답 오류(prcesResultDivCd=%r, %s)" % (j.get("header", {}).get("prcesResultDivCd"), p))
        lst = j.get("body", {}).get("list") or []
        pages.append(dict(page=pg, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(lst),
                          total=j.get("body", {}).get("totalCount")))
        for k, r in enumerate(lst, 1):
            d = ymd(r.get("regDt", ""))
            items.append(dict(title=r.get("ttlNm", ""), d=d, date_txt=d.isoformat() if d else r.get("regDt", ""),
                              file=r.get("ortxtFileNm", ""), key=re.sub(r"\.pdf$", "", r.get("atcFileNm", "")) or "rank%s" % r.get("rank"),
                              enc=r.get("atcFilePthNm#[E]", ""), page=pg, row=k, list_path=p, list_sha=m["sha256"],
                              list_at=m["fetched_at"]))
        if not lst or all(ymd(r.get("regDt", "")) and ymd(r.get("regDt", "")) < FROM_SUSI for r in lst):
            break
    total = pages[0]["total"] if pages else ""
    scope = "%s — 목록 %d쪽(%d건, 사이트 표시 총 %s건) 받음, 등록일 %s 이후 수시·최근 4개 분기(2025.3~2026.2분기) 분기공시 중 " \
            "제목에 「대주주」" % (MRZ_MENU, len(pages), len(items), total, FROM_SUSI)
    return items, scope, pages


def meritz_get(it):
    """화면 pdfDownload 와 같은 2단계: POST /hp/fileDownload.do(check=Y) → GET 같은 주소(check=N)."""
    org = it["title"] + ".pdf"
    for a, bch in (("@", "%40"), (":", "%3A"), ("$", "%24"), (",", "%2C"), ("(", "%28"), (")", "%29"), ("/", "／")):
        org = org.replace(a, bch)                        # 화면 fileUtil.makeURIParam 그대로
    prm = {"path": it["enc"], "id": it["enc"], "orgFileName": org}
    url = MRZ + "/hp/fileDownload.do"
    name = "메리츠화재_%s.pdf" % re.sub(r"[^\w.]+", "_", it["key"])
    if OFFLINE or os.path.exists(os.path.join(DIR, name)):
        return fetch(url + "?" + urllib.parse.urlencode(dict(prm, check="N")), name, cache=True)
    p1, m1, b1 = fetch(url, name + ".check.json", dict(목록제목=it["title"], 단계="check=Y"), data=dict(prm, check="Y"),
                       referer=MRZ_PAGE, headers={"X-Requested-With": "XMLHttpRequest"})
    try:
        msg = json.loads(b1.decode("utf-8")).get("resultMsg")
    except Exception:                                    # noqa: BLE001
        msg = "응답이 JSON 아님"
    if msg not in ("", None):
        raise Stop("메리츠화재 다운로드 확인 단계 응답 %r (%s)" % (msg, p1))
    return fetch(url + "?" + urllib.parse.urlencode(dict(prm, check="N")), name,
                 dict(목록제목=it["title"], 목록등록일=it["date_txt"], 목록파일명=it["file"], 단계="check=N(GET)"),
                 referer=MRZ_PAGE)


# ── NH농협손해보험 (www.nhfire.co.kr) ─────────────────────────────────────
NHF = "https://www.nhfire.co.kr"
NHF_LIST = NHF + "/announce/managementAnnounce/retrieveAnytimeManagementAnnounce.nhfire"
NHF_MENU = ("NH농협손해보험 누리집 > 공시실 > 경영공시 > 수시경영공시(%s — 손보협회 공시실 > 경영공시 > 수시경영공시의 「농협손보 링크」)"
            % NHF_LIST)


def nhfire_list():
    """화면 goPage(row) 와 같은 POST(devonTargetRow=1,11,21…, searchYear 전체). 등록일이 2025-01-01 앞인 쪽까지."""
    items, pages = [], []
    for k in range(0, 80):
        row = 1 + 10 * k
        data = {"devonTargetRow": str(row), "devonOrderBy": "", "searchWord": "", "searchYear": "", "tempSearchWord": "",
                "ntfySqno": "", "ntfyPdtClsfCd": "02"}
        p, m, b = fetch(NHF_LIST, "NH농협손해보험_수시경영공시_r%03d.html" % row, dict(메뉴=NHF_MENU, devonTargetRow=row),
                        data=data, referer=NHF_LIST)
        t = b.decode("utf-8", "replace")
        i = t.find("수시경영 공시 리스트")
        if i < 0:
            raise Stop("NH농협손해보험 목록 표(「수시경영 공시 리스트」)가 없음 — 구조 변경 의심 (%s)" % p)
        tb = t[i:t.find("</table>", i)]
        got = []
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            fd = re.search(r"fnFileDownload\('([^']+)',\s*'([^']+)'\)", tr)
            if len(tds) < 3:
                continue
            title = re.sub(r"\s+", " ", text_of(tds[1]))
            d = ymd(text_of(tds[2]))
            got.append(dict(no=text_of(tds[0]), title=title, d=d, date_txt=text_of(tds[2]),
                            fileId=fd.group(1) if fd else "", seq=fd.group(2) if fd else "",
                            key=fd.group(1) if fd else "no%s" % text_of(tds[0]), page=row, row=len(got) + 1,
                            list_path=p, list_sha=m["sha256"], list_at=m["fetched_at"]))
        pages.append(dict(page=row, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(got)))
        items += got
        if not got or all(x["d"] and x["d"] < FROM_SUSI for x in got) or "goPage('%d')" % (row + 10) not in t:
            break
    scope = "%s — 목록 %d쪽(%d건) 받음, 등록일 %s 이후 수시·최근 4개 분기(2025.3~2026.2분기) 분기공시 중 제목에 「대주주」" % (
        NHF_MENU, len(pages), len(items), FROM_SUSI)
    return items, scope, pages


def nhfire_get(it):
    """화면 fnFileDownload(fileId, afileSeqn) 와 같은 POST /imageView/downloadFile.ajax."""
    return fetch(NHF + "/imageView/downloadFile.ajax", "NH농협손해보험_%s_%s.pdf" % (it["fileId"], it["seq"]),
                 dict(목록제목=it["title"], 목록등록일=it["date_txt"], 목록번호=it["no"], 화면함수="fnFileDownload"),
                 data={"fileId": it["fileId"], "afileSeqn": it["seq"]}, referer=NHF_LIST, cache=True)


# ── NH농협생명 (www.nhlife.co.kr) — 목록만(원문 다운로드 경로 /ho/zz/ 는 robots.txt Disallow) ─────────────
NHL = "https://www.nhlife.co.kr"
NHL_LIST = NHL + "/ho/on/HOON0002M00.nhl"
NHL_MENU = "NH농협생명 누리집 > 공시실 > 수시공시(%s)" % NHL_LIST


def nhlife_list():
    items, pages = [], []
    for pg in range(1, 80):
        p, m, b = fetch(NHL_LIST, "NH농협생명_수시공시_p%02d.html" % pg, dict(메뉴=NHL_MENU, 쪽=pg, 화면함수="linkPage"),
                        data={"prsPagcn": str(pg), "bulthTinm": ""}, referer=NHL_LIST)
        t = b.decode("utf-8", "replace")
        i = t.find("<caption>수시공시 리스트내역</caption>")
        if i < 0:
            raise Stop("NH농협생명 목록 표가 없음 — 구조 변경 의심 (%s)" % p)
        tb = t[i:t.find("</table>", i)]
        got = []
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            th = re.findall(r"<th[^>]*>(.*?)</th>", tr, re.S)
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            fd = re.search(r"fileDwld\('([^']+)',\s*'([^']+)'\)", tr)
            if len(tds) < 2:
                continue
            d = ymd(text_of(tds[1]))
            got.append(dict(no=text_of(th[0]) if th else "", title=re.sub(r"\s+", " ", text_of(tds[0])), d=d,
                            date_txt=text_of(tds[1]), apdFlid=fd.group(1) if fd else "", seq=fd.group(2) if fd else "",
                            key=fd.group(1) if fd else "", page=pg, row=len(got) + 1, list_path=p, list_sha=m["sha256"],
                            list_at=m["fetched_at"]))
        pages.append(dict(page=pg, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(got)))
        items += got
        if not got or all(x["d"] and x["d"] < FROM_SUSI for x in got) or "linkPage(%d)" % (pg + 1) not in t:
            break
    scope = "%s — 목록 %d쪽(%d건) 받음, 등록일 %s 이후 수시·최근 4개 분기(2025.3~2026.2분기) 분기공시 중 제목에 「대주주」" % (
        NHL_MENU, len(pages), len(items), FROM_SUSI)
    return items, scope, pages


def nhlife_url(it):
    return "%s/ho/zz/FileDwld.nhl?apdFlid=%s&fileSeqn=%s" % (NHL, it["apdFlid"], it["seq"])   # 화면 fileDwld() 주소


# ── 하나생명 (www.hanalife.co.kr) ─────────────────────────────────────────
HNL = "https://www.hanalife.co.kr"
HNL_LIST = HNL + "/home/publicAnn/listPublicAnn.do"
HNL_MENU = "하나생명 누리집 > 공시실 > 경영공시실 > 수시공시(%s?gubun=A)" % HNL_LIST


def hanalife_list():
    items, pages = [], []
    for pg in range(1, 80):
        if pg == 1:
            p, m, b = fetch(HNL_LIST + "?gubun=A", "하나생명_수시공시_p%02d.html" % pg, dict(메뉴=HNL_MENU, 쪽=pg),
                            referer=HNL + "/home/main.do")
        else:
            p, m, b = fetch(HNL_LIST, "하나생명_수시공시_p%02d.html" % pg, dict(메뉴=HNL_MENU, 쪽=pg, 화면함수="fn_search"),
                            data={"gubun": "A", "pageIndex": str(pg), "seqno": ""}, referer=HNL_LIST + "?gubun=A")
        t = b.decode("utf-8", "replace")
        i = t.find("<caption>경영공시실 파일 다운로드</caption>")
        if i < 0:
            raise Stop("하나생명 목록 표가 없음 — 구조 변경 의심 (%s)" % p)
        tb = t[i:t.find("</table>", i)]
        got = []
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            fd = re.search(r"fn_download\('([^']+)','([^']*)'\)", tr)
            if len(tds) < 3:
                continue
            d = ymd(text_of(tds[2]))
            got.append(dict(no=text_of(tds[0]), title=re.sub(r"\s+", " ", text_of(tds[1])), d=d, date_txt=text_of(tds[2]),
                            fname=fd.group(1) if fd else "", file=html.unescape(fd.group(2)) if fd else "",
                            key=(fd.group(1) if fd else "no%s" % text_of(tds[0])), page=pg, row=len(got) + 1,
                            list_path=p, list_sha=m["sha256"], list_at=m["fetched_at"]))
        pages.append(dict(page=pg, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(got)))
        items += got
        if not got or all(x["d"] and x["d"] < FROM_SUSI for x in got) or 'fn_search("%d")' % (pg + 1) not in t:
            break
    scope = "%s — 목록 %d쪽(%d건) 받음, 일자 %s 이후 수시·최근 4개 분기(2025.3~2026.2분기) 분기공시 중 제목에 「대주주」" % (
        HNL_MENU, len(pages), len(items), FROM_SUSI)
    return items, scope, pages


def hanalife_get(it):
    """화면 fn_download(filename, downFileName) 와 같은 GET /home/download2.do?fileName=HO_CI/<f>&downFileName=<encodeURI>."""
    url = "%s/home/download2.do?fileName=HO_CI/%s&downFileName=%s" % (
        HNL, it["fname"], urllib.parse.quote(it["file"], safe="~@#$&()*!+=:;,.?/'"))
    return fetch(url, "하나생명_%s" % re.sub(r"[^\w.]+", "_", it["fname"]),
                 dict(목록제목=it["title"], 목록일자=it["date_txt"], 목록파일명=it["file"], 화면함수="fn_download"),
                 referer=HNL_LIST + "?gubun=A", cache=True)


# ── PDF 읽기 ────────────────────────────────────────────────────────────────
# 1) 쪽 글: 10차 web10_insdeal.read_layout(pypdf layout 모드) 그대로 → <원본>.layout.txt (글자 층이 없으면 빈 쪽).
# 2) 표 칸: 9차 web9_c30.page_cells(칸마다 거는 clip 사각형으로 글자 묶기)를 먼저 쓰고, clip 칸이 없는 PDF(하나생명)는
#    칸 배경을 채우는 사각형 경로(m·l·h·f / re·f)로 같은 일을 한다(page_rect_cells). 칸 글자는 PDF 글자 층 추출 순서 그대로
#    잇는다(9차 clean: 칸 안 줄바꿈만 붙이고 연속 공백 하나로). 행 = 9차 rows_of(가장 얇은 가로 띠). → <원본>.cells.txt
# 3) 칸도 쪽 글도 없으면(스캔 그림 PDF) OCR 하지 않고 「미확인(문서 읽기 불가)」. 문서보안(DRM) 파일은 열지 않는다.
import web9_c30 as C9                                              # noqa: E402  — 9차 C30 칸 묶기(import 만)

CELL_NOTE = ("표 칸: 9차 web9_c30.page_cells(clip 사각형) — clip 이 없는 PDF 는 칸 배경 사각형 경로(m·l·h·f, re)로 같은 묶기; "
             "칸 글자는 PDF 글자 층 추출 순서 그대로, 칸 안 줄바꿈만 붙임(9차 clean). 행 = 9차 rows_of. 칸 사이 ' | '")


def page_rect_cells(page):
    """clip 이 없는 PDF 용: 채움·선 그리기 경로의 외곽 사각형을 칸으로 보고, 글자 시작점이 든 가장 작은 사각형에 글자를 묶는다.
    (칸 목록, 칸 밖 글)."""
    st = {"path": [], "rects": []}
    runs = []

    def before(op, args, cm, tm):
        if op in (b"m", b"l"):
            st["path"].append(C9._pt(float(args[0]), float(args[1]), cm))
        elif op == b"re":
            x, y, wd, ht = [float(a) for a in args]
            st["path"] += [C9._pt(x, y, cm), C9._pt(x + wd, y + ht, cm)]
        elif op in (b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"S", b"s", b"n"):
            if len(st["path"]) >= 2:
                xs = [p[0] for p in st["path"]]
                ys = [p[1] for p in st["path"]]
                st["rects"].append((min(xs), min(ys), max(xs), max(ys)))
            st["path"] = []

    def vt(text, cm, tm, fd, fs):
        if text:
            mm = C9._mul(tm, cm)
            runs.append((text, mm[4], mm[5]))

    page.extract_text(visitor_operand_before=before, visitor_text=vt)
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)
    rects = [r for r in set(tuple(round(v, 1) for v in r) for r in st["rects"])
             if r[2] - r[0] > 3 and r[3] - r[1] > 3 and (r[2] - r[0]) * (r[3] - r[1]) < 0.8 * pw * ph]
    cells, order, free = {}, [], []
    for text, x, y in runs:
        inside = [r for r in rects if r[0] - 0.5 <= x <= r[2] + 0.5 and r[1] - 0.5 <= y <= r[3] + 0.5]
        if not inside:
            free.append(text)
            continue
        r = min(inside, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
        if r not in cells:
            cells[r] = []
            order.append(r)
        cells[r].append(text)
    out = []
    for r in order:
        t = C9.clean("".join(cells[r]))
        if t.strip(" "):
            out.append(dict(x0=r[0], y0=r[1], x1=r[2], y1=r[3], text=t))
    return out, "".join(free)


def nows(s):
    return re.sub(r"\s+", "", s or "")


def read_doc(path):
    """(쪽 목록, 텍스트화 설명). 쪽 = {no, lines(layout), cells, free, rows, how}."""
    import pypdf
    lay, how = W10.read_layout(path)
    r = pypdf.PdfReader(path)
    pages = []
    for i, pg in enumerate(r.pages):
        cl, fr = C9.page_cells(pg)
        kind = "clip"
        if len(cl) < 3:
            cl2, fr2 = page_rect_cells(pg)
            if len(cl2) >= 3:
                cl, fr, kind = cl2, fr2, "rect"
            else:
                cl, kind = [], ""
        pages.append(dict(no=i + 1, lines=lay[i]["lines"] if i < len(lay) else [], cells=cl, free=fr,
                          rows=C9.rows_of(cl) if cl else [], how=kind))
    txt = ""
    for p in pages:
        txt += "=== p.%d (칸: %s) ===\n" % (p["no"], {"clip": "clip 사각형", "rect": "칸 배경 사각형"}.get(p["how"], "없음"))
        txt += "".join(C9.joinrow(rc) + "\n" for _, rc in p["rows"])
        txt += "--- 칸 밖 글 ---\n%s\n" % p["free"]
    cp = path + ".cells.txt"
    if any(p["cells"] for p in pages) and (not os.path.exists(cp) or open(cp, encoding="utf-8").read() != txt):
        save(TASK, os.path.basename(cp), txt.encode("utf-8"), dict(원본=path, 만든방법=CELL_NOTE, fetched_at=now()))
    return pages, how


# ── 서식 읽기 ───────────────────────────────────────────────────────────────
def _lab(t):
    """칸 라벨 비교용: 공백·앞뒤 번호(「1.」「대주주명1.」)·괄호 단위 표기를 뗀 글."""
    t = nows(t)
    t = re.sub(r"^\d+\.|\d+\.$", "", t)
    return t


def kv_find(rows, pat):
    """칸 행들에서 라벨 칸이 pat 에 맞는 행의 값(라벨 오른쪽 칸들). (값, 행 글)."""
    for rc in rows:
        for i, c in enumerate(rc):
            if re.fullmatch(pat, _lab(c["text"])):
                rest = [x["text"] for x in rc[i + 1:]]
                return " ".join(rest).strip(), " | ".join(x["text"] for x in rc)
    return "", ""


COMP_PAT = re.compile(r"포괄|(승인|의결|결의).{0,30}한도|한도.{0,30}(승인|의결|결의)")


def comp_marks(texts):
    """포괄승인 표기 — 「포괄」이 있거나 승인·의결·결의와 한도가 같은 칸(줄)에 함께 있는 글 그대로. 없으면 「문서에 없음」."""
    hit = [t for t in texts if COMP_PAT.search(nows(t))]
    return " / ".join(dict.fromkeys(hit)) if hit else NONE


def _name_line(lines):
    """칸이 없거나 칸에서 대주주명을 못 찾은 쪽: 「대주주명」이 든 줄(기재상의 주의 「주2) “대주주명”에는 …」 줄 제외)에서
    번호(「1.」)와 「대주주명」 글자만 뗀 나머지 — 글자 층의 글 그대로(순서 뒤바뀜 포함). (이름, 줄)."""
    for ln in lines:
        if re.search(r"대주주\s*명", ln) and "에는" not in ln and not re.match(r"\s*(주\s*\d?\s*\)|<|※)", ln):
            nm = re.sub(r"\s+", " ", re.sub(r"(?<![\d,])\d\s*\.|대주주\s*명", " ", ln)).strip()
            if nm:
                return nm, ln
    return "", ""


def form_rows(page, title, code):
    """수시공시 서식(제7-1-1~4호) 한 쪽 → 행 1개(대주주명이 없는 쪽이면 None). 칸에서 대주주명을 찾으면 칸으로,
    못 찾으면 쪽 글(layout)·칸 밖 글 줄에서."""
    rows = [rc for _, rc in page["rows"]]
    name = kv_find(rows, r"대주주명")[0] if rows else ""
    if name:
        bod, _ = kv_find(rows, r"이사회(결의|의결)일")
        kind = ""
        for pat in (r"신용공여종류", r"채권의종류", r"주식의종류"):
            kind, _ = kv_find(rows, pat)
            if kind:
                kind = "%s: %s" % (pat.replace("의", "의 "), kind)
                break
        amt = ""
        for pat, lab in ((r"신용공여금액(\(원\))?", "신용공여금액"), (r"취득금액(\(원\))?", "취득금액"), (r"거래금액(\(원\))?", "거래금액")):
            v, _ = kv_find(rows, pat)
            if v:
                amt = "%s: %s" % (lab, v)
                break
        day = ""
        for pat, lab in ((r"신용공여일", "신용공여일"), (r"취득일", "취득일"), (r"거래일", "거래일"),
                         (r"주주총회일(\(의결권행사일\))?|\(?의결권행사일\)?", "주주총회일(의결권행사일)")):
            v, _ = kv_find(rows, pat)
            if v:
                day = "%s %s" % (lab, v)
                break
        src = "\n".join(" | ".join(c["text"] for c in rc) for rc in rows)
        texts = [c["text"] for rc in rows for c in rc]
        how = "칸"
    else:
        body = []
        for ln in page["lines"]:
            if re.match(r"\s*<\s*기재\s*상", ln) or re.match(r"\s*<\s*>\s*기재상", ln):
                break
            body.append(ln)
        name, _ = _name_line(body) if body else ("", "")
        if not name:
            name, _ = _name_line([x for x in page["free"].split("\n")])
        if not name:
            return None
        bl = W10.body_lines([dict(no=page["no"], lines=page["lines"])])
        try:
            r = W10.susi_rows(bl, code, title)[0]
        except Exception:                             # noqa: BLE001
            r = dict(board_approval=NONE, amount=NONE, fy=NONE)
        bod = "" if r["board_approval"] == NONE else r["board_approval"]
        kind, amt = "", "" if r["amount"].startswith(NONE) or r["amount"].startswith("의결권") else r["amount"]
        day = "" if r["fy"] == NONE else r["fy"]
        src = W10.src_text(bl) if bl else "\n".join(body)
        texts = page["lines"]
        how = "쪽 글(layout)"
    vote = code == "제7-1-4호" or "의결권" in (title or "")
    return dict(counterparty=name or NONE, deal_type=(title or NONE) + (" / " + kind if kind else ""),
                amount=amt or ("의결권 행사 서식 — 금액 칸 없음" if vote else NONE),
                board=bod or NONE, comp=comp_marks(texts), source_text=src or NONE, page=str(page["no"]),
                doc_date=day or NONE, how=how, section=title)


def _hdr_label(c, hdr_cells):
    hs = sorted([h for h in hdr_cells if C9.xover(h, c)], key=lambda h: -h["y1"])
    return " ".join(dict.fromkeys(h["text"] for h in hs))


SKIP_NAME = re.compile(r"(소계|합계|총계)$|^해당사항없음$|^-$|^계정구분$")


def table_rows(page, title):
    """분기공시 표(제7-2-1호 신용공여현황·제7-2-2호 채권·주식 취득현황) 한 쪽 → 대주주 이름 칸마다 행 1개.
    여러 띠(거래일·만기일이 여러 줄)에 걸친 병합 이름 칸은 한 건으로 묶고, 그 띠들의 칸을 처음 나온 순서대로 잇는다."""
    out, name_h, hdr_cells, sect = [], None, [], ""
    groups = {}
    order = []
    for _, rc in page["rows"]:
        flat = [nows(c["text"]) for c in rc]
        nh = next((c for c in rc if nows(c["text"]) in ("대주주명", "대주주")), None)
        if nh and any(re.search(r"전분기말|신용공여|취득현황|종류", f) for f in flat):
            if name_h is None or (round(nh["x0"]), round(nh["y0"])) != (round(name_h["x0"]), round(name_h["y0"])):
                hdr_cells = []
                sect = ""
            name_h = nh
            hdr_cells += [c for c in rc if c not in hdr_cells]
            if any("신용공여" in f for f in flat):
                sect = "대주주에 대한 신용공여 현황"
            elif any("취득현황" in f for f in flat):
                sect = "대주주가 발행한 채권 또는 주식 취득현황"
            continue
        if name_h is None:
            continue
        if any(re.fullmatch(r"총계", f) for f in flat):     # 총계 줄 뒤(각주 등)는 표 밖 — 다음 머리까지 건너뜀
            if any(re.search(r"해당사항없음", f) for f in flat):
                out.append(dict(none=True, section=sect, source_text=C9.joinrow(rc), page=str(page["no"])))
            name_h = None
            continue
        nm = next((c for c in rc if C9.xover(c, name_h)), None)
        if nm is None or SKIP_NAME.search(nows(nm["text"])) or not nm["text"].strip(" -"):
            if any(re.search(r"해당사항없음", f) for f in flat):
                out.append(dict(none=True, section=sect, source_text=C9.joinrow(rc), page=str(page["no"])))
            continue
        k = (sect, round(nm["x0"], 1), round(nm["y0"], 1), round(nm["x1"], 1), round(nm["y1"], 1))
        if k not in groups:
            groups[k] = dict(name=nm, cells=[], sect=sect, hdr=list(hdr_cells), name_h=name_h)
            order.append(k)
        for c in rc:
            if not any(c is x for x in groups[k]["cells"]):
                groups[k]["cells"].append(c)
    for k in order:
        g = groups[k]
        cells, nm, hdr = g["cells"], g["name"], g["hdr"]
        acct = [c["text"] for c in cells if c["x1"] <= g["name_h"]["x0"] + 1]
        vals = [c for c in cells if c["x0"] >= g["name_h"]["x1"] - 1]
        kinds = ["%s: %s" % (_hdr_label(c, hdr), c["text"]) for c in vals if "종류" in nows(_hdr_label(c, hdr))]
        money = ["%s: %s" % (_hdr_label(c, hdr), c["text"]) for c in vals
                 if re.search(r"전분기말|당분기말|증감\(B-A\)", nows(_hdr_label(c, hdr))) and "사유" not in _hdr_label(c, hdr)]
        out.append(dict(counterparty=nm["text"], section=g["sect"],
                        deal_type="%s%s%s" % (g["sect"] or title or NONE,
                                              " / 계정구분: %s" % " ".join(acct) if acct else "",
                                              " / " + "; ".join(kinds) if kinds else ""),
                        amount="; ".join(money) or NONE, board=NONE, comp=NONE,
                        source_text=" | ".join(c["text"] for c in cells), page=str(page["no"]), how="칸",
                        note_extra="표 머리(칸 순서): %s" % " | ".join(_hdr_label(c, hdr) or "?" for c in cells)))
    return out


def basis_units(page):
    """쪽의 「(YYYY. MM. DD 기준, 단위: …)」 표기(칸 밖 글·쪽 글) — 글 그대로 목록."""
    src = page["free"] + "\n" + "\n".join(page["lines"])
    out = [re.sub(r"\s+", " ", m.group(0)) for m in re.finditer(r"\(\s*20\d{2}\s*\.[^()\n]{0,40}?\)\s*(기준\s*단위\s*\S+)?", src)]
    return list(dict.fromkeys(out))


def parse_doc(path, title_hint=""):
    """(행 목록, 문서 정보). 문서 정보 = {code, title, npg, how, readable, basis, mentions}."""
    pages, how = read_doc(path)
    all_lines = [ln for p in pages for ln in p["lines"]]
    has_text = any(ln.strip() for ln in all_lines) or any(p["cells"] for p in pages)
    info = dict(npg=len(pages), how=how, readable=has_text, code="", title="", basis=[],
                cellhow=sorted(set(p["how"] for p in pages if p["how"])))
    if not has_text:
        return [], info
    bl = W10.body_lines([dict(no=p["no"], lines=p["lines"]) for p in pages])
    code = W10.form_code(bl)
    if not code:
        m = re.search(r"제\s*(7)\s*-\s*(\d)\s*-\s*(\d)\s*호", " ".join(p["free"] for p in pages) + " ".join(all_lines))
        code = "제%s-%s-%s호" % m.groups() if m else ""
    title = W10.doc_title(bl)
    info.update(code=code, title=title)
    rows = []
    is_table = any(re.search(r"전분기말", nows(c["text"])) for p in pages for c in p["cells"]) or \
        any("전분기말" in nows(ln) for ln in all_lines)
    for p in pages:
        info["basis"] += basis_units(p)
        if is_table:
            if p["rows"]:
                rows += table_rows(p, title_hint)
            elif p["lines"]:                          # 칸 없는 표 — 10차 table_rows(layout 줄)
                for r in W10.table_rows([dict(no=p["no"], lines=p["lines"])], code, title):
                    if r["counterparty"] == NONE:
                        rows.append(dict(none=True, section=title, source_text=r["source_text"], page=r["page"]))
                    else:
                        rows.append(dict(counterparty=r["counterparty"], section=title, deal_type=r["deal_type"],
                                         amount=r["amount"], board=NONE, comp=NONE, source_text=r["source_text"],
                                         page=r["page"], how="쪽 글(layout)", note_extra=r.get("note_extra", "")))
        else:
            t = W10.doc_title(W10.body_lines([dict(no=p["no"], lines=p["lines"])])) or title or title_hint
            r = form_rows(p, t, code)
            if r:
                rows.append(r)
            elif rows and p["lines"]:                 # 대주주명 없는 이어지는 쪽 — 기재상의 주의 밖 글만 앞 행 원문에 덧붙임
                more = []
                for ln in p["lines"]:
                    if re.match(r"\s*<\s*>?\s*기재\s*상", ln):
                        break
                    if not re.match(r"\s*(주\s*\d\s*\)|\S{0,2}\s*을\s+기재)", ln):
                        more.append(ln)
                if more:
                    rows[-1]["source_text"] += "\n" + "\n".join(more)
    info["basis"] = list(dict.fromkeys(info["basis"]))
    full = nows(" ".join(all_lines) + " ".join(c["text"] for p in pages for c in p["cells"]))
    info["fulltext"] = full
    return rows, info


def pick(items):
    """목록에서 고를 공시 — (항목, 공시 구분, 고른 사유). 같은 파일 키는 한 번만."""
    out, seen = [], set()
    for it in items:
        ok, kind, why = wanted(it["title"], it["d"], it.get("file", ""))
        if not ok or it["key"] in seen:
            continue
        seen.add(it["key"])
        out.append((it, kind, why))
    return out


# ── 하나손해보험 (www.hanainsure.co.kr) ───────────────────────────────────
# 손보협회 공시실 「하나손보 링크」는 www.educar.co.kr/w/disclosure/manage/occasionalMngDisclosure 인데 그 호스트는
# robots.txt 요청부터 응답 없이 연결을 끊는다(RemoteDisconnected — RFC 9309 Unreachable → 그 호스트는 받지 않음).
# 하나손해보험 첫 화면 www.hanainsure.co.kr 의 「공시실」 메뉴가 같은 경로(/w/disclosure/…)를 쓰므로 그 호스트에서 robots 를
# 따로 확인하고 받는다(같은 회사 공식 누리집 — 차단 화면을 피해 간 것이 아니라 응답하지 않는 옛 주소 대신 현재 주소).
HNI = "https://www.hanainsure.co.kr"
HNI_PAGE = HNI + "/w/disclosure/manage/occasionalMngDisclosure"
HNI_API = HNI + "/w/disclosure/manage/getOccMngDisclosure.json"
HNI_MENU = "하나손해보험 누리집 > 공시실 > 경영공시 > 수시경영공시(%s)" % HNI_PAGE


def hanains_list():
    """화면 searchOccList(pageIndex) 와 같은 POST JSON {page, pageSize:10}."""
    items, pages = [], []
    for pg in range(1, 60):
        p, m, b = fetch(HNI_API, "하나손해보험_수시경영공시_p%02d.json" % pg, dict(메뉴=HNI_MENU, 쪽=pg, 화면함수="searchOccList"),
                        data=json.dumps({"page": pg, "pageSize": 10}).encode(), referer=HNI_PAGE,
                        headers={"Content-Type": "application/json;charset=utf-8", "X-Requested-With": "XMLHttpRequest",
                                 "Accept": "application/json, text/javascript, */*; q=0.01"})
        j = json.loads(b.decode("utf-8"))
        if not j.get("header", {}).get("success"):
            raise Stop("하나손해보험 목록 응답 실패 %r (%s)" % (j.get("header"), p))
        lst = j.get("body") or []
        pages.append(dict(page=pg, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(lst),
                          total=(j.get("page") or {}).get("totalRows")))
        for k, r in enumerate(lst, 1):
            d = ymd(r.get("sRegDt", ""))
            items.append(dict(no=str(r.get("nSeqNo", "")), title=r.get("sTitle", ""), d=d,
                              date_txt=d.isoformat() if d else r.get("sRegDt", ""), fid=r.get("sFileID", ""),
                              key=r.get("sFileID", "") or "seq%s" % r.get("nSeqNo"), page=pg, row=k, list_path=p,
                              list_sha=m["sha256"], list_at=m["fetched_at"]))
        if not lst or all(ymd(r.get("sRegDt", "")) and ymd(r.get("sRegDt", "")) < FROM_SUSI for r in lst):
            break
    scope = "%s — 목록 %d쪽(%d건, 사이트 표시 총 %s건) 받음, 게시일 %s 이후 수시·최근 4개 분기 분기공시 중 제목에 「대주주」" % (
        HNI_MENU, len(pages), len(items), pages[0]["total"] if pages else "", FROM_SUSI)
    return items, scope, pages


def hanains_get(it):
    """화면 목록의 <a href="/download/<sFileID>"> 그대로 GET."""
    return fetch("%s/download/%s" % (HNI, it["fid"]), "하나손해보험_%s.pdf" % it["fid"],
                 dict(목록제목=it["title"], 목록게시일=it["date_txt"], 목록seq=it["no"]), referer=HNI_PAGE, cache=True)


# ── 신한EZ손해보험 (www.shinhanez.co.kr) ──────────────────────────────────
SEZ = "https://www.shinhanez.co.kr"
SEZ_PAGE = SEZ + "/static/pub/PUB10000T01.html"
SEZ_MENU = "신한EZ손해보험 누리집 > 공시실 > 경영공시 > 수시공시 탭(%s — 손보협회 공시실 「신한EZ손해보험 링크」)" % SEZ_PAGE


def _sez_body(srv, payload):
    import random
    from datetime import datetime
    dttm = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    rdn = "%04d" % random.randint(0, 9999)
    hd = dict(trnmSysCode="HPG", ipAddr="", tlgrCretDttm=dttm, rndmNo=rdn, trnnNo="%sHPG%s" % (dttm, rdn), hsno=1,
              emnb="6900002", belnOrgnCode="", prsnInfoIncsYn="N", rcveSrvcId=srv, rcveSysCode="HPG", serverType="D",
              rspnDvsnCode="S", chnlTypeCode="SVR")                       # 화면 exchange.js 머리 그대로
    return json.dumps({"header": hd, "payload": payload}, ensure_ascii=False).encode("utf-8")


def shinhanez_list():
    """화면 PUB10000T01.js getList(tabNo=2 수시공시, pageNo) 와 같은 POST /shezApi(서비스 hpgpub0001r, perPage 10)."""
    items, pages = [], []
    for pg in range(1, 60):
        p, m, b = fetch(SEZ + "/shezApi", "신한EZ손해보험_수시공시_p%02d.json" % pg,
                        dict(메뉴=SEZ_MENU, 쪽=pg, 화면함수="PUB10000T01.js getList / exchange('hpgpub0001r')"),
                        data=_sez_body("hpgpub0001r", {"pageNo": pg, "perPage": 10, "mgmDclFlgCd": "2"}), referer=SEZ_PAGE,
                        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01",
                                 "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        j = json.loads(b.decode("utf-8"))
        lst = (j.get("payload") or {}).get("list") or []
        pages.append(dict(page=pg, path=p, sha256=m["sha256"], at=m["fetched_at"], n=len(lst),
                          total=(j.get("payload") or {}).get("totalCnt")))
        for k, r in enumerate(lst, 1):
            d = ymd(r.get("inpDt", ""))
            f = (r.get("fileList") or [{}])[0]
            items.append(dict(no=str(r.get("mgmDclAdmNo", "")), title=r.get("mgmDclCon", ""), d=d,
                              date_txt=r.get("inpDt", ""), fid=f.get("adxFileId", ""), seq=str(f.get("adxFileSeqno", "")),
                              file=f.get("adxFileNm", ""), key=f.get("adxFileId", "") or "adm%s" % r.get("mgmDclAdmNo"),
                              page=pg, row=k, list_path=p, list_sha=m["sha256"], list_at=m["fetched_at"]))
        if not lst or all(ymd(r.get("inpDt", "")) and ymd(r.get("inpDt", "")) < FROM_SUSI for r in lst):
            break
    scope = "%s — 목록 %d쪽(%d건, 사이트 표시 총 %s건) 받음, 등록일 %s 이후 수시·최근 4개 분기 분기공시 중 제목에 「대주주」" % (
        SEZ_MENU, len(pages), len(items), pages[0]["total"] if pages else "", FROM_SUSI)
    return items, scope, pages


def shinhanez_get(it):
    """화면 $.callNasDown({lrnkPath:'fileDown', dvsnCode:'cmn', fileNo, fileSeq, type:'chl'}) 와 같은 POST multipart /cmn/fileDown."""
    bd = "----lastpriceFormBoundary11"
    fields = [("lrnkPath", "fileDown"), ("dvsnCode", "cmn"), ("fileNo", it["fid"]), ("fileSeq", it["seq"]), ("type", "chl")]
    body = "".join('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (bd, k, v) for k, v in fields)
    body = (body + "--%s--\r\n" % bd).encode("utf-8")
    return fetch(SEZ + "/cmn/fileDown", "신한EZ손해보험_%s_%s.pdf" % (it["fid"], it["seq"]),
                 dict(목록제목=it["title"], 목록등록일=it["date_txt"], 목록파일명=it["file"], 화면함수="callNasDown"),
                 data=body, referer=SEZ_PAGE, headers={"Content-Type": "multipart/form-data; boundary=" + bd,
                                                       "X-Requested-With": "XMLHttpRequest"}, cache=True)


GETTER = {"메리츠화재": meritz_get, "NH농협손해보험": nhfire_get, "하나생명": hanalife_get, "하나손해보험": hanains_get,
          "신한EZ손해보험": shinhanez_get}
LISTER = {"메리츠화재": meritz_list, "NH농협손해보험": nhfire_list, "NH농협생명": nhlife_list, "하나생명": hanalife_list,
          "하나손해보험": hanains_list, "신한EZ손해보험": shinhanez_list}


# ── 지주·지주 자회사 이름 판정 ─────────────────────────────────────────────
# 지주 이름: 공백·(주)·주식회사를 뗀 이름이 아래 지주명과 같을 때만(AGENT_11_INS 지시 그대로).
# 지주의 자회사 목록: handoff/12_지분관계.csv 에 그 지주가 있으면 10차 web10_insdeal.group_list(가장 최근 보고서) 그대로,
#   없으면(메리츠금융지주·농협금융지주·하나금융지주) OpenDART 타법인출자현황(otrCprInvstmntSttus) 최근 사업보고서 —
#   레포 DART 수집기(scripts/dart/client.py DartClient)가 이미 받아 둔 dart_out/04_타법인출자현황.csv 의 같은 응답 행을
#   쓴다(새 API 호출 없음 — 키를 쓰지 않음). 이름 앞부분만 같은 것은 「이름 앞부분 일치」로 따로(10차 규칙).
HOLD = {"메리츠화재": "메리츠금융지주", "NH농협손해보험": "농협금융지주", "NH농협생명": "농협금융지주",
        "신한라이프": "신한지주", "하나생명": "하나금융지주", "하나손해보험": "하나금융지주", "신한EZ손해보험": "신한지주",
        "KB손해보험": "KB금융"}
PARENT = {"메리츠금융지주": "메리츠금융지주", "농협금융지주": "NH농협금융지주", "신한지주": "신한금융지주",
          "하나금융지주": "하나금융지주", "KB금융": "KB금융지주"}
HOLD_NAMES = {"메리츠금융지주": ["메리츠금융지주"], "농협금융지주": ["NH농협금융지주", "농협금융지주"],
              "신한지주": ["신한금융지주", "신한금융지주회사"], "하나금융지주": ["하나금융지주"],
              "KB금융": ["KB금융지주", "케이비금융지주"]}
SELF_NAMES = {"메리츠화재": ["메리츠화재해상보험", "메리츠화재"], "NH농협손해보험": ["농협손해보험", "NH농협손해보험"],
              "NH농협생명": ["농협생명보험", "NH농협생명보험", "NH농협생명"], "신한라이프": ["신한라이프생명보험", "신한라이프"],
              "하나생명": ["하나생명보험", "하나생명"], "하나손해보험": ["하나손해보험"], "신한EZ손해보험": ["신한EZ손해보험"],
              "KB손해보험": ["KB손해보험"]}
DART04 = os.path.join("dart_out", "04_타법인출자현황.csv")


def norm11(s):
    """10차 norm(공백·(주)·㈜·주식회사·(비상장)·(상장) 떼기, 케이비→KB) 앞에: DART 표 각주 표시 「(주2)」·주식 종류
    「(보통주)」「(우선주)」·각주 별표 「*」·글자 층에서 빈 괄호로 남은 「( )」를 떼고, 엔에이치→NH."""
    s = re.sub(r"\(\s*주\s*\d+\s*\)", "", s or "")
    s = re.sub(r"\((보통주|우선주)\)", "", s)
    s = re.sub(r"[*※]+", "", s)
    s = re.sub(r"\(\s*\)", "", s)
    return W10.norm(s.replace("엔에이치", "NH"))


_GL11 = {}


def group_list11(hold):
    """(자회사 이름들, 출처 설명)."""
    if hold in _GL11:
        return _GL11[hold]
    names, src = W10.group_list(hold)
    if not names:
        rows = [r for r in csv.DictReader(open(DART04, encoding="utf-8-sig"))
                if r["corp_label"] == hold and r["reprt_code"] == "11011"]
        if rows:
            yr = max(r["bsns_year"] for r in rows)
            rs = [r for r in rows if r["bsns_year"] == yr and r["inv_prm"].strip() != "합계"]
            names = [re.sub(r"\s+", "", r["inv_prm"]) for r in rs]
            src = ("OpenDART 타법인출자현황(otrCprInvstmntSttus) %s %s 사업보고서(rcept_no %s) %d곳 — 레포 DART 수집기가 받아 둔 "
                   "%s 행(원본 dart_out/raw_part*.tar.gz 안 %s, 받은 시각 %s; 새 API 호출 없음)" % (
                       hold, yr, rs[0]["rcept_no"], len(names), DART04, rs[0]["raw_path"], rs[0]["fetched_at"]))
        else:
            src = "handoff/12_지분관계.csv·%s 에 %s 행 없음" % (DART04, hold)
    _GL11[hold] = (names, src)
    return names, src


def classify11(cp, corp):
    """(상대방 구분, 근거). 「지주 본체」/「지주의 다른 자회사」/「지주의 다른 자회사(이름 앞부분 일치)」/「그 밖의 대주주」."""
    hold = HOLD[corp]
    subs, src = group_list11(hold)
    me = [norm11(x) for x in SELF_NAMES.get(corp, [])]
    subs2 = [s for s in subs if norm11(s) not in me]
    out = []
    for part in re.split(r"\s*[,/·]\s*|\s+및\s+", cp or ""):
        n = norm11(part)
        if not n or n in ("-", NONE):
            continue
        if any(n == norm11(h) for h in HOLD_NAMES[hold]):
            out.append(("지주 본체", "「%s」= 지주 이름(%s)" % (part, "·".join(HOLD_NAMES[hold]))))
            continue
        hit = [s for s in subs2 if any(n == p + norm11(s) or p + n == norm11(s) for p in ("", "KB", "NH"))]
        if hit:
            out.append(("지주의 다른 자회사", "「%s」= %s 의 「%s」" % (part, src, hit[0])))
            continue
        pre = [s for s in subs2 if len(norm11(s)) >= 3 and any(n.startswith(p + norm11(s)) for p in ("", "KB", "NH"))]
        if pre:
            out.append(("지주의 다른 자회사(이름 앞부분 일치)",
                        "「%s」 앞부분 = %s 의 「%s」(펀드·조합·채권 종목명 등 — 발행인·운용사 여부는 문서 표기만)" % (part, src, pre[0])))
    for k in ("지주 본체", "지주의 다른 자회사", "지주의 다른 자회사(이름 앞부분 일치)"):
        why = [w for kk, w in out if kk == k]
        if why:
            return k, "; ".join(why)
    return "그 밖의 대주주", "지주·지주 자회사 목록과 이름 불일치(%s)" % src


# ── 수집 ────────────────────────────────────────────────────────────────────
OUT_CSV = os.path.join(OUT, "보험자회사_지주거래공시.csv")
ALL_CSV = os.path.join(WORK, "보험자회사_지주거래_전체행.csv")
ROB_CSV = os.path.join(WORK, "보험자회사_robots.csv")
TERMS_CSV = os.path.join(WORK, "보험자회사_약관.csv")
COLS = ["corp_label", "parent", "공시 구분", "공시일", "거래 상대방", "상대방 구분", "거래 유형", "금액", "이사회 의결일",
        "포괄승인 표기", "source_text", "url", "doc_name", "page", "note", "collected_at", "source_sha256"]
ALL_COLS = COLS + ["판정 근거", "원본 경로", "목록 제목"]
KNIA_HUB = "https://kpub.knia.or.kr/managementDisc/spot/spotDisclosure.do"
KNIA_MENU = "손해보험협회 공시실(kpub.knia.or.kr) > 경영공시 > 수시경영공시(%s)" % KNIA_HUB
CORPS = [   # (회사, 필수/선택, 누리집 기준 주소, 목록 화면)
    ("메리츠화재", "필수", MRZ, MRZ_PAGE), ("NH농협손해보험", "필수", NHF, NHF_LIST), ("NH농협생명", "필수", NHL, NHL_LIST),
    ("신한라이프", "필수", "https://www.shinhanlife.co.kr", "https://www.shinhanlife.co.kr/"),
    ("하나생명", "필수", HNL, HNL_LIST + "?gubun=A"),
    ("하나손해보험", "선택", HNI, HNI_PAGE), ("신한EZ손해보험", "선택", SEZ, SEZ_PAGE),
]
TERMS_PAGES = [  # (회사, 약관 화면 URL, 저장 이름, 메모)
    ("메리츠화재", MRZ + "/default/views/biz/cm/mo/hmpguse/termsOfUse.tpl", "메리츠화재_termsOfUse.tpl",
     "홈페이지 이용약관 화면(/certification-center/use-of-website/user-agreement.do — 메뉴 목록 /menuList.do 의 「홈페이지 이용약관」)"
     " 의 본문 템플릿(화면 termsOfUse.js 가 그리는 tpl)"),
    ("NH농협손해보험", NHF + "/announce/hpTermsAndConditions/homepageTermsAndConditions.nhfire", "NH농협손해보험_이용약관.html",
     "하단 「홈페이지이용약관」"),
    ("NH농협생명", NHL + "/ho/tp/HOTP0001M00.nhl", "NH농협생명_이용약관.html", "하단 「이용약관」"),
    ("하나생명", HNL + "/foot/guide/adhesionContracts.do", "하나생명_이용약관.html", "하단 「이용약관」"),
    ("하나손해보험", HNI + "/w/terms/homepageContract", "하나손해보험_이용약관.html",
     "하단 「약관 및 정책」 > 「온라인서비스통합회원가입이용약관」(사이트 이용약관 따로 없음)"),
    ("신한EZ손해보험", SEZ + "/static/ann/ANN30000M01.html", "신한EZ손해보험_이용약관.html",
     "하단 「사이트 이용약관」(commView.goMenu('ANN30000M01') — 공시실 PUB10000T01 과 같은 /static/<메뉴>/<ID>.html 꼴)"),
]
BAN = W10.BAN
RESTRICT = re.compile(r"(제3자|타인).{0,40}(제공|이용하게|이용|배포)|(복제|전송|출판|배포|방송|재배포).{0,60}(금지|안\s*됩니다|아니\s*됩니다|"
                      r"없습니다|않습니다)|영리\s*목적")


def terms():
    """회사 누리집 이용약관 — 자동 수집 금지 문구(이메일 주소 수집 금지는 해당 아님)와 제3자 제공·이용 제한 문구를 글 그대로."""
    rows = []
    for corp, url, name, memo in TERMS_PAGES:
        try:
            p, m, b = fetch(url, name, dict(확인목적="이용약관 — 자동 수집 금지·제3자 제공 제한 문구", 메모=memo), cache=True)
        except Stop as e:
            rows.append(dict(corp=corp, url=url, status="받지 못함: %s" % e, 자동수집금지_문구="", 자동수집_낱말_검토="",
                             제3자제공_이용제한_문구="",
                             관련문장="", 판정="확인 불가", 원본="", checked_at=now(), note=memo))
            continue
        t = b.decode("utf-8", "replace")
        if "charset=euc-kr" in t[:3000].lower():
            t = b.decode("euc-kr", "replace")
        t = re.sub(r"<(script|style)\b.*?</\1>", " ", t, flags=re.S | re.I)
        t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
        sents = [x.strip() for x in re.split(r"(?<=[.다])\s+", t) if x.strip()]
        ban, notban = [], []
        for x in sents:                               # 10차 BAN 낱말 맞춤 → 맞은 부분을 보고 해당 아닌 것은 따로 적는다
            for mm in BAN.finditer(x):
                frag = x[mm.start():mm.end()]
                why = ("이메일 주소 수집 금지" if re.search(r"이메일|전자우편", x) else
                       "전자금융거래 정의의 「자동화된 방식」" if "자동화된" in frag else
                       "전자적 장치 정의의 「현금자동지급기·자동입출금기」" if re.search(r"자동지급기|자동입출금기", frag) else
                       "메뉴 글(「보안프로그램안내 … 이용약관」)" if "보안프로그램" in x[max(0, mm.start() - 4):mm.end()]
                       else "")
                (notban if why else ban).append("「…%s…」%s" % (frag, " → 해당 아님: " + why if why else ""))
        ban, notban = list(dict.fromkeys(ban)), list(dict.fromkeys(notban))
        res = [x for x in sents if RESTRICT.search(x) and re.search(r"얻은\s*정보|게시물|게시된|콘텐츠|저작물", x)]
        rel = [x for x in sents if re.search(r"무단|크롤|로봇|복제|저작권|자동", x)]
        ok = "약관" in t or "제1조" in t.replace(" ", "")
        verdict = ("확인 불가 — 받은 화면에 약관 본문 없음" if not ok else
                   ("자동 수집 금지 문구 있음 — 수집하지 않아야 함" if ban else "자동 수집 금지 문구 없음") +
                   ("; 제3자 제공·이용 제한 문구 있음(재배포 때 유의)" if res else ""))
        rows.append(dict(corp=corp, url=url, status="HTTP %s · %d자" % (m["http_status"], len(t)),
                         자동수집금지_문구=" / ".join(ban)[:2000], 자동수집_낱말_검토=" / ".join(notban)[:2000],
                         제3자제공_이용제한_문구=" / ".join(res)[:2000],
                         관련문장=" / ".join(rel)[:2500], 판정=verdict, 원본=p, checked_at=m.get("fetched_at", ""), note=memo))
        print(corp, verdict, flush=True)
    rows.append(dict(corp="(손해보험협회 공시실)", url="https://kpub.knia.or.kr/main.do", status="10차 확인 결과 재사용",
                     자동수집금지_문구="", 자동수집_낱말_검토="", 제3자제공_이용제한_문구="", 관련문장="",
                     판정=K10.verdict_of("kpub.knia.or.kr") or "10차 기록 없음",
                     원본="dart_out/risk10/knia_robots_약관.csv (10차 web10_knia terms, 2026-10-01)", checked_at=now(),
                     note="공시실 하단에 이용약관·저작권정책 링크 없음, 받은 화면에서 자동 수집 금지 문구 없음(10차). 11차는 robots.txt 만 "
                          "다시 확인(HTTP 403 — 제한 없음)"))
    write_csv(TERMS_CSV, list(rows[0].keys()), rows)
    return {r["corp"]: r for r in rows}


def robots_rows():
    """호스트별 robots 판정 기록(이번 실행에서 확인한 것 + 요청하지 않은 생보협회)."""
    rows = []
    hosts = [("손해보험협회 공시실", "https://kpub.knia.or.kr")] + [(c, b) for c, _, b, _ in CORPS] + \
        [("하나손해보험(손보협회 링크 주소)", "https://www.educar.co.kr")]
    seen = set()
    for label, base in hosts:
        if base in seen:
            continue
        seen.add(base)
        rb = robots(base)
        host = urllib.parse.urlparse(base).netloc
        p = os.path.join(DIR, "robots_%s.txt" % host)
        txt = open(p, encoding="utf-8", errors="replace").read() if rb.status == "OK" and os.path.exists(p) else ""
        meta = {}
        if os.path.exists(p + ".meta.json") and rb.status == "OK":
            meta = json.load(open(p + ".meta.json", encoding="utf-8"))
        extra = ""
        if txt and re.search(r"<html|<!doctype", txt[:500], re.I):
            extra = ("robots.txt 응답이 HTML(%s, 최종URL %s) — 규칙 줄 없음 → RFC 9309 상 제한 없음"
                     % (re.sub(r"\s+", " ", (re.search(r"<title>(.*?)</title>", txt, re.S | re.I) or [None, "제목 없음"])[1]).strip(),
                        meta.get("최종URL", "")))
        rows.append(dict(label=label, host=host, status=rb.status, note="; ".join(x for x in (rb.note, extra) if x),
                         root_allowed=rb.allowed(base + "/"), robots_text=" ".join(txt.split())[:1500] if not extra else "",
                         saved=p if txt else ";".join(sorted(glob.glob(os.path.join(DIR, "robots_%s_HTTP*.html" % host)))),
                         checked_at=meta.get("fetched_at", now())))
    rows.append(dict(label="생명보험협회 공시실", host="pub.insure.or.kr", status="요청 안 함(10차 확인 재사용)",
                     note="10차 robots.txt(2026-10-01 받음): User-agent:* Disallow:/ — 11차는 요청하지 않음(지시)",
                     root_allowed=False, robots_text="User-agent:Yeti Disallow: User-agent:daumoa Disallow: User-agent:* Disallow:/",
                     saved=os.path.join(DIR10, "robots_pub.insure.or.kr.txt"), checked_at="2026-10-01T17:24:33+09:00"))
    write_csv(ROB_CSV, list(rows[0].keys()), rows)
    return {r["label"]: r for r in rows}


def _short(p):
    return p


def doc_url(corp, it, meta):
    u = meta.get("출처URL", "")
    if meta.get("method") == "POST":
        u += " (POST %s)" % meta.get("요청본문", "")[:200]
    return u


def collect():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    # 손보협회 공시실 — 경영공시 > 수시경영공시 화면(각 사 누리집 링크 모음). 10차에 받지 않은 화면이라 새로 받는다.
    knia = {}
    try:
        p, m, b = fetch(KNIA_HUB, "knia_수시경영공시.html", dict(메뉴=KNIA_MENU))
        t = b.decode("utf-8", "replace")
        for li in re.findall(r"<li[^>]*>(.*?)</li>", t, re.S):
            h3 = re.search(r'<h3 class="title">(.*?)</h3>', li, re.S)
            a = re.search(r'<a href="([^"]+)"[^>]*>\s*링크 바로가기', li)
            if h3 and a:
                knia[text_of(h3.group(1))] = a.group(1)
        knia_meta = m
    except Stop as e:
        knia_meta = dict(오류=str(e))
    rob = robots_rows()
    trm = terms()
    all_rows, cover = [], []
    for corp, need, base, page in CORPS:
        hold = HOLD[corp]
        parent = PARENT[hold]
        rb = robots(base)
        if not rb.allowed(base + "/") or corp not in LISTER:
            why = rb.note or ("robots.txt 가 / 를 막음" if rb.status == "OK" else rb.status)
            if corp == "신한라이프":
                why = ("누리집 www.shinhanlife.co.kr 이 robots.txt 요청부터 응답하지 않음(%s; 10차에도 시간 초과) — RFC 9309 "
                       "Unreachable 이라 수집 안 함. 생명보험협회 공시실(pub.insure.or.kr)은 robots Disallow:/ 라 요청 안 함" % rb.note)
            cover.append(dict(corp=corp, need=need, status="접속 불가", why=why, url=base + "/robots.txt", n_s=0, n_q=0,
                              n_unread=0, scope=""))
            continue
        try:
            items, scope, pages = LISTER[corp]()
        except Stop as e:
            cover.append(dict(corp=corp, need=need, status="멈춤", why=str(e), url=page, n_s=0, n_q=0, n_unread=0, scope=""))
            continue
        picks = pick(items)
        n_s = sum(1 for _, k, _ in picks if k == "수시")
        n_q = sum(1 for _, k, _ in picks if k == "분기")
        dates = sorted(it["d"] for it, _, _ in picks if it["d"])
        st = dict(corp=corp, need=need, status="OK", why="", url=page, n_s=n_s, n_q=n_q, n_unread=0, scope=scope,
                  period="%s~%s" % (dates[0], dates[-1]) if dates else "",
                  n_list=len(items), n_deal=sum(1 for it in items if is_deal(it["title"])))
        tnote = trm.get(corp, {}).get("판정", "")
        print("==", corp, scope, "→ 수시 %d · 분기 %d" % (n_s, n_q), flush=True)
        for it, kind, why_pick in sorted(picks, key=lambda x: (x[0]["d"] or date.min, x[0]["key"])):
            base_row = dict(corp_label=corp, parent=parent, **{"공시 구분": kind, "공시일": it["d"].isoformat() if it["d"] else
                                                                it["date_txt"]})
            listnote = "목록 「%s」 %s (%s %s쪽 %s행, 목록 원본 %s sha256 %s…) / 고른 사유: %s" % (
                it["title"], it["date_txt"], "목록", it["page"], it["row"], it["list_path"], it["list_sha"][:12], why_pick)
            if corp == "NH농협생명":                 # 원문 다운로드 경로가 robots Disallow — 요청하지 않음
                u = nhlife_url(it)
                why = ("원문 받지 않음 — 다운로드 주소 %s 의 /ho/zz/ 가 robots.txt(www.nhlife.co.kr) 「Disallow: /ho/zz/」" % u)
                all_rows.append(dict(base_row, **{"거래 상대방": NONE, "상대방 구분": "미확인(원문 받지 않음 — robots)",
                                                  "거래 유형": it["title"], "금액": NONE, "이사회 의결일": NONE,
                                                  "포괄승인 표기": NONE, "source_text": NONE, "url": u, "doc_name": NONE,
                                                  "page": "", "collected_at": it["list_at"], "source_sha256": "",
                                                  "note": " / ".join([why, listnote, "출처 화면·기간: " + scope]),
                                                  "판정 근거": why, "원본 경로": "", "목록 제목": it["title"]}))
                st["n_unread"] += 1
                continue
            try:
                p, m, b = GETTER[corp](it)
            except Stop as e:
                all_rows.append(dict(base_row, **{"거래 상대방": NONE, "상대방 구분": "미확인(원문 받기 실패)",
                                                  "거래 유형": it["title"], "금액": NONE, "이사회 의결일": NONE,
                                                  "포괄승인 표기": NONE, "source_text": NONE, "url": "", "doc_name": NONE,
                                                  "page": "", "collected_at": now(), "source_sha256": "",
                                                  "note": "원문 받기 멈춤: %s / %s" % (e, listnote), "판정 근거": str(e),
                                                  "원본 경로": "", "목록 제목": it["title"]}))
                st["n_unread"] += 1
                continue
            fname = m.get("원파일명") or W10.cd_name(m.get("content_disposition", ""))
            if not fname or re.search(r"[\x80-\xff]|\?", fname):     # 서버가 파일명 글자를 깨뜨려 보낸 경우 — 목록의 파일명
                fname = it.get("file") or it["title"]
            url = doc_url(corp, it, m)
            common = dict(url=url, doc_name=fname, collected_at=m.get("fetched_at", ""), source_sha256=m.get("sha256", ""))
            src_note = ["원본 %s (sha256 %s…)" % (p, m.get("sha256", "")[:12]), listnote, "출처 화면·기간: " + scope]
            if tnote:
                src_note.append("이용약관: " + tnote)
            if not b.startswith(b"%PDF"):
                why = ("문서보안(DRM) 암호화 파일(파일 머리 %r) — 열거나 풀지 않음(우회 금지)" % b[:8].decode("latin-1")
                       if b.startswith(b"SCDSA") else "PDF 아님(%d바이트, %s)" % (len(b), m.get("content_type")))
                all_rows.append(dict(base_row, **common, **{"거래 상대방": NONE, "상대방 구분": "미확인(문서 읽기 불가)",
                                                            "거래 유형": it["title"], "금액": NONE, "이사회 의결일": NONE,
                                                            "포괄승인 표기": NONE, "source_text": NONE, "page": "",
                                                            "note": " / ".join([why] + src_note), "판정 근거": why,
                                                            "원본 경로": p, "목록 제목": it["title"]}))
                st["n_unread"] += 1
                continue
            try:
                rows, info = parse_doc(p, it["title"])
            except Exception as e:                       # noqa: BLE001
                rows, info = [], dict(readable=False, npg=0, how="", code="", title="", basis=[], cellhow=[],
                                      fulltext="", err=repr(e))
            how = info.get("how", "")
            hownote = "텍스트화: %s → %s.layout.txt%s" % (how, p, ("; " + CELL_NOTE + " → %s.cells.txt" % p)
                                                       if info.get("cellhow") else "")
            if not info.get("readable"):
                why = ("PDF 글자 층이 비어 있음(스캔 그림 PDF로 보임, %d쪽) — 글자 추출 불가, OCR 하지 않음" % info.get("npg", 0)
                       if not info.get("err") else "PDF 읽기 실패 %s" % info["err"])
                all_rows.append(dict(base_row, **common, **{"거래 상대방": NONE, "상대방 구분": "미확인(문서 읽기 불가)",
                                                            "거래 유형": it["title"], "금액": NONE, "이사회 의결일": NONE,
                                                            "포괄승인 표기": NONE, "source_text": NONE, "page": "1",
                                                            "note": " / ".join([why] + src_note + [hownote]),
                                                            "판정 근거": why, "원본 경로": p, "목록 제목": it["title"]}))
                st["n_unread"] += 1
                continue
            mention = [h for h in HOLD_NAMES[hold] if nows(h) in info.get("fulltext", "")]
            real = [r for r in rows if not r.get("none")]
            if not real:                                 # 표에 대주주 행 없음(「해당사항 없음」 등) — 작업 기록에만
                nones = list(dict.fromkeys(r["source_text"] for r in rows if r.get("none")))
                why = "표에 대주주 이름 행 없음" + ("(「해당사항 없음」: %s)" % " ‖ ".join(nones) if nones else "")
                all_rows.append(dict(base_row, **common, **{"거래 상대방": NONE, "상대방 구분": "해당 행 없음",
                                                            "거래 유형": info.get("title") or it["title"], "금액": NONE,
                                                            "이사회 의결일": NONE, "포괄승인 표기": NONE,
                                                            "source_text": " ‖ ".join(nones) or NONE, "page": "1",
                                                            "note": " / ".join([why, "서식 %s" % (info.get("code") or "번호 없음"),
                                                                                "표 표기: %s" % " ".join(info.get("basis", []))]
                                                                               + src_note + [hownote]),
                                                            "판정 근거": why, "원본 경로": p, "목록 제목": it["title"]}))
                continue
            for r in real:
                k, why = classify11(r["counterparty"], corp)
                notes = ["상대방 판정: %s — %s" % (k, why), "서식 %s" % (info.get("code") or "번호 없음"),
                         "PDF %d쪽" % info.get("npg", 0), "문서 일자: %s" % r.get("doc_date", NONE) if kind == "수시" else
                         "표 표기(기준일·단위, 글 그대로): %s" % (" ".join(info.get("basis", [])) or NONE),
                         "읽은 곳: %s" % r.get("how", "")]
                if r.get("note_extra"):
                    notes.append(r["note_extra"])
                if mention and k != "지주 본체":
                    notes.append("문서 글 안에 지주 이름(%s)이 있음 — 거래 상대방 칸은 아님(.layout.txt·.cells.txt 참조)"
                                 % "·".join(mention))
                notes += src_note + [hownote]
                all_rows.append(dict(base_row, **common, **{
                    "거래 상대방": r["counterparty"], "상대방 구분": k, "거래 유형": r["deal_type"], "금액": r["amount"],
                    "이사회 의결일": r["board"], "포괄승인 표기": r["comp"], "source_text": r["source_text"],
                    "page": r["page"], "note": " / ".join(notes), "판정 근거": why, "원본 경로": p,
                    "목록 제목": it["title"]}))
        cover.append(st)
    write_outputs(all_rows, cover, rob, trm, knia, knia_meta)


def write_outputs(all_rows, cover, rob, trm, knia, knia_meta):
    out = []
    for st in cover:
        corp = st["corp"]
        hold = HOLD[corp]
        parent = PARENT[hold]
        mine = [r for r in all_rows if r["corp_label"] == corp]
        if st["status"] != "OK":
            out.append(dict(corp_label=corp, parent=parent, **{"공시 구분": "수시·분기", "공시일": NONE, "거래 상대방": NONE,
                                                               "상대방 구분": "미확인(누리집 접속 불가)", "거래 유형": NONE,
                                                               "금액": NONE, "이사회 의결일": NONE, "포괄승인 표기": NONE,
                                                               "source_text": NONE, "url": st["url"], "doc_name": NONE,
                                                               "page": "", "collected_at": now(), "source_sha256": "",
                                                               "note": "%s(%s) — %s" % (corp, st["need"], st["why"])}))
            continue
        hold_rows = [r for r in mine if r["상대방 구분"] == "지주 본체"]
        out += [{k: r.get(k, "") for k in COLS} for r in hold_rows]
        for kind in ("수시", "분기"):
            ks = [r for r in mine if r["공시 구분"] == kind]
            if not ks:
                continue
            sub = [r for r in ks if r["상대방 구분"] == "지주의 다른 자회사"]
            pre = [r for r in ks if r["상대방 구분"] == "지주의 다른 자회사(이름 앞부분 일치)"]
            ds = sorted(r["공시일"] for r in ks)
            from collections import Counter
            cnt = Counter(nows(r["거래 상대방"]) for r in sub)
            pcnt = Counter(nows(r["거래 상대방"]) for r in pre)
            ndoc = len(set(r["원본 경로"] or r["url"] for r in ks))
            nread = len(set(r["원본 경로"] or r["url"] for r in ks if not r["상대방 구분"].startswith("미확인")))
            note = ["%s 공시 %d건(%s~%s, 문서 %d개 — 읽지 못한 문서 %d개)에서 거래 상대방이 지주의 다른 자회사(이름 일치)인 행 %d건"
                    % (kind, len(set(r["목록 제목"] + r["공시일"] + (r["원본 경로"] or r["url"]) for r in ks)), ds[0], ds[-1],
                       ndoc, len(set(r["원본 경로"] or r["url"] for r in ks if r["상대방 구분"].startswith("미확인"))),
                       len(sub)),
                    "상대방 이름별(공백 뺀 표기): %s" % (", ".join("%s %d건" % x for x in cnt.most_common()) or "없음"),
                    "공시일: %s" % (", ".join(sorted(set(r["공시일"] for r in sub))) or "없음")]
            if kind == "분기":
                note.append("분기공시는 표의 대주주 행(계정구분·표 별) 하나를 1건으로 셈 — 같은 상대방이 분기마다 다시 나옴")
            if pre:
                note.append("별도: 이름 앞부분만 지주 자회사와 같은 상대방 %d건(%s) — 건수에 넣지 않음"
                            % (len(pre), ", ".join("%s %d건" % x for x in pcnt.most_common())))
            note.append("자회사 목록: %s" % group_list11(hold)[1])
            note.append("개별 행: %s (상대방 구분 열)" % ALL_CSV)
            out.append(dict(corp_label=corp, parent=parent, **{"공시 구분": kind, "공시일": "%s~%s" % (ds[0], ds[-1]),
                                                               "거래 상대방": "(지주의 다른 자회사)",
                                                               "상대방 구분": "지주의 다른 자회사", "거래 유형": "건수만",
                                                               "금액": "", "이사회 의결일": "", "포괄승인 표기": "",
                                                               "source_text": ("건수만: %d건" % len(sub)) if nread else
                                                               "건수만: 미확인(읽은 문서 0개)", "url": st["url"],
                                                               "doc_name": "", "page": "", "collected_at": now(),
                                                               "source_sha256": "", "note": " / ".join(note)}))
        unread = [r for r in mine if r["상대방 구분"].startswith("미확인")]
        out += [{k: r.get(k, "") for k in COLS} for r in unread]
        if not hold_rows:
            seen_docs = len(set(r["원본 경로"] or r["url"] for r in mine))
            read_docs = len(set(r["원본 경로"] or r["url"] for r in mine if not r["상대방 구분"].startswith("미확인")))
            out.append(dict(corp_label=corp, parent=parent, **{
                "공시 구분": "수시·분기", "공시일": NONE, "거래 상대방": NONE,
                "상대방 구분": "지주 본체" if read_docs or not mine else "미확인(읽은 문서 없음)", "거래 유형": NONE,
                "금액": NONE, "이사회 의결일": NONE, "포괄승인 표기": NONE, "source_text": NONE, "url": st["url"],
                "doc_name": NONE, "page": "", "collected_at": now(), "source_sha256": "",
                "note": " / ".join(x for x in [
                    ("거래 상대방이 지주 본체(%s)인 행 없음" % "·".join(HOLD_NAMES[hold])) if read_docs or not mine else
                    "고른 공시 원문을 하나도 읽지 못함(위 「미확인」 행) — 지주 본체(%s) 상대방 건이 있는지 모름"
                    % "·".join(HOLD_NAMES[hold]),
                    "확인한 화면: %s" % st["scope"],
                    "목록 %d건 중 제목에 「대주주」 %d건, 고른 공시(수시 2025-01-01 이후·분기 2025.3~2026.2분기) 수시 %d건·분기 %d건"
                    " (기간 %s), 본 문서 %d개 — 그중 읽지 못함 %d개(위 「미확인」 행)" % (
                        st.get("n_list", 0), st.get("n_deal", 0), st["n_s"], st["n_q"], st.get("period", ""), seen_docs,
                        st["n_unread"]),
                    "손보협회 공시실 링크: %s" % knia.get({"메리츠화재": "메리츠화재", "NH농협손해보험": "농협손보",
                                                       "하나손해보험": "하나손보", "신한EZ손해보험": "신한EZ손해보험"}.get(corp, ""),
                                                      "해당 없음(생명보험사)") if corp not in ("NH농협생명", "하나생명")
                    else "생명보험협회 공시실(pub.insure.or.kr)은 robots Disallow:/ 라 요청 안 함",
                    "이용약관: %s" % trm.get(corp, {}).get("판정", "")] if x)}))
    # KB손해보험 — 10차 「미확인(문서 읽기 불가)」 분기공시 4건
    kb10 = [r for r in csv.DictReader(open(os.path.join("handoff", "원문_10차", "보험자회사_대주주거래공시.csv"),
                                           encoding="utf-8-sig"))
            if r["corp_label"] == "KB손해보험" and "미확인(문서 읽기 불가)" in r["note"]]
    out.append(dict(corp_label="KB손해보험", parent="KB금융지주", **{
        "공시 구분": "분기", "공시일": ", ".join(r["공시일"] for r in kb10), "거래 상대방": NONE,
        "상대방 구분": "미확인(문서 읽기 불가)", "거래 유형": "대주주에 대한 신용공여 현황 및 채권·주식 취득현황(분기)",
        "금액": NONE, "이사회 의결일": NONE, "포괄승인 표기": NONE, "source_text": NONE, "url": KNIA_HUB,
        "doc_name": " | ".join(r["doc_name"] for r in kb10), "page": "", "collected_at": knia_meta.get("fetched_at", now()),
        "source_sha256": "",
        "note": "10차 handoff/원문_10차/보험자회사_대주주거래공시.csv 의 「미확인(문서 읽기 불가)」 %d건(%s) — 손보협회 공시실에 같은 "
                "공시 글이 있는지 확인: 공시실 「경영공시 > 수시경영공시」는 회사별 누리집 링크 모음뿐(KB손보 링크 %s = 10차 출처와 "
                "같은 화면), 「정기경영공시」는 연도별 통일경영공시 PDF(분기 대주주거래 공시와 다른 문서)라 같은 공시 글 없음 → "
                "미확인 유지(OCR 하지 않음). 원본은 10차 dart_out/raw/web10/insdeal/(KB손해보험_seq982·1003·1029·1055.pdf)"
                % (len(kb10), ", ".join("%s %s" % (r["공시일"], r["url"]) for r in kb10), knia.get("KB손보", "?"))}))
    out.append(dict(corp_label="(손해보험협회 공시실)", parent="", **{
        "공시 구분": "수시·분기", "공시일": NONE, "거래 상대방": NONE, "상대방 구분": "문서에 없음", "거래 유형": NONE,
        "금액": NONE, "이사회 의결일": NONE, "포괄승인 표기": NONE, "source_text": NONE, "url": KNIA_HUB, "doc_name": NONE,
        "page": "", "collected_at": knia_meta.get("fetched_at", now()), "source_sha256": knia_meta.get("sha256", ""),
        "note": "%s 는 대주주거래 공시 글을 따로 싣지 않고 회사별 누리집 수시경영공시 링크만 둠(메리츠화재 %s · 농협손보 %s · 하나손보 %s"
                " · 신한EZ손해보험 %s · KB손보 %s) — 각 사 행은 이 링크(하나손보는 같은 경로의 현 주소)에서 받음. robots: %s. 약관: %s"
                % (KNIA_MENU, knia.get("메리츠화재", "?"), knia.get("농협손보", "?"), knia.get("하나손보", "?"),
                   knia.get("신한EZ손해보험", "?"), knia.get("KB손보", "?"),
                   "%s %s" % (rob.get("손해보험협회 공시실", {}).get("status", ""), rob.get("손해보험협회 공시실", {}).get("note", "")),
                   trm.get("(손해보험협회 공시실)", {}).get("판정", ""))}))
    out.append(dict(corp_label="(생명보험협회 공시실)", parent="", **{
        "공시 구분": "수시·분기", "공시일": NONE, "거래 상대방": NONE, "상대방 구분": "요청 안 함", "거래 유형": NONE,
        "금액": NONE, "이사회 의결일": NONE, "포괄승인 표기": NONE, "source_text": NONE, "url": "https://pub.insure.or.kr/robots.txt",
        "doc_name": NONE, "page": "", "collected_at": "2026-10-01T17:24:33+09:00", "source_sha256": "",
        "note": "robots.txt(pub.insure.or.kr) 가 User-agent:* Disallow:/ (10차 확인, 원본 %s) — 11차는 요청하지 않음(지시). "
                "생보사(NH농협생명·신한라이프·하나생명)는 각 사 누리집에서만 확인" % os.path.join(DIR10, "robots_pub.insure.or.kr.txt")}))
    for r in out:
        r.setdefault("collected_at", now())
    write_csv(OUT_CSV, COLS, [{k: r.get(k, "") for k in COLS} for r in out])
    write_csv(ALL_CSV, ALL_COLS, [{k: r.get(k, "") for k in ALL_COLS} for r in all_rows])
    from collections import Counter
    print("handoff %d행 → %s · 전체 %d행 → %s" % (len(out), OUT_CSV, len(all_rows), ALL_CSV))
    print(Counter((r["corp_label"], r["상대방 구분"]) for r in all_rows))
    print(Counter((r["corp_label"], r["상대방 구분"]) for r in out))


def download(argv):
    for corp in (argv or list(GETTER)):
        items, scope, pages = LISTER[corp]()
        for it, kind, why in pick(items):
            try:
                p, m, b = GETTER[corp](it)
            except Stop as e:
                print(corp, it["title"], "Stop", e)
                continue
            head = b[:8]
            print(corp, kind, it["date_txt"], it["title"], "→", p, m.get("content_type"), len(b), head)


def listing(argv):
    fn = LISTER
    for corp in (argv or list(fn)):
        try:
            items, scope, pages = fn[corp]()
        except Stop as e:
            print(corp, "Stop", e)
            continue
        print("==", corp, scope)
        for it in items:
            ok, kind, why = wanted(it["title"], it["d"], it.get("file", ""))
            if is_deal(it["title"]):
                print("  ", "O" if ok else "-", kind, it["date_txt"], it["title"], "|", it.get("file", ""), "|", why)


def probe(argv):
    url, name = argv[0], argv[1]
    data = dict(x.split("=", 1) for x in argv[2:]) or None
    try:
        p, m, b = fetch(url, name, dict(확인목적="점검(probe)"), data=data, referer=base_of(url) + "/")
    except Stop as e:
        print("Stop:", e)
        return
    print(m["http_status"], m["content_type"], m["바이트"], m["최종URL"], p)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "probe":
        probe(sys.argv[2:])
    elif cmd == "download":
        download([a for a in sys.argv[2:] if not a.startswith("--")])
    elif cmd == "list":
        listing([a for a in sys.argv[2:] if not a.startswith("--")])
    elif cmd == "collect":
        collect()
    elif cmd == "terms":
        terms()
    else:
        print(__doc__)
