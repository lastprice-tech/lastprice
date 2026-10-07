# -*- coding: utf-8 -*-
"""13차 9-1 법령 원문 — 모범규준 조항 기준 표 보강(작업 9)의 법령 묶음.

    LAW_DELAY=1.0 python3 -I scripts/dart/web13_law91.py fetch   # ① 오늘 현행 판 재확인(다르면 새 판 받기)
                                                                 # ② 금융지주회사감독규정 연혁 판 목록 + 판 XML
    python3 -I scripts/dart/web13_law91.py md                    # 받은 XML 만 읽어(요청 없음) md·csv 작성

· 법제처 Open API(7차 lawclient·resolve) — OC 는 환경변수/.env 로만 쓰고 기록은 OC=*** (lawclient 가 가림).
  원장: dart_out/raw/web13/law91/_call_log.csv. 요청 간격 LAW_DELAY(1.0 이상).
· 이미 받은 XML(dart_out/raw/web9·web10·web11/law)은 다시 받지 않는다. 오늘 현행과 일련번호·시행일자가 같으면 그 XML 을 쓰고,
  다르면 현행 판을 새로 받아 dart_out/raw/web13/law91/ 에 두고 두 판을 다 기록한다.
· 원문은 XML 의 글을 글자 그대로 옮긴다(별표내용·조문내용·항·호·목). 요약·고쳐 쓰기 없음. 해설은 md 의 「note:」 줄에만.
· 산출: handoff/13차_산출물/9-1_법령원문.md, 기록 dart_out/risk13/9-1_법령판.csv.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "law"))
import web10_law as L10  # noqa: E402 — law_units·article_text·rule_articles (읽기만)
from web13 import RAW, WORK, OUT, save, now, write_csv  # noqa: E402

TASK = "law91"
LAWDIR = os.path.join(RAW, TASK)
LEDGER = os.path.join(LAWDIR, "_call_log.csv")
STATE = os.path.join(LAWDIR, "_fetch_state.json")
MD = os.path.join(OUT, "9-1_법령원문.md")
CSV = os.path.join(WORK, "9-1_법령판.csv")
TODAY = "20261007"
FHC_RULE = "금융지주회사감독규정"
GOV_LAW = "금융회사의 지배구조에 관한 법률"

# (키, API 이름, 종류, 이미 받은 XML)
TARGETS = [
    ("세칙", "금융지주회사감독규정시행세칙", "rule",
     "dart_out/raw/web11/law/금융지주회사감독규정시행세칙_2200000107297.xml"),
    ("지배구조감독규정", "금융회사 지배구조 감독규정", "rule",
     "dart_out/raw/web9/law/금융회사지배구조감독규정_2100000285614.xml"),
    ("지배구조법", GOV_LAW, "law",
     "dart_out/raw/web10/law/금융회사의지배구조에관한법률_277253.xml"),
    ("지배구조법시행령", GOV_LAW + " 시행령", "decree",
     "dart_out/raw/web10/law/금융회사의지배구조에관한법률시행령_290289.xml"),
    ("금융지주회사법", "금융지주회사법", "law",
     "dart_out/raw/web11/law/금융지주회사법_254783.xml"),
    ("감독규정", FHC_RULE, "rule",
     "dart_out/raw/web10/law/금융지주회사감독규정_2100000285612.xml"),
]
KINDNAME = {"law": "법률", "decree": "시행령", "rule": "행정규칙"}
# 이미 받은 감독규정 판(다시 받지 않음)
HAVE_FHC = {
    "2100000285612": "dart_out/raw/web10/law/금융지주회사감독규정_2100000285612.xml",
    "2100000266376": "dart_out/raw/web10/law/금융지주회사감독규정_2100000266376.xml",
}


def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def xml_info(xb):
    """XML 기본정보 → dict(일련번호, 시행일자, 발령_공포일자, 제개정구분, 이름)."""
    root = ET.fromstring(xb)
    bi = root.find("행정규칙기본정보")
    if bi is not None:
        g = lambda k: (bi.findtext(k) or "").strip()  # noqa: E731
        return dict(일련번호=g("행정규칙일련번호"), 시행일자=g("시행일자"), 발령_공포일자=g("발령일자"),
                    발령번호=g("발령번호"), 제개정구분=g("제개정구분명"), 이름=g("행정규칙명"), 현행여부=g("현행여부"),
                    조문형식여부=g("조문형식여부"))
    # 법령(eflaw) XML 에는 법령일련번호(MST)가 없다(실측: 루트 속성 법령키=법령ID+공포일자+공포번호).
    # 일련번호는 파일 이름(…_<MST>.xml, 9~11차 저장 규칙)에서 읽고, 공포일자·공포번호·시행일자는 XML 에서 읽어 함께 대조한다.
    bi = root.find("기본정보")
    g = lambda k: (bi.findtext(k) or "").strip() if bi is not None else ""  # noqa: E731
    return dict(일련번호="", 시행일자=g("시행일자"), 발령_공포일자=g("공포일자"), 발령번호=g("공포번호"),
                제개정구분=g("제개정구분"), 이름=g("법령명_한글"), 현행여부="", 조문형식여부="",
                법령키=root.get("법령키", ""))


def serial_from_name(p):
    m = re.search(r"_(\d+)(?:_[^/]*)?\.xml$", p)
    return m.group(1) if m else ""


def _meta(p):
    m = p + ".meta.json"
    return json.load(open(m, encoding="utf-8")) if os.path.exists(m) else {}


# ── fetch ─────────────────────────────────────────────────────────────────
def _resolve_all(client):
    import resolve
    out, cache = {}, {}
    for key, name, kind, old in TARGETS:
        rec = dict(키=key, 법령명=name, 종류=KINDNAME[kind], 기존XML=old, 상태="", note="")
        try:
            oxb = open(old, "rb").read()
            oi = xml_info(oxb)
            if not oi["일련번호"]:
                oi["일련번호"] = serial_from_name(old)
            rec.update(기존_일련번호=oi["일련번호"], 기존_시행일자=oi["시행일자"], 기존_발령공포일=oi["발령_공포일자"],
                       기존_발령번호=oi["발령번호"],
                       기존_제개정=oi["제개정구분"], 기존_sha256=_sha(oxb), 기존_수집=_meta(old).get("fetched_at", ""),
                       기존_출처URL=_meta(old).get("출처URL", ""))
            if kind == "rule":
                cur, st, how, cands = resolve.resolve_rule(client, name)
                if not cur:
                    raise RuntimeError("현행 판을 하나로 못 정함(%s): %s" % (st, cands[:5]))
                rec.update(현행_일련번호=cur.get("행정규칙일련번호", ""), 현행_시행일자=cur.get("시행일자", ""),
                           현행_발령공포일=cur.get("발령일자", ""), 현행_제개정=cur.get("제개정구분명", ""),
                           현행_API이름=cur.get("행정규칙명", ""), 일치방식=how, 시행예정판="(행정규칙 — 현행만 조회)")
            else:
                base = GOV_LAW if name.startswith(GOV_LAW) else name
                if base not in cache:
                    cache[base] = resolve.resolve_law(client, base)
                res, st, cands = cache[base]
                tier = res.get("법률" if kind == "law" else "시행령", {})
                cur = tier.get("현행")
                if not cur:
                    raise RuntimeError("현행을 못 찾음(%s): %s" % (st, cands[:5]))
                rec.update(현행_일련번호=cur.get("법령일련번호", ""), 현행_시행일자=cur.get("시행일자", ""),
                           현행_발령공포일=cur.get("공포일자", ""), 현행_제개정=cur.get("제개정구분명", ""),
                           현행_API이름=cur.get("법령명한글", ""), 일치방식=tier.get("일치", ""),
                           시행예정판=" ; ".join("%s(시행 %s, 공포 %s)" % (p.get("법령일련번호", ""), p.get("시행일자", ""),
                                                                    p.get("공포일자", ""))
                                                for p in tier.get("시행예정") or []) or "없음")
            # 같은 판: 일련번호·시행일자·발령(공포)일자가 모두 같을 때
            same = (rec["현행_일련번호"] == rec["기존_일련번호"] and rec["현행_시행일자"] == rec["기존_시행일자"]
                    and rec["현행_발령공포일"] == rec["기존_발령공포일"])
            rec["같은판"] = "Y" if same else "N"
            if same:
                rec.update(사용XML=old, 사용_sha256=rec["기존_sha256"])
            else:
                sn, ef = rec["현행_일련번호"], rec["현행_시행일자"]
                if kind == "rule":
                    sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
                else:
                    sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=sn, efYd=ef, type="XML")
                if client.count_oc(xb):
                    raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
                p, m = save(TASK, "%s_%s_현행%s.xml" % (name.replace(" ", ""), sn, TODAY), xb,
                            dict(출처URL=murl, http_status=sc, fetched_at=now()))
                rec.update(사용XML=p, 사용_sha256=m["sha256"], 새판_출처URL=murl, 새판_수집=m["fetched_at"])
            rec["상태"] = "OK"
        except Exception as e:                               # noqa: BLE001
            rec["상태"] = "실패"
            rec["note"] = client.mask("%s: %s" % (type(e).__name__, e))[:300]
        print("  %-24s %s 기존 %s(%s) · 현행 %s(%s) · 같은판 %s %s" % (
            name, rec["상태"], rec.get("기존_일련번호"), rec.get("기존_시행일자"), rec.get("현행_일련번호"),
            rec.get("현행_시행일자"), rec.get("같은판"), rec["note"][:80]))
        out[key] = rec
    return out


def _history(client):
    """lawSearch admrul query=금융지주회사감독규정 nw=2 display=100(쪽 넘김) → 판 목록. 목록 응답도 원본으로 저장."""
    rows, page, pages = [], 1, []
    while True:
        st, body, murl, host = client.api("lawSearch.do", target="admrul", type="XML", query=FHC_RULE,
                                          nw="2", display="100", page=str(page))
        # 목록 응답의 상세링크에 OC 값이 그대로 실려 온다(실측) → 원본 그대로 저장하지 않고 OC 를 *** 로 가린 사본만 저장.
        n_oc = client.count_oc(body)
        body = client.mask(body)
        if client.count_oc(body):
            raise RuntimeError("가린 뒤에도 인증값이 남음 — 저장하지 않음")
        p, m = save(TASK, "_연혁목록_%s_p%d.xml" % (FHC_RULE, page), body,
                    dict(출처URL=murl, http_status=st, fetched_at=now(),
                         가림="응답 본문의 OC 값 %d곳을 ***로 바꾼 사본(원 응답 바이트와 다름)" % n_oc if n_oc else ""))
        pages.append(dict(page=page, 파일=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"]))
        root = ET.fromstring(body)
        got = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("admrul")]
        total = int((root.findtext("totalCnt") or "0").strip() or 0)
        rows += got
        print("  목록 p%d: %d건 (누계 %d / totalCnt %d)" % (page, len(got), len(rows), total))
        if not got or len(rows) >= total or page >= 20:
            break
        page += 1
    return rows, pages


def _norm(s):
    return re.sub(r"\s+", "", s or "")


def fetch():
    client = _client()
    print("① 현행 재확인 (%s)" % TODAY)
    res = _resolve_all(client)
    print("② %s 연혁 판 목록" % FHC_RULE)
    rows, pages = _history(client)
    hist = []
    for r in rows:
        nm = r.get("행정규칙명", "")
        rec = dict(행정규칙명=nm, 일련번호=r.get("행정규칙일련번호", ""), 발령일자=r.get("발령일자", ""),
                   시행일자=r.get("시행일자", ""), 발령번호=r.get("발령번호", ""), 제개정구분=r.get("제개정구분명", ""),
                   현행연혁구분=r.get("현행연혁구분", ""), 행정규칙종류=r.get("행정규칙종류", ""),
                   소관=r.get("소관부처명", ""), 행정규칙ID=r.get("행정규칙ID", ""), 대상="", 제외사유="", XML="",
                   sha256="", 출처URL="", 수집="", 재사용="")
        if nm == FHC_RULE:
            rec["대상"] = "Y"
        elif _norm(nm) == _norm(FHC_RULE):
            rec["대상"] = "Y"
            rec["제외사유"] = "이름 공백만 다름(본문 판으로 봄)"
        else:
            rec["대상"] = "N"
            rec["제외사유"] = ("이름이 다른 일괄개정 고시 — 금융지주회사감독규정 본문 판이 아님" if "일괄" in nm else
                            "이름이 다른 행정규칙(검색어 부분일치) — 본문 판이 아님")
        hist.append(rec)
    todo = [h for h in hist if h["대상"] == "Y"]
    print("  본문 판 %d건 · 제외 %d건" % (len(todo), len(hist) - len(todo)))
    for h in sorted(todo, key=lambda x: (x["시행일자"], x["발령일자"], x["일련번호"])):
        sn = h["일련번호"]
        mine = os.path.join(LAWDIR, "%s_%s.xml" % (FHC_RULE, sn))
        if sn in HAVE_FHC:
            p = HAVE_FHC[sn]
            xb = open(p, "rb").read()
            h.update(XML=p, sha256=_sha(xb), 출처URL=_meta(p).get("출처URL", ""), 수집=_meta(p).get("fetched_at", ""),
                     재사용="Y(10차 원본 — 다시 받지 않음)")
            continue
        if os.path.exists(mine):                            # 이번 차수에 이미 받은 판(재실행)
            xb = open(mine, "rb").read()
            h.update(XML=mine, sha256=_sha(xb), 출처URL=_meta(mine).get("출처URL", ""),
                     수집=_meta(mine).get("fetched_at", ""), 재사용="N(13차 수집 — 재실행 시 다시 받지 않음)")
            continue
        try:
            sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
            if client.count_oc(xb):
                raise RuntimeError("응답 본문에 인증값 — 저장하지 않음")
            p, m = save(TASK, "%s_%s.xml" % (FHC_RULE, sn), xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            h.update(XML=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"], 재사용="N")
        except Exception as e:                               # noqa: BLE001
            h["제외사유"] = client.mask("받기 실패 %s: %s" % (type(e).__name__, e))[:300]
        print("    %s 발령 %s 시행 %s %s %s" % (sn, h["발령일자"], h["시행일자"], h["제개정구분"],
                                           "OK" if h["XML"] else h["제외사유"][:60]))
    state = dict(수집일=now(), 현행재확인=res, 연혁목록쪽=pages, 연혁=hist, API호출=client.n_calls)
    os.makedirs(LAWDIR, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print("API 호출 %d · 상태 → %s" % (client.n_calls, STATE))


def bulk():
    """연혁 목록에서 이름이 다른 「…일부개정규정/일괄개정규정」 고시를 받아 본문 판인지(조문 구조), 제30조를 건드리는지 확인한다.
    본문 판 여부는 XML 의 조문내용이 「제1조(목적)」으로 시작하는 감독규정 전문인지로 본다. 받은 XML 은 law91 에 둔다."""
    client = _client()
    st = json.load(open(STATE, encoding="utf-8"))
    for h in st["연혁"]:
        if h["대상"] != "N" or h["행정규칙명"].replace(" ", "") == "금융지주회사감독규정시행세칙":
            continue
        sn = h["일련번호"]
        p = os.path.join(LAWDIR, "일괄개정고시_%s.xml" % sn)
        if os.path.exists(p):
            xb = open(p, "rb").read()
            h.update(XML=p, sha256=_sha(xb), 출처URL=_meta(p).get("출처URL", ""), 수집=_meta(p).get("fetched_at", ""))
            continue
        try:
            sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
            if client.count_oc(xb):
                raise RuntimeError("응답 본문에 인증값 — 저장하지 않음")
            p, m = save(TASK, "일괄개정고시_%s.xml" % sn, xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            h.update(XML=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"])
        except Exception as e:                               # noqa: BLE001
            h["제외사유"] += client.mask(" · 받기 실패 %s: %s" % (type(e).__name__, e))[:200]
        print("  %s %s %s" % (sn, h["행정규칙명"][:40], "OK" if h["XML"] else "실패"))
    st["API호출_bulk"] = client.n_calls
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


# ── md · csv (요청 없음, 받은 XML 만 읽음) ─────────────────────────────────
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
# 1차 실행(2026-10-07 14:48) 결함 기록: 법령 XML 에 법령일련번호 칸이 없어 비교가 실패 → 같은 판 3건을 다시 받음.
REFETCH_NOTE = ("13차 1차 실행(2026-10-07 14:48 UTC) 때 스크립트 결함(법령 XML 에 법령일련번호 칸이 없어 기존 판 비교 실패)으로 "
                "같은 판을 한 번 더 받았다(원장 law91/_call_log.csv 에 기록). 받은 바이트의 sha256 이 기존 XML 과 같아 사본은 지웠다 — "
                "결과적으로 오늘 현행 본문이 기존 XML 과 바이트 단위로 같음을 확인한 셈")
REFETCHED = {"지배구조법", "지배구조법시행령", "금융지주회사법"}


def _fence(t):
    return ["```text", t.rstrip("\n"), "```"]


def _d(s):
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:8]) if re.match(r"^\d{8}$", s or "") else (s or "")


def _annex(xb, no, ga="00"):
    root = ET.fromstring(xb)
    for b in root.iter("별표단위"):
        g = lambda k: (b.findtext(k) or "").strip()  # noqa: E731
        if g("별표구분") == "별표" and g("별표번호") == no and (g("별표가지번호") or "00") == ga:
            c = b.find("별표내용")
            return dict(제목=g("별표제목"), 글="".join(c.itertext()) if c is not None else "", 키=b.get("별표키", ""),
                        hwp=g("별표서식파일링크"), pdf=g("별표서식PDF파일링크"))
    return None


def _rule_art(xb, label):
    hit = [a for a in L10.rule_articles(xb) if a[0] == label]
    return hit[0] if hit else None


def _hang_lines(text, n):
    """행정규칙 조문 글(한 덩어리)에서 n 번째 항(①…)의 줄들만 — 다음 항 머리 줄 앞까지. 글자 그대로."""
    lines = text.split("\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\s*(?:제\d+조(?:의\d+)?\([^)]*\)\s*)?([%s])" % CIRC, ln)]
    marks = {}
    for i in idx:
        m = re.match(r"^\s*(?:제\d+조(?:의\d+)?\([^)]*\)\s*)?([%s])" % CIRC, lines[i])
        marks[i] = CIRC.index(m.group(1)) + 1
    starts = [i for i in idx if marks[i] == n]
    if not starts:
        return None, []
    s = starts[0]
    nxt = [i for i in idx if i > s]
    e = nxt[0] if nxt else len(lines)
    return "\n".join(lines[s:e]), [marks[i] for i in idx]


def _law_hang(xb, jo, n, hos=None):
    """법령 XML 의 조 jo 제n항(항내용 + 호·목). hos 를 주면 그 호만(예: {'2.'}). 글자 그대로(요소마다 줄바꿈)."""
    want = L10._jo_key(jo)
    root = ET.fromstring(xb)
    for u in root.iter("조문단위"):
        if L10._t(u, "조문여부") not in ("", "조문"):
            continue
        if (L10._t(u, "조문번호").lstrip("0"), (L10._t(u, "조문가지번호") or "0").lstrip("0") or "0") != want:
            continue
        for h in u.findall("항"):
            if L10._t(h, "항번호")[:1] == CIRC[n - 1]:
                if hos is None:
                    return L10.article_text(h)
                out = [L10._t(h, "항내용")]
                for ho in h.findall("호"):
                    if L10._t(ho, "호번호") in hos:
                        out.append(L10.article_text(ho))
                return "\n".join(x for x in out if x)
    return None


def _law_art(xb, jo):
    r = L10.find_unit(xb, jo)
    return r


def _a5_blocks(raw):
    """별표5 표를 항목 단위로 나눈다 → (머리 줄들, [(코드, 제목, 줄들)]). 줄은 원문 그대로(빈 줄 포함)."""
    lines = raw.split("\n")
    top = next(i for i, ln in enumerate(lines) if ln.startswith("┏"))
    hdr_end = next(i for i, ln in enumerate(lines) if ln.startswith("┣"))
    starts = []
    for i, ln in enumerate(lines):
        m = re.match(r"^┃(\[(\d+)\.\s*[^\]]*\]|(\d+-\d+)\.)", ln)
        if m and i > hdr_end:
            starts.append((i, m.group(3) or "[%s]" % m.group(2)))
    stops = [i for i, ln in enumerate(lines) if ln.startswith("┠") or ln.startswith("┗")]
    blocks = []
    for k, (i, code) in enumerate(starts):
        cand = [s for s, _ in starts if s > i] + [s for s in stops if s > i]
        j = min(cand) if cand else len(lines)
        blk = lines[i:j]
        while blk and not blk[-1].strip():
            blk.pop()
        col1 = []
        for ln in blk:
            if ln.startswith("┃") and "│" in ln:
                c = ln[1:].split("│")[0].strip().replace("　", "").strip()
                if c:
                    col1.append(c)
        blocks.append((code, " ".join(col1), blk))
    return lines[:hdr_end + 1], top, blocks


def build_md():
    st = json.load(open(STATE, encoding="utf-8"))
    res = st["현행재확인"]
    X = {k: open(v["사용XML"], "rb").read() for k, v in res.items()}
    M = {k: _meta(v["사용XML"]) for k, v in res.items()}
    recheck_at = st["수집일"]

    def cite(key, where):
        r, m = res[key], M[key]
        return "[%s · 일련번호 %s(시행 %s, 발령/공포 %s) · %s · %s · 수집 %s(원본 %s), 현행 재확인 %s]" % (
            r["현행_API이름"] or r["법령명"], r["현행_일련번호"], _d(r["현행_시행일자"]), _d(r["현행_발령공포일"]),
            m.get("출처URL", ""), where, (m.get("fetched_at", "") or "")[:10], r["사용XML"], recheck_at[:10])

    md, gots, notgots, diffs, judg = [], [], [], [], []
    md += ["# 9-1 법령 원문 — 13차(리스크부문 작업 9: 모범규준 조항 기준 표 보강)", "",
           "- 출처: 국가법령정보센터 Open API(`lawSearch.do`·`lawService.do`, 요청 URL 의 인증값은 `OC=***` 로 가림). "
           "원장 `dart_out/raw/web13/law91/_call_log.csv`(LAW_DELAY=1.0).",
           "- 수집일: 2026-10-07(현행 판 재확인 %s · 금융지주회사감독규정 연혁 판 받기). 본문 XML 은 9·10·11차에 받은 것을 그대로 썼다"
           "(오늘 현행과 일련번호·시행일자·발령/공포일자가 모두 같음 — 0절)." % recheck_at,
           "- 방법: XML 의 글(행정규칙은 `조문내용`, 법령은 `조문내용`·`항내용`·`호내용`·`목내용`, 별표는 `별표내용`)을 "
           "고치지 않고 코드 블록에 옮겼다. 법령 조문은 요소마다 줄을 바꿨다(10·11차와 같은 방식). 별표 PDF·HWP 는 받지 않았다"
           "(XML 별표내용에 글이 있음). 스크립트 `scripts/dart/web13_law91.py`(`fetch`·`bulk`·`md`).",
           "- 한계: ① 법령에는 쪽이 없어 위치는 조·항·별표 번호로 적는다. ② 세칙 별표 글 가운데 원문 XML 바이트 자체가 ASCII 물음표"
           "(`?`, 0x3F)인 곳이 있다(1-1·1-3·1-4절 note) — 원래 글자를 확인하지 못해 그대로 두었다. ③ 행정규칙 연혁 판 XML 은 법제처 DB 가 "
           "나중에 만든 것(생성일자)이라 당시 고시 원문과 글자까지 같다고 보장되지 않는다(5절 한계). ④ 「추출 범위에 없음」은 적힌 범위에서 "
           "찾지 못했다는 뜻이지 없다는 단정이 아니다.",
           "- 표기: 원문 인용은 코드 블록. 해설은 「note:」 줄, 해석이 들어간 곳은 「(판단)」.",
           "- 모범규준 조 번호: 사용자 지시서 9-1 에는 조 번호가 없다. 폐지 모범규준 원문이 저장소에 없어 조 대응을 확인할 수 없으므로 "
           "조 번호를 새로 붙이지 않고, 주제1 표의 어느 칸 자료인지만 「(판단)」으로 적는다.", ""]

    # 0. 현행 재확인
    md += ["## 0. 현행 판 재확인(2026-10-07)", "",
           "| 법령 | 종류 | 받아 둔 XML(일련번호 · 시행일 · 발령/공포일) | 오늘 현행(API) | 결과 | 쓴 XML · sha256 |",
           "|---|---|---|---|---|---|"]
    for k, r in res.items():
        md.append("| %s | %s | %s · %s · %s | %s · %s · %s | %s | `%s` · `%s` |" % (
            r["법령명"], r["종류"], r["기존_일련번호"], _d(r["기존_시행일자"]), _d(r["기존_발령공포일"]),
            r["현행_일련번호"], _d(r["현행_시행일자"]), _d(r["현행_발령공포일"]),
            "같은 판 — 기존 XML 사용" if r["같은판"] == "Y" else "다른 판 — 새로 받음", r["사용XML"], r["사용_sha256"]))
    md += ["", "- note: 법령(법률·시행령)의 시행예정 판: " + " · ".join(
        "%s %s" % (r["법령명"], r["시행예정판"]) for r in res.values() if r["종류"] != "행정규칙") +
           ". 행정규칙은 현행만 조회했다(resolve_rule).",
           "- note: " + REFETCH_NOTE + ".", ""]

    # 1. 세칙
    sx = X["세칙"]
    md += ["## 1. 금융지주회사감독규정시행세칙", "",
           "- 판: " + cite("세칙", "행정규칙 XML"),
           "- 주제1 표 칸(판단): 별표 3·3-1·4, 제12조 → 「지주 평가·검사·공시」 칸(경영실태평가). 별표 5 → 같은 칸(경영공시).", ""]
    qmarks = {}
    for no, ga, sec, want_title in (("0003", "00", "1-1", "경영실태평가 부문별 평가항목"),
                                    ("0003", "01", "1-2", "계량지표의 산정기준"),
                                    ("0004", "00", "1-3", "경영실태 평가등급별 정의")):
        a = _annex(sx, no, ga)
        lab = "별표 %d%s" % (int(no), "" if ga == "00" else "-%d" % int(ga))
        qmarks[lab] = [(m.start(), a["글"][max(0, m.start() - 8):m.start() + 9].replace("\n", " ").strip())
                       for m in re.finditer(r"\?", a["글"])]
        md += ["### %s [%s] %s" % (sec, lab, a["제목"]), "",
               "- 인용: " + cite("세칙", "[%s] 별표내용(별표키 %s)" % (lab, a["키"])),
               "- 원본 파일 링크(받지 않음): HWP http://www.law.go.kr%s · PDF http://www.law.go.kr%s" % (a["hwp"], a["pdf"])]
        if qmarks[lab]:
            md.append("- note: 원문 XML 에 ASCII `?`(0x3F)로 들어 있는 곳 %d곳: %s — 고치지 않음(원래 글자는 가운뎃점일 수 있음, 판단)." % (
                len(qmarks[lab]), " · ".join("「%s」" % c for _, c in qmarks[lab])))
        if sec == "1-1":
            md += ["- note(지시서 대조): 지시서 「재무상태 부문의 자산건전성·수익성·유동성 항목, 각주 포함」. 원문 [별표 3] 은 평가부문 "
                   "리스크관리(R)·재무상태(F)·잠재적 충격(I) 셋이고, 재무상태(F)의 세부평가부문은 자본적정성(C)·자산건전성(A)·수익성(E)·"
                   "유동성(L) 넷이다. 각주는 「1)」 하나이며 자본적정성(C) 칸 「보통주자본비율1)」에 붙어 있다(자산건전성·수익성·유동성 칸에는 "
                   "각주 표시가 없다). 아래는 별표 전문."]
            diffs.append("9-1 세칙 [별표 3]: 지시서는 「재무상태 부문의 자산건전성·수익성·유동성 항목, 각주 포함」이라 했으나 원문 재무상태(F)에는 "
                         "자본적정성(C)도 있고, 각주는 1개(「1) 규정 제25조의4가 적용되는 은행지주회사는 2019년 12월 31일까지 적용배제, 2020년부터 "
                         "적용」)로 자본적정성 칸 「보통주자본비율1)」에 붙어 있음. 별표 3 전문에는 리스크관리(R)·잠재적 충격(I) 부문도 있음(전문을 옮김).")
        if sec == "1-2":
            t = a["글"]
            have = [w for w in ("필요자본에 대한 자기자본 비율", "부채비율", "이중레버리지비율") if w in t]
            md += ["- note(지시서 대조): 지시서의 세 지표가 원문에 있다 — 「1. 자본적정성 지표 … 마. 필요자본에 대한 자기자본 비율」, "
                   "「2. 금융지주회사 재무구조안정성 지표 가. 부채비율 / 나. 이중레버리지비율」(확인한 낱말: %s). 원문 표기는 "
                   "「자기자본 비율」(띄어 씀). 같은 별표에 총자본비율·기본자본비율·보통주자본비율·레버리지비율도 있다. 산식의 분수는 원문이 "
                   "가로줄 글자(─)로 그린 것이며 그대로 옮겼다." % " · ".join("「%s」" % w for w in have)]
        if sec == "1-3":
            md += ["- note: 지시서 「경영실태평가 등급별 정의」 ↔ 원문 제목 「경영실태 평가등급별 정의」(띄어쓰기만 다름). 구성: 1. 리스크관리 "
                   "종합 + 1)~4), 2. 재무상태 종합 + 1)~4), 3. 잠재적 충격 종합 + 1)~3), 4. 종합평가."]
        md += [""] + _fence(a["글"]) + [""]
        gots.append(dict(item="금융지주회사감독규정시행세칙 [%s] %s 전문" % (lab, a["제목"]),
                         source="법제처 Open API 행정규칙 XML 일련번호 2200000107297(11차 원본, 2026-10-07 현행 재확인)",
                         articles="조 번호 미부여 — 주제1 표 「지주 평가·검사·공시」 칸 자료(판단)"))

    # 1-4 별표5
    a5 = _annex(sx, "0005")
    head, top, blocks = _a5_blocks(a5["글"])
    risky = [c for c, t, b in blocks if any("리스크" in ln for ln in b)]
    pickA = [c for c, t, b in blocks if c == "[5]" or c.startswith("5-")]
    pickB = ["4-1", "4-2", "4-3", "4-4", "4-5"]
    picked = [b for b in blocks if b[0] in pickA + pickB]
    unpicked = [b for b in blocks if b[0] not in pickA + pickB]
    md += ["### 1-4 [별표 5] %s — 리스크관리 관련 항목" % a5["제목"], "",
           "- 인용: " + cite("세칙", "[별표 5] 별표내용(별표키 %s)" % a5["키"]),
           "- 원본 파일 링크(받지 않음): HWP http://www.law.go.kr%s · PDF http://www.law.go.kr%s" % (a5["hwp"], a5["pdf"]),
           "- note(고른 기준): 기준 A(기계적) — 표의 행 글에 「리스크」가 들어간 항목: %s(= [5. 리스크관리] 머리 행과 5-1~5-5). "
           "기준 B(판단) — [4. 경영지표] 가운데 [별표 3] 재무상태 부문(자본적정성·자산건전성·수익성·유동성)과 같은 지표를 공시하는 "
           "4-1~4-5. 4-6 신용평가등급은 고르지 않았다." % " · ".join(risky),
           "- note: 항목 행은 원문 표의 줄을 그대로 잘라 옮겼다(표 머리 줄 + 고른 항목의 줄, 항목 사이 빈 줄 포함). "
           "고르지 않은 행은 옮기지 않았고 제목만 아래에 적는다. 별표 첫머리(개정 연혁 줄·제목 줄)는 표 머리와 함께 옮긴다."]
    q5 = [(m.start(), a5["글"][max(0, m.start() - 8):m.start() + 9].replace("\n", " ").strip()) for m in re.finditer(r"\?", a5["글"])]
    if q5:
        md.append("- note: 원문 XML 에 ASCII `?`(0x3F)로 들어 있는 곳 %d곳(별표 5 전체): %s — 고치지 않음." % (
            len(q5), " · ".join("「%s」" % c for _, c in q5)))
    md += ["", "표 머리(별표 첫머리 ~ 머리 행):", ""] + _fence("\n".join(head)) + [""]
    for code, title, blk in picked:
        md += ["항목 「%s」 — %s:" % (title, "기준 A" if code in pickA else "기준 B(판단)"), ""] + _fence("\n".join(blk)) + [""]
    md += ["고르지 않은 항목(제목은 표 첫 칸 글을 이어 붙인 것): " + " · ".join("%s「%s」" % (c, t) for c, t, _ in unpicked), "",
           "- note(판단): 고르지 않은 것 가운데 6-1 내부거래(그룹 내부거래 정책·거래내역), 6-2 내부통제, 3-7 시스템적 중요도 평가지표, "
           "3-8 우발부채 등은 모범규준의 위험 전이·내부통제 조항과 닿을 수 있다 — 필요하면 같은 XML 에서 옮길 수 있다.", ""]
    gots.append(dict(item="금융지주회사감독규정시행세칙 [별표 5] 경영공시 항목 및 내용 — 리스크관리 관련 항목(%s)" % ", ".join(pickA + pickB),
                     source="법제처 Open API 행정규칙 XML 일련번호 2200000107297(11차 원본, 2026-10-07 현행 재확인)",
                     articles="조 번호 미부여 — 주제1 표 「지주 평가·검사·공시」 칸(공시) 자료(판단)"))
    judg.append("9-1 세칙 [별표 5] 리스크관리 관련 항목 선정: 기준 A(행 글에 「리스크」 — [5. 리스크관리]·5-1~5-5)는 기계적, "
                "기준 B(4-1~4-5 를 [별표 3] 재무상태 부문 대응 지표로 봄)는 판단. 6-1·6-2·3-7·3-8 은 고르지 않음(판단).")

    # 1-5 제12조 ⑥ ⑧
    lab12, ti12, t12 = _rule_art(sx, "제12조")
    h6, marks = _hang_lines(t12, 6)
    h8, _ = _hang_lines(t12, 8)
    h2, _ = _hang_lines(t12, 2)
    md += ["### 1-5 세칙 제12조(%s) 제6항·제8항" % ti12, "",
           "- 인용: " + cite("세칙", "제12조 조문내용"),
           "- note(항 번호 확인): 제12조 조문내용의 항 머리 순서 %s. 제6항 앞은 ⑤(경영실태평가등급별 정의 <별표4>), 뒤는 ⑦(의견제출 기회). "
           "제8항은 마지막 항(앞은 ⑦). 아래는 그 항의 줄만(항 머리 줄 ~ 다음 항 머리 줄 앞, 들여쓰기 그대로)." % "".join(CIRC[i - 1] for i in marks), "",
           "제6항:", ""] + _fence(h6) + ["", "제8항:", ""] + _fence(h8) + [
           "", "보충(지시 범위 밖 — 판단으로 덧붙임): 제12조 제2항은 경영실태평가 때 평가대상에서 뺄 수 있는 자회사등을 정한다. 사용자 9-4 의 "
           "「3조: 위험이 경미한 자회사를 적용에서 빼는 기준」과 닿을 수 있어 옮긴다.", ""] + _fence(h2) + [""]
    gots.append(dict(item="금융지주회사감독규정시행세칙 제12조 제6항·제8항(+보충 제2항)", source="같은 XML 조문내용",
                     articles="조 번호 미부여 — 「지주 평가·검사·공시」 칸(판단); 보충 제2항은 모범규준 3조(사용자 9-4 표기)와 닿을 수 있음(판단)"))
    judg.append("9-1 세칙 제12조 제2항(평가대상 제외 자회사등)을 지시 범위 밖이지만 모범규준 3조(사용자 9-4 표기 조 번호)와 닿는다고 보고 덧붙임(판단).")

    # 2. 지배구조 감독규정
    gx = X["지배구조감독규정"]
    md += ["## 2. 금융회사 지배구조 감독규정 제8조·제10조·제13조", "",
           "- 판: " + cite("지배구조감독규정", "행정규칙 XML"),
           "- 주제1 표 칸(판단): 「현행 법령」 칸(위험관리위원회 심의사항·위험관리기준·위험관리전담조직).", ""]
    for jo in ("제8조", "제10조", "제13조"):
        lab, ti, t = _rule_art(gx, jo)
        md += ["### %s(%s)" % (jo, ti), "", "- 인용: " + cite("지배구조감독규정", jo + " 조문내용"), ""] + _fence(t) + [""]
    md += ["- note: 제8조는 법 제21조제5호(위험관리위원회 심의·의결 사항의 고시 위임), 제10조는 법 제23조제1항·영 제18조(금융지주회사 "
           "완전자회사등의 경영 투명성 요건), 제13조는 영 제22조제1항제10호·제2항(위험관리기준·위험관리전담조직)을 받는 조문이다(조문 첫 문장의 "
           "인용 그대로). 제10조 제목은 「경영의 투명성 등 요건」이다.", ""]
    gots.append(dict(item="금융회사 지배구조 감독규정 제8조·제10조·제13조 전문",
                     source="법제처 Open API 행정규칙 XML 일련번호 2100000285614(9차 원본, 2026-10-07 현행 재확인)",
                     articles="조 번호 미부여 — 「현행 법령」 칸(판단)"))

    # 3. 지배구조법 시행령
    dx, lx = X["지배구조법시행령"], X["지배구조법"]
    md += ["## 3. 금융회사의 지배구조에 관한 법률 시행령 제6조제3항, 제20조, 제22조, 제24조", "",
           "- 판(시행령): " + cite("지배구조법시행령", "법령 XML"),
           "- 판(법률, 인용 조문 확인용): " + cite("지배구조법", "법령 XML"),
           "- 주제1 표 칸(판단): 「현행 법령」 칸(위험관리위원회 설치 예외, 위험관리책임자·준법감시인, 위험관리기준).", ""]
    r6 = _law_art(dx, "제6조")
    md += ["### 3-1 시행령 제6조(%s) 제3항" % r6[1], "", "- 인용: " + cite("지배구조법시행령", "제6조제3항"), ""] + \
        _fence(_law_hang(dx, "제6조", 3)) + [""]
    for jo, sec in (("제20조", "3-2"), ("제22조", "3-3"), ("제24조", "3-4")):
        r = _law_art(dx, jo)
        md += ["### %s 시행령 %s(%s)" % (sec, jo, r[1]), "", "- 인용: " + cite("지배구조법시행령", jo)] + \
            (["- note: 지시서 「20조(직원 중 선임 가능 회사)」 — 원문 제목은 「준법감시인의 임면 등」이고, 직원 중 선임 가능 회사는 제2항"
              "(법 제25조제2항 단서의 「대통령령으로 정하는 금융회사」)이다. 법 제28조제2항이 제25조제2항~제6항을 위험관리책임자에 준용한다(3-5절)."]
             if jo == "제20조" else []) + [""] + _fence(r[2]) + [""]
    diffs.append("9-1 지배구조법 시행령 제20조: 지시서 괄호 「직원 중 선임 가능 회사」는 조 제목이 아니라 제2항의 내용(원문 제목 「준법감시인의 임면 등」).")
    gots.append(dict(item="금융회사의 지배구조에 관한 법률 시행령 제6조제3항, 제20조, 제22조, 제24조 전문",
                     source="법제처 Open API 법령 XML MST 290289(시행 2026-10-01, 10차 원본, 2026-10-07 현행 재확인)",
                     articles="조 번호 미부여 — 「현행 법령」 칸(판단)"))
    # 3-5 인용된 법 조문
    md += ["### 3-5 위 조문이 인용하는 법 조문(금융회사의 지배구조에 관한 법률)", "",
           "- note: 시행령 제6조제3항 → 법 제3조제3항(그 제2호·제3호가 법 제16조·제21조를 가리킴). 시행령 제20조 → 법 제25조제1항·제2항. "
           "시행령 제22조 → 법 제27조제1항. 시행령 제24조 → 법 제29조제2호·제5호, 법 제25조제1항, 법 제28조제1항. 감독규정 제8조 → 법 제21조. "
           "다른 법률(자본시장법·은행법·보험업법 등) 인용은 옮기지 않았다.", ""]
    q3 = _law_hang(lx, "제3조", 3)
    md += ["법 제3조(%s) 제3항 — 인용: %s" % (_law_art(lx, "제3조")[1], cite("지배구조법", "제3조제3항")), ""] + _fence(q3) + [""]
    for jo in ("제16조", "제21조", "제25조", "제27조", "제28조", "제29조"):
        r = _law_art(lx, jo)
        md += ["법 %s(%s) — 인용: %s" % (jo, r[1], cite("지배구조법", jo)), ""] + _fence(r[2]) + [""]
    s11 = _law_hang(dx, "제11조", 2, hos={"2."})
    md += ["보충(지시 범위 밖 — 판단으로 덧붙임): 시행령 제11조(%s) 제2항 본문과 제2호 — 금융지주회사 위험관리책임자·준법감시인이 "
           "자회사등에서 같은 업무를 겸직하는 경우를 다룬다. 인용: %s. 제1호·제3호·제4호는 옮기지 않음." % (
               _law_art(dx, "제11조")[1], cite("지배구조법시행령", "제11조제2항 본문·제2호")), ""] + _fence(s11) + [""]
    # 3-6 확인
    t63 = _law_hang(dx, "제6조", 3)
    t202 = _law_hang(dx, "제20조", 2)
    fhc_63 = "금융지주회사" in t63
    fhc_202 = "금융지주회사" in t202
    gov_all = "\n".join(t for _, _, t in L10.rule_articles(gx))
    ref6 = re.findall(r"영 제6조[^ ]*", gov_all)
    ref20 = re.findall(r"영 제20조[^ ]*", gov_all)
    md += ["### 3-6 확인할 것", "",
           "① 위험관리위원회 설치 예외", "",
           "- note: 법 제16조제1항제3호가 위험관리위원회를 설치 의무 위원회로 두고, 같은 조 제2항(보수위원회)·제3항(내부통제위원회)에는 "
           "설치하지 않을 수 있는 경우가 있으나 위험관리위원회에 대한 그런 문구는 제16조에 없다.",
           "- note: 예외를 두는 곳은 법 제3조제3항(「대통령령으로 정하는 금융회사에 대해서는 … 2. 제16조제1항부터 제3항까지에 따른 이사회내 "
           "위원회의 설치에 관한 사항 3. 제21조에 따른 위험관리위원회에 관한 사항」을 적용하지 아니함)과 이를 받는 시행령 제6조제3항이다.",
           "- note: 시행령 제6조제3항 각 호는 1. 상호저축은행(자산총액 7천억원 미만) 2. 금융투자업자·종합금융회사(5조원 미만, 운용재산 합계 "
           "20조원 이상은 제외) 3. 보험회사(5조원 미만) 4. 여신전문금융회사(5조원 미만) 5. 금융위원회 고시 자이고, 단서로 주권상장법인으로서 "
           "자산총액 2조원 이상인 자는 뺀다. 제3항 글에 「금융지주회사」 낱말: %s." % ("있음" if fhc_63 else "나오지 않음"),
           "- note: 제5호의 「금융위원회가 정하여 고시하는 자」 — 금융회사 지배구조 감독규정 현행(2100000285614) 전 조문에서 「영 제6조」를 "
           "인용하는 곳을 찾았으나 %s → 추출 범위에 없음(그 밖의 고시는 찾지 않음)." % (
               "· ".join(ref6) if ref6 else "없었다(정규식 `영 제6조`, 조문내용 전체)"),
           "- (판단) 법령 글만으로는 금융지주회사는 시행령 제6조제3항 제1~4호에 들지 않으므로 위험관리위원회 설치 예외 대상이 아닌 것으로 "
           "읽힌다. 제5호 고시 위임의 내용은 확인하지 못했다.",
           "- note: 금융지주회사감독규정 제30조는 「이사회 내에 리스크관리를 위한 위원회를 두고 그 업무를 담당하게 할 수 있다」(5절)로, "
           "지배구조법 제16조제1항(「설치하여야 한다」)과 문구가 다르다.", "",
           "② 위험관리책임자와 준법감시인 겸직 허용 범위", "",
           "- note: 법 제29조는 준법감시인·위험관리책임자가 담당해서는 안 되는 업무를 정하고, 제5호를 시행령에 맡긴다. 시행령 제24조제2항은 "
           "제5호의 업무를 「1. 위험관리책임자: … 준법감시인의 내부통제 관련 업무 2. 준법감시인: … 위험관리책임자의 위험 점검ㆍ 관리 업무」로 "
           "정하고, 단서로 「제20조제2항에 따른 금융회사 및 외국금융회사의 자산총액 7천억원 미만인 국내지점(…)」은 겸직할 수 있다고 한다.",
           "- note: 시행령 제20조제2항 각 호는 제6조제3항과 같은 꼴(상호저축은행 7천억원 미만, 금융투자업자 5조원 미만(운용재산 20조원 이상 "
           "제외), 보험회사·여신전문금융회사 5조원 미만, 금융위원회 고시 자; 단서 주권상장법인 자산총액 2조원 이상 제외)이다. 제2항 글에 "
           "「금융지주회사」 낱말: %s. 감독규정에서 「영 제20조」 인용: %s → 제5호 고시 내용은 추출 범위에 없음." % (
               "있음" if fhc_202 else "나오지 않음", "· ".join(ref20) if ref20 else "찾지 못함"),
           "- note: 법 제29조제4호는 「금융지주회사의 경우에는 자회사등의 업무(금융지주회사의 위험관리책임자가 그 소속 자회사등의 위험관리업무를 "
           "담당하는 경우는 제외한다)」를 금지 업무로 둔다. 시행령 제11조제2항제2호 단서(보충)는 금융지주회사 감사위원·준법감시인·위험관리책임자가 "
           "자회사등에서 같은 업무를 겸직하는 경우를 승인 대상에서 뺀다.",
           "- (판단) 법령 글만으로는 금융지주회사는 시행령 제20조제2항 제1~4호에 들지 않으므로 위험관리책임자·준법감시인 상호 겸직 허용(제24조제2항 "
           "단서) 범위에 들어가지 않는 것으로 읽힌다. 다만 지주 위험관리책임자가 소속 자회사등의 위험관리업무를 맡는 것은 법 제29조제4호 괄호가 "
           "금지에서 뺀다.", ""]
    judg.append("9-1 지배구조법 시행령 확인 ①: 금융지주회사는 시행령 제6조제3항 1~4호에 없어 위험관리위원회 설치 예외 대상이 아닌 것으로 읽힘(판단; "
                "5호 고시 내용은 추출 범위에 없음).")
    judg.append("9-1 지배구조법 시행령 확인 ②: 금융지주회사는 시행령 제20조제2항 1~4호에 없어 CRO·준법감시인 상호 겸직 허용(제24조제2항 단서) 범위 밖으로 "
                "읽힘(판단). 법 제29조제4호 괄호(지주 CRO 의 자회사 위험관리업무 담당)는 별개.")
    notgots.append(dict(item="지배구조법 시행령 제6조제3항제5호·제20조제2항제5호의 「금융위원회가 정하여 고시하는 자」 내용",
                        how="금융회사 지배구조 감독규정 현행 XML(2100000285614) 조문내용 전체에서 정규식 「영 제6조」「영 제20조」「영 제24조」 검색 — 0건",
                        reason="추출 범위에 없음 — 다른 고시(예: 금융투자업규정 등)는 찾지 않음"))
    gots.append(dict(item="금융회사의 지배구조에 관한 법률 제3조제3항, 제16조, 제21조, 제25조, 제27조, 제28조, 제29조(시행령 인용 조문) + 시행령 제11조제2항 본문·제2호(보충)",
                     source="법제처 Open API 법령 XML MST 277253(시행 2026-01-02, 10차 원본) · MST 290289",
                     articles="조 번호 미부여 — 「현행 법령」 칸(판단)"))

    # 4. 금융지주회사법 제22조
    fx = X["금융지주회사법"]
    r22 = _law_art(fx, "제22조")
    md += ["## 4. 금융지주회사법 제22조(%s)" % r22[1], "",
           "- 판: " + cite("금융지주회사법", "제22조"),
           "- note(지시서 대조): 지시서 「22조(전환대상자)」 — 원문 제목은 「%s」이고, 「전환대상자」는 제1항이 정의하는 용어"
           "(「그 전환계획에서 비은행지주회사와 자회사등으로 예정한 회사들(이하 이 조에서 \"전환대상자\"라 한다)」)이다." % r22[1],
           "- 주제1 표 칸(판단): 「현행 법령」 칸(적용 대상 범위).", ""] + _fence(r22[2]) + [""]
    diffs.append("9-1 금융지주회사법 제22조: 지시서 「22조(전환대상자)」 ↔ 원문 제목 「%s」 — 「전환대상자」는 제1항의 정의 용어." % r22[1])
    gots.append(dict(item="금융지주회사법 제22조 전문", source="법제처 Open API 법령 XML MST 254783(시행 2023-09-14, 11차 원본, 2026-10-07 현행 재확인)",
                     articles="조 번호 미부여 — 「현행 법령」 칸(판단)"))

    # 5. 감독규정 제30조 연혁
    hist = st["연혁"]
    body = sorted([h for h in hist if h["대상"] == "Y" and h["XML"]], key=lambda x: (x["시행일자"], x["발령일자"], x["일련번호"]))
    excl = [h for h in hist if h["대상"] != "Y"]
    from collections import Counter
    exn = Counter(h["행정규칙명"] for h in excl)
    rows30, prev, changed = [], None, []
    for h in body:
        xb = open(h["XML"], "rb").read()
        hits = [a for a in L10.rule_articles(xb) if a[0] == "제30조"]
        t = hits[0][2] if hits else ""
        ti = hits[0][1] if hits else ""
        root = ET.fromstring(xb)
        reason = " ".join("".join(e.itertext()) for e in root.iter("제개정이유"))
        buchik = ["".join(e.itertext()) for e in root.iter("부칙내용")]
        h.update(제30조제목=ti, 제30조=t, 제30조_sha=_sha(t.encode("utf-8")) if t else "", 제30조수=len(hits),
                 생성일자=(root.findtext("행정규칙기본정보/생성일자") or "").strip(),
                 개정문30=("제개정이유에 「제30조」 있음" if "제30조" in reason else "") +
                 (" 마지막 부칙에 「제30조」 있음" if buchik and "제30조" in buchik[-1] else ""))
        if prev is None or t != prev["제30조"]:
            dd = ""
            if prev is not None:
                import difflib
                sm = difflib.SequenceMatcher(None, prev["제30조"], t)
                opk = {"delete": "빠짐", "insert": "들어감", "replace": "바뀜"}
                pv = prev["제30조"]
                dd = " · ".join("%s: 「%s」→「%s」(%s→%s)" % (
                    opk[op], pv[max(0, a1 - 3):a2 + 3], t[max(0, b1 - 3):b2 + 3],
                    ",".join("U+%04X" % ord(c) for c in pv[a1:a2]) or "없음",
                    ",".join("U+%04X" % ord(c) for c in t[b1:b2]) or "없음")
                    for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal")
            changed.append((h, dd))
        h["직전판과같음"] = "" if prev is None else ("Y" if t == prev["제30조"] else "N")
        rows30.append(h)
        prev = h
    before = [h for h in body if h["시행일자"] < "20160801"][-1]
    before2 = [h for h in body if h["시행일자"] < "20160801"][-2]
    after = [h for h in body if h["시행일자"] >= "20160801"][0]
    fhc_cur = res["감독규정"]
    bulks = [e for e in excl if e["행정규칙명"].replace(" ", "") != "금융지주회사감독규정시행세칙"]
    for e in bulks:
        if e["XML"]:
            broot = ET.fromstring(open(e["XML"], "rb").read())
            barts = ["".join(x.itertext()) for x in broot.iter("조문내용")]
            e["개정문꼴"] = all(re.match(r"^제\d+조\(「[^」]+」의 개정\)", a.strip()) for a in barts if a.strip())
            e["제30조언급"] = any("제30조" in "".join(x.itertext()) for x in broot.iter())
        else:
            e["개정문꼴"], e["제30조언급"] = None, None
        e["본문판"] = [h["일련번호"] for h in body if h["발령번호"] == e["발령번호"]]
    bulk_ok = all(e["개정문꼴"] for e in bulks)
    bulk_no30 = all(e["제30조언급"] is False for e in bulks)
    bulk_twin = all(e["본문판"] for e in bulks)
    md += ["## 5. 금융지주회사감독규정 제30조의 제정·개정 연혁", "",
           "- 방법: `lawSearch.do target=admrul query=금융지주회사감독규정 nw=2 display=100`(쪽 넘김) → 목록 %d건(totalCnt 와 같음, 1쪽). "
           "이름이 정확히 「금융지주회사감독규정」인 본문 판 %d건을 시행일 순으로 놓고 판마다 `lawService.do target=admrul ID=<일련번호>` XML 의 "
           "제30조 조문내용을 뽑아 직전 판과 글자 단위로 비교했다. 현행 판(%s)과 2025-10-01 판(2100000266376)은 10차 원본을 썼고 나머지 %d판은 "
           "13차에 받아 `dart_out/raw/web13/law91/` 에 두었다. 목록 응답은 OC 를 가린 사본만 저장(`_연혁목록_금융지주회사감독규정_p1.xml`)." % (
               len(hist), len(body), fhc_cur["현행_일련번호"], sum(1 for h in body if h["재사용"].startswith("N"))),
           "- 제외: " + " · ".join("「%s」 %d건" % (k, v) for k, v in exn.items()) +
           ". 시행세칙은 검색어 부분일치로 함께 나온 다른 행정규칙이다. 이름이 다른 개정 고시 %d건은 XML 을 받아 확인했다 — 조문이 모두 "
           "「제N조(「…」의 개정)」로 시작하는 개정문인가: %s · XML 어디에든 「제30조」 낱말: %s · 같은 발령번호의 본문 판이 목록에 따로 있음: %s"
           "(아래 표 「개정 고시」 열). 그래서 본문 판이 아니라고 보고 제외했다." % (
               len(bulks), "예" if bulk_ok else "아님(표 참조)", "없음" if bulk_no30 else "있음(표 참조)", "예" if bulk_twin else "일부 없음"),
           "- 한계: ① 현행 본문의 개정 표기 날짜 가운데 목록의 발령·시행일과 맞지 않는 것이 있다(2001.7.3, 2002.9.23, 2010.1.19, 2012.12.26, "
           "2014.2.10, 2016.8.1, 2023.4.14) — 예: 「(2002. 9. 23)」 표기는 2004-03-31 판에 처음 나오고 그 사이 판은 목록에 없다. API 연혁 목록이 "
           "모든 개정 판을 담고 있다고 보장되지 않는다. ② 2021-10-14 판 XML(생성일자 20231215)에 「<삭제> (2023. 4. 14)」가 들어 있다 — 연혁 판 "
           "XML 이 당시 고시 원문 그대로가 아닐 수 있다. ③ 아래 「달라진 글자」가 실제 개정인지 DB 입력 차이인지는 확인하지 못했다(그 판 XML 의 "
           "제개정이유·마지막 부칙에 「제30조」가 있는지만 봤다).", ""]
    md += ["### 5-1 제30조 글이 직전 판과 달라진 판", "",
           "| 판(일련번호) | 발령일 | 시행일 | 발령번호 · 제개정 | 제30조 제목 | 달라진 글자(직전 판 → 이 판) | 개정문에 제30조 |", "|---|---|---|---|---|---|---|"]
    for h, dd in changed:
        md.append("| %s | %s | %s | %s · %s | %s | %s | %s |" % (
            h["일련번호"], _d(h["발령일자"]), _d(h["시행일자"]), h["발령번호"], h["제개정구분"], h["제30조제목"],
            dd or "(제정 — 첫 판)", h["개정문30"] or "없음"))
    md += ["", "- note: 제30조 제목은 38판 모두 「%s」. 제정 판 이후 달라진 것은 「각 호」→「각호」 띄어쓰기, 「심의·의결」의 가운뎃점 빠짐(2008-03-28 판)"
           "·되살아남(2008-04-07 판), 가운뎃점 글자 U+00B7→U+318D(2021-06-09 판)뿐이고 나머지 글자는 같다(기계적 비교)." % (
               "·".join(sorted({h["제30조제목"] for h in body}))), ""]
    for h, dd in changed:
        md += ["제30조 — %s 판(발령 %s · 시행 %s · %s) · 인용: [금융지주회사감독규정 · 일련번호 %s · %s · 제30조 조문내용 · 수집 %s]" % (
            h["일련번호"], _d(h["발령일자"]), _d(h["시행일자"]), h["제개정구분"], h["일련번호"], h["출처URL"], (h["수집"] or "")[:10]), ""] + \
            _fence(h["제30조"]) + [""]
    md += ["### 5-2 지배구조법 시행(2016-08-01) 앞뒤 판", "",
           "- 직전 판: %s(발령 %s · 시행 %s · 제%s호 · %s) — 제30조 sha256 `%s`" % (
               before["일련번호"], _d(before["발령일자"]), _d(before["시행일자"]), before["발령번호"], before["제개정구분"], before["제30조_sha"]),
           "- 직후 판: %s(발령 %s · 시행 %s · 제%s호 · %s) — 제30조 sha256 `%s`" % (
               after["일련번호"], _d(after["발령일자"]), _d(after["시행일자"]), after["발령번호"], after["제개정구분"], after["제30조_sha"]),
           "- note: 두 판의 제30조 글은 %s. 2016-07-27 판(제2016-29호)에서 제13조의13(임원의 자격요건)·제13조의14(경영의 투명성 등 요건)·"
           "제13조의15(임직원의 겸직기준 등)·제13조의16(내부통제기준)이 「<삭 제> (2016. 8.1)」로 바뀌었으나 제30조는 바뀌지 않았다(기계적 비교)." % (
               "같다(글자 단위)" if before["제30조"] == after["제30조"] else "다르다"),
           "- note: 그보다 한 판 앞인 %s(발령·시행 %s, 제%s호)에는 제13조의13~제13조의16 본문이 아직 있다. 이 판의 제30조도 위 두 판과 %s." % (
               before2["일련번호"], _d(before2["시행일자"]), before2["발령번호"],
               "같다(글자 단위)" if before2["제30조"] == before["제30조"] else "다르다"),
           "- (판단) 지배구조법 시행 전후로 금융지주회사감독규정 제30조 문구는 바뀌지 않은 것으로 보인다(목록에 없는 판이 있을 수 있음 — 5절 한계 ①).", ""]
    md += ["직전 판 제30조 · 인용: [금융지주회사감독규정 · 일련번호 %s · %s · 제30조 · 수집 %s]" % (
        before["일련번호"], before["출처URL"], (before["수집"] or "")[:10]), ""] + _fence(before["제30조"]) + [""]
    md += ["직후 판 제30조 · 인용: [금융지주회사감독규정 · 일련번호 %s · %s · 제30조 · 수집 %s]" % (
        after["일련번호"], after["출처URL"], (after["수집"] or "")[:10]), ""] + _fence(after["제30조"]) + [""]
    # 개정 고시 ↔ 본문 판 대응
    bulk_map = {}
    for e in excl:
        if e["행정규칙명"].replace(" ", "") != "금융지주회사감독규정시행세칙":
            twin = [h["일련번호"] for h in body if h["발령번호"] == e["발령번호"]]
            bulk_map[e["일련번호"]] = twin
    md += ["### 5-3 판 전체 목록(%d판, 시행일 순)" % len(body), "",
           "| # | 일련번호 | 발령일 | 시행일 | 발령번호 | 제개정 | 제30조 제목 | 제30조 sha256(앞 12) | 직전 판과 같음 | XML | 개정 고시 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, h in enumerate(body, 1):
        tw = [e for e in excl if e["발령번호"] == h["발령번호"] and e["행정규칙명"].replace(" ", "") != "금융지주회사감독규정시행세칙"]
        md.append("| %d | %s | %s | %s | %s | %s | %s | `%s` | %s | `%s` | %s |" % (
            i, h["일련번호"], _d(h["발령일자"]), _d(h["시행일자"]), h["발령번호"], h["제개정구분"], h["제30조제목"],
            h["제30조_sha"][:12], h["직전판과같음"] or "(첫 판)", h["XML"],
            " ".join("%s「%s」" % (e["일련번호"], e["행정규칙명"]) for e in tw) or ""))
    md += ["", "제외한 개정 고시 3건:", "", "| 일련번호 | 이름 | 발령일 | 시행일 | 발령번호 | 제개정 | 제외 사유 | 같은 발령번호 본문 판 | XML |",
           "|---|---|---|---|---|---|---|---|---|"]
    for e in excl:
        if e["행정규칙명"].replace(" ", "") == "금융지주회사감독규정시행세칙":
            continue
        md.append("| %s | %s | %s | %s | %s | %s | 개정문 꼴 %s — 본문 판 아님; 「제30조」 낱말 %s | %s | `%s` |" % (
            e["일련번호"], e["행정규칙명"], _d(e["발령일자"]), _d(e["시행일자"]), e["발령번호"], e["제개정구분"],
            "예" if e.get("개정문꼴") else "확인 못 함", "없음" if e.get("제30조언급") is False else "있음/미확인",
            ", ".join(bulk_map.get(e["일련번호"]) or []) or "-", e["XML"]))
    md += [""]
    gots.append(dict(item="금융지주회사감독규정 제30조 연혁(본문 %d판, 2000-12-29 제정 ~ 2026-10-02 현행) — 바뀐 판 %d개·2016-08-01 앞뒤 판" % (
        len(body), len(changed)), source="법제처 Open API admrul 연혁 목록(nw=2) + 판별 XML", articles="조 번호 미부여 — 「현행 법령」 칸(판단)"))
    judg.append("9-1 금융지주회사감독규정 제30조: 판 사이 차이가 띄어쓰기·가운뎃점 글자뿐이라 지배구조법 시행 전후 문구 변화 없음으로 봄(판단 — API 연혁 목록이 "
                "모든 판을 담는지 보장 안 됨).")
    diffs.append("9-1 금융지주회사감독규정 연혁: 현행 본문의 개정 표기 날짜 7개(2001.7.3, 2002.9.23, 2010.1.19, 2012.12.26, 2014.2.10, 2016.8.1, 2023.4.14)가 "
                 "API 연혁 목록의 발령·시행일과 맞지 않음. 2021-10-14 판 XML(생성일자 20231215)에 「<삭제> (2023. 4. 14)」가 들어 있음.")
    diffs.append("9-1 세칙 별표 3·4·5 원문 XML 에 ASCII 「?」(0x3F)로 들어 있는 글자 %d곳(별표3 %d, 별표4 %d, 별표5 %d) — 원래 글자 미확인, 고치지 않음." % (
        len(qmarks["별표 3"]) + len(qmarks["별표 4"]) + len(q5), len(qmarks["별표 3"]), len(qmarks["별표 4"]), len(q5)))
    notgots.append(dict(item="금융지주회사감독규정 연혁 가운데 API 목록에 없는 판(개정 표기 날짜로 추정되는 판)",
                        how="lawSearch.do target=admrul query=금융지주회사감독규정 nw=2 display=100 page=1(totalCnt 86, 1쪽에 다 옴)",
                        reason="추출 범위에 없음 — 목록에 없는 판은 받지 못함(제30조 글이 앞뒤 판에서 같아 영향은 작다고 봄, 판단)"))

    # 6. 모범규준 조 행 후보(판단) — 사용자 지시서 9-4 에 적힌 조 번호·주제와 낱말이 겹치는 원문 위치만
    a3 = _annex(sx, "0003")["글"]
    a5t = a5["글"]
    g8 = _rule_art(gx, "제8조")[2]
    g13 = _rule_art(gx, "제13조")[2]
    d22 = _law_art(dx, "제22조")[2]
    l21 = _law_art(lx, "제21조")[2]
    f30 = _rule_art(X["감독규정"], "제30조")[2]
    cand = [
        ("3조", "위험이 경미한 자회사를 적용에서 빼는 기준", "세칙 제12조제2항제5호", h2,
         "그 밖에 주력자회사의 건전경영에 미치는 영향이 적어 평가의 실익이 낮다고 인정되는 회사"),
        ("4조·5조", "위험관리 철학·원칙", "지배구조법 시행령 제22조제1항제1호", d22, "위험관리의 기본방침"),
        ("4조·5조", "위험관리 철학·원칙", "지배구조법 제21조제1호", l21, "위험관리의 기본방침 및 전략 수립"),
        ("4조·5조", "위험관리 철학·원칙", "금융지주회사감독규정 제30조제1호", f30, "경영전략에 부합하는 리스크관리 기본방침 수립"),
        ("21조", "신용위험", "세칙 [별표 3] 재무상태 자산건전성(A)", a3, "·신용리스크 관리의 적정성"),
        ("21조", "신용위험", "세칙 [별표 5] 5-2", a5t, "5-2. 신용리스크관리"),
        ("22조", "시장위험", "세칙 [별표 5] 5-3", a5t, "5-3. 시장리스크관리"),
        ("28조", "통합리스크관리시스템", "세칙 [별표 3] 리스크관리(R) 리스크 모니터링 및 보고", a3, "·경영정보시스템(MIS)의 적정성"),
        ("28조", "통합리스크관리시스템", "지배구조 감독규정 제8조제2호·제13조제1항제6호", g8 + "\n" + g13, "위험관리정보시스템의 운영"),
        ("34조", "해외위험", "지배구조 감독규정 제8조제4호(제5호도 국외 현지법인·국외 지점 언급)", g8, "각 국외 현지법인 및 국외지점의 상황을 고려한 위기상황분석"),
        ("53조", "위기대응조직", "지배구조 감독규정 제13조제1항제1호", g13, "금융사고 등 우발상황에 대한 위험관리 비상계획"),
        ("53조", "위기대응조직", "세칙 [별표 3] 자본적정성(C)·유동성(L) 비계량항목", a3, "·위기상황분석 및 비상계획의 적정성"),
    ]
    md += ["## 6. 모범규준 조 행 후보 (판단)", "",
           "- note: 사용자 지시서 9-4 에 조 번호와 주제가 함께 적힌 조(3·4·5·21·22·24·27·28·30·34·53·55조)만 대상으로, 위 원문 가운데 "
           "그 주제 낱말과 겹치는 문구가 있는 곳을 적는다. 문구는 원문 그대로(스크립트가 원문 안에 있는지 확인), 조 대응은 전부 판단이다. "
           "24조(금리위험)·27조(전략·평판위험)·30조(적합성 검증)·55조(조기경보)와 겹치는 문구는 9-1 원문에서 찾지 못했다(추출 범위에 없음 — "
           "검색어 「금리」「평판」「적합성」「검증」「조기경보」를 위 원문에 넣어 봄; 「전략」은 「위험관리의 기본방침 및 전략 수립」처럼 다른 뜻으로만 나옴).", "",
           "| 모범규준 조(사용자 9-4 표기) | 주제(사용자 표기) | 9-1 원문 위치 | 원문 문구 |", "|---|---|---|---|"]
    for jo, topic, where, src, phrase in cand:
        if phrase in src:
            md.append("| %s (판단) | %s | %s | 「%s」 |" % (jo, topic, where, phrase))
    probe = "\n".join([a3, _annex(sx, "0003", "01")["글"], _annex(sx, "0004")["글"], a5t, t12, g8, _rule_art(gx, "제10조")[2], g13,
                       _law_hang(dx, "제6조", 3), _law_art(dx, "제20조")[2], d22, _law_art(dx, "제24조")[2], s11,
                       q3] + [_law_art(lx, j)[2] for j in ("제16조", "제21조", "제25조", "제27조", "제28조", "제29조")] +
                      [r22[2], f30])
    hitw = {w: (w in probe) for w in ("금리", "평판", "적합성", "검증", "조기경보", "전략")}
    md += ["", "- note: 위 검색어가 9-1 에서 옮긴 원문 전체(세칙 별표 3·3-1·4·5 전문과 제12조 전문, 지배구조 감독규정 제8·10·13조, 시행령 "
           "제6조제3항·제20·22·24조·제11조제2항, 법 제3조제3항·제16·21·25·27·28·29조, 금융지주회사법 제22조, 감독규정 제30조)에 나오는지: " + " · ".join("「%s」 %s" % (w, "나옴(다른 뜻 — 조 대응 안 함)" if v else "안 나옴") for w, v in hitw.items()) + ".", ""]
    judg.append("9-1 → 모범규준 조 행 후보 표(6절): 사용자 9-4 의 조 번호·주제와 원문 문구가 겹치는 곳에만 조 번호를 붙임 — 대응 자체는 전부 판단.")

    # 7. 정리표
    md += ["## 7. 정리 — 받은 것 / 받지 못한 것 / 원문과 다른 것", "",
           "| 구분 | 항목 | 출처·방법 | 주제1 표 칸·조 번호 |", "|---|---|---|---|"]
    for g in gots:
        md.append("| 받은 것 | %s | %s | %s |" % (g["item"], g["source"], g["articles"]))
    for n in notgots:
        md.append("| 받지 못한 것 | %s | %s | %s |" % (n["item"], n["how"], n["reason"]))
    for d in diffs:
        md.append("| 원문과 다른 것 | %s | | |" % d)
    md += ["", "판단이 들어간 곳:", ""] + ["- (판단) " + j for j in judg] + [""]
    os.makedirs(OUT, exist_ok=True)
    text = "\n".join(md) + "\n"
    with open(MD, "w", encoding="utf-8") as f:
        f.write(text)

    # CSV
    cols = ["법령명", "종류", "용도", "일련번호", "시행일자", "발령_공포일자", "발령번호", "제개정구분", "원문XML", "sha256", "출처URL",
            "수집일시", "현행재확인_20261007", "재사용", "제30조_제목", "제30조_sha256", "제30조_직전판과같음", "note"]
    use = {"세칙": "9-1-1 별표3·3-1·4·5, 제12조⑥⑧", "지배구조감독규정": "9-1-2 제8조·제10조·제13조",
           "지배구조법": "9-1-3 인용 조문(제3조③·16·21·25·27·28·29)", "지배구조법시행령": "9-1-3 제6조③·20·22·24(+11조②)",
           "금융지주회사법": "9-1-4 제22조", "감독규정": "9-1-5 제30조 연혁(현행 판)"}
    out = []
    for k, r in res.items():
        out.append({"법령명": r["법령명"], "종류": r["종류"], "용도": use[k], "일련번호": r["현행_일련번호"],
                    "시행일자": r["현행_시행일자"], "발령_공포일자": r["현행_발령공포일"], "발령번호": r.get("기존_발령번호", ""),
                    "제개정구분": r["현행_제개정"], "원문XML": r["사용XML"], "sha256": r["사용_sha256"],
                    "출처URL": M[k].get("출처URL", ""), "수집일시": M[k].get("fetched_at", ""),
                    "현행재확인_20261007": ("같은 판(일련번호·시행일자·발령/공포일자 일치) — 기존 XML 사용; 확인 %s" % recheck_at
                                         if r["같은판"] == "Y" else "다른 판 — 새로 받음"),
                    "재사용": "Y(이전 차수 원본 — 다시 받지 않음)", "제30조_제목": "", "제30조_sha256": "", "제30조_직전판과같음": "",
                    "note": ("시행예정판: %s" % r["시행예정판"]) + (" · " + REFETCH_NOTE if k in REFETCHED else "")})
    for h in body:
        out.append({"법령명": FHC_RULE, "종류": "행정규칙(연혁 판)", "용도": "9-1-5 제30조 연혁", "일련번호": h["일련번호"],
                    "시행일자": h["시행일자"], "발령_공포일자": h["발령일자"], "발령번호": h["발령번호"], "제개정구분": h["제개정구분"],
                    "원문XML": h["XML"], "sha256": h["sha256"], "출처URL": h["출처URL"], "수집일시": h["수집"],
                    "현행재확인_20261007": "현행" if h["현행연혁구분"] == "현행" else "연혁(API 현행연혁구분=%s)" % h["현행연혁구분"],
                    "재사용": h["재사용"], "제30조_제목": h["제30조제목"], "제30조_sha256": h["제30조_sha"],
                    "제30조_직전판과같음": h["직전판과같음"] or "(첫 판)",
                    "note": "XML 생성일자 %s%s" % (h["생성일자"], (" · " + h["개정문30"]) if h["개정문30"] else "")})
    for e in excl:
        if e["행정규칙명"].replace(" ", "") == "금융지주회사감독규정시행세칙":
            continue
        out.append({"법령명": e["행정규칙명"], "종류": "행정규칙(개정 고시 — 제외)", "용도": "9-1-5 제외 확인", "일련번호": e["일련번호"],
                    "시행일자": e["시행일자"], "발령_공포일자": e["발령일자"], "발령번호": e["발령번호"], "제개정구분": e["제개정구분"],
                    "원문XML": e["XML"], "sha256": e["sha256"], "출처URL": e["출처URL"], "수집일시": e["수집"],
                    "현행재확인_20261007": "연혁", "재사용": "N", "제30조_제목": "", "제30조_sha256": "", "제30조_직전판과같음": "",
                    "note": "개정문(본문 판 아님) — 「제30조」 낱말 없음 · 같은 발령번호 본문 판 %s" % (
                        ", ".join(bulk_map.get(e["일련번호"]) or []) or "-")})
    out.append({"법령명": FHC_RULE + "(연혁 목록)", "종류": "검색 응답", "용도": "9-1-5 연혁 목록", "일련번호": "",
                "시행일자": "", "발령_공포일자": "", "발령번호": "", "제개정구분": "",
                "원문XML": st["연혁목록쪽"][0]["파일"], "sha256": st["연혁목록쪽"][0]["sha256"],
                "출처URL": st["연혁목록쪽"][0]["출처URL"], "수집일시": st["연혁목록쪽"][0]["수집"], "현행재확인_20261007": "",
                "재사용": "N", "제30조_제목": "", "제30조_sha256": "", "제30조_직전판과같음": "",
                "note": "목록 %d건(본문 판 %d · 시행세칙 %d · 개정 고시 3) — 응답 본문의 OC 값을 ***로 가린 사본(원 응답 바이트와 다름)" % (
                    len(hist), len(body), exn.get("금융지주회사감독규정시행세칙", 0))})
    write_csv(CSV, cols, out)
    if os.environ.get("LAW91_SUMMARY"):
        print(json.dumps(dict(got=gots, not_got=notgots, diffs=diffs, judgments=judg), ensure_ascii=False, indent=1))
    print("md → %s (%d줄) · csv → %s (%d행)" % (MD, len(md), CSV, len(out)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "bulk":
        bulk()
    elif cmd == "md":
        build_md()  # noqa: F821 — 아래에서 정의
    else:
        print(__doc__)
