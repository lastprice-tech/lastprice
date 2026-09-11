# -*- coding: utf-8 -*-
"""오프라인 셀프테스트 — 네트워크도 API 키도 없이 collect→emit 전 구간을 검증한다."""
from __future__ import annotations

import csv
import glob
import json
import os
import shutil
import sys

import client as C
import config
import corpcode
import docparse
import emit
import fixtures
import phase0
import phase1
import phase2

FAKE_KEY = "FAKEKEY_0123456789abcdef0123456789abcdef0000"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("    %s %s%s" % ("✓" if cond else "✗", name, ("  — " + detail) if detail and not cond else ""))
    return cond


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def mkclient(out, transport=None, **kw):
    kw.setdefault("delay", 0.0)
    return C.DartClient(out, transport=transport, require_key=False, **kw)


# ── 전송 계층 단위 테스트 ─────────────────────────────────────────────────
def transport_cases(out_root):
    print("\n  [1] 전송·상태 처리")
    out = os.path.join(out_root, "t_transport")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)

    def body(b):
        return lambda url, timeout: (200, b if isinstance(b, bytes) else b.encode(), {})

    # 013 은 정상 응답이다 — 재시도하지 않고 캐시한다
    calls = {"n": 0}

    def t013(url, timeout):
        calls["n"] += 1
        return 200, b'{"status":"013","message":"\xec\xa1\xb0\xed\x9a\x8c\xeb\x90\x9c \xeb\x8d\xb0\xec\x9d\xb4\xed\x83\x80\xea\xb0\x80 \xec\x97\x86\xec\x8a\xb5\xeb\x8b\x88\xeb\x8b\xa4."}', {}
    c = mkclient(out, t013)
    r = c.call("empSttus", {"corp_code": "00100001", "bsns_year": "2021", "reprt_code": "11011"})
    check("013 은 재시도하지 않는다", calls["n"] == 1, "호출 %d회" % calls["n"])
    check("013 은 캐시된다", os.path.exists(os.path.join(out, "raw/empSttus/00100001_2021_11011.json")))
    c2 = mkclient(out, t013)
    r2 = c2.call("empSttus", {"corp_code": "00100001", "bsns_year": "2021", "reprt_code": "11011"})
    check("013 재실행은 캐시 적중", r2.cached and calls["n"] == 1)
    check("캐시 적중 시 최초 조회시각 유지", r2.fetched_at == r.fetched_at)

    # 020 은 캐시되면 안 된다 — 한 번의 한도 초과가 '데이터 없음' 수천 건이 되는 걸 막는다
    out2 = os.path.join(out_root, "t_020")
    shutil.rmtree(out2, ignore_errors=True); os.makedirs(out2)
    c = mkclient(out2, body('{"status":"020","message":"요청 제한을 초과하였습니다."}'))
    try:
        c.call("empSttus", {"corp_code": "00100001", "bsns_year": "2021", "reprt_code": "11011"})
        ok = False
    except C.FatalDartError as e:
        ok = e.status == "020"
    check("020 은 즉시 중단", ok)
    check("020 은 캐시 경로에 쓰이지 않는다",
          not os.path.exists(os.path.join(out2, "raw/empSttus/00100001_2021_11011.json")))
    check("020 원본은 _transient 에 감사용으로 남는다",
          bool(glob.glob(os.path.join(out2, "raw/_transient/empSttus/*"))))
    check("RUN_ABORTED.txt 로 재개 방법을 남긴다",
          os.path.exists(os.path.join(out2, "RUN_ABORTED.txt")))

    # .json 인데 HTML/잘린 JSON
    for nm, payload in (("WAF HTML", "<html><body>blocked</body></html>"),
                        ("잘린 JSON", '{"status":"000","list":[{"a"')):
        o = os.path.join(out_root, "t_" + nm.split()[0])
        shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
        c = mkclient(o, body(payload))
        try:
            c.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
            ok = False
        except C.FatalDartError:
            ok = True
        check("%s 는 파싱하지 않고 중단" % nm, ok)

    # ZIP 자리에 XML 오류 본문
    o = os.path.join(out_root, "t_zipxml")
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    c = mkclient(o, body('<?xml version="1.0"?><result><status>014</status>'
                         '<message>파일이 존재하지 않습니다.</message></result>'))
    r = c.call("document", {"rcept_no": "20200101000001"})
    check("ZIP 자리의 XML 오류 본문에서 status 를 읽는다", r.status == "014", r.status)

    # status 000 인데 list 키가 없는 응답
    o = os.path.join(out_root, "t_nolist")
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    c = mkclient(o, body('{"status":"000","message":"정상"}'))
    r = c.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
    check("000 + list 키 없음을 이상으로 기록", r.anomaly == "empty_list_on_000", r.anomaly)

    # sha256 불일치 → 격리 후 재조회
    o = os.path.join(out_root, "t_corrupt")
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    c = mkclient(o, body('{"status":"000","message":"정상","list":[{"a":"1"}]}'))
    c.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
    p = os.path.join(o, "raw/empSttus/1_2021_11011.json")
    with open(p, "wb") as f:
        f.write(b'{"status":"000","message":"tampered","list":[]}')
    c2 = mkclient(o, body('{"status":"000","message":"정상","list":[{"a":"1"}]}'))
    r = c2.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
    check("변조된 캐시는 격리하고 재조회", (not r.cached) and len(r.rows()) == 1)
    check("격리본은 삭제하지 않고 보관",
          bool(glob.glob(os.path.join(o, "raw/_quarantine/empSttus/*.corrupt"))))

    # 사이드카 없는 반쪽 파일은 캐시 미스
    o = os.path.join(out_root, "t_partial")
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    os.makedirs(os.path.join(o, "raw/empSttus"))
    with open(os.path.join(o, "raw/empSttus/1_2021_11011.json"), "wb") as f:
        f.write(b'{"status":"000"')
    c = mkclient(o, body('{"status":"000","message":"정상","list":[{"a":"1"}]}'))
    r = c.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
    check("사이드카 없는 잔해는 캐시 미스로 처리", not r.cached)

    # Content-Length 불일치는 전송 오류
    o = os.path.join(out_root, "t_clen")
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    c = mkclient(o, lambda u, t: (200, b'{"status":"000","list":[]}', {"Content-Length": "9999"}))
    try:
        c.call("empSttus", {"corp_code": "1", "bsns_year": "2021", "reprt_code": "11011"})
        ok = False
    except C.FatalDartError:
        ok = True
    check("Content-Length 불일치는 응답으로 받지 않는다", ok)


# ── 전 구간 ───────────────────────────────────────────────────────────────
def pipeline(out_root):
    print("\n  [2] 픽스처 전 구간 (resolve → phase0 → phase1 → phase2 → emit)")
    out = os.path.join(out_root, "pipeline")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    fx = os.path.join(out_root, "_fixtures")
    shutil.rmtree(fx, ignore_errors=True)
    fixtures.build(fx)
    os.environ["DART_FIXTURE_DIR"] = fx
    os.environ["DART_API_KEY"] = FAKE_KEY
    try:
        c = mkclient(out)
        phase0.run(c, out, verbose=False)
        check("PHASE0_REPORT.md 생성", os.path.exists(os.path.join(out, "PHASE0_REPORT.md")))
        rep = open(os.path.join(out, "PHASE0_REPORT.md"), encoding="utf-8").read()
        check("탐침 ① 이 경계연도 2015 를 집어낸다", "= **2015**" in rep,
              rep[rep.find("**결론**"):][:200] if "**결론**" in rep else "")
        check("탐침 ② 가 감사보고서만 내는 법인을 짚는다",
              "신한이지손해보험" in rep and "**없음**" in rep)
        check("탐침 ③ 이 CSM 원문 필요를 결론낸다", "Phase 2 원문 파싱이 필요하다" in rep)

        entries = corpcode.load_corp_codes(out)
        # config.TARGETS 를 기준으로 삼는다 — 대상이 늘 때마다 테스트를 고칠 필요가 없다
        check("대상 법인 전부 해석", len(entries) == len(config.TARGETS),
              "해석 %d / 대상 %d" % (len(entries), len(config.TARGETS)))
        wm = [e for e in entries if e["label"] == "우리금융지주(구)"]
        wn = [e for e in entries if e["label"] == "우리금융지주"]
        check("동명 우리금융지주 2건이 서로 다른 corp_code 로 갈린다",
              bool(wm) and bool(wn) and wm[0]["corp_code"] != wn[0]["corp_code"])
        check("신 우리금융지주는 종목코드로 매칭", wn and wn[0]["resolved_by"] == "stock_code")
        # --only 로 일부만 돌려도 corp_codes.csv 의 나머지 법인이 살아 있어야 한다.
        # 덮어쓰면 emit 이 라벨을 못 붙여 원문추출 수십만 행이 빈칸이 된다.
        import corpcode as _cc
        subset = [e for e in entries[:2]]
        _cc.write_corp_codes(out, subset)
        after = _cc.load_corp_codes(out)
        check("--only 부분 실행이 corp_codes.csv 를 덮어쓰지 않는다",
              len(after) == len(entries), "%d → %d" % (len(entries), len(after)))
        check("정체성 교차검증 통과",
              all(e["identity_check"] in ("검증됨", "확인항목없음") for e in entries),
              ",".join("%s=%s" % (e["label"], e["identity_check"]) for e in entries
                       if e["identity_check"] not in ("검증됨", "확인항목없음")))

        c = mkclient(out)
        phase1.run(c, out, config.DEFAULT_YEARS, config.DEFAULT_HALF_YEARS, verbose=False)
        c = mkclient(out)
        phase2.run(c, out, verbose=False)
        paths = emit.emit_all(out, config.DEFAULT_YEARS, config.DEFAULT_HALF_YEARS)
        check("산출물 생성", len(paths) >= 14, "%d개" % len(paths))
    finally:
        os.environ.pop("DART_FIXTURE_DIR", None)
    return out


def assertions(out):
    print("\n  [3] 산출물 불변식")
    req = ["source_endpoint", "source_params", "rcept_no", "fetched_at", "status"]
    for p in sorted(glob.glob(os.path.join(out, "[0-9][0-9]*.csv"))):
        rows = read_csv(p)
        if not rows:
            continue
        missing = [c for c in req if c not in rows[0]]
        check("필수 출처 컬럼: %s" % os.path.basename(p), not missing, "누락 %s" % missing)

    fs = read_csv(os.path.join(out, "03_재무제표.csv"))
    check("union-of-keys 로 예상 밖 필드도 보존",
          bool(fs) and "unexpected_new_field" in fs[0])
    check("모든 재무 행에 raw_sha256", all(r.get("raw_sha256") for r in fs))
    check("accounting_std 는 추론임을 라벨링",
          bool(fs) and "accounting_std_inferred" in fs[0] and "inference_rule" in fs[0])
    y2022 = [r for r in fs if r["bsns_year"] == "2022"]
    y2023 = [r for r in fs if r["bsns_year"] == "2023"]
    check("IFRS4/IFRS17 이 보고서 연도로 갈린다",
          all(r["accounting_std_inferred"] == "IFRS4" for r in y2022)
          and all(r["accounting_std_inferred"] == "IFRS17" for r in y2023))

    lg = read_csv(os.path.join(out, "03b_재무제표_long.csv"))
    terms = {r["term_code"] for r in lg}
    check("분기·누적 term 키를 잃지 않는다",
          {"thstrm", "thstrm_add", "frmtrm", "frmtrm_q", "bfefrmtrm"} <= terms,
          "관측 %s" % sorted(terms))
    st = {r["parse_status"] for r in lg}
    check("빈칸의 의미를 분리 (dash/key_absent/ok)",
          {"ok", "dash", "key_absent"} <= st, "관측 %s" % sorted(st))
    neg = [r for r in lg if r["amount_raw"].startswith("△")]
    check("△ 표기를 음수로 파싱", bool(neg) and neg[0]["amount"].startswith("-"),
          neg[0]["amount"] if neg else "없음")
    paren = [r for r in lg if r["amount_raw"].startswith("(")]
    check("괄호 표기를 음수로 파싱", bool(paren) and paren[0]["amount"].startswith("-"))
    check("비교표시 플래그", {"Y", "N"} <= {r["is_comparative"] for r in lg})
    check("합병·회계 단절을 표시", any(r["comparability_break"] == "Y" for r in lg))

    b1 = read_csv(os.path.join(out, "07_회사채미상환잔액.csv"))
    b2 = read_csv(os.path.join(out, "08_신종자본증권미상환잔액.csv"))
    check("회사채와 신종자본증권의 만기구간 컬럼이 서로 다르다",
          bool(b1) and bool(b2)
          and ("yy1_excess_yy2_below" in b1[0]) and ("yy1_excess_yy2_below" not in b2[0])
          and ("yy20_excess_yy30_below" in b2[0]))

    own = read_csv(os.path.join(out, "12_지분관계.csv"))
    hw = [r for r in own if r["child_name"] == "한화손해보험"]
    check("지분 그래프에 부모-자식과 지분율", bool(hw) and hw[0]["trmend_qota_rt"] == "51.36")
    check("미매칭 자회사는 unmatched 로 라벨",
          any(r["child_match_method"] == "unmatched" for r in own))

    doc = read_csv(os.path.join(out, "11_원문추출.csv"))
    # 실측(동양생명 2024)에서 확인된 실패 모드: CSM 은 어떤 섹션 제목에도 없고
    # 회사에 따라 「보험계약마진」으로 쓴다. 제목 기준 매칭만으로는 통째로 놓친다.
    csm = [r for r in doc if r["kind"] == "table" and "보험계약마진" in r.get("cell_text", "")]
    check("제목에 없는 CSM(보험계약마진)을 표 내용으로 찾아낸다", bool(csm))
    check("표 내용 매칭임을 match_scope 로 표시",
          bool(csm) and csm[0]["match_scope"] in ("table", "title"),
          csm[0]["match_scope"] if csm else "")
    check("표 안에 있는 단위 표기도 원문 그대로 포착",
          bool(csm) and csm[0]["unit_hint"] == "(단위 : 백만원)",
          csm[0]["unit_hint"] if csm else "")
    idx = [r for r in doc if r["kind"] == "table_index"]
    check("표는 전개하지 않아도 색인 행을 남긴다(삭제 아님)",
          bool(idx) and any(r["table_extracted"] == "N" for r in idx),
          "전개 %s" % sorted({r["table_extracted"] for r in idx}))
    check("키워드 없는 표는 셀 전개를 생략",
          any(r["table_extracted"] == "N" and not r["table_matched_keyword"] for r in idx))
    # 제목으로도 걸리고 본문으로도 걸린 섹션에서 matched_keyword 는 제목 히트만 남긴다.
    # 그러면 본문 히트가 조용히 사라진다 — 실측(원문 103건)에서 섹션 155개가 그렇게
    # '자회사'·'자본비율'·'지급여력' 기록을 잃었다. 본문 히트는 별도 컬럼에 남아야 한다.
    # 픽스처 「가. 관계회사 및 자회사의 투자지분 현황」은 제목이 걸리면서 본문에
    # '계열회사'가 들어 있는 바로 그 경우다.
    both = [r for r in doc
            if r["kind"] == "text" and r["match_scope"] == "title"
            and r.get("body_matched_keyword")]
    check("제목·본문에 모두 걸린 섹션의 본문 키워드가 덮어써지지 않는다",
          any("계열회사" in r["body_matched_keyword"] for r in both),
          "body_matched_keyword 가 남은 행 %d개" % len(both))
    check("rowspan/colspan 을 격자 추론 없이 보존",
          any(r.get("colspan") == "2" for r in doc))
    check("TE/TU 셀 태그 인식", {"te", "tu"} <= {r.get("cell_tag") for r in doc})
    # DART 는 셀 내용을 <TD><P>…</P></TD> 로 감싸는 일이 흔하다. <P> 가 셀 버퍼를
    # 리셋하면 그 셀이 빈 값으로 나온다 (실측: 우리 2018 의 이중레버리지 정의가 통째로 사라졌다)
    check("<TD><P>텍스트</P></TD> 의 셀 내용이 보존된다",
          any(r.get("cell_text") == "한화손해보험" for r in doc))
    # DART 는 ZIP 멤버명 앞에 '/' 를 붙이기도 한다. traversal 로 오인해 거부하면
    # 유일한 본문 멤버가 버려져 원문이 통째로 비게 된다 (실측 69개 중 21개가 해당).
    # 2001년식 사업보고서는 '계열회사' 대신 '관계회사·자회사·기업집단'을 쓴다.
    # 출범 시 계열사 구조가 최우선 산출이라 구시대 어휘를 놓치면 안 된다.
    old = [r for r in doc if "관계회사 및 자회사" in r.get("section_title", "")]
    check("2000년대 초 표기(관계회사·자회사)도 섹션으로 잡는다", bool(old))
    # NFKC 가 ㆍ(U+318D)를 U+119E 로 바꿔 중점 표기 필터가 0건이 되던 버그
    check("중점·아래아 표기가 같은 값으로 정규화된다",
          docparse.normalize_for_match("교환·이전") == docparse.normalize_for_match("교환ㆍ이전")
          == docparse.normalize_for_match("교환\u119e이전"))
    check("구시대 표기는 제목으로 매칭된다",
          bool(old) and any(r["match_scope"] == "title" for r in old))
    slash_docs = {r["rcept_no"] for r in doc if r["member_selected"].startswith("/")}
    check("멤버명 선행 슬래시 ZIP 도 본문을 추출한다", bool(slash_docs),
          "선행 슬래시 문서에서 추출된 행 없음")
    check("섹션 매칭 실패에 대비해 문서 전문 보관",
          bool(glob.glob(os.path.join(out, "text/*/_full.txt"))))
    check("지분취득 추적 원문(주요사항보고서) 수집",
          os.path.exists(os.path.join(out, "raw/document/20160415000777.zip")))
    # 사업보고서가 0건인 법인은 감사보고서 원문으로 대체 수집되어야 한다
    ez = [r for r in doc if r["corp_label"] == "신한이지손해보험"]
    check("사업보고서 없는 법인은 감사보고서 원문으로 대체 수집",
          bool(ez), "신한이지손해보험 원문 행 %d" % len(ez))

    ms = read_csv(os.path.join(out, "99_미확보목록.csv"))
    codes = {r["reason_code"] for r in ms}
    check("미확보 사유를 코드로 분리", "api_013" in codes, "관측 %s" % sorted(codes))
    carrot = [r for r in ms if r["corp_label"] == "캐롯손해보험"
              and r["reason_code"] == "not_applicable_entity_window"]
    check("소멸 법인의 기간 밖 칸은 '누락'이 아니라 '해당없음'", bool(carrot))

    acc = read_csv(os.path.join(out, "00_계정과목목록.csv"))
    check("계정과목 고유값 목록 생성", bool(acc) and "years_seen" in acc[0])
    check("비표준 account_id 를 표시",
          any(r["account_id_is_standard"] == "N" for r in acc))
    check("보험사 계정(보험계약부채)이 목록에 있다",
          any(r["account_nm"] == "보험계약부채" for r in acc))

    print("\n  [4] 키 유출·멱등성")
    leaked = []
    for p in glob.glob(os.path.join(out, "**", "*"), recursive=True):
        if not os.path.isfile(p) or p.endswith((".zip", ".xlsx")):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                if FAKE_KEY in f.read():
                    leaked.append(os.path.relpath(p, out))
        except Exception:
            pass
    check("API 키가 어떤 산출물에도 남지 않는다", not leaked, ", ".join(leaked[:5]))
    log = read_csv(os.path.join(out, "call_log.csv"))
    check("call_log 의 URL 이 마스킹됨",
          bool(log) and all("crtfc_key=***" in r["url_redacted"] or not r["url_redacted"]
                            for r in log))
    check("call_log 에 run_id·script_sha 기록", bool(log) and log[0].get("run_id"))

    before = {}
    for p in glob.glob(os.path.join(out, "[0-9][0-9]*.csv")):
        before[p] = open(p, "rb").read()
    emit.emit_all(out, config.DEFAULT_YEARS, config.DEFAULT_HALF_YEARS)
    same = all(open(p, "rb").read() == b for p, b in before.items())
    check("emit 은 멱등 (두 번 돌려도 같은 결과)", same)


# ── 지주 전환 신고서 섹션 키워드 회귀 ─────────────────────────────────────
def conversion_section_cases():
    """2000년대 「주식교환ㆍ이전신고서」의 실제 제목이 SECTION_KEYWORDS 에 걸리는지.

    emit.emit_documents 는 키워드가 걸린 섹션만 내보낸다. 과거에 "주식이전의 목적"
    하나만 있어서 「1. 주식교환·이전의 목적」이 부분문자열로 걸리지 않았고, 그 결과
    신한 2004 · 하나 2005 · 한투 2005/2006 · 국민 2008 의 「목적」 섹션이 출력에서
    통째로 빠져 있었다. 아래 제목들은 전부 원문에서 실측한 문자열이다.
    """
    print("\n  [5] 지주 전환 신고서 섹션 키워드")

    # emit.emit_documents 의 규칙을 글자 그대로 옮긴다. 예전에는 여기에만
    # `normalize_for_match(k) and` 가드가 있어서, 빈 키워드가 섞여도 이 시험은 조용히
    # 넘어가고 emit 만 전 섹션을 매칭하는 상태가 됐다 — 시험이 본 코드보다 느슨하면
    # 시험이 아니다. 가드는 빼고, '빈 키워드가 없다'를 아래에서 따로 단언한다.
    def hits(title):
        t = docparse.normalize_for_match(title)
        return [k for k in config.SECTION_KEYWORDS
                if docparse.normalize_for_match(k) in t]

    normed = [docparse.normalize_for_match(k) for k in config.SECTION_KEYWORDS]
    check("SECTION_KEYWORDS 에 빈(공백뿐인) 항목이 없다", all(normed),
          "빈 항목 %r" % [k for k, n in zip(config.SECTION_KEYWORDS, normed) if not n])
    check("SECTION_KEYWORDS 는 정규화 후에도 중복이 없다",
          len(set(normed)) == len(normed),
          "중복 %r" % sorted({n for n in normed if normed.count(n) > 1}))

    # DART 원문은 중점 자리에 ㆍ(U+318D)를 쓰기도 한다. 같은 서식인데 문서마다
    # 표기가 갈리므로 두 표기 모두로 시험한다 — 한쪽만 통과하면 절반이 새 나간다.
    for mark, name in (("\u00b7", "중점 U+00B7"), ("\u318d", "아래아 U+318D")):
        title = "1. 주식교환%s이전의 목적" % mark
        check("「%s」 (%s) 이 섹션 키워드에 걸린다" % (title, name), bool(hits(title)),
              "걸린 키워드 없음")

    for title in ("나. 설립하는 완전모회사의 사업목적",
                  "타. 기타 이사회결의사항 또는 주식이전계획중 중요한 사항"):
        check("「%s」 이 섹션 키워드에 걸린다" % title, bool(hits(title)), "걸린 키워드 없음")

    # 같은 내용이 시대별로 다른 제목에 담기는 꼭지들. 한쪽만 걸리면 1차(우리·메리츠)와
    # 2차(2000년대) 배치가 같은 항목을 두고 서로 다른 것을 담게 된다 — 비교가 깨진다.
    for old_t, new_t, what in (
            ("다. 주식매수예정가격 등", "Ⅶ. 주식매수청구권에 관한 사항", "주식매수청구권"),
            ("라. 행사절차, 방법, 기간 및 장소", "Ⅶ. 주식매수청구권에 관한 사항", "행사절차"),
            ("가. 당해 회사의 연혁", "2. 회사의 연혁", "회사의 연혁")):
        check("%s: 2000년대 표기「%s」와 현대 표기「%s」가 둘 다 걸린다"
              % (what, old_t, new_t), bool(hits(old_t)) and bool(hits(new_t)),
              "2000년대 %s / 현대 %s" % (hits(old_t), hits(new_t)))

    # 「정 정 신 고 (보고)」는 글자 사이 공백이 의미를 갖는다. normalize_for_match 는
    # 연속 공백을 하나로 줄일 뿐 없애지 않으므로, 공백이 여러 칸이어도 걸려야 한다.
    check("「정 정 신 고 (보고)」 가 걸린다 (공백 여러 칸 포함)",
          bool(hits("정 정 신 고 (보고)")) and bool(hits("정  정  신  고  (보고)")),
          "걸린 키워드 없음")

    # 설립 신고서와 편입 신고서를 섞으면 설립 목적 분석이 오염된다.
    vals = set(config.DOC_PURPOSE.values())
    n_est = sum(1 for v in config.DOC_PURPOSE.values() if v == "설립")
    check("DOC_PURPOSE 는 32건", len(config.DOC_PURPOSE) == 32,
          "%d건" % len(config.DOC_PURPOSE))
    check("DOC_PURPOSE 값은 설립·편입 두 종류뿐",
          vals == {"설립", "편입·완전자회사화"}, "관측 %s" % sorted(vals))
    check("DOC_PURPOSE 내역 설립 18 / 편입 14",
          n_est == 18 and len(config.DOC_PURPOSE) - n_est == 14,
          "설립 %d / 편입 %d" % (n_est, len(config.DOC_PURPOSE) - n_est))
    # 접수번호가 한 글자라도 틀리면 그 문서는 어떤 파일에도 걸리지 않고 handoff 에서
    # 조용히 빠진다(건수 단언은 통과한다). 형식만이라도 붙잡아 둔다.
    bad_rc = [k for k in config.DOC_PURPOSE if not (len(k) == 14 and k.isdigit())]
    check("DOC_PURPOSE 키는 전부 14자리 접수번호", not bad_rc, "형식 이상 %r" % bad_rc)

    # handoff._batch_of 는 표에 없는 corp_label 을 경고만 찍고 '2차'로 넣는다.
    # 라벨을 한 글자 틀리면 1차 법인의 행이 통째로 2차 CSV 로 넘어가도 파일은 만들어진다.
    batch = getattr(config, "HANDOFF_BATCH", {})
    unknown = [l for l in batch if l not in config.TARGETS_BY_LABEL]
    check("HANDOFF_BATCH 의 라벨이 전부 TARGETS 에 실재한다", not unknown,
          "TARGETS 에 없는 라벨 %r" % unknown)
    check("HANDOFF_BATCH 값은 1차·2차뿐", set(batch.values()) <= {"1차", "2차"},
          "관측 %s" % sorted(set(batch.values())))


def main(out_dir):
    root = os.path.join(os.path.abspath(out_dir), "_selftest")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    print("  셀프테스트 (네트워크·API 키 불필요)  작업경로: %s" % root)
    transport_cases(root)
    out = pipeline(root)
    assertions(out)
    conversion_section_cases()
    print("\n  결과: 통과 %d / 실패 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("  실패 항목:")
        for f in FAIL:
            print("    - %s" % f)
        return 1
    print("  전부 통과.")
    return 0
