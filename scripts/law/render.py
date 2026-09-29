# -*- coding: utf-8 -*-
"""본문 XML → HTML → PDF (사용자 결정 ① — (가) XML 직접 렌더링이 기본).

목적이 조문 인용이므로 **모양보다 조문이 빠짐없이 들어 있는지**가 중요하다. 그래서
공식 본문 XML의 조문·항·호·목·부칙 텍스트를 **원문 그대로**(공백 접기도 하지
않는다 — CSS pre-wrap) HTML로 옮기고, Chromium headless 로 오프라인 인쇄한다.
네트워크를 쓰지 않으므로 같은 XML 이면 같은 글자가 찍힌다(단 Chromium 이 PDF 에
생성 시각을 넣으므로 **sha256 은 찍을 때마다 바뀐다** — 다시 찍으면 manifest 를 갱신).
verify7 이 PDF 텍스트에 모든 조문 표지가 들어 있는지 기계로 확인한다.

별표·서식은 본문 PDF 에 **목록만** 싣는다(annex_index_html). 내용은 법제처 원본
PDF(없으면 HWP)로 따로 받고, 원본 링크가 아예 없는 것만 annex_text_html 로 따로 찍는다.

모든 PDF 첫 쪽 머리에 출처를 찍는다(사용자 요청):
  「법제처 Open API 원문 XML 렌더링 · 시행일 YYYY-MM-DD · 법령일련번호 NNN」

■ 법제처가 준 별표·서식 원본 PDF 에는 아무것도 찍지 않는다 — 그것은 원문이다.
  도장은 **우리가 렌더링한** 본문·체계도·(원본 없는) 별표 PDF 에만 찍는다.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
)
# 폰트·용지 — 법제처 사이트 「저장 > 용지/폰트 설정」 기본값에 맞춘다(사용자 요청):
#   법령명/조번호 = 견고딕 · 조문내용 = 신명조 · 조문 10pt · 여백 상20 좌15 우15 하15(mm)
#   부가정보(표지·개정문|개정이유) 저장 안 함
# 견고딕·신명조는 한양(HY) 독점 폰트라 공개 경로로 받을 수 없다. 사용자가 HY견고딕·
# HY신명조 TTF 를 올려 ~/.fonts 에 넣으면 첫 순위로 잡힌다. 없으면 무료 대체:
#   견고딕 → Noto Sans KR Bold,  신명조 → Noto Serif KR   (둘 다 SIL OFL)
# (앞서 요청한 맑은고딕으로 통일하려면 GOTHIC·SERIF 첫 항목을 "Malgun Gothic" 으로.)
GOTHIC = ('"HY견고딕", "HYGothic-Extra", "HYGothic", "견고딕", "Noto Sans KR", '
          '"Noto Sans CJK KR", "NanumGothic", sans-serif')
SERIF = ('"HY신명조", "HYSinMyeongJo-Medium", "HYSinMyeongJo", "신명조", "Noto Serif KR", '
         '"Noto Serif CJK KR", "NanumMyeongjo", serif')
FONT_STACK = SERIF
# 별표내용 텍스트는 고정폭으로 짠 글이다(한글 2칸·영숫자 1칸). 원본 파일이 없어 이 글을
# 따로 찍어야 할 때만 쓴다 — 한글이 영문 두 배 폭인 CJK 고정폭이라야 줄이 맞는다.
MONO = ('"D2Coding", "Noto Sans Mono CJK KR", "NanumGothicCoding", '
        '"WenQuanYi Zen Hei Mono", monospace')

CSS = """
@page { size: A4; margin: 20mm 15mm 15mm 15mm; }
body { font-family: %(serif)s; font-size: 10pt; line-height: 1.6; color: #111; }
.stamp { font-family: %(gothic)s; border: 1px solid #555; padding: 5px 9px; font-size: 8.6pt;
         color: #222; background: #f4f4f4; margin-bottom: 10px; }
.stamp b { font-weight: 700; }
h1 { font-family: %(gothic)s; font-weight: 700; font-size: 15pt; margin: 6px 0 2px 0; }
.meta { font-family: %(gothic)s; font-size: 8.4pt; color: #444; margin-bottom: 12px; }
.meta td { padding: 1px 10px 1px 0; vertical-align: top; }
h2 { font-family: %(gothic)s; font-weight: 700; font-size: 11.5pt; margin: 14px 0 6px 0;
     border-bottom: 1px solid #999; }
.chap { font-family: %(gothic)s; font-weight: 700; margin: 12px 0 4px 0; }
.jo { font-family: %(gothic)s; font-weight: 700; }
.art { margin: 0 0 7px 0; }
.t { white-space: pre-wrap; word-break: break-all; }
.hang { margin-left: 1.0em; }
.ho { margin-left: 2.0em; }
.mok { margin-left: 3.0em; }
.bu { margin: 0 0 9px 0; }
.bu .hd, .byl .hd { font-family: %(gothic)s; font-weight: 700; }
.byl { margin: 0 0 12px 0; page-break-inside: auto; }
.byl pre { white-space: pre-wrap; word-break: break-all; font-family: inherit;
           font-size: 9pt; margin: 3px 0 0 0; }
.axnote { font-family: %(gothic)s; font-size: 8.6pt; color: #333; margin: 0 0 6px 0; }
table.ax { border-collapse: collapse; width: 100%%; font-size: 8.6pt; table-layout: fixed; }
table.ax col.k { width: 3.2em; } table.ax col.n { width: 5em; }
table.ax col.d { width: 6.4em; } table.ax col.f { width: 42%%; }
table.ax td.k, table.ax td.d, table.ax th { white-space: nowrap; }
table.ax th { font-family: %(gothic)s; font-weight: 700; background: #eee; }
table.ax th, table.ax td { border: 1px solid #999; padding: 2px 5px; vertical-align: top;
                           text-align: left; word-break: break-all; }
table.ax td.f { font-family: %(gothic)s; font-size: 7.6pt; color: #333; }
pre.axraw { font-family: %(mono)s; font-size: 8.4pt; line-height: 1.35;
            white-space: pre-wrap; word-break: break-all; margin: 0; }
""" % {"serif": SERIF, "gothic": GOTHIC, "mono": MONO}

# 「제5조의2(인가받을 의무 등)」 머리. 조번호는 견고딕으로 찍되 **글자는 바꾸지 않는다**
# (span 으로 감쌀 뿐이라 PDF 텍스트는 원문과 같다 — verify7 의 조문표지 대조가 그대로 유효).
_JO = re.compile(r"^(\s*제\s*\d+(?:\s*-\s*\d+)*\s*조(?:\s*의\s*\d+)?(?:\s*[（(][^)）]*[)）])?)")
# 행정규칙 조문 머리 — 「제5조(…)」「제1-1조(…)」「제2조의2(…)」「제2조 삭제」. 괄호·「<」·
# 「삭제」가 바로 뒤따를 때만 머리로 본다(문장 첫머리의 「제3조에 따라」를 머리로 잡지 않게).
_RULE_HEAD = re.compile(r"^\s*(제\s*\d+(?:\s*-\s*\d+)*\s*조(?:\s*의\s*\d+)?)(?=\s*[（(<〈]|\s*삭\s*제)")
_RULE_CHAP = re.compile(r"^\s*제\s*\d+(?:\s*-\s*\d+)*\s*[편장절관](?:\s*의\s*\d+)?\s")


def _jo_html(txt):
    m = _JO.match(txt or "")
    if not m:
        return _esc(txt)
    return '<span class="jo">%s</span>%s' % (_esc(m.group(1)), _esc(txt[m.end():]))


def chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("Chromium headless 가 없습니다: %s" % ", ".join(CHROME_CANDIDATES))


def _t(e, tag):
    x = e.find(tag)
    return (x.text or "").strip() if x is not None and x.text else ""


def _esc(s):
    return html.escape(s or "", quote=False)


def _fmt_date(d):
    d = (d or "").strip()
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if len(d) == 8 and d.isdigit() else d


def stamp_html(kind, efyd, serial, pending=False, extra=""):
    """첫 쪽 머리 도장. kind: '원문 XML 렌더링' / '체계도(lsStmd) 렌더링'."""
    label = "행정규칙일련번호" if extra == "행정규칙" else "법령일련번호"
    s = "법제처 Open API %s · 시행일 %s · %s %s" % (kind, _fmt_date(efyd), label, serial)
    if pending:
        s += " · <b>시행예정</b>"
    return '<div class="stamp">%s</div>' % s


# ── 별표·서식 ─────────────────────────────────────────────────────────────
# 본문 PDF 에는 별표·서식의 **목록만** 싣는다(사용자 요청 2026-09-29). 별표내용 필드는
# HWP 를 고정폭 텍스트로 떠낸 글이라 비례폭 글꼴로 찍으면 표·줄맞춤이 무너진다. 내용은
# 법제처가 준 원본 PDF(없으면 HWP)로 따로 저장하고, 원본 파일이 아예 없는 것만
# annex_text_html 로 따로 찍는다. 별표내용 텍스트 자체는 원문 XML 에 그대로 남아 있다.
def annex_units(root):
    """XML 순서 그대로의 별표단위 목록(법령 XML·행정규칙 XML 공통)."""
    return list(root.iter("별표단위"))


def is_rule_root(root):
    return root.tag == "AdmRulService"


def annex_no(unit, rule=False):
    """별표 번호 표기. 법령은 「1의2」, 행정규칙은 원문 표기대로 「1-2」(실측: 금융지주회사
    감독규정 〈별표1-2〉, 외국환거래규정 [별지 제2-1호 서식])."""
    num = (_t(unit, "별표번호").lstrip("0") or "0")
    gaji = _t(unit, "별표가지번호").lstrip("0")
    return num + (("-%s" if rule else "의%s") % gaji if gaji else "")


def annex_index_html(root, annex_files=None):
    """별표·서식 목록 표. annex_files: XML 순서와 같은 [(저장 파일명, 상태)] — 없으면 빈칸.

    목록 줄 수 ≠ 파일 목록 수면 짝이 틀어진 것이므로 찍지 않고 멈춘다(엉뚱한 파일명을
    다른 별표 옆에 적는 것보다 낫다). 머리 설명은 실제 저장 결과를 센 숫자로 쓴다.
    """
    units = annex_units(root)
    if not units:
        return []
    rule = is_rule_root(root)
    files = list(annex_files) if annex_files is not None else [("", "")] * len(units)
    if len(files) != len(units):
        raise ValueError("별표 목록 %d건 ≠ 파일 목록 %d건" % (len(units), len(files)))
    kinds = {}
    for u in units:
        k = _t(u, "별표구분") or "별표"
        kinds[k] = kinds.get(k, 0) + 1
    got = {"원본 PDF": 0, "원본 HWP": 0, "XML 렌더링": 0, "파일 없음": 0}
    for fname, state in files:
        if not fname:
            got["파일 없음"] += 1
        elif fname.endswith("_XML렌더링.pdf"):
            got["XML 렌더링"] += 1
        elif fname.lower().endswith((".hwp", ".hwpx")):
            got["원본 HWP"] += 1
        else:
            got["원본 PDF"] += 1
    head = " · ".join("%s %d건" % (k, n) for k, n in kinds.items())
    saved = " · ".join("%s %d" % (k, n) for k, n in got.items() if n)
    out = ["<h2>별표·서식</h2>",
           '<div class="axnote">%s. 내용은 이 PDF에 싣지 않고 따로 저장했다(같은 폴더의 '
           "별표/·서식/) — %s. 「원본」은 법제처가 제공한 파일 그대로이고, 「XML 렌더링」은 "
           "원본 링크가 없어 원문 XML의 별표내용을 따로 찍은 것이다.</div>" % (head, saved),
           '<table class="ax"><colgroup><col class="k"><col class="n"><col><col class="d">'
           '<col class="f"></colgroup><tr><th>구분</th><th>번호</th><th>제목</th>'
           "<th>시행일</th><th>저장 파일</th></tr>"]
    for u, (fname, state) in zip(units, files):
        cell = _esc(fname) if fname else "(%s)" % _esc(state or "파일 없음")
        if fname and state and state not in ("OK",):
            cell += " · %s" % _esc(state)
        out.append('<tr><td class="k">%s</td><td class="n">%s</td><td>%s</td><td class="d">%s</td>'
                   '<td class="f">%s</td></tr>'
                   % (_esc(_t(u, "별표구분") or "별표"), annex_no(u, rule),
                      _esc(_title(u)), _fmt_date(_t(u, "별표시행일자")), cell))
    out.append("</table>")
    return out


def annex_text_html(unit, law_name, efyd, serial, pending=False, extra=""):
    """원본 PDF·HWP 가 없는 별표 하나를 원문 XML 별표내용으로 따로 찍는다(글자 그대로).

    법제처 XML 은 별표내용을 줄마다 CDATA 하나로 싣고 줄 사이에 빈 CDATA 를 끼운다
    (실측: 금융지주회사법 시행령 별표 11건 모두 홀수 번째 줄이 빈 줄). 그대로 찍으면
    줄마다 빈 줄이 끼어 표의 세로선이 끊기므로, **홀수 번째 줄이 전부 비었을 때만** 그
    빈 줄을 접고 그 사실을 PDF 머리에 적는다. 글자는 바꾸지 않고, 원문 XML 은 그대로다.
    """
    rule = extra == "행정규칙"
    kind = _t(unit, "별표구분") or "별표"
    head = "%s [%s %s]" % (law_name, kind, annex_no(unit, rule))
    text = _raw(unit, "별표내용")
    lines = text.split("\n")
    folded = len(lines) > 2 and all(not x.strip() for x in lines[1::2])
    if folded:
        text = "\n".join(lines[0::2])
    note = "%s · [%s %s] · %s · 별표시행일 %s" % (law_name, kind, annex_no(unit, rule), _title(unit),
                                             _fmt_date(_t(unit, "별표시행일자")) or "(XML에 없음)")
    if folded:
        note += " · XML 줄 구분용 빈 줄 %d개를 접음(글자는 원문 그대로)" % len(lines[1::2])
    return "\n".join([
        "<!doctype html><html><head><meta charset='utf-8'><title>%s</title>"
        "<style>%s</style></head><body>" % (_esc(head), CSS),
        stamp_html("원문 XML 별표내용 렌더링(원본 파일 없음)", efyd, serial, pending, extra),
        '<div class="axnote">%s</div>' % _esc(note),
        '<pre class="axraw">%s</pre>' % _esc(text),
        "</body></html>"])


def _title(unit):
    """별표제목 표시용. 법제처 XML 은 CDATA 안에 엔티티를 글자로 넣어 둔다(실측:
    `<![CDATA[삭제 &lt;2016. 7. 28.&gt;]]>`). 같은 XML 의 별표제목문자열 필드가 푼 꼴을
    주므로 그것을 쓰고, 그 필드가 없는 XML(행정규칙)에서만 한 번 푼다. **PDF 에 찍을 때만**
    이렇게 하고, 원문 XML·manifest 의 제목은 받은 그대로 둔다."""
    return _t(unit, "별표제목문자열") or html.unescape(_t(unit, "별표제목"))


def label_check(labels, pdf_text):
    """조문 표지가 PDF 에 **조 머리 꼴로** 있는가. → (누락, 본문 속 언급만 있는 것).

    「제1조」를 그냥 부분 문자열로 찾으면 「제1조의2」·「제2조제1항」·부칙의 「제1조(시행일)」
    안에서도 걸려 누락을 못 잡는다. 그래서 (1) 첫 「부칙」 제목 줄 앞까지만 보고, (2) **줄
    머리**에서 표지로 시작하고 바로 뒤가 줄 끝·공백·「(」·「[」·「<」·「〈」·「삭제」인 곳만 조
    머리로 센다(뒤에 숫자·「의숫자」가 오면 다른 조). 렌더링이 조마다 새 줄에서 시작하므로
    줄 머리가 곧 조 머리다. 실측: 원문 XML 에 제목 없이 「제24조」만 있는 조(자본시장법
    시행령), 대괄호 제목 「제28조[…]」(전자등록법)도 있다 — 둘 다 조 머리다.
    머리 꼴은 없지만 글자는 있는 표지는 따로 돌려준다 — 조용히 통과시키지 않는다.
    """
    lines = pdf_text.split("\n")
    cut = len(lines)
    for i, ln in enumerate(lines):
        if ln.strip() == "부칙" and i > 0:
            cut = i
            break
    heads = [re.sub(r"\s+", "", ln) for ln in lines[:cut]]
    flat_all = re.sub(r"\s+", "", pdf_text)
    miss, weak = [], []
    for l in labels:
        pat = re.compile(re.escape(l) + r"(?![0-9]|의[0-9])(?:$|[（(\[<〈]|삭제)")
        if any(h.startswith(l) and pat.match(h) for h in heads):
            continue
        (weak if l in flat_all else miss).append(l)
    return miss, weak


def _raw(e, tag):
    """앞뒤 공백을 자르지 않은 원문(고정폭 줄맞춤 보존)."""
    x = e.find(tag)
    return x.text if x is not None and x.text else ""


# ── 법령(법률·시행령·시행규칙) ────────────────────────────────────────────
def _render_children(e, out, level):
    """항 → 호 → 목. 태그 이름으로 내려가며 내용 텍스트를 그대로 싣는다."""
    for child in e:
        tag = child.tag
        if tag == "항":
            txt = _t(child, "항내용")
            if txt:
                out.append('<div class="hang t">%s</div>' % _esc(txt))
            _render_children(child, out, level + 1)
        elif tag == "호":
            txt = _t(child, "호내용")
            if txt:
                out.append('<div class="ho t">%s</div>' % _esc(txt))
            _render_children(child, out, level + 1)
        elif tag == "목":
            txt = _t(child, "목내용")
            if txt:
                out.append('<div class="mok t">%s</div>' % _esc(txt))
            _render_children(child, out, level + 1)


def article_labels(root):
    """XML 에 있는 조문 표지(「제5조의2」 꼴) 목록 — verify7 이 PDF 텍스트와 대조한다."""
    labels = []
    for u in root.iter("조문단위"):
        if _t(u, "조문여부") != "조문":
            continue
        n, g = _t(u, "조문번호"), _t(u, "조문가지번호")
        if n:
            labels.append("제%s조%s" % (n, ("의%s" % g) if g and g != "0" else ""))
    return labels


def law_html(xml_bytes, efyd, serial, pending=False, annex_files=None):
    root = ET.fromstring(xml_bytes)
    bi = root.find("기본정보")
    name = _t(bi, "법령명_한글") if bi is not None else ""
    meta_rows = []
    if bi is not None:
        for k in ("법령ID", "법종구분", "공포일자", "공포번호", "시행일자", "제개정구분", "소관부처"):
            v = _t(bi, k)
            if v:
                meta_rows.append("<tr><td>%s</td><td>%s</td></tr>" % (k, _esc(v)))
    out = ["<!doctype html><html><head><meta charset='utf-8'><title>%s</title>"
           "<style>%s</style></head><body>" % (_esc(name), CSS),
           stamp_html("원문 XML 렌더링", efyd, serial, pending),
           "<h1>%s</h1>" % _esc(name),
           '<table class="meta">%s</table>' % "".join(meta_rows),
           "<h2>조문</h2>"]
    jo = root.find("조문")
    for u in (jo if jo is not None else []):
        if u.tag != "조문단위":
            continue
        txt = _t(u, "조문내용")
        if _t(u, "조문여부") == "전문":            # 장·절·관 제목
            out.append('<div class="chap t">%s</div>' % _esc(txt))
            continue
        out.append('<div class="art"><div class="t">%s</div>' % _jo_html(txt))
        _render_children(u, out, 1)
        out.append("</div>")
    bu = root.find("부칙")
    if bu is not None and len(bu):
        out.append("<h2>부칙</h2>")
        for b in bu:
            if b.tag != "부칙단위":
                continue
            hd = "부칙 〈%s, %s〉" % (_t(b, "부칙공포번호"), _fmt_date(_t(b, "부칙공포일자")))
            body = "\n".join((x.text or "").strip() for x in b.findall("부칙내용") if x.text)
            out.append('<div class="bu"><div class="hd">%s</div><div class="t">%s</div></div>'
                       % (_esc(hd), _esc(body)))
    out.extend(annex_index_html(root, annex_files))
    out.append("</body></html>")
    return "\n".join(out), name, article_labels(root)


# ── 행정규칙 ──────────────────────────────────────────────────────────────
def admrul_html(xml_bytes, efyd, serial, pending=False, annex_files=None):
    root = ET.fromstring(xml_bytes)
    bi = root.find("행정규칙기본정보")
    name = _t(bi, "행정규칙명") if bi is not None else ""
    meta_rows = []
    if bi is not None:
        for k in ("행정규칙ID", "행정규칙종류", "발령일자", "발령번호", "시행일자",
                  "제개정구분명", "소관부처명"):
            v = _t(bi, k)
            if v:
                meta_rows.append("<tr><td>%s</td><td>%s</td></tr>" % (k, _esc(v)))
    out = ["<!doctype html><html><head><meta charset='utf-8'><title>%s</title>"
           "<style>%s</style></head><body>" % (_esc(name), CSS),
           stamp_html("원문 XML 렌더링", efyd, serial, pending, extra="행정규칙"),
           "<h1>%s</h1>" % _esc(name),
           '<table class="meta">%s</table>' % "".join(meta_rows),
           "<h2>조문</h2>"]
    # 조문내용 한 요소가 조 하나인 규정(금융지주회사감독규정 104요소)도 있고, 규정 전체가
    # 한 요소에 든 것(외국환거래규정 1요소·18만 자·「제1-1조」 208개)도 있다. 그래서
    # 줄 단위로 조 머리·장절 머리를 찾아 나눈다. 줄 글자는 그대로 싣는다.
    labels = []
    for c in root.findall("조문내용"):
        txt = (c.text or "").strip()
        if not txt:
            continue
        in_art = False
        for line in txt.split("\n"):
            m = _RULE_HEAD.match(line)
            if m:
                if in_art:
                    out.append("</div>")
                labels.append(re.sub(r"\s+", "", m.group(1)))
                out.append('<div class="art"><div class="t">%s</div>' % _jo_html(line))
                in_art = True
            elif _RULE_CHAP.match(line):
                if in_art:
                    out.append("</div>")
                    in_art = False
                out.append('<div class="chap t">%s</div>' % _esc(line))
            else:
                out.append('<div class="t">%s</div>' % (_esc(line) or "&#8203;"))
        if in_art:
            out.append("</div>")
    # 행정규칙 XML 은 <부칙> 하나에 (부칙공포일자, 부칙공포번호, 부칙내용) 셋이 차례로
    # 되풀이된다(실측: 금융지주회사감독규정 부칙 40여 개). 셋씩 짝지어 부칙마다 머리를 단다.
    bus = root.findall("부칙")
    if bus:
        out.append("<h2>부칙</h2>")
        for b in bus:
            day = no = ""
            for c in b:
                t = (c.text or "").strip()
                if c.tag == "부칙공포일자":
                    day = t
                elif c.tag == "부칙공포번호":
                    no = t
                elif c.tag == "부칙내용":
                    hd = "부칙 〈%s, %s〉" % (no, _fmt_date(day))
                    out.append('<div class="bu"><div class="hd">%s</div><div class="t">%s</div></div>'
                               % (_esc(hd), _esc(t)))
                    day = no = ""
    out.extend(annex_index_html(root, annex_files))
    out.append("</body></html>")
    return "\n".join(out), name, labels


# ── 체계도 ────────────────────────────────────────────────────────────────
def hierarchy_html(tree_lines, title, efyd, serial):
    """tree_lines: [(깊이, 종류, 이름, 시행일)]."""
    out = ["<!doctype html><html><head><meta charset='utf-8'><title>%s 체계도</title>"
           "<style>%s .n{margin:1px 0}</style></head><body>" % (_esc(title), CSS),
           stamp_html("체계도(lsStmd) 렌더링", efyd, serial),
           "<h1>%s — 법령 체계도</h1>" % _esc(title)]
    for d, kind, nm, ef in tree_lines:
        out.append('<div class="n" style="margin-left:%.1fem">%s<b>[%s]</b> %s '
                   '<span style="color:#666">(시행 %s)</span></div>'
                   % (d * 1.6, "└ " if d else "", _esc(kind), _esc(nm), _fmt_date(ef)))
    out.append("</body></html>")
    return "\n".join(out)


# ── 인쇄 ──────────────────────────────────────────────────────────────────
def html_to_pdf(html_text, pdf_path, timeout=180):
    """오프라인 file:// 인쇄. 외부 자원을 참조하지 않으므로 네트워크가 필요 없다."""
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    # 예전 파일이 남아 있으면 Chromium 이 아무것도 안 써도 「있음」으로 통과한다 — 먼저 지운다.
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(html_text)
        src = f.name
    try:
        cmd = [chrome(), "--headless", "--no-sandbox", "--disable-gpu",
               "--no-pdf-header-footer", "--print-to-pdf-no-header",
               "--run-all-compositor-stages-before-draw",
               "--print-to-pdf=%s" % pdf_path, "file://%s" % src]
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
        if not ok:
            raise RuntimeError("PDF 렌더링 실패: %s" % r.stderr.decode("utf-8", "replace")[-400:])
    finally:
        os.remove(src)
    return pdf_path


def pdf_info(path):
    """(시그니처 OK, 쪽수, 전체 텍스트). pypdf 가 없으면 쪽수 -1."""
    with open(path, "rb") as f:
        head = f.read(8)
    sig = head.startswith(b"%PDF")
    if not sig:
        return False, 0, ""
    try:
        import pypdf
        r = pypdf.PdfReader(path)
        txt = "\n".join((p.extract_text() or "") for p in r.pages)
        return True, len(r.pages), txt
    except Exception:                          # noqa: BLE001
        return True, -1, ""
