# -*- coding: utf-8 -*-
"""10차 6-4 (에이전트 B) — 「지배구조 및 보수체계 연차보고서 작성기준」 원문(은행연합회·생보협회)과 게시처 확인.

    python3 scripts/dart/web10_std.py std       # 6-4-1 작성기준 원문 → handoff/원문_10차/작성기준_*.md · 작성기준_대조.csv
    python3 scripts/dart/web10_std.py posting   # 6-4-2 게시처 확인 → dart_out/risk10/게시처_std.csv
    python3 scripts/dart/web10_std.py all       # 둘 다

공용 도구는 web10.py(Web·save·Robots·now·write_csv·OUT·WORK)를 그대로 쓴다(고치지 않음).
원본: dart_out/raw/web10/std/ — 받은 바이트 그대로 + .meta.json(출처·시각·HTTP·sha256).
호스트마다 Robots 로 robots.txt 를 먼저 보고, 막힌 호스트·경로는 요청하지 않는다(우회 없음).
손해보험협회(knia.or.kr)는 다른 에이전트 몫이라 요청하지 않는다.

실측(2026-10-01) 요약 — 사유는 산출물 note 에 원문 그대로 남긴다.
  · www.kfb.or.kr · kfb.or.kr · portal.kfb.or.kr : robots.txt 「User-agent: * / Disallow: /」 → 은행연합회는 아무것도 받지 않음.
  · pub.insure.or.kr(생보협회 공시실) : robots.txt 가 User-agent:* 에 「Disallow:/」 → 받지 않음.
  · www.klia.or.kr : robots.txt 는 User-agent:Yeti 그룹만 있음 → 우리 UA 제한 없음. 목록·원문 파일 받음.
  · www.kofia.or.kr · dis.kofia.or.kr : /robots.txt 가 HTTP 200 으로 HTML 오류 화면을 돌려줌(규칙 줄 없음)
    → 2xx 응답을 규칙대로 해석하면 그룹 없음 = 제한 없음. 전자공시(dis)는 WebSquare 화면이 부르는
    /proframeWeb/XMLSERVICES/ 에 화면과 같은 XML 전문을 POST 해서 목록을 받는다.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web10 import Web, save, Robots, now, write_csv, OUT, WORK, RAW   # noqa: E402
from web9_klia import cd_filename, safe_name                           # noqa: E402 — 9차 함수 재사용(수정 없음)

TASK = "std"
DIR = os.path.join(RAW, TASK)
OLE = bytes.fromhex("d0cf11e0a1b11ae1")

KFB_HOSTS = ["https://www.kfb.or.kr", "https://kfb.or.kr", "https://portal.kfb.or.kr"]
KLIA = "https://www.klia.or.kr"
KLIA_LIST = KLIA + "/member/insurRegul/selfRegul/list.do"
KLIA_MENU = "회원사 > 자율규제운영 > 자율규제 규정정보"
KLIA_NAME = "지배구조 및 보수체계 연차보고서 작성기준"
KLIA_SEARCH = "연차보고서"
PUB = "https://pub.insure.or.kr"
KOFIA = "https://www.kofia.or.kr"
DIS = "https://dis.kofia.or.kr"
DIS_SVC = DIS + "/proframeWeb/XMLSERVICES/"
DIS_SCREEN = DIS + ("/websquare/index.jsp?w2xPath=/wq/compann/DISCompGovernanceStut.xml"
                    "&divisionId=MDIS02008002000000&serviceId=SDIS02008002000")

MD_KFB = os.path.join(OUT, "작성기준_은행연합회.md")
MD_KLIA = os.path.join(OUT, "작성기준_생보협회.md")
CSV_CMP = os.path.join(OUT, "작성기준_대조.csv")
CSV_POST = os.path.join(WORK, "게시처_std.csv")
CMP_COLS = ["구분", "항목", "은행연합회_위치", "은행연합회_source_text", "생보협회_위치", "생보협회_source_text",
            "차이여부", "note", "은행연합회_출처", "생보협회_출처", "collected_at"]
POST_COLS = ["corp_label", "site", "url", "found", "checked_at", "note", "evidence_file", "evidence_sha256"]
CORPS = ["메리츠금융지주", "한국투자금융지주"]
NA = "확인 불가"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def get(w, url, tries=3, **kw):
    """Web.get(3회 재시도)을 tries 번까지 — 이 환경의 프록시가 큰 응답을 가끔 중간에 끊는다(IncompleteRead)."""
    err = None
    for _ in range(tries):
        try:
            return w.get(url, **kw)
        except Exception as e:                       # noqa: BLE001
            if getattr(e, "code", None):             # HTTP 오류는 다시 하지 않는다
                raise
            err = e
    raise err


def robots_text(rb):
    """Robots 가 저장한 robots.txt 원문(줄 그대로)과 메타."""
    host = urllib.parse.urlparse(rb.base).netloc
    p = os.path.join(DIR, "robots_%s.txt" % host)
    if not os.path.exists(p):
        return "", {}, p
    meta = json.load(open(p + ".meta.json", encoding="utf-8"))
    return open(p, "rb").read().decode("utf-8", "replace"), meta, p


def robots_lines(rb):
    t, m, p = robots_text(rb)
    if not m:
        return "%s/robots.txt — %s %s" % (rb.base, rb.status, rb.note)
    body = t.strip()
    if body.lower().startswith(("<!doctype", "<html", "<?xml")):
        title = re.search(r"<title>(.*?)</title>", body, re.S | re.I)
        body = "HTML 응답(title: %s) — 규칙 줄 없음" % (html.unescape(title.group(1)).strip() if title else "")
    else:
        body = " / ".join(l.strip() for l in body.splitlines() if l.strip())
    return "%s/robots.txt (HTTP %s, %s, sha256 %s…): 「%s」" % (rb.base, m.get("http_status"), m.get("fetched_at"),
                                                              m.get("sha256", "")[:16], body)


# ── 6-4-1 작성기준 원문 ─────────────────────────────────────────────────────
def kfb_check(w):
    """은행연합회 호스트들의 robots.txt 만 받는다. 막혀 있으면 그 밖의 요청은 하지 않는다."""
    out = []
    for base in KFB_HOSTS:
        rb = Robots(w, base, TASK)
        allowed = rb.allowed(base + "/")
        out.append((base, rb, allowed))
        print("  robots %-28s %s 허용(/)=%s" % (base, rb.status, allowed))
    return out


def kfb_md(kfb):
    lines = ["# 「지배구조 및 보수체계 연차보고서 작성기준」 — 은행연합회 (원문 미수집)", "",
             "- 찾으려던 것: 은행연합회 「지배구조 및 보수체계 연차보고서 작성기준」(2026.1.6 개정) — "
             "www.kfb.or.kr 의 자율규제·모범규준 등 게시판의 게시글 HTML·첨부 원본(hwp/hwpx/pdf)",
             "- 결과: **수집하지 않음** — 아래 robots.txt 가 모든 사용자 에이전트에 사이트 전체를 막는다. "
             "robots.txt 외에는 어떤 페이지도 요청하지 않았다(우회 없음).", ""]
    for base, rb, allowed in kfb:
        t, m, p = robots_text(rb)
        lines.append("## %s/robots.txt" % base)
        lines.append("")
        if m:
            lines.append("- HTTP %s · 수집일 %s · %s바이트 · sha256 %s · 원본 %s" % (
                m.get("http_status"), m.get("fetched_at"), m.get("바이트"), m.get("sha256"), p))
            lines.append("- 우리 UA 로 「/」 허용 여부: %s" % ("허용" if allowed else "불허"))
            lines += ["", "```", t.rstrip("\n"), "```", ""]
        else:
            lines += ["- %s %s" % (rb.status, rb.note), ""]
    lines += ["## 확인하지 못한 것", "",
              "- 게시판·게시글·첨부·개정 이력: 사이트를 열지 못해 확인 못 함(「문서에 없음」이 아니라 「확인 불가」).",
              "- 이용약관·저작권정책: 같은 이유로 받지 않음(robots.txt 가 「/」 전체를 막음).",
              "- 원문 텍스트: 없음.", ""]
    os.makedirs(OUT, exist_ok=True)
    with open(MD_KFB, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("  %s (원문 미수집 기록)" % MD_KFB)


def klia_fetch(w):
    """생보협회 목록에서 작성기준 행을 다시 찾고(검색어 '연차보고서'), 행의 원문보기 링크를 모두 받는다."""
    rb = Robots(w, KLIA, TASK)
    print("  robots %s %s" % (KLIA, rb.status))
    if not rb.allowed(KLIA_LIST):
        raise SystemExit("www.klia.or.kr robots.txt 가 목록 화면을 막음 — 받지 않음: " + robots_lines(rb))
    info = dict(robots=robots_lines(rb), terms="")
    # 이용약관·저작권정책 — 사이트맵(/etc/sitemap.do, 상단 메뉴 링크)을 한 번 요청해 본다. 직접 요청에는
    # 「적절하지 않은 경로를 통한 요청입니다」 화면이 온다(실측) — Referer 를 붙여 다시 하지 않고(판단), 아래 목록
    # 화면 HTML(전체 메뉴·푸터 포함)의 링크로 약관·저작권 페이지가 있는지 본다.
    smap = KLIA + "/etc/sitemap.do"
    smap_note = ""
    if rb.allowed(smap):
        fu, st, hd, b = get(w, smap)
        p, m = save(TASK, "klia_sitemap.html", b, dict(출처URL=smap, 최종URL=fu, http_status=st, fetched_at=now()))
        t = b.decode("utf-8", "replace")
        body = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t[t.find("<body"):]))).strip()
        smap_note = "사이트맵 %s 직접 요청 → HTTP %s 「%s」(sha256 %s…, 다시 요청 안 함)" % (
            smap, st, body[:80], m["sha256"][:16])
    # 목록 검색(화면의 검색 폼과 같은 POST)
    fu, st, hd, b = get(w, KLIA_LIST, referer=KLIA_LIST, data={"pageIndex": "1", "search_text": KLIA_SEARCH})
    p_list, m_list = save(TASK, "klia_목록_검색_%s.html" % KLIA_SEARCH, b,
                          dict(출처URL=KLIA_LIST, 요청="POST pageIndex=1&search_text=%s" % KLIA_SEARCH, 메뉴=KLIA_MENU,
                               최종URL=fu, http_status=st, fetched_at=now()))
    t = b.decode("utf-8", "replace")
    tb = re.search(r'<table class="board_list_table04">(.*?)</table>', t, re.S)
    if st != 200 or not tb:
        raise SystemExit("목록 표를 못 찾음(HTTP %s) — 구조 변경·차단 의심, 멈춤: %s" % (st, p_list))
    links = [(h, re.sub(r"<[^>]+>|\s+", " ", x).strip()) for h, x in
             re.findall(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', t, re.S)]
    hit = sorted(set("%s(%s)" % (x, h) for h, x in links if re.search("약관|저작권", x)))
    foot = re.findall(r'class="btn_privacy">([^<]*)<', t)
    info["terms"] = ("목록 화면 HTML(전체 메뉴·푸터 포함, sha256 %s…)의 링크 %d개 중 '약관·저작권' 낱말 링크: %s; "
                     "푸터 링크: %s(화면 안 팝업); %s" % (m_list["sha256"][:16], len(links),
                                                    ", ".join(hit) if hit else "없음", "·".join(foot) or "없음",
                                                    smap_note))
    info["terms_hits"] = hit
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tb.group(1), re.S):
        nm = re.search(r'<p class="hidden-xs">(.*?)</p>', tr, re.S)
        if not nm:
            continue
        name = html.unescape(re.sub(r"<[^>]+>", "", nm.group(1))).strip()
        date = re.findall(r'<td class="hidden-xs">(\d{4}-\d{2})</td>', tr)
        num = re.search(r'displayNum="([^"]*)"', tr)
        links = []
        for a in re.findall(r"gfn_fileDown\('(\d+)',\s*'(\d+)'\)", tr):
            if a not in links:
                links.append(a)
        rows.append(dict(name=name, date=date[0] if date else "", num=num.group(1) if num else "", links=links,
                         n_onclick=len(re.findall(r"gfn_fileDown\(", tr))))
    hit = [r for r in rows if r["name"] == KLIA_NAME]
    print("  목록 검색 '%s' %d행, 같은 이름 %d행" % (KLIA_SEARCH, len(rows), len(hit)))
    if not hit:
        raise SystemExit("목록에서 '%s' 행을 못 찾음" % KLIA_NAME)
    files = []
    for r in hit:
        for no, seq in r["links"]:
            url = KLIA + "/FileDown.do?fileNo=%s&seq=%s" % (no, seq)
            fu, st, hd, body = get(w, url, referer=KLIA_LIST)
            cd = hd.get("Content-Disposition", "")
            fname = cd_filename(cd)
            meta = dict(출처URL=url, 게시글URL=KLIA_LIST, 목록검색="POST search_text=%s" % KLIA_SEARCH, 메뉴=KLIA_MENU,
                        규제명=r["name"], 제개정월=r["date"], 목록번호=r["num"], 최종URL=fu, http_status=st,
                        content_type=hd.get("Content-Type", ""), content_disposition=cd, 원파일명=fname,
                        fetched_at=now())
            if not body.startswith(OLE):
                p, m = save(TASK, "klia_실패응답_%s-%s.html" % (no, seq), body, meta)
                raise SystemExit("hwp(OLE) 아님 — 저장만 하고 멈춤: %s 앞부분 %r" % (p, body[:60]))
            p, m = save(TASK, "klia_원문_%s-%s_%s" % (no, seq, safe_name(fname or "이름없음.hwp")), body, meta)
            print("  받음 %s %s바이트 sha256 %s…" % (os.path.basename(p), m["바이트"], m["sha256"][:12]))
            files.append((p, m, r))
    info.update(list_path=p_list, list_meta=m_list, rows=rows, hit=hit)
    return files, info


def klia_md(path, meta, info):
    """hwp2md(수정 없이)로 전체를 텍스트화 → 맨 위 머리말 + 글자 그대로."""
    full = os.path.splitext(path)[0] + "_hwp2md.md"
    r = subprocess.run([sys.executable, os.path.join(HERE, "hwp2md.py"), path, full], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("hwp2md 실패: %s" % r.stderr[-500:])
    body = open(full, encoding="utf-8").read()
    full_sha = sha(full)
    row = info["hit"][0]
    head = [
        "# 「지배구조 및 보수체계 연차보고서 작성기준」 — 생명보험협회 (원문 전체)",
        "",
        "- 출처 URL(원문보기): %s" % meta["출처URL"],
        "- 게시글 URL: 별도 게시글 화면 없음 — 목록 화면 %s (메뉴 %s)의 「%s」 행(목록 번호 %s, 제·개정월 %s)의 "
        "「다운로드」 단추(gfn_fileDown) → 위 URL" % (KLIA_LIST, KLIA_MENU, row["name"], row["num"], row["date"]),
        "- 행의 원문보기 링크: %s (PC칸·모바일칸 onclick %d개, 고유 링크 %d개) — 화면에 없는 seq 는 요청하지 않음"
        % (", ".join("fileNo=%s&seq=%s" % x for x in row["links"]), row["n_onclick"], len(row["links"])),
        "- 원파일명: %s" % meta["원파일명"],
        "- 수집일: %s · HTTP %s · %s바이트 · sha256 %s" % (meta["fetched_at"], meta["http_status"], meta["바이트"],
                                                     meta["sha256"]),
        "- 원본 저장: %s" % meta["저장경로"],
        "- 텍스트화: scripts/dart/hwp2md.py(사용자 제공, 수정 없음) → %s (sha256 %s). 아래 「---」 줄과 빈 줄 하나 "
        "다음부터가 그 출력 전체이며 글자를 바꾸지 않았다." % (full, full_sha),
        "- hwp2md 표기: 표는 마크다운 표, 칸 안 줄바꿈 `<br>`, 칸 안의 `|` 는 `\\|`, 표 안의 표는 「[내부표]」로 "
        "한 칸에 이어 적힌다. 머리말·꼬리말은 빠진다.",
        "- hwp 는 쪽 정보가 없다 — 쪽은 원문 「목 차」 표의 쪽 번호(원문 표기)로만 알 수 있고, 대조 CSV 의 위치는 "
        "이 md 파일의 줄 번호(1부터)로 적는다.",
        "- 판 표시: 원파일명 「%s」, 목록 제·개정월 「%s」. 본문 텍스트에서 「2026」 표기 %d회·「부칙」 %d회."
        % (meta["원파일명"], row["date"], body.count("2026"), body.count("부칙")),
        "- robots.txt: %s" % info["robots"],
        "- 이용약관·저작권정책: %s → 자동 수집 금지 문구를 확인할 약관 페이지를 찾지 못함." % info.get("terms", ""),
        "",
        "---",
        "",
    ]
    text = "\n".join(head) + body
    if not text.endswith("\n"):
        text += "\n"
    with open(MD_KLIA, "w", encoding="utf-8") as f:
        f.write(text)
    print("  %s — %d줄" % (MD_KLIA, text.count("\n")))
    return text.split("\n"), len(head), full, full_sha


# ── 대조 CSV ──────────────────────────────────────────────────────────────
LEVELS = [(0, re.compile(r"^제\s*\d+\s*절")), (1, re.compile(r"^\d+\.\s")), (2, re.compile(r"^[가-힣]\.\s")),
          (3, re.compile(r"^\d+\)\s")), (4, re.compile(r"^[가-힣]\)\s")), (5, re.compile(r"^\(\d+\)"))]


def marker(title):
    for lv, rx in LEVELS:
        m = rx.match(title)
        if m:
            return lv, re.sub(r"\s+", "", m.group(0))
    return None, ""


def nows(s):
    return re.sub(r"\s+", "", s)


def toc_rows(lines, start):
    """「목 차」 다음 첫 표의 행 → [(md줄번호, 제목칸, 쪽칸, 계층경로)]."""
    i = next(k for k in range(start, len(lines)) if lines[k].strip() == "목 차")
    j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("|"))
    out, path = [], {}
    k = j
    while k < len(lines) and lines[k].startswith("|"):
        m = re.match(r"^\| (.*?) \| (.*?) \|$", lines[k])
        k += 1
        if not m or set(m.group(1).strip()) <= set("-") and set(m.group(2).strip()) <= set("-"):
            continue
        title, page = m.group(1).strip(), m.group(2).strip()
        if not title:
            continue
        lv, mk = marker(title)
        if lv is not None:
            path = {a: b for a, b in path.items() if a < lv}
            path[lv] = mk
        out.append((k, title, page, " ".join(path[a] for a in sorted(path)) if lv is not None else ""))
    return out, k


def block(lines, a, b):
    """md 줄 a..b(1부터, 둘 다 포함)의 원문 그대로."""
    return "\n".join(lines[a - 1:b]).strip("\n")


def find(lines, pred, start=0, end=None, what=""):
    end = len(lines) if end is None else end
    for k in range(start, end):
        if pred(lines[k]):
            return k + 1                              # 1부터 센 줄 번호
    raise SystemExit("md 에서 표지를 못 찾음: %s" % what)


def eq(s):
    return lambda l: l.rstrip() == s


def risk_rows(lines, body0):
    """위험관리위원회 활동 기재 항목(+그 절이 참고하라고 한 2.다·6.나, 사외이사 활동표, 리스크관리협의회)."""
    b = body0
    c7 = find(lines, eq("7. 위험관리위원회"), b, what="7.")
    c8 = find(lines, eq("8. 내부통제위원회"), c7, what="8.")
    a7 = find(lines, eq(" 가. 역할(권한과 책무)"), c7, c8, "7.가")
    n7 = find(lines, eq(" 나. 구성(위험관리위원회위원)"), c7, c8, "7.나")
    d7 = find(lines, eq(" 다. 활동내역 및 평가"), c7, c8, "7.다")
    d71 = find(lines, eq("  1) 활동내역 개요"), d7, c8, "7.다.1")
    d72 = find(lines, eq("  2) 회의 개최내역"), d7, c8, "7.다.2")
    d73 = find(lines, eq("  3) 평가"), d7, c8, "7.다.3")
    c2 = find(lines, eq("2. 이사회"), b, what="2.")
    d2 = find(lines, eq(" 다. 활동내역"), c2, what="2.다")
    r2 = find(lines, lambda l: l.startswith(" 라. 이사회 및 이사"), d2, what="2.라")
    c6 = find(lines, eq("6. 감사위원회"), b, what="6.")
    n6 = find(lines, eq(" 나. 구성(감사위원회위원)"), c6, c7, "6.나")
    d6 = find(lines, eq(" 다. 활동내역 및 평가"), n6, c7, "6.다")
    c4 = find(lines, lambda l: re.match(r"^4\. 사외이사 활동", l), b, what="4.")
    g41 = find(lines, eq("  1) 이사회 및 이사회내 위원회 회의일시, 안건내용"), c4, what="4.가.1")
    g42 = find(lines, eq("  2) 사외이사 개인별 이사회내 위원회 참석 및 찬성여부"), g41, what="4.가.2")
    n4 = find(lines, eq(" 나. 임원배상책임보험 가입 현황"), g42, what="4.나")
    c11 = find(lines, eq("11. 리스크관리협의회(금융지주회사의 경우)"), b, what="11.")
    c12 = find(lines, eq("12. 감독당국 권고사항 및 개선계획"), c11, what="12.")
    s11 = [find(lines, lambda l, h=h: l.startswith(h), c11, c12, "11." + h) for h in
           (" 가. 역할", " 나. 협의절차", " 다. 구성", " 라. 활동내역 개요")]
    n13 = find(lines, eq("  3) 지배구조 현황(요약)"), b, what="1.나.3")
    d13 = find(lines, eq(" 다. 관련 규정"), n13, what="1.다")
    rem = find(lines, lambda l: re.match(r"^제\s*2절", l), c12, what="제2절")
    p1 = find(lines, lambda l: "(위험관리위원회 위원 여부)" in l, rem, what="보수위원회 구성표")
    p0 = find(lines, lambda l: l.startswith("- OOOO년 3월 정기주총 이전"), rem, p1, "보수위 구성표 앞")
    p2 = find(lines, eq("  2) 구성원"), p1, what="보수위 2) 구성원")
    spec = [
        ("7. 위험관리위원회 — 절 머리 작성기준", "제1절 7.", c7, a7 - 1, ""),
        ("7.가. 역할(권한과 책무) — 기재 항목 제목", "제1절 7. 가.", a7, n7 - 1,
         "활동 항목은 아니나 위원회 절의 기재 항목 전체를 보이려고 넣음. 7.가 아래에는 별도 작성지침 없음(제목만)."),
        ("7.나. 구성(위원) — 작성기준·구성원 서식(성명·상임/사외/비상임·직위·선임일·임기 만료일)", "제1절 7. 나.",
         n7, d7 - 1, "작성기준이 「위 ‘6.나.’를 참고」하라고 함 → 6.나 행 참조."),
        ("7.다. 활동내역 및 평가 — 작성기준", "제1절 7. 다.", d7, d71 - 1,
         "「위 ‘2.다.’를 참고」 → 2.다 행 참조."),
        ("7.다.1) 활동내역 개요", "제1절 7. 다. 1)", d71, d72 - 1,
         "7 절에는 제목만 있음 — 작성지침은 2.다.1)을 참고하라는 7.다 작성기준에 따름."),
        ("7.다.2) 회의 개최내역 — 회차 표기(회의일·회의시간·안건 통지일)와 위원별 활동내역 서식"
         "(위원 성명·참석여부 및 (불참)사유·보고안건 의견·의결안건·가결여부)", "제1절 7. 다. 2)", d72, d73 - 1,
         "서식의 비고 1)~3) 칸은 원문에 번호만 있음."),
        ("7.다.3) 평가 — 작성지침·작성예시", "제1절 7. 다. 3)", d73, c8 - 1, ""),
        ("[7.다가 참고하는 원문] 2.다. 이사회 활동내역 — 작성지침(참석여부·불참사유·안건·찬반·가결여부 기재 방법)",
         "제1절 2. 다.", d2, r2 - 1, "7.다 작성기준이 참고하라고 한 부분(이사회 서식: 「이사 성명」·「참석여부」)."),
        ("[7.나가 참고하는 원문] 6.나. 감사위원회 구성 — 작성기준·작성지침·구성원 서식", "제1절 6. 나.", n6, d6 - 1,
         "7.나 작성기준이 참고하라고 한 부분."),
        ("4.가.1) 이사회 및 이사회내 위원회 회의일시, 안건내용 — 위원회별(라) 위험관리위원회) 기재", "제1절 4. 가. 1)",
         g41, g42 - 1, "사외이사 활동내역 장에서 위원회별 회의일시·안건을 적게 함."),
        ("4.가.2) 사외이사 개인별 이사회내 위원회 참석 및 찬성여부 — 요약표에 「리스크관리 위원회」 개최·참여·찬성 칸",
         "제1절 4. 가. 2)", g42, n4 - 1, "요약표 머리에는 「리스크관리<br>위원회」로 적혀 있음(7절 제목은 「위험관리위원회」)."),
        ("1.나.3) 지배구조 현황(요약) — 「위험관리위원회」 행(구성·의장·관련 규정)", "제1절 1. 나. 3)", n13, d13 - 1, ""),
        ("[제2절] 1.나.1) 보수위원회 구성표 — 「사외이사 여부(위험관리위원회 위원 여부)」 칸", "제2절 1. 나. 1)",
         p0, p2 - 1, "보수위원회 위원의 위험관리위원회 겸임 여부를 적게 하는 칸."),
    ]
    labels = [lines[a - 1].strip() for a in s11]         # 원문 제목 그대로(예: 「나. 협의절차 (운영현황)」)
    ends = s11[1:] + [c12]
    spec.append(("11. 리스크관리협의회(금융지주회사의 경우) — 절 머리", "제1절 11.", c11, s11[0] - 1,
                 "이사회내 위원회가 아니라 금융지주 그룹 단위 협의회 — 「리스크관리」 이름이라 함께 넣음(판단)."))
    for lab, a, e in zip(labels, s11, ends):
        spec.append(("11.%s — 작성지침%s" % (lab, "·작성예시·구성 서식" if lab.startswith("다") else ""),
                     "제1절 11. %s" % lab.split()[0], a, e - 1,
                     "금융지주회사만 작성하는 항목." + (" 부결/보류안건명과 사유를 적게 함." if lab.startswith("라") else "")))
    return spec


def compare(lines, n_head, meta, kfb, info):
    kfb_note = "; ".join(robots_lines(rb) for _, rb, _ in kfb)
    kfb_src = ("은행연합회 www.kfb.or.kr 자율규제·모범규준 게시판(2026.1.6 개정본) — 원문 미수집: %s" % kfb_note)
    klia_src = ("생명보험협회 %s(%s) 「%s」(제·개정월 %s) 원문보기 %s · 원파일명 %s · sha256 %s · 텍스트 %s" % (
        KLIA_LIST, KLIA_MENU, KLIA_NAME, info["hit"][0]["date"], meta["출처URL"], meta["원파일명"], meta["sha256"],
        MD_KLIA))
    common_note = ("은행연합회 원문 미수집(robots.txt 「User-agent: * / Disallow: /」, 우회 없음) — 대조 불가라 "
                   "차이여부 「확인 불가」. hwp 는 쪽 정보가 없어 위치는 이 md 줄 번호(1부터)")
    rows = []
    toc, toc_end = toc_rows(lines, n_head)
    # 본문 대응 줄: 목차 제목과 공백 제거 후 같은 본문 줄을 순서대로 찾는다(찾지 못하면 note 에 적음)
    ptr = toc_end
    for ln, title, page, path in toc:
        hit = None
        for k in range(ptr, len(lines)):
            if lines[k].strip() and not lines[k].startswith("|") and nows(lines[k]) == nows(title):
                hit = k + 1
                break
        if hit:
            ptr = hit
        rows.append({
            "구분": "목차", "항목": title,
            "은행연합회_위치": NA, "은행연합회_source_text": NA + "(원문 미수집)",
            "생보협회_위치": "%s · 목차표 md %d행 · 목차상 %s · 본문 %s" % (
                path or "계층 표지 없음", ln, ("%s쪽" % page) if page else "쪽 칸 비어 있음",
                ("md %d행" % hit) if hit else "같은 제목 줄 못 찾음"),
            "생보협회_source_text": title,
            "차이여부": NA,
            "note": common_note + (" · 본문 줄은 공백 제거 후 같은 줄을 목차 순서대로 찾은 것" if hit else
                                   " · 본문에서 공백 제거 후 같은 제목 줄을 못 찾음(목차표와 본문 표기가 다르거나 여러 항목을 한 칸에 묶음)"),
            "은행연합회_출처": kfb_src, "생보협회_출처": klia_src, "collected_at": meta["fetched_at"]})
    for item, pos, a, b, note in risk_rows(lines, toc_end):
        rows.append({
            "구분": "위험관리위원회", "항목": item,
            "은행연합회_위치": NA, "은행연합회_source_text": NA + "(원문 미수집)",
            "생보협회_위치": "%s · md %d~%d행" % (pos, a, b),
            "생보협회_source_text": block(lines, a, b),
            "차이여부": NA, "note": common_note + (" · " + note if note else ""),
            "은행연합회_출처": kfb_src, "생보협회_출처": klia_src, "collected_at": meta["fetched_at"]})
    write_csv(CSV_CMP, CMP_COLS, rows)
    n_toc = sum(r["구분"] == "목차" for r in rows)
    print("  %s — %d행 (목차 %d · 위험관리위원회 %d)" % (CSV_CMP, len(rows), n_toc, len(rows) - n_toc))
    return rows


def std():
    w = Web()
    print("[6-4-1] 은행연합회")
    kfb = kfb_check(w)
    if any(a for _, _, a in kfb):
        print("  ※ 허용된 호스트가 있음 — 이 스크립트는 그 경우의 게시판 탐색을 구현하지 않았다. 수동 확인 필요.")
    kfb_md(kfb)
    print("[6-4-1] 생명보험협회")
    files, info = klia_fetch(w)
    path, meta, _r = files[0]
    lines, n_head, full, full_sha = klia_md(path, meta, info)
    compare(lines, n_head, meta, kfb, info)
    json.dump(dict(klia_terms=info.get("terms", ""), klia_robots=info["robots"],
                   klia_list=info["list_path"], klia_files=[(p, m["sha256"]) for p, m, _ in files],
                   kfb=[robots_lines(rb) for _, rb, _ in kfb], at=now()),
              open(os.path.join(DIR, "_std_요약.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  약관 확인(생보협회): %s" % info.get("terms", ""))


# ── 6-4-2 게시처 ─────────────────────────────────────────────────────────
def dis_call(w, app, svc, fn, dto, fields, name, what):
    """dis.kofia.or.kr 화면(callProframe.js)이 보내는 것과 같은 XML 전문 POST. 응답 원본 저장."""
    inner = "".join("    <%s>%s</%s>\n" % (k, html.escape(v, quote=False), k) for k, v in fields.items())
    req = ('<?xml version="1.0" encoding="utf-8"?>\n<message>\n  <proframeHeader>\n'
           '    <pfmAppName>%s</pfmAppName>\n    <pfmSvcName>%s</pfmSvcName>\n    <pfmFnName>%s</pfmFnName>\n'
           '  </proframeHeader>\n  <systemHeader></systemHeader>\n    <%s>\n%s</%s>\n</message>\n'
           % (app, svc, fn, dto, inner, dto))
    fu, st, hd, b = get(w, DIS_SVC, data=req.encode("utf-8"), referer=DIS_SCREEN,
                        headers={"Content-Type": "text/xml; charset=UTF-8"})
    p, m = save(TASK, name, b, dict(출처URL=DIS_SVC, 화면=DIS_SCREEN, 용도=what, 요청본문=req, 최종URL=fu,
                                    http_status=st, content_type=hd.get("Content-Type", ""), fetched_at=now()))
    return b.decode("utf-8", "replace"), p, m


def xml_rows(t, tag):
    return [dict((k, html.unescape(v)) for k, v in re.findall(r"<(\w+)>([^<]*)</\1>", x))
            for x in re.findall(r"<%s>(.*?)</%s>" % (tag, tag), t, re.S)]


def kofia(w):
    """금융투자협회 전자공시 「금융투자회사공시 > 금융회사 지배구조 공시 > 공시 현황」."""
    res = dict(rows=[], note="", evidence=("", ""))
    rw = Robots(w, KOFIA, TASK)
    rd = Robots(w, DIS, TASK)
    res["robots"] = "%s; %s" % (robots_lines(rw), robots_lines(rd))
    print("  robots %s %s · %s %s" % (KOFIA, rw.status, DIS, rd.status))
    if not (rd.allowed(DIS_SVC) and rd.allowed(DIS_SCREEN)):
        res["blocked"] = True
        return res
    # 이용약관 — 푸터 링크(개인정보 처리 · 메일주소무단수집거부 안내 · CONTACT US)만 있다. 이메일 무단수집 거부 문구 확인.
    terms = []
    if rw.allowed(KOFIA + "/index.do"):
        try:
            fu, st, hd, b = get(w, KOFIA + "/index.do")
            p, m = save(TASK, "kofia_index.html", b, dict(출처URL=KOFIA + "/index.do", 최종URL=fu, http_status=st,
                                                          fetched_at=now()))
            t = re.sub(r"<!--.*?-->", "", b.decode("utf-8", "replace"), flags=re.S)   # 주석 처리된 링크 제외
            foot = t[t.find('id="footer"'):]
            alts = re.findall(r'<li class="privacy\d"><a href="([^"]+)"><img [^>]*alt="([^"]+)"', foot)
            terms.append("www.kofia.or.kr 푸터 링크: %s — '이용약관·저작권' 링크 없음%s" % (
                ", ".join("%s(%s)" % (a, h) for h, a in alts),
                "" if not re.search("이용약관|저작권정책", t) else " (본문에 '이용약관/저작권정책' 낱말 있음 — 확인 필요)"))
        except Exception as e:                       # noqa: BLE001
            terms.append("www.kofia.or.kr 첫 화면 못 받음(%s)" % e)
    em = KOFIA + "/wpge/m_35/etc03.do"
    if rw.allowed(em):
        try:
            fu, st, hd, b = get(w, em)
            p, m = save(TASK, "kofia_메일주소무단수집거부.html", b, dict(출처URL=em, 최종URL=fu, http_status=st,
                                                                     fetched_at=now()))
            t = b.decode("utf-8", "replace")
            # 본문 첫 문단(<div class="privacy1"><p>…</p>) — 태그만 걷고 HTML 공백 규칙대로 한 칸으로
            ps = re.findall(r'<div class="privacy1">\s*<p>(.*?)</p>', t, re.S)
            sent = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip() for x in ps]
            terms.append("%s(sha256 %s…) 본문: 「%s」 — 이메일 주소의 자동 수집을 거부하는 안내로, 공시 자료의 "
                         "자동 수집 일반을 금지하는 문구는 아님" % (em, m["sha256"][:16],
                                                       " / ".join(sent) or "해당 문단 못 찾음"))
        except Exception as e:                       # noqa: BLE001
            terms.append("%s 못 받음(%s)" % (em, e))
    res["terms"] = "; ".join(terms)
    # 메뉴(실제 화면 위치 근거)
    try:
        t, p, m = dis_call(w, "FS-DIS2", "DISMenuSO", "selectGrandMenu", "DISMenuDTO", {}, "kofia_dis_메뉴.xml",
                           "전자공시 메뉴(화면 위치 근거)")
        mrow = [r for r in xml_rows(t, "DISMenuDTO") if r.get("divisionId", "").startswith("MDIS02008")]
        res["menu"] = "메뉴: " + " / ".join("%s %s(%s)" % (r.get("divisionId"), r.get("divisionNm"),
                                                         r.get("programPath", "") + r.get("runFilepageNm", ""))
                                          for r in mrow)
    except Exception as e:                           # noqa: BLE001
        res["menu"] = "메뉴 못 받음(%s)" % e
    # 회사 검색(화면 「회사선택」 팝업과 같은 호출)
    t, p, m = dis_call(w, "FS-COM", "COMDetCdMngInqSO", "selectDetCd", "COMDetCdMngDTO", {"groupCd": "C0219"},
                       "kofia_dis_업권코드.xml", "업권 코드(C0219)")
    ugb = [(r["commonCd"], r["codeNm"]) for r in xml_rows(t, "COMDetCdMngDTO") if r.get("commonCd")]
    ul = ",".join("'%s'" % c for c, _ in ugb)
    comp = {}
    for kw in ["메리츠", "한국투자", "지주"]:
        t, p, m = dis_call(w, "FS-DIS2", "DISComCompSrchSO", "select", "DISComCompSrchListDTO",
                           {"useYN": "", "uSrchWord": kw, "uCpnyTyp": "", "uCdList": ul, "uListCompGb": ""},
                           "kofia_dis_회사검색_%s.xml" % kw, "회사선택 검색어 %s (과거회사 포함)" % kw)
        comp[kw] = ["%s(%s·%s·%s)" % (r.get("uCpnyNm"), r.get("companyCd"), r.get("middleCategory"), r.get("useYN"))
                    for r in xml_rows(t, "dtolist")]
    res["comp"] = comp
    # 공시 현황 — 업권 전체, 2025-10-01 ~ 오늘(조회기간 3년 이내 제한 안)
    end = now()[:10].replace("-", "")
    fields = {"companyCd": "", "uData": "/".join(c for c, _ in ugb), "vStrtDt": "20251001", "vEndDt": end,
              "uRptList": "", "tsCd": "", "uRptAllYN": "1", "uGb": ""}
    t, p, m = dis_call(w, "FS-DIS2", "DISCompGovernanceSO", "select", "DISFTimeAnnInsDTO", fields,
                       "kofia_dis_지배구조공시현황_20251001-%s.xml" % end, "금융회사 지배구조 공시 > 공시 현황(업권 전체)")
    rows = xml_rows(t, "list")
    tot = re.search(r"<dbio_total_count_>(\d+)</dbio_total_count_>", t)
    res.update(rows=rows, total=tot.group(1) if tot else "", evidence=(p, m["sha256"]), period=(fields["vStrtDt"], end),
               ugb=ugb, at=m["fetched_at"])
    print("  공시 현황 %d행(표시 총 %s) · 회사검색 %s" % (len(rows), res["total"], {k: len(v) for k, v in comp.items()}))
    return res


def posting():
    w = Web()
    out = []
    print("[6-4-2] 은행연합회")
    kfb = kfb_check(w)
    for corp in CORPS:
        for base, rb, allowed in kfb:
            if base == "https://kfb.or.kr":
                continue                             # www 와 같은 기관 — www 행 note 에 함께 적는다
            t, m, p = robots_text(rb)
            site = ("은행연합회 소비자포털(portal.kfb.or.kr)" if "portal" in base else
                    "은행연합회 홈페이지 지배구조 공시(www.kfb.or.kr)")
            extra = ("; 같은 내용 " + robots_lines(kfb[1][1])) if "www" in base else ""
            out.append(dict(corp_label=corp, site=site, url=base + "/", found=NA if not allowed else "미확인",
                            checked_at=m.get("fetched_at", now()),
                            note=("robots.txt 가 사이트 전체를 막아 지배구조 공시 화면을 요청하지 않음(우회 없음) — "
                                  "실제 화면 URL·게시 여부 확인 못 함. %s%s" % (robots_lines(rb), extra)),
                            evidence_file=p if m else "", evidence_sha256=m.get("sha256", "")))
    print("[6-4-2] 생명보험협회 공시실")
    rp = Robots(w, PUB, TASK)
    t, m, p = robots_text(rp)
    allowed = rp.allowed(PUB + "/")
    print("  robots %s %s 허용(/)=%s" % (PUB, rp.status, allowed))
    for corp in CORPS:
        out.append(dict(corp_label=corp, site="생명보험협회 공시실(pub.insure.or.kr) 지배구조 공시",
                        url=PUB + "/", found=NA if not allowed else "미확인", checked_at=m.get("fetched_at", now()),
                        note=("robots.txt 가 우리 UA(User-agent:* 그룹)에 「Disallow:/」 — 공시실 화면을 요청하지 않음"
                              "(우회 없음). %s · 생보협회 홈페이지(www.klia.or.kr) 상단 메뉴의 「공시실」 링크는 "
                              "http://pub.insure.or.kr (9차 저장 목록 화면 HTML 근거). http 쪽 robots 는 이 환경이 "
                              "https 프록시만 지원해 따로 받지 않음." % robots_lines(rp)),
                        evidence_file=p if m else "", evidence_sha256=m.get("sha256", "")))
    print("[6-4-2] 금융투자협회(요청 밖 추가 확인)")
    try:
        k = kofia(w)
    except Exception as e:                           # noqa: BLE001
        k = dict(error="%s: %s" % (type(e).__name__, e))
    for corp in CORPS:
        base = dict(corp_label=corp, site="금융투자협회 전자공시 금융회사 지배구조 공시 > 공시 현황(dis.kofia.or.kr)",
                    url=DIS_SCREEN)
        if k.get("error") or k.get("blocked"):
            out.append(dict(base, found=NA, checked_at=now(), evidence_file="", evidence_sha256="",
                            note="요청 밖 추가 확인. %s" % (k.get("error") or "robots 차단: " + k.get("robots", ""))))
            continue
        key = "메리츠" if "메리츠" in corp else "한국투자"
        mine = [r for r in k["rows"] if corp in r.get("koreanNm", "")]
        rel = [r for r in k["rows"] if key in r.get("koreanNm", "")]
        ann = [r for r in k["rows"] if r.get("uRptGb") == "L103"]
        firms = sorted(set(r["koreanNm"] for r in k["rows"]))

        def fmt(rs):
            return ", ".join("%s %s 「%s」(%s)" % (r["standardDt"], r["koreanNm"], r["announceTtl"], r["uRptGb"])
                             for r in sorted(rs, key=lambda r: (r["standardDt"], r["koreanNm"])))
        note = ["요청 밖 추가 확인",
                "조회: 업권 전체(%s)·기간 %s~%s·보고서 전체 → 표시 총 %s건/받은 %d행·회사 %d곳" % (
                    "/".join("%s %s" % x for x in k["ugb"]), k["period"][0], k["period"][1], k["total"],
                    len(k["rows"]), len(firms)),
                "회사명에 「%s」 들어간 행: %d건" % (corp, len(mine)),
                "회사선택 검색 「%s」: %s" % (key, "; ".join(k["comp"].get(key, [])) or "없음"),
                "회사선택 검색 「지주」: %s" % ("; ".join(k["comp"].get("지주", [])) or "없음"),
                "같은 그룹 이름(「%s」) 회사의 지배구조·보수체계 연차보고서 행: %s" % (
                    key, fmt([r for r in rel if r.get("uRptGb") in ("L103", "L104")]) or "없음"),
                "이 화면의 「지배구조 연차보고서」(L103) %d건 게시 회사: %s" % (
                    len(ann), ", ".join("%s(%s)" % (r["koreanNm"], r["standardDt"]) for r in
                                        sorted(ann, key=lambda r: (r["koreanNm"], r["standardDt"])))),
                k.get("menu", ""), "robots: " + k.get("robots", ""), "약관: " + k.get("terms", "")]
        found = "Y" if any(r.get("uRptGb") in ("L103", "L104") for r in mine) else "N"
        if found == "Y":
            note.insert(1, "게시: " + fmt([r for r in mine if r.get("uRptGb") in ("L103", "L104")]))
        out.append(dict(base, found=found, checked_at=k["at"], note=" / ".join(x for x in note if x),
                        evidence_file=k["evidence"][0], evidence_sha256=k["evidence"][1]))
    write_csv(CSV_POST, POST_COLS, out)
    print("  %s — %d행" % (CSV_POST, len(out)))
    for r in out:
        print("   ", r["corp_label"], "|", r["site"], "|", r["found"])


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    fn = {"std": [std], "posting": [posting], "all": [std, posting]}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    os.makedirs(DIR, exist_ok=True)
    for f in fn:
        f()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
