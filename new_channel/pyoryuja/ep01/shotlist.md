# 「표류자 EP.1」 바닷가의 민물 — 장면표 · 영상 프롬프트

타이밍 출처: 음절 속도 계획치(TTS 녹음 후 render 재실행 시 실측으로 갱신). 이 파일은 `render`가 생성한다(원본: shots.json).

연결 규칙: 모든 샷은 앞 샷에서 **실제로 쓰는 마지막 프레임**에서 출발한다. C는 그 프레임을 그대로 `image`로 고정하고, A·T는 그 프레임을 이미지 편집해 카메라·시간만 바꾼 뒤 고정한다.

| 샷 | 슬롯 | 화면 | 길이 | 생성 | 연결 | 출발 | 장면 |
|---|---|---|---|---|---|---|---|
| S01 | STATE | 0:00.00–0:04.85 | 4.85s | 6s | K 키프레임 합성 | L01 | 물가에서 깨어나 일어나 앉음 · 고양이가 몸을 턺 |
| S02 | NEED | 0:04.85–0:08.00 | 3.15s | 5s | C 이어가기(앞 끝 프레임 그대로) | S01 | 일어서서 텅 빈 해안을 훑어봄 |
| S03 | NEED | 0:08.00–0:15.15 | 7.15s | 9s | A 앵글 컷(앞 끝 프레임 편집) | S02 | 바닷물을 떠 올렸다가 흘려보냄 |
| S04 | HAVE | 0:15.15–0:22.40 | 7.25s | 9s | A 앵글 컷(앞 끝 프레임 편집) | S03 | 주머니 확인 — 젖은 성냥, 호루라기 |
| S05 | GATHER | 0:22.40–0:25.15 | 2.75s | 4s | C 이어가기(앞 끝 프레임 그대로) | S04 | 고양이가 먼저 바위 쪽으로 감 |
| S06 | GATHER | 0:25.15–0:31.65 | 6.50s | 8s | A 앵글 컷(앞 끝 프레임 편집) | S05 | 젖은 바위틈 냄새 · 구멍 많은 현무암 |
| S07 | GATHER | 0:31.65–0:36.40 | 4.75s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S06 | (인서트) 떠밀려 온 대나무 |
| S08 | FAIL | 0:36.40–0:41.50 | 5.10s | 7s | A 앵글 컷(앞 끝 프레임 편집) | S06 | 틈의 물을 마셨다가 뱉음 — 짜다 |
| S09 | FAIL | 0:41.50–0:43.90 | 2.40s | 4s | C 이어가기(앞 끝 프레임 그대로) | S08 | 파도가 틈을 덮침 — 밀물 |
| S10 | PRINCIPLE | 0:43.90–0:51.42 | 7.52s | 9s | A 앵글 컷(앞 끝 프레임 편집) | S09 | 만 전경, 나란히 앉음 (도면) |
| S11 | PRINCIPLE | 0:51.42–1:02.92 | 11.50s | 13s | C 이어가기(앞 끝 프레임 그대로) | S10 | 구름이 걷히고 물이 빠지기 시작 (도면) |
| S12 | BUILD | 1:02.92–1:05.57 | 2.65s | 4s | T 시간 점프(앞 끝 프레임 편집) | S11 | 대나무를 너럭바위로 끌어옴 |
| S13 ★ | BUILD | 1:05.57–1:09.17 | 3.60s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S12 | 돌 조각으로 마디 아래에 홈 내기 |
| S14 | BUILD | 1:09.17–1:12.17 | 3.00s | 5s | C 이어가기(앞 끝 프레임 그대로) | S13 | 꺾기 + 한 뼘 반 재기 |
| S15 | BUILD | 1:12.17–1:14.72 | 2.55s | 4s | T 시간 점프(앞 끝 프레임 편집) | S14 | 완성된 통 몸체 — 바닥은 마디 |
| S16 | BUILD | 1:14.72–1:18.62 | 3.90s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S15 | 참나무 조각을 갈아 마개 끼우기 |
| S17 | TEST | 1:18.62–1:22.82 | 4.20s | 6s | T 시간 점프(앞 끝 프레임 편집) | S16 +S08 | 썰물, 틈에서 맑은 물 — 통에 받기 |
| S18 | TEST | 1:22.82–1:25.52 | 2.70s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S17 | 마심 · 고양이도 핥음 |
| S19 | COST | 1:25.52–1:28.47 | 2.95s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S18 | (인서트) 밀물 첫 물결이 웅덩이에 섞임 |
| S20 | COST | 1:28.47–1:35.62 | 7.15s | 9s | A 앵글 컷(앞 끝 프레임 편집) | S18 | 물통을 무릎에 두고 돌아오는 바다를 봄 (경고) |
| S21 | UNLOCK | 1:35.62–1:38.42 | 2.80s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S20 | 물통 클로즈업 (획득 카드) |
| S22 | NEXT | 1:38.42–1:42.22 | 3.80s | 5s | T 시간 점프(앞 끝 프레임 편집) | S21 +S07 | 해 질 녘, 눅눅한 성냥갑 |
| S23 | NEXT | 1:42.22–1:46.22 | 4.00s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S22 | 널빤지의 쇠못 — 닿기 직전 멈춤 |
| S24 | TAG | 1:46.22–1:49.22 | 3.00s | — | F 정지 프레임 | S23 | 정지 + 엔드카드 |

★ = 히어로 샷(재생성 예산 우선 배정)

---

## S01 · STATE · 물가에서 깨어나 일어나 앉음 · 고양이가 몸을 턺 · 0:00.00–0:04.85 (4.85s)

**장면** 와이드. 현무암 물가에 옆으로 쓰러져 있던 주인공이 팔로 몸을 밀어 일어나 앉는다. 뒤편 널빤지 위의 젖은 고양이가 몸을 털며 일어선다.

- 연결: **K** 키프레임 합성 · 출발 L01
- 빛: morning · 레퍼런스: P, C
- 생성 6s → 사용 구간 0.000–4.850s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N01` 바다에 빠졌다. 깨어난 곳은, 1653년 제주.
- 효과음: 파도(작게 부서짐), 고양이 몸 터는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 물가 바위에 똑바로 앉아 바다(화면 오른쪽)를 봄. 고양이: 뒤쪽 널빤지 위에 서 있음, 젖은 털.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) L01 레퍼런스 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Place the figure from <IMAGE_1> lying on its right side on the wet black basalt rocks at the waterline in the lower middle of <IMAGE_0>, one arm stretched toward the sea, its orange life vest bright against the dark rock and its trousers soaked; place the ginger cat from <IMAGE_2> sitting on the broken plank about two metres behind the figure, fur wet and spiky, looking at the figure. Keep the shoreline, debris, distant mountain, light and framing of <IMAGE_0>, and keep both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. Small waves wash over the lowest rocks. The figure stirs, pushes itself up with both arms and slowly sits up, its head turning toward the open sea; behind it the cat stands up on the plank and shakes the water from its fur. Slow, steady push-in from the wide shot toward the figure. It ends with the figure sitting upright on the rocks, still, looking out to sea. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Small waves wash over the lowest rocks. The figure stirs, pushes itself up with both arms and slowly sits up, its head turning toward the open sea; behind it the cat stands up on the plank and shakes the water from its fur. Slow, steady push-in from the wide shot toward the figure. It ends with the figure sitting upright on the rocks, still, looking out to sea. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S02 · NEED · 일어서서 텅 빈 해안을 훑어봄 · 0:04.85–0:08.00 (3.15s)

**장면** 같은 컷 이어서. 주인공이 맨발로 비틀거리며 일어나 바위를 짚고, 고개를 좌→우로 돌려 텅 빈 해안을 훑는다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S01
- 빛: morning · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.042–3.192s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N02` 이 바위 해안에 닿은 건 둘뿐이다.
- 효과음: 바람, 맨발이 젖은 돌을 딛는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 서서 발밑 조수 웅덩이를 내려다봄. 고양이: 널빤지 위.

**① 시작 프레임** = S01 승인 클립의 끝 프레임 그대로(편집 없음). 첫 1프레임은 중복이라 버린다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the figure gets to its bare feet unsteadily, steadies itself with one hand on a boulder, and turns its head slowly from left to right, scanning the empty shoreline; there is no one else anywhere along the coast. The cat stays on the plank. The camera holds the wide framing with a slight drift to the left. It ends with the figure standing still, facing a shallow tide pool at its feet. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the figure gets to its bare feet unsteadily, steadies itself with one hand on a boulder, and turns its head slowly from left to right, scanning the empty shoreline; there is no one else anywhere along the coast. The cat stays on the plank. The camera holds the wide framing with a slight drift to the left. It ends with the figure standing still, facing a shallow tide pool at its feet. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S03 · NEED · 바닷물을 떠 올렸다가 흘려보냄 · 0:08.00–0:15.15 (7.15s)

**장면** 로우 사이드 미디엄 클로즈업. 웅덩이 가에 무릎 꿇고 두 손으로 바닷물을 떠 올리다가 머리 앞에서 멈추고, 손가락을 벌려 물을 흘려보낸다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S02
- 빛: morning · 레퍼런스: P
- 생성 9s → 사용 구간 0.000–7.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N03` 물 없이 버티는 건, 보통 사흘 안팎. / `N04` 그런데 바닷물은, 마실수록 목이 더 마른다.
- 효과음: 물 뜨는 소리, 손가락 사이로 흘러내리는 물
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 꿇은 채 젖은 손을 내림, 고개 약간 숙임.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S02 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a low side-angle medium close-up of the same place a moment later: the figure from <IMAGE_1> now kneels at the edge of the shallow tide pool with both cupped hands dipped in the seawater. Keep the same location, wet rocks, light and soaked outfit as <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The figure lifts its cupped hands full of seawater toward the lower front of its smooth head, stops just before touching it and holds for a beat, then slowly opens its fingers and lets the water spill back into the pool. Static camera. It ends with the figure kneeling, hands lowered and dripping, head bowed slightly. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lifts its cupped hands full of seawater toward the lower front of its smooth head, stops just before touching it and holds for a beat, then slowly opens its fingers and lets the water spill back into the pool. Static camera. It ends with the figure kneeling, hands lowered and dripping, head bowed slightly. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S04 · HAVE · 주머니 확인 — 젖은 성냥, 호루라기 · 0:15.15–0:22.40 (7.25s)

**장면** 정면 미디엄(가슴 높이). 뒤꿈치 위에 앉아 조끼 주머니를 더듬어 눅눅한 성냥갑을 꺼내 연다. 젖어 뭉친 성냥. 어깨끈의 쇠 호루라기를 만진다. (인벤토리 UI가 좌상단에 겹침 — 인물은 중앙 유지)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S03
- 빛: morning · 레퍼런스: P
- 생성 9s → 사용 구간 0.000–7.250s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N05` 가진 건 이게 전부다. / `N06` 구명조끼, 젖은 성냥, 호루라기. 그리고 고양이 한 마리.
- 효과음: 젖은 종이갑 여는 소리, 호루라기 금속 딸깍
- 끝 상태(다음 샷의 출발점): 주인공: 뒤꿈치 위 앉음, 오른손 손바닥에 열린 성냥갑, 시선 아래.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S03 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a frontal medium shot at chest height of the same place a moment later: the figure from <IMAGE_1> sits back on its heels beside the tide pool, facing the camera, both hands resting on its orange life vest. Keep the same location, light, soaked outfit and the small steel whistle on the left shoulder strap as in <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The figure pats the pockets of its life vest, pulls a small soggy plain cardboard matchbox from the right chest pocket and slides it open to show a clump of wet, darkened matches, then touches the steel whistle hanging from its shoulder strap. Static camera with a very slow push-in. It ends with the figure looking down at the open matchbox in its palm, still. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure pats the pockets of its life vest, pulls a small soggy plain cardboard matchbox from the right chest pocket and slides it open to show a clump of wet, darkened matches, then touches the steel whistle hanging from its shoulder strap. Static camera with a very slow push-in. It ends with the figure looking down at the open matchbox in its palm, still. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S05 · GATHER · 고양이가 먼저 바위 쪽으로 감 · 0:22.40–0:25.15 (2.75s)

**장면** 같은 컷 이어서. 고양이가 주인공 뒤에서 들어와 옆을 스쳐 오른쪽 큰 현무암 바위 쪽으로 걸어가 멈추고 뒤돌아본다. 주인공이 성냥갑을 닫고 고개로 따라간다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S04
- 빛: morning · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.042–2.792s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N07` 고양이가 먼저 움직인다.
- 효과음: 고양이 발소리(젖은 돌), 파도
- 끝 상태(다음 샷의 출발점): 고양이: 큰 바위 밑에서 뒤돌아봄. 주인공: 앉은 채 고양이 쪽을 봄, 성냥갑 닫음.

**① 시작 프레임** = S04 승인 클립의 끝 프레임 그대로(편집 없음). 첫 1프레임은 중복이라 버린다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the ginger cat walks into frame from behind the figure, passes close beside it and pads across the wet rocks toward the large black boulders on the right, then stops and looks back over its shoulder. The figure closes the matchbox and turns its head to follow the cat. The camera pans slightly right with the cat. It ends with the cat standing still at the foot of the boulders, looking back, and the figure looking toward it. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the ginger cat walks into frame from behind the figure, passes close beside it and pads across the wet rocks toward the large black boulders on the right, then stops and looks back over its shoulder. The figure closes the matchbox and turns its head to follow the cat. The camera pans slightly right with the cat. It ends with the cat standing still at the foot of the boulders, looking back, and the figure looking toward it. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S06 · GATHER · 젖은 바위틈 냄새 · 구멍 많은 현무암 · 0:25.15–0:31.65 (6.50s)

**장면** 로우 매크로. 구멍 숭숭한 현무암 바위 밑동의 젖은 틈. 고양이가 냄새를 맡고 흰 앞발로 한 번 건드린다. 주인공의 손이 들어와 다공질 표면을 손끝으로 쓸어본다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S05
- 빛: morning · 레퍼런스: C, P
- 생성 8s → 사용 구간 0.000–6.500s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N08` 검은 돌, 제주 현무암. / `N09` 구멍이 숭숭 뚫려, 빗물이 그대로 스며드는 돌이다.
- 효과음: 물방울 똑똑, 고양이 코 킁킁
- 끝 상태(다음 샷의 출발점): 틈 옆 다공질 바위 위에 주인공 손이 평평하게 놓임. 고양이: 그 옆에 앉음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S05 끝 프레임 · 2) 레퍼런스 C · 3) 레퍼런스 P

```text
Change the camera to a low macro close-up at the foot of the black boulder in <IMAGE_0>: a dark wet crack runs along the base of a vesicular basalt boulder covered in small holes, a thin film of water glistening inside it, and the ginger cat from <IMAGE_1> crouches with its nose close to the crack. Keep the same light and wet rocks as <IMAGE_0>, and the cat's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 C · <IMAGE_2> 레퍼런스 P

```text
<IMAGE_0> is the first frame. The cat sniffs along the wet crack and touches it once with a white front paw, then pulls the paw back and shakes it. The figure's matte light-grey porcelain hand enters from the left and its fingertips trace the porous, pitted surface of the basalt. Very slow camera slide to the right along the rock. It ends on the hand resting flat on the porous rock beside the crack, the cat sitting next to it. Keep the cat exactly as in <IMAGE_1>, moving like a real cat. Keep the figure exactly as in <IMAGE_2>; its head stays a smooth, featureless matte porcelain egg in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat sniffs along the wet crack and touches it once with a white front paw, then pulls the paw back and shakes it. The figure's matte light-grey porcelain hand enters from the left and its fingertips trace the porous, pitted surface of the basalt. Very slow camera slide to the right along the rock. It ends on the hand resting flat on the porous rock beside the crack, the cat sitting next to it. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S07 · GATHER · (인서트) 떠밀려 온 대나무 · 0:31.65–0:36.40 (4.75s)

**장면** 인서트(어깨 너머). 바위 밑에 무릎 꿇은 주인공의 어깨 너머로 10m 밖 난파 잔해. 바위 사이에 낀 굵은 대나무와 고양이가 앉아 있던 널빤지. 천천히 대나무로 푸시인.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S06
- 빛: morning · 레퍼런스: P, BAMBOO, PLANK
- 생성 6s → 사용 구간 0.000–4.750s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N10` 부서진 배 조각 사이, 떠밀려 온 굵은 대나무 한 줄기.
- 효과음: 파도가 잔해 사이로 드나듦
- 끝 상태(다음 샷의 출발점): 프레임 중앙에 대나무 장대. (컷어웨이 — 다음 샷은 S06 끝 프레임에서 이어짐)

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S06 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO · 4) 레퍼런스 PLANK

```text
Change the camera to an over-the-shoulder view from behind the figure from <IMAGE_1>, now kneeling at the foot of the boulder in <IMAGE_0>, looking back along the shore toward the scattered shipwreck debris about ten metres away: the thick weathered bamboo pole from <IMAGE_2> lies wedged between two rocks beside the broken plank from <IMAGE_3>. Keep the same location, wet rocks and light as <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The figure's head turns toward the debris and the camera pushes in slowly past its shoulder toward the thick bamboo pole; small waves wash around the planks. It ends with the bamboo pole clearly visible in the middle of the frame. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo exactly as in <IMAGE_2>. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure's head turns toward the debris and the camera pushes in slowly past its shoulder toward the thick bamboo pole; small waves wash around the planks. It ends with the bamboo pole clearly visible in the middle of the frame. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S08 · FAIL · 틈의 물을 마셨다가 뱉음 — 짜다 · 0:36.40–0:41.50 (5.10s)

**장면** 사이드 미디엄. 바위틈에 무릎 꿇고 배어 나오는 물을 두 손으로 받아 머리 앞으로 가져갔다가, 고개를 홱 젖히고 좌우로 흔들며 물을 털어버린다. 고양이가 움찔 물러난다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S06
- 빛: morning · 레퍼런스: P, C
- 생성 7s → 사용 구간 0.000–5.100s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N11` 바위틈에서 물이 배어 나온다. / `N12` 떠서 마신다. / `N13` 짜다.
- 효과음: 물 받는 소리, 퉤 하고 털어내는 물소리(목소리 없음)
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 꿇은 채 바다 쪽으로 고개 돌림. 고양이: 반 걸음 뒤.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S06 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to a side medium shot at the foot of the boulder: the figure from <IMAGE_1> kneels close to the porous black rock with both cupped hands held under a thin trickle of water seeping from the dark crack, and the ginger cat from <IMAGE_2> sits half a metre behind it. Keep the same boulder, crack, wet rocks and light as <IMAGE_0>, and both designs exactly as in <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 7s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure brings its cupped hands of water up to the lower front of its smooth head, then jerks its head back sharply, shakes it from side to side and flings the water away, wiping its hand on its jacket. The cat flinches and takes a step back. Static camera. It ends with the figure frozen, kneeling, head turned toward the sea behind it. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure brings its cupped hands of water up to the lower front of its smooth head, then jerks its head back sharply, shakes it from side to side and flings the water away, wiping its hand on its jacket. The cat flinches and takes a step back. Static camera. It ends with the figure frozen, kneeling, head turned toward the sea behind it. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S09 · FAIL · 파도가 틈을 덮침 — 밀물 · 0:41.50–0:43.90 (2.40s)

**장면** 같은 컷 이어서. 큰 파도가 낮은 바위를 넘어 흰 거품째 바위틈으로 밀려든다. 주인공 무릎이 젖고, 고양이는 마른 바위 위로 가볍게 뛰어오른다(위기 연출 아님).

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S08
- 빛: morning · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.042–2.442s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N14` 지금은, 밀물이다.
- 효과음: 파도 크게 부서짐, 거품 빠지는 소리
- 끝 상태(다음 샷의 출발점): 바위틈이 바닷물로 차 있음. 주인공: 무릎 꿇고 틈을 봄. 고양이: 마른 바위 위.

**① 시작 프레임** = S08 승인 클립의 끝 프레임 그대로(편집 없음). 첫 1프레임은 중복이라 버린다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, a larger wave surges up over the low rocks and washes white foam right into the crack at the foot of the boulder, soaking the figure's knees; the figure leans back on one hand and the cat hops calmly up onto a dry rock. Static camera. It ends with the foam draining away and seawater filling the crack, the figure still kneeling and looking at it. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, a larger wave surges up over the low rocks and washes white foam right into the crack at the foot of the boulder, soaking the figure's knees; the figure leans back on one hand and the cat hops calmly up onto a dry rock. Static camera. It ends with the foam draining away and seawater filling the crack, the figure still kneeling and looking at it. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S10 · PRINCIPLE · 만 전경, 나란히 앉음 (도면) · 0:43.90–0:51.42 (7.52s)

**장면** 하이 와이드(8m 위 경사면). 밀물이 낮은 바위를 덮은 만 전체. 주인공과 고양이는 물가 위 마른 바위에 나란히 앉아 바다를 본다. 아주 느린 크레인 다운. 화면 중·상단을 비워 도면 오버레이 자리 확보(배경 40% 어둡게).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S09
- 빛: morning · 레퍼런스: P, C
- 생성 9s → 사용 구간 0.000–7.522s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N15` 비는 이 돌을 지나 땅속에 고인다. / `N16` 민물은 바닷물보다 2.5퍼센트 가볍다.
- 오버레이: `diagram_freshwater_lens` (overlays.json)
- 효과음: 파도 베드(낮게), 갈매기 먼 소리
- 끝 상태(다음 샷의 출발점): 만 전경, 밀물. 주인공·고양이 나란히 앉음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S09 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to a high wide shot of the whole cove in <IMAGE_0>, seen from about eight metres up the slope: the sea is at high tide covering the lower rocks, and the figure from <IMAGE_1> sits on a dry boulder above the waterline near the crack with the ginger cat from <IMAGE_2> sitting beside it. Keep the same shoreline, debris, light and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>. Leave the upper and middle part of the frame calm and uncluttered.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. Waves roll in slowly and wash over the low rocks; the figure and the cat sit still, watching the sea, and the cat's tail flicks once. Very slow, steady downward crane of the camera. It ends with the same calm composition. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Waves roll in slowly and wash over the low rocks; the figure and the cat sit still, watching the sea, and the cat's tail flicks once. Very slow, steady downward crane of the camera. It ends with the same calm composition. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, soft grey overcast morning light after rain, wet glistening rocks, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S11 · PRINCIPLE · 구름이 걷히고 물이 빠지기 시작 (도면) · 0:51.42–1:02.92 (11.50s)

**장면** 같은 컷 이어서. 구름이 갈라지며 햇빛이 번지고, 파도가 약해지며 물선이 물러나 젖은 바위가 드러나기 시작한다. 끝에 주인공이 난파 잔해 쪽으로 고개를 돌린다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S10
- 빛: late_morning · 레퍼런스: P, C
- 생성 13s → 사용 구간 0.042–11.542s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N17` 그래서 바닷물 위에 떠서, 해안으로 새어 나온다. / `N18` 오늘날 이런 물을 용천수라 부른다. / `N19` 조건은 하나. 바다가 물러난 시간.
- 오버레이: `diagram_freshwater_lens` (overlays.json)
- 효과음: 파도 약해짐, 바람 잦아듦
- 끝 상태(다음 샷의 출발점): 물이 빠지기 시작. 주인공: 잔해 쪽으로 고개 돌림.

**① 시작 프레임** = S10 승인 클립의 끝 프레임 그대로(편집 없음). 첫 1프레임은 중복이라 버린다.

**② 영상** (`grok-imagine-video-1.5`, 13s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the clouds slowly part and soft sunlight spreads across the cove; the waves gradually lose strength and the waterline begins to retreat, revealing wet rocks. The figure and the cat remain seated. The camera continues its very slow downward crane. It ends with the figure turning its head toward the shipwreck debris. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the clouds slowly part and soft sunlight spreads across the cove; the waves gradually lose strength and the waterline begins to retreat, revealing wet rocks. The figure and the cat remain seated. The camera continues its very slow downward crane. It ends with the figure turning its head toward the shipwreck debris. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S12 · BUILD · 대나무를 너럭바위로 끌어옴 · 1:02.92–1:05.57 (2.65s)

**장면** 시간 점프(조금 뒤). 해안 위쪽 평평한 용암 너럭바위. 주인공이 굵은 대나무 장대를 두 손으로 끌어 올려 내려놓고, 무릎 꿇고 마디까지 손으로 훑는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S11
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 4s → 사용 구간 0.000–2.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N20` 기다리는 동안 통을 만든다.
- 효과음: 대나무가 돌에 끌리는 소리, 툭 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 너럭바위 위 대나무 옆에 무릎, 손은 마디 바로 아래.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S11 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Change the scene to a medium-wide shot of a flat lava shelf higher up the same shore, a little later: the figure from <IMAGE_1> drags the thick weathered bamboo pole from <IMAGE_2> up onto the flat shelf with both hands. Keep the same coastline and soaked outfit as <IMAGE_0>, with brighter late-morning overcast light, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The figure hauls the bamboo pole the last metre onto the flat rock, lets it drop with a small bounce, kneels beside it and runs one hand along it to a node. The camera follows with a short, steady move. It ends with the figure kneeling, one hand on the bamboo just below a node. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure hauls the bamboo pole the last metre onto the flat rock, lets it drop with a small bounce, kneels beside it and runs one hand along it to a node. The camera follows with a short, steady move. It ends with the figure kneeling, one hand on the bamboo just below a node. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S13 · BUILD · 돌 조각으로 마디 아래에 홈 내기 · 1:05.57–1:09.17 (3.60s)

**장면** 히어로 샷 — 익스트림 클로즈업. 왼손은 대나무를 굴리고, 오른손은 얇고 날카로운 현무암 조각으로 마디 바로 아래를 빙 둘러 긁어 옅은 홈을 낸다. 섬유가 말려 나오고 가루가 검은 돌에 떨어진다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S12
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 5s → 사용 구간 0.000–3.600s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N21` 돌 조각으로 마디 바로 아래를 빙 둘러 긁고, 꺾는다.
- 효과음: 돌이 대나무를 긁는 소리(근접), 가루 떨어짐
- 끝 상태(다음 샷의 출발점): 마디 바로 아래 한 바퀴 홈 완성. 두 손이 대나무 위.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S12 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 BAMBOO

```text
Change the camera to an extreme close-up of the figure's matte light-grey porcelain hands from <IMAGE_1> on the bamboo pole in <IMAGE_0>: the left hand holds the pole steady on the rock and the right hand grips a sharp, thin flake of black basalt pressed against the bamboo just below a node. Keep the same bamboo, rock surface and light as <IMAGE_0>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
<IMAGE_0> is the first frame. The right hand draws the basalt flake firmly around the bamboo just below the node while the left hand rolls the pole, cutting a pale shallow groove all the way around; thin fibres curl away and fine dust falls onto the black rock. Static macro camera with shallow depth of field. It ends with a complete pale ring groove around the bamboo. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand draws the basalt flake firmly around the bamboo just below the node while the left hand rolls the pole, cutting a pale shallow groove all the way around; thin fibres curl away and fine dust falls onto the black rock. Static macro camera with shallow depth of field. It ends with a complete pale ring groove around the bamboo. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S14 · BUILD · 꺾기 + 한 뼘 반 재기 · 1:09.17–1:12.17 (3.00s)

**장면** 같은 컷 이어서. 홈 양쪽을 잡고 바위 모서리에 대고 꺾자 '딱' 하고 깔끔하게 부러진다. 이어서 손바닥을 펴 엄지와 가운뎃손가락으로 한 뼘 반을 잰다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S13
- 빛: late_morning · 레퍼런스: P, BAMBOO
- 생성 5s → 사용 구간 0.042–3.042s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N22` 한 뼘 반 위에서 한 번 더.
- 효과음: 대나무 꺾이는 '딱'
- 끝 상태(다음 샷의 출발점): 대나무가 홈에서 꺾여 둘로 나뉨. 펼친 손이 마디에서 한 뼘 반 지점에 놓임.

**① 시작 프레임** = S13 승인 클립의 끝 프레임 그대로(편집 없음). 첫 1프레임은 중복이라 버린다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 BAMBOO

```text
Continuing from <IMAGE_0>, the hands set the flake down, grip the bamboo on both sides of the groove and bend it sharply over the edge of the rock; it cracks cleanly along the groove and snaps in two, showing the hollow inside. Then one hand spreads its thumb and middle finger wide and measures one and a half hand-spans up the pole from the node. Static camera. It ends with the spread hand resting on the bamboo at the measured point. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the hands set the flake down, grip the bamboo on both sides of the groove and bend it sharply over the edge of the rock; it cracks cleanly along the groove and snaps in two, showing the hollow inside. Then one hand spreads its thumb and middle finger wide and measures one and a half hand-spans up the pole from the node. Static camera. It ends with the spread hand resting on the bamboo at the measured point. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo pole is about six centimetres thick, pale green-yellow with white salt stains and nodes every thirty centimetres. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S15 · BUILD · 완성된 통 몸체 — 바닥은 마디 · 1:12.17–1:14.72 (2.55s)

**장면** 시간 점프(몇 분 뒤). 미디엄 클로즈업. 마개 없는 대나무 통(30cm, 아래는 마디로 막힘)을 가슴 높이로 들고 돌려 보이며 바닥을 두 번 두드리고, 잘린 테두리를 현무암에 문질러 다듬는다. 바위 위엔 대나무 자투리.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S14
- 빛: late_morning · 레퍼런스: P, FLASK
- 생성 4s → 사용 구간 0.000–2.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N23` 마디가 그대로 바닥이 된다.
- 효과음: 대나무 통 바닥 '톡톡', 테두리 문지르는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 마개 없는 대나무 통을 똑바로 세워 듦.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S14 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLASK

```text
Change the scene to a medium close-up a few minutes later: the figure from <IMAGE_1> kneels on the flat lava shelf holding up, at chest height, a single finished bamboo section shaped like the flask in <IMAGE_2> but without its plug, about 30 cm long, with the natural closed node at the bottom and the open cut rim at the top; offcuts of bamboo lie on the rock. Keep the same shelf, light and outfit as <IMAGE_0>, and the figure's design exactly as in <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure slowly turns the bamboo section in its hands to show the closed node at the bottom, taps the bottom twice on the rock, then rubs the cut rim smooth against the rough basalt. Static camera with a slight push-in. It ends with the figure holding the section upright, rim at the top. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo flask exactly as in <IMAGE_2>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure slowly turns the bamboo section in its hands to show the closed node at the bottom, taps the bottom twice on the rock, then rubs the cut rim smooth against the rough basalt. Static camera with a slight push-in. It ends with the figure holding the section upright, rim at the top. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S16 · BUILD · 참나무 조각을 갈아 마개 끼우기 · 1:14.72–1:18.62 (3.90s)

**장면** 클로즈업. 널빤지에서 떼어 낸 참나무 조각을 거친 현무암에 앞뒤로 갈아 둥근 마개로 만들고, 대나무 통 입구에 꾹 눌러 끼운다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S15
- 빛: late_morning · 레퍼런스: P, FLASK, PLANK
- 생성 5s → 사용 구간 0.000–3.900s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N24` 마개는 배의 나무 조각을 현무암에 갈아서.
- 효과음: 나무를 돌에 가는 소리, 마개 '뽁' 끼우는 소리
- 끝 상태(다음 샷의 출발점): 마개 끼운 대나무 물통이 바위 위에 서 있음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S15 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLASK · 4) 레퍼런스 PLANK

```text
Change the camera to a close-up of the figure's matte light-grey porcelain hands from <IMAGE_1>: one hand presses a small splinter of dark oak, broken from the plank in <IMAGE_3>, against the rough black basalt surface, and the open bamboo section from <IMAGE_0> stands upright beside it on the rock. Keep the same rock, light and bamboo section as <IMAGE_0>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLASK · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The hand grinds the oak splinter back and forth on the rough basalt, rounding it into a small plug as fine wood dust gathers; then it lifts the plug and presses it firmly into the open mouth of the bamboo section, where it fits snugly. Static macro camera. It ends with the plugged bamboo flask standing upright on the rock. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo flask exactly as in <IMAGE_2>. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand grinds the oak splinter back and forth on the rough basalt, rounding it into a small plug as fine wood dust gathers; then it lifts the plug and presses it firmly into the open mouth of the bamboo section, where it fits snugly. Static macro camera. It ends with the plugged bamboo flask standing upright on the rock. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, brighter overcast late-morning light with the clouds beginning to break, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S17 · TEST · 썰물, 틈에서 맑은 물 — 통에 받기 · 1:18.62–1:22.82 (4.20s)

**장면** 시간 점프(몇 시간 뒤, 썰물, 오후). 같은 바위틈(S08 참조). 바다가 멀리 물러나 낮은 바위가 드러났고, 틈에서 맑은 물이 꾸준히 흘러 작은 웅덩이에 고인다. 주인공이 마개 뺀 물통을 물줄기에 대자 기포가 올라오며 찬다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S16 · 참고 프레임 S08
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 6s → 사용 구간 0.000–4.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N25` 물이 빠졌다. / `N26` 같은 틈에서, 다른 물이 나온다.
- 효과음: 졸졸 흐르는 물(근접), 통에 물 차는 꾸르륵
- 끝 상태(다음 샷의 출발점): 주인공: 가득 찬 물통을 들어 올림. 고양이: 웅덩이 옆.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S16 끝 프레임 · 2) S08 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 FLASK

```text
Change the scene to the same crack at the foot of the boulder shown in <IMAGE_1>, hours later at low tide in warm afternoon light: the sea has drawn far back beyond the lower rocks, which are now exposed and drying, and a steady stream of clear water flows out of the crack into a small rock pool. The figure from <IMAGE_2> kneels at the pool holding the bamboo flask from <IMAGE_4> with its plug removed, and the ginger cat from <IMAGE_3> sits beside the pool. Keep the boulder and crack as in <IMAGE_1>, the flask as in <IMAGE_0>, and both designs exactly as in <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure lowers the open bamboo flask into the stream at the mouth of the crack; clear water pours in and bubbles rise out of the flask until it overflows. The cat watches the water. Slow push-in. It ends with the figure lifting the full, dripping flask out of the stream. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask exactly as in <IMAGE_3>. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lowers the open bamboo flask into the stream at the mouth of the crack; clear water pours in and bubbles rise out of the flask until it overflows. The cat watches the water. Slow push-in. It ends with the figure lifting the full, dripping flask out of the stream. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S18 · TEST · 마심 · 고양이도 핥음 · 1:22.82–1:25.52 (2.70s)

**장면** 좌전방 미디엄 클로즈업. 물통을 머리 아래 앞쪽에 대고 천천히 마신 뒤 내려놓고, 어깨가 풀린다. 옆에서 고양이가 웅덩이 물을 핥는다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S17
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 4s → 사용 구간 0.000–2.700s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N27` 맑고, 차갑고, 싱겁다.
- 효과음: 꿀꺽(작게, 사람 목소리 아님), 고양이 물 핥는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 위에 물통. 고양이: 웅덩이 물 핥는 중.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S17 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK

```text
Change the camera to a medium close-up from the front-left of the same moment: the figure from <IMAGE_1> kneels by the pool holding the full bamboo flask from <IMAGE_3> near the lower front of its smooth head, and the ginger cat from <IMAGE_2> crouches at the edge of the pool with its head lowered to the water. Keep the same place, warm afternoon light and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The figure tilts the bamboo flask so its rim rests against the smooth lower front of its head and drinks slowly, then lowers the flask and stays still for a moment, shoulders relaxing. Beside it the cat laps water from the pool with small quick movements of its tongue. Static camera. It ends with the figure resting the flask on its knee. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask exactly as in <IMAGE_3>. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure tilts the bamboo flask so its rim rests against the smooth lower front of its head and drinks slowly, then lowers the flask and stays still for a moment, shoulders relaxing. Beside it the cat laps water from the pool with small quick movements of its tongue. Static camera. It ends with the figure resting the flask on its knee. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S19 · COST · (인서트) 밀물 첫 물결이 웅덩이에 섞임 · 1:25.52–1:28.47 (2.95s)

**장면** 로우 앵글 인서트. 용천수 웅덩이의 바다 쪽 가장자리. 돌아오는 밀물의 첫 잔물결이 테두리를 넘어 웅덩이로 흘러들며 맑은 물이 뿌옇게 섞인다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S18
- 빛: afternoon · 레퍼런스: 없음
- 생성 4s → 사용 구간 0.000–2.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N28` 하지만 밀물이 오면 다시 짜진다.
- 효과음: 잔물결이 넘쳐 드는 소리
- 끝 상태(다음 샷의 출발점): 웅덩이가 바닷물과 섞여 뿌옇게 됨.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S18 끝 프레임

```text
Change the camera to a low angle right at the seaward rim of the small rock pool in <IMAGE_0>: the clear spring water fills the pool in the foreground, and beyond the rim the first small wave of the returning tide is sliding up over the exposed rocks toward it. Keep the same rocks and warm afternoon light as <IMAGE_0>; no figure or cat in the frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정)

```text
<IMAGE_0> is the first frame. The small wave slides up, spills over the rim of the pool and pours in, its foam swirling through the clear spring water and clouding it. Static camera at water level. It ends with the pool cloudy and mixed with seawater. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The small wave slides up, spills over the rim of the pool and pours in, its foam swirling through the clear spring water and clouding it. Static camera at water level. It ends with the pool cloudy and mixed with seawater. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S20 · COST · 물통을 무릎에 두고 돌아오는 바다를 봄 (경고) · 1:28.47–1:35.62 (7.15s)

**장면** 미디엄 와이드. 주인공이 마른 바위에 기대앉아 물통을 무릎에 올리고 돌아오는 바다를 본다. 고양이는 앞발을 핥는다. 천천히 풀백. (상단 경고 오버레이)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S18
- 빛: afternoon · 레퍼런스: P, C, FLASK
- 생성 9s → 사용 구간 0.000–7.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N29` 하루 두 번, 물때를 외워야 한다. / `N30` 그리고 끓이지 않은 물은, 언제나 위험하다.
- 오버레이: `warning_boil` (overlays.json)
- 효과음: 먼 파도, 고양이 핥는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 물통을 무릎에 올리고 바다를 봄. 고양이: 옆에 앉음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S18 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 FLASK

```text
Change the camera to a medium-wide shot from slightly behind and to the side, a minute later: the figure from <IMAGE_1> sits back on a dry rock above the pool with the plugged bamboo flask from <IMAGE_3> on its knee, gazing at the sea, and the ginger cat from <IMAGE_2> sits beside it. Keep the same place, warm afternoon light and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. Far out, a line of small waves creeps back toward the exposed rocks as the tide turns; the figure sits still, watching it, and the cat licks its white front paw. The camera slowly pulls back. It ends with the figure sitting still, watching the returning water. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the bamboo flask exactly as in <IMAGE_3>. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Far out, a line of small waves creeps back toward the exposed rocks as the tide turns; the figure sits still, watching it, and the cat licks its white front paw. The camera slowly pulls back. It ends with the figure sitting still, watching the returning water. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S21 · UNLOCK · 물통 클로즈업 (획득 카드) · 1:35.62–1:38.42 (2.80s)

**장면** 바위 높이 클로즈업. 젖어 반짝이는 대나무 물통이 평평한 현무암 위에 서 있고, 주인공 손이 막 놓는다. 물방울이 대나무를 타고 흘러 돌을 적신다. 아주 느린 오비트. (인벤토리 카드 +1)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S20
- 빛: afternoon · 레퍼런스: P, FLASK
- 생성 4s → 사용 구간 0.000–2.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N31` 첫 번째 물건. 대나무 물통.
- 오버레이: `inventory_unlock` (overlays.json)
- 효과음: 물방울, 국악 타악 1타(획득)
- 끝 상태(다음 샷의 출발점): 대나무 물통 단독 프레임.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S20 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLASK

```text
Change the camera to a close-up at rock level: the plugged bamboo flask from <IMAGE_2>, wet and glistening, stands upright on a flat black basalt rock, the matte light-grey porcelain hand of the figure from <IMAGE_1> just letting go of it, the sea softly out of focus behind. Keep the same warm afternoon light as <IMAGE_0> and the flask's design exactly as in <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLASK

```text
<IMAGE_0> is the first frame. The hand lets go of the flask and withdraws out of frame; a drop of water runs down the bamboo and darkens the rock. Very slow orbit of the camera around the flask. It ends with the flask alone in the frame. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the bamboo flask exactly as in <IMAGE_2>. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand lets go of the flask and withdraws out of frame; a drop of water runs down the bamboo and darkens the rock. Very slow orbit of the camera around the flask. It ends with the flask alone in the frame. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The bamboo flask is a single thirty-centimetre bamboo section closed at the bottom by its node, with a rough dark oak plug. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the rocks drying, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S22 · NEXT · 해 질 녘, 눅눅한 성냥갑 · 1:38.42–1:42.22 (3.80s)

**장면** 시간 점프(해 질 녘). 난파 잔해(S07 참조) 와이드, 반쯤 실루엣. 주인공이 널빤지 옆 바위에 앉아 눅눅한 성냥갑을 뒤집어 보다 흔들고 내린다. 고양이가 다리에 기대 눕는다. 끝에 널빤지 쪽으로 고개를 돌린다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S21 · 참고 프레임 S07
- 빛: dusk · 레퍼런스: P, C, PLANK
- 생성 5s → 사용 구간 0.000–3.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N32` 물은 해결됐다. / `N33` 오늘 밤도, 불은 없다.
- 오버레이: `map_inset` (overlays.json)
- 효과음: 저녁 파도, 성냥갑 흔드는 소리(눅눅함)
- 끝 상태(다음 샷의 출발점): 해 질 녘. 주인공: 널빤지 쪽으로 고개. 고양이: 다리에 기대 누움.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S21 끝 프레임 · 2) S07 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 PLANK

```text
Change the scene to dusk at the shipwreck debris shown in <IMAGE_1>: the sky glows orange low over the sea and the rocks are in cool blue shadow; the figure from <IMAGE_2> sits on a rock beside the broken plank from <IMAGE_4>, holding the small soggy matchbox, with the plugged bamboo flask from <IMAGE_0> at its side, and the ginger cat from <IMAGE_3> sits next to it. Wide shot, both partly silhouetted. Keep the debris layout as in <IMAGE_1> and both designs exactly as in <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The figure turns the soggy matchbox over in its fingers, shakes it once and lowers it; the cat stretches and lies down against the figure's leg. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turning toward the broken plank beside it. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure turns the soggy matchbox over in its fingers, shakes it once and lowers it; the cat stretches and lies down against the figure's leg. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turning toward the broken plank beside it. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S23 · NEXT · 널빤지의 쇠못 — 닿기 직전 멈춤 · 1:42.22–1:46.22 (4.00s)

**장면** 클로즈업 푸시인. 풍화된 참나무 널빤지에 비스듬히 박힌 녹슨 사각 대가리 단조 쇠못이 마지막 주황빛을 받는다. 고양이가 냄새를 맡고 물러나고, 주인공 손이 다가가 닿기 직전 멈춘다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S22
- 빛: dusk · 레퍼런스: P, C, PLANK
- 생성 5s → 사용 구간 0.000–4.000s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N34` 부서진 널빤지에, 쇠못 하나가 박혀 있다.
- 효과음: 저녁 파도(작게), 낮은 앰비언트 음 1개 지속
- 끝 상태(다음 샷의 출발점): 손이 못에 닿기 직전 정지, 못이 프레임 중앙에 선명.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S22 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 PLANK

```text
Change the camera to a close-up of the broken plank from <IMAGE_3> in the dusk light of <IMAGE_0>: a hand-forged square-headed iron nail sticks out of the weathered oak at an angle, rusted orange-brown and catching the last orange light, and the nose of the ginger cat from <IMAGE_2> comes into the edge of the frame. Keep the same dusk light as <IMAGE_0> and the plank exactly as in <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK

```text
<IMAGE_0> is the first frame. The camera pushes in slowly toward the iron nail; the cat sniffs the rusty nail and pulls back, and the figure's matte light-grey porcelain hand enters, reaches toward the nail and stops just short of touching it. It ends with the hand frozen just short of the nail and the nail sharp in the centre of the frame. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, featureless matte porcelain egg in every frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The camera pushes in slowly toward the iron nail; the cat sniffs the rusty nail and pulls back, and the figure's matte light-grey porcelain hand enters, reaches toward the nail and stops just short of touching it. It ends with the hand frozen just short of the nail and the nail sharp in the centre of the frame. The figure has a large smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S24 · TAG · 정지 + 엔드카드 · 1:46.22–1:49.22 (3.00s)

**장면** S23 끝 프레임 정지 + 엔드카드 「표류자 EP.1」 · 시즌1. 음성 없음, 파도 소리만.

- 연결: **F** 정지 프레임 · 출발 S23
- 빛: — · 레퍼런스: 없음
- 오버레이: `endcard` (overlays.json)
- 효과음: 파도
- 끝 상태(다음 샷의 출발점): 엔드카드.

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임
