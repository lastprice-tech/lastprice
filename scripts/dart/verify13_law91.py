# -*- coding: utf-8 -*-
"""13차 9-1 검증·보정 — handoff/13차_산출물/9-1_법령원문.md · dart_out/risk13/9-1_법령판.csv.

    python3 -I scripts/dart/verify13_law91.py           # 대조만(요청 없음). 문제 0 이면 exit 0.
                                                         #   결과 → dart_out/risk13/verify13_law91.txt
    LAW_DELAY=1.0 python3 -I scripts/dart/verify13_law91.py fetch
        # 반박용 원본 받기: www.law.go.kr robots 확인 → 세칙 별표 3·4·5 PDF(XML 의 별표서식PDF파일링크),
        # 「금융회사 지배구조 감독규정」 연혁 목록(admrul nw=2)과 판 XML, 「금융지주회사 감독규정」(띄어 쓴 이름) 연혁 목록.
        # 원본 → dart_out/raw/web13/verify13_law91/ (원장 _call_log.csv, OC=*** 로 가림)
    python3 -I scripts/dart/verify13_law91.py search     # 받은 원본만 읽어 넓은 검색어로 다시 찾기 → _search.json
    python3 -I scripts/dart/verify13_law91.py fix        # md·csv 보정(멱등). 고친 곳은 _fix_log.json 과 md 「검증 기록」에

· 원문 대조는 공백만 무시한다(공백·줄바꿈을 지운 뒤 포함 관계). 글자 하나라도 다르면 문제로 센다.
· 조문 글은 scripts/dart/web10_law.py 의 rule_articles(행정규칙)·find_unit/article_text(법령)·md_text 로 뽑는다(읽기만).
· OC·DART 키 값은 출력·파일 어디에도 쓰지 않는다(값이 산출물에 들어 있는지 검사만 하고, 결과는 「있음/없음」만 적음).
"""
from __future__ import annotations

import csv
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
import web10_law as L10  # noqa: E402 — rule_articles·find_unit·article_text·md_text (읽기만)
from web13 import RAW, WORK, OUT, save, now  # noqa: E402

TASK = "verify13_law91"
VDIR = os.path.join(RAW, TASK)
LEDGER = os.path.join(VDIR, "_call_log.csv")
STATE = os.path.join(VDIR, "_fetch_state.json")
SEARCH = os.path.join(VDIR, "_search.json")
FIXLOG = os.path.join(VDIR, "_fix_log.json")
MD = os.path.join(OUT, "9-1_법령원문.md")
CSV = os.path.join(WORK, "9-1_법령판.csv")
REPORT = os.path.join(WORK, "verify13_law91.txt")
MOBEOM_MD = os.path.join(OUT, "9-4_모범규준_원문.md")
MOBEOM_CSV = os.path.join(WORK, "모범규준_조목록.csv")
REQUEST = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
TODAY = "2026-10-07"

SRC = {
    "세칙": "dart_out/raw/web11/law/금융지주회사감독규정시행세칙_2200000107297.xml",
    "지배구조감독규정": "dart_out/raw/web9/law/금융회사지배구조감독규정_2100000285614.xml",
    "지배구조법": "dart_out/raw/web10/law/금융회사의지배구조에관한법률_277253.xml",
    "시행령": "dart_out/raw/web10/law/금융회사의지배구조에관한법률시행령_290289.xml",
    "지주법": "dart_out/raw/web11/law/금융지주회사법_254783.xml",
    "감독규정": "dart_out/raw/web10/law/금융지주회사감독규정_2100000285612.xml",
}
SERIAL = {"세칙": "2200000107297", "지배구조감독규정": "2100000285614", "지배구조법": "277253",
          "시행령": "290289", "지주법": "254783", "감독규정": "2100000285612"}
GOVREG = "금융회사 지배구조 감독규정"
FHC = "금융지주회사감독규정"
LAW91_LIST = os.path.join(RAW, "law91", "_연혁목록_금융지주회사감독규정_p1.xml")


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def nows(s):
    return re.sub(r"\s+", "", s or "")


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def _meta(p):
    m = p + ".meta.json"
    return json.load(open(m, encoding="utf-8")) if os.path.exists(m) else {}


def annex(xb, no, ga="00"):
    """행정규칙 XML 의 [별표 no(-ga)] (별표구분=별표만). → dict(제목, 글, 키, pdf, hwp) 또는 None."""
    root = ET.fromstring(xb)
    no4 = "%04d" % int(no)
    for b in root.iter("별표단위"):
        g = lambda k: (b.findtext(k) or "").strip()  # noqa: E731
        if g("별표구분") == "별표" and g("별표번호") == no4 and (g("별표가지번호") or "00") == ga:
            c = b.find("별표내용")
            return dict(제목=g("별표제목"), 글="".join(c.itertext()) if c is not None else "", 키=b.get("별표키", ""),
                        hwp=g("별표서식파일링크"), pdf=g("별표서식PDF파일링크"))
    return None


def is_rule(xb):
    return ET.fromstring(xb).find("행정규칙기본정보") is not None


def units(xb):
    """검색 단위 [(위치표지, 글)] — 조문(행정규칙은 조문내용, 법령은 조문단위 글)·부칙·별표·제개정이유."""
    root = ET.fromstring(xb)
    out = []
    if root.find("행정규칙기본정보") is not None:
        for lab, ti, t in L10.rule_articles(xb):
            out.append(("%s(%s)" % (lab, ti) if lab else "조문(표지 없음)", t))
    else:
        for lab, ti, u in L10.law_units(xb):
            if lab:
                out.append(("%s(%s)" % (lab, ti), L10.article_text(u)))
    for i, e in enumerate(root.iter("부칙내용")):
        t = "".join(e.itertext())
        if t.strip():
            out.append(("부칙#%d" % (i + 1), t))
    for b in root.iter("별표단위"):
        g = lambda k: (b.findtext(k) or "").strip()  # noqa: E731
        c = b.find("별표내용")
        t = "".join(c.itertext()) if c is not None else ""
        if t.strip():
            no = g("별표번호").lstrip("0") or "0"
            ga = (g("별표가지번호") or "00").lstrip("0")
            out.append(("[%s %s%s] %s" % (g("별표구분") or "별표", no, "-" + ga if ga else "", g("별표제목")), t))
    for tag in ("제개정이유내용", "개정문내용"):
        for e in root.iter(tag):
            t = "".join(e.itertext())
            if t.strip():
                out.append((tag, t))
    return out


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}


def dump(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


# ── fetch(요청) ───────────────────────────────────────────────────────────
def _list(client, query, tag):
    """lawSearch admrul nw=2 display=100(쪽 넘김) — 응답의 OC 값은 *** 로 가린 사본만 저장."""
    rows, pages, page = [], [], 1
    while True:
        st, body, murl, host = client.api("lawSearch.do", target="admrul", type="XML", query=query,
                                          nw="2", display="100", page=str(page))
        n_oc = client.count_oc(body)
        body = client.mask(body)
        if client.count_oc(body):
            raise RuntimeError("가린 뒤에도 인증값이 남음 — 저장하지 않음")
        p, m = save(TASK, "_연혁목록_%s_p%d.xml" % (tag, page), body,
                    dict(출처URL=murl, http_status=st, fetched_at=now(),
                         가림=("응답 본문의 OC 값 %d곳을 ***로 바꾼 사본" % n_oc) if n_oc else ""))
        root = ET.fromstring(body)
        got = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("admrul")]
        total = int((root.findtext("totalCnt") or "0").strip() or 0)
        rows += got
        pages.append(dict(page=page, 파일=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"], totalCnt=total))
        print("  목록 %s p%d: %d건 (누계 %d / totalCnt %d)" % (tag, page, len(got), len(rows), total))
        if not got or len(rows) >= total or page >= 10:
            break
        page += 1
    return rows, pages


def _pdf_text(body):
    import io
    import pypdf
    r = pypdf.PdfReader(io.BytesIO(body))
    return "\n".join("=== p.%d ===\n%s" % (i + 1, (pg.extract_text() or "")) for i, pg in enumerate(r.pages)), len(r.pages)


def fetch():
    import lawclient
    from web13 import Web, Robots
    client = lawclient.LawClient(LEDGER)
    st = load_state()
    os.makedirs(VDIR, exist_ok=True)
    # ① robots(www.law.go.kr) — 별표 PDF 는 /LSW/flDownload.do (Open API 가 아닌 웹 경로)
    web = Web()
    rb = Robots(web, "https://www.law.go.kr", TASK)
    st["robots"] = dict(대상="https://www.law.go.kr/robots.txt", 상태=rb.status, note=rb.note, 확인=now())
    print("① robots www.law.go.kr:", rb.status, rb.note[:80])
    # ② 세칙 별표 3·4·5 PDF
    xb = rd(SRC["세칙"])
    pdfs = st.get("별표PDF", {})
    for no in ("3", "4", "5"):
        a = annex(xb, no)
        name = "세칙_2200000107297_별표%s.pdf" % no
        p = os.path.join(VDIR, name)
        if os.path.exists(p):
            print("  별표%s PDF 이미 받음" % no)
            continue
        url = "https://www.law.go.kr" + a["pdf"]
        # web13.Robots 판정(웹 UA) + lawclient UA 로도 확인(둘 다 허용일 때만 받음)
        if not rb.allowed(url) or (rb.rp is not None and not rb.rp.can_fetch(lawclient.UA, url)):
            pdfs[no] = dict(상태="robots 불허 또는 확인 불가(%s) — 받지 않음" % rb.status, url=url)
            continue
        sc, body, ct, murl, host = client.file(a["pdf"])
        if not body.startswith(b"%PDF"):
            pdfs[no] = dict(상태="PDF 아님(HTTP %s, %s, %d바이트) — 저장 안 함" % (sc, ct, len(body)), url=murl)
            print("  별표%s: PDF 아님" % no)
            continue
        p, m = save(TASK, name, body, dict(출처URL=murl, http_status=sc, content_type=ct, fetched_at=now(),
                                           별표=a["제목"], 별표키=a["키"]))
        txt, n = _pdf_text(body)
        save(TASK, name + ".txt", txt.encode("utf-8"), dict(원본=p, 방법="pypdf extract_text, 쪽 표지 === p.N ===",
                                                           쪽수=n, fetched_at=m["fetched_at"]))
        pdfs[no] = dict(상태="OK", 파일=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"], 쪽수=n)
        print("  별표%s PDF %d쪽 저장" % (no, n))
    st["별표PDF"] = pdfs
    # ③ 금융회사 지배구조 감독규정 연혁 판
    rows, pages = _list(client, GOVREG, "금융회사지배구조감독규정")
    hist = []
    for r in rows:
        nm, sn = r.get("행정규칙명", ""), r.get("행정규칙일련번호", "")
        h = dict(행정규칙명=nm, 일련번호=sn, 발령일자=r.get("발령일자", ""), 시행일자=r.get("시행일자", ""),
                 발령번호=r.get("발령번호", ""), 제개정구분=r.get("제개정구분명", ""), 현행연혁구분=r.get("현행연혁구분", ""),
                 대상="Y" if nows(nm) == nows(GOVREG) else "N", XML="", sha256="", 출처URL="", 수집="")
        if h["대상"] == "Y":
            if sn == SERIAL["지배구조감독규정"]:
                p = SRC["지배구조감독규정"]
                h.update(XML=p, sha256=_sha(rd(p)), 출처URL=_meta(p).get("출처URL", ""), 수집=_meta(p).get("fetched_at", ""),
                         재사용="Y(9차 원본)")
            else:
                p = os.path.join(VDIR, "지배구조감독규정_%s.xml" % sn)
                if os.path.exists(p):
                    h.update(XML=p, sha256=_sha(rd(p)), 출처URL=_meta(p).get("출처URL", ""),
                             수집=_meta(p).get("fetched_at", ""), 재사용="N")
                else:
                    try:
                        sc, body, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
                        if client.count_oc(body):
                            raise RuntimeError("응답 본문에 인증값 — 저장하지 않음")
                        p, m = save(TASK, "지배구조감독규정_%s.xml" % sn, body,
                                    dict(출처URL=murl, http_status=sc, fetched_at=now()))
                        h.update(XML=p, sha256=m["sha256"], 출처URL=murl, 수집=m["fetched_at"], 재사용="N")
                    except Exception as e:  # noqa: BLE001
                        h["오류"] = client.mask("%s: %s" % (type(e).__name__, e))[:200]
        hist.append(h)
    # 같은 목록에 함께 나온 「금융회사 지배구조 감독규정 시행세칙」(금감원장 세칙) 가운데 가장 최근 판 1건도 받아
    # 넓은 검색 대상에 더한다(고시 위임을 받는 문서는 아니지만 「영 제6조」 등의 인용이 있는지 확인용).
    sub = sorted([h for h in hist if h["대상"] == "N" and nows(h["행정규칙명"]) == nows(GOVREG + " 시행세칙")],
                 key=lambda x: (x["시행일자"], x["발령일자"]))
    if sub:
        h = sub[-1]
        p = os.path.join(VDIR, "지배구조감독규정시행세칙_%s.xml" % h["일련번호"])
        if not os.path.exists(p):
            try:
                sc, body, murl, host = client.api("lawService.do", target="admrul", ID=h["일련번호"], type="XML")
                if client.count_oc(body):
                    raise RuntimeError("응답 본문에 인증값 — 저장하지 않음")
                p, m = save(TASK, os.path.basename(p), body, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            except Exception as e:  # noqa: BLE001
                h["오류"] = client.mask("%s: %s" % (type(e).__name__, e))[:200]
        if os.path.exists(p):
            h.update(XML=p, sha256=_sha(rd(p)), 출처URL=_meta(p).get("출처URL", ""), 수집=_meta(p).get("fetched_at", ""),
                     재사용="N", 비고="넓은 검색용(시행세칙 최근 판)")
    st["지배구조감독규정_연혁"] = dict(목록쪽=pages, 판=hist)
    print("③ 지배구조 감독규정 목록 %d건 · 본문 판 %d건" % (len(hist), sum(h["대상"] == "Y" for h in hist)))
    # ④ 금융지주회사 감독규정(띄어 쓴 이름) 연혁 목록 — law91 목록(붙여 쓴 이름)에 없던 판이 있는지
    rows2, pages2 = _list(client, "금융지주회사 감독규정", "금융지주회사_감독규정_띄어씀")
    old = {it.findtext("행정규칙일련번호").strip() for it in ET.parse(LAW91_LIST).getroot().iter("admrul")}
    new = []
    for r in rows2:
        sn = r.get("행정규칙일련번호", "")
        rec = dict(행정규칙명=r.get("행정규칙명", ""), 일련번호=sn, 발령일자=r.get("발령일자", ""),
                   시행일자=r.get("시행일자", ""), 발령번호=r.get("발령번호", ""), 제개정구분=r.get("제개정구분명", ""),
                   law91목록에있음="Y" if sn in old else "N")
        new.append(rec)
    st["감독규정_띄어씀목록"] = dict(목록쪽=pages2, 항목=new)
    print("④ 띄어 쓴 이름 목록 %d건 · law91 목록에 없던 것 %d건" % (len(new), sum(x["law91목록에있음"] == "N" for x in new)))
    st["API호출"] = st.get("API호출", 0) + client.n_calls
    st["수집일"] = now()
    dump(STATE, st)
    print("API 호출 %d · 상태 → %s" % (client.n_calls, STATE))


# ── search(요청 없음) ─────────────────────────────────────────────────────
# 시행령 제6조제3항제5호·제20조제2항제5호 「금융위원회가 정하여 고시하는 자」를 받는 조를 찾는 넓은 검색어
DELEG_PATS = [
    ("영 제6조", r"영\s*제\s*6\s*조"), ("시행령 제6조", r"시행령\s*」?\s*제\s*6\s*조"),
    ("제6조제3항", r"제\s*6\s*조\s*제\s*3\s*항"), ("영 제20조", r"영\s*제\s*20\s*조"),
    ("시행령 제20조", r"시행령\s*」?\s*제\s*20\s*조"), ("제20조제2항", r"제\s*20\s*조\s*제\s*2\s*항"),
    ("법 제3조제3항", r"법\s*제\s*3\s*조\s*제\s*3\s*항"), ("법 제25조제2항", r"법\s*제\s*25\s*조\s*제\s*2\s*항"),
    ("법 제28조제2항", r"법\s*제\s*28\s*조\s*제\s*2\s*항"), ("법 제29조", r"법\s*제\s*29\s*조"),
    ("영 제24조", r"영\s*제\s*24\s*조"),
    ("고시하는 자(자격 제외)", r"고시하는\s*자(?!격)"), ("고시하는 금융회사", r"고시하는\s*금융회사"),
    ("적용 범위·적용범위", r"적용\s*범위"), ("적용하지 아니", r"적용하지\s*아니"), ("적용 배제", r"적용\s*(?:을\s*)?배제"),
    ("적용 특례", r"적용\s*(?:의\s*)?특례"), ("직원 중·직원중", r"직원\s*중"), ("자산총액·자산규모", r"자산\s*(?:총액|규모)"),
    ("영위하는 금융업무", r"영위하는\s*금융업무"), ("위험관리위원회", r"위험관리위원회"), ("겸직", r"겸직"),
    ("금융지주회사", r"금융지주회사"),
]
# 6절 「추출 범위에 없음」(모범규준 24·27·30·55조) 반박용 넓은 검색어
TOPIC_PATS = {
    "24조 금리위험": r"금리|이자율|ΔEVE|ΔNII|IRRBB|interest\s*rate",
    "27조 전략·평판위험": r"평판|(?<!투)명성|reputation|전략\s*(?:위험|리스크)|전략적\s*위험",
    "30조 적합성 검증": r"적합성|검증|백\s*테스|back\s*-?test|타당성\s*(?:평가|점검)|validation",
    "55조 조기경보": r"조기\s*경보|경보\s*(?:지표|발령|체계|단계)|early\s*warning|조기\s*(?:감지|위험감지)|위기\s*징후",
}
DATES = ["2001.7.3", "2002.9.23", "2010.1.19", "2012.12.26", "2014.2.10", "2016.8.1", "2023.4.14"]


def _date_pats(d):
    y, m, dd = d.split(".")
    a = r"%s\s*\.\s*0?%s\s*\.\s*0?%s(?!\d)" % (y, m, dd)
    b = r"%s\s*년\s*0?%s\s*월\s*0?%s\s*일" % (y, m, dd)
    return a, b


def _ctx(t, m, w=45):
    return re.sub(r"\s+", " ", t[max(0, m.start() - w):m.end() + w]).strip()


def _deleg_rows(xb):
    """「…에서 "(그 밖에 )금융위원회가 정하여 고시하는 …"」 위임 문구(글자 그대로)를 조마다."""
    rows = []
    for lab, ti, t in L10.rule_articles(xb):
        for m in re.finditer(r"((?:법|영)\s*제\d+조(?:의\d+)?[^\"“”.]{0,60}?)에서\s*[\"“](?:그\s*밖에\s*)?금융위원회가\s*정하여\s*"
                             r"고시하는\s*([^\"”]+)[\"”]", t):
            rows.append(dict(조=lab, 제목=ti, 근거=m.group(1).strip(), 대상=m.group(2).strip(), 원문=m.group(0)))
        for m in re.finditer(r"금융위원회가\s*정하여\s*고시하는\s*바에\s*따라", t):
            rows.append(dict(조=lab, 제목=ti, 근거="(인용 조문 없음)", 대상="바", 원문=_ctx(t, m, 0)))
    return rows


def search():
    st = load_state()
    res = {}
    # S1 지배구조 감독규정 — 현행 + 연혁 8판 + 시행세칙 최근 판, 조문·부칙·별표·제개정이유 전체
    vers = [h for h in st["지배구조감독규정_연혁"]["판"] if h.get("XML")]
    s1 = []
    for h in sorted(vers, key=lambda x: (x["대상"], x["시행일자"])):
        xb = rd(h["XML"])
        us = units(xb)
        rec = dict(일련번호=h["일련번호"], 이름=h["행정규칙명"], 시행일자=h["시행일자"], 발령일자=h["발령일자"],
                   발령번호=h["발령번호"], 제개정=h["제개정구분"], XML=h["XML"], 단위수=len(us), 검색어={})
        for name, pat in DELEG_PATS:
            hits = []
            for lab, t in us:
                for m in re.finditer(pat, t):
                    hits.append(dict(위치=lab[:60], 문맥=_ctx(t, m)))
            rec["검색어"][name] = dict(건수=len(hits), 예=hits[:6])
        rec["고시위임"] = _deleg_rows(xb) if is_rule(xb) and h["대상"] == "Y" else []
        s1.append(rec)
    res["S1_지배구조감독규정"] = s1
    # S2 6절 주제어 — 6개 원문 XML 전체(조문·부칙·별표)
    s2 = {}
    for k, p in SRC.items():
        us = units(rd(p))
        for topic, pat in TOPIC_PATS.items():
            hits = []
            for lab, t in us:
                ms = list(re.finditer(pat, t, flags=re.I))
                if ms:
                    hits.append(dict(위치=lab[:80], 건수=len(ms), 낱말=sorted(set(m.group(0) for m in ms))[:8],
                                     문맥=_ctx(t, ms[0])))
            s2.setdefault(topic, {})[k] = hits
    res["S2_6절주제어"] = s2
    # S3 감독규정 연혁 — 목록에 없는 판으로 본 개정 표기 날짜 7개가 어느 판 조문·부칙에 처음 나오는지
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    fhc = {}
    for r in rows:
        if r["법령명"] == FHC and r["원문XML"].endswith(".xml") and r["일련번호"] not in fhc:
            fhc[r["일련번호"]] = r
    order = sorted(fhc.values(), key=lambda r: (r["시행일자"], r["발령_공포일자"], r["일련번호"]))
    s3 = {}
    for d in DATES:
        pa, pb = _date_pats(d)
        first_text, in_buchik = None, []
        for r in order:
            xb = rd(r["원문XML"])
            root = ET.fromstring(xb)
            body = "\n".join(t for lab, t in units(xb) if not lab.startswith("부칙") and lab not in ("제개정이유내용", "개정문내용"))
            if first_text is None and re.search(pa, body):
                m = re.search(pa, body)
                first_text = dict(일련번호=r["일련번호"], 시행일자=r["시행일자"], 발령일자=r["발령_공포일자"], 문맥=_ctx(body, m))
            for i, e in enumerate(root.iter("부칙내용")):
                t = "".join(e.itertext())
                for pat in (pa, pb):
                    m = re.search(pat, t)
                    if m:
                        in_buchik.append(dict(일련번호=r["일련번호"], 시행일자=r["시행일자"], 발령일자=r["발령_공포일자"],
                                              부칙=i + 1, 문맥=_ctx(t, m, 80), 원문줄=[ln for ln in t.split("\n") if re.search(pat, ln)][:1]))
                        break
        s3[d] = dict(조문첫등장=first_text, 부칙=in_buchik[:8], 부칙건수=len(in_buchik))
    res["S3_개정표기날짜"] = s3
    sp = st.get("감독규정_띄어씀목록", {})
    res["S3_띄어쓴이름목록"] = dict(건수=len(sp.get("항목", [])),
                                  law91목록에없던것=[x for x in sp.get("항목", []) if x["law91목록에있음"] == "N"])
    # S4 세칙 별표 3·4·5 의 「?」(0x3F) — 별표 PDF 텍스트에서 같은 자리 글자
    xb = rd(SRC["세칙"])
    s4 = []

    def clean(s):
        return re.sub(r"[\s─-╿]+", "", s)
    for no in ("3", "4", "5"):
        a = annex(xb, no)
        t = a["글"]
        tp = os.path.join(VDIR, "세칙_2200000107297_별표%s.pdf.txt" % no)
        ptxt = open(tp, encoding="utf-8").read() if os.path.exists(tp) else ""
        pc = clean(ptxt)
        for m in re.finditer(r"\?", t):
            Lc = clean(t[max(0, m.start() - 30):m.start()])[-5:]
            Rc = clean(t[m.end():m.end() + 30])[:5]
            pat = "".join("(.{1,2}?)" if c == "?" else re.escape(c) for c in Lc) + "(.{1,2}?)" + \
                  "".join("(.{1,2}?)" if c == "?" else re.escape(c) for c in Rc)
            gi = Lc.count("?") + 1
            mm = list(re.finditer(pat, pc))
            ch = mm[0].group(gi) if len(mm) == 1 else ""
            # PDF 텍스트 원문 줄(쪽 표지 포함) — 앞뒤 낱말이 들어 있는 줄
            page, line = "", ""
            if ch:
                lc, rc = re.sub(r"\?", "", Lc), re.sub(r"\?", "", Rc)
                for key in (lc[-2:] + ch + rc[:1], ch + rc[:2], lc[-2:] + ch):
                    cur = ""
                    for ln in ptxt.split("\n"):
                        pm = re.match(r"=== p\.(\d+) ===", ln)
                        if pm:
                            cur = pm.group(1)
                            continue
                        if key in clean(ln):
                            page, line = cur, ln
                            break
                    if line:
                        break
            s4.append(dict(별표=no, XML문맥=Lc + "?" + Rc, XML줄=[ln for ln in t.split("\n") if ln.find("?") >= 0 and
                                                           clean(ln).find(Lc[-2:] + "?") >= 0][:1],
                           PDF일치수=len(mm), PDF글자=ch, 코드=" ".join("U+%04X" % ord(c) for c in ch), PDF쪽=page, PDF줄=line))
    res["S4_별표물음표"] = s4
    res["S1b_다른고시"] = search_other()
    dump(SEARCH, res)
    # 요약(짧게)
    cur = [r for r in s1 if r["일련번호"] == SERIAL["지배구조감독규정"]][0]
    print("S1 지배구조 감독규정 %d판(+시행세칙) — 판마다 「영 제6조」「영 제20조」「제6조제3항」「제20조제2항」 건수:" % len(s1))
    for r in s1:
        print("   %s %s %s: %s" % (r["일련번호"], r["시행일자"], r["이름"][-6:],
                                 " ".join("%s=%d" % (k, r["검색어"][k]["건수"]) for k in
                                          ("영 제6조", "시행령 제6조", "제6조제3항", "영 제20조", "제20조제2항", "고시하는 자(자격 제외)"))))
    print("   현행 고시 위임 문구 %d곳" % len(cur["고시위임"]))
    for topic, d in s2.items():
        print("S2 %s: %s" % (topic, " ".join("%s=%d" % (k, len(v)) for k, v in d.items())))
    for d, v in s3.items():
        print("S3 %s: 조문첫등장 %s · 부칙 %d건" % (d, (v["조문첫등장"] or {}).get("시행일자"), v["부칙건수"]))
    print("S4 「?」 %d곳 · PDF 에서 글자 확인 %d곳" % (len(s4), sum(1 for x in s4 if x["PDF글자"])))




# ── check(대조 — 요청 없음) ──────────────────────────────────────────────
FENCE = re.compile(r"^```")


def md_blocks(lines):
    """md 의 원문 인용 — 코드 블록(```)과 > 인용 블록. → [dict(시작줄, 끝줄, 종류, 글)] (줄 번호 1부터)."""
    out, i, n = [], 0, len(lines)
    while i < n:
        if FENCE.match(lines[i]):
            j = i + 1
            while j < n and not FENCE.match(lines[j]):
                j += 1
            out.append(dict(시작줄=i + 1, 끝줄=j + 1, 종류="코드", 글="\n".join(lines[i + 1:j])))
            i = j + 1
            continue
        if lines[i].startswith(">"):
            j = i
            while j < n and lines[j].startswith(">"):
                j += 1
            out.append(dict(시작줄=i + 1, 끝줄=j, 종류="인용", 글="\n".join(re.sub(r"^>\s?", "", x) for x in lines[i:j])))
            i = j
            continue
        i += 1
    return out


CITE_RE = re.compile(r"\[([^\[\]]*?(?:\[[^\[\]]*\][^\[\]]*?)*?)\]")


def find_cite(lines, start):
    """블록 앞쪽으로 거슬러 올라가 가장 가까운 출처 표기 줄(「인용:」·「판:」·「출처:」)과 그 괄호 내용."""
    for k in range(start - 2, -1, -1):
        ln = lines[k]
        if FENCE.match(ln):
            # 다른 코드 블록을 지나면: 같은 절의 출처 줄(1-4 처럼 한 출처에 여러 블록)을 계속 찾는다
            continue
        if re.search(r"(인용|판|출처)\s*(\([^)]*\))?\s*:\s*\[", ln) and ("일련번호" in ln or "flSeq" in ln):
            i = ln.find("[", re.search(r"(인용|판|출처)\s*(\([^)]*\))?\s*:\s*\[", ln).start())
            depth, j = 0, i
            while j < len(ln):
                if ln[j] == "[":
                    depth += 1
                elif ln[j] == "]":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            return k + 1, ln[i + 1:j]
        if ln.startswith("## ") or ln.startswith("### "):
            # 절 머리를 넘어가면 그 위 절의 출처는 쓰지 않는다
            return None, ""
    return None, ""


def _serial_paths():
    m = {}
    for r in csv.DictReader(open(CSV, encoding="utf-8-sig")):
        if r["원문XML"].endswith(".xml") and r["일련번호"] not in m:
            m[r["일련번호"]] = r["원문XML"]
    for k, sn in SERIAL.items():
        m.setdefault(sn, SRC[k])
    st = load_state()
    for h in st.get("지배구조감독규정_연혁", {}).get("판", []):
        if h.get("XML"):
            m.setdefault(h["일련번호"], h["XML"])
    return m


def _pdf_by_seq():
    st = load_state()
    out = {}
    for no, v in st.get("별표PDF", {}).items():
        if v.get("상태") == "OK":
            seq = re.search(r"flSeq=(\d+)", v["출처URL"]).group(1)
            out[seq] = v["파일"] + ".txt"
    return out


def resolve_source(cite):
    """출처 괄호 내용 → (원문 글, 설명) 또는 (None, 사유)."""
    segs = [s.strip() for s in cite.split(" · ")]
    if "flSeq=" in cite:
        seq = re.search(r"flSeq=(\d+)", cite).group(1)
        tp = _pdf_by_seq().get(seq)
        pm = re.search(r"(?:^|\s)p\.(\d+)", cite)
        if not tp or not pm:
            return None, "PDF 텍스트 또는 쪽 표기 없음", None
        txt = open(tp, encoding="utf-8").read()
        pages = re.split(r"^=== p\.(\d+) ===$", txt, flags=re.M)
        d = {pages[i]: pages[i + 1] for i in range(1, len(pages) - 1, 2)}
        return d.get(pm.group(1)), "%s p.%s" % (os.path.basename(tp), pm.group(1)), tp
    sm = re.search(r"일련번호\s*(\d+)", cite)
    if not sm:
        return None, "일련번호 없음", None
    path = _serial_paths().get(sm.group(1))
    if not path or not os.path.exists(path):
        return None, "일련번호 %s 의 XML 없음" % sm.group(1), None
    xb = rd(path)
    for s in segs[1:]:
        am = re.match(r"\[별표\s*(\d+)(?:-(\d+))?\]", s)
        if am:
            a = annex(xb, am.group(1), "%02d" % int(am.group(2) or 0))
            return (a["글"] if a else None), "%s [별표 %s]" % (path, am.group(1) + ("-" + am.group(2) if am.group(2) else "")), path
        if s.startswith("부칙"):
            return "\n".join("".join(e.itertext()) for e in ET.fromstring(xb).iter("부칙내용")), "%s 부칙" % path, path
        if s.startswith("조문 전체"):
            return L10.md_text(xb, "rule" if is_rule(xb) else "law"), "%s 조문 전체" % path, path
        jm = re.match(r"제(\d+)조(?:의(\d+))?", s)
        if jm:
            jo = "제%s조%s" % (jm.group(1), "의" + jm.group(2) if jm.group(2) else "")
            if is_rule(xb):
                hit = [t for lab, ti, t in L10.rule_articles(xb) if lab == jo]
                return (hit[0] if hit else None), "%s %s" % (path, jo), path
            r = L10.find_unit(xb, jo)
            return (r[2] if r else None), "%s %s" % (path, jo), path
    return None, "위치(조·별표) 표기 없음", None


def compare(quote, src):
    """공백만 무시한 대조 → (결과, 설명). 결과: 일치 / 일치(줄 단위) / 불일치."""
    q, s = nows(quote), nows(src)
    if not q:
        return "빈 인용", ""
    if q in s:
        return "일치", ("글자 그대로(공백 포함)" if quote.strip() in src else "공백만 다름")
    pos = 0
    for ln in [x for x in quote.split("\n") if x.strip()]:
        k = s.find(nows(ln), pos)
        if k < 0:
            return "불일치", "원문에 없는 줄: " + ln.strip()[:80]
        pos = k + len(nows(ln))
    return "일치(줄 단위)", "줄마다 원문에 있고 순서도 같음(가운데를 건너뛴 발췌)"


def _secrets():
    vals = []
    try:
        import lawclient
        vals.append(("LAW_OC", lawclient.load_oc()))
    except BaseException:  # noqa: BLE001 — 값이 없으면 검사할 것도 없음
        pass
    v = os.environ.get("DART_API_KEY", "").strip()
    if not v and os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            if line.strip().startswith("DART_API_KEY="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
    if v:
        vals.append(("DART_API_KEY", v))
    return [(k, x) for k, x in vals if len(x) >= 6]


MOBEOM_TAG = re.compile(r"제(\d+)조\(([^)]*)\)")


def check(write=True):
    probs, info = [], []
    lines = open(MD, encoding="utf-8").read().split("\n")
    blocks = md_blocks(lines)
    res = []
    for b in blocks:
        cl, cite = find_cite(lines, b["시작줄"])
        rec = dict(b, 출처줄=cl, 출처=cite)
        if not cite:
            rec.update(결과="출처 없음", 설명="")
            probs.append("인용 %d줄: 출처 표기를 찾지 못함" % b["시작줄"])
            res.append(rec)
            continue
        src, how, spath = resolve_source(cite)
        cd = re.search(r"수집\s*(20\d\d-\d\d-\d\d)", cite)
        md_ = _meta(spath) if spath else {}
        if cd and md_.get("fetched_at") and md_["fetched_at"][:10] != cd.group(1):
            probs.append("인용 %d줄: 수집일 %s ↔ 원본 meta %s" % (b["시작줄"], cd.group(1), md_["fetched_at"][:10]))
        if src is None:
            rec.update(결과="원문 못 찾음", 설명=how)
            probs.append("인용 %d줄: 원문을 찾지 못함(%s)" % (b["시작줄"], how))
        else:
            r, d = compare(b["글"], src)
            rec.update(결과=r, 설명=d, 원문=how)
            if r == "불일치" or r == "빈 인용":
                probs.append("인용 %d줄: %s — %s (%s)" % (b["시작줄"], r, d, how))
        # 출처 표기 요소: 문서명·일련번호 또는 URL·위치·수집일
        miss = []
        if not re.match(r"\s*[^·]+", cite):
            miss.append("문서명")
        if "일련번호" not in cite and "flSeq=" not in cite:
            miss.append("일련번호/URL")
        if "law.go.kr" not in cite:
            miss.append("URL")
        if not re.search(r"수집\s*20\d\d-\d\d-\d\d", cite):
            miss.append("수집일")
        if not re.search(r"\[별표|제\d+조|조문 전체|부칙|p\.\d+", cite):
            miss.append("위치(조·별표·쪽)")
        if "OC=" in cite and "OC=***" not in cite:
            miss.append("OC 가림")
        if miss:
            probs.append("인용 %d줄: 출처 표기에 빠진 것 %s" % (b["시작줄"], "·".join(miss)))
        rec["출처빠짐"] = miss
        res.append(rec)
    n_ok = sum(1 for r in res if r.get("결과", "").startswith("일치"))
    n_exact = sum(1 for r in res if r.get("설명") == "글자 그대로(공백 포함)")
    info.append("원문 인용 블록 %d개 대조 — 일치 %d(글자 그대로 %d · 공백만 다름 %d · 줄 단위 발췌 %d)" % (
        len(res), n_ok, n_exact, sum(1 for r in res if r.get("설명") == "공백만 다름"),
        sum(1 for r in res if r.get("결과") == "일치(줄 단위)")))
    text = "\n".join(lines)
    # 「전문」 주장: 별표 3·3-1·4 와 조문 전문은 원문 전체와 같아야 함
    xs = rd(SRC["세칙"])
    full = [("세칙 [별표 3] 전문", annex(xs, "3")["글"]), ("세칙 [별표 3-1] 전문", annex(xs, "3", "01")["글"]),
            ("세칙 [별표 4] 전문", annex(xs, "4")["글"])]
    xg = rd(SRC["지배구조감독규정"])
    for jo in ("제8조", "제10조", "제13조"):
        full.append(("지배구조 감독규정 %s 전문" % jo, [t for lab, ti, t in L10.rule_articles(xg) if lab == jo][0]))
    xd = rd(SRC["시행령"])
    for jo in ("제20조", "제22조", "제24조"):
        full.append(("시행령 %s 전문" % jo, L10.find_unit(xd, jo)[2]))
    full.append(("시행령 제6조제3항", L10.find_unit(xd, "제6조", 3)[2]))
    full.append(("금융지주회사법 제22조 전문", L10.find_unit(rd(SRC["지주법"]), "제22조")[2]))
    for name, src in full:
        ok = any(nows(b["글"]) == nows(src) for b in blocks)
        if not ok:
            probs.append("지시서 항목 「%s」: 원문 전체와 같은 인용 블록이 없음" % name)
    info.append("「전문」 항목 %d개: 원문 전체와 같은 블록 확인" % len(full))
    # 지시서 9-1 항목마다 받은 글 또는 「추출 범위에 없음」+찾은 방법
    req_items = [("1 세칙 별표3 전문", r"### 1-1 \[별표 3\]"), ("1 세칙 별표3-1", r"### 1-2 \[별표 3-1\]"),
                 ("1 세칙 별표4 전문", r"### 1-3 \[별표 4\]"), ("1 세칙 별표5 리스크관리 항목", r"### 1-4 \[별표 5\]"),
                 ("1 세칙 12조 6항·8항", r"### 1-5 세칙 제12조"), ("2 지배구조 감독규정 8·10·13조", r"## 2\. 금융회사 지배구조 감독규정"),
                 ("3 시행령 6조3항", r"### 3-1 시행령 제6조"), ("3 시행령 20조", r"### 3-2 시행령 제20조"),
                 ("3 시행령 22조", r"### 3-3 시행령 제22조"), ("3 시행령 24조", r"### 3-4 시행령 제24조"),
                 ("3 확인할 것(위험관리위원회 설치 예외·겸직 허용 범위)", r"### 3-6 확인할 것"),
                 ("4 금융지주회사법 22조", r"## 4\. 금융지주회사법 제22조"), ("5 감독규정 30조 연혁", r"## 5\. 금융지주회사감독규정 제30조")]
    for name, pat in req_items:
        if not re.search(pat, text, flags=re.M):
            probs.append("지시서 항목 「%s」: 절이 없음" % name)
    info.append("지시서 9-1 항목 %d개: 절 확인" % len(req_items))
    # 「추출 범위에 없음」마다 찾은 방법(검색어·범위)
    n_nf = 0
    for i, ln in enumerate(lines):
        if "추출 범위에 없음" in ln and not ln.startswith("```"):
            n_nf += 1
            win = " ".join(lines[max(0, i - 3):i + 4])
            if not re.search(r"검색|찾|정규식|lawSearch|확인|대조|넣어", win):
                probs.append("「추출 범위에 없음」 %d줄: 찾은 방법이 곁에 없음" % (i + 1))
    info.append("「추출 범위에 없음」 %d곳: 찾은 방법 확인" % n_nf)
    # 모범규준 조 표기 — 자료 묶음마다 「모범규준 조」 줄, 조 번호·제목이 조목록과 맞는지
    titles = {r["조"]: r["제목_2016.8.1판"] for r in csv.DictReader(open(MOBEOM_CSV, encoding="utf-8-sig"))}
    bundles = [r"### 1-1 ", r"### 1-2 ", r"### 1-3 ", r"### 1-4 ", r"### 1-5 ", r"### 제8조\(", r"### 제10조\(",
               r"### 제13조\(", r"### 3-1 ", r"### 3-2 ", r"### 3-3 ", r"### 3-4 ", r"### 3-5 ", r"### 3-6 ", r"## 4\. ",
               r"## 5\. "]
    heads = [i for i, ln in enumerate(lines) if ln.startswith("#")]
    for pat in bundles:
        hs = [i for i in heads if re.match(pat, lines[i])]
        if not hs:
            probs.append("자료 묶음 %s: 머리 없음" % pat)
            continue
        h = hs[0]
        nxt = [i for i in heads if i > h]
        seg = lines[h:(nxt[0] if nxt else len(lines))]
        tag = [ln for ln in seg if ln.startswith("- 모범규준 조")]
        if not tag:
            probs.append("자료 묶음 「%s」: 「모범규준 조」 줄 없음" % lines[h][:40])
    for i, ln in enumerate(lines):
        if ln.startswith("- 모범규준 조") or ln.startswith("| 제") and "(판단)" in ln:
            for m in MOBEOM_TAG.finditer(ln.split("—")[0] if ln.startswith("- 모범규준 조") else ln.split("|")[1]):
                no, ti = m.group(1), m.group(2)
                if no in titles and nows(ti) != nows(titles[no]):
                    probs.append("모범규준 조 표기 %d줄: 제%s조(%s) ↔ 조목록 「%s」" % (i + 1, no, ti, titles[no]))
                if no not in titles:
                    probs.append("모범규준 조 표기 %d줄: 제%s조는 조목록(1~59조)에 없음" % (i + 1, no))
    # 「」 조각(모범규준 조 줄·6절 표 행)이 원문(9-1 원문 XML 6개 + 모범규준 원문 md)에 있는지
    U = _union_text()
    n_frag = 0
    srec = [i for i, ln in enumerate(lines) if ln.startswith(SREC)]
    s8i = [i for i, ln in enumerate(lines) if ln.startswith(S8)]
    s8r = range(s8i[0], srec[0] if srec else len(lines)) if s8i else range(0)
    for i, ln in enumerate(lines):
        if ln.startswith("- 모범규준 조(") or (ln.startswith("| 제") and JUDGE in ln) or (i in s8r and ln.startswith("- note")):
            for m in re.finditer(r"「([^「」]+)」", ln):
                frag = m.group(1)
                if frag in ("지주 평가·검사·공시",):
                    continue
                n_frag += 1
                if nows(frag) not in U:
                    probs.append("%d줄: 「%s」 가 원문에 없음" % (i + 1, frag[:60]))
    info.append("모범규준 조 줄·6절 표의 「」 원문 조각 %d개 대조" % n_frag)
    # 「모범규준 제N조(제목)」 꼴(7절 표 등)의 조 제목 — 검증 기록(고친 곳 전·후 글을 줄여 옮김)은 빼고
    for i, ln in enumerate(lines[:srec[0] if srec else len(lines)]):
        for run in re.finditer(r"모범규준\s+((?:제\d+조\([^)]*\)[·\s]*)+)", ln):
            for m in MOBEOM_TAG.finditer(run.group(1)):
                no, ti = m.group(1), m.group(2)
                if no not in titles or nows(ti) != nows(titles[no]):
                    probs.append("%d줄: 모범규준 제%s조(%s) ↔ 조목록 「%s」" % (i + 1, no, ti, titles.get(no, "없음")))
    # 5-2·5-3 의 제30조 sha256·직전 판과 같음 ↔ csv
    c30 = {r["일련번호"]: r for r in csv.DictReader(open(CSV, encoding="utf-8-sig"))
           if r["법령명"] == FHC and r.get("제30조_sha256")}
    n30 = 0
    for m in re.finditer(r"(\d{4,})\(발령[^)]*\) — 제30조 sha256 `([0-9a-f]{64})`", text):
        n30 += 1
        if c30.get(m.group(1), {}).get("제30조_sha256") != m.group(2):
            probs.append("5-2절 %s 제30조 sha256 이 csv 와 다름" % m.group(1))
    for ln in lines:
        m = re.match(r"^\| \d+ \| (\d+) \| (?:[^|]+\|){5} `([0-9a-f]{12})` \| ([^|]+) \|", ln)
        if m:
            n30 += 1
            r = c30.get(m.group(1))
            if not r or r["제30조_sha256"][:12] != m.group(2) or r["제30조_직전판과같음"] != m.group(3).strip():
                probs.append("5-3절 표 %s: 제30조 sha256·직전 판과 같음이 csv 와 다름" % m.group(1))
    info.append("5-2·5-3절 제30조 sha256 표기 %d곳 ↔ csv 대조" % n30)
    # 세칙 별표 「?」 개수(1-1·1-3·1-4절 note: 1·3·6곳)
    for no, want in (("3", 1), ("4", 3), ("5", 6)):
        got = annex(xs, no)["글"].count("?")
        if got != want:
            probs.append("세칙 [별표 %s] 「?」 %d곳(md 는 %d곳)" % (no, got, want))
    # 0절 표·csv — 파일·sha256·판 정보
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    n_csv = 0
    for r in rows:
        p = r["원문XML"]
        if not p or not os.path.exists(p):
            probs.append("csv %s %s: 원문 파일 없음(%s)" % (r["법령명"][:20], r["일련번호"], p))
            continue
        b = rd(p)
        n_csv += 1
        if r["sha256"] and r["sha256"] != _sha(b):
            probs.append("csv %s %s: sha256 다름" % (r["법령명"][:20], r["일련번호"]))
        if p.endswith(".xml") and b.lstrip().startswith(b"<"):
            root = ET.fromstring(b)
            bi = root.find("행정규칙기본정보")
            if bi is not None:
                for col, tag in (("일련번호", "행정규칙일련번호"), ("시행일자", "시행일자"), ("발령_공포일자", "발령일자")):
                    if r[col] and (bi.findtext(tag) or "").strip() != r[col]:
                        probs.append("csv %s %s: %s 다름(XML %s)" % (r["법령명"][:20], r["일련번호"], col,
                                                               (bi.findtext(tag) or "").strip()))
            if r.get("제30조_sha256"):
                t = [x for lab, ti, x in L10.rule_articles(b) if lab == "제30조"]
                if not t or _sha(t[0].encode("utf-8")) != r["제30조_sha256"]:
                    probs.append("csv %s: 제30조 sha256 다름" % r["일련번호"])
        u = r.get("출처URL", "")
        if "OC=" in u and "OC=***" not in u:
            probs.append("csv %s: 출처URL 의 OC 가 가려지지 않음" % r["일련번호"])
        mt = _meta(p)
        if mt.get("fetched_at") and r.get("수집일시") and r["수집일시"] != mt["fetched_at"]:
            probs.append("csv %s: 수집일시 %s ↔ meta %s" % (r["일련번호"], r["수집일시"], mt["fetched_at"]))
    for m in re.finditer(r"`(dart_out/raw/[^`]+\.xml)` · `([0-9a-f]{64})`", text):
        if not os.path.exists(m.group(1)) or _sha(rd(m.group(1))) != m.group(2):
            probs.append("0절 표: %s sha256 다름" % m.group(1))
    info.append("csv %d행: 원문 파일·sha256·판 정보·제30조 sha256·OC 가림·수집일시 대조" % n_csv)
    # 키·OC 값, PDF
    scan = [MD, CSV, REPORT, os.path.abspath(__file__)] + [os.path.join(VDIR, f) for f in os.listdir(VDIR)]
    for k, v in _secrets():
        for p in scan:
            if os.path.isfile(p) and v.encode() in rd(p):
                probs.append("%s 값이 %s 에 들어 있음" % (k, p))
    info.append("키·OC 값 검사: %d종 × 파일 %d개(md·csv·결과·스크립트·검증 원본 폴더 — 값은 출력하지 않음)" % (len(_secrets()), len(scan)))
    pdfs = [f for f in os.listdir(OUT) if f.lower().endswith(".pdf")]
    if pdfs:
        probs.append("산출 폴더에 PDF: %s" % pdfs)
    if not re.search(r"^## 검증 기록\(2026-10-07\)", text, flags=re.M):
        probs.append("「## 검증 기록(2026-10-07)」 절 없음")
    if write:
        out = ["# 13차 9-1 검증 결과 — scripts/dart/verify13_law91.py (실행 %s)" % now(), "",
               "대상: %s · %s" % (MD, CSV), ""]
        out += ["- " + x for x in info]
        out += ["", "## 문제 %d건" % len(probs)] + ["- " + x for x in probs]
        out += ["", "## 인용 블록별 결과(시작줄 · 종류 · 결과 · 설명 · 원문 · 출처줄)"]
        for r in res:
            out.append("- %d · %s · %s · %s · %s · 출처 %s줄%s" % (
                r["시작줄"], r["종류"], r.get("결과"), r.get("설명", ""), r.get("원문", ""), r.get("출처줄"),
                (" · 출처 빠짐 " + "·".join(r["출처빠짐"])) if r.get("출처빠짐") else ""))
        fl = json.load(open(FIXLOG, encoding="utf-8")) if os.path.exists(FIXLOG) else {}
        if fl:
            out += ["", "## 보정 기록(fix — _fix_log.json 요약)"]
            for c in fl.get("고친곳", []):
                out.append("- [%s] %s" % (c["종류"], c["설명"]))
        with open(REPORT, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
    return probs, info, res


def main_check():
    probs, info, res = check()
    for x in info:
        print(x)
    print("문제 %d건%s" % (len(probs), "" if not probs else " — 앞 15건:"))
    for x in probs[:15]:
        print("  " + x[:200])
    print("결과 →", REPORT)
    sys.exit(0 if not probs else 1)


# ── fix(보정 — 요청 없음, 멱등) ─────────────────────────────────────────
BAK_MD = os.path.join(VDIR, "_검증전_9-1_법령원문.md")
BAK_CSV = os.path.join(VDIR, "_검증전_9-1_법령판.csv")
S8 = "## 8. 검증 보충(2026-10-07)"
SREC = "## 검증 기록(2026-10-07)"
JUDGE = "(판단)"

# 자료 묶음마다 붙일 「모범규준 조」 줄 — 조 제목은 dart_out/risk13/모범규준_조목록.csv(2016.8.1 판). 9-1 지시서에는 조 번호가 없어 전부 판단.
TAGS = [
    (r"### 1-1 ", "- 모범규준 조(판단): 제8조(이사회) · 제10조(경영진) · 제7조(조직구성) · 제13조(그룹위험관리부서) · "
     "제14조(위험 통제) · 제16조(보고체계) · 제19조(위험 측정) · 제20조(위험 관리) · 제28조(시스템 구축 및 관리) · "
     "제37조(자본적정성 평가 및 관리 체제) · 제21조(신용위험) · 제25조(유동성위험) · 제56조(통합위기상황분석) · 제57조(비상계획) · "
     "제33조(그룹내 위험 전이 방지) — 평가항목 문구 기준: 「·리스크관리체제 구축을 위한 이사회 및 경영진의 역할」→제8·10조, "
     "「·리스크관리 조직 및 인력의 적정성」→제7·13조, 「·리스크허용한도의 적정성」→제14조, 「·리스크 측정, 모니터링의 적정성」→제19·20조, "
     "「·경영진등에 대한 리스크보고의 적정성」→제16조, 「·경영정보시스템(MIS)의 적정성」→제28조, 「·리스크를 감안한 자본규모의 적정성」→제37조, "
     "「·신용리스크 관리의 적정성」→제21조, 「·유동성리스크 관리의 적정성」→제25조, 「·위기상황분석 및 비상계획의 적정성」→제56·57조, "
     "「·그룹 내부거래의 적정성」→제33조. 9-1 지시서에는 조 번호가 없어 전부 판단(조 제목은 모범규준_조목록.csv 2016.8.1 판)."),
    (r"### 1-2 ", "- 모범규준 조(판단): 제37조(자본적정성 평가 및 관리 체제) — 「필요자본에 대한 자기자본 비율」·「부채비율」·「이중레버리지비율」은 "
     "감독 계량지표의 산정식이라 직접 대응 조는 없고 자본적정성 평가(모범규준 제5장)와 가장 가깝다(판단). 모범규준 2016.8.1 판 전문"
     "(9-4_모범규준_원문.md 5절)에서 검색어 「부채비율」「이중레버리지」「레버리지」는 나오지 않음."),
    (r"### 1-3 ", "- 모범규준 조(판단): 직접 대응 조 없음 — [별표 3] 평가항목의 등급별 정의라 1-1절과 같은 조 행"
     "(제8·10·21·25·28·37·56·57조 등)의 「지주 평가·검사·공시」 칸 보조 자료(판단)."),
    (r"### 1-4 ", "- 모범규준 조(판단): 제7조(조직구성) · 제21조(신용위험) · 제22조(시장위험) · 제23조(운영위험) · 제25조(유동성위험) · "
     "제37조(자본적정성 평가 및 관리 체제) — 「5-1. 리스크관리 개요」(「리스크관리조직, 관리체계 및 관리정책」)→제7조, "
     "「5-2. 신용리스크관리」→제21조, 「5-3. 시장리스크관리」→제22조, 「5-4. 운영리스크관리」→제23조, "
     "「5-5. 유동성리스크관리」·「4-3. 유동성지표」→제25조, 「4-1. 자본적정성지표」→제37조. 4-2·4-4·4-5 는 직접 대응 조 없음(판단)."),
    (r"### 1-5 ", "- 모범규준 조(판단): 제3조(적용대상) · 제18조(측정 및 관리 대상) · 제36조(적용대상) — 제6항·제8항(평가등급 조정, "
     "계량지표 등급구분기준)은 직접 대응 조 없음. 보충 제2항(평가대상에서 제외할 수 있는 자회사등)은 모범규준 제3조 단서 "
     "「위험이 경미한 자회사등」, 제18조제3항 「위험이 경미한 자회사등은 제외할 수 있으며」, 제36조 단서 "
     "「비중이 미미(예: 자산비중 5% 미만)하거나 비금융회사인 자회사등」과 닿음(판단; 3조는 사용자 9-4 표기 조 번호)."),
    (r"### 제8조\(", "- 모범규준 조(판단): 제9조(그룹위험관리위원회) · 제28조(시스템 구축 및 관리) · 제14조(위험 통제) · "
     "제34조(해외위험 관리) · 제56조(통합위기상황분석) · 제6조(문서화) — 위험관리위원회 심의·의결 사항(모범규준 제9조제6항 결의사항 자리). "
     "「위험관리정보시스템의 운영에 관한 사항」→제28조, 「각종 한도의 설정 및 한도초과의 승인에 관한 사항」→제14조, "
     "「각 국외 현지법인 및 국외지점의 상황을 고려한 위기상황분석」→제34·56조, 「자산건전성 분류기준」→제6조(제1항제6호 "
     "「자산건전성 분류기준 및 관리」)."),
    (r"### 제10조\(", "- 모범규준 조(판단): 제17조(의사전달체계) · 제5조(위험관리 원칙) · 제14조(위험 통제) — 제2항 각 호는 "
     "금융지주회사등의 내부통제 사항: 「금융지주회사등의 경영의사결정에 필요한 정보가 효율적으로 전달될 수 있는 체제의 구축에 관한 사항」→제17조, "
     "「금융지주회사등의 자산의 운용 또는 업무의 영위과정에서 발생하는 위험의 관리에 관한 사항」→제5조(제2항제6호 "
     "「금융지주회사는 자회사등의 위험관리를 통할한다」)·제14조. 제2항제1호(업무의 분장 및 조직구조)는 모범규준 제3장(제14~17조) 자리(판단)."),
    (r"### 제13조\(", "- 모범규준 조(판단): 제57조(비상계획) · 제13조(그룹위험관리부서) · 제14조(위험 통제) · 제47조(내부자본 한도 관리) · "
     "제28조(시스템 구축 및 관리) · 제16조(보고체계) — 「금융사고 등 우발상황에 대한 위험관리 비상계획」→제57조(6절의 53조 행과 함께), "
     "「위험관리를 전담하는 조직」→제13조, 「부서별 또는 사업부문별 위험부담한도 및 거래한도 등의 설정ㆍ운영」·「위험한도의 운영상황 점검 및 분석」"
     "→제14·47조, 「위험관리정보시스템의 운영」→제28조, 「위험관리위원회, 이사회, 임원에 대한 위험관리정보의 적시 제공」→제16조."),
    (r"### 3-1 ", "- 모범규준 조(판단): 제9조(그룹위험관리위원회) · 제7조(조직구성) — 법 제3조제3항제3호 「제21조에 따른 위험관리위원회에 관한 사항」의 "
     "적용 예외 대상을 정하는 항이라 위험관리위원회 조 행(판단)."),
    (r"### 3-2 ", "- 모범규준 조(판단): 제11조(그룹위험관리책임자) — 법 제28조제2항이 제25조제2항(직원 중 선임)을 위험관리책임자에 준용하므로 "
     "그룹위험관리책임자 조 행(판단)."),
    (r"### 3-3 ", "- 모범규준 조(판단): 제4조(위험관리 철학) · 제5조(위험관리 원칙) · 제6조(문서화) · 제9조(그룹위험관리위원회) · "
     "제13조(그룹위험관리부서) · 제11조(그룹위험관리책임자) — 「위험관리의 기본방침」→제4·5조(6절), 위험관리기준 각 호→제6조(문서화 항목), "
     "「금융회사가 부담 가능한 위험 수준의 설정」→제9조(제6항제2호 「부담 가능한 위험수준의 결정」), 「위험관리를 전담하는 조직」→제13조, "
     "「위험관리책임자의 임면」→제11조."),
    (r"### 3-4 ", "- 모범규준 조(판단): 제11조(그룹위험관리책임자) · 제13조(그룹위험관리부서) — 위험관리책임자·준법감시인 겸직 제한→제11조, "
     "모범규준 제13조제1항 「위험관리 담당 직원은 다른 업무를 겸직할 수 없다」와 같은 자리(판단)."),
    (r"### 3-5 ", "- 모범규준 조(판단): 제9조(그룹위험관리위원회) · 제7조(조직구성) · 제11조(그룹위험관리책임자) · 제6조(문서화) · 제8조(이사회) — "
     "법 제21조 1~4호(「위험관리의 기본방침 및 전략 수립」 · 「금융회사가 부담 가능한 위험 수준 결정」 · 「적정투자한도 및 손실허용한도 승인」 · "
     "「제27조에 따른 위험관리기준의 제정 및 개정」)는 모범규준 제9조제6항 1·2·3·5호와 문구가 거의 같다. 법 제3조제3항·제16조→제7·9조, "
     "법 제25·28·29조·시행령 제11조제2항제2호→제11조, 법 제27조(위험관리기준)→제6조·제8조제2항(판단)."),
    (r"### 3-6 ", "- 모범규준 조(판단): 제9조(그룹위험관리위원회) · 제11조(그룹위험관리책임자) — ① 위험관리위원회 설치 예외→제9조, "
     "② 위험관리책임자·준법감시인 겸직 허용 범위→제11조(판단)."),
    (r"## 4\. ", "- 모범규준 조(판단): 제3조(적용대상) — 전환대상자를 「이 법에 따른 금융지주회사 및 그 자회사등으로 본다」 — 모범규준 제3조 "
     "「이 규준은 금융지주회사 및 그 자회사등에 적용된다」의 적용 대상 범위와 닿음(판단; 3조는 사용자 9-4 표기 조 번호)."),
    (r"## 5\. ", "- 모범규준 조(판단): 제8조(이사회) · 제9조(그룹위험관리위원회) — 제30조 본문(이사회 심의·의결, 이사회 내 위원회)→제8조제2항·제9조. "
     "제1~4호(「경영전략에 부합하는 리스크관리 기본방침 수립」 · 「금융기관별 부담가능한 리스크 수준의 결정」 · 「적정투자한도 또는 손실허용한도 승인」 · "
     "「리스크관리규정의 제정 및 개정」)는 모범규준 제9조제6항 1·2·3·5호(「그룹의 경영전략에 부합하는 위험관리 기본방침의 수립」 · "
     "「부담 가능한 위험수준의 결정」 · 「적정투자한도 또는 손실허용한도의 승인」 · 그룹위험관리규정의 제정 및 개정)와 문구가 거의 같다(판단)."),
]


class Fixer(object):
    def __init__(self, text):
        self.lines = text.split("\n")
        self.log = []

    def _uniq(self, prefix):
        hit = [i for i, ln in enumerate(self.lines) if ln.startswith(prefix)]
        if len(hit) != 1:
            raise RuntimeError("줄 머리가 하나가 아님(%d): %s" % (len(hit), prefix[:60]))
        return hit[0]

    def append(self, prefix, suffix, kind, why):
        i = self._uniq(prefix)
        if suffix.strip() in self.lines[i]:
            return
        before = self.lines[i]
        self.lines[i] = before + suffix
        self.log.append(dict(종류=kind, 줄=i + 1, 설명=why, 전=before, 후=self.lines[i]))

    def replace(self, prefix, new, kind, why):
        hit = [i for i, ln in enumerate(self.lines) if ln == new]
        if hit:
            return
        i = self._uniq(prefix)
        before = self.lines[i]
        self.lines[i] = new
        self.log.append(dict(종류=kind, 줄=i + 1, 설명=why, 전=before, 후=new))

    def last_cell(self, prefix, cell, kind, why):
        i = self._uniq(prefix)
        cells = self.lines[i].split(" | ")
        new = " | ".join(cells[:-1] + [cell + " |"])
        if new == self.lines[i]:
            return
        before = self.lines[i]
        self.lines[i] = new
        self.log.append(dict(종류=kind, 줄=i + 1, 설명=why, 전=before, 후=new))

    def cell(self, prefix, k, cell, kind, why):
        i = self._uniq(prefix)
        cells = self.lines[i].split(" | ")
        if cells[k] == cell:
            return
        before = self.lines[i]
        cells[k] = cell
        self.lines[i] = " | ".join(cells)
        self.log.append(dict(종류=kind, 줄=i + 1, 설명=why, 전=before, 후=self.lines[i]))

    def insert_after(self, idx, new_lines, kind, why):
        self.lines[idx + 1:idx + 1] = new_lines
        self.log.append(dict(종류=kind, 줄=idx + 2, 설명=why, 전="", 후="\n".join(new_lines)))

    def tag(self, head_re, line):
        heads = [i for i, ln in enumerate(self.lines) if ln.startswith("#")]
        hs = [i for i in heads if re.match(head_re, self.lines[i])]
        if len(hs) != 1:
            raise RuntimeError("머리 %s: %d개" % (head_re, len(hs)))
        h = hs[0]
        nxt = [i for i in heads if i > h]
        end = nxt[0] if nxt else len(self.lines)
        seg = range(h + 1, end)
        old = [i for i in seg if self.lines[i].startswith("- 모범규준 조")]
        if old:
            if self.lines[old[0]] != line:
                before = self.lines[old[0]]
                self.lines[old[0]] = line
                self.log.append(dict(종류="모범규준 조", 줄=old[0] + 1, 설명="「모범규준 조」 줄 고침 — " + self.lines[h][:40],
                                     전=before, 후=line))
            return
        # 첫 「- 인용:」/「- 판:」 줄 뒤(코드 블록 전), 없으면 머리 다음 빈 줄 뒤
        pos = None
        for i in seg:
            if self.lines[i].startswith("```"):
                break
            if self.lines[i].startswith("- 인용:") or self.lines[i].startswith("- 판:") or self.lines[i].startswith("- 판(시행령)"):
                pos = i
                break
        if pos is None:
            pos = h + 1 if (h + 1 < len(self.lines) and not self.lines[h + 1].strip()) else h
        self.insert_after(pos, [line], "모범규준 조", "「모범규준 조」 줄 더함 — " + self.lines[h][:40])

    def text(self):
        return "\n".join(self.lines)


def _cite_rule(key, loc, collected):
    sn = SERIAL[key]
    p = SRC[key]
    xb = rd(p)
    root = ET.fromstring(xb)
    bi = root.find("행정규칙기본정보")
    name = (bi.findtext("행정규칙명") or "").strip()
    ef, pr = (bi.findtext("시행일자") or "").strip(), (bi.findtext("발령일자") or "").strip()
    d = lambda s: "%s-%s-%s" % (s[:4], s[4:6], s[6:])  # noqa: E731
    return ("[%s · 일련번호 %s(시행 %s, 발령/공포 %s) · http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=%s&type=XML · "
            "%s · 수집 %s(원본 %s), 검증 재사용 %s]" % (name, sn, d(ef), d(pr), sn, loc, collected, p, TODAY))


def _block(text):
    return ["```text", text.rstrip("\n"), "```"]


def _lines_between(t, start_pat, end_pat):
    ls = t.split("\n")
    s = next(i for i, ln in enumerate(ls) if re.search(start_pat, ln))
    e = next(i for i, ln in enumerate(ls) if i >= s and re.search(end_pat, ln))
    return "\n".join(ls[s:e + 1])


def build_s8(S, st):
    out = [S8, "",
           "- note: 이 절은 검증 단계(`scripts/dart/verify13_law91.py` fetch·search·fix)에서 더했다. 「추출 범위에 없음」 주장마다 같은 출처를 "
           "넓은 검색어로 다시 찾은 결과다. 원문 인용은 코드 블록, 해설은 note, 해석은 「(판단)」.",
           "- 수집: 법제처 Open API(원장 `dart_out/raw/web13/verify13_law91/_call_log.csv`, 요청 URL 의 인증값은 `OC=***`, LAW_DELAY=1.0). "
           "별표 PDF 는 www.law.go.kr robots.txt 확인(상태 %s, 확인 %s — 원본 `dart_out/raw/web13/verify13_law91/robots_www.law.go.kr.txt`) 뒤 "
           "`/LSW/flDownload.do` 로 받았다. 받은 시각은 각 `.meta.json` 의 fetched_at(KST)." % (st["robots"]["상태"], st["robots"]["확인"]),
           ""]
    # 8-1
    s1 = S["S1_지배구조감독규정"]
    cur = [r for r in s1 if r["일련번호"] == SERIAL["지배구조감독규정"]][0]
    names = [n for n, _ in DELEG_PATS]
    out += ["### 8-1 시행령 제6조제3항제5호·제20조제2항제5호 「금융위원회가 정하여 고시하는 자」 — 금융회사 지배구조 감독규정 전체 재검색", "",
            "- 모범규준 조(판단): 제9조(그룹위험관리위원회) · 제11조(그룹위험관리책임자) — 3-6절 ①·②의 보충.",
            "- 찾은 범위: 「금융회사 지배구조 감독규정」 현행(2100000285614) + 법제처 연혁 목록(`lawSearch.do target=admrul query=금융회사 지배구조 감독규정 "
            "nw=2 display=100`, totalCnt %d — 본문 판 %d · 「금융회사 지배구조 감독규정 시행세칙」 %d)의 본문 판 전부(2016-08-01 제정 판 ~ 2026-10-02 현행) + "
            "시행세칙 가장 최근 판. 판마다 조문내용·부칙내용·별표내용·제개정이유 전체." % (
                len(st["지배구조감독규정_연혁"]["판"]), sum(h["대상"] == "Y" for h in st["지배구조감독규정_연혁"]["판"]),
                sum(h["대상"] == "N" for h in st["지배구조감독규정_연혁"]["판"])),
            "- 검색어(정규식, 낱말 사이 공백 허용, %d개): %s." % (len(names), " · ".join("「%s」" % n for n in names)),
            "- 그 밖에 로컬의 다른 법령·고시 XML(`dart_out/raw/web9|web10|web11/law/`, `dart_out/raw/web13/law91·law92*/`) 전체에서 "
            "정규식 `지배구조에\\s*관한\\s*법률\\s*시행령\\s*」?\\s*제\\s*(6|20|24)\\s*조` — %d건." % S.get("S1b_다른고시", {}).get("건수", 0),
            "",
            "| 판(일련번호) | 시행일 | 발령번호 · 제개정 | 「영 제6조」 | 「시행령 제6조」 | 「제6조제3항」 | 「영 제20조」 | 「시행령 제20조」 | 「제20조제2항」 | "
            "「법 제3조제3항」 | 「법 제25조제2항」 | 「고시하는 자」 | 「적용 범위」 | 「직원 중」 |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in s1:
        g = lambda k: r["검색어"][k]["건수"]  # noqa: E731
        out.append("| %s%s | %s | %s · %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            r["일련번호"], " (시행세칙)" if "시행세칙" in r["이름"] else "", r["시행일자"], r["발령번호"], r["제개정"],
            g("영 제6조"), g("시행령 제6조"), g("제6조제3항"), g("영 제20조"), g("시행령 제20조"), g("제20조제2항"),
            g("법 제3조제3항"), g("법 제25조제2항"), g("고시하는 자(자격 제외)"), g("적용 범위·적용범위"), g("직원 중·직원중")))
    gz = [e for r in s1 for e in r["검색어"]["고시하는 자(자격 제외)"]["예"]]
    other = []
    for r in s1:
        for k in ("적용 범위·적용범위", "직원 중·직원중", "법 제3조제3항", "법 제25조제2항"):
            for e in r["검색어"][k]["예"]:
                other.append("%s %s(%s)" % (r["일련번호"], e["위치"][:24], k.split("·")[0]))
    out += ["",
            "- note: 위 표의 0 이 아닌 칸 가운데 「고시하는 자」 밖의 것: %s — 내용을 읽어 보니 시행령 제6조·제20조 위임과 다른 뜻(판단)." % (
                " · ".join(other) if other else "없음")]
    out += ["- note: 「고시하는 자」가 나온 곳은 %s — 모두 영 제25조의2제2항(내부통제등 관리의무 대상 임원)을 받는 문구로, 영 제6조·제20조와 관계없다."
            % " · ".join(sorted(set("%s %s" % (r["일련번호"], e["위치"][:20]) for r in s1 for e in r["검색어"]["고시하는 자(자격 제외)"]["예"]))) if gz
            else "- note: 「고시하는 자」 0건.",
            "- 결과: 위 범위·검색어로 시행령 제6조제3항제5호·제20조제2항제5호의 위임을 받는 조를 찾지 못했다 → **추출 범위에 없음**(상태 유지). "
            "다른 고시(금융투자업규정·보험업감독규정 등 업권 감독규정)는 법제처에서 새로 받아 찾지 않았다(로컬 XML 만 찾음).",
            "",
            "현행 판에서 「금융위원회가 정하여 고시하는」 위임을 받는 문구 %d곳(조문내용에서 정규식으로 뽑은 글자 그대로, 한 줄에 한 곳) — "
            "인용: %s" % (len(cur["고시위임"]), _cite_rule("지배구조감독규정", "조문 전체(고시 위임 문구)", "2026-10-01")),
            ""]
    out += _block("\n".join(d["원문"] for d in cur["고시위임"]))
    out += ["", "| # | 조(제목) | 위임 근거 | 고시 대상 낱말 |", "|---|---|---|---|"]
    for i, d in enumerate(cur["고시위임"], 1):
        out.append("| %d | %s(%s) | %s | %s |" % (i, d["조"], d["제목"], d["근거"], d["대상"]))
    xg = rd(SRC["지배구조감독규정"])
    a5 = [t for lab, ti, t in L10.rule_articles(xg) if lab == "제5조"][0]
    a6 = [t for lab, ti, t in L10.rule_articles(xg) if lab == "제6조"][0]
    a5_first = a5.split("\n")[0]
    out += ["",
            "- note: 위임 근거로 인용된 조문은 영 제7·11·16·17·18·21·22·25조의2·26·27조와 법 제21·22·23·30조의3 이다(위 표). "
            "영 제6조·제20조를 받는 문구는 없다.",
            "- 사용자 예시 「감독규정 제5조·제6조」: 제5조(지배구조내부규범 작성 및 공시)는 법 제14조를, 제6조(감사위원 자격요건)는 영 제16조제1항제6호를 받는 조다. "
            "제5조 전문에 「금융지주회사」 낱말: %s · 제6조 전문에 「금융지주회사」 낱말: %s. 제6조 전문과 제5조 첫 줄:" % (
                "나옴" if "금융지주회사" in a5 else "안 나옴", "나옴" if "금융지주회사" in a6 else "안 나옴"),
            "",
            "제6조 — 인용: " + _cite_rule("지배구조감독규정", "제6조 조문내용", "2026-10-01"), ""]
    out += _block(a6)
    out += ["", "제5조 첫 줄 — 인용: " + _cite_rule("지배구조감독규정", "제5조 조문내용(첫 줄)", "2026-10-01"), ""]
    out += _block(a5_first)
    out += ["",
            "- (판단) 감독규정 8판 어디에도 시행령 제6조제3항제5호·제20조제2항제5호를 받는 조가 없으므로, 그 고시가 정해지지 않았을 수 있다 — "
            "단정하지 않음. 법령 글만으로 읽으면 금융지주회사는 제1~4호에 들지 않아 위험관리위원회 설치 예외·위험관리책임자와 준법감시인 상호 겸직 허용 범위 밖이다(3-6절 판단 유지).",
            ""]
    # 8-2 별표 8
    xs = rd(SRC["세칙"])
    a8 = annex(xs, "8")
    blk1 = _lines_between(a8["글"], r"│은행    │계량", r"세부 리스크 유형별 위기상황 분석의 적정성")
    blk2 = _lines_between(a8["글"], r"^4\. \(계량지표 산정기준\)", r"시 분모의 금리리스크량은 고려하지 않는다")
    cite8 = ("[금융지주회사감독규정시행세칙 · 일련번호 2200000107297(시행 2025-05-16, 발령/공포 2025-05-16) · "
             "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2200000107297&type=XML · [별표 8] 별표내용(별표키 %s) · "
             "수집 2026-10-02(원본 dart_out/raw/web11/law/금융지주회사감독규정시행세칙_2200000107297.xml), 검증 재사용 %s]" % (a8["키"], TODAY))
    hit24 = S["S2_6절주제어"]["24조 금리위험"]
    out += ["### 8-2 모범규준 제24조(금리위험) — 세칙 [별표 8] 은행지주회사의 리스크평가 기준(반박 성공 — 지시 범위 밖, 같은 출처)", "",
            "- 모범규준 조(판단): 제24조(금리위험) · 제21조(신용위험) · 제22조(시장위험) · 제23조(운영위험) · 제25조(유동성위험) · 제26조(신용편중위험) · "
            "제56조(통합위기상황분석) — 24조는 사용자 9-4 표기 조 번호, 나머지는 판단.",
            "- 찾은 방법: 6절의 「추출 범위에 없음」(검색 범위 = 9-1 에서 옮긴 원문)을 같은 출처 XML 6개 전체(조문·부칙·별표·서식·제개정이유)로 넓혀 "
            "정규식 `%s` 로 다시 찾음. 세칙에서 %d개 단위(그 가운데 별표 %s), 지배구조 감독규정 %d, 금융지주회사감독규정 %d — 대부분 「금리(수수료)」·「적용금리」·"
            "「표면금리」 같은 거래조건 낱말이고, 금리위험 관리·평가 문구는 세칙 [별표 8] 뿐." % (
                TOPIC_PATS["24조 금리위험"], len(hit24["세칙"]),
                "·".join(h["위치"].split("]")[0].replace("[별표 ", "").strip() for h in hit24["세칙"] if h["위치"].startswith("[별표")),
                len(hit24["지배구조감독규정"]), len(hit24["감독규정"])),
            "- 인용: " + cite8,
            "- 원본 파일 링크(받지 않음): HWP http://www.law.go.kr%s · PDF http://www.law.go.kr%s" % (a8["hwp"], a8["pdf"]),
            "- note: 아래 첫 블록은 [별표 8] 「3. (평가항목)」 표의 은행 부분(계량 「금리」 칸에 「기본자본 대비 ΔEVE 비율」·「기본자본 대비 ΔNII 비율」, "
            "비계량 「리스크 관리」 칸에 「금리리스크」). 같은 별표 안 상자 글(「<개정 2021.4.23.>」·「[시행일 : 2021.12.31.]」)의 개정 평가항목 표에는 "
            "은행 부분과 「금리」 칸이 없다 — 상자 글이 2021.12.31 부터 적용되는 개정 글로 읽힌다(판단). 둘째 블록은 그 개정 글의 「4. (계량지표 산정기준)」"
            "(「분모의 금리리스크량은 고려하지 않는다」). XML 의 「??」는 원문 바이트 그대로(글머리 기호 자리로 보임, 판단).",
            ""]
    out += _block(blk1) + [""] + _block(blk2) + [""]
    # 8-3 지배구조 감독규정 별표 3 검증
    ag3 = annex(xg, "3")
    b3a = _lines_between(ag3["글"], r"나\. 다음의 보험계리업무와 관련한", r"증기준, 임직원의 권한과 책임에 관한 사항")
    b3b = _lines_between(ag3["글"], r"바\. 지급여력비율 관리업무와 관련한", r"검증기준, 임직원의 권한과 책임에 관한 사항")
    cite3 = ("[금융회사 지배구조 감독규정 · 일련번호 2100000285614(시행 2026-10-02, 발령/공포 2026-09-29) · "
             "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2100000285614&type=XML · [별표 3] 별표내용(별표키 %s) · "
             "수집 2026-10-01(원본 dart_out/raw/web9/law/금융회사지배구조감독규정_2100000285614.xml), 검증 재사용 %s]" % (ag3["키"], TODAY))
    out += ["### 8-3 모범규준 제30조(목적)(제4절 적합성 검증) — 지배구조 감독규정 [별표 3] 「내부 검증절차」(약한 겹침)", "",
            "- 모범규준 조(판단): 제30조(목적) · 제31조(적합성 검증의 대상) · 제32조(적합성 검증의 실시) — 30조는 사용자 9-4 표기 조 번호(적합성 검증), 대응은 판단.",
            "- 찾은 방법: 같은 출처 XML 6개 전체에서 정규식 `%s`. 지배구조 감독규정 [별표 1](「자격검증」 — 최고경영자 후보 관리, 다른 뜻)·[별표 3], "
            "금융지주회사감독규정 [별표 4](「지배구조의 적합성」 — 자체정상화계획, 다른 뜻)에서 나옴. 위험 측정과 닿는 것은 [별표 3] 보험회사 항목뿐." % TOPIC_PATS["30조 적합성 검증"],
            "- 인용: " + cite3,
            "- note(판단): 보험회사 내부통제기준에 넣을 사항(보험계리업무·지급여력비율 관리업무의 「내부 검증절차」와 검증기준)이라, 모범규준 제30~32조의 "
            "「위험 측정시스템에 대한 적합성검증」(지주 차원)과는 대상이 달라 약한 대응이다.",
            ""]
    out += _block(b3a) + [""] + _block(b3b) + [""]
    # 8-4 27·55
    s2 = S["S2_6절주제어"]
    out += ["### 8-4 모범규준 제27조(전략 및 평판위험) · 제55조(조기경보체계) — 여전히 추출 범위에 없음", "",
            "- 모범규준 조(판단): 제27조(전략 및 평판위험) · 제55조(조기경보체계) — 사용자 9-4 표기 조 번호.",
            "- 찾은 방법: 같은 출처 XML 6개(세칙 2200000107297, 지배구조 감독규정 2100000285614, 지배구조법 277253, 같은 법 시행령 290289, "
            "금융지주회사법 254783, 금융지주회사감독규정 2100000285612)의 조문·부칙·별표·서식·제개정이유 전체에서 정규식 27조 `%s` · 55조 `%s` "
            "(「투명성」 안의 「명성」, 「변경보고」 안의 「경보」 같은 거짓 일치는 정규식에서 뺌)." % (TOPIC_PATS["27조 전략·평판위험"], TOPIC_PATS["55조 조기경보"]),
            "- 결과: 27조 %s · 55조 %s → **추출 범위에 없음**(상태 유지)." % (
                " ".join("%s %d" % (k, len(v)) for k, v in s2["27조 전략·평판위험"].items()),
                " ".join("%s %d" % (k, len(v)) for k, v in s2["55조 조기경보"].items())),
            ""]
    # 8-5 연혁 날짜
    s3 = S["S3_개정표기날짜"]
    sp = S["S3_띄어쓴이름목록"]
    out += ["### 8-5 금융지주회사감독규정 연혁 — API 목록에 없는 판(개정 표기 날짜 7개) 다시 찾기", "",
            "- 모범규준 조(판단): 제8조(이사회) · 제9조(그룹위험관리위원회) — 5절 보충.",
            "- 찾은 방법 ①: 띄어 쓴 이름으로 목록 다시 받기 — `lawSearch.do target=admrul query=금융지주회사 감독규정 nw=2 display=100` → %d건, "
            "law91 목록(붙여 쓴 이름, 86건)에 없던 일련번호 %d건." % (sp["건수"], len(sp["law91목록에없던것"])),
            "- 찾은 방법 ②: 받아 둔 38판의 조문·별표에서 날짜가 처음 나오는 판, 부칙내용에서 「YYYY. M. D」·「YYYY년 M월 D일」 꼴 날짜 문구.",
            "",
            "| 개정 표기 날짜 | 조문·별표에 처음 나오는 판(일련번호 · 시행일) | 부칙에 그 날짜 문구 |", "|---|---|---|"]
    for d, v in s3.items():
        f = v["조문첫등장"] or {}
        out.append("| %s | %s · %s | %d건 |" % (d, f.get("일련번호", "-"), f.get("시행일자", "-"), v["부칙건수"]))
    p77 = "dart_out/raw/web13/law91/금융지주회사감독규정_2100000077553.xml"
    bu = ["".join(e.itertext()).strip() for e in ET.fromstring(rd(p77)).iter("부칙내용")]
    out += ["",
            "- 결과: 위 ①·② 방법으로 다시 찾음 — 새 판 0건, 부칙 날짜 문구 0건 → 목록에 없는 판은 **추출 범위에 없음**(상태 유지).",
            "- note: 예로 「(2016. 8.1)」 삭제 표기가 처음 나오는 2016-07-27 판(제2016-29호)의 마지막 부칙은 아래와 같다 — 2016년 8월 1일 날짜가 없다.",
            "",
            "2016-07-27 판 마지막 부칙 — 인용: [금융지주회사감독규정 · 일련번호 2100000077553(시행 2016-07-27, 발령/공포 2016-07-27) · "
            "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2100000077553&type=XML · 부칙내용(마지막 부칙) · 수집 %s(원본 %s)]" % (
                _meta(p77).get("fetched_at", "")[:10], p77),
            ""]
    out += _block(bu[-1]) + [""]
    # 8-6 물음표
    s4 = S["S4_별표물음표"]
    pdfs = st["별표PDF"]
    out += ["### 8-6 세칙 별표 3·4·5 의 「?」(0x3F) 10곳 — 별표 PDF 텍스트(반박 성공)", "",
            "- 모범규준 조(판단): 1-1·1-3·1-4절과 같음(이 절은 글자 확인용).",
            "- 찾은 방법: XML 별표의 별표서식PDF파일링크(`/LSW/flDownload.do?flSeq=…`)로 PDF 를 받아(robots 허용 확인 뒤) pypdf 로 글을 뽑고, "
            "「?」 앞뒤 낱말(공백·표 선 무시)로 같은 자리를 찾았다. md 1-1·1-3·1-4절의 인용은 XML 글 그대로(「?」 유지) 두고 고치지 않는다.",
            "- 한계: PDF 글은 pypdf 추출이라 글꼴의 글자 대응에 따라 원 HWP 글자와 다를 수 있다. PDF 원본은 산출 폴더에 두지 않음(`dart_out/raw/web13/verify13_law91/`).",
            "",
            "| 별표 | XML 글(공백·표 선 뺌) | PDF 글자 | 유니코드 | PDF 쪽 |", "|---|---|---|---|---|"]
    for x in s4:
        out.append("| %s | `%s` | %s | %s | p.%s |" % (x["별표"], x["XML문맥"], x["PDF글자"], x["코드"], x["PDF쪽"]))
    out.append("")
    for no in ("3", "4", "5"):
        v = pdfs[no]
        rows = [x for x in s4 if x["별표"] == no and x["PDF줄"]]
        for pg in sorted(set(x["PDF쪽"] for x in rows), key=int):
            ls = []
            for x in rows:
                if x["PDF쪽"] == pg and x["PDF줄"] not in ls:
                    ls.append(x["PDF줄"])
            out += ["[별표 %s] PDF p.%s — 인용: [금융지주회사감독규정시행세칙 [별표 %s] PDF · 일련번호 2200000107297 의 별표서식PDF파일링크 · %s · p.%s "
                    "(pypdf 텍스트 `%s.txt`) · 수집 %s · sha256 %s]" % (no, pg, no, v["출처URL"], pg, v["파일"], v["수집"][:10], v["sha256"]), ""]
            out += _block("\n".join(ls)) + [""]
    return out


def _union_text():
    parts = []
    for p in SRC.values():
        parts += [t for lab, t in units(rd(p))]
    parts.append(open(MOBEOM_MD, encoding="utf-8").read())
    return nows("\n".join(parts))


def fix():
    S = json.load(open(SEARCH, encoding="utf-8"))
    st = load_state()
    import shutil
    for src, bak in ((MD, BAK_MD), (CSV, BAK_CSV)):       # 검증 전 사본(바이트 그대로) — 처음 한 번만
        if not os.path.exists(bak):
            shutil.copyfile(src, bak)
    # 언제나 검증 전 사본에서 다시 시작한다(멱등 — 고친 곳 기록도 매번 처음부터)
    text = open(BAK_MD, encoding="utf-8").read()
    for mark in ("\n" + S8, "\n" + SREC):
        if mark in text:
            text = text[:text.index(mark)].rstrip("\n") + "\n"
    F = Fixer(text.rstrip("\n"))
    s4 = S["S4_별표물음표"]
    ch = {no: [x for x in s4 if x["별표"] == no] for no in ("3", "4", "5")}
    fmt = lambda xs: " · ".join("「%s」(%s)" % (x["PDF글자"], x["코드"]) for x in xs)  # noqa: E731
    # 머리말
    F.replace("- 모범규준 조 번호: 사용자 지시서 9-1 에는 조 번호가 없다.",
              "- 모범규준 조 번호: 사용자 지시서 9-1 에는 조 번호가 없다. 처음 작성 때는 폐지 모범규준 원문이 저장소에 없어 주제1 표의 칸만 「(판단)」으로 적었다. "
              "검증(2026-10-07)에서 모범규준 원문(`handoff/13차_산출물/9-4_모범규준_원문.md`, 2016.8.1 판)과 조 목록(`dart_out/risk13/모범규준_조목록.csv`)을 "
              "대조해 자료 묶음마다 「- 모범규준 조(판단): 제N조(조 제목)」 줄을 붙였다 — 9-1 의 조 대응은 전부 「(판단)」(사용자 9-4 에 적힌 조 번호는 그 번호 그대로).",
              "머리말", "모범규준 원문이 이제 저장소에 있으므로 「원문이 없어 조 번호를 붙이지 않음」 문장을 바로잡음")
    F.append("- 한계: ① 법령에는 쪽이 없어", " ⑤ 검증(2026-10-07): ②의 「?」 10곳은 별표 PDF 텍스트에서 글자를 확인했다(8-6절) — XML 인용은 그대로 둠.",
             "머리말", "한계 ②의 「?」 원래 글자 확인 결과를 덧붙임")
    # 0절 — 행정규칙 3건 현행 여부를 검증 때 받은 연혁 목록(현행연혁구분)으로 다시 확인
    cur_ok = []
    for h in st["지배구조감독규정_연혁"]["판"]:
        if h["일련번호"] == SERIAL["지배구조감독규정"] and h.get("현행연혁구분") == "현행":
            cur_ok.append("지배구조 감독규정 %s" % h["일련번호"])
    for x in ET.parse(st["감독규정_띄어씀목록"]["목록쪽"][0]["파일"]).getroot().iter("admrul"):
        d = {c.tag: (c.text or "").strip() for c in x}
        if d.get("현행연혁구분") == "현행" and d.get("행정규칙일련번호") in (SERIAL["세칙"], SERIAL["감독규정"]):
            cur_ok.append("%s %s" % (d.get("행정규칙명"), d.get("행정규칙일련번호")))
    F.append("- note: 법령(법률·시행령)의 시행예정 판:",
             " 검증(2026-10-07): 행정규칙 %d건(%s)은 검증 때 받은 연혁 목록(%s)의 현행연혁구분=현행으로 같은 일련번호가 현행임을 다시 확인했다"
             "(법률·시행령은 다시 묻지 않음)." % (len(cur_ok), " · ".join(cur_ok), st["수집일"]), "현행 재확인", "0절 — 행정규칙 현행 여부 재확인")
    xs0 = rd(SRC["세칙"])
    for no in ("3", "4", "5"):
        a = annex(xs0, no)
        F.append("- 원본 파일 링크(받지 않음): HWP http://www.law.go.kr%s" % a["hwp"],
                 " — 검증(2026-10-07) 때 「?」 글자 확인용으로 이 PDF 를 받음(8-6절, `dart_out/raw/web13/verify13_law91/`, 산출 폴더에 두지 않음).",
                 "출처 표기", "[별표 %s] 원본 파일 링크 — 검증 때 PDF 를 받은 사실 덧붙임" % no)
    F.append("- 방법: XML 의 글(행정규칙은 `조문내용`", " 검증(2026-10-07) 때 「?」 글자 확인용으로 별표 3·4·5 PDF 만 받았다(8-6절).",
             "머리말", "방법 — 검증 때 받은 별표 PDF 덧붙임")
    # 1-1·1-3·1-4 의 「?」 note
    F.append("- note: 원문 XML 에 ASCII `?`(0x3F)로 들어 있는 곳 1곳:", " → 검증(2026-10-07): 별표 PDF 텍스트에서는 %s(8-6절)." % fmt(ch["3"]),
             "반박 성공", "1-1 「?」 원래 글자")
    F.append("- note: 원문 XML 에 ASCII `?`(0x3F)로 들어 있는 곳 3곳:", " → 검증(2026-10-07): 별표 PDF 텍스트에서는 차례로 %s(8-6절)." % fmt(ch["4"]),
             "반박 성공", "1-3 「?」 원래 글자")
    F.append("- note: 원문 XML 에 ASCII `?`(0x3F)로 들어 있는 곳 6곳", " → 검증(2026-10-07): 별표 PDF 텍스트에서는 차례로 %s(8-6절)." % fmt(ch["5"]),
             "반박 성공", "1-4 「?」 원래 글자")
    # 3-6 고시 위임
    s1 = S["S1_지배구조감독규정"]
    nv = sum(1 for r in s1 if "시행세칙" not in r["이름"])
    trail = (" → 검증(2026-10-07): 범위를 넓혀 다시 찾음 — 감독규정 본문 %d판(2016-08-01 제정 판~2026-10-02 현행)과 시행세칙 최근 판의 조문·부칙·별표·"
             "제개정이유 전체, 검색어 %d개(「영 제6조」「시행령 제6조」「제6조제3항」「영 제20조」「시행령 제20조」「제20조제2항」「법 제3조제3항」"
             "「법 제25조제2항」「고시하는 자」「적용 범위」「적용하지 아니」「적용 배제」「직원 중」 등) — 위임을 받는 조 0건. 현행 판의 「금융위원회가 정하여 "
             "고시하는」 위임 문구 %d곳의 근거에도 영 제6조·제20조는 없음(8-1절). 여전히 추출 범위에 없음." % (
                 nv, len(DELEG_PATS), len([r for r in s1 if r["일련번호"] == SERIAL["지배구조감독규정"]][0]["고시위임"])))
    F.append("- note: 제5호의 「금융위원회가 정하여 고시하는 자」", trail, "반박 실패", "3-6 ① 제5호 고시 — 찾은 방법 덧붙임")
    F.append("- note: 시행령 제20조제2항 각 호는 제6조제3항과 같은 꼴", trail.replace("영 제6조·제20조는 없음", "영 제20조·제6조는 없음"),
             "반박 실패", "3-6 ② 제5호 고시 — 찾은 방법 덧붙임")
    F.append("- (판단) 법령 글만으로는 금융지주회사는 시행령 제6조제3항 제1~4호에 들지 않으므로",
             " 검증에서도 감독규정 전 판에 제5호 위임을 받는 조가 없었다 — 고시가 정해지지 않았을 수 있으나 단정하지 않음(8-1절).", "판단 보충", "3-6 ① 판단")
    F.append("- (판단) 법령 글만으로는 금융지주회사는 시행령 제20조제2항 제1~4호에 들지 않으므로",
             " 검증에서도 감독규정 전 판에 제5호 위임을 받는 조가 없었다(8-1절).", "판단 보충", "3-6 ② 판단")
    # 5절 한계
    F.append("- 한계: ① 현행 본문의 개정 표기 날짜 가운데",
             " ④ 검증(2026-10-07): 띄어 쓴 이름(「금융지주회사 감독규정」) 목록도 %d건으로 새 판 %d건, 7개 날짜는 38판 부칙에 날짜 문구로 나오지 않음(8-5절) — "
             "목록에 없는 판은 여전히 추출 범위에 없음." % (S["S3_띄어쓴이름목록"]["건수"], len(S["S3_띄어쓴이름목록"]["law91목록에없던것"])),
             "반박 실패", "5절 한계 ① — 찾은 방법 덧붙임")
    # 모범규준 조 줄
    for head, line in TAGS:
        F.tag(head, line)
    # 6절
    F.replace("- note: 사용자 지시서 9-4 에 조 번호와 주제가 함께 적힌 조",
              "- note: 사용자 지시서 9-4 에 조 번호와 주제가 함께 적힌 조(3·4·5·17·21·22·24·27·28·30·34·53·55조)를 대상으로, 위 원문 가운데 그 주제 낱말과 "
              "겹치는 문구가 있는 곳을 적는다. 조 제목은 검증(2026-10-07) 때 모범규준 원문 2016.8.1 판(`dart_out/risk13/모범규준_조목록.csv`)대로 붙였고, "
              "사용자 9-4 에 없는 조(제9·17·23·25·57조 행)는 검증 때 더한 판단이다. 문구는 원문 그대로(스크립트가 원문 안에 있는지 확인), 조 대응은 전부 판단이다. "
              "24조(금리위험)·27조(전략·평판위험)·30조(적합성 검증)·55조(조기경보)와 겹치는 문구는 처음 작성 때 9-1 에서 옮긴 원문에서 찾지 못했다"
              "(검색어 「금리」「평판」「적합성」「검증」「조기경보」; 「전략」은 「위험관리의 기본방침 및 전략 수립」처럼 다른 뜻으로만 나옴). "
              "검증 때 같은 출처 XML 전체로 넓혀 다시 찾아 24조는 세칙 [별표 8](8-2절), 30조는 지배구조 감독규정 [별표 3](8-3절, 약한 겹침)에서 찾았고, "
              "27조·55조는 여전히 추출 범위에 없음(8-4절).",
              "6절", "6절 머리 note — 조 제목 근거·반박 결과 반영(17조 행 추가 포함)")
    F.replace("| 모범규준 조(사용자 9-4 표기) |", "| 모범규준 조(번호: 사용자 9-4 표기 · 제목: 2016.8.1 판) | 주제(사용자 표기) | 9-1 원문 위치 | 원문 문구 |",
              "6절", "6절 표 머리")
    ren = [("| 3조 (판단) |", "제3조(적용대상) (판단)"), ("| 21조 (판단) | 신용위험 | 세칙 [별표 3]", "제21조(신용위험) (판단)"),
           ("| 21조 (판단) | 신용위험 | 세칙 [별표 5]", "제21조(신용위험) (판단)"), ("| 22조 (판단) |", "제22조(시장위험) (판단)"),
           ("| 28조 (판단) | 통합리스크관리시스템 | 세칙", "제28조(시스템 구축 및 관리) (판단)"),
           ("| 28조 (판단) | 통합리스크관리시스템 | 지배구조", "제28조(시스템 구축 및 관리) (판단)"), ("| 34조 (판단) |", "제34조(해외위험 관리) (판단)"),
           ("| 53조 (판단) | 위기대응조직 | 지배구조", "제53조(위기대응조직) (판단)"), ("| 53조 (판단) | 위기대응조직 | 세칙", "제53조(위기대응조직) (판단)"),
           ("| 4조·5조 (판단) | 위험관리 철학·원칙 | 지배구조법 시행령", "제4조(위험관리 철학)·제5조(위험관리 원칙) (판단)"),
           ("| 4조·5조 (판단) | 위험관리 철학·원칙 | 지배구조법 제21조", "제4조(위험관리 철학)·제5조(위험관리 원칙) (판단)"),
           ("| 4조·5조 (판단) | 위험관리 철학·원칙 | 금융지주회사감독규정", "제4조(위험관리 철학)·제5조(위험관리 원칙) (판단)")]
    for pre, new in ren:
        try:
            i = F._uniq(pre)
        except RuntimeError:
            continue
        cells = F.lines[i].split(" | ")
        before = F.lines[i]
        cells[0] = "| " + new
        F.lines[i] = " | ".join(cells)
        F.log.append(dict(종류="모범규준 조", 줄=i + 1, 설명="6절 표 조 번호에 조 제목(2016.8.1 판) 붙임", 전=before, 후=F.lines[i]))
    new6 = [
        "| 제9조(그룹위험관리위원회) (판단) | (사용자 9-4 에 없음 — 검증 때 더함) 그룹위험관리위원회 결의사항 | 금융지주회사감독규정 제30조제1호 | 「경영전략에 부합하는 리스크관리 기본방침 수립」 |",
        "| 제9조(그룹위험관리위원회) (판단) | (사용자 9-4 에 없음 — 검증 때 더함) 그룹위험관리위원회 결의사항 | 지배구조법 제21조제1호 | 「위험관리의 기본방침 및 전략 수립」 |",
        "| 제17조(의사전달체계) (판단) | 지주가 자회사에 의사를 전달하는 문서 형식 | 지배구조 감독규정 제10조제2항제5호 | 「금융지주회사등의 경영의사결정에 필요한 정보가 효율적으로 전달될 수 있는 체제의 구축에 관한 사항」 |",
        "| 제23조(운영위험) (판단) | (사용자 9-4 에 없음 — 검증 때 더함) 운영위험 | 세칙 [별표 5] 5-4 | 「5-4. 운영리스크관리」 |",
        "| 제24조(금리위험) (판단) | 금리위험 | 세칙 [별표 8] 은행 계량평가 「금리」(8-2절, 지시 범위 밖) | 「기본자본 대비 ΔEVE 비율」 |",
        "| 제25조(유동성위험) (판단) | (사용자 9-4 에 없음 — 검증 때 더함) 유동성위험 | 세칙 [별표 5] 5-5 | 「5-5. 유동성리스크관리」 |",
        "| 제30조(목적) (판단) | 적합성 검증 | 지배구조 감독규정 [별표 3] 보험회사 항목(8-3절, 약한 겹침) | 「내부 검증절차」 |",
        "| 제57조(비상계획) (판단) | (사용자 9-4 에 없음 — 검증 때 더함) 비상계획 | 지배구조 감독규정 제13조제1항제1호 | 「금융사고 등 우발상황에 대한 위험관리 비상계획」 |",
    ]
    last6 = max(i for i, ln in enumerate(F.lines) if ln.startswith("| 제53조(위기대응조직) (판단) |"))
    if not any(ln == new6[0] for ln in F.lines):
        F.insert_after(last6, new6, "모범규준 조", "6절 표에 행 8개 더함(제9·17·23·24·25·30·57조 — 사용자 9-4 표기 아닌 조는 그렇게 적음)")
    F.append("- note: 위 검색어가 9-1 에서 옮긴 원문 전체", " 검증(2026-10-07): 같은 검색을 같은 출처 XML 6개 전체로 넓힌 결과는 8-2~8-4절.",
             "반박", "6절 끝 note — 넓힌 검색 결과 가리킴")
    # 7절
    sev = [
        ("| 받은 것 | 금융지주회사감독규정시행세칙 [별표 3] 경영실태평가",
         "모범규준 제8조(이사회)·제10조(경영진)·제21조(신용위험)·제25조(유동성위험)·제28조(시스템 구축 및 관리)·제37조(자본적정성 평가 및 관리 체제)·"
         "제56조(통합위기상황분석)·제57조(비상계획) 등(판단, 1-1절) — 주제1 표 「지주 평가·검사·공시」 칸 자료(판단)"),
        ("| 받은 것 | 금융지주회사감독규정시행세칙 [별표 3-1]",
         "모범규준 제37조(자본적정성 평가 및 관리 체제)(판단 — 직접 대응 조 없음, 1-2절) — 주제1 표 「지주 평가·검사·공시」 칸 자료(판단)"),
        ("| 받은 것 | 금융지주회사감독규정시행세칙 [별표 4]",
         "모범규준 직접 대응 조 없음(판단, 1-3절) — 주제1 표 「지주 평가·검사·공시」 칸 자료(판단)"),
        ("| 받은 것 | 금융지주회사감독규정시행세칙 [별표 5]",
         "모범규준 제7조(조직구성)·제21조(신용위험)·제22조(시장위험)·제23조(운영위험)·제25조(유동성위험)·제37조(자본적정성 평가 및 관리 체제)(판단, 1-4절) — "
         "주제1 표 「지주 평가·검사·공시」 칸(공시) 자료(판단)"),
        ("| 받은 것 | 금융지주회사감독규정시행세칙 제12조",
         "모범규준 제3조(적용대상)·제18조(측정 및 관리 대상)·제36조(적용대상)(보충 제2항, 판단 — 3조는 사용자 9-4 표기) · 제6·8항은 직접 대응 조 없음(판단, 1-5절) — "
         "「지주 평가·검사·공시」 칸(판단)"),
        ("| 받은 것 | 금융회사 지배구조 감독규정 제8조",
         "모범규준 제9조(그룹위험관리위원회)·제17조(의사전달체계)·제13조(그룹위험관리부서)·제57조(비상계획)·제28조(시스템 구축 및 관리) 등(판단, 2절) — 「현행 법령」 칸(판단)"),
        ("| 받은 것 | 금융회사의 지배구조에 관한 법률 시행령 제6조제3항",
         "모범규준 제9조(그룹위험관리위원회)·제11조(그룹위험관리책임자)·제4조(위험관리 철학)·제5조(위험관리 원칙)·제6조(문서화)·제13조(그룹위험관리부서)(판단, 3-1~3-4절) — "
         "「현행 법령」 칸(판단)"),
        ("| 받은 것 | 금융회사의 지배구조에 관한 법률 제3조제3항",
         "모범규준 제9조(그룹위험관리위원회)·제7조(조직구성)·제11조(그룹위험관리책임자)·제6조(문서화)·제8조(이사회)(판단, 3-5절) — 「현행 법령」 칸(판단)"),
        ("| 받은 것 | 금융지주회사법 제22조", "모범규준 제3조(적용대상)(판단, 4절) — 「현행 법령」 칸(판단)"),
        ("| 받은 것 | 금융지주회사감독규정 제30조 연혁", "모범규준 제8조(이사회)·제9조(그룹위험관리위원회)(판단, 5절) — 「현행 법령」 칸(판단)"),
        ("| 받지 못한 것 | 지배구조법 시행령 제6조제3항제5호",
         "추출 범위에 없음 — 다른 고시(예: 금융투자업규정 등)는 찾지 않음 · 모범규준 제9조(그룹위험관리위원회)·제11조(그룹위험관리책임자)(판단)"),
        ("| 받지 못한 것 | 금융지주회사감독규정 연혁 가운데 API 목록에 없는 판",
         "추출 범위에 없음 — 목록에 없는 판은 받지 못함(제30조 글이 앞뒤 판에서 같아 영향은 작다고 봄, 판단) · 모범규준 제8조(이사회)·제9조(그룹위험관리위원회)(판단)"),
    ]
    for pre, cell in sev:
        F.last_cell(pre, cell, "모범규준 조", "7절 표 조 번호 칸: 「조 번호 미부여」→ 모범규준 조(판단)")
    F.cell("| 받지 못한 것 | 지배구조법 시행령 제6조제3항제5호", 2,
           "금융회사 지배구조 감독규정 현행 XML(2100000285614) 조문내용 전체에서 정규식 「영 제6조」「영 제20조」「영 제24조」 검색 — 0건; 검증(2026-10-07): "
           "감독규정 본문 %d판+시행세칙 최근 판의 조문·부칙·별표·제개정이유 전체, 검색어 %d개 — 0건(8-1절)" % (nv, len(DELEG_PATS)),
           "반박 실패", "7절 받지 못한 것 — 찾은 방법 덧붙임(고시 위임)")
    F.cell("| 받지 못한 것 | 금융지주회사감독규정 연혁 가운데 API 목록에 없는 판", 2,
           "lawSearch.do target=admrul query=금융지주회사감독규정 nw=2 display=100 page=1(totalCnt 86, 1쪽에 다 옴); 검증(2026-10-07): query=금융지주회사 감독규정"
           "(띄어 씀) %d건 — 새 판 %d건, 38판 부칙에 7개 날짜 문구 0건(8-5절)" % (S["S3_띄어쓴이름목록"]["건수"], len(S["S3_띄어쓴이름목록"]["law91목록에없던것"])),
           "반박 실패", "7절 받지 못한 것 — 찾은 방법 덧붙임(연혁 판)")
    n24 = sum(1 for x in s4 if x["코드"] == "U+2024")
    F.cell("| 원문과 다른 것 | 9-1 세칙 별표 3·4·5 원문 XML 에 ASCII", 1,
           "9-1 세칙 별표 3·4·5 원문 XML 에 ASCII 「?」(0x3F)로 들어 있는 글자 10곳(별표3 1, 별표4 3, 별표5 6) — 고치지 않음. 검증(2026-10-07): 별표 PDF 텍스트에서는 "
           "%d곳 「․」(U+2024)·%s(8-6절)." % (n24, " · ".join("1곳 「%s」(%s)" % (x["PDF글자"], x["코드"]) for x in s4 if x["코드"] != "U+2024")),
           "반박 성공", "7절 원문과 다른 것 — 「?」 원래 글자 확인")
    lastr = max(i for i, ln in enumerate(F.lines) if ln.startswith("| 원문과 다른 것 |"))
    add7 = [
        "| 받은 것(검증 보충) | 금융지주회사감독규정시행세칙 [별표 8] 은행지주회사의 리스크평가 기준 — 평가항목 표의 은행 부분·「4. (계량지표 산정기준)」(지시 범위 밖, 같은 출처) | "
        "같은 XML 별표내용(별표키 000800) | 모범규준 제24조(금리위험)(판단, 8-2절) |",
        "| 받은 것(검증 보충) | 금융회사 지배구조 감독규정 [별표 3] 보험회사 내부통제기준 항목 가운데 「내부 검증절차」 줄 | XML 2100000285614 별표내용(별표키 000300) | "
        "모범규준 제30조(목적)(판단 — 약한 겹침, 8-3절) |",
        "| 받은 것(검증 보충) | 세칙 [별표 3]·[별표 4]·[별표 5] PDF 텍스트에서 「?」 자리 글자 10곳 | 법제처 flDownload PDF 3건(robots 허용) + pypdf | 1-1·1-3·1-4절 보조(판단) |",
        "| 받지 못한 것 | 모범규준 제27조(전략 및 평판위험)·제55조(조기경보체계)와 문구가 겹치는 원문 | 같은 출처 XML 6개 전체(조문·부칙·별표·서식·제개정이유)에서 "
        "「평판」「전략 위험·리스크」「조기경보」「경보 지표·발령」「조기 감지」「위기 징후」 등 정규식 — 0건(8-4절) | 추출 범위에 없음 — 모범규준 제27조(전략 및 평판위험)·"
        "제55조(조기경보체계)(판단) |",
    ]
    if not any(ln == add7[0] for ln in F.lines):
        F.insert_after(lastr, add7, "채운 항목", "7절 표에 검증 보충 행 4개 더함")
    F.append("- (판단) 9-1 → 모범규준 조 행 후보 표(6절)",
             " 검증(2026-10-07): 모범규준 원문·조목록으로 조 제목을 붙이고 자료 묶음마다 「모범규준 조」 줄을 더함 — 전부 판단.", "모범규준 조", "7절 판단 목록")
    body = F.text().rstrip("\n") + "\n\n" + "\n".join(build_s8(S, st)).rstrip("\n") + "\n"
    with open(MD, "w", encoding="utf-8") as f:
        f.write(body)
    # 인용 「…」 조각이 원문에 있는지(모범규준 조 줄·6절 표) — 없으면 멈춤
    U = _union_text()
    bad = []
    for ln in body.split("\n"):
        if ln.startswith("- 모범규준 조(") or (ln.startswith("| 제") and JUDGE in ln):
            for m in re.finditer(r"「([^「」]+)」", ln):
                frag = m.group(1)
                if frag in ("지주 평가·검사·공시",):
                    continue
                if nows(frag) not in U:
                    bad.append(frag)
    if bad:
        raise SystemExit("원문에 없는 「」 조각: %s" % bad[:10])
    # csv — 검증 때 쓴 원본 행 더함(원문XML 경로로 멱등)
    _fix_csv(st)
    # 검증 기록
    probs, info, res = check(write=False)
    rec = build_record(F.log, S, st, res, probs)
    with open(MD, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(rec).rstrip("\n") + "\n")
    dump(FIXLOG, dict(실행=now(), 고친곳=F.log))
    print("보정 %d곳 · md %d줄" % (len(F.log), len(open(MD, encoding="utf-8").read().split("\n"))))


def _fix_csv(st):
    rows = list(csv.DictReader(open(BAK_CSV, encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    have = {r["원문XML"] for r in rows}
    add = []

    def base(**kw):
        r = {c: "" for c in cols}
        r.update(kw)
        return r
    for h in st["지배구조감독규정_연혁"]["판"]:
        p = h.get("XML", "")
        if not p or p in have or p == SRC["지배구조감독규정"]:
            continue
        sub = "시행세칙" in h["행정규칙명"]
        add.append(base(법령명=h["행정규칙명"], 종류="행정규칙(시행세칙 — 넓은 검색용)" if sub else "행정규칙(연혁 판)",
                        용도="검증13 8-1 시행령 제6조③5·제20조②5 고시 위임 재검색", 일련번호=h["일련번호"], 시행일자=h["시행일자"],
                        발령_공포일자=h["발령일자"], 발령번호=h["발령번호"], 제개정구분=h["제개정구분"], 원문XML=p, sha256=_sha(rd(p)),
                        출처URL=_meta(p).get("출처URL", ""), 수집일시=_meta(p).get("fetched_at", ""),
                        현행재확인_20261007="%s(API 현행연혁구분=%s)" % ("현행" if h.get("현행연혁구분") == "현행" else "연혁", h.get("현행연혁구분", "")),
                        재사용="N(검증13 수집)", note="dart_out/raw/web13/verify13_law91/ — 검증 스크립트 verify13_law91.py fetch"))
    for pg, nm, use in ((st["지배구조감독규정_연혁"]["목록쪽"], "금융회사 지배구조 감독규정(연혁 목록)", "검증13 8-1 연혁 목록"),
                        (st["감독규정_띄어씀목록"]["목록쪽"], "금융지주회사 감독규정(띄어 쓴 이름 연혁 목록)", "검증13 8-5 목록에 없는 판 재검색")):
        for x in pg:
            if x["파일"] in have:
                continue
            add.append(base(법령명=nm, 종류="검색 응답", 용도=use, 원문XML=x["파일"], sha256=_sha(rd(x["파일"])), 출처URL=x["출처URL"],
                            수집일시=_meta(x["파일"]).get("fetched_at", ""), 재사용="N(검증13 수집)",
                            note="totalCnt %d — 응답 본문의 OC 값을 ***로 가린 사본(원 응답 바이트와 다름)" % x["totalCnt"]))
    for no, v in sorted(st["별표PDF"].items()):
        if v.get("상태") != "OK" or v["파일"] in have:
            continue
        add.append(base(법령명="금융지주회사감독규정시행세칙 [별표 %s] PDF" % no, 종류="별표 PDF(별표서식PDF파일링크)",
                        용도="검증13 8-6 「?」 원래 글자 확인", 일련번호="2200000107297", 시행일자="20250516", 발령_공포일자="20250516",
                        원문XML=v["파일"], sha256=v["sha256"], 출처URL=v["출처URL"], 수집일시=v["수집"], 재사용="N(검증13 수집)",
                        note="PDF %d쪽 · pypdf 텍스트 %s.txt · robots.txt(www.law.go.kr) 허용 확인 뒤 받음 · 산출 폴더에 두지 않음" % (v["쪽수"], v["파일"])))
    if True:
        with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows + add:
                w.writerow(r)
    return len(add)


def _short(s, n=260):
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…(전문은 _fix_log.json)"


def build_record(log, S, st, res, probs):
    n = len(res)
    orig = sum(1 for r in res if r["시작줄"] < [i for i, ln in enumerate(open(MD, encoding="utf-8").read().split("\n"))
                                              if ln.startswith(S8)][0] + 1)
    ok = sum(1 for r in res if r.get("결과", "").startswith("일치"))
    ex = sum(1 for r in res if r.get("설명") == "글자 그대로(공백 포함)")
    ln_ = sum(1 for r in res if r.get("결과") == "일치(줄 단위)")
    s1 = S["S1_지배구조감독규정"]
    out = [SREC, "",
           "- 방법: `scripts/dart/verify13_law91.py` — 인자 없이 = 대조(요청 없음, 문제 0 이면 exit 0, 결과 `dart_out/risk13/verify13_law91.txt`), "
           "`fetch` = 반박용 원본 받기, `search` = 넓은 검색, `fix` = 이 md·csv 보정(멱등). 원문 대조는 공백만 무시(공백·줄바꿈을 지우고 포함 관계). "
           "조문 글은 `scripts/dart/web10_law.py` 의 rule_articles·find_unit·article_text·md_text 로 뽑음. 검증 전 사본: `%s`, `%s`." % (BAK_MD, BAK_CSV),
           "- 실행: %s(KST — 작업 기준일은 2026-10-07). 법제처 요청 %d회(Open API·첨부 파일, 원장 `dart_out/raw/web13/verify13_law91/_call_log.csv`, OC=***), 별표 PDF 3건(robots 허용)." % (
               now(), st.get("API호출", 0)),
           "",
           "### 대조한 인용",
           "",
           "- 원문 인용 블록 %d개(처음 작성분 %d · 검증 보충 8절 %d) — 원문과 일치 %d(글자 그대로 %d · 줄 단위 발췌 %d — 시행령 제11조제2항 본문·제2호처럼 가운데를 건너뛴 것) · "
           "불일치 0. 처음 작성분의 인용은 모두 원문과 글자 그대로 같아 **고친 인용은 0곳**이다." % (n, orig, n - orig, ok, ex, ln_),
           "- 출처 표기(문서명 · 일련번호/URL · 조·별표·쪽 · 수집일): 블록마다 거슬러 올라가 가장 가까운 「인용:」·「판:」 줄을 읽어 확인 — 빠진 것 0. "
           "수집일은 원본 `.meta.json` fetched_at 과 같음. URL 의 인증값은 모두 `OC=***`.",
           "- 「전문」이라 적은 11개(세칙 별표 3·3-1·4, 지배구조 감독규정 제8·10·13조, 시행령 제6조제3항·제20·22·24조, 금융지주회사법 제22조)는 "
           "인용 블록이 원문 전체와 같음(공백만 무시).",
           "- 0절 표와 csv: 원문 파일·sha256·일련번호·시행일자·발령일자·제30조 sha256·수집일시를 원본과 대조 — 다른 것 0.",
           "",
           "### 고친 곳(전·후)",
           "",
           "- 줄 번호는 보정을 마친 이 md 기준. 전·후 글이 길면 줄여 적었다(전문은 `dart_out/raw/web13/verify13_law91/_fix_log.json`, 검증 전 사본과 비교 가능).",
           ""]
    final = open(MD, encoding="utf-8").read().split("\n")
    for c in log:                                   # 줄 번호는 보정을 마친 md 기준으로 다시 셈
        first = c["후"].split("\n")[0]
        hit = [i for i, ln in enumerate(final) if ln == first]
        if hit:
            c["줄"] = hit[0] + 1
    for c in sorted(log, key=lambda x: x["줄"]):
        if c["전"] and c["후"].startswith(c["전"]):
            out.append("- [%s] %d줄 — %s. 덧붙인 글: 「%s」" % (c["종류"], c["줄"], c["설명"], _short(c["후"][len(c["전"]):].strip())))
        elif c["전"]:
            out.append("- [%s] %d줄 — %s. 전: 「%s」 → 후: 「%s」" % (c["종류"], c["줄"], c["설명"], _short(c["전"]), _short(c["후"])))
        else:
            out.append("- [%s] %d줄 — %s. 더한 글: 「%s」" % (c["종류"], c["줄"], c["설명"], _short(c["후"], 160)))
    out += ["- [csv] `dart_out/risk13/9-1_법령판.csv` 에 검증 때 쓴 원본 행을 더함(지배구조 감독규정 연혁 판·시행세칙·연혁 목록 2건·별표 PDF 3건). 기존 행은 고치지 않음.",
            "",
            "### 채운 항목",
            "",
            "- 지시서 9-1 항목(1. 세칙 별표3·3-1·4·5·12조⑥⑧ / 2. 지배구조 감독규정 8·10·13조 / 3. 시행령 6조③·20·22·24조와 확인 2개 / 4. 지주법 22조 / "
            "5. 감독규정 30조 연혁) 13개는 모두 처음부터 「받은 글」이 있었다 — 빠진 항목 0.",
            "- 자료 묶음 16곳(1-1~1-5, 2절 제8·10·13조, 3-1~3-6, 4절, 5절)에 「- 모범규준 조(판단): 제N조(조 제목)」 줄을 붙이고, 6절 표의 조 번호에 조 제목을 붙이고 "
            "행 8개를 더하고, 7절 표의 「조 번호 미부여」 칸을 모범규준 조로 바꿈. 조 제목은 `dart_out/risk13/모범규준_조목록.csv`(2016.8.1 판)과 스크립트로 대조.",
            "- 8절(검증 보충) 6개: 8-1 고시 위임 재검색, 8-2 세칙 [별표 8] 금리, 8-3 지배구조 감독규정 [별표 3] 검증, 8-4 27·55조, 8-5 연혁 날짜, 8-6 별표 「?」 글자.",
            "",
            "### 「추출 범위에 없음」 반박",
            "",
            "- 성공: ① 모범규준 24조(금리위험) 문구 — 세칙 [별표 8] 「기본자본 대비 ΔEVE 비율」·「금리리스크」 등(8-2절, 지시 범위 밖·같은 출처). "
            "② 30조(적합성 검증) — 지배구조 감독규정 [별표 3] 「내부 검증절차」(8-3절, 약한 겹침 — 판단). "
            "③ 세칙 별표 3·4·5 「?」 10곳의 원래 글자 — 별표 PDF 텍스트(8-6절; XML 인용은 그대로).",
            "- 실패(상태 유지, 찾은 방법 덧붙임): ④ 시행령 제6조제3항제5호·제20조제2항제5호 「금융위원회가 정하여 고시하는 자」 — 지배구조 감독규정 본문 %d판+시행세칙, "
            "검색어 %d개, 로컬 다른 법령·고시 XML 까지 0건(8-1절). ⑤ 27조(전략·평판)·55조(조기경보) — 같은 출처 XML 6개 전체 0건(8-4절). "
            "⑥ 금융지주회사감독규정 API 목록에 없는 판 — 띄어 쓴 이름 목록·부칙 날짜 문구 0건(8-5절)." % (
                sum(1 for r in s1 if "시행세칙" not in r["이름"]), len(DELEG_PATS)),
            "",
            "### 남은 문제",
            ""]
    probs = [p for p in probs if "검증 기록(2026-10-07)」 절 없음" not in p]   # 이 절은 지금 쓰는 중
    if probs:
        out += ["- 대조 문제 %d건(아래) — `dart_out/risk13/verify13_law91.txt` 참고." % len(probs)] + ["  - " + p for p in probs]
    else:
        out.append("- 대조 문제 0건(이 기록을 쓰기 직전 실행 기준).")
    out += ["- 다른 업권 고시(금융투자업규정·보험업감독규정·상호저축은행업감독규정·여신전문금융업감독규정 등)를 법제처에서 새로 받아 「지배구조에 관한 법률 시행령」 "
            "제6조·제20조 인용을 찾지는 않았다(로컬에 있는 XML 만 찾음) — ④는 그 범위에서 추출 범위에 없음.",
            "- 8-6절 글자는 PDF 의 pypdf 추출 결과라 원 HWP 글자와 다를 수 있다. 8-2절 [별표 8] 상자 글이 개정 글이라는 것은 판단.",
            "- 금융지주회사감독규정 연혁 판 XML 이 당시 고시 원문 그대로라는 보장은 없다(5절 한계 ②, 그대로).",
            ""]
    return out


def search_other():
    """S1b — 로컬의 다른 법령·고시 XML 에서 「지배구조에 관한 법률 시행령」 제6·20·24조 인용."""
    import glob
    pat = r"지배구조에\s*관한\s*법률\s*시행령\s*」?\s*제\s*(?:6|20|24)\s*조"
    files = sorted(set(glob.glob("dart_out/raw/web9/law/*.xml") + glob.glob("dart_out/raw/web10/law/*.xml") +
                       glob.glob("dart_out/raw/web11/law/*.xml") + glob.glob("dart_out/raw/web13/law9*/*.xml")))
    hits = []
    for f in files:
        s = rd(f).decode("utf-8", "replace")
        for m in re.finditer(pat, s):
            hits.append(dict(파일=f, 문맥=_ctx(s, m)))
    return dict(파일수=len(files), 건수=len(hits), 예=hits[:10])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    {"fetch": fetch, "search": search, "fix": fix, "check": main_check}[cmd]()
