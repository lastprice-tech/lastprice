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
 E  「없음」 단정 0: 합본 CSV 3개의 모든 칸과 00_목록.md 의 모든 줄에서, 「」 인용 조각·정한 말(「추출 범위에 없음」
    「해당 없음(대응 임원 추출 범위에 없음)」)·작업 사실(「글자층 없음」)·열 이름(「…없으면…」)을 뺀 글에
    「없음·없었·없고·없어·없다」(00_목록은 「없는·없이·없으…·수 없」도) 꼴이 0곳. 원문 칸(원문 표·문장을 옮긴 칸)에서
    걸린 글이 그 회사 텍스트(dart_out/text/risk8)에 공백 무시로 그대로 있으면 원문으로 보고 셈에서 뺌.
 N  조직단위 행 가운데 대응_방식(또는 대응_임원)이 「추출 범위에 없음」인 행: 대응_근거 칸이 비어 있지 않고 「찾은 방법」이 적힘
 D  기준일 칸 빈칸 0: 조직단위 조직도_기준일(원문) 모든 행, 인원_기준일은 공시인원에 값이 있는 행(「추출 범위에 없음」으로
    시작하지 않거나 「추출 범위에 없음(직원 인원)」 — 위원 수 행), 지원조직 기준일 모든 행
    (참고로 날짜를 채우면서 「판단」 글이 나오지 않는 줄 수를 기록 — 문제로 세지 않음)
 C  8개사 공통 꼴(비평 보정 2 — dart_out/org14/critic14_2.json 뒤 메인이 정한 꼴):
    C1 한계 줄 단정 0: 회사 md 0) 의 한계 줄에 「추출 범위(사업보고서·연차보고서·경영공시 — 찾은 방법은 6) 받지 못한 것)에
       나오지 않아」 꼴이 있고, 회사 md 7) 앞과 00_목록.md 의 「」 인용 밖에 「공시되지 않」 류 단정 0. 00_목록 4) 한계에도 같은 꼴.
    C2 공시인원 「추출 범위에 없음」 행(「추출 범위에 없음(직원 인원)」 포함): 인원_출처에 「찾은 방법:」이 있고, 인원_내역(원문 열)에
       「찾은 방법」 0. 「추출 범위에 없음」(직원 인원 꼴 뺌) 행의 인원_기준일은 빈칸(00_목록 5-1 설명과 맞음).
    C3 임원_겸직 한 꼴: 맡은 임원 「추출 범위에 없음」 행의 임원_겸직 = 「해당 없음(대응 임원 추출 범위에 없음)」(8개사 모두).
    C4 기준일 (판단) 꼴: 조직도_기준일(원문)·인원_기준일·지원조직 기준일의 줄마다 날짜 글(숫자 4자리)이 있고,
       「 / 」로 이은 조각(괄호·「」 밖에서 나눔) 가운데 「판단」이 든 조각은 「<날짜>(판단: <무엇>에 기준일 글이 나오지 않아 <근거>로 둠)」 꼴
       (「기준일 날짜 글이」「날짜가」 변형 허용), 「판단」 없이 「나오지 않」「적히지 않」「표기」 관찰만 적은 옛 꼴 0.
    C5 열 이름 한 꼴: 회사 CSV 머리 = 합본 머리(임원겸직은 앞 13열 또는 16열 전체) — 이름 맞춤 표 없이.
 K  키·OC 값(.env·환경 변수에서 읽음 — 값은 찍지 않음)이 14차 산출 파일에 나오지 않음, crtfc_key=/OC= 뒤에 가리지 않은 값 0
 F  handoff/14차_조직인원겸직 에 PDF·PNG·HWP(그림·원본) 파일 0개(dart_out/org14 도 함께 확인)
 B  1~13차 산출물이 커밋 b4ecf46 과 같음: git diff --quiet b4ecf46 -- <경로들> (+ 그 경로에 추적 안 되는 새 파일 0개)
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
# 합본 열 이름 → 회사 CSV 에서 허용하는 같은 자리 열 이름 꼴. 비평 보정 2 뒤 8개사 회사 CSV 머리가 합본 머리와 같아 비움
# (전: 「출처(문서·접수번호·쪽)」 ← 「출처」, 「주요 활동(원문)」 ← 「주요 활동」).
SAME_COL: dict = {}
TEXT = os.path.join(ROOT, "dart_out", "text", "risk8")
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
        m = re.match(r"(\d+)명 \(그중 같은 날 임원 표에 있는 사람 (\d+)\)(?: — 임원 표에 나오지 않는 사람: (.*))?$", c[8])
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


# ───────────── E: 「없음」 단정(원문 칸·「」 인용 밖) ─────────────
EOPSEUM = re.compile(r"없(?:음|었|고|어|다)")                       # 그룹 검증(E·검사 9)과 같은 꼴
EOPSEUM_MD = re.compile(r"없(?:음|었|고|어|다|는|이|으)|수\s?없")     # 00_목록(합본 스크립트가 쓰는 글)은 더 넓게
ALLOW = ["해당 없음(대응 임원 추출 범위에 없음)", "추출 범위에 없음", "글자층 없음"]   # 정한 말 · 작업 사실
RAW_COLS = {   # 원문(또는 판독) 글을 옮긴 칸
    "조직단위": {"조직도_기준일(원문)", "상위단위(판독)", "조직단위(판독)", "단위_층위(판독)", "조직도_겸직표시(판독, 없으면 빈칸)",
               "인원_내역(원문)", "대응_근거(담당업무 원문)", "임원_겸직(원문: 겸직회사·직위·선임일·상근)"},
    "임원겸직": {"성명", "직위", "등기", "상근", "담당업무(원문)", "겸직회사", "겸직회사_직위", "선임일", "상근여부"},
    "지원조직": {"부서(팀)명", "직원수", "직위(근속연수)", "주요 활동(원문)", "기준일"},
}
_SRC = {}


def src_text(co):
    """그 회사 원문 텍스트(dart_out/text/risk8 에서 파일 이름에 회사 이름이 든 것) — 공백 뺀 글. 필요할 때만 읽음."""
    if co not in _SRC:
        parts = []
        for fn in sorted(os.listdir(TEXT)):
            if co in fn and fn.endswith(".txt"):
                parts.append(open(os.path.join(TEXT, fn), encoding="utf-8", errors="replace").read())
        _SRC[co] = ns("\n".join(parts))
    return _SRC[co]


def blank_quotes(s):
    """「…」(겹 「」 포함) 안 글을 같은 길이의 빈칸으로 바꿈 — 자리(index)는 그대로."""
    out, depth = [], 0
    for ch in s:
        if ch == "「":
            depth += 1
            out.append(" ")
        elif ch == "」" and depth:
            depth -= 1
            out.append(" ")
        else:
            out.append(" " if depth else ch)
    return "".join(out)


def blank_phrases(s, phrases):
    for p in phrases:
        s = s.replace(p, " " * len(p))
    return s


def check_eopseum(data):
    n_cell = n_hit_raw = 0
    bad = []
    for kind, (fname, head) in MERGED.items():
        for r, x in enumerate(data.get(kind, []), start=2):
            for j, v in enumerate(x):
                if "없" not in v:
                    continue
                n_cell += 1
                t = blank_phrases(blank_quotes(v), ALLOW)
                for m in EOPSEUM.finditer(t):
                    if head[j] in RAW_COLS[kind]:
                        seg = ns(v[max(0, m.start() - 15):m.end()])
                        if seg and seg in src_text(x[0]):
                            n_hit_raw += 1
                            continue
                    bad.append(f"{fname} 레코드 {r} ({x[0]}) 「{head[j]}」: …{v[max(0, m.start() - 25):m.end() + 8]}…")
    L = md_lines(os.path.join(HND, "00_목록.md"))
    colnames = sorted({h for _, (_, hd) in MERGED.items() for h in hd if "없" in h}, key=len, reverse=True)
    n_md = 0
    for i, l in enumerate(L, start=1):
        if "없" not in l:
            continue
        n_md += 1
        t = blank_phrases(blank_quotes(blank_phrases(l, colnames)), ALLOW)
        for m in EOPSEUM_MD.finditer(t):
            bad.append(f"00_목록.md {i}행: …{l[max(0, m.start() - 25):m.end() + 8]}…")
    for b in bad:
        prob("E 「없음」", b.replace("\n", " ")[:220])
    info(f"E 「없음」 검사: 합본 CSV 칸 {n_cell}개·00_목록 줄 {n_md}개에 「없」 글자 — 원문 칸에서 회사 텍스트와 같은 글 {n_hit_raw}곳은 원문으로 봄 · 단정 {len(bad)}곳")


# ───────────── N: 맡은 임원 「추출 범위에 없음」 행의 찾은 방법 ─────────────
def check_nomap(data):
    head = MERGED["조직단위"][1]
    ki, kg, km, kj = (head.index("대응_임원(성명·직위)"), head.index("대응_근거(담당업무 원문)"),
                      head.index("대응_방식(이름 일치/(판단)/추출 범위에 없음)"), head.index("임원_겸직(원문: 겸직회사·직위·선임일·상근)"))
    cnt, zero, forms = OrderedDict((co, 0) for co in COS), OrderedDict((co, 0) for co in COS), OrderedDict()
    for r, x in enumerate(data["조직단위"], start=2):
        if not (x[km].startswith("추출 범위에 없음") or x[ki].startswith("추출 범위에 없음")):
            continue
        cnt[x[0]] += 1
        g = x[kg].strip()
        if not g or "찾은 방법" not in g:
            prob(f"N {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 대응_임원 「추출 범위에 없음」인데 대응_근거에 찾은 방법이 적히지 않음")
        if re.search(r"— 0건", g):
            zero[x[0]] += 1
        forms.setdefault(x[kj] or "(빈칸)", []).append(x[0])
    info("N 맡은 임원 「추출 범위에 없음」 행(찾은 방법 적힘 / 그중 「— 0건」): "
         + " · ".join(f"{co} {cnt[co]}/{zero[co]}" for co in COS))
    info("N 같은 행의 임원_겸직 칸 꼴(참고): " + " · ".join(
        f"「{k[:30]}」 {'·'.join(OrderedDict.fromkeys(v))} {len(v)}행" for k, v in forms.items()))


# ───────────── D: 기준일 칸 빈칸 ─────────────
def check_dates(data):
    hu, hs = MERGED["조직단위"][1], MERGED["지원조직"][1]
    i_org, i_pp, i_num = hu.index("조직도_기준일(원문)"), hu.index("인원_기준일"), hu.index("공시인원(원문, 없으면 「추출 범위에 없음」)")
    i_sd = hs.index("기준일")
    n_need = 0
    for r, x in enumerate(data["조직단위"], start=2):
        if not x[i_org].strip():
            prob(f"D {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 조직도_기준일 빈칸")
        v = x[i_num]
        if (not v.startswith("추출 범위에 없음")) or v.startswith("추출 범위에 없음(직원 인원)"):
            n_need += 1
            if not x[i_pp].strip():
                prob(f"D {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 공시인원 값이 있는데 인원_기준일 빈칸")
    for r, x in enumerate(data["지원조직"], start=2):
        if not x[i_sd].strip():
            prob(f"D {x[0]}", f"지원조직 레코드 {r} 「{x[2]}」: 기준일 빈칸")

    def nojud(v):
        return [l for l in v.split("\n") if re.search(r"나오지 않|적히지 않", l) and re.search(r"\d{4}", l) and "판단" not in l]
    ref = OrderedDict()
    for kind, idx in (("조직단위", i_pp), ("지원조직", i_sd)):
        for x in data[kind]:
            if nojud(x[idx]):
                ref[f"{kind} {x[0]}"] = ref.get(f"{kind} {x[0]}", 0) + 1
    info(f"D 기준일 칸: 조직단위 {len(data['조직단위'])}행 조직도_기준일 · 인원 값 있는 {n_need}행 인원_기준일 · 지원조직 {len(data['지원조직'])}행 기준일 — 빈칸은 문제로 셈")
    info("D 참고(문제로 세지 않음): 「나오지 않음」 관찰과 날짜를 함께 적고 「판단」 글이 나오지 않는 줄 — "
         + (" · ".join(f"{k} {v}" for k, v in ref.items()) if ref else "0"))


# ───────────── C: 8개사 공통 꼴(비평 보정 2) ─────────────
LIMIT_FORM = "추출 범위(사업보고서·연차보고서·경영공시 — 찾은 방법은 6) 받지 못한 것)에 나오지 않아"
LIMIT_FORM_MERGED = "추출 범위(사업보고서·연차보고서·경영공시 — 찾은 방법은 회사 md 6) 받지 못한 것)에 나오지 않아"
DANJEONG = re.compile(r"공시되지\s?않|공시하지\s?않|공시돼\s?있지\s?않|공시되어\s?있지\s?않")
NOMAP_CONC = "해당 없음(대응 임원 추출 범위에 없음)"
JUD = re.compile(r"^(?:[①-⑳]\s*)?(?P<d>[^()]*\d{4}[^()]*)\(판단: (?P<body>.+)\)$")
JUD_BODY = re.compile(r"^.+?에 .*?(?:기준일(?: 날짜)? 글이|기준일\(날짜\) 글이|날짜 글이|날짜가) 나오지 않아 .+?로 둠(?: — .+)?$")
OLD_DATE = re.compile(r"나오지 않|적히지 않|표기")


def split_top(s):
    """「 / 」로 이은 조각을 괄호·「」 밖에서만 나눔."""
    out, buf, d, i = [], "", 0, 0
    while i < len(s):
        ch = s[i]
        if ch in "(「":
            d += 1
        elif ch in ")」":
            d = max(0, d - 1)
        if d == 0 and s.startswith(" / ", i):
            out.append(buf)
            buf, i = "", i + 3
            continue
        buf += ch
        i += 1
    out.append(buf)
    return out


def md_body_lines(L, stop):
    """회사 md 에서 stop 줄 앞까지, 코드 블록·「>」 인용 줄을 뺀 (줄 번호, 글)."""
    out, code = [], False
    for i, l in enumerate(L[:stop], start=1):
        if l.startswith("```"):
            code = not code
            continue
        if code or l.startswith(">"):
            continue
        out.append((i, l))
    return out


def check_common(data):
    # C1 한계 줄
    n_lim = 0
    for co in COS:
        L = md_lines(os.path.join(HND, f"14_{co}.md"))
        s0, e0 = section(L, "## 0)")
        lim = [(i + 1, L[i]) for i in range(s0, e0) if re.match(r"(\| 한계 \||- 한계[:：])", L[i])]
        if not lim:
            prob(f"C1 {co}", "회사 md 0) 에 한계 줄이 나오지 않음")
        for ln, l in lim:
            n_lim += 1
            if LIMIT_FORM not in l:
                prob(f"C1 {co}", f"md {ln}행 한계 줄에 공통 꼴 「{LIMIT_FORM[:30]}…」이 나오지 않음")
        s7 = next((i for i, l in enumerate(L) if l.startswith("## 7)")), len(L))
        for ln, l in md_body_lines(L, s7):
            m = DANJEONG.search(blank_quotes(l))
            if m:
                prob(f"C1 {co}", f"md {ln}행(7) 앞) 단정 꼴: …{l[max(0, m.start() - 20):m.end() + 6]}…")
    L = md_lines(os.path.join(HND, "00_목록.md"))
    for i, l in enumerate(L, start=1):
        m = DANJEONG.search(blank_quotes(l))
        if m:
            prob("C1 00_목록.md", f"{i}행 단정 꼴: …{l[max(0, m.start() - 20):m.end() + 6]}…")
    s4, e4 = section(L, "## 4)")
    if not any(LIMIT_FORM_MERGED in l for l in L[s4:e4]):
        prob("C1 00_목록.md", "4) 한계에 일반 부서 인원 공통 꼴 줄이 나오지 않음")
    info(f"C1 한계 줄: 회사 md 0) {n_lim}줄 모두 공통 꼴 확인 대상 · 회사 md 7) 앞·00_목록 의 「공시되지 않」 류 단정은 문제로 셈")

    # C2 공시인원 「추출 범위에 없음」 행의 찾은 방법 자리
    hu = MERGED["조직단위"][1]
    kp, kd, kb, ks = (hu.index("공시인원(원문, 없으면 「추출 범위에 없음」)"), hu.index("인원_내역(원문)"),
                      hu.index("인원_기준일"), hu.index("인원_출처"))
    c2 = OrderedDict((co, [0, 0]) for co in COS)
    for r, x in enumerate(data["조직단위"], start=2):
        v = x[kp]
        if not v.startswith("추출 범위에 없음"):
            continue
        wiwon = v.startswith("추출 범위에 없음(직원 인원)")
        c2[x[0]][1 if wiwon else 0] += 1
        if not re.search(r"찾은 방법\s?:", x[ks]):
            prob(f"C2 {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 공시인원 「추출 범위에 없음」인데 인원_출처에 「찾은 방법:」이 나오지 않음")
        if "찾은 방법" in x[kd]:
            prob(f"C2 {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 인원_내역(원문 열)에 「찾은 방법」 작업 글")
        if not wiwon and x[kb].strip():
            prob(f"C2 {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 공시인원 「추출 범위에 없음」 행인데 인원_기준일이 빈칸이 아님(00_목록 5-1 설명과 다름)")
    info("C2 공시인원 「추출 범위에 없음」 행(인원_출처 「찾은 방법:」 · 인원_내역 작업 글 0) — 일반 / 「(직원 인원)」 위원회 행: "
         + " · ".join(f"{co} {a}/{b}" for co, (a, b) in c2.items()))

    # C3 맡은 임원 「추출 범위에 없음」 행의 임원_겸직
    ki, km, kj = hu.index("대응_임원(성명·직위)"), hu.index("대응_방식(이름 일치/(판단)/추출 범위에 없음)"), hu.index("임원_겸직(원문: 겸직회사·직위·선임일·상근)")
    c3 = OrderedDict((co, 0) for co in COS)
    for r, x in enumerate(data["조직단위"], start=2):
        if not (x[km].startswith("추출 범위에 없음") or x[ki].startswith("추출 범위에 없음")):
            continue
        c3[x[0]] += 1
        if x[kj] != NOMAP_CONC:
            prob(f"C3 {x[0]}", f"조직단위 레코드 {r} 「{x[5]}」: 임원_겸직 「{x[kj][:40]}」 ≠ 공통 꼴 「{NOMAP_CONC}」")
    info("C3 맡은 임원 「추출 범위에 없음」 행의 임원_겸직 공통 꼴 확인: " + " · ".join(f"{co} {n}" for co, n in c3.items()))

    # C4 기준일 칸
    hs = MERGED["지원조직"][1]
    cols = [("조직단위", hu.index("조직도_기준일(원문)")), ("조직단위", kb), ("지원조직", hs.index("기준일"))]
    n_seg = n_jud = 0
    for kind, j in cols:
        cname = MERGED[kind][1][j]
        for r, x in enumerate(data[kind], start=2):
            for ln in x[j].split("\n"):
                if not ln.strip():
                    continue
                where = f"{kind} 레코드 {r} ({x[0]}) 「{cname}」"
                if not re.search(r"\d{4}", ln):   # 날짜 글은 줄마다(원문 「2025년말 기준 / 준법감시인 제외」처럼 「 / 」가 원문인 줄이 있어 조각마다 보지 않음)
                    prob(f"C4 {x[0]}", f"{where}: 날짜 글(숫자 4자리)이 나오지 않는 줄 「{ln[:60]}」")
                for sg in split_top(ln):
                    sg = sg.strip()
                    if not sg:
                        continue
                    n_seg += 1
                    if "판단" in sg:
                        n_jud += 1
                        m = JUD.match(sg)
                        if not m or not JUD_BODY.match(m.group("body")):
                            prob(f"C4 {x[0]}", f"{where}: (판단) 조각이 공통 꼴이 아님 「{sg[:90]}」")
                    elif OLD_DATE.search(sg):
                        prob(f"C4 {x[0]}", f"{where}: 「판단」 없이 관찰만 적은 옛 꼴 「{sg[:80]}」")
    info(f"C4 기준일 칸 조각 {n_seg}개(조직도_기준일·인원_기준일·지원조직 기준일) 가운데 (판단) 조각 {n_jud}개 — 모두 날짜 글 + 공통 꼴이어야 함")

    # C5 열 이름 한 꼴
    ok = OrderedDict()
    allowed = {"조직단위": {19}, "임원겸직": {13, 16}, "지원조직": {8}}
    for kind, (_, head) in MERGED.items():
        ok[kind] = 0
        for co in COS:
            h = rcsv(os.path.join(ORG, f"{co}_{kind}.csv"))[0]
            if len(h) not in allowed[kind] or h != head[:len(h)]:
                bad = [f"{i}:「{a}」≠「{b}」" for i, (a, b) in enumerate(zip(h, head)) if a != b]
                prob(f"C5 {co}", f"{kind} CSV 머리가 합본 머리와 다름(열 {len(h)}) {' '.join(bad)[:120]}")
            else:
                ok[kind] += 1
    if SAME_COL:
        prob("C5", f"열 이름 맞춤 표 SAME_COL 이 비어 있지 않음: {sorted(SAME_COL)}")
    info("C5 회사 CSV 머리 = 합본 머리(맞춤 표 없이): " + " · ".join(f"{k} {n}/8" for k, n in ok.items()))


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
        check_eopseum(data)
        check_nomap(data)
        check_dates(data)
        check_common(data)
    check_fragments()
    check_secrets_files()
    check_old()
    lines = [f"# verify14 — 14차 합본 검증 ({now})", "",
             "검사: G 그룹 검증 4개 실행 · J 합본 = 회사 CSV 이어 붙임(+멱등) · S 00_목록 2절 숫자 = CSV 다시 셈 · "
             "E 「없음」 단정(원문 칸·「」 인용 밖) 0 · N 맡은 임원 「추출 범위에 없음」 행의 찾은 방법 · D 기준일 칸 빈칸 0 · "
             "C 8개사 공통 꼴(한계 줄 단정 0·찾은 방법 자리·임원_겸직 한 꼴·기준일 (판단) 꼴·열 이름 한 꼴) · "
             "Q 00_목록 「」 조각 ↔ 회사 md·CSV · K 키·OC 값이 파일에 나오지 않음 · F 산출 폴더 PDF·PNG·HWP 0개 · B 1~13차 = b4ecf46", ""]
    lines += ["## 기록"] + [f"- {x}" for x in INFO] + [""]
    lines += [f"## 문제 {len(PROBS)}건"] + [f"- {x}" for x in PROBS] + [""]
    lines.append("결과: " + ("통과(exit 0)" if not PROBS else "실패(exit 1)"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    for x in INFO:
        if x.startswith(("G ", "J ", "E ", "N ", "D ", "C", "K ", "F ", "B ")):
            print(x[:200])
    print(f"S 2절 회사 {sum(1 for x in INFO if x.startswith('S '))}행 확인 · Q {next((x for x in INFO if x.startswith('Q ')), '')}")
    for x in PROBS[:30]:
        print("문제:", x[:220])
    print(f"문제 {len(PROBS)}건 · 결과 dart_out/org14/verify14.txt")
    return 0 if not PROBS else 1


if __name__ == "__main__":
    sys.exit(main())
