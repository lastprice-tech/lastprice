# -*- coding: utf-8 -*-
"""정식 명칭 확정 — API 검색 결과로만 정한다. 모호하면 멈춘다(요청서 1절).

법령(법률·시행령·시행규칙)
  현행법령(시행일) 목록 `lawSearch target=eflaw` 를 쓴다.
    nw=3 → 현행, nw=2 → 시행예정 (실측: 보험업법 시행령 현행 1 · 시행예정 2)
  3단은 이름 규칙으로 찾는다: 「X」, 「X 시행령」, 「X 시행규칙」. 체계도가 교차 확인한다.
  ★ 같은 법령일련번호가 현행과 시행예정에 동시에 쓰인다(보험업법 시행령 285553 이
    2026-04-21 현행이자 2027-01-01 시행예정). 그래서 버전 키는 (MST, 시행일) 쌍이다.

행정규칙
  `lawSearch target=admrul`. 현행만 쓴다.

■ 일치 판정
  - 정확일치 → 그대로
  - 공백만 다름 → 일치로 보되 정식 표기를 기록한다(「금융지주회사감독규정 시행세칙」 vs
    API 「금융지주회사감독규정시행세칙」). 글자는 같고 띄어쓰기만 다르다.
  - 그 밖 → **모호**. 후보를 보여주고 수집하지 않는다.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import targets as T

TODAY = "20260929"


def _norm(s):
    return re.sub(r"\s+", "", s or "")


def _rows(xml_bytes, item_tag):
    root = ET.fromstring(xml_bytes)
    out = []
    for it in root.iter(item_tag):
        out.append({c.tag: (c.text or "").strip() for c in it})
    total = (root.findtext("totalCnt") or "").strip()
    return out, total


def _search(client, target, query, **extra):
    """모든 페이지. display=100."""
    rows, page = [], 1
    item = "law" if target in ("law", "eflaw") else target
    while True:
        st, body, murl, host = client.api("lawSearch.do", target=target, type="XML",
                                          query=query, display="100", page=str(page), **extra)
        if not body:
            raise RuntimeError("검색 실패: %s" % murl)
        r, total = _rows(body, item)
        rows += r
        if not r or len(rows) >= int(total or 0) or page >= 20:
            break
        page += 1
    return rows


def _match(rows, want, key):
    exact = [r for r in rows if r.get(key, "") == want]
    if exact:
        return exact, "정확일치"
    loose = [r for r in rows if _norm(r.get(key, "")) == _norm(want)]
    if loose:
        return loose, "공백무시일치"
    return [], ""


def resolve_law(client, req_name):
    """→ {tier: {'현행': row|None, '시행예정': [rows], '일치': str}}, 상태, 후보."""
    cur = _search(client, "eflaw", req_name, nw="3")
    pend = _search(client, "eflaw", req_name, nw="2")
    out, cands = {}, []
    for tier in T.TIERS:
        want = req_name + T.TIER_SUFFIX[tier]
        c, how = _match(cur, want, "법령명한글")
        p, _ = _match(pend, want, "법령명한글")
        out[tier] = {"현행": c[0] if c else None, "현행후보수": len(c),
                     "시행예정": p, "일치": how}
    status = "확정"
    if not out["법률"]["현행"]:
        status = "모호"
        cands = sorted({r.get("법령명한글", "") for r in cur})[:15]
    elif any(v["현행후보수"] > 1 for v in out.values()):
        status = "모호"
        cands = ["%s ×%d" % (req_name + T.TIER_SUFFIX[t], v["현행후보수"])
                 for t, v in out.items() if v["현행후보수"] > 1]
    return out, status, cands


def resolve_rule(client, req_name):
    rows = _search(client, "admrul", req_name)
    cur = [r for r in rows if (r.get("현행연혁구분") or "현행") == "현행"]
    m, how = _match(cur, req_name, "행정규칙명")
    if len(m) == 1:
        return m[0], "확정", how, []
    cands = sorted({"%s (%s·%s)" % (r.get("행정규칙명", ""), r.get("행정규칙종류", ""),
                                     r.get("소관부처명", "")) for r in (m or cur)})[:15]
    return None, "모호", how, cands
