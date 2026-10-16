#!/usr/bin/env python3
"""14차 합본 검증 — 인자 없이 실행, 결과 dart_out/org14/verify14.txt, exit 0(문제 0건) / 1.

검사(로컬 파일만 읽음 — 웹 요청 없음):
 G  그룹 검증 scripts/dart/verify14_g1.py ~ verify14_g4.py 를 실행해 exit 코드·마지막 줄을 모음(하나라도 0 이 아니면 문제)
 J  합본 CSV 3개 = 회사 CSV 8개를 회사 순서(KB·신한·하나·우리·메리츠·한국투자·iM·NH)로 이어 붙인 것
    (utf-8-sig, 머리 = COMMON14 열 이름, 같은 자리 열은 이름 꼴만 다를 수 있음, 회사 CSV 에 없는 뒤 열은 빈칸)
    + scripts/dart/org14_merge.py --check 로 다시 만든 것과 같은지(멱등)
 S  00_목록.md 2절 요약표 숫자·이름 = 합본 CSV 에서 이 스크립트가 따로 다시 센 값
    (단위 수·보조 행 수, 인원 공시 단위(직원 인원 / 위원·이사·구성원 수) 이름 목록, 등기·미등기 임원 수, 계열사 겸직 임원 수,
     조직도 겸직 표시 수, 조직도 기준일 = CSV 원문 칸). 지주 직원 수는 CSV 에 없어 회사 md 2) 직원 표 「합 계」 행과 맞댐.
    「추출 범위에 없음」 칸은 회사 md 2) 에 같은 말이 있는지 확인. 1-1·1-2·3-4 의 행 수·칸 수도 CSV 에서 다시 셈.
 Q  00_목록.md 1~4절의 「…」 조각이 회사 md·CSV 에 있는지(공백 무시) — 회사 행은 그 회사 파일에서, 나머지는 8개사 파일 전체에서
 K  키·OC 값(.env·환경 변수에서 읽음 — 값은 찍지 않음)이 14차 산출 파일에 없음, crtfc_key=/OC= 뒤 가리지 않은 값 없음
 F  handoff/14차_조직인원겸직 에 PDF·PNG·HWP(그림·원본) 파일 없음(dart_out/org14 도 함께 확인)
 B  1~13차 산출물이 커밋 b4ecf46 과 같음: git diff --quiet b4ecf46 -- <경로들> (+ 그 경로에 추적 안 되는 새 파일 없음)
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORG = os.path.join(ROOT, "dart_out", "org14")
HND = os.path.join(ROOT, "handoff", "14차_조직인원겸직")
OUT = os.path.join(ORG, "verify14.txt")
KST = timezone(timedelta(hours=9))

COS = ["KB금융지주", "신한금융지주", "하나금융지주", "우리금융지주",
       "메리츠금융지주", "한국투자금융지주", "iM금융지주", "NH농협금융지주"]
MERGED = {
    "조직단위": ("14_조직단위_인원_겸직.csv", [
        "회사", "조직도_문서", "조직도_쪽", "조직도_기준일(원문)", "상위단위(판독)", "조직단위(판독)", "단위_층위(판독)",
        "조직도_겸직표시(판독, 없으면 빈칸)", "공시인원(원문, 없으면 「추출 범위에 없음」)", "인원_내역(원문)", "인원_기준일",
        "인원_출처", "대응_임원(성명·직위)", "대응_근거(담당업무 원문)", "대응_방식(이름 일치/(판단)/추출 범위에 없음)",
        "임원_겸직(원문: 겸직회사·직위·선임일·상근)", "겸직_출처", "판독_대조", "비고"]),
    "임원겸직": ("14_임원겸직.csv", [
        "회사", "성명", "직위", "등기", "상근", "담당업무(원문)", "대응_조직단위", "대응_방식", "겸직회사", "겸직회사_직위",
        "선임일", "상근여부", "출처(문서·접수번호·쪽)", "임원표_구분", "겸직표_구분", "비고"]),
    "지원조직": ("14_지원조직_인원.csv", [
        "회사", "조직 종류", "부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)", "기준일", "출처"]),
}
# 합본 열 이름 → 회사 CSV 에서 허용하는 같은 자리 열 이름 꼴
SAME_COL = {
    "조직도_겸직표시(판독, 없으면 빈칸)": {"조직도_겸직표시(판독)"},
    "공시인원(원문, 없으면 「추출 범위에 없음」)": {"공시인원(원문)"},
    "대응_방식(이름 일치/(판단)/추출 범위에 없음)": {"대응_방식"},
    "임원_겸직(원문: 겸직회사·직위·선임일·상근)": {"임원_겸직(원문)"},
    "출처(문서·접수번호·쪽)": {"출처"},
    "주요 활동(원문)": {"주요 활동"},
}
OLD_PATHS = ["handoff/13차_산출물", "handoff/원문_10차", "handoff/원문_11차", "handoff/법령원문_10차",
             "handoff/법령원문_11차", "handoff/법령원문_저용량", "handoff/임원현황.csv", "handoff/겸직현황_정리.csv",
             "handoff/직원현황.csv"]

PROBS, INFO = [], []


def prob(where, msg):
    PROBS.append(f"[{where}] {msg}")


def info(msg):
    INFO.append(msg)


def rcsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def ns(s):
    return re.sub(r"\s+", "", s)


# ───────────── G ─────────────
def check_groups():
    for g in (1, 2, 3, 4):
        sp = os.path.join(ROOT, "scripts", "dart", f"verify14_g{g}.py")
        try:
            r = subprocess.run([sys.executable, sp], cwd=ROOT, capture_output=True, text=True, timeout=900)
            code, outp = r.returncode, (r.stdout + r.stderr)
        except subprocess.TimeoutExpired:
            code, outp = -1, "시간 초과"
        last = [l for l in outp.strip().split("\n") if l.strip()]
        last = last[-1].strip() if last else ""
        info(f"G verify14_g{g}.py exit {code} — 「{last[:160]}」 (결과 파일 dart_out/org14/verify14_g{g}.txt)")
        if code != 0:
            prob(f"G g{g}", f"verify14_g{g}.py exit {code}")


# ───────────── J ─────────────
def check_merged():
    data = {}
    for kind, (fname, head) in MERGED.items():
        p = os.path.join(HND, fname)
        if not os.path.exists(p):
            prob(f"J {fname}", "파일 없음")
            continue
        raw = open(p, "rb").read()
        if not raw.startswith(b"\xef\xbb\xbf"):
            prob(f"J {fname}", "utf-8-sig(BOM) 아님")
        m = rcsv(p)
        if m[0] != head:
            prob(f"J {fname}", "머리가 COMMON14 열 이름과 다름")
        want = []
        for co in COS:
            r = rcsv(os.path.join(ORG, f"{co}_{kind}.csv"))
            h = r[0]
            if len(h) > len(head):
                prob(f"J {fname}", f"{co} CSV 열 {len(h)} > 합본 열 {len(head)}")
                continue
            for i, name in enumerate(h):
                if name != head[i] and name not in SAME_COL.get(head[i], set()):
                    prob(f"J {fname}", f"{co} 열 {i} 「{name}」 ↔ 합본 「{head[i]}」")
            for x in r[1:]:
                want.append(x + [""] * (len(head) - len(h)))
        got = m[1:]
        if len(got) != len(want):
            prob(f"J {fname}", f"행 수 {len(got)} ≠ 회사 CSV 합 {len(want)}")
        bad = sum(1 for a, b in zip(got, want) if a != b)
        if bad:
            prob(f"J {fname}", f"회사 CSV 를 이어 붙인 것과 다른 행 {bad}개")
        order = list(OrderedDict.fromkeys(x[0] for x in got))
        if order != COS:
            prob(f"J {fname}", f"회사 순서 {order}")
        info(f"J {fname}: {len(got)}행 = 회사 CSV 이어 붙임({', '.join(str(sum(1 for x in got if x[0] == co)) for co in COS)}) · 다른 행 {bad}")
        data[kind] = got
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "dart", "org14_merge.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True, timeout=300)
    info(f"J org14_merge.py --check exit {r.returncode} — 「{r.stdout.strip()[:120]}」")
    if r.returncode != 0:
        prob("J 멱등", "org14_merge.py --check 가 다시 만든 것과 다르다고 함")
    return data


# ───────────── S: 다시 세기(이 스크립트의 규칙 구현) ─────────────
MARKS = ("직원 아님", "직원 수 아님", "직원 수가 아님", "(직원 인원)", "총원(위원)")


def recount(co, data):
    U = [dict(zip(MERGED["조직단위"][1], x)) for x in data["조직단위"] if x[0] == co]
    doc0 = U[0]["조직도_문서"]
    main = [u for u in U if u["조직도_문서"] == doc0]
    aux = [u for u in U if u["조직도_문서"] != doc0]
    kp = "공시인원(원문, 없으면 「추출 범위에 없음」)"

    def split(rows):
        a, b = [], []
        for u in rows:
            v = u[kp]
            if v.startswith("추출 범위에 없음") and not v.startswith("추출 범위에 없음(직원 인원)"):
                continue
            blob = u[kp] + "\n" + u["인원_내역(원문)"] + "\n" + u["인원_출처"]
            (b if any(mk in blob for mk in MARKS) else a).append(u["조직단위(판독)"])
        return a, b

    staff, wiwon = split(main)
    astaff, awiwon = split(aux)
    km = "조직도_겸직표시(판독, 없으면 빈칸)"
    marks = [u["조직단위(판독)"] for u in main if u[km].strip()]
    amarks = [u["조직단위(판독)"] for u in aux if u[km].strip()]
    bases = {u["조직도_기준일(원문)"] for u in main}

    E = [dict(zip(MERGED["임원겸직"][1], x)) for x in data["임원겸직"] if x[0] == co]
    wide = len(rcsv(os.path.join(ORG, f"{co}_임원겸직.csv"))[0]) == 16
    src = "출처(문서·접수번호·쪽)"

    def in_exec(e):
        if wide:
            return re.search(r"임원\s?현황\(기준일 2025", e["임원표_구분"]) is not None
        return (not e["직위"].startswith("임원 표(")) and "임원 현황 (기준일 : 2025년 12월 31일" in e[src].split("‖")[0]

    def in_conc(e):
        if not e["겸직회사"] or "나오지 않음" in e["겸직회사"]:
            return False
        if wide:
            t = e["겸직표_구분"]
            return "2025" in t and not any(k in t for k in ("타회사", "약력", "연차보고서", "VII장"))
        if "‖ 겸직:" in e[src]:
            t = e[src].split("‖ 겸직:")[1]
        elif e["직위"].startswith("임원 표("):
            t = e[src]
        else:
            return False
        return "2025년 12월 31일" in t

    ex = OrderedDict()
    for e in E:
        if in_exec(e) and e["성명"] not in ex:
            ex[e["성명"]] = e["등기"]
    reg = sum(1 for g in ex.values() if g in ("사내이사", "사외이사", "기타비상무이사"))
    unreg = sum(1 for g in ex.values() if g == "미등기")
    conc = list(OrderedDict.fromkeys(e["성명"] for e in E if in_conc(e)))
    return dict(main=main, aux=aux, staff=staff, wiwon=wiwon, astaff=astaff, awiwon=awiwon, marks=marks,
                amarks=amarks, bases=bases, nexec=len(ex), reg=reg, unreg=unreg, conc=conc,
                conc_in=[n for n in conc if n in ex], conc_out=[n for n in conc if n not in ex])


def md_lines(path):
    return open(path, encoding="utf-8").read().split("\n")


def section(L, prefix):
    s = next(i for i, l in enumerate(L) if l.startswith(prefix))
    e = next((i for i, l in enumerate(L) if i > s and l.startswith("## ")), len(L))
    return s, e


def md_staff_total(co):
    L = md_lines(os.path.join(HND, f"14_{co}.md"))
    s, e = section(L, "## 2)")
    found = set()
    for l in L[s:e]:
        t = re.sub(r"[`|*]", " ", l).strip().lstrip("-").strip()
        m = re.match(r"합\s?계((?:\s+합\s?계)?)\s+(.*)$", t)
        if not m:
            continue
        toks = m.group(2).split()
        if len(toks) >= 5 and all(re.fullmatch(r"[\d,]+|-", k) for k in toks[:5]) and toks[4].isdigit():
            found.add(int(toks[4]))
    return found, L[s:e]


def parse_names(s):
    return [x.strip() for x in s.split(", ") if x.strip()]


def check_summary(data):
    L = md_lines(os.path.join(HND, "00_목록.md"))
    s, e = section(L, "## 2)")
    rows = [l for l in L[s:e] if l.startswith("| ") and not l.startswith("| 회사") and not l.startswith("|---")]
    seen = []
    for l in rows:
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        co = c[0]
        if co not in COS:
            prob("S 2절", f"모르는 회사 행 「{co}」")
            continue
        seen.append(co)
        if len(c) != 10:
            prob(f"S {co}", f"칸 수 {len(c)} ≠ 10")
            continue
        R = recount(co, data)
        # 기준일
        m = re.match(r"「([^」]*)」", c[1])
        if len(R["bases"]) != 1 or not m or m.group(1) not in R["bases"]:
            prob(f"S {co} 기준일", f"「{m.group(1) if m else ''}」 ↔ CSV 주 조직도 행 기준일 {sorted(R['bases'])}")
        # 단위 수
        m = re.match(r"(\d+)(?: \(보조 조직도 행 (\d+) 따로\))?$", c[3])
        got = (int(m.group(1)), int(m.group(2) or 0)) if m else None
        if got != (len(R["main"]), len(R["aux"])):
            prob(f"S {co} 단위 수", f"표 {c[3]} ↔ CSV 주 {len(R['main'])} · 보조 {len(R['aux'])}")
        # 인원 공시 단위
        parts = c[4].split("<br>")
        want = OrderedDict([("직원 인원", R["staff"]), ("위원·이사·구성원 수", R["wiwon"])])
        if R["astaff"]:
            want["보조 조직도 행 직원 인원"] = R["astaff"]
        if R["awiwon"]:
            want["보조 조직도 행 위원·이사·구성원 수"] = R["awiwon"]
        gotp = OrderedDict()
        for p in parts:
            m = re.match(r"(.+?) (\d+)(?: — (.*))?$", p)
            if not m:
                prob(f"S {co} 인원 공시", f"읽지 못한 조각 「{p[:60]}」")
                continue
            nm = parse_names(m.group(3) or "")
            if int(m.group(2)) != len(nm):
                prob(f"S {co} 인원 공시", f"「{m.group(1)}」 수 {m.group(2)} ≠ 이름 {len(nm)}개")
            gotp[m.group(1)] = nm
        if gotp != want:
            diff = []
            for k in list(OrderedDict.fromkeys(list(gotp) + list(want))):
                a, b = gotp.get(k, []), want.get(k, [])
                if a != b:
                    diff.append(f"{k}: 표에만 {[x for x in a if x not in b]} · CSV 에만 {[x for x in b if x not in a]} · 수 {len(a)}/{len(b)}")
            prob(f"S {co} 인원 공시", "; ".join(diff) or "순서가 다름")
        # 직원 수
        m = re.match(r"(\d+)명", c[5])
        tot, sec2 = md_staff_total(co)
        if not m or len(tot) != 1 or int(m.group(1)) not in tot:
            prob(f"S {co} 직원 수", f"표 {c[5][:20]} ↔ 회사 md 2) 「합 계」 행 {sorted(tot)}")
        # 직원 겸직 숫자: 추출 범위에 없음이면 md 2) 에 같은 말
        if c[6].startswith("추출 범위에 없음"):
            if not any("직원 겸직 숫자" in x and "추출 범위에 없음" in x.replace("*", "") for x in sec2):
                prob(f"S {co} 직원 겸직", "회사 md 2) 에 「직원 겸직 숫자 … 추출 범위에 없음」 줄이 없음")
        # 임원
        m = re.match(r"(\d+)명 \(등기 (\d+) · 미등기 (\d+)\)$", c[7])
        if not m or tuple(map(int, m.groups())) != (R["nexec"], R["reg"], R["unreg"]):
            prob(f"S {co} 임원 수", f"표 {c[7]} ↔ CSV {R['nexec']}(등기 {R['reg']} · 미등기 {R['unreg']})")
        # 겸직 임원
        m = re.match(r"(\d+)명 \(그중 같은 날 임원 표에 있는 사람 (\d+)\)(?: — 임원 표에 없는 사람: (.*))?$", c[8])
        if not m or (int(m.group(1)), int(m.group(2)), parse_names(m.group(3) or "")) != (len(R["conc"]), len(R["conc_in"]), R["conc_out"]):
            prob(f"S {co} 겸직 임원", f"표 {c[8][:60]} ↔ CSV {len(R['conc'])}명(임원 표 {len(R['conc_in'])}, 밖 {R['conc_out']})")
        # 조직도 겸직 표시
        p9 = c[9].split("<br>")
        mains = [x for x in p9 if not x.startswith("보조 조직도 행")]
        auxs = [x for x in p9 if x.startswith("보조 조직도 행")]
        n_main = 0
        names_main = []
        for x in mains:
            if x.startswith("나오지 않음"):
                continue
            m = re.match(r"「[^」]+」 (\d+)곳 — (.*?)(?: \(판독\))?$", x)
            if m:
                n_main += int(m.group(1))
                names_main += parse_names(m.group(2))
        if n_main != len(R["marks"]) or names_main != R["marks"]:
            prob(f"S {co} 겸직 표시", f"표 주 조직도 {n_main} ↔ CSV {len(R['marks'])}")
        n_aux = sum(int(re.match(r"보조 조직도 행 (\d+)곳", x).group(1)) for x in auxs)
        if n_aux != len(R["amarks"]):
            prob(f"S {co} 겸직 표시", f"표 보조 {n_aux} ↔ CSV {len(R['amarks'])}")
        info(f"S {co}: 단위 {len(R['main'])}+보조 {len(R['aux'])} · 직원 인원 {len(R['staff'])} · 위원·이사·구성원 {len(R['wiwon'])}"
             f" (보조 {len(R['astaff'])}/{len(R['awiwon'])}) · 직원 {sorted(tot)} · 임원 {R['nexec']}({R['reg']}/{R['unreg']})"
             f" · 겸직 {len(R['conc'])}(임원 표 {len(R['conc_in'])}) · 겸직 표시 {len(R['marks'])}/{len(R['amarks'])} — 표와 같음")
    if seen != COS:
        prob("S 2절", f"회사 행 순서·수 {seen}")
    # 1-1 행 수, 1-2 행 수, 3-4 판독대조 칸 수
    txt = "\n".join(L)
    for kind, (fname, _) in MERGED.items():
        m = re.search(r"\| `" + re.escape(fname) + r"` \| [^|]*\| (\d+) \|", txt)
        if not m or int(m.group(1)) != len(data[kind]):
            prob(f"S 1-1 {fname}", f"행 수 {m.group(1) if m else '?'} ↔ CSV {len(data[kind])}")
    s1, e1 = section(L, "## 1)")
    for l in L[s1:e1]:
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        if c and c[0] in COS and len(c) == 5:
            co = c[0]
            nn = tuple(int(x) for x in re.findall(r"\d+", c[3]))
            want = (sum(1 for x in data["조직단위"] if x[0] == co), sum(1 for x in data["임원겸직"] if x[0] == co),
                    sum(1 for x in data["지원조직"] if x[0] == co), len(rcsv(os.path.join(ORG, f"{co}_판독대조.csv"))) - 1)
            if nn != want:
                prob(f"S 1-2 {co}", f"행 수 {nn} ↔ CSV {want}")
    s3, e3 = section(L, "## 3)")
    for l in L[s3:e3]:
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        if c and c[0] in COS and len(c) == 4 and c[1].isdigit():
            n = len(rcsv(os.path.join(ORG, f"{c[0]}_판독대조.csv"))) - 1
            if int(c[1]) != n:
                prob(f"S 3-4 {c[0]}", f"판독대조 칸 수 {c[1]} ↔ CSV {n}")


# ───────────── Q: 「」 조각 ─────────────
def corpus(co):
    parts = [open(os.path.join(HND, f"14_{co}.md"), encoding="utf-8").read()]
    for k in ("조직단위", "임원겸직", "지원조직", "판독대조"):
        parts.append(open(os.path.join(ORG, f"{co}_{k}.csv"), encoding="utf-8-sig").read())
    return ns("\n".join(parts))


def check_fragments():
    C = {co: corpus(co) for co in COS}
    ALL = "".join(C.values())
    L = md_lines(os.path.join(HND, "00_목록.md"))
    s5 = next(i for i, l in enumerate(L) if l.startswith("## 5)"))
    s1 = next(i for i, l in enumerate(L) if l.startswith("## 1)"))
    n_ok, miss = 0, []
    for i in range(s1, s5):
        l = L[i]
        if "셈 규칙" in l or l.startswith("- 판독한 조직 단위 수") or l.startswith("- 인원이 공시된 단위") or l.startswith("- 지주 전체 직원 수") \
                or l.startswith("- 계열사 겸직") or l.startswith("- 등기·미등기") or l.startswith("- 조직도 겸직 표시") or l.startswith("- 회사 md 끝 counts"):
            scope = ALL  # 셈 규칙 줄: CSV 표시 낱말
        else:
            c = l.strip().strip("|").split(" | ")
            co = c[0].strip() if c else ""
            scope = C[co] if co in C else ALL
        for frag in re.findall(r"「([^「」]+)」", l):
            f = ns(frag)
            if not f:
                continue
            if f in scope:
                n_ok += 1
            else:
                miss.append((i + 1, frag))
    for ln, frag in miss:
        prob(f"Q 00_목록.md {ln}행", f"「{frag[:80]}」 이 회사 md·CSV 에 없음(공백 무시)")
    info(f"Q 00_목록.md 1~4절 「」 조각 {n_ok + len(miss)}개 중 회사 md·CSV 에서 찾음 {n_ok}")


# ───────────── K·F·B ─────────────
def secret_values():
    vals = []
    for name in ("DART_API_KEY", "LAW_OC", "OC", "LAW_API_OC"):
        v = os.environ.get(name)
        if v and len(v) >= 4:
            vals.append(v)
    envp = os.path.join(ROOT, ".env")
    if os.path.exists(envp):
        for ln in open(envp, encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*([A-Za-z_]+)\s*=\s*['\"]?([^'\"\s#]+)", ln)
            if m and ("KEY" in m.group(1) or "OC" in m.group(1)) and len(m.group(2)) >= 4:
                vals.append(m.group(2))
    return list(dict.fromkeys(vals))


def check_secrets_files():
    vals = secret_values()
    targets = []
    for d in (HND, ORG):
        for dp, _, fn in os.walk(d):
            targets += [os.path.join(dp, x) for x in fn]
    for x in ("org14_g1.py", "org14_g2.py", "org14_g3.py", "org14_g4.py", "org14_merge.py",
              "verify14_g1.py", "verify14_g2.py", "verify14_g3.py", "verify14_g4.py", "verify14.py"):
        targets.append(os.path.join(ROOT, "scripts", "dart", x))
    for p in targets:
        if p == OUT:
            continue
        s = open(p, encoding="utf-8", errors="ignore").read()
        for v in vals:
            if v in s:
                prob(f"K {os.path.relpath(p, ROOT)}", "인증값 문자열이 파일에 있음(값은 적지 않음)")
        if re.search(r"crtfc_key=(?!\*\*\*)[0-9A-Za-z]", s) or re.search(r"[?&]OC=(?!\*\*\*)[0-9A-Za-z]", s):
            prob(f"K {os.path.relpath(p, ROOT)}", "crtfc_key=/OC= 뒤에 가리지 않은 값")
    info(f"K 인증값 비교 대상 {len(vals)}개(값은 적지 않음) · 검사 파일 {len(targets)}개")
    bad = []
    for d in (HND, ORG):
        for dp, _, fn in os.walk(d):
            for x in fn:
                if x.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".hwp", ".hwpx")):
                    bad.append(os.path.relpath(os.path.join(dp, x), ROOT))
    for b in bad:
        prob("F", f"산출 폴더에 원본·그림 파일 {b}")
    info(f"F handoff/14차_조직인원겸직·dart_out/org14 의 PDF·PNG·JPG·HWP 파일 {len(bad)}개")


def check_old():
    r = subprocess.run(["git", "diff", "--quiet", "b4ecf46", "--"] + OLD_PATHS, cwd=ROOT)
    if r.returncode != 0:
        prob("B", f"git diff --quiet b4ecf46 -- (1~13차 산출물) exit {r.returncode}")
    u = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--"] + OLD_PATHS,
                       cwd=ROOT, capture_output=True, text=True)
    if u.stdout.strip():
        prob("B", f"1~13차 경로에 바뀐·새 파일 {len(u.stdout.strip().splitlines())}개")
    info(f"B git diff --quiet b4ecf46 -- {' '.join(OLD_PATHS)} → exit {r.returncode}; git status 줄 {len(u.stdout.strip().splitlines()) if u.stdout.strip() else 0}")


def main():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    check_groups()
    data = check_merged()
    if len(data) == 3:
        check_summary(data)
    check_fragments()
    check_secrets_files()
    check_old()
    lines = [f"# verify14 — 14차 합본 검증 ({now})", "",
             "검사: G 그룹 검증 4개 실행 · J 합본 = 회사 CSV 이어 붙임(+멱등) · S 00_목록 2절 숫자 = CSV 다시 셈 · "
             "Q 00_목록 「」 조각 ↔ 회사 md·CSV · K 키·OC 값 없음 · F 산출 폴더 PDF·PNG·HWP 없음 · B 1~13차 = b4ecf46", ""]
    lines += ["## 기록"] + [f"- {x}" for x in INFO] + [""]
    lines += [f"## 문제 {len(PROBS)}건"] + [f"- {x}" for x in PROBS] + [""]
    lines.append("결과: " + ("통과(exit 0)" if not PROBS else "실패(exit 1)"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    for x in INFO:
        if x.startswith(("G ", "J ", "K ", "F ", "B ")):
            print(x[:200])
    print(f"S 2절 회사 {sum(1 for x in INFO if x.startswith('S '))}행 확인 · Q {next((x for x in INFO if x.startswith('Q ')), '')}")
    for x in PROBS[:30]:
        print("문제:", x[:220])
    print(f"문제 {len(PROBS)}건 · 결과 dart_out/org14/verify14.txt")
    return 0 if not PROBS else 1


if __name__ == "__main__":
    sys.exit(main())
