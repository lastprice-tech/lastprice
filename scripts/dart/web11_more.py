# -*- coding: utf-8 -*-
"""11차 7-3 별표 4·5 본문과 7-1 특수관계인 정의대조 — web11_law.py 의 하위 명령(annex·define)으로 부른다.

annex  : 금융지주회사법 시행령 원문 XML 의 [별표 4]·[별표 5] 별표내용(Open API 가 준 글)을 글자 그대로 옮긴다.
         별표내용이 비었으면 별표 파일(PDF 먼저)의 글자 층을 쓰고, 글자 층이 없으면 「미확인(문서 읽기 불가)」.
define : 원문_11차/특수관계인_정의대조.csv — 은행법 시행령 제1조의4(항·호·목 전부)와 그 조문이 인용하는 조문,
         금융지주회사법 제2조제1항제7호·제9호, 제34조제1항, 같은 법 시행령 제3조, 지배구조법 제2조제6호·시행령 제3조(10차 수집본),
         은행법 시행령 제1조의4제1항 ↔ 지배구조법 시행령 제3조제1항 호·목 대조(짝짓기는 내용 기준 — 판단, note 에 표시).
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import web10_law as L10  # noqa: E402
import web11_law as W  # noqa: E402
from web11 import OUT, LAWOUT, WORK, save, now, write_csv  # noqa: E402

ANNEX_MD = os.path.join(LAWOUT, "금융지주회사법시행령_별표4·5.md")
DEF_CSV = os.path.join(OUT, "특수관계인_정의대조.csv")
DEF_COLS = ["구분", "법령", "조문", "조문제목", "원문", "인용하는 조문", "외국 법인 언급", "대조_상대조문", "대조_상대원문",
            "차이여부", "note", "rcept_no_or_url", "doc_name", "page", "collected_at", "source_sha256"]
GOV_D_XML = os.path.join("dart_out", "raw", "web10", "law", "금융회사의지배구조에관한법률시행령_290289.xml")
GOV_XML = os.path.join("dart_out", "raw", "web10", "law", "금융회사의지배구조에관한법률_277253.xml")
FTC_XML = os.path.join("dart_out", "raw", "web10", "law", "독점규제및공정거래에관한법률_290153_현행재확인20261002.xml")
FTC_D_XML = os.path.join("dart_out", "raw", "web10", "law", "독점규제및공정거래에관한법률시행령_284737.xml")


def _nows(s):
    return re.sub(r"\s+", "", s or "")


# ── annex ─────────────────────────────────────────────────────────────────
def annex():
    import collect
    from pypdf import PdfReader
    rows = W.listed()
    r = rows[W.FHC_D]
    xb = open(r["원문XML"], "rb").read()
    root = ET.fromstring(xb)
    out, recs = [], []
    client = None
    for no in ("0004", "0005"):
        u = next((b for b in root.iter("별표단위") if (b.findtext("별표번호") or "").strip() == no
                  and (b.findtext("별표가지번호") or "").strip() in ("", "00")
                  and (b.findtext("별표구분") or "").strip() == "별표"), None)
        g = (lambda k: (u.findtext(k) or "").strip()) if u is not None else (lambda k: "")
        title, body, how = g("별표제목"), (u.findtext("별표내용") if u is not None else "") or "", ""
        if body.strip():
            how = "Open API 원문 XML 별표내용(글자 그대로)"
        else:
            client = client or W._client()
            for link, want in ((g("별표서식PDF파일링크"), "PDF"), (g("별표서식파일링크"), "HWP")):
                if not link:
                    continue
                st, b, ct, murl, host = client.file(link)
                fmt = collect.sniff(b) if b else ""
                if st == 200 and fmt == "PDF":
                    p, m = save("annex", "금융지주회사법시행령_별표%s.pdf" % int(no), b,
                                dict(출처URL=murl, 링크=link, http_status=st, fetched_at=now()))
                    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages)
                    if txt.strip():
                        body, how = txt, "별표 PDF 글자 층(pypdf) — %s sha256 %s" % (murl, m["sha256"])
                        break
                    how = "미확인(문서 읽기 불가) — PDF 에 글자 층 없음(%s)" % murl
            if not body.strip():
                body = "미확인(문서 읽기 불가)"
                how = how or "미확인(문서 읽기 불가) — 별표내용·파일 글자 모두 없음"
        out += ["## [별표 %d] %s" % (int(no), title), "",
                "- 별표 시행일자 %s · 원본 파일 링크: PDF %s · HWP %s (OC 불필요, 받지 않음)" % (
                    g("별표시행일자") or "(XML 에 없음)", "http://www.law.go.kr" + g("별표서식PDF파일링크") if g("별표서식PDF파일링크") else "-",
                    "http://www.law.go.kr" + g("별표서식파일링크") if g("별표서식파일링크") else "-"),
                "- 옮긴 곳: %s" % how, "", "```", body.rstrip("\n"), "```", ""]
        recs.append(dict(no=int(no), title=title, how=how, ok=not body.startswith("미확인")))
    head = ["# 금융지주회사법 시행령 [별표 4]·[별표 5]", "",
            "- 법령: 금융지주회사법 시행령 · 일련번호 %s · 시행일자 %s · 공포일자 %s" % (r["일련번호"], r["시행일자"], r["공포일자"]),
            "- 출처: 국가법령정보센터 Open API %s (OC=*** 가림) · 수집일 %s · 원문 XML sha256 %s"
            % (r["출처URL"], r["collected_at"], r["xml_sha256"]),
            "- 별표 본문은 XML 의 별표내용 글(표의 테두리 글자 포함)을 고치지 않고 코드 블록 안에 옮겼다.",
            "- 시행예정 판: %s" % r["시행예정판"], "", "---", ""]
    text = "\n".join(head + out) + "\n"
    with open(ANNEX_MD, "w", encoding="utf-8") as f:
        f.write(text)
    # 작업 기록 CSV 에 별표 행(있으면 바꿈)
    allr = [x for x in csv.DictReader(open(W.LIST_CSV, encoding="utf-8-sig")) if x["종류"] != "별표"]
    for x in recs:
        row = {c: "" for c in W.COLS}
        row.update(법령명="금융지주회사법 시행령 [별표 %d] %s" % (x["no"], x["title"]), 종류="별표", 일련번호=r["일련번호"],
                   시행일자=r["시행일자"], 공포일자=r["공포일자"], 파일=ANNEX_MD,
                   sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), note=x["how"],
                   name="금융지주회사법 시행령 [별표 %d]" % x["no"], kind="별표", 작업="7-3", 상태="OK" if x["ok"] else "미확인",
                   원문XML=r["원문XML"], xml_sha256=r["xml_sha256"], 텍스트=ANNEX_MD, 출처URL=r["출처URL"],
                   collected_at=r["collected_at"])
        allr.append(row)
    write_csv(W.LIST_CSV, W.COLS, allr)
    print("별표 4·5:", "; ".join("%d %s — %s" % (x["no"], x["title"][:30], x["how"][:40]) for x in recs))


# ── define ────────────────────────────────────────────────────────────────
REF = re.compile(r"「[^」]+」\s*(?:제\d+조(?:의\d+)?(?:\s*제\d+항)?(?:\s*제\d+호)?(?:\s*[가-하]목)?)?"
                 r"|(?:법|같은 법(?: 시행령)?|영)\s*제\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+호)?(?:[가-하]목)?"
                 r"|같은\s*(?:항|조)\s*제\d+호(?:\s*및\s*제\d+호)?(?:\s*각\s*목)?|같은\s*목|제\d+호(?:ㆍ제\d+호)*(?:또는|및)?")


def _refs(text):
    out = []
    for m in REF.finditer(text):
        x = re.sub(r"\s+", " ", m.group(0)).strip()
        if x.startswith("제") and "조" not in x:     # 같은 조 안의 호 참조(제1호 등)는 뺀다
            continue
        if x not in out:
            out.append(x)
    return " | ".join(out)


def define():
    rows = W.listed()
    bank_d, bank, fhc, fhc_d = rows[W.BANK_D], rows["은행법"], rows[W.FHC], rows[W.FHC_D]
    X = {k: open(v["원문XML"], "rb").read() for k, v in (("bank_d", bank_d), ("bank", bank), ("fhc", fhc),
                                                        ("fhc_d", fhc_d))}
    X["gov_d"], X["gov"] = open(GOV_D_XML, "rb").read(), open(GOV_XML, "rb").read()
    X["ftc"], X["ftc_d"] = open(FTC_XML, "rb").read(), open(FTC_D_XML, "rb").read()
    META = {"bank_d": (bank_d["출처URL"], "은행법 시행령(일련번호 %s, 시행 %s)" % (bank_d["일련번호"], bank_d["시행일자"]),
                       bank_d["collected_at"], bank_d["xml_sha256"]),
            "bank": (bank["출처URL"], "은행법(일련번호 %s, 시행 %s)" % (bank["일련번호"], bank["시행일자"]),
                     bank["collected_at"], bank["xml_sha256"]),
            "fhc": (fhc["출처URL"], "금융지주회사법(일련번호 %s, 시행 %s)" % (fhc["일련번호"], fhc["시행일자"]),
                    fhc["collected_at"], fhc["xml_sha256"]),
            "fhc_d": (fhc_d["출처URL"], "금융지주회사법 시행령(일련번호 %s, 시행 %s)" % (fhc_d["일련번호"], fhc_d["시행일자"]),
                      fhc_d["collected_at"], fhc_d["xml_sha256"])}
    import json
    for k, path, nm in (("gov_d", GOV_D_XML, "금융회사의 지배구조에 관한 법률 시행령(일련번호 290289, 시행 20261001, 10차 수집본)"),
                        ("gov", GOV_XML, "금융회사의 지배구조에 관한 법률(일련번호 277253, 시행 20260102, 10차 수집본)"),
                        ("ftc", FTC_XML, "독점규제 및 공정거래에 관한 법률(일련번호 290153, 시행 20261002, 10-02 현행 재확인본)"),
                        ("ftc_d", FTC_D_XML, "독점규제 및 공정거래에 관한 법률 시행령(일련번호 284737, 시행 20260324, 10차 수집본)")):
        m = json.load(open(path + ".meta.json", encoding="utf-8"))
        META[k] = (m.get("출처URL", ""), nm, m.get("fetched_at", ""), hashlib.sha256(X[k]).hexdigest())

    def law_name(k):
        return META[k][1].split("(")[0]

    def unit(k, jo, hang=None, ho=None, mok=None):
        u = L10.find_unit(X[k], jo, hang, ho, mok)
        if not u:
            raise SystemExit("조문 없음 %s %s" % (k, L10._loc(jo, hang, ho, mok)))
        return u

    def row(구분, k, jo, hang=None, ho=None, mok=None, text=None, note="", **kw):
        if text is None:
            title, text = unit(k, jo, hang, ho, mok)[1:]
        else:
            title = unit(k, jo)[1]
        loc = L10._loc(jo, hang, ho, mok)
        fx = sorted(set(re.sub(r"\s+", " ", x) for x in re.findall(L10.FOREIGN, text)))
        url, nm, when, sha = META[k]
        d = dict(구분=구분, 법령=law_name(k), 조문=loc, 조문제목=title, 원문=text,
                 **{"인용하는 조문": _refs(text), "외국 법인 언급": ("Y(%s)" % "|".join(fx)) if fx else "N"},
                 대조_상대조문="", 대조_상대원문="",
                 차이여부="", note=note, rcept_no_or_url=url, doc_name=nm,
                 page="%s (법령은 쪽 없음 — 조문 위치)" % loc, collected_at=when, source_sha256=sha)
        d.update(kw)
        return d

    out = []
    # (A) 은행법 시행령 제1조의4 — 항·호·목 전부(항 머리, 각 호, 각 목을 한 행씩)
    A = "은행법 시행령 제1조의4"
    u = unit("bank_d", "제1조의4")
    root = ET.fromstring(X["bank_d"])
    art = next(e for e in root.iter("조문단위") if L10.jo_label(e) == "제1조의4")
    for h in art.findall("항"):
        hn = L10.CIRCLED.get(L10._t(h, "항번호")[:1])
        out.append(row(A, "bank_d", "제1조의4", hn, text=L10._t(h, "항내용"), note="항 머리 글"))
        for ho in h.findall("호"):
            hon = int(re.match(r"(\d+)", L10._t(ho, "호번호")).group(1))
            out.append(row(A, "bank_d", "제1조의4", hn, hon, text=L10._t(ho, "호내용")))
            for mk in ho.findall("목"):
                out.append(row(A, "bank_d", "제1조의4", hn, hon, L10._t(mk, "목번호")[:1], text=L10._t(mk, "목내용")))
    # (B) 제1조의4 가 인용하는 조문(공정거래법·은행법·금융지주회사법)
    B = "제1조의4 가 인용하는 조문"
    cites = [("bank", "제2조", 1, 8, None, "제1항 머리 「법 제2조제1항제8호」"),
             ("ftc", "제2조", None, 11, None, "제1항제6호 「「독점규제 및 공정거래에 관한 법률」 제2조제11호에 따른 기업집단」"),
             ("ftc_d", "제5조", 1, 2, None, "제1항제1호 단서 「…시행령」 제5조제1항제2호가목에 따른 독립경영자」 — 가목의 상위 호 전체"),
             ("ftc_d", "제5조", 1, 2, "가", "제1항제1호 단서 「…제5조제1항제2호가목」"),
             ("ftc_d", "제4조", 1, 1, None, "제1항제6호 「같은 법 시행령 제4조제1항제1호 각 목」"),
             ("ftc_d", "제4조", 1, 2, None, "제1항제6호 「같은 항 제2호 각 목」"),
             ("fhc", "제2조", 1, 5, None, "제2항제2호 「「금융지주회사법」 제2조제1항제5호에 따른 은행지주회사」"),
             ("fhc", "제4조", 1, 2, None, "제2항제2호 「같은 법 제4조제1항제2호에 따른 자회사등」"),
             ("fhc", "제2조", 1, 1, None, "제2항제2호 「같은 법 제2조제1항제1호에 따른 금융기관」")]
    for k, jo, hg, ho, mk, where in cites:
        note = "인용한 곳: 은행법 시행령 제1조의4 %s" % where
        t = unit(k, jo, hg, ho, mk)[2]
        if k == "ftc_d" and jo == "제5조":
            note += (" · 기계 대조: 인용 단위에 「독립경영자」 낱말 %s(이 판의 용어는 「독립경영친족」 — 판단 필요)"
                     % ("있음" if "독립경영자" in t else "없음"))
        out.append(row(B, k, jo, hg, ho, mk, note=note))
    out.append(dict(row(B, "bank_d", "제1조의4", text="문서에 없음"), 조문="(그 밖의 인용 법률)", 원문="문서에 없음",
                    **{"인용하는 조문": "「사회기반시설에 대한 민간투자법」 제8조의2 | 「국가재정법」 제5조 | 「조세특례제한법」 제104조의31제1항 | "
                                     "「기업구조조정 촉진법」 | 「채무자 회생 및 파산에 관한 법률」 | 「자본시장과 금융투자업에 관한 법률」 | 법 제37조제2항",
                       "외국 법인 언급": ""}, page="",
                    note="제2항(특수관계인에서 제외) 이 인용하는 다른 법률 — 요청 범위(공정거래법 계열회사·기업집단·동일인관련자 등) 밖이라 원문 받지 않음"))
    # (C) 금융지주회사법·시행령
    C = "금융지주회사법·시행령"
    out.append(row(C, "fhc", "제2조", 1, 7, note="동일인 = 본인 + 특수관계인(시행령 제3조)"))
    out.append(row(C, "fhc", "제2조", 1, 9, note="대주주 = 「금융회사의 지배구조에 관한 법률」 제2조제6호에 따른 주주"))
    t34 = unit("fhc", "제34조", 1)[2]
    out.append(row(C, "fhc", "제34조", 1, note="대주주 정의 문구: 「해당 비은행지주회사의 대주주(그의 특수관계인을 포함한다. 이하 이 조에서 같다)」"
                                               if "그의 특수관계인을 포함한다" in t34 else "대주주 정의 문구 확인 필요"))
    for hg in (1, 2):
        out.append(row(C, "fhc_d", "제3조", hg, text=unit("fhc_d", "제3조", hg)[2],
                       note="특수관계인 = 본인과 「은행법 시행령」 제1조의4제1항 각 호의 관계에 있는 자" if hg == 1 else
                       "동일인 범위에서 제외(은행법 시행령 제1조의4제2항과 같은 꼴 — 아래 대조 참고)"))
    # (D) 지배구조법 연결(10차 수집본)
    D = "지배구조법 연결(10차 수집본)"
    out.append(row(D, "gov", "제2조", None, 6, note="대주주(최대주주·주요주주) 정의 — 최대주주는 특수관계인 포함"))
    out.append(row(D, "gov_d", "제3조", 2, note="은행·금융지주회사는 각각 은행법 시행령 제1조의4·금융지주회사법 시행령 제3조제1항의 특수관계인"))
    # (E) 은행법 시행령 제1조의4제1항 ↔ 지배구조법 시행령 제3조제1항 — 내용 기준 짝짓기(판단)
    E = "대조: 은행법 시행령 §1의4① ↔ 지배구조법 시행령 §3①"
    PAIRS = [  # (은행 호, [(지배 호, 목)], 판단 note)
        (None, [(None, None)], "항 머리: 둘 다 「본인과 다음 각 호의 … 관계에 있는 자(특수관계인)」. 지배구조법은 본인이 개인(1호)·법인·단체(2호)로 나눠 적고 은행법은 나누지 않음"),
        (1, [(1, None), (1, "가"), (1, "나"), (1, "다")], "같은 점: 배우자·6촌 이내 혈족·4촌 이내 인척, 공정거래법 시행령 제5조제1항제2호가목 독립경영자 제외 단서. "
                                                       "다른 점: 지배구조법은 배우자에 사실혼 포함(가목 괄호)"),
        (None, [(1, "라"), (1, "마"), (1, "바")], "지배구조법에만: 양자의 생가 직계존속, 양자·배우자와 양가 직계비속, 혼인 외 출생자의 생모 — 은행법 제1조의4제1항에는 이 관계가 없음"),
        (4, [(1, "사"), (2, "가")], "부분 대응: 은행법 4호(본인 등에게 고용된 사람·임원, 개인 사용자의 경우 그 재산으로 생계를 유지하는 사람) ↔ "
                                 "지배구조법 1호 사목(생계 유지·생계를 함께 하는 사람)·2호 가목(임원). 지배구조법에는 「고용된 사람」 일반이 없음"),
        (2, [(1, "아"), (1, "자")], "부분 대응: 은행법 2호는 비영리법인·조합·단체(임원 과반수·50% 이상 출연·설립자), 지배구조법 1호 아·자목은 법인·단체에 "
                                 "30% 이상 출자 또는 사실상 영향력 — 기준(과반수·50% 출연 ↔ 30% 출자·영향력)이 다름"),
        (3, [(1, "아"), (2, "라")], "부분 대응: 은행법 3호는 의결권 있는 주식 30% 이상 또는 최다수 주식소유자로 경영 참여하는 회사, 지배구조법은 30% 이상 출자 "
                                 "또는 임원 임면 등 사실상 영향력 — 「최다수 주식소유자로 경영 참여」 ↔ 「사실상 영향력」"),
        (5, [(1, "자"), (2, "라")], "부분 대응: 은행법 5호는 본인 및 1~4호의 자가 30% 이상 소유·최다수 주식소유자로 경영 참여하는 회사(2단계)"),
        (6, [(2, "나")], "같은 점: 공정거래법상 기업집단·계열회사로 연결. 다른 점: 은행법 6호는 본인이 계열주(기업집단을 지배하는 자)일 때 그 기업집단 소속 회사와 "
                         "임원이며 「…요건에 해당하는 외국법인을 포함한다」고 외국법인을 명시. 지배구조법 2호 나목은 본인이 법인일 때 「공정거래법에 따른 계열회사 및 그 임원」"
                         "으로 외국 법인 언급 없음"),
        (7, [], "은행법에만: 본인이 계열주의 친족(1·2호 관계)이거나 기업집단 소속 회사 임원일 때 그 계열주의 기업집단 소속 회사와 임원"),
        (8, [(2, "나")], "같은 점: 본인이 기업집단 소속 회사면 같은 기업집단 소속 회사·임원 ↔ 계열회사·임원. 은행법 8호에는 외국법인 문구 없음(「이하 이 조에서 같다」로 "
                         "6호 괄호의 외국법인 포함이 「기업집단에 속하는 회사」에 이어지는지는 판단)"),
        (9, [], "은행법에만: 합의·계약 등으로 은행 발행주식의 의결권을 공동으로 행사하는 자"),
        (None, [(2, "다")], "지배구조법에만(직접 대응 없음): 본인(법인)에게 30% 이상 출자하거나 사실상 영향력을 행사하는 개인·법인·단체와 그 임원 — 은행법 제1조의4제1항에는 "
                            "「본인에게 출자한 자」를 따로 적은 호가 없음(기업집단이면 6~8호)"),
    ]
    for bho, gl, nt in PAIRS:
        btxt = unit("bank_d", "제1조의4", 1, bho)[2] if bho else unit("bank_d", "제1조의4", 1)[2].split("\n")[0]
        gtxts, glocs = [], []
        for gho, gmk in gl:
            t = unit("gov_d", "제3조", 1, gho, gmk)[2] if gho else unit("gov_d", "제3조", 1)[2].split("\n")[0]
            if gho and not gmk:
                t = t.split("\n")[0]                 # 호 머리 줄만(각 목은 따로 짝)
            gtxts.append(t)
            glocs.append(L10._loc("제3조", 1, gho, gmk))
        if bho is None and gl and gl[0][0] is not None:
            base = row(E, "gov_d", "제3조", 1, gl[0][0], gl[0][1], text="\n".join(gtxts))
            base.update(조문="(은행법 대응 없음)", 원문="문서에 없음", 대조_상대조문=" · ".join(glocs),
                        대조_상대원문="\n".join(gtxts), 차이여부="지배구조법에만", note=nt + " · 짝짓기는 내용 기준(판단)",
                        **{"인용하는 조문": _refs("\n".join(gtxts))})
            out.append(base)
            continue
        d = row(E, "bank_d", "제1조의4", 1, bho, text=btxt)
        same = gtxts and _nows(btxt) == _nows("\n".join(gtxts))
        d.update(대조_상대조문=" · ".join(glocs) or "(지배구조법 대응 없음)",
                 대조_상대원문="\n".join(gtxts) or "문서에 없음",
                 차이여부="같음" if same else ("은행법에만" if not gl else "다름(부분 대응)"),
                 note=nt + " · 짝짓기는 내용 기준(판단)")
        out.append(d)
    write_csv(DEF_CSV, DEF_COLS, out)
    print("특수관계인_정의대조 %d행 — %s · 외국 법인 언급 Y %d" % (
        len(out), ", ".join("%s %d" % (g, sum(1 for x in out if x["구분"] == g)) for g in dict.fromkeys(x["구분"] for x in out)),
        sum(x["외국 법인 언급"].startswith("Y") for x in out)))
