# -*- coding: utf-8 -*-
"""9차 작업 5 — 웹 수집(비DART). 받은 원본은 그대로 두고 출처·시각·HTTP 상태·sha256 을 남긴다.

    python3 scripts/dart/web9.py raas        # 5-1 금감원 RAAS 매뉴얼 hwp → RAAS_매뉴얼_원문.md

원본: dart_out/raw/web9/<작업>/ (git 무시), 메타: 같은 이름 + .meta.json
요청은 하나씩, 1.2초 간격, 실패 3회까지 재시도. 접속이 안 되면 사유를 남기고 멈춘다(우회 없음).
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RAW = os.path.join("dart_out", "raw", "web9")
WORK = os.path.join("dart_out", "risk9")
HANDOFF = "handoff"
UA = ("lastprice-research/1.0 (financial-holding risk governance study; "
      "contact: repository owner)")
DELAY = 1.2
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


class Web:
    def __init__(self):
        ca = os.environ.get("SSL_CERT_FILE")
        ctx = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar),
                                              urllib.request.HTTPSHandler(context=ctx))
        self.last = 0.0

    def get(self, url, referer="", data=None, headers=None):
        """(최종 URL, 상태, 헤더 dict, 바이트). 실패하면 예외."""
        h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "ko,en;q=0.8"}
        if referer:
            h["Referer"] = referer
        if data is not None and not isinstance(data, bytes):
            data = urllib.parse.urlencode(data).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        h.update(headers or {})
        err = None
        for i in range(3):
            wait = DELAY - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            try:
                r = self.op.open(urllib.request.Request(url, data=data, headers=h), timeout=60)
                b = r.read()
                self.last = time.time()
                return r.geturl(), r.status, dict(r.headers.items()), b
            except Exception as e:                   # noqa: BLE001
                self.last = time.time()
                err = e
                time.sleep(2 * (i + 1))
        raise err


def save(task, name, body, meta):
    d = os.path.join(RAW, task)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p + ".part", "wb") as f:
        f.write(body)
    os.replace(p + ".part", p)
    meta = dict(meta, 저장경로=p, 바이트=len(body), sha256=hashlib.sha256(body).hexdigest())
    with open(p + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return p, meta


# ── 5-1 RAAS ──────────────────────────────────────────────────────────────
RAAS_POST = "https://www.fss.or.kr/fss/bbs/B0000167/view.do?nttId=196121&menuNo=200177"


def raas():
    import re
    w = Web()
    fu, st, hd, b = w.get(RAAS_POST)
    page = b.decode("utf-8", "replace")
    p_html, m_html = save("raas", "게시글_nttId196121.html", b,
                          dict(출처URL=RAAS_POST, 최종URL=fu, http_status=st, fetched_at=now()))
    import html as _html
    title = re.search(r'<h3 class="subject">(.*?)</h3>', page, re.S) or re.search(r"<title>(.*?)</title>", page, re.S)
    # <a href="…fileDown.do…" class="btn-attach-download"><i …></i> 파일명.hwp (파일크기: …)</a>
    links = []
    for m in re.finditer(r'<a href="(/fss/cmmn/file/fileDown\.do\?[^"]+)"[^>]*>(.*?)</a>', page, re.S):
        txt = re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()
        if ".hwp" in txt.lower():
            links.append((m.group(1), txt))
    if not links:
        raise SystemExit("게시글에서 hwp 첨부 링크를 못 찾음 — 페이지 구조 확인 필요")
    href, fname = links[0]
    url = urllib.parse.urljoin(fu, href.replace("&amp;", "&"))
    fu2, st2, hd2, body = w.get(url, referer=RAAS_POST)
    if not body.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        raise SystemExit("hwp(OLE) 시그니처 아님 — 앞부분 %r" % body[:40])
    fname = re.sub(r"\s*\(파일크기:[^)]*\)\s*$", "", fname).strip()
    p, meta = save("raas", "RAAS_매뉴얼.hwp", body,
                   dict(출처URL=url, 게시글URL=RAAS_POST, 원파일명=fname, 최종URL=fu2, http_status=st2,
                        content_type=hd2.get("Content-Type", ""),
                        content_disposition=hd2.get("Content-Disposition", ""),
                        게시글제목=(_html.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else ""),
                        fetched_at=now()))
    print("RAAS hwp %s바이트 sha256 %s… ← %s" % (meta["바이트"], meta["sha256"][:12], fname))
    raas_md(p, meta)
    return p, meta


def _section(lines, start, end, what):
    """start(줄 판정 함수)가 참인 첫 줄부터 end 가 참인 줄 앞까지. 못 찾으면 멈춘다(추정 없음)."""
    i = next((k for k, l in enumerate(lines) if start(k, l)), None)
    if i is None:
        raise SystemExit("%s 시작 표지를 못 찾음" % what)
    j = next((k for k in range(i + 1, len(lines)) if end(k, lines[k])), None)
    if j is None:
        raise SystemExit("%s 끝 표지를 못 찾음" % what)
    return i, j


def raas_md(hwp_path, meta):
    import re
    """hwp2md.py(사용자 제공, 수정 없이 사용)로 전체를 텍스트화한 뒤, 두 부분만 글자 그대로 옮긴다.
      · <붙임2> 평가부문별 평가항목 — 「<붙임2>」 줄부터 「<붙임3>」 줄 앞까지
      · Ⅳ. 비계량평가항목 세부 평가기준 중 1. 경영관리리스크 — 「Ⅳ」 줄부터 「󰊲 보험리스크」 줄 앞까지
    """
    import subprocess
    full = os.path.join(os.path.dirname(hwp_path), "RAAS_매뉴얼_전체.md")
    subprocess.run([sys.executable, os.path.join(HERE, "hwp2md.py"), hwp_path, full], check=True)
    lines = open(full, encoding="utf-8").read().split("\n")
    a1, a2 = _section(lines, lambda k, l: l.strip() == "<붙임2>",
                      lambda k, l: l.strip().startswith("<붙임3>"), "붙임2")
    b1, b2 = _section(lines, lambda k, l: l.strip() == "Ⅳ" and k + 1 < len(lines)
                      and lines[k + 1].strip().startswith("비계량평가항목 세부 평가기준"),
                      lambda k, l: l.strip().startswith("󰊲 보험리스크"), "Ⅳ.1 경영관리리스크")
    full_sha = hashlib.sha256(open(full, "rb").read()).hexdigest()
    # 목차의 쪽 번호(원문 목차 그대로) — 「<붙임2> 평가부문별 평가항목\t24」, 「Ⅳ. …」 다음 「1. 경영관리리스크\t53」
    toc = lines[:a1]
    p2 = next((re.search(r"(\d+)\s*$", l).group(1) for l in toc
               if "<붙임2>" in l and re.search(r"\d+\s*$", l)), "목차에 없음")
    k4 = next((k for k, l in enumerate(toc) if l.strip().startswith("Ⅳ. 비계량평가항목 세부 평가기준")), None)
    p4 = (re.search(r"(\d+)\s*$", toc[k4 + 1]).group(1)
          if k4 is not None and k4 + 1 < len(toc) and "경영관리리스크" in toc[k4 + 1] else "목차에 없음")
    head = [
        "# 보험회사 위험기준 경영실태평가(RAAS) 매뉴얼 — 원문 발췌",
        "",
        "- 출처 게시글: %s (%s)" % (meta["게시글URL"], meta.get("게시글제목", "")),
        "- 첨부 원파일명: %s" % meta["원파일명"],
        "- 다운로드 URL: %s" % meta["출처URL"],
        "- 수집일: %s · HTTP %s · %s바이트 · sha256 %s" % (meta["fetched_at"], meta["http_status"],
                                                      meta["바이트"], meta["sha256"]),
        "- 텍스트화: scripts/dart/hwp2md.py(채팅에서 받은 olefile 기반 스크립트, 수정 없음) → "
        "RAAS_매뉴얼_전체.md(sha256 %s)" % full_sha,
        "- 발췌 범위(전체 텍스트의 줄 번호, 1부터): 붙임2 %d~%d행 · Ⅳ.1 경영관리리스크 %d~%d행"
        % (a1 + 1, a2, b1 + 1, b2),
        "- 글자는 바꾸지 않았다. 「󰊱·󰊲…」는 한글 문서의 원문자(①②…)가 사용자 정의 영역 글자로 "
        "나온 것이고, 표 칸 안 줄바꿈은 `<br>`, 칸 구분 `|` 는 `\\|` 로 적혀 있다(hwp2md 표기).",
        "- hwp 는 쪽 정보가 없어 쪽 번호 대신 위 줄 번호와 원문 목차의 쪽(붙임2: %s쪽, Ⅳ.1: %s쪽)을 적는다." % (p2, p4),
        "",
        "---",
        "",
        "## <붙임2> 평가부문별 평가항목 (목차상 %s쪽)" % p2,
        "",
    ]
    mid = ["", "---", "", "## Ⅳ. 비계량평가항목 세부 평가기준 — 1. 경영관리리스크 (목차상 %s쪽)" % p4, ""]
    body = head + lines[a1:a2] + mid + lines[b1:b2]
    dst = os.path.join(HANDOFF, "RAAS_매뉴얼_원문.md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(body).rstrip() + "\n")
    print("RAAS_매뉴얼_원문.md — 붙임2 %d줄 · Ⅳ.1 %d줄" % (a2 - a1, b2 - b1))


# ── 5-4 법령 원문 ─────────────────────────────────────────────────────────
# 7차 law_archive 와 같은 도구(lawclient·resolve·render)를 쓰되, 7차 산출물(law_archive/00_manifest)은
# 건드리지 않는다 — 원본은 dart_out/raw/web9/law/, 원장도 따로.
LAWS = [
    # (요청명, 종류)  — 법령은 계층(시행령)까지 이름에 넣어 찾는다
    ("금융회사 지배구조 감독규정", "rule"),
    ("주식회사 등의 외부감사에 관한 법률 시행령", "law"),
    ("보험업감독규정", "rule"),
    ("보험업감독업무시행세칙", "rule"),
]


def _xml_text(xb, rule):
    """원문 XML → 텍스트(md). 조문·부칙·별표 목록의 글을 문서 순서대로, 글자는 그대로."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xb)
    keep = ({"조문내용", "부칙내용", "별표제목"} if rule else
            {"조문내용", "항내용", "호내용", "목내용", "부칙내용", "별표제목"})
    out = []
    for e in root.iter():
        if e.tag in keep:
            t = "".join(e.itertext()).strip()
            if t:
                out.append(t)
    return "\n\n".join(out)


def laws():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
    import csv
    import lawclient
    import render
    import resolve
    led = os.path.join(RAW, "law", "_call_log.csv")
    client = lawclient.LawClient(led)
    prev = {r["정식명"]: r for r in csv.DictReader(open(os.path.join("law_archive", "00_manifest", "law_list.csv"),
                                                       encoding="utf-8-sig"))}
    rows = []
    for name, kind in LAWS:
        rec = dict(name=name, kind="행정규칙" if kind == "rule" else "법령(시행령)", 상태="", 법령ID="",
                   일련번호="", 시행일자="", 발령_공포일자="", 소관="", 원문XML="", xml_sha256="", 텍스트="",
                   텍스트_sha256="", PDF="", pdf_sha256="", 쪽수="", 출처URL="", collected_at="",
                   차7_일련번호="", 차7_시행일자="", 차7과같은판="", note="")
        try:
            if kind == "rule":
                cur, st, how, cands = resolve.resolve_rule(client, name)
                if not cur:
                    raise RuntimeError("현행 판을 하나로 못 정함(%s): %s" % (st, cands[:5]))
                serial, ef = cur.get("행정규칙일련번호", ""), cur.get("시행일자", "")
                rec.update(법령ID=cur.get("행정규칙ID", ""), 일련번호=serial, 시행일자=ef,
                           발령_공포일자=cur.get("발령일자", ""), 소관=cur.get("소관부처명", ""))
                sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=serial, type="XML")
            else:
                base = name.replace(" 시행령", "")
                res, st, cands = resolve.resolve_law(client, base)
                cur = res.get("시행령", {}).get("현행")
                if not cur:
                    raise RuntimeError("현행 시행령을 못 찾음(%s): %s" % (st, cands[:5]))
                ms, ef = cur.get("법령일련번호", ""), cur.get("시행일자", "")
                rec.update(법령ID=cur.get("법령ID", ""), 일련번호=ms, 시행일자=ef,
                           발령_공포일자=cur.get("공포일자", ""), 소관=cur.get("소관부처명", ""))
                sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=ms, efYd=ef, type="XML")
            if client.count_oc(xb):
                raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
            stem = "%s_%s" % (name.replace(" ", ""), rec["일련번호"])
            p, m = save("law", stem + ".xml", xb, dict(출처URL=murl, http_status=sc, fetched_at=now()))
            rec.update(원문XML=p, xml_sha256=m["sha256"], 출처URL=murl, collected_at=m["fetched_at"])
            txt = _xml_text(xb, kind == "rule")
            md = ["# %s" % name, "", "- 종류: %s · 일련번호 %s · 시행일자 %s · 발령/공포일자 %s · 소관 %s"
                  % (rec["kind"], rec["일련번호"], rec["시행일자"], rec["발령_공포일자"], rec["소관"]),
                  "- 출처: 국가법령정보센터 Open API %s (OC=*** 가림) · 수집일 %s" % (murl, rec["collected_at"]),
                  "- 원문 XML sha256 %s — 아래 글은 그 XML 의 조문·부칙·별표제목 글을 순서대로 옮긴 것(글자 수정 없음)."
                  % rec["xml_sha256"], "", "---", "", txt]
            os.makedirs(os.path.join(HANDOFF, "법령원문_9차"), exist_ok=True)
            mdp = os.path.join(HANDOFF, "법령원문_9차", name.replace(" ", "") + ".md")
            body = "\n".join(md) + "\n"
            with open(mdp, "w", encoding="utf-8") as f:
                f.write(body)
            rec.update(텍스트=mdp, 텍스트_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest())
            # PDF — 7차와 같은 렌더링(원문 XML → HTML → Chromium PDF)
            fn = render.admrul_html if kind == "rule" else render.law_html
            html_text, _nm, labels = fn(xb, rec["시행일자"], rec["일련번호"])
            pdfp = os.path.join(RAW, "law", stem + "_본문.pdf")
            render.html_to_pdf(html_text, pdfp)
            ok, npg, _t = render.pdf_info(pdfp)
            rec.update(PDF=pdfp, pdf_sha256=hashlib.sha256(open(pdfp, "rb").read()).hexdigest(), 쪽수=npg)
            pv = prev.get(name, {})
            rec.update(차7_일련번호=pv.get("법령일련번호", ""), 차7_시행일자=pv.get("시행일자", ""))
            rec["차7과같은판"] = ("Y" if pv and pv.get("법령일련번호") == rec["일련번호"] else
                              "N(7차 이후 바뀐 판)" if pv else "7차 목록에 없음")
            rec["상태"] = "OK"
        except Exception as e:                       # noqa: BLE001 — 사유를 남기고 다음 법령
            rec["상태"] = "실패"
            rec["note"] = client.mask("%s: %s" % (type(e).__name__, e))[:300]
        print("  %-30s %s %s %s" % (name, rec["상태"], rec["일련번호"], rec["note"][:80]))
        rows.append(rec)
    cols = list(rows[0].keys())
    path = os.path.join(WORK, "법령원문_9차.csv")
    os.makedirs(WORK, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("법령 %d건 · OK %d · API 호출 %d" % (len(rows), sum(r["상태"] == "OK" for r in rows), client.n_calls))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    fn = {"raas": raas, "laws": laws}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    fn()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
