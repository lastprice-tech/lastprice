# -*- coding: utf-8 -*-
"""13차 9-2 의 1·2·3·5번 검증·보정 — handoff/13차_산출물/9-2-1_2_ORSA_연혁.md · 9-2-3_5_별표37_별표22.md,
dart_out/risk13/9-2-1_2_판목록.csv · 9-2-3_별표37_항목대조.csv · 9-2-3_별표37_줄대조.csv · 9-2-5_별표22_제목줄.csv.

    python3 -I scripts/dart/verify13_law92.py            # 대조만(요청 없음). 문제 0 이면 exit 0.
                                                          #   결과 → dart_out/risk13/verify13_law92.txt
    LAW_DELAY=1.0 python3 -I scripts/dart/verify13_law92.py fetch
        # 이분 탐색이 건너뛴 판 받기(법제처 lawService.do target=admrul ID=<일련번호> type=XML):
        #   보험업감독규정 연혁 목록의 받지 않은 판 전부 · 세칙 연혁 순번 0~136(작은 판)과 182 ·
        #   같은 행정규칙ID 의 옛 이름(보험감독규정·보험감독규정시행세칙) 판 전부 · 세칙 큰 판 사이 경계는 이분 탐색.
        #   원본 → dart_out/raw/web13/verify13_law92/ (원장 _call_log.csv, OC=*** 로 가림). 이미 받은 판은 다시 받지 않음.
    python3 -I scripts/dart/verify13_law92.py scan       # 받은 판 전부에서 제7-5조·제5-6조의2·[별표 37] 떼어 대조 → _scan.json
    python3 -I scripts/dart/verify13_law92.py search     # 「추출 범위에 없음」 반박용 넓은 검색 → _search.json
    python3 -I scripts/dart/verify13_law92.py fix        # md·csv 보정(멱등). 고친 곳은 _fix_log.json 과 md 「검증 기록」에

· 원문 대조는 공백만 무시한다(공백·줄바꿈을 지운 뒤 같음/포함). 글자 하나라도 다르면 문제로 센다.
· 조 글은 이 스크립트가 따로 뽑는다(조문내용 요소 전부를 이은 글에서 공백 무시로 찾고, 바로 뒤가 다음 조·장·절 표지인지 본다)
  — 수집 스크립트의 find_jo 와 독립. 판목록 csv 의 글 sha256 재계산에만 find_jo(web13_law92a, 읽기만)를 쓴다.
· OC·DART 키 값은 출력·파일 어디에도 쓰지 않는다(값이 산출물에 들어 있는지 검사만 하고 「있음/없음」만 적음).
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
import web13_law92 as P  # noqa: E402 — info·annex_units·addenda·load_hist (읽기만)
import web13_law92a as W  # noqa: E402 — find_jo·norm (읽기만, csv sha 재계산용)
from web13 import RAW, WORK, OUT, save, now, write_csv  # noqa: E402

TASK = "verify13_law92"
VDIR = os.path.join(RAW, TASK)
LEDGER = os.path.join(VDIR, "_call_log.csv")
STATE = os.path.join(VDIR, "_fetch_state.json")
SCAN = os.path.join(VDIR, "_scan.json")
SEARCH = os.path.join(VDIR, "_search.json")
FIXLOG = os.path.join(VDIR, "_fix_log.json")
MD1 = os.path.join(OUT, "9-2-1_2_ORSA_연혁.md")
MD2 = os.path.join(OUT, "9-2-3_5_별표37_별표22.md")
CSV_VER = os.path.join(WORK, "9-2-1_2_판목록.csv")
CSV_ITEMS = os.path.join(WORK, "9-2-3_별표37_항목대조.csv")
CSV_LINES = os.path.join(WORK, "9-2-3_별표37_줄대조.csv")
CSV_22 = os.path.join(WORK, "9-2-5_별표22_제목줄.csv")
REPORT = os.path.join(WORK, "verify13_law92.txt")
MOBEOM_MD = os.path.join(OUT, "9-4_모범규준_원문.md")
MOBEOM_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MD24 = os.path.join(OUT, "9-2-4_ORSA_보도자료.md")
REQUEST = "/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/curate13/REQUEST13.md"
TODAY = "2026-10-07"
SREC = "## 검증 기록(2026-10-07)"
# 13차 정합성 보정(scripts/dart/fix13_C.py): 절 제목 날짜 KST(R5)·연혁·출처 묶음의 조 번호 칸(R2)도 대조가 받도록
SREC_ANY = (SREC, "## 검증 기록(2026-10-08 KST)")
NOART = "조 번호 해당 없음(연혁·출처 자료)"

REG, SEC = P.REG, P.SEC
XML_DIRS = [os.path.join("dart_out", "raw", w, "law") for w in ("web9", "web10", "web11")] + [
    os.path.join(RAW, "law92"), os.path.join(RAW, "law92a"), VDIR]
REG_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독규정_2100000279112.xml")
SEC_XML9 = os.path.join("dart_out", "raw", "web9", "law", "보험업감독업무시행세칙_2200000108939.xml")
A37_MD10 = os.path.join("handoff", "원문_10차", "세칙_별표37.md")
A37_PDF10 = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37_pdf.txt")
A37_HWP2MD = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37_hwp2md.md")
A37_PDF = os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37.pdf")
A37_CSV10 = os.path.join("handoff", "원문_10차", "세칙_별표37_표시.csv")
B92 = os.path.join(RAW, "law92b")
A37_XMLTXT = os.path.join(B92, "별표37_별표내용.txt")
A22_TXT = os.path.join(B92, "별표22_별표내용.txt")
A221_TXT = os.path.join(B92, "별표22-1_별표내용.txt")
HIST_XML = [os.path.join(RAW, "law92", f) for f in sorted(os.listdir(os.path.join(RAW, "law92")))
            if f.startswith("연혁검색_") and f.endswith(".xml")]
OLD_NAMES = {REG: ("보험감독규정",), SEC: ("보험감독규정시행세칙", "보험감독규정 시행세칙")}
ORSA_RE = re.compile(r"자체\s*위험\s*및\s*지급여력\s*평가")
SEC_SMALL_MAX = 136          # 세칙 연혁 순번 136(2020.10 앞)까지는 판 XML 이 0.2MB 안팎 — 전부 받는다
SEC_EXTRA = ["2200000108867"]  # 세칙 순번 182(2026.06.29 과 2026.08.28 사이) — [별표 37]·제5-6조의2 의 신설 뒤 연혁을 닫는다


def nows(s):
    return re.sub(r"\s+", "", s or "")


def _sha(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest() if b else ""


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def _meta(p):
    mp = (p or "") + ".meta.json"
    return json.load(open(mp, encoding="utf-8")) if p and os.path.exists(mp) else {}


def dump(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".part", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(p + ".part", p)


def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else (default if default is not None else {})


def xml_path(serial):
    for d in XML_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith("_%s.xml" % serial):
                return os.path.join(d, f)
    return None


def stage_of(p):
    if not p:
        return ""
    if "/web9/" in p:
        return "9차(web9)"
    if "/law92/" in p:
        return "9-2 수집(law92)"
    if "/law92a/" in p:
        return "9-2 수집(law92a)"
    if "/%s/" % TASK in p:
        return "검증(verify13_law92)"
    return p


# ── 연혁 목록(같은 날 9-2 수집 에이전트가 받은 nw=2 검색 응답) ───────────────────
def hist_all():
    """검색 응답 원본(쪽마다)의 행 전부 → [dict] (이름 필터 없이, 일련번호로 중복 제거)."""
    seen, out = set(), []
    for p in HIST_XML:
        for it in ET.parse(p).getroot().iter("admrul"):
            d = {c.tag: (c.text or "").strip() for c in it}
            if d.get("행정규칙일련번호") in seen:
                continue
            seen.add(d["행정규칙일련번호"])
            d["_검색응답"] = p
            out.append(d)
    return out


def old_rows(name):
    """같은 행정규칙ID 인데 옛 이름이라 연혁 목록(이름 필터)에서 빠진 판 — 발령일자 순."""
    ids = {r["행정규칙ID"] for r in P.load_hist(name)}
    rows = [r for r in hist_all() if r.get("행정규칙명") in OLD_NAMES[name] and r.get("행정규칙ID") in ids]
    return sorted(rows, key=lambda r: (r.get("발령일자", ""), r.get("행정규칙일련번호", "")))


# ── fetch ─────────────────────────────────────────────────────────────────
def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


def fetch_one(client, name, serial, why):
    p = xml_path(serial)
    if p:
        return p, False
    st, body, murl, host = client.api("lawService.do", target="admrul", ID=serial, type="XML")
    if not body:
        raise RuntimeError("빈 응답 %s" % murl)
    b = ET.fromstring(body).find("행정규칙기본정보")
    got = (b.findtext("행정규칙일련번호") or "").strip() if b is not None else ""
    if got != serial:
        raise RuntimeError("요청 %s 인데 응답 일련번호 %s — %s" % (serial, got, murl))
    n_oc = client.count_oc(body)
    body = client.mask(body)
    p, _ = save(TASK, "%s_%s.xml" % (nows(name), serial), body,
                dict(출처URL=murl, http_status=st, fetched_at=now(), 호스트=host, 받은까닭=why,
                     OC가림=("응답 본문의 OC 값 %d곳을 저장 전 *** 로 바꿈" % n_oc) if n_oc else ""))
    return p, True


def fetch():
    client = _client()
    st = load(STATE, {"받음": [], "실패": []})
    plan = []
    for i, r in enumerate(P.load_hist(REG)):
        plan.append((REG, r["행정규칙일련번호"], "감독규정 연혁 순번 %d — 이분 탐색이 건너뛴 판 전수" % i))
    for i, r in enumerate(P.load_hist(SEC)):
        if i <= SEC_SMALL_MAX or r["행정규칙일련번호"] in SEC_EXTRA:
            plan.append((SEC, r["행정규칙일련번호"], "세칙 연혁 순번 %d — 이분 탐색이 건너뛴 판" % i))
    for name in (REG, SEC):
        for r in old_rows(name):
            plan.append((r["행정규칙명"], r["행정규칙일련번호"], "같은 행정규칙ID %s 의 옛 이름 판(연혁 목록 이름 필터로 빠짐)"
                         % r["행정규칙ID"]))
    todo = [x for x in plan if not xml_path(x[1])]
    print("계획 %d판 · 이미 있음 %d · 받을 것 %d" % (len(plan), len(plan) - len(todo), len(todo)))
    for k, (name, serial, why) in enumerate(todo):
        try:
            p, new = fetch_one(client, name, serial, why)
            st["받음"].append(dict(규정=name, 일련번호=serial, 파일=p, 까닭=why, 시각=now()))
        except Exception as e:  # noqa: BLE001 — 사유를 남기고 다음 판
            st["실패"].append(dict(규정=name, 일련번호=serial, 사유=str(e)[:200], 시각=now()))
            print("  실패 %s %s: %s" % (name, serial, str(e)[:120]))
        if k % 20 == 0:
            dump(STATE, st)
            print("  %d/%d (%s)" % (k + 1, len(todo), serial), flush=True)
    dump(STATE, st)
    # 세칙 큰 판 구간: 실질·표기 변화 경계가 인접 판 사이로 닫힐 때까지 가운데 판(단조 가정)
    for _ in range(30):
        S = scan(write=False)
        gaps = []
        for key in ("세칙|제5-6조의2", "세칙|[별표 37]"):
            for g in S[key]["열린경계"]:
                gaps.append((key, g))
        if not gaps:
            break
        key, (lo, hi) = gaps[0]
        mid = (lo + hi) // 2
        r = P.load_hist(SEC)[mid]
        print("경계 열림 %s 순번 %d~%d → %d(%s) 받음" % (key, lo, hi, mid, r["행정규칙일련번호"]), flush=True)
        p, new = fetch_one(client, SEC, r["행정규칙일련번호"], "세칙 %s 경계 이분 탐색(순번 %d~%d)" % (key, lo, hi))
        st["받음"].append(dict(규정=SEC, 일련번호=r["행정규칙일련번호"], 파일=p, 까닭="경계 이분 탐색", 시각=now()))
        dump(STATE, st)
    print("요청 %d회 · 실패 %d" % (client.n_calls, len(st["실패"])))


# ── scan(받은 판 전부) ────────────────────────────────────────────────────────
def info(xb):
    return P.info(xb)


def all_text(xb):
    """XML 의 모든 글(조문·부칙·별표·개정문) — ORSA 문구가 어디든 처음 나온 판을 보려고."""
    return "".join(ET.fromstring(xb).itertext())


def annex(xb, no, gaji="00"):
    u = P.annex_units(xb, no, gaji, "별표")
    return u[0] if u else None


def norm(s):
    return W.norm(s)


def _cmp(prev, txt):
    if prev is None:
        return "처음 받은 판"
    if not prev and not txt:
        return "같음(둘 다 없음)"
    if not prev:
        return "없음→있음"
    if not txt:
        return "있음→없음"
    if prev == txt:
        return "같음"
    if norm(prev) == norm(txt):
        return "표기만 다름(판단)"
    return "글 바뀜"


def scan(write=True):
    """연혁 목록(이름 필터) 판마다 받은 XML 이 있으면 조·별표 글을 떼어 앞 받은 판과 비교. 옛 이름 판은 따로."""
    out = {}
    cache = {}

    def xb_of(s):
        p = xml_path(s)
        if not p:
            return None, None
        if s not in cache:
            cache.clear()
            cache[s] = rd(p)
        return cache[s], p

    for name, label, key in ((REG, "제7-5조", "감독규정|제7-5조"), (SEC, "제5-6조의2", "세칙|제5-6조의2"),
                             (SEC, "[별표 37]", "세칙|[별표 37]")):
        rows = P.load_hist(name)
        res, prev, prev_i = [], None, None
        for i, r in enumerate(rows):
            s = r["행정규칙일련번호"]
            xb, p = xb_of(s)
            row = dict(순번=i, 일련번호=s, 발령일자=r.get("발령일자", ""), 시행일자=r.get("시행일자", ""),
                       발령번호=r.get("발령번호", ""), 제개정=r.get("제개정구분명", ""), 받음="N")
            if xb is None:
                res.append(row)
                continue
            inf = P.info(xb)
            if label.startswith("[별표"):
                a = annex(xb, "0037")
                txt = a["별표내용"] if a else ""
            else:
                txt = W.find_jo(xb, label)[0]
            orsa_any = bool(ORSA_RE.search(all_text(xb)))
            c = _cmp(prev, txt)
            row.update(받음="Y", 파일=p, 단계=stage_of(p), XML_발령일자=inf.get("발령일자", ""),
                       XML_시행일자=inf.get("시행일자", ""), XML_발령번호=inf.get("발령번호", ""),
                       있음="Y" if txt else "N", ORSA="Y" if ORSA_RE.search(txt or "") else "N",
                       ORSA_XML어디든="Y" if orsa_any else "N", 글자수=len(txt), 글_sha256=_sha(txt),
                       앞받은판=(rows[prev_i]["행정규칙일련번호"] if prev_i is not None else ""),
                       인접=("Y" if prev_i is not None and prev_i == i - 1 else ("N" if prev_i is not None else "")),
                       앞판대비=c)
            res.append(row)
            prev, prev_i = txt, i
        got = [x for x in res if x["받음"] == "Y"]
        # 열린 경계: 앞 받은 판과 다르고(실질·표기 모두) 사이에 받지 않은 판이 있는 곳
        gaps = []
        for x in got:
            if x["인접"] == "N" and x["앞판대비"] not in ("같음", "같음(둘 다 없음)"):
                lo = [y for y in got if y["일련번호"] == x["앞받은판"]][0]["순번"]
                gaps.append((lo, x["순번"]))
        flag = "ORSA" if label == "제7-5조" else "있음"
        seq = [x[flag] for x in got]
        mono = "".join(seq).lstrip("N").find("N") < 0          # N…N Y…Y 꼴
        first = next((x for x in got if x[flag] == "Y"), None)
        before = None
        if first:
            k = got.index(first)
            before = got[k - 1] if k else None
        unrec = [x["순번"] for x in res if x["받음"] == "N"]
        out[key] = dict(규정=name, 대상=label, 목록판수=len(rows), 받은판수=len(got), 받지않은순번=_ranges(unrec),
                        단조=mono, 판정기준=flag,
                        처음Y=(first and {k2: first[k2] for k2 in ("순번", "일련번호", "발령일자", "시행일자", "발령번호")}),
                        처음Y_앞판=(before and {k2: before[k2] for k2 in ("순번", "일련번호", "발령일자", flag)}),
                        처음Y_경계인접=bool(first and before and before["순번"] == first["순번"] - 1),
                        ORSA_XML어디든_처음=next(({k2: x[k2] for k2 in ("순번", "일련번호", "발령일자")}
                                             for x in got if x["ORSA_XML어디든"] == "Y"), None),
                        변화=[{k2: x[k2] for k2 in ("순번", "일련번호", "발령일자", "시행일자", "앞판대비", "인접", "글자수")}
                            for x in got if x["앞판대비"] not in ("같음", "같음(둘 다 없음)", "처음 받은 판")],
                        열린경계=gaps, 판=res)
    # 옛 이름 판(같은 행정규칙ID)
    old = []
    for name in (REG, SEC):
        for r in old_rows(name):
            s = r["행정규칙일련번호"]
            xb, p = xb_of(s)
            row = dict(목록이름=name, 행정규칙명=r["행정규칙명"], 일련번호=s, 발령일자=r.get("발령일자", ""),
                       시행일자=r.get("시행일자", ""), 제개정=r.get("제개정구분명", ""), 행정규칙ID=r.get("행정규칙ID", ""),
                       받음="N")
            if xb is not None:
                a = annex(xb, "0037")
                row.update(받음="Y", 파일=p, 제7_5조=("Y" if W.find_jo(xb, "제7-5조")[0] else "N"),
                           제5_6조의2=("Y" if W.find_jo(xb, "제5-6조의2")[0] else "N"),
                           별표37=("Y" if a else "N"), 별표37_제목=(a["별표제목"] if a else ""),
                           ORSA_XML어디든=("Y" if ORSA_RE.search(all_text(xb)) else "N"),
                           ORSA_부분=re.sub(r"\s+", "", "".join(m.group(0) for m in ORSA_RE.finditer(all_text(xb))))[:40])
            old.append(row)
    out["옛이름판"] = old
    out["만든때"] = now()
    if write:
        dump(SCAN, out)
        for k, v in out.items():
            if isinstance(v, dict):
                print("%s: 목록 %d · 받은 %d · 단조 %s · 처음Y %s(앞 판 %s, 인접 %s) · 변화 %d · 열린 경계 %s · 받지 않은 순번 %s" % (
                    k, v["목록판수"], v["받은판수"], v["단조"], v["처음Y"] and v["처음Y"]["발령일자"],
                    v["처음Y_앞판"] and v["처음Y_앞판"]["발령일자"], v["처음Y_경계인접"], len(v["변화"]),
                    v["열린경계"], v["받지않은순번"][:200]))
        print("옛 이름 판 %d(받음 %d): ORSA 어디든 Y %d · 제7-5조 Y %d · 제5-6조의2 Y %d · 별표37 Y %d" % (
            len(old), sum(1 for x in old if x["받음"] == "Y"), sum(1 for x in old if x.get("ORSA_XML어디든") == "Y"),
            sum(1 for x in old if x.get("제7_5조") == "Y"), sum(1 for x in old if x.get("제5_6조의2") == "Y"),
            sum(1 for x in old if x.get("별표37") == "Y")))
    return out


def _ranges(nums):
    out, st, pv = [], None, None
    for n in nums + [None]:
        if st is None:
            st = pv = n
            continue
        if n is not None and n == pv + 1:
            pv = n
            continue
        out.append(("%d" % st) if st == pv else ("%d~%d" % (st, pv)))
        st = pv = n
    return ", ".join(x for x in out if x != "None")


# ── 원문 인용 대조 ───────────────────────────────────────────────────────────
FENCE = re.compile(r"^\s*```")


def md_blocks(lines):
    """md 의 원문 인용 — 코드 블록(```)과 > 인용 블록 → [dict(시작줄, 끝줄, 종류, 글)] (줄 번호 1부터)."""
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


def _bracket_with(ln, key="수집"):
    """줄에서 key 가 든 바깥 [ … ] (안에 [별표 37] 같은 괄호가 겹쳐도 됨)."""
    i = 0
    while True:
        i = ln.find("[", i)
        if i < 0:
            return None
        depth, j = 0, i
        while j < len(ln):
            if ln[j] == "[":
                depth += 1
            elif ln[j] == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        seg = ln[i + 1:j]
        if key in seg:
            return seg
        i = i + 1


def find_cite(lines, start):
    """블록 바로 앞(빈 줄 건너뜀)의 출처 줄 → (줄 번호, 출처 줄 전체, 괄호 안)."""
    k = start - 2
    while k >= 0 and not lines[k].strip():
        k -= 1
    if k < 0:
        return None, "", ""
    seg = _bracket_with(lines[k])
    return (k + 1, lines[k], seg) if seg else (None, lines[k], "")


def jo_units(xb):
    """조문내용 요소 글 목록(문서 순서)."""
    return ["".join(e.itertext()) for e in ET.fromstring(xb).iter("조문내용")]


NEXT_MARK = re.compile(r"^(?:제\d+-\d+조(?:의\d+)?|제\d+조(?:의\d+)?|제\d+장|제\d+절|제\d+관)")


def article_full(xb, label):
    """조 전문(공백 무시 비교용): 조문내용 요소에서 「제7-5조(」 로 시작하는 곳부터 다음 조·장·절·관 표지 앞까지.
    수집 스크립트의 find_jo 와 따로 — 요소를 이은 글을 공백 없이 보고 경계를 찾는다."""
    want = nows(label) + "("
    whole = nows("\n".join(jo_units(xb)))
    k = 0
    while True:
        k = whole.find(want, k)
        if k < 0:
            return None
        if label == "제7-5조" and whole[k:k + len("제7-5조의")] == "제7-5조의":
            k += 1
            continue
        break
    m = None
    pos = k + len(want)
    for mm in re.finditer(r"제\d+-\d+조(?:의\d+)?(?=\(|삭제)|제\d+장|제\d+절|제\d+관", whole[pos:]):
        cand = mm.group(0)
        if cand == nows(label):
            continue
        m = mm
        break
    return whole[k: pos + (m.start() if m else len(whole) - pos)]


def addenda(xb):
    return P.addenda(xb)


def gaejeongmun(xb):
    g = ET.fromstring(xb).find("개정문")
    return "".join(g.itertext()) if g is not None else None


def pdf_pages():
    txt = open(A37_PDF10, encoding="utf-8").read()
    parts = re.split(r"^=== p\.(\d+) ===$", txt, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def annex_lines(xb, no, gaji="00"):
    a = annex(xb, no, gaji)
    return a["별표내용"].split("\n") if a else None


def table_lines_before(lines, start):
    """블록 앞 표(| 줄 | 위치 |)의 줄 번호 목록 — 「위 표의 줄만 표의 차례대로」 인용용."""
    k = start - 2
    while k >= 0 and not lines[k].startswith("|"):
        k -= 1
    out = []
    while k >= 0 and lines[k].startswith("|"):
        m = re.match(r"^\|\s*(\d+)\s*\|", lines[k])
        if m:
            out.append(int(m.group(1)))
        k -= 1
    return list(reversed(out))


def _fmt(d):
    return "%s.%s.%s" % (d[:4], d[4:6], d[6:8]) if len(d) == 8 else d


def _cmp_text(quote, src, mode):
    """mode: 같음(공백 무시 전체 같음) / 포함 / 줄(줄마다 차례로 포함)."""
    q, s = nows(quote), nows(src)
    if not q:
        return "빈 인용", ""
    if mode == "같음":
        if q == s:
            return "일치", "전문 — 공백 무시 같음" + ("(글자 그대로)" if quote.strip() == (src or "").strip() else "")
        if q in s:
            return "불일치", "원문의 일부만 옮김(전문 아님)"
    if q in s:
        return "일치", "공백 무시 포함"
    pos = 0
    for ln in [x for x in quote.split("\n") if x.strip()]:
        k = s.find(nows(ln), pos)
        if k < 0:
            return "불일치", "원문에 없는 줄: " + ln.strip()[:90]
        pos = k + len(nows(ln))
    return "일치(줄 단위)", "줄마다 원문에 있고 차례도 같음(사이를 건너뛴 발췌)"


def resolve(lines, b, cl, cline, seg):
    """출처 → 대조 결과 dict. 원문 파일·위치를 출처 괄호 글에서 읽는다."""
    r = dict(원문="", 결과="원문 못 찾음", 설명="", 출처문제=[])
    # 출처 표기 요소
    miss = []
    if not re.match(r"\s*보험업감독(규정|업무시행세칙)", seg) and not ("보도자료" in seg and "fsc.go.kr" in seg):
        miss.append("문서명")
    if "일련번호" not in seg and "flSeq=" not in seg and "fsc.go.kr/no010101/" not in seg:
        miss.append("일련번호/URL")
    if "law.go.kr" not in seg and "fsc.go.kr" not in seg:
        miss.append("URL")
    if not re.search(r"수집\s*20\d\d-\d\d-\d\d", seg):
        miss.append("수집일")
    if not re.search(r"제\d+-\d+조|부칙|개정문|제개정이유|\[별표\s*\d+(?:-\d+)?\]\s*별표내용|p\.\d+|md \d+줄", seg):
        miss.append("위치(조·부칙·별표·쪽·줄)")
    if "OC=" in seg and "OC=***" not in seg:
        miss.append("OC 가림")
    r["출처문제"] += ["출처 표기에 빠진 것: " + "·".join(miss)] if miss else []
    cm = re.search(r"수집\s*(20\d\d-\d\d-\d\d(?:T[\d:]+\+\d\d:\d\d)?)", seg)
    # PDF
    if "flSeq=168886133" in seg:
        pm = re.search(r"p\.(\d+)(?:~(\d+))?", seg)
        pg = pdf_pages()
        a, z = int(pm.group(1)), int(pm.group(2) or pm.group(1))
        src = "\n".join(pg[i] for i in range(a, z + 1))
        r["원문"] = "%s p.%d~%d" % (A37_PDF10, a, z)
        mode = "줄" if z > a else "포함"
        r["결과"], r["설명"] = _cmp_text(b["글"], src, mode)
        meta = _meta(A37_PDF)
        if cm and meta.get("fetched_at", "")[:10] != cm.group(1)[:10]:
            r["출처문제"].append("수집일 %s ↔ PDF meta %s" % (cm.group(1), meta.get("fetched_at")))
        return r
    if "fsc.go.kr/no010101/72075" in seg:
        src = open(PRESS_HWP, encoding="utf-8").read()
        r["원문"] = PRESS_HWP
        r["결과"], r["설명"] = _cmp_text(b["글"], src, "포함")
        meta = _meta(PRESS_HWP[:-3])
        if not cm or cm.group(1) != meta.get("fetched_at"):
            r["출처문제"].append("수집 %s ↔ hwp meta %s" % (cm and cm.group(1), meta.get("fetched_at")))
        pdf = open(PRESS_PDF, encoding="utf-8").read()
        pm = re.search(r"p\.(\d+)", seg)
        parts = re.split(r"^=== p\.(\d+) ===$", pdf, flags=re.M)
        pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
        first = nows(b["글"].strip().split("\n")[0])
        if not pm or first not in nows(pages.get(int(pm.group(1)), "")):
            r["출처문제"].append("PDF 쪽 표기 %s 에 첫 줄이 없음" % (pm and pm.group(0)))
        return r
    if "flSeq=168886111" in seg:
        lm = re.search(r"md (\d+)줄", seg)
        L = open(A37_MD10, encoding="utf-8").read().split("\n")
        src = L[int(lm.group(1)) - 1]
        r["원문"] = "%s %s줄" % (A37_MD10, lm.group(1))
        r["결과"], r["설명"] = _cmp_text(b["글"], src, "같음")
        meta = _meta(os.path.join("dart_out", "raw", "web10", "annex37", "세칙_별표37.hwp"))
        if cm and meta.get("fetched_at", "")[:10] != cm.group(1)[:10]:
            r["출처문제"].append("수집일 %s ↔ HWP meta %s" % (cm.group(1), meta.get("fetched_at")))
        return r
    sm = re.search(r"일련번호\s*(\d+)", seg)
    if not sm:
        r["설명"] = "일련번호 없음"
        return r
    serial = sm.group(1)
    p = xml_path(serial)
    if not p:
        r["설명"] = "일련번호 %s 의 XML 없음" % serial
        return r
    xb = rd(p)
    inf = P.info(xb)
    meta = _meta(p)
    # 판 정보·URL·수집 시각
    dm = re.search(r"발령\s*([\d.]+)\s*·\s*시행\s*([\d.]+)\s*·\s*발령번호\s*([\w-]+)", seg)
    if dm:
        for k, v in (("발령일자", dm.group(1)), ("시행일자", dm.group(2))):
            if _fmt(inf.get(k, "")) != v:
                r["출처문제"].append("%s %s ↔ XML %s" % (k, v, _fmt(inf.get(k, ""))))
        if inf.get("발령번호", "") != dm.group(3):
            r["출처문제"].append("발령번호 %s ↔ XML %s" % (dm.group(3), inf.get("발령번호")))
    if not seg.strip().startswith(inf.get("행정규칙명", "?")):
        r["출처문제"].append("문서명 ↔ XML 행정규칙명 %s" % inf.get("행정규칙명"))
    um = re.search(r"https?://\S+lawService\.do\S*", seg)
    if um and ("ID=%s" % serial) not in um.group(0):
        r["출처문제"].append("URL 의 ID 가 일련번호와 다름")
    if cm and meta.get("fetched_at"):
        want = cm.group(1)
        if ("T" in want and want != meta["fetched_at"]) or want[:10] != meta["fetched_at"][:10]:
            r["출처문제"].append("수집 %s ↔ meta fetched_at %s" % (want, meta["fetched_at"]))
    r["원문"] = p
    whole_line = cline
    # 위치
    am = re.search(r"\[별표\s*(\d+)(?:-(\d+))?\]\s*별표내용(?:\s*(\d+)(?:~(\d+))?줄)?", seg)
    if am:
        no = "%04d" % int(am.group(1))
        gj = "%02d" % int(am.group(2) or 0)
        lab = am.group(1) + ("-" + am.group(2) if am.group(2) else "")
        AL = annex_lines(xb, no, gj)
        if AL is None:
            r["설명"] = "[별표 %s] 없음" % lab
            return r
        if "위 표의 줄만" in whole_line:
            nums = table_lines_before(lines, b["시작줄"])
            ql = b["글"].split("\n")
            if len(nums) != len(ql):
                r["결과"], r["설명"] = "불일치", "표 줄 %d개 ↔ 인용 줄 %d개" % (len(nums), len(ql))
                return r
            bad = [(n, q) for n, q in zip(nums, ql) if nows(AL[n - 1]) != nows(q)]
            exact = all(AL[n - 1].rstrip("\r") == q for n, q in zip(nums, ql))
            if bad:
                r["결과"], r["설명"] = "불일치", "표의 줄 %d 글이 다름: %s" % (bad[0][0], bad[0][1][:60])
            else:
                r["결과"], r["설명"] = "일치", "표의 줄 %d개가 별표내용의 그 줄과 공백 무시 같음%s" % (
                    len(nums), "(글자 그대로)" if exact else "")
            r["원문"] += " [별표 %s] 별표내용 표의 줄" % lab
            return r
        if am.group(3):
            a = int(am.group(3))
            z = int(am.group(4) or am.group(3))
            src = "\n".join(AL[a - 1:z])
            r["원문"] += " [별표 %s] 별표내용 %d~%d줄" % (lab, a, z)
        else:
            src = "\n".join(AL)
            r["원문"] += " [별표 %s] 별표내용" % lab
        r["결과"], r["설명"] = _cmp_text(b["글"], src, "포함")
        return r
    if "<제개정이유>" in seg:
        e = ET.fromstring(xb).find(".//제개정이유")
        r["원문"] += " <제개정이유>"
        if e is None:
            r["설명"] = "제개정이유 요소 없음"
            return r
        r["결과"], r["설명"] = _cmp_text(b["글"], "".join(e.itertext()), "포함" if "발췌" in whole_line else "같음")
        return r
    if "<개정문>" in seg:
        g = gaejeongmun(xb)
        r["원문"] += " <개정문>"
        if g is None:
            r["설명"] = "개정문 요소 없음"
            return r
        r["결과"], r["설명"] = _cmp_text(b["글"], g, "포함")
        return r
    if "<부칙>" in seg:
        dd = re.search(r"부칙공포일자\s*(\d{8})", seg)
        nn = re.search(r"부칙공포번호\s*([\w-]+)", seg)
        hit = [t for d, n, t in addenda(xb) if (not dd or d == dd.group(1)) and (not nn or n == nn.group(1))]
        r["원문"] += " <부칙> %s %s" % (dd.group(1) if dd else "", nn.group(1) if nn else "")
        if len(hit) != 1:
            r["설명"] = "맞는 부칙 %d건" % len(hit)
            return r
        mode = "포함" if "발췌" in whole_line else "같음"
        r["결과"], r["설명"] = _cmp_text(b["글"], hit[0], mode)
        return r
    jm = re.search(r"(제\d+-\d+조(?:의\d+)?)(\(조문내용\)|\s*제(\d+)항)", seg)
    if jm:
        art = article_full(xb, jm.group(1))
        r["원문"] += " " + jm.group(1)
        if art is None:
            r["설명"] = "%s 없음" % jm.group(1)
            return r
        mode = "같음" if jm.group(2) == "(조문내용)" else "포함"
        r["결과"], r["설명"] = _cmp_text(b["글"], art, mode)
        return r
    r["설명"] = "위치 표기를 읽지 못함"
    return r


def check_quotes(md):
    lines = open(md, encoding="utf-8").read().split("\n")
    srec = [i for i, ln in enumerate(lines) if ln.startswith(SREC_ANY)]
    lim = srec[0] if srec else len(lines)
    res = []
    for b in md_blocks(lines):
        if b["시작줄"] > lim:
            continue
        cl, cline, seg = find_cite(lines, b["시작줄"])
        rec = dict(b, 파일=md, 출처줄=cl)
        if not seg:
            rec.update(결과="출처 없음", 설명="블록 바로 앞 줄에 「[… 수집 …]」 출처 표기가 없음", 출처문제=[], 원문="")
        else:
            rec.update(resolve(lines, b, cl, cline, seg))
        res.append(rec)
    return res


# ── 표·수치 주장 대조 ───────────────────────────────────────────────────────
ORIG_DIRS = [os.path.join("dart_out", "raw", "web9", "law"), os.path.join(RAW, "law92"), os.path.join(RAW, "law92a")]


def orig_xml(serial):
    for d in ORIG_DIRS:
        for f in os.listdir(d):
            if f.endswith("_%s.xml" % serial):
                return os.path.join(d, f)
    return None


def table_after(lines, header_prefix):
    """머리줄이 header_prefix 로 시작하는 첫 표 → [[칸…]] (구분선 빼고)."""
    for i, ln in enumerate(lines):
        if ln.startswith(header_prefix):
            out = []
            for ln2 in lines[i + 2:]:
                if not ln2.startswith("|"):
                    break
                out.append([c.strip() for c in ln2.strip().strip("|").split("|")])
            return out
    return None


def csv_rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def check_ver_csv(probs, info):
    """판목록 csv(수집 때 열) ↔ 원본 XML·meta·연혁 목록. 검증 열(검증_*)이 있으면 _scan.json 과도 대조."""
    rows = csv_rows(CSV_VER)
    S = load(SCAN)
    n_y = 0
    hist = {REG: P.load_hist(REG), SEC: P.load_hist(SEC)}
    for r in rows:
        h = hist[r["규정"]][int(r["연혁순번"])]
        for col, k in (("행정규칙일련번호", "행정규칙일련번호"), ("발령일자", "발령일자"), ("시행일자", "시행일자"),
                       ("발령번호", "발령번호")):
            if r[col] != h.get(k, ""):
                probs.append("판목록 csv %s %s 순번 %s: %s 가 연혁 목록과 다름" % (r["규정"], r["대상"], r["연혁순번"], col))
        op = orig_xml(r["행정규칙일련번호"])
        if r["판_받음"] == "N":
            if op:
                probs.append("판목록 csv %s 순번 %s: 판_받음 N 인데 수집 폴더에 XML 있음" % (r["대상"], r["연혁순번"]))
        else:
            n_y += 1
            if not op or os.path.normpath(op) != os.path.normpath(r["XML경로"]):
                probs.append("판목록 csv %s 순번 %s: XML경로가 없음/다름" % (r["대상"], r["연혁순번"]))
                continue
            xb = rd(op)
            mt = _meta(op)
            if r["XML_sha256"] != _sha(xb):
                probs.append("판목록 csv %s 순번 %s: XML_sha256 다름" % (r["대상"], r["연혁순번"]))
            if r["수집시각"] != mt.get("fetched_at", ""):
                probs.append("판목록 csv %s 순번 %s: 수집시각 ↔ meta" % (r["대상"], r["연혁순번"]))
            if "OC=" in r["출처URL"] and "OC=***" not in r["출처URL"]:
                probs.append("판목록 csv %s 순번 %s: 출처URL OC 안 가림" % (r["대상"], r["연혁순번"]))
            inf = P.info(xb)
            for col, k in (("XML_발령일자", "발령일자"), ("XML_시행일자", "시행일자"), ("XML_발령번호", "발령번호"),
                           ("조문형식여부", "조문형식여부")):
                if r[col] != inf.get(k, ""):
                    probs.append("판목록 csv %s 순번 %s: %s ↔ XML" % (r["대상"], r["연혁순번"], col))
            if r["대상"].startswith("[별표"):
                a = annex(xb, "0037")
                txt = a["별표내용"] if a else ""
            else:
                txt = W.find_jo(xb, r["대상"])[0]
            if r["글_sha256"] != _sha(txt) or str(len(txt)) != r["글자수"] or r["있음"] != ("Y" if txt else "N") \
                    or r["ORSA문구"] != ("Y" if ORSA_RE.search(txt or "") else "N"):
                probs.append("판목록 csv %s 순번 %s: 글(sha·글자수·있음·ORSA) ↔ XML 재계산 다름" % (r["대상"], r["연혁순번"]))
            if r["글파일"] and os.path.exists(r["글파일"]):
                if _sha(open(r["글파일"], encoding="utf-8").read()) != r["글_sha256"]:
                    probs.append("판목록 csv %s 순번 %s: 글파일 sha 다름" % (r["대상"], r["연혁순번"]))
            elif r["글파일"]:
                probs.append("판목록 csv %s 순번 %s: 글파일 없음" % (r["대상"], r["연혁순번"]))
        # 검증 열
        if "검증_판_받음" in r and S:
            key = {"제7-5조": "감독규정|제7-5조", "제5-6조의2": "세칙|제5-6조의2", "[별표 37]": "세칙|[별표 37]"}[r["대상"]]
            sr = S[key]["판"][int(r["연혁순번"])]
            if r["검증_판_받음"] != sr["받음"] or (sr["받음"] == "Y" and (
                    r["검증_글_sha256"] != sr["글_sha256"] or r["검증_앞판대비"] != sr["앞판대비"]
                    or r["검증_인접"] != sr["인접"] or r["검증_ORSA문구"] != sr["ORSA"])):
                probs.append("판목록 csv %s 순번 %s: 검증 열 ↔ _scan.json 다름" % (r["대상"], r["연혁순번"]))
    info.append("판목록 csv %d행(받은 판 %d행): 연혁 목록·XML 경로·sha256·meta 수집시각·판 정보·조 글 sha 재계산·글파일 대조%s" % (
        len(rows), n_y, " + 검증 열 ↔ 전수 대조" if rows and "검증_판_받음" in rows[0] else ""))
    return rows


def check_md1_claims(probs, info, vrows):
    lines = open(MD1, encoding="utf-8").read().split("\n")
    text = "\n".join(lines)
    by = {(r["대상"], r["연혁순번"]): r for r in vrows}
    n = 0
    # 2-9 표
    t = table_after(lines, "| 연혁순번 | 일련번호 | 발령 | 시행 | 제개정 | 글자수 | 문구 |")
    for c in t or []:
        r = by.get(("제7-5조", c[0]))
        n += 1
        want = [r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["제개정구분"], r["글자수"],
                r["ORSA문구"], r["앞판대비"], r["앞받은판과_인접"], r["글_sha256"][:12]] if r else None
        if c != want:
            probs.append("md1 2-9 표 순번 %s: csv 와 다름 %s ↔ %s" % (c[0], c, want))
    # 3-8 표
    t = table_after(lines, "| 연혁순번 | 일련번호 | 발령 | 시행 | 제5-6조의2 글자수 |")
    for c in t or []:
        r = by.get(("제5-6조의2", c[0]))
        a = by.get(("[별표 37]", c[0]))
        n += 1
        want = [r["연혁순번"], r["행정규칙일련번호"], _fmt(r["발령일자"]), _fmt(r["시행일자"]), r["글자수"], r["앞판대비"],
                r["앞받은판과_인접"], ("있음(%s자)" % a["글자수"]) if a["있음"] == "Y" else "없음", a["앞판대비"]]
        if c != want:
            probs.append("md1 3-8 표 순번 %s: csv 와 다름 %s ↔ %s" % (c[0], c, want))
    # 2-1·3-1·3-6 표
    for hp, tgt in (("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | 발령번호 | 제개정 | 제7-5조 | 문구 |", "제7-5조"),
                    ("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | 제개정 | 제5-6조의2 |", "제5-6조의2"),
                    ("| 구분 | 연혁순번 | 일련번호 | 발령일 | 시행일 | [별표 37] 제목", "[별표 37]")):
        for c in table_after(lines, hp) or []:
            r = by.get((tgt, c[1]))
            n += 1
            if not r or r["행정규칙일련번호"] != c[2] or _fmt(r["발령일자"]) != c[3] or _fmt(r["시행일자"]) != c[4]:
                probs.append("md1 %s 표 「%s」 행: 일련번호·발령·시행 ↔ csv 다름" % (tgt, c[0]))
                continue
            if tgt == "제7-5조":
                if c[5] != "제%s호" % r["발령번호"] or c[6] != r["제개정구분"] or c[7] != "있음(%s자)" % r["글자수"] \
                        or c[8] != r["ORSA문구"]:
                    probs.append("md1 2-1 표 「%s」 행: 발령번호·제개정·글자수·문구 ↔ csv 다름" % c[0])
            elif tgt == "제5-6조의2":
                if c[5] != r["제개정구분"] or c[6] != (("있음(%s자)" % r["글자수"]) if r["있음"] == "Y" else "없음"):
                    probs.append("md1 3-1 표 「%s」 행: 제개정·조 ↔ csv 다름" % c[0])
            else:
                xb = rd(r["XML경로"])
                a = annex(xb, "0037")
                if a:
                    if c[5] != a["별표제목"] or c[6] != str(len(a["별표내용"])) or c[7] != _sha(a["별표내용"])[:12]:
                        probs.append("md1 3-6 표 「%s」 행: 별표 제목·글자수·sha ↔ XML 다름" % c[0])
                elif c[6] != "0":
                    probs.append("md1 3-6 표 「%s」 행: 별표 없음인데 글자수 %s" % (c[0], c[6]))
    info.append("md1 표(2-1·2-9·3-1·3-6·3-8) %d행 ↔ 판목록 csv·XML" % n)
    # 수치 주장
    cur = rd(REG_XML9)
    ad = addenda(cur)
    hits = [n_ for d, n_, t_ in ad if re.search(r"7-5조|자체\s*위험|지급여력\s*평가|ORSA", t_)]
    if "부칙 107건" not in text or len(ad) != 107 or hits != ["2016-15", "2016-30"]:
        probs.append("md1 2-5 note: 현행 감독규정 부칙 %d건·맞는 부칙 %s" % (len(ad), hits))
    sc = rd(SEC_XML9)
    ad2 = addenda(sc)
    hits2 = [d for d, n_, t_ in ad2 if re.search(r"5-6조의2|별표\s*37|자체\s*위험|지급여력\s*평가|ORSA|내부모형", t_)]
    if "부칙 185건" not in text or len(ad2) != 185 or hits2 != ["20160428", "20260629"]:
        probs.append("md1 3-9: 현행 세칙 부칙 %d건·맞는 부칙 %s" % (len(ad2), hits2))
    a53 = [t_ for d, n_, t_ in addenda(rd(xml_path("2100000217538"))) if n_ == "2022-53"]
    if not a53 or len(a53[0]) != 2601 or any(k in a53[0][a53[0].find("제2조"):] for k in ("7-5", "자체 위험", "위험관리체제")):
        probs.append("md1 2-7 note: 2022-53 부칙 2601자·제2조 이하 0곳 주장 다름")
    if "sha256 %s" % _sha(W.find_jo(cur, "제7-5조")[0])[:12] not in text:
        probs.append("md1 2-8 note: 현행 제7-5조 sha256 앞 12자 다름")
    t44 = W.find_jo(rd(xml_path("2100000044084")), "제7-5조")[0]
    if t44.count("&#8228;") != 1:
        probs.append("md1 2-3 note: 2016.4.1 판 「&#8228;」 %d곳" % t44.count("&#8228;"))
    if "제61조(위험관리)" not in rd(xml_path("2000000082206")).decode("utf-8"):
        probs.append("md1 2-1 note: 2000.12.29 판에 「제61조(위험관리)」 없음")
    cj = load(os.path.join(RAW, "law92a", "현행재확인.json"))
    for name, ser in ((REG, "2100000279112"), (SEC, "2200000108939")):
        k = cj.get(name, {})
        if not k.get("같은판") or [x["행정규칙일련번호"] for x in k.get("같은이름행", [])] != [ser] or k.get("조회시각", "") not in text:
            probs.append("md1 1절: %s 현행 재확인 기록과 다름" % name)
    info.append("md1 수치 주장(부칙 107·185건과 맞는 부칙, 2022-53 부칙 2601자, 현행 제7-5조 sha, &#8228; 1곳, 제61조, 현행 재확인 2건) 대조")


def a37_sources():
    L = open(A37_MD10, encoding="utf-8").read().split("\n")
    st = next(i for i, l in enumerate(L) if l.strip() == "## 원문")
    hw = L[st + 1:]
    pg = pdf_pages()
    X = annex(rd(SEC_XML9), "0037")["별표내용"]
    xs = []
    for l in X.split("\n"):
        if l.startswith("│") and l.rstrip().endswith("│"):
            l = l[1:l.rstrip().rfind("│")]
        elif re.fullmatch(r"\s*[┌└][─]*[┐┘]\s*", l):
            l = ""
        xs.append(l)
    return hw, pg, xs, X


def check_md2_claims(probs, info):
    import difflib
    lines = open(MD2, encoding="utf-8").read().split("\n")
    text = "\n".join(lines)
    hw, pg, xs, X = a37_sources()
    H = nows("\n".join(hw))
    Pt = nows("\n".join(pg[i] for i in sorted(pg)))
    pl = [l for i in sorted(pg) for l in pg[i].split("\n") if l.strip()]
    if not (len(hw) == 180 and len(H) == 9336 and len(Pt) == 9336 and H == Pt and len(pl) == 336):
        probs.append("md2 1절: hwp %d줄·%d자, PDF %d자·%d줄, 같음 %s" % (len(hw), len(H), len(Pt), len(pl), H == Pt))
    Xn = nows("\n".join(xs))
    ops = [o for o in difflib.SequenceMatcher(None, H, Xn, autojunk=False).get_opcodes() if o[0] != "equal"]
    if [(H[o[1]:o[2]], Xn[o[3]:o[4]]) for o in ops] != [("‧", "?"), ("․", "?"), ("‧", "?")] or X.count("?") != 3:
        probs.append("md2 1-2: hwp↔XML 다른 곳 %d곳·XML ? %d개" % (len(ops), X.count("?")))
    lc = csv_rows(CSV_LINES)
    if len(lc) != 6 or [(r["A글"], r["B글"], r["B위치"]) for r in lc][:3] != [("‧", "?", "771"), ("․", "?", "879"), ("‧", "?", "945")]:
        probs.append("md2 줄대조 csv 가 재계산(3곳 × md·PDF)과 다름")
    for r in lc:
        if r["대조"] == "md↔XML":
            src = open(A37_MD10, encoding="utf-8").read().split("\n")[int(r["A위치"]) - 1]
        else:
            src = open(A37_PDF10, encoding="utf-8").read().split("\n")[int(r["A위치"].strip("()").split(",")[0]) - 1]
        if r["A글"] not in src or "?" not in X.split("\n")[int(r["B위치"]) - 1]:
            probs.append("md2 줄대조 csv 행 %s %s: 위치의 글이 다름" % (r["대조"], r["A위치"]))
    IT = re.compile(r"^\s*(\d+)\s*\.\s*\(([^)]*)\)")
    nums = {}
    for nm, ls in (("hwp", hw), ("pdf", pl), ("xml", xs)):
        nums[nm] = [int(m.group(1)) for l in ls for m in [IT.match(l)] if m]
        if nums[nm] != list(range(1, 22)):
            probs.append("md2 1절: %s 번호 항목이 1~21 연속이 아님" % nm)
    # 항목대조 csv ↔ 세 원본, 1-1 표 ↔ csv
    rows = csv_rows(CSV_ITEMS)
    L = open(A37_MD10, encoding="utf-8").read().split("\n")
    PL = open(A37_PDF10, encoding="utf-8").read().split("\n")
    XL = X.split("\n")
    IT2 = re.compile(r"^\s*│?\s*(\d+)\s*\.\s*\(([^)]*)\)")
    page_of, cur = {}, 0
    for i, l in enumerate(PL):
        m = re.match(r"^=== p\.(\d+) ===$", l.strip())
        if m:
            cur = int(m.group(1))
        page_of[i + 1] = cur
    for r in rows:
        for nm, ls, col in (("md", L, "md줄"), ("pdf", PL, "PDF_txt줄"), ("xml", XL, "XML별표내용줄")):
            m = IT2.match(ls[int(r[col]) - 1])
            if not m or m.group(1) != r["번호"] or nows(m.group(2)) != nows(r["제목"]):
                probs.append("항목대조 csv %s.: %s 줄 %s 의 글이 다름" % (r["번호"], nm, r[col]))
        if str(page_of[int(r["PDF_txt줄"])]) != r["PDF쪽"]:
            probs.append("항목대조 csv %s.: PDF 쪽 다름" % r["번호"])
    tb = [l for l in lines if re.match(r"^\| \d+\. \|", l)]
    titles = mobeom_titles()
    for l, r in zip(tb, rows):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        want = [r["번호"] + ".", r["제목"], r["장"], r["절"] or "—", r["md줄"], "p.%s (%s)" % (r["PDF쪽"], r["PDF_txt줄"]),
                r["XML별표내용줄"], "Y" if r["제목_md_PDF_같음"] == "Y" and r["제목_md_XML_같음"] == "Y" else "N"]
        if c[:8] != want:
            probs.append("md2 1-1 표 %s: 항목대조 csv 와 다름" % c[0])
    if len(tb) != len(rows) or len(rows) != 21:
        probs.append("md2 1-1 표 %d행 · csv %d행" % (len(tb), len(rows)))
    info.append("md2 [별표 37]: hwp 180줄 9336자 = PDF 9336자(336줄), hwp↔XML 다른 곳 3곳(?) · 번호 1~21(세 원본) · 항목대조 csv 21행·줄대조 csv 6행·1-1 표 대조")
    # PDF 다시 읽기(pypdf)·그림
    try:
        import pypdf
        rdr = pypdf.PdfReader(A37_PDF)
        same = [nows(p.extract_text()) == nows(pg[i + 1]) for i, p in enumerate(rdr.pages)]
        if not all(same) or len(same) != 10:
            probs.append("md2 1절: pypdf 재추출이 10차 텍스트와 다른 쪽 %s" % [i + 1 for i, x in enumerate(same) if not x])
        info.append("md2 [별표 37] PDF: pypdf %s 재추출 10쪽 전부 10차 텍스트와 공백 무시 같음" % pypdf.__version__)
    except ImportError:
        info.append("pypdf 없음 — PDF 재추출 대조 건너뜀")
    # [별표 22]
    sx = rd(SEC_XML9)
    units = []
    for u in ET.fromstring(sx).iter("별표단위"):
        if (u.findtext("별표번호") or "").strip() == "0022":
            c = u.findtext("별표내용") or ""
            units.append(((u.findtext("별표가지번호") or "").strip(), (u.findtext("별표구분") or "").strip(),
                          (u.findtext("별표제목") or "").strip(), len(c), len(c.split("\n")),
                          (u.findtext("별표서식파일링크") or "").strip(), (u.findtext("별표서식PDF파일링크") or "").strip()))
    t21 = table_after(lines, "| 별표키 | 별표번호 | 가지번호 | 구분 | 별표제목(원문) |") or []
    for c, u in zip(t21, units):
        fs = re.findall(r"flSeq=(\d+)", c[6])
        if c[2] != u[0] or c[3] != u[1] or c[4] != u[2] or c[5] != "%d자 · %d줄" % (u[3], u[4]) or \
                fs != [re.search(r"flSeq=(\d+)", u[5]).group(1), re.search(r"flSeq=(\d+)", u[6]).group(1)]:
            probs.append("md2 2-1 표 %s/%s: XML 별표단위와 다름" % (c[2], c[3]))
    if len(t21) != len(units):
        probs.append("md2 2-1 표 %d행 ↔ XML 별표번호 0022 단위 %d" % (len(t21), len(units)))
    A = annex(sx, "0022")["별표내용"]
    AL = A.split("\n")
    if open(A22_TXT, encoding="utf-8", newline="").read() != A or \
            open(A37_XMLTXT, encoding="utf-8", newline="").read() != X:
        probs.append("law92b 별표내용 덤프 파일이 XML 별표내용과 다름")
    if A.count("?") != 241 or "생명?장기손해" not in AL[3976]:
        probs.append("md2 2-1 note: [별표 22] ? %d개·3977줄" % A.count("?"))
    # 2-2~2-6 표 ↔ 제목줄 csv
    c22 = csv_rows(CSV_22)
    md_rows = []
    s5i = [i for i, ln in enumerate(lines) if ln.startswith("## 5. 검증 보충")]
    for i, ln in enumerate(lines[:s5i[0] if s5i else len(lines)]):
        m = re.match(r"^\| (\d+) \| ([^|]*) \|$", ln)
        if m and i > 0 and lines[i - 1].startswith("|"):
            md_rows.append((m.group(1), "" if m.group(2).strip() == "(머리)" else m.group(2).strip()))
    if [(r["줄"], r["위치"]) for r in c22] != md_rows:
        probs.append("md2 2-2~2-6 표(줄·위치 %d행) ↔ 제목줄 csv(%d행) 다름" % (len(md_rows), len(c22)))
    for r in c22:
        if AL[int(r["줄"]) - 1] != r["글"]:
            probs.append("제목줄 csv 줄 %s: 글이 별표내용과 다름" % r["줄"])
        if r["물음표"] != ("Y" if "?" in r["글"] else ""):
            probs.append("제목줄 csv 줄 %s: 물음표 칸 다름" % r["줄"])
    # 2-8 표 수(「…위험」 뒤 「액」 없음)
    cnt = {}
    for nm, pat in (("생명·장기손해", r"생명[·ㆍ?]장기손해보험위험(?!액)"), ("일반손해", r"일반손해보험위험(?!액)"),
                    ("시장", r"시장위험(?!액)"), ("신용", r"신용위험(?!액)"), ("운영위험", r"운영위험(?!액)")):
        cnt[nm] = [i + 1 for i, l in enumerate(AL) for m in re.finditer(pat, l)]
    t28 = table_after(lines, "| 지시서(9-2 의 5번) |") or []
    for c in t28:
        k = c[0]
        m = re.match(r"(\d+)곳", c[3])
        if k not in cnt or not m or int(m.group(1)) != len(cnt[k]):
            probs.append("md2 2-8 표 %s: 「…위험」(액 없음) %s ↔ 재계산 %s곳" % (k, c[3][:10], len(cnt.get(k, []))))
        for ex in re.findall(r"(\d+)줄", c[3]):
            if int(ex) not in cnt.get(k, []):
                probs.append("md2 2-8 표 %s: 예시 %s줄이 재계산 목록에 없음" % (k, ex))
    for ln_no, frag in ((4065, "시장, 신용위험 등"), (4611, "k : 주식위험, 부동산위험, 신용위험"), (4955, "(운영위험)"),
                        (85, "신용위험스프레드’"), (10499, "운영위험이 존재하")):
        if nows(frag) not in nows(AL[ln_no - 1]):
            probs.append("md2 2-8 note: %d줄에 「%s」 없음" % (ln_no, frag))
    if "ㆍ" not in AL[212] or "·" not in AL[5130]:
        probs.append("md2 2-8 note: 가운뎃점 주장 다름")
    B1 = annex(sx, "0022", "01")["별표내용"].split("\n")[0]
    if "## 5. 검증 보충" in text and ("「[별표 22-1] <신설 2026.06.29.>」" not in text or not B1.startswith("[별표 22-1] <신설 2026.06.29.>")):
        probs.append("md2 5-3 note: [별표 22-1] 첫 줄 주장 ↔ XML %r" % B1[:40])
    info.append("md2 [별표 22]: 별표단위 %d개 표·? 241개·덤프=XML·2-2~2-6 표 %d행=제목줄 csv·2-8 표 수 재계산" % (
        len(units), len(md_rows)))
    # 모범규준 원문 md 줄 번호(3절 note)
    ML = open(MOBEOM_MD, encoding="utf-8").read().split("\n")
    s5 = next(i for i, l in enumerate(ML) if l.startswith("## 5. "))
    want = []
    for jo in ("제18조(측정 및 관리 대상)", "제42조(위험 인식)"):
        k = next(i for i in range(s5, len(ML)) if ML[i].startswith(jo))
        if "보험" not in ML[k]:
            probs.append("모범규준 원문 %s 줄에 「보험」 없음" % jo)
        want.append(k + 1)
    m = re.search(r"9-4_모범규준_원문\.md (\d+)·(\d+)줄", text)
    if not m or [int(m.group(1)), int(m.group(2))] != want:
        probs.append("md2 3절 note: 모범규준 원문 md 줄 %s ↔ 지금 파일 제18조·제42조 줄 %s" % (m.groups() if m else None, want))
    return text


def mobeom_titles():
    return {r["조"]: r["제목_2016.8.1판"] for r in csv_rows(MOBEOM_CSV)}


MOBEOM_TAG = re.compile(r"제(\d+)조\(([^)]*)\)")


def check_mobeom(probs, info, md, bundle_pats, table_heads):
    """자료 묶음마다 「- 모범규준 조」 줄, 조 번호·제목이 조목록과 맞는지, 「(판단)」 표시."""
    lines = open(md, encoding="utf-8").read().split("\n")
    titles = mobeom_titles()
    heads = [i for i, ln in enumerate(lines) if ln.startswith("#")]
    srec = [i for i, ln in enumerate(lines) if ln.startswith(SREC_ANY)]
    lim = srec[0] if srec else len(lines)
    nb = 0
    for pat in bundle_pats:
        hs = [i for i in heads if re.match(pat, lines[i])]
        if not hs:
            probs.append("%s 자료 묶음 %s: 머리 없음" % (os.path.basename(md), pat))
            continue
        for h in hs:
            nb += 1
            nxt = [i for i in heads if i > h]
            seg = lines[h:(nxt[0] if nxt else len(lines))]
            tag = [ln for ln in seg if ln.startswith("- 모범규준 조")]
            if not tag:
                probs.append("%s 자료 묶음 「%s」: 「- 모범규준 조」 줄 없음" % (os.path.basename(md), lines[h][:40]))
            for ln in tag:
                if "(판단" not in ln and NOART not in ln:  # NOART: 연혁·출처 묶음(13차 정합성 보정 R2)
                    probs.append("%s 「%s」: 모범규준 조 줄에 (판단) 표시 없음" % (os.path.basename(md), lines[h][:30]))
    nt = 0
    for i, ln in enumerate(lines[:lim]):
        tagged = ln.startswith("- 모범규준 조") or "모범규준" in ln or (ln.startswith("|") and "(판단" in ln)
        if not tagged:
            continue
        for m in MOBEOM_TAG.finditer(ln):
            no, ti = m.group(1), m.group(2)
            if ln.startswith("|") and not re.search(r"\(판단", ln):
                continue
            if no in titles and nows(ti) == nows(titles[no]):
                nt += 1
            elif ln.startswith("- 모범규준 조") or (ln.startswith("|") and "(판단" in ln) or "모범규준 제" in ln:
                if re.match(r"제\d+-\d+조|제\d+조의\d+", ln[m.start():]):
                    continue
                if not re.search(r"감독규정|세칙|시행령|별표", ln[max(0, m.start() - 12):m.start()]):
                    probs.append("%s %d줄: 제%s조(%s) ↔ 조목록 「%s」" % (os.path.basename(md), i + 1, no, ti, titles.get(no, "없음")))
    info.append("%s: 자료 묶음 %d개 「모범규준 조」 줄 · 조 번호(제목) %d곳 ↔ 조목록" % (os.path.basename(md), nb, nt))


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


def check_notfound(probs, info, md):
    lines = open(md, encoding="utf-8").read().split("\n")
    srec = [i for i, ln in enumerate(lines) if ln.startswith(SREC_ANY)]
    lines = lines[:srec[0]] if srec else lines
    inblock = False
    n = 0
    for i, ln in enumerate(lines):
        if FENCE.match(ln):
            inblock = not inblock
            continue
        if inblock or "추출 범위에 없음" not in ln:
            continue
        n += 1
        win = " ".join(lines[max(0, i - 3):i + 4])
        if not re.search(r"검색|찾|정규식|lawSearch|대조|받지 않|건너뜀|범위|칸 없음|확인", win):
            probs.append("%s %d줄: 「추출 범위에 없음」 곁에 찾은 방법이 없음" % (os.path.basename(md), i + 1))
    info.append("%s: 「추출 범위에 없음」 %d곳 — 찾은 방법 곁에 있음 확인" % (os.path.basename(md), n))


def check_coverage(probs, info):
    S = load(SCAN)
    if not S:
        probs.append("_scan.json 없음 — scan 을 먼저")
        return S
    for key in ("감독규정|제7-5조", "세칙|제5-6조의2", "세칙|[별표 37]"):
        v = S[key]
        if not v["단조"]:
            f = v["판정기준"]
            got = [x for x in v["판"] if x["받음"] == "Y"]
            k1 = next(i for i, x in enumerate(got) if x[f] == "Y")
            odd = [x["일련번호"] for x in got[k1:] if x[f] == "N"]
            t1 = open(MD1, encoding="utf-8").read()
            miss = [x for x in odd if x not in t1]
            if miss:
                probs.append("%s: 처음 Y 뒤에 N 인 판 %s 를 md1 이 적지 않음(단조 가정이 깨진 곳)" % (key, miss))
            else:
                info.append("%s: 단조 아님 — 처음 Y 뒤 N 인 판 %s 는 md1 6절에 적음" % (key, odd))
        if not v["처음Y_경계인접"]:
            probs.append("%s: 처음 Y 판과 그 앞 받은 판이 인접하지 않음" % key)
        if v["열린경계"]:
            probs.append("%s: 열린 경계 %s" % (key, v["열린경계"]))
        info.append("%s: 목록 %d판 중 받은 판 %d · 처음 %s=Y 판 %s(%s, 앞 판 %s %s) · 받지 않은 순번 %s" % (
            key, v["목록판수"], v["받은판수"], v["판정기준"], v["처음Y"]["일련번호"], v["처음Y"]["발령일자"],
            v["처음Y_앞판"]["일련번호"], v["처음Y_앞판"]["발령일자"], v["받지않은순번"] or "없음"))
    first = {k: S[k]["처음Y"]["일련번호"] for k in ("감독규정|제7-5조", "세칙|제5-6조의2", "세칙|[별표 37]")}
    if first != {"감독규정|제7-5조": "2100000044084", "세칙|제5-6조의2": "2200000048212", "세칙|[별표 37]": "2200000108841"}:
        probs.append("처음 든 판이 md 0절과 다름: %s" % first)
    old = S.get("옛이름판", [])
    if any(x["받음"] != "Y" for x in old):
        probs.append("옛 이름 판 가운데 받지 못한 판 %d" % sum(1 for x in old if x["받음"] != "Y"))
    if any(x.get("ORSA_XML어디든") == "Y" or x.get("제7_5조") == "Y" or x.get("제5_6조의2") == "Y" or x.get("별표37") == "Y"
           for x in old):
        probs.append("옛 이름 판에 ORSA 문구·제7-5조·제5-6조의2·[별표 37] 가 있음 — md 결론 다시 볼 것")
    info.append("옛 이름(같은 행정규칙ID) 판 %d: 받음 %d · ORSA 문구/제7-5조/제5-6조의2/[별표 37] 있는 판 %d" % (
        len(old), sum(1 for x in old if x["받음"] == "Y"),
        sum(1 for x in old if "Y" in (x.get("ORSA_XML어디든"), x.get("제7_5조"), x.get("제5_6조의2"), x.get("별표37")))))
    return S


def check(write=True):
    probs, info = [], []
    res = check_quotes(MD1) + check_quotes(MD2)
    for r in res:
        tag = "%s %d줄" % (os.path.basename(r["파일"]), r["시작줄"])
        if not r["결과"].startswith("일치"):
            probs.append("인용 %s: %s — %s (%s)" % (tag, r["결과"], r["설명"], r.get("원문", "")))
        for x in r.get("출처문제", []):
            probs.append("인용 %s: %s" % (tag, x))
    info.append("원문 인용 블록 %d개(md1 %d · md2 %d) 대조 — 일치 %d(전문 같음 %d · 포함 %d · 줄 단위 %d · 표의 줄 %d)" % (
        len(res), sum(1 for r in res if r["파일"] == MD1), sum(1 for r in res if r["파일"] == MD2),
        sum(1 for r in res if r["결과"].startswith("일치")), sum(1 for r in res if r["설명"].startswith("전문")),
        sum(1 for r in res if r["설명"] == "공백 무시 포함"), sum(1 for r in res if r["결과"] == "일치(줄 단위)"),
        sum(1 for r in res if r["설명"].startswith("표의 줄"))))
    vrows = check_ver_csv(probs, info)
    check_md1_claims(probs, info, vrows)
    check_md2_claims(probs, info)
    S = check_coverage(probs, info)
    check_mobeom(probs, info, MD1, [r"### 2-\d+ ", r"### 3-\d+ ", r"## 6\. "], [])
    check_mobeom(probs, info, MD2, [r"### 1-\d+ ", r"### 2-\d+ ", r"## 1\. ", r"## 5\. "], [])
    check_notfound(probs, info, MD1)
    check_notfound(probs, info, MD2)
    # 지시서 9-2 항목 → md 절
    t1 = open(MD1, encoding="utf-8").read()
    t2 = open(MD2, encoding="utf-8").read()
    req = [("9-2 1 감독규정 7-5조 문구가 처음 든 개정일·시행일", t1, r"### 2-1 「자체 위험 및 지급여력 평가」 문구가 처음 든 판"),
           ("9-2 2 세칙 5-6조의2 신설일", t1, r"### 3-1 제5-6조의2가 처음 나온 판"),
           ("9-2 2 [별표 37] 신설일·연혁", t1, r"### 3-6 \[별표 37\] 신설과 연혁"),
           ("9-2 2 개정 연혁(판별 대조)", t1, r"### 3-8 받은 판별"),
           ("9-2 2 부칙 유예·적용례(2016.4.28)", t1, r"### 3-3 신설 판\(2016\.4\.28\)의 부칙 전문"),
           ("9-2 2 2026.6.29 부칙 3조", t1, r"제3조\(‘자체 위험 및 지급여력평가’에 대한 적용례\)"),
           ("9-2 3 [별표 37] 1.~20. 대조·빠진 번호", t2, r"## 1\. \[별표 37\] 번호 항목 목록과 빠진 번호"),
           ("9-2 5 [별표 22] 위험 분류·하위 위험", t2, r"## 2\. \[별표 22\]\(K-ICS\) 위험 분류 체계와 하위 위험 목록"),
           ("9-2 4 보도자료(다른 산출물) 안내", t1, r"9-2-4_ORSA_보도자료\.md")]
    for name, t, pat in req:
        if not re.search(pat, t):
            probs.append("지시서 항목 「%s」: md 에 절/글이 없음" % name)
    if not os.path.exists(MD24):
        probs.append("9-2 4번 산출물 %s 없음" % MD24)
    info.append("지시서 9-2 항목 %d개 → md 절·글 확인(4번 보도자료는 9-2-4_ORSA_보도자료.md 몫 — 파일 있음 %s)" % (
        len(req), os.path.exists(MD24)))
    # 검증 보충·검증 기록 절
    # 「2026-10-08 KST」: 13차 정합성 보정(fix13_C.py, R5) 뒤 제목
    for md, t, need in ((MD1, t1, [r"^## 6\. 검증 보충\(2026-10-0(?:7|8 KST)\)", r"^## 검증 기록\(2026-10-0(?:7|8 KST)\)"]),
                        (MD2, t2, [r"^## 5\. 검증 보충\(2026-10-0(?:7|8 KST)\)", r"^## 검증 기록\(2026-10-0(?:7|8 KST)\)"])):
        for pat in need:
            if not re.search(pat, t, flags=re.M):
                probs.append("%s: 「%s」 절 없음" % (os.path.basename(md), pat.strip("^")))
    # 키·OC 값, PDF
    scan_files = [MD1, MD2, CSV_VER, CSV_ITEMS, CSV_LINES, CSV_22, REPORT, os.path.abspath(__file__)] + \
        [os.path.join(VDIR, f) for f in os.listdir(VDIR) if not f.endswith(".xml")]
    sec = _secrets()
    for k, v in sec:
        for p in scan_files:
            if os.path.isfile(p) and v.encode() in rd(p):
                probs.append("%s 값이 %s 에 들어 있음" % (k, p))
    xmls = [os.path.join(VDIR, f) for f in os.listdir(VDIR) if f.endswith(".xml")]
    for k, v in sec:
        for p in xmls:
            if v.encode() in rd(p):
                probs.append("%s 값이 받은 XML %s 에 들어 있음" % (k, p))
    info.append("키·OC 값 검사: %d종 × 파일 %d개 + 검증 폴더 XML %d개(값은 출력하지 않음)" % (len(sec), len(scan_files), len(xmls)))
    pdfs = [f for f in os.listdir(OUT) if f.lower().endswith(".pdf")]
    if pdfs:
        probs.append("산출 폴더에 PDF: %s" % pdfs)
    if write:
        out = ["# 13차 9-2(1·2·3·5번) 검증 결과 — scripts/dart/verify13_law92.py (실행 %s)" % now(), "",
               "대상: %s · %s · %s · %s · %s · %s" % (MD1, MD2, CSV_VER, CSV_ITEMS, CSV_LINES, CSV_22), ""]
        out += ["- " + x for x in info]
        out += ["", "## 문제 %d건" % len(probs)] + ["- " + x for x in probs]
        out += ["", "## 인용 블록별 결과(파일 · 시작줄 · 결과 · 설명 · 원문 · 출처줄)"]
        for r in res:
            out.append("- %s · %d · %s · %s · %s · 출처 %s줄" % (os.path.basename(r["파일"]), r["시작줄"], r["결과"],
                                                         r["설명"], r.get("원문", ""), r.get("출처줄")))
        fl = load(FIXLOG)
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
        print(x[:220])
    print("문제 %d건%s" % (len(probs), "" if not probs else " — 앞 20건:"))
    for x in probs[:20]:
        print("  " + x[:220])
    print("결과 →", REPORT)
    sys.exit(0 if not probs else 1)


# ── search(「추출 범위에 없음」 반박용, 요청 없음) ───────────────────────────────
PRESS_HWP = os.path.join(RAW, "fss", "press", "file", "fsc_72075_2.hwp.md")       # 9-2-4 가 받은 2016.3.30 보도자료 hwp 글
PRESS_PDF = os.path.join(RAW, "fss", "press", "file", "fsc_72075_1.pdf.txt")
SUB_TERMS = [r"하위\s*위험", r"세부\s*위험", r"구분한다", r"구분하여", r"으로\s*구분", r"로\s*나누", r"세분",
             r"신용위험액은", r"운영위험액은", r"\(이하\s*‘[^’]*위험액’\)", r"Sub", r"sub-risk"]
BOX = re.compile(r"^\s*[│┌└├┐┘┤─]")


def search():
    out = {"만든때": now()}
    # (md1) 개정 이유: 받은 판 XML 요소 이름 전수
    tags, nx, seen, why = set(), 0, set(), {}
    for d in XML_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".xml") and (f.startswith("보험업감독") or f.startswith("보험감독")):
                nx += 1
                root = ET.fromstring(rd(os.path.join(d, f)))
                for e in root.iter():
                    tags.add(e.tag)
                b = root.find("행정규칙기본정보")
                sn, nm, dt = (b.findtext("행정규칙일련번호") or "").strip(), (b.findtext("행정규칙명") or "").strip(), \
                    (b.findtext("발령일자") or "").strip()
                if sn in seen:
                    continue
                seen.add(sn)
                w = why.setdefault(nm, dict(있음=0, 없음=0, 처음=""))
                if root.find(".//제개정이유") is not None:
                    w["있음"] += 1
                    w["처음"] = min(w["처음"] or dt, dt)
                else:
                    w["없음"] += 1
    out["제개정이유_판"] = why
    out["개정이유_XML요소"] = dict(XML수=nx, 요소이름=sorted(tags),
                              검색어=["이유", "취지", "사유", "제개정이유", "개정이유", "제정이유"],
                              맞은요소=sorted(t for t in tags if re.search(r"이유|취지|사유", t)))
    L24 = open(MD24, encoding="utf-8").read().split("\n")
    out["개정이유_9-2-4"] = [dict(줄=i + 1, 글=l[:160]) for i, l in enumerate(L24)
                          if "자체 위험 및 지급여력 평가제도 도입" in l or "3.30일 확정" in l]
    # (md2) PDF 에만 있는 글
    import pypdf
    rdr = pypdf.PdfReader(A37_PDF)
    pg = pdf_pages()
    imgs = []
    for i, p in enumerate(rdr.pages):
        res = p.get("/Resources") or {}
        xo = res.get("/XObject") if res else None
        if xo:
            xo = xo.get_object()
            for k in xo:
                o = xo[k].get_object()
                row = dict(쪽=i + 1, 이름=str(k), 종류=str(o.get("/Subtype")), 가로=int(o.get("/Width", 0) or 0),
                           세로=int(o.get("/Height", 0) or 0))
                if row["종류"] == "/Image" and str(o.get("/ColorSpace")) == "/DeviceRGB" and int(o["/BitsPerComponent"]) == 8:
                    dd = o.get_data()
                    w, h = row["가로"], row["세로"]
                    dark = [(x, y) for y in range(h) for x in range(w) if sum(dd[(y * w + x) * 3:(y * w + x) * 3 + 3]) / 3 < 128]
                    row.update(어두운화소=len(dark), 범위=(min(x for x, _ in dark), max(x for x, _ in dark),
                                                   min(y for _, y in dark), max(y for _, y in dark)) if dark else None)
                imgs.append(row)
    out["별표37_PDF"] = dict(pypdf=pypdf.__version__, 쪽수=len(rdr.pages),
                           쪽마다같음=[nows(p.extract_text()) == nows(pg[i + 1]) for i, p in enumerate(rdr.pages)],
                           주석쪽=[i + 1 for i, p in enumerate(rdr.pages) if p.get("/Annots")],
                           AcroForm=bool(rdr.trailer["/Root"].get("/AcroForm")), XObject=imgs)
    # (md2) [별표 22] 신용·운영 하위위험 — 넓은 검색어
    sx = rd(SEC_XML9)
    AL = annex(sx, "0022")["별표내용"].split("\n")
    BL = annex(sx, "0022", "01")["별표내용"].split("\n")
    regions = {"정의(4)(5) 285~292줄": (285, 292), "Ⅳ 제5장 신용위험액 8997~10486줄": (8997, 10486),
               "Ⅳ 제6장 운영위험액 10487~10660줄": (10487, 10660)}
    sr = {}
    for nm, (a, z) in regions.items():
        rows = []
        for i in range(a, z + 1):
            l = AL[i - 1]
            hit = [t for t in SUB_TERMS if re.search(t, l)]
            if hit:
                rows.append(dict(줄=i, 상자=bool(BOX.match(l)), 검색어=hit, 글=l.strip()[:200]))
        sr[nm] = dict(맞은줄=len(rows), 상자밖=[r for r in rows if not r["상자"]],
                      하위위험_낱말=sum(1 for r in rows if any("하위" in t for t in r["검색어"])))
    sr["[별표 22] 전체 「하위\\s*위험」 줄"] = [i + 1 for i, l in enumerate(AL) if re.search(r"하위\s*위험", l)]
    sr["[별표 22-1] 「하위\\s*위험」 줄"] = [i + 1 for i, l in enumerate(BL) if re.search(r"하위\s*위험", l)]
    sr["검색어"] = SUB_TERMS
    out["별표22_하위위험"] = sr
    dump(SEARCH, out)
    print("개정 이유: XML %d개 요소 이름 %d종 중 「이유·취지·사유」 %s · 9-2-4 md 맞는 줄 %d" % (
        nx, len(tags), out["개정이유_XML요소"]["맞은요소"], len(out["개정이유_9-2-4"])))
    print("별표37 PDF: 쪽마다 같음 %s · 주석 %s · AcroForm %s · XObject %s" % (
        all(out["별표37_PDF"]["쪽마다같음"]), out["별표37_PDF"]["주석쪽"], out["별표37_PDF"]["AcroForm"],
        [(x["쪽"], x["이름"], x.get("어두운화소")) for x in imgs]))
    for nm in regions:
        print("%s: 맞은 줄 %d · 상자 밖 %d · 「하위위험」 낱말 %d" % (nm, sr[nm]["맞은줄"], len(sr[nm]["상자밖"]), sr[nm]["하위위험_낱말"]))
    return out


# ── fix(보정 — 요청 없음, 멱등: 언제나 검증 전 사본에서 다시 만든다) ───────────────
BAK1 = os.path.join(VDIR, "_검증전_9-2-1_2_ORSA_연혁.md")
BAK2 = os.path.join(VDIR, "_검증전_9-2-3_5_별표37_별표22.md")
BAKC = os.path.join(VDIR, "_검증전_9-2-1_2_판목록.csv")
JUDGE = "(판단 — 지시서 9-2 에 조 번호 없음)"
T = {n: "제%s조(%s)" % (n, t) for n, t in (
    ("3", "적용대상"), ("6", "문서화"), ("8", "이사회"), ("10", "경영진"), ("18", "측정 및 관리 대상"), ("19", "위험 측정"),
    ("20", "위험 관리"), ("21", "신용위험"), ("22", "시장위험"), ("23", "운영위험"), ("24", "금리위험"), ("26", "신용편중위험"),
    ("33", "그룹내 위험 전이 방지"), ("35", "경영에의 활용"), ("36", "적용대상"), ("37", "자본적정성 평가 및 관리 체제"),
    ("38", "기본 원칙"),
    ("39", "이사회 및 경영진의 감독"), ("41", "독립적인 제3자 점검"), ("42", "위험 인식"), ("43", "위험 평가"),
    ("44", "통합 내부자본 산출"), ("45", "가용자본 산출"), ("46", "평가 및 관리"), ("47", "내부자본 한도 관리"), ("48", "보고"),
    ("49", "자본계획"), ("56", "통합위기상황분석"))}


def J(*nos):
    return " · ".join(T[n] for n in nos)


R75 = J("37", "18", "19", "20", "21", "22", "23", "35", "33")
S562 = J("39", "48", "42", "43", "44", "45", "46", "47", "49", "35", "36")
MAP1 = {"2-1": J("37") + " — 제5장(제36조~제49조) 전반",
        "2-2": J("18", "19", "20", "35", "33") + " — 문구가 들기 전 글(위험관리체제)",
        "2-3": R75, "2-4": J("37"), "2-5": J("37"), "2-6": R75, "2-7": R75, "2-8": R75, "2-9": J("37"),
        "3-1": J("37", "36"), "3-2": S562, "3-3": J("36"), "3-4": S562, "3-5": J("36", "3"),
        "3-6": J("36", "3", "37") + " — [별표 37] 항목별은 9-2-3_5 산출물 1-1 표", "3-7": J("37"), "3-8": J("37"),
        "3-9": J("36", "3")}
MAP2 = {"1.": J("37", "36") + " — 항목별은 1-1 표 마지막 칸",
        "1-1": "항목마다 표 마지막 칸 — " + J("37", "44", "45", "36", "3", "38", "39", "8", "10", "42", "43",
                                         "46", "49", "56", "47", "35", "48", "41", "6"),
        "1-2": J("46", "41", "6") + " — 다른 곳 3곳이 든 항목 15.(평가 범위 및 주기)·18.(제3자 검증)·19.(문서화)",
        "2-1": J("18"), "2-2": J("18", "19"), "2-3": J("18", "19"),
        "2-4": J("18", "42", "21", "22", "23", "24", "26"),
        "2-5": J("19", "21", "22", "23", "24", "26", "18"), "2-6": J("19", "21", "22", "23", "24", "26", "18"),
        "2-7": J("18", "42", "21", "22", "23", "24", "26"), "2-8": J("18", "21", "22", "23")}


class Fixer(object):
    def __init__(self, lines, name):
        self.L = list(lines)
        self.name = name
        self.log = []

    def rep(self, old, new, why, kind="보정"):
        hit = [i for i, l in enumerate(self.L) if old in l]
        if len(hit) != 1:
            raise SystemExit("%s: 「%s」 줄이 %d개" % (self.name, old[:50], len(hit)))
        i = hit[0]
        before = self.L[i]
        self.L[i] = before.replace(old, new)
        self.log.append(dict(파일=self.name, 종류=kind, 줄=i + 1, 전=old, 후=new, 설명=why))

    def after(self, anchor, new_lines, why, kind="채움"):
        hit = [i for i, l in enumerate(self.L) if l.startswith(anchor)]
        if len(hit) != 1:
            raise SystemExit("%s: 「%s」 로 시작하는 줄이 %d개" % (self.name, anchor[:50], len(hit)))
        i = hit[0]
        self.L[i + 1:i + 1] = new_lines
        self.log.append(dict(파일=self.name, 종류=kind, 줄=i + 2, 전="", 후="\n".join(new_lines)[:300], 설명=why))

    def tags(self, mp, pat):
        out, i, n = [], 0, 0
        while i < len(self.L):
            ln = self.L[i]
            out.append(ln)
            m = re.match(pat, ln)
            if m and m.group(1) in mp:
                if i + 1 < len(self.L) and self.L[i + 1] == "":
                    out.append("")
                    i += 1
                out.append("- 모범규준 조%s: %s (판단)" % (JUDGE, mp[m.group(1)]))
                out.append("")
                n += 1
            i += 1
        self.L = out
        self.log.append(dict(파일=self.name, 종류="모범규준 조", 줄="", 전="", 후="자료 묶음 %d곳" % n,
                             설명="자료 묶음마다 「- 모범규준 조%s」 줄을 붙임(조목록 2016.8.1 판 제목)" % JUDGE))


def _cite_x(serial, where):
    p = xml_path(serial)
    x = P.info(rd(p))
    m = _meta(p)
    return "[%s · 일련번호 %s(발령 %s · 시행 %s · 발령번호 %s) · %s · %s · 수집 %s]" % (
        x.get("행정규칙명"), serial, _fmt(x.get("발령일자", "")), _fmt(x.get("시행일자", "")), x.get("발령번호", ""),
        m.get("출처URL", "http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=%s&type=XML" % serial),
        where, m.get("fetched_at", ""))


def _code(lines_):
    body = "\n".join(l.rstrip() for l in lines_)
    assert "```" not in body
    return ["```text"] + body.split("\n") + ["```"]


def _difflabel(a, b):
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]
    parts = []
    for o in ops[:4]:
        x, y = a[o[1]:o[2]], b[o[3]:o[4]]
        parts.append("「%s」→「%s」" % (x.replace("\n", "⏎")[:14] or "∅", y.replace("\n", "⏎")[:14] or "∅"))
    return " ".join(parts) + (" 외 %d곳" % (len(ops) - 4) if len(ops) > 4 else "")


def _txt_of(key, serial):
    xb = rd(xml_path(serial))
    if key.endswith("[별표 37]"):
        a = annex(xb, "0037")
        return a["별표내용"] if a else ""
    return W.find_jo(xb, key.split("|")[1])[0]


def runs(v):
    """받은 판의 판정 차례를 순번 구간으로: N(0~70) Y(71~126)."""
    f = v["판정기준"]
    got = [x for x in v["판"] if x["받음"] == "Y"]
    out, cur, a, b = [], None, None, None
    for x in got:
        if x[f] != cur:
            if cur is not None:
                out.append("%s(%s)" % (cur, ("%d" % a) if a == b else ("%d~%d" % (a, b))))
            cur, a = x[f], x["순번"]
        b = x["순번"]
    out.append("%s(%s)" % (cur, ("%d" % a) if a == b else ("%d~%d" % (a, b))))
    return " → ".join(out)


def odd_rows(v):
    f = v["판정기준"]
    got = [x for x in v["판"] if x["받음"] == "Y"]
    k1 = next(i for i, x in enumerate(got) if x[f] == "Y")
    return [x for x in got[k1:] if x[f] == "N"]


def build_s6(S, orig_rows):
    """md1 「## 6. 검증 보충」."""
    out = ["## 6. 검증 보충(2026-10-07) — 이분 탐색이 건너뛴 판 전수 대조", "",
           "- 모범규준 조%s: %s · %s (판단) — 2~4절과 같은 기준" % (JUDGE, T["37"], T["36"]), "",
           "- 방법: `scripts/dart/verify13_law92.py fetch` 로 연혁 목록(2-1 note 의 nw=2 목록, 같은 날 받은 것)에서 수집 때 받지 않은 판을 "
           "`lawService.do target=admrul ID=<행정규칙일련번호> type=XML` 로 받았다(원본 `dart_out/raw/web13/verify13_law92/`, "
           "원장 `verify13_law92/_call_log.csv`, OC=***, LAW_DELAY=1.0, 요청 시각 2026-10-08 03:23~ UTC). 감독규정은 127판 전부, "
           "세칙은 판 XML 이 작은 순번 0~136 전부와 순번 182, 그리고 큰 판(4~5MB) 구간 138~160 은 경계 이분 탐색으로 고른 판만 받았다. "
           "`scan` 이 받은 판마다 제7-5조·제5-6조의2(수집 스크립트와 같은 find_jo)·[별표 37](별표번호 0037 별표내용)을 떼어 바로 앞 받은 판과 "
           "비교했다(비교 기준은 머리의 「비교 기준」과 같음). 결과 원본 `verify13_law92/_scan.json`, 판목록 csv 의 「검증_」 열.", ""]
    nget = {k: sum(1 for r in orig_rows if r["대상"] == k.split("|")[1] and r["판_받음"] == "Y")
            for k in ("감독규정|제7-5조", "세칙|제5-6조의2", "세칙|[별표 37]")}
    out += ["### 6-1 덮은 범위와 처음 든 판 재확인", "",
            "- 모범규준 조%s: %s (판단)" % (JUDGE, T["37"]), "",
            "| 대상 | 연혁 목록 판수 | 수집 때 받은 판 | 검증에서 더 받은 판 | 지금 받은 판 | 받지 않은 순번(추출 범위에 없음) | 받은 판의 판정 차례 | 처음 Y 판(앞 받은 판 · 인접) |",
            "|---|---|---|---|---|---|---|---|"]
    for key in ("감독규정|제7-5조", "세칙|제5-6조의2", "세칙|[별표 37]"):
        v = S[key]
        got = [x for x in v["판"] if x["받음"] == "Y"]
        f = v["판정기준"]
        nN = sum(1 for x in got if x[f] == "N")
        nY = sum(1 for x in got if x[f] == "Y")
        out.append("| %s %s(판정: %s) | %d | %d | %d | %d | %s | %s(N %d판 · Y %d판, %s) | %s(%s) · 앞 %s(%s) · %s |" % (
            v["규정"], v["대상"], "「자체 위험 및 지급여력 평가」 문구" if f == "ORSA" else "있음", v["목록판수"], nget[key],
            v["받은판수"] - nget[key], v["받은판수"], v["받지않은순번"] or "없음", runs(v), nN, nY, "단조" if v["단조"] else "단조 아님",
            v["처음Y"]["일련번호"], _fmt(v["처음Y"]["발령일자"]), v["처음Y_앞판"]["일련번호"], _fmt(v["처음Y_앞판"]["발령일자"]),
            "인접" if v["처음Y_경계인접"] else "인접 아님"))
    r75 = S["감독규정|제7-5조"]
    orsa_any = r75["ORSA_XML어디든_처음"]
    s56 = S["세칙|제5-6조의2"]
    assert runs(r75) == "N(0~70) → Y(71~126)" and r75["받은판수"] == 127, runs(r75)
    odd = odd_rows(s56) if not s56["단조"] else []
    out += ["",
            "- note: 감독규정은 연혁 목록 127판을 모두 받아 단조 가정 없이 다시 보았다 — 「자체 위험 및 지급여력 평가」 문구는 순번 0~70 의 어느 판의 제7-5조에도 없고 "
            "순번 71(2100000044084, 발령 2016.04.01)부터 126(현행)까지 모든 판에 있다. 0절·2-1 의 결론(처음 든 판 2016.04.01 발령·시행, 제2016-15호)은 바뀌지 않는다.",
            "- note: 세칙 제5-6조의2 는 처음 나온 판(순번 93, 2016.04.28)의 앞 순번 0~92 를 모두 받아 「처음 나온 판」 결론은 그대로다. 다만 판정 차례가 단조가 아니다 — "
            "%s 판 XML 에는 제5-6조의2 가 없다. 두 판에서는 제5-3조의2 도 함께 빠져 조문내용 요소가 164개(앞 판 93·뒤 판 96 은 166개)이고, 판 XML 전체에 「자체 위험 및 지급여력 평가」 정규식이 맞는 곳이 없다. "
            "빠진 두 조는 2016.4.28 부칙 제1조가 「2017년 1월 1일부터 시행」으로 정한 조이며(3-3), 그 부칙은 두 판 XML 에도 실려 있다. 원문과 다른 곳 — 까닭은 법제처 자료에 설명 없음(판단 보류). "
            "수집 때 이분 탐색은 93 과 96 이 「같음」이라 그 사이(94·95)를 받지 않았다(단조 가정이 깨진 곳)." % (
                " · ".join("순번 %d(%s, 발령 %s · 시행 %s)" % (x["순번"], x["일련번호"], _fmt(x["발령일자"]), _fmt(x["시행일자"])) for x in odd)
                if odd else "(없음)"),
            "- note: 같은 정규식을 판 XML 전체(조문·부칙·개정문·별표·제개정이유)에 걸어도 감독규정에서 처음 맞는 판은 %s(%s 발령)이다%s." % (
                orsa_any["일련번호"], _fmt(orsa_any["발령일자"]),
                " — 제7-5조에 처음 든 판과 같다" if orsa_any["일련번호"] == "2100000044084" else " — 제7-5조에 처음 든 판과 다르다(6-3 참조)"),
            "- note: 세칙 판 XML 전체에서 같은 정규식이 처음 맞는 판은 %s(%s 발령)이다." % (
                s56["ORSA_XML어디든_처음"]["일련번호"], _fmt(s56["ORSA_XML어디든_처음"]["발령일자"])),
            "- note: 세칙에서 받지 않은 순번(%s)은 판 XML 이 4~5MB 인 2020.10 뒤 판이다. 이 구간의 제5-6조의2·[별표 37] 글은 추출 범위에 없음 — "
            "찾은 방법: 앞뒤 받은 판의 글이 같은 구간은 받지 않았고(같음/같음(둘 다 없음)), 글이 달라진 구간(순번 138~160)만 가운데 판을 받아 인접 판 사이로 좁혔다(단조 가정). "
            "현행 조 끝 개정 표지 「<신설 2016. 4. 28., 개정 2026. 6. 29.>」, [별표 37] 첫 줄 「<신설 2026.06.29.>」 와 받은 판의 변화가 맞는다(3-7·3-6)." % (
                s56["받지않은순번"]), ""]
    # 6-2 옛 이름 판
    out += ["### 6-2 연혁 목록(이름 필터)에서 빠졌던 같은 행정규칙ID 의 옛 이름 판", "",
            "- 모범규준 조%s: %s (판단)" % (JUDGE, T["37"]), "",
            "- note: 수집 때 연혁 목록은 검색 응답(`law92/연혁검색_*.xml`, query=보험업감독규정·보험업감독업무시행세칙, nw=2) 가운데 행정규칙명이 "
            "정확히 같은 행만 남겼다. 같은 응답에 행정규칙ID 가 같은(21843 · 2041116) 옛 이름 「보험감독규정」·「보험감독규정시행세칙」·「보험감독규정 시행세칙」 판이 "
            "있어 이분 탐색 범위 밖이었다. 검증에서 모두 받아 보았다.", "",
            "| 목록 | 행정규칙명(검색 응답) | 일련번호 | 발령 | 시행 | 제개정 | 제7-5조 | 제5-6조의2 | [별표 37] | 「자체 위험 및 지급여력 평가」(XML 전체) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for x in S["옛이름판"]:
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x["목록이름"], x["행정규칙명"], x["일련번호"], _fmt(x["발령일자"]), _fmt(x["시행일자"]), x["제개정"],
            x.get("제7_5조", "받지 못함"), x.get("제5_6조의2", "받지 못함"), x.get("별표37", "받지 못함"),
            x.get("ORSA_XML어디든", "받지 못함")))
    om = [r for r in hist_all() if "일괄개정" in r.get("행정규칙명", "")]
    if om:
        o = om[0]
        tgt = [x for x in r75["판"] if x["발령일자"] == o["발령일자"]]
        out += ["", "- note: 같은 검색 응답의 「%s」(%s, 발령 %s, 행정규칙ID %s)는 다른 ID 의 일괄개정 규정이다. 같은 날 발령된 보험업감독규정 판(순번 %s, %s, %s)이 "
                "연혁 목록에 있어 6-3 전수 대조에 들어갔고, 그 판의 제7-5조는 앞 판과 「%s」 이다." % (
                    o["행정규칙명"], o["행정규칙일련번호"], _fmt(o["발령일자"]), o["행정규칙ID"],
                    tgt[0]["순번"] if tgt else "?", tgt[0]["일련번호"] if tgt else "?", tgt[0]["제개정"] if tgt else "?",
                    tgt[0]["앞판대비"] if tgt else "?")]
    out.append("")
    # 6-3 · 6-4 변화 목록
    for sec_no, keys, title in (("6-3", ("감독규정|제7-5조",), "감독규정 제7-5조 — 연혁 목록 127판 전부의 변화(「같음」이 아닌 판)"),
                                ("6-4", ("세칙|제5-6조의2", "세칙|[별표 37]"), "세칙 제5-6조의2·[별표 37] — 받은 판의 변화(「같음」이 아닌 판)")):
        out += ["### %s %s" % (sec_no, title), "",
                "- 모범규준 조%s: %s (판단)" % (JUDGE, R75 if sec_no == "6-3" else S562), "",
                "| 대상 | 순번 | 일련번호 | 발령 | 시행 | 제개정 | 앞 받은 판 대비 | 인접 | 글자수 | 바뀐 글자(해설 — 앞 받은 판 → 이 판, 공백 무시 아님) |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for key in keys:
            v = S[key]
            rows = v["판"]
            for x in rows:
                if x["받음"] != "Y" or x["앞판대비"] in ("같음", "같음(둘 다 없음)", "처음 받은 판"):
                    continue
                lab = ""
                if x["앞판대비"] in ("표기만 다름(판단)", "글 바뀜"):
                    lab = _difflabel(_txt_of(key, x["앞받은판"]), _txt_of(key, x["일련번호"]))
                out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    v["대상"], x["순번"], x["일련번호"], _fmt(x["발령일자"]), _fmt(x["시행일자"]), x["제개정"], x["앞판대비"],
                    x["인접"], x["글자수"], lab.replace("|", "｜")))
        out += ["", "- note: 「바뀐 글자」 칸은 difflib 로 뽑은 해설이다(원문 인용 아님 — 원문은 각 판 XML, 판 글은 `verify13_law92/_scan.json` 의 sha256 로 확인). "
                "「표기만 다름(판단)」 은 수집 때와 같은 기준(공백·가운뎃점·물음표·마침표·따옴표만 다름)이다.", ""]
    # 6-5 보도자료 교차 대조
    pm = _meta(PRESS_HWP[:-3])
    q = ["자체 위험 및 지급여력 평가제도 도입",
         " ㅇ  보험회사가 자체적으로 재무건전성의 적정성을 평가하여 의사결정에 활용하는 자체 위험 및 지급여력 평가제도 도입",
         "    * (현행) 보험회사 재무건전성 평가시 RBC비율 등 정량적 평가에만 의존",
         "      (개선) 보험회사 스스로 재무건전성을 정성적으로 평가하여 미래 위험에 대처할 수 있도록 자체위험 및 지급여력 평가제도 세부기준 마련"]
    s92 = [x for x in s56["판"] if x["일련번호"] == "2200000047377"][0]
    out += ["### 6-5 2016.3.30 보도자료(9-2-4 산출물)와 교차 대조 — 개정 취지", "",
            "- 모범규준 조%s: %s (판단)" % (JUDGE, T["37"]), "",
            "- note: 2016.4.1 감독규정 판(2100000044084)·2016.4.28 세칙 판(2200000048212) XML 에는 <제개정이유> 요소가 없다(검증 search — 6-6). "
            "개정 취지는 9-2 의 4번 산출물(`handoff/13차_산출물/9-2-4_ORSA_보도자료.md` Q2)이 받은 금융위·금감원 보도자료에 있어, 그 원본 글(같은 파일)과 대조해 한 단락을 옮긴다.",
            "- 인용: [금융위원회·금융감독원 보도자료 「｢보험산업 경쟁력 강화 로드맵｣ 후속 조치를 위한 ｢보험업법 시행령｣ 등 보험업법령 개정·시행」(배포 2016.3.30) · "
            "첨부 「%s」 · https://www.fsc.go.kr/no010101/72075 · PDF p.3(금융위 72075 첨부 PDF) · 수집 %s · 대조 원본: hwp 글 `%s`]" % (
                pm.get("원파일명", ""), pm.get("fetched_at", ""), PRESS_HWP)]
    out += _code(q)
    out += ["",
            "- note: 같은 보도자료는 개정 경과를 「보험업감독규정(3.30일 금융위원회 의결), 보험업감독업무시행세칙(3.30일 확정)」, 시행을 「4.1일부터」로 적는다"
            "(9-2-4 산출물 Q2 「개정 경과」 인용). 법제처 연혁에서 2016.03.30 발령 세칙 판(순번 92, 2200000047377)에는 제5-6조의2 가 없고, "
            "판 XML 전체에서 「자체 위험 및 지급여력 평가」 정규식이 맞는 곳도 %s(검증 scan). 제5-6조의2 는 2016.04.28 발령 판(2200000048212)에 처음 나온다 — "
            "원문과 다른 곳(3.30 확정분과 4.28 발령분의 관계는 두 자료에 설명 없음, 판단 보류)." % (
                "없다" if s92.get("ORSA_XML어디든") == "N" else "있다"),
            "- note: 감독규정 쪽은 보도자료의 「4.1일부터 시행」과 처음 든 판의 발령·시행일(2016.04.01)이 맞고, 시행일 표의 「자체 위험 및 지급여력 평가제도 도입 | ‘17.1.1일」"
            "(9-2-4 산출물 Q2)은 그 판 부칙 제1조의 제7-5조제1항 시행일(2017.1.1)과 맞는다(2-5).", ""]
    # 6-6 개정 표지·제개정이유
    srch = load(SEARCH)
    tg = srch.get("개정이유_XML요소", {})
    out += ["### 6-6 개정 표지·<제개정이유> 요소와의 대조", "",
            "- 모범규준 조%s: %s (판단)" % (JUDGE, T["37"]), "",
            "- note: 현행 제7-5조 ① 끝 표지는 「<개정 2016. 4. 1.>」, ② 끝은 「<개정 2016. 4. 1., 2022. 12. 21.>」 이다(2-8). 127판 전수 대조에서 실질 글이 바뀐 판은 "
            "2016.04.01(①②)·2016.07.28 타법개정(①의 근거 조문)·2022.12.22(②) 셋이며, 2016.07.28 타법개정에는 조 끝 표지가 붙지 않았다(2-6 note 와 같음).",
            "- note: 받은 판 XML %d개의 요소 이름 %d종을 「이유·취지·사유」로 찾으면 <제개정이유>·<제개정이유내용> 이 있다(수집 때 「행정규칙 XML 에 제·개정 이유 칸이 없어」라고 "
            "적은 것을 바로잡음). 판(일련번호)별로 세면 %s. 제7-5조 글이 바뀐 세 판 가운데에는 2022.12.22 판(2100000217538)에만 있다 — 전문은 2-7." % (
                tg.get("XML수", 0), len(tg.get("요소이름", [])),
                " · ".join("%s %d판 중 %d판%s" % (k, v["있음"] + v["없음"], v["있음"], (" (처음 %s 발령 판)" % _fmt(v["처음"])) if v["처음"] else "")
                           for k, v in sorted(srch.get("제개정이유_판", {}).items()))), ""]
    return out


def build_s5_md2(srch):
    """md2 「## 5. 검증 보충」."""
    sx = rd(SEC_XML9)
    AL = annex(sx, "0022")["별표내용"].split("\n")
    BL = annex(sx, "0022", "01")["별표내용"].split("\n")
    pdfi = srch["별표37_PDF"]
    sr = srch["별표22_하위위험"]
    reg5 = "Ⅳ 제5장 신용위험액 8997~10486줄"
    reg6 = "Ⅳ 제6장 운영위험액 10487~10660줄"
    pick = [r["줄"] for r in sr[reg5]["상자밖"] if re.search(r"구분|신용위험액은", r["글"])][:3] + \
        [r["줄"] for r in sr[reg5]["상자밖"] if r["글"].startswith("가.신용위험액은")]
    pick = sorted(set(x for x in pick if x in (9029, 9169, 9353)))
    pick6 = sorted(set(r["줄"] for r in sr[reg6]["상자밖"] if r["줄"] in (10495, 10507, 10527, 10577)))
    cite = "[보험업감독업무시행세칙(일련번호 2200000108939) · http://www.law.go.kr/DRF/lawService.do?OC=***&target=admrul&ID=2200000108939&type=XML · %s 별표내용 %s줄 · 수집 2026-10-01, 현행 재확인 2026-10-08T08:50]"
    out = ["## 5. 검증 보충(2026-10-07)", "",
           "- 모범규준 조%s: %s · %s · %s (판단)" % (JUDGE, T["21"], T["23"], T["18"]), "",
           "### 5-1 「PDF 에만 있는 [별표 37] 글」 반박 시도", "",
           "- 모범규준 조%s: %s (판단)" % (JUDGE, T["37"]), "",
           "- note: 같은 PDF(`dart_out/raw/web10/annex37/세칙_별표37.pdf`, flSeq=168886133)를 pypdf %s 로 다시 읽어 %d쪽 모두 10차 텍스트와 공백 무시 같음(%s), "
           "주석(/Annots) 있는 쪽 %s, 서식(/AcroForm) %s, 그림 XObject %d개(%s). 그림은 RGB 화소에서 밝기 128 미만을 세어 다시 확인했다. "
           "hwp 「## 원문」 180줄과 PDF 글 층은 공백을 빼면 9336자로 같다. → 반박 실패(PDF 에만 있는 글을 찾지 못함 — 추출 범위에 없음 유지)." % (
               pdfi["pypdf"], pdfi["쪽수"], all(pdfi["쪽마다같음"]), pdfi["주석쪽"] or "없음", "있음" if pdfi["AcroForm"] else "없음",
               len(pdfi["XObject"]), "; ".join("p.%d %s %s %d×%d 어두운 화소 %s개 가로 %s~%s·세로 %s~%s" % (
                   x["쪽"], x["이름"], x["종류"], x["가로"], x["세로"], x.get("어두운화소"), *(x.get("범위") or ("?",) * 4))
                   for x in pdfi["XObject"])), "",
           "### 5-2 [별표 22] 신용·운영위험액에서 넓은 검색어로 찾은 「구분」 줄", "",
           "- 모범규준 조%s: %s · %s (판단)" % (JUDGE, T["21"], T["23"]), "",
           "- note: 검색어(정규식) %s 를 정의 (4)(5)(285~292줄)·Ⅳ 제5장(8997~10486줄)·제6장(10487~10660줄)에 걸었다. 맞은 줄: 정의 %d · 제5장 %d · 제6장 %d — "
           "「하위위험」·「하위 위험」 낱말은 세 범위에 0곳이다(반박 실패 — 신용·운영의 「하위위험」 이름은 추출 범위에 없음 유지). [별표 22] 전체에서 「하위\\s*위험」 이 든 줄은 %d곳"
           "(제2·3·4장, Ⅰ.2.라.(1)~(3), 1-6.비례성원칙 등). 대신 측정 대상을 나누는 줄을 아래에 옮긴다(위험 이름이 아니라 익스포져·위험액의 구분)." % (
               " · ".join("`%s`" % t for t in srch["별표22_하위위험"]["검색어"]), sr["정의(4)(5) 285~292줄"]["맞은줄"], sr[reg5]["맞은줄"],
               sr[reg6]["맞은줄"], len(sr["[별표 22] 전체 「하위\\s*위험」 줄"])), "",
           "| 별표내용 줄 | 위치(부 > 장 > 항 > 목 > 세목) |", "|---|---|"]
    paths = {9029: "Ⅳ. > 제5장 > 5-1. > 나. > (1)", 9169: "Ⅳ. > 제5장 > 5-1. > 나. > (2)", 9353: "Ⅳ. > 제5장 > 5-2. > 가.",
             10495: "Ⅳ. > 제6장 > 6-1. > 가.", 10507: "Ⅳ. > 제6장 > 6-1. > 나. > (1)", 10527: "Ⅳ. > 제6장 > 6-1. > 나. > (2)",
             10577: "Ⅳ. > 제6장 > 6-2. > 가."}
    lines_ = pick + pick6
    for n in lines_:
        out.append("| %d | %s |" % (n, paths.get(n, "")))
    out += ["", ("원문 " + cite % ("[별표 22]", "%d~%d" % (lines_[0], lines_[-1]))) +
            " — 위 표의 줄만 표의 차례대로 옮겼다(그 사이 줄은 뺐다)"]
    out += _code([AL[n - 1] for n in lines_])
    out += ["- note: 위치 칸은 이 절에서 줄 번호로 매긴 해설이다(판단). 9025·9217·10503·10581·10629줄은 2-6 에 이미 옮겼다.", ""]
    bl = [49, 51, 53, 57, 59, 61]
    out += ["### 5-3 [별표 22-1](내부모형 적용기준)의 「개별위험」·「하위위험」 정의", "",
            "- 모범규준 조%s: %s · %s (판단)" % (JUDGE, T["18"], T["42"]), "",
            "- note: 2-1 에서 범위 밖으로 둔 [별표 22-1] 별표내용(1850줄)에 같은 검색어를 걸면 「하위\\s*위험」 줄 %d곳이 나온다. 그 가운데 정의 두 항을 옮긴다 — "
            "신용·운영리스크의 하위위험 이름은 여기에도 없다(예시는 생명·장기손해보험위험의 7개뿐)." % len(sr["[별표 22-1] 「하위\\s*위험」 줄"]), "",
            "| 별표내용 줄 | 위치(부 > 장 > 항 > 목 > 세목) |", "|---|---|"]
    for n in bl:
        out.append("| %d | %s |" % (n, "[별표 22-1] > 라." if n < 57 else "[별표 22-1] > 마."))
    out += ["", ("원문 " + cite % ("[별표 22-1]", "49~61")) + " — 위 표의 줄만 표의 차례대로 옮겼다(그 사이 빈 줄은 뺐다)"]
    out += _code([BL[n - 1] for n in bl])
    out += ["- note: [별표 22-1] 첫 줄은 「[별표 22-1] <신설 2026.06.29.>」 이다(이 판 별표내용 1줄). 상자 그림 글의 「?」 는 XML 원문 그대로(가운뎃점 자리).", ""]
    return out


def fix():
    for src, bak in ((MD1, BAK1), (MD2, BAK2), (CSV_VER, BAKC)):
        if not os.path.exists(bak):
            with open(bak, "wb") as f:
                f.write(rd(src))
    S = load(SCAN)
    srch = load(SEARCH)
    if not S or not srch:
        raise SystemExit("scan·search 를 먼저")
    orig_rows = list(csv.DictReader(open(BAKC, encoding="utf-8-sig")))
    # ── md1
    F1 = Fixer(open(BAK1, encoding="utf-8").read().rstrip("\n").split("\n"), "9-2-1_2_ORSA_연혁.md")
    v75, v56 = S["감독규정|제7-5조"], S["세칙|제5-6조의2"]
    F1.rep("받지 않은 사이 판의 글은 추출 범위에 없음.",
           "받지 않은 사이 판의 글은 추출 범위에 없음. [검증 보충 2026-10-07: 감독규정은 연혁 목록 127판을 모두 받아 단조 가정 없이 다시 대조했다 — 결론 같음(6-1·6-3). "
           "세칙은 %d판을 받아 다시 대조했고, 받지 않은 순번 %s 의 글은 추출 범위에 없음(6-1 note — 앞뒤 받은 판의 글이 같은 구간)]" % (
               v56["받은판수"], v56["받지않은순번"]),
           "한계 ① 에 전수 대조 결과를 덧붙임(반박: 감독규정 성공, 세칙 일부)")
    F1.rep("③ 행정규칙 XML 에 제·개정 이유 칸이 없어 개정 취지는 옮기지 않았다.",
           "③ 행정규칙 XML 의 제·개정 이유 칸(<제개정이유>)은 문구가 처음 든 2016.4.1 판·2016.7.28 판과 세칙 판에는 없어 그 개정 취지는 XML 에서 옮기지 못했다"
           "(2022.12.22 판에는 있어 2-7 에 옮김, 2016.4.1 판의 취지는 보도자료에서 6-5 에 옮김 — 검증 보정 2026-10-07).",
           "한계 ③ 의 「행정규칙 XML 에 제·개정 이유 칸이 없어」는 틀림 — 2100000217538 등 감독규정 판 %d개 XML 에 <제개정이유> 요소가 있음(검증 search)" %
           srch.get("제개정이유_판", {}).get(REG, {}).get("있음", 0), "바로잡음")
    F1.rep("5절 2016.8.1 판 전문).",
           "5절 2016.8.1 판 전문). 검증(2026-10-07): 2·3·6절 자료 묶음마다 「- 모범규준 조」 줄을 같은 기준으로 붙였다(전부 판단).",
           "모범규준 조 표기 범위 덧붙임")
    F1.rep("「표기만 다름」 경계는 사이 판을 받지 않았다.",
           "「표기만 다름」 경계는 사이 판을 받지 않았다. [검증 보충 2026-10-07: 이 문장은 수집 때 받은 판 기준이다. 사이 판까지 받아 보니 세칙 제5-6조의2 는 2016.06.10·2016.06.23 판에 없다가 2016.06.30 판에 다시 있다(있음→없음→있음 — 6-1 note·6-4). 감독규정 「표기만 다름」 경계는 6-3 에서 모두 인접 판 사이로 닫힘]",
           "비교 기준 줄에 전수 대조로 드러난 단조 가정 예외를 덧붙임")
    F1.after("- 모범규준 조 번호: 지시서 9-2 에는 조 번호가 없다.",
             ["- 검증(2026-10-07): `scripts/dart/verify13_law92.py`(인자 없이 돌리면 대조만) — 원문 인용 전부를 법제처 XML·보도자료 원본 글과 공백 무시로 대조, "
              "판목록 csv 재계산, 이분 탐색이 건너뛴 판 전수 대조(6절), 결과 `dart_out/risk13/verify13_law92.txt`, 고친 곳은 끝 「검증 기록」 절."],
             "머리에 검증 줄 추가")
    F1.after("| 현행 세칙(오늘 재확인) |",
             ["", "- note(검증 2026-10-07): 위 「처음 든 판」·「처음 나온 판」 세 줄은 6절 전수 대조(감독규정 127판 전부, 세칙 %d판)로 다시 확인했다 — 바뀐 곳 없음." %
              v56["받은판수"]], "0절 요약에 검증 결과 note")
    xb538 = rd(xml_path("2100000217538"))
    rs = "".join(ET.fromstring(xb538).find(".//제개정이유").itertext())
    rs_lines = rs.strip("\n").split("\n")
    F1.after("- note: 이 판 XML 에는 <개정문> 요소가 없다.",
             ["- note(검증 보충 2026-10-07): 이 판 XML 에는 <제개정이유> 요소가 있다(수집 때 한계 ③ 「행정규칙 XML 에 제·개정 이유 칸이 없어」를 바로잡음 — 6-6). 전문:",
              "- 인용: " + _cite_x("2100000217538", "<제개정이유> 제개정이유내용")] + _code(rs_lines) + [""],
             "2022.12.22 판 <제개정이유> 전문 인용 추가(「개정 이유 — 추출 범위에 없음」 반박 성공)")
    lab = {x["순번"]: x for x in v75["판"]}
    F1.rep("2017.8.28 판부터 `·`, 2022.2.17 판부터 `ㆍ` 로 실려 있다(받은 판 기준).",
           "2017.8.28 판부터 `·`, 2022.2.17 판부터 `ㆍ` 로 실려 있다(받은 판 기준). [검증 보충 2026-10-07 — 127판 전수 대조: `?`→`·` 는 %s 판(순번 76)부터, "
           "`·`→`ㆍ` 는 %s 판(순번 101)부터다. 2005~2015 사이에도 제7-5조 가운뎃점 자리가 `“`(2005.03.03 판) 또는 `?`(2010.04.01·2012.02.28·2015.09.07 판부터)로 바뀌었다가 뒤 판(2005.03.30·2011.03.22·2012.06.26·2015.11.24)에서 `·` 로 돌아온 구간이 있다 — 6-3]" % (
               _fmt(lab[76]["발령일자"]), _fmt(lab[101]["발령일자"])),
           "2-3 note 의 가운뎃점 표기 판을 전수 대조로 좁힘(받은 판 기준 → 정확한 판)")
    odd56 = odd_rows(v56) if not v56["단조"] else []
    F1.rep("신설 뒤 글이 실질적으로 바뀐 판은 받은 판 가운데 이 판 하나다",
           "신설 뒤 글이 실질적으로 바뀐 판은 받은 판 가운데 이 판 하나다[검증 보충 2026-10-07: 세칙 %d판 대조에서도 「글 바뀜」은 이 판뿐이다. 다만 %s 판 XML 에는 제5-6조의2 가 없다 — 6-1 note·6-4]" % (
               v56["받은판수"], "·".join("%s(%s)" % (_fmt(x["발령일자"]), x["일련번호"]) for x in odd56)),
           "3-4 note 에 전수 대조 결과(제5-6조의2 가 빠진 판) 덧붙임")
    F1.rep("「인접」이 N 인 경계는 사이 판을 받지 않아 표기가 바뀐 정확한 판은 추출 범위에 없음.",
           "「인접」이 N 인 경계는 사이 판을 받지 않아 표기가 바뀐 정확한 판은 추출 범위에 없음(이 표는 수집 때 받은 판만). → 검증 보충 6-3: 127판 전부를 받아 표기가 바뀐 정확한 판을 적었다.",
           "2-9 note 에 전수 대조 결과 안내")
    ch75 = [x for x in v75["판"] if x["받음"] == "Y" and x["앞판대비"] == "표기만 다름(판단)"]
    F1.rep("| 추출 범위에 없음 | 표기만 바뀐 경계(가운뎃점·공백)의 정확한 판 | 사이 판을 받지 않음(판목록 csv 「판정」 칸) |",
           "| 받은 것(검증 보충 — 제7-5조) · 추출 범위에 없음(세칙 일부) | 표기만 바뀐 경계(가운뎃점·공백)의 정확한 판 | 제7-5조: 127판 전수 대조로 %d곳 모두 인접 판 사이로 찾음(%s) — 6-3. "
           "제5-6조의2: 받은 %d판 사이 경계 — 6-4(남은 받지 않은 순번은 6-1). [수집 때 글: 「추출 범위에 없음 · 사이 판을 받지 않음(판목록 csv 「판정」 칸)」] |" % (
               len(ch75), ", ".join(_fmt(x["발령일자"]) for x in ch75), v56["받은판수"]),
           "「추출 범위에 없음」(표기 경계) 반박: 제7-5조 성공·세칙 일부", "상태 바꿈")
    F1.rep("| 추출 범위에 없음 | 받지 않은 사이 판의 제7-5조·제5-6조의2 글 | 단조 가정으로 건너뜀 — 판목록 csv 「판_받음」 N |",
           "| 받은 것(검증 보충 — 제7-5조 127판 전부) · 추출 범위에 없음(세칙 일부) | 받지 않은 사이 판의 제7-5조·제5-6조의2 글 | 제7-5조: 전부 받음(6-1·6-3, 판목록 csv 「검증_」 열). "
           "제5-6조의2·[별표 37]: 받지 않은 순번 %s — 추출 범위에 없음(찾은 방법: 앞뒤 받은 판 글이 같은 구간이라 받지 않음, 6-1 note). [수집 때 글: 「추출 범위에 없음 · 단조 가정으로 건너뜀 — 판목록 csv 「판_받음」 N」] |" % (
               v56["받지않은순번"]),
           "「추출 범위에 없음」(사이 판 글) 반박: 제7-5조 성공·세칙 일부", "상태 바꿈")
    F1.rep("| 추출 범위에 없음 | 개정 이유(제·개정 이유서) | 행정규칙 XML 에 칸 없음; 다른 경로(관보·금융위 보도자료)는 이번 범위 밖 — 보도자료는 9-2 의 4번 몫 |",
           "| 받은 것(검증 보충 — 2022.12.22 판·2016.3.30 보도자료) · 추출 범위에 없음(2016.4.1·2016.7.28 판, 세칙 판의 XML 제개정이유) | 개정 이유(제·개정 이유서) | "
           "2100000217538 판 <제개정이유> 전문 → 2-7; 2016.4.1 판의 개정 취지는 9-2-4 보도자료(2016.3.30)에서 → 6-5. 찾은 방법: 받은 XML %d개의 요소 이름 전수를 「이유·취지·사유」로 검색 — "
           "2016.4.1·2016.7.28 판과 세칙 판에는 <제개정이유> 없음(6-6). 관보는 찾지 않음. [수집 때 글: 「추출 범위에 없음 · 행정규칙 XML 에 칸 없음; 다른 경로(관보·금융위 보도자료)는 이번 범위 밖 — 보도자료는 9-2 의 4번 몫」] |" % (
               srch["개정이유_XML요소"]["XML수"]),
           "「추출 범위에 없음」(개정 이유) 반박: 2022.12.22 판은 성공, 2016.4.1 판은 보도자료로 일부", "상태 바꿈")
    F1.after("| 원문과 다른 곳 | 지시서 「'자체 위험 및 지급여력 평가 체제' 문구」",
             ["| 원문과 다른 곳(검증 보충) | 수집 때 한계 ③ 「행정규칙 XML 에 제·개정 이유 칸이 없어」 ↔ 2100000217538 등 감독규정 판 XML 의 <제개정이유> 요소 | 2-7 · 6-6 |",
              "| 원문과 다른 곳(검증 보충) | 2016.3.30 보도자료 「보험업감독업무시행세칙(3.30일 확정)」 ↔ 법제처 연혁: 2016.03.30 발령 세칙 판(2200000047377)에 제5-6조의2 없음, 처음 나온 판은 2016.04.28 발령 | 6-5 |",
              "| 받은 것(검증 보충) | 연혁 목록 이름 필터로 빠졌던 같은 행정규칙ID 옛 이름 판 %d개(보험감독규정·보험감독규정시행세칙) — 제7-5조·제5-6조의2·[별표 37]·문구 모두 없음 | 6-2 |" %
              len(S["옛이름판"]),
              "| 받은 것(검증 보충) | 보도자료로 본 2016.4.1 개정 취지(9-2-4 산출물 원본 글과 대조) | 6-5 |",
              "| 원문과 다른 곳(검증 보충) | 세칙 %s 판 XML 에 제5-6조의2·제5-3조의2 가 없음(앞 2016.04.28 판·뒤 2016.06.30 판에는 있음 — 수집 때 단조 가정이 깨진 곳) | 6-1 · 6-4 |" % (
                  "·".join("%s(%s)" % (_fmt(x["발령일자"]), x["일련번호"]) for x in odd56))],
             "5절 표에 검증 보충 행 추가")
    F1.tags(MAP1, r"^### (\d+-\d+) ")
    F1.L += [""] + build_s6(S, orig_rows)
    # ── md2
    F2 = Fixer(open(BAK2, encoding="utf-8").read().rstrip("\n").split("\n"), "9-2-3_5_별표37_별표22.md")
    ML = open(MOBEOM_MD, encoding="utf-8").read().split("\n")
    s5 = next(i for i, l in enumerate(ML) if l.startswith("## 5. "))
    n18 = next(i for i in range(s5, len(ML)) if ML[i].startswith("제18조(측정 및 관리 대상)")) + 1
    n42 = next(i for i in range(s5, len(ML)) if ML[i].startswith("제42조(위험 인식)")) + 1
    F2.rep("(9-4_모범규준_원문.md 909·996줄)", "(9-4_모범규준_원문.md %d·%d줄 — 5절 제18조제1항·제42조제1항)" % (n18, n42),
           "모범규준 원문 md 줄 번호가 지금 파일과 다름(909·996 → %d·%d — 그 파일이 검증에서 늘어 줄이 밀림)" % (n18, n42), "바로잡음")
    F2.rep("찾은 범위: PDF 1~10쪽 글 층 전부(pypdf 로 다시 읽은 글이 10차 텍스트와 쪽마다 같음) ↔ 10차 md 「## 원문」 180줄.",
           "찾은 범위: PDF 1~10쪽 글 층 전부(pypdf 로 다시 읽은 글이 10차 텍스트와 쪽마다 같음) ↔ 10차 md 「## 원문」 180줄. [검증 2026-10-07: 주석·서식·그림까지 넓혀 다시 찾음 — 반박 실패, 5-1]",
           "1절 결론에 반박 시도 결과 덧붙임")
    F2.after("- 기록 파일: 스크립트 `scripts/dart/web13_law92b.py`",
             ["- 검증(2026-10-07): `scripts/dart/verify13_law92.py`(인자 없이 돌리면 대조만) — 원문 인용 전부를 hwp·PDF·XML 원본과 공백 무시로 대조, csv 3개 재계산, "
              "「추출 범위에 없음」 반박 시도(5절), 결과 `dart_out/risk13/verify13_law92.txt`, 고친 곳은 끝 「검증 기록」 절."],
             "머리에 검증 줄 추가")
    F2.rep("| 받지 못한 것 | PDF 에만 있는 [별표 37] 글 — 추출 범위에 없음(PDF 1~10쪽 글 층 ↔ hwp 「## 원문」, 공백 무시 글자 대조·줄 포함 대조) | 1 |",
           "| 받지 못한 것 | PDF 에만 있는 [별표 37] 글 — 추출 범위에 없음(PDF 1~10쪽 글 층 ↔ hwp 「## 원문」, 공백 무시 글자 대조·줄 포함 대조; 검증 2026-10-07: pypdf 재추출·주석·서식·그림 XObject 까지 다시 찾음 — 반박 실패) | 1 · 5-1 |",
           "「추출 범위에 없음」(PDF 에만 있는 글) 반박 실패 — 찾은 방법 덧붙임")
    F2.rep("| 받지 못한 것 | [별표 22] 신용리스크·운영리스크의 「하위위험」 이름 — 추출 범위에 없음(정의 (4)(5) 줄, Ⅳ 제5·6장 상자 밖 줄에서 「(이하 ‘…위험액’)」·「(하위위험)」 검색) | 2-4 · 2-6 |",
           "| 받지 못한 것 · 일부 받음(검증 보충) | [별표 22] 신용리스크·운영리스크의 「하위위험」 이름 — 추출 범위에 없음(정의 (4)(5) 줄, Ⅳ 제5·6장 상자 밖 줄에서 「(이하 ‘…위험액’)」·「(하위위험)」 검색; "
           "검증 2026-10-07: 검색어 %d개로 넓혀도 「하위위험」 낱말 0곳 — 반박 실패). 대신 익스포져·위험액 「구분」 줄 %d개와 [별표 22-1] 의 「하위위험」 정의를 옮김 | 2-4 · 2-6 · 5-2 · 5-3 |" % (
               len(SUB_TERMS), len([1 for _ in (9029, 9169, 9353, 10495, 10507, 10527, 10577)])),
           "「추출 범위에 없음」(신용·운영 하위위험) 반박 실패 — 찾은 방법 덧붙이고 관련 줄을 채움", "상태 바꿈")
    F2.after("| 다른 곳 | XML [별표 22] 별표내용 `?` 241개",
             ["| 다른 곳(검증 보충) | 3절 note 의 모범규준 원문 md 줄 번호 909·996 ↔ 지금 그 파일의 제18조·제42조 줄 %d·%d | 3 |" % (n18, n42)],
             "4절 표에 다른 곳 행 추가")
    F2.tags(MAP2, r"^#{2,3} (\d+(?:-\d+)?\.?)(?: |$)")
    F2.L += [""] + build_s5_md2(srch)
    for F in (F1, F2):
        for c in F.log:
            first = next((x for x in c["후"].split("\n") if x.strip()), "")
            if c["종류"] == "모범규준 조" or not first:
                continue
            key = first[:60]
            hit = [i for i, l in enumerate(F.L) if key in l]
            c["줄"] = hit[0] + 1 if hit else ""
    with open(MD1, "w", encoding="utf-8") as f:
        f.write("\n".join(F1.L) + "\n")
    with open(MD2, "w", encoding="utf-8") as f:
        f.write("\n".join(F2.L) + "\n")
    # ── 판목록 csv: 수집 때 열은 그대로, 검증 열을 붙임
    cols = list(orig_rows[0].keys())
    add = ["검증_판_받음", "검증_받은단계", "검증_XML경로", "검증_수집시각", "검증_있음", "검증_ORSA문구", "검증_ORSA_XML어디든",
           "검증_글자수", "검증_글_sha256", "검증_앞받은판", "검증_인접", "검증_앞판대비"]
    keymap = {"제7-5조": "감독규정|제7-5조", "제5-6조의2": "세칙|제5-6조의2", "[별표 37]": "세칙|[별표 37]"}
    out = []
    for r in orig_rows:
        sr = S[keymap[r["대상"]]]["판"][int(r["연혁순번"])]
        r = dict(r)
        got = sr["받음"] == "Y"
        r.update({"검증_판_받음": sr["받음"], "검증_받은단계": sr.get("단계", ""), "검증_XML경로": sr.get("파일", ""),
                  "검증_수집시각": _meta(sr["파일"]).get("fetched_at", "") if got else "", "검증_있음": sr.get("있음", ""),
                  "검증_ORSA문구": sr.get("ORSA", ""), "검증_ORSA_XML어디든": sr.get("ORSA_XML어디든", ""),
                  "검증_글자수": sr.get("글자수", "") if got else "", "검증_글_sha256": sr.get("글_sha256", ""),
                  "검증_앞받은판": sr.get("앞받은판", ""), "검증_인접": sr.get("인접", ""), "검증_앞판대비": sr.get("앞판대비", "")})
        out.append(r)
    write_csv(CSV_VER, cols + add, out)
    log = dict(만든때=now(), 고친곳=F1.log + F2.log + [dict(파일="9-2-1_2_판목록.csv", 종류="채움", 줄="", 전="", 후="검증 열 %d개" % len(add),
                                                       설명="수집 때 열은 그대로 두고 전수 대조 결과 열(%s)을 붙임" % ", ".join(add))])
    dump(FIXLOG, log)
    # 검증 기록(검사 결과를 넣으려고 한 번 돌린 뒤 덧붙임)
    probs, info_, res = check(write=False)
    probs = [p for p in probs if "검증 기록" not in p]
    for md, F, name in ((MD1, F1, "md1"), (MD2, F2, "md2")):
        rec = build_record(name, log, res, probs, S, srch)
        with open(md, "w", encoding="utf-8") as f:
            f.write("\n".join(F.L + [""] + rec) + "\n")
    probs, info_, res = check(write=True)
    print("fix: md1 %d곳 · md2 %d곳 고침/채움 · 판목록 csv 검증 열 %d개 · 남은 문제 %d건" % (
        len(F1.log), len(F2.log), len(add), len(probs)))
    for p in probs[:20]:
        print("  " + p[:220])


def _short(s, n=400):
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…(줄임)"


def build_record(name, log, res, probs, S, srch):
    md = MD1 if name == "md1" else MD2
    mine = [r for r in res if r["파일"] == md]
    out = [SREC, "",
           "- 검증 스크립트: `scripts/dart/verify13_law92.py`(인자 없이 = 대조만, 문제 0 이면 exit 0) · 결과 `dart_out/risk13/verify13_law92.txt` · "
           "보정 기록 `dart_out/raw/web13/verify13_law92/_fix_log.json` · 검증 전 사본 `dart_out/raw/web13/verify13_law92/_검증전_*.md·csv`.",
           "- 대조한 인용: 이 파일의 원문 인용 블록 %d개(> 인용 %d · 코드 블록 %d) — 일치 %d · 불일치 %d. 수집 때 블록 %d개는 글자 하나 고칠 곳 없이 원문과 맞았고, "
           "출처 표기(문서명·일련번호/URL·위치·수집 시각, 판 발령·시행·발령번호, OC 가림)도 원본 XML·meta 와 맞았다. 나머지 %d개는 검증 보충에서 새로 넣은 인용이다." % (
               len(mine), sum(1 for r in mine if r["종류"] == "인용"), sum(1 for r in mine if r["종류"] == "코드"),
               sum(1 for r in mine if r["결과"].startswith("일치")), sum(1 for r in mine if not r["결과"].startswith("일치")),
               20 if name == "md1" else 16, len(mine) - (20 if name == "md1" else 16)),
           "- 대조 방법: 공백만 무시. 조 「(조문내용)」 인용은 조 전문과 같아야 함(조문내용 요소를 이은 글에서 「제7-5조(」 부터 다음 조·장·절 표지 앞까지 — 수집 스크립트와 따로 뽑음), "
           "부칙은 부칙공포일자·번호로 고른 부칙내용 전문과 같아야 함(「발췌」는 포함), 개정문·별표·PDF 쪽은 포함, 「위 표의 줄만」 인용은 표의 줄 번호마다 별표내용 그 줄과 같아야 함.", ""]
    mylog = [c for c in log["고친곳"] if c["파일"] == os.path.basename(md) or (name == "md1" and c["파일"].endswith(".csv"))]
    out += ["### 고친 곳(전·후)", "", "| 종류 | 줄(고친 뒤 이 파일에서의 위치) | 설명 | 전 | 후 |", "|---|---|---|---|---|"]
    for c in mylog:
        out.append("| %s | %s | %s | %s | %s |" % (c["종류"], c["줄"], c["설명"].replace("|", "｜"),
                                              _short(c["전"]).replace("|", "｜") or "(없음 — 새로 넣음)",
                                              _short(c["후"]).replace("|", "｜")))
    out += ["", "### 채운 지시서 항목", ""]
    if name == "md1":
        out += ["- 9-2 1(제7-5조 문구가 처음 든 개정일·시행일): 수집 때 글 그대로 맞음. 127판 전수 대조로 이분 탐색의 단조 가정 없이 다시 확인(6-1).",
                "- 9-2 2(제5-6조의2·[별표 37] 신설일·개정 연혁·부칙 유예·적용례, 2026.6.29 부칙 제3조): 수집 때 글 그대로 맞음. 세칙 순번 182(2200000108867)를 받아 [별표 37]·제5-6조의2 의 신설 뒤 연혁 구간을 닫음(6-4).",
                "- 9-2 4(보도자료): 이 파일 몫이 아님 — `9-2-4_ORSA_보도자료.md`. 다만 2016.4.1 개정 취지 한 단락을 그 원본 글과 대조해 6-5 에 옮김.",
                "- 모범규준 조 번호: 2·3·6절 자료 묶음마다 「- 모범규준 조」 줄(전부 판단, 조목록 2016.8.1 판 제목과 대조)."]
    else:
        out += ["- 9-2 3([별표 37] 1.~20. 대조·빠진 번호): 수집 때 글 그대로 맞음(세 원본 모두 1.~21., 빠진 번호 없음 — 재계산).",
                "- 9-2 5([별표 22] 위험 분류·하위 위험): 수집 때 글 그대로 맞음. 신용·운영위험액의 측정 대상 「구분」 줄과 [별표 22-1] 「하위위험」 정의를 5-2·5-3 에 채움.",
                "- 모범규준 조 번호: 1·2·5절 자료 묶음마다 「- 모범규준 조」 줄(전부 판단, 조목록 2016.8.1 판 제목과 대조)."]
    out += ["", "### 「추출 범위에 없음」 반박 시도", "", "| 주장(수집 때) | 다시 찾은 곳·검색어 | 결과 |", "|---|---|---|"]
    if name == "md1":
        v56 = S["세칙|제5-6조의2"]
        out += ["| 표기만 바뀐 경계의 정확한 판 | 법제처 lawService.do admrul ID=<일련번호> — 감독규정 연혁 목록 127판 전부, 세칙 %d판 | 성공(제7-5조) · 일부(세칙 — 받지 않은 순번 %s) |" % (
                    v56["받은판수"], v56["받지않은순번"]),
                "| 받지 않은 사이 판의 제7-5조·제5-6조의2 글 | 같음 | 성공(제7-5조 전부) · 일부(세칙) |",
                "| 개정 이유(제·개정 이유서) | 받은 XML %d개의 요소 이름 전수 — 검색어 「이유」「취지」「사유」「제개정이유」「개정이유」「제정이유」; 9-2-4 산출물의 2016.3.30 보도자료 원본 글 | "
                "성공(2022.12.22 판 <제개정이유>) · 일부(2016.4.1 판은 보도자료 취지 단락) · 실패(2016.4.1·2016.7.28 판과 세칙 판의 XML 제개정이유 — 요소 없음) |" % (
                    srch["개정이유_XML요소"]["XML수"])]
    else:
        out += ["| PDF 에만 있는 [별표 37] 글 | pypdf %s 재추출 10쪽·/Annots·/AcroForm·그림 XObject 2개 화소 | 실패(추출 범위에 없음 유지) |" % srch["별표37_PDF"]["pypdf"],
                "| [별표 22] 신용·운영리스크의 「하위위험」 이름 | 정의 (4)(5)·Ⅳ 제5·6장, [별표 22] 전체, [별표 22-1] — 검색어 %s | 실패(「하위위험」 낱말 0곳) · 관련 「구분」 줄과 [별표 22-1] 정의는 채움(5-2·5-3) |" % (
                    " ".join("`%s`" % t for t in SUB_TERMS))]
    out += ["", "### 판 범위 재확인(이분 탐색이 덮은 판)", ""]
    if name == "md1":
        for key in ("감독규정|제7-5조", "세칙|제5-6조의2", "세칙|[별표 37]"):
            v = S[key]
            out.append("- %s: 수집 때 이분 탐색은 연혁 목록(이름 필터) %d판 전체를 범위로 잡았다(처음·끝 판 받음). 검증 뒤 받은 판 %d · 받지 않은 순번 %s · 판정 차례 %s(%s) · 처음 Y 판 %s(앞 받은 판과 %s)." % (
                key, v["목록판수"], v["받은판수"], v["받지않은순번"] or "없음", runs(v), "단조" if v["단조"] else "단조 아님 — 6-1 note",
                _fmt(v["처음Y"]["발령일자"]), "인접" if v["처음Y_경계인접"] else "인접 아님"))
        out.append("- 빠졌던 판: 같은 행정규칙ID 의 옛 이름 판 %d개(1998.04.01~2000.09.05)는 이분 탐색 범위 밖이었다 — 검증에서 모두 받아 문구·조·별표가 없음을 확인(6-2)." % len(S["옛이름판"]))
    else:
        out.append("- 이 파일은 현행 판(2200000108939) 하나만 쓴다 — 연혁 판 범위는 9-2-1_2_ORSA_연혁.md 6절.")
    out += ["", "### 남은 문제", ""]
    out += ["- 검증 스크립트 문제: %d건%s" % (len(probs), "" if not probs else " — " + "; ".join(p[:120] for p in probs[:5]))]
    if name == "md1":
        out += ["- 세칙 큰 판(2020.10 뒤, 4~5MB) 가운데 받지 않은 판의 글은 여전히 추출 범위에 없음(6-1 note).",
                "- 관보·금융위원회 고시 원본(PDF/HWP)과의 대조는 하지 않았다(수집 때 한계 ④ 그대로).",
                "- 2016.3.30 보도자료의 「세칙(3.30일 확정)」과 법제처 세칙 2016.04.28 판의 관계는 판단 보류(6-5)."]
    else:
        out += ["- [별표 22] 는 XML 별표내용만 봤다(별표 HWP·PDF 대조 안 함 — 수집 때 한계 ② 그대로).",
                "- 신용·운영리스크의 「하위위험」 이름은 추출 범위에 없음(5-2·5-3 의 검색어로도 찾지 못함)."]
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "fetch":
        fetch()
    elif cmd == "scan":
        scan()
    elif cmd == "search":
        search()
    elif cmd == "fix":
        fix()
    elif cmd == "check":
        main_check()
    else:
        raise SystemExit("미구현: " + cmd)
