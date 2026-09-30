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
  · 첨부파일: 고시·세칙 첨부 **전부**를 원본 그대로(hwp·pdf·hwpx·zip·xlsx …) — 고르지 않는다.
    규칙 전문은 본문 PDF(원문 XML)가 기준이다(fetch_attachments 참고)
  · 폴더: B_추가검토/2_행정규칙/<상위 법률>/<NN_규칙명>. 상위 법률 = 그 규칙을 체계도에
    올린 법률 중 목록 순서상 첫째. 나머지 상위 법률은 manifest 상위법 칸에 병기한다
「한국표준산업분류」는 보류(사용자가 정한다) — 받지 않고 크기만 잰다.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
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
    err = os.path.join(PARTS, key + ".err")
    if os.path.exists(err):                      # 앞선 실패 기록은 이력으로 옮겨 둔다
        os.makedirs(os.path.join(PARTS, "_이전실패"), exist_ok=True)
        os.replace(err, os.path.join(PARTS, "_이전실패", key + ".err"))
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


ATT_EXT = {".pdf": "PDF", ".hwp": "HWP", ".hwpx": "HWPX", ".zip": "ZIP", ".xlsx": "XLSX",
           ".docx": "DOCX"}
FMT_EXT = {"PDF": ".pdf", "HWP": ".hwp", "HWPX": ".hwpx", "ZIP": ".zip", "XLSX": ".xlsx",
           "DOCX": ".docx", "OLE": ".ole"}


def fetch_attachments(client, atts, dest_dir, stem, meta):
    """행정규칙 첨부파일 **전부**를 원본 그대로 받는다(hwp·pdf·hwpx·zip·xlsx …).

    어느 첨부가 규칙 전문인지는 이름·순서로 가를 수 없다(실측: 첫 첨부가 다른 고시의
    제정고시문, 2쪽짜리 개정고시문, 여러 문서를 묶은 zip, 서식이 가리키는 엑셀 양식).
    그래서 고르지 않고 모두 남기며, 원파일명·실제 형식을 적는다. 형식은 확장자가 아니라
    바이트로 판정한다(zip 을 hwpx 로 적지 않는다). 규칙 전문은 본문 PDF(원문 XML)가 기준이다.
    """
    if not atts:
        return [dict(meta, 유형="첨부파일", 상태="없음", 비고="XML 에 첨부파일 없음")]
    rows = []
    for i, (name, link) in enumerate(atts, 1):
        u = urllib.parse.urlsplit(link)
        st, body, ct, murl, host = client.file(u.path + ("?" + u.query if u.query else ""))
        fmt = collect.sniff(body) if body else ""
        row = dict(meta, 유형="첨부파일", 번호=str(i), 제목=name, 출처URL=murl)
        if st != 200 or not body or fmt.startswith(("HTML", "기타", "ZIP?")):
            rows.append(dict(row, 상태="실패", 비고="원파일명 %s → %s" % (name, fmt or "응답 없음")))
            continue
        ext0 = os.path.splitext(name)[1].lower()
        want = ATT_EXT.get(ext0)
        ext = FMT_EXT.get(fmt, ext0 or ".bin")
        label = collect.title_slug(name[:-len(ext0)] if want else name, n=60)
        dest = collect.fit_dest(os.path.join(dest_dir, "%s_첨부%02d" % (stem, i)), label, tail=ext)
        try:
            h = collect.write(dest + ext, body)
        except OSError as e:
            rows.append(dict(row, 상태="실패", 비고="저장 실패(%s): 원파일명 %s" % (type(e).__name__, name)))
            continue
        note = "법제처 첨부파일 원본 그대로 · 원파일명 %s" % name
        if want and want != fmt:
            note += " · 확장자(%s)와 실제 형식(%s)이 다름 — 실제 형식으로 저장" % (want, fmt)
        if fmt == "ZIP":
            import zipfile
            with zipfile.ZipFile(dest + ext) as z:
                members = [m.filename for m in z.infolist() if not m.is_dir()]
            note += " · 묶음 파일 %d개" % len(members)
        pages = render.pdf_info(dest + ext)[1] if fmt == "PDF" else ""
        rows.append(dict(row, 파일경로=collect.rel(dest + ext), 원본형식=fmt, 페이지수=pages,
                         sha256=h, 상태="OK", 비고=note))
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
        try:
            units = collect.annex_list(xb) if xb else []
        except ET.ParseError as e:
            out[name] = {"정식명": cur["행정규칙명"], "상태": "측정 실패 — XML 해석 불가: %s" % e,
                         "출처URL": murl}
            continue
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
            except (lawclient.AuthError, lawclient.BlockedError):
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
            except (lawclient.AuthError, lawclient.BlockedError):
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
    except lawclient.BlockedError as e:
        # 끝난 법령은 parts 에 남아 있다. 다시 부르면 끝나지 않은 것부터 이어간다.
        log("■ 서버 차단 — 멈춥니다(끝난 법령은 보존, 재개 시 이어서). %s" % client.mask(str(e)))
        return 4
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
                e = extra.setdefault(n["ID"], {"ID": n["ID"], "일련번호": n.get("일련번호", ""),
                                               "시행일자": n.get("시행일자", ""), "이름": n["이름"],
                                               "종류": n["종류"], "상위": []})
                if law not in e["상위"]:
                    e["상위"].append(law)
    hj = {"생성": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "원천": "lsStmd",
          "법령": laws, "체계도에만있는행정규칙": list(extra.values())}
    with open(os.path.join(collect.MAN, "hierarchy.json"), "w", encoding="utf-8") as f:
        json.dump(hj, f, ensure_ascii=False, indent=1)
    # 행정규칙이 어느 법률 폴더에 들어갔고 체계도상 상위 법률은 무엇인지 — 폴더만 보면
    # 「보험업감독규정이 왜 외국환거래법 밑에?」가 되므로 한 표로 남긴다.
    prow = []
    for i, req in enumerate(T.B2_RULES, 1):
        d = part_done(part_key("B-2", i)) or {}
        prow.append(dict(순번=i, 요청명=req, 정식명=d.get("정식명", ""), 폴더=d.get("폴더", ""),
                         체계도상위법률=" · ".join(d.get("상위법") or []) or "(체계도 미연결)",
                         배치규칙="체계도에 이 규칙을 올린 법률 중 목록(A→B-1) 순서상 첫째"))
    collect.write_csv(os.path.join(collect.MAN, "행정규칙_상위법.csv"), prow,
                      ["순번", "요청명", "정식명", "폴더", "체계도상위법률", "배치규칙"])
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
        # 파일 없는 기록 행(폐기한 보조뷰어·실패·없음)도 그 법령 zip 의 manifest 에 넣는다.
        sig = {(r["그룹"], r["상위법"] if r["그룹"] != "B-2" else r["정식명"]) for r in mine}
        mine += [r for r in rows if not r["파일경로"] and
                 (r["그룹"], r["상위법"] if r["그룹"] != "B-2" else r["정식명"]) in sig]
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


def wait_and_run(interval=900, tries=16):
    """서버 차단이 풀릴 때까지 기다렸다가 재개한다. 확인은 **가벼운 검색 한 번**뿐이고,
    차단 페이지를 따라가지 않는다. 풀리면 run() — 끝난 법령은 건너뛴다."""
    client = lawclient.LawClient(os.path.join(collect.MAN, "call_log.csv"))
    for i in range(1, tries + 1):
        try:
            st, body, murl, host = client.api("lawSearch.do", target="eflaw", type="XML",
                                              query="중대재해 처벌 등에 관한 법률", nw="3")
            ET.fromstring(body)
            log("차단 풀림 확인(%d번째 확인) — 간격 %.1f초로 재개" % (i, client.delay))
            return run()
        except (lawclient.BlockedError, ET.ParseError) as e:
            log("아직 차단(%d/%d) — %d분 뒤 다시 확인. %s" % (i, tries, interval // 60,
                                                          client.mask(str(e))[:120]))
        time.sleep(interval)
    log("■ %d번 확인했지만 차단이 풀리지 않음 — 멈춥니다" % tries)
    return 4


# ── 사후 보정 ─────────────────────────────────────────────────────────────
RETRY_STATES = ("실패", "HWP대체(PDF실패)")


def _vkey(r):
    return (r["그룹"], r["상위법"], r["계층"], r["정식명"], r["법령일련번호"], r["시행일자"],
            r["시행예정여부"])


def _load_part(key):
    p = os.path.join(PARTS, key + ".manifest.csv")
    return p, list(csv.DictReader(open(p, encoding="utf-8-sig")))


def _rebody(rows, x, is_rule):
    """한 판의 본문 PDF 를 저장된 원문 XML 로 다시 찍고 행을 갱신한다(별표 목록이 바뀐 뒤)."""
    xb = open(os.path.join(collect.REPO, x["파일경로"]), "rb").read()
    arows = [r for r in rows if r["유형"] in ("별표", "서식") and _vkey(r) == _vkey(x)]
    b = [r for r in rows if r["유형"] == "본문" and _vkey(r) == _vkey(x)][0]
    pending = x["시행예정여부"] == "Y"
    fn = render.admrul_html if is_rule else render.law_html
    h, _nm, labels = fn(xb, x["시행일자"], x["법령일련번호"], pending, collect.annex_files(arows))
    pdfp = os.path.join(collect.REPO, b["파일경로"])
    collect._swap_render(h, pdfp)
    new = collect.body_row({}, pdfp, labels, len(arows))
    b.update(페이지수=new["페이지수"], sha256=new["sha256"], 상태=new["상태"], 비고=new["비고"])


def retry():
    """「실패」·「HWP대체(PDF실패)」 별표·서식만 다시 받는다. 받은 판은 본문 PDF 의 별표
    목록도 다시 찍는다. PDF 를 새로 받으면 앞서 대신 받은 HWP 는 치우고 비고에 적는다."""
    client = lawclient.LawClient(os.path.join(collect.MAN, "call_log.csv"))
    fixed, still = [], []
    try:
        for key in order_keys():
            if not part_done(key):
                continue
            path, rows = _load_part(key)
            todo = [r for r in rows if r["유형"] in ("별표", "서식") and r["상태"] in RETRY_STATES]
            if not todo:
                continue
            touched = set()
            for r in todo:
                x = [q for q in rows if q["유형"] == "원문XML" and _vkey(q) == _vkey(r)][0]
                xb = open(os.path.join(collect.REPO, x["파일경로"]), "rb").read()
                units = collect.annex_list(xb)
                arows = [q for q in rows if q["유형"] in ("별표", "서식") and _vkey(q) == _vkey(r)]
                a = units[arows.index(r)]
                assert a["번호"] == r["번호"], (a["번호"], r["번호"])
                stem = os.path.basename(x["파일경로"])[:-len("_원문.xml")]
                tdir = os.path.dirname(os.path.join(collect.REPO, x["파일경로"]))
                sub = collect.annex_sub(a)
                dest = collect.fit_dest(os.path.join(tdir, sub, "%s_%s%s" % (
                    stem, collect.slug(a["구분"]) or sub, a["번호"])), collect.title_slug(a["제목"]))
                is_rule = r["계층"] == "행정규칙"
                meta = {k: r[k] for k in ("그룹", "상위법", "계층", "정식명", "법령ID", "법령일련번호",
                                          "공포일자", "공포번호", "시행일자", "시행예정여부", "소관부처")}
                new = collect.fetch_annex(client, a, dest, meta,
                                          ctx=(r["정식명"], r["시행일자"], r["법령일련번호"],
                                               r["시행예정여부"] == "Y", is_rule))
                old_path, old_state = r["파일경로"], r["상태"]
                if new["상태"] in ("OK", "삭제별표") or (new["상태"] != "실패" and old_state == "실패"):
                    if old_path and old_path != new.get("파일경로") and os.path.exists(
                            os.path.join(collect.REPO, old_path)):
                        os.remove(os.path.join(collect.REPO, old_path))
                    new["비고"] = ("재시도로 확보(%s, 이전 상태 %s%s)" % (
                        time.strftime("%Y-%m-%d %H:%M"), old_state,
                        ", 대신 받은 HWP 교체" if old_state != "실패" else "")
                        + (" · " + new["비고"] if new.get("비고") else ""))
                    r.clear()
                    r.update({c: new.get(c, "") for c in collect.MANIFEST_COLS})
                    fixed.append("%s %s %s%s → %s" % (r["정식명"], r["시행일자"], r["유형"], r["번호"],
                                                      r["상태"]))
                    touched.add(_vkey(x))
                else:
                    still.append("%s %s %s%s (%s)" % (r["정식명"], r["시행일자"], r["유형"], r["번호"],
                                                      new.get("비고", "")))
            for vk in touched:
                x = [q for q in rows if q["유형"] == "원문XML" and _vkey(q) == vk][0]
                _rebody(rows, x, x["계층"] == "행정규칙")
            collect.write_csv(path, rows, collect.MANIFEST_COLS)
    except lawclient.BlockedError as e:
        log("■ 서버 차단 — 재시도 중단. %s" % client.mask(str(e)))
    log("재시도 — 확보 %d · 여전히 못 받음 %d · 호출 %d" % (len(fixed), len(still), client.n_calls))
    for f in fixed + ["여전히: " + s_ for s_ in still]:
        log("  ", f)
    return 0 if not still else 1


def recheck():
    """API 호출 없이 본문 PDF 의 조문 검사와 시행규칙 「없음」 비고를 새 규칙으로 다시 판정한다
    (PDF·XML 은 그대로 — sha256 불변)."""
    changed = []
    for key in order_keys():
        if not part_done(key):
            continue
        path, rows = _load_part(key)
        xs = {_vkey(r): r for r in rows if r["유형"] == "원문XML" and r["파일경로"]}
        dirty = False
        for b in rows:
            if b["유형"] != "본문" or not b["파일경로"] or _vkey(b) not in xs:
                continue
            xb = open(os.path.join(collect.REPO, xs[_vkey(b)]["파일경로"]), "rb").read()
            if b["계층"] == "행정규칙":
                labels = render.admrul_html(xb, b["시행일자"], b["법령일련번호"])[2]
            else:
                labels = render.article_labels(ET.fromstring(xb))
            n_ax = sum(1 for r in rows if r["유형"] in ("별표", "서식") and _vkey(r) == _vkey(b))
            new = collect.body_row({}, os.path.join(collect.REPO, b["파일경로"]), labels, n_ax)
            if new["sha256"] != b["sha256"]:
                raise SystemExit("본문 PDF 가 manifest 와 다르다: %s" % b["파일경로"])
            if (new["상태"], new["비고"]) != (b["상태"], b["비고"]):
                changed.append("%s %s %s: %s → %s" % (b["정식명"], b["시행일자"], b["계층"],
                                                      b["상태"], new["상태"]))
                b.update(상태=new["상태"], 비고=new["비고"])
                dirty = True
        if dirty:
            collect.write_csv(path, rows, collect.MANIFEST_COLS)
        lp = os.path.join(PARTS, key + ".lawlist.csv")
        lrows = list(csv.DictReader(open(lp, encoding="utf-8-sig")))
        d = part_done(key)
        ldirty = False
        for r in lrows:
            if r["상태"] == "없음" and r["계층"] == "시행규칙" and d.get("시행규칙급_체계도노드") is not None:
                law = r["정식명"][:-len(" 시행규칙")] if r["정식명"].endswith(" 시행규칙") else r["정식명"]
                note = collect.rule_absence_note(law, d["시행규칙급_체계도노드"])
                m = re.search(r"사용자 확인\(.*$", r["비고"] or "")
                if m:
                    note += " · " + m.group(0)
                if note != r["비고"]:
                    changed.append("%s 없음 비고 갱신" % r["정식명"])
                    r["비고"] = note
                    ldirty = True
        if ldirty:
            collect.write_csv(lp, lrows, collect.LAWLIST_COLS)
    log("재판정 — 바뀐 행 %d" % len(changed))
    for c in changed:
        log("  ", c)
    return 0


# ── 전달용 묶음 ───────────────────────────────────────────────────────────
BUNDLE_CAP = int(28.5 * 2 ** 20)      # 원본 바이트 합 상한 — 압축 뒤 30MiB(전달 한도) 아래
SEND_LIMIT = 30 * 2 ** 20
MAN_FILES = ["manifest.csv", "law_list.csv", "hierarchy.json", "verify7.txt", "행정규칙_상위법.csv",
             "서식200초과_목록.csv", "보류_크기측정.json", "resolve.json", "call_log.csv"]


def _unit_files(folder):
    out = []
    for root, ds, fs in os.walk(folder):
        ds.sort()
        for f in sorted(fs):
            if ".tmp" in f:
                continue
            out.append(os.path.join(root, f))
    return out


def bundle(out_dir):
    """법령 원문 전체를 30MiB 아래 묶음으로(사용자 요청 2026-09-29, 대화로 전달).

    순서: 00_manifest(기록) → A 01~15 → B-1 01~14 → B-2 규칙 01~18. zip 안 경로는
    law_archive/ 아래 구조 그대로. 법령 폴더를 통째로 담고, 넘치면 다음 묶음. 한 법령이
    상한보다 크면 **파일 단위로** 여러 묶음에 나눈다(바이트 분할이 아니라 묶음마다 따로 열린다).
    """
    import hashlib
    units = [("00_manifest", [os.path.join(collect.MAN, f) for f in MAN_FILES
                              if os.path.exists(os.path.join(collect.MAN, f))])]
    for grp in ("A", "B-1"):
        gdir = os.path.join(collect.ARCH, collect.GROUP_DIR[grp])
        for d in sorted(os.listdir(gdir)):
            units.append(("%s %s" % (grp, d), _unit_files(os.path.join(gdir, d))))
    rules = []
    for par in sorted(os.listdir(RULE_DIR)):
        for d in os.listdir(os.path.join(RULE_DIR, par)):
            rules.append((d, os.path.join(RULE_DIR, par, d)))
    for d, full in sorted(rules):
        units.append(("B-2 %s" % d, _unit_files(full)))
    # 짜기
    plan, cur, size = [], [], 0
    for label, files in units:
        tot = sum(os.path.getsize(f) for f in files)
        if tot <= BUNDLE_CAP and size + tot <= BUNDLE_CAP:
            cur.append((label, files)); size += tot
            continue
        if cur:
            plan.append(cur); cur, size = [], 0
        if tot <= BUNDLE_CAP:
            cur.append((label, files)); size = tot
            continue
        part, psize, k = [], 0, 1                      # 큰 법령 — 파일 단위로 나눈다
        for f in files:
            fs = os.path.getsize(f)
            if part and psize + fs > BUNDLE_CAP:
                plan.append([("%s (나눔 %d)" % (label, k), part)]); part, psize, k = [], 0, k + 1
            part.append(f); psize += fs
        cur, size = [("%s (나눔 %d)" % (label, k) if k > 1 else label, part)], psize
    if cur:
        plan.append(cur)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.startswith("7차_법령원문_"):
            os.remove(os.path.join(out_dir, f))
    n = len(plan)
    rows_all, made = [], []
    for i, b in enumerate(plan, 1):
        name = "7차_법령원문_%02d_of_%02d.zip" % (i, n)
        for label, files in b:
            for f in files:
                h = hashlib.sha256(open(f, "rb").read()).hexdigest()
                rows_all.append(dict(묶음=name, 단위=label, 파일경로=collect.rel(f),
                                     바이트=os.path.getsize(f), sha256=h))
    cols = ["묶음", "단위", "파일경로", "바이트", "sha256"]
    for i, b in enumerate(plan, 1):
        name = "7차_법령원문_%02d_of_%02d.zip" % (i, n)
        zp = os.path.join(out_dir, name)
        mine = [r for r in rows_all if r["묶음"] == name]
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for label, files in b:
                for f in files:
                    z.write(f, collect.rel(f))
            for fn, lst in (("묶음목록_이묶음.csv", mine),) + ((("묶음목록_전체.csv", rows_all),) if i == 1 else ()):
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=cols)
                w.writeheader()
                w.writerows(lst)
                z.writestr("law_archive/" + fn, ("\ufeff" + buf.getvalue()).encode("utf-8"))
        made.append((name, os.path.getsize(zp), [lab for lab, _f in b], len(mine)))
    over = [m for m in made if m[1] >= SEND_LIMIT]
    for name, sz, labs, cnt in made:
        print("%s  %5.1fMiB  파일 %4d  %s" % (name, sz / 2 ** 20, cnt,
                                            ", ".join(labs) if len(labs) <= 4 else
                                            "%s … %s (%d개)" % (labs[0], labs[-1], len(labs))))
    print("묶음 %d개 · 파일 %d개 · 합계 %.1fMiB · 30MiB 이상 %d" % (
        n, len(rows_all), sum(m[1] for m in made) / 2 ** 20, len(over)))
    return made, rows_all, over


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "run"
    if cmd == "run":
        return run()
    if cmd == "waitrun":
        return wait_and_run()
    if cmd == "retry":
        return retry()
    if cmd == "recheck":
        return recheck()
    if cmd == "bundle":
        made, rows_all, over = bundle(argv[2])
        return 0 if not over else 1
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
