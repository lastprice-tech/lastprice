"""15차 작업 C(지주 설립·전환 신고서의 인력·조직 키워드 문단) 조각 생성기 — dart_out/ops15/조각/C.csv 와 dart_out/ops15/원문/C/*.md 를 씀.

    python3 scripts/dart/ops15_C/build.py

입력(모두 저장소 상대 경로, 웹 요청·API 키 없음 — 받기는 fetch_docs.py·fetch_lists.py·fetch_nh.py 가 따로 함):
  scripts/dart/ops15_C/docs.py        사건별 대상 문서 목록(DOCS)
  scripts/dart/ops15_C/manifest.json  tomd.py 가 만든 문서별 OpenDART 상태·받은 시각·sha256·md 경로
  dart_out/text/ops15/신고서__<접수번호>.md       tomd.py 가 dart_out/raw/document/<접수번호>.zip 에서 만든 XML md(git 밖)
  dart_out/text/ops15/신고서__<접수번호>__본문PDF.md  pdf2md.py 가 handoff/원본_주요신고서본문.zip 의 본문 PDF 에서 만든 쪽 글(git 밖)
  dart_out/raw/list/<corp_code>_*.json(.meta.json) 공시목록 원장(git 밖 — 커밋한 dart_out/raw_part*.tar.gz 에서 풀거나 fetch_*.py 로 다시 받음)
  handoff/dart-benchmark-kit.zip 안 원문_지주전환_서술.csv  우리 2018 정정 8건 웹 회수본(이전 차수, 이번에 새로 받지 않음)
저장소 밖 파일을 다시 만드는 방법은 같은 폴더 README.md.
(15차 6파동: 저장소 밖 scratchpad C/scripts/build.py 를 이 폴더로 옮기고 경로를 저장소 상대로 바꿈 — 옮긴 뒤 다시 돌려 C.csv·원문 md 가 같음을 확인)
"""
import re, os, sys, json, csv, collections, hashlib, zipfile, io
csv.field_size_limit(10**9)
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from docs import DOCS
from extract import KW, kws, jj_excluded, units, RE_JJ, paras
def units2(md_text):
    sec_n, sec_t, tab, in_tab, ri = 0, '(머리말)', 0, False, 0
    for line in md_text.split('\n'):
        mm = re.match(r'^### \[절 (\d+)\] (.*)$', line)
        if mm: sec_n, sec_t = int(mm.group(1)), mm.group(2).strip(); continue
        mm = re.match(r'^\[표 (\d+)\]$', line)
        if mm: tab=int(mm.group(1)); in_tab=True; ri=0; continue
        if line=='[표 끝]': in_tab=False; continue
        if not line.strip(): continue
        if in_tab and line.startswith('| '):
            ri+=1
            if len(line) > 1500:
                for p_ in paras(line): yield sec_n, sec_t, tab, '표칸문단', p_, ri
            else: yield sec_n, sec_t, tab, '표행', line, ri
        else:
            for p_ in paras(line): yield sec_n, sec_t, (tab if in_tab else None), '문단', p_, 0
ROOT=os.path.abspath(os.path.join(HERE,'..','..','..'))
TXT=os.path.join(ROOT,'dart_out/text/ops15')
OUTCSV=os.path.join(ROOT,'dart_out/ops15/조각/C.csv')
OUTMD=os.path.join(ROOT,'dart_out/ops15/원문/C')
man={d['rcept']:dict(d,md=(os.path.join(ROOT,d['md']) if d.get('md') else '')) for d in json.load(open(os.path.join(HERE,'manifest.json'),encoding='utf-8'))}
KITZIP=os.path.join(ROOT,'handoff','dart-benchmark-kit.zip')
COLS=['corp_label','doc_kind','rcept_no','rcept_dt','section_title','keyword','source_text','page','note','doc_name','collected_at']
BASE={'하나2005':'20050729000361','KB2008':'20080430001516','BNK2011':'20101224000173','DGB2011':'20101230000131',
      '메리츠2010':'20101210000020','JB2013':'20130311000538','우리2018':'20181108000394','메리츠2022':'20221121000209',
      '메리츠2022b':'20230119000440'}
def base_of(ev,r):
    if ev=='한투2003':
        return '20021014000046' if r.startswith('2002') else '20030129000284'
    return BASE[ev]
EVNOTE={'하나2005':'사건: 하나은행 주식이전 → 하나금융지주 설립(2005)',
        'KB2008':'사건: 국민은행 주식이전 → KB금융지주 설립(2008)',
        'BNK2011':'사건: 부산은행 주식이전 → BS금융지주(현 BNK금융지주) 설립(2011.3)',
        'DGB2011':'사건: 대구은행 주식이전 → DGB금융지주(현 iM금융지주) 설립(2011.5)',
        '메리츠2010':'사건: 메리츠화재 인적분할 → 메리츠금융지주 설립(2011.3)',
        'JB2013':'사건: 전북은행 주식이전 → JB금융지주 설립(2013.7)',
        '우리2018':'사건: 우리은행 주식이전 → 우리금융지주 설립(2019.1)',
        '메리츠2022':'사건: 메리츠금융지주 포괄적 주식교환 — 완전자회사가 되는 회사 메리츠화재해상보험(2022.11 신고)',
        '메리츠2022b':'사건: 메리츠금융지주 포괄적 주식교환 — 완전자회사가 되는 회사 메리츠증권(2023.1 신고, 2022.11 발표 건의 2차)',
        '한투2003':'사건: 동원산업 인적분할 → 동원파이낸스 설립(2003.1.11) → 금융지주 본인가 후 동원금융지주(현 한국금융지주)'}
def norm(s):
    s=s.replace('&cr;','').replace('<br>','')
    return re.sub(r'[\s|｜]+','',s)
BND=re.compile(r'다\.|\.\s|&cr;|<br>|\s\|\s|\?\s')
def windows(text, maxlen=1200):
    """긴 단위는 키워드 든 문장(이웃한 것은 이어 붙임)만. 반환: [(start,end)] 원문 부분문자열 위치."""
    if len(text)<=maxlen: return [(0,len(text))], False
    b=sorted(set([0,len(text)]+[m.end() for m in BND.finditer(text)]))
    sents=[(b[i],b[i+1]) for i in range(len(b)-1) if b[i+1]>b[i]]
    hit=[kws(text[s:e]) != [] for s,e in sents]
    spans=[]; cur=None
    for (s,e),h in zip(sents,hit):
        if h:
            if cur and cur[1]==s: cur=(cur[0],e)
            else:
                if cur: spans.append(cur)
                cur=(s,e)
        else:
            if cur: spans.append(cur); cur=None
    if cur: spans.append(cur)
    out=[]
    for s,e in spans:
        if e-s<=1500: out.append((s,e)); continue
        # 문장 경계가 없는 긴 덩어리: 키워드마다 앞뒤 300자(공백 맞춤), 겹치면 합침
        sub=[]
        for k in KW:
            pat = RE_JJ if k=='전적' else re.compile(re.escape(k))
            for m in pat.finditer(text, s, e):
                a=max(s,m.start()-300); z=min(e,m.end()+300)
                while a>s and not text[a-1].isspace(): a-=1
                while z<e and not text[z].isspace(): z+=1
                sub.append((a,z))
        sub.sort()
        for a,z in sub:
            if out and out[-1][1]>=a and out[-1][0]>=s: out[-1]=(out[-1][0],max(out[-1][1],z))
            else: out.append((a,z))
    res=[]
    for s,e in out:
        t=text[s:e]
        ls=len(t)-len(t.lstrip()); rs=len(t)-len(t.rstrip())
        t2=re.sub(r'^(?:&cr;|<br>|\s|\|)+','',t); s2=s+(len(t)-len(t2)); t3=re.sub(r'(?:&cr;|<br>|\s|\|)+$','',t2)
        if t3: res.append((s2,s2+len(t3)))
    return res, True
REL_A=re.compile(r'기본사항|목적|배경|사업계획|이해관계|지주|설립|완전모회사|이사회결의|분할의|이전의|교환의|당사회사간')
REL_B=re.compile(r'조직|인력|임원 및 직원|직원|겸직')
def relevant(sec_t, text):
    return bool(REL_A.search(sec_t) or REL_B.search(sec_t) or ('지주' in text))
# ── PDF 쪽 대조 ───────────────────────────────────────────
class PdfPages:
    def __init__(self, path):
        s=open(path,encoding='utf-8').read()
        parts=re.split(r'^## p\.(\d+)\n', s, flags=re.M)
        self.buf=[]; self.idx=[]
        for i in range(1,len(parts),2):
            pn=int(parts[i]); t=norm(parts[i+1])
            self.idx.append((len(''.join(self.buf)) if False else sum(len(x) for x in self.buf), pn)); self.buf.append(t)
        self.all=''.join(self.buf)
        self.pos=0
    def page_at(self, off):
        p=self.idx[0][1]
        for o,pn in self.idx:
            if o<=off: p=pn
            else: break
        return p
    def find(self, text):
        n=norm(text)
        cands=[]
        if len(n)>=10: cands.append(n[:40])
        # 키워드 주변
        for k in KW:
            i=n.find(k)
            if i>=0: cands.append(n[max(0,i-15):i+len(k)+15]); break
        if len(n)>=50: cands.append(n[len(n)//2:len(n)//2+30])
        # (15차 검증 verify15_C 고침 F6) 위 조각이 모두 쪽 사이(끼어든 표 등)에 걸려 못 찾을 때 마지막으로 첫 20자
        if len(n)>=20: cands.append(n[:20])
        for c in cands:
            if len(c)<8: continue
            hits=[m.start() for m in re.finditer(re.escape(c), self.all)]
            if not hits: continue
            after=[h for h in hits if h>=self.pos]
            h=after[0] if after else hits[0]
            self.pos=h
            pg=self.page_at(h)
            # (15차 검증 verify15_C 고침 F5) 글이 쪽을 넘으면 시작 쪽~끝 쪽(전에는 찾은 조각이 있는 쪽 하나만 적어
            #   글이 앞 쪽에서 시작하는데 뒤 쪽 번호가 붙은 행이 있었음). 시작 = h 앞 가까운 곳의 글 첫 20자, 끝 = 그 뒤 글 끝 20자.
            ps=pe=pg
            if len(n)>=20:
                a=self.all.rfind(n[:20], max(0,h-len(n)-3000), h+20)
                if a>=0: ps=self.page_at(a)
                else: a=h
                z=self.all.find(n[-20:], max(a, a+int(0.8*len(n))-20), a+3*len(n)+3000)
                if z>=0: pe=self.page_at(z)
            if ps>pg: ps=pg
            if pe<pg: pe=pg
            return (str(ps) if ps==pe else f"{ps}~{pe}"), len(hits)
        return None, 0
PDFMD={r:os.path.join(TXT,f'신고서__{r}__본문PDF.md') for r in ['20050729000361','20080430001516','20101210000020','20181108000394']}
# ── 웹 회수본(우리 2018 정정 8건) ───────────────────────────
web=collections.defaultdict(dict)  # rcept -> sec_idx -> dict
with zipfile.ZipFile(KITZIP) as _kz, io.TextIOWrapper(_kz.open('원문_지주전환_서술.csv'),encoding='utf-8-sig') as f:   # open() 과 같은 줄바꿈 처리
    for row in csv.DictReader(f):
        if not row['status'].startswith('014'): continue
        d=web[row['rcept_no']].setdefault(int(row['section_index']),dict(title=row['section_title_raw'],chunks={},fetched_at=row['fetched_at'],raw_path=row['raw_path'],status=row['status']))
        d['chunks'][int(row['chunk_seq'])]=row['section_text']
# ── 본 문서 정규화 글(정정 대조) ───────────────────────────
_basecache={}
def base_norm(r):
    if r not in _basecache:
        p=man.get(r,{}).get('md')
        _basecache[r]=norm(open(p,encoding='utf-8').read()) if p else ''
    return _basecache[r]
rows=[]; stats=collections.OrderedDict(); md_sections=collections.defaultdict(list)
def kwstr(t): return '·'.join(kws(t))
for ev,label,filer,r,dt,nm in DOCS:
    m=man.get(r,{})
    st=m.get('status','')
    doc_name=f"{nm} — {filer} 제출 (DART 접수 {r})"
    base=base_of(ev,r)
    evn=EVNOTE[ev]
    cand=[]; jjx=0; src=''
    if m.get('md'):
        src='xml'; coll=m['fetched_at']
        body=open(m['md'],encoding='utf-8').read().split('\n',5)[5]
        for sec_n,sec_t,tab,kind,t,ri in units2(body):
            jjx+=jj_excluded(t)
            if not kws(t): continue
            spans,win=windows(t)
            for s,e in spans:
                tt=t[s:e]
                if not kws(tt): continue
                cand.append(dict(sec_n=sec_n,sec_t=sec_t,tab=tab,kind=kind,text=tt,win=win,unit_len=len(t),rel_text=t,sub=None,ri=ri))
    elif r in web:
        src='web'; coll=None
        btitles=[(int(mm.group(1)),mm.group(2).strip()) for mm in re.finditer(r'^### \[절 (\d+)\] (.*)$', open(man[base]['md'],encoding='utf-8').read(), re.M)]
        for si in sorted(web[r]):
            d=web[r][si]; t=''.join(d['chunks'][k] for k in sorted(d['chunks'])); coll=d['fetched_at']
            jjx+=jj_excluded(t)
            marks=[]; pos=0
            for bn_,bt in btitles:
                if len(bt)<4: continue
                i=t.find(bt,pos)
                if i>=0: marks.append((i,bn_,bt)); pos=i+len(bt)
            spans,win=windows(t)
            for s,e in spans:
                tt=t[s:e]
                if not kws(tt): continue
                sub=None
                for i,bn_,bt in marks:
                    if i<=s: sub=(bn_,bt)
                    else: break
                cand.append(dict(sec_n=si,sec_t=d['title'],tab=None,kind='웹문단',text=tt,win=win,unit_len=len(t),rel_text=tt,sub=sub))
    # 같은 절·표의 같은 글은 한 번
    seen=collections.Counter(); uniq=[]
    for c in cand:
        key=(c['sec_n'],c['tab'],c['text'])
        seen[key]+=1
        if seen[key]==1: uniq.append(c)
    for c in uniq: c['dup']=seen[(c['sec_n'],c['tab'],c['text'])]
    n_all=len(uniq); capped=False; dropped=0
    if n_all>60:
        capped=True
        keep=[c for c in uniq if relevant(c['sub'][1] if c['sub'] else c['sec_t'], c['rel_text'])]
        dropped=n_all-len(keep); uniq=keep
    stats[r]=dict(ev=ev,label=label,nm=nm,status=st,src=src,n_all=n_all,n_keep=len(uniq),dropped=dropped,jj=jjx)
    if not uniq:
        # (15차 검증 verify15_C 고침 F1·F2) 「문서에 없음」 행도 page 에 찾은 범위, 웹 회수본은 note 에 「이전 차수 웹 회수본 — 이번에 새로 받지 않음」
        if st and st!='000' and src!='web':
            # (15차 6파동 고침) 원문을 못 받은 문서는 「문서에 없음」이 아니라 「수집 실패」 — 내용을 보지 못했으므로
            note=(f"OpenDART document.xml {st}(파일 미제공) — 원문을 볼 수 없어 내용 확인 못함; '문서에 없음' 아님. "
                  f"「{m.get('fetched_at','')} 조회 — 파일이 존재하지 않습니다」. "
                  "DART 웹 뷰어·PDF 내려받기는 robots.txt Disallow 라 받지 않음. "+("[첨부정정] = 첨부서류만 고친 공시. " if '첨부정정' in nm else '')+evn)
            coll=m.get('fetched_at','')
            pg0=f"원문 미제공(OpenDART document.xml {st}) — 쪽 없음"
            rows.append(dict(corp_label=label,doc_kind=nm,rcept_no=r,rcept_dt=dt,section_title='',keyword='',source_text='수집 실패',page=pg0,note=note,doc_name=doc_name,collected_at=coll or ''))
            continue
        elif src=='web':
            ks=sorted(web[r]); d0=web[r][ks[0]]
            note=(f"이전 차수 웹 회수본 — 이번에 새로 받지 않음(OpenDART document.xml 014(파일 없음) → {d0['fetched_at']} DART 웹 뷰어에서 회수해 둔 본문 글, "
                  f"handoff/dart-benchmark-kit.zip 원문_지주전환_서술.csv, {d0['raw_path']}; 뷰어는 robots Disallow). "
                  f"찾은 범위: 이 문서 웹 회수본 전체(목차 {len(ks)}개: "+'·'.join(f"[{k}] 「{web[r][k]['title']}」" for k in ks)+f") · 검색어 {', '.join(KW)} — 키워드 든 글 없음. "+evn)
            pg0=f"웹 회수본 목차 [{ks[0]}]~[{ks[-1]}] 전체(찾은 범위 — 쪽 번호 없음)"
        else:
            note=f"찾은 범위: 이 문서 전체({'OpenDART XML md '+os.path.relpath(m['md'],ROOT) if m.get('md') else '웹 회수본'}) · 검색어 {', '.join(KW)} — 키워드 든 문단·표 줄 없음. "+evn
            pg0="XML 전체(찾은 범위 — 쪽 없음)"
        rows.append(dict(corp_label=label,doc_kind=nm,rcept_no=r,rcept_dt=dt,section_title='',keyword='',source_text='문서에 없음',page=pg0,note=note,doc_name=doc_name,collected_at=coll or ''))
        continue
    pdf=PdfPages(PDFMD[r]) if r in PDFMD else None
    bn=base_norm(base) if r!=base else ''
    for c in uniq:
        notes=[]
        if src=='xml':
            pg=f"XML [절 {c['sec_n']}] 「{c['sec_t']}」"+(f" [표 {c['tab']}]" if c['tab'] else '')
            if c['kind']=='표칸문단': pg+=' (표 칸 안 문단)'
            if pdf:
                p,nh=pdf.find(c['text'])
                if p: pg=f"p.{p}(본문 PDF) · "+pg; 
                if p and nh>1: notes.append(f"PDF 쪽은 같은 글이 {nh}곳에 있어 문서 순서로 고름(판단)")
                if not p: notes.append('본문 PDF 에서 같은 글을 찾지 못해 쪽 번호 없음')
        else:
            pg=f"웹 회수본 목차 [{c['sec_n']}] 「{c['sec_t']}」"+(f" 안 「{c['sub'][1]}」 부분" if c['sub'] else '')+"(쪽 번호 없음)"
            # (15차 검증 verify15_C 고침 F1) note 맨 앞에 「이전 차수 웹 회수본 — 이번에 새로 받지 않음」
            notes.append(f"이전 차수 웹 회수본 — 이번에 새로 받지 않음: OpenDART document.xml 014(파일 없음) → {web[r][c['sec_n']]['fetched_at']} DART 웹 뷰어에서 회수해 둔 본문 글(handoff/dart-benchmark-kit.zip 원문_지주전환_서술.csv, {web[r][c['sec_n']]['raw_path']}). 뷰어는 robots Disallow 라 이번에 다시 받지 않음. 표 칸은 회수본에 없음")
            if c['sub']: notes.append(f"웹 회수본 목차 단위가 굵어 이 사건 첫 신고서 {base} XML 의 절 제목([절 {c['sub'][0]}])이 나오는 위치로 나눠 절을 붙임(판단)")
        if c.get('ri')==1 and c['kind']=='표행':
            notes.append('표 첫 줄(머리) — 표의 나머지 줄은 키워드가 없어 행으로 뽑지 않음, 원문 md 의 같은 절에 표 전체')
        if c['win']:
            notes.append(f"긴 문단({c['unit_len']:,}자) 중 키워드 든 문장만 옮김(판단)")
        if c['dup']>1:
            notes.append(f"같은 절·표에 같은 글 {c['dup']}번 — 1행으로")
        if r!=base:
            if norm(c['text']) and norm(c['text']) in bn:
                notes.append(f"이 사건 첫 신고서 {base} 에도 같은 글(공백·줄바꿈 무시)")
            else:
                notes.append(f"이 사건 첫 신고서 {base} XML 에서 같은 글을 찾지 못함(공백·줄바꿈 무시) — 정정·추가분이거나 표기 차이")
        if capped:
            notes.append(f"이 문서 키워드 행 {n_all}개(60 초과) → 지주회사 설립·운영·조직·인력·겸직 절(또는 「지주」가 든 문단)만 남김, {dropped}개 뺌(판단)")
        notes.append(evn)
        rows.append(dict(corp_label=label,doc_kind=nm,rcept_no=r,rcept_dt=dt,section_title=(c['sub'][1] if c.get('sub') else c['sec_t']),keyword=kwstr(c['text']),
                         source_text=c['text'],page=pg,note=' / '.join(notes),doc_name=doc_name,collected_at=coll))
        md_sections[r].append((c['sec_n'],c['sec_t']))
# 사건 단위 「문서에 없음」 행
# (15차 검증 verify15_C 고침 F2·F3·F4) 사건 단위 「문서에 없음」 3행: page 에 찾은 범위, rcept_no 칸에 조회한 공시목록 API 주소(인증키 칸 뺌),
#   신한 2001 은 법인 구분을 바로잡음 — 00137571 = 신한은행(구)(2001년 「주식교환ㆍ이전결정」 있음), 00149293 = 조흥은행(현 신한은행, company.json 설립 1897·종목코드 000010)
def list_url(cc):
    import glob
    fs=sorted(glob.glob(os.path.join(ROOT,'dart_out/raw/list',cc+'_*_p*.json.meta.json')))
    p=json.load(open(fs[0])).get('params',{}) if fs else {}
    return f"https://opendart.fss.or.kr/api/list.json?corp_code={cc}&bgn_de={p.get('bgn_de','')}&end_de={p.get('end_de','')}&last_reprt_at={p.get('last_reprt_at','N')}"
SRCNOTE=' 출처 칸(rcept_no)에는 접수번호 대신 조회한 공시목록 OpenDART API 주소(인증키 칸 뺌)를 적음 — C 열에 URL 칸이 없어서(판단).'
extra=[
 dict(corp_label='신한금융지주',doc_kind='(유가증권신고서·주식교환ㆍ이전신고서·투자설명서 — 공시목록에 없음)',rcept_no=' · '.join(list_url(c) for c in ['00137571','00149293','00382199']),rcept_dt='',section_title='',keyword='',source_text='문서에 없음',
      page='공시목록 2001-01~2001-12 전체(찾은 범위 — 쪽 없음; 넓혀 2000-07~2002-06 도 봄)',
      note=('찾은 범위: dart_out/raw/list/00137571_19990101_20260911_p*.json(신한은행(구) — 2001년 임원ㆍ주요주주 소유상황보고서 보고자에 라응찬·이인호·최영휘), '
            'dart_out/raw/list/00149293_19990101_20260911_p*.json(조흥은행 — company.json 설립일 1897-02-19·종목코드 000010, 20040412001121 주식교환ㆍ이전신고서 표지에 「주식회사 조흥은행」; '
            'DART 이름은 둘 다 「신한은행」), dart_out/raw/list/00382199_19990101_20260831_p*.json(신한지주) 의 2001년 공시 목록 전체. '
            '신한은행(구) 00137571 의 2001년 주식이전 관련 공시는 「주식교환ㆍ이전결정」(20010628000184, 2001-06-28) 하나뿐이고 신고서·투자설명서는 없음(결정 공시는 신고서·투자설명서가 아니라 C 대상 밖). '
            '신한지주는 2001-09-04 「등록법인신청서[모집설립이외]」(20010904000098)가 첫 공시이고 2001년 신고서는 무보증사채 증권신고서뿐(설립·전환 서류 아님). '
            '넓혀 본 2000-07~2002-06 에도 세 법인의 주식이전 신고서·투자설명서 없음(2002-04·05 신한지주 「주식교환ㆍ이전결정」 2건은 결정 공시). '
            '법인 구분(00137571=신한은행(구), 00149293=조흥은행)은 공시 보고자 이름·company.json·신고서 표지로 함(판단). 이전 판(15차 1회)은 00149293 을 신한은행(구)로 적고 결정 공시도 없다고 적었음 — 바로잡음.'
            +SRCNOTE+' 사건: 신한은행 등 주식이전 → 신한금융지주 설립(2001.9)'),
      doc_name='OpenDART list.json(공시목록) — 신한은행(구) 00137571·조흥은행(현 신한은행) 00149293·신한지주 00382199',collected_at=''),
 dict(corp_label='하나금융지주',doc_kind='투자설명서',rcept_no=list_url('00130897'),rcept_dt='',section_title='',keyword='',source_text='문서에 없음',
      page='공시목록 2005-06~2005-12 전체(찾은 범위 — 쪽 없음; 넓혀 2004-12~2006-06 도 봄)',
      note=('찾은 범위: dart_out/raw/list/00130897_*.json(하나은행(구)) 2005-06~2005-12 공시 목록 — 주식이전 관련 투자설명서 없음(신고서 5건과 결정 공시만). '
            '같은 이름 「하나은행」 00156017·00158909 의 같은 기간 목록은 투자설명서 0건, 넓혀 본 2004-12~2006-06 에도 주식이전 관련 투자설명서 없음. 하나금융지주 00547583 의 2005년 목록은 원장(2020~)에 없어 못 봄.'
            +SRCNOTE+' 사건: 하나은행 주식이전 → 하나금융지주 설립(2005)'),
      doc_name='OpenDART list.json(공시목록) — 하나은행(구) 00130897',collected_at=''),
 dict(corp_label='KB금융지주',doc_kind='투자설명서',rcept_no=list_url('00386937')+' · '+list_url('00688996'),rcept_dt='',section_title='',keyword='',source_text='문서에 없음',
      page='공시목록 2008-03~2008-10 전체(찾은 범위 — 쪽 없음; 넓혀 2007-09~2009-04 도 봄)',
      note=('찾은 범위: dart_out/raw/list/00386937_*.json(국민은행) 2008-03~2008-10 공시 목록 — 주식이전 관련 투자설명서 없음(투자설명서는 일괄신고-사채뿐). '
            'dart_out/raw/list/00688996_*.json(KB금융) 같은 기간은 투자설명서 0건, 넓혀 본 2007-09~2009-04 에도 주식이전 투자설명서 없음.'
            +SRCNOTE+' 사건: 국민은행 주식이전 → KB금융지주 설립(2008)'),
      doc_name='OpenDART list.json(공시목록) — 국민은행 00386937·KB금융 00688996',collected_at=''),
]
# 목록 원장 받은 시각 채우기
def list_fetched(cc):
    import glob
    fs=sorted(glob.glob(os.path.join(ROOT,'dart_out/raw/list',cc+'_*.meta.json')))
    return json.load(open(fs[0])).get('fetched_at','') if fs else ''
extra[1]['collected_at']=list_fetched('00130897'); extra[2]['collected_at']=list_fetched('00386937'); extra[0]['collected_at']=list_fetched('00137571')
# (15차 6파동 더함) NH농협금융지주 설립(2012-03-02, 농협중앙회 신용사업 분리) — fetch_nh.py 가 받은 공시목록(nh_list.json)에서 설립·전환 신고서를 찾음
def nh_row():
    nh=json.load(open(os.path.join(HERE,'nh_list.json'),encoding='utf-8'))
    KEY=re.compile(nh['keyword_re'])
    q={(x['corp_code'],x['pblntf_ty']):x for x in nh['queries'] if x['page']==1}
    corps=[]
    for cc in dict.fromkeys(x['corp_code'] for x in nh['queries']):
        nm0=next(x['corp'] for x in nh['queries'] if x['corp_code']==cc)
        cnt=', '.join(f"{ty or '전체'} {q[(cc,ty)]['total_count'] or 0}건" for ty in ('C','B','I','E',''))
        corps.append(f"{nm0} {cc}({cnt})")
    allitems=[it for x in nh['queries'] if x['pblntf_ty']=='' for it in x['items']]
    hits=sorted({(it['rcept_dt'],it['rcept_no'],it['report_nm']) for it in allitems if KEY.search(it['report_nm'])})
    ev=[h for h in hits if re.search(r'주식교환|주식이전|교환ㆍ이전|분할|합병|설립|등록법인신청서',h[2]) or ('증권신고서' in h[2] and '채무증권' not in h[2])]
    first=min((it['rcept_dt'],it['report_nm']) for it in allitems if it['corp_name']=='농협금융지주')
    assert not ev, ev   # 설립·전환 신고서가 나오면 다른 사건처럼 문서를 받아 키워드 문단을 뽑아야 함
    b,e=nh['range']
    q0=q[('00908021','')]
    return dict(corp_label='NH농협금융지주',doc_kind='(증권신고서·투자설명서·주식이전·분할 신고서 — 공시목록에 없음)',
        rcept_no=' · '.join(f"https://opendart.fss.or.kr/api/list.json?corp_code={cc}&bgn_de={b}&end_de={e}" for cc in dict.fromkeys(x['corp_code'] for x in nh['queries'])),
        rcept_dt='',section_title='',keyword='',source_text='문서에 없음',
        page=f"공시목록 {b[:4]}-{b[4:6]}~{e[:4]}-{e[4:6]} 전체(찾은 범위 — 쪽 없음)",
        note=(f"찾은 범위: OpenDART list.json {b[:4]}-{b[4:6]}-{b[6:]}~{e[:4]}-{e[4:6]}-{e[6:]} 공시목록 — "+'; '.join(corps)+
              " (공시유형 C 발행공시·B 주요사항보고·I 거래소공시·E 기타공시·전체; corp_code 는 dart_out/raw/corpCode/corpCode.zip 에서 이름으로 찾음). "
              f"보고서명 검색어 「{nh['keyword_re'].replace('|','」「')}」 — 걸린 것은 농협금융지주 2012-10~12 채무증권 공시 "
              +', '.join(f"{h[2]}({h[1]})" for h in hits)+
              " 뿐: 「증권신고서(채무증권)」과 그 정정·발행조건확정, 그 바로 뒤 「투자설명서」(앞 신고서가 채무증권이라 설립·전환 사건 서류가 아님 — 판단). "
              f"지주 설립·전환(주식이전·분할·주식교환) 증권신고서·투자설명서 없음. 이 기간 농협금융지주 첫 공시는 {first[0][:4]}-{first[0][4:6]}-{first[0][6:]} 「{first[1]}」. "
              "받은 글: dart_out/raw/list/nh15/<corp_code>_<유형>_p001.json, 요약 scripts/dart/ops15_C/nh_list.json."
              +SRCNOTE+' 사건: 농협중앙회 신용사업 분리 → NH농협금융지주 설립(2012.3.2)'),
        doc_name='OpenDART list.json(공시목록) — 농협금융지주 00908021·농협은행 00908757·농업협동조합중앙회 00332565·00291675',
        collected_at=q0['fetched_at'])
rows=extra[:1]+rows+extra[1:]+[nh_row()]
os.makedirs(os.path.dirname(OUTCSV),exist_ok=True)
with open(OUTCSV,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=COLS); w.writeheader(); w.writerows(rows)
json.dump(dict(stats=stats,md_sections={k:sorted(set(v)) for k,v in md_sections.items()}),open(os.path.join(HERE,'build_stats.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('rows',len(rows))
for r,s in stats.items(): print(r,s)
# ── 원문 md(행이 나온 절 전체) ─────────────────────────────
import shutil
if os.path.isdir(OUTMD):
    for fn in os.listdir(OUTMD):
        if fn.endswith('.md'): os.remove(os.path.join(OUTMD,fn))
os.makedirs(OUTMD,exist_ok=True)
def safe(s): return re.sub(r'[\[\]()/\\:*?"<>| ]+','_',s).strip('_')
rowcount=collections.Counter((r['rcept_no'],r['section_title']) for r in rows)
written=[]; total=0; seen_sec={}; n_ptr=0
for ev,label,filer,r,dt,nm in DOCS:
    secs=sorted(set(md_sections.get(r,[])))
    if not secs: continue
    m=man.get(r,{})
    fn=f"{safe(label)}__{dt}__{safe(nm)}__{r}.md"
    out=[f"# {nm} — {filer} ({label} 설립·전환 관련) · 접수 {r} ({dt})\n"]
    if m.get('md'):
        out.append(f"- 출처: OpenDART document.xml `dart_out/raw/document/{r}.zip` (sha256 {m.get('sha','')}) · 받은 시각 {m.get('fetched_at','')} · md `{os.path.relpath(m['md'],ROOT)}`\n")
        out.append(f"- 뷰어 링크(사람용): https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r}\n")
        if r in PDFMD: out.append(f"- 본문 PDF 쪽 텍스트: `{os.path.relpath(PDFMD[r],ROOT)}`(「## p.N」) — CSV page 칸에 PDF 쪽을 붙임\n")
        out.append("- 아래는 작업 C 행(source_text)이 나온 절 전체를 XML md 그대로 옮긴 것(「&cr;」는 DART XML 줄바꿈 표시 그대로). 쪽 번호 없음 — 위치는 [절 n]·[표 m].\n\n")
        lines=open(m['md'],encoding='utf-8').read().split('\n')
        heads=[(i,int(mm.group(1)),mm.group(2)) for i,l in enumerate(lines) for mm in [re.match(r'^### \[절 (\d+)\] (.*)$',l)] if mm]
        want={n for n,_ in secs}
        for j,(i,n,t) in enumerate(heads):
            if n not in want: continue
            end=heads[j+1][0] if j+1<len(heads) else len(lines)
            body_='\n'.join(lines[i+1:end]).strip('\n')
            h_=hashlib.sha256(body_.encode()).hexdigest()
            hk=hashlib.sha256(re.sub(r'^\[표 \d+\]$','[표 #]',body_,flags=re.M).encode()).hexdigest()
            out.append(f"## [절 {n}] {t}\n\n- 출처: 접수 {r} · XML [절 {n}] 「{t}」 · 절 글 sha256 {h_}\n\n")
            if hk in seen_sec and len(body_)>2000:
                out.append(f"(이 절 글은 `{seen_sec[hk][0]}` 의 「{seen_sec[hk][1]}」 절과 글자 하나까지 같음(「[표 n]」 표지의 순번만 다를 수 있음) — 크기를 줄이려고 글은 그 파일에만 둠(판단). {len(body_):,}자)\n\n"); n_ptr+=1
            else:
                seen_sec.setdefault(hk,(fn,f"[절 {n}] {t}"))
                out.append(body_+'\n\n')
        if 0 in want:
            first=heads[0][0] if heads else len(lines)
            out.append("## (머리말 — 첫 절 제목 앞)\n\n"+'\n'.join(l for l in lines[6:first]).strip('\n')+'\n\n')
    else:
        d0=web[r][secs[0][0]]
        out.append(f"- 출처(이전 차수 웹 회수본 — 이번에 새로 받지 않음): OpenDART document.xml {m.get('status','')}(파일 없음) → {d0['fetched_at']} DART 웹 뷰어에서 회수해 둔 본문 글(handoff/dart-benchmark-kit.zip 안 원문_지주전환_서술.csv, {d0['raw_path']}). 이번 15차에는 새로 받지 않음(DART 웹 뷰어는 robots.txt Disallow).\n")
        out.append("- 회수본은 목차 단위 글이고 줄바꿈·표 칸이 없음. 아래는 그 목차 절 글 전체(32,767자 조각을 chunk_seq 순으로 이어 붙임 — 글자는 그대로).\n\n")
        for n in sorted({n for n,_ in secs}):
            d=web[r][n]; t=''.join(d['chunks'][k] for k in sorted(d['chunks']))
            h_=hashlib.sha256(t.encode()).hexdigest()
            out.append(f"## 웹 회수본 목차 [{n}] {d['title']}\n\n- 출처: 접수 {r} · 회수 {d['fetched_at']} · 절 글 sha256 {h_}\n\n")
            if h_ in seen_sec and len(t)>2000:
                out.append(f"(이 절 글은 `{seen_sec[h_][0]}` 의 「{seen_sec[h_][1]}」 절과 글자 하나까지 같음(sha256 일치) — 글은 그 파일에만 둠(판단). {len(t):,}자)\n\n"); n_ptr+=1
            else:
                seen_sec.setdefault(h_,(fn,f"웹 회수본 목차 [{n}] {d['title']}"))
                out.append(t+'\n\n')
    s=''.join(out)
    open(os.path.join(OUTMD,fn),'w',encoding='utf-8',newline='\n').write(s)
    written.append((fn,len(s))); total+=len(s.encode())
print('md files',len(written),'bytes',total,'pointers',n_ptr)
