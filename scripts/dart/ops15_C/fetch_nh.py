"""작업 C — NH농협금융지주 설립(2012-03-02, 농협중앙회 신용사업 분리) 때 지주 설립·전환 신고서가 있는지 OpenDART 공시목록으로 확인.

    python3 scripts/dart/ops15_C/fetch_nh.py      # DART_API_KEY 는 환경변수(scripts/dart/client.py 가 읽고 로그에서 가림)

2011-07-01~2012-12-31, 법인 4곳(농협금융지주 00908021 · 농협은행 00908757 · 농업협동조합중앙회 00332565·00291675 — corp_code 는
dart_out/raw/corpCode/corpCode.zip 에서 이름으로 찾음), 공시유형 C(발행공시)·B(주요사항보고)·I(거래소공시)·E(기타공시)와 유형 지정 없음(전체).
응답은 DartClient 가 dart_out/raw/list/ 에 저장(git 밖). 요약(보고서명·접수번호·받은 시각·상태)은 이 폴더 nh_list.json 에 씀 — build.py 가 읽음.
주의: DartClient 의 list 캐시 파일 이름(slug)에는 pblntf_ty 가 없어 유형만 다른 조회가 같은 파일을 캐시로 돌려줌 → refresh=True 로 매번 새로 받고,
  받은 날 글을 dart_out/raw/list/nh15/<corp_code>_<유형>_p<쪽>.json 으로 따로 둠(유형 지정 없음 조회를 마지막에 해 기본 캐시 파일이 그 응답이 되게 함).
"""
import shutil
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'dart'))
from client import DartClient

CORPS = [('NH농협금융지주(농협금융지주)', '00908021'), ('농협은행', '00908757'),
         ('농업협동조합중앙회', '00332565'), ('농업협동조합중앙회(같은 이름 다른 코드)', '00291675')]
BGN, END = '20110701', '20121231'
TYPES = [('C', '발행공시'), ('B', '주요사항보고'), ('I', '거래소공시'), ('E', '기타공시'), ('', '전체(유형 지정 없음)')]
KEY_RE = re.compile(r'증권신고서|투자설명서|주식교환|주식이전|교환ㆍ이전|분할|합병|설립|등록법인신청서')

c = DartClient(os.path.join(ROOT, 'dart_out'), delay=0.6, max_calls=80, refresh=True)
KEEP = os.path.join(ROOT, 'dart_out', 'raw', 'list', 'nh15')
os.makedirs(KEEP, exist_ok=True)
out = dict(range=[BGN, END], keyword_re=KEY_RE.pattern, queries=[])
for nm, cc in CORPS:
    for ty, tyn in TYPES:
        page = 1
        while True:
            params = dict(corp_code=cc, bgn_de=BGN, end_de=END, page_no=page, page_count=100)
            if ty:
                params['pblntf_ty'] = ty
            res = c.call('list', params, phase='ops15_C_nh')
            d = res.data or {}
            items = d.get('list', []) or []
            keep = os.path.join(KEEP, '%s_%s_p%03d.json' % (cc, ty or 'ALL', page))
            shutil.copyfile(os.path.join(ROOT, 'dart_out', res.raw_path), keep)
            out['queries'].append(dict(corp=nm, corp_code=cc, pblntf_ty=ty, type_name=tyn, page=page, status=res.status,
                                       message=res.message, total_count=d.get('total_count'), cached=res.cached,
                                       raw_path=os.path.relpath(keep, os.path.join(ROOT, 'dart_out')).replace(os.sep, '/'),
                                       fetched_at=res.fetched_at,
                                       items=[dict(rcept_no=it['rcept_no'], rcept_dt=it['rcept_dt'], corp_name=it.get('corp_name', ''),
                                                   report_nm=it['report_nm'].strip(), flr_nm=it.get('flr_nm', '')) for it in items]))
            print(nm, cc, ty or '*', res.status, res.message, 'page', page, '/', d.get('total_page'), 'n', len(items),
                  'hits', sum(1 for it in items if KEY_RE.search(it['report_nm'])))
            if page >= int(d.get('total_page', 1) or 1):
                break
            page += 1
with open(os.path.join(HERE, 'nh_list.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
