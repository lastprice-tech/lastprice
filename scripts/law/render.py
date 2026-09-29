# -*- coding: utf-8 -*-
"""본문 XML → HTML → PDF (사용자 결정 ① — (가) XML 직접 렌더링이 기본).

목적이 조문 인용이므로 **모양보다 조문이 빠짐없이 들어 있는지**가 중요하다. 그래서
공식 본문 XML의 조문·항·호·목·부칙·별표 텍스트를 **원문 그대로**(공백 접기도 하지
않는다 — CSS pre-wrap) HTML로 옮기고, Chromium headless 로 오프라인 인쇄한다.
네트워크를 쓰지 않으므로 결정적으로 재현되고, verify7 이 PDF 텍스트에 모든 조문
표지가 들어 있는지 기계로 확인한다.

모든 PDF 첫 쪽 머리에 출처를 찍는다(사용자 요청):
  「법제처 Open API 원문 XML 렌더링 · 시행일 YYYY-MM-DD · 법령일련번호 NNN」

■ 법제처가 준 별표·서식 원본 PDF 에는 아무것도 찍지 않는다 — 그것은 원문이다.
  도장은 **우리가 렌더링한** 본문·체계도 PDF 에만 찍는다.
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
""" % {"serif": SERIF, "gothic": GOTHIC}

# 「제5조의2(인가받을 의무 등)」 머리. 조번호는 견고딕으로 찍되 **글자는 바꾸지 않는다**
# (span 으로 감쌀 뿐이라 PDF 텍스트는 원문과 같다 — verify7 의 조문표지 대조가 그대로 유효).
_JO = re.compile(r"^(\s*제\s*\d+\s*조(?:\s*의\s*\d+)?(?:\s*[（(][^)）]*[)）])?)")


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


def law_html(xml_bytes, efyd, serial, pending=False):
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
    by = root.find("별표")
    if by is not None and len(by):
        out.append("<h2>별표·서식</h2>")
        for b in by:
            if b.tag != "별표단위":
                continue
            out.append('<div class="byl"><div class="hd">%s</div><pre>%s</pre></div>'
                       % (_esc(_t(b, "별표제목")), _esc(_t(b, "별표내용"))))
    out.append("</body></html>")
    return "\n".join(out), name, article_labels(root)


# ── 행정규칙 ──────────────────────────────────────────────────────────────
def admrul_html(xml_bytes, efyd, serial, pending=False):
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
    labels = []
    for c in root.findall("조문내용"):
        txt = (c.text or "").strip()
        if not txt:
            continue
        m = re.match(r"(제\s*\d+\s*조(?:\s*의\s*\d+)?)", txt)
        if m:
            labels.append(re.sub(r"\s+", "", m.group(1)))
            out.append('<div class="art t">%s</div>' % _jo_html(txt))
        else:
            out.append('<div class="chap t">%s</div>' % _esc(txt))
    bus = root.findall("부칙")
    if bus:
        out.append("<h2>부칙</h2>")
        for b in bus:
            hd = "부칙 〈%s, %s〉" % (_t(b, "부칙공포번호"), _fmt_date(_t(b, "부칙공포일자")))
            body = "\n".join((x.text or "").strip() for x in b.findall("부칙내용") if x.text)
            out.append('<div class="bu"><div class="hd">%s</div><div class="t">%s</div></div>'
                       % (_esc(hd), _esc(body)))
    by = root.find("별표")
    if by is not None and len(by):
        out.append("<h2>별표·서식</h2>")
        for b in by:
            if b.tag != "별표단위":
                continue
            out.append('<div class="byl"><div class="hd">%s</div><pre>%s</pre></div>'
                       % (_esc(_t(b, "별표제목")), _esc(_t(b, "별표내용"))))
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
