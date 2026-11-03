"""15차 확장 작업 F·F-2·F-3 g1 조각 검증(인자 없음, exit 0 = 통과 / 1 = 실패). 결과 dart_out/ops15/verify15b_F_g1.txt.

생성기(ops15b_F_g1.py)와 따로 원문을 다시 읽어 대조한다(COMMON15b 원문 대조 규칙):
- source_text 와 모든 *_text 칸(chair·members·cadence·agenda·agenda_list·duty·concurrent_or_dispatched)과 확인 CSV source_excerpt:
  「문서에 없음」이 아니면 공백·줄바꿈을 지운 칸 글이 공백·줄바꿈을 지운 출처 글 안에 이어서 그대로 있어야 함.
  OpenDART XML md 출처는 md 표지 「|」「<br>」도 양쪽에서 지움. 출처 글에서 변환 표지(「### [절 n]」 머리표, 「[표 n]」「[표 끝]」 줄,
  연차보고서 md 의 「## p.N」·「## p.N (글자 없음)」 줄)는 지우고 봄.
- 출처 = 행의 rcept_no_or_url(또는 rcept_no) 문서 + note 에 적힌 rcept_no·URL 문서(칸이 다른 곳에서 왔을 때 note 에 위치를 적음).
- 모든 행: 출처·doc_name·page·collected_at 이 비지 않음, 「문서에 없음」 칸이 있으면 note 가 비지 않음.
- 분류 칸 재계산: function_kw(작업 F 키워드 중 body_name·source_text 에 든 낱말), subsidiary_related(agenda_list_text 에 자회사·그룹·계열사).
- 비밀: 산출 파일에 DART_API_KEY 값·crtfc_key 가 없음.
"""
import csv, os, re, sys, glob

csv.field_size_limit(10**9)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'dart_out', 'ops15')
NA = '문서에 없음'
KW_F = ['협의회', '협의체', '회의체', '위원회', '그룹', '리스크', '내부통제', '준법', '감사', '소비자보호', 'ESG', '디지털', 'AI', 'IT',
        '정보보호', '브랜드', '시너지', '개최', '분기', '매월']

_docs = {}


def strip(t, xml=False):
    if xml:
        t = t.replace('<br>', '').replace('|', '')
    return re.sub(r'\s+', '', t)


def br_text(rcept):
    for x in csv.DictReader(open(os.path.join(OUT, '사업보고서_원문.csv'), encoding='utf-8-sig')):
        if x['rcept_no'] == rcept and x['text_path']:
            lines = open(os.path.join(ROOT, x['text_path']), encoding='utf-8').read().split('\n')
            out, started = [], False
            for ln in lines:
                if ln.startswith('### [절 '):
                    started = True
                    ln = re.sub(r'^### \[절 \d+\] ?', '', ln)
                elif not started:
                    continue
                elif re.fullmatch(r'\s*\[표 (\d+|끝)\]\s*', ln):
                    continue
                out.append(ln)
            return strip('\n'.join(out), xml=True)
    return None


def ar_text(url):
    for g in ('g1', 'g2'):
        p = os.path.join(OUT, f'연차보고서15_목록_{g}.csv')
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding='utf-8-sig')):
            if r['파일_url'].split(' (')[0] == url:
                md = os.path.join(ROOT, 'dart_out', 'text', 'ops15', f"연차보고서__{r['회사']}__{r['공시연도']}__{r['공시유형']}.md")
                if os.path.exists(md):
                    lines = open(md, encoding='utf-8').read().split('\n')
                    out, started = [], False
                    for ln in lines:
                        if re.fullmatch(r'## p\.\d+(\s.*)?', ln):
                            started = True
                            continue
                        if started:
                            out.append(ln)
                    return strip('\n'.join(out))
    for r in csv.DictReader(open(os.path.join(ROOT, 'handoff', '연차보고서_파일목록.csv'), encoding='utf-8-sig')):
        if r['url'] == url and '지배구조' in r['파일명']:
            fname = r['파일명']
            rows = [k for k in csv.DictReader(open(os.path.join(OUT, 'kit56', '연차보고서_섹션.csv'), encoding='utf-8-sig'))
                    if k['파일명'] == fname]
            rows.sort(key=lambda k: (int(k['섹션순번']), int(k['chunk_seq'])))
            return strip(''.join(k['본문'] for k in rows))
    return None


def doc(ref):
    if ref not in _docs:
        if re.fullmatch(r'\d{14}', ref):
            _docs[ref] = br_text(ref)
        else:
            _docs[ref] = ar_text(ref)
    return _docs[ref]


def refs_in(note):
    out = re.findall(r'(?<!\d)(\d{14})(?!\d)', note or '')
    out += re.findall(r'(https?://[^\s」』)\]]+)', note or '')
    return out


def contained(val, refs):
    if not val or val == NA:
        return True
    v_plain, v_xml = strip(val), strip(val, xml=True)
    for ref in refs:
        t = doc(ref)
        if t is None:
            continue
        if re.fullmatch(r'\d{14}', ref):
            if v_xml in t:
                return True
        elif v_plain in t:
            return True
    return False


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


TEXT_COLS = {
    'F_g1.csv': ['source_text', 'chair_text', 'members_text', 'cadence_text', 'agenda_text'],
    'F2_g1.csv': ['agenda_list_text', 'members_text', 'established'],
    'F3_g1.csv': ['duty_text', 'concurrent_or_dispatched', 'unit_name', 'function'],
    '확인_F_g1.csv': ['source_excerpt'],
}
REQ = {
    'F_g1.csv': ['corp_label', 'fy', 'body_name', 'function_kw', 'chair_text', 'members_text', 'cadence_text', 'held_count', 'agenda_text',
                 'doc_kind', 'section_title', 'source_text', 'rcept_no_or_url', 'page', 'note', 'doc_name', 'collected_at'],
    'F2_g1.csv': ['corp_label', 'fy', 'committee', 'established', 'held_count', 'agenda_list_text', 'subsidiary_related', 'members_text',
                  'rcept_no', 'page', 'note', 'doc_name', 'collected_at'],
    'F3_g1.csv': ['corp_label', 'fy', 'function', 'unit_name', 'headcount', 'concurrent_or_dispatched', 'duty_text', 'rcept_no_or_url',
                  'page', 'note', 'doc_name', 'collected_at'],
    '확인_F_g1.csv': ['item_id', 'item_text', 'corp_label', 'fy', 'result', 'where', 'rcept_no_or_url', 'page', 'source_excerpt', 'note'],
}


def main():
    lines, fails = [], []
    checks = 0
    for fn, cols in TEXT_COLS.items():
        path = os.path.join(OUT, '조각', fn)
        if not os.path.exists(path):
            fails.append(f'{fn}: 파일 없음')
            continue
        rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
        hdr = list(rows[0].keys()) if rows else open(path, encoding='utf-8-sig').readline().strip().split(',')
        if hdr != REQ[fn]:
            fails.append(f'{fn}: 열 다름 {hdr}')
        na_rows = 0
        for i, r in enumerate(rows, 2):
            ref = r.get('rcept_no_or_url') or r.get('rcept_no') or ''
            key = f"{fn}:{i} {r.get('corp_label')} FY{r.get('fy')} {r.get('body_name') or r.get('committee') or r.get('unit_name') or r.get('item_id')}"
            # 빈 칸
            need = ['rcept_no_or_url' if 'rcept_no_or_url' in r else 'rcept_no', 'page']
            if fn != '확인_F_g1.csv':
                need += ['doc_name', 'collected_at']
            for c in need:
                checks += 1
                if not (r.get(c) or '').strip():
                    if not (fn == '확인_F_g1.csv' and r.get('result') != '원문 있음'):
                        fails.append(f'{key}: {c} 비어 있음')
            if any((r.get(c) or '') == NA for c in r):
                na_rows += 1
                checks += 1
                if not (r.get('note') or '').strip():
                    fails.append(f'{key}: 「문서에 없음」 칸이 있는데 note 비어 있음')
            refs = ([ref] if ref else []) + refs_in(r.get('note'))
            for c in cols:
                v = r.get(c, '')
                if c in ('unit_name', 'function', 'established') and v in ('', NA):
                    continue
                checks += 1
                if not contained(v, refs):
                    fails.append(f'{key}: {c} 원문 대조 실패 「{v[:60]}…」')
                if v and v != NA and ('…' in v) and '…' not in ''.join(doc(x) or '' for x in refs):
                    fails.append(f'{key}: {c} 에 원문에 없는 「…」')
            if fn == 'F_g1.csv':
                checks += 1
                exp = fkw(r['body_name'], r['source_text'] if r['source_text'] != NA else '')
                if r['function_kw'] != exp:
                    fails.append(f'{key}: function_kw 「{r["function_kw"]}」 ≠ 재계산 「{exp}」')
            if fn == 'F2_g1.csv':
                checks += 1
                a = r['agenda_list_text']
                exp = NA if a == NA else ('Y' if re.search('자회사|그룹|계열사', re.sub(r'\s+', '', a)) else 'N')
                if r['subsidiary_related'] != exp:
                    fails.append(f'{key}: subsidiary_related 「{r["subsidiary_related"]}」 ≠ 재계산 「{exp}」')
        lines.append(f'{fn}: 행 {len(rows)}, 「문서에 없음」 칸이 있는 행 {na_rows}')
    # 비밀
    key = os.environ.get('DART_API_KEY', '')
    outs = glob.glob(os.path.join(OUT, '조각', '*F*_g1.csv')) + glob.glob(os.path.join(OUT, '원문', 'F*', '*.md')) + \
        [os.path.join(OUT, '문서목록15b_F_g1.csv'), os.path.join(ROOT, 'scripts', 'dart', 'ops15b_F_g1.py')]
    for p in outs:
        if not os.path.exists(p):
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        checks += 1
        if (key and len(key) > 8 and key in t) or 'crtfc_key=' in t:
            fails.append(f'{p}: 비밀 값 의심')
    lines.append(f'대조·점검 {checks}건, 실패 {len(fails)}건')
    lines += ['FAIL ' + f for f in fails]
    txt = '\n'.join(lines) + '\n'
    open(os.path.join(OUT, 'verify15b_F_g1.txt'), 'w', encoding='utf-8').write(txt)
    print(txt[:4000])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
