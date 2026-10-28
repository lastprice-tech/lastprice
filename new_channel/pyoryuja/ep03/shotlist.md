# 「표류자 EP.3」 바닷물을 굽다 — 장면표 · 영상 프롬프트

타이밍 출처: 음절 속도 계획치(TTS 녹음 후 render 재실행 시 실측으로 갱신). 이 파일은 `render`가 생성한다(원본: shots.json).

연결 규칙: 모든 샷은 앞 샷에서 **실제로 쓰는 마지막 프레임**에서 출발한다. C는 그 프레임을 그대로 `image`로 고정하고, A·T는 그 프레임을 이미지 편집해 카메라·시간만 바꾼 뒤 고정한다.

| 샷 | 슬롯 | 화면 | 길이 | 생성 | 연결 | 출발 | 장면 |
|---|---|---|---|---|---|---|---|
| S01 | STATE | 0:00.00–0:04.20 | 4.20s | 6s | C 이어가기(앞 끝 프레임 그대로) | EP2_END | EP.2 끝 프레임에서 그대로 — 홈 옆에 조약돌 하나(태우지 않을 표시) |
| S02 | NEED | 0:04.20–0:07.95 | 3.75s | 5s | T 시간 점프(앞 끝 프레임 편집) | S01 | 다음 날 아침 · 꺼진 불자리 옆, 민물로 뒷목을 식힘 |
| S03 | NEED | 0:07.95–0:12.85 | 4.90s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S02 | 높은 와이드 — 갯벌 없이 바위뿐인 만, 걸어가는 둘 |
| S04 | HAVE | 0:12.85–0:17.70 | 4.85s | 6s | T 시간 점프(앞 끝 프레임 편집) | S03 | 젖은 쑥 솜을 볕에 펴 말림 · 가진 것을 나란히 (인벤토리) |
| S05 | GATHER | 0:17.70–0:20.80 | 3.10s | 5s | T 시간 점프(앞 끝 프레임 편집) | S04 | 밀물이 닿지 않는 높은 너럭바위의 오목들 — 고양이가 먼저 걸어 듦 |
| S06 | GATHER | 0:20.80–0:25.35 | 4.55s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S05 | 흰 테에 코를 대는 고양이(고양이 역할 컷) → 스스로 물러남 |
| S07 | GATHER | 0:25.35–0:29.05 | 3.70s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S06 | 관계 비트 — 흰 앞발을 민물로 헹구고, 남은 물은 고양이 몫 |
| S08 | FAIL | 0:29.05–0:32.80 | 3.75s | 5s | T 시간 점프(앞 끝 프레임 편집) | S07 | 솥 대신 전복 껍데기로 바닷물을 뜸 — 구멍에서 물줄기 |
| S09 | FAIL | 0:32.80–0:35.20 | 2.40s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S08 | 매크로 — 구멍마다 물이 샘 |
| S10 | FAIL | 0:35.20–0:37.75 | 2.55s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S09 | 빈 껍데기를 내려놓고 멈춤 |
| S11 | PRINCIPLE | 0:37.75–0:43.44 | 5.70s | 7s | T 시간 점프(앞 끝 프레임 편집) | S10 +S05 | 측면 정렬 구도 · 넓은 오목에 바닷물을 부음 (도면 — 수면선 y≈720) |
| S12 | PRINCIPLE | 0:43.44–0:49.60 | 6.15s | 8s | C 이어가기(앞 끝 프레임 그대로) | S11 | 실시간 이어짐 · 수면 위 열기, 고양이가 엎드림 (도면) |
| S13 | PRINCIPLE | 0:49.60–0:53.86 | 4.26s | 6s | T 시간 점프(앞 끝 프레임 편집) | S12 | 조건 줄(실사) — 오목 대여섯 개를 바닷물로 채움 |
| S14 | PRINCIPLE | 0:53.86–0:57.07 | 3.21s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S13 | 귀에 남는 문장 — 볕이 끓이는 오목, 맨발이 지나감 |
| S15 | BUILD | 0:57.07–1:00.82 | 3.75s | 5s | T 시간 점프(앞 끝 프레임 편집) | S14 | (재료 인서트) 잔해 판자에 못 박힌 구리판 |
| S16 | BUILD | 1:00.82–1:03.97 | 3.15s | 5s | T 시간 점프(앞 끝 프레임 편집) | S15 | 떼어 낸 구리판의 마지막 귀를 접어 얕은 솥 완성 |
| S17 | BUILD | 1:03.97–1:07.52 | 3.55s | 5s | T 시간 점프(앞 끝 프레임 편집) | S16 +S13 | 한낮 — 줄어든 오목의 물을 가운데 깊은 오목으로 모음(단계 농축) |
| S18 | BUILD | 1:07.52–1:10.67 | 3.15s | 5s | T 시간 점프(앞 끝 프레임 편집) | S17 +S02 | 오후 — 어제 불자리에 마른 받침돌 셋 · 마른 판자 땔감 · 바람막이 |
| S19 | BUILD | 1:10.67–1:14.27 | 3.60s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S18 | 볕에 마른 쑥 솜에 다시 불씨 — 쇠못과 흰 돌 |
| S20 | TEST | 1:14.27–1:17.92 | 3.65s | 5s | T 시간 점프(앞 끝 프레임 편집) | S19 +S18 | 늦은 오후 — 돌 셋 위 구리판 솥이 끓고, 줄면 또 부음 · 고양이는 멀리 |
| S21 | TEST | 1:17.92–1:20.32 | 2.40s | 4s | T 시간 점프(앞 끝 프레임 편집) | S20 | 해 질 녘 — 솥 가장자리 흰 테, 얇은 결정 막 (결정은 여기서부터) |
| S22 | TEST | 1:20.32–1:23.27 | 2.95s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S21 +S20 | 소금죽이 튐 — 긴 막대로 불을 빼 끝까지 졸이지 않음 |
| S23 | TEST | 1:23.27–1:27.02 | 3.75s | 5s | T 시간 점프(앞 끝 프레임 편집) | S22 | 실패한 전복 껍데기가 체로 — 젖은 소금을 담자 구멍에서 간수가 떨어짐 |
| S24 ★ | TEST | 1:27.02–1:30.47 | 3.45s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S23 | 손끝에서 사각거리는 회색 소금 (답 · 히어로) |
| S25 | COST | 1:30.47–1:33.42 | 2.95s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S24 +S20 | 와이드 — 큰 재 더미, 바닥난 땔감, 그을린 솥 · 고양이가 와서 옆에 앉음 |
| S26 | COST | 1:33.42–1:37.27 | 3.85s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S25 | 대비 — 전경의 작은 소금, 뒤의 큰 재 더미 |
| S27 | UNLOCK | 1:37.27–1:39.92 | 2.65s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S26 | 소금 껍데기를 손끝으로 톡톡 두 번 (획득 카드) |
| S28 | NEXT | 1:39.92–1:42.87 | 2.95s | 4s | T 시간 점프(앞 끝 프레임 편집) | S27 +S25 | 해 진 직후 · 꺼진 재, 땔감 없음 · 섬 안쪽으로 고개 |
| S29 | NEXT | 1:42.87–1:47.17 | 4.30s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S28 | 어깨 너머 — 섬 안쪽 들판 너머 연기 한 줄 (EP3_END) |
| S30 | TAG | 1:47.17–1:49.67 | 2.50s | — | F 정지 프레임 | S29 | 정지 + 엔드카드 |

★ = 히어로 샷(재생성 예산 우선 배정)

---

## S01 · STATE · EP.2 끝 프레임에서 그대로 — 홈 옆에 조약돌 하나(태우지 않을 표시) · 0:00.00–0:04.20 (4.20s)

**장면** EP.2 마지막 프레임(비 갠 해 질 녘, 빗물 고인 널빤지 아랫면 홈 클로즈업)에서 편집 없이 이어서. 프레임 오른쪽 가장자리에서 손이 들어와 연한 조약돌 하나를 홈 옆 젖은 나뭇결 위에 얹고(홈을 가리지 않음) 물러난다. 시리즈 표시 '조약돌' — 이 널빤지는 땔감으로 쓰지 않는다는 표시. 손만 보인다. (QC: 조약돌이 홈을 덮거나 홈이 글자·기호로 읽히면 탈락)

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 EP2_END
- 빛: dusk_after_rain · 레퍼런스: P, PLANK_UNDER
- 생성 6s → 사용 구간 0.000–4.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N01` 불은 꺼졌다. 홈 난 널빤지는 태우지 않는다.
- 오버레이: `ref_chip` (overlays.json)
- 효과음: 저녁 파도(작게), 조약돌이 젖은 나무에 닿는 '톡'
- 끝 상태(다음 샷의 출발점): 널빤지 아랫면 클로즈업: 빗물 고인 홈(F1)과 빈 못 구멍 옆 젖은 나뭇결 위에 연한 조약돌 1개(홈은 가리지 않음). 손은 프레임 밖. 비 갠 해 질 녘 마지막 주황빛.

**① 시작 프레임** = EP2_END(이전 회차) 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 PLANK_UNDER

```text
Continuing from <IMAGE_0>, a slender matte light-grey porcelain hand reaches in from the right edge of the frame and sets one small pale pebble down on the wet oak beside the water-filled grooves and the small empty square hole where the nail was pulled out, leaving the grooves uncovered, then withdraws out of frame. Static close-up. It ends with the pale pebble resting beside the grooves and the empty nail hole, the water in them still catching the last orange light. Pace the action so that this ending is reached at about 3.9 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_2>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, a slender matte light-grey porcelain hand reaches in from the right edge of the frame and sets one small pale pebble down on the wet oak beside the water-filled grooves and the small empty square hole where the nail was pulled out, leaving the grooves uncovered, then withdraws out of frame. Static close-up. It ends with the pale pebble resting beside the grooves and the empty nail hole, the water in them still catching the last orange light. Pace the action so that this ending is reached at about 3.9 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S02 · NEED · 다음 날 아침 · 꺼진 불자리 옆, 민물로 뒷목을 식힘 · 0:04.20–0:07.95 (3.75s)

**장면** 시간 점프(밤을 건너뛰어 다음 날 아침, 맑음, 볕이 벌써 따갑다). 측면에서 조금 뒤쪽 미디엄(머리는 옆·뒤로만). 어제 꺼진 불자리(마른 회색 재, 검은 잔가지 끝) 옆 바위에 앉은 주인공이 물통 마개를 빼고 왼손바닥에 민물을 조금 따라 젖은 손바닥을 뒷목에 댄다(더위 신호 — 마시는 장면 없음). 고양이는 옆 바위 그늘에 웅크림. 옷은 밤새 마르다 만 상태.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S01
- 빛: clear_morning · 레퍼런스: P, C, FLASK, L01
- 생성 5s → 사용 구간 0.000–3.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N02` 땀으로 빠져나간 소금은 물로 채울 수 없다.
- 오버레이: `time_card_morning` (overlays.json)
- 효과음: 아침 파도, 물 따르는 소리(작게), 먼 바닷새
- 끝 상태(다음 샷의 출발점): 맑은 아침. 주인공: 꺼진 불자리(마른 재) 옆 바위에 앉아 마개 끼운 물통을 쥠, 고개를 바다 쪽으로. 고양이: 옆 바위 그늘에 웅크림. 옷 거의 마름.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S01 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK · 5) 레퍼런스 L01

```text
Change the time to the next morning, clear and already hot, with the sun low over the sea, and the camera to a medium view from the side and slightly behind the figure from <IMAGE_1> on the same cove, the shoreline shaped like the one in <IMAGE_4>: it sits on a rock beside the bare hollow where yesterday's fire went out, now dry grey ash and black twig ends, holding the bamboo flask from <IMAGE_3> in its right hand with the dark oak plug pulled out; the ginger cat from <IMAGE_2> lies curled in the shade of the rock beside it. Keep the outfit as in <IMAGE_0>, the clothes almost dry, and all designs exactly as in <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK · <IMAGE_4> 레퍼런스 L01

```text
<IMAGE_0> is the first frame. The figure tips the flask and pours a little water into its cupped left palm, then presses the wet palm to the back of its neck, its blank head bowed forward; the cat stays curled in the shade. Static camera. It ends with the figure pushing the plug back into the flask, its head turned toward the bright sea. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Take only the coastline, rocks and distant hills from <IMAGE_4>. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure tips the flask and pours a little water into its cupped left palm, then presses the wet palm to the back of its neck, its blank head bowed forward; the cat stays curled in the shade. Static camera. It ends with the figure pushing the plug back into the flask, its head turned toward the bright sea. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S03 · NEED · 높은 와이드 — 갯벌 없이 바위뿐인 만, 걸어가는 둘 · 0:07.95–0:12.85 (4.90s)

**장면** 앵글 컷(높은 와이드 부감). 갯벌도 모래톱도 없이 검은 현무암 바위와 너럭바위만 바다까지 이어진 만(옛 기록 줄 — '소금 만들 땅이 없는 해안'을 화면으로). 작은 주인공이 물통을 들고 바위 위를 걸어가고 고양이가 몇 걸음 뒤따른다. 사람·염전·배·건물은 없다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S02
- 빛: clear_morning · 레퍼런스: P, C, L01
- 생성 6s → 사용 구간 0.000–4.900s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N03` 옛 기록엔 이 섬에서 소금 굽기는 품이 백배 든다고 했다.
- 효과음: 아침 파도, 바람, 먼 바닷새
- 끝 상태(다음 샷의 출발점): 높은 와이드: 바위뿐인 해안(갯벌 없음). 주인공: 너럭바위 가장자리에 멈춤(작게, 물통). 고양이: 옆. 맑은 아침.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S02 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 L01

```text
Change the camera to a high wide view angled down along the same cove a moment later, in the clear morning sun: black basalt boulders and flat lava shelves run unbroken right down into the water, bare rock all the way to the sea's edge along the whole cove, the shoreline shaped like the one in <IMAGE_3>; the figure from <IMAGE_1>, small in the lower middle of the frame, stands on the rocks with the bamboo flask in its hand, and the ginger cat from <IMAGE_2> is a few steps behind it. The shoreline is empty in both directions. Keep the light of <IMAGE_0> and both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 L01

```text
<IMAGE_0> is the first frame. The figure walks slowly along the rocks toward a broad flat lava shelf, and the cat follows a few steps behind. Static high wide camera. It ends with the figure stopping at the edge of the flat shelf, the cat beside it. Pace the action so that this ending is reached at about 4.6 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Take only the coastline, rocks and distant hills from <IMAGE_3>. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure walks slowly along the rocks toward a broad flat lava shelf, and the cat follows a few steps behind. Static high wide camera. It ends with the figure stopping at the edge of the flat shelf, the cat beside it. Pace the action so that this ending is reached at about 4.6 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S04 · HAVE · 젖은 쑥 솜을 볕에 펴 말림 · 가진 것을 나란히 (인벤토리) · 0:12.85–0:17.70 (4.85s)

**장면** 시간 점프(조금 뒤). 비스듬한 미디엄(가슴 높이). EP.2에서 쑥을 말리던 볕 드는 너럭바위(연한 조약돌 3개). 주인공이 뒤꿈치 위에 앉아 젖어 뭉친 회녹색 쑥 솜을 얇게 뜯어 펴고 조약돌 3개로 눌러 볕에 말린다(오후 불씨 재료). 바위 위에 쇠못·깨진 흰 돌·물통이 나란히. 인물은 중앙~오른쪽, 왼쪽 1/3은 바위와 바다만(인벤토리 패널 자리).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S03
- 빛: clear_morning · 레퍼런스: P, NAIL, FLINT, FLASK
- 생성 6s → 사용 구간 0.000–4.850s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N04` 가진 건 물통과 쇠못, 흰 돌, 그리고 젖은 쑥 솜이다.
- 오버레이: `inventory_panel` (overlays.json)
- 효과음: 솜 뜯는 소리, 조약돌 놓는 소리 3번, 아침 파도
- 끝 상태(다음 샷의 출발점): 너럭바위: 회녹색 쑥 솜을 얇게 펴 조약돌 3개로 눌러 둠(볕에 말리는 중), 옆에 쇠못·깨진 흰 돌·물통(마개 끼움). 주인공: 뒤꿈치 위 앉음, 손은 무릎 위, 고개 숙임. 맑은 아침.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S03 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT · 5) 레퍼런스 FLASK

```text
Change the camera to a medium view at chest height, slightly to the side, a little later: the figure from <IMAGE_1> sits back on its heels at a flat black basalt slab in the morning sun, its blank head tilted down toward its hands, which hold two damp, matted balls of grey-green mugwort fluff over the warm rock beside three pale pebbles; laid out in a row on the slab beside it are the iron nail from <IMAGE_2>, the broken white stone from <IMAGE_3> and the bamboo flask from <IMAGE_4> with its plug in. Frame the figure in the centre-right and keep the left third of the frame as plain rock and sea. Keep the light, outfit and designs exactly as in <IMAGE_0>, <IMAGE_1>, <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT · <IMAGE_4> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The hands pull the damp fluff apart into thin loose tufts on the warm rock and set the three pale pebbles on them, one after another, so the wind cannot take them. Static camera. It ends with the tufts spread under the pebbles beside the nail, the white stone and the flask, the figure's hands resting on its knees. Pace the action so that this ending is reached at about 4.5 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_4>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hands pull the damp fluff apart into thin loose tufts on the warm rock and set the three pale pebbles on them, one after another, so the wind cannot take them. Static camera. It ends with the tufts spread under the pebbles beside the nail, the white stone and the flask, the figure's hands resting on its knees. Pace the action so that this ending is reached at about 4.5 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S05 · GATHER · 밀물이 닿지 않는 높은 너럭바위의 오목들 — 고양이가 먼저 걸어 듦 · 0:17.70–0:20.80 (3.10s)

**장면** 시간 점프(한낮이 가까움, 볕이 강하다). 와이드(바위 높이보다 조금 위). 밀물이 닿지 않는 높은 너럭바위에 손바닥~팔 길이의 얕은 오목이 흩어져 있다. 밤새 물보라가 채운 오목엔 바닷물이 조금 반짝이고, 가장 얕은 오목들은 말라 가장자리에 얇은 흰 테만 남았다(두꺼운 소금 껍질 금지). 고양이가 전경에서 오목 사이를 골라 걷다가 흰 앞발로 바닷물 고인 오목의 젖은 가장자리를 밟는다(N07 짠물의 원인). 주인공은 뒤쪽.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S04
- 빛: late_morning_sun · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.100s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N05` 밀물도 닿지 않는 높은 너럭바위.
- 효과음: 바람, 먼 파도, 고양이 발소리(작게)
- 끝 상태(다음 샷의 출발점): 높은 너럭바위 와이드: 얕은 오목들(일부 바닷물, 가장 얕은 것은 말라 얇은 흰 테). 고양이: 마른 오목 가장자리에 서서 흰 테 쪽으로 고개 숙임. 주인공: 뒤쪽. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S04 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the scene to a wide view, from a little above rock height, of a broad flat basalt shelf high above the reach of the tide on the same cove, later in the morning with strong sun and short hard shadows: shallow hollows from palm-size to arm-length are scattered across the black rock, some still holding a little bright seawater left by the spray, and the shallowest ones dried out, each left with only a thin white ring around its edge; the ginger cat from <IMAGE_2> walks between the hollows in the foreground, and the figure from <IMAGE_1> stands further back near the slab. Keep the coastline, outfit and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The cat picks its way between the hollows, its white front paws splashing through the wet rim of a shallow pool of seawater, and stops at the edge of a dry one with a white ring. Static camera. It ends with the cat standing at the dry hollow, its head lowered toward the white ring. Pace the action so that this ending is reached at about 2.8 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat picks its way between the hollows, its white front paws splashing through the wet rim of a shallow pool of seawater, and stops at the edge of a dry one with a white ring. Static camera. It ends with the cat standing at the dry hollow, its head lowered toward the white ring. Pace the action so that this ending is reached at about 2.8 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S06 · GATHER · 흰 테에 코를 대는 고양이(고양이 역할 컷) → 스스로 물러남 · 0:20.80–0:25.35 (4.55s)

**장면** 앵글 컷(바위 높이 로우 클로즈업). 마른 얕은 오목의 얇은 흰 테(소금기)가 전경에 선명하고, 고양이가 코를 대고 수염을 앞으로 내밀어 냄새를 맡는다(핥지 않음 — 고양이 역할 컷). 이어 고양이가 스스로 고개를 들고 오른쪽 프레임 밖으로 걸어 나간다 — 손은 들어오지 않는다(EP.1 S06 원칙). (QC: 시작 프레임 후보에 인물이 합성되면 탈락)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S05
- 빛: late_morning_sun · 레퍼런스: C
- 생성 6s → 사용 구간 0.000–4.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N06` 물보라가 채운 얕은 오목이 볕에 말라 흰 테를 남긴다.
- 오버레이: `label_rim` (overlays.json)
- 효과음: 고양이 킁킁(아주 작게), 바람
- 끝 상태(다음 샷의 출발점): 마른 오목과 얇은 흰 테(전경, 선명). 고양이는 프레임 밖(스스로 물러남). 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S05 끝 프레임 · 2) 레퍼런스 C

```text
Change the camera to a low close-up at rock level, a moment later, across the dry shallow hollow from <IMAGE_0>: its thin crusty white ring is sharp in the foreground on the hot black basalt, and the ginger cat from <IMAGE_1> has its head down at the far edge of the hollow, nose close to the white ring and whiskers pushed forward. Only the cat and the rock are in this frame for now. Keep the strong late-morning sun and the cat exactly as in <IMAGE_0> and <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The cat sniffs along the white ring with its whiskers pushed forward, its nose hovering just above the crust, then lifts its head, turns and trots out of the frame to the right. Static camera. It ends with the empty dry hollow and its white ring sharp in the foreground. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the cat exactly as in <IMAGE_1>, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat sniffs along the white ring with its whiskers pushed forward, its nose hovering just above the crust, then lifts its head, turns and trots out of the frame to the right. Static camera. It ends with the empty dry hollow and its white ring sharp in the foreground. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S07 · GATHER · 관계 비트 — 흰 앞발을 민물로 헹구고, 남은 물은 고양이 몫 · 0:25.35–0:29.05 (3.70s)

**장면** 관계 비트(주인공이 고양이를 위해 하는 행동). 로우 클로즈업(손만). 고양이가 흰 테에서 떨어진 깨끗한 작은 오목 가장자리에 서 있다. 손이 물통의 민물을 흰 앞발 위로 천천히 부어 헹구고, 헹군 물은 바위 아래로 흘러간다. 고양이가 한쪽 앞발을 털고, 고개를 숙여 물통에서 떨어지는 가는 민물 줄기를 핥아 마신다(바닷물·소금은 핥지 않음).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S06
- 빛: late_morning_sun · 레퍼런스: P, C, FLASK
- 생성 5s → 사용 구간 0.000–3.700s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N07` 고양이 발에 묻은 짠물은 민물로 헹군다.
- 효과음: 물 붓는 소리, 고양이 발 터는 소리, 할짝이는 소리(작게)
- 끝 상태(다음 샷의 출발점): 헹군 물은 바위 아래로 흘러감, 고양이가 물통에서 떨어지는 가는 물줄기를 핥음(흰 앞발 젖음). 손: 물통을 기울여 듦(손만, 민물 거의 다 씀). 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S06 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK

```text
Change the camera to a low close-up a moment later beside a small clean hollow in the rock, away from the white rings: the ginger cat from <IMAGE_2> stands with its two white front paws at the edge of the hollow, and the matte light-grey porcelain hands of the figure from <IMAGE_1> hold the bamboo flask from <IMAGE_3>, unplugged, tilted just above the cat's paws. Keep the strong late-morning sun of <IMAGE_0> and all designs exactly as in <IMAGE_2> and <IMAGE_3>; only the hands and forearms of the figure appear, its head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The flask pours a slow trickle of fresh water over the cat's white front paws and it runs off down the rock; the cat lifts and shakes one paw, then lowers its head and laps from the thin stream still trickling from the flask. Static camera. It ends with the cat lapping from the trickle and the hands holding the flask tilted beside it. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The flask pours a slow trickle of fresh water over the cat's white front paws and it runs off down the rock; the cat lifts and shakes one paw, then lowers its head and laps from the thin stream still trickling from the flask. Static camera. It ends with the cat lapping from the trickle and the hands holding the flask tilted beside it. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S08 · FAIL · 솥 대신 전복 껍데기로 바닷물을 뜸 — 구멍에서 물줄기 · 0:29.05–0:32.80 (3.75s)

**장면** 시간 점프(조금 뒤, 아래쪽 바위 물웅덩이). 측면 미디엄 클로즈업. 주인공이 맑은 바위 물웅덩이 옆에 무릎 꿇고, 바위틈에서 주운 큰 전복 껍데기로 바닷물을 떠 올린다. 들어 올리자 가장자리에 한 줄로 난 구멍들에서 가는 물줄기가 떨어지기 시작한다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S07
- 빛: late_morning_sun · 레퍼런스: P, ABALONE
- 생성 5s → 사용 구간 0.000–3.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N08` 솥 대신 전복 껍데기로 바닷물을 떠 올린다.
- 효과음: 물 뜨는 소리, 가는 물줄기 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 웅덩이 옆 무릎, 오른손에 전복 껍데기를 들어 올림(구멍마다 물줄기), 고개 숙임. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S07 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE

```text
Change the camera to a medium close-up from the side a little later, lower down the shore beside a clear rock pool among the black boulders: the figure from <IMAGE_1> kneels at the pool's edge, its blank head bowed toward its hands, holding the large empty abalone shell from <IMAGE_2> in its right hand, hollow side up, just touching the water. Keep the strong late-morning sun, the outfit and the designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. The hand dips the shell into the pool and lifts it out brimming; at once thin streams of water start to pour from the row of holes along the shell's edge. Static camera. It ends with the figure holding the shell up just above the pool, water streaming from its holes. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand dips the shell into the pool and lifts it out brimming; at once thin streams of water start to pour from the row of holes along the shell's edge. Static camera. It ends with the figure holding the shell up just above the pool, water streaming from its holes. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S09 · FAIL · 매크로 — 구멍마다 물이 샘 · 0:32.80–0:35.20 (2.40s)

**장면** 앵글 컷(매크로, 손만). 들어 올린 전복 껍데기 — 바깥은 거칠고 따개비가 붙었고, 가장자리에 한 줄로 난 구멍 4~5개마다 물줄기가 떨어진다. 진주빛 안쪽의 물이 금세 줄어 빈다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S08
- 빛: late_morning_sun · 레퍼런스: P, ABALONE
- 생성 4s → 사용 구간 0.000–2.400s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N09` 구멍마다, 물이 샌다.
- 오버레이: `label_abalone` (overlays.json)
- 효과음: 물줄기 소리 → 물방울
- 끝 상태(다음 샷의 출발점): 빈 전복 껍데기(물방울만 떨어짐)를 든 손(손만). 매크로, 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S08 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE

```text
Change the camera to a macro close-up a moment later of the abalone shell from <IMAGE_2> held up by the matte light-grey porcelain hand of the figure from <IMAGE_1>: the rough, barnacled outer side and the curved row of holes along its edge face the camera, a thin stream of water falling from each open hole, and the iridescent inside still holding some water. Keep the light of <IMAGE_0>; only the hand and forearm appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. Water keeps streaming from every hole until the shining inside of the shell is empty and only drops fall. Static macro camera. It ends with the empty, dripping shell held still in the hand. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Water keeps streaming from every hole until the shining inside of the shell is empty and only drops fall. Static macro camera. It ends with the empty, dripping shell held still in the hand. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S10 · FAIL · 빈 껍데기를 내려놓고 멈춤 · 0:35.20–0:37.75 (2.55s)

**장면** 앵글 컷(측면 미디엄). 주인공이 빈 전복 껍데기를 웅덩이 옆 바위에 내려놓고 두 손을 무릎에 얹은 채 멈춘다. 고개 숙임. 껍데기는 버리지 않고 옆에 둔다(TEST에서 체로 다시 씀).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S09
- 빛: late_morning_sun · 레퍼런스: P, ABALONE
- 생성 4s → 사용 구간 0.000–2.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N10` 끓일 그릇이, 없다.
- 효과음: 껍데기 내려놓는 소리, 정적 — 파도만
- 끝 상태(다음 샷의 출발점): 주인공: 웅덩이 옆 무릎, 두 손 무릎 위, 고개 숙임. 빈 전복 껍데기는 옆 바위 위. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S09 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE

```text
Change the camera to a medium view from the side a moment later: the figure from <IMAGE_1> kneels by the rock pool with its blank head bowed, holding the dripping, empty abalone shell from <IMAGE_2> low over the rock. Keep the light, the place and the designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. The figure sets the empty shell down on the rock beside the pool and rests both hands on its knees, still. Static camera. It ends with the figure kneeling motionless, the empty shell on the rock beside it. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure sets the empty shell down on the rock beside the pool and rests both hands on its knees, still. Static camera. It ends with the figure kneeling motionless, the empty shell on the rock beside it. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S11 · PRINCIPLE · 측면 정렬 구도 · 넓은 오목에 바닷물을 부음 (도면 — 수면선 y≈720) · 0:37.75–0:43.44 (5.70s)

**장면** 측면 정렬 구도(완전한 옆모습, S05 참고 프레임, 바위 높이, 정지 카메라). 높은 너럭바위의 넓고 얕은 오목이 프레임을 가로지르고, 고요한 수면이 밝은 수평선으로 프레임 위에서 약 37%(y≈720)에 놓인다 — 도면의 수면선. 주인공은 오목 건너편에 무릎 꿇고(상단 띠 y300~540, 중앙보다 약간 왼쪽), 물통의 바닷물을 오목에 천천히 붓는다(물통은 웅덩이에서 바닷물로 채움). 고양이는 왼쪽 위 마른 바위. 오른쪽 위는 바다와 하늘(도면의 증발 화살표 자리). 아래 약 60%는 앞쪽의 그늘진 바위 면만(도면, 배경 40% 어둡게).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S10 · 참고 프레임 S05
- 빛: late_morning_sun · 레퍼런스: P, C, FLASK
- 생성 7s → 사용 구간 0.000–5.698s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N11` 바닷물 1리터엔 소금이 약 35그램 녹아 있다. / `N12` 물만 날려 보내면 소금은 남는다.
- 오버레이: `diagram_salt` (overlays.json)
- 효과음: 물 붓는 소리, 바람(낮게)
- 끝 상태(다음 샷의 출발점): 정렬 구도: 넓은 오목(수면 y≈720, 고요), 건너편에 무릎 꿇은 주인공(상단 띠, 물통 세워 듦), 왼쪽 위 고양이, 오른쪽 위 바다·하늘. 아래 60% 그늘진 바위 면.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S10 끝 프레임 · 2) S05 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 FLASK

```text
Change the time to a little later and the place to the high flat shelf from <IMAGE_1> (take only the rock shelf and its hollows from it; the figure and the cat appear only once, where described here), with the camera side-on at rock height: a wide, shallow hollow full of still seawater runs across the frame, its water surface a bright level line about thirty-seven percent of the way down the frame; the figure from <IMAGE_2> kneels just beyond the far edge of the hollow, slightly left of centre, side-on to the camera in full profile, its blank head bowed toward the water, its head and shoulders between about a sixth and just over a quarter of the way down the frame, holding the bamboo flask from <IMAGE_4> tilted over the water, and the ginger cat from <IMAGE_3> sits on a dry rock at the upper left, level with the figure; the upper right of the frame is open sea and sky. Leave the lower sixty percent of the frame plain: only the dark, shadowed near face of the rock. Keep the strong late-morning sun of <IMAGE_0> and all designs exactly as in <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 7s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. A thin stream of seawater runs from the flask into the hollow, sending slow rings across the surface, then the flask tips upright. Static camera. It ends with the same calm composition, the water surface settling still and bright. Pace the action so that this ending is reached at about 5.4 seconds and then held, almost motionless, until the clip ends at 7 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. A thin stream of seawater runs from the flask into the hollow, sending slow rings across the surface, then the flask tips upright. Static camera. It ends with the same calm composition, the water surface settling still and bright. Pace the action so that this ending is reached at about 5.4 seconds and then held, almost motionless, until the clip ends at 7 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S12 · PRINCIPLE · 실시간 이어짐 · 수면 위 열기, 고양이가 엎드림 (도면) · 0:43.44–0:49.60 (6.15s)

**장면** 같은 컷 이어서(실시간). 수면 위로 열기가 희미하게 아른거리고 햇빛이 반짝인다. 주인공이 물통을 오목 옆에 내려놓고, 고양이가 따뜻한 바위에 엎드린다. 구도는 S11과 같다(수면선 y≈720 유지).

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S11
- 빛: late_morning_sun · 레퍼런스: P, C, FLASK
- 생성 8s → 사용 구간 0.000–6.154s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N13` 물을 열에 아홉은 날려야 소금이 비친다.
- 오버레이: `diagram_salt` (overlays.json)
- 효과음: 바람(낮게), 먼 파도
- 끝 상태(다음 샷의 출발점): 같은 구도(수면선 y≈720). 주인공: 물통을 옆에 두고 무릎 꿇음. 고양이: 엎드림. 수면 반짝임.

**① 시작 프레임** = S11 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
Continuing from <IMAGE_0>, faint heat shimmer rises off the black rock and sunlight glints on the still water; the figure sets the flask down beside the hollow, and the cat settles down onto its chest on the warm rock. Static camera. It ends with the same composition, the figure kneeling still behind the bright water. Pace the action so that this ending is reached at about 5.9 seconds and then held, almost motionless, until the clip ends at 8 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, faint heat shimmer rises off the black rock and sunlight glints on the still water; the figure sets the flask down beside the hollow, and the cat settles down onto its chest on the warm rock. Static camera. It ends with the same composition, the figure kneeling still behind the bright water. Pace the action so that this ending is reached at about 5.9 seconds and then held, almost motionless, until the clip ends at 8 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S13 · PRINCIPLE · 조건 줄(실사) — 오목 대여섯 개를 바닷물로 채움 · 0:49.60–0:53.86 (4.26s)

**장면** 시간 점프(조금 뒤, 물통으로 여러 번 오간 뒤 — 0.5 L 통으로 열몇 번). 와이드(높은 너럭바위). 오목 대여섯 개가 바닷물로 채워져 하늘빛으로 반짝인다(바다에 가까운 오목부터 채움). 주인공이 물가 쪽에서 물통을 들고 올라와 마지막 빈 오목에 붓는다. 고양이는 큰 바위 그늘에 누움. 도면 없음.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S12
- 빛: late_morning_sun · 레퍼런스: P, C, FLASK
- 생성 6s → 사용 구간 0.000–4.263s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N14` 그래서 볕으로 먼저 졸이고 불로 마저 끓인다.
- 효과음: 바람, 물 붓는 소리, 맨발 소리
- 끝 상태(다음 샷의 출발점): 와이드: 오목 5~6개 모두 바닷물로 반짝임. 주인공: 마지막 오목 옆에 일어섬(물통). 고양이: 큰 바위 그늘. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S12 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK

```text
Change the time to a little later and the camera to a wide view of the high flat shelf: five or six shallow hollows across the black basalt are now filled with seawater and shine with the sky, and the figure from <IMAGE_1> walks up from the water's edge at the right with the bamboo flask from <IMAGE_3> in hand toward the last, still-empty hollow; the ginger cat from <IMAGE_2> lies in the shade of a large boulder at the back. Keep the strong late-morning sun and all designs exactly as in <IMAGE_0>, <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure crouches at the empty hollow and pours the flask into it, the water spreading across the bottom. Static wide camera. It ends with all the hollows shining with water and the figure standing up beside the last one. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure crouches at the empty hollow and pours the flask into it, the water spreading across the bottom. Static wide camera. It ends with all the hollows shining with water and the figure standing up beside the last one. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S14 · PRINCIPLE · 귀에 남는 문장 — 볕이 끓이는 오목, 맨발이 지나감 · 0:53.86–0:57.07 (3.21s)

**장면** 앵글 컷(로우 클로즈업, 오목 수면 높이). 채운 오목 수면에 해가 눈부시게 비치고 검은 바위 위로 열기가 아른거린다. 왼쪽 가장자리의 맨발(자기 질감 발, 걷은 숯회색 바지)이 뜨거운 바위를 천천히 밟고 지나가 프레임 밖으로(맨발 — EP.4 짚신 복선). 도면 없음.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S13
- 빛: late_morning_sun · 레퍼런스: P
- 생성 5s → 사용 구간 0.000–3.209s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N15` 볕은 땔감이 들지 않는 불이다.
- 효과음: 바람(낮게), 맨발이 뜨거운 돌을 딛는 소리
- 끝 상태(다음 샷의 출발점): 볕이 눈부신 채운 오목(수면), 열기 아른거림. 발은 프레임 밖. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S13 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a low close-up at the level of the water in one of the filled hollows from <IMAGE_0>: the sun blazes on the still surface and heat shimmer rises from the black rock around it; at the left edge of the frame stand the bare matte light-grey porcelain feet and lower legs of the figure from <IMAGE_1>, charcoal trousers rolled to mid-calf. Keep the strong late-morning sun; only the feet and lower legs appear, the figure's head and body stay out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The bare porcelain feet step slowly past the hollow across the hot black rock and out of the frame; the shimmer keeps rising and the sun glitters on the water. Static camera. It ends with the bright, still hollow alone in the frame. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's bare matte light-grey porcelain feet and lower legs, with charcoal trousers rolled to mid-calf, appear, exactly as in <IMAGE_1>; its head and body stay out of frame. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The bare porcelain feet step slowly past the hollow across the hot black rock and out of the frame; the shimmer keeps rising and the sun glitters on the water. Static camera. It ends with the bright, still hollow alone in the frame. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's bare matte light-grey porcelain feet and lower legs, with charcoal trousers rolled to mid-calf, appear,; its head and body stay out of frame. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S15 · BUILD · (재료 인서트) 잔해 판자에 못 박힌 구리판 · 0:57.07–1:00.82 (3.75s)

**장면** 시간 점프(조금 뒤). 재료 인서트(어깨 너머, 뒤통수만). 폭풍이 밀물선 위로 올려 놓고 사흘 볕에 마른 난파 잔해 더미(회색 판자·통판·밧줄) 속, 부서진 판자 한 장에 무광 적갈색 구리판이 가장자리 못 줄로 박혀 있다(배 부엌칸 벽 덧판이라는 허구 설정 — 설명란에만). 천천히 푸시인. 글자·각인·반짝이는 새 구리 없음.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S14
- 빛: late_morning_sun · 레퍼런스: P, COPPER
- 생성 5s → 사용 구간 0.000–3.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N16` 잔해 속 판자에 구리판 한 장이 못 박혀 있다.
- 효과음: 바람, 마른 나무 부딪는 소리
- 끝 상태(다음 샷의 출발점): 프레임 중앙: 판자에 못 박힌 구리판(떼기 전). 주변에 마른 판자·통판(땔감). 주인공 어깨는 프레임 가장자리. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S14 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 COPPER

```text
Change the camera to an over-the-shoulder view from behind the figure from <IMAGE_1>, its blank head seen only from the back, a little later, aimed down at what is left of the shipwreck debris the storm threw up above the high-tide line: a small heap of dry, sun-bleached grey planks, split barrel staves and a coil of rope, and among them one broken board with the dull reddish-brown copper sheet from <IMAGE_2> nailed flat to it along its edges. Keep the strong sun, the figure's design and the copper sheet exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 COPPER

```text
<IMAGE_0> is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the copper sheet on the board. It ends with the copper sheet clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the copper sheet's size, dull tarnished reddish-brown colour and row of nails along its edges exactly as in <IMAGE_2>. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the copper sheet on the board. It ends with the copper sheet clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The copper sheet is a thin, dull reddish-brown sheet about forty by thirty centimetres, tarnished dark, nailed along its edges to a broken oak board. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S16 · BUILD · 떼어 낸 구리판의 마지막 귀를 접어 얕은 솥 완성 · 1:00.82–1:03.97 (3.15s)

**장면** 시간 점프(20~40분 뒤 — 쇠못을 지렛대 삼아 못을 뽑고 판을 떼어 냄, 생략). 클로즈업(손만). 평평한 바위 위, 빈 못 구멍이 가장자리에 줄지은 구리판의 세 변이 이미 접혀 올라가 있다. 두 손이 바위 모서리에 대고 마지막 변을 접어 올리고 모서리를 주름 잡아 눌러, 얕은 판을 바위 위에 평평하게 놓는다. 못 구멍은 모두 접어 올린 벽 위쪽(바닥에 구멍 없음).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S15
- 빛: late_morning_sun · 레퍼런스: P, COPPER, COPPER_PAN
- 생성 5s → 사용 구간 0.000–3.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N17` 네 귀를 접어 올리면 얕은 솥이 된다.
- 효과음: 얇은 구리 휘는 소리, 구리판이 돌에 닿는 소리
- 끝 상태(다음 샷의 출발점): 평평한 바위 위 완성된 얕은 구리판 솥(네 벽, 주름 잡힌 모서리, 벽 위쪽에만 못 구멍). 손은 거둬들임. 강한 볕.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S15 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 COPPER · 4) 레퍼런스 COPPER_PAN

```text
Change the camera to a close-up a while later of a flat black basalt rock: the copper sheet from <IMAGE_2>, now pried off its board, lies on the rock with three of its sides already bent up into low sloping walls with pleated corners, like the tray in <IMAGE_3>, the row of empty nail holes running along the tops of the walls, and the matte light-grey porcelain hands of the figure from <IMAGE_1> press the last flat side against the rock's edge, ready to bend it up. Keep the strong sun of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 COPPER · <IMAGE_3> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The hands bend the last side up against the rock edge and press its two corners into rough pleats. Static camera. It ends with the finished shallow tray standing level on the rock, the hands drawing back. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the copper sheet's size, dull tarnished reddish-brown colour and row of nails along its edges exactly as in <IMAGE_2>. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_3>; any soot or white crust are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hands bend the last side up against the rock edge and press its two corners into rough pleats. Static camera. It ends with the finished shallow tray standing level on the rock, the hands drawing back. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The copper sheet is a thin, dull reddish-brown sheet about forty by thirty centimetres, tarnished dark, nailed along its edges to a broken oak board. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S17 · BUILD · 한낮 — 줄어든 오목의 물을 가운데 깊은 오목으로 모음(단계 농축) · 1:03.97–1:07.52 (3.55s)

**장면** 시간 점프(한낮, 그림자가 가장 짧다). 미디엄. 높은 너럭바위의 오목들 물이 줄어 가장자리에 흰 테가 생기기 시작했다. 주인공이 얕아진 오목에서 물통으로 물을 떠 가운데 깊은 오목 하나에 모아 붓는다(구엄식 단계 농축). 고양이는 큰 바위 그늘에서 잠듦.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S16 · 참고 프레임 S13
- 빛: midday_sun · 레퍼런스: P, C, FLASK
- 생성 5s → 사용 구간 0.000–3.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N18` 물이 줄면 더 적은 오목으로 모아 붓는다.
- 오버레이: `time_card_noon` (overlays.json)
- 효과음: 물 뜨는 소리, 물 붓는 소리, 바람
- 끝 상태(다음 샷의 출발점): 한낮. 주인공: 오목 사이에 쪼그려 물통을 얕은 오목에 담금. 가운데 깊은 오목에 물이 모임, 얕은 오목들은 바닥이 드러나며 흰 테. 고양이: 큰 바위 그늘에서 잠듦.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S16 끝 프레임 · 2) S13 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 FLASK

```text
Change the time to midday, the sun almost overhead and the shadows very short, at the high shelf shown in <IMAGE_1> (take only the rock and the hollows from it; the figure and the cat appear only once, where described here), with the camera at a medium distance: the water in the shallow hollows has sunk low and thin white rings are forming around their edges; the figure from <IMAGE_2> crouches between two hollows, dipping the bamboo flask from <IMAGE_4> into a low one, beside one deeper hollow in the middle that holds more water; the ginger cat from <IMAGE_3> sleeps in the shade of the large boulder at the back. Keep the outfit of <IMAGE_0> and all designs exactly as in <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure lifts the full flask from the low hollow and pours it into the deeper middle hollow, then dips it again into the next low one. Static camera. It ends with the figure crouched over the next low hollow, the flask in the water. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, harsh midday sun almost straight overhead, very short shadows, heat shimmer rising off the black rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lifts the full flask from the low hollow and pours it into the deeper middle hollow, then dips it again into the next low one. Static camera. It ends with the figure crouched over the next low hollow, the flask in the water. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, harsh midday sun almost straight overhead, very short shadows, heat shimmer rising off the black rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S18 · BUILD · 오후 — 어제 불자리에 마른 받침돌 셋 · 마른 판자 땔감 · 바람막이 · 1:07.52–1:10.67 (3.15s)

**장면** 시간 점프(오후, 해가 기울기 시작). 미디엄 와이드. 높은 물때선 위, EP.2의 불자리 바위 오목(큰 바위가 바람을 가림). 오목 둘레에 밀물선 위에서 주운 마른 주먹돌 셋이 받침으로 놓였다(젖은 갯바위 돌 금지 — 불에 터질 수 있음). 주인공이 잔해의 마지막 마른 회색 판자·통판 한 아름을 그 옆에 막 내려놓고 무릎 꿇은 상태에서(시작 프레임), 판자 하나를 바람 오는 쪽에 세워 돌에 기댄다(바람막이). 홈 난 널빤지는 이 더미에 없다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S17 · 참고 프레임 S02
- 빛: afternoon · 레퍼런스: P
- 생성 5s → 사용 구간 0.000–3.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N19` 땔감은 폭풍이 올려 둔 마른 판자다.
- 효과음: 마른 판자 내려놓는 소리, 나무가 돌에 기대는 소리
- 끝 상태(다음 샷의 출발점): 불자리: 오목 둘레 마른 돌 3개(받침), 바람 쪽에 세운 판자 바람막이, 옆에 마른 판자·통판 더미. 주인공: 돌 옆 무릎. 오후.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S17 끝 프레임 · 2) S02 끝 프레임 · 3) 레퍼런스 P

```text
Change the time to the afternoon, the sun lower from the left with long soft shadows, and the scene to the bare rock hollow from <IMAGE_1> where yesterday's fire burned, above the high-tide line and sheltered by the large boulder (take only the rocks, the large boulder and the hollow from it; the figure appears only once, where described here): three dry, fist-sized stones are set around the hollow as a stand, and the figure from <IMAGE_2> kneels beside the hollow with an armful of dry, sun-bleached grey planks and split barrel staves, the last of the debris, just set down beside it. Keep the outfit and the figure's design exactly as in <IMAGE_0> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The figure stands one plank on its edge on the windward side, leaning it against a stone as a windbreak, and settles back onto its knees. Static camera. It ends with the wood pile beside the hollow, the windbreak plank standing, and the figure kneeling by the three stones. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure stands one plank on its edge on the windward side, leaning it against a stone as a windbreak, and settles back onto its knees. Static camera. It ends with the wood pile beside the hollow, the windbreak plank standing, and the figure kneeling by the three stones. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S19 · BUILD · 볕에 마른 쑥 솜에 다시 불씨 — 쇠못과 흰 돌 · 1:10.67–1:14.27 (3.60s)

**장면** 익스트림 클로즈업(손만, 불자리 위). 왼손에 깨진 흰 돌(날 위) + 엄지로 누른, 아침 볕에 바삭하게 마른 쑥 솜. 오른손이 쇠못 간 면으로 날을 비스듬히 빠르게 긁어 내린다(손가락을 내리치지 않는 궤적). 여러 번 친 끝에 불티 하나가 솜에 박혀 주황 점이 번지고 가는 연기 한 줄(볶지 않은 쑥이라 EP.2처럼 쉽게 붙지 않는다). (입으로 불지 않는다 — 이후 둥지 흔들기는 생략, 시간 점프)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S18
- 빛: afternoon · 레퍼런스: P, NAIL, FLINT
- 생성 5s → 사용 구간 0.000–3.600s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N20` 어제 익힌 쇠와 돌로 다시 불을 깨운다.
- 효과음: '칙' 여러 번, 아주 작은 지글거림
- 끝 상태(다음 샷의 출발점): 쑥 솜에 주황 불씨 + 가는 연기 한 줄. 두 손 쥐기 자세로 정지(손만). 오후.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S18 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT

```text
Change the camera to an extreme close-up a moment later of the figure's matte light-grey porcelain hands from <IMAGE_1> above the fire hollow: the left hand holds the broken white stone from <IMAGE_3> with its sharp glassy edge on top and a pinch of crisp, sun-dried grey-green fluff resting on the stone just behind the edge under the left thumb, and the right hand holds the iron nail from <IMAGE_2> by its head, its bright ground side just above the edge. Keep the afternoon sun of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The right hand scrapes the nail down the stone's edge in fast glancing strokes, again and again, until at last a tiny orange spark lands on the fluff and stays, and a pin-point of orange glow slowly spreads in it as a thin thread of smoke rises. Static macro camera. It ends with the small orange glow in the fluff, the thread of smoke rising and the hands still. Pace the action so that this ending is reached at about 3.3 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand scrapes the nail down the stone's edge in fast glancing strokes, again and again, until at last a tiny orange spark lands on the fluff and stays, and a pin-point of orange glow slowly spreads in it as a thin thread of smoke rises. Static macro camera. It ends with the small orange glow in the fluff, the thread of smoke rising and the hands still. Pace the action so that this ending is reached at about 3.3 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S20 · TEST · 늦은 오후 — 돌 셋 위 구리판 솥이 끓고, 줄면 또 부음 · 고양이는 멀리 · 1:14.27–1:17.92 (3.65s)

**장면** 시간 점프(한참 뒤, 늦은 오후). 측면 미디엄. 돌 셋 위의 구리판 솥 아래 작은 불(판자 끝, 바람막이), 솥 안의 졸인 물이 맑게 끓으며 흰 김이 바람 아래쪽으로 흐른다. 주인공이 바람 위쪽에 무릎 꿇고 팔을 뻗어 물통의 졸인 물을 솥에 보탠다(솥 높이 2/3). 고양이는 몇 걸음 뒤 큰 바위 그늘 — 불·김과 멀리, 먼저 자리를 피해 있음.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S19 · 참고 프레임 S18
- 빛: late_afternoon_fire · 레퍼런스: P, C, COPPER_PAN
- 생성 5s → 사용 구간 0.000–3.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N21` 끓어 줄면, 또 붓는다. / `N22` 해가 기울 무렵, 가장자리에 흰 테가 선다.
- 오버레이: `time_card_late` (overlays.json)
- 효과음: 보글보글 끓는 소리, 작은 불 타닥, 물 붓는 소리
- 끝 상태(다음 샷의 출발점): 구리판 솥(돌 셋 위, 2/3 높이)이 끓음, 흰 김은 바람 아래로. 주인공: 바람 위쪽 무릎, 물통 세워 듦. 고양이: 큰 바위 그늘(멀리). 늦은 오후 금빛.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S19 끝 프레임 · 2) S18 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 COPPER_PAN

```text
Change the time to much later in the afternoon, the sun low and golden from the left, at the same fire hollow as in <IMAGE_1> (take only the rocks, the large boulder, the three stones and the windbreak plank from it; the figure appears only once, where described here), seen in a medium side view: the shallow copper tray from <IMAGE_4> sits level on the three stones over a small fire of plank ends, the windbreak plank standing behind it and a few planks left beside the hollow, and the liquid in the tray is boiling, white steam drifting away downwind; the figure from <IMAGE_2> kneels on the upwind side, arm stretched out, tilting the bamboo flask, a single bamboo section with a dark oak plug, toward the tray; the ginger cat from <IMAGE_3> sits in the shade of the large boulder several steps behind, well away from the fire. Keep all designs exactly as in <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. A stream of liquid from the flask pours into the boiling tray until it is about two-thirds full; the boiling settles for a moment, then rolls up again with more steam. Static camera. It ends with the tray boiling steadily and the figure kneeling back with the flask upright. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_3>; any soot or white crust are exactly as described above. Photoreal live-action look, low golden late-afternoon sun from the left, long shadows, the small fire glowing warm under the copper tray, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. A stream of liquid from the flask pours into the boiling tray until it is about two-thirds full; the boiling settles for a moment, then rolls up again with more steam. Static camera. It ends with the tray boiling steadily and the figure kneeling back with the flask upright. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, low golden late-afternoon sun from the left, long shadows, the small fire glowing warm under the copper tray, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S21 · TEST · 해 질 녘 — 솥 가장자리 흰 테, 얇은 결정 막 (결정은 여기서부터) · 1:17.92–1:20.32 (2.40s)

**장면** 시간 점프(해 질 녘). 솥 클로즈업(위에서 비스듬히). 물이 처음의 1/10 남짓으로 줄었다. 안쪽 가장자리를 따라 흰 테(소금꽃)가 둘러지고, 표면에 얇은 결정 막이 뜬다. 손에 쥔 막대가 천천히 저으면 막이 깨지며 바닥에 잔 알갱이가 보인다. 결정은 이 샷부터만 보인다(S20까지는 맑은 물).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S20
- 빛: dusk_fire · 레퍼런스: P, COPPER_PAN
- 생성 4s → 사용 구간 0.000–2.400s (아웃 포인트 = 다음 샷 출발 프레임)
- 효과음: 낮게 끓는 소리, 막대 젓는 소리
- 끝 상태(다음 샷의 출발점): 구리판 솥: 얕게 남은 탁한 물, 안쪽 가장자리 흰 테, 깨진 결정 막과 바닥의 잔 알갱이(걸쭉해지기 시작). 막대를 쥔 손(테두리에, 손만). 해 질 녘, 김.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S20 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 COPPER_PAN

```text
Change the time to dusk and the camera to a close-up angled steeply down into the copper tray from <IMAGE_2>, still over the small fire: only a shallow layer of cloudy liquid is left, a crusty white ring has formed all around the inside edges, and a thin, glassy skin of tiny crystals floats on the surface; the matte light-grey porcelain hand of the figure from <IMAGE_1> holds a bare wooden stick resting on the tray's rim. Keep the place of <IMAGE_0>; only the hand and forearm appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The stick stirs slowly through the liquid, breaking the thin crystal skin into flakes and showing small grey-white grains settled on the bottom, as steam rises. Static camera. It ends with the stick resting on the rim and the liquid thick with grains. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_2>; any soot or white crust are exactly as described above. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, the small fire under the copper tray the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The stick stirs slowly through the liquid, breaking the thin crystal skin into flakes and showing small grey-white grains settled on the bottom, as steam rises. Static camera. It ends with the stick resting on the rim and the liquid thick with grains. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, the small fire under the copper tray the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S22 · TEST · 소금죽이 튐 — 긴 막대로 불을 빼 끝까지 졸이지 않음 · 1:20.32–1:23.27 (2.95s)

**장면** 앵글 컷(측면 미디엄). 걸쭉해진 솥에서 작은 방울이 탁탁 튀기 시작한다. 주인공이 몸을 멀리 둔 채 긴 막대로 불타는 판자 끝 두 개를 솥 아래에서 끌어내 불을 줄인다(끝까지 졸이지 않음 — 쓴맛·튐 방지). 맨손으로 솥을 잡지 않는다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S21 · 참고 프레임 S20
- 빛: dusk_fire · 레퍼런스: P, COPPER_PAN
- 생성 4s → 사용 구간 0.000–2.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N23` 끝까지 졸이면, 쓴맛이 남는다.
- 효과음: 탁탁 튀는 소리, 나무 끄는 소리, 치익(작게)
- 끝 상태(다음 샷의 출발점): 솥 아래 불은 잦아든 숯불, 끌어낸 판자 끝 두 개가 바위 위에서 연기. 솥 안 걸쭉한 회색 소금죽. 주인공: 바람 위쪽 무릎, 긴 막대. 해 질 녘.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S21 끝 프레임 · 2) S20 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 COPPER_PAN

```text
Change the camera to a medium side view a moment later: the figure from <IMAGE_2> kneels at arm's length from the fire on its upwind side, holding a long stick, and the copper tray from <IMAGE_3> sits on the three stones over the small fire, its thick grey slurry spitting small droplets. Keep the dusk light, the place and all designs exactly as in <IMAGE_0>, <IMAGE_2> and <IMAGE_3>. Take only the rocks, the three stones and the windbreak plank from <IMAGE_1>; the figure appears only once, where described here.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The figure reaches in with the long stick and drags two burning plank ends out from under the tray onto the bare rock, and the spitting slows down; the figure keeps its body well back from the tray. Static camera. It ends with low embers under the tray, the dragged-out plank ends smoking on the rock, and the figure kneeling back with the stick. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_2>; any soot or white crust are exactly as described above. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, the small fire under the copper tray the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure reaches in with the long stick and drags two burning plank ends out from under the tray onto the bare rock, and the spitting slows down; the figure keeps its body well back from the tray. Static camera. It ends with low embers under the tray, the dragged-out plank ends smoking on the rock, and the figure kneeling back with the stick. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, the small fire under the copper tray the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S23 · TEST · 실패한 전복 껍데기가 체로 — 젖은 소금을 담자 구멍에서 간수가 떨어짐 · 1:23.27–1:27.02 (3.75s)

**장면** 시간 점프(조금 뒤, 솥이 식음 — 뜨거운 솥은 막대 두 개로만 옮겼다, 생략). 클로즈업(손만). FAIL의 전복 껍데기가 조약돌 두 개 위에 놓였고, 구멍 위에 마른 풀을 한 겹 깔았다. 손이 납작한 통판 조각으로 식은 솥의 젖은 회색 소금을 떠 껍데기에 옮긴다. 남은 물(간수)이 구멍으로 방울방울 떨어져 바위를 적신다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S22
- 빛: dusk_embers · 레퍼런스: P, ABALONE, COPPER_PAN
- 생성 5s → 사용 구간 0.000–3.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N24` 구멍 난 전복 껍데기가, 이번엔 체가 된다.
- 효과음: 소금 떠 옮기는 사각 소리, 물방울 똑똑
- 끝 상태(다음 샷의 출발점): 전복 껍데기(조약돌 두 개 위, 마른 풀 깔림)에 젖은 회색 소금 한 줌 남짓(껍데기 바닥을 덮을 정도), 구멍에서 물방울이 떨어짐. 옆에 식은 구리판 솥(옆면 그을음). 손은 통판 조각을 듦(손만). 해 질 녘.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S22 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE · 4) 레퍼런스 COPPER_PAN

```text
Change the camera to a close-up a little later, beside the fire hollow, of the empty abalone shell from <IMAGE_2> propped on two small pebbles, hollow side up, its holes covered by a thin layer of dry grass, with the copper tray from <IMAGE_3> cooled on the rock beside it, its outer walls streaked with soot and a thin layer of wet grey salt across its bottom; the matte light-grey porcelain hand of the figure from <IMAGE_1> holds a flat piece of barrel stave over the tray like a scoop. Keep the dusk light of <IMAGE_0>; only the hand and forearm appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE · <IMAGE_3> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The hand scrapes the thin layer of wet grey salt together with the stave and tips it into the grass-lined shell; a moment later clear drops begin to fall from the holes underneath onto the rock. Static camera. It ends with the wet salt lying in the shell and drops falling steadily from its holes. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_3>; any soot or white crust are exactly as described above. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand scrapes the thin layer of wet grey salt together with the stave and tips it into the grass-lined shell; a moment later clear drops begin to fall from the holes underneath onto the rock. Static camera. It ends with the wet salt lying in the shell and drops falling steadily from its holes. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S24 · TEST · 손끝에서 사각거리는 회색 소금 (답 · 히어로) · 1:27.02–1:30.47 (3.45s)

**장면** 히어로 샷(매크로, 손만). 엄지와 검지가 껍데기의 소금을 한 꼬집 집어 비빈다. 회색빛 잔 결정(재 티 섞임)이 손끝에서 부서지며 껍데기로 떨어지고, 몇 알은 손끝에 붙어 마지막 빛을 받는다. 사각거리는 소리. 맛보는 장면 없음, 새하얀 소금 더미 금지.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S23
- 빛: dusk_embers · 레퍼런스: P, ABALONE
- 생성 5s → 사용 구간 0.000–3.450s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N25` 손끝에서, 소금이 사각거린다.
- 효과음: 소금 결정 비비는 사각사각(가깝게)
- 끝 상태(다음 샷의 출발점): 손끝(엄지·검지)에 붙은 회색빛 잔 결정 몇 알, 아래 껍데기의 소금 더미(초점 밖). 해 질 녘 마지막 빛.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S23 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE

```text
Change the camera to a macro close-up a moment later of the matte light-grey porcelain thumb and forefinger of the figure from <IMAGE_1> holding a pinch of the damp salt just above the abalone shell from <IMAGE_2>: coarse, uneven grey-white crystals with a few dark specks of ash, the heaped salt in the shell soft and out of focus below. Keep the dusk light of <IMAGE_0>; only the hand appears, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. The thumb and forefinger rub the pinch together slowly; the grey-white crystals grind and crumble and fall back onto the heap in the shell, a few sticking to the fingertips and catching the last light. Static macro camera. It ends with the fingertips held still above the shell, a few crystals clinging to them. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The thumb and forefinger rub the pinch together slowly; the grey-white crystals grind and crumble and fall back onto the heap in the shell, a few sticking to the fingertips and catching the last light. Static macro camera. It ends with the fingertips held still above the shell, a few crystals clinging to them. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S25 · COST · 와이드 — 큰 재 더미, 바닥난 땔감, 그을린 솥 · 고양이가 와서 옆에 앉음 · 1:30.47–1:33.42 (2.95s)

**장면** 앵글 컷(와이드, 해 질 녘). 불자리: 잦아든 숯불과 큰 재 더미. 아침에 쌓아 둔 땔감 더미 자리엔 그을린 통판 끝 두세 개뿐. 옆면이 검게 그을린 구리판 솥이 옆 바위에. 바람막이 판자도 마지막에 태워 돌 셋 바람 쪽은 맨바위. 주인공이 숯불 건너편에 앉아 있고, 고양이가 큰 바위 쪽에서 걸어와 숯불 반대쪽 주인공 옆에 앉는다(숯불에서 2m쯤). (경고 오버레이 시작)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S24 · 참고 프레임 S20
- 빛: dusk_embers · 레퍼런스: P, C, COPPER_PAN
- 생성 4s → 사용 구간 0.000–2.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N26` 하루 해와 땔감 더미가 다 들었다.
- 오버레이: `warning_salt` (overlays.json)
- 효과음: 숯불 타닥(작게), 저녁 파도
- 끝 상태(다음 샷의 출발점): 와이드 해 질 녘: 잦아든 숯불 + 큰 재 더미, 땔감 더미는 그을린 끝 2~3개만. 그을린 구리판 솥은 옆 바위, 바람막이 판자 없음. 주인공·고양이 나란히 앉음(숯불 반대편, 2m).

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S24 끝 프레임 · 2) S20 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 COPPER_PAN

```text
Change the camera to a wide view at dusk of the fire hollow and the rock around it: the fire has burned down to a few glowing embers in a big pile of white-grey ash, only two or three charred stave ends lie where the wood pile was, bare open rock stands on the windward side of the three stones, and the copper tray from <IMAGE_4> sits on a rock beside it, its sides streaked black with soot; the figure from <IMAGE_2> sits on the rock beyond the hollow, and the ginger cat from <IMAGE_3> is walking over from the large boulder. Take only the rocks, the large boulder and the fire hollow from <IMAGE_1>; the figure and the cat appear only once, where described here. Keep the dusk light and all designs exactly as in <IMAGE_0>, <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The cat walks around to the figure's side away from the embers and sits down beside it, about two metres from the hollow; a thin wisp of smoke rises from the ash. Static wide camera. It ends with the figure and the cat sitting side by side beyond the dying embers. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_3>; any soot or white crust are exactly as described above. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat walks around to the figure's side away from the embers and sits down beside it, about two metres from the hollow; a thin wisp of smoke rises from the ash. Static wide camera. It ends with the figure and the cat sitting side by side beyond the dying embers. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S26 · COST · 대비 — 전경의 작은 소금, 뒤의 큰 재 더미 · 1:33.42–1:37.27 (3.85s)

**장면** 앵글 컷(로우 클로즈업, 바위 높이). 전경에 소금이 담긴 전복 껍데기(작다, 손바닥 두세 줌), 그 뒤로 불자리의 큰 재 더미가 산처럼 차지한다. 초점이 소금에서 재 더미로 천천히 옮겨 가고 마지막 숯불 하나가 사그라든다. 인물 없음.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S25
- 빛: dusk_embers · 레퍼런스: ABALONE
- 생성 5s → 사용 구간 0.000–3.850s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N27` 소금 한 줌이 장작 한 아름을 먹는다.
- 오버레이: `warning_salt` (overlays.json)
- 효과음: 숯불 사그라드는 소리, 바람
- 끝 상태(다음 샷의 출발점): 로우: 전경 소금 껍데기(초점 밖, 작음), 뒤 큰 재 더미(초점), 마지막 숯불이 꺼져 감. 해 질 녘.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S25 끝 프레임 · 2) 레퍼런스 ABALONE

```text
Change the camera to a low close-up at rock level a moment later: in the near foreground sits the abalone shell from <IMAGE_1> with its small heap of grey salt, sharp and small, and behind it, filling the background softly out of focus, rises the big pile of white-grey ash in the fire hollow with a few faint embers. Keep the dusk light of <IMAGE_0> and the shell exactly as in <IMAGE_1>; only the shell, the salt, the ash and the rock are in this frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. The focus slowly shifts from the small heap of salt in the shell back to the big ash pile behind it, where a last ember fades. Static camera. It ends with the ash pile sharp and the shell of salt soft in the foreground. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_1>; whatever it holds is exactly as described above. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The focus slowly shifts from the small heap of salt in the shell back to the big ash pile behind it, where a last ember fades. Static camera. It ends with the ash pile sharp and the shell of salt soft in the foreground. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S27 · UNLOCK · 소금 껍데기를 손끝으로 톡톡 두 번 (획득 카드) · 1:37.27–1:39.92 (2.65s)

**장면** 클로즈업(손만). 조약돌 두 개 위 전복 껍데기의 회색 소금(구멍 아래 아직 물방울). 첫 1초에 오른손 손끝이 껍데기 가장자리를 두 번 톡톡(습관). 손이 물러나고 물방울 하나가 더 떨어진다. 위쪽 40%는 어두워지는 바위와 하늘뿐(획득 카드 자리).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S26
- 빛: dusk_embers · 레퍼런스: P, ABALONE
- 생성 4s → 사용 구간 0.000–2.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N28` 세 번째 기록. 소금.
- 오버레이: `inventory_unlock` (overlays.json)
- 효과음: 톡톡 2회(껍데기), 물방울 한 번, 국악 타악 1타(획득, 톡톡 0.3초 뒤)
- 끝 상태(다음 샷의 출발점): 전복 껍데기 소금(프레임 아래 절반), 구멍 아래 물방울. 손은 프레임 밖. 위 40% 어두운 바위·하늘.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S26 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 ABALONE

```text
Change the camera to a close-up a moment later of the abalone shell from <IMAGE_2> with its heap of grey salt, resting on two pebbles on the rock, a drop still hanging under one hole, and the matte light-grey porcelain right fingertip of the figure from <IMAGE_1> just above the shell's rim. Frame the shell in the lower half of the frame, with only dim rock and darkening sky in the upper 40% of the frame. Keep the dusk light of <IMAGE_0>; only the hand appears, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 ABALONE

```text
<IMAGE_0> is the first frame. The fingertip taps the shell's rim twice, then the hand draws back and the shell rests still as one more drop falls from beneath it. Static camera. It ends with the shell of salt alone in the lower half of the frame. Pace the action so that this ending is reached at about 2.4 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the abalone shell's ear shape, rough barnacled outside, curved row of holes along its edge and iridescent inside exactly as in <IMAGE_2>; whatever it holds is exactly as described above. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The fingertip taps the shell's rim twice, then the hand draws back and the shell rests still as one more drop falls from beneath it. Static camera. It ends with the shell of salt alone in the lower half of the frame. Pace the action so that this ending is reached at about 2.4 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The abalone shell is a single ear-shaped shell about fourteen centimetres long, rough brown-grey and barnacled outside with a curved row of small open holes along one edge, smooth iridescent mother-of-pearl inside. Photoreal live-action look, late dusk with a fading orange glow low over the sea and the rocks in deep blue shadow, the last embers of the fire glowing faintly, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S28 · NEXT · 해 진 직후 · 꺼진 재, 땔감 없음 · 섬 안쪽으로 고개 · 1:39.92–1:42.87 (2.95s)

**장면** 시간 점프(해가 다 진 직후). 해안을 따라 옆에서 본 와이드(바다 왼쪽·육지 오른쪽, 인물은 옆모습). 불자리의 재에 붉은 기운이 마지막으로 사그라든다. 옆에 그을린 구리판 솥과 소금 껍데기, 땔감 더미는 없고 그을린 통판 끝 2~3개뿐, 아래 물가에 조약돌 얹은 뒤집힌 널빤지. 주인공이 앉아 있고 고양이가 다리에 몸을 붙인다. 주인공이 옆모습인 채 바다(왼쪽)에서 섬 안쪽(오른쪽)으로 고개를 돌리고, 고양이도 같은 쪽으로 고개를 든다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S27 · 참고 프레임 S25
- 빛: after_sunset · 레퍼런스: P, C, COPPER_PAN
- 생성 4s → 사용 구간 0.000–2.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N29` 남은 건 태우지 않을 판자뿐이다.
- 효과음: 저녁 파도, 바람
- 끝 상태(다음 샷의 출발점): 해 진 직후 와이드: 불 꺼진 재, 그을린 구리판 솥·소금 껍데기, 그을린 통판 끝 2~3개뿐, 물가에 뒤집힌 널빤지(조약돌 1개). 주인공: 옆모습, 섬 안쪽(프레임 오른쪽)으로 고개. 고양이: 다리에 붙어 같은 쪽으로 고개. 수평선 마지막 주황 띠.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S27 끝 프레임 · 2) S25 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 COPPER_PAN

```text
Change the time to just after sunset and the camera to a wide shot looking along the shore at the same fire hollow as in <IMAGE_1> (take only the rocks, the large boulder and the fire hollow from it; the figure and the cat appear only once, where described here): the sea with its last thin band of orange is at the left of the frame and the dark land rises at the right; the figure from <IMAGE_2> sits on the rock beside the hollow, seen in profile facing the sea, where only a faint red glow is left in the ash, with the soot-blackened copper tray from <IMAGE_4> and the abalone shell of salt on the rock beside it and only two or three charred stave ends lying beside the ash; below them, near the waterline, lies the dark overturned plank with one pale pebble on it; the ginger cat from <IMAGE_3> sits pressed against the figure's leg. Both are partly silhouetted against the last light. Keep all designs exactly as in <IMAGE_2>, <IMAGE_3> and <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 COPPER_PAN

```text
<IMAGE_0> is the first frame. The last red glow in the ash fades out; the figure's head turns slowly in profile from the sea at the left toward the dark land at the right, and the cat lifts its head the same way. Static wide camera. It ends with the figure's head turned in profile toward the land, held still, the cat against its leg. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the copper tray's size, low bent-up sides, pleated corners, row of empty nail holes along its rims and dull reddish-brown copper exactly as in <IMAGE_3>; any soot or white crust are exactly as described above. Photoreal live-action look, just after sunset, a last thin band of orange on the horizon fading into deep blue, the land dark and the sky still faintly bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The last red glow in the ash fades out; the figure's head turns slowly in profile from the sea at the left toward the dark land at the right, and the cat lifts its head the same way. Static wide camera. It ends with the figure's head turned in profile toward the land, held still, the cat against its leg. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The copper tray is the same thin dull reddish-brown copper sheet bent by hand into a shallow open tray about thirty-five by twenty-five centimetres, with low sloping sides about five centimetres high, rough pleated corners and a row of empty nail holes along the tops of its sides. Photoreal live-action look, just after sunset, a last thin band of orange on the horizon fading into deep blue, the land dark and the sky still faintly bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S29 · NEXT · 어깨 너머 — 섬 안쪽 들판 너머 연기 한 줄 (EP3_END) · 1:42.87–1:47.17 (4.30s)

**장면** 앵글 컷(어깨 너머, 뒤통수만). 해안 뒤 풀밭과 어두운 들판, 낮은 오름 능선 너머, 어두워지는 섬 안쪽 하늘로 회백색 연기 한 줄이 곧게 오른다(누구의 불인지 보이지 않음 — 집·사람·불빛을 그리지 않는다). 천천히 푸시인. 연기는 들판에서 프레임 중앙 조금 위까지(위쪽 엔드카드 자리 비움). (EP3_END → EP.4 S01 C 링크 base)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S28
- 빛: after_sunset · 레퍼런스: P, C
- 생성 6s → 사용 구간 0.000–4.300s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N30` 섬 안쪽 들판 너머로 가는 연기 한 줄이 오른다.
- 효과음: 바람, 먼 풀벌레
- 끝 상태(다음 샷의 출발점): 프레임 중앙: 먼 섬 안쪽 들판 너머 회백색 연기 한 줄(들판에서 프레임 중앙 조금 위까지 — 엔드카드 y300~520과 겹치지 않음). 주인공 뒤통수·고양이는 프레임 아래 가장자리. 해 진 직후. (EP3_END → EP.4 S01 C 링크 base)

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S28 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to an over-the-shoulder view from behind the figure from <IMAGE_1>, its blank head seen only from the back, with the ginger cat from <IMAGE_2> sitting beside it at the bottom edge of the frame, facing inland past the strip of grass behind the shore toward dark fields and the low ridge of a volcanic hill against the fading sky; far away beyond the fields a single thin column of pale grey smoke rises straight up into the dusk, and the land is dark and empty all the way to it. Keep the light and designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The camera pushes in slowly past the figure's shoulder toward the distant column of smoke, which drifts a little at the top as it rises. It ends with the thin column of smoke rising from the dark fields to just above the centre of the frame. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, just after sunset, a last thin band of orange on the horizon fading into deep blue, the land dark and the sky still faintly bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The camera pushes in slowly past the figure's shoulder toward the distant column of smoke, which drifts a little at the top as it rises. It ends with the thin column of smoke rising from the dark fields to just above the centre of the frame. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, just after sunset, a last thin band of orange on the horizon fading into deep blue, the land dark and the sky still faintly bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S30 · TAG · 정지 + 엔드카드 · 1:47.17–1:49.67 (2.50s)

**장면** S29 끝 프레임 정지 + 엔드카드 「표류자 EP.3」 · 기록 03 / ?. 음성 없음, 바람 소리만.

- 연결: **F** 정지 프레임 · 출발 S29
- 빛: — · 레퍼런스: 없음
- 오버레이: `endcard` (overlays.json)
- 효과음: 바람, 먼 파도
- 끝 상태(다음 샷의 출발점): 엔드카드.

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임
