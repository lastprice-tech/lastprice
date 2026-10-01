# -*- coding: utf-8 -*-
"""10차 6-1·6-2 법령 원문과 6-4 게시처 합치기. 실행은 web10.py 의 하위 명령으로.

6-1 laws : 국가법령정보센터 Open API(9차 web9.laws 와 같은 방식 — 7차 lawclient·resolve·render)로
           금산법·같은 법 시행령(현행)과 금융지주회사감독규정(현행, 인용 조항 확인용),
           6-6 공정거래법·같은 법 시행령(현행)을 받는다.
           원본 XML·렌더링 PDF → dart_out/raw/web10/law/, 텍스트 → handoff/법령원문_10차/*.md,
           목록 → dart_out/risk10/법령원문_10차.csv
6-1 cite : 받은 XML 만 읽어(추가 요청 없음) 금산법_확인.csv · 금산법_인용대조.csv 를 만든다.
6-2 annex37 : 9차에 받은 보험업감독업무시행세칙 현행 XML 의 별표37 링크(별표서식파일링크=hwp,
           별표서식PDF파일링크=pdf)로 원본을 받아 hwp 는 hwp2md.py, pdf 는 pypdf 로 텍스트화.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
from web10 import RAW, WORK, OUT, LAWOUT, save, now, write_csv  # noqa: E402

LAWDIR = os.path.join(RAW, "law")
LEDGER = os.path.join(LAWDIR, "_call_log.csv")
GEUMSAN = "금융산업의 구조개선에 관한 법률"
FHC_RULE = "금융지주회사감독규정"
# (요청명, 종류, md 파일 이름)
FTC = "독점규제 및 공정거래에 관한 법률"
LAWS = [
    (GEUMSAN, "law", "금산법.md"),
    (GEUMSAN + " 시행령", "decree", "금산법시행령.md"),
    (FHC_RULE, "rule", "금융지주회사감독규정.md"),
    (FTC, "law", "공정거래법.md"),                       # 6-6
    (FTC + " 시행령", "decree", "공정거래법시행령.md"),
    # 6-6 연결 조문(지배구조법 시행령 §3①2호 나목 → 공정거래법 계열회사, 보험업법 §106①·§111) 확인용
    ("금융회사의 지배구조에 관한 법률", "law", "지배구조법.md"),
    ("금융회사의 지배구조에 관한 법률 시행령", "decree", "지배구조법시행령.md"),
    ("보험업법", "law", "보험업법.md"),
]
LIST_CSV = os.path.join(WORK, "법령원문_10차.csv")
LAW7 = os.path.join("law_archive", "00_manifest", "law_list.csv")


def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


# ── 조문 구조 ─────────────────────────────────────────────────────────────
def _t(e, tag):
    return (e.findtext(tag) or "").strip()


def jo_label(u):
    """조문단위 → 「제9조의2」. 조문여부가 「전문」(장·절 표제)이면 빈칸."""
    if _t(u, "조문여부") and _t(u, "조문여부") != "조문":
        return ""
    n, g = _t(u, "조문번호"), _t(u, "조문가지번호")
    return "제%s조%s" % (n, "의%s" % g if g and g != "0" else "") if n else ""


def article_text(u):
    """조문 하나의 글을 문서 순서대로(조문내용·항내용·호내용·목내용). 글자는 그대로, 요소마다 줄바꿈."""
    out = []
    for e in u.iter():
        if e.tag in ("조문내용", "항내용", "호내용", "목내용"):
            t = "".join(e.itertext()).strip()
            if t:
                out.append(t)
    return "\n".join(out)


def law_units(xb):
    """[(조문표지, 조문제목, 조문단위 element)] — 법령(eflaw) XML."""
    root = ET.fromstring(xb)
    return [(jo_label(u), _t(u, "조문제목"), u) for u in root.iter("조문단위")]


def rule_articles(xb):
    """행정규칙 XML 은 조문내용 하나에 조 전체가 들어 있다 → [(조문표지, 제목, 글)]."""
    root = ET.fromstring(xb)
    out = []
    for e in root.iter("조문내용"):
        t = "".join(e.itertext()).strip()
        m = re.match(r"(제\d+조(?:의\d+)?)\s*(?:\(([^)]*)\))?", t)
        out.append((m.group(1) if m else "", (m.group(2) or "") if m else "", t))
    return out


def md_text(xb, kind):
    """md 본문: 법령은 조문단위마다(조문·항·호·목 줄바꿈), 행정규칙은 조문내용 그대로. 부칙·별표제목 뒤에."""
    root = ET.fromstring(xb)
    parts = []
    if kind == "rule":
        parts += [t for _, _, t in rule_articles(xb)]
    else:
        parts += [article_text(u) for _, _, u in law_units(xb)]
    for tag in ("부칙내용", "별표제목"):
        for e in root.iter(tag):
            t = "".join(e.itertext()).strip()
            if t:
                parts.append(t)
    return "\n\n".join(p for p in parts if p)


# ── 6-1 laws ──────────────────────────────────────────────────────────────
def laws():
    import render
    import resolve
    client = _client()
    prev = {r["정식명"]: r for r in csv.DictReader(open(LAW7, encoding="utf-8-sig"))} if os.path.exists(LAW7) else {}
    rows = []
    resolved = {}
    for name, kind, mdname in LAWS:
        rec = dict(name=name, kind={"law": "법률", "decree": "시행령", "rule": "행정규칙"}[kind], 상태="",
                   법령ID="", 일련번호="", 시행일자="", 발령_공포일자="", 소관="", 시행예정판="",
                   원문XML="", xml_sha256="", 텍스트="", 텍스트_sha256="", PDF="", pdf_sha256="", 쪽수="",
                   출처URL="", collected_at="", 차7_일련번호="", 차7_시행일자="", 차7과같은판="", note="")
        try:
            if kind == "rule":
                cur, st, how, cands = resolve.resolve_rule(client, name)
                if not cur:
                    raise RuntimeError("현행 판을 하나로 못 정함(%s): %s" % (st, cands[:5]))
                rec.update(법령ID=cur.get("행정규칙ID", ""), 일련번호=cur.get("행정규칙일련번호", ""),
                           시행일자=cur.get("시행일자", ""), 발령_공포일자=cur.get("발령일자", ""),
                           소관=cur.get("소관부처명", ""))
                sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=rec["일련번호"], type="XML")
            else:
                base = name.replace(" 시행령", "")
                if base not in resolved:
                    resolved[base] = resolve.resolve_law(client, base)
                res, st, cands = resolved[base]
                tier = "법률" if kind == "law" else "시행령"
                cur = res.get(tier, {}).get("현행")
                if not cur:
                    raise RuntimeError("현행 %s 을 못 찾음(%s): %s" % (tier, st, cands[:5]))
                pend = res.get(tier, {}).get("시행예정") or []
                rec["시행예정판"] = " ; ".join("%s(시행 %s)" % (p.get("법령일련번호", ""), p.get("시행일자", ""))
                                           for p in pend) or "없음"
                rec.update(법령ID=cur.get("법령ID", ""), 일련번호=cur.get("법령일련번호", ""),
                           시행일자=cur.get("시행일자", ""), 발령_공포일자=cur.get("공포일자", ""),
                           소관=cur.get("소관부처명", ""))
                sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=rec["일련번호"],
                                                efYd=rec["시행일자"], type="XML")
            if client.count_oc(xb):
                raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
            stem = "%s_%s" % (name.replace(" ", ""), rec["일련번호"])
            p, m = save("law", stem + ".xml", xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            rec.update(원문XML=p, xml_sha256=m["sha256"], 출처URL=murl, collected_at=m["fetched_at"])
            md = ["# %s" % name, "",
                  "- 종류: %s · 일련번호 %s · 시행일자 %s · 발령/공포일자 %s · 소관 %s"
                  % (rec["kind"], rec["일련번호"], rec["시행일자"], rec["발령_공포일자"], rec["소관"]),
                  "- 출처: 국가법령정보센터 Open API %s (OC=*** 가림) · 수집일 %s" % (murl, rec["collected_at"]),
                  "- 원문 XML sha256 %s — 아래 글은 그 XML 의 %s 글을 문서 순서대로 옮긴 것(글자 수정 없음). "
                  "법령에는 쪽이 없어 위치는 조문 번호로 적는다." % (
                      rec["xml_sha256"], "조문·부칙·별표제목" if kind == "rule" else "조문·항·호·목·부칙·별표제목"),
                  "", "---", "", md_text(xb, kind)]
            os.makedirs(LAWOUT, exist_ok=True)
            mdp = os.path.join(LAWOUT, mdname)
            body = "\n".join(md) + "\n"
            with open(mdp, "w", encoding="utf-8") as f:
                f.write(body)
            rec.update(텍스트=mdp, 텍스트_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest())
            fn = render.admrul_html if kind == "rule" else render.law_html
            html_text, _nm, _labels = fn(xb, rec["시행일자"], rec["일련번호"])
            pdfp = os.path.join(LAWDIR, stem + "_본문.pdf")
            render.html_to_pdf(html_text, pdfp)
            ok, npg, _x = render.pdf_info(pdfp)
            rec.update(PDF=pdfp, pdf_sha256=hashlib.sha256(open(pdfp, "rb").read()).hexdigest(), 쪽수=npg)
            pv = prev.get(name, {})
            rec.update(차7_일련번호=pv.get("법령일련번호", ""), 차7_시행일자=pv.get("시행일자", ""))
            rec["차7과같은판"] = ("Y" if pv and pv.get("법령일련번호") == rec["일련번호"] else
                              "N(7차 이후 바뀐 판)" if pv else "7차 목록에 없음")
            rec["상태"] = "OK"
        except Exception as e:                       # noqa: BLE001 — 사유를 남기고 다음
            rec["상태"] = "실패"
            rec["note"] = client.mask("%s: %s" % (type(e).__name__, e))[:300]
        print("  %-28s %s %s %s %s" % (name, rec["상태"], rec["일련번호"], rec["시행일자"], rec["note"][:80]))
        rows.append(rec)
    # 시행예정 판: 받아 두기만 한다(md 없음). 현행 판과 조문을 대조하는 데 쓴다 — 어느 판이 맞는지 판정하지 않는다.
    for cur in [r for r in rows if r["상태"] == "OK" and r["시행예정판"] not in ("", "없음")]:
        for item in cur["시행예정판"].split(" ; "):
            mm = re.match(r"(\d+)\(시행 (\d+)\)", item)
            rec = dict(cur, kind=cur["kind"] + "(시행예정)", 상태="", 일련번호=mm.group(1), 시행일자=mm.group(2),
                       시행예정판="", 텍스트="", 텍스트_sha256="", PDF="", pdf_sha256="", 쪽수="", note="")
            try:
                sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=rec["일련번호"],
                                                efYd=rec["시행일자"], type="XML")
                if client.count_oc(xb):
                    raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
                p, m = save("law", "%s_%s_시행%s.xml" % (cur["name"].replace(" ", ""), rec["일련번호"], rec["시행일자"]),
                            xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
                rec.update(원문XML=p, xml_sha256=m["sha256"], 출처URL=murl, collected_at=m["fetched_at"], 상태="OK",
                           note="시행예정 판(현행 %s 과 대조용, md 없음)" % cur["일련번호"])
            except Exception as e:                   # noqa: BLE001
                rec.update(상태="실패", note=client.mask("%s: %s" % (type(e).__name__, e))[:300])
            print("  %-28s %s %s %s" % (cur["name"] + "(시행예정)", rec["상태"], rec["일련번호"], rec["시행일자"]))
            rows.append(rec)
    # 감독규정: API 가 「현행」으로 준 판의 시행일이 수집일 뒤면(실측: 발령 2026-09-29·시행 2026-10-02),
    # 수집일에 시행 중인 판(7차 일련번호)도 받아 둔다. 어느 판이 맞는지 판정하지 않고 둘 다 남긴다.
    cur = next(r for r in rows if r["name"] == FHC_RULE)
    pv = prev.get(FHC_RULE, {})
    if cur["상태"] == "OK" and pv and pv.get("법령일련번호") and pv["법령일련번호"] != cur["일련번호"]:
        rec = dict(cur, kind="행정규칙(7차 판)", 상태="", 일련번호=pv["법령일련번호"], 시행일자=pv.get("시행일자", ""),
                   발령_공포일자=pv.get("공포일자", ""), 시행예정판="", note="")
        try:
            sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=rec["일련번호"], type="XML")
            if client.count_oc(xb):
                raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
            stem = "%s_%s" % (FHC_RULE, rec["일련번호"])
            p, m = save("law", stem + ".xml", xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            mdp = os.path.join(LAWOUT, "금융지주회사감독규정_7차판_%s.md" % rec["일련번호"])
            body = "\n".join(["# %s (7차 수집 판)" % FHC_RULE, "",
                              "- 종류: 행정규칙 · 일련번호 %s · 시행일자 %s (7차 law_list.csv 기준)"
                              % (rec["일련번호"], rec["시행일자"]),
                              "- 출처: 국가법령정보센터 Open API %s (OC=*** 가림) · 수집일 %s" % (murl, m["fetched_at"]),
                              "- 원문 XML sha256 %s — 조문·부칙·별표제목 글을 순서대로 옮긴 것(글자 수정 없음)." % m["sha256"],
                              "- API 현행 판(%s, 시행 %s)의 시행일이 수집일 뒤라 함께 받음." % (cur["일련번호"], cur["시행일자"]),
                              "", "---", "", md_text(xb, "rule")]) + "\n"
            with open(mdp, "w", encoding="utf-8") as f:
                f.write(body)
            rec.update(원문XML=p, xml_sha256=m["sha256"], 출처URL=murl, collected_at=m["fetched_at"], 텍스트=mdp,
                       텍스트_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(), PDF="", pdf_sha256="", 쪽수="",
                       차7과같은판="Y", 상태="OK",
                       note="API 현행 판 %s 의 시행일(%s)이 수집일 뒤라 수집일 시행 중인 7차 판도 받음"
                       % (cur["일련번호"], cur["시행일자"]))
        except Exception as e:                       # noqa: BLE001
            rec.update(상태="실패", note=client.mask("%s: %s" % (type(e).__name__, e))[:300])
        print("  %-28s %s %s %s" % (FHC_RULE + "(7차 판)", rec["상태"], rec["일련번호"], rec["note"][:60]))
        rows.append(rec)
    write_csv(LIST_CSV, list(rows[0].keys()), rows)
    print("법령 %d건 · OK %d · API 호출 %d" % (len(rows), sum(r["상태"] == "OK" for r in rows), client.n_calls))


def _listed():
    """이름 → 현행 판 행(시행예정·7차 판 행은 빼고)."""
    return {r["name"]: r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig"))
            if r["kind"] in ("법률", "시행령", "행정규칙")}


# ── 6-1 cite ──────────────────────────────────────────────────────────────
CIRCLED = {c: i + 1 for i, c in enumerate("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳")}
TERMS = ("금융체계상 중요한", "금융체계상중요한", "자체정상화계획", "부실정리계획")
CHECK_CSV = os.path.join(OUT, "금산법_확인.csv")
CITE_CSV = os.path.join(OUT, "금산법_인용대조.csv")
CHECK_COLS = ["구분", "법령", "조문", "조문제목", "포함어", "source_text", "rcept_no_or_url", "doc_name",
              "page", "note", "collected_at", "source_sha256"]
CITE_COLS = ["감독규정_조항", "요청범위", "사용자_표기", "인용표기", "인용상_법령", "법_해당조문", "시행령_해당조문",
             "실제조문", "조문제목", "원문첫문장", "인용단위_source_text", "감독규정_source_text", "7차판과_같음",
             "rcept_no_or_url", "doc_name", "page", "note", "collected_at", "source_sha256"]
# 사용자가 확인을 요청한 인용(작업 6-1) — (감독규정 조항, 사용자 표기)
ASKED = {("제25조의2제6항", "제9조의2"): "§9의2", ("제25조의2제6항", "시행령 제5조의4제2항"): "시행령 §5의4②",
         ("제25조의5제1항", "제5조의5제1항제5호"): "§5의5①5호", ("제25조의5제2항", "제9조의4"): "§9의4"}
# 연차보고서(FY2025, 2026년 공시 본공시) 인용 — 8차 텍스트(dart_out/text/risk8, pypdf 쪽 표지)에서 고른 문장.
AR_QUOTES = [
    ("KB금융지주", 48, "가. 2025년 KB금융지주 자체정상화계획 갱신(안): 「금융산업구조개선법 시행령」에 의거 KB금융지주가 "
     "‘금융 체계상 중요한 금융기관’에 선정됨에 따라 자체정상화계획 작성 및 금융감독원 제출에 관한 이사회 논의 및 결의",
     "선정(「‘금융 체계상 중요한 금융기관’에 선정됨에 따라」)·작성·금융감독원 제출을 함께 적음"),
    ("KB금융지주", 37, "「금융산업의 구조개선에 관한 법률」에 따라 ‘KB금융지주 자체정상화계획 갱신(안)’을 논의 및 결의하였으며, "
     "예금보험공사가 수립한 ‘KB금융지주의 「부실정리계획 실행 시 예상 장애요인 해소 조치」 결과’를 보고하고 금융위에 제출하였습니다.",
     "자체정상화계획 갱신 결의 + 부실정리계획 예상 장애요인 해소 조치 결과 금융위 제출(법 §9의8 관련으로 읽힘 — 판단)"),
    ("신한금융지주", 25, "기타 중요사항으로 2025년 7월 25일 개최한 제3회 정기이사회를 통하여 그룹 자체정상화계획(안)의 방향성을 "
     "보고하였으며, 2025년 9월 26일 제11회 위험관리위원회에서 '그룹 자체정상화계획(안)’을 심의하고, 이어진 제7회 임시이사회에서 "
     "최종 승인한 그룹 자체정상화계획(안)을 금융감독기관에 제출하였습니다.",
     "제출(「금융감독기관에 제출하였습니다」) 명시. 「선정」 낱말은 이 문장에 없음"),
    ("하나금융지주", 64, "나. 2025년 자체정상화계획 정기갱신 : 자체정상화계획 도입 배경, 정기 갱신(안) 주요 내용, 진행 경과, "
     "향후 일정, 수시갱신 사항 등에 대해 심의 후 2025년 자체정상화계획 정기갱신(안)이 가결되었습니다.",
     "정기갱신 가결만 적음 — 「선정」「제출」 낱말은 이 보고서 본문 검색(자체정상화계획·금융체계상 중요한)에서 못 찾음"),
    ("우리금융지주", 23, "또한 리스크관리와 관련한 주요 활동으로 2025년 9월 25일 개최한 제10차 임시이사회에서 ‘2025년 우리금융지주 "
     "자체정상화계획 수립(案)’을 의결하였습니다. 해당 안건은 「금융산업의 구조개선에 관한 법률」 에 의거하여 경영위기 상황 대비 "
     "자구계획을 수립하기 위함이며, 작성 지침에 의거 지배구조 수립, 중요자회사 선정 등 7개 항목에 따라 계획안을 수립하고 "
     "이사회의 승인을 득하여 2025년 10월 금융감독원에 제출하였습니다.",
     "제출(2025년 10월 금융감독원) 명시. 문장 속 「선정」은 「중요자회사 선정」(계획 작성 항목)이지 금융체계상 중요한 금융기관 선정이 아님"),
    ("우리금융지주", 51, "나) <보험사 편입에 따른> 2025년 우리금융지주 자체정상화계획 재수립(案): 그룹 내 보험사 편입에 따라 "
     "9월 그룹BIS비율 기준, 「위기상황분석」 및 「자체정상화수단」을 재작성하여 재수립한 자체정상화계획을 2025.12.22. "
     "금감원에 제출하였습니다.",
     "보험사 편입에 따라 자체정상화계획 재수립·재제출(2025.12.22.) — 보험 자회사가 지주 자체정상화계획 범위에 들어간 사례"),
    ("NH농협금융지주", 45, "(의안 제21호) 농협금융 자체정상화계획(안) : 위기상황 선제적 대응체계 구축을 위한 농협금융 자체정상화계획",
     "의결 안건명만 적음 — 「선정」「제출」 낱말은 이 보고서 본문 검색에서 못 찾음"),
    ("NH농협금융지주", 41, "(보고 제18호) 농협금융 자체정상화계획 심의 결과 : 자체정상화계획의 안정적 운영을 통한 위기상황 선제적 "
     "대응체계 구축을 위한 농협금융 자체정상화계획 결의",
     "보고 안건(심의 결과) — 제출 여부는 적혀 있지 않음"),
]
AR_LIST = os.path.join("handoff", "연차보고서_파일목록.csv")
AR_TEXT = os.path.join("dart_out", "text", "risk8", "연차보고서__%s_지배구조연차보고서_2026%s.txt")


def _nows(s):
    return re.sub(r"\s+", "", s or "")


def _first_sentence(t):
    t = re.sub(r"\s+", " ", t).strip()
    m = re.search(r"^(.*?다\.)(\s|$)", t)
    return m.group(1) if m else t


def _jo_key(label):
    m = re.match(r"제(\d+)조(?:의(\d+))?", label)
    return (m.group(1).lstrip("0"), (m.group(2) or "0").lstrip("0") or "0") if m else None


def find_unit(xb, jo, hang=None, ho=None, mok=None):
    """법령 XML 에서 조(항·호·목). → (조문표지, 조문제목, 단위 글) 또는 None(없음). 글자는 그대로."""
    want = _jo_key(jo)
    root = ET.fromstring(xb)
    for u in root.iter("조문단위"):
        if _t(u, "조문여부") not in ("", "조문"):
            continue
        if (_t(u, "조문번호").lstrip("0"), (_t(u, "조문가지번호") or "0").lstrip("0") or "0") != want:
            continue
        title = _t(u, "조문제목")
        if hang is None and ho is None:
            return jo_label(u), title, article_text(u)
        scope = u
        if hang is not None:
            hs = [h for h in u.findall("항") if CIRCLED.get(_t(h, "항번호")[:1]) == hang]
            if not hs:
                return None
            scope = hs[0]
        if ho is None:
            return jo_label(u), title, article_text(scope)
        hos = [h for h in scope.iter("호") if re.match(r"%d\.$" % ho, _t(h, "호번호"))]
        if not hos:
            return None
        scope = hos[0]
        if mok is None:
            return jo_label(u), title, article_text(scope)
        ms = [m for m in scope.iter("목") if _t(m, "목번호").startswith(mok)]
        return (jo_label(u), title, article_text(ms[0])) if ms else None
    return None


def _parse_ref(ref):
    """「제5조의5제1항제5호」 → (제5조의5, 1, 5, None)."""
    m = re.match(r"(제\d+조(?:의\d+)?)\s*(?:제(\d+)항)?\s*(?:제(\d+)호)?\s*(?:([가-힣])목)?", ref)
    return (m.group(1), int(m.group(2)) if m.group(2) else None, int(m.group(3)) if m.group(3) else None,
            m.group(4)) if m else None


def _loc(jo, hang, ho, mok=None):
    return jo + ("제%d항" % hang if hang else "") + ("제%d호" % ho if ho else "") + ("%s목" % mok if mok else "")


GEUMSAN_RE = (r"(?:「금융산업의\s*구조개선에\s*관한\s*법률\s*」|금융산업의구조개선에관한법률|「금융산업의구조개선에관한법률」)\s*"
              r"(제\d+조(?:의\d+)?(?:\s*제\d+항)?(?:\s*제\s*\d+호)?)"
              r"(?:\s*및\s*같은\s*법\s*시행령\s*(제\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+호)?))?")


def _rule_clauses(text):
    """감독규정 조 글 → [(항번호 or None, 항 글)]. 항 표지 ①… 로 자른다."""
    parts = re.split(r"(?=\s[①-⑳]\s)", " " + text)
    out = []
    for p in parts:
        p = p.strip()
        m = re.match(r"([①-⑳])", p)
        out.append((CIRCLED[m.group(1)] if m else None, p))
    return out


def cite():
    lst = _listed()
    law, dec = lst[GEUMSAN], lst[GEUMSAN + " 시행령"]
    rule = lst[FHC_RULE]
    rule7 = next((r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig"))
                  if r["kind"] == "행정규칙(7차 판)"), None)
    xb_law = open(law["원문XML"], "rb").read()
    xb_dec = open(dec["원문XML"], "rb").read()
    xb_rule = open(rule["원문XML"], "rb").read()
    old = {l: t for l, _, t in rule_articles(open(rule7["원문XML"], "rb").read())} if rule7 and rule7["상태"] == "OK" else {}

    def dname(r):
        return "%s(%s 일련번호 %s, 시행 %s)" % (r["name"], r["kind"], r["일련번호"], r["시행일자"])

    def lawrow(kind_r, 구분, loc, title, text, note=""):
        terms = "|".join(sorted({("금융체계상 중요한" if k.startswith("금융체계상") else k)
                                 for k in TERMS if k in text}))
        return dict(구분=구분, 법령={"법률": "법", "시행령": "시행령"}.get(kind_r["kind"], kind_r["kind"]), 조문=loc,
                    조문제목=title, 포함어=terms, source_text=text, rcept_no_or_url=kind_r["출처URL"],
                    doc_name=dname(kind_r), page="%s (법령은 쪽 없음 — 조문 위치)" % loc, note=note,
                    collected_at=kind_r["collected_at"], source_sha256=kind_r["xml_sha256"])

    rows = []
    # (A) 법 제2조제1호 「금융기관」 각 목 + 시행령 제2조(차목 위임)
    head = find_unit(xb_law, "제2조", None, 1)
    rows.append(lawrow(law, "제2조제1호 금융기관", "제2조제1호", head[1], head[2].split("\n")[0],
                       "호 본문(각 목은 아래 행)"))
    for mok in "가나다라마바사아자차":
        u = find_unit(xb_law, "제2조", None, 1, mok)
        if not u:
            rows.append(lawrow(law, "제2조제1호 금융기관", _loc("제2조", None, 1, mok), "", "문서에 없음",
                               "법 XML 제2조제1호에 %s목 없음" % mok))
            continue
        note = ("금융지주회사 포함 — 원문 자목 「「금융지주회사법」에 따른 금융지주회사」" if "금융지주회사" in u[2] else "")
        if mok == "차":
            note = "대통령령 위임 → 시행령 제2조(아래 행)"
        rows.append(lawrow(law, "제2조제1호 금융기관", _loc("제2조", None, 1, mok), u[1], u[2], note))
    u = find_unit(xb_dec, "제2조")
    rows.append(lawrow(dec, "제2조제1호 금융기관", "제2조", u[1], u[2],
                       "법 제2조제1호차목의 「대통령령으로 정하는 기관」. 단서: 농협은행·수협은행은 법 제9조의2~제9조의10·"
                       "제14조의9 적용 때만 금융기관"))
    has_fhc = any("금융지주회사" in r["source_text"] for r in rows if r["조문"].endswith("자목"))
    # (B) 「금융체계상 중요한 금융기관」·「자체정상화계획」·「부실정리계획」이 나오는 조문(법·시행령 전수)
    for kr, xb in ((law, xb_law), (dec, xb_dec)):
        for lab, tit, u in law_units(xb):
            t = article_text(u)
            if not any(k in t for k in TERMS):
                continue
            if not lab:
                rows.append(lawrow(kr, "SIFI 관련 조문", "(장 제목)", "", t, "조문이 아닌 장(章) 제목 줄"))
            else:
                rows.append(lawrow(kr, "SIFI 관련 조문", lab, tit, t,
                                   "조문 제목 「%s」 · 첫 문장: %s" % (tit, _first_sentence(t.split("\n")[0]
                                                                         if len(t.split("\n")[0]) > 20 else
                                                                         " ".join(t.split("\n")[:2])))))
    # (C) 선정 대상 업권 · 근거 조문
    u = find_unit(xb_law, "제9조의2", 1)
    rows.append(lawrow(law, "선정 대상 업권", "제9조의2제1항", u[1], u[2],
                       "선정 근거(법). 대상은 「대통령령으로 정하는 종류의 금융기관(그 자회사를 포함한다…)」 → 시행령 제5조의4제1항"))
    u = find_unit(xb_dec, "제5조의4", 1)
    insur = any(k in u[2] for k in ("보험회사", "보험업법", "보험지주"))
    rows.append(lawrow(dec, "선정 대상 업권", "제5조의4제1항", u[1], u[2],
                       "선정 대상 종류(시행령): 은행·은행지주회사·농협은행·수협은행. 보험회사·보험지주(보험업법) 낱말 %s. "
                       "판단: 보험회사는 독자 종류로는 대상이 아니나, 법 제9조의2제1항 괄호 「(그 자회사를 포함한다. 이하 이 장에서 "
                       "같다)」에 따라 선정된 은행지주회사의 보험 자회사는 그 범위에 들어가는 것으로 읽힘(조문 문언 기준)"
                       % ("있음" if insur else "없음")))
    u = find_unit(xb_dec, "제5조의4", 2)
    rows.append(lawrow(dec, "선정 대상 업권", "제5조의4제2항", u[1], u[2], "구체적 선정기준(시행령)"))
    rule_art = {l: t for l, _, t in rule_articles(xb_rule)}
    for hang in (1, 6):
        txt = dict(_rule_clauses(rule_art["제25조의2"])).get(hang, "")
        rows.append(dict(lawrow(rule, "선정 대상 업권", "제25조의2제%d항" % hang, "금융체계상 중요한 은행지주회사 선정 등", txt,
                                "감독규정: 금융위가 은행지주회사 중 선정(①), 그 은행지주회사를 금산법상 금융체계상 중요한 "
                                "금융기관으로 선정(⑥)" if hang == 6 else "감독규정: 선정 대상은 은행지주회사"),
                         법령="감독규정"))
    # (D) 연차보고서(FY2025) 서술 — 선정·자체정상화계획 제출
    meta = {r["파일명"]: r for r in csv.DictReader(open(AR_LIST, encoding="utf-8-sig"))}
    for co, page, quote, note in AR_QUOTES:
        fn = "%s_지배구조연차보고서_2026.pdf" % co
        m = meta.get(fn, {})
        s = open(AR_TEXT % (co, ""), encoding="utf-8").read()
        pg = re.search(r"^=== p\.%d ===[^\n]*\n(.*?)(?=^=== p\.|\Z)" % page, s, re.S | re.M)
        ok = bool(pg) and _nows(quote) in _nows(pg.group(1))
        if not ok:
            raise SystemExit("연차보고서 인용 불일치: %s p.%d" % (co, page))
        add = AR_TEXT % (co, "_추가공시")
        add_note = ""
        if os.path.exists(add):
            add_note = (" · 추가공시 텍스트에도 같은 문장 있음" if _nows(quote) in _nows(open(add, encoding="utf-8").read())
                        else " · 추가공시 텍스트에는 같은 문장 없음(문구 다르거나 해당 쪽 없음)")
        rows.append(dict(구분="연차보고서 서술(FY2025)", 법령="연차보고서", 조문=co, 조문제목="", 포함어="|".join(
            k for k in ("금융체계상 중요한", "자체정상화계획", "부실정리계획") if _nows(k) in _nows(quote)),
            source_text=quote, rcept_no_or_url=m.get("url", ""),
            doc_name="%s %s(%s)" % (co, m.get("제목", ""), fn), page="p.%d" % page, note=note + add_note,
            collected_at=m.get("fetched_at", ""), source_sha256=m.get("sha256", "")))
    for co in ("KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"):
        if not any(r["조문"] == co for r in rows):
            rows.append(dict(구분="연차보고서 서술(FY2025)", 법령="연차보고서", 조문=co, source_text="문서에 없음",
                             note="자체정상화계획 문장 못 찾음"))
    write_csv(CHECK_CSV, CHECK_COLS, rows)

    # 인용 대조 — 감독규정에서 금산법을 가리키는 표기 전수(§25의2⑥·§25의5 는 요청범위 Y)
    crow = []
    for lab, tit, text in rule_articles(xb_rule):
        for hang, ctext in _rule_clauses(text):
            for m in re.finditer(GEUMSAN_RE, ctext):
                refs = [("법", re.sub(r"\s+", "", m.group(1)))]
                if m.group(2):
                    refs.append(("시행령", re.sub(r"\s+", "", m.group(2))))
                # 감독규정 안의 호 위치: 인용이 들어 있는 줄이 「N.」 으로 시작하면 그 호
                line = ctext[:m.start()].split("\n")[-1] + ctext[m.start():].split("\n")[0]
                hm = re.match(r"\s*(\d+(?:의\d+)?)\.", line)
                for say, ref in refs:
                    clause = lab + ("제%d항" % hang if hang else "") + ("제%s호" % hm.group(1) if hm else "")
                    key = (re.sub(r"제\d+(?:의\d+)?호$", "", clause) if hm else clause,
                           ref if say == "법" else "시행령 " + ref)
                    key = (clause, ref if say == "법" else "시행령 " + ref)
                    jo, hg, ho, mok = _parse_ref(ref)
                    in_law = find_unit(xb_law, jo, hg, ho, mok)
                    in_dec = find_unit(xb_dec, jo, hg, ho, mok)
                    said = in_law if say == "법" else in_dec
                    other = in_dec if say == "법" else in_law
                    note = ""
                    # 법 제2조 각 호(정의) 인용: 인용 호의 정의어가 감독규정 글에 있는지 기계 대조
                    if jo == "제2조" and ho and said:
                        dm = re.search(r'"([^"]+)"(?:이)?란', said[2])
                        term = dm.group(1) if dm else ""
                        if term and _nows(term) not in _nows(ctext):
                            alt = [(k, d) for k in range(1, 20) for d in [find_unit(xb_law, "제2조", None, k)]
                                   if d and re.search(r'"([^"]+)"(?:이)?란', d[2])
                                   and re.search(r'"([^"]+)"(?:이)?란', d[2]).group(1).replace(" ", "") in _nows(ctext)]
                            note = ("기계 대조: 인용 호(제2조제%d호)의 정의어 「%s」이(가) 감독규정 글에 없음(공백 무시)%s — 판단 필요"
                                    % (ho, term, "; 감독규정 글에 있는 정의어: " + ", ".join(
                                        "「%s」(제2조제%d호)" % (re.search(r'"([^"]+)"(?:이)?란', d[2]).group(1), k)
                                        for k, d in alt) if alt else ""))
                        elif term:
                            note = "기계 대조: 인용 호의 정의어 「%s」이(가) 감독규정 글에 있음(공백 무시)" % term
                    if said:
                        actual, unit = ("법" if say == "법" else "시행령") + " " + _loc(jo, hg, ho, mok), said
                    elif other:
                        actual = "%s %s (감독규정 표기는 %s — %s 에는 %s 없음)" % (
                            "시행령" if say == "법" else "법", _loc(jo, hg, ho, mok), say, say,
                            _loc(jo, hg, ho, mok))
                        unit = other
                        up = find_unit(xb_dec if say == "법" else xb_law, jo, hg) if ho else None
                        note = ("표기된 %s XML 에 %s 이(가) 없고(조 자체 없음: %s), 같은 번호의 %s 조문이 있다. %s"
                                "판단: 감독규정 글(감독규정_source_text)과 이 조문 글(인용단위_source_text)이 같은 내용"
                                "(금융위 고시로 정하는 자체정상화계획 포함사항)으로 읽혀, 실제 근거는 %s 조문으로 봄" % (
                                    say, _loc(jo, hg, ho, mok), "예" if not find_unit(xb_law if say == "법" else xb_dec, jo)
                                    else "아니오", "시행령" if say == "법" else "법",
                                    ("상위 항 첫 줄(원문): 「%s」. " % up[2].split("\n")[0]) if up else "",
                                    "시행령" if say == "법" else "법"))
                    else:
                        actual, unit = "문서에 없음(법·시행령 모두 해당 조문 없음)", None
                    crow.append(dict(
                        감독규정_조항=clause, 요청범위="Y" if key in ASKED else "N", 사용자_표기=ASKED.get(key, ""),
                        인용표기=re.sub(r"\s+", " ", m.group(0)).strip(), 인용상_법령=say,
                        법_해당조문=("있음 — %s(%s)" % (_loc(jo, hg, ho, mok), in_law[1]) if in_law else
                                  "없음 — 법에 %s 없음%s" % (_loc(jo, hg, ho, mok), "" if find_unit(xb_law, jo) else
                                                         "(조 자체가 없음)")),
                        시행령_해당조문=("있음 — %s(%s)" % (_loc(jo, hg, ho, mok), in_dec[1]) if in_dec else
                                    "없음 — 시행령에 %s 없음%s" % (_loc(jo, hg, ho, mok), "" if find_unit(xb_dec, jo) else
                                                              "(조 자체가 없음)")),
                        실제조문=actual, 조문제목=(unit[1] if unit else ""),
                        원문첫문장=_first_sentence(unit[2]) if unit else "문서에 없음",
                        인용단위_source_text=unit[2] if unit else "문서에 없음", 감독규정_source_text=ctext,
                        **{"7차판과_같음": ("Y" if _nows(old.get(lab, "")) == _nows(text) else "N") if old else "7차 판 없음"},
                        rcept_no_or_url=" ; ".join([rule["출처URL"], (law if (unit is in_law) else dec)["출처URL"]])
                        if unit else rule["출처URL"],
                        doc_name=" ; ".join([dname(rule)] + ([dname(law if unit is in_law else dec)] if unit else [])),
                        page="감독규정 %s → %s (법령은 쪽 없음)" % (clause, actual.split(" (")[0]),
                        note=note, collected_at=rule["collected_at"],
                        source_sha256=" ; ".join([rule["xml_sha256"]] + ([(law if unit is in_law else dec)["xml_sha256"]]
                                                                         if unit else []))))
    missing = [v for k, v in ASKED.items() if not any((r["감독규정_조항"], r["사용자_표기"]) == (k[0], v) for r in crow)]
    if missing:
        raise SystemExit("요청한 인용을 감독규정에서 못 찾음: %s" % missing)
    crow.sort(key=lambda r: (r["요청범위"] != "Y", r["감독규정_조항"]))
    write_csv(CITE_CSV, CITE_COLS, crow)
    print("금산법_확인 %d행 (제2조제1호 자목 금융지주회사 %s) · 인용대조 %d행(요청 %d)"
          % (len(rows), "있음" if has_fhc else "없음", len(crow), sum(r["요청범위"] == "Y" for r in crow)))


# ── 6-6 define ────────────────────────────────────────────────────────────
DEF_CSV = os.path.join(OUT, "계열회사_정의대조.csv")
DEF_COLS = ["구분", "법령", "조문", "조문제목", "원문첫문장", "외국법인_언급", "외국_어구", "source_text", "시행예정판_대조",
            "rcept_no_or_url", "doc_name", "page", "note", "collected_at", "source_sha256"]
FOREIGN = r"국외\s*계열회사|외국\s*법인|외국법인|외국\s*회사|외국회사|외국에\s*주된|외국인|외국의\s*법령|국외[가-힣]*"
DOMESTIC = r"국내\s*회사"


def _units_with(xb, pat):
    """조문 → 항(없으면 조) 단위로 pat 이 들어 있는 것: [(조문표지, 조문제목, 항번호|None, 글)]."""
    out = []
    for lab, tit, u in law_units(xb):
        if not lab:
            continue
        hs = u.findall("항")
        if hs:
            head = _t(u, "조문내용")
            if re.search(pat, head):
                out.append((lab, tit, None, head))
            for h in hs:
                t = article_text(h)
                if re.search(pat, t):
                    out.append((lab, tit, CIRCLED.get(_t(h, "항번호")[:1]), t))
        else:
            t = article_text(u)
            if re.search(pat, t):
                out.append((lab, tit, None, t))
    return out


def define():
    lst = _listed()
    allrows = list(csv.DictReader(open(LIST_CSV, encoding="utf-8-sig")))
    X = {}
    for r in allrows:
        if r["상태"] == "OK":
            X[(r["name"], r["kind"], r["일련번호"])] = (r, open(r["원문XML"], "rb").read())

    def cur(name):
        r = lst[name]
        return r, X[(name, r["kind"], r["일련번호"])][1]

    def pend(name):
        return [(r, xb) for (n, k, sn), (r, xb) in X.items() if n == name and k.endswith("(시행예정)")]

    def dname(r):
        return "%s(%s 일련번호 %s, 시행 %s)" % (r["name"], r["kind"], r["일련번호"], r["시행일자"])

    def row(구분, name, jo, hang=None, ho=None, mok=None, text=None, title=None, note="", 법령=None):
        r, xb = cur(name)
        if text is None:
            u = find_unit(xb, jo, hang, ho, mok)
            if not u:
                raise SystemExit("조문 없음: %s %s" % (name, _loc(jo, hang, ho, mok)))
            title, text = u[1], u[2]
        loc = _loc(jo, hang, ho, mok)
        fx = sorted(set(re.sub(r"\s+", " ", x) for x in re.findall(FOREIGN, text)))
        dx = sorted(set(re.sub(r"\s+", " ", x) for x in re.findall(DOMESTIC, text)))
        flag = "Y" if fx else ("N(「국내 회사」로 한정)" if dx else "N")
        if fx and all(x.startswith("외국인") for x in fx):
            note = (note + " · " if note else "") + "외국 어구가 「외국인」(개인)뿐 — 회사·법인 언급은 아님"
        cmp_ = []
        for pr, pxb in sorted(pend(name), key=lambda z: z[0]["시행일자"]):
            pu = find_unit(pxb, jo, hang, ho, mok)
            cmp_.append("%s(시행 %s) %s" % (pr["일련번호"], pr["시행일자"],
                                           "같음" if pu and _nows(pu[2]) == _nows(text) else
                                           ("다름" if pu else "조문 없음")))
        return dict(구분=구분, 법령=법령 or "%s(%s)" % (name, r["kind"]), 조문=loc, 조문제목=title or "",
                    원문첫문장=_first_sentence(text), 외국법인_언급=flag, 외국_어구="|".join(fx + dx),
                    source_text=text, 시행예정판_대조=" ; ".join(cmp_) or "시행예정 판 없음",
                    rcept_no_or_url=r["출처URL"], doc_name=dname(r),
                    page="%s (법령은 쪽 없음 — 조문 위치)" % loc, note=note, collected_at=r["collected_at"],
                    source_sha256=r["xml_sha256"])

    def absent(구분, name, what, note):
        r, xb = cur(name)
        return dict(구분=구분, 법령="%s(%s)" % (name, r["kind"]), 조문=what, 조문제목="", 원문첫문장="문서에 없음",
                    외국법인_언급="", 외국_어구="", source_text="문서에 없음", 시행예정판_대조="",
                    rcept_no_or_url=r["출처URL"], doc_name=dname(r), page="", note=note,
                    collected_at=r["collected_at"], source_sha256=r["xml_sha256"])

    FTC_D = FTC + " 시행령"
    rows = []
    # (A) 법 제2조 정의
    _, xb = cur(FTC)
    defs = {re.search(r'"([^"]+)"(?:이)?란', find_unit(xb, "제2조", None, k)[2]).group(1): k
            for k in range(1, 40) if find_unit(xb, "제2조", None, k)
            and re.search(r'"([^"]+)"(?:이)?란', find_unit(xb, "제2조", None, k)[2])}
    for term in ("기업집단", "계열회사"):
        rows.append(row("정의(법 제2조)", FTC, "제2조", None, defs[term],
                        note="기업집단: 동일인이 「사실상 그 사업내용을 지배하는 회사의 집단」 — 「회사」에 국내·국외 구분 없음"
                        if term == "기업집단" else "계열회사: 동일한 기업집단에 속하는 회사 — 국내·국외 구분 없음. 판단: 법 제26조제1항·"
                        "제28조제2항·제29조제1항이 「(국외 계열회사는 제외한다…)」고 따로 빼고, 시행령 제35조가 국외 계열회사 "
                        "현황을 공시 항목으로 두는 것은 국외 계열회사가 계열회사에 들어감을 전제로 한 문언으로 읽힘(아래 "
                        "「외국 법인·국외 계열회사」 행)"))
    for term in ("동일인", "회사"):
        if term in defs:
            rows.append(row("정의(법 제2조)", FTC, "제2조", None, defs[term]))
        else:
            rows.append(absent("정의(법 제2조)", FTC, "제2조 「%s」 정의" % term,
                               "기계 검색: 법 제2조 각 호에 「\"%s\"이란/란」 정의가 없음(정의 낱말 %d개: %s). %s"
                               % (term, len(defs), ", ".join(sorted(defs, key=defs.get)),
                                  "동일인은 제2조제11호(기업집단) 안에서 쓰이고, 시행령 제4조가 동일인관련자를 정의"
                                  if term == "동일인" else "제2조제7~9호는 「국내 회사」라고 따로 한정해 씀")))
    for term in ("지주회사", "자회사", "손자회사"):
        rows.append(row("정의(법 제2조)", FTC, "제2조", None, defs[term],
                        note="대비: 이 정의들은 「국내 회사」로 한정 — 기업집단·계열회사 정의에는 이런 한정이 없음"))
    # (B) 시행령 기업집단 범위(사실상 지배 판단 기준)
    rows.append(row("기업집단 범위(시행령)", FTC_D, "제4조", 1,
                    note="법 제2조제11호의 「사실상 그 사업내용을 지배하는 회사」 판단 기준(지분 30% 이상 최다출자자·지배적 영향력)"))
    rows.append(row("기업집단 범위(시행령)", FTC_D, "제4조", 2))
    for jo in ("제5조", "제6조"):
        u = find_unit(cur(FTC_D)[1], jo, 1)
        rows.append(row("기업집단 범위(시행령)", FTC_D, jo, 1, text=u[2].split("\n")[0], title=u[1],
                        note="항의 첫 줄만(각 호는 원문 md 참조)"))
    # (C) 외국 법인·국외 계열회사 언급 조문(법·시행령 전수, 항 단위)
    for name in (FTC, FTC_D):
        for lab, tit, hang, t in _units_with(cur(name)[1], FOREIGN):
            rows.append(row("외국 법인·국외 계열회사", name, lab, hang, text=t, title=tit))
    # (D) 「국내 회사」로 한정한 조문(외국 언급 없는 것만, 항 단위)
    for name in (FTC, FTC_D):
        seen = {(r["법령"], r["조문"]) for r in rows}
        for lab, tit, hang, t in _units_with(cur(name)[1], DOMESTIC):
            if re.search(FOREIGN, t):
                continue
            rr = row("「국내 회사」 한정 조문", name, lab, hang, text=t, title=tit)
            if (rr["법령"], rr["조문"]) not in seen:
                rows.append(rr)
    # (E) 연결 조문 — 대주주 → 특수관계인 → 공정거래법 계열회사
    GOV, GOV_D, INS = "금융회사의 지배구조에 관한 법률", "금융회사의 지배구조에 관한 법률 시행령", "보험업법"
    rows.append(row("연결 조문", INS, "제2조", None, 17, note="보험업법의 대주주 = 지배구조법 제2조제6호"))
    rows.append(row("연결 조문", GOV, "제2조", None, 6, note="대주주(최대주주·주요주주) — 최대주주는 특수관계인 포함"))
    u = find_unit(cur(GOV_D)[1], "제3조", 1)
    rows.append(row("연결 조문", GOV_D, "제3조", 1, text=u[2].split("\n")[0], title=u[1], note="특수관계인 정의(항 첫 줄)"))
    rows.append(row("연결 조문", GOV_D, "제3조", 1, 2, "나",
                    note="본인이 법인인 경우 특수관계인 = 공정거래법 계열회사 및 그 임원 — 국외 계열회사 포함 여부는 "
                         "공정거래법 계열회사 정의(위 정의 행)에 달림"))
    for ho in (4, 5, 6):
        rows.append(row("연결 조문", INS, "제106조", 1, ho))
    for hang in (1, 2, 3, 4):
        rows.append(row("연결 조문", INS, "제111조", hang))
    write_csv(DEF_CSV, DEF_COLS, rows)
    print("계열회사_정의대조 %d행 · 외국 언급 Y %d · 국내 회사 한정 %d · 문서에 없음 %d"
          % (len(rows), sum(r["외국법인_언급"] == "Y" for r in rows),
             sum(r["외국법인_언급"].startswith("N(") for r in rows), sum(r["source_text"] == "문서에 없음" for r in rows)))


# ── 6-2 annex37 ───────────────────────────────────────────────────────────
SEC_XML = os.path.join("dart_out", "raw", "web9", "law", "보험업감독업무시행세칙_2200000108939.xml")
SEC_META = SEC_XML + ".meta.json"
A37_MD = os.path.join(OUT, "세칙_별표37.md")
A37_CSV = os.path.join(OUT, "세칙_별표37_표시.csv")
A37_COLS = ["표시", "위치", "md_줄", "pdf_page", "source_text", "rcept_no_or_url", "doc_name", "page", "note",
            "collected_at", "source_sha256"]
# 사용자 요청 표시 항목 → 줄 판정(원문 낱말). 판정 낱말은 note 에 그대로 남긴다.
MARKS = [
    ("적용 대상(제1장 3.)", None),                                  # 제1장의 「3.」 항목 — 위치로 찾는다
    ("시행 시기·유예", r"시행|유예|경과규정|경과조치|부칙|도입"),
    ("이사회·위원회 보고", r"이사회|위원회"),
    ("자회사·그룹 범위", r"자회사|그룹|계열|지주|연결"),
]


def _pdf_pages(path):
    from pypdf import PdfReader
    return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(path).pages)]


def annex37():
    import json
    import xml.etree.ElementTree as ET2
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
    import collect
    client = _client()
    xb = open(SEC_XML, "rb").read()
    smeta = json.load(open(SEC_META, encoding="utf-8"))
    root = ET2.fromstring(xb)
    unit = next(b for b in root.iter("별표단위") if (b.findtext("별표번호") or "").strip() == "0037"
                and (b.findtext("별표구분") or "").strip() == "별표")
    g = lambda k: (unit.findtext(k) or "").strip()                                  # noqa: E731
    title = g("별표제목")
    got = {}
    for link, want in ((g("별표서식PDF파일링크"), "PDF"), (g("별표서식파일링크"), "HWP")):
        done = [q for q in glob.glob(os.path.join(RAW, "annex37", "세칙_별표37.*.meta.json"))
                if json.load(open(q, encoding="utf-8")).get("링크") == link]
        if done:                                     # 이미 받은 원본은 다시 받지 않는다
            m = json.load(open(done[0], encoding="utf-8"))
            got[want] = dict(상태="OK", 경로=m["저장경로"], **m)
            continue
        st, body, ct, murl, host = client.file(link)
        fmt = collect.sniff(body) if body else ""
        if st != 200 or fmt not in ("PDF", "HWP", "HWPX"):
            got[want] = dict(상태="실패", 출처URL=murl, note="HTTP %s · 형식 %s" % (st, fmt or "없음"))
            continue
        ext = {"PDF": ".pdf", "HWP": ".hwp", "HWPX": ".hwpx"}[fmt]
        p, m = save("annex37", "세칙_별표37" + ext, body,
                    dict(출처URL=murl, 링크=link, 원형식=fmt, http_status=st, content_type=ct, fetched_at=now(),
                         세칙XML=SEC_XML, 세칙XML_sha256=smeta.get("sha256", ""), 별표제목=title))
        got[want] = dict(상태="OK", 경로=p, **m)
    if got.get("HWP", {}).get("상태") != "OK":
        raise SystemExit("별표37 hwp 를 받지 못함: %s" % got.get("HWP"))
    hwp = got["HWP"]
    full = os.path.join(RAW, "annex37", "세칙_별표37_hwp2md.md")
    subprocess.run([sys.executable, os.path.join(HERE, "hwp2md.py"), hwp["경로"], full], check=True)
    raw_md = open(full, encoding="utf-8").read().rstrip("\n")
    # 읽기용 변환(글자는 그대로): 별표 전체가 한 칸짜리 표라 hwp2md 가 한 줄(<br> 로 줄바꿈)로 낸다.
    #   ① 칸 글만 꺼내고(앞뒤 「| 」·「 |」 떼기) ② <br> → 줄바꿈 ③ \| → | ④ 표 구분줄 |---| 생략.
    lines = []
    for l in raw_md.split("\n"):
        st = l.strip()
        if re.fullmatch(r"\|(\s*-+\s*\|)+", st):
            continue
        if st.startswith("|") and "<br>" in st:
            cell = re.sub(r"^\|\s?", "", st)
            cell = re.sub(r"\s?\|$", "", cell)
            lines += [x.replace("\\|", "|") for x in cell.split("<br>")]
        else:
            lines.append(l)
    while lines and not lines[-1].strip():
        lines.pop()
    pages = _pdf_pages(got["PDF"]["경로"]) if got.get("PDF", {}).get("상태") == "OK" else []
    if pages:
        with open(os.path.join(RAW, "annex37", "세칙_별표37_pdf.txt"), "w", encoding="utf-8") as f:
            for n, t in pages:
                f.write("=== p.%d ===\n%s\n" % (n, t))

    def pdf_page(text):
        k = _nows(text)[:40]
        hit = [n for n, t in pages if k and k in _nows(t)]
        if not hit and k:                            # 쪽 경계에 걸친 줄: 앞 20자로 다시
            hit = [n for n, t in pages if k[:20] in _nows(t)]
        return ",".join(map(str, hit)) if hit else ("PDF 에서 못 찾음" if pages else "PDF 없음")

    # 줄마다 위치(장 > 절 > 번호 항목 > 가목) — 원문 표지 그대로
    ctx = dict(장="", 절="", 항="", 목="")
    loc_of = []
    for l in lines:
        st = l.strip()
        if re.match(r"^제\s*\d+\s*장", st):
            ctx = dict(장=st, 절="", 항="", 목="")
        elif re.match(r"^제\s*\d+\s*절", st):
            ctx.update(절=st, 항="", 목="")
        elif re.match(r"^\d+\.\s*\(", st):
            ctx.update(항=re.match(r"^(\d+\.\s*\([^)]*\))", st).group(1), 목="")
        elif re.match(r"^[가-하]\.", st):
            ctx.update(목=st[:2])
        loc_of.append(" > ".join(v for v in (ctx["장"], ctx["절"], ctx["항"], ctx["목"]) if v))
    rows = []
    docname = "보험업감독업무시행세칙(세칙 일련번호 2200000108939, 시행 20260910) [별표 37] %s" % title
    url = "%s ; %s" % (got.get("HWP", {}).get("출처URL", ""), got.get("PDF", {}).get("출처URL", ""))
    sha = "hwp %s ; pdf %s" % (got["HWP"]["sha256"], got.get("PDF", {}).get("sha256", ""))

    def add(mark, i, j, note):
        txt = "\n".join(lines[i:j]).strip()
        ln = "%d~%d" % (i + 1, j) if j - i > 1 else str(i + 1)
        pg = pdf_page(txt)
        rows.append(dict(표시=mark, 위치=loc_of[i] or "(장 표지 전)", md_줄=ln, pdf_page=pg, source_text=txt,
                         rcept_no_or_url=url, doc_name=docname, page="pdf p.%s · md 「## 원문」 %s번째 줄" % (pg, ln),
                         note=note, collected_at=hwp["fetched_at"], source_sha256=sha))

    def none(mark, note):
        rows.append(dict(표시=mark, 위치="", md_줄="", pdf_page="", source_text="문서에 없음", rcept_no_or_url=url,
                         doc_name=docname, page="", note=note, collected_at=hwp["fetched_at"], source_sha256=sha))

    # (1) 제1장 「3.」 항목 — 「3. (」 줄부터 다음 번호 항목·장 앞까지
    s3 = next((i for i, l in enumerate(lines) if loc_of[i].startswith("제1장") and re.match(r"^\s*3\.\s*\(", l)), None)
    if s3 is None:
        none("적용 대상(제1장 3.)", "제1장 안에 「3. (」 으로 시작하는 줄 없음")
    else:
        e3 = next((i for i in range(s3 + 1, len(lines)) if re.match(r"^\s*(\d+\.\s*\(|제\s*\d+\s*[장절])", lines[i])),
                  len(lines))
        add("적용 대상(제1장 3.)", s3, e3, "제1장 「3. (적용 대상)」 항목 전체(다음 번호 항목·장 앞까지)")
    # (2)~(4) 낱말이 든 줄(가목·(1) 등 한 줄이 한 항목)
    for mark, pat in MARKS[1:]:
        n = 0
        for i, l in enumerate(lines):
            ws = sorted(set(re.findall(pat, l)))
            if ws and l.strip():
                add(mark, i, i + 1, "판정 낱말: %s" % ", ".join(ws))
                n += 1
        if not n:
            none(mark, "별표 본문에 판정 낱말(%s) 없음" % pat)
    # (2') 시행 시기·유예 — 세칙 부칙(원문 XML 부칙내용)에서 별표37·제5-6조의2·「자체 위험」을 언급한 조
    for e in root.iter("부칙내용"):
        t = "".join(e.itertext())
        head_ = t.strip().split("\n")[0].strip()
        paras = re.split(r"\n(?=\s*제\d+조)", t)
        hit_37 = any(re.search(r"별표\s*37", x) for x in paras)
        for para in paras:
            first_art = re.match(r"\s*제1조\s*\(시행일\)", para)
            if re.search(r"별표\s*37|5-6조의2|자체\s*위험", para) or (hit_37 and first_art):
                why = ("별표37 을 신설한 개정 부칙의 시행일 조" if (hit_37 and first_art and not re.search(
                    r"별표\s*37|5-6조의2|자체\s*위험", para)) else
                       "제5-6조의2(별표37 의 근거 조)를 언급" if "5-6조의2" in para and not hit_37 else "")
                rows.append(dict(표시="시행 시기·유예", 위치="세칙 %s" % head_, md_줄="", pdf_page="",
                                 source_text=para.strip(), rcept_no_or_url=smeta.get("출처URL", ""),
                                 doc_name="보험업감독업무시행세칙(일련번호 2200000108939) 부칙 — 원문 XML 부칙내용",
                                 page="세칙 %s (원문 XML, 쪽 없음)" % head_,
                                 note="세칙 부칙(별표 밖). %s%s" % (why + ". " if why else "", "판정 낱말: %s" % ", ".join(
                                     sorted(set(re.findall(r"별표\s*37|5-6조의2|자체\s*위험", para)))) if re.search(
                                     r"별표\s*37|5-6조의2|자체\s*위험", para) else ""),
                                 collected_at=smeta.get("fetched_at", ""), source_sha256=smeta.get("sha256", "")))
    write_csv(A37_CSV, A37_COLS, rows)
    # md: 머리말 + 표시 목록 + 원문(읽기용 변환만)
    from collections import OrderedDict
    idx = OrderedDict()
    for r in rows:
        idx.setdefault(r["표시"], []).append(r["md_줄"] or r["위치"])
    head = ["# 보험업감독업무시행세칙 [별표 37] %s" % title, "",
            "- 세칙: 보험업감독업무시행세칙 일련번호 2200000108939 · 시행 20260910 · 발령 20260828(9차 수집 현행 판, "
            "원문 XML sha256 %s)" % smeta.get("sha256", ""),
            "- 별표 표지(원문 XML 별표내용 첫 줄): %s — 사용자 메모의 「2026.6.29 개정」은 원문 표기로는 「신설」"
            % g("별표내용").split("\n")[0].strip(),
            "- 원본: 국가법령정보센터 별표 파일 — HWP %s (sha256 %s, %s바이트) · PDF %s (sha256 %s, %d쪽)"
            % (got["HWP"]["출처URL"], got["HWP"]["sha256"], got["HWP"]["바이트"],
               got.get("PDF", {}).get("출처URL", "실패"), got.get("PDF", {}).get("sha256", ""), len(pages)),
            "- 수집일: %s" % hwp["fetched_at"],
            "- 텍스트화: scripts/dart/hwp2md.py(사용자 제공, 수정 없음) 출력(sha256 %s). 별표 전체가 한 칸짜리 표라 "
            "hwp2md 가 한 줄로 내므로, 아래 「원문」은 ① 칸 글만 꺼내고 ② `<br>` 을 줄바꿈으로 ③ `\\|` 를 `|` 로 "
            "④ 표 구분줄을 뺐다. 글자는 바꾸지 않았다(원 출력은 원본 묶음 세칙_별표37_hwp2md.md)."
            % hashlib.sha256(raw_md.encode("utf-8")).hexdigest(),
            "- 쪽 번호는 같은 별표 PDF 를 pypdf 로 읽어 그 줄을 찾은 쪽(세칙_별표37_표시.csv 의 pdf_page).",
            "", "## note 표시 (사용자 요청 항목 → 「## 원문」 줄 번호, 상세·원문은 세칙_별표37_표시.csv)", ""]
    head += ["- %s: %s" % (k, ", ".join(v)) for k, v in idx.items()]
    head += ["", "---", "", "## 원문", ""]
    with open(A37_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(head + lines) + "\n")
    print("별표37: HWP %s · PDF %s(%d쪽) · 원문 %d줄 · 표시 %d행 (%s)" % (
        got["HWP"]["상태"], got.get("PDF", {}).get("상태"), len(pages), len(lines), len(rows),
        ", ".join("%s %d" % (k, len(v)) for k, v in idx.items())))


# ── 6-4 posting ───────────────────────────────────────────────────────────
POST_CSV = os.path.join(OUT, "목록_연차보고서_게시처.csv")
POST_COLS = ["corp_label", "site", "url", "found", "checked_at", "note", "evidence_file", "evidence_sha256"]


def posting():
    """자사 누리집 행(8차에 받은 FY2025 연차보고서 기록) + 협회별 확인 결과(dart_out/risk10/게시처_*.csv)."""
    rows = []
    for r in csv.DictReader(open(AR_LIST, encoding="utf-8-sig")):
        if r["지주명"] in ("메리츠금융지주", "한국투자금융지주") and r["공시연도"] == "2026" and "지배구조" in r["구분"]:
            rows.append(dict(corp_label=r["지주명"], site="자사 누리집", url=r["url"],
                             found="Y" if r["다운로드성공"] == "Y" else "N", checked_at=r["fetched_at"],
                             note="8차 수집 기록(handoff/연차보고서_파일목록.csv): %s「%s」 %s · %s쪽%s" % (
                                 r["공시유형"] + " ", r["제목"], r["파일명"], r["페이지수"],
                                 " · 방식 POST(같은 URL 에 파일별 파라미터)" if r["방식"] == "POST" else ""),
                             evidence_file=r["파일명"], evidence_sha256=r["sha256"]))
    for f in sorted(glob.glob(os.path.join(WORK, "게시처_*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            rows.append({k: r.get(k, "") for k in POST_COLS})
    write_csv(POST_CSV, POST_COLS, rows)
    print("게시처 %d행 — %s" % (len(rows), ", ".join("%s/%s:%s" % (r["corp_label"][:2], r["site"][:6], r["found"])
                                                    for r in rows)))
