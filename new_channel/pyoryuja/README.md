# 표류자 — 신규 픽션 채널 제작 키트 (EP.1 준비 완료본)

기존 역사공학 채널(영어, 완전 사실 기반)과 **분리된** 신규 한국어 픽션 채널의 제작 폴더다. 영상은 **Grok Imagine**으로 만든다. EP.1은 영상 생성 버튼을 누르기 직전까지 모두 준비돼 있다: 캐릭터·소품 레퍼런스 정의, 장면표, 대본, 영상 프롬프트, 실행기.

## 무엇이 들어 있나

| 파일 | 내용 |
|---|---|
| `PROCESS_TO_SCRIPT.md` | 기획 → 시즌 → 바이블 → 엔진 사양 → 캐릭터 → 대본 → 장면표 → 오버레이 → 리뷰까지 실제로 밟은 절차와 다음 회차 체크리스트 |
| `bible/series_bible.yaml` | 세계관·캐릭터·스타일·금지 목록 (제작판) |
| `bible/ledger.json` | 회차 종료 상태 원장(인벤토리·위치·결말) — 연속성 린트 기준 |
| `characters/model_sheet.svg` · `_preview.jpg` | 디자인 기준 시트(비율·색·식별점) |
| `characters/CHARACTERS.md` | 레퍼런스 생성 순서·선택 기준·정체성 유지 장치 |
| `characters/refs.json` | 레퍼런스 이미지 작업 11개(주인공 4·고양이 3·소품 3·로케이션 1)의 프롬프트 |
| `ep01/shots.json` | **원본 데이터**: 내레이션 34줄 + 샷 24개(연결 방식·편집 프롬프트·영상 프롬프트·끝 상태·효과음) |
| `ep01/shotlist.md` | 장면표 + 샷별 최종 프롬프트(API용 태그본, 앱용 평문본) — `render` 생성물 |
| `ep01/script.md` · `narration_tts.txt` · `subtitles.srt` | 대본(슬롯·타임코드·음절 속도), TTS 입력본, 자막 — `render` 생성물 |
| `ep01/overlays.json` · `diagram_freshwater_lens.svg` | 후반 오버레이(태그·상태 자막·인벤토리·도면·경고·지도·엔드카드), 원리 도면 |
| `ep01/factcheck.md` · `metadata.md` | 사실 확인 시트(출처), 업로드 메타데이터·고정 댓글·교차 게시 |
| `tools/grok_chain.py` | 실행기: 린트 → 문서 생성 → 레퍼런스 → 시작 프레임 → 영상 → 끝 프레임 → 다음 샷 → 조립 |
| `review/PROCEDURE.md` · `review/personas/*.md` | 영상 생성 전 외부 제작자 페르소나 심사 절차(「신비한 건축사전」·「문명」) — 실행은 `.claude/workflows/pyoryuja-persona-review.js` |
| `review/ep01/persona_review.md` | EP.1 심사 결과와 반영 내역 |

## 영상 연결 방식 — "앞 영상의 마지막 프레임에서 다음 행동을 잇는다"

```
S01 ──끝 프레임──▶ S02(C) ──끝──▶ [편집: 카메라만 바꿈] ──▶ S03(A) ──끝──▶ [편집] ──▶ S04(A) ──끝──▶ S05(C) …
                                                          T(시간 점프) = 같은 장소, 물때·빛만 바꾼 편집
```

- **C 이어가기:** 앞 클립의 아웃 포인트 프레임을 그대로 다음 영상의 시작 프레임으로 고정한다(`image`). 다음 영상은 "Continuing from…"으로 행동만 덧붙인다. 조립할 때 앞 클립은 아웃 프레임 직전에서 끝나고 다음 클립의 첫 프레임(=그 아웃 프레임)이 바로 이어져 이음매가 보이지 않는다.
- **끝 상태 도달 시각:** 영상 프롬프트마다 "이 끝 상태에 약 N초에 도달하고 클립 끝까지 거의 움직이지 않는다"는 문장이 자동으로 붙는다. N은 아웃 포인트 0.3초 전이다. 그래서 다음 샷이 출발하는 프레임이 버려지는 꼬리가 아니라 끝 상태에 놓인다.
- **A 앵글 컷 / T 시간 점프:** 앞 끝 프레임과 캐릭터 레퍼런스를 함께 넣어 이미지 편집으로 새 시작 프레임을 만든다. 바꾸는 것은 카메라 각도, 또는 시간·물때·빛뿐이다. 소품 위치·빛·옷 상태는 앞 프레임에서 물려받는다. 컷은 있지만 끊긴 느낌은 없다.
- **왜 전부 C로 잇지 않나:**
  - 같은 프레임을 계속 다시 생성하면 색과 형태가 조금씩 흘러간다(드리프트).
  - 100초 원테이크는 쇼츠에서 지루하다.
  - 그래서 C는 연속 1번까지만 쓰고(린트 상한 3), A·T로 레퍼런스에 다시 맞춘다. EP.1은 26샷 중 C 5 · A 11 · T 8 · K 1 · F 1이다(페르소나 심사 후 재편).
- **아웃 포인트 = 다음 샷의 출발점:** 클립을 승인할 때 실제로 쓸 마지막 프레임을 정한다. 실행기는 그 주변 ±3프레임 중 흔들림이 적은 프레임으로 맞춘 뒤 PNG로 뽑아 다음 샷에 넘긴다. 클립 끝(+1초 여유분)이 아니라 **편집에 실제로 쓰는 지점**에서 이어야 연결이 맞는다.
- **매 영상에 레퍼런스 동봉:** `reference_images`에 주인공·고양이·소품 확정 이미지를 넣고, 프롬프트 끝에 정체성 문장을 붙인다. 시작 프레임이 `<IMAGE_0>`, 레퍼런스가 `<IMAGE_1…>`이다.

## EP.1 제작 순서 (처음부터 끝까지)

로컬(~/video_studio)로 옮겨도 그대로 동작한다. Python 3.10+와 ffmpeg만 있으면 된다.

```bash
cd new_channel/pyoryuja
export XAI_API_KEY=...                       # xAI 콘솔에서 발급

# 0) 점검 — 린트와 문서 재생성
python3 tools/grok_chain.py ep01 check
python3 tools/grok_chain.py ep01 render
#    그다음 페르소나 심사(review/PROCEDURE.md) → A 항목 반영 → check/render 재실행. 영상 생성 전에 한 번만.

# 1) 캐릭터·소품·로케이션 레퍼런스 (CHARACTERS.md 3절 기준으로 고르기)
python3 tools/grok_chain.py ep01 refs --only P --live    # → characters/refs/_candidates/P_cand1~4.png
python3 tools/grok_chain.py ep01 pick-ref P 3
#    C, L01 → P_side, P_back, P_kneel, C_walk, C_crouch → PLANK, BAMBOO → FLASK 순서로 반복
python3 tools/grok_chain.py ep01 sheet                   # characters/refs/P_sheet.png, C_sheet.png

# 2) 내레이션 먼저 녹음 (줄 ID별 파일) → 타이밍 실측 반영
#    narration_tts.txt 의 각 줄을 build/tts/N01.wav … N34.wav 로 저장
python3 tools/grok_chain.py ep01 render                  # 장면 길이·생성 초·자막·오버레이 시간이 실측으로 갱신됨

# 3) 샷 체인 — next 를 반복한다. 사람 게이트 2개: 시작 프레임 승인, 클립 승인
python3 tools/grok_chain.py ep01 next --live             # S01: L01+P+C 편집 → 시작 프레임 후보 2장
python3 tools/grok_chain.py ep01 approve S01 start --pick 1
python3 tools/grok_chain.py ep01 next --live             # S01 영상 생성(6초) → build/clips/S01_t1.mp4
python3 tools/grok_chain.py ep01 approve S01 clip         # 계획 아웃 포인트 사용. 직접 지정: --out 4.6
python3 tools/grok_chain.py ep01 next --live             # S02(C): S01 끝 프레임으로 바로 영상 생성
#    … S24까지. 마음에 안 들면: retake S05 clip --live / retake S06 start --live
python3 tools/grok_chain.py ep01 status

# 4) 무음 픽처 락 (1080x1920, 24fps)
python3 tools/grok_chain.py ep01 assemble                # → ep01/build/EP1_picture.mp4

# 5) 후반: 기존 파이프라인으로 TTS·효과음(shots.json sfx)·오버레이(build/overlays_resolved.json)·자막 합성, -14 LUFS
```

키 없이 흐름을 점검하려면 `--simulate`를 쓴다. ffmpeg 더미 이미지·영상으로 refs → next/approve → assemble 전 과정이 돈다. 이 저장소에서 26샷 전체 리허설을 통과했다(조립 109.71초, 계획 대비 최대 0.02초, 조립본과 실제 타임라인 2633프레임 일치. 수정 전 24샷 판에서 아웃 PNG 23/23 프레임 일치 확인).

**재작업 안전장치**
- `retake S10 clip`처럼 어느 샷을 다시 만들면, 그 끝 프레임에서 (직·간접으로) 출발한 하류 샷의 승인이 자동으로 취소된다. `next`가 하류를 다시 진행한다. 시작 프레임이 그대로인 샷은 기존 클립을 재사용한다.
- 클립은 자신을 만든 시작 프레임의 해시를 기억한다. 이전 시작 프레임으로 만든 take는 승인할 수 없다.
- `assemble`은 다음 두 경우 조립을 거부한다. 우회는 `--force`다.
  - 출발 프레임이 바뀐 샷이 있다.
  - 샷 시작 시각이 계획(내레이션 기준)에서 0.1초 넘게 어긋난다.
- 실제 타이밍은 `build/timeline_actual.json`에 남는다.

## 사람이 보는 곳 (샷당 1~2분)

**시작 프레임 승인(A·T·K):**
- [ ] 머리 얼굴 요소 0
- [ ] 조끼(버클 3개, 왼쪽 호루라기), 맨발
- [ ] 고양이 식별점 3개와 목걸이
- [ ] 앞 샷과 같은 장소·빛·소품 위치
- [ ] 사람·현대 물체·글자 없음

**클립 승인:**
- [ ] 위 항목이 모든 프레임에서 유지된다
- [ ] 손가락 5개, 손이 물체를 관통하지 않는다
- [ ] 물·파도 물리가 자연스럽다
- [ ] 고양이 위기 연출이 없다
- [ ] 아웃 포인트 프레임이 흔들리지 않는다(다음 샷의 출발점)

**히어로 샷 S13(대나무 홈 내기)**: 재생성 예산을 먼저 쓴다.

## 비용·시간 (EP.1)

| 항목 | 계산 | 금액 |
|---|---|---|
| 영상 | 생성 142초 × $0.08/s(grok-imagine-video-1.5 공식가) × 재생성 2배 | 약 $22.7 |
| 시작 프레임 편집 | 20샷 × 후보 2장 × $0.04 × 2배 | 약 $3.2 |
| 레퍼런스(시리즈 1회) | 약 40장 × $0.04 | 약 $1.6 |
| **EP.1 합계** | | **약 $27.5** (2화부터 약 $26) |

- **단가 정정:** 이전 리서치의 "$0.14/s"는 재판매처 단가였다. xAI 공식 가격표는 $0.08/s다(2026-10 확인).
- **레퍼런스 입력 과금:** 레퍼런스 입력 이미지 요금은 공식 표에 없다. 첫 호출의 usage로 확인한다.
- **사람 시간:** 첫 화 약 3~4시간. 레퍼런스 선택 1시간, 26샷 승인 각 2~5분, 고증 10분. 이후 회차는 편당 약 1.5시간이 목표다.

## 아직 실측하지 못한 것 (첫 실행 때 확인)

1. **실제 API 호출은 이 환경에서 해 보지 못했다(키 없음).** 요청 형식은 docs.x.ai 2026-10 문서 기준이다.
   - 영상: `image` + `reference_images` + `generate_audio` + `duration`
   - 편집: `images[]` + `aspect_ratio` + `resolution`
   - 첫 호출에서 400이 나면 실행기가 응답 본문을 그대로 출력한다.
2. **`image`(첫 프레임 고정)와 레퍼런스를 함께 쓰면 해상도 상한이 720p다.** 업로드용으로 1080x1920 업스케일(lanczos)을 조립 단계에서 한다.
3. **Grok 출력 fps는 클립마다 ffprobe로 읽어 프레임 단위로 자른다.** 조립 출력은 24fps로 통일한다.
4. **얼굴 없는 머리를 유지하는 비율은 측정값이 없다.** S01~S06에서 탈락률을 기록한다. 30%를 넘으면 CHARACTERS.md 4절 대응을 적용한다. 이 기록이 파일럿 W0 캘리브레이션을 겸한다.
5. **사실 확인 시트의 ⚠ 5건(F1·F3·F8·F10·F12)은 공개 전에 출처를 보강해야 한다.**

## 다음 회차 만들기

1. `ep01/`을 `ep02/`로 복사하고 `shots.json`의 narration·shots를 새로 쓴다. 슬롯 12개 순서는 유지한다.
2. `bible/ledger.json`에 EP.2 종료 상태를 추가한다. `check`가 HAVE 인벤토리, 획득 카운터, 연속 결말 유형을 검사한다.
3. 회차 사이도 끊기지 않게 EP.2 첫 샷을 EP.1 마지막 프레임에서 **그대로** 잇는다(페르소나 심사 B7).
   - `ep01/build/frames/S23_out.png`(해 질 녘, 쇠못에 손이 닿기 직전)를 `characters/refs/EP1_END.png`로 복사한다.
   - `refs.json`에 `{"id": "EP1_END", "role": "EP.1 마지막 프레임", "aspect_ratio": "9:16", "prompt": ""}`를 추가한다.
   - EP.2 S01을 `"link": "C", "base": "EP1_END"`로 둔다(`from` 없음). 실행기가 그 프레임을 편집 없이 첫 프레임으로 고정한다. 행동 예: 손이 못을 쥐고 널빤지를 뒤집어 아랫면의 거친 각인(F1)을 마지막 주황빛에 보인다.
   - 밤·아침으로 넘기는 시간 점프는 S02(T 링크)에서 한다.
4. 페르소나 심사의 다음 회차 규칙 15건(`review/ep01/persona_review.md` 4절)을 EP.2 대본·오버레이에 적용한다. 렌더러 타입 추가가 필요한 항목(상태 바·trace·companion_stat·ref_chip)은 먼저 렌더러에 넣는다.
