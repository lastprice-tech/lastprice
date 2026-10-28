# 「표류자 EP.2」 못 하나로 불 — 장면표 · 영상 프롬프트

타이밍 출처: 음절 속도 계획치(TTS 녹음 후 render 재실행 시 실측으로 갱신). 이 파일은 `render`가 생성한다(원본: shots.json).

연결 규칙: 모든 샷은 앞 샷에서 **실제로 쓰는 마지막 프레임**에서 출발한다. C는 그 프레임을 그대로 `image`로 고정하고, A·T는 그 프레임을 이미지 편집해 카메라·시간만 바꾼 뒤 고정한다.

| 샷 | 슬롯 | 화면 | 길이 | 생성 | 연결 | 출발 | 장면 |
|---|---|---|---|---|---|---|---|
| S01 | STATE | 0:00.00–0:03.05 | 3.05s | 5s | C 이어가기(앞 끝 프레임 그대로) | EP1_END | EP.1 끝 프레임에서 그대로 — 쇠못을 쥐고 당김, 꿈쩍 않음 |
| S02 | NEED | 0:03.05–0:07.70 | 4.65s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S01 | 널빤지를 뒤집음 — 아랫면의 거친 홈(F1 심기) |
| S03 | NEED | 0:07.70–0:10.90 | 3.20s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S02 | 못 끝을 돌로 쳐 되밀기 (전경에 홈) |
| S04 | HAVE | 0:10.90–0:16.55 | 5.65s | 7s | T 시간 점프(앞 끝 프레임 편집) | S02 | 다음 날 아침 · 뽑아 낸 쇠못을 손바닥에 (인벤토리) |
| S05 | GATHER | 0:16.55–0:18.60 | 2.05s | 4s | T 시간 점프(앞 끝 프레임 편집) | S04 | 해안 뒤 풀밭의 쑥 — 큰 잎만 훑어 딴다 |
| S06 | GATHER | 0:18.60–0:22.40 | 3.80s | 5s | T 시간 점프(앞 끝 프레임 편집) | S05 | 볕에 달군 너럭바위 — 고양이가 먼저 누워 있음 |
| S07 | GATHER | 0:22.40–0:25.90 | 3.50s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S06 | 고양이 옆에 잎을 펼치고 조약돌로 눌러 둠 |
| S08 | FAIL | 0:25.90–0:30.85 | 4.95s | 6s | T 시간 점프(앞 끝 프레임 편집) | S07 | 현무암 모서리에 못을 내리침 — 돌이 부스러짐 |
| S09 | FAIL | 0:30.85–0:33.00 | 2.15s | 4s | C 이어가기(앞 끝 프레임 그대로) | S08 | 한 번 더 — 불티 없음, 손을 내림 |
| S10 | PRINCIPLE | 0:33.00–0:40.92 | 7.92s | 9s | T 시간 점프(앞 끝 프레임 편집) | S09 | 측면 정렬 구도 · 바위 위에서 쇠못을 들어 봄 (도면) |
| S11 | PRINCIPLE | 0:40.92–0:49.28 | 8.36s | 10s | C 이어가기(앞 끝 프레임 그대로) | S10 | 실시간 이어짐 · 고양이가 고개를 듦 (도면) |
| S12 | PRINCIPLE | 0:49.28–0:52.69 | 3.41s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S11 | 일어서서 난파 잔해 쪽으로 고개 (귀에 남는 문장) |
| S13 | BUILD | 0:52.69–0:56.34 | 3.65s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S12 | (재료 인서트) 배 밑바닥 잔해에 낀 흰 돌 |
| S14 | BUILD | 0:56.34–0:58.69 | 2.35s | 4s | T 시간 점프(앞 끝 프레임 편집) | S13 | 흰 돌을 깨서 유리 같은 날 세우기 |
| S15 | BUILD | 0:58.69–1:02.14 | 3.45s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S14 | 실패한 현무암에 못의 녹을 갈아 냄 (숫돌) |
| S16 | BUILD | 1:02.14–1:05.99 | 3.85s | 5s | T 시간 점프(앞 끝 프레임 편집) | S15 +S07 | 반나절 뒤 — 바삭해진 쑥잎을 비벼 솜을 얻음 |
| S17 | BUILD | 1:05.99–1:09.34 | 3.35s | 5s | T 시간 점프(앞 끝 프레임 편집) | S16 | 불 받을 둥지와 잔가지를 미리 준비 |
| S18 | BUILD | 1:09.34–1:13.84 | 4.50s | 6s | A 앵글 컷(앞 끝 프레임 편집) | S17 | 조선식 쥐기 — 돌 위에 쑥 솜, 못으로 날을 긁어 내림 |
| S19 | TEST | 1:13.84–1:18.84 | 5.00s | 6s | T 시간 점프(앞 끝 프레임 편집) | S17 | 한참 뒤 — 치고 또 침, 불티는 몇 번에 한 번 |
| S20 | TEST | 1:18.84–1:22.39 | 3.55s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S19 | 불티가 솜에 떨어져도 꺼짐 — 볶지 못한 쑥 |
| S20b | TEST | 1:22.39–1:26.29 | 3.90s | 5s | C 이어가기(앞 끝 프레임 그대로) | S20 | 불티가 솜에 박힘 — 주황 점이 번짐 |
| S21 ★ | TEST | 1:26.29–1:32.44 | 6.15s | 8s | A 앵글 컷(앞 끝 프레임 편집) | S20b +S19 | 둥지에 감싸 흔들어 바람을 먹임 → 불꽃 (실시간 히어로) |
| S22 | COST | 1:32.44–1:35.69 | 3.25s | 5s | C 이어가기(앞 끝 프레임 그대로) | S21 | 작은 불 · 따뜻한 자리를 고양이에게(관계 비트) · 바다 쪽 소나기 구름 |
| S23 | COST | 1:35.69–1:38.29 | 2.60s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S22 | 고양이가 먼저 바위 밑으로 · 굵은 빗방울 · 몸을 숙여 불을 가림 |
| S24 | COST | 1:38.29–1:40.69 | 2.40s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S23 | 불꽃이 몇 초에 걸쳐 낮아지다 꺼짐 · 남은 쑥 솜도 젖음 |
| S25 | UNLOCK | 1:40.69–1:43.14 | 2.45s | 4s | A 앵글 컷(앞 끝 프레임 편집) | S24 | 빗속, 손바닥 위 쇠못과 흰 돌 — 톡톡 두 번 (획득 카드) |
| S26 | NEXT | 1:43.14–1:46.39 | 3.25s | 5s | T 시간 점프(앞 끝 프레임 편집) | S25 +S23 | 비 갠 해 질 녘 · 꺼진 불자리 · 고양이가 나와 다리에 붙음 · 널빤지 쪽으로 고개 |
| S27 | NEXT | 1:46.39–1:49.59 | 3.20s | 5s | A 앵글 컷(앞 끝 프레임 편집) | S26 | 널빤지 아랫면 — 빗물 고인 홈이 또렷해짐 (EP2_END) |
| S28 | TAG | 1:49.59–1:52.09 | 2.50s | — | F 정지 프레임 | S27 | 정지 + 엔드카드 |

★ = 히어로 샷(재생성 예산 우선 배정)

---

## S01 · STATE · EP.1 끝 프레임에서 그대로 — 쇠못을 쥐고 당김, 꿈쩍 않음 · 0:00.00–0:03.05 (3.05s)

**장면** EP.1 마지막 프레임(해 질 녘, 손이 쇠못에 닿기 직전)에서 편집 없이 이어서. 손이 녹슨 사각 대가리를 감싸 쥐고 두 번 세게 당긴다. 못은 물 먹은 참나무에서 빠지지 않는다. 손만 보인다. (QC: EP1_END 프레임 가장자리에 고양이 코가 남아 있으면 refs에 C를 추가하고 'the cat's nose stays at the edge of the frame'을 prompt에 넣는다)

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 EP1_END
- 빛: dusk · 레퍼런스: P, PLANK
- 생성 5s → 사용 구간 0.000–3.050s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N01` 물은 찾았다. 남은 건 쇠못 하나.
- 오버레이: `ref_chip` (overlays.json)
- 효과음: 저녁 파도(작게), 손이 녹슨 쇠를 쥐는 마찰음, 젖은 나무가 버티는 삐걱
- 끝 상태(다음 샷의 출발점): 손: 못 대가리를 쥔 채 정지(손·팔뚝만). 못: 널빤지에 비스듬히 박힌 그대로, 프레임 중앙. 해 질 녘 주황 역광. 고양이: 프레임 밖(EP.1 S23에서 물러남).

**① 시작 프레임** = EP1_END(이전 회차) 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 PLANK

```text
Continuing from <IMAGE_0>, the hand closes around the rusty square head of the nail and pulls hard, once and then a second time, the fingers straining; the nail stays fixed in the oak. Static close-up. It ends with the hand still gripping the nail head, the nail unmoved in the centre of the frame. Pace the action so that this ending is reached at about 2.8 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the plank and its iron nail exactly as in <IMAGE_2>. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the hand closes around the rusty square head of the nail and pulls hard, once and then a second time, the fingers straining; the nail stays fixed in the oak. Static close-up. It ends with the hand still gripping the nail head, the nail unmoved in the centre of the frame. Pace the action so that this ending is reached at about 2.8 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S02 · NEED · 널빤지를 뒤집음 — 아랫면의 거친 홈(F1 심기) · 0:03.05–0:07.70 (4.65s)

**장면** 앵글 컷(측면 미디엄, 널빤지 높이, 옆에서 든 마지막 주황빛에 흰 머리·주황 조끼·주황 고양이가 또렷). 비스듬히 박힌 못은 위에서 뽑을 수 없어, 주인공이 두 손으로 널빤지 가장자리를 들어 뒤집는다. 젖어 더 어두운 아랫면에 못 끝이 삐져나와 있고, 그 옆에 해초에 반쯤 가린 거친 홈 몇 줄(F1 — 읽을 수 없음, 설명 없음). 고개가 홈 쪽으로 숙여지고 한 손이 그 옆에 멈춘다. 고양이는 뒤쪽 한 칸 위 바위.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S01
- 빛: dusk · 레퍼런스: P, C, PLANK, PLANK_UNDER
- 생성 6s → 사용 구간 0.000–4.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N02` 불이 있어야 물을 끓인다. 1분은 팔팔 끓여야 한다.
- 효과음: 널빤지가 돌 위로 뒤집히는 둔탁한 소리, 젖은 해초 소리, 낮은 앰비언트 음 1개(홈이 보일 때)
- 끝 상태(다음 샷의 출발점): 널빤지: 두 바위 사이에 걸쳐 뒤집힘(아래쪽 못 대가리는 허공), 아랫면이 위(못 끝이 삐져나옴, 홈은 해초에 반쯤 가림). 주인공: 그 옆에 무릎, 고개를 홈 쪽으로 숙임, 한 손은 홈 옆. 고양이: 뒤쪽 한 칸 위 바위. 해 질 녘.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S01 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 PLANK · 5) 레퍼런스 PLANK_UNDER

```text
Change the camera to a medium side view of the same place a moment later, at the height of the plank: the figure from <IMAGE_1> kneels on the dark rocks beside the broken plank from <IMAGE_3>, both hands gripping the plank's near edge, the rusty nail still sticking up out of its top side, and the ginger cat from <IMAGE_2> sits on a higher rock a metre behind. Keep the dusk light of <IMAGE_0>, the last low orange light from the side catching the figure's pale porcelain head and orange life vest and the cat's ginger fur, bright against the darkening blue rocks, and all designs exactly as in <IMAGE_1>, <IMAGE_2> and <IMAGE_3>; the plank's underside, turned down against the rock for now, is the one in <IMAGE_4>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK · <IMAGE_4> 레퍼런스 PLANK_UNDER

```text
<IMAGE_0> is the first frame. The figure lifts the plank by its near edge and turns it over onto two rocks, so that it lands bridging the gap between them with its darker, wet underside facing up, where the pointed tip of the nail pokes through and, beside it, a short row of rough shallow grooves lies half hidden under strands of seaweed. The figure's head bows toward the grooves and one hand comes to rest beside them. Static camera. It ends with the figure kneeling still beside the overturned plank, its head bowed toward the grooves. Pace the action so that this ending is reached at about 4.4 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank and its iron nail exactly as in <IMAGE_3>. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_4>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure lifts the plank by its near edge and turns it over onto two rocks, so that it lands bridging the gap between them with its darker, wet underside facing up, where the pointed tip of the nail pokes through and, beside it, a short row of rough shallow grooves lies half hidden under strands of seaweed. The figure's head bows toward the grooves and one hand comes to rest beside them. Static camera. It ends with the figure kneeling still beside the overturned plank, its head bowed toward the grooves. Pace the action so that this ending is reached at about 4.4 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The plank is broken weathered dark oak with seaweed on it and one rusty hand-forged square-headed iron nail sticking out at an angle. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S03 · NEED · 못 끝을 돌로 쳐 되밀기 (전경에 홈) · 0:07.70–0:10.90 (3.20s)

**장면** 로우 클로즈업(손만). 전경에 해초에 반쯤 가린 홈(초점, 읽을 수 없음), 그 너머로 오른손이 주먹만 한 현무암 덩이로 삐져나온 못 끝을 짧게 여러 번 쳐서 나무 속으로 되민다(반대쪽 대가리가 올라와 뽑힌다 — 실제 5~20분 걸리는 일이라 다음 컷은 시간 점프). (널빤지가 두 바위 사이에 걸쳐 있어 아래쪽 못 대가리가 허공에 뜬다)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S02
- 빛: dusk · 레퍼런스: P, PLANK_UNDER
- 생성 5s → 사용 구간 0.000–3.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N03` 널빤지 아랫면에 거친 홈이 나 있다.
- 효과음: 돌로 쇠를 치는 '탁탁', 파도(작게)
- 끝 상태(다음 샷의 출발점): 못 끝이 나무 속으로 거의 평평하게 되밀림. 손: 현무암 덩이를 널빤지 위에 내려놓은 채(손만). 전경에 홈. 해 질 녘 막바지.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S02 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 PLANK_UNDER

```text
Change the camera to a low close-up across the underside of the overturned plank from <IMAGE_2>, a moment later: the rough shallow grooves lie sharp in the near foreground, half hidden under strands of seaweed, and beyond them the matte light-grey porcelain right hand of the figure from <IMAGE_1> holds a fist-sized lump of black basalt just above the pointed nail tip poking up through the wood. The plank rests across two rocks, so the nail's head hangs free in the dark gap beneath it. Keep the dusk light of <IMAGE_0>; only the hand and forearm appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 PLANK_UNDER

```text
<IMAGE_0> is the first frame. The hand taps the basalt lump down on the nail tip in short, firm taps, and the tip sinks back into the wood a little with each tap until it sits almost flush. The grooves in the foreground stay still and sharp. Static camera. It ends with the hand resting the basalt lump on the plank beside the flush nail tip. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_2>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand taps the basalt lump down on the nail tip in short, firm taps, and the tip sinks back into the wood a little with each tap until it sits almost flush. The grooves in the foreground stay still and sharp. Static camera. It ends with the hand resting the basalt lump on the plank beside the flush nail tip. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hand and forearm appear,; its head stays out of frame. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, dusk with an orange glow low over the sea and the rocks in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S04 · HAVE · 다음 날 아침 · 뽑아 낸 쇠못을 손바닥에 (인벤토리) · 0:10.90–0:16.55 (5.65s)

**장면** 시간 점프(밤을 건너뛰어 다음 날 아침, 맑음). 비스듬한 미디엄(가슴 높이). 뒤집힌 널빤지(못 구멍만 남음) 옆, 주인공이 뒤꿈치 위에 앉아 뽑아 낸 쇠못을 펼친 오른손바닥에 올리고 고개를 숙인다. 고양이는 널빤지 옆에서 기지개를 켠다. 인물은 중앙~오른쪽(좌측 1/3은 인벤토리 패널).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S02
- 빛: clear_morning · 레퍼런스: P, C, NAIL, PLANK_UNDER
- 생성 7s → 사용 구간 0.000–5.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N04` 그 밖에 가진 건 구명조끼, 젖은 성냥, 호루라기, 물통이다.
- 오버레이: `inventory_panel` (overlays.json)
- 효과음: 아침 파도, 먼 새소리, 고양이 기지개(작게)
- 끝 상태(다음 샷의 출발점): 맑은 아침. 주인공: 뒤꿈치 위 앉음, 쇠못을 쥔 오른손, 고개를 해안 뒤 풀밭 쪽으로. 고양이: 널빤지 옆에 앉음. 뒤집힌 널빤지(못 구멍만 남음, 홈은 작게).

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S02 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 NAIL · 5) 레퍼런스 PLANK_UNDER

```text
Change the time to the next morning, clear and sunny, at the same spot, with the camera at chest height slightly to the side: the figure from <IMAGE_1> sits back on its heels beside the overturned plank from <IMAGE_4>, which now has only a small square hole where the nail was, and holds the pulled-out nail from <IMAGE_3> across its open right palm, its blank head tilted down toward it; the ginger cat from <IMAGE_2> sits on the rock beside the plank. Frame the figure in the centre-right and keep the left third of the frame as plain rock and sea. Keep the same shore, debris and outfit as in <IMAGE_0>, the clothes dry now, and all designs exactly as in <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 7s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL · <IMAGE_4> 레퍼런스 PLANK_UNDER

```text
<IMAGE_0> is the first frame. The figure turns the nail over once on its palm, then closes its fingers around it; beside it the cat stretches its front legs out along the rock and sits up again. Static camera with a very slow push-in. It ends with the figure holding the nail in its closed right hand, its head turning toward the grassy slope behind the shore. Pace the action so that this ending is reached at about 5.4 seconds and then held, almost motionless, until the clip ends at 7 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_4>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure turns the nail over once on its palm, then closes its fingers around it; beside it the cat stretches its front legs out along the rock and sits up again. Static camera with a very slow push-in. It ends with the figure holding the nail in its closed right hand, its head turning toward the grassy slope behind the shore. Pace the action so that this ending is reached at about 5.4 seconds and then held, almost motionless, until the clip ends at 7 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S05 · GATHER · 해안 뒤 풀밭의 쑥 — 큰 잎만 훑어 딴다 · 0:16.55–0:18.60 (2.05s)

**장면** 시간 점프(조금 뒤). 바위 띠 바로 뒤 풀밭·모래언덕 가장자리(바위 위가 아님). 허리 높이까지 자란 쑥 덤불 — 깊게 갈라진 잎, 뒷면은 은백색 솜털. 주인공이 옆모습으로 줄기를 훑어 큰 잎을 따서 왼손에 모은다. 고양이가 풀밭 가장자리를 따라 걷는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S04
- 빛: clear_morning · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.000–2.050s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N05` 섬 들판에 흔한 쑥.
- 오버레이: `label_mugwort` (overlays.json)
- 효과음: 풀잎 스치는 소리, 잎 훑는 소리, 바람
- 끝 상태(다음 샷의 출발점): 주인공: 쑥 덤불 사이에 옆모습으로 섬, 왼손에 쑥잎 한 아름, 고개를 바위 쪽으로. 고양이: 풀밭 가장자리. 맑은 아침.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S04 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the scene to the strip of grass and low sand dune just behind the band of black rocks of the same cove, a little later in the same clear morning light: the figure from <IMAGE_1>, seen in side view, stands among clumps of wild mugwort growing up to its waist, their deeply cut leaves green on top and silvery white underneath, holding a loose handful of picked leaves in its left hand; the ginger cat from <IMAGE_2> walks along the edge of the grass behind it, with the black rocks and the sea beyond. Keep the outfit and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure's right hand strips the large leaves from a mugwort stem in one slow pull and adds them to the handful, the silvery undersides flashing in the sun; the cat keeps walking along the edge of the grass. Static camera. It ends with the figure holding a thick handful of leaves, its head turned toward the rocks. Pace the action so that this ending is reached at about 1.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure's right hand strips the large leaves from a mugwort stem in one slow pull and adds them to the handful, the silvery undersides flashing in the sun; the cat keeps walking along the edge of the grass. Static camera. It ends with the figure holding a thick handful of leaves, its head turned toward the rocks. Pace the action so that this ending is reached at about 1.7 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, clear early-morning sunlight low from the left, long cool shadows, the black rocks dry and the sea bright, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S06 · GATHER · 볕에 달군 너럭바위 — 고양이가 먼저 누워 있음 · 0:18.60–0:22.40 (3.80s)

**장면** 시간 점프(한낮이 가까움, 볕이 강함). 높은 물때선 위 평평한 검은 너럭바위. 고양이가 이미 볕 든 바위 위에 옆으로 길게 누워 있다. 주인공이 쑥잎을 한 아름 안고 왼쪽에서 들어와 바위 옆에 무릎 꿇고 잎을 가장자리에 내려놓는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S05
- 빛: late_morning_sun · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.800s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N06` 쑥 부싯깃은 볶아서 만들지만 볶을 불이 없다.
- 효과음: 맨발이 마른 돌 딛는 소리, 잎 더미 내려놓는 소리
- 끝 상태(다음 샷의 출발점): 너럭바위(강한 볕). 고양이: 바위 위에 옆으로 누움. 주인공: 바위 옆 무릎, 고개 숙임, 쑥잎 더미를 가장자리에 놓음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S05 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the scene to a flat black basalt slab in full sun on the rocks above the high-tide line of the same cove, later in the morning with strong sun and short hard shadows: the ginger cat from <IMAGE_2> lies stretched out on its side on the warm slab, dozing, and the figure from <IMAGE_1> walks in from the left carrying an armful of picked mugwort leaves. Keep the coastline, outfit and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure steps up to the slab and kneels beside it, setting the armful of leaves down at its edge; the cat stays lying in the sun and only flicks one ear. Static camera. It ends with the figure kneeling at the slab beside the cat, its head bowed toward the leaves. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure steps up to the slab and kneels beside it, setting the armful of leaves down at its edge; the cat stays lying in the sun and only flicks one ear. Static camera. It ends with the figure kneeling at the slab beside the cat, its head bowed toward the leaves. Pace the action so that this ending is reached at about 3.5 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S07 · GATHER · 고양이 옆에 잎을 펼치고 조약돌로 눌러 둠 · 0:22.40–0:25.90 (3.50s)

**장면** 부감 클로즈업(손만). 달궈진 검은 바위 위, 고양이의 흰 앞발 아래로 손이 쑥잎을 한 겹 펼치고 연한 조약돌 세 개를 차례로 얹어 바람에 날리지 않게 누른다(시리즈 표시 '조약돌'). 고양이 꼬리가 한 번 바위를 쓴다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S06
- 빛: late_morning_sun · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.500s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N07` 가장 뜨거운 돌은 고양이가 먼저 안다.
- 효과음: 잎 펴는 소리, 조약돌 놓는 소리 3번
- 끝 상태(다음 샷의 출발점): 너럭바위 위 쑥잎 한 겹 + 연한 조약돌 3개(누름). 고양이: 위쪽에 누움, 흰 앞발이 보임. 손은 프레임 밖.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S06 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to an overhead close-up of the sunlit slab from <IMAGE_0>: the ginger cat from <IMAGE_2> lies along the top of the frame with its two white front paws resting at the top edge of the frame, and a hand's width below them the matte light-grey porcelain hands of the figure from <IMAGE_1> spread the mugwort leaves in a single layer on the hot black rock, three pale pebbles beside them. Keep the strong late-morning sun and the designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>; only the hands and forearms of the figure appear, its head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The hands smooth the last leaves flat and set the three pale pebbles on them, one after another, to hold them down; the cat's tail sweeps once across the rock. The hands stay in the lower half of the frame, clear of the paws. Static overhead camera. It ends with the leaves spread flat under the pebbles beside the cat's white paws and the hands withdrawing out of frame. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hands smooth the last leaves flat and set the three pale pebbles on them, one after another, to hold them down; the cat's tail sweeps once across the rock. The hands stay in the lower half of the frame, clear of the paws. Static overhead camera. It ends with the leaves spread flat under the pebbles beside the cat's white paws and the hands withdrawing out of frame. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S08 · FAIL · 현무암 모서리에 못을 내리침 — 돌이 부스러짐 · 0:25.90–0:30.85 (4.95s)

**장면** 시간 점프(몇 분 뒤). 측면 미디엄 클로즈업. 너럭바위 옆에 무릎 꿇은 주인공이 왼손에 구멍 숭숭한 현무암 덩이를 모서리가 위로 오게 쥐고, 오른손의 쇠못으로 그 모서리를 위에서 아래로 내리친다. 모서리가 가루·잔조각으로 부스러지고 불티는 없다. 뒤로 너럭바위 위 고양이와 조약돌로 눌러 둔 쑥잎(초점 밖).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S07
- 빛: late_morning_sun · 레퍼런스: P, C, NAIL
- 생성 6s → 사용 구간 0.000–4.950s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N08` 현무암 모서리에 못을 내리친다. / `N09` 돌이 부스러진다.
- 효과음: 쇠가 돌을 긁는 '드륵', 돌가루 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 무릎, 고개 숙임, 왼손 현무암 덩이(모서리가 부스러짐), 오른손 쇠못. 바위에 회색 가루. 불티 없음. 뒤로 너럭바위 위 고양이.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S07 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 NAIL

```text
Change the camera to a medium close-up from the side a few minutes later: the figure from <IMAGE_1> kneels beside the sunlit slab, its blank head bowed toward its hands, holding a fist-sized lump of rough, pitted black basalt in its left hand with one edge up and the rusty iron nail from <IMAGE_3> raised in its right hand above that edge; behind it, slightly out of focus, the cat from <IMAGE_2> lies on the slab beside the leaves held down by the pale pebbles. Keep the strong late-morning sun and all designs exactly as in <IMAGE_0>, <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL

```text
<IMAGE_0> is the first frame. The right hand brings the nail down hard along the basalt edge in one fast stroke; the porous edge crumbles into dull grey grit and small chips that patter onto the rock in a puff of grey dust. Static camera. It ends with both hands frozen just after the stroke, a little grey dust still drifting down. Pace the action so that this ending is reached at about 4.7 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand brings the nail down hard along the basalt edge in one fast stroke; the porous edge crumbles into dull grey grit and small chips that patter onto the rock in a puff of grey dust. Static camera. It ends with both hands frozen just after the stroke, a little grey dust still drifting down. Pace the action so that this ending is reached at about 4.7 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S09 · FAIL · 한 번 더 — 불티 없음, 손을 내림 · 0:30.85–0:33.00 (2.15s)

**장면** 같은 컷 이어서. 한 번 더 세게 내리친다. 또 부스러지고 아무것도 빛나지 않는다. 두 손을 무릎 위로 내린다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S08
- 빛: late_morning_sun · 레퍼런스: P, C, NAIL
- 생성 4s → 사용 구간 0.000–2.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N10` 불티는, 없다.
- 효과음: 두 번째 '드륵', 정적 — 파도만
- 끝 상태(다음 샷의 출발점): 주인공: 무릎 꿇고 두 손을 무릎 위에(쇠못·부스러진 현무암 덩이), 고개 숙임. 불티 없음. 뒤로 고양이.

**① 시작 프레임** = S08 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL

```text
Continuing from <IMAGE_0>, the figure strikes the basalt edge once more, harder; more dull grey grit crumbles away and drifts down as dust. The figure lowers both hands to its knees and stays still. Static camera. It ends with the figure kneeling, its hands resting on its knees with the nail and the crumbled basalt lump, its head bowed. Pace the action so that this ending is reached at about 1.8 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the figure strikes the basalt edge once more, harder; more dull grey grit crumbles away and drifts down as dust. The figure lowers both hands to its knees and stays still. Static camera. It ends with the figure kneeling, its hands resting on its knees with the nail and the crumbled basalt lump, its head bowed. Pace the action so that this ending is reached at about 1.8 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S10 · PRINCIPLE · 측면 정렬 구도 · 바위 위에서 쇠못을 들어 봄 (도면) · 0:33.00–0:40.92 (7.92s)

**장면** 측면 와이드(바위 높이). 주인공은 큰 현무암 바위 꼭대기에 앉아 오른손으로 쇠못을 들어 올리고 고개를 그쪽으로 기울인다 — 못 위치 x≈620·y≈480(도면 지시선 시작점). 고양이는 왼쪽 너럭바위에 누움. 둘 다 상단 띠(y300~540), 합친 폭 약 1/3. 아래 2/3는 그늘진 바위 면만(도면, 배경 40% 어둡게).

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S09
- 빛: late_morning_sun · 레퍼런스: P, C, NAIL
- 생성 9s → 사용 구간 0.000–7.924s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N11` 불티는 돌이 아니라 쇠에서 나온다. / `N12` 단단한 돌 날이 대패처럼 쇠를 깎는다. / `N13` 깎인 조각이 달아올라 공기 속에서 탄다.
- 오버레이: `diagram_strike_spark` (overlays.json)
- 효과음: 파도 베드(낮게), 바람
- 끝 상태(다음 샷의 출발점): 상단 띠: 바위 위 주인공(오른손에 쇠못을 들어 올림, x≈620·y≈480), 왼쪽 너럭바위에 고양이 누움. 아래 2/3 그늘진 바위 면.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S09 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 NAIL

```text
Change the camera to a side-on view at the height of the rocks, a little later: the figure from <IMAGE_1> sits on top of a large black boulder in the upper part of the frame, between about a sixth and just over a quarter of the way down, holding the rusty iron nail from <IMAGE_3> up in its right hand just right of the centre of the frame and about a quarter of the way down, its blank head tilted toward the nail; the ginger cat from <IMAGE_2> lies on the sunlit slab at the upper left, level with the figure, the two together spanning about a third of the frame width. Leave the lower two-thirds of the frame plain and empty: only the shadowed side of the boulder and dark rock. Keep the late-morning sun of <IMAGE_0> and all designs exactly as in <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 9s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL

```text
<IMAGE_0> is the first frame. The figure turns the nail slowly between its fingers, holding it up in the same place; the cat lies still in the sun and the tip of its tail lifts once. Static camera. It ends with the same calm composition, the nail held up in the figure's right hand. Pace the action so that this ending is reached at about 7.6 seconds and then held, almost motionless, until the clip ends at 9 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure turns the nail slowly between its fingers, holding it up in the same place; the cat lies still in the sun and the tip of its tail lifts once. Static camera. It ends with the same calm composition, the nail held up in the figure's right hand. Pace the action so that this ending is reached at about 7.6 seconds and then held, almost motionless, until the clip ends at 9 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S11 · PRINCIPLE · 실시간 이어짐 · 고양이가 고개를 듦 (도면) · 0:40.92–0:49.28 (8.36s)

**장면** 같은 컷 이어서(실시간). 주인공이 못을 조금 내렸다가 같은 자리로 다시 든다. 고양이가 귀를 쫑긋하고 주인공 쪽으로 고개를 들었다가 다시 눕는다.

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S10
- 빛: late_morning_sun · 레퍼런스: P, C, NAIL
- 생성 10s → 사용 구간 0.000–8.359s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N14` 오늘날 굳기 척도로 부싯돌은 약 7이다. 쇠보다 단단하다.
- 오버레이: `diagram_strike_spark` (overlays.json)
- 효과음: 파도 베드(낮게), 바람
- 끝 상태(다음 샷의 출발점): 같은 구도. 주인공: 쇠못을 든 채. 고양이: 다시 누움.

**① 시작 프레임** = S10 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 10s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL

```text
Continuing from <IMAGE_0>, the figure lowers the nail a little and raises it again to the same place; the cat's ear twitches, it lifts its head toward the figure, then lays it down again. Static camera. It ends with the same composition, the nail held up in the figure's right hand. Pace the action so that this ending is reached at about 8.1 seconds and then held, almost motionless, until the clip ends at 10 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the figure lowers the nail a little and raises it again to the same place; the cat's ear twitches, it lifts its head toward the figure, then lays it down again. Static camera. It ends with the same composition, the nail held up in the figure's right hand. Pace the action so that this ending is reached at about 8.1 seconds and then held, almost motionless, until the clip ends at 10 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S12 · PRINCIPLE · 일어서서 난파 잔해 쪽으로 고개 (귀에 남는 문장) · 0:49.28–0:52.69 (3.41s)

**장면** 앵글 컷(뒤쪽 비스듬한 미디엄). 도면 없음, 어둡게 안 함. 주인공이 바위 위에서 일어서 쇠못을 쥐고, 해안선을 따라 몇 m 아래 난파 잔해(부서진 널빤지·밧줄·통판·배 밑바닥 굵은 목재) 쪽으로 고개를 돌린다. 아래 너럭바위에서 고양이가 고개를 든다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S11
- 빛: late_morning_sun · 레퍼런스: P, C, NAIL
- 생성 5s → 사용 구간 0.000–3.408s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N15` 돌은 칼이 되고, 쇠가 불이 된다.
- 효과음: 파도, 맨발이 돌을 딛는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 바위 위에 서서 잔해 쪽으로 고개, 오른손에 쇠못. 고양이: 너럭바위에서 고개 듦. 배경에 난파 잔해(배 밑바닥 목재 포함).

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S11 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 NAIL

```text
Change the camera to a medium shot from behind and to the side of the figure from <IMAGE_1>, a moment later: it is getting to its feet on top of the boulder with the iron nail from <IMAGE_3> in its right hand, and just below the boulder, a few metres away along the waterline, lies the scattered shipwreck debris of the cove: broken dark planks, a coil of thick rope, split barrel staves and a broken section of the ship's heavy bottom timbers; the ginger cat from <IMAGE_2> lies on the slab below. Keep the late-morning sun and all designs exactly as in <IMAGE_0>, <IMAGE_1>, <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL

```text
<IMAGE_0> is the first frame. The figure straightens up on the boulder, closes its hand around the nail, and its head turns toward the shipwreck debris along the shore; below, the cat lifts its head. Static camera. It ends with the figure standing still, head turned toward the debris. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure straightens up on the boulder, closes its hand around the nail, and its head turns toward the shipwreck debris along the shore; below, the cat lifts its head. Static camera. It ends with the figure standing still, head turned toward the debris. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S13 · BUILD · (재료 인서트) 배 밑바닥 잔해에 낀 흰 돌 · 0:52.69–0:56.34 (3.65s)

**장면** 인서트(어깨 너머, 뒤통수만). 서 있는 주인공의 어깨 너머로 2m 앞 아래 배 밑바닥 굵은 목재. 목재 틈에 둥근 돌 몇 개가 끼어 있고, 그 위 분필처럼 흰 껍질의 울퉁불퉁한 돌 하나로 천천히 푸시인(바닥짐 돌 — 허구 설정).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S12
- 빛: late_morning_sun · 레퍼런스: P, FLINT
- 생성 5s → 사용 구간 0.000–3.650s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N16` 배 밑바닥 잔해에 흰 돌 하나가 끼어 있다.
- 효과음: 파도가 잔해 사이로 드나듦
- 끝 상태(다음 샷의 출발점): 프레임 중앙: 배 밑바닥 목재 틈의 흰 껍질 돌(깨기 전, 통째). 주인공 어깨는 프레임 가장자리.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S12 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLINT

```text
Change the camera to an over-the-shoulder view from behind the figure from <IMAGE_1>, standing on the boulder in <IMAGE_0> with its blank head seen only from the back, toward the broken section of the ship's heavy bottom timbers lying on the rocks about two metres below and in front of it: wedged between two thick timbers lie a few rounded stones, and on top of them one knobbly palm-sized stone with a chalky white rind like the whole stone in <IMAGE_2>, bright against the dark wood and black rock. Keep the same debris, shoreline, late-morning sun and the figure's design exactly as in <IMAGE_0> and <IMAGE_1>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the chalk-white stone; small waves wash in and out around the timbers. It ends with the white stone clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_2>; it is whole or broken exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure holds still as the camera pushes in slowly past its shoulder toward the chalk-white stone; small waves wash in and out around the timbers. It ends with the white stone clearly visible in the middle of the frame. Pace the action so that this ending is reached at about 3.4 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S14 · BUILD · 흰 돌을 깨서 유리 같은 날 세우기 · 0:56.34–0:58.69 (2.35s)

**장면** 시간 점프(몇 분 뒤) 클로즈업(손만). 평평한 현무암 위에서 왼손이 흰 돌을 누르고, 오른손의 주먹만 한 현무암 덩이로 내리친다. 쩍 갈라지며 짙은 회색 유리질 속(조개껍데기 같은 매끈한 곡면)과 얇고 날카로운 날이 드러난다. 큰 조각이 바위 위에 벌어져 날이 카메라 쪽을 향한다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S13
- 빛: late_morning_sun · 레퍼런스: P, FLINT
- 생성 4s → 사용 구간 0.000–2.350s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N17` 깨면 유리 같은 날이 선다.
- 효과음: 돌 깨지는 '딱', 조각 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 깨진 흰 돌 두 조각이 바위 위에 벌어져 짙은 회색 유리질 속·날이 카메라 쪽. 오른손은 현무암 덩이를 쥔 채 옆.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S13 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 FLINT

```text
Change the camera to a close-up a few minutes later of a flat black basalt rock in the late-morning sun: the matte light-grey porcelain left hand of the figure from <IMAGE_1> holds the whole chalk-white stone from <IMAGE_2> down on the rock, and the right hand raises a fist-sized lump of black basalt above it. Keep the light of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The right hand brings the basalt lump down sharply on the white stone and it splits in two; the larger half rocks open on the rock, showing dark grey glassy stone inside with smooth curved shell-like surfaces and a thin sharp edge. Static macro camera. It ends with the two halves lying open on the rock, the glassy inside and the sharp edge toward the camera. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_2>; it is whole or broken exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand brings the basalt lump down sharply on the white stone and it splits in two; the larger half rocks open on the rock, showing dark grey glassy stone inside with smooth curved shell-like surfaces and a thin sharp edge. Static macro camera. It ends with the two halves lying open on the rock, the glassy inside and the sharp edge toward the camera. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S15 · BUILD · 실패한 현무암에 못의 녹을 갈아 냄 (숫돌) · 0:58.69–1:02.14 (3.45s)

**장면** 클로즈업(손만). 왼손으로 누른 실패한 현무암 덩이의 거친 면에 오른손이 쇠못 한 면을 대고 앞뒤로 세게 문지른다. 주황·갈색 녹가루가 검은 돌에 묻고 은회색 새 쇳빛 줄이 드러난다. 손이 못을 기울여 간 면에 햇빛을 받는다. 옆에 깨진 흰 돌 조각.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S14
- 빛: late_morning_sun · 레퍼런스: P, NAIL, FLINT
- 생성 5s → 사용 구간 0.000–3.450s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N18` 실패한 현무암은 못을 가는 숫돌이 된다.
- 효과음: 쇠를 돌에 가는 '스윽스윽'
- 끝 상태(다음 샷의 출발점): 오른손: 쇠못(한 면이 은회색으로 갈림)을 들어 빛에 비춤. 바위에 녹가루. 깨진 흰 돌 조각은 옆.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S14 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT

```text
Change the camera to a close-up a moment later of the fist-sized lump of pitted black basalt from the failed strike, its crumbled edge up, held down on the rock by the matte light-grey porcelain left hand of the figure from <IMAGE_1>, while the right hand presses one flat side of the rusty iron nail from <IMAGE_2> against the rough basalt; the broken white stone from <IMAGE_3> lies on the rock nearby with its glassy edge up. Keep the late-morning sun of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The hand rubs the nail back and forth along the rough basalt in short, hard strokes; orange-brown rust dust smears onto the black rock and a stripe of bright grey metal appears along the ground side. The hand lifts the nail and tilts it so the bright side catches the sun. Static macro camera. It ends with the nail held still, its bright ground side toward the camera. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The hand rubs the nail back and forth along the rough basalt in short, hard strokes; orange-brown rust dust smears onto the black rock and a stripe of bright grey metal appears along the ground side. The hand lifts the nail and tilts it so the bright side catches the sun. Static macro camera. It ends with the nail held still, its bright ground side toward the camera. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, bright late-morning sun high in a clear sky, short hard shadows, the black rocks hot and dry, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S16 · BUILD · 반나절 뒤 — 바삭해진 쑥잎을 비벼 솜을 얻음 · 1:02.14–1:05.99 (3.85s)

**장면** 시간 점프(반나절 뒤, 오후 낮은 해, 그림자가 길어짐). S07의 너럭바위(조약돌 3개 위치 그대로). 쑥잎이 바삭하게 말려 오그라들었다. 고양이는 바위 가장자리 그늘에 앉음. 주인공이 무릎 꿇고 마른 잎 한 줌을 두 손바닥 사이에 세게 비빈다. 초록 부스러기가 떨어지고 손바닥에 회녹색 솜 한 뭉치가 남는다.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S15 · 참고 프레임 S07
- 빛: afternoon · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.850s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N19` 바삭하게 마른 쑥잎을 비비면 솜이 남는다.
- 오버레이: `time_card_halfday` (overlays.json)
- 효과음: 마른 잎 바스러지는 소리, 부스러기 떨어지는 소리
- 끝 상태(다음 샷의 출발점): 주인공: 너럭바위 옆 무릎, 펼친 손바닥에 회녹색 쑥 솜 한 뭉치. 바위 위 마른 잎·조약돌 3개·초록 부스러기. 고양이: 가장자리 그늘에 앉음. 오후 낮은 해.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S15 끝 프레임 · 2) S07 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C

```text
Change the scene to the sunlit slab shown in <IMAGE_1>, half a day later in warm low afternoon sun with long shadows: the mugwort leaves spread under the same three pale pebbles are now dry, curled and crisp, and the figure from <IMAGE_2> kneels at the slab with its blank head bowed toward its hands, holding a handful of the dry leaves between its palms; the ginger cat from <IMAGE_3> sits in the shade at the edge of the slab. Take only the slab, the leaves and the pebbles from <IMAGE_1>; the figure and the cat each appear only once, where described here. Keep the outfit as in <IMAGE_0> and both designs exactly as in <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure rubs the dry leaves hard between its palms; green crumbs fall away onto the rock, and it opens its hands to show a small soft ball of grey-green fluff left in one palm. The cat stays sitting in the shade. Static camera. It ends with the figure holding its palm open with the grey-green fluff, head bowed toward it. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure rubs the dry leaves hard between its palms; green crumbs fall away onto the rock, and it opens its hands to show a small soft ball of grey-green fluff left in one palm. The cat stays sitting in the shade. Static camera. It ends with the figure holding its palm open with the grey-green fluff, head bowed toward it. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S17 · BUILD · 불 받을 둥지와 잔가지를 미리 준비 · 1:05.99–1:09.34 (3.35s)

**장면** 시간 점프(잠시 뒤 — 쑥 솜 2~3뭉치를 더 비비고 사구 가장자리에서 잔가지를 주워 온 뒤, 몇 걸음 옆 측면 미디엄). 풀밭과 떨어지고 큰 바위가 바람을 가린 맨바위 오목(높은 물때선 위). 주인공이 마른 풀과 풀어 낸 밧줄 섬유로 만든 새 둥지 모양 뭉치를 오목에 앉히고 가운데를 두 손가락으로 눌러 오목하게 한다. 옆에 순비기나무 죽은 잔가지가 성냥개비 굵기→손가락 굵기로 한 줄, 납작한 돌 위에 쑥 솜 뭉치 두세 개. 고양이는 뒤쪽 너럭바위.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S16
- 빛: afternoon · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.350s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N20` 불 받을 둥지는 불씨보다 먼저 만든다.
- 효과음: 마른 풀 바스락, 잔가지 놓는 소리
- 끝 상태(다음 샷의 출발점): 바위 오목: 마른 풀·밧줄 섬유 둥지(가운데 오목). 옆: 잔가지 줄(가는→굵은), 납작돌 위 쑥 솜 2~3뭉치. 주인공: 오목 옆 무릎, 고개 숙임. 고양이: 뒤쪽 너럭바위. 오후.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S16 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the time to a little later the same afternoon, a few steps away, seen in a medium side view: the figure from <IMAGE_1> kneels at a shallow hollow in the bare rock, sheltered from the wind by a large boulder and well away from the grass, holding a loose bird's-nest-shaped bundle of pale dead grass and frayed brown rope fibres over it; beside the hollow lie dead twigs in a row from matchstick-thin to finger-thick, and on a small flat stone sit two or three soft balls of grey-green fluff. The ginger cat from <IMAGE_2> sits on the slab a few metres behind. Keep the warm afternoon sun and all designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure sets the nest down into the hollow and presses its centre into a small cup with two fingers, then lays a few of the thinnest twigs ready beside it. Static camera. It ends with the nest sitting in the hollow and the figure's hands resting on its knees, head bowed toward the nest. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure sets the nest down into the hollow and presses its centre into a small cup with two fingers, then lays a few of the thinnest twigs ready beside it. Static camera. It ends with the nest sitting in the hollow and the figure's hands resting on its knees, head bowed toward the nest. Pace the action so that this ending is reached at about 3.1 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S18 · BUILD · 조선식 쥐기 — 돌 위에 쑥 솜, 못으로 날을 긁어 내림 · 1:09.34–1:13.84 (4.50s)

**장면** 익스트림 클로즈업(손만, 오목 위). 왼손에 깨진 흰 돌, 날을 위로. 날 바로 뒤에 쑥 솜을 얹어 엄지로 누름. 오른손이 쇠못 대가리를 쥐고 간 면으로 날을 위에서 아래로 비스듬히 빠르게 긁어 내린다(손가락을 내리치지 않는 궤적). 첫 번째는 아무것도 없고, 두 번째에 작은 주황 불티 하나가 튀어 몇 cm 날다 꺼진다. (QC: 흰 불꽃 소나기·폭죽·떠다니는 빛 입자·손에 붙는 불이면 탈락 — factcheck F14. 불티는 모래알만 한 주황 점 1~3개, 몇 cm 호를 그리고 즉시 꺼짐) S18이 3테이크 안에 통과하지 못하면 S18은 두 번 긁고 불티 없이 끝내고 첫 불티는 S19에서.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S17
- 빛: afternoon · 레퍼런스: P, NAIL, FLINT
- 생성 6s → 사용 구간 0.000–4.500s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N21` 돌 위에 쑥 솜을 얹고 못으로 모서리를 긁어 내린다.
- 효과음: 쇠가 돌 날을 긁는 '칙', 두 번째 '칙'
- 끝 상태(다음 샷의 출발점): 두 손 쥐기 자세 정지: 왼손 흰 돌(날 위)+엄지로 누른 쑥 솜, 오른손 쇠못(간 면). 솜은 아직 안 붙음.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S17 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT

```text
Change the camera to an extreme close-up a moment later of the figure's matte light-grey porcelain hands from <IMAGE_1> above the hollow: the left hand holds the broken white stone from <IMAGE_3> with its sharp glassy edge on top and a pinch of grey-green fluff resting on the stone just behind the edge under the left thumb, and the right hand holds the iron nail from <IMAGE_2> by its head, its bright ground side just above the edge. Keep the warm afternoon sun of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The right hand scrapes the bright side of the nail down along the stone's edge in one fast glancing stroke, then a second; the first stroke only scrapes, and on the second a single tiny orange spark jumps from the edge, arcs a few centimetres and fades out as it falls. Static macro camera. It ends with both hands held still in the grip, the fluff still grey-green. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right hand scrapes the bright side of the nail down along the stone's edge in one fast glancing stroke, then a second; the first stroke only scrapes, and on the second a single tiny orange spark jumps from the edge, arcs a few centimetres and fades out as it falls. Static macro camera. It ends with both hands held still in the grip, the fluff still grey-green. Pace the action so that this ending is reached at about 4.2 seconds and then held, almost motionless, until the clip ends at 6 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S19 · TEST · 한참 뒤 — 치고 또 침, 불티는 몇 번에 한 번 · 1:13.84–1:18.84 (5.00s)

**장면** 시간 점프(한참 뒤, 해가 더 낮고 그림자가 길다). 측면 미디엄. 오목 옆에 무릎 꿇은 주인공이 일정한 박자로 계속 친다. 무릎 주변 바위에 흰·회색 돌 부스러기(무뎌진 날을 다시 깬 흔적). 대부분은 아무것도 없고 가끔 작은 주황 불티 1~2개. 손을 한 번 털고 다시 친다. 고양이는 몇 걸음 뒤 너럭바위, 불티와 멀리. (QC: 흰 불꽃 소나기·폭죽·떠다니는 빛 입자·손에 붙는 불이면 탈락 — factcheck F14. 불티는 모래알만 한 주황 점 1~3개, 몇 cm 호를 그리고 즉시 꺼짐)

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S17
- 빛: afternoon · 레퍼런스: P, C, NAIL, FLINT
- 생성 6s → 사용 구간 0.000–5.000s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N22` 치고, 또 친다. / `N23` 무른 쇠라, 불티는 몇 번에 한 번 튄다.
- 오버레이: `time_card_later` (overlays.json)
- 효과음: '칙' 반복(일정한 리듬), 가끔 미세한 '틱'
- 끝 상태(다음 샷의 출발점): 주인공: 오목 옆 무릎, 쥐기 자세로 멈춤, 고개 숙임. 무릎 주변 돌 부스러기. 고양이: 뒤쪽 너럭바위. 늦은 오후 빛.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S17 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C · 4) 레퍼런스 NAIL · 5) 레퍼런스 FLINT

```text
Change the time to much later the same afternoon, the sun lower and the shadows longer, at the same hollow, seen in a medium side view: the figure from <IMAGE_1> kneels beside the nest in the hollow, its blank head bowed toward its hands, in the same striking grip with the broken white stone from <IMAGE_4> in its left hand and the iron nail from <IMAGE_3>, its ground side bright, in its right; small white and grey flakes knocked off the stone lie scattered on the rock around its knees, and the ginger cat from <IMAGE_2> sits on the slab several steps behind, well away from the hands. Keep the hollow, the nest and the twigs as in <IMAGE_0> and all designs exactly as in <IMAGE_1>, <IMAGE_2>, <IMAGE_4> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 6s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 NAIL · <IMAGE_4> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The figure strikes again and again in a steady rhythm; most strokes only scrape, and only now and then one or two tiny orange sparks jump from the stone and fade in the air. Between strokes it shakes its right hand once and goes on. The cat stays sitting on the slab. Static camera. It ends with the figure paused in the grip, hands held still just above the hollow. Pace the action so that this ending is reached at about 4.7 seconds and then held, almost motionless, until the clip ends at 6 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_3>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_4>; it is whole or broken exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure strikes again and again in a steady rhythm; most strokes only scrape, and only now and then one or two tiny orange sparks jump from the stone and fade in the air. Between strokes it shakes its right hand once and goes on. The cat stays sitting on the slab. Static camera. It ends with the figure paused in the grip, hands held still just above the hollow. Pace the action so that this ending is reached at about 4.7 seconds and then held, almost motionless, until the clip ends at 6 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S20 · TEST · 불티가 솜에 떨어져도 꺼짐 — 볶지 못한 쑥 · 1:18.84–1:22.39 (3.55s)

**장면** 익스트림 클로즈업(손만). 쇠못이 날을 몇 번 긁어 내린다. 작은 주황 불티가 쑥 솜 위에 떨어지지만 붙지 못하고 하나씩 꺼진다(그을리지 않은 생쑥). (QC: 흰 불꽃 소나기·폭죽·떠다니는 빛 입자·손에 붙는 불이면 탈락 — factcheck F14. 불티는 모래알만 한 주황 점 1~3개, 몇 cm 호를 그리고 즉시 꺼짐)

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S19
- 빛: afternoon · 레퍼런스: P, NAIL, FLINT
- 생성 5s → 사용 구간 0.000–3.550s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N24` 볶지 못한 쑥은 불티를 잘 붙잡지 못한다.
- 효과음: '칙' 3번, 아주 작은 '틱'
- 끝 상태(다음 샷의 출발점): 쥐기 자세. 쑥 솜은 아직 안 붙음(불티 자국만). 손만.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S19 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT

```text
Change the camera to an extreme close-up a moment later of the pinch of grey-green fluff on top of the broken white stone from <IMAGE_3>, held under the left thumb of the figure's matte light-grey porcelain hand from <IMAGE_1>, with the right hand holding the iron nail from <IMAGE_2>, its ground side bright, poised just above the stone's edge. Keep the lower afternoon sun of <IMAGE_0>; only the hands appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The nail scrapes down the edge three times; twice a tiny orange spark lands on the fluff, glows for an instant and goes out. Static macro camera. It ends with the hands poised for another stroke, the fluff still grey-green. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The nail scrapes down the edge three times; twice a tiny orange spark lands on the fluff, glows for an instant and goes out. Static macro camera. It ends with the hands poised for another stroke, the fluff still grey-green. Pace the action so that this ending is reached at about 3.2 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S20b · TEST · 불티가 솜에 박힘 — 주황 점이 번짐 · 1:22.39–1:26.29 (3.90s)

**장면** 같은 컷 이어서. 한 번 더 긁자 불티 하나가 솜에 박혀, 바늘 끝만 한 주황 점이 천천히 번지고 가는 연기 한 줄이 오른다. 두 손이 멈춘다. (QC: 흰 불꽃 소나기·폭죽·떠다니는 빛 입자·손에 붙는 불이면 탈락 — factcheck F14. 불티는 모래알만 한 주황 점 1~3개, 몇 cm 호를 그리고 즉시 꺼짐)

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S20
- 빛: afternoon · 레퍼런스: P, NAIL, FLINT
- 생성 5s → 사용 구간 0.000–3.900s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N25` 그러다, 솜 위에 주황 점 하나가 번진다.
- 효과음: '칙' 1번, 아주 작은 지글거림
- 끝 상태(다음 샷의 출발점): 쑥 솜에 주황 불씨(작게 번짐) + 가는 연기 한 줄. 두 손 정지(손만).

**① 시작 프레임** = S20 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
Continuing from <IMAGE_0>, the nail scrapes down the edge once more; a tiny orange spark lands on the fluff and stays, and a pin-point of orange glow slowly spreads in it as a thin thread of smoke rises. The hands go still. Static macro camera. It ends with the small orange glow in the fluff and the thread of smoke rising, the hands motionless. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the nail scrapes down the edge once more; a tiny orange spark lands on the fluff and stays, and a pin-point of orange glow slowly spreads in it as a thin thread of smoke rises. The hands go still. Static macro camera. It ends with the small orange glow in the fluff and the thread of smoke rising, the hands motionless. Pace the action so that this ending is reached at about 3.6 seconds and then held, almost motionless, until the clip ends at 5 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S21 · TEST · 둥지에 감싸 흔들어 바람을 먹임 → 불꽃 (실시간 히어로) · 1:26.29–1:32.44 (6.15s)

**장면** 히어로 샷 — 측면 미디엄 클로즈업, 실시간. 주인공이 불씨 든 솜을 넣은 둥지를 두 손으로 오므려, 머리에서 멀리 팔을 뻗은 채 천천히 앞뒤로 흔든다(입으로 불지 않는다). 흰 연기가 흔들 때마다 짙어지다가 노란 불꽃이 확 인다. 불붙은 둥지를 오목의 가는 잔가지 위에 내려놓는다. 불꽃이 화면 안 가장 따뜻한 광원.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S20b · 참고 프레임 S19
- 빛: afternoon · 레퍼런스: P, C
- 생성 8s → 사용 구간 0.000–6.150s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N26` 둥지에 감싸, 바람을 먹인다. / `N27` 연기가 짙어지다가, 불꽃이 선다.
- 효과음: 둥지 흔드는 바람 소리, 연기 '훅', 불꽃 이는 '화르륵'(작게)
- 끝 상태(다음 샷의 출발점): 바위 오목에 작은 불꽃(둥지+가는 잔가지). 주인공: 옆에 무릎, 손을 거둠. 고양이: 주인공 뒤 2m쯤 바위(오목 반대편), 먼 바다 수평선에 낮은 비구름. 불꽃이 가장 따뜻한 광원.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S20b 끝 프레임 · 2) S19 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C

```text
Change the camera to a medium close-up from the side a moment later: the figure from <IMAGE_2> kneels by the hollow and holds the loose nest of dry grass and rope fibre in both hands at chest height, well out in front of its body and away from its head, with the glowing fluff tucked into the nest's centre and a thread of smoke rising from it; the ginger cat from <IMAGE_3> sits on a rock about two metres behind the figure, on the side away from the hollow; far out over the sea behind them a dark grey bank of rain cloud sits low on the horizon. Take only the hollow, the nest's surroundings, the large boulder and the slab from <IMAGE_1>; the figure and the cat each appear only once, where described here. Keep the lower afternoon sun of <IMAGE_0> and both designs exactly as in <IMAGE_2> and <IMAGE_3>.
```

**② 영상** (`grok-imagine-video-1.5`, 8s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The figure folds the nest loosely closed around the glowing fluff and swings it slowly back and forth at arm's length, white smoke pouring out thicker with each swing; then it sets the smoking nest down into the hollow on the thinnest twigs, and a small yellow flame bursts up out of it as the hands draw back. Static camera. It ends with the small flame burning in the hollow and the figure kneeling beside it, its hands drawn back. Pace the action so that this ending is reached at about 5.9 seconds and then held, almost motionless, until the clip ends at 8 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The figure folds the nest loosely closed around the glowing fluff and swings it slowly back and forth at arm's length, white smoke pouring out thicker with each swing; then it sets the smoking nest down into the hollow on the thinnest twigs, and a small yellow flame bursts up out of it as the hands draw back. Static camera. It ends with the small flame burning in the hollow and the figure kneeling beside it, its hands drawn back. Pace the action so that this ending is reached at about 5.9 seconds and then held, almost motionless, until the clip ends at 8 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, warm low afternoon sun from the left, long soft shadows, the black rocks dry and warm, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S22 · COST · 작은 불 · 따뜻한 자리를 고양이에게(관계 비트) · 바다 쪽 소나기 구름 · 1:32.44–1:35.69 (3.25s)

**장면** 같은 컷 이어서. 손바닥 높이도 안 되는 작은 불이 잔가지 속에서 낮게 탄다. 주인공이 불 반대편, 무릎 옆의 마르고 따뜻한 바위를 손바닥으로 한 번 두드리고, 고양이가 뒤쪽 바위에서 건너와 거기 앉는다(주인공 몸이 고양이와 불 사이). 수평선에 있던 짙은 회색 소나기 구름이 바다 쪽에서 다가오고 빛이 어두워진다. (경고 오버레이 시작)

- 연결: **C** 이어가기(앞 끝 프레임 그대로) · 출발 S21
- 빛: squall · 레퍼런스: P, C
- 생성 5s → 사용 구간 0.000–3.250s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N28` 바다 쪽에서 소나기가 온다.
- 오버레이: `warning_fire` (overlays.json)
- 효과음: 작은 불 타닥, 바람이 세짐
- 끝 상태(다음 샷의 출발점): 작은 불(손바닥 높이 이하). 주인공: 불 옆 무릎. 고양이: 주인공 옆, 주인공 몸이 불과의 사이, 바다 쪽으로 고개. 바다 위 소나기 구름, 빛이 어두워짐.

**① 시작 프레임** = S21 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다.

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
Continuing from <IMAGE_0>, the figure pats the warm dry rock beside its knee, on the side away from the fire, and the cat steps over from the rock behind and sits down there, the figure's body between the cat and the small fire, which burns low in the twigs, about a hand high. Out over the sea the dark grey squall comes closer and the light dims. Static camera. It ends with the cat sitting close against the figure's side, its head turning toward the sea. Pace the action so that this ending is reached at about 3.0 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, late-afternoon light dimming fast as a dark grey rain squall rolls in over the sea, the small fire the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
Continuing from the uploaded image, the figure pats the warm dry rock beside its knee, on the side away from the fire, and the cat steps over from the rock behind and sits down there, the figure's body between the cat and the small fire, which burns low in the twigs, about a hand high. Out over the sea the dark grey squall comes closer and the light dims. Static camera. It ends with the cat sitting close against the figure's side, its head turning toward the sea. Pace the action so that this ending is reached at about 3.0 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, late-afternoon light dimming fast as a dark grey rain squall rolls in over the sea, the small fire the warmest light in the frame, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S23 · COST · 고양이가 먼저 바위 밑으로 · 굵은 빗방울 · 몸을 숙여 불을 가림 · 1:35.69–1:38.29 (2.60s)

**장면** 앵글 컷(조금 더 넓은 측면). 고양이가 먼저 일어나 큰 바위 밑 마른 틈으로 들어간다(위험보다 먼저 피함). 이어서 굵은 빗방울이 듣고, 주인공이 오목 위로 몸을 숙여 비를 막고 두 손은 오목 양옆 바위를 짚는다(불 위로 손을 덮지 않음). 쉬익 흰 김.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S22
- 빛: rain · 레퍼런스: P, C
- 생성 4s → 사용 구간 0.000–2.600s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N29` 빗물이 열을 빼앗는다.
- 오버레이: `warning_fire` (overlays.json)
- 효과음: 굵은 빗방울, 쉬익(물이 불에 닿는 소리)
- 끝 상태(다음 샷의 출발점): 굵은 비. 주인공: 오목 위로 몸을 숙여 비를 막고 두 손은 오목 양옆 바위를 짚음, 흰 김. 고양이: 큰 바위 밑 마른 틈 안.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S22 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 C

```text
Change the camera to a slightly wider side view a moment later, as the squall arrives: the first heavy raindrops spatter the dark rocks, the figure from <IMAGE_1> kneels by the small fire in the hollow, and the ginger cat from <IMAGE_2> is already up and trotting toward a dry gap under the overhang of the large boulder behind them. Keep the place, the small fire and both designs exactly as in <IMAGE_0>, <IMAGE_1> and <IMAGE_2>, in the dim grey light of the squall.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C

```text
<IMAGE_0> is the first frame. The cat slips into the dry gap under the boulder; then the rain thickens, and the figure hunches its body and shoulders low over the hollow to shield the fire from the rain, both hands braced flat on the rock either side of it, as raindrops hiss on the embers and white steam begins to rise. Static camera. It ends with the figure hunched over the hollow, its hands braced on the rock either side, steam rising past its vest. Pace the action so that this ending is reached at about 2.3 seconds and then held, almost motionless, until the clip ends at 4 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat slips into the dry gap under the boulder; then the rain thickens, and the figure hunches its body and shoulders low over the hollow to shield the fire from the rain, both hands braced flat on the rock either side of it, as raindrops hiss on the embers and white steam begins to rise. Static camera. It ends with the figure hunched over the hollow, its hands braced on the rock either side, steam rising past its vest. Pace the action so that this ending is reached at about 2.3 seconds and then held, almost motionless, until the clip ends at 4 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S24 · COST · 불꽃이 몇 초에 걸쳐 낮아지다 꺼짐 · 남은 쑥 솜도 젖음 · 1:38.29–1:40.69 (2.40s)

**장면** 로우 클로즈업(손만). 몸으로 가린 오목 속 불꽃이(손은 오목 양옆 바위를 짚음) 빗속에서 몇 초에 걸쳐 낮아지다 불씨만 깜빡이고 꺼진다(순간 소멸 아님). 젖은 검은 잔가지에서 흰 김만 오른다. 옆 납작돌 위 남은 쑥 솜 뭉치가 비에 젖어 짙게 눌린다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S23
- 빛: rain · 레퍼런스: P
- 생성 4s → 사용 구간 0.000–2.400s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N30` 남은 쑥 솜도 다 젖었다.
- 오버레이: `warning_fire` (overlays.json)
- 효과음: 쉬익 — 점점 작게, 빗소리
- 끝 상태(다음 샷의 출발점): 불 꺼짐(젖은 검은 잔가지, 흰 김). 손: 오목 양옆 바위를 짚은 채 정지(손만). 납작돌 위 쑥 솜 젖어 눌림. 비.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S23 끝 프레임 · 2) 레퍼런스 P

```text
Change the camera to a low close-up a moment later of the hollow in the rain: the small fire burns low in the shadow of the figure's hunched body, the matte light-grey porcelain hands of the figure from <IMAGE_1> braced flat on the rock at either side of the hollow, white steam curling up through the falling rain, and on the small flat stone beside the hollow the two spare balls of grey-green fluff are darkening as they soak. Keep the dim grey rain light of <IMAGE_0>; only the hands and forearms appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P

```text
<IMAGE_0> is the first frame. Over a few seconds the flames sink lower and lower in the rain, shrink to a few glowing embers that blink and go dark, and only white steam is left rising from the wet black twigs; the spare fluff beside it is soaked flat. The hands stay braced on the rock either side of the hollow. Static camera. It ends with the dead, steaming fire and the hands still braced beside it. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. Over a few seconds the flames sink lower and lower in the rain, shrink to a few glowing embers that blink and go dark, and only white steam is left rising from the wet black twigs; the spare fluff beside it is soaked flat. The hands stay braced on the rock either side of the hollow. Static camera. It ends with the dead, steaming fire and the hands still braced beside it. Pace the action so that this ending is reached at about 2.1 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S25 · UNLOCK · 빗속, 손바닥 위 쇠못과 흰 돌 — 톡톡 두 번 (획득 카드) · 1:40.69–1:43.14 (2.45s)

**장면** 클로즈업(손만). 빗방울 맺힌 펼친 왼손바닥 위에 쇠못(간 면이 위)과 깨진 흰 돌. 첫 1초에 오른손 손끝이 쇠못을 두 번 톡톡(습관). 왼손 손가락이 천천히 오므려진다. 위쪽 40%는 비와 흐린 바위뿐(획득 카드 자리).

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S24
- 빛: rain · 레퍼런스: P, NAIL, FLINT
- 생성 4s → 사용 구간 0.000–2.450s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N31` 두 번째 기록. 불.
- 오버레이: `inventory_unlock` (overlays.json)
- 효과음: 톡톡 2회(쇠), 빗소리, 국악 타악 1타(획득, 톡톡 0.3초 뒤)
- 끝 상태(다음 샷의 출발점): 왼손이 쇠못과 흰 돌을 쥐고 오므려짐, 빗물이 손마디를 타고 흐름(손만).

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S24 끝 프레임 · 2) 레퍼런스 P · 3) 레퍼런스 NAIL · 4) 레퍼런스 FLINT

```text
Change the camera to a close-up a moment later in the rain beside the dead fire: the open left palm of the figure from <IMAGE_1> holds the iron nail from <IMAGE_2>, its bright ground side up, and the broken white stone from <IMAGE_3>, raindrops beading on both, with the right hand's fingertip just above the nail. Keep the dim grey rain light of <IMAGE_0>. Frame the palm in the lower half of the frame, with only falling rain and soft dark rock in the upper 40% of the frame; only the hands appear, the figure's head stays out of frame.
```

**② 영상** (`grok-imagine-video-1.5`, 4s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 NAIL · <IMAGE_3> 레퍼런스 FLINT

```text
<IMAGE_0> is the first frame. The right fingertip taps the nail twice, then the fingers of the left hand close slowly over the nail and the stone as the rain keeps falling. Static camera. It ends with the closed hand holding them, rain running over the knuckles. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear, exactly as in <IMAGE_1>; its head stays out of frame. Keep the nail's length, tapering square shank and lumpy hand-forged square head exactly as in <IMAGE_2>; its rust and any bright ground side are exactly as described above. Keep the stone's chalky white rind, dark grey glassy inside and size exactly as in <IMAGE_3>; it is whole or broken exactly as described above. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The right fingertip taps the nail twice, then the fingers of the left hand close slowly over the nail and the stone as the rain keeps falling. Static camera. It ends with the closed hand holding them, rain running over the knuckles. Pace the action so that this ending is reached at about 2.2 seconds and then held, almost motionless, until the clip ends at 4 seconds. Only the figure's slender matte light-grey porcelain hands and forearms appear,; its head stays out of frame. The nail is a hand-forged iron nail about twelve centimetres long with a tapering square shank and a lumpy square head, rusted orange-brown, with one side ground to bright grey metal only when described so. The stone is a palm-sized flint nodule with a knobbly chalky white rind; where broken it shows dark grey glassy stone with smooth curved shell-like surfaces and a thin sharp edge. Photoreal live-action look, dim grey light in a heavy passing shower, rain streaking down, the black rocks wet and glistening, the small fire the only warm light while it lasts, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S26 · NEXT · 비 갠 해 질 녘 · 꺼진 불자리 · 고양이가 나와 다리에 붙음 · 널빤지 쪽으로 고개 · 1:43.14–1:46.39 (3.25s)

**장면** 시간 점프(소나기가 지나간 해 질 녘). 와이드, 반쯤 실루엣. 흠뻑 젖은 주인공이 꺼진 불자리(젖은 재·검은 잔가지) 옆 바위에 앉아 있다. 고양이(털은 거의 마름)가 바위 밑에서 나와 다리에 몸을 붙이고 앉는다. 아래 물가에 뒤집힌 널빤지. 끝에 널빤지 쪽으로 고개.

- 연결: **T** 시간 점프(앞 끝 프레임 편집) · 출발 S25 · 참고 프레임 S23
- 빛: dusk_after_rain · 레퍼런스: P, C, PLANK_UNDER
- 생성 5s → 사용 구간 0.000–3.250s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N32` 불은 꺼졌다. 쇠못과 돌은 남았다.
- 오버레이: `time_card_dusk` (overlays.json)
- 효과음: 저녁 파도, 바위에서 듣는 물방울
- 끝 상태(다음 샷의 출발점): 비 갠 해 질 녘. 주인공: 꺼진 불자리 옆 바위에 앉음(흠뻑 젖음), 고개를 물가의 뒤집힌 널빤지 쪽으로. 고양이: 다리에 붙어 앉음(털 거의 마름). 왼손에 쇠못·흰 돌.

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S25 끝 프레임 · 2) S23 끝 프레임 · 3) 레퍼런스 P · 4) 레퍼런스 C · 5) 레퍼런스 PLANK_UNDER

```text
Change the time to dusk just after the shower has passed, the camera pulled back to a wide shot of the same shore: the figure from <IMAGE_2>, soaked through, sits on the rock beside the hollow where the fire was, now only wet black twigs and ash, its closed left hand resting on its knee; below, near the waterline, lies the overturned plank from <IMAGE_4> with its underside up, and the ginger cat from <IMAGE_3>, its fur still mostly dry, steps out from the gap under the large boulder. Both are partly silhouetted against a thin band of orange glow under the clouds low over the sea. Keep the designs exactly as in <IMAGE_2>, <IMAGE_3> and <IMAGE_4>, with the rain-wet rocks of <IMAGE_0>. Take only the hollow, the large boulder with the dry gap under it and the shoreline from <IMAGE_1>; the figure and the cat each appear only once, where described here.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 P · <IMAGE_2> 레퍼런스 C · <IMAGE_3> 레퍼런스 PLANK_UNDER

```text
<IMAGE_0> is the first frame. The cat walks over and presses its side against the figure's leg, then sits; the figure's head turns down toward the overturned plank below. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turned toward the plank, held still, the cat against its leg. Pace the action so that this ending is reached at about 3.0 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the figure exactly as in <IMAGE_1>; its head stays a smooth, blank, featureless matte porcelain egg in every frame, its surface unbroken from crown to neck. Keep the cat exactly as in <IMAGE_2>, moving like a real cat. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_3>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The cat walks over and presses its side against the figure's leg, then sits; the figure's head turns down toward the overturned plank below. Gentle waves hiss on the rocks. Static wide camera. It ends with the figure's head turned toward the plank, held still, the cat against its leg. Pace the action so that this ending is reached at about 3.0 seconds and then held, almost motionless, until the clip ends at 5 seconds. The figure has a smooth egg-shaped head of matte light-grey porcelain with no facial features, slender porcelain hands, a navy windbreaker with the sleeves pushed up, a safety-orange life vest with three black buckles and a small steel whistle on the left strap, charcoal trousers rolled to the calf and bare porcelain feet; its head stays featureless in every frame. The cat is a lean adult ginger tabby with darker stripes, a white chest and two white front paws, a small notch at the tip of its left ear and a thin braided leather collar with one small brass disc, moving like a real cat. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S27 · NEXT · 널빤지 아랫면 — 빗물 고인 홈이 또렷해짐 (EP2_END) · 1:46.39–1:49.59 (3.20s)

**장면** 클로즈업 푸시인. 뒤집힌 널빤지 아랫면, 못이 빠진 작은 사각 구멍. 얕은 홈마다 빗물이 고여 마지막 주황빛을 받고, 홈 모양이 처음보다 또렷하다 — 여전히 일부뿐이고 해초에 가려 읽을 수 없다. 해초에서 물방울 하나가 홈에 떨어져 잔물결이 지나간다.

- 연결: **A** 앵글 컷(앞 끝 프레임 편집) · 출발 S26
- 빛: dusk_after_rain · 레퍼런스: PLANK_UNDER
- 생성 5s → 사용 구간 0.000–3.200s (아웃 포인트 = 다음 샷 출발 프레임)
- 내레이션: `N33` 빗물이 고이자 홈이 또렷해진다.
- 효과음: 물방울 한 번, 낮은 앰비언트 음 1개 지속
- 끝 상태(다음 샷의 출발점): 널빤지 아랫면 홈(빗물이 고여 주황빛 반사)이 프레임 중앙에 선명. 못 구멍. 해초. (EP2_END → EP.3 S01 C 링크 base)

**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)

업로드 순서: 1) S26 끝 프레임 · 2) 레퍼런스 PLANK_UNDER

```text
Change the camera to a close-up of the underside of the overturned plank from <IMAGE_1> in the dusk light of <IMAGE_0>: the wet dark oak, the small square hole where the nail was, and the row of rough shallow grooves with rainwater standing in them, each thin line of water catching the last orange glow so the grooves stand out more clearly than before, still fragmentary and partly covered by seaweed. Keep the plank exactly as in <IMAGE_1>; only the plank, the grooves and the wet rock are in this frame.
```

**② 영상** (`grok-imagine-video-1.5`, 5s, 9:16, 720p, 오디오 끔)

이미지: <IMAGE_0> 시작 프레임(image 고정) · <IMAGE_1> 레퍼런스 PLANK_UNDER

```text
<IMAGE_0> is the first frame. The camera pushes in slowly toward the grooves; a drop of water falls from the seaweed into one groove and sends a tiny ripple along it, then the water lies still and shining. It ends with the water-filled grooves sharp in the centre of the frame. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. Keep the plank's underside and its row of rough shallow grooves exactly as in <IMAGE_1>, the grooves half hidden by seaweed and too fragmentary to read; the nail is in or out of the wood exactly as described above. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>

```text
The uploaded image is the first frame. The camera pushes in slowly toward the grooves; a drop of water falls from the seaweed into one groove and sends a tiny ripple along it, then the water lies still and shining. It ends with the water-filled grooves sharp in the centre of the frame. Pace the action so that this ending is reached at about 2.9 seconds and then held, almost motionless, until the clip ends at 5 seconds. The underside of the plank is darker, wetter oak with strands of seaweed and a short row of rough, shallow cut grooves half hidden under the seaweed, too fragmentary to read. Photoreal live-action look, dusk just after a passing shower, a thin band of orange glow under the clouds low over the sea, everything wet and in cool blue shadow, muted natural colours, realistic textures and physics, natural real-time motion, no on-screen text.
```

</details>

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임

---

## S28 · TAG · 정지 + 엔드카드 · 1:49.59–1:52.09 (2.50s)

**장면** S27 끝 프레임 정지 + 엔드카드 「표류자 EP.2」 · 기록 02 / ?. 음성 없음, 파도 소리만.

- 연결: **F** 정지 프레임 · 출발 S27
- 빛: — · 레퍼런스: 없음
- 오버레이: `endcard` (overlays.json)
- 효과음: 파도, 물방울
- 끝 상태(다음 샷의 출발점): 엔드카드.

QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · 사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임
