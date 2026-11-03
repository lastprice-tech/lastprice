"""15차 비평 표본 대조(읽기 전용). 표본 40행(A15·B10·C8·D7)을 원문 텍스트의 해당 위치(절·표·쪽)와 맞댐."""
import csv, io, json, os, random, re, sys, zipfile
from collections import defaultdict

ROOT = "/home/user/lastprice"
H = os.path.join(ROOT, "handoff", "원문_지주운영방식")
OPS = os.path.join(ROOT, "dart_out", "ops15")
TXT = os.path.join(ROOT, "dart_out", "text", "ops15")
OUT = sys.argv[1]

def rd(f):
    return list(csv.DictReader(open(os.path.join(H, f), encoding="utf-8-sig")))

A = rd("원문_지주임원겸직.csv"); B = rd("원문_지주직원현황.csv")
C = rd("원문_지주설립_인력계획.csv"); D = rd("원문_지주위수탁.csv")

bs = {}
for r in csv.DictReader(open(os.path.join(OPS, "사업보고서_원문.csv"), encoding="utf-8-sig")):
    if r["text_path"]:
        bs[r["rcept_no"]] = os.path.join(ROOT, r["text_path"])
gov = {}
for g in ("g1", "g2"):
    for r in csv.DictReader(open(os.path.join(OPS, "연차보고서15_목록_%s.csv" % g), encoding="utf-8-sig")):
        p = os.path.join(TXT, "연차보고서__%s__%s__%s.md" % (r["회사"], r["공시연도"], r["공시유형"]))
        if r["파일_url"] and os.path.exists(p):
            gov.setdefault(r["파일_url"], p)
for r in json.load(open(os.path.join(OPS, "gov15_g1_work", "download.json"), encoding="utf-8")):
    if r.get("text_path"):
        for u in (r.get("실제_url"), r.get("파일_url")):
            if u:
                gov.setdefault(u, os.path.join(ROOT, r["text_path"]))
sec6 = defaultdict(list)
for r in csv.DictReader(open(os.path.join(OPS, "kit56", "연차보고서_섹션.csv"), encoding="utf-8-sig")):
    sec6[r["파일명"]].append(r)
t13 = zipfile.ZipFile(os.path.join(ROOT, "handoff", "13차_지주관리유형", "13차_지주관리유형_텍스트.zip"))

def ws(s):
    return re.sub(r"\s+", " ", s.replace("﻿", "")).strip()

def nn(s):
    return re.sub(r"[\s|\x00-\x1f]+", "", s.replace("<br>", "").replace("&cr;", ""))

def md_section(text, n):
    m = re.search(r"(?m)^### \[절 %d\].*$" % n, text)
    if not m:
        return None
    e = re.search(r"(?m)^### \[절 \d+\]", text[m.end():])
    return text[m.start(): m.end() + (e.start() if e else len(text))]

def md_table(text, m):
    i = text.find("[표 %d]\n" % m)
    if i < 0:
        return None
    j = text.find("[표 끝]", i)
    return text[i: j if j > 0 else len(text)]

def pages(text, a, b=None):
    b = b or a
    out = []
    for n in range(a, b + 1):
        m = re.search(r"(?m)^## p\.%d\b.*$" % n, text)
        if m:
            e = re.search(r"(?m)^## p\.\d+", text[m.end():])
            out.append(text[m.end(): m.end() + (e.start() if e else len(text))])
    return "\n".join(out) if out else None

def locate(row, task):
    """→ (위치 설명, 위치 블록 글, 문서 전체 글)."""
    page = row["page"]
    src = row.get("rcept_no_or_url") or row.get("rcept_no")
    dk = row["doc_kind"]
    if task == "C":
        p = os.path.join(TXT, "신고서__%s.md" % src)
        full = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    elif dk == "사업보고서":
        p = bs.get(src)
        full = open(p, encoding="utf-8").read() if p else None
    elif dk == "경영공시":
        n = next((x for x in t13.namelist() if x.endswith("텍스트/경영공시__%s.md" % row["corp_label"])), None)
        full = t13.read(n).decode("utf-8") if n else None
    else:
        m = re.search(r"파일 (.+?)\)$", row["doc_name"])
        if m and m.group(1) in sec6 and "시작페이지" in page:
            rs = sec6[m.group(1)]
            sp = re.search(r"시작페이지 (\d+)", page).group(1)
            blk = "\n".join(x["본문"] for x in sorted([x for x in rs if x["시작페이지"] == sp], key=lambda x: (int(x["섹션순번"] or 0), int(x["chunk_seq"] or 0))))
            full = "\n".join(x["본문"] for x in sorted(rs, key=lambda x: (int(x["섹션순번"] or 0), int(x["chunk_seq"] or 0))))
            return "sec6 시작페이지 %s" % sp, blk, full
        p = gov.get(src)
        full = open(p, encoding="utf-8").read() if p else None
    if full is None:
        return "출처 글 없음", None, None
    mp = re.search(r"p\.(\d+)(?:\s*~\s*p\.(\d+))?", page)
    mx = re.search(r"\[절 (\d+)\]", page)
    mt = re.findall(r"\[표 (\d+)\]", page)
    if mx and ("XML" in page):
        sec = md_section(full, int(mx.group(1)))
        if mt and sec is not None:
            blk = "\n".join(filter(None, (md_table(sec, int(t)) for t in mt)))
            return "절 %s 표 %s" % (mx.group(1), ",".join(mt)), blk or None, full
        return "절 %s" % mx.group(1), sec, full
    if mp:
        a = int(mp.group(1)); b = int(mp.group(2)) if mp.group(2) else a
        return "p.%d~%d" % (a, b), pages(full, a, b), full
    return "위치 해석 못 함", None, full

def judge(st, blk, full):
    if st == "문서에 없음":
        return "문서에 없음(대조 없음)"
    if blk is None and full is None:
        return "출처 글 없음"
    res = []
    if blk is not None:
        if st in blk: res.append("위치·글자 그대로")
        elif ws(st) in ws(blk): res.append("위치·공백만 다름")
        elif nn(st) in nn(blk): res.append("위치·공백/표지 제거 후 맞음")
        elif all(nn(p) in nn(blk) for p in st.split(" … ")): res.append("위치·「 … 」조각 맞음")
        else: res.append("위치 안에 없음")
    if full is not None and (blk is None or res[-1] == "위치 안에 없음"):
        if st in full: res.append("문서 전체엔 그대로")
        elif nn(st) in nn(full): res.append("문서 전체엔 정규화 후")
        elif all(nn(p) in nn(full) for p in st.split(" … ")): res.append("문서 전체엔 조각")
        else: res.append("문서 전체에도 없음")
    return " / ".join(res)

random.seed(1503)
def pick(rows, n, strata):
    out = []
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[strata(r)].append(i)
    keys = sorted(groups)
    random.shuffle(keys)
    k = 0
    while len(out) < n:
        g = groups[keys[k % len(keys)]]
        cand = [i for i in g if i not in out]
        if cand:
            out.append(random.choice(cand))
        k += 1
    return out

def pick2(rows, n_txt, n_none, strata):
    T = [r for r in rows if r["source_text"] != "문서에 없음"]
    N = [r for r in rows if r["source_text"] == "문서에 없음"]
    it = [rows.index(T[i]) for i in pick(T, n_txt, strata)]
    inn = [rows.index(N[i]) for i in pick(N, n_none, lambda r: r["corp_label"])] if n_none else []
    return it + inn
sel = {
    "A": pick2(A, 14, 1, lambda r: (r["doc_kind"], r["corp_label"])),
    "B": pick2(B, 8, 2, lambda r: (r["doc_kind"], r["corp_label"])),
    "C": pick2(C, 7, 1, lambda r: r["corp_label"]),
    "D": pick2(D, 5, 2, lambda r: (r["doc_kind"], r["corp_label"])),
}
# A 에 reason_text 원문 행 1개를 반드시 넣음(마지막 자리 교체)
rt = [i for i, r in enumerate(A) if r["reason_text"] != "문서에 없음"]
sel["A"][-2] = random.choice(rt)

res = []
for task, rows in (("A", A), ("B", B), ("C", C), ("D", D)):
    for i in sel[task]:
        r = rows[i]
        where, blk, full = locate(r, task)
        j = judge(r["source_text"], blk, full)
        extra = ""
        if task == "A" and r["reason_text"] != "문서에 없음":
            # reason_text: 연차보고서에서 이었으면 note 의 url·page 쪽에서 찾음
            rt_full = full
            m = re.search(r"reason_text 출처: 지배구조 연차보고서 (\S+) (p\.\d+|시작페이지 \d+)", r["note"])
            if m:
                fake = dict(r, rcept_no_or_url=m.group(1), page=m.group(2), doc_kind="지배구조 연차보고서")
                w2, b2, f2 = locate(fake, "A")
                extra = "reason_text: " + judge(r["reason_text"], b2, f2) + " (" + w2 + ")"
            else:
                extra = "reason_text: " + judge(r["reason_text"], blk, full)
        res.append({"task": task, "row": i + 2, "corp": r["corp_label"], "fy": r.get("fy", ""), "doc_kind": r["doc_kind"],
                    "src": r.get("rcept_no_or_url") or r.get("rcept_no"), "page": r["page"][:90], "where": where,
                    "judge": j, "extra": extra, "source_text": r["source_text"][:160], "note": r["note"][:220]})
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in res:
    print(x["task"], x["row"], x["corp"], x["fy"], x["doc_kind"][:6], "|", x["where"], "|", x["judge"], "|", x["extra"])
