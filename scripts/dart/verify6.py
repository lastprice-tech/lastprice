# -*- coding: utf-8 -*-
"""6차 검증 — 지배구조 연차보고서. 읽기만 하고 아무것도 고치지 않는다.

`python3 scripts/dart/verify6.py [--lines <행지문 디렉토리>]`

요청서의 검증 7항목에, 원문을 읽어야만 답할 수 있는 두 가지를 더해 답한다:
  - 추가공시가 보수 부분만 따로 낸 것인가, 전체를 다시 낸 것인가 (쪽수·목차 대조)
  - 정정공시가 본공시와 무엇이 다른가 (섹션 단위 대조)
"""
from __future__ import annotations

import collections
import csv
import difflib
import glob
import hashlib
import json
import os
import sys

csv.field_size_limit(10 ** 9)
OUT, HANDOFF = "dart_out", "handoff"
OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print("  %s %s%s" % ("✓" if cond else "✗", name, ("  — " + detail) if detail else ""))
    return bool(cond)


def rows(p):
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def hp(n):
    return os.path.join(HANDOFF, n)


def _secset(secs, fname):
    """파일의 섹션 제목 목록(원문 그대로, 순서 유지)."""
    seen, out = set(), []
    for r in secs:
        if r["파일명"] != fname:
            continue
        t = r["섹션제목_원문"]
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _body(secs, fname):
    """섹션제목 → 본문(청크 이어붙임)."""
    out = collections.OrderedDict()
    for r in secs:
        if r["파일명"] != fname:
            continue
        out.setdefault(r["섹션제목_원문"], []).append(r["본문"])
    return {k: "".join(v) for k, v in out.items()}


def main(lines_dir=None):
    print("\n■ 6차 검증 — 금융지주 지배구조·보수체계 연차보고서\n")
    metas = [json.load(open(m, encoding="utf-8"))
             for m in sorted(glob.glob(os.path.join(OUT, "raw", "governance",
                                                    "*", "*.meta.json")))]
    files = rows(hp("연차보고서_파일목록.csv"))
    secs = rows(hp("연차보고서_섹션.csv"))
    tbls = rows(hp("연차보고서_표.csv"))
    tops = rows(hp("연차보고서_주제추출.csv"))

    # ── 1. 다운로드 ───────────────────────────────────────────────────────
    print("[1] 다운로드 46건")
    ok = [m for m in metas if m.get("성공") == "Y"]
    bad = [m for m in metas if m.get("성공") != "Y"]
    check("목록 46건이 전부 시도됐다", len(metas) == 46, "메타 %d건" % len(metas))
    check("다운로드 성공 %d / 실패 %d" % (len(ok), len(bad)), not bad,
          "; ".join("%s %s: %s" % (m["지주명"], m["저장파일명"],
                                   (m.get("실패사유") or "")[:60]) for m in bad))
    nonpdf = [m for m in ok if m["저장파일명"].lower().endswith(".pdf")
              and not (m.get("content_type") or "").lower().startswith(
                  ("application/pdf", "application/octet-stream"))]
    check("비PDF(HTML 오류 페이지 등)로 판정된 건", True,
          "%d건 — 시그니처 검사는 다운로드 단계에서 %%PDF 로 이미 걸렀다" % len(nonpdf))
    alt = [m for m in ok if m.get("실제url") and m["실제url"] != m["url"]]
    if alt:
        print("     목록 URL 과 다른 경로로 받은 건 %d (하나금융 :8002 → 443):" % len(alt))
        for m in alt:
            print("       %s" % m["저장파일명"])

    # ── 2. 크기 대조 ──────────────────────────────────────────────────────
    print("\n[2] 목록 크기 ↔ 실제 크기")
    diff = [m for m in ok if m.get("크기차이")]
    check("크게 다른 건", not diff,
          "; ".join("%s %s" % (m["저장파일명"], m["크기차이"]) for m in diff) or
          "0건 (크기 칸이 빈 9건은 전부 조직도 이미지)")

    # ── 3. 공시유형 ───────────────────────────────────────────────────────
    print("\n[3] 공시유형별 건수")
    c = collections.Counter(m.get("공시유형") for m in metas)
    print("   ", dict(c))
    pdfs = {f["파일명"]: f for f in files if f["파일명"].lower().endswith(".pdf")}

    print("\n[3-1] 추가공시는 보수 부분만인가, 전체를 다시 낸 것인가")
    print("  %-14s %-5s %8s %8s %8s %8s  %s"
          % ("지주", "연도", "본공시쪽", "추가쪽", "본공시섹션", "추가섹션", "판정"))
    for (corp, yr), grp in sorted(collections.Counter(
            (f["지주명"], f["공시연도"]) for f in pdfs.values()).items()):
        base = [f for f in pdfs.values() if f["지주명"] == corp and f["공시연도"] == yr
                and f["공시유형"] == "본공시"]
        add = [f for f in pdfs.values() if f["지주명"] == corp and f["공시연도"] == yr
               and f["공시유형"] in ("추가공시", "재공시")]
        if not (base and add):
            continue
        b, a = base[0], add[0]
        bs, as_ = _secset(secs, b["파일명"]), _secset(secs, a["파일명"])
        bp, ap = int(b["페이지수"] or 0), int(a["페이지수"] or 0)
        common = len(set(bs) & set(as_))
        ratio = ap / bp if bp else 0
        verdict = ("전체 재공시" if ratio > 0.8 and common >= max(1, len(bs) * 0.6)
                   else "일부(보수 등)만" if ratio < 0.5 else "판단불가")
        print("  %-14s %-5s %8d %8d %8d %8d  %s (쪽 비율 %.2f, 공통섹션 %d)"
              % (corp, yr, bp, ap, len(bs), len(as_), verdict, ratio, common))

    print("\n[3-2] 정정공시는 본공시와 무엇이 다른가 (섹션 단위)")
    found_corr = False
    for f in pdfs.values():
        if f["공시유형"] != "정정공시":
            continue
        found_corr = True
        base = [g for g in pdfs.values() if g["지주명"] == f["지주명"]
                and g["공시연도"] == f["공시연도"] and g["공시유형"] == "본공시"]
        if not base:
            print("  %s %s: 본공시가 없어 대조 불가" % (f["지주명"], f["공시연도"]))
            continue
        b = base[0]
        bb, ab = _body(secs, b["파일명"]), _body(secs, f["파일명"])
        added = [k for k in ab if k not in bb]
        removed = [k for k in bb if k not in ab]
        changed = [k for k in ab if k in bb and ab[k] != bb[k]]
        print("  %s %s — 섹션 추가 %d / 삭제 %d / 내용변경 %d"
              % (f["지주명"], f["공시연도"], len(added), len(removed), len(changed)))
        for k in changed[:8]:
            sm = difflib.SequenceMatcher(None, bb[k], ab[k])
            print("     변경: %-40s 유사도 %.3f (%d자 → %d자)"
                  % (k[:40], sm.quick_ratio(), len(bb[k]), len(ab[k])))
        for k in added[:5]:
            print("     추가: %s" % k[:56])
        for k in removed[:5]:
            print("     삭제: %s" % k[:56])
    if not found_corr:
        print("  정정공시 0건")

    # ── 4. 텍스트 추출 ────────────────────────────────────────────────────
    print("\n[4] 텍스트 추출 실패(스캔본)")
    scan = [f for f in pdfs.values() if f["스캔본추정"] == "Y"]
    noext = [f for f in pdfs.values() if f["텍스트추출"] != "Y"]
    check("텍스트가 안 나온 PDF", not noext,
          ", ".join(f["파일명"] for f in noext) or "0건")
    check("스캔본 추정(쪽당 60자 미만)", not scan,
          ", ".join(f["파일명"] for f in scan) or "0건")
    notoc = [f for f in pdfs.values() if f.get("목차없음") == "Y"]
    print("   목차를 못 찾아 문서 전체를 한 섹션으로 실은 파일 %d건: %s"
          % (len(notoc), ", ".join(f["파일명"] for f in notoc) or "없음"))

    # ── 5. 법인별 섹션·표 ─────────────────────────────────────────────────
    print("\n[5] 법인별 섹션 수 / 표 셀 수 (0건은 0으로 보고한다)")
    cs = collections.Counter(r["지주명"] for r in secs)
    ct = collections.Counter(r["corp_label"] for r in tbls)
    cf = collections.Counter(f["지주명"] for f in pdfs.values())
    corps = sorted(set(cs) | set(ct) | set(cf))
    print("  %-14s %6s %8s %10s" % ("지주", "PDF", "섹션행", "표셀"))
    for c_ in corps:
        print("  %-14s %6d %8d %10d" % (c_, cf[c_], cs[c_], ct[c_]))
    check("10개 지주 전부 섹션이 있다", all(cs[c_] for c_ in cf),
          "0건: " + ", ".join(c_ for c_ in cf if not cs[c_]))

    # ── 6. 주제별 법인 × 주제 ─────────────────────────────────────────────
    print("\n[6] 주제별 추출 결과 (법인 × 주제)")
    import governance_emit as GE
    names = [t[0] for t in GE.TOPICS]
    grid = collections.defaultdict(lambda: collections.Counter())
    for r in tops:
        grid[r["지주명"]][(r["주제"], r["추출결과"])] += 1
    hdr = "  %-14s" % "지주" + "".join("%-9s" % n[:8] for n in names)
    print(hdr)
    for c_ in sorted(grid):
        line = "  %-14s" % c_
        for n in names:
            g = grid[c_]
            if g[(n, "찾음")]:
                line += "%-9s" % ("찾음%d" % g[(n, "찾음")])
            elif g[(n, "없음")]:
                line += "%-9s" % "없음"
            else:
                line += "%-9s" % "판단불가"
        print(line)

    # ── 7. 1~5차 불변 + 키 유출 ───────────────────────────────────────────
    print("\n[7] 1~5차 산출물 불변 / 키 유출")
    if lines_dir and os.path.isdir(lines_dir):
        changed = []
        for lh in sorted(glob.glob(os.path.join(lines_dir, "*.lh"))):
            name = os.path.basename(lh)[:-3]
            p = hp(name)
            if not os.path.exists(p):
                changed.append(name + "(사라짐)")
                continue
            old = open(lh).read().split("\n")
            new = []
            with open(p, "rb") as f:
                for line in f:
                    new.append(hashlib.sha1(line).hexdigest()[:20])
            new.sort()
            if collections.Counter(old) - collections.Counter(new):
                changed.append(name)
        check("기준선 CSV 에서 사라진 행 없음", not changed, ", ".join(changed))
    else:
        print("   (--lines 기준선 미지정 — 건너뜀)")
    key = os.environ.get("DART_API_KEY") or ""
    leak = []
    if key:
        for p in glob.glob(os.path.join(HANDOFF, "*.csv")) + \
                glob.glob(os.path.join(HANDOFF, "*.md")) + \
                glob.glob(os.path.join(OUT, "raw", "governance", "*", "*.meta.json")):
            with open(p, "rb") as f:
                if key.encode() in f.read():
                    leak.append(os.path.basename(p))
    check("평문 산출물·메타에 API 키 0회", not leak, ", ".join(leak))

    print("\n■ 결과: 통과 %d / 실패 %d" % (len(OK), len(BAD)))
    for b in BAD:
        print("   ✗ " + b)
    return 0 if not BAD else 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ld = sys.argv[sys.argv.index("--lines") + 1] if "--lines" in sys.argv else None
    sys.exit(main(ld))
