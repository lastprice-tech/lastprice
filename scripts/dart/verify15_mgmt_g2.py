# -*- coding: utf-8 -*-
"""15차 검증 — 경영공시 g2(메리츠·iM·BNK·JB·한국투자) FY2019~FY2025: 목록 dart_out/ops15/경영공시15_목록_g2.csv,
조각 dart_out/ops15/조각/B_mgmt_g2.csv·D_mgmt_g2.csv, 원문 md dart_out/ops15/원문/B|D/<회사>__FY<fy>__경영공시.md.

인자 없이 실행 → 결과 dart_out/ops15/verify15_mgmt_g2.txt. 문제 없으면 exit 0, 하나라도 있으면 exit 1.
`python3 scripts/dart/verify15_mgmt_g2.py`

독립 검증(2026-11-03 KST 다시 씀): 출처 쪽 글은 이 스크립트가 md(dart_out/text/ops15/경영공시__<회사>__FY<fy>.md 「## p.N」)를
직접 읽어 나눔(생성기 load_pages·units·검색어를 쓰지 않음). 생성기에서는 경로 함수(dest_of·md_of)와 「다시 돌린 결과 = 파일」 대조용
build() 만 씀.
 (a) 대조(15차 새 원문 대조 규칙): 「공백·줄바꿈만 지운 source_text」가 「공백·줄바꿈만 지운 그 행 page 쪽 글」 안에 이어서 그대로
     있는지(PDF 출처라 「|」는 지우지 않음). 보이지 않는 제어문자(U+0000~U+001F 중 줄바꿈·탭 말고)를 지워야 맞는 행은 note 에
     「제어문자 지움」이 있어야 함. 2,000자 넘는 행, 출처에 없는 「 | 」·「…」 꼴도 이 대조에서 걸림.
 (b) 열(COMMON15 지정 열 그대로)·utf-8-sig·필수 칸(출처·page·doc_name·collected_at), 목록 URL·수집일과 같은지, sha256·크기·쪽 수.
 (c) 빠짐: md 마다 B 6개 키워드(겸직·파견·출향·전출·전적·겸무)를 직접 찾아 B 행이 덮지 않는 자리 = 문제(낱말 조각 오탐 꼴만 뺌).
     D 는 「위탁」「수탁」「용역」「자문」「전산」「공동」을 직접 찾아, D 행이 덮지 않고 앞뒤 40자 안에 「지주」가 있는 자리를
     아래 REVIEWED(검증이 원문을 보고 정한 제외 갈래)로 설명 못 하면 문제.
 (d) 「문서에 없음」 행: page 꼴·note 의 찾은 범위, 위 (c) 가 그 FY 에도 그대로 적용됨(반박 시도). B 는 넓은 검색어(겸임·겸업·인사교류·
     인력교류·전보·지원인력)도 찾아 참고로 적음.
 (e) 목록: 회사×FY 35칸, status 와 파일 있음/없음이 맞는지(받음 = PDF·md 있고 sha256 같음, 실패 = PDF 없음·.fail.json 있음),
     robots·이용약관 기록, md 의 보고서 연도 = FY.
 (f) 비밀값 꼴 없음, PDF 가 git 추적 경로에 없음(raw·text 폴더는 git 무시).
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "dart"))
csv.field_size_limit(10 ** 9)
import ops15_mgmt_g2 as G  # noqa: E402  (경로 함수·build 대조만)

OPS = os.path.join("dart_out", "ops15")
OUT = os.path.join(OPS, "verify15_mgmt_g2.txt")
LIST = os.path.join(OPS, "경영공시15_목록_g2.csv")
FR = {"B": os.path.join(OPS, "조각", "B_mgmt_g2.csv"), "D": os.path.join(OPS, "조각", "D_mgmt_g2.csv")}
# COMMON15.md 지정 열(사용자 열 + doc_name·collected_at)
COLS = {"B": ["corp_label", "fy", "employees_total", "regular", "contract", "keyword", "source_text", "doc_kind", "rcept_no_or_url",
              "page", "note", "doc_name", "collected_at"],
        "D": ["corp_label", "fy", "counterparty", "contract_type", "amount", "source_text", "doc_kind", "rcept_no_or_url", "page",
              "note", "doc_name", "collected_at"]}
LIST_COLS = ["corp_label", "fy", "period_원문", "url", "posted_at", "fetched_at", "bytes", "pages", "sha256",
             "robots_verdict", "terms_note", "status", "note"]
COS = ["메리츠금융지주", "iM금융지주", "BNK금융지주", "JB금융지주", "한국투자금융지주"]
FYS = range(2019, 2026)
TXT = os.path.join("dart_out", "text", "ops15")
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
WS = re.compile(r"\s")
KST = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$")
NONE = "문서에 없음"
B_KW = ["겸직", "파견", "출향", "전출", "전적", "겸무"]
B_RX = re.compile("|".join(B_KW))
# 낱말 조각 오탐(사람·조직 이동 뜻이 아님): 완전적용·전적인 책임·사전적·도전적·금전적 … / 버전출시
B_FP = re.compile(r"완전적|전적인|전적으로|사전적|도전적|금전적|안전적|발전적|버전출")
B_WIDE = re.compile(r"겸임|겸업|인사교류|인력교류|전보|지원인력")
V_D = re.compile(r"위탁|수탁|용역|자문|전산|공동")
# D: 행이 덮지 않고 앞뒤 40자 안에 「지주」가 있는 자리 — 검증이 원문을 보고 정한 제외 갈래(앞뒤 15자 창에서 찾음)
REVIEWED = [
    ("회사·업 이름 속 낱말(투자자문업·…투자자문유한공사·…위탁관리부동산투자회사)", re.compile(r"투자자문|위탁관리부동산투자회사")),
    ("증권 영업·운용 낱말(위탁매매·위탁중개·위탁운용보수 — 계열사끼리 거래 표 포함)", re.compile(r"위탁매매|위탁중개|위탁운용")),
    ("임원 경력·학력 칸(전산학 학사·경영자문위원회 회장)", re.compile(r"전산학|경영자문위")),
    ("목차·이용자편람 줄(「공동광고·시설물 등 공동이용 현황」 절 이름)", re.compile(r"공동광고[·・]?시설물등공동이용현황|공동광고현황<이용자편람")),
    ("기부·출연 표(사회복지공동모금회·은행 공동 사회공헌)", re.compile(r"공동모금회|은행공동사회공헌")),
    ("감사 실시 횟수(공동감사)", re.compile(r"공동감사")),
    ("준법감시인 업무·사전검토 목록(광고(공동광고 포함)·보고 지원 및 자문)", re.compile(r"공동광고포함|보고지원및자문|각부서에대한자문")),
    ("거래 없음 표 칸(「공동영업수수료 ----」)", re.compile(r"공동영업수수료-{2,}")),
    ("직원 수 범위 각주(용역·파견 직원 제외)", re.compile(r"용역,파견|용역/파견")),
    ("계열사 연혁 표의 다른 회사 칸·자사 일(신용정보·유페이먼트·캐피탈 수탁 운영, 전산인트라넷·차세대전산시스템 구축, 전산소 가동, "
     "전산센터 이전)", re.compile(r"(?:신용정보|유페이먼트|캐피탈)(?:전산시스템|모바일홈페이지|대량메일발송시스템|홈페이지)수탁운|"
                               r"전산인트라넷|차세대전산시스템|전산소가동|전산센[터타]")),
]
YR = re.compile(r"(20\d\d)(?:년?(?:\(주\))?(?:BNK|JB|메리츠)금융지주현황|DGBFinancialGroupReport|iMFinancialGroupReport|AnnualReport|"
                r"\.12\.31|년12월31일)")

probs, info = [], []


def P(msg):
    probs.append(msg)


def nsw(s):
    return WS.sub("", s)


def nctl(s):
    return WS.sub("", CTRL.sub("", s))


def read_csv(path, cols):
    raw = open(path, "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf"):
        P("%s: utf-8-sig BOM 없음" % path)
    rows = list(csv.reader(open(path, encoding="utf-8-sig", newline="")))
    if rows[0] != cols:
        P("%s 열 다름: %s" % (path, rows[0]))
    for i, r in enumerate(rows[1:], 2):
        if len(r) != len(rows[0]):
            P("%s %d행 칸 수 %d" % (path, i, len(r)))
    return [dict(zip(rows[0], r)) for r in rows[1:]]


_PG = {}


def pages_md(co, fy):
    """md 를 이 스크립트가 직접 나눔: {쪽 번호: 쪽 글(「## p.N」 줄 다음부터 다음 「## p.」 앞까지)}."""
    k = (co, str(fy))
    if k not in _PG:
        s = open(os.path.join(TXT, "경영공시__%s__FY%s.md" % k), encoding="utf-8").read()
        parts = re.split(r"(?m)^## p\.(\d+)(?: \(글자 없음\))?\n", s)
        _PG[k] = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
    return _PG[k]


def covered(rows_on_page, n):
    iv = []
    for st in rows_on_page:
        for m in re.finditer(re.escape(st), n):
            iv.append((m.start(), m.end()))
    return iv


def main():
    # ── (e) 목록 ──
    L = read_csv(LIST, LIST_COLS)
    keys = [(r["corp_label"], r["fy"]) for r in L]
    want = [(c, str(y)) for c in COS for y in FYS]
    if sorted(keys) != sorted(want) or len(set(keys)) != 35:
        P("목록 회사×FY 35칸이 아님(%d행)" % len(L))
    lst = {(r["corp_label"], r["fy"]): r for r in L}
    got = [k for k in want if lst.get(k, {}).get("status") == "받음"]
    for r in L:
        k = "%s FY%s" % (r["corp_label"], r["fy"])
        for c in ("robots_verdict", "terms_note", "status", "note", "url"):
            if not r[c].strip():
                P("목록 %s 빈 칸 %s" % (k, c))
        if "robots.txt" not in r["robots_verdict"] or "약관" not in r["terms_note"]:
            P("목록 %s robots·이용약관 기록 꼴" % k)
        if "금지" in r["robots_verdict"] and r["status"] == "받음":
            P("목록 %s robots 금지인데 받음" % k)
        pdf = G.dest_of(r["corp_label"], int(r["fy"]))
        md = os.path.join(TXT, "경영공시__%s__FY%s.md" % (r["corp_label"], r["fy"]))
        if r["status"] == "받음":
            for c in ("period_원문", "posted_at", "fetched_at", "bytes", "pages", "sha256"):
                if not r[c]:
                    P("목록 %s 빈 칸 %s" % (k, c))
            if not KST.match(r["fetched_at"]):
                P("목록 %s fetched_at 꼴 %s" % (k, r["fetched_at"]))
            if os.path.exists(pdf):
                b = open(pdf, "rb").read()
                if hashlib.sha256(b).hexdigest() != r["sha256"] or str(len(b)) != r["bytes"]:
                    P("목록 %s sha256·크기가 받은 파일과 다름" % k)
                if not b.startswith(b"%PDF"):
                    P("목록 %s 받은 파일이 PDF 아님" % k)
            else:
                info.append("목록 %s: 받은 PDF 가 이 컨테이너에 없어 sha256 대조 생략" % k)
            if not os.path.exists(md):
                P("목록 %s 글 md 없음" % k)
                continue
            head = open(md, encoding="utf-8").readline()
            if r["sha256"] not in head or r["fetched_at"] not in head:
                P("목록 %s md 머리 줄의 sha256·수집 시각이 목록과 다름" % k)
            pg = pages_md(r["corp_label"], r["fy"])
            if str(len(pg)) != r["pages"] or sorted(pg) != list(range(1, len(pg) + 1)):
                P("목록 %s pages %s ≠ md 쪽 수 %d" % (k, r["pages"], len(pg)))
            yr = Counter(YR.findall(nctl("".join(pg.values())))).most_common(1)
            if not yr or yr[0][0] != r["fy"]:
                P("목록 %s md 의 보고서 연도 표기(%s)가 FY 와 다름" % (k, yr))
        else:
            if os.path.exists(pdf) or os.path.exists(md):
                P("목록 %s status %s 인데 PDF·md 가 있음" % (k, r["status"]))
            if r["status"] == "실패" and not os.path.exists(pdf + ".fail.json") and os.path.isdir(os.path.dirname(pdf)):
                P("목록 %s 실패 기록(.fail.json) 없음" % k)
            if r["status"] == "실패" and not r["note"].strip():
                P("목록 %s 실패 사유 없음" % k)
    for co in COS:
        d = os.path.join("dart_out", "raw", "mgmt15", co)
        if os.path.isdir(d) and not any(f.startswith("robots_") for f in os.listdir(d)):
            P("%s robots.txt 원본 기록 없음" % co)

    # ── (a)(b) 조각 ──
    rows = {w: read_csv(FR[w], COLS[w]) for w in ("B", "D")}
    for w in ("B", "D"):
        for i, r in enumerate(rows[w], 2):
            k = "%s %d행(%s FY%s %s)" % (w, i, r["corp_label"], r["fy"], r["page"])
            req = ["corp_label", "fy", "source_text", "doc_kind", "rcept_no_or_url", "page", "note", "doc_name", "collected_at"]
            req += ["keyword"] if w == "B" else []
            for c in req:
                if not r[c].strip():
                    P("%s 빈 칸 %s" % (k, c))
            if r["corp_label"] not in COS or not r["fy"].isdigit() or int(r["fy"]) not in FYS:
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
            if r["corp_label"] not in r["doc_name"] or "경영공시" not in r["doc_name"]:
                P("%s doc_name 꼴" % k)
            for c in COLS[w]:
                if CTRL.search(r[c]):
                    P("%s 칸 %s 에 제어문자" % (k, c))
            pg = pages_md(r["corp_label"], r["fy"])
            if r["source_text"] == NONE:
                m = re.fullmatch(r"p\.1~p\.(\d+) 전체\(찾은 범위, PDF 쪽 — 해당 글 없음\)", r["page"])
                if not m or m.group(1) != li["pages"]:
                    P("%s 「문서에 없음」 page 꼴·쪽 수" % k)
                if "찾은 범위" not in r["note"] or "검색어" not in r["note"]:
                    P("%s 「문서에 없음」 note 에 찾은 범위·검색어 없음" % k)
                if w == "B" and r["keyword"] != "없음":
                    P("%s 「문서에 없음」 행 keyword 가 「없음」 아님" % k)
                continue
            m = re.fullmatch(r"p\.(\d+)", r["page"])
            if not m or int(m.group(1)) not in pg:
                P("%s page 꼴·범위" % k)
                continue
            pn = int(m.group(1))
            st = nsw(r["source_text"])
            if len(r["source_text"]) > 2000:
                P("%s source_text 2,000자 넘음" % k)
            if st not in nsw(pg[pn]):
                if st in nctl(pg[pn]):
                    if "제어문자 지움" not in r["note"]:
                        P("%s 제어문자를 지워야 맞는데 note 에 「제어문자 지움」 없음" % k)
                else:
                    where = [p for p, t in pg.items() if st in nctl(t)]
                    P("%s source_text 가 출처 쪽 글에 이어서 없음%s" % (k, (" — 실제 쪽 p.%s" % where) if where else ""))
            if w == "B":
                if r["keyword"] not in B_KW or r["keyword"] not in st:
                    P("%s keyword %s 가 source_text 에 없음" % (k, r["keyword"]))
                if r["employees_total"] or r["regular"] or r["contract"] or "직원 수는 같은 FY 사업보고서 행" not in r["note"]:
                    P("%s 직원 수 칸·note 규칙" % k)
            else:
                if not V_D.search(st):
                    P("%s D 검색어가 source_text 에 없음" % k)
                if "지주" not in st and "(판단)" not in r["note"]:
                    P("%s source_text 에 지주 쪽 말이 없는데 note 에 (판단) 설명 없음" % k)
                for c in ("contract_type", "amount"):
                    if r[c] and nsw(r[c]) not in st and not all(nsw(x) in st for x in r[c].split("·")):
                        P("%s %s 「%s」 가 source_text 에 없음" % (k, c, r[c]))
                if r["counterparty"]:
                    near = nctl(pg[pn]) + nctl(pg.get(pn - 1, ""))
                    if any(nsw(x) not in near for x in r["counterparty"].split("·")):
                        P("%s counterparty 「%s」 가 그 쪽(또는 앞 쪽)에 없음" % (k, r["counterparty"]))
    # FY 마다 B·D 행이 있는지, 「문서에 없음」 행은 그 FY 에 다른 행이 없을 때만
    for w in ("B", "D"):
        by = {}
        for r in rows[w]:
            by.setdefault((r["corp_label"], r["fy"]), []).append(r)
        for key, li in lst.items():
            g = by.get(key, [])
            if li["status"] == "받음" and not g:
                P("%s %s FY%s: 받은 FY 인데 행 없음" % (w, key[0], key[1]))
            if li["status"] != "받음" and g:
                P("%s %s FY%s: 받지 못한 FY 인데 행 있음" % (w, key[0], key[1]))
            if any(r["source_text"] == NONE for r in g) and len(g) != 1:
                P("%s %s FY%s: 「문서에 없음」 행과 다른 행이 함께 있음" % (w, key[0], key[1]))
        dup = Counter((r["corp_label"], r["fy"], r["page"], r["source_text"], r.get("keyword", ""), r.get("counterparty", "")) for r in rows[w])
        for kk, v in dup.items():
            if v > 1:
                P("%s 같은 행 %d번: %s FY%s %s" % (w, v, kk[0], kk[1], kk[2]))

    # ── (c)(d) 빠짐·「문서에 없음」 반박 — md 를 직접 찾음 ──
    on = {"B": {}, "D": {}}
    for w in ("B", "D"):
        for r in rows[w]:
            if r["source_text"] != NONE and re.fullmatch(r"p\.\d+", r["page"]):
                on[w].setdefault((r["corp_label"], r["fy"], int(r["page"][2:])), []).append(nctl(r["source_text"]))
    none_fy = {w: {(r["corp_label"], r["fy"]) for r in rows[w] if r["source_text"] == NONE} for w in ("B", "D")}
    cat = Counter()
    nfp = Counter()
    for co, fy in got:
        for pn, t in pages_md(co, fy).items():
            n = nctl(t)
            ivb = covered(on["B"].get((co, fy, pn), []), n)
            for m in B_RX.finditer(n):
                if B_FP.search(n[max(0, m.start() - 3):m.end() + 3]):
                    nfp[m.group(0)] += 1
                    continue
                if not any(a <= m.start() and m.end() <= b for a, b in ivb):
                    P("B 빠짐: %s FY%s p.%d 「%s」(…%s…)%s" % (co, fy, pn, m.group(0), n[max(0, m.start() - 20):m.end() + 20],
                                                     " — 「문서에 없음」 반박" if (co, fy) in none_fy["B"] else ""))
            if (co, fy) in none_fy["B"]:
                for m in B_WIDE.finditer(n):
                    info.append("B 「문서에 없음」 넓은 검색어: %s FY%s p.%d 「%s」(…%s…)" % (co, fy, pn, m.group(0), n[max(0, m.start() - 20):m.end() + 20]))
            ivd = covered(on["D"].get((co, fy, pn), []), n)
            for m in V_D.finditer(n):
                if any(a <= m.start() and m.end() <= b for a, b in ivd):
                    cat["(덮임) D 행 안"] += 1
                    continue
                if "지주" not in n[max(0, m.start() - 40):m.end() + 40]:
                    cat["(지주 없음) 앞뒤 40자에 지주 없음"] += 1
                    continue
                win = n[max(0, m.start() - 15):m.end() + 15]
                hit = [name for name, rx in REVIEWED if rx.search(win)]
                if hit:
                    cat[hit[0]] += 1
                else:
                    P("D 빠짐: %s FY%s p.%d 「%s」(…%s…)%s" % (co, fy, pn, m.group(0), n[max(0, m.start() - 30):m.end() + 30],
                                                     " — 「문서에 없음」 반박" if (co, fy) in none_fy["D"] else ""))
    info.append("B 키워드 자리 중 낱말 조각 오탐으로 뺀 것: " + ", ".join("%s %d" % kv for kv in sorted(nfp.items())))
    info.append("D 검색어(위탁·수탁·용역·자문·전산·공동) 자리 갈래: " + "; ".join("%s %d" % kv for kv in sorted(cat.items())))

    # ── 원문 md ──
    for w in ("B", "D"):
        need = {}
        for r in rows[w]:
            if r["source_text"] != NONE:
                need.setdefault((r["corp_label"], r["fy"]), []).append(r)
        d = os.path.join(OPS, "원문", w)
        have = {f for f in os.listdir(d) if re.fullmatch(r"(.+)__FY(\d{4})__경영공시\.md", f)
                and f.split("__")[0] in COS and int(f.split("__")[1][2:]) in FYS}   # 2026.2Q(13차) 등 다른 조각의 md 는 뺌
        for (co, fy), rs in need.items():
            f = "%s__FY%s__경영공시.md" % (co, fy)
            if f not in have:
                P("원문 %s/%s 없음" % (w, f))
                continue
            s = open(os.path.join(d, f), encoding="utf-8").read()
            secs = {int(m.group(1)): m.group(2) for m in re.finditer(r"^## [^\n]* — p\.(\d+)\n\n- 출처: [^\n]*\n\n```text\n(.*?)\n```", s, re.S | re.M)}
            pg = pages_md(co, fy)
            for pn, body in secs.items():
                if nsw(body) != nctl(pg[pn]):
                    P("원문 %s/%s p.%d 글이 출처 쪽 글과 다름" % (w, f, pn))
            for r in rs:
                pn = int(r["page"][2:])
                if pn not in secs:
                    P("원문 %s/%s 에 p.%d 절 없음" % (w, f, pn))
                elif nctl(r["source_text"]) not in nsw(secs[pn]):
                    P("원문 %s/%s p.%d 에 source_text 없음" % (w, f, pn))
            if sorted(secs) != sorted({int(r["page"][2:]) for r in rs}):
                P("원문 %s/%s 절 쪽이 조각 행 쪽과 다름" % (w, f))
            if not all(r["rcept_no_or_url"] in s and r["collected_at"] in s for r in rs):
                P("원문 %s/%s 출처 줄 URL·수집일이 조각과 다름" % (w, f))
        extra = have - {"%s__FY%s__경영공시.md" % k for k in need}
        if extra:
            P("원문 %s 에 행 없는 md: %s" % (w, sorted(extra)))

    # ── 생성기 다시 돌린 결과 = 파일 ──
    B2, D2, _ = G.build()
    for w, rs2 in (("B", B2), ("D", D2)):
        if [{c: r[c] for c in COLS[w]} for r in rs2] != rows[w]:
            P("%s 조각이 생성기 extract 다시 돌린 결과와 다름" % w)

    # ── (f) 비밀값 꼴·PDF 가 git 추적 경로에 없는지 ──
    key = os.environ.get("DART_API_KEY", "")
    files = [LIST, FR["B"], FR["D"]] + [os.path.join(OPS, "원문", w, f) for w in ("B", "D")
                                     for f in os.listdir(os.path.join(OPS, "원문", w)) if re.fullmatch(r".+__FY\d{4}__경영공시\.md", f)
                                     and f.split("__")[0] in COS]
    files += [os.path.join("scripts", "dart", f) for f in ("ops15_mgmt_g2.py", "ops15_mgmt_g2_pdf2md.py", "verify15_mgmt_g2.py")]
    for f in files:
        s = open(f, encoding="utf-8", errors="replace").read()
        if (key and key in s) or re.search(r"crtfc_key=[0-9a-zA-Z]", s) or re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])", s) \
                or re.search(r"(?i)(api[_-]?key|secret|token|password)\s*[=:]\s*['\"]?[0-9A-Za-z]{16,}", s):
            P("비밀값 꼴: %s" % f)
    try:
        tracked = subprocess.run(["git", "ls-files", "-z", "--", "dart_out", "scripts"], capture_output=True, check=True).stdout.split(b"\0")
        pdfs = [x.decode("utf-8", "replace") for x in tracked if x.lower().endswith(b".pdf")]
        if pdfs:
            P("git 추적 PDF: %s" % pdfs[:5])
        for p in [G.dest_of(c, int(y)) for c, y in got] + [os.path.join(TXT, "경영공시__%s__FY%s.md" % k) for k in got]:
            if subprocess.run(["git", "check-ignore", "-q", "--", p]).returncode != 0:
                P("git 무시 폴더 밖: %s" % p)
    except Exception as e:  # git 없는 환경
        info.append("git 점검 생략: %s" % e)

    # ── 결과 ──
    nb, nd = len(rows["B"]), len(rows["D"])
    nb0 = sum(r["source_text"] == NONE for r in rows["B"])
    nd0 = sum(r["source_text"] == NONE for r in rows["D"])
    st = Counter(r["status"] for r in L)
    out = ["# verify15_mgmt_g2 — %s" % G.now(), "",
           "목록 35칸: " + ", ".join("%s %d" % kv for kv in sorted(st.items())),
           "B_mgmt_g2.csv %d행(「문서에 없음」 %d) · D_mgmt_g2.csv %d행(「문서에 없음」 %d)" % (nb, nb0, nd, nd0),
           "B 회사별: " + ", ".join("%s %d" % kv for kv in Counter(r["corp_label"] for r in rows["B"]).items())
           + " · D 회사별: " + ", ".join("%s %d" % kv for kv in Counter(r["corp_label"] for r in rows["D"]).items()),
           "대조 규칙: 공백·줄바꿈만 지운 source_text ⊂ 공백·줄바꿈만 지운 그 쪽 PDF 글(「|」 안 지움, 제어문자는 note 표시 행만). "
           "쪽 글은 이 스크립트가 md 를 직접 나눔. 빠짐은 B 6개·D 6개 검색어를 md 에서 직접 찾음", ""]
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
