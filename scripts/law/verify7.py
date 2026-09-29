# -*- coding: utf-8 -*-
"""7차 검증 — 요청서 「검증」 절 9항목. 결과는 00_manifest/verify7.txt 에도 쓴다.

    python3 scripts/law/verify7.py

API 를 부르지 않는다. 디스크의 원문 XML·PDF 와 manifest 만 본다.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect       # noqa: E402
import lawclient     # noqa: E402
import render        # noqa: E402

MAN = collect.MAN
REPO = collect.REPO
BASELINE = "/tmp/claude-0/snap7/baseline_1to6.sha256"
SAVED = ("OK", "삭제별표", "이동별표", "HWP대체(PDF실패)", collect.RENDERED_ANNEX)
MAGIC = {"PDF": lambda b: b[:4] == b"%PDF", "HWP": lambda b: b[:4] == b"\xd0\xcf\x11\xe0",
         "HWPX": lambda b: b[:4] == b"PK\x03\x04", "ZIP": lambda b: b[:4] == b"PK\x03\x04",
         "XLSX": lambda b: b[:4] == b"PK\x03\x04", "DOCX": lambda b: b[:4] == b"PK\x03\x04"}


def fold(s):
    """PDF 글자층 비교용: NFKC + Noto KR 글꼴이 다른 코드로 내보내는 두 글자(ʻ→‘, ⻑→長)."""
    import unicodedata
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s or "").replace("\u02bb", "\u2018")
                  .replace("\u2ed1", "\u9577"))

out_lines, fails = [], []


def say(s=""):
    print(s, flush=True)
    out_lines.append(s)


def check(name, ok, detail=""):
    say("  [%s] %s%s" % ("통과" if ok else "실패", name, (" — " + detail) if detail else ""))
    if not ok:
        fails.append(name)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def vkey(r):
    return (r["그룹"], r["상위법"], r["계층"], r["정식명"], r["법령일련번호"], r["시행일자"],
            r["시행예정여부"])


def main():
    rows = list(csv.DictReader(open(os.path.join(MAN, "manifest.csv"), encoding="utf-8-sig")))
    lrows = list(csv.DictReader(open(os.path.join(MAN, "law_list.csv"), encoding="utf-8-sig")))
    hj = json.load(open(os.path.join(MAN, "hierarchy.json"), encoding="utf-8"))
    oc = lawclient.load_oc()
    say("■ 7차 검증 — manifest %d행 · law_list %d행" % (len(rows), len(lrows)))

    xml_rows = [r for r in rows if r["유형"] == "원문XML" and r["파일경로"]]
    annex_by_v = {}
    for r in rows:
        if r["유형"] in ("별표", "서식"):
            annex_by_v.setdefault(vkey(r), []).append(r)

    # 1 ─ API 목록(원문 XML의 별표단위) 대비 저장 건수
    say("\n[1] 법령별·계층별 본문·별표·서식 — 원문 XML 목록 대비 저장")
    say("  %-44s %-6s %4s %4s %9s %9s" % ("법령(상위법)", "계층", "판", "본문", "별표 XML/저장", "서식 XML/저장"))
    agg, missing = {}, []
    bodies = {vkey(r): r for r in rows if r["유형"] == "본문"}
    for x in xml_rows:
        xb = open(os.path.join(REPO, x["파일경로"]), "rb").read()
        units = collect.annex_list(xb)
        ar = annex_by_v.get(vkey(x), [])
        k = (x["상위법"] if x["계층"] != "행정규칙" else x["정식명"], x["계층"])
        a = agg.setdefault(k, [0, 0, 0, 0, 0, 0])
        a[0] += 1
        b = bodies.get(vkey(x))
        a[1] += 1 if b and b["파일경로"] else 0
        for u in units:
            a[2 if collect.annex_sub(u) == "별표" else 4] += 1
        for r in ar:
            if r["파일경로"] and r["상태"] in SAVED:
                a[3 if r["유형"] == "별표" else 5] += 1
            else:
                missing.append("%s %s %s%s (%s)" % (x["정식명"], x["시행일자"], r["유형"], r["번호"],
                                                   r["상태"] + (": " + r["비고"] if r["비고"] else "")))
        if len(units) != len(ar):
            missing.append("%s %s — XML 별표 %d · manifest %d" % (x["정식명"], x["시행일자"],
                                                               len(units), len(ar)))
    for (law, tier), a in agg.items():
        say("  %-44s %-6s %4d %4d %4d/%-4d %4d/%-4d" % (law[:44], tier, a[0], a[1], a[2], a[3], a[4], a[5]))
    tot = [sum(a[i] for a in agg.values()) for i in range(6)]
    say("  합계: 판 %d · 본문 %d · 별표 %d/%d · 서식 %d/%d" % tuple(tot))
    check("원문 XML 판 수 = 본문 PDF 수", tot[0] == tot[1], "%d/%d" % (tot[1], tot[0]))
    check("별표·서식 누락 0", not missing, "; ".join(missing[:10]) + (" …외 %d" % (len(missing) - 10) if len(missing) > 10 else ""))
    xfail = [r for r in rows if r["유형"] in ("원문XML", "본문") and r["상태"] not in ("OK",)]
    check("원문 XML·본문 실패 0", not xfail,
          "; ".join("%s %s %s %s" % (r["정식명"], r["시행일자"], r["유형"], r["상태"]) for r in xfail[:10]))
    att = [r for r in rows if r["유형"] == "첨부파일"]
    att_bad = [r for r in att if r["상태"] not in ("OK", "없음")]
    import runall
    att_short = []
    for x in xml_rows:
        if x["계층"] != "행정규칙":
            continue
        want = len(runall.attachments(open(os.path.join(REPO, x["파일경로"]), "rb").read()))
        got = sum(1 for r in att if vkey(r) == vkey(x) and r["상태"] == "OK")
        if got != want:
            att_short.append("%s XML %d · 저장 %d" % (x["정식명"], want, got))
    say("  행정규칙 첨부파일 %d건 · 실패 %d" % (len(att), len(att_bad)))
    check("행정규칙 첨부파일 = XML 첨부 목록(전부)", not att_short and not att_bad,
          "; ".join(att_short[:5]))
    check("옛 「첨부원본」(하나만 고른) 행 0", not [r for r in rows if r["유형"] == "첨부원본"])

    # 2 ─ 시행규칙 「없음」 ↔ 체계도
    say("\n[2] 시행규칙 「없음」 ↔ 체계도")
    none_rows = [r for r in lrows if r["상태"] == "없음"]
    conflict = [r for r in none_rows if "목록 검색과 불일치" in (r["비고"] or "")]
    for r in none_rows:
        say("  없음: %s — %s" % (r["정식명"], r["비고"]))
    check("「없음」인데 체계도에 같은 이름의 시행규칙이 있는 법 0", not conflict,
          "; ".join(r["정식명"] + " " + r["비고"] for r in conflict))

    # 3 ─ %PDF·쪽수, manifest sha256 ↔ 디스크, 고아 파일
    say("\n[3] 파일 형식·쪽수·sha256")
    notpdf, zero, shabad, gone, magic_bad = [], [], [], [], []
    for r in rows:
        if not r["파일경로"]:
            continue
        p = os.path.join(REPO, r["파일경로"])
        if not os.path.exists(p):
            gone.append(r["파일경로"])
            continue
        if r["sha256"] and sha(p) != r["sha256"]:
            shabad.append(r["파일경로"])
        if r["원본형식"] in MAGIC:
            with open(p, "rb") as f:
                head = f.read(8)
            if not MAGIC[r["원본형식"]](head):
                magic_bad.append("%s(%s)" % (r["파일경로"], r["원본형식"]))
        if r["원본형식"] in ("HWPX", "ZIP", "XLSX") and collect._zip_kind(open(p, "rb").read()) != r["원본형식"]:
            magic_bad.append("%s(%s≠%s)" % (r["파일경로"], r["원본형식"],
                                           collect._zip_kind(open(p, "rb").read())))
        if p.lower().endswith(".pdf"):
            with open(p, "rb") as f:
                if not f.read(5).startswith(b"%PDF"):
                    notpdf.append(r["파일경로"])
            if str(r["페이지수"]).strip() in ("0", "-1"):
                zero.append(r["파일경로"])
    on_disk = set()
    for p in glob.glob(os.path.join(collect.ARCH, "**", "*"), recursive=True):
        if os.path.isfile(p) and os.sep + "00_manifest" + os.sep not in p:
            on_disk.add(os.path.relpath(p, REPO))
    listed = {r["파일경로"] for r in rows if r["파일경로"]}
    orphan = sorted(on_disk - listed - {p for p in on_disk if p.endswith(("체계도.json", "체계도.md"))})
    orphan = [p for p in orphan if not p.endswith("_run.log")]
    check("manifest 의 파일이 모두 디스크에 있다", not gone, "; ".join(gone[:5]))
    check("manifest sha256 = 디스크", not shabad, "; ".join(shabad[:5]))
    check("%PDF 아닌 .pdf 0", not notpdf, "; ".join(notpdf[:5]))
    check("파일 바이트 = manifest 원본형식(zip 을 hwpx 로 적지 않음)", not magic_bad,
          "; ".join(magic_bad[:5]))
    check("0쪽·쪽수 못 읽은 PDF 0", not zero, "; ".join(zero[:5]))
    check("manifest 에 없는 파일(고아) 0", not orphan, "; ".join(orphan[:5]))

    # 4 ─ HWP 로만 받은 별표·서식
    say("\n[4] HWP 로만 받은 별표·서식")
    hwp = [r for r in rows if r["유형"] in ("별표", "서식") and r["원본형식"] in ("HWP", "HWPX")]
    rend = [r for r in rows if r["상태"] == collect.RENDERED_ANNEX]
    sub = [r for r in rows if r["상태"] == "HWP대체(PDF실패)"]
    say("  HWP 원본 %d건 (그중 PDF 링크가 있었으나 실패 %d) · 원본 링크 없어 XML 렌더링 %d건"
        % (len(hwp), len(sub), len(rend)))
    for r in (hwp + rend)[:20]:
        say("   - %s %s %s%s %s" % (r["정식명"], r["시행일자"], r["유형"], r["번호"], r["상태"]))

    # 5 ─ 본문 PDF: 조문 표지 전부 + 첫 쪽 머리글
    say("\n[5] 본문 PDF — 조문 표지·첫 쪽 머리글")
    lab_bad, stamp_bad, unverif, weak_all = [], [], [], []
    ref_n, ref_miss = [0], []
    for x in xml_rows:
        b = bodies.get(vkey(x))
        if not b or not b["파일경로"]:
            continue
        xb = open(os.path.join(REPO, x["파일경로"]), "rb").read()
        if x["계층"] == "행정규칙":
            _h, _n, labels = render.admrul_html(xb, x["시행일자"], x["법령일련번호"])
        else:
            labels = render.article_labels(ET.fromstring(xb))
        ok, npg, txt = render.pdf_info(os.path.join(REPO, b["파일경로"]))
        miss, weak = render.label_check(labels, txt)
        if x["계층"] != "행정규칙":
            ft = fold(txt)
            for u in ET.fromstring(xb).iter("조문참고자료"):
                t = fold(u.text)[:15]
                if t:
                    ref_n[0] += 1
                    if t not in ft:
                        ref_miss.append("%s: %s" % (os.path.basename(b["파일경로"]), (u.text or "").strip()[:30]))
        if not labels:
            unverif.append(b["파일경로"])
        if miss:
            lab_bad.append("%s 누락 %d (%s)" % (b["파일경로"], len(miss), ",".join(miss[:3])))
        if weak:
            weak_all.append("%s %d (%s)" % (b["파일경로"], len(weak), ",".join(weak[:3])))
        first = re.sub(r"\s+", " ", txt[:400])
        want_date = render._fmt_date(x["시행일자"])
        okst = (want_date in first and x["법령일련번호"] in first
                and (("시행예정" in first) == (x["시행예정여부"] == "Y")))
        if not okst:
            stamp_bad.append(b["파일경로"])
    check("조문 표지 누락 0 (조 머리 꼴·부칙 앞까지)", not lab_bad, "; ".join(lab_bad[:5]))
    check("머리 꼴 없이 글자만 있는 표지 0", not weak_all, "; ".join(weak_all[:5]))
    check("조문참고자료(시행일·유효기간·위헌 주석 등) %d개 모두 본문에" % ref_n[0], not ref_miss,
          "; ".join(ref_miss[:5]))
    check("첫 쪽 머리글의 시행일·일련번호·시행예정 표시 = manifest", not stamp_bad, "; ".join(stamp_bad[:5]))
    say("  조문 표지를 못 찾아 누락 검사를 못 한 본문 %d건%s"
        % (len(unverif), (": " + "; ".join(unverif[:5])) if unverif else ""))

    # 6 ─ 체계도
    say("\n[6] 체계도")
    nn = sum(len(v["노드"]) for v in hj["법령"].values())
    ne = sum(len(v["간선"]) for v in hj["법령"].values())
    say("  법령 %d개 · 노드 %d · 상하위 관계 %d" % (len(hj["법령"]), nn, ne))
    for law, v in hj["법령"].items():
        say("   - %s: 노드 %d · 관계 %d" % (law, len(v["노드"]), len(v["간선"])))
    ex = hj.get("체계도에만있는행정규칙", [])
    say("  체계도에 있는데 B-2 에 없는 행정규칙 %d건 (추가 검토 후보)" % len(ex))
    for e in ex[:60]:
        say("   · [%s] %s ← %s" % (e["종류"], e["이름"], ", ".join(e["상위"][:3])))
    check("체계도 법령 수 = 법률 29", len(hj["법령"]) == 29, str(len(hj["법령"])))
    blank = [(law, n["key"]) for law, v in hj["법령"].items() for n in v["노드"] if not n.get("이름")]
    check("체계도 이름 없는 노드 0(자치법규 뭉침 방지)", not blank, str(blank[:3]))
    import collections as _c
    kinds = _c.Counter(n.get("분류") for v in hj["법령"].values() for n in v["노드"])
    say("  노드 분류: %s" % dict(kinds))

    # 7 ─ 시행예정·버전 중복
    say("\n[7] 시행예정·버전 키")
    pend = [r for r in xml_rows if r["시행예정여부"] == "Y"]
    keys = [(r["법령일련번호"], r["시행일자"], r["시행예정여부"], r["정식명"]) for r in xml_rows]
    paths = [r["파일경로"] for r in rows if r["파일경로"]]
    say("  시행예정 판 %d (법률 %d · 행정규칙 %d)" % (len(pend), sum(r["계층"] != "행정규칙" for r in pend),
                                             sum(r["계층"] == "행정규칙" for r in pend)))
    check("(MST, 시행일, 시행예정) 중복 0", len(keys) == len(set(keys)))
    past = [r for r in xml_rows if r["시행예정여부"] == "Y" and r["시행일자"] <= "20260929"]
    check("시행예정 판의 시행일 > 오늘(지난 판 0)", not past,
          "; ".join("%s %s" % (r["정식명"], r["시행일자"]) for r in past))
    ex = [r for r in lrows if r["상태"].startswith("제외")]
    say("  제외한 지난 판 %d: %s" % (len(ex), "; ".join("%s %s(%s)" % (r["정식명"], r["시행일자"],
                                                                   r["법령일련번호"]) for r in ex)))
    check("파일경로 중복 0", len(paths) == len(set(paths)), str(len(paths) - len(set(paths))))

    # 8 ─ OC 가림
    say("\n[8] OC 가림")
    stmd = [r for r in rows if r["유형"] == "체계도원문XML"]
    lenbad = [r["파일경로"] for r in stmd if "길이차 검증 일치" not in r["비고"]]
    check("체계도 가린 사본 길이차 = OC 등장 수 × (len−3)", not lenbad and bool(stmd),
          "%d건 중 불일치 %d" % (len(stmd), len(lenbad)))
    hits = []
    for p in on_disk:
        with open(os.path.join(REPO, p), "rb") as f:
            if oc.encode() in f.read():
                hits.append(p)
    for p in glob.glob(os.path.join(MAN, "**", "*"), recursive=True):
        if os.path.isfile(p) and oc.encode() in open(p, "rb").read():
            hits.append(os.path.relpath(p, REPO))
    check("law_archive 전체에 OC 원문 0", not hits, "; ".join(hits[:5]))

    # 9 ─ 1~6차 sha256·키 유출
    say("\n[9] 1~6차 산출물·키 유출")
    if os.path.exists(BASELINE):
        r = subprocess.run(["sha256sum", "-c", "--quiet", BASELINE], cwd=REPO,
                           capture_output=True, text=True)
        check("1~6차 산출물 sha256 동일", r.returncode == 0, (r.stdout + r.stderr).strip()[:300])
    else:
        check("1~6차 기준선 파일 있음", False, BASELINE)
    keys_ = {"LAW_OC": oc}
    dk = os.environ.get("DART_API_KEY") or ""
    envp = os.path.join(REPO, ".env")
    if not dk and os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            if line.startswith("DART_API_KEY="):
                dk = line.split("=", 1)[1].strip()
    if dk:
        keys_["DART_API_KEY"] = dk
    zhits, nz = [], 0
    for zp in glob.glob(os.path.join(REPO, "law_archive_zip", "**", "*.zip"), recursive=True):
        with zipfile.ZipFile(zp) as z:
            for n in z.namelist():
                nz += 1
                data = z.read(n)
                for k, v in keys_.items():
                    if v.encode() in data:
                        zhits.append("%s!%s ← %s" % (os.path.relpath(zp, REPO), n, k))
    check("zip 내부 키 0 (멤버 %d개)" % nz, not zhits, "; ".join(zhits[:5]))
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "leakscan.py")],
                       cwd=REPO, capture_output=True, text=True)
    check("git 추적·스테이징 파일 키 0", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:])

    say("\n■ 결과: 실패 %d건%s" % (len(fails), (" — " + ", ".join(fails)) if fails else ""))
    with open(os.path.join(MAN, "verify7.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
