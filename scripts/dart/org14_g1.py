#!/usr/bin/env python3
"""14차 그룹 g1 — KB금융지주·신한금융지주: 지주 조직도 × 조직별 인원 × 겸직.

하는 일(로컬 파일만 읽음, 웹 요청 없음):
  1) 조직도 판독 A(dart_out/org14/<회사>_판독A.json, 사람이 그림을 보고 적은 것)를 읽는다.
  2) 사업보고서 FY2025 원문 XML(dart_out/raw/document/<접수번호>.zip)에서 임원 표·임원 겸직 표·
     직원 표·지원조직 표·내부회계 인력 표를 뽑고, 같은 보고서 PDF 텍스트
     (dart_out/text/risk8/사업보고서__…txt)에서 칸 글이 나오는 쪽을 찾아 붙인다(공백 무시 대조).
  3) 연차보고서·경영공시·사업보고서 텍스트에서 정해 둔 서술을 줄 그대로 옮긴다(쪽 포함).
  4) 산출: handoff/14차_조직인원겸직/14_<회사>.md, dart_out/org14/<회사>_{조직단위,임원겸직,지원조직,판독대조}.csv
     와 dart_out/org14/g1_검사.json(대조·검사 기록).
  5) 검증 반영 입력 dart_out/org14/<회사>_검증반영.json(검증 에이전트가 2026-10-16 산출물에 직접 고친 값 — 판독대조 B·확정·
     확정 방법, 판독_대조 칸, 단위 비고, 인원 보탬, md 6) 보탬·바꿈, 7) 검증 기록)을 읽어 그때 산출물을 그대로 다시 만든다.
  6) 비평 보정(critic14, 2026-10-19): 「없음」 꼴 보정 표(FIX_EOPSEUM), 맡은 임원 찾은 방법, 거꾸로 조직도 (판단) 표시,
     빠진 글 보탬, 떨어진 줄 인용 블록 표지, 사업보고서 「조직도」 검색 기록, 7) 끝 「비평 보정」 기록. 작업 시각은 고정값(멱등).
  7) 비평 보정 2(critic14_2, 2026-10-19): 보정 표 2(FIX2 — 한계 줄 단정, 기준일 칸 「날짜(판단: …)」 꼴; RB2_MARK — 판독대조 판독B ② 꼴),
     지원조직 CSV 열 이름 「주요 활동(원문)」, 7) 끝 「비평 보정 2」 기록. 위 6) 기록은 그대로 남게 FIX 뒤에 씀.

실행: python3 -I scripts/dart/org14_g1.py   (키·OC 값은 쓰지도 읽지도 않음)
"""
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from dart import docparse as dp  # noqa: E402

OUT_DIR = ROOT / "dart_out" / "org14"
MD_DIR = ROOT / "handoff" / "14차_조직인원겸직"
TXT = ROOT / "dart_out" / "text" / "risk8"
KST = dt.timezone(dt.timedelta(hours=9))
NONE = "추출 범위에 없음"


# ───────────────────────── 비평 보정(critic14 대응) ─────────────────────────
FIX_KST = "2026-10-19 09:52 KST"  # 비평 보정을 넣은 작업 시각(고정값 — 다시 돌려도 같은 파일이 나오게)
# 「없음」 규칙(13차와 같은 공통 꼴) 보정 표: (전, 후, 규칙). 원문 인용(md 「> 」 줄·``` 블록)에는 쓰지 않고,
# 「전」 글이 원문 텍스트에 나오지 않는지는 run_company 에서 확인함. 긴 것부터 차례로 바꿈.
#   ① 자료를 찾지 못함 → 추출 범위에 없음(찾은 범위) ② 원문 표·글 안 관찰 → 나오지 않음 ③ 대응 판단 → 대응하는 … 를 찾지 못함
#   ④ 그대로 둠: 원문 인용, 작업 사실(웹 요청 없음·고친 곳 없음·바뀐 곳 없음), 7) 검증 기록의 전 → 후 기록
FIX_EOPSEUM = [
    ("문장에 기준일 글 없음 (사업보고서 기준일 2025년 12월 31일)", "문장에 기준일 글이 나오지 않음 (사업보고서 기준일 2025년 12월 31일 — (판단))", "②+(판단) 표시"),
    ("표에 기준일 글 없음", "표에 기준일 글이 나오지 않음", "②"),
    ("문장에 기준일 글 없음", "문장에 기준일 글이 나오지 않음", "②"),
    ("표 칸에 줄바꿈이 없는 것은 원문 XML 칸 글에도 줄바꿈이 없기 때문", "표 칸에 줄바꿈이 나오지 않는 것은 원문 XML 칸 글에도 줄바꿈이 나오지 않기 때문", "②"),
    ("칸 안 항목 사이에 구분 글자가 없는 것도", "칸 안 항목 사이에 구분 글자가 나오지 않는 것도", "②"),
    ("(판단) 대응 단위 없음 — ", "(판단) 대응하는 단위를 찾지 못함 — ", "③"),
    ("대응 단위 없음", "대응하는 단위를 찾지 못함(판단)", "③"),
    ("원문 XML 없음(", "원문 XML zip 을 읽지 못함(", "작업 사실(낱말만 바로잡음 — zip 파일은 있으나 열리지 않음)"),
    ("— 조직도에 「감사담당」 없음;", "— 조직도(판독)에 「감사담당」이 나오지 않음;", "②"),
    ("- 부서 단위 겸직 글(숫자 없음, 경영공시):", "- 부서 단위 겸직 글(경영공시 — 이 글에 숫자가 나오지 않음):", "②"),
    ("검색 — 지주 임직원 수 글 없음(목차 일반현황은 조직 및 영업점뿐)", "검색 — 추출 범위에 없음(지주 임직원 수 글이 나오지 않음; 목차 「일반현황」 아래는 「조직 및 영업점」뿐)", "①"),
    ("검색 — 지주 임직원 수 글 없음", "검색 — 추출 범위에 없음(지주 임직원 수 글이 나오지 않음)", "①"),
    ("2026.8 조직도(판독)에 같은 이름 없음", "2026.8 조직도(판독)에 같은 이름이 나오지 않음", "②"),
    ("사업보고서 표에는 합계 숫자 없음", "사업보고서 표에는 합계 숫자가 나오지 않음", "②"),
    ("54상자 이름·겸직표시(모두 없음) 전부 같음", "54상자 이름·겸직표시(모두 빈칸 — 표시 나오지 않음) 전부 같음", "②"),
    ("인원 없는 43개 단위 이름", "인원이 나오지 않는 43개 단위 이름", "②"),
    ("의 일반 낱말(계열사)이라 해당 없음.", "의 일반 낱말(계열사)이라 단위 인원 글이 아님 (판단).", "③"),
    ("이 뜻을 적은 원문은 없음.", "이 뜻을 적은 원문은 찾지 못함(추출 범위에 없음 — 찾은 범위: 위 「(겸)」「겸직」「겸임」 검색).", "①"),
    ("의 겸직 상대 회사·인원은 추출 범위에 없음.", "의 겸직 상대 회사·인원은 추출 범위에 없음(찾은 범위: 같은 검색).", "①"),
    ("겸직 직원 수로 볼 수는 없음 — ", "겸직 직원 수로 보지 않음 — ", "③"),
    ("겸직 경영진이 있다는 글이나 숫자는 없음.", "겸직 경영진이 있다는 글이나 숫자는 나오지 않음.", "②"),
    ("같은 이름 단위가 조직도에 없고", "같은 이름 단위가 조직도(판독)에 나오지 않고", "②"),
    ("에는 없는 사람(직원 신분 겸직으로 보임 (판단))", "에는 나오지 않는 사람(직원 신분 겸직으로 보임 (판단))", "②"),
    ("「(겸)」 0건, 「겸직」「겸임」 검색 — 정의 글 없음", "「(겸)」 0건, 「겸직」「겸임」 검색 — 추출 범위에 없음(정의 글이 나오지 않음)", "①"),
    ("같은 검색 — 모형검증팀만 「은행 겸직」 글 있음(인원 숫자 없음)", "같은 검색 — 추출 범위에 없음(모형검증팀만 「은행 겸직」 글이 나오고 인원 숫자는 나오지 않음)", "①"),
    ("띄어쓰기 없어 보임", "띄어쓰기가 보이지 않음", "②"),
    ("같은 방법(인원 없는 39개 단위)", "같은 방법(인원이 나오지 않는 39개 단위)", "②"),
    ("직원의 타사 임원 겸직(숫자 없음)", "직원의 타사 임원 겸직(숫자가 나오지 않음)", "②"),
    ("— 겸직 언급 없음(아래 인용)", "— 겸직 언급이 나오지 않음(아래 인용)", "②"),
    ("반박 못 함 — 정의 글 없음.", "반박 못 함 — 정의 글이 나오지 않음.", "②"),
    ("글 밖에 없음 |", "글 밖에 나오지 않음 |", "②"),
    ("세 숫자 차이로 겸직 직원 수를 셀 수 없음.", "세 숫자 차이로 겸직 직원 수를 세지 않음.", "③"),
    ("겸직 상대 회사·인원은 원문에 없음 — ", "겸직 상대 회사·인원은 원문에서 찾지 못함(추출 범위에 없음 — 찾은 범위: 위 ④ 표) — ", "①"),
    ("추출 범위에 없음(표에 부서명 칸이 없음)", "추출 범위에 없음(찾은 범위: 연차보고서 p.201 준법감시직원 현황 표 — 표에 부서명 칸이 나오지 않음)", "①+②"),
    ("팀 전체 인원은 추출 범위에 없음.", "팀 전체 인원은 추출 범위에 없음(찾은 범위: md 7) 검증 기록 ④ 반박 검색).", "①"),
]
# 판독대조 CSV 빈 값 표지(「(없음…)」 → 빈칸 표지)
RB_MARK = {("상위단위", "(없음 — 맨 위)"): "(빈칸 — 맨 위)", ("상위단위", "(없음)"): "(빈칸)",
           ("겸직표시", "(없음)"): "(빈칸 — 표시 나오지 않음)"}
GAP_MARK = "[…줄 건너뜀: 텍스트 {a}~{b}행…]"
# 7) 검증 기록(검증 반영 입력 「검증기록_줄」) 가운데 지난 전 → 후 기록 줄 번호(0부터) — 「없음」 규칙 ④로 그대로 둠
VR_KEEP = {"KB금융지주": (9, 21), "신한금융지주": (9, 13, 22, 23, 24)}


class Fixer:
    """보정 표를 글에 쓰고 몇 곳 바꿨는지 셈(회사·산출물별)."""

    def __init__(self):
        self.n = {}

    def __call__(self, s, where):
        if not s or "없" not in s:
            return s
        for old, new, _ in FIX_EOPSEUM:
            k = s.count(old)
            if k:
                s = s.replace(old, new)
                self.n[(where, old)] = self.n.get((where, old), 0) + k
        return s


FIX = Fixer()


# ───────────────────────── 비평 보정 2(critic14_2 대응) ─────────────────────────
FIX2_KST = "2026-10-19 11:40 KST"  # 비평 보정 2 를 넣은 작업 시각(고정값 — 멱등)
BASIS_RULE = "기준일 칸 공통 꼴(iM 꼴 「<날짜>(판단: <무엇>에 기준일 글이 나오지 않아 <근거>로 둠)」)"
# (전, 후, 규칙, 꼴) — 위 FIX_EOPSEUM 을 쓴 뒤의 글에 씀(위 「비평 보정」 기록 숫자는 그대로 남게).
#   꼴 "sub" = 글 안 어디든, "cell" = CSV 칸 줄 전체 · md 표 칸(「| 」·「<br>」 사이) 조각 전체만. 긴 것부터.
FIX2 = [
    ("일반 부서 인원은 공시되지 않아 대부분 「추출 범위에 없음」",
     "일반 부서 인원은 추출 범위(사업보고서·연차보고서·경영공시 — 찾은 방법은 6) 받지 못한 것)에 나오지 않아 대부분 「추출 범위에 없음」",
     "한계 줄 단정 → 추출 범위 꼴(critic14_2 [2])", "sub"),
    ("표에 기준일 글이 나오지 않음 (사업보고서 기준일 2025년 12월 31일 — (판단))",
     "2025.12.31(판단: 표에 기준일 글이 나오지 않아 사업보고서 작성기준일로 둠)", BASIS_RULE, "sub"),
    ("문장에 기준일 글이 나오지 않음 (사업보고서 기준일 2025년 12월 31일 — (판단))",
     "2025.12.31(판단: 문장에 기준일 글이 나오지 않아 사업보고서 작성기준일로 둠)", BASIS_RULE, "sub"),
    ("표에 기준일 글이 나오지 않음(사업보고서 2025.12.31 기준 (판단))",
     "2025.12.31(판단: 표에 기준일 글이 나오지 않아 사업보고서 작성기준일로 둠)", BASIS_RULE, "sub"),
    # 날짜 글이 아예 없던 칸(연차보고서 문장 행만 — run_company 에서 출처가 연차보고서인지 확인)
    ("문장에 기준일 글이 나오지 않음",
     "2025년(판단: 문장에 기준일 글이 나오지 않아 연차보고서 대상 연도로 둠)", BASIS_RULE + " · 날짜 글이 없던 칸(critic14_2 [5])", "cell"),
]
# 판독대조 CSV 판독B 칸(검증 반영 입력 = 판독 B JSON 글) 의 ② 꼴(g3·g4 와 같게) — (전 조각, 후 조각)
RB2_MARK = [("같은 집계 글이 없음", "같은 집계 글이 적히지 않음"), ("범례·각주가 쪽에 없음", "범례·각주가 쪽에 나오지 않음")]
FIX2N = {}
_MD_CELL = {}


def fix2(s, where, md=False):
    """FIX2 를 글 하나(CSV 칸 또는 md 줄)에 쓰고 바꾼 곳을 셈."""
    if not s:
        return s
    for old, new, _, kind in FIX2:
        if kind == "sub":
            k = s.count(old)
            s = s.replace(old, new)
        elif md:
            rx = _MD_CELL.setdefault(old, re.compile(r"(?:(?<=\| )|(?<=<br>))" + re.escape(old) + r"(?=<br>| \|)"))
            s, k = rx.subn(new, s)
        else:
            parts = s.split("\n")
            k = sum(p == old for p in parts)
            s = "\n".join(new if p == old else p for p in parts)
        if k:
            FIX2N[(where, old)] = FIX2N.get((where, old), 0) + k
    return s


def fix2_rows(rows, where, cols):
    return [{k: (fix2(v, where) if k in cols else v) for k, v in r.items()} for r in rows]


def none_in(where, what):
    """① 꼴: 추출 범위에 없음(찾은 범위: …)."""
    return f"{NONE}(찾은 범위: {where} — {what})"


def fix_rows(rows, where, skip_cols=()):
    return [{k: (v if k in skip_cols else FIX(v, where)) for k, v in r.items()} for r in rows]


def load_vr(company):
    """검증 반영 입력(dart_out/org14/<회사>_검증반영.json): 검증 에이전트가 2026-10-16 에 산출물에 직접 고친 값
    (판독대조 B·확정·확정 방법, 판독_대조 칸, 단위 비고 고침, 인원 보탬, md 6) 보탬·바꿈, 7) 검증 기록)과
    작업 시각(고정값 — 다시 돌려도 같은 파일이 나오게)."""
    return json.loads((OUT_DIR / f"{company}_검증반영.json").read_text(encoding="utf-8"))


# ───────────────────────── 공통 도구 ─────────────────────────
def nz(s):
    """공백 제거(대조용)."""
    return re.sub(r"\s+", "", s or "")


def nzd(s):
    """공백 제거 + 가운뎃점 꼴 통일(대조용, 판단 표시와 함께만 씀)."""
    s = nz(s)
    for ch in "ㆍᆞ・‧•-":
        s = s.replace(ch, "·")
    return s


def kst(iso):
    if not iso:
        return ""
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def read_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p, cols, rows):
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


class Text:
    """쪽 표지(=== p.N ===)가 있는 텍스트 파일. 줄→쪽, 공백 제거 대조."""

    def __init__(self, path):
        self.path = path
        self.rel = str(Path(path).relative_to(ROOT))
        self.lines = Path(path).read_text(encoding="utf-8").split("\n")
        self.page = []
        cur = 0
        for l in self.lines:
            m = re.match(r"=== p\.(\d+) ===", l)
            if m:
                cur = int(m.group(1))
            self.page.append(cur)
        # 공백 제거 글자열과 글자→줄 대응
        buf, owner = [], []
        for i, l in enumerate(self.lines):
            if l.startswith("=== p."):
                continue
            for ch in nz(l):
                buf.append(ch)
                owner.append(i)
        self.norm = "".join(buf)
        self.owner = owner
        self._line_start = {}
        for k, i in enumerate(owner):
            self._line_start.setdefault(i, k)

    def find_line(self, rx, after=0, before=None):
        r = re.compile(rx)
        hi = len(self.lines) if before is None else before
        for i in range(after, hi):
            if r.search(self.lines[i]):
                return i
        return None

    def char_of_line(self, i):
        while i < len(self.lines):
            if i in self._line_start:
                return self._line_start[i]
            i += 1
        return len(self.norm)

    def find_norm(self, s, lo_line=0, hi_line=None):
        """공백 무시 대조. 찾으면 (시작 줄, 끝 줄) 아니면 None."""
        key = nz(s)
        if not key:
            return None
        a = self.char_of_line(lo_line)
        b = len(self.norm) if hi_line is None else self.char_of_line(hi_line)
        k = self.norm.find(key, a, b)
        if k < 0 or k + len(key) > b:
            return None
        return self.owner[k], self.owner[k + len(key) - 1]

    def seg(self, start_rx, end_rx=None, nlines=None, after=0):
        i = self.find_line(start_rx, after)
        if i is None:
            raise SystemExit(f"[인용 시작 줄 못 찾음] {self.rel}: {start_rx}")
        if end_rx is None and nlines is None:
            j = i
        elif nlines is not None:
            j = i + nlines - 1
        else:
            j = self.find_line(end_rx, i)
            if j is None:
                raise SystemExit(f"[인용 끝 줄 못 찾음] {self.rel}: {end_rx}")
        keep = [k for k in range(i, j + 1)
                if not self.lines[k].startswith("=== p.")
                and not re.match(r"^전자공시시스템 dart\.fss\.or\.kr Page \d+", self.lines[k])
                and self.lines[k].strip() != ""]
        return keep


def _runs(idx):
    """연속한 줄 번호 묶음."""
    out = []
    for i in idx:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def pages_str(pages):
    ps = sorted(set(p for p in pages if p))
    if not ps:
        return "?"
    if len(ps) == 1:
        return f"p.{ps[0]}"
    if ps == list(range(ps[0], ps[-1] + 1)):
        return f"p.{ps[0]}~{ps[-1]}"
    return "p." + ",".join(str(p) for p in ps)


# ───────────────────────── 원문 XML 표 ─────────────────────────
def load_sections(zip_path, rcept):
    info = dp.read_zip(Path(zip_path).read_bytes(), rcept)
    secs, err = dp.parse_document(info["text"])
    return secs, err


def expand(rows):
    """rowspan/colspan 을 펼친 격자와 원래 칸 글(raw) 을 함께 돌려준다."""
    grid, pend = [], {}
    for r in rows:
        out, col, k = [], 0, 0
        while k < len(r) or any(c >= col for c in pend):
            if col in pend:
                rem, txt = pend[col]
                out.append(txt)
                if rem - 1 > 0:
                    pend[col] = (rem - 1, txt)
                else:
                    del pend[col]
                col += 1
                continue
            if k >= len(r):
                break
            c = r[k]
            k += 1
            cs = int(c.get("colspan") or 1)
            rs = int(c.get("rowspan") or 1)
            for _ in range(cs):
                out.append(c["text"])
                if rs > 1:
                    pend[col] = (rs - 1, c["text"])
                col += 1
        grid.append(out)
    return grid


def pick_tables(secs, sec_kw, head_pred):
    out = []
    for s in secs:
        if sec_kw not in s["title"]:
            continue
        for t in s["tables"]:
            if t["rows"] and head_pred([c["text"] for c in t["rows"][0]]):
                out.append(t)
    return out


def raw_rows(t):
    return [[c["text"] for c in r] for r in t["rows"]]


def next_table(secs, t):
    for s in secs:
        if t in s["tables"]:
            i = s["tables"].index(t)
            return s["tables"][i + 1] if i + 1 < len(s["tables"]) else None
    return None


# ───────────────────────── 회사별 설정 ─────────────────────────
CFG = {
    "KB금융지주": dict(
        corp_dart="KB금융",
        biz="20260313001191", biz_corr=["20260324000835", "20260619000667"],
        ann="연차보고서__KB금융지주_지배구조연차보고서_2026.txt",
        ann_add="연차보고서__KB금융지주_지배구조연차보고서_2026_추가공시.txt",
        mgmt="경영공시__KB금융지주.txt",
        exec_ranges=[("기준일", r"^\(1\) 임원 현황", r"^\* 공시서류 작성기준일 이후 임원현황",
                      "(기준일 : 2025년 12월 31일 )", "(1) 임원 현황"),
                     ("이후", r"^\* 공시서류 작성기준일 이후 임원현황", r"^1\) 회사와 계열회사간 임원 겸직 현황",
                      "(기준일 : 2026년 3월 13일 )", "* 공시서류 작성기준일 이후 임원현황")],
        conc_head="대상 계열사",
        conc_ranges=[("기준일", r"^\(기준일 : 2025년 12월 31일\)", r"^\(기준일 : 2026년 03월13일\)",
                      "(기준일 : 2025년 12월 31일)", "1) 회사와 계열회사간 임원 겸직 현황", r"^1\) 회사와 계열회사간 임원 겸직 현황"),
                     ("이후", r"^\(기준일 : 2026년 03월13일\)", r"^\(기준일 : 2026년 03월 13일 \)",
                      "(기준일 : 2026년 03월13일)", "* 공시서류 작성기준일 이후 회사와 계열사간 임원 겸직 현황", r"^1\) 회사와 계열회사간 임원 겸직 현황")],
        conc_copy_sec="계열회사 등에 관한 사항",
        emp_range=(r"^\(4\) 직원 등 현황", r"^\(5\) 육아지원제도 사용 현황"),
        support_ranges=[("감사위원회 지원", r"^바\. 감사위원회 지원조직 현황", 120, "바. 감사위원회 지원조직 현황"),
                        ("준법감시인 지원", r"^\(3\) 준법감시인 등 지원조직 현황", 120, "(3) 준법감시인 등 지원조직 현황")],
        ia_range=(r"^\(1\) 내부회계관리운영조직 인력 및 공인회계사 보유현황", 60,
                  "(1) 내부회계관리운영조직 인력 및 공인회계사 보유현황"),
        unreg_range=(r"^\(7\) 미등기임원 보수 현황", 60),
        quotes={
            "chart_title": ("mgmt", [(r"^나\. 조직도 \(작성기준일", None, None)]),
            "bod_sec_biz": ("biz", [(r"^당사는 사외이사에 대한 업무지원을 활성화하며", r"^회사무국은 사무국장 1명, 팀장 1명, 팀원 3명으로 구성되어 있습니다", None)]),
            "bod_roles_biz": ("biz", [(r"^참고로 이사회사무국의 역할은 다음과 같습니다", r"^3\. 이사회 및 관련 위원회 부의 안건에 대한 실무적 검토", None),
                                      (r"^4\. 사외이사 활동지원 및 정보제공", r"^11\. 기타 사외이사의 역할과 책임을 위해 필요한 지원 업무", None)]),
            "emp_notes": ("biz", [(r"^주1\) 2025\.1\.1부터 2025\.12\.31까지 지급된 급여총액", r"^월별 평균급여액은 해당 월의 급여총액을", None)]),
            # 비평 보정(critic14 gaps): 그룹 전 계열사 인력교류 숫자 — 직원 겸직 칸의 가까운 글
            "emp_exchange": ("biz", [(r"^\(2\) 종업원에 관한 사항", r"^산운용 등 역량강화 부문 71명, 총 163명의 인력이 교류하여 근무중입니다", None)]),
            "unreg_note": ("biz", [(r"^주1\) 인원수 : 원소속회사가 계열사인 미등기임원", None, None)]),
            "other_conc": ("biz", [(r"^2\) 타회사 임원 겸임 현황", r"^- 해당사항 없음", None)]),
            "reorg": ("biz", [(r"^KB금융그룹은 금융의 사회적 역할이 확대되고", r"^.WM.SME부문.을 신설하였습니다", None)]),
            "ia_notes": ("biz", [(r"^※ 2025년 12월 31일 기준 내부회계관리운영조직 관련 사항 기재", r"^.\*1.감사위원회 위원은 이사회 위원이므로", None)]),
            "ann_chart": ("ann", [(r"^\(1\) 조직도 $", None, None),
                                  (r"^※ 상기 위원회 중 감사위원후보추천위원회는 비상설 위원회임", None, 37)]),
            "ann_bod_121": ("ann", [(r"^KB금융지주는 「이사회규정」에서 사외이사에 대한 지원업무를", r"^1명, 팀원 3명으로 총 5명입니다", None)]),
            "ann_succ_132": ("ann", [(r"^최고경영자 승계업무 지원부서는 「경영승계규정」과", r"^팀원 3명으로 총 5명입니다", None)]),
            "ann_audit_157": ("ann", [(r"^감사위원회는 효율적인 감사업무수행을 위하여 감사위원회 보조 기구로 감사부를", r"^감사업무를 원활하게 수행할 수 있는 전문인력 및 적정 인원\(15명\)", None)]),
            "ann_riskcomp_214": ("ann", [(r"^\(3\) 위험관리, 준법감시 부서의 인원현황", r"^\* 2025년 12월말 기준 현재 담당업무 경영진을 제외한 직원 수", None)]),
            "ann_conc_217": ("ann", [(r"^\* 이와 별도로 원소속회사가 자회사인 겸직 경영진 10명", r"^따라 회사간 분담하기로 결의", None)]),
            "ann_comp_208": ("ann", [(r"^\(2\) 준법감시직원 현황", r"^\s*- 해당사항 없음", None)]),
            "ann_gyeom_usage": ("ann", [(r"KB금융지주 보험부문장 \(겸\) KB손해보험 대표이사", None, None)]),
            "mgmt_model": ("mgmt", [(r"^모델검증부서\(지주사 및 은행 겸직\)", r"^조직과 분리하여 독립성을 보장하고 있습니다", None)]),
            "mgmt_audit": ("mgmt", [(r"^신용평가시스템 관련 업무와 직접 이해관계가 없는 지주 및 자회사의 감사부서가", r"^검결과를 지주 감사부에 보고하고", None)]),
        },
        # 지원조직 CSV 에 서술(문장)로 더할 행: (종류, 부서명, 직원수 조각, 직위 조각, 활동 인용 id, 출처 인용 id, 기준일 원문)
        support_quotes=[
            ("사외이사 지원(이사회 지원조직)", "이사회사무국", "사무국장 1명, 팀장 1명, 팀원 3명", "사무국장 1명, 팀장 1명, 팀원 3명", "bod_roles_biz", "bod_sec_biz", "문장에 기준일 글 없음 (사업보고서 기준일 2025년 12월 31일)"),
            ("사외이사 지원(연차보고서)", "이사회사무국", "총 5명", "국장 1명, 팀장 1명, 팀원 3명", "ann_bod_121", "ann_bod_121", "2025년 말 현재"),
            ("최고경영자 승계업무 지원(연차보고서)", "이사회사무국", "총 5명", "사무국장 1명, 팀장 1명, 팀원 3명", "ann_succ_132", "ann_succ_132", "2025년 말 현재"),
            ("감사위원회 보조조직(연차보고서)", "감사부", "적정 인원(15명)", NONE, "ann_audit_157", "ann_audit_157", "문장에 기준일 글 없음"),
            ("위험관리(연차보고서)", "리스크관리부", "19명", NONE, "ann_riskcomp_214", "ann_riskcomp_214", "2025년 12월말 기준"),
            ("준법감시(연차보고서)", "준법추진부", "11명(변호사 4명 포함)", NONE, "ann_riskcomp_214", "ann_riskcomp_214", "2025년 12월말 기준"),
        ],
        # 연차보고서 조직도(글자 층) 의 「부서 (N 명)」 쌍: (부서 줄, 인원 줄)
        ann_chart_pairs=[("감사부", "(15 명)"), ("HR 부", "(14 명)"), ("리스크관리부", "(19 명)"),
                         ("ESG 사업부", "(11 명)"), ("이사회사무국", "(5 명)"), ("준법추진부", "(11 명)")],
        ann_chart_basis="(2025.12.31. 기준)",
        # 조직단위 ↔ 인원 출처 연결: 단위 id → [(출처 종류, 키, 방식)]
        unit_staff={
            "K53": [("support", "감사부", "이름 일치"), ("ann_chart", "감사부", "이름 일치"), ("sq", 3, "이름 일치")],
            "K30": [("support", "준법추진부", "이름 일치"), ("support", "준법추진부(내부통제팀)", "(판단) 표의 「준법추진부(내부통제팀)」 — 괄호 안 팀은 조직도에 나오지 않아 준법추진부에 붙임"),
                    ("support", "준법추진부(법무/송무팀)", "(판단) 표의 「준법추진부(법무/송무팀)」 — 괄호 안 팀은 조직도에 나오지 않아 준법추진부에 붙임"),
                    ("ann_chart", "준법추진부", "이름 일치"), ("sq", 5, "이름 일치")],
            "K54": [("sq", 0, "이름 일치"), ("sq", 1, "이름 일치"), ("sq", 2, "이름 일치"), ("ann_chart", "이사회사무국", "이름 일치")],
            "K37": [("ann_chart", "리스크관리부", "이름 일치"), ("sq", 4, "이름 일치")],
            "K40": [("ann_chart", "HR 부", "(판단) 연차보고서 조직도 글 「HR 부」와 띄어쓰기만 다름")],
            "K09": [("ann_chart", "ESG 사업부", "(판단) 연차보고서 조직도 글 「ESG 사업부」와 띄어쓰기만 다름")],
            "K34": [("ia", "회계처리부서(회계부)", "(판단) 내부회계 표 「회계처리부서(회계부)」 괄호 안 이름이 같음 — 총원은 부서 전체 인원으로 봄")],
            "K45": [("ia", "전산운영부서(IT기획부)", "(판단) 내부회계 표 「전산운영부서(IT기획부)」 괄호 안 이름이 같음 — 총원은 부서 전체 인원으로 봄")],
            "K33": [("ia", "자금운영부서(재무기획부)", "(판단) 내부회계 표 「자금운영부서(재무기획부)」 괄호 안 이름이 같음 — 총원은 부서 전체 인원으로 봄")],
            "K52": [("ia", "감사위원회", "이름 일치 — (판단) 위원 수이지 직원 수 아님")],
            "K51": [("ia", "이사회(*1)", "(판단) 내부회계 표 「이사회(*1)」 — 이사 수이지 직원 수 아님")],
        },
        # 담당업무 글자 그대로 일치가 없을 때의 판단 연결: (표, 성명) → [(단위 id, 근거)]
        manual={
            ("기준일", "양종희"): [("K48", "(판단) 직위 「회장」 — 조직도 「회 장」 상자"), ("K51", "(판단) 사내이사 → 이사회 구성원")],
            ("이후", "양종희"): [("K48", "(판단) 직위 「회장」 — 조직도 「회 장」 상자"), ("K51", "(판단) 사내이사 → 이사회 구성원")],
            ("기준일", "이재근"): [("K19", "(판단) 담당업무 「글로벌사업부문장」 — 2026.3.13 표에서 같은 사람이 「글로벌부문장」")],
            ("기준일", "이창권"): [("", "(판단) 대응 단위 없음 — 담당업무 「디지털부문장(CDO),IT부문장(CITO)」의 「디지털부문」「IT부문」이 2026.8 조직도에 나오지 않음(2026.3.13 표에서 같은 사람은 「미래전략부문장」)")],
            ("기준일", "권봉중"): [("", "(판단) 대응 단위 없음 — 「IR본부」가 2026.8 조직도에 나오지 않음(「IR부」는 재무담당 아래, 이름 다름). 2026.1.1 퇴임(작성기준일 이후 변동 표)")],
            ("기준일", "박효익"): [("K25", "(판단) 「보험사업담당」 — 조직도 「보험담당」과 이름 다름. 2026.1.1 퇴임, 2026.3.13 표의 윤희승이 「보험담당」")],
            ("기준일", "차대현"): [("K53", "(판단) 「감사담당」 — 조직도에 「감사담당」 없음; 감사위원회 지원조직 표 「감사부 … 감사담당임원(2년)」에 따라 감사부에 붙임")],
            ("기준일", "조영서"): [("K12", "(판단) 「AIㆍ디지털본부장」 — 조직도 「AI·DT추진본부」와 이름 다름; 겸직 표에 국민은행 「AIㆍDT추진그룹대표 부행장」. 확정 못 함")],
        },
        board_member_unit="K51",
        audit_committee_unit="K52",
        audit_member_rx=r"감사위원",
        upside_down=("(판단) 조직도를 위아래 거꾸로 그린 꼴로 봄 — md·판독대조 K48",
                     ["K03", "K19", "K21", "K23", "K25", "K27", "K29", "K32", "K36", "K39", "K42", "K44", "K48"], ("회 장", "이사회")),
        chart_search_note="(판단) 두 줄 모두 4407행 「리브똑똑」 아래 메신저 서비스 설명(「기업사내메신저」)이라 지주 조직도가 아님 — 지주 조직도 글은 사업보고서 텍스트에 나오지 않음",
    ),
    "신한금융지주": dict(
        corp_dart="신한지주",
        biz="20260318000826", biz_corr=[],
        ann="연차보고서__신한금융지주_지배구조연차보고서_2026.txt",
        ann_add="연차보고서__신한금융지주_지배구조연차보고서_2026_추가공시.txt",
        mgmt="경영공시__신한금융지주.txt",
        exec_ranges=[("기준일", r"^가\. 임원 현황", r"^\(기준일 : 2026년 3월 18일 \)",
                      "(기준일 : 2025년 12월 31일 )", "가. 임원 현황"),
                     ("이후", r"^\(기준일 : 2026년 3월 18일 \)", r"^\(기준일 : 2025년 12월 31일 \)$",
                      "(기준일 : 2026년 3월 18일 )", "※ 공시서류 작성기준일 이후 임원현황")],
        conc_head="대상회사",
        conc_ranges=[("기준일", r"^\(기준일 : 2025년 12월 31일 \)$", r"^\(기준일 : 2026년 3월 18일 \)$",
                      "(기준일 : 2025년 12월 31일 )", "(2) 계열회사간 임원 겸직현황", r"^\(2\) 계열회사간 임원 겸직현황"),
                     ("이후", r"^\(기준일 : 2026년 3월 18일 \)$", r"^\s*\(기준일 : 2026년 03월 18일 \)",
                      "(기준일 : 2026년 3월 18일 )", "※ 공시서류 작성기준일 이후 계열회사간 임원 겸직 현황", r"^\(2\) 계열회사간 임원 겸직현황")],
        conc_copy_sec="계열회사 등에 관한 사항",
        emp_range=(r"^나\. 직원 등 현황", r"^\(단위 : 명,%\)"),
        support_ranges=[("감사위원회 지원", r"^\(6\) 감사위원회 지원조직 현황", 60, "(6) 감사위원회 지원조직 현황"),
                        ("준법감시인 지원", r"^\(3\) 준법지원인 등 지원조직 현황", 120, "(3) 준법지원인 등 지원조직 현황")],
        ia_range=(r"^가\. 내부회계관리ㆍ운영조직 인력 및 공인회계사 보유현황", 140,
                  "가. 내부회계관리ㆍ운영조직 인력 및 공인회계사 보유현황"),
        unreg_range=(r"^마\. 미등기임원 보수 현황", 40),
        quotes={
            "chart_title": ("mgmt", [(r"^나\. 조직도 \(신한금융지주회사\)", None, None)]),
            "bod_sec_biz": ("biz", [(r"^당사는 이사회 및 이사회 내의 위원회의 원활한 활동을 보좌하고", r"^.을 운영 중에 있습니다", None)]),
            "bod_roles_biz": ("biz", [(r"^이사회사무국은 다음 각호의 업무를 수행하고 있으며", r"^\s*9\) 기타 이사회 등의 지시사항 처리", None)]),
            "emp_notes": ("biz", [(r"^주1\) 연간급여 총액은 2025년 1월 1일부터", r"^\(월별 평균 급여액 : 해당 월의 급여총액을", None)]),
            "unreg_note": ("biz", [(r"^주\) 겸직 경영진의 경우, 소득세법 제20조에 따라", None, None)]),
            "org_773": ("biz", [(r"^확대하고 있습니다\. 2026년 신한금융지주회사는", r"^를 확대하기 위해 노력하고 있습니다", None)]),
            "ia_notes": ("biz", [(r"^주1\) 감사위원회 4인 포함", r"^주4\) 내부회계담당인력의 평균경력월수는", None)]),
            "ann_chart": ("ann", [(r"^\(1\) 조직도 \(2026\.1월초 조직개편 반영 기준\)", None, None),
                                  (r"^이사회사무국$", None, 45)]),
            "ann_bod_90": ("ann", [(r"^\(가\) 사외이사 지원부서 설치현황", r"^\s*- 인원구성 : 사무국장 1명\(총괄\), 팀원 2명", None)]),
            "ann_bod_129": ("ann", [(r"^당사는 사외이사 관련 업무를 담당하고, 사외이사의 역할과 책임 수행을 위해", r"^있습니다\.\s*$", None)]),
            "ann_cmte_129": ("ann", [(r"^또한 일부 이사회내위원회는 유관 업무를 담당하는 회사 내 부서에서 지원하고", r"^회장후보추천위원회, 자회사최고경영자후보추천위원회\) 입니다", None)]),
            # 비평 보정(critic14 gaps): p.137 「팀장과 팀원 10명」 문장
            "ann_succ_137": ("ann", [(r"^사\. 대표이사 회장 승계업무 지원부서 운영 현황\s*$", r"^대표이사 후보자 선발 및 자격요건 충족 여부 등을 검증한 결과를", None)]),
            "ann_succ_138": ("ann", [(r"^\s*<대표이사 회장 승계업무 지원부서 운영 현황>", r"^\s*② 회추위사무국 \(직원수 총 6명", None)]),
            "ann_audit_157": ("ann", [(r"^감사위원회는 보조조직인 감사팀을 직접 지휘하여", r"^구성되어 있으며, 자회사별 담당자를 지정하여", None)]),
            "ann_succ_185": ("ann", [(r"^\(4\) 자회사 대표이사 승계업무 지원부서 현황", r"^\s*- 직원수 : 총 10명", None)]),
            "ann_emp_200": ("ann", [(r"^전직원$", r"^\(252명\) 해당사항 없음", None)]),
            "ann_comp_201": ("ann", [(r"^\(2\) 준법감시직원 현황 및 비율", r"^라\. 가부터 다까지에 해당하지 않는 직원 중", None)]),
            "ann_conc_33": ("ann", [(r"^정상혁 이사는 신한은행 은행장을 겸직하고 있으며", None, None)]),
            "ann_ax_21": ("ann", [(r"^첫째, AX•DX 실행력 강화입니다", None, None)]),
            "mgmt_risk": ("mgmt", [(r"^지주회사 리스크관리팀 주관으로 비소매 신용평가모형을 개발하고", r"^총괄팀/모형공학팀, 제주은행 리스크총괄파트\)와 함께", None)]),
            "mgmt_model": ("mgmt", [(r"^2\) 적합성 검증", r"^한은행 및 제주은행 각사의 모형에 대해 적합성 검증", None)]),
            "mgmt_audit": ("mgmt", [(r"^지주회사 감사팀이 지주회사와 신한카드, 제주은행 모형에 대한", r"^은행 감사부에서 별도 점검", None)]),
            "mgmt_model2": ("mgmt", [(r"^지주회사 모형검증팀은 연 1회 이상 정기적으로", r"^\(Validation\)을 실시하고 적합성 검증 결과는", None)]),
        },
        support_quotes=[
            ("사외이사 지원(이사회 지원조직)", "이사회사무국", "사무국장과 2명의 책임자급 직원", "사무국장과 2명의 책임자급 직원", "bod_roles_biz", "bod_sec_biz", "문장에 기준일 글 없음 (사업보고서 기준일 2025년 12월 31일)"),
            ("사외이사 지원(연차보고서)", "이사회사무국", "사무국장 1명(총괄), 팀원 2명", "사무국장 1명(총괄), 팀원 2명", "ann_bod_90", "ann_bod_90", "문장에 기준일 글 없음"),
            ("사외이사 지원(연차보고서)", "이사회사무국", "책임자급 직원 2명", "이사회사무국장의 관할 하에 책임자급 직원 2명", "ann_bod_129", "ann_bod_129", "문장에 기준일 글 없음"),
            ("대표이사 회장 승계업무 지원(연차보고서)", "신한리더십센터", "직원수 총 10명", NONE, "ann_succ_138", "ann_succ_138", "문장에 기준일 글 없음"),
            ("대표이사 회장 승계업무 지원(연차보고서)", "회추위사무국", "직원수 총 6명 – 이사회사무국 1명, 전략기획팀 1명, 홍보팀 1명, 신한리더십센터 3명", NONE, "ann_succ_138", "ann_succ_138", "문장에 기준일 글 없음"),
            ("감사위원회 보조조직(연차보고서)", "감사팀", NONE, "팀장 1명, 공인회계사(CPA) 2명, 실무 경력이 풍부한 책임자 이상의 직원으로", "ann_audit_157", "ann_audit_157", "문장에 기준일 글 없음"),
            ("자회사 대표이사 승계업무 지원(연차보고서)", "신한리더십센터", "총 10명", "팀장과 팀원 총 10명", "ann_succ_185", "ann_succ_185", "문장에 기준일 글 없음"),
            ("준법감시(연차보고서 준법감시직원 현황)", "추출 범위에 없음(표에 부서명 칸이 없음) — (판단) 준법감시인 산하 인력: 원문 「* 준법감시인 산하 인력 중 아래 인력은 미합산」", "준법감시직원 수 10 준법감시인 제외", NONE, "ann_comp_201", "ann_comp_201", "2025년말 기준 / 준법감시인 제외"),
            ("대표이사 회장 승계업무 지원(연차보고서)", "신한리더십센터", "팀장과 팀원 10명", "팀장과 팀원 10명", "ann_succ_137", "ann_succ_137", "문장에 기준일 글 없음"),
        ],
        ann_chart_pairs=[("이사회사무국", "(3명)"), ("리스크관리팀", "(14명)"), ("SDGs기획팀", "(6명)"),
                         ("전략기획팀", "(16명)"), ("감사팀", "(10명)"), ("신한리더십센터", "(10명)"), ("준법지원획팀", "(10명)")],
        ann_chart_basis="(1) 조직도 (2026.1월초 조직개편 반영 기준)",
        unit_staff={
            "S13": [("support", "감사팀", "이름 일치"), ("ann_chart", "감사팀", "이름 일치"), ("sq", 5, "이름 일치")],
            "S17": [("support", "준법지원팀", "이름 일치"), ("ann_chart", "준법지원획팀", "(판단) 연차보고서 조직도 글 「준법지원획팀」 — 같은 이름 단위가 조직도에 없고 내부통제위원회 옆 자리라 준법지원팀의 오기로 봄")],
            "S16": [("sq", 7, "(판단) 준법감시직원 = 준법감시인(준법지원파트장) 산하 인력으로 봄")],
            "S03": [("sq", 0, "이름 일치"), ("sq", 1, "이름 일치"), ("sq", 2, "이름 일치"), ("ann_chart", "이사회사무국", "이름 일치")],
            "S48": [("ann_chart", "리스크관리팀", "이름 일치")],
            "S40": [("ann_chart", "SDGs기획팀", "이름 일치")],
            "S24": [("ann_chart", "전략기획팀", "이름 일치")],
            "S38": [("ann_chart", "신한리더십센터", "이름 일치"), ("sq", 3, "이름 일치"), ("sq", 6, "이름 일치"),
                    ("sq", 8, "이름 일치 — (판단) 「팀장과 팀원 10명」은 총 10명 또는 팀장 1명+팀원 10명으로 읽힘")],
            "S30": [("ia", "회계파트", "(판단) 내부회계 표 「회계파트」 — 조직도 「회계 파트」와 띄어쓰기만 다름")],
            "S05": [("ia", "감사위원회주2)", "이름 일치 — (판단) 위원 수이지 직원 수 아님")],
            "S02": [("ia", "이사회 주1), 주3)", "(판단) 내부회계 표 「이사회」 — 이사 수이지 직원 수 아님")],
        },
        manual={
            ("기준일", "진옥동"): [("S14", "(판단) 직위 「대표이사회장」 — 조직도 「대표이사 회장」과 띄어쓰기만 다름"), ("S02", "(판단) 사내이사 → 이사회 구성원")],
            ("이후", "진옥동"): [("S14", "(판단) 직위 「대표이사회장」 — 조직도 「대표이사 회장」과 띄어쓰기만 다름"), ("S02", "(판단) 사내이사 → 이사회 구성원")],
        },
        board_member_unit="S02",
        audit_committee_unit=None,
        audit_member_rx=None,
        chart_search_note="「IX. 계열회사 등에 관한 사항」 아래 절 제목 — 이 줄 뒤(같은 쪽)에는 계열회사 수 표 글(「기업집단의 명칭」「계열회사의 수」)만 나오고 지주 안 부서 이름 글은 나오지 않음 (판단: 계열회사 조직도 절이고, 그림이라 텍스트에 글이 나오지 않는 것으로 봄) — 지주 안 조직도 글은 사업보고서 텍스트에 나오지 않음",
    ),
}

QTITLE = {
    "ann_bod_121": "연차보고서 — 사외이사 지원 부서의 인원", "ann_succ_132": "연차보고서 — 최고경영자 승계업무 지원부서 인원",
    "ann_audit_157": "연차보고서 — 감사보조조직(감사부) 인원", "ann_riskcomp_214": "연차보고서 — 위험관리·준법감시 부서의 인원현황",
    "ann_conc_217": "연차보고서 — 원소속회사가 자회사인 겸직 경영진", "ann_comp_208": "연차보고서 — 준법감시직원 현황",
    "ann_gyeom_usage": "연차보고서 — 「(겸)」 쓰임(경력 글)", "ann_bod_90": "연차보고서 — 사외이사 지원부서 설치현황",
    "ann_bod_129": "연차보고서 — 사외이사 지원부서 활동(인원)", "ann_cmte_129": "연차보고서 — 이사회내위원회별 지원 부서",
    "ann_succ_138": "연차보고서 — 대표이사 회장 승계업무 지원부서", "ann_audit_157_sh": "연차보고서 — 감사팀 구성",
    "ann_succ_185": "연차보고서 — 자회사 대표이사 승계업무 지원부서", "ann_emp_200": "연차보고서 — 장기근무직원 현황 표의 전직원 수",
    "ann_comp_201": "연차보고서 — 준법감시직원 현황 및 비율", "ann_conc_33": "연차보고서 — 기타비상무이사 겸직 서술",
    "ann_ax_21": "연차보고서 — AX•디지털부문 출범", "mgmt_risk": "경영공시 — 지주회사 리스크관리팀(신용평가모형)",
    "mgmt_model": "경영공시 — 모형 검증 부서의 겸직", "mgmt_audit": "경영공시 — 지주 감사 부서(제3자 점검)",
    "mgmt_model2": "경영공시 — 모형검증팀 사후검증",
    "ann_succ_137": "연차보고서 — 대표이사 회장 승계업무 지원부서 운영 현황(신한리더십센터 구성)",
}
# 인용 뒤에 붙이는 판단 글(비평 보정)
QNOTE = {
    "ann_succ_137": "- (판단) 「팀장과 팀원 10명」은 총 10명 또는 팀장 1명+팀원 10명으로 읽힘 — 같은 보고서 p.185 자회사 승계 지원부서 글은 「팀장과 팀원 총 10명」, p.138 표는 「직원수 총 10명」, 조직도 글은 「(10명)」.",
}

DOCNAME = {"biz": "사업보고서 (2025.12)", "ann": "지배구조 및 보수체계 연차보고서(2026 공시, 본공시)",
           "ann_add": "지배구조 및 보수체계 연차보고서(2026 공시, 추가공시)", "mgmt": "경영공시 2026 2Q"}


# ───────────────────────── 메타 ─────────────────────────
def load_meta(company, cfg):
    m = {}
    for r in read_csv(ROOT / "dart_out/risk8/경영공시_2026_2Q.csv"):
        if r["corp_label"] == company:
            m["mgmt"] = dict(title=r["제목"], date=r["게시일"], url=r["url"], sha=r["sha256"], fetched=kst(r["fetched_at"]))
    for r in read_csv(ROOT / "dart_out/risk8/연차보고서_FY2025.csv"):
        if r["지주명"] == company:
            k = "ann" if r["공시유형"] == "본공시" else "ann_add"
            m[k] = dict(title=r["제목"], date=r["공시일"], url=r["url"], sha=r["sha256"], fetched=kst(r["fetched_at"]))
    m["biz_all"] = {}
    for r in read_csv(ROOT / "dart_out/risk8/DART_문서목록.csv"):
        if r["corp_label"] == company and r["doc_kind"] == "사업보고서":
            m["biz_all"][r["rcept_no"]] = dict(title=r["report_nm"], date=r["rcept_dt"], zip_sha=r["document_sha256"],
                                                status=r["document_status"], fetched=kst(r["document_at"]),
                                                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r['rcept_no']}")
    for r in read_csv(ROOT / "dart_out/risk8/텍스트목록.csv"):
        if r["corp_label"] == company and r["doc_kind"] == "사업보고서":
            rc = r["doc_id"].split("__")[-1]
            if rc in m["biz_all"]:
                m["biz_all"][rc].update(pdf_sha=r["원본sha256"], pages=r["쪽수"], txt=r["텍스트"])
    m["biz"] = m["biz_all"][cfg["biz"]]
    return m


def src(meta, key, pages, extra=""):
    if key == "biz":
        b = meta["biz"]
        s = f"[사업보고서 (2025.12) · {CFG_CUR['biz']} · {pages} · 수집 {b['fetched'][:10]}"
    else:
        d = meta[key]
        s = f"[{DOCNAME[key]} · {d['url']} · {pages} · 수집 {d['fetched'][:10]}"
    return s + (f" · {extra}" if extra else "") + "]"


# ───────────────────────── 회사 하나 처리 ─────────────────────────
def run_company(company, cfg):
    global CFG_CUR
    CFG_CUR = cfg
    meta = load_meta(company, cfg)
    VR = load_vr(company)
    readA = json.loads((OUT_DIR / f"{company}_판독A.json").read_text(encoding="utf-8"))
    unitsA = readA["units"]  # 판독 A 그대로(판독대조 CSV 판독A 칸)
    # 판독 확정 값(판독대조 「확정」 칸 — 검증 반영 입력) 을 단위 칸에 씀
    conf = {r[0]: r[2] for r in VR["판독대조"]}

    def unval(v):
        return "" if v.startswith("(없음") else v

    FLD = {"단위 이름": "단위", "상위단위": "상위단위", "층위": "층위", "겸직표시": "겸직표시"}
    units = []
    for u in unitsA:
        v = dict(u)
        for lab, k in FLD.items():
            c = conf.get(f"{u['id']} {lab}")
            if c is not None:
                v[k] = unval(c)
        ov = VR["단위_고침"].get(u["id"], {})
        if "md_비고" in ov:
            v["md_비고"] = ov["md_비고"]
        if "csv_비고" in ov:
            v["csv_비고"] = ov["csv_비고"]
        units.append(v)
    # 비평 보정: 거꾸로 그린 조직도 해석에 기댄 상위단위 행의 비고에 (판단) 표시
    upside = []
    if cfg.get("upside_down"):
        note, ids, parents = cfg["upside_down"]
        for v in units:
            if v["id"] in ids:
                if v["상위단위"] not in parents:
                    raise SystemExit(f"[거꾸로 조직도 비고] {v['id']} 상위단위 「{v['상위단위']}」 가 예상과 다름")
                for k in ("비고", "md_비고", "csv_비고"):
                    if k in v or k == "비고":
                        v[k] = "; ".join(x for x in [v.get(k, ""), note] if x)
                upside.append(v["id"])
        if len(upside) != len(ids):
            raise SystemExit(f"[거꾸로 조직도 비고] 단위 수 {len(upside)} ↔ {len(ids)}")
    uid = {u["id"]: u for u in units}
    checks = {"company": company, "problems": [], "notes": []}

    docs = {
        "biz": Text(TXT / f"사업보고서__{company}__{cfg['biz']}.txt"),
        "ann": Text(TXT / cfg["ann"]),
        "ann_add": Text(TXT / cfg["ann_add"]),
        "mgmt": Text(TXT / cfg["mgmt"]),
    }
    biz = docs["biz"]
    # 비평 보정: 사업보고서 텍스트의 「조직도」 검색 기록(COMMON 21행)
    chart_hits = [(i + 1, biz.page[i], biz.lines[i].strip()) for i, l in enumerate(biz.lines) if "조직도" in l]
    # 보정 표의 「전」 글이 원문 텍스트에 나오지 않는지(원문 글을 바꾸지 않게)
    for old, _, _ in FIX_EOPSEUM:
        for dk, t in docs.items():
            if nz(old) in t.norm:
                checks["problems"].append(f"보정 표 「{old}」 가 원문 텍스트 {t.rel} 에 나옴 — 원문을 바꿀 수 있음")
    for old in [x[0] for x in FIX2] + [x[0] for x in RB2_MARK]:
        for dk, t in docs.items():
            if nz(old) in t.norm:
                checks["problems"].append(f"보정 표 2 「{old}」 가 원문 텍스트 {t.rel} 에 나옴 — 원문을 바꿀 수 있음")

    # ── 인용(서술) ──
    Q = {}
    for qid, (dk, segs) in cfg["quotes"].items():
        t = docs[dk]
        lines, after, segtexts = [], 0, []
        for (a, b, n) in segs:
            ks = t.seg(a, b, n, after)
            after = ks[-1] + 1
            lines += ks
            segtexts.append("\n".join(t.lines[k].strip() for k in ks))
        text = "\n".join(t.lines[k].strip() for k in lines)
        Q[qid] = dict(doc=dk, text=text, pages=pages_str([t.page[k] for k in lines]), segs=segtexts,
                      lines=",".join(f"{a + 1}~{b + 1}" for a, b in _runs(lines)), src=None)
        Q[qid]["src"] = src(meta, dk, Q[qid]["pages"], f"{t.rel} {Q[qid]['lines']}행")
    # 연차보고서 인용이 추가공시에도 같은지
    for qid, q in Q.items():
        if q["doc"] == "ann":
            same = all(nz(x) in docs["ann_add"].norm for x in q["segs"])
            q["ann_add_same"] = "같음" if same else "다름/없음"
            if not same:
                checks["problems"].append(f"연차보고서 인용 {qid} 가 추가공시 텍스트에 공백 무시로 그대로 나오지 않음")

    # ── 원문 XML ──
    secs, perr = load_sections(ROOT / "dart_out/raw/document" / f"{cfg['biz']}.zip", cfg["biz"])
    checks["xml_parse"] = perr or "ok"

    def is_exec(h):
        return h and h[0] == "성명" and "담당업무" in "".join(h)

    def is_conc(h):
        return any(cfg["conc_head"] == x.replace(" ", "").replace("대상계열사", "대상 계열사") or cfg["conc_head"] in x for x in h)

    exec_tabs = pick_tables(secs, "임원 및 직원 등의 현황", is_exec)
    conc_tabs = pick_tables(secs, "임원 및 직원 등의 현황", is_conc)
    conc_copy = pick_tables(secs, cfg["conc_copy_sec"], is_conc)
    emp_tab = pick_tables(secs, "임원 및 직원 등의 현황", lambda h: h[:1] == ["직원"])[0]
    sup_tabs = pick_tables(secs, "감사제도에 관한 사항", lambda h: h[:1] == ["부서(팀)명"])
    ia_tab = pick_tables(secs, "내부통제에 관한 사항", lambda h: h[:1] and h[0].startswith("소속기관"))[0]
    unreg_tab = pick_tables(secs, "임원 및 직원 등의 현황", lambda h: h[:2] == ["구 분", "인원수"])[0]
    assert len(exec_tabs) == 2 and len(conc_tabs) == 2 and len(sup_tabs) == 2, (len(exec_tabs), len(conc_tabs), len(sup_tabs))

    def locate_rows(keys, lo, hi, label):
        """keys 를 차례로(앞 행 다음부터) 공백 무시로 찾는다. 범위에 없으면 문서 전체에서 찾고 표시."""
        out, cur = [], lo
        for key in keys:
            hit = biz.find_norm(key, cur, hi)
            how = "범위 안"
            if hit is None:
                hit = biz.find_norm(key, lo, hi)
                how = "범위 안(순서 어긋남)"
            if hit is None:
                hit = biz.find_norm(key, 0, None)
                how = "범위 밖(문서 전체)"
                checks["problems"].append(f"{label}: '{key[:30]}' 가 정한 범위 밖에서 찾아짐" if hit else f"{label}: '{key[:30]}' PDF 텍스트에 없음")
            if hit:
                cur = hit[1] + 1
                out.append((biz.page[hit[0]], hit[0], how))
            else:
                out.append((None, None, "없음"))
        return out

    # 임원 표
    execs = {}
    for (tag, a, b, basis, title), t in zip(cfg["exec_ranges"], exec_tabs):
        lo = biz.find_line(a)
        hi = biz.find_line(b, lo + 1)
        rows = [r for r in raw_rows(t) if len(r) >= 12 and r[0] not in ("성명",)]
        rows = [r for r in rows if r[0] and r[0] != "의결권있는 주식"]
        keys = ["".join(r[:6]) for r in rows]
        locs = locate_rows(keys, lo, hi, f"임원 표({tag})")
        lst = []
        for r, (pg, ln, how) in zip(rows, locs):
            # 담당업무가 같은 쪽(또는 다음 쪽) PDF 텍스트에 공백 무시로 나오는지
            ok = "?"
            if ln is not None:
                hit = biz.find_norm(r[6], ln, ln + 80) if r[6] else (ln, ln)
                ok = "같음(공백 무시)" if hit else "PDF 텍스트에서 못 찾음"
                if not hit:
                    checks["problems"].append(f"임원 표({tag}) {r[0]} 담당업무 PDF 대조 실패")
            lst.append(dict(성명=r[0], 성별=r[1], 출생=r[2], 직위=r[3], 등기=r[4], 상근=r[5], 담당업무=r[6],
                            쪽=pg, 줄=(ln + 1 if ln is not None else None), 대조=ok, 찾은곳=how))
        execs[tag] = dict(rows=lst, basis=basis, title=title, hdr=raw_rows(t)[0])

    # 임원 겸직 표
    concs = {}
    for (tag, a, b, basis, title, anchor), t in zip(cfg["conc_ranges"], conc_tabs):
        anc = biz.find_line(anchor)
        lo = biz.find_line(a, anc)
        hi = biz.find_line(b, lo + 1)
        if hi is None or tag == "이후":
            hi = (hi or lo) + 40 if tag == "이후" else hi
        raw = raw_rows(t)[1:]
        grid = expand(t["rows"])[1:]
        keys = ["".join(r) for r in raw]
        locs = locate_rows(keys, lo, hi, f"겸직 표({tag})")
        lst = []
        for r, g, (pg, ln, how) in zip(raw, grid, locs):
            lst.append(dict(성명=g[0], 회사=g[1], 직위=g[2], 선임=g[3], 상근=g[4], 이름칸합침=(len(r) < len(g)),
                            쪽=pg, 줄=(ln + 1 if ln is not None else None), 찾은곳=how, raw=" | ".join(r)))
        concs[tag] = dict(rows=lst, basis=basis, title=title)
    # 겸직 표 사본(IX 장) 대조
    copy_diffs = []
    for (tag, *_), t, c in zip(cfg["conc_ranges"], conc_tabs, conc_copy):
        A, B = raw_rows(t), raw_rows(c)
        for i, (x, y) in enumerate(zip(A, B)):
            if x != y:
                copy_diffs.append(f"{tag} 표 {i}행: VIII장 「{' | '.join(x)}」 ↔ IX장 「{' | '.join(y)}」")
        if len(A) != len(B):
            copy_diffs.append(f"{tag} 표 행 수 다름: VIII장 {len(A)} ↔ IX장 {len(B)}")
    checks["겸직표_사본대조"] = copy_diffs or ["같음"]

    # 직원 표
    emp_raw = raw_rows(emp_tab)
    total = [r for r in emp_raw if r and r[0].replace(" ", "") == "합계"][0]
    lo = biz.find_line(cfg["emp_range"][0])
    hit = biz.find_norm("".join(total[:6]), lo, None)
    emp = dict(합계행=" | ".join(total), 쪽=biz.page[hit[0]] if hit else None,
               기준일=biz.lines[biz.find_line(r"^\(기준일 : 2025년 12월 31일 \) \(단위 : 백만원\)", lo)].strip(),
               rows=[" | ".join(r) for r in emp_raw[4:]], head=[" | ".join(r) for r in emp_raw[:4]])
    # 미등기임원 보수 표
    unreg = [" | ".join(r) for r in raw_rows(unreg_tab)]

    # 지원조직 표
    supports = []
    for (kind, a, n, title), t in zip(cfg["support_ranges"], sup_tabs):
        lo = biz.find_line(a)
        rows = raw_rows(t)[1:]
        keys = [r[0] + r[1] for r in rows]
        locs = locate_rows(keys, lo, lo + n, f"지원조직 표({kind})")
        nt = next_table(secs, t)
        note = ""
        if nt and nt["rows"] and nt["rows"][0] and nt["rows"][0][0]["text"].startswith("주"):
            note = " ".join(c["text"] for c in nt["rows"][0])
            if not biz.find_norm(note, lo, lo + n):
                checks["problems"].append(f"지원조직 표 주석 PDF 대조 실패: {note[:30]}")
        for r, (pg, ln, how) in zip(rows, locs):
            # 활동·직위 칸이 PDF 텍스트에 나오는지
            ok = all(biz.find_norm(x, lo, lo + n) for x in r if x)
            supports.append(dict(kind=kind, title=title, dept=r[0], n=r[1], pos=r[2], act=r[3], note=note,
                                 쪽=pg, 대조="같음(공백 무시)" if ok else "일부 칸 PDF 텍스트에서 못 찾음"))
            if not ok:
                checks["problems"].append(f"지원조직 {r[0]} 칸 대조 실패")

    # 내부회계 인력 표
    a, n, ia_title = cfg["ia_range"]
    lo = biz.find_line(a)
    ia_raw = raw_rows(ia_tab)
    ia_rows = [r for r in ia_raw[2:] if len(r) >= 6]
    locs = locate_rows([r[0] + "".join(r[1:3]) for r in ia_rows], lo, lo + n, "내부회계 인력 표")
    ia = []
    for r, (pg, ln, how) in zip(ia_rows, locs):
        ia.append(dict(dept=r[0], 총원=r[1], 담당=r[2], cpa=r[3], 비율=r[4], 경력=r[5], 쪽=pg, head=" | ".join(ia_raw[0]) + " ‖ " + " | ".join(ia_raw[1])))

    # 연차보고서 조직도(글자 층) 쌍
    ann = docs["ann"]
    qa = Q["ann_chart"]
    a_lo = ann.find_line(cfg["quotes"]["ann_chart"][1][1][0])
    chart_pairs = {}
    for name, cnt in cfg["ann_chart_pairs"]:
        i = None
        for k in range(a_lo, a_lo + 60):
            if ann.lines[k].strip() == name and ann.lines[k + 1].strip() == cnt:
                i = k
                break
        if i is None:
            checks["problems"].append(f"연차보고서 조직도 글 쌍 못 찾음: {name} {cnt}")
            continue
        chart_pairs[name] = dict(text=f"{ann.lines[i].strip()}\n{ann.lines[i + 1].strip()}", page=ann.page[i], line=i + 1,
                                 same_add=nz(ann.lines[i] + ann.lines[i + 1]) in docs["ann_add"].norm)

    # 서술 지원조직 행
    sq_rows = []
    for (kind, dept, ncount, pos, act_q, src_q, basis) in cfg["support_quotes"]:
        for frag in (ncount, pos):
            if frag != NONE and nz(frag) not in nz(Q[src_q]["text"]):
                checks["problems"].append(f"서술 조각이 인용에 없음: {frag}")
        # ① 꼴: 문장에 인원·직위 글이 나오지 않는 칸은 찾은 범위를 붙임(비평 보정)
        where = f"출처 칸 문장({Q[src_q]['pages']})"
        n_out = ncount if ncount != NONE else none_in(where, "총 인원 숫자가 나오지 않음")
        pos_out = pos if pos != NONE else none_in(where, "직위 글이 나오지 않음")
        sq_rows.append(dict(kind=kind, dept=dept, n=n_out, pos=pos_out, act=Q[act_q]["text"], basis=basis,
                            src=Q[src_q]["src"], act_src=Q[act_q]["src"], pos_raw=pos))

    # ── 정정판 대조 ──
    corr = []
    for rc in cfg["biz_corr"]:
        info = meta["biz_all"].get(rc, {})
        zp = ROOT / "dart_out/raw/document" / f"{rc}.zip"
        tp = TXT / f"사업보고서__{company}__{rc}.txt"
        res = dict(rcept=rc, title=info.get("title", ""), date=info.get("date", ""))
        try:
            s2, _ = load_sections(zp, rc)
            e2 = pick_tables(s2, "임원 및 직원 등의 현황", is_exec)
            c2 = pick_tables(s2, "임원 및 직원 등의 현황", is_conc)
            em2 = pick_tables(s2, "임원 및 직원 등의 현황", lambda h: h[:1] == ["직원"])
            su2 = pick_tables(s2, "감사제도에 관한 사항", lambda h: h[:1] == ["부서(팀)명"])
            ia2 = pick_tables(s2, "내부통제에 관한 사항", lambda h: h[:1] and h[0].startswith("소속기관"))
            same = ([raw_rows(x) for x in e2] == [raw_rows(x) for x in exec_tabs]
                    and [raw_rows(x) for x in c2] == [raw_rows(x) for x in conc_tabs]
                    and raw_rows(em2[0]) == emp_raw and [raw_rows(x) for x in su2] == [raw_rows(x) for x in sup_tabs]
                    and raw_rows(ia2[0]) == ia_raw)
            res["방법"] = "원문 XML 표 칸 글 비교(임원 2·겸직 2·직원·지원조직 2·내부회계)"
            res["결과"] = "같음" if same else "다름"
        except Exception as ex:  # zip 없음 등
            t2 = Text(tp)
            keys = ["".join(r[:6]) for tag in execs for r in [[x["성명"], x["성별"], x["출생"], x["직위"], x["등기"], x["상근"]] for x in execs[tag]["rows"]]]
            keys += ["".join(r) for t in conc_tabs for r in raw_rows(t)[1:]]
            keys += [s["dept"] + s["n"] for s in supports] + ["".join(total[:6])]
            miss = [k for k in keys if nz(k) not in t2.norm]
            res["방법"] = f"원문 XML 없음({type(ex).__name__}) → PDF 텍스트에서 표 행 {len(keys)}개 공백 무시 대조"
            res["결과"] = "같음(모든 행 나옴)" if not miss else f"없는 행 {len(miss)}개: {miss[:5]}"
        corr.append(res)
    checks["정정판대조"] = corr

    # ── 임원 ↔ 조직 단위 대응 ──
    def match_exec(tag, e):
        out = []
        duty = e["담당업무"]
        for u in units:
            nm = u["단위"]
            if u["층위"].startswith("도식"):
                continue
            if nm in duty:
                out.append((u["id"], "이름 일치", f"담당업무에 「{nm}」 글자 그대로"))
            elif len(nz(nm)) >= 4 and nzd(nm) in nzd(duty) and nm not in ("회 장", "대표이사 회장"):
                out.append((u["id"], "(판단)", f"(판단) 담당업무 「{duty}」 — 조직도 「{nm}」와 띄어쓰기·가운뎃점·「그룹」 붙임만 다름"))
        for (uid_, why) in cfg["manual"].get((tag, e["성명"]), []):
            out.append((uid_, "(판단)", why))
        if e["등기"] in ("사외이사", "기타비상무이사") and not any(x[0] == cfg["board_member_unit"] for x in out):
            out.append((cfg["board_member_unit"], "(판단)", f"(판단) 등기임원({e['등기']}) → 이사회 구성원"))
        if cfg["audit_member_rx"] and re.search(cfg["audit_member_rx"], duty) and not any(x[0] == cfg["audit_committee_unit"] for x in out):
            out.append((cfg["audit_committee_unit"], "(판단)", f"(판단) 담당업무 「{duty}」의 「감사위원」을 감사위원회 위원으로 봄"))
        # 이름 일치가 있으면 같은 단위의 판단 중복 제거
        seen, res = set(), []
        for x in out:
            if (x[0], x[1]) in seen:
                continue
            seen.add((x[0], x[1]))
            res.append(x)
        return res

    for tag in execs:
        for e in execs[tag]["rows"]:
            e["대응"] = match_exec(tag, e)

    # ── 산출: 임원겸직 CSV ──
    exec_rows = []
    b = meta["biz"]
    for tag in ("기준일", "이후"):
        cmap = {}
        for c in concs[tag]["rows"]:
            cmap.setdefault(c["성명"], []).append(c)
        names = [e["성명"] for e in execs[tag]["rows"]]
        for e in execs[tag]["rows"]:
            units_s = "; ".join(f"{uid[x[0]]['단위']}({x[0]})" if x[0] else "대응 단위 없음" for x in e["대응"]) or NONE
            way_s = "; ".join(x[2] if x[1] != "이름 일치" else f"이름 일치: {uid[x[0]]['단위']}" for x in e["대응"]) or "(판단) 담당업무에 조직도 단위 이름이 나오지 않음"
            esrc = f"사업보고서 (2025.12) · {cfg['biz']} · p.{e['쪽']} · {execs[tag]['title']} {execs[tag]['basis']}"
            cs = cmap.get(e["성명"], [])
            if not cs:
                exec_rows.append(dict(회사=company, 성명=e["성명"], 직위=e["직위"], 등기=e["등기"], 상근=e["상근"], **{"담당업무(원문)": e["담당업무"]},
                                      대응_조직단위=units_s, 대응_방식=way_s, 겸직회사=f"겸직 표({concs[tag]['basis']})에 나오지 않음",
                                      겸직회사_직위="", 선임일="", 상근여부="", **{"출처(문서·접수번호·쪽)": esrc}))
            for c in cs:
                exec_rows.append(dict(회사=company, 성명=e["성명"], 직위=e["직위"], 등기=e["등기"], 상근=e["상근"], **{"담당업무(원문)": e["담당업무"]},
                                      대응_조직단위=units_s, 대응_방식=way_s, 겸직회사=c["회사"], 겸직회사_직위=c["직위"], 선임일=c["선임"], 상근여부=c["상근"],
                                      **{"출처(문서·접수번호·쪽)": esrc + f" ‖ 겸직: p.{c['쪽']} · {concs[tag]['title']} {concs[tag]['basis']}"
                                         + (" (성명 칸은 위 행과 합친 칸 — rowspan)" if c["이름칸합침"] else "")}))
        for nm, cs in cmap.items():
            if nm in names:
                continue
            for c in cs:
                exec_rows.append(dict(회사=company, 성명=nm, 직위=f"임원 표({execs[tag]['basis']})에 나오지 않음", 등기="", 상근="",
                                      **{"담당업무(원문)": "임원 표에 나오지 않음"}, 대응_조직단위=NONE, 대응_방식="(판단) 임원 표 밖 인물 — 겸직 표에만 나옴",
                                      겸직회사=c["회사"], 겸직회사_직위=c["직위"], 선임일=c["선임"], 상근여부=c["상근"],
                                      **{"출처(문서·접수번호·쪽)": f"사업보고서 (2025.12) · {cfg['biz']} · p.{c['쪽']} · {concs[tag]['title']} {concs[tag]['basis']}"
                                         + (" (성명 칸은 위 행과 합친 칸 — rowspan)" if c["이름칸합침"] else "")}))
    EXEC_COLS = ["회사", "성명", "직위", "등기", "상근", "담당업무(원문)", "대응_조직단위", "대응_방식", "겸직회사", "겸직회사_직위", "선임일", "상근여부", "출처(문서·접수번호·쪽)"]
    write_csv(OUT_DIR / f"{company}_임원겸직.csv", EXEC_COLS, fix_rows(exec_rows, f"{company} 임원겸직 CSV"))

    # ── 산출: 지원조직 CSV ──
    # 비평 보정 2: 열 이름 「주요 활동」 → 「주요 활동(원문)」(8개사 공통 꼴)
    SUP_COLS = ["회사", "조직 종류", "부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)", "기준일", "출처"]
    sup_rows = []
    for s in supports:
        sup_rows.append({"회사": company, "조직 종류": s["kind"] + " (사업보고서 표)", "부서(팀)명": s["dept"], "직원수": s["n"],
                         "직위(근속연수)": s["pos"] + (f"\n{s['note']}" if s["note"] else ""), "주요 활동(원문)": s["act"],
                         "기준일": "표에 기준일 글 없음 (사업보고서 기준일 2025년 12월 31일 — (판단))",
                         "출처": src(meta, "biz", f"p.{s['쪽']}", f"{s['title']} · 원문 XML 칸 글, PDF 텍스트 {s['대조']}")})
    for s in sq_rows:
        sup_rows.append({"회사": company, "조직 종류": s["kind"], "부서(팀)명": s["dept"], "직원수": s["n"], "직위(근속연수)": s["pos"],
                         "주요 활동(원문)": s["act"], "기준일": s["basis"], "출처": s["src"] + (f" ‖ 활동: {s['act_src']}" if s["act_src"] != s["src"] else "")})
    for name, p in chart_pairs.items():
        sup_rows.append({"회사": company, "조직 종류": "연차보고서 지배구조 조직도(글자 층) 인원", "부서(팀)명": name,
                         "직원수": p["text"].split("\n")[1],
                         "직위(근속연수)": none_in("출처 칸 조직도 글", "부서 이름·인원 밖 글이 나오지 않음"),
                         "주요 활동(원문)": none_in("출처 칸 조직도 글", "부서 이름·인원 밖 글이 나오지 않음"),
                         "기준일": cfg["ann_chart_basis"], "출처": src(meta, "ann", f"p.{p['page']}", f"{docs['ann'].rel} {p['line']}행 · 원문 줄: {p['text'].replace(chr(10), ' / ')}")})
    ia_basis = "※ 2025년 12월 31일 기준 내부회계관리운영조직 관련 사항 기재" if company == "KB금융지주" else "표에 기준일 글 없음 (사업보고서 기준일 2025년 12월 31일 — (판단))"
    for r in ia:
        sup_rows.append({"회사": company, "조직 종류": "내부회계관리 운영조직 인력 (사업보고서 표)", "부서(팀)명": r["dept"], "직원수": f"총원 {r['총원']}",
                         "직위(근속연수)": f"내부회계담당인력수(A) {r['담당']} · 공인회계사자격증소지자수(B) {r['cpa']} · 비율(B/A*100) {r['비율']} · 내부회계담당인력의평균경력월수 {r['경력']}",
                         "주요 활동(원문)": none_in("출처 칸 표", "이 표는 인원·자격만 적음"), "기준일": ia_basis,
                         "출처": src(meta, "biz", f"p.{r['쪽']}", f"{ia_title} · 원문 XML 칸 글")})
    sup_out = fix_rows(sup_rows, f"{company} 지원조직 CSV")
    # 비평 보정 2: 날짜 글이 없던 기준일 칸(「cell」 꼴)은 연차보고서 문장 행에만 있어야 「연차보고서 대상 연도」 근거가 맞음
    for r in sup_out:
        if r["기준일"] in [x[0] for x in FIX2 if x[3] == "cell"] and not r["출처"].startswith(f"[{DOCNAME['ann']}"):
            checks["problems"].append(f"기준일 「{r['기준일']}」 행의 출처가 연차보고서가 아님: {r['부서(팀)명']}")
    write_csv(OUT_DIR / f"{company}_지원조직.csv", SUP_COLS, fix2_rows(sup_out, f"{company} 지원조직 CSV", ("기준일",)))

    # ── 단위별 인원 연결 ──
    sup_by = {s["dept"]: s for s in supports}
    ia_by = {r["dept"]: r for r in ia}

    def staff_items(u):
        items = []
        for (kind, key, way) in cfg["unit_staff"].get(u["id"], []):
            if kind == "support":
                s = sup_by[key]
                items.append(dict(n=s["n"], 내역=f"{s['dept']} | {s['n']} | {s['pos']}" + (f" | {s['note']}" if s["note"] else ""),
                                  basis="표에 기준일 글 없음(사업보고서 2025.12.31 기준 (판단))",
                                  src=src(meta, "biz", f"p.{s['쪽']}", s["title"]), way=way))
            elif kind == "ann_chart":
                p = chart_pairs[key]
                items.append(dict(n=p["text"].split("\n")[1], 내역=p["text"].replace("\n", " "), basis=cfg["ann_chart_basis"],
                                  src=src(meta, "ann", f"p.{p['page']}", "지배구조 현황 (1) 조직도(글자 층)"), way=way))
            elif kind == "ia":
                r = ia_by[key]
                items.append(dict(n=f"총원 {r['총원']}", 내역=f"{r['dept']} | 총원 {r['총원']} | 내부회계담당인력수(A) {r['담당']}",
                                  basis=ia_basis, src=src(meta, "biz", f"p.{r['쪽']}", ia_title), way=way))
            elif kind == "sq":
                s = sq_rows[key]
                items.append(dict(n=s["n"], 내역=s["pos_raw"] if s["pos_raw"] != NONE else s["n"], basis=s["basis"], src=s["src"], way=way))
        # 검증 에이전트가 반박 검색으로 보탠 연차보고서 조직도 글(위원 수) — 검증 반영 입력 「인원_보탬」
        for x in VR["인원_보탬"]:
            if x["단위"] != u["id"]:
                continue
            t = docs["ann"]
            assert t.rel.endswith(x["파일"]), (t.rel, x["파일"])
            a_, b_ = x["줄"]
            ls = [t.lines[k].strip() for k in range(a_ - 1, b_)]
            k0 = [k for k, l in enumerate(ls) if l.startswith("(")][0]
            n_txt = " ".join(ls[k0:])
            if n_txt != x["인원_글"]:
                checks["problems"].append(f"인원 보탬 {u['id']} 줄 {a_}~{b_} 글이 입력과 다름: {n_txt}")
            items.append(dict(n=n_txt, 내역=" ".join(ls), basis=cfg["ann_chart_basis"],
                              src=src(meta, "ann", f"p.{t.page[a_ - 1]}", "지배구조 현황 (1) 조직도(글자 층)"),
                              way=f"{x['연결']} · 검증 에이전트가 반박 검색으로 보탬({x['파일']} {a_}~{b_}행)",
                              md_way=f"{x['연결']} (검증 반박으로 보탬)"))
        return items

    # 단위별 임원(이후 표 우선, 기준일 표 함께)
    unit_exec = {u["id"]: [] for u in units}
    for tag in ("이후", "기준일"):
        for e in execs[tag]["rows"]:
            for (u_, way, why) in e["대응"]:
                if u_:
                    unit_exec[u_].append((tag, e, way, why))
    conc_by = {tag: {} for tag in concs}
    for tag in concs:
        for c in concs[tag]["rows"]:
            conc_by[tag].setdefault(c["성명"], []).append(c)

    UNIT_COLS = ["회사", "조직도_문서", "조직도_쪽", "조직도_기준일(원문)", "상위단위(판독)", "조직단위(판독)", "단위_층위(판독)", "조직도_겸직표시(판독, 없으면 빈칸)",
                 "공시인원(원문, 없으면 「추출 범위에 없음」)", "인원_내역(원문)", "인원_기준일", "인원_출처",
                 "대응_임원(성명·직위)", "대응_근거(담당업무 원문)", "대응_방식(이름 일치/(판단)/추출 범위에 없음)",
                 "임원_겸직(원문: 겸직회사·직위·선임일·상근)", "겸직_출처", "판독_대조", "비고"]
    unit_rows, unit_md_ways, no_exec = [], [], []

    def nkey(x):
        return nzd(x).replace("그룹", "")

    chart_doc =f"{readA['문서']} · {readA['url']} · sha256 {readA['pdf_sha256'][:12]}…"
    basis_txt = Q["chart_title"]["text"]
    staffed = 0
    for u in units:
        st = staff_items(u)
        if st:
            staffed += 1
        ex = unit_exec[u["id"]]
        # 같은 사람·같은 표 중복 제거
        seen, ex2 = set(), []
        for x in ex:
            k = (x[0], x[1]["성명"])
            if k in seen:
                continue
            seen.add(k)
            ex2.append(x)
        tagname = {"이후": execs["이후"]["basis"], "기준일": execs["기준일"]["basis"]}
        ex_s = "\n".join(f"[{tagname[t]}] {e['성명']} · {e['직위']}" for t, e, w, y in ex2)
        why_s = "\n".join(f"[{tagname[t]}] {e['성명']}: {e['담당업무']} (p.{e['쪽']})" for t, e, w, y in ex2)
        way_s = "\n".join(f"[{tagname[t]}] {e['성명']}: {w if w == '이름 일치' else y}" for t, e, w, y in ex2)
        cc, cs_src = [], []
        for t, e, w, y in ex2:
            for c in conc_by[t].get(e["성명"], []):
                cc.append(f"[{concs[t]['basis']}] {c['성명']}: {c['회사']} · {c['직위']} · {c['선임']} · {c['상근']}")
                cs_src.append(f"사업보고서 (2025.12) · {cfg['biz']} · p.{c['쪽']} · {concs[t]['title']}")
        if ex2 and not cc:
            cc = [f"대응 임원의 이름이 겸직 표({concs['기준일']['basis']} / {concs['이후']['basis']})에 나오지 않음"]
        if not ex2:
            # 비평 보정: 맡은 임원 「추출 범위에 없음」 행에 찾은 방법(기계 검색 결과)을 적음
            key = nkey(u["단위"])
            hits = [(t, e) for t in ("기준일", "이후") for e in execs[t]["rows"] if key and key in nkey(e["담당업무"])]
            base = (f"찾은 방법: 사업보고서 {cfg['biz']} 임원 표 {execs['기준일']['basis']} {len(execs['기준일']['rows'])}명·"
                    f"작성기준일 이후 임원 표 {execs['이후']['basis']} {len(execs['이후']['rows'])}명의 담당업무에서 「{u['단위']}」 글자 검색"
                    "(띄어쓰기·가운뎃점·「그룹」 붙임 무시)")
            if not hits:
                why_s = base + " — 0건"
            else:
                names = "·".join(dict.fromkeys(e["성명"] for _, e in hits))
                why_s = base + f" — {len(hits)}건({names} 담당업무 안 다른 낱말에 걸림)"
                if u["층위"].startswith("도식"):
                    why_s += " — (판단) 도식 상자 이름이 다른 낱말 안에 걸린 것이라 대응하지 않음"
                else:
                    checks["problems"].append(f"맡은 임원 없음 단위 {u['단위']} 가 담당업무 글자 검색에 걸림 — 대응 다시 볼 것")
            cc = ["해당 없음(대응 임원 추출 범위에 없음)"]
            no_exec.append((u, len(hits)))
        unit_rows.append({
            "회사": company, "조직도_문서": chart_doc, "조직도_쪽": f"PDF p.{readA['pdf_쪽']} (인쇄 쪽 {readA['인쇄_쪽']})",
            "조직도_기준일(원문)": basis_txt, "상위단위(판독)": u["상위단위"], "조직단위(판독)": u["단위"], "단위_층위(판독)": u["층위"],
            "조직도_겸직표시(판독, 없으면 빈칸)": u["겸직표시"],
            "공시인원(원문, 없으면 「추출 범위에 없음」)": "\n".join(f"{s['n']}" for s in st) if st else NONE,
            "인원_내역(원문)": "\n".join(s["내역"] for s in st),
            "인원_기준일": "\n".join(s["basis"] for s in st),
            "인원_출처": "\n".join(f"{s['src']} — 연결: {s['way']}" for s in st) if st else
                     f"찾은 방법: 사업보고서 {cfg['biz']} 지원조직 표 2개·내부회계 인력 표·사외이사 지원 문장, 연차보고서 조직도 글·인원 서술, 경영공시 전문(「임직원」「직원」「인원」「명」 검색)에서 이 단위 이름+인원 숫자 나오지 않음",
            "대응_임원(성명·직위)": ex_s or NONE,
            "대응_근거(담당업무 원문)": why_s,
            "대응_방식(이름 일치/(판단)/추출 범위에 없음)": way_s or NONE,
            "임원_겸직(원문: 겸직회사·직위·선임일·상근)": "\n".join(cc),
            "겸직_출처": "\n".join(sorted(set(cs_src))),
            "판독_대조": VR["판독_대조"][u["id"]],
            "비고": u["csv_비고"] if "csv_비고" in u else "; ".join(x for x in [u["연결근거"], u["비고"]] if x),
        })
        unit_md_ways.append([(s.get("md_way", s["way"]), "md_way" in s) for s in st])
    write_csv(OUT_DIR / f"{company}_조직단위.csv", UNIT_COLS,
              fix2_rows(fix_rows(unit_rows, f"{company} 조직단위 CSV"), f"{company} 조직단위 CSV", ("인원_기준일",)))

    # ── 산출: 판독대조 CSV ──
    RB_COLS = ["칸", "판독A", "판독B", "확정", "확정 방법"]
    rb = []
    for h in readA["머리글_판독"]:
        rb.append({"칸": h["칸"], "판독A": h["판독"]})
    for u in unitsA:
        rb.append({"칸": f"{u['id']} 단위 이름", "판독A": u["단위"]})
        rb.append({"칸": f"{u['id']} 상위단위", "판독A": u["상위단위"] or "(없음 — 맨 위)"})
        rb.append({"칸": f"{u['id']} 층위", "판독A": u["층위"]})
        rb.append({"칸": f"{u['id']} 겸직표시", "판독A": u["겸직표시"] or "(없음)"})
    # 판독B·확정·확정 방법 칸 = 검증 반영 입력(검증 에이전트가 판독 B JSON 을 먼저 저장한 뒤 채운 값)
    if [r["칸"] for r in rb] != [x[0] for x in VR["판독대조"]]:
        raise SystemExit(f"[판독대조 칸 순서가 검증 반영 입력과 다름] {company}")
    for r, x in zip(rb, VR["판독대조"]):
        r["판독B"], r["확정"], r["확정 방법"] = x[1], x[2], x[3]
    # 비평 보정: 빈 값 표지 「(없음…)」 → 「(빈칸…)」(②: 조직도에 그 표시·선이 나오지 않음)
    for r in rb:
        fld = r["칸"].split(" ", 1)[-1]
        for col in ("판독A", "판독B", "확정"):
            new = RB_MARK.get((fld, r[col]))
            if new:
                FIX.n[(f"{company} 판독대조 CSV", f"{r[col]} → {new}")] = FIX.n.get((f"{company} 판독대조 CSV", f"{r[col]} → {new}"), 0) + 1
                r[col] = new
    # 비평 보정 2: 판독B 칸 「…없음」 → ② 꼴(판독 B JSON 은 그대로 — CSV 로 옮길 때만 바꿈)
    for r in rb:
        for old, new in RB2_MARK:
            if old in r["판독B"]:
                FIX2N[(f"{company} 판독대조 CSV", old)] = FIX2N.get((f"{company} 판독대조 CSV", old), 0) + r["판독B"].count(old)
                r["판독B"] = r["판독B"].replace(old, new)
    write_csv(OUT_DIR / f"{company}_판독대조.csv", RB_COLS, rb)

    # ── 집계 ──
    marks = [u for u in units if u["겸직표시"]]
    n_exec = len(execs["기준일"]["rows"])
    exec_names = {e["성명"] for e in execs["기준일"]["rows"]}
    conc_names = {c["성명"] for c in concs["기준일"]["rows"]}
    n_exec_conc = len(exec_names & conc_names)
    counts = dict(company=company, units=len(units), units_with_headcount=staffed, executives=n_exec,
                  executives_concurrent=n_exec_conc, orgchart_concurrent_marks=len(marks))
    dept_layers = {"부", "센터", "Unit", "연구소", "국", "실"}
    if company == "KB금융지주":
        cnt = dict(부문=sum(u["층위"] == "부문" for u in units), 담당=sum(u["층위"].startswith("담당") for u in units),
                   본부=sum(u["층위"] == "본부" for u in units), 부서=sum(u["층위"] in dept_layers for u in units),
                   부서_이름=[u["단위"] for u in units if u["층위"] in dept_layers])
    else:
        from collections import Counter
        cnt = dict(Counter(u["층위"] for u in units))
    checks["판독집계"] = cnt
    checks["counts"] = counts

    return dict(company=company, cfg=cfg, meta=meta, readA=readA, units=units, uid=uid, Q=Q, execs=execs, concs=concs,
                emp=emp, unreg=unreg, supports=supports, ia=ia, chart_pairs=chart_pairs, sq_rows=sq_rows,
                unit_rows=unit_rows, exec_rows=exec_rows, checks=checks, counts=counts, docs=docs, copy_diffs=copy_diffs,
                corr=corr, marks=marks, ia_basis=ia_basis, ia_title=ia_title, VR=VR, unit_md_ways=unit_md_ways,
                no_exec=no_exec, chart_hits=chart_hits, upside=upside, sup_rows=sup_rows)


# ───────────────────────── md ─────────────────────────
def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", "<br>")


def bq(text):
    return "\n".join("> " + l for l in text.split("\n"))


def md_fix(lines, where):
    """「없음」 보정 표를 md 줄에 씀 — 원문 인용(「> 」 줄)과 ``` 블록은 건드리지 않음."""
    out, code = [], False
    for x in lines:
        if x.startswith("```"):
            code = not code
            out.append(x)
            continue
        out.append(x if code or x.startswith(">") else FIX(x, where))
    return out


CIT_RX = re.compile(r"dart_out/text/risk8/(\S+?\.txt) ([0-9~,]+)행")
_TXT_CACHE = {}


def _keep(l):
    return l.strip() != "" and not l.startswith("=== p.") and not re.match(r"^전자공시시스템 dart\.fss\.or\.kr Page \d+", l)


def gap_marks(lines):
    """인용 블록이 떨어진 줄 범위를 이어 붙였고 그 사이에 다른 글이 끼어 있으면, 그 자리에
    블록 안 표지 줄 「[…줄 건너뜀: 텍스트 N~M행…]」 을 넣음(원문 줄은 그대로). 돌려줌: (새 줄, 넣은 표지 목록)."""
    out, marks, i = [], [], 0
    while i < len(lines):
        if not (lines[i].startswith(">") and not lines[i].startswith("> 「(판단)」 표시가 없는 글은")):
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < len(lines) and lines[j].startswith(">"):
            j += 1
        block = lines[i:j]
        cit = None
        for k in range(j, min(j + 4, len(lines))):
            m = CIT_RX.search(lines[k])
            if m:
                cit = m
                break
            if lines[k].startswith(">") or lines[k].startswith("#"):
                break
        if cit and "," in cit.group(2):
            fn = cit.group(1)
            if fn not in _TXT_CACHE:
                _TXT_CACHE[fn] = (TXT / fn).read_text(encoding="utf-8").split("\n")
            T = _TXT_CACHE[fn]
            rs = []
            for part in cit.group(2).split(","):
                a, _, b = part.partition("~")
                rs.append((int(a), int(b or a)))
            kept = [[n for n in range(a, b + 1) if _keep(T[n - 1])] for a, b in rs]
            if sum(len(k) for k in kept) != len(block):
                raise SystemExit(f"[건너뜀 표지] 블록 {len(block)}줄 ↔ 출처 줄 {sum(len(k) for k in kept)}줄: {fn} {cit.group(2)}")
            new, pos = [], 0
            for idx, (a, b) in enumerate(rs):
                new += block[pos:pos + len(kept[idx])]
                pos += len(kept[idx])
                if idx + 1 < len(rs):
                    a2 = rs[idx + 1][0]
                    if any(_keep(T[n - 1]) for n in range(b + 1, a2)):
                        new.append("> " + GAP_MARK.format(a=b + 1, b=a2 - 1))
                        marks.append((fn, b + 1, a2 - 1))
            block = new
        out += block
        i = j
    return out, marks


def fix_record(R, marks):
    """7) 검증 기록 끝에 붙이는 「비평 보정」 기록(전 → 후 대표 예와 개수 — 개수는 이번 실행에서 센 값)."""
    c = R["company"]
    n = {}
    for (where, old), k in FIX.n.items():
        if where.startswith(c + " "):
            n.setdefault(old, {})[where[len(c) + 1:]] = k
    L = [f"### 비평 보정(critic14 대응, {FIX_KST[:10]} KST)", "",
         f"비평 `dart_out/org14/critic14.json`(issues·gaps)과 `dart_out/raw/org14/critic/eopseum_content_hits.json` 에 따라 생성기 "
         "`scripts/dart/org14_g1.py` 를 고쳐 다시 만듦(산출물은 손으로 고치지 않음, 보정 시각 " + FIX_KST + "). 순서: ① 검증 때 산출물에 직접 고친 값"
         "(판독대조 CSV 판독B·확정·확정 방법, 조직단위 CSV 판독_대조·비고, 연차보고서 조직도 위원 수 보탬, 6) 보탬·바꿈 행, 7) 검증 기록)을 "
         f"`dart_out/org14/{c}_검증반영.json` 으로 옮기고 생성기가 그때의 md·CSV 를 바이트까지 같게 다시 만드는 것을 확인(diff 0) → "
         "② 아래 보정 → ③ `scripts/dart/verify14_g1.py` exit 0 · 생성기 두 번 실행 md5 같음. 원문 인용(「> 」 줄·``` 블록)·원문 칸 글은 그대로, "
         "작업 사실(웹 요청 없음·고친 곳: 없음·바뀐 곳 없음)과 위 검증 기록의 지난 전 → 후 기록도 그대로.", "",
         "| 바꾼 것 | 전 → 후(대표 예) | 개수 |", "|---|---|---|"]
    for old, new, rule in FIX_EOPSEUM:
        if old in n:
            cnt = " · ".join(f"{w} {k}" for w, k in n[old].items())
            L.append(f"| 「없음」 꼴 {rule} | 「{esc(old)}」 → 「{esc(new)}」 | {cnt} |")
    # ① 찾은 범위를 붙인 「추출 범위에 없음」 칸(이번 실행 산출에서 셈)
    for key, before, ex in ((f"{NONE}(찾은 범위: 출처 칸 문장(", NONE, "직위 글이 나오지 않음 / 총 인원 숫자가 나오지 않음"),
                            (f"{NONE}(찾은 범위: 출처 칸 조직도 글", NONE, "부서 이름·인원 밖 글이 나오지 않음"),
                            (f"{NONE}(찾은 범위: 출처 칸 표", f"{NONE} (이 표는 인원·자격만 적음)", "이 표는 인원·자격만 적음")):
        k_sup = sum(v.count(key) for r in R["sup_rows"] for v in r.values())
        k_unit = sum(v.count(key) for r in R["unit_rows"] for v in r.values())
        if k_sup or k_unit:
            where = key[len(NONE) + 1:].rstrip("(")
            L.append(f"| ① 찾은 범위 붙임 | 「{before}」 → 「{NONE}({where} — {ex})」 꼴 | 지원조직 CSV {k_sup} · 조직단위 CSV {k_unit}"
                     + (" (md 3-6 표에도 같은 칸)" if k_unit else "") + " |")
    for old, d in n.items():
        if " → (빈칸" in old:
            cnt = " · ".join(f"{w} {k}" for w, k in d.items())
            L.append(f"| ② 판독대조 빈 값 표지 | 「{old.split(' → ')[0]}」 → 「{old.split(' → ')[1]}」 | {cnt} |")
    ne = R["no_exec"]
    n0 = sum(1 for _, h in ne if h == 0)
    L.append(f"| 맡은 임원 「{NONE}」 행의 찾은 방법(조직단위 CSV) | 대응_근거 빈칸 → 「찾은 방법: 사업보고서 … 임원 표 … 담당업무에서 「단위」 글자 검색"
             f"(띄어쓰기·가운뎃점·「그룹」 붙임 무시) — 0건」; 임원_겸직 빈칸 → 「해당 없음(대응 임원 추출 범위에 없음)」 | {len(ne)}행(0건 {n0} · 다른 낱말에 걸림 {len(ne) - n0}) · md 6) 「맡은 임원」 행 1 |")
    if R["upside"]:
        L.append(f"| 거꾸로 그린 조직도 해석에 기댄 상위단위 (판단) 표시 | 비고 「…(판독)」 → 「…(판독); (판단) 조직도를 위아래 거꾸로 그린 꼴로 봄 — md·판독대조 K48」 | "
                 f"{len(R['upside'])}행({', '.join(R['upside'])}) · 조직단위 CSV·md 1) 표 |")
    if c == "KB금융지주":
        q = R["Q"]["emp_exchange"]
        L.append(f"| 빠진 가까운 글 보탬(gaps) | 2) 직원 겸직 칸에 사업보고서 {q['pages']} 「(2) 종업원에 관한 사항」 인력교류 문장 인용(텍스트 {q['lines']}행) + (판단) 그룹 전 계열사 숫자 — 지주 직원 겸직 숫자 아님 | md 인용 1 · 6) 받은 것 1 |")
    else:
        q = R["Q"]["ann_succ_137"]
        L.append(f"| 빠진 문장 보탬(gaps) | 3-4 에 연차보고서 {q['pages']} 「사. 대표이사 회장 승계업무 지원부서 운영 현황」 인용(텍스트 {q['lines']}행) + (판단) 「팀장과 팀원 10명」 = 총 10명 또는 팀장 1명+팀원 10명; 신한리더십센터 행 공시인원에 보탬 | md 인용 1 · 조직단위 CSV 1행(칸 4개) · 지원조직 CSV 1행 · 6) 받은 것 1 |")
    for fn, a, b in marks:
        L.append(f"| 떨어진 줄을 이은 인용 블록 | 이어 붙인 자리(표지 없음) → 블록 안 표지 줄 「{GAP_MARK.format(a=a, b=b)}」({fn}) | 1 |")
    L.append(f"| 사업보고서 「조직도」 검색 기록(COMMON 21행) | 기록 없음 → 1) 에 「사업보고서 텍스트에서 「조직도」 검색 … 나온 곳 {len(R['chart_hits'])}줄 …」 한 줄 | 1 |")
    L.append("| 작업 시각 | 「작업일」 칸이 실행할 때마다 바뀜 → 첫 실행 시각·보정 시각을 고정값으로(멱등) | 1 |")
    return L


def write_md(R, extra):
    c, cfg, meta, Q = R["company"], R["cfg"], R["meta"], R["Q"]
    A = R["readA"]
    b = meta["biz"]
    L = []
    L.append(f"# 14차 — {c} 지주 조직도 × 조직별 인원 × 겸직\n")
    L.append("> 「(판단)」 표시가 없는 글은 원문 글자 그대로(공백만 정리), 「판독」은 조직도 그림을 눈으로 읽은 글(원문 글자 그대로가 아님).\n")
    L.append("## 0) 머리\n")
    L.append("| 항목 | 내용 |\n|---|---|")
    L.append(f"| 조직도 문서 | {A['문서']} · {A['url']} · 게시일 {meta['mgmt']['date']} · sha256 `{meta['mgmt']['sha']}` · 수집 {meta['mgmt']['fetched']} · PDF p.{A['pdf_쪽']}(인쇄 쪽 {A['인쇄_쪽']}) |")
    L.append(f"| 사업보고서 | {b['title']} · 접수번호 {cfg['biz']} · {b['url']} · 접수일 {b['date']} · 본문 PDF sha256 `{b.get('pdf_sha', '')}` · 원문 XML zip sha256 `{b['zip_sha']}` · 수집 {b['fetched']} |")
    for rc in cfg["biz_corr"]:
        x = meta["biz_all"][rc]
        L.append(f"| 사업보고서 정정판 | {x['title']} · {rc} · 접수일 {x['date']} · 본문 PDF sha256 `{x.get('pdf_sha', '')}` · XML zip sha256 `{x['zip_sha']}`(document_status {x['status']}) |")
    for k in ("ann", "ann_add"):
        d = meta[k]
        L.append(f"| {DOCNAME[k]} | {d['title']} · {d['url']} · 공시일 {d['date']} · sha256 `{d['sha']}` · 수집 {d['fetched']} |")
    L.append(f"| 텍스트(쪽 표지 `=== p.N ===`) | `{R['docs']['biz'].rel}`, `{R['docs']['ann'].rel}`, `{R['docs']['ann_add'].rel}`, `{R['docs']['mgmt'].rel}` |")
    L.append(f"| 작업일 | {R['VR']['작업일_KST']} (스크립트 `scripts/dart/org14_g1.py` 첫 실행 시각) · 비평 보정 {FIX_KST}(같은 스크립트로 다시 만듦 — 시각은 스크립트 안 고정값이라 다시 돌려도 같은 파일) · 판독 A {A['판독일시_KST']} |")
    L.append(f"| 기준일 ① 조직도 | 「{Q['chart_title']['text']}」 (경영공시 {Q['chart_title']['pages']}, 글자 층 원문) |")
    L.append(f"| 기준일 ② 사업보고서 | 임원 표 「{R['execs']['기준일']['basis']}」, 작성기준일 이후 임원 표 「{R['execs']['이후']['basis']}」, 직원 표 「{R['emp']['기준일']}」 |")
    L.append(f"| 기준일 ③ 연차보고서 | 조직도 「{cfg['ann_chart_basis']}」, 인원 서술은 문장마다 다름(아래 3) 표의 기준일 칸) |")
    L.append("| 방법 | 조직도: 200dpi 쪽 그림을 먼저 보고 글자가 작은 곳은 300~600dpi 로 잘라(clip) 판독(그림 목록은 `" + f"dart_out/org14/{c}_판독A.json`). 표: 사업보고서 원문 XML 칸 글을 그대로 옮기고, 같은 접수번호 PDF 텍스트에서 공백 무시로 찾아 쪽을 붙임. 서술: 텍스트 파일 줄 그대로(쪽·줄 번호). 웹 요청 없음. |")
    L.append("| 쪽 번호 | 모두 PDF 쪽(텍스트 파일 `=== p.N ===`). 사업보고서 PDF 쪽 아래 「Page N」 인쇄 번호와 다름. |")
    L.append("| 한계 | 조직도(2026년 8월)와 인원·겸직(2025.12.31 / 작성기준일 이후 2026.3) 기준일이 다름. 일반 부서 인원은 공시되지 않아 대부분 「추출 범위에 없음」. 조직도 그림 원본 해상도가 낮아(" + A["그림"]["원본_해상도_추정"] + ") 단위 이름·선 관계는 검증 판독 B 대조로 확정(7) 검증 기록 — 가운뎃점 글자 등 남은 문제는 그곳에). |\n")

    # 1) 조직도 판독 표
    L.append("## 1) 조직도 판독 표 (판독 A · 검증 판독 B 대조 후 확정 — 대조는 7) 검증 기록)\n")
    L.append(f"- 기준일 글(글자 층, 원문): 「{Q['chart_title']['text']}」 {Q['chart_title']['src']}")
    for h in A["머리글_판독"]:
        L.append(f"- {h['칸']} (판독): 「{h['판독']}」 — 확대: `{h['확대그림']}` {h['dpi']}dpi clip {h['clip_pt']}")
    L.append(f"- 배치(판독): {A['배치_판독']}")
    L.append(f"- 겸직 표시(판독): {A['겸직표시_판독']}")
    hits = R["chart_hits"]
    L.append(f"- 사업보고서 텍스트에서 「조직도」 검색(`{R['docs']['biz'].rel}` 전체) — 나온 곳 {len(hits)}줄: "
             + " · ".join(f"{ln}행(p.{pg}) 「{t}」" for ln, pg, t in hits) + f" — {cfg['chart_search_note']}\n")
    L.append("| id | 상위단위(판독) | 조직단위(판독) | 층위(판독) | 겸직 표시(판독) | 선·자리 근거(판독) | 비고 |\n|---|---|---|---|---|---|---|")
    for u in R["units"]:
        L.append(f"| {u['id']} | {esc(u['상위단위'])} | {esc(u['단위'])} | {esc(u['층위'])} | {esc(u['겸직표시'])} | {esc(u['연결근거'])} | {esc(u.get('md_비고', u['비고']))} |")
    L.append("")
    L.extend(extra.get("chart_check", []))

    # 2) 직원 수·겸직 숫자
    L.append("## 2) 지주 전체 직원 수 · 직원 겸직 숫자\n")
    e = R["emp"]
    L.append("**사업보고서 「직원 등 현황」**")
    L.append(f"- 기준일 글: 「{e['기준일']}」 · [사업보고서 (2025.12) · {cfg['biz']} · p.{e['쪽']}]")
    L.append("- 표 머리(원문 XML 칸, 「 | 」로 칸 구분): " + " ‖ ".join(f"`{h}`" for h in e["head"]))
    for r in e["rows"]:
        L.append(f"  - `{r}`")
    L.append("- 표 아래 주석(원문 줄):\n")
    L.append(bq(Q["emp_notes"]["text"]))
    L.append(f"\n  {Q['emp_notes']['src']}\n")
    L.append("**미등기임원 보수 현황 표**(원문 XML 칸): " + " ‖ ".join(f"`{x}`" for x in R["unreg"]))
    L.append("\n" + bq(Q["unreg_note"]["text"]) + f"\n\n  {Q['unreg_note']['src']}\n")
    L.extend(extra.get("emp_extra", []))

    # 3) 조직별 공시 인원
    L.append("## 3) 조직별 공시 인원 (원문)\n")
    L.append("### 3-1 사업보고서 지원조직 표 (원문 XML 칸 글 · PDF 텍스트 공백 무시 대조)\n")
    L.append("| 조직 종류 | 부서(팀)명 | 직원수(명) | 직위(근속연수) | 주요 활동내역 | 쪽 | 대조 |\n|---|---|---|---|---|---|---|")
    for s in R["supports"]:
        L.append(f"| {esc(s['title'])} | {esc(s['dept'])} | {esc(s['n'])} | {esc(s['pos'])}{'<br>' + esc(s['note']) if s['note'] else ''} | {esc(s['act'])} | p.{s['쪽']} | {s['대조']} |")
    L.append(f"\n출처: [사업보고서 (2025.12) · {cfg['biz']} · 위 쪽 · 수집 {b['fetched'][:10]}] — 표 칸에 줄바꿈이 없는 것은 원문 XML 칸 글에도 줄바꿈이 없기 때문(PDF 텍스트는 칸 폭으로 줄이 꺾임).\n")
    L.append("### 3-2 사외이사 지원조직(이사회사무국) — 사업보고서 문장\n")
    L.append(bq(Q["bod_sec_biz"]["text"]) + f"\n\n{Q['bod_sec_biz']['src']}\n")
    L.append(bq(Q["bod_roles_biz"]["text"]) + f"\n\n{Q['bod_roles_biz']['src']}\n")
    L.append(f"### 3-3 내부회계관리 운영조직 인력 표 — 「{R['ia_title']}」\n")
    L.append("| 소속기관 또는 부서 | 총 원 | 내부회계담당인력수(A) | 공인회계사자격증소지자수(B) | 비율(B/A*100) | 평균경력월수 | 쪽 |\n|---|---|---|---|---|---|---|")
    for r in R["ia"]:
        L.append(f"| {esc(r['dept'])} | {r['총원']} | {r['담당']} | {r['cpa']} | {r['비율']} | {r['경력']} | p.{r['쪽']} |")
    L.append("\n" + bq(Q["ia_notes"]["text"]) + f"\n\n{Q['ia_notes']['src']}\n")
    L.append("### 3-4 연차보고서 — 조직도(글자 층)·부서 인원 서술\n")
    L.append(bq(Q["ann_chart"]["text"]) + f"\n\n{Q['ann_chart']['src']} · 추가공시 텍스트와 {Q['ann_chart'].get('ann_add_same', '')}\n")
    for qid in [k for k in Q if k.startswith("ann_") and k not in ("ann_chart",)]:
        L.append(f"**{QTITLE.get(qid, qid)}** (`{qid}`)\n\n" + bq(Q[qid]["text"]) + f"\n\n{Q[qid]['src']} · 추가공시 텍스트와 {Q[qid].get('ann_add_same', '')}\n")
        if qid in QNOTE:
            L.append(QNOTE[qid] + "\n")
    L.append("### 3-5 경영공시 2026 2Q — 조직 관련 글\n")
    for qid in [k for k in Q if k.startswith("mgmt_")]:
        L.append(f"**{QTITLE.get(qid, qid)}** (`{qid}`)\n\n" + bq(Q[qid]["text"]) + f"\n\n{Q[qid]['src']}\n")
    L.append("- 경영공시 2026 2Q 의 임직원 수: " + NONE + " — 찾은 방법: `" + R["docs"]["mgmt"].rel + "` 전체(목차 「일반현황」 아래 「조직 및 영업점」뿐)에서 「임직원」「직원」「인원」「사무국」「조직」 검색; 나온 글은 위 3-5 와 은행 자회사 유동성 조직 설명뿐.\n")
    L.extend(extra.get("other_quotes", []))
    L.append("### 3-6 조직 단위별 인원 연결 (조직단위 CSV 요약)\n")
    L.append("| 단위(판독) | 공시인원(원문) | 인원 내역(원문) | 기준일 | 연결 방식 |\n|---|---|---|---|---|")
    # 순서: 수집 때 인원을 붙인 단위(조직도 순서) → 검증 반박으로만 인원을 보탠 단위(조직도 순서)
    trip = list(zip(R["unit_rows"], R["units"], R["unit_md_ways"]))
    trip = [x for x in trip if not all(e for _, e in x[2])] + [x for x in trip if x[2] and all(e for _, e in x[2])]
    for r, u, mw in trip:
        if r["공시인원(원문, 없으면 「추출 범위에 없음」)"] != NONE:
            ways = "<br>".join(w for w, _ in mw)
            L.append(f"| {esc(u['단위'])} | {esc(r['공시인원(원문, 없으면 「추출 범위에 없음」)'])} | {esc(r['인원_내역(원문)'])} | {esc(r['인원_기준일'])} | {ways} |")
    L.append(f"\n그 밖 {len(R['units']) - R['counts']['units_with_headcount']}개 단위: 「{NONE}」(찾은 방법은 조직단위 CSV 「인원_출처」 칸).\n")

    # 4) 임원 ↔ 조직 단위
    L.append("## 4) 임원(사업보고서 「임원 현황」) ↔ 조직 단위\n")
    for tag in ("기준일", "이후"):
        X = R["execs"][tag]
        L.append(f"### {X['title']} {X['basis']} — {len(X['rows'])}명\n")
        L.append("| 성명 | 직위 | 등기 | 상근 | 담당업무(원문) | 쪽 | 대응 조직 단위 | 대응 방식 |\n|---|---|---|---|---|---|---|---|")
        for e in X["rows"]:
            us = "<br>".join(f"{R['uid'][x[0]]['단위']}" if x[0] else "대응 단위 없음" for x in e["대응"]) or NONE
            ws = "<br>".join("이름 일치" if x[1] == "이름 일치" else esc(x[2]) for x in e["대응"]) or "(판단) 담당업무에 조직도 단위 이름이 나오지 않음"
            L.append(f"| {e['성명']} | {esc(e['직위'])} | {e['등기']} | {e['상근']} | {esc(e['담당업무'])} | p.{e['쪽']} | {esc(us)} | {ws} |")
        L.append(f"\n출처: [사업보고서 (2025.12) · {cfg['biz']} · 표의 쪽 칸 · 수집 {b['fetched'][:10]}] — 담당업무 칸 글은 원문 XML 그대로(칸 안 항목 사이에 구분 글자가 없는 것도 원문 XML 그대로이며, PDF 에서는 줄바꿈으로 보임)이고, PDF 텍스트 대조 결과는 모든 행 「" + ", ".join(sorted(set(e['대조'] for e in X['rows']))) + "」.\n")

    # 5) 임원 겸직
    L.append("## 5) 임원 겸직 — 사업보고서 「계열회사간 임원 겸직 현황」\n")
    for tag in ("기준일", "이후"):
        C = R["concs"][tag]
        L.append(f"### {C['title']} {C['basis']} — {len(C['rows'])}행\n")
        L.append("| 성명 | 대상 회사 | 직책(직위) | 선임 | 비고(상근) | 쪽 | 원문 행(칸 그대로) |\n|---|---|---|---|---|---|---|")
        for x in C["rows"]:
            L.append(f"| {x['성명']}{' (합친 칸)' if x['이름칸합침'] else ''} | {esc(x['회사'])} | {esc(x['직위'])} | {x['선임']} | {x['상근']} | p.{x['쪽']} | `{x['raw']}` |")
        L.append("")
    L.append("- 같은 표가 「IX. 계열회사 등에 관한 사항」에도 실려 있어 칸 글을 맞대 봄: " + "; ".join(R["copy_diffs"] or ["두 사본 칸 글 같음"]) + "\n")
    L.extend(extra.get("conc_extra", []))

    # 6) 받은 것 / 받지 못한 것 / 다른 것
    L.append("## 6) 받은 것 · 받지 못한 것 · 원문과 다른 것\n")
    L.append("| 구분 | 항목 | 출처·방법 |\n|---|---|---|")
    for g in extra["got"]:
        L.append(f"| 받은 것 | {esc(g[0])} | {esc(g[1])} |")
    for g in extra["not_got"]:
        L.append(f"| 받지 못한 것 | {esc(g[0])} | {esc(g[1])} |")
    for g in extra["diffs"]:
        L.append(f"| 다른 것 | {esc(g[0])} | {esc(g[1])} |")
    L.append("")
    # 비평 보정: 「없음」 꼴(인용 「> 」 줄·``` 블록 밖) → 떨어진 줄을 이은 인용 블록 안 건너뜀 표지 → 보정 기록
    lines = md_fix("\n".join(L).split("\n"), f"{c} md")
    # 비평 보정 2: FIX2(한계 줄·기준일 칸) — 원문 인용(「> 」 줄)과 ``` 블록은 건드리지 않음
    code = False
    for i, x in enumerate(lines):
        if x.startswith("```"):
            code = not code
        elif not code and not x.startswith(">"):
            lines[i] = fix2(x, f"{c} md", md=True)
    # 7) 검증 기록 = 검증 반영 입력(검증 에이전트가 쓴 글). 지난 전 → 후 기록 줄(VR_KEEP)은 「없음」 보정도 하지 않음
    lines.append(R["VR"]["검증기록_제목"] + "\n")
    keep = VR_KEEP.get(c, ())
    body = R["VR"]["검증기록_줄"]
    for i, x in enumerate(body):
        if i in keep:
            assert "→" in x, (c, i, x[:40])
            lines.append(x)
        else:
            lines += md_fix([x], f"{c} md")
    lines.append("")
    lines, marks = gap_marks(lines)
    text = "\n".join(lines)
    assert text.endswith("\n")
    text += "\n" + "\n".join(fix_record(R, marks)) + "\n"
    text += "\n" + "\n".join(fix_record2(R)) + "\n"
    (MD_DIR / f"14_{c}.md").write_text(text, encoding="utf-8")


def fix_record2(R):
    """7) 끝 「비평 보정 2」 기록(critic14_2 대응 — 전 → 후 대표 예와 개수, 개수는 이번 실행에서 센 값)."""
    c = R["company"]
    n = {}
    for (where, old), k in FIX2N.items():
        if where.startswith(c + " "):
            n.setdefault(old, {})[where[len(c) + 1:]] = k
    mine = "[1]·[2]·[5]" if c == "신한금융지주" else "[2]·[5]"
    L = [f"### 비평 보정 2(critic14_2 대응, {FIX2_KST[:10]} KST)", "",
         f"비평 `dart_out/org14/critic14_2.json` new_issues 가운데 이 회사 몫({mine})과 메인이 정한 8개사 공통 꼴(한계 줄 · 공시인원 「{NONE}」 행의 찾은 방법 자리 · "
         "맡은 임원 「추출 범위에 없음」 행의 임원_겸직 · 기준일 칸 · CSV 열 이름)에 따라 생성기 `scripts/dart/org14_g1.py` 의 보정 표 2(FIX2 · RB2_MARK)로 다시 만듦"
         f"(산출물은 손으로 고치지 않음, 보정 시각 {FIX2_KST}). 위 「비평 보정」 기록과 7) 검증 기록의 지난 전 → 후 기록은 그대로(④), 원문 인용(「> 」 줄·``` 블록)·원문 칸 글도 그대로. "
         "`scripts/dart/verify14_g1.py` 에 검사 12~14 를 보태 exit 0 · 생성기 두 번 실행 md5 같음.", "",
         "| 바꾼 것 | 전 → 후(대표 예) | 개수 |", "|---|---|---|"]
    for old, new, rule, _ in FIX2:
        if old in n:
            cnt = " · ".join(f"{w} {k}" for w, k in n[old].items())
            L.append(f"| {esc(rule)} | 「{esc(old)}」 → 「{esc(new)}」 | {cnt} |")
    for old, new in RB2_MARK:
        if old in n:
            cnt = " · ".join(f"{w} {k}" for w, k in n[old].items())
            L.append(f"| 판독대조 CSV 판독B 칸 「없음」 꼴 → ②(critic14_2 [1] — g3·g4 와 같게; 판독 B JSON 은 그대로) | 「…{old}」 → 「…{new}」 | {cnt} |")
    L.append("| 지원조직 CSV 열 이름(8개사 공통 꼴) | 「주요 활동」 → 「주요 활동(원문)」 | 머리 1 |")
    ur = R["unit_rows"]
    hc = "공시인원(원문, 없으면 「추출 범위에 없음」)"
    nn = [r for r in ur if r[hc] == NONE]
    ok_src = sum(1 for r in nn if r["인원_출처"].startswith("찾은 방법: ") and not r["인원_내역(원문)"])
    ne = [r for r in ur if r["대응_임원(성명·직위)"] == NONE]
    ok_ne = sum(1 for r in ne if r["임원_겸직(원문: 겸직회사·직위·선임일·상근)"] == "해당 없음(대응 임원 추출 범위에 없음)")
    L.append(f"| 공시인원 「{NONE}」 행의 찾은 방법 자리(공통 꼴 — 바꾼 곳 0, 확인만) | 인원_출처 칸 「찾은 방법: …」 · 인원_내역(원문) 칸 빈칸 — 처음부터 이 꼴 | {ok_src}/{len(nn)}행 |")
    L.append(f"| 「{NONE}(직원 인원) — 위원 수는 인원_내역」 꼴 행(공통 꼴 — 바꾼 곳 0) | 이 회사 산출에는 이 꼴 행이 나오지 않음 — 위원회·이사회 행은 공시인원 칸에 위원 수 원문을 두고 인원_출처 연결 칸에 「(판단) 위원·이사 수이지 직원 수 아님」 류를 적음 | 0행 |")
    L.append(f"| 맡은 임원 「{NONE}」 행의 임원_겸직(공통 꼴 — 바꾼 곳 0, 확인만) | 「해당 없음(대응 임원 추출 범위에 없음)」 — 처음부터 이 꼴 | {ok_ne}/{len(ne)}행 |")
    L.append("| 임원겸직 CSV 열 이름(공통 꼴 — 바꾼 곳 0, 확인만) | 「출처(문서·접수번호·쪽)」 — 처음부터 이 이름 | 머리 1 |")
    L.append("| 검증 스크립트 검사 보탬·고침 | `scripts/dart/verify14_g1.py` 보탬: 12 한계 줄 꼴·「공시되지 않음」 류 단정 0 · 회사 CSV 열 이름 / 13 공시인원 「추출 범위에 없음」 행의 인원_출처 「찾은 방법:」·인원_내역 빈칸, 임원_겸직 꼴 / "
             "14 기준일 칸(지원조직 CSV 기준일 · 조직단위 CSV 인원_기준일 · md 3-6 기준일) = 원문 글 또는 「날짜(판단: …에 기준일 글이 나오지 않아 …로 둠)」 + 근거 문서 = 출처 문서. "
             "고침: 7 판독B 칸 = 판독 B JSON 그대로 또는 끝 「없음」 → ② 꼴만 허용, 「…없음」 으로 끝나는 판독B 칸은 문제로; 「주요 활동」 열 이름 2곳. "
             "고치기 전 산출(git HEAD ddac128 — 지원조직 CSV 머리만 새 열 이름으로 바꿔)에 돌리면 48건을 잡음(한계 줄 4 · 기준일 칸 42 · 판독B 칸 2) | 검사 3 보탬 · 2 고침 |")
    return L


# ───────────────────────── 회사별 덧붙임(받은 것·못 받은 것·차이) ─────────────────────────
def extras(R):
    c = R["company"]
    Q, ex = R["Q"], {}
    cp = R["chart_pairs"]
    if c == "KB금융지주":
        cnt = R["checks"]["판독집계"]
        ex["chart_check"] = [
            "### 1-1 머리글 집계와 판독 수 맞대기\n",
            f"- 머리글(판독) 「4부문 8담당(준법감시인 포함) 3본부 34부서*」, 각주(판독) 「* 연구소, 국, 실, 센터, Unit 포함」.",
            f"- 판독한 상자 수: 부문 {cnt['부문']} · 담당 {cnt['담당']}(준법감시인 포함) · 본부 {cnt['본부']} · 부서 {cnt['부서']} — "
            + ("머리글과 모두 맞음." if (cnt['부문'], cnt['담당'], cnt['본부'], cnt['부서']) == (4, 8, 3, 34) else "머리글과 다름(아래 참고)."),
            "- (판단) 부서 34 를 세는 법: 부·센터·Unit 이름 상자 30 + 각주가 말한 연구소(경영연구소)·실(비서실)·국(이사회사무국) 3 + 감사부 1. 부문·담당·본부 머리 상자와 회장·이사회·감사위원회, 고객·계열사 상자는 뺌.",
            "- 부서로 센 34개: " + ", ".join(cnt["부서_이름"]) + "\n",
        ]
        ex["emp_extra"] = [
            "**직원 겸직 숫자**: " + NONE + " — 찾은 방법: 사업보고서·연차보고서(본·추가)·경영공시 텍스트 전체에서 「겸직」「겸임」「겸직직원」「겸직 직원」「겸직인원」「겸직 인원」「(겸)」 검색(검색 결과 `dart_out/raw/org14/search/*__겸.txt`). 「겸직직원·겸직 직원·겸직인원」 0건.",
            "- 가까운 글(판단: 그룹 전 계열사 인력교류 숫자 — 지주 직원 겸직 숫자가 아님):\n",
            bq(Q["emp_exchange"]["text"]) + f"\n\n  {Q['emp_exchange']['src']}\n",
            "- 가까운 글(직원이 아니라 경영진·미등기임원 숫자):\n",
            bq(Q["ann_conc_217"]["text"]) + f"\n\n  {Q['ann_conc_217']['src']}\n",
            "- (판단) 위 「겸직 경영진 10명」과 사업보고서 미등기임원 보수 주석의 「원소속회사가 계열사인 미등기임원(2025.12.31 기준 10명)」은 같은 10명으로 보이나 원문이 같은 사람들이라고 적지는 않음.",
            "- 부서 단위 겸직 글(숫자 없음, 경영공시):\n",
            bq(Q["mgmt_model"]["text"]) + f"\n\n  {Q['mgmt_model']['src']}\n",
            "- 연차보고서 「준법감시직원 현황」:\n",
            bq(Q["ann_comp_208"]["text"]) + f"\n\n  {Q['ann_comp_208']['src']}\n",
        ]
        ex["other_quotes"] = [
            "### 3-7 사업보고서 — 조직개편 서술\n",
            bq(Q["reorg"]["text"]) + f"\n\n{Q['reorg']['src']}\n",
        ]
        ex["conc_extra"] = [
            "- 타회사 임원 겸임 현황(원문):\n", bq(Q["other_conc"]["text"]) + f"\n\n  {Q['other_conc']['src']}\n",
            "- KB 문서의 「(겸)」 쓰임(참고 — 조직도 표시가 아니라 경력 글): 사업보고서 임원 표 주요경력 칸에 「(겸)국민은행 기획조정부장」 같은 꼴 36줄(검색 결과 `dart_out/raw/org14/search/사업보고서__KB금융지주__20260313001191__겸.txt`), 연차보고서:\n",
            bq(Q["ann_gyeom_usage"]["text"]) + f"\n\n  {Q['ann_gyeom_usage']['src']}\n",
        ]
        got = [
            ("조직도 판독 A 54상자(머리글·각주 포함) · 집계 맞대기", f"경영공시 2026 2Q PDF p.6 · {R['readA']['url']}"),
            ("지주 직원 수 144(합계 행) · 주석", f"사업보고서 {R['cfg']['biz']} p.{R['emp']['쪽']}"),
            ("감사위원회 지원조직 표(감사부 15) · 준법감시인 지원조직 표(준법추진부 1 / 내부통제팀 6 / 법무·송무팀 4)", f"사업보고서 {R['cfg']['biz']} p.839~841"),
            ("사외이사 지원조직(이사회사무국: 사무국장 1명, 팀장 1명, 팀원 3명) 문장·역할", Q["bod_sec_biz"]["src"]),
            ("내부회계관리 운영조직 인력 표(회계부 총원 26 · IT기획부 7 · 재무기획부 22 등)", f"사업보고서 p.808"),
            ("연차보고서 조직도 글자 층 인원 6개 부서(감사부 15 · HR 부 14 · 리스크관리부 19 · ESG 사업부 11 · 이사회사무국 5 · 준법추진부 11)", Q["ann_chart"]["src"]),
            ("연차보고서 인원 서술(이사회사무국 총 5명 ×2 · 감사부 15명 · 리스크관리부 19명 · 준법추진부 11명 · 겸직 경영진 10명)", "연차보고서 p.121·132·157·214·217"),
            ("임원 표 32명(2025.12.31) + 작성기준일 이후 32명(2026.3.13) · 임원 겸직 표 17행 + 14행", f"사업보고서 p.851~869"),
            ("경영공시 모델검증부서 「(지주사 및 은행 겸직)」 글", Q["mgmt_model"]["src"]),
        ]
        not_got = [
            ("일반 부서(부·센터·Unit 대부분) 인원", "사업보고서 지원조직 표·내부회계 표, 연차보고서 조직도·서술, 경영공시 전문에서 단위 이름+인원 숫자 검색 — 위 9개 단위 밖은 나오지 않음"),
            ("직원 겸직 숫자(겸직직원 수)", "세 문서 「겸직」「겸임」「겸직직원」「겸직 직원」「겸직인원」 검색 — 0건(경영진 10명·미등기임원 10명만 있음)"),
            ("경영공시 2026 2Q 임직원 수", "경영공시 텍스트 p.1~204 「임직원」「직원」「인원」 검색 — 지주 임직원 수 글 없음(목차 일반현황은 조직 및 영업점뿐)"),
            ("조직도의 겸직 표시", "조직도 판독 — KB 조직도에는 「(겸)」 등 겸직 표시가 나오지 않음(판독)"),
        ]
        diffs = [
            ("조직 이름: 2025.12.31 임원 표 담당업무 「디지털부문장」「IT부문장」「IR본부장」「보험사업담당」「글로벌사업부문장」「AIㆍ디지털본부장」「감사담당」", "2026.8 조직도(판독)에 같은 이름 없음 — 2026.1.1 조직개편·임원 변동(작성기준일 이후 변동 표) 때문으로 봄(판단). 작성기준일 이후(2026.3.13) 표는 조직도 이름과 대부분 글자 그대로 맞음"),
            ("연차보고서 조직도 「HR 부」「ESG 사업부」 ↔ 경영공시 조직도(판독) 「HR부」「ESG사업부」", "띄어쓰기만 다름(기준일도 2025.12.31 ↔ 2026년 08월)"),
            ("준법추진부 인원: 사업보고서 표 1+6+4 행 ↔ 연차보고서 「11명(변호사 4명 포함)」·조직도 「(11 명)」", "(판단) 합 11 로 맞음 — 사업보고서 표에는 합계 숫자 없음"),
            ("겸직 표 사본(VIII장 ↔ IX장)", "; ".join(R["copy_diffs"]) or "같음"),
        ] + [(f"사업보고서 정정판 {x['rcept']} ({x['title']})", f"{x['방법']} → {x['결과']}") for x in R["corr"]]
    else:
        ex["chart_check"] = [
            "### 1-1 「(겸)」 표시 판독과 뜻 찾기\n",
            "- 「(겸)」이 붙은 단위(판독, 8곳): " + ", ".join(f"{u['단위']} {u['겸직표시']}" for u in R["marks"]) + ".",
            "- 「(겸)」의 뜻이 적힌 곳: " + NONE + " — 찾은 방법: 경영공시(p.1~145)·연차보고서 본·추가(p.1~316)·사업보고서(p.1~1065) 텍스트에서 「(겸)」 검색 0건, 「겸직」「겸임」 검색(결과 `dart_out/raw/org14/search/*신한*__겸.txt`). 조직도 쪽(p.6)에도 범례·각주 글 나오지 않음(판독).",
            "- 가장 가까운 글(단위 하나에 대한 겸직 서술, 경영공시):\n",
            bq(Q["mgmt_model"]["text"]) + f"\n\n  {Q['mgmt_model']['src']}\n",
            "- (판단) 조직도에서 「(겸)」 단위를 맡은 임원은 겸직 표에서 신한은행 상근 겸직이 나옴: AX·디지털부문 ↔ 최혁재(그룹AXㆍ디지털부문, 신한은행 부행장 2025.10.01 상근), 소비자보호 부문 ↔ 박현주(그룹소비자보호부문, 신한은행 부행장 2022.01.01 상근). 모형검증팀은 경영공시 「모형검증팀(은행 겸직)」. 그래서 「(겸)」 = 신한은행 겸직 단위로 읽히나, 이 뜻을 적은 원문은 없음. 팀 단위(브랜드전략팀·SDGs기획팀·사회공헌팀·소비자보호팀·여신감리팀)의 겸직 상대 회사·인원은 " + NONE + ".",
            "- 조직도 안 집계 글(「○부문 ○팀」)·각주: 나오지 않음(판독).\n",
        ]
        ex["emp_extra"] = [
            "**연차보고서의 전 직원 수 · 준법감시직원 수**(「겸직 포함」 글이 붙은 유일한 직원 수):\n",
            bq(Q["ann_emp_200"]["text"]) + f"\n\n  {Q['ann_emp_200']['src']}\n",
            bq(Q["ann_comp_201"]["text"]) + f"\n\n  {Q['ann_comp_201']['src']}\n",
            "**직원 겸직 숫자**: " + NONE + " — 찾은 방법: 세 문서에서 「겸직」「겸임」「겸직직원」「겸직 직원」「겸직인원」「겸직 인원」「(겸)」 검색. 「겸직직원·겸직 직원·겸직인원」 0건. 연차보고서 p.201 「총 임직원 수 252 임원 제외 / 겸직 포함」은 겸직을 넣은 총수일 뿐 겸직 인원 숫자는 나오지 않음.",
            "- (판단) 사업보고서 직원 수 195(「직원 수는 월별 평균 근무인원의 12개월 평균」, 미등기임원 포함)와 연차보고서 252(「임원 제외 / 겸직 포함」, 2025년말)의 차 57명을 겸직 직원 수로 볼 수는 없음 — 셈하는 법(평균 ↔ 연말, 임원 포함 여부)이 달라서.",
            "- 사업보고서 미등기임원 보수 표 주석「겸직 경영진의 경우 … 원 소속사에서 공시」(위 인용)는 겸직 경영진이 있다는 글이나 숫자는 없음.\n",
        ]
        ex["other_quotes"] = [
            "### 3-7 사업보고서 — 2026년 조직 운영 서술\n",
            bq(Q["org_773"]["text"]) + f"\n\n{Q['org_773']['src']}\n",
        ]
        ex["conc_extra"] = [
            "- 겸직 표에는 나오지만 임원 표(2025.12.31 / 2026.3.18)에는 없는 사람(직원 신분 겸직으로 보임 (판단)): 기준일 표 황경업·고유선·이원태·김원길, 이후 표 고유선·이원태·한동영·최종윤·구교영·장선형·김원길·김동우·윤원희. 황경업은 사업보고서 p.812 회계담당자 표에 「회계파트장」으로 나옴 → 조직도 「회계 파트」 (판단).",
            "- 연차보고서 서술(임원 겸직):\n", bq(Q["ann_conc_33"]["text"]) + f"\n\n  {Q['ann_conc_33']['src']}\n",
        ]
        got = [
            ("조직도 판독 A 50상자 · 「(겸)」 8곳(부문 2·팀 6)", f"경영공시 2026 2Q PDF p.6 · {R['readA']['url']}"),
            ("지주 직원 수 195(합계 행) · 주석 주1~주5", f"사업보고서 {R['cfg']['biz']} p.{R['emp']['쪽']}"),
            ("감사위원회 지원조직 표(감사팀 10) · 준법지원인 지원조직 표(준법지원팀 11) · 표 주석", f"사업보고서 {R['cfg']['biz']} p.837~838"),
            ("사외이사 지원조직(이사회사무국: 사무국장과 2명의 책임자급 직원) 문장·역할", Q["bod_sec_biz"]["src"]),
            ("내부회계관리 운영조직 인력 표(회계파트 1 · 회계처리부서 12 · 내부회계관리담당부서 4 · 자금운영부서 12 · 전산운영부서 4 등)", "사업보고서 p.811~812"),
            ("연차보고서 조직도 글자 층 인원 7개(이사회사무국 3 · 리스크관리팀 14 · SDGs기획팀 6 · 전략기획팀 16 · 감사팀 10 · 신한리더십센터 10 · 「준법지원획팀」 10)", Q["ann_chart"]["src"]),
            ("연차보고서 인원 서술(이사회사무국 · 신한리더십센터 10 · 회추위사무국 6 · 감사팀 구성 · 전직원 252 · 준법감시직원 10)", "연차보고서 p.90·129·138·157·185·200·201"),
            ("임원 표 20명(2025.12.31) + 작성기준일 이후 20명(2026.3.18) · 임원 겸직 표 23행 + 23행", "사업보고서 p.847~853"),
            ("「(겸)」 단위와 겸직 임원 맞대기 · 경영공시 「모형검증팀(은행 겸직)」", Q["mgmt_model"]["src"]),
        ]
        not_got = [
            ("「(겸)」 표시의 뜻(범례·정의 글)", "경영공시·연차보고서(본·추가)·사업보고서 텍스트 「(겸)」 0건, 「겸직」「겸임」 검색 — 정의 글 없음"),
            ("「(겸)」 팀의 겸직 상대 회사·겸직 인원", "같은 검색 — 모형검증팀만 「은행 겸직」 글 있음(인원 숫자 없음)"),
            ("일반 팀 인원(재무팀·회계팀·IR팀·사업지원팀·디지털전략팀 등)", "사업보고서 지원조직 표·내부회계 표, 연차보고서 조직도·서술, 경영공시 전문 검색 — 나오지 않음"),
            ("직원 겸직 숫자", "세 문서 「겸직직원」「겸직 직원」「겸직인원」 0건 — 연차보고서 252명은 「겸직 포함」 총수"),
            ("경영공시 2026 2Q 임직원 수", "경영공시 텍스트 p.1~145 「임직원」「직원」「인원」 검색 — 지주 임직원 수 글 없음"),
            ("미래전략연구소·리스크관리 파트 사이 선의 뜻", "조직도 600dpi 확대로도 상하 관계 확정 못 함(판독) — 사업보고서 p.773 은 두 조직을 나란히 적음"),
        ]
        diffs = [
            ("겸직 표 사본(VIII장 ↔ IX장)", "; ".join(R["copy_diffs"]) or "같음"),
            ("준법지원팀 인원: 사업보고서 표 11(2025.12.31) ↔ 연차보고서 조직도 「준법지원획팀 (10명)」(2026.1월초 조직개편 반영 기준) ↔ 준법감시직원 수 10(2025년말, 준법감시인 제외)", "기준일·셈하는 법이 다름; 연차보고서 조직도 이름 「준법지원획팀」은 경영공시 조직도(판독) 「준법지원팀」과 다름(판단: 오기)"),
            ("이사회사무국: 연차보고서 조직도 「(3명)」 ↔ 사업보고서 「사무국장과 2명의 책임자급 직원」", "(판단) 1+2=3 으로 맞음"),
            ("지주 직원 수: 사업보고서 195 ↔ 연차보고서 전직원 252(임원 제외 / 겸직 포함)", "셈하는 법 다름(위 2) 참고)"),
            ("조직 이름: 조직도(판독) 「AX·디지털부문」「전략 부문」「재무 부문」「운영 부문」「소비자보호 부문」「감사 파트」「리스크관리 파트」 ↔ 사업보고서 임원 표 「그룹AXㆍ디지털부문」「그룹 전략부문」「그룹재무부문」「그룹 운영부문」「그룹소비자보호부문」「감사파트」「그룹 리스크관리파트」", "띄어쓰기·「그룹」 붙임·가운뎃점만 다름 → 대응 방식 (판단)"),
            ("CRO: 2025.12.31 표 방동권 「파트장(부사장)」 「그룹 리스크관리파트 (CRO)」 ↔ 2026.3.18 표 나훈 「파트장 (상무)」 「리스크관리파트 (CRO)」", "작성기준일 이후 바뀜"),
            ("CFO: 2025.12.31 표 천상영 ↔ 2026.3.18 표 장정훈 「그룹재무부문 (CFO)」", "작성기준일 이후 바뀜"),
        ]
    # 비평 보정: 빠진 가까운 글(받은 것) · 맡은 임원(받지 못한 것)
    if c == "KB금융지주":
        got.append(("가까운 글: 그룹 전 계열사 인력교류 총 163명(2025년, 「(2) 종업원에 관한 사항」) — (판단) 지주 직원 겸직 숫자가 아님", Q["emp_exchange"]["src"]))
    else:
        got.append(("신한리더십센터 「팀장과 팀원 10명」(대표이사 회장 승계업무 지원부서) — (판단) 총 10명 또는 팀장 1명+팀원 10명으로 읽힘", Q["ann_succ_137"]["src"]))
    ne = R["no_exec"]
    n0 = [u["단위"] for u, h in ne if h == 0]
    nh = [u["단위"] for u, h in ne if h]
    eb, ea = R["execs"]["기준일"], R["execs"]["이후"]
    not_got.append((f"맡은 임원(조직도 단위 {len(ne)}곳)",
                    f"{NONE} — 찾은 방법: 사업보고서 {R['cfg']['biz']} 임원 표 {eb['basis']} {len(eb['rows'])}명·작성기준일 이후 임원 표 {ea['basis']} {len(ea['rows'])}명의 "
                    f"담당업무에서 단위 이름 글자 검색(띄어쓰기·가운뎃점·「그룹」 붙임 무시) — {len(n0)}곳 0건(" + "·".join(n0) + ")"
                    + (f"; {len(nh)}곳(" + "·".join(nh) + ")은 다른 낱말 안에 걸림 — (판단) 도식 상자라 대응하지 않음" if nh else "")
                    + ". 단위별 결과는 조직단위 CSV 대응_근거 칸"))
    # 검증 에이전트가 6) 표에 보태거나 바꾼 행(검증 반영 입력)
    lists = {"받은 것": got, "받지 못한 것": not_got, "다른 것": diffs}
    for x in R["VR"]["md_6_바꿈"]:
        lst = lists[x["구분"]]
        k = [i for i, g in enumerate(lst) if g[0] == x["전_항목"]]
        if len(k) != 1:
            raise SystemExit(f"[6) 바꿀 행 못 찾음] {c}: {x['전_항목']}")
        lst[k[0]] = (x["항목"], x["출처·방법"])
    for x in R["VR"]["md_6_보탬"]:
        lists[x["구분"]].append((x["항목"], x["출처·방법"]))
    ex["got"], ex["not_got"], ex["diffs"] = got, not_got, diffs
    return ex


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MD_DIR.mkdir(parents=True, exist_ok=True)
    allchk = {"작업시각": load_vr(next(iter(CFG)))["작업일_KST"], "companies": []}
    for company, cfg in CFG.items():
        R = run_company(company, cfg)
        ex = extras(R)
        write_md(R, ex)
        R["checks"]["got"] = ex["got"]
        R["checks"]["not_got"] = ex["not_got"]
        R["checks"]["diffs"] = ex["diffs"]
        R["checks"]["인용"] = {k: dict(pages=v["pages"], lines=v["lines"], doc=v["doc"], ann_add=v.get("ann_add_same", "")) for k, v in R["Q"].items()}
        allchk["companies"].append(R["checks"])
        print(company, json.dumps(R["counts"], ensure_ascii=False), "문제", len(R["checks"]["problems"]))
        for p in R["checks"]["problems"]:
            print("  !", p)
    (OUT_DIR / "g1_검사.json").write_text(json.dumps(allchk, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
