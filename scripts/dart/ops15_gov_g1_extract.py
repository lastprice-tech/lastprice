# -*- coding: utf-8 -*-
"""15차 — 지배구조 및 보수체계 연차보고서(g1: KB·신한·하나·우리·NH농협) 에서 작업 A·B 조각 행을 뽑는다.

    python3 scripts/dart/ops15_gov_g1_extract.py hits     # 키워드 줄 모으기 → 작업 기록(검토용)
    python3 scripts/dart/ops15_gov_g1_extract.py build    # 조각 CSV·원문 md 쓰기

원문:
  FY2019~2023(공시연도 2020~2024): ops15_gov_g1.py 가 받은 PDF 의 쪽 텍스트 md(dart_out/text/ops15/연차보고서__<회사>__<연도>__<유형>.md,
    「## p.N」= PDF 쪽). 출처 url·fetched_at 은 dart_out/ops15/gov15_g1_work/download.json.
  FY2024·2025(공시연도 2025·2026): 6차 섹션 글(dart_out/ops15/kit56/연차보고서_섹션.csv). url·fetched_at 은
    handoff/연차보고서_파일목록.csv. page = 「시작페이지 N 섹션 안」. FY2025 는 13차 텍스트(같은 PDF, sha256 같음)의 쪽을 note 에 덧붙임.
글자는 원문 그대로 옮긴다. PDF 줄바꿈만 붙여 쓴다(줄 끝 공백은 원문대로). 웹 요청·API 키 없음.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
csv.field_size_limit(10 ** 9)

WORK = os.path.join("dart_out", "ops15", "gov15_g1_work")
SEC_CSV = os.path.join("dart_out", "ops15", "kit56", "연차보고서_섹션.csv")
FILELIST = os.path.join("handoff", "연차보고서_파일목록.csv")
T13_ZIP = os.path.join("handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
G1 = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주", "NH농협금융지주"]
KST = timezone(timedelta(hours=9))
KW = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
KW_RE = re.compile("|".join(KW))
# 「전적」 오탐: 사전적·전적으로·전적인(全的) — 전적(轉籍) 아님 (판단)
FALSE_RE = re.compile(r"사\s?전적|전적으로|전적인|전적합|전적\s*지원")


def kst(s):
    """'2026-09-22T02:37:14+0000' → '2026-09-22T11:37:14+09:00'."""
    if not s:
        return ""
    if s.endswith("+0000"):
        d = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S+0000").replace(tzinfo=timezone.utc)
        return d.astimezone(KST).isoformat(timespec="seconds")
    return s


# ---------------------------------------------------------------- 문서 읽기
def load_docs():
    docs = []
    # FY2019~2023 — 새로 받은 PDF
    for r in json.load(open(os.path.join(WORK, "download.json"), encoding="utf-8")):
        if not r.get("text_path"):
            continue
        L = open(r["text_path"], encoding="utf-8").read().split("\n")
        lines, pg = [], 0
        for l in L:
            m = re.match(r"## p\.(\d+)", l)
            if m:
                pg = int(m.group(1))
                lines.append((pg, None))         # 쪽 표지
                continue
            if pg:
                lines.append((pg, l))
        docs.append(dict(co=r["회사"], year=int(r["공시연도"]), fy=int(r["공시연도"]) - 1, kind=r["공시유형"], src="pdf",
                         title=r["제목"], url=r["실제_url"], list_url=r["파일_url"], board=r["게시판_url"],
                         fetched_at=r["fetched_at"], sha256=r["sha256"], text_path=r["text_path"],
                         file=os.path.basename(r["저장경로"]), lines=lines, pages=r["쪽수"]))
    # FY2024·2025 — 6차 섹션 글
    fl = {}
    for r in csv.DictReader(open(FILELIST, encoding="utf-8-sig")):
        if r["지주명"] in G1 and r["공시연도"]:
            fl[(r["지주명"], r["공시연도"], r["공시유형"])] = r
    secs = {}
    for r in csv.DictReader(open(SEC_CSV, encoding="utf-8-sig")):
        if r["지주명"] not in G1:
            continue
        k = (r["지주명"], r["공시연도"], r["공시유형"])
        secs.setdefault(k, []).append(r)
    for k, rows in sorted(secs.items()):
        f = fl[k]
        # 섹션순번·chunk_seq 순서로 이어 붙임
        bysec = {}
        for r in rows:
            bysec.setdefault(int(r["섹션순번"]), []).append(r)
        units = []
        for sn in sorted(bysec):
            ch = sorted(bysec[sn], key=lambda x: int(x["chunk_seq"] or 0))
            body = "".join(c["본문"] for c in ch)
            units.append(dict(sn=sn, no=ch[0]["섹션번호"], title=ch[0]["섹션제목_원문"], start=ch[0]["시작페이지"],
                              src=ch[0]["섹션출처"], body=body, sha=ch[0]["sha256"]))
        docs.append(dict(co=k[0], year=int(k[1]), fy=int(k[1]) - 1, kind=k[2], src="sec6", title=f["제목"], url=f["url"],
                         list_url=f["url"], board="", fetched_at=kst(f["fetched_at"]), sha256=f["sha256"],
                         text_path=SEC_CSV, file=f["파일명"], units=units, pages=f["페이지수"]))
    return docs



# ---------------------------------------------------------------- 문장 잘라내기(줄 단위)
END_RE = re.compile(r"(다\.|요\.|음\.|함\.|됨\.|임\.|\.|(임|다|음|함)\))\s*$")
BULLET_RE = re.compile(r"^\s*([-*•·□■○●▶◦]|주\s?\d+\)|\(?\d{1,2}\)|[①-⑳]|[가-하]\.|\([가-하]\)|\d{1,2}\.|결의-|보고-|\([가-하IVX]+\))\s*")


def sentence(lines, i, maxback=4, maxfwd=4):
    """i 번째 줄이 든 문장 범위(앞뒤 줄)를 잡는다. (이어 붙인 글, 시작 줄, 끝 줄)."""
    s = i
    for _ in range(maxback):
        if s == 0:
            break
        prev = lines[s - 1]
        if prev is None or not prev.strip() or END_RE.search(prev) or BULLET_RE.match(lines[s] or "") \
                or len(prev.strip()) < 20:
            break
        s -= 1
    e = i
    for _ in range(maxfwd):
        cur = lines[e]
        if cur is None or END_RE.search(cur) or e + 1 >= len(lines):
            break
        if BULLET_RE.match(cur) and len(cur.strip()) < 45:
            break                     # 「바) …」 같은 짧은 머리 줄은 다음 줄과 잇지 않음
        nxt = lines[e + 1]
        if nxt is None or not nxt.strip() or BULLET_RE.match(nxt) or nxt.strip().startswith("(") \
                or (len(nxt.strip()) < 12 and not nxt.strip().endswith(".")):
            break
        e += 1
    txt = "".join(lines[j] for j in range(s, e + 1) if lines[j] is not None)
    return txt.strip(), s, e


REG_PAGE_RE = re.compile(r"제\s?\d+\s?조\s?\(")
BOILER = [  # 사외이사·비상임이사 자격요건/겸직 여부 문구 (판단: 지주 인력 서술 아님)
    "겸직 여부", "겸직여부", "겸직사실", "겸직 사실", "겸직상황", "겸직 상황", "겸직하지 않", "겸직한 사실", "겸직사항 없음",
    "겸직 사항 없음", "현재 겸직 업무", "비상임감사 겸직", "본인이 겸직하고 있는 외부 기관", "겸직 제한",
]




# ================================================================ 글 흐름(segment)
# pdf 문서: 한 덩어리(쪽 표지 줄은 None). 6차: 섹션마다 한 덩어리.
def segments(d):
    if d["src"] == "pdf":
        texts = [l for (_, l) in d["lines"]]
        pages = [p for (p, _) in d["lines"]]
        return [dict(texts=texts, pages=pages, unit=None, sec=None, start=None)]
    out = []
    for u in d["units"]:
        t = [x for x in u["body"].split("\n") if x.strip()]     # 6차 레이아웃 글은 줄 사이마다 빈 줄 — 빼고 이음
        out.append(dict(texts=t, pages=[u["start"]] * len(t), unit=u["sn"], sec="%s %s" % (u["no"], u["title"]),
                        start=u["start"]))
    return out


def fulltext(seg):
    """줄을 \\n 으로 이은 글과 줄마다 시작 오프셋."""
    offs, parts, o = [], [], 0
    for t in seg["texts"]:
        offs.append(o)
        s = "" if t is None else t
        parts.append(s)
        o += len(s) + 1
    return "\n".join(parts), offs


def line_of(offs, pos):
    import bisect
    return max(0, bisect.bisect_right(offs, pos) - 1)


def join(txt, how):
    """여러 줄 원문 → 한 칸: prose 는 줄바꿈만 없앰(줄 끝 공백은 그대로), table 은 「 | 」로 이음."""
    lines = [l for l in txt.split("\n")]
    if how == "table":
        return " | ".join(l.strip() for l in lines if l.strip())
    return "".join(lines).strip()


def rx(phrase):
    """글자 사이 공백·줄바꿈을 허용하는 정규식(6차 레이아웃 글·PDF 줄바꿈 대응). 글자는 그대로."""
    chars = [c for c in phrase if not c.isspace()]
    return r"\s*".join(re.escape(c) for c in chars)


# ================================================================ 키워드·문장
TRUE_JEONJEOK = re.compile(r"(?<![가-힣])전적(?!으로|인|합)")


def kws_in(t):
    out = [k for k in ("겸직", "파견", "출향", "전출", "겸무") if k in t]
    if TRUE_JEONJEOK.search(t) and not re.search(r"사\s전적합", t):
        out.append("전적")
    return out


SENT_END = re.compile(r"(?:다|[음함임됨])\.(?=\s|$)|(?:임|다)\)(?=\s|$)")


def split_sents(joined):
    """이어 붙인 글을 문장으로 나눈다(「…다.」「…음/함/임/됨.」 뒤에서). 원문 부분 문자열만 돌려줌."""
    out, st = [], 0
    for m in SENT_END.finditer(joined):
        out.append(joined[st:m.end()])
        st = m.end()
    if st < len(joined):
        out.append(joined[st:])
    return [s.strip() for s in out if s.strip()]


def collect_hits(d):
    """문서의 키워드 문장(중복 없이)."""
    res, seen = [], set()
    for si, seg in enumerate(segments(d)):
        texts = seg["texts"]
        for i, l in enumerate(texts):
            if not l or not KW_RE.search(l):
                continue
            def short(x):
                return bool(x) and bool(x.strip()) and len(x.strip()) < 30 and not END_RE.search(x)
            prev_ = texts[i - 1] if i > 0 else None
            next_ = texts[i + 1] if i + 1 < len(texts) else None
            if short(l) and (short(prev_) or short(next_)):
                # 표 칸(짧은 줄): 앞의 짧은 칸 4개까지를 같은 행으로 보고 「 | 」로 이음 (판단).
                # 칸이 「가.」「3)」 같은 머리로 시작하면 앞 칸은 붙이지 않음
                s = i
                while (not BULLET_RE.match(texts[i])) and s > 0 and (s > i - 4) and short(texts[s - 1]) \
                        and not BULLET_RE.match(texts[s - 1]):
                    s -= 1
                e = i
                pieces = [" | ".join(texts[j].strip() for j in range(s, e + 1) if texts[j] and texts[j].strip())]
                mode = "table"
            else:
                _, s, e = sentence(texts, i)
                joined = "".join(texts[j] for j in range(s, e + 1) if texts[j] is not None)
                pieces = split_sents(joined)
                mode = "prose"
            for snt in pieces:
                k = kws_in(snt)
                if not k:
                    continue
                key = (si, re.sub(r"\s+", "", snt))
                if key in seen:
                    continue
                seen.add(key)
                res.append(dict(seg=si, s=s, e=e, i=i, page=seg["pages"][i], sec=seg["sec"], sent=snt, kws=k,
                                line=l, mode=mode))
    # 다른 문장 안에 통째로 든 짧은 문장은 뺌(같은 덩어리·같은 쪽)
    keep = []
    for h in res:
        nh = norm(h["sent"])
        if any(o is not h and o["seg"] == h["seg"] and o["page"] == h["page"] and nh in norm(o["sent"])
               and len(norm(o["sent"])) > len(nh) for o in res):
            continue
        keep.append(h)
    return keep


# ================================================================ 분류
BOILER2 = BOILER + ["소극적 요건", "소극적 자격요건", "결격요건", "직무공정성", "비상임이사의 요건", "적극적 요건",
                    "다른 회사의 사외이사", "자격요건", "겸직 중인 법인"]


def is_reg(h, d, segs):
    t = h["sent"]
    if REG_PAGE_RE.search(t):
        return True
    if re.search(r"[^니]다\.\s*$", t) and not re.search(r"니다\.\s*$", t):
        return True                          # 「…한다.」 꼴 = 규정·윤리강령 문체 (판단)
    if re.match(r"^\s*\d+\.\s*“", t):
        return True
    if d["src"] == "pdf":
        seg = segs[h["seg"]]
        pg = seg["pages"][h["i"]]
        n = sum(1 for p, l in zip(seg["pages"], seg["texts"]) if p == pg and l and REG_PAGE_RE.search(l))
        if n >= 3:
            return True
    else:
        if re.search(r"규정|규범|정관|준칙|강령", h["sec"] or "") and re.match(r"^\s*([①-⑳]|제\s?\d+\s?조|\d+\.)", t):
            return True
    return False


def category(h, d, segs):
    t = h["sent"]
    k = set(h["kws"])
    if not k:
        return "X오탐"
    nt = norm(t)
    if any(norm(b) in nt for b in BOILER2):
        return "X자격요건"
    if len(re.findall(r"\d{4}\.?\d{0,2}\s*~", t)) >= 2 or re.search(r"\(\s*파견\s*\)\s*부장", t):
        return "X경력"
    if is_reg(h, d, segs):
        return "X규정"
    if k == {"파견"} and re.search(r"前|現|역임|OECD|경력|전문성|적격성|추천 이유|추천이유|재직|\d{4}\s*년?\s*\d{0,2}\s*월?\s*~", t):
        return "X경력"
    if re.search(r"위원장.{0,40}겸직하며", re.sub(r"\s+", " ", t)):
        return "X이사회직책"
    return "B"


CAT_NOTE = {
    "X오탐": "「전적」이 사전적·도전적·발전적·전적으로 등 다른 낱말의 일부(轉籍 아님)",
    "X자격요건": "사외이사·비상임이사 자격요건·겸직 여부·결격 문구(지주 인력 서술 아님)",
    "X규정": "정관·규정·내부규범·윤리강령 조문(「…한다.」 꼴 또는 조문 쪽)",
    "X경력": "이사·후보의 경력 서술 속 「파견」(지주 인력 서술 아님)",
    "X이사회직책": "이사회 내 위원장 겸임 서술(회사 간 겸직 아님)",
}


# ================================================================ 작업 A — 개별 겸직 문장(손으로 고른 목록)
def A(co, year, src, person="", birth="", title="", pairs=(), join_how="prose", reason=None, extra=None,
      near_line=None, unit=None, note="", since="", fulltime="", registered=""):
    return dict(co=co, year=year, src=src, person=person, birth=birth, title=title, pairs=list(pairs), join=join_how,
                reason=reason, extra=extra, near_line=near_line, unit=unit, note=note, since=since, fulltime=fulltime,
                registered=registered)


ANY = r"[\s\S]{0,400}?"
SH_REASON = rx("창립 이래 당사는 그룹 전략의 일관성 유지") + ANY + rx("비상임이사로 선임하고 있습니다.")
SH_REASON2 = rx("창립이래 당사는") + ANY + rx("선임하고 있습니다.")
NOTE_REASON = ("(판단) reason_text 는 같은 문단의 비상임이사 선임 이유 문장(원문 그대로) — 은행장의 지주 비상임이사 겸직에 "
               "대한 서술로 보아 옮김")
NOTE_OD = "사외이사 후보 추천 관련 사항 — 후보 본인 소명 「3) 현재 겸직 업무」 칸(표 칸은 「 | 」로 이음)"


def od(co, year, line, text, person, birth, pairs, unit=None, ahead=None, note=""):
    """사외이사 후보 본인 소명 「현재 겸직 업무」 칸."""
    src = rx("3) 현재 겸직 업무") + r"\*?\s*" + r"\s*".join(rx(t) for t in text)
    if ahead:
        src += r"(?=[\s\S]{0,900}?" + rx(ahead) + ")"
    n = NOTE_OD + ("; birth_ym 은 출생연도만(월 없음)" if birth else "") + ("; " + note if note else "") + \
        "; (판단) concurrent_company·title 은 원문 한 칸을 회사·직위로 나눔" + \
        ("; 원문 「… 외 겸직사항 없음」" if any("외 겸직사항 없음" in t for t in text) else "")
    return A(co, year, src, person=person, birth=birth, title="사외이사 후보", pairs=pairs, join_how="table",
             near_line=line, unit=unit, note=n)


A_SPECS = [
    # ── KB금융지주 FY2019: 이사회 활동내역 보고 안건(성명 없음)
    A("KB금융지주", 2020, rx("나. 지주회사 집행임원 선임 보고 : 데이터 총괄 집행임원(KB국민은행 데이터전략본부 전무, "
                           "KB국민카드 데이터전략본부 전무 겸직) 선임 보고"),
      title="데이터 총괄 집행임원", pairs=[("KB국민은행", "데이터전략본부 전무"), ("KB국민카드", "데이터전략본부 전무")],
      note="이사회 활동내역의 보고 안건(지주회사 집행임원 선임 보고) — 원문에 성명 없음"),
    A("KB금융지주", 2020, rx("라. 지주회사 집행임원 선임 보고 : 연금본부장(KB국민은행 연금사업본부장, KB증권 연금기획부장, "
                           "KB손해보험 연금기획부장 겸직) 선임 보고"),
      title="연금본부장", pairs=[("KB국민은행", "연금사업본부장"), ("KB증권", "연금기획부장"), ("KB손해보험", "연금기획부장")],
      note="이사회 활동내역의 보고 안건(지주회사 집행임원 선임 보고) — 원문에 성명 없음"),
    # ── 신한금융지주: 은행장의 지주 비상임이사 겸직
    *[A("신한금융지주", y, rx("진옥동 이사는 신한은행 은행장을 겸직하고 있습니다."), person="진옥동", title="비상임이사",
        pairs=[("신한은행", "은행장")], reason=SH_REASON,
        note="이사회 구성 — 「이사 진옥동 (비상임이사)」 절. " + NOTE_REASON) for y in (2020, 2021, 2022)],
    A("신한금융지주", 2023, rx("진옥동 이사는 2022년 말까지 신한은행 은행장을 겸직하였습니다."), person="진옥동",
      title="비상임이사", pairs=[("신한은행", "은행장")], reason=SH_REASON, since="",
      note="이사회 구성 — 「이사 진옥동 (비상임이사)」 절. 원문 「2022년 말까지 … 겸직하였습니다」. " + NOTE_REASON),
    *[A("신한금융지주", y, rx("정상혁 이사는 신한은행 은행장을 겸직하고 있으며,") + ANY + rx("선임하고 있습니다."),
        person="정상혁", title="비상임이사", pairs=[("신한은행", "은행장")], reason=SH_REASON2,
        note=("이사회 구성 — 「이사 정상혁 (비상임이사)」 절. " if y == 2024 else "6차 섹션 「라. 이사회 및 이사에 대한 평가」 글. ")
        + "(판단) reason_text 는 같은 문장의 뒷부분(원문 그대로)") for y in (2024, 2025, 2026)],
    A("신한금융지주", 2020, rx("GMS사업부문겸직 부사장 장동기(임기 1년)"), person="장동기", title="부사장",
      pairs=[("문서에 없음", "GMS사업부문")],
      note="이사회운영위원회 「이사 아닌 경영진 신규 선임」 추천 결과 목록. (판단) 원문 「GMS사업부문겸직 부사장」을 지주 부사장의 "
           "GMS사업부문 겸직으로 읽음 — 겸직 회사명은 원문에 없음. 같은 날 이사회 결의 문장(p.25 「…겸직 사업부문 활성화를 위해 "
           "경영진 신규 선임…」)은 B 조각에 있음"),
    A("신한금융지주", 2020, rx("GIB사업부문겸직 부사장 정운진(임기 1년)"), person="정운진", title="부사장",
      pairs=[("문서에 없음", "GIB사업부문")],
      note="이사회운영위원회 「이사 아닌 경영진 신규 선임」 추천 결과 목록. (판단) 원문 「GIB사업부문겸직 부사장」을 지주 부사장의 "
           "GIB사업부문 겸직으로 읽음 — 겸직 회사명은 원문에 없음"),
    A("신한금융지주", 2021, rx("결의-나.이사 아닌 경영진 선임의 건 : 지주회사와 신한DS 대표이사를 겸직하는 "
                             "그룹디지털부문장을 선임하였습니다."),
      title="그룹디지털부문장", pairs=[("신한DS", "대표이사")], note="이사회 활동내역(결의 안건) — 원문에 성명 없음"),
    od("신한금융지주", 2020, 4323, ["성균관대학교 외 겸직사항 없음"], "성재호", "1960", [("성균관대학교", "")]),
    od("신한금융지주", 2020, 5263, ["(유)프리메르코리아 외 겸직사항 없음"], "히라카와 유키", "1960", [("(유)프리메르코리아", "")]),
    od("신한금융지주", 2021, 5295, ["(유)프리메르코리아 외 겸직사항 없음"], "히라카와 유키", "1960", [("(유)프리메르코리아", "")]),
    od("신한금융지주", 2021, 5504, ["㈜CYS 대표이사 외 겸직사항 없음"], "최경록", "1966", [("㈜CYS", "대표이사")]),
    od("신한금융지주", 2021, 5621, ["홍익대학교 외 겸직사항 없음"], "윤재원", "1970", [("홍익대학교", "")]),
    od("신한금융지주", 2021, 5727, ["㈜페도라 외 겸직사항 없음"], "진현덕", "1955", [("㈜페도라", "")]),
    od("신한금융지주", 2022, 4139, ["성균관대학교 외 겸직사항 없음"], "성재호", "1960", [("성균관대학교", "")]),
    od("신한금융지주", 2022, 5002, ["㈜CYS 대표이사 외 겸직사항 없음"], "최경록", "1966", [("㈜CYS", "대표이사")]),
    od("신한금융지주", 2022, 5244, ["First Bridge Strategy Ltd. CEO 외 겸직사항 없음"], "허용학", "1958",
       [("First Bridge Strategy Ltd.", "CEO")]),
    od("신한금융지주", 2023, 4974, ["First Bridge Strategy Ltd. CEO 외 겸직사항 없음"], "허용학", "1958",
       [("First Bridge Strategy Ltd.", "CEO")]),
    od("신한금융지주", 2023, 5211, ["㈜페도라 외 겸직사항 없음"], "진현덕", "1955", [("㈜페도라", "")]),
    od("신한금융지주", 2023, 5334, ["홍익대학교 외 겸직사항 없음"], "윤재원", "1970", [("홍익대학교", "")],
       note="같은 문서 감사위원 후보 부분(p.82)에도 같은 칸"),
    od("신한금융지주", 2023, 5443, ["오사카상업대학교 외 겸직사항 없음"], "김조설", "1957", [("오사카상업대학교", "")]),
    od("신한금융지주", 2023, 5521, ["성균관대학교 외 겸직사항 없음"], "성재호", "1960", [("성균관대학교", "")]),
    od("신한금융지주", 2023, 5619, ["변호사법인 오르비스 외 겸직사항 없음"], "배훈", "1953", [("변호사법인 오르비스", "")]),
    # ── 하나금융지주: 리스크관리집행위원회 구성 표 + 주5
    *[A("하나금융지주", y, rx(nm) + r"\s*" + rx(ttl + "주5") + r"\s*" + rx(dt) + r"\s*" + rx("위원장"), person=nm, title=ttl,
        pairs=[("하나은행", cttl)], join_how="table", extra=rx("주5) 하나은행 " + cttl + " 겸직"),
        note="리스크관리집행위원회 구성 표의 행과 각주 주5(표 칸은 「 | 」, 행과 각주는 「 … 」로 이음). 표의 선임일은 위원 선임일"
             "(주4 「최초 회의참석일 기준」) — 겸직 시작일 아님")
      for (y, nm, ttl, dt, cttl) in [
          (2020, "황효상", "하나금융지주 리스크관리 담당임원", "2014.2.26.", "리스크관리담당임원"),
          (2021, "황효상", "하나금융지주 리스크관리 담당임원", "2014.2.26.", "리스크관리담당임원"),
          (2022, "황효상", "하나금융지주 리스크관리 담당임원", "2014.02.26.", "리스크관리담당임원"),
          (2023, "김주성", "하나금융지주 리스크관리 담당 임원", "2022.01.25.", "리스크관리 담당 임원"),
          (2024, "김주성", "하나금융지주 리스크관리 담당 임원", "2022. 1. 25.", "리스크관리 담당 임원")]],
    A("하나금융지주", 2022, rx("그룹임원후보추천위원회가 하나은행 임원후보추천위원회에 추천한") + ANY +
      rx("박성호 후보를 비상임이사로 추천하였습니다."), person="박성호", title="비상임이사 후보",
      pairs=[("하나은행", "대표이사 은행장")],
      reason=rx("그룹 내 회사의 비중 및 이익 측면에서") + ANY + rx("판단하여"),
      note="그룹임원후보추천위원회 활동(비상임이사 후보 추천). (판단) reason_text 는 같은 문장 가운데 추천 판단 부분(원문 그대로) "
           "— 원문이 「은행장이 지주회사 비상임이사를 겸직하는 것이 …」라고 직접 말함"),
    # ── 우리금융지주
    A("우리금융지주", 2020, rx("1월 11일 1차 임시이사회에서는 일부 임원에 대해서는 업무 효율성을 위해 지주사와 일부 계열사를 "
                             "겸직하는 것을 검토해볼 것을 요청하였으며, 이는 그룹사 임원 겸직을 통한 경영효율성 제고로 이어지게 "
                             "되었습니다."),
      title="문서에 없음", pairs=[("문서에 없음", "")],
      reason=rx("1월 11일 1차 임시이사회에서는 일부 임원에 대해서는 업무 효율성을 위해 지주사와 일부 계열사를 겸직하는 것을 "
                "검토해볼 것을 요청하였으며, 이는 그룹사 임원 겸직을 통한 경영효율성 제고로 이어지게 되었습니다."),
      note="사외이사 활동 서술. (판단) 개별 겸직 건이 아니라 이사회 요청 서술 — 원문 「일부 임원」「지주사와 일부 계열사를 겸직」. "
           "같은 문장을 reason_text 에도 옮김"),
    A("우리금융지주", 2022, rx("김홍태 이사는 비상임이사로서") + ANY + rx("역임하였습니다."), person="김홍태",
      title="비상임이사", pairs=[("예금보험공사", "인사지원부 (파견)부장")],
      note="이사회 구성 — 이사별 서술. 원문 「現 예금보험공사 인사지원부 (파견)부장으로 재직 중」. 같은 문서 p.22 이사 현황 표에도 "
           "「예금보험공사 인사지원부 (파견) 부장」"),
    od("우리금융지주", 2023, 2364, ["우리은행 사외이사", "삼성꿈장학재단 이사장"], "노성태", "1946",
       [("우리은행", "사외이사"), ("삼성꿈장학재단", "이사장")]),
    od("우리금융지주", 2023, 2534, ["우리은행 사외이사", "연세대학교 경영학과 명예교수"], "박상용", "1951",
       [("우리은행", "사외이사"), ("연세대학교", "경영학과 명예교수")],
       note="(판단) PDF 글 순서상 이 표가 다음 후보(윤인섭) 인적사항 뒤에 나오나, 표 위 「③ 사외이사 후보 본인 소명」 머리가 "
            "박상용 절에 있고 p.177 이사 약력 표에도 박상용 「연세대학교 경영학과 명예교수」라 박상용으로 봄"),
    od("우리금융지주", 2023, 2772, ["우리은행 사외이사"], "정찬형", "1956", [("우리은행", "사외이사")]),
    od("우리금융지주", 2023, 2874, ["신영증권 고문"], "신요환", "1962", [("신영증권", "고문")]),
    od("우리금융지주", 2023, 2948, ["아이엠엠인베스트먼트(주) 대표이사"], "장동우", "1967", [("아이엠엠인베스트먼트(주)", "대표이사")]),
    od("우리금융지주", 2023, 3136, ["법무법인(유) 세종 파트너 변호사"], "송수영", "1980", [("법무법인(유) 세종", "파트너 변호사")]),
    od("우리금융지주", 2024, 4227, ["우리은행 사외이사"], "정찬형", "1956", [("우리은행", "사외이사")]),
    od("우리금융지주", 2024, 4433, ["아이엠엠인베스트먼트(주) 대표이사"], "지성배", "1967", [("아이엠엠인베스트먼트(주)", "대표이사")]),
    od("우리금융지주", 2025, None, ["우리은행 사외이사"], "정찬형", "auto", [("우리은행", "사외이사")],
       unit="사외이사 후보 추천", ahead="정찬형 후보자에 대한"),
    od("우리금융지주", 2025, None, ["서울대학교 사회과학대학 언론정보학과 교수"], "이은주", "auto",
       [("서울대학교", "사회과학대학 언론정보학과 교수")], unit="사외이사 후보 추천", ahead="이은주 후보자에 대한"),
    od("우리금융지주", 2025, None, ["동국대학교 경제학과 부교수", "우리벤처파트너스(주) 사외이사"], "박선영", "auto",
       [("동국대학교", "경제학과 부교수"), ("우리벤처파트너스(주)", "사외이사")], unit="사외이사 후보 추천",
       ahead="박선영 후보자에 대한"),
    od("우리금융지주", 2026, None, ["우리아메리카은행 사외이사"], "윤인섭", "auto", [("우리아메리카은행", "사외이사")],
       unit="사외이사 후보 추천", ahead="윤인섭 후보자에 대한"),
    od("우리금융지주", 2026, None, ["서울대학교 국제대학원 교수"], "이영섭", "auto", [("서울대학교", "국제대학원 교수")],
       unit="사외이사 후보 추천", ahead="이영섭 후보자에 대한"),
]


# ================================================================ 찾기 도구
def norm(t):
    """비교용: 공백·줄바꿈과 표 칸 구분 「|」를 뺀 글."""
    return re.sub(r"[\s|]+", "", t or "")


class Doc:
    """문서 하나: 찾기·쪽·절 경계."""

    def __init__(self, d):
        self.d = d
        if d["src"] == "pdf":
            md = open(d["text_path"], encoding="utf-8").read()
            self.md_lines = md.split("\n")
            self.head = next(i for i, l in enumerate(self.md_lines) if l.startswith("## p.1"))
            self.text, self.offs = fulltext(dict(texts=self.md_lines))
            pg, self.pg = 0, []
            for l in self.md_lines:
                m = re.match(r"## p\.(\d+)", l)
                if m:
                    pg = int(m.group(1))
                self.pg.append(pg)
            self.ntext = norm(self.text)
        else:
            self.ntext = norm("\n".join(u["body"] for u in d["units"]))

    # pdf: md 줄 번호(0부터) → 쪽
    def find(self, pattern, near_line=None, unit=None):
        """(원문 글, 쪽 칸, 절 정보) 또는 None."""
        d = self.d
        if d["src"] == "pdf":
            if near_line:
                a = self.offs[max(0, near_line - 6)]
                b = self.offs[min(len(self.offs) - 1, near_line + 8)]
                m = re.compile(pattern).search(self.text, a, b)
            else:
                m = re.compile(pattern).search(self.text)
            if not m:
                return None
            li = line_of(self.offs, m.start())
            return dict(raw=m.group(0), page="p.%d" % self.pg[li], line=li, unit=None)
        for u in d["units"]:
            if unit and unit not in u["title"]:
                continue
            m = re.compile(pattern).search(u["body"])
            if m:
                return dict(raw=m.group(0), page="시작페이지 %s 섹션 안" % u["start"], line=None, unit=u,
                            pos=m.start())
        return None

    def section(self, li):
        """pdf md 줄 li 가 든 절: (시작 줄, 끝 줄, 제목, 비고)."""
        L = self.md_lines
        HEAD = re.compile(r"^\s*([IVX]+\.|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|제\s*\d+\s*[절장]|\d{1,2}\.|[가-하]\.|\([가-하]\)|\(\d{1,2}\))\s*\S")

        def lev(t):
            m = HEAD.match(t)
            if not m or len(t.strip()) > 45 or re.search(r"(니다|다)\.\s*$", t) or re.match(r"^\s*\d{1,2}\.\d", t):
                return None
            k = m.group(1)
            if re.match(r"[IVX]+\.|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|제", k):
                return 0
            if re.match(r"\d", k):
                return 1
            if re.match(r"[가-하]\.", k):
                return 2
            if re.match(r"\([가-하]\)", k):
                return 3
            return 4
        for maxlev in (2, 3, 4):
            s = next((j for j in range(li, max(self.head, li - 1500), -1) if (lev(L[j]) is not None and lev(L[j]) <= maxlev)),
                     None)
            if s is None:
                continue
            sl = lev(L[s])
            e = next((j for j in range(li + 1, min(len(L), li + 1500)) if (lev(L[j]) is not None and lev(L[j]) <= sl)),
                     len(L))
            if e - s <= 260:
                return s, e, L[s].strip(), ""
        s, e = max(self.head, li - 60), min(len(L), li + 60)
        return s, e, "(절 머리를 못 잡음)", "(판단) 절 경계를 제목 줄로 못 잡거나 절이 길어 앞뒤 60줄만"


# ================================================================ 행 만들기
A_COLS = ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
DOC_KIND = "지배구조 연차보고서"
MISSING = {("KB금융지주", 2021): "; 이 FY 추가공시 파일은 서버가 PDF 대신 6바이트를 돌려줘 받지 못함 — 본공시만 봄"}
T13 = {}


def t13_page(co, needle):
    """FY2025(공시연도 2026 본공시) — 13차 텍스트(같은 PDF)에서 같은 글이 있는 쪽."""
    if co not in T13:
        import zipfile
        z = zipfile.ZipFile(T13_ZIP)
        name = next((n for n in z.namelist() if n.endswith("연차보고서__%s.md" % co)), None)
        T13[co] = None
        if name:
            t = z.read(name).decode("utf-8")
            pages, cur = [], None
            for l in t.split("\n"):
                m = re.match(r"## p\.(\d+)", l)
                if m:
                    cur = [int(m.group(1)), []]
                    pages.append(cur)
                elif cur:
                    cur[1].append(l)
            T13[co] = [(p, norm("\n".join(ls))) for p, ls in pages]
    if not T13[co]:
        return ""
    n = norm(needle)[:60]
    hit = [p for p, t in T13[co] if n and n in t]
    return ",".join("p.%d" % p for p in hit[:3])


def doc_name(d):
    return "%s (%s, 파일 %s)" % (d["title"], d["kind"], d["file"])


def base_note(d):
    if d["src"] == "sec6":
        return "6차 섹션 글(PDF 원본은 이번 컨테이너에 없음; 레이아웃 추출이라 낱말 사이 공백이 여러 칸일 수 있음)"
    return "PDF 쪽 텍스트(pymupdf) — PDF 줄바꿈만 붙여 씀"


def build():
    docs = load_docs()
    by = {}
    for d in docs:
        by.setdefault((d["co"], d["year"]), []).append(d)
    D = {id(d): Doc(d) for d in docs}
    sections = {}          # (task, co, fy) -> list of section dicts (중복 없이)
    A_rows, B_rows, problems = [], [], []

    def other_versions(d, raw):
        out = []
        for o in by[(d["co"], d["year"])]:
            if o is d:
                continue
            out.append("%s %s" % (o["kind"], "같은 글" if norm(raw) in D[id(o)].ntext else "에 이 글 없음"))
        return out

    def add_section(task, d, f):
        key = (task, d["co"], d["fy"])
        lst = sections.setdefault(key, [])
        if d["src"] == "pdf":
            s, e, title, nb = D[id(d)].section(f["line"])
            k = (d["kind"], s, e)
            if not any(x["k"] == k for x in lst):
                lst.append(dict(k=k, d=d, title=title, body="\n".join(D[id(d)].md_lines[s:e]),
                                pages="p.%d–p.%d" % (D[id(d)].pg[s], D[id(d)].pg[max(s, e - 1)]), note=nb))
        else:
            u = f["unit"]
            k = (d["kind"], u["sn"])
            if not any(x["k"] == k for x in lst):
                lst.append(dict(k=k, d=d, title="%s %s" % (u["no"], u["title"]), body=u["body"],
                                pages="시작페이지 %s" % u["start"], note="6차 섹션 글 전체(chunk 이어 붙임)"))

    # ---------------- A: 손으로 고른 개별 겸직
    used = {}     # id(doc) -> [norm source]
    for sp in A_SPECS:
        ds = [d for d in by.get((sp["co"], sp["year"]), []) if d["kind"] == "본공시"]
        if not ds:
            problems.append("A 원문 문서 없음: %s %s" % (sp["co"], sp["year"]))
            continue
        d = ds[0]
        f = D[id(d)].find(sp["src"], sp["near_line"], sp["unit"])
        if not f:
            problems.append("A 원문 못 찾음: %s %s %s" % (sp["co"], sp["year"], sp["src"][:60]))
            continue
        src = join(f["raw"], sp["join"])
        notes = [sp["note"], base_note(d)]
        if sp["extra"]:
            g = D[id(d)].find(sp["extra"]) if d["src"] == "pdf" else None
            if g:
                src = src + " … " + join(g["raw"], "prose")
                used.setdefault(id(d), []).append(norm(g["raw"]))
                notes.append("각주 %s" % g["page"])
            else:
                problems.append("A 각주 못 찾음: %s %s" % (sp["co"], sp["year"]))
        reason = "문서에 없음"
        if sp["reason"]:
            r = D[id(d)].find(sp["reason"], sp["near_line"], sp["unit"]) if d["src"] == "pdf" else None
            if d["src"] != "pdf":
                r = D[id(d)].find(sp["reason"], None, f["unit"]["title"])
            if r:
                reason = join(r["raw"], "prose")
            else:
                problems.append("A 사유 못 찾음: %s %s" % (sp["co"], sp["year"]))
        birth = sp["birth"]
        if birth == "auto" and d["src"] == "sec6":
            body = f["unit"]["body"][:f["pos"]]
            ms = list(re.finditer(rx("후보 (" + sp["person"] + ")"), body))
            mb = re.search(r"출생연도\s*:\s*(\d{4})", body[ms[-1].end():ms[-1].end() + 400]) if ms else None
            birth = mb.group(1) if mb else ""
            if not birth:
                notes.append("출생연도 못 찾음")
        ov = other_versions(d, f["raw"])
        if ov:
            notes.append("같은 FY 다른 공시: " + ", ".join(ov))
        if d["year"] == 2026:
            p13 = t13_page(d["co"], f["raw"])
            if p13:
                notes.append("13차 텍스트(같은 PDF sha256) %s" % p13)
        used.setdefault(id(d), []).append(norm(f["raw"]))
        for (cc, ct) in sp["pairs"]:
            A_rows.append(dict(corp_label=d["co"], fy=d["fy"], person=sp["person"], birth_ym=birth,
                               holdco_title=sp["title"], holdco_duty="문서에 없음", registered=sp["registered"],
                               fulltime=sp["fulltime"], concurrent_company=cc, concurrent_title=ct,
                               concurrent_since=sp["since"] or "문서에 없음", reason_text=reason, doc_kind=DOC_KIND,
                               source_text=src, rcept_no_or_url=d["url"], page=f["page"], note="; ".join(x for x in notes if x),
                               doc_name=doc_name(d), collected_at=d["fetched_at"]))
        add_section("A", d, f)

    # ---------------- A: 「임원 겸직 현황」 표 없음 — FY 마다 1행
    for (co, year), ds in sorted(by.items()):
        d = next((x for x in ds if x["kind"] == "본공시"), ds[0])
        n_narr = sum(1 for r in A_rows if r["corp_label"] == co and r["fy"] == year - 1)
        kinds = ", ".join("%s(%s)" % (x["kind"], x["file"]) for x in ds)
        A_rows.append(dict(corp_label=co, fy=year - 1, person="", birth_ym="", holdco_title="", holdco_duty="",
                           registered="", fulltime="", concurrent_company="", concurrent_title="", concurrent_since="",
                           reason_text="문서에 없음", doc_kind=DOC_KIND, source_text="문서에 없음", rcept_no_or_url=d["url"],
                           page="전체", doc_name=doc_name(d), collected_at=d["fetched_at"],
                           note=("「임원 겸직 현황」 표(겸직 1건당 행이 있는 표)·「겸직 사유」 칸 없음 — 찾은 범위: %s 전문, 검색어 "
                                 "「겸직」「겸임」「겸무」「겸직 현황」「겸직 사유」 및 이사·경영진 명단 표. (판단) 서술 문장·위원회 표 속 "
                                 "개별 겸직 %d행은 따로 넣음. 「겸임」은 (나오면) 이미 넣은 은행장-비상임이사 건·「겸임교수」 직함·"
                                 "위원회 위원 겸임 제한 문구뿐. 이사 현황의 경력·약력 칸(現 직위)은 겸직 표가 아니라 넣지 않음(사업보고서 "
                                 "조각이 다룸)%s%s") % (kinds, n_narr, MISSING.get((co, year), ""),
                                 "; 6차 섹션 글 범위 안에서 찾음" if d["src"] == "sec6" else "")))

    # ---------------- B
    excl_log = []
    for (co, year), ds in sorted(by.items()):
        main = next((x for x in ds if x["kind"] == "본공시"), None)
        for d in ds:
            segs = segments(d)
            hs = collect_hits(d)
            nb, cats, cats_of = 0, {}, {}
            for h in hs:
                c = category(h, d, segs)
                cats_of[id(h)] = c
                if c == "B" and any(norm(h["sent"]) in u or u in norm(h["sent"]) for u in used.get(id(d), [])):
                    c = "A"
                cats[c] = cats.get(c, 0) + 1
                if c != "B":
                    excl_log.append(dict(co=co, year=year, kind=d["kind"], page=h["page"], cat=c, sent=h["sent"][:300]))
                    continue
                notes = [base_note(d)]
                if h.get("mode") == "table":
                    notes.append("표 칸은 「 | 」로 이음 (판단: 앞의 짧은 칸들을 같은 행으로 봄)")
                if MISSING.get((co, year)):
                    notes.append(MISSING[(co, year)].lstrip("; "))
                if d is not main and main is not None and norm(h["sent"]) in D[id(main)].ntext:
                    continue          # 본공시 행에 「같은 글」로 적음
                if d is not main:
                    notes.append("본공시에 없는 글(%s 에만)" % d["kind"])
                ov = other_versions(d, h["sent"]) if d is main else []
                if ov:
                    notes.append("같은 FY 다른 공시: " + ", ".join(ov))
                if d["src"] == "sec6":
                    notes.append("섹션 「%s」" % h["sec"])
                    if d["year"] == 2026:
                        p13 = t13_page(co, h["sent"])
                        if p13:
                            notes.append("13차 텍스트(같은 PDF sha256) %s" % p13)
                nb += 1
                f = dict(line=(D[id(d)].head + h["i"]) if d["src"] == "pdf" else None, unit=next((u for u in d.get("units", []) if u["sn"] == segs[h["seg"]]["unit"]), None))
                for k in h["kws"]:
                    B_rows.append(dict(corp_label=co, fy=year - 1, employees_total="", regular="", contract="", keyword=k,
                                       source_text=h["sent"], doc_kind=DOC_KIND, rcept_no_or_url=d["url"],
                                       page=("p.%s" % h["page"]) if d["src"] == "pdf" else "시작페이지 %s 섹션 안" % h["page"],
                                       note="; ".join(notes), doc_name=doc_name(d), collected_at=d["fetched_at"]))
                add_section("B", d, f)
            def _pg(x):
                try:
                    return int(x.get("pages") or 0)
                except (TypeError, ValueError):
                    return 0
            n_bhits = sum(1 for h in hs if cats_of.get(id(h)) == "B")
            # 본공시가 아닌 문서: B 문장이 있으면(본공시와 같은 글이면 본공시 행 note 에 적음) 「없음」 행을 만들지 않고,
            # B 문장이 없으면 본공시 전체 사본(쪽수 50% 이상)일 때만 건너뜀
            full_copy = d is not main and main is not None and (n_bhits > 0 or _pg(d) >= 0.5 * max(1, _pg(main)))
            covered = full_copy
            if d is not main and full_copy:
                continue           # 본공시와 같은 글 — 본공시 행(또는 본공시 「없음」 행)에 적음
            if nb == 0:
                cs = ", ".join("%s %d" % (CAT_NOTE.get(k, k) if k != "A" else "A 조각으로 옮긴 문장", v) for k, v in cats.items())
                B_rows.append(dict(corp_label=co, fy=year - 1, employees_total="", regular="", contract="", keyword="없음",
                                   source_text="문서에 없음", doc_kind=DOC_KIND, rcept_no_or_url=d["url"], page="전체",
                                   note=("찾은 범위: %s 전문(%s), 검색어 겸직·파견·출향·전출·전적·겸무 — 조직·인력 서술 속 키워드 문장 "
                                         "없음%s%s") % (d["file"], "6차 섹션 글" if d["src"] == "sec6" else "PDF 쪽 텍스트",
                                                      ("; 키워드는 있으나 뺀 것: " + cs + " (판단)") if cs else "",
                                                      ("; 같은 FY 다른 공시(%s)도 같은 범위로 확인" % ", ".join(
                                                          o["kind"] for o in ds if o is not d)) if d is main and len(ds) > 1 else ""),
                                   doc_name=doc_name(d), collected_at=d["fetched_at"]))
    # ---------------- 쓰기
    out_dir = os.path.join("dart_out", "ops15", "조각")
    os.makedirs(out_dir, exist_ok=True)
    for name, cols, rows in (("A_gov_g1.csv", A_COLS, A_rows), ("B_gov_g1.csv", B_COLS, B_rows)):
        rows.sort(key=lambda r: (G1.index(r["corp_label"]), r["fy"], r["source_text"] == "문서에 없음"))
        with open(os.path.join(out_dir, name), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(WORK, "B_제외문장.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["co", "year", "kind", "page", "cat", "sent"])
        w.writeheader()
        w.writerows(excl_log)
    # 원문 md
    for (task, co, fy), lst in sorted(sections.items()):
        od_ = os.path.join("dart_out", "ops15", "원문", task)
        os.makedirs(od_, exist_ok=True)
        p = os.path.join(od_, "%s__FY%d__연차보고서.md" % (co, fy))
        with open(p, "w", encoding="utf-8") as f:
            f.write("# %s FY%d 지배구조 및 보수체계 연차보고서 — 작업 %s 원문(행의 source_text 가 나온 절)\n\n" % (co, fy, task))
            for x in lst:
                d = x["d"]
                f.write("## %s (%s)\n\n" % (x["title"], x["pages"]))
                f.write("- 출처: %s\n- url: %s\n- 게시판: %s\n- sha256: %s\n- 수집: %s\n- 원문 글: %s%s\n\n" % (
                    doc_name(d), d["url"], d["board"] or "-", d["sha256"], d["fetched_at"],
                    d["text_path"] if d["src"] == "pdf" else "%s (6차 섹션 CSV)" % SEC_CSV,
                    ("\n- 비고: " + x["note"]) if x["note"] else ""))
                f.write("```text\n%s\n```\n\n" % x["body"].replace("```", "ˋˋˋ"))
    print("A", len(A_rows), "B", len(B_rows), "제외", len(excl_log))
    for pmsg in problems:
        print("문제:", pmsg)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build()
    else:
        print(__doc__)
