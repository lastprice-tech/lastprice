# -*- coding: utf-8 -*-
"""7차 — 법령 원문 아카이브 수집기.

`python3 scripts/law/collect.py resolve`   정식명 확정 47건(모호하면 표로 보여주고 끝)
`python3 scripts/law/collect.py pilot`     금융지주회사법 하나로 시범(요청서 5-1)
`python3 scripts/law/collect.py dryrun`    다운로드 없이 건수·용량 표(요청서 5-2)
`python3 scripts/law/collect.py run`       본 수집

규율(1~6차와 같다): 원문은 바이트 그대로 보존하고 sha256 을 남긴다. 추정·보간·삭제
금지 — 못 받은 것은 manifest 에 상태와 사유로 남긴다. OC 는 어디에도 원문으로
남기지 않는다(lawclient.mask).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lawclient     # noqa: E402
import render        # noqa: E402
import resolve       # noqa: E402
import targets as T  # noqa: E402

REPO = lawclient.REPO
ARCH = os.path.join(REPO, "law_archive")
MAN = os.path.join(ARCH, "00_manifest")
GROUP_DIR = {"A": "A_요청법령", "B-1": os.path.join("B_추가검토", "1_법률"),
             "B-2": os.path.join("B_추가검토", "2_행정규칙")}

MANIFEST_COLS = ["그룹", "상위법", "계층", "정식명", "법령ID", "법령일련번호", "공포일자",
                 "공포번호", "시행일자", "시행예정여부", "소관부처", "유형", "번호", "제목",
                 "파일경로", "원본형식", "페이지수", "sha256", "출처URL", "상태", "비고"]
LAWLIST_COLS = ["그룹", "순번", "요청명", "정식명", "계층", "법령ID", "법령일련번호",
                "공포일자", "공포번호", "시행일자", "시행예정여부", "소관부처", "법령구분",
                "일치방식", "상태", "비고"]
_BAD = re.compile(r'[\\/:*?"<>|\s]+')


def slug(s):
    return _BAD.sub("", s or "")


def title_slug(t, n=40):
    """「금융업의 본질적 업무(제26조제9항 관련)」 → 「금융업의본질적업무」.

    별표 제목에는 HTML 엔티티가 **글자 그대로** 들어 있다(실측: 「삭제 &lt;2016. 7. 28.&gt;」).
    그대로 두면 파일명에 `&lt;` 가 박힌다. 엔티티를 먼저 풀고 날짜 꺾쇠를 뗀다.
    """
    import html as _h
    t = _h.unescape(_h.unescape(t or ""))
    t = re.sub(r"[（(][^()（）]*관련[^()（）]*[)）]", "", t)
    t = re.sub(r"<[^>]*>|〈[^〉]*〉|&[a-z]+;", "", t)
    return slug(t)[:n] or "제목없음"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def sniff(b):
    """실제 시그니처로 형식을 판정한다. 확장자·Content-Type 을 믿지 않는다."""
    if b[:4] == b"%PDF":
        return "PDF"
    if b[:4] == b"\xd0\xcf\x11\xe0":
        return "HWP"            # HWP 5.0 (OLE 복합문서)
    if b[:4] == b"PK\x03\x04":
        return "HWPX"
    head = b[:200].lower()
    if b"<html" in head or b"<!doctype" in head:
        return "HTML(오류페이지)"
    return "기타(%s)" % b[:4].hex()


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return sha256(data)


def rel(p):
    return os.path.relpath(p, REPO)


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ── 정식명 확정 ───────────────────────────────────────────────────────────
def do_resolve(client):
    res = {"laws": {}, "rules": {}}
    amb = []
    for grp, seq, name in T.all_law_targets():
        out, status, cands = resolve.resolve_law(client, name)
        res["laws"][name] = {"그룹": grp, "순번": seq, "상태": status, "후보": cands, "계층": out}
        if status != "확정":
            amb.append((grp, seq, name, cands))
    for i, name in enumerate(T.B2_RULES + T.DEFERRED_RULES):
        row, status, how, cands = resolve.resolve_rule(client, name)
        grp = "B-2" if name in T.B2_RULES else "보류"
        res["rules"][name] = {"그룹": grp, "순번": i + 1, "상태": status, "일치": how,
                              "현행": row, "후보": cands}
        if status != "확정":
            amb.append((grp, i + 1, name, cands))
    os.makedirs(MAN, exist_ok=True)
    # 목록 응답의 링크에는 OC 가 되돌아온다 — 저장 전에 가린다.
    txt = client.mask(json.dumps(res, ensure_ascii=False, indent=1))
    with open(os.path.join(MAN, "resolve.json"), "w", encoding="utf-8") as f:
        f.write(txt)
    return res, amb


def load_resolve():
    p = os.path.join(MAN, "resolve.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


# ── 체계도 ────────────────────────────────────────────────────────────────
def parse_stmd(xml_bytes):
    """→ (nodes{key: node}, edges[(from,to,관계)], tree_lines[(깊이,종류,이름,시행일)])."""
    root = ET.fromstring(xml_bytes)
    nodes, edges, lines = {}, [], []

    def node_of(e):
        bi = e.find("기본정보")
        if bi is None:
            return None
        g = lambda k: (bi.findtext(k) or "").strip()
        if g("행정규칙ID") or g("행정규칙명"):
            key = "행정규칙:" + (g("행정규칙ID") or g("행정규칙명"))
            n = dict(key=key, 종류=g("법종구분") or e.tag, 이름=g("행정규칙명"),
                     ID=g("행정규칙ID"), 일련번호=g("행정규칙일련번호"), 시행일자=g("시행일자"),
                     분류="행정규칙")
        else:
            key = "법령:" + (g("법령ID") or g("법령명"))
            n = dict(key=key, 종류=g("법종구분"), 이름=g("법령명"), ID=g("법령ID"),
                     일련번호=g("법령일련번호"), 시행일자=g("시행일자"), 분류="법령")
        return n

    def walk(e, parent, depth, rel_kind):
        n = node_of(e)
        here = parent
        if n is not None and e.tag not in ("법령체계도",):
            nodes.setdefault(n["key"], n)
            if parent:
                edges.append((parent, n["key"], rel_kind))
            lines.append((depth, n["종류"], n["이름"], n["시행일자"]))
            here, depth = n["key"], depth + 1
        for c in e:
            if c.tag in ("기본정보", "본문상세링크"):
                continue
            walk(c, here, depth, "관련" if c.tag == "관련법령" else rel_kind)

    top = root.find("상하위법")
    if top is not None:
        walk(top, None, 0, "하위")
    rel = root.find("관련법령")
    if rel is not None:
        walk(rel, None, 0, "관련")
    # 같은 노드가 여러 가지에 되풀이된다(법률 밑·시행령 밑에 같은 고시). 간선은 dedupe.
    edges = sorted(set(edges))
    return nodes, edges, lines


def hierarchy_md(title, nodes, edges, lines):
    out = ["# %s — 법령 체계도" % title, "",
           "원천: 법제처 Open API `lawService.do?target=lsStmd` (OC 가림 사본에서 생성)", "",
           "노드 %d개 · 상하위 관계 %d개" % (len(nodes), len(edges)), ""]
    for d, kind, nm, ef in lines:
        out.append("%s- **[%s]** %s (시행 %s)" % ("  " * d, kind, nm, ef))
    return "\n".join(out) + "\n"


# ── 별표·서식 ─────────────────────────────────────────────────────────────
def annex_list(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for b in root.iter("별표단위"):
        g = lambda k: (b.findtext(k) or "").strip()
        num = g("별표번호").lstrip("0") or "0"
        gaji = g("별표가지번호").lstrip("0")
        kind = g("별표구분") or "별표"
        out.append(dict(구분=kind, 번호=num + ("의%s" % gaji if gaji else ""),
                        제목=g("별표제목"), pdf=g("별표서식PDF파일링크"),
                        hwp=g("별표서식파일링크")))
    return out


def fetch_annex(client, a, dest_noext, meta, dry=False):
    """PDF 링크 우선, 없거나 실패하면 HWP. 원본 그대로 저장한다(변환하지 않는다)."""
    row = dict(meta, 유형="별표" if a["구분"] == "별표" else "서식",
               번호=a["번호"], 제목=a["제목"])
    deleted = a["제목"].strip().startswith("삭제")
    tried = []
    for link, want in ((a["pdf"], "PDF"), (a["hwp"], "HWP")):
        if not link:
            continue
        if dry:
            return dict(row, 원본형식=want, 상태="예정", 출처URL="http://www.law.go.kr" + link)
        st, body, ct, murl, host = client.file(link)
        fmt = sniff(body) if body else ""
        tried.append("%s→%s" % (want, fmt or "실패"))
        if st == 200 and fmt in ("PDF", "HWP", "HWPX"):
            ext = {"PDF": ".pdf", "HWP": ".hwp", "HWPX": ".hwpx"}[fmt]
            path = dest_noext + ext
            h = write(path, body)
            pages = ""
            if fmt == "PDF":
                ok, n, _ = render.pdf_info(path)
                pages = n
            return dict(row, 파일경로=rel(path), 원본형식=fmt, 페이지수=pages, sha256=h,
                        출처URL=murl, 상태="삭제별표" if deleted else "OK",
                        비고="PDF 링크 없음·실패로 HWP 원본" if want == "HWP" else "")
    return dict(row, 상태="실패", 비고="; ".join(tried) or "링크 없음")


# ── 한 법령(3단) ──────────────────────────────────────────────────────────
def collect_law(client, grp, seq, req, info, pilot=False, dry=False):
    tiers = info["계층"]
    law_row = tiers["법률"]["현행"]
    top = law_row["법령명한글"]
    base = os.path.join(ARCH, GROUP_DIR[grp], T.folder_name(seq, top))
    mrows, lrows, hier = [], [], {"nodes": {}, "edges": []}

    # 체계도
    mst = law_row["법령일련번호"]
    st, body, murl, host = client.api("lawService.do", target="lsStmd", MST=mst, type="XML")
    n_oc = client.count_oc(body)
    masked = client.mask(body)
    nodes, edges, lines = parse_stmd(masked)
    hier["nodes"], hier["edges"] = nodes, edges
    d0 = os.path.join(base, "0_체계도")
    common = dict(그룹=grp, 상위법=top, 정식명=top, 법령ID=law_row["법령ID"], 법령일련번호=mst,
                  시행일자=law_row["시행일자"], 소관부처=law_row.get("소관부처명", ""))
    if not dry:
        h = write(os.path.join(d0, "체계도_원문(OC가림).xml"), masked)
        # 가림 검증: 바뀐 곳이 OC 문자열뿐인가(길이 차 = 등장 수 × (len(OC)−3)).
        diff_ok = len(body) - len(masked) == n_oc * (len(client.oc) - 3)
        mrows.append(dict(common, 계층="체계도", 유형="체계도원문XML",
                          파일경로=rel(os.path.join(d0, "체계도_원문(OC가림).xml")),
                          원본형식="XML", sha256=h, 출처URL=murl, 상태="OK",
                          비고="OC %d곳 가림 · 원 응답 sha256 %s · 길이차 검증 %s"
                          % (n_oc, sha256(body), "일치" if diff_ok else "불일치")))
        js = {"법령": top, "원천": "lsStmd", "노드": list(nodes.values()),
              "간선": [{"from": a, "to": b, "관계": r} for a, b, r in edges]}
        jp = os.path.join(d0, "체계도.json")
        write(jp, json.dumps(js, ensure_ascii=False, indent=1).encode("utf-8"))
        mdp = os.path.join(d0, "체계도.md")
        write(mdp, hierarchy_md(top, nodes, edges, lines).encode("utf-8"))
        pp = os.path.join(d0, "체계도.pdf")
        render.html_to_pdf(render.hierarchy_html(lines, top, law_row["시행일자"], mst), pp)
        ok, npg, _ = render.pdf_info(pp)
        for p_, fmt in ((jp, "JSON"), (mdp, "MD"), (pp, "PDF")):
            mrows.append(dict(common, 계층="체계도", 유형="체계도", 파일경로=rel(p_),
                              원본형식=fmt, 페이지수=npg if fmt == "PDF" else "",
                              sha256=sha256(open(p_, "rb").read()), 상태="OK",
                              비고="렌더링(XML→PDF)" if fmt == "PDF" else ""))

    # 체계도에 있는 시행규칙 노드 — 이름 규칙과 교차 확인한다.
    stmd_kinds = {n["종류"] for n in nodes.values() if n["분류"] == "법령"}
    stmd_rules = [n for n in nodes.values() if n["분류"] == "법령"
                  and n["종류"] not in ("법률", "대통령령")]

    for tier in T.TIERS:
        t = tiers[tier]
        versions = []
        if t["현행"]:
            versions.append((t["현행"], False))
        for p in t["시행예정"]:
            versions.append((p, True))
        if not versions:
            note = ""
            if tier == "시행규칙":
                note = ("체계도에도 시행규칙 노드 없음(교차 확인)" if not stmd_rules else
                        "체계도에는 시행규칙급 노드가 있다: " +
                        ", ".join("%s(%s)" % (n["이름"], n["종류"]) for n in stmd_rules))
            lrows.append(dict(그룹=grp, 순번=seq, 요청명=req, 정식명=req + T.TIER_SUFFIX[tier],
                              계층=tier, 상태="없음", 비고=note))
            continue
        for row, pending in versions:
            name = row["법령명한글"]
            ef, ms = row["시행일자"], row["법령일련번호"]
            lrows.append(dict(그룹=grp, 순번=seq, 요청명=req, 정식명=name, 계층=tier,
                              법령ID=row["법령ID"], 법령일련번호=ms, 공포일자=row["공포일자"],
                              공포번호=row["공포번호"], 시행일자=ef,
                              시행예정여부="Y" if pending else "N",
                              소관부처=row.get("소관부처명", ""), 법령구분=row.get("법령구분명", ""),
                              일치방식=t["일치"], 상태="확정"))
            tdir = os.path.join(base, T.TIER_DIR[tier])
            stem = "%s_%s_%s%s" % (slug(top), tier, ef, "_시행예정" if pending else "")
            meta = dict(그룹=grp, 상위법=top, 계층=tier, 정식명=name, 법령ID=row["법령ID"],
                        법령일련번호=ms, 공포일자=row["공포일자"], 공포번호=row["공포번호"],
                        시행일자=ef, 시행예정여부="Y" if pending else "N",
                        소관부처=row.get("소관부처명", ""))
            st, xb, murl, host = client.api("lawService.do", target="eflaw", MST=ms, efYd=ef,
                                            type="XML")
            if not xb:
                mrows.append(dict(meta, 유형="원문XML", 상태="실패", 출처URL=murl))
                continue
            annexes = annex_list(xb)
            if dry:
                mrows.append(dict(meta, 유형="원문XML", 상태="예정", 출처URL=murl,
                                  비고="%d바이트" % len(xb)))
                for a in annexes:
                    mrows.append(fetch_annex(client, a, "", meta, dry=True))
                continue
            noc = client.count_oc(xb)
            xpath = os.path.join(tdir, stem + "_원문.xml")
            xdata = client.mask(xb) if noc else xb
            h = write(xpath, xdata)
            mrows.append(dict(meta, 유형="원문XML", 파일경로=rel(xpath), 원본형식="XML", sha256=h,
                              출처URL=murl, 상태="OK",
                              비고=("OC %d곳 가림 · 원 응답 sha256 %s" % (noc, sha256(xb)))
                              if noc else "바이트 그대로(OC 0회)"))
            # (가) XML 직접 렌더링 — 기본
            html_text, _nm, labels = render.law_html(xb, ef, ms, pending)
            pdfp = os.path.join(tdir, stem + "_본문.pdf")
            render.html_to_pdf(html_text, pdfp)
            ok, npg, txt = render.pdf_info(pdfp)
            flat = txt.replace(" ", "")
            miss = [l for l in labels if l not in flat]
            mrows.append(dict(meta, 유형="본문", 파일경로=rel(pdfp), 원본형식="PDF",
                              페이지수=npg, sha256=sha256(open(pdfp, "rb").read()),
                              출처URL=murl, 상태="OK" if not miss else "조문누락",
                              비고="렌더링(원문XML→PDF) · 조문표지 %d개 중 누락 %d%s"
                              % (len(labels), len(miss), (" " + ",".join(miss[:5])) if miss else "")))
            if pilot:
                mrows.append(try_viewer(client, ms, ef, pdfp.replace("_본문.pdf", "_보조뷰어.pdf"),
                                        labels, meta))
            for a in annexes:
                sub = "별표" if a["구분"] == "별표" else "서식"
                dest = os.path.join(tdir, sub, "%s_%s%s_%s" % (stem, sub, a["번호"],
                                                               title_slug(a["제목"])))
                mrows.append(fetch_annex(client, a, dest, meta))
    return mrows, lrows, hier, stmd_rules


def try_viewer(client, ms, ef, out_pdf, labels, meta):
    """(나) DRF 뷰어 렌더링 — 시범에서 한 번만. 잘리면 버리고 사실만 적는다."""
    url = "http://www.law.go.kr/DRF/lawService.do?OC=%s&target=eflaw&MST=%s&efYd=%s&type=HTML" % (
        client.oc, ms, ef)
    cmd = [render.chrome(), "--headless", "--no-sandbox", "--disable-gpu",
           "--no-pdf-header-footer", "--virtual-time-budget=30000",
           "--print-to-pdf=%s" % out_pdf, url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=180)
    except Exception as e:                      # noqa: BLE001
        return dict(meta, 유형="보조뷰어", 상태="실패", 비고=client.mask(str(e))[:200])
    if not os.path.exists(out_pdf):
        return dict(meta, 유형="보조뷰어", 상태="실패", 비고="PDF 가 만들어지지 않음")
    ok, npg, txt = render.pdf_info(out_pdf)
    flat = txt.replace(" ", "")
    got = sum(1 for l in labels if l in flat)
    good = npg > 1 and got == len(labels)
    row = dict(meta, 유형="보조뷰어", 파일경로=rel(out_pdf), 원본형식="PDF", 페이지수=npg,
               sha256=sha256(open(out_pdf, "rb").read()), 출처URL=client.mask(url),
               상태="OK" if good else "폐기",
               비고="DRF 뷰어 인쇄 · 쪽수 %d · 조문표지 %d/%d" % (npg, got, len(labels)))
    if not good:
        os.remove(out_pdf)
        row["파일경로"] = ""
        row["sha256"] = ""
        row["비고"] += " — 잘림/누락이라 폐기"
    return row


# ── 다시 찍기 ─────────────────────────────────────────────────────────────
def rerender():
    """저장된 원문 XML 에서 본문·체계도 PDF 만 다시 찍는다. **API 호출 0.**

    폰트·용지를 바꿀 때 쓴다(사용자가 HY견고딕·HY신명조를 올려 주는 경우 등).
    원문 XML 은 건드리지 않고, manifest 의 해당 행 sha256·쪽수·비고만 갱신한다.
    """
    mp = os.path.join(MAN, "manifest.csv")
    rows = list(csv.DictReader(open(mp, encoding="utf-8-sig")))
    by_xml = {}
    for r in rows:
        if r["유형"] == "원문XML" and r["파일경로"]:
            by_xml[r["파일경로"].replace("_원문.xml", "")] = r
    n = 0
    for r in rows:
        if r["유형"] == "본문" and r["파일경로"]:
            stem = r["파일경로"].replace("_본문.pdf", "")
            x = by_xml.get(stem)
            if not x:
                continue
            xb = open(os.path.join(REPO, x["파일경로"]), "rb").read()
            pending = r["시행예정여부"] == "Y"
            if r["계층"] == "행정규칙":
                h, _nm, labels = render.admrul_html(xb, r["시행일자"], r["법령일련번호"], pending)
            else:
                h, _nm, labels = render.law_html(xb, r["시행일자"], r["법령일련번호"], pending)
            pdfp = os.path.join(REPO, r["파일경로"])
            render.html_to_pdf(h, pdfp)
            ok, npg, txt = render.pdf_info(pdfp)
            flat = txt.replace(" ", "")
            miss = [l for l in labels if l not in flat]
            r.update(페이지수=npg, sha256=sha256(open(pdfp, "rb").read()),
                     상태="OK" if not miss else "조문누락",
                     비고="렌더링(원문XML→PDF) · 조문표지 %d개 중 누락 %d%s"
                     % (len(labels), len(miss), (" " + ",".join(miss[:5])) if miss else ""))
            n += 1
        elif r["유형"] == "체계도" and r["원본형식"] == "PDF":
            d0 = os.path.dirname(os.path.join(REPO, r["파일경로"]))
            xb = open(os.path.join(d0, "체계도_원문(OC가림).xml"), "rb").read()
            _nodes, _edges, lines = parse_stmd(xb)
            render.html_to_pdf(render.hierarchy_html(lines, r["상위법"], r["시행일자"],
                                                     r["법령일련번호"]),
                               os.path.join(REPO, r["파일경로"]))
            ok, npg, _ = render.pdf_info(os.path.join(REPO, r["파일경로"]))
            r.update(페이지수=npg, sha256=sha256(open(os.path.join(REPO, r["파일경로"]), "rb").read()))
            n += 1
    write_csv(mp, rows, MANIFEST_COLS)
    print("다시 찍음 %d건 (API 호출 0)" % n)


# ── 진입점 ────────────────────────────────────────────────────────────────
def main(argv):
    cmd = argv[1] if len(argv) > 1 else "pilot"
    if cmd == "rerender":
        rerender()
        return 0
    client = lawclient.LawClient(os.path.join(MAN, "call_log.csv"))
    try:
        if cmd == "resolve":
            res, amb = do_resolve(client)
            print_resolve(res, amb)
            return 0 if not amb else 2
        if cmd == "pilot":
            res = load_resolve() or do_resolve(client)[0]
            info = res["laws"]["금융지주회사법"]
            mrows, lrows, hier, stmd_rules = collect_law(client, "A", 15, "금융지주회사법",
                                                         info, pilot=True)
            write_csv(os.path.join(MAN, "manifest.csv"), mrows, MANIFEST_COLS)
            write_csv(os.path.join(MAN, "law_list.csv"), lrows, LAWLIST_COLS)
            hj = {"생성": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "원천": "lsStmd",
                  "법령": {"금융지주회사법": {"노드": list(hier["nodes"].values()),
                                          "간선": [{"from": a, "to": b, "관계": r}
                                                   for a, b, r in hier["edges"]]}}}
            with open(os.path.join(MAN, "hierarchy.json"), "w", encoding="utf-8") as f:
                f.write(client.mask(json.dumps(hj, ensure_ascii=False, indent=1)))
            print("시범 완료 — manifest %d행 · law_list %d행 · 호출 %d건"
                  % (len(mrows), len(lrows), client.n_calls))
            return 0
    except lawclient.AuthError as e:
        print("■ 인증 오류 — 멈춥니다. 오류 원문:\n%s" % e)
        return 3
    print("알 수 없는 명령:", cmd)
    return 1


def print_resolve(res, amb):
    print("■ 법령 29건")
    for name, v in res["laws"].items():
        t = v["계층"]
        def cell(k):
            c = t[k]["현행"]
            s = ("%s(%s)" % (c["시행일자"], t[k]["일치"][:2])) if c else "없음"
            if t[k]["시행예정"]:
                s += " +예정%d" % len(t[k]["시행예정"])
            return s
        print("  %-4s %2d %-34s %-6s 법률 %-16s 시행령 %-16s 시행규칙 %s"
              % (v["그룹"], v["순번"], name[:34], v["상태"], cell("법률"), cell("시행령"),
                 cell("시행규칙")))
    print("\n■ 행정규칙 %d건 (+보류)" % len(res["rules"]))
    for name, v in res["rules"].items():
        r = v["현행"] or {}
        print("  %-4s %2d %-36s %-4s %-10s %s %s" % (
            v["그룹"], v["순번"], name[:36], v["상태"], v["일치"],
            ("정식명=%s · %s · %s · 시행 %s" % (r.get("행정규칙명", ""), r.get("행정규칙종류", ""),
                                               r.get("소관부처명", ""), r.get("시행일자", "")))
            if r else "", ""))
    if amb:
        print("\n■ 모호 %d건 — 후보를 보고 정해 주세요" % len(amb))
        for grp, seq, name, cands in amb:
            print("  [%s %d] %s" % (grp, seq, name))
            for c in cands:
                print("       - %s" % c)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
