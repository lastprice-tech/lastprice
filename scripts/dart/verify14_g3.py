#!/usr/bin/env python3
"""14차 그룹 g3(메리츠금융지주·한국투자금융지주) 검증 — 인자 없이 실행, 결과 dart_out/org14/verify14_g3.txt, exit 0/1.

검사(로컬 파일만 읽음 — 웹 요청 없음):
 Q  md 인용 코드 블록 ↔ 텍스트 파일 줄 범위(공백 무시) + 쪽 표지(=== p.N ===)
 P  md·CSV 의 「p.N · 줄 L」「p.N 줄 L」 쪽 표기 ↔ 그 줄의 쪽 표지
 F  md(7) 검증 기록 절 제외 — 고치기 전 글·검색어를 적은 곳)·CSV 의 「…」 조각 ↔ 회사 텍스트(사업보고서 본·정정, 연차보고서 본·재공시, 경영공시; 공백·가운뎃점 모양 무시).
    칸 이름·표지 낱말(term), 문서 제목(title, 메타 CSV), 판독 이름(pandok), 찾은 방법의 검색어(search)는 따로 셈
 T  임원겸직 CSV 원문 칸(성명·직위·담당업무·겸직회사·직책·상근여부) ↔ 출처 줄 근처 텍스트
 S  지원조직 CSV 원문 칸(부서명·직위·주요 활동) ↔ 출처 줄 범위
 M  CSV ↔ md 같은 값(1-2 판독 표·3-1 지원조직 표·3-4 공시인원 표·4 임원 표·5 겸직 표)
 R  판독대조 CSV: 판독B·확정·확정 방법 빈칸 없음, 확정 = 조직단위 CSV, 판독B 칸 = 판독B.json
 C  조직도 머리 집계 글 ↔ 확정 단위 수(두 회사 모두 집계 글 나오지 않음 — 단위 수만 맞댐)
 N  「이름 일치」: 단위 이름이 담당업무 원문에 글자 그대로(앞뒤 글자 경계, 「장」「소속」「겸」 붙음 허용) 있는지
 K  키·OC 값 없음(값은 적지 않음), 산출 폴더(handoff/14차_조직인원겸직, dart_out/org14)에 PDF·PNG 없음
"""
import csv, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TXT = os.path.join(ROOT, "dart_out", "text", "risk8")
ORG = os.path.join(ROOT, "dart_out", "org14")
HND = os.path.join(ROOT, "handoff", "14차_조직인원겸직")
OUT = os.path.join(ORG, "verify14_g3.txt")

COS = {
    "메리츠금융지주": {
        "pre": "M", "units": 22,
        "texts": {
            "본": "사업보고서__메리츠금융지주__20260318001419.txt",
            "20260331004089": "사업보고서__메리츠금융지주__20260331004089.txt",
            "20260331004202": "사업보고서__메리츠금융지주__20260331004202.txt",
            "20260318001549": "사업보고서__메리츠금융지주__20260318001549.txt",
            "20260406004144": "사업보고서__메리츠금융지주__20260406004144.txt",
            "연차": "연차보고서__메리츠금융지주_지배구조연차보고서_2026.txt",
            "경영공시": "경영공시__메리츠금융지주.txt",
        },
        # 정정판 20260318001549 원문 XML 대신 저장된 OpenDART 응답(014) — md 의 「파일이 존재하지 않습니다」 원문
        "extra": ["dart_out/raw/document/20260318001549.zip"],
    },
    "한국투자금융지주": {
        "pre": "K", "units": 24,
        "texts": {
            "본": "사업보고서__한국투자금융지주__20260319001006.txt",
            "연차": "연차보고서__한국투자금융지주_지배구조연차보고서_2026.txt",
            "재공시": "연차보고서__한국투자금융지주_지배구조연차보고서_2026_재공시.txt",
            "경영공시": "경영공시__한국투자금융지주.txt",
        },
    },
}
META = ["dart_out/risk8/연차보고서_FY2025.csv", "dart_out/risk8/경영공시_2026_2Q.csv", "dart_out/risk8/DART_문서목록.csv"]

# 원문 인용이 아닌 「」 낱말(이 작업의 칸 이름·표지·판단 낱말, 검증 기록 낱말)
TERMS = {"판독", "(판단)", "추출 범위에 없음", "나오지 않음", "=== p.N ===", "원본 수집", "이름 일치", "공시인원", "인원_내역",
         "단위_층위", "글자층", "(겸)", "겸", "장", "소속", "실", "N부문 N팀", "N실", "위원장/위원/의장", "B 대기(검증 에이전트)",
         "(판단) 띄어쓰기만 다름", "(판단) 「실」 글자만 빠짐", "판독_대조", "A↔글자층", "연결선 없음", "4부문 8담당…",
         "34부서", "판독대조", "글자층에 없음 — 그림 판독/설명", "글자층과 같음…", "(판단) / 이름 일치", "확정",
         "판독 A", "판독 B", "판독B", "다름", "같음", "/", " / ", "부문장", "그룹 부문", "협의회", "책임자(임원)", "부문",
         "경영 회의체", "최고책임자(직위 상자)", "직위 상자", "부문장(직위 상자)", "책임자(직위 상자)", "준법감시인(직위 상자)",
         "글자층과 같음(공백 무시)", "검증 기록", "판독 표", "(판독)",
         # COMMON 지침의 표 이름(3-1 절 제목)·메타 CSV 칸 이름
         "준법감시인(준법지원인) 지원조직", "감사위원회 지원조직", "찾은곳"}

probs, notes = [], []
stat = {}


def ws(s):
    return re.sub(r"\s+", "", (s or "").replace("<br>", "\n"))


def dot(s):
    return (s or "").replace("ㆍ", "·").replace("・", "·").replace("‧", "·").replace("•", "·")


def norm(s):
    return dot(ws(s))


class Text:
    def __init__(self, path):
        self.path = path
        self.lines = open(path, encoding="utf-8").read().split("\n")
        self.page = [0] * (len(self.lines) + 2)
        pg = 0
        for i, ln in enumerate(self.lines, 1):
            m = re.match(r"^=== p\.(\d+) ===\s*$", ln)
            if m:
                pg = int(m.group(1))
            self.page[i] = pg
        self.full = norm("\n".join(self.lines))

    def rng(self, a, b):
        return norm("\n".join(self.lines[max(a, 1) - 1:min(b, len(self.lines))]))


def load_csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def frags(s):
    return re.findall(r"「([^「」]+)」", s or "")


def bound(name, hay):
    pat = r"(?<![가-힣A-Za-z0-9])" + re.escape(name) + r"(?=$|[\s(),/·ㆍ\]]|장|소속|겸)"
    return re.search(pat, hay) is not None


def doc_key(seg, T):
    """조각 앞 글에서 가장 뒤에 나온 문서 이름으로 텍스트를 고름(없으면 사업보고서 본)."""
    best, pos = "본", -1
    for m in re.finditer(r"사업보고서|임원약력|연차보고서|경영공시|재공시|(2026\d{10})", seg):
        k = m.group(0)
        if m.group(1):
            key = k if k in T else ("본" if k in ("20260318001419", "20260319001006") else None)
        elif k in ("사업보고서", "임원약력"):
            key = "본"
        elif k == "연차보고서":
            key = "연차"
        elif k == "재공시":
            key = "재공시" if "재공시" in T else "연차"
        else:
            key = "경영공시"
        if key and m.start() >= pos:
            best, pos = key, m.start()
    return best


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


def meta_titles():
    s = set()
    for p in META:
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            for r in load_csv(fp):
                for v in r.values():
                    if v and len(v) < 120:
                        s.add(norm(v))
    return s


def check_company(co, cfg, titles):
    st = {k: 0 for k in ("quotes", "quote_page", "page_refs", "frag_ok", "frag_term", "frag_title", "frag_pandok",
                         "frag_search", "frag_bad", "exec_cells", "concur_cells", "support_cells", "md_unit_rows",
                         "md_exec_rows", "md_conc_rows", "md_support_rows", "md_head_rows", "cmp_rows", "name_match_pairs",
                         "name_match_cells", "local_frags")}
    T = {k: Text(os.path.join(TXT, v)) for k, v in cfg["texts"].items()}
    pool = [t.full for t in T.values()]
    for x in cfg.get("extra", []):
        pool.append(norm(open(os.path.join(ROOT, x), encoding="utf-8", errors="replace").read()))
    mdp = os.path.join(HND, f"14_{co}.md")
    md = open(mdp, encoding="utf-8").read().split("\n")
    rel = lambda p: os.path.relpath(p, ROOT)

    # ── 판독 이름(그림에서 읽은 글) 모음 ──
    pandok = set()
    for jf in (f"{co}_판독A.json", f"{co}_판독B.json"):
        j = json.load(open(os.path.join(ORG, jf), encoding="utf-8"))
        for u in j.get("단위", []) + j.get("units", []):
            for k in ("조직단위(판독)", "이름", "단위", "상자 글", "상자글"):
                if isinstance(u, dict) and u.get(k):
                    pandok.add(norm(u[k]))
        for s in j.get("보조_조직도_B", []):
            for u in s["units"]:
                pandok.add(norm(u["조직단위(판독)"]))
                for f in frags(u.get("비고", "")):
                    pandok.add(norm(f)); pandok.add(norm(u["조직단위(판독)"] + " " + f))
            nums = s.get("인원숫자(판독)")
            for v in (nums.values() if isinstance(nums, dict) else []):
                pandok.add(norm(v))
        for k in ("기준일(그림 안 글, 판독)",):
            for s in j.get("보조_조직도_B", []):
                if s.get(k):
                    pandok.add(norm(s[k]))
    for r in load_csv(os.path.join(ORG, f"{co}_판독대조.csv")):
        if "상자 글" in r["칸"] or "단위 이름" in r["칸"]:
            pandok.add(norm(re.sub(r"\s*\(상자 글:.*$", "", r["확정"])))
            pandok.add(norm(r["확정"].replace("(세로쓰기)", "")))
            m = re.match(r"^(.+?)\s+(\(.+\))$", r["확정"])
            if m:
                pandok.add(norm(m.group(2)))
    for u in load_csv(os.path.join(ORG, f"{co}_조직단위.csv")):
        pandok.add(norm(u["조직단위(판독)"]))

    def found(fr):
        parts = [p for p in re.split(r"…|\.\.\.", fr) if norm(p)]
        return bool(parts) and all(any(norm(p) in t for t in pool) for p in parts)

    def classify(fr, ctx, where):
        n = norm(fr)
        if found(fr):
            st["frag_ok"] += 1; return
        if fr in TERMS or n in {norm(x) for x in TERMS}:
            st["frag_term"] += 1; notes.append((co[:2], where, "term", fr)); return
        if n in titles:
            st["frag_title"] += 1; notes.append((co[:2], where, "title", fr)); return
        if n in pandok or n.replace("(세로쓰기)", "") in pandok or n in {x.strip("【】") for x in pandok}:
            st["frag_pandok"] += 1; notes.append((co[:2], where, "pandok", fr)); return
        if ("검색" in ctx or "0건" in ctx) and len(n) <= 15:
            st["frag_search"] += 1; notes.append((co[:2], where, "search", fr)); return
        st["frag_bad"] += 1
        probs.append((co, where, "F 원문에서 찾지 못한 「」 조각", fr[:120]))

    # ── Q: md 인용 블록 ──
    qre = re.compile(r"^\[(.+?) · p\.(\d+)(?:~(\d+))? · 줄 (\d+)–(\d+) · (dart_out/text/risk8/[^ ]+\.txt) · 원본 수집 .+? · 인용 (\w+)\]$")
    i = 0
    in_code = set()
    while i < len(md):
        m = qre.match(md[i])
        if m:
            src, p1, p2, a, b, f, qid = m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), int(m.group(5)), m.group(6), m.group(7)
            fp = os.path.join(ROOT, f)
            t = next((x for x in T.values() if x.path == fp), None) or Text(fp)
            j = i + 1
            while j < len(md) and not md[j].startswith("```"):
                j += 1
            k = j + 1
            while k < len(md) and not md[k].startswith("```"):
                k += 1
            body = md[j + 1:k]
            in_code.update(range(j, k + 1))
            st["quotes"] += 1
            if norm("\n".join(body)) != t.rng(a, b):
                probs.append((co, f"md {i+1}줄 인용 {qid}", "Q 인용 블록 ≠ 텍스트 줄 범위(공백 무시)", f"{f} {a}–{b}"))
            if t.page[a] != p1 and not (md[j + 1].startswith("=== p.") if j + 1 < len(md) else False):
                probs.append((co, f"md {i+1}줄 인용 {qid}", "Q 쪽 표기 ≠ 시작 줄 쪽 표지", f"p.{p1} vs 줄{a} p.{t.page[a]}"))
            elif p2 and t.page[b] != int(p2):
                probs.append((co, f"md {i+1}줄 인용 {qid}", "Q 쪽 표기(끝) ≠ 끝 줄 쪽 표지", f"p.{p2} vs 줄{b} p.{t.page[b]}"))
            else:
                st["quote_page"] += 1
            i = k + 1
            continue
        i += 1

    # ── P: 쪽·줄 표기 ──
    pre_ = re.compile(r"p\.(\d+)(?:~(\d+))?(?: \(그림[^)]*\))? (?:· )?줄 (\d+)(?:[–-](\d+))?")

    def check_pages(s, where):
        if (s or "").startswith("|"):
            for c in s.strip()[1:-1].split(" | "):
                check_pages(c, where)
            return
        for m in pre_.finditer(s or ""):
            key = doc_key(s[:m.start()], T)
            t = T[key]
            p1, p2, a, b = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
            st["page_refs"] += 1
            if a > len(t.lines):
                probs.append((co, where, "P 줄 번호가 텍스트 밖", f"{key} 줄{a}")); continue
            if t.page[a] != p1:
                probs.append((co, where, "P 쪽 표기 ≠ 줄의 쪽 표지", f"{key} p.{p1} 줄{a} → p.{t.page[a]}"))
            if p2 and b and t.page[int(b)] != int(p2):
                probs.append((co, where, "P 끝 쪽 표기 ≠ 끝 줄 쪽 표지", f"{key} p.{p2} 줄{b} → p.{t.page[int(b)]}"))

    # ── L: 같은 칸(또는 짝 출처 칸)·같은 표 행의 「」 조각이 그 칸이 적은 줄 범위 안에 있는지 ──
    #    (줄 범위 a–b 는 ±3줄, 한 줄 표기 「줄 L」 은 표 행이 여러 줄로 풀린 것을 감안해 L-3~L+16, 「인용 Qnn」 은 그 인용 블록 줄 범위)
    qmap = {}
    for ln in md:
        mq = qre.match(ln)
        if mq:
            fp = os.path.join(ROOT, mq.group(6))
            key = next((k for k, x in T.items() if x.path == fp), None)
            if key:
                qmap[mq.group(7)] = (key, int(mq.group(4)), int(mq.group(5)))
    bare = re.compile(r"줄 (\d+)(?:[–-](\d+))?")

    def windows(s):
        out = []
        if (s or "").startswith("|"):
            for c in s.strip()[1:-1].split(" | "):
                out += windows(c)
            return out
        for m in bare.finditer(s or ""):
            t = T[doc_key(s[:m.start()], T)]
            a = int(m.group(1)); b = int(m.group(2) or 0)
            out.append(t.rng(a - 3, (b + 3) if b else (a + 16)))
        for m in re.finditer(r"인용 ([QA]\d+b?)", s or ""):
            if m.group(1) in qmap:
                k, a, b = qmap[m.group(1)]
                out.append(T[k].rng(a - 1, b + 1))
        return out

    unames = {norm(u["조직단위(판독)"]) for u in load_csv(os.path.join(ORG, f"{co}_조직단위.csv"))}

    def local(frs, wins, where):
        if not wins:
            return
        for fr in frs:
            n = norm(fr)
            if not found(fr) or len(n) < 4 or n in titles or n in unames:
                continue
            parts = [norm(p) for p in re.split(r"…|\.\.\.", fr) if norm(p)]
            st["local_frags"] += 1
            if not all(any(p in w for w in wins) for p in parts):
                probs.append((co, where, "L 「」 조각이 이 칸·행이 적은 줄 범위 밖", fr[:100]))

    LROWS = set()
    for h in ("| 조직단위(판독) | 공시인원", "| 단위 | 표기 | 출처 |", "| 표 | 성명 | 직위 |", "| 표 | 겸직대상자(원문) |",
              "| 종류 | 부서(팀)명 |", "| 성명 | 기간(원문) |"):
        LROWS |= {ln - 1 for ln, _ in md_tables(md, h)}
    # ── F/P: md 전체(코드 블록 밖) ──
    rec0 = next((i for i, l in enumerate(md) if l.startswith("## 7) 검증 기록")), len(md))
    for n, ln in enumerate(md):
        if n in in_code:
            continue
        check_pages(ln, f"md {n+1}줄")
        if n >= rec0:
            # 7) 검증 기록: 고치기 전 글·검색어·칸 이름을 적은 곳이라 「」 조각은 원문 대조에서 빼고 따로 셈(쪽 표기는 위에서 검사)
            for fr in frags(ln):
                st["frag_record"] = st.get("frag_record", 0) + 1
            continue
        if ln.startswith("|") and n in LROWS:
            local([f for f in frags(ln)], windows(ln), f"md {n+1}줄(표 행)")
        for fr in frags(ln):
            classify(fr, ln, f"md {n+1}줄")

    # ── CSV 읽기 ──
    units = load_csv(os.path.join(ORG, f"{co}_조직단위.csv"))
    execs = load_csv(os.path.join(ORG, f"{co}_임원겸직.csv"))
    sups = load_csv(os.path.join(ORG, f"{co}_지원조직.csv"))
    cmp_ = load_csv(os.path.join(ORG, f"{co}_판독대조.csv"))
    for name, rows in (("조직단위", units), ("임원겸직", execs), ("지원조직", sups), ("판독대조", cmp_)):
        for ri, r in enumerate(rows, 2):
            for col, v in r.items():
                if col in ("판독A", "판독B", "확정", "확정 방법(확대 그림 파일·dpi·clip)"):
                    continue
                check_pages(v, f"{name} CSV {ri}행 {col}")
                for fr in frags(v):
                    classify(fr, v, f"{name} CSV {ri}행 {col}")

    PAIRS = {"조직단위": [("인원_내역(원문)", "인원_출처"), ("대응_근거(담당업무 원문)", "대응_근거(담당업무 원문)"),
                        ("임원_겸직(원문)", "임원_겸직(원문)")],
             "임원겸직": [("비고", "출처")], "지원조직": [("기준일", "출처")]}
    for name, rows in (("조직단위", units), ("임원겸직", execs), ("지원조직", sups)):
        for ri, r in enumerate(rows, 2):
            for col, src in PAIRS[name]:
                v = r.get(col) or ""
                frs = [f for f in frags(v) if "(판독)" not in v[max(0, v.find("「" + f) - 12):v.find("「" + f)]]
                local(frs, windows(r.get(src) or ""), f"{name} CSV {ri}행 {col}")

    # ── T: 임원겸직 CSV 원문 칸 ──
    t0 = T["본"]
    for ri, r in enumerate(execs, 2):
        src = r["출처"]
        m = re.search(r"임원 표 p\.(\d+) 줄 (\d+)", src)
        if m:
            L = int(m.group(2))
            win = t0.rng(L - 2, L + 14)
            for col in ("성명", "직위", "담당업무(원문)"):
                for piece in (r[col] or "").split("\n"):
                    if not norm(piece):
                        continue
                    st["exec_cells"] += 1
                    if norm(piece) not in win:
                        probs.append((co, f"임원겸직 CSV {ri}행 {col}", "T 원문 칸이 임원 표 줄 근처에 없음", f"{piece} (줄 {L})"))
            for col in ("등기", "상근"):
                st["exec_cells"] += 1
                if norm(r[col]) and norm(r[col]) not in win and norm(r[col]) != norm("미등기"):
                    probs.append((co, f"임원겸직 CSV {ri}행 {col}", "T 등기·상근 칸이 임원 표 줄 근처에 없음", f"{r[col]} (줄 {L})"))
        m2 = re.search(r"겸직 표 p\.(\d+) 줄 (\d+)", src)
        if m2:
            L = int(m2.group(2))
            win = t0.rng(L - 3, L + 6)
            for col in ("겸직회사", "겸직회사_직위", "상근여부"):
                for piece in (r[col] or "").split("\n"):
                    if not norm(piece):
                        continue
                    st["concur_cells"] += 1
                    if norm(piece) not in win:
                        probs.append((co, f"임원겸직 CSV {ri}행 {col}", "T 겸직 칸이 겸직 표 줄 근처에 없음", f"{piece} (줄 {L})"))
        m3 = re.search(r"임원약력 p\.(\d+) 줄 (\d+) 「([^」]+)」", src)
        if m3:
            L = int(m3.group(2)); st["concur_cells"] += 1
            if norm(m3.group(3)) not in t0.rng(L, L):
                probs.append((co, f"임원겸직 CSV {ri}행 출처", "T 임원약력 인용이 그 줄에 없음", m3.group(3)))
            if t0.page[L] != int(m3.group(1)):
                probs.append((co, f"임원겸직 CSV {ri}행 출처", "T 임원약력 쪽 표기 틀림", f"p.{m3.group(1)} 줄{L}"))

    # ── S: 지원조직 CSV ──
    for ri, r in enumerate(sups, 2):
        m = re.search(r"p\.(\d+)(?:~(\d+))? · 줄 (\d+)–(\d+)", r["출처"])
        if not m:
            continue
        t = T[doc_key(r["출처"][:m.start()], T)]
        a, b = int(m.group(3)), int(m.group(4))
        win = t.rng(a - 1, b)
        for col in ("부서(팀)명", "직위(근속연수)", "주요 활동(원문)"):
            v = r[col]
            if not v or "판독" in v or "나오지 않음" in v or "추출 범위에 없음" in v or "(원문)" in v:
                continue
            for piece in v.split("\n"):
                if not norm(piece):
                    continue
                st["support_cells"] += 1
                mc = re.match(r"^\((.+)\)$", piece.strip())
                if mc and norm(piece) not in win:
                    # 칸 이름을 붙여 칸 여러 개를 합친 조각 — 낱말마다 줄 범위에 있는지
                    toks = [x for x in re.split(r"[,\s]+", mc.group(1)) if x]
                    if all(norm(x) in win for x in toks):
                        notes.append((co[:2], f"지원조직 CSV {ri}행 {col}", "composite", piece)); continue
                if norm(piece) not in win:
                    probs.append((co, f"지원조직 CSV {ri}행 {col}", "S 원문 칸이 출처 줄 범위에 없음", f"{piece[:60]} ({a}–{b})"))

    # ── M: CSV ↔ md ──
    ukey = {}
    for u in units:
        k = re.match(r"^\[([A-Z]{1,2}\d\d)\]", u["비고"]).group(1)
        ukey[k] = u
    for ln, c in md_tables(md, "| 번호 | 상위단위(판독) |"):
        st["md_unit_rows"] += 1
        u = ukey.get(c[0])
        if not u:
            probs.append((co, f"md {ln}줄", "M 1-2 표 번호가 조직단위 CSV 에 없음", c[0])); continue
        par = "" if c[1] in ("—", "") else c[1]
        for mdv, csvv, lab in ((par, u["상위단위(판독)"], "상위단위"), (c[2], u["조직단위(판독)"], "조직단위"),
                               (c[3], u["단위_층위(판독)"], "층위"), (c[5], u["조직도_겸직표시(판독)"], "겸직표시")):
            if norm(mdv) != norm(csvv):
                probs.append((co, f"md {ln}줄 {c[0]}", f"M 1-2 표 {lab} ≠ 조직단위 CSV", f"{mdv} / {csvv}"))
    main_units = [u for u in units if "경영공시" in u["조직도_문서"]]
    nrow = len(md_tables(md, "| 번호 | 상위단위(판독) |"))
    if not (len(main_units) == nrow == cfg["units"]):
        probs.append((co, "단위 수", "C 조직단위 CSV(경영공시 행)·md 1-2 표·확정 단위 수가 다름", f"{len(main_units)}/{nrow}/{cfg['units']}"))
    # 3-4 공시인원 표
    for ln, c in md_tables(md, "| 조직단위(판독) | 공시인원"):
        st["md_head_rows"] += 1
        u = [x for x in units if x["조직단위(판독)"] == c[0]]
        if not u or norm(u[0]["공시인원(원문)"]) != norm(c[1]):
            probs.append((co, f"md {ln}줄", "M 3-4 표 공시인원 ≠ 조직단위 CSV", f"{c[0]} {c[1]}"))
    # 4 임원 표
    for ln, c in md_tables(md, "| 표 | 성명 | 직위 |"):
        st["md_exec_rows"] += 1
        cand = [r for r in execs if r["임원표_구분"] == c[0] and r["성명"] == c[1]]
        if not cand:
            probs.append((co, f"md {ln}줄", "M 4 임원 표 행이 임원겸직 CSV 에 없음", f"{c[0]} {c[1]}")); continue
        r = cand[0]
        for mdv, col in ((c[2], "직위"), (c[3], "등기"), (c[4], "상근"), (c[5], "담당업무(원문)"), (c[6], "대응_조직단위"), (c[7], "대응_방식")):
            if norm(mdv) != norm(r[col]):
                probs.append((co, f"md {ln}줄 {c[1]}", f"M 4 임원 표 {col} ≠ CSV", f"{mdv[:40]} / {r[col][:40]}"))
    # 5 겸직 표
    for ln, c in md_tables(md, "| 표 | 겸직대상자(원문) |"):
        st["md_conc_rows"] += 1
        nm = re.sub(r"\(.*$", "", c[1]).split()[-1]
        cand = [r for r in execs if r["겸직표_구분"] == c[0] and r["성명"] == nm and norm(r["겸직회사"]) == norm(c[2])
                and norm(r["겸직회사_직위"]) == norm(c[3]) and norm(r["상근여부"]) == norm(c[5])]
        if not cand:
            probs.append((co, f"md {ln}줄", "M 5 겸직 표 행이 임원겸직 CSV 에 없음", f"{c[0]} {c[1]} {c[2]} {c[3]}"))
    # 3-1 지원조직 표
    for ln, c in md_tables(md, "| 종류 | 부서(팀)명 | 직원수(명) |"):
        st["md_support_rows"] += 1
        cand = [r for r in sups if r["부서(팀)명"] == c[1] and norm(r["직원수"]) == norm(c[2])]
        if not cand or norm(cand[0]["직위(근속연수)"]) != norm(c[3].replace("(근속연수 4.1년, 지원업무 담당기간 4.1년)", "(근속연수 4.1년, 지원업무 담당기간 4.1년)")) \
                or norm(cand[0]["주요 활동(원문)"]) != norm(c[4]):
            probs.append((co, f"md {ln}줄", "M 3-1 지원조직 표 ≠ 지원조직 CSV", c[1]))

    # ── G: 2장 겸직 검색 표(걸린 줄 수·쪽)·「0건」 목록 재계산 ──
    lab = {"사업보고서(본)": "본", "연차보고서": "연차", "연차보고서(재공시)": "재공시", "경영공시": "경영공시"}

    def hits(key, term):
        t = T[key]
        return [t.page[i] for i, l in enumerate(t.lines, 1) if term in l]
    st["search_rows"] = 0
    for ln, c in md_tables(md, "| 문서 | 검색어 | 걸린 줄 수 | 걸린 쪽 |"):
        st["search_rows"] += 1
        h = hits(lab[c[0]], c[1])
        pages = ", ".join(f"p.{x}" for x in sorted(set(h)))
        if str(len(h)) != c[2] or pages != c[3]:
            probs.append((co, f"md {ln}줄", "G 검색 표 줄 수·쪽 재계산과 다름", f"{c[0]} {c[1]}: {len(h)} {pages}"))
    for ln in md:
        if ln.startswith("- 0건:"):
            for d, term in re.findall(r"(사업보고서\(본\)|연차보고서\(재공시\)|연차보고서|경영공시)「([^」]+)」", ln):
                st["search_rows"] += 1
                if hits(lab[d], term):
                    probs.append((co, "md 0건 목록", "G 「0건」이라 적었으나 걸리는 줄 있음", f"{d} {term}"))

    # ── R: 판독대조 ──
    B = json.load(open(os.path.join(ORG, f"{co}_판독B.json"), encoding="utf-8"))
    bnames = {norm(u["조직단위(판독)"]) for u in B["units"]}
    for s in B.get("보조_조직도_B", []):
        bnames |= {norm(u["조직단위(판독)"]) for u in s["units"]}
    cur = None
    for ri, r in enumerate(cmp_, 2):
        st["cmp_rows"] += 1
        for col in ("판독B", "확정", "확정 방법(확대 그림 파일·dpi·clip)"):
            if not (r[col] or "").strip():
                probs.append((co, f"판독대조 {ri}행", f"R {col} 빈칸", r["칸"]))
        if "판독B" not in (r["확정 방법(확대 그림 파일·dpi·clip)"] or "") and "B: " not in (r["확정 방법(확대 그림 파일·dpi·clip)"] or ""):
            probs.append((co, f"판독대조 {ri}행", "R 확정 방법에 B 그림 기록 없음", r["칸"]))
        m = re.match(r"^([A-Z]{1,2}\d\d)(?: \(보조 조직도 [^)]*\))? (.+)$", r["칸"])
        if not m:
            if r["칸"] == "조직 단위 수" and int(r["확정"]) != cfg["units"]:
                probs.append((co, "판독대조 단위 수", "R/C 확정 단위 수 ≠ 기대값", r["확정"]))
            continue
        key, fld = m.group(1), m.group(2)
        u = ukey.get(key)
        if fld in ("단위 이름", "상자 글"):
            bn = norm(re.sub(r"\s+\(.*$", "", r["판독B"]))
            if bn not in bnames and norm(r["판독B"]) not in bnames:
                probs.append((co, f"판독대조 {ri}행", "R 판독B 칸 이름이 판독B.json 에 없음", r["판독B"]))
        if not u:
            continue
        if fld in ("단위 이름", "상자 글"):
            nm = re.sub(r"\s*\(상자 글:.*$", "", r["확정"]).replace("(세로쓰기)", "")
            nm = re.sub(r"\s+\(.*$", "", nm) if key[:2] in ("KA",) else nm
            if norm(nm) != norm(u["조직단위(판독)"]):
                probs.append((co, f"판독대조 {ri}행", "R 확정 이름 ≠ 조직단위 CSV", f"{nm} / {u['조직단위(판독)']}"))
        elif fld in ("상위단위", "상위"):
            cv = "" if r["확정"].startswith("(없음") else r["확정"]
            if norm(cv) != norm(u["상위단위(판독)"]):
                probs.append((co, f"판독대조 {ri}행", "R 확정 상위 ≠ 조직단위 CSV", f"{cv} / {u['상위단위(판독)']}"))
        elif fld == "층위":
            if norm(r["확정"]) != norm(u["단위_층위(판독)"]):
                probs.append((co, f"판독대조 {ri}행", "R 확정 층위 ≠ 조직단위 CSV", f"{r['확정']} / {u['단위_층위(판독)']}"))
    for u in units:
        if "B 대기" in u["판독_대조"] or "A·B 대조" not in u["판독_대조"]:
            probs.append((co, "조직단위 CSV", "R 판독_대조 칸이 대조 결과가 아님", u["조직단위(판독)"]))

    # ── N: 이름 일치 ──
    for ri, r in enumerate(execs, 2):
        way = r["대응_방식"] or ""
        if "이름 일치" not in way:
            continue
        duty = r["담당업무(원문)"].replace("\n", " ")
        us = [x for x in r["대응_조직단위"].split("\n") if x.strip()]
        hit = [x for x in us if bound(x, duty)]
        st["name_match_cells"] += 1
        st["name_match_pairs"] += len(us)
        if way.strip() == "이름 일치" and len(hit) != len(us):
            probs.append((co, f"임원겸직 CSV {ri}행 {r['성명']}", "N 「이름 일치」인데 담당업무에 글자 그대로 없는 단위", ", ".join(x for x in us if x not in hit)))
        if way.strip() != "이름 일치" and not hit:
            probs.append((co, f"임원겸직 CSV {ri}행 {r['성명']}", "N 「… / 이름 일치」인데 글자 그대로 맞는 단위 0개", way))
        if "(판단)" not in way and len(hit) != len(us):
            probs.append((co, f"임원겸직 CSV {ri}행 {r['성명']}", "N 글자 일치 안 되는 단위가 있는데 (판단) 표시 없음", way))
    # 조직단위 CSV 대응
    for ri, u in enumerate(units, 2):
        way = u["대응_방식"] or ""
        if "이름 일치" not in way:
            continue
        name = u["조직단위(판독)"]
        hits, names_here = [], []
        for blk in re.split(r"\n(?=[가-힣]{2,4}: )", u["대응_근거(담당업무 원문)"]):
            mm = re.match(r"^([가-힣]{2,4}): ", blk)
            if not mm:
                continue
            names_here.append(mm.group(1))
            # 이 임원 블록 안 「」 조각 중 임원 CSV 담당업무 값과 같은 것만 담당업무로 봄
            dvals = {norm(r["담당업무(원문)"]) for r in execs if r["성명"] == mm.group(1)}
            if any(bound(name, f) for f in frags(blk) if norm(f) in dvals):
                hits.append(mm.group(1))
        st["name_match_cells"] += 1
        if way.strip() == "이름 일치" and len(hits) != len(names_here):
            probs.append((co, f"조직단위 CSV {ri}행 {name}", "N 「이름 일치」인데 글자 그대로 없는 임원", ", ".join(n for n in names_here if n not in hits)))
        if not hits:
            probs.append((co, f"조직단위 CSV {ri}행 {name}", "N 「이름 일치」 표시인데 글자 그대로 맞는 임원 0명", way))

    stat[co] = st
    return [mdp] + [os.path.join(ORG, f"{co}_{x}") for x in ("조직단위.csv", "임원겸직.csv", "지원조직.csv", "판독대조.csv", "판독A.json", "판독B.json")]


def main():
    titles = meta_titles()
    files = []
    for co, cfg in COS.items():
        files += check_company(co, cfg, titles)
    files += [os.path.abspath(__file__), os.path.join(ROOT, "scripts", "dart", "org14_g3.py")]
    vals = secret_values()
    for p in files:
        s = open(p, encoding="utf-8").read()
        for v in vals:
            if v in s:
                probs.append(("공통", os.path.relpath(p, ROOT), "K 인증값 문자열이 파일에 있음(값은 적지 않음)", ""))
        if re.search(r"crtfc_key=(?!\*\*\*)\w", s) or re.search(r"[?&]OC=(?!\*\*\*)\w", s):
            probs.append(("공통", os.path.relpath(p, ROOT), "K crtfc_key=/OC= 뒤에 가리지 않은 값", ""))
    nimg = 0
    for d in (ORG, HND):
        for dp, dn, fn in os.walk(d):
            for f in fn:
                if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                    nimg += 1
                    probs.append(("공통", os.path.relpath(os.path.join(dp, f), ROOT), "K 산출 폴더에 PDF·그림 파일", ""))
    lines = ["# verify14_g3 — 메리츠금융지주·한국투자금융지주 검증 결과",
             f"인증값 비교 대상 {len(vals)}개(값은 적지 않음), 검사한 파일 {len(files)}개, 산출 폴더 PDF·그림 {nimg}개", ""]
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
    head = [ln for ln in lines if not re.match(r"^(메리|한국) \|", ln)]
    print("\n".join(head[:80]))
    if len(head) > 80:
        print(f"... ({len(lines)} 줄 — {os.path.relpath(OUT, ROOT)})")
    sys.exit(0 if not probs else 1)


if __name__ == "__main__":
    main()
