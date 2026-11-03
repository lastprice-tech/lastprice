"""15차 확장 작업 F·F-2·F-3 g2(메리츠금융지주·iM금융지주·BNK금융지주·JB금융지주·한국투자금융지주) 독립 검증.

실행: python3 scripts/dart/verify15b_F_g2.py  (인자 없음; 네트워크 안 씀) → exit 0 = 통과 / 1 = 실패.
결과: dart_out/ops15/verify15b_F_g2.txt (점검 건수·실패 목록·빠짐 검토 목록·숫자 대조 표본).

생성기(scripts/dart/ops15b_F_g2.py)를 import 하지 않고, 출처 글을 따로 다시 읽어 본다.

출처 글(대조 기준) — COMMON15·COMMON15b 그대로:
- 사업보고서 = dart_out/text/ops15/사업보고서__<회사>__FY<fy>__<rcept>.md(목록 dart_out/ops15/사업보고서_원문.csv). 첫 「### [절 n]」 앞은 버림.
  「### [절 n] 제목」 줄은 제목만 글로, 「[표 n]」「[표 끝]」 줄은 위치 표지(글 아님). 대조 때 공백·줄바꿈과 md 표지 「|」「<br>」를 양쪽에서 지움.
- 연차보고서 FY2023 = dart_out/text/ops15/연차보고서__<회사>__2024__<공시유형>.md(「## p.N」 = PDF 쪽; 목록 연차보고서15_목록_g2.csv).
- 연차보고서 FY2024·FY2025 = dart_out/ops15/kit56/연차보고서_섹션.csv(6차 섹션 글; 섹션순번·chunk_seq 순서, 위치 = 섹션 시작페이지;
  파일 URL·제목·fetched_at 은 handoff/연차보고서_파일목록.csv, 같은 URL(POST)이 여럿이면 gov_old 목록 URL 문자열·sha256 으로 구분).
- 보이지 않는 제어문자(\\x00 등)는 지우고 봄 — 그 출처 글에 제어문자가 있으면 행 note 에 「제어문자 지움」이 있어야 함.

점검:
(a) 원문 대조: source_text 와 모든 원문 칸(chair·members·cadence·agenda·agenda_list·established·function·unit_name·
    concurrent_or_dispatched·duty_text, 확인 CSV source_excerpt) — 「문서에 없음」이 아니면 출처 글의 한 곳에 이어서 그대로 있어야 함.
    위치: 기준 칸(F source_text, F-2 agenda_list_text, F-3 unit_name, 확인 source_excerpt)은 page 칸 위치(절·표 / 쪽 / 섹션 시작페이지)가
    그 글이 있는 곳에서 계산한 위치와 같아야 함. 다른 칸은 그 위치 범위 안에 있거나, note 에 「<칸 이름> … <위치>」(다른 문서면 그 rcept/URL)가 있어야 함.
    FY2025 사업보고서(메리츠·iM·한국투자) page 의 「p.N(본문 PDF, 13차 보관 — 칸 글 K자째부터 20자 위치」는 13차 zip 글에서 그 20자가 처음 나오는 쪽이 N 인지 봄.
    원문 md(dart_out/ops15/원문/F·F2·F3/<회사>__…md)에도 그 칸 글이 이어서 있어야 함.
(b) 꼴: 열 이름·순서, utf-8-sig(BOM), rcept_no_or_url·page·doc_name·collected_at 빈칸 0, collected_at = 출처 목록의 받은 시각(KST +09:00),
    doc_name = 출처 목록의 문서 제목, 행 fy = 출처 문서 fy, 문서목록15b_F_g2.csv 열·BOM·행 출처가 모두 목록에 있음.
(c) 빠짐: F 는 회사×FY2023~2025 마다 행; F-2 는 회사×FY2024·2025×5개 위원회(자회사대표이사후보추천·내부통제·감사·ESG·위험관리) 한 행씩;
    F-3 은 회사마다 감사 행과 준법·위험관리 행. 출처 글(연차보고서 본공시 — JB FY2025 는 정정공시 — 와 사업보고서 본, FY2023~2025)에서
    「…협의회·협의체·회의체·간담회·집행위원회·운영위원회·실무위원회·경영위원회·인사위원회」 이름을 모두 뽑아, 조각 body_name/committee 에 있거나
    아래 NOT_F(검토해서 뺀 이름과 그 까닭 — 자회사 회의체·외부 기구·경력·규정 일반어·이사회 내 위원회·글 조각)에 있어야 함.
(d) 「문서에 없음」 반박: F 의 chair·cadence·held 「문서에 없음」 칸은 그 협의체 이름 앞뒤 글(공백 지운 300자)에서 의장·위원장·주재·매월·분기·반기·격월·
    수시·개최·N회 낱말을 찾고, F-2 「문서에 없음」 위원회는 넓은 이름(자회사·CEO·대표이사 후보추천, ESG·지속가능, 내부통제위원회)을 사업보고서·연차보고서에서 찾고,
    F-3 「문서에 없음」은 준법감시·위험관리·리스크관리 부서 인원 글을 찾음. 걸린 곳은 REVIEWED(검토 결과 — 문서 글이 그 칸 뜻이 아님/ note 에 이미 적음)에 있어야 함.
(e) 숫자: held_count·headcount 전부 — note 「원문 「…」」 이면 그 글이 출처에 있고 숫자가 같은지, 「(판단)」 센 값이면 칸 글에서 다시 셈.
(f) 분류: function_kw(작업 F 키워드 중 body_name·source_text 에 든 낱말, AI·IT 는 앞뒤 영문자 아닐 때), subsidiary_related(agenda_list_text 에
    자회사·그룹·계열사) 재계산. note 의 「」 밖 글에 기능 분류·이유 추정 낱말(추정·보인다·듯·아마·의도·때문에·기능상 등) 없음.
(g) 확인_F_g2.csv: REQUEST15b 「함께 볼 것」 줄(F-2) 글이 item_text 와 같음, g2 대상 회사(BNK)의 FY2024 행이 있음, result 값,
    원문 있음 → source_excerpt 300자 이하·출처에 있음, 문서에 없음 → note 에 찾은 범위, where 가 가리키는 조각 행이 있음.
(h) 비밀 값(DART_API_KEY 값·crtfc_key·40자리 hex) 없음, 산출 경로에 PDF·zip·xml·그림 없음, dart_out/raw·text·ops15/조직도 는 git 무시 폴더.
"""
import csv, os, re, sys, glob, bisect, zipfile, subprocess
from datetime import datetime, timezone, timedelta

csv.field_size_limit(10**9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'dart_out', 'ops15')
NA = '문서에 없음'
G2 = ['메리츠금융지주', 'iM금융지주', 'BNK금융지주', 'JB금융지주', '한국투자금융지주']
KST = timezone(timedelta(hours=9))
CTRL = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]')
WS = re.compile(r'\s+')
KW_F = ['협의회', '협의체', '회의체', '위원회', '그룹', '리스크', '내부통제', '준법', '감사', '소비자보호', 'ESG', '디지털', 'AI', 'IT',
        '정보보호', '브랜드', '시너지', '개최', '분기', '매월']

REQ = {
    'F_g2.csv': ['corp_label', 'fy', 'body_name', 'function_kw', 'chair_text', 'members_text', 'cadence_text', 'held_count', 'agenda_text',
                 'doc_kind', 'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at'],
    'F2_g2.csv': ['corp_label', 'fy', 'committee', 'established', 'held_count', 'agenda_list_text', 'subsidiary_related', 'members_text',
                  'rcept_no', 'page', 'note', 'doc_name', 'collected_at'],
    'F3_g2.csv': ['corp_label', 'fy', 'function', 'unit_name', 'headcount', 'concurrent_or_dispatched', 'duty_text', 'rcept_no_or_url',
                  'page', 'note', 'doc_name', 'collected_at'],
    '확인_F_g2.csv': ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note'],
}
DL_COLS = ['doc_kind', 'corp_label', 'fy_or_date', 'report_nm', 'rcept_no_or_url', 'rcept_dt', 'raw_path', 'sha256', 'fetched_at',
           'text_path', 'status', 'note']
MAIN = {'F_g2.csv': 'source_text', 'F2_g2.csv': 'agenda_list_text', 'F3_g2.csv': 'unit_name', '확인_F_g2.csv': 'source_excerpt'}
OTHER = {'F_g2.csv': ['chair_text', 'members_text', 'cadence_text', 'agenda_text'],
         'F2_g2.csv': ['established', 'members_text'],
         'F3_g2.csv': ['function', 'concurrent_or_dispatched', 'duty_text'],
         '확인_F_g2.csv': []}
SUB = {'F_g2.csv': 'F', 'F2_g2.csv': 'F2', 'F3_g2.csv': 'F3', '확인_F_g2.csv': 'F2'}

# ───────────── (c) 검토해서 F 에서 뺀 이름(공백 지운 이름 → 까닭). 회사별. ─────────────
# 까닭 낱말: 자회사 = 자회사(은행·증권 등) 안의 회의체로 적힌 곳 / 외부 = 그룹 밖 기관·단체 / 경력 = 사람 경력 줄 / 규정 = 규정 조문의 일반어·
# 다른 협의체 규정 안 이름 / 이사회 = 이사회 내 위원회(F-2 쪽) / 조각 = PDF 글 순서 때문에 잘린 이름(앞 글자가 빠져 조각 body_name 의 일부)
NOT_F = {
    '메리츠금융지주': {
        '대출및종목심사협의회': '자회사 — 사업보고서 Ⅱ 「5. 재무건전성 등 기타 참고사항」 「부문별로 금융투자상품선정위원회, 유동성관리협의회, 비상대책실무협의회, 대출및종목심사협의회」(증권 부문)',
        '비상대책실무협의회': '자회사 — 같은 곳(증권 부문별 운영)', '유동성관리협의회': '자회사 — 같은 곳(증권 부문별 운영)',
        '실무협의회': '자회사 — 같은 곳(증권 부문별 운영) 이름의 일부', '조정협의회': '외부감사 서식 항목 — Ⅴ 「1. 외부감사에 관한 사항」 「사. 조정협의회 주요 협의내용」',
        '채권금융기관협의회': '외부', '있습니다협의회': '조각', '관리협의회': '조각', '부통제협의회': '조각(내부통제협의회)',
        '리스크관리협의회': '규정 — 그룹리스크관리위원회규정 「제12조 리스크관리협의회 … 그룹리스크협의회를 둘 수 있다」(조각 그룹리스크협의회 행)',
        '감사협의회': '조각(그룹 감사협의회 행)', '리스크협의회': '조각(그룹리스크협의회 행)',
        '리스크관리실무위원회': '자회사 — 사업보고서 Ⅱ 「5. 재무건전성 등 기타 참고사항」(보험·증권 리스크관리 조직)', '리스크실무위원회': '자회사 — 같은 곳',
        '실무위원회': '자회사 — 같은 곳 이름의 일부',
    },
    'iM금융지주': {
        '경제교육단체협의회': '외부', '조정협의회': '외부감사 서식 항목 — Ⅴ 「1. 외부감사에 관한 사항」 「사. 조정협의회 주요 협의내용」', '한국사회복지협의회': '외부', '지역균형발전협의회': '경력',
        '리스크관리회의체': '규정 — 첨부 그룹리스크관리규정 일반어(「권한이 부여된 리스크관리회의체」)', '크관리회의체': '조각(규정 일반어)',
        '경영협의회': '이사회 — 사업보고서 FY2023 ESG위원회 안건 「ESG 경영협의회 규정 개정」(조각 ESG경영협의회 행)', '리협의회': '조각',
        '위험관리집행위원회': '자회사 — 사업보고서 Ⅱ 「iM뱅크는 위험관리위원회 및 위험관리집행위원회 등」', '인사위원회': '조각(그룹임원인사위원회 행)·노동위원회 등',
        '운영위원회': '외부·규정 일반어',
    },
    'BNK금융지주': {
        'ALM협의회': '자회사 — 사업보고서 Ⅱ 은행 리스크관리 조직', '여신협의회': '자회사 — 같은 곳', '본부심사역협의회': '자회사 — 같은 곳',
        '탄소회계금융협의체': '외부(PCAF)', '한국상장사협의회': '외부', '및한국상장사협의회': '외부', '한국상장회사협의회': '외부',
        '조정협의회': '외부감사 서식 항목 — Ⅴ 「1. 외부감사에 관한 사항」 「사. 조정협의회 주요 협의내용」', '주주간담회': '외부(주주와의 간담회)', '리스크관리회의체': '규정 일반어', '리협의회': '조각',
        '스크관리협의회': '조각(리스크관리협의회 행)', '룹경영관리협의회': '조각(그룹경영관리협의회 행)', '경영관리협의회': '조각(그룹경영관리협의회 행)',
        '리스크관리집행위원회': '자회사 — 사업보고서 Ⅱ 은행 리스크관리 조직', '운영리스크관리집행위원회': '자회사 — 연차보고서 FY2025 리스크관리협의회 부의사항 「자회사 운영리스크관리집행위원회 운영 사항」',
        '통제집행위원회': '조각(내부통제집행위원회 행)', '실무위원회': '규정 — 위원회 규정 「필요에 따라 … 실무위원회를 둘 수 있다」',
        '이사회운영위원회': '이사회 — 이사회 운영 관련 위원회(이사회 내)', '회운영위원회': '조각(이사회운영위원회)', '사회운영위원회': '조각(이사회운영위원회)',
        '운영위원회': '조각·외부', 'ESG운영위원회': '조각 — 연차보고서 FY2023 쪽 머리 글', '인사위원회': '자회사·외부(노동위원회 등)',
        '경영위원회': '조각(그룹경영위원회 행)', '장사협의회': '조각(한국상장사협의회 — 외부)',
        '투명경영위원회': '외부 — 사업보고서 FY2023 Ⅶ 주주에 관한 사항 표의 다른 회사 사외이사 직함 「투명경영위원회위원장」',
    },
    'JB금융지주': {
        '경영간담회': '규정 — 첨부 지배구조내부규범 「사외이사만의 경영간담회를 개최하고 지원할 수 있다」(사외이사 회의)',
        '조정협의회': '외부감사 서식 항목 — Ⅴ 「1. 외부감사에 관한 사항」 「사. 조정협의회 주요 협의내용」', '등간담회': '조각', '및간담회': '조각', '부의하며협의회': '조각', '위원회간담회': '조각',
        '그룹및자회사회의체': '규정 — 리스크관리위원회 보고안건 「그룹 및 자회사 회의체 심의·결의사항」(자회사 리스크관리위원회·지주 리스크관리운영위원회를 가리킴)',
        '및자회사회의체': '조각(같은 곳)', '자회사의회의체': '조각(같은 곳)', '2023년4분기에진행된그룹및자회사의회의체': '조각(같은 곳)',
        '2024년4분기에진행된그룹및자회사의회의체': '조각(같은 곳)', '2025년3분기에진행된그룹및자회사의회의체': '조각(같은 곳)',
        '2022년4분기에진행된그룹및자회사의회의체': '조각(같은 곳)',
        '리스크관리실무위원회': '자회사 — 사업보고서 FY2023 Ⅳ 「고유재산운용규정」 리스크관리실무위원회(자산운용 자회사 서술)',
        '리스크관리운용위원회': '조각(리스크관리운영위원회 행 — 사업보고서 표기)', '관리운영위원회': '조각(리스크관리운영위원회 행)',
        '운영위원회': '조각·외부', '이사회운영위원회': '이사회', '전차운영위원회': '조각', '인사위원회': '자회사·외부',
        '경영위원회': '조각', '자율협의회': '외부 — 사업보고서 FY2025 「5. 부외거래」 소송 표(채권단 자율협의회)',
    },
    '한국투자금융지주': {
        '리스크관리실무협의회': '자회사 — 사업보고서 Ⅱ 「5. 재무건전성 등 기타 참고사항」 증권 「부문별 실무협의회」',
        '실무협의회': '자회사 — 같은 곳', '장외파생상품실무협의회': '자회사 — 같은 곳', '장외파생상품실무협의위원회': '자회사 — 같은 곳',
        '리스크관리실무위원회': '자회사 — 같은 곳', '리스크협의회': '조각(그룹리스크관리협의회 행 — 사업보고서 재무제표 주석에도 「그룹리스크협의회」)',
        '그룹리스크협의회그룹리스크협의회': '조각(같은 협의회 — 사업보고서 연결재무제표 주석 「3) 그룹리스크협의회」, 조각 그룹리스크관리협의회 행)',
        '그룹리스크협의회': '같은 협의회(조각 그룹리스크관리협의회 행) — 사업보고서 재무제표 주석 이름', '룹리스크관리협의회': '조각',
        '리스크관리협의회': '조각(그룹리스크관리협의회 행)', '경영협의회': '조각(그룹경영협의회 행)',
        '경영위원회': '이사회 — 한국투자 경영위원회는 이사회 내 위원회(사업보고서 Ⅵ)', '위원경영위원회': '조각(이사회 내 경영위원회)', '위원장경영위원회': '조각(이사회 내 경영위원회)',
        '운영위원회': '외부', '인사위원회': '외부',
    },
}

# ───────────── (d) 검토 결과: 「문서에 없음」 칸 근처에서 낱말이 걸렸지만 그 칸 뜻의 글이 아닌 곳 ─────────────
# 키 (회사, fy, 이름, 칸) → 까닭. 이름은 공백 지운 body_name / committee.
_BRD = '이사회 회의 내역·안건 표 글(이사 성명·의장·다른 안건의 「분기」「개최」) — 이 회의체의 주재자·주기·횟수 글 아님'
REVIEWED = {
    ('메리츠금융지주', '2023', '경영협의회', 'chair_text'): '협의절차 「협의회 의장이 별도로 소집할 수 있습니다」 — 의장이 누구인지 적은 글 아님(행 note 에 적음)',
    ('메리츠금융지주', '2024', '경영협의회', 'chair_text'): '같음', ('메리츠금융지주', '2025', '경영협의회', 'chair_text'): '같음',
    ('메리츠금융지주', '2025', '내부통제협의회', 'held_count'): '「개최」는 「2025.7.15. 개최된 제3차 내부통제위원회」 글',
    ('한국투자금융지주', '2023', '내부통제위원회', 'cadence_text'): '「매분기」는 감사위원회 감사 실적 표 일상감사 주기 칸(「… 내부통제위원회 개최 등」은 점검 대상 글)',
    ('한국투자금융지주', '2023', '내부통제위원회', 'held_count'): '같은 감사 실적 표 글', ('한국투자금융지주', '2024', '내부통제위원회', 'cadence_text'): '같음',
    ('한국투자금융지주', '2024', '내부통제위원회', 'held_count'): '같음',
    ('iM금융지주', '2023', 'ESG경영협의회', 'chair_text'): 'ESG위원회 글(「ESG위원회 위원장 선임」) — 협의회 글 아님',
    ('iM금융지주', '2023', 'ESG경영협의회', 'held_count'): 'ESG위원회 글(「2023년도 ESG위원회는 총4회 소집」·「안건은 총8건」) — 협의회 글 아님',
    ('BNK금융지주', '2024', '내부통제위원회', 'held_count'): '「개최」는 사업보고서 Ⅰ 정관 표 「제14기 정기주주총회(\'25.3.26 개최예정)」',
    ('BNK금융지주', '2025', '내부통제집행위원회', 'cadence_text'): '「반기」는 「2025년 상반기 내부통제등 총괄관리의무를 수행」(대표이사 의무 수행 기간) 글',
    ('JB금융지주', '2023', '집행위원회', 'chair_text'): _BRD, ('JB금융지주', '2023', '집행위원회', 'cadence_text'): _BRD,
    ('JB금융지주', '2024', '집행위원회', 'chair_text'): _BRD, ('JB금융지주', '2024', '집행위원회', 'cadence_text'): _BRD,
    ('JB금융지주', '2024', '집행위원회', 'held_count'): _BRD, ('JB금융지주', '2025', '집행위원회', 'chair_text'): _BRD,
    ('JB금융지주', '2025', '집행위원회', 'cadence_text'): _BRD, ('JB금융지주', '2025', '집행위원회', 'held_count'): _BRD,
    ('JB금융지주', '2025', '내부통제협의회', 'cadence_text'): '「2025년도 2분기 집행위원회 결의사항」·내부통제위원회 회의 글 — 협의회 주기 글 아님',
    ('JB금융지주', '2025', '내부통제협의회', 'held_count'): '「제2025년도 제3차 내부통제위원회」 개최 글 — 협의회 횟수 글 아님',
    ('한국투자금융지주', '2023', '그룹비상경영위원회', 'chair_text'): '그룹경영협의회규정 제7조 「위원장이 필요하다고 인정하는 경우」(협의회 위원장)·제8조 「그룹리스크관리책임자의 소집요청」 — 비상경영위원회 주재자 글 아님(구성은 제3조를 따름 — members_text)',
    ('한국투자금융지주', '2024', '그룹비상경영위원회', 'chair_text'): '같음', ('한국투자금융지주', '2025', '그룹비상경영위원회', 'chair_text'): '같음',
    ('iM금융지주', '2023', '그룹임원인사위원회', 'chair_text'): _BRD, ('iM금융지주', '2024', '그룹임원인사위원회', 'chair_text'): _BRD,
    ('iM금융지주', '2024', '그룹임원인사위원회', 'held_count'): _BRD + '(「KLPGA투어 개최 계약」)',
    ('iM금융지주', '2025', '그룹임원인사위원회', 'cadence_text'): _BRD, ('iM금융지주', '2025', '그룹임원인사위원회', 'chair_text'): _BRD + '(「이사회 의장 선임」)',
    ('iM금융지주', '2025', '집행위원회', 'cadence_text'): _BRD,
    # F-2 「문서에 없음」 위원회(FY2024 내부통제위원회) — 넓은 이름이 걸린 곳
    ('메리츠금융지주', '2024', '내부통제위원회', 'BR'): '사업보고서 FY2024 Ⅵ 준법감시인 활동 표 「반기 | 내부통제위원회 활동」 — F_g2.csv 메리츠 FY2024 「내부통제위원회」 행(이사회 내 위원회 아님 판단)',
    ('한국투자금융지주', '2024', '내부통제위원회', 'BR'): '사업보고서 FY2024 Ⅰ 정관 변경 표(2025년03월28일 제23기 정기주주총회 「이사회내 내부통제위원회 신설」)·Ⅵ 준법지원실 활동 칸 — FY2024 위원회 구성·개최 글 아님',
    ('한국투자금융지주', '2024', '내부통제위원회', 'AR_kit'): '연차보고서 FY2024 「이사회 내 위원회와는 별도로 … 대표이사를 위원장으로 하는 내부통제위원회」 — F_g2.csv 한국투자 FY2024 「내부통제위원회」 행',
    ('iM금융지주', '2024', '내부통제위원회', 'BR'): '사업보고서 FY2024 Ⅰ 정관 변경 표 「2024.03.28 제13기 정기주주총회 1.내부통제위원회 신설(45조)」 — 조항 신설 글(F2 행 note 에 적음)',
    ('iM금융지주', '2024', '내부통제위원회', 'AR_kit'): '연차보고서 FY2024 「10. 내부통제위원회」 「설치 예정」·「해당사항 없음」, 첨부 정관 목록(F2 행 note 에 적음)',
    ('BNK금융지주', '2024', '내부통제위원회', 'BR'): '사업보고서 FY2024 Ⅰ 정관 표(제14기 정기주주총회 예정 안건)·지배구조법 개정 서술·Ⅵ 준법지원인 표(F_g2.csv BNK FY2024 「내부통제위원회」 행)',
    ('BNK금융지주', '2024', '내부통제위원회', 'AR_kit'): '연차보고서 FY2024 「11.내부통제위원회」 규정 제정 결의·시행 예정 글, 첨부 규정 목록(F2 행 note·확인 F2-BNK-1 에 적음)',
    ('JB금융지주', '2024', '내부통제위원회', 'BR'): '사업보고서 FY2024 Ⅰ 정관 변경 표(2025년03월27일 정기주주총회)·Ⅳ 서술·Ⅵ 준법지원인 표(F_g2.csv JB FY2024 「내부통제 위원회」 행)',
    # F-3 「문서에 없음」(준법·위험관리 지원조직) — 걸린 곳
    ('iM금융지주', '2025', NA, 'F3'): '「2) 준법감시직원 현황 - 해당사항 없음」(F3 행 note 에 적음)·위험관리협의회 구성 글(「리스크관리부서장을 위원으로 하여 총6명」) — 지원조직 현황 표 아님',
    ('BNK금융지주', '2025', NA, 'F3'): '첨부 규정 조문 「그룹 준법감시인의 직무와 지원조직 등에 관한 세부사항」 — 현황 표 아님',
    ('JB금융지주', '2025', NA, 'F3'): '리스크관리운영위원회 구성 글·변동보상 대상자 글(「리스크관리책임자 1명, 내부감사책임자 1명」) — 지원조직 현황 아님(조직도 글은 F3 행 note 에 적음)',
}


def rd(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


def norm(t, xml=False):
    t = CTRL.sub('', t or '')
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return WS.sub('', t)


def to_kst(s):
    s = (s or '').strip()
    if s.endswith('+0000'):
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S+0000').replace(tzinfo=timezone.utc).astimezone(KST).isoformat()
    return s


class Src:
    """출처 글: segs = [(위치표지, 글)] → 공백 지운 글 s, 위치 시작점 pos."""

    def __init__(self, kind, ref, corp, fy, title, fetched, segs, xml, path):
        self.kind, self.ref, self.corp, self.fy, self.title, self.fetched, self.xml, self.path = kind, ref, corp, fy, title, fetched, xml, path
        self.nctrl = sum(len(CTRL.findall(t)) for _, t in segs)
        parts, self.pos, self.lab, n = [], [], [], 0
        for lab, t in segs:
            s = norm(t, xml)
            self.pos.append(n)
            self.lab.append(lab)
            parts.append(s)
            n += len(s)
        self.s = ''.join(parts)

    def label(self, i):
        k = bisect.bisect_right(self.pos, i) - 1
        return self.lab[k] if k >= 0 else ''

    def occ(self, val):
        v = norm(val, self.xml)
        out, i = [], self.s.find(v) if v else -1
        while i >= 0 and v:
            out.append((i, i + len(v)))
            i = self.s.find(v, i + 1)
        return out

    def page_of(self, a, b):
        la, lb = self.label(a), self.label(b - 1)
        if self.kind == 'BR':
            return la if la == lb else f'{la} ~ {lb}'
        return f'p.{la}' if la == lb else f'p.{la}~{lb}'

    def num_of(self, i):
        """위치 비교용 수: 사업보고서 = 절 번호, 연차보고서 = 쪽(섹션 시작페이지)."""
        lab = self.label(i)
        m = re.search(r'\[절 (\d+)\]', lab) if self.kind == 'BR' else re.match(r'(\d+)', lab)
        return int(m.group(1)) if m else None


BRL = rd(os.path.join(OUT, '사업보고서_원문.csv'))
ARL = rd(os.path.join(OUT, '연차보고서15_목록_g2.csv'))
KITF = [r for r in rd(os.path.join(ROOT, 'handoff', '연차보고서_파일목록.csv')) if '지배구조' in r['파일명']]
GOVP = os.path.join(OUT, '문서목록15b_gov_old.csv')
GOV = rd(GOVP) if os.path.exists(GOVP) else []
_kit, _src = None, {}


def kit_rows():
    global _kit
    if _kit is None:
        _kit = {}
        for k in rd(os.path.join(OUT, 'kit56', '연차보고서_섹션.csv')):
            if k['지주명'] in G2:
                _kit.setdefault(k['파일명'], []).append(k)
    return _kit


def load_br(rcept):
    x = [r for r in BRL if r['rcept_no'] == rcept]
    if not x or not x[0]['text_path']:
        return None
    x = x[0]
    segs, started, sec = [], False, ''
    cur = None
    for ln in open(os.path.join(ROOT, x['text_path']), encoding='utf-8').read().split('\n'):
        m = re.match(r'^### \[절 (\d+)\] ?(.*)$', ln)
        if m:
            started = True
            sec = f'XML [절 {m.group(1)}] 「{m.group(2).strip()}」'
            cur = [sec, [m.group(2)]]
            segs.append(cur)
            continue
        if not started:
            continue
        mt = re.match(r'^\[표 (\d+)\]\s*$', ln.strip())
        if mt:
            cur = [sec + f' [표 {mt.group(1)}]', []]
            segs.append(cur)
            continue
        if ln.strip() == '[표 끝]':
            cur = [sec, []]
            segs.append(cur)
            continue
        cur[1].append(ln)
    return Src('BR', rcept, x['label'], int(x['fy']), x['report_nm'], x['fetched_at'], [(a, '\n'.join(b)) for a, b in segs], True,
               x['text_path'])


def load_ar_md(meta, ref):
    p = os.path.join(ROOT, 'dart_out', 'text', 'ops15', f"연차보고서__{meta['회사']}__{meta['공시연도']}__{meta['공시유형']}.md")
    if not os.path.exists(p):
        return None
    segs, cur = [], None
    for ln in open(p, encoding='utf-8').read().split('\n'):
        m = re.match(r'^## p\.(\d+)(\s.*)?$', ln)
        if m:
            cur = [m.group(1), []]
            segs.append(cur)
            continue
        if cur is not None:
            cur[1].append(ln)
    return Src('AR_md', ref, meta['회사'], int(meta['공시연도']) - 1, meta['제목'], meta['fetched_at'],
               [(a, '\n'.join(b)) for a, b in segs], False, os.path.relpath(p, ROOT))


def load_kit(meta, ref):
    rows = sorted(kit_rows().get(meta['파일명'], []), key=lambda k: (int(k['섹션순번']), int(k['chunk_seq'])))
    if not rows:
        return None
    segs = [(k['시작페이지'] or '?', k['본문']) for k in rows if k['본문']]
    return Src('AR_kit', ref, meta['지주명'], int(meta['공시연도']) - 1, meta['제목'], to_kst(meta['fetched_at']), segs, False,
               f"kit56 {meta['파일명']}")


def resolve_ar(ref):
    c = [r for r in ARL if r['파일_url'] == ref]
    if not c:
        c = [r for r in ARL if r['파일_url'].split(' (')[0] == ref]
        if len(c) > 1:
            c = []
    if len(c) == 1:
        return load_ar_md(c[0], ref)
    k = [r for r in KITF if r['url'] == ref]
    if len(k) == 1:
        return load_kit(k[0], ref)
    g = [r for r in GOV if r.get('rcept_no_or_url') == ref]
    if len(g) == 1:
        k = [r for r in KITF if r['sha256'] == g[0]['sha256']]
        if len(k) == 1:
            return load_kit(k[0], ref)
    m = re.match(r'^(.*) \(파일명 (.+)\)$', ref)
    if m:
        k = [r for r in KITF if r['파일명'] == m.group(2) and r['url'] == m.group(1)]
        if len(k) == 1:
            return load_kit(k[0], ref)
    return None


def src(ref):
    if ref not in _src:
        _src[ref] = load_br(ref) if re.fullmatch(r'\d{14}', ref) else (resolve_ar(ref) if ref.startswith('http') else None)
    return _src[ref]


def ar_doc(co, fy, typ='본공시'):
    """회사·FY 연차보고서(공시연도 FY+1) 글."""
    yr = fy + 1
    if yr <= 2024:
        c = [r for r in ARL if r['회사'] == co and r['공시연도'] == str(yr) and r['공시유형'] == typ]
        if not c:
            return None
        ref = c[0]['파일_url'].split(' (')[0]
        if sum(1 for r in ARL if r['파일_url'].split(' (')[0] == ref) > 1:
            ref = c[0]['파일_url']
        return src(ref) or load_ar_md(c[0], ref)
    c = [r for r in KITF if r['지주명'] == co and r['공시연도'] == str(yr) and r['공시유형'] == typ]
    return load_kit(c[0], c[0]['url']) if c else None


def br_doc(co, fy):
    c = [r for r in BRL if r['label'] == co and r['fy'] == str(fy) and r['kind'] == '본']
    return src(c[0]['rcept_no']) if c else None


ALL_REFS = sorted(set([r['파일_url'] for r in ARL] + [r['파일_url'].split(' (')[0] for r in ARL] + [r['url'] for r in KITF] +
                      [r['rcept_no_or_url'] for r in GOV if r.get('rcept_no_or_url', '').startswith('http')]), key=len, reverse=True)


def note_refs(note):
    out = re.findall(r'(?<!\d)(\d{14})(?!\d)', note or '')
    rest = note or ''
    for u in ALL_REFS:
        if u and u in rest:
            out.append(u)
            rest = rest.replace(u, ' ')
    return list(dict.fromkeys(out))


def fkw(*texts):
    t = re.sub(r'\s+', '', ' '.join(texts))
    out = []
    for k in KW_F:
        if k in ('AI', 'IT'):
            if re.search(r'(?<![A-Za-z])' + k + r'(?![A-Za-z])', t):
                out.append(k)
        elif k in t:
            out.append(k)
    return ', '.join(out)


# ───────────── 13차 FY2025 사업보고서 본문 PDF 글 ─────────────
_p13 = {}


def p13(co):
    if co not in _p13:
        z = zipfile.ZipFile(os.path.join(ROOT, 'handoff', '13차_지주관리유형', '13차_지주관리유형_텍스트.zip'))
        nm = [n for n in z.namelist() if n.endswith(f'텍스트/사업보고서__{co}.md')]
        if not nm:
            _p13[co] = None
        else:
            t = z.read(nm[0]).decode('utf-8')
            parts, pos, n = [], [], 0
            ms = list(re.finditer(r'(?m)^## p\.(\d+).*$', t))
            for i, m in enumerate(ms):
                body = t[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(t)]
                c = WS.sub('', body)
                pos.append((n, int(m.group(1))))
                parts.append(c)
                n += len(c)
            _p13[co] = (''.join(parts), pos)
    return _p13[co]


def page_parts(page):
    """page 칸 → (위치 부분, 13차 부분)."""
    main = page.split(' / ')[0].replace(' (6차 섹션 시작페이지)', '').strip()
    return main, page[len(page.split(' / ')[0]):]


def range_nums(d, page_main):
    if d.kind == 'BR':
        ns = [int(x) for x in re.findall(r'\[절 (\d+)\]', page_main)]
    else:
        m = re.fullmatch(r'p\.(\d+)(?:~(\d+))?', page_main)
        ns = [int(m.group(1)), int(m.group(2) or m.group(1))] if m else []
    return (min(ns), max(ns)) if ns else None


def wonmun_text(co, sub):
    """원문 md(회사·작업 폴더) 글 — 머리 줄·「## 위치」 줄 빼고 공백·「|」「<br>」 지움."""
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, '원문', sub, f'{co}__*.md'))):
        body = False
        for ln in open(p, encoding='utf-8').read().split('\n'):
            if re.match(r'^## (p\.|XML \[절 )', ln):  # 위치 머리 줄(이 줄부터 글)
                body = True
                out.append('¶')  # 떨어진 구간끼리 잇지 않음
                continue
            if body:
                out.append(ln)
    return norm('\n'.join(out), True)


SPEC_WORDS = ['추정', '보인다', '보임', '듯하', '듯함', '아마', '의도', '때문에', '때문으로', '기능상', '기능 분류', '것으로 보', '것 같']


def outside_quotes(t):
    return re.sub(r'「[^」]*」', '', t or '')


def count_date_rows(txt):
    """md 표 행 중 앞 3칸 중 한 칸이 날짜만(YYYY.M.D) 적힌 행 수."""
    n = 0
    for ln in txt.split('\n'):
        if not ln.startswith('|'):
            continue
        cells = [re.sub(r'\s|<br>', '', c) for c in ln.strip().strip('|').split('|')][:3]
        if any(re.fullmatch(r'20\d\d\.\d{1,2}\.\d{1,2}\.?', c) for c in cells):
            n += 1
    return n


DATE_RX = re.compile(r'(?<!\d)(20\d\d|\d\d)\s*[.\-년/]\s*(\d{1,2})\s*[.\-월/]\s*(\d{1,2})(?!\d)')


def table_date_rows(txt):
    """「개최일자」류 머리 칸 아래에서 날짜가 있는 행 수(머리 칸 열 → 없으면 그 열 앞 칸)."""
    rows, col = 0, None
    for ln in txt.split('\n'):
        if not ln.startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        hit = [i for i, c in enumerate(cells) if re.sub(r'\s|<br>', '', c) in ('개최일자', '개최일', '개최일시', '일자', '개최일자(회차)', '개최일(회차)', '회의일자')]
        if hit:
            col = hit[0]
            continue
        if col is None:
            continue
        nz = lambda c: re.sub(r'<br>|\s', '', c)
        m = DATE_RX.search(nz(cells[col])) if col < len(cells) else None
        if not m:
            for c in cells[:col + 1]:
                m = DATE_RX.search(nz(c))
                if m:
                    break
        if m:
            rows += 1
    return rows


def main():
    lines, fails, review, numlog = [], [], [], []
    checks = 0
    data = {}

    def ck(cond, msg):
        nonlocal checks
        checks += 1
        if not cond:
            fails.append(msg)
        return cond

    # ── (b) 파일 꼴 ──
    for fn, cols in REQ.items():
        p = os.path.join(OUT, '조각', fn)
        if not ck(os.path.exists(p), f'{fn}: 파일 없음'):
            continue
        raw = open(p, 'rb').read()
        ck(raw[:3] == b'\xef\xbb\xbf', f'{fn}: utf-8-sig(BOM) 아님')
        hdr = next(csv.reader(open(p, encoding='utf-8-sig')))
        ck(hdr == cols, f'{fn}: 열 이름·순서 다름 {hdr}')
        data[fn] = rd(p)
    dlp = os.path.join(OUT, '문서목록15b_F_g2.csv')
    dl = []
    if ck(os.path.exists(dlp), '문서목록15b_F_g2.csv 없음'):
        ck(open(dlp, 'rb').read()[:3] == b'\xef\xbb\xbf', '문서목록: BOM 아님')
        ck(next(csv.reader(open(dlp, encoding='utf-8-sig'))) == DL_COLS, '문서목록: 열 다름')
        dl = rd(dlp)
        for i, r in enumerate(dl, 2):
            ck(r['status'] in ('받음', '014', '없음', '막힘', '실패'), f'문서목록:{i} status 「{r["status"]}」')
            if r['status'] == '받음' and r['rcept_no_or_url']:
                ck(bool(r['fetched_at']), f'문서목록:{i} fetched_at 비어 있음')
    dl_refs = set(r['rcept_no_or_url'] for r in dl)

    wonmun = {}
    na_count = {}
    # ── 행 점검 ──
    for fn, rows in data.items():
        main_col = MAIN[fn]
        na_rows = 0
        for i, r in enumerate(rows, 2):
            name = r.get('body_name') or r.get('committee') or r.get('unit_name') or r.get('item_id')
            key = f"{fn}:{i} {r.get('corp_label')} FY{r.get('fy')} {name}"
            co = r.get('corp_label')
            ck(co in G2, f'{key}: g2 밖 회사')
            ref = r.get('rcept_no_or_url') or r.get('rcept_no') or ''
            note = r.get('note') or ''
            is_chk = fn == '확인_F_g2.csv'
            if any((r.get(c) or '') == NA for c in r):
                na_rows += 1
                ck(bool(note.strip()), f'{key}: 「문서에 없음」 칸이 있는데 note 비어 있음')
            # (b) 빈칸
            for c in (['rcept_no_or_url' if 'rcept_no_or_url' in r else 'rcept_no', 'page'] + ([] if is_chk else ['doc_name', 'collected_at'])):
                if is_chk and r.get('result') != '원문 있음' and c == 'page':
                    continue
                ck(bool((r.get(c) or '').strip()), f'{key}: {c} 비어 있음')
            if not is_chk:
                ck(r['collected_at'].endswith('+09:00'), f'{key}: collected_at KST 아님')
                ck(ref in dl_refs, f'{key}: 출처 {ref[:60]} 가 문서목록에 없음')
            d = src(ref) if ref else None
            if not ck(d is not None, f'{key}: 출처 글을 못 읽음 {ref[:80]}'):
                continue
            ck(d.corp == co, f'{key}: 출처 문서 회사 {d.corp} ≠ {co}')
            if not is_chk:
                ck(r['doc_name'] == d.title, f'{key}: doc_name 「{r["doc_name"]}」 ≠ 목록 제목 「{d.title}」')
                ck(r['collected_at'] == d.fetched, f'{key}: collected_at {r["collected_at"]} ≠ 목록 받은 시각 {d.fetched}')
            ck(str(d.fy) == str(r['fy']), f'{key}: 출처 문서 FY{d.fy} ≠ 행 fy {r["fy"]}')
            if d.nctrl:
                texts = [r.get(c) for c in [main_col] + OTHER[fn] if r.get(c) and r.get(c) != NA]
                if texts and not is_chk:
                    ck('제어문자 지움' in note, f'{key}: 출처 글에 제어문자 {d.nctrl}개 — note 「제어문자 지움」 없음')
            # (a) 기준 칸 위치
            page = r.get('page') or ''
            pmain, p13part = page_parts(page)
            mv = r.get(main_col) or ''
            rng = None
            if mv and mv != NA:
                oc = d.occ(mv)
                if ck(bool(oc), f'{key}: {main_col} 원문 대조 실패(출처에 이어서 없음) 「{mv[:50]}」'):
                    pages = [d.page_of(a, b) for a, b in oc]
                    ck(pmain in pages, f'{key}: page 「{pmain}」 ≠ 그 글 위치 {pages[:3]}')
                    rng = range_nums(d, pmain)
                if '…' in mv:
                    ck(bool(oc), f'{key}: {main_col} 에 원문에 없는 「…」')
            elif mv == NA and not is_chk:
                ck('찾은' in note, f'{key}: {main_col} 「문서에 없음」 — note 에 찾은 범위 없음')
            # 13차 쪽
            if p13part:
                m = re.search(r'p\.(\d+)\(본문 PDF, 13차 보관 — 칸 글 (\d+)자째부터 20자 위치', p13part)
                if m:
                    P = p13(co)
                    k = norm(mv, True)[int(m.group(2)):int(m.group(2)) + 20]
                    h = P[0].find(k) if P else -1
                    pg_ = None
                    if h >= 0:
                        pg_ = [x[1] for x in P[1]][bisect.bisect_right([x[0] for x in P[1]], h) - 1]
                    ck(pg_ == int(m.group(1)), f'{key}: 13차 쪽 p.{m.group(1)} ≠ 다시 찾은 쪽 {pg_}')
                else:
                    ck('13차 보관 본문 PDF 글에서 칸 글 첫머리를 못 찾음' in p13part, f'{key}: 13차 쪽 꼴 모름 「{p13part[:60]}」')
            elif (d.kind == 'BR' and co in ('메리츠금융지주', 'iM금융지주', '한국투자금융지주') and d.fy == 2025 and mv and mv != NA
                  and ref == [x['rcept_no'] for x in BRL if x['label'] == co and x['fy'] == '2025' and x['kind'] == '본'][0]):
                ck(False, f'{key}: FY2025 사업보고서 행인데 13차 본문 PDF 쪽(COMMON15 page 규칙)이 없음')
            # (a) 다른 칸
            for c in OTHER[fn]:
                v = r.get(c) or ''
                if not v or v == NA:
                    continue
                oc = d.occ(v)
                ok = False
                if oc:
                    if rng and any(rng[0] <= (d.num_of(a) or -1) <= rng[1] for a, b in oc):
                        ok = True
                    else:
                        for a, b in oc:
                            lab = d.label(a)
                            locs = re.findall(r'\[절 \d+\]', lab) if d.kind == 'BR' else [f'p.{lab}']
                            if c in note and all(x in note for x in locs):
                                ok = True
                                break
                    ck(ok, f'{key}: {c} 가 page 위치 밖({d.page_of(*oc[0])})인데 note 에 위치가 없음')
                else:
                    others = [x for x in note_refs(note) if x != ref]
                    hit = [x for x in others if src(x) and src(x).occ(v)]
                    ck(bool(hit) and c in note, f'{key}: {c} 원문 대조 실패 「{v[:50]}」')
                if '…' in v and not ok and not oc:
                    fails.append(f'{key}: {c} 에 원문에 없는 「…」')
            # 원문 md
            sub = SUB[fn]
            if (co, sub) not in wonmun:
                wonmun[(co, sub)] = wonmun_text(co, sub)
            for c in [main_col] + OTHER[fn]:
                v = r.get(c) or ''
                if v and v != NA:
                    ck(norm(v, True) in wonmun[(co, sub)], f'{key}: {c} 글이 원문 md(원문/{sub}/{co}__*.md)에 없음')
            # (f) 분류 칸
            if fn == 'F_g2.csv':
                exp = fkw(r['body_name'], r['source_text'] if r['source_text'] != NA else '')
                ck(r['function_kw'] == exp, f'{key}: function_kw 「{r["function_kw"]}」 ≠ 재계산 「{exp}」')
                ck(r['fy'] in ('2023', '2024', '2025'), f'{key}: fy 범위 밖')
            if fn == 'F2_g2.csv':
                a = r['agenda_list_text']
                exp = NA if a == NA else ('Y' if re.search('자회사|그룹|계열사', WS.sub('', a)) else 'N')
                ck(r['subsidiary_related'] == exp, f'{key}: subsidiary_related 「{r["subsidiary_related"]}」 ≠ 재계산 「{exp}」')
                ck(r['fy'] in ('2024', '2025'), f'{key}: fy 범위 밖')
            if fn == 'F3_g2.csv':
                ck(r['fy'] == '2025', f'{key}: fy 범위 밖')
            bad = [w for w in SPEC_WORDS if w in outside_quotes(note)]
            ck(not bad, f'{key}: note 에 추정·기능분류 낱말 {bad}')
            # (e) 숫자
            for c in ('held_count', 'headcount'):
                if c not in r or r[c] in ('', NA):
                    continue
                v = r[c]
                if not ck(re.fullmatch(r'\d+', v) is not None, f'{key}: {c} 숫자 아님 「{v}」'):
                    continue
                m = re.search(c + r' 원문 「([^」]+)」', note)
                if m:
                    q = m.group(1)
                    nums = re.findall(r'\d+', WS.sub('', q))
                    ok = (v in nums) and (bool(d.occ(q)) or any(src(x) and src(x).occ(q) for x in note_refs(note)))
                    mj = re.search(r'\(판단\)([^/]*?)더함', note)
                    if c == 'headcount' and mj and not ok:  # 원문에 합계가 없어 더한 값: (판단) 글의 「N명」을 더해 봄
                        tot = sum(int(x) for x in re.findall(r'(\d+)\s*명', mj.group(1)))
                        ok = str(tot) == v and bool(d.occ(q))
                    ck(ok, f'{key}: {c} {v} — note 원문 「{q[:40]}」 과 안 맞음')
                    numlog.append(f'{key}: {c}={v} ← 원문 「{q[:50]}」 ' + ('OK' if ok else 'X'))
                    continue
                if '활동 표에서 앞 3칸 중 한 칸이 개최일자' in note:
                    srcf = 'agenda_list_text' if fn == 'F2_g2.csv' else 'agenda_text'
                    n = count_date_rows(r[srcf])
                    ck(str(n) == v, f'{key}: {c} {v} ≠ 다시 센 행 수 {n}')
                    numlog.append(f'{key}: {c}={v} ← 다시 센 날짜 행 {n} ' + ('OK' if str(n) == v else 'X'))
                    continue
                if '개최 내역 표에서 개최일이 적힌 행 수를 셈' in note:
                    n = table_date_rows(r['agenda_list_text'])
                    ck(str(n) == v, f'{key}: {c} {v} ≠ 다시 센 개최일 행 {n}')
                    numlog.append(f'{key}: {c}={v} ← 다시 센 개최일 행 {n} ' + ('OK' if str(n) == v else 'X'))
                    continue
                m = re.search(r'\(판단\) held_count 는 (\w+) 의 회의별 개최일 글\((\d+)개', note)
                if m:
                    fld = m.group(1)
                    ds = set(re.findall(r'\((20\d\d\.\d{2}\.\d{2})\)', WS.sub('', r.get(fld, ''))))
                    ck(str(len(ds)) == v, f'{key}: {c} {v} ≠ 다시 센 개최일 {len(ds)}')
                    numlog.append(f'{key}: {c}={v} ← 다시 센 「(YYYY.MM.DD)」 {len(ds)} ' + ('OK' if str(len(ds)) == v else 'X'))
                    continue
                m = re.search(r'\(판단\) ' + c + r'[^「]*「([^」]+)」', note)
                if m and ' / ' in m.group(1):  # PDF 글 줄을 「 / 」로 이어 적은 인용 — 줄마다 출처에 있고 숫자가 그 안에 있어야 함
                    parts = m.group(1).split(' / ')
                    ok = all(d.occ(x) for x in parts) and v in re.findall(r'\d+', m.group(1))
                    ck(ok, f'{key}: {c} {v} — (판단) 근거 PDF 글 「{m.group(1)[:40]}」 과 안 맞음')
                    numlog.append(f'{key}: {c}={v} ← (판단) PDF 글 줄 「{m.group(1)[:50]}」 ' + ('OK' if ok else 'X'))
                    continue
                if m and d.occ(m.group(1)):
                    nums = re.findall(r'\d+', m.group(1))
                    ok = v in nums or str(sum(int(x) for x in nums)) == v
                    ck(ok, f'{key}: {c} {v} — (판단) 근거 글 「{m.group(1)[:40]}」 과 안 맞음')
                    numlog.append(f'{key}: {c}={v} ← (판단) 근거 「{m.group(1)[:50]}」 ' + ('OK' if ok else 'X'))
                    continue
                ck(False, f'{key}: {c} 근거(원문 「…」 또는 (판단) 센 방법) note 없음 — 다시 대조 못 함')
            # (e) F-2 사업보고서 표로 센 횟수 ↔ 연차보고서 「총 N회」 맞대기 note: 인용 글이 그 FY 연차보고서에 있고, 같음/다름이 맞는지
            if fn == 'F2_g2.csv' and r['held_count'] not in ('', NA):
                m = re.search(r'연차보고서 FY(\d{4}) (p\.[\d~]+) 원문 「([^」]+)」 — 사업보고서 표로 센 (\d+)회와 (같음|다름)', note)
                if m:
                    ad = ar_doc(co, int(m.group(1)), '정정공시' if (co == 'JB금융지주' and m.group(1) == '2025') else '본공시')
                    oc = ad.occ(m.group(3)) if ad else []
                    n_ar = re.findall(r'총\s*(\d+)\s*(?:회|차례)', m.group(3))
                    ok = bool(oc) and m.group(4) == r['held_count'] and bool(n_ar) and ((n_ar[0] == r['held_count']) == (m.group(5) == '같음'))
                    ck(ok, f'{key}: 연차보고서 횟수 맞대기 note 가 원문과 안 맞음 「{m.group(3)[:40]}」')
                    numlog.append(f'{key}: held_count={r["held_count"]} ↔ 연차보고서 FY{m.group(1)} {m.group(2)} 「{m.group(3)[:40]}」 {m.group(5)} ' + ('OK' if ok else 'X'))
                else:
                    ck('대조 못 함' in note, f'{key}: 연차보고서 횟수 맞대기 note 없음')
        na_count[fn] = na_rows
        lines.append(f'{fn}: 행 {len(rows)}, 「문서에 없음」 칸이 있는 행 {na_rows}')

    F, F2, F3, CHK = (data.get(x, []) for x in ('F_g2.csv', 'F2_g2.csv', 'F3_g2.csv', '확인_F_g2.csv'))

    # ── (c) 범위 ──
    for co in G2:
        for fy in ('2023', '2024', '2025'):
            ck(any(r['corp_label'] == co and r['fy'] == fy for r in F), f'빠짐: F {co} FY{fy} 행 없음')
        for fy in ('2024', '2025'):
            cats = {'자회사대표이사후보추천': 0, '내부통제': 0, '감사': 0, 'ESG': 0, '위험관리': 0}
            for r in F2:
                if r['corp_label'] != co or r['fy'] != fy:
                    continue
                c = r['committee']
                cat = ('자회사대표이사후보추천' if '후보추천' in c else '내부통제' if '내부통제' in c else '감사' if '감사' in c else
                       'ESG' if 'ESG' in c else '위험관리' if ('리스크' in c or '위험' in c) else None)
                ck(cat is not None, f'F2 {co} FY{fy}: 위원회 「{c}」 5개 범주 밖')
                if cat:
                    cats[cat] += 1
            for k, n in cats.items():
                ck(n == 1, f'빠짐/겹침: F2 {co} FY{fy} {k} 행 {n}개')
        f3 = [r for r in F3 if r['corp_label'] == co]
        ck(any('감사' in (r['function'] + r['unit_name']) for r in f3), f'빠짐: F3 {co} 감사 행 없음')
        ck(any('준법감시인·위험관리책임자' in r['note'] or '준법' in r['function'] or '리스크' in r['function'] or '위험' in r['function'] for r in f3),
           f'빠짐: F3 {co} 준법·위험관리 행 없음')
    # 이름 훑기
    have = {co: set() for co in G2}
    for r in F:
        have[r['corp_label']].add(WS.sub('', r['body_name']))
    for r in F2:
        have[r['corp_label']].add(WS.sub('', r['committee']))
    RX = re.compile(r'([가-힣A-Za-z0-9·]{1,20}(?:협의회|협의체|회의체|간담회|집행위원회|운영위원회|실무위원회|경영위원회|인사위원회))')
    for co in G2:
        names = {}
        for fy in (2023, 2024, 2025):
            for d in (ar_doc(co, fy, '정정공시' if (co == 'JB금융지주' and fy == 2025) else '본공시'), br_doc(co, fy)):
                if d is None:
                    fails.append(f'빠짐 훑기: {co} FY{fy} 출처 글 못 읽음')
                    continue
                raw_lines = []
                if d.kind == 'BR':
                    raw = open(os.path.join(ROOT, d.path), encoding='utf-8').read()
                elif d.kind == 'AR_md':
                    raw = open(os.path.join(ROOT, d.path), encoding='utf-8').read()
                else:
                    rows = sorted(kit_rows()[d.path.split(' ', 1)[1]], key=lambda k: (int(k['섹션순번']), int(k['chunk_seq'])))
                    raw = '\n'.join(k['본문'] for k in rows)
                raw = CTRL.sub('', raw)
                for m in RX.finditer(raw):
                    names.setdefault(m.group(1), set()).add(f"{'BR' if d.kind == 'BR' else 'AR'}{fy}")
        for n, w in sorted(names.items()):
            checks += 1
            if any(h and (h in n or n in h) for h in have[co]):
                continue
            if n in NOT_F.get(co, {}):
                continue
            fails.append(f'빠짐 검토 안 됨: {co} 「{n}」({",".join(sorted(w))}) — 조각에도 NOT_F 에도 없음')

    # ── (d) 「문서에 없음」 반박 ──
    CUE = {'chair_text': r'의장|위원장|주재|주관', 'cadence_text': r'매월|매분기|분기|반기|격월|수시|정기회의|연\d+회|월\d+회|주\d+회',
           'held_count': r'\d+회|총\d+|개최'}
    for r in F:
        d = src(r['rcept_no_or_url'])
        if d is None:
            continue
        bn = WS.sub('', r['body_name'])
        for c, cue in CUE.items():
            if r[c] != NA:
                continue
            hits = []
            for a, b in d.occ(bn):
                w = d.s[max(0, a - 150):b + 150]
                hits += re.findall(cue, w)
            checks += 1
            k = (r['corp_label'], r['fy'], bn, c)
            if hits and k not in REVIEWED:
                review.append(f'반박 검토: F {k} 이름 앞뒤 150자에 {sorted(set(hits))[:6]}')
    F2_WIDE = {'자회사대표이사후보추천': r'자회사[^。]{0,8}(대표|CEO|최고경영자)[^。]{0,8}추천|자회사CEO|자회사대표이사후보', 'ESG': r'ESG위원회|지속가능경영위원회|지속가능위원회',
               '내부통제': r'내부통제위원회'}
    for r in F2:
        if r['agenda_list_text'] != NA:
            continue
        c = r['committee']
        cat = '자회사대표이사후보추천' if '후보추천' in c else '내부통제' if '내부통제' in c else 'ESG' if 'ESG' in c else None
        if not cat:
            continue
        for d in (br_doc(r['corp_label'], int(r['fy'])), ar_doc(r['corp_label'], int(r['fy']), '정정공시' if (r['corp_label'] == 'JB금융지주' and r['fy'] == '2025') else '본공시')):
            if d is None:
                continue
            hs = sorted(set(re.findall(F2_WIDE[cat], d.s)))
            checks += 1
            k = (r['corp_label'], r['fy'], WS.sub('', c), d.kind)
            if hs and k not in REVIEWED:
                review.append(f'반박 검토: F2 {k} 넓은 이름 걸림 {hs[:5]}')
    for r in F3:
        if r['unit_name'] != NA:
            continue
        d = ar_doc(r['corp_label'], 2025, '정정공시' if r['corp_label'] == 'JB금융지주' else '본공시')
        hs = sorted(set(re.findall(r'준법감시(?:인|직원|부서|부|팀)[^。]{0,12}(?:지원조직|인원|현황|\d+명)|(?:위험관리|리스크관리)(?:책임자|부서|부|팀)[^。]{0,12}(?:지원조직|인원|\d+명)|준법감시부\(?\d+명', d.s)))
        checks += 1
        k = (r['corp_label'], r['fy'], NA, 'F3')
        if hs and k not in REVIEWED:
            review.append(f'반박 검토: F3 {k} 걸림 {hs[:5]}')

    # ── (g) 확인 CSV ──
    req = open(os.path.join(OUT, 'REQUEST15b.md'), encoding='utf-8').read()
    line_f2 = [ln.strip()[2:] for ln in req.split('\n') if ln.strip().startswith('* 함께 볼 것')]
    ck(len(line_f2) == 1, 'REQUEST15b 「함께 볼 것」 줄을 못 찾음')
    for i, r in enumerate(CHK, 2):
        key = f"확인:{i} {r['item_id']}"
        ck(r['item_text'] in [x for x in line_f2], f'{key}: item_text 가 REQUEST15b 줄 글과 다름')
        ck(r['result'] in ('원문 있음', '문서에 없음', '수집 실패'), f'{key}: result 값')
        if r['result'] == '원문 있음':
            ck(len(WS.sub(' ', r['source_excerpt'])) <= 300, f'{key}: source_excerpt 300자 넘음')
        else:
            ck(r['source_excerpt'] == NA or bool(src(r['rcept_no_or_url']) and src(r['rcept_no_or_url']).occ(r['source_excerpt'])),
               f'{key}: 문서에 없음 행 source_excerpt')
            ck('없음' in r['note'], f'{key}: 문서에 없음 — note 에 없는 범위 글 없음')
        m = re.match(r'(F2?_g2\.csv|F3_g2\.csv) (\S+) FY(\d{4}) (\S+)', r['where'])
        if ck(bool(m), f'{key}: where 꼴 모름'):
            tgt = data.get(m.group(1), [])
            ck(any(x['corp_label'] == m.group(2) and x['fy'] == m.group(3) and (x.get('committee') or x.get('body_name')) == m.group(4) for x in tgt),
               f'{key}: where 가 가리키는 행 없음 {r["where"][:60]}')
    for co in ('BNK금융지주',):
        ck(any(r['corp_label'] == co and r['fy'] == '2024' for r in CHK), f'확인: {co} FY2024 내부통제위원회 첫 개최 행 없음')

    # ── (h) 비밀·git ──
    keyv = os.environ.get('DART_API_KEY', '')
    outs = [os.path.join(OUT, '조각', x) for x in REQ] + [dlp, os.path.join(OUT, 'verify15b_F_g2.txt'),
                                                         os.path.join(ROOT, 'scripts', 'dart', 'ops15b_F_g2.py'), os.path.abspath(__file__)]
    outs += [p for p in glob.glob(os.path.join(OUT, '원문', 'F*', '*.md')) if any(os.path.basename(p).startswith(c + '__') for c in G2)]
    for p in outs:
        if not os.path.exists(p):
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        if p == os.path.abspath(__file__):
            t = t.replace("r'crtfc_key", '')
        ck(not ((keyv and len(keyv) > 8 and keyv in t) or re.search(r'crtfc_key=\w{8,}', t) or
                re.search(r'(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])', t)), f'{p}: 비밀 값 의심')
    for p in glob.glob(os.path.join(OUT, '원문', 'F*', '*')) + glob.glob(os.path.join(OUT, '조각', '*F*_g2*')):
        ck(not re.search(r'\.(pdf|zip|xml|png|jpe?g)$', p, re.I), f'산출 경로에 원본·그림 파일 {p}')
    try:
        ign = subprocess.run(['git', '-C', ROOT, 'check-ignore', 'dart_out/raw/x', 'dart_out/text/x', 'dart_out/ops15/조직도/x'],
                             capture_output=True, text=True).stdout.split('\n')
        ck(len([x for x in ign if x.strip()]) == 3, 'dart_out/raw·text·ops15/조직도 가 git 무시 폴더가 아님')
        tracked = subprocess.run(['git', '-C', ROOT, 'ls-files', '-co', '--exclude-standard', 'dart_out/ops15', 'scripts/dart'],
                                 capture_output=True, text=True).stdout.split('\n')
        bad = [x for x in tracked if re.search(r'\.(pdf|zip)$', x, re.I)]
        ck(not bad, f'git 추적(또는 무시 안 된) 경로에 PDF·zip {bad[:3]}')
    except Exception as ex:
        fails.append(f'git 점검 실패 {ex}')

    lines.append(f'대조·점검 {checks}건, 실패 {len(fails)}건, 반박 검토 남음 {len(review)}건, 숫자 대조 {len(numlog)}건')
    lines += ['FAIL ' + f for f in fails]
    lines += ['REVIEW ' + x for x in review]
    lines.append('── 숫자 대조(held_count·headcount 전부) ──')
    lines += numlog
    txt = '\n'.join(lines) + '\n'
    open(os.path.join(OUT, 'verify15b_F_g2.txt'), 'w', encoding='utf-8').write(txt)
    print('\n'.join(lines[:6 + len(fails) + len(review)])[:6000])
    return 1 if (fails or review) else 0


if __name__ == '__main__':
    sys.exit(main())
