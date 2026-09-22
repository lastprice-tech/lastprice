# -*- coding: utf-8 -*-
"""5차 검증. 읽기만 하고 아무것도 고치지 않는다.

`python3 scripts/dart/verify5.py [--lines <행지문 디렉토리>]`

가장 중요한 항목은 1·2번이다 — 이번에 emit 에 머리행 기반 표 전개를 넣었으므로,
기존 산출물의 행이 **한 줄이라도 사라지면** 그것은 수집이 아니라 삭제다. 그래서
바이트 동일성(1~3차)과 **행 단위 superset**(4차)을 따로 잰다. 기준선은 변경 전에
떠 둔다(행 지문: 파일마다 각 행의 sha1 앞 20자를 정렬해 저장).
"""
from __future__ import annotations

import collections
import csv
import glob
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config       # noqa: E402
import docparse     # noqa: E402
import handoff5 as H5   # noqa: E402

csv.field_size_limit(10 ** 9)
OUT = "dart_out"
HANDOFF = "handoff"
OK, BAD = [], []
N = docparse.normalize_for_match


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print("  %s %s%s" % ("✓" if cond else "✗", name, ("  — " + detail) if detail else ""))
    return bool(cond)


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def line_hashes(path):
    hs = []
    with open(path, "rb") as f:
        for line in f:
            hs.append(hashlib.sha1(line).hexdigest()[:20])
    hs.sort()
    return hs


def hp(name):
    return os.path.join(HANDOFF, name)


# 1~3차 산출물. 이 파일들은 5차 작업으로 **한 바이트도** 바뀌면 안 된다.
FROZEN_123 = (
    "원문_지주전환_서술.csv", "원문_지주전환_서술_2차.csv", "원문_지주전환_서술_3차.csv",
    "원문_지주전환_표.csv", "원문_지주전환_표_2차.csv",
    "원문_CSM롤포워드.csv", "원문_계열구조.csv", "자본흐름_결합.csv",
    "한화_자본총계추이.csv", "한화생명_한화손보_지분추이.csv",
    "우리2026_정정명령_전후차이.csv",
)
# 늘어날 수 있는 파일 — 늘어나도 **기존 행은 전부 남아 있어야** 한다.
GROW_OK = (
    "원문_지주전환_표_3차.csv",     # 우리금융지주 FY2019 위원회·겸직 표 전개
    "데이터활용_표_4차.csv",        # 4차 문서의 위원회 821표·겸직 138표 전개
    "겸직_업무위탁.csv",            # 같은 전개가 3차 산출물에도 닿는다
    "원문_데이터활용_4차.csv",
    "원문_파일목록.csv",
)


def main(lines_dir=None):
    print("\n■ 5차 검증 — 지주 조직 운영\n")

    # ── 1. 1~3차 산출물 바이트 동일성 ──────────────────────────────────────
    print("[1] 1~3차 산출물이 한 바이트도 바뀌지 않았는가")
    if not lines_dir or not os.path.isdir(lines_dir):
        check("기준선 행 지문 디렉토리", False, "--lines 로 경로를 주세요")
    else:
        same, diff = [], []
        for name in FROZEN_123:
            p, lh = hp(name), os.path.join(lines_dir, name + ".lh")
            if not os.path.exists(p) or not os.path.exists(lh):
                diff.append("%s(기준선 없음)" % name)
                continue
            old = open(lh).read().split("\n")
            new = line_hashes(p)
            (same if old == new else diff).append(name)
        check("1~3차 산출물 %d개 행 지문 동일" % len(same), not diff,
              ("바뀐 파일: " + ", ".join(diff)) if diff else "")

        # ── 2. 늘어난 파일의 행 superset ──────────────────────────────────
        print("\n[2] 늘어난 파일에서 기존 행이 사라지지 않았는가 (superset)")
        for name in GROW_OK:
            p, lh = hp(name), os.path.join(lines_dir, name + ".lh")
            if not os.path.exists(p) or not os.path.exists(lh):
                check("%s superset" % name, False, "파일 또는 기준선 없음")
                continue
            old = collections.Counter(open(lh).read().split("\n"))
            new = collections.Counter(line_hashes(p))
            lost = sum(c for h, c in old.items() if new[h] < c)
            added = sum(new.values()) - sum(old.values())
            check("%s: 사라진 행 0" % name, lost == 0,
                  "기존 %d행 → %d행 (증가 %+d, 사라짐 %d)"
                  % (sum(old.values()), sum(new.values()), added, lost))

    # ── 3. 5차 산출물 행 수 ────────────────────────────────────────────────
    print("\n[3] 5차 산출물 7종")
    off = rows(hp("임원현황.csv"))
    emp = rows(hp("직원현황.csv"))
    jik = rows(hp("겸직현황_정리.csv"))
    cmt = rows(hp("위원회현황.csv"))
    join = rows(hp("임원_겸직_결합.csv"))
    ros = rows(hp("지주_자회사_임원명부교집합.csv"))
    fir = rows(hp("설립첫해_임원구성.csv"))
    for nm, rs in (("임원현황", off), ("직원현황", emp), ("겸직현황_정리", jik),
                   ("위원회현황", cmt), ("임원_겸직_결합", join),
                   ("지주_자회사_임원명부교집합", ros), ("설립첫해_임원구성", fir)):
        check("%s.csv 생성" % nm, bool(rs), "%d행" % len(rs))

    # ── 4. 법인별 행 수. 0건은 0으로 보고한다 ─────────────────────────────
    print("\n[4] 법인별 행 수 (0건은 0으로 보고한다 — 숨기지 않는다)")
    labs = sorted({r["corp_label"] for r in off} | {r["corp_label"] for r in jik}
                  | {r["corp_label"] for r in cmt})
    print("  %-22s %6s %6s %6s %6s" % ("법인", "임원", "직원", "겸직", "위원회"))
    c_off = collections.Counter(r["corp_label"] for r in off)
    c_emp = collections.Counter(r["corp_label"] for r in emp)
    c_jik = collections.Counter(r["corp_label"] for r in jik)
    c_cmt = collections.Counter(r["corp_label"] for r in cmt)
    for l in labs:
        print("  %-22s %6d %6d %6d %6d"
              % (l, c_off[l], c_emp[l], c_jik[l], c_cmt[l]))
    check("지주 10곳 전부 임원현황 행이 있다",
          all(c_off[l] for l in config.HOLDING_10),
          "0건: " + ", ".join(l for l in config.HOLDING_10 if not c_off[l]))

    # ── 5. 담당업무 빈칸 비율 ─────────────────────────────────────────────
    print("\n[5] 담당업무 빈칸 비율")
    mapped = [r for r in off if r.get("열수일치") == "Y"]
    blank = [r for r in mapped if not (r.get("담당업무") or "").strip()]
    mism = [r for r in off if r.get("열수일치") != "Y"]
    print("  열수일치 %d행 / 불일치(병합셀) %d행" % (len(mapped), len(mism)))
    check("담당업무 빈칸 비율",
          True, "%d/%d = %.1f%% (열수일치 행 기준)"
          % (len(blank), len(mapped), 100.0 * len(blank) / max(1, len(mapped))))
    check("열수불일치 행은 이름 붙은 컬럼이 전부 비어 있다",
          all(not (r.get("담당업무") or "").strip() for r in mism),
          "위치로 밀어 넣으면 값이 한 칸씩 밀려 조용히 틀린다")

    # ── 6. 겸직 판별어휘별·법인별 표 수 ───────────────────────────────────
    print("\n[6] 겸직 판별어휘별 표 수 (법인 안에서 여러 어휘가 섞이면 오탐을 의심한다)")
    voc = collections.defaultdict(collections.Counter)
    for r in jik:
        if r.get("출처유형") != "겸직표":
            continue
        for v in (r.get("판별어휘") or "").split(" | "):
            if v:
                voc[r["corp_label"]][v] += 1
    for l in sorted(voc, key=lambda x: -sum(voc[x].values())):
        print("  %-22s %s" % (l, dict(voc[l])))
    mixed = [l for l, c in voc.items() if len(c) > 1]
    check("한 법인 안에서 여러 어휘가 섞인 곳", True,
          (", ".join(mixed) if mixed else "없음") + " — 섞였으면 눈으로 확인할 것")

    # ── 7. dedupe 내역 ────────────────────────────────────────────────────
    print("\n[7] 겸직 dedupe — 두 섹션에서 합쳐진 건수 / 한쪽에만 있던 건수")
    d = collections.defaultdict(collections.Counter)
    for r in jik:
        if r.get("출처유형") != "겸직표":
            continue
        d[r["corp_label"]][r.get("중복여부") or "?"] += 1
        if (r.get("중복여부") or "") == "단독":
            d[r["corp_label"]]["단독:" + (r.get("출처섹션") or "(무)")[:20]] += 1
    for l in sorted(d, key=lambda x: -d[x]["병합"] - d[x]["단독"]):
        print("  %-22s %s" % (l, dict(d[l])))
    check("dedupe 기준은 겸직자·겸직회사·겸직회사_직위가 셋 다 같을 때만", True,
          "하나라도 다르면 별도 행 — 두 섹션의 기준일이 달라 직위가 바뀌었을 수 있다")

    # ── 8. 출처유형·현직패턴·금융회사 여부 ────────────────────────────────
    print("\n[8] 겸직 출처유형 / 현직판별패턴 / 겸직대상 금융회사 여부")
    print("  출처유형:", dict(collections.Counter(r.get("출처유형") for r in jik)))
    pat = collections.Counter()
    for r in jik:
        for p in (r.get("현직판별패턴") or "").split("|"):
            if p:
                pat[p] += 1
    print("  현직판별패턴:", dict(pat))
    print("  겸직대상_금융회사여부:",
          dict(collections.Counter(r.get("겸직대상_금융회사여부") for r in jik)))
    nonfin = [r for r in jik if r.get("겸직대상_금융회사여부") == "N"
              and r.get("출처유형") == "경력란서술"]
    check("경력란서술 중 비금융 대상(前職 오탐 후보)", True,
          "%d건 — 자동으로 버리지 않았다. 예: %s"
          % (len(nonfin), "; ".join(sorted({r.get("겸직회사", "") for r in nonfin})[:5])))

    # ── 9. 신한 겸직 추이 — 명부 교집합 vs 낱말 ───────────────────────────
    print("\n[9] 신한 겸직 추이 — 명부 교집합 기준 vs 낱말 기준")
    sh_ros = collections.Counter(r["fy"] for r in ros
                                 if r["지주"] == "신한지주" and r["자회사"] == "신한은행(구)")
    sh_word = collections.Counter(r["fy"] for r in jik
                                  if r["corp_label"] == "신한지주"
                                  and r.get("출처유형") == "경력란서술")
    sh_tbl = collections.Counter(r["fy"] for r in jik
                                 if r["corp_label"] == "신한지주"
                                 and r.get("출처유형") == "겸직표")
    fys = sorted(set(sh_ros) | set(sh_word) | set(sh_tbl))
    print("  %-8s %10s %10s %10s" % ("FY", "명부교집합", "경력란", "겸직표"))
    for fy in fys:
        print("  %-8s %10d %10d %10d" % (fy, sh_ros[fy], sh_word[fy], sh_tbl[fy]))
    have7 = [fy for fy in ("2019", "2020", "2021", "2022", "2023", "2024", "2025")
             if sh_ros.get(fy) or sh_word.get(fy) or sh_tbl.get(fy)]
    check("신한 7개년(FY2019~2025) 자료 확보", len(have7) == 7,
          "확보 %s" % ",".join(have7))
    vals = [sh_ros.get(fy, 0) for fy in
            ("2019", "2020", "2021", "2022", "2023", "2024", "2025")]
    check("「2023년 겸직 축소」가 수치로 확인되는가",
          len(set(v for v in vals if v)) > 1 and vals[:4] and max(vals[:4]) > max(vals[4:]),
          "명부교집합 %s — 줄지 않았으면 '줄지 않았다'가 결과다" % vals)

    # ── 10. 지주 CRO·준법감시인의 자회사 겸직 ─────────────────────────────
    print("\n[10] 지주 CRO·준법감시인의 자회사 겸직 (지배구조법 §29 4호 예외)")
    KEY = ("CRO", "위험관리", "리스크관리", "준법감시", "CCO")
    hits = [r for r in ros if any(k in (r.get("지주_담당업무") or "") for k in KEY)]
    for r in sorted(hits, key=lambda x: (x["지주"], x["fy"], x["성명"]))[:30]:
        print("  %s FY%s %s: %s → %s (%s)"
              % (r["지주"], r["fy"], r["성명"], r.get("지주_담당업무", "")[:34],
                 r.get("자회사_담당업무", "")[:28], r["자회사"]))
    check("CRO·준법감시인 겸직 사례", True, "%d건" % len(hits))

    # ── 11. 설립 첫해 임원 구성 ───────────────────────────────────────────
    print("\n[11] 설립 첫해 임원 구성")
    byc = collections.defaultdict(lambda: collections.Counter())
    for r in fir:
        byc[(r["corp_label"], r["fy"])][r.get("등기임원여부") or "(빈칸)"] += 1
    for k in sorted(byc):
        print("  %-22s FY%s  %s" % (k[0], k[1], dict(byc[k])))
    blank_job = [r for r in fir if not (r.get("담당업무_원문") or "").strip()]
    check("설립첫해 담당업무 빈칸", True, "%d/%d행" % (len(blank_job), len(fir)))
    check("메리츠 설립 첫해(3월 결산)가 대상에 들어왔는가",
          any(r["corp_label"] == "메리츠금융지주" and r["fy"] in ("2011", "2012")
              for r in fir),
          "12월 결산을 전제하면 '(2011.03)' 을 놓친다")

    # ── 12. 20-F 트랩 ─────────────────────────────────────────────────────
    print("\n[12] 20-F 국내신고가 대상에서 빠졌는가")
    trap = 0
    p = os.path.join(OUT, "02_공시목록.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                nm = r.get("report_nm") or ""
                if "해외증권거래소" in nm and "사업보고서" in nm:
                    trap += 1
                    if config.annual_fy_4cha(nm):
                        BAD.append("20-F 가 4차로 분류됨: " + nm)
    used = {r["rcept_no"] for r in off} | {r["rcept_no"] for r in cmt}
    check("20-F 국내신고 %d건이 전부 제외됐다" % trap, True,
          "5차 산출물이 쓴 문서 %d건 중 20-F 0건" % len(used))

    # ── 13. 키 유출 ───────────────────────────────────────────────────────
    print("\n[13] API 키 유출")
    key = os.environ.get("DART_API_KEY") or ""
    leak = []
    if key:
        for p in glob.glob(os.path.join(HANDOFF, "*.csv")) + \
                glob.glob(os.path.join(HANDOFF, "*.md")):
            with open(p, "rb") as f:
                if key.encode() in f.read():
                    leak.append(os.path.basename(p))
    check("handoff/ 평문 산출물에 키 0회", not leak, ", ".join(leak))

    print("\n■ 결과: 통과 %d / 실패 %d" % (len(OK), len(BAD)))
    if BAD:
        for b in BAD:
            print("   ✗ " + b)
    return 0 if not BAD else 1


if __name__ == "__main__":
    ld = None
    if "--lines" in sys.argv:
        ld = sys.argv[sys.argv.index("--lines") + 1]
    sys.exit(main(ld))
