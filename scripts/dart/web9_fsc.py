# -*- coding: utf-8 -*-
"""9차 — 금융위원회 「금융규제·법령해석포털」(better.fsc.go.kr) 법령해석·비조치의견서 검색 수집.

    python3 scripts/dart/web9_fsc.py             # 검색 → 상세 → 목록 CSV·원문 md
    python3 scripts/dart/web9_fsc.py --refresh   # 저장해 둔 원본을 쓰지 않고 다시 받는다

요청은 공용 모듈 web9.Web(UA·1.2초 간격·3회 재시도)로 하나씩 보낸다. 접속 자체가 끊기면(프록시 터널
끊김 등) 30·60초 쉬고 다시 해 보고, 그래도 안 되거나 401·403·429·로그인 화면·캡차가 나오면 우회하지 않고
멈춘 뒤 사유를 검색기록에 남긴다. 받은 응답은 web9.save 로 dart_out/raw/web9/fsc/ 에 원본 + .meta.json.

목록 API — 사이트 화면의 DataTables 가 부르는 것과 같은 방식(POST, 서버측 파라미터, 한 쪽 10건, 끝 쪽까지)
  · 회신사례 통합조회 (TotalReplyList.do) → POST /fsc_new/replyCase/selectReplyCaseTotalReplyList.do
      searchKeyword=<낱말> searchCondition=all(제목+내용) searchType=(전체) start=0,10,… length=10
      응답 {recordsTotal, data:[{dataIdx, pastreqType, title, replyRegDate}]} — 법령해석·비조치의견서·
      (2014이전)·현장건의 과제가 섞여 온다. 현장건의 과제는 대상이 아니어서 건수만 센다.
      ※ searchType 으로 거르면 recordsTotal 과 실제 행이 어긋나서(겸직·비조치: 1건 표시에 10행) 전체로 받는다.
  · 최근회신사례 (PastReplyList.do) → POST /fsc_new/replyCase/selectReplyCasePastReplyList.do
      같은 낱말 → {idx, gubun, category, title, number(일련번호), regDate(등록일)}. 통합조회 응답에는
      일련번호가 없어 이것으로 붙인다(원문 md 파일명 = 일련번호).
  · 상세 — 사이트 「URL 복사」 단추에 적힌 주소(GET, POST 로 열 때와 같은 응답임을 확인):
      LawreqDetail.do?stNo=11&muNo=117&muGpNo=75&lawreqIdx=…, OpinionDetail.do?…&opinionIdx=…
      2014 이전 건은 그 단추가 없어 화면 JS(goUrl)의 파라미터 그대로 PastReqDetail.do?…&pastreqIdx=…&actCd=R
AND 검색 — 「금융지주 낱말」(공백)·「금융지주+낱말」은 한 덩어리 문자열로 찾아 0건이다(AND 미지원).
  그래서 낱말로만 찾고, 제목·질의요지에 '금융지주'가 들어간 건을 related=Y 로 둔다. 공백 결합 검색도
  낱말마다 1쪽씩 불러 검색기록에 남긴다(점검용, 결과는 합치지 않는다).

산출물
  handoff/목록_법령해석.csv  (UTF-8 BOM) 같은 건은 한 행, search_terms 에 걸린 낱말 모두
  handoff/법령해석_원문/<일련번호>.md  related=Y 건 상세 페이지 본문 전문
  dart_out/risk9/법령해석_검색기록.csv  낱말·목록별 사이트 총건수 ↔ 받은 행 수 대조

옮기는 방식(글자는 바꾸지 않는다): 태그만 걷어내고 엔티티(&nbsp; 등)는 그 글자로 푼다.
  태그 없는 칸은 원래 줄바꿈 그대로(앞뒤의 서식 공백만 뗌). 태그 있는 칸은 HTML 서식 줄바꿈을 공백으로 보고
  <br> → 줄바꿈, <p>·<div> 등 문단 → 빈 줄, 칸 안의 표는 칸 사이 탭·행 사이 줄바꿈.
  answer_summary = 「회답」 칸의 첫 문단(태그 있는 칸은 첫 <p> 등 블록, 태그 없는 칸은 첫 줄). 사이트에
  회신 요지 칸은 없다. question = 「질의요지」 칸 전부(500자 넘으면 앞 500자 + note).
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
import time
import urllib.error
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))          # 저장소 루트(web9 의 상대 경로 기준)

from web9 import Web, save, now, RAW, WORK, HANDOFF       # noqa: E402

TASK = "fsc"
BASE = "https://better.fsc.go.kr"
TOTAL_PAGE = BASE + "/fsc_new/replyCase/TotalReplyList.do?stNo=11&muNo=117&muGpNo=88"
TOTAL_API = BASE + "/fsc_new/replyCase/selectReplyCaseTotalReplyList.do"
PAST_PAGE = BASE + "/fsc_new/replyCase/PastReplyList.do?stNo=11&muNo=171&muGpNo=75"
PAST_API = BASE + "/fsc_new/replyCase/selectReplyCasePastReplyList.do"
DETAIL = {
    "law": BASE + "/fsc_new/replyCase/LawreqDetail.do?stNo=11&muNo=117&muGpNo=75&lawreqIdx=%s",
    "opinion": BASE + "/fsc_new/replyCase/OpinionDetail.do?stNo=11&muNo=117&muGpNo=75&opinionIdx=%s",
    "pastreq": BASE + "/fsc_new/replyCase/PastReqDetail.do?stNo=11&muNo=117&pastreqIdx=%s&actCd=R",
}
HOLD = "금융지주"
WORDS = ["위험관리책임자", "겸직", "완전자회사", "위험관리기준", "업무위탁", "경영관리업무"]
PAGE = 10
OUT_CSV = os.path.join(HANDOFF, "목록_법령해석.csv")
OUT_MD = os.path.join(HANDOFF, "법령해석_원문")
LOG_CSV = os.path.join(WORK, "법령해석_검색기록.csv")
XHR = {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"}
REFRESH = "--refresh" in sys.argv


class Stop(Exception):
    """차단·로그인·캡차·접속 불가 — 우회하지 않고 멈춘다."""


# ── 요청 ─────────────────────────────────────────────────────────────────
W = None


def fetch(url, referer="", data=None, headers=None):
    """web9.Web.get + 접속 끊김 때만 30·60초 쉬고 다시. 401/403/429 는 바로 멈춘다."""
    global W
    if W is None:
        W = Web()
    last = None
    for k in range(3):
        try:
            fu, st, hd, b = W.get(url, referer=referer, data=data, headers=headers)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise Stop("HTTP %s (차단 의심) — %s" % (e.code, url))
            raise
        except Exception as e:                        # noqa: BLE001 — 프록시 터널 끊김 등
            last = e
            if k < 2:
                print("  … 접속 끊김(%s) — %d초 뒤 다시" % (type(e).__name__, 30 * (k + 1)), flush=True)
                time.sleep(30 * (k + 1))
            continue
        low = b[:20000].decode("utf-8", "replace").lower()
        if "/login/" in fu or "captcha" in low or "자동입력" in low:
            raise Stop("로그인/캡차 화면 — %s → %s" % (url, fu))
        return fu, st, hd, b
    raise Stop("접속 불가(재시도 9회) — %s: %r" % (url, last))


def cached(task, name, url, referer="", data=None, headers=None, extra=None):
    """원본이 있으면 그것을, 없으면 받아서 save. (본문 bytes, meta)"""
    p = os.path.join(RAW, task, name)
    if not REFRESH and os.path.exists(p) and os.path.exists(p + ".meta.json"):
        with open(p, "rb") as f, open(p + ".meta.json", encoding="utf-8") as g:
            return f.read(), json.load(g)
    fu, st, hd, b = fetch(url, referer, data, headers)
    meta = dict(출처URL=url, method="POST" if data is not None else "GET", 최종URL=fu, http_status=st,
                content_type=hd.get("Content-Type", ""), fetched_at=now())
    if data is not None:
        meta["요청본문"] = dict(data)
    meta.update(extra or {})
    _, meta = save(task, name, b, meta)
    return b, meta


def dt_params(cols, kw, extra, start):
    """DataTables 1.10 서버측 요청 파라미터 — 검색 단추를 누른 뒤와 같은 모양(search[value]=검색조건)."""
    d = [("draw", str(start // PAGE + 1))]
    for i, c in enumerate(cols):
        d += [("columns[%d][data]" % i, c), ("columns[%d][name]" % i, ""),
              ("columns[%d][searchable]" % i, "true"), ("columns[%d][orderable]" % i, "false"),
              ("columns[%d][search][value]" % i, ""), ("columns[%d][search][regex]" % i, "false")]
    d += [("order[0][column]", "0"), ("order[0][dir]", "asc"), ("start", str(start)), ("length", str(PAGE)),
          ("search[value]", "all"), ("search[regex]", "true"), ("searchKeyword", kw)]
    return d + extra


LISTS = {
    "통합조회": dict(page=TOTAL_PAGE, api=TOTAL_API, cols=["rownumber", "pastreqType", "title", "replyRegDate"],
                 extra=[("searchCondition", "all"), ("searchType", "")]),
    "최근회신사례": dict(page=PAST_PAGE, api=PAST_API,
                   cols=["rownumber", "gubun", "category", "title", "number", "regDate"],
                   extra=[("searchCondition", "all"), ("searchReplyRegDateStart", ""),
                          ("searchReplyRegDateEnd", ""), ("searchType", ""), ("searchCategory", ""),
                          ("searchLawType", "")]),
}


def search(lst, kw, tag, max_pages=None):
    """한 낱말을 끝 쪽까지. (recordsTotal 목록, 행 목록, 쪽 수, 마지막 meta)"""
    L = LISTS[lst]
    totals, rows, n, start, meta = [], [], 0, 0, {}
    while True:
        name = "%s_%s_p%02d.json" % (tag, re.sub(r"[^\w가-힣]+", "_", kw), start // PAGE + 1)
        try:
            body, meta = cached(TASK + "/search", name, L["api"], referer=L["page"],
                                data=dt_params(L["cols"], kw, L["extra"], start), headers=XHR,
                                extra=dict(목록=lst, 검색어=kw, start=start, length=PAGE))
        except urllib.error.HTTPError as e:
            raise Stop("목록 HTTP %s — %s %s 쪽 %d" % (e.code, lst, kw, start // PAGE + 1))
        try:
            j = json.loads(body.decode("utf-8"))
            tot, data = int(j["recordsTotal"]), j["data"]
        except Exception as e:                         # noqa: BLE001
            raise Stop("목록 응답이 JSON 이 아님(%s) — %s %s 쪽 %d: %r" % (e, lst, kw, start // PAGE + 1, body[:200]))
        totals.append(tot)
        rows += data
        n += 1
        start += PAGE
        if start >= tot or not data or (max_pages and n >= max_pages):
            return totals, rows, n, meta


# ── 상세 파싱 ─────────────────────────────────────────────────────────────
class Rows(HTMLParser):
    """sub-con 안의 바깥 표 행을 순서대로: ('head', 글) | ('row', [(th|td, 원HTML, attrs)…])."""

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src, self.starts = src, [0] + [m.end() for m in re.finditer("\n", src)]
        self.depth, self.items, self.cur, self.cell, self.head = 0, [], None, None, None

    def off(self):
        ln, col = self.getpos()
        return self.starts[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.depth += 1
            return
        if self.depth == 0 and (tag == "h3" or (tag == "div" and a.get("class") == "tit")):
            self.head = (tag, self.off() + len(self.get_starttag_text()))
        if self.depth != 1:
            return
        if tag == "tr":
            self.cur = []
        elif tag in ("th", "td") and self.cur is not None:
            self.cell = (tag, self.off() + len(self.get_starttag_text()), a)

    def handle_endtag(self, tag):
        if self.head and tag == self.head[0] and self.depth == 0:
            self.items.append(("head", text(self.src[self.head[1]:self.off()])))
            self.head = None
        if self.depth == 1:
            if tag in ("th", "td") and self.cell:
                k, s, a = self.cell
                self.cur.append((k, self.src[s:self.off()], a))
                self.cell = None
            elif tag == "tr" and self.cur is not None:
                self.items.append(("row", self.cur))
                self.cur = None
        if tag == "table":
            self.depth -= 1


TAG = re.compile(r"</?(?:p|br|span|div|font|b|strong|u|i|em|a|img|table|tbody|thead|tr|td|th|ul|ol|li|h\d|"
                 r"o:p|sup|sub|col|colgroup|caption|blockquote|pre|hr|center|strike|s|ins|del|mark|small|big)"
                 r"\b[^>]*>", re.I)


def text(h):
    """HTML 칸 → 글. 태그만 걷어내고 줄바꿈 유지(설명은 모듈 머리말)."""
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S).replace("\r\n", "\n").replace("\r", "\n")
    if not TAG.search(h):                                     # 태그 없는 칸: 원래 줄바꿈 그대로
        return html.unescape(h).strip(" \t\n")
    h = re.sub(r"[ \t]*\n[ \t\n]*", " ", h)                   # HTML 서식 줄바꿈 → 공백(브라우저와 같게)
    h = re.sub(r"<br\b[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"</?(?:p|div|h\d|ul|ol|table|blockquote|pre|center|hr)\b[^>]*>", "\n\n", h, flags=re.I)
    h = re.sub(r"</?(?:li|tr)\b[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", "\t", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)                             # 나머지 태그
    h = html.unescape(h)
    lines = [ln.strip(" ") for ln in h.split("\n")]           # 서식 공백(ASCII 공백)만 뗀다 — &nbsp; 는 남는다
    h = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return h.strip(" \t\n")


def paragraphs(h):
    """칸의 문단들 — 태그 있는 칸은 빈 줄로 나뉜 블록, 태그 없는 칸은 줄. 빈 문단은 뺀다."""
    t = text(h)
    parts = re.split(r"\n[ \t]*\n", t) if TAG.search(re.sub(r"<!--.*?-->", "", h, flags=re.S)) else t.split("\n")
    return [p for p in parts if p.strip(" \t\n\xa0　")]


def parse_detail(body):
    page = body.decode("utf-8", "replace")
    i = page.find('<div class="sub-con">')
    if i < 0:
        return None
    j = page.find("<script", i)
    seg = page[i:j if j > 0 else len(page)]
    p = Rows(seg)
    p.feed(seg)
    p.close()
    blocks, cur = [], None                                    # [(머리, [(label|None, 원HTML)…])]
    for kind, v in p.items:
        if kind == "head":
            cur = (v, [])
            blocks.append(cur)
            continue
        if cur is None:
            cur = ("", [])
            blocks.append(cur)
        ths = [c for c in v if c[0] == "th"]
        tds = [c for c in v if c[0] == "td"]
        if ths and tds:
            cur[1].append((text(ths[0][1]), tds[0][1]))
        elif tds and "subject" in (tds[0][2].get("class") or ""):
            cur[1].append((None, tds[0][1]))
    fields = {}
    for _, rows in blocks:
        for lab, raw in rows:
            fields.setdefault(lab or "#제목", []).append(raw)
    return dict(blocks=blocks, fields=fields)


# ── 본체 ─────────────────────────────────────────────────────────────────
def kind_code(t):
    t = t or ""
    if "2014" in t:
        return "pastreq"
    if t.startswith("법령해석"):
        return "law"
    if t.startswith("비조치"):
        return "opinion"
    return None                                                # 현장건의 과제 등


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(OUT_MD, exist_ok=True)
    log, items, stop = [], {}, None                           # items[(code, idx)] = dict

    def logrow(**k):
        base = dict.fromkeys(["검색어", "목록", "검색조건", "사이트_총건수", "받은_쪽수", "받은_행수", "고유_건수",
                              "일치", "법령해석", "비조치의견서", "법령해석(2014이전)", "비조치의견서(2014이전)",
                              "현장건의_과제(제외)", "기타", "요청URL", "수집시각", "비고"], "")
        base.update(k)
        log.append(base)

    try:
        for lst in LISTS:                                      # 목록 화면을 먼저 열어 세션·Referer 를 화면과 같게
            cached(TASK, "%s_화면.html" % lst, LISTS[lst]["page"])
        # 1) AND 점검 — 공백 결합 1쪽씩
        for w in WORDS:
            q = "%s %s" % (HOLD, w)
            tots, rows, n, meta = search("통합조회", q, "AND점검_통합", max_pages=1)
            logrow(검색어=q, 목록="통합조회(AND 점검)", 검색조건="제목+내용", 사이트_총건수=tots[0], 받은_쪽수=n,
                   받은_행수=len(rows), 요청URL=TOTAL_API, 수집시각=meta.get("fetched_at", ""),
                   비고="공백 결합은 한 덩어리 문자열 검색 — 결과는 합치지 않음(점검용)")
        # 2) 낱말별 끝 쪽까지
        for w in WORDS:
            for lst, tag in (("통합조회", "통합"), ("최근회신사례", "최근")):
                tots, rows, n, meta = search(lst, w, tag)
                cnt = dict.fromkeys(["법령해석", "비조치의견서", "법령해석(2014이전)", "비조치의견서(2014이전)",
                                     "현장건의_과제(제외)", "기타"], 0)
                keys = set()
                for r in rows:
                    if lst == "통합조회":
                        typ, idx = html.unescape(r.get("pastreqType") or ""), r.get("dataIdx")
                    else:
                        typ, idx = html.unescape(r.get("gubun") or ""), r.get("idx")
                    code = kind_code(typ) if lst == "통합조회" else ("law" if typ == "법령해석" else "opinion")
                    if typ in cnt:
                        cnt[typ] += 1
                    elif typ == "현장건의 과제":
                        cnt["현장건의_과제(제외)"] += 1
                    else:
                        cnt["기타"] += 1
                    keys.add((typ, idx))
                    if code is None:
                        continue
                    it = items.setdefault((code, str(idx)), dict(code=code, idx=str(idx), terms=[], lists=set()))
                    if w not in it["terms"]:
                        it["terms"].append(w)
                    it["lists"].add(lst)
                    if lst == "통합조회":
                        it.setdefault("kind", typ)
                        it.setdefault("list_title", html.unescape(r.get("title") or ""))
                        it.setdefault("list_date", r.get("replyRegDate") or "")
                    else:
                        it.setdefault("serial", (r.get("number") or "").strip())
                        it.setdefault("category", r.get("category") or "")
                        it.setdefault("regDate", r.get("regDate") or "")
                        it.setdefault("past_title", html.unescape(r.get("title") or ""))
                        it.setdefault("past_kind", typ)
                same = len(set(tots)) == 1
                ok = same and len(rows) == tots[0] and len(keys) == tots[0]
                note = []
                if not same:
                    note.append("쪽마다 총건수 다름 %s" % tots)
                if len(keys) != len(rows):
                    note.append("쪽 사이 중복 %d행" % (len(rows) - len(keys)))
                logrow(검색어=w, 목록=lst, 검색조건="제목+내용", 사이트_총건수=tots[0], 받은_쪽수=n,
                       받은_행수=len(rows), 고유_건수=len(keys), 일치="Y" if ok else "N",
                       요청URL=LISTS[lst]["api"], 수집시각=meta.get("fetched_at", ""), 비고="; ".join(note),
                       **cnt)
                print("%-8s %-6s 총 %4d건 · %d쪽 · 받은 %d행(고유 %d)%s" % (w, lst, tots[0], n, len(rows), len(keys),
                                                                 "" if ok else " ← 불일치"), flush=True)
        # 3) 상세
        todo = sorted(items.values(), key=lambda x: (x["code"], int(x["idx"])))
        print("상세 %d건 받기" % len(todo), flush=True)
        for k, it in enumerate(todo, 1):
            url = DETAIL[it["code"]] % it["idx"]
            it["url"] = url
            name = "%s_%s.html" % ({"law": "법령해석", "opinion": "비조치의견서", "pastreq": "2014이전"}[it["code"]],
                                   it["idx"])
            try:
                body, meta = cached(TASK + "/detail", name, url,
                                    referer=TOTAL_PAGE, extra=dict(구분=it.get("kind", it.get("past_kind", "")),
                                                                   검색어=it["terms"]))
            except urllib.error.HTTPError as e:
                it["err"] = "상세 HTTP %s" % e.code
                continue
            it["meta"], it["raw"] = meta, os.path.join(RAW, TASK, "detail", name)
            it["detail"] = parse_detail(body)
            if k % 25 == 0 or k == len(todo):
                print("  상세 %d/%d" % (k, len(todo)), flush=True)
    except Stop as e:
        stop = str(e)
        print("멈춤:", stop, flush=True)
        logrow(검색어="(중단)", 비고=stop, 수집시각=now())

    rows_out, md_n, serials = [], 0, {}
    for it in items.values():
        note = []
        d = it.get("detail")
        f = d["fields"] if d else {}
        title = text(f["#제목"][0]) if f.get("#제목") else it.get("list_title") or it.get("past_title", "")
        lt = it.get("list_title") or it.get("past_title", "")
        if d and lt and lt.strip() != title.strip():
            note.append("목록 제목: %s" % lt)
        kind = it.get("kind") or it.get("past_kind", "")
        if not it.get("kind"):
            note.append("통합조회 목록에 없음(최근회신사례에서만 걸림) — kind 는 최근회신사례 구분")
        elif it["code"] != "pastreq" and "최근회신사례" not in it["lists"]:
            note.append("최근회신사례 목록에 없음")
        if it["code"] == "pastreq" and f.get("타입"):
            t2 = text(f["타입"][0])
            if t2 and t2 not in kind:
                note.append("상세 페이지 타입: %s" % t2)
        serial = it.get("serial", "")
        if not serial and f.get("일련번호"):
            serial = text(f["일련번호"][0])
        # 회신일 — 상세의 「회신일」 칸, 없으면 통합조회 목록의 회신일 열
        rd = text(f["회신일"][0]) if f.get("회신일") else ""
        if not rd and it.get("list_date"):
            rd = it["list_date"]
            if d:
                note.append("회신일: 상세에 회신일 칸 없음 — 통합조회 목록의 회신일 열 값")
        elif rd and it.get("list_date") and rd != it["list_date"]:
            note.append("통합조회 목록 회신일: %s" % it["list_date"])
        if f.get("회신일") and len(f["회신일"]) > 1:
            note.append("회신 %d개 — 첫 회신 기준" % len(f["회신일"]))
        q_full = text(f["질의요지"][0]) if f.get("질의요지") else ""
        question = q_full
        if len(q_full) > 500:
            question = q_full[:500]
            note.append("question: 앞 500자(전체 %d자)" % len(q_full))
        ans = ""
        if f.get("회답"):
            ps = paragraphs(f["회답"][0])
            ans = ps[0].strip(" \t\n") if ps else ""
            if not ans:
                note.append("회답 칸이 비어 있음")
        if d and not f.get("질의요지"):
            note.append("상세에 질의요지 칸 없음")
        if d and not f.get("회답"):
            note.append("상세에 회답 칸 없음")
        if not d:
            note.append(it.get("err") or ("상세 미수집: %s" % stop if stop else "상세 페이지 구조를 못 읽음"))
        related = "Y" if (HOLD in title or HOLD in lt or HOLD in q_full) else "N"
        if related == "N" and d:
            elsewhere = [lab for lab, raws in f.items() if lab not in ("#제목", "질의요지")
                         and any(HOLD in text(r) for r in raws)]
            if elsewhere:
                note.append("'금융지주'는 제목·질의요지 밖에만 있음(%s)" % "·".join(x.lstrip("#") for x in elsewhere))
        body_md = ""
        if related == "Y" and d:
            fn = serial or "%s_idx%s" % (it["code"], it["idx"])
            if not serial:
                note.append("일련번호 없음 — 파일명은 사이트 내부번호")
            if fn in serials and serials[fn] != (it["code"], it["idx"]):
                fn = "%s_%s%s" % (fn, it["code"], it["idx"])
                note.append("일련번호가 다른 건과 겹쳐 파일명에 구분 덧붙임")
            serials[fn] = (it["code"], it["idx"])
            body_md = os.path.join(OUT_MD, fn + ".md")
            write_md(body_md, it, title, rd, serial, kind, d)
            md_n += 1
        rows_out.append(dict(title=title, reply_date=rd, kind=kind, question=question, answer_summary=ans,
                             url=it.get("url", ""), search_terms=", ".join(it["terms"]), related=related,
                             body_md=body_md, collected_at=(it.get("meta") or {}).get("fetched_at", ""),
                             note="; ".join(note), _serial=serial))
    rows_out.sort(key=lambda r: (r["related"] != "Y", [-ord(c) for c in r["reply_date"]], r["title"]))
    cols = ["title", "reply_date", "kind", "question", "answer_summary", "url", "search_terms", "related",
            "body_md", "collected_at", "note"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as fo:
        wr = csv.DictWriter(fo, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows_out)
    ny = sum(r["related"] == "Y" for r in rows_out)
    logrow(검색어="(합계·중복 제거)", 목록="통합조회+최근회신사례", 고유_건수=len(rows_out), 수집시각=now(),
           비고="법령해석·비조치의견서 %d건(현장건의 과제 제외) · related=Y %d건 · 원문 md %d개 · 상세 실패 %d건%s"
              % (len(rows_out), ny, md_n, sum(1 for it in items.values() if not it.get("detail")),
                 (" · 중단: " + stop) if stop else ""))
    with open(LOG_CSV, "w", encoding="utf-8-sig", newline="") as fo:
        wr = csv.DictWriter(fo, fieldnames=list(log[0].keys()))
        wr.writeheader()
        wr.writerows(log)
    print("목록 %d행(related=Y %d) → %s · 원문 md %d개 → %s/ · 검색기록 → %s"
          % (len(rows_out), ny, OUT_CSV, md_n, OUT_MD, LOG_CSV))
    return 2 if stop else 0


LONG = {"질의요지", "회답", "이유", "법령해석요청의 원인이 되는 사실관계", "해석대상 법령 조문 및 관련법령"}


def write_md(path, it, title, rd, serial, kind, d):
    m = it["meta"]
    out = ["# %s" % title, "",
           "- 제목: %s" % title,
           "- 회신일: %s" % rd,
           "- URL: %s" % it["url"],
           "- 수집일: %s" % m.get("fetched_at", ""),
           "- 구분(통합조회 원값): %s · 일련번호: %s%s" % (kind, serial or "(없음)",
                                                 (" · 분야: %s" % it["category"]) if it.get("category") else ""),
           "- 찾은 검색어: %s" % ", ".join(it["terms"]),
           "- 원본: %s (HTTP %s · sha256 %s)" % (it["raw"], m.get("http_status", ""), m.get("sha256", "")),
           "- 옮긴 방식: 상세 페이지 본문 표를 순서대로, 글자는 바꾸지 않고 HTML 태그만 걷어냈다"
           "(<br> 은 줄바꿈, <p> 문단 사이는 빈 줄, 태그 없는 칸은 원래 줄바꿈 그대로, &nbsp; 등 엔티티는 그 글자로).",
           "", "---", ""]
    for head, rows in d["blocks"]:
        if head:
            out += ["## %s" % head, ""]
        for lab, raw in rows:
            t = text(raw)
            if lab is None:
                out += ["### %s" % t, ""]
            elif lab in LONG or "\n" in t or len(t) > 100:
                out += ["### %s" % lab, "", t, ""]
            else:
                out += ["- %s: %s" % (lab, re.sub(r"\s*\n\s*", " / ", t) if lab == "첨부파일" else t)]
        if out[-1] != "":
            out.append("")
    with open(path, "w", encoding="utf-8") as fo:
        fo.write("\n".join(out).rstrip() + "\n")


if __name__ == "__main__":
    sys.exit(main())
