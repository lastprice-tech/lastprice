# -*- coding: utf-8 -*-
"""8차 검증 — 원문_지주리스크체계.csv · _근거.csv.

    python3 scripts/dart/verify8.py        # 결과를 dart_out/risk8/verify8.txt 에도 남긴다

1. 인용마다 그 쪽 원문에 글자 그대로 있는가(공백·줄바꿈만 무시). 텍스트·원본 PDF sha256 도 대조.
2. 항목 칸에는 인용(`[p.N] 원문`, ` ‖ `로 연결)이나 「문서에 없음」만 있는가 — 요약·해석 섞임 금지.
   칸의 인용은 근거 파일의 같은 (문서·항목·쪽·문구)와 1:1 로 맞아야 한다.
3. 「문서에 없음」마다 근거 파일에 검색 범위·어휘·후보 수 기록이 있는가.
4. 행 수 — 8개사 × (연차보고서·사업보고서·경영공시) + 전환 증권신고서 4건. 빠진 행과 사유.
5. source_text·page 가 항목 칸의 인용과 일치하는가.
6. 키 유출 0 — DART_API_KEY·LAW_OC 값(7차 leakscan 과 같이 환경변수 → .env 에서 읽는다.
   값은 코드에 쓰지 않는다), 가려지지 않은 `OC=`. 추적 파일 전체는 7차 leakscan.py 로도 본다.
7. 1~7차 추적 산출물(handoff/·law_archive/·dart_out/)이 바뀌지 않았는가 — 7차 마지막 커밋
   (BASELINE) 기준. 스크립트는 산출물이 아니라 범위 밖. 호출 원장 세 개는 뒤에 덧붙이기만
   했는지(앞부분이 그대로인지)만 본다.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import risk8  # noqa: E402

BASELINE = "6b9cfbe"          # 7차 마지막 커밋
OUTPUT_DIRS = ("handoff/", "law_archive/", "dart_out/")
APPEND_ONLY = {"dart_out/call_log.csv", "dart_out/quota_ledger.csv", "dart_out/runs.csv"}
WIDE = os.path.join(risk8.HANDOFF, "원문_지주리스크체계.csv")
LONG = os.path.join(risk8.HANDOFF, "원문_지주리스크체계_근거.csv")

nows = risk8._nows


def _read(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    out, fails = [], []

    def ok(cond, msg):
        out.append(("OK   " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    idx = {r["doc_id"]: r for r in _read(os.path.join(risk8.WORK, "텍스트목록.csv"))}
    wide, long_ = _read(WIDE), _read(LONG)
    pages = {}

    def page_text(doc_id, n):
        if doc_id not in pages:
            s = open(idx[doc_id]["텍스트"], encoding="utf-8").read()
            pages[doc_id] = {k: nows(v) for k, v in risk8.re_split_pages(s)}
        return pages[doc_id].get(n)

    # 1. 인용 ↔ 원문 쪽
    quotes = [r for r in long_ if r["quote"] != risk8.NOT_FOUND]
    miss = []
    for r in quotes:
        t = page_text(r["doc_id"], int(r["page"]))
        if t is None or nows(r["quote"]) not in t:
            miss.append("%s %s p.%s %s" % (r["doc_id"], r["field"], r["page"], r["quote"][:40]))
    ok(not miss, "1. 인용 %d개가 모두 해당 쪽 원문에 있음(공백 무시)%s"
       % (len(quotes), "" if not miss else " — 불일치 %d: %s" % (len(miss), miss[:5])))
    # 1a. 사업보고서 인용은 「실제 위험관리 절」(risk8.BIZ_SCOPE) 안에 있어야 한다
    out_scope, scoped = [], {}
    for r in quotes:
        if r["doc_kind"] != "사업보고서":
            continue
        if r["doc_id"] not in scoped:
            s = open(idx[r["doc_id"]]["텍스트"], encoding="utf-8").read()
            _sec, sp = risk8._scope(idx[r["doc_id"]], risk8.re_split_pages(s))
            scoped[r["doc_id"]] = {n: nows(t) for n, t in sp}
        t = scoped[r["doc_id"]].get(int(r["page"]))
        if t is None or nows(r["quote"]) not in t:
            out_scope.append("%s %s p.%s" % (r["doc_id"], r["field"], r["page"]))
    ok(not out_scope, "1a. 사업보고서 인용 %d개가 모두 위험관리 절 범위 안%s"
       % (sum(1 for r in quotes if r["doc_kind"] == "사업보고서"),
          "" if not out_scope else " — 범위 밖 %s" % out_scope[:5]))
    bad_sha = []
    for d in sorted({r["doc_id"] for r in wide}):
        m = idx[d]
        if _sha(m["텍스트"]) != m["텍스트sha256"]:
            bad_sha.append(d + " 텍스트")
        if os.path.exists(m["원본"]) and _sha(m["원본"]) != m["원본sha256"]:
            bad_sha.append(d + " 원본")
        elif not os.path.exists(m["원본"]):
            out.append("     (참고) 원본 PDF 가 이 작업 트리에 없음 — %s" % m["원본"])
    ok(not bad_sha, "1b. 인용 문서의 텍스트·원본 sha256 이 텍스트목록.csv 와 같음%s"
       % ("" if not bad_sha else " — %s" % bad_sha))

    # 2. 항목 칸 형식 + 근거와 1:1
    seg_re = re.compile(r"^\[p\.(\d+)\] (.+)$", re.S)
    by_key = {}
    for r in quotes:
        by_key.setdefault((r["doc_id"], r["field"]), []).append((int(r["page"]), r["quote"]))
    bad_cell = []
    for w in wide:
        for f in risk8.MAIN_FIELDS:
            v = w[f]
            if v == risk8.NOT_FOUND:
                if by_key.get((w["doc_id"], f)):
                    bad_cell.append("%s %s: 칸은 문서에 없음인데 근거 인용 있음" % (w["doc_id"], f))
                continue
            segs = v.split(risk8.SEP)
            got = []
            for s in segs:
                m = seg_re.match(s)
                if not m:
                    bad_cell.append("%s %s: 형식 아님 %r" % (w["doc_id"], f, s[:40]))
                    continue
                got.append((int(m.group(1)), m.group(2)))
            if got != by_key.get((w["doc_id"], f), []):
                bad_cell.append("%s %s: 근거 파일과 다름" % (w["doc_id"], f))
    ok(not bad_cell, "2. 항목 칸 %d개가 인용 또는 「문서에 없음」뿐이고 근거와 1:1%s"
       % (len(wide) * len(risk8.MAIN_FIELDS), "" if not bad_cell else " — %s" % bad_cell[:5]))

    # 3. 문서에 없음 ↔ 검색 기록
    nf = [(w["doc_id"], f) for w in wide for f in risk8.MAIN_FIELDS if w[f] == risk8.NOT_FOUND]
    logged = {(r["doc_id"], r["field"]) for r in long_ if r["quote"] == risk8.NOT_FOUND and r["검색"].strip()}
    lack = [x for x in nf if x not in logged]
    ok(not lack, "3. 「문서에 없음」 %d칸 모두 검색 범위·어휘·후보 수 기록 있음%s"
       % (len(nf), "" if not lack else " — 없음 %s" % lack[:5]))

    # 4. 행
    want = [(lab, k) for k in ("연차보고서", "사업보고서", "경영공시") for lab in risk8.LABELS]
    have = {(w["corp_label"], w["doc_kind"]) for w in wide if w["doc_kind"] != "증권신고서"}
    missing = [x for x in want if x not in have]
    conv = {w["doc_id"] for w in wide if w["doc_kind"] == "증권신고서"}
    conv_missing = [d for d in risk8.CONVERSION_ROWS if d not in conv]
    dup = len(wide) - len({w["doc_id"] for w in wide})
    ok(not missing and not conv_missing and not dup,
       "4. 행 %d개 = 8개사×3문서 %d + 전환 증권신고서 %d, 중복 %d%s"
       % (len(wide), len(want) - len(missing), len(conv), dup,
          "" if not (missing or conv_missing) else " — 빠짐 %s %s" % (missing, conv_missing)))

    # 5. source_text·page
    bad_src = []
    for w in wide:
        rs = [r for r in quotes if r["doc_id"] == w["doc_id"]]
        exp = risk8.SEP.join("[%s p.%s] %s" % (r["field"], r["page"], r["quote"]) for r in rs) or risk8.NOT_FOUND
        pg = ", ".join(str(p) for p in sorted({int(r["page"]) for r in rs}))
        if w["source_text"] != exp or w["page"] != pg:
            bad_src.append(w["doc_id"])
    ok(not bad_src, "5. source_text·page 가 인용과 일치%s" % ("" if not bad_src else " — %s" % bad_src))

    # 6. 키 유출
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
    import leakscan
    found = leakscan.secrets()
    ok("LAW_OC" in found and "DART_API_KEY" in found,
       "6a. 검사할 비밀값을 읽음(%s)" % ", ".join(sorted(found)) if found else "6a. 비밀값을 못 읽음")
    secrets = list(found.values())
    scan = [WIDE, LONG, os.path.join(HERE, "risk8.py"), os.path.abspath(__file__),
            os.path.join(HERE, "data", "risk8_선별.json")]
    scan += [os.path.join(risk8.WORK, f) for f in os.listdir(risk8.WORK) if f.endswith((".csv", ".txt"))]
    leak = []
    for p in scan:
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="replace").read()
        if any(k in s for k in secrets):
            leak.append(p + " (키 값)")
        if re.search(r"OC=(?!\*\*\*)", s):
            leak.append(p + " (OC= 노출)")
    ok(not leak, "6b. 8차 파일 키 유출 0 — %d개 파일, 비밀값 %d종 + `OC=` 검사%s"
       % (len(scan), len(secrets), "" if not leak else " — %s" % leak))
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), "law", "leakscan.py")],
                       capture_output=True, text=True)
    ok(r.returncode == 0, "6c. leakscan.py(추적·스테이징 파일 전체): %s"
       % (r.stdout.strip().splitlines() or ["출력 없음"])[-1])

    # 7. 1~7차 산출물 불변
    def git(*a):
        return subprocess.run(["git"] + list(a), capture_output=True, check=True).stdout
    old = [p for p in git("-c", "core.quotepath=off", "ls-tree", "-r", "--name-only", BASELINE)
           .decode("utf-8").splitlines() if p.startswith(OUTPUT_DIRS)]
    changed, appended = [], []
    for p in old:
        if not os.path.exists(p):
            changed.append(p + " (삭제)")
            continue
        base = git("show", "%s:%s" % (BASELINE, p))
        cur = open(p, "rb").read()
        if cur == base:
            continue
        if p in APPEND_ONLY and cur.startswith(base):
            appended.append(p)
        else:
            changed.append(p)
    ok(not changed, "7. %s 의 추적 파일 %d개 불변(호출 원장 %d개는 덧붙이기만)%s"
       % (BASELINE, len(old), len(appended), "" if not changed else " — 바뀜 %s" % changed[:10]))

    out.append("")
    out.append("실패 %d" % len(fails))
    txt = "\n".join(out) + "\n"
    print(txt, end="")
    with open(os.path.join(risk8.WORK, "verify8.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
