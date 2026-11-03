# -*- coding: utf-8 -*-
"""15차 — 사업보고서 FY2019~FY2025 (g2: NH농협금융지주·메리츠금융지주·iM금융지주) 에서 작업 A·B·D 조각을 뽑는다.

    python3 scripts/dart/ops15_bs_g2.py          # 조각 CSV 3개 + 원문 md + 점검 기록(work json)

입력(모두 로컬, 웹 요청·API 키 없음):
  dart_out/ops15/사업보고서_원문.csv 의 세 회사 행(본·정정) → text_path md(OpenDART XML 을 옮긴 것, 「### [절 n]」·「[표 n]」).
  handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip — FY2025 사업보고서 본문 PDF 텍스트(쪽 번호 찾기)와
    경영공시 2026.2Q PDF 텍스트(작업 B·D 의 2026.2Q 행). 경영공시 출처 url·fetched_at 은 dart_out/risk8/경영공시_2026_2Q.csv.
  handoff/겸직현황_정리.csv — 5차 겸직 행(대조용).
산출:
  dart_out/ops15/조각/A_bs_g2.csv · B_bs_g2.csv · D_bs_g2.csv (utf-8-sig)
  dart_out/ops15/원문/{A,B,D}/<회사>__FY<fy>__사업보고서.md (행이 나온 절 전체 + 출처 줄), 경영공시는 <회사>__2026.2Q__경영공시.md
  dart_out/ops15/조각/bs_g2_work.json (5차 대조·정정 비교·판단 기록)
글자는 md(=XML) 그대로 옮긴다. source_text 는 표 행이면 md 의 「| … |」 줄 그대로, 문단이면 그 줄(문장) 그대로.
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
CORPS = ["NH농협금융지주", "메리츠금융지주", "iM금융지주"]
H5_NAME = {"NH농협금융지주": "농협금융지주", "메리츠금융지주": "메리츠금융지주", "iM금융지주": "iM금융지주"}
# 지주 자기 이름(경력 칸의 現 표시가 지주 자신을 가리키면 겸직 아님)
SELF = {"NH농협금융지주": ["농협금융지주", "NH농협금융지주"], "메리츠금융지주": ["메리츠금융지주"],
        "iM금융지주": ["iM금융지주", "DGB금융지주"]}
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
# 작업 D — 계약·거래 뜻의 낱말(지주·계열사 업무위탁·용역·자문·전산 공동). 넓은 낱말은 따로 세어 note 에만.
D_RE = re.compile(r"업무\s*위\s*[·ㆍ]?\s*수탁|업무\s*위탁|업무\s*수탁|위\s*[·ㆍ]\s*수탁|위수탁|위탁\s*계약|수탁\s*계약|"
                  r"용역|경영\s*자문|자문\s*계약|자문\s*료|자문\s*수수료|공동\s*사용|공동\s*이용|시스템\s*공동|"
                  r"전산\s*공동|IT\s*공동|공동\s*전산")
D_BROAD = re.compile(r"위탁|수탁|자문|전산|(?<![A-Za-z])IT(?![A-Za-z])|공동")


# ================================================================ 공통 도구
def norm(t):
    """비교용: <br>·&cr;·공백·「|」를 뺀 글."""
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    return re.sub(r"[\s|]+", "", t)


def cell(t):
    """칸 값: 칸 안 줄바꿈 표시(<br>·&cr;)만 띄어쓰기로 바꾸고 앞뒤 공백을 걷음(글자는 그대로)."""
    return re.sub(r"(<br>|&cr;)", " ", t or "").strip()


def pname(t):
    """성명 비교 키: 괄호 표시(등기임원)·(주)·공백 제거."""
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    t = re.sub(r"\(.*?\)", "", t)
    return re.sub(r"\s+", "", t)


def cname(t):
    t = (t or "").replace("<br>", "").replace("&cr;", "")
    t = re.sub(r"\(주\)|㈜|주식회사|\(비상장\)|\(상장\)", "", t)
    return re.sub(r"[\s·ㆍ]+", "", t)


def bnorm(b):
    """출생년월 비교 키(YYYY.MM). '61.12 → 1961.12 (판단: 두 자리 해는 19xx)."""
    b = (b or "").strip()
    m = re.search(r"(\d{4})\D+(\d{1,2})", b)
    if m:
        return "%s.%02d" % (m.group(1), int(m.group(2)))
    m = re.search(r"'(\d{2})\.(\d{1,2})", b)
    if m:
        return "19%s.%02d" % (m.group(1), int(m.group(2)))
    return b


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
        """표 앞 글줄(원문) — 바로 앞 작은 기준일 표·빈 줄은 건너뛰고, 머리 글줄(※·가.·1)·(1)·마-1. 등)이 나오면 거기까지."""
        out = []
        i = t["start"] - 1
        while i >= 0 and t["start"] - i <= back and len(out) < 3:
            l = self.L[i].strip()
            if l == "[표 끝]":
                k = i - 1
                while k >= 0 and not re.match(r"\[표 \d+\]$", self.L[k]):
                    k -= 1
                if i - k - 1 > 2:
                    break            # 앞이 큰 표면 멈춤(작은 기준일 표만 건너뜀)
                i = k - 1
                continue
            if l.startswith("### "):
                break
            if l and not l.startswith("|") and re.sub(r"(&cr;|\s)", "", l):
                out.append(l)
                if re.match(r"(※|[가-하]\.|[가-하]-\d\.|\d+\)|\(\d+\)|\d+\.)", re.sub(r"^(&cr;|\s)+", "", l)) or "현황" in l:
                    break
            i -= 1
        return out

    def prev_table(self, t):
        k = self.tables.index(t)
        return self.tables[k - 1] if k else None

    def doc_name(self):
        return "%s — %s (접수 %s, %s)" % (self.name, self.corp, self.rcept, self.kind)


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
        _T13[key] = dict(pages=[(p, ls, norm("".join(ls))) for p, ls in pages], head=head)
    return _T13[key]


def t13_rcept(corp):
    m = re.search(r"dart_out/doc/(\d+)/", t13_pages("사업보고서", corp)["head"])
    return m.group(1) if m else ""


def t13_find(corp, text):
    """같은 글이 있는 PDF 쪽(들). 긴 행은 앞 40자로, 쪽 경계에 걸치면 이어 붙여 봄."""
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


# ================================================================ 임원 현황 표
def exec_tables(d, rng):
    """Ⅷ 안 임원 현황 표들: [(table, kind_label, rows:[dict])]."""
    out = []
    first = True
    for t in d.tables:
        if not (rng[0] <= t["start"] < rng[1]) or not t["rows"]:
            continue
        h = [norm(c) for c in t["rows"][0][1]]
        if not (h and h[0] == "성명" and len(h) > 7 and h[1] == "성별" and "출생" in h[2]):
            continue
        cap = " / ".join(d.caption(t))
        if first and "이후" not in cap:
            kind = "기준일"
        else:
            kind = "이후"
        first = False
        rows = []
        for i, c in t["rows"][1:]:
            if len(c) < 8 or norm(c[0]).startswith("의결권"):
                continue
            rows.append(dict(line=i, name=cell(c[0]), key=pname(c[0]), birth=cell(c[2]), bkey=bnorm(cell(c[2])),
                             title=cell(c[3]), reg=cell(c[4]), ft=cell(c[5]), duty=cell(c[6]), career=c[7],
                             duty_raw=c[6], table=t, tkind=kind, cap=cap))
        out.append((t, kind, cap, rows))
    return out


# ================================================================ 겸직 표
def concurrent_tables(d, rngs):
    out = []
    for t in d.tables:
        if not any(a <= t["start"] < b for a, b in rngs) or not t["rows"]:
            continue
        h = norm(" ".join(t["rows"][0][1]))
        if not re.search(r"대상계열사|대상회사|겸직대상자|계열회사겸직내역", h):
            continue
        hdr = [norm(c) for c in t["rows"][0][1]]
        fmt = "meritz" if "겸직대상자" in h else ("f4" if len(hdr) == 4 else "f5")
        ncol = {"meritz": 5, "f4": 4, "f5": 5}[fmt]
        body = t["rows"][2:] if fmt == "meritz" else t["rows"][1:]
        # 기준일: 앞 작은 표 「(기준일 : …)」 또는 앞 글줄
        cap = d.caption(t)
        pt = d.prev_table(t)
        basis = ""
        for c in cap:
            m = re.search(r"기준일\s*:?\s*(\d[0-9.년월일 ]*)|\(([0-9.]+)\s*기준\)|([0-9]{4}\.[0-9.]+)\s*기준", c)
            if m:
                basis = (m.group(1) or m.group(2) or m.group(3) or "").strip()
                break
        if not basis and pt and pt["end"] == t["start"] - 1 and len(pt["rows"]) == 1:
            m = re.search(r"기준\s*<br>\s*일|기준일", pt["rows"][0][1][0] + "".join(pt["rows"][0][1]))
            if m:
                basis = re.sub(r"(<br>|&cr;|\(|\)|기준|일\s*:)", "", " ".join(pt["rows"][0][1])).strip(" :")
        capj = " / ".join(cap)
        my = re.search(r"(\d{4})", basis)
        after = bool(re.search(r"이후|제출일", capj)) or bool(my and int(my.group(1)) > d.fy)
        group = bool(re.search(r"그룹\s*임원\s*겸직", capj))
        rows, prev = [], None
        for i, c in body:
            if len(c) == ncol:
                nm, rest = c[0], c[1:]
            elif len(c) == ncol - 1 and prev is not None:
                nm, rest = prev, c
            else:
                rows.append(dict(line=i, bad=True, cells=c))
                continue
            prev = nm
            rec = dict(line=i, name=cell(nm), key=pname(nm), mark=re.findall(r"\((?:주\d*|등기임원|미등기임원)\)", nm), company=cell(rest[0]), ckey=cname(rest[0]),
                       title=cell(rest[1]), tkey=norm(rest[1]), table=t, after=after, group=group, basis=basis,
                       cap=capj, cont=(len(c) == ncol - 1))
            if fmt == "meritz":
                rec.update(since="", remark=cell(rest[2]), remark2=cell(rest[3]))
            elif fmt == "f4":
                rec.update(since=cell(rest[2]), remark="", remark2="")
            else:
                rec.update(since=cell(rest[2]), remark=cell(rest[3]), remark2="")
            rec["name_line"] = None
            if rec["cont"]:
                # 이름이 위 행에 있는 행 — 이름 줄을 같이 source_text 로
                for j in range(len(rows) - 1, -1, -1):
                    if not rows[j].get("bad") and not rows[j]["cont"] and rows[j]["key"] == rec["key"]:
                        rec["name_line"] = rows[j]["line"]
                        break
            rows.append(rec)
        # 표 바로 아래 각주(작은 표 또는 글줄) — 성명 칸 (주) 표시 풀이용
        foot = ""
        k = d.tables.index(t)
        nt = d.tables[k + 1] if k + 1 < len(d.tables) else None
        if nt and nt["start"] - t["end"] <= 2 and len(nt["rows"]) == 1 and re.match(r"\(?주", nt["rows"][0][1][0]):
            foot = d.L[nt["rows"][0][0]]
        else:
            for j in range(t["end"] + 1, min(t["end"] + 4, len(d.L))):
                if re.match(r"\s*\(주\d*\)|\s*주\d*\)", d.L[j]):
                    foot = d.L[j]
                    break
        out.append(dict(table=t, fmt=fmt, basis=basis, after=after, group=group, cap=capj, foot=foot,
                        chap=("VIII" if t["start"] < d.ch.get("IX", 10 ** 9) else "IX"), rows=rows))
    return out


# ================================================================ 임원 현황 칸(현직 표시·겸직)
PREFIX = re.compile(r"\(\s*現\s*\)|現\s*\)|\(\s*현\s*\)|現(?=\s*[^\s)])")
SUFFIX = re.compile(r"\(([^()]*?~\s*)?(現|현재|현)\s*\)")


def career_entries(text):
    """경력 칸에서 현직 표시(現·(現)·現)·(…~현재))가 붙은 조각을 원문 그대로 뽑음 → [(조각, 표시, 경계 애매 여부)].

    칸 안 줄바꿈: <br> 은 경력 구분, &cr; 은 뒤에 글머리(-·○•)가 오면 구분·아니면 한 경력 안 줄바꿈(띄어쓰기)으로 봄.
    「·」 글머리 칸(칸이 「·」로 시작)은 「·」에서도 나눔. 「(<br>現<br>)」처럼 줄로 갈라진 표시는 「(現)」로 붙여 봄.
    """
    t = text or ""
    t = re.sub(r"\(\s*(?:<br>\s*|&cr;\s*)*現\s*(?:<br>\s*|&cr;\s*)*\)", "(現)", t)
    t = re.sub(r"&cr;(?=\s*[-·○•])", "<br>", t).replace("&cr;", " ")
    bullet_dot = t.strip().startswith("·")
    pieces = []
    for p in t.split("<br>"):
        pieces += p.split("·") if bullet_dot else [p]
    out = []
    last_nonempty = None
    n_pieces = len([p for p in pieces if p.strip()])
    for p in pieces:
        ps = p.strip()
        if not ps:
            continue
        if re.fullmatch(r"\(\s*現\s*\)|現", ps):
            if last_nonempty is not None:
                out.append((last_nonempty, ps, "sep"))
            continue
        # 글머리 「- 」 로 나뉜 조각
        subs = [s for s in re.split(r"(?:^|(?<=[^\s~\-–]))\s*-\s+(?=\S)|^-(?=\S)", ps) if s and s.strip()]
        for s in subs:
            s0 = s.strip()
            last_nonempty = s0.lstrip("-").strip()
            found = False
            for m in PREFIX.finditer(s0):
                nxt = PREFIX.search(s0, m.end())
                seg = s0[m.end(): nxt.start() if nxt else len(s0)].strip(" -,·ㆍ")
                seg = SUFFIX.sub("", seg).strip()
                if seg:
                    out.append((seg, m.group(0).strip(), ""))
                    found = True
            if found:
                continue
            for m in SUFFIX.finditer(s0):
                b = s0.rfind(")", 0, m.start()) + 1
                seg = s0[b:m.start()].strip(" -,·ㆍ")
                if seg:
                    out.append((seg, m.group(0), "space" if (b == 0 and len(seg.split()) >= 3 and len(subs) == 1
                                                             and n_pieces == 1) else ""))
    return out


def nm_raw(d, rec):
    """겸직 표 성명 칸 원문(칸 합침 행이면 이름 줄의 칸)."""
    i = rec["line"] if rec["name_line"] is None else rec["name_line"]
    return d.L[i].strip()[1:-1].split("|")[0].strip()


def split_cn(seg):
    """→ (회사, 직위, 기간 괄호 원문). 끝의 「(2020~)」「(2009~)」 같은 기간 괄호는 떼어 since 로."""
    seg = seg.strip()
    since = ""
    seg = seg.strip(" ·ㆍ,")
    m = re.search(r"\s*\(([^()]*\d{2,4}[^()]*~[^()]*)\)\s*[·ㆍ,]?\s*$", seg)
    if m:
        since = m.group(1).strip()
        seg = seg[:m.start()].strip()
    if " " in seg:
        a, b = seg.rsplit(" ", 1)
        return a.strip(), b.strip(), since
    return seg, "", since


# ================================================================ 작업 A — 한 보고서
def extract_A(d):
    r8 = d.chap_range("VIII", ["IX", "X", "XI", "XII"])
    r9 = d.chap_range("IX", ["X", "XI", "XII"])
    res = dict(rows=[], probs=[], execs=[], ctabs=[], r8=r8, r9=r9)
    if not r8:
        res["probs"].append("Ⅷ 절 없음")
        return res
    ets = exec_tables(d, r8)
    execs = [e for t, k, c, rs in ets for e in rs]
    res["execs"] = execs
    rngs = [r8] + ([r9] if r9 else [])
    cts = concurrent_tables(d, rngs)
    res["ctabs"] = cts

    def find_exec(key, after=False):
        base = [e for e in execs if e["key"] == key and e["tkind"] == "기준일"]
        aft = [e for e in execs if e["key"] == key and e["tkind"] != "기준일"]
        cand = (aft + base) if after else (base + aft)
        births = sorted(set(e["bkey"] for e in cand))
        return (cand[0] if cand else None), births

    # 순서: 기준일 표(Ⅷ→Ⅸ 개별→Ⅸ 그룹) → 이후 표
    order = sorted(cts, key=lambda c: (c["after"], c["group"], c["table"]["start"]))
    kept = []
    for ct in order:
        for rec in ct["rows"]:
            if rec.get("bad"):
                res["probs"].append("겸직 표 행 칸 수 다름 [표 %d] 줄 %d" % (ct["table"]["no"], rec["line"] + 1))
                continue
            if any(rec["ckey"] and s in rec["ckey"] for s in [cname(x) for x in SELF[d.corp]]):
                continue        # 그룹 표의 지주 자기 직위 줄(겸직 상대 회사 아님) — note 로만
            dup = None
            for k in kept:
                if k["key"] == rec["key"] and k["ckey"] == rec["ckey"] and (
                        k["tkey"] == rec["tkey"] or (k["since"] and k["since"] == rec["since"])):
                    dup = k
                    break
            if dup:
                diff = []
                if dup["tkey"] != rec["tkey"]:
                    diff.append("직책 「%s」" % rec["title"])
                if norm(dup["since"]) != norm(rec["since"]):
                    diff.append("선임시기 「%s」" % rec["since"])
                dup.setdefault("also_lines", []).append(rec["line"])
                dup.setdefault("also", []).append(
                    "[표 %d]%s%s" % (rec["table"]["no"], "(작성기준일 이후 %s)" % rec["basis"] if rec["after"] else "",
                                    "에서는 " + "·".join(diff) if diff else ""))
                continue
            kept.append(rec)
    for rec in kept:
        e, births = find_exec(rec["key"], rec["after"])
        lines = [rec["line"]] if rec["name_line"] is None else [rec["name_line"], rec["line"]]
        src = "\n".join(d.L[i] for i in lines)
        note = []
        ct_tab = rec["table"]
        where = "Ⅷ" if ct_tab["start"] < (r9[0] if r9 else 10 ** 9) else "Ⅸ"
        note.append("%s 겸직 표 「%s」%s" % (where, rec["cap"][:80], " 기준일 " + rec["basis"] if rec["basis"] else ""))
        if rec["after"]:
            note.append("작성기준일 이후 표에만 있는 행")
        if rec["group"]:
            note.append("그룹 임원 겸직 표(자회사·지주 직위를 함께 적은 표)")
            hold = [x for c2 in cts if c2["table"] is ct_tab for x in c2["rows"]
                    if not x.get("bad") and x["key"] == rec["key"] and any(cname(s) in x["ckey"] for s in SELF[d.corp])]
            if hold:
                note.append("같은 표의 지주 직위 줄: 「%s」 %s %s" % (hold[0]["title"], hold[0]["since"], hold[0]["remark"]))
        if rec["mark"]:
            ftxt = next((c2["foot"] for c2 in cts if c2["table"] is ct_tab), "")
            note.append("성명 칸 원문 「%s」(표시 %s)%s" % (d.L[rec["line"] if rec["name_line"] is None else rec["name_line"]]
                                                       .split("|")[1].strip(), "".join(rec["mark"]),
                                                       " — 표 아래 각주 「%s」" % ftxt.strip("| ") if ftxt and "주" in "".join(rec["mark"]) else ""))
        if rec["remark"] or rec["remark2"]:
            note.append("겸직 표 비고/상근여부: 「%s」" % " / ".join(x for x in (rec["remark"], rec["remark2"]) if x))
        if rec["name_line"] is not None:
            note.append("이름이 윗줄에 있는 행(칸 합침) — source_text 는 이름 줄과 그 행 두 줄")
        if not rec["since"]:
            note.append("겸직 표에 선임시기 칸 없음" if ct_tab["rows"] and "선임" not in norm(" ".join(ct_tab["rows"][0][1]))
                        else "선임시기 칸 비어 있음")
        if rec.get("also"):
            note.append("같은 행: " + ", ".join(rec["also"]))
        if e is None:
            note.append("같은 보고서 임원 현황 표에 이 성명 없음 — 지주 직위·담당업무·등기·상근·출생년월 빈칸")
        else:
            if e["tkind"] != "기준일":
                note.append("지주 쪽 칸은 작성기준일 이후 임원 표(%s)에서" % e["cap"][:40])
            if len(births) > 1:
                note.append("(판단) 같은 성명이 같은 보고서 임원 표들에 출생년월 %s 로 다르게 적힘 — 겸직 표 쪽(%s)에 맞는 임원 표 행으로 맞춤; "
                            "동일인 여부는 원문으로 가리지 않음" % ("·".join(births), "작성기준일 이후 표" if rec["after"] else "작성기준일 표"))
        res["rows"].append(dict(
            src_kind="table", person=re.sub(r"\s*\((?:주\d*|등기임원|미등기임원)\)\s*", "",
                                            re.sub(r"<br>|&cr;", "", nm_raw(d, rec))).strip(), birth_ym=e["birth"] if e else "", holdco_title=e["title"] if e else "",
            holdco_duty=e["duty"] if e else "", registered=e["reg"] if e else "", fulltime=e["ft"] if e else "",
            concurrent_company=rec["company"], concurrent_title=rec["title"], concurrent_since=rec["since"],
            source_text=src, line=rec["line"], lines=lines, also_lines=rec.get("also_lines", []), note=note,
            key=(rec["key"], rec["ckey"], rec["tkey"]),
            cmp=norm(src)))

    # --- 임원 표 각주의 겸직 글(이름이 있는 것)
    names = {e["key"]: e for e in execs}
    exec_lines = set(e["line"] for e in execs)
    for t in d.tables:
        if not (r8[0] <= t["start"] < r8[1]):
            continue
        for i, c in t["rows"]:
            if i in exec_lines:
                continue
            txt = " ".join(c)
            if "겸직" not in txt:
                continue
            for m in re.finditer(r"(?:\(주\d*\)\s*)?([가-힣]{2,4})\s+(\S+?)\(원소속\)\s*(.+?)\s*겸직(종료)?", txt.replace("<br>", "\n")):
                key = pname(m.group(1))
                if key not in names:
                    continue
                if any(r["src_kind"] == "table" and r["key"][0] == key and cname(m.group(2)) in r["key"][1]
                       for r in res["rows"]):
                    continue
                e = names[key]
                note = ["임원 현황 표 각주에서 — 겸직 표에 없음", "각주 글: 「%s」" % m.group(0).strip()]
                if m.group(4):
                    note.append("각주에 「겸직종료」")
                note.append("지주 쪽 칸은 임원 표(%s) 행에서" % ("작성기준일 현재" if e["tkind"] == "기준일" else e["cap"][:40]))
                sb = sorted(set(x["bkey"] for x in execs if x["key"] == key))
                if len(sb) > 1:      # 15차 검증 보탬: 동명이인 표시
                    note.append("(판단) 같은 성명이 같은 보고서 임원 표에 출생년월 %s 로 나옴 — 각주에는 출생년월이 없어 %s 행으로 맞춤; "
                                "동일인 여부는 원문으로 가리지 않음" % ("·".join(sb), e["bkey"]))
                res["rows"].append(dict(
                    src_kind="footnote", person=e["name"], birth_ym=e["birth"], holdco_title=e["title"],
                    holdco_duty=e["duty"], registered=e["reg"], fulltime=e["ft"],
                    concurrent_company=m.group(2), concurrent_title=m.group(3).strip(), concurrent_since="",
                    source_text=d.L[i], line=i, lines=[i], note=note,
                    key=(key, cname(m.group(2)), norm(m.group(3))), cmp=norm(m.group(0))))

    # --- 임원 현황 칸(담당업무 「겸직」·주요경력 현직 표시)
    seen = set()
    ckeys = {}
    for r in res["rows"]:
        ckeys.setdefault(r["key"][0], set()).add(r["key"][1])
    selfk = [cname(s) for s in SELF[d.corp]]
    for e in execs:
        items = []
        if "겸직" in e["duty"]:
            items.append(("duty", e["duty"], "", e["duty"], "담당업무 칸 「겸직」", ""))
        for seg, mk, amb in career_entries(e["career"]):
            if any(s in cname(seg) for s in selfk):
                continue
            co, ti, sn = split_cn(seg)
            m2 = re.match(r"\(([^()]*?)~\s*(現|현재|현)\s*\)", mk)
            if m2 and not sn:
                sn = mk.strip("()")
            why = "주요경력 칸 현직 표시 「%s」" % mk
            if amb == "sep":
                why += "; (판단) 「現」 표시가 칸 안 줄바꿈으로 따로 떨어져 있어 바로 앞 경력에 붙여 봄"
            elif amb == "space":
                why += "; (판단) 앞 경력과 띄어쓰기로만 이어져 조각 경계가 애매 — 앞부분이 다른 경력일 수 있음"
            items.append(("career", seg, co, ti, why, sn))
        for kind, seg, co, ti, why, *rest in items:
            k = (e["key"], e["bkey"], norm(seg))
            if k in seen:
                continue
            seen.add(k)
            cov = ckeys.get(e["key"], set())
            if kind == "duty":
                if cov:
                    continue        # 같은 사람이 겸직 표에 있음(담당업무 「(겸직)」 표시는 그 행이 받음)
            else:
                if any(c and (c in cname(seg) or cname(seg) in c) for c in cov):
                    continue
            note = ["임원 현황 칸에서 — 겸직 표에 없음", why]
            if kind == "duty":
                note.append("(판단) 담당업무 칸에 겸직 상대 회사가 적혀 있지 않음 — concurrent_company 빈칸")
            else:
                note.append("(판단) 경력 조각 「%s」을 마지막 띄어쓰기에서 회사·직위로 나누고 끝 기간 괄호는 concurrent_since 로" % seg)
            if e["tkind"] != "기준일":
                note.append("작성기준일 이후 임원 표(%s)" % e["cap"][:40])
            sb = sorted(set(x["bkey"] for x in execs if x["key"] == e["key"]))
            if len(sb) > 1:          # 15차 검증 보탬: 동명이인 표시
                note.append("같은 성명이 같은 보고서 임원 표에 출생년월 %s 로 나옴(동명이인이거나 표기 차이) — 이 행은 출생년월 %s 인 "
                            "임원 표 행의 칸에서 나옴(출생년월로 구분)" % ("·".join(sb), e["bkey"]))
            res["rows"].append(dict(
                src_kind="cell", person=e["name"], birth_ym=e["birth"], holdco_title=e["title"], holdco_duty=e["duty"],
                registered=e["reg"], fulltime=e["ft"], concurrent_company=co if kind == "career" else "",
                concurrent_title=ti if kind == "career" else "", concurrent_since=rest[0] if rest else "",
                source_text=d.L[e["line"]],
                line=e["line"], lines=[e["line"]], note=note, key=(e["key"], cname(co), norm(ti)),
                cmp=re.sub(r"[·,.\-]", "", norm(e["name"] + e["bkey"] + seg))))
    return res


# ================================================================ 작업 B — 한 보고서
def staff_table(d, r8):
    for t in d.tables:
        if not (r8[0] <= t["start"] < r8[1]) or len(t["rows"]) < 3:
            continue
        h = norm(" ".join(" ".join(c) for i, c in t["rows"][:4]))
        if "직원수" in h.replace(" ", "") or ("직원" in h and "기간의정함" in h):
            tot = [(i, c) for i, c in t["rows"] if re.fullmatch(r"합\s*계|합계|총\s*계|계", norm(c[0]))]
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
    """문단 줄이 길면 그 낱말이 든 문장만(원문 조각 그대로)."""
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
    res = dict(staff=None, hits=[], probs=[])
    if not r8:
        res["probs"].append("Ⅷ 절 없음")
        return res
    t, tot = staff_table(d, r8)
    if t is None:
        res["probs"].append("직원 현황 표(합계 행) 못 찾음")
    else:
        i, c = tot[-1]
        hdr = norm(" ".join(" ".join(x) for j, x in t["rows"][:4]))
        # 합계 행: 합계 | 정함없는(전체) | (단시간) | 기간제(전체) | (단시간) | 합계 | 평균근속 | 급여총액 | 1인평균 | …
        res["staff"] = dict(line=i, cells=c, total=c[5] if len(c) > 5 else "", regular=c[1] if len(c) > 1 else "",
                            contract=c[3] if len(c) > 3 else "", table=t, n_tot=len(tot), hdr=hdr)
        if len(tot) > 1:
            res["probs"].append("직원 표 합계 행 %d개 — 마지막 행을 씀" % len(tot))
        # 표 아래 각주(주·※·* 로 시작하는 글줄 또는 1행 표) — note 에 원문 그대로
        foot = []
        j = t["end"] + 1
        while j < min(t["end"] + 12, r8[1]):
            l = d.L[j].strip()
            if re.match(r"\[표 \d+\]$", l):
                nxt = d.L[j + 1].strip() if j + 1 < len(d.L) else ""
                if re.match(r"\|\s*(\(주|주\d|※|\*)", nxt):
                    j += 1
                    while j < len(d.L) and d.L[j] != "[표 끝]":
                        if d.L[j].startswith("|"):
                            foot.append(d.L[j])
                        j += 1
                    j += 1
                    continue
                break
            if re.match(r"(\(주|주\d*\)|※|\*)", l):
                foot.append(l)
            elif l and not re.match(r"(&cr;)+$", l):
                break
            j += 1
        res["staff"]["foot"] = foot
        # 표 바로 아래 각주(표·글) — 원문 md 에 함께 들어감(절 전체)
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
    """계약·거래가 아닌 쓰임 (판단): 「업무수탁자」(사람·대상 이름), 「…」 안 규정·문서 이름 속 낱말."""
    if l[m.end(): m.end() + 1] == "자":
        return True
    tail = re.split(r"[,，、|]", l[m.end(): m.end() + 25])[0]
    if re.search(r"업무방법|규정|준칙|지침|매뉴얼", tail):
        return True             # 「외주용역 보안관리 업무방법」 같은 내규 이름
    a = l.rfind("「", 0, m.start())
    if a >= 0 and l.find("」", a) > m.start() and l.rfind("」", 0, m.start()) < a:
        return True
    return False


# ================================================================ 실행
def load_list():
    rows = [r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig")) if r["label"] in CORPS]
    return rows


def main():
    lst = load_list()
    docs = {}
    for r in lst:
        if r["text_path"] and os.path.exists(r["text_path"]):
            docs[r["rcept_no"]] = Doc(r)
    work = dict(probs=[], judg=[], h5=[], corr=[], sections={})
    A, B, D = [], [], []
    sections = {}       # (task, corp, fy) -> {(rcept, head line): (doc, s, e, n, title)}

    def add_sec(task, d, i):
        s, e, n, title = d.section(i)
        sections.setdefault((task, d.corp, d.fy), {})[(d.rcept, s)] = (d, s, e, n, title)

    def base(d):
        return dict(corp_label=d.corp, fy=str(d.fy), doc_kind=DOC_KIND, rcept_no_or_url=d.rcept,
                    doc_name=d.name, collected_at=d.collected)

    def page13(d, text):
        if d.fy == 2025 and d.rcept == t13_rcept(d.corp):
            p = t13_find(d.corp, text)
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

            # ---------------- A
            ra = extract_A(dm)
            work["probs"] += ["A %s FY%d %s: %s" % (corp, fy, dm.rcept, p) for p in ra["probs"]]
            corr_A = [(dc, extract_A(dc)) for dc in corr_docs]
            rowsA = []
            for x in ra["rows"]:
                note = list(x["note"])
                for dc, rc in corr_A:
                    same = any(y["cmp"] == x["cmp"] for y in rc["rows"])
                    if same:
                        note.append("정정 %s: 같은 행" % dc.rcept)
                    else:
                        alt = [y for y in rc["rows"] if y["key"][:2] == x["key"][:2]]
                        if alt:
                            note.append("정정 %s: 이 겸직 행 글이 바뀜(정정판 행은 따로 1행)" % dc.rcept)
                        else:
                            note.append("정정 %s: 이 행 없음" % dc.rcept)
                note += corr_notes
                rowsA.append((dm, x, note, False))
            for dc, rc in corr_A:
                for y in rc["rows"]:
                    if any(y["cmp"] == x["cmp"] for x in ra["rows"]):
                        continue
                    note = ["정정 %s: 본 보고서(%s)와 다른 행 — 정정판 글" % (dc.rcept, dm.rcept)] + list(y["note"])
                    rowsA.append((dc, y, note, True))
            if not rowsA:
                rng = ra.get("r8")
                A.append(dict(base(dm), person="", reason_text=NONE, source_text=NONE,
                              page=range_page(dm, (rng[0], (ra.get("r9") or rng)[1])) if rng else "",
                              note="찾은 범위: Ⅷ 임원 현황 표·임원 표 각주·「타회사 임원 겸직/겸임」「계열회사간 임원 겸직」 표, Ⅸ 겸직 표"
                                   " — 겸직 행 없음" + ("; " + "; ".join(corr_notes) if corr_notes else "")))
            for d, x, note, is_corr in rowsA:
                p13, p = page13(d, x["source_text"])
                if d.fy == 2025 and d.rcept == t13_rcept(d.corp) and not p:
                    note.append("13차 본문 PDF 텍스트에서 같은 글 못 찾음")
                note.append("reason_text: 사업보고서에 겸직 사유 글 없음(Ⅷ·Ⅸ 겸직 표·임원 표·각주에서 찾음)")
                A.append(dict(base(d), person=x["person"], birth_ym=x["birth_ym"], holdco_title=x["holdco_title"],
                              holdco_duty=x["holdco_duty"], registered=x["registered"], fulltime=x["fulltime"],
                              concurrent_company=x["concurrent_company"], concurrent_title=x["concurrent_title"],
                              concurrent_since=x["concurrent_since"], reason_text=NONE, source_text=x["source_text"],
                              page="; ".join(d.loc(i) for i in x["lines"][-1:]) + p13, note="; ".join(note)))
                for i in x["lines"] + x.get("also_lines", []):
                    add_sec("A", d, i)
        
            # 5차 대조(FY2023~2025)
            h5 = [r for r in csv.DictReader(open(H5_CSV, encoding="utf-8-sig"))
                  if r["corp_label"] == H5_NAME[corp] and r["구분"] == "지주" and r["fy"] == str(fy)]
            for r in h5:
                k = (pname(r["겸직자"]), cname(r["겸직회사"]))
                ours = [a for a in A if a["corp_label"] == corp and a["fy"] == str(fy)
                        and ((pname(a["person"]) == k[0] and cname(a["concurrent_company"]) == k[1])
                             or (norm(r["원문행"]) and norm(r["원문행"]) in norm(a["source_text"])))]
                if not ours:
                    # 원문에서 다시: 같은 rcept md 에 그 행 글이 있는지
                    dd = docs.get(r["rcept_no"])
                    found = dd is not None and norm(r["원문행"]) and any(norm(r["원문행"]) in norm(l) for l in dd.L)
                    work["h5"].append(dict(corp=corp, fy=fy, rcept=r["rcept_no"], person=r["겸직자"],
                                           company=r["겸직회사"], title=r["겸직회사_직위"], found_in_md=bool(found),
                                           row=r["원문행"][:120]))

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
            cn += corr_notes
            snote = ""
            if st:
                snote = "직원 표 합계 행: 칸 순서 합계|기간의 정함이 없는 근로자 전체|(단시간)|기간제 근로자 전체|(단시간)|합계|평균근속|급여총액|1인평균 — 그 칸 원문 숫자"
            if st and st.get("foot"):
                snote += "; 직원 표 아래 각주: " + " / ".join("「%s」" % f for f in st["foot"])
            elif st:
                snote += "; 직원 표 아래 각주 없음"
            if not rb["hits"]:
                p13, p = page13(dm, dm.L[st["line"]]) if st else ("", None)
                B.append(dict(base(dm), keyword="없음", source_text=dm.L[st["line"]] if st else NONE,
                              page=(dm.loc(st["line"]) + p13) if st else "",
                              note="; ".join(x for x in [snote, "Ⅷ 전체(임원·직원 현황 표·각주·보수)에서 겸직·파견·출향·전출·전적·겸무 없음"] + cn if x),
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
                        nn.append("정정 %s: %s" % (dc.rcept, "같은 글" if any(norm(h["text"]) in norm(dc.L[x["line"]])
                                                                       for x in rc["hits"]) else "이 글 없음/바뀜"))
                    nn += corr_notes
                    if dm.fy == 2025 and dm.rcept == t13_rcept(corp) and not p:
                        nn.append("13차 본문 PDF 텍스트에서 같은 글 못 찾음")
                    B.append(dict(base(dm), keyword=h["kw"], source_text=h["text"], page=dm.loc(h["line"]) + p13,
                                  note="; ".join(x for x in nn if x), **nums))
                    add_sec("B", dm, h["line"])
                for dc, rc in corr_B:
                    for h in rc["hits"]:
                        if any(norm(h["text"]) == norm(x["text"]) for x in rb["hits"]):
                            continue
                        s2 = rc["staff"]
                        B.append(dict(base(dc), keyword=h["kw"], source_text=h["text"], page=dc.loc(h["line"]),
                                      employees_total=s2["total"] if s2 else "", regular=s2["regular"] if s2 else "",
                                      contract=s2["contract"] if s2 else "",
                                      note="; ".join(x for x in [
                                          "정정 %s: 본 보고서(%s)에 없는 글 — 정정판 글" % (dc.rcept, dm.rcept), snote,
                                          "직원 수 칸은 같은 정정판 직원 표 합계 행 값", "합계 행: 「%s」" % dc.L[s2["line"]] if s2 else ""] if x)))
                        add_sec("B", dc, h["line"])

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
                bnote = "(판단) 넓은 검색어(위탁·수탁·자문·전산·IT·공동)가 나온 %d줄은 계약·거래 뜻이 아닌 쓰임(매매주문 수탁·위탁자예수금·" \
                        "전산시스템 관련 제재·개인정보 수탁자·공동기업 등)이라 행으로 넣지 않음: %s" % (
                            len(broad), " / ".join(ex[:6]) + (" 외 %d줄" % (len(ex) - 6) if len(ex) > 6 else ""))
            tnote = tx_note(dm)          # 15차 검증 보탬: Ⅹ 장 계열사 거래 표의 거래 종류(브랜드사용료 등)
            if tnote:
                bnote = "; ".join(x for x in (bnote, tnote) if x)
            if not rd["rows"]:
                D.append(dict(base(dm), counterparty="", contract_type="", amount="", source_text=NONE,
                              page=range_page(dm, rd["rng"]) if rd["rng"] else "",
                              note="; ".join(x for x in [
                                  "찾은 범위: 「%s」~「%s」 절 전체(표·문단)" % (
                                      dm.head_of(rd["rng"][0])[2].strip() if rd["rng"] else "Ⅹ",
                                      "Ⅺ 끝" ),
                                  "검색어: 업무위탁·업무수탁·위수탁·위탁계약·수탁계약·용역·경영자문·자문계약·자문료·공동사용·공동이용·시스템 공동·전산 공동·IT 공동",
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
            sections.setdefault(("B", corp, "2026.2Q"), {}).update(mg["sec"])

    # FY2025 13차 쪽(A·B·D 의 page 에 이미 붙임)
    write_csv(os.path.join(OUT, "A_bs_g2.csv"), A, A_COLS)
    write_csv(os.path.join(OUT, "B_bs_g2.csv"), B, B_COLS)
    write_csv(os.path.join(OUT, "D_bs_g2.csv"), D, D_COLS)
    work["written"] = write_md(sections)
    work["counts"] = {t: count(rows) for t, rows in (("A", A), ("B", B), ("D", D))}
    json.dump(work, open(os.path.join(OUT, "bs_g2_work.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(work["counts"], ensure_ascii=False))
    print("probs", len(work["probs"]), "h5 missing", len(work["h5"]))


def range_page(d, rng):
    """「문서에 없음」 행의 page: 찾은 범위(절 번호·제목)."""
    secs = [(n, t.strip()) for i, n, t in d.heads if rng[0] <= i < rng[1]]
    if not secs:
        return ""
    return "XML [절 %d]~[절 %d] 「%s」~「%s」 전체(찾은 범위 — 해당 글 없음)" % (secs[0][0], secs[-1][0], secs[0][1], secs[-1][1])


TX_RE = re.compile(r"브랜드\s*사용료|수수료\s*수익|임대차|명칭\s*사용료|상표\s*사용료")


def tx_note(d):
    """Ⅹ 장(대주주 등과의 거래) 계열사 거래 표에 나온 거래 종류 낱말(요청 낱말 계약이 아닌 것) — note 에만 원문 낱말·위치."""
    rx = d.chap_range("X", ["XI", "XII"])
    if not rx:
        return ""
    found = []
    for i in range(rx[0], rx[1]):
        l = d.L[i]
        if not l.startswith("|"):
            continue
        for m in TX_RE.finditer(l):
            t = d.table_at(i)
            cellt = next((c.strip() for c in l.strip()[1:-1].split("|") if m.group(0) in c), m.group(0))
            if len(cell(cellt)) > 30:
                continue        # 표 아래 각주 칸(「주2) 당사의 영업수익은 … 수수료수익 등」)은 거래 종류 칸이 아님
            item = "「%s」[표 %s]" % (cell(cellt), t["no"] if t else "?")
            if item not in found:
                found.append(item)
    if not found:
        return ""
    return ("(판단) Ⅹ 장 계열사 거래 표의 거래 종류 칸 %s 은 요청 낱말(업무위탁·용역·경영자문·전산 공동사용) 계약이 아니라 행으로 넣지 않음"
            % "·".join(found))


def count(rows):
    c = {}
    for r in rows:
        k = r["corp_label"]
        c.setdefault(k, {"rows": 0, NONE: 0})
        c[k]["rows"] += 1
        if r.get("source_text") == NONE:
            c[k][NONE] += 1
    return c


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
        # 칸이 머리와 같은 수일 때만 칸 이름으로 집음(칸 합침 행은 note)
        if len(cells) == len(hdr):
            col = dict(zip(hdr, cells))
            CP = r"원고|피고|상대방|거래상대|계약상대|법인명|회사명"
            cps = [col[h] for h in hdr if re.search(CP, h)]
            cp = " / ".join(cell(v) for v in cps if cell(v) and cell(v) != "-")
            am = [col[h] for h in hdr if re.search(r"계약금액|거래금액|^금액", h)]
            amt = " / ".join(cell(v) for v in am if cell(v) and cell(v) != "-")
            sv = [(h, col[h]) for h in hdr if re.search(r"소송가", h)]
            if cp:
                note.append("(판단) counterparty 는 표의 「%s」 칸 원문(소송 표면 소송 당사자)" % "·".join(
                    h for h in hdr if re.search(CP, h)))
            else:
                note.append("표에 계약 상대방 칸 없음 — counterparty 빈칸")
            for h, v in sv:
                note.append("「%s」 칸 「%s」 — 계약 금액이 아니라 amount 빈칸" % (h, cell(v)))
        else:
            note.append("행 칸 수(%d)가 머리(%d)와 달라(칸 합침) 칸 이름으로 집지 않음 — counterparty·amount 빈칸" % (len(cells), len(hdr)))
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


def mg_range(P):
    """경영공시 「문서에 없음」 행의 page: 찾은 PDF 쪽 범위(15차 검증 보탬)."""
    ps = [p for p, ls, nt in P["pages"]]
    return "p.%d~p.%d 전체(찾은 범위, PDF 쪽 — 해당 글 없음)" % (min(ps), max(ps)) if ps else ""


def mgmt_rows(corp):
    """13차 경영공시 2026.2Q PDF 텍스트 — 작업 B 키워드 문장, 작업 D 업무위탁 현황."""
    meta = next((r for r in csv.DictReader(open(MGMT_CSV, encoding="utf-8-sig")) if r["corp_label"] == corp), None)
    P = t13_pages("경영공시", corp)
    head = P["head"]
    url = meta["url"] if meta else ""
    coll = kst(meta["fetched_at"]) if meta else ""
    name = "%s 경영공시 2026.2Q 「%s」 (13차 보관 PDF 텍스트)" % (corp, meta["제목"] if meta else "")
    b = dict(corp_label=corp, fy="2026.2Q", employees_total="", regular="", contract="", doc_kind="경영공시",
             rcept_no_or_url=url, doc_name=name, collected_at=coll)
    out = dict(B=[], D=[], sec={})
    hits = []
    for p, ls, nt in P["pages"]:
        for j, l in enumerate(ls):
            for k in KW:
                if k in l:
                    fr = KW_FALSE.get(k)
                    if fr and not re.sub(fr, "", l).count(k):
                        continue
                    hits.append((p, j, k, ls))
    pdfnote = "PDF 쪽 텍스트(pymupdf, 13차 보관 %s) — 문장이 PDF 줄에서 끊긴 곳은 줄바꿈만 붙여 씀" % (
        re.search(r"sha256 \S+", head).group(0) if re.search(r"sha256 \S+", head) else "")
    for p, j, k, ls in hits:
        # 문장: 앞 줄이 문장 끝(다./니다.)이 아니면 붙임, 뒤로 「다.」 까지
        a = j
        while a > 0 and not re.search(r"(다\.|\.)\s*$", ls[a - 1]) and not ls[a - 1].startswith("(") and j - a < 3:
            a -= 1
        if ls[a].lstrip().startswith("(") and a < j:
            a += 1
        z = j
        while z < len(ls) - 1 and not re.search(r"다\.\s*$", ls[z]) and z - j < 3:
            z += 1
        sent = "".join(ls[a:z + 1])
        out["B"].append(dict(b, keyword=k, source_text=sent, page="p.%d" % p,
                             note="직원 수 칸 빈칸(경영공시에서 키워드 문장만 모음); " + pdfnote))
        out["sec"][("mgmt", p)] = ("mgmt", corp, p, ls, url, name, coll)
    if not hits:
        out["B"].append(dict(b, keyword="없음", source_text=NONE, page=mg_range(P),
                             note="찾은 범위: 경영공시 2026.2Q PDF 텍스트 전 쪽(%d쪽), 검색어 겸직·파견·출향·전출·전적·겸무"
                                  "(「전적」은 완전적용 등 오탐 뺌) — 없음" % len(P["pages"])))
    dh = []
    for p, ls, nt in P["pages"]:
        for j, l in enumerate(ls):
            if D_RE.search(l) or "업무위탁" in norm(l):
                dh.append((p, j, l))
    if dh:
        for p, j, l in dh:
            out["D"].append(dict(corp_label=corp, fy="2026.2Q", counterparty="", contract_type=D_RE.search(l).group(0)
                                 if D_RE.search(l) else "업무위탁", amount="", source_text=l, doc_kind="경영공시",
                                 rcept_no_or_url=url, page="p.%d" % p, note=pdfnote, doc_name=name, collected_at=coll))
            out["sec"][("mgmt", p)] = ("mgmt", corp, p, P["pages"][[x[0] for x in P["pages"]].index(p)][1], url, name, coll)
    else:
        out["D"].append(dict(corp_label=corp, fy="2026.2Q", counterparty="", contract_type="", amount="", source_text=NONE,
                             doc_kind="경영공시", rcept_no_or_url=url, page=mg_range(P), doc_name=name, collected_at=coll,
                             note="찾은 범위: 경영공시 2026.2Q PDF 텍스트 전 쪽(%d쪽, 공백 무시), 검색어 업무위탁·위수탁·용역·경영자문·"
                                  "자문계약·공동사용·공동이용·전산 공동 — 「업무위탁」 현황 없음" % len(P["pages"])))
    return out


def write_md(sections):
    """원문 md 쓰기. 다시 돌릴 때는 지난번에 이 스크립트가 쓴 파일(bs_g2_work.json 의 written)만 지우고 다시 씀."""
    wj = os.path.join(OUT, "bs_g2_work.json")
    try:
        prev = json.load(open(wj, encoding="utf-8")).get("written", [])
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
                   "키워드 문장이 나온 PDF 쪽 글 전체를 그대로 옮김(13차 보관 PDF 텍스트, 「## p.N」= PDF 쪽).", ""]
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
