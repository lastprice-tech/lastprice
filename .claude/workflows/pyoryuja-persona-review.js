export const meta = {
  name: 'pyoryuja-persona-review',
  description: '표류자 회차를 「신비한 건축사전」·「문명」 제작자 페르소나로 심사하고 Fable 판정으로 반영/보류/기각 분류',
  whenToUse: '표류자 회차의 대본·장면표·오버레이가 check를 통과한 뒤, 영상 생성 전에. args: {episode: "ep01"}',
  phases: [
    { title: 'Persona review', detail: '건축사전 3렌즈 + 문명 3렌즈, 각자 자기 카드만 읽고 심사', model: 'opus' },
    { title: 'Cross-exam', detail: '각 페르소나가 상대의 상위 제안을 자기 기준으로 반박', model: 'opus' },
    { title: 'Judge', detail: '바이블·가드레일·비용 기준으로 A 지금 / B 다음 회차 / C 기각', model: 'fable' },
  ],
}

const ep = (args && args.episode) || 'ep01'
const ROOT = '/home/user/lastprice/new_channel/pyoryuja'
const FILES = `읽을 파일(모두 ${ROOT} 아래, 읽기 전용 — 어떤 파일도 수정하지 말 것):
- ${ep}/shots.json (원본: 내레이션 줄, 샷, 편집·영상 프롬프트, 끝 상태, 효과음)
- ${ep}/script.md, ${ep}/shotlist.md (렌더된 대본·장면표, 타임코드)
- ${ep}/overlays.json, ${ep}/diagram_freshwater_lens.svg, ${ep}/diagram_freshwater_lens_preview.jpg (오버레이·도면; jpg는 Read로 볼 수 있다)
- ${ep}/metadata.md (제목·설명란·고정 댓글·커버·교차 게시)
- ${ep}/build/timeline.json (줄·샷 시각)
- characters/model_sheet_preview.jpg, characters/CHARACTERS.md (캐릭터)
- bible/series_bible.yaml, bible/ledger.json (시리즈 규칙·연속성)`

const PERSONAS = {
  geonchuk: {
    name: '신비한 건축사전 제작자',
    card: `${ROOT}/review/personas/geonchuk_sajeon.md`,
    lenses: [
      { key: 'overlay', title: '오버레이·도면', focus: '도면이 2초 안에 읽히는가, 라벨 수, 숫자 개수와 필요성, 강조선·픽토그램·고대비, 콜아웃 위치와 지시선, 동시에 뜨는 글자 수, 세이프존. overlays.json의 모든 item과 SVG 레이어 순서를 하나씩 본다. 도면 미리보기 jpg를 직접 본다.' },
      { key: 'structure', title: '영상 구조·페이싱', focus: '도입/난관/해결/요약 4파트 매핑, 질문 1개·답 1개인지, 답이 나오는 시각과 그 뒤 길이, 컷마다 새로 보이는 것, 5초 넘게 머무는 그림, 캐릭터 연기 컷의 정보 밀도, 총 길이. timeline.json의 샷 시각으로 계산한다.' },
      { key: 'script', title: '대사·제목', focus: '첫 문장의 겉보기-사실 대비, 첫 3초의 질문, 문장당 정보 1개, 종결어미 통일, 7자/초 초과 문장, 전문 용어와 비유, 요약 문장. 제목·설명란·커버 문구를 자기 식으로 다시 쓴 3안을 낸다(시리즈 접두어는 유지).' },
    ],
  },
  munmyeong: {
    name: '문명 제작자',
    card: `${ROOT}/review/personas/munmyeong.md`,
    lenses: [
      { key: 'serial', title: '연재 장치·캐릭터', focus: '첫 4초의 연결 신호, 아이템 획득의 보상감과 인벤토리 UI, 다음 회 예고와 쿠키, 떡밥 유무(재료 예고와 미스터리 구분), EP.n 참조 콜아웃, 주인공의 선택 순간, 고양이와의 관계 비트, 별명을 부를 만한 습관, 캐릭터 식별성.' },
      { key: 'script', title: '대본·비유·과학 비중', focus: '귀에 남는 비유·문장 1개가 있는가, 과학 비중(PRINCIPLE 슬롯 초 / 총 초), 과학이 "지금 필요한 이유"로 나오는가, 문장 길이·리듬, 3인칭 거리, 실패와 대가의 무게, 결말 유형. 대사를 자기 식으로 고친 예를 3군데 낸다.' },
      { key: 'ops', title: '운영·오버레이 시스템', focus: '제목이 재생목록에서 읽히는가, 고정 댓글(별명 공모·다음 회 시각), 업로드 리듬, 롱폼 이벤트·EP.0·몰아보기 계획, 회차 간 연결(마지막 프레임→다음 회), 인벤토리·지도·상태 자막이 한 시스템으로 보이는가, 도면이 서사를 멈추는가, AI 품질 위험 컷.' },
    ],
  },
}

const REVIEW = {
  type: 'object',
  properties: {
    persona: { type: 'string' },
    lens: { type: 'string' },
    scores: {
      type: 'object',
      properties: {
        hook: { type: 'number' }, structure: { type: 'number' }, script: { type: 'number' },
        overlay: { type: 'number' }, character_serial: { type: 'number' }, title_ops: { type: 'number' },
      },
      required: ['hook', 'structure', 'script', 'overlay', 'character_serial', 'title_ops'],
    },
    first_three_changes: { type: 'array', items: { type: 'string' } },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          location: { type: 'string', description: '샷 ID / 줄 ID / 파일:항목' },
          problem: { type: 'string' },
          evidence: { type: 'string', description: '페르소나 카드의 어떤 규칙·수치에 근거하는지' },
          proposal: { type: 'string', description: '구체 대안: 바꿀 문장·오버레이 값·구조 변경' },
          impact: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['location', 'problem', 'evidence', 'proposal', 'impact'],
      },
    },
    praise: { type: 'array', items: { type: 'string' }, description: '이 페르소나 기준으로 잘한 점(바꾸지 말아야 할 것)' },
  },
  required: ['persona', 'lens', 'scores', 'first_three_changes', 'findings', 'praise'],
}

function reviewPrompt(p, lens) {
  return `당신은 「${p.name}」이다. 먼저 ${p.card} 를 읽고 그 사람의 사실·제작 문법·체크리스트·편향을 자기 것으로 삼아라. 카드에 없는 취향을 지어내지 말고, 카드의 규칙과 수치에 근거해서만 판단하라.

심사 대상: 신규 한국어 픽션 쇼츠 시리즈 「표류자」 ${ep}. 얼굴 없는 현대인과 주황 고양이가 1653년 제주 해안에 표류해 매 회 그 시대 기술 1개를 만들고 원리 1개를 설명한다. 영상은 Grok Imagine으로 만들며, 지금은 영상 생성 전 단계(대본·장면표·오버레이 확정 단계)다.

${FILES}

당신의 렌즈: **${lens.title}** — ${lens.focus}

규칙:
- 카드 3~4절 체크리스트를 항목별로 실제 파일에 대조하라. 통과한 항목은 praise에, 실패한 항목은 findings에 넣어라.
- findings마다 위치(샷 ID·줄 ID·파일:항목)와, 당신이라면 쓸 구체 대안(바꿀 문장 전문, 오버레이 값, 구조 변경)을 써라. "더 좋게"가 아니라 "이렇게"로.
- 점수 6개(1~5)는 카드의 '채점' 절 항목에 맞춰 매긴다(건축사전 4절, 문명 5절). 당신 렌즈 밖 항목도 전체를 본 인상으로 매긴다.
- first_three_changes: 당신이 이 회차를 직접 만든다면 가장 먼저 바꿀 것 3개.
- 시리즈 전제(캐릭터 존재, 1653 제주, 시즌 연재, 한국어)는 바꾸라고 하지 마라. 그 안에서 당신 문법을 최대한 적용하라.
- 모든 파일은 읽기 전용이다. 수정하지 마라.`
}

phase('Persona review')
const jobs = []
for (const key of Object.keys(PERSONAS)) {
  const p = PERSONAS[key]
  for (const lens of p.lenses) {
    jobs.push(() => agent(reviewPrompt(p, lens), {
      label: `${key}:${lens.key}`, phase: 'Persona review', schema: REVIEW, model: 'opus',
    }).then(r => r ? { ...r, persona: key, lens: lens.key } : null))
  }
}
const reviews = (await parallel(jobs)).filter(Boolean)
log(`persona reviews: ${reviews.length}/6 returned, ${reviews.reduce((n, r) => n + r.findings.length, 0)} findings`)

const byPersona = k => reviews.filter(r => r.persona === k)
const topOf = k => byPersona(k).flatMap(r => r.findings.filter(f => f.impact === 'high')).slice(0, 12)

phase('Cross-exam')
const CROSS = {
  type: 'object',
  properties: {
    persona: { type: 'string' },
    objections: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          target_location: { type: 'string' },
          target_proposal: { type: 'string' },
          what_breaks: { type: 'string', description: '그 제안을 받으면 내 기준에서 무엇이 깨지는가' },
          compromise: { type: 'string', description: '둘 다 살리는 절충안이 있으면' },
        },
        required: ['target_location', 'target_proposal', 'what_breaks', 'compromise'],
      },
    },
    agreements: { type: 'array', items: { type: 'string' }, description: '상대 제안 중 내 기준에서도 맞는 것' },
  },
  required: ['persona', 'objections', 'agreements'],
}
const cross = (await parallel([
  ['geonchuk', 'munmyeong'], ['munmyeong', 'geonchuk'],
].map(([me, other]) => () => agent(`당신은 「${PERSONAS[me].name}」이다. ${PERSONAS[me].card} 를 읽고 그 사람이 되어라.
아래는 「${PERSONAS[other].name}」이 같은 회차(「표류자」 ${ep})에 낸 상위 제안이다. 각 제안을 받아들이면 당신 문법에서 무엇이 깨지는지, 절충안이 있는지 말하라. 당신 기준에서도 맞는 제안은 agreements에 넣어라. 필요하면 ${ROOT}/${ep}/script.md 와 shotlist.md 를 확인하라. 파일은 수정하지 마라.

상대 제안:
${JSON.stringify(topOf(other), null, 1)}`, { label: `cross:${me}`, phase: 'Cross-exam', schema: CROSS, model: 'opus' })
  .then(r => r ? { ...r, persona: me } : null)))).filter(Boolean)

phase('Judge')
const VERDICT = {
  type: 'object',
  properties: {
    scoreboard: { type: 'string', description: '페르소나×6항목 평균 점수표(마크다운)' },
    apply_now: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          location: { type: 'string' },
          change: { type: 'string', description: '변경 전 → 변경 후, 파일 필드 단위로 정확히' },
          why: { type: 'string' },
          from: { type: 'array', items: { type: 'string' } },
        },
        required: ['location', 'change', 'why', 'from'],
      },
    },
    next_episodes: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          rule: { type: 'string', description: '바이블/슬롯 템플릿/운영 규칙에 적을 문장' },
          why: { type: 'string' },
          from: { type: 'array', items: { type: 'string' } },
        },
        required: ['rule', 'why', 'from'],
      },
    },
    rejected: {
      type: 'array',
      items: {
        type: 'object',
        properties: { proposal: { type: 'string' }, reason: { type: 'string' }, from: { type: 'array', items: { type: 'string' } } },
        required: ['proposal', 'reason', 'from'],
      },
    },
    conflicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { topic: { type: 'string' }, geonchuk_says: { type: 'string' }, munmyeong_says: { type: 'string' }, our_choice: { type: 'string' }, why: { type: 'string' } },
        required: ['topic', 'geonchuk_says', 'munmyeong_says', 'our_choice', 'why'],
      },
    },
    keep: { type: 'array', items: { type: 'string' }, description: '두 페르소나가 모두 칭찬한 것 — 바꾸지 말 것' },
    verdict: { type: 'string', description: '3~5줄 총평' },
  },
  required: ['scoreboard', 'apply_now', 'next_episodes', 'rejected', 'conflicts', 'keep', 'verdict'],
}
const judged = await agent(`당신은 「표류자」 제작 책임자다. 두 외부 제작자 페르소나(「신비한 건축사전」, 「문명」)의 심사 결과와 교차 심문을 받았다. 판정 기준은 ${ROOT}/bible/series_bible.yaml (world_rules, forbidden_list, serial_slots, style, naming) 와 ${ROOT}/review/PROCEDURE.md 3단계, 그리고 두 페르소나 카드의 '편향' 절(${PERSONAS.geonchuk.card} 5절, ${PERSONAS.munmyeong.card} 6절)이다.

모든 제안을 다음으로 분류하라.
- apply_now (A): 영상 생성 전에 비용 0으로 바꿀 수 있고(대본 문장, 오버레이 값, 도면, 제목, 설명란, 고정 댓글, 샷 설명) 바이블과 충돌하지 않는 것. 파일 필드 단위로 '변경 전 → 변경 후'를 정확히 써라. 내레이션 문장을 바꾸면 음절 수가 ±20% 안에 있어야 타이밍이 유지된다.
- next_episodes (B): 슬롯 템플릿·바이블·운영 규칙을 바꿔야 하는 것. 규칙 문장으로 써라.
- rejected (C): 바이블·정책 충돌, 근거 부족, 카드에 적힌 페르소나 편향에 해당하는 것. 한 줄 이유.
- conflicts: 두 페르소나가 반대 방향을 제안한 주제. 우리 선택과 이유.
- keep: 둘 다 칭찬한 것.
중복은 합치고, 각 항목에 출처 페르소나:렌즈를 from에 적어라. 제안을 받아들이기 전에 실제 파일을 열어 그 지적이 사실인지 확인하라. 파일은 수정하지 마라.

심사 결과:
${JSON.stringify(reviews, null, 1)}

교차 심문:
${JSON.stringify(cross, null, 1)}`, { label: 'judge', phase: 'Judge', schema: VERDICT, model: 'fable' })

return { episode: ep, reviews, cross, judged }
