# -*- coding: utf-8 -*-
"""13차_지주관리유형 — 9차 때 받아 둔 원본 24건 묶기 + 전체 텍스트 + 목차표 + MANIFEST (새 수집 없음).

    <pymupdf 있는 파이썬> -I scripts/dart/pack13_mgmt.py pack      # 1~3, 5 (원본 복사·sha256·텍스트·MANIFEST) + 사업보고서 목차
    <pymupdf 있는 파이썬> -I scripts/dart/pack13_mgmt.py toc       # 목차표.csv 합치기(사업보고서 북마크 + 목차표_조각/*.csv)
    python3 -I scripts/dart/pack13_mgmt.py zip                     # 6 (zipfile, UTF-8 파일 이름)
    python3 -I scripts/dart/pack13_mgmt.py check                   # 다시 대조(원본 sha256·쪽 수·텍스트 쪽 머리·zip 안 목록)

- 네트워크 요청 없음. 입력은 dart_out 에 이미 있는 파일뿐(9차 근거 CSV 의 source_file 과 같은 경로).
- 원본은 고치지 않는다(shutil.copy2 뒤 sha256 을 다시 맞댐).
- 텍스트: 쪽마다 「## p.<PDF 쪽번호>」 머리줄 + pymupdf page.get_text() 그대로(글자 수정·요약·생략 없음).
  글자가 나오지 않는 쪽은 「## p.N (글자 없음)」.
- 내려받은 PDF 는 신뢰하지 않는 데이터 — 이 스크립트는 -I 로 돌리고 경로는 코드 안 상수로만 읽는다.
"""
import csv
import hashlib
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "handoff", "13차_지주관리유형")
PACK = os.path.join(OUT, "원본")
TEXT = os.path.join(OUT, "텍스트")
FRAG = os.path.join(OUT, "목차표_조각")
EVID = os.path.join(ROOT, "handoff", "원문_지주리스크체계_근거.csv")
KST = timezone(timedelta(hours=9))

CORPS = [  # (회사, 사업보고서 FY2025 접수번호)
    ("KB금융지주", "20260313001191"),
    ("신한금융지주", "20260318000826"),
    ("하나금융지주", "20260316001292"),
    ("우리금융지주", "20260313001235"),
    ("iM금융지주", "20260318000971"),
    ("NH농협금융지주", "20260331004252"),
    ("메리츠금융지주", "20260318001419"),
    ("한국투자금융지주", "20260319001006"),
]
MAN_COLS = ["doc_kind", "corp", "period", "rcept_no_or_url", "dart_out_path", "packed_path", "bytes", "pages",
            "sha256", "sha256_9차대조", "text_path", "note"]
TOC_COLS = ["doc_kind", "corp", "text_path", "level", "title", "start_page", "printed_page", "method", "required_item", "note"]


def rel(p):
    return os.path.relpath(p, ROOT)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def evid_sha():
    m = {}
    with open(EVID, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            m.setdefault(r["source_file"], set()).add(r["source_sha256"])
    return m


def meta_urls():
    """경영공시·연차보고서 URL — 8차 수집 기록에서(새 요청 없음)."""
    u = {}
    with open(os.path.join(ROOT, "dart_out", "risk8", "경영공시_2026_2Q.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            u[("경영공시", r["corp_label"])] = (r["실제url"] or r["url"], r["제목"], r.get("게시일", ""))
    for corp, _ in CORPS:
        mp = os.path.join(ROOT, "dart_out", "raw", "governance", corp, f"{corp}_지배구조연차보고서_2026.pdf.meta.json")
        if os.path.exists(mp):
            m = json.load(open(mp, encoding="utf-8"))
            u[("연차보고서", corp)] = (m.get("실제url") or m.get("url", ""), m.get("제목", ""), m.get("공시일", ""))
    return u


def targets():
    """(doc_kind, corp, period, rcept_or_url, src_abs, packed_rel_dir, convert?, note)"""
    urls = meta_urls()
    T = []
    for corp, rc in CORPS:
        d = os.path.join(ROOT, "dart_out", "doc", rc)
        dart = f"{rc} · https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rc}"
        if not os.path.isdir(d):
            T.append(("사업보고서", corp, "FY2025(2025.12)", dart, d, None, False, "dart_out 에 없음"))
        else:
            for base, _dirs, files in os.walk(d):
                _dirs.sort()
                for fn in sorted(files):
                    src = os.path.join(base, fn)
                    sub = os.path.relpath(base, d)
                    T.append(("사업보고서", corp, "FY2025(2025.12)", dart, src,
                              os.path.join("사업보고서", corp, "" if sub == "." else sub),
                              fn == "본문.pdf" and sub == ".", ""))
        # 원문 XML(OpenDART document.xml zip) — _파일목록.json 「본문XML」이 가리키는 파일(dart_out/doc 폴더 밖)
        x = os.path.join(ROOT, "dart_out", "raw", "document", f"{rc}.zip")
        if os.path.exists(x):
            T.append(("사업보고서", corp, "FY2025(2025.12)", dart, x, os.path.join("사업보고서", corp), False,
                      "원문 XML(OpenDART document.xml zip) — dart_out/doc/<접수번호>/_파일목록.json 「본문XML」이 가리키는 파일"))
        else:
            T.append(("사업보고서", corp, "FY2025(2025.12)", dart, x, None, False, "dart_out 에 없음(원문 XML)"))
    for corp, _ in CORPS:
        p = os.path.join(ROOT, "dart_out", "raw", "risk8", "경영공시", corp, f"{corp}_경영공시_2026_2Q.pdf")
        url, title, day = urls.get(("경영공시", corp), ("", "", ""))
        T.append(("경영공시", corp, "2026.2Q", f"{url} · 「{title}」 게시일 {day or '기록 없음'}", p,
                  os.path.join("경영공시", corp) if os.path.exists(p) else None, True, "" if os.path.exists(p) else "dart_out 에 없음"))
    for corp, _ in CORPS:
        p = os.path.join(ROOT, "dart_out", "raw", "governance", corp, f"{corp}_지배구조연차보고서_2026.pdf")
        url, title, day = urls.get(("연차보고서", corp), ("", "", ""))
        T.append(("연차보고서", corp, "FY2025(2026 공시)", f"{url} · 「{title}」 공시일 {day or '기록 없음'}", p,
                  os.path.join("연차보고서", corp) if os.path.exists(p) else None, True, "" if os.path.exists(p) else "dart_out 에 없음"))
    return T


def to_text(pdf, out_md, doc_kind, corp, sha, src_rel):
    import pymupdf
    d = pymupdf.open(pdf)
    blank = []
    with open(out_md, "w", encoding="utf-8", newline="\n") as w:
        w.write(f"# {doc_kind} — {corp}\n\n")
        w.write(f"- 원본: `{src_rel}` · sha256 {sha} · {d.page_count}쪽 · 변환 pymupdf {pymupdf.__version__} page.get_text()(글자 그대로)\n")
        w.write("- 쪽 머리 「## p.N」의 N 은 PDF 쪽 번호(1부터). 글자가 나오지 않는 쪽은 「## p.N (글자 없음)」.\n\n")
        for i, pg in enumerate(d, 1):
            t = pg.get_text()
            if t.strip():
                w.write(f"## p.{i}\n\n{t}")
                if not t.endswith("\n"):
                    w.write("\n")
                w.write("\n")
            else:
                blank.append(i)
                w.write(f"## p.{i} (글자 없음)\n\n")
    return d.page_count, blank, d


REQ_BIZ = [  # (필수 항목 이름, 북마크 제목에서 찾을 글(공백 무시), 수준 조건)
    ("Ⅰ. 회사의 개요", "I.회사의개요", 1),
    ("Ⅰ. 정관에 관한 사항", "정관에관한사항", None),
    ("Ⅱ. 사업의 내용", "II.사업의내용", 1),
    ("Ⅵ. 이사회 등 회사의 기관에 관한 사항", "VI.이사회등회사의기관에관한사항", 1),
    ("Ⅷ. 임원 및 직원 등에 관한 사항", "VIII.임원및직원등에관한사항", 1),
    ("Ⅸ. 계열회사 등에 관한 사항", "IX.계열회사등에관한사항", 1),
]


def nows(s):
    return "".join(s.split())


def biz_toc(corp, pdf, text_rel):
    """사업보고서 — PDF 북마크 전부 + 필수 항목 표시 + 「계열회사 간 임원 겸직 현황」 본문 검색."""
    import pymupdf
    d = pymupdf.open(pdf)
    toc = d.get_toc()
    rows, found = [], set()
    for lv, title, page in toc:
        req = ""
        for name, key, lvreq in REQ_BIZ:
            if nows(title).startswith(key) or (lvreq is None and key in nows(title)):
                if lvreq is None or lv == lvreq:
                    req = name
                    found.add(name)
        rows.append(dict(doc_kind="사업보고서", corp=corp, text_path=text_rel, level=lv, title=title, start_page=page,
                         printed_page="", method="PDF 북마크", required_item=req, note=""))
    # Ⅰ 의 하위 「정관에 관한 사항」이 북마크로 Ⅰ 범위 밖에 걸리면 표시만 — 범위 검사
    i1 = next((p for lv, t, p in toc if lv == 1 and nows(t).startswith("I.회사의개요")), None)
    i2 = next((p for lv, t, p in toc if lv == 1 and nows(t).startswith("II.사업의내용")), None)
    for r in rows:
        if r["required_item"] == "Ⅰ. 정관에 관한 사항" and i1 and i2 and not (i1 <= r["start_page"] < i2):
            r["note"] = "Ⅰ 범위 밖의 같은 제목 북마크"
    # 계열회사 간 임원 겸직 현황 — 북마크에 없으면 본문 검색(Ⅸ 범위와 그 밖 전부)
    ix = next((p for lv, t, p in toc if lv == 1 and nows(t).startswith("IX.계열회사등에관한사항")), None)
    nxt = next((p for lv, t, p in toc if lv == 1 and (nows(t).startswith("X.") or nows(t).startswith("XI."))), None)
    bm = [r for r in rows if "임원겸직" in nows(r["title"])]
    for r in bm:
        r["required_item"] = "Ⅸ. 계열회사 간 임원 겸직 현황"
        found.add("Ⅸ. 계열회사 간 임원 겸직 현황")
    if not bm:
        hits = []
        for i, pg in enumerate(d, 1):
            for ln in pg.get_text().splitlines():
                n = nows(ln)
                if "임원겸직현황" in n and len(n) <= 60:
                    hits.append((i, ln.strip()))
        for i, ln in hits:
            inside = ix is not None and i >= ix and (nxt is None or i < nxt)
            rows.append(dict(doc_kind="사업보고서", corp=corp, text_path=text_rel, level="",
                             title=ln, start_page=i, printed_page="", method="본문 검색(「임원 겸직 현황」, 공백 무시)",
                             required_item="Ⅸ. 계열회사 간 임원 겸직 현황" if inside else "",
                             note="Ⅸ 범위 안" if inside else "Ⅸ 범위 밖(같은 표가 다른 장에도 나옴)"))
            if inside:
                found.add("Ⅸ. 계열회사 간 임원 겸직 현황")
    missing = [n for n, _, _ in REQ_BIZ if n not in found]
    if "Ⅸ. 계열회사 간 임원 겸직 현황" not in found:
        missing.append("Ⅸ. 계열회사 간 임원 겸직 현황")
    for m in missing:
        rows.append(dict(doc_kind="사업보고서", corp=corp, text_path=text_rel, level="", title="", start_page="",
                         printed_page="", method="PDF 북마크 + 본문 검색", required_item=m,
                         note="찾지 못함 — 북마크 제목·본문 줄에서 공백 무시 검색"))
    return rows


def write_csv(path, cols, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def cmd_pack():
    os.makedirs(PACK, exist_ok=True)
    os.makedirs(TEXT, exist_ok=True)
    ev = evid_sha()
    man, biz_rows = [], []
    for kind, corp, period, rc, src, pdir, conv, note in targets():
        srel = rel(src)
        row = dict(doc_kind=kind, corp=corp, period=period, rcept_no_or_url=rc, dart_out_path=srel, note=note)
        if pdir is None or not os.path.exists(src):
            row.update(packed_path="", bytes="", pages="", sha256="", text_path="")
            row["sha256_9차대조"] = "비교불가"
            row["note"] = note or "dart_out 에 없음"
            man.append(row)
            continue
        dst_dir = os.path.join(PACK, pdir)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        s = sha256(src)
        if sha256(dst) != s:
            raise SystemExit(f"복사 뒤 sha256 다름: {srel}")
        row.update(packed_path=os.path.relpath(dst, OUT), bytes=os.path.getsize(src), sha256=s)
        if srel in ev:
            row["sha256_9차대조"] = "같음" if ev[srel] == {s} else "다름"
            if row["sha256_9차대조"] == "다름":
                row["note"] = (row["note"] + "; " if row["note"] else "") + "9차 근거 CSV sha256: " + ",".join(sorted(ev[srel]))
        else:
            row["sha256_9차대조"] = "비교불가"
            row["note"] = (row["note"] + "; " if row["note"] else "") + "9차 근거 CSV 의 source_file 에 이 파일 행이 없음"
        if src.lower().endswith(".pdf"):
            import pymupdf
            row["pages"] = pymupdf.open(src).page_count
        if conv:
            tmd = os.path.join(TEXT, f"{kind}__{corp}.md")
            pages, blank, _ = to_text(src, tmd, kind, corp, s, srel)
            row["text_path"] = os.path.relpath(tmd, OUT)
            if blank:
                row["note"] = (row["note"] + "; " if row["note"] else "") + f"글자 없음 쪽 {len(blank)}: " + ",".join(map(str, blank))
            if kind == "사업보고서":
                biz_rows += biz_toc(corp, src, row["text_path"])
        else:
            row["text_path"] = ""
        man.append(row)
    write_csv(os.path.join(OUT, "MANIFEST.csv"), MAN_COLS, man)
    os.makedirs(FRAG, exist_ok=True)
    write_csv(os.path.join(FRAG, "사업보고서.csv"), TOC_COLS, biz_rows)
    print(f"MANIFEST {len(man)}행 · 사업보고서 목차 {len(biz_rows)}행 · 작성 {datetime.now(KST):%Y-%m-%d %H:%M} KST")


def cmd_toc():
    rows = []
    order = {"사업보고서": 0, "경영공시": 1, "연차보고서": 2}
    corp_order = {c: i for i, (c, _) in enumerate(CORPS)}
    for fn in sorted(os.listdir(FRAG)):
        if fn.endswith(".csv"):
            with open(os.path.join(FRAG, fn), encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    rows.append(r)
    rows.sort(key=lambda r: (order.get(r["doc_kind"], 9), corp_order.get(r["corp"], 99)))  # 안정 정렬 — 조각 안 순서 유지
    write_csv(os.path.join(OUT, "목차표.csv"), TOC_COLS, rows)
    print(f"목차표 {len(rows)}행")


def zip_write(zpath, items):
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for src, arc in items:
            zi = zipfile.ZipInfo.from_file(src, arc)
            zi.flag_bits |= 0x800  # UTF-8 파일 이름
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(src, "rb") as f, z.open(zi, "w", force_zip64=True) as w:
                shutil.copyfileobj(f, w, 1 << 20)


def walk(d, base):
    out = []
    for b, ds, fs in os.walk(d):
        ds.sort()
        for fn in sorted(fs):
            p = os.path.join(b, fn)
            out.append((p, os.path.relpath(p, base)))
    return out


def cmd_zip():
    top = "13차_지주관리유형"
    t_items = [(p, f"{top}/{a}") for p, a in walk(TEXT, OUT)]
    t_items += [(os.path.join(OUT, "목차표.csv"), f"{top}/목차표.csv"), (os.path.join(OUT, "MANIFEST.csv"), f"{top}/MANIFEST.csv")]
    o_items = [(p, f"{top}/{a}") for p, a in walk(PACK, OUT)] + [(os.path.join(OUT, "MANIFEST.csv"), f"{top}/MANIFEST.csv")]
    zt = os.path.join(OUT, "13차_지주관리유형_텍스트.zip")
    zo = os.path.join(OUT, "13차_지주관리유형_원본.zip")
    zip_write(zt, t_items)
    zip_write(zo, o_items)
    for z in (zt, zo):
        print(rel(z), os.path.getsize(z))


def cmd_check():
    import pymupdf
    probs = []
    with open(os.path.join(OUT, "MANIFEST.csv"), encoding="utf-8-sig") as f:
        man = list(csv.DictReader(f))
    for r in man:
        if not r["packed_path"]:
            continue
        p = os.path.join(OUT, r["packed_path"])
        if sha256(p) != r["sha256"] or sha256(os.path.join(ROOT, r["dart_out_path"])) != r["sha256"]:
            probs.append(f"sha256 다름: {r['packed_path']}")
        if r["text_path"]:
            n = int(r["pages"])
            heads = [ln for ln in open(os.path.join(OUT, r["text_path"]), encoding="utf-8") if ln.startswith("## p.")]
            nums = [int(h.split()[1][2:]) for h in heads]
            if nums != list(range(1, n + 1)):
                probs.append(f"쪽 머리 {len(nums)} ≠ {n}: {r['text_path']}")
            d = pymupdf.open(p)
            txt = open(os.path.join(OUT, r["text_path"]), encoding="utf-8").read()
            for i in (0, n // 2, n - 1):
                t = d[i].get_text()
                if t.strip() and t not in txt:
                    probs.append(f"쪽 글 대조 실패 p.{i+1}: {r['text_path']}")
    for zname, must in (("13차_지주관리유형_텍스트.zip", ["목차표.csv", "MANIFEST.csv"]), ("13차_지주관리유형_원본.zip", ["MANIFEST.csv"])):
        zp = os.path.join(OUT, zname)
        if os.path.exists(zp):
            with zipfile.ZipFile(zp) as z:
                names = z.namelist()
                bad = [i.filename for i in z.infolist() if not (i.flag_bits & 0x800) and any(ord(c) > 127 for c in i.filename)]
                if bad:
                    probs.append(f"{zname}: UTF-8 표지 없는 한글 이름 {len(bad)}")
                for m in must:
                    if f"13차_지주관리유형/{m}" not in names:
                        probs.append(f"{zname}: {m} 없음")
                if z.testzip() is not None:
                    probs.append(f"{zname}: testzip 실패")
    print("문제 %d건" % len(probs))
    for p in probs:
        print(" -", p)
    return 1 if probs else 0


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"pack": cmd_pack, "toc": cmd_toc, "zip": cmd_zip, "check": cmd_check}.get(c, lambda: print(__doc__))() or 0)
