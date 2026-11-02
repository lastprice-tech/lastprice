# -*- coding: utf-8 -*-
"""15차 g2 — PDF → 쪽 텍스트 md. 「## p.N」(N=PDF 쪽) 아래 pymupdf page.get_text() 그대로. 글자 없는 쪽은 「## p.N (글자 없음)」.
사용: <venv python> -I gov15_g2_pdf2md.py <pdf> <md> <머리줄>   → stdout: 쪽수<TAB>글자없는쪽(쉼표)"""
import sys

import pymupdf

pdf, md, head = sys.argv[1:4]
doc = pymupdf.open(pdf)
empty = []
with open(md, "w", encoding="utf-8") as f:
    f.write("# 연차보고서 쪽 텍스트 — %s\n\n원본: %s\n\n" % (head, pdf))
    for i, page in enumerate(doc, 1):
        t = page.get_text()
        if not t.strip():
            empty.append(str(i))
            f.write("## p.%d (글자 없음)\n\n" % i)
        else:
            f.write("## p.%d\n\n%s\n\n" % (i, t))
print("%d\t%s" % (doc.page_count, ",".join(empty)))
