# -*- coding: utf-8 -*-
"""9·10차 법령원문의 저용량 텍스트본 — Claude 프로젝트 참고 파일용(2026-10-02 사용자 요청).

    python3 scripts/dart/law_compact.py recheck   # 수집한 법령마다 오늘 현행 판을 다시 확인(바뀌었으면 새 판 XML 을 받음)
    python3 scripts/dart/law_compact.py compact   # handoff/법령원문_저용량/*.txt + 00_목록.txt
    python3 scripts/dart/law_compact.py check     # 다시 쓰지 않고 대조만

범위(사용자 선택 「9·10차 + 외감법」): dart_out/risk9/법령원문_9차.csv · dart_out/risk10/법령원문_10차.csv 의 현행 판
(법률·시행령·행정규칙) + 보험업감독업무시행세칙 [별표 37](10차 hwp 텍스트). 감독규정 7차 판·시행예정 판은 넣지 않는다.
줄이는 방식(사용자 선택 「연혁 표지·지난 부칙 제외」):
  · 조문 글은 그대로 — 조문내용·항·호·목을 한 줄씩, 줄 앞뒤 공백·빈 줄·연속 공백만 정리
  · 연혁 표지 삭제: <개정 …>·<신설 …>·<전문개정 …>·[본조신설 …]·[제목개정 …]·[종전 …]·(개정 …)·(신설 …)·삭제 뒤 <날짜>
    (「[시행일: …]」 같은 시행일 표지는 남긴다)
  · 부칙: 그 판의 부칙(공포·발령일이 가장 늦은 것)만 남기고 지난 부칙은 뺀다 — 전부는 원래 md 에 있다
  · 별표·서식은 제목 목록만(원래 md 와 같음)
형식: UTF-8(BOM 없음)·LF 의 .txt — PDF 가 아니라 Claude 가 바로 읽는 가장 작은 꼴. 머리 2줄에 법령명·판·출처·생략 내용.
검증: 원문 XML 의 조문 글에서 연혁 표지만 뺀 것이 저용량본에 공백 무시로 그대로 들어 있는지 조문마다 대조한다.
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
import web10_law as L  # noqa: E402
from web10 import save, now, write_csv  # noqa: E402

LIST9 = os.path.join("dart_out", "risk9", "법령원문_9차.csv")
LIST10 = L.LIST_CSV
LIST11 = os.path.join("dart_out", "risk11", "법령원문_11차.csv")        # 2026-10-02 11차 7-1·7-3
RECHECK = os.path.join(L.WORK, "법령_현행재확인.csv")
OUTDIR = os.path.join("handoff", "법령원문_저용량")
SHORT = {  # 파일 이름(짧게)
    "금융산업의 구조개선에 관한 법률": "금산법", "금융산업의 구조개선에 관한 법률 시행령": "금산법시행령",
    "금융지주회사감독규정": "금융지주회사감독규정", "독점규제 및 공정거래에 관한 법률": "공정거래법",
    "독점규제 및 공정거래에 관한 법률 시행령": "공정거래법시행령", "금융회사의 지배구조에 관한 법률": "지배구조법",
    "금융회사의 지배구조에 관한 법률 시행령": "지배구조법시행령", "보험업법": "보험업법",
    "주식회사 등의 외부감사에 관한 법률": "외감법", "주식회사 등의 외부감사에 관한 법률 시행령": "외감법시행령",
    "금융회사 지배구조 감독규정": "금융회사지배구조감독규정", "보험업감독규정": "보험업감독규정",
    "보험업감독업무시행세칙": "보험업감독업무시행세칙",
    # 11차
    "외부감사 및 회계 등에 관한 규정": "외부감사및회계등에관한규정", "금융복합기업집단의 감독에 관한 법률": "금융복합기업집단법",
    "금융지주회사법": "금융지주회사법", "금융지주회사법 시행령": "금융지주회사법시행령",
    "금융지주회사감독규정시행세칙": "금융지주회사감독규정시행세칙", "보험업법 시행령": "보험업법시행령",
    "은행법 시행령": "은행법시행령", "은행법": "은행법",
}
KIND = {"법률": "law", "시행령": "decree", "행정규칙": "rule", "법령(시행령)": "decree"}
LABEL = {"법령(시행령)": "시행령"}


def entries():
    """[(차수, 목록 행)] — 9·10·11차 목록의 현행 판(법률·시행령·행정규칙)만(별표 행·시행예정·7차 판 제외)."""
    out = []
    for tag, path in (("9차", LIST9), ("10차", LIST10), ("11차", LIST11)):
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8-sig")):
            if r["상태"] == "OK" and r["kind"] in KIND:
                out.append((tag, r))
    return out


# ── recheck ───────────────────────────────────────────────────────────────
def recheck():
    import resolve
    client = L._client()
    rows, cache = [], {}
    for tag, r in entries():
        name, kind = r["name"], KIND[r["kind"]]
        rec = dict(name=name, kind=r["kind"], 차수=tag, 수집_일련번호=r["일련번호"], 수집_시행일자=r["시행일자"],
                   오늘_일련번호="", 오늘_시행일자="", 같은판="", 새판XML="", 새판_sha256="", 출처URL="",
                   checked_at=now(), note="")
        try:
            if kind == "rule":
                cur, st, how, cands = resolve.resolve_rule(client, name)
                if not cur:
                    raise RuntimeError("현행 판을 하나로 못 정함(%s): %s" % (st, cands[:5]))
                sn, ef = cur.get("행정규칙일련번호", ""), cur.get("시행일자", "")
            else:
                base = name.replace(" 시행령", "")
                if base not in cache:
                    cache[base] = resolve.resolve_law(client, base)
                res, st, cands = cache[base]
                cur = res.get("법률" if kind == "law" else "시행령", {}).get("현행")
                if not cur:
                    raise RuntimeError("현행을 못 찾음(%s): %s" % (st, cands[:5]))
                sn, ef = cur.get("법령일련번호", ""), cur.get("시행일자", "")
            rec.update(오늘_일련번호=sn, 오늘_시행일자=ef)
            same = (sn, ef) == (r["일련번호"], r["시행일자"])
            rec["같은판"] = "Y" if same else "N"
            if not same:
                if kind == "rule":
                    sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
                else:
                    sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=sn, efYd=ef, type="XML")
                if client.count_oc(xb):
                    raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
                p, m = save("law", "%s_%s_현행재확인%s.xml" % (name.replace(" ", ""), sn, ef), xb,
                            dict(출처URL=murl, http_status=sc, fetched_at=now()))
                rec.update(새판XML=p, 새판_sha256=m["sha256"], 출처URL=murl,
                           note="수집 뒤 현행 판이 바뀜(수집 %s·시행 %s → 오늘 %s·시행 %s) — 저용량본은 오늘 현행 판으로"
                           % (r["일련번호"], r["시행일자"], sn, ef))
        except Exception as e:                       # noqa: BLE001
            rec["note"] = client.mask("확인 실패 %s: %s" % (type(e).__name__, e))[:300]
        print("  %-30s %s %s→%s %s" % (name, rec["같은판"] or "?", r["일련번호"], rec["오늘_일련번호"], rec["note"][:50]))
        rows.append(rec)
    write_csv(RECHECK, list(rows[0].keys()), rows)
    print("현행 재확인 %d건 · 바뀐 판 %d · 실패 %d · API 호출 %d" % (
        len(rows), sum(x["같은판"] == "N" for x in rows), sum(not x["같은판"] for x in rows), client.n_calls))


# ── compact ───────────────────────────────────────────────────────────────
HIST = re.compile(
    r"\s*[<\[(]\s*(?:개정|신설|전문개정|본조신설|제목개정|조번호개정|본조개정|타법개정|항번호개정|호번호개정|목번호개정)"
    r"(?:\s*[\d.,·\s]+|\s*(?:개정|신설))*\s*[>\])]"
    r"|\s*\[종전[^\]]*\]"
    r"|(?<=삭제)\s*[<(]\s*\d{4}\s*\.\s*\d{1,2}\s*\.\s*\d{1,2}\s*\.?\s*[>)]"
    r"|(?<=삭제>)\s*\(\s*\d{4}\s*\.\s*\d{1,2}\s*\.\s*\d{1,2}\s*\.?\s*\)")
REMOVED = []                                     # 지운 표지 기록(검토용)


def _rm(m):
    REMOVED.append(m.group(0).strip())
    return ""


def strip_hist(t, log=False):
    return HIST.sub(_rm, t) if log else HIST.sub("", t)


def tidy(lines):
    out = []
    for l in lines:
        l = re.sub(r"[ \t　]+", " ", strip_hist(l, log=True)).strip()
        if l:
            out.append(l)
    return out


def units_text(xb, kind):
    """[(조문표지, 글 줄들)] — 조문 글(원문 그대로, 줄 단위)."""
    if kind == "rule":
        return [(lab, t.split("\n")) for lab, _, t in L.rule_articles(xb)]
    return [(lab, L.article_text(u).split("\n")) for lab, _, u in L.law_units(xb)]


def last_buchik(xb, kind):
    """그 판의 부칙 = 공포(발령)일자가 가장 늦은 부칙(같은 날 여럿이면 모두). → (일자, [글], 전체 부칙 수)."""
    root = ET.fromstring(xb)
    items = []
    if kind == "rule":
        for b in root.iter("부칙"):
            kids = list(b)
            for i, c in enumerate(kids):
                if c.tag == "부칙공포일자":
                    body = next((k for k in kids[i + 1:i + 3] if k.tag == "부칙내용"), None)
                    items.append(((c.text or "").strip(), "".join(body.itertext()) if body is not None else ""))
    else:
        for u in root.iter("부칙단위"):
            items.append(((u.findtext("부칙공포일자") or "").strip(), "".join(u.find("부칙내용").itertext())
                          if u.find("부칙내용") is not None else ""))
    if not items:
        return "", [], 0
    last = max(d for d, _ in items)
    return last, [t for d, t in items if d == last], len(items)


def annex_titles(xb):
    root = ET.fromstring(xb)
    return ["".join(e.itertext()).strip() for e in root.iter("별표제목") if "".join(e.itertext()).strip()]


ANNEX45_MD = os.path.join("handoff", "법령원문_11차", "금융지주회사법시행령_별표4·5.md")
BOX = re.compile(r"[\u2500-\u257f]")


def annex_body(xb, no):
    root = ET.fromstring(xb)
    u = next((b for b in root.iter("별표단위") if (b.findtext("별표번호") or "").strip() == no
              and (b.findtext("별표가지번호") or "").strip() in ("", "00") and (b.findtext("별표구분") or "").strip() == "별표"),
             None)
    return ((u.findtext("별표제목") or "").strip(), u.findtext("별표내용") or "") if u is not None else ("", "")


def annex45(dec):
    """별표 4·5 저용량본: 테두리만 있는 줄(─┌┐ 등과 공백뿐)은 빼고, 칸 구분 │ 은 남기고, 공백만 정리. 글자는 그대로."""
    xb = open(dec["원문XML"], "rb").read()
    body, orig = [], []
    for no in ("0004", "0005"):
        title, t = annex_body(xb, no)
        orig.append(t)
        body.append("[별표 %d] %s" % (int(no), title))
        for l in t.split("\n"):
            if not re.sub(r"[\s\u2500-\u257f]", "", l):
                continue
            l = re.sub(r"[ \t\u3000]+", " ", l).strip()
            if l:
                body.append(l)
    head = ["금융지주회사법 시행령 [별표 4]·[별표 5] | 시행령 일련번호 %s | 시행 %s | 출처 국가법령정보센터 Open API(law.go.kr) | 확인 %s"
            % (dec["일련번호"], dec["시행일자"], dec["collected_at"][:10]),
            "저용량본: 표 테두리만 있는 줄 생략, 칸 구분 │ 은 남김, 공백 정리. 글자는 그대로. 전체: %s" % ANNEX45_MD]
    text = "\n".join(head + ["---"] + body) + "\n"
    fn = "금융지주회사법시행령_별표4·5.txt"
    with open(os.path.join(OUTDIR, fn), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    strip = lambda x: BOX.sub("", re.sub(r"\s+", "", x))  # noqa: E731
    ok = all(t.strip() and strip(t) in strip(text) for t in orig)          # 별표마다 따로
    return fn, text, ok


def compact():
    rc = {(r["name"], r["kind"]): r for r in csv.DictReader(open(RECHECK, encoding="utf-8-sig"))} \
        if os.path.exists(RECHECK) else {}
    os.makedirs(OUTDIR, exist_ok=True)
    index, checks = [], []
    seen = set()
    for tag, r in entries():
        name, kind = r["name"], KIND[r["kind"]]
        if name in seen:
            raise SystemExit("같은 법령이 9·10차에 둘 다 있음: %s" % name)
        seen.add(name)
        re_ = rc.get((name, r["kind"]), {})
        if re_.get("같은판") == "N" and re_.get("새판XML"):
            xml_path, sn, ef, src = re_["새판XML"], re_["오늘_일련번호"], re_["오늘_시행일자"], re_["출처URL"]
            when = re_["checked_at"]
            full = "원래 md(%s, 일련번호 %s)는 수집일 판 — 이 파일은 %s 현행 재확인 판" % (r["텍스트"], r["일련번호"], when[:10])
        else:
            xml_path, sn, ef, src, when = r["원문XML"], r["일련번호"], r["시행일자"], r["출처URL"], r["collected_at"]
            full = "전체(연혁 표지·모든 부칙 포함): %s" % r["텍스트"]
        xb = open(xml_path, "rb").read()
        sha = hashlib.sha256(xb).hexdigest()
        units = units_text(xb, kind)
        body = []
        for lab, lines in units:
            body += tidy(lines)
        bdate, btexts, bn = last_buchik(xb, kind)
        tail = []
        if btexts:
            tail.append("[부칙 — 이 판의 부칙만(%s), 지난 부칙 %d개 생략]" % (bdate, bn - len(btexts)))
            for t in btexts:
                tail += tidy(t.split("\n"))
        at = annex_titles(xb)
        if at:
            tail.append("[별표·서식 제목]")
            tail += tidy(at)
        head = ["%s | %s | 일련번호 %s | 시행 %s | 출처 국가법령정보센터 Open API(law.go.kr) | 확인 %s"
                % (name, LABEL.get(r["kind"], r["kind"]), sn, ef, (when or "")[:10]),
                "저용량본: 연혁 표지(<개정…>·[본조신설…] 등)·지난 부칙 생략, 공백 정리. 조문 글은 그대로. %s" % full]
        text = "\n".join(head + ["---"] + body + tail) + "\n"
        fn = "%s.txt" % SHORT.get(name, name.replace(" ", ""))
        with open(os.path.join(OUTDIR, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        # 검증: 조문마다 「연혁 표지만 뺀 원문 글」이 저용량본에 공백 무시로 그대로
        flat = re.sub(r"\s+", "", text)
        bad = [lab for lab, lines in units if re.sub(r"\s+", "", strip_hist("\n".join(lines))) not in flat]
        checks.append((fn, len(units), bad))
        index.append(dict(파일=fn, 법령명=name, 종류=LABEL.get(r["kind"], r["kind"]), 일련번호=sn, 시행일자=ef, 차수=tag,
                          바이트=len(text.encode("utf-8")), 원래_md_바이트=os.path.getsize(r["텍스트"]) if r["텍스트"] else 0,
                          조문수=len(units), 원문XML_sha256=sha, 출처URL=src, 확인일=(when or "")[:10],
                          비고=re_.get("note", "") if re_.get("같은판") == "N" else ""))
    # 별표 37(10차 hwp 텍스트) — 세칙 XML 의 별표내용과 별개 원본이라 따로 한 파일
    md = open(L.A37_MD, encoding="utf-8").read()
    a37 = md.split("\n## 원문\n", 1)[1].split("\n")
    buch = [r for r in csv.DictReader(open(L.A37_CSV, encoding="utf-8-sig")) if r["위치"].startswith("세칙 부칙")]
    head = ["보험업감독업무시행세칙 [별표 37] 자체 위험 및 지급여력평가체제 구축·운용 및 점검 기준 | 신설 2026.6.29. | "
            "출처 국가법령정보센터 별표 파일(hwp→hwp2md) | 확인 %s" % now()[:10],
            "저용량본: 공백·빈 줄 정리, 글은 그대로. 끝에 이 별표를 언급한 세칙 부칙 조. 전체: %s" % L.A37_MD]
    tail = ["[세칙 부칙 중 별표37·제5-6조의2 관련 조]"]
    for b in buch:
        tail.append(b["위치"].replace("세칙 ", ""))
        tail += tidy(b["source_text"].split("\n"))
    text = "\n".join(head + ["---"] + tidy(a37) + tail) + "\n"
    fn = "보험업감독업무시행세칙_별표37.txt"
    with open(os.path.join(OUTDIR, fn), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    ok37 = re.sub(r"\s+", "", strip_hist("\n".join(a37))) in re.sub(r"\s+", "", text)
    checks.append((fn, 1, [] if ok37 else ["별표37"]))
    index.append(dict(파일=fn, 법령명="보험업감독업무시행세칙 [별표 37]", 종류="행정규칙 별표", 일련번호="2200000108939(세칙)",
                      시행일자="20260910(세칙)", 차수="10차", 바이트=len(text.encode("utf-8")),
                      원래_md_바이트=os.path.getsize(L.A37_MD), 조문수="", 원문XML_sha256="", 출처URL="별표 hwp: "
                      "https://www.law.go.kr/LSW/flDownload.do?flSeq=168886111", 확인일=now()[:10], 비고=""))
    # 금융지주회사법 시행령 별표 4·5(11차) — 원문 XML 별표내용
    if os.path.exists(LIST11):
        r11 = {r["name"]: r for r in csv.DictReader(open(LIST11, encoding="utf-8-sig"))}
        dec = r11.get("금융지주회사법 시행령")
        if dec and dec["상태"] == "OK":
            fn, text, ok45 = annex45(dec)
            checks.append((fn, 2, [] if ok45 else ["별표4·5"]))
            index.append(dict(파일=fn, 법령명="금융지주회사법 시행령 [별표 4]·[별표 5]", 종류="시행령 별표", 일련번호=dec["일련번호"],
                              시행일자=dec["시행일자"], 차수="11차", 바이트=len(text.encode("utf-8")),
                              원래_md_바이트=os.path.getsize(ANNEX45_MD) if os.path.exists(ANNEX45_MD) else 0, 조문수="",
                              원문XML_sha256=dec["xml_sha256"], 출처URL=dec["출처URL"], 확인일=dec["collected_at"][:10], 비고=""))
    # 목록 파일
    lines = ["법령원문 저용량본 목록 | 만든 날 %s | UTF-8 텍스트, 법령마다 한 파일" % now()[:10],
             "줄인 것: 연혁 표지(<개정…>·<신설…>·[본조신설…]·(개정 …) 등)와 지난 부칙(그 판 부칙만 남김), 줄 앞뒤 공백·빈 줄. "
             "조문 글자는 그대로. 별표·서식은 제목만(별표37 은 따로 본문). 연혁·부칙 전체는 저장소 handoff/법령원문_9차·10차 md.",
             "파일 | 법령명 | 종류 | 일련번호 | 시행일 | 크기(바이트, 원래 md 대비)"]
    for x in index:
        lines.append("%s | %s | %s | %s | %s | %d (%s)" % (
            x["파일"], x["법령명"], x["종류"], x["일련번호"], x["시행일자"], x["바이트"],
            "%.0f%%" % (100.0 * x["바이트"] / x["원래_md_바이트"]) if x["원래_md_바이트"] else "-")
            + (" — " + x["비고"] if x["비고"] else ""))
    lines.append("넣지 않은 것: 금융지주회사감독규정 7차 판(2100000266376, 2026-10-02 부터 지난 판)·시행예정 판(공정거래법 4·보험업법 1, "
                 "원본 XML 만 보관; 보험업법 시행령 285553(시행 2027-01-01)은 일련번호·시행일만 기록).")
    with open(os.path.join(OUTDIR, "00_목록.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    write_csv(os.path.join(L.WORK, "법령원문_저용량_목록.csv"), list(index[0].keys()), index)
    from collections import Counter
    kinds = Counter(re.sub(r"\d+", "0", re.sub(r"\s+", "", x)) for x in REMOVED)
    write_csv(os.path.join(L.WORK, "법령원문_저용량_지운표지.csv"), ["꼴(숫자→0)", "건수", "예"],
              [{"꼴(숫자→0)": k, "건수": v, "예": next(x for x in REMOVED
                                                    if re.sub(r"\d+", "0", re.sub(r"\s+", "", x)) == k)}
               for k, v in kinds.most_common()])
    print("지운 연혁 표지 %d개(꼴 %d가지) → dart_out/risk10/법령원문_저용량_지운표지.csv" % (len(REMOVED), len(kinds)))
    tot = sum(x["바이트"] for x in index)
    orig = sum(x["원래_md_바이트"] for x in index)
    for fn, n, bad in checks:
        print("  %-36s 조문 %4s  대조 %s" % (fn, n, "OK" if not bad else "불일치 %d: %s" % (len(bad), bad[:5])))
    print("저용량본 %d개 파일 · %d바이트 (원래 md %d바이트의 %.1f%%) · 대조 불일치 %d" % (
        len(index), tot, orig, 100.0 * tot / orig, sum(len(b) for _, _, b in checks)))
    return 0 if not any(b for _, _, b in checks) else 1


def source_of(r, rc):
    """저용량본을 만든 원문 XML 경로 — 오늘 현행이 바뀐 법령은 재확인 판."""
    re_ = rc.get((r["name"], r["kind"]), {})
    return re_["새판XML"] if re_.get("같은판") == "N" and re_.get("새판XML") else r["원문XML"]


def check():
    """파일을 다시 쓰지 않고 대조만: 법령마다 저용량본이 있고, 조문마다 연혁 표지만 뺀 원문 글이 공백 무시로 그대로 있는가.
    → (파일 수, [문제])"""
    rc = {(r["name"], r["kind"]): r for r in csv.DictReader(open(RECHECK, encoding="utf-8-sig"))} \
        if os.path.exists(RECHECK) else {}
    probs, n = [], 0
    for tag, r in entries():
        fn = os.path.join(OUTDIR, "%s.txt" % SHORT.get(r["name"], r["name"].replace(" ", "")))
        if not os.path.exists(fn):
            probs.append("없음 " + fn)
            continue
        n += 1
        raw = open(fn, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw:
            probs.append("BOM·CRLF " + fn)
        flat = re.sub(r"\s+", "", raw.decode("utf-8"))
        xb = open(source_of(r, rc), "rb").read()
        for lab, lines in units_text(xb, KIND[r["kind"]]):
            if re.sub(r"\s+", "", strip_hist("\n".join(lines))) not in flat:
                probs.append("조문 불일치 %s %s" % (fn, lab))
    if os.path.exists(LIST11):
        dec = {r["name"]: r for r in csv.DictReader(open(LIST11, encoding="utf-8-sig"))}.get("금융지주회사법 시행령")
        fn = os.path.join(OUTDIR, "금융지주회사법시행령_별표4·5.txt")
        if dec and dec["상태"] == "OK":
            if not os.path.exists(fn):
                probs.append("없음 " + fn)
            else:
                xb = open(dec["원문XML"], "rb").read()
                strip = lambda x: BOX.sub("", re.sub(r"\s+", "", x))  # noqa: E731
                got = strip(open(fn, encoding="utf-8").read())
                for no in ("0004", "0005"):
                    src = annex_body(xb, no)[1]
                    if not src.strip() or strip(src) not in got:
                        probs.append("별표 %d 불일치 %s" % (int(no), fn))
                n += 1
    return n, probs


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "recheck":
        recheck()
    elif cmd == "compact":
        sys.exit(compact())
    elif cmd == "check":
        n, probs = check()
        print("저용량본 %d개 대조 · 문제 %d" % (n, len(probs)), *probs[:20], sep="\n")
        sys.exit(1 if probs else 0)
    else:
        print(__doc__)
