# -*- coding: utf-8 -*-
"""7차 본 수집 — 목록 전체(A 15 · B-1 14 · B-2 18). 사용자 지시(2026-09-29): 확인 없이 진행.

    python3 scripts/law/runall.py run      본 수집(중단되면 다시 부르면 끝난 법령은 건너뛴다)
    python3 scripts/law/runall.py merge    parts → manifest.csv · law_list.csv · hierarchy.json
    python3 scripts/law/runall.py zip      법령 단위 zip(A·B 따로) → law_archive_zip/

순서: 법률(A→B-1) 먼저 — 체계도가 모여야 행정규칙의 상위 법률 폴더를 정할 수 있다 —
그다음 행정규칙(B-2). 법령 하나가 끝날 때마다 00_manifest/parts/ 에 그 법령의 manifest·
law_list·체계도를 쓴다. 그래서 중간에 죽어도 끝난 법령은 다시 받지 않는다.

행정규칙
  · 현행: resolve 가 확정한 판. 시행예정: 연혁 검색(nw=2)에서 같은 이름·시행일 > 오늘인 판
    (실측: 행정규칙 기본 검색은 현행만 준다)
  · 본문 XML(lawService target=admrul ID=행정규칙일련번호) → 본문 PDF(목록만 실은 별표)
  · 별표·서식: 법령과 같은 규칙(PDF 우선 → HWP → 링크 없으면 XML 별표내용 렌더링)
  · 첨부파일: 고시·세칙 **전체 원본**(법제처가 싣는 hwp·pdf). PDF 우선, 없으면 HWP
  · 폴더: B_추가검토/2_행정규칙/<상위 법률>/<NN_규칙명>. 상위 법률 = 그 규칙을 체계도에
    올린 법률 중 목록 순서상 첫째. 나머지 상위 법률은 manifest 상위법 칸에 병기한다
「한국표준산업분류」는 보류(사용자가 정한다) — 받지 않고 크기만 잰다.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import traceback
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect       # noqa: E402
import lawclient     # noqa: E402
import render        # noqa: E402
import resolve       # noqa: E402
import targets as T  # noqa: E402

PARTS = os.path.join(collect.MAN, "parts")
ZIPS = os.path.join(collect.REPO, "law_archive_zip")
RULE_DIR = os.path.join(collect.ARCH, collect.GROUP_DIR["B-2"])
NO_PARENT = "00_체계도미연결"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def part_key(grp, seq):
    return "%s_%02d" % (grp, seq)


def part_done(key):
    p = os.path.join(PARTS, key + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    return d if d.get("완료") else None


def save_part(key, mrows, lrows, extra):
    os.makedirs(PARTS, exist_ok=True)
    collect.write_csv(os.path.join(PARTS, key + ".manifest.csv"), mrows, collect.MANIFEST_COLS)
    collect.write_csv(os.path.join(PARTS, key + ".lawlist.csv"), lrows, collect.LAWLIST_COLS)
    extra = dict(extra, 완료=True, 시각=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    with open(os.path.join(PARTS, key + ".json"), "w", encoding="utf-8") as f:
        json.dump(extra, f, ensure_ascii=False, indent=1)


# ── 이름 확정(사용자 확인 2건 반영) ──────────────────────────────────────
def final_resolve(client):
    res = collect.load_resolve()
    if res is None:
        res = collect.do_resolve(client)[0]
    changed = False
    for req, official in T.NAME_OVERRIDES.items():
        note = T.OVERRIDE_NOTE % (req, official)
        if req in res["laws"] and res["laws"][req].get("사용자확인") != official:
            tiers, status, cands = resolve.resolve_law(client, official)
            v = res["laws"][req]
            v.update(계층=tiers, 상태="확정" if status == "확정" else status, 후보=cands,
                     사용자확인=official, 비고=note)
            changed = True
        if req in res["rules"] and res["rules"][req].get("사용자확인") != official:
            row, status, how, cands = resolve.resolve_rule(client, official)
            v = res["rules"][req]
            v.update(현행=row, 상태=status, 일치=how, 후보=cands, 사용자확인=official, 비고=note)
            changed = True
    if changed:
        with open(os.path.join(collect.MAN, "resolve.json"), "w", encoding="utf-8") as f:
            f.write(client.mask(json.dumps(res, ensure_ascii=False, indent=1)))
    bad = [k for k, v in list(res["laws"].items()) + list(res["rules"].items())
           if v.get("그룹") != "보류" and v.get("상태") != "확정"]
    if bad:
        raise SystemExit("아직 확정되지 않은 이름: %s" % ", ".join(bad))
    return res


# ── 법률(3단) ─────────────────────────────────────────────────────────────
def run_law(client, grp, seq, req, info, carry_rows=()):
    official = info.get("사용자확인") or req
    mrows, lrows, hier, stmd_rules = collect.collect_law(client, grp, seq, official, info)
    for r in lrows:                      # 요청명은 요청서 표기 그대로 남긴다
        r["요청명"] = req
        if info.get("사용자확인"):
            r["비고"] = ((r.get("비고") or "") + " · " + info["비고"]).strip(" ·")
    mrows.extend(carry_rows)
    top = info["계층"]["법률"]["현행"]["법령명한글"]
    save_part(part_key(grp, seq), mrows, lrows, {
        "그룹": grp, "순번": seq, "요청명": req, "법률": top,
        "노드": list(hier["nodes"].values()),
        "간선": [{"from": a, "to": b, "관계": r} for a, b, r in hier["edges"]],
        "시행규칙급_체계도노드": stmd_rules})


# ── 행정규칙 ──────────────────────────────────────────────────────────────
def rule_parents(res):
    """{행정규칙ID: [상위 법률 이름…]} — 법률 목록 순서(A→B-1)대로."""
    out = {}
    for grp, seq, req in T.all_law_targets():
        d = part_done(part_key(grp, seq))
        if not d:
            continue
        for n in d["노드"]:
            if n.get("분류") == "행정규칙" and n.get("ID"):
                lst = out.setdefault(n["ID"], [])
                if d["법률"] not in lst:
                    lst.append(d["법률"])
    return out


def rule_versions(client, cur, official):
    """현행 + 시행예정(연혁 검색에서 같은 이름·시행일 > 오늘)."""
    rows = resolve._search(client, "admrul", official, nw="2")
    seen, pend = {cur["행정규칙일련번호"]}, []
    for r in sorted(rows, key=lambda r: (r.get("시행일자", ""), r.get("행정규칙일련번호", ""))):
        if (r.get("행정규칙명") == official and r.get("시행일자", "") > resolve.TODAY
                and r.get("행정규칙일련번호") not in seen):
            seen.add(r["행정규칙일련번호"])
            pend.append(r)
    return [(cur, False)] + [(r, True) for r in pend], len(rows)


def attachments(xml_bytes):
    """<첨부파일> 의 (파일명, 링크) 쌍 — 순서대로 번갈아 나온다(실측)."""
    root = ET.fromstring(xml_bytes)
    out = []
    for a in root.findall("첨부파일"):
        name = None
        for c in a:
            t = (c.text or "").strip()
            if c.tag == "첨부파일명":
                name = t
            elif c.tag == "첨부파일링크" and t:
                out.append((name or "", t))
                name = None
    return out


def fetch_attachments(client, atts, dest_dir, stem, meta):
    """고시·세칙 전체 원본. PDF 가 있으면 PDF 만, 없거나 실패하면 HWP."""
    rows = []
    pdfs = [a for a in atts if a[0].lower().endswith(".pdf")]
    others = [a for a in atts if not a[0].lower().endswith(".pdf")]
    tried = []
    for name, link in pdfs + others:
        path_qs = urllib.parse.urlsplit(link)
        path_qs = path_qs.path + ("?" + path_qs.query if path_qs.query else "")
        st, body, ct, murl, host = client.file(path_qs)
        fmt = collect.sniff(body) if body else ""
        tried.append("%s→%s" % (name, fmt or "실패"))
        if st == 200 and fmt in ("PDF", "HWP", "HWPX"):
            ext = {"PDF": ".pdf", "HWP": ".hwp", "HWPX": ".hwpx"}[fmt]
            path = os.path.join(dest_dir, "%s_첨부원본%s" % (stem, ext))
            try:
                h = collect.write(path, body)
            except OSError as e:
                tried[-1] += " 저장실패(%s)" % type(e).__name__
                continue
            pages = render.pdf_info(path)[1] if fmt == "PDF" else ""
            rows.append(dict(meta, 유형="첨부원본", 제목=name, 파일경로=collect.rel(path),
                             원본형식=fmt, 페이지수=pages, sha256=h, 출처URL=murl,
                             상태="OK" if (fmt == "PDF" or not pdfs) else "HWP대체(PDF실패)",
                             비고="고시·세칙 전체 원본(법제처 첨부파일) · 원파일명 %s" % name))
            return rows
    rows.append(dict(meta, 유형="첨부원본", 상태="실패" if atts else "없음",
                     비고="; ".join(tried) if atts else "XML 에 첨부파일 없음"))
    return rows


def run_rule(client, seq, req, info, parents):
    cur = info["현행"]
    official = cur["행정규칙명"]
    pars = parents.get(cur.get("행정규칙ID", ""), [])
    pdir = collect.slug(pars[0]) if pars else NO_PARENT
    base = os.path.join(RULE_DIR, pdir, T.folder_name(seq, official))
    versions, n_hist = rule_versions(client, cur, official)
    same_day = {}
    for r, p in versions:
        same_day[(r["시행일자"], p)] = same_day.get((r["시행일자"], p), 0) + 1
    mrows, lrows = [], []
    for row, pending in versions:
        ef, serial = row["시행일자"], row["행정규칙일련번호"]
        stem = "%s_행정규칙_%s%s" % (collect.slug(official), ef, "_시행예정" if pending else "")
        if same_day[(ef, pending)] > 1:
            stem += "_일련번호%s" % serial
        collect.claim_stem(os.path.join(base, stem), (serial, ef, pending))
        meta = dict(그룹="B-2", 상위법=" · ".join(pars) or "(체계도 미연결)", 계층="행정규칙",
                    정식명=official, 법령ID=row.get("행정규칙ID", ""), 법령일련번호=serial,
                    공포일자=row.get("발령일자", ""), 공포번호=row.get("발령번호", ""), 시행일자=ef,
                    시행예정여부="Y" if pending else "N", 소관부처=row.get("소관부처명", ""))
        note = info.get("비고", "")
        if not pars:
            note = (note + " · 어느 법률의 체계도에도 없음 → %s 폴더" % NO_PARENT).strip(" ·")
        lrows.append(dict(그룹="B-2", 순번=seq, 요청명=req, 정식명=official, 계층="행정규칙",
                          법령ID=row.get("행정규칙ID", ""), 법령일련번호=serial,
                          공포일자=row.get("발령일자", ""), 공포번호=row.get("발령번호", ""),
                          시행일자=ef, 시행예정여부="Y" if pending else "N",
                          소관부처=row.get("소관부처명", ""), 법령구분=row.get("행정규칙종류", ""),
                          일치방식=info.get("일치", ""), 상태="확정", 비고=note))
        st, xb, murl, host = client.api("lawService.do", target="admrul", ID=serial, type="XML")
        if not xb:
            mrows.append(dict(meta, 유형="원문XML", 상태="실패", 출처URL=murl))
            continue
        noc = client.count_oc(xb)
        xdata = client.mask(xb) if noc else xb
        xpath = os.path.join(base, stem + "_원문.xml")
        h = collect.write(xpath, xdata)
        mrows.append(dict(meta, 유형="원문XML", 파일경로=collect.rel(xpath), 원본형식="XML",
                          sha256=h, 출처URL=murl, 상태="OK",
                          비고=("OC %d곳 가림 · 원 응답 sha256 %s" % (noc, collect.sha256(xb)))
                          if noc else "바이트 그대로(OC 0회)"))
        arows, used = [], set()
        for a in collect.annex_list(xdata):
            sub = collect.annex_sub(a)
            dest = collect.fit_dest(os.path.join(base, sub, "%s_%s%s" % (
                stem, collect.slug(a["구분"]) or sub, a["번호"])), collect.title_slug(a["제목"]))
            dup = ""
            if dest in used:
                k = 2
                while "%s_중복%d" % (dest, k) in used:
                    k += 1
                dest, dup = "%s_중복%d" % (dest, k), "같은 판에 구분·번호·제목이 같은 별표가 또 있어 _중복%d 을 붙임" % k
            used.add(dest)
            ar = collect.fetch_annex(client, a, dest, meta, ctx=(official, ef, serial, pending, True))
            if dup:
                ar["비고"] = (ar.get("비고", "") + " · " + dup).strip(" ·")
            arows.append(ar)
        html_text, _nm, labels = render.admrul_html(xdata, ef, serial, pending,
                                                    collect.annex_files(arows))
        pdfp = os.path.join(base, stem + "_본문.pdf")
        render.html_to_pdf(html_text, pdfp)
        mrows.append(collect.body_row(meta, pdfp, labels, len(arows), 출처URL=murl))
        mrows.extend(fetch_attachments(client, attachments(xdata), os.path.join(base, "첨부"),
                                       stem, meta))
        mrows.extend(arows)
    save_part(part_key("B-2", seq), mrows, lrows, {
        "그룹": "B-2", "순번": seq, "요청명": req, "정식명": official, "상위법": pars,
        "폴더": collect.rel(base), "연혁검색건수": n_hist,
        "시행예정": [r["행정규칙일련번호"] for r, p in versions if p]})


def probe_deferred(client, res):
    """보류 후보는 받지 않고 크기만 잰다(사용자가 정한다)."""
    out = {}
    for name, v in res["rules"].items():
        if v.get("그룹") != "보류" or not v.get("현행"):
            continue
        cur = v["현행"]
        st, xb, murl, host = client.api("lawService.do", target="admrul",
                                        ID=cur["행정규칙일련번호"], type="XML")
        units = collect.annex_list(xb) if xb else []
        out[name] = {"정식명": cur["행정규칙명"], "종류": cur.get("행정규칙종류"),
                     "소관부처": cur.get("소관부처명"), "시행일자": cur.get("시행일자"),
                     "행정규칙일련번호": cur["행정규칙일련번호"], "본문XML바이트": len(xb),
                     "별표서식수": len(units),
                     "첨부파일": [n for n, _l in attachments(xb)] if xb else [],
                     "출처URL": murl, "상태": "보류 — 받지 않음(크기만 측정)"}
    with open(os.path.join(collect.MAN, "보류_크기측정.json"), "w", encoding="utf-8") as f:
        f.write(client.mask(json.dumps(out, ensure_ascii=False, indent=1)))
    return out


# ── 본 수집 ───────────────────────────────────────────────────────────────
def run():
    client = lawclient.LawClient(os.path.join(collect.MAN, "call_log.csv"))
    collect._STEMS.clear()
    t0 = time.time()
    os.makedirs(PARTS, exist_ok=True)
    # 시범에서 버린 (나) 보조뷰어 기록은 금융지주회사법 part 로 옮겨 남긴다(파일 없음·폐기 사유).
    carry = []
    old = os.path.join(collect.MAN, "manifest.csv")
    if os.path.exists(old) and not part_done("A_15"):
        carry = [r for r in csv.DictReader(open(old, encoding="utf-8-sig"))
                 if r["유형"] == "보조뷰어"]
    try:
        res = final_resolve(client)
        errs = []
        laws = T.all_law_targets()
        for i, (grp, seq, req) in enumerate(laws, 1):
            key = part_key(grp, seq)
            if part_done(key):
                log("[%d/%d] %s %s — 이미 완료, 건너뜀" % (i, len(laws), key, req))
                continue
            log("[%d/%d] %s %s — 시작 (누적 호출 %d)" % (i, len(laws), key, req, client.n_calls))
            try:
                run_law(client, grp, seq, req, res["laws"][req],
                        carry if key == "A_15" else ())
                d = part_done(key)
                n = sum(1 for _ in open(os.path.join(PARTS, key + ".manifest.csv"),
                                        encoding="utf-8-sig")) - 1
                log("    완료 — manifest %d행 · 체계도 노드 %d" % (n, len(d["노드"])))
            except lawclient.AuthError:
                raise
            except Exception as e:                  # noqa: BLE001 — 법령 하나 실패로 전체를 멈추지 않는다
                msg = client.mask(traceback.format_exc())
                errs.append((key, req, client.mask(str(e))))
                with open(os.path.join(PARTS, key + ".err"), "w", encoding="utf-8") as f:
                    f.write(msg)
                log("    ■ 실패 — %s" % client.mask(str(e))[:300])
        parents = rule_parents(res)
        rules = [(i + 1, n) for i, n in enumerate(T.B2_RULES)]
        for j, (seq, req) in enumerate(rules, 1):
            key = part_key("B-2", seq)
            if part_done(key):
                log("[규칙 %d/%d] %s %s — 이미 완료, 건너뜀" % (j, len(rules), key, req))
                continue
            log("[규칙 %d/%d] %s %s — 시작 (누적 호출 %d)" % (j, len(rules), key, req, client.n_calls))
            try:
                run_rule(client, seq, req, res["rules"][req], parents)
                log("    완료")
            except lawclient.AuthError:
                raise
            except Exception as e:                  # noqa: BLE001
                errs.append((key, req, client.mask(str(e))))
                with open(os.path.join(PARTS, key + ".err"), "w", encoding="utf-8") as f:
                    f.write(client.mask(traceback.format_exc()))
                log("    ■ 실패 — %s" % client.mask(str(e))[:300])
        pr = probe_deferred(client, res)
        for k, v in pr.items():
            log("보류 %s — 본문 XML %d바이트 · 별표·서식 %d · 첨부 %s (받지 않음)"
                % (k, v["본문XML바이트"], v["별표서식수"], ", ".join(v["첨부파일"])))
    except lawclient.AuthError as e:
        log("■ 인증 오류 — 멈춥니다. 오류 원문:\n%s" % e)
        return 3
    merge()
    log("끝 — 호출 %d건 · %.1f분 · 실패 법령 %d" % (client.n_calls, (time.time() - t0) / 60, len(errs)))
    for e in errs:
        log("  실패:", *e)
    return 0 if not errs else 1


# ── 병합 ──────────────────────────────────────────────────────────────────
def order_keys():
    ks = [part_key(g, s) for g, s, _r in T.all_law_targets()]
    ks += [part_key("B-2", i + 1) for i in range(len(T.B2_RULES))]
    return ks


def merge():
    mrows, lrows, laws, missing = [], [], {}, []
    for key in order_keys():
        d = part_done(key)
        if not d:
            missing.append(key)
            continue
        mrows += list(csv.DictReader(open(os.path.join(PARTS, key + ".manifest.csv"),
                                          encoding="utf-8-sig")))
        lrows += list(csv.DictReader(open(os.path.join(PARTS, key + ".lawlist.csv"),
                                          encoding="utf-8-sig")))
        if "노드" in d:
            laws[d["법률"]] = {"그룹": d["그룹"], "순번": d["순번"], "노드": d["노드"],
                             "간선": d["간선"]}
    collect.write_csv(os.path.join(collect.MAN, "manifest.csv"), mrows, collect.MANIFEST_COLS)
    collect.write_csv(os.path.join(collect.MAN, "law_list.csv"), lrows, collect.LAWLIST_COLS)
    # 체계도에 올라 있지만 B-2 에 없는 행정규칙 — 추가 검토 후보
    b2_ids = {r["법령ID"] for r in lrows if r["그룹"] == "B-2"}
    extra = {}
    for law, v in laws.items():
        for n in v["노드"]:
            if n.get("분류") == "행정규칙" and n.get("ID") not in b2_ids:
                e = extra.setdefault(n["ID"], {"이름": n["이름"], "종류": n["종류"], "상위": []})
                if law not in e["상위"]:
                    e["상위"].append(law)
    hj = {"생성": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "원천": "lsStmd",
          "법령": laws, "체계도에만있는행정규칙": list(extra.values())}
    with open(os.path.join(collect.MAN, "hierarchy.json"), "w", encoding="utf-8") as f:
        json.dump(hj, f, ensure_ascii=False, indent=1)
    # 서식 200개 초과 판 — 목록(요청서 5-3; 사용자 지시로 확인 없이 받았고 목록은 남긴다)
    cnt = {}
    for r in mrows:
        if r["유형"] == "서식":
            k = (r["정식명"], r["시행일자"], r["시행예정여부"], r["법령일련번호"])
            cnt.setdefault(k, []).append(r)
    over = [(k, v) for k, v in cnt.items() if len(v) > 200]
    rows = [dict(정식명=k[0], 시행일자=k[1], 시행예정여부=k[2], 법령일련번호=k[3], 서식수=len(v),
                 번호=r["번호"], 제목=r["제목"], 파일경로=r["파일경로"], 상태=r["상태"])
            for k, v in over for r in v]
    collect.write_csv(os.path.join(collect.MAN, "서식200초과_목록.csv"), rows,
                      ["정식명", "시행일자", "시행예정여부", "법령일련번호", "서식수", "번호", "제목",
                       "파일경로", "상태"])
    print("병합 — manifest %d행 · law_list %d행 · 체계도 %d법령 · 체계도에만 있는 행정규칙 %d · "
          "서식 200 초과 판 %d · 미완료 part %s"
          % (len(mrows), len(lrows), len(laws), len(extra), len(over), missing or "없음"))


# ── zip ──────────────────────────────────────────────────────────────────
def zip_all():
    """법령 단위 zip. A·B 를 따로 둔다. 안에 그 법령의 manifest 행도 넣는다."""
    rows = list(csv.DictReader(open(os.path.join(collect.MAN, "manifest.csv"),
                                    encoding="utf-8-sig")))
    units = []
    for grp in ("A", "B-1"):
        gdir = os.path.join(collect.ARCH, collect.GROUP_DIR[grp])
        for d in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
            units.append(os.path.join(gdir, d))
    if os.path.isdir(RULE_DIR):
        for p in sorted(os.listdir(RULE_DIR)):
            for d in sorted(os.listdir(os.path.join(RULE_DIR, p))):
                units.append(os.path.join(RULE_DIR, p, d))
    made = []
    for u in units:
        relu = os.path.relpath(u, collect.ARCH)
        zp = os.path.join(ZIPS, relu + ".zip")
        os.makedirs(os.path.dirname(zp), exist_ok=True)
        prefix = collect.rel(u) + os.sep
        mine = [r for r in rows if r["파일경로"].startswith(prefix)]
        tmp = zp + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _ds, fs in os.walk(u):
                for f in sorted(fs):
                    if f.endswith(".tmp.pdf"):
                        continue
                    fp = os.path.join(root, f)
                    z.write(fp, os.path.relpath(fp, collect.ARCH))
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=collect.MANIFEST_COLS, extrasaction="ignore")
            w.writeheader()
            w.writerows(mine)
            z.writestr(os.path.join(relu, "manifest_이법령.csv"),
                       ("﻿" + buf.getvalue()).encode("utf-8"))
        os.replace(tmp, zp)
        made.append((zp, os.path.getsize(zp), len(mine)))
    tot = sum(s for _z, s, _n in made)
    print("zip %d개 · 합계 %.1f MB → %s" % (len(made), tot / 1e6, collect.rel(ZIPS)))
    return made


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "run"
    if cmd == "run":
        return run()
    if cmd == "merge":
        merge()
        return 0
    if cmd == "zip":
        zip_all()
        return 0
    print("알 수 없는 명령:", cmd)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
