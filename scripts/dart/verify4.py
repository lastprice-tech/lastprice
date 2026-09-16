# -*- coding: utf-8 -*-
"""4차 검증 15항목. 읽기만 하고 아무것도 고치지 않는다.

`python3 scripts/dart/verify4.py [--baseline <sha256 파일>]`

가장 중요한 항목은 8번이다 — emit 규칙을 문서 단위로 분기했으므로, 1~3차 CSV 가
한 바이트라도 바뀌면 그 분기가 새는 것이다. 기준선은 변경 전에 떠 둔다:
    sha256sum handoff/*.csv > before.sha256
"""
from __future__ import annotations

import collections
import csv
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config          # noqa: E402
import handoff as H    # noqa: E402

csv.field_size_limit(10 ** 9)
OUT = "dart_out"
HANDOFF = "handoff"
OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print("  %s %s%s" % ("✓" if cond else "✗", name, ("  — " + detail) if detail else ""))
    return cond


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(baseline=None):
    print("\n═══ 4차 검증 ═══\n")

    # ── 1. 겸영·부수업무 ──────────────────────────────────────────────────
    cb = rows(os.path.join(HANDOFF, "겸영부수업무_목록.csv"))
    hit = collections.Counter(r["법인"] for r in cb if r["구분"] != "(없음)")
    zero = sorted({r["법인"] for r in cb if r["구분"] == "(없음)"} - set(hit))
    print("【1】 겸영·부수업무 — 추출 법인 %d곳 / 0건 법인 %d곳 / 총 %d행"
          % (len(hit), len(zero), len(cb)))
    for k, v in hit.most_common():
        print("        %-20s %4d건" % (k, v))
    print("        0건: %s" % ", ".join(zero))
    check("겸영부수업무_목록.csv 가 생성됐다", bool(cb), "%d행" % len(cb))
    nofile = [r for r in cb if r["구분"] == "(없음)" and not r["text_path"]]
    check("0건 법인에도 text_path 가 남아 있다", not nofile,
          "text_path 없는 0건 행 %d" % len(nofile))
    filed = [r for r in cb if (r.get("신고일") or "").strip()]
    check("신고일은 전량 빈칸이다(원문에 기재 없음)", not filed,
          "신고일이 채워진 행 %d — 원문 확인 필요" % len(filed))

    # ── 2. 마이데이터 ────────────────────────────────────────────────────
    md = rows(os.path.join(HANDOFF, "마이데이터_영위업무.csv"))
    yes = sorted({r["법인"] for r in md if r["기재여부"] == "있음"})
    no = sorted({r["법인"] for r in md if r["기재여부"] == "없음"} - set(yes))
    words = collections.Counter()
    for r in md:
        for w in (r.get("근거낱말") or "").split("|"):
            if w:
                words[w] += 1
    print("\n【2】 마이데이터·허가/등록 기재 — 있음 %d곳 / 없음 %d곳" % (len(yes), len(no)))
    print("        있음: %s" % ", ".join(yes))
    print("        없음: %s" % ", ".join(no))
    print("        근거낱말: %s" % dict(words.most_common()))
    check("마이데이터_영위업무.csv 가 생성됐다", bool(md), "%d행" % len(md))

    # ── 3. 혁신금융서비스 ────────────────────────────────────────────────
    inno = [r for r in md if "혁신금융서비스" in (r.get("근거낱말") or "")]
    inno_corp = collections.Counter(r["법인"] for r in inno)
    print("\n【3】 「혁신금융서비스」 — 법인 %d곳 / 총 %d건"
          % (len(inno_corp), len(inno)))
    for k, v in inno_corp.most_common():
        print("        %-20s %4d건" % (k, v))

    # ── 4. 소집공고 본문의 사업목적 ──────────────────────────────────────
    ch = rows(os.path.join(HANDOFF, "정관_사업목적.csv"))
    notice = {r["rcept_no"] for r in ch if r["출처유형"] == "주주총회소집공고"}
    got = {r["rcept_no"] for r in ch
           if r["출처유형"] == "주주총회소집공고" and "문구 있음" in r["조항전문_확보여부"]}
    # 수집은 됐으나 표가 한 줄도 안 잡힌 소집공고까지 세려면 원문 쪽을 봐야 한다.
    disc = H._disclosure_index(OUT)
    collected = {rc for rc, d in disc.items()
                 if config.is_meeting_notice_4cha(d.get("report_nm", ""), d.get("rcept_dt", ""))
                 and os.path.isdir(os.path.join(OUT, "text", rc))}
    miss = sorted(collected - got)
    print("\n【4】 주주총회소집공고 — 수집 %d건 / 본문에서 「사업목적」이 잡힌 건 %d / 안 잡힌 건 %d"
          % (len(collected), len(got), len(miss)))
    if miss:
        print("        안 잡힌 접수번호(웹 첨부 수집 판단용): %s%s"
              % (", ".join(miss[:12]), " …" if len(miss) > 12 else ""))

    # ── 6. 스키마 드리프트 ───────────────────────────────────────────────
    print()
    n4 = os.path.join(HANDOFF, H.NARRATIVE_NAME["4차"])
    t4 = os.path.join(HANDOFF, H.TABLE_NAME["4차"])
    n3 = os.path.join(HANDOFF, H.NARRATIVE_NAME["3차"])
    t3 = os.path.join(HANDOFF, H.TABLE_NAME["3차"])

    def head(p):
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f), None)

    check("4차 서술 CSV 컬럼 == 3차", head(n4) == head(n3) and head(n4) is not None,
          "4차 %s / 3차 %s" % (head(n4), head(n3)))
    check("4차 표 CSV 컬럼 == 3차", head(t4) == head(t3) and head(t4) is not None,
          "4차 %s / 3차 %s" % (head(t4), head(t3)))

    # ── 7. 청크 재조립·셀 길이 ───────────────────────────────────────────
    nr = rows(n4)
    bad_len, chunk = 0, collections.defaultdict(list)
    for r in nr:
        key = (r.get("rcept_no"), r.get("section_index"))
        chunk[key].append(r)
    mism = 0
    for key, rs in chunk.items():
        joined = "".join(x.get("section_text", "") for x in
                         sorted(rs, key=lambda x: int(x.get("chunk_seq") or 0)))
        want = rs[0].get("text_chars") or ""
        if want.isdigit() and len(joined) != int(want):
            mism += 1
    check("4차 서술: 청크 재조립 글자수 == text_chars", mism == 0, "불일치 %d섹션" % mism)
    over = 0
    for r in rows(t4):
        if len(r.get("cell_text") or "") > 32767:
            over += 1
    check("4차 표: 32,767자 초과 셀 0개", over == 0, "초과 %d" % over)

    # ── 8. 1~3차 CSV 바이트 동일 (가장 중요) ─────────────────────────────
    print()
    if baseline and os.path.exists(baseline):
        want = {}
        for line in open(baseline, encoding="utf-8"):
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                want[parts[1].strip()] = parts[0]
        # 4차에서 새로 생기거나 누적으로 갱신되는 파일은 비교 대상이 아니다.
        skip = {os.path.join(HANDOFF, H.NARRATIVE_NAME["4차"]),
                os.path.join(HANDOFF, H.TABLE_NAME["4차"]),
                os.path.join(HANDOFF, "원문_파일목록.csv"),      # 누적 파일
                os.path.join(OUT, "11_원문추출.csv"),            # 4차 규칙으로 재생성
                os.path.join(HANDOFF, "겸영부수업무_목록.csv"),
                os.path.join(HANDOFF, "마이데이터_영위업무.csv"),
                os.path.join(HANDOFF, "정관_사업목적.csv"),
                os.path.join(HANDOFF, "계열사_데이터거래.csv"),
                os.path.join(HANDOFF, "이사회_정보거버넌스_안건.csv"),
                os.path.join(HANDOFF, "고객정보_제재.csv")}
        diff, checked = [], 0
        for path, h in sorted(want.items()):
            if path in skip or not os.path.exists(path):
                continue
            checked += 1
            if sha(path) != h:
                diff.append(path)
        check("1~3차 CSV %d개가 바이트 동일" % checked, not diff,
              "달라진 파일: %s" % diff)
        if diff:
            print("      ↑ emit 의 4차 분기가 1~3차 문서까지 건드렸다는 뜻이다. 즉시 원인을 찾을 것.")
    else:
        print("  · 기준선 파일이 없어 8번(바이트 동일)은 건너뜀 — %s" % baseline)

    # ── 9. 배치 라우팅 ───────────────────────────────────────────────────
    print()
    db = H.doc_batch_map(OUT)
    leak3 = [r for r in rows(n3) if db.get(r.get("rcept_no")) == "4차"]
    leak4 = [r for r in nr if db.get(r.get("rcept_no")) != "4차"]
    check("4차 행이 3차 서술 CSV 로 새지 않았다", not leak3, "샌 행 %d" % len(leak3))
    check("4차 서술 CSV 에 4차 아닌 문서가 없다", not leak4, "이물 %d행" % len(leak4))
    noname = [b for b in H.BATCHES if b not in H.NARRATIVE_NAME or b not in H.TABLE_NAME]
    check("BATCHES 의 모든 차수에 출력 파일명이 있다", not noname, str(noname))

    # ── 10. AI 제외 고정 ─────────────────────────────────────────────────
    check('TABLE_KEYWORDS_4CHA 에 "AI" 가 없다', "AI" not in config.TABLE_KEYWORDS_4CHA)

    # ── 11. 안건결과 분포 ────────────────────────────────────────────────
    print()
    NEG = ("부결", "보류", "재논의", "철회")
    for fn, col in (("이사회_정보거버넌스_안건.csv", "안건_원문"),
                    ("계열사_데이터거래.csv", "거래_원문")):
        rs = rows(os.path.join(HANDOFF, fn))
        dist = collections.Counter(r["안건결과"] for r in rs)
        neg = [r for r in rs if r["안건결과"] in NEG]
        print("【11】 %s — %d행 / 결과 %s / 부결·보류·재논의·철회 %d건"
              % (fn, len(rs), dict(dist.most_common()), len(neg)))
        for r in neg[:20]:
            print("        ✦ [%s %s] %s" % (r["법인"], r["안건결과"], r[col][:150]))

    # ── 12. 20-F 트랩 ────────────────────────────────────────────────────
    print()
    trap = [rc for rc, d in disc.items() if "해외증권거래소" in (d.get("report_nm") or "")]
    inb = [rc for rc in trap if rc in db]
    check("20-F 국내신고 %d건이 4차 대상에 없다" % len(trap), not inb, "섞인 건 %r" % inb[:5])

    # ── 13. 지주별 정보거버넌스 처리 방식 ────────────────────────────────
    gov = rows(os.path.join(HANDOFF, "이사회_정보거버넌스_안건.csv"))
    by = collections.defaultdict(lambda: collections.Counter())
    for r in gov:
        kind = "지침 제·개정 의결" if ("지침" in r["안건_원문"]
                                   and r["안건결과"] in ("가결", "결의", "원안가결",
                                                    "수정가결", "조건부")) else (
            "현황 보고" if r["안건결과"] in ("보고", "이의 없음", "이의없음") else "기타")
        by[r["법인"]][kind] += 1
    print("\n【13】 법인별 정보거버넌스 안건 처리 방식")
    for lab in sorted(by):
        print("        %-20s %s" % (lab, dict(by[lab].most_common())))
    docs_all = {d["corp_label"] for d in disc.values() if d.get("corp_label")}
    silent = sorted(set(config.TARGETS_BY_LABEL) - set(by) - {""})
    print("        안건 0건인 대상 법인: %s" % ", ".join(silent))

    # ── 14·15 ────────────────────────────────────────────────────────────
    print()
    print("【14】 selftest 는 `python3 scripts/dart/run.py selftest` 로 따로 돌린다")
    print("【15】 키 유출 검사는 `scripts/dart/run.py selftest` 의 아카이브 스캔이 담당한다")

    print("\n결과: 통과 %d / 실패 %d" % (len(OK), len(BAD)))
    if BAD:
        print("실패 항목: %s" % BAD)
    return 1 if BAD else 0


if __name__ == "__main__":
    b = None
    if "--baseline" in sys.argv:
        b = sys.argv[sys.argv.index("--baseline") + 1]
    sys.exit(main(b))
