"""작업 C — OpenDART document.xml 받기(dart_out/raw/document/<접수번호>.zip + .meta.json).

    python3 scripts/dart/ops15_C/fetch_docs.py <접수번호> [<접수번호> …]
    python3 scripts/dart/ops15_C/fetch_docs.py --missing     # docs.py 의 문서 가운데 zip 이 없는 것만

DART_API_KEY 는 환경변수(scripts/dart/client.py 가 읽고 로그·파일에서 가림). 이미 받은 것은 캐시를 씀.
(15차 6파동: scratchpad C/scripts/fetch_docs.py 를 옮김 — 경로만 저장소 상대로, --missing 더함)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'dart'))
sys.path.insert(0, HERE)
from client import DartClient
from docs import DOCS
rs = sys.argv[1:]
if rs == ['--missing']:
    rs = [r for _, _, _, r, _, _ in DOCS if not os.path.exists(os.path.join(ROOT, 'dart_out', 'raw', 'document', r + '.zip.meta.json'))]
c = DartClient(os.path.join(ROOT, 'dart_out'), delay=0.8, max_calls=60, doc_timeout=180)
for r in rs:
    res = c.call('document', dict(rcept_no=r), phase='ops15_C')
    print(r, res.status, res.message, 'cache' if res.cached else 'net', len(res.body or b''), res.fetched_at, res.raw_path)
