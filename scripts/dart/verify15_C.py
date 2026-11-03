# -*- coding: utf-8 -*-
"""15차 검증 — 작업 C 조각(지주 설립·전환 신고서·투자설명서의 인력·조직 문단): dart_out/ops15/조각/C.csv.

    python3 scripts/dart/verify15_C.py      # 인자 없음 → exit 0(통과)/1(실패), 결과 dart_out/ops15/verify15_C.txt

원문은 생성기(scratchpad C/scripts/build.py — 저장소 밖)와 따로 읽어 대조한다(웹 요청·API 키 사용 없음, 입력은 읽기만).
  원문: OpenDART document.xml 원본 dart_out/raw/document/<rcept>.zip 을 ops15_prep.xml_to_md() 로 다시 md 로 옮긴 글
        (저장해 둔 dart_out/text/ops15/신고서__<rcept>.md 본문과 같은지도 봄),
        본문 PDF 쪽 텍스트 dart_out/text/ops15/신고서__<rcept>__본문PDF.md(「## p.N」, 원본 handoff/원본_주요신고서본문.zip sha256 대조),
        우리 2018 정정 웹 회수본 = handoff/dart-benchmark-kit.zip 안 원문_지주전환_서술.csv(status 014→웹회수, 이전 차수 회수본).
  (a) 모든 행 source_text 가 그 행 출처 원문에 글자 그대로 있는지 — 공백·줄바꿈·「|」(｜)만 무시. (C 에는 reason_text 칸 없음)
  (b) page: 「XML [절 n] 「제목」 [표 m]」 → md 의 절 n 제목이 같고 글이 그 절(표 m 이 있으면 그 표 안, 없으면 표 밖)에 있음,
      「p.N(본문 PDF)」 → 그 글이 PDF 쪽 N 에(쪽을 넘으면 N 에서 시작), 「웹 회수본 목차 [n] 「제목」 안 「소절」 부분」 → 회수본
      목차 n 제목이 같고 글이 그 안에, 소절 제목이 글 앞에 있음. section_title 칸도 같은 제목인지.
  (c) 열 이름(COMMON15 순서)·utf-8-sig·필수 칸(corp_label·doc_kind·rcept_no(출처)·page·note·doc_name·collected_at·source_text)
      빈칸 0, doc_kind·rcept_dt 가 공시목록 원장(dart_out/raw/list)과 같음, collected_at 이 원문 받은 시각과 같음, keyword 칸.
  (d) 키·비밀값 문자열 없음(DART_API_KEY 값은 환경변수에서 읽어 들어 있는지만 보고 값은 어디에도 쓰지 않음).
  더해서:
  (e) 사건 10개마다 공시목록 원장과 대조해 신고서·투자설명서가 빠짐없는지(원장에 있는 사건 서류가 모두 C 에 있고, C 의 문서가 모두 원장에 있음).
  (f) 우리 2018 정정 8건(웹 회수본) 행 note 에 「이전 차수 웹 회수본 — 이번에 새로 받지 않음」.
  (g) 문서당 60행 상한: 후보를 다시 세어 note 의 「키워드 행 N개 … M개 뺌」·문서별 행 수·보고 숫자와 같은지.
  (h) 원문 md(dart_out/ops15/원문/C/) 에 행마다 그 절이 있고 글이 있는지(같은 절 가리킴 줄은 따라감), 절 글 sha256 이 원문과 같은지.
  (i) 「문서에 없음」 7행 반박 시도: 더 넓은 검색어로 같은 문서·공시목록을 다시 찾음. 「전적」(轉籍) 0건도 다시 봄.
"""
from __future__ import annotations

import csv
import glob
import gzip
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, HERE)
csv.field_size_limit(10 ** 9)
from ops15_prep import xml_to_md  # noqa: E402  (읽기 전용 변환 함수만)

KST = timezone(timedelta(hours=9))
FRAG = "dart_out/ops15/조각/C.csv"
OUT = "dart_out/ops15/verify15_C.txt"
MDDIR = "dart_out/ops15/원문/C"
TXT = "dart_out/text/ops15"
DOCDIR = "dart_out/raw/document"
LISTDIR = "dart_out/raw/list"
KITZIP = "handoff/dart-benchmark-kit.zip"
PDFZIP = "handoff/원본_주요신고서본문.zip"
COLS = ["corp_label", "doc_kind", "rcept_no", "rcept_dt", "section_title", "keyword", "source_text", "page", "note",
        "doc_name", "collected_at"]
NOT = "문서에 없음"
WEBPHRASE = "이전 차수 웹 회수본 — 이번에 새로 받지 않음"
# (i) 사람이 걸린 글을 읽고 적은 판단(웹 회수본 「문서에 없음」 2행) — 기능 분류·이유 추정 아님, 「인력 운용 계획 글인지」만
REVIEW = {
    "20181115000215": "걸린 「근무·종업원」은 첨부 분기재무제표 주석의 퇴직급여 회계(근무용역기간·당기근무원가·확정급여제도) 글, 「부서」는 「…첨부서류인 분기재무제표」의 "
                      "「서류」 글자 — 지주 설립 때 인력·조직 운용 글이 아님",
    "20181115000218": "걸린 「종업원」은 첨부 재무제표 주석의 「임금피크제 대상 종업원 … 확정기여형 연금제도」(퇴직연금 회계), 「부서」는 「…첨부서류인 분기재무제표」의 "
                      "「서류」 글자 — 지주 설립 때 인력·조직 운용 글이 아님",
}
VENV_PY ="/tmp/claude-0/-home-user-lastprice/c4bd4cae-f7c6-585d-b437-41528ddfc94a/scratchpad/venv/bin/python"  # COMMON15 의 PDF 처리 파이썬(없으면 건너뜀)
PDF_CODE = ("import sys,json,zipfile,hashlib,fitz\n"
            "z=zipfile.ZipFile(sys.argv[1]);o={}\n"
            "for m in sys.argv[2:]:\n"
            "    d=fitz.open(stream=z.read(m),filetype='pdf')\n"
            "    o[m]=[hashlib.sha256(('\\n'+p.get_text()+'\\n').encode()).hexdigest() for p in d]\n"
            "print(json.dumps(o))\n")
WEB8 = ["20181115000213", "20181115000214", "20181115000215", "20181115000218", "20181115000219", "20181115000220",
        "20181121000024", "20181126000093"]

# 사건: (corp_label, 원장 corp_code(제출인·지주), 기간, 첫 신고서 rcept)
EVENTS = OrderedDict([
    ("신한 2001", ("신한금융지주", ["00137571", "00149293", "00382199"], "20010101", "20011231")),
    ("하나 2005", ("하나금융지주", ["00130897", "00156017", "00158909", "00547583"], "20050601", "20051231")),
    ("KB 2008", ("KB금융지주", ["00386937", "00688996"], "20080301", "20081031")),
    ("BNK 2011", ("BNK금융지주", ["00124106", "00858364"], "20100701", "20110630")),
    ("DGB 2011", ("iM금융지주(DGB)", ["00109019", "00878915"], "20101001", "20111031")),
    ("메리츠 2010 분할", ("메리츠금융지주", ["00117744", "00860332"], "20100901", "20110430")),
    ("JB 2013", ("JB금융지주", ["00147295", "00980122"], "20121001", "20131031")),
    ("우리 2018", ("우리금융지주", ["00254045", "01350869"], "20180901", "20190131")),
    ("메리츠 2022", ("메리츠금융지주", ["00860332", "00117744", "00163682"], "20221101", "20230430")),
    ("한국투자 2003", ("한국투자금융지주", ["00118026", "00360425", "00406709", "00432102", "00162142"], "20020801", "20030630")),
])
# 사건 서류(신고서·투자설명서) 이름 꼴. 결정·주요사항보고서·종료보고서는 신고서·투자설명서가 아니라 C 대상 밖(보고 「실패·누락」에 적힌 대로).
EVDOC = re.compile(r"주식교환ㆍ이전신고서|증권신고서\(주식의포괄적교환ㆍ이전\)|증권신고서\(분할\)|분할신고서|증권신고서\[주식|"
                   r"예비투자설명서\[주식\]|투자설명서\[주식\]|유가증권신고서")
BARE_TS = re.compile(r"^(?:\[[^\]]+\])*투자설명서$")
REG = re.compile(r"신고서")

# ── 생성기 추출 규칙(scratchpad C/scripts/extract.py·build.py 와 같은 규칙 — (g) 다시 세기용) ─────────────
KW = ["인력", "임직원", "조직", "겸직", "파견", "전적", "채용"]
RE_JJ = re.compile(r"(?<![가-힣])전적(?!으로|인|이)")


def kws(t):
    return [k for k in KW if (RE_JJ.search(t) if k == "전적" else k in t)]


SPLIT = re.compile(r"(?:\s*&cr;\s*){2,}|(?:<br>\s*){2,}")


def paras(s):
    parts, pos = [], 0
    for m in SPLIT.finditer(s):
        parts.append(s[pos:m.start()])
        pos = m.end()
    parts.append(s[pos:])
    out = []
    for p in parts:
        q2 = re.sub(r"^(?:&cr;|\s)+|(?:&cr;|\s)+$", "", p.strip())
        if q2:
            out.append(q2)
    return out


def units2(md_text):
    sec_n, sec_t, tab, in_tab = 0, "(머리말)", 0, False
    for line in md_text.split("\n"):
        mm = re.match(r"^### \[절 (\d+)\] (.*)$", line)
        if mm:
            sec_n, sec_t = int(mm.group(1)), mm.group(2).strip()
            continue
        mm = re.match(r"^\[표 (\d+)\]$", line)
        if mm:
            tab, in_tab = int(mm.group(1)), True
            continue
        if line == "[표 끝]":
            in_tab = False
            continue
        if not line.strip():
            continue
        if in_tab and line.startswith("| "):
            if len(line) > 1500:
                for p_ in paras(line):
                    yield sec_n, sec_t, tab, p_
            else:
                yield sec_n, sec_t, tab, line
        else:
            for p_ in paras(line):
                yield sec_n, sec_t, (tab if in_tab else None), p_


BND = re.compile(r"다\.|\.\s|&cr;|<br>|\s\|\s|\?\s")


def windows(text, maxlen=1200):
    if len(text) <= maxlen:
        return [(0, len(text))]
    b = sorted(set([0, len(text)] + [m.end() for m in BND.finditer(text)]))
    sents = [(b[i], b[i + 1]) for i in range(len(b) - 1) if b[i + 1] > b[i]]
    spans, cur = [], None
    for s, e in sents:
        if kws(text[s:e]):
            if cur and cur[1] == s:
                cur = (cur[0], e)
            else:
                if cur:
                    spans.append(cur)
                cur = (s, e)
        else:
            if cur:
                spans.append(cur)
                cur = None
    if cur:
        spans.append(cur)
    out = []
    for s, e in spans:
        if e - s <= 1500:
            out.append((s, e))
            continue
        sub = []
        for k in KW:
            pat = RE_JJ if k == "전적" else re.compile(re.escape(k))
            for m in pat.finditer(text, s, e):
                a, z = max(s, m.start() - 300), min(e, m.end() + 300)
                while a > s and not text[a - 1].isspace():
                    a -= 1
                while z < e and not text[z].isspace():
                    z += 1
                sub.append((a, z))
        sub.sort()
        for a, z in sub:
            if out and out[-1][1] >= a and out[-1][0] >= s:
                out[-1] = (out[-1][0], max(out[-1][1], z))
            else:
                out.append((a, z))
    res = []
    for s, e in out:
        t = text[s:e]
        t2 = re.sub(r"^(?:&cr;|<br>|\s|\|)+", "", t)
        s2 = s + (len(t) - len(t2))
        t3 = re.sub(r"(?:&cr;|<br>|\s|\|)+$", "", t2)
        if t3:
            res.append((s2, s2 + len(t3)))
    return res


REL_A = re.compile(r"기본사항|목적|배경|사업계획|이해관계|지주|설립|완전모회사|이사회결의|분할의|이전의|교환의|당사회사간")
REL_B = re.compile(r"조직|인력|임원 및 직원|직원|겸직")


def relevant(sec_t, text):
    return bool(REL_A.search(sec_t) or REL_B.search(sec_t) or ("지주" in text))


# ── 공통 도구 ─────────────────────────────────────────────────
def n1(s):  # (a) 규칙: 공백·줄바꿈·「|」(md 의 칸 안 ｜ 포함)만 무시
    return re.sub(r"[\s|｜]+", "", s)


def npdf(s):  # PDF 쪽 대조용: XML 표지(&cr;·<br>)도 걷어냄(PDF 에는 없음)
    return re.sub(r"[\s|｜]+", "", s.replace("&cr;", "").replace("<br>", ""))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_list():
    led = {}
    files = defaultdict(set)
    for f in glob.glob(os.path.join(LISTDIR, "*_p*.json")):
        if f.endswith(".meta.json"):
            continue
        cc = os.path.basename(f).split("_")[0]
        files[cc].add(f)
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for it in d.get("list") or []:
            led.setdefault(it["rcept_no"], dict(it, cc=cc, file=f))
    return led, files


def list_meta(cc):
    fs = sorted(glob.glob(os.path.join(LISTDIR, cc + "_*_p*.json.meta.json")))
    return [json.load(open(f, encoding="utf-8")) for f in fs]


def main():
    lines = []
    P = lines.append
    fails = Counter()
    warn = []
    now = datetime.now(KST).isoformat(timespec="seconds")
    P("# 15차 작업 C 조각 검증 (verify15_C.py)")
    P(f"실행: {now} KST · 웹 요청 없음 · 입력은 읽기만 · 대상 {FRAG}")
    P("")

    # ── (c) 형식 ──
    raw = open(FRAG, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    hdr = next(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if not bom:
        fails["c_bom"] += 1
    if hdr != COLS:
        fails["c_cols"] += 1
    req = ["corp_label", "doc_kind", "rcept_no", "page", "note", "doc_name", "collected_at", "source_text"]
    empty = Counter()
    for r in rows:
        for c in req:
            if not (r.get(c) or "").strip():
                empty[c] += 1
        if r["source_text"] != NOT:
            for c in ["rcept_dt", "section_title", "keyword"]:
                if not r[c].strip():
                    empty[c] += 1
    fails["c_empty"] += sum(empty.values())
    badts = [i for i, r in enumerate(rows) if not re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00$", r["collected_at"])]
    fails["c_collected_fmt"] += len(badts)

    led, lfiles = load_list()
    # 원문 읽기
    kit = defaultdict(dict)  # rcept -> sec_idx -> dict
    with zipfile.ZipFile(KITZIP) as z:
        t = z.read("원문_지주전환_서술.csv").decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(t, newline="")):
        if not row["status"].startswith("014"):
            continue
        d = kit[row["rcept_no"]].setdefault(int(row["section_index"]), dict(title=row["section_title_raw"], ch={},
                                                                              fetched_at=row["fetched_at"], raw_path=row["raw_path"]))
        d["ch"][int(row["chunk_seq"])] = row["section_text"]
    web = {r: {si: dict(d, text="".join(d["ch"][k] for k in sorted(d["ch"]))) for si, d in v.items()} for r, v in kit.items()}

    rcepts = list(OrderedDict.fromkeys(r["rcept_no"] for r in rows if re.match(r"^\d{14}$", r["rcept_no"])))
    src = {}  # rcept -> dict(kind, md, meta)
    md_mismatch = []
    for rc in rcepts + ["20181108000394"]:
        if rc in src:
            continue
        zp = os.path.join(DOCDIR, rc + ".zip")
        meta = json.load(open(zp + ".meta.json", encoding="utf-8")) if os.path.exists(zp + ".meta.json") else {}
        if meta.get("api_status") == "000":
            b = open(zp, "rb").read()
            if meta.get("sha256") and sha(b) != meta["sha256"]:
                fails["src_zip_sha"] += 1
            md, member, enc = xml_to_md(b, rc)
            saved = os.path.join(TXT, f"신고서__{rc}.md")
            if os.path.exists(saved):
                body = open(saved, encoding="utf-8").read().split("\n", 5)[5]
                if body.lstrip("\n") != md:
                    md_mismatch.append(rc)
            else:
                md_mismatch.append(rc + "(저장 md 없음)")
            src[rc] = dict(kind="xml", md=md, meta=meta)
        elif rc in web:
            src[rc] = dict(kind="web", meta=meta)
        else:
            src[rc] = dict(kind="none", meta=meta)
    fails["src_md_mismatch"] += len(md_mismatch)

    # 절·표 구조
    def struct(md):
        secs = OrderedDict()
        cur = 0
        secs[0] = dict(title="(머리말)", lines=[], tabs=defaultdict(list), out=[])
        tab = None
        for line in md.split("\n"):
            mm = re.match(r"^### \[절 (\d+)\] (.*)$", line)
            if mm:
                cur = int(mm.group(1))
                secs[cur] = dict(title=mm.group(2).strip(), raw_title=mm.group(2), lines=[], tabs=defaultdict(list), out=[])
                continue
            mm = re.match(r"^\[표 (\d+)\]$", line)
            if mm:
                tab = int(mm.group(1))
                continue
            if line == "[표 끝]":
                tab = None
                continue
            secs[cur]["lines"].append(line)
            (secs[cur]["tabs"][tab] if tab is not None else secs[cur]["out"]).append(line)
        for s in secs.values():
            s["n_all"] = n1("\n".join(s["lines"]))
            s["n_out"] = n1("\n".join(s["out"]))
            s["n_tab"] = {k: n1("\n".join(v)) for k, v in s["tabs"].items()}
        return secs

    st_cache = {rc: struct(s["md"]) for rc, s in src.items() if s["kind"] == "xml"}
    full_n = {rc: n1(s["md"]) for rc, s in src.items() if s["kind"] == "xml"}
    web_n = {rc: n1("\n".join(d["text"] for d in web[rc].values())) for rc in web}

    # PDF
    pdfp = {}
    pdf_info = []
    # 쪽 글 다시 뽑기: 이 파이썬에 PyMuPDF 가 있으면 바로, 없으면 COMMON15 의 PDF 처리 파이썬(venv, -I)을 따로 띄워 쪽마다 sha256 만 받음
    reext_sha = {}
    try:
        import fitz  # noqa
        have_fitz = True
    except Exception:
        have_fitz = False
    pdf_mds = sorted(glob.glob(os.path.join(TXT, "신고서__*__본문PDF.md")))
    members = [f"doc/{os.path.basename(f).split('__')[1]}/본문.pdf" for f in pdf_mds]
    if not have_fitz and os.path.exists(VENV_PY) and members:
        import subprocess
        try:
            cp = subprocess.run([VENV_PY, "-I", "-c", PDF_CODE, os.path.abspath(PDFZIP)] + members,
                                capture_output=True, text=True, timeout=900)
            reext_sha = json.loads(cp.stdout) if cp.returncode == 0 else {}
        except Exception:
            reext_sha = {}
    with zipfile.ZipFile(PDFZIP) as pz:
        for f in pdf_mds:
            rc = os.path.basename(f).split("__")[1]
            s = open(f, encoding="utf-8").read()
            m = re.search(r"sha256 ([0-9a-f]{64})", s)
            pdfb = pz.read(f"doc/{rc}/본문.pdf")
            ok_sha = bool(m and m.group(1) == sha(pdfb))
            parts = re.split(r"^## p\.(\d+)\n", s, flags=re.M)
            pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
            reext = "PyMuPDF 없음(sha256 대조만)"
            if have_fitz:
                doc = fitz.open(stream=pdfb, filetype="pdf")
                hs = [sha(f"\n{pg.get_text()}\n".encode()) for pg in doc]
            else:
                hs = reext_sha.get(f"doc/{rc}/본문.pdf")
            if hs:
                same = sum(1 for i, h in enumerate(hs) if sha(pages.get(i + 1, "").encode()) == h)
                reext = f"PyMuPDF 로 다시 뽑은 쪽 글과 같음 {same}/{len(hs)}{'' if have_fitz else '(venv 파이썬 -I)'}"
                if same != len(hs) or len(pages) != len(hs):
                    fails["pdf_reextract"] += 1
            if not ok_sha:
                fails["pdf_sha"] += 1
            pdfp[rc] = {k: npdf(v) for k, v in pages.items()}
            pdf_info.append(f"{rc} {len(pages)}쪽 · 원본 zip sha256 {'같음' if ok_sha else '다름'} · {reext}")

    # ── 행별 (a)(b) ──
    RE_XML = re.compile(r"^(?:p\.(\d+)(?:~(\d+))?\(본문 PDF\) · )?XML \[절 (\d+)\] 「(.*)」(?: \[표 (\d+)\])?( \(표 칸 안 문단\))?$")
    pdf_start_only = []
    RE_WEB = re.compile(r"^웹 회수본 목차 \[(\d+)\] 「(.*?)」(?: 안 「(.*)」 부분)?\(쪽 번호 없음\)$")
    stat = Counter()
    bad_rows = []
    pdf_levels = Counter()
    kw_bad = []
    per_doc_rows = Counter()
    for i, r in enumerate(rows, start=2):
        rc, stx = r["rcept_no"], r["source_text"]
        if stx == NOT:
            stat["not"] += 1
            continue
        per_doc_rows[rc] += 1
        s = src.get(rc, {})
        # keyword 칸
        if set(filter(None, r["keyword"].split("·"))) != set(kws(stx)):
            kw_bad.append(i)
        if s.get("kind") == "xml":
            stat["xml"] += 1
            if stx in s["md"]:
                stat["a_exact"] += 1
            if n1(stx) in full_n[rc]:
                stat["a_ok"] += 1
            else:
                bad_rows.append((i, "a", rc, stx[:50]))
                continue
            m = RE_XML.match(r["page"])
            if not m:
                bad_rows.append((i, "b-꼴", rc, r["page"][:60]))
                continue
            pdfpg, pdfe, sn, stt, tb = m.group(1), m.group(2), int(m.group(3)), m.group(4), m.group(5)
            sec = st_cache[rc].get(sn)
            if not sec or sec["title"] != stt:
                bad_rows.append((i, "b-절제목", rc, f"[절 {sn}] {stt[:30]} / md {sec['title'][:30] if sec else '없음'}"))
                continue
            if r["section_title"] != stt:
                bad_rows.append((i, "b-section_title", rc, r["section_title"][:40]))
                continue
            region = sec["n_tab"].get(int(tb), "") if tb else sec["n_out"]
            if n1(stx) not in region:
                bad_rows.append((i, "b-위치", rc, r["page"][:60]))
                continue
            stat["b_ok"] += 1
            if pdfpg:
                stat["pdf_rows"] += 1
                ps, pe = int(pdfpg), int(pdfe) if pdfe else int(pdfpg)
                pages = pdfp.get(rc)
                if not pages or ps not in pages or pe not in pages or pe < ps:
                    bad_rows.append((i, "b-PDF쪽없음", rc, r["page"][:30]))
                    continue
                t = npdf(stx)
                span = "".join(pages[p] for p in range(ps, pe + 1))
                nxt = span + pages.get(pe + 1, "")
                k = nxt.find(t)
                head, tail = t[:20], t[-20:]
                if t and ps == pe and t in pages[ps]:
                    pdf_levels["full"] += 1          # 글 전체가 그 쪽 안
                elif t and 0 <= k < len(pages[ps]) and (ps == pe or k + len(t) > len(span) - len(pages[pe])):
                    pdf_levels["full"] += 1          # 글 전체가 이어져 있고 시작 쪽·끝 쪽이 맞음
                elif head in pages[ps] and (ps == pe or tail in pages[pe]):
                    pdf_levels["start"] += 1         # 쪽 사이에 머리말·표가 끼어 글이 끊김 — 첫 20자가 시작 쪽, (범위면) 끝 20자가 끝 쪽
                    if ps == pe and tail not in pages[ps]:
                        pdf_start_only.append(i)
                else:
                    pdf_levels["fail"] += 1
                    bad_rows.append((i, "b-PDF쪽", rc, r["page"][:40]))
            elif rc in pdfp:
                stat["pdf_missing_page"] += 1  # PDF 가 있는데 쪽을 못 붙인 행(note 확인)
                if "본문 PDF 에서 같은 글을 찾지 못해" not in r["note"]:
                    bad_rows.append((i, "b-PDF쪽없음note", rc, ""))
        elif s.get("kind") == "web":
            stat["web"] += 1
            if n1(stx) not in web_n[rc]:
                bad_rows.append((i, "a", rc, stx[:50]))
                continue
            stat["a_ok"] += 1
            if any(stx in d["text"] for d in web[rc].values()):
                stat["a_exact"] += 1
            m = RE_WEB.match(r["page"])
            if not m:
                bad_rows.append((i, "b-꼴", rc, r["page"][:60]))
                continue
            si, stt, sub = int(m.group(1)), m.group(2), m.group(3)
            d = web[rc].get(si)
            if not d or d["title"] != stt or n1(stx) not in n1(d["text"]):
                bad_rows.append((i, "b-웹목차", rc, r["page"][:60]))
                continue
            if r["section_title"] != (sub or stt):
                bad_rows.append((i, "b-section_title", rc, r["section_title"][:40]))
                continue
            if sub:
                pos = d["text"].find(stx)
                sp = d["text"].find(sub)
                if pos < 0 or sp < 0 or sp > pos:
                    bad_rows.append((i, "b-웹소절", rc, sub[:40]))
                    continue
            stat["b_ok"] += 1
        else:
            bad_rows.append((i, "a-원문없음", rc, stx[:40]))
    fails["ab"] += len(bad_rows)
    fails["keyword"] += len(kw_bad)

    # 출처·원장 대조
    led_bad = []
    coll_bad = []
    for i, r in enumerate(rows, start=2):
        rc = r["rcept_no"]
        if re.match(r"^\d{14}$", rc):
            it = led.get(rc)
            if not it:
                led_bad.append((i, rc, "원장에 없음"))
            else:
                if it["report_nm"].strip() != r["doc_kind"]:
                    led_bad.append((i, rc, "doc_kind≠report_nm"))
                if it["rcept_dt"] != r["rcept_dt"]:
                    led_bad.append((i, rc, "rcept_dt"))
            if rc not in r["doc_name"]:
                led_bad.append((i, rc, "doc_name 에 접수번호 없음"))
            s = src.get(rc, {})
            if s.get("kind") == "xml":
                if r["collected_at"] != s["meta"].get("fetched_at"):
                    coll_bad.append((i, rc))
            elif s.get("kind") == "web":
                ok = {d["fetched_at"] for d in web[rc].values()}
                if r["collected_at"] not in ok:
                    coll_bad.append((i, rc))
            else:
                if r["collected_at"] != s.get("meta", {}).get("fetched_at"):
                    coll_bad.append((i, rc))
        elif rc.startswith("https://opendart.fss.or.kr/api/list.json?"):
            ccs = re.findall(r"corp_code=(\d{8})", rc)
            fa = sorted(m_.get("fetched_at", "") for cc in ccs for m_ in list_meta(cc))
            if not ccs or r["collected_at"] not in fa:
                coll_bad.append((i, rc[:60]))
            if "crtfc_key" in rc:
                led_bad.append((i, rc[:40], "URL 에 인증키 칸"))
        else:
            led_bad.append((i, rc[:30], "출처 꼴"))
    fails["ledger"] += len(led_bad)
    fails["collected_at"] += len(coll_bad)

    P("## (c) 열 이름·utf-8-sig·필수 칸·출처")
    P(f"- {len(rows)}행 · BOM {'있음' if bom else '없음'} · 열 {'같음' if hdr == COLS else '다름: ' + ','.join(hdr)}"
      f" · 필수 칸 빈칸 {sum(empty.values())}{' ' + dict(empty).__repr__() if empty else ''} · collected_at 꼴(+09:00) 어긋남 {len(badts)}")
    P(f"- 접수번호 행: doc_kind·rcept_dt·doc_name 이 공시목록 원장(dart_out/raw/list)과 다름 {len(led_bad)}"
      f"{' ' + str(led_bad[:5]) if led_bad else ''} · collected_at 이 원문 받은 시각(XML zip meta·웹 회수본 fetched_at·목록 meta)과 다름 {len(coll_bad)}"
      f"{' ' + str(coll_bad[:5]) if coll_bad else ''}")
    P(f"- keyword 칸 = source_text 안 키워드(인력·임직원·조직·겸직·파견·전적(轉籍 꼴)·채용) 집합과 다른 행 {len(kw_bad)}{' ' + str(kw_bad[:10]) if kw_bad else ''}")
    P("")
    P("## (a) source_text ↔ 원문 글자 그대로(공백·줄바꿈·「|」만 무시) · (b) page ↔ 실제 위치")
    P(f"- 원문 md: OpenDART zip 에서 xml_to_md 로 다시 만든 글과 저장 md(dart_out/text/ops15/신고서__*.md) 본문이 다른 문서 {len(md_mismatch)}"
      f"{' ' + str(md_mismatch) if md_mismatch else ''} (XML 원문 {sum(1 for s in src.values() if s['kind'] == 'xml')}건 · 웹 회수본 {sum(1 for s in src.values() if s['kind'] == 'web')}건 · 원문 없음(014) {sum(1 for s in src.values() if s['kind'] == 'none')}건)")
    nn = len(rows) - stat["not"]
    P(f"- 「문서에 없음」 {stat['not']}행 · 글 행 {nn}(XML {stat['xml']} · 웹 회수본 {stat['web']})")
    P(f"- (a) 원문에 있음 {stat['a_ok']}/{nn} (공백 무시 없이도 그대로 부분 문자열 {stat['a_exact']})")
    P(f"- (b) page 맞음 {stat['b_ok']}/{nn} — XML 은 절 번호·제목이 md 와 같고 글이 그 절의 그 표(표 없으면 표 밖)에 있음, 웹은 목차 번호·제목·소절 위치")
    P(f"- (b) 본문 PDF 쪽(「p.N」 또는 쪽을 넘는 글 「p.S~E」): 쪽 붙은 행 {stat['pdf_rows']} — 글 전체가 그 쪽(범위)에 이어져 있음 {pdf_levels['full']} · "
      f"쪽 사이에 머리말·표가 끼어 끊겼지만 첫 20자가 시작 쪽(범위면 끝 20자가 끝 쪽)에 있음 {pdf_levels['start']} · 못 찾음 {pdf_levels['fail']} · "
      f"PDF 있는 문서인데 쪽 없는 행 {stat['pdf_missing_page']}(note 「본문 PDF 에서 같은 글을 찾지 못해」 있음)")
    if pdf_start_only:
        P(f"  · 그 가운데 「p.N」 한 쪽인데 끝 20자가 그 쪽에 없는 행(PDF 에서 표가 글 사이에 끼어 끝을 쪽으로 못 정함 — 시작 쪽은 맞음): {pdf_start_only}")
    for x in pdf_info:
        P(f"  · PDF {x}")
    if bad_rows:
        P(f"- 틀린 행 {len(bad_rows)}:")
        for b in bad_rows[:40]:
            P(f"  · {b}")
    P("")
    return lines, fails, warn, dict(rows=rows, src=src, web=web, led=led, lfiles=lfiles, st=st_cache,
                                   per_doc_rows=per_doc_rows)


def part2(ctx, lines, fails, warn):
    P = lines.append
    rows, src, web, led = ctx["rows"], ctx["src"], ctx["web"], ctx["led"]
    # ── (e) 사건별 문서 목록 ──
    P("## (e) 사건마다 문서 목록 ↔ 공시목록 원장(dart_out/raw/list)")
    in_csv = defaultdict(set)
    for r in rows:
        in_csv[r["corp_label"]].add(r["rcept_no"])
    all_c = {r["rcept_no"] for r in rows}
    covered = set()
    for ev, (label, ccs, b, e) in EVENTS.items():
        evdocs, other_ts, excluded = [], [], Counter()
        cover = []
        by_cc = defaultdict(list)
        for it in led.values():
            if it["cc"] in ccs and b <= it["rcept_dt"] <= e:
                by_cc[it["cc"]].append(it)
        for cc in ccs:
            rng = sorted({"_".join(os.path.basename(f).split("_")[1:3]) for f in ctx["lfiles"].get(cc, [])})
            ok = any(x.split("_")[0] <= b and x.split("_")[1] >= e for x in rng)
            part = any(x.split("_")[0] <= e and x.split("_")[1] >= b for x in rng)
            cover.append(f"{cc}:{'기간 전부' if ok else ('기간 일부' if part else '원장 없음')}")
            its = sorted(by_cc[cc], key=lambda x: (x["rcept_dt"], x["rcept_no"]))
            for j, it in enumerate(its):
                nm = it["report_nm"].strip()
                if EVDOC.search(nm):
                    evdocs.append(it)
                elif BARE_TS.match(nm):
                    # 이름만 「투자설명서」인 것: 같은 법인이 바로 앞에 낸 신고서(일괄신고서·지분·신탁 신고서 빼고)가 사건 서류면 사건 투자설명서.
                    # 로컬 원문이 있으면 글에 「주식이전·포괄적 교환·분할」이 있는지도 봄(보조 확인).
                    prev = [p for p in its[:j] if REG.search(p["report_nm"]) and not re.search(r"최대주주|신탁|일괄신고|공개매수|자기주식", p["report_nm"])]
                    pv = prev[-1]["report_nm"].strip() if prev else ""
                    body = src.get(it["rcept_no"], {}).get("md", "")
                    word = bool(re.search(r"주식이전|주식의 포괄적|포괄적 주식|주식의포괄적|분할", body)) if body else None
                    if EVDOC.search(pv):
                        evdocs.append(it)
                        if word is False:
                            warn.append(f"{it['rcept_no']} 투자설명서: 앞 신고서는 사건 서류인데 글에 주식이전·교환·분할 낱말이 없음")
                    else:
                        other_ts.append(f"{it['rcept_no']} {nm}(바로 앞 신고서 「{pv}」{', 글에 주식이전·교환·분할 낱말 있음' if word else ''})")
                        if word:
                            warn.append(f"{it['rcept_no']} 투자설명서: 앞 신고서는 사건 서류가 아닌데 글에 주식이전·교환·분할 낱말이 있음")
                elif re.search(r"결정|주요사항보고서|종료보고서", nm) and re.search(r"교환|이전|분할", nm):
                    excluded[nm.split("]")[-1]] += 1
        ev_r = {it["rcept_no"] for it in evdocs}
        missing = sorted(ev_r - all_c)
        covered |= ev_r
        fails["e_missing"] += len(missing)
        P(f"- {ev} ({label}) 원장 {', '.join(cover)} · 기간 {b}~{e} · 사건 서류 {len(ev_r)}건 · C 에 있음 {len(ev_r) - len(missing)}"
          f"{' · 빠짐 ' + str(missing) if missing else ''}")
        if other_ts:
            P(f"  · 사건 서류 아님(앞 신고서가 채무증권 등): {'; '.join(other_ts)}")
        if excluded:
            P(f"  · 신고서·투자설명서가 아니라 대상 밖(결정·주요사항보고서·종료보고서): {dict(excluded)}")
    extra = sorted(r for r in all_c if re.match(r"^\d{14}$", r) and r not in covered)
    fails["e_extra"] += len(extra)
    P(f"- C 에 있는데 위 사건 서류 목록에 없는 접수번호 {len(extra)}{' ' + str(extra) if extra else ''}")
    P("- 원장 한계: 하나금융지주 00547583 은 원장이 2020~ 만 있어 2005년 목록은 볼 수 없음(하나은행(구) 00130897 목록으로 대조).")
    P("")

    # ── (f) 웹 회수본 note ──
    P("## (f) 우리 2018 정정 8건(웹 회수본) 행 note")
    wr = [r for r in rows if r["rcept_no"] in WEB8]
    nophrase = [r["rcept_no"] for r in wr if WEBPHRASE not in r["note"]]
    docs_w = Counter(r["rcept_no"] for r in wr)
    fails["f_phrase"] += len(nophrase)
    P(f"- 8건 모두 C 에 있음: {'예' if set(docs_w) == set(WEB8) else '아니오 ' + str(sorted(set(WEB8) - set(docs_w)))} · 행 {len(wr)}"
      f"(글 행 {sum(1 for r in wr if r['source_text'] != NOT)} · 「문서에 없음」 {sum(1 for r in wr if r['source_text'] == NOT)}) · "
      f"note 에 「{WEBPHRASE}」 없는 행 {len(nophrase)}")
    srcs = Counter(src.get(r, {}).get("kind") for r in WEB8)
    P(f"- 8건의 원문 종류: {dict(srcs)} (OpenDART document.xml 014 → handoff/dart-benchmark-kit.zip 원문_지주전환_서술.csv 의 status 「014→웹회수」 글)")
    P("")

    # ── (g) 60행 상한 다시 세기 ──
    P("## (g) 문서당 60행 상한 — 후보 다시 세기 ↔ note·행 수·보고")
    base_titles = [(int(mm.group(1)), mm.group(2).strip()) for mm in
                   re.finditer(r"^### \[절 (\d+)\] (.*)$", src["20181108000394"]["md"], re.M)]
    capped = []
    doc_bad = []
    for rc in OrderedDict.fromkeys(r["rcept_no"] for r in rows):
        s = src.get(rc)
        if not s or s["kind"] == "none":
            continue
        cand = []
        if s["kind"] == "xml":
            for sn, stt, tb, t in units2(s["md"]):
                if not kws(t):
                    continue
                for a, z in windows(t):
                    tt = t[a:z]
                    if kws(tt):
                        cand.append((sn, tb, tt, stt, t))
        else:
            for si in sorted(web[rc]):
                d = web[rc][si]
                t = d["text"]
                marks, pos = [], 0
                for bn_, bt in base_titles:
                    if len(bt) < 4:
                        continue
                    k = t.find(bt, pos)
                    if k >= 0:
                        marks.append((k, bt))
                        pos = k + len(bt)
                for a, z in windows(t):
                    tt = t[a:z]
                    if not kws(tt):
                        continue
                    sub = None
                    for k, bt in marks:
                        if k <= a:
                            sub = bt
                        else:
                            break
                    cand.append((si, None, tt, sub or d["title"], tt))
        seen, uniq = set(), []
        for c in cand:
            if (c[0], c[1], c[2]) in seen:
                continue
            seen.add((c[0], c[1], c[2]))
            uniq.append(c)
        n_all = len(uniq)
        keep = [c for c in uniq if relevant(c[3], c[4])] if n_all > 60 else uniq
        dropped = n_all - len(keep)
        n_rows = ctx["per_doc_rows"].get(rc, 0)
        notes = {r["note"] for r in rows if r["rcept_no"] == rc and r["source_text"] != NOT}
        pat = re.compile(r"이 문서 키워드 행 (\d+)개\(60 초과\) → .*?, (\d+)개 뺌")
        got = {pat.search(n).groups() if pat.search(n) else None for n in notes}
        label = next(r["corp_label"] for r in rows if r["rcept_no"] == rc)
        if n_all > 60:
            capped.append((rc, label, n_all, len(keep), dropped))
            if got != {(str(n_all), str(dropped))} or n_rows != len(keep):
                doc_bad.append((rc, n_all, dropped, len(keep), n_rows, got))
        else:
            if any(g is not None for g in got) or n_rows != n_all:
                doc_bad.append((rc, n_all, 0, n_all, n_rows, got))
    fails["g_doc"] += len(doc_bad)
    tot = sum(c[4] for c in capped)
    byc = Counter(c[1] for c in capped)
    P(f"- 다시 센 결과: 후보 60 초과 문서 {len(capped)}건 · 뺀 행 {tot:,}개 · 회사별 {dict(byc)}")
    for c in capped:
        P(f"  · {c[0]} {c[1]} 후보 {c[2]} → 남김 {c[3]} · 뺌 {c[4]}")
    P(f"- 문서마다 note 의 「키워드 행 N개 … M개 뺌」 숫자·C 행 수가 다시 센 것과 다른 문서 {len(doc_bad)}{' ' + str(doc_bad[:5]) if doc_bad else ''}"
      f" (60 이하 문서는 note 에 상한 문구가 없고 행 수 = 후보 수인지)")
    REP_DOCS, REP_DROP, REP_BY = 20, 1884, {"KB금융지주": 3, "우리금융지주": 3, "메리츠금융지주": 12, "그 밖": 2}
    same_tot = (len(capped) == REP_DOCS and tot == REP_DROP)
    if not same_tot:
        fails["g_report"] += 1
    P(f"- 보고(wave1_results.json c.judgments)와 대조: 「후보가 60행을 넘은 문서 20건 … 뺀 행은 모두 1,884개」 → "
      f"{'같음' if same_tot else '다름'}")
    real_by = dict(byc)
    if real_by != {k: v for k, v in REP_BY.items() if k != "그 밖"} or REP_BY.get("그 밖"):
        warn.append(f"보고 글의 회사별 나눔 「KB 3, 우리 3, 메리츠 12, 그 밖 2」는 실제 {real_by}(우리 5·그 밖 0) — 조각·note 는 맞고 보고 글만 틀림")
        P(f"- 주의: 보고 글의 회사별 나눔 「KB 3, 우리 3, 메리츠 12, 그 밖 2」 ≠ 실제 {real_by} — 합계(20건·1,884개)와 조각 note 는 맞음. "
          "보고 글(wave1_results.json, 메인 소유)만 고칠 것: 「KB 3, 우리 5, 메리츠 12」")
    P("")
    return capped


def part3(ctx, lines, fails, warn):
    P = lines.append
    rows, src, web, led = ctx["rows"], ctx["src"], ctx["web"], ctx["led"]
    # ── (h) 원문 md ──
    P("## (h) 원문 md(dart_out/ops15/원문/C/) ↔ 행·원문")
    files = {os.path.basename(f).rsplit("__", 1)[1][:-3]: f for f in glob.glob(os.path.join(MDDIR, "*.md"))}
    cache = {}

    def secs_of(path):
        if path not in cache:
            s = open(path, encoding="utf-8").read()
            parts = re.split(r"^(## .*)$", s, flags=re.M)
            d = {}
            for k in range(1, len(parts), 2):
                d[parts[k][3:].strip()] = parts[k + 1]
            cache[path] = d
        return cache[path]

    md_bad, ptr, sha_bad, sha_ok = [], 0, 0, 0
    need = set()
    for i, r in enumerate(rows, start=2):
        if r["source_text"] == NOT:
            continue
        rc = r["rcept_no"]
        f = files.get(rc)
        if not f:
            md_bad.append((i, rc, "md 파일 없음"))
            continue
        if src[rc]["kind"] == "xml":
            mm = re.search(r"XML \[절 (\d+)\] ", r["page"])
            sn = int(mm.group(1))
            head = (f"[절 {sn}] {ctx['st'][rc][sn]['raw_title'].strip()}" if sn else "(머리말 — 첫 절 제목 앞)")
            key = (rc, sn)
        else:
            mm = re.match(r"^웹 회수본 목차 \[(\d+)\] 「(.*?)」", r["page"])
            head = f"웹 회수본 목차 [{mm.group(1)}] {mm.group(2)}"
            key = (rc, -int(mm.group(1)))
        d = secs_of(f)
        body = d.get(head)
        if body is None:
            md_bad.append((i, rc, "절 없음 " + head[:30]))
            continue
        need.add((key, head, f))
        if n1(r["source_text"]) in n1(body):
            continue
        pm = re.search(r"\(이 절 글은 `([^`]+)` 의 「(.*?)」 절과 글자 하나까지 같음", body)
        if pm:
            other = os.path.join(MDDIR, pm.group(1))
            b2 = secs_of(other).get(pm.group(2)) if os.path.exists(other) else None
            if b2 is not None and n1(r["source_text"]) in n1(b2):
                ptr += 1
                continue
        md_bad.append((i, rc, "글 없음 " + head[:30]))
    # 절 글 sha256 대조(XML 절: 원문 md 의 그 절 글과 같은지, 웹: 회수본 목차 글)
    for key, head, f in sorted(need):
        rc, n = key
        if n == 0:
            sha_ok += 1  # 머리말 절은 sha 줄이 없음 — 글 대조만(위)
            continue
        body = secs_of(f)[head]
        mh = re.search(r"절 글 sha256 ([0-9a-f]{64})", body)
        if not mh:
            sha_bad += 1
            continue
        if n > 0:
            md = src[rc]["md"].split("\n")
            hs = [(j, int(x.group(1))) for j, l in enumerate(md) for x in [re.match(r"^### \[절 (\d+)\] ", l)] if x]
            idx = [k for k, (j, nn) in enumerate(hs) if nn == n][0]
            end = hs[idx + 1][0] if idx + 1 < len(hs) else len(md)
            truth = "\n".join(md[hs[idx][0] + 1:end]).strip("\n")
        else:
            truth = web[rc][-n]["text"]
        if mh.group(1) == sha(truth.encode()):
            sha_ok += 1
        else:
            sha_bad += 1
    fails["h_md"] += len(md_bad) + sha_bad
    P(f"- md 파일 {len(files)}개 · 행이 가리킨 절 {len(need)}개 · 행 글이 md 그 절에 있음(공백·「|」 무시) — 없는 행 {len(md_bad)}"
      f"{' ' + str(md_bad[:5]) if md_bad else ''} (그 가운데 「같은 절 가리킴」 줄을 따라가 찾은 행 {ptr})")
    P(f"- md 의 「절 글 sha256」 이 원문(zip 에서 다시 만든 md 의 그 절·웹 회수본 목차 글)과 같음 {sha_ok}/{len(need)}")
    P("")

    # ── (d) 키·비밀값 ──
    P("## (d) 키·비밀값 문자열")
    key = os.environ.get("DART_API_KEY", "")
    targets = [FRAG] + sorted(glob.glob(os.path.join(MDDIR, "*.md"))) + sorted(glob.glob(os.path.join(TXT, "신고서__*.md"))) + [__file__]
    hit_key = hit_crt = hit_hex = 0
    for f in targets:
        s = open(f, encoding="utf-8", errors="ignore").read()
        if key and key in s:
            hit_key += 1
        if re.search(r"crtfc_key=(?!\*\*\*)[0-9A-Za-z]{8,}", s):
            hit_crt += 1
        if re.search(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])", s):
            hit_hex += 1
    fails["d"] += hit_key + hit_crt + hit_hex
    P(f"- 본 파일 {len(targets)}개(C.csv · 원문/C md · 신고서 md · 이 스크립트) · DART_API_KEY 값 "
      f"{'(환경변수 없음 — 값 대조 생략)' if not key else '들어 있는 파일 ' + str(hit_key)} · 「crtfc_key=값」 {hit_crt} · 40자리 16진 문자열(키 꼴) {hit_hex}")
    P("")

    # ── (i) 「문서에 없음」 반박 ──
    P("## (i) 「문서에 없음」 반박 시도(더 넓은 검색어)")
    BROAD = ["인력", "임직원", "조직", "겸직", "파견", "전적", "채용", "인원", "직원", "임원", "인사", "겸임", "겸무", "출향", "전출",
             "전입", "근무", "고용", "승계", "노동조합", "종업원", "본부", "부서"]
    for i, r in enumerate(rows, start=2):
        if r["source_text"] != NOT:
            continue
        rc = r["rcept_no"]
        if re.match(r"^\d{14}$", rc):
            s = src.get(rc, {})
            if s.get("kind") == "web":
                t = "\n".join(web[rc][k]["text"] for k in sorted(web[rc]))
                hits = {w: t.count(w) for w in BROAD if w in t}
                ctxs = []
                for w in hits:
                    for mm in list(re.finditer(re.escape(w), t))[:2]:
                        ctxs.append(f"{w}: …{t[max(0, mm.start() - 25):mm.end() + 25]}…".replace("\n", " "))
                P(f"- 행 {i} {r['corp_label']} {rc} {r['doc_kind']}: 웹 회수본 {len(web[rc])}개 목차 {len(t):,}자 · 넓은 검색어 걸림 {hits or '없음'}")
                for c in ctxs[:8]:
                    P(f"  · {c}")
                if kws(t):
                    fails["i_rebutted"] += 1
                    P(f"  → 반박됨: 7개 키워드 {kws(t)} 가 회수본에 있음 — 행을 다시 뽑아야 함")
                else:
                    P(f"  → 판단(사람이 읽음): {REVIEW.get(rc, '걸린 글을 읽고 판단할 것')} → 「문서에 없음」 유지")
            else:
                local = []
                for p in [os.path.join(DOCDIR, rc + ".zip")]:
                    if os.path.exists(p) and os.path.getsize(p) > 1000:
                        local.append(p)
                with zipfile.ZipFile(KITZIP) as z:
                    for nm in ["원문_지주전환_서술.csv", "원문_지주전환_서술_2차.csv", "원문_지주전환_서술_3차.csv"]:
                        if rc.encode() in z.read(nm):
                            local.append(nm)
                with zipfile.ZipFile(PDFZIP) as z:
                    if any(rc in n for n in z.namelist()):
                        local.append(PDFZIP)
                g = gzip.open("dart_out/11_원문추출.csv.gz", "rb").read()
                if rc.encode() in g:
                    local.append("11_원문추출.csv.gz")
                P(f"- 행 {i} {r['corp_label']} {rc} {r['doc_kind']}: OpenDART {s.get('meta', {}).get('api_status')} · 로컬 다른 원문(kit 서술 1~3차·주요신고서본문 zip·11_원문추출) "
                  f"{local or '없음'} → 반박할 글 없음 → 「문서에 없음」 유지(DART 웹 뷰어는 robots Disallow 라 새로 받지 않음)")
                if local:
                    fails["i_rebutted"] += 1
        else:
            label = r["corp_label"]
            ev = next(k for k, v in EVENTS.items() if v[0] == label)
            _, ccs, b, e = EVENTS[ev]
            # 넓힌 기간(앞뒤 6개월)·넓힌 이름(신고서·설명서·교환·이전·지주·설립·등록·인가)
            def shift(d, mo):
                y, m_ = divmod(int(d[:4]) * 12 + int(d[4:6]) - 1 + mo, 12)
                return f"{y:04d}{m_ + 1:02d}{d[6:]}"
            b2, e2 = shift(b, -6), shift(e, 6)
            pat = re.compile(r"신고서|설명서|교환|이전|지주|설립|등록|인가")
            hits = sorted((it["rcept_dt"], it["rcept_no"], it["cc"], it["report_nm"].strip()) for it in led.values()
                          if it["cc"] in ccs and b2 <= it["rcept_dt"] <= e2 and pat.search(it["report_nm"])
                          and not re.search(r"최대주주|임원ㆍ주요주주|사채|채무증권|파생|일괄|신탁|기업어음|주식등의대량보유", it["report_nm"]))
            want = "투자설명서" if r["doc_kind"] == "투자설명서" else "신고서·투자설명서"
            ts = [h for h in hits if ("설명서" in h[3] if want == "투자설명서" else re.search(r"신고서|설명서", h[3]))]
            P(f"- 행 {i} {label} {r['doc_kind'][:30]}: 원장 {','.join(ccs)} 기간을 {b2}~{e2} 로 넓혀 이름에 신고서·설명서·교환·이전·지주·설립·등록·인가 "
              f"(사채·채무증권·파생·일괄·신탁·지분 공시 뺌) → {len(hits)}건, 그 가운데 {want} {len(ts)}건")
            for h in hits[:12]:
                P(f"  · {h[0]} {h[1]} {h[2]} {h[3]}")
            if ts:
                fails["i_rebutted"] += 1
                P(f"  → 반박됨: {want} {len(ts)}건 — 문서 목록에 넣어야 함")
            else:
                P(f"  → 걸린 것은 결정·등록·종료·소제기·편입 공시와 이미 C 에 있는 신고서뿐 — {want} 없음 → 「문서에 없음」 유지")
    # 전적(轉籍)
    alljj = excl_suffix = excl_prefix = 0
    sfx_ctx = []
    for rc, s in src.items():
        if s["kind"] == "xml":
            texts = [s["md"]]
        elif s["kind"] == "web":
            texts = [d["text"] for d in web[rc].values()]
        else:
            continue
        for t in texts:
            for mm in re.finditer("전적", t):
                alljj += 1
                pre = t[mm.start() - 1] if mm.start() else ""
                nxt = t[mm.end():mm.end() + 2]
                if re.match(r"[가-힣]", pre):
                    excl_prefix += 1
                elif re.match(r"으로|인|이", nxt):
                    excl_suffix += 1
                    if len(sfx_ctx) < 6:
                        sfx_ctx.append(f"{rc}: …{t[max(0, mm.start() - 20):mm.end() + 12]}…".replace("\n", " "))
    kept = alljj - excl_prefix - excl_suffix
    P(f"- 「전적」(轉籍) 다시 봄: 원문(XML·웹, 중복 문서 포함) 「전적」 {alljj}곳 = 앞이 한글(금전적·사전적 …) {excl_prefix} + 뒤가 「으로·인·이」 {excl_suffix} + 남는 것 {kept}")
    for c in sfx_ctx:
        P(f"  · 뒤 「으로·인·이」 보기: {c}")
    if kept:
        fails["jj"] += kept
    P("")


FIXES = [
    "F1 우리 2018 정정 8건(웹 회수본) 30행(글 28 + 「문서에 없음」 2) note 맨 앞에 「이전 차수 웹 회수본 — 이번에 새로 받지 않음」을 넣음"
    "(전에는 「… 회수해 둔 본문 글 … 이번에 새로 받지 않음(뷰어는 robots Disallow)」 꼴이라 이 문구가 없었음). 원문 md(웹 회수본 6개 파일) 머리 출처 줄에도 같은 문구. "
    "생성기 build.py 에 넣음.",
    "F2 「문서에 없음」 7행 page 빈칸 → 찾은 범위로 채움(014 2행 「원문 미제공(OpenDART 014) — 쪽 없음」, 웹 2행 「웹 회수본 목차 [n]~[m] 전체(찾은 범위 — 쪽 번호 없음)」, "
    "공시목록 3행 「공시목록 YYYY-MM~YYYY-MM 전체(찾은 범위 — 쪽 없음)」). 생성기 build.py 에 넣음.",
    "F3 사건 단위 「문서에 없음」 3행(신한 2001·하나 2005 투자설명서·KB 2008 투자설명서) rcept_no 빈칸 → 조회한 공시목록 OpenDART API 주소(인증키 칸 뺌)를 출처로 적음"
    "(C 열에는 URL 칸이 없어 rcept_no 칸에 둠 — note 에 (판단)). 생성기 build.py 에 넣음.",
    "F4 신한 2001 「문서에 없음」 note 바로잡음: 전에는 00149293 을 「신한은행(구)」로 적고 「결정 공시가 없음」이라 했으나, 00149293 은 company.json "
    "설립일 1897-02-19·종목코드 000010 인 조흥은행(2006 신한은행으로 이름 바꾼 존속법인)이고, 신한은행(구)는 00137571(2001년 공시 보고자 라응찬·이인호 등)임. "
    "00137571 의 2001년 목록에 「주식교환ㆍ이전결정」(20010628000184, 2001-06-28)이 있음(결정 공시 — 신고서·투자설명서 아님). 신고서·투자설명서가 없다는 결론은 그대로. "
    "collected_at 은 00137571 목록 받은 시각. 생성기 build.py 에 넣음.",
    "F5 본문 PDF 쪽: 쪽을 넘는 글 6행의 page 를 「p.N」 → 「p.시작~끝」으로(행 7·12·14·19 = p.38~39·p.63~64·p.84~85·p.149~150, "
    "행 160·165 = p.52~53·p.287~288 — 이 둘은 전에 글이 시작하는 앞 쪽이 아니라 키워드 조각이 있는 뒤 쪽 번호만 적혀 있었음). 생성기 build.py 의 PdfPages.find 에 넣음.",
    "F6 본문 PDF 쪽을 못 찾았던 3행 중 행 387(메리츠 2010 분할 증권신고서 「…고능률 조직 중심의 성장정책으로…」)은 PDF 에서 표가 글 가운데 끼어 앞 조각들이 "
    "모두 쪽 사이에 걸렸던 것 — 마지막 후보로 첫 20자를 더해 「p.47~48(본문 PDF)」를 붙이고 note 의 「본문 PDF 에서 같은 글을 찾지 못해」를 뺌. "
    "남은 2행(행 15·16, 하나 2005 「(5) 조직도」·「조직도(2005.07.29).jpg조직도 2005.07.29 기준」)은 그림 파일 이름이라 PDF 글에 없음 — 그대로.",
    "생성기를 고친 뒤 다시 돌려 C.csv·원문/C md 를 다시 씀(바뀐 칸: note 34행(웹 30 + 사건 단위 3 + 행 387), page 14행(문서에 없음 7 + PDF 쪽 7), rcept_no 3, doc_name 3, collected_at 1 · "
    "source_text·행 수 769 그대로). 고치기 전 생성기는 지금 조각과 글자 하나까지 같게 다시 만들어짐을 먼저 확인함.",
]


def run():
    lines, fails, warn, ctx = main()
    part2(ctx, lines, fails, warn)
    part3(ctx, lines, fails, warn)
    P = lines.append
    P("## 고친 곳(이번 검증에서 — 조각 C.csv 는 생성기 scratchpad C/scripts/build.py 를 고쳐 다시 만듦)")
    for f in FIXES:
        P(f"- {f}")
    P("")
    P("## 결과")
    bad = {k: v for k, v in fails.items() if v}
    P(f"- 실패 항목: {bad if bad else '없음'}")
    if warn:
        for w in warn:
            P(f"- 주의(조각 밖): {w}")
    P(f"- exit {'1' if bad else '0'}")
    text = "\n".join(lines) + "\n"
    key = os.environ.get("DART_API_KEY", "")
    if key and key in text:
        text = text.replace(key, "***")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"verify15_C: {'FAIL ' + str(bad) if bad else 'OK'} → {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(run())
