# -*- coding: utf-8 -*-
"""11차 7-1·7-3 법령 원문 — 10차 web10_law 와 같은 방식(7차 lawclient·resolve, Open API XML 의 조문·항·호·목 글을 그대로).

    python3 scripts/dart/web11_law.py laws      # 현행 판 받기 → handoff/법령원문_11차/*.md, dart_out/risk11/법령원문_11차.csv
    python3 scripts/dart/web11_law.py annex     # 금융지주회사법 시행령 별표 4·5 본문 → 법령원문_11차/금융지주회사법시행령_별표4·5.md
    python3 scripts/dart/web11_law.py define    # 7-1 원문_11차/특수관계인_정의대조.csv

· 이미 받은 XML(dart_out/raw/web9·web10·web11/law)에 같은 이름·같은 일련번호가 있으면 다시 받지 않고 옮기기만 한다.
· 시행예정 판은 일련번호·시행일만 기록(받지 않음). 렌더링 PDF 는 만들지 않는다(사용자: 첨부 묶음에 PDF 불필요).
· 별표·서식은 제목만 — 금융지주회사법 시행령 별표 4·5 만 본문(Open API 별표내용 글, 없으면 파일의 글자 층, 없으면 「미확인(문서 읽기 불가)」).
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "law"))
import web10_law as L10  # noqa: E402
from web11 import RAW, WORK, OUT, LAWOUT, save, now, write_csv  # noqa: E402

LAWDIR = os.path.join(RAW, "law")
LEDGER = os.path.join(LAWDIR, "_call_log.csv")
LIST_CSV = os.path.join(WORK, "법령원문_11차.csv")
LAW7 = os.path.join("law_archive", "00_manifest", "law_list.csv")
FHC, FHC_D, BANK_D = "금융지주회사법", "금융지주회사법 시행령", "은행법 시행령"
# (요청명, 종류, md 파일, 작업) — 7-3 순서: 원문이 전혀 없던 두 건 먼저
LAWS = [
    ("외부감사 및 회계 등에 관한 규정", "rule", "외부감사및회계등에관한규정.md", "7-3"),
    ("금융복합기업집단의 감독에 관한 법률", "law", "금융복합기업집단법.md", "7-3"),
    (FHC, "law", "금융지주회사법.md", "7-1·7-3"),
    (FHC_D, "decree", "금융지주회사법시행령.md", "7-1·7-3"),
    ("금융지주회사감독규정시행세칙", "rule", "금융지주회사감독규정시행세칙.md", "7-3"),
    ("보험업법 시행령", "decree", "보험업법시행령.md", "7-3"),
    (BANK_D, "decree", "은행법시행령.md", "7-1"),
    ("은행법", "law", "은행법.md", "7-1(시행령 제1조의4 가 인용하는 법 제2조제1항제8호)"),
]
KINDNAME = {"law": "법률", "decree": "시행령", "rule": "행정규칙"}
COLS = ["법령명", "종류", "일련번호", "시행일자", "공포일자", "파일", "sha256", "note",
        # 추적·재사용 열(10차 목록과 같은 이름 — law_compact.py 가 읽는다)
        "name", "kind", "작업", "상태", "법령ID", "소관", "시행예정판", "원문XML", "xml_sha256", "텍스트", "텍스트_sha256",
        "출처URL", "collected_at", "차7_일련번호", "차7_시행일자", "차7과같은판", "재사용"]


def _client():
    import lawclient
    return lawclient.LawClient(LEDGER)


def _have(name, serial):
    """이미 받은 XML(9·10·11차 원본 폴더)에서 같은 이름·일련번호를 찾는다(시행예정·재확인 파일 포함)."""
    stem = name.replace(" ", "")
    for d in ("web9", "web10", "web11"):
        for p in glob.glob(os.path.join("dart_out", "raw", d, "law", "%s_%s*.xml" % (stem, serial))):
            return p
    return ""


def laws():
    import resolve
    client = _client()
    prev = {r["정식명"]: r for r in csv.DictReader(open(LAW7, encoding="utf-8-sig"))} if os.path.exists(LAW7) else {}
    rows, cache = [], {}
    for name, kind, mdname, task in LAWS:
        rec = {c: "" for c in COLS}
        rec.update(법령명=name, name=name, 종류=KINDNAME[kind], kind=KINDNAME[kind], 작업=task)
        try:
            if kind == "rule":
                cur, st, how, cands = resolve.resolve_rule(client, name)
                if not cur:
                    raise RuntimeError("현행 판을 하나로 못 정함(%s): %s" % (st, cands[:5]))
                sn, ef, pd = cur.get("행정규칙일련번호", ""), cur.get("시행일자", ""), cur.get("발령일자", "")
                rec.update(법령ID=cur.get("행정규칙ID", ""), 소관=cur.get("소관부처명", ""), 시행예정판="(행정규칙 — 현행만 조회)")
                if how != "정확일치":
                    rec["note"] += "이름 일치 방식: %s(API 표기 「%s」) · " % (how, cur.get("행정규칙명", ""))
            else:
                base = name.replace(" 시행령", "")
                if base not in cache:
                    cache[base] = resolve.resolve_law(client, base)
                res, st, cands = cache[base]
                tier = res.get("법률" if kind == "law" else "시행령", {})
                cur = tier.get("현행")
                if not cur:
                    raise RuntimeError("현행을 못 찾음(%s): %s" % (st, cands[:5]))
                sn, ef, pd = cur.get("법령일련번호", ""), cur.get("시행일자", ""), cur.get("공포일자", "")
                rec.update(법령ID=cur.get("법령ID", ""), 소관=cur.get("소관부처명", ""),
                           시행예정판=" ; ".join("%s(시행 %s, 공포 %s)" % (p.get("법령일련번호", ""), p.get("시행일자", ""),
                                                                   p.get("공포일자", "")) for p in tier.get("시행예정") or [])
                           or "없음")
            rec.update(일련번호=sn, 시행일자=ef, 공포일자=pd)
            old = _have(name, sn)
            if old:                                   # 이미 받은 원본 — 다시 받지 않는다
                xb = open(old, "rb").read()
                meta = json.load(open(old + ".meta.json", encoding="utf-8")) if os.path.exists(old + ".meta.json") else {}
                p, murl, when = old, meta.get("출처URL", ""), meta.get("fetched_at", "")
                rec["재사용"] = ("N(11차 수집 원본 %s)" % old if os.sep + "web11" + os.sep in old
                               else "Y(이전 차수 원본 %s — 다시 받지 않음)" % old)
            else:
                if kind == "rule":
                    sc, xb, murl, host = client.api("lawService.do", target="admrul", ID=sn, type="XML")
                else:
                    sc, xb, murl, host = client.api("lawService.do", target="eflaw", MST=sn, efYd=ef, type="XML")
                if client.count_oc(xb):
                    raise RuntimeError("응답 본문에 인증값이 들어 있음 — 저장하지 않음")
                p, m = save("law", "%s_%s.xml" % (name.replace(" ", ""), sn), xb,
                            dict(출처URL=murl, http_status=sc, fetched_at=now()))
                when = m["fetched_at"]
                rec["재사용"] = "N"
            sha = hashlib.sha256(xb).hexdigest()
            rec.update(원문XML=p, xml_sha256=sha, sha256=sha, 출처URL=murl, collected_at=when)
            md = ["# %s" % name, "",
                  "- 종류: %s · 일련번호 %s · 시행일자 %s · 공포/발령일자 %s · 소관 %s"
                  % (rec["kind"], sn, ef, pd, rec["소관"]),
                  "- 출처: 국가법령정보센터 Open API %s (OC=*** 가림) · 수집일 %s" % (murl, when),
                  "- 원문 XML sha256 %s — 아래 글은 그 XML 의 %s 글을 문서 순서대로 옮긴 것(글자 수정 없음). "
                  "법령에는 쪽이 없어 위치는 조문 번호로 적는다. 별표·서식은 제목만." % (
                      sha, "조문·부칙·별표제목" if kind == "rule" else "조문·항·호·목·부칙·별표제목"),
                  "- 시행예정 판(받지 않음, 기록만): %s" % rec["시행예정판"],
                  "", "---", "", L10.md_text(xb, "rule" if kind == "rule" else "law")]
            os.makedirs(LAWOUT, exist_ok=True)
            mdp = os.path.join(LAWOUT, mdname)
            body = "\n".join(md) + "\n"
            with open(mdp, "w", encoding="utf-8") as f:
                f.write(body)
            rec.update(파일=mdp, 텍스트=mdp, 텍스트_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest())
            pv = prev.get(name, {})
            rec.update(차7_일련번호=pv.get("법령일련번호", ""), 차7_시행일자=pv.get("시행일자", ""))
            rec["차7과같은판"] = ("Y" if pv and pv.get("법령일련번호") == sn else
                              "N(7차 이후 바뀐 판)" if pv else "7차 목록에 없음")
            if pv and pv.get("법령일련번호") and pv.get("법령일련번호") != sn:
                rec["note"] += "7차 수집 판 %s(시행 %s) → 현행 %s(시행 %s) · " % (
                    pv["법령일련번호"], pv.get("시행일자", ""), sn, ef)
            if rec["시행예정판"] not in ("없음", "(행정규칙 — 현행만 조회)"):
                rec["note"] += "시행예정 판 있음(받지 않음): %s · " % rec["시행예정판"]
            rec["상태"] = "OK"
        except Exception as e:                       # noqa: BLE001
            rec["상태"] = "실패"
            rec["note"] += client.mask("%s: %s" % (type(e).__name__, e))[:300]
        rec["note"] = rec["note"].rstrip(" ·")
        print("  %-30s %s %s %s %s" % (name, rec["상태"], rec["일련번호"], rec["시행일자"], rec["note"][:90]))
        rows.append(rec)
    write_csv(LIST_CSV, COLS, rows)
    print("법령 %d건 · OK %d · API 호출 %d" % (len(rows), sum(r["상태"] == "OK" for r in rows), client.n_calls))


def listed():
    return {r["name"]: r for r in csv.DictReader(open(LIST_CSV, encoding="utf-8-sig"))}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"laws": laws}.get(cmd)
    if cmd == "annex":
        import web11_more
        web11_more.annex()
    elif cmd == "define":
        import web11_more
        web11_more.define()
    elif fn:
        fn()
    else:
        print(__doc__)
