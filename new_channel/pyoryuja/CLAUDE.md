# 표류자 (new_channel/pyoryuja) — 세션 규칙

이 폴더는 한국어 AI 픽션 쇼츠 「표류자」 제작 키트다. 저장소 루트의 Next.js 앱과는 관계없다. 운영자의 기존 영어 채널(역사공학)과도 섞지 않는다.

- **처음이면 [START_HERE.md](START_HERE.md)부터 읽는다.** 상태, 결정사항, 첫날 순서, 운영자 선호가 거기 있다.
- 원본 데이터는 `ep0N/shots.json`·`overlays.json`이다. `script.md`·`shotlist.md`·`subtitles.srt`·`narration_tts.txt`는 `python3 tools/grok_chain.py ep0N render`의 생성물이므로 직접 고치지 않는다.
- 고친 뒤에는 `python3 tools/grok_chain.py ep0N check`가 "통과 / 경고 0건"이어야 한다.
- `--live`는 xAI 과금이 발생한다. 운영자에게 횟수와 예상 금액을 먼저 말한다. `XAI_API_KEY`는 출력하지도 커밋하지도 않는다.
- 연속 영상·음성을 실제로 보거나 듣지 않았으면 검수했다고 말하지 않는다.
- 한국어로 답한다. 리서치·작업은 Opus, 최종 판정은 Fable.
