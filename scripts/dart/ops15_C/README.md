# 15차 작업 C — 지주 설립·전환 신고서의 인력·조직 문단 (생성기)

산출: `dart_out/ops15/조각/C.csv`(utf-8-sig, 작업 C 열 + doc_name·collected_at), `dart_out/ops15/원문/C/*.md`(행이 나온 절 전체).
검증: `python3 scripts/dart/verify15_C.py` → `dart_out/ops15/verify15_C.txt`(exit 0/1).
15차 6파동(2026-11-03)에 저장소 밖 scratchpad(`C/scripts/*.py` + `manifest.json` + `kit/`)에서 이 폴더로 옮김. 옮긴 뒤 고치기 전에 다시 돌려
C.csv(md5 ad02161c…)·원문/C md 46개·build_stats.json 이 옮기기 전과 바이트까지 같음을 확인함.

## 파일과 돌리는 차례

| 파일 | 하는 일 | 웹·키 |
|---|---|---|
| `docs.py` | 사건 10개의 대상 문서 50건(사건·회사·제출인·접수번호·접수일·보고서명) | — |
| `fetch_lists.py` | 사건 기간 공시목록(list.json) 받기 → `dart_out/raw/list/` | OpenDART(키) |
| `fetch_nh.py` | NH농협금융지주 2011-07~2012-12 공시목록(유형 C·B·I·E·전체) → `dart_out/raw/list/nh15/`, 요약 `nh_list.json` | OpenDART(키) |
| `fetch_docs.py` | document.xml 받기 → `dart_out/raw/document/<접수번호>.zip(.meta.json)` (`--missing` = 없는 것만) | OpenDART(키) |
| `tomd.py` | zip → `dart_out/text/ops15/신고서__<접수번호>.md`(ops15_prep.xml_to_md) + 이 폴더 `manifest.json` | — |
| `pdf2md.py` | `handoff/원본_주요신고서본문.zip` 안 본문 PDF → `신고서__<접수번호>__본문PDF.md`(「## p.N」) | — |
| `extract.py` | 키워드(인력·임직원·조직·겸직·파견·전적(轉籍 꼴)·채용)·문단 나누기 규칙(build.py 가 import) | — |
| `build.py` | C.csv·원문/C md·`build_stats.json` 쓰기 | — |

DART_API_KEY 는 환경변수로만 둠(`scripts/dart/client.py` 가 읽고 로그·파일에서 가림). 어떤 파일에도 쓰지 않음.

## 저장소 밖(git 밖) 입력을 다시 만드는 법

`dart_out/raw/`·`dart_out/text/` 는 .gitignore 라 컨테이너가 다시 만들어지면 사라짐.

1. 커밋한 원문 묶음 풀기: `cd dart_out && for f in raw_part*.tar.gz; do tar xzf $f; done` → `dart_out/raw/`(공시목록 원장 `raw/list/`, document zip 대부분).
2. 묶음에 없는 document 25건(15차에 작업 C 가 새로 받은 것 — BNK·DGB·JB·한국투자 사건 전부와 메리츠·우리 일부):
   `python3 scripts/dart/ops15_C/fetch_docs.py --missing`. 014(파일 미제공) 10건은 다시 받아도 014 — BNK 20101229000364·JB 20130320000306 은 C 에 「수집 실패」,
   우리 2018 정정 8건은 아래 kit 의 이전 차수 웹 회수본을 씀.
3. 사건 기간 목록(묶음에 없는 것): `python3 scripts/dart/ops15_C/fetch_lists.py`, NH: `python3 scripts/dart/ops15_C/fetch_nh.py`.
4. `python3 scripts/dart/ops15_C/tomd.py` (md 40건과 manifest.json — 커밋한 manifest.json 과 같게 나와야 함; 받은 시각은 .meta.json 값).
5. 본문 PDF 4건(PyMuPDF 파이썬, 내려받은 파일이라 `-I`):
   `<venv>/bin/python -I scripts/dart/ops15_C/pdf2md.py handoff/원본_주요신고서본문.zip 20050729000361 하나은행 dart_out/text/ops15/신고서__20050729000361__본문PDF.md`
   (같은 꼴로 20080430001516 국민은행 · 20101210000020 메리츠화재 · 20181108000394 우리은행).
6. `python3 scripts/dart/ops15_C/build.py` → `python3 scripts/dart/verify15_C.py`.

저장소 안 입력: `handoff/dart-benchmark-kit.zip`(안의 `원문_지주전환_서술.csv` = 우리 2018 정정 8건 웹 회수본 — 2026-09 에 DART 웹 뷰어에서 회수한 것,
이번에 새로 받지 않음; 뷰어는 robots.txt Disallow), `handoff/원본_주요신고서본문.zip`, `scripts/dart/ops15_prep.py`, 이 폴더의 `manifest.json`·`nh_list.json`.
옮기지 않은 것: 원본 PDF·zip(handoff 에 있음), scratchpad 의 중간 파일(all_list.tsv·cand.csv·review1.txt 등 문서 고르기 기록), 비밀값.

## 주의

- DartClient 의 list 캐시 파일 이름에는 `pblntf_ty` 가 없어, 같은 법인·기간을 유형만 바꿔 조회하면 첫 응답을 캐시로 돌려줌 → `fetch_nh.py` 는 `refresh=True`
  로 받고 유형별 원본을 `dart_out/raw/list/nh15/<corp_code>_<유형>_p001.json` 에 따로 둠(유형 지정 없는 조회를 마지막에 해 기본 캐시 = 전체 목록).
- 사건 단위 「문서에 없음」 행(신한 2001·하나 2005 투자설명서·KB 2008 투자설명서·NH 2012)은 C 열에 URL 칸이 없어 rcept_no 칸에 조회한 list.json 주소(인증키 칸 뺌)를 적음(판단).
