# -*- coding: utf-8 -*-
"""15차 검증 — 경영공시 g2(메리츠·iM·BNK·JB·한국투자) FY2019~2025: 목록 dart_out/ops15/경영공시15_목록_g2.csv,
조각 dart_out/ops15/조각/B_mgmt_g2.csv·D_mgmt_g2.csv, 원문 md dart_out/ops15/원문/B|D/<회사>__FY<fy>__경영공시.md.

인자 없이 실행 → 결과 dart_out/ops15/verify15_mgmt_g2.txt. 문제 없으면 exit 0, 하나라도 있으면 exit 1.
`python3 scripts/dart/verify15_mgmt_g2.py`

대조(15차 새 원문 대조 규칙): 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 출처 텍스트(그 행 page 의 PDF 쪽 글,
dart_out/text/ops15/경영공시__<회사>__FY<fy>.md 「## p.N」)」 안에 이어서 그대로 있는지. PDF 출처라 「|」는 지우지 않음.
출처 쪽 글에서 보이지 않는 제어문자(U+0000~U+001F 중 줄바꿈·탭 말고)만은 지우고 보되, 그것을 지워야 맞는 행은 note 에 「제어문자 지움」이 있어야 함.
그 밖에: 열·utf-8-sig·필수 칸, 목록(35칸·sha256·쪽 수)과 출처·수집일 일치, 키워드·칸 글이 source_text 안에 있는지,
「문서에 없음」 행 반박 시도(키워드 다시 찾기), 원문 md 의 쪽 글 = 출처 쪽 글, 생성기 extract 를 다시 돌린 결과 = 파일, 비밀값 꼴 없음.
"""
import csv
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))
csv.field_size_limit(10 ** 9)
import ops15_mgmt_g2 as G  # noqa: E402

OPS = os.path.join("dart_out", "ops15")
OUT = os.path.join(OPS, "verify15_mgmt_g2.txt")
FR = {"B": os.path.join(OPS, "조각", "B_mgmt_g2.csv"), "D": os.path.join(OPS, "조각", "D_mgmt_g2.csv")}
COLS = {"B": G.B_COLS, "D": G.D_COLS}
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
WS = re.compile(r"\s")
KST = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$")
NONE = "문서에 없음"
B_KW = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
# 반박 시도용 오탐 목록(생성기와 따로 적음): 이 꼴이면 사람·조직 이동 낱말이 아님
B_FP = re.compile(r"완전적|전적인|전적으로|사전적|도전적|금전적|안전적|발전적|버전출")
STATUSES = {"받음", "받음(글 추출 실패)", "실패", "누리집에 없음", "막힘", "robots 금지"}

probs, info = [], []


def P(msg):
    probs.append(msg)


def nsw(s):
    return WS.sub("", s)


def read_csv(path):
    raw = open(path, "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf"):
        P("%s: utf-8-sig BOM 없음" % path)
    rows = list(csv.reader(open(path, encoding="utf-8-sig", newline="")))
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]


def pages_of(co, fy):
    return dict(G.load_pages(co, int(fy)))


def main():
    # ── 1. 목록 ──
    hdr, L = read_csv(G.LIST)
    if hdr != G.LIST_COLS:
        P("목록 열 다름: %s" % hdr)
    keys = [(r["corp_label"], r["fy"]) for r in L]
    want = [(c, str(y)) for c in G.COS for y in G.FYS]
    if sorted(keys) != sorted(want) or len(set(keys)) != 35:
        P("목록 회사×FY 35칸이 아님(%d행)" % len(L))
    lst = {(r["corp_label"], r["fy"]): r for r in L}
    for r in L:
        k = "%s FY%s" % (r["corp_label"], r["fy"])
        if r["status"] not in STATUSES:
            P("목록 %s status 이상: %s" % (k, r["status"]))
        for c in ("robots_verdict", "terms_note", "status", "note"):
            if not r[c]:
                P("목록 %s 빈 칸 %s" % (k, c))
        if r["status"].startswith("받음"):
            for c in ("period_원문", "url", "posted_at", "fetched_at", "bytes", "pages", "sha256"):
                if not r[c]:
                    P("목록 %s 빈 칸 %s" % (k, c))
            if not KST.match(r["fetched_at"]):
                P("목록 %s fetched_at 꼴 %s" % (k, r["fetched_at"]))
            f = G.dest_of(r["corp_label"], int(r["fy"]))
            if os.path.exists(f):
                b = open(f, "rb").read()
                if hashlib.sha256(b).hexdigest() != r["sha256"] or str(len(b)) != r["bytes"]:
                    P("목록 %s sha256·크기가 받은 파일과 다름" % k)
            else:
                info.append("목록 %s: 받은 파일이 이 컨테이너에 없어 sha256 대조 생략" % k)
            md = G.md_of(r["corp_label"], int(r["fy"]))
            if r["status"] == "받음":
                if not os.path.exists(md):
                    P("목록 %s 글 md 없음" % k)
                elif G.md_pages(md)[0] != r["pages"]:
                    P("목록 %s pages %s ≠ md 쪽 수 %s" % (k, r["pages"], G.md_pages(md)[0]))
        elif r["status"] == "실패" and not r["url"]:
            P("목록 %s 실패인데 url 없음" % k)

    # ── 2. 조각 ──
    rows = {}
    for w in ("B", "D"):
        hdr, R = read_csv(FR[w])
        if hdr != COLS[w]:
            P("%s 열 다름: %s" % (FR[w], hdr))
        rows[w] = R
    cache = {}
    for w in ("B", "D"):
        for i, r in enumerate(rows[w], 2):
            k = "%s %d행(%s FY%s %s)" % (w, i, r["corp_label"], r["fy"], r["page"])
            req = ["corp_label", "fy", "source_text", "doc_kind", "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
            req += ["keyword"] if w == "B" else []
            for c in req:
                if not r[c].strip():
                    P("%s 빈 칸 %s" % (k, c))
            if r["corp_label"] not in G.COS or not r["fy"].isdigit() or int(r["fy"]) not in G.FYS:
                P("%s 대상 밖 회사·FY" % k)
                continue
            if r["doc_kind"] != "경영공시":
                P("%s doc_kind %s" % (k, r["doc_kind"]))
            li = lst.get((r["corp_label"], r["fy"]))
            if not li or li["status"] != "받음":
                P("%s 목록 status 받음 아닌 FY 의 행" % k)
                continue
            if r["rcept_no_or_url"] != li["url"] or r["collected_at"] != li["fetched_at"]:
                P("%s 출처 URL·수집일이 목록과 다름" % k)
            if not KST.match(r["collected_at"]):
                P("%s collected_at 꼴" % k)
            for c in COLS[w]:
                if CTRL.search(r[c]):
                    P("%s 칸 %s 에 제어문자" % (k, c))
            key = (r["corp_label"], r["fy"])
            if key not in cache:
                cache[key] = pages_of(*key)
            pg = cache[key]
            if r["source_text"] == NONE:
                m = re.fullmatch(r"p\.1~p\.(\d+) 전체\(찾은 범위, PDF 쪽 — 해당 글 없음\)", r["page"])
                if not m or m.group(1) != li["pages"]:
                    P("%s 「문서에 없음」 page 꼴·쪽 수" % k)
                if "찾은 범위" not in r["note"] or "검색어" not in r["note"]:
                    P("%s 「문서에 없음」 note 에 찾은 범위·검색어 없음" % k)
                continue
            m = re.fullmatch(r"p\.(\d+)", r["page"])
            if not m or int(m.group(1)) not in pg:
                P("%s page 꼴·범위" % k)
                continue
            pn = int(m.group(1))
            st = nsw(r["source_text"])
            src_raw, src = nsw(pg[pn]), nsw(CTRL.sub("", pg[pn]))
            if len(r["source_text"]) > 2000:
                P("%s source_text 2,000자 넘음" % k)
            if st not in src:
                where = [p for p, t in pg.items() if st in nsw(CTRL.sub("", t))]
                P("%s source_text 가 출처 쪽 글에 이어서 없음%s" % (k, (" — 실제 쪽 p.%s" % where) if where else ""))
            elif st not in src_raw and "제어문자 지움" not in r["note"]:
                P("%s 제어문자를 지워야 맞는데 note 에 「제어문자 지움」 없음" % k)
            if w == "B":
                if r["keyword"] not in B_KW or r["keyword"] not in st:
                    P("%s keyword %s 가 source_text 에 없음" % (k, r["keyword"]))
                if r["employees_total"] or r["regular"] or r["contract"] or "직원 수는 같은 FY 사업보고서 행" not in r["note"]:
                    P("%s 직원 수 칸·note 규칙" % k)
            else:
                if not G.D_RE.search(st):
                    P("%s D 검색어가 source_text 에 없음" % k)
                for c in ("contract_type", "amount"):
                    if r[c] and nsw(r[c]) not in st and not all(nsw(x) in st for x in r[c].split("·")):
                        P("%s %s 「%s」 가 source_text 에 없음" % (k, c, r[c]))
                if r["counterparty"]:
                    near = src + nsw(CTRL.sub("", pg.get(pn - 1, "")))
                    if any(nsw(x) not in near for x in r["counterparty"].split("·")):
                        P("%s counterparty 「%s」 가 그 쪽(또는 앞 쪽)에 없음" % (k, r["counterparty"]))
    # FY 마다 B·D 행이 있는지, 「문서에 없음」 행은 그 FY 에 다른 행이 없을 때만
    for w in ("B", "D"):
        by = {}
        for r in rows[w]:
            by.setdefault((r["corp_label"], r["fy"]), []).append(r)
        for key, li in lst.items():
            got = by.get(key, [])
            if li["status"] == "받음" and not got:
                P("%s %s FY%s: 받은 FY 인데 행 없음" % (w, key[0], key[1]))
            if li["status"] != "받음" and got:
                P("%s %s FY%s: 받지 못한 FY 인데 행 있음" % (w, key[0], key[1]))
            if any(r["source_text"] == NONE for r in got) and len(got) != 1:
                P("%s %s FY%s: 「문서에 없음」 행과 다른 행이 함께 있음" % (w, key[0], key[1]))

    # ── 3. 「문서에 없음」 반박 시도 ──
    for r in rows["B"]:
        if r["source_text"] != NONE:
            continue
        pg = cache[(r["corp_label"], r["fy"])]
        for pn, t in pg.items():
            n = nsw(CTRL.sub("", t))
            for kw in B_KW:
                for m in re.finditer(kw, n):
                    if not B_FP.search(n[max(0, m.start() - 3):m.end() + 3]):
                        P("B 「문서에 없음」 반박: %s FY%s p.%d 에 「%s」(%s)" % (r["corp_label"], r["fy"], pn, kw, n[max(0, m.start() - 15):m.end() + 15]))
    for r in rows["D"]:
        if r["source_text"] != NONE:
            continue
        ud, _ = G.units(r["corp_label"], int(r["fy"]), "D")
        bad = [u for u in ud if u["rel"]]
        if bad:
            P("D 「문서에 없음」 반박: %s FY%s 에 관련 행 %d곳" % (r["corp_label"], r["fy"], len(bad)))
        # 독립 점검: 지주 이름 + 업무위탁·위수탁이 한 쪽 안 가까이(40자) 있는 곳
        for pn, t in cache[(r["corp_label"], r["fy"])].items():
            n = nsw(CTRL.sub("", t))
            for m in re.finditer(r"업무위탁|위[ㆍ·․・]?수탁", n):
                w40 = n[max(0, m.start() - 40):m.end() + 40]
                if "지주" in w40 and not G.D_EXCL.search(w40):
                    info.append("D 「문서에 없음」 참고: %s FY%s p.%d 「…%s…」 — 생성기 판정: 지주·계열사 사이 아님(같은 문장·표 행 기준)"
                                % (r["corp_label"], r["fy"], pn, w40))

    # ── 4. 원문 md ──
    for w in ("B", "D"):
        need = {}
        for r in rows[w]:
            if r["source_text"] != NONE:
                need.setdefault((r["corp_label"], r["fy"]), []).append(r)
        d = os.path.join(OPS, "원문", w)
        have = {f for f in os.listdir(d) if re.fullmatch(r"(.+)__FY(\d{4})__경영공시\.md", f)
                and f.split("__")[0] in G.COS and int(f.split("__")[1][2:]) in G.FYS}   # 2026.2Q(13차) 등 다른 조각의 md 는 뺌
        for (co, fy), rs in need.items():
            f = "%s__FY%s__경영공시.md" % (co, fy)
            if f not in have:
                P("원문 %s/%s 없음" % (w, f))
                continue
            s = open(os.path.join(d, f), encoding="utf-8").read()
            secs = {int(m.group(1)): m.group(2) for m in re.finditer(r"^## [^\n]* — p\.(\d+)\n\n- 출처: [^\n]*\n\n```text\n(.*?)\n```", s, re.S | re.M)}
            pg = cache[(co, fy)]
            for pn, body in secs.items():
                if nsw(body) != nsw(CTRL.sub("", pg[pn])):
                    P("원문 %s/%s p.%d 글이 출처 쪽 글과 다름" % (w, f, pn))
            for r in rs:
                pn = int(r["page"][2:])
                if pn not in secs:
                    P("원문 %s/%s 에 p.%d 절 없음" % (w, f, pn))
                elif nsw(r["source_text"]) not in nsw(secs[pn]):
                    P("원문 %s/%s p.%d 에 source_text 없음" % (w, f, pn))
            if sorted(secs) != sorted({int(r["page"][2:]) for r in rs}):
                P("원문 %s/%s 절 쪽이 조각 행 쪽과 다름" % (w, f))
            if re.search(r"(?m)^- 출처: (.*?) · 문서: ", s) and not all(r["rcept_no_or_url"] in s for r in rs):
                P("원문 %s/%s 출처 줄 URL 이 조각과 다름" % (w, f))
        extra = have - {"%s__FY%s__경영공시.md" % k for k in need}
        if extra:
            P("원문 %s 에 행 없는 md: %s" % (w, sorted(extra)))

    # ── 5. 생성기 다시 돌린 결과 = 파일 ──
    B2, D2, _ = G.build()
    for w, rs2 in (("B", B2), ("D", D2)):
        if [{c: r[c] for c in COLS[w]} for r in rs2] != rows[w]:
            P("%s 조각이 생성기 extract 다시 돌린 결과와 다름" % w)

    # ── 6. 비밀값 꼴 ──
    key = os.environ.get("DART_API_KEY", "")
    files = [G.LIST, FR["B"], FR["D"]] + [os.path.join(OPS, "원문", w, f) for w in ("B", "D")
                                         for f in os.listdir(os.path.join(OPS, "원문", w)) if re.fullmatch(r".+__FY\d{4}__경영공시\.md", f)
                                         and f.split("__")[0] in G.COS]
    files += [os.path.join("scripts", "dart", f) for f in ("ops15_mgmt_g2.py", "ops15_mgmt_g2_pdf2md.py", "verify15_mgmt_g2.py")]
    for f in files:
        s = open(f, encoding="utf-8", errors="replace").read()
        if (key and key in s) or re.search(r"crtfc_key=[0-9a-zA-Z]", s) or re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])", s):
            P("비밀값 꼴: %s" % f)

    # ── 결과 ──
    nb = len(rows["B"])
    nd = len(rows["D"])
    nb0 = sum(r["source_text"] == NONE for r in rows["B"])
    nd0 = sum(r["source_text"] == NONE for r in rows["D"])
    st = {}
    for r in L:
        st[r["status"]] = st.get(r["status"], 0) + 1
    out = ["# verify15_mgmt_g2 — %s" % G.now(), "",
           "목록 35칸: " + ", ".join("%s %d" % kv for kv in sorted(st.items())),
           "B_mgmt_g2.csv %d행(「문서에 없음」 %d) · D_mgmt_g2.csv %d행(「문서에 없음」 %d)" % (nb, nb0, nd, nd0),
           "대조 규칙: 공백·줄바꿈만 지운 source_text ⊂ 공백·줄바꿈만 지운 그 쪽 PDF 글(「|」 안 지움, 제어문자는 note 표시 행만)", ""]
    out += ["## 문제 %d건" % len(probs)] + ["- " + p for p in probs] + ["", "## 참고 %d건" % len(info)] + ["- " + x for x in info]
    out.append("")
    out.append("판정: %s" % ("통과(exit 0)" if not probs else "실패(exit 1)"))
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out[:6]))
    print("문제 %d건 · 참고 %d건 → %s" % (len(probs), len(info), OUT))
    for p in probs[:20]:
        print(" -", p[:200])
    return 0 if not probs else 1


if __name__ == "__main__":
    sys.exit(main())
