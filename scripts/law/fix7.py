# -*- coding: utf-8 -*-
"""7차 최종 교차 검증(에이전트 4렌즈)에서 확인된 결함을 **이미 받은 아카이브에** 반영한다.

    python3 scripts/law/fix7.py          # 전부(첨부파일만 API 호출, 나머지는 저장된 XML 로)

고치는 것 (코드는 collect·render·runall 에 이미 반영 — 앞으로 새로 받으면 처음부터 이렇게 된다)
  1. 체계도: 자치법규(조례) 노드가 이름 없는 노드 하나로 뭉쳤던 것 → 저장된 가림 XML 로 다시
     해석해 체계도.json·md·pdf·parts·hierarchy.json 재생성
  2. API 가 시행예정으로 줬지만 시행일이 오늘·현행 이전인 지난 판(조세특례제한법 시행령
     283625 @20260701) → 요청 범위(현행+시행예정) 밖이므로 파일을 치우고 law_list 에 사유 기록
  3. 번호 없는 별표(원문 「[별표]」)를 「별표0」으로 적던 것 → 번호 비움·파일명 변경,
     제목은 별표제목문자열(엔티티 없는 꼴), 「…로 이동」 자리표시는 이동별표
  4. 행정규칙 첨부: 첫 파일 하나만 「전체 원본」이라 적던 것 → 첨부 **전부**를 원본 그대로
     (zip 을 hwpx 로 적던 것도 바로잡음)
  5. 본문 PDF 전부 다시 찍기: 조문참고자료(시행일·유효기간·위헌 주석 등)·조문별 시행일 추가,
     숫자 문자 참조 표시, 번호 없는 별표 목록 표기
  6. law_list 시행규칙 「없음」 비고(자치법규 제외) 갱신 → 병합·zip
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect       # noqa: E402
import lawclient     # noqa: E402
import render        # noqa: E402
import resolve       # noqa: E402
import runall        # noqa: E402
import targets as T  # noqa: E402

log = runall.log
REPO = collect.REPO


def parts():
    for key in runall.order_keys():
        d = runall.part_done(key)
        if d:
            yield key, d


def load(key):
    mp, rows = runall._load_part(key)
    lp = os.path.join(runall.PARTS, key + ".lawlist.csv")
    lrows = list(csv.DictReader(open(lp, encoding="utf-8-sig")))
    return mp, rows, lp, lrows


def save(key, mp, rows, lp, lrows, d=None):
    collect.write_csv(mp, rows, collect.MANIFEST_COLS)
    collect.write_csv(lp, lrows, collect.LAWLIST_COLS)
    if d is not None:
        with open(os.path.join(runall.PARTS, key + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)


def fix_hierarchy(key, d, rows):
    """1. 체계도 재해석(자치법규 노드)."""
    xrow = [r for r in rows if r["유형"] == "체계도원문XML"]
    if not xrow:
        return 0
    xb = open(os.path.join(REPO, xrow[0]["파일경로"]), "rb").read()
    nodes, edges, lines = collect.parse_stmd(xb)
    top = d["법률"]
    d0 = os.path.dirname(os.path.join(REPO, xrow[0]["파일경로"]))
    js = {"법령": top, "원천": "lsStmd", "노드": list(nodes.values()),
          "간선": [{"from": a, "to": b, "관계": r} for a, b, r in edges]}
    jp, mdp, pp = (os.path.join(d0, n) for n in ("체계도.json", "체계도.md", "체계도.pdf"))
    collect.write(jp, json.dumps(js, ensure_ascii=False, indent=1).encode("utf-8"))
    collect.write(mdp, collect.hierarchy_md(top, nodes, edges, lines).encode("utf-8"))
    law = [r for r in rows if r["유형"] == "체계도"][0]
    npg, h = collect._swap_render(render.hierarchy_html(lines, top, law["시행일자"],
                                                        law["법령일련번호"]), pp)
    for r in rows:
        if r["유형"] == "체계도":
            p_ = os.path.join(REPO, r["파일경로"])
            r["sha256"] = collect.sha256(open(p_, "rb").read())
            if r["원본형식"] == "PDF":
                r["페이지수"] = npg
    before = len(d["노드"])
    d["노드"] = list(nodes.values())
    d["간선"] = [{"from": a, "to": b, "관계": r} for a, b, r in edges]
    d["시행규칙급_체계도노드"] = [n for n in nodes.values() if n["분류"] == "법령"
                              and n["종류"] not in ("법률", "대통령령")]
    return len(nodes) - before


def fix_past_pending(key, rows, lrows):
    """2. 지난 판을 시행예정으로 받은 것 치우기."""
    cur = {}
    for r in lrows:
        if r["상태"] == "확정" and r["시행예정여부"] == "N":
            cur[r["계층"]] = r["시행일자"]
    drop = set()
    for r in lrows:
        if r["상태"] == "확정" and r["시행예정여부"] == "Y" and \
                r["시행일자"] <= max(resolve.TODAY, cur.get(r["계층"], "")):
            drop.add((r["계층"], r["법령일련번호"], r["시행일자"]))
            r.update(상태="제외(지난 판)", 시행예정여부="N",
                     비고=collect.PAST_NOTE % (r["시행일자"], resolve.TODAY, cur.get(r["계층"], "")))
    if not drop:
        return rows, []
    keep, gone = [], []
    for r in rows:
        if (r["계층"], r["법령일련번호"], r["시행일자"]) in drop and r["시행예정여부"] == "Y":
            if r["파일경로"] and os.path.exists(os.path.join(REPO, r["파일경로"])):
                os.remove(os.path.join(REPO, r["파일경로"]))
            gone.append(r)
        else:
            keep.append(r)
    return keep, gone


def fix_annexes(rows):
    """3. 번호·제목·이동별표. 번호가 바뀌면 파일명도 바꾼다."""
    renamed, moved, titled = 0, 0, 0
    for x in [r for r in rows if r["유형"] == "원문XML" and r["파일경로"]]:
        xb = open(os.path.join(REPO, x["파일경로"]), "rb").read()
        units = collect.annex_list(xb)
        arows = [r for r in rows if r["유형"] in ("별표", "서식") and runall._vkey(r) == runall._vkey(x)]
        assert len(units) == len(arows), x["파일경로"]
        for a, r in zip(units, arows):
            if r["번호"] != a["번호"]:
                label = collect.slug(a["구분"]) or collect.annex_sub(a)
                old = os.path.join(REPO, r["파일경로"])
                d, b = os.path.split(old)
                tag_old, tag_new = "_%s%s_" % (label, r["번호"]), "_%s%s_" % (label, a["번호"])
                assert tag_old in b, (b, tag_old)
                i = b.index(tag_old)
                new = os.path.join(d, b[:i] + tag_new + b[i + len(tag_old):])
                assert not os.path.exists(new), new
                os.replace(old, new)
                r.update(번호=a["번호"], 파일경로=collect.rel(new))
                renamed += 1
            if r["제목"] != a["제목"]:
                r["제목"] = a["제목"]
                titled += 1
            if r["상태"] == "OK" and collect.MOVED.search(a["제목"]) and len(a["제목"]) < 80:
                r["상태"] = "이동별표"
                moved += 1
    return renamed, titled, moved


def fix_attachments(client, rows):
    """4. 행정규칙 첨부 전부."""
    out, n_old, n_new = [], 0, 0
    for r in rows:
        if r["유형"] == "첨부원본":
            if r["파일경로"] and os.path.exists(os.path.join(REPO, r["파일경로"])):
                os.remove(os.path.join(REPO, r["파일경로"]))
            n_old += 1
        else:
            out.append(r)
    new_rows = []
    for x in [r for r in out if r["유형"] == "원문XML" and r["계층"] == "행정규칙"]:
        xb = open(os.path.join(REPO, x["파일경로"]), "rb").read()
        stem = os.path.basename(x["파일경로"])[:-len("_원문.xml")]
        base = os.path.dirname(os.path.join(REPO, x["파일경로"]))
        meta = {k: x[k] for k in ("그룹", "상위법", "계층", "정식명", "법령ID", "법령일련번호",
                                  "공포일자", "공포번호", "시행일자", "시행예정여부", "소관부처")}
        got = runall.fetch_attachments(client, runall.attachments(xb), os.path.join(base, "첨부"),
                                       stem, meta)
        new_rows += got
        n_new += len(got)
    # 원래 자리(본문 다음)에 끼워 넣는다
    res = []
    for r in out:
        res.append(r)
        if r["유형"] == "본문" and r["계층"] == "행정규칙":
            res += [a for a in new_rows if runall._vkey(a) == runall._vkey(r)]
    return res, n_old, n_new


def rerender_bodies(rows):
    """5. 본문 다시 찍기."""
    n = 0
    for x in [r for r in rows if r["유형"] == "원문XML" and r["파일경로"]]:
        runall._rebody(rows, x, x["계층"] == "행정규칙")
        n += 1
    return n


def fix_absence_notes(d, lrows):
    """6. 시행규칙 「없음」 비고."""
    import re
    n = 0
    for r in lrows:
        if r["상태"] == "없음" and r["계층"] == "시행규칙" and d.get("시행규칙급_체계도노드") is not None:
            law = r["정식명"][:-len(" 시행규칙")] if r["정식명"].endswith(" 시행규칙") else r["정식명"]
            note = collect.rule_absence_note(law, d["시행규칙급_체계도노드"])
            m = re.search(r"사용자 확인\(.*$", r["비고"] or "")
            if m:
                note += " · " + m.group(0)
            if note != r["비고"]:
                r["비고"] = note
                n += 1
    return n


def main():
    t0 = time.time()
    client = lawclient.LawClient(os.path.join(collect.MAN, "call_log.csv"))
    for key, d in list(parts()):
        mp, rows, lp, lrows = load(key)
        msg = []
        if "노드" in d:
            dn = fix_hierarchy(key, d, rows)
            msg.append("체계도 노드 %+d" % dn)
            rows, gone = fix_past_pending(key, rows, lrows)
            if gone:
                msg.append("지난 판 제외 %d행" % len(gone))
            msg.append("없음 비고 %d" % fix_absence_notes(d, lrows))
        rn, tt, mv = fix_annexes(rows)
        msg.append("별표 번호 %d·제목 %d·이동 %d" % (rn, tt, mv))
        if key.startswith("B-2"):
            rows, n_old, n_new = fix_attachments(client, rows)
            msg.append("첨부 %d→%d" % (n_old, n_new))
        nb = rerender_bodies(rows)
        msg.append("본문 %d" % nb)
        save(key, mp, rows, lp, lrows, d)
        log("%s %s — %s" % (key, d.get("법률") or d.get("정식명"), " · ".join(msg)))
    runall.merge()
    runall.zip_all()
    log("보정 끝 — %.1f분 · 호출 %d" % ((time.time() - t0) / 60, client.n_calls))
    return 0


if __name__ == "__main__":
    sys.exit(main())
