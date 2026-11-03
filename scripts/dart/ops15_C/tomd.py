"""dart_out/raw/document/<접수번호>.zip(OpenDART document.xml) → dart_out/text/ops15/신고서__<접수번호>.md 와 이 폴더 manifest.json.

    python3 scripts/dart/ops15_C/tomd.py

XML→md 는 scripts/dart/ops15_prep.py 의 xml_to_md() 를 그대로 씀. 받은 시각·상태·sha256 은 zip 옆 .meta.json(DartClient 가 씀)에서.
(15차 6파동: scratchpad C/scripts/tomd.py 를 옮김 — 경로만 저장소 상대로, manifest 의 md 는 저장소 상대 경로)
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'dart'))
sys.path.insert(0, HERE)
from ops15_prep import xml_to_md
from docs import DOCS
TXT = os.path.join(ROOT, 'dart_out/text/ops15')
os.makedirs(TXT, exist_ok=True)
man = []
for ev, label, filer, r, dt, nm in DOCS:
    zp = os.path.join(ROOT, 'dart_out/raw/document', r + '.zip')
    mp = zp + '.meta.json'
    m = json.load(open(mp)) if os.path.exists(mp) else {}
    st = m.get('api_status', '')
    rec = dict(event=ev, label=label, rcept=r, status=st, fetched_at=m.get('fetched_at', ''), sha=m.get('sha256', ''), md='')
    if st == '000':
        b = open(zp, 'rb').read()
        md, member, enc = xml_to_md(b, r)
        p = os.path.join(TXT, f'신고서__{r}.md')
        head = (f"# {nm} — {filer} ({label} 설립·전환 관련)\n\n- 접수번호 {r} · 접수일 {dt} · "
                f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r}\n- 원문: OpenDART document.xml `dart_out/raw/document/{r}.zip` "
                f"(sha256 {m.get('sha256','')}) · 멤버 {member} · 받은 시각 {m.get('fetched_at','')}\n"
                "- 쪽 번호 없음(XML). 위치는 「[절 n]」(제목 순번)·「[표 n]」(표 순번). 글자는 XML 그대로(태그만 걷어냄).\n\n")
        open(p, 'w', encoding='utf-8', newline='\n').write(head + md)
        rec['md'] = os.path.relpath(p, ROOT); rec['member'] = member; rec['enc'] = enc; rec['chars'] = len(md)
    man.append(rec)
    print(ev, r, st, rec.get('member', ''), rec.get('enc', ''), rec.get('chars', ''))
with open(os.path.join(HERE, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(man, f, ensure_ascii=False, indent=1)
