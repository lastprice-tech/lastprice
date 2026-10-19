#!/usr/bin/env python3
"""14차 그룹 g2(하나금융지주·우리금융지주) 검증 — 인자 없이 실행, 결과 dart_out/org14/verify14_g2.txt, exit 0/1.

검사:
 Q  md 인용 코드 블록(인용 Qnn) ↔ 텍스트 파일 줄 범위(공백 무시) + 쪽 표지(=== p.N ===)
 F  md·CSV 의 「…」 조각 ↔ 회사 텍스트(본·정정·연차 본/추가·경영공시, 공백 무시). 판독 이름·검색어는 따로 셈
 T  임원겸직 CSV 원문 칸(성명·직위·담당업무·겸직 칸) ↔ 인용한 쪽/줄 근처 텍스트
 S  지원조직 CSV 원문 칸(부서명·직원수·직위·주요 활동) ↔ 인용한 줄 범위
 M  CSV ↔ md 같은 값(1-2 판독 표, 3-4 공시인원 표, 4 임원 표, 5 겸직 표)
 R  판독대조 CSV: 판독B·확정·확정 방법 빈칸 없음, 확정 = 조직단위 CSV, 판독B.json 이름과 같음(공백 무시)
 C  하나 조직도 머리 집계 글 ↔ 확정 단위 수
 N  「이름 일치」 대응: 단위 이름이 담당업무(대표이사는 직위 포함) 원문에 글자 그대로 있는지
 H  회사 CSV 열 이름 = COMMON14 「산출 2~3」 꼴(조직단위는 KB금융지주_조직단위.csv 머리 줄과 글자 그대로 같음), 지원조직 기준일 빈칸 0
 E  「없음」 단정(없음·없었음·없고·없어·없다)이 원문 밖에 0 — md(코드 블록·「>」 줄 밖)와 CSV 모든 칸에서 원문 줄·원문 「」 조각·
    작업 사실 낱말(EOK)을 뺀 나머지를 셈. md 「비평 보정」 절의 「」 조각(지난 전·후 기록)은 뺌
 K  키·OC 값 없음, 산출 폴더에 PDF·PNG 없음
로컬 파일만 읽음(웹 요청 없음).
"""
import csv, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TXT = os.path.join(ROOT, "dart_out", "text", "risk8")
ORG = os.path.join(ROOT, "dart_out", "org14")
HND = os.path.join(ROOT, "handoff", "14차_조직인원겸직")
OUT = os.path.join(ORG, "verify14_g2.txt")

COS = {
    "하나금융지주": {
        "pre": "H",
        "texts": {
            "사업보고서": "사업보고서__하나금융지주__20260316001292.txt",
            "사업보고서정정": "사업보고서__하나금융지주__20260814004019.txt",
            "연차보고서": "연차보고서__하나금융지주_지배구조연차보고서_2026.txt",
            "연차보고서추가": "연차보고서__하나금융지주_지배구조연차보고서_2026_추가공시.txt",
            "경영공시": "경영공시__하나금융지주.txt",
        },
        "head_rows": ("머리 — 집계 글 1줄", "머리 — 집계 글 2줄"),
    },
    "우리금융지주": {
        "pre": "W",
        "texts": {
            "사업보고서": "사업보고서__우리금융지주__20260313001235.txt",
            "연차보고서": "연차보고서__우리금융지주_지배구조연차보고서_2026.txt",
            "연차보고서추가": "연차보고서__우리금융지주_지배구조연차보고서_2026_추가공시.txt",
            "경영공시": "경영공시__우리금융지주.txt",
        },
        "head_rows": (),
    },
}

probs, notes = [], []
stat = {}

# md·CSV 에서 「」로 감싼 낱말 중 원문 인용이 아닌 것(이 작업의 칸 이름·표지 낱말·판단 낱말) — 대조에서 따로 셈
TERMS = {"원본 수집", "추출 범위에 없음", "글자층", "(겸)", "…부문", "공시인원", "이름 일치", "(판단)", "위원장/위원",
         "단위_층위", "N부문 N부", "이어지지 않음", "부서급", "나오지 않음", "판독", "인원_내역", "=== p.N ===",
         "준법감시인(준법지원인) 등 지원조직", "감사위원회 지원조직",
         # 7) 검증 기록의 칸·키 이름과 판독 B 층위 낱말
         "clip_pt", "보조_연차보고서_조직도_판독B", "판독_대조", "B 대기(검증 에이전트)", "B 대기", "A↔글자층",
         "판독 A ↔ 판독 B", "p.N · 줄 L", "부서(부)", "부서(팀)", "부", "팀"}
# 회사 CSV 열 이름(COMMON14 「산출 2~3」 꼴 — 조직단위는 KB금융지주_조직단위.csv 머리 줄과 같음). 임원겸직은 앞 13열이 COMMON 꼴, 뒤 3열은 g2 덧붙임.
HEAD_UNIT = ["회사", "조직도_문서", "조직도_쪽", "조직도_기준일(원문)", "상위단위(판독)", "조직단위(판독)", "단위_층위(판독)",
             "조직도_겸직표시(판독, 없으면 빈칸)", "공시인원(원문, 없으면 「추출 범위에 없음」)", "인원_내역(원문)", "인원_기준일", "인원_출처",
             "대응_임원(성명·직위)", "대응_근거(담당업무 원문)", "대응_방식(이름 일치/(판단)/추출 범위에 없음)",
             "임원_겸직(원문: 겸직회사·직위·선임일·상근)", "겸직_출처", "판독_대조", "비고"]
HEAD_EXEC = ["회사", "성명", "직위", "등기", "상근", "담당업무(원문)", "대응_조직단위", "대응_방식", "겸직회사", "겸직회사_직위", "선임일",
             "상근여부", "출처(문서·접수번호·쪽)", "임원표_구분", "겸직표_구분", "비고"]
HEAD_SUPP = ["회사", "조직 종류", "부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)", "기준일", "출처"]
# 검사 안에서는 짧은 열쇠로 읽는다(파일 열 이름 → 짧은 꼴)
SHORT = {"조직도_겸직표시(판독, 없으면 빈칸)": "조직도_겸직표시(판독)", "공시인원(원문, 없으면 「추출 범위에 없음」)": "공시인원(원문)",
         "대응_방식(이름 일치/(판단)/추출 범위에 없음)": "대응_방식", "임원_겸직(원문: 겸직회사·직위·선임일·상근)": "임원_겸직(원문)",
         "출처(문서·접수번호·쪽)": "출처"}
TOP = "(맨 위 — 위로 이어진 상자가 나오지 않음)"
# E 검사: 「없음」 단정 꼴과, 단정이 아닌 작업 사실 낱말(방법 설명 — 13차와 같은 공통 꼴 ④)
EOPSEUM = re.compile(r"없(?:음|었|고(?=\s)|어(?=\s)|다(?=[\s.]))")
EOK = ["추출 범위에 없음", "글자층 없음", "글자층에 없음", "API 키·OC 사용 없음", "고친 인용: 없음", "(인자 없음"]
FIX_HEAD = "### 비평 보정"
META = ["dart_out/risk8/연차보고서_FY2025.csv", "dart_out/risk8/경영공시_2026_2Q.csv", "dart_out/risk8/DART_문서목록.csv"]


def ws(s):
    return re.sub(r"\s+", "", s or "")


def dot(s):
    return (s or "").replace("ㆍ", "·").replace("・", "·").replace("‧", "·")


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
        self.pagews = {p: ws("\n".join(v)) for p, v in self.pagelines.items()}

    def rng(self, a, b):
        return ws("\n".join(self.lines[max(a, 1) - 1:min(b, len(self.lines))]))


def bound(name, hay):
    """단위 이름이 앞뒤 글자 경계로 있는지(「장」「소속」 붙음 허용 — md 4) 대응 규칙)."""
    pat = r"(?<![가-힣A-Za-z0-9])" + re.escape(name) + r"(?=$|[\s(),/·ㆍ\]]|장|소속)"
    return re.search(pat, hay) is not None


def doc_of(seg, T):
    """출처 조각에서 문서 종류를 고름(가장 뒤에 나온 문서 이름)."""
    best, pos = None, -1
    for key, kw in (("사업보고서", "사업보고서"), ("연차보고서", "연차보고서"), ("경영공시", "경영공시")):
        k = seg.rfind(kw)
        if k > pos:
            best, pos = key, k
    if best == "사업보고서" and "20260814004019" in seg[pos:]:
        best = "사업보고서정정"
    if best == "연차보고서" and "추가" in seg[pos:pos + 80]:
        best = "연차보고서추가"
    return T.get(best)


def load_csv(p):
    return [{SHORT.get(k, k): v for k, v in r.items()} for r in csv.DictReader(open(p, encoding="utf-8-sig"))]


def head_of(p):
    return next(csv.reader(open(p, encoding="utf-8-sig")))


def frags(s):
    return re.findall(r"「([^「」]+)」", s or "")


def md_tables(lines, header_start):
    """header_start 로 시작하는 표 줄 다음의 행들을 칸 목록으로."""
    out = []
    for i, ln in enumerate(lines):
        if ln.startswith(header_start):
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split(" | ")]
                out.append((j + 1, cells))
                j += 1
    return out


def check_company(co, cfg):
    st = {k: 0 for k in ("quotes", "frag_ok", "frag_term", "frag_title", "frag_pandok", "frag_search", "frag_bad", "pageline", "exec_cells", "concur_rows",
                         "support_cells", "md_rows", "cmp_rows", "name_match", "name_match_ws")}
    T = {k: Text(os.path.join(TXT, v)) for k, v in cfg["texts"].items()}
    path2T = {os.path.join("dart_out/text/risk8", v): T[k] for k, v in cfg["texts"].items()}
    md_path = os.path.join(HND, f"14_{co}.md")
    md = open(md_path, encoding="utf-8").read().split("\n")
    units = load_csv(os.path.join(ORG, f"{co}_조직단위.csv"))
    execs = load_csv(os.path.join(ORG, f"{co}_임원겸직.csv"))
    sup = load_csv(os.path.join(ORG, f"{co}_지원조직.csv"))
    cmpr = load_csv(os.path.join(ORG, f"{co}_판독대조.csv"))
    A = json.load(open(os.path.join(ORG, f"{co}_판독A.json"), encoding="utf-8"))
    B = json.load(open(os.path.join(ORG, f"{co}_판독B.json"), encoding="utf-8"))
    tag = co[:2]

    # 판독 이름 모음(판독 글은 원문 글자 그대로가 아니므로 「」 조각 대조에서 따로 셈)
    pandok = set()
    for u in A["단위"]:
        pandok |= {ws(dot(u["조직단위_판독"])), ws(dot(u["상위단위_판독"])), ws(dot(u["상자글_판독"]).replace("⏎", ""))}
    for u in B["단위"]:
        pandok |= {ws(dot(u["단위"]))}
    for u in A.get("보조_연차보고서_조직도", {}).get("단위", []):
        pandok |= {ws(dot(u["단위"])), ws(dot(u["상위_판독"]))}
    for r in units:
        pandok |= {ws(dot(r["조직단위(판독)"])), ws(dot(r["상위단위(판독)"]))}
    pandok |= {x.replace("/", "") for x in list(pandok)}
    pandok.discard("")
    alltext = "".join(t.full for t in T.values())
    alltext_dot = dot(alltext)

    meta = ""
    for mp in META:
        mpp = os.path.join(ROOT, mp)
        if os.path.exists(mpp):
            meta += ws(open(mpp, encoding="utf-8-sig").read())

    def frag_status(f, ctx):
        w = ws(f)
        if not w:
            return "ok"
        if w in alltext or ws(dot(f)) in alltext_dot:
            return "ok"
        if "…" in f:                      # 줄임표로 이은 인용: 조각마다 같은 파일에 차례대로 있어야 함
            parts = [ws(x) for x in f.split("…") if ws(x)]
            for t in T.values():
                pos, okp = 0, True
                for x in parts:
                    k = t.full.find(x, pos)
                    if k < 0:
                        okp = False; break
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
        if any(k in ctx for k in ("찾은 방법", "검색", "검색어")):
            return "search"
        return "bad"

    # ── Q: md 인용 코드 블록
    hdr_re = re.compile(r"^\[(.*) · 줄 (\d+)–(\d+) · (dart_out/text/risk8/[^ ]+?\.txt) · .*인용 (Q\d+[a-z]?)\]\s*$")
    seen_q = set()
    for i, ln in enumerate(md):
        m = hdr_re.match(ln)
        if not m:
            continue
        pre, a, b, tp, q = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), m.group(5)
        pm = list(re.finditer(r"p\.(\d+)(?:\s*[–~-]\s*(\d+))?", pre))
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
        seen_q.add(q)
        if ws(block) != t.rng(a, b):
            probs.append((tag, f"md {i+1}줄 {q}", f"코드 블록이 {tp} 줄 {a}–{b} 와 다름(공백 무시)"))
        if pm:
            p1 = int(pm[-1].group(1)); p2 = int(pm[-1].group(2) or p1)
            if t.page[a] != p1 or t.page[b] not in (p1, p2) or (p2 != p1 and t.page[b] != p2):
                probs.append((tag, f"md {i+1}줄 {q}", f"쪽 표기 p.{p1}{'–'+str(p2) if p2!=p1 else ''} ↔ 텍스트 줄 {a} p.{t.page[a]}, 줄 {b} p.{t.page[b]}"))
        else:
            probs.append((tag, f"md {i+1}줄 {q}", "쪽 표기 없음"))

    # ── P: 출처 표기 「p.N · 줄 L(–M)」 ↔ 텍스트 쪽 표지 (md 본문·CSV 모든 칸)
    def pageline(text, where):
        for seg in re.split(r"\n|<br>|; | ; ", text):
            for m in re.finditer(r"p\.(\d+) · 줄 (\d+)(?:–(\d+))?", seg):
                t = doc_of(seg[:m.start()], T)
                if t is None:
                    continue
                p, a = int(m.group(1)), int(m.group(2))
                b = int(m.group(3) or a)
                st["pageline"] += 1
                if a >= len(t.page) or t.page[a] != p or t.page[min(b, len(t.page) - 1)] not in (p, p + 1):
                    pa = t.page[a] if a < len(t.page) else "?"
                    probs.append((tag, where, f"p.{p} · 줄 {a} ↔ {os.path.basename(t.path)} 줄 {a} 은 p.{pa}"))

    inb = False
    for i, ln in enumerate(md):
        if ln.startswith("```"):
            inb = not inb
            continue
        if not inb and not hdr_re.match(ln):
            pageline(ln, f"md {i+1}줄")
    for fname, rows_ in (("조직단위", units), ("지원조직", sup)):
        for n, r in enumerate(rows_, 2):
            for col, v in r.items():
                if v and "줄 " in v:
                    pageline(v, f"{fname} CSV {n}행 {col}")

    # ── F: md 의 「」 조각(코드 블록 밖)
    inblock = False
    fix_from = next((i for i, ln in enumerate(md) if ln.startswith(FIX_HEAD)), len(md))
    st["frag_fixrec"] = 0
    for i, ln in enumerate(md):
        if ln.startswith("```"):
            inblock = not inblock
            continue
        if inblock:
            continue
        if i >= fix_from:
            st["frag_fixrec"] += len(frags(ln))
            continue
        for f in frags(ln):
            s = frag_status(f, ln)
            if s == "bad" and "|" in f:
                s = "search"          # 정규식 검색어 묶음
            st["frag_" + s] += 1
            if s not in ("ok", "bad"):
                notes.append((tag, f"md {i+1}줄", s, f[:70]))
            if s == "bad":
                probs.append((tag, f"md {i+1}줄", f"「{f[:60]}」 가 회사 텍스트(공백 무시)·판독 이름에 없음"))

    # ── F: 조직단위 CSV 원문 칸 「」 조각
    for n, r in enumerate(units, 2):
        for col in ("공시인원(원문)", "인원_내역(원문)", "대응_근거(담당업무 원문)", "임원_겸직(원문)"):
            for f in frags(r[col]):
                s = frag_status(f, r[col])
                st["frag_" + s] += 1
                if s not in ("ok", "bad"):
                    notes.append((tag, f"조직단위 CSV {n}행 {col}", s, f[:70]))
                if s == "bad":
                    probs.append((tag, f"조직단위 CSV {n}행 {col}", f"「{f[:60]}」 가 텍스트에 없음"))

    # ── T: 임원겸직 CSV
    for n, r in enumerate(execs, 2):
        src = r["출처"]
        m = re.search(r"임원 표 p\.(\d+) 줄 (\d+)", src)
        t = T["사업보고서"]
        if m:
            p, l = int(m.group(1)), int(m.group(2))
            win = t.rng(l - 2, l + 45)
            if t.page[l] != p:
                probs.append((tag, f"임원겸직 CSV {n}행", f"임원 표 쪽 p.{p} ↔ 줄 {l} 은 p.{t.page[l]}"))
            for col in ("성명", "담당업무(원문)", "직위", "등기", "상근"):
                v = r[col]
                if not v or v.startswith(("추출 범위에 없음", "나오지 않음")):
                    continue
                st["exec_cells"] += 1
                if ws(v) not in win and ws(v) not in t.pagews.get(p, ""):
                    probs.append((tag, f"임원겸직 CSV {n}행 {col}", f"「{v[:50]}」 가 p.{p} 줄 {l} 근처에 없음"))
        else:
            probs.append((tag, f"임원겸직 CSV {n}행", "출처에 「임원 표 p.N 줄 L」 없음"))
        if r["겸직회사"] and "나오지 않음" not in r["겸직회사"] and "추출 범위" not in r["겸직회사"]:
            m2 = re.search(r"겸직 표 p\.(\d+)", src)
            if not m2:
                probs.append((tag, f"임원겸직 CSV {n}행", "겸직 칸이 있는데 출처에 「겸직 표 p.N」 없음"))
                continue
            p = int(m2.group(1))
            st["concur_rows"] += 1
            seq = ws(r["겸직회사"] + r["겸직회사_직위"] + r["선임일"] + r["상근여부"])
            pg = t.pagews.get(p, "") + t.pagews.get(p + 1, "")
            if seq not in pg:
                probs.append((tag, f"임원겸직 CSV {n}행 겸직", f"「{r['겸직회사']} {r['겸직회사_직위']} {r['선임일']} {r['상근여부']}」 이 겸직 표 p.{p} 에 이어서 없음"))
            if ws(r["성명"]) not in pg:
                probs.append((tag, f"임원겸직 CSV {n}행 겸직", f"성명 {r['성명']} 이 겸직 표 p.{p} 에 없음"))

    # ── S: 지원조직 CSV
    for n, r in enumerate(sup, 2):
        src = r["출처"]
        m = re.search(r"p\.(\d+) · 줄 (\d+)–(\d+) · .*?(dart_out/text/risk8/[^ ;]+?\.txt)", src)
        if not m:
            if r["부서(팀)명"] == "추출 범위에 없음":
                continue
            # 출처에 파일 경로가 줄여 적힌 경우: 문서 종류로 고름
            m = re.search(r"p\.(\d+) · 줄 (\d+)–(\d+)", src)
            if not m:
                probs.append((tag, f"지원조직 CSV {n}행", "출처에 「p.N · 줄 a–b」 없음")); continue
            t = T["연차보고서"] if src.startswith("연차보고서") else T["사업보고서"]
        else:
            t = path2T.get(m.group(4))
            if t is None:
                probs.append((tag, f"지원조직 CSV {n}행", f"텍스트 {m.group(4)} 가 목록에 없음")); continue
        p, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if t.page[a] != p:
            probs.append((tag, f"지원조직 CSV {n}행", f"쪽 p.{p} ↔ 줄 {a} 은 p.{t.page[a]}"))
        win = t.rng(a - 12, b + 6)
        for col in ("부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)"):
            v = r[col]
            if not v or "나오지 않음" == v or v.startswith("추출 범위에 없음"):
                continue
            st["support_cells"] += 1
            if ws(v) in win:
                continue
            fs = frags(v)
            pieces = fs if fs else [x for x in re.split(r"\n|; |, " + ("|·" if col == "부서(팀)명" else ""), v) if x.strip()]
            for piece in pieces:
                piece = re.sub(r"\((?:평균 )?근속연수 나오지 않음\)|근속연수 나오지 않음|직위 나오지 않음", "", piece).strip()
                if not piece or "(판단)" in piece:
                    continue
                if ws(piece) not in win and ws(piece) not in t.pagews.get(p, "") + t.pagews.get(p + 1, ""):
                    if re.match(r"^\d+ \(텍스트", v) or v.startswith(("표에 활동 칸이 나오지 않음", "해당부서 평균 근속기간")):
                        continue      # 주석이 붙은 칸 — 「」 조각만 원문(위 frags 로 검사)
                    probs.append((tag, f"지원조직 CSV {n}행 {col}", f"「{piece[:60]}」 가 줄 {a}–{b} 근처에 없음"))

    # ── M: CSV ↔ md
    ou = [r for r in units if r["조직도_문서"].startswith("경영공시")]
    rows12 = md_tables(md, "| 번호 | 상위단위(판독) |")
    if len(rows12) != len(ou):
        probs.append((tag, "md 1-2 표", f"행 수 {len(rows12)} ↔ 조직단위 CSV(경영공시 조직도) {len(ou)}"))
    for (ln, c), r in zip(rows12, ou):
        st["md_rows"] += 1
        want = [("—" if not r["상위단위(판독)"] else r["상위단위(판독)"]), r["조직단위(판독)"], r["단위_층위(판독)"], r["조직도_겸직표시(판독)"]]
        got = [c[1], c[2], c[3], c[5]]
        if got != want:
            probs.append((tag, f"md {ln}줄 1-2 표", f"{got} ↔ CSV {want}"))
    rows34 = md_tables(md, "| 조직단위(판독) | 공시인원(원문) |")
    bymame = {r["조직단위(판독)"]: r for r in units}
    for ln, c in rows34:
        st["md_rows"] += 1
        r = bymame.get(c[0])
        if r is None:
            probs.append((tag, f"md {ln}줄 3-4 표", f"단위 {c[0]} 가 CSV 에 없음")); continue
        if c[1] != r["공시인원(원문)"] or c[2].replace("<br>", "\n") != r["인원_내역(원문)"]:
            probs.append((tag, f"md {ln}줄 3-4 표", f"{c[0]} 공시인원/인원_내역이 CSV 와 다름"))
    rows4 = md_tables(md, "| 표 | 성명 | 직위 | 등기 |")
    ex1 = {}
    for r in execs:
        ex1.setdefault((r["임원표_구분"], r["성명"]), r)
    for ln, c in rows4:
        st["md_rows"] += 1
        r = ex1.get((c[0], c[1]))
        if r is None:
            probs.append((tag, f"md {ln}줄 4 표", f"({c[0]}, {c[1]}) 가 임원겸직 CSV 에 없음")); continue
        want = [r["직위"], r["등기"], r["상근"], r["담당업무(원문)"], r["대응_조직단위"], r["대응_방식"]]
        got = [c[2], c[3], c[4], c[5], c[6].replace("<br>", "\n"), c[7]]
        if got != want:
            probs.append((tag, f"md {ln}줄 4 표", f"{c[1]}: {got} ↔ CSV {want}"))
    if len(rows4) != len(ex1):
        probs.append((tag, "md 4 표", f"행 수 {len(rows4)} ↔ 임원겸직 CSV 임원 {len(ex1)}"))
    rows5 = md_tables(md, "| 표 | 성명 | 겸직회사명/대상회사 |")
    conc = [(r["겸직표_구분"], r["성명"], r["겸직회사"], r["겸직회사_직위"], r["선임일"], r["상근여부"]) for r in execs if r["겸직표_구분"]]
    md5 = [tuple(c[:6]) for _, c in rows5]
    st["md_rows"] += len(rows5)
    if set(md5) != set(conc) or len(md5) != len(set(md5)):
        a_only = set(md5) - set(conc); c_only = set(conc) - set(md5)
        probs.append((tag, "md 5 겸직 표", f"CSV 와 다름: md만 {sorted(a_only)[:3]} / CSV만 {sorted(c_only)[:3]}"))

    # ── R: 판독대조
    num_unit = {u["번호"]: (units[i] if i < len(units) else None) for i, u in enumerate(A["단위"])}
    Bn = {ws(dot(u["단위"])) for u in B["단위"]}
    for n, r in enumerate(cmpr, 2):
        st["cmp_rows"] += 1
        for col in ("판독B", "확정", "확정 방법(확대 그림 파일·dpi·clip)"):
            if not r[col].strip():
                probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"{col} 빈칸"))
        m = re.match(r"^([HW]\d\d) (단위 이름|상위단위|층위)$", r["칸"])
        if not m:
            continue
        u = num_unit.get(m.group(1))
        if u is None:
            probs.append((tag, f"판독대조 CSV {n}행", f"{m.group(1)} 가 조직단위 CSV 에 없음")); continue
        col = {"단위 이름": "조직단위(판독)", "상위단위": "상위단위(판독)", "층위": "단위_층위(판독)"}[m.group(2)]
        want = u[col] if u[col] else TOP
        if r["확정"] != want:
            probs.append((tag, f"판독대조 CSV {n}행 {r['칸']}", f"확정 「{r['확정']}」 ↔ 조직단위 CSV 「{want}」"))
        if m.group(2) == "단위 이름" and ws(dot(r["확정"])) not in Bn:
            probs.append((tag, f"판독대조 CSV {n}행", f"확정 「{r['확정']}」 가 판독B.json 이름(공백 무시)에 없음"))
    if len(B["단위"]) != len(ou):
        probs.append((tag, "판독B.json", f"단위 {len(B['단위'])} ↔ 조직단위 CSV(경영공시) {len(ou)}"))

    # ── C: 머리 집계 글
    if cfg["head_rows"]:
        hd = {r["칸"]: r["확정"] for r in cmpr}
        h1, h2 = hd[cfg["head_rows"][0]], hd[cfg["head_rows"][1]]
        want = dict((k, int(v)) for v, k in re.findall(r"(\d+)(부문|실|본부|부서)", h1))
        want.update((k, int(v)) for v, k in re.findall(r"(\d+)(단|국|센터|팀)", h2))
        lay = [r["단위_층위(판독)"] for r in ou]
        got = {
            "부문": sum(1 for x in lay if x == "부문") + sum(1 for x in lay if x.startswith("준법감시인")),
            "실": lay.count("실"), "본부": lay.count("본부"), "단": lay.count("단"),
            "국": sum(1 for x in lay if x.startswith("국")), "센터": lay.count("센터"), "팀": lay.count("팀"),
        }
        got["부서"] = got["단"] + got["국"] + got["센터"] + got["팀"]
        st["집계"] = f"글 {want} ↔ 확정 {got} (부문 = 「부문」 {got['부문']-1} + 준법감시인 1, (판단))"
        for k, v in want.items():
            if got.get(k) != v:
                probs.append((tag, "머리 집계 글", f"{k} 글 {v} ↔ 확정 단위 수 {got.get(k)}"))
    else:
        hd = {r["칸"]: r["확정"] for r in cmpr}
        st["집계"] = f"집계 글 {hd.get('머리 — 집계 글','')[:12]} · 확정 단위 수 {hd.get('조직 단위 수')} ↔ CSV {len(ou)}"
        if str(len(ou)) != hd.get("조직 단위 수"):
            probs.append((tag, "조직 단위 수", f"{hd.get('조직 단위 수')} ↔ {len(ou)}"))

    # ── N: 「이름 일치」
    for n, r in enumerate(execs, 2):
        if "이름 일치" not in r["대응_방식"]:
            continue
        hay = r["담당업무(원문)"] + " " + r["직위"]
        for un in r["대응_조직단위"].split("\n"):
            if "(판단)" in un or not un.strip() or un.startswith("추출 범위"):
                continue
            un = re.sub(r"\s*\[.*\]$", "", un).strip()
            st["name_match"] += 1
            if bound(un, hay):
                continue
            if un in hay:
                probs.append((tag, f"임원겸직 CSV {n}행 {r['성명']}", f"「{un}」 가 담당업무 안 더 긴 이름의 일부로만 있음(앞뒤 글자 경계 아님)"))
                continue
            if ws(un) in ws(hay):
                st["name_match_ws"] += 1
                continue
            probs.append((tag, f"임원겸직 CSV {n}행 {r['성명']}", f"「이름 일치」인데 「{un}」 가 담당업무·직위 원문에 글자 그대로 없음"))
    for n, r in enumerate(units, 2):
        if "이름 일치" not in r["대응_방식"]:
            continue
        name = r["조직단위(판독)"]
        for line in r["대응_근거(담당업무 원문)"].split("\n"):
            if "(판단)" in line or not line.strip():
                continue
            fs = frags(line)
            if not fs:
                continue
            st["name_match"] += 1
            hay = fs[0]
            ex = [e for e in execs if e["성명"] == line.split(":")[0].strip()]
            if ex:
                hay += " " + ex[0]["직위"]
            if bound(name, hay):
                continue
            if name in hay:
                probs.append((tag, f"조직단위 CSV {n}행 {name}", f"담당업무 「{fs[0][:40]}」 안 더 긴 이름의 일부로만 있음"))
                continue
            if ws(name) in ws(hay):
                st["name_match_ws"] += 1
                continue
            probs.append((tag, f"조직단위 CSV {n}행 {name}", f"「이름 일치」인데 담당업무 「{fs[0][:40]}」 에 단위 이름이 없음"))
    # ── H: 회사 CSV 열 이름 · 지원조직 기준일 빈칸
    for fname, want in (("조직단위", HEAD_UNIT), ("임원겸직", HEAD_EXEC), ("지원조직", HEAD_SUPP)):
        got = head_of(os.path.join(ORG, f"{co}_{fname}.csv"))
        if got != want:
            probs.append((tag, f"{fname} CSV 머리", f"열 이름이 COMMON 꼴과 다름: {[g for g, w in zip(got, want) if g != w][:3]}"))
    kb = os.path.join(ORG, "KB금융지주_조직단위.csv")
    if os.path.exists(kb) and head_of(kb) != HEAD_UNIT:
        probs.append((tag, "조직단위 CSV 머리", "KB금융지주_조직단위.csv 머리 줄과 다름"))
    for n, r in enumerate(sup, 2):
        if not r["기준일"].strip():
            probs.append((tag, f"지원조직 CSV {n}행", "기준일 빈칸"))

    # ── E: 「없음」 단정이 원문 밖에 있는지
    def rest(text, drop_all_frags=False):
        keep = []
        for line in re.split(r"\n|<br>", text):
            w = ws(line)
            if len(w) >= 6 and (w in alltext or ws(dot(line)) in alltext_dot):
                continue                       # 원문 줄 그대로
            for _ in range(4):                 # 겹친 「「…」…」 는 안쪽부터 여러 번
                for f in frags(line):
                    if drop_all_frags or (ws(f) and (ws(f) in alltext or ws(dot(f)) in alltext_dot)):
                        line = line.replace("「" + f + "」", "〔〕")
            for ok in EOK:
                line = line.replace(ok, "")
            keep.append(line)
        return "\n".join(keep)

    st["eopseum"] = 0
    inb = False
    for i, ln in enumerate(md):
        if ln.startswith("```"):
            inb = not inb
            continue
        if inb or ln.startswith(">"):
            continue
        for m in EOPSEUM.finditer(rest(ln, drop_all_frags=i >= fix_from)):
            st["eopseum"] += 1
            probs.append((tag, f"md {i+1}줄", f"「없음」 단정 꼴 「…{rest(ln, i >= fix_from)[max(0, m.start()-25):m.end()]}」"))
    for fname, rows_ in (("조직단위", units), ("임원겸직", execs), ("지원조직", sup), ("판독대조", cmpr)):
        for n, r in enumerate(rows_, 2):
            for col, v in r.items():
                for m in EOPSEUM.finditer(rest(v or "")):
                    st["eopseum"] += 1
                    probs.append((tag, f"{fname} CSV {n}행 {col}", f"「없음」 단정 꼴 「…{rest(v)[max(0, m.start()-25):m.end()]}」"))
    stat[co] = st
    return [md_path, os.path.join(ORG, f"{co}_조직단위.csv"), os.path.join(ORG, f"{co}_임원겸직.csv"),
            os.path.join(ORG, f"{co}_지원조직.csv"), os.path.join(ORG, f"{co}_판독대조.csv"),
            os.path.join(ORG, f"{co}_판독A.json"), os.path.join(ORG, f"{co}_판독B.json"), os.path.join(ORG, f"{co}_검증입력.json")]


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
    files += [os.path.abspath(__file__), os.path.join(ROOT, "scripts", "dart", "org14_g2.py")]
    vals = secret_values()
    for p in files:
        if not os.path.exists(p):
            probs.append(("공통", p, "파일 없음")); continue
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
    lines = ["# verify14_g2 — 하나금융지주·우리금융지주 검증 결과", f"인증값 비교 대상 {len(vals)}개(값은 적지 않음), 산출 폴더 PDF·그림 {nimg}개", ""]
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
    print("\n".join(lines[:40]))
    if len(lines) > 40:
        print(f"... ({len(lines)-40} 줄 더 — {os.path.relpath(OUT, ROOT)})")
    sys.exit(0 if not probs else 1)


if __name__ == "__main__":
    main()
