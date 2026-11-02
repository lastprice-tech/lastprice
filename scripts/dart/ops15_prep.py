# -*- coding: utf-8 -*-
"""15차(지주 운영방식 리서치 — 겸직·파견·전적·위수탁 원문) 준비 단계.

    python3 scripts/dart/ops15_prep.py restore   # 커밋해 둔 dart_out/raw_part*.tar.gz 를 dart_out/raw 로 풀기(네트워크 없음)
    python3 scripts/dart/ops15_prep.py corps     # OpenDART corpCode.xml → 대상 지주 10곳 corp_code (API, 키는 환경변수)
    python3 scripts/dart/ops15_prep.py list      # OpenDART list.json → FY2019~FY2025 사업보고서(본·정정) 목록
    python3 scripts/dart/ops15_prep.py docs      # OpenDART document.xml(이미 있으면 캐시) → 원문 XML → 순서 보존 md

- DART 웹(dart.fss.or.kr) 뷰어·PDF 내려받기는 쓰지 않는다: robots.txt 가 /dsaf001/main.do, /report/viewer.do,
  /pdf/download/ 를 Disallow (2026-11-02 확인). OpenDART API(opendart.fss.or.kr/api)만 쓴다.
- DART_API_KEY 는 환경변수로만 읽고(client.DartClient), 출력·파일에 쓰지 않는다(client.scrub).
- md 변환: XML 의 TITLE·P·TABLE 을 나온 순서대로 옮김. 글자는 그대로(태그만 걷어냄, 줄 안 공백 줄임 없음 — 셀 안 줄바꿈은 「 / 」 가 아니라
  「<br>」로 남김). 표마다 문서 안 번호 「[표 n]」, 제목마다 「[절 n]」 — 쪽 번호가 없는 XML 의 위치 표기로 씀.
"""
import csv
import html
import io
import json
import os
import re
import sys
import tarfile
import zipfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTD = os.path.join(ROOT, "dart_out")
WORK = os.path.join(OUTD, "ops15")
TXT = os.path.join(OUTD, "text", "ops15")

# 대상 지주 10곳 — (보고용 이름, 종목코드, corpCode 이름(비상장 확인용))
TARGETS = [
    ("KB금융지주", "105560", "KB금융"),
    ("신한금융지주", "055550", "신한지주"),
    ("하나금융지주", "086790", "하나금융지주"),
    ("우리금융지주", "316140", "우리금융지주"),   # 신 지주(2019). 구 법인 00375302 와 혼동 금지 — 종목코드로만
    ("NH농협금융지주", "", "농협금융지주"),        # 비상장 — 이름으로, 후보가 여럿이면 멈춤
    ("메리츠금융지주", "138040", "메리츠금융지주"),
    ("iM금융지주", "139130", "iM금융지주"),
    ("BNK금융지주", "138930", "BNK금융지주"),
    ("JB금융지주", "175330", "JB금융지주"),
    ("한국투자금융지주", "071050", "한국금융지주"),
]
FY = range(2019, 2026)


def client(max_calls=400):
    from client import DartClient
    return DartClient(OUTD, delay=0.5, max_calls=max_calls)


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def cmd_restore():
    n = 0
    for i in range(1, 5):
        p = os.path.join(OUTD, f"raw_part{i}.tar.gz")
        with tarfile.open(p) as t:
            for m in t.getmembers():
                if m.name.startswith("/") or ".." in m.name.split("/") or not m.name.startswith("raw/"):
                    raise SystemExit(f"이상한 경로: {m.name}")
                if not (m.isfile() or m.isdir()):
                    continue
                dst = os.path.join(OUTD, m.name)
                if m.isfile() and os.path.exists(dst) and os.path.getsize(dst) == m.size:
                    continue
                t.extract(m, OUTD)
                n += 1
    print(f"restore: {n}개 풀었음 → dart_out/raw")


def cmd_corps():
    import corpcode
    c = client()
    rows, _ = corpcode.load_corp_index(c, phase="ops15")
    out = []
    for label, stock, name in TARGETS:
        if stock:
            hit = [r for r in rows if r.get("stock_code", "").strip() == stock]
        else:
            hit = [r for r in rows if r.get("corp_name", "") == name and not r.get("stock_code", "").strip()]
        if len(hit) != 1:
            raise SystemExit(f"{label}: corp_code 후보 {len(hit)}개 — 멈춤 {[h.get('corp_code') for h in hit]}")
        h = hit[0]
        out.append(dict(label=label, corp_code=h["corp_code"], corp_name=h.get("corp_name", ""),
                        stock_code=h.get("stock_code", "").strip(), how="종목코드" if stock else "이름(비상장)"))
    write_csv(os.path.join(WORK, "targets.csv"), out, ["label", "corp_code", "corp_name", "stock_code", "how"])
    for o in out:
        print(o["label"], o["corp_code"], o["corp_name"], o["stock_code"] or "(비상장)")


def targets():
    with open(os.path.join(WORK, "targets.csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def cmd_list():
    c = client()
    out = []
    for t in targets():
        page = 1
        while True:
            res = c.call("list", dict(corp_code=t["corp_code"], bgn_de="20200101", end_de="20261102",
                                      pblntf_ty="A", page_no=page, page_count=100), phase="ops15")
            if res.status not in ("000", "013"):
                raise SystemExit(f"list 실패 {t['label']}: {res.status} {res.message}")
            data = res.data or {}
            for r in data.get("list", []) or []:
                nm = r.get("report_nm", "")
                m = re.search(r"사업보고서\s*\((\d{4})\.12\)", nm)
                if m and int(m.group(1)) in FY:
                    out.append(dict(label=t["label"], corp_code=t["corp_code"], fy=m.group(1), rcept_no=r["rcept_no"],
                                    rcept_dt=r.get("rcept_dt", ""), report_nm=nm, flr_nm=r.get("flr_nm", ""),
                                    rm=r.get("rm", ""), kind="정정" if nm.strip().startswith("[") else "본",
                                    list_raw=res.raw_path))
            tp = int(data.get("total_page", 1) or 1)
            if page >= tp:
                break
            page += 1
    out.sort(key=lambda r: (r["label"], r["fy"], r["rcept_no"]))
    write_csv(os.path.join(WORK, "사업보고서_목록.csv"), out,
              ["label", "corp_code", "fy", "kind", "rcept_no", "rcept_dt", "report_nm", "flr_nm", "rm", "list_raw"])
    from collections import Counter
    c2 = Counter((r["label"], r["fy"], r["kind"]) for r in out)
    for t in targets():
        print(t["label"], " ".join(f"{fy}:{c2[(t['label'], str(fy), '본')]}+{c2[(t['label'], str(fy), '정정')]}" for fy in FY))


class Dart2MD(HTMLParser):
    """DART XML → md(나온 순서). TITLE → 「### [절 n] 제목」, P/글 → 줄, TABLE → 「[표 n]」 + 「| 칸 | 칸 |」 줄."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf = [], []
        self.mode = None
        self.n_title = self.n_table = 0
        self.depth_table = 0
        self.row, self.cell = None, None

    def flush_text(self):
        t = "".join(self.buf).strip()
        self.buf = []
        if t:
            self.out.append(t)

    def handle_starttag(self, tag, attrs):
        tag = tag.upper()
        if tag == "TITLE":
            self.flush_text()
            self.mode = "title"
        elif tag == "TABLE":
            if self.depth_table == 0:
                self.flush_text()
                self.n_table += 1
                self.out.append(f"[표 {self.n_table}]")
            self.depth_table += 1
        elif tag == "TR" and self.depth_table:
            self.row = []
        elif tag in ("TD", "TH", "TU", "TE") and self.depth_table:
            self.cell = []
        elif tag in ("BR",):
            (self.cell if self.cell is not None else self.buf).append("<br>")
        elif tag in ("P", "SPAN", "PGBRK"):
            if self.cell is None and self.depth_table == 0 and tag == "P":
                self.flush_text()

    def handle_endtag(self, tag):
        tag = tag.upper()
        if tag == "TITLE":
            t = "".join(self.buf).strip()
            self.buf = []
            self.n_title += 1
            self.out.append(f"### [절 {self.n_title}] {t}")
            self.mode = None
        elif tag in ("TD", "TH", "TU", "TE") and self.cell is not None:
            self.row.append("".join(self.cell).strip().replace("|", "｜").replace("\n", "<br>"))
            self.cell = None
        elif tag == "TR" and self.row is not None:
            self.out.append("| " + " | ".join(self.row) + " |")
            self.row = None
        elif tag == "TABLE" and self.depth_table:
            self.depth_table -= 1
            if self.depth_table == 0:
                self.out.append("[표 끝]")
        elif tag == "P" and self.cell is None and self.depth_table == 0:
            self.flush_text()

    def handle_data(self, d):
        if self.cell is not None:
            self.cell.append(d)
        else:
            self.buf.append(d)

    def result(self):
        self.flush_text()
        return "\n".join(self.out) + "\n"


def xml_to_md(zbytes, rcept):
    import docparse
    text, member, note = None, None, ""
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    members = docparse.safe_members(zf)
    principal, how = docparse.pick_principal(members, rcept)
    raw = zf.read(principal)
    text, declared, enc, repl = docparse.decode_document(raw)
    p = Dart2MD()
    p.feed(text)
    p.close()
    return p.result(), f"{principal.filename}({how})", f"{enc}{' 대체 '+str(repl) if repl else ''}"


def cmd_docs():
    import hashlib
    c = client(max_calls=400)
    with open(os.path.join(WORK, "사업보고서_목록.csv"), encoding="utf-8-sig") as f:
        lst = list(csv.DictReader(f))
    os.makedirs(TXT, exist_ok=True)
    rows = []
    for r in lst:
        res = c.call("document", dict(rcept_no=r["rcept_no"]), phase="ops15")
        row = dict(r)
        row.update(doc_status=res.status, doc_message=res.message, raw_path=res.raw_path, raw_sha256=res.raw_sha256,
                   cached=res.cached, fetched_at=res.fetched_at)
        if res.status == "000" and res.body:
            try:
                md, member, enc = xml_to_md(res.body, r["rcept_no"])
                p = os.path.join(TXT, f"사업보고서__{r['label']}__FY{r['fy']}__{r['rcept_no']}.md")
                head = (f"# {r['report_nm']} — {r['label']} (FY{r['fy']})\n\n- 접수번호 {r['rcept_no']} · 접수일 {r['rcept_dt']} · "
                        f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r['rcept_no']}\n- 원문: OpenDART document.xml `{res.raw_path}` "
                        f"(sha256 {res.raw_sha256}) · 멤버 {member} · 받은 시각 {res.fetched_at}\n"
                        "- 쪽 번호 없음(XML). 위치는 「[절 n]」(제목 순번)·「[표 n]」(표 순번). 글자는 XML 그대로(태그만 걷어냄).\n\n")
                with open(p, "w", encoding="utf-8", newline="\n") as w:
                    w.write(head + md)
                row.update(text_path=os.path.relpath(p, ROOT), text_sha256=hashlib.sha256((head + md).encode()).hexdigest())
            except Exception as e:  # 변환 실패는 기록
                row.update(text_path="", note=f"변환 실패 {type(e).__name__}: {e}")
        rows.append(row)
        print(r["label"], r["fy"], r["kind"], r["rcept_no"], res.status, "cache" if res.cached else "net")
    write_csv(os.path.join(WORK, "사업보고서_원문.csv"), rows,
              ["label", "corp_code", "fy", "kind", "rcept_no", "rcept_dt", "report_nm", "doc_status", "doc_message", "raw_path",
               "raw_sha256", "cached", "fetched_at", "text_path", "text_sha256", "note"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"restore": cmd_restore, "corps": cmd_corps, "list": cmd_list, "docs": cmd_docs}.get(cmd, lambda: print(__doc__))()
