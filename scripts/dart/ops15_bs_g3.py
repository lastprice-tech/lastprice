# -*- coding: utf-8 -*-
"""15차 — 사업보고서 FY2019~FY2025 (g3: BNK금융지주·JB금융지주·한국투자금융지주) 에서 작업 A·B·D 조각을 뽑는다.

    python3 scripts/dart/ops15_bs_g3.py          # 조각 CSV 3개 + 원문 md + 점검 기록(work json)

입력(모두 로컬, 웹 요청·API 키 없음):
  dart_out/ops15/사업보고서_원문.csv 의 세 회사 행(본·정정) → text_path md(OpenDART XML 을 옮긴 것, 「### [절 n]」·「[표 n]」).
  handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip — 한국투자금융지주 FY2025 사업보고서 본문 PDF 텍스트(쪽 번호 찾기)와
    경영공시 2026.2Q PDF 텍스트(작업 B·D 의 2026.2Q 행). 경영공시 출처 url·fetched_at 은 dart_out/risk8/경영공시_2026_2Q.csv.
    BNK·JB 는 13차 텍스트가 없음(사업보고서 PDF 쪽·경영공시 모두) — 경영공시는 「미수집」 note 행.
  handoff/겸직현황_정리.csv — 5차 겸직 행(대조용, FY2023~2025).
산출:
  dart_out/ops15/조각/A_bs_g3.csv · B_bs_g3.csv · D_bs_g3.csv (utf-8-sig)
  dart_out/ops15/원문/{A,B,D}/<회사>__FY<fy>__사업보고서.md (행이 나온 절 전체 + 출처 줄), 경영공시는 <회사>__2026.2Q__경영공시.md
  dart_out/ops15/조각/bs_g3_work.json (5차 대조·정정 비교·판단 기록)
글자는 md(=XML) 그대로 옮긴다. source_text 는 표 행이면 md 의 「| … |」 줄 그대로, 문단이면 그 줄(문장) 그대로.
틀은 scripts/dart/ops15_bs_g2.py 를 따르되 세 회사 표 꼴(BNK 그룹 겸직 표·JB 지주 직위 줄이 든 겸직 표·한국투자 「직명|성명|회사명」 겸직 표와
「임원약력」 표, 지난해 기준 겸직 표)에 맞춰 다시 씀.
"""
from __future__ import annotations

import csv
import json
import os
import re
import zipfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
csv.field_size_limit(10 ** 9)

LIST_CSV = os.path.join("dart_out", "ops15", "사업보고서_원문.csv")
T13_ZIP = os.path.join("handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
MGMT_CSV = os.path.join("dart_out", "risk8", "경영공시_2026_2Q.csv")
H5_CSV = os.path.join("handoff", "겸직현황_정리.csv")
OUT = os.path.join("dart_out", "ops15", "조각")
RAWMD = os.path.join("dart_out", "ops15", "원문")
WORK = os.path.join(OUT, "bs_g3_work.json")
CORPS = ["BNK금융지주", "JB금융지주", "한국투자금융지주"]
H5_NAME = {"BNK금융지주": "BNK금융지주", "JB금융지주": "JB금융지주", "한국투자금융지주": "한국금융지주"}
# 지주 자기 이름(겸직 표의 지주 직위 줄·경력 칸의 현직 표시가 지주 자신을 가리키면 겸직 상대 아님)
SELF = {"BNK금융지주": ["BNK금융지주"], "JB금융지주": ["JB금융지주"],
        "한국투자금융지주": ["한국투자금융지주", "한국금융지주"]}
MGMT_NONE = ("BNK금융지주", "JB금융지주")     # 13차에 경영공시 텍스트가 없는 회사
KST = timezone(timedelta(hours=9))

A_COLS = ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
D_COLS = ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]

NONE = "문서에 없음"
DOC_KIND = "사업보고서"
KW = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
# 「전적」 오탐(全的·前的): 전적으로·전적인·사전적·완전적 등 — 轉籍 아님 (판단)
KW_FALSE = {"전적": re.compile(r"사\s?전적|전적으로|전적인|완\s?전\s?적|전적합"),
            "전출": re.compile(r"전출입")}
# 작업 D — 계약·거래 뜻의 낱말(업무위탁·용역·자문·전산 공동). 넓은 낱말은 따로 세어 note 에만.
D_RE = re.compile(r"업무\s*위\s*[·ㆍ]?\s*수탁|업무\s*위탁|업무\s*수탁|위\s*[·ㆍ]\s*수탁|위수탁|위탁\s*계약|수탁\s*계약|"
                  r"용역|경영\s*자문|자문\s*계약|자문\s*료|자문\s*수수료|공동\s*사용|공동\s*이용|시스템\s*공동|"
                  r"전산\s*공동|IT\s*공동|공동\s*전산")
D_BROAD = re.compile(r"위탁|수탁|자문|전산|(?<![A-Za-z])IT(?![A-Za-z])|공동")
D_TERMS = "업무위탁·업무수탁·위수탁·위ㆍ수탁·위탁계약·수탁계약·용역·경영자문·자문계약·자문료·자문수수료·공동사용·공동이용·시스템 공동·전산 공동·IT 공동"


# ================================================================ 공통 도구
def norm(t):
    """비교용: <br>·&cr;·공백·「|」를 뺀 글."""
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    return re.sub(r"[\s|]+", "", t)


def cell(t):
    """칸 값: 칸 안 줄바꿈 표시(<br>·&cr;)만 띄어쓰기로 바꾸고 겹친 공백을 하나로(글자는 그대로)."""
    return re.sub(r"\s+", " ", re.sub(r"(<br>|&cr;)", " ", t or "")).strip()


def pname(t):
    """성명 비교 키: 괄호 표시·■·공백·줄바꿈 표시 제거."""
    t = (t or "").replace("<br>", "").replace("&cr;", "").replace("■", "")
    t = re.sub(r"\(.*?\)", "", t)
    return re.sub(r"\s+", "", t)


def cname(t):
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    t = re.sub(r"\(주\)|㈜|주식회사|\(비상장\)|\(상장\)", "", t)
    return re.sub(r"[\s·ㆍ]+", "", t)


def bnorm(b):
    """출생년월 비교 키(YYYY.MM)."""
    b = (b or "").strip()
    m = re.search(r"(\d{4})\D+(\d{1,2})", b)
    if m:
        return "%s.%02d" % (m.group(1), int(m.group(2)))
    return re.sub(r"\s+", "", b)


def kst(s):
    if not s:
        return ""
    if s.endswith("+00:00") or s.endswith("Z"):
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(KST).isoformat(timespec="seconds")
    return s


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def is_self(corp, text):
    k = cname(text)
    return any(cname(s) in k for s in SELF[corp])


# ================================================================ md 읽기
ROMAN = r"(VIII|IX|XII|XI|X|Ⅷ|Ⅸ|Ⅹ|Ⅺ|Ⅻ)"
CH = {"Ⅷ": "VIII", "Ⅸ": "IX", "Ⅹ": "X", "Ⅺ": "XI", "Ⅻ": "XII"}


class Doc:
    def __init__(self, r):
        self.r = r
        self.corp, self.fy, self.kind, self.rcept = r["label"], int(r["fy"]), r["kind"], r["rcept_no"]
        self.name = r["report_nm"]
        self.collected = r["fetched_at"]
        self.path = r["text_path"]
        self.L = open(self.path, encoding="utf-8").read().split("\n")
        self.heads = []          # (line idx, n, title)
        for i, l in enumerate(self.L):
            m = re.match(r"### \[절 (\d+)\] (.*)$", l)
            if m:
                self.heads.append((i, int(m.group(1)), m.group(2)))
        self.tables = []          # dict(start, end, no, rows:[(idx, cells)])
        cur = None
        for i, l in enumerate(self.L):
            m = re.match(r"\[표 (\d+)\]$", l)
            if m:
                cur = dict(start=i, no=int(m.group(1)), rows=[])
            elif l == "[표 끝]" and cur is not None:
                cur["end"] = i
                self.tables.append(cur)
                cur = None
            elif cur is not None and l.startswith("|"):
                cur["rows"].append((i, [c.strip() for c in l.strip()[1:-1].split("|")]))
        self.ch = {}
        for i, n, t in self.heads:
            m = re.match(ROMAN + r"\.", t.strip())
            if m:
                k = CH.get(m.group(1), m.group(1))
                self.ch.setdefault(k, i)

    def chap_range(self, a, b_list):
        s = self.ch.get(a)
        if s is None:
            return None
        ends = [self.ch[b] for b in b_list if b in self.ch and self.ch[b] > s]
        ends += [i for i, n, t in self.heads if i > s and re.match(r"【", t.strip())]
        return (s, min(ends) if ends else len(self.L))

    def head_of(self, i):
        h = None
        for hi, n, t in self.heads:
            if hi <= i:
                h = (hi, n, t)
            else:
                break
        return h

    def section(self, i):
        """줄 i 를 담은 절: (머리 줄, 끝 줄(다음 ### 전), n, 제목)."""
        h = self.head_of(i)
        nxt = next((hi for hi, n, t in self.heads if hi > h[0]), len(self.L))
        return h[0], nxt, h[1], h[2]

    def table_at(self, i):
        for t in self.tables:
            if t["start"] <= i <= t["end"]:
                return t
        return None

    def loc(self, i):
        h = self.head_of(i)
        t = self.table_at(i)
        s = "XML [절 %d] 「%s」" % (h[1], h[2].strip())
        if t:
            s += " [표 %d]" % t["no"]
        else:
            s += " (문단)"
        return s

    def caption(self, t, back=12):
        """표 앞 글줄(원문) — 바로 앞 작은 표(1~2행)·빈 줄은 건너뛰고, 머리 글줄(※·가.·1)·(1) 등)이 나오면 거기까지."""
        out = []
        i = t["start"] - 1
        while i >= 0 and t["start"] - i <= back and len(out) < 3:
            l = self.L[i].strip()
            if l == "[표 끝]":
                k = i - 1
                while k >= 0 and not re.match(r"\[표 \d+\]$", self.L[k]):
                    k -= 1
                if i - k - 1 > 2:
                    break
                i = k - 1
                continue
            if l.startswith("### "):
                break
            if l and not l.startswith("|") and re.sub(r"(&cr;|\s)", "", l):
                out.append(l)
                if re.match(r"(※|[가-하]\.|\d+\)|\(\d+\)|\d+\.)", re.sub(r"^(&cr;|\s)+", "", l)) or "현황" in l:
                    break
            i -= 1
        return out

    def prev_small(self, t):
        """표 바로 앞(빈 줄·글줄 3줄 안)의 1~2행 작은 표 글."""
        k = self.tables.index(t)
        if k == 0:
            return ""
        pt = self.tables[k - 1]
        if t["start"] - pt["end"] <= 4 and len(pt["rows"]) <= 2:
            return " ".join(" ".join(c) for i, c in pt["rows"])
        return ""


# ================================================================ 13차 PDF 텍스트(쪽 찾기)
_T13 = {}


def t13_pages(kind, corp):
    key = (kind, corp)
    if key not in _T13:
        z = zipfile.ZipFile(T13_ZIP)
        name = next((n for n in z.namelist() if n.endswith("텍스트/%s__%s.md" % (kind, corp))), None)
        pages, head = [], ""
        if name:
            t = z.read(name).decode("utf-8")
            cur = None
            for l in t.split("\n"):
                m = re.match(r"## p\.(\d+)", l)
                if m:
                    cur = [int(m.group(1)), []]
                    pages.append(cur)
                elif cur:
                    cur[1].append(l)
                elif l.startswith("- 원본:"):
                    head = l
        _T13[key] = dict(pages=[(p, ls, norm("".join(ls))) for p, ls in pages], head=head, name=name)
    return _T13[key]


def t13_rcept(corp):
    m = re.search(r"dart_out/doc/(\d+)/", t13_pages("사업보고서", corp)["head"])
    return m.group(1) if m else ""


def t13_find(corp, text):
    """같은 글이 있는 PDF 쪽(들). 긴 행은 앞 80·40자로, 쪽 경계에 걸치면 이어 붙여 봄."""
    P = t13_pages("사업보고서", corp)["pages"]
    n = norm(text)
    if not n:
        return ""
    for k in (n, n[:80], n[:40]):
        if len(k) < 8:
            continue
        hit = [p for p, ls, t in P if k in t]
        if hit:
            return ",".join("p.%d" % p for p in hit[:3])
        for j in range(len(P) - 1):
            if k in P[j][2] + P[j + 1][2]:
                return "p.%d~p.%d" % (P[j][0], P[j + 1][0])
    return ""


# ================================================================ 기준일
DATE_RE = re.compile(r"(\d{4})\s*(?:년|\.)\s*(\d{1,2})\s*(?:월|\.)?\s*(말|\d{1,2})?")


def basis_of(d, t, cap):
    """겸직 표 기준일 원문과 (연, 월). 앞 작은 표·앞 글줄에서 찾음."""
    srcs = [d.prev_small(t)] + cap
    for s in srcs:
        s2 = re.sub(r"(<br>|&cr;)", " ", s or "")
        if not re.search(r"기준|현재|\d{4}\s*[년.]\s*\d", s2):
            continue
        m = DATE_RE.search(s2)
        if m:
            return m.group(0).strip(), (int(m.group(1)), int(m.group(2)))
    return "", None


# ================================================================ 임원 현황 표
def exec_tables(d, rng):
    """Ⅷ 안 임원 현황 표들(등기임원 선임 후보자 표 「구분|성명」 은 뺌): [(table, kind, cap, rows)]."""
    out = []
    first = True
    for t in d.tables:
        if not (rng[0] <= t["start"] < rng[1]) or not t["rows"]:
            continue
        h = [norm(c) for c in t["rows"][0][1]]
        if not (len(h) > 7 and h[0] == "성명" and h[1] == "성별" and "출생" in h[2]):
            continue
        cap = " / ".join(d.caption(t))
        kind = "기준일" if (first and "이후" not in cap) else "이후"
        first = False
        rows = []
        for i, c in t["rows"][1:]:
            if len(c) < 8 or norm(c[0]).startswith("의결권"):
                continue
            rows.append(dict(line=i, name=cell(c[0]), key=pname(c[0]), birth=cell(c[2]), bkey=bnorm(cell(c[2])),
                             title=cell(c[3]), reg=cell(c[4]), ft=cell(c[5]), duty=cell(c[6]), career=c[7],
                             table=t, tkind=kind, cap=cap))
        out.append((t, kind, cap, rows))
    return out


def bio_entries(d, r8):
    """한국투자 「☞ 임원약력」 표(경력 칸이 「아래참조」): {성명키: [(이름 줄, 행 줄, 기간 칸, 경력 칸)]}.
    FY2019~2022 는 「(n) 성명」 글줄 + 사람마다 표, FY2023~ 는 한 표 안 「| ■ 성명 |  |」 행."""
    s = next((i for i in range(*r8) if "임원약력" in d.L[i] and not d.L[i].startswith("|")), None)
    out = {}
    if s is None:
        return out
    cur, cur_line = None, None
    for i in range(s + 1, r8[1]):
        l = d.L[i]
        ls = re.sub(r"^(?:&cr;|\s)+", "", l)
        if re.match(r"(나\.|다\.|###)", ls):
            break
        if not l.startswith("|"):
            m = re.match(r"\((\d+)\)\s*(\S.*?)(?:&cr;|\s)*$", ls)
            if m:
                cur, cur_line = pname(m.group(2)), i
            continue
        c = [x.strip() for x in l.strip()[1:-1].split("|")]
        if c and c[0].startswith("■"):
            cur, cur_line = pname(c[0]), i
        elif cur and len(c) == 2:
            out.setdefault(cur, []).append((cur_line, i, c[0], c[1]))
    return out


# ================================================================ 경력 칸(현직 표시) 조각
SUF = re.compile(r"\(\s*(?:([^()]{0,12}?)\s*[,/]\s*)?(現|현재|현)\s*\)")
PRE = re.compile(r"^(?:\(\s*現\s*\)|現\s*\)|現\s+|\(현\))\s*")
PERIOD_NOW = re.compile(r"^(\d{4}(?:\.\d{1,2})?)\s*~\s*현재\s*")
LEAD_DATE = re.compile(r"^((?:\d{2}\.\d{2})|(?:\d{4}(?:\.\d{1,2})?(?:\s*~\s*\d{4}(?:\.\d{1,2})?)?))\s+")
CO_END = re.compile(r"(은행|증권|금융지주|지주|캐피탈|저축은행|자산운용|운용|생명|손해보험|화재|보험|카드|파트너스|신탁|투자|"
                    r"신용정보|시스템|회계법인|법률사무소|법무법인|대학교|대학원|대학|연구원|연구소|학회|협회|공사|공단|위원회|"
                    r"재단|그룹|홀딩스|㈜|\(주\)|주식회사|Inc\.?|Ltd\.?|LLC|Co\.?|Partners|Bank|Group)(\(주\))?[,]?$")


def norm_marks(t):
    t = re.sub(r"\(\s*(?:(?:<br>|&cr;)\s*)*(現|前|현재|현|전)\s*(?:(?:<br>|&cr;)\s*)*\)", r"(\1)", t or "")
    t = re.sub(r"~\s*(?:(?:<br>|&cr;)\s*)*현재", "~현재", t)
    return t


def split_entries(corp, t):
    t = norm_marks(t)
    parts = re.split(r"<br>|&cr;|\n", t)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        for s in re.split(r"(?:^|\s)-\s+", p):
            s = s.strip()
            if not s:
                continue
            # 날짜로 시작하는 경력이 줄바꿈 없이 붙은 칸: 날짜 앞에서 나눔
            segs = re.split(r"(?<![\d.~/])(?=\d{2}\.\d{2}\s)" if corp == "BNK금융지주" else r"(?!)", s)
            segs2 = []
            for x in segs:
                segs2 += re.split(r"(?<![\d.~/])(?=\d{4}\s*~\s*(?:현재|\d{4}))", x)
            segs3 = []
            for x in segs2:
                if corp == "한국투자금융지주":
                    segs3 += re.split(r"(?=\(현\))", x)          # 한국투자: 「(현) 회사 직위」 앞 표시
                else:
                    segs3 += re.split(r"(?<=現\))|(?<=\(현\))|(?<=\(현재\))", x)   # BNK·JB: 「회사 직위(現)」 뒤 표시
            out += [x.strip() for x in segs3 if x.strip()]
    return out


def split_cn(body):
    """경력 조각 → (회사, 직위). 회사 끝말(은행·증권·지주·대학 등)이 붙은 첫 낱말까지를 회사로, 없으면 마지막 띄어쓰기에서 나눔."""
    w = body.split()
    for k, x in enumerate(w[:-1]):
        if CO_END.search(x):
            return " ".join(w[:k + 1]), " ".join(w[k + 1:])
    if len(w) >= 2:
        return " ".join(w[:-1]), w[-1]
    return body, ""


def career_items(corp, raw):
    """경력 칸에서 현직 표시가 붙은 조각: [dict(seg, body, mark, since, gyeom)]."""
    out = []
    for s in split_entries(corp, raw):
        mark, since, body, gyeom = "", "", s, ""
        m = PERIOD_NOW.match(s)
        if m:
            mark, since, body = m.group(0).strip(), m.group(0).strip(), s[m.end():]
        elif corp == "한국투자금융지주" and s.startswith("(현)"):
            mark, body = "(현)", s[4:]
        else:
            m = SUF.search(s)
            if m:
                mark, body = m.group(0), s[:m.start()]
                if m.group(1) and "겸" in m.group(1):
                    gyeom = m.group(0)
            else:
                m = PRE.match(s)
                if m:
                    mark, body = m.group(0).strip(), s[m.end():]
        if not mark:
            continue
        body = body.strip(" ,·ㆍ-")
        m = LEAD_DATE.match(body)
        if m:
            since = since or m.group(1)
            body = body[m.end():].strip()
        if body.startswith("(겸)"):
            gyeom = gyeom or "(겸)"
            body = body[3:].strip()
        if not body:
            continue
        co, ti = split_cn(body)
        out.append(dict(seg=s, body=body, mark=mark, since=since, gyeom=gyeom, co=co, ti=ti))
    return out


# ================================================================ 겸직 표
def concurrent_tables(d, rngs):
    out = []
    for t in d.tables:
        if not any(a <= t["start"] < b for a, b in rngs) or not t["rows"]:
            continue
        hdr = [norm(c) for c in t["rows"][0][1]]
        hj = "".join(hdr)
        if re.search(r"대상회사|대상계열사", hj) and hdr[0] == "성명":
            fmt = "f5"
        elif len(hdr) >= 4 and hdr[0] == "직명" and hdr[1] == "성명" and "회사명" in hdr[2]:
            fmt = "kis"
        else:
            continue
        cap = d.caption(t)
        capj = " / ".join(cap)
        basis, ym = basis_of(d, t, cap)
        if ym is None:
            when = "기준일"            # 기준일 표시 없음 → 작성기준일 표로 봄(note)
        elif ym[0] > d.fy:
            when = "이후"
        elif ym[0] < d.fy:
            when = "지난해"
        else:
            when = "이후" if re.search(r"이후|제출일", capj) else "기준일"
        rows, prev, prev_title, seg_after = [], None, "", False
        ncol = len(hdr)
        for i, c in t["rows"][1:]:
            if [norm(x) for x in c] == hdr:
                seg_after = True        # 표 안 두 번째 머리 행(뒤는 다른 기준일 표가 붙은 것) — (판단)
                prev = None
                continue
            cont = False
            if fmt == "f5":
                if len(c) == ncol:
                    nm, co, ti, sn, rk = c[0], c[1], c[2], c[3], c[4]
                elif len(c) == ncol - 1 and prev is not None:
                    nm, co, ti, sn, rk = prev[1], c[0], c[1], c[2], c[3]
                    cont = True
                else:
                    rows.append(dict(line=i, bad=True, cells=c))
                    continue
                htitle = ""
            else:
                if len(c) == 5:
                    htitle, nm, co, ti, rk = c
                elif len(c) == 4 and prev is not None:
                    htitle, (nm, co, ti, rk) = prev_title, c
                elif len(c) == 3 and prev is not None:
                    htitle, nm, (co, ti, rk) = prev_title, prev[1], c
                    cont = True
                else:
                    rows.append(dict(line=i, bad=True, cells=c))
                    continue
                sn = ""
                prev_title = htitle
            if not cont:
                prev = (i, nm)
            rec = dict(line=i, name_line=(prev[0] if cont else None), name=cell(nm), key=pname(nm),
                       company=cell(co), ckey=cname(co), title=cell(ti), tkey=norm(ti), since=cell(sn), remark=cell(rk),
                       htitle=cell(htitle), table=t, fmt=fmt, basis=basis, when=("이후" if seg_after else when),
                       seg_after=seg_after, cap=capj, self_line=is_self(d.corp, co))
            rows.append(rec)
        # 표 바로 아래 주석 글(주·※ 로 시작, 3줄까지, 다음 표·절 전)
        foot = []
        for j in range(t["end"] + 1, min(t["end"] + 12, len(d.L))):
            l = d.L[j].strip()
            if re.match(r"\[표 \d+\]$", l) or l.startswith("###"):
                if re.match(r"\[표 \d+\]$", l) and j + 1 < len(d.L) and re.match(r"\|\s*주\)?", d.L[j + 1]):
                    foot.append(d.L[j + 1].strip())
                break
            if re.match(r"(주\d*\)|※|\*)", l):
                foot.append(l)
            elif foot and l and not re.match(r"(&cr;)+$", l) and len(foot) < 4:
                foot.append(l)
            elif l and not re.match(r"(&cr;)+$", l):
                break
        chap = "VIII" if t["start"] < d.ch.get("IX", 10 ** 9) else "IX"
        out.append(dict(table=t, fmt=fmt, basis=basis, when=when, cap=capj, foot=foot, chap=chap, rows=rows))
    return out


# ================================================================ 작업 A — 한 보고서
def extract_A(d):
    r8 = d.chap_range("VIII", ["IX", "X", "XI", "XII"])
    r9 = d.chap_range("IX", ["X", "XI", "XII"])
    res = dict(rows=[], probs=[], judg=[], past=[], r8=r8, r9=r9)
    if not r8:
        res["probs"].append("Ⅷ 절 없음")
        return res
    ets = exec_tables(d, r8)
    execs = [e for t, k, c, rs in ets for e in rs]
    rngs = [r8] + ([r9] if r9 else [])
    cts = concurrent_tables(d, rngs)
    res["ctabs"] = [(c["table"]["no"], c["chap"], c["when"], c["basis"], len(c["rows"])) for c in cts]

    def find_exec(key, after=False):
        base = [e for e in execs if e["key"] == key and e["tkind"] == "기준일"]
        aft = [e for e in execs if e["key"] == key and e["tkind"] != "기준일"]
        cand = (aft + base) if after else (base + aft)
        births = sorted(set(e["bkey"] for e in cand))
        return (cand[0] if cand else None), births

    def where(ct_tab):
        return "Ⅷ" if ct_tab["start"] < (r9[0] if r9 else 10 ** 9) else "Ⅸ"

    # 지난해 기준 겸직 표는 넣지 않음(그 해 보고서 몫) — 기록만
    for ct in cts:
        if ct["when"] == "지난해":
            res["past"].append("[표 %d] %s(%s)" % (ct["table"]["no"], ct["basis"], where(ct["table"])))
    use = [ct for ct in cts if ct["when"] != "지난해"]
    order = sorted([(ct, r) for ct in use for r in ct["rows"]],
                   key=lambda x: (x[1].get("when", "") == "이후", x[0]["table"]["start"], x[1]["line"]))
    kept, selfs = [], {}
    for ct, rec in order:
        if rec.get("bad"):
            res["probs"].append("겸직 표 행 칸 수 다름 [표 %d] 줄 %d: %s" % (ct["table"]["no"], rec["line"] + 1, rec["cells"]))
            continue
        if rec["self_line"]:
            selfs.setdefault(rec["key"], []).append(rec)
            continue
        dup = next((k for k in kept if k["key"] == rec["key"] and k["ckey"] == rec["ckey"] and k["tkey"] == rec["tkey"]), None)
        if dup is None:
            dup = next((k for k in kept if k["key"] == rec["key"] and k["ckey"] == rec["ckey"]
                        and k["since"] and k["since"] == rec["since"]), None)
        if dup:
            diff = []
            if dup["tkey"] != rec["tkey"]:
                diff.append("직책 「%s」" % rec["title"])
            if norm(dup["since"]) != norm(rec["since"]):
                diff.append("선임시기 「%s」" % rec["since"])
            if norm(dup["remark"]) != norm(rec["remark"]):
                diff.append("비고 「%s」" % rec["remark"])
            dup.setdefault("also_lines", []).append(rec["line"])
            dup.setdefault("also", []).append("%s [표 %d]%s%s" % (
                where(rec["table"]), rec["table"]["no"], "(기준 %s)" % rec["basis"] if rec["basis"] else "",
                " 에서는 " + "·".join(diff) if diff else ""))
            continue
        kept.append(rec)
    # 지주 직위 줄만 있고 다른 회사 줄이 없는 사람 → 지주 직위 줄을 행으로(판단)
    for key, sl in selfs.items():
        if not any(k["key"] == key for k in kept):
            r0 = sl[0]
            r0 = dict(r0, only_self=True)
            kept.append(r0)
    for rec in kept:
        e, births = find_exec(rec["key"], rec["when"] == "이후")
        lines = [rec["line"]] if rec["name_line"] is None else [rec["name_line"], rec["line"]]
        src = "\n".join(d.L[i] for i in lines)
        ct_tab = rec["table"]
        note = ["%s 겸직 표 「%s」%s" % (where(ct_tab), rec["cap"][:80] or "(앞 글 없음)",
                                     " 기준 「%s」" % rec["basis"] if rec["basis"] else " — 기준일 표시 못 찾음(작성기준일 표로 봄)")]
        if rec["when"] == "이후":
            note.append("작성기준일 이후 겸직 표의 행")
        if rec["seg_after"]:
            note.append("(판단) 표 안에 머리 행이 한 번 더 나오고 그 뒤 행 — 표 아래 글(「%s」)로 보아 작성기준일 이후 겸직 행"
                        % " ".join(next((c["foot"] for c in cts if c["table"] is ct_tab), []))[:90])
        if rec["fmt"] == "kis":
            note.append("겸직 표 「직명」 칸(지주 직위) 「%s」" % rec["htitle"])
        sl = [x for x in selfs.get(rec["key"], []) if x["table"] is ct_tab]
        if rec.get("only_self"):
            note.append("(판단) 겸직 표에 이 사람의 지주 직위 줄만 있고 다른 회사 줄이 없음 — 그 줄을 행으로 넣음")
        elif sl:
            note.append("같은 표의 지주 직위 줄: 「%s」" % d.L[sl[0]["line"]].strip())
        if rec["remark"]:
            note.append("겸직 표 비고/상근여부 칸: 「%s」" % rec["remark"])
        foot = next((c["foot"] for c in cts if c["table"] is ct_tab), [])
        if foot:
            note.append("표 아래 글: " + " / ".join("「%s」" % f[:160] for f in foot[:3]))
        if rec["name_line"] is not None:
            note.append("이름이 윗줄에 있는 행(칸 합침) — source_text 는 이름 줄과 그 행 두 줄")
        if rec["fmt"] == "kis":
            note.append("겸직 표에 선임시기 칸 없음 — concurrent_since 빈칸")
        elif not rec["since"]:
            note.append("선임시기 칸 비어 있음")
        if rec.get("also"):
            note.append("같은 행: " + ", ".join(rec["also"]))
        if e is None:
            note.append("같은 보고서 임원 현황 표에 이 성명 없음 — 지주 직위·담당업무·등기·상근·출생년월 빈칸")
        else:
            if e["tkind"] != "기준일":
                note.append("지주 쪽 칸은 작성기준일 이후 임원 표(「%s」)에서" % e["cap"][:50])
            if len(births) > 1:
                note.append("(판단) 같은 성명이 같은 보고서 임원 표들에 출생년월 %s 로 적힘 — %s 행으로 맞춤; 동일인 여부는 원문으로 가리지 않음"
                            % ("·".join(births), "작성기준일 이후 표" if rec["when"] == "이후" else "작성기준일 표"))
        res["rows"].append(dict(
            src_kind="table", person=re.sub(r"\s*\((?:주\d*|등기임원|미등기임원)\)\s*", "", rec["name"]).strip(),
            birth_ym=e["birth"] if e else "", holdco_title=e["title"] if e else "",
            holdco_duty=e["duty"] if e else "", registered=e["reg"] if e else "", fulltime=e["ft"] if e else "",
            concurrent_company=rec["company"], concurrent_title=rec["title"], concurrent_since=rec["since"],
            source_text=src, line=rec["line"], lines=lines, also_lines=rec.get("also_lines", []), note=note,
            key=(rec["key"], rec["ckey"], rec["tkey"]), cmp=norm(src)))

    # --- 임원 현황 칸(담당업무 「겸직」·주요경력 현직 표시), 한국투자는 「임원약력」 표도
    bios = bio_entries(d, r8) if d.corp == "한국투자금융지주" else {}
    cov = {}
    for r in res["rows"]:
        cov.setdefault(r["key"][0], set()).add(r["key"][1])
    seen = {}
    for e in execs:
        items = []
        if "겸직" in e["duty"] or "겸무" in e["duty"]:
            items.append(dict(kind="duty", src_line=e["line"], name_line=None, co="", ti="", since="",
                              why="담당업무 칸 「%s」" % e["duty"], body=e["duty"]))
        for it in career_items(d.corp, e["career"]):
            if is_self(d.corp, it["body"]):
                continue
            items.append(dict(kind="career", src_line=e["line"], name_line=None, co=it["co"], ti=it["ti"],
                              since=it["since"], body=it["body"],
                              why="주요경력 칸 현직 표시 「%s」%s 조각 「%s」" % (it["mark"], (" 겸 표시 「%s」" % it["gyeom"]) if it["gyeom"] else "",
                                                                  it["seg"][:120])))
        if norm(e["career"]) in ("아래참조", "하단참조") and e["key"] in bios:
            for nl, rl, per, txt in bios[e["key"]]:
                if "현재" not in per:
                    continue
                body = cell(txt)
                gy = ""
                if body.startswith("(겸)"):
                    gy, body = "(겸)", body[3:].strip()
                if is_self(d.corp, body) or not body:
                    continue
                co, ti = split_cn(body)
                items.append(dict(kind="bio", src_line=rl, name_line=nl, co=co, ti=ti, since=cell(per), body=body,
                                  why="임원 현황 표 「주요경력」 칸 「아래참조」 → 「임원약력」 표 행: 기간 칸 「%s」%s" % (
                                      cell(per), " 겸 표시 「(겸)」" if gy else "")))
        for it in items:
            if it["kind"] == "duty":
                if cov.get(e["key"]):
                    continue
            elif any(c and (c in cname(it["body"]) or cname(it["co"]) in c) for c in cov.get(e["key"], set())):
                continue
            k = (e["key"], e["bkey"], cname(it["co"]) or norm(it["body"]))
            if k in seen:
                prev = seen[k]
                if it["src_line"] not in prev["lines"] and it["src_line"] not in prev["also_lines"]:
                    prev["also_lines"].append(it["src_line"])
                    prev["note"].append("같은 사람·같은 회사 현직 조각이 %s 에도: 「%s」" % (
                        d.loc(it["src_line"]).replace("XML ", ""), it["body"][:60]))
                continue
            note = ["임원 현황 칸에서 — 겸직 표에 없음", it["why"]]
            if it["kind"] == "duty":
                note.append("(판단) 담당업무 칸에 겸직 상대 회사가 적혀 있지 않음 — concurrent_company 빈칸")
            else:
                note.append("(판단) 현직 조각 「%s」을 회사 끝말(은행·증권·지주·대학 등) 또는 마지막 띄어쓰기에서 회사·직위로 나누고, "
                            "앞 연월·기간은 concurrent_since 로(겸직 표의 선임일이 아니라 경력 칸 연월)" % it["body"][:80])
            if e["tkind"] != "기준일":
                note.append("작성기준일 이후 임원 표(「%s」)" % e["cap"][:50])
            lines = [it["src_line"]] if it["name_line"] is None else [it["name_line"], it["src_line"]]
            row = dict(src_kind=it["kind"], person=e["name"], birth_ym=e["birth"], holdco_title=e["title"],
                       holdco_duty=e["duty"], registered=e["reg"], fulltime=e["ft"],
                       concurrent_company=it["co"], concurrent_title=it["ti"], concurrent_since=it["since"],
                       source_text="\n".join(d.L[i] for i in lines), line=it["src_line"], lines=lines,
                       also_lines=[], note=note, key=(e["key"], cname(it["co"]), norm(it["ti"])),
                       cmp=re.sub(r"[·,.\-]", "", norm(e["name"] + e["bkey"] + it["body"])))
            seen[k] = row
            res["rows"].append(row)
    return res


# ================================================================ 작업 B — 한 보고서
def staff_table(d, r8):
    for t in d.tables:
        if not (r8[0] <= t["start"] < r8[1]) or len(t["rows"]) < 3:
            continue
        h = norm(" ".join(" ".join(c) for i, c in t["rows"][:4]))
        if "직원수" in h or ("직원" in h and "기간의정함" in h):
            tot = [(i, c) for i, c in t["rows"] if re.fullmatch(r"합계|총계|계", norm(c[0]))]
            if tot and "기간제" in h:
                return t, tot
    return None, []


def kw_hits(d, rng):
    hits = []
    for i in range(rng[0], rng[1]):
        l = d.L[i]
        for k in KW:
            if k not in l:
                continue
            fr = KW_FALSE.get(k)
            if fr and not re.sub(fr, "", l).count(k):
                continue
            hits.append((i, k))
    return hits


def sentence_of(line, k):
    """문단 줄이 길면 그 낱말이 든 문장만(원문 조각 그대로). 표 행은 줄 그대로."""
    if line.startswith("|") or len(line) <= 300:
        return line
    pos = line.find(k)
    a = max(line.rfind("다.", 0, pos), line.rfind(". ", 0, pos))
    a = a + 2 if a >= 0 else 0
    b = line.find("다.", pos)
    b = b + 2 if b >= 0 else len(line)
    return line[a:b].strip()


def extract_B(d):
    r8 = d.chap_range("VIII", ["IX", "X", "XI", "XII"])
    res = dict(staff=None, hits=[], probs=[], r8=r8)
    if not r8:
        res["probs"].append("Ⅷ 절 없음")
        return res
    t, tot = staff_table(d, r8)
    if t is None:
        res["probs"].append("직원 현황 표(합계 행) 못 찾음")
    else:
        i, c = tot[-1]
        res["staff"] = dict(line=i, cells=c, total=c[5] if len(c) > 5 else "", regular=c[1] if len(c) > 1 else "",
                            contract=c[3] if len(c) > 3 else "", table=t, n_tot=len(tot))
        if len(tot) > 1:
            res["probs"].append("직원 표 합계 행 %d개 — 마지막 행을 씀" % len(tot))
        foot = []
        j = t["end"] + 1
        while j < min(t["end"] + 14, r8[1]):
            l = d.L[j].strip()
            if re.match(r"\[표 \d+\]$", l):
                nxt = d.L[j + 1].strip() if j + 1 < len(d.L) else ""
                if re.match(r"\|\s*(\(주|주\d|주\)|※|\*)", nxt):
                    j += 1
                    while j < len(d.L) and d.L[j] != "[표 끝]":
                        if d.L[j].startswith("|"):
                            foot.append(d.L[j])
                        j += 1
                    j += 1
                    continue
                break
            if re.match(r"(\(주|주\d*\)|※|\*|\d\))", l) or (foot and l and not re.match(r"(다\.|라\.|나\.)", l)
                                                         and not l.startswith("###") and len(foot) < 10):
                if l and not re.match(r"(&cr;)+$", l):
                    foot.append(l)
            elif l and not re.match(r"(&cr;)+$", l):
                break
            j += 1
        res["staff"]["foot"] = foot
    for i, k in kw_hits(d, r8):
        res["hits"].append(dict(line=i, kw=k, text=sentence_of(d.L[i], k)))
    return res


# ================================================================ 작업 D — 한 보고서
def extract_D(d):
    rx = d.chap_range("X", ["XII"])
    res = dict(rows=[], broad=[], rng=rx, probs=[])
    if not rx:
        res["probs"].append("Ⅹ 절 없음")
        return res
    for i in range(rx[0], rx[1]):
        l = d.L[i]
        ms = [m for m in D_RE.finditer(l) if not d_skip(l, m)]
        if not ms:
            if D_BROAD.search(l) and not l.startswith("### "):
                res["broad"].append((i, D_BROAD.search(l).group(0)))
            continue
        t = d.table_at(i)
        ctype = []
        for m in ms:
            if m.group(0) not in ctype:
                ctype.append(m.group(0))
        res["rows"].append(dict(line=i, terms=ctype, table=t))
    return res


def d_skip(l, m):
    """계약·거래가 아닌 쓰임 (판단): 「…」 안 법·규정·문서 이름 속 낱말, 「…업무방법·규정·지침」 같은 내규 이름."""
    tail = re.split(r"[,，、|]", l[m.end(): m.end() + 25])[0]
    if re.search(r"^\S*\s?(업무방법|규정|준칙|지침|매뉴얼)", tail):
        return True
    a = l.rfind("「", 0, m.start())
    if a >= 0 and l.find("」", a) > m.start() and l.rfind("」", 0, m.start()) < a:
        return True
    return False


def d_fields(d, x, bnote, corr_D, corr_notes):
    i = x["line"]
    t = x["table"]
    line = d.L[i]
    cp, amt = "", ""
    note = []
    if t:
        hdr = [norm(c) for c in t["rows"][0][1]]
        cells = dict(t["rows"])[i]
        note.append("표 머리: 「%s」" % d.L[t["rows"][0][0]])
        if len(cells) == len(hdr):
            col = dict(zip(hdr, cells))
            CP = r"원고|피고|상대방|거래상대|계약상대|법인명|회사명|조치대상|대상자"
            cps = [col[h] for h in hdr if re.search(CP, h)]
            cp = " / ".join(cell(v) for v in cps if cell(v) and cell(v) != "-")
            am = [col[h] for h in hdr if re.search(r"계약금액|거래금액|^금액", h)]
            amt = " / ".join(cell(v) for v in am if cell(v) and cell(v) != "-")
            sv = [(h, col[h]) for h in hdr if re.search(r"소송가|소가", h)]
            if cp:
                note.append("(판단) counterparty 는 표의 「%s」 칸 원문(소송·제재 표면 그 당사자·대상)" % "·".join(
                    h for h in hdr if re.search(CP, h)))
            else:
                note.append("표에 계약 상대방 칸 없음 — counterparty 빈칸")
            for h, v in sv:
                note.append("「%s」 칸 「%s」 — 계약 금액이 아니라 amount 빈칸" % (h, cell(v)))
        else:
            note.append("행 칸 수(%d)가 머리(%d)와 달라(칸 합침) 칸 이름으로 집지 않음 — counterparty·amount 빈칸" % (len(cells), len(hdr)))
    else:
        note.append("문단 줄 — counterparty·amount 는 원문에서 칸으로 집지 않음(빈칸)")
    note.append("contract_type 은 원문 낱말 「%s」" % "·".join(x["terms"]))
    note.append("(판단) 지주–계열사 사이 계약인지는 원문 행으로만 — 소송·제재 표 행이면 계열사·제3자 일일 수 있음")
    for dc, rc in corr_D:
        note.append("정정 %s: %s" % (dc.rcept, "같은 글" if any(norm(dc.L[y["line"]]) == norm(line) for y in rc["rows"])
                                      else "이 글 없음/바뀜"))
    note += corr_notes
    p13 = ""
    if d.fy == 2025 and d.rcept == t13_rcept(d.corp):
        p = t13_find(d.corp, line)
        p13 = ("; %s(본문 PDF, 13차 보관)" % p) if p else ""
        if not p:
            note.append("13차 본문 PDF 텍스트에서 같은 글 못 찾음")
    if bnote:
        note.append(bnote)
    return dict(counterparty=cp, contract_type=" · ".join(x["terms"]), amount=amt, source_text=line,
                page=d.loc(i) + p13, note="; ".join(note))


# ================================================================ 경영공시 2026.2Q
def mgmt_rows(corp):
    """13차 경영공시 2026.2Q PDF 텍스트 — 작업 B 키워드 문장, 작업 D 업무위탁 현황. BNK·JB 는 미수집 note 행."""
    out = dict(B=[], D=[], sec={})
    if corp in MGMT_NONE:
        nb = ("경영공시 미수집(이번 범위에서 받지 않음) — 13차 경영공시 2026.2Q 텍스트는 8개사뿐이고 %s 는 없음"
              "(handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip 에 경영공시__%s.md 없음)" % (corp, corp))
        out["B"].append(dict(corp_label=corp, fy="2026.2Q", employees_total="", regular="", contract="", keyword="",
                             source_text="", doc_kind="경영공시", rcept_no_or_url="", page="", note=nb,
                             doc_name="", collected_at=""))
        out["D"].append(dict(corp_label=corp, fy="2026.2Q", counterparty="", contract_type="", amount="", source_text="",
                             doc_kind="경영공시", rcept_no_or_url="", page="", note=nb, doc_name="", collected_at=""))
        return out
    meta = next((r for r in csv.DictReader(open(MGMT_CSV, encoding="utf-8-sig")) if r["corp_label"] == corp), None)
    P = t13_pages("경영공시", corp)
    head = P["head"]
    url = meta["url"] if meta else ""
    coll = kst(meta["fetched_at"]) if meta else ""
    name = "%s 경영공시 2026.2Q 「%s」 (13차 보관 PDF 텍스트)" % (corp, meta["제목"] if meta else "")
    where = ("POST 내려받기 — 목록 %s, %s" % (meta["목록"], meta["찾은곳"])) if meta else ""
    b = dict(corp_label=corp, fy="2026.2Q", employees_total="", regular="", contract="", doc_kind="경영공시",
             rcept_no_or_url=url, doc_name=name, collected_at=coll)
    pdfnote = "PDF 쪽 텍스트(pymupdf, 13차 보관 %s)%s" % (
        re.search(r"sha256 \S+", head).group(0) if re.search(r"sha256 \S+", head) else "", "; " + where if where else "")
    hits = []
    for p, ls, nt in P["pages"]:
        for j, l in enumerate(ls):
            for k in KW:
                if k in l:
                    fr = KW_FALSE.get(k)
                    if fr and not re.sub(fr, "", l).count(k):
                        continue
                    hits.append((p, j, k, ls))
    for p, j, k, ls in hits:
        a = j
        while a > 0 and not re.search(r"(다\.|\.)\s*$", ls[a - 1]) and not ls[a - 1].startswith("(") and j - a < 3:
            a -= 1
        z = j
        while z < len(ls) - 1 and not re.search(r"다\.\s*$", ls[z]) and z - j < 3:
            z += 1
        sent = "".join(ls[a:z + 1])
        out["B"].append(dict(b, keyword=k, source_text=sent, page="p.%d" % p,
                             note="직원 수 칸 빈칸(경영공시에서 키워드 문장만 모음); 문장이 PDF 줄에서 끊긴 곳은 줄바꿈만 붙여 씀; " + pdfnote))
        out["sec"][("mgmt", p)] = ("mgmt", corp, p, ls, url, name, coll)
    if not hits:
        out["B"].append(dict(b, keyword="없음", source_text=NONE, page="",
                             note="찾은 범위: 경영공시 2026.2Q PDF 텍스트 전 쪽(%d쪽), 검색어 겸직·파견·출향·전출·전적·겸무"
                                  "(「전적」은 전적으로 등 오탐 뺌) — 없음; %s" % (len(P["pages"]), pdfnote)))
    dh = []
    for p, ls, nt in P["pages"]:
        for j, l in enumerate(ls):
            if D_RE.search(l) or "업무위탁" in norm(l):
                dh.append((p, j, l, ls))
    for p, j, l, ls in dh:
        out["D"].append(dict(corp_label=corp, fy="2026.2Q", counterparty="", contract_type=D_RE.search(l).group(0)
                             if D_RE.search(l) else "업무위탁", amount="", source_text=l, doc_kind="경영공시",
                             rcept_no_or_url=url, page="p.%d" % p, note=pdfnote, doc_name=name, collected_at=coll))
        out["sec"][("mgmt", p)] = ("mgmt", corp, p, ls, url, name, coll)
    if not dh:
        out["D"].append(dict(corp_label=corp, fy="2026.2Q", counterparty="", contract_type="", amount="", source_text=NONE,
                             doc_kind="경영공시", rcept_no_or_url=url, page="", doc_name=name, collected_at=coll,
                             note="찾은 범위: 경영공시 2026.2Q PDF 텍스트 전 쪽(%d쪽, 공백 무시), 검색어 %s — 「업무위탁」 현황 없음"
                                  "(「위탁매매」「투자자문」 같은 업종·회사 이름 낱말만 있음); %s" % (len(P["pages"]), D_TERMS, pdfnote)))
    return out


# ================================================================ 실행
def load_list():
    return [r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig")) if r["label"] in CORPS]


def main():
    lst = load_list()
    docs = {}
    for r in lst:
        if r["text_path"] and os.path.exists(r["text_path"]):
            docs[r["rcept_no"]] = Doc(r)
    work = dict(probs=[], judg=[], h5=[], h5_selfline=[], corr=[], past_tables=[], ctabs={}, sections={})
    A, B, D = [], [], []
    sections = {}       # (task, corp, fy) -> {(rcept, head line): (doc, s, e, n, title)}
    h5_all = list(csv.DictReader(open(H5_CSV, encoding="utf-8-sig")))

    def add_sec(task, d, i):
        s, e, n, title = d.section(i)
        sections.setdefault((task, d.corp, d.fy), {})[(d.rcept, s)] = (d, s, e, n, title)

    def base(d):
        return dict(corp_label=d.corp, fy=str(d.fy), doc_kind=DOC_KIND, rcept_no_or_url=d.rcept,
                    doc_name=d.name, collected_at=d.collected)

    def page13(d, text):
        if d.fy == 2025 and d.rcept == t13_rcept(d.corp):
            p = t13_find(d.corp, text.split("\n")[-1])
            return ("; %s(본문 PDF, 13차 보관)" % p) if p else "", p
        return "", None

    for corp in CORPS:
        for fy in range(2019, 2026):
            items = [r for r in lst if r["label"] == corp and int(r["fy"]) == fy]
            main_r = [r for r in items if r["kind"] == "본"]
            if not main_r:
                work["probs"].append("%s FY%d 본 보고서 없음" % (corp, fy))
                continue
            dm = docs[main_r[0]["rcept_no"]]
            corr = [r for r in items if r["kind"] == "정정"]
            corr_docs, corr_notes = [], []
            for r in corr:
                if r["rcept_no"] not in docs:
                    corr_notes.append("정정 %s(%s): XML 없음(status %s %s) — 비교 못 함" % (
                        r["rcept_no"], r["report_nm"], r["doc_status"], r["doc_message"]))
                    continue
                dc = docs[r["rcept_no"]]
                if "VIII" not in dc.ch:
                    corr_notes.append("정정 %s(%s): Ⅷ~Ⅺ 절 없음(첨부서류 정정) — 비교 대상 아님" % (r["rcept_no"], r["report_nm"]))
                    continue
                corr_docs.append(dc)
            if corr_notes:
                work["corr"] += ["%s FY%d: %s" % (corp, fy, x) for x in corr_notes]

            # ---------------- A
            ra = extract_A(dm)
            work["ctabs"]["%s FY%d %s" % (corp, fy, dm.rcept)] = ra.get("ctabs", [])
            work["probs"] += ["A %s FY%d %s: %s" % (corp, fy, dm.rcept, p) for p in ra["probs"]]
            if ra["past"]:
                work["past_tables"].append("%s FY%d %s: %s" % (corp, fy, dm.rcept, ", ".join(ra["past"])))
            corr_A = [(dc, extract_A(dc)) for dc in corr_docs]
            rowsA = []
            for x in ra["rows"]:
                note = list(x["note"])
                for dc, rc in corr_A:
                    if any(y["cmp"] == x["cmp"] for y in rc["rows"]):
                        note.append("정정 %s: 같은 행" % dc.rcept)
                    elif any(y["key"][:2] == x["key"][:2] for y in rc["rows"]):
                        note.append("정정 %s: 이 겸직 행 글이 바뀜(정정판 행은 따로 1행)" % dc.rcept)
                    else:
                        note.append("정정 %s: 이 행 없음" % dc.rcept)
                note += corr_notes
                rowsA.append((dm, x, note))
            for dc, rc in corr_A:
                nd = 0
                for y in rc["rows"]:
                    if any(y["cmp"] == x["cmp"] for x in ra["rows"]):
                        continue
                    nd += 1
                    note = ["정정 %s: 본 보고서(%s)와 다른 행 — 정정판 글" % (dc.rcept, dm.rcept)] + list(y["note"])
                    rowsA.append((dc, y, note))
                work["corr"].append("A %s FY%d 정정 %s: 본과 다른 겸직 행 %d개" % (corp, fy, dc.rcept, nd))
            past_note = ("; 넣지 않은 지난해 기준 겸직 표: " + ", ".join(ra["past"])) if ra["past"] else ""
            if not rowsA:
                A.append(dict(base(dm), person="", reason_text=NONE, source_text=NONE, page="",
                              note="찾은 범위: Ⅷ 임원 현황 표(주요경력·담당업무 칸)·「회사와 계열회사간 임원 겸직 현황」 표, Ⅸ 겸직 표"
                                   " — 겸직 행 없음" + past_note + ("; " + "; ".join(corr_notes) if corr_notes else "")))
            for d, x, note in rowsA:
                p13, p = page13(d, x["source_text"])
                if d.fy == 2025 and d.rcept == t13_rcept(d.corp) and not p:
                    note.append("13차 본문 PDF 텍스트에서 같은 글 못 찾음")
                note.append("reason_text: 사업보고서에 겸직 사유 글 없음(Ⅷ·Ⅸ 겸직 표·임원 표·주석에서 찾음)")
                if ra["past"] and x["src_kind"] == "table":
                    note.append("넣지 않은 지난해 기준 겸직 표: " + ", ".join(ra["past"]))
                A.append(dict(base(d), person=x["person"], birth_ym=x["birth_ym"], holdco_title=x["holdco_title"],
                              holdco_duty=x["holdco_duty"], registered=x["registered"], fulltime=x["fulltime"],
                              concurrent_company=x["concurrent_company"], concurrent_title=x["concurrent_title"],
                              concurrent_since=x["concurrent_since"], reason_text=NONE, source_text=x["source_text"],
                              page=d.loc(x["lines"][-1]) + p13, note="; ".join(note)))
                for i in x["lines"] + x.get("also_lines", []):
                    add_sec("A", d, i)

            # 5차 대조
            for r in [r for r in h5_all if r["corp_label"] == H5_NAME[corp] and r["구분"] == "지주" and r["fy"] == str(fy)]:
                k = (pname(r["겸직자"]), cname(r["겸직회사"]))
                ours = [a for a in A if a["corp_label"] == corp and a["fy"] == str(fy)
                        and ((k[0] and pname(a["person"]) == k[0] and cname(a["concurrent_company"]) == k[1])
                             or (norm(r["원문행"]) and norm(r["원문행"]) in norm(a["source_text"])))]
                if ours:
                    continue
                dd = docs.get(r["rcept_no"])
                found = dd is not None and norm(r["원문행"]) and any(norm(r["원문행"]) in norm(l) for l in dd.L)
                rec = dict(corp=corp, fy=fy, rcept=r["rcept_no"], person=r["겸직자"], company=r["겸직회사"],
                           title=r["겸직회사_직위"], found_in_md=bool(found), row=r["원문행"][:120])
                if r["겸직회사"] and is_self(corp, r["겸직회사"]):
                    # 5차가 겸직 표의 지주 직위 줄을 겸직으로 센 것 — 우리 행 note 에 「같은 표의 지주 직위 줄」로 있음
                    has = any(a for a in A if a["corp_label"] == corp and a["fy"] == str(fy) and pname(a["person"]) == k[0])
                    rec["ours_same_person"] = has
                    work["h5_selfline"].append(rec)
                else:
                    work["h5"].append(rec)

            # ---------------- B
            rb = extract_B(dm)
            work["probs"] += ["B %s FY%d %s: %s" % (corp, fy, dm.rcept, p) for p in rb["probs"]]
            corr_B = [(dc, extract_B(dc)) for dc in corr_docs]
            st = rb["staff"]
            nums = dict(employees_total=st["total"] if st else "", regular=st["regular"] if st else "",
                        contract=st["contract"] if st else "")
            cn = []
            for dc, rc in corr_B:
                s2 = rc["staff"]
                if s2 and st and norm(dc.L[s2["line"]]) != norm(dm.L[st["line"]]):
                    cn.append("정정 %s: 직원 표 합계 행 바뀜 「%s」" % (dc.rcept, dc.L[s2["line"]]))
                elif s2 and st:
                    cn.append("정정 %s: 직원 표 합계 행 같음" % dc.rcept)
                if s2 and st and [norm(f) for f in s2.get("foot", [])] != [norm(f) for f in st.get("foot", [])]:
                    cn.append("정정 %s: 직원 표 아래 주석 바뀜" % dc.rcept)
            cn += corr_notes
            snote = ""
            if st:
                snote = ("직원 표 합계 행: 칸 순서 합계|기간의 정함이 없는 근로자 전체|(단시간)|기간제 근로자 전체|(단시간)|합계|평균근속|"
                         "연간급여총액|1인평균 — 그 칸 원문 숫자")
                snote += ("; 직원 표 아래 주석: " + " / ".join("「%s」" % f for f in st["foot"])) if st.get("foot") else "; 직원 표 아래 주석 없음"
            if not rb["hits"]:
                p13, p = page13(dm, dm.L[st["line"]]) if st else ("", None)
                B.append(dict(base(dm), keyword="없음", source_text=dm.L[st["line"]] if st else NONE,
                              page=(dm.loc(st["line"]) + p13) if st else "",
                              note="; ".join(x for x in [snote, "Ⅷ 전체(임원·직원 현황 표·주석·보수)에서 겸직·파견·출향·전출·전적·겸무 없음"] + cn if x),
                              **nums))
                if st:
                    add_sec("B", dm, st["line"])
            else:
                if st:
                    add_sec("B", dm, st["line"])
                for h in rb["hits"]:
                    p13, p = page13(dm, h["text"])
                    nn = [snote, "직원 수 칸은 같은 보고서 직원 표 합계 행 값; source_text 는 키워드가 든 줄%s" % (
                        "(긴 문단이라 그 문장만)" if h["text"] != dm.L[h["line"]] else "")]
                    if st:
                        nn.append("합계 행: 「%s」" % dm.L[st["line"]])
                    for dc, rc in corr_B:
                        nn.append("정정 %s: %s" % (dc.rcept, "같은 글" if any(norm(h["text"]) in norm(dc.L[y["line"]])
                                                                       for y in rc["hits"]) else "이 글 없음/바뀜"))
                    nn += corr_notes
                    if dm.fy == 2025 and dm.rcept == t13_rcept(corp) and not p:
                        nn.append("13차 본문 PDF 텍스트에서 같은 글 못 찾음")
                    B.append(dict(base(dm), keyword=h["kw"], source_text=h["text"], page=dm.loc(h["line"]) + p13,
                                  note="; ".join(x for x in nn if x), **nums))
                    add_sec("B", dm, h["line"])
                for dc, rc in corr_B:
                    for h in rc["hits"]:
                        if any(norm(h["text"]) == norm(y["text"]) for y in rb["hits"]):
                            continue
                        s2 = rc["staff"]
                        B.append(dict(base(dc), keyword=h["kw"], source_text=h["text"], page=dc.loc(h["line"]),
                                      employees_total=s2["total"] if s2 else "", regular=s2["regular"] if s2 else "",
                                      contract=s2["contract"] if s2 else "",
                                      note="; ".join(x for x in [
                                          "정정 %s: 본 보고서(%s)에 없는 글 — 정정판 글" % (dc.rcept, dm.rcept), snote,
                                          "직원 수 칸은 같은 정정판 직원 표 합계 행 값",
                                          "합계 행: 「%s」" % dc.L[s2["line"]] if s2 else ""] if x)))
                        add_sec("B", dc, h["line"])
            # 정정판 합계 행이 바뀌었으면 정정판 합계 행도 따로 1행
            for dc, rc in corr_B:
                s2 = rc["staff"]
                if s2 and st and norm(dc.L[s2["line"]]) != norm(dm.L[st["line"]]):
                    B.append(dict(base(dc), keyword="(정정판 합계 행)", source_text=dc.L[s2["line"]], page=dc.loc(s2["line"]),
                                  employees_total=s2["total"], regular=s2["regular"], contract=s2["contract"],
                                  note="정정 %s: 본 보고서(%s) 직원 표 합계 행과 다름 — 정정판 글(본 「%s」)" % (
                                      dc.rcept, dm.rcept, dm.L[st["line"]])))
                    add_sec("B", dc, s2["line"])

            # ---------------- D
            rd = extract_D(dm)
            work["probs"] += ["D %s FY%d %s: %s" % (corp, fy, dm.rcept, p) for p in rd["probs"]]
            corr_D = [(dc, extract_D(dc)) for dc in corr_docs]
            broad = rd["broad"]
            bnote = ""
            if broad:
                ex = []
                for i, w in broad:
                    s = re.sub(r"\s+", " ", dm.L[i])
                    p = s.find(w)
                    ex.append("%s「%s」" % (dm.loc(i).replace("XML ", ""), s[max(0, p - 15): p + 15]))
                bnote = ("(판단) 넓은 검색어(위탁·수탁·자문·전산·IT·공동)가 나온 %d줄은 계약·거래 뜻 낱말이 아니라(매매 위탁·위탁자·"
                         "전산 관련 제재·공동대표 등) 행으로 넣지 않음: %s" % (
                             len(broad), " / ".join(ex[:6]) + (" 외 %d줄" % (len(ex) - 6) if len(ex) > 6 else "")))
            if not rd["rows"]:
                D.append(dict(base(dm), counterparty="", contract_type="", amount="", source_text=NONE, page="",
                              note="; ".join(x for x in [
                                  "찾은 범위: 「%s」~「%s」 절 전체(표·문단)" % (
                                      dm.head_of(rd["rng"][0])[2].strip() if rd["rng"] else "Ⅹ",
                                      "XI. 그 밖에 투자자 보호를 위하여 필요한 사항 끝(XII 상세표 전)"),
                                  "검색어: " + D_TERMS,
                                  "지주·계열사 사이 업무위탁·용역·자문·전산 공동사용 계약·거래 언급 없음", bnote] + corr_notes if x)))
            for x in rd["rows"]:
                D.append(dict(base(dm), **d_fields(dm, x, bnote, corr_D, corr_notes)))
                add_sec("D", dm, x["line"])
            for dc, rc in corr_D:
                for y in rc["rows"]:
                    if any(norm(dc.L[y["line"]]) == norm(dm.L[x["line"]]) for x in rd["rows"]):
                        continue
                    f = d_fields(dc, y, "", [], [])
                    f["note"] = "정정 %s: 본 보고서(%s)에 없는 글 — 정정판 글; " % (dc.rcept, dm.rcept) + f["note"]
                    D.append(dict(base(dc), **f))
                    add_sec("D", dc, y["line"])

        # ---------------- 경영공시 2026.2Q (B·D)
        mg = mgmt_rows(corp)
        B += mg["B"]
        D += mg["D"]
        if mg["sec"]:
            sections.setdefault(("B", corp, "2026.2Q"), {}).update(
                {k: v for k, v in mg["sec"].items() if any(r["page"] == "p.%d" % k[1] for r in mg["B"])})
            dsec = {k: v for k, v in mg["sec"].items() if any(r["page"] == "p.%d" % k[1] for r in mg["D"])}
            if dsec:
                sections.setdefault(("D", corp, "2026.2Q"), {}).update(dsec)

    write_csv(os.path.join(OUT, "A_bs_g3.csv"), A, A_COLS)
    write_csv(os.path.join(OUT, "B_bs_g3.csv"), B, B_COLS)
    write_csv(os.path.join(OUT, "D_bs_g3.csv"), D, D_COLS)
    work["written"] = write_md(sections)
    work["counts"] = {t: count(rows) for t, rows in (("A", A), ("B", B), ("D", D))}
    json.dump(work, open(WORK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(work["counts"], ensure_ascii=False))
    print("probs", len(work["probs"]), "h5 missing", len(work["h5"]), "h5 selfline", len(work["h5_selfline"]))


def count(rows):
    c = {}
    for r in rows:
        k = (r["corp_label"], r["fy"])
        c.setdefault(r["corp_label"], {"rows": 0, NONE: 0, "fy": {}})
        c[r["corp_label"]]["rows"] += 1
        c[r["corp_label"]]["fy"][r["fy"]] = c[r["corp_label"]]["fy"].get(r["fy"], 0) + 1
        if r.get("source_text") == NONE:
            c[r["corp_label"]][NONE] += 1
    return c


def write_md(sections):
    """원문 md 쓰기. 다시 돌릴 때는 지난번에 이 스크립트가 쓴 파일(bs_g3_work.json 의 written)만 지우고 다시 씀."""
    try:
        prev = json.load(open(WORK, encoding="utf-8")).get("written", [])
    except Exception:
        prev = []
    for fn in prev:
        if os.path.exists(fn):
            os.remove(fn)
    written = []
    for (task, corp, fy), secs in sorted(sections.items(), key=lambda x: (x[0][0], x[0][1], str(x[0][2]))):
        os.makedirs(os.path.join(RAWMD, task), exist_ok=True)
        if fy == "2026.2Q":
            fn = os.path.join(RAWMD, task, "%s__2026.2Q__경영공시.md" % corp)
            out = ["# %s 경영공시 2026.2Q — 작업 %s 원문" % (corp, task), "",
                   "행이 나온 PDF 쪽 글 전체를 그대로 옮김(13차 보관 PDF 텍스트, 「## p.N」= PDF 쪽).", ""]
            for k, (m, c, p, ls, url, name, coll) in sorted(secs.items(), key=lambda x: x[0][1]):
                out += ["## %s — p.%d" % (name, p), "",
                        "- 출처: %s · 문서: %s · 위치: p.%d · 수집: %s" % (url, name, p, coll), "", "```text"] + ls + ["```", ""]
            open(fn, "w", encoding="utf-8").write("\n".join(out))
            written.append(fn)
            continue
        fn = os.path.join(RAWMD, task, "%s__FY%d__사업보고서.md" % (corp, fy))
        out = ["# %s FY%d 사업보고서 — 작업 %s 원문" % (corp, fy, task), "",
               "조각 행의 source_text 가 나온 절 전체(절 머리 「### [절 n] …」부터 다음 절 머리 전까지)를 md(=OpenDART XML) 글자 그대로 옮김.", ""]
        for k, (d, s, e, n, title) in sorted(secs.items(), key=lambda x: (x[1][0].kind != "본", x[0][0], x[0][1])):
            out += ["## %s — [절 %d] %s" % (d.name, n, title.strip()), "",
                    "- 출처: 접수번호 %s (%s) · 문서: %s · 위치: XML [절 %d] 「%s」 · 수집: %s · md: %s" % (
                        d.rcept, d.kind, d.name, n, title.strip(), d.collected, d.path), "", "```text"]
            out += d.L[s:e]
            out += ["```", ""]
        open(fn, "w", encoding="utf-8").write("\n".join(out))
        written.append(fn)
    return sorted(written)


if __name__ == "__main__":
    main()
