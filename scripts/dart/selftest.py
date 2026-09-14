# -*- coding: utf-8 -*-
"""오프라인 셀프테스트 — 네트워크도 API 키도 없이 collect→emit 전 구간을 검증한다."""
from __future__ import annotations

import csv
import glob
import zipfile
import tarfile
import gzip
import json
import os
import shutil
import sys

import client as C
import config
import corpcode
import docparse
import emit
import handoff
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
    # 아카이브 안도 본다. .zip/.xlsx 를 건너뛰면 키가 zip 멤버로 새도 이 단언이
    # 그대로 통과하는데, 이 프로젝트는 zip 을 그대로 인계한다 — 사각지대가 곧 인계 표면이다.
    def _leak_in(path):
        """(샜는가, 검사한 멤버 수). 못 여는 아카이브는 '검사 못 함'으로 센다."""
        low = path.lower()
        try:
            if low.endswith((".zip", ".xlsx", ".docx", ".pptx")):
                with zipfile.ZipFile(path) as z:
                    names = z.namelist()
                    return any(FAKE_KEY.encode() in z.read(n) for n in names), len(names)
            if low.endswith((".tar.gz", ".tgz")):
                with tarfile.open(path, "r:gz") as t:
                    n = 0
                    for m in t:
                        if not m.isfile():
                            continue
                        n += 1
                        f = t.extractfile(m)
                        if f and FAKE_KEY.encode() in f.read():
                            return True, n
                    return False, n
            if low.endswith(".gz"):
                with gzip.open(path, "rb") as f:
                    return FAKE_KEY.encode() in f.read(), 1
        except Exception:
            # 확장자가 .zip 인데 실제로는 DART 오류 응답 XML 인 파일이 있다
            # (status 013/014 는 200 으로 오고 본문이 XML 이다). 아카이브로 못 열면
            # 건너뛰지 말고 평문 바이트로 다시 본다 — 건너뛰는 쪽이 위험하다.
            try:
                with open(path, "rb") as f:
                    return FAKE_KEY.encode() in f.read(), 1
            except Exception:
                return None, 0      # 이것마저 실패하면 통과로 뭉개지 않는다
        with open(path, "rb") as f:
            return FAKE_KEY.encode() in f.read(), 1

    leaked, unreadable, members = [], [], 0
    for p in glob.glob(os.path.join(out, "**", "*"), recursive=True):
        if not os.path.isfile(p):
            continue
        hit, n = _leak_in(p)
        members += n
        if hit is None:
            unreadable.append(os.path.relpath(p, out))
        elif hit:
            leaked.append(os.path.relpath(p, out))
    check("API 키가 어떤 산출물에도 남지 않는다 (아카이브 내부 포함)",
          not leaked, ", ".join(leaked[:5]))
    check("키 검사가 못 연 파일이 없다 (못 열면 통과로 뭉개진다)",
          not unreadable, ", ".join(unreadable[:5]))

    # 사각지대 자체를 고정한다: zip 안에 키를 넣어 두면 위 단언이 반드시 실패해야 한다.
    probe = os.path.join(out, "_leakprobe.zip")
    with zipfile.ZipFile(probe, "w") as z:
        z.writestr("inner.csv", "crtfc_key=" + FAKE_KEY)
    hit, _ = _leak_in(probe)
    os.remove(probe)
    check("zip 멤버 안의 키를 실제로 잡아낸다", hit is True)
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
    # 개수를 박아 두면 차수를 더할 때마다 깨져서, 고치는 김에 단언을 무력화하게 된다.
    # 개수 대신 '설정이 스스로 선언한 총합과 맞는가'를 본다.
    n3 = len(getattr(config, "DOC_PURPOSE_3RD", {}))
    check("DOC_PURPOSE 는 1·2차 32건 + 3차분", len(config.DOC_PURPOSE) == 32 + n3,
          "총 %d건 (3차 %d건)" % (len(config.DOC_PURPOSE), n3))
    check("DOC_PURPOSE_3RD 가 DOC_PURPOSE 에 전부 반영됐다",
          all(k in config.DOC_PURPOSE for k in getattr(config, "DOC_PURPOSE_3RD", {})))
    check("DOC_PURPOSE 값은 설립·편입 두 종류뿐",
          vals == {"설립", "편입·완전자회사화"}, "관측 %s" % sorted(vals))
    # 설립 18건은 1·2차에서 확정됐고 3차는 전부 편입이다. 설립이 늘면 분류 사고다.
    check("DOC_PURPOSE 의 설립은 18건 그대로 (3차는 전부 편입)", n_est == 18,
          "설립 %d / 편입 %d" % (n_est, len(config.DOC_PURPOSE) - n_est))
    check("3차분은 전부 편입·완전자회사화",
          set(getattr(config, "DOC_PURPOSE_3RD", {}).values()) <= {"편입·완전자회사화"},
          "관측 %s" % sorted(set(getattr(config, "DOC_PURPOSE_3RD", {}).values())))
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
    check("HANDOFF_BATCH 값은 1·2·3차뿐", set(batch.values()) <= {"1차", "2차", "3차"},
          "관측 %s" % sorted(set(batch.values())))
    # 배치표에 없는 라벨은 handoff 가 경고만 찍고 2차로 넣는다. 3차 문서의 법인이
    # 빠져 있으면 3차 CSV 가 조용히 비고 그 행이 2차로 샌다.
    need3 = {"신한지주", "오렌지라이프생명보험", "KB금융", "KB손해보험",
             "우리금융지주", "동양생명보험", "iM금융지주", "iM라이프생명보험"}
    miss3 = sorted(l for l in need3 if batch.get(l) != "3차")
    check("3차 편입 건의 양쪽 당사자가 모두 3차로 지정됐다", not miss3,
          "3차가 아닌 라벨 %r" % miss3)


def parser_edge_cases(out_root):
    """파서 경계값. 여기서 잡는 것은 전부 '조용한 손실'이었던 것들이다."""
    print("\n  [6] 파서 경계 — 중첩 표·잘린 문서·표기")

    def tables(html):
        secs, err = docparse.parse_document(html)
        return [t for s in secs for t in s["tables"]], \
               " ".join(docparse.section_body(s) for s in secs), err

    def cells(tabs):
        return [[c["text"] for c in r] for t in tabs for r in t["rows"]]

    # DART 원문은 표 안에 표를 넣는다(실측: 우리 2018 웹회수 8건에 중첩 열림 1,624회,
    # 최대 깊이 3). 파서가 self._table 을 덮어쓰던 시절에는 바깥 표 187개와 그 셀
    # 356개가 통째로 사라졌고, 내용 있는 331행이 전부 "(주n) 정정 전/정정 후" 라벨이라
    # 정정신고서에서 어느 표가 정정 전인지가 인계본에서 없어졌다.
    nest = ("<TABLE><TR><TD>(주1) 정정 전</TD></TR>"
            "<TR><TD><TABLE><TR><TD>안쪽</TD></TR></TABLE></TD></TR>"
            "<TR><TD>(주1) 정정 후</TD></TR></TABLE>")
    tb, body, err = tables(nest)
    flat = [c for row in cells(tb) for c in row]
    check("중첩 표: 바깥 표의 셀이 보존된다",
          "(주1) 정정 전" in flat and "(주1) 정정 후" in flat, "셀 %r" % (flat,))
    check("중첩 표: 안쪽 표도 따로 남는다", "안쪽" in flat)
    check("중첩 표: 표 개수가 <TABLE> 개수와 같다", len(tb) == 2, "표 %d" % len(tb))
    # table_index 는 원문 등장 순서여야 한다. 바깥 표를 닫는 시점에 실으면 제 자식들
    # 뒤로 밀려 색인이 문서 순서와 어긋난다.
    check("중첩 표: 바깥 표가 안쪽 표보다 먼저 색인된다",
          bool(tb) and any(c == "(주1) 정정 전" for r in tb[0]["rows"] for c in
                           [x["text"] for x in r]))
    check("중첩 표: 바깥 셀 내용이 본문으로 새지 않는다", "정정 후" not in body,
          "본문 %r" % body[:60])

    tb, _, _ = tables("<TABLE><TR><TD>앞<TABLE><TR><TD>안</TD></TR></TABLE>뒤</TD></TR></TABLE>")
    check("셀 안에 표가 끼어도 그 셀의 앞뒤 텍스트가 한 셀에 남는다",
          ["앞뒤"] in cells(tb), "셀 %r" % (cells(tb),))

    # 원문 크기 초과 절단·목차 노드를 바이트로 자른 조각은 태그 한가운데서 끝난다.
    tb, _, _ = tables("<TABLE><TR><TD>합계 100</TD></TR>")
    check("닫히지 않은 <TABLE> 의 셀도 버리지 않는다",
          ["합계 100"] in cells(tb), "셀 %r" % (cells(tb),))
    _, body, _ = tables("<P>꼬리 값")
    check("닫히지 않은 <P> 의 텍스트를 close() 에서 버리지 않는다",
          "꼬리 값" in body, "본문 %r" % body)

    # DART 는 '&' 를 escape 하지 않는다. 모르는 엔티티를 빈 문자열로 바꾸면 지워진다.
    _, body, _ = tables("<P>M&A중개</P>")
    check("미정의 엔티티(M&A)가 본문에서 보존된다", body == "M&A중개", "본문 %r" % body)
    tb, _, _ = tables("<TABLE><TR><TD>S&P500</TD></TR></TABLE>")
    check("미정의 엔티티가 셀에서도 보존된다", ["S&P500"] in cells(tb), "셀 %r" % (cells(tb),))
    _, body, _ = tables("<P>값 &#1114112;</P>")
    check("변환 못 하는 문자참조는 지우지 않고 원문을 남긴다", "&#1114112;" in body,
          "본문 %r" % body)

    tb, _, _ = tables("<TABLE><TR><TD></TD><TD>x</TD></TR></TABLE>")
    check("빈 셀이 행을 무너뜨리지 않는다", cells(tb) == [["", "x"]], "셀 %r" % (cells(tb),))

    # 안 닫힌 <TD> — 예전에는 다음 셀 태그가 버퍼를 리셋해 두 칸이 다 사라지고
    # 빈 행이 </TR> 에서 통째로 버려졌다(표 1개 / 행 0개).
    tb, _, _ = tables("<TABLE><TR><TD>첫칸<TD>둘째칸</TR></TABLE>")
    check("닫히지 않은 <TD> 의 글자를 다음 셀이 지우지 않는다",
          cells(tb) == [["첫칸", "둘째칸"]], "셀 %r" % (cells(tb),))
    tb, _, _ = tables('<TABLE><TR><TD COLSPAN="2" ROWSPAN="3">x<TD>y</TR></TABLE>')
    spans = [(c["rowspan"], c["colspan"]) for t in tb for r in t["rows"] for c in r]
    check("닫히지 않은 셀의 rowspan/colspan 도 원문 그대로 남는다",
          spans == [("3", "2"), ("", "")], "span %r" % (spans,))
    # 안 닫힌 <TR> — 예전에는 다음 <TR> 이 self._row 를 갈아치워 앞 행이 사라졌다.
    tb, _, _ = tables("<TABLE><TR><TD>a</TD><TR><TD>b</TD></TR></TABLE>")
    check("닫히지 않은 <TR> 의 행을 다음 행이 지우지 않는다",
          cells(tb) == [["a"], ["b"]], "셀 %r" % (cells(tb),))
    # 표 안이지만 <TR> 밖인 텍스트 — 셀에도 본문에도 없이 사라지던 경로.
    tb, body, _ = tables("<TABLE>표안텍스트<P>표안P</P><TR><TD>셀</TD></TR></TABLE>")
    check("표 안·행 밖 텍스트를 버리지 않는다",
          "표안텍스트" in body and "표안P" in body, "본문 %r" % body)

    # ── 웹 회수 경로: 목차 제목 표기 ──────────────────────────────────────
    # ZIP 경로의 section_title 은 emit 이 sec["title"](= normalize_for_match 결과)을
    # 싣는다. 웹 경로만 원문 표기(ㆍ U+318D)로 두면 같은 CSV 안에서 표기가 갈려
    # 중점('·')으로 거르면 웹 8건이 0건으로 나온다.
    out = os.path.join(out_root, "t_web")
    shutil.rmtree(out, ignore_errors=True)
    d = os.path.join(out, "doc", "20181115000214")
    os.makedirs(d)
    html = ("<TITLE>머리</TITLE><TABLE><TR><TD>정정 전</TD></TR>"
            "<TR><TD><TABLE><TR><TD>1,234</TD></TR></TABLE></TD></TR></TABLE>").encode("cp949")
    with open(os.path.join(d, "본문.html"), "wb") as f:
        f.write(html)
    rec = {"파일종류": "본문HTML", "수령성공여부": "성공",
           "저장경로": "doc/20181115000214/본문.html", "sha256": "0" * 64,
           "fetched_at": "2026-09-11T00:00:00+09:00",
           "목차_노드": [{"순서": 1, "제목": "제1부 주식의 포괄적 교환ㆍ이전의 개요",
                       "시작바이트": 0, "바이트": len(html)}]}
    with open(os.path.join(d, "_파일목록.json"), "w", encoding="utf-8") as f:
        json.dump({"files": [rec]}, f, ensure_ascii=False)
    notes = []
    parts, prov = handoff._web_doc_parts(out, "20181115000214", notes)
    check("웹 회수: 목차 노드를 읽어 낸다", len(parts) == 1, "parts %d" % len(parts))
    if parts:
        pt = parts[0]
        check("웹 회수 제목이 ZIP 경로와 같은 표기로 정규화된다",
              pt["title"] == docparse.normalize_for_match(pt["title_raw"])
              and "·" in pt["title"], "title %r" % pt["title"])
        check("웹 회수 제목의 원문 표기를 따로 보존한다",
              pt["title_raw"] == "제1부 주식의 포괄적 교환ㆍ이전의 개요")
        # 같은 필터가 두 경로에 똑같이 걸려야 한다
        check("중점 표기로 걸러도 웹 회수 제목이 잡힌다",
              "교환·이전" in pt["title"])
        check("웹 회수 표에서도 중첩 바깥 표의 셀이 보존된다",
              any(c["text"] == "정정 전" for t in pt["tables"] for r in t["rows"]
                  for c in r), "표 %d" % len(pt["tables"]))
    check("웹 회수 출처를 뭉개지 않는다", prov.get("status") == "014→웹회수")

    # `바이트` 가 없으면 파일 끝까지 읽어 버리던 자리 — 이제는 건너뛰고 사유를 남긴다.
    rec2 = dict(rec, 목차_노드=[{"순서": 1, "제목": "x", "시작바이트": 0, "바이트": ""}])
    with open(os.path.join(d, "_파일목록.json"), "w", encoding="utf-8") as f:
        json.dump({"files": [rec2]}, f, ensure_ascii=False)
    notes2 = []
    parts2, _ = handoff._web_doc_parts(out, "20181115000214", notes2)
    check("`바이트` 결측 노드는 파일 끝까지 읽지 않고 사유를 남긴다",
          not parts2 and any("바이트 범위가 없어" in n for n in notes2),
          "parts %d notes %r" % (len(parts2), notes2))


def main(out_dir):
    root = os.path.join(os.path.abspath(out_dir), "_selftest")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    print("  셀프테스트 (네트워크·API 키 불필요)  작업경로: %s" % root)
    transport_cases(root)
    out = pipeline(root)
    assertions(out)
    conversion_section_cases()
    parser_edge_cases(root)
    print("\n  결과: 통과 %d / 실패 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("  실패 항목:")
        for f in FAIL:
            print("    - %s" % f)
        return 1
    print("  전부 통과.")
    return 0
