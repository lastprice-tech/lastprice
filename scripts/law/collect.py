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
    t = re.sub(r"\[[^\]]*관련[^\]]*\]", "", t)
    t = re.sub(r"<[^>]*>|〈[^〉]*〉|&[a-z]+;", "", t)
    t = slug(t)[:n]
    if t.count("(") > t.count(")"):               # 자르다 연 괄호가 남으면 그 앞까지
        t = t[:t.rfind("(")]
    return t.rstrip(",.·ㆍ_-") or "제목없음"


NAME_MAX = 240          # ext4 한 이름 255바이트. .tmp.pdf 등 붙는 것을 빼고 넉넉히 둔다.


def fit_dest(prefix_path, title, tail="_XML렌더링.pdf"):
    """별표 저장 경로(확장자 없음). 파일 이름이 NAME_MAX 바이트를 넘으면 제목을 줄인다.

    실측: 「공중등협박…법률」 줄기는 118바이트 — 시행예정·일련번호·별표번호·제목 40자까지
    붙으면 305바이트가 되어 저장이 실패한다(OSError 36). 제목만 줄이고 번호는 지킨다.
    """
    d, base = os.path.split(prefix_path)
    t = title
    while t and len((base + "_" + t + tail).encode("utf-8")) > NAME_MAX:
        t = t[:-1]
    t = t.rstrip(",.·ㆍ_-(")
    if not t:
        return os.path.join(d, base)
    return os.path.join(d, base + "_" + t)


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
    """임시 파일에 쓰고 바꿔 넣는다 — 쓰다 멈춰도 기존 manifest 가 반쯤 잘리지 않는다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, path)


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
    """XML 순서 그대로의 별표·서식. unit 은 원본 파일이 없을 때 따로 찍으려고 들고 다닌다."""
    root = ET.fromstring(xml_bytes)
    rule = render.is_rule_root(root)
    out = []
    for b in render.annex_units(root):
        g = lambda k: (b.findtext(k) or "").strip()
        kind = g("별표구분") or "별표"
        out.append(dict(구분=kind, 번호=render.annex_no(b, rule),
                        제목=g("별표제목"), 시행일자=g("별표시행일자"),
                        pdf=g("별표서식PDF파일링크"), hwp=g("별표서식파일링크"), unit=b))
    return out


def annex_sub(a):
    """저장 하위 폴더·manifest 유형. 별표만 「별표」, 서식·별지 등은 「서식」."""
    return "별표" if a["구분"] == "별표" else "서식"


def annex_files(annex_rows):
    """manifest 별표·서식 행(XML 순서) → 본문 PDF 목록 표의 [(저장 파일명, 상태)]."""
    out = []
    for r in annex_rows:
        fn = os.path.basename(r.get("파일경로") or "")
        st = r.get("상태") or ""
        if not fn:
            st = "%s: %s" % (st, r.get("비고") or "") if r.get("비고") else st
        out.append((fn, st))
    return out


def fetch_annex(client, a, dest_noext, meta, dry=False, ctx=None):
    """PDF 링크 우선, 없거나 실패하면 HWP. 원본 그대로 저장한다(변환하지 않는다).

    PDF·HWP 링크가 **둘 다 없을 때만** 원문 XML 별표내용을 따로 찍는다(ctx =
    (법령명, 시행일, 일련번호, 시행예정, 행정규칙여부)). 링크가 있는데 받지 못한 것은
    대신 찍지 않고 「실패」로 남긴다 — 다시 받아야 할 것을 렌더링으로 덮지 않는다.
    """
    row = dict(meta, 유형=annex_sub(a), 번호=a["번호"], 제목=a["제목"])
    deleted = a["제목"].strip().startswith("삭제")
    tried = []
    if not a["pdf"] and not a["hwp"]:
        if dry:
            return dict(row, 원본형식="PDF", 상태="예정",
                        비고="원본 PDF·HWP 링크 없음 → 원문 XML 별표내용 렌더링 예정")
        return render_annex(a, dest_noext, row, ctx, deleted)
    for link, want in ((a["pdf"], "PDF"), (a["hwp"], "HWP")):
        if not link:
            continue
        if dry:
            return dict(row, 원본형식=want, 상태="예정", 출처URL="http://www.law.go.kr" + link,
                        비고="" if want == "PDF" else "PDF 링크 없음 → HWP 원본 예정")
        st, body, ct, murl, host = client.file(link)
        fmt = sniff(body) if body else ""
        tried.append("%s→%s" % (want, fmt or "실패"))
        if st == 200 and fmt in ("PDF", "HWP", "HWPX"):
            ext = {"PDF": ".pdf", "HWP": ".hwp", "HWPX": ".hwpx"}[fmt]
            path = dest_noext + ext
            try:
                h = write(path, body)
            except OSError as e:
                return dict(row, 상태="실패", 출처URL=murl,
                            비고="저장 실패(%s): %s" % (type(e).__name__, os.path.basename(path)))
            pages = ""
            if fmt == "PDF":
                ok, n, _ = render.pdf_info(path)
                pages = n
            # PDF 링크가 있었는데 못 받아 HWP 로 대신한 것은 「OK」와 가른다 — PDF 를
            # 다시 받아야 할 대상이다. PDF 링크가 원래 없던 것은 OK(HWP 가 원본의 전부).
            pdf_failed = want == "HWP" and bool(a["pdf"])
            state = ("HWP대체(PDF실패)" if pdf_failed else "삭제별표" if deleted else "OK")
            note = ""
            if want == "HWP":
                got = "HWP 링크에서 %s 원본" % fmt       # HWP 링크가 PDF 를 줄 때도 있다
                note = ("PDF 링크가 있었으나 실패(%s) → %s" % ("; ".join(tried[:-1]), got)
                        if pdf_failed else "PDF 링크 없음 → %s" % got)
                if deleted and pdf_failed:
                    note += " · 삭제별표"
            elif fmt != "PDF":
                note = "PDF 링크에서 %s 를 받음(원본 그대로 저장)" % fmt
            return dict(row, 파일경로=rel(path), 원본형식=fmt, 페이지수=pages, sha256=h,
                        출처URL=murl, 상태=state, 비고=note)
    return dict(row, 상태="실패", 비고="; ".join(tried) or "링크 없음")


RENDERED_ANNEX = "원본없음·XML렌더링"


def render_annex(a, dest_noext, row, ctx, deleted=False):
    """원본 파일이 없는 별표 하나를 따로 찍는다. 별표내용도 비었으면 실패로 남긴다.

    상태는 rerender 가 찾을 수 있게 RENDERED_ANNEX 로 두고, 삭제 별표면 비고에 적는다."""
    unit = a.get("unit")
    if unit is None or ctx is None or not (unit.findtext("별표내용") or "").strip():
        return dict(row, 상태="실패", 비고="원본 PDF·HWP 링크 없음, 원문 XML 별표내용도 비어 있음"
                    + (" · 삭제별표" if deleted else ""))
    name, ef, serial, pending, is_rule = ctx
    path = dest_noext + "_XML렌더링.pdf"
    render.html_to_pdf(render.annex_text_html(unit, name, ef, serial, pending,
                                              "행정규칙" if is_rule else ""), path)
    ok, npg, _ = render.pdf_info(path)
    return dict(row, 파일경로=rel(path), 원본형식="PDF", 페이지수=npg,
                sha256=sha256(open(path, "rb").read()), 상태=RENDERED_ANNEX,
                비고="원본 PDF·HWP 링크 없음 → 원문 XML 별표내용 렌더링(글자 그대로)"
                + (" · 삭제별표" if deleted else ""))


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
        seen_v, uniq = set(), []                   # 같은 (MST, 시행일, 시행예정)이 두 번 오면 하나만
        for row, pending in versions:
            k = (row["법령일련번호"], row["시행일자"], pending)
            if k not in seen_v:
                seen_v.add(k)
                uniq.append((row, pending))
        versions = uniq
        # 같은 시행일에 시행예정판이 여럿일 수 있다(실측: 조세특례제한법 법률 20270101 5건,
        # 법인세법 시행령 20270101 3건 — 공포가 다른 개정이 같은 날 시행). 파일명이 「법령_
        # 계층_시행일_시행예정」뿐이면 서로 덮어쓰므로, 겹치는 판에만 법령일련번호를 붙인다.
        same_day = {}
        for row, pending in versions:
            k = (row["시행일자"], pending)
            same_day[k] = same_day.get(k, 0) + 1
        if not versions:
            note = ""
            if tier == "시행규칙":
                note = rule_absence_note(req, stmd_rules)
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
            if same_day[(ef, pending)] > 1:
                stem += "_일련번호%s" % ms
            claim_stem(os.path.join(tdir, stem), (ms, ef, pending))
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
            # 별표·서식을 먼저 받는다 — 본문 PDF 의 별표 목록에 저장 파일명을 적기 위해서.
            arows, used = [], set()
            for a in annexes:
                sub = annex_sub(a)
                label = slug(a["구분"]) or sub    # 별표·서식·별지 — 원문 구분 이름 그대로
                dest = fit_dest(os.path.join(tdir, sub, "%s_%s%s" % (stem, label, a["번호"])),
                                title_slug(a["제목"]))
                dup = ""
                if dest in used:       # 같은 판 안에서 (구분·번호·제목)이 겹치면 덮지 않는다
                    k = 2
                    while "%s_중복%d" % (dest, k) in used:
                        k += 1
                    dest, dup = "%s_중복%d" % (dest, k), "같은 판에 구분·번호·제목이 같은 별표가 또 있어 _중복%d 을 붙임" % k
                used.add(dest)
                ar = fetch_annex(client, a, dest, meta, ctx=(name, ef, ms, pending, False))
                if dup:
                    ar["비고"] = (ar.get("비고", "") + " · " + dup).strip(" ·")
                arows.append(ar)
            # (가) XML 직접 렌더링 — 기본. 별표·서식은 목록만 싣는다.
            html_text, _nm, labels = render.law_html(xb, ef, ms, pending, annex_files(arows))
            pdfp = os.path.join(tdir, stem + "_본문.pdf")
            render.html_to_pdf(html_text, pdfp)
            mrows.append(body_row(meta, pdfp, labels, len(arows), 출처URL=murl))
            if pilot:
                mrows.append(try_viewer(client, ms, ef, pdfp.replace("_본문.pdf", "_보조뷰어.pdf"),
                                        labels, meta))
            mrows.extend(arows)
    return mrows, lrows, hier, stmd_rules


_STEMS = {}


def claim_stem(stem_path, key):
    """한 실행에서 파일명 줄기 하나는 한 판(MST·시행일·시행예정)만 쓴다. 다른 판이 같은
    줄기를 쓰려 하면 덮어쓰기 전에 멈춘다(원문 보존 — 조용히 덮는 것이 가장 나쁘다)."""
    prev = _STEMS.setdefault(stem_path, key)
    if prev != key:
        raise RuntimeError("파일명 충돌: %s — %s 와 %s" % (rel(stem_path), prev, key))


def rule_absence_note(law, stmd_rules):
    """시행규칙 「없음」의 체계도 교차 확인. 이름으로 본다 — 체계도의 총리령·대법원규칙 가운데
    「○○ 직제 시행규칙」처럼 **다른 규칙**을 이 법의 시행규칙으로 오인하지 않는다."""
    want = re.sub(r"\s+", "", law + " 시행규칙")
    same = [n for n in stmd_rules if re.sub(r"\s+", "", n["이름"]) == want]
    if same:
        return ("체계도에는 「%s 시행규칙」이 있다(목록 검색과 불일치 — 확인 필요): %s"
                % (law, ", ".join("%s(%s)" % (n["이름"], n["종류"]) for n in same)))
    note = "체계도에도 「%s 시행규칙」 없음(교차 확인)" % law
    if stmd_rules:
        note += " · 체계도의 다른 시행규칙급 노드(이 법의 시행규칙 아님): " + ", ".join(
            "%s(%s)" % (n["이름"], n["종류"]) for n in stmd_rules)
    return note


def body_row(meta, pdfp, labels, n_annex, **extra):
    """본문 PDF 의 manifest 행 — 조문표지 누락 검사와 별표 목록 건수를 적는다."""
    ok, npg, txt = render.pdf_info(pdfp)
    miss, weak = render.label_check(labels, txt)
    note = "렌더링(원문XML→PDF) · 조문표지 %d개 중 누락 %d%s" % (
        len(labels), len(miss), (" " + ",".join(miss[:5])) if miss else "")
    if weak:
        note += " · 조 머리 꼴 없이 글자만 있는 표지 %d(%s)" % (len(weak), ",".join(weak[:5]))
    if n_annex:
        note += " · 별표·서식 %d건은 목록만(내용은 따로 저장)" % n_annex
    if not labels:
        # 조문 표지를 하나도 못 찾으면 누락 검사가 빈 검사다 — OK 로 적지 않는다.
        state, note = "검증불가", note + " · 원문 XML 에서 조문 표지를 찾지 못해 누락 검사를 못 함"
    else:
        state = "조문누락" if miss else "확인필요" if weak else "OK"
    return dict(meta, 유형="본문", 파일경로=rel(pdfp), 원본형식="PDF", 페이지수=npg,
                sha256=sha256(open(pdfp, "rb").read()), 상태=state, 비고=note, **extra)


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
        client._log("viewer", url, 0, 0, 1, "chromium", "%s: %s" % (type(e).__name__, str(e)[-120:]))
        return dict(meta, 유형="보조뷰어", 상태="실패", 비고=client.mask(str(e))[:200])
    # Chromium 이 직접 부르므로 LawClient 원장을 거치지 않는다 — 원장에 따로 한 줄 남긴다.
    client._log("viewer", url, "", os.path.getsize(out_pdf) if os.path.exists(out_pdf) else 0,
                1, "chromium", "" if os.path.exists(out_pdf) else "PDF 가 만들어지지 않음")
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
def _swap_render(html_text, path):
    """임시 파일에 찍고 확인한 뒤 제자리로 바꾼다 — 찍다 실패해도 기존 PDF 는 그대로다."""
    tmp = path + ".tmp.pdf"
    try:
        render.html_to_pdf(html_text, tmp)       # html_to_pdf 가 남은 tmp 를 먼저 지운다
        ok, npg, _ = render.pdf_info(tmp)
        if not ok or npg < 1:
            raise RuntimeError("렌더링 결과가 PDF 가 아니거나 0쪽: %s" % rel(path))
        h = sha256(open(tmp, "rb").read())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return npg, h


def rerender():
    """저장된 원문 XML 에서 **우리가 찍은** PDF 만 다시 찍는다. **API 호출 0.**

    대상: 본문 PDF(별표·서식 목록 포함), 체계도 PDF, 원본 없는 별표의 XML 렌더링 PDF.
    폰트·용지를 바꿀 때 쓴다. 법제처가 준 별표·서식 원본 PDF·HWP 와 원문 XML 은 건드리지
    않고, manifest 의 해당 행 sha256·쪽수·상태·비고만 갱신한다.

    1) **먼저 전부 검사하고** 하나라도 어긋나면 아무것도 찍지 않고 멈춘다 — 찍다가 멈추면
       이미 바뀐 PDF 와 manifest sha256 이 어긋난다(Chromium PDF 는 찍을 때마다 sha256 이
       바뀐다). 2) 찍는 중에 예외가 나도 그때까지 찍은 행은 manifest 에 써 둔다.
    """
    mp = os.path.join(MAN, "manifest.csv")
    rows = list(csv.DictReader(open(mp, encoding="utf-8-sig")))
    vkey = lambda r: (r["그룹"], r["상위법"], r["계층"], r["정식명"], r["법령일련번호"],
                      r["시행일자"], r["시행예정여부"])
    by_xml, annexes, path_key = {}, {}, {}
    for r in rows:
        if r["유형"] == "원문XML" and r["파일경로"]:
            by_xml[vkey(r)] = r
            path_key.setdefault(r["파일경로"], set()).add(vkey(r))
        elif r["유형"] in ("별표", "서식"):
            annexes.setdefault(vkey(r), []).append(r)          # manifest 순서 = XML 순서

    # ── 1) 검사 ──
    problems, plan = [], []
    for p_, ks in path_key.items():
        if len(ks) > 1:
            problems.append("원문 XML 하나를 여러 판이 가리킴: %s (%d판)" % (p_, len(ks)))
    for r in rows:
        if r["유형"] == "본문" and r["파일경로"]:
            x = by_xml.get(vkey(r))
            if not x:
                problems.append("원문 XML 행 없음: %s" % r["파일경로"])
                continue
            xp = os.path.join(REPO, x["파일경로"])
            if not os.path.exists(xp):
                problems.append("원문 XML 파일 없음: %s" % x["파일경로"])
                continue
            xb = open(xp, "rb").read()
            if x["sha256"] and sha256(xb) != x["sha256"]:
                problems.append("원문 XML sha256 불일치: %s" % x["파일경로"])
                continue
            arows = annexes.get(vkey(r), [])
            units = annex_list(xb)
            if len(units) != len(arows):
                problems.append("별표 수 불일치 %s: XML %d · manifest %d"
                                % (r["파일경로"], len(units), len(arows)))
                continue
            bad = [(a, ar) for a, ar in zip(units, arows)
                   if a["번호"] != ar["번호"] or ar["유형"] != annex_sub(a)]
            if bad:
                a, ar = bad[0]
                problems.append("별표 순서 불일치 %s: XML %s%s · manifest %s%s"
                                % (r["파일경로"], a["구분"], a["번호"], ar["유형"], ar["번호"]))
                continue
            plan.append(("본문", r, xb, units, arows))
        elif r["유형"] == "체계도" and r["원본형식"] == "PDF":
            xp = os.path.join(os.path.dirname(os.path.join(REPO, r["파일경로"])),
                              "체계도_원문(OC가림).xml")
            if not os.path.exists(xp):
                problems.append("체계도 XML 없음: %s" % rel(xp))
                continue
            xb = open(xp, "rb").read()
            src = [s_ for s_ in rows if s_["유형"] == "체계도원문XML" and s_["파일경로"] == rel(xp)]
            if src and src[0]["sha256"] and sha256(xb) != src[0]["sha256"]:
                problems.append("체계도 XML sha256 불일치: %s" % rel(xp))
                continue
            try:
                parse_stmd(xb)
            except Exception as e:                  # noqa: BLE001
                problems.append("체계도 XML 해석 실패 %s: %s" % (rel(xp), e))
                continue
            plan.append(("체계도", r, xb, None, None))
    if problems:
        print("■ 다시 찍기 전 검사에서 %d건 어긋남 — 아무것도 찍지 않았습니다" % len(problems))
        for p_ in problems[:20]:
            print("  -", p_)
        raise SystemExit(2)

    # ── 2) 찍기 ──
    n = 0
    try:
        for kind, r, xb, units, arows in plan:
            if kind == "체계도":
                _nodes, _edges, lines = parse_stmd(xb)
                pp = os.path.join(REPO, r["파일경로"])
                npg, h = _swap_render(render.hierarchy_html(lines, r["상위법"], r["시행일자"],
                                                            r["법령일련번호"]), pp)
                r.update(페이지수=npg, sha256=h)
                n += 1
                continue
            pending = r["시행예정여부"] == "Y"
            is_rule = r["계층"] == "행정규칙"
            for a, ar in zip(units, arows):
                if ar["상태"] == RENDERED_ANNEX:
                    ap = os.path.join(REPO, ar["파일경로"])
                    npg, h = _swap_render(render.annex_text_html(
                        a["unit"], r["정식명"], r["시행일자"], r["법령일련번호"], pending,
                        "행정규칙" if is_rule else ""), ap)
                    ar.update(페이지수=npg, sha256=h)
                    n += 1
            fn = render.admrul_html if is_rule else render.law_html
            h, _nm, labels = fn(xb, r["시행일자"], r["법령일련번호"], pending, annex_files(arows))
            pdfp = os.path.join(REPO, r["파일경로"])
            _swap_render(h, pdfp)
            new = body_row({}, pdfp, labels, len(arows))
            r.update(페이지수=new["페이지수"], sha256=new["sha256"], 상태=new["상태"],
                     비고=new["비고"])
            n += 1
    finally:
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
