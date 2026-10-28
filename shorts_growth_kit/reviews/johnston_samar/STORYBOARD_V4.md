# 존스턴·사마르 해전 쇼츠 — 재구성 장면표 v4 (제안)

> **문서 성격**: 영상 생성 전 설계안이다. 이 장면표로 영상·음성을 생성하거나 시청한 적은 없다. 모든 역사 문장은 NHHC 원문 대조(`FACTCHECK_NHHC.md`) 범위 안에서 썼다.

## 0. 원안 대비 무엇이 바뀌었나

| 원안(86.7초·25컷·183단어)의 문제 | v4의 해결 |
|---|---|
| ① "왜 돌진했나"의 작동 원리가 없다. 답이 마지막 해석 문장에 걸려 있다 | C03–C04 속도 제약(≈35노트 대 17–20노트), C07 원리 도식(어뢰는 맞히지 않아도 회피를 강요하고 회피가 시간을 잃게 한다), 같은 도식을 C09(발사)·C15–C16(역할 반전)에 재사용. 답 "…buy them time"이 H-Gram 원문("buy time for the escort carriers to get their planes off the decks")에 직접 근거한다 |
| ② 첫 3초: 결말 문구 카드, 주어가 항모, 방향이 모호하다 | 첫 대사 "The carriers run. One destroyer turns toward the guns. Why?" 질문 카드는 1.0–3.4초. 결말을 미리 공개하던 카드는 삭제. 갈라지는 두 항적을 화살표로 1.2초 표시 |
| ③ 같은 선미 사선·황금 역광 반복(역광은 사실과 다름) | 황금 역광 소스를 전부 뺐다. 회색 스콜 아침으로 통일. 정면 저각, 우현 함수, 탑다운 도식, 당일 실사 사진을 번갈아 쓴다 |
| ④ 클라이맥스 붕괴(메타 대사, 2초 전환, 1943 항구 사진) | C13 재질문 "Why turn toward the guns again?", C14 갬비어 베이 유인 시도와 실패(당일 사진 80-G-287505), C15–C16 야하기 구축전대가 조기 발사(같은 원리의 재적용) |
| ⑤ 넓은 시드에서 세부 동작 요구, 발사 장면 미해결 | 발사·발포·입수 요구 0건. 발사 박자는 기존 어뢰 PNG의 부채꼴 궤적 그래픽으로 처리. Veo 7건 모두 고정 카메라에 동작 1개. 실패 시 대체안을 명기 |

수치: 86.7초 → **81.9초**, 25컷 → **21컷**, 영어 183단어 → **246단어**(구절 사이 공백을 줄여 정보 밀도를 높였다), 실사 사진은 1943 항구 사진 → **사마르 당일 사진 2장** + 결말 기록 사진 2장.

## 0-1. 만든 방법

1. **초안 3종**(Opus): A 인과 중심 · B 인물·선택 중심 · C 제작 실현성 중심.
2. **채점 3인**(Opus):

   | 렌즈 | A 인과 | B 인물 | C 실현성 |
   |---|---|---|---|
   | 훅·구조 | 8 | 6.5 | 6 |
   | 역사 정확성 | 9 | 7.5 | 8 |
   | 제작 실현성 | 7.5 | 5.5 | 8 |

3. **통합**: A를 뼈대로 B·C의 장점을 이식했다. 세션 모델이 바뀌어 있어 이 단계는 Opus가 수행했다.
4. **반박 검증 4인**: 역사 반박(major 12), 제작 반박(major 7), 「신비한 건축사전」 페르소나(major 3), 「문명」 페르소나(major 3).
5. **최종 판정(Fable)**: 57건 중 56건 반영(부분 6), 핵심 기각 1건.
6. **적대적 감사 2인(Opus) → 마감(Fable)**: 감사 major 7건을 모두 반영했다.
7. **근거 보강(오케스트레이터)**: 저장된 NHHC 원문으로 남은 사전 확인 3건을 해소했다(H-Gram "buy time…", "Heermann bluffed Yamato…", Kalinin Bay·Johnston DANFS의 야하기 구축전대). 세부 변경은 `CHANGELOG.md`에 있다.

## 0-2. 페르소나 비평 처리 (「신비한 건축사전」 × 「문명」)

| 페르소나 | 지적(major) | 처리 |
|---|---|---|
| 건축사전 | C13의 새 질문 카드가 영상을 두 편으로 가른다 | 반영. 같은 카드를 재사용하고 "AGAIN" 태그를 붙여 **첫 질문의 재질문**으로 만들었다 |
| 건축사전 | C11–C12가 8초 동안 같은 그림이다 | 반영. C12는 손상 구역 펀치인(1.35→1.50배) |
| 건축사전 | 한국어판 답이 '시간'으로 끝나지 않는다 | 반영. KO C21 "포구로 돈 이유는, 항모를 가려 벌어 준 시간이었습니다." |
| 문명 | '시간 → 함재기' 사슬이 대사에서 끊긴다 | 반영. C04 "They need time to launch planes" → C17 "Carrier planes are up." |
| 문명 | 보상 박자(C16·C18)에 숨이 없다 | 부분 반영. C16 0.4초 정적 + 히트음, C18 0.4초 바다 소리. C15 단축은 사실 문장 길이 때문에 기각 |
| 문명 | 엔딩을 "He didn't have to win — just buy the carriers time."으로 | 기각(사실 근거가 없는 의도 해석). "He'd" 제거만 반영 |

minor는 건축사전 8건(콜아웃 라벨 ≤2, 7자/초, 염료 라벨 위치, 답 순간의 "TIME" 괄호 등)과 문명 4건(승조원 행위자, 얼굴 박자의 글자량, 음악 규칙, 질문형 고정 댓글)이고 모두 반영했다. 숫자는 건축사전 편향 규칙대로 '줄이되 없애지 않았다'.

---

# Why a U.S. Destroyer Charged Yamato's Fleet / WHY TURN TOWARD THE GUNS?

81.9초 · 21컷 · EN 내레이션 246단어 · Veo 7건(+조건부 N8). 오프닝 카드는 1.0–3.4초에 상단(y12–20%)에 띄운다. 0초 프레임에는 카드를 두지 않는다. VO 질문과 같은 말을 같은 박자에 쓰고, 결말 문장은 미리 공개하지 않는다. KO 내레이션은 발화 구간 기준 ≤7.5음절/초로 맞추고, 괄호 속 영문("(Center Force)")은 자막 전용이며 TTS 입력에서 뺀다.

## 설계 논리

1. **중심 질문:** 항모가 달아날 때 왜 구축함 한 척은 포구를 향해 돌았나? 답은 '항모를 가려 벌어 준 시간'이다. 마지막 문장의 마지막 단어 "time"으로 회수한다. 근거는 MOH 인용 "consistently interposed his vessel between the hostile fleet units and our carriers" / "diverted the powerful blasts of hostile guns from the lightly armed and armored carriers"(factcheck #14)이다. 목적의 직접 근거는 H-Gram 036 원문이다(factcheck 추가 확인 A1). 에번스의 단독 어뢰 공격은 "a desperate attempt to buy time for the escort carriers to get their planes off the decks and into the battle"이었다. 사슬은 C04 필요('함재기를 띄울 시간') → C07 원리(어뢰 위협이 회피를 강요하고 회피가 시간을 잃게 한다. 실제 사례 A2: 히어먼의 어뢰 공격 시도에 야마토가 돌아서며 몇 분을 잃음) → C16 적용(조기 발사) → C17·C18 함재기 공격 속 철수다. C13에서 같은 질문을 다시 묻는다("again").
2. **공개 순서:**
   - 질문: 1.0초
   - 제약: 6.6초. 최고 속력 ≈35노트 대 ≈17–20노트, 항모가 할 수 있는 일은 함재기를 띄우는 것
   - 원리: 20.4초. 어뢰는 항로 이탈을 강요하고 그것이 곧 시간이다
   - 행동: 1만 야드 안까지 포화를 뚫고 접근(DJ 실제 행동. 발사 요건으로 단정하지 않는다)
   - 결과: 32.5초. 구마노 12노트로 낙오
   - 대가: 17노트, 승조원의 손 조타
   - 첫 질문 재질문(AGAIN) "WHY TURN TOWARD THE GUNS?": 46.3초
   - 두 번째 진입: 다른 호위함의 어뢰 공격 엄호, 갬비어 베이 쪽 포화를 끌어오려다 실패
   - 같은 원리 재적용: 53.9초. 일본 구축전대 조기 발사
   - 철수와 손실 → 답(약 81.3초) → C01로 루프
3. **핵심 선택 1:** 같은 탑다운 도식을 세 번 쓴다. C07은 이름 없는 일반 원리(중립 회색 구축함 아이콘, 궤적 5개), C09는 같은 좌표에 이름이 붙은 실제 발사(앰버, 궤적 10개), C15–16은 역할이 뒤집힌 장면이다. 그래서 시청자는 재질문의 답을 대사보다 먼저 추론한다. 발사 박자(구 C12)는 **방식 ①, 기존 어뢰 PNG 부채꼴 궤적 그래픽**으로 처리한다(이 편 C09).
4. **핵심 선택 2:** 숫자와 시계는 화면이 맡고 인과는 대사가 맡는다. 숫자 사슬은 35 → 17–20 → 12 → 17 KN, 시계는 07:20·07:30·08:45·9시 직후다. 오버레이는 자막 외에 동시 2개까지만, 칩 하나에 라벨은 2개까지만, 도식은 컷당 3단계까지만 쓴다.
5. **조명과 레지스터:** 황금 역광 소스는 쓰지 않고 회색 스콜 아침으로 새로 만든다. 실사 사진은 세 자리에만 둔다. 걸려 있던 것(C04), 실패(C14), 치른 대가(C19–20)다.
6. **보상과 대가의 박자:** 보상 박자(C10·C16)에는 0.4초 정적 + 같은 히트음을 쓰고, 최대 보상 C18에는 히트음 없이 0.4초의 바다 소리만 둔다. 대가(C19–C21)는 음악 없이 앰비언스만 쓴다.

## 묶음 구조 표

| 묶음 | 질문→관찰→작동/선택→남는 한계→다음 질문 | 컷 | 시간 |
|---|---|---|---|
| B1 질문 | **질문** 모두 달아나는데 왜 먼저 한 척이 포구 쪽으로 도나?(HO "went in to attack independently". 뒤에 다른 호위함도 따른다) → **관찰** 반대로 갈라지는 두 항적. 전함 4척·중순양함 6척 중 한 척의 거대한 전방 포탑 → **작동/선택** 돌진이라는 선택만 보인다 → **한계** 이유가 없다 → **다음** 항모는 왜 그냥 달아나지 못하나? | C01–C02 | 0.00–6.60 |
| B2 제약 | **질문** 왜 도망으로는 안 되나? → **관찰** 최고 속력 ≈35노트 대 ≈17–20노트 칩. 실사 사진: 멀리 다른 호위항모 주변에 물기둥이 서는 동안 앞쪽 비행갑판에서 와일드캣이 발진을 준비한다(캡션 원문 확인 전제) → **작동** 항모에 필요한 것은 도주가 아니라 함재기를 띄울 시간이다(HG "buy time … get their planes off the decks", A1) → **한계** 누가, 무엇으로 거대한 함대를 늦추나? → **다음** 작은 구축함의 수단은? | C03–C04 | 6.60–13.30 |
| B3 수단과 조건 | **질문** 무엇으로 늦추나? → **관찰** 명령을 기다리지 않고 연막을 피우며 돌진하는 에번스, 염료 물기둥, 5연장 발사관 2기(10발) → **작동** 어뢰는 맞히지 않아도 항로 이탈을 강요하고, 그것이 곧 시간이다(일반 원리 도식) → **한계** 존스턴은 포화를 뚫고 1만 야드 안까지 들어가야 했다(DJ 실제 행동) → **다음** 거기까지 가서 쏠 수 있나? | C05–C08 | 13.30–29.70 |
| B4 결과와 대가 | **질문** 통했나? → **관찰** 같은 도식에 이름이 붙고 10→0. 구마노 함수 파손, 12노트로 낙오(0.4초 정적). 07:30 전함 포탄 피격, 17노트로 항모와 같은 속도, 스콜 → **작동** 순양함 한 척을 추격에서 뺐다 → **한계** 어뢰 0발, 승조원의 수동 조타, 함장 부상 → **다음(재질문)** 그런데 왜 또 포구로 도나? | C09–C13 | 29.70–48.50 |
| B5 같은 원리, 두 번째 | **질문** 어뢰 없이 무엇을 할 수 있나? → **관찰** 다른 호위함들의 어뢰 공격을 엄호하고, 갬비어 베이를 겨눈 포화를 끌어오려다 실패한다(실사). 08:45 야하기가 이끄는 일본 구축전대가 어뢰 공격에 들어오고, 존스턴의 포격선과 항공기가 종대를 막는다. 종대가 항모 반대쪽으로 돌아서며 어뢰를 일찍 발사한다(도식). 항모의 함재기가 떠 있고, 폭탄 없는 조종사들도 급강하한다 → **작동** 위협만으로도 회피를 강요하고, 그것이 다시 시간이 된다 → **한계** 한 번은 실패했고, 존스턴은 계속 맞는다 → **다음** 그 시간은 무엇을 낳았나? | C14–C17 | 48.50–64.70 |
| B6 목적 회수 | **질문** 결과는? → **관찰** 9시가 조금 지나 Center Force 철수(공중 공격과 혼란). 포격에 침몰한 미군 함정 4척. 존스턴 327명 중 186명 희생. 에번스는 그날 밤 물 위에서 마지막으로 목격된다 → **작동** 시간이 함재기가 되고, 함재기의 공격 속에 Center Force가 물러난다. 첫 질문의 답은 '항모를 가려 벌어 준 시간'이다 → **한계** 대가를 숨기지 않는다 → **다음** 없음. 마지막 장면이 C01과 같은 배·같은 항적으로 루프한다 | C18–C21 | 64.70–81.90 |

## 컷 표

| ID | 시간(초) | EN 대사 | KO 대사 | 행동(화면에서 일어나는 일) | 카메라 목적 | 연결(이어받기/하드컷+이유) | 시작 이미지 | 오버레이(문구·위치) | 수단 |
|---|---|---|---|---|---|---|---|---|---|
| C01 | 0.00–3.40 (3.40) | The carriers run. One destroyer turns toward the guns. Why? | 항모는 달아납니다. 구축함 한 척은 포구로 돕니다. 왜일까요? | 존스턴이 선체를 기울이며 선회를 마치고, 함수가 우측 수평선의 적 함대를 향한다. 좌측 원경의 호위항모 2척은 작게 남는다(항적은 좌향). 두 항적이 반대로 갈라진다. | 수면 높이 저각에 고정한다(우현 선미 사분면). 갈라지는 두 항적을 한 화면에서 비교하게 해, 선택의 대비가 곧 질문이 되게 한다. | 오프닝. 첫 프레임은 검수된 N1 시작 이미지이고, 동작 중간에서 시작한다. | 새 생성 N1 [0,82) | 0.0–0.9초: 화살표 2개(화면 중단, 흰 ← 항모 항적 / 앰버 → 함수 앞). VO는 "The carriers run." 0.05–0.85초, "One destroyer turns toward the guns. Why?" 1.0–3.3초. 1.0–3.4초: 카드 "WHY TURN TOWARD THE GUNS?"(KO "왜 포구로?", 상단 y12–20%). 카드는 VO와 같은 말·같은 박자로 뜨며, 그동안 자막은 생략한다(카드가 자막 역할). 동시 오버레이는 2개를 넘지 않는다. | [새 생성]+[그래픽] |
| C02 | 3.40–6.60 (3.20) | Straight at the Center Force — four battleships, six heavy cruisers. | 곧장 중앙부대(Center Force)로 향합니다. 전함 넷, 중순양함 여섯. | 일본 중순양함이 전진한다. 카메라가 원경의 큰 전방 포탑을 찾아 멈춘다. 좌우 반전으로 적은 좌향으로 진행한다. V_C06의 함형은 ONI 222-J 묘코급·다카오급 인식도와 대조해 검수한다(연돌 배치, 연장 포탑 5기). 맞지 않으면 N8(아래 '새 생성 목록')로 교체한다. | 질문 속 "guns"의 크기를 체감시킨다. 규모 수치는 대사가 맡는다. | 하드컷. C01 함수가 가리킨 대상으로 시점을 옮긴다. | 기존 V_C06 [0,77), 좌우 반전(검수 조건부. 실패 시 N8 [0,77)) | 없음. 함명 라벨 금지(구마노가 아니다). "(Center Force)"는 자막 전용이며 TTS에서 뺀다. | [기존] |
| C03 | 6.60–9.90 (3.30) | Japan's cruisers can steam nearly twice as fast as the carriers. | 일본 순양함은 항모보다 거의 두 배 빠릅니다. | 같은 테이크를 1.3배 크롭해 하단의 함수 물살을 화면 중심에 둔다. 물살이 빠르게 밀려난다. | 포탑(C02) → 함수 물살(C03)로 정보를 바꾼다. 속도를 물살로 읽고, 숫자 칩으로 시청자가 직접 비교하게 한다. 대사는 "Japan's cruisers"로 화면 속 특정 함과 떼어 둔다. | 이어받기. 같은 테이크의 연속 구간, 크롭만 바뀐다. | 기존 V_C06 [77,156), 좌우 반전 + 1.3배 크롭(V_C06 교체 시 N8 [77,156)) | 상단 y16–26%에 칩 2줄. +0.3초 "CRUISERS · ≈35 KN MAX"(빨간 테두리) → +1.0초 "CARRIERS · ≈17–20 KN MAX"(흰 테두리). KO "순양함 · 최고 약 35노트" / "호위항모 · 최고 약 17–20노트". "MAX"는 설계 속력이라는 뜻이다. | [기존]+[그래픽] |
| C04 | 9.90–13.30 (3.40) | The carriers can't outrun them. They need time to launch planes. | 따돌릴 수는 없습니다. 함재기 띄울 시간이 필요합니다. | 당일 실제 사진. 앞쪽 호위항모 비행갑판에서 와일드캣이 발진을 준비하고, 멀리 다른 호위항모 주변에 포탄 물기둥이 솟는다(함명은 NHHC 캡션 원문 확인 뒤 확정. 사전 확인 참조). 고해상 스캔이면 물기둥에서 비행갑판의 전투기 쪽으로 느리게 패닝한다. 폭 맞춤일 때는 패닝 대신 비행갑판 전투기를 중심으로 1.00→1.06 푸시. | 시선을 "쫓긴다"(물기둥)에서 "함재기를 띄울 시간"(발진 준비)으로 옮긴다. 답의 단어 '시간'을 여기서 처음 심는다. | 하드컷 + 레지스터 전환(실사 1: 걸려 있던 것). | 외부 자료 80-G-287497(USN, 퍼블릭 도메인). 캡션이 발진 준비를 뒷받침하지 않으면 factcheck #16(c)의 80-G-288886·80-G-288889 중 캡션이 확인된 사진으로 교체 | 출처 칩(좌, y56–60%) "ESCORT CARRIER UNDER FIRE · 25 OCT 1944 · USN 80-G-287497". 캡션 확인 뒤 함명을 넣을 수 있다. | [외부 자료] |
| C05 | 13.30–17.10 (3.80) | Commander Ernest Evans doesn't wait for orders. He makes smoke and charges. | 에번스 함장은 명령을 기다리지 않고, 연막을 피우며 돌진합니다. | 존스턴이 우현 함수 15° 각도로 카메라 쪽에 돌진한다. 함수파가 솟고, 중심선 앞뒤로 선 두 연돌의 검은 연기가 함 뒤와 화면 좌측으로 낮은 벽을 이루고, 함미 쪽에 흰 화학 연막이 섞인다. 양현 멀찍이 서 있던 분홍·황록 물기둥이 천천히 무너져 내린다(새 물기둥은 요구하지 않는다). | 수면 높이, 우현 함수 15° 저각에 고정한다. 함수가 관객 쪽으로 오며 결단의 방향을 보여 주고, 연막 벽이 함 뒤로 읽히게 하며, 선미 사선 구도의 반복을 끊는다. | 하드컷. "시간이 필요하다" 다음에 그 시간을 벌 주체가 등장한다. | 새 생성 N2 [0,91) | 상단 y16–22% 같은 자리에 순서대로. 0.2–2.0초 "USS JOHNSTON · CDR. EVANS"(KO "존스턴 · 에번스 함장"). 분홍 물기둥이 가장 높이 서 있는 프레임(생성본에서 확인. 시작 상태가 이어지므로 보통 0.2–1.0초 사이 시작, 0.6초)에 그 옆(x85% 안쪽)에 얇은 흰 링 + 라벨 "DYE-MARKED SHELLS"(KO "색 염료 포탄")를 붙이고 물기둥이 무너지기 전에 페이드한다. 칩과 동시여도 오버레이는 2개다. 링은 지시선 금지 규칙의 허용 대체다. | [새 생성]+[그래픽] |
| C06 | 17.10–20.40 (3.30) | Johnston's guns can't stop a heavy cruiser. Her ten torpedoes might. | 함포로는 순양함을 못 멈춥니다. 어뢰 열 발이라면 모를까. | 5연장 발사관의 정지 구도. 닫힌 캡 5개가 보이고, 너울만 움직인다. | 고정. 캡을 셀 수 있게 해 수단을 식별시킨다. | 하드컷. "무엇으로?"에 답한다. | 기존 V_C10_V2 [0,79) | 상단 y14–24%: 어두운 반투명 판 위에 기존 어뢰 PNG와 "TORPEDOES · 5 × 2"(KO "어뢰 · 5 × 2"). 흰 링 5개가 '5'를, ×2가 보이지 않는 두 번째 발사관을 맡는다. 0.3–2.5초에 캡 5개를 얇은 흰 링으로 강조. 지시선과 단독 "TORPEDO" 카드는 쓰지 않는다. | [기존]+[그래픽] |
| C07 | 20.40–25.90 (5.50) | A torpedo doesn't have to hit. To dodge one, a ship must swing off course — and that costs time. | 어뢰는 맞히지 않아도 됩니다. 피하려면 배는 항로를 벗어나야 하고, 그만큼 시간을 잃습니다. | C06 마지막 프레임을 정지하고 채도를 −60% 낮춘 뒤 탑다운 도식 S2를 띄운다(좌표는 공통 사양). 3단계만 쓴다. ① 0.3–1.8초: 빨간 순양함 아이콘이 시작점(x72% y30%)에서 점선 예상 진로를 따라 흰 항모 아이콘(x20% y54%)에 다가간다. ② 1.8–2.8초: 이름 없는 **중립 회색 외곽선** 구축함 아이콘(x46% y44%)에서 흰 궤적 5개가 0.8초 동안 부채꼴로 진로를 가로지른다. ③ 2.8–4.6초: 순양함 진로가 꺾여 비켜 간다(명중 없음). 그 사이에 흰 점선 "TIME" 괄호가 나타나 벌어진다. 4.6–5.5초는 정지. 함명 없는 일반 원리 도식이며, 앰버와 10발은 C09에서 처음 쓴다. | 위에서 내려다보며 원리를 눈으로 추론하게 한다. 그림이 대사보다 약 0.3초 먼저 움직인다. | 이어받기. 실사 정지 프레임 위에 패널을 얹는다. | 기존 V_C10_V2 f78 정지 + 그래픽 | 패널 y18–60%. 첫 등장이므로 일반명 1단어 라벨만 붙인다. 0.3초 "CARRIER"(흰 옆)·"CRUISER"(빨강 옆), 1.8초 "DESTROYER"(회색 옆), 3.0초에 셋 다 0.2초 페이드(KO "항모"/"순양함"/"구축함"). 패널 우하 소형 태그 "EXAMPLE · NOT TO SCALE". 패널 밖 오버레이는 없다. | [그래픽] |
| C08 | 25.90–29.70 (3.80) | So Johnston closes to within ten thousand yards — under fire. | 존스턴은 1만 야드 안까지 다가갑니다. 포화 속으로요. | 같은 돌진 테이크의 후반. 함수가 화면 하단을 채울 만큼 커지고, 무너진 물기둥의 거품이 양현에 남으며, 연막 벽이 뒤에 남는다. | C05와 같은 우현 함수 15° 저각 고정. 커지는 함수로 거리를 좁히는 대가(노출)를 보인다. | 하드컷. 도식에서 실사로 돌아온다. C05와 같은 원본의 뒤 시간이라 같은 배·같은 축으로 복귀한다. | 새 생성 N2 [101,192) | 우상단(x55–83%, y14–20%) 칩 "≈10,000 YD". 대사의 "ten thousand"에 맞춰 등장. | [새 생성]+[그래픽] |
| C09 | 29.70–32.50 (2.80) | She fires all ten at the cruiser Kumano. | 존스턴은 순양함 구마노를 향해 열 발을 모두 쏩니다. | **발사 박자는 방식 ①, 기존 어뢰 PNG 부채꼴 궤적 그래픽이다.** N2 마지막 프레임을 0.2초 정지·탈색한 뒤 C07 마지막 화면과 같은 좌표의 S2 패널을 띄운다. ① 흰 항모 아이콘(x20% y54%)은 라벨 없이 유지 ② x46% y44%의 구축함 아이콘이 앰버로 바뀌고 "JOHNSTON" ③ 순양함 시작점(x72% y30%)에 빨간 "KUMANO"(연돌 1개 실루엣). 0.6–1.4초에 흰 궤적 10개가 C07과 같은 부채꼴 각도로 뻗고, 끝에 축소한 어뢰 PNG가 붙는다. JOHNSTON 옆 숫자가 궤적 하나마다 1씩 10→0으로 준다. 명중은 그리지 않는다. 사운드는 짧은 화약 임펄스 사출음 10회(약 0.08초 간격, 궤적 하나마다 1회) 또는 저음 펄스 10회. 실사 무기 방출은 없다. | C07에서 배운 그림이 같은 자리에서 이름을 달고 실제로 일어난다(원리에서 적용으로). | 이어받기(정지 프레임 → 도식). 끝은 KUMANO 아이콘 위치(x72% y30%)에서 그래픽 매치 하드컷. | N2 f191 정지 + 그래픽 + 기존 어뢰 PNG | 상단좌 시계 "≈07:20"(x6–30%, y12.5–16%, 패널과 겹치지 않음). 패널 안에는 함명 2개와 숫자, 우하 소형 "NOT TO SCALE"만 둔다. | [그래픽] |
| C10 | 32.50–35.90 (3.40) | One does hit. Kumano limps out of the chase. | 한 발은 실제로 맞습니다. 구마노는 추격에서 빠집니다. | 모가미급 구마노(트렁크형 대형 연돌 1개, 연장 포탑 전방 3기·후방 2기)가 함수를 약간 앞으로 숙인 채 감속한 속도로 꾸준히 나아간다. 부서진 함수 주변에 중간 정도의 물살, 앞갑판에서 연기가 나고, 배는 떠 있다. 정확한 절단선은 주장하지 않는다. 함수 파손은 화면이, 12노트는 칩이 맡는다. "chase" 뒤 0.4초 정적 + 음악 히트(첫 성과의 보상). | 높은 측면 원경 고정. 함형, 손상, 감속을 한 화면에서 읽게 한다. 대사는 C07의 원리("맞히지 않아도 된다")와 실제 결과(맞았다)를 명시적으로 잇는다. | 하드컷(그래픽 매치·생략 편집). 시작 이미지에서 함체가 화면 우상(S2 좌표 x72% y30%)에 좌향으로 놓이므로 크롭 없이 매치한다. 명중 순간과 폭발은 만들지 않는다. | 새 생성 N3 [0,82) | 좌상 x8–50%, y14–24%에 칩 1줄 "KUMANO · 12 KN"(KO "구마노 · 12노트"). C03의 ≈17–20 KN보다 느려졌다는 것을 시청자가 읽는다. 시계는 쓰지 않는다. | [새 생성]+[그래픽] |
| C11 | 35.90–39.10 (3.20) | Minutes later, heavy battleship shells — probably Yamato's — hit Johnston. | 전함 포탄이 존스턴을 찢습니다. 아마 야마토입니다. | 손상된 존스턴(제2연돌 뒤 후부 보일러실 구역에서 솟는 검은 연기와 증기, 그을리고 찌그러진 후부 상부 구조)이 스콜 속을 감속했지만 꾸준한 속도로 나아간다. 가는 비가 화면을 가로지르지만 함은 화면 중간 1/3을 채우며 또렷이 보인다. | 우현 함수 사분면 저각 고정. 함수 쪽 근접 사분면에서 손상을 관찰한다. '몇 분 뒤'는 시계 07:20 → 07:30이 맡는다. | 하드컷 + 시계. 시간이 점프한다. 피격 순간과 포탄 궤적은 만들지 않는다. | 새 생성 N4 [0,77) | 상단좌 시계 "≈07:30" | [새 생성]+[그래픽] |
| C12 | 39.10–43.90 (4.80) | Evans loses fingers. Johnston is down to seventeen knots — no faster than the carriers. | 에번스는 손가락을 잃습니다. 존스턴은 이제 항모만큼 느립니다. | 같은 원본의 펀치인. 1.35배 크롭(중심: 제2연돌 뒤 손상 구역과 연기)에서 4.4초 동안 1.35→1.50배로 느리게 돌리 인하고, 마지막 0.4초(빗소리만)는 정지한다. 얼굴·재연 없이 다친 배를 가까이 본다. | 같은 축 펀치인(와이드 C11 → 손상부 C12). 얼굴, 함교 내부, 부상 재연은 없다. 마지막 0.4초는 관찰과 숨 고르기다. 크롭 화질이 버티지 못하면 41.3–43.9초를 S2 레이아웃 미니 도식(앰버 점선 존스턴 아이콘과 흰 항모 아이콘이 같은 길이의 속도 화살표로 나란히 간다)으로 교체한다. | 하드컷(같은 원본·같은 축 펀치인) | 새 생성 N4 [77,192), 1.35→1.50배 크롭 | 상단 y16–22%: "seventeen"에 맞춰 앰버 칩 "JOHNSTON · 17 KN"(KO "존스턴 · 17노트". 숫자 사슬 35 → 17–20 → 12 → 17). 스콜 칩은 쓰지 않는다(C11의 비와, 함미에 걸린 스콜 가장자리를 벗어나는 C13이 맡는다). | [새 생성]+[그래픽] |
| C13 | 43.90–48.50 (4.60) | No torpedoes. Her crew steers by hand. Why turn toward the guns again? | 어뢰는 없고, 승조원이 키를 돌립니다. 왜 또 포구로 돌까요? | C01과 같은 수면 저각 자리(우현 선미 사분면). 손상된 존스턴이 기울어진 선회를 마치며 함미에 걸린 스콜 가장자리를 벗어나, 우측 수평선의 적 함대 쪽으로 다시 나아간다. 발화 배분: 앞 문장 0.05–2.2초(EN 7단어 ≈3.3단어/초, KO 15음절 ≈7.0음절/초), 질문 2.4–4.2초, 질문 뒤 0.4초 침묵(4.2–4.6초). KO의 '손으로'는 EN과 DJ 근거가 맡고 자막에만 "(손으로)"를 보조로 둘 수 있다. | C01과 같은 카메라 자리로 돌아와 첫 선회와 각운을 이룬다. 화면이 먼저 "다시 간다"를 보여 주고, 대사가 같은 질문을 다시 묻는다. 승조원이 행위자로 처음 등장한다(DJ "Steering had to be done manually"). | 하드컷. 같은 화면 문법으로 돌아와 두 장면을 비교하게 한다. 새 질문이 아니라 첫 질문의 재질문이므로 영상이 두 편으로 갈라지지 않는다. | 새 생성 N5 [0,111) | 0.0–0.8초: 앰버 → 화살표(C01과 같은 스타일, 함수 앞). 2.4–4.2초: C01 카드를 그대로 재사용 "WHY TURN TOWARD THE GUNS?"(KO "왜 또 포구로?") + 우측 앰버 소형 태그 "AGAIN"(KO "또"). 그동안 질문 자막은 생략. 상태 스택과 텍스트 칩은 쓰지 않는다. | [새 생성]+[그래픽] |
| C14 | 48.50–53.90 (5.40) | She covers the other escorts' torpedo run, then tries to draw fire off Gambier Bay. It fails. | 다른 호위함의 어뢰 공격을 엄호하고, 갬비어 베이의 포화를 끌어오려 합니다. 실패합니다. | 당일 실제 사진. 불타며 포탄 물기둥에 둘러싸여 낙오하는 갬비어 베이와, 수평선에 희미한 일본 순양함(위치는 캡션 원문과 스캔으로 확인)이 있다. 처음부터 갬비어 베이와 순양함이 모두 들어오는 최소 크롭(폭 맞춤의 1.3배 이내)으로 고정하고, 둘의 중간점을 중심으로 1.00→1.06 푸시한다. "fails" 뒤 0.4초 정지. | 누가 누구를 쏘는지 관객이 찾게 하고, 실패를 기록으로 정직하게 보인다. 재진입의 첫 목적(다른 호위함 엄호, 약 0750)과 0830의 실패를 한 컷에 담는다. | 하드컷 + 레지스터 전환(실사 2: 실패). 이 사진이 존스턴의 유인 시도 순간이라고, 또 사진 속 순양함이 0830의 그 순양함이라고 주장하지 않는다. | 외부 자료 80-G-287505 | 출처 칩(좌, y56–60%) "USS GAMBIER BAY UNDER FIRE · 25 OCT 1944 · USN 80-G-287505"는 컷 전체. "Gambier Bay"에 맞춰 갬비어 베이에 얇은 흰 원(라벨 없음)을 띄우고, 순양함 원이 뜨기 0.2초 전에 0.2초로 페이드아웃한다. "fails" 뒤 정지 구간에 수평선 순양함에 얇은 흰 원(라벨 없음, NHHC 캡션 "Note Japanese cruiser, barely visible" 근거, x85% 안쪽 유지). 동시 오버레이는 어느 순간에도 출처 칩 + 원 1개 = 2개다. | [외부 자료]+[그래픽] |
| C15 | 53.90–56.90 (3.00) | A Japanese destroyer squadron closes in to torpedo the carriers. | 일본 구축전대가 항모에 어뢰를 쏘려고 다가옵니다. | 도식 S3. S2와 같은 좌표이고, 직전 사진을 흐리고 어둡게 깐 위에 남색 85% 패널을 얹는다. 빨간 종대(한 단계 큰 선두 아이콘 = 경순양함 야하기 + 구축함 아이콘 4척. KB DANFS 척수)가 우측 시작점(x72% y30%)에서 항모 아이콘(x20% y54%)으로 다가오고, "TIME" 괄호가 다시 나타나 줄어든다. 그 사이에 앰버 존스턴 아이콘(x46% y44%, 점선 외곽 = 손상)이 있다. | C07과 같은 탑다운 시점. 같은 원리를 역할만 바꿔 보여 줄 준비다. | 하드컷 + 시계. 약 15분 점프. | 그래픽(배경: 80-G-287505 블러·암전) | 상단좌 시계 "≈08:45". 패널 우하 소형 "NOT TO SCALE". | [그래픽] |
| C16 | 56.90–61.50 (4.60) | Under Johnston's guns and strafing planes, they turn away — and fire too early. | 존스턴과 항공기가 막아섭니다. 구축전대는 돌아서며 어뢰를 일찍 쏩니다. | 도식 3단계. ① 0.0–1.4초: 앰버 아이콘에서 종대를 향한 얇은 포격선 2–3개가 짧게 깜박이고, 흰 항공기 아이콘 하나가 종대를 가로지른다(SA "Johnston's furious fire and strafing"). ② 1.4–2.6초: 선두 아이콘이 진행 방향 오른쪽(우현)으로 90° 꺾고 종대가 따라 돌아 항모에서 멀어진다(DJ Hagen 회고 "a 90-degree turn to starboard"). ③ 2.6–3.8초: 먼 거리에서 짧은 빨간 궤적이 나와 항모에 닿기 전에 흐려지고, "TIME" 괄호가 멈춘다. 3.8–4.6초는 정지. "too early" 뒤 0.4초 정적 + C10과 같은 히트음(보상 신호의 반복 학습). "TIME" 괄호가 멈추는 시점은 이 0.4초의 시작에 맞춘다. 흐려지는 궤적은 '조기 발사'의 개념 표현이며, 실제 항적을 재현한 것이 아니다. | 시청자가 C07의 "꺾임"을 알아보고 재질문의 답을 스스로 추론한다. | 이어받기(도식 연속) | 그래픽 | 추가 라벨 없음. "LAUNCHED TOO EARLY" 라벨, 기총 점선은 뺀다. ①의 포격선은 라벨 없는 선 하나짜리 요소로 센다. | [그래픽] |
| C17 | 61.50–64.70 (3.20) | Carrier planes are up. Some with no bombs keep diving. | 함재기가 떠 있습니다. 폭탄 없는 조종사들도 급강하합니다. | TBM 어벤저가 우측 수평선의 순양함을 향해 기수를 내리며 급강하에 들어간다. 투하와 발포는 없다(더미 공격). | 기체 옆을 같은 거리에서 동행하며 수평선을 유지한다. 무장 없는 위협이 회피를 강요하는 세 번째 사례이고, C04의 "함재기를 띄우는 수밖에"가 낳은 결과(함재기가 떠 있다. #11·#12)를 대사로 잇는다. | 하드컷(도식에서 실사로 전환). 08:45와 9시의 두 사건 사이를 시각적으로 갈라 준다. | 새 생성 N6(A06 시드). 급강하 진입이 보이는 77프레임 | 없음 | [새 생성] |
| C18 | 64.70–69.70 (5.00) | A little after nine, under air attack and in confusion, the Center Force breaks off. | 9시가 조금 지나, 공중 공격과 혼란 속에 중앙부대(Center Force)가 물러납니다. | C02와 같은 적 순양함이 비스듬히 돌아서기 시작하고, 항적이 넓게 휜다. 선회 도중에 끝난다. "breaks off" 뒤 0.4초는 히트음 없이 선회 항적과 바다 소리만 남긴다(최대 보상이지만 승리를 두드리지 않는다). | 높은 측면 고정. 선회 궤적을 읽게 한다. C02의 접근과 대칭을 이루는 북엔드다. | 하드컷. 급강하의 목표에서 그 함대의 반응으로 넘어간다. | 새 생성 N7(A02 좌우 반전 시드). 선회 호가 가장 잘 읽히는 120프레임 | 상단좌 시계 "JUST AFTER 09:00". "(Center Force)"는 자막 전용이며 TTS에서 뺀다. | [새 생성]+[그래픽] |
| C19 | 69.70–74.10 (4.40) | Four American ships are sunk by gunfire. Johnston is one of them. | 미군 함정 네 척이 포격에 침몰합니다. 존스턴도 그중 하나입니다. | 존스턴 1943년 전체 사진(원본 톤)을 1.00→1.05로 느리게 푸시한다. 하늘 영역의 반투명 판 위에 손실 목록이 침몰 시간순으로 한 줄씩 쌓인다. 0.4·0.8·1.2초 함명 3개(회색 소형) → "Johnston"(약 2.3초)에 JOHNSTON 줄. 대사 뒤 0.5초는 관찰 시간이다. 음악은 이 하드컷에서 끊고, 이후 바다·바람 앰비언스만 쓴다. | 이름을 읽을 시간을 준다. VO는 수와 원인(포격. 가미카제로 잃은 세인트 로는 세지 않는다)을, 화면은 이름을 맡는다. | 하드컷 + 레지스터 전환(실사 3: 치른 대가) | 기존 NH63495(식별·캡션 날짜는 사전 확인) | 판 y14–40%(공통 사양의 예외. 판 하단은 사진 속 마스트 꼭대기보다 위): HOEL / GAMBIER BAY / SAMUEL B. ROBERTS(회색 소형) / "JOHNSTON · 186 OF 327 LOST"(KO: "존스턴 · 327명 중 186명 전사·실종"). 헤더와 침몰 시각은 쓰지 않는다(시계 4회 규칙, C18 직후의 순서 혼동 방지). 출처 칩 "USS JOHNSTON · 1943 · NH 63495"(캡션이 날짜를 주면 그대로 쓴다) | [기존]+[그래픽] |
| C20 | 74.10–77.50 (3.40) | Evans was last seen in the water that night. | 에번스는 밤바다에서 마지막으로 목격됐습니다. | 에번스 공식 초상, 원본 톤. 아주 느리게 푸시한 뒤 정지한다. 앰비언스만. | 처음이자 유일하게 얼굴을 보인다. 재연 없이 기록으로만. 시선이 글자가 아니라 얼굴로 가도록 칩은 한 줄만 쓴다. | 하드컷(배에서 사람으로) | 기존 NH92320(에번스 식별은 사전 확인. 캡션이 Evans를 명시하지 않으면 MOH 페이지 게재 초상과 그 카탈로그 번호로 교체) | 0.3초부터 상단 y14–24%에 한 줄 "CDR. ERNEST E. EVANS · MEDAL OF HONOR"(KO "어니스트 에번스 중령 · 명예훈장"). "미 해군 최초의 아메리카 원주민 수훈자"(HG)는 설명란과 고정 댓글로 옮긴다. 출처 칩(좌, y56–60%) "NH 92320". 칩이 얼굴과 겹치는지 사전 확인. | [기존]+[그래픽] |
| C21 | 77.50–81.90 (4.40) | He turned toward the guns to shield the carriers — and buy them time. | 포구로 돈 이유는, 항모를 가려 벌어 준 시간이었습니다. | 오프닝 원본의 후반. 선회를 마친 존스턴이 우측 수평선의 적 함대를 향해 멀어지고, 좌측 원경의 항모는 작게 남아 있다. 마지막 프레임을 0.40초 정지한다. 앰비언스만 남기고, 그 수면음을 C01 첫 프레임으로 이어 루프한다. | 답을 첫 장면의 연장 위에 놓는다. 과거 시제와 화면이 같은 '그때'를 가리킨다. 근거는 MOH "interposed his vessel between the hostile fleet units and our carriers"(가림)와, C07의 원리 → C16 조기 발사 → C17·C18 함재기 공격 속 철수(#8·#11·#12)로 이어진 사슬(시간)이다. | 하드컷(초상 → 오프닝 원본의 뒤 시간). "time" 뒤 0.5초 여운을 두고, 같은 배·같은 항적의 C01("The carriers run.")로 루프. | 새 생성 N1 [96,192) + f191 정지 0.40초 | 약 3.1–3.9초(발화 "time"에 맞춰 완성)에 흰 점선 괄호(라벨 없음, y30–50%)를 존스턴 항적과 좌측 원경 항모 사이에 0.8초 성장선으로 펼친다. 4.2초까지 유지하고 4.35초까지 페이드아웃해, 정지 마지막 프레임은 깨끗한 루프 프레임으로 남긴다. KO판은 '시간이었습니다'에 같은 박자로 맞춘다. | [새 생성]+[그래픽] |

**그래픽·오버레이 공통 사양**
- **안전 영역:**
  - 카드와 칩은 y12–28%에 둔다. 출처 칩은 좌측 y56–60%에 고정한다. 자막은 y62–70%에 둔다.
  - 예외: C19 손실 목록 판만 y14–40%. 판 하단은 사진 속 마스트 꼭대기보다 위에 둔다. 맞지 않으면 사진을 y34–76%로 내리고, 자막과 겹치는 구간은 블러 확장부로 처리한다.
  - y72% 아래와 x85% 이상은 쓰지 않는다. 0초 프레임에는 카드를 두지 않는다.
- **밀도 상한:**
  - 오버레이는 자막을 빼고 동시에 2개까지만 쓴다. 같은 자리의 칩은 순서대로 바꿔 띄운다.
  - 같은 대상을 가리키는 같은 모양의 묶음(C06 캡 링 5개, C16 포격선 2–3개)은 1개 요소로 센다.
  - 칩 하나에 라벨은 2개까지만 둔다. 정밀 숫자(속도 사슬, 186/327)는 남기고 나머지는 보조 라벨로 내리거나 뺀다.
  - 도식은 컷당 3단계까지만 쓴다. 성장선은 0.8초다.
  - 질문 카드가 떠 있는 동안에는 같은 뜻의 질문 자막을 생략한다.
- **색 체계(화살표·도식 공통):**
  - 항모: 흰/회색
  - 존스턴: 앰버. 손상 후에는 점선 외곽
  - 중립(일반 원리 예시, C07만): 회색 외곽선. 앰버는 쓰지 않는다
  - 일본 함: 빨강
  - 항공기: 흰 아이콘
  - 미군 어뢰 궤적: 흰 선, 일본 어뢰 궤적: 빨간 선
  - "TIME" 괄호: 흰 점선
  - 실루엣만 쓰고 국적 문양은 넣지 않는다.
- **도식 패널:**
  - S2(C07·C09)는 실사 정지 프레임 위에 반투명 남색 70%를 얹는다. S3(C15·C16)는 블러 처리한 사진 위에 남색 85%를 얹는다.
  - 좌표 고정(S2·S3 공통): 패널 y18–60%. 항모(흰) x20% y54%, 존스턴/중립 구축함 x46% y44%, 적함 시작점(빨강) x72% y30%. 시계 칩은 x6–30% y12.5–16%로 패널에 닿지 않는다.
  - S2와 S3는 레이아웃과 아이콘이 같고 역할만 바뀐다. 모두 패널 우하에 소형 "NOT TO SCALE" 태그를 단다. 일반명 라벨(CARRIER/CRUISER/DESTROYER)은 첫 등장인 C07에만 쓴다.
  - C07은 함명 없는 일반 원리이고, 특정 적함이 존스턴 어뢰를 회피했다고 주장하지 않는다. 그래서 C07의 발사 아이콘은 회색이고 궤적은 5개다.
- **시계 칩:** 상단좌 고정 위치, 같은 서체, 0.2초 페이드. ≈07:20, ≈07:30, ≈08:45, JUST AFTER 09:00 네 번만 쓴다. 손실 목록에는 시각을 쓰지 않는다.
- **사운드:**
  - 히트음은 C10과 C16 두 번만 쓴다(같은 소리). C18의 0.4초는 바다 소리만.
  - 음악은 C19 하드컷에서 끊는다. C19–C21은 바다·바람 앰비언스만 쓴다. C21의 "time" 뒤 여운과 정지 0.40초도 앰비언스만 남기고, 그 수면음을 C01 첫 프레임으로 이어 루프한다. 슬픈 현악 스웰은 쓰지 않는다.
- **실사 사진:**
  - 원본 톤을 유지하고 컬러화하지 않는다.
  - 고해상 스캔이면 9:16으로 크롭해 패닝한다. 불가능하면 폭에 맞추고 위아래를 같은 사진의 블러로 확장한다. 폭 맞춤일 때는 패닝 대신 목표 중심 1.00→1.06 푸시를 쓴다(C04 목표: 비행갑판 전투기, C14 목표: 갬비어 베이와 순양함의 중간점).
- **KO판:** 같은 위치에 한국어 칩과 카드를 쓴다. 예: "왜 포구로?"(C01), "왜 또 포구로?" + "또"(C13), "327명 중 186명 전사·실종". '포구로 돌다'를 질문·재질문·답(C01·C13·C21)에서 같은 말로 쓴다. KO 내레이션은 발화 구간 기준 ≤7.5음절/초, 괄호 속 영문은 TTS에서 뺀다.

## 새 생성 목록

공통 설정: veo-3.1-fast, 8초, 9:16, 1080p, 첫 프레임 PNG 1장, 무음. 새 시작 이미지는 Veo에 넣기 전에 정지 상태로 검수한다(함형, 조명, 좌우 방향, 폰 크기에서의 판독). 모더레이션 차단은 문구를 바꾸거나 다른 공급자로 우회해 다시 요청하지 않고 바로 대체안으로 간다. 무기 방출, 명중, 발포, 어뢰 입수는 어떤 요청에도 넣지 않는다. 우선순위는 N1 > N2 > N4 > N5 > N3 > N7 > N6 > N8(조건부)이다. N5 시작 이미지는 N1 시작 이미지가 승인된 뒤에 만든다. 새 생성 7건은 N1–N7이고, N8은 V_C06/A02가 함형 검수를 통과하지 못할 때만 추가한다.

### N1 — 오프닝 선회 (C01, C21)
- **사용 구간:** [0,82) → C01. [96,192) + f191 정지 0.40초 → C21. [82,96)은 버퍼.
- **시작 이미지(새):**
  > A low camera just above the waves off the starboard quarter of a single gray 1944 U.S. Fletcher-class destroyer heeling to port, away from the camera, in a hard starboard turn, its bow swinging toward the right of the frame and its curved white wake arcing behind it. Farther back on the left, two small flat-deck escort carriers steam away toward the left edge, their straight wakes pointing the other way. On the right horizon, low dark silhouettes of a battleship and cruiser fleet under a uniform grey sky. Grey overcast morning, low cloud, a dark rain squall on the far left, soft even light from behind the camera. Vertical 9:16 photorealistic frame, restrained documentary color.
  - negative: `golden sunset, sunrise glow, bright sun or glare behind the distant fleet, lens flare, fire, explosion, flags, insignia, hull numbers, text, logos, extra destroyers, cartoon`
  - 검수 항목:
    - 연돌이 2개인가
    - 우현과 선미가 보이고 함수가 화면 우측을 향하는가
    - 두 항적이 반대 방향인가
    - 일본 함대 쪽에 태양과 역광이 없는가
    - 폰 크기에서 방향이 읽히는가
  - 승인된 이 이미지가 N5 편집의 기준이 된다.
- **Veo:**
  > The destroyer finishes its heeling turn and drives on toward the dark ships on the right horizon, its wake curling into a clear arc behind it. The two small carriers stay small and distant on the left. The camera holds still just above the water. Ends with the destroyer heading away toward the distant fleet and the carriers small on the left.
  - negative: `camera orbit, camera pan, background rotation, ship morph, ship duplication, extra destroyers, reversed wake, carriers moving right, carriers changing heading, carriers turning toward the fleet, fire, explosion, sun glare, golden sky, text, graphics, HUD`
- **변경:** A안의 카메라 드리프트를 뺐다. 선회와 이어지는 전진을 한 동작으로 묶었다. 움직이는 주체는 구축함 하나뿐이고, 항모의 진행 방향은 시작 이미지의 좌향 항적과 C01의 흰 ← 화살표가 맡는다.
- **실패 시:**
  - C01 → V_C01[0,69)를 0.85배속(81프레임, 3.38초)으로 쓰고 f68을 1프레임 정지해 3.40초를 채운다. 조건부 차선이다. 상단을 크롭해 수평선의 적 함대와 태양 구역을 제거하고, 쿨 그레이로 그레이딩하고, 화살표를 유지할 때만 쓴다.
  - C21 → C20 초상을 7.8초로 늘려 마지막 문장까지 얹고(A 원안 구조), 0.5초 여운 뒤 루프한다. "TIME" 괄호는 쓰지 않는다.

### N2 — 정면 돌진과 염료 물기둥 (C05, C08, C09 정지 프레임)
- **사용 구간:** [0,91) → C05. [101,192) → C08. f191 정지 0.2초 → C09 도입. [91,101)은 버퍼.
- **시작 이미지(새):**
  > Water-level view slightly off the starboard bow (about 15 degrees) of a gray 1944 U.S. Fletcher-class destroyer charging toward the camera, a high white bow wave curling off its stem. Its two funnels stand one behind the other on the centerline and pour thick black funnel smoke that trails back into a low wall across the sea behind it and off to the left of the frame, mixed with white chemical smoke astern. Two tall columns of spray stand in the water well off its bows, one tinted pink and one pale green-yellow. Grey overcast morning, low cloud, a rain squall on the horizon, soft diffuse light. Vertical 9:16 photorealistic frame.
  - negative: `explosion on the ship, fire, hull damage, muzzle flash, golden sunset, sun glare, flags, insignia, hull numbers, text, extra funnels, side-by-side funnels, cartoon`
  - 검수 항목:
    - 연돌 2개가 중심선 앞뒤로 보이는가
    - 연막 벽이 함 뒤로 읽히는가
    - 폰 크기에서 분홍과 황록이 구분되는가
- **Veo:**
  > The destroyer drives toward the camera at a slight angle, its bow wave climbing and spray sheeting off the stem. The pink and green-yellow columns of spray already standing well off its bows hang for a moment and slowly fall back into the sea. The camera holds still at water level. Ends with the bow filling the lower half of the frame and the smoke wall trailing behind it.
  - negative: `new columns of spray, new splashes, hit on the ship, explosion, fire, muzzle flash, gun firing, spray landing on the deck, ship morph, extra funnels, side-by-side funnels, camera orbit, camera movement, sudden cut, golden sky, sun glare, text, graphics`
- **변경:** A안의 카메라 후퇴와 "물기둥이 점점 가까이" 진행 요구를 뺐다. 동작은 함의 전진 하나이고, 물기둥은 시작 이미지의 '서 있는' 상태를 이어 무너지는 서술로만 둔다(새 물기둥이 솟는 두 번째 동작은 요구하지 않는다). C05 염료 링은 생성본에서 분홍 물기둥이 가장 높은 프레임에 맞춘다. 거리가 좁혀지는 느낌은 고정 카메라 쪽으로 다가오는 함수가 맡는다. 정면 시점 대신 우현 함수 15°로 바꿔 연돌 2개와 연막 벽이 읽히게 했고, "shell splashes"는 모더레이션 회피를 위해 "columns of spray"로 썼다.
- **실패 시:**
  - 시작 이미지가 승인됐으면 그 정지 이미지를 쓴다.
    - C05: 느린 푸시 1.00→1.08
    - C08: 1.25배 크롭 + 칩
    - C09: 같은 정지 프레임
  - 시작 이미지가 차단되면 V_C11을 쓴다. 조건부 차선이며, 수평선과 하늘을 크롭하고 쿨 그레이로 그레이딩할 때만 쓴다. 길이 배분: C05 = V_C11[0,56)(2.33초) 뒤에 f55를 1.47초 정지하고 정지 구간에 1.00→1.05 푸시. C08 = V_C11 f55 정지를 1.25배 크롭하고 1.00→1.06 푸시와 "≈10,000 YD" 칩(3.80초). C09 = V_C11 f55 정지 0.2초 → S2.

### N3 — 구마노 결과 (C10)
- **사용 구간:** [0,82) → C10
- **시작 이미지(새):**
  > A 1944 Japanese Mogami-class heavy cruiser seen from a high side angle at middle distance on a grey sea. It has one large raked trunked funnel, a tall bridge tower, three twin gun turrets forward and two aft. The cruiser sits in the upper-right part of the frame, its bow pointing toward the left of the frame. Its bow is badly wrecked: the plating near the stem is torn and crumpled, and the ship sits slightly down by the head. Grey smoke drifts from the forward deck, and the ship is clearly afloat, steaming at reduced speed under a grey overcast morning sky with low cloud. Vertical 9:16 photorealistic frame.
  - negative: `two funnels, separate funnels, pristine undamaged bow, explosion, fire burst, sinking, capsizing, dead in the water, stopped ship, awash foredeck, people, golden sunset, sun glare, flags, text, cartoon`
  - 검수 항목:
    - 연돌이 트렁크형 1개인가
    - 포탑이 전방 3기·후방 2기인가
    - 함수가 파손돼 약간 앞으로 숙였는가(침수 수준은 아닌가)
    - 배가 떠 있고 좌향으로 진행하는가(C02·C18과 같은 화면 방향)
    - 함체가 화면 우상(S2 좌표 x72% y30%)에 있어 크롭 없이 C09와 매치되는가
  - 함수가 "없다"고 요구하지 않는다. 절단선을 주장하지 않고, 함수가 다시 생겨나는 생성 실패도 피한다.
  - NH 82400은 참고 자료로도 쓰지 않는다. 그 사진의 함수 손실은 11월 6일 잠수함 어뢰에 의한 것이다.
- **Veo:**
  > The damaged cruiser steams ahead at reduced speed, slightly down by the head, a moderate wash breaking around its wrecked stem. Grey smoke drifts back from the forward deck across the turrets. The camera holds still at its high side angle. Ends with the cruiser still afloat, moving slowly but steadily, a weak wash at its broken bow.
  - negative: `explosion, new fire burst, sinking, capsizing, dead in the water, stopped ship, awash foredeck, bow repairing itself, pristine bow, second funnel, ship morph, extra ships, camera orbit, golden sky, text`
- **변경:** "crawls forward / barely making way / forward deck close to the water"를 뺐다. 12노트(DJ)와 칩 "12 KN"에 맞춰 감속하되 멈추지 않은 배로 그린다.
- **차단·실패 시:** 다시 요청하지 않는다. 대신 ONI 222-J 모가미급 인식도를 트레이스한 단색 측면도 그래픽을 쓴다.
  - 함수 윤곽이 이미 부서진 측면도가 감속하며 좌하로 처진다(궤적 접촉과 명중 순간은 그리지 않는다. 절단선도 주장하지 않는다).
  - 칩은 같은 것을 쓴다.
  - V_C13은 연돌이 2개라 구마노로 쓰지 않는다.

### N4 — 스콜 속 손상된 존스턴 (C11, C12)
- **사용 구간:** [0,77) → C11. [77,192) → C12(1.35→1.50배 크롭 펀치인). 원본 전체를 쓴다.
- **시작 이미지(새):**
  > A low camera near the water off the starboard bow quarter of a gray 1944 U.S. Fletcher-class destroyer, now damaged: dark smoke and steam stream from the after fireroom area just aft of the second funnel, and the after superstructure around that funnel is scorched and dented. It moves at a reduced but steady speed, a clear white wake behind it, inside a grey rain squall; fine rain streaks across the frame and dims the sea, but the ship stays clearly visible, filling the middle third of the frame. Soft, flat light under low cloud. Vertical 9:16 photorealistic frame.
  - negative: `explosion, fire burst, open flames, sinking, people visible, faces, sunlight, golden sky, flags, insignia, hull numbers, text, cartoon`
  - 검수 항목:
    - 연돌이 2개인가
    - 폰 크기에서 제2연돌 뒤의 연기·증기와 그을린 후부 상부 구조가 읽히는가
    - 1.35배 크롭(C12) 후에도 손상 구역이 판독되는가
    - 손상 묘사가 DJ로 확인된 후부 보일러실·기관실 구역 중심인가(함교 손상은 강조하지도, 멀쩡하다고 주장하지도 않는다. 같은 피격으로 에번스가 손가락을 잃었다)
- **Veo:**
  > The damaged destroyer pushes forward through the rain at a reduced but steady speed, dark smoke and steam streaming aft from behind the second funnel. Fine rain streaks across the frame and pocks the sea around the hull. The camera holds still at the same low bow-quarter position. Ends with the ship still moving steadily inside the grey squall, smoke trailing behind it.
  - negative: `new hit, explosion, flash, fire burst, sinking, listing over, stopped ship, crew close-up, faces, ship morph, camera orbit, sunlight, golden sky, text`
- **변경:** A안의 "비가 엷어지며 함수가 빠져나온다" 상태 변화를 뺐다. 재진입은 N5가 맡는다. 근거 없는 '휜 마스트'와 '그을린 함교 전면'을 빼고, 손상을 DJ의 후부 보일러실 구역으로 옮겼다. 이 손상 세트(제2연돌 뒤 연기·증기 + 그을린 후부 상부 구조)는 선미 쪽 시점인 N5에서도 보인다.
- **실패 시:**
  - 품질 실패면 같은 프롬프트로 1회 재생성한다. 차단이면 다시 요청하지 않는다.
  - 그래도 실패하면 V_C14[48,192)(6.0초)를 쓴다. 조건부 차선이며, 상단 크롭으로 수평선의 적 함대와 태양을 지우고, 쿨 그레이로 그레이딩하고, 비를 합성할 때만 쓴다. 모자란 2.0초는 마지막 프레임 정지로 채우고, C12의 펀치인은 그 정지 프레임의 1.35배 크롭으로 대신한다.

### N5 — 재진입 각운 (C13)
- **사용 구간:** [0,111) → C13(4.60초로 트림). [111,192)는 사용하지 않는다. N1·N4의 실패 대안은 각 항목에 정해진 것만 쓴다(N5는 손상 전 오프닝이나 스콜 안 함수 쪽 시점을 대신할 수 없고, N1 승인 뒤에만 존재한다).
- **시작 이미지(N1 시작 이미지 편집 2회, N1 승인 후):**
  - 1차 편집:
  > Remove the two escort carriers and their wakes and fill that area with open grey sea under the rain squall on the left. Extend the rain squall to the right so that the destroyer's stern is still just inside its edge, with the bow already out in clearer air. Change nothing else.
  - 2차 편집:
  > Keep the exact camera position, horizon line, ship pose and light. The destroyer is now battered: dark smoke and steam stream from just aft of its second funnel, and the after superstructure around that funnel is scorched and dented. Change nothing else.
  - negative: `large flames, fireball, clean undamaged hull, three funnels, extra destroyers, people, sun in frame, golden light, text`
  - 검수 항목:
    - N1과 같은 함형(연돌 2개), 같은 카메라 자리(우현 선미 사분면)와 높이인가
    - 손상 세트가 N4와 같은가(제2연돌 뒤 연기·증기, 그을린 후부 상부 구조)
    - 항모가 사라진 자리가 자연스러운가
    - 스콜 가장자리가 함미에 걸려 있고 함수는 그 밖인가(없으면 Veo의 '스콜을 벗어난다'를 'the rain squall staying on the far left behind it'으로 바꾼다)
  - 편집 기능이 없으면 N1 문안에서 항모 문장을 빼고 손상 문장을 넣어 새로 생성하고, 카메라 높이를 N1에 맞춰 검수한다.
- **Veo:**
  > The damaged destroyer finishes its heeling turn, comes upright and pushes on at a reduced but steady speed toward the warships on the right horizon, its stern clearing the edge of the rain squall behind it. Dark smoke streams back from behind its second funnel over a reduced wake. The camera holds still just above the water. Ends with the destroyer upright, clear of the rain and heading toward the distant fleet.
  - negative: `repaired hull, clean undamaged ship, new explosion, fireball, large flames, gunfire, muzzle flash, reversing course, ship duplication, extra destroyers, extra funnel, rain closing over the ship, camera orbit, camera movement, sun in frame, golden light, people, text, HUD`
- **설계:** 함수 방향 반전과 다른 구축함의 동시 등장은 요구하지 않는다. 모순된 편집 요구이고 복제 위험이 있다. 시작 이미지는 N1과 같은 선회 중 경사 자세이므로 Veo 동작은 N1처럼 '선회를 마치고 전진'으로 쓴다(경사 자세 그대로 직진을 요구하지 않는다). 스콜은 1차 편집에서 함미까지 늘려 '벗어남'이 시작 상태와 맞게 한다. '두 번째 선회'의 각운은 C01과 같은 카메라 자리·같은 선회 자세와 앰버 → 화살표가 맡는다.
- **실패 시:** 승인된 시작 이미지를 정지로 쓰고 느린 푸시 1.00→1.06 + 화살표 + 카드를 얹는다. 시작 이미지도 실패하면 N4 마지막 프레임 정지로 대체한다(A 원안).

### N6 — 폭탄 없는 급강하 (C17)
- **시작 이미지:** 기존 A06. 새로 생성하지 않는다. 우측 수평선 순양함 뒤의 밝은 구름 틈만 −1.5EV 로컬 보정해 역광을 없앤다. 요청 전에 A06에서 기체 진행 방향을 확인한다. 진행 방향 앞에 순양함이 없으면 아래 "toward the cruiser on the right horizon"을 "into a steep dive, the cruiser small on the horizon"으로 바꾼다.
- **Veo:**
  > The Avenger noses down into a steep dive toward the cruiser on the right horizon. The camera stays alongside at the same distance, keeping the horizon level. Low grey cloud and soft overcast light hang over a dark sea. Ends with the aircraft diving and the cruiser larger below it.
  - negative: `bomb release, falling bombs, torpedo drop, explosion, fire, gun flashes, tracer, turning away from the cruiser, banking away, extra aircraft, aircraft morph, stopped propeller, camera spin, golden sunset, sun glare, text`
  - A06의 기체 표식이 지워지지 않도록 negative에 표식 관련 단어를 넣지 않는다.
- **변경:** 'banks left'(우측 목표의 반대쪽으로 꺾이는 동작으로 읽힌다), 구름 흐름, 바다 접근을 빼고 동작을 급강하 하나로 줄였다.
- **실패 시:** C17을 삭제하고 3.2초를 줄인다. 항공기의 몫은 C16·C18 대사와 C16의 항공기 아이콘이 유지한다. 이때 "Carrier planes are up."의 역할은 C18 "under air attack"이 맡는다.

### N7 — Center Force 철수 (C18)
- **시작 이미지:** 기존 A02를 좌우 반전해 쓴다. C02·C03의 V_C06과 같은 함, 같은 방향이다. V_C06이 함형 검수에 실패해 N8로 교체되면 N8 시작 이미지를 대신 쓴다. 함 뒤 하늘의 역광과 밝은 구름 틈을 검수하고, 있으면 A06과 같이 −1.5EV 로컬 보정 뒤 쿨 그레이로 그레이딩한다.
- **Veo:**
  > The cruiser begins a slow turn away from the camera, its bow swinging toward the horizon and its wake bending into a wide white curve. The camera holds still at the same high side angle. Grey overcast light stays soft and even over the rough sea. Ends mid-turn, the ship angled away with its wake curving behind it.
  - negative: `explosion, fire, sinking, ship morph, pivoting in place, spinning, rotating like a model, stern toward camera, extra funnels, extra ships appearing, camera orbit, sun behind the ship, golden sky, text`
- **변경:** 8초 안에 선미가 카메라를 향할 만큼 도는 요구를 뺐다(중순양함 선회 반경으로 불가능해 제자리 회전 위험). 선회 도중에 끝낸다.
- **실패 시:** S3 도식을 재사용한다. 빨간 함대 아이콘이 항모 반대쪽으로 선회하고, 시계 "JUST AFTER 09:00"을 띄운다.

### N8 — 손상 없는 일본 중순양함, 묘코급·다카오급 (C02·C03·C18 조건부 교체)
- **조건:** V_C06/A02를 ONI 222-J 묘코급·다카오급 인식도와 대조해 연돌 배치(대형 트렁크형 전방 연돌 + 소형 후방 연돌의 2연돌)와 연장 포탑 5기(전방 3·후방 2)가 맞지 않을 때만 만든다. 맞으면 만들지 않는다. N8은 검수 기준과 같은 함급(묘코급·다카오급)으로 만든다. 1연돌 + 전방 3·후방 2 포탑은 모가미급(N3 구마노)의 실루엣이므로 N8에는 쓰지 않는다(C02 '구마노가 아니다'와 충돌).
- **시작 이미지(새):**
  > A 1944 Japanese heavy cruiser of the Myoko or Takao type seen from a high side angle at middle distance on a grey sea, undamaged. It has a large raked trunked forward funnel and a smaller upright after funnel, a tall bridge tower, and five twin gun turrets, three forward and two aft. Its bow points toward the left of the frame and a clean white bow wave breaks at its stem. Grey overcast morning, low cloud, soft even light from behind the camera. Vertical 9:16 photorealistic frame.
  - negative: `single funnel, three funnels, damaged bow, explosion, fire, smoke damage, sinking, people, golden sunset, sun glare, backlight behind the ship, flags, text, cartoon`
  - 검수 항목: 연돌이 2개(대형 트렁크형 전방 + 소형 후방)인가, 포탑이 전방 3기·후방 2기인가, 좌향으로 진행하는가, 함 뒤에 역광이 없는가, N3 구마노(1연돌)와 한눈에 구별되는가.
- **Veo:**
  > The cruiser steams steadily toward the left of the frame, its bow wave climbing and a straight white wake behind it. The camera holds still at its high side angle. Grey overcast light stays soft and even, with low cloud over the sea. Ends with the cruiser still driving ahead, its forward turrets clearly readable.
  - negative: `explosion, fire, muzzle flash, gun firing, ship morph, third funnel, funnel merging, extra ships, camera orbit, sun behind the ship, golden sky, text`
- **사용 구간:** [0,77) → C02, [77,156) → C03(1.3배 크롭). 시작 이미지는 N7 시드로도 쓴다.
- **실패 시:** V_C06 반전을 쓰되 C02·C03 자막에 함명을 두지 않고, 묶음표에 '대표 함형'이라고 적어 둔다.

## 집계

- **총 길이:** 81.90초 (통합본 76.70초 + 5.20초. C13 +0.8, C14 +1.2, C15 +0.2, C16 +0.4, C17 +0.6, C18 +0.4, C19 +0.8, C21 +0.8)
  - 내레이션: EN 246단어. 평균 3.00단어/초(발화 구간 약 3.15). 컷별 2.63(C08)–3.45(C07)단어/초이고, 모두 2.5–3.5 범위다(C13은 4.60초에 13단어, 2.83).
  - KO 내레이션: 발화 구간 기준 모든 컷 ≤7.5음절/초(C20은 20음절로 줄여 약 6.9). 카드가 고정된 컷(C01·C13)은 문장 단위로 검산한다: C13 앞 문장 15음절/2.15초 ≈ 7.0, 질문 8음절/1.8초 ≈ 4.4. 괄호 속 영문은 TTS에서 뺀다.
  - 계획된 침묵: 3.9초. C10·C12·C13·C14·C16·C18 각 0.4초, C19·C20·C21 각 0.5초. 보상 박자(C16·C18)에도 숨을 넣었다.
- **질문과 답의 위치:**
  - 첫 질문: 1.0–3.4초(카드)
  - 첫 질문 재질문(AGAIN): 46.3–48.1초(카드)
  - 답 "time": 약 81.3초. 같은 박자에 "TIME" 괄호가 완성된다.
  - "time"은 C04(약 12초, '함재기 띄울 시간' — HG A1)와 C07(약 25초, 원리 — HG A2)에 미리 심었다. C04의 '함재기'는 C17(#11·#12)로 잇는다.
- **컷 수:** 21 (묶음 6개)
- **새 생성:**
  - Veo 7건(N1–N7). N8은 V_C06/A02 함형 검수 실패 시에만 추가(조건부 8건째).
  - 새 시작 이미지 4장(N1·N2·N3·N4)과 편집 1장(N5 = N1 시작 이미지 편집 2회). 조건부 1장(N8).
  - 기존 이미지 가공 2건: A06 노출 보정, A02 좌우 반전(+역광 검수·보정)
  - 새 생성이 주 화면인 컷 10개: C01, C05, C08, C10, C11, C12, C13, C17, C18, C21
  - A안의 N3(발사관 선회)는 삭제했다.
- **기존 재사용:**
  - 컷 5개: C02·C03(V_C06 반전, 함형 검수 조건부), C06(V_C10_V2[0,79)), C19(NH63495), C20(NH92320)
  - 시드·소재 4개: V_C10_V2 f78, A02, A06, 어뢰 PNG(C06·C09)
  - 실패 원본(V_C09·V_C10·V_C12·V_C18·V_C20)은 하나도 쓰지 않았다.
- **그래픽:**
  - 도식이 주 화면인 컷 4개, 15.9초: C07, C09, C15, C16
  - 오버레이 요소:
    - 방향 화살표 2회, 질문 카드 2(같은 카드 재사용 + "AGAIN" 태그 1)
    - 속도 칩 1, 어뢰 판 1, 사거리 칩 1, 염료 링+라벨 1
    - 함명·인물 칩 3(C05·C10·C20), 상태 칩 1(C12)
    - 도식 일반명 라벨 3(C07만), "TIME" 괄호 4(C07·C15·C16·C21)
    - 시계 4, 손실 목록 1, 강조 원 3(C05 염료, C14 갬비어 베이·순양함), 출처 칩 4
- **외부 자료:** 컷 2개. C04(80-G-287497), C14(80-G-287505). 둘 다 USN 공식 사진이고 퍼블릭 도메인이다.
- **예상 생성 초수:** 7건 × 8초 = 56초. 채택 분량은 39.2초(사용률 70%)이고 정지 0.60초(C09 0.2, C21 0.4)가 따로 있다.
  - N1 7.42초, N2 7.58초, N3 3.42초, N4 8.0초, N5 4.60초, N6 3.21초, N7 5.0초
  - 예비 재생성 2건(N4 1회 + 품질 실패 1회)을 포함하면 상한 72초. N8이 추가되면 80초다.

**쓰지 않은 기존 소스와 이유**
- **황금 역광 계열:** V_C01·V_C02·V_C04·V_C07·V_C11·V_C14·V_C18_V2. 일본 함대 뒤에 황금 역광이 있어 조명 사실 규칙(#17)과 충돌한다. 크롭과 그레이딩을 조건으로 하는 대체안으로만 둔다.
- **V_C08:** C03과 역할이 겹친다. 다만 좌우 반전 후 좌향 진행이고 황금 역광이 없으며 함형 검수를 통과하면, C03(물살 컷)에 V_C06 크롭 대신 쓸 수 있다.
- **V_C13:** 연돌이 2개라 구마노로 쓸 수 없고, 이름 없이 써도 구마노로 오인될 위험이 있다.
- **NH79408:** 1944년 4월 사진이라 당일 사진으로 교체했다.
- **80-G-288885:** 캡션의 함명이 확정되지 않았다.

**사실 근거 매핑**
- **C01·C21:** MOH(factcheck #14) "consistently interposed his vessel between the hostile fleet units and our carriers" / "diverted the powerful blasts of hostile guns from the lightly armed and armored carriers" → "shield the carriers". "buy them time"은 HG 원문 "buy time for the escort carriers to get their planes off the decks and into the battle"(A1)을 직접 따른다. 사슬: C04 필요 → C07 원리(A2) → C16 조기 발사(HG, #8) → C17·C18 함재기 공격 속 철수(#11·#12). B1 '먼저 한 척이'는 HO "went in to attack independently"(#1).
- **C02:** SA "four battleships… six heavy cruisers", 'Center Force'
- **C03:** 순양함 ≈35노트(설계 속력, WIKI), 항모 17·19·19.3·20노트(HG·GB·WP·FB, #3) → 칩 "≈17–20 KN MAX". 실제 접근 속력은 22–25노트(DJ)였으므로 "can steam"과 "MAX"로 표기했다. "Japan's cruisers"로 화면 속 특정 함과 떼어 놓았다.
- **C04:** "The carriers can't outrun them"은 factcheck 뉘앙스 3의 허용 표현이고, HG "Taffy 3 was doomed as it was being overtaken by the much faster Japanese force"(A1)가 받친다. "They need time to launch planes"는 HG "buy time for the escort carriers to get their planes off the decks and into the battle"(A1). 사진 80-G-287497은 factcheck #16(c)에서 화이트 플레인스 사진군으로 확인됐다. '와일드캣 발진 준비' 캡션 원문은 여전히 사전 확인 항목이므로 출처 칩은 단수 'ESCORT CARRIER UNDER FIRE'로 둔다.
- **C05:** DJ "Without having received orders… funnel smoke", HG "on his own initiative". 대사는 factcheck 작가 노트의 문장이다. 염료 라벨은 SA·KB 근거다.
- **C07:** 일반 원리로 제시한다(회색 중립 아이콘, 궤적 5개, 특정 함 비주장). 원리의 실제 근거는 HG "an attempted torpedo attack by Heermann bluffed Yamato, Kurita's flagship, into turning away, taking agonizing (for the Japanese) minutes to get back into the fight"(A2)다. 맞히지 않은 어뢰 위협이 회피를 강요해 시간을 번 사례다. C15–C16은 같은 원리의 변형(위협에 밀린 회피와 조기 발사)이지 어뢰 회피 사례 자체는 아니다. 이전 판의 축소안(8단어·3.00초)은 근거가 확인돼 적용하지 않는다.
- **C08:** DJ "closed to within ten thousand yards". 실제 행동의 서술이며 발사 요건으로 단정하지 않는다.
- **C09:** JT "10 torpedoes at… Kumano". 발사 시각은 약 0720(뉘앙스 4). 사출음은 미 해군 발사관의 화약 임펄스 방식에 맞췄다.
- **C10:** DJ 12노트. HG "at least one torpedo that blew off her bow". "a torpedo wrecked her bow; she limped out"(작가 노트)은 화면 근거다. 침몰하지 않았다(JT).
- **C11:** "heavy battleship shells, probably Yamato's"(뉘앙스 6). 손상 묘사는 DJ "after fire room and engine room… steering engine"(#6)에 맞춰 후부 보일러실 구역으로 한정했다.
- **C12:** DJ 손가락 부상("bloody stumps of his fingers"), 17노트
- **C13:** DJ 0730 이후 수동 조타("Steering had to be done manually"), MOH "men turning the rudder by hand"(#9) → "Her crew steers by hand". KO 내레이션 "승조원이 키를 돌립니다"는 음절 속도 때문에 '손으로'를 뺀 것이며 사실 변경이 아니다.
- **C14:** DJ "Although Johnston had already fired all ten… she slid in astern… to provide fire support"(#8, 약 0750 다른 호위함 엄호). DJ 0830 "unsuccessfully attempted to draw fire from Gambier Bay". 사진은 80-G-287505 캡션 "Note Japanese cruiser, barely visible" 근거이며, 사진 속 순양함(GB "most likely Chikuma")을 0830의 순양함과 동일시하지 않는다.
- **C15·C16:** SA 0845 'Yahagi attack' "repulsed by Johnston's furious fire and strafing by U.S. aircraft"(#8). HG "launching their torpedoes too early". 종대는 KB "Yahagi and four enemy destroyers steamed in column"(0830, A3), 선두함 선회는 DJ(Hagen 회고) "the destroyer leader executed a 90-degree turn to starboard"(A3), 발사는 KB "launched torpedoes from a range of approximately 10,500 yards at 0915"(A3). 존스턴이 갬비어 베이 유인을 멈추고 구축함 쪽으로 사격을 돌린 시각은 DJ "checked fire at 0840 to engage enemy destroyers"(A3). 화력 집중은 그리지 않는다.
- **C17:** GB "without bombs or torpedoes… dummy bombing runs", FB "dummy runs without weapons"(#11). "Carrier planes are up"은 SA·GB의 미 해군 항공 공격(#12) 근거다.
- **C18:** SA·HG "a little after 9", 공중 공격, 상황 인식 부족
- **C19:** 포격 침몰 4척: HO 0855, GB 0911, SA SBR, DJ 1010(#13). 세인트 로(가미카제, 1100 이후)는 "sunk by gunfire"로 한정해 제외했다. JT "186 lost"(전사, 부상·노출 사망, 실종 후 사망 추정 포함)라서 EN은 LOST, KO는 전사·실종으로 표기했다.
- **C20:** DJ "last seen… in the water… night of 25 October", HG "first Native American in the U.S. Navy to be so recognized"(설명란·고정 댓글로 이동). "배와 함께 침몰" 표현은 쓰지 않았다.
- 허구 대사, 사망 순간 재연, 취역사 인용, 경례 증언은 쓰지 않았다.

**운영(설명란·고정 댓글):** 고정 댓글에 HG 근거로 "에번스 함장은 이 전투로 명예훈장을 받았고, 미 해군에서 그렇게 인정받은 최초의 아메리카 원주민입니다."를 적는다. 단발 편이므로 다음 회 예고는 없고, 둘째 줄은 "C19 손실 목록의 다른 두 척(호엘, 새뮤얼 B. 로버츠) 이야기도 궁금하신가요?"처럼 질문형으로 댓글을 유도한다.

**사전 확인:**
- NHHC 카탈로그 캡션 원문·URL을 factcheck에 행으로 추가할 것: 80-G-287497(발진 준비 여부와 함명), NH 63495(존스턴 1943년 사진 식별·날짜), NH 92320(에번스 초상 식별). NH92320이 Evans를 명시하지 않으면 MOH 페이지 게재 초상과 그 카탈로그 번호로 교체.
- NH63495의 'courtesy' 권리 표기. 폭 맞춤 시 마스트 꼭대기의 y 위치(C19 판 하단과의 관계).
- 80-G 두 장을 9:16으로 크롭했을 때의 판독성. C14는 갬비어 베이와 순양함이 모두 들어오는 최소 크롭이 폭 맞춤의 1.3배 이내인지, 순양함이 x85% 안에 들어오는지.
- V_C06/A02의 함형을 ONI 222-J 묘코급·다카오급 인식도와 대조(2연돌 배치: 대형 트렁크형 전방 + 소형 후방, 연장 포탑 5기). 실패 시 N8(같은 함급으로 생성). factcheck 작가 노트 "one big raked funnel and five twin turrets"가 구마노(모가미급, #7)만을 가리키는 것인지 확인하고, 그렇다면 C02·C03·C18의 대표 함형 기준은 묘코·다카오급(2연돌)으로 둔다(뉘앙스 7 "Chōkai and Haguro had two").
- A06의 기체 진행 방향(N6 프롬프트 분기). A02의 함 뒤 역광.
- C20 칩이 초상 얼굴과 겹치는지.
- 대사 근거 3건(C04 HG "buy time" 원문, C07 어뢰 회피 사례, C15·C16 구축전대 척수·선회)은 2026-10-28 저장된 NHHC 원문으로 확인을 마쳤다(factcheck '추가 확인' A1–A3). 조건부 문안을 확정 문안으로 바꿨다.