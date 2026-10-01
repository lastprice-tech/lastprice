# -*- coding: utf-8 -*-
"""10차 에이전트 A — 손해보험협회(knia.or.kr) 수집: 6-3 · 6-4(손보협회 부분) · 6-5.

    python3 scripts/dart/web10_knia.py terms     # 호스트별 robots.txt·이용약관(저작권정책) 확인 → dart_out/risk10/knia_robots_약관.csv
    python3 scripts/dart/web10_knia.py rule      # 6-3 「보험회사의 제3자 리스크관리 가이드라인」 손보협회판 원본 + md
    python3 scripts/dart/web10_knia.py compare   # 6-3 생보협회판(9차)과 조문 대조 → handoff/원문_10차/제3자가이드라인_대조.csv
    python3 scripts/dart/web10_knia.py posting   # 6-4 손보협회 공시실 지배구조공시 → dart_out/risk10/게시처_knia.csv
    python3 scripts/dart/web10_knia.py catalog   # 6-5 손보협회 규정목록 전체 + 관련 건 원문 → 목록_손보협회_자율규제.csv
    python3 scripts/dart/web10_knia.py all       # 위 순서대로 모두
    python3 scripts/dart/web10_knia.py rulemd            # 받은 원본으로 6-3 md 만 다시 쓰기(요청 없음)
    python3 scripts/dart/web10_knia.py catalog --offline # 받은 목록·원문으로 6-5 CSV·md 다시 쓰기(요청 없음)

산출: handoff/원문_10차/손보협회_제3자가이드라인.md · 제3자가이드라인_대조.csv · 목록_손보협회_자율규제.csv ·
      손보협회_자율규제_원문/<목록번호>_<규정명>.md, dart_out/risk10/게시처_knia.csv · knia_robots_약관.csv ·
      knia_자율규제_변경공고.csv(보조: 변경공고 게시판 58건과 규정목록 이름 대조)
이메일 주소: 손보협회 누리집의 「이메일무단수집거부」 고지를 존중해 handoff 산출물에는 이메일 주소를 「[이메일 주소 가림]」으로
  적는다(그 밖의 글자는 그대로, 원본 파일에는 그대로 있음). 바꾼 건수는 각 md 머리에 적는다.

게시처(2026-10-01 실측, 누리집 메뉴 그대로):
  · www.knia.or.kr  공시·자료실 > 손해보험협회 규정현황 > 규정목록       /data/regulation/regulation01
        표(번호·규정명·개정년월·다운로드). 쪽 넘김은 같은 주소로 POST(keyword, page) — 화면 fnSubmitForm(n) 그대로.
        다운로드 = onclick="location.href='/file/download/<키>'" (GET).
  · www.knia.or.kr  공시·자료실 > 손해보험협회 규정현황 > 자율규제 변경공고 /data/regulation/regulation06
        표(번호·제목·등록일·조회·첨부). 검색 POST(type=1 제목, keyword, page). 게시글 /content?index=N, 첨부 /file/download/<키>.
  · kpub.knia.or.kr 손해보험협회 공시실 > 기타공시 > 지배구조공시 > 공시자료실 /etcDisc/governance/governanceDataList.do
        표(번호·제목·회사명·등록일·첨부·조회수). 검색·쪽 넘김은 같은 주소로 POST(pageNo, menuCd=ETC1602, schType, schKeyword)
        — 화면 goSearch()/goPage(n) 그대로. 상세 = POST governanceDataView.do (governanceDataIdx).

규율(COMMON.md): web10.Web(UA 고정·1.2초 간격·3회 재시도)만 쓴다. 호스트마다 web10.Robots 로 확인하고 막힌 URL 은
요청하지 않는다. 보안장비 차단 화면(「보안정책 위배」)·로그인·캡차가 나오면 우회하지 않고 멈춘다(Stop) — 사유를 남긴다.
www·kpub 의 /robots.txt 는 보안장비가 HTTP 403(「Requested URL is in the Block URL List」)으로 막는다(실측) →
RFC 9309 §2.3.1.3 Unavailable = 제한 없음(web10.Robots 판정). 이용약관·저작권정책은 `terms` 가 따로 확인한다.
원본: dart_out/raw/web10/knia/ (받은 바이트 그대로 + .meta.json). 원문 인용은 글자 그대로, 요약은 요지·note 열에만.
"""
from __future__ import annotations

import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from web10 import Web, save, Robots, now, write_csv, OUT, WORK, RAW  # noqa: E402

TASK = "knia"
DIR = os.path.join(RAW, TASK)
WWW = "https://www.knia.or.kr"
KPUB = "https://kpub.knia.or.kr"
REG01 = WWW + "/data/regulation/regulation01"
REG06 = WWW + "/data/regulation/regulation06"
MENU01 = "손해보험협회 누리집 > 공시·자료실 > 손해보험협회 규정현황 > 규정목록"
MENU06 = "손해보험협회 누리집 > 공시·자료실 > 손해보험협회 규정현황 > 자율규제 변경공고"
GOV_LIST = KPUB + "/etcDisc/governance/governanceDataList.do"
GOV_VIEW = KPUB + "/etcDisc/governance/governanceDataView.do"
GOV_MENU = "손해보험협회 공시실(kpub.knia.or.kr) > 기타공시 > 지배구조공시 > 공시자료실"
RULE_NAME = "보험회사의 제3자 리스크관리 가이드라인"
OLE = bytes.fromhex("d0cf11e0a1b11ae1")
BLOCK_WORDS = ["보안정책 위배", "보안정책에 위배", "Block URL List", "captcha", "CAPTCHA", "자동입력 방지",
               "보안문자", "로봇이 아닙니다", "로그인이 필요", "로그인 후 이용", "Access Denied", "Too Many Requests"]
MAX_PAGES = 400


class Stop(Exception):
    """차단·로그인·캡차·robots 금지·구조 이상 — 우회하지 않고 멈춘다."""


# ── 공용 ──────────────────────────────────────────────────────────────────
_W = None
_ROBOTS = {}


def web():
    global _W
    if _W is None:
        _W = Web()
    return _W


def robots(base):
    """호스트(서브도메인)마다 한 번 — web10.Robots(RFC 9309 판정, robots 원본 저장)."""
    if base not in _ROBOTS:
        _ROBOTS[base] = Robots(web(), base, TASK)
    return _ROBOTS[base]


def text_of(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def flat(s):
    """HTML 조각 → 글(태그 제거·&nbsp; 풀기·연속 공백 하나로). 화면 확인용(인용 열에는 원본 파일 텍스트를 쓴다)."""
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def cd_filename(cd):
    """Content-Disposition 의 파일명(원문). urllib 은 헤더를 latin-1 로 풀어 주므로 바이트로 되돌려 디코딩한다."""
    if not cd:
        return ""
    m = re.search(r"filename\*\s*=\s*([\w-]*)'[^']*'([^;]+)", cd, re.I)
    if m:
        return urllib.parse.unquote(m.group(2).strip().strip('"'), encoding=m.group(1) or "utf-8")
    m = re.search(r'filename\s*=\s*"*(.*?)"*\s*(?:;|$)', cd, re.I)
    if not m:
        return ""
    raw = m.group(1).strip()
    try:
        b = raw.encode("latin-1")
        for enc in ("utf-8", "cp949"):
            try:
                raw = b.decode(enc)
                break
            except UnicodeDecodeError:
                continue
    except UnicodeEncodeError:
        pass
    if re.search(r"%[0-9A-Fa-f]{2}", raw):
        raw = urllib.parse.unquote_plus(raw, encoding="utf-8")
    return raw


def safe_name(s, n=120):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s).strip().strip(".")
    return s[:n] or "noname"


def fetch(url, name, meta=None, data=None, referer="", headers=None):
    """robots 확인 → 받기 → 원본 저장(dart_out/raw/web10/knia/<name>) → 차단 신호 확인.
    (경로, meta, 바이트). robots 금지면 요청하지 않고 Stop. HTTP 4xx/5xx 는 응답 본문을 저장하고 Stop."""
    pu = urllib.parse.urlparse(url)
    base = "%s://%s" % (pu.scheme, pu.netloc)
    rb = robots(base)
    if not rb.allowed(url):
        raise Stop("robots.txt(%s, 판정 %s)가 %s 를 막음 — 요청하지 않음 %s" % (base, rb.status, url, rb.note))
    req = dict(meta or {}, 출처URL=url)
    if data is not None:
        req["요청"] = "POST " + (data if isinstance(data, str) else urllib.parse.urlencode(data))
        if isinstance(data, str):
            data = data.encode("utf-8")
    try:
        fu, st, hd, b = web().get(url, referer=referer, data=data, headers=headers)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:                            # noqa: BLE001
            pass
        p, m = save(TASK, "실패응답_" + name + ".html", body,
                    dict(req, http_status=e.code, fetched_at=now(), 비고="HTTP 오류 응답 본문"))
        t = body.decode("cp949", "replace") if b"charset=euc-kr" in body.lower() or b"\xba\xb8\xbe\xc8" in body \
            else body.decode("utf-8", "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        raise Stop("%s HTTP %s%s (응답 저장 %s)" % (url, e.code, " 차단 신호 %s" % hit if hit else "", p))
    except Exception as e:                           # noqa: BLE001
        raise Stop("%s 접속 실패 %s: %s" % (url, type(e).__name__, e))
    ct = hd.get("Content-Type", "")
    cd = hd.get("Content-Disposition", "")
    p, m = save(TASK, name, b, dict(req, 최종URL=fu, http_status=st, content_type=ct, content_disposition=cd,
                                    원파일명=cd_filename(cd), fetched_at=now()))
    if "text/html" in ct.lower():
        t = b.decode("utf-8", "replace")
        hit = [x for x in BLOCK_WORDS if x in t]
        if hit or "login" in urllib.parse.urlparse(fu).path.lower():
            raise Stop("%s 차단/로그인/캡차 신호 %s 최종URL %s (저장 %s)" % (url, hit, fu, p))
    return p, m, b


def fetch_file(url, prefix, meta, referer=""):
    """첨부 1건 — 받은 뒤 Content-Disposition 파일명으로 이름을 바꿔 다시 저장(같은 바이트, 같은 메타)."""
    tmp = prefix + "_받는중.bin"
    p, m, b = fetch(url, tmp, meta, referer=referer)
    fname = m.get("원파일명", "")
    if "text/html" in m.get("content_type", "").lower() or b[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise Stop("%s 파일 대신 HTML 응답(저장 %s)" % (url, p))
    if not fname:
        ext = ".hwp" if b.startswith(OLE) else ".pdf" if b.startswith(b"%PDF") else ".zip" if b.startswith(b"PK") else ".bin"
        fname = "이름없음" + ext
        m["비고"] = "Content-Disposition 에 파일명 없음 — 확장자는 파일 시그니처로만 붙임"
    keep = {k: v for k, v in m.items() if k not in ("저장경로", "바이트", "sha256")}
    p2, m2 = save(TASK, prefix + "_" + safe_name(fname), b, keep)
    for q in (p, p + ".meta.json"):
        os.remove(q)
    return p2, m2, b


def hwp_to_md(path):
    """hwp(OLE) → scripts/dart/hwp2md.py(사용자 제공, 수정 없음). 같은 폴더에 .md. hwpx 는 zip 안 section*.xml 의 hp:t."""
    stem = os.path.splitext(path)[0]
    dst = stem + ".md"
    b = open(path, "rb").read(8)
    if b.startswith(OLE):
        r = subprocess.run([sys.executable, os.path.join(HERE, "hwp2md.py"), path, dst], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(dst):
            raise RuntimeError("hwp2md 실패: %s" % (r.stderr.strip().splitlines() or [r.stdout])[-1])
        return dst, "scripts/dart/hwp2md.py(olefile 기반, 사용자 제공·수정 없음)로 hwp → md (표는 | 칸, 칸 안 줄바꿈 <br>)"
    if b.startswith(b"PK"):
        import zipfile
        z = zipfile.ZipFile(path)
        secs = sorted([n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)],
                      key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
        out = []
        for n in secs:
            x = z.read(n).decode("utf-8")
            cur = []
            for mm in re.finditer(r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>|</hp:p>", x, re.S):
                if mm.group(0) == "</hp:p>":         # 문단 끝마다 한 줄(표 칸 안 문단도 순서대로)
                    if cur:
                        out.append("".join(cur))
                    cur = []
                else:
                    cur.append(html.unescape(re.sub(r"<[^>]+>", "", mm.group(1))))
            if cur:
                out.append("".join(cur))
        open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
        return dst, "hwpx(zip) Contents/section*.xml 의 hp:t 글을 문단(hp:p) 순서대로"
    raise RuntimeError("hwp/hwpx 시그니처 아님")


def pdf_to_txt(path):
    """PDF → pypdf 쪽마다 「=== p.N ===」 표지 + extract_text() 그대로. 같은 폴더에 .pages.txt."""
    import pypdf
    r = pypdf.PdfReader(path)
    parts = []
    for i, pg in enumerate(r.pages, 1):
        parts.append("=== p.%d ===" % i)
        parts.append(pg.extract_text() or "")
    dst = os.path.splitext(path)[0] + ".pages.txt"
    open(dst, "w", encoding="utf-8").write("\n".join(parts).rstrip() + "\n")
    import pypdf as _p
    return dst, "pypdf %s PdfReader.extract_text() — 쪽마다 「=== p.N ===」 표지, 글자 수정 없음" % _p.__version__, len(r.pages)


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ── 약관·robots ─────────────────────────────────────────────────────────
# 자동 수집·복제 금지로 읽힐 수 있는 낱말. 걸리면 앞뒤 글을 그대로 기록하고, 문맥으로 갈래를 나눈다.
TERM_WORDS = ["자동 수집", "자동수집", "자동으로 수집", "크롤", "스크래", "스크랩", "로봇", "robot", "무단 복제", "무단복제",
              "무단으로", "무단 수집", "무단수집", "기술적 장치", "저작권", "이용약관", "복제", "전재"]
TERM_PAGES = [
    # (호스트, 이름, URL, 무엇을 보려고)
    (WWW, "약관_www_main.html", WWW + "/", "누리집 첫 화면 — 하단(footer) 링크 목록(이용약관·저작권정책 유무)과 이메일무단수집거부 팝업 글"),
    (WWW, "약관_www_privacy-guide01.html", WWW + "/howtouse/privacy-guide01", "하단 링크 「개인정보처리방침」"),
    # 공시실 첫 주소 /index.jsp 는 99바이트 스크립트(location.href="/main.do")뿐이라 /main.do 를 받는다
    (KPUB, "약관_kpub_main.html", KPUB + "/main.do", "공시실 첫 화면 — 하단(footer) 링크 목록"),
    (KPUB, "약관_kpub_useGuide.html", KPUB + "/summary/useGuide/useGuideInf.do", "공시실 > 공시실개요 > 이용가이드"),
]


def footer_links(t):
    m = re.search(r"<footer\b.*?</footer>", t, re.S)
    f = m.group(0) if m else ""
    links = [(h, flat(x)) for h, x in re.findall(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', f, re.S)]
    return [(h, x) for h, x in links if x], bool(m)


def classify_hit(ctx):
    if "이메일" in ctx or "전자우편" in ctx:
        return "이메일 주소 무단수집 거부(이메일 주소 수집 금지 — 자동 수집 일반 금지 아님)"
    if "쿠키" in ctx or "COOKIE" in ctx or "접속 정보" in ctx or "행태정보" in ctx or "자동으로 수집하는 장치" in ctx:
        return "개인정보처리방침의 쿠키·접속정보 자동 수집 고지(협회가 방문자 정보를 수집하는 내용 — 수집 금지 아님)"
    if "특별약관" in ctx or "보험약관" in ctx:
        return "보험 상품 약관(사이트 이용약관 아님)"
    if "RIGHTS RESERVED" in ctx.upper():
        return "저작권 표시(COPYRIGHT … ALL RIGHTS RESERVED) — 자동 수집 금지 문구 아님"
    return "검토 필요"


def terms():
    rows = []
    checked = now()
    for base in (WWW, KPUB):
        rb = robots(base)
        host = urllib.parse.urlparse(base).netloc
        rfiles = sorted(glob.glob(os.path.join(DIR, "robots_%s*" % host)))
        rfiles = [x for x in rfiles if not x.endswith(".meta.json")]
        pages, hits, foot = [], [], []
        stop = ""
        for b2, name, url, why in TERM_PAGES:
            if b2 != base:
                continue
            try:
                p, m, b = fetch(url, name, dict(확인목적=why))
            except Stop as e:
                stop = str(e)
                pages.append("%s → 멈춤: %s" % (url, e))
                break
            t = b.decode("utf-8", "replace")
            fl, has = footer_links(t)
            if "main" in name or "index" in name:
                foot.append("%s 하단 링크(%s): %s" % (m["최종URL"], "footer 태그" if has else "footer 없음",
                                                  " · ".join(x for _, x in fl) or "없음"))
            txt = flat(t)
            seen = set()
            for k in TERM_WORDS:
                for mm in re.finditer(re.escape(k), txt):
                    ctx = txt[max(0, mm.start() - 60): mm.start() + 90]
                    key = (classify_hit(ctx), ctx[50:110])
                    if key in seen:
                        continue
                    seen.add(key)
                    hits.append("[%s] %s: 「…%s…」 → %s" % (name, k, ctx, classify_hit(ctx)))
            pages.append("%s (HTTP %s, %s바이트, sha256 %s, 저장 %s)" % (url, m["http_status"], m["바이트"],
                                                                     m["sha256"][:16], p))
        has_tos = any("이용약관" in x or "저작권" in x for x in foot)
        bad = [h for h in hits if h.endswith("검토 필요")]
        if stop:
            verdict = "확인 불가 — %s" % stop
        elif bad:
            verdict = "검토 필요 — 분류 안 된 낱말 %d건(note)" % len(bad)
        else:
            verdict = ("수집 가능 — 하단에 이용약관·저작권정책 링크 %s; 받은 화면에서 자동 수집 금지 문구 없음%s"
                       % ("있음(확인 필요)" if has_tos else "없음",
                          ". 「이메일무단수집거부」는 이메일 주소 수집 금지라 해당 아님"
                          if any("이메일 주소 무단수집" in h for h in hits) else ""))
        rows.append(dict(host=host, robots_url=base + "/robots.txt", robots_status=rb.status, robots_note=rb.note,
                         robots_saved=" ; ".join(rfiles), terms_pages=" | ".join(pages), footer_links=" | ".join(foot),
                         terms_hits=" | ".join(hits) or "해당 낱말 없음", terms_verdict=verdict, checked_at=checked))
        print("%s robots=%s 약관판정=%s" % (host, rb.status, verdict[:60]))
    cols = ["host", "robots_url", "robots_status", "robots_note", "robots_saved", "terms_pages", "footer_links",
            "terms_hits", "terms_verdict", "checked_at"]
    path = os.path.join(WORK, "knia_robots_약관.csv")
    write_csv(path, cols, rows)
    print("CSV %s — %d행" % (path, len(rows)))
    return rows


def verdict_of(host):
    """terms() 결과(있으면)에서 판정 글. 없으면 빈칸."""
    path = os.path.join(WORK, "knia_robots_약관.csv")
    if not os.path.exists(path):
        return ""
    import csv
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        if r["host"] == host:
            return "robots %s · 약관 %s" % (r["robots_status"], r["terms_verdict"].split(" — ")[0])
    return ""


def require_ok(host):
    v = verdict_of(host)
    if not v:
        raise SystemExit("먼저 `terms` 를 실행해 %s 의 robots·약관 판정을 남겨야 한다" % host)
    if "수집 가능" not in v:
        raise SystemExit("%s 판정이 수집 가능이 아님(%s) — 수집하지 않음" % (host, v))
    return v


# ── 목록 파서 ─────────────────────────────────────────────────────────────
def _total(t):
    m = re.search(r'<p class="num">\s*총\s*<strong>\s*([\d,]+)\s*</strong>\s*건', t)
    return m.group(1).replace(",", "") if m else ""


def _pages(t):
    return set(int(x) for x in re.findall(r"fnSubmitForm\((\d+)\)", t))


def parse_reg01(t):
    """규정목록 표 → [{번호, 규정명, 개정년월, 다운로드, 버튼제목}]. 열 머리도 돌려준다."""
    m = re.search(r'<table class="tbl_bbs[^"]*">(.*?)</table>', t, re.S)
    if not m:
        raise Stop("규정목록 표(tbl_bbs)가 없음 — 구조 변경 또는 차단 의심")
    tb = m.group(1)
    head = [text_of(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
    cap = text_of((re.search(r"<caption>(.*?)</caption>", tb, re.S) or [None, ""])[1] or "")
    rows = []
    body = re.search(r"<tbody>(.*?)</tbody>", tb, re.S)
    for tr in re.findall(r"<tr>(.*?)</tr>", body.group(1) if body else "", re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        links = re.findall(r"location\.href='([^']+)'", tds[3] if len(tds) > 3 else "")
        btn = re.findall(r'class="btn_down"[^>]*title="([^"]*)"', tr)
        rows.append(dict(번호=text_of(tds[0]), 규정명=text_of(tds[1]), 개정년월=text_of(tds[2]),
                         다운로드=[urllib.parse.urljoin(REG01, html.unescape(x)) for x in links],
                         버튼제목=btn, 칸글=flat(tds[3]) if len(tds) > 3 else ""))
    return rows, head, cap


def parse_reg06(t):
    m = re.search(r'<table class="bbs-list[^"]*">(.*?)</table>', t, re.S)
    if not m:
        raise Stop("자율규제 변경공고 표(bbs-list)가 없음 — 구조 변경 또는 차단 의심")
    tb = m.group(1)
    head = [text_of(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
    rows = []
    body = re.search(r"<tbody>(.*?)</tbody>", tb, re.S)
    for tr in re.findall(r"<tr>(.*?)</tr>", body.group(1) if body else "", re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        if len(tds) < 4 or not a:
            continue
        rows.append(dict(번호=text_of(tds[0]), 제목=text_of(a.group(2)),
                         url=urllib.parse.urljoin(REG06, html.unescape(a.group(1))),
                         등록일=text_of(tds[2]), 조회=text_of(tds[3]), 첨부=flat(tds[4]) if len(tds) > 4 else ""))
    return rows, head


def walk(url, first, later, parse, tag, menu, pages_fn=None, total_fn=None):
    """쪽 넘김 목록 전수. first = 1쪽 POST 데이터(None 이면 GET), later(n) = n쪽 POST 데이터.
    (행 목록, 쪽 메타 목록, 사이트 표시 총건수, 표 머리, 중단 사유)."""
    allrows, pmeta, seen = [], [], set()
    total, head, stop = "", [], ""
    page, last = 1, 1
    while page <= MAX_PAGES:
        data = first if page == 1 else later(page)
        try:
            p, m, b = fetch(url, "%s_p%03d.html" % (tag, page), dict(메뉴=menu), data=data, referer=url)
        except Stop as e:
            stop = "%d쪽: %s" % (page, e)
            break
        t = b.decode("utf-8", "replace")
        try:
            res = parse(t)
        except Stop as e:
            stop = "%d쪽: %s" % (page, e)
            break
        rows, head = res[0], res[1]
        total = total or (total_fn or _total)(t)
        sig = tuple(tuple(sorted((k, str(v)) for k, v in r.items())) for r in rows)
        if rows and sig in seen:
            stop = "%d쪽이 앞 쪽과 같은 내용 — 쪽 넘김이 먹지 않음(전수 미확인)" % page
            break
        seen.add(sig)
        for k, r in enumerate(rows, 1):
            r.update(_page=page, _row=k, _raw=p, _sha=m["sha256"], _at=m["fetched_at"])
        allrows.extend(rows)
        pmeta.append(dict(page=page, rows=len(rows), path=p, sha256=m["sha256"], at=m["fetched_at"]))
        last = max([last] + list((pages_fn or _pages)(t)))
        if not rows or page >= last:
            break
        page += 1
    return allrows, pmeta, total, head, stop


# ── 6-3 제3자 리스크관리 가이드라인(손보협회판) ───────────────────────────
MANIFEST = os.path.join(DIR, "제3자_수집목록.json")
RULE_MD = os.path.join(OUT, "손보협회_제3자가이드라인.md")


def parse_post(t):
    """자율규제 변경공고 게시글 → 등록일·조회·제목·내용(글)·첨부[(href, 글)]. 주석 처리된 옛 링크는 빼고 따로 돌려준다."""
    m = re.search(r'<table class="bbs-article">(.*?)</table>', t, re.S)
    if not m:
        raise Stop("게시글 표(bbs-article)가 없음")
    tb = m.group(1)
    cells = {}
    for th, td in re.findall(r'<th scope="row">(.*?)</th>\s*<td[^>]*>(.*?)</td>', tb, re.S):
        cells.setdefault(text_of(th), td)
    att_html = cells.get("첨부", "")
    commented = re.findall(r"<!--(.*?)-->", att_html, re.S)
    live = re.sub(r"<!--.*?-->", "", att_html, flags=re.S)
    atts = [(urllib.parse.urljoin(REG06, html.unescape(h)), text_of(x))
            for h, x in re.findall(r'<a href="([^"]+)"[^>]*class="attach-file"[^>]*>(.*?)</a>', live, re.S)]
    old = [(h, text_of(x)) for c in commented for h, x in re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', c, re.S)]
    body = cells.get("내용", "")
    # 내용 글: 문단(<p>)마다 한 줄, &nbsp; 는 공백으로, 다른 글자는 그대로
    paras = [html.unescape(re.sub(r"<[^>]+>", "", x)).replace("\xa0", " ")
             for x in re.findall(r"<p>(.*?)</p>", body, re.S)] or [flat(body)]
    # 등록일·조회는 한 줄에 th/td 두 쌍
    reg = re.search(r'등록일</th>\s*<td>(.*?)</td>\s*<th scope="row">조회</th>\s*<td>(.*?)</td>', tb, re.S)
    return dict(등록일=text_of(reg.group(1)) if reg else "", 조회=text_of(reg.group(2)) if reg else "",
                제목=text_of(cells.get("제목", "")), 내용=paras, 첨부=atts, 주석처리된옛첨부=old)


def rule():
    require_ok("www.knia.or.kr")
    os.makedirs(DIR, exist_ok=True)
    docs, notes = [], []
    # (1) 자율규제 변경공고 — 제목 검색 「제3자」 (제정·개정 공고 모두 잡기)
    kw = "제3자"
    r6, pm6, tot6, head6, stop6 = walk(REG06, {"type": "1", "keyword": kw, "page": "1"},
                                       lambda n: {"keyword": kw, "page": str(n)}, parse_reg06,
                                       "제3자_변경공고검색", MENU06)
    notes.append("자율규제 변경공고 제목 검색 「%s」: 표시 총 %s건, 받은 행 %d (%s)%s" % (
        kw, tot6, len(r6), ", ".join("%s|%s|%s" % (r["번호"], r["제목"], r["등록일"]) for r in r6),
        " — 중단: " + stop6 if stop6 else ""))
    # (2) 규정목록 — 규정명 검색 「제3자」
    r1, pm1, tot1, head1, stop1 = walk(REG01, {"keyword": kw, "page": "1"},
                                       lambda n: {"keyword": kw, "page": str(n)}, parse_reg01,
                                       "제3자_규정목록검색", MENU01)
    notes.append("규정목록 규정명 검색 「%s」: 표시 총 %s건, 받은 행 %d (%s)%s" % (
        kw, tot1, len(r1), ", ".join("%s|%s|%s" % (r["번호"], r["규정명"], r["개정년월"]) for r in r1),
        " — 중단: " + stop1 if stop1 else ""))
    for n in notes:
        print(n)
    # (3) 규정목록의 해당 규정 파일
    k = 0
    for r in r1:
        if RULE_NAME not in r["규정명"]:
            continue
        for u in r["다운로드"]:
            k += 1
            p, m, b = fetch_file(u, "제3자_규정목록_%d" % k,
                                 dict(게시처=MENU01, 게시화면URL=REG01, 목록검색어=kw, 목록번호=r["번호"],
                                      규정명=r["규정명"], 개정년월=r["개정년월"], 버튼제목="·".join(r["버튼제목"]),
                                      목록원본=r["_raw"], 목록sha256=r["_sha"]), referer=REG01)
            docs.append(dict(kind="규정목록", path=p, meta=m, row=dict((x, r[x]) for x in ("번호", "규정명", "개정년월"))))
    # (4) 변경공고 게시글과 첨부
    for r in r6:
        if RULE_NAME not in r["제목"]:
            continue
        idx = urllib.parse.parse_qs(urllib.parse.urlparse(r["url"]).query).get("index", ["?"])[0]
        p, m, b = fetch(r["url"], "제3자_공고게시글_%s.html" % idx, dict(게시처=MENU06, 목록제목=r["제목"]),
                        referer=REG06)
        post = parse_post(b.decode("utf-8", "replace"))
        post_doc = dict(kind="공고게시글", path=p, meta=m, post=post, row=r)
        docs.append(post_doc)
        for j, (u, label) in enumerate(post["첨부"], 1):
            pf, mf, bf = fetch_file(u, "제3자_공고%s_첨부%d" % (idx, j),
                                    dict(게시처=MENU06, 게시글URL=r["url"], 게시글제목=post["제목"],
                                         게시글등록일=post["등록일"], 첨부표시글=label), referer=r["url"])
            docs.append(dict(kind="공고첨부", path=pf, meta=mf, label=label, post_url=r["url"]))
    # (5) 텍스트화
    for d in docs:
        if d["kind"] == "공고게시글":
            continue
        b = open(d["path"], "rb").read(8)
        if b.startswith(b"%PDF"):
            tp, how, npg = pdf_to_txt(d["path"])
            d.update(text=tp, how=how, pages=npg)
        else:
            tp, how = hwp_to_md(d["path"])
            d.update(text=tp, how=how)
        d["text_sha256"] = sha_file(tp)
        print("  %s %s → %s" % (d["kind"], os.path.basename(d["path"]), os.path.basename(tp)))
    man = dict(collected_at=now(), notes=notes, search_pages=[dict(tag="변경공고검색", pages=pm6),
                                                              dict(tag="규정목록검색", pages=pm1)],
               docs=docs)
    json.dump(man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    write_rule_md(man)
    return man


MASK = "[이메일 주소 가림]"


def mask_email(t):
    """이메일 주소만 MASK 로 바꾼다(손보협회 「이메일무단수집거부」 고지 존중). (글, 바꾼 수)."""
    return re.subn(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", MASK, t)


def write_rule_md(man):
    docs = man["docs"]
    files = [d for d in docs if d["kind"] != "공고게시글"]
    post = [d for d in docs if d["kind"] == "공고게시글"]
    L = ["# %s — 손해보험협회판 원문" % RULE_NAME, ""]
    L.append("- 수집: scripts/dart/web10_knia.py rule · 수집일 %s (KST) · 원본 dart_out/raw/web10/knia/" % man["collected_at"])
    L.append("- 손보협회 누리집의 두 게시처에서 받은 원문을 모두 싣는다. 어느 것이 「최종」인지 판정하지 않는다"
             "(게시처·게시일·표기만 적는다).")
    for n in man["notes"]:
        L.append("- " + n)
    L.append("- robots·약관: www.knia.or.kr — %s" % (verdict_of("www.knia.or.kr") or "terms 미실행"))
    L.append("")
    L.append("## 문서 목록")
    L.append("")
    for i, d in enumerate(files, 1):
        m = d["meta"]
        L.append("%d. %s" % (i, m.get("원파일명") or os.path.basename(d["path"])))
        if d["kind"] == "규정목록":
            L.append("   - 게시처: %s (%s) — 목록 번호 %s · 규정명 「%s」 · 개정년월 %s · 다운로드 버튼 title 「%s」"
                     % (m["게시처"], m["게시화면URL"], m["목록번호"], m["규정명"], m["개정년월"], m.get("버튼제목", "")))
            if "pdf" in m.get("버튼제목", "").lower() and open(d["path"], "rb").read(8).startswith(OLE):
                L.append("   - 버튼 title 은 「pdf 다운로드」이나 받은 파일은 hwp(OLE 시그니처, 원파일명 확장자 .hwp)")
        else:
            L.append("   - 게시처: %s — 게시글 「%s」 (등록일 %s) %s · 첨부 표시 「%s」"
                     % (m["게시처"], m["게시글제목"], m["게시글등록일"], m["게시글URL"], m["첨부표시글"]))
        L.append("   - 출처 URL(다운로드): %s · 최종URL %s" % (m["출처URL"], m.get("최종URL", "")))
        L.append("   - 원파일명(Content-Disposition): %s" % (m.get("원파일명") or "없음"))
        L.append("   - 수집일 %s · HTTP %s · %s바이트 · sha256 %s · Content-Type %s"
                 % (m["fetched_at"], m["http_status"], m["바이트"], m["sha256"], m.get("content_type", "")))
        L.append("   - 텍스트화: %s → %s (sha256 %s)%s" % (d["how"], d["text"], d["text_sha256"],
                                                      " · %d쪽" % d["pages"] if d.get("pages") else
                                                      " · hwp 라 쪽 번호 없음(아래 인용 위치는 이 파일의 줄 번호)"))
    for d in post:
        m, p = d["meta"], d["post"]
        L.append("- 공고 게시글 HTML: %s · HTTP %s · %s바이트 · sha256 %s · 저장 %s"
                 % (m["출처URL"], m["http_status"], m["바이트"], m["sha256"], d["path"]))
        if p["주석처리된옛첨부"]:
            L.append("  - 게시글 HTML 안에 주석(<!-- -->)으로 가려진 옛 첨부 링크(받지 않음): %s"
                     % " , ".join("%s %s" % tuple(x) for x in p["주석처리된옛첨부"]))
    L += ["", "---", ""]
    for d in post:
        p = d["post"]
        L.append("## 공고 게시글 본문 — 「%s」 (등록일 %s, 조회 %s)" % (p["제목"], p["등록일"], p["조회"]))
        L.append("")
        L.append("- 출처: %s · 텍스트화: 게시글 HTML 「내용」 칸의 <p> 문단마다 한 줄(태그 제거, &nbsp; → 공백, 다른 글자 그대로)"
                 % d["meta"]["출처URL"])
        L.append("")
        L += ["```text"] + p["내용"] + ["```", ""]
    for i, d in enumerate(files, 1):
        m = d["meta"]
        L.append("## %d. %s" % (i, m.get("원파일명") or os.path.basename(d["path"])))
        L.append("")
        L.append("- 출처 %s · sha256 %s · 텍스트화 %s" % (m["출처URL"], m["sha256"], d["how"]))
        L.append("- 아래는 텍스트화 결과 파일 %s 의 글 전체를 글자 그대로 옮긴 것이다." % d["text"])
        L.append("")
        body, nmask = mask_email(open(d["text"], encoding="utf-8").read().rstrip("\n"))
        if nmask:
            L.append("- 이메일 주소 %d건은 「%s」로 바꿔 적었다 — 손보협회 누리집의 「이메일무단수집거부」 고지(2011.09.29 게시)에 "
                     "따라 이메일 주소는 옮기지 않는다. 그 밖의 글자는 그대로이며 원본 파일·텍스트화 파일에는 그대로 있다."
                     % (nmask, MASK))
            L.append("")
        L.append("<!-- 원문 시작: %s -->" % os.path.basename(d["text"]))
        L.append(body)
        L.append("<!-- 원문 끝: %s -->" % os.path.basename(d["text"]))
        L.append("")
    os.makedirs(OUT, exist_ok=True)
    open(RULE_MD, "w", encoding="utf-8").write("\n".join(L).rstrip() + "\n")
    print("md %s — 문서 %d건" % (RULE_MD, len(files)))



def rulemd():
    """받은 원본으로 md 만 다시 쓴다(요청 없음)."""
    write_rule_md(json.load(open(MANIFEST, encoding="utf-8")))


# ── 6-3 대조 ─────────────────────────────────────────────────────────────
KLIA_MD = os.path.join("handoff", "생보협회_자율규제_원문", "원문_21297-1_보험회사의 제3자 리스크관리 가이드라인(20251201).md")
KLIA_URL = "https://www.klia.or.kr/FileDown.do?fileNo=21297&seq=1"
KLIA_DOC = "보험회사의 제3자 리스크관리 가이드라인(20251201).hwp"
KLIA_LIST = "handoff/목록_생보협회_자율규제.csv"
CMP_CSV = os.path.join(OUT, "제3자가이드라인_대조.csv")
CMP_COLS = ["조문", "주제", "생보_조문", "생보_요지", "손보_조문", "손보_요지", "차이여부", "생보_source_text",
            "손보_source_text", "생보_출처", "손보_출처", "priority", "note", "collected_at"]

# 사용자가 우선 보라고 한 주제(작업 지시 그대로) — 단위 열쇠 → 이름
PRIORITY = {
    "본칙 제2조": "업무위탁 정의",
    "본칙 제3조": "적용 범위",
    "본칙 제11조": "판매위탁리스크",
    "별첨1 표제": "판매위탁리스크", "별첨1 제1조": "판매위탁리스크", "별첨1 제2조": "판매위탁리스크",
    "별첨1 제3조": "판매위탁리스크", "별첨1 제4조": "판매위탁리스크",
    "부칙 제1조": "유예 규정",
    "본칙 제14조": "중점관리 기준",
    "별첨2": "중점관리 기준",
}

# 요지 — 사용자가 요청한 요약 열(원문에 있는 내용만, 한두 문장). 열쇠는 단위.
GIST = {
    "표제": "가이드라인 제목과 제정일 표기.",
    "제1장": "제1장 총칙(장 제목).",
    "본칙 제1조": "보험회사가 업무위탁에 따른 제3자 리스크를 관리하기 위해 준수할 최소한의 사항을 제시하는 것이 목적.",
    "본칙 제2조": "보험회사·보험대리점·제3자 리스크·제3자 리스크관리 체계·업무위탁·이사회 등·경영진 7개 용어를 정의. "
                "업무위탁은 인가 등을 받은 금융업 영위를 위해 제3자의 용역·시설 등을 계속적으로 활용하는 행위이고, "
                "후선업무 관련 단순 집행업무 등 금융업 영위와 직접 관계없는 위탁계약은 제외.",
    "본칙 제3조": "제3자와 업무위탁 계약을 체결하는 모든 보험회사가 적용 대상.",
    "본칙 제4조": "전사 리스크관리 프로세스와 통합된 제3자 리스크 관리체계를 회사 규모·복잡성·위탁계약 특성을 감안해 "
                "구축·시행·유지하고, 책임을 사업영역·사업단위별로 분장.",
    "제2장": "제2장 제3자 리스크관리 체계(장 제목).",
    "본칙 제5조": "현재·신규 리스크를 포함한 중요 리스크를 고려해 정량·정성 방법으로 측정하고, 금융당국 제공 또는 자체 "
                "체크리스트 양식을 활용할 수 있음.",
    "본칙 제6조": "조기경보 등 모니터링 절차와 경감 전략·도구를 갖추고 수용 불가 리스크는 업무 중단·변경을 고려. "
                "리스크 관리 정책에 넣을 8개 사항과 활용할 수 있는 내부통제 방법 5개를 열거.",
    "본칙 제7조": "제3자 리스크와 측정·조치계획을 이사회 또는 경영진에 보고하고, 보고절차를 문서화하며 긴급 사항은 "
                "보고 주기와 관계없이 보고.",
    "본칙 제8조": "이사회가 제3자 리스크 관리의 최종책임을 지고(리스크관리위원회·경영진에 일부 위임 가능), 리스크 편중에 "
                "유의해 정책 주요사항을 심의·의결하며 체계를 정기 점검·개정·승인하고 내부감사 점검을 확인.",
    "본칙 제9조": "경영진은 이사회 정책 이행을 위해 체계를 구축·시행·유지하고 이행 결과를 이사회 등에 보고하며, "
                "권한·책임 부여, 필요 자원 확보, 담당자 간 협력 환경을 조성.",
    "본칙 제10조": "단위 사업부문·독립적 리스크 관리부문(준법조직 포함)·내부감사로 이루어진 3단계 통제체계를 구축하고 "
                 "역할·책임을 명확히 부여(한 부문이 1·2차를 함께 맡으면 2차 독립성 확보·문서화).",
    "본칙 제11조": "보험상품 판매 관련 중요 업무·기능 위탁에서 생기는 운영리스크(판매위탁리스크)를 중요 리스크로 선정해 "
                 "식별·측정하고, 이를 맡을 지원조직을 구성·유지(업무 7개 열거). 인식·측정 원칙은 [별첨1].",
    "제3장": "제3장 계약 단계별 리스크관리(장 제목).",
    "본칙 제12조": "계약 전 거래상대방을 평가해 리스크를 감내 수준 이내로 하고, 중요 업무 위탁 시 미위탁 업무와 적어도 "
                 "동일한 수준의 감독, 현장실사(불가 시 공동실사·서면심사 등 대체)와 수탁자 전문성·이해도·수행능력 확인.",
    "본칙 제13조": "서면 계약서에 수탁자 업무범위·수준, 보안요구사항, 점검권한·자료요구권한과 수탁자 협조, 소비자보호 등을 "
                 "명확히 규정하고, 계약 체결·개정 시 고려사항 7개를 열거.",
    "본칙 제14조": "리스크 수준·업무중요도를 고려해 중점관리 위탁계약을 선정하고, 동일 수탁자에게 중요도 높은 업무를 다수 "
                 "위탁하면 그 계약은 반드시 포함. 세부 선정기준은 [별첨2].",
    "본칙 제15조": "계약기간 중 제3자 리스크를 주기적으로 모니터링하고 중대한 징후는 경영진에 즉시 보고·대응하며, "
                 "중점관리 위탁계약은 평가주기 단축 등 강화 관리, 위탁업무 정기 점검·경영진 보고.",
    "본칙 제16조": "계약기간 중 중대한 사고에 대비한 업무연속성 계획(BCP)을 마련하고 정기적으로 적정성을 점검.",
    "본칙 제17조": "대체서비스 제공자 확보·정보보호 및 파기·소비자 피해방지 등을 포함한 계약종료 절차를 마련하고 종료 후에도 "
                 "잔여 리스크를 점검·관리.",
    "본칙 제18조": "업무위탁과 제3자 리스크관리 활동 기록을 문서화(전자문서 포함)해 대표이사등이 정한 기간 동안 보관·유지.",
    "제4장": "제4장 보칙(장 제목).",
    "본칙 제19조": "가이드라인 시행에 필요한 세부사항은 보험회사가 별도로 정할 수 있음.",
    "부칙": "부칙(제목).",
    "부칙 제1조": "2025년 12월 1일 시행. 판매위탁리스크 외 제3자 리스크는 2026년 6월 30일까지 적용 유예 가능, "
                "2023년 12월 31일이 속하는 사업연도말 자산총액 5조원 미만 보험회사는 2026년 12월 1일까지 적용 유예.",
    "별첨 목록": "[별첨1]~[별첨3] 제목 목록.",
    "별첨1 표제": "[별첨1] 판매위탁리스크 인식 및 측정에 관한 원칙(제목).",
    "별첨1 제1조": "판매위탁리스크 인식·측정 원칙을 제시해 보험소비자 보호와 건전한 모집질서 확립이 목적.",
    "별첨1 제2조": "보험대리점과의 판매위탁 전 과정에서 판매위탁리스크를 식별하고, 위탁 전후 리스크 증감 측정·직접 판매와 "
                 "비교 분석 등으로 통제·경감·이전하며, 수용 불가 시 위탁업무 중단 또는 보완장치 마련 등을 통한 변경을 고려.",
    "별첨1 제3조": "적절한 수단·기법으로 정량·정성 측정하며, 정량 지표(불완전판매율·민원, 제재·금융사고 이력 등)와 정성 지표"
                 "(대리점 내부통제·소비자보호·리스크 거버넌스·설계사 관리·변칙 영업 등)를 활용할 수 있음.",
    "별첨1 제4조": "필요시 금융당국이 IAIS 국제기준 등을 참고해 체크리스트 표준(안)을 제공할 수 있음.",
    "별첨2": "중점관리 위탁계약 선정 기준 표. 업권 공통(계약 금액, 내부자료·고객정보 접근, 특정 수탁자 위탁집중에 따른 "
           "집중리스크 — 유형에 금융지주사 내 다수 자회사의 동일 업무 위탁 포함, 위탁 업무 유형, 지정대리인, 계약체결 부서 판단)과 "
           "보험업권(판매위탁 연간 매출액이 중요성 기준금액 이상). 美 OCC·FDIC·FRB 가이드라인 참고 상자 포함.",
    "별첨3": "수탁사 실사 체크리스트(예시) 표 — 기본사항(전략·이력·재무건전성·지배구조·주요인력·법규 준수·재위탁·보험), "
           "리스크 관리(내부통제·리스크관리 역량, 정보보안·재해복구), 기타(평판, 해외 수탁자 관할권 리스크).",
}

RX_JANG = re.compile(r"^제(\d+)장\s")
RX_JO = re.compile(r"^제(\d+)조\s*\(([^)]*)\)")
RX_BC = re.compile(r"^\[별첨\s*(\d+)\]\s*(.*)$")


def segment(lines):
    """hwp2md 텍스트 줄 → 단위 [{key, 조문, 주제, start, end(포함), text}] (줄 번호는 1부터).
    표제(제1장 앞) · 제n장 · 본칙 제n조 · 부칙 · 부칙 제n조 · 별첨 목록 · 별첨1 표제 · 별첨1 제n조 · 별첨2 · 별첨3."""
    units, cur = [], None
    sec, lastbc, mode = "본칙", 0, ""

    def start(key, label, topic, i):
        nonlocal cur
        cur = dict(key=key, 조문=label, 주제=topic, start=i + 1, lines=[])
        units.append(cur)

    start("표제", "표제", "제목·제정일", 0)
    for i, l in enumerate(lines):
        s = l.strip()
        mj, mo, mb = RX_JANG.match(s), RX_JO.match(s), RX_BC.match(s)
        if mj and sec == "본칙":
            start("제%s장" % mj.group(1), s, s, i)
        elif s == "부칙":
            sec = "부칙"
            start("부칙", "부칙", "부칙", i)
        elif mb:
            n = int(mb.group(1))
            if mode != "본문" and (mode == "" or n > lastbc):
                if mode == "":
                    start("별첨 목록", "별첨 목록", "별첨 목록", i)
                mode, lastbc = "목록", n
            else:
                mode, sec = "본문", "별첨%d" % n
                if n == 1:
                    start("별첨1 표제", s, mb.group(2), i)
                else:
                    start("별첨%d" % n, s, mb.group(2), i)
        elif mo and (sec in ("본칙", "부칙", "별첨1")):
            start("%s 제%s조" % (sec, mo.group(1)), "%s%s" % ("" if sec == "본칙" else sec + " ", s[:mo.end()]),
                  mo.group(2), i)
        cur["lines"].append((i + 1, l))
    out = []
    for u in units:
        ls = u.pop("lines")
        while ls and not ls[-1][1].strip():
            ls.pop()
        while ls and not ls[0][1].strip():
            ls.pop(0)
        if not ls:
            continue
        u.update(start=ls[0][0], end=ls[-1][0], text="\n".join(x for _, x in ls))
        out.append(u)
    return out


def nows(s):
    return re.sub(r"\s+", "", s)


def diff_frag(a, b, la="생보", lb="손보", ctx=6, limit=6):
    """공백 뺀 두 글의 다른 조각 — 가까운 차이는 한 묶음으로, 양쪽 모두 자기 글자로(앞뒤 ctx 글자 곁들임).
    [ ] 안이 다른 글자. 차이 판정은 공백 제거 기준이라 조각도 공백을 뺀 글이다."""
    import difflib
    x, y = nows(a), nows(b)
    sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
    out = []
    for g in sm.get_grouped_opcodes(ctx):
        fx, fy = [], []
        for op, i1, i2, j1, j2 in g:
            if op == "equal":
                fx.append(x[i1:i2])
                fy.append(y[j1:j2])
            else:
                fx.append("[%s]" % x[i1:i2])
                fy.append("[%s]" % y[j1:j2])
        out.append("%s 「%s」 ↔ %s 「%s」" % (la, "".join(fx), lb, "".join(fy)))
    more = len(out) - limit
    return out[:limit] + (["… 외 %d곳" % more] if more > 0 else [])


def find_word(text, word="금융지주"):
    hits = []
    for l in text.split("\n"):
        if word in l:
            for frag in re.split(r"<br>|\|", l):
                if word in frag:
                    hits.append(frag.strip())
    return hits


def compare():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    files = [d for d in man["docs"] if d["kind"] != "공고게시글"]
    regd = [d for d in files if d["kind"] == "규정목록"]
    draft = [d for d in files if d["kind"] == "공고첨부" and "전문" in (d["meta"].get("원파일명") or d["label"])]
    if len(regd) != 1:
        raise SystemExit("규정목록 원문이 %d건 — 대조 기준을 하나로 정할 수 없어 멈춘다" % len(regd))
    sb = regd[0]
    sb_lines = open(sb["text"], encoding="utf-8").read().split("\n")
    lb_lines = open(KLIA_MD, encoding="utf-8").read().split("\n")
    # 손보 원문이 handoff md 안에서 시작하는 줄(「<!-- 원문 시작: … -->」 다음 줄)
    md_lines = open(RULE_MD, encoding="utf-8").read().split("\n")
    mk = "<!-- 원문 시작: %s -->" % os.path.basename(sb["text"])
    off = md_lines.index(mk) + 1 if mk in md_lines else None   # 표지 줄의 1부터 줄 번호 — 텍스트 n줄 = off + n
    U_l, U_s = segment(lb_lines), segment(sb_lines)
    U_d = segment(open(draft[0]["text"], encoding="utf-8").read().split("\n")) if draft else []
    dl, ds, dd = ({u["key"]: u for u in U} for U in (U_l, U_s, U_d))
    keys = [u["key"] for u in U_l] + [u["key"] for u in U_s if u["key"] not in dl]
    klia_at, klia_row = "", ""
    import csv
    for n, r in enumerate(csv.DictReader(open(KLIA_LIST, encoding="utf-8-sig")), 1):
        if r["url"] == KLIA_URL:
            klia_at, klia_row = r["collected_at"], "%d행(머리행 제외)" % n
    sm = sb["meta"]
    rows = []
    for k in keys:
        a, b = dl.get(k), ds.get(k)
        note = []
        if a and b:
            if nows(a["text"]) == nows(b["text"]):
                diff = "같음"
                if a["text"] != b["text"]:
                    note.append("공백·줄바꿈만 다름(공백 제거 후 같음): " + " ; ".join(
                        "생보 %r ↔ 손보 %r" % (x, y) for x, y in zip(a["text"].split("\n"), b["text"].split("\n"))
                        if x != y and nows(x) == nows(y))[:400])
            else:
                diff = "다름"
                note.append("다른 곳(공백 제거 후 비교, [ ] 안이 다른 글자): " + " / ".join(diff_frag(a["text"], b["text"])))
            if a["주제"] != b["주제"]:
                note.append("조문 제목 다름: 생보 %r · 손보 %r" % (a["주제"], b["주제"]))
        elif a:
            diff = "생보판에만"
        else:
            diff = "손보판에만"
        # 손보 제정(안) 전문(2025-09-18 공고 첨부)과 견줌 — 판정 없이 사실만
        if draft:
            c = dd.get(k)
            if b and c:
                if nows(b["text"]) == nows(c["text"]):
                    note.append("손보 제정(안) 전문(2025-09-18 공고 첨부)과 견줌: 같음")
                else:
                    note.append("손보 제정(안) 전문(2025-09-18 공고 첨부)과 견줌: 다름 — " + " / ".join(
                        diff_frag(c["text"], b["text"], "제정(안)", "규정목록판")))
            elif b and not c:
                note.append("손보 제정(안) 전문에는 이 단위 없음")
        pr = PRIORITY.get(k, "")
        if pr == "중점관리 기준" or any("금융지주" in (u or {}).get("text", "") for u in (a, b)):
            fa = find_word(a["text"]) if a else []
            fb = find_word(b["text"]) if b else []
            note.append("금융지주 내 다수 자회사의 같은 수탁자 위탁 기준 — 생보: %s · 손보: %s" % (
                "있음(「%s」)" % " / ".join(fa) if fa else "문서에 없음(이 단위 원문에 「금융지주」 낱말 없음)",
                "있음(「%s」)" % " / ".join(fb) if fb else "문서에 없음(이 단위 원문에 「금융지주」 낱말 없음)"))
            if k == "본칙 제14조":
                note.append("제14조 본문에는 없고 ③이 세부기준을 [별첨2]로 넘김 — [별첨2] 행 참조")
        if k == "본칙 제2조":
            note.append("업무위탁 정의는 제2조 제5호(양쪽 원문). 제2호는 보험대리점(판매위탁 계약 상대) 정의")
        gist = GIST.get(k, "")
        gist_s = gist
        if k == "표제" and b and "|" in b["text"]:
            gist_s = gist + " 문서 머리 표 칸에도 제목이 있음."
        elif diff == "다름" and k != "표제":
            gist_s = gist + " (생보판과 글이 달라 요지 재검토 필요 — note 참조)"
        page_note = "hwp 라 쪽 번호 없음 — md 줄 번호"
        rows.append({
            "조문": k, "주제": (a or b)["주제"],
            "생보_조문": a["조문"] if a else "문서에 없음", "생보_요지": gist if a else "문서에 없음",
            "손보_조문": b["조문"] if b else "문서에 없음", "손보_요지": gist_s if b else "문서에 없음",
            "차이여부": diff,
            "생보_source_text": a["text"] if a else "문서에 없음",
            "손보_source_text": mask_email(b["text"])[0] if b else "문서에 없음",
            "생보_출처": ("%s · %s(생보협회 2025.11.28 제정, 9차 목록 %s %s, 9차 수집 %s) · %s · %s %d~%d행 (%s)"
                       % (KLIA_URL, KLIA_DOC, KLIA_LIST, klia_row, klia_at or "기록 없음", a["조문"], KLIA_MD, a["start"],
                          a["end"], page_note) if a else "문서에 없음"),
            "손보_출처": ("%s · %s(손보협회 규정목록, 개정년월 %s) · %s · %s %s행 (텍스트화 파일 %s %d~%d행; %s)"
                       % (sm["출처URL"], sm.get("원파일명", ""), sm.get("개정년월", ""), b["조문"], RULE_MD,
                          "%d~%d" % (b["start"] + off, b["end"] + off) if off else "?",
                          sb["text"], b["start"], b["end"], page_note) if b else "문서에 없음"),
            "priority": pr, "note": " / ".join(note),
            "collected_at": sm["fetched_at"],
        })
    write_csv(CMP_CSV, CMP_COLS, rows)
    from collections import Counter
    print("CSV %s — %d행 %s" % (CMP_CSV, len(rows), dict(Counter(r["차이여부"] for r in rows))))
    return rows



# ── 6-4 게시처 — 손보협회 공시실 지배구조공시 ─────────────────────────────
POST_CSV = os.path.join(WORK, "게시처_knia.csv")
POST_COLS = ["corp_label", "site", "url", "found", "checked_at", "note", "evidence_file", "evidence_sha256"]
CORPS = [
    # (corp_label, 회사명 칸 검색어들, 전체(제목+회사명) 검색어들, 회사명 칸 일치 판정 낱말)
    ("메리츠금융지주", ["메리츠금융지주"], ["메리츠금융"], "메리츠금융"),
    ("한국투자금융지주", ["한국투자금융지주", "한국투자"], ["한국투자", "한투"], "한국투자"),
]
FY_FROM = "2026-01-01"          # FY2025 연차보고서는 2026년(3월경) 게시 — 등록일 기준으로 가른다(표기만)


def parse_gov(t):
    m = re.search(r'<main id="content".*?</main>', t, re.S)
    if not m:
        raise Stop("공시실 본문(main#content)이 없음 — 구조 변경 또는 차단 의심")
    mm = m.group(0)
    tb = re.search(r"<table>(.*?)</table>", mm, re.S)
    if not tb:
        raise Stop("공시자료실 표가 없음")
    head = [text_of(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb.group(1), re.S)]
    rows = []
    body = re.search(r"<tbody>(.*?)</tbody>", tb.group(1), re.S)
    for tr in re.findall(r"<tr>(.*?)</tr>", body.group(1) if body else "", re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 6:
            continue
        idx = re.search(r"goDetail\('(\d+)'\)", tr)
        f = re.search(r'<a href="(/file/download/[^"]+)"', tds[4])
        rows.append(dict(번호=text_of(tds[0]), 제목=text_of(tds[1]), 회사명=text_of(tds[2]), 등록일=text_of(tds[3]),
                         첨부=urllib.parse.urljoin(GOV_LIST, f.group(1)) if f else "", 조회수=text_of(tds[5]),
                         idx=idx.group(1) if idx else ""))
    empty = "조회내용이 없습니다" in flat(tb.group(1))
    return rows, head, empty


def _gov_pages(t):
    return set(int(x) for x in re.findall(r"goPage\((\d+)\)", t))


def _gov_total(t):
    rows = parse_gov(t)[0]
    nums = [int(r["번호"]) for r in rows if r["번호"].isdigit()]
    return str(max(nums)) if nums else "0"


def gov_search(styp, kw, tag):
    base = {"governanceDataIdx": "", "menuCd": "ETC1602", "schType": styp, "schKeyword": kw}
    rows, pm, tot, head, stop = walk(GOV_LIST, dict(base, pageNo="1"), lambda n: dict(base, pageNo=str(n)), parse_gov,
                                     tag, GOV_MENU, pages_fn=_gov_pages, total_fn=_gov_total)
    return dict(type=styp, kw=kw, rows=rows, pages=pm, total=tot, head=head, stop=stop)


def gov_view(idx, ctx, name):
    data = {"pageNo": "1", "governanceDataIdx": idx, "menuCd": "ETC1602", "schType": ctx[0], "schKeyword": ctx[1]}
    p, m, b = fetch(GOV_VIEW, name, dict(메뉴=GOV_MENU, 상세idx=idx), data=data, referer=GOV_LIST)
    t = b.decode("utf-8", "replace")
    cells = {text_of(th): td for th, td in re.findall(r'<th scope="row">(.*?)</th>\s*<td>(.*?)</td>', t, re.S)}
    files = [(urllib.parse.urljoin(GOV_VIEW, h), text_of(x))
             for h, x in re.findall(r'<a href="(/file/download/[^"]+)">(.*?)</a>', cells.get("공시자료", ""), re.S)]
    return p, m, dict(제목=text_of(cells.get("제목", "")), 회사명=text_of(cells.get("회사명", "")),
                      등록일=text_of(cells.get("등록일", "")), 첨부=files)


def desc(sr):
    return "%s 검색(schType=%s) 「%s」: 결과 %s%s" % (
        {"COMPANY": "회사명", "TITLE": "제목", "ALL": "전체"}[sr["type"]], sr["type"], sr["kw"],
        "%d행(%d쪽, 목록 번호 최대 %s)" % (len(sr["rows"]), len(sr["pages"]), sr["total"]) if sr["rows"] else "0행(「조회내용이 없습니다.」)",
        " — 중단: " + sr["stop"] if sr["stop"] else "")


def posting():
    require_ok("kpub.knia.or.kr")
    checked = now()
    # 지배구조공시 안내 화면(메뉴 근거) + 제목 「연차보고서」 검색 전수(회사명 목록 근거)
    pi, mi, bi = fetch(KPUB + "/etcDisc/governance/governanceInf.do", "게시처_지배구조공시안내.html", dict(메뉴=GOV_MENU))
    ann = gov_search("TITLE", "연차보고서", "게시처_제목검색_연차보고서")
    fy = [r for r in ann["rows"] if r["등록일"] >= FY_FROM]
    fy_corps = sorted(set(r["회사명"] for r in fy))
    all_corps = sorted(set(r["회사명"] for r in ann["rows"]))
    print(desc(ann))
    out = []
    for label, comp_kws, all_kws, word in CORPS:
        srs = [gov_search("COMPANY", k, "게시처_회사명검색_%s" % k) for k in comp_kws]
        srs += [gov_search("ALL", k, "게시처_전체검색_%s" % k) for k in all_kws]
        for sr in srs:
            print(" ", desc(sr))
        mine = {}
        for sr in srs + [ann]:
            for r in sr["rows"]:
                if word in r["회사명"]:
                    mine[r["idx"] or r["번호"]] = r
        rep = [r for r in mine.values() if "연차보고서" in r["제목"]]
        rep_fy = sorted([r for r in rep if r["등록일"] >= FY_FROM], key=lambda r: r["등록일"])
        notes = ["본 화면: %s (%s)" % (GOV_MENU, GOV_LIST)]
        notes += [desc(sr) for sr in srs]
        notes.append(desc(ann))
        ev, evs, url = "", "", GOV_LIST
        if rep_fy:
            found = "Y"
            for k, r in enumerate(rep_fy, 1):
                p, m, v = gov_view(r["idx"], ("COMPANY", comp_kws[0]), "게시처_상세_%s_%s.html" % (label, r["idx"]))
                notes.append("게시글: 번호 %s · 제목 「%s」 · 회사명 「%s」 · 등록일 %s · 조회수 %s · 상세(POST %s governanceDataIdx=%s) "
                             "화면 제목 「%s」 · 공시자료 %s" % (
                                 r["번호"], r["제목"], r["회사명"], r["등록일"], r["조회수"], GOV_VIEW, r["idx"], v["제목"],
                                 " , ".join("%s(%s)" % (x, h) for h, x in v["첨부"]) or "없음"))
                if k == 1:
                    ev, evs = p, m["sha256"]
                    url = "%s (POST governanceDataIdx=%s; 목록 %s 회사명 검색 「%s」)" % (GOV_VIEW, r["idx"], GOV_LIST, comp_kws[0])
            notes.append("첨부 파일은 받지 않음(게시 여부 확인 작업 — 목록·상세 화면만 저장)")
        else:
            found = "N"
            others = sorted(set(r["제목"] for r in mine.values()))
            notes.append("이 회사(회사명 칸에 「%s」) 게시글 %d건, 그중 제목에 「연차보고서」 %d건(등록일 %s 이후 %d건)%s"
                         % (word, len(mine), len(rep), FY_FROM, len(rep_fy),
                            " — 이 회사 게시글 제목: " + " , ".join(others[:20]) if others else ""))
            notes.append("제목 「연차보고서」 검색 결과 중 등록일 %s 이후 게시 회사명(사이트 표기 그대로) %d곳: %s"
                         % (FY_FROM, len(fy_corps), " · ".join(fy_corps)))
            notes.append("같은 검색 전체 기간 회사명 %d곳: %s" % (len(all_corps), " · ".join(all_corps)))
            first = next((sr for sr in srs if sr["pages"]), None)
            if first:
                ev, evs = first["pages"][0]["path"], first["pages"][0]["sha256"]
        stops = [sr["stop"] for sr in srs + [ann] if sr["stop"]]
        if stops:
            found = "확인 불가" if found != "Y" else found
            notes.append("중단: " + " ; ".join(stops))
        out.append(dict(corp_label=label, site="손해보험협회", url=url, found=found, checked_at=checked,
                        note=" / ".join(notes), evidence_file=ev, evidence_sha256=evs))
        print("%s → %s" % (label, found))
    write_csv(POST_CSV, POST_COLS, out)
    print("CSV %s — %d행" % (POST_CSV, len(out)))
    return out



# ── 6-5 손보협회 자율규제(규정목록) 전체 ──────────────────────────────────
CAT_CSV = os.path.join(OUT, "목록_손보협회_자율규제.csv")
CAT_COLS = ["name", "enacted_or_amended", "category", "url", "related", "file_saved", "file_sha256", "collected_at", "note"]
CAT_DIR = os.path.join(OUT, "손보협회_자율규제_원문")
ANN_CSV = os.path.join(WORK, "knia_자율규제_변경공고.csv")
ANN_COLS = ["번호", "제목", "등록일", "조회", "첨부", "url", "규정목록_일치", "collected_at", "note"]


def cached(url):
    """같은 출처URL 로 이미 받은 원문 파일(.meta.json)이 있으면 (경로, meta)."""
    for mp in glob.glob(os.path.join(DIR, "*.meta.json")):
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:                            # noqa: BLE001
            continue
        f = mp[:-len(".meta.json")]
        if m.get("출처URL") == url and os.path.exists(f) and not f.endswith(".html") and m.get("http_status") == 200:
            return f, m
    return None


def ann_name(title):
    """변경공고 제목에서 규정명 부분만(대조용, 기계적): 「…」(또는 ？…？) 안 글이 있으면 그것, 없으면 끝의
    「제정/개정/폐지 (공고)」를 뗀 것."""
    m = re.search(r"[「？](.+?)[」？]", title)
    if m:
        return m.group(1).strip()
    return re.sub(r"\s*(제정|개정|폐지|전부개정|일부개정)\s*(\(안\))?\s*(공고|예고)?\s*$", "", title).strip()


def walk_saved(tag, parse, pages_fn=None, total_fn=None):
    """앞서 받은 목록 쪽 원본(dart_out/raw/web10/knia/<tag>_pNNN.html)만으로 walk 와 같은 결과(요청 없음)."""
    allrows, pmeta, total, head = [], [], "", []
    for k, p in enumerate(sorted(glob.glob(os.path.join(DIR, "%s_p[0-9][0-9][0-9].html" % tag))), 1):
        m = json.load(open(p + ".meta.json", encoding="utf-8"))
        t = open(p, "rb").read().decode("utf-8", "replace")
        res = parse(t)
        rows, head = res[0], res[1]
        total = total or (total_fn or _total)(t)
        page = int(re.search(r"_p(\d+)\.html$", p).group(1))
        for j, r in enumerate(rows, 1):
            r.update(_page=page, _row=j, _raw=p, _sha=m["sha256"], _at=m["fetched_at"])
        allrows.extend(rows)
        pmeta.append(dict(page=page, rows=len(rows), path=p, sha256=m["sha256"], at=m["fetched_at"]))
    return allrows, pmeta, total, head, "" if pmeta else "저장된 목록 쪽 없음(%s)" % tag


def to_text(path):
    b = open(path, "rb").read(8)
    if b.startswith(b"%PDF"):
        tp, how, npg = pdf_to_txt(path)
        return tp, how, npg
    tp, how = hwp_to_md(path)
    return tp, how, 0


def write_cat_md(r, path, meta, tp, how, npg):
    os.makedirs(CAT_DIR, exist_ok=True)
    dst = os.path.join(CAT_DIR, "%02d_%s.md" % (int(r["번호"]) if r["번호"].isdigit() else 0, safe_name(r["규정명"], 100)))
    body, nmask = mask_email(open(tp, encoding="utf-8").read().rstrip("\n"))
    L = ["# %s — 손해보험협회 규정목록 원문" % r["규정명"], "",
         "- 출처 URL(다운로드): %s · 최종URL %s" % (meta["출처URL"], meta.get("최종URL", "")),
         "- 게시 화면: %s (%s) — 목록 %s쪽 %s행 · 목록 번호 %s · 개정년월 %s · 다운로드 버튼 title 「%s」"
         % (MENU01, REG01, r["_page"], r["_row"], r["번호"], r["개정년월"], "·".join(r["버튼제목"])),
         "- 원파일명(Content-Disposition): %s" % (meta.get("원파일명") or "없음"),
         "- 수집일 %s · HTTP %s · %s바이트 · sha256 %s · Content-Type %s"
         % (meta["fetched_at"], meta["http_status"], meta["바이트"], meta["sha256"], meta.get("content_type", "")),
         "- 원본: %s" % path,
         "- 텍스트화: %s → %s (sha256 %s)%s" % (how, tp, sha_file(tp), " · %d쪽" % npg if npg else " · hwp 라 쪽 번호 없음"),
         "- 파일 이름 앞 번호는 규정목록 화면의 「번호」 칸(사이트 표시 순번)이다 — 규정목록에는 따로 게시번호가 없다."]
    if nmask:
        L.append("- 이메일 주소 %d건은 「%s」로 바꿔 적었다(손보협회 「이메일무단수집거부」 고지). 그 밖의 글자는 그대로." % (nmask, MASK))
    L += ["", "---", "", body]
    open(dst, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return dst


def catalog():
    require_ok("www.knia.or.kr")
    from web9_klia import judge          # 9차 생보협회 목록과 같은 관련 판정(제목 낱말 일치)
    if "--offline" in sys.argv:                  # 받은 목록 원본만으로 다시 쓰기(요청 없음, 원문 파일은 받은 것 재사용)
        rows, pm, tot, head, stop = walk_saved("규정목록", parse_reg01)
        a6, pm6, tot6, head6, stop6 = walk_saved("변경공고목록", parse_reg06)
    else:
        rows, pm, tot, head, stop = walk(REG01, None, lambda n: {"keyword": "", "page": str(n)}, parse_reg01,
                                         "규정목록", MENU01)
        a6, pm6, tot6, head6, stop6 = walk(REG06, None, lambda n: {"keyword": "", "page": str(n)}, parse_reg06,
                                           "변경공고목록", MENU06)
    nums = sorted(int(r["번호"]) for r in rows if r["번호"].isdigit())
    gaps = [i for i in range(1, (nums[-1] if nums else 0) + 1) if i not in set(nums)]
    cnt = "사이트 표시 총 %s건 vs 수집 %d행 (쪽 %d, 목록 번호 %s~%s%s)%s" % (
        tot, len(rows), len(pm), nums[0] if nums else "-", nums[-1] if nums else "-",
        ", 빠진 번호 %s" % gaps if gaps else "·빠진 번호 없음", " — 중단: " + stop if stop else "")
    cnt6 = "자율규제 변경공고 사이트 표시 총 %s건 vs 수집 %d행 (쪽 %d)%s" % (tot6, len(a6), len(pm6),
                                                                 " — 중단: " + stop6 if stop6 else "")
    print(cnt)
    print(cnt6)
    by_name = {}
    for a in a6:
        by_name.setdefault(nows(ann_name(a["제목"])), []).append(a)
    names = {nows(r["규정명"]): r["규정명"] for r in rows}
    out = []
    for r in rows:
        rel, why = judge(r["규정명"])
        anns = by_name.get(nows(r["규정명"]), [])
        note = ["%d쪽 %d행 · 목록 번호 %s" % (r["_page"], r["_row"], r["번호"]),
                "분류: 사이트에 분류 없음(규정목록 열: %s) — 빈칸" % "·".join(head),
                "다운로드 버튼 title 「%s」" % "·".join(r["버튼제목"]) if r["버튼제목"] else "다운로드 버튼 없음(칸 글 %r)" % r["칸글"]]
        if len(r["다운로드"]) > 1:
            note.append("다운로드 링크 %d개: %s" % (len(r["다운로드"]), " , ".join(r["다운로드"])))
        note.append("자율규제 변경공고 게시글(제목의 규정명 부분 — 「」 안 또는 끝의 「제정/개정 공고」를 뗀 것 — 이 "
                    "규정명과 공백 빼고 같은 것): %s" % (
            " , ".join("%s「%s」 %s %s" % (a["번호"], a["제목"], a["등록일"], a["url"]) for a in anns) if anns else "없음"))
        note.append("관련 판정: %s" % (why if why else "해당 낱말 없음"))
        o = dict(name=r["규정명"], enacted_or_amended=r["개정년월"], category="", url=r["다운로드"][0] if r["다운로드"] else "",
                 related=rel, file_saved="", file_sha256="", collected_at=r["_at"])
        if rel and r["다운로드"] and not stop:
            u = r["다운로드"][0]
            try:
                c = cached(u)
                if c:
                    path, meta = c
                    note.append("원문: 앞서 받은 원본 재사용(%s, 받은 시각 %s)" % (path, meta["fetched_at"]))
                else:
                    path, meta, _b = fetch_file(u, "규정_%02d" % int(r["번호"]),
                                                dict(게시처=MENU01, 게시화면URL=REG01, 목록번호=r["번호"], 규정명=r["규정명"],
                                                     개정년월=r["개정년월"], 버튼제목="·".join(r["버튼제목"]),
                                                     목록원본=r["_raw"], 목록sha256=r["_sha"]), referer=REG01)
                tp, how, npg = to_text(path)
                md = write_cat_md(r, path, meta, tp, how, npg)
                o["file_saved"], o["file_sha256"] = path, meta["sha256"]
                o["collected_at"] = meta["fetched_at"]
                kind = "hwp" if open(path, "rb").read(8).startswith(OLE) else os.path.splitext(path)[1].lstrip(".")
                note.append("원문 %s(원파일명 %r, %s바이트, HTTP %s, 형식 %s%s) → %s" % (
                    os.path.basename(path), meta.get("원파일명", ""), meta["바이트"], meta["http_status"], kind,
                    "; 버튼 title 은 pdf 이나 받은 파일은 %s" % kind if "pdf" in "·".join(r["버튼제목"]).lower() and kind != "pdf" else "",
                    md))
            except Stop as e:
                stop = "원문 받기 중 %s" % e
                note.append("원문 미수집: " + stop)
            except Exception as e:                   # noqa: BLE001
                note.append("원문 받기/텍스트화 실패: %s: %s" % (type(e).__name__, e))
        elif rel and stop:
            note.append("원문 미수집: 앞서 중단(%s)" % stop)
        note.append("전수확인: " + cnt)
        o["note"] = " / ".join(note)
        out.append(o)
    if not rows:
        out.append(dict(name="", enacted_or_amended="", category="", url=REG01, related="", file_saved="", file_sha256="",
                        collected_at=now(), note="목록을 받지 못함 — %s (%s)" % (stop or "행 0개", MENU01)))
    write_csv(CAT_CSV, CAT_COLS, out)
    # 변경공고 게시판 목록(보조) — 규정목록에 같은 이름이 있는지 기계적으로만 표시
    arows = []
    for a in a6:
        nm = ann_name(a["제목"])
        hit = names.get(nows(nm), "")
        arows.append(dict(번호=a["번호"], 제목=a["제목"], 등록일=a["등록일"], 조회=a["조회"], 첨부=a["첨부"], url=a["url"],
                          규정목록_일치=hit or "규정목록에 같은 이름 없음",
                          collected_at=a["_at"],
                          note="%d쪽 %d행 · 대조 이름 「%s」(제목의 「」(또는 ？？) 안 글, 없으면 끝의 「제정/개정 (공고)」를 뗀 것 — "
                               "공백만 빼고 글자 그대로 비교, 가운뎃점·띄어쓰기 외 표기 차이는 다른 이름으로 봄) · %s"
                               % (a["_page"], a["_row"], nm, cnt6)))
    write_csv(ANN_CSV, ANN_COLS, arows)
    nrel = sum(1 for o in out if o["related"])
    nf = sum(1 for o in out if o["file_saved"])
    print("CSV %s — %d행 · 관련 %d · 원문 %d" % (CAT_CSV, len(out), nrel, nf))
    print("CSV %s — %d행 · 규정목록에 같은 이름 없는 공고 %d" % (ANN_CSV, len(arows),
                                                     sum(1 for x in arows if x["규정목록_일치"].startswith("규정목록에"))))
    return out


# ── 실행 ──────────────────────────────────────────────────────────────────
def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    order = ["terms", "rule", "compare", "posting", "catalog"]
    fns = {k: globals().get(k) for k in order + ["rulemd"]}
    if cmd == "all":
        for k in order:
            print("── %s" % k)
            fns[k]()
        return 0
    fn = fns.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    fn()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
