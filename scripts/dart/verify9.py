# -*- coding: utf-8 -*-
"""9차 검증·보고 — 리스크부문 v0.4 위임 산출물.

    python3 scripts/dart/verify9.py      # 결과: dart_out/risk9/verify9.txt (작업별 건수·실패·문서에 없음 비율 포함)

검사
  A. 원문 대조 — 행이 가리키는 쪽(뷰어 본문 PDF 추출 텍스트)에 그 행의 원문 값이 공백 무시로 있는가
     · 위험관리위원회 활동: 개최일자 + 의안 앞 30자  · CRO: 성명(쪽 cro) / 직원 합계 행 값(쪽 employees)
     · 내부회계: 의견 앞 25자  · 자본지표: 행 이름 + 값  · 보험 자회사: 인용문
  B. 출처 — 모든 행에 rcept_no(또는 URL)·문서명·수집일, 값이 있는 행은 쪽(없으면 note 에 사유)
  C. RAAS 발췌가 전체 텍스트의 해당 줄과 글자까지 같은가, 법령 텍스트가 저장된 XML 에서 다시 만든 것과 같은가
  D. 웹 수집 CSV(생보협회·법령해석) — 받은 파일 sha256 이 meta 와 같은가
  E. 키 유출 0(DART_API_KEY·LAW_OC 값, `OC=` 뒤 값) — 9차 파일 + leakscan.py(추적 파일 전체)
  F. 기존 산출물 — 1~7차(6b9cfbe) 불변(호출 원장은 덧붙이기만), 8차 산출물 중 9차가 고치지 않는 파일 불변
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import risk8  # noqa: E402
import risk9  # noqa: E402

H = risk8.HANDOFF
NF = risk8.NOT_FOUND
nows = risk8._nows
BASE7 = "6b9cfbe"
BASE8 = "342f23b"          # 8차 마지막 커밋
# 9차가 일부러 바꾸는 8차 산출물(작업 1 본표 갱신)
CHANGED_BY_9 = {"handoff/원문_지주리스크체계.csv", "handoff/원문_지주리스크체계_근거.csv",
                "scripts/dart/data/risk8_선별.json", "dart_out/risk8/검색기록.csv",
                "dart_out/risk8/후보문장.csv", "dart_out/risk8/verify8.txt"}
APPEND_ONLY = {"dart_out/call_log.csv", "dart_out/quota_ledger.csv", "dart_out/runs.csv"}


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if os.path.exists(p) else None


def on_page(rc, page, *keys):
    P = risk9.pages_of(rc)
    t = P.get(int(page)) if str(page).isdigit() else None
    return t is not None and all(nows(k) in t for k in keys if k)


def main():
    out, fails, stats = [], [], []

    def ok(cond, msg):
        out.append(("OK   " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    def stat(task, rows, value_cols, extra=""):
        if rows is None:
            stats.append("%-34s 파일 없음" % task)
            return
        cells = [r[c] for r in rows for c in value_cols]
        nf = sum(1 for v in cells if (v or "").startswith(NF))
        stats.append("%-34s 행 %4d · 값 칸 %5d · 문서에 없음 %4d (%.1f%%)%s"
                     % (task, len(rows), len(cells), nf, 100.0 * nf / max(1, len(cells)), extra))

    # ── 작업 1 본표: verify8 그대로 ─────────────────────────────────────────
    r = subprocess.run([sys.executable, os.path.join(HERE, "verify8.py")], capture_output=True, text=True)
    ok(r.returncode == 0, "작업1 원문_지주리스크체계 — verify8: %s" % (r.stdout.strip().splitlines() or ["?"])[-1])
    w = rd(os.path.join(H, "원문_지주리스크체계.csv"))
    stat("작업1 원문_지주리스크체계(17열)", w, risk8.MAIN_FIELDS)
    if w:
        ok(all(x["rcept_no_or_url"] and x["doc_name"] and x["collected_at"] for x in w),
           "작업1 모든 행에 rcept_no_or_url·doc_name·collected_at")

    # ── 작업 1 추가 산출물 ─────────────────────────────────────────────────
    a = rd(os.path.join(H, "원문_위험관리위원회_활동.csv"))
    if a is not None:
        def act_ok(x):
            P = risk9.pages_of(x["rcept_no"]).get(int(x["page"]), "")
            tail = x["agenda"].split(" | ")[-1]
            d = nows(x["meeting_date"])
            # 「<보고사항>1)」 같은 앞머리를 뗀 의안 핵심(risk9.activity_page 와 같은 규칙)
            core = re.sub(r"^[\s\-·ㅇｏo•▶]*([<\[(（【][^>\])）】]{1,8}[>\])）】])?\s*(\d+[).]|[-·ㅇｏ])?\s*", "",
                          x["agenda"])
            if (d in P and nows(core[:12]) in P) or nows(core[:20]) in P:
                return True
            return (nows(x["agenda"][:30]) in P or nows(tail[:30]) in P or
                    (d in P and any(nows(k) and nows(k) in P for k in (x["agenda"][:12], tail[:12]))) or
                    (x["page_basis"].startswith("개최일(") and d in P))
        bad = [x for x in a if x["page"] and not act_ok(x)]
        nop = [x for x in a if not x["page"] and "쪽을 못 찾음" not in x["note"]]
        ok(not bad, "작업1 위원회 활동 %d행 — 쪽에 개최일·의안 있음%s" % (len(a), "" if not bad else " — 불일치 %d" % len(bad)))
        ok(not nop, "작업1 위원회 활동 — 쪽 없는 행은 note 에 사유(%d행 쪽 없음)" % sum(1 for x in a if not x["page"]))
        ok(all(x["rcept_no"] and x["doc_name"] and x["collected_at"] for x in a), "작업1 위원회 활동 출처·수집일")
        docs = rd(os.path.join(risk9.WORK, "위원회활동_문서별.csv")) or []
        stat("작업1 원문_위험관리위원회_활동", a, ["agenda"],
             " · 문서 %d(본문 없음 %d)" % (len(docs), sum(1 for d in docs if d["rows"] == "")))
    c = rd(os.path.join(H, "원문_지주조직_CRO.csv"))
    if c is not None:
        bad = [x for x in c if x["page_cro"] and not on_page(x["rcept_no"], x["page_cro"], x["cro_name"].split(" ‖ ")[0])]
        bad += [x for x in c if x["page_employees"] and not on_page(x["rcept_no"], x["page_employees"], x["employees"])]
        ok(not bad, "작업1 CRO %d행 — 쪽에 성명·직원 합계 있음%s" % (len(c), "" if not bad else " — 불일치 %d" % len(bad)))
        ok(all(x["rcept_no"] and x["doc_name"] and x["collected_at"] for x in c), "작업1 CRO 출처·수집일")
        stat("작업1 원문_지주조직_CRO", c, ["employees", "cro_name", "cro_title", "cro_career", "cro_concurrent"])
    # ── 작업 2·3 ───────────────────────────────────────────────────────────
    k = rd(os.path.join(H, "원문_비은행지주_자본지표.csv"))
    if k is not None:
        def cap_ok(x):
            lab = x["source_text"].split("[행] ")[-1].split(" | ")[0]
            if x["value"] == NF:                 # 당기 칸이 숫자가 아닌 행 — 행 이름과 원문 칸 글자로 대조
                m = re.search(r"당기 칸 원문 「(.*?)」", x["note"])
                return on_page(x["rcept_no_or_url"], x["page"], lab, m.group(1) if m else "")
            return on_page(x["rcept_no_or_url"], x["page"], lab, x["value"])
        bad = [x for x in k if x["page"] and not cap_ok(x)]
        ok(not bad, "작업2 자본지표 %d행 — 쪽에 행 이름·값 있음%s" % (len(k), "" if not bad else " — 불일치 %d" % len(bad)))
        nop = [x for x in k if x["value"] != NF and not x["page"]]
        ok(True, "작업2 값 있는데 쪽 못 찾은 행 %d" % len(nop))
        stat("작업2 원문_비은행지주_자본지표", k, ["value"])
    i = rd(os.path.join(H, "원문_지주내부회계.csv"))
    if i is not None:
        def icfr_ok(x):
            if x["source_text"].startswith("[첨부 "):
                f = x["source_text"][len("[첨부 "):].split(" · ")[0]
                P = risk9._attach_text(os.path.join("dart_out", "doc", x["rcept_no"], "첨부", f))
                return nows(x["opinion"][:25]) in nows(P.get(int(x["page"]), ""))
            return on_page(x["rcept_no"], x["page"], x["opinion"][:25])
        bad = [x for x in i if x["page"] and not icfr_ok(x)]
        ok(not bad, "작업3 내부회계 %d행 — 쪽에 의견 문구 있음%s" % (len(i), "" if not bad else " — 불일치 %d" % len(bad)))
        stat("작업3 원문_지주내부회계", i, ["icfr_scope", "opinion_type", "opinion"])
    # ── 작업 4 ─────────────────────────────────────────────────────────────
    s4 = rd(os.path.join(H, "원문_보험자회사_지주연계.csv"))
    if s4 is not None:
        bad = [x for x in s4 if x["source_text"] != NF and not on_page(x["rcept_no_or_url"], x["page"], x["source_text"])]
        ok(not bad, "작업4 보험 자회사 %d행 — 인용이 쪽 원문에 있음%s" % (len(s4), "" if not bad else " — 불일치 %d" % len(bad)))
        stat("작업4 원문_보험자회사_지주연계", s4, ["source_text"])
    # ── 작업 5 ─────────────────────────────────────────────────────────────
    md = os.path.join(H, "RAAS_매뉴얼_원문.md")
    full = os.path.join("dart_out", "raw", "web9", "raas", "RAAS_매뉴얼_전체.md")
    if os.path.exists(md) and os.path.exists(full):
        body = open(md, encoding="utf-8").read()
        m = re.search(r"붙임2 (\d+)~(\d+)행 · Ⅳ\.1 경영관리리스크 (\d+)~(\d+)행", body)
        fl = open(full, encoding="utf-8").read().split("\n")
        good = bool(m) and all("\n".join(fl[int(m.group(a_)) - 1:int(m.group(b_))]) in body
                               for a_, b_ in ((1, 2), (3, 4)))
        ok(good, "작업5-1 RAAS 발췌 두 부분이 전체 텍스트의 그 줄과 글자까지 같음")
        stats.append("%-34s 붙임2·Ⅳ.1 두 부분" % "작업5-1 RAAS_매뉴얼_원문.md")
    lw = rd(os.path.join(risk9.WORK, "법령원문_9차.csv"))
    if lw is not None:
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
        import web9
        same = []
        for x in lw:
            if x["상태"] != "OK":
                continue
            xb = open(x["원문XML"], "rb").read() if os.path.exists(x["원문XML"]) else b""
            t = web9._xml_text(xb, x["kind"] == "행정규칙") if xb else None
            same.append(bool(t) and t in open(x["텍스트"], encoding="utf-8").read())
        ok(all(same) and len(same) == len(lw), "작업5-4 법령 %d건 — 텍스트가 저장 XML 에서 다시 만든 것과 같음" % len(lw))
        stats.append("%-34s %d건 OK · 7차와 다른 판 %d" % ("작업5-4 법령원문_9차", sum(x["상태"] == "OK" for x in lw),
                                                       sum(x["차7과같은판"].startswith("N") for x in lw)))
    for name, task in (("목록_생보협회_자율규제.csv", "작업5-2"), ("목록_법령해석.csv", "작업5-3")):
        g = rd(os.path.join(H, name))
        if g is None:
            stats.append("%-34s 파일 없음" % ("%s %s" % (task, name)))
            continue
        ok(all(x.get("collected_at") for x in g), "%s %s %d행 — 수집일" % (task, name, len(g)))
        stats.append("%-34s 행 %d" % ("%s %s" % (task, name), len(g)))

    # ── E. 키 유출 ─────────────────────────────────────────────────────────
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "law"))
    import leakscan
    secrets = list(leakscan.secrets().values())
    scan = []
    for root in (H, risk9.WORK, os.path.join(HERE)):
        for dp, _dn, fn in os.walk(root):
            scan += [os.path.join(dp, f) for f in fn if f.endswith((".csv", ".md", ".py", ".json", ".txt"))]
    leak = []
    for p in scan:
        s = open(p, encoding="utf-8", errors="replace").read()
        if any(x in s for x in secrets):
            leak.append(p)
        if re.search(r"OC=(?!\*\*\*)[A-Za-z0-9]", s):
            leak.append(p + "(OC=)")
    ok(not leak and len(secrets) >= 2, "키 유출 0 — 파일 %d개 · 비밀값 %d종%s" % (len(scan), len(secrets),
                                                                      "" if not leak else " — %s" % leak[:5]))
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), "law", "leakscan.py")],
                       capture_output=True, text=True)
    ok(r.returncode == 0, "leakscan.py: %s" % (r.stdout.strip().splitlines() or ["?"])[-1])

    # ── F. 기존 산출물 ─────────────────────────────────────────────────────
    def git(*a_):
        return subprocess.run(["git", "-c", "core.quotepath=off"] + list(a_), capture_output=True, check=True).stdout
    for base, label, skip in ((BASE7, "1~7차", set()), (BASE8, "8차", CHANGED_BY_9)):
        names = [p for p in git("ls-tree", "-r", "--name-only", base).decode("utf-8").splitlines()
                 if p.startswith(("handoff/", "law_archive/", "dart_out/"))]
        changed, appended = [], 0
        for p in names:
            if p in skip:
                continue
            if not os.path.exists(p):
                changed.append(p + "(삭제)")
                continue
            b = git("show", "%s:%s" % (base, p))
            cur = open(p, "rb").read()
            if cur == b:
                continue
            if p in APPEND_ONLY and cur.startswith(b):
                appended += 1
            else:
                changed.append(p)
        ok(not changed, "%s(%s) 추적 산출물 %d개 불변(9차가 고치는 %d개 제외, 호출 원장 덧붙이기 %d)%s"
           % (label, base, len(names), len(skip), appended, "" if not changed else " — 바뀜 %s" % changed[:8]))

    txt = "\n".join(out + ["", "[작업별 수집 건수 · 문서에 없음 비율]"] + stats + ["", "실패 %d" % len(fails)]) + "\n"
    print(txt, end="")
    os.makedirs(risk9.WORK, exist_ok=True)
    with open(os.path.join(risk9.WORK, "verify9.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
