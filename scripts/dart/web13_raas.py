# -*- coding: utf-8 -*-
"""13차 9-3 RAAS 매뉴얼(2025.7) — 9차에 받은 hwp 와 그 hwp2md 텍스트만 읽어 산출(웹 요청 없음).

    python3 -I scripts/dart/web13_raas.py        # handoff/13차_산출물/9-3_RAAS.md · dart_out/risk13/9-3_RAAS_낱말문장.csv

  1. Ⅳ.2~Ⅳ.7(보험·금리·투자·유동성·자본적정성·수익성) 비계량 평가항목·세부 점검사항·점검 체크리스트 전문
  2. 󰊱-나-1~󰊱-나-4, 󰊱-다-5 — 9차 발췌(handoff/RAAS_매뉴얼_원문.md)와 글자 대조만(다시 옮기지 않음)
  3. 「금융지주회사」「지주」「대주주」「계열회사」「계열사」가 나오는 문장(문단) 전부

원칙(13차 COMMON13.md): 원본은 다시 받지 않는다(9차 dart_out/raw/web9/raas/). 인용은 전체 md 의 줄을 글자 그대로
옮긴다. 단 hwp2md(9차, 수정 없음)가 건너뛴 「글자 겹치기」(HWP 컨트롤 tcps) 자리에는 hwp 원본에서 읽은 겹침 글자를
`[글자겹침 X]` 표지로 끼워 넣는다 — 표지를 지우면 전체 md 의 줄과 바이트 단위로 같다(스크립트가 확인).
판단(모범규준 조 대응 등)은 md 의 「note:」 줄과 「(판단)」 표시로만.
hwp(내려받은 파일)는 olefile 로 읽기만 한다 — `python3 -I` 로 실행.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(os.path.dirname(HERE)))  # 저장소 루트
import olefile  # noqa: E402
from hwp2md import records, ctrl_id, PARA_TEXT, CTRL_HEADER, EXT_CTRL, INLINE_CTRL  # noqa: E402
from web13 import OUT, WORK, now  # noqa: E402

RAAS = os.path.join("dart_out", "raw", "web9", "raas")
HWP = os.path.join(RAAS, "RAAS_매뉴얼.hwp")
FULL = os.path.join(RAAS, "RAAS_매뉴얼_전체.md")
PREV = os.path.join("handoff", "RAAS_매뉴얼_원문.md")
MD = os.path.join(OUT, "9-3_RAAS.md")
CSV = os.path.join(WORK, "9-3_RAAS_낱말문장.csv")
POST = "https://www.fss.or.kr/fss/bbs/B0000167/view.do?nttId=196121&menuNo=200177"
DOC = "보험회사 위험기준 경영실태평가(RAAS) 매뉴얼(2025년 7월)"
PUA = "\U000f02b1\U000f02b2\U000f02b3\U000f02b4\U000f02b5\U000f02b6\U000f02b7"  # 한글 원문자 ①~⑦(사용자 정의 영역)
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳➀➁➂➃➄➅➆➇➈➉"
TCPS = 23  # HWP 글자 겹치기 컨트롤 문자 코드(hwp2md 의 EXT_CTRL 에 들어 있어 통째로 건너뜀)
MARK = re.compile(r"\[글자겹침 [^\]]+\]")
WORDS = ["금융지주회사", "지주", "대주주", "계열회사", "계열사"]
EXTRA = ["관계회사", "관계사", "자회사", "그룹"]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- hwp: 글자 겹치기 위치
def tcps_in_hwp(path):
    """[(문단 글(hwp2md decode_text 와 같은 결과), 글자 위치, 겹침 글자)] — 문서 순서."""
    ole = olefile.OleFileIO(path)
    head = ole.openstream("FileHeader").read()
    compressed = bool(struct.unpack_from("<I", head, 36)[0] & 1)
    secs = sorted(["/".join(e) for e in ole.listdir() if e[0] == "BodyText"],
                  key=lambda s: int(s.split("Section")[-1]))
    out, pending = [], []
    for sec in secs:
        data = ole.openstream(sec).read()
        if compressed:
            data = zlib.decompress(data, -15)
        for tag, level, payload in records(data):
            if tag == PARA_TEXT:
                assert not pending, "글자 겹치기 컨트롤 헤더 짝이 맞지 않음"
                text, pos = walk(payload)
                pending = [(text, p) for p in pos]
            elif tag == CTRL_HEADER and ctrl_id(payload) == "tcps":
                n = struct.unpack_from("<H", payload, 4)[0]
                chars = payload[6:6 + 2 * n].decode("utf-16-le")
                text, p = pending.pop(0)
                out.append((text, p, chars))
    ole.close()
    assert not pending
    return out


def walk(payload):
    """hwp2md.decode_text 와 같은 규칙으로 글을 만들면서 글자 겹치기 컨트롤이 놓인 글자 위치를 함께 돌려준다."""
    units = struct.unpack("<%dH" % (len(payload) // 2), payload[: len(payload) // 2 * 2])
    out, pos, i = [], [], 0
    while i < len(units):
        c = units[i]
        if c in EXT_CTRL or c in INLINE_CTRL:
            if c == TCPS and struct.pack("<2H", units[i + 1], units[i + 2]) == b"spct":
                pos.append(len(out))
            i += 8
            continue
        if c == 9:
            out.append(0x09)
            i += 8
            continue
        if c == 10:
            out.append(0x0A)
        elif c in (13, 0):
            pass
        elif c == 24:
            out.append(ord("-"))
        elif c in (30, 31):
            out.append(ord(" "))
        elif c < 32:
            pass
        else:
            out.append(c)
        i += 1
    s = struct.pack("<%dH" % len(out), *out).decode("utf-16-le", errors="replace")
    # 위치를 파이썬 글자 수로 바꿈(서로게이트 쌍 = 1글자)
    fix = []
    for p in pos:
        fix.append(len(struct.pack("<%dH" % p, *out[:p]).decode("utf-16-le", errors="replace")))
    return s, fix


def place_marks(L, tc):
    """전체 md 줄에 겹침 글자 자리를 찾는다 → {줄번호: [(열, 글자, 문단 글)]}. 문서 순서대로 앞에서부터 찾는다."""
    marks, cur_line, cur_col = {}, 0, 0
    for text, p, chars in tc:
        s = text.strip()
        lead = len(text) - len(text.lstrip())
        off = max(0, p - lead)
        needle = s.replace("|", "\\|").replace("\n", "<br>")
        rx = re.compile(r"(?:(?<=\| )|(?<=<br>))" + re.escape(needle) + r"(?=<br>| \|)")
        hit = None
        for i in range(cur_line, len(L)):
            m = rx.search(L[i], cur_col if i == cur_line else 0)
            if m:
                hit = (i, m.start())
                break
        assert hit, ("글자 겹치기 자리를 전체 md 에서 찾지 못함", s)
        i, col = hit
        marks.setdefault(i + 1, []).append((col + off, chars, s))
        cur_line, cur_col = i, col + len(needle)
    return marks


def marked(L, marks, n):
    line = L[n - 1]
    for col, chars, _ in sorted(marks.get(n, []), reverse=True):
        line = line[:col] + "[글자겹침 %s]" % chars + line[col:]
    assert MARK.sub("", line) == L[n - 1]
    return line


# ---------------------------------------------------------------- 표·위치
def cells(line):
    inner = line[1:-1]
    return [c[1:-1] if len(c) >= 2 else "" for c in re.split(r"(?<!\\)\|", inner)]


def is_row(line):
    return line.startswith("|") and line.endswith("|") and not re.fullmatch(r"\|(?:---\|)+", line)


def toc(L):
    """목차 줄 → {(장, 절키): 쪽}, 목차 줄 범위."""
    start = L.index("목 차")
    pages, chap, end = {}, None, None
    for i in range(start, len(L)):
        t = L[i]
        m = re.match(r"^\s*(.*?)\s*(?:\t|…+)\s*(\d+)\s*$", t)
        if not m:
            continue
        title, page = m.group(1), int(m.group(2))
        r = re.match(r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ)\.", title)
        if r:
            chap = r.group(1)
            pages[(chap, None)] = page
        elif title.startswith("[별첨]"):
            pages[("별첨", None)] = page
            end = i + 1
            break
        elif re.match(r"^<붙임(\d)>", title):
            pages[(chap, "붙임" + re.match(r"^<붙임(\d)>", title).group(1))] = page
        else:
            pages[(chap, re.match(r"^(\d+)\.", title).group(1))] = page
    return pages, start + 1, end


class Where:
    """줄마다 장·절·항목 위치(사람이 읽는 경로)와 목차 쪽 키."""

    def __init__(self, L):
        self.info = {}
        chap = chap_t = sec = sub = part = None
        key = None
        art = hang = ho = None
        tbl_head = None
        prev_row = False
        for n, t in enumerate(L, 1):
            s = t.strip()
            nxt = next((x.strip() for x in L[n:n + 6] if x.strip()), "")
            if s in ("Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ"):
                chap, chap_t, sec, sub, part, key = s, nxt, None, None, None, (s, None)
            elif s == "[별첨]":
                chap, chap_t, sec, sub, part, key = "별첨", nxt, None, None, None, ("별첨", None)
                art = hang = ho = None
            elif chap in ("Ⅰ", "Ⅱ") and re.match(r"^\d+\.\s*\S", t):
                sec, sub, part = s, None, None
                key = (chap, re.match(r"^(\d+)\.", t).group(1))
            elif chap == "Ⅱ" and re.fullmatch(r"<붙임\d>", s):
                sec, sub, part = s + " " + nxt, None, None
                key = (chap, "붙임" + s[3])
            elif chap == "Ⅱ" and (s.startswith("▣ ") or (sec or "").startswith("<붙임1>") and re.fullmatch(r"□ \S+", s)):
                sub = s
            elif chap == "Ⅲ" and re.match(r"^ \d\. ", t):
                sec, sub = s, None
                key = (chap, s.split(".")[0])
            elif chap == "Ⅲ" and re.fullmatch(r"\| [가-하]\. .+ \|", t):
                sub = cells(t)[0]
            elif chap == "Ⅳ" and len(s) > 2 and s[0] in PUA and s[1] == " ":
                sec, sub, part = "Ⅳ.%d %s" % (PUA.index(s[0]) + 1, s[2:]), None, "평가항목·세부 점검사항 표"
                key = (chap, str(PUA.index(s[0]) + 1))
            elif chap == "Ⅳ" and re.match("^[" + PUA + r"]-[가-하]\. ", s):
                sub, part = s, None
            elif chap == "Ⅳ" and s.startswith("<<세부 점검사항(재보험사)"):
                sub, part = s, None
            elif chap == "Ⅳ" and s.startswith("<<세부 점검사항"):
                part = s + " 목록"
            elif chap == "Ⅳ" and s == "세부 점검사항별 점검 체크리스트":
                part = "점검 체크리스트 표"
            elif chap == "별첨" and s.startswith("□ "):
                sec, sub, art, hang, ho = s, None, None, None, None
            elif chap == "별첨" and (s.startswith("[감독규정 별표") or s.startswith("<시행세칙 별표")):
                sub, art, hang, ho = s + " " + nxt, None, None, None
            elif chap == "별첨" and re.match(r"^제\s?[\d-]+조(?:의\s?\d+)?\(", s):
                art, hang, ho = re.match(r"^(제\s?[\d-]+조(?:의\s?\d+)?\([^)]*\))", s).group(1), None, None
            if chap == "별첨" and art:
                m = re.match(r"^\s*([①-⑳])", t)
                if m:
                    hang, ho = m.group(1), None
                m = re.match(r"^(\d+)\.\s", t)
                if m:
                    ho = m.group(1) + "."
            row = is_row(t)
            if row and not prev_row:
                tbl_head = cells(t)
            prev_row = row or bool(re.fullmatch(r"\|(?:---\|)+", t))
            parts = [x for x in ((chap + ". " + chap_t) if chap and chap != "별첨" else ("[별첨] " + chap_t) if chap else "표지·목차",
                                 sec, sub) if x]
            if chap == "Ⅳ" and part:
                parts.append(part)
            if chap == "별첨" and art:
                parts.append(art + (" " + hang if hang else "") + (" " + ho if ho else ""))
            self.info[n] = dict(path=" > ".join(parts), key=key, head=tbl_head if row else None, row=row)

    def path(self, n):
        return self.info[n]["path"]


# ---------------------------------------------------------------- 문장(문단) 단위
def units(L, n, hdr):
    """줄 n 의 문장 단위: 표 줄은 칸마다 <br> 로 나눈 문단(첫 칸=항목 이름은 칸 전체), 그 밖은 줄 전체.
    [(칸 이름, 칸 번호, 문단, 그 문단이 딸린 질문 번호)]"""
    t = L[n - 1]
    if not is_row(t):
        return [("", None, t, "")]
    out = []
    cs = cells(t)
    for j, c in enumerate(cs):
        name = hdr[j] if hdr and j < len(hdr) else ""
        if j == 0:
            out.append((name, j, c, ""))
            continue
        segs = c.split("<br>")
        q = ""
        for sg in segs:
            k = qnum(sg)
            if k:
                q = k
            out.append((name, j, sg, q if not k else ""))
    return out


def qnum(seg):
    """문단이 체크리스트 질문(①②…)으로 시작하면 그 번호(글자겹침 표지 안의 번호 포함)."""
    m = re.match(r"^\[글자겹침 (.)\]", seg)
    if m and m.group(1) in CIRC:
        return m.group(1)
    return seg[:1] if seg[:1] in CIRC else ""


def hits(seg, words):
    got = []
    for w in words:
        if w in seg:
            got.append(w)
    return got


def label(got, seg):
    lab = []
    for w in got:
        if w == "지주" and "금융지주회사" in got and seg.count("지주") == seg.count("금융지주회사"):
            continue
        if w == "대주주" and seg.count("대주주") == seg.count("최대주주"):
            lab.append("대주주(「최대주주」 안)")
        elif w == "대주주" and "최대주주" in seg:
            lab.append("대주주(「최대주주」 포함)")
        else:
            lab.append(w)
    if "금융지주회사" in got and "지주" in got and seg.count("지주") == seg.count("금융지주회사"):
        lab = ["금융지주회사·지주(「금융지주회사」 안)" if x == "금융지주회사" else x for x in lab]
    return " · ".join(lab)


# ---------------------------------------------------------------- 산출
def main():
    meta = json.load(open(HWP + ".meta.json", encoding="utf-8"))
    h_hwp, h_full = sha(HWP), sha(FULL)
    assert h_hwp == meta["sha256"], "hwp sha256 이 9차 meta 와 다름"
    prev_txt = open(PREV, encoding="utf-8").read()
    rec = re.search(r"RAAS_매뉴얼_전체\.md\(sha256 ([0-9a-f]{64})\)", prev_txt).group(1)
    assert h_full == rec, "전체 md sha256 이 9차 기록과 다름"
    L = open(FULL, encoding="utf-8").read().split("\n")
    if L and L[-1] == "":
        L = L[:-1]
    P = prev_txt.split("\n")
    pages, toc_a, toc_b = toc(L)
    W = Where(L)

    def prevno(n):
        for a, b, d in ((1008, 1106, 959), (491, 518, 475)):
            if a <= n <= b:
                assert P[n - d - 1] == L[n - 1], ("9차 발췌 줄과 다름", n)
                return n - d
        return None

    def page(n):
        k = W.info[n]["key"]
        if k is None:
            return "목차 앞"
        if k in pages:
            return "목차상 %d쪽~(이 절의 시작 쪽)" % pages[k]
        return "목차상 %d쪽~(장의 시작 쪽)" % pages[(k[0], None)] if (k[0], None) in pages else "목차 쪽 없음"

    tc = tcps_in_hwp(HWP)
    marks = place_marks(L, tc)

    def quote(a, b):
        out = []
        for n in range(a, b + 1):
            ln = marked(L, marks, n)
            out.append("> " + ln if ln else ">")
        return out

    def cite(a, b, pg):
        return "[%s · %s · %s · 전체 md %d~%d행 · 수집 2026-10-01(9차 원본), 옮김 2026-10-07]" % (DOC, POST, pg, a, b)

    # ---- Ⅳ 부문 범위
    starts = {}
    for n, t in enumerate(L, 1):
        if len(t) > 2 and t[0] in PUA and t[1] == " " and W.info[n]["key"] and W.info[n]["key"][0] == "Ⅳ":
            starts[PUA.index(t[0]) + 1] = (n, t[2:])
    bj = L.index("[별첨]") + 1
    ranges = {}
    for k in range(1, 8):
        a = starts[k][0]
        b = (starts[k + 1][0] if k < 7 else bj) - 1
        while not L[b - 1].strip():
            b -= 1
        ranges[k] = (a, b, starts[k][1])
    assert ranges[1][0] == 1010 and ranges[1][1] == 1106, ranges[1]

    # ---- 항목 번호 목록(세 군데) 대조
    def norm(s):
        s = MARK.sub("", s).replace("<br>", "")
        s = re.sub("[\u2024\u00b7\u2027\uff65\u30fb\u318d\u2025]", "·", s)
        return re.sub(r"\s+", "", s)
    numrx = re.compile("^(?:\\[글자겹침 ([" + PUA + "])\\])?([" + PUA + "])?-([가-하])[-.](\\d+)\\.?\\s*(.*)$", re.S)
    lists = {}  # (부문, 평가항목, 번호, 재보험사?) -> {A|B|C: (줄, 이름)}
    for k in range(1, 8):
        a, b, _ = ranges[k]
        rein = False
        for n in range(a, b + 1):
            t = marked(L, marks, n)
            if t.startswith("<<세부 점검사항(재보험사)>>"):
                rein = True
            if is_row(t) and W.info[n]["head"] and W.info[n]["head"][0] == "평가항목":
                c = cells(t)
                if c[0] == "평가항목":
                    continue
                r2 = "<<재보험사>>" in c[1]
                for sg in c[1].split("<br>"):
                    m = numrx.match(sg)
                    if m:
                        lists.setdefault((k, m.group(3), m.group(4), r2), {})["A"] = (n, sg)
            elif is_row(t) and W.info[n]["head"] and W.info[n]["head"][0] == "세부 점검사항":
                c0 = cells(t)[0]
                if c0 == "세부 점검사항":
                    continue
                m = numrx.match(c0.replace("<br>", " ", 1))
                if m:
                    lists.setdefault((k, m.group(3), m.group(4), rein), {})["C"] = (n, c0)
            elif re.match("^ [" + PUA + "]-[가-하]-\\d", t):
                m = numrx.match(t.strip())
                lists.setdefault((k, m.group(3), m.group(4), rein), {})["B"] = (n, t.strip())
    name_diffs = []
    for key_, d in sorted(lists.items()):
        nm = {}
        for src, (n, s) in d.items():
            m = numrx.match(s.replace("<br>", " ", 1))
            nm[src] = (n, s, norm(m.group(5)))
        vals = {v[2] for v in nm.values()}
        if len(vals) > 1 or len(nm) < 3:
            name_diffs.append((key_, nm))
    numfmt = [(n, cells(L[n - 1])[0]) for k in range(2, 8) for n in range(ranges[k][0], ranges[k][1] + 1)
              if is_row(L[n - 1]) and re.match("^[" + PUA + r"]-[가-하]\.\d", cells(L[n - 1])[0])]

    # ---- 낱말 문장
    found, extra = [], []
    for n in range(1, len(L) + 1):
        hdr = W.info[n]["head"]
        for col, j, seg, q in units([marked(L, marks, n)], 1, hdr):
            g = hits(seg, WORDS)
            if g:
                found.append(dict(n=n, col=col, j=j, seg=seg, q=q, got=g))
            g2 = hits(seg, EXTRA)
            if g2 and not g:
                extra.append(dict(n=n, col=col, j=j, seg=seg, q=q, got=g2))

    def loc(f):
        n = f["n"]
        s = W.path(n)
        if W.info[n]["row"]:
            row_lab = cells(L[n - 1])[0]
            s += " > 「%s」 행" % (row_lab if row_lab else "(첫 칸 빈칸)")
            s += " · %s 칸" % (f["col"] or "%d번째" % (f["j"] + 1))
            if f["q"]:
                s += " · 질문 %s 아래" % f["q"]
        return s

    cnt = {w: sum(f["seg"].count(w) for f in found) for w in WORDS}
    cnt_seg = {w: sum(1 for f in found if w in f["got"]) for w in WORDS}

    # ---- 모범규준 조 대응(판단): 사용자 지시서에 이름이 나온 조만, 근거 문항은 스크립트가 찾아 줄 번호를 붙인다
    MAP = [
        ("5조(위험관리 원칙)", "󰊱-나-1", r"리스크관리 기본원칙"),
        ("21조(신용위험)", "󰊴-가-1", None),
        ("21조(신용위험)", "󰊴-가-2", None),
        ("22조(시장위험)", "󰊴-가-3", None),
        ("22조(시장위험)", "󰊴-가-4", None),
        ("24조(금리위험)", "󰊳-가-1", None),
        ("24조(금리위험)", "󰊳-가-2", None),
        ("24조(금리위험)", "󰊳-나-1", None),
        ("24조(금리위험)", "󰊳-나-2", None),
        ("27조(전략·평판위험)", "󰊱-나-2", r"비재무리스크"),
        ("28조(통합리스크관리시스템)", "󰊱-나-1", r"ERM|ORSA"),
        ("28조(통합리스크관리시스템)", "󰊶-나-1", r"자체위험 및 지급여력 평가"),
        ("28조(통합리스크관리시스템)", "󰊶-나-3", r"통합리스크|리스크허용한도"),
        ("30조(적합성 검증)", "󰊱-나-1", r"주기적으로 검증"),
        ("30조(적합성 검증)", "-가-1", r"사후검증|사후 검증"),
        ("30조(적합성 검증)", "󰊴-가-3", r"사후검증|사후 검증"),
        ("30조(적합성 검증)", "-나-2", r"적합성 검증"),
        ("34조(해외위험)", "󰊴-나-", r"해외"),
        ("53조(위기대응조직)", "󰊵-가-2", r"역할 분담|직무에 관한"),
        ("53조(위기대응조직)", "-나-2", r"단계별 대응방안"),
        ("55조(조기경보)", "-가-2", r"조기경보"),
        ("55조(조기경보)", "-가-4", r"조기경보"),
        ("55조(조기경보)", "󰊴-나-1", r"조기경보"),
        ("55조(조기경보)", "-나-3", r"조기경보"),
    ]
    map_rows = []
    seen = set()
    for art, prefix, rx in MAP:
        for n in range(1010, ranges[7][1] + 1):
            t = L[n - 1]
            if not (is_row(t) and W.info[n]["head"] and W.info[n]["head"][0] == "세부 점검사항"):
                continue
            c0 = cells(marked(L, marks, n))[0]
            if c0 == "세부 점검사항":
                continue
            c0n = re.sub(r"\[글자겹침 ([^\]]+)\]", r"\1", c0)
            if not (c0n.startswith(prefix) or (prefix.startswith("-") and c0n[1:].startswith(prefix))):
                continue
            for col, j, seg, q in units([marked(L, marks, n)], 1, W.info[n]["head"]):
                if j != 1:
                    continue
                ok = bool(qnum(seg)) if rx is None else bool(re.search(rx, seg))
                if ok and (art, n, seg) not in seen:
                    seen.add((art, n, seg))
                    map_rows.append((art, n, c0, q or qnum(seg), seg))

    # ---------------------------------------------------------------- md 쓰기
    o = []
    w = o.append
    w("# 9-3 RAAS 매뉴얼(2025.7) — 13차(리스크부문 작업 9: 모범규준 조항 기준 표 보강)")
    w("")
    w("- 출처: 금융감독원 게시글 「%s」 %s · 첨부 원파일명 `%s` · 다운로드 URL %s" % (meta["게시글제목"], POST, meta["원파일명"], meta["출처URL"]))
    w("- 원본: 9차에 받은 hwp `%s`(%s · HTTP %s · %d바이트 · sha256 `%s` — 9차 .meta.json 값과 다시 계산한 값이 같음). **이번에 다시 받지 않았다(웹 요청 0건).**"
      % (HWP, meta["fetched_at"], meta["http_status"], meta["바이트"], h_hwp))
    w("- 텍스트: 9차 hwp2md(`scripts/dart/hwp2md.py`, 수정 없음) 결과 `%s`(%d줄 · sha256 `%s` — 이 파일에는 .meta.json 이 따로 없고, 9차 발췌 `%s` 7행에 적힌 sha256 과 다시 계산한 값이 같음). **줄 번호는 모두 이 파일 기준(1부터).**"
      % (FULL, len(L), h_full, PREV))
    w("- 9차에 이미 옮긴 발췌: `%s`(붙임2 491~518행 · Ⅳ.1 경영관리리스크 1008~1107행). 이번에 그 범위는 다시 옮기지 않고 글자 대조만 했다(2절)." % PREV)
    w("- 작성: 2026-10-07(실행 시각 %s) · 스크립트 `scripts/dart/web13_raas.py`(`python3 -I` 로 실행; hwp 는 olefile 로 읽기만)." % now())
    w("- 방법: ① 목차(전체 md %d~%d행)에서 Ⅳ장 각 부문의 시작 쪽을 읽고, 본문에서 부문 머리(「󰊲 보험리스크」 등) 줄부터 다음 부문 머리 앞 줄까지를 통째로 옮겼다. "
      "② 「1-나-1」 등은 매뉴얼의 번호 「󰊱-나-1」(󰊱=① 경영관리리스크 부문, 나=평가항목, 1=세부 점검사항)이다(0절). "
      "③ 낱말 문장은 전체 md 1~%d행 전부를 찾았다(문장 단위는 아래 표기 규칙)." % (toc_a, toc_b, len(L)))
    w("- 한계: ① hwp 에는 쪽 정보가 없다(9차와 같음). 쪽은 **목차에 적힌 시작 쪽**만 적고, 부문의 끝 쪽은 「다음 항목 시작 쪽 − 1」로 적었다(판단). 문장 하나하나의 쪽은 모른다 — 대신 줄 번호를 적었다. "
      "② hwp2md 가 HWP 의 「글자 겹치기」 컨트롤(tcps)을 건너뛰어 Ⅳ장 안 %d곳에서 글자가 빠졌다(4-1절). 이 문서는 그 자리에 hwp 원본에서 읽은 글자를 `[글자겹침 X]` 표지로 넣었다. "
      "같은 이유로 건너뛴 수식(eqed)·그리기 개체(gso)는 모두 표지·목차·Ⅲ장 산식·별첨에 있고 Ⅳ장에는 없다(hwp 레코드 순서로 앞 문단을 보아 확인). "
      "③ 「추출 범위에 없음」은 적힌 범위에서 찾지 못했다는 뜻이지 없다는 단정이 아니다." % len(tc))
    w("- 모범규준 조 번호: 사용자 지시서 9-3 에는 조 번호가 없다. 폐지 모범규준 원문이 저장소에 없으므로, 지시서 다른 작업(9-4)에 조 제목과 함께 나온 조(3·4·5·17·21·22·24·27·28·30·34·53·55조)에만 「(판단)」으로 대응을 붙였다(5절).")
    w("")
    w("## 표기 규칙")
    w("")
    w("- 원문 인용은 `>` 인용 블록. 인용 블록의 각 줄 = `> ` + 전체 md 의 같은 줄 그대로(빈 줄은 `>`). 해설·판단은 인용 밖 「note:」 줄, 해석이 들어간 곳은 「(판단)」.")
    w("- hwp2md 표기를 고치지 않았다: `<br>` = 표 칸 안의 문단 나눔, `\\|` = 칸 안 글자 「|」, `[내부표] … / …` = 칸 안에 든 표를 한 칸에 펼친 것(행은 ` / `), "
      "`|  |` 처럼 빈 칸은 원문 칸이 비었거나 수식·그림이라 글이 없는 칸. 표는 hwp 의 행·열을 그대로 md 표로 옮긴 것이라 셀 병합은 풀려 있다.")
    w("- 「󰊱 󰊲 󰊳 󰊴 󰊵 󰊶 󰊷」은 한글 문서의 원문자(①~⑦)가 사용자 정의 영역 글자(U+F02B1~U+F02B7)로 나온 것이다(9차와 같음). 글꼴에 따라 네모·빈칸으로 보일 수 있다.")
    w("- `[글자겹침 X]` = 이 문서가 넣은 표지. hwp 의 글자 겹치기 컨트롤에 든 글자 X 를 그 자리에 적은 것이다. 표지를 지우면 전체 md 의 줄과 같다(스크립트가 줄마다 확인).")
    w("- 문장 단위(3절): 표 밖은 줄 하나(= hwp 문단 하나). 표 안은 칸을 `<br>` 로 나눈 문단 하나. 단 표의 첫 칸(평가부문·세부 점검사항 이름)은 칸 전체를 한 단위로 본다(이름이 `<br>` 로 끊겨 있어서).")
    w("")

    # 0절
    w("## 0. 매뉴얼 번호 체계와 목차 위치")
    w("")
    w(cite(toc_a, toc_b, "목차"))
    w("")
    o.extend(quote(toc_a, toc_b))
    w("")
    w("- note: 목차에 Ⅳ장 「비계량평가항목 세부 평가기준」(53쪽)과 그 아래 1.~7. 부문이 모두 있다 — 사용자가 말한 6개 부문(보험·금리·투자·유동성·자본적정성·수익성)은 **모두 이 매뉴얼 Ⅳ.2~Ⅳ.7 에 있다**(다른 자료·붙임으로 미룬 부문 없음).")
    w("- note: 번호 「1-나-1」 = 본문 「󰊱-나-1.」 — Ⅳ.1 경영관리리스크 부문(󰊱)의 평가항목 「󰊱-나. 리스크관리체제의 적정성」의 세부 점검사항 1번 「리스크관리 체제구축」(전체 md 1016·1041·1050행). "
      "「1-다-5」 = 「󰊱-다-5. 일반관리 및 금융사고 예방」(평가항목 「󰊱-다. 내부통제의 적정성」, 1017·1061·1073행). 세부 점검사항마다 「점검 체크리스트」(①②… 질문과 ▫ 점검 내용)가 붙어 있다 — 사용자 표현 「세부 점검 문항」은 이 체크리스트에 해당(판단).")
    a2 = next(n for n in range(1, len(L)) if L[n - 1].strip().startswith("◦ [2단계]"))
    w("")
    w("### 0-1 비계량 평가 방법(Ⅱ.7 평가등급 산정기준 가운데 2단계) — 9차 발췌에 없음")
    w("")
    w(cite(a2, a2 + 5, page(a2)))
    w("")
    o.extend(quote(a2, a2 + 5))
    w("")
    w("- note: 위 241행은 세부 점검사항을 「Ⅴ. 비계량평가항목 세부 점검사항」이라고 부르지만, 목차·본문의 장 번호는 「Ⅳ. 비계량평가항목 세부 평가기준」이다(원문 안 표기 차이, 4-2절).")
    b5 = L.index("<붙임5>") + 1
    e5 = next(n for n in range(b5, len(L)) if L[n - 1].startswith("| 합계"))
    w("")
    w("### 0-2 <붙임5> 비계량평가 항목별 가중치 — 9차 발췌에 없음")
    w("")
    w(cite(b5, e5, page(b5)))
    w("")
    o.extend(quote(b5, e5))
    w("")

    # 1절
    w("## 1. 6개 부문 비계량 평가항목·세부 점검사항·점검 체크리스트 전문(Ⅳ.2~Ⅳ.7)")
    w("")
    w("- note: 부문마다 ① 평가항목·세부 점검사항 표 → ② 평가항목별 「<<세부 점검사항>>」 목록 → ③ 「세부 점검사항별 점검 체크리스트」 표(세부 점검사항 | 점검 체크리스트 | 비 고) 순서다. 아래는 부문 머리 줄부터 다음 부문 머리 앞까지 빠짐없이 옮겼다.")
    w("- note: 「보험리스크」에는 일반보험사용 세부 점검사항과 「<<재보험사>>」용 세부 점검사항(번호가 다시 󰊲-나-1·󰊲-나-2)이 함께 있다.")
    w("")
    for k in range(2, 8):
        a, b, nm = ranges[k]
        p0 = pages[("Ⅳ", str(k))]
        p1 = (pages[("Ⅳ", str(k + 1))] if k < 7 else pages[("별첨", None)]) - 1
        w("### 1-%d Ⅳ.%d %s — 목차상 %d쪽~%d쪽(끝 쪽은 판단) · 전체 md %d~%d행" % (k - 1, k, nm, p0, p1, a, b))
        w("")
        rows = []
        for n in range(a, b + 1):
            t = L[n - 1]
            if is_row(t) and W.info[n]["head"] and W.info[n]["head"][0] == "세부 점검사항" and cells(t)[0] != "세부 점검사항":
                c0 = cells(marked(L, marks, n))[0]
                rows.append((n, c0, len(marks.get(n, []))))
        sub_h = [(n, L[n - 1].strip()) for n in range(a, b + 1) if re.match("^[" + PUA + r"]-[가-하]\. ", L[n - 1].strip())]
        w("- 평가항목(머리 줄): " + " · ".join("「%s」(%d행)" % (s, n) for n, s in sub_h))
        w("- 점검 체크리스트 표의 세부 점검사항 행(첫 칸 그대로):")
        w("")
        w("| 전체 md 줄 | 세부 점검사항(첫 칸) | 글자겹침 표지 수 |")
        w("|---|---|---|")
        for n, c0, mk in rows:
            w("| %d | %s | %s |" % (n, c0, mk or ""))
        w("")
        w(cite(a, b, "Ⅳ.%d %s, 목차상 %d쪽~" % (k, nm, p0)))
        w("")
        o.extend(quote(a, b))
        w("")
    # 2절
    w("## 2. 1-나-1 ~ 1-나-4, 1-다-5 — 모두 9차 발췌에 이미 있음(다시 옮기지 않음)")
    w("")
    w("| 번호(사용자 표기) | 매뉴얼 번호·이름(전체 md 그대로) | 평가항목 | 체크리스트 행: 전체 md 줄 | 9차 파일 줄(`handoff/RAAS_매뉴얼_원문.md`) | 글자 대조 | 상태 |")
    w("|---|---|---|---|---|---|---|")
    targets = [("1-나-1", "󰊱-나-1."), ("1-나-2", "󰊱-나-2."), ("1-나-3", "󰊱-나-3."), ("1-나-4", "󰊱-나-4."), ("1-다-5", "󰊱-다-5.")]
    for u, pre in targets:
        n = next(n for n in range(1008, 1107) if is_row(L[n - 1]) and cells(L[n - 1])[0].startswith(pre))
        m = prevno(n)
        same = "같음" if P[m - 1] == L[n - 1] else "다름"
        sub = next(s for s in reversed([x for x in [(q, L[q - 1].strip()) for q in range(1008, n)]
                                        if re.match("^[" + PUA + r"]-[가-하]\. ", x[1])]))
        w("| %s | %s | %s(%d행) | %d | %d | 바이트 단위 %s | 이미 받음(9차 파일 %d행) |" % (u, cells(L[n - 1])[0], sub[1], sub[0], n, m, same, m))
    w("")
    lst = [n for n in range(1008, 1107) if re.match(r"^ 󰊱-(나-[1-4]|다-5)\. ", L[n - 1]) or
           (is_row(L[n - 1]) and re.match(r"^󰊱-(나|다)\. ", cells(L[n - 1])[0]))]
    w("- 목록 줄(평가항목·세부 점검사항 표, <<세부 점검사항>> 목록)도 9차 파일에 있음: " + ", ".join("전체 %d행 = 9차 %d행" % (n, prevno(n)) for n in lst) + ".")
    w("- note: 9차 발췌(Ⅳ.1, 전체 1008~1106행 ↔ 9차 49~147행)는 전체 md 와 줄마다 바이트 단위로 같다(1107행 빈 줄 하나만 9차 파일에서 빠짐). Ⅳ.1 범위에는 글자 겹치기 누락이 없다(4-1절의 %d곳은 모두 Ⅳ.2 이후)." % len(tc))
    w("- note: 「1-나-3 IT리스크관리」는 정보기술부문 실태평가를 실시하면 평가에서 빠진다는 서술이 Ⅱ.7 에 있다(아래, 9차 발췌에 없음).")
    a3 = next(n for n in range(1, len(L)) if "정보기술부문 실태평가 결과를 20% 반영" in L[n - 1])
    b3 = next(n for n in range(a3, len(L)) if L[n - 1].startswith("| <참고><br>전자금융감독규정"))
    w("")
    w(cite(a3, b3, page(a3)))
    w("")
    o.extend(quote(a3, b3))
    w("")
    # 3절
    w("## 3. 「금융지주회사」「지주」「대주주」「계열회사」「계열사」가 나오는 문장")
    w("")
    w("- 찾은 범위: 전체 md 1~%d행 전부(표지·목차·Ⅰ~Ⅳ장·붙임·별첨). 낱말은 글자열 그대로 찾았다(「대주주」는 「최대주주」 안의 것도 걸림 — 따로 표시)." % len(L))
    w("- 문장 수: %d개. 낱말별(문장 수 / 나온 횟수): " % len(found) + " · ".join("%s %d / %d" % (x, cnt_seg[x], cnt[x]) for x in WORDS))
    w("- note: 「지주」는 모두 「금융지주회사」 안에서만 나온다(별첨에 옮겨 실은 보험업감독규정 제7-18조·제7-19조). 매뉴얼 본문(Ⅰ~Ⅳ장)에는 「금융지주회사」「지주」가 없다(찾은 범위: 1~%d행, 별첨 시작 %d행)." % (bj - 1, bj))
    w("- note: 「계열회사」「계열사」는 Ⅳ장 3곳(󰊱-가-1, 󰊱-다-5, 󰊲-나-2(재보험사))에만 나온다.")
    w("")
    rows_csv = []
    for i, f in enumerate(found, 1):
        n = f["n"]
        pn = prevno(n)
        lab = label(f["got"], f["seg"])
        w("**3-%02d** · 걸린 낱말: %s · 위치: %s · %s · 전체 md %d행%s" % (i, lab, loc(f), page(n), n, (" · 9차 파일 %d행(이미 받음)" % pn) if pn else ""))
        w("")
        seg = f["seg"]
        w("> " + seg)
        w("")
        rows_csv.append({"번호": "3-%02d" % i, "걸린낱말": lab, "위치": loc(f), "목차쪽": page(n), "전체md줄": n,
                         "9차파일줄": pn or "", "문장": seg})
    w("### 3-참고 「관계회사」「관계사」「자회사」「그룹」(지시 범위 밖 — 지주·계열 관계를 다룬 다른 낱말이라 참고로 붙임, 판단)")
    w("")
    w("- 위 3절 문장과 겹치는 것은 뺐다. 찾은 범위는 같음(1~%d행)." % len(L))
    w("")
    for i, f in enumerate(extra, 1):
        n = f["n"]
        pn = prevno(n)
        w("**3-참고-%02d** · 걸린 낱말: %s · 위치: %s · %s · 전체 md %d행%s" % (i, " · ".join(f["got"]), loc(f), page(n), n, (" · 9차 파일 %d행(이미 받음)" % pn) if pn else ""))
        w("")
        w("> " + f["seg"])
        w("")
    # 4절
    w("## 4. 원문과 다른 곳 · 원문 안 표기 차이")
    w("")
    w("### 4-1 hwp2md 가 뺀 「글자 겹치기」 글자(%d곳) — hwp 원본에는 있음" % len(tc))
    w("")
    w("- 확인 방법: hwp 의 BodyText 레코드에서 문단 글(PARA_TEXT) 안 컨트롤 문자 23(글자 겹치기)과 그 컨트롤 헤더(`tcps`)의 겹침 글자 배열을 읽었다(HWP 5.0 문서 형식의 글자 겹치기 구조: 길이 WORD + 글자 WCHAR 배열). "
      "hwp2md 는 이 컨트롤을 8글자 단위로 건너뛰므로 겹침 글자가 텍스트에서 빠진다. 위치는 같은 문단 글을 전체 md 에서 문서 순서대로 찾아 정했다.")
    w("")
    w("| # | 전체 md 줄 | 위치 | 겹침 글자(hwp) | 전체 md 에 나온 글(문단) |")
    w("|---|---|---|---|---|")
    i = 0
    for n in sorted(marks):
        for col, chars, s in marks[n]:
            i += 1
            w("| %d | %d | %s | %s | %s |" % (i, n, W.path(n), chars, s))
    w("")
    w("- note: 15곳은 세부 점검사항 번호 앞의 부문 원문자(󰊲·󰊶)가, 3곳은 체크리스트 질문 번호(②·③)가 빠진 것이다. 원문 글자는 위 표의 겹침 글자이고, 1절 인용에는 `[글자겹침 X]` 로 넣었다.")
    w("")
    w("### 4-2 매뉴얼 안에서 같은 항목의 이름·번호 표기가 다른 곳")
    w("")
    w("| 위치 | 평가항목 표(A) | <<세부 점검사항>> 목록(B) | 점검 체크리스트 표 첫 칸(C) |")
    w("|---|---|---|---|")
    for key_, nm in name_diffs:
        k, ga, no, rein = key_
        lab = "Ⅳ.%d %s-%s-%s%s" % (k, PUA[k - 1], ga, no, " (재보험사)" if rein else "")
        w("| %s | %s | %s | %s |" % (lab, *("%d행 「%s」" % (nm[s][0], nm[s][1]) if s in nm else "없음" for s in "ABC")))
    for n, c0 in numfmt:
        w("| Ⅳ %d행 번호 형식 | — | — | %d행 「%s」 — 평가항목 기호와 세부 번호 사이가 다른 행처럼 「-」가 아니라 「.」 |" % (n, n, c0))
    w("| Ⅱ.7 2단계(241행) | — | — | 세부 점검사항을 「Ⅴ. 비계량평가항목 세부 점검사항」이라 부름 ↔ 목차·본문은 「Ⅳ. 비계량평가항목 세부 평가기준」 |")
    w("")
    w("- note: 비교는 띄어쓰기와 가운뎃점 종류(․·‧･)를 무시하고 했다. 위 표에 없는 세부 점검사항은 세 곳 이름이 같다.")
    w("- note: 게시글 제목은 「…매뉴얼(2025년 7월)」, 첨부 파일명은 「25.6월 기준 … 매뉴얼_개정판(대외용)」, 표지는 「…운영매뉴얼 / 2025. 7.」이다(같은 문서의 다른 이름).")
    w("")
    # 5절
    w("## 5. 모범규준 조 대응 (판단)")
    w("")
    w("- note: 모두 「(판단)」. 조 제목은 사용자 지시서 9-4 에 적힌 표현이고 모범규준 원문으로 확인하지 못했다. 근거 문항은 1절 인용 안의 글이며 줄 번호는 전체 md 기준.")
    w("- note: 주제1 표의 칸은 「자회사 평가·기준(RAAS 등)」 칸(판단).")
    w("")
    w("| 모범규준 조(판단) | RAAS 세부 점검사항(첫 칸) | 전체 md 줄 | 질문 | 근거 문단(원문 그대로) |")
    w("|---|---|---|---|---|")
    for art, n, c0, q, seg in map_rows:
        w("| %s | %s | %d | %s | %s |" % (art, c0, n, q, seg))
    w("")
    a4, b4 = ranges[1][0], ranges[7][1]
    def cnt_in(word):
        return [n for n in range(a4, b4 + 1) if word in L[n - 1]]
    zero = [x for x in ("철학", "적용 제외", "적용제외", "경미", "해외진출", "해외사업", "현지법인") if not cnt_in(x)]
    other = ["「%s」 %s행" % (x, "·".join(map(str, cnt_in(x)))) for x in ("제외", "문서", "지시", "통보") if cnt_in(x)]
    w("- note: 3조(위험이 경미한 자회사 적용 제외)·4조(위험관리 철학)·17조(지주→자회사 의사 전달 문서 형식)에 대응하는 문항은 Ⅳ장(%d~%d행)에서 **추출 범위에 없음**. "
      "찾은 방법: Ⅳ장 줄 전부에서 낱말 검색 — %s 은 0건, %s 은 나오지만 모두 다른 맥락(유동성자산에서 제외, 의사록·회의록 문서화, 감독당국 지시사항 전파, 점검 결과 통보 등)이다(판단)."
      % (a4, b4, "·".join("「%s」" % x for x in zero), ", ".join(other)))
    w("- note: 34조(해외위험)는 해외**투자** 문항(󰊴-나-1~3)과 해외 신종자본증권 환율 문항(󰊶-다-2, 1369행)만 있다. 해외진출·해외사업(현지법인) 리스크의 총괄·사전 검토·정기 점검을 보는 비계량 문항은 Ⅳ장에서 추출 범위에 없음(위 검색). "
      "Ⅱ.14 「해외 현지법인 및 지점에 대한 평가기준」(목차상 17쪽)은 현지법인·지점 자체를 계량평가하는 기준이다.")
    w("- note: 자회사를 다루는 RAAS 비계량 문항은 󰊱-나-4 관계회사 리스크관리(1053행, 9차 발췌 94행)와 󰊵-가-1 「자회사 및 관계회사의 유동성리스크」(1309행)뿐이다(3-참고). 이 둘은 보험회사가 자기 자회사를 보는 문항이라, 지주의 자회사 관리 조항과 겹치는 조 번호는 지시서에 없어 붙이지 않았다(판단).")
    w("")
    # 6절
    w("## 6. 9-3 요약 — 받은 것 / 받지 못한 것 / 원문과 다른 것")
    w("")
    w("| 작업 | 받은 것 | 받지 못한 것 | 원문과 다른 것을 발견한 곳 | 주제1 표 조(판단) |")
    w("|---|---|---|---|---|")
    w("| 9-3-1 6개 부문 비계량 | Ⅳ.2 보험(%d~%d행)·Ⅳ.3 금리(%d~%d)·Ⅳ.4 투자(%d~%d)·Ⅳ.5 유동성(%d~%d)·Ⅳ.6 자본적정성(%d~%d)·Ⅳ.7 수익성(%d~%d) 전문 + 붙임5 가중치 | 없음(6개 부문 모두 매뉴얼 Ⅳ장에 있음) | hwp2md 글자 겹치기 누락 %d곳(4-1) · 매뉴얼 안 항목 이름·번호 표기 차이 %d곳 + 241행 「Ⅴ.」↔ 장 번호 「Ⅳ.」(4-2) | 21·22·24·28·30·34·53·55조(5절) |"
      % (*[x for k in range(2, 8) for x in ranges[k][:2]], len(tc), len(name_diffs) + len(numfmt)))
    w("| 9-3-2 1-나-1~4·1-다-5 | 5개 모두 9차 발췌에 있음(9차 91~94·114행), 전체 md 와 바이트 단위 같음 + IT 실태평가 대체 서술(%d~%d행) 보충 | 없음 | 없음(9차 발췌 = 전체 md) | 5·27·28·30조(5절) |" % (a3, b3))
    w("| 9-3-3 지주·대주주·계열 문장 | %d문장(낱말별 문장 수 — 한 문장에 두 낱말이 걸린 것은 양쪽에 셈: 금융지주회사·지주 2 · 대주주 %d · 계열회사·계열사 3) | 매뉴얼 본문(Ⅰ~Ⅳ)에 「금융지주회사」「지주」 문장은 **추출 범위에 없음**(전체 1~%d행 검색, 별첨에 옮겨 실은 보험업감독규정 제7-18조·제7-19조 2곳만) | 없음(9차 발췌 범위 문장은 9차 파일 줄과 같음) | — (대주주 거래·계열 문항에 대응하는 조는 지시서에 없음) |"
      % (len(found), cnt_seg["대주주"], len(L)))
    w("")
    os.makedirs(OUT, exist_ok=True)
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(o) + "\n")
    os.makedirs(WORK, exist_ok=True)
    with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
        cw = csv.DictWriter(f, fieldnames=["번호", "걸린낱말", "위치", "목차쪽", "전체md줄", "9차파일줄", "문장"])
        cw.writeheader()
        cw.writerows(rows_csv)
    verify(MD, L)
    print(MD, len(o), "줄 ·", CSV, len(rows_csv), "문장 · 글자겹침", len(tc), "· 이름차이", len(name_diffs), "· 조대응", len(map_rows))


def verify(md, L):
    """인용 블록의 줄이 전체 md 의 연속 줄과 같은지(표지 지운 뒤) 확인."""
    txt = open(md, encoding="utf-8").read().split("\n")
    full = "\n".join(L)
    blocks, cur = [], []
    for t in txt:
        if t.startswith(">"):
            cur.append(MARK.sub("", t[2:] if t.startswith("> ") else ""))
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    for b in blocks:
        s = "\n".join(b)
        assert s in full, ("인용이 전체 md 와 다름", s[:80])
    print("인용 블록", len(blocks), "개 모두 전체 md 와 일치")


if __name__ == "__main__":
    main()
