"""작업 C — 사건 문서를 고를 때 본 OpenDART 공시목록(list.json) 받기. 결과는 DartClient 가 dart_out/raw/list/ 에 저장(git 밖), 요약은 표준출력(TSV).

    python3 scripts/dart/ops15_C/fetch_lists.py                    # 15차에 새로 본 사건 기간 목록(아래 JOBS)
    python3 scripts/dart/ops15_C/fetch_lists.py <corp_code> <bgn_de> <end_de>

DART_API_KEY 는 환경변수. 1~14차에 받아 둔 원장(<corp_code>_19990101_*.json 등)은 커밋한 dart_out/raw_part*.tar.gz 에 있음.
(15차 6파동: scratchpad C/scripts/fetch_lists.py·fetch_lists2.py 를 옮겨 합침 — 경로만 저장소 상대로, 출력은 표준출력)
NH농협금융지주 2012 목록은 fetch_nh.py(유형별 조회 — DartClient list 캐시 이름에 pblntf_ty 가 없어 refresh 로 받음).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'dart'))
from client import DartClient
JOBS = [
    ('부산은행', '00124106', '20100701', '20110630'),
    ('대구은행', '00109019', '20101001', '20111031'),
    ('전북은행', '00147295', '20121001', '20131031'),
    ('BNK금융지주', '00858364', '20110101', '20111231'),
    ('JB금융지주', '00980122', '20130101', '20131231'),
]
if len(sys.argv) == 4:
    JOBS = [('', sys.argv[1], sys.argv[2], sys.argv[3])]
c = DartClient(os.path.join(ROOT, 'dart_out'), delay=0.6, max_calls=60)
for nm, cc, b, e in JOBS:
    page = 1
    while True:
        res = c.call('list', dict(corp_code=cc, bgn_de=b, end_de=e, page_no=page, page_count=100), phase='ops15_C')
        d = res.data or {}
        for it in d.get('list', []) or []:
            print('\t'.join([cc, it.get('corp_name', ''), it['rcept_dt'], it['rcept_no'], it['report_nm'].strip(), res.raw_path, res.fetched_at]))
        print('#', nm, cc, res.status, res.message, 'page', page, '/', d.get('total_page'), file=sys.stderr)
        if page >= int(d.get('total_page', 1) or 1):
            break
        page += 1
