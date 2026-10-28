# 존스턴·사마르 해전 쇼츠 — 연출·비평 검수

검수일 2026-10-28 · 검수 대상: `JOHNSTON_CLAUDE_REVIEW` 패키지 (제목 "Why This U.S. Destroyer Charged a Japanese Fleet", 183단어 · 9씬 · 25컷 · 86.708초)

## 0. 내가 본 것 / 보지 않은 것

| 구분 | 내용 |
|---|---|
| **1단계 (독립)** | 01 장면표·대본 전문, 기준이미지 A01·A02·A03·A04·A06·A08, C10 발사관 개념도·어뢰 PNG·오버레이 합성 표본 1장, 자료사진 C20·C26·C27·C28 표시본. 이 시점의 잠정평가는 따로 고정해 두었다(부록 A). |
| **2단계 (보완)** | 02 제작 과정, 03 실제 제출 프롬프트 16개와 미제출 3개 원문, 04 실패 기록, 05 요청서, 실패 컨택트시트 5장(C09·C10·C12·C18·C20), `current_cut_execution.json`(컷별 실제 소스 구간), `measured_timing_current.json`(ASR 기반 컷 타이밍), `storyboard_v3_original.json`(오버레이·카드 계획). |
| **역사 검증** | NHHC(DANFS·H-Gram·MOH 표창문 등) 대조는 별도 사실검증 에이전트가 맡았다. 결과는 ⑧절에 반영. 재구성 장면표는 ⑩절과 `STORYBOARD_V4.md`. |
| **보지 않은 것** | 연속 영상과 음성은 하나도 보거나 듣지 않았다. 컨택트시트는 1초 간격 정지 표본이다. 그래서 동작의 자연스러움, 정상 속도에서의 리듬, 발음, 실제 폰 UI 겹침은 판정하지 않았다. 기존 PASS·서명도 근거로 삼지 않았다. |

---

## ① 전체 판정과 가장 큰 문제 5개

**전체 판정: 구조 REVISE. 현재 형태로 본생성(C21·C22·C25)에 들어가지 말 것.**

대본은 순서가 바르다. 도주와 역행 → 맥락 → 연막의 한계 → 어뢰 → 대가 → 재진입 → 공동 방어 → 결과 → 함장. 승리담으로 부풀리지 않은 절제도 장점이다.

그러나 다섯 가지 문제가 있다.

1. **질문의 답을 받쳐 줄 "작동 원리"가 빠져 있다.**
   - "왜 큰 포를 향해 돌진했나"의 실제 논리는 시간이다. 느린 호위항모는 도망칠 수 없다. 그래서 누군가 적을 돌려세워야 한다. 어뢰는 맞히지 않아도 큰 배가 회피 기동을 하게 만들어 시간을 번다.
   - 지금 대본에는 항모의 속도 제약도, 어뢰가 왜 위협인지도 없다. 그래서 30초의 "torpedoes can hurt a much larger ship"이 최종 답처럼 들린다. 진짜 답은 마지막 4초의 해석 문장 하나에 맡겨졌다.
   - 즉 시청자가 추론해서 도착하는 답이 아니라 선언으로 끝난다.
2. **첫 3초에 세 채널이 경쟁하고, 결말이 미리 공개된다.**
   - 첫 프레임에 오프닝 카드 "HE TURNED / TOWARD THE GUNS"가 뜬다. 같은 순간 VO는 다른 문장("The U.S. escort carriers turn away.")을 읽는다. 그림(A01)은 함수와 항적 방향이 폰 크기에서 모호하다.
   - 카드 문구는 C28의 결말 문장 그 자체다. "HE"가 누구인지는 25초(C09)까지 나오지 않는다.
   - 대비는 3.1초에, 질문은 6.75초에야 나온다.
3. **같은 구도와 같은 빛이 영상 전체에서 반복된다.**
   - 존스턴이 나오는 컷 대부분이 같은 선미 사선에 같은 황금 역광이다: C01·C02·C09·C11·C14·C16·C18·C19, 그리고 C12 대안까지.
   - 이 중 셋은 같은 원본에서 나왔다. C02는 V_C02[0,88), C09는 같은 원본의 [88,192), C11은 그 마지막 프레임에서 이어 생성했다.
   - A08(다른 호위함)도 같은 구도라 존스턴을 복제한 것처럼 읽힌다. C20과 C27은 같은 원사진 NH63495다.
   - 역광의 역사적 개연성은 ⑧절에서 다룬다.
4. **클라이맥스(43–57초)가 가장 약하다.**
   - C18 "And now comes the harder choice."는 정보가 없는 예고문이다. 재진입의 전환점인 C19는 2.0초뿐이다.
   - "guns that still work" 위에는 1943년 시애틀 항구 사진 크롭이 나온다. 이 사진은 C27에서 또 쓰인다.
   - 이 구간에서 재연과 기록 사진이 핑퐁하며 레지스터가 깨진다(재연 → 54.6초 자료사진 → 57.4초 재연 → 71.8초부터 자료사진).
   - 사료에 있는 가장 강한 장면은 쓰지 않았다. 갬비어 베이를 위해 적 순양함의 포화를 끌어당긴 것, 수동 조타로 버틴 것 등이다(⑧절에서 검증).
5. **생성 전략과 편집 리듬이 실패를 낳는 구조다.**
   - 세 번 모두 넓은 시드에서 세부 동작을 요구했다(C10 발사관, C12 어뢰, C20 함포). 모델은 확대하면서 세부를 발명했다: 3연장, 엉뚱한 발사 위치, 상부 불덩이.
   - 긍정 프롬프트에 "No painted star or stripes… diamond icons… HUD"를 반복한 계열에서 실제로 별·마름모·빨간 라벨이 나왔다(C09·C18). 인과를 증명할 수는 없지만, 부정어가 오히려 그 요소를 불러냈을 가능성이 있다.
   - 편집 리듬 문제도 크다. ASR 타이밍상 실제 발화는 65.5초이고, 약 21초(24%)가 구절 사이 공백이다. 발화 속도는 약 168wpm로 정상이지만, 25번 멈췄다 가는 리듬이 된다. 음성을 들은 판단이 아니라 타이밍 수치에서 나온 추정이다.

---

## ② 25컷 판정표

**표기**
- 해결 수단
  - **[기존]**: 이미 있는 원본 구간·사진·PNG의 재배치, 자르기, 오버레이, 대사·자막·음성 편집으로 해결.
  - **[그래픽]**: 새로 만드는 2D 합성. 정책상 "무통보 대체 금지"이므로 명시적으로 채택 결정이 필요하다.
  - **[새 생성]**: 새 이미지나 Veo 요청이 필요.
  - **[외부 자료]**: 패키지 밖 공공 자료를 확보해야 함.
- **판정 축**: 대본·구성은 문서만으로 판정했다. 실제 동작이 판정의 핵심인 컷은 UNVERIFIED로 두었다.

| 컷 | 시간(현재) | 판정 | 문제 | 수정안 (대사 / 행동·카메라 / 프롬프트) | 수단 |
|---|---|---|---|---|---|
| C01 | 0.00–3.08 (3.08) | **REVISE** | 첫 문장의 주어가 항모라 주인공이 아니다. 카드는 결말 문장을 미리 공개하고, "HE"는 미정의다. A01은 방향이 모호하고 역광이다. 내부컷 이후는 이미 제외했다. | 대사 "The carriers run. One destroyer turns toward the battleships." (9단어, 약 3.2초). 카드는 결말 문구 대신 0–1.5초 무카드로 두고, 질문 카드는 C02로. 첫 프레임에 화살표 2개를 1.2초 동안 즉시 표시: 항모 항적에 흰 화살표 ←, 존스턴 함수 앞에 빨간 화살표 →. 끝나면 제거. "USS JOHNSTON" 라벨을 여기서 먼저(현재는 C09). 근본 수정은 A01 재생성(⑤-1). 수면 높이 저각, 선회로 기운 선체, 함수 물보라가 화면 쪽, 항모 항적은 뒤로 갈라짐. | [기존]+[그래픽]. 근본 수정은 [새 생성] |
| C02 | 3.08–6.75 (3.67) | **REVISE** | 대비를 C01로 당기면 이 컷의 대사는 중복이다. 영상(V_C02[0,88))은 유지 가능. | 대사 "Why charge the biggest guns afloat?" (6단어 2.2초). 질문을 6.75초에서 3.3초로 당긴다. 카드 "WHY TURN TOWARD THE GUNS?"(빨강, 상단). 결말 문장과 짝을 이루는 질문형으로. | [기존] |
| C03 | 6.75–9.96 (3.21) | **KEEP**(영상) / 대사 이동 | 원경 큰 포탑을 찾는 카메라는 이 편에서 거의 유일하게 목적이 분명한 움직임이다(V_C06[0,77)). 질문 대사가 C02로 옮겨 가므로 이 컷은 위협 제시를 맡는다. | 대사 "Battleships and cruisers are closing in." (현재 C06 대사를 앞당김). 화면은 그대로. | [기존] |
| C04 | 9.96–13.25 (3.29) | **REMOVE**(대사) | "It's nineteen forty-four, off Samar."는 그림이 맡을 수 있는 정보를 3.3초 대사로 쓴다. | 대사 삭제. C05 첫 0.8초에 소형 카드 "OFF SAMAR · OCT 25, 1944"(흰 글자·반투명 바, 상단). V_C04[0,67)은 C05 앞부분으로 흡수. | [기존] |
| C05 | 13.25–17.04 (3.79) | **REVISE** | "small carriers"는 왜 지켜야 하는지(임무)와 왜 도망칠 수 없는지(속도)를 말하지 않는다. 이 결손이 문제 1의 뿌리다. | 대사 "These little carriers cover the troops on Leyte — and they're too slow to escape." (14단어 약 5초). 화면은 V_C04[0,144) 항모와 갑판 함재기, 라벨 "ESCORT CARRIER" 유지. | [기존] |
| C06 | 17.04–20.88 (3.83) | **REVISE**(경미) | 영상 V_C06[77,169)은 유효하다. 대사가 C03으로 옮겨 가므로 시간을 줄인다. A02는 묘코급 대용 순양함이다(03에 명시). | 2.0초로 줄이고 대사 없이 함수 물살 위에 C05 대사의 끝을 겹친다. | [기존] |
| C07 | 20.88–23.33 (2.46) | **KEEP**(영상) / 대사 병합 | 연막이 항모를 가리는 변화가 화면에서 일어난다. 대사는 그것을 읽어 줄 뿐이다. | C07과 C08을 한 문장으로: "Smoke hides the carriers — but it can't stop the chase." (10단어 3.6초). C07 1.8초, C08 1.8초. | [기존] |
| C08 | 23.33–25.29 (1.96) | **REVISE** | 1.96초에 발화가 컷 끝에서 끝난다(여유 0.01초). "pursuit"를 보여 줄 시간이 없다. 요청했던 연막 구간도 원본에 없다(03). | 위 병합. 적 함수 물살로 끝내고 대사 끝 뒤 0.3초 여유. | [기존] |
| C09 | 25.29–30.42 (5.12) | **REVISE** | 소스 V_C02[88,192)는 C02와 같은 테이크 후반이다. 시청자에게는 20초 전 장면의 반복이다. 존스턴 이름도 25초에야 나온다. 5.1초에 정보는 "공격하러 나선다" 하나. | 대사 "Commander Ernest Evans doesn't wait for orders. He takes Johnston straight in." [⑧절 #1 검증 결과로 표현 확정]. 화면은 새 각도: 존스턴 앞쪽 수면 높이 정면 저각, 다가오는 함수와 뒤로 끌리는 연막(⑤-3). 대안 [기존]: V_C11[56,133) 미사용 구간도 같은 사선이라 반복은 해소되지 않는다. | [새 생성] 권장 |
| C10 | 30.42–33.75 (3.33) | **REVISE** | 대사 "torpedoes", 빨간 카드 "TORPEDO", 어뢰 그림이 3중으로 겹친다. 왜 큰 배에 위협인지는 하나도 없다. 흰 지시선은 회색 하늘과 장비 위에서 잘 안 보인다. 자막 위치가 높이 약 79–82%로 쇼츠 하단 UI와 겹칠 위험이 있다(실제 폰 미확인). | 대사 "His guns can't sink a cruiser. His ten torpedoes can." [#4 검증]. 오버레이: 지시선과 "TORPEDO" 카드를 삭제. 어뢰 PNG는 어두운 반투명 판 위에 두고 카드 "10 TORPEDOES". 5개 캡에 얇은 흰 링 강조(2개 발사대 중 하나라는 점은 대사가 담당). 자막은 높이 62–70%로. 영상 V_C10_V2[0,80) 유지. 흐린 하늘 대 황금 역광의 톤 차이는 그레이딩으로 맞춤. | [기존]+[그래픽] |
| C11 | 33.75–36.08 (2.33) | **REVISE** | "First, it has to get closer."에 대응하는 그림이 C02·C09와 같은 사선 추적이다. 접근의 대가(포화 속 노출)가 안 보인다. 계획했던 함포 사격도 프롬프트에서 "No firing"으로 빠졌다. | 대사 "But only from close range — under fire." 화면은 존스턴 함교 높이의 전방 시점. 적 함대가 커지고 주변에 물기둥이 선다(색 물기둥 여부는 #10). 프롬프트는 ⑤-4. 대안 [기존]: V_C11[0,56) 유지 + "≈ 5 MILES" 카드(#4 검증 시). | [새 생성] 권장 / [기존] 차선 |
| C12 | 36.08–39.29 (3.21) | **UNVERIFIED** (현 대안 불충분) | 발사 영상이 없다. 현 제안(V_C11[56,133) 이어 쓰기)은 C11과 합쳐 5.5초 동안 같은 넓은 사선을 보여 준다. 그사이 VO는 "launches"라고 말한다. 핵심 행동 박자에서 대사와 그림이 어긋난다. | 아래 ⑦의 A안(그래픽 부채꼴)을 1순위로. 대사 "Johnston fires all ten at the cruiser Kumano." [#4 검증] | [기존]+[그래픽] |
| C13 | 39.29–43.17 (3.88) | **REVISE** | A03은 연돌 2개라 묘코계 외형으로 보인다. 함수도 온전하다. 그런데 계획과 사료는 "선수 손상"이다[#5·#7 검증]. 그 위에 "KUMANO" 라벨을 붙이면 함형 오류를 실명으로 확정하는 셈이다. | 대사 "One tears off Kumano's bow. She drops out of the fight." [#5 검증]. 근본 수정은 A03을 모가미급 외형(단일 대형 연돌)에 함수가 1번 포탑 앞에서 없는 상태로 재생성(⑤-5). 차선은 현재 영상 유지 + "KUMANO" 라벨 삭제(VO가 이름을 담당). | [새 생성] / [기존] 차선 |
| C14 | 43.17–47.33 (4.17) | **REVISE** | A04가 A01과 같은 구도다. 같은 배가 같은 자리에서 연기만 났다. 원본 앞의 폭발 구간 제외는 옳다. | 대사 "Then heavy shells smash into Johnston. Evans is wounded." [#6 검증]. 화면은 새 축: 우현 함수 쪽 저각, 스콜 속 비와 연기, 손상된 함교 외부(⑤-6). 차선은 현행 V_C14[48,136) 유지. | [새 생성] 권장 / [기존] 차선 |
| C16 | 47.33–49.96 (2.62) | **REVISE** | "The ship has spent its torpedoes."의 시제와 순서가 어뢰를 피격 뒤에 다 쓴 것처럼 읽힌다. 어뢰는 첫 공격에서 다 썼다[#4]. 소스 V_C14[136,192)에서는 소진이 보이지 않는다. | 대사 "No torpedoes left. Half its power gone." [#6 검증]. 오버레이로 C10의 "10 TORPEDOES" 카드를 "0"으로 바꾸어 0.8초 회수. | [기존]+[그래픽] |
| C18 | 49.96–52.62 (2.67) | **REVISE** | 메타 예고문이라 정보가 없다. V_C18_V2는 카메라 궤도가 커서 선회를 증명할 수 없다(03). 카메라가 배의 선회를 흉내 내는 구간이다. | 대사 "When the other destroyers charge, Johnston goes back in with them." [#8 검증]. 화면은 V_C18_V2[0,97)의 깨끗한 앞부분을 C18+C19 통합 4.0초로. "선회"라고 주장하지 않고 "함께 전진"만 읽히게. | [기존] |
| C19 | 52.62–54.62 (2.00) | **REVISE** | 전환점인데 2.0초다. 발화가 컷 끝과 함께 끝난다. | C18과 통합(위). 대사 끝 뒤 0.5초 정적 여유로 결단의 무게를 둔다. | [기존] |
| C20 | 54.62–57.38 (2.75) | **REMOVE** | 1943년 항구 사진(배경 스미스 타워) 크롭이 "아직 작동하는 함포"의 증거로 쓰인다. 이 사진은 C27과 같은 원본이다. 재연과 기록 레지스터가 핑퐁한다. | 대사 대체: "With only its guns, it pulls fire away from the carriers." [#8·#14 검증]. 화면은 V_C18_V2 후반의 깨끗한 구간이 있으면 그것, 없으면 ⑤-7의 새 생성(손상된 포가 현측을 향한 정지 상태, 발포 없음). 자료사진은 결말 구간에서만. | [기존] 또는 [새 생성] |
| C21 | 57.38–59.88 (2.50) | **UNVERIFIED** (미생성) / 계획 REVISE | A08 구도가 A01과 같다. 존스턴 복제로 읽힐 위험. | 새 A08: 손상된 존스턴 갑판의 연기를 전경에 두고, 그 너머로 두 구축함이 고속으로 지나가는 시점. "다른 배"가 주인공의 눈으로 읽힌다. 라벨 "HOEL · HEERMANN"[#8 검증]. ⑤-8. | [새 생성] |
| C22 | 59.88–62.25 (2.38) | **UNVERIFIED** (미생성) / 대사 REVISE | 화면이 대사를 반복한다. A06 Avenger 외형은 양호. | 대사 "Pilots keep diving — some with no bombs left." [#11 검증]. 존스턴의 "어뢰 없이 재진입"과 짝을 이룬다. 프롬프트는 ⑤-9로 압축. | [새 생성] |
| C23 | 62.25–68.08 (5.83) | **REVISE** | 추상 3항 나열("Smoke, repeated attacks, and confusion…")에 5.8초. 화면 계획은 미생성 C21 원본에 의존한다. | 3.5초로 줄임. 대사 "Smoke, torpedoes, and dive after dive keep the giant fleet turning." [#12 검증]. 화면은 C21 원본 후반, 없으면 V_C07·V_C08 미사용 구간. | [기존]/[새 생성] |
| C25 | 68.08–71.83 (3.75) | **UNVERIFIED** (미생성) / 대사 REVISE | 통용 용어는 "Center Force"다. A07이 없다. V_C25 프롬프트는 한 요청에 조건이 과밀하다. | 대사 "And then the Japanese fleet turns back." [#12 검증]. 프롬프트는 ⑤-10으로 압축. | [새 생성] |
| C26 | 71.83–76.50 (4.67) | **REVISE** | 사진 위쪽에 원래 캡션 헤더가 박혀 있다. 1944년 4월 사진이다. 손실이 갬비어 베이 하나로만 읽힌다. | 헤더를 잘라 내고 출처를 소형 크레딧으로. 대사 "Gambier Bay is sunk. So are Hoel and Samuel B. Roberts." [#13]. 가능하면 사마르 당일 촬영된 실제 전투 사진으로 교체[#16]. | [기존] / [외부 자료] |
| C27 | 76.50–78.71 (2.21) | **KEEP**(사진) / 대사 REVISE | 존스턴 신원 사진으로 적절하다. C20을 제거하면 중복도 해소된다. "does not make it home"은 C28의 "never came home"과 겹치고 시제가 섞인다. | 대사 "And Johnston." (2단어). 사진과 "USS JOHNSTON • LOST" 카드가 나머지를 말한다. 1.5초 정적. | [기존] |
| C28 | 78.71–86.71 (8.00) | **REVISE** | 8초 단일 초상은 결말 예외로 허용 가능하다. 다만 "to give the men behind him a chance"는 근거를 밝히지 않은 해석이다. 앞의 사진 두 장과 합치면 약 15초 정지 구간이 된다. | 대사 "Evans was never found. He turned toward the guns so the carriers could run." [#14 검증]. 마지막 "could run"이 첫 대사 "The carriers run."으로 이어지는 루프 구조. 카드 "ERNEST E. EVANS · MEDAL OF HONOR"[#14]. 6.5초 + 여운 1초. | [기존] |

C15·C17·C24는 정본에 없는 결번이다. 실제 25컷 = C01–C14, C16, C18–C23, C25–C28.

**집계**

| 판정 | 수 | 해당 컷 |
|---|---|---|
| KEEP(부분 포함) | 3 | C03, C07, C27 |
| REVISE | 16 | |
| REMOVE | 2 | C04 대사, C20 |
| UNVERIFIED | 4 | C12, C21, C22, C25 |

KEEP 3개도 대사는 이동하거나 바뀐다.

---

## ③ 유지하면 좋은 선택

- **"승리담 금지"와 "정확히 모르는 것은 주장하지 않기" 원칙.** 구마노를 격침시키지 않고, 쿠리타 철수를 존스턴 혼자의 공으로 돌리지 않는다. "help frustrate"라는 신중한 동사도 좋다.
- **C03의 원경 포탑 찾기.** 이 편에서 카메라가 새 정보를 주는 가장 좋은 예다.
- **C07 연막 은폐.** 화면 안에서 상태가 바뀌어(보임→가림) 대사 없이도 읽힌다.
- **실패 원본을 크롭으로 숨기지 않고 정상 구간만 쓰는 규율.** 차단된 이미지 요청을 다른 문구나 공급자로 우회하지 않은 판단도 그렇다.
- **결말 자료사진은 원본 톤 유지, 자동 컬러화 금지.** 침몰·사망 순간을 재연하지 않는 원칙도.
- **C10_V2의 교훈.** 세부 정지이미지에서 정적 동작만 요구하니 성공했다. 이것을 표준 절차로 삼을 것(⑤-0).
- **"His guns… / turned toward the guns"의 수미상관 의도.** 다만 오프닝 카드에서 미리 말하지 말고 질문형으로 열어 둘 것.

---

## ④ 수정 설명묶음과 대본 예시

> 이 절은 검수 단계의 1차 예시다. 최종 제안은 ⑩절과 `STORYBOARD_V4.md`(재구성 장면표 v4)가 대체한다.

목표는 약 72초다. 단어 수는 거의 같게 두고, 구절 사이 공백을 평균 0.85초에서 0.25초로 줄인다. 대괄호 번호는 ⑧절 사실검증 항목이다.

| 묶음 | 질문 → 관찰 → 작동/선택 → 남는 한계 → 다음 질문 | 컷 |
|---|---|---|
| G1 질문 (0–6초) | 모두 도망치는데 한 척만 반대로 → 왜? | C01–C02 |
| G2 왜 도망칠 수 없나 (6–17초) | 위협 → 항모의 임무와 느린 속도 → 연막은 숨길 뿐 | C03, C05–C08 |
| G3 작은 배의 무기 (17–33초) | 함포로는 안 됨 → 어뢰 10발, 단 가까이서 → 발사 → 구마노 이탈 → 그 대가는? | C09–C13 |
| G4 대가와 두 번째 선택 (33–46초) | 피격·부상·어뢰 0 → 그래도 다시 들어감 → 포로 적의 사격을 끌어당김 | C14–C20 |
| G5 혼자가 아니다 (46–55초) | 다른 호위함, 폭탄 없는 비행기 → 거대 함대가 계속 회피 | C21–C23 |
| G6 결과와 대가 (55–72초) | 일본 함대 회항 → 손실 → 에번스 → 첫 질문 회수와 루프 | C25–C28 |

| 컷 | EN | KO (자막·검토용) |
|---|---|---|
| C01 | The carriers run. One destroyer turns toward the battleships. | 항모들은 달아납니다. 구축함 한 척만 전함들 쪽으로 돕니다. |
| C02 | Why charge the biggest guns afloat? [#2] | 왜 세상에서 가장 큰 함포를 향해 돌진할까요? |
| C03 | Battleships and cruisers are closing in. | 전함과 순양함이 다가옵니다. |
| C05 | These little carriers cover the troops on Leyte — and they're too slow to escape. [#3] | 이 작은 항모들은 레이테의 지상군을 엄호합니다. 그리고 너무 느려서 도망칠 수 없습니다. |
| C07–08 | Smoke hides the carriers — but it can't stop the chase. | 연막은 항모를 숨기지만, 추격을 멈추진 못합니다. |
| C09 | Commander Ernest Evans doesn't wait for orders. He takes Johnston straight in. [#1] | 어니스트 에번스 함장은 명령을 기다리지 않습니다. 존스턴을 곧장 몰고 들어갑니다. |
| C10 | His guns can't sink a cruiser. His ten torpedoes can. [#4] | 함포로는 순양함을 못 가라앉힙니다. 어뢰 열 발이라면 가능합니다. |
| C11 | But only from close range — under fire. [#4] | 다만 가까이, 포화 속으로 들어가야 합니다. |
| C12 | Johnston fires all ten at the cruiser Kumano. [#4] | 존스턴은 순양함 구마노를 향해 열 발을 모두 쏩니다. |
| C13 | One tears off Kumano's bow. She drops out of the fight. [#5] | 한 발이 구마노의 함수를 날립니다. 구마노는 전투에서 빠집니다. |
| C14 | Then heavy shells smash into Johnston. Evans is wounded. [#6] | 곧 대구경 포탄이 존스턴을 강타합니다. 에번스도 다칩니다. |
| C16 | No torpedoes left. Half its power gone. [#6] | 어뢰는 하나도 없고, 동력은 절반을 잃었습니다. |
| C18–19 | When the other destroyers charge, Johnston goes back in with them. [#8] | 다른 구축함들이 돌격하자, 존스턴도 함께 다시 들어갑니다. |
| C20 | With only its guns, it pulls fire away from the carriers. [#8][#14] | 남은 함포만으로, 항모를 향하던 포화를 자신에게 끌어옵니다. |
| C21 | The other escorts charge too. | 다른 호위함들도 돌격합니다. |
| C22 | Pilots keep diving — some with no bombs left. [#11] | 조종사들도 계속 급강하합니다. 폭탄이 없는 채로도요. |
| C23 | Smoke, torpedoes, and dive after dive keep the giant fleet turning. [#12] | 연막과 어뢰, 거듭된 급강하가 거대한 함대를 계속 회피하게 만듭니다. |
| C25 | And then the Japanese fleet turns back. [#12] | 그리고 일본 함대가 돌아섭니다. |
| C26 | Gambier Bay is sunk. So are Hoel and Samuel B. Roberts. [#13] | 갬비어 베이가 가라앉았습니다. 호엘과 새뮤얼 B. 로버츠도. |
| C27 | And Johnston. | 그리고 존스턴도. |
| C28 | Evans was last seen in the water that night. He turned toward the guns so the carriers could run. [#14] | 그날 밤, 에번스는 물 위에서 마지막으로 목격됐습니다. 그는 항모들이 달아날 수 있도록 포화를 향해 배를 돌렸습니다. |

- **루프**: 마지막 "…so the carriers could run."이 첫 문장 "The carriers run."으로 이어진다.
- **질문의 공개 순서**:
  - 3초: 질문.
  - 13초: 제약(느림).
  - 30초: 수단과 조건(어뢰, 가까이).
  - 37초: 결과(구마노).
  - 44초: 두 번째 질문(어뢰 없이 왜?).
  - 72초: 목적(항모가 달아날 시간).
- 중간 답들은 "부분 답 + 새 제약"으로 끝나서 최종 답처럼 들리지 않는다.

---

## ⑤ 반드시 수정할 프롬프트

### ⑤-0 모든 요청에 적용

- **공통 보일러플레이트 약 120단어를 삭제한다.**
  - 순서: ① 시작 상태(이미 보이는 것) → ② 단 하나의 물리 행동 → ③ 카메라(무엇을 찾고 어디서 멈추나) → ④ 끝 상태.
  - 4–6문장으로 쓴다.
  - "No …" 문장은 긍정 프롬프트에서 전부 빼고 negative 칸으로만 옮긴다. 특히 star·stripes·diamond·HUD·label은 긍정 프롬프트에 절대 쓰지 않는다.
- **세부 동작은 세부 시작 이미지에서만 요구한다.**
  - 발사관·함포·함교 같은 세부를 움직이려면, 그 세부가 화면의 30% 이상을 차지하는 검수된 정지이미지를 먼저 만든다. 그다음 작은 동작 하나만 요구한다. C10_V2가 이렇게 성공했다.
  - 넓은 시드에서 "카메라가 다가가 세부를 보여 주고 행동"은 금지.
- **빛을 하나로 통일한다.** 현재 황금 역광 시드를 계승하지 말고 아침 빛으로 다시 시작한다. 구체 조건은 #17 검증 결과로 확정한다.
- **enhance_prompt를 비교한다.** 끄는 것이 가능한지와 효과는 확인하지 못했다(UNVERIFIED). 같은 시드로 on/off 1쌍만 비교해 볼 가치가 있다.
- **화면 방향 규칙은 좌우 관계만 지킨다.** "적 우상, 항모 좌하"는 좌우 관계를 지키는 규칙이지 같은 카메라 위치를 요구하는 규칙이 아니다. 거리(원·중·근), 높이(수면·함교·상공), 측면(좌현·우현)을 컷마다 바꾸되 좌우 관계만 유지한다.

### ⑤-1 A01′ 시작 이미지 (C01) — [새 생성]

```text
A low camera just above the waves beside a single gray 1944 U.S. Fletcher-class destroyer heeling hard into a starboard turn, bow spray thrown toward the camera, its curved wake bending behind it. Far behind it, two small flat-deck escort carriers steam away toward the left edge, their straight wakes pointing the opposite way. On the right horizon, low gray silhouettes of a large battleship fleet. Early-morning light from behind the camera, broken cloud and a dark rain squall on the horizon. Vertical 9:16, photorealistic, restrained documentary color.
```

### ⑤-2 V_C01′ (첫 3초) — [새 생성]

```text
The destroyer from the first frame keeps heeling through its turn until its bow points at the battleship silhouettes on the right; its wake curls into a clear arc. The carriers behind it keep sailing toward the left edge. The camera stays low at water level and drifts with the destroyer without rotating. Ends with the destroyer's bow aimed at the enemy and the carriers' wakes running the other way.
```
negative: `camera orbit, background rotation, ship morph, extra ships, reversed wake, fire, explosion, text, graphics`

### ⑤-3 C09 새 각도 (정면 저각) — [새 생성]

- 시작 이미지: 존스턴이 화면 정면을 향해 다가오는 수면 높이 구도(정지이미지 먼저 검수).

```text
The destroyer charges straight toward the camera, bow wave climbing and spray sheeting off the bow, a gray smoke screen trailing from its funnels behind it. The camera holds at water level and slowly backs away, keeping the bow centered. Ends with the bow filling the lower half of the frame and the smoke wall behind.
```

### ⑤-4 C11 함교 시점 접근 — [새 생성]

- 시작 이미지: 존스턴 함교 앞 난간 너머 전방 시야. 앞쪽 5인치 포탑 1기와 수평선의 적 함대(정지이미지 검수).

```text
From the destroyer's open bridge, looking over the forward gun, the enemy warships on the horizon slowly grow larger as the ship closes. Tall white shell splashes rise from the sea on both sides ahead of the bow and fall back. The camera stays fixed to the ship and rises and falls with the swell. Ends with the enemy line noticeably closer and splashes still rising.
```
- 색 물기둥은 검증 완료(#10) — "tall pink and green dye-colored shell splashes"로 쓴다.
- 폭발이나 피격은 요구하지 않는다(모더레이션 위험을 피하고 행동은 하나로).

### ⑤-5 A03′ 구마노 (C13) — [새 생성]

```text
A 1944 Japanese Mogami-class heavy cruiser with one large raked trunked funnel, three forward twin 8-inch turrets and a tall bridge, moving slowly, its bow missing forward of the first turret so the hull ends in a ragged blunt front low in the water, gray smoke drifting from the forward deck. Seen from a high side angle at distance, the ship clearly still afloat. Morning light, gray sea. Vertical 9:16, photorealistic.
```
- 외형 조건은 #7 검증 결과에 맞춰 조정한다.
- 이미지 요청이 차단되면 우회 재시도하지 않는다. 차선(라벨 삭제)으로 간다.

### ⑤-6 A04′/V_C14′ 손상된 존스턴, 새 축 — [새 생성]

```text
The same Fletcher-class destroyer, now damaged: a scorched bridge front, a bent mast, dark smoke from amidships, moving slowly through a gray rain squall. Seen from a low bow-quarter angle on its starboard side, the opposite side from earlier shots.
```
- 영상 동작은 "rain sweeps across, smoke streams aft, ship keeps slowly moving; camera static" 하나만.

### ⑤-7 C20 대체 (발포 없음) — [새 생성] 또는 [기존]

- V_C18_V2 후반에 깨끗한 구간이 있으면 그것을 쓴다.
- 새로 만든다면 시작 이미지는 "손상된 갑판 위 5인치 포탑 1기, 포신이 현측 바다를 향함, 주변 연기"이고, 영상 동작은 "포탑이 천천히 좌현으로 선회해 멈춘다" 하나다.
- 발포 장면은 앞서 생성 실패 1회와 이미지 차단 1회가 있었으므로 다시 요구하지 않는다.

### ⑤-8 A08′/V_C21 다른 호위함 — [새 생성]

```text
From the smoke-stained deck of a damaged destroyer, two other gray destroyers race past in the middle distance at high speed, bows throwing spray, heading toward the enemy on the horizon. Smoke from the near deck drifts across the lower foreground.
```
- 영상: "the two destroyers keep racing toward the right edge; camera static on the near deck".

### ⑤-9 V_C22 압축 — [새 생성]

```text
One U.S. Navy TBM Avenger banks and dives toward the distant enemy cruiser below. The camera follows alongside, keeping the horizon level. Ends with the aircraft in a steep dive and the ship visible below.
```
- negative: 기존 목록 유지.

### ⑤-10 V_C25 압축 — [새 생성]

```text
The cruiser slowly turns away to the right, its bow swinging first and the whole hull following in one smooth arc while its wake curves behind it. The camera holds still. Ends with the ship heading away toward the open sea.
```
- 지금 프롬프트의 함형·도장·배경 보존 조건 약 15개는 시작 이미지가 맡는다. 길이가 늘면 모델은 앞부분만 따른다.

---

## ⑥ 새 생성 필요 / 기존 소스로 해결

| 기존 소스·편집·오버레이로 해결 (생성 비용 0) | 새 생성 필요 |
|---|---|
| C01 대사 교체, 오프닝 카드를 질문형으로, 방향 화살표 2개 1.2초, JOHNSTON 라벨 앞당김 | A01′/V_C01′ 첫 3초 (빛·방향 근본 수정) |
| C02 질문 앞당김·질문 카드 | C09 정면 저각 (반복 해소) |
| C03 대사 이동 / C04 대사 삭제 + 장소·날짜 카드 | C11 함교 시점 접근 (노출과 물기둥) |
| C05 대사 교체 (임무와 속도) / C06 단축 | A03′ 구마노 (모가미급, 함수 손실) — 차선은 라벨 삭제 |
| C07+C08 한 문장 통합, 대사 끝 여유 | A04′/V_C14′ 새 축 손상 (차선 현행 유지) |
| C10 오버레이 교체(지시선·TORPEDO 삭제, "10 TORPEDOES", 링 강조, 자막 위치 상향) | C20 대체 (발포 없는 손상 포탑) — 차선 V_C18_V2 후반 |
| C12 그래픽 부채꼴 A안 (⑦) | A08′/V_C21 (주인공 시점의 다른 호위함) |
| C13 차선: KUMANO 라벨 삭제 | V_C22 Avenger |
| C16 "10→0" 카드 회수 | V_C25 일본 함대 회항 |
| C18+C19 통합 4초 (V_C18_V2[0,97)) | |
| C20 삭제 (C27 사진 중복 해소) | |
| C23 단축 / C26 헤더 크롭과 대사 / C27 "And Johnston." / C28 대사와 카드 | |
| **음성**: 구절 사이 공백을 평균 0.85초에서 0.25초로 (TTS 재생성 또는 무음 구간 편집; 단어 짜깁기는 아님) → 약 86.7초에서 약 72초 | |
| C26을 사마르 당일 실제 사진으로 교체 — 80-G-287505(갬비어 베이 피격, 적 순양함 보임) 등 퍼블릭 도메인 확인 [외부 자료, #16] | |

**최소 경로 (새 생성 0건으로 할 수 있는 것)**
- 왼쪽 열만 적용해도 문제 1·2·4와 리듬 문제는 대부분 고칠 수 있다.
- 문제 3(반복 구도와 빛)은 새 생성 없이는 부분적으로만 고쳐진다.

**새 생성 우선순위**
1. A01′/V_C01′ — 첫 3초, 시청 유지에 가장 큰 영향.
2. C11 — 접근의 대가를 보여 줌.
3. C09 — 반복 구도 해소.
4. 미생성 3개(C21·C22·C25).
5. A03′, A04′.

---

## ⑦ C12 — "정상 접근 → 별도 손상 결과" 대안은 충분한가

**불충분하다.**
- 이 생략은 정직하지만, 박자상 한가운데에 구멍이 생긴다.
  - C11과 C12를 합쳐 5.5초 동안 같은 넓은 사선이 이어진다. 이 구도는 C02·C09와도 같다.
  - 그 위에서 VO가 "launches"라고 말한다. 대사가 행동을 말하는 순간 그림은 바뀌지 않는다.
- C10에서 보여 준 어뢰는 끝까지 한 번도 움직이지 않는다. 그래서 C13의 결과가 원인 없이 도착한다.

| 안 | 내용 | 수단 | 평가 |
|---|---|---|---|
| **A (1순위)** | 부채꼴 어뢰 궤적 그래픽 | [기존]+[그래픽], 새 생성 0 | 아래 설명 참조 |
| B | 발사관 선회(발사 준비) 영상 + 소리 | [새 생성] 1건 | 무기 방출 없이 기계 동작만 요구 |
| C | 실제 전시 기록 필름 | [외부 자료] | 레지스터 핑퐁, A안보다 후순위 |
| D | 현 제안 + 사운드만 | [기존] | 최후 차선 |

**A안 — 부채꼴 어뢰 궤적 그래픽**
- V_C11[56,133)을 1.0초 쓴 뒤, 같은 프레임 위에 반투명 위에서 내려다본 도식을 2.0초 겹친다. 프레임 정지 0.2초 + 채도 감소.
- 도식 내용:
  - 존스턴 아이콘과 KUMANO 아이콘.
  - 존스턴에서 나가는 흰 궤적 10개가 부채꼴로 0.8초 동안 뻗어 간다.
  - 기존 어뢰 PNG를 축소해 궤적 끝 아이콘으로 쓴다.
- 이 편의 정책은 "길·흐름이 설명의 주동작일 때 성장선 허용"이다. 어뢰 부채꼴은 바로 그 경우다.
- 얻는 것:
  - "10발"과 "한 번에"를 보여 주므로 C16의 "0"이 회수된다.
  - 부채꼴이 회피를 강요한다는 원리도 보인다.
- 정책상 "로컬 그래픽 무통보 대체 금지"이므로 명시적 채택 결정이 필요하다.

**B안 — 발사관 선회 + 소리**
- C10_V2 정지 개념도에서 "발사관 전체가 천천히 현측으로 선회해 멈춘다" 하나만 요구한다.
- 실제 발사관은 함 축선 방향으로 격납돼 있다가 현측으로 돌려야 발사할 수 있다. 무기 방출을 요구하지 않는 기계 동작이다.
- 발사는 화약식 사출음 두 번(사운드)과 컷으로 처리한다.
- 앞서 차단된 "수면 입수" 요청을 다른 말로 다시 시도하는 것이 아니다. 어뢰가 나오지 않는 다른 장면이다.

**C안 — 실제 전시 기록 필름**
- 미 해군 공개 기록 영상 중 플레처급 구축함의 어뢰 발사 장면을 쓰고 "Fletcher-class torpedo launch, archival — not Johnston"으로 표시한다.
- 확보와 권리 확인이 필요하다. 재연 구간 한가운데 기록 영상이 들어가 레지스터가 핑퐁하므로 A안보다 후순위다.

**D안 — 현 제안 + 사운드만**
- "launches" 위치에 사출음 두 번, 그리고 C13으로 스매시 컷.
- 그림은 여전히 바뀌지 않는다. 최후 차선이다.

---

## ⑧ 역사 인과 검증 (NHHC 대조 결과)

별도 사실검증 에이전트가 NHHC 원문(DANFS Johnston·H-Gram 036·Samar 주제 페이지·MOH 표창문·DANFS Gambier Bay/Hoel/Heermann/Kalinin Bay/White Plains 등)을 직접 내려받아 대조했다. 전문: `FACTCHECK_NHHC.md`. 요약:

| # | 주장 | 판정 | 대본에 쓸 때 |
|---|---|---|---|
| 1 | 에번스의 자발적 돌진 | **지지(뉘앙스)** | DANFS "Without having received orders to do so", H-Gram "on his own initiative". 단 Sprague도 연막(07:00)·어뢰 공격(07:16)을 명령했으므로 "명령을 기다리지 않고"라고 쓰고 "명령이 없었다"고는 쓰지 말 것 |
| 2 | 용어 | **확정** | "Center Force"가 공식 용어. "central force"는 수정 |
| 3 | 항모가 도망칠 수 없음 | **지지** | 호위항모 17–19노트 vs 일본 순양함 35노트. "too slow to escape"는 공정한 표현 |
| 4 | 첫 공격 | **지지** | 200발 이상 + 어뢰 10발 전부, 약 10,000야드(≈5해리)에서 발사(~07:20), 명중 07:24–27 |
| 5 | 구마노 함수 절단 | **지지** | H-Gram "blew off her bow", NHHC가 존스턴 공으로 기록, 이설 없음. 속력 12노트로 낙오, 전투 생존, 11/25 침몰. 스즈야도 기함 이동으로 이탈. ⚠ **NH 82400 사진 사용 금지** — 그 함수 손실은 11/6 잠수함 어뢰 |
| 6 | 존스턴 피격 07:30 | **지지(출처 상충)** | DANFS는 야마토 18.1인치 3발+6.1인치 3발, Samar 페이지는 14인치. → "heavy battleship shells, probably Yamato's"로. 조타 동력 상실·17노트·에번스 손가락 절단·스콜 10분 피신 모두 확인 |
| 7 | 모가미급 외형 | **지지** | 트렁크형 대형 연돌 1개 + 연장 포탑 5기(전방 3). **연돌 2개짜리 A02/A03은 다른 급(조카이·하구로 계열) 외형** — C13 함형 지적 확정 |
| 8 | 2차 공격 | **지지** | 어뢰 소진 후 포격 지원 합류, 야하기 구축함대 격퇴(항공기와 함께), 갬비어 베이를 위해 포화 유인(시도는 실패). MOH "diverted the powerful blasts of hostile guns from the… carriers" |
| 9 | 수동 조타 | **지지** | MOH 표창문: 함미에서 열린 해치로 조타 명령을 외침 |
| 10 | 색 물기둥 | **지지** | 염료 포탄 — 핏빛·분홍·황록 물기둥. C11 물기둥 연출에 사용 가능 |
| 11 | 폭탄 없는 급강하 | **지지** | DANFS Gambier Bay·Fanshaw Bay: "dummy runs without weapons". C22 대사 근거 확보 |
| 12 | 쿠리타 철수 | **지지(뉘앙스)** | "a little after 9 a.m."(09:11~09:20 출처별 상이). 원인: 공세성+항공 공격+상황 인식 부족+운. 항공기 공을 반드시 포함 |
| 13 | 손실 | **지지** | 갬비어 베이 09:11, 호엘 08:55, 로버츠 ~10:05(2차 출처), 존스턴 10:10, 세인트 로는 그날 늦게 가미카제. 존스턴 승조 327/생존 141/전사 186 |
| 14 | 에번스 | **지지(뉘앙스)** | 밤에 물 위에서 마지막 목격, 미귀환. 추서 명예훈장, 미 해군 최초의 아메리카 원주민 수훈자. "배와 함께 가라앉았다"고 쓰지 말 것 |
| 15 | 취역사 인용문 | **지지(회고)** | "This is going to be a fighting ship…"은 NHHC 게재본이 있으나 1945년 Hagen 회고 — 쓰려면 "as survivors remembered" |
| 16 | 실전 사진 | **확인** | 사마르 당일 공식 사진 존재·퍼블릭 도메인: 갬비어 베이 피격+적 순양함 80-G-287505, 연막 80-G-288885 외, 화이트 플레인스 지근탄 80-G-288886 외 → C26 교체 후보 |
| 17 | 빛·날씨 | **역광 거짓** | 아침 전투. 태양 방위 약 102°(동남동) — **미군 등 뒤**. 일본군은 북북서(방위 345°)에서 접근. 스콜·낮은 구름. **일본 함대 뒤 황금 역광은 성립 불가** → 전 컷 조명 교체 근거 확정 |
| 18 | 일본 함장의 경례 | **지지(단일 증언)** | H-Gram 수록, 함장 이름 미상. 쓰려면 "생존자들의 증언으로는" |

**판정표 반영**: C09·C13·C14·C16·C20·C22·C28 수정안 대사의 사실 근거가 모두 확보됐다. C28은 "Evans was last seen in the water that night."가 가장 정확하다. ⑤-4의 물기둥은 "tall pink and green dye-colored splashes"로 쓸 수 있다. ⑤의 모든 새 생성은 "golden backlit" 대신 "grey squally dawn, low overcast, sun low behind the camera(미군 시점)"로 통일한다.

---

## ⑨ 페르소나 비평 — 「신비한 건축사전」 × 「문명」 → Fable 통합 판정

**검수 한계: 두 페르소나와 이 Fable 판정 모두 연속 영상·음성을 확인하지 못했다. 대본(영어 내레이션), 장면표 시간, 기준이미지 7장(A01~A08), C10 합성본(540×960)만으로 판정했다.**


대상은 표류자 회차가 아니라 완전 사실 기반 전쟁사 쇼츠(외부 제작물)다. 페르소나 카드의 편향 절(`/home/user/lastprice/new_channel/pyoryuja/review/personas/geonchuk_sajeon.md` §5, `/home/user/lastprice/new_channel/pyoryuja/review/personas/munmyeong.md` §6)과 대조하되, 표류자 바이블 충돌 항목(정밀 숫자 유지, 연재 장치 유지)은 이 대상에 구속력이 없으므로 가독성과 단발 완결성 기준으로만 판정했다. 허구 연출을 요구한 제안은 양측 모두 없었다 — 오히려 두 페르소나가 'AI 얼굴 생성 금지·가짜 유언 금지'를 지킬 점으로 재확인했다.

### 1. 페르소나별 채점표와 한 줄 총평

**「신비한 건축사전」 제작자 — 합계 16/30**

| 축 | 훅·첫3초 | 구조·페이싱 | 대사·내레이션 | 오버레이·도면 | 제목·소재 | 반복가능성 |
|---|---|---|---|---|---|---|
| 점수 | 2 | 3 | 4 | 2 | 3 | 2 |

> 총평: "문장은 이미 내 채널 수준(2.1단어/초)이지만, 목적 답이 런타임 95~99% 지점에 처음 나오고 설명 장치가 콜아웃 1장뿐 — '질문→답'이 아니라 '연대기 끝에 교훈'으로 읽힌다."

**「문명」 제작자 — 합계 15/30**

| 축 | 훅·연결 | 구조·페이싱 | 대사·비유 | 캐릭터·관계 | 연재 장치 | 운영 |
|---|---|---|---|---|---|---|
| 점수 | 3 | 3 | 2 | 2 | 2 | 3 |

> 총평: "첫 프레임과 정직한 결말은 좋지만, 에번스가 25.3초에야 이름으로·78.7초에야 얼굴로 나와 '배의 기동 기록'이지 '한 사람의 선택'으로 읽히지 않는다."

판정자 메모: 같은 대본에 대사 축이 4(건축사전) vs 2(문명)인 것은 모순이 아니다. 전자는 명료성·리듬(문장당 정보 1개, 시제 설계)을, 후자는 인용 가능성(귀에 남는 문장, 모티프)을 재는 축이다. 두 축 모두 타당하며, 반영 권고는 명료성을 유지한 채 인용 가능성을 올리는 방향으로 통합했다.

### 2. 두 페르소나가 합의한 문제 (가장 강한 신호)

독립적으로 작성된 두 비평이 같은 컷·같은 결론에 수렴한 지점이다. 최우선 반영 대상.

1. **핵심의 후치(後置)** — 건축사전: 목적 답("to give the men behind him a chance")이 82.6~85.6s, 런타임 95~99% 지점. 문명: 주인공 이름 25.3s, 얼굴 78.7s. 같은 병의 두 증상 — '왜'와 '누가'가 모두 뒤에 있다.
2. **C21/A08 연속성 오류** — 양측이 문장 수준까지 동일하게 지적: 손상된 존스턴 직후 같은 구도·멀쩡한 동형함이 나와 "존스턴이 수리됐다"로 오독된다.
3. **C12 발사 장면 생성 리스크** — 양측 모두 '어뢰 공격이 화면에서 빌 수 있다'를 지적하고, 생성 실패와 무관한 대체 연출(전술도/카운터)을 각자 제시.
4. **C10 콜아웃 미완** — 건축사전: 지시선이 안 보이고 박스가 엉뚱한 대상(하늘의 어뢰 PNG)에 붙음. 문명: 지시선이 관 측면에서 끊기고 보유 개수가 없음.
5. **C16 어뢰 소진이 화면에 없음** — 양측 모두 C10 콜아웃을 같은 자리에서 회수하라고 제안(건축사전 '0 LEFT' / 문명 '×0').
6. **중반(36~80s) 처짐** — 건축사전: 답 전 44초가 질문을 진척시키지 않음. 문명: 정점 직후 10.7초간 주인공 퇴장. 압축 후 재배분 방향 일치.
7. **C28 엔딩 재설계** — 8초 단일 정지 초상을 분할하고, "Evans never came home."을 추가하고(양측이 같은 문장을 독립 제안), A01 첫 프레임으로 복귀.
8. **지킬 것도 합의** — A01 구도(방향 분기만으로 '선택'이 보임), A01/A04 비포-애프터 짝, 원톤 공식 초상·음성 CTA 없음·부풀리지 않는 결과 진술, C10 콜아웃의 형식 자체.

### 3. 반영 권고 (컷 번호·구체 수정안·제안자)

1. **C01–C03 훅 재구성** [통합: 문명 인물 선제 + 건축사전 오버레이·질문]
   - C01(0~3.1s): "The carriers turn away." (4단어)
   - C02(3.1~6.75s): "Commander Ernest Evans turns his destroyer toward the Japanese fleet." (10단어 — C01+C02 합산 14단어/6.75s ≈ 2.1단어/초, 현행 리듬 유지)
   - C03(6.75~9.96s): "How does charging battleships protect anyone?" [건축사전 질문 변형]
   - 오버레이 시차 배치로 글자 과밀 회피: 0.3s부터 빨간 6px 곡선 화살표(존스턴 함수→수평선 함대) + 'JAPANESE FLEET' 라벨 박스 [건축사전], 1.0~2.5s 'USS JOHNSTON · CDR. ERNEST EVANS' 이름표 [문명].
2. **C09 — 답과 선택의 조기화** [통합]
   - 대사: "No one orders him in. Evans attacks anyway — to slow the chase." (근거가 '명령 전'을 지지하지 않으면 "Evans doesn't wait for orders. He attacks — to slow the chase."로 강도 하향) [문명 프레이밍 + 건축사전 목적절]
   - 'Evans' 발화 순간 C28과 같은 공식 초상을 원톤 그대로 0.8s 삽입 + 'CDR. ERNEST E. EVANS' 이름표 — 얼굴의 '소개'와 '상실' 시점 분리 [문명].
   - C09 앞 2.0s는 평면 전술도(항모 3·연막 띠·일본 함대·존스턴 곡선 화살표, 라벨 2개) [건축사전].
3. **C13 — 성과 문장과 보상 연출** [통합]: "Kumano falls back, damaged. That buys the carriers time." [건축사전 인과 + 문명의 'but still afloat' 삭제]. A03에 빨간 선체 윤곽 + 'KUMANO'/'DAMAGED' 라벨 [건축사전], 연기 강화·선수파 축소·이탈 방향 부여로 A02와의 상태 차이를 1초 안에 [문명].
4. **C04–C06 — 지도 + 'Behind him' 씨앗** [통합]: C04 3.29s 전체를 필리핀→사마르 줌 지도('SAMAR' + 'OCT 1944') [건축사전]. 대사는 "October 1944, off Samar. Behind him: small carriers covering the landings. Ahead: battleships and cruisers." — 결말 'men behind him'의 복선 [문명]. C05는 3.8→2.5s [문명].
5. **C10 — 콜아웃 재시공** [통합]: 하늘의 어뢰 PNG 삭제, 배경 40% 감광, 5연장 발사관 관구를 빨간 6px 윤곽선으로, 굵은 지시선을 관 입구까지 [건축사전 + 문명]. 라벨은 주 단어 'TORPEDOES' + 보조 '×10' — 문명의 카운터를 건축사전의 '주 단어 1 + 보조 라벨 1' 틀에 수납(가독성 기준 통과, ×10은 DANFS 확인 후). 대사는 "He has one weapon that can hurt a cruiser." [문명].
6. **C11 — 메커니즘 확장(약 4.7s)** [통합]: "To use it, he has to get close — like a knife in a gunfight." [문명 문장 + 건축사전 비유]. 실사 30% 감광 위에 막대그래프 2줄(긴 회색 'BIG GUNS' / 짧은 빨간 'TORPEDO') + 존스턴 아이콘 진입 [건축사전]. 화면 숫자는 넣지 않음 — 바이블 충돌이 아니라 순수 가독성 판단.
7. **C12 — 생성 리스크 제거** [통합]: C09 전술도의 다음 상태로 교체(어뢰 항적 부채꼴→타격 표시→순양함 이탈) [건축사전] + 상단 카운터 ×10→×0 0.5s 낙하 [문명]. 실사 생성 성패와 무관해진다.
8. **C14–C20 — 재진입을 감정 정점으로** [문명 기본 + 건축사전 부분 수용]
   - C14: "Johnston is hit hard. Evans is wounded, and keeps command." + 손상 함교 근접 구도(A04 전체 구도는 아껴 둠) [문명].
   - C16: 2.0s로 단축, 같은 자리에 회색 'TORPEDOES ×0' 콜아웃으로 C10 회수 [건축사전 단축 + 문명 카운터].
   - C18–C19: "And now comes the harder choice." 삭제(양측 합의). 대사 "Torpedoes gone. Ship crippled. Evans turns back in—", 화면은 A04 전체 구도로 재선회 동작 1회 생성 — 0초 첫 선회와 같은 구도의 '시각 각운' [문명].
   - C20: 1943년 자료사진을 정점에서 제거, 재진입 연속 컷 + "with the guns he has left." 자료사진은 결말 블록 전용('AI 재연=현재, 원톤 기록=추모' 문법) [문명].
9. **C21–C23 — S07 압축 + 갬비어 베이 비트** [문명 기본]: S07을 약 4s "He isn't alone. Other escorts and carrier planes keep attacking." + A06 Avenger 컷으로 압축 — A08을 아예 쓰지 않으므로 합의 문제 2(연속성 오류)가 원천 해소된다. A08을 부득이 쓰면 건축사전의 재구성안(손상 존스턴 전경 + 'OTHER ESCORTS' 라벨)을 폴백으로. 확보한 약 6s로 C26 앞에 유인 비트 삽입: "When cruisers close on Gambier Bay, Evans steers at them to draw their fire. It isn't enough." → C26 "Gambier Bay goes down."(흑백 원본 유지) — 실패와 대가가 있어야 결말이 값싸지 않다 [문명].
10. **용어 통일** [건축사전]: C01 'carriers'(1번 항목에서 자동 해소), C08 "But it cannot stop the chase.", C25 "Eventually, the Japanese fleet turns back."('Center Force'는 화면 보조 라벨로만). 번인 자막 기준선 전 컷 y≈1150~1300(원해상도)으로 상향.
11. **C28 — 분할 엔딩** [통합]: 78.7~81.7s Evans 초상(원톤) + 'ERNEST EVANS'/'COMMANDER' 라벨 + "Evans never came home."(양측 동일 제안) → 81.7~86.7s A01 복귀, C01의 빨간 화살표 재서화 + 항모 쪽 파란 화살표 [건축사전]. 최종 문장은 "He turned toward the guns so the men behind him could turn away." [문명 — §4의 건축사전 동결 지시 기각 참조]. 여운 1.125s는 무자막 A01 프레임으로 하드컷해 쇼츠 루프 [문명 ①안. ②쿠키 자막은 단발물에서 차선].
12. **제작 파이프라인 — 그래픽 템플릿 4종 고정** [건축사전]: 지도 카드 / 평면 전술도(C09·C12에서 상태만 바꿔 재사용, C23은 러닝타임 여유 시 3회차) / 빨간 박스 콜아웃 / 같은 구도 비포-애프터 와이프(A01→A04). 실사 연쇄 컷 약 20→10~12개. 다음 해전 소재부터 함명·지명·화살표만 바꿔 재생산.

시간 수지(개략): 확보 −12.6s(C05 1.3 + C16 단축 ~4.8 + S07 6.7) vs 투입 +8.4s(갬비어 베이 6.0 + C11 연장 2.4) — 약 4s 여유. 여유분은 C23 전술도 또는 재진입 여운에 배분.

### 4. 기각

- **[건축사전] C01 "This looks like a suicide charge." 도입 공식** — 사유: 편향(카드 §2 '겉보기-사실 대비' 도입 공식의 기계적 이식). 'suicide'는 출처 인용 없는 단정 프레이밍으로 사실 기반 채널 톤에 부담이고, 문명의 인물 선제 소개와 충돌한다. 통합 훅(turn away / turns toward)이 대비 기능을 이미 수행한다.
- **[건축사전] C18 삭제·재진입 평탄화("같은 답의 연장")** — 사유: 편향(카드 §5 '캐릭터 축소' 편향과 동근 — 질문 1개 정보 포맷이 두 번째 선택이라는 감정 정점을 군더더기로 본다). 재진입은 이 소재의 심장이므로 문명안(시각 각운)을 채택. 단, 같은 묶음의 C16 단축과 ×0 회수는 수용(3번·8번 항목).
- **[건축사전] C28 최종 문장 동결("한 글자도 바꾸지 말 것")** — 부분 기각. 문명의 대구안이 turn 모티프 3회 반복(훅-정점-결말)을 완성하고 사실 변형이 없다. 건축사전이 지키려던 것(답의 한 문장 재진술, 'turns toward' 회수)은 수정안에도 그대로 남는다.
- **[문명] 상단 함대 실루엣 누적 스트립(인벤토리 UI)** — 사유: 대상 불일치(단발물) + 편향(카드 §6 '자기 외형 신호·연재 장치' 항목). §6 시리즈화 시 재검토.
- **[문명] 57초 클리프행어 분할·쿠키 컷 문법** — 동일 사유. §6으로 이관.
- **보류(기각 아님 — 1차 출처 확정 대기, 확인되면 반영)**: 'I intend to go in harm's way' 취역식 발언 자막[문명], C09 '명령 전 공격' 표현[문명], 어뢰 ×10 수량[문명], 'buys time' 인과[건축사전], 잔해 2021년·6,400m[문명]. 모두 DANFS/NHHC 대조 후 사용 — 두 페르소나 스스로 단 검증 단서를 유지한다.

### 5. 제목 3안 비교와 추천

| 안 | 출처 | 강점 | 약점 |
|---|---|---|---|
| A. "Every Ship Ran Away. This Destroyer Turned Around." | 건축사전 1안 (= 문명 2안 "Everyone Turned Away. One Destroyer Turned In."과 콘셉트 수렴) | 두 페르소나가 독립적으로 같은 콘셉트에 도달한 유일한 제목. A01 첫 프레임과 1:1 일치(제목-훅 일치), turn 모티프가 결말 대구까지 관통 | 함명·시대 정보 없음 |
| B. "He Had No Torpedoes Left. He Went Back In." | 문명 1안 | 가장 구체적인 긴장, ×0 카운터 연출과 직결 | 중반 정점(재진입)을 제목이 선소비 — 57초의 반전이 약해짐 |
| C. "Why a Tiny Destroyer Charged Japan's Battleships" | 건축사전 2안 | '왜' 질문형, 검색·추천 친화 | 대비 없이 평서형에 가까워 A·B보다 클릭 동기가 약함 |

**추천: A** — 수렴 신호가 가장 강하고 훅 화면과 일치한다. 문구는 건축사전판을 쓴다. 문명판의 "Turned In"은 영어에서 '제출하다/잠자리에 들다'로도 읽히는 중의성이 있다.

### 6. 시리즈화 아이디어 (문명 렌즈, 참고용 — 이번 판에는 미적용)

- **'Taffy 3' 5부작**: EP1 존스턴 0~57초(선회→구마노→×0→재진입), 클리프행어 "Evans turns back in—" 정지 + 쿠키 1초 'He isn't the only one.' / EP2 Hoel / EP3 Samuel B. Roberts / EP4 갬비어 베이 시점(존스턴 유인 시도를 반대편에서 회수) / EP5 '왜 일본 함대는 돌아섰나' + 존스턴 침몰·에번스 초상 피날레.
- 상단 고정 스트립: 미군 6 CVE·3 DD·4 DE와 일본 중순양함 실루엣을 회차마다 회색 처리(편성 숫자 확인 후) — 인벤토리식 누적.
- 잔해 발견(2021·2022)은 EP.0 롱폼 프리퀄 겸 떡밥 회수 회차.
- 판정자 주: 시리즈화하더라도 문명 카드 §6 편향(매일 업로드, 자기 외형 신호 모사)은 그대로 기각 대상이다.

### 7. 페르소나 비평 자체에 대한 비평 (사용자 요청)

**건축사전 비평** — 강점: 초 단위·단어/초 정량 근거가 전 이슈에 깔려 있고, 카드 체크리스트(세이프존, 5초 룰, 라벨 ≤2, 비유 1개)를 항목별로 충실히 적용했다. 정본의 '사거리 선 금지' 제약을 존중하며 우회안을 낸 것도 좋다. 약점: ① 거의 모든 fix가 "내 포맷이 된다"로 수렴 — 대상 채널의 정체성(인물 중심 전쟁사) 검토가 없고, 그 결과 에번스라는 인물이 비평 전체에서 사실상 부재한다(카드 §5의 캐릭터 축소 편향이 '언급 자체를 안 하는' 형태로 발현). ② 교체 대사의 사실 검증을 'NHHC 대조 후 확정' 단서로 판정자에게 떠넘기는 패턴. ③ '반복가능성 2'는 하루 5편이라는 자기 기준으로 외부 단발물을 잰 것 — 다만 탈락 원본 5건·권리 미확인 4건 지적 자체는 유효하다. ④ 14건 중 12건이 major로 심각도 변별력이 낮다.

**문명 비평** — 강점: '얼굴의 소개 시점 = 상실 시점 일치'(C09/C28) 지적은 카드 §2의 캐릭터 애착 데이터에 정확히 근거한, 두 비평을 통틀어 가장 독창적인 발견이다. 패키지의 근거 목록(DANFS 유인 시도, 부상 후 지휘)에서 안 쓴 재료를 찾아낸 것도 판정자 입장에서 가장 쓸모 있었다. 약점: ① 13건 중 12건 major — 역시 변별력 부족. ② 거의 모든 fix가 대사 전면 교체라 원 제작자의 보이스 보존 고려가 없다. ③ C02 단독 리듬(10단어/3.67s ≈ 2.7단어/초)처럼 교체 대사의 초당 검산이 군데군데 생략됐다(합산으로만 처리). ④ 연재 문법(카운터·쿠키·클리프행어)을 단발물 유효분과 구분하지 않고 섞어 내 분리를 판정자 몫으로 남겼다 — 카드 §6 편향 절이 경고한 그대로다. ⑤ 한국어 연재 채널 페르소나가 영어 카피라이팅까지 수행하는 것은 카드가 보증하지 않는 능력 가정이다.

**공통·카드 대조**: 둘 다 검수 한계(연속 영상·음성 미확인)를 자진 명시했고, '여운 1.125초' 같은 패키지 수치가 양측에서 일치해 교차 검증이 된다. 채점 축 명칭도 각 카드 §4/§5와 정확히 일치한다. 두 페르소나의 맹점이 정확히 반대(건축사전은 인물 부재, 문명은 포맷 이식 과잉)라서 통합 판정의 재료로는 오히려 상호 보완이 성립했다 — 이 조합 자체는 유지할 가치가 있다. 개선 과제: (a) 두 카드 모두에 "major는 이슈의 1/3 이하" 같은 심각도 배분 규칙 추가, (b) '사실 확인 필요' 단서가 붙은 제안은 페르소나 단계에서 근거 문구를 직접 인용하도록 카드 체크리스트에 명문화, (c) 문명 카드에 '단발물 평가 시 연재 장치 제안은 별도 절로 분리' 지시 추가 — 이번에 판정자가 수동으로 한 일을 카드가 하게 만든다.
#### 판정 후속 — 보류 항목 해소 (NHHC 사실 검증 반영)

페르소나 판정이 "1차 출처 확정 대기"로 남긴 항목들은 ⑧절 검증으로 해소됐다:
- **C09 '명령 전 공격'**: DANFS "Without having received orders to do so" — "doesn't wait for orders" 표현 사용 가능. 단 "No one orders him in"은 과장(Sprague의 연막·어뢰 명령 존재) → 하향안 채택.
- **어뢰 ×10**: 확정(10발 전부 발사) — ×10→×0 카운터 사용 가능.
- **'buys time' 인과**: H-Gram의 지연·혼란 기여 서술로 지지. 단독 공으로 쓰지 않는 조건.
- **취역식 발언**: 1945년 회고 — 자막으로 쓰려면 "as survivors remembered" 필수.
- **잔해 2021년·수심**: 이번 검증 범위 밖 — 시리즈화 시 별도 확인.

---

## ⑩ 내가 장면표를 새로 만든다면 — 재구성 v4

전문은 `STORYBOARD_V4.md`에 있다(21컷 전부의 시간, EN·KO 대사, 행동, 카메라 목적, 연결, 시작 소스, 오버레이, 수단, Veo 프롬프트 7건과 실패 시 대안).

**구조** (81.9초 · 21컷 · 영어 246단어 · 새 Veo 7건 · 그래픽 도식 4컷 · 당일 실사 사진 2장)

| 묶음 | 시간 | 내용 |
|---|---|---|
| B1 질문 | 0.0–6.6 | 항모는 달아나는데 한 척만 포구로 돈다. Why? → Center Force 규모 |
| B2 제약 | 6.6–13.3 | 순양함 ≈35노트 대 항모 17–20노트, 따라잡힌다 → 함재기를 띄울 **시간**이 필요하다(당일 사진) |
| B3 수단과 원리 | 13.3–29.7 | 에번스가 명령을 기다리지 않고 연막을 피우며 돌진(정면 저각, 염료 물기둥) → 어뢰 10발 → **원리 도식**: 맞히지 않아도 회피를 강요하고 회피가 시간을 잃게 한다 → 1만 야드까지, 포화 속으로 |
| B4 결과와 대가 | 29.7–48.5 | 같은 도식으로 10발 부채꼴 → 한 발이 맞아 구마노 낙오(모가미급, 함수 파손) → 07:30 전함 포탄, 손가락 부상, 17노트, 수동 조타 → **재질문** "Why turn toward the guns again?" |
| B5 같은 원리, 두 번째 | 48.5–64.7 | 다른 호위함 엄호 → 갬비어 베이 유인 시도 실패(당일 사진) → 야하기 구축전대가 존스턴 포화와 기총소사에 밀려 90° 선회, 어뢰를 일찍 발사(같은 도식, 역할 반전) → 폭탄 없이 급강하하는 조종사들 |
| B6 목적 회수 | 64.7–81.9 | 9시 조금 지나 Center Force 철수 → 포격 침몰 4척, 327명 중 186명 → 에번스 초상 "last seen in the water that night" → "He turned toward the guns to shield the carriers — and buy them time." → 첫 컷으로 루프 |

**대본 (EN)**
1. The carriers run. One destroyer turns toward the guns. Why?
2. Straight at the Center Force — four battleships, six heavy cruisers.
3. Japan's cruisers can steam nearly twice as fast as the carriers.
4. The carriers can't outrun them. They need time to launch planes.
5. Commander Ernest Evans doesn't wait for orders. He makes smoke and charges.
6. Johnston's guns can't stop a heavy cruiser. Her ten torpedoes might.
7. A torpedo doesn't have to hit. To dodge one, a ship must swing off course — and that costs time.
8. So Johnston closes to within ten thousand yards — under fire.
9. She fires all ten at the cruiser Kumano.
10. One does hit. Kumano limps out of the chase.
11. Minutes later, heavy battleship shells — probably Yamato's — hit Johnston.
12. Evans loses fingers. Johnston is down to seventeen knots — no faster than the carriers.
13. No torpedoes. Her crew steers by hand. Why turn toward the guns again?
14. She covers the other escorts' torpedo run, then tries to draw fire off Gambier Bay. It fails.
15. A Japanese destroyer squadron closes in to torpedo the carriers.
16. Under Johnston's guns and strafing planes, they turn away — and fire too early.
17. Carrier planes are up. Some with no bombs keep diving.
18. A little after nine, under air attack and in confusion, the Center Force breaks off.
19. Four American ships are sunk by gunfire. Johnston is one of them.
20. Evans was last seen in the water that night.
21. He turned toward the guns to shield the carriers — and buy them time.

**새 생성 대 기존 소스**
- 새 생성:
  - Veo 7건(오프닝 선회, 정면 돌진, 구마노 결과, 스콜 속 손상, 재진입, 급강하, 철수)
  - 새 시작 이미지 4장, 편집 1장
- 기존 소스:
  - V_C06(반전, C02·C03), V_C10_V2(C06·C07)
  - 어뢰 PNG(C06·C09), A02·A06(시드)
  - 결말 기록 사진 NH63495·NH92320
- 외부 자료: 사마르 당일 사진 2장(80-G-287497, 80-G-287505)
- 실패 원본 5개와 황금 역광 소스는 쓰지 않는다.

---

## 부록 A. 1단계 독립 잠정평가 원문 (02·03·04를 열기 전 고정)

### 1단계 — 독립 잠정평가 (01 장면표 + 기준이미지만 읽은 상태)

작성 시점: 02·03·04·실패표본을 열기 전. 역사 사실 중 "확인 대기"는 별도 사실검증 결과로 확정한다.

### 전체 인상
- 대본의 뼈대(도주 vs 역행 → 맥락 → 연막의 한계 → 어뢰 공격 → 대가 → 재진입 → 공동 방어 → 결과 → 함장)는 인과가 바르다. 과장·단독 승리담을 피한 절제도 좋다.
- 그러나 **"왜 돌진했나"의 실제 작동 원리(시간 벌기)가 대본에 없다.** 항모가 왜 도망칠 수 없었는지(속도 차), 어뢰가 큰 배에 왜 위협인지(맞히지 않아도 회피 기동을 강요해 시간을 번다)가 빠져, 질문의 답이 마지막 "to give the men behind him a chance"라는 감정 문장 하나에 걸린다. 답이 '추론'이 아니라 '선언'으로 끝난다.
- 화면은 같은 사선 구도(A01·A04·A08)를 세 번 반복하고, 빛(황금 역광)이 C10(흐린 낮)과 충돌한다. 클라이맥스(C18–C20)는 메타 대사 + 1943년 항구 사진으로 가장 약하다.

### 9개 축 잠정 비판
1. **첫 3초**: "The U.S. escort carriers turn away."는 주인공이 아닌 배경 대상을 먼저 말한다. 대비(역행)는 3.08초 뒤, 질문은 6.75초. A01은 함수/항적 방향이 폰 크기에서 모호해 '반대로 돈다'가 그림만으로 읽히지 않는다.
2. **Q/A 순서**: 30초의 "torpedoes can hurt a much larger ship"이 질문의 답처럼 들려 중간 이탈 위험. 50초 재질문("harder choice")은 정보 없는 예고문.
3. **씬 연결**: 01 문서상 C 연결은 의도가 좋으나 S03→S04(연막 해역→발사관 하드컷), S06(C20 자료사진)에서 주체·시간이 끊긴다. 자료사진이 54.6초 중간에 한 번 끼었다가 71.8초부터 다시 나와 '재연↔기록' 레지스터가 핑퐁한다.
4. **대사/영상 역할**: C07 연막, C10 어뢰(+TORPEDO 카드+어뢰 그림), C22 항공기 — 대사가 화면을 읽어 주거나 화면이 대사를 반복(3중 중복). 화면이 '무엇', 대사가 '왜'를 맡도록 분담 필요.
5. **반복 구도**: A01=A04=A08 동일 사선·동일 역광. A08의 두 구축함은 존스턴 복제로 오인 가능. A02/A03(구마노)도 같은 측면 구도.
6. **카메라 목적**: 거의 모든 컷이 "짧게 상승/접근 후 안정". 정보가 늘지 않는 미세 이동이 반복된다. 목적이 분명한 것은 C03(원경 포탑 발견)뿐.
7. **컷 시간**: 맥락(C04–C06) 10.9초는 길고, 정서의 전환점 C19(2.0초)·C18(2.67초)은 짧다. C08 1.96초에 "pursuit"를 보이기엔 짧다. C28 8초 정지 인물사진은 결말 예외로 허용 가능하나 앞의 C26·C27(정지 사진 2장)과 합쳐 15초 정지 구간이 된다.
8. **오버레이**: C10 자막 위치(화면 높이 약 79–82%)가 쇼츠 하단 UI(채널명/설명)와 겹칠 위험. 흰 지시선은 회색 하늘·장비 위에서 거의 안 보임. 빨간 TORPEDO 카드는 대사·그림과 같은 정보.
9. **역사 인과** (확인 대기 포함): 
   - 항모가 느려 도망칠 수 없었다는 전제가 없음.
   - 에번스의 첫 돌진이 명령 전 자발적이었는지(확인 대기) 누락.
   - 구마노의 실제 손상은 함수 절단(확인 대기)인데 A03은 함수 온전.
   - A02/A03 구마노는 연돌 2개 — 모가미급 외형과 불일치 의심(확인 대기).
   - 황금 역광은 아침·남동 태양·스콜 조건과 맞지 않을 가능성(확인 대기).
   - "central force"는 통용 용어 "Center Force"와 다름.
   - C27 "does not make it home"(현재형) → C28 "never came home"(과거형) 시제/표현 중복.
   - C26 "Gambier Bay is lost"만 말해 호엘·새뮤얼 B. 로버츠 상실이 빠짐(분량상 허용 가능, 다만 "Other escorts are fighting too" 뒤 결말에서 사라짐).
   - "to give the men behind him a chance"는 해석이므로 MOH 표창문 같은 근거 문구로 받치는 편이 안전.

### 잠정 컷 판정 (1단계)
| 컷 | 판정 | 핵심 이유 |
|---|---|---|
| C01 | REVISE | 첫 대사가 주인공이 아님, 방향 모호, 역광 |
| C02 | REVISE | 대비 대사를 C01로 당기고 C02는 항적 확인 |
| C03 | KEEP(대사 수정) | 원경 포탑 발견은 목적 있는 카메라. 질문은 더 날카롭게 |
| C04 | REMOVE(대사)/화면 흡수 | 연도·장소는 자막으로, 대사 3.3초 절약 |
| C05 | REVISE | "small carriers" 대신 속도 제약을 말해야 인과 성립 |
| C06 | KEEP(빛 수정) | 위협 대비 하드컷은 유효 |
| C07 | REVISE | 연막을 읽어 주는 대사 → 효과/한계를 말함 |
| C08 | REVISE | 1.96초, C07과 합쳐 하나의 관찰로 |
| C09 | REVISE | '자발적 첫 돌진'(확인 시) 정보 추가, 5.1초 활용 |
| C10 | REVISE | 3중 중복 오버레이, 원리(수선 아래/회피 강요) 부재 |
| C11 | REVISE | 접근의 대가(물기둥) 시각화가 핵심, 카메라 목적 명확화 |
| C12 | UNVERIFIED | 발사 영상 미확정 |
| C13 | REVISE | 함수 손상 반영 필요(확인 대기), 함형 |
| C14 | REVISE | A01과 동일 구도 |
| C15 | — | (01에 없음: 번호 결번) |
| C16 | REVISE | '어뢰 소진'은 발사 시점에 말하는 편이 인과상 명확 |
| C18 | REVISE | 메타 대사 → 구체적 재질문 |
| C19 | REVISE | 전환점인데 2초 |
| C20 | REMOVE/REPLACE | 1943 항구 사진은 '아직 작동하는 함포'의 증거가 아님, 레지스터 핑퐁 |
| C21 | UNVERIFIED | 미생성, A08 구도 반복 |
| C22 | UNVERIFIED | 미생성, 대사 중복 |
| C23 | REVISE | 추상 3항 나열 5.8초 |
| C25 | UNVERIFIED | A07 없음, 미생성, 용어 |
| C26 | REVISE | 캡션 헤더 박힘, 항구 사진 |
| C27 | KEEP(시제 수정) | |
| C28 | REVISE | 해석 문장 근거화, 중복 표현 |

(C15·C17·C24는 01에 없는 결번 — 실제 25컷은 C01–C14, C16, C18–C23, C25–C28.)


## 부록 B. 2단계 보완 메모 원문

### 2단계 보완 메모 (02·03·04·실패표본·source JSON 확인 후)

### 1단계에서 바뀐/강화된 판단
- 제작은 Grok이 아니라 Veo 3.1 Fast(첫 PNG 1장, last frame/참조 미사용, enhance_prompt=true).
- **반복 구도는 1단계 추정보다 심각**: C02=V_C02[0,88), C09=V_C02[88,192)(같은 테이크 후반), C11=V_C02 f191에서 이어 생성, C12 대안=V_C11[56,133). 존스턴 선미 사선+황금 역광이 C01·C02·C09·C11·(C12)·C14·C16·C18·C19에 반복. 실패표본 5장 모두 같은 역광.
- **C20 아카이브 크롭(NH63495)은 C27과 같은 원사진** → 같은 사진이 22초 간격으로 두 번, 다른 의미(작동 함포 vs 추모)로 쓰임.
- **오프닝 카드 "HE TURNED / TOWARD THE GUNS"**: 결말 문장(C28)을 첫 프레임에 미리 공개. "HE"는 25초(C09)까지 미정의. 첫 3초에 카드 4단어 + 다른 문장 VO + 방향 모호 이미지 = 3채널 경쟁.
- 이름표: USS JOHNSTON 라벨이 C09(25.3초)에서야 등장 — 주인공 식별이 25초 늦음.
- **침묵 비율**: 실제 발화 65.5초 / 전체 86.7초 → 약 21초(24%)가 구절 사이 공백. 발화 중 속도는 약 168 wpm로 정상이지만 전체 127 wpm. 컷마다 0.4–0.6초 전 + 0.3–0.6초 후 여백. (ASR 추정 타이밍 기반 계산, 음성 청취 아님)
- 리타임: C04 67→79f, C05 77→91f, C09 104→123f(약 18% 감속) — 정상 속도 시청 안 했으므로 물결/연기 끊김 여부 UNVERIFIED.
- 실패 패턴: 넓은 시드에서 세부 동작 요구(C10 발사관, C12 어뢰, C20 함포) → 모델이 확대하며 세부를 발명(3연장, 엉뚱한 발사 위치, 상부 불덩이). 성공한 C10_V2는 세부 정지이미지에서 정적 동작만 요구한 경우.
- 긍정 프롬프트 안의 부정어 과다: "No painted star or stripes…diamond icons…HUD" 를 쓴 V_C07·V_C08·V_C18_V2·V_C09 계열에서 실제로 별·마름모·빨간 라벨 출현(C09, C18). 부정어 프라이밍 의심(인과 증명은 아님).
- 공통 보일러플레이트 약 120단어가 매 요청 앞에 붙어 핵심 동작이 뒤로 밀림. enhance_prompt=true로 서버 재작성 내용은 미확인.
- C12 프롬프트 내부 충돌: 시작 프레임은 넓은 사선(발사관이 수십 px) ↔ "camera holds this high quarter angle to show the launcher". "existing open tube" ↔ C10에서 확립한 닫힌 캡 5개 + "No tube-cap opening". 발사관이 함 축선 방향으로 격납된 상태 ↔ 현측으로 선회해야 발사 가능.
- C18 프롬프트: pullback + 두 척 등장 + 존스턴 실제 선회 + 손상 유지 + 넓은 끝 — 한 요청에 4개 동작.
- C20 프롬프트: 1초 안에 접근 도착 + 1.5초 발포 + 반동 복귀 + 연기 — 시간 지정이 과밀, "fire" 단어가 기존 화재와 결합해 불덩이.
- 정책상 "로컬 그래픽 무통보 대체 금지" → 그래픽 대안은 명시적 결정으로 채택해야 함.
