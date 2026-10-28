# 「표류자 EP.1」 바닷가의 민물 — 장면표 · 영상 프롬프트

타이밍 출처: 음절 속도 계획치(TTS 녹음 후 render 재실행 시 실측으로 갱신). 이 파일은 `render`가 생성한다(원본: shots.json).

연결 규칙: 모든 샷은 앞 샷에서 **실제로 쓰는 마지막 프레임**에서 출발한다. C는 그 프레임을 그대로 `image`로 고정하고, A·T는 그 프레임을 이미지 편집해 카메라·시간만 바꾼 뒤 고정한다.

| 샷 | 슬롯 | 화면 | 길이 | 생성 | 연결 | 출발 | 장면 |
|---|---|---|---|---|---|---|---|
| S01 | STATE | 0:00.00–0:04.85 | 4.85s | 6s | K 키프레임 합성 | L01 | 물가에서 깨어나 일어나 앉음 · 고양이가 몸을 턺 |
| S02 | NEED | 0:04.85–0:08.00 | 3.15s | 5s | C 이어가기(앞 끝 프레임 그대로) | S01 | 일어서서 텅 빈 해안을 훑어봄 |
| S03 | NEED | 0:08.00–0:14.95 | 6.95s | 8s | A 앵글 컷(앞 끝 프레임 편집) | S02 | 바닷물을 떠 올렸다가 흘려보냄 |
| S04 | HAVE | 0:14.95–0:20.85 | 5.90s | 7s | A 앵글 컷(앞 끝 프레임 편집) | S03 | 주머니 확인 — 젖은 성냥, 호루라기 |
| S05 | GATHER | 0:20.85–0:23.60 | 2.75s | 4s | C 이어가기(앞 끝 프레임 그대로) | S04 | 고양이가 먼저 바위 쪽으로 감 |
| S06 | GATHER | 0:23.60–0:29.90 | 6.30s | 8s | A 앵글 컷(앞 끝 프레임 편집) | S05 | 젖은 바위틈 냄새 · 구멍 많은 현무암 |
| S08 | FAIL | 0:29.90–0:35.00 | 5.10s | 7s | A 앵글 컷(앞 끝 프레임 편집) | S06 | 틈의 물을 마셨다가 뱉음 — 짜다 |
| S09 | FAIL | 0:35.00–0:37.40 | 2.40s | 4s | C 이어가기(앞 끝 프레임 그대로) | S08 | 파도가 틈을 덮침 — 밀물 |
| S10 | PRINCIPLE | 0:37.40–0:45.13 | 7.74s | 9s | A 앵글 컷(앞 끝 프레임 편집) | S09 | 해안 측면 정렬 구도, 나란히 앉음 (도면) |
| S11 | PRINCIPLE | 0:45.13–0:53.56 | 8.43s | 10s | C 이어가기(앞 끝 프레임 그대로) | S10 | 실시간 이어짐 · 밀물, 꼬리가 팔을 스침 (도면) |
| S11b | PRINCIPLE | 0:53.56–0:57.50 | 3.94s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S11 | 밀물선에 조약돌 놓기 · 잔해 쪽으로 고개 |
| S07 | BUILD | 0:57.50–1:02.05 | 4.55s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S11b +S01 | (인서트) 떠밀려 온 대나무 |
| S12 | BUILD | 1:02.05–1:04.70 | 2.65s | 4s | T 시간 점프(앞 끝 프레임 편집) | S07 | 대나무를 너럭바위로 끌어옴 |
| S13 ★ | BUILD | 1:04.70–1:08.50 | 3.80s | 5s | T 시간 점프(앞 끝 프레임 편집) | S12 | 돌 조각으로 마디 아래에 홈 내기 |
| S14 | BUILD | 1:08.50–1:11.30 | 2.80s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S13 | 꺾기 + 한 뼘 반 재기 |
| S15 | BUILD | 1:11.30–1:13.85 | 2.55s | 4s | T 시간 점프(앞 끝 프레임 편집) | S14 | 완성된 통 몸체 — 바닥은 마디 |
| S16 | BUILD | 1:13.85–1:18.15 | 4.30s | 6s | T 시간 점프(앞 끝 프레임 편집) | S15 | 참나무 조각을 갈아 마개 끼우기 |
| S17 | TEST | 1:18.15–1:21.35 | 3.20s | 5s | T 시간 점프(앞 끝 프레임 편집) | S16 +S08 | 썰물, 틈에서 맑은 물 — 통에 받기 |
| S18 | TEST | 1:21.35–1:23.55 | 2.20s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S17 | 첫 모금은 고양이에게 — 바위 오목에 따라 줌 |
| S18b | TEST | 1:23.55–1:26.15 | 2.60s | 4s | C 이어가기(앞 끝 프레임 그대로) | S18 | 뒤에서 본 채 마심 |
| S19 | COST | 1:26.15–1:29.10 | 2.95s | 4s | T 시간 점프(앞 끝 프레임 편집) | S18b | (인서트) 밀물 첫 물결이 웅덩이에 섞임 |
| S20 | COST | 1:29.10–1:36.05 | 6.95s | 8s | T 시간 점프(앞 끝 프레임 편집) | S18b +S19 | 마개 끼우기 → 풀백, 돌아오는 밀물 (경고) |
| S21 | UNLOCK | 1:36.05–1:39.40 | 3.35s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S20 | 물통 클로즈업 (획득 카드) |
| S22 | NEXT | 1:39.40–1:43.40 | 4.00s | 5s | T 시간 점프(앞 끝 프레임 편집) | S21 +S01 | 해 질 녘, 눅눅한 성냥갑 |
| S23 | NEXT | 1:43.40–1:47.20 | 3.80s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S22 | 널빤지의 쇠못 — 닿기 직전 멈춤 |
| S24 | TAG | 1:47.20–1:49.70 | 2.50s | — | F 정지 프레임 | S23 | 정지 + 엔드카드 |

★ = 히어로 샷(재생성 예산 우선 배정)

---

## S01 · STATE · 물가에서 깨어나 일어나 앉음 · 고양이가 몸을 턺 · 0:00.00–0:04.85 (4.85s)

**장면** 와이드. 현무암 물가에 옆으로 쓰러져 있던 주인공이 팔로 몸을 밀어 일어나 앉는다. 뒤편 널빤지 위의 젖은 고양이가 몸을 털며 일어선다.

- 연결: **K** 키프레임 합성 · 출발 L01
- 빛: morning · 레퍼런스: P, C, PLANK
- 생성 6s → 사용 구간 0.000–4.850s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N01` 바다에 빠진 둘. 깨어난 곳은, 1653년 제주.
- 효과음: 파도(작게 부서짐), 고양이 몸 터는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 물가 바위에 똑바로 앉아 고개가 바다(화면 오른쪽)를 향함. 고양이: 뒤쪽 널빤지 위에 서 있음, 젖은 털.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) L01 레퍼런스 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 PLANK

```text
Place the figure from <IMAGE_1> lying on its right side in the foreground on the wet black basalt at the waterline, across the middle band of <IMAGE_0> (between about 45% and 62% of the frame height), its body spanning about two-thirds of the frame width with its blank head nearest the camera, one arm stretched toward the sea, its orange life vest bright against the dark rock and its trousers soaked; place the ginger cat from <IMAGE_2> sitting on the broken plank from <IMAGE_3>, which lies where the broken plank lies in <IMAGE_0> about two metres behind the figure, clearly visible against the pale sea, fur wet and spiky, looking at the figure. Keep the shoreline, debris, distant mountain, light and framing of <IMAGE_0>, and keep both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. Small waves wash over the lowest rocks. The figure stirs, pushes itself up with both arms and slowly sits up, its head turning toward the open sea; behind it the cat stands up on the plank and shakes the water from its fur. The camera holds the wide shot with only a very slight push-in, so the whole cove, the debris with the plank and the distant mountain stay in frame. It ends with the figure sitting upright on the rocks, still, its head turned toward the sea. Pace the action so that this ending is reached at about 4.5 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Small waves wash over the lowest rocks. The figure stirs, pushes itself up with both arms and slowly sits up, its head turning toward the open sea; behind it the cat stands up on the plank and shakes the water from its fur. The camera holds the wide shot with only a very slight push-in, so the whole cove, the debris with the plank and the distant mountain stay in frame. It ends with the figure sitting upright on the rocks, still, its head turned toward the sea. Pace the action so that this ending is reached at about 4.5 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S02 · NEED · 일어서서 텅 빈 해안을 훑어봄 · 0:04.85–0:08.00 (3.15s)

**장면** 같은 컷 이어서. 주인공이 바위를 짚고 맨발로 일어나 고개를 좌→우로 돌려 텅 빈 해안을 훑고, 발밑 조수 웅덩이 쪽으로 고개를 숙인다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S01
- 빛: morning · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N02` 사방이 바다인데 마실 물이 없다.
- 오버레이: `map_inset` (overlays.json)
- 효과음: 바람, 맨발이 젖은 돌을 딛는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 서서 발밑 조수 웅덩이를 내려다봄. 고양이: 널빤지 위.

**① 시작 프레임** = S01 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the figure rises to its bare feet, one hand on a boulder, and its head turns slowly from left to right along the shoreline, which is empty in both directions. The cat stays on the plank. The camera holds the wide framing with a slight drift to the left. It ends with the figure standing still, head tilted down toward a shallow tide pool at its feet. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the figure rises to its bare feet, one hand on a boulder, and its head turns slowly from left to right along the shoreline, which is empty in both directions. The cat stays on the plank. The camera holds the wide framing with a slight drift to the left. It ends with the figure standing still, head tilted down toward a shallow tide pool at its feet. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S03 · NEED · 바닷물을 떠 올렸다가 흘려보냄 · 0:08.00–0:14.95 (6.95s)

**장면** 로우 사이드 미디엄 클로즈업. 웅덩이 가에 무릎 꿇고 두 손으로 바닷물을 떠 올리다가 머리 앞에서 멈추고, 손가락을 벌려 물을 흘려보낸다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S02
- 빛: morning · 레퍼런스: P
- 생성 8s → 사용 구간 0.000–6.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N03` 물 없이 버티는 건 보통 사흘 안팎. / `N04` 그런데 바닷물은, 마실수록 목이 더 마른다.
- 효과음: 물 뜨는 소리, 손가락 사이로 흘러내리는 물
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 꿇은 채 젖은 손을 내림, 고개 약간 숙임.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S02 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a low side-angle medium close-up of the same place a moment later: the figure from <IMAGE_1> now kneels at the edge of the shallow tide pool with both cupped hands dipped in the seawater at the centre of the frame, just below the middle. Keep the same location, wet rocks, light and soaked outfit as <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The figure lifts its cupped hands full of seawater up close beneath its blank head, stops just short of it and holds for a beat, then slowly opens its fingers and lets the water spill back into the pool. Static camera. It ends with the figure kneeling, hands lowered and dripping, head bowed slightly. Pace the action so that this ending is reached at about 6.7 seconds and then held, almost motionless, until the clip ends at 8 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lifts its cupped hands full of seawater up close beneath its blank head, stops just short of it and holds for a beat, then slowly opens its fingers and lets the water spill back into the pool. Static camera. It ends with the figure kneeling, hands lowered and dripping, head bowed slightly. Pace the action so that this ending is reached at about 6.7 seconds and then held, almost motionless, until the clip ends at 8 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S04 · HAVE · 주머니 확인 — 젖은 성냥, 호루라기 · 0:14.95–0:20.85 (5.90s)

**장면** 정면 미디엄(가슴 높이), 배경 오른쪽에 큰 현무암 바위. 뒤꿈치 위에 앉아 재킷 주머니를 더듬어 눅눅한 성냥갑을 꺼내 연다. 젖어 뭉친 성냥. 어깨끈의 쇠 호루라기를 만진다. (인벤토리 UI가 좌상단에 겹침 — 인물은 중앙 유지)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S03
- 빛: morning · 레퍼런스: P
- 생성 7s → 사용 구간 0.000–5.900s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N05` 가진 건 구명조끼, 젖은 성냥, 호루라기. 그리고 고양이 한 마리.
- 효과음: 젖은 종이갑 여는 소리, 호루라기 금속 딸깍
- 끝 상태(다음 샷의 출발점): 주인공: 뒤꿈치 위 앉음, 오른손 손바닥에 열린 성냥갑, 고개 숙임. 배경 오른쪽에 큰 바위.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S03 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a frontal medium shot at chest height of the same place a moment later: the figure from <IMAGE_1> sits back on its heels beside the tide pool, its body facing the camera and its blank head tilted down toward its hands, with the large black boulders of the cove visible in the background to the right, both hands resting on its orange life vest. Keep the same location, light, soaked outfit and the small steel whistle on the left shoulder strap as in <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 7s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The figure pats the pockets of its navy jacket, pulls a small soggy plain cardboard matchbox from the side pocket and slides it open to show a clump of wet, darkened matches, then touches the steel whistle hanging from its shoulder strap. Static camera with a very slow push-in. It ends with the figure's head tilted down toward the open matchbox in its palm, still. Pace the action so that this ending is reached at about 5.6 seconds and then held, almost motionless, until the clip ends at 7 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure pats the pockets of its navy jacket, pulls a small soggy plain cardboard matchbox from the side pocket and slides it open to show a clump of wet, darkened matches, then touches the steel whistle hanging from its shoulder strap. Static camera with a very slow push-in. It ends with the figure's head tilted down toward the open matchbox in its palm, still. Pace the action so that this ending is reached at about 5.6 seconds and then held, almost motionless, until the clip ends at 7 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S05 · GATHER · 고양이가 먼저 바위 쪽으로 감 · 0:20.85–0:23.60 (2.75s)

**장면** 같은 컷 이어서. 고양이가 주인공 뒤에서 들어와 옆을 스쳐 오른쪽 큰 현무암 바위 쪽으로 걸어간다. 주인공이 성냥갑을 닫고 고개로 따라간다. 카메라가 고양이를 따라 오른쪽으로 팬.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S04
- 빛: morning · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.000–2.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N07` 고양이가 먼저 움직인다.
- 효과음: 고양이 발소리(젖은 돌), 파도
- 끝 상태(다음 샷의 출발점): 고양이: 큰 바위 밑동 한 걸음 앞, 걷는 중. 주인공: 앉은 채 고개를 고양이 쪽으로, 성냥갑 닫음.

**① 시작 프레임** = S04 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the ginger cat, its fur still damp and clumped from the sea, walks into frame from behind the figure, passes close beside it and pads away across the wet rocks toward the right edge of the frame; the figure closes the matchbox and its head turns to follow the cat. The camera pans right with the cat toward the large black boulders already standing at the right of the frame. It ends with the cat still walking, a stride from the foot of the boulders, and the figure's head turned toward it. Pace the action so that this ending is reached at about 2.5 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the ginger cat, its fur still damp and clumped from the sea, walks into frame from behind the figure, passes close beside it and pads away across the wet rocks toward the right edge of the frame; the figure closes the matchbox and its head turns to follow the cat. The camera pans right with the cat toward the large black boulders already standing at the right of the frame. It ends with the cat still walking, a stride from the foot of the boulders, and the figure's head turned toward it. Pace the action so that this ending is reached at about 2.5 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S06 · GATHER · 젖은 바위틈 냄새 · 구멍 많은 현무암 · 0:23.60–0:29.90 (6.30s)

**장면** 로우 매크로. 구멍 숭숭한 현무암 바위 밑동의 젖은 틈. 고양이가 냄새를 맡고 흰 앞발로 한 번 건드린다. 주인공의 손이 들어와 다공질 표면을 손끝으로 쓸어본다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S05
- 빛: morning · 레퍼런스: C, P
- 생성 8s → 사용 구간 0.000–6.300s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N08` 검은 돌, 제주 현무암. / `N09` 구멍과 틈이 많아, 빗물이 잘 스며드는 돌이다.
- 효과음: 물방울 똑똑, 고양이 코 킁킁
- 끝 상태(다음 샷의 출발점): 틈 옆 다공질 바위 위에 주인공 손이 평평하게 놓임. 고양이: 그 옆에 앉음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S05 끝 프레임 · 2) 레퍼런스 C · 3) 레퍼런스 P

```text
Change the camera to a low macro close-up at the foot of the black boulder in <IMAGE_0>: a dark wet crack runs along the base of a vesicular basalt boulder covered in small holes, a thin film of water glistening inside it, and the ginger cat from <IMAGE_1>, its fur still damp and clumped from the sea, crouches with its nose close to the crack. Keep the same light and wet rocks as <IMAGE_0>, and the cat's design exactly as in <IMAGE_1>. The figure from <IMAGE_2> is just out of frame to the left; only the cat, the crack and the rock are in this frame. The pitted rock face fills the middle of the frame and the crack runs across the frame just below the middle.
```

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 C · <IMAGE_2> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The cat sniffs along the wet crack and touches it once with a white front paw, then pulls the paw back, shakes it and steps aside to the right edge of the frame; only then the figure's matte light-grey porcelain hand enters from the left and its fingertips trace the porous, pitted surface of the basalt. Static macro camera. It ends on the hand resting flat on the porous rock beside the crack, the cat sitting at the right edge of the frame. Pace the action so that this ending is reached at about 6.0 seconds and then held, almost motionless, until the clip ends at 8 seconds. Keep the cat exactly as in <IMAGE_1>, moving like a real cat. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_2>; its head stays out of frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat sniffs along the wet crack and touches it once with a white front paw, then pulls the paw back, shakes it and steps aside to the right edge of the frame; only then the figure's matte light-grey porcelain hand enters from the left and its fingertips trace the porous, pitted surface of the basalt. Static macro camera. It ends on the hand resting flat on the porous rock beside the crack, the cat sitting at the right edge of the frame. Pace the action so that this ending is reached at about 6.0 seconds and then held, almost motionless, until the clip ends at 8 seconds. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S08 · FAIL · 틈의 물을 마셨다가 뱉음 — 짜다 · 0:29.90–0:35.00 (5.10s)

**장면** 어깨 너머(뒤통수만 보임). 바위틈 물줄기 아래 두 손을 2초쯤 대고 물을 모은 뒤(N11), 머리 앞으로 가져가 기울이고(N12), 고개를 홱 젖혀 좌우로 흔들며 물을 털어버린다(N13). 고양이가 움찔 물러난다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S06
- 빛: morning · 레퍼런스: P, C
- 생성 7s → 사용 구간 0.000–5.100s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N11` 바위틈에서 물이 배어 나온다. / `N12` 떠서 마신다. / `N13` 짜다.
- 효과음: 물 받는 소리, 퉤 하고 털어내는 물소리(목소리 없음)
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 꿇은 채 바위틈 반대쪽으로 고개 돌림. 고양이: 반 걸음 뒤.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S06 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to an over-the-shoulder view from behind and slightly to the left of the figure from <IMAGE_1>, its blank head seen only from the back, kneeling close to the porous black rock with both cupped hands held under a thin trickle of water seeping from the dark crack; the crack runs diagonally from the lower left toward the centre of the frame, and the ginger cat from <IMAGE_2> sits half a metre to the figure's right. Keep the same boulder, crack, wet rocks and light as <IMAGE_0>, and both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 7s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. Water quickly collects in the figure's cupped hands under the thin trickle; it raises the cupped water up in front of its head, out of the camera's view behind the back of the head, holds a beat, then jerks its head back and flings the water away to the side. The cat flinches and takes a step back. Static camera. It ends with the figure frozen, kneeling, head turned away from the crack. Pace the action so that this ending is reached at about 4.8 seconds and then held, almost motionless, until the clip ends at 7 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Water quickly collects in the figure's cupped hands under the thin trickle; it raises the cupped water up in front of its head, out of the camera's view behind the back of the head, holds a beat, then jerks its head back and flings the water away to the side. The cat flinches and takes a step back. Static camera. It ends with the figure frozen, kneeling, head turned away from the crack. Pace the action so that this ending is reached at about 4.8 seconds and then held, almost motionless, until the clip ends at 7 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S09 · FAIL · 파도가 틈을 덮침 — 밀물 · 0:35.00–0:37.40 (2.40s)

**장면** 같은 컷 이어서. 큰 파도가 낮은 바위를 넘어 흰 거품째 바위틈으로 쏟아진다. 주인공 무릎이 젖고, 고양이는 한 칸 높은 바위로 올라선다(위기 연출 아님).

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S08
- 빛: morning · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.000–2.400s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N14` 지금은, 밀물이다.
- 효과음: 파도 크게 부서짐, 거품 빠지는 소리
- 끝 상태(다음 샷의 출발점): 바위틈에 거품이 소용돌이침(밀물). 주인공: 무릎 꿇음. 고양이: 높은 바위 위.

**① 시작 프레임** = S08 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the cat calmly hops up onto a higher dry rock; a moment later a larger wave surges over the low rocks below it and pours white foam into the crack, wetting the figure's knees while the cat stays dry above. Static camera. It ends with foam swirling in the flooded crack, the figure still kneeling. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the cat calmly hops up onto a higher dry rock; a moment later a larger wave surges over the low rocks below it and pours white foam into the crack, wetting the figure's knees while the cat stays dry above. Static camera. It ends with foam swirling in the flooded crack, the figure still kneeling. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S10 · PRINCIPLE · 해안 측면 정렬 구도, 나란히 앉음 (도면) · 0:37.40–0:45.13 (7.74s)

**장면** 해안선 측면 와이드(바위 꼭대기 높이), 밀물. 수면선 y≈670, 잠긴 틈 x≈716 — 도면의 해수면·출구와 겹친다. 주인공·고양이는 좌상단 바위 위(y300~540 띠, 합친 폭 ≥ 프레임 1/4). 아래 2/3는 비움(도면, 배경 40% 어둡게).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S09
- 빛: morning · 레퍼런스: P, C
- 생성 9s → 사용 구간 0.000–7.739s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N15` 비는 이 돌을 지나 땅속에 고인다. / `N16` 민물은 바닷물보다 약 2.5% 가볍다.
- 오버레이: `diagram_freshwater_lens` (overlays.json)
- 효과음: 파도 베드(낮게), 갈매기 먼 소리
- 끝 상태(다음 샷의 출발점): 만 전경, 밀물. 주인공·고양이 나란히 앉음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S09 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to a side-on view along the shoreline, level with the top of the boulder in <IMAGE_0>, a moment later at high tide: the land and the black porous boulder fill the left two-thirds of the frame and the open sea fills the right third; the waterline crosses the frame horizontally about one third of the way down, and the flooded crack at the foot of the boulder meets the water just right of the centre of the frame. The figure from <IMAGE_1> and the ginger cat from <IMAGE_2> sit side by side on top of the boulder in the upper left, between about a sixth and a quarter of the way down the frame, together spanning about a quarter of the frame width, both heads turned toward the sea. Keep the light as in <IMAGE_0> and both designs exactly as in <IMAGE_1> and <IMAGE_2>. Leave the lower two-thirds of the frame as plain dark wet rock and calm water with nothing else in it.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. Small waves roll in from the right and wash into the flooded crack; the figure and the cat sit still on the boulder, their heads turned toward the sea, and the cat's tail flicks once. Static camera. It ends with the same calm composition. Pace the action so that this ending is reached at about 7.4 seconds and then held, almost motionless, until the clip ends at 9 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Small waves roll in from the right and wash into the flooded crack; the figure and the cat sit still on the boulder, their heads turned toward the sea, and the cat's tail flicks once. Static camera. It ends with the same calm composition. Pace the action so that this ending is reached at about 7.4 seconds and then held, almost motionless, until the clip ends at 9 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S11 · PRINCIPLE · 실시간 이어짐 · 밀물, 꼬리가 팔을 스침 (도면) · 0:45.13–0:53.56 (8.43s)

**장면** 같은 컷 이어서(실시간). 파도가 계속 틈으로 밀려들고, 고양이 꼬리가 한 번 움직여 주인공 팔을 스치고, 주인공 손이 바위 위에서 한 번 옮겨진다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S10
- 빛: morning · 레퍼런스: P, C
- 생성 10s → 사용 구간 0.000–8.426s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N17` 그래서 기름처럼 바닷물 위에 떠, 해안으로 새어 나온다. / `N18` 오늘날 이런 물을 용천수라 부른다.
- 오버레이: `diagram_freshwater_lens` (overlays.json)
- 효과음: 파도 베드(낮게), 바람
- 끝 상태(다음 샷의 출발점): 밀물. 둘이 나란히 앉아 바다를 봄.

**① 시작 프레임** = S10 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 10s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, waves keep washing into the crack; the cat's tail flicks once and brushes the figure's arm, and the figure's hand shifts once on the rock. Static camera. It ends with the two still sitting side by side on the boulder, heads turned toward the sea. Pace the action so that this ending is reached at about 8.1 seconds and then held, almost motionless, until the clip ends at 10 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, waves keep washing into the crack; the cat's tail flicks once and brushes the figure's arm, and the figure's hand shifts once on the rock. Static camera. It ends with the two still sitting side by side on the boulder, heads turned toward the sea. Pace the action so that this ending is reached at about 8.1 seconds and then held, almost motionless, until the clip ends at 10 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S11b · PRINCIPLE · 밀물선에 조약돌 놓기 · 잔해 쪽으로 고개 · 0:53.56–0:57.50 (3.94s)

**장면** 앵글 컷(측면 미디엄). 주인공이 잠긴 틈 옆 바위로 내려와 연한 조약돌 하나를 집어 방금 파도가 닿은 자리에 놓고 앉는다(물때 표시). 고양이는 한 칸 위 바위에서 내려다본다. 끝에 난파 잔해 쪽으로 고개. 도면 없음, 어둡게 안 함.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S11
- 빛: morning · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.944s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N19` 바다가 물러나야, 섬이 물을 내준다.
- 효과음: 파도 베드(낮게), 돌이 돌에 놓이는 소리
- 끝 상태(다음 샷의 출발점): 밀물. 조약돌이 밀물선에 놓임. 주인공: 잔해 쪽으로 고개. 고양이: 한 칸 위 바위.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S11 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to a medium shot from the side, a moment later: the figure from <IMAGE_1> now sits on the rock shelf beside the flooded crack at the foot of the boulder in <IMAGE_0>, a few pale pebbles lying on the rock by its hand, and the ginger cat from <IMAGE_2> sits on a slightly higher rock just behind it, looking down. High tide, the same light as <IMAGE_0>; keep both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure picks up one pale pebble, leans forward and sets it down on the rock exactly where the highest wave has just reached, then sits back; the cat watches the pebble. Static camera. It ends with the figure's head turning toward the shipwreck debris along the shore. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure picks up one pale pebble, leans forward and sets it down on the rock exactly where the highest wave has just reached, then sits back; the cat watches the pebble. Static camera. It ends with the figure's head turning toward the shipwreck debris along the shore. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S07 · BUILD · (인서트) 떠밀려 온 대나무 · 0:57.50–1:02.05 (4.55s)

**장면** 인서트(어깨 너머, 밀물). 잠긴 바위틈 옆에 앉은 주인공의 어깨 너머로 10m 밖 난파 잔해. 바위 사이에 낀 굵은 대나무와 쇠못 널빤지, 위쪽 바위의 고양이. 천천히 대나무로 푸시인.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S11b · 참고 프레임 S01
- 빛: morning · 레퍼런스: P, C, BAMBOO
- 생성 6s → 사용 구간 0.000–4.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N10` 부서진 배 조각 사이, 떠밀려 온 굵은 대나무 한 줄기.
- 효과음: 파도가 잔해 사이로 드나듦
- 끝 상태(다음 샷의 출발점): 프레임 중앙에 대나무 장대, 널빤지와 고양이도 프레임 안. (다음 샷 S12는 이 프레임에서 T 링크)

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S11b 끝 프레임 · 2) S01 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 BAMBOO

```text
Change the camera to an over-the-shoulder view from behind the figure from <IMAGE_2>, now sitting on the rock beside the flooded crack in <IMAGE_0> with the ginger cat from <IMAGE_3> on the boulder above it at the edge of the frame, its head turned back along the shore toward the scattered shipwreck debris of the cove in <IMAGE_1>, about ten metres away: the broken plank with its iron nail lies where it lies in <IMAGE_1>, and the thick weathered bamboo pole from <IMAGE_4> lies wedged between two rocks at the far end of the debris, a few metres beyond the plank. Keep the wet rocks and light of <IMAGE_0>, the debris and shoreline of <IMAGE_1>, and the figure's design exactly as in <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the thick bamboo pole; small waves wash around the planks. It ends with the bamboo pole clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo's colour, white salt stains and node spacing exactly as in <IMAGE_3>. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the thick bamboo pole; small waves wash around the planks. It ends with the bamboo pole clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S12 · BUILD · 대나무를 너럭바위로 끌어옴 · 1:02.05–1:04.70 (2.65s)

**장면** 시간 점프(조금 뒤, 물이 빠지기 시작, 밝아진 오전). 해안 위쪽 평평한 용암 너럭바위. 주인공이 끌어온 굵은 대나무 끝을 툭 내려놓고 옆에 무릎 꿇어 마디 바로 아래에 손을 얹는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S07
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 4s → 사용 구간 0.000–2.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N20` 기다리는 동안 통을 만든다.
- 효과음: 대나무가 돌에 끌리는 소리, 툭 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 너럭바위 위 대나무 옆에 무릎, 손은 마디 바로 아래.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S07 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Change the scene to a medium-wide shot of a flat lava shelf higher up the same shore, a little later: the figure from <IMAGE_1> drags the thick weathered bamboo pole from <IMAGE_2> up onto the flat shelf with both hands. Keep the same coastline and soaked outfit as <IMAGE_0>, with brighter late-morning overcast light, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The figure lets the end of the bamboo pole drop onto the flat rock with a small bounce and kneels beside it, one hand coming to rest on the pole just below a node. The camera follows with a short, steady move. It ends with the figure kneeling, one hand on the bamboo just below the node. Pace the action so that this ending is reached at about 2.4 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the bamboo's colour, white salt stains and node spacing exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lets the end of the bamboo pole drop onto the flat rock with a small bounce and kneels beside it, one hand coming to rest on the pole just below a node. The camera follows with a short, steady move. It ends with the figure kneeling, one hand on the bamboo just below the node. Pace the action so that this ending is reached at about 2.4 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S13 · BUILD · 돌 조각으로 마디 아래에 홈 내기 · 1:04.70–1:08.50 (3.80s)

**장면** 히어로 샷 — 익스트림 클로즈업(몇 분 뒤). 홈은 이미 거의 한 바퀴 파여 있고, 오른손이 현무암 조각으로 마지막 남은 부분을 톱질하듯 긁어 홈을 완성한다. 섬유가 말려 나오고 가루가 검은 돌에 떨어진다. 끝에 조각을 바위에 내려놓는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S12
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 5s → 사용 구간 0.000–3.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N21` 마디 아래를, 돌 조각으로 한 바퀴. 그리고 꺾는다.
- 효과음: 돌이 대나무를 긁는 소리(근접), 가루 떨어짐
- 끝 상태(다음 샷의 출발점): 마디 바로 아래 한 바퀴 홈 완성. 현무암 조각은 바위 위에 내려놓음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S12 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Change the camera to an extreme close-up of the figure's matte light-grey porcelain hands from <IMAGE_1> on the bamboo pole in <IMAGE_0>, a few minutes later: the left hand holds the pole steady on the rock and the right hand holds a sharp, thin flake of black basalt in a pale groove already scored deep most of the way around the bamboo just below a node, a few curled fibres and shavings on the rock. Keep the same bamboo, rock surface and light as <IMAGE_0>. The fingertips and the flake occupy only the lower third of the frame; most of the frame is the groove and the falling shavings.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The right hand saws the basalt flake back and forth in short, firm strokes in the groove while the left hand turns the pole a little, cutting through the last uncut section until the pale groove runs all the way around; thin fibres curl away and fine shavings fall onto the black rock. Static macro camera with shallow depth of field. It ends with a complete pale ring groove around the bamboo and the right hand laying the flake down on the rock. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the bamboo's colour, white salt stains and node spacing exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand saws the basalt flake back and forth in short, firm strokes in the groove while the left hand turns the pole a little, cutting through the last uncut section until the pale groove runs all the way around; thin fibres curl away and fine shavings fall onto the black rock. Static macro camera with shallow depth of field. It ends with a complete pale ring groove around the bamboo and the right hand laying the flake down on the rock. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S14 · BUILD · 꺾기 + 한 뼘 반 재기 · 1:08.50–1:11.30 (2.80s)

**장면** 앵글 컷(한 걸음 뒤 클로즈업). 홈을 너럭바위 모서리에 걸치고 튀어나온 쪽을 눌러 '딱' 꺾는다 — 속이 빈 단면. 이어서 엄지와 가운뎃손가락을 벌려 마디에서 한 뼘 반을 잰다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S13
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 4s → 사용 구간 0.000–2.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N22` 한 뼘 반 위에서 한 번 더.
- 효과음: 대나무 꺾이는 '딱'
- 끝 상태(다음 샷의 출발점): 대나무가 홈에서 꺾여 둘로 나뉨. 펼친 손이 마디에서 한 뼘 반 지점에 놓임.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S13 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Pull the camera back to a close-up a moment later showing both hands from <IMAGE_1> and about sixty centimetres of the bamboo pole from <IMAGE_2>: the fresh pale ring groove, just below a node, sits right over the edge of the lava shelf, the node on the shelf side and the rest of the pole sticking out past the edge, one hand pressing the pole flat on the shelf, the other on the overhanging end, and the basalt flake set down on the rock. Keep the same rock, light and bamboo as <IMAGE_0>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. At once the hand on the overhanging end pushes down hard and the bamboo snaps along the groove at the shelf edge with a crack, showing the hollow inside. That hand then spreads its thumb and middle finger wide and lays one and a half hand-spans along the piece on the shelf, starting from the node at its broken end. Static camera. It ends with the spread hand resting on the bamboo at the measured point. Pace the action so that this ending is reached at about 2.5 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the bamboo's colour, white salt stains and node spacing exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. At once the hand on the overhanging end pushes down hard and the bamboo snaps along the groove at the shelf edge with a crack, showing the hollow inside. That hand then spreads its thumb and middle finger wide and lays one and a half hand-spans along the piece on the shelf, starting from the node at its broken end. Static camera. It ends with the spread hand resting on the bamboo at the measured point. Pace the action so that this ending is reached at about 2.5 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S15 · BUILD · 완성된 통 몸체 — 바닥은 마디 · 1:11.30–1:13.85 (2.55s)

**장면** 시간 점프(몇 분 뒤). 미디엄 클로즈업. 아직 마개 없는 대나무 통(30cm, 아래는 마디로 막힘, 위는 열림)을 가슴 높이로 들어 돌려 보이고 바닥을 두 번 두드린다. 바위 위엔 대나무 자투리.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S14
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 4s → 사용 구간 0.000–2.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N23` 마디가 그대로 바닥이 된다.
- 효과음: 대나무 통 바닥 '톡톡'
- 끝 상태(다음 샷의 출발점): 주인공: 열린 대나무 통을 똑바로 세워 듦(마개 없음).

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S14 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Change the scene to a medium close-up a few minutes later: the figure from <IMAGE_1> kneels on the flat lava shelf, its blank head tilted down toward its hands, holding up at chest height a single bamboo section about 30 cm long cut from the pole in <IMAGE_2>, its natural closed node at the bottom and its cut end at the top open, showing the hollow inside; offcuts of bamboo lie on the rock. Keep the same shelf, light and outfit as <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The figure turns the bamboo section in its hands to show the closed node at the bottom and taps the bottom twice on the rock. Static camera with a slight push-in. It ends with the section held upright, open end at the top. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the bamboo's colour, white salt stains and node spacing exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure turns the bamboo section in its hands to show the closed node at the bottom and taps the bottom twice on the rock. Static camera with a slight push-in. It ends with the section held upright, open end at the top. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S16 · BUILD · 참나무 조각을 갈아 마개 끼우기 · 1:13.85–1:18.15 (4.30s)

**장면** 클로즈업(조금 뒤). 널빤지에서 떼어 내 이미 거의 둥글게 간 참나무 마개를 거친 현무암에 마지막으로 몇 번 더 갈고, 대나무 통 입구에 꾹 눌러 끼운다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S15
- 빛: late_morning · 레퍼런스: P, FLASK
- 생성 6s → 사용 구간 0.000–4.300s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N24` 마개는 배의 나무 조각을 현무암에 갈아 만든다.
- 효과음: 나무를 돌에 가는 소리, 마개 '뽁' 끼우는 소리
- 끝 상태(다음 샷의 출발점): 마개 끼운 대나무 물통이 바위 위에 서 있음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S15 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLASK

```text
Change the camera to a close-up of the figure's matte light-grey porcelain hands from <IMAGE_1>, a little later: one hand presses a small plug of dark weathered ship's oak, already ground nearly round like the plug of the flask in <IMAGE_2>, against the rough black basalt surface with a little fine wood dust around it, and the open bamboo section from <IMAGE_0>, still without any plug, stands upright beside it on the rock. Keep the same rock, light and bamboo section as <IMAGE_0>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The hand gives the oak plug a few last firm strokes back and forth on the rough basalt; then it lifts the plug and presses it firmly into the open end of the bamboo section, where it fits snugly. Static macro camera. It ends with the plugged bamboo flask standing upright on the rock. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_2>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand gives the oak plug a few last firm strokes back and forth on the rough basalt; then it lifts the plug and presses it firmly into the open end of the bamboo section, where it fits snugly. Static macro camera. It ends with the plugged bamboo flask standing upright on the rock. Pace the action so that this ending is reached at about 4.0 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S17 · TEST · 썰물, 틈에서 맑은 물 — 통에 받기 · 1:18.15–1:21.35 (3.20s)

**장면** 시간 점프(몇 시간 뒤, 썰물, 오후). 같은 바위틈(S08 참조). 바다가 멀리 물러나 낮은 바위가 드러났고, 틈에서 맑은 물이 꾸준히 흘러 작은 웅덩이에 고인다. 마개는 웅덩이 옆 바위 위. 주인공이 열린 물통을 물줄기에 대자 기포가 올라오며 찬다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S16 · 참고 프레임 S08
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 5s → 사용 구간 0.000–3.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N25` 물이 빠졌다. / `N26` 같은 틈에서, 다른 물이 나온다.
- 효과음: 졸졸 흐르는 물(근접), 통에 물 차는 꾸르륵
- 끝 상태(다음 샷의 출발점): 주인공: 가득 찬 물통을 들어 올림. 마개는 바위 위. 고양이: 웅덩이 옆.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S16 끝 프레임 · 2) S08 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 FLASK

```text
Change the scene to the same crack at the foot of the boulder shown in <IMAGE_1>, hours later at low tide in warm afternoon light: the sea has drawn far back beyond the lower rocks, which are now exposed and drying, and a steady stream of clear water flows out of the crack into a small rock pool. The figure from <IMAGE_2> kneels at the pool holding the bamboo flask from <IMAGE_4> upright with its open end at the top, its small dark oak plug lying on the rock beside the pool, and the ginger cat from <IMAGE_3> sits beside the pool. The crack runs diagonally from the lower left toward the centre of the frame, and the pale pebble the figure set down at high tide now sits on the dry rock beside the crack, well above the water. Keep the boulder and crack as in <IMAGE_1>, and both designs exactly as in <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure lowers the open bamboo flask into the stream where it leaves the crack; clear water pours in and bubbles rise out of the flask until it overflows. The flask stays open and its oak plug stays lying on the rock. The cat watches the water. Slow push-in. It ends with the figure lifting the full, dripping flask out of the stream. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lowers the open bamboo flask into the stream where it leaves the crack; clear water pours in and bubbles rise out of the flask until it overflows. The flask stays open and its oak plug stays lying on the rock. The cat watches the water. Slow push-in. It ends with the figure lifting the full, dripping flask out of the stream. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S18 · TEST · 첫 모금은 고양이에게 — 바위 오목에 따라 줌 · 1:21.35–1:23.55 (2.20s)

**장면** 뒤쪽 오른쪽 어깨 너머 미디엄 클로즈업. 주인공이 물통을 기울여 앞의 바위 오목에 맑은 물을 조금 따라 주고 세운다. 고양이가 다가와 핥는다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S17
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 4s → 사용 구간 0.000–2.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 효과음: 물 따르는 소리(짧게), 고양이 물 핥는 소리
- 끝 상태(다음 샷의 출발점): 고양이: 오목의 물을 핥는 중. 주인공: 물통을 무릎 위에 세워 듦.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S17 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK

```text
Change the camera to a medium close-up from behind and to the right of the figure, slightly above its shoulder, of the same moment: the figure from <IMAGE_1> kneels at the pool with its back to the camera, its blank head seen only from behind, holding the full open bamboo flask from <IMAGE_3> upright in both hands; a shallow hollow in the flat black rock lies just in front of it, and the ginger cat from <IMAGE_2> sits half a metre away on the far side of the hollow, facing the figure. The oak plug lies on the rock beside the pool. Keep the same place, warm afternoon light and all designs exactly as in <IMAGE_0>, <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure tips the open flask and pours a little clear water into the shallow hollow in the rock in front of the cat, then holds the flask upright again; the cat steps forward, lowers its head and laps from the hollow with small quick movements of its tongue. The oak plug stays on the rock. Static camera. It ends with the cat lapping from the hollow and the figure holding the flask upright on its knee. Pace the action so that this ending is reached at about 1.9 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure tips the open flask and pours a little clear water into the shallow hollow in the rock in front of the cat, then holds the flask upright again; the cat steps forward, lowers its head and laps from the hollow with small quick movements of its tongue. The oak plug stays on the rock. Static camera. It ends with the cat lapping from the hollow and the figure holding the flask upright on its knee. Pace the action so that this ending is reached at about 1.9 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S18b · TEST · 뒤에서 본 채 마심 · 1:23.55–1:26.15 (2.60s)

**장면** 같은 컷 이어서. 고양이는 계속 핥고, 주인공이 물통을 머리 앞쪽(카메라에서는 뒤통수에 가려짐)으로 올려 잠시 멈췄다 무릎에 내려놓는다. 얼굴 요소 없음.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S18
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 4s → 사용 구간 0.000–2.600s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N27` 맑고, 차갑고, 싱겁다.
- 효과음: 꿀꺽(작게, 사람 목소리 아님)
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 위에 열린 물통. 고양이: 오목 옆에 앉음.

**① 시작 프레임** = S18 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
Continuing from <IMAGE_0>, the cat keeps lapping from the hollow; the figure raises the flask until its rim meets the front of its blank head, hidden from the camera behind the back of the head, holds it there for a moment, then lowers the flask to its knee and stays still, shoulders relaxing; the head stays blank throughout. The flask stays open and its oak plug stays on the rock. Static camera. It ends with the flask resting on the figure's knee and the cat sitting up beside the hollow. Pace the action so that this ending is reached at about 2.3 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the cat keeps lapping from the hollow; the figure raises the flask until its rim meets the front of its blank head, hidden from the camera behind the back of the head, holds it there for a moment, then lowers the flask to its knee and stays still, shoulders relaxing; the head stays blank throughout. The flask stays open and its oak plug stays on the rock. Static camera. It ends with the flask resting on the figure's knee and the cat sitting up beside the hollow. Pace the action so that this ending is reached at about 2.3 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S19 · COST · (인서트) 밀물 첫 물결이 웅덩이에 섞임 · 1:26.15–1:29.10 (2.95s)

**장면** 시간 점프(한 시간쯤 뒤, 물때가 바뀜). 로우 앵글 인서트. 용천수 웅덩이의 바다 쪽 가장자리. 돌아오는 밀물의 첫 잔물결이 테두리를 넘어 웅덩이로 흘러들며 맑은 물이 뿌옇게 섞인다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S18b
- 빛: afternoon · 레퍼런스: 없음
- 생성 4s → 사용 구간 0.000–2.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N28` 하지만 밀물이 오면 다시 짜진다.
- 효과음: 잔물결이 넘쳐 드는 소리
- 끝 상태(다음 샷의 출발점): 웅덩이가 바닷물과 섞여 뿌옇게 됨.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S18b 끝 프레임

```text
Change the camera to a low angle right at the seaward rim of the small rock pool in <IMAGE_0>, an hour or so later as the tide turns: the clear spring water fills the pool in the foreground, and beyond the rim the first small wave of the returning tide is sliding up over the exposed rocks toward it. Keep the same rocks as <IMAGE_0>, the warm afternoon sun a little lower; only rock, water and sky in the frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정)

```text
The provided image is the first frame. The small wave slides up, spills over the rim of the pool and pours in, its foam swirling through the clear spring water and clouding it. Static camera at water level. It ends with the pool cloudy and mixed with seawater. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The small wave slides up, spills over the rim of the pool and pours in, its foam swirling through the clear spring water and clouding it. Static camera at water level. It ends with the pool cloudy and mixed with seawater. Pace the action so that this ending is reached at about 2.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S20 · COST · 마개 끼우기 → 풀백, 돌아오는 밀물 (경고) · 1:29.10–1:36.05 (6.95s)

**장면** 미디엄 클로즈업 → 풀백(S19 직후). 무릎 위 물통 입구에 참나무 마개를 꾹 눌러 끼우는 손에서 시작해 천천히 물러나, 마른 바위에 앉은 주인공과 아래 뿌옇게 섞인 웅덩이로 넘치는 잔물결을 보인다. 끝에 고양이가 다리에 몸을 붙인다. (상단 경고 오버레이)

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S18b · 참고 프레임 S19
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 8s → 사용 구간 0.000–6.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N29` 다음 썰물까지, 이 한 통으로 버틴다. / `N30` 끓이지 않은 물은, 언제나 위험하다.
- 오버레이: `warning_boil` (overlays.json)
- 효과음: 마개 꾹 누르는 소리, 먼 파도
- 끝 상태(다음 샷의 출발점): 주인공: 마개 끼운 물통 무릎 위, 밀려오는 물 쪽으로 고개. 고양이: 다리에 몸을 붙임. 밀물 시작.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S18b 끝 프레임 · 2) S19 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 FLASK

```text
Change the camera to a medium close-up from slightly behind and to the side, a little later, just after the moment in <IMAGE_1>: the figure from <IMAGE_2> sits on a dry rock above the pool with the bamboo flask from <IMAGE_4> standing on its knee, one hand holding the flask and the other pressing the oak plug that lay on the rock in <IMAGE_0> into its open end, its head tilted down toward the flask, and the ginger cat from <IMAGE_3> sits beside it; below them the edge of the pool is cloudy with seawater as in <IMAGE_1>. Keep the same place and both designs exactly as in <IMAGE_0>, <IMAGE_2> and <IMAGE_3>, with the warm afternoon sun as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The hand pushes the oak plug firmly home into the flask and rests on it; then the camera slowly pulls back to a medium-wide shot showing the figure sitting above the cloudy pool, small waves of the returning tide spilling over its rim and sliding back, its head turning toward the water; near the end the cat shifts and presses its side against the figure's leg. It ends with the figure sitting still, head turned toward the incoming water, the cat against its leg. Pace the action so that this ending is reached at about 6.7 seconds and then held, almost motionless, until the clip ends at 8 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_3>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand pushes the oak plug firmly home into the flask and rests on it; then the camera slowly pulls back to a medium-wide shot showing the figure sitting above the cloudy pool, small waves of the returning tide spilling over its rim and sliding back, its head turning toward the water; near the end the cat shifts and presses its side against the figure's leg. It ends with the figure sitting still, head turned toward the incoming water, the cat against its leg. Pace the action so that this ending is reached at about 6.7 seconds and then held, almost motionless, until the clip ends at 8 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S21 · UNLOCK · 물통 클로즈업 (획득 카드) · 1:36.05–1:39.40 (3.35s)

**장면** 바위 높이 클로즈업. 젖어 반짝이는 대나무 물통이 평평한 현무암 위에 서 있고, 주인공 손이 막 놓는다. 물방울이 대나무를 타고 흘러 돌을 적신다. 아주 느린 오비트. (인벤토리 카드 +1)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S20
- 빛: afternoon · 레퍼런스: P, FLASK
- 생성 5s → 사용 구간 0.000–3.350s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N31` 첫 번째 기록. 대나무 물통.
- 오버레이: `inventory_unlock` (overlays.json)
- 효과음: 대나무 '톡톡' 2회, 물방울, 국악 타악 1타(획득, 톡톡 0.3초 뒤)
- 끝 상태(다음 샷의 출발점): 대나무 물통 단독 프레임.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S20 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLASK

```text
Change the camera to a close-up at rock level: the plugged bamboo flask from <IMAGE_2>, wet and glistening, stands upright on a flat black basalt rock, the matte light-grey porcelain hand of the figure from <IMAGE_1> just letting go of it, the sea softly out of focus behind. Keep the same warm afternoon light as <IMAGE_0> and the flask's design exactly as in <IMAGE_2>. Frame it so the flask stands in the lower half of the frame, with only soft out-of-focus sea and sky in the upper 40% of the frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The fingertip taps the side of the flask twice, then the hand lets go and withdraws out of frame; a drop of water runs down the bamboo and darkens the rock. Very slow orbit of the camera around the flask. It ends with the flask alone in the frame. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the bamboo flask's bamboo, node, size and dark oak plug exactly as in <IMAGE_2>, with the plug in or out of its open end exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The fingertip taps the side of the flask twice, then the hand lets go and withdraws out of frame; a drop of water runs down the bamboo and darkens the rock. Very slow orbit of the camera around the flask. It ends with the flask alone in the frame. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a removable rough dark oak plug that is in its open end only when described so. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S22 · NEXT · 해 질 녘, 눅눅한 성냥갑 · 1:39.40–1:43.40 (4.00s)

**장면** 시간 점프(해 질 녘). S01의 만, 쇠못 널빤지 옆 와이드(대나무 장대는 이미 없음), 반쯤 실루엣. 주인공이 눅눅한 성냥갑을 뒤집어 보다 흔들고 내린다. 고양이가 다리에 기대 눕는다. 끝에 널빤지 쪽으로 고개를 돌린다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S21 · 참고 프레임 S01
- 빛: dusk · 레퍼런스: P, C, PLANK
- 생성 5s → 사용 구간 0.000–4.000s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N32` 물은 찾았다. / `N33` 오늘 밤도, 끓일 불은 없다.
- 효과음: 저녁 파도, 성냥갑 흔드는 소리(눅눅함)
- 끝 상태(다음 샷의 출발점): 해 질 녘. 주인공: 널빤지 쪽으로 고개. 고양이: 다리에 기대 누움.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S21 끝 프레임 · 2) S01 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 PLANK

```text
Change the scene to dusk at the shipwreck debris of the cove shown in <IMAGE_1>: the sky glows orange low over the sea and the rocks are in cool blue shadow. The broken plank from <IMAGE_4> lies where it is in <IMAGE_1>. The figure from <IMAGE_2> now sits on a rock beside the plank holding the small soggy matchbox, with the plugged bamboo flask from <IMAGE_0> standing at its side, and the ginger cat from <IMAGE_3> sits next to it. Wide shot, both partly silhouetted. Keep the debris and shoreline as in <IMAGE_1>, and both designs exactly as in <IMAGE_2> and <IMAGE_3>. Take only the shoreline and debris from <IMAGE_1>; the figure and the cat each appear only once, where described here.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The cat settles down against the figure's leg; then the figure shakes the soggy matchbox once and lowers it, its head turning toward the broken plank beside it. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turned toward the plank, held still. Pace the action so that this ending is reached at about 3.7 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat settles down against the figure's leg; then the figure shakes the soggy matchbox once and lowers it, its head turning toward the broken plank beside it. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turned toward the plank, held still. Pace the action so that this ending is reached at about 3.7 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S23 · NEXT · 널빤지의 쇠못 — 닿기 직전 멈춤 · 1:43.40–1:47.20 (3.80s)

**장면** 클로즈업 푸시인. 풍화된 참나무 널빤지에 비스듬히 박힌 녹슨 사각 대가리 단조 쇠못이 마지막 주황빛을 받는다. 고양이가 냄새를 맡고 물러나고, 주인공 손이 다가가 닿기 직전 멈춘다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S22
- 빛: dusk · 레퍼런스: P, C, PLANK
- 생성 5s → 사용 구간 0.000–3.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N34` 부서진 널빤지에 쇠못 하나가 박혀 있다.
- 효과음: 저녁 파도(작게), 낮은 앰비언트 음 1개 지속
- 끝 상태(다음 샷의 출발점): 손이 못에 닿기 직전 정지, 못이 프레임 중앙에 선명.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S22 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 PLANK

```text
Change the camera to a close-up of the broken plank from <IMAGE_3> in the dusk light of <IMAGE_0>: a hand-forged square-headed iron nail sticks out of the weathered oak at an angle, rusted orange-brown and catching the last orange light, and the nose of the ginger cat from <IMAGE_2> comes into the edge of the frame. Keep the same dusk light as <IMAGE_0> and the plank exactly as in <IMAGE_3>. The figure from <IMAGE_1> is just out of frame; only the plank, the nail and the cat's nose are in this frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The camera pushes in slowly toward the iron nail; the cat sniffs the rusty nail and pulls back, and the figure's matte light-grey porcelain hand enters, reaches toward the nail and stops just short of touching it. It ends with the hand frozen just short of the nail and the nail sharp in the centre of the frame. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The camera pushes in slowly toward the iron nail; the cat sniffs the rusty nail and pulls back, and the figure's matte light-grey porcelain hand enters, reaches toward the nail and stops just short of touching it. It ends with the hand frozen just short of the nail and the nail sharp in the centre of the frame. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S24 · TAG · 정지 + 엔드카드 · 1:47.20–1:49.70 (2.50s)

**장면** S23 끝 프레임 정지 + 엔드카드 「표류자 EP.1」 · 시즌1. 음성 없음, 파도 소리만.

- 연결: **F** 정지 프레임 · 출발 S23
- 빛: — · 레퍼런스: 없음
- 오버레이: `endcard` (overlays.json)
- 효과음: 파도
- 끝 상태(다음 샷의 출발점): 엔드카드.

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임
