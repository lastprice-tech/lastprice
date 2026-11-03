#!/usr/bin/env python3
"""15차 g1 사업보고서(KB·신한·하나·우리금융지주, FY2019~FY2025) — 작업 A·B·D 조각.

입력(모두 로컬, 웹 요청 없음):
  dart_out/ops15/사업보고서_원문.csv (g1 행) → text_path 의 md(OpenDART XML 을 옮긴 글)
  handoff/겸직현황_정리.csv · handoff/임원_겸직_결합.csv (5차, 대조용)
  handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip (FY2025 본문 PDF 텍스트 · 경영공시 2026.2Q 텍스트)
  dart_out/risk8/경영공시_2026_2Q.csv (경영공시 받은 시각·URL)
출력:
  dart_out/ops15/조각/A_bs_g1.csv, B_bs_g1.csv, D_bs_g1.csv (utf-8-sig)
  dart_out/ops15/원문/{A,B,D}/<회사>__FY<fy>__사업보고서.md (행이 나온 절 전체), 원문/{B,D}/<회사>__2026.2Q__경영공시.md
  (진단) 표준출력 요약 — 다시 돌리면 같은 결과(입력이 같으면 바이트까지 같음).
사용: python3 scripts/dart/ops15_bs_g1.py
규칙: source_text 는 md 줄(표 행 「| … |」 또는 글 줄) 그대로. 해석·판단은 note(판단 표시 「(판단)」).
15차 검증 보정(scripts/dart/verify15_bs_g1.py, 2026-11-03): 경영공시 「문서에 없음」 page 채움, 겸직 사유를 Ⅷ·Ⅸ 밖 사람별 표 칸까지 찾음,
  묶인 겸직 행의 다른 글을 note 에 옮김, 같은 성명 다른 출생년월 note, D 「문서에 없음」 넓은 낱말 결과 note.
"""
from __future__ import annotations

import bisect
import csv
import os
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.path.join(ROOT, "dart_out", "ops15")
FRAG = os.path.join(WORK, "조각")
ORIG = os.path.join(WORK, "원문")
T13_ZIP = os.path.join(ROOT, "handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip")
MGMT_CSV = os.path.join(ROOT, "dart_out", "risk8", "경영공시_2026_2Q.csv")
H5_GJ = os.path.join(ROOT, "handoff", "겸직현황_정리.csv")
H5_JOIN = os.path.join(ROOT, "handoff", "임원_겸직_결합.csv")

COS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주"]
LABEL5 = {"KB금융": "KB금융지주", "신한지주": "신한금융지주", "하나금융지주": "하나금융지주", "우리금융지주": "우리금융지주"}
KST = timezone(timedelta(hours=9))
DOC_KIND = "사업보고서"

A_COLS = ["corp_label", "fy", "person", "birth_ym", "holdco_title", "holdco_duty", "registered", "fulltime",
          "concurrent_company", "concurrent_title", "concurrent_since", "reason_text", "doc_kind", "source_text",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
D_COLS = ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url",
          "page", "note", "doc_name", "collected_at"]

NONE = "문서에 없음"


# ================================================================ 글자 정규화(비교용 — 출력 글은 손대지 않음)
def nz(s):
    return re.sub(r"\s|&cr;|<br>", "", s or "")


def nzs(s):
    """글자 그대로 비교(공백·줄바꿈·「|」만 무시 — &cr;·<br> 은 글자로 셈). 「같은 행」 판정용."""
    return re.sub(r"[\s|]", "", s or "")


def name_key(s):
    t = nz(s)
    t = re.sub(r"\(?주\d\)|\(?주\d+\)|[*※]+", "", t)
    return t


def comp_key(s):
    t = nz(s)
    for x in ("(주)", "㈜", "주식회사", "(株)", "(유)"):
        t = t.replace(x, "")
    return t


def cells_of(line):
    if not (line.startswith("|") and line.endswith("|")):
        return None
    inner = line[2:-2] if len(line) >= 4 else ""
    return inner.split(" | ")


ROMAN_RE = re.compile(r"^(?:[IVX]+|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ])\.")


def level_of(title):
    if ROMAN_RE.match(title) or title.startswith("【"):
        return 1
    if re.match(r"^\d+(?:-\d+)?\.", title):
        return 2
    return 3


DATE_RE = re.compile(r"(20\d{2})(?:년|\.)(\d{1,2})(?:월|\.)(\d{1,2})")


def last_date(text):
    ds = [(int(a), int(b), int(c)) for a, b, c in DATE_RE.findall(nz(text))]
    ds = [d for d in ds if 1 <= d[1] <= 12 and 1 <= d[2] <= 31]
    return ds[-1] if ds else None


# ================================================================ 문서(md)
class Doc:
    def __init__(self, meta):
        self.meta = meta
        self.label, self.fy, self.kind = meta["label"], int(meta["fy"]), meta["kind"]
        self.rcept = meta["rcept_no"]
        with open(os.path.join(ROOT, meta["text_path"]), encoding="utf-8") as f:
            self.L = f.read().split("\n")
        self.heads = []          # (idx, n, title, level)  — 제목이 빈 절은 경계로 쓰지 않음
        self.tables = []         # dict(no, s, e, rows=[(idx, cells)])
        self.tab_of = {}         # 줄 → 표 번호
        cur = None
        for i, l in enumerate(self.L):
            m = re.match(r"### \[절 (\d+)\] ?(.*)$", l)
            if m and cur is None:
                t = m.group(2).strip()
                if t:
                    self.heads.append((i, int(m.group(1)), t, level_of(t)))
                continue
            m = re.fullmatch(r"\[표 (\d+)\]", l)
            if m:
                cur = dict(no=int(m.group(1)), s=i, e=None, rows=[])
                self.tables.append(cur)
                continue
            if l == "[표 끝]" and cur is not None:
                cur["e"] = i
                cur = None
                continue
            if cur is not None:
                self.tab_of[i] = cur["no"]
                c = cells_of(l)
                if c is not None:
                    cur["rows"].append((i, c))
        self.hidx = [h[0] for h in self.heads]
        self.tab_by_no = {t["no"]: t for t in self.tables}
        self.tab_end = {t["e"]: t for t in self.tables if t["e"] is not None}

    # --- 위치
    def head_at(self, i):
        k = bisect.bisect_right(self.hidx, i) - 1
        return self.heads[k] if k >= 0 else None

    def section_span(self, i):
        k = bisect.bisect_right(self.hidx, i) - 1
        h = self.heads[k]
        end = len(self.L)
        for j in range(k + 1, len(self.heads)):
            if self.heads[j][3] <= h[3]:
                end = self.heads[j][0]
                break
        return h[0], end

    def chapter(self, roman):
        """장(VIII 등) 범위 [시작, 끝)."""
        for k, h in enumerate(self.heads):
            if h[3] == 1 and re.match(r"^%s\." % roman, h[2]):
                end = len(self.L)
                for j in range(k + 1, len(self.heads)):
                    if self.heads[j][3] == 1:
                        end = self.heads[j][0]
                        break
                return h[0], end
        return None

    def page(self, i):
        h = self.head_at(i)
        p = "XML [절 %d] 「%s」" % (h[1], h[2]) if h else "XML"
        if i in self.tab_of:
            p += " [표 %d]" % self.tab_of[i]
        return p

    def table_caption(self, t, maxlines=6):
        """표 앞 글(제목·기준일) — 앞 표가 1행 「기준일/단위」 표면 그 글도. 각주(주1) 등)·긴 글에서 멈춤."""
        out, i = [], t["s"] - 1
        while i >= 0 and len(out) < maxlines:
            l = self.L[i]
            if l.startswith("### "):
                break
            if l == "[표 끝]":
                pt = self.tab_end.get(i)
                if pt and len(pt["rows"]) <= 1 and pt["rows"] and re.search(r"기준|단위", nz(self.L[pt["rows"][0][0]])):
                    out.append(self.L[pt["rows"][0][0]])
                    i = pt["s"] - 1
                    continue
                break
            st = l.strip()
            if st and not re.fullmatch(r"(&cr;)+", st):
                if re.match(r"^\s*\(?주\s?\d*\)", st) or len(st) > 150:
                    break
                out.append(l)
            i -= 1
        return list(reversed(out))


MARK_RE = re.compile(r"^\s*(?:\(?\d+\)?|[가-하]\.|[가-하]-\d\.|\*|■|◈|◆|-|※|\d+\.)")


def title_lines(cap):
    """캡션 가운데 표 제목 줄(기준일 줄 빼고, 표에 가까운 쪽부터 머리 표시가 나올 때까지)."""
    body = [x for x in cap if not x.startswith("|") and not re.fullmatch(r"\(?기준일?\s*:.*\)?", x.strip())]
    acc = []
    for x in reversed(body):
        acc.insert(0, x)
        if MARK_RE.match(x) and "현황" in nz("".join(acc)):
            break
        if len(acc) >= 4:
            break
    return acc


# ================================================================ 13차 PDF(쪽 찾기)
class PDFText:
    def __init__(self, text):
        self.pages = []                       # (n, [lines])
        cur = None
        for l in text.split("\n"):
            m = re.match(r"## p\.(\d+)", l)
            if m:
                cur = (int(m.group(1)), [])
                self.pages.append(cur)
            elif cur:
                cur[1].append(l)
        parts, self.starts, o = [], [], 0
        for n, ls in self.pages:
            self.starts.append(o)
            t = nz("".join(ls))
            parts.append(t)
            o += len(t)
        self.buf = "".join(parts)

    def page_at(self, pos):
        k = bisect.bisect_right(self.starts, pos) - 1
        return self.pages[k][0]

    def anchor(self, title):
        """본문의 장 제목(목차 아닌 것) — 줄 전체가 제목인 마지막 줄."""
        want = nz(title)
        hit = None
        for n, ls in self.pages:
            for l in ls:
                if nz(l) == want:
                    hit = n
        if hit is None:
            return 0
        k = [p[0] for p in self.pages].index(hit)
        return self.starts[k]

    def find(self, needle, start, window=60000):
        if not needle or len(needle) < 4:
            return -1
        return self.buf.find(needle, start, start + window + len(needle))


_T13 = {}


def t13_text(kind, co):
    key = (kind, co)
    if key not in _T13:
        z = zipfile.ZipFile(T13_ZIP)
        name = next((n for n in z.namelist() if n.endswith("텍스트/%s__%s.md" % (kind, co))), None)
        _T13[key] = (name, z.read(name).decode("utf-8")) if name else (None, None)
    return _T13[key]


# ================================================================ 입력
def kst_iso(s):
    if not s:
        return ""
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d.astimezone(KST).isoformat()


def load_reports():
    with open(os.path.join(WORK, "사업보고서_원문.csv"), encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["label"] in COS]
    rows.sort(key=lambda r: (COS.index(r["label"]), int(r["fy"]), r["kind"] != "본", r["rcept_no"]))
    return rows


def load_mgmt():
    out = {}
    with open(MGMT_CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["corp_label"] in COS and r["성공"] == "Y":
                out[r["corp_label"]] = r
    return out


# ================================================================ 작업 A — 표 찾기
GJ_COL = {"성명": "person", "대상계열사": "company", "대상회사": "company", "겸직회사": "company", "겸직회사명": "company",
          "직책": "title", "직위명": "title", "직위": "title",
          "선임시기": "since", "선임일": "since", "겸임일자": "since", "재임기간": "since",
          "비고": "remark", "상근여부": "remark", "상근/비상근여부": "remark",
          "직무": "duty2", "겸직회사의주된사업목적": "purpose", "지분보유현황": "stake"}
OFF_COL = {"성명": "name", "성별": "gender", "출생년월": "birth", "직위": "title", "직위(직책)": "title",
           "등기임원여부": "reg", "상근여부": "ft", "담당업무": "duty", "주요경력": "career"}


def is_gj_header(c):
    h = [nz(x) for x in c]
    return bool(h) and h[0] == "성명" and any(x in GJ_COL and GJ_COL[x] == "company" for x in h) and "출생년월" not in h


def is_off_header(c):
    h = [nz(x) for x in c]
    return len(h) >= 8 and h[0] == "성명" and "출생년월" in h and "담당업무" in h


def officer_tables(d):
    s, e = d.chapter("VIII")
    out = []
    for t in d.tables:
        if not (s <= t["s"] < e) or not t["rows"] or not is_off_header(t["rows"][0][1]):
            continue
        hdr = [nz(x) for x in t["rows"][0][1]]
        idx = {}
        for k, h in enumerate(hdr):
            if h in OFF_COL and OFF_COL[h] not in idx:
                idx[OFF_COL[h]] = k
        cap = d.table_caption(t)
        dt = last_date(" ".join(cap))
        after = (dt is not None and dt > (d.fy, 12, 31)) or ("이후" in " ".join(cap))
        offs = []
        for (i, c) in t["rows"][1:]:
            if len(c) < 8 or nz(c[0]) in ("성명", "의결권있는주식"):
                continue
            o = {k: (c[v] if v < len(c) else "") for k, v in idx.items()}
            o.update(line=i, table=t["no"], after=after, key=name_key(o.get("name", "")), cap=cap)
            if o["key"]:
                offs.append(o)
        out.append(dict(t=t, cap=cap, after=after, date=dt, offs=offs))
    return out


def gj_tables(d):
    """Ⅷ 시작 ~ Ⅹ 시작 사이의 겸직 표."""
    s = d.chapter("VIII")[0]
    e = d.chapter("X")[0]
    out = []
    for t in d.tables:
        if not (s <= t["s"] < e) or not t["rows"] or not is_gj_header(t["rows"][0][1]):
            continue
        hdr = [nz(x) for x in t["rows"][0][1]]
        cols = [GJ_COL.get(h, "x%d" % k) for k, h in enumerate(hdr)]
        cap = d.table_caption(t)
        capt = " ".join(cap)
        dt = last_date(capt)
        after = (dt is not None and dt > (d.fy, 12, 31)) or (dt is None and "이후" in capt)
        kind = "타회사" if "타회사" in nz("".join(title_lines(cap))) else "계열회사"
        recs, prev = [], None
        for (i, c) in t["rows"][1:]:
            if all(not x.strip() for x in c):
                continue
            carried = []
            if len(c) < len(cols) and prev is not None:
                k = len(cols) - len(c)
                full = prev[:k] + c
                carried = [cols[j] for j in range(k)]
            elif len(c) > len(cols):
                full = c[:len(cols)]
                carried = ["칸 수 넘침(%d>%d)" % (len(c), len(cols))]
            else:
                full = c
            prev = full
            r = {cols[j]: full[j] for j in range(len(cols))}
            r.update(line=i, table=t["no"], after=after, date=dt, kind=kind, cap=cap, carried=carried,
                     src=d.L[i], prev_line=(d.L[i - 1] if carried else ""))
            r["pkey"] = name_key(r.get("person", ""))
            r["ckey"] = comp_key(r.get("company", ""))
            r["tkey"] = nz(r.get("title", ""))
            recs.append(r)
        out.append(dict(t=t, cap=cap, after=after, date=dt, kind=kind, recs=recs, cols=cols))
    return out


def cap_short(cap):
    """겸직 표 제목 줄 + 기준일 줄 — 원문 줄을 「 / 」로 이음."""
    tl = title_lines(cap)
    dl = [x for x in cap if x not in tl and DATE_RE.search(nz(x))]
    return " / ".join(x.strip() for x in tl + dl[-1:] if x.strip())[:200]


# ---------------------------------------------------------------- 임원 현황 칸의 현재 겸직
SELF = {"KB금융지주": r"KB금융지주|KB금융그룹|케이비금융지주|KB<br>금융지주",
        "신한금융지주": r"신한금융지주|신한지주|신한금융그룹",
        "하나금융지주": r"하나금융지주|하나금융그룹",
        "우리금융지주": r"우리금융지주|우리금융그룹"}
BRAND = {"KB금융지주": r"KB|케이비|국민은행|국민카드|푸르덴셜생명",
         "신한금융지주": r"신한(?:은행|카드|금융투자|투자증권|생명|라이프|캐피탈|자산운용|BNP|DS|데이타시스템|아이타스|신용정보|에이아이|AI|대체투자|리츠|저축은행|벤처투자|자산신탁|펀드파트너스|EZ|프리미어|베트남|파이낸스)|제주은행|오렌지라이프|아시아신탁",
         "하나금융지주": r"하나(?:은행|증권|카드|캐피탈|생명|손해|저축|자산|대체|벤처|금융티아이|금융투자|에프앤아이|펀드|금융파인|금융F|UBS|대투|금융경영|금융연구|생명보험|손해보험)|핀크",
         "우리금융지주": r"우리(?:은행|카드|종합금융|자산|투자|\s?FIS|에프아이에스|신용정보|펀드서비스|프라이빗|PE|글로벌|금융캐피탈|금융저축|금융에프앤아이|벤처|금융경영연구소|금융F&I|금융FIS|금융연구소)|동양생명|ABL생명"}
SEP_RE = re.compile(r"ㅇ\s|(?<![A-Za-z])ㆍ|ㆍ(?![A-Za-z])|•|&cr;|<br>|\[경력\]|\[학력\]|\(약력\)|\(학력\)|(?:(?<=\s)|(?<=\))|^)-\s?(?=\S)"
                    r"|(?<!\()(?=現)|(?=\(겸\))|(?='\d{2}\.\s)")
GYEOM_SPLIT = re.compile(r"兼|\(겸\)|(?<!\()겸\)|(?<=\s)겸(?=\s)")
GYEOM_RE = re.compile(r"兼|\(겸\)|겸\)|(?<=\s)겸(?=\s)|겸직|겸무|겸임(?!교수)")
TITLE_RE = re.compile(r"대표이사|대표|부사장|사장|부회장|회장|은행장|행장|전무|상무|이사장|사외이사|기타비상무이사|비상임이사|사내이사|이사(?!회)|감사(?!위원)|CEO|부총경리|총경리")
EDU_RE = re.compile(r"학사|석사|박사|졸업|MBA|LL\.?M|대학원(?!장)|고등학교|(?:^|\s)\S+고$")


ORG_ANY = re.compile(r"학회|협회|재단|법인|회사|㈜|\(주\)|은행|증권|카드|생명|보험|캐피탈|운용|신탁|그룹|공사|공단|대학|연구소|연구원|거래소|위원회|학원|인베스트먼트|투자|상사|Ltd|LLC|LLP|Inc|Co\.")
ORG_SUF = re.compile(r"(은행|증권|카드|생명|보험|캐피탈|운용|신탁|회사|㈜|\(주\)|지주|금융|투자|인베스트먼트|공사|재단|협회|학회|법인|대학교|대학|연구소|연구원|센터|그룹|DS|FIS|신용정보|파트너스|유한공사|유한회사|Limited|Ltd\.?|Inc\.?|LLC|LLP/?|위원회|거래소|공단|\(유\)|학원|상사㈜|사무소,?)$")


def split_entries(text):
    """경력 칸을 조각으로(구분: ㅇ·ㆍ·&cr;·<br>·「- 」·現·(겸)·'YY.). 낱말 안 <br>(예: <br>KB<br>금융지주)은 먼저 붙임."""
    text = re.sub(r"(?<=[^\s>])<br>(?=[^\s<\-])", "", text)
    out, st = [], 0
    for m in SEP_RE.finditer(text):
        if m.start() > st:
            out.append(text[st:m.start()])
        st = max(st, m.end())
    out.append(text[st:])
    return [e.strip(" -") for e in out if e.strip(" -")]


def split_gyeom(ent, co):
    """兼·(겸)·「 겸 」 앞뒤로 나눔. 뒤 조각에 회사 꼴 낱말이 없으면(같은 곳 직함 겸임) 앞 조각에 다시 붙임."""
    out, st, mk = [], 0, False
    for m in GYEOM_SPLIT.finditer(ent):
        if m.start() > st:
            out.append([ent[st:m.start()], mk])
        st, mk = m.start(), True
    out.append([ent[st:], mk])
    res = []
    for part, mk in out:
        body = re.sub(r"^(兼|\(겸\)|겸\)|겸)\s*", "", part.strip())
        orgish = re.search(BRAND[co], body) or any(ORG_SUF.search(t) or t.startswith(("㈜", "(주)")) for t in body.split()[:-1])
        if res and mk and not orgish:
            res[-1][0] += part
        else:
            res.append([part, mk])
    return [(p, m) for p, m in res]


def is_current(e):
    if "현재" in e or "(현)" in e or "現)" in e:
        return True
    for m in re.finditer(r"現", e):
        if e[max(0, m.start() - 1):m.start()] == "(":      # 「(現 신한DS)」 = 이름 바뀜 표시
            continue
        return True
    return False


def split_company_title(part):
    """(판단) 「회사 직위」 나누기 — 회사 꼴 끝말(은행·증권·…)이 나오는 낱말까지를 회사로."""
    p = re.sub(r"^(現\)?|兼|\(겸\)|겸\)|겸)\s*", "", part.strip())
    p = re.sub(r"\s*[\(（][^()（）]*(?:현재|~|현\))[^()（）]*[\)）]\s*$", "", p)
    p = re.sub(r"\s*\(현\)\s*$", "", p).strip()
    toks = p.split()
    for k in range(len(toks) - 2, -1, -1):
        if ORG_SUF.search(toks[k]) or toks[k].startswith(("㈜", "(주)")):
            return " ".join(toks[:k + 1]), " ".join(toks[k + 1:])
    if len(toks) >= 2:
        return toks[0], " ".join(toks[1:])
    return p, ""


def since_of(part):
    m = re.search(r"[\(（]\s*([^()~]*?)\s*~\s*현재?\s*[\)）]", part)
    return m.group(1).strip() if m else ""


def cell_concurrents(co, off):
    """임원 현황 칸(담당업무·주요경력)의 현재 겸직 후보 — (칸이름, 조각, 기준)."""
    out = []
    for field in ("duty", "career"):
        text = off.get(field, "") or ""
        for ent in split_entries(text):
            if field == "career" and not is_current(ent):
                continue
            for part, marked in split_gyeom(ent, co):
                pt = part.strip()
                if not pt:
                    continue
                wo = re.sub(SELF[co], "", pt)
                brand = re.search(BRAND[co], wo)
                if re.search(SELF[co], pt) and not brand:
                    continue                        # 지주 자신
                if not brand:
                    if field == "duty":
                        continue
                    if EDU_RE.search(pt) and not TITLE_RE.search(pt):
                        continue
                    if "교수" in pt or (re.search(r"위원(?!장)", pt) and not TITLE_RE.search(pt)):
                        continue
                if brand:
                    why = "그룹사 이름"
                elif not ORG_ANY.search(re.sub(r"[\(（][^()（）]*[\)）]", "", pt)):
                    continue                        # 회사·기관 이름 꼴이 없는 조각(앞 조각의 이어짐 등)
                elif marked or GYEOM_RE.search(pt):
                    why = "겸 표시"
                elif TITLE_RE.search(pt):
                    why = "직함"
                else:
                    continue
                out.append((field, pt, why))
    return out


# ================================================================ 작업 B·D 검색어
TRUE_JEONJEOK = re.compile(r"(?<![가-힣])전적(?!으로|인|합)")
B_KWS = ["겸직", "파견", "출향", "전출", "전적", "겸무"]


def b_kws(t):
    out = []
    for k in B_KWS:
        if k == "전적":
            if TRUE_JEONJEOK.search(t):
                out.append(k)
        elif k in t:
            out.append(k)
    return out


D_RE = re.compile(r"업무\s?위\s?[·ㆍ]?\s?수탁|위\s?[·ㆍ]\s?수탁|위수탁|업무\s?위탁|업무\s?수탁|위탁\s?계약|수탁\s?계약"
                  r"|용역\s?(?:계약|거래|비|료|대가|제공|수수료)|용역을\s?제공|상품\s?용역|경영\s?자문|자문\s?(?:계약|용역|료|수수료|서비스)"
                  r"|공동\s?(?:사용|이용|활용)|시스템\s?공동|전산\s?공동|IT\s?공동")
D_TERMS = "업무위탁·업무수탁·위수탁·위ㆍ수탁·위탁계약·수탁계약·용역계약/거래/비/료/제공·상품용역·경영자문·자문계약/용역/료·공동사용/이용/활용·시스템 공동·전산 공동·IT 공동"
CT_RE = re.compile(r"계약|거래|약정|수수료|체결")


D_BROAD = re.compile(r"위탁|수탁|용역|자문|아웃소싱|외주|대행|공동")


def broad_d_note(d, s, e):
    """(15차 검증 보정) D 「문서에 없음」 행 — 같은 범위를 넓은 낱말로 다시 찾은 결과(줄마다 공백 무시). 행으로는 넣지 않음."""
    cnt, ex, info = {}, {}, None
    for i in range(s, e):
        t = re.sub(r"\s", "", d.L[i])
        for m in D_BROAD.finditer(t):
            w = m.group(0)
            cnt[w] = cnt.get(w, 0) + 1
            if w not in ex:
                ex[w] = "md %d행 「…%s…」" % (i + 1, t[max(0, m.start() - 15):m.end() + 15])
        m = re.search(r"(?:고객|개인|신용)\(?(?:신용)?\)?정보.{0,12}위탁|위탁업체", t)
        if m and info is None:
            info = "md %d행 「…%s…」" % (i + 1, t[max(0, m.start() - 10):m.end() + 25])
    if not cnt:
        return "넓은 낱말(위탁·수탁·용역·자문·아웃소싱·외주·대행·공동) 다시 찾기: 0곳"
    return ("넓은 낱말(위탁·수탁·용역·자문·아웃소싱·외주·대행·공동) 다시 찾기(공백 무시): %s — 낱말별 첫 곳 %s%s; "
            "(판단) 모두 D 검색어 꼴(업무위탁·위수탁·위탁계약·용역계약·경영자문·공동사용 등)이 아님. 고객·개인(신용)정보 처리 위탁 글은 "
            "KB·신한 보고서의 같은 꼴 글도 행으로 넣지 않았으므로 같은 기준으로 행에 넣지 않음"
            % (" ".join("%s %d" % kv for kv in sorted(cnt.items(), key=lambda x: -x[1])), " · ".join(ex.values()),
               (" · 정보 처리 위탁 글 " + info) if info else ""))


def contract_type(line, m):
    """(판단) 검색어가 든 낱말 덩어리(원문) — 왼쪽은 조사·어미 글자 앞까지(8자 안), 오른쪽은 조사·어미 글자 앞까지."""
    a = m.start()
    while a > 0 and m.start() - a < 8 and re.match(r"[가-힣A-Za-z0-9·ㆍ]", line[a - 1]) and line[a - 1] not in LSTOP:
        a -= 1
    b = m.end()
    while b < len(line) and re.match(r"[가-힣A-Za-z0-9·ㆍ]", line[b]) and line[b] not in RSTOP:
        b += 1
    w = line[a:b]
    if w.endswith("시") and len(w) > len(m.group(0)) and (b >= len(line) or not re.match(r"[가-힣]", line[b])):
        w = w[:-1]                                  # 「위탁시」의 「시」(때)
    return w


LSTOP = set("을를에의은는과와로가이하고도며")
RSTOP = set("을를에의은는과와로으가이하할한함며고")


def counterparties(text, m):
    """(판단) 「…는/은 <상대방>과/와 … 계약/거래」 꼴에서 상대방 글(원문). 여럿이면 「, 」·「 및 」로 나눔."""
    seg = text[:m.start()]
    mm = None
    for x in re.finditer(r"(?:는|은)\s+((?:(?!는\s|은\s).){1,80}?)(?:과|와)\s", seg):
        mm = x
    if not mm:
        return []
    cp = mm.group(1).strip()
    if len(cp) > 60 or re.search(r"[.。]\s", cp):
        return []
    parts = [p.strip() for p in re.split(r",\s*|\s및\s", cp) if p.strip()]
    if not all(CP_RE.search(p) for p in parts):
        return []
    return parts


CP_RE = re.compile(r"은행|증권|카드|생명|보험|캐피탈|자산운용|신탁|회사|㈜|\(주\)|Ltd|LLC|Inc|금융|공사|공단|라이프")


# ================================================================ md 글 단위(표 행은 한 줄, 글은 문단 이어 붙임)
def is_body(d, i):
    l = d.L[i]
    return bool(l.strip()) and not l.startswith("### ") and not re.fullmatch(r"\[표 \d+\]|\[표 끝\]", l)


def _is_text(d, j):
    return j not in d.tab_of and is_body(d, j) and not re.fullmatch(r"\s*(&cr;|<br>)*\s*", d.L[j])


def _ends(l):
    t = l.rstrip()
    return bool(re.search(r"(&cr;|<br>)$", t)) or bool(END_RE.search(t))


def _starts_new(l):
    return bool(BULLET_RE.match(l)) or bool(re.match(r"^\s*(\*|※|■|◈|◆|\(주\d*\)|주\d*\)|[가-하]-\d+\.)", l))


def _title(l):
    """머리 표시로 시작하는 짧은 줄(제목) — 앞뒤 글과 잇지 않음."""
    return _starts_new(l) and len(l.strip()) < 45


def unit_of(d, i, lo, hi, maxn=3):
    """표 행이면 그 줄. 글이면 앞뒤 줄을 문장 끝(다./&cr; 등)·머리 표시 전까지 이어 붙임(줄바꿈 그대로 — md 글 그대로)."""
    if i in d.tab_of:
        return d.L[i], i, i
    def step(j, k):
        """j 에서 k(±1) 쪽 다음 글 줄 — 빈 줄(공백만) 2개까지 건너뜀(이어 붙일 때 그 빈 줄도 그대로 넣음)."""
        for _ in range(3):
            j += k
            if j < lo or j >= hi or j in d.tab_of:
                return None
            if d.L[j].strip() == "" and d.L[j] != "":
                continue
            return j if _is_text(d, j) else None
        return None

    s = i
    for _ in range(maxn):
        p = step(s, -1)
        if p is None or _ends(d.L[p]) or _starts_new(d.L[s]) or _title(d.L[p]):
            break
        s = p
    e = i
    for _ in range(maxn):
        q = step(e, 1)
        if q is None or _ends(d.L[e]) or _starts_new(d.L[q]) or _title(d.L[e]):
            break
        e = q
    return "\n".join(d.L[s:e + 1]), s, e



# ================================================================ 본체
def build():
    reports = load_reports()
    docs = {}
    for r in reports:
        if r["text_path"]:
            docs[r["rcept_no"]] = Doc(r)
    by_fy = {}
    for r in reports:
        by_fy.setdefault((r["label"], int(r["fy"])), []).append(r)
    mg = load_mgmt()

    A_rows, B_rows, D_rows = [], [], []
    sections = {}       # (task, co, fykey, docfile) -> {rcept: set(section start idx)}
    pdf_jobs = {}       # rcept -> list of (line_idx, needle_nz, row)
    probs, judg = [], set()

    def base(d):
        return dict(corp_label=d.label, fy=str(d.fy), doc_kind=DOC_KIND, rcept_no_or_url=d.rcept,
                    doc_name=d.meta["report_nm"], collected_at=d.meta["fetched_at"])

    def add_sec(task, d, i, row):
        row.setdefault("_secs", []).append((task, d, i))

    def want_pdf(d, i, needle, row):
        row["_pdf"] = (d, i, needle)

    def register(rows):
        """조각에 실제로 들어간 행만 절·쪽 찾기에 올림."""
        for row in rows:
            for (task, d, i) in row.get("_secs", []):
                s, e = d.section_span(i)
                sections.setdefault((task, d.label, d.fy), {}).setdefault(d.rcept, set()).add(s)
            if row.get("_pdf"):
                d, i, needle = row["_pdf"]
                if d.fy == 2025 and d.kind == "본":
                    pdf_jobs.setdefault(d.rcept, []).append((i, needle, row))

    # ------------------------------------------------------------ A
    def a_extract(d):
        """문서 하나의 겸직 기록(중복 묶음 전) + 임원 표."""
        offt = officer_tables(d)
        gjt = gj_tables(d)
        return offt, gjt

    def match_officer(offt, pkey, after):
        pref = [o for t in offt for o in t["offs"] if o["key"] == pkey and o["after"] == after]
        other = [o for t in offt for o in t["offs"] if o["key"] == pkey and o["after"] != after]
        cands = pref or other
        births = sorted(set(nz(o.get("birth", "")) for o in cands))
        if not cands:
            return None, "임원 현황 표에 같은 성명 없음 — holdco·출생 칸 비움"
        if len(births) > 1:
            return None, "(판단) 동명이인 가능 — 임원 현황 표 같은 성명 출생년월 %s, 맞출 수 없어 비움" % "·".join(births)
        o = cands[0]
        how = "임원 현황 [표 %d] 성명으로 맞춤(출생 %s)" % (o["table"], o.get("birth", ""))
        if not pref:
            how += "; " + ("작성기준일 이후 임원 표" if o["after"] else "기준일 임원 표") + "에서 찾음"
        return o, how

    def gj_groups(gjt):
        """(사람, 회사, 직위) 같은 행 묶기 — 기준일 표가 먼저."""
        groups, order = {}, []
        for g in sorted(gjt, key=lambda g: (g["after"], g["t"]["s"])):
            for r in g["recs"]:
                k = (r["after"], r["kind"], r["pkey"], r["ckey"], r["tkey"])
                if k not in groups:
                    groups[k] = [r]
                    order.append(k)
                else:
                    groups[k].append(r)
        return groups, order

    a_fy_rows = {}
    a_records = {}    # rcept -> (offt, gjt)
    for d in docs.values():
        a_records[d.rcept] = a_extract(d)

    def a_rows_for(d, extra_note="", only=None):
        offt, gjt = a_records[d.rcept]
        groups, order = gj_groups(gjt)
        rows = []
        endkeys = {(k[1], k[2], k[3], k[4]) for k in order if not k[0]}
        aftkeys = {(k[1], k[2], k[3], k[4]) for k in order if k[0]}
        has_after = {g["kind"] for g in gjt if g["after"]}
        for k in order:
            if only is not None and k not in only:
                continue
            rs = groups[k]
            r = rs[0]
            after, kind = k[0], k[1]
            if after and (kind, k[2], k[3], k[4]) in endkeys:
                continue            # 기준일 표 행에 붙임(아래 note)
            o, how = match_officer(offt, r["pkey"], after)
            notes = []
            notes.append("겸직 표 「%s」" % cap_short(r["cap"]))
            if after:
                notes.append("작성기준일 이후 표에만 있는 행")
            if r.get("remark"):
                notes.append("겸직 표 「%s」 칸: %s" % ("비고/상근여부", r["remark"]))
            for f, nm in (("duty2", "직무"), ("purpose", "겸직회사의 주된 사업목적"), ("stake", "지분보유현황")):
                if r.get(f):
                    notes.append("겸직 표 「%s」: %s" % (nm, r[f]))
            if r["carried"]:
                notes.append("(판단) 병합 칸 — %s 은(는) 윗줄 값(윗줄: %s)" % (
                    "·".join({"person": "성명", "company": "회사"}.get(x, x) for x in r["carried"]), r["prev_line"][:120]))
                judg.add("겸직 표 병합 칸(칸 수가 머리행보다 적은 행)은 앞 칸을 윗줄 값으로 채움(오른쪽 맞춤)")
            dup = ["[표 %d](%s)" % (x["table"], d.page(x["line"]).split(" [표")[0]) for x in rs[1:] if nzs(x["src"]) == nzs(r["src"])]
            if dup:
                notes.append("같은 행이 %s 에도" % ", ".join(dup))
            # (15차 검증 보정) 사람·회사·직위는 같고 글(선임일·병합 칸 등)이 다른 행은 그 글을 note 에 옮김
            dup2 = ["[표 %d](%s) 「%s」" % (x["table"], d.page(x["line"]).split(" [표")[0], x["src"]) for x in rs[1:] if nzs(x["src"]) != nzs(r["src"])]
            if dup2:
                notes.append("같은 사람·회사·직위 행(글 다름)이 %s 에도" % ", ".join(dup2))
            if not after:
                ak = (kind, k[2], k[3], k[4])
                same_after = [x for kk in order if kk[0] and (kk[1], kk[2], kk[3], kk[4]) == ak for x in groups[kk]]
                if same_after:
                    notes.append("작성기준일 이후 표(%s)에도 같은 행" % ", ".join(
                        "[표 %d]" % x["table"] + ("" if nzs(x["src"]) == nzs(r["src"]) else "(글 다름: 「%s」)" % x["src"])
                        for x in same_after))
                elif kind in has_after:
                    notes.append("작성기준일 이후 표에는 이 행 없음")
            notes.append(how)
            notes.append("겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음")
            if extra_note:
                notes.append(extra_note)
            row = base(d)
            row.update(person=r.get("person", ""), birth_ym=(o or {}).get("birth", ""),
                       holdco_title=(o or {}).get("title", ""), holdco_duty=(o or {}).get("duty", ""),
                       registered=(o or {}).get("reg", ""), fulltime=(o or {}).get("ft", ""),
                       concurrent_company=r.get("company", ""), concurrent_title=r.get("title", ""),
                       concurrent_since=r.get("since", ""), reason_text=NONE, source_text=r["src"],
                       page=d.page(r["line"]), note="; ".join(notes))
            row["_line"] = r["line"]
            row["_key"] = ("gj",) + k
            rows.append(row)
            add_sec("A", d, r["line"], row)
            for x in rs[1:]:
                add_sec("A", d, x["line"], row)
            want_pdf(d, r["line"], nz("".join(cells_of(r["src"]) or [r["src"]]))[:40], row)
        # 임원 현황 칸
        allgj = [r for g in gjt for r in g["recs"]]
        seen = set()
        for t in sorted(offt, key=lambda t: (t["after"], t["t"]["s"])):
            for o in t["offs"]:
                for field, part, why in cell_concurrents(d.label, o):
                    pk = (o["key"], nz(part))
                    if pk in seen:
                        continue
                    seen.add(pk)
                    np_ = comp_key(part)
                    covered = [g for g in allgj if g["pkey"] == o["key"] and g["ckey"] and
                               (g["ckey"] in np_ or re.sub(r"^(KB|신한|하나|우리)", "", g["ckey"]) in np_
                                or g["ckey"][:5] in np_)]      # (판단) 앞 5글자 같으면 같은 곳(표기 차이: DAHOE/DAOHE 등)
                    if covered:
                        continue
                    key = ("cell", o["key"], nz(part))
                    if only is not None and key not in only:
                        continue
                    comp, title = split_company_title(part)
                    notes = ["임원 현황 칸에서 — 겸직 표에 없음",
                             "칸 「%s」 조각: %s" % ({"duty": "담당업무", "career": "주요경력"}[field], part),
                             "(판단) 현재 겸직으로 본 기준: %s%s" % (why, "" if field == "duty" else " + 현직 표시(현재·(현)·現)"),
                             "(판단) 회사·직위는 조각을 끝말(은행·증권·회사 등) 기준으로 나눔",
                             "임원 현황 [표 %d]%s" % (o["table"], " (작성기준일 이후 표)" if o["after"] else ""),
                             "겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음"]
                    judg.add("임원 현황 칸 겸직: 주요경력의 현직 조각(현재·(현)·現) 중 그룹사 이름·겸 표시·직함(이사·대표·사장·은행장 등)이 있는 것, 담당업무는 그룹사 이름이 있는 것만; 지주 자신·학력·교수·위원 조각은 뺌; 같은 사람 겸직 표 행과 회사 이름이 겹치면 뺌")
                    if extra_note:
                        notes.append(extra_note)
                    row = base(d)
                    row.update(person=o.get("name", ""), birth_ym=o.get("birth", ""), holdco_title=o.get("title", ""),
                               holdco_duty=o.get("duty", ""), registered=o.get("reg", ""), fulltime=o.get("ft", ""),
                               concurrent_company=comp, concurrent_title=title, concurrent_since=since_of(part),
                               reason_text=NONE, source_text=d.L[o["line"]], page=d.page(o["line"]),
                               note="; ".join(notes))
                    row["_line"] = o["line"]
                    row["_key"] = key
                    rows.append(row)
                    add_sec("A", d, o["line"], row)
                    want_pdf(d, o["line"], nz("".join((cells_of(d.L[o["line"]]) or [""])[:3])), row)
        return rows

    # ------------------------------------------------------------ B
    def b_scan(d):
        s, e = d.chapter("VIII")
        emp = None
        for t in d.tables:
            if s <= t["s"] < e and t["rows"] and nz(t["rows"][0][1][0]) == "직원" and "소속외" in nz(" ".join(t["rows"][0][1])):
                for (i, c) in t["rows"]:
                    if nz(c[0]) == "합계":
                        emp = dict(line=i, cells=c, table=t["no"])
                        break
                if emp:
                    break
        hits, seen = [], set()
        for i in range(s, e):
            if not is_body(d, i):
                continue
            for k in b_kws(d.L[i]):
                txt, a0, b0 = unit_of(d, i, s, e)
                if (k, a0, b0) in seen:
                    continue
                seen.add((k, a0, b0))
                hits.append(dict(i=i, k=k, s=a0, e=b0, text=txt))
        return emp, hits

    def b_rows_for(d, emp, hits, extra_note="", only=None):
        rows = []
        tot = reg = con = ""
        empnote = ""
        if emp:
            c = emp["cells"]
            reg, con, tot = (c[1] if len(c) > 1 else ""), (c[3] if len(c) > 3 else ""), (c[5] if len(c) > 5 else "")
            empnote = "직원 수: [표 %d] 합계 행 「%s」 — (판단) 칸 차례 합계|기간의정함없음 전체|(단시간)|기간제 전체|(단시간)|합계" % (emp["table"], d.L[emp["line"]])
            judg.add("직원 수: 직원 등 현황 표 합계 행의 2·4·6번째 칸 = 기간의 정함이 없는 근로자 전체·기간제 근로자 전체·합계(머리행 차례)")
        else:
            tot = reg = con = NONE
            empnote = "직원 등 현황 표 합계 행을 Ⅷ에서 찾지 못함"
        if only is None and not hits:
            row = base(d)
            row.update(employees_total=tot, regular=reg, contract=con, keyword="없음",
                       source_text=d.L[emp["line"]] if emp else NONE, page=d.page(emp["line"]) if emp else "",
                       note="; ".join(x for x in ["Ⅷ 전체(직원 현황 표·각주·미등기임원 보수 포함)에서 겸직·파견·출향·전출·전적·겸무 없음",
                                                   empnote, extra_note] if x))
            row["_line"] = emp["line"] if emp else 0
            row["_key"] = ("emp",)
            rows.append(row)
            if emp:
                add_sec("B", d, emp["line"], row)
                want_pdf(d, emp["line"], nz("".join(emp["cells"]))[:40], row)
            return rows
        for h in hits:
            i, k = h["i"], h["k"]
            key = ("kw", k, nz(h["text"]))
            if only is not None and key not in only:
                continue
            row = base(d)
            where = "표 행" if i in d.tab_of else ("글 줄" if h["s"] == h["e"] else "글(md 줄 %d개 — 문단 이어 붙임, 줄바꿈 그대로)" % (h["e"] - h["s"] + 1))
            row.update(employees_total=tot, regular=reg, contract=con, keyword=k, source_text=h["text"], page=d.page(i),
                       note="; ".join(x for x in ["Ⅷ %s" % where, empnote, extra_note] if x))
            row["_line"] = i
            row["_key"] = key
            rows.append(row)
            add_sec("B", d, i, row)
            if emp:
                add_sec("B", d, emp["line"], row)
            c = cells_of(h["text"]) if h["s"] == h["e"] else None
            want_pdf(d, h["s"], nz("".join(c) if c else h["text"])[:40], row)
        return rows

    # ------------------------------------------------------------ D
    def d_scan(d):
        x = d.chapter("X")
        xi = d.chapter("XI")
        s = x[0]
        e = xi[1] if xi else x[1]
        hits, seen = [], set()
        for i in range(s, e):
            if not is_body(d, i) or not D_RE.search(d.L[i]):
                continue
            txt, a0, b0 = unit_of(d, i, s, e)
            if (a0, b0) in seen:
                continue
            seen.add((a0, b0))
            hits.append(dict(i=i, s=a0, e=b0, text=txt, ms=list(D_RE.finditer(txt))))
        heads = [h for h in d.heads if s <= h[0] < e and h[3] <= 2]
        return hits, heads, (s, e)

    def table_header(d, i):
        tno = d.tab_of.get(i)
        if not tno:
            return None
        t = d.tab_by_no[tno]
        return t["rows"][0][1] if t["rows"] else None

    def d_rows_for(d, hits, heads, extra_note="", only=None):
        rows, seen = [], {}
        x0, x1 = d.chapter("X")
        for h in hits:
            i, l, ms = h["i"], h["text"], h["ms"]
            types = []
            for m in ms:
                t = contract_type(l, m)
                if t not in types:
                    types.append(t)
            m = ms[0]
            ctype = types[0]
            cps, amount, an, cp_from_table = [], "", "", False
            hdr = table_header(d, i) if i in d.tab_of else None
            c = cells_of(l)
            if hdr and c and len(hdr) == len(c) and nz(" ".join(hdr)) != nz(" ".join(c)):
                for hk, hv in zip(hdr, c):
                    hh = nz(hk)
                    if re.search(r"상대방|거래처|계약처", hh):
                        cps, cp_from_table = [hv], True
                    if re.search(r"금액|가액|수수료", hh) and not amount:
                        amount, an = hv, "amount 는 표 「%s」 칸" % hk
            if not cps and i not in d.tab_of:
                cps = counterparties(l, m)
            cps = cps or [""]
            for cp in cps:
                key = (nz(cp), nz(ctype))
                if key in seen:
                    seen[key]["_more"].append(h["s"])
                    continue
                if only is not None and ("d", nz(l), key) not in only:
                    continue
                hd = d.head_at(i)
                row = base(d)
                where = "표 행" if i in d.tab_of else ("글 줄" if h["s"] == h["e"] else "글(md 줄 %d개 — 문단 이어 붙임, 줄바꿈 그대로)" % (h["e"] - h["s"] + 1))
                notes = ["%s 「%s」 %s" % ("Ⅹ" if x0 <= i < x1 else "Ⅺ", hd[2], where),
                         "검색어 「%s」" % "·".join(dict.fromkeys(mm.group(0) for mm in ms))]
                if len(types) > 1:
                    notes.append("같은 글의 다른 검색어 낱말: %s" % "·".join(types[1:]))
                if not CT_RE.search(l):
                    notes.append("같은 글에 계약·거래·약정·수수료·체결 낱말 없음")
                notes.append("(판단) contract_type 은 검색어가 든 낱말 덩어리(앞뒤 조사·어미 뗌)")
                if cp and not cp_from_table:
                    notes.append("(판단) counterparty 는 문장 「…는 <상대방>과/와 …」 꼴에서 옮김" + (" — 한 문장의 상대방 여럿을 나눔" if len(cps) > 1 else ""))
                if an:
                    notes.append(an)
                if extra_note:
                    notes.append(extra_note)
                row.update(counterparty=cp, contract_type=ctype, amount=amount, source_text=l, page=d.page(i))
                row["_notes"] = notes
                row["_more"] = []
                row["_line"] = i
                row["_s"] = h["s"]
                row["_key"] = ("d", nz(l), key)
                seen[key] = row
                rows.append(row)
                add_sec("D", d, i, row)
                cc = cells_of(l) if h["s"] == h["e"] else None
                want_pdf(d, h["s"], nz("".join(cc) if cc else l)[:40], row)
        for row in rows:
            more = sorted(set(x for x in row["_more"] if x != row["_s"]))
            if more:
                row["_notes"].append("같은 상대방·유형 언급 글 %d개 더: %s" % (len(more), ", ".join(d.page(x).replace("XML ", "") for x in more[:8]) + (" …" if len(more) > 8 else "")))
                for x in more:
                    add_sec("D", d, x, row)
            row["note"] = "; ".join(row.pop("_notes"))
            row.pop("_more")
        return rows

    # ------------------------------------------------------------ 회사·연도별
    h5 = load_h5()
    h5_report = []
    for co in COS:
        for fy in range(2019, 2026):
            lst = by_fy.get((co, fy), [])
            mains = [r for r in lst if r["kind"] == "본"]
            if not mains:
                probs.append("%s FY%d 본 사업보고서 없음" % (co, fy))
                continue
            dm = docs.get(mains[0]["rcept_no"])
            if dm is None:
                probs.append("%s FY%d 본 %s md 없음" % (co, fy, mains[0]["rcept_no"]))
                continue
            corrs = [r for r in lst if r["kind"] == "정정"]
            # ---------- A
            a_main = a_rows_for(dm)
            a_extra = []
            cnotes = []
            for cr in corrs:
                if not cr["text_path"]:
                    msg = "정정 %s(%s): OpenDART 원문 없음(status %s %s) — 비교 못함" % (
                        cr["rcept_no"], cr["report_nm"], cr["doc_status"], cr["doc_message"])
                    cnotes.append(msg)
                    probs.append("%s FY%d %s" % (co, fy, msg))
                    continue
                dc = docs[cr["rcept_no"]]
                a_c = a_rows_for(dc)
                km = {r["_key"]: r for r in a_main}
                kc = {r["_key"]: r for r in a_c}
                newk = [k for k in kc if k not in km]
                gone = [k for k in km if k not in kc]
                om = {nz(dm.L[o["line"]]) for t in a_records[dm.rcept][0] for o in t["offs"]}
                oc = {nz(dc.L[o["line"]]) for t in a_records[dc.rcept][0] for o in t["offs"]}
                if om != oc:
                    chg = {}
                    for t in a_records[dm.rcept][0] + a_records[dc.rcept][0]:
                        for o in t["offs"]:
                            dd = dm if t in a_records[dm.rcept][0] else dc
                            if nz(dd.L[o["line"]]) in (om ^ oc):
                                chg[o["key"]] = "%s(%s)" % (o.get("name", ""), o.get("birth", ""))
                    cnotes.append("정정 %s: 임원 현황 표 행 글자 다름 — %s (본에만 %d·정정판에만 %d행)" % (
                        cr["rcept_no"], ", ".join(sorted(chg.values())), len(om - oc), len(oc - om)))
                if not newk and not gone:
                    cnotes.append("정정 %s: 겸직 행(겸직 표·임원 현황 칸) 같음" % cr["rcept_no"])
                else:
                    cnotes.append("정정 %s: 정정판에 새로 생긴/바뀐 행 %d, 정정판에 없는 행 %d" % (cr["rcept_no"], len(newk), len(gone)))
                    for k in gone:
                        km[k]["note"] += "; 정정 %s: 이 행이 정정판에 없음(바뀌었거나 빠짐)" % cr["rcept_no"]
                    for k in newk:
                        r = kc[k]
                        r["note"] = "정정 %s: 본(%s)에 없는 행 — 정정판 글; " % (cr["rcept_no"], dm.rcept) + r["note"]
                        a_extra.append(r)
            for r in a_main:
                if cnotes:
                    r["note"] += "; " + "; ".join(cnotes)
            rows = a_main + a_extra
            if not rows:
                row = base(dm)
                s8, _ = dm.chapter("VIII")
                row.update(person="", birth_ym="", holdco_title="", holdco_duty="", registered="", fulltime="",
                           concurrent_company="", concurrent_title="", concurrent_since="", reason_text=NONE,
                           source_text=NONE, page="XML Ⅷ·Ⅸ",
                           note="Ⅷ 임원 현황·Ⅷ/Ⅸ 겸직 표(계열회사간·타회사, 작성기준일 이후 포함)에 겸직 행 없음")
                row["_line"] = s8
                row["_key"] = ("none",)
                rows = [row]
            a_fy_rows[(co, fy)] = rows
            register(rows)
            A_rows.extend(rows)
            # 5차 대조
            h5_report.extend(compare_h5(co, fy, h5, a_records, docs, by_fy, rows))
            # ---------- B
            emp, hits = b_scan(dm)
            b_main = b_rows_for(dm, emp, hits)
            b_extra, bnotes = [], []
            for cr in corrs:
                if not cr["text_path"]:
                    bnotes.append("정정 %s: OpenDART 원문 없음 — 비교 못함" % cr["rcept_no"])
                    continue
                dc = docs[cr["rcept_no"]]
                emp_c, hits_c = b_scan(dc)
                diffs = []
                if (emp and emp_c and dm.L[emp["line"]] != dc.L[emp_c["line"]]) or (bool(emp) != bool(emp_c)):
                    diffs.append("합계 행이 「%s」 로 바뀜" % (dc.L[emp_c["line"]] if emp_c else "없음"))
                km = {("kw", h["k"], nz(h["text"])) for h in hits}
                kc = {("kw", h["k"], nz(h["text"])) for h in hits_c}
                newk = kc - km
                gone = km - kc
                same_wrap = {k for k in newk if any(g[1] == k[1] and (g[2] in k[2] or k[2] in g[2]) for g in gone)}
                if same_wrap:
                    diffs.append("키워드 글 %d개는 글자 같고 줄 나눔·이어 붙인 범위만 다름(행 추가 안 함)" % len(same_wrap))
                    gone = {g for g in gone if not any(g[1] == k[1] and (g[2] in k[2] or k[2] in g[2]) for k in same_wrap)}
                    newk = newk - same_wrap
                if newk:
                    diffs.append("키워드 줄 %d개 새로(정정판 글로 행 추가)" % len(newk))
                    b_extra.extend(b_rows_for(dc, emp_c, hits_c, extra_note="정정 %s: 본(%s)에 없는 키워드 줄" % (cr["rcept_no"], dm.rcept), only=newk))
                if gone:
                    diffs.append("본의 키워드 줄 %d개가 정정판에 없음" % len(gone))
                bnotes.append("정정 %s: %s" % (cr["rcept_no"], "; ".join(diffs) if diffs else "직원 표·Ⅷ 키워드 줄 같음"))
            for r in b_main:
                if bnotes:
                    r["note"] += "; " + "; ".join(bnotes)
            register(b_main + b_extra)
            B_rows.extend(b_main + b_extra)
            # ---------- D
            dh, heads, (ds, de) = d_scan(dm)
            d_main = d_rows_for(dm, dh, heads)
            d_extra, dnotes = [], []
            for cr in corrs:
                if not cr["text_path"]:
                    dnotes.append("정정 %s: OpenDART 원문 없음 — 비교 못함" % cr["rcept_no"])
                    continue
                dc = docs[cr["rcept_no"]]
                dh_c, heads_c, _ = d_scan(dc)
                lm = {nz(h["text"]) for h in dh}
                lc = {nz(h["text"]) for h in dh_c}
                newl = lc - lm
                gone = lm - lc
                if newl:
                    rows_c = d_rows_for(dc, [h for h in dh_c if nz(h["text"]) in newl], heads_c,
                                        extra_note="정정 %s: 본(%s)에 없는 줄 — 정정판 글" % (cr["rcept_no"], dm.rcept))
                    d_extra.extend(rows_c)
                dnotes.append("정정 %s: %s" % (cr["rcept_no"], "Ⅹ·Ⅺ 검색어 줄 같음" if not newl and not gone else
                                                  "새 줄 %d · 정정판에 없는 본 줄 %d" % (len(newl), len(gone))))
            if not d_main:
                row = base(dm)
                xs = [h for h in dm.heads if ds <= h[0] < de and h[3] == 1]
                row.update(counterparty="", contract_type="", amount="", source_text=NONE,
                           page="XML " + " · ".join("[절 %d] 「%s」" % (h[1], h[2]) for h in xs),
                           note="찾은 범위: %s 전체(표·글) · 검색어: %s · 없음" % (" ~ ".join(h[2] for h in xs), D_TERMS)
                           + "; " + broad_d_note(dm, ds, de))
                row["_line"] = ds
                row["_key"] = ("none",)
                d_main = [row]
            for r in d_main:
                if dnotes:
                    r["note"] += "; " + "; ".join(dnotes)
            register(d_main + d_extra)
            D_rows.extend(d_main + d_extra)

    # ------------------------------------------------------------ (15차 검증 보정) 겸직 사유 — Ⅷ·Ⅸ 밖까지 넓혀 찾기
    # ① 사람별 표 칸: 표 행 첫 칸이 성명이고, 다른 칸에 「겸직/겸임」과 사유 표현이 함께 있음(예: 이사 현황 「선임 배경」 칸)
    #    → 같은 보고서·같은 성명·그 칸에 겸직 회사 이름이 나오는 A 행의 reason_text 로 옮김(칸 글 그대로)
    # ② 사람 없는 글 줄: 「위해/위하여 … 겸직」 — reason_text 에 넣지 않고 그 보고서 A 행 note 에만 적음
    RSN = re.compile(r"겸(?:직|임)[^|]{0,60}?(?:고려|위하여|위해|위한|목적|사유|이유|배경|가능할 것으로|필요)"
                     r"|(?:고려하여|위하여|위해|목적|사유|이유)[^|]{0,60}?겸(?:직|임)")
    GEN_RSN = re.compile(r"(?:위해|위하여)[^.|]{0,40}?겸직")
    r_cells, r_lines = {}, {}

    def person_key(c0):
        return re.sub(r"\(\W*\)|[^가-힣]", "", nz(c0))

    for rc, d in docs.items():
        cs, gl = [], []
        r8, r9 = d.chapter("VIII"), d.chapter("IX")
        for t in d.tables:
            hdr = t["rows"][0][1] if t["rows"] else []
            for (i, c) in t["rows"][1:]:
                if not c or not re.fullmatch(r"[가-힣]{2,4}", person_key(c[0])):
                    continue
                for ci, cell in enumerate(c[1:], 1):
                    if len(nz(cell)) > 20 and RSN.search(cell) and not re.search(r"겸직하고\s?있지\s?않|겸직\s?제한", cell):
                        cs.append((person_key(c[0]), cell, i, t["no"], hdr[ci] if len(hdr) == len(c) else ""))
        for i, l in enumerate(d.L):
            if i in d.tab_of or any(r and r[0] <= i < r[1] for r in (r8, r9)):
                continue
            m = GEN_RSN.search(l)
            if m:
                # 그 글 줄에서 맞은 곳이 든 문장만(앞 「다.」·&cr; 다음 ~ 뒤 「다.」까지) — 글자 그대로
                a = max(l.rfind("다.", 0, m.start()) + 2 if l.rfind("다.", 0, m.start()) >= 0 else 0,
                        l.rfind("&cr;", 0, m.start()) + 4 if l.rfind("&cr;", 0, m.start()) >= 0 else 0)
                b = l.find("다.", m.end())
                gl.append((i, l[a:(b + 2 if b >= 0 else len(l))].strip()))
        r_cells[rc], r_lines[rc] = cs, gl
    for r in A_rows:
        d = docs.get(r["rcept_no_or_url"])
        if not d or r["reason_text"] != NONE:
            continue
        hit = [x for x in r_cells[d.rcept] if x[0] == person_key(r["person"]) and nz(r["concurrent_company"])
               and nz(r["concurrent_company"]) in nz(x[1])]
        if hit:
            pk, cell, i, tno, hn = hit[0]
            r["reason_text"] = cell
            r["note"] = r["note"].replace("겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음",
                                          "reason_text: 같은 보고서 %s 「%s」 칸(성명 「%s」 행) — (판단) 「겸직」과 사유 표현(고려하여·위하여 등)이 함께 적힌 "
                                          "사람별 칸이고 그 칸에 겸직 회사 「%s」가 나와 이 행의 겸직 사유로 옮김"
                                          % (d.page(i), hn, cells_of(d.L[i])[0], r["concurrent_company"]))
            s0, _ = d.section_span(i)
            sections.setdefault(("A", d.label, d.fy), {}).setdefault(d.rcept, set()).add(s0)
            judg.add("겸직 사유: Ⅷ·Ⅸ 밖 사람별 표 칸(이사 현황 「선임 배경」 등)에 「겸직」과 사유 표현이 함께 있고 겸직 회사 이름이 나오면 reason_text 로 옮김")
        elif r_lines[d.rcept]:
            i, l = r_lines[d.rcept][0]
            r["note"] = r["note"].replace("겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음",
                                          "겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음 — 넓혀 찾음: %s 글 「%s」이 있으나 사람별 사유가 아니라 reason_text 에 넣지 않음(판단)"
                                          % (d.page(i), l.strip()))
            judg.add("겸직 사유: 사람이 정해지지 않은 「…위해 … 겸직체계」 같은 글은 reason_text 에 넣지 않고 그 보고서 A 행 note 에만 적음")
        else:
            r["note"] = r["note"].replace("겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음",
                                          "겸직 사유 글: 이 보고서 Ⅷ·Ⅸ에 없음(보고서 전체의 사람별 표 칸·「위해 … 겸직」 글로 넓혀 찾아도 없음)")

    # ------------------------------------------------------------ (15차 검증 보정) 같은 회사·같은 성명 출생년월 원문이 둘 이상
    byname = {}
    for r in A_rows:
        if r["birth_ym"]:
            byname.setdefault((r["corp_label"], name_key(r["person"])), {}).setdefault(r["birth_ym"].rstrip("."), set()).add(r["fy"])
    for r in A_rows:
        bs = byname.get((r["corp_label"], name_key(r["person"])), {})
        if len(bs) > 1:
            r["note"] += ("; (판단) 동명이인 확인: 같은 회사 겸직 행에서 같은 성명의 출생년월 원문이 보고서마다 다름 — %s; "
                          "원문만으로 같은 사람인지 가를 수 없어 행마다 그 보고서 임원 현황 표 값을 둠(애매)"
                          % " · ".join("%s(FY%s)" % (b, "·FY".join(sorted(f))) for b, f in sorted(bs.items())))
            judg.add("동명이인 확인: 같은 회사·같은 성명에 출생년월 원문이 둘 이상이면 행 note 에 FY별 값을 적고 애매로 표시")

    # ------------------------------------------------------------ 13차 경영공시 2026.2Q (B·D)
    for co in COS:
        name, text = t13_text("경영공시", co)
        m = mg.get(co)
        if not text or not m:
            probs.append("%s 경영공시 2026.2Q 텍스트 없음" % co)
            continue
        pdf = PDFText(text)
        lines = []          # (page, line)
        for n, ls in pdf.pages:
            for l in ls:
                lines.append((n, l))
        texts = [l for (_, l) in lines]
        mb = dict(corp_label=co, fy="2026.2Q", doc_kind="경영공시", rcept_no_or_url=m["실제url"] or m["url"],
                  doc_name=m["제목"], collected_at=kst_iso(m["fetched_at"]))
        common = "13차 경영공시 2026.2Q PDF 텍스트(%s, pymupdf) — PDF 줄바꿈만 붙여 씀" % name.split("/")[-1]
        seen = set()
        brow = []
        for i, (pg, l) in enumerate(lines):
            for k in b_kws(l):
                txt, s, e = sentence(texts, i)
                key = (k, nz(txt))
                if key in seen:
                    continue
                seen.add(key)
                if k not in b_kws(txt):
                    continue
                r = dict(mb)
                pages = sorted(set(lines[j][0] for j in range(s, e + 1)))
                r.update(employees_total="", regular="", contract="", keyword=k, source_text=txt,
                         page=",".join("p.%d" % p for p in pages),
                         note="; ".join([common, "직원 수 칸은 비움(사업보고서 행 참조)"]))
                r["_line"] = i
                brow.append(r)
                for p in pages:
                    sections.setdefault(("B", co, "2026.2Q"), {}).setdefault("mgmt", set()).add(p)
        if not brow:
            r = dict(mb)
            r.update(employees_total="", regular="", contract="", keyword="없음", source_text=NONE,
                     page="p.1~p.%d(경영공시 전체 — 찾은 범위)" % len(pdf.pages),
                     note="; ".join([common, "찾은 범위: 경영공시 2026.2Q 전체 %d쪽 · 검색어 겸직·파견·출향·전출·전적·겸무 · 없음" % len(pdf.pages),
                                     "직원 수 칸은 비움(사업보고서 행 참조)"]))
            r["_line"] = 0
            brow.append(r)
        B_rows.extend(brow)
        drow, seen = [], set()
        for i, (pg, l) in enumerate(lines):
            for mm in D_RE.finditer(l):
                txt, s, e = sentence(texts, i)
                key = nz(txt)
                if key in seen:
                    continue
                seen.add(key)
                r = dict(mb)
                pages = sorted(set(lines[j][0] for j in range(s, e + 1)))
                r.update(counterparty="", contract_type=contract_type(l, mm), amount="", source_text=txt,
                         page=",".join("p.%d" % p for p in pages),
                         note="; ".join([common, "검색어 「%s」" % mm.group(0)] +
                                        ([] if CT_RE.search(txt) else ["같은 글에 계약·거래·약정·수수료·체결 낱말 없음"]) +
                                        ["(판단) contract_type 은 검색어가 든 낱말 덩어리(앞뒤 조사·어미 뗌)"]))
                r["_line"] = i
                drow.append(r)
                for p in pages:
                    sections.setdefault(("D", co, "2026.2Q"), {}).setdefault("mgmt", set()).add(p)
        if not drow:
            r = dict(mb)
            r.update(counterparty="", contract_type="", amount="", source_text=NONE,
                     page="p.1~p.%d(경영공시 전체 — 찾은 범위)" % len(pdf.pages),
                     note="; ".join([common, "찾은 범위: 경영공시 2026.2Q 전체 %d쪽(「업무위탁」 현황 표·글 없음) · 검색어: %s · 없음" % (len(pdf.pages), D_TERMS)]))
            r["_line"] = 0
            drow.append(r)
        D_rows.extend(drow)

    # ------------------------------------------------------------ FY2025 본: 13차 본문 PDF 쪽
    for rcept, jobs in pdf_jobs.items():
        d = docs[rcept]
        name, text = t13_text("사업보고서", d.label)
        if not text or rcept not in text[:2000]:
            probs.append("%s FY2025 13차 본문 PDF 텍스트가 %s 것이 아님 — 쪽 못 붙임" % (d.label, rcept))
            continue
        pdf = PDFText(text)
        cur = anchor = pdf.anchor("VIII. 임원 및 직원 등에 관한 사항")
        miss = 0
        for (i, needle, row) in sorted(jobs, key=lambda x: x[0]):
            pos = pdf.find(needle, cur, 40000)
            if pos >= 0:
                cur = pos
            else:
                # 앞뒤 가까운 곳(같은 장) — 찾아도 커서는 움직이지 않음
                pos = pdf.find(needle, max(anchor, cur - 40000), 80000)
                if pos < 0:
                    pos = pdf.find(needle, cur, len(pdf.buf))     # 멀리 앞(Ⅺ 등) — 커서 옮김
                    if pos >= 0:
                        cur = pos
                if pos < 0 and len(needle) > 12:
                    pos = pdf.find(needle[:12], cur, 6000)
            if pos >= 0:
                row["page"] += "; p.%d(본문 PDF, 13차 보관)" % pdf.page_at(pos)
            else:
                miss += 1
                row["note"] += "; 13차 본문 PDF 텍스트에서 같은 글 못 찾음(쪽 없음)"
                if os.environ.get("BS_G1_DEBUG"):
                    print("PDFMISS", d.label, i, needle, file=sys.stderr)
        if miss:
            probs.append("%s FY2025 13차 PDF 쪽 못 찾은 행 %d" % (d.label, miss))

    # ------------------------------------------------------------ 쓰기
    for rows in (A_rows, B_rows, D_rows):
        for r in rows:
            for k in [k for k in r if k.startswith("_")]:
                r.pop(k)
    os.makedirs(FRAG, exist_ok=True)
    write(os.path.join(FRAG, "A_bs_g1.csv"), A_rows, A_COLS)
    write(os.path.join(FRAG, "B_bs_g1.csv"), B_rows, B_COLS)
    write(os.path.join(FRAG, "D_bs_g1.csv"), D_rows, D_COLS)
    nfiles = write_orig(sections, docs, mg)
    return A_rows, B_rows, D_rows, probs, judg, h5_report, nfiles


# ================================================================ 5차 대조
def load_h5():
    out = {}
    with open(H5_GJ, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            co = LABEL5.get(r["corp_label"])
            if co and r["구분"] == "지주" and 2019 <= int(r["fy"]) <= 2025:
                out.setdefault((co, int(r["fy"])), []).append(r)
    join = {}
    with open(H5_JOIN, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            co = LABEL5.get(r["corp_label"])
            if co and r["구분"] == "지주" and 2019 <= int(r["fy"]) <= 2025:
                join.setdefault((co, int(r["fy"]), r["rcept_no"], name_key(r["겸직자"]), comp_key(r["겸직회사"])), []).append(r)
    return dict(gj=out, join=join)


def compare_h5(co, fy, h5, a_records, docs, by_fy, rows):
    """5차 행(같은 접수번호 문서)마다 이번 추출과 견줌. 돌려줌: (회사, fy, 접수번호, 5차 성명, 5차 회사, 판정)."""
    out = []
    for r in h5["gj"].get((co, fy), []):
        rc = r["rcept_no"]
        if rc not in a_records:
            out.append((co, fy, rc, r["겸직자"], r["겸직회사"], "5차 접수번호의 md 없음"))
            continue
        offt, gjt = a_records[rc]
        pk, ck = name_key(r["겸직자"]), comp_key(r["겸직회사"])
        recs = [x for g in gjt for x in g["recs"]]
        tgt = nz(r["원문행"]).replace("|", "")
        if r["출처유형"] == "겸직표":
            exact = [x for x in recs if nz(x["src"]).replace("|", "") == tgt]
            ok = exact or [x for x in recs if x["pkey"] == pk and pk and
                           (x["ckey"] == ck or (ck and ck in x["ckey"]) or (x["ckey"] and x["ckey"] in ck))]
            if ok and not pk:
                out.append((co, fy, rc, r["겸직자"], r["원문행"][:60], "같음 — 5차 미매핑(성명 빈칸) 병합 칸 행, 이번엔 윗줄 성명 「%s」로 채움" % ok[0].get("person", "")))
            elif ok:
                out.append((co, fy, rc, r["겸직자"], r["겸직회사"], "같음"))
            else:
                inmd = any(nz(l).replace("|", "") == tgt for l in docs[rc].L)
                out.append((co, fy, rc, r["겸직자"], r["겸직회사"],
                            "겸직표 행 — 이번 추출에 없음; 원문행 글이 md 에 %s" % ("있음(추출 누락)" if inmd else "없음")))
        else:
            mine = [x for x in rows if name_key(x["person"]) == pk]
            comp_hit = [x for x in mine if comp_key(x["concurrent_company"]) and
                        (comp_key(x["concurrent_company"]) in ck or ck in comp_key(x["concurrent_company"]))]
            if comp_hit:
                v = "같음(경력란서술 — 이번엔 %s)" % ("겸직 표 행" if not comp_hit[0]["note"].startswith("임원 현황 칸") else "임원 현황 칸 행")
            else:
                v = "5차에만(경력란서술 「%s」) — 원문에 있으나 이번 기준(겸임교수·학교 등 제외)으로 뺌" % r["판별어휘"]
            out.append((co, fy, rc, r["겸직자"], r["겸직회사"][:40], v))
    return out


# ================================================================ 문장(PDF 줄) — 15차 g1 연차보고서 스크립트와 같은 규칙
END_RE = re.compile(r"(다\.|요\.|음\.|함\.|됨\.|임\.|\.|(임|다|음|함)\))\s*$")
BULLET_RE = re.compile(r"^\s*([-*•·□■○●▶◦]|주\s?\d+\)|\(?\d{1,2}\)|[①-⑳]|[가-하]\.|\([가-하]\)|\d{1,2}\.|\([가-하IVX]+\))\s*")


def sentence(lines, i, maxback=4, maxfwd=4):
    s = i
    for _ in range(maxback):
        if s == 0:
            break
        prev = lines[s - 1]
        if not prev.strip() or END_RE.search(prev) or BULLET_RE.match(lines[s] or "") or len(prev.strip()) < 20:
            break
        s -= 1
    e = i
    for _ in range(maxfwd):
        cur = lines[e]
        if END_RE.search(cur) or e + 1 >= len(lines):
            break
        if BULLET_RE.match(cur) and len(cur.strip()) < 45:
            break
        nxt = lines[e + 1]
        if not nxt.strip() or BULLET_RE.match(nxt) or nxt.strip().startswith("(") \
                or (len(nxt.strip()) < 12 and not nxt.strip().endswith(".")):
            break
        e += 1
    return "".join(lines[j] for j in range(s, e + 1)).strip(), s, e


# ================================================================ 쓰기
def write(path, rows, cols):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def write_orig(sections, docs, mg):
    """이 스크립트 몫(g1 4개사 사업보고서·2026.2Q 경영공시) 원문 md 를 지우고 다시 씀 — 다른 에이전트 파일은 건드리지 않음."""
    for task in ("A", "B", "D"):
        d0 = os.path.join(ORIG, task)
        if not os.path.isdir(d0):
            continue
        for fn in os.listdir(d0):
            if re.fullmatch(r"(%s)__(FY20\d\d__사업보고서|2026\.2Q__경영공시)\.md" % "|".join(COS), fn):
                os.remove(os.path.join(d0, fn))
    n = 0
    for (task, co, fy), per in sorted(sections.items(), key=lambda x: (x[0][0], COS.index(x[0][1]), str(x[0][2]))):
        d0 = os.path.join(ORIG, task)
        os.makedirs(d0, exist_ok=True)
        if fy == "2026.2Q":
            name, text = t13_text("경영공시", co)
            pdf = PDFText(text)
            m = mg[co]
            out = ["# %s 2026.2Q 경영공시 — 작업 %s 원문(행이 나온 쪽 전체)" % (co, task), "",
                   "- 출처: 「%s」 · %s · 받은 시각 %s(KST) · 원본 sha256 %s" % (m["제목"], m["실제url"] or m["url"], kst_iso(m["fetched_at"]), m["sha256"]),
                   "- 글: 13차 보관 텍스트 `%s`(handoff/13차_지주관리유형/13차_지주관리유형_텍스트.zip, pymupdf 글자 그대로) — 쪽 「## p.N」= PDF 쪽" % name, ""]
            for p in sorted(per["mgmt"]):
                for (pn, ls) in pdf.pages:
                    if pn == p:
                        out.append("## p.%d" % pn)
                        out.extend(ls)
                        out.append("")
            fn = os.path.join(d0, "%s__2026.2Q__경영공시.md" % co)
        else:
            out = ["# %s FY%d 사업보고서 — 작업 %s 원문(행이 나온 절 전체)" % (co, fy, task), ""]
            for rc in sorted(per, key=lambda x: (docs[x].kind != "본", x)):
                d = docs[rc]
                mt = d.meta
                out.append("## 출처: %s (%s) · 접수번호 %s · 접수일 %s · OpenDART document.xml `%s` (sha256 %s) · 받은 시각 %s · md `%s`" % (
                    mt["report_nm"], mt["kind"], rc, mt["rcept_dt"], mt["raw_path"], mt["raw_sha256"], mt["fetched_at"], mt["text_path"]))
                out.append("")
                for s in sorted(per[rc]):
                    a, b = d.section_span(s)
                    out.extend(d.L[a:b])
                    out.append("")
            fn = os.path.join(d0, "%s__FY%d__사업보고서.md" % (co, fy))
        with open(fn, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out).rstrip("\n") + "\n")
        n += 1
    return n


def main():
    A, B, D, probs, judg, h5r, nfiles = build()
    from collections import Counter
    print("A", len(A), dict(Counter(r["corp_label"] for r in A)))
    print("B", len(B), dict(Counter(r["corp_label"] for r in B)))
    print("D", len(D), dict(Counter(r["corp_label"] for r in D)))
    print("문서에 없음: A %d · B %d · D %d" % (sum(r["source_text"] == NONE for r in A), sum(r["source_text"] == NONE for r in B),
                                         sum(r["source_text"] == NONE for r in D)))
    print("원문 md 파일", nfiles)
    print("문제", len(probs))
    for p in probs:
        print("  ", p)
    print("판단", len(judg))
    for j in sorted(judg):
        print("  ", j)
    c5 = Counter(x[5].split(";")[0] if "경력란" not in x[5] else x[5] for x in h5r)
    print("5차 대조", len(h5r), dict(c5))
    diag = os.environ.get("BS_G1_DIAG")
    if diag:
        with open(diag, "w", encoding="utf-8") as f:
            for x in h5r:
                f.write("\t".join(str(y) for y in x) + "\n")


if __name__ == "__main__":
    main()
