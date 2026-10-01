# -*- coding: utf-8 -*-
"""10차 6-6(가) — 금융위 「금융규제·법령해석포털」(better.fsc.go.kr) 법령해석·비조치의견서 중 대주주 거래
(보험업법 §111·§106, 금융지주회사법 §34·§36) 관련 회신 수집.

    python3 scripts/dart/web10_fsc.py             # robots·이용약관 → 검색 → 상세 → 목록 CSV·원문 md·우선 CSV
    python3 scripts/dart/web10_fsc.py --probe     # 낱말마다 두 목록 1쪽만(사이트 총건수 보기) — 산출물 안 씀
    python3 scripts/dart/web10_fsc.py --offline   # 받지 않고 저장해 둔 원본만으로 산출물
    python3 scripts/dart/web10_fsc.py --refresh   # 저장해 둔 원본(10차·9차)을 쓰지 않고 다시 받는다

요청 방식은 9차 scripts/dart/web9_fsc.py(고치지 않음)와 같다 — 그 모듈의 목록 API 정의(LISTS·dt_params)·상세 URL
(DETAIL)·상세 파싱(parse_detail·text·paragraphs)을 import 해서 그대로 쓰고, 요청·저장만 10차 공용 모듈(web10)로 한다.
  · 요청은 web10.Web(=web9.Web: UA 고정·1.2초 간격·3회 재시도)로 하나씩, 요청 시작 사이 4초 이상(GAP).
  · 접속 자체가 끊기면 30·60초 쉬고 다시(기록: dart_out/raw/web10/fsc/접속끊김.csv). 그래도 안 되거나
    401·403·429·로그인 화면·캡차가 나오면 우회하지 않고 멈춘 뒤 사유를 검색기록에 남긴다.
  · robots.txt(web10.Robots, RFC 9309)가 막는 URL 은 요청하지 않는다. 이용약관·저작권정책·사이트 이용안내 화면을
    (robots 허용 시) 받아 자동 수집 금지 문구가 있는지 보고, 있으면 검색·상세를 받지 않는다.
  · 원본은 web10.save 로 dart_out/raw/web10/fsc/ 에 원본 + .meta.json. 이미 받은 원본은 다시 받지 않는다.
    상세 페이지는 9차에 받아 둔 같은 URL 의 원본(dart_out/raw/web9/fsc/detail/)이 있으면 그것을 읽어 쓰고
    note·md 머리에 그 경로를 적는다(같은 요청).
목록 API 2종(통합조회·최근회신사례)의 합집합을 대상으로 한다(9차 실측: 같은 낱말에도 걸리는 건이 다름).
사이트는 AND 검색이 안 된다(공백 낱말은 한 덩어리 문자열로 찾음) — 검색어를 그대로 한 번 찾고, 0건이거나
좁으면 보조 낱말로 찾는다. 보조 낱말 가운데 너무 넓은 것(사이트 총건수가 많아 대주주 거래와 무관한 건이 대부분인
낱말)은 1쪽만 받아 총건수를 기록하고(점검), 합집합에는 넣지 않는다 — 어느 낱말을 어떻게 썼는지 검색기록에.

관련(related) 판정 — 제목(상세·목록)·질의요지·회답 칸 글에서 낱말이 그대로 나올 때만(추정 없음):
  · 보험업법 §111           「보험업법」 바로 뒤(따옴표·괄호·공백만 사이)에 「제111조」
  · 보험업법 §106①5호/6호  같은 꼴로 「보험업법 제106조(제1항)제5호/제6호」(「및 제6호」처럼 이어진 호 포함).
                            호가 없거나 5·6호가 아니면 「보험업법 §106」(다른 호는 note)
  · 금융지주회사법 §34·§36  「금융지주회사법」 바로 뒤에 「제34조」·「제36조」
  · 공정거래법 계열회사      한 문단 안에 「계열회사」와 공정거래법 이름(공정거래법·독점규제 및 공정거래에 관한 법률)
  · 지배구조법 특수관계인(시행령 §3)  한 문단 안에 「특수관계인」과 지배구조법 이름(지배구조법·금융사지배구조법·
                            금융회사의 지배구조에 관한 법률)
  법률명 없이 「법 제111조」처럼만 나오거나 이유 칸에만 나오는 것은 related 에 넣지 않고 note 에 구절을 적는다.
  related_9차식 = 9차와 같은 규칙(제목·목록 제목·질의요지에 '금융지주'가 있으면 Y, 아니면 N).

산출물
  handoff/원문_10차/목록_법령해석_대주주거래.csv   (UTF-8 BOM) 같은 건은 한 행, search_terms 에 걸린 낱말 모두
  handoff/원문_10차/법령해석_대주주거래/<일련번호>.md   related 가 있는 건의 상세 페이지 본문 전문
  dart_out/risk10/법령해석_대주주거래_검색기록.csv  낱말·목록별 사이트 총건수 ↔ 받은 행 수, robots·약관 점검
  dart_out/risk10/법령해석_대주주거래_우선.csv      우선 볼 질문 3개 ↔ 회신(아래 PRIORITY, 회답 문장은 원문
                                                    그대로 있는지 스크립트가 대조하고, 없으면 멈춘다)
옮기는 방식은 9차와 같다(web9_fsc.text: 태그만 걷어내고 엔티티는 그 글자로, 글자는 바꾸지 않음).
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))          # 저장소 루트(web10 의 상대 경로 기준)

from web10 import Web, save, Robots, now, write_csv, OUT, WORK, RAW   # noqa: E402
import web9_fsc as F9                                               # noqa: E402 — 고치지 않고 정의만 가져다 씀
from web9 import RAW as RAW9                                        # noqa: E402

TASK = "fsc"
BASE = F9.BASE
LISTS, DETAIL, PAGE, XHR = F9.LISTS, F9.DETAIL, F9.PAGE, F9.XHR
TOTAL_PAGE = F9.TOTAL_PAGE
POLICY = {                                                          # 화면 꼬리(footer)의 링크 그대로
    "사이트 이용안내": BASE + "/fsc_new/page/selectPage.do?stNo=11&muNo=198&muGpNo=195",
    "저작권정책": BASE + "/fsc_new/page/selectPage.do?stNo=11&muNo=200&muGpNo=195",
    "이메일무단수집거부": BASE + "/fsc_new/page/selectPage.do?stNo=11&muNo=201&muGpNo=195",
}

# 검색어 — 사용자 지정(우선순위 순). 「주」는 끝 쪽까지 받는다.
MAIN = ["보험업법 제111조", "대주주와의 거래", "금융지주회사 자회사 보험회사", "대주주 특수관계인",
        "외국 계열회사", "금융지주회사법 제34조"]
# 보조 낱말 — 주 검색어가 0건이거나 좁을 때(--probe 결과를 보고 정함, 이유는 검색기록 비고).
#   AUX  : 끝 쪽까지 받아 합집합에 넣는다.
#   PROBE: 너무 넓어 1쪽만 받아 총건수만 기록(합집합에 넣지 않음).
AUX = {}
PROBE = {}
CANDIDATES = ["제111조", "대주주와의 거래등", "제106조", "제34조", "제36조", "계열회사", "특수관계인"]  # 사용자 예시

OUT_CSV = os.path.join(OUT, "목록_법령해석_대주주거래.csv")
OUT_MD = os.path.join(OUT, "법령해석_대주주거래")
LOG_CSV = os.path.join(WORK, "법령해석_대주주거래_검색기록.csv")
PRI_CSV = os.path.join(WORK, "법령해석_대주주거래_우선.csv")
NONE = "문서에 없음"
REFRESH = "--refresh" in sys.argv
OFFLINE = "--offline" in sys.argv
PROBE_ONLY = "--probe" in sys.argv


class Stop(Exception):
    """차단·로그인·캡차·robots 차단·접속 불가 — 우회하지 않고 멈춘다."""


# ── 요청 ─────────────────────────────────────────────────────────────────
W = None
R = None                                                     # Robots(better.fsc.go.kr)
GAP = 4.0                                                    # 9차와 같은 간격(요청 시작 사이 최소 초)
DROPS = []
DROP_LOG = os.path.join(RAW, TASK, "접속끊김.csv")
FETCHED, REUSED9 = [], []


def web():
    global W
    if W is None:
        W = Web()
    return W


def fetch(url, referer="", data=None, headers=None):
    """web10.Web.get + 접속 끊김 때만 30·60초 쉬고 다시. robots 차단·401/403/429·로그인·캡차는 바로 멈춘다."""
    if OFFLINE:
        raise Stop("--offline: 저장된 원본 없음 — %s" % url)
    if R is None or not R.allowed(url):
        raise Stop("robots.txt 가 허용하지 않음(%s) — 요청 안 함: %s" % (R.status if R else "미확인", url))
    w = web()
    last = None
    for k in range(3):
        wait = GAP - (time.time() - w.last)
        if wait > 0:
            time.sleep(wait)
        try:
            fu, st, hd, b = w.get(url, referer=referer, data=data, headers=headers)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise Stop("HTTP %s (차단 의심) — %s" % (e.code, url))
            raise
        except Exception as e:                        # noqa: BLE001 — 프록시 터널 끊김 등
            last = e
            DROPS.append((now(), url, "%s: %s" % (type(e).__name__, e)))
            os.makedirs(os.path.dirname(DROP_LOG), exist_ok=True)
            new = not os.path.exists(DROP_LOG)
            with open(DROP_LOG, "a", encoding="utf-8-sig" if new else "utf-8", newline="") as fo:
                wr = csv.writer(fo)
                if new:
                    wr.writerow(["시각", "URL", "오류(web10.Web.get 3회 재시도 뒤)"])
                wr.writerow(DROPS[-1])
            if k < 2:
                print("  … 접속 끊김(%s) — %d초 뒤 다시" % (type(e).__name__, 30 * (k + 1)), flush=True)
                time.sleep(30 * (k + 1))
            continue
        low = b[:20000].decode("utf-8", "replace").lower()
        if "/login/" in fu or "captcha" in low or "자동입력" in low:
            raise Stop("로그인/캡차 화면 — %s → %s" % (url, fu))
        return fu, st, hd, b
    raise Stop("접속 불가(재시도 9회) — %s: %r" % (url, last))


def cached(task, name, url, referer="", data=None, headers=None, extra=None, raw9=None):
    """10차 원본 → (있으면) 9차 같은 요청 원본 → 받아서 save. (본문 bytes, meta, 원본 경로)"""
    p = os.path.join(RAW, task, name)
    if not REFRESH and os.path.exists(p) and os.path.exists(p + ".meta.json"):
        with open(p, "rb") as f, open(p + ".meta.json", encoding="utf-8") as g:
            return f.read(), json.load(g), p
    if raw9 and not REFRESH and os.path.exists(raw9) and os.path.exists(raw9 + ".meta.json"):
        with open(raw9 + ".meta.json", encoding="utf-8") as g:
            meta = json.load(g)
        if meta.get("출처URL") == url:                      # 같은 요청(같은 URL·GET)일 때만
            meta = dict(meta, 재사용="9차 원본(같은 URL·GET) — %s" % raw9)
            REUSED9.append(raw9)
            with open(raw9, "rb") as f:
                return f.read(), meta, raw9
    fu, st, hd, b = fetch(url, referer, data, headers)
    meta = dict(출처URL=url, method="POST" if data is not None else "GET", 최종URL=fu, http_status=st,
                content_type=hd.get("Content-Type", ""), fetched_at=now())
    if data is not None:
        meta["요청본문"] = dict(data)
    meta.update(extra or {})
    path, meta = save(task, name, b, meta)
    FETCHED.append(name)
    return b, meta, path


def search(lst, kw, tag, max_pages=None):
    """한 낱말을 끝 쪽까지(또는 max_pages 쪽). (recordsTotal 목록, 행 목록, 쪽 수, 마지막 meta)"""
    L = LISTS[lst]
    totals, rows, n, start, meta = [], [], 0, 0, {}
    while True:
        name = "%s_%s_p%02d.json" % (tag, re.sub(r"[^\w가-힣]+", "_", kw), start // PAGE + 1)
        try:
            body, meta, _ = cached(TASK + "/search", name, L["api"], referer=L["page"],
                                   data=F9.dt_params(L["cols"], kw, L["extra"], start), headers=XHR,
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


# ── 이용약관 점검 ──────────────────────────────────────────────────────────
BAN = re.compile(r"(자동|프로그램|크롤|스크래|스크랩|로봇|봇|기계적).{0,60}(수집|복제|추출|접근)|"
                 r"(수집|복제|추출).{0,60}(자동|프로그램|크롤|스크래|스크랩|로봇|기계적)")
EMAIL = re.compile(r"이메일|전자우편|e-?mail", re.I)


def policy_check(logrow):
    """사이트 이용안내·저작권정책·이메일무단수집거부 화면 — 자동 수집 금지 문구(이메일 주소 수집 금지는 제외)."""
    ban = []
    for nm, url in POLICY.items():
        body, meta, path = cached(TASK + "/policy", "%s.html" % nm.replace(" ", "_"), url, referer=TOTAL_PAGE)
        page = body.decode("utf-8", "replace")
        i = page.find('<div class="sub-con">')
        j = page.find("<footer", i if i >= 0 else 0)
        seg = page[i if i >= 0 else 0:j if j > 0 else len(page)]
        seg = re.sub(r"<script\b.*?</script>", "", seg, flags=re.S | re.I)
        t = F9.text(seg)
        sents = [s.strip() for s in re.split(r"(?<=[.다])\s+|\n", t) if s.strip()]
        hit = [s for s in sents if BAN.search(s)]
        hit_ban = [s for s in hit if not EMAIL.search(s)]
        hit_mail = [s for s in hit if EMAIL.search(s)]
        kw = [s for s in sents if re.search(r"무단|수집|크롤|로봇", s)]
        logrow(검색어="(이용약관 점검) %s" % nm, 목록="", 요청URL=url, 수집시각=meta.get("fetched_at", ""),
               비고="글 %d자 · 자동수집 금지 문구 %d개%s · 이메일 주소 수집 금지 문구 %d개(해당 아님) · '무단·수집·크롤·"
                    "로봇' 든 문장 원문: %s · 원본 %s"
                    % (len(t), len(hit_ban), (" — " + " / ".join(hit_ban)) if hit_ban else "", len(hit_mail),
                       " / ".join(kw[:8]) or "(없음)", path))
        print("약관 %-10s %6d자 · 자동수집 금지 %d · 이메일 %d" % (nm, len(t), len(hit_ban), len(hit_mail)), flush=True)
        ban += [(nm, s) for s in hit_ban]
    return ban


# ── 관련 조문 판정 ─────────────────────────────────────────────────────────
GAP_RE = r"[」』\"”’'\s]*"
HO = r"제\s*(\d+)\s*호((?:\s*(?:및|·|ㆍ|,|、|와|과|또는)\s*(?:같은\s*항\s*)?제\s*\d+\s*호)*)"
P111 = re.compile(r"보험업법" + GAP_RE + r"(?:§\s*111|제\s*111\s*조)(?!\s*의\s*\d)")
P106 = re.compile(r"보험업법" + GAP_RE + r"(?:§\s*106|제\s*106\s*조)(?!\s*의\s*\d)"
                  r"(?:\s*(?:제\s*1\s*항|①)\s*(?:" + HO + r")?)?")
P34 = re.compile(r"금융지주회사법" + GAP_RE + r"(?:§\s*34|제\s*34\s*조)(?!\s*의\s*\d)")
P36 = re.compile(r"금융지주회사법" + GAP_RE + r"(?:§\s*36|제\s*36\s*조)(?!\s*의\s*\d)")
FTC = re.compile(r"공정거래법|독점규제\s*및\s*공정거래에\s*관한\s*법률")
GOV = re.compile(r"지배구조법|금융회사의\s*지배구조에\s*관한\s*법률")
LOOSE = re.compile(r"(제\s*(?:111|106|34|36)\s*조)(?!\s*의\s*\d)")
LABELS = ["보험업법 §111", "보험업법 §106①5호", "보험업법 §106①6호", "보험업법 §106", "금융지주회사법 §34",
          "금융지주회사법 §36", "공정거래법 계열회사", "지배구조법 특수관계인(시행령 §3)"]


def related_of(texts):
    """texts: [(칸 이름, 글, 문단들)] → (관련 조문 집합, note 조각들)."""
    found, notes = set(), []
    for lab, t, paras in texts:
        flat = re.sub(r"\s+", " ", t)
        if P111.search(flat):
            found.add("보험업법 §111")
        for m in P106.finditer(flat):
            hos = []
            if m.group(1):
                hos = [m.group(1)] + re.findall(r"제\s*(\d+)\s*호", m.group(2) or "")
            five_six = [h for h in hos if h in ("5", "6")]
            for h in five_six:
                found.add("보험업법 §106①%s호" % h)
            if not five_six:
                found.add("보험업법 §106")
                if hos:
                    notes.append("%s: 보험업법 §106 의 %s호(5·6호 아님) — '%s'" % (lab, "·".join(hos), m.group(0)))
        if P34.search(flat):
            found.add("금융지주회사법 §34")
        if P36.search(flat):
            found.add("금융지주회사법 §36")
        for p in paras:
            pf = re.sub(r"\s+", " ", p)
            if "계열회사" in pf and FTC.search(pf):
                found.add("공정거래법 계열회사")
            if "특수관계인" in pf and GOV.search(pf):
                found.add("지배구조법 특수관계인(시행령 §3)")
    return found, notes


def loose_notes(texts, found):
    """법률명 바로 뒤가 아닌 「제111조·제106조·제34조·제36조」 구절(앞뒤 20자) — related 아님, note 용."""
    out = []
    strict = [P111, P106, P34, P36]
    for lab, t, _ in texts:
        flat = re.sub(r"\s+", " ", t)
        spans = [m.span() for p in strict for m in p.finditer(flat)]
        for m in LOOSE.finditer(flat):
            if any(a <= m.start() < b for a, b in spans):
                continue
            out.append("%s: 「%s」" % (lab, flat[max(0, m.start() - 20):m.end() + 12]))
    return out


# ── 본체 ─────────────────────────────────────────────────────────────────
def main():
    global R
    os.makedirs(WORK, exist_ok=True)
    log, items, stop = [], {}, None

    def logrow(**k):
        base = dict.fromkeys(["검색어", "구분", "목록", "검색조건", "사이트_총건수", "받은_쪽수", "받은_행수", "고유_건수",
                              "일치", "법령해석", "비조치의견서", "법령해석(2014이전)", "비조치의견서(2014이전)",
                              "현장건의_과제(제외)", "기타", "요청URL", "수집시각", "비고"], "")
        base.update(k)
        log.append(base)

    try:
        # 0) robots.txt · 이용약관
        if OFFLINE:
            rp = os.path.join(RAW, TASK, "robots_better.fsc.go.kr.txt")
            R = type("R", (), {})()
            R.status, R.note = ("OK(저장본)" if os.path.exists(rp) else "확인 불가"), "--offline"
            R.allowed = lambda u: False
        else:
            for k in range(3):                                 # 접속 끊김(확인 불가)만 30·60초 쉬고 다시 — 9차와 같은 규칙
                wait = GAP - (time.time() - web().last)
                if wait > 0:
                    time.sleep(wait)
                R = Robots(web(), BASE, TASK)
                if R.status != "확인 불가":
                    break
                DROPS.append((now(), BASE + "/robots.txt", R.note))
                os.makedirs(os.path.dirname(DROP_LOG), exist_ok=True)
                new = not os.path.exists(DROP_LOG)
                with open(DROP_LOG, "a", encoding="utf-8-sig" if new else "utf-8", newline="") as fo:
                    wr = csv.writer(fo)
                    if new:
                        wr.writerow(["시각", "URL", "오류(web10.Web.get 3회 재시도 뒤)"])
                    wr.writerow(DROPS[-1])
                if k < 2:
                    print("  … robots.txt 접속 끊김 — %d초 뒤 다시" % (30 * (k + 1)), flush=True)
                    time.sleep(30 * (k + 1))
        rb = ""
        rpath = os.path.join(RAW, TASK, "robots_better.fsc.go.kr.txt")
        if os.path.exists(rpath):
            rb = open(rpath, encoding="utf-8", errors="replace").read()
        logrow(검색어="(robots.txt 점검)", 목록="", 요청URL=BASE + "/robots.txt", 수집시각=now(),
               비고="상태 %s · %s · 원문: %s · 목록 API 허용 %s · 상세 허용 %s"
                    % (R.status, R.note or "규칙대로", re.sub(r"\s+", " ", rb)[:400] or "(저장본 없음)",
                       R.allowed(LISTS["통합조회"]["api"]) if not OFFLINE else "(offline)",
                       R.allowed(DETAIL["law"] % 1) if not OFFLINE else "(offline)"))
        print("robots:", R.status, R.note, flush=True)
        if not OFFLINE:
            for u in [LISTS[k]["page"] for k in LISTS] + [LISTS[k]["api"] for k in LISTS] + \
                     [DETAIL[k] % 1 for k in DETAIL] + list(POLICY.values()):
                if not R.allowed(u):
                    raise Stop("robots.txt 가 막음 — %s" % u)
        ban = policy_check(logrow)
        if ban:
            raise Stop("이용약관·저작권정책에 자동 수집 금지 문구 — %s" % " / ".join("%s: %s" % x for x in ban))
        for lst in LISTS:                                      # 목록 화면을 먼저 열어 세션·Referer 를 화면과 같게
            cached(TASK, "%s_화면.html" % lst, LISTS[lst]["page"])

        if PROBE_ONLY:
            for w in MAIN + [x for x in CANDIDATES if x not in AUX and x not in PROBE] + list(AUX) + list(PROBE):
                for lst, tag in (("통합조회", "통합"), ("최근회신사례", "최근")):
                    tots, rows, n, meta = search(lst, w, tag, max_pages=1)
                    print("PROBE %-16s %-6s 총 %4d건" % (w, lst, tots[0]), flush=True)
                    logrow(검색어=w, 구분="probe", 목록=lst, 사이트_총건수=tots[0], 받은_쪽수=1, 받은_행수=len(rows),
                           요청URL=LISTS[lst]["api"], 수집시각=meta.get("fetched_at", ""))

        words = [(w, "주", None) for w in MAIN] + [(w, "보조", why) for w, why in AUX.items()] + \
                [(w, "점검(1쪽)", why) for w, why in PROBE.items()]
        for w, gubun, why in words:
            for lst, tag in (("통합조회", "통합"), ("최근회신사례", "최근")):
                full = gubun != "점검(1쪽)"
                tots, rows, n, meta = search(lst, w, tag, max_pages=None if full else 1)
                cnt = dict.fromkeys(["법령해석", "비조치의견서", "법령해석(2014이전)", "비조치의견서(2014이전)",
                                     "현장건의_과제(제외)", "기타"], 0)
                keys = set()
                for r in rows:
                    if lst == "통합조회":
                        typ, idx = html.unescape(r.get("pastreqType") or ""), r.get("dataIdx")
                    else:
                        typ, idx = html.unescape(r.get("gubun") or ""), r.get("idx")
                    code = F9.kind_code(typ) if lst == "통합조회" else ("law" if typ == "법령해석" else "opinion")
                    if typ in cnt:
                        cnt[typ] += 1
                    elif typ == "현장건의 과제":
                        cnt["현장건의_과제(제외)"] += 1
                    else:
                        cnt["기타"] += 1
                    keys.add((typ, idx))
                    if code is None or not full:
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
                note = [] if not why else [why]
                if not full:
                    note.append("1쪽만 받음(총건수 확인용) — 합집합에 넣지 않음")
                if not same:
                    note.append("쪽마다 총건수 다름 %s" % tots)
                if len(keys) != len(rows):
                    note.append("쪽 사이 중복 %d행" % (len(rows) - len(keys)))
                logrow(검색어=w, 구분=gubun, 목록=lst, 검색조건="제목+내용", 사이트_총건수=tots[0], 받은_쪽수=n,
                       받은_행수=len(rows), 고유_건수=len(keys), 일치=("Y" if ok else "N") if full else "-",
                       요청URL=LISTS[lst]["api"], 수집시각=meta.get("fetched_at", ""), 비고="; ".join(note), **cnt)
                print("%-16s %-8s %-6s 총 %4d건 · %d쪽 · 받은 %d행(고유 %d)%s"
                      % (w, gubun, lst, tots[0], n, len(rows), len(keys), "" if ok or not full else " ← 불일치"),
                      flush=True)
        # 상세
        todo = sorted(items.values(), key=lambda x: (x["code"], int(x["idx"])))
        print("상세 %d건" % len(todo), flush=True)
        for k, it in enumerate(todo, 1):
            url = DETAIL[it["code"]] % it["idx"]
            it["url"] = url
            name = "%s_%s.html" % ({"law": "법령해석", "opinion": "비조치의견서", "pastreq": "2014이전"}[it["code"]],
                                   it["idx"])
            try:
                body, meta, path = cached(TASK + "/detail", name, url, referer=TOTAL_PAGE,
                                          extra=dict(구분=it.get("kind", it.get("past_kind", "")), 검색어=it["terms"]),
                                          raw9=os.path.join(RAW9, "fsc", "detail", name))
            except urllib.error.HTTPError as e:
                it["err"] = "상세 HTTP %s" % e.code
                continue
            it["meta"], it["raw"] = meta, path
            it["detail"] = F9.parse_detail(body)
            if k % 25 == 0 or k == len(todo):
                print("  상세 %d/%d" % (k, len(todo)), flush=True)
    except Stop as e:
        stop = str(e)
        print("멈춤:", stop, flush=True)
        logrow(검색어="(중단)", 비고=stop, 수집시각=now())
    if PROBE_ONLY:
        write_csv(os.path.join(WORK, "법령해석_대주주거래_probe.csv"), list(log[0].keys()), log)
        for r in log:
            if r["검색어"].startswith("("):
                print(r["검색어"], "|", r["비고"])
        return 2 if stop else 0

    rows_out, md_n, parsed = [], 0, {}
    sc = {}
    for it in items.values():
        if it.get("serial"):
            sc[it["serial"]] = sc.get(it["serial"], 0) + 1
    os.makedirs(OUT_MD, exist_ok=True)
    for it in items.values():
        note = []
        d = it.get("detail")
        f = d["fields"] if d else {}
        title = F9.text(f["#제목"][0]) if f.get("#제목") else it.get("list_title") or it.get("past_title", "")
        lt = it.get("list_title") or it.get("past_title", "")
        if d and lt and lt.strip() != title.strip():
            note.append("목록 제목: %s" % lt)
        kind = it.get("kind") or it.get("past_kind", "")
        if not it.get("kind"):
            note.append("통합조회 목록에 없음(최근회신사례에서만 걸림) — kind 는 최근회신사례 구분")
        elif it["code"] != "pastreq" and "최근회신사례" not in it["lists"]:
            note.append("최근회신사례 목록에 없음")
        if it["code"] == "pastreq" and f.get("타입"):
            t2 = F9.text(f["타입"][0])
            if t2 and t2 not in kind:
                note.append("상세 페이지 타입: %s" % t2)
        serial = it.get("serial", "")
        if not serial and f.get("일련번호"):
            serial = F9.text(f["일련번호"][0])
        rd = F9.text(f["회신일"][0]) if f.get("회신일") else ""
        if not rd and it.get("list_date"):
            rd = it["list_date"]
            if d:
                note.append("회신일: 상세에 회신일 칸 없음 — 통합조회 목록의 회신일 열 값")
        elif rd and it.get("list_date") and rd != it["list_date"]:
            note.append("통합조회 목록 회신일: %s" % it["list_date"])
        if f.get("회신일") and len(f["회신일"]) > 1:
            note.append("회신 %d개 — 첫 회신 기준" % len(f["회신일"]))
        q_full = F9.text(f["질의요지"][0]) if f.get("질의요지") else ""
        question = q_full
        if len(q_full) > 500:
            question = q_full[:500]
            note.append("question: 앞 500자(전체 %d자)" % len(q_full))
        ans, a_full = "", ""
        if f.get("회답"):
            a_full = "\n\n".join(F9.text(x) for x in f["회답"])
            ps = F9.paragraphs(f["회답"][0])
            ans = ps[0].strip(" \t\n") if ps else ""
            if not ans:
                note.append("회답 칸이 비어 있음")
            elif len(ans) < 40:
                note.append("answer_summary: 회답 첫 문단이 %d자 — 이어지는 회답은 상세 페이지·원문 md" % len(ans))
            if q_full and q_full == F9.text(f["회답"][0]):
                note.append("사이트의 질의요지 칸 글이 회답 칸과 같음(원문 그대로 둠)")
        st = list(dict.fromkeys(F9.text(x) for x in f.get("처리구분", [])))
        if st and st != ["완료"]:
            note.append("처리구분: %s" % "/".join(st))
        if d and not f.get("질의요지"):
            note.append("상세에 질의요지 칸 없음")
        if d and not f.get("회답"):
            note.append("상세에 회답 칸 없음")
        if d and (not q_full or not ans) and f.get("첨부파일"):
            att = " / ".join(x.strip() for x in F9.text(f["첨부파일"][0]).split("\n") if x.strip())
            if att:
                note.append("첨부파일: %s" % att)
        if not d:
            note.append(it.get("err") or ("상세 미수집: %s" % stop if stop else "상세 페이지 구조를 못 읽음"))
        if (it.get("meta") or {}).get("재사용"):
            note.append("원본: %s" % it["meta"]["재사용"])
        # 관련 조문
        texts = [("제목", title, [title])]
        if lt and lt.strip() != title.strip():
            texts.append(("목록 제목", lt, [lt]))
        for lab in ("질의요지", "회답"):
            for raw in f.get(lab, []):
                texts.append((lab, F9.text(raw), F9.paragraphs(raw)))
        found, rn = related_of(texts)
        note += rn
        related = "|".join(x for x in LABELS if x in found)
        ln = loose_notes(texts, found)
        if ln:
            note.append("법률명 바로 뒤가 아닌 조문 구절(related 아님): " + " / ".join(ln[:6]) +
                        (" 외 %d" % (len(ln) - 6) if len(ln) > 6 else ""))
        if d:                                                   # 이유 등 다른 칸에만 있는 관련 조문
            other = [(lab, F9.text(r), F9.paragraphs(r)) for lab, raws in f.items()
                     if lab not in ("#제목", "질의요지", "회답") for r in raws]
            f2, _ = related_of(other)
            only = [x for x in LABELS if x in f2 and x not in found]
            if only:
                note.append("제목·질의요지·회답 밖(이유 등)에만 나오는 조문: %s" % "|".join(only))
        r9 = "Y" if (F9.HOLD in title or F9.HOLD in lt or F9.HOLD in q_full) else "N"
        body_md = ""
        if related and d:
            fn = serial or "%s_idx%s" % (it["code"], it["idx"])
            if not serial:
                note.append("일련번호 없음 — 파일명은 사이트 내부번호")
            elif sc.get(serial, 0) > 1:
                fn = "%s_%s%s" % (serial, it["code"], it["idx"])
                note.append("일련번호 %s 가 다른 건과 겹쳐 파일명에 구분·내부번호 덧붙임" % serial)
            body_md = os.path.join(OUT_MD, fn + ".md")
            write_md(body_md, it, title, rd, serial, kind, d, related)
            md_n += 1
        parsed[serial or it["idx"]] = dict(title=title, url=it.get("url", ""), f=f, it=it)
        rows_out.append(dict(title=title, reply_date=rd, kind=kind, question=question, answer_summary=ans,
                             url=it.get("url", ""), search_terms=", ".join(it["terms"]), related_9차식=r9,
                             related=related, body_md=body_md,
                             collected_at=(it.get("meta") or {}).get("fetched_at", ""), note="; ".join(note),
                             _it=it, _serial=serial))
    for w in MAIN + list(AUX):
        hit = [r for r in rows_out if w in r["_it"]["terms"]]
        by = {c: sum(1 for r in hit if r["_it"]["code"] == c) for c in ("law", "opinion", "pastreq")}
        logrow(검색어=w, 구분="주" if w in MAIN else "보조", 목록="합집합(통합조회∪최근회신사례)", 고유_건수=len(hit),
               수집시각=now(),
               비고="법령해석 %d · 비조치의견서 %d · 2014이전 %d · related 있음 %d · related_9차식=Y %d"
                  % (by["law"], by["opinion"], by["pastreq"], sum(bool(r["related"]) for r in hit),
                     sum(r["related_9차식"] == "Y" for r in hit)))
    rows_out.sort(key=lambda r: (not r["related"], [-ord(c) for c in r["reply_date"]], r["title"]))
    cols = ["title", "reply_date", "kind", "question", "answer_summary", "url", "search_terms", "related_9차식",
            "related", "body_md", "collected_at", "note"]
    write_csv(OUT_CSV, cols, [{c: r[c] for c in cols} for r in rows_out])
    made = {os.path.basename(r["body_md"]) for r in rows_out if r["body_md"]}
    for fn in sorted(os.listdir(OUT_MD)):                     # 이 스크립트 전용 폴더 — 이번에 안 만든 md 는 지운다
        if fn.endswith(".md") and fn not in made:
            os.remove(os.path.join(OUT_MD, fn))
            print("  지난 실행의 md 지움:", fn)
    pri_n = priority(parsed)
    nrel = sum(bool(r["related"]) for r in rows_out)
    ndrop = 0
    if os.path.exists(DROP_LOG):
        with open(DROP_LOG, encoding="utf-8-sig") as fi:
            ndrop = max(0, sum(1 for _ in csv.reader(fi)) - 1)
    logrow(검색어="(합계·중복 제거)", 목록="통합조회∪최근회신사례", 고유_건수=len(rows_out), 수집시각=now(),
           비고="법령해석·비조치의견서 %d건(현장건의 과제 제외) · related 있음 %d건 · 원문 md %d개 · 상세 실패 %d건"
                " · 이 실행에서 새로 받은 원본 %d개 · 9차 원본 재사용 %d개 · 접속 끊김 뒤 재시도 이 실행 %d회"
                "(누적 기록 %d회, %s) · %s"
              % (len(rows_out), nrel, md_n, sum(1 for it in items.values() if not it.get("detail")),
                 len(FETCHED), len(REUSED9), len(DROPS), ndrop, DROP_LOG,
                 ("중단: " + stop) if stop else "이 실행에서 401·403·429·로그인·캡차 없음"))
    write_csv(LOG_CSV, list(log[0].keys()), log)
    print("목록 %d행(related %d) → %s · 원문 md %d개 → %s/ · 우선 %d행 → %s · 검색기록 → %s"
          % (len(rows_out), nrel, OUT_CSV, md_n, OUT_MD, pri_n, PRI_CSV, LOG_CSV))
    return 2 if stop else 0


# ── 우선 볼 질문 ───────────────────────────────────────────────────────────
QUESTIONS = [
    "① 금융지주 자회사인 보험회사와 지주(대주주) 사이 거래에 보험업법 §111·§106 이 적용되는지",
    "② 보험회사 대주주의 특수관계인에 외국 계열사가 들어가는지",
    "③ 금융지주회사법 §34 와 보험업법 §111 이 함께 걸릴 때 이사회 의결·보고·공시를 각각 하는지",
]
# (질문 번호, 일련번호, 칸, 회답 원문 문장 그대로, note) — 원문 md 를 읽고 고른 것. 스크립트가 원문에 그대로
# 있는지 대조한다. 맞는 회신이 없는 질문은 「문서에 없음」 행.
PRIORITY = []


def priority(parsed):
    rows = []
    for qi, q in enumerate(QUESTIONS, 1):
        picks = [p for p in PRIORITY if p[0] == qi]
        if not picks:
            rows.append(dict(질문=q, 일련번호=NONE, title=NONE, url="", source_text=NONE, source_field="",
                             collected_at=now(), note="수집한 회신(검색어 합집합) 가운데 이 질문에 바로 답하는 회신을 찾지 못함"))
            continue
        for _, serial, lab, sent, nt in picks:
            p = parsed.get(serial)
            if not p:
                raise SystemExit("우선 CSV: 일련번호 %s 가 목록에 없음" % serial)
            full = "\n\n".join(F9.text(x) for x in p["f"].get(lab, []))
            if sent not in full:
                raise SystemExit("우선 CSV: %s %s 칸에 문장이 그대로 없음 — %r" % (serial, lab, sent[:60]))
            line = full[:full.index(sent)].count("\n") + 1
            rows.append(dict(질문=q, 일련번호=serial, title=p["title"], url=p["url"], source_text=sent,
                             source_field="%s 칸 %d째 줄(원문 md 기준 칸 안 줄)" % (lab, line),
                             collected_at=(p["it"].get("meta") or {}).get("fetched_at", ""), note=nt))
    write_csv(PRI_CSV, ["질문", "일련번호", "title", "url", "source_text", "source_field", "collected_at", "note"],
              rows)
    return len(rows)


LONG = F9.LONG


def write_md(path, it, title, rd, serial, kind, d, related):
    m = it["meta"]
    out = ["# %s" % title, "",
           "- 출처 URL(상세 페이지 = 게시글): %s" % it["url"],
           "- 게시글 URL: %s" % it["url"],
           "- 원파일명: (첨부 파일 아님 — 상세 HTML 페이지) 저장 원본 %s" % os.path.basename(it["raw"]),
           "- 수집일: %s" % m.get("fetched_at", ""),
           "- HTTP: %s · 바이트: %s · sha256: %s" % (m.get("http_status", ""), m.get("바이트", ""), m.get("sha256", "")),
           "- 원본: %s%s" % (it["raw"], (" (%s)" % m["재사용"]) if m.get("재사용") else ""),
           "- 제목: %s" % title,
           "- 회신일: %s" % rd,
           "- 구분(통합조회 원값): %s · 일련번호: %s%s" % (kind, serial or "(없음)",
                                                 (" · 분야: %s" % it["category"]) if it.get("category") else ""),
           "- 찾은 검색어: %s" % ", ".join(it["terms"]),
           "- 관련 조문(제목·질의요지·회답 낱말 일치): %s" % related,
           "- 텍스트화 방법: 상세 페이지 본문 표를 순서대로, 글자는 바꾸지 않고 HTML 태그만 걷어냈다"
           "(9차 web9_fsc.text 그대로 — `<br>` 은 줄바꿈, `<p>` 문단 사이는 빈 줄, 태그 없는 칸은 원래 줄바꿈 그대로, "
           "`&nbsp;` 등 엔티티는 그 글자(U+00A0 등)로). 칸 이름(처리구분·질의요지·회답·이유 …)은 사이트 표의 머리 칸 그대로다.",
           "", "---", ""]

    def gap():
        if out[-1] != "":
            out.append("")

    for head, rows in d["blocks"]:
        if head:
            gap()
            out += ["## %s" % head, ""]
        for lab, raw in rows:
            t = F9.text(raw)
            if lab is None:
                gap()
                out += ["### %s" % t, ""]
            elif lab == "첨부파일":
                out += ["- %s: %s" % (lab, " / ".join(x.strip() for x in t.split("\n") if x.strip()))]
            elif lab in LONG or "\n" in t or len(t) > 100:
                gap()
                out += ["### %s" % lab, "", t, ""]
            else:
                out += ["- %s: %s" % (lab, t)]
        gap()
    with open(path, "w", encoding="utf-8") as fo:
        fo.write("\n".join(out).rstrip() + "\n")


if __name__ == "__main__":
    sys.exit(main())
