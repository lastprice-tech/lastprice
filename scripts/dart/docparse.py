# -*- coding: utf-8 -*-
"""DART 공시서류 원문(document.xml ZIP) 파서.

DART 원문은 자체 DTD 이고 자주 비정형이다(미정의 엔티티, 대문자 태그). 엄격한 XML
파서는 실패하므로 html.parser 기반의 관대한 파서를 쓴다. 표는 격자로 '추론'하지 않고
rowspan/colspan 을 그대로 실어 내보낸다 — COLSPAN 헤더에서 격자를 잘못 짜면 기말 CSM
이 전기 칸으로 밀린다.
"""
from __future__ import annotations

import io
import os
import re
import unicodedata
import zipfile
from html.parser import HTMLParser

CELL_TAGS = {"td", "th", "te", "tu"}
SECTION_TAGS = re.compile(r"^section(-\d+)?$")
DEFAULT_MAX_DOC_BYTES = 200 * 1024 * 1024
MAX_ZIP_RATIO = 200  # 압축폭탄 방어

# 원문에 흔한 미정의 엔티티 (엄격 파서를 죽이는 주범)
ENTITY_TEXT = {
    "cir": "○", "nbsp": " ", "middot": "·", "bull": "•", "times": "×",
    "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'",
    "cr": "", "lowbar": "_", "sim": "~", "deg": "°", "permil": "‰",
}


def normalize_for_match(s: str) -> str:
    """매칭 전용. 출력에는 항상 원문을 쓴다.

    DART 는 중점 자리에 ㆍ(U+318D)를 쓴다 — 정규화하지 않으면 보고서 유형이 통째로 샌다.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    # U+119E 가 목록에 있어야 한다: NFKC 가 ㆍ(U+318D HANGUL LETTER ARAEA)를
    # U+119E(HANGUL JUNGSEONG ARAEA)로 먼저 바꿔버리기 때문에, U+318D 만 적어 두면
    # 치환이 헛돈다. 실측: "주식의포괄적교환·이전"(중점)으로 필터하면 0건, 아래아
    # 표기로만 42건이 잡혔다 — 표기를 정확히 맞춰야만 결과가 나오는 함정이었다.
    for ch in "ㆍᆞ·・‧":
        s = s.replace(ch, "·")
    s = s.replace(" ", " ").replace("　", " ")
    return re.sub(r"\s+", " ", s).strip()


def normalize_for_output(s: str) -> str:
    """출력 전용. 공백만 접는다 — NFKC 도 중점 치환도 하지 않는다.

    예전에는 출력 버퍼에도 normalize_for_match 를 쓴 탓에 NFKC 가 글자를
    바꿔버렸다(원문 103건 실측): ㈜→'(주)', ①→'1', Ⅰ→'I', ㆍ→'·', 그리고
    ㅇ(U+3147 HANGUL LETTER IEUNG) → ᄋ(U+110B 조합용 초성) — 마지막 것은 폰트에
    따라 보이지도 않고 'ㅇ' 으로 검색해도 안 잡힌다. 그것은 보존이 아니라 변조다.

    전각공백(U+3000)·NBSP 를 보통 공백으로 바꾸고 연속 공백을 하나로 줄이는 것은
    가독성상 필요하고 정보 손실이 아니다(글자가 바뀌지 않는다).
    """
    if not s:
        return ""
    s = s.replace(" ", " ").replace("　", " ")
    return re.sub(r"\s+", " ", s).strip()


# ── 인코딩 ────────────────────────────────────────────────────────────────
def decode_document(data: bytes):
    """(text, declared, used, replacements) — cp949 는 euc-kr 상위집합이라 따로 안 쓴다.

    선언이 utf-8 인데 실제로는 cp949 인 문서가 존재하므로 선언을 맹신하지 않는다.
    """
    m = re.search(rb'encoding\s*=\s*["\']([\w\-]+)["\']', data[:512])
    declared = m.group(1).decode("ascii", "replace").lower() if m else ""
    ladder = []
    if declared:
        ladder.append(declared)
    ladder += ["utf-8-sig", "utf-8", "cp949"]
    for enc in ladder:
        try:
            return data.decode(enc), declared, enc, 0
        except (UnicodeDecodeError, LookupError):
            continue
    text = data.decode("cp949", errors="replace")
    return text, declared, "cp949+replace", text.count("�")


# ── ZIP ───────────────────────────────────────────────────────────────────
def normalize_member(name: str) -> str:
    """ZIP 멤버명을 정규화한다.

    DART 는 멤버명 앞에 '/' 를 붙여 내려주는 경우가 있다(실측: 원문 ZIP 69개 중 21개).
    선행 슬래시를 traversal 로 보고 거부하면 유일한 본문 멤버가 통째로 버려진다.
    진짜 위험한 것은 '..' 이므로 그것만 막고 선행 구분자는 벗겨낸다.
    """
    n = name.replace("\\", "/").lstrip("/")
    if len(n) > 1 and n[1] == ":":          # 윈도우 드라이브 문자
        n = n[2:].lstrip("/")
    return n


def safe_members(zf: zipfile.ZipFile):
    """경로 traversal 과 압축폭탄을 거른다."""
    out = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        norm = normalize_member(info.filename)
        if not norm or ".." in norm.split("/"):
            continue
        if info.compress_size and info.file_size / max(info.compress_size, 1) > MAX_ZIP_RATIO:
            continue
        out.append(info)
    return out


def pick_principal(members, rcept_no):
    """본문 멤버 선택: 이름 정확일치 우선, 없으면 최대 .xml."""
    exact = [m for m in members
             if os.path.basename(normalize_member(m.filename)).lower() == "%s.xml" % rcept_no.lower()]
    if exact:
        return exact[0], "exact_name"
    xmls = [m for m in members if normalize_member(m.filename).lower().endswith(".xml")]
    if xmls:
        return max(xmls, key=lambda m: m.file_size), "largest_xml"
    if members:
        return max(members, key=lambda m: m.file_size), "largest_any"
    return None, "none"


def read_zip(body: bytes, rcept_no: str, max_bytes=DEFAULT_MAX_DOC_BYTES):
    """ZIP → {members, principal, text, encoding..., truncated}"""
    zf = zipfile.ZipFile(io.BytesIO(body))
    members = safe_members(zf)
    info = {"namelist": [m.filename for m in members],
            "member_sizes": {m.filename: m.file_size for m in members}}
    principal, how = pick_principal(members, rcept_no)
    info["member_selected"] = principal.filename if principal else ""
    info["member_selection"] = how
    if principal is None:
        info.update(text="", truncated=False, encoding_declared="", encoding_used="",
                    decode_replacements=0)
        return info
    if principal.file_size > max_bytes:
        info.update(text="", truncated=True, encoding_declared="", encoding_used="",
                    decode_replacements=0)
        return info
    with zf.open(principal) as fh:
        data = fh.read(max_bytes + 1)
    truncated = len(data) > max_bytes
    text, declared, used, repl = decode_document(data[:max_bytes])
    info.update(text=text, truncated=truncated, encoding_declared=declared,
                encoding_used=used, decode_replacements=repl)
    return info


# ── 파서 ──────────────────────────────────────────────────────────────────
class DartDocParser(HTMLParser):
    """섹션(TITLE 기준)과 표를 추출한다. 의미 정규화는 하지 않는다."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.src = text
        self._line_starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                self._line_starts.append(i + 1)
        self.sections = []          # {title, title_raw, text_parts, tables, start}
        self._cur = None
        self._mode = None           # title | cell | text
        self._buf = []
        self._table = None
        self._row = None
        self._cell_attrs = {}
        self._cell_tag = ""         # 열린 셀의 여는 태그 — 닫을 때 지어내지 않는다
        self._table_start = 0
        self._recent_text = []      # 표 직전 '(단위: 백만원)' 포착용
        self._loose = []            # 표·제목 밖 텍스트(태그 경계에서 플러시)
        self._stack = []            # 중첩 <TABLE> — 바깥 표의 상태를 밀어 둔다
        self._ensure_section(0, "(머리말)")

    # 위치 → 문자 오프셋
    def _off(self):
        line, col = self.getpos()
        return self._line_starts[min(line - 1, len(self._line_starts) - 1)] + col

    def _ensure_section(self, off, title):
        self._cur = {"title": normalize_for_match(title), "title_raw": title,
                     "text_parts": [], "tables": [], "start": off}
        self.sections.append(self._cur)
        self._recent_text = []   # 단위 표기가 섹션 경계를 넘어 잘못 붙는 것을 막는다

    def _emit(self, s):
        """데이터·엔티티·문자참조가 모두 같은 경로를 타게 한다.

        예전에는 엔티티를 self._mode 가 있을 때만 버퍼에 넣어서, 표 밖·제목 밖
        텍스트의 엔티티가 통째로 사라졌다. 실측(원문 103건)으로는 그 경로의 엔티티가
        &cr 11건·문자참조 0건뿐이라 지금 당장의 손실은 없었지만, 구조상 손실이므로
        경로를 하나로 합친다.
        """
        if not s:
            return
        if self._mode:
            self._buf.append(s)
        elif self._cur is not None:
            # 표 안이지만 셀 밖에 있는 텍스트(<TABLE> 와 첫 <TR> 사이 등)도 버리지
            # 않는다. 예전에는 self._table 이 열려 있으면 통째로 지웠다. 셀로는
            # 복원할 수 없으므로 close() 와 같은 정책으로 본문 텍스트에 남긴다.
            # 실측(원문 ZIP 103건 + 웹 회수 목차 153노드): 이 경로를 타는 글자 0자 —
            # 지금 산출물은 한 글자도 바뀌지 않고 열려 있던 삭제 경로만 닫힌다.
            self._loose.append(s)

    def _autoclose_cell(self):
        """안 닫힌 <TD>/<TH> 를 닫아 행에 싣는다.

        예전에는 다음 셀 태그가 self._buf 를 [] 로 리셋해 앞 셀의 글자와 셀 자체가
        같이 사라졌다. 최소 재현: "<TABLE><TR><TD>첫칸<TD>둘째칸</TR></TABLE>" 이
        표 1개 / 행 0개가 되어 '첫칸'·'둘째칸' 이 둘 다 없어졌다(셀이 하나도 안 실린
        행은 </TR> 에서 통째로 버려진다). 태그 이름은 열 때 기억해 둔 것을 쓴다 —
        없으면 없는 대로 빈칸이고, 지어내지 않는다.
        """
        if self._mode != "cell" or self._row is None:
            return
        self._row.append({
            "text": normalize_for_output("".join(self._buf)),
            "rowspan": self._cell_attrs.get("rowspan", ""),
            "colspan": self._cell_attrs.get("colspan", ""),
            "tag": self._cell_tag,
        })
        self._mode, self._buf, self._cell_attrs, self._cell_tag = None, [], {}, ""

    def _autoclose_row(self):
        """안 닫힌 <TR> 을 닫아 표에 싣는다(열린 셀이 있으면 먼저 닫는다)."""
        self._autoclose_cell()
        if self._row and self._table is not None:
            self._table["rows"].append(self._row)
        self._row = None

    def _flush_loose(self):
        """표·제목 밖 텍스트는 모았다가 태그 경계에서 한 번에 넣는다.

        조각마다 바로 넣으면 section_body 가 " " 로 잇기 때문에, 엔티티로 끊긴
        'M&A중개' 가 'M &A 중개' 로 벌어진다. 태그 경계까지 모으면 원문의 붙임이 유지된다.
        """
        if not self._loose:
            return
        s = normalize_for_output("".join(self._loose))
        self._loose = []
        if s and self._cur is not None:
            self._cur["text_parts"].append(s)

    def handle_starttag(self, tag, attrs):
        self._flush_loose()
        t = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}
        if t == "title":
            self._mode, self._buf = "title", []
        elif t in ("table", "table-group"):
            # DART 원문은 표 안에 표를 넣는다. 스택 없이 self._table 을 덮어쓰면 바깥
            # 표가 통째로 사라졌다 — 여는 시점의 상태를 밀어 두고 닫을 때 되돌린다.
            # 실측(우리 2018 웹회수 8건): <TABLE> 10,549개 중 파서가 낸 것이 10,362개뿐,
            # 즉 바깥 표 187개가 없어졌고 그 안의 셀 356개(내용 있는 행 331개)가 같이
            # 날아갔다. 그 331행이 전부 "(주n) 정정 전" / "(주n) 정정 후" 라벨이라,
            # 정정신고서에서 어느 표가 정정 전이고 어느 것이 후인지가 인계본에서 사라졌다.
            self._stack.append((self._table, self._row, self._mode, self._buf,
                                self._cell_attrs, self._table_start, self._cell_tag))
            self._table = {"rows": [], "unit_hint": self._find_unit(),
                           "unit_hint_source": "", "caption": "", "start": self._off()}
            self._table_start = self._off()
            self._row, self._mode, self._buf = None, None, []
            self._cell_attrs, self._cell_tag = {}, ""
            # 닫을 때가 아니라 여는 시점에 싣는다. 그래야 table_index 가 원문의 <TABLE>
            # 등장 순서와 같고(바깥 표가 제 자식들 뒤로 밀리지 않는다), 끝까지 닫히지
            # 않은 표도 있는 만큼은 남는다. raw_xml·unit_hint 는 같은 객체에 나중에
            # 채우므로 닫을 때의 값이 그대로 반영된다.
            if self._cur is not None:
                self._cur["tables"].append(self._table)
        elif t == "tr" and self._table is not None:
            self._autoclose_row()       # 앞 <TR> 이 안 닫혔으면 버리지 말고 닫는다
            self._row = []
        elif t in CELL_TAGS and self._row is not None:
            self._autoclose_cell()      # 앞 셀이 안 닫혔으면 버리지 말고 닫는다
            self._mode, self._buf, self._cell_attrs = "cell", [], a
            self._cell_tag = t
        elif t == "p":
            # 표 밖의 <P> 만 본문으로 취급한다. DART 는 셀 내용을 <TD><P>…</P></TD> 로
            # 감싸는 일이 흔한데, 여기서 모드를 갈아치우면 셀 버퍼가 리셋돼 그 셀이
            # 빈 값으로 나온다(실측: 전체 셀의 9.9%가 그렇게 비어 있었다).
            if self._row is None:
                self._mode, self._buf = "text", []

    def handle_startendtag(self, tag, attrs):
        self._flush_loose()

    # 주석·선언·처리지시도 텍스트 경계다(예전에 조각이 나뉘던 지점을 그대로 유지).
    def handle_comment(self, data):
        self._flush_loose()

    def handle_decl(self, decl):
        self._flush_loose()

    def handle_pi(self, data):
        self._flush_loose()

    def unknown_decl(self, data):
        self._flush_loose()

    def close(self):
        # 닫히지 않은 <P>/<TD>/<TITLE> 안에 남은 텍스트를 버리지 않는다. 문서가
        # 중간에서 끝나면(원문 크기 초과 절단, 목차 노드를 바이트로 자른 웹회수 조각)
        # self._buf 가 그대로 사라졌다. 셀로는 복원할 수 없으므로 본문 텍스트로 남긴다.
        # 중첩 <TABLE> 안에서 문서가 끝나면 바깥 프레임의 버퍼가 스택에 남는다.
        # 예전에는 가장 안쪽 것만 건지고 나머지는 통째로 사라졌다.
        # super().close() 가 남은 조각을 처리하다 죽어도 버퍼는 비워 낸다(finally).
        # 예외는 삼키지 않고 그대로 올려 보낸다 — parse_document 가 사유를 기록한다.
        try:
            super().close()
        finally:
            while True:
                tail = normalize_for_output("".join(self._buf))
                self._buf = []
                if tail and self._cur is not None:
                    self._cur["text_parts"].append(tail)
                if not self._stack:
                    break
                (self._table, self._row, self._mode, self._buf, self._cell_attrs,
                 self._table_start, self._cell_tag) = self._stack.pop()
            self._flush_loose()

    def handle_endtag(self, tag):
        self._flush_loose()
        t = tag.lower()
        # 출력 버퍼는 normalize_for_output(공백 접기)만 거친다. 여기에
        # normalize_for_match 를 쓰면 셀·본문이 NFKC 로 변조된다(㈜→1자→3자,
        # ㅇ→조합용 자모). 매칭은 읽는 쪽에서 양쪽을 정규화해 해결한다.
        txt = normalize_for_output("".join(self._buf))
        if t == "title":
            self._ensure_section(self._off(), "".join(self._buf).strip())
            self._mode, self._buf = None, []
        elif t in CELL_TAGS and self._row is not None:
            self._row.append({
                "text": txt,
                "rowspan": self._cell_attrs.get("rowspan", ""),
                "colspan": self._cell_attrs.get("colspan", ""),
                "tag": t,
            })
            self._mode, self._buf, self._cell_attrs = None, [], {}
            self._cell_tag = ""
        elif t == "tr" and self._row is not None:
            self._autoclose_cell()      # </TD> 없이 </TR> 이 온 경우
            if self._row:
                self._table["rows"].append(self._row)
            self._row = None
        elif t in ("table", "table-group") and self._table is not None:
            self._autoclose_row()       # </TR> 없이 </TABLE> 이 온 경우
            self._table["raw_xml"] = self.src[self._table_start:self._off() + len(tag) + 3]
            # 단위 표기가 표 바깥 <P> 가 아니라 표의 첫 행 셀에 들어 있는 경우가 흔하다
            # (실측: 동양생명 2024 주석의 CSM 롤포워드 표). 표 안에 있으면 그 표의 것이
            # 확실하므로 앞 <P> 추정보다 우선한다. 원문 그대로만 싣고 환산하지 않는다.
            for row in self._table["rows"][:3]:
                found = next((c["text"] for c in row
                              if "단위" in normalize_for_match(c["text"])), None)
                if found:
                    self._table["unit_hint"] = found
                    self._table["unit_hint_source"] = "table_cell"
                    break
            else:
                if self._table["unit_hint"]:
                    self._table["unit_hint_source"] = "preceding_text"
            # 싣는 것은 여는 시점에 이미 했다. 여기서는 바깥 표의 상태만 되돌린다.
            if self._stack:
                (self._table, self._row, self._mode, self._buf, self._cell_attrs,
                 self._table_start, self._cell_tag) = self._stack.pop()
            else:                       # 짝 없는 </TABLE> — 바깥이 없다
                self._table, self._row = None, None
        elif t == "p":
            if self._row is not None:
                return          # 셀 안의 </P> — 버퍼를 건드리지 않고 </TD> 가 받게 둔다
            if txt:
                self._recent_text.append(txt)
                del self._recent_text[:-8]
                # 표 안이지만 <TR> 밖에 있는 <P>(예: "<TABLE><P>주석</P><TR>…")도
                # 본문에 남긴다. 예전에는 self._table 이 열려 있으면 지웠다 — 셀에도
                # 본문에도 없으니 통째 삭제였다. 실측(원문 103건 + 웹 153노드) 0자.
                if self._cur is not None:
                    self._cur["text_parts"].append(txt)
            self._mode, self._buf = None, []

    def handle_data(self, d):
        self._emit(d)

    # 미정의 엔티티가 파싱을 죽이지도, 내용을 지우지도 않게 한다
    def handle_entityref(self, name):
        # DART 원문은 '&' 를 escape 하지 않는다. html.parser 는 'M&A중개' 를
        # handle_entityref("A") + handle_data("중개") 로 읽으므로, 모르는 이름을
        # 빈 문자열로 바꾸면 '&A' 가 통째로 사라진다. 실측(원문 ZIP 103건 전수,
        # handle_entityref 호출 기준): 미정의 1,013건 / 53종 —
        # &A 267·&P 230·&S 93·&Trading 85·&G 45·&C 36·&White 34·&P500 32 …
        # 전부 M&A·S&P500·Sales&Trading·Hull&White·AT&T 같은 실제 용어라
        # 지울 것이 하나도 없다(정의된 &cr 은 따로 30,987건).
        # 모르면 원문('&' + 이름)을 그대로 복원한다. ENTITY_TEXT 에 있는 이름은
        # 지금대로 매핑하고(&cr → "" 는 DART 의 줄바꿈 표시라 유지),
        # 다만 "" 도 값이므로 get(...) or 가 아니라 is None 로 갈라야 한다.
        rep = ENTITY_TEXT.get(name.lower())
        if rep is None:
            rep = "&" + name
        self._emit(rep)

    def handle_charref(self, name):
        try:
            ch = chr(int(name[1:], 16) if name[:1].lower() == "x" else int(name))
        except Exception:
            ch = "&#%s;" % name     # 변환 실패 — 지우지 말고 원문을 남긴다
        self._emit(ch)

    def _find_unit(self):
        """DART 는 '(단위: 백만원)' 을 TABLE 바깥 바로 앞 P 에 쓴다. 원문 그대로만 싣는다."""
        for s in reversed(self._recent_text[-5:]):
            if "단위" in normalize_for_match(s):
                return s
        return ""


def parse_document(text):
    p = DartDocParser(text)
    try:
        p.feed(text)
        p.close()
    except Exception as e:  # 어떤 문서도 전체 실행을 죽이지 않는다
        # 예외 지점까지 읽어 둔 버퍼를 버리지 않는다. 예전에는 close() 를 못 타서
        # 마지막 <P>/<TD> 의 글자와 느슨한 텍스트가 사유도 없이 사라졌다.
        try:
            p.close()
        except Exception:
            pass
        return p.sections, "parser_error: %s" % type(e).__name__
    return p.sections, ""


def match_sections(sections, keywords):
    """키워드가 걸린 섹션만 (index, section, matched) 로 돌려준다."""
    normed = [(k, normalize_for_match(k)) for k in keywords]
    out = []
    for i, sec in enumerate(sections):
        title = sec["title"]
        if not title:
            continue
        hits = [k for k, nk in normed if nk and nk in title]
        if hits:
            out.append((i, sec, hits))
    return out


def text_keywords(text, keywords):
    """본문·셀 텍스트에 걸린 키워드. 양쪽을 정규화해서 비교한다.

    출력을 더 이상 NFKC 하지 않으므로(글자 변조 방지), 키워드를 그대로 대본문에
    넘기면 ㈜·전각 표기 차이로 히트가 조용히 줄어든다. 빈 키워드(nk 이 "")는
    아무 문자열에나 포함되므로 걸러낸다 — match_sections 와 같은 가드다.
    """
    blob = normalize_for_match(text)
    out = []
    for k in keywords:
        nk = normalize_for_match(k)
        if nk and nk in blob:
            out.append(k)
    return out


def table_keywords(table, keywords):
    """표 안의 셀 텍스트에 걸린 키워드. 제목이 아니라 내용으로 표를 고르기 위한 것."""
    return text_keywords(" ".join(c["text"] for r in table["rows"] for c in r), keywords)


def section_body(section):
    return " ".join(section["text_parts"])


def slug(s, n=40):
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "_", normalize_for_match(s))
    return s.strip("_")[:n] or "section"
