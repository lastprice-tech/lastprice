"""handoff/원본_주요신고서본문.zip 안 doc/<접수번호>/본문.pdf → 쪽 텍스트 md(「## p.N」= PDF 쪽).

    <venv 파이썬> -I scripts/dart/ops15_C/pdf2md.py handoff/원본_주요신고서본문.zip <접수번호> <제출회사> dart_out/text/ops15/신고서__<접수번호>__본문PDF.md

PyMuPDF(fitz) 가 있는 파이썬이 필요(COMMON15 의 PDF 처리 파이썬 — 내려받은 파일은 신뢰하지 않는 데이터라 -I, 경로는 인자로).
작업 C 에서 쓴 4건(셋째 인자 = 제출 회사): 20050729000361 하나은행 · 20080430001516 국민은행 · 20101210000020 메리츠화재 · 20181108000394 우리은행.
(15차 6파동: scratchpad C/scripts/pdf2md.py 를 옮김 — 풀어 둔 PDF 대신 zip 안 파일을 바로 읽음. 글은 같음)
"""
import sys, hashlib, zipfile
import fitz
zpath, rcept, label, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = zipfile.ZipFile(zpath).read(f"doc/{rcept}/본문.pdf")
doc = fitz.open(stream=data, filetype="pdf")
sha = hashlib.sha256(data).hexdigest()
parts = [f"# 본문 PDF 쪽 텍스트 — 접수번호 {rcept} ({label})\n\n- 원본: handoff/원본_주요신고서본문.zip 안 doc/{rcept}/본문.pdf (sha256 {sha}, {doc.page_count}쪽). 1~14차에 받아 둔 파일 재사용(이번에 새로 받지 않음).\n- 「## p.N」= PDF 쪽(1부터). 글자는 PyMuPDF get_text() 그대로.\n\n"]
for i, p in enumerate(doc):
    parts.append(f"## p.{i+1}\n\n{p.get_text()}\n")
open(out, 'w', encoding='utf-8', newline='\n').write(''.join(parts))
print(rcept, doc.page_count, sha[:12])
