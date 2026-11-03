"""15차 확장(REQUEST15b.md) 작업 B 추가분·C 추가분·E — 조각 만들기(단계 2). 문서 받기는 ops15b_X2_fetch.py.

산출(utf-8-sig, 사용자 열 + doc_name, collected_at):
  dart_out/ops15/조각/B_ext.csv · C_ext.csv · E.csv · 확인_B_ext.csv · 확인_C_ext.csv · 확인_E.csv
  dart_out/ops15/원문/B|C|E/*.md (행이 나온 절 글 그대로) · dart_out/ops15/문서목록15b_X2.csv

규칙(기계적으로 정한 것 — 행 note 에도 적음):
- 작업 B 키워드: 겸직·파견·출향·전출·전적·겸무(「전적」은 「전적으로/전적인/전적합」 뺌 — 기존 ops15_bs_g1.py 와 같은 규칙).
  글 단위: md 표 행은 한 줄, 글은 이어진 줄(빈 줄·표·제목에서 끊고, 앞 줄이 「&cr;」·「…다.」로 끝나거나 새 줄이 「주1)」「※」「(1)」「가.」 등으로
  시작하면 끊음). 키워드는 공백·줄바꿈을 지운 글에서 찾음(줄에 걸친 낱말).
  사업보고서는 Ⅷ(임원 및 직원 등에 관한 사항) 안(기존 B 와 같은 범위). NH FY2012 와 우리 FY2022·FY2023 「전출」은 사용자 질문 때문에 문서 전체(판단, note).
  직원 수: Ⅷ 직원 현황 표(머리에 「직원수」)의 합계 행 — 머리 「정규직|계약직|기타|합계」이면 2·3·5번째 칸, 「기간의 정함이 없는 근로자|기간제 근로자|합계」
  (+전체|(단시간))이면 2·4·6번째 칸(기존 B 와 같음).
- 작업 C(우리 2024-08~2025-07 공시): C 키워드(인력·임직원·조직·겸직·파견·전적·채용)와 「내부통제」「준법」「성과평가」를 동양생명·ABL생명 언급 글 단위에서 찾음.
- 작업 E: 합병 주요사항보고서 「1. 합병의 목적」 절의 문단(XML 줄바꿈 표지 &cr; 와 새 문단 머리로 나눔, 제목 줄은 section_title 로) 마다 1행,
  FY2013 사업보고서 「회사와 계열회사간 임원 겸직 현황」 표 행마다 1행(+ 표 아래 주, 문서 안 다른 「겸직」 글 줄).
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OPS = "dart_out/ops15"
FRAG = OPS + "/조각"
RAWX = "dart_out/raw/ops15b/X2"
NONE = "문서에 없음"
DOCS = json.load(open(RAWX + "/docs.json", encoding="utf-8"))
REQ = open(OPS + "/REQUEST15b.md", encoding="utf-8").read().split("\n")

B_COLS = ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind",
          "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
C_COLS = ["corp_label", "doc_kind", "rcept_no", "rcept_dt", "section_title", "keyword", "source_text", "page", "note",
          "doc_name", "collected_at"]
E_COLS = ["corp_label", "doc_kind", "rcept_no", "rcept_dt", "section_title", "source_text", "page", "note", "doc_name",
          "collected_at"]
K_COLS = ["item_id", "item_text", "corp_label", "fy", "result", "where", "rcept_no_or_url", "page", "source_excerpt", "note"]
L_COLS = ["doc_kind", "corp_label", "fy_or_date", "report_nm", "rcept_no_or_url", "rcept_dt", "raw_path", "sha256",
          "fetched_at", "text_path", "status", "note"]


# ================================================================ 공통
def nz(s):
    return re.sub(r"\s+", "", s or "")


def nzx(s):
    """XML md 대조용: 공백·줄바꿈과 md 표지 「|」「<br>」를 지움."""
    return re.sub(r"\s+|\||<br>", "", s or "")


def cells_of(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split(" | ")] if " | " in s else [s.strip()]


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def req_line(prefix):
    for l in REQ:
        s = l.strip()
        if s.startswith("* "):
            s = s[2:]
        if s.startswith(prefix):
            return s
    raise SystemExit("REQUEST15b 줄 없음: " + prefix)


def excerpt(text, pos, maxlen=300):
    """pos 가 든 문장(「다.」 사이) — 원문 이어진 글, 300자 이하."""
    a = max(text.rfind("다.", 0, pos), text.rfind("&cr;", 0, pos))
    a = 0 if a < 0 else a + (2 if text[a:a + 2] == "다." else 4)
    b = text.find("다.", pos)
    b = len(text) if b < 0 else b + 2
    s = text[a:b].strip()
    if len(s) > maxlen:
        st = max(a, pos - maxlen // 2)
        s = text[st:st + maxlen].strip()
    return s


TRUE_JJ = re.compile(r"(?<![가-힣])전적(?!으로|인|합)")
B_KWS = ["겸직", "파견", "출향", "전출", "전적", "겸무"]


def b_kws(t):
    t = nz(t)
    return [k for k in B_KWS if (TRUE_JJ.search(t) if k == "전적" else k in t)]


class Md:
    def __init__(self, path):
        self.path = path
        self.L = open(path, encoding="utf-8").read().split("\n")
        self.body = 0
        for i, l in enumerate(self.L[:12]):
            if l.startswith("- 쪽 번호 없음"):
                self.body = i + 1
        self.heads, self.tab_of, self.tables = [], {}, []
        cur = None
        for i, l in enumerate(self.L):
            if i < self.body:
                continue
            m = re.match(r"### \[절 (\d+)\] ?(.*)$", l)
            if m:
                self.heads.append((i, int(m.group(1)), m.group(2).strip()))
                continue
            m = re.match(r"\[표 (\d+)\]$", l.strip())
            if m:
                cur = dict(no=int(m.group(1)), s=i, e=None, rows=[])
                self.tables.append(cur)
                continue
            if l.strip() == "[표 끝]":
                if cur:
                    cur["e"] = i
                cur = None
                continue
            if cur is not None and l.startswith("|"):
                self.tab_of[i] = cur["no"]
                cur["rows"].append((i, cells_of(l)))

    def head_at(self, i):
        h = None
        for x in self.heads:
            if x[0] <= i:
                h = x
            else:
                break
        return h

    def chap_at(self, i):
        h = None
        for x in self.heads:
            if x[0] > i:
                break
            if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ|Ⅺ|Ⅻ)\.", x[2]):
                h = x
        return h

    def page(self, i):
        h = self.head_at(i)
        p = 'XML [절 %d] 「%s」' % (h[1], h[2]) if h else "XML (첫 절 앞)"
        if i in self.tab_of:
            p += " [표 %d]" % self.tab_of[i]
        return p

    def chapter(self, start_rx, end_rx):
        s = e = None
        for (i, n, t) in self.heads:
            if s is None and re.match(start_rx, t):
                s = i
            elif s is not None and re.match(end_rx, t):
                e = i
                break
        if s is None:
            return None
        return s, (e if e is not None else len(self.L))

    def section_span(self, i):
        h = self.head_at(i)
        if not h:
            return self.body, i + 1
        nxt = [x[0] for x in self.heads if x[0] > h[0]]
        return h[0], (nxt[0] if nxt else len(self.L))


def is_blank(l):
    return re.sub(r"(&cr;)+", "", l).strip() == ""


START_NEW = re.compile(r"^\s*(주\s*\d+\)|주\)|※|\*|＊|\(\d+\)|\d+\)|[가-하]\.|\d+\.\s|-\s|·|ㆍ|◆|<|\[|가-\d)")


def ends_par(l):
    s = l.rstrip()
    return s.endswith("&cr;") or bool(re.search(r"(다|음|함|임|됨|요)\.\s*$", s))


def units(md, s, e, maxn=6):
    out, run = [], []

    def flush():
        if run:
            out.append(("text", run[0], run[-1]))
        run.clear()

    for i in range(max(s, md.body), e):
        l = md.L[i]
        if l.startswith("### ") or re.match(r"\[표 \d+\]$", l.strip()) or l.strip() == "[표 끝]":
            flush()
            continue
        if i in md.tab_of:
            flush()
            out.append(("row", i, i))
            continue
        if is_blank(l):
            flush()
            continue
        if run and (START_NEW.match(l) or ends_par(md.L[run[-1]]) or len(run) >= maxn):
            flush()
        run.append(i)
    flush()
    return out


def utext(md, u):
    return "\n".join(md.L[u[1]:u[2] + 1])


def doc_meta(rc):
    for d in DOCS:
        if d["rcept_no"] == rc:
            return d
    raise KeyError(rc)


BR = {}
for r in csv.DictReader(open(OPS + "/사업보고서_원문.csv", encoding="utf-8-sig")):
    BR[r["rcept_no"]] = r


def emp_table(md, s, e):
    for t in md.tables:
        if not (s <= t["s"] < e) or not t["rows"]:
            continue
        heads = " ".join(nz(c) for _, cs in t["rows"][:3] for c in cs)
        if "직원수" not in heads and nz(t["rows"][0][1][0]) != "직원":
            continue
        tot = [(i, c) for i, c in t["rows"] if nz(c[0]) == "합계"]
        if not tot:
            continue
        i, c = tot[-1]
        g = lambda k: c[k] if len(c) > k else ""
        if "정규직" in heads:
            return dict(line=i, cells=c, table=t["no"], reg=g(1), con=g(2), etc=g(3), tot=g(4),
                        how="(판단) 칸 차례 합계|정규직|계약직|기타|합계(머리행 「정규직|계약직|기타|합계」)")
        return dict(line=i, cells=c, table=t["no"], reg=g(1), con=g(3), etc="", tot=g(5),
                    how="(판단) 칸 차례 합계|기간의정함없음 전체|(단시간)|기간제 전체|(단시간)|합계")
    return None


def officer_tables(md, s, e):
    out = set()
    for t in md.tables:
        if s <= t["s"] < e and t["rows"]:
            h = nz(" ".join(t["rows"][0][1]))
            if "성명" in h and ("출생년월" in h or "등기임원" in h):
                out.add(t["no"])
    return out


SEC_MD = defaultdict(list)   # (task, mdname) -> [(md, i, label)]


def add_sec(task, name, md, i, head):
    SEC_MD[(task, name)].append((md, i, head))


def write_secs():
    made = []
    for (task, name), lst in SEC_MD.items():
        path = "%s/원문/%s/%s" % (OPS, task, name)
        head = lst[0][2]
        parts, seen = [], set()
        for md, i, _ in sorted(lst, key=lambda x: (x[0].path, x[1])):
            a, b = md.section_span(i)
            key = (md.path, a, b)
            if b - a > 400:   # 아주 긴 절(재무제표 등)은 행 앞뒤 40줄만
                a2, b2 = max(a, i - 40), min(b, i + 41)
                key = (md.path, a2, b2)
                if key in seen:
                    continue
                seen.add(key)
                hh = md.head_at(i)
                parts.append("## %s — md 줄 %d~%d(절이 길어 행 앞뒤 40줄만; 절 머리 「[절 %d] %s」 md 줄 %d)\n\n- 글: `%s`\n\n%s\n"
                             % (md.page(i), a2 + 1, b2, hh[1] if hh else 0, hh[2] if hh else "", a + 1, md.path,
                                "\n".join(md.L[a2:b2])))
                continue
            if key in seen:
                continue
            seen.add(key)
            hh = md.head_at(i)
            parts.append("## XML [절 %s] 「%s」 — md 줄 %d~%d\n\n- 글: `%s`\n\n%s\n"
                         % (hh[1] if hh else "-", hh[2] if hh else "", a + 1, b, md.path, "\n".join(md.L[a:b])))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as w:
            w.write(head + "\n\n" + "\n".join(parts))
        made.append(path)
    return made


def mdname(task, corp, fyd, doc):
    """기존 이름과 겹치지 않게 — 이미 있고 이번 실행에서 만든 것이 아니면 「__X2」를 붙임."""
    base = "%s__%s__%s.md" % (corp, fyd, doc)
    p = "%s/원문/%s/%s" % (OPS, task, base)
    if os.path.exists(p) and (task, base) not in SEC_MD and not MINE.get(p):
        base = "%s__%s__%s__X2.md" % (corp, fyd, doc)
    MINE["%s/원문/%s/%s" % (OPS, task, base)] = True
    return base


MINE_PATH = RAWX + "/mine_md.json"
MINE = {}
if os.path.exists(MINE_PATH):
    MINE = json.load(open(MINE_PATH, encoding="utf-8"))
JUDG = []


# ================================================================ 작업 B
def b_rows_doc(meta, scope, fy, label, extra_note="", only_kw=None, docname=None):
    md = Md(meta["text_path"])
    viii = md.chapter(r"^(VIII|Ⅷ)\.", r"^(IX|Ⅸ|X|Ⅹ)\.")
    s, e = (viii if scope == "VIII" else (md.body, len(md.L)))
    emp = emp_table(md, *viii) if viii else None
    offs = officer_tables(md, *viii) if viii else set()
    hits = []
    for u in units(md, s, e):
        t = utext(md, u)
        for k in b_kws(t):
            if only_kw and k not in only_kw:
                continue
            hits.append((u, k, t))
    return md, viii, emp, offs, hits


def b_base(label, fy, meta, docname=None):
    return dict(corp_label=label, fy=fy, doc_kind="사업보고서", rcept_no_or_url=meta["rcept_no"],
                doc_name=docname or meta.get("report_nm", ""), collected_at=meta.get("fetched_at", ""))


def emp_fields(emp):
    if not emp:
        return dict(employees_total=NONE, regular=NONE, contract=NONE), "직원 현황 표 합계 행을 Ⅷ에서 찾지 못함"
    note = "직원 수: [표 %d] 합계 행 「%s」 — %s" % (emp["table"], " | ".join(emp["cells"]), emp["how"])
    if emp["etc"] not in ("", "-"):
        note += "; 기타 칸 %s" % emp["etc"]
    return dict(employees_total=emp["tot"], regular=emp["reg"], contract=emp["con"]), note


def build_b():
    rows, kchk = [], []
    secname = {}

    def sec(md, i, label, fyd, meta):
        nm = secname.get((label, fyd, meta["rcept_no"]))
        if not nm:
            nm = mdname("B", label, fyd, "사업보고서" if meta.get("doc_kind", "사업보고서") == "사업보고서" else "문서")
            secname[(label, fyd, meta["rcept_no"])] = nm
        head = ("# %s FY%s 사업보고서 — 작업 B 행이 나온 절(15b X2)\n\n- 출처: %s · 접수번호 %s · https://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s"
                " · 받은 시각 %s · 글 `%s`\n- 글자는 XML md 그대로(태그만 걷어냄)."
                % (label, fyd.replace("FY", ""), meta.get("report_nm", ""), meta["rcept_no"], meta["rcept_no"],
                   meta.get("fetched_at", ""), meta["text_path"]))
        add_sec("B", nm, md, i, head)

    # ---------- KB FY2014·FY2016·FY2017 (+정정), NH FY2012
    groups = defaultdict(list)
    for d in DOCS:
        if d["task"] == "B":
            groups[(d["label"], d["fy"])].append(d)
    for (label, fy), ds in sorted(groups.items()):
        main = [d for d in ds if d["kind"] == "본"][0]
        cors = sorted([d for d in ds if d["kind"] != "본"], key=lambda d: d["rcept_no"])
        scope = "ALL" if label == "NH농협금융지주" else "VIII"
        md, viii, emp, offs, hits = b_rows_doc(main, scope, fy, label)
        ef, enote = emp_fields(emp)
        cor_txt = {}
        for c in cors:
            cm = Md(c["text_path"])
            cv = cm.chapter(r"^(VIII|Ⅷ)\.", r"^(IX|Ⅸ|X|Ⅹ)\.")
            cor_txt[c["rcept_no"]] = (cm, cv, nzx("\n".join(cm.L[cv[0]:cv[1]])) if cv else "", emp_table(cm, *cv) if cv else None)

        def cor_note(t):
            out = []
            for rc, (cm, cv, ctext, cemp) in cor_txt.items():
                out.append("정정 %s: %s" % (rc, "같은 글 있음" if nzx(t) in ctext else "이 글 없음(바뀜·빠짐)"))
            return "; ".join(out)

        emp_cor = []
        for rc, (cm, cv, ctext, cemp) in cor_txt.items():
            if emp and cemp and nzx(" ".join(cemp["cells"])) != nzx(" ".join(emp["cells"])):
                emp_cor.append("정정 %s 직원 합계 행 다름: 「%s」" % (rc, " | ".join(cemp["cells"])))
        if emp:
            sec(md, emp["line"], label, "FY" + fy, main)
        if not hits:
            r = b_base(label, fy, main)
            r.update(ef)
            r.update(keyword="없음", source_text=md.L[emp["line"]] if emp else NONE, page=md.page(emp["line"]) if emp else "Ⅷ 전체",
                     note="; ".join(x for x in ["Ⅷ 전체(임원 현황·겸직 표·직원 현황 표·각주·임원 보수)에서 겸직·파견·출향·전출·전적·겸무 없음",
                                                 enote, cor_note(md.L[emp["line"]]) if emp else "", "; ".join(emp_cor)] if x))
            rows.append(r)
        seen = set()
        for (u, k, t) in hits:
            key = (k, u[1], u[2])
            if key in seen:
                continue
            seen.add(key)
            r = b_base(label, fy, main)
            r.update(ef)
            where = "표 행" if u[0] == "row" else ("글 줄" if u[1] == u[2] else "글(md 줄 %d개 이어 붙임, 줄바꿈 그대로)" % (u[2] - u[1] + 1))
            ch = md.chap_at(u[1])
            loc = ("Ⅷ " if viii and viii[0] <= u[1] < viii[1] else "(위치) %s — Ⅷ 밖; " % (ch[2] if ch else "?")) + where
            pos = "(위치) 임원 현황 표 — 작업 A 와 겹침" if md.tab_of.get(u[1]) in offs else ""
            extra = ""
            if scope == "ALL" and not (viii and viii[0] <= u[1] < viii[1]):
                extra = "(판단) NH FY2012 는 사용자 질문(중앙회·은행 출신의 전적·파견 여부) 때문에 Ⅷ 밖 문서 전체에서도 찾음"
                JUDG.append("B_ext NH FY2012: Ⅷ 밖 문서 전체에서 키워드 행을 더함")
            r.update(keyword=k, source_text=t, page=md.page(u[1]),
                     note="; ".join(x for x in [pos, loc, extra, enote, cor_note(t), "; ".join(emp_cor)] if x))
            rows.append(r)
            sec(md, u[1], label, "FY" + fy, main)
        # 정정에만 있는 키워드 글
        for rc, (cm, cv, ctext, cemp) in cor_txt.items():
            if not cv:
                continue
            maintext = nzx("\n".join(md.L[viii[0]:viii[1]])) if viii else ""
            cmeta = [c for c in cors if c["rcept_no"] == rc][0]
            for u in units(cm, *cv):
                t = utext(cm, u)
                for k in b_kws(t):
                    if nzx(t) not in maintext:
                        r = b_base(label, fy, cmeta)
                        r.update(ef if not cemp else emp_fields(cemp)[0])
                        r.update(keyword=k, source_text=t, page=cm.page(u[1]),
                                 note="정정 %s 에만 있는 글(본 %s Ⅷ 에 같은 글 없음); Ⅷ" % (rc, main["rcept_no"]))
                        rows.append(r)
                        sec(cm, u[1], label, "FY" + fy, cmeta)
        # NH: 직원 현황 합계 행·각주(사용자 항목)
        if label == "NH농협금융지주" and emp:
            r = b_base(label, fy, main)
            r.update(ef)
            r.update(keyword="없음", source_text=md.L[emp["line"]], page=md.page(emp["line"]),
                     note="(판단) 키워드 낱말 없는 행 — 사용자 항목(직원 현황, 평균근속 10개월) 때문에 넣은 직원 현황 표 합계 행(평균근속연수 칸 「%s」); %s"
                          % (emp["cells"][5] if len(emp["cells"]) > 5 else "", enote))
            rows.append(r)
            fn = None
            for j in range(emp["line"] + 1, min(emp["line"] + 6, len(md.L))):
                if md.L[j].startswith("주1)"):
                    fn = j
                    break
            if fn is not None:
                r = b_base(label, fy, main)
                r.update(ef)
                r.update(keyword="없음", source_text=md.L[fn], page=md.page(fn),
                         note="(판단) 키워드 낱말 없는 행 — 사용자 항목(직원 현황 각주, 평균근속 산정 기준) 때문에 넣은 직원 현황 표 바로 아래 각주 줄; "
                              "이 각주(주1~주3)에 평균근속연수 산정 기준 글 없음(주1 직원수 기준·주2 기타·주3 급여 기간)")
                rows.append(r)
            JUDG.append("B_ext NH FY2012: 키워드 없는 직원 현황 합계 행·각주 줄을 keyword 「없음」으로 넣음(사용자 항목 때문)")

    # ---------- KB FY2017 연차보고서(gov_old md) — 키워드 행
    gl = list(csv.DictReader(open(OPS + "/문서목록15b_gov_old.csv", encoding="utf-8-sig")))
    for g in gl:
        if g["corp_label"] == "KB금융지주" and g["fy_or_date"] == "FY2017" and g["status"] == "받음" and "추가공시" not in g["report_nm"]:
            t = open(g["text_path"], encoding="utf-8").read()
            add_t = ""
            for g2 in gl:
                if g2["corp_label"] == "KB금융지주" and g2["fy_or_date"] == "FY2017" and "추가공시" in g2["report_nm"] and g2["text_path"]:
                    add_t = open(g2["text_path"], encoding="utf-8").read()
            hits = [k for k in B_KWS if (TRUE_JJ.search(nz(t)) if k == "전적" else re.search(r"\s*".join(k), t))]
            npg = len(re.findall(r"^## p\.\d+", t, re.M))
            gyeom = len(re.findall(r"겸\s*직|겸\s*임|겸\s*무", t))
            assert not hits, hits
            r = dict(corp_label="KB금융지주", fy="2017", employees_total="", regular="", contract="", keyword="없음",
                     source_text=NONE, doc_kind="지배구조 연차보고서", rcept_no_or_url=g["rcept_no_or_url"],
                     page="p.1~p.%d 전체(찾은 범위 — 해당 글 없음)" % npg,
                     note=("찾은 범위: %s 전문(PDF 쪽 텍스트 %s — gov_old 받음), 검색어 겸직·파견·출향·전출·전적·겸무(글자 사이 공백·줄바꿈 허용) — 키워드 글 없음"
                           "(「전적」 글자는 「사전적으로」 4곳뿐 — 규칙상 뺌); 넓은 낱말 겸직·겸임·겸무 %d곳; 「겸」 한 글자는 「회장 겸 국민은행 은행장」(경력 칸)·「겸비」뿐; "
                           "같은 FY 추가공시(%s)도 같은 검색 — 없음") % (g["report_nm"], g["text_path"], gyeom,
                                                                      "있음" if add_t else "없음"),
                     doc_name="%s (본공시, 파일 %s)" % (g["report_nm"], os.path.basename(g["raw_path"])),
                     collected_at=g["fetched_at"])
            rows.append(r)

    # ---------- FY2019~2025 확인 항목: 기존 B_bs 와 대조해 빠진 Ⅷ 키워드 글을 보충
    exist = []
    for f in ["B_bs_g1", "B_bs_g2", "B_bs_g3", "B_gov_g1", "B_gov_g2"]:
        for r in csv.DictReader(open("%s/%s.csv" % (FRAG, f), encoding="utf-8-sig")):
            r["_file"] = f
            exist.append(r)
    GAP = [("KB금융지주", "2023"), ("KB금융지주", "2024"), ("신한금융지주", "2022"), ("신한금융지주", "2023"), ("신한금융지주", "2024"),
           ("하나금융지주", "2022"), ("하나금융지주", "2023"), ("하나금융지주", "2024"), ("BNK금융지주", "2022"), ("BNK금융지주", "2023"),
           ("BNK금융지주", "2024"), ("iM금융지주", "2019"), ("iM금융지주", "2020"), ("iM금융지주", "2023"), ("iM금융지주", "2024"),
           ("우리금융지주", "2022"), ("우리금융지주", "2023")]
    gapinfo = {}
    for (label, fy) in GAP:
        mains = [r for r in BR.values() if r["label"] == label and r["fy"] == fy and r["kind"] == "본" and r["text_path"]]
        if not mains:
            gapinfo[(label, fy)] = dict(err="사업보고서 본 md 없음")
            continue
        m = mains[0]
        meta = dict(rcept_no=m["rcept_no"], report_nm=m["report_nm"], fetched_at=m["fetched_at"], text_path=m["text_path"])
        md, viii, emp, offs, hits = b_rows_doc(meta, "VIII", fy, label)
        ex = [r for r in exist if r["corp_label"] == label and r["fy"] == fy and r["doc_kind"] == "사업보고서"
              and r["rcept_no_or_url"] == m["rcept_no"]]
        exn = [nzx(r["source_text"]) for r in ex if r["source_text"] != NONE]
        added = []
        for (u, k, t) in hits:
            tn = nzx(t)
            ok = any((tn in x) or (len(x) >= 4 and x in tn) for x in exn)
            if not ok:
                ef, enote = emp_fields(emp)
                r = b_base(label, fy, meta)
                if ex and ex[0]["employees_total"]:
                    r.update(employees_total=ex[0]["employees_total"], regular=ex[0]["regular"], contract=ex[0]["contract"])
                else:
                    r.update(ef)
                where = "표 행" if u[0] == "row" else ("글 줄" if u[1] == u[2] else "글(md 줄 %d개 이어 붙임)" % (u[2] - u[1] + 1))
                r.update(keyword=k, source_text=t, page=md.page(u[1]),
                         note="기존 조각(%s, 같은 접수번호)에 이 글 없음 — 15b X2 보충(확인 항목 대조); Ⅷ %s; %s"
                              % ("·".join(sorted({x["_file"] for x in ex})) or "B_bs 행 없음", where, enote))
                rows.append(r)
                added.append(r)
                sec(md, u[1], label, "FY" + fy, meta)
        gapinfo[(label, fy)] = dict(meta=meta, ex=ex, hits=hits, added=added, emp=emp, md=md, viii=viii)

    # ---------- 우리 FY2022·FY2023 「전출」(문서 전체, 사용자 항목) / 「겸직인원」 주석
    woori = {}
    for fy in ("2022", "2023"):
        info = gapinfo[("우리금융지주", fy)]
        md, meta = info["md"], info["meta"]
        jc = []
        for u in units(md, md.body, len(md.L)):
            t = utext(md, u)
            if "전출" in nz(t) and not (info["viii"][0] <= u[1] < info["viii"][1]):
                jc.append((u, t))
                r = b_base("우리금융지주", fy, meta)
                ex = info["ex"]
                r.update(employees_total=ex[0]["employees_total"] if ex else "", regular=ex[0]["regular"] if ex else "",
                         contract=ex[0]["contract"] if ex else "")
                ch = md.chap_at(u[1])
                r.update(keyword="전출", source_text=t, page=md.page(u[1]),
                         note="(위치) %s — Ⅷ 밖 표 행; (판단) 사용자 항목(2023 감축 인원의 은행 전출 언급) 때문에 문서 전체에서 「전출」을 찾은 결과 — 퇴직급여 주석 표 칸"
                              % (ch[2] if ch else "?"))
                rows.append(r)
                sec(md, u[1], "우리금융지주", "FY" + fy, meta)
        JUDG.append("B_ext 우리 FY2022·FY2023: Ⅷ 밖 문서 전체의 「전출」 표 행(퇴직급여 주석 「전출입효과」)을 더함(사용자 항목 때문)")
        gj = []
        v = info["viii"]
        for u in units(md, *v):
            t = utext(md, u)
            if "겸직인원" in nz(t) or "자회사소속" in nz(t):
                gj.append((u, t))
        woori[fy] = dict(jc=jc, gj=gj, info=info)
    return rows, gapinfo, woori, exist


def build_kb(rows, gapinfo, woori, exist):
    K = []
    it1 = req_line("KB FY2014·FY2016·FY2017")
    it2 = req_line("신한 FY2022~FY2024, 하나 FY2022~FY2024")
    it3 = req_line("우리 FY2022·FY2023:")
    it4 = req_line("NH FY2012:")

    def ext_rows(label, fy, kind="사업보고서"):
        return [(i, r) for i, r in enumerate(rows) if r["corp_label"] == label and r["fy"] == fy and r["doc_kind"] == kind]

    def first_src(rs):
        for i, r in rs:
            if r["source_text"] != NONE:
                return r
        return rs[0][1] if rs else None

    for fy in ("2014", "2016", "2017"):
        rs = ext_rows("KB금융지주", fy)
        r0 = first_src(rs)
        kws = Counter(r["keyword"] for _, r in rs)
        K.append(dict(item_id="B-1", item_text=it1, corp_label="KB금융지주", fy=fy, result="원문 있음",
                      where="B_ext.csv KB금융지주 FY%s 사업보고서 행 %d개(keyword %s) — 직원 합계 %s" % (fy, len(rs), dict(kws), r0["employees_total"]),
                      rcept_no_or_url=r0["rcept_no_or_url"], page=r0["page"], source_excerpt=r0["source_text"][:300],
                      note="사업보고서 Ⅷ 직원 현황 표 합계 행·키워드 글(새로 받음)"))
        gl = [g for g in csv.DictReader(open(OPS + "/문서목록15b_gov_old.csv", encoding="utf-8-sig"))
              if g["corp_label"] == "KB금융지주" and g["fy_or_date"] == "FY" + fy]
        if fy == "2017":
            g = [x for x in gl if "추가공시" not in x["report_nm"]][0]
            K.append(dict(item_id="B-1", item_text=it1, corp_label="KB금융지주", fy=fy, result=NONE,
                          where="B_ext.csv KB금융지주 FY2017 지배구조 연차보고서 행(keyword 없음)", rcept_no_or_url=g["rcept_no_or_url"],
                          page="전체", source_excerpt="",
                          note="연차보고서 FY2017(본공시·추가공시, gov_old 받음) 전문에서 겸직·파견·출향·전출·전적·겸무 글 없음"))
        else:
            K.append(dict(item_id="B-1", item_text=it1, corp_label="KB금융지주", fy=fy, result="수집 실패",
                          where="dart_out/ops15/문서목록15b_gov_old.csv KB금융지주 FY%s 행(status 실패)" % fy,
                          rcept_no_or_url=gl[0]["rcept_no_or_url"] if gl else "", page="", source_excerpt="",
                          note="그 해 지배구조 연차보고서는 gov_old 가 받지 못함(서버가 PDF 대신 6바이트) — 연차보고서 조직·인력 서술은 보지 못함; 사업보고서만 봄"))
    for fy in ("2023", "2024"):
        K.extend(gap_k("B-1", it1, "KB금융지주", fy, gapinfo, exist))
    for lab, fys in (("신한금융지주", ("2022", "2023", "2024")), ("하나금융지주", ("2022", "2023", "2024")),
                     ("BNK금융지주", ("2022", "2023", "2024")), ("iM금융지주", ("2019", "2020", "2023", "2024"))):
        for fy in fys:
            K.extend(gap_k("B-2", it2, lab, fy, gapinfo, exist))
    # 우리
    w22, w23 = woori["2022"], woori["2023"]
    for fy, w in (("2022", w22), ("2023", w23)):
        info = w["info"]
        md, meta = info["md"], info["meta"]
        if w["gj"]:
            u, t = [x for x in w["gj"] if "겸직인원" in nz(x[1])][0] if [x for x in w["gj"] if "겸직인원" in nz(x[1])] else w["gj"][0]
            p = nz(t).find("자회사소속겸직인원")
            i0 = t.find("주1)")
            K.append(dict(item_id="B-3", item_text=it3, corp_label="우리금융지주", fy=fy, result="원문 있음" if "겸직인원" in nz(t) else NONE,
                          where="B_bs_g1.csv 우리금융지주 FY%s 행(keyword 겸직, rcept %s) — 같은 글" % (fy, meta["rcept_no"]),
                          rcept_no_or_url=meta["rcept_no"], page=md.page(u[1]),
                          source_excerpt=t[i0:i0 + 60] if i0 >= 0 else t[:300],
                          note="「자회사 소속 겸직인원」 주석: Ⅷ 직원 현황 표 아래 각주 주1)"))
        else:
            emp = info["emp"]
            fn = [j for j in range(emp["line"] + 1, emp["line"] + 6) if md.L[j].startswith("주1)")] if emp else []
            K.append(dict(item_id="B-3", item_text=it3, corp_label="우리금융지주", fy=fy, result=NONE,
                          where="B_bs_g1.csv 우리금융지주 FY%s 행(rcept %s) — 직원 현황 각주에 이 주석 없음" % (fy, meta["rcept_no"]),
                          rcept_no_or_url=meta["rcept_no"], page=md.page(fn[0]) if fn else "",
                          source_excerpt=md.L[fn[0]][:300] if fn else "",
                          note="FY%s Ⅷ 직원 현황 각주(source_excerpt = 표 아래 각주 줄 전체)에 「자회사 소속 겸직인원」 없음(찾은 범위: Ⅷ 전체 「겸직인원」「자회사 소속」); 직원 합계 %s(FY2022 150)"
                                    % (fy, emp["tot"] if emp else "")))
    info = w23["info"]
    jc = w23["jc"]
    K.append(dict(item_id="B-3", item_text=it3, corp_label="우리금융지주", fy="2023", result=NONE,
                  where="B_ext.csv 우리금융지주 FY2023 keyword 전출 행 %d개(퇴직급여 주석 표 칸뿐)" % len(jc),
                  rcept_no_or_url=info["meta"]["rcept_no"], page=info["md"].page(jc[0][0][1]) if jc else "",
                  source_excerpt=jc[0][1][:300] if jc else "",
                  note=("「은행 전출」 글 없음. 찾은 범위: FY2023 사업보고서 본 %s·정정 20240516001472 전체(「전출」은 별도재무제표 퇴직급여 주석 「전출입효과」 표 칸 %d곳뿐), "
                        "연차보고서 FY2023(공시연도 2024 본공시·추가공시 dart_out/text/ops15/연차보고서__우리금융지주__2024__*.md — 「전출」 없음), 경영공시 FY2023(dart_out/text/ops15/경영공시__우리금융지주__FY2023.md — 「전출」 없음)")
                       % (info["meta"]["rcept_no"], len(jc))))
    # NH
    nh = ext_rows("NH농협금융지주", "2012")
    nh_kw = [r for _, r in nh if r["keyword"] not in ("없음",)]
    md = Md(doc_meta("20130329002244")["text_path"])
    allt = "\n".join(md.L[md.body:])
    jj = [m.start() for m in re.finditer(r"전적", allt)]
    pg = [m.start() for m in re.finditer(r"파견", allt)]
    gyeom = [r for r in nh_kw if "원 소속회사" in r["source_text"]]
    K.append(dict(item_id="B-4", item_text=it4, corp_label="NH농협금융지주", fy="2012", result=NONE,
                  where="B_ext.csv NH농협금융지주 FY2012 행(keyword %s)" % dict(Counter(r["keyword"] for r in nh_kw)),
                  rcept_no_or_url="20130329002244", page=gyeom[0]["page"] if gyeom else "",
                  source_excerpt=gyeom[0]["source_text"][:300] if gyeom else "",
                  note=("「전적」「파견」 글(직원 관련) 없음. 찾은 범위: 사업보고서 (2012.12) 20130329002244 전체 — 「파견」 %d곳, 「전적」 %d곳(「전적으로 발행자가 보유」 신종자본증권 표 칸 — 규칙상 뺌), "
                        "「출향」「겸무」 0; 「중앙회」는 연혁·주주·계열회사 서술에만; source_excerpt 는 Ⅷ 집행간부 현황 각주의 겸직 글(원 소속회사 표기)")
                       % (len(pg), len(jj))))
    emp_r = [r for _, r in nh if r["keyword"] == "없음" and r["source_text"].startswith("| 합 계")]
    fn_r = [r for _, r in nh if r["keyword"] == "없음" and r["source_text"].startswith("주1)")]
    K.append(dict(item_id="B-4", item_text=it4, corp_label="NH농협금융지주", fy="2012", result="원문 있음",
                  where="B_ext.csv NH농협금융지주 FY2012 직원 현황 합계 행(keyword 없음)", rcept_no_or_url="20130329002244",
                  page=emp_r[0]["page"] if emp_r else "", source_excerpt=emp_r[0]["source_text"][:300] if emp_r else "",
                  note="평균근속연수 칸 「10개월」(합계 행)·남 10개월·여 9개월 — 숫자만 있음"))
    K.append(dict(item_id="B-4", item_text=it4, corp_label="NH농협금융지주", fy="2012", result=NONE,
                  where="B_ext.csv NH농협금융지주 FY2012 직원 현황 각주 행(keyword 없음)", rcept_no_or_url="20130329002244",
                  page=fn_r[0]["page"] if fn_r else "", source_excerpt=fn_r[0]["source_text"][:300] if fn_r else "",
                  note="평균근속 산정 기준 글 없음 — 표 아래 각주 주1)~주3)(source_excerpt)에 근속 기준 없음(주3 은 급여 기간: 설립일 2012년 3월~12월말); 문서 전체 「근속」은 직원 현황 표 머리와 제재 현황 표뿐"))
    return K


def gap_k(iid, itext, label, fy, gapinfo, exist):
    info = gapinfo.get((label, fy), {})
    if info.get("err"):
        return [dict(item_id=iid, item_text=itext, corp_label=label, fy=fy, result="수집 실패", where="", rcept_no_or_url="",
                     page="", source_excerpt="", note=info["err"])]
    meta, ex, added, emp = info["meta"], info["ex"], info["added"], info["emp"]
    gov = [r for r in exist if r["corp_label"] == label and r["fy"] == fy and r["_file"].startswith("B_gov")]
    kws = Counter(r["keyword"] for r in ex)
    srcs = [r for r in ex if r["source_text"] != NONE and r["keyword"] != "없음"] or [r for r in ex if r["source_text"] != NONE]
    r0 = srcs[0] if srcs else None
    where = "%s %s FY%s 사업보고서 행 %d개(keyword %s, rcept %s)" % ("·".join(sorted({r["_file"] for r in ex})) or "B_bs", label, fy,
                                                               len(ex), dict(kws), meta["rcept_no"])
    if added:
        where += "; B_ext.csv 보충 행 %d개" % len(added)
    if gov:
        where += "; %s 연차보고서 행 %d개(keyword %s)" % ("·".join(sorted({r["_file"] for r in gov})), len(gov),
                                                    dict(Counter(r["keyword"] for r in gov)))
    res = "원문 있음" if (r0 and r0["keyword"] != "없음") or added else ("원문 있음" if r0 else NONE)
    note = "직원 합계 %s(기존 조각 값)" % (ex[0]["employees_total"] if ex else (emp["tot"] if emp else ""))
    if r0 and r0["keyword"] == "없음":
        note += "; 사업보고서 Ⅷ 키워드 글 없음(직원 수 행만)"
    note += "; Ⅷ 키워드 글 %d개를 기존 행과 대조 — 빠진 것 %d개%s" % (len(info["hits"]), len(added), "(B_ext 에 더함)" if added else "")
    return [dict(item_id=iid, item_text=itext, corp_label=label, fy=fy, result=res, where=where,
                 rcept_no_or_url=r0["rcept_no_or_url"] if r0 else meta["rcept_no"], page=r0["page"] if r0 else "",
                 source_excerpt=(r0["source_text"][:300] if r0 else ""), note=note)]


# ================================================================ 작업 C
def build_c():
    INS = re.compile(r"동양생명|ABL생명|에이비엘생명|보험사\s*인수")
    KW = ["인력", "임직원", "조직", "겸직", "파견", "전적", "채용", "내부통제", "준법", "성과평가"]
    cdocs = [d for d in DOCS if d["task"] == "C"]
    groups = defaultdict(list)
    for d in cdocs:
        base = re.sub(r"^\[[^\]]+\]", "", d["report_nm"]).strip()
        groups[(base, d["rcept_dt"][:6] if "분기" not in base else "2025Q1")].append(d)
    rows, K = [], []
    found_rows = []
    approval = None
    for (base, _), ds in sorted(groups.items(), key=lambda x: min(d["rcept_no"] for d in x[1])):
        ds = sorted(ds, key=lambda d: d["rcept_no"])
        main = [d for d in ds if d["kind"] == "본"] or ds
        main = main[0]
        md = Md(main["text_path"])
        un = []
        for i in range(md.body, len(md.L)):
            l = md.L[i]
            if not INS.search(l):
                continue
            segs = re.split(r"<br>|&cr;| \| ", l) if (l.startswith("|") or len(l) > 3000) else [l]
            for s in segs:
                if INS.search(s):
                    un.append((i, s))
        if not un:
            continue   # 동양·ABL 언급 없는 공시(우리투자증권 편입·발행조건확정) — 문서목록에만
        hits = []
        for (i, s) in un:
            for k in KW:
                if (TRUE_JJ.search(s) if k == "전적" else k in s):
                    hits.append((i, s, k))
        for (i, s) in un:
            if "편입 승인" in s and "2025년 5월" in s and approval is None:
                approval = (main, md, i, s)
        others = [d["rcept_no"] for d in ds if d is not main]
        fyd = main["rcept_dt"]
        nm = mdname("C", "우리금융지주", fyd, re.sub(r"[\[\]\s()/]", "", base)[:30])
        add_sec("C", nm, md, un[0][0], "# 우리금융지주 %s %s — 작업 C 추가(동양생명·ABL생명 편입 관련 글 단위)\n\n- 출처: 접수번호 %s · https://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s · 받은 시각 %s · 글 `%s`\n- 아래는 동양생명·ABL생명 언급이 든 절(찾은 범위의 근거)."
                % (fyd, main["report_nm"], main["rcept_no"], main["rcept_no"], main["fetched_at"], main["text_path"]))
        for (i, s) in un[1:]:
            add_sec("C", nm, md, i, "")
        base_r = dict(corp_label="우리금융지주", doc_kind=main["report_nm"], rcept_no=main["rcept_no"], rcept_dt=main["rcept_dt"],
                      doc_name=main["report_nm"], collected_at=main["fetched_at"])
        if hits:
            for (i, s, k) in hits:
                r = dict(base_r)
                r.update(section_title=(md.head_at(i) or (0, 0, ""))[2], keyword=k, source_text=s, page=md.page(i),
                         note="(판단) 11.3 추가 항목 낱말" if k in ("내부통제", "준법", "성과평가") else "")
                rows.append(r)
                found_rows.append(r)
        else:
            r = dict(base_r)
            r.update(section_title="", keyword="", source_text=NONE, page="XML 전체(찾은 범위 — 해당 글 없음)",
                     note=("찾은 범위: 이 공시 전체에서 동양생명·ABL생명(에이비엘생명)·「보험사 인수」 언급 글 단위 %d개(표 칸·<br> 단위)를 보고, "
                           "그 안에서 인력·임직원·조직·겸직·파견·전적·채용·내부통제·준법·성과평가 — 없음; 문서 전체에서 「준법감시 조직」「준법 조직」「내부통제 개선/혁신 계획·방안」"
                           "「성과평가…내부통제」 글도 없음(「내부통제 강화」는 제재 조치·성과급 서술뿐)%s; (판단) 11.3 추가 항목 낱말")
                          % (len(un), ("; 같은 건 정정·관련판 %s 도 같은 범위로 확인 — 없음" % "·".join(others)) if others else ""))
            rows.append(r)
    JUDG.append("C_ext: 동양·ABL 언급이 없는 공시(20240801800172 우리투자증권 편입, 발행조건확정 증권신고서 2건)는 행 없이 문서목록에만")
    it = req_line("추가(11.3): 우리금융 2025.5")
    rng = "OpenDART 목록 우리금융지주(01350869) 접수 2024-08-01~2025-07-31(캐시 dart_out/raw/list/01350869_19990101_20260831_p*.json) — 받은 문서 %d건(문서목록15b_X2.csv)" % len(cdocs)
    if approval:
        main, md, i, s = approval
        p = s.find("2025년 5월")
        K.append(dict(item_id="C-1", item_text=it, corp_label="우리금융지주", fy="2025.5", result="원문 있음",
                      where="(C_ext 행 아님 — 키워드 없는 글) %s %s" % (main["report_nm"], main["rcept_no"]),
                      rcept_no_or_url=main["rcept_no"], page=md.page(i), source_excerpt=excerpt(s, p),
                      note="2025.5 편입 관련 공시 글: 금융위 자회사 편입 승인(2025년 5월) 서술 — 내부통제·준법·성과평가 낱말 없음"))
    for sub in ("준법조직 확대 개편", "자회사 성과평가의 내부통제 평가"):
        K.append(dict(item_id="C-1", item_text=it, corp_label="우리금융지주", fy="2024-08~2025-07", result=NONE,
                      where="C_ext.csv 우리금융지주 「문서에 없음」 행 %d개" % len([r for r in rows if r["source_text"] == NONE]),
                      rcept_no_or_url="", page="", source_excerpt="",
                      note="「%s」 서술 없음. %s; 더 넓혀 사업보고서 FY2024(20250318001196)·FY2025(20260313001235) 전체에서 「준법감시 조직」「준법 조직」「성과평가…내부통제」 — 없음" % (sub, rng)))
    return rows, K


# ================================================================ 작업 E
HEAD_RX = re.compile(r"^\s*(\d+\.|[가-하]\.|\(\d+\)|<[^>]+>)\s*\S")


def e_paras(md):
    """「1. 합병의 목적」 ~ 「2. 합병의 형태」 사이 문단 — (section_title, 문단 글, 첫 줄 i)."""
    s = e = None
    for i in range(md.body, len(md.L)):
        w = nz("".join(md.L[i:i + 4]))
        if s is None and w.startswith("1.합병") and "1.합병의목적" in nz("".join(md.L[i:i + 4]))[:12]:
            s = i
        if s is not None and i > s and nz(md.L[i]).startswith("2.합병의형태"):
            e = i
            break
    out, title, buf, buf_i = [], [], [], None
    # 줄을 이어 하나의 흐름으로 — 표는 건너뜀(표 앞뒤로 문단 끊음)
    seq = []
    for i in range(s, e):
        l = md.L[i]
        if i in md.tab_of or re.match(r"\[표 \d+\]$", l.strip()) or l.strip() == "[표 끝]":
            seq.append((None, i))
            continue
        seq.append((l, i))
    pieces = []   # (글, 첫 줄)
    cur, cur_i = "", None
    for (l, i) in seq:
        if l is None:
            if cur.strip():
                pieces.append((cur, cur_i))
            cur, cur_i = "", None
            continue
        parts = l.split("&cr;")
        for k, p in enumerate(parts):
            if k > 0:   # &cr; = 줄바꿈 표지 → 문단 끊음
                if cur.strip():
                    pieces.append((cur, cur_i))
                cur, cur_i = "", None
            if cur and k == 0:
                prev = cur.rstrip()
                if (HEAD_RX.match(p) or p.lstrip().startswith("- ")) and re.search(r"(다\.|다\. |음\.|함\.)\s*$", prev + " "):
                    pieces.append((cur, cur_i))
                    cur, cur_i = "", None
            if p.strip() or cur:
                if cur_i is None:
                    cur_i = i
                cur = cur + ("\n" if cur and k == 0 else "") + p
    if cur.strip():
        pieces.append((cur, cur_i))
    for (t, i) in pieces:
        st = t.strip()
        if not st:
            continue
        if re.fullmatch(r"\d+", st) or re.fullmatch(r".*\.(jpg|png|gif)", st):
            out.append(("skip", st, i))
            continue
        if (HEAD_RX.match(st) or st.startswith("<")) and len(st) < 60 and not re.search(r"다\.\s*$", st):
            lvl = 0 if re.match(r"^\s*\d+\.", st) else (1 if re.match(r"^\s*[가-하]\.", st) else 2)
            title = title[:lvl] + [re.sub(r"\s+", " ", st)]
            continue
        if not title and re.fullmatch(r"1\.\s*합\s*병\s*의\s*목\s*적", re.sub(r"\n", "", st)):
            title = ["1. 합병의 목적"]
            continue
        if nz(st) in ("합병조직",):
            out.append(("skip", st, i))
            continue
        out.append((" > ".join(title), t.strip("\n"), i))
    return out


def build_e():
    rows, K = [], []
    rc_main = {"20140514005150": "한국씨티금융지주", "20150507001778": "한국SC금융지주"}
    filer = {"20140514005150": "주식회사 한국씨티은행", "20150507001778": "주식회사 한국스탠다드차타드은행"}
    paras_by = {}
    for rc, label in rc_main.items():
        meta = doc_meta(rc)
        md = Md(meta["text_path"])
        ps = e_paras(md)
        others = [d for d in DOCS if d["task"] == "E" and d["doc_kind"] == "주요사항보고서" and d["label"] == label and d["rcept_no"] != rc]
        otext = {}
        for d in others:
            if d["text_path"]:
                otext[d["rcept_no"]] = (d, nzx(open(d["text_path"], encoding="utf-8").read()))
        skipped = [p for p in ps if p[0] == "skip"]
        n = 0
        for (title, t, i) in ps:
            if title == "skip":
                continue
            n += 1
            same = [r for r, (d, x) in otext.items() if nzx(t) in x]
            diff = [r for r, (d, x) in otext.items() if nzx(t) not in x]
            miss = [d["rcept_no"] for d in others if not d["text_path"]]
            note = ["제출인 %s(표지 「회사명」) — 합병 존속회사; %s 는 소멸(해산) 회사" % (filer[rc], label),
                    "문단 %d — (판단) 문단 나누기: XML 줄바꿈 표지 &cr; 와 새 문단 머리(가./(1)/- 등) 기준" % n]
            if same:
                note.append("같은 문단 있음: %s" % "·".join(same))
            if diff:
                note.append("이 문단 글이 다름(번호·괄호·낱말 차이 등): %s" % "·".join(diff))
            if miss:
                note.append("정정판 %s 는 OpenDART 014(파일 없음) — 대조 못함" % "·".join(miss))
            if "합병조직" in "".join(s for _, s, _ in skipped) and "다. 향후" in title:
                note.append("이 절에 그림 이름 「합병조직.jpg」만 있음(XML 에 그림 없음)")
            rows.append(dict(corp_label=label, doc_kind="주요사항보고서(합병결정)", rcept_no=rc, rcept_dt=meta["rcept_dt"],
                             section_title="Ⅱ. 보고 내용 > " + title, source_text=t, page=md.page(i), note="; ".join(note),
                             doc_name=(meta["report_nm"] or "주요사항보고서(합병결정)") + " — " + filer[rc].replace("주식회사 ", "(주)") + " 제출",
                             collected_at=meta["fetched_at"]))
            add_sec("E", mdname("E", label, meta["rcept_dt"], "주요사항보고서합병결정"), md, i,
                    "# %s %s 주요사항보고서(합병결정) — 작업 E 합병 목적·배경 절\n\n- 출처: 접수번호 %s(제출인 %s) · https://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s · 받은 시각 %s · 글 `%s`"
                    % (label, meta["rcept_dt"], rc, filer[rc], rc, meta["fetched_at"], meta["text_path"]))
        paras_by[rc] = [r for r in rows if r["rcept_no"] == rc]
    JUDG.append("E: 문단 나누기(XML &cr; 표지·새 문단 머리), 제목 줄은 section_title 로 — 「1. 합병의 목적」 절(가·나·다) 전체를 합병 목적·배경으로 봄")
    # ---------- FY2013 사업보고서 겸직 표
    for label in ("한국씨티금융지주", "한국SC금융지주"):
        ds = [d for d in DOCS if d["task"] == "E" and d["doc_kind"] == "사업보고서" and d["label"] == label]
        main = [d for d in ds if d["kind"] == "본"][0]
        cors = [d for d in ds if d["kind"] != "본"]
        md = Md(main["text_path"])
        ctext = {c["rcept_no"]: nzx(open(c["text_path"], encoding="utf-8").read()) for c in cors if c["text_path"]}
        tbl = None
        for t in md.tables:
            if t["rows"] and "겸직" in nz(" ".join(t["rows"][0][1])) and "성명" in nz(t["rows"][0][1][0]):
                tbl = t
                break
        assert tbl, label
        cap_i = max(i for i in range(tbl["s"] - 6, tbl["s"]) if "겸직" in nz(md.L[i]))
        cap = re.sub(r"&cr;", "", md.L[cap_i]).strip()
        hdr = md.L[tbl["rows"][0][0]]
        ncol = len(tbl["rows"][0][1])
        person = ""
        nm = mdname("E", label, "FY2013", "사업보고서")
        head = ("# %s FY2013 사업보고서 — 작업 E 임원 겸직 표가 나온 절\n\n- 출처: %s · 접수번호 %s · https://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s · 받은 시각 %s · 글 `%s`"
                % (label, main["report_nm"], main["rcept_no"], main["rcept_no"], main["fetched_at"], main["text_path"]))
        for (i, c) in tbl["rows"][1:]:
            note = []
            if len(c) == ncol:
                person = c[0]
            else:
                note.append("(판단) 칸 합침(rowspan) — 칸 %d개(머리 %d개): 앞 행 성명 「%s」의 이어지는 행으로 봄" % (len(c), ncol, person))
                JUDG.append("E: %s FY2013 겸직 표 칸 합침 행의 성명을 앞 행에서 이어 봄" % label)
            note.append("표 머리 「%s」; 표 제목 「%s」; (위치) Ⅵ. 이사회 등 회사의 기관 및 계열회사에 관한 사항 > 4. 계열회사 등의 현황 — Ⅷ 에는 겸직 표 없음(Ⅷ 은 임원 현황 표)" % (hdr, cap))
            for rc, x in ctext.items():
                note.append("정정 %s: %s" % (rc, "같은 행 있음" if nzx(md.L[i]) in x else "이 행 없음(바뀜)"))
            rows.append(dict(corp_label=label, doc_kind="사업보고서", rcept_no=main["rcept_no"], rcept_dt=main["rcept_dt"],
                             section_title=cap, source_text=md.L[i], page=md.page(i), note="; ".join(note),
                             doc_name=main["report_nm"], collected_at=main["fetched_at"]))
            add_sec("E", nm, md, i, head)
        # 표 아래 주(작성기준일 이후 변동) — 다음 표·제목 전까지
        j = tbl["e"] + 1
        k = j
        while k < len(md.L) and not md.L[k].startswith("### ") and not re.match(r"\[표 \d+\]$", md.L[k].strip()) \
                and not re.match(r"^\s*[가-하]\.\s", md.L[k]):
            k += 1
        foot = "\n".join(md.L[j:k]).strip("\n")
        if nz(re.sub(r"&cr;", "", foot)):
            rows.append(dict(corp_label=label, doc_kind="사업보고서", rcept_no=main["rcept_no"], rcept_dt=main["rcept_dt"],
                             section_title=cap + " — 표 아래 주", source_text=foot, page=md.page(j),
                             note="겸직 표 바로 아래 글(md 줄 %d~%d, 줄바꿈 그대로)" % (j + 1, k),
                             doc_name=main["report_nm"], collected_at=main["fetched_at"]))
        # 문서 안 다른 「겸직」 글
        for u in units(md, md.body, len(md.L)):
            if tbl["s"] <= u[1] <= k or not ("겸직" in nz(utext(md, u))):
                continue
            t = utext(md, u)
            ch = md.chap_at(u[1])
            rows.append(dict(corp_label=label, doc_kind="사업보고서", rcept_no=main["rcept_no"], rcept_dt=main["rcept_dt"],
                             section_title=(ch[2] if ch else "") + " > " + (md.head_at(u[1])[2] if md.head_at(u[1]) else ""),
                             source_text=t, page=md.page(u[1]),
                             note="(판단) 겸직 표 밖의 「겸직」 글 — 같은 문서에서 참고로 넣음(%s)" % ("표 행" if u[0] == "row" else "글"),
                             doc_name=main["report_nm"], collected_at=main["fetched_at"]))
            add_sec("E", nm, md, u[1], head)
        JUDG.append("E: FY2013 사업보고서 겸직 표 밖 「겸직」 글 줄도 참고 행으로 넣음")
    # ---------- 확인_E: 6가지 × 2건
    it = req_line("뽑을 것: 합병 목적·배경 문단 전문")
    pats = [("지주 존립 의의", r"존립", r"실익"),
            ("지주 유지 비용", r"비용의 추가 지출|지주회사 유지에 따른[^.]*비용", None),
            ("추가 보고 건수", r"추가보고건수|추가\s*보고\s*건수", None),
            ("업무위탁 부가세", r"부가가치세", None),
            ("감사 중복", r"감사업무중복|감사\s*업무\s*중복", None),
            ("해외 본사·지역본부 관리", r"해외\s*본사", None)]
    for rc, label in rc_main.items():
        prs = paras_by[rc]
        for n, (name, rx, alt) in enumerate(pats, 1):
            hit = None
            for idx, r in enumerate(prs):
                m = re.search(rx, r["source_text"])
                if m:
                    hit = (idx, r, m, False)
                    break
            if not hit and alt:
                for idx, r in enumerate(prs):
                    m = re.search(alt, r["source_text"])
                    if m:
                        hit = (idx, r, m, True)
                        break
            if hit:
                idx, r, m, isalt = hit
                note = "문단 %d(section 「%s」)" % (idx + 1, r["section_title"])
                if isalt:
                    note += "; (판단) 「존립」 낱말은 없고 「지주회사 체제를 유지할 실익」 글을 이 항목으로 봄"
                    JUDG.append("확인_E: %s 「존립 의의」 — 「실익」 글로 봄" % label)
                K.append(dict(item_id="E-%d %s" % (n, name), item_text=it, corp_label=label, fy=r["rcept_dt"], result="원문 있음",
                              where="E.csv %s %s 문단 %d" % (label, rc, idx + 1), rcept_no_or_url=rc, page=r["page"],
                              source_excerpt=excerpt(r["source_text"], m.start()), note=note))
            else:
                extra = ""
                if name == "추가 보고 건수":
                    for idx, r in enumerate(prs):
                        m = re.search(r"보고\s*업무\s*부담|보고 등을 위한 서류작업", r["source_text"])
                        if m:
                            extra = "; 보고 부담 글은 있음(건수 숫자 없음): 문단 %d 「%s」" % (idx + 1, excerpt(r["source_text"], m.start())[:120])
                            break
                K.append(dict(item_id="E-%d %s" % (n, name), item_text=it, corp_label=label, fy=prs[0]["rcept_dt"], result=NONE,
                              where="E.csv %s %s 문단 1~%d" % (label, rc, len(prs)), rcept_no_or_url=rc, page="", source_excerpt="",
                              note="찾은 범위: 이 보고서 「1. 합병의 목적」 절 전체 문단(검색어 %s)%s" % (rx, extra)))
    return rows, K


# ================================================================ 문서목록
def build_list():
    out = []
    for d in DOCS:
        st = {"000": "받음", "014": "014"}.get(d["doc_status"], "실패")
        note = ["작업 %s" % d["task"], "구분 %s" % d["kind"], "목록 %s" % (d.get("list_raw") or "(접수번호 지정)")]
        if d["task"] == "C" and d["rcept_no"] == "20240801800172":
            note.append("(판단) 보고서명 「편입」으로 받았으나 본문의 편입 회사는 우리투자증권 — 동양·ABL 아님, 행 없음")
        if d["task"] == "C" and "발행조건확정" in d["report_nm"]:
            note.append("본문에 동양·ABL 언급 없음 — 행 없음")
        if d.get("filer"):
            note.append("제출인 %s" % d["filer"])
        if d["doc_status"] == "014":
            note.append("OpenDART 014 파일 없음")
        out.append(dict(doc_kind=d["doc_kind"] if d["doc_kind"] != "공시" else "공시(우리 2024-08~2025-07)", corp_label=d["label"],
                        fy_or_date=("FY" + d["fy"]) if d["doc_kind"] == "사업보고서" else d["rcept_dt"], report_nm=d["report_nm"],
                        rcept_no_or_url=d["rcept_no"], rcept_dt=d["rcept_dt"], raw_path=d["raw_path"], sha256=d["raw_sha256"],
                        fetched_at=d["fetched_at"], text_path=d["text_path"], status=st, note="; ".join(note)))
    for g in csv.DictReader(open(OPS + "/문서목록15b_gov_old.csv", encoding="utf-8-sig")):
        if g["corp_label"] == "KB금융지주" and g["fy_or_date"] in ("FY2014", "FY2016", "FY2017"):
            out.append(dict(doc_kind="지배구조 연차보고서", corp_label="KB금융지주", fy_or_date=g["fy_or_date"], report_nm=g["report_nm"],
                            rcept_no_or_url=g["rcept_no_or_url"], rcept_dt=g["rcept_dt"], raw_path=g["raw_path"], sha256=g["sha256"],
                            fetched_at=g["fetched_at"], text_path=g["text_path"], status=g["status"],
                            note="gov_old 가 받은 것을 읽기만(dart_out/ops15/문서목록15b_gov_old.csv) — 작업 B 연차보고서 키워드"))
    for (label, fy) in [("KB금융지주", "2023"), ("KB금융지주", "2024"), ("신한금융지주", "2022"), ("신한금융지주", "2023"), ("신한금융지주", "2024"),
                        ("하나금융지주", "2022"), ("하나금융지주", "2023"), ("하나금융지주", "2024"), ("BNK금융지주", "2022"), ("BNK금융지주", "2023"),
                        ("BNK금융지주", "2024"), ("iM금융지주", "2019"), ("iM금융지주", "2020"), ("iM금융지주", "2023"), ("iM금융지주", "2024"),
                        ("우리금융지주", "2022"), ("우리금융지주", "2023")]:
        for r in BR.values():
            if r["label"] == label and r["fy"] == fy and r["kind"] == "본":
                out.append(dict(doc_kind="사업보고서", corp_label=label, fy_or_date="FY" + fy, report_nm=r["report_nm"], rcept_no_or_url=r["rcept_no"],
                                rcept_dt=r["rcept_dt"], raw_path=r["raw_path"], sha256=r["raw_sha256"], fetched_at=r["fetched_at"],
                                text_path=r["text_path"], status="받음",
                                note="기존 글 재사용(dart_out/ops15/사업보고서_원문.csv) — 확인_B_ext 대조·보충용"))
    L = json.load(open(RAWX + "/lists.json", encoding="utf-8"))
    for lab in L:
        out.append(dict(doc_kind="공시목록(list.json)", corp_label=lab, fy_or_date="", report_nm="OpenDART list.json 캐시 묶음",
                        rcept_no_or_url="", rcept_dt="", raw_path=" · ".join(sorted({x["list_raw"].rsplit("_p", 1)[0] for x in L[lab]}))[:500],
                        sha256="", fetched_at="", text_path=RAWX + "/lists.json", status="받음", note="목록 %d건" % len(L[lab])))
    return out


def main():
    b_rows, gapinfo, woori, exist = build_b()
    write_csv(FRAG + "/B_ext.csv", b_rows, B_COLS)
    kb = build_kb(b_rows, gapinfo, woori, exist)
    write_csv(FRAG + "/확인_B_ext.csv", kb, K_COLS)
    print("B_ext", len(b_rows), Counter(r["keyword"] for r in b_rows), "확인", len(kb), Counter(r["result"] for r in kb))
    c_rows, kc = build_c()
    write_csv(FRAG + "/C_ext.csv", c_rows, C_COLS)
    write_csv(FRAG + "/확인_C_ext.csv", kc, K_COLS)
    print("C_ext", len(c_rows), "확인", len(kc), Counter(r["result"] for r in kc))
    e_rows, ke = build_e()
    write_csv(FRAG + "/E.csv", e_rows, E_COLS)
    write_csv(FRAG + "/확인_E.csv", ke, K_COLS)
    print("E", len(e_rows), Counter(r["rcept_no"] for r in e_rows), "확인", len(ke), Counter(r["result"] for r in ke))
    made = write_secs()
    json.dump({p: True for p in made}, open(MINE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    write_csv(OPS + "/문서목록15b_X2.csv", build_list(), L_COLS)
    json.dump(sorted(set(JUDG)), open(RAWX + "/judgments.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("원문 md", len(made))
    for j in sorted(set(JUDG)):
        print("판단:", j)


if __name__ == "__main__":
    main()
