#!/usr/bin/env python3
"""14차 그룹 g4(iM금융지주·NH농협금융지주) 검증 — 인자 없이 실행, 결과 dart_out/org14/verify14_g4.txt, exit 0/1.

검사:
 Q  md 인용 코드 블록(인용 Qnn) ↔ 텍스트 파일 줄 범위(공백 무시) + 쪽 표지(=== p.N ===) + 쪽 꼬리(Page M)
 P  md·CSV 의 출처 표기 「p.N(쪽 꼬리 Page M) · … a~b행」 ↔ 텍스트 쪽 표지·쪽 꼬리
 F  md·CSV(조직단위·임원겸직·지원조직·판독대조)의 「…」 조각 ↔ 회사 텍스트(본·정정·연차 본/추가·경영공시, 공백 무시).
    원문이 아닌 조각(칸 이름·표지 낱말·판독 이름·찾은 방법의 검색어·문서 제목)은 따로 셈
 T  임원겸직 CSV 원문 칸(성명·직위·등기·상근·담당업무 / 겸직회사·직위·선임일·상근여부) ↔ 인용한 줄 근처 텍스트
 S  지원조직 CSV 원문 칸(부서명·직원수·직위·주요 활동) ↔ 인용한 줄 범위
 M  CSV ↔ md 같은 값(1-2·보조 판독 표, 3-4 공시인원 표, 4 임원 표, 5 겸직 표, 3-1 지원조직 표)
 R  판독대조 CSV: 판독B·확정·확정 방법 빈칸 없음, 확정 = 조직단위 CSV, 판독B.json 이름과 같음(공백 무시),
    연차 p.11 글자층 단위 이름 = 텍스트 p.11 줄
 C  iM 조직도 머리 집계 글 ↔ 확정 단위 층위 수(알려진 차이: 팀 머리 2 ↔ 상자 3 — 그 밖 차이는 실패)
 N  「이름 일치」 대응: 단위 이름이 담당업무(대표이사는 직위 포함) 원문에 글자 그대로 있는지(공백만 다르면 실패)
 H  md 0) 머리 sha256 ↔ 원본 PDF·ZIP(로컬)
 K  키·OC 값 없음, 산출 폴더(handoff/14차_조직인원겸직, dart_out/org14)에 PDF·PNG 없음
로컬 파일만 읽음(웹 요청 없음).
"""
import csv, hashlib, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TXT = os.path.join(ROOT, "dart_out", "text", "risk8")
ORG = os.path.join(ROOT, "dart_out", "org14")
HND = os.path.join(ROOT, "handoff", "14차_조직인원겸직")
OUT = os.path.join(ORG, "verify14_g4.txt")

COS = {
    "iM금융지주": {
        "texts": {
            "사업보고서": "사업보고서__iM금융지주__20260318000971.txt",
            "사업보고서정정": "사업보고서__iM금융지주__20260515000720.txt",
            "연차보고서": "연차보고서__iM금융지주_지배구조연차보고서_2026.txt",
            "연차보고서추가": "연차보고서__iM금융지주_지배구조연차보고서_2026_추가공시.txt",
            "경영공시": "경영공시__iM금융지주.txt",
        },
        "rcp": {"20260318000971": "사업보고서", "20260515000720": "사업보고서정정"},
        "src": ["dart_out/raw/risk8/경영공시/iM금융지주/iM금융지주_경영공시_2026_2Q.pdf",
                "dart_out/raw/governance/iM금융지주/iM금융지주_지배구조연차보고서_2026.pdf",
                "dart_out/raw/governance/iM금융지주/iM금융지주_지배구조연차보고서_2026_추가공시.pdf",
                "dart_out/raw/document/20260318000971.zip", "dart_out/raw/document/20260515000720.zip",
                "dart_out/doc/20260318000971/본문.pdf", "dart_out/doc/20260515000720/본문.pdf"],
    },
    "NH농협금융지주": {
        "texts": {
            "사업보고서": "사업보고서__NH농협금융지주__20260331004252.txt",
            "연차보고서": "연차보고서__NH농협금융지주_지배구조연차보고서_2026.txt",
            "연차보고서추가": "연차보고서__NH농협금융지주_지배구조연차보고서_2026_추가공시.txt",
            "경영공시": "경영공시__NH농협금융지주.txt",
        },
        "rcp": {"20260331004252": "사업보고서"},
        "src": ["dart_out/raw/risk8/경영공시/NH농협금융지주/NH농협금융지주_경영공시_2026_2Q.pdf",
                "dart_out/raw/governance/NH농협금융지주/NH농협금융지주_지배구조연차보고서_2026.pdf",
                "dart_out/raw/governance/NH농협금융지주/NH농협금융지주_지배구조연차보고서_2026_추가공시.pdf",
                "dart_out/raw/document/20260331004252.zip", "dart_out/doc/20260331004252/본문.pdf"],
    },
}

probs, notes = [], []
stat = {}

# 「」 안 낱말 중 원문 인용이 아닌 것(칸 이름·표지 낱말·판단 낱말·검증 기록 낱말)
TERMS = {"원본 수집", "추출 범위에 없음", "글자층", "(겸)", "공시인원", "이름 일치", "(판단)", "판독", "나오지 않음", "인원_내역",
         "=== p.N ===", "단위_층위", "판독_대조", "판독 B 전(검증 에이전트가 채움)", "판독 A ↔ 판독 B", "N부문 N부", "4부문 8담당…",
         "B 판독에 없음", "다름", "같음", "A=B 같음", "층위 낱말 대조", "(판독)", "판독B", "확정", "확정 방법", "(은행 원적)",
         "겸", "겸직", "원적", "ㄴ", "Page M", "p.N(쪽 꼬리 Page M) · … a~b행", "B_저장_뒤_다시_본_곳", "(보조 annual_chart p.11)",
         "(보조 annual_chart p.19)", "(보조 annual_chart p.7)", "다름: …", "A=B 같음(…)", "지주<겸직>"}
META = ["dart_out/risk8/연차보고서_FY2025.csv", "dart_out/risk8/경영공시_2026_2Q.csv", "dart_out/risk8/DART_문서목록.csv"]


def ws(s):
    return re.sub(r"\s+", "", s or "")


def dot(s):
    return (s or "").replace("ㆍ", "·").replace("・", "·").replace("‧", "·").replace("∙", "·")


def nl(s):
    """md 칸의 ⏎·<br> 를 줄바꿈으로."""
    return (s or "").replace(" ⏎ ", "\n").replace("⏎", "\n").replace("<br>", "\n")


class Text:
    def __init__(self, path):
        self.path = path
        self.lines = open(path, encoding="utf-8").read().split("\n")
        self.page = [0] * (len(self.lines) + 2)
        self.pagelines = {}
        pg = 0
        for i, ln in enumerate(self.lines, 1):
            m = re.match(r"^=== p\.(\d+) ===\s*$", ln)
            if m:
                pg = int(m.group(1))
            self.page[i] = pg
            self.pagelines.setdefault(pg, []).append(ln)
        self.full = ws("\n".join(self.lines))
        self.fulldot = dot(self.full)
        self.pagews = {p: ws("\n".join(v)) for p, v in self.pagelines.items()}

    def rng(self, a, b):
        return ws("\n".join(self.lines[max(a, 1) - 1:min(b, len(self.lines))]))


def load_csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def frags(s):
    return re.findall(r"「([^「」]+)」", s or "")


def md_tables(lines, header_start):
    out = []
    for i, ln in enumerate(lines):
        if ln.startswith(header_start):
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = [c.strip() for c in lines[j].strip()[1:-1].split(" | ")]
                out.append((j + 1, cells))
                j += 1
    return out


CIT = re.compile(r"p\.(\d+)(?:~(\d+))?(?:\(쪽 꼬리 Page (\d+)(?:~(\d+))?\))?((?:(?!p\.\d)[^\]|‖\n])*?)(?<![\d.])(\d+)(?:~(\d+))?행")


def check_company(co, cfg):
    st = {k: 0 for k in ("quotes", "quote_pages", "pageline", "pageline_tail", "frag_ok", "frag_term", "frag_title", "frag_pandok",
                         "frag_search", "frag_bad", "exec_cells", "concur_rows", "support_cells", "md_rows", "cmp_rows",
                         "cmp_unit_rows", "name_match", "p11_rows")}
    T = {k: Text(os.path.join(TXT, v)) for k, v in cfg["texts"].items()}
    path2T = {os.path.join("dart_out/text/risk8", v): T[k] for k, v in cfg["texts"].items()}
    tag = co[:2]
    md_path = os.path.join(HND, f"14_{co}.md")
    md = open(md_path, encoding="utf-8").read().split("\n")
    units = load_csv(os.path.join(ORG, f"{co}_조직단위.csv"))
    execs = load_csv(os.path.join(ORG, f"{co}_임원겸직.csv"))
    sup = load_csv(os.path.join(ORG, f"{co}_지원조직.csv"))
    cmpr = load_csv(os.path.join(ORG, f"{co}_판독대조.csv"))
    A = json.load(open(os.path.join(ORG, f"{co}_판독A.json"), encoding="utf-8"))
    B = json.load(open(os.path.join(ORG, f"{co}_판독B.json"), encoding="utf-8"))
    C_UNIT = [c for c in units[0] if c.startswith("공시인원")][0]
    C_KJ = [c for c in units[0] if c.startswith("조직도_겸직표시")][0]
    C_HOW = [c for c in units[0] if c.startswith("대응_방식")][0]
    C_EXK = [c for c in units[0] if c.startswith("임원_겸직")][0]

    def doc_T(seg):
        m = re.search(r"(dart_out/text/risk8/\S+?\.txt)", seg)
        if m and m.group(1) in path2T:
            return path2T[m.group(1)]
        for r, k in cfg["rcp"].items():
            if r in seg:
                return T[k]
        best, pos = None, -1
        for key, kw in (("사업보고서", "사업보고서"), ("연차보고서", "연차보고서"), ("경영공시", "경영공시")):
            k = seg.rfind(kw)
            if k > pos:
                best, pos = key, k
        if best == "연차보고서" and "추가" in seg[pos:]:
            best = "연차보고서추가"
        if best is None and "추가공시" in seg:
            best = "연차보고서추가"
        return T.get(best)

    # 판독 이름 모음
    pandok = set()
    for u in A["units"]:
        pandok |= {ws(dot(u["조직단위"])), ws(dot(u["상위단위"])), ws(dot(u["상자글"]).replace("⏎", ""))}
    for b in A.get("보조_조직도", []):
        for u in b.get("units", []):
            pandok |= {ws(dot(u["조직단위"])), ws(dot(u["상위단위"])), ws(dot(u.get("상자글", "")).replace("⏎", ""))}
    for ch in B["조직도"]:
        if isinstance(ch["단위"], list):
            for u in ch["단위"]:
                pandok |= {ws(dot(u["조직단위"])), ws(dot(u["상위단위"]))}
        pandok.add(ws(dot(ch.get("머리_집계글_판독", ""))))
    for r in units:
        pandok |= {ws(dot(re.sub(r"〔[^〕]*〕", "", r["조직단위(판독)"]))), ws(dot(r["상위단위(판독)"])), ws(dot(r[C_KJ]))}
    for m in A.get("머리", []):
        pandok.add(ws(dot(m["판독A"])))
    pandok |= {x.replace("/", "") for x in list(pandok)}
    pandok.discard("")
    meta = ""
    for mp in META:
        mpp = os.path.join(ROOT, mp)
        if os.path.exists(mpp):
            meta += ws(open(mpp, encoding="utf-8-sig").read())

    def in_texts(f):
        w = ws(f)
        wd = ws(dot(f))
        return any(w in t.full or wd in t.fulldot for t in T.values())

    def frag_status(f, ctx):
        w = ws(f)
        if not w:
            return "ok"
        if in_texts(f):
            return "ok"
        if "…" in f:
            parts = [ws(dot(x)) for x in f.split("…") if ws(x)]
            for t in T.values():
                pos, okp = 0, True
                for x in parts:
                    k = t.fulldot.find(x, pos)
                    if k < 0:
                        okp = False
                        break
                    pos = k + len(x)
                if okp:
                    return "ok"
        if f.strip() in TERMS:
            return "term"
        if w in meta:
            return "title"
        wd = ws(dot(f)).replace("⏎", "").replace("/", "")
        if wd in pandok or any(wd == p + "장" or wd.startswith(p + "(") for p in pandok) or (len(wd) >= 2 and any(wd in p for p in pandok)):
            return "pandok"
        if any(k in ctx for k in ("찾은 방법", "검색", "검색어", "낱말")):
            return "search"
        return "bad"

    # ── H: md 머리 sha256 ↔ 원본 파일(로컬, git 무시 폴더)
    mdtext = "\n".join(md)
    for sp in cfg.get("src", []):
        fp = os.path.join(ROOT, sp)
        if not os.path.exists(fp):
            notes.append((tag, "sha256", "원본 없음", sp))
            continue
        h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
        st["sha256"] = st.get("sha256", 0) + 1
        if h not in mdtext:
            probs.append((tag, "md 0) 머리 sha256", f"{sp} 의 sha256 {h[:16]}… 가 md 에 없음"))

    # ── Q: md 인용 코드 블록
    hdr_re = re.compile(r"^\[(.*) · (dart_out/text/risk8/\S+?\.txt) (\d+)~(\d+)행\]\s*$")
    quote_hdr_lines = set()
    for i, ln in enumerate(md):
        m = hdr_re.match(ln)
        if not m or i == 0 or not md[i - 1].startswith("**인용 Q"):
            continue
        quote_hdr_lines.add(i)
        q = re.match(r"\*\*인용 (Q\d+[a-z]*v?)\*\*", md[i - 1]).group(1)
        pre, tp, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        if tp not in path2T:
            probs.append((tag, f"md {i+1}줄 {q}", f"텍스트 파일 {tp} 가 회사 목록에 없음"))
            continue
        t = path2T[tp]
        j = i + 1
        while j < len(md) and not md[j].startswith("```"):
            j += 1
        k = j + 1
        while k < len(md) and not md[k].startswith("```"):
            k += 1
        block = "\n".join(md[j + 1:k])
        st["quotes"] += 1
        if ws(block) != t.rng(a, b):
            probs.append((tag, f"md {i+1}줄 {q}", f"코드 블록이 {tp} 줄 {a}–{b} 와 다름(공백 무시)"))
        pm = list(re.finditer(r"p\.(\d+)(?:~(\d+))?(?:\(쪽 꼬리 Page (\d+)(?:~(\d+))?\))?", pre))
        if not pm:
            probs.append((tag, f"md {i+1}줄 {q}", "쪽 표기 없음"))
            continue
        g = pm[-1]
        p1 = int(g.group(1)); p2 = int(g.group(2) or p1)
        st["quote_pages"] += 1
        if t.page[a] != p1 or not (p1 <= t.page[b] <= p2):
            probs.append((tag, f"md {i+1}줄 {q}", f"쪽 표기 p.{p1}{'~'+str(p2) if p2 != p1 else ''} ↔ 텍스트 줄 {a} p.{t.page[a]}, 줄 {b} p.{t.page[b]}"))
        if g.group(3):
            for pg, tail in ((p1, g.group(3)), (p2, g.group(4))):
                if tail and ("Page" + tail) not in t.pagews.get(pg, ""):
                    probs.append((tag, f"md {i+1}줄 {q}", f"쪽 꼬리 Page {tail} 가 p.{pg} 글에 없음"))

    # ── P: 출처 표기
    def pageline(text, where):
        for seg in re.split(r"\n|‖|\]\s*;|\] ⏎ ", text):
            for m in CIT.finditer(seg):
                t = doc_T(seg)
                if t is None:
                    probs.append((tag, where, f"출처 「{m.group(0)[:50]}」 의 문서를 못 가림"))
                    continue
                p1 = int(m.group(1)); p2 = int(m.group(2) or p1)
                a = int(m.group(6)); b = int(m.group(7) or a)
                st["pageline"] += 1
                if a >= len(t.page) or b >= len(t.page):
                    probs.append((tag, where, f"줄 {a}~{b} 가 {os.path.basename(t.path)} 밖"))
                    continue
                if t.page[a] != p1 or not (p1 <= t.page[b] <= max(p2, p1 + 1)):
                    probs.append((tag, where, f"p.{p1} · {a}~{b}행 ↔ {os.path.basename(t.path)} 줄 {a} p.{t.page[a]}, 줄 {b} p.{t.page[b]}"))
                if m.group(3):
                    st["pageline_tail"] += 1
                    if ("Page" + m.group(3)) not in t.pagews.get(p1, ""):
                        probs.append((tag, where, f"쪽 꼬리 Page {m.group(3)} 가 {os.path.basename(t.path)} p.{p1} 에 없음"))

    inb = False
    for i, ln in enumerate(md):
        if ln.startswith("```"):
            inb = not inb
            continue
        if not inb:
            pageline(ln, f"md {i+1}줄")
    for fname, rows_ in (("조직단위", units), ("지원조직", sup), ("임원겸직", execs)):
        for n, r in enumerate(rows_, 2):
            for col, v in r.items():
                if v and "행" in v and "p." in v:
                    pageline(v, f"{fname} CSV {n}행 {col}")

    # ── F: 「」 조각
    inblock = False
    sec7 = False
    for i, ln in enumerate(md):
        if ln.startswith("```"):
            inblock = not inblock
            continue
        if inblock:
            continue
        for f in frags(ln):
            s = frag_status(f, ln)
            if s == "bad" and "|" in f:
                s = "search"
            st["frag_" + s] += 1
            if s not in ("ok", "bad"):
                notes.append((tag, f"md {i+1}줄", s, f[:70]))
            if s == "bad":
                probs.append((tag, f"md {i+1}줄", f"「{f[:60]}」 가 회사 텍스트(공백 무시)·판독 이름에 없음"))
    for fname, rows_, cols in (("조직단위", units, None), ("임원겸직", execs, None), ("지원조직", sup, None),
                               ("판독대조", cmpr, ["확정 방법(확대 그림 파일·dpi·clip)"])):
        for n, r in enumerate(rows_, 2):
            for col, v in r.items():
                if cols and col not in cols:
                    continue
                for f in frags(v):
                    s = frag_status(f, v)
                    if s == "bad" and "|" in f:
                        s = "search"
                    st["frag_" + s] += 1
                    if s not in ("ok", "bad"):
                        notes.append((tag, f"{fname} CSV {n}행 {col}", s, f[:70]))
                    if s == "bad":
                        probs.append((tag, f"{fname} CSV {n}행 {col}", f"「{f[:60]}」 가 텍스트에 없음"))

    # ── T: 임원겸직 CSV
    tabkey = {}
    for n, r in enumerate(execs, 2):
        src = r["출처"]
        parts = src.split("‖")
        main_src = [x for x in parts if not x.strip().startswith("겸직:")]
        conc_src = [x for x in parts if x.strip().startswith("겸직:")]
        if main_src:
            m = re.search(r"p\.(\d+)\(쪽 꼬리 Page \d+\) · (\d+)행", main_src[0])
            t = doc_T(main_src[0])
            if not m or t is None:
                probs.append((tag, f"임원겸직 CSV {n}행", "임원 표 출처 「p.N(쪽 꼬리 Page M) · L행」 못 읽음"))
            else:
                p, l = int(m.group(1)), int(m.group(2))
                win = t.rng(l - 2, l + 40)
                for col in ("성명", "직위", "등기", "상근", "담당업무(원문)"):
                    v = r[col]
                    if not v or v.startswith(("추출 범위에 없음", "나오지 않음")):
                        continue
                    st["exec_cells"] += 1
                    if ws(v) not in win:
                        probs.append((tag, f"임원겸직 CSV {n}행 {col}", f"「{v[:50]}」 가 p.{p} 줄 {l} 근처에 없음"))
                # 성명~담당업무가 한 줄 묶음으로 이어지는지(같은 행 칸)
                seq = ws(r["성명"])
                if seq and seq not in t.rng(l, l + 1):
                    probs.append((tag, f"임원겸직 CSV {n}행", f"성명 {r['성명']} 이 줄 {l} 에 없음"))
        if conc_src and r["겸직회사"] and not r["겸직회사"].startswith(("겸직 표에 나오지 않음", "추출 범위")):
            m = re.search(r"p\.(\d+)\(쪽 꼬리 Page \d+\) · (\d+)행", conc_src[0])
            t = doc_T(conc_src[0])
            if not m or t is None:
                probs.append((tag, f"임원겸직 CSV {n}행", "겸직 출처 못 읽음"))
                continue
            p, l = int(m.group(1)), int(m.group(2))
            st["concur_rows"] += 1
            line = t.rng(l, l)
            seq = ws(r["성명"] + r["겸직회사"] + r["겸직회사_직위"] + r["선임일"] + r["상근여부"])
            seq2 = ws(r["겸직회사"] + r["겸직회사_직위"] + r["선임일"] + r["상근여부"])
            near = t.rng(l - 3, l + 3)
            if seq not in near and not (seq2 in line or seq2 in near):
                probs.append((tag, f"임원겸직 CSV {n}행 겸직", f"「{r['성명']} {r['겸직회사']} {r['겸직회사_직위']} {r['선임일']} {r['상근여부']}」 이 줄 {l} 근처에 이어서 없음"))
            if t.page[l] != p:
                probs.append((tag, f"임원겸직 CSV {n}행 겸직", f"p.{p} ↔ 줄 {l} p.{t.page[l]}"))
            # 표 구분 확인용: 인용한 줄 위로 가장 가까운 표 머리 줄(「성명 대상…」)
            hdrs = [k for k in range(l, max(l - 200, 1), -1) if ws(t.lines[k - 1]).startswith("성명대상")]
            if hdrs:
                kind = "타회사" if "타회사" in r["겸직표_구분"] else "계열"
                dts = re.findall(r"20\d\d[.년]\s*\d+", r["겸직표_구분"])
                tabkey.setdefault((os.path.basename(t.path), hdrs[0]), set()).add((kind, ws(dts[-1]) if dts else "", n))
            else:
                probs.append((tag, f"임원겸직 CSV {n}행 겸직", f"줄 {l} 위 200줄 안에 표 머리(성명 대상…) 없음"))
    for (fn, h), v in tabkey.items():
        kinds = {(k, d) for k, d, _ in v}
        if len(kinds) > 1:
            probs.append((tag, f"임원겸직 CSV {sorted(n for *_, n in v)}행 겸직", f"서로 다른 표 구분 {sorted(kinds)} 이 {fn} 같은 표(머리 줄 {h})를 인용"))

    # ── S: 지원조직 CSV
    for n, r in enumerate(sup, 2):
        src = r["출처"]
        m = re.search(r"p\.(\d+)(?:~(\d+))?(?:\(쪽 꼬리 Page [\d~]+\))? · .*?(dart_out/text/risk8/\S+?\.txt) (\d+)~(\d+)행", src)
        if not m:
            if r["부서(팀)명"].startswith("추출 범위에 없음") or "추출 범위에 없음" in r["직원수"]:
                continue
            probs.append((tag, f"지원조직 CSV {n}행", "출처 「p.N · 파일 a~b행」 못 읽음"))
            continue
        t = path2T.get(m.group(3))
        a, b = int(m.group(4)), int(m.group(5))
        win = t.rng(a - 3, b + 3)
        pgw = t.pagews.get(int(m.group(1)), "") + t.pagews.get(int(m.group(1)) + 1, "")
        if r["조직 종류"].startswith("내부회계"):
            # XML 표 칸을 「칸 이름 값」으로 적은 행: 부서명 + 값들이 인용한 줄에 차례대로 있어야 함
            vals = re.findall(r"(?:총 원|\(A\)|\(B\)|비율|평균경력월수)\s+(\S+)", r["직원수"] + " / " + r["직위(근속연수)"])
            seq = ws(r["부서(팀)명"]) + "".join(vals)
            st["support_cells"] += 1
            if seq not in t.rng(a, b):
                probs.append((tag, f"지원조직 CSV {n}행", f"「{r['부서(팀)명']} {' '.join(vals)}」 가 인용한 줄 {a}~{b} 에 이어서 없음"))
            continue
        for col in ("부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)"):
            v = r[col]
            if not v or v in ("나오지 않음",) or v.startswith(("추출 범위에 없음", "나오지 않음")):
                continue
            st["support_cells"] += 1
            if ws(nl(v)) in win:
                continue
            fs = frags(v)
            pieces = fs if fs else [x for x in re.split(r"\n| ⏎ | / ", v) if x.strip()]
            for piece in pieces:
                piece = re.sub(r"\s*\((판단|표에[^)]*|인원 수 칸 없음[^)]*)\)\s*$", "", piece).strip()
                if not piece or "(판단)" in piece or piece.startswith(("표에 ", "칸 없음")):
                    continue
                if ws(piece) not in win and ws(piece) not in pgw:
                    probs.append((tag, f"지원조직 CSV {n}행 {col}", f"「{piece[:60]}」 가 줄 {a}~{b} 근처에 없음"))

    exby = {}
    for r in execs:
        exby.setdefault(r["성명"], []).append(r)
    last_nm = ""
    # ── U: 조직단위 CSV 원문 칸(공시인원·인원_내역·인원_기준일·임원_겸직·대응_근거) ↔ 텍스트
    SKIP = ("추출 범위에 없음", "(숫자 글 없음", "문장·표에 기준일 글 없음", "표에 기준일 글 없음", "대응 임원이 겸직 표에 나오지 않음", "그림·쪽 글에 기준일 글 없음")

    def items(v):
        out = []
        for it in re.split(r"(?m)^(?=[①-⑳])", v or ""):
            it = re.sub(r"^[①-⑳]\s*", "", it.strip())
            it = re.sub(r"\s*〔[^〕]*〕\s*$", "", it).strip()
            it = re.sub(r"^상자 글 안 숫자\(글자층 원문\):\s*", "", it)
            if it and not it.startswith(SKIP):
                out.append(it)
        return out

    def piece_ok(x):
        x = x.replace("⏎", "")
        return in_texts(x) or in_texts(x.replace("ㆍ", "·"))

    for n, r in enumerate(units, 2):
        for col in (C_UNIT, "인원_내역(원문)", "인원_기준일"):
            for it in items(r[col]):
                st["unit_cells"] = st.get("unit_cells", 0) + 1
                if not piece_ok(it):
                    probs.append((tag, f"조직단위 CSV {n}행 {col[:6]}", f"「{it[:60]}」 가 회사 텍스트(공백 무시)에 없음"))
        # 공시인원·인원_내역 ①②… ↔ 인원_출처 ①②… 의 줄 범위(앞뒤 3줄)
        def numbered(v):
            d = {}
            for it in re.split(r"(?m)^(?=[①-⑳])", v or ""):
                it = it.strip()
                if it and it[0] in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳":
                    d[it[0]] = it[1:].strip()
            return d
        srcs = numbered(r["인원_출처"])
        for col in (C_UNIT, "인원_내역(원문)"):
            for k_, it in numbered(r[col]).items():
                it = re.sub(r"\s*〔[^〕]*〕\s*$", "", it).strip()
                if not it or it.startswith(SKIP) or k_ not in srcs:
                    continue
                m = re.search(r"(dart_out/text/risk8/\S+?\.txt) (\d+)~(\d+)행", srcs[k_])
                if not m or m.group(1) not in path2T:
                    continue
                t = path2T[m.group(1)]
                a_, b_ = int(m.group(2)), int(m.group(3))
                st["unit_cited"] = st.get("unit_cited", 0) + 1
                if ws(it.replace("⏎", "")) not in t.rng(a_ - 3, b_ + 3):
                    probs.append((tag, f"조직단위 CSV {n}행 {col[:6]} {k_}", f"「{it[:50]}」 가 인용한 {os.path.basename(m.group(1))} {a_}~{b_}행 근처에 없음"))
        for line in r[C_EXK].split("\n"):
            m = re.match(r"^(?:(\S+): )?(.+?) · (.+?) · 선임 (.+?)(?: · (.+?))?\s*〔([^〕]*)〕\s*$", line.strip())
            if not m:
                if line.strip() and not line.strip().startswith(SKIP):
                    probs.append((tag, f"조직단위 CSV {n}행 임원_겸직", f"「{line[:50]}」 꼴을 못 읽음"))
                continue
            st["unit_cells"] = st.get("unit_cells", 0) + 1
            nm = m.group(1) or last_nm
            last_nm = nm
            seq = ws(nm + m.group(2) + m.group(3) + m.group(4) + (m.group(5) or ""))
            seq2 = ws(nm + "(주)" + m.group(2) + m.group(3) + m.group(4) + (m.group(5) or ""))
            if not any(seq in t.full or seq2 in t.full for t in T.values()):
                probs.append((tag, f"조직단위 CSV {n}행 임원_겸직", f"「{line.strip()[:60]}」 이 겸직 표 행으로 이어서 없음"))
        for line in r["대응_근거(담당업무 원문)"].split("\n"):
            m = re.match(r"^(\S+): ", line)
            if m:
                cur = m.group(1)
        # 대응_근거의 담당업무 = 임원겸직 CSV 담당업무(같은 사람)
        ev = re.split(r"(?m)^(\S+): ", r["대응_근거(담당업무 원문)"])
        for k in range(1, len(ev) - 1, 2):
            nm, body = ev[k], ev[k + 1]
            body = re.sub(r" — \(판단\).*", "", body, flags=re.S).strip()
            if not body or body.startswith("추출"):
                continue
            st["unit_cells"] = st.get("unit_cells", 0) + 1
            if ws(body) not in {ws(e["담당업무(원문)"]) for e in exby.get(nm, [])}:
                probs.append((tag, f"조직단위 CSV {n}행 대응_근거", f"{nm} 담당업무 「{body[:40]}」 가 임원겸직 CSV 담당업무와 다름"))

    # ── X: md 표의 원문 칸 ↔ 텍스트(「칸 글은 원문」 표·「(원문」 머리 칸)
    for i, ln in enumerate(md):
        if not ln.startswith("| ") or i + 1 >= len(md) or not md[i + 1].startswith("|---"):
            continue
        hdr = [c.strip() for c in ln.strip()[1:-1].split(" | ")]
        prev = next((md[k] for k in range(i - 1, max(i - 4, 0), -1) if md[k].strip()), "")
        allraw = "칸 글은 원문" in prev
        cols = [k for k, h in enumerate(hdr) if allraw or "(원문" in h or h in ("총 원", "내부회계담당인력수(A)", "공인회계사자격증소지자수(B)", "비율(B/A*100)", "평균경력월수")]
        if hdr[0] == "번호" or hdr[0] == "임원 표" or hdr[0] == "표":
            continue        # 3-4·4·5 표는 M 검사(CSV 와 같음) + T·U 로 봄
        j = i + 2
        while j < len(md) and md[j].startswith("|"):
            cells = [c.strip() for c in md[j].strip()[1:-1].split(" | ")]
            if allraw or hdr[0].startswith("소속기관"):
                # 행 전체(숫자 칸 포함)가 텍스트에 차례대로 있는지 — 이어진 같은 글 칸(XML 칸 합침)은 하나로,
                # XML 빈칸 「-」 는 PDF 글자층에서 빠지기도 해서 「-」 를 뺀 차례로도 봄
                use = cells if allraw else cells[:6]
                ded = [c for n_, c in enumerate(use) if n_ == 0 or c != use[n_ - 1] or not re.search(r"[가-힣]", c)]
                st["md_raw_rows"] = st.get("md_raw_rows", 0) + 1
                nodash = ws(nl("".join(c for c in ded if c != "-"))).replace("-", "")
                if not in_texts(nl("".join(ded))) and not any(nodash in t.full.replace("-", "") for t in T.values()):
                    probs.append((tag, f"md {j+1}줄 원문 표 행", f"「{' '.join(ded)[:70]}」 이 텍스트에 차례대로 없음"))
            if hdr[:2] == ["조직 단위", "인원(원문 조각)"] and len(cells) >= 6:
                m = re.search(r"(dart_out/text/risk8/\S+?\.txt) (\d+)~(\d+)행", cells[5])
                if m and m.group(1) in path2T:
                    t = path2T[m.group(1)]
                    a_, b_ = int(m.group(2)), int(m.group(3))
                    for k in (1, 2):
                        v = nl(cells[k]).replace("\n", "")
                        if v and not v.startswith(SKIP):
                            st["md_cited_cells"] = st.get("md_cited_cells", 0) + 1
                            if ws(v) not in t.rng(a_ - 3, b_ + 3):
                                probs.append((tag, f"md {j+1}줄 3-3 표", f"「{v[:50]}」 가 같은 행 출처 {a_}~{b_}행 근처에 없음"))
            for k in cols:
                if k >= len(cells):
                    continue
                v = cells[k]
                if not v or v in ("-", "—") or re.fullmatch(r"[\d,.\-\s]+", v) or v.startswith(SKIP) or v.startswith(("표에 인원 수 칸 없음", "표에 활동 칸 없음")):
                    continue
                st["md_raw_cells"] = st.get("md_raw_cells", 0) + 1
                if not piece_ok(nl(v)):
                    parts = [x for x in nl(v).split("\n") if x.strip()]
                    if not all(piece_ok(x) for x in parts):
                        probs.append((tag, f"md {j+1}줄 「{hdr[k][:14]}」 칸", f"「{v[:60]}」 가 회사 텍스트(공백 무시)에 없음"))
            j += 1

    # ── M: CSV ↔ md
    def strip_tag(s):
        return re.sub(r"\s*〔[^〕]*〕\s*$", "", s or "")

    groups = {}
    for r in units:
        groups.setdefault(r["조직도_문서"][:20], []).append(r)
    main_rows = [r for r in units if r["조직도_문서"].startswith("경영공시")]
    rows12 = md_tables(md, "| 번호 | 상위단위(판독) | 조직단위(판독) | 층위(판독) | 상자 글(판독")
    if len(rows12) != len(main_rows):
        probs.append((tag, "md 1-2 표", f"행 수 {len(rows12)} ↔ 조직단위 CSV(경영공시) {len(main_rows)}"))
    for (ln, c), r in zip(rows12, main_rows):
        st["md_rows"] += 1
        want = [(r["상위단위(판독)"] or "—"), r["조직단위(판독)"], r["단위_층위(판독)"], r[C_KJ]]
        got = [c[1], c[2], c[3], c[5]]
        if got != want:
            probs.append((tag, f"md {ln}줄 1-2 표", f"{got} ↔ CSV {want}"))
    sub_rows = [r for r in units if not r["조직도_문서"].startswith("경영공시")]
    rowsS = md_tables(md, "| 번호 | 상위단위(판독) | 조직단위(판독) | 층위(판독) | 상자 글 |") + \
        md_tables(md, "| 번호 | 상위단위(판독) | 조직단위(글자층 원문) | 층위(판독) | 상자 글 |")
    rowsS.sort()
    if len(rowsS) != len(sub_rows):
        probs.append((tag, "md 보조 조직도 표", f"행 수 {len(rowsS)} ↔ 조직단위 CSV(보조) {len(sub_rows)}"))
    subkey = {(strip_tag(r["조직단위(판독)"]), r["조직도_쪽"]): r for r in sub_rows}
    for ln, c in rowsS:
        st["md_rows"] += 1
        cand = [r for r in sub_rows if strip_tag(r["조직단위(판독)"]) == c[2] and ws(r["상위단위(판독)"] or "—") == ws(c[1])]
        if not cand:
            probs.append((tag, f"md {ln}줄 보조 표", f"{c[1]} → {c[2]} 가 조직단위 CSV 보조 행에 없음"))
            continue
        r = cand[0]
        if c[3] != r["단위_층위(판독)"] or c[5] != r[C_KJ]:
            probs.append((tag, f"md {ln}줄 보조 표", f"{c[2]} 층위/겸직표시 {c[3]}/{c[5]} ↔ CSV {r['단위_층위(판독)']}/{r[C_KJ]}"))
    rows34 = md_tables(md, "| 번호 | 조직단위(판독) | 공시인원(원문) | 기준일 |")
    for ln, c in rows34:
        st["md_rows"] += 1
        cand = [r for r in units if r["조직단위(판독)"] == c[1] or strip_tag(r["조직단위(판독)"]) == c[1]]
        cand = [r for r in cand if nl(c[2]) == r[C_UNIT]] or cand
        if not cand:
            probs.append((tag, f"md {ln}줄 3-4 표", f"단위 {c[1]} 가 CSV 에 없음"))
            continue
        r = cand[0]
        if nl(c[2]) != r[C_UNIT] or nl(c[3]) != r["인원_기준일"]:
            probs.append((tag, f"md {ln}줄 3-4 표", f"{c[1]} 공시인원/기준일이 CSV 와 다름"))
    rows4 = md_tables(md, "| 임원 표 | 성명 | 직위 | 등기 | 상근 | 담당업무(원문) |")
    ex1 = {}
    for r in execs:
        if r["임원표_구분"]:
            ex1.setdefault((r["임원표_구분"], r["성명"]), r)
    for ln, c in rows4:
        st["md_rows"] += 1
        r = ex1.get((c[0], c[1]))
        if r is None:
            probs.append((tag, f"md {ln}줄 4 표", f"({c[0]}, {c[1]}) 가 임원겸직 CSV 에 없음"))
            continue
        want = [r["직위"], r["등기"], r["상근"], r["담당업무(원문)"], r["대응_조직단위"], r["대응_방식"]]
        got = [c[2], c[3], c[4], nl(c[5]), nl(c[6]), nl(c[7])]
        if got != want:
            probs.append((tag, f"md {ln}줄 4 표", f"{c[1]}: md ↔ CSV 다름 {[(x, y) for x, y in zip(got, want) if x != y][:2]}"))
    if len(rows4) != len(ex1):
        probs.append((tag, "md 4 표", f"행 수 {len(rows4)} ↔ 임원겸직 CSV 임원 {len(ex1)}"))
    rows5 = md_tables(md, "| 표 | 성명(원문) | 대상 계열사 | 직책 | 선임시기 | 비고 | 쪽 |")
    conc = {(r["겸직표_구분"], r["성명"], r["겸직회사"], r["겸직회사_직위"], r["선임일"], r["상근여부"]) for r in execs
            if r["겸직표_구분"] and ("계열회사" in r["겸직표_구분"] or "겸직" in r["겸직표_구분"]) and "타회사" not in r["겸직표_구분"]}
    md5 = [tuple([c[0], re.sub(r"\s*\(주\)$", "", c[1])] + c[2:6]) for _, c in rows5]   # 성명(원문) 칸의 「(주)」 표시(원소속 주석)는 떼고 맞댐
    st["md_rows"] += len(rows5)
    if set(md5) != conc or len(md5) != len(set(md5)):
        probs.append((tag, "md 5 겸직 표", f"CSV 와 다름: md만 {sorted(set(md5) - conc)[:2]} / CSV만 {sorted(conc - set(md5))[:2]}"))
    rows31 = md_tables(md, "| 조직 종류 | 부서(팀)명 | 직원수(명) | 직위(근속연수) | 주요 활동내역(원문) |")
    for ln, c in rows31:
        st["md_rows"] += 1
        cand = [r for r in sup if r["부서(팀)명"] == c[1] and ws(nl(c[3])) == ws(r["직위(근속연수)"])]
        if not cand:
            probs.append((tag, f"md {ln}줄 3-1 표", f"{c[1]} 행이 지원조직 CSV 에 같은 값으로 없음"))

    # ── R: 판독대조
    bmain = B["조직도"][0]["단위"]
    Bn = {ws(dot(u["조직단위"])) for ch in B["조직도"] if isinstance(ch["단위"], list) for u in ch["단위"]}
    amap = {u["번호"]: u for u in A["units"]}
    for b in A.get("보조_조직도", []):
        for u in b.get("units", []):
            amap[u["번호"]] = dict(u, _page=b["page"])
    def csv_row(num):
        u = amap[num]
        if "_page" in u:
            pool = [r for r in sub_rows if f"p.{u['_page']}" in r["조직도_쪽"]]
        else:
            pool = main_rows
        cand = [r for r in pool if strip_tag(r["조직단위(판독)"]) == u["조직단위"] and (r["상위단위(판독)"] or "") == (u["상위단위"] or "")]
        return cand[0] if cand else None
    for n, r in enumerate(cmpr, 2):
        st["cmp_rows"] += 1
        for col in ("판독B", "확정", "확정 방법(확대 그림 파일·dpi·clip)"):
            if not r[col].strip():
                probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"{col} 빈칸"))
        m = re.match(r"^(?:\(보조 [^)]+\) )?([A-Z]{1,2}\d\d) (단위 이름·상자 글|단위 이름\(글자층 원문\)|단위 이름|상위단위\(선\)|겸직 표시)$", r["칸"])
        if not m:
            continue
        num, what = m.group(1), m.group(2)
        if num not in amap:
            probs.append((tag, f"판독대조 CSV {n}행", f"{num} 가 판독A.json 에 없음"))
            continue
        cr = csv_row(num)
        if cr is None:
            probs.append((tag, f"판독대조 CSV {n}행", f"{num} 가 조직단위 CSV 에 없음"))
            continue
        st["cmp_unit_rows"] += 1
        if what in ("단위 이름", "단위 이름(글자층 원문)"):
            want = strip_tag(cr["조직단위(판독)"])
        elif what == "단위 이름·상자 글":
            want = None
            if ws(dot(r["확정"].split("⏎")[0])).replace("/", "").split("(세로쓰기")[0] != ws(dot(strip_tag(cr["조직단위(판독)"]))) and \
               not ws(dot(r["확정"])).replace("/", "").startswith(ws(dot(strip_tag(cr["조직단위(판독)"])))):
                probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"확정 「{r['확정'][:30]}」 ↔ 조직단위 CSV 「{cr['조직단위(판독)']}」"))
        elif what == "상위단위(선)":
            want = cr["상위단위(판독)"] or "—"
        else:
            want = None
            if ws(r["확정"].split("—")[0]) not in ws(cr[C_KJ]):
                probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"겸직 표시 확정 ↔ 조직단위 CSV 「{cr[C_KJ][:30]}」"))
        if want is not None and r["확정"] != want:
            probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"확정 「{r['확정']}」 ↔ 조직단위 CSV 「{want}」"))
        if what.startswith("단위 이름") and ws(dot(r["판독B"].split("⏎")[0])).replace("/", "").split("(세로쓰기")[0] not in Bn and \
                ws(dot(r["판독B"])).split("⏎")[0] not in Bn:
            if not any(ws(dot(r["판독B"])).replace("/", "").startswith(x) for x in Bn):
                probs.append((tag, f"판독대조 CSV {n}행", f"판독B 「{r['판독B'][:30]}」 가 판독B.json 이름에 없음"))
        if "같음" not in r["확정 방법(확대 그림 파일·dpi·clip)"] and "다름" not in r["확정 방법(확대 그림 파일·dpi·clip)"]:
            probs.append((tag, f"판독대조 CSV {n}행", "확정 방법에 대조 결과(같음/다름) 없음"))
        # 연차 p.11 글자층 원문 이름 ↔ 텍스트 p.11
        if what == "단위 이름(글자층 원문)":
            st["p11_rows"] += 1
            pw = T["연차보고서"].pagews.get(11, "")
            if ws(r["확정"]) not in pw:
                probs.append((tag, f"판독대조 CSV {n}행", f"글자층 이름 「{r['확정']}」 가 연차보고서 p.11 글에 없음"))
    if len(bmain) != len(main_rows):
        probs.append((tag, "판독B.json", f"경영공시 조직도 단위 {len(bmain)} ↔ 조직단위 CSV {len(main_rows)}"))
    for r in units:
        if not r["판독_대조"] or "판독 B 전" in r["판독_대조"]:
            probs.append((tag, f"조직단위 CSV {r['조직단위(판독)']}", "판독_대조 칸이 비었거나 「판독 B 전」"))

    # ── C: iM 머리 집계
    if co == "iM금융지주":
        hd = {r["칸"]: r["확정"] for r in cmpr}
        h1 = hd.get("머리 — 집계 글 1줄(판독)", "")
        want = {k: int(v) for v, k in re.findall(r"(\d+)(총괄|소|부|실|국|팀)", h1)}
        lay = [r["단위_층위(판독)"] for r in main_rows]
        got = {"총괄": lay.count("총괄"), "소": lay.count("소"), "부": lay.count("부"), "실": lay.count("실"), "국": lay.count("국"),
               "팀": lay.count("팀")}
        known = {"팀": (2, 3)}
        st["집계"] = f"머리 {want} ↔ 확정 층위 수 {got} (알려진 차이: 팀 머리 2 ↔ 상자 3)"
        for k, v in want.items():
            if got.get(k) != v and known.get(k) != (v, got.get(k)):
                probs.append((tag, "머리 집계 글", f"{k} 머리 {v} ↔ 확정 {got.get(k)}"))
        h2 = hd.get("머리 — 집계 글 2줄(판독)", "")
        m = re.search(r"(\d+)개 부서", h2)
        if m and int(m.group(1)) != want["소"] + want["부"] + want["실"] + want["국"] + want["팀"]:
            probs.append((tag, "머리 집계 글", "18개 부서 ≠ 소+부+실+국+팀(머리 숫자)"))

    # ── N: 「이름 일치」
    def judged(r, u):
        return "(판단)" in r["대응_방식"] and (u in r["비고"] or u in r.get("대응_근거(담당업무 원문)", ""))
    for n, r in enumerate(execs, 2):
        if not r["대응_조직단위"] or r["대응_조직단위"].startswith("추출 범위"):
            continue
        hay = r["담당업무(원문)"] + "\n" + r["직위"]
        for u in [x.strip() for x in r["대응_조직단위"].split("\n") if x.strip()]:
            st["name_match"] += 1
            if u in hay:
                continue
            if judged(r, u):
                continue
            if ws(u) in ws(hay):
                probs.append((tag, f"임원겸직 CSV {n}행 {r['성명']}", f"「{u}」 가 담당업무에 공백만 다르게 있음 — 「이름 일치」가 아니라 (판단)"))
            else:
                probs.append((tag, f"임원겸직 CSV {n}행 {r['성명']}", f"「{u}」 가 담당업무·직위 원문에 글자 그대로 없고 (판단) 근거도 없음"))
    for n, r in enumerate(units, 2):
        if "이름 일치" not in r[C_HOW]:
            continue
        name = strip_tag(r["조직단위(판독)"])
        for line in r["대응_임원(성명·직위)"].split("\n"):
            nm = line.split(" · ")[0].strip()
            ers = exby.get(nm, [])
            if not ers:
                probs.append((tag, f"조직단위 CSV {n}행 {name}", f"대응 임원 {nm} 가 임원겸직 CSV 에 없음"))
                continue
            st["name_match"] += 1
            if any(name in (e["담당업무(원문)"] + "\n" + e["직위"]) for e in ers):
                continue
            if any(name in e["대응_조직단위"] and "(판단)" in e["대응_방식"] and name in e["비고"] for e in ers) or \
                    ("(판단)" in r[C_HOW] and "(판단)" in r["대응_근거(담당업무 원문)"]):
                continue
            if any(ws(name) in ws(e["담당업무(원문)"]) for e in ers):
                probs.append((tag, f"조직단위 CSV {n}행 {name}", f"{nm} 담당업무에 공백만 다르게 있음 — 「이름 일치」가 아니라 (판단)"))
            else:
                probs.append((tag, f"조직단위 CSV {n}행 {name}", f"「이름 일치」인데 {nm} 담당업무에 단위 이름이 글자 그대로 없음"))
    stat[co] = st
    return [md_path] + [os.path.join(ORG, f"{co}_{k}") for k in ("조직단위.csv", "임원겸직.csv", "지원조직.csv", "판독대조.csv", "판독A.json", "판독B.json")]


def secret_values():
    vals = []
    for name in ("DART_API_KEY", "LAW_OC", "OC", "LAW_API_OC"):
        v = os.environ.get(name)
        if v and len(v) >= 4:
            vals.append(v)
    envp = os.path.join(ROOT, ".env")
    if os.path.exists(envp):
        for ln in open(envp, encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*['\"]?([^'\"\s]+)", ln)
            if m and ("KEY" in m.group(1) or "OC" in m.group(1)) and len(m.group(2)) >= 4:
                vals.append(m.group(2))
    return vals


def main():
    files = []
    for co, cfg in COS.items():
        files += check_company(co, cfg)
    files += [os.path.abspath(__file__), os.path.join(ROOT, "scripts", "dart", "org14_g4.py")]
    vals = secret_values()
    for p in files:
        if not os.path.exists(p):
            probs.append(("공통", p, "파일 없음"))
            continue
        s = open(p, encoding="utf-8").read()
        for v in vals:
            if v in s:
                probs.append(("공통", os.path.relpath(p, ROOT), "인증값 문자열이 파일에 있음(값은 적지 않음)"))
        if re.search(r"crtfc_key=(?!\*\*\*)\w", s) or re.search(r"[?&]OC=(?!\*\*\*)\w", s):
            probs.append(("공통", os.path.relpath(p, ROOT), "crtfc_key=/OC= 뒤에 가리지 않은 값"))
    nimg = 0
    for d in (ORG, HND):
        for dp, dn, fn in os.walk(d):
            for f in fn:
                if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                    nimg += 1
                    probs.append(("공통", os.path.relpath(os.path.join(dp, f), ROOT), "산출 폴더에 PDF·그림 파일"))
    lines = ["# verify14_g4 — iM금융지주·NH농협금융지주 검증 결과", f"인증값 비교 대상 {len(vals)}개(값은 적지 않음), 산출 폴더 PDF·그림 {nimg}개", ""]
    for co, st in stat.items():
        lines.append(f"## {co}")
        for k, v in st.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    lines.append(f"## 원문 대조에서 따로 센 「」 조각 {len(notes)}개 (term=칸 이름·표지 낱말, title=문서 제목(메타 CSV), pandok=판독 이름, search=찾은 방법의 검색어)")
    for x in notes:
        lines.append(" | ".join(x))
    lines.append("")
    lines.append(f"## 문제 {len(probs)}건")
    for p in probs:
        lines.append(" | ".join(str(x) for x in p))
    lines.append("")
    lines.append("결과: " + ("통과(exit 0)" if not probs else "실패(exit 1)"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    head = [ln for ln in lines if not re.match(r"^(iM|NH) \| ", ln) or ln.count("|") > 2][:60]
    print("\n".join(lines[:30]))
    print(f"... 문제 {len(probs)}건 — 전체는 {os.path.relpath(OUT, ROOT)}")
    sys.exit(0 if not probs else 1)


if __name__ == "__main__":
    main()
