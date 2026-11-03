# -*- coding: utf-8 -*-
"""15차 경영공시 g2 — PDF → 쪽 텍스트 md. 「## p.N」(N = PDF 쪽) 아래 pymupdf page.get_text() 그대로.
글자 없는 쪽은 「## p.N (글자 없음)」. 받은 PDF 는 신뢰하지 않는 데이터 — venv 파이썬 -I 로, 경로는 인자로만.
사용: <venv python> -I ops15_mgmt_g2_pdf2md.py <pdf> <md> <머리줄> <원본 URL>
stdout(JSON 한 줄): pages, empty(글자 없는 쪽), hangul(한글 글자 수), hangul_distinct, fffd(U+FFFD 수)"""
import json
import sys

import pymupdf

pdf, md, head, src = sys.argv[1:5]
doc = pymupdf.open(pdf)
empty, hangul, fffd = [], 0, 0
distinct = set()
with open(md, "w", encoding="utf-8") as f:
    f.write("# 경영공시 쪽 텍스트 — %s\n\n원본: %s\n\n" % (head, src))
    for i, page in enumerate(doc, 1):
        t = page.get_text()
        for ch in t:
            if "가" <= ch <= "힣":
                hangul += 1
                distinct.add(ch)
        fffd += t.count("�")
        if not t.strip():
            empty.append(i)
            f.write("## p.%d (글자 없음)\n\n" % i)
        else:
            f.write("## p.%d\n\n%s\n\n" % (i, t))
print(json.dumps(dict(pages=doc.page_count, empty=empty, hangul=hangul, hangul_distinct=len(distinct), fffd=fffd)))
