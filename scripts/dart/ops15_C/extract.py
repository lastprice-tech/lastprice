import re, os, sys, json, csv
KW = ['인력','임직원','조직','겸직','파견','전적','채용']
# 전적: 轉籍 뜻만. 앞이 한글 음절이거나 뒤가 「으로·인·이」면 다른 낱말(금전적·사전적·발전적·전적으로 …) — (판단)
RE_JJ = re.compile(r'(?<![가-힣])전적(?!으로|인|이)')
def kws(t):
    out=[]
    for k in KW:
        if k=='전적':
            if RE_JJ.search(t): out.append(k)
        elif k in t: out.append(k)
    return out
def jj_excluded(t):
    return len(re.findall('전적',t)) - len(RE_JJ.findall(t))
SPLIT = re.compile(r'(?:\s*&cr;\s*){2,}|(?:<br>\s*){2,}')
def paras(s):
    parts=[]; pos=0
    for m in SPLIT.finditer(s):
        parts.append((pos, s[pos:m.start()])); pos=m.end()
    parts.append((pos, s[pos:]))
    out=[]
    for st,p in parts:
        q=p.strip()
        q2=re.sub(r'^(?:&cr;|\s)+|(?:&cr;|\s)+$','',q)
        if q2: out.append(q2)
    return out
def units(md_text):
    """yield (sec_n, sec_title, table_n or None, kind, text)"""
    sec_n, sec_t, tab, in_tab = 0, '(머리말)', 0, False
    for line in md_text.split('\n'):
        m = re.match(r'^### \[절 (\d+)\] (.*)$', line)
        if m:
            sec_n, sec_t = int(m.group(1)), m.group(2).strip(); continue
        m = re.match(r'^\[표 (\d+)\]$', line)
        if m: tab=int(m.group(1)); in_tab=True; continue
        if line=='[표 끝]': in_tab=False; continue
        if not line.strip(): continue
        if in_tab and line.startswith('| '):
            if len(line) > 1500:
                for p in paras(line):
                    yield sec_n, sec_t, tab, '표칸문단', p
            else:
                yield sec_n, sec_t, tab, '표행', line
        else:
            for p in paras(line):
                yield sec_n, sec_t, (tab if in_tab else None), '문단', p
def extract(md_path):
    s=open(md_path,encoding='utf-8').read()
    # 머리(출처 줄) 건너뜀: 첫 '### [절' 또는 본문 시작 전 4줄
    body = s.split('\n',5)[5] if s.startswith('# ') else s
    rows=[]; jjx=0
    for sec_n,sec_t,tab,kind,t in units(body):
        jjx += jj_excluded(t)
        k=kws(t)
        if k: rows.append(dict(sec_n=sec_n,sec_t=sec_t,tab=tab,kind=kind,text=t,kw='·'.join(k)))
    return rows, jjx
if __name__=='__main__':
    man=json.load(open(sys.argv[1]))
    out=[]
    for d in man:
        if not d.get('md'): continue
        rows,jjx=extract(d['md'])
        for r in rows: r['rcept']=d['rcept']; out.append(r)
        print(d['event'], d['rcept'], 'rows', len(rows), '전적제외', jjx, 'maxlen', max([len(r['text']) for r in rows] or [0]))
    with open(sys.argv[2],'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['rcept','sec_n','sec_t','tab','kind','kw','text']); w.writeheader(); w.writerows(out)
