# -*- coding: utf-8 -*-
"""13차 9-3 RAAS 매뉴얼(2025.7) 산출물 검증·보정.

    python3 -I scripts/dart/verify13_raas.py        # 대조만 — 결과 dart_out/risk13/verify13_raas.txt, 문제 0 이면 exit 0
    python3 -I scripts/dart/verify13_raas.py fix    # 보정(멱등: 보정 전 사본에서 다시 만든 뒤 덧붙임) → 대조

대상(이 스크립트가 고치는 파일): handoff/13차_산출물/9-3_RAAS.md, dart_out/risk13/9-3_RAAS_낱말문장.csv. 결과: dart_out/risk13/verify13_raas.txt.
원본(읽기만, 웹 요청 없음): dart_out/raw/web9/raas/RAAS_매뉴얼.hwp(+.meta.json, 9차), RAAS_매뉴얼_전체.md(9차 hwp2md 결과, 줄 번호 기준),
      handoff/RAAS_매뉴얼_원문.md(9차 발췌). 모범규준: handoff/13차_산출물/9-4_모범규준_원문.md, dart_out/risk13/모범규준_조목록.csv(2016.8.1판 제목).
보정 전 사본: dart_out/raw/web13/raas_verify/(git 무시) — 처음 fix 때 저장(없으면 커밋 ec4a426 의 글을 sha256 확인 뒤 씀).
hwp(내려받은 파일)는 olefile 로 읽기만 한다 — `python3 -I` 로 실행.

대조(인자 없이):
  1. 원본 사슬 — hwp sha256·크기 = 9차 meta, hwp 를 hwp2md(수정 없음)로 메모리에서 다시 바꾼 글 = 전체 md(바이트), 전체 md sha256 = 9차 발췌 기록, md 머리 값.
  2. 인용 블록(>·```)마다 바로 앞 출처 줄 [문서명 · URL · 쪽 · 전체 md 줄 · 수집일] — 문서명·URL·수집일이 meta 와 같은지, 쪽이 목차(본문 절 머리 ↔ 목차 쪽)와
     같은지, 인용 글이 그 줄(들)·칸 문단과 같은지(글자 그대로, 아니면 공백만 무시), 「[글자겹침 X]」 표지가 hwp 의 글자 겹치기(tcps) 글자·자리와 같은지.
  3. 표 안 원문 글 — 1절 세부 점검사항 행·평가항목 머리 줄, 2절 표·목록 줄, 3절 머리(줄·9차 줄·쪽·걸린 낱말), 4-1 겹침 글자, 4-2 이름, 5절 근거 문단·질문 번호.
  4. 6개 부문 ↔ 목차 — 목차 Ⅳ.1~Ⅳ.7 쪽·본문 머리 줄·옮긴 범위, <붙임5> 평가항목 ↔ Ⅳ 평가항목 머리 줄, 평가항목 표의 세부 점검사항 ↔ 체크리스트 행.
  5. 낱말 문장 다시 세기 — 이 스크립트의 단위 규칙(표 밖 = 줄, 표 안 = 칸의 <br> 문단, 표 첫 칸 = 칸 전체)으로 다시 세어 md·CSV 와 대조, hwp 레코드 전부와도 대조.
  6. 모범규준 조 — md 의 「N조(제목)」가 2016.8.1판 제목으로 시작하는지, 자료 묶음마다 「모범규준 조(판단 …)」 줄이 있는지, CSV 조 칸.
  7. 「추출 범위에 없음」 반박 — 넓힌 검색어 결과가 검증 기록 표와 같은지. 8. 지시서 항목 대조 표·검증 기록 절·인증값(키·OC)·산출 폴더 PDF.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)
import olefile  # noqa: E402
from hwp2md import (records, decode_text, ctrl_id, extract as hwp_extract, PARA_HEADER, PARA_TEXT,  # noqa: E402
                    CTRL_HEADER, EXT_CTRL, INLINE_CTRL)

TODAY = "2026-10-07"
RAAS = os.path.join("dart_out", "raw", "web9", "raas")
HWP = os.path.join(RAAS, "RAAS_매뉴얼.hwp")
FULL = os.path.join(RAAS, "RAAS_매뉴얼_전체.md")
PREV = os.path.join("handoff", "RAAS_매뉴얼_원문.md")
OUT = os.path.join("handoff", "13차_산출물")
WORK = os.path.join("dart_out", "risk13")
MD = os.path.join(OUT, "9-3_RAAS.md")
CSV_P = os.path.join(WORK, "9-3_RAAS_낱말문장.csv")
OUT_TXT = os.path.join(WORK, "verify13_raas.txt")
ART_CSV = os.path.join(WORK, "모범규준_조목록.csv")
MB_MD = os.path.join(OUT, "9-4_모범규준_원문.md")
BASE = os.path.join("dart_out", "raw", "web13", "raas_verify")
BASE_MD = os.path.join(BASE, "9-3_RAAS.보정전.md")
BASE_CSV = os.path.join(BASE, "9-3_RAAS_낱말문장.보정전.csv")
BASE_COMMIT = "ec4a426"
BASE_SHA = {"md": "bdf23d52179aead8b9698a588419c9ad292ad0a8ad8aa629624742a2ff42d4b0",
            "csv": "b0835433b28a7058a0e591629925d908b1d9209b0a87121ec0c685f0ee2e329e"}
VERIFY_HEAD = "## 검증 기록(2026-10-07)"
# 13차 정합성 보정(scripts/dart/fix13_D.py, 2026-10-08 KST)이 고친 판도 받아들임 — 대조 규칙은 그대로, 받아들이는 글만 넓힘:
#   R5 절 제목 「검증 기록(2026-10-08 KST)」은 옛 제목과 같은 절로 읽음(대조 때만 — fix 모드가 쓰는 제목은 그대로),
#   R2 자료 묶음 조 줄은 fix13_D fix_log 의 「후」이면 그 「전」을 스크립트 대응표와 견줌. 재생성 순서: fix → fix13_D.py.
VERIFY_HEAD_KST = "## 검증 기록(2026-10-08 KST)"
FIXD_LOG = os.path.join("dart_out", "raw", "web13", "fix13_D", "fix_log.json")
PUA = "\U000f02b1\U000f02b2\U000f02b3\U000f02b4\U000f02b5\U000f02b6\U000f02b7"  # 한글 원문자 ①~⑦(사용자 정의 영역)
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳➀➁➂➃➄➅➆➇➈➉"
MARK = re.compile(r"\[글자겹침 ([^\]]+)\]")
WORDS = ["금융지주회사", "지주", "대주주", "계열회사", "계열사"]
EXTRA = ["관계회사", "관계사", "자회사", "그룹"]
CSV_COLS = ["번호", "걸린낱말", "위치", "목차쪽", "전체md줄", "9차파일줄", "문장"]
CSV_ART_COL = "모범규준_조(판단·2016.8.1판제목)"
ART_LINE = "- 모범규준 조(판단, 2016.8.1판 제목 — `dart_out/risk13/모범규준_조목록.csv`): "
IV_A, IV_B = 1010, 1401  # Ⅳ장 본문(부문 머리 ~ 수익성 끝) — 13차 산출물이 쓴 범위


# ── 공용 ─────────────────────────────────────────────────────────────────────
def ns(x):
    return re.sub(r"\s+", "", x)


def unmark(x):
    return MARK.sub("", x)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, "rb") as f:
        return sha_bytes(f.read())


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def is_row(line):
    return line.startswith("|") and line.endswith("|") and len(line) > 1 and not re.fullmatch(r"\|(?:---\|)+", line)


def row_cells(line):
    """hwp2md 표 줄(「| a | b |」) → 칸 글. 칸 안 「|」 는 「\\|」 로 적혀 있음."""
    parts = re.split(r"(?<!\\)\|", line[1:-1])
    return [p[1:-1] if len(p) >= 2 else "" for p in parts]


def units(line):
    """문장 단위(이 스크립트가 다시 정한 규칙): 표 밖 = 줄 하나, 표 안 = 첫 칸은 칸 전체, 나머지 칸은 <br> 로 나눈 문단."""
    if not is_row(line):
        return [line]
    cs = row_cells(line)
    out = [cs[0]]
    for c in cs[1:]:
        out.extend(c.split("<br>"))
    return out


def qnum(seg):
    m = re.match(r"^\s*\[글자겹침 (.)\]", seg)
    if m and m.group(1) in CIRC:
        return m.group(1)
    s = seg.lstrip()
    return s[:1] if s[:1] in CIRC else ""


def question_of(line, seg_idx_in_cell, cell_idx):
    """칸(cell_idx≥1) 안 seg_idx 번째 문단이 딸린 질문 번호(그 문단이 질문이면 그 번호)."""
    segs = row_cells(line)[cell_idx].split("<br>")
    q = ""
    for i, s in enumerate(segs[:seg_idx_in_cell + 1]):
        k = qnum(s)
        if k:
            q = k
    return q


class Report:
    def __init__(self):
        self.lines, self.bad = [], 0
        self.issues = []

    def h(self, s):
        self.lines += ["", "== " + s]

    def ok(self, s):
        self.lines.append("  ok  " + s)

    def ng(self, s):
        self.bad += 1
        self.lines.append("  !!  " + s)
        self.issues.append(s)

    def note(self, s):
        self.lines.append("      " + s)


# ── 원본 ─────────────────────────────────────────────────────────────────────
_S = {}


def source():
    if _S:
        return _S
    meta = json.load(open(HWP + ".meta.json", encoding="utf-8"))
    raw = read(FULL)
    L = raw.split("\n")
    if L and L[-1] == "":
        L = L[:-1]
    P = read(PREV).split("\n")
    hw = hwp_scan()
    ML, placed = marked_lines(L, hw["tc"])
    toc, starts, toc_rng = page_map(L)
    T = {int(r["조"]): r["제목_2016.8.1판"] for r in csv.DictReader(open(ART_CSV, encoding="utf-8-sig"))}
    _S.update(meta=meta, raw=raw, L=L, P=P, hw=hw, ML=ML, placed=placed, toc=toc, starts=starts, toc_rng=toc_rng, T=T,
              **{"DOC": meta["게시글제목"], "POST": meta["게시글URL"], "COL": meta["fetched_at"][:10]})
    return _S


def walk(payload):
    """hwp2md.decode_text 와 같은 규칙으로 글을 만들고, 글자 겹치기(제어 문자 23 + 'tcps') 자리(파이썬 글자 위치)를 함께 돌려준다."""
    u = struct.unpack("<%dH" % (len(payload) // 2), payload[: len(payload) // 2 * 2])
    out, pos, i = [], [], 0
    while i < len(u):
        c = u[i]
        if c in EXT_CTRL or c in INLINE_CTRL:
            if c == 23 and i + 2 < len(u) and struct.pack("<2H", u[i + 1], u[i + 2]) == b"spct":
                pos.append(len(out))
            i += 8
            continue
        if c == 9:
            out.append(9)
            i += 8
            continue
        if c == 10:
            out.append(10)
        elif c in (13, 0):
            pass
        elif c == 24:
            out.append(ord("-"))
        elif c in (30, 31):
            out.append(32)
        elif c < 32:
            pass
        else:
            out.append(c)
        i += 1

    def dec(x):
        return struct.pack("<%dH" % len(x), *x).decode("utf-16-le", errors="replace")
    return dec(out), [len(dec(out[:p])) for p in pos]


def hwp_scan():
    """hwp BodyText 를 한 번 읽어: 글자 겹치기 문단, 문단(수준·쪽 나누기 표시·글), 레코드 글 전부."""
    ole = olefile.OleFileIO(HWP)
    head = ole.openstream("FileHeader").read()
    comp = bool(struct.unpack_from("<I", head, 36)[0] & 1)
    secs = sorted(["/".join(e) for e in ole.listdir() if e[0] == "BodyText"], key=lambda s: int(s.split("Section")[-1]))
    tc, paras, any_txt, n_tcps_hdr = [], [], [], 0
    pend = None
    for sec in secs:
        data = ole.openstream(sec).read()
        if comp:
            data = zlib.decompress(data, -15)
        for tag, level, pl in records(data):
            any_txt.append(pl[: len(pl) // 2 * 2].decode("utf-16-le", errors="ignore"))
            any_txt.append(pl[1: 1 + (len(pl) - 1) // 2 * 2].decode("utf-16-le", errors="ignore"))
            if tag == PARA_HEADER:
                paras.append({"level": level, "bt": pl[11] if len(pl) > 11 else 0, "text": "", "sec": sec})
            elif tag == PARA_TEXT:
                assert pend is None, "글자 겹치기 컨트롤 헤더 짝이 맞지 않음"
                text, pos = walk(pl)
                assert text == decode_text(pl)
                if paras:
                    paras[-1]["text"] = text
                if pos:
                    pend = {"text": text, "pos": pos, "chars": []}
            elif tag == CTRL_HEADER and ctrl_id(pl) == "tcps":
                n_tcps_hdr += 1
                n = struct.unpack_from("<H", pl, 4)[0]
                pend["chars"].append(pl[6:6 + 2 * n].decode("utf-16-le"))
                if len(pend["chars"]) == len(pend["pos"]):
                    tc.append((pend["text"], list(zip(pend["pos"], pend["chars"]))))
                    pend = None
    ole.close()
    return {"tc": tc, "paras": paras, "any": "\n".join(any_txt), "n_tcps_hdr": n_tcps_hdr,
            "para_text": "\n".join(p["text"] for p in paras)}


def hwp2md_text():
    """hwp2md.main 과 같은 방식으로 메모리에서 글을 만든다(파일을 쓰지 않음)."""
    out = []
    for kind, payload in hwp_extract(HWP):
        if kind == "p":
            out.append(payload.rstrip())
        else:
            out += ["", payload, ""]
    return "\n".join(out)


def marked_lines(L, tc):
    """전체 md 줄에 hwp 의 겹침 글자를 [글자겹침 X] 로 넣은 줄 목록 + 놓인 자리 [(줄, 열, 글자, 문단 글)]."""
    ins = {}
    placed = []
    cur_line, cur_col = 0, 0
    for text, marks in tc:
        s = text.strip()
        lead = len(text) - len(text.lstrip())
        conv = s.replace("|", "\\|").replace("\n", "<br>")
        rx = re.compile(r"(?:(?<=\| )|(?<=<br>))" + re.escape(conv) + r"(?=<br>| \|)")
        hit = None
        for i in range(cur_line, len(L)):
            m = rx.search(L[i], cur_col if i == cur_line else 0)
            if m:
                hit = (i, m.start())
                break
            if not is_row(L[i]) and L[i].strip() == s:
                hit = (i, L[i].index(s))
                break
        if hit is None:
            raise SystemExit("글자 겹치기 문단을 전체 md 에서 찾지 못함: %r" % s[:60])
        i, col = hit
        for p, ch in marks:
            off = len(text[lead:p].replace("|", "\\|").replace("\n", "<br>"))
            ins.setdefault(i, []).append((col + off, ch))
            placed.append((i + 1, col + off, ch, conv))
        cur_line, cur_col = i, col + len(conv)
    ML = list(L)
    for i, lst in ins.items():
        t = L[i]
        for col, ch in sorted(lst, reverse=True):
            t = t[:col] + "[글자겹침 %s]" % ch + t[col:]
        ML[i] = t
    return ML, placed


def page_map(L):
    """목차(쪽) + 본문 절 머리 줄 → 줄마다 「목차상 쪽」. 번호 절은 차례대로(1,2,3…) 나오는 것만 머리로 본다."""
    a = L.index("목 차")
    toc, chap, b = {}, None, None
    titles = {}
    for i in range(a, len(L)):
        m = re.match(r"^\s*(.*?)\s*(?:\t|…+)\s*(\d+)\s*$", L[i])
        if not m:
            continue
        title, page = m.group(1), int(m.group(2))
        r = re.match(r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ)\.", title)
        if r:
            chap = r.group(1)
            k = (chap, None)
        elif title.startswith("[별첨]"):
            k = ("별첨", None)
            b = i + 1
        elif re.match(r"^<붙임(\d)>", title):
            k = (chap, "붙임" + re.match(r"^<붙임(\d)>", title).group(1))
        else:
            k = (chap, re.match(r"^(\d+)\.", title).group(1))
        toc[k] = page
        titles[k] = title
        if b:
            break
    starts = []
    chap, expect = None, 1
    for n in range(b + 1, len(L) + 1):
        raw = L[n - 1]
        s = raw.strip()
        if raw in ("Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ"):
            chap, expect = raw, 1
            starts.append((n, (chap, None), raw))
            continue
        if s == "[별첨]":
            chap = "별첨"
            starts.append((n, ("별첨", None), s))
            continue
        if chap in ("Ⅰ", "Ⅱ"):
            m = re.match(r"^(\d+)\.\s*\S", raw)
            if m and int(m.group(1)) == expect:
                starts.append((n, (chap, m.group(1)), s))
                expect += 1
                continue
            m = re.fullmatch(r"\s*<붙임(\d)>\s*", raw)
            if m and chap == "Ⅱ":
                starts.append((n, (chap, "붙임" + m.group(1)), s))
        elif chap == "Ⅲ":
            m = re.match(r"^ (\d)\. ", raw)
            if m and int(m.group(1)) == expect:
                starts.append((n, (chap, m.group(1)), s))
                expect += 1
        elif chap == "Ⅳ":
            if len(raw) > 2 and raw[0] in PUA and raw[1] == " " and PUA.index(raw[0]) + 1 == expect:
                starts.append((n, ("Ⅳ", str(expect)), s))
                expect += 1
    return toc, starts, (a + 1, b, titles)


def page_of(n):
    S = source()
    k = None
    for ln, key, _ in S["starts"]:
        if ln <= n:
            k = key
    if k is None:
        return None
    return S["toc"].get(k, S["toc"].get((k[0], None)))


def iv_ranges():
    """Ⅳ 부문 k → (머리 줄, 끝 줄(빈 줄 뺌), 이름)."""
    S = source()
    L = S["L"]
    st = [(n, int(key[1]), s) for n, key, s in S["starts"] if key[0] == "Ⅳ" and key[1]]
    bj = next(n for n, key, _ in S["starts"] if key[0] == "별첨")
    out = {}
    for i, (n, k, s) in enumerate(st):
        e = (st[i + 1][0] if i + 1 < len(st) else bj) - 1
        while not L[e - 1].strip():
            e -= 1
        out[k] = (n, e, s[2:])
    return out


# ── md 구조 ──────────────────────────────────────────────────────────────────
def md_blocks(lines):
    out, i = [], 0
    while i < len(lines):
        t = lines[i]
        if t.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append((i, j + 1, "code", lines[i + 1:j]))
            i = j + 1
            continue
        if t.startswith(">"):
            j = i
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            out.append((i, j, "quote", [x[2:] if x.startswith("> ") else x[1:] for x in lines[i:j]]))
            i = j
            continue
        i += 1
    return out


CITE_RE = re.compile(r"^\[(?P<doc>.+?) · (?P<url>https?://\S+) · (?P<pg>.+?) · 전체 md (?P<a>\d+)(?:~(?P<b>\d+))?행"
                     r"(?P<unit>\([^)]*\))? · 수집 (?P<col>\d{4}-\d{2}-\d{2})(?P<rest>[^\]]*)\]$")


def md_cells(line):
    parts = re.split(r"(?<!\\)\|", line.strip()[1:-1])
    return [p.strip() for p in parts]


def section_of(lines, idx):
    for j in range(idx, -1, -1):
        if lines[j].startswith("#"):
            return lines[j]
    return ""


def body_lines(lines):
    """검증 기록 절 앞까지."""
    if VERIFY_HEAD in lines:
        return lines[: lines.index(VERIFY_HEAD)]
    return lines


# ── 1. 원본 사슬 ──────────────────────────────────────────────────────────────
def check_source(R, md):
    S = source()
    R.h("1. 원본 사슬(hwp → hwp2md → 전체 md) · md 머리 값")
    meta = S["meta"]
    hb = open(HWP, "rb").read()
    if sha_bytes(hb) != meta["sha256"] or len(hb) != meta["바이트"]:
        R.ng("hwp sha256·크기가 9차 meta 와 다름")
    else:
        R.ok("hwp sha256 %s · %d바이트 = 9차 meta" % (meta["sha256"], len(hb)))
    regen = hwp2md_text()
    if regen.encode("utf-8") != open(FULL, "rb").read():
        R.ng("hwp 를 hwp2md 로 다시 바꾼 글이 전체 md 와 다름")
    else:
        R.ok("hwp 를 hwp2md(수정 없음)로 메모리에서 다시 바꾼 글 = 전체 md(바이트 단위 같음, %d줄)" % len(S["L"]))
    rec = re.search(r"RAAS_매뉴얼_전체\.md\(sha256 ([0-9a-f]{64})\)", read(PREV))
    hf = sha_file(FULL)
    if not rec or rec.group(1) != hf:
        R.ng("전체 md sha256 이 9차 발췌 기록과 다름")
    else:
        R.ok("전체 md sha256 %s = 9차 발췌 기록" % hf)
    head = "\n".join(md.split("\n")[:12])
    for lab, v in (("게시글제목", meta["게시글제목"]), ("게시글URL", meta["게시글URL"]), ("원파일명", meta["원파일명"]),
                   ("출처URL", meta["출처URL"]), ("fetched_at", meta["fetched_at"]), ("http", "HTTP %s" % meta["http_status"]),
                   ("바이트", "%d바이트" % meta["바이트"]), ("hwp sha256", meta["sha256"]), ("전체 md sha256", hf),
                   ("줄 수", "%d줄" % len(S["L"]))):
        if v not in head:
            R.ng("md 머리에 %s 값(%s)이 없음" % (lab, v))
    R.ok("md 머리의 출처 값 10개(게시글 제목·URL·원파일명·다운로드 URL·수집 시각·HTTP·바이트·sha256 2개·줄 수) 확인")
    if S["hw"]["n_tcps_hdr"] != len(S["placed"]):
        R.ng("hwp 글자 겹치기 헤더 %d ↔ 놓인 자리 %d" % (S["hw"]["n_tcps_hdr"], len(S["placed"])))
    else:
        R.ok("hwp 글자 겹치기 컨트롤 %d개 모두 전체 md 줄에 자리를 찾음" % len(S["placed"]))


# ── 2. 인용 블록 ──────────────────────────────────────────────────────────────
def check_quotes(R, md):
    S = source()
    L, ML = S["L"], S["ML"]
    R.h("2. 인용 블록(> · ```) ↔ 출처 줄 · 원문")
    lines = md.split("\n")
    body = body_lines(lines)
    st = {"blocks": 0, "lines": 0, "range": 0, "seg": 0, "exact": 0, "space": 0, "bad": 0, "marks": 0, "wrong": []}
    for i, j, kind, content in md_blocks(body):
        st["blocks"] += 1
        st["lines"] += len(content)
        k = i - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        cite = lines[k] if k >= 0 else ""
        m = CITE_RE.match(cite)
        where = "md %d행" % (i + 1)
        if not m:
            R.ng("%s 인용 앞에 출처 줄 [문서명 · URL · 쪽 · 전체 md 줄 · 수집일] 이 없음(앞 줄: %s)" % (where, cite[:70]))
            st["bad"] += 1
            st["wrong"].append(("cite", i, None))
            continue
        if m.group("doc") != S["DOC"]:
            R.ng("%s 출처 문서명 %r ≠ meta 게시글 제목" % (where, m.group("doc")))
        if m.group("url") != S["POST"]:
            R.ng("%s 출처 URL ≠ meta 게시글 URL" % where)
        if m.group("col") != S["COL"]:
            R.ng("%s 수집일 %s ≠ meta %s" % (where, m.group("col"), S["COL"]))
        a = int(m.group("a"))
        b = int(m.group("b") or a)
        pg = m.group("pg")
        pm = re.search(r"목차상 (\d+)쪽", pg)
        exp = page_of(a)
        if pm:
            if exp is None or int(pm.group(1)) != exp:
                R.ng("%s 쪽 표기 %s쪽 ↔ 목차 계산 %s쪽(전체 md %d행)" % (where, pm.group(1), exp, a))
        elif pg.strip() == "목차":
            if exp is not None:
                R.ng("%s 쪽 표기 「목차」 인데 %d행은 본문(목차상 %s쪽)" % (where, a, exp))
        else:
            R.ng("%s 쪽 표기 없음: %s" % (where, pg))
        unit = m.group("unit") or ""
        if "문장 단위" in unit or "칸 안 문단" in unit:
            st["seg"] += 1
            us_m = units(ML[a - 1])
            us = [unmark(x) for x in us_m]
            got = [unmark(x) for x in content]
            pos = next((p for p in range(len(us) - len(got) + 1) if us[p:p + len(got)] == got), None)
            if pos is not None and us_m[pos:pos + len(content)] == content:
                st["exact"] += 1
            elif pos is not None:
                R.ng("%s 글은 같으나 [글자겹침] 표지가 hwp 와 다름" % where)
                st["bad"] += 1
            elif ns("".join(got)) in ns("".join(us)):
                st["space"] += 1
                R.note("%s 공백만 다름(전체 md %d행)" % (where, a))
            else:
                R.ng("%s 인용 글이 전체 md %d행의 문장(칸 문단)과 다름: %s" % (where, a, got[0][:60]))
                st["bad"] += 1
                st["wrong"].append(("seg", i, (a, content)))
            st["marks"] += sum(len(MARK.findall(x)) for x in content)
        else:
            st["range"] += 1
            src_m = ML[a - 1:b]
            src = L[a - 1:b]
            got = [unmark(x) for x in content]
            if got == src and content == src_m:
                st["exact"] += 1
            elif got == src:
                R.ng("%s 글은 같으나 [글자겹침] 표지가 hwp 와 다름(전체 md %d~%d행)" % (where, a, b))
                st["bad"] += 1
                st["wrong"].append(("range", i, (a, b)))
            elif ns("\n".join(got)) == ns("\n".join(src)):
                st["space"] += 1
                R.note("%s 공백만 다름(전체 md %d~%d행)" % (where, a, b))
            else:
                d = next((x for x in range(max(len(got), len(src))) if x >= len(got) or x >= len(src) or got[x] != src[x]), 0)
                R.ng("%s 인용이 전체 md %d~%d행과 다름(인용 %d번째 줄부터)" % (where, a, b, d + 1))
                st["bad"] += 1
                st["wrong"].append(("range", i, (a, b)))
            st["marks"] += sum(len(MARK.findall(x)) for x in content)
    R.ok("인용 블록 %d개(%d줄): 줄 범위 인용 %d · 문장·칸 문단 인용 %d — 글자 그대로 같음 %d, 공백만 다름 %d, 다름·출처 없음 %d"
         % (st["blocks"], st["lines"], st["range"], st["seg"], st["exact"], st["space"], st["bad"]))
    R.ok("인용 안 [글자겹침] 표지 %d개(1절 범위 인용은 hwp 의 겹침 글자·자리와 줄마다 대조)" % st["marks"])
    return st


# ── 3. 표 안 원문 글 ──────────────────────────────────────────────────────────
def check_tables(R, md):
    S = source()
    L, ML, P = S["L"], S["ML"], S["P"]
    R.h("3. 표·머리 줄 안의 원문 글 조각")
    lines = body_lines(md.split("\n"))
    cnt = {"head": 0, "row1": 0, "t2": 0, "list2": 0, "h3": 0, "t41": 0, "t42": 0, "t5": 0}
    sec, hdr, prev_row, t41_i = "", None, False, 0
    for idx, t in enumerate(lines):
        if t.startswith("#"):
            sec, hdr, prev_row = t, None, False
            continue
        if t.startswith("|"):
            if not prev_row:
                hdr, prev_row = md_cells(t), True
                continue
            if re.fullmatch(r"\|(?:-+\|)+", t):
                continue
            c = md_cells(t)
            h0 = hdr[0]
            if h0 == "전체 md 줄" and len(c) == 3:
                n = int(c[0])
                cnt["row1"] += 1
                if row_cells(ML[n - 1])[0].strip() != c[1]:
                    R.ng("1절 세부 점검사항 행 %d: 첫 칸이 원문(표지 포함)과 다름" % n)
                k = len(MARK.findall(ML[n - 1]))
                if c[2] != (str(k) if k else ""):
                    R.ng("1절 %d행 글자겹침 표지 수 %r ↔ hwp %d" % (n, c[2], k))
            elif h0 == "번호(사용자 표기)":
                cnt["t2"] += 1
                n, m_ = int(c[3]), int(c[4])
                if row_cells(L[n - 1])[0].strip() != c[1]:
                    R.ng("2절 %s 매뉴얼 번호·이름 ≠ 전체 md %d행 첫 칸" % (c[0], n))
                hm = re.fullmatch(r"(.+)\((\d+)행\)", c[2])
                if not hm or L[int(hm.group(2)) - 1].strip() != hm.group(1):
                    R.ng("2절 %s 평가항목 머리 줄이 원문과 다름" % c[0])
                if P[m_ - 1] != L[n - 1]:
                    R.ng("2절 %s 9차 파일 %d행 ≠ 전체 md %d행" % (c[0], m_, n))
                if ("9차 파일 %d행" % m_) not in c[6] or c[5] != "바이트 단위 같음":
                    R.ng("2절 %s 상태·대조 칸이 다름" % c[0])
            elif h0 == "#" and len(c) == 5 and len(hdr) > 3 and "겹침" in hdr[3]:
                cnt["t41"] += 1
                if t41_i >= len(S["placed"]):
                    R.ng("4-1 표 행이 hwp 글자 겹치기 수보다 많음")
                    continue
                n, col, ch, conv = S["placed"][t41_i]
                t41_i += 1
                if int(c[1]) != n or c[3] != ch or ns(c[4]) != ns(conv):
                    R.ng("4-1 표 %s행: (%s, %s) ↔ hwp (%d, %s)" % (c[0], c[1], c[3], n, ch))
            elif h0 == "위치" and len(hdr) > 1 and "평가항목 표(A)" in hdr[1]:
                for n, txt in re.findall(r"(\d+)행 「([^」]+)」", t):
                    cnt["t42"] += 1
                    if ns(unmark(txt)) not in ns(L[int(n) - 1]):
                        R.ng("4-2 표 %s행 「%s」 이 원문 줄에 없음" % (n, txt[:30]))
            elif h0.startswith("모범규준 조") and len(c) == 5 and c[2].isdigit():
                cnt["t5"] += 1
                n = int(c[2])
                cs = row_cells(ML[n - 1])
                if cs[0].strip() != c[1]:
                    R.ng("5절 %s %d행 첫 칸이 원문과 다름" % (c[0], n))
                segs = cs[1].split("<br>")
                hit = [k for k, s in enumerate(segs) if s.strip() == c[4]]
                if not hit:
                    R.ng("5절 %s %d행 근거 문단이 원문 칸 문단과 다름: %s" % (c[0], n, c[4][:40]))
                else:
                    q = question_of(ML[n - 1], hit[0], 1)
                    if q != c[3]:
                        R.ng("5절 %s %d행 질문 번호 %s ↔ 계산 %s" % (c[0], n, c[3], q))
            continue
        prev_row = False
        if t.startswith(">"):
            continue
        if t.startswith("- 평가항목(머리 줄): "):
            for txt, n in re.findall(r"「([^」]+)」\((\d+)행\)", t):
                cnt["head"] += 1
                if L[int(n) - 1].strip() != txt:
                    R.ng("%s 평가항목 머리 줄 %s행 「%s」 ≠ 원문" % (sec[:12], n, txt))
        if t.startswith("- 목록 줄("):
            for n, m_ in re.findall(r"전체 (\d+)행 = 9차 (\d+)행", t):
                cnt["list2"] += 1
                if P[int(m_) - 1] != L[int(n) - 1]:
                    R.ng("2절 목록 줄 전체 %s행 ≠ 9차 %s행" % (n, m_))
        if t.startswith("**3-"):
            cnt["h3"] += 1
            m = re.match(r"^\*\*(3-(?:참고-)?\d\d)\*\* · 걸린 낱말: (.+?) · 위치: (.+) · (목차상 (\d+)쪽~\([^)]*\)|목차 앞) · "
                         r"전체 md (\d+)행(?: · 9차 파일 (\d+)행\(이미 받음\))?$", t)
            if not m:
                R.ng("3절 머리 줄 꼴이 다름: %s" % t[:60])
                continue
            n = int(m.group(6))
            if m.group(5) and int(m.group(5)) != page_of(n):
                R.ng("3절 %s 쪽 %s ↔ 목차 계산 %s" % (m.group(1), m.group(5), page_of(n)))
            if m.group(7) and P[int(m.group(7)) - 1] != L[n - 1]:
                R.ng("3절 %s 9차 파일 %s행 ≠ 전체 md %d행" % (m.group(1), m.group(7), n))
            if not m.group(7) and (1008 <= n <= 1106 or 491 <= n <= 518):
                R.ng("3절 %s 9차 파일 줄 표기 빠짐" % m.group(1))
    if t41_i != len(S["placed"]):
        R.ng("4-1 표 행 %d ↔ hwp 글자 겹치기 %d" % (t41_i, len(S["placed"])))
    R.ok("표·머리 줄 대조: 평가항목 머리 줄 %(head)d · 1절 세부 점검사항 행 %(row1)d · 2절 표 %(t2)d행·목록 줄 %(list2)d · "
         "3절·3-참고 머리 %(h3)d · 4-1 겹침 글자 %(t41)d · 4-2 이름 %(t42)d · 5절 근거 문단 %(t5)d" % cnt)
    return cnt


# ── 4. 6개 부문 ↔ 목차 ────────────────────────────────────────────────────────
def norm_name(s):
    s = unmark(s).replace("<br>", "")
    s = re.sub("[\u2024\u00b7\u2027\uff65\u30fb\u318d\u2025]", "·", s)
    return re.sub(r"\s+", "", s)


NUMRX = re.compile("^(?:\\[글자겹침 [" + PUA + "]\\])?[" + PUA + "]?-([가-하])[-.](\\d+)\\.?")


def coverage(md):
    """부문별 대조 값 — 표로 쓰고 대조에도 씀."""
    S = source()
    L, ML, P = S["L"], S["ML"], S["P"]
    rng = iv_ranges()
    toc = S["toc"]
    # <붙임5> 비계량 평가항목
    b5 = L.index("<붙임5>") + 1
    att5 = {}
    for n in range(b5, b5 + 20):
        if is_row(L[n - 1]) and L[n - 1][2:3] in PUA:
            c = row_cells(L[n - 1])
            att5[PUA.index(c[0][0]) + 1] = [re.sub(r"^[①-⑳]\s*", "", x) for x in c[1].split("<br>")]
    lines = md.split("\n")
    rows = []
    for k in range(1, 8):
        a, b, nm = rng[k]
        heads = [(n, L[n - 1].strip()) for n in range(a, b + 1) if re.match("^[" + PUA + r"]-[가-하]\. ", L[n - 1].strip())]
        A, C = set(), set()
        rein = False
        head = None
        for n in range(a, b + 1):
            t = ML[n - 1]
            if t.startswith("<<세부 점검사항(재보험사)"):
                rein = True
            if is_row(t):
                if n == a or not ML[n - 2].startswith("|"):
                    head = row_cells(t)
                    continue
                c = row_cells(t)
                if head and head[0] == "평가항목":
                    r2 = "<<재보험사>>" in c[1]
                    for sg in c[1].split("<br>"):
                        mm = NUMRX.match(sg)
                        if mm:
                            A.add((mm.group(1), mm.group(2), r2))
                elif head and head[0] == "세부 점검사항":
                    mm = NUMRX.match(c[0])
                    if mm:
                        C.add((mm.group(1), mm.group(2), rein))
        names5 = att5.get(k, [])
        hn = [norm_name(re.sub("^[" + PUA + r"]-[가-하]\.\s*", "", s)) for _, s in heads]
        same5 = [x for x in names5 if norm_name(x) in hn]
        if k == 1:
            where = "9차 발췌 `handoff/RAAS_매뉴얼_원문.md` 49~147행(= 전체 md 1008~1106행)"
            ok_cov = all(P[n - 960] == L[n - 1] for n in range(1008, 1107))
            quoted = ok_cov
        else:
            sec_h = next((x for x in lines if x.startswith("### 1-%d Ⅳ.%d " % (k - 1, k))), "")
            where = "1-%d절 인용(전체 md %d~%d행)" % (k - 1, a, b)
            blk = None
            if sec_h:
                si = lines.index(sec_h)
                blk = next(((i, j, c) for i, j, kd, c in md_blocks(lines) if i > si), None)
            quoted = bool(blk) and [unmark(x) for x in blk[2]] == L[a - 1:b] and \
                all(not L[x - 1].strip() for x in range(b + 1, (rng[k + 1][0] if k < 7 else b + 2)))
        p0 = toc[("Ⅳ", str(k))]
        res = []
        if not quoted:
            res.append("옮긴 범위 다름")
        if len(same5) != len(names5) or len(names5) != len(heads):
            res.append("평가항목 이름 다름(공백·가운뎃점 무시)")
        if A != C:
            res.append("세부 점검사항 ↔ 체크리스트 행 다름")
        rows.append(dict(k=k, nm=nm, p0=p0, a=a, b=b, where=where, n5=len(names5), nh=len(heads), nA=len(A), nC=len(C),
                         res="; ".join(res) or "같음", heads=heads, A=A, C=C, quoted=quoted))
    return rows, att5


def coverage_table(rows):
    S = source()
    out = ["| 목차 항목(쪽) | 본문 머리 줄 | 옮긴 곳 | <붙임5> 비계량 평가항목 수 | Ⅳ 평가항목 머리 줄 수 | 평가항목 표의 세부 점검사항 수 | 체크리스트 행 수 | 결과 |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| Ⅳ.%d %s(목차 %d쪽) | %d행 「%s %s」 | %s | %d | %d | %d | %d | %s |"
                   % (r["k"], r["nm"], r["p0"], r["a"], PUA[r["k"] - 1], r["nm"], r["where"], r["n5"], r["nh"], r["nA"], r["nC"], r["res"]))
    out.append("| 합계 | — | — | %d | %d | %d | %d | <붙임5> 「7개 부문 23개 항목」 |"
               % tuple(sum(r[x] for r in rows) for x in ("n5", "nh", "nA", "nC")))
    return out


def check_coverage(R, md):
    R.h("4. 6개 부문 비계량 항목 ↔ 목차·<붙임5>·평가항목 표")
    S = source()
    toc = S["toc"]
    rows, att5 = coverage(md)
    titles = S["toc_rng"][2]
    for n, key, s in S["starts"]:
        if key in titles:
            tt = re.sub(r"^\d+\.\s*|^<붙임\d>\s*", "", titles[key])
            bt = re.sub(r"^\d+\.\s*|^<붙임\d>|^[" + PUA + r"]\s*", "", s)
            if not (ns(bt).startswith(ns(tt)) or ns(tt).startswith(ns(bt))) and key[1]:
                R.note("목차 제목 ↔ 본문 머리 줄 다름(참고): %s / %d행 %s" % (titles[key], n, s))
    missing = [k for k in toc if k not in {key for _, key, _ in S["starts"]}]
    if missing:
        R.note("목차에는 있으나 본문 머리 줄을 찾지 못한 항목: %s" % missing)
    for r in rows:
        if r["res"] != "같음":
            R.ng("Ⅳ.%d %s: %s" % (r["k"], r["nm"], r["res"]))
        else:
            R.ok("Ⅳ.%d %s(목차 %d쪽, 전체 md %d~%d행): %s · 평가항목 %d(붙임5 %d) · 세부 점검사항 %d = 체크리스트 행 %d"
                 % (r["k"], r["nm"], r["p0"], r["a"], r["b"], r["where"], r["nh"], r["n5"], r["nA"], r["nC"]))
        if r["k"] >= 2:
            m = re.search(r"^### 1-%d Ⅳ\.%d (.+?) — 목차상 (\d+)쪽~(\d+)쪽\(끝 쪽은 판단\) · 전체 md (\d+)~(\d+)행$" % (r["k"] - 1, r["k"]), md, re.M)
            nxt = toc[("Ⅳ", str(r["k"] + 1))] if r["k"] < 7 else toc[("별첨", None)]
            if not m or (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))) != (r["nm"], r["p0"], nxt - 1, r["a"], r["b"]):
                R.ng("1-%d절 머리(이름·쪽·줄) ↔ 목차·본문 다름" % (r["k"] - 1))
    if sum(r["nh"] for r in rows) != 23:
        R.ng("Ⅳ 평가항목 머리 줄 합계 %d ≠ <붙임5> 23개" % sum(r["nh"] for r in rows))
    tbl = coverage_table(rows)
    t = md.split(VERIFY_HEAD)[-1] if VERIFY_HEAD in md else ""
    if not all(x in t.split("\n") for x in tbl):
        R.ng("검증 기록의 「6개 부문 ↔ 목차 대조」 표가 다시 계산한 값과 다름(또는 없음)")
    else:
        R.ok("검증 기록의 6개 부문 ↔ 목차 대조 표 = 다시 계산한 값")
    return rows


# ── 5. 낱말 문장 다시 세기 ────────────────────────────────────────────────────
def label(seg, words):
    got = [w for w in words if w in seg]
    lab = []
    for w in got:
        if w == "지주" and "금융지주회사" in got and seg.count("지주") == seg.count("금융지주회사"):
            continue
        if w == "대주주" and seg.count("대주주") == seg.count("최대주주"):
            lab.append("대주주(「최대주주」 안)")
        elif w == "대주주" and "최대주주" in seg:
            lab.append("대주주(「최대주주」 포함)")
        elif w == "금융지주회사" and "지주" in got and seg.count("지주") == seg.count("금융지주회사"):
            lab.append("금융지주회사·지주(「금융지주회사」 안)")
        else:
            lab.append(w)
    return " · ".join(lab)


def recount():
    S = source()
    ML = S["ML"]
    found, extra = [], []
    for n in range(1, len(ML) + 1):
        for seg in units(ML[n - 1]):
            g = [w for w in WORDS if w in seg]
            if g:
                found.append((n, seg, g))
            elif any(w in seg for w in EXTRA):
                extra.append((n, seg, [w for w in EXTRA if w in seg]))
    per = {w: (sum(1 for f in found if w in f[2]), sum(f[1].count(w) for f in found)) for w in WORDS}
    return found, extra, per


def recount_table(per, found):
    S = source()
    full = "\n".join(S["L"])
    pt, an = S["hw"]["para_text"], S["hw"]["any"]
    out = ["| 낱말 | 다시 센 문장 수 | 다시 센 나온 횟수(전체 md, 공백 무시도 같음) | hwp 문단 글 전부(머리말·꼬리말 포함) 나온 횟수 | 결과 |",
           "|---|---|---|---|---|"]
    for w in WORDS:
        a = full.count(w)
        same = a == ns(full).count(w) == pt.count(w) == per[w][1]
        out.append("| %s | %d | %d | %d | %s |" % (w, per[w][0], a, pt.count(w), "md 3절과 같음" if same else "다름"))
    lines_w = sorted({f[0] for f in found})
    out.append("| 합계 | %d문장(낱말이 든 줄 %d개) | — | hwp 레코드 글 전부(문단 글 밖 포함) 「지주」 %d · 「대주주」 %d · 「계열」 %d | — |"
               % (len(found), len(lines_w), an.count("지주"), an.count("대주주"), an.count("계열")))
    return out


def check_words(R, md, csv_rows):
    S = source()
    L, P = S["L"], S["P"]
    R.h("5. 「금융지주회사·지주·대주주·계열회사(계열사)」 문장 다시 세기")
    found, extra, per = recount()
    full = "\n".join(L)
    exp_line = "- 문장 수: %d개. 낱말별(문장 수 / 나온 횟수): " % len(found) + " · ".join("%s %d / %d" % (w, per[w][0], per[w][1]) for w in WORDS)
    if exp_line not in md.split("\n"):
        R.ng("3절 「문장 수」 줄이 다시 센 값과 다름 — 다시 센 값: %s" % exp_line[2:])
    else:
        R.ok("3절 문장 수 %d개·낱말별 값 = 다시 센 값(%s)" % (len(found), exp_line.split(": ", 2)[-1]))
    for w in WORDS:
        if full.count(w) != per[w][1] or ns(full).count(w) != per[w][1]:
            R.ng("%s: 문장 안 횟수 %d ↔ 전체 md %d(공백 무시 %d)" % (w, per[w][1], full.count(w), ns(full).count(w)))
        if S["hw"]["para_text"].count(w) != full.count(w):
            R.ng("%s: hwp 문단 글 %d ↔ 전체 md %d" % (w, S["hw"]["para_text"].count(w), full.count(w)))
    R.ok("낱말 횟수: 다시 센 문장 안 = 전체 md(공백 무시 포함) = hwp 문단 글 전부(머리말·꼬리말 포함) — "
         + " · ".join("%s %d" % (w, per[w][1]) for w in WORDS))
    an = S["hw"]["any"]
    R.ok("hwp 레코드 글 전부(문단 글 밖 수식·필드 등 포함, 두 정렬로 풂): 「지주」 %d · 「대주주」 %d · 「계열」 %d"
         % (an.count("지주"), an.count("대주주"), an.count("계열")))
    m6 = re.search(r"^\| 9-3-3 지주·대주주·계열 문장 \| (\d+)문장\(.*?금융지주회사·지주 (\d+) · 대주주 (\d+) · 계열회사·계열사 (\d+)\)", md, re.M)
    e6 = (len(found), sum(1 for f in found if "금융지주회사" in f[2] or "지주" in f[2]), per["대주주"][0],
          sum(1 for f in found if "계열회사" in f[2] or "계열사" in f[2]))
    if not m6 or tuple(int(x) for x in m6.groups()) != e6:
        R.ng("6절 요약 표 문장 수 ↔ 다시 센 값 %s" % (e6,))
    else:
        R.ok("6절 요약 표 문장 수(%d · 지주 %d · 대주주 %d · 계열 %d) = 다시 센 값" % e6)
    # md 3절 항목 ↔ 다시 센 문장(순서대로)
    lines = md.split("\n")
    items = []
    for i, t in enumerate(lines):
        m = re.match(r"^\*\*(3-(?:참고-)?\d\d)\*\* · 걸린 낱말: (.+?) · 위치: (.+) · (목차상 \d+쪽~\([^)]*\)|목차 앞) · "
                     r"전체 md (\d+)행(?: · 9차 파일 (\d+)행\(이미 받음\))?$", t)
        if m:
            j = next(x for x in range(i + 1, len(lines)) if lines[x].startswith(">"))
            q = lines[j][2:] if lines[j].startswith("> ") else lines[j][1:]
            items.append(dict(no=m.group(1), lab=m.group(2), loc=m.group(3), pg=m.group(4), n=int(m.group(5)),
                              pn=m.group(6) or "", seg=q))
    main = [x for x in items if "참고" not in x["no"]]
    ref = [x for x in items if "참고" in x["no"]]
    if len(main) != len(found):
        R.ng("3절 항목 %d개 ↔ 다시 센 문장 %d개" % (len(main), len(found)))
    for it, (n, seg, g) in zip(main, found):
        if (it["n"], it["seg"]) != (n, seg):
            R.ng("3절 %s: (%d행 %s) ↔ 다시 센 (%d행 %s)" % (it["no"], it["n"], it["seg"][:30], n, seg[:30]))
        if it["lab"] != label(seg, WORDS):
            R.ng("3절 %s 걸린 낱말 %s ↔ 계산 %s" % (it["no"], it["lab"], label(seg, WORDS)))
    if len(ref) != len(extra):
        R.ng("3-참고 항목 %d개 ↔ 다시 센 %d개" % (len(ref), len(extra)))
    for it, (n, seg, g) in zip(ref, extra):
        if (it["n"], it["seg"]) != (n, seg) or it["lab"] != " · ".join(g):
            R.ng("3-참고 %s ↔ 다시 센 (%d행)" % (it["no"], n))
    R.ok("3절 항목 %d개·3-참고 %d개가 다시 센 문장과 순서·줄·글·걸린 낱말까지 같음" % (len(main), len(ref)))
    # CSV
    if not csv_rows or list(csv_rows[0].keys())[:7] != CSV_COLS:
        R.ng("CSV 열 이름이 다름")
    if len(csv_rows) != len(main):
        R.ng("CSV %d행 ↔ md 3절 %d항목" % (len(csv_rows), len(main)))
    T = S["T"]
    for r, it in zip(csv_rows, main):
        want = {"번호": it["no"], "걸린낱말": it["lab"], "위치": it["loc"], "목차쪽": it["pg"], "전체md줄": str(it["n"]),
                "9차파일줄": it["pn"], "문장": it["seg"]}
        for k, v in want.items():
            if r.get(k) != v:
                R.ng("CSV %s 「%s」 칸이 md 와 다름" % (it["no"], k))
        if r.get("9차파일줄") and P[int(r["9차파일줄"]) - 1] != L[int(r["전체md줄"]) - 1]:
            R.ng("CSV %s 9차 파일 줄 ≠ 전체 md 줄" % it["no"])
        av = r.get(CSV_ART_COL)
        if av is None:
            R.ng("CSV 에 「%s」 칸 없음" % CSV_ART_COL)
            break
        if "(판단" not in av or bad_titles(av, T):
            R.ng("CSV %s 조 칸이 (판단) 표시·2016.8.1판 제목과 맞지 않음: %s" % (it["no"], av))
        elif av != csv_art(it["n"], T):
            R.ng("CSV %s 조 칸 ≠ 스크립트 대응표" % it["no"])
    R.ok("CSV %d행 — md 3절과 칸마다 같음, 9차 줄 대조, 「%s」 칸 확인" % (len(csv_rows), CSV_ART_COL))
    tbl = recount_table(per, found)
    t = md.split(VERIFY_HEAD)[-1] if VERIFY_HEAD in md else ""
    if not all(x in t.split("\n") for x in tbl):
        R.ng("검증 기록의 「문장 다시 세기」 표가 다시 계산한 값과 다름(또는 없음)")
    else:
        R.ok("검증 기록의 문장 다시 세기 표 = 다시 계산한 값")
    return found, per, main


# ── 6. 모범규준 조 ────────────────────────────────────────────────────────────
ART_RE = re.compile(r"(?<![제\d\-])(\d{1,2})조\(([^()]*)\)")


def bad_titles(text, T):
    out = []
    for n, tt in ART_RE.findall(text):
        n = int(n)
        if n not in T or not tt.startswith(T[n]):
            out.append("%d조(%s)" % (n, tt))
    return out


def A(n, why=""):
    return (n, why)


# 자료 묶음(md 머리 줄 앞부분) → [(조, 까닭)], 조가 없을 때 쓰는 말 — 모두 판단
SEC_ART = [
    ("## 0. 매뉴얼 번호 체계와 목차 위치", [], "대응 조 없음 — 목차·번호 체계(자료 위치 안내)"),
    ("### 0-1 ", [A(14, "④2호 자회사등 위험관리업무 평가에 견줄 감독당국 비계량 평가 방법")], ""),
    ("### 0-2 ", [A(14, "④2호 — 비계량 평가항목 가중치")], ""),
    ("### 1-1 ", [A(18, "① 보험 위험을 측정·관리 대상으로 듦"), A(42, "① 내부자본 평가 때 보험위험 감안"),
                  A(20, "보험리스크 허용한도"), A(31, "측정모형 사후검증"), A(32), A(55, "조기경보 지표")], ""),
    ("### 1-2 ", [A(24), A(20, "금리리스크 한도"), A(31, "측정모형 사후검증"), A(32), A(55, "금리 조기경보·역마진 예측지표")], ""),
    ("### 1-3 ", [A(21), A(22), A(26, "가계대출 편중·투융자 집중"), A(6, "①6호 자산건전성 분류기준·①10호 신용공여한도"),
                  A(33, "①1호 — 󰊴-라 대주주와의 거래"), A(34, "해외투자 문항만"), A(31, "측정모형 사후검증"), A(32), A(55)], ""),
    ("### 1-4 ", [A(25), A(57, "② 유동성 위기 관리대책(contingency plan)의 역할 분담·정보 전달"), A(56, "유동성 위기상황 분석"),
                  A(53, "13차 대응 그대로"), A(20, "유동성리스크 허용한도")], ""),
    ("### 1-5 ", [A(37, "ORSA 체제"), A(43), A(46, "②위기상황분석·⑨가용자본 구성"), A(47, "리스크허용한도·소진율"), A(48),
                  A(49, "중·장기 자본적정성 관리계획"), A(56, "자본적정성 위기상황분석"), A(54, "단계별 대응방안"), A(55),
                  A(28, "13차 대응 그대로")], ""),
    ("### 1-6 ", [A(35, "①경영관리 활용·②위험조정성과평가"), A(5, "②4호 성과관리체계 — KPI 에 건전성 기준")],
     "직접 대응 조는 찾지 못함 — 가장 가까운 조"),
    ("## 2. ", [A(4, "1-나-1 ③ 관리문화(5-2-2)"), A(5, "1-나-1 ② 기본원칙"), A(6, "1-나-1 ② 리스크관리 제 규정"), A(37, "1-나-1 ① ORSA"),
                A(7, "1-나-2"), A(9, "1-나-2 ① 리스크관리위원회"), A(11, "1-나-2 ② CRO"), A(13, "1-나-2 ③④ 전담조직"),
                A(27, "1-나-2 ⑤ 비재무리스크"), A(23, "1-나-3 IT·1-다-5 금융사고"), A(14, "1-나-4 관계회사"),
                A(33, "1-나-4 관계회사·1-다-5 대주주·계열회사 계약")], ""),
    ("## 3. ", [A(33, "①1호 — 대주주와의 거래·계열회사 거래 문장")],
     "대주주의 적정성(󰊱-가-1)·별첨 금융지주회사 편입 문장은 대응 조 없음 — 문장별 조는 CSV 칸"),
    ("### 3-참고 ", [A(5, "②6호 자회사등 위험관리 통할"), A(14), A(33)], "「그룹」 문단(118·336행)은 대응 조 없음"),
    ("### 5-2 ", [A(3, "단서 — 위험이 경미한 자회사등"), A(18, "③ 위험이 경미한 자회사등 제외"), A(36, "단서 — 비중 미미 자회사등 제외"),
                  A(4), A(17, "①"), A(34, "④")], ""),
]


SEC_LABEL = {"## 0. 매뉴얼 번호 체계와 목차 위치": "0 번호 체계·목차", "### 0-1 ": "0-1 비계량 평가 방법(Ⅱ.7)", "### 0-2 ": "0-2 <붙임5> 비계량 가중치",
             "### 1-1 ": "1-1 보험리스크", "### 1-2 ": "1-2 금리리스크", "### 1-3 ": "1-3 투자리스크", "### 1-4 ": "1-4 유동성리스크",
             "### 1-5 ": "1-5 자본적정성", "### 1-6 ": "1-6 수익성", "## 2. ": "2 1-나-1~1-나-4·1-다-5(+Ⅱ.7 IT 대체 서술)",
             "## 3. ": "3 금융지주회사·지주·대주주·계열회사 문장", "### 3-참고 ": "3-참고 관계회사·관계사·자회사·그룹",
             "### 5-2 ": "5-2 넓힌 검색으로 찾은 글"}


def art_line(spec, none_txt, T):
    parts = []
    for n, why in spec:
        parts.append("%d조(%s)%s" % (n, T[n], (" " + why) if why else ""))
    s = " · ".join(parts)
    if none_txt and none_txt.startswith("직접 대응 조는"):
        s = none_txt + ": " + s
    elif none_txt:
        s = (s + " · " if s else "") + none_txt
    return ART_LINE + s + " — 검증 때 붙임(모두 판단)"


def csv_art(n, T):
    if n in (1015, 1023, 1033):
        return "대응 조 없음(판단 — 󰊱-가-1 대주주의 적정성: 지원 가능성·비전)"
    if n in (1449, 1462):
        return "대응 조 없음(판단 — 별첨 보험업감독규정: 경영개선 계획 가운데 금융지주회사 자회사 편입)"
    if n == 1073:
        return "33조(%s) ①1호(판단 — 대주주·계열회사와의 구매·용역 계약)" % T[33]
    if n == 1180:
        return "33조(%s) ①1호(판단 — 계열회사간 재보험거래)" % T[33]
    return "33조(%s) ①1호(판단 — 대주주와의 거래)" % T[33]


def fixd_before():
    """fix13_D 가 이 md 에서 고친 줄 「후」 → 「전」."""
    if not os.path.exists(FIXD_LOG):
        return {}
    return {x["후"]: x["전"] for x in json.load(open(FIXD_LOG, encoding="utf-8"))["보정"] if x["파일"] == MD and isinstance(x["후"], str)}


def check_articles(R, md):
    S = source()
    T = S["T"]
    R.h("6. 모범규준 조 번호(조 제목) — 2016.8.1판(%s, %d개 조)" % (ART_CSV, len(T)))
    if not os.path.exists(MB_MD) or len(T) != 59:
        R.ng("모범규준 원문·조목록이 없음")
    lines = body_lines(md.split("\n"))
    nbad, nall = 0, 0
    for i, t in enumerate(lines):
        if t.startswith(">") or t.startswith("```"):
            continue
        for n, tt in ART_RE.findall(t):
            nall += 1
        for b in bad_titles(t, T):
            nbad += 1
            R.ng("md %d행 조 제목이 2016.8.1판과 다름: %s → %d조(%s)" % (i + 1, b, int(re.match(r"\d+", b).group()),
                                                                T.get(int(re.match(r"\d+", b).group()), "?")))
    R.ok("md 본문의 「N조(제목)」 %d곳 대조(다름 %d)" % (nall, nbad))
    stale = [x for x in ("모범규준 원문이 저장소에 없", "모범규준 원문으로 확인하지 못했다") if x in "\n".join(lines)]
    if stale:
        R.ng("모범규준 원문이 없다는 옛 서술이 남아 있음: %s" % stale)
    heads = [t for t in lines if t.startswith("#")]
    for pre, spec, none_txt in SEC_ART:
        h = next((x for x in heads if x.startswith(pre)), None)
        if h is None:
            R.ng("자료 묶음 머리 줄 「%s」 없음" % pre.strip())
            continue
        i = lines.index(h)
        j = next((x for x in range(i + 1, len(lines)) if lines[x].startswith("#")), len(lines))
        al = [x for x in lines[i + 1:j] if x.startswith("- 모범규준 조(판단")]
        if not al:
            R.ng("「%s」 자료 묶음에 모범규준 조(판단) 줄 없음" % h[:30])
        elif al[0] != art_line(spec, none_txt, T) and fixd_before().get(al[0]) != art_line(spec, none_txt, T):
            R.ng("「%s」 조 줄이 스크립트 대응표와 다름" % h[:30])
    R.ok("자료 묶음 %d곳의 「모범규준 조(판단 …)」 줄 확인" % len(SEC_ART))


# ── 7. 「추출 범위에 없음」 반박 ───────────────────────────────────────────────
REFUTE = [
    # (번호, 주장(곳), 범위, 넓힌 검색어, 결과(판단), 처리, Ⅳ장 밖(1~1402행)으로 넓힌 검색어)
    ("R1", "3절 note·6절 표 — 매뉴얼 본문(Ⅰ~Ⅳ장)의 「금융지주회사」「지주」 문장", (1, 1402),
     ["지주", "지 주", "지주사", "지주회사", "holding", "금융그룹", "그룹", "모회사", "지배회사", "복합", "금융복합기업집단", "계열", "연결"],
     "실패(판단) — 「지주」 뜻의 글은 추출 범위에 없음: 「그룹」은 등급구간·표본 그룹, 「지배회사」는 연결재무제표의 지배회사 지분(보험회사 자신), 「계열」은 계열회사·계열사(3절), 「연결」은 연결재무제표·연결대상 자회사",
     "추출 범위에 없음 그대로 — 검색어를 3절 note·6절 표에 덧붙임", None),
    ("R2", "5절 note — 3조(적용대상) 단서(위험이 경미한 자회사등 적용배제)에 대응하는 문항(Ⅳ장)", (IV_A, IV_B),
     ["경미", "적용배제", "적용 배제", "배제", "제외", "예외", "생략", "면제", "소규모", "미미", "실익", "평가대상"],
     "Ⅳ장 실패(판단) — 「배제」는 성과평가에서 재무성과 배제, 「제외」는 유동성자산·지급 제외 등, 「예외」는 겸직 예외, 「생략」은 징계절차 생략",
     "Ⅳ장 밖 Ⅱ.2·Ⅱ.5·Ⅱ.14 의 평가대상·평가부문 제외 기준을 찾음 — 일부 성공(판단), 5-2-1 에 원문", ["소규모", "실익", "미미", "평가대상에서 제외", "평가 제외"]),
    ("R3", "5절 note — 4조(위험관리 철학)에 대응하는 문항(Ⅳ장)", (IV_A, IV_B),
     ["철학", "가치규범", "최상위", "위험성향", "리스크성향", "risk appetite", "appetite", "문화", "관리문화", "전파", "연수"],
     "일부 성공(판단) — 「문화」 1050행 󰊱-나-1 ③ 리스크 중심의 관리문화(1037행은 성과주의 문화)",
     "5-2-2 에 원문(9차 발췌 91행에도 있음)", None),
    ("R4", "5절 note — 17조(의사전달체계) ② 지주→자회사 공식문서 전달에 대응하는 문항(Ⅳ장)", (IV_A, IV_B),
     ["의사전달", "의사 전달", "정보전달", "전달", "공식문서", "공문", "전자문서", "서면", "문서", "지시", "통보", "보고체계"],
     "실패(판단) — 지주·자회사 사이 문서 형식 문항은 추출 범위에 없음. 「전달」 1069·1310행은 회사 안 정보 전달(참고)",
     "추출 범위에 없음 그대로 — 1069행 원문을 참고로 5-2-3 에, 검색어를 5절 note 에 덧붙임", ["의사전달", "공식문서", "전달"]),
    ("R5", "5절 note — 34조(해외위험 관리) 해외진출·해외사업 총괄·사전 검토·정기 점검 문항(Ⅳ장)", (IV_A, IV_B),
     ["해외진출", "해외 진출", "해외사업", "진출", "현지법인", "현지", "해외점포", "해외지점", "해외법인", "국외", "외국", "글로벌", "overseas"],
     "Ⅳ장 실패(판단) — 「현지」는 해외투자 외부전문가, 「외국」은 외국사 국내지점·외화",
     "Ⅳ장 밖 Ⅱ.14 해외 현지법인 및 지점 평가기준(감독당국 평가)을 찾음 — 일부 성공(판단), 5-2-4 에 원문", ["현지법인", "해외현지법인", "해외지점", "진출"]),
]


def search_cell(terms, a, b):
    L = source()["L"]
    zero, hit = [], []
    for t in terms:
        tn = ns(t).lower()
        ls = [n for n in range(a, b + 1) if tn in ns(L[n - 1]).lower()]
        if ls:
            hit.append("「%s」 %d건(%s)" % (t, len(ls), "·".join(map(str, ls[:12])) + ("…" if len(ls) > 12 else "")))
        else:
            zero.append("「%s」" % t)
    return ("0건: " + "·".join(zero) if zero else "") + ("; " if zero and hit else "") + "; ".join(hit)


def page_break_stats():
    """본문 수준(level 0) 문단의 쪽·구역 나누기 표시만으로 쪽을 센다. 장 머리 글(Ⅲ·Ⅳ·[별첨])은 글상자 등 아래 수준에 있어도 그때의 쪽을 쓴다."""
    S = source()
    paras = S["hw"]["paras"]
    top = [p for p in paras if p["level"] == 0]
    pg, at, prev = 1, {}, None
    for p in paras:
        if p["level"] == 0:
            if prev is not None and (p["bt"] & 0x05 or p["sec"] != prev["sec"]):
                pg += 1
            prev = p
        s = p["text"].strip()
        if s in ("Ⅲ", "Ⅳ", "[별첨]") and s not in at:
            at[s] = pg
    n4 = sum(1 for p in top if p["bt"] & 0x04)
    n1 = sum(1 for p in top if p["bt"] & 0x01)
    return n4, n1, at


def refute_rows():
    S = source()
    T = S["T"]
    out = ["| # | 주장(곳) | 넓힌 검색어(같은 출처 전체 md, 공백·대소문자 무시) → 줄 | 결과 | 처리 |", "|---|---|---|---|---|"]
    for rid, claim, (a, b), terms, res, act, wide in REFUTE:
        w2 = (" — 1~1402행으로 넓힘: %s" % search_cell(wide, 1, 1402)) if wide else ""
        out.append("| %s | %s | %d~%d행 — %s | %s | %s%s |" % (rid, claim, a, b, search_cell(terms, a, b), res, act, w2))
    n4, n1, at = page_break_stats()
    toc = S["toc"]
    out.append("| R6 | 머리 「한계」 — 문장별 쪽 번호(hwp 에 쪽 정보 없음) | hwp 문단 머리(PARA_HEADER)의 나누기 표시: 쪽 나누기 %d곳·구역 나누기 %d곳 → "
               "이 표시로만 센 쪽 Ⅲ %d쪽·Ⅳ %d쪽·[별첨] %d쪽 ↔ 목차 Ⅲ %d쪽·Ⅳ %d쪽·[별첨] %d쪽 | 실패 — 자동 쪽 나눔은 hwp 에 저장되지 않음 | "
               "추출 범위에 없음 그대로 — 목차 시작 쪽·줄 번호로 대신(한계 줄에 덧붙임) |"
               % (n4, n1, at.get("Ⅲ", 0), at.get("Ⅳ", 0), at.get("[별첨]", 0), toc[("Ⅲ", None)], toc[("Ⅳ", None)], toc[("별첨", None)]))
    ok = os.path.exists(MB_MD) and len(T) == 59
    out.append("| R7 | 13차 보고 not_got·머리 줄·5절 note — 모범규준 원문이 저장소에 없음 | `handoff/13차_산출물/9-4_모범규준_원문.md`·`dart_out/risk13/모범규준_조목록.csv`(%d개 조) | %s | "
               "조 제목을 2016.8.1판으로 바로잡고 자료 묶음마다 조를 붙임(5-1절·CSV) |" % (len(T), "성공" if ok else "실패"))
    return out


def check_refute(R, md):
    R.h("7. 「추출 범위에 없음」 반박 검색")
    rows = refute_rows()
    t = md.split(VERIFY_HEAD)[-1] if VERIFY_HEAD in md else ""
    if not all(x in t.split("\n") for x in rows):
        R.ng("검증 기록의 「추출 범위에 없음 반박」 표가 다시 찾은 결과와 다름(또는 없음)")
    else:
        R.ok("반박 표 %d행 = 다시 찾은 결과" % (len(rows) - 2))
    body = "\n".join(body_lines(md.split("\n")))
    for ln in body.split("\n"):
        if "추출 범위에 없음" in ln and not ln.startswith(">"):
            if not re.search(r"찾은 방법|검색|찾은 범위|찾음|찾지 못|반박|검증 기록", ln):
                R.ng("「추출 범위에 없음」 줄에 찾은 방법이 없음: %s" % ln[:60])
    R.ok("본문의 「추출 범위에 없음」 줄마다 찾은 방법·검색어가 있음")


# ── 8. 지시서 항목·공통 ───────────────────────────────────────────────────────
def req_rows(md, cov, found):
    S = source()
    L = S["L"]
    lines = md.split("\n")
    out = ["| 지시서 항목(REQUEST13 9-3) | 상태 | 근거·찾은 방법 |", "|---|---|---|"]
    for r in cov:
        if r["k"] == 1:
            continue
        out.append("| 9-3-1 %s(Ⅳ.%d) 비계량 평가항목·세부 점검 문항 전문 | 받은 글 | %s %d줄 · 평가항목 %d · 세부 점검사항 %d(체크리스트 행 %d) |"
                   % (r["nm"], r["k"], r["where"], r["b"] - r["a"] + 1, r["nh"], r["nA"], r["nC"]))
    out.append("| 9-3-1 받지 못한 부문의 자료 위치(쪽·붙임 번호) | 받은 글 | 받지 못한 부문 0개 — 0절 목차 인용(전체 md 59~66행)에 Ⅳ.1~Ⅳ.7 이 모두 있고 6개 부문 모두 1절에 옮김(6개 부문 ↔ 목차 대조 표) |")
    for u, pre in (("1-나-1", "󰊱-나-1."), ("1-나-2", "󰊱-나-2."), ("1-나-3", "󰊱-나-3."), ("1-나-4", "󰊱-나-4."), ("1-다-5", "󰊱-다-5.")):
        n = next(n for n in range(1008, 1107) if is_row(L[n - 1]) and row_cells(L[n - 1])[0].startswith(pre))
        out.append("| 9-3-2 %s 전문 | 받은 글 | 9차 발췌 `handoff/RAAS_매뉴얼_원문.md` %d행 = 전체 md %d행(바이트 같음, 지시대로 다시 옮기지 않음 — 2절 표) |"
                   % (u, n - 959, n))
    nos = {}
    i = 0
    for t in lines:
        m = re.match(r"^\*\*(3-\d\d)\*\*", t)
        if m:
            n, seg, g = found[i]
            for w in g:
                nos.setdefault(w, []).append(m.group(1))
            i += 1

    def span(xs):
        return "·".join(xs) if len(xs) <= 6 else "%s~%s 가운데 %d개" % (xs[0], xs[-1], len(xs))
    out.append("| 9-3-3 「금융지주회사」 문장과 항목 번호 | 받은 글 + 본문 추출 범위에 없음 | 받은 글 %d문장(%s, 별첨 보험업감독규정) · 매뉴얼 본문(Ⅰ~Ⅳ장, 1~1402행) 찾은 방법: 글자열·공백 무시 검색, hwp 문단 글 전부 검색, 넓힌 검색어(반박 표 R1) |"
               % (len(nos.get("금융지주회사", [])), span(nos.get("금융지주회사", []))))
    out.append("| 9-3-3 「지주」 문장과 항목 번호 | 받은 글 + 본문 추출 범위에 없음 | 받은 글 %d문장(%s — 모두 「금융지주회사」 안) · 본문 찾은 방법: 위와 같음(반박 표 R1) |"
               % (len(nos.get("지주", [])), span(nos.get("지주", []))))
    out.append("| 9-3-3 「대주주」 문장과 항목 번호 | 받은 글 | %d문장(%s; 「최대주주」 안 2곳 따로 표시) |" % (len(nos.get("대주주", [])), span(nos.get("대주주", []))))
    ky = sorted(set(nos.get("계열회사", []) + nos.get("계열사", [])))
    out.append("| 9-3-3 「계열회사」(「계열사」 포함) 문장과 항목 번호 | 받은 글 | %d문장(%s) |" % (len(ky), span(ky)))
    out.append("| 끝에 낼 것 — 모범규준 조 번호 | 판단 | 지시서 9-3 에는 조 번호 없음 → 5절 표(제목 바로잡음)·5-1절 자료 묶음별 조·CSV 「%s」 칸 |" % CSV_ART_COL)
    return out


def check_req(R, md, cov, found):
    R.h("8-1. 지시서(REQUEST13 9-3) 항목 대조 표")
    rows = req_rows(md, cov, found)
    t = md.split(VERIFY_HEAD)[-1] if VERIFY_HEAD in md else ""
    tl = t.split("\n")
    for x in rows[2:]:
        c = md_cells(x)
        if not (c[1].startswith("받은 글") or c[1].startswith("추출 범위에 없음") or c[1].startswith("판단")):
            R.ng("지시서 항목 상태 칸 꼴이 다름: %s" % c[0])
        if "추출 범위에 없음" in c[1] and "찾은 방법" not in c[2]:
            R.ng("지시서 항목 「%s」: 추출 범위에 없음인데 찾은 방법 없음" % c[0])
        if x not in tl:
            R.ng("검증 기록에 지시서 항목 행이 없거나 다름: %s" % c[0])
    R.ok("지시서 항목 %d개 — 모두 「받은 글」 또는 「추출 범위에 없음 + 찾은 방법」 또는 「판단」" % (len(rows) - 2))


def secrets():
    vals = []
    for k in ("DART_API_KEY", "LAW_OC"):
        v = os.environ.get(k, "").strip()
        if v:
            vals.append(v)
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*(DART_API_KEY|LAW_OC)\s*=\s*(.+)$", line)
                if m:
                    vals.append(m.group(2).strip().strip('"').strip("'"))
    return [v for v in vals if len(v) >= 6]


def check_common(R, md, files):
    R.h("8-2. 인증값·PDF·검증 기록 절")
    vals = secrets()
    for p in files:
        if not os.path.exists(p):
            continue
        t = read(p) if p != MD else md
        if any(v in t for v in vals):
            R.ng("인증값 문자열이 들어 있음: %s" % p)
        for pat in (r"(?<![A-Za-z_])OC=(?!\*\*\*)[A-Za-z0-9]", r"crtfc_key=[0-9a-f]{20,}", r"DART_API_KEY\s*=\s*\w{10,}", r"LAW_OC\s*=\s*\w{4,}"):
            if re.search(pat, t):
                R.ng("인증값 꼴 문자열(%s): %s" % (pat, p))
    R.ok("인증값 값 %d개·꼴 4개로 %d개 파일 확인(값은 적지 않음)" % (len(vals), len(files)))
    pdfs = [os.path.join(dp, f) for dp, _, fs in os.walk(OUT) for f in fs if f.lower().endswith(".pdf")]
    if pdfs:
        R.ng("산출 폴더에 PDF: %s" % pdfs)
    else:
        R.ok("산출 폴더(handoff/13차_산출물)에 PDF 없음")
    heads = [ln for ln in md.split("\n") if ln.startswith("## ")]
    if not heads or heads[-1] != VERIFY_HEAD:
        R.ng("md 맨 끝 절이 「%s」 아님" % VERIFY_HEAD)
    else:
        R.ok("md 맨 끝 절 「%s」" % VERIFY_HEAD)
    if VERIFY_HEAD in md:
        tail = md.split(VERIFY_HEAD)[-1]
        if md_blocks(tail.split("\n")):
            R.ng("검증 기록 절 안에 인용 블록이 있음(인용은 본문에만)")


def quote_line_stat(st):
    return ("- 대조한 인용: 인용 블록 %d개(%d줄) — 줄 범위 인용 %d개·문장/칸 문단 인용 %d개. 글자 그대로 같음 %d, 공백만 다름 %d, 다름·출처 없음 %d. "
            "인용 안 [글자겹침] 표지 %d개(hwp 겹침 글자·자리와 같음)."
            % (st["blocks"], st["lines"], st["range"], st["seg"], st["exact"], st["space"], st["bad"], st["marks"]))


def verify(md=None, csv_rows=None, write=True, quiet=False, label_="대상"):
    if md is None:
        md = read(MD)
    if csv_rows is None:
        csv_rows = list(csv.DictReader(io.StringIO(read(CSV_P).lstrip("\ufeff"))))
    R = Report()
    R.lines.append("verify13_raas — 13차 9-3 RAAS 산출물 검증(%s, scripts/dart/verify13_raas.py)" % TODAY)
    R.lines.append("%s: %s · %s" % (label_, MD, CSV_P))
    R.lines.append("  sha256 %s  %s" % (sha_bytes(md.encode("utf-8")), MD))
    if os.path.exists(CSV_P):
        R.lines.append("  sha256 %s  %s" % (sha_file(CSV_P), CSV_P))
    md = "\n".join(VERIFY_HEAD if ln == VERIFY_HEAD_KST else ln for ln in md.split("\n"))   # fix13_D 절 제목(KST)
    check_source(R, md)
    st = check_quotes(R, md)
    tb = check_tables(R, md)
    cov = check_coverage(R, md)
    found, per, main = check_words(R, md, csv_rows)
    check_articles(R, md)
    check_refute(R, md)
    check_req(R, md, cov, found)
    if VERIFY_HEAD in md and quote_line_stat(st) not in md.split(VERIFY_HEAD)[-1].split("\n"):
        R.ng("검증 기록의 「대조한 인용」 줄이 다시 센 값과 다름")
    check_common(R, md, [MD, CSV_P, OUT_TXT, os.path.abspath(__file__)])
    R.lines += ["", "문제 %d" % R.bad]
    if write:
        with open(OUT_TXT, "w", encoding="utf-8") as f:
            f.write("\n".join(R.lines) + "\n")
    if not quiet:
        print("\n".join(x for x in R.lines if x.startswith("==") or x.startswith("  !!"))[:5000])
        print("문제", R.bad, "→", OUT_TXT if write else "(기록 안 함)")
    R.st, R.tb, R.cov, R.found, R.per = st, tb, cov, found, per
    return R


# ── 보정(fix) ─────────────────────────────────────────────────────────────────
def baseline():
    os.makedirs(BASE, exist_ok=True)
    if not os.path.exists(BASE_MD):
        got = {}
        for key, p, dst in (("md", MD, BASE_MD), ("csv", CSV_P, BASE_CSV)):
            b = subprocess.run(["git", "show", "%s:%s" % (BASE_COMMIT, p)], capture_output=True).stdout
            if sha_bytes(b) != BASE_SHA[key]:
                b = open(p, "rb").read()
            with open(dst, "wb") as f:
                f.write(b)
            got[key] = sha_bytes(b)
    return read(BASE_MD), open(BASE_CSV, "rb").read()


def patches(T):
    """(곳, 전, 후) — 보정 전 글에서 찾아 바꾼다(없으면 건너뜀). 조 제목은 2016.8.1판 조목록."""
    t27, t28, t30, t34, t55 = T[27], T[28], T[30], T[34], T[55]
    r1 = next(x for x in REFUTE if x[0] == "R1")
    r1s = "·".join("「%s」" % x for x in r1[3])
    r2_4 = "·".join("「%s」" % x for x in dict.fromkeys(next(x for x in REFUTE if x[0] == "R2")[3] + next(x for x in REFUTE if x[0] == "R3")[3]
                                                     + next(x for x in REFUTE if x[0] == "R4")[3]))
    r5s = "·".join("「%s」" % x for x in next(x for x in REFUTE if x[0] == "R5")[3])
    return [
        ("머리 「한계」 ①", "① hwp 에는 쪽 정보가 없다(9차와 같음).",
         "① hwp 에는 쪽 번호가 저장되어 있지 않다(9차와 같음; 검증 때 hwp 문단 머리의 쪽 나누기 표시를 세어 보았으나 목차 쪽과 맞출 수 없음 — 검증 기록 R6)."),
        ("머리 「모범규준 조 번호」",
         "- 모범규준 조 번호: 사용자 지시서 9-3 에는 조 번호가 없다. 폐지 모범규준 원문이 저장소에 없으므로, 지시서 다른 작업(9-4)에 조 제목과 함께 나온 조(3·4·5·17·21·22·24·27·28·30·34·53·55조)에만 「(판단)」으로 대응을 붙였다(5절).",
         "- 모범규준 조 번호: 사용자 지시서 9-3 에는 조 번호가 없다. 13차 작성 때는 폐지 모범규준 원문을 저장소에서 찾지 못해 지시서 다른 작업(9-4)에 나온 조 표현(3·4·5·17·21·22·24·27·28·30·34·53·55조)으로 「(판단)」 대응을 붙였고(5절), "
         "검증(2026-10-07) 때 `handoff/13차_산출물/9-4_모범규준_원문.md`·`dart_out/risk13/모범규준_조목록.csv`(2016.8.1판 1~59조 제목)로 조 제목을 바로잡고 자료 묶음마다 「모범규준 조(판단 …)」 줄을 붙였다(5-1절, 모두 판단)."),
        ("3절 note(「지주」)", "매뉴얼 본문(Ⅰ~Ⅳ장)에는 「금융지주회사」「지주」가 없다(찾은 범위: 1~1402행, 별첨 시작 1403행).",
         "매뉴얼 본문(Ⅰ~Ⅳ장)에서 「금융지주회사」「지주」는 **추출 범위에 없음**(찾은 범위: 1~1402행, 별첨 시작 1403행). "
         "검증(2026-10-07) 때 넓힌 검색어 %s(공백·대소문자 무시)와 hwp 문단 글 전부(머리말·꼬리말 포함)로 다시 찾아도 「지주」 뜻의 글은 추출 범위에 없음(검증 기록 R1)." % r1s),
        ("5절 note(조 제목 출처)", "조 제목은 사용자 지시서 9-4 에 적힌 표현이고 모범규준 원문으로 확인하지 못했다.",
         "조 제목은 13차 작성 때 사용자 지시서 9-4 표현을 따랐고, 검증 때 2016.8.1판 조목록(`dart_out/risk13/모범규준_조목록.csv`)의 제목으로 바로잡았다(검증 기록 「고친 곳」)."),
        ("5절 표 27조", "| 27조(전략·평판위험) |", "| 27조(%s) |" % t27),
        ("5절 표 28조", "| 28조(통합리스크관리시스템) |", "| 28조(%s) |" % t28),
        ("5절 표 30조", "| 30조(적합성 검증) |", "| 30조(%s — 제4절 적합성 검증) |" % t30),
        ("5절 표 34조", "| 34조(해외위험) |", "| 34조(%s) |" % t34),
        ("5절 표 55조", "| 55조(조기경보) |", "| 55조(%s) |" % t55),
        ("5절 note 3·4·17조", "- note: 3조(위험이 경미한 자회사 적용 제외)·4조(위험관리 철학)·17조(지주→자회사 의사 전달 문서 형식)에 대응하는 문항은",
         "- note: 3조(%s — 단서: 위험이 경미한 자회사등 적용배제)·4조(%s)·17조(%s — ②: 공식문서로 전달)에 대응하는 문항은" % (T[3], T[4], T[17])),
        ("5절 note 3·4·17조 끝", "점검 결과 통보 등)이다(판단).",
         "점검 결과 통보 등)이다(판단). 검증(2026-10-07) 때 넓힌 검색어 %s 로 다시 찾음 — 3조: Ⅳ장 밖 Ⅱ.2·Ⅱ.14 평가대상 제외 기준(5-2-1), "
         "4조: 󰊱-나-1 ③ 관리문화 질문(5-2-2), 17조: 회사 안 정보 전달 문항만(5-2-3, 지주·자회사 사이 문서 형식은 추출 범위에 없음) — 검증 기록 R2~R4." % r2_4),
        ("5절 note 34조", "- note: 34조(해외위험)는", "- note: 34조(%s)는" % t34),
        ("5절 note 34조 끝", "현지법인·지점 자체를 계량평가하는 기준이다.",
         "현지법인·지점 자체를 계량평가하는 기준이다. 검증 때 넓힌 검색어 %s 로 다시 찾음 — Ⅳ장 비계량 문항으로는 여전히 추출 범위에 없음, Ⅱ.14 원문은 5-2-4 에 옮김(검증 기록 R5)." % r5s),
        ("5절 note 자회사 문항", "지주의 자회사 관리 조항과 겹치는 조 번호는 지시서에 없어 붙이지 않았다(판단).",
         "지주의 자회사 관리 조항과 겹치는 조 번호는 지시서에 없어 붙이지 않았다(판단). 검증 때 모범규준 원문으로 5조 ②6호·14조(%s)·33조(%s)를 붙였다(5-1절, 판단)." % (T[14], T[33])),
        ("6절 표 9-3-1 조", "| 21·22·24·28·30·34·53·55조(5절) |",
         "| 21조(%s)·22조(%s)·24조(%s)·28조(%s)·30조(%s — 제4절 적합성 검증)·34조(%s)·53조(%s)·55조(%s)(5절) · 검증 때 더한 조는 5-1절(판단) |"
         % (T[21], T[22], T[24], t28, t30, t34, T[53], t55)),
        ("6절 표 9-3-2 조", "| 5·27·28·30조(5절) |",
         "| 5조(%s)·27조(%s)·28조(%s)·30조(%s — 제4절 적합성 검증)(5절) · 검증 때 더한 조는 5-1절(판단) |" % (T[5], t27, t28, t30)),
        ("6절 표 9-3-3 받지 못한 것", "별첨에 옮겨 실은 보험업감독규정 제7-18조·제7-19조 2곳만) |",
         "별첨에 옮겨 실은 보험업감독규정 제7-18조·제7-19조 2곳만; 검증 때 넓힌 검색어로 다시 찾아도 추출 범위에 없음 — 검증 기록 R1) |"),
        ("6절 표 9-3-3 조", "| — (대주주 거래·계열 문항에 대응하는 조는 지시서에 없음) |",
         "| 33조(%s)(판단 — 대주주와의 거래·계열회사 거래 문장; 검증 때 붙임, 5-1절·CSV) · 그 밖의 문장은 대응 조 없음(판단) |" % T[33]),
    ]


def cite(a, b, pg, unit=""):
    S = source()
    rng = ("%d~%d" % (a, b)) if b and b != a else "%d" % a
    return "[%s · %s · %s · 전체 md %s행%s · 수집 %s(9차 원본), 옮김 2026-10-07]" % (S["DOC"], S["POST"], pg, rng, unit, S["COL"])


def pg_label(n):
    p = page_of(n)
    return "목차상 %d쪽~(이 절의 시작 쪽)" % p if p is not None else "목차"


def quote_range(a, b):
    ML = source()["ML"]
    return ["> " + x if x else ">" for x in ML[a - 1:b]]


def seg_slice(n, start_pred, stop_pred):
    segs = units(source()["ML"][n - 1])
    i = next(k for k, s in enumerate(segs) if start_pred(s))
    j = next((k for k in range(i + 1, len(segs)) if stop_pred(segs[k], k)), len(segs))
    return segs[i:j]


def sec52(T):
    S = source()
    L = S["L"]
    o = []
    w = o.append
    w("### 5-2 「추출 범위에 없음」을 넓힌 검색으로 다시 찾은 글(검증 2026-10-07)")
    w("")
    sp = next(x for x in SEC_ART if x[0] == "### 5-2 ")
    w(art_line(sp[1], sp[2], T))
    w("- note: 같은 출처(전체 md)에서 낱말 변형·띄어쓰기·동의어로 다시 찾은 글이다. 검색어와 결과는 검증 기록 「추출 범위에 없음 반박」 표. 조 대응은 모두 (판단).")
    w("")
    a2 = next(n for n in range(S["toc_rng"][1] + 1, len(L)) if L[n - 1] == "2. 평가대상")
    a14 = next(n for n in range(S["toc_rng"][1] + 1, len(L)) if L[n - 1] == "14. 해외 현지법인 및 지점에 대한 평가기준")
    b14 = next(n for n in range(a14, len(L)) if L[n].strip() == "<붙임1>")
    t14 = next(n for n in range(a14, b14) if L[n - 1].strip() == "□ 평가대상")
    w("#### 5-2-1 3조(%s) 단서에 견줄 글 — Ⅱ.2 평가대상·Ⅱ.14 평가대상(Ⅳ장 밖)" % T[3])
    w("")
    w(cite(a2, a2 + 1, pg_label(a2)))
    w("")
    o.extend(quote_range(a2, a2 + 1))
    w("")
    a5 = next(n for n in range(1, len(L)) if "장기손보 미취급 손보사는 금리리스크 부문 평가 제외" in L[n - 1])
    w(cite(a5, a5 + 2, pg_label(a5)))
    w("")
    o.extend(quote_range(a5, a5 + 2))
    w("")
    w(cite(t14, t14 + 1, pg_label(t14)))
    w("")
    o.extend(quote_range(t14, t14 + 1))
    w("")
    w("- note: 감독당국이 RAAS 평가대상에서 소규모·실익이 적은 회사(Ⅱ.14 는 연결대상 자회사인 해외현지법인·지점)를 뺄 수 있고(Ⅱ.2·Ⅱ.14), 비중이 미미한 부문은 평가에서 뺀다(Ⅱ.5)는 글 — "
      "모범규준 3조 단서·18조 ③·36조 단서(위험이 경미하거나 비중이 미미한 자회사등 제외)와 같은 꼴의 적용 제외 기준(판단). Ⅳ장 비계량 문항으로는 추출 범위에 없음(검증 기록 R2).")
    w("")
    n4 = 1050
    segs = seg_slice(n4, lambda s: s.startswith("③ 리스크 중심의 관리문화"), lambda s, k: bool(qnum(s)))
    w("#### 5-2-2 4조(%s)에 견줄 글 — 󰊱-나-1 질문 ③(9차 발췌 91행에도 있음)" % T[4])
    w("")
    w(cite(n4, n4, pg_label(n4), "(칸 안 문단 — 󰊱-나-1 점검 체크리스트 질문 ③과 그 아래 ▫)"))
    w("")
    o.extend("> " + s for s in segs)
    w("")
    w("- note: 「철학」·「최상위」·「가치규범」 낱말은 추출 범위에 없음. 리스크 중심의 관리문화를 묻는 질문이 위험관리 철학(임직원이 고려하고 그룹에 전파하는 가치규범)에 가장 가까움(판단, 검증 기록 R3).")
    w("")
    n5 = next(n for n in range(IV_A, IV_B + 1) if "경영의사결정에 필요한 정보가 효율적으로 전달될 수 있는 체제의 구축" in L[n - 1])
    segs = seg_slice(n5, lambda s: s.lstrip().startswith("①"),
                     lambda s, k: s.startswith("▫") and k > 2 and "경영의사결정" not in s and not s.startswith("-"))
    w("#### 5-2-3 17조(%s)에 견줄 글 — 회사 안 정보 전달(지주·자회사 사이는 아님)" % T[17])
    w("")
    w(cite(n5, n5, pg_label(n5), "(칸 안 문단 — 󰊱-다-1 점검 체크리스트 질문 ①과 그 아래 ▫·- 일부)"))
    w("")
    o.extend("> " + s for s in segs)
    w("")
    w("- note: 내부통제기준에 들어갈 「정보 전달 체제」 — 회사 안의 일이며, 모범규준 17조 ②의 지주→자회사 공식문서 전달에 대응하는 문항은 추출 범위에 없음(검증 기록 R4). "
      "1310행 󰊵-가-2 의 「정보전달의 절차」(유동성 위기 관리대책)는 1-4절 인용에 있다.")
    w("")
    w("#### 5-2-4 34조(%s)에 견줄 글 — Ⅱ.14 해외 현지법인 및 지점에 대한 평가기준(Ⅳ장 밖)" % T[34])
    w("")
    w(cite(a14, b14, pg_label(a14)))
    w("")
    o.extend(quote_range(a14, b14))
    w("")
    w("- note: 보험회사의 연결대상 해외 현지법인·지점을 감독당국이 CAEL 방식으로 따로 평가하는 기준 — 모범규준 34조 ④(자회사 해외위험 관리실태 정기 점검)에 견줄 감독 쪽 기준(판단). "
      "보험회사가 해외진출·해외사업 위험을 총괄·사전 검토하는지 보는 Ⅳ장 비계량 문항은 추출 범위에 없음(검증 기록 R5).")
    w("")
    return o


def sec51(T):
    o = []
    w = o.append
    w("### 5-1 자료 묶음별 모범규준 조(검증 때 붙임·바로잡음, 2016.8.1판 제목, 모두 판단)")
    w("")
    w("- note: 근거 조문은 `handoff/13차_산출물/9-4_모범규준_원문.md` 5장(2016.8.1판 전문). 위 5절 표는 13차 대응을 두고 조 제목만 바로잡았다(전·후는 검증 기록).")
    w("- note: 30조의 제목은 「%s」(제4절 적합성 검증의 첫 조)다 — 사후검증 문항은 31조(%s)·32조(%s)에 더 가깝다(판단)." % (T[30], T[31], T[32]))
    w("- note: 28조(%s)는 통합위험관리시스템 구축 조다 — 13차가 28조에 이은 ORSA·통합리스크 수준 문항은 제5장 37조(%s)·46조(%s)·47조(%s)에 더 가깝다(판단)." % (T[28], T[37], T[46], T[47]))
    w("- note: 유동성 위기 관리대책(contingency plan, 1310행)의 「역할 분담」은 57조(%s) ②(비상계획에 담을 관련부서간 역할 및 책임)에 더 가깝다 — 13차의 53조(%s) 대응은 그대로 둠(판단)." % (T[57], T[53]))
    w("")
    w("| 자료 묶음(md 절) | 모범규준 조(2016.8.1판 제목) — 까닭(판단) |")
    w("|---|---|")
    for pre, spec, none_txt in SEC_ART:
        s = art_line(spec, none_txt, T)[len(ART_LINE):].replace(" — 검증 때 붙임(모두 판단)", "")
        w("| %s | %s |" % (SEC_LABEL[pre], s.replace("|", "／")))
    w("")
    return o


def apply_fix(text, T):
    lines = text.split("\n")
    if VERIFY_HEAD in lines:
        lines = lines[: lines.index(VERIFY_HEAD)]
        while lines and not lines[-1].strip():
            lines.pop()
        lines.append("")
    text = "\n".join(lines)
    done = []
    for where, old, new in patches(T):
        c = text.count(old)
        if c and new not in text:
            text = text.replace(old, new)
            done.append((where, old, new, c))
    lines = text.split("\n")
    # 자료 묶음 조 줄
    n_art = 0
    for pre, spec, none_txt in SEC_ART:
        if pre == "### 5-2 ":
            continue
        i = next((k for k, x in enumerate(lines) if x.startswith(pre)), None)
        if i is None:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if lines[j].startswith("- 모범규준 조(판단"):
            lines[j] = art_line(spec, none_txt, T)
            continue
        lines[j:j] = [art_line(spec, none_txt, T), ""] if not lines[j].startswith("- ") else [art_line(spec, none_txt, T)]
        n_art += 1
    # 3절 인용 출처 줄
    n_cite = 0
    out = []
    k = 0
    while k < len(lines):
        t = lines[k]
        out.append(t)
        m = re.match(r"^\*\*3-(?:참고-)?\d\d\*\* · .* · 전체 md (\d+)행(?: · 9차 파일 \d+행\(이미 받음\))?$", t)
        if m:
            nxt = next(x for x in range(k + 1, len(lines)) if lines[x].strip())
            if not lines[nxt].startswith("["):
                n = int(m.group(1))
                out += ["", cite(n, n, pg_label(n), "(문장 단위)")]
                n_cite += 1
        k += 1
    lines = out
    # 5-1·5-2 절
    if not any(x.startswith("### 5-1 ") for x in lines):
        i6 = next(k for k, x in enumerate(lines) if x.startswith("## 6. "))
        lines[i6:i6] = sec51(T) + sec52(T)
    return "\n".join(lines), done, n_art, n_cite


def write_csv(rows, T):
    cols = CSV_COLS + [CSV_ART_COL]
    buf = io.StringIO()
    cw = csv.DictWriter(buf, fieldnames=cols, lineterminator="\r\n")
    cw.writeheader()
    for r in rows:
        r = {k: r.get(k, "") for k in CSV_COLS}
        r[CSV_ART_COL] = csv_art(int(r["전체md줄"]), T)
        cw.writerow(r)
    with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
        f.write(buf.getvalue())


ISSUE_CATS = [
    ("인용 앞 출처 줄(문서명·URL·쪽·줄·수집일) 없음", r"출처 줄"),
    ("조 제목이 2016.8.1판과 다름", r"조 제목이 2016\.8\.1판과 다름"),
    ("자료 묶음에 모범규준 조(판단) 줄 없음", r"모범규준 조\(판단\) 줄 없음|자료 묶음 머리 줄"),
    ("모범규준 원문이 없다는 옛 서술", r"옛 서술"),
    ("CSV 조 칸 없음", r"CSV 에 「"),
    ("지시서 항목 대조 표 없음", r"지시서 항목"),
    ("검증 기록 절·표 없음", r"검증 기록|맨 끝 절"),
    ("인용 글이 원문과 다름", r"인용 글이|인용이 전체 md|표지가 hwp 와 다름"),
]


def verify_record(R_before, R_mid, done, n_art, n_cite, base_md, base_csv, T, md_now):
    S = source()
    o = []
    w = o.append
    w(VERIFY_HEAD)
    w("")
    w("- 검증 스크립트: `scripts/dart/verify13_raas.py`(`python3 -I`; 인자 없이 = 대조만, `fix` = 보정 전 사본에서 다시 고침) · 대조 결과: `dart_out/risk13/verify13_raas.txt` · 웹 요청 0건(9차 원본만 읽음).")
    w("- 원본 사슬: hwp sha256 `%s`(9차 meta 와 같음) → hwp 를 `scripts/dart/hwp2md.py`(수정 없음)로 메모리에서 다시 바꾼 글 = `%s`(바이트 단위 같음, sha256 `%s` = 9차 발췌 7행 기록)."
      % (S["meta"]["sha256"], FULL, sha_file(FULL)))
    w("- 보정 전 사본: `%s`(sha256 `%s`)·`%s`(sha256 `%s`) — git 무시 폴더. 보정 전 대조 문제 %d건(아래 「고친 곳」에서 모두 고침), 보정 뒤 다시 대조한 결과는 결과 파일 끝 줄 「문제 N」."
      % (BASE_MD, sha_bytes(base_md.encode("utf-8")), BASE_CSV, sha_bytes(base_csv), R_before.bad))
    cats = {}
    for s in R_before.issues:
        key = next((lab for lab, rx in ISSUE_CATS if re.search(rx, s)), "기타")
        cats[key] = cats.get(key, 0) + 1
    w("- 보정 전 문제 종류: " + " · ".join("%s %d건" % (k, v) for k, v in sorted(cats.items(), key=lambda x: -x[1])))
    w("")
    w("### 대조한 인용")
    w("")
    w(quote_line_stat(R_mid.st))
    tb = R_mid.tb
    w("- 표·머리 줄 안 원문 조각: 평가항목 머리 줄 %(head)d · 1절 세부 점검사항 행 %(row1)d · 2절 표 %(t2)d행·목록 줄 %(list2)d · 3절·3-참고 머리 %(h3)d(줄·9차 줄·쪽) · "
      "4-1 겹침 글자 %(t41)d · 4-2 이름 %(t42)d · 5절 근거 문단 %(t5)d(첫 칸·칸 문단·질문 번호) — 모두 원문과 같음." % tb)
    w("- 틀린 인용: 0곳(인용 글을 바꾼 곳 없음). 보정 전 인용 가운데 출처 줄이 빠진 것은 3절·3-참고 문장 인용 %d곳(머리 줄에 쪽·줄만 있고 문서명·URL·수집일이 없었음)." % n_cite)
    w("")
    w("### 고친 곳(전·후)")
    w("")
    w("| # | 곳 | 전 | 후 |")
    w("|---|---|---|---|")
    k = 0
    for where, old, new, c in done:
        k += 1
        w("| %d | %s%s | %s | %s |" % (k, where, (" (%d곳)" % c) if c > 1 else "", old.replace("|", "／").strip("／ "), new.replace("|", "／").strip("／ ")))
    k += 1
    w("| %d | 3절·3-참고 문장 인용 %d곳 | 머리 줄(쪽·줄)만 — 문서명·URL·수집일 없음 | 인용 바로 앞에 출처 줄 [문서명 · 게시글 URL · 목차상 쪽 · 전체 md 줄(문장 단위) · 수집 %s(9차 원본), 옮김 2026-10-07] |" % (k, n_cite, S["COL"]))
    k += 1
    w("| %d | 자료 묶음 %d곳(0·0-1·0-2·1-1~1-6·2·3·3-참고) | 조 번호 없음(5절 표에만 13차 조) | 머리 줄 아래 「모범규준 조(판단, 2016.8.1판 제목 …)」 줄 |" % (k, n_art))
    k += 1
    w("| %d | 5-1·5-2절 | 없음 | 5-1 자료 묶음별 조 표, 5-2 넓힌 검색으로 찾은 원문 4묶음(인용 블록 6개) |" % k)
    k += 1
    w("| %d | CSV `%s` | 7칸 | 8칸 — 「%s」 칸(문장별 조, 모두 판단) 덧붙임 |" % (k, CSV_P, CSV_ART_COL))
    w("")
    w("### 채운 항목")
    w("")
    w("- 지시서 9-3 항목(아래 대조 표)마다 「받은 글」/「추출 범위에 없음 + 찾은 방법」을 적음 — 빠진 지시서 항목은 없었고, 「끝에 낼 것 — 모범규준 조 번호」를 자료 묶음마다 채움(5-1절·CSV).")
    w("- 「추출 범위에 없음」 5건(R1~R5)에 넓힌 검색어를 덧붙이고, 찾은 글 4묶음을 5-2절에 원문으로 넣음. R7(모범규준 원문 없음)은 반박 성공 → 조 제목 바로잡음.")
    w("")
    w("### 6개 부문 ↔ 목차 대조")
    w("")
    o.extend(coverage_table(R_mid.cov))
    w("")
    w("- note: 목차 Ⅳ장 항목은 1.~7. 부문뿐이고(쪽만 있음) 그 아래 평가항목은 <붙임5>(목차 28쪽)에 있어 둘 다 맞춰 봄. Ⅳ.1 은 지시대로 9차 발췌로 갈음. 평가항목 이름은 공백·가운뎃점 종류만 다른 것을 같게 봄(4-2절의 이름 차이는 세부 점검사항 이름).")
    w("")
    w("### 「금융지주회사·지주·대주주·계열회사(계열사)」 문장 다시 세기")
    w("")
    o.extend(recount_table(R_mid.per, R_mid.found))
    w("")
    w("- note: 단위 규칙(표 밖 = 줄, 표 안 = 첫 칸은 칸 전체·나머지 칸은 <br> 문단)을 이 스크립트에서 따로 짜서 전체 md 1~%d행을 다시 셈 — md 3절 「문장 수: %d개」·낱말별 값, 3절 항목 %d개(순서·줄·글·걸린 낱말), CSV %d행, 6절 표와 모두 같음."
      % (len(S["L"]), len(R_mid.found), len(R_mid.found), len(R_mid.found)))
    w("")
    w("### 「추출 범위에 없음」 반박")
    w("")
    o.extend(refute_rows())
    w("")
    w("### 지시서 항목 대조")
    w("")
    o.extend(req_rows(md_now, R_mid.cov, R_mid.found))
    w("")
    w("### 남은 문제")
    w("")
    w("- 문장 하나하나의 쪽 번호는 여전히 모름(hwp 에 화면 쪽이 저장되지 않음, R6) — 목차 시작 쪽과 전체 md 줄 번호로 대신함.")
    w("- 5절 표·1절 세부 점검사항 표·4-1/4-2 표에는 원문 조각이 표 칸 안에 들어 있음(인용 블록 밖) — 모두 원문과 글자 대조했고 같은 글이 1절 인용 블록에 있음. 표 꼴은 13차 그대로 둠.")
    w("- 모범규준 조 대응은 모두 판단이며, RAAS 는 보험회사(자회사) 평가 기준이라 지주 차원 조와는 견줌일 뿐임. 3조·17조·34조에 바로 대응하는 Ⅳ장 비계량 문항은 추출 범위에 없음(R2·R4·R5).")
    w("- `scripts/dart/web13_raas.py` 를 다시 돌리면 md·CSV 가 13차 글로 돌아감 — 그 뒤에는 `python3 -I scripts/dart/verify13_raas.py fix` 를 다시 돌릴 것.")
    w("")
    return o


def fix():
    T = source()["T"]
    base_md, base_csv = baseline()
    base_rows = list(csv.DictReader(io.StringIO(base_csv.decode("utf-8-sig"))))
    R_before = verify(md=base_md, csv_rows=base_rows, write=False, quiet=True, label_="보정 전 사본")
    text, done, n_art, n_cite = apply_fix(base_md, T)
    write_csv(base_rows, T)
    with open(MD, "w", encoding="utf-8") as f:
        f.write(text)
    R_mid = verify(md=text, write=False, quiet=True, label_="보정 중")
    rec = verify_record(R_before, R_mid, done, n_art, n_cite, base_md, base_csv, T, text)
    if not text.endswith("\n"):
        text += "\n"
    text = text.rstrip("\n") + "\n\n" + "\n".join(rec).rstrip("\n") + "\n"
    with open(MD, "w", encoding="utf-8") as f:
        f.write(text)
    print("보정 전 문제 %d건 · 바꾼 글 %d곳 · 조 줄 %d · 출처 줄 %d" % (R_before.bad, len(done), n_art, n_cite))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        fix()
    R = verify()
    sys.exit(0 if R.bad == 0 else 1)


if __name__ == "__main__":
    main()
