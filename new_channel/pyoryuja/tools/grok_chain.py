#!/usr/bin/env python3
"""표류자 Grok 체인 실행기 — 레퍼런스 → 시작 프레임 → 영상 → 끝 프레임 → 다음 샷.

설계 원칙
  * 모든 샷은 앞 샷의 '실제로 쓰는 마지막 프레임(아웃 포인트)'에서 출발한다.
      C(이어가기)  시작 프레임 = from 샷의 끝 프레임 그대로 (image 고정)
      A(앵글 컷)   시작 프레임 = from 샷 끝 프레임을 이미지 편집해 카메라만 바꾼 것
      T(시간 점프) 시작 프레임 = from 샷 끝 프레임을 편집해 시간·빛·물때를 바꾼 것
      K(키프레임)  베이스 플레이트 + 레퍼런스로 새로 합성 (S01만)
      F(정지)      from 샷 끝 프레임을 length초 정지 (영상 생성 없음)
  * 매 영상 요청에 캐릭터 레퍼런스를 함께 넣어 체인이 길어져도 정체성이 흐르지 않게 한다.
  * 사람 게이트 2개: 시작 프레임 승인, 클립 승인(아웃 포인트 지정). 승인 전엔 다음 샷으로 안 간다.
  * 모든 요청·응답은 build/evidence/jobs.jsonl 에 남는다(가드레일 B-11 제작 증거).

xAI API (2026-10 docs.x.ai 기준)
  POST /v1/images/generations  {model, prompt, n, aspect_ratio, resolution, quality, response_format}
  POST /v1/images/edits        {model, prompt, image|images[≤5], aspect_ratio, resolution, n, response_format}
  POST /v1/videos/generations  {model, prompt, image, reference_images[≤14], last_frame, keyframes,
                                duration 1-15, aspect_ratio, resolution, generate_audio}
  GET  /v1/videos/{request_id} → status pending|done|failed|expired, video.url
  프롬프트 태그: image 고정 시 <IMAGE_0>=시작 프레임, 레퍼런스는 <IMAGE_1>부터.
  레퍼런스 사용 시 해상도 상한 720p.

사용법 (시리즈 폴더에서)
  python3 tools/grok_chain.py ep01 check            # 린트
  python3 tools/grok_chain.py ep01 render           # 대본·장면표·자막·TTS 원고·오버레이 시간 생성
  python3 tools/grok_chain.py ep01 plan [S05]       # 요청 본문 미리보기 (API 호출 없음)
  python3 tools/grok_chain.py ep01 refs [--only P] --live      # 레퍼런스 후보 생성
  python3 tools/grok_chain.py ep01 pick-ref P 2                # 후보 2번을 P로 확정
  python3 tools/grok_chain.py ep01 sheet                       # 캐릭터 시트 PNG 조립
  python3 tools/grok_chain.py ep01 next --live                 # 다음 단계 1개 진행
  python3 tools/grok_chain.py ep01 approve S03 start --pick 1  # 시작 프레임 승인
  python3 tools/grok_chain.py ep01 approve S03 clip [--take 2] [--out 6.6]
  python3 tools/grok_chain.py ep01 retake S03 [start|clip] --live
  python3 tools/grok_chain.py ep01 status
  python3 tools/grok_chain.py ep01 assemble         # 승인 클립 → build/EP_picture.mp4 (무음 1080x1920)

  --live 없이 실행하면 요청만 출력한다(dry-run). --simulate 는 API 대신 ffmpeg 더미 이미지·영상으로
  전체 흐름을 리허설한다(키 없이 파이프라인 점검용).

의존성: Python 3.10+ 표준 라이브러리, ffmpeg/ffprobe. 키: 환경변수 XAI_API_KEY.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import http.client
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.x.ai/v1"
SERIES = Path(__file__).resolve().parent.parent
PRICE_VIDEO_PER_S = 0.08      # grok-imagine-video-1.5, docs.x.ai/developers/pricing (2026-10)
PRICE_IMAGE = 0.04            # grok-imagine-image-2.0
RETAKE_FACTOR = 2.0           # 예산 가정: 샷당 평균 2회 생성
SLOT_ORDER = ["STATE", "NEED", "HAVE", "GATHER", "FAIL", "PRINCIPLE", "BUILD",
              "TEST", "COST", "UNLOCK", "NEXT", "TAG"]
FORBIDDEN = ["아이", "어린이", "동화", "귀여", "귀엽", "kids", "cute"]
FORBIDDEN_OK = ("아이콘", "아이디", "아이스", "아이템")   # 금칙어로 시작하지만 허용하는 단어
TOKEN_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")


# ───────────────────────────────────────────────────────────── 로딩
class Episode:
    def __init__(self, ep_dir: str):
        self.dir = (SERIES / ep_dir).resolve()
        self.spec = json.loads((self.dir / "shots.json").read_text(encoding="utf-8"))
        self.refs_path = (self.dir / self.spec["refs_file"]).resolve()
        self.refs = json.loads(self.refs_path.read_text(encoding="utf-8"))
        self.ref_by_id = {r["id"]: r for r in self.refs["refs"]}
        ov = self.dir / "overlays.json"
        self.overlays = json.loads(ov.read_text(encoding="utf-8")) if ov.exists() else {"items": []}
        self.build = self.dir / "build"
        self.ref_dir = SERIES / "characters" / "refs"
        self.shots = self.spec["shots"]
        self.shot_by_id = {s["id"]: s for s in self.shots}
        self.lines = self.spec["narration"]
        self.line_by_id = {l["id"]: l for l in self.lines}
        self.state_path = self.build / "state.json"
        self.state = (json.loads(self.state_path.read_text(encoding="utf-8"))
                      if self.state_path.exists() else {"shots": {}, "refs": {}})

    def save_state(self):
        self.build.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def st(self, sid: str) -> dict:
        return self.state["shots"].setdefault(sid, {})

    def ref_file(self, rid: str) -> Path:
        return self.ref_dir / f"{rid}.png"


# ───────────────────────────────────────────────────────────── 타이밍
def syllables(s: str) -> int:
    return len(re.findall(r"[가-힣]", s))


def internal_pauses(s: str) -> int:
    return s.count(",") + max(0, len(re.findall(r"[.?!]", s.strip())) - 1)


def ffprobe_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", str(path)],
                             capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except Exception:
        return None


def measured_tts(ep: Episode, lid: str) -> float | None:
    for ext in ("wav", "mp3", "m4a", "flac"):
        p = ep.build / "tts" / f"{lid}.{ext}"
        if p.exists():
            return ffprobe_duration(p)
    return None


def line_times(ep: Episode) -> dict[str, dict]:
    """내레이션 줄별 시작·끝(초). TTS 파일(build/tts/Nxx.*)이 있으면 실측, 없으면 음절 속도로 계획."""
    r = ep.spec["narration_rules"]
    t, prev_slot, out = r["first_line_at"], None, {}
    for ln in ep.lines:
        if prev_slot and ln["slot"] != prev_slot:
            t += r["slot_gap"]
        spoken = ln.get("tts", ln["text"])
        n = syllables(spoken)
        rate = r["rate_syl_per_s"].get(ln["slot"], r["rate_syl_per_s"]["default"])
        meas = measured_tts(ep, ln["id"])
        d = meas if meas else n / rate + r["comma_pause"] * internal_pauses(spoken)
        out[ln["id"]] = {"start": round(t, 3), "end": round(t + d, 3), "dur": round(d, 3),
                         "syl": n, "rate": round(n / d, 2) if d else 0.0,
                         "measured": bool(meas), "slot": ln["slot"]}
        t += d + ln.get("pause_after", r["pause_default"])
        prev_slot = ln["slot"]
    return out


def resolve(anchor: dict, lt: dict) -> float:
    if "at" in anchor:
        return float(anchor["at"])
    edge = lt[anchor["line"]][anchor.get("edge", "start")]
    return round(edge + float(anchor.get("offset", 0.0)), 3)


def shot_times(ep: Episode, lt: dict) -> dict[str, dict]:
    starts = [resolve(s["start"], lt) for s in ep.shots]
    vd = ep.spec["video_defaults"]
    out = {}
    for i, s in enumerate(ep.shots):
        a = starts[i]
        b = starts[i + 1] if i + 1 < len(ep.shots) else a + float(s.get("length", 3.0))
        screen = round(b - a, 3)
        trim_in = 0.0   # C 포함 전부 0: 앞 샷은 아웃 프레임 직전에서 끝나고, 이 샷의 0번 프레임(=고정한 아웃 프레임)이 그 자리를 잇는다
        gen = None
        if s["link"] != "F":
            gen = int(s.get("duration") or min(15, max(2, math.ceil(screen + trim_in + vd["handle_s"]))))
        out[s["id"]] = {"t_in": a, "t_out": round(b, 3), "screen": screen,
                        "trim_in": trim_in, "trim_out": round(trim_in + screen, 3), "gen_s": gen}
    return out


# ───────────────────────────────────────────────────────────── 프롬프트 조립
def edit_images(ep: Episode, s: dict) -> list[tuple[str, str]]:
    """편집 요청 이미지 순서 [(토큰, 설명)]: SRC, CTX1.., refs.."""
    imgs = [("SRC", f"{s['from']} 끝 프레임" if s["link"] != "K" else f"{s['base']} 레퍼런스")]
    for i, c in enumerate(s.get("context", []), 1):
        imgs.append((f"CTX{i}", f"{c} 끝 프레임"))
    for r in s.get("refs", []):
        imgs.append((r, f"레퍼런스 {r}"))
    return imgs


def video_images(s: dict) -> list[tuple[str, str]]:
    return [("SRC", "시작 프레임(image 고정)")] + [(r, f"레퍼런스 {r}") for r in s.get("refs", [])]


def tagify(text: str, order: list[tuple[str, str]], mode: str) -> str:
    idx = {tok: i for i, (tok, _) in enumerate(order)}

    def sub(m):
        tok = m.group(1)
        if tok not in idx:
            return m.group(0)
        if mode == "api":
            return f"<IMAGE_{idx[tok]}>"
        return f"image {idx[tok] + 1}"
    return TOKEN_RE.sub(sub, text)


def video_prompt(ep: Episode, s: dict, mode: str = "api") -> str:
    order = video_images(s)
    tm = shot_times(ep, line_times(ep))[s["id"]]
    t_end = max(1.0, tm["trim_out"] - 0.3)          # 아웃 포인트 0.3초 전에 끝 상태 도달, 그 뒤는 정지(버려지는 꼬리)
    parts = [s["prompt"],
             f"Pace the action so that this ending is reached at about {t_end:.1f} seconds and then held, "
             f"almost motionless, until the clip ends at {tm['gen_s']} seconds."]
    for r in s.get("refs", []):
        if mode == "api":
            line = s.get("identity", {}).get(r) or ep.spec["identity_lines"].get(r)
        elif s.get("identity", {}).get(r):          # 손만 나오는 샷: 앱용도 같은 제한 문장(토큰만 뺌)
            line = s["identity"][r].replace(" exactly as in {" + r + "}", "")
        else:
            line = ep.ref_by_id.get(r, {}).get("plain")
        if line:
            parts.append(line)
    light = ep.spec["light"][s["light"]]
    parts.append(ep.spec["style_suffix"].replace("{light}", light))
    text = " ".join(parts)
    if mode == "api":
        if not s.get("refs"):          # 레퍼런스 없는 순수 i2v: 태그 대신 평문
            text = text.replace("{SRC} is the first frame.", "The provided image is the first frame.")
        return tagify(text, order, "api")
    return text.replace("{SRC} is the first frame.", "The uploaded image is the first frame.") \
               .replace("{SRC}", "the uploaded image")


def edit_prompt(ep: Episode, s: dict, mode: str = "api") -> str:
    return tagify(s["edit_prompt"], edit_images(ep, s), mode)


# ───────────────────────────────────────────────────────────── 린트
def check(ep: Episode) -> int:
    errs, warns = [], []
    lt = line_times(ep)
    stimes = shot_times(ep, lt)
    seen, c_run, prev = set(), 0, None
    for s in ep.shots:
        sid = s["id"]
        if s["slot"] not in SLOT_ORDER:
            errs.append(f"{sid}: 알 수 없는 슬롯 {s['slot']}")
        if prev and SLOT_ORDER.index(s["slot"]) < SLOT_ORDER.index(prev["slot"]):
            errs.append(f"{sid}: 슬롯 순서 역행 ({prev['slot']} → {s['slot']})")
        link = s["link"]
        if link not in "KCATF":
            errs.append(f"{sid}: link {link} 미정의")
        if link != "K" and s.get("from") not in seen:
            errs.append(f"{sid}: from={s.get('from')} 가 앞 샷이 아님")
        for c in s.get("context", []):
            if c not in seen:
                errs.append(f"{sid}: context {c} 가 앞 샷이 아님")
        if link == "C" and prev and s["from"] != prev["id"]:
            warns.append(f"{sid}: C 링크인데 직전 샷({prev['id']})이 아닌 {s['from']}에서 이어짐 — 컷 이음매 확인")
        c_run = c_run + 1 if link == "C" else 0
        if c_run > 3:
            errs.append(f"{sid}: C 링크 4연속 — 드리프트 방지를 위해 A/T로 재고정")
        for r in s.get("refs", []):
            if r not in ep.ref_by_id:
                errs.append(f"{sid}: 레퍼런스 {r} 가 refs.json에 없음")
        if link in "KAT":
            if not s.get("edit_prompt"):
                errs.append(f"{sid}: {link} 링크에 edit_prompt 없음")
            else:
                n_img = len(edit_images(ep, s))
                if n_img > 5:
                    errs.append(f"{sid}: 편집 이미지 {n_img}장 > 5장 한도")
                allowed = {t for t, _ in edit_images(ep, s)}
                bad = set(TOKEN_RE.findall(s["edit_prompt"])) - allowed
                if bad:
                    errs.append(f"{sid}: edit_prompt 토큰 {sorted(bad)} 가 이미지 목록에 없음")
            if link == "K" and s.get("base") not in ep.ref_by_id:
                errs.append(f"{sid}: K 링크 base={s.get('base')} 없음")
        if link != "F":
            bad = set(TOKEN_RE.findall(s.get("prompt", ""))) - {"SRC"}
            if bad:
                errs.append(f"{sid}: 영상 prompt에는 {{SRC}}만 허용 (발견 {sorted(bad)}) — 레퍼런스는 identity_lines가 붙인다")
            if s.get("light") not in ep.spec["light"]:
                errs.append(f"{sid}: light={s.get('light')} 미정의")
            if len(s.get("refs", [])) > 14:
                errs.append(f"{sid}: 레퍼런스 14장 초과")
            tm = stimes[sid]
            if tm["screen"] <= 0:
                errs.append(f"{sid}: 화면 길이 {tm['screen']}s ≤ 0 — 앵커 순서 확인")
            elif tm["screen"] < 2.0:
                warns.append(f"{sid}: 화면 길이 {tm['screen']}s — 2초 미만 컷")
            if tm["gen_s"] and tm["gen_s"] < tm["trim_out"]:
                errs.append(f"{sid}: 생성 길이 {tm['gen_s']}s < 사용 구간 {tm['trim_out']}s")
            if tm["screen"] > 9.0:
                warns.append(f"{sid}: 화면 길이 {tm['screen']}s — 쇼츠 기준 긴 컷(오버레이로 정보량 보강 필요)")
        seen.add(sid)
        prev = s

    r = ep.spec["narration_rules"]
    for lid, v in lt.items():
        if v["rate"] > r["lint_rate_max"]:
            warns.append(f"{lid}: 말 속도 {v['rate']}음절/s > {r['lint_rate_max']}")
        if v["rate"] < r["lint_rate_min"] and v["syl"] > 3:
            warns.append(f"{lid}: 말 속도 {v['rate']}음절/s < {r['lint_rate_min']}")
    total = stimes[ep.shots[-1]["id"]]["t_out"]
    if not 90 <= total <= 120:
        warns.append(f"총 길이 {total:.1f}s — 시리즈 규격 90~120s 밖")
    if total > 180:
        errs.append(f"총 길이 {total:.1f}s > 180s (쇼츠 상한)")
    l0 = ep.lines[0]
    spoken0 = l0.get("tts", l0["text"])
    first_sent = re.split(r"[.?!]", spoken0)[0]
    v0 = lt[l0["id"]]
    t_first = v0["start"] + v0["dur"] * syllables(first_sent) / max(1, syllables(spoken0))
    if t_first > 2.6:
        warns.append(f"첫 문장이 {t_first:.2f}s에 끝남 — 2.6초 규칙 초과")

    texts = [ep.spec["title"]] + [l["text"] for l in ep.lines] + [l["tts"] for l in ep.lines if l.get("tts")]
    for t in texts:
        for w in FORBIDDEN:
            pat = (rf"(?<![가-힣]){re.escape(w)}" if "가" <= w[0] <= "힣"
                   else rf"(?<![A-Za-z]){re.escape(w)}(?![A-Za-z])")
            for m in re.finditer(pat, t, re.I):
                if not t.startswith(FORBIDDEN_OK, m.start()):
                    errs.append(f"금칙어 '{w}': {t}")
    if len(ep.spec["title"]) > 40:
        errs.append(f"제목 {len(ep.spec['title'])}자 > 40자")

    # 연속성: HAVE 오버레이 = 직전 회 원장 인벤토리
    ledger_p = SERIES / "bible" / "ledger.json"
    if ledger_p.exists():
        ledger = {e["episode"]: e for e in json.loads(ledger_p.read_text(encoding="utf-8"))["episodes"]}
        num = int(ep.spec["episode"].split(".")[1])
        prev_ep, this_ep = ledger.get(f"EP.{num - 1}"), ledger.get(ep.spec["episode"])
        inv = next((o for o in ep.overlays["items"] if o["type"] == "inventory"), None)
        if prev_ep and inv:
            shown = [f"{i['name']}" + ("(0)" if i.get("count") == 0 else "") for i in inv["items"]]
            want = prev_ep["inventory"]
            if sorted(shown) != sorted(want):
                errs.append(f"연속성: HAVE 인벤토리 {shown} ≠ 원장 EP.{num - 1} {want}")
        unlock = next((o for o in ep.overlays["items"] if o["type"] == "inventory_card"), None)
        if this_ep and unlock:
            if unlock["counter"] != f"보유 {len(this_ep['inventory'])}":
                errs.append(f"연속성: 획득 카드 '{unlock['counter']}' ≠ 원장 보유 {len(this_ep['inventory'])}")
            if unlock["item"]["name"] not in this_ep["inventory"]:
                errs.append(f"연속성: 획득 아이템 {unlock['item']['name']} 가 원장 EP 인벤토리에 없음")
        if prev_ep and this_ep and prev_ep["outcome_type"] == this_ep["outcome_type"]:
            errs.append("결말 유형이 직전 회와 같음(연속 2회 금지)")

    sb = ep.overlays.get("safe_box")
    for o in ep.overlays.get("items", []):
        for k in ("start", "end"):
            try:
                resolve(o[k], lt)
            except KeyError as e:
                errs.append(f"오버레이 {o['id']}: 앵커 {e} 해석 불가")
        b = o.get("box")
        if sb and b and not (sb["x0"] <= b["x"] and b["x"] + b["w"] <= sb["x1"]
                             and sb["y0"] <= b["y"] and b["y"] + b["h"] <= sb["y1"]):
            warns.append(f"오버레이 {o['id']}: 세이프존 밖 {b}")

    n_edit = sum(1 for s in ep.shots if s["link"] in "KAT")
    gen_total = sum(v["gen_s"] or 0 for v in stimes.values())
    print(f"샷 {len(ep.shots)}개 (영상 생성 {sum(1 for s in ep.shots if s['link'] != 'F')}, "
          f"시작 프레임 편집 {n_edit}) · 총 {total:.1f}s · 생성 초 합계 {gen_total}s")
    est = gen_total * PRICE_VIDEO_PER_S * RETAKE_FACTOR + n_edit * ep.spec["edit_defaults"]["n"] * PRICE_IMAGE * RETAKE_FACTOR
    print(f"예상 비용(재생성 {RETAKE_FACTOR}배 가정): 영상 ${gen_total * PRICE_VIDEO_PER_S * RETAKE_FACTOR:.2f}"
          f" + 편집 ${n_edit * ep.spec['edit_defaults']['n'] * PRICE_IMAGE * RETAKE_FACTOR:.2f} = 약 ${est:.2f}"
          " (레퍼런스 입력 이미지 과금 여부는 공식 가격표에 없음 — 첫 호출 영수증으로 확인)")
    for w in warns:
        print("  경고 ·", w)
    for e in errs:
        print("  오류 ·", e)
    print("check:", "통과" if not errs else f"오류 {len(errs)}건", f"/ 경고 {len(warns)}건")
    return 1 if errs else 0


# ───────────────────────────────────────────────────────────── 문서 생성
def fmt_ts(t: float, srt: bool = False) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{m}:{s:02d}.{ms // 10:02d}"


def render(ep: Episode):
    lt = line_times(ep)
    stimes = shot_times(ep, lt)
    measured = any(v["measured"] for v in lt.values())
    src = "TTS 실측" if measured else "음절 속도 계획치(TTS 녹음 후 render 재실행 시 실측으로 갱신)"
    ep.build.mkdir(parents=True, exist_ok=True)

    # 자막
    srt = []
    for i, ln in enumerate(ep.lines, 1):
        v = lt[ln["id"]]
        srt.append(f"{i}\n{fmt_ts(v['start'], True)} --> {fmt_ts(v['end'] + 0.15, True)}\n{ln['text']}\n")
    (ep.dir / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")

    # TTS 원고
    tts = [f"# {ep.spec['title']} — TTS 입력본 (줄 ID별로 따로 생성해 build/tts/Nxx.wav 로 저장)",
           "# 톤: 30~40대 성인 다큐 내레이터, 낮고 차분하게, 문장 끝을 내린다. 감탄·과장 금지.", ""]
    for ln in ep.lines:
        tts.append(f"{ln['id']}\t{ln.get('tts', ln['text'])}")
    (ep.dir / "narration_tts.txt").write_text("\n".join(tts) + "\n", encoding="utf-8")

    # 대본
    md = [f"# {ep.spec['title']} — 대본", "",
          f"- 세계: {ep.spec['world']['day']} · {ep.spec['world']['date']} · {ep.spec['world']['location']} · 결말 유형 {ep.spec['world']['outcome_type']}",
          f"- 타이밍 출처: {src}",
          f"- 총 길이: {stimes[ep.shots[-1]['id']]['t_out']:.1f}초 · 내레이션 {sum(v['syl'] for v in lt.values())}음절",
          "- 이 파일은 `tools/grok_chain.py render`가 shots.json에서 생성한다. 직접 고치지 말고 shots.json을 고친다.", ""]
    cur = None
    for ln in ep.lines:
        if ln["slot"] != cur:
            cur = ln["slot"]
            shots_in = [s["id"] for s in ep.shots if s["slot"] == cur]
            md += ["", f"## {cur}  ·  화면 {', '.join(shots_in)}", ""]
        v = lt[ln["id"]]
        tts_note = f"  ← 읽기: {ln['tts']}" if "tts" in ln else ""
        md.append(f"- `{ln['id']}` {fmt_ts(v['start'])}–{fmt_ts(v['end'])} ({v['syl']}음절, {v['rate']}/s) **{ln['text']}**{tts_note}")
    md += ["", "## TAG", "", "- 음성 없음. 파도 소리 + 엔드카드 「표류자 EP.1」 · 시즌1", ""]
    (ep.dir / "script.md").write_text("\n".join(md), encoding="utf-8")

    # 장면표
    legend = {"K": "키프레임 합성", "C": "이어가기(앞 끝 프레임 그대로)", "A": "앵글 컷(앞 끝 프레임 편집)",
              "T": "시간 점프(앞 끝 프레임 편집)", "F": "정지 프레임"}
    sl = [f"# {ep.spec['title']} — 장면표 · 영상 프롬프트", "",
          f"타이밍 출처: {src}. 이 파일은 `render`가 생성한다(원본: shots.json).", "",
          "연결 규칙: 모든 샷은 앞 샷에서 **실제로 쓰는 마지막 프레임**에서 출발한다. "
          "C는 그 프레임을 그대로 `image`로 고정하고, A·T는 그 프레임을 이미지 편집해 카메라·시간만 바꾼 뒤 고정한다.", "",
          "| 샷 | 슬롯 | 화면 | 길이 | 생성 | 연결 | 출발 | 장면 |", "|---|---|---|---|---|---|---|---|"]
    for s in ep.shots:
        tm = stimes[s["id"]]
        frm = s.get("from") or s.get("base")
        ctx = f" +{','.join(s['context'])}" if s.get("context") else ""
        sl.append(f"| {s['id']}{' ★' if s.get('hero') else ''} | {s['slot']} | {fmt_ts(tm['t_in'])}–{fmt_ts(tm['t_out'])} | "
                  f"{tm['screen']:.2f}s | {str(tm['gen_s']) + 's' if tm['gen_s'] else '—'} | {s['link']} {legend[s['link']]} | "
                  f"{frm}{ctx} | {s.get('beat', s['desc_ko'])} |")
    sl += ["", "★ = 히어로 샷(재생성 예산 우선 배정)", ""]
    for s in ep.shots:
        tm = stimes[s["id"]]
        sl += ["---", "", f"## {s['id']} · {s['slot']} · {s.get('beat', '')} · {fmt_ts(tm['t_in'])}–{fmt_ts(tm['t_out'])} ({tm['screen']:.2f}s)", "",
               f"**장면** {s['desc_ko']}", "",
               f"- 연결: **{s['link']}** {legend[s['link']]} · 출발 {s.get('from') or s.get('base')}"
               + (f" · 참고 프레임 {', '.join(s['context'])}" if s.get("context") else ""),
               f"- 빛: {s.get('light', '—')} · 레퍼런스: {', '.join(s.get('refs', [])) or '없음'}"]
        if s["link"] != "F":
            sl.append(f"- 생성 {tm['gen_s']}s → 사용 구간 {tm['trim_in']:.3f}–{tm['trim_out']:.3f}s (아웃 포인트 = 다음 샷 출발 프레임)")
        lines_here = [l for l in ep.lines if tm["t_in"] - 0.05 <= lt[l["id"]]["start"] < tm["t_out"]]
        if lines_here:
            sl.append("- 내레이션: " + " / ".join(f"`{l['id']}` {l['text']}" for l in lines_here))
        if s.get("overlay"):
            sl.append(f"- 오버레이: `{s['overlay']}` (overlays.json)")
        sl.append(f"- 효과음: {', '.join(s.get('sfx', []))}")
        sl.append(f"- 끝 상태(다음 샷의 출발점): {s['end_state']}")
        if s["link"] in "KAT":
            order = edit_images(ep, s)
            sl += ["", "**① 시작 프레임 편집** (`/v1/images/edits`, 9:16, 2k)", "",
                   "업로드 순서: " + " · ".join(f"{i}) {d}" for i, (_, d) in enumerate(order, 1)), "",
                   "```text", edit_prompt(ep, s, "api"), "```"]
        elif s["link"] == "C":
            sl += ["", f"**① 시작 프레임** = {s['from']} 승인 클립의 끝 프레임 그대로(편집 없음). 앞 샷은 이 프레임 직전에서 끝나고 이 샷의 첫 프레임이 그 자리를 잇는다."]
        if s["link"] != "F":
            vorder = video_images(s)
            sl += ["", f"**② 영상** (`grok-imagine-video-1.5`, {tm['gen_s']}s, 9:16, 720p, 오디오 끔)", "",
                   "이미지: " + " · ".join(f"<IMAGE_{i}> {d}" for i, (_, d) in enumerate(vorder)), "",
                   "```text", video_prompt(ep, s, "api"), "```", "",
                   "<details><summary>레퍼런스 없이 앱에 시작 프레임 1장만 올릴 때</summary>", "",
                   "```text", video_prompt(ep, s, "app"), "```", "", "</details>"]
        sl += ["", "QC: 머리에 이목구비 없음 · 조끼 주황+버클 3개+왼쪽 호루라기 · 맨발 · 고양이 흰 가슴+흰 앞발 2개+왼귀 홈+목걸이 · "
               "사람·현대 물체·글자 없음 · 손가락 5개 · 물리(물·파도) 자연스러움 · 끝 0.3초 안에 흔들림 없는 프레임", ""]
    (ep.dir / "shotlist.md").write_text("\n".join(sl), encoding="utf-8")

    # 오버레이 절대 시간 + 타임라인
    res = []
    for o in ep.overlays.get("items", []):
        o2 = dict(o)
        o2["t_in"], o2["t_out"] = resolve(o["start"], lt), resolve(o["end"], lt)
        if "build" in o:
            o2["build"] = [{**b, "t": resolve(b["at"], lt)} for b in o["build"]]
        res.append(o2)
    (ep.build / "overlays_resolved.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (ep.build / "timeline.json").write_text(json.dumps({"lines": lt, "shots": stimes}, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    print(f"render 완료 ({src}): script.md, shotlist.md, subtitles.srt, narration_tts.txt, build/overlays_resolved.json, build/timeline.json")


# ───────────────────────────────────────────────────────────── API
class Runner:
    def __init__(self, ep: Episode, live: bool, simulate: bool):
        self.ep, self.live, self.sim = ep, live, simulate
        self.key = os.environ.get("XAI_API_KEY")
        if live and not simulate and not self.key:
            sys.exit("XAI_API_KEY 환경변수가 없습니다.")
        (ep.build / "evidence").mkdir(parents=True, exist_ok=True)

    # 요청 기록 (base64는 경로·해시로 치환)
    def log(self, kind: str, body: dict, resp: dict | None, files: dict):
        rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "kind": kind,
               "simulated": self.sim, "body": scrub(body), "inputs": files,
               "response": scrub(resp) if resp else None}
        with open(self.ep.build / "evidence" / "jobs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _req(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        # POST는 요청이 처리되지 않은 게 확실한 429/503만 재시도(중복 생성·이중 과금 방지), GET은 5xx도 재시도
        retry_codes = {429, 503} if method == "POST" else {429, 500, 502, 503, 504}
        for attempt in range(4):
            req = urllib.request.Request(API + path, data=data, method=method,
                                         headers={"Authorization": f"Bearer {self.key}",
                                                  "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:2000]
                if e.code in retry_codes and attempt < 3:
                    print(f"   API {e.code} — {10 * (attempt + 1)}초 후 재시도")
                    time.sleep(10 * (attempt + 1))
                    continue
                sys.exit(f"API {e.code} {path}: {msg}")
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
                if method == "GET" and attempt < 3:
                    print(f"   네트워크 오류({getattr(e, 'reason', e)}) — 재시도")
                    time.sleep(10 * (attempt + 1))
                    continue
                sys.exit(f"네트워크 오류 {path}: {getattr(e, 'reason', e)}")
        sys.exit(f"API 재시도 초과: {path}")

    def show(self, kind: str, body: dict, files: dict):
        print(f"\n[{kind}] 요청 본문 (dry-run, 이미지는 경로로 표시)")
        print(json.dumps(scrub(body), ensure_ascii=False, indent=2))
        for k, v in files.items():
            print(f"   {k}: {v}")

    # 이미지 생성/편집 → 후보 파일 목록
    def image(self, kind: str, body: dict, files: dict, out_stem: Path) -> list[Path]:
        if not self.live and not self.sim:
            self.show(kind, body, files)
            return []
        out_stem.parent.mkdir(parents=True, exist_ok=True)
        n = body.get("n", 1)
        outs = [out_stem.with_name(f"{out_stem.name}_cand{i}.png") for i in range(1, n + 1)]
        if self.sim:
            for i, p in enumerate(outs):
                w, h = aspect_px(body.get("aspect_ratio", "9:16"))
                hue = int(hashlib.md5((out_stem.name + str(i)).encode()).hexdigest()[:2], 16) / 255 * 6.28
                sh(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:d=1",
                    "-vf", f"hue=h={hue}", "-frames:v", "1", str(p)])
            self.log(kind, body, {"simulated": True}, files)
            return outs
        path = "/images/edits" if kind.startswith("edit") else "/images/generations"
        body = {**body, "response_format": "b64_json"}
        resp = self._req("POST", path, body)
        got = []
        for i, item in enumerate(resp.get("data", [])):
            p = outs[i] if i < len(outs) else out_stem.with_name(f"{out_stem.name}_cand{i + 1}.png")
            if item.get("b64_json"):
                p.write_bytes(base64.b64decode(item["b64_json"]))
            elif item.get("url"):
                download(item["url"], p)
            got.append(p)
        self.log(kind, body, resp, files)
        return got

    # 영상 생성 → mp4 경로
    def video(self, body: dict, files: dict, out: Path, st: dict | None = None, save=None) -> Path | None:
        if not self.live and not self.sim:
            self.show("video", body, files)
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        if self.sim:
            start = files.get("image")
            n = int(round(body["duration"] * 24))
            # 시작 프레임에서 천천히 줌인하는 더미 영상: 0번 프레임 = 시작 이미지, 이후 프레임은 모두 다름(이음매·아웃 프레임 검증용)
            sh(["ffmpeg", "-y", "-v", "error", "-i", start,
                "-vf", f"scale=720:1280,zoompan=z='1+0.002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=720x1280:fps=24,format=yuv420p",
                "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", str(out)])
            self.log("video", body, {"simulated": True}, files)
            return out
        def clear():
            if st is not None:
                st.pop("pending_rid", None)
                st.pop("pending_out", None)
                save()
        rid = (st or {}).get("pending_rid")
        if rid:                                   # 중단된 요청 이어서 대기(새 생성·이중 과금 없음)
            out = Path(st["pending_out"])
            print(f"   이전 요청 {rid} 이어서 대기")
        else:
            resp = self._req("POST", "/videos/generations", body)
            rid = resp.get("request_id") or resp.get("id")
            self.log("video-submit", body, {"request_id": rid}, files)
            if st is not None:
                st["pending_rid"], st["pending_out"] = rid, str(out)
                save()
        print(f"   request_id={rid} — 생성 대기")
        t0 = time.time()
        while True:
            time.sleep(5)
            jd = self._req("GET", f"/videos/{rid}")
            status = jd.get("status")
            if status == "done":
                url = (jd.get("video") or {}).get("url")
                download(url, out)
                self.log("video", body, {**jd, "request_id": rid}, files)
                clear()
                if False in (jd.get("respect_moderation"), (jd.get("video") or {}).get("respect_moderation")):
                    print("   경고: respect_moderation=false (필터링됨) — 클립 확인 필요")
                return out
            if status in ("failed", "expired"):
                self.log("video", body, {**jd, "request_id": rid}, files)
                clear()
                sys.exit(f"영상 생성 {status}: {json.dumps(jd, ensure_ascii=False)[:800]}")
            if time.time() - t0 > 900:
                sys.exit(f"15분 초과 — 요청 {rid} 은 state에 남아 있으니 next --live 로 다시 대기")
            print(f"   … {status} ({int(time.time() - t0)}s)")


def scrub(o):
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items()}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    if isinstance(o, str) and (o.startswith("data:") or len(o) > 4096):   # data URI·b64_json
        return f"<{len(o)}B sha256:{hashlib.sha256(o.encode()).hexdigest()[:12]}>"
    return o


def sh(cmd: list[str], capture: bool = False) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"명령 실패: {' '.join(cmd[:6])} …\n{r.stderr[-1500:]}")
    return r.stdout + r.stderr if capture else ""


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def aspect_px(ar: str) -> tuple[int, int]:
    a, b = (float(x) for x in ar.split(":"))
    return (720, int(720 * b / a)) if b >= a else (int(720 * a / b), 720)


def data_uri(path: Path) -> str:
    """업로드용 data URI. 3MB 넘는 PNG는 JPEG(q2)로 줄여 보낸다."""
    path = Path(path)
    if path.stat().st_size > 3_000_000:
        small = path.with_suffix(".upload.jpg")
        if not small.exists() or small.stat().st_mtime < path.stat().st_mtime:
            sh(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-q:v", "2", str(small)])
        path = small
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[path.suffix.lower()]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def img_obj(path: Path) -> dict:
    return {"url": data_uri(path)}


# ───────────────────────────────────────────────────────────── 레퍼런스
def cmd_refs(ep: Episode, run: Runner, only: str | None):
    d = ep.refs["defaults"]
    for r in ep.refs["refs"]:
        if only and r["id"] != only:
            continue
        stem = ep.ref_dir / "_candidates" / r["id"]
        sketch = SERIES / r["sketch"] if r.get("sketch") else None
        files, images = {}, []
        if r.get("from"):
            src = ep.ref_file(r["from"])
            if not src.exists() and not (run.sim or not run.live):
                print(f"{r['id']}: 먼저 {r['from']} 를 확정하세요 (pick-ref)")
                continue
            images.append(src)
            files["FROM"] = str(src)
            for i, w in enumerate(r.get("with", []), 1):
                images.append(ep.ref_file(w))
                files[f"WITH{i}"] = str(ep.ref_file(w))
            prompt = r["prompt"]
            tok = ["FROM"] + [f"WITH{i}" for i in range(1, len(r.get("with", [])) + 1)]
            for i, t in enumerate(tok):
                prompt = prompt.replace("{" + t + "}", f"<IMAGE_{i}>")
            kind = "edit-ref"
        elif sketch and sketch.exists():
            images.append(sketch)
            files["SKETCH"] = str(sketch)
            prompt = r["prompt_from_sketch"].replace("{SKETCH}", "<IMAGE_0>")
            kind = "edit-ref"
        else:
            prompt = r["prompt"]
            kind = "gen-ref"
        body = {"model": d["model"], "prompt": prompt, "n": d["n"],
                "aspect_ratio": r["aspect_ratio"], "resolution": d["resolution"]}
        if kind == "gen-ref":
            body["quality"] = d["quality"]
        if images:
            ok = [p for p in images if Path(p).exists()]
            if len(ok) == len(images):
                if len(ok) == 1:
                    body["image"] = img_obj(ok[0])
                else:
                    body["images"] = [img_obj(p) for p in ok]
            else:
                body["images"] = [f"<{p}>" for p in images]
        outs = run.image(kind, body, files, stem)
        if outs:
            print(f"{r['id']}: 후보 {len(outs)}장 → {outs[0].parent}  (확정: pick-ref {r['id']} <번호>)")


def cmd_pick_ref(ep: Episode, rid: str, num: int):
    cand = ep.ref_dir / "_candidates" / f"{rid}_cand{num}.png"
    if not cand.exists():
        sys.exit(f"후보 없음: {cand}")
    ep.ref_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(cand, ep.ref_file(rid))
    ep.state["refs"][rid] = {"picked": cand.name, "sha256": sha(ep.ref_file(rid)),
                             "at": dt.datetime.now().isoformat(timespec="seconds")}
    ep.save_state()
    print(f"{rid} 확정 → {ep.ref_file(rid)}")


def cmd_sheet(ep: Episode):
    for name, ids in ep.refs["sheet"].items():
        if name.startswith("_"):
            continue
        files = [ep.ref_file(i) for i in ids if ep.ref_file(i).exists()]
        if len(files) < 2:
            print(f"{name}: 확정 레퍼런스 부족 ({len(files)}/{len(ids)})")
            continue
        out = ep.ref_dir / f"{name}.png"
        inputs = sum([["-i", str(f)] for f in files], [])
        fl = "".join(f"[{i}:v]scale=-2:1200,pad=iw+40:1240:20:20:color=0x3a3a3a[v{i}];" for i in range(len(files)))
        fl += "".join(f"[v{i}]" for i in range(len(files))) + f"hstack=inputs={len(files)}"
        sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fl, "-frames:v", "1", str(out)])
        print(f"{name} → {out}")


def probe_fps(p: Path) -> float:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=r_frame_rate", "-of", "default=nw=1:nk=1", str(p)],
                             capture_output=True, text=True, check=True).stdout.strip()
        n, d = out.split("/")
        return float(n) / float(d)
    except Exception:
        return 24.0


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# ───────────────────────────────────────────────────────────── 샷 진행
def out_frame(ep: Episode, sid: str) -> Path:
    return ep.build / "frames" / f"{sid}_out.png"


def start_frame(ep: Episode, sid: str) -> Path:
    return ep.build / "frames" / f"{sid}_start.png"


def need_ref(ep: Episode, rid: str, run: Runner) -> Path:
    p = ep.ref_file(rid)
    if not p.exists() and run.live and not run.sim:
        sys.exit(f"레퍼런스 {rid} 미확정 — refs → pick-ref 먼저")
    return p


def build_edit_body(ep: Episode, s: dict, run: Runner) -> tuple[dict, dict]:
    d = ep.spec["edit_defaults"]
    order = edit_images(ep, s)
    paths = []
    for tok, _ in order:
        if tok == "SRC":
            paths.append(ep.ref_file(s["base"]) if s["link"] == "K" else out_frame(ep, s["from"]))
        elif tok.startswith("CTX"):
            paths.append(out_frame(ep, s["context"][int(tok[3:]) - 1]))
        else:
            paths.append(need_ref(ep, tok, run))
    files = {tok: str(p) for (tok, _), p in zip(order, paths)}
    body = {"model": d["model"], "prompt": edit_prompt(ep, s, "api"), "n": d["n"],
            "aspect_ratio": d["aspect_ratio"], "resolution": d["resolution"]}
    if all(Path(p).exists() for p in paths):
        if len(paths) == 1:
            body["image"] = img_obj(paths[0])
        else:
            body["images"] = [img_obj(p) for p in paths]
    else:
        body["images"] = [f"<{p}>" for p in paths]
    return body, files


def build_video_body(ep: Episode, s: dict, gen_s: int, run: Runner) -> tuple[dict, dict]:
    v = ep.spec["video_defaults"]
    start = start_frame(ep, s["id"])
    refs = [need_ref(ep, r, run) for r in s.get("refs", [])]
    files = {"image": str(start), **{f"ref:{r}": str(p) for r, p in zip(s.get("refs", []), refs)}}
    ready = start.exists() and all(p.exists() for p in refs)
    body = {"model": v["model"], "prompt": video_prompt(ep, s, "api"), "duration": gen_s,
            "aspect_ratio": v["aspect_ratio"], "resolution": v["resolution"],
            "generate_audio": v["generate_audio"],
            "image": img_obj(start) if ready else f"<{start}>"}
    if refs:
        body["reference_images"] = [img_obj(p) for p in refs] if ready else [f"<{p}>" for p in refs]
    if s.get("last_frame"):
        lf = ep.build / "frames" / s["last_frame"]
        body["last_frame"] = img_obj(lf) if lf.exists() else f"<{lf}>"
    return body, files


def source_shas(ep: Episode, s: dict) -> dict:
    """시작 프레임이 어떤 입력에서 나왔는지(출발·참고 샷 끝 프레임, K는 베이스 레퍼런스)."""
    if s["link"] == "K":
        f = ep.ref_file(s["base"])
        out = {f"ref:{s['base']}": sha(f) if f.exists() else None}
    else:
        out = {d: ep.st(d).get("out_sha") for d in [s["from"]] + s.get("context", [])}
    for r in s.get("refs", []):                       # 편집·영상 요청에 들어간 레퍼런스도 출처다
        f = ep.ref_file(r)
        out[f"ref:{r}"] = sha(f) if f.exists() else None
    return out


def invalidate_downstream(ep: Episode, sid: str) -> list[str]:
    """sid의 끝 프레임이 바뀌면, 그 프레임에서 (직·간접으로) 출발한 모든 샷을 미승인으로 되돌린다."""
    dead, hit = {sid}, []
    for x in ep.shots:
        if x["id"] == sid:
            continue
        if x.get("from") in dead or set(x.get("context", [])) & dead:
            dead.add(x["id"])
            stx = ep.st(x["id"])
            if any(stx.get(k) for k in ("start_ok", "start_cands", "clip_ok")):
                hit.append(x["id"])
            for k in ("start_ok", "start_cands", "clip_ok", "src_shas"):
                stx.pop(k, None)
    return hit


def current_takes(ep: Episode, sid: str) -> list[int]:
    """지금 시작 프레임으로 만든 take 번호들(이전 시작 프레임으로 만든 클립은 제외)."""
    st, sf = ep.st(sid), start_frame(ep, sid)
    cur = sha(sf) if sf.exists() else None
    return [i + 1 for i, src in enumerate(st.get("clip_src", [])) if src == cur]


def step(ep: Episode, run: Runner, sid: str, retake: str | None = None):
    s = ep.shot_by_id[sid]
    st = ep.st(sid)
    tm = shot_times(ep, line_times(ep))[sid]
    live = run.live or run.sim
    if retake:
        for k in (("start_ok", "start_cands", "clip_ok", "src_shas") if retake == "start" else ("clip_ok",)):
            st.pop(k, None)
        ep.save_state()   # 하류 무효화는 새 끝 프레임을 승인할 때 cmd_approve 의 out_sha 비교로 한다(끝 프레임이 같으면 하류 재사용)
    if live and s["link"] != "K" and not st.get("start_ok"):
        for dep in [s["from"]] + s.get("context", []):
            if not ep.st(dep).get("clip_ok"):
                sys.exit(f"{sid}: 출발/참고 샷 {dep} 이 아직 승인되지 않음")

    # 1) 시작 프레임
    if s["link"] == "F":
        if not out_frame(ep, s["from"]).exists():
            sys.exit(f"{sid}: {s['from']} 끝 프레임 없음")
        st.update({"start_ok": True, "clip_ok": True, "freeze_of": s["from"], "length": tm["screen"],
                   "src_shas": source_shas(ep, s)})
        ep.save_state()
        print(f"{sid}: 정지 프레임({s['from']}) {tm['screen']}s — 완료")
        return
    if not st.get("start_ok"):
        if s["link"] == "C":
            src = out_frame(ep, s["from"])
            if src.exists():
                start_frame(ep, sid).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, start_frame(ep, sid))
                st["start_ok"] = True
                st["src_shas"] = source_shas(ep, s)
                ep.save_state()
                print(f"{sid}: C 링크 — {s['from']} 끝 프레임을 시작 프레임으로 고정")
            elif live:
                sys.exit(f"{sid}: {s['from']} 끝 프레임 없음 — approve {s['from']} clip 먼저")
        else:
            if st.get("start_cands") and not retake:
                print(f"{sid}: 시작 프레임 후보 대기 중 → {st['start_cands']}\n"
                      f"   확인 후: approve {sid} start --pick <번호>   (다시: retake {sid} start --live)")
                return
            body, files = build_edit_body(ep, s, run)
            outs = run.image(f"edit-start:{sid}", body, files, ep.build / "frames" / f"{sid}_start")
            if outs:
                st["start_cands"] = [str(p) for p in outs]
                ep.save_state()
                print(f"{sid}: 시작 프레임 후보 {len(outs)}장 → approve {sid} start --pick <번호>")
                return
    # 2) 영상
    if not st.get("start_ok") and live:
        return
    if current_takes(ep, sid) and not st.get("clip_ok") and not retake:
        print(f"{sid}: 클립 검수 대기 → {st['clips'][current_takes(ep, sid)[-1] - 1]}\n"
              f"   확인 후: approve {sid} clip [--take N] [--out 초]   (다시: retake {sid} clip --live)")
        return
    if st.get("clip_ok"):
        print(f"{sid}: 이미 승인됨")
        return
    body, files = build_video_body(ep, s, tm["gen_s"], run)
    take = len(st.get("clips", [])) + 1
    out = run.video(body, files, ep.build / "clips" / f"{sid}_t{take}.mp4", st, ep.save_state)
    if out:
        st.setdefault("clips", []).append(str(out))
        st.setdefault("clip_src", []).append(sha(start_frame(ep, sid)))
        ep.save_state()
        print(f"{sid}: 클립 take {take} → {out}\n   계획 사용 구간 {tm['trim_in']:.3f}–{tm['trim_out']:.3f}s. "
              f"확인 후: approve {sid} clip --take {take} [--out 초]")


def cmd_next(ep: Episode, run: Runner):
    for s in ep.shots:
        if not ep.st(s["id"]).get("clip_ok"):
            step(ep, run, s["id"])
            if not (run.live or run.sim):
                print("\n(dry-run: 다음 샷 요청은 앞 샷 승인 뒤에 만들어진다)")
            return
    print("모든 샷 승인 완료 → assemble")


def sharpest_near(clip: Path, t: float, window: float = 0.125, margin: float = 1.15) -> float:
    """t 앞뒤 ±window(24fps 기준 3프레임) 안에서 blurdetect 값이 가장 낮은 프레임 시각.
    t 프레임의 흐림이 최솟값보다 margin배 이상 나쁠 때만 옮긴다(샷 길이가 계통적으로 줄지 않게)."""
    a = max(0.0, t - window)
    try:                                   # blurdetect는 ffmpeg 5.1+ — 없으면 보정 없이 진행
        txt = sh(["ffmpeg", "-v", "info", "-ss", f"{a:.3f}", "-t", f"{2 * window + 0.02:.3f}", "-i", str(clip),
                  "-vf", "blurdetect=block_width=32:block_height=32,metadata=print", "-f", "null", "-"], capture=True)
    except SystemExit:
        return t
    frames, cur_t = [], None
    for line in txt.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            cur_t = float(m.group(1))
        m = re.search(r"lavfi\.blur=([\d.]+)", line)
        if m and cur_t is not None:
            frames.append((a + cur_t, float(m.group(1))))
    if not frames:
        return t
    at_t = min(frames, key=lambda f: abs(f[0] - t))
    best = min(frames, key=lambda f: f[1])
    return round(best[0], 4) if at_t[1] > best[1] * margin else round(at_t[0], 4)


def cmd_approve(ep: Episode, sid: str, what: str, pick: int | None, take: int | None,
                t_in: float | None, t_out: float | None, exact: bool):
    s = ep.shot_by_id[sid]
    st = ep.st(sid)
    tm = shot_times(ep, line_times(ep))[sid]
    if what == "start":
        cands = st.get("start_cands") or []
        if not cands:
            sys.exit(f"{sid}: 시작 프레임 후보가 없음")
        if not 1 <= (pick or 1) <= len(cands):
            sys.exit(f"{sid}: --pick 는 1~{len(cands)}")
        p = Path(cands[(pick or 1) - 1])
        sf = start_frame(ep, sid)
        old = sha(sf) if sf.exists() else None
        shutil.copy(p, sf)
        if st.get("clip_ok") and sha(sf) != old:
            st.pop("clip_ok", None)          # 승인 클립은 이전 시작 프레임으로 만든 것 — next 로 다시 생성·승인
            print(f"   시작 프레임이 바뀌어 {sid} 클립 승인 취소")
        st["start_ok"] = True
        st["start_pick"] = p.name
        st["src_shas"] = source_shas(ep, s)
        ep.save_state()
        print(f"{sid}: 시작 프레임 확정 ← {p.name}")
        return
    clips = st.get("clips") or []
    if not st.get("start_ok"):
        sys.exit(f"{sid}: 시작 프레임이 미승인/무효 상태 — next 로 시작 프레임부터 다시")
    valid = current_takes(ep, sid)
    if not valid:
        sys.exit(f"{sid}: 현재 시작 프레임으로 만든 클립이 없음 — next 로 생성")
    take = take or valid[-1]
    if take not in valid:
        sys.exit(f"{sid}: take {take} 는 이전 시작 프레임으로 만든 클립 — 사용 가능: {valid}")
    clip = Path(clips[take - 1])
    dur = ffprobe_duration(clip) or 0
    fps = probe_fps(clip)
    a = tm["trim_in"] if t_in is None else t_in
    prev = ep.shots[:[x["id"] for x in ep.shots].index(sid)]
    want = tm["screen"]
    if t_out is None and all(ep.st(x["id"]).get("clip_ok") for x in prev):
        # 앞 샷들의 실제 길이 합에 맞춰 아웃을 정한다 → 프레임 반올림 오차가 샷마다 누적되지 않는다
        t_act = sum(ep.st(x["id"])["length"] if x["link"] == "F" else ep.st(x["id"])["out"] - ep.st(x["id"])["in"]
                    for x in prev)
        want = tm["t_out"] - t_act
    b = (a + want) if t_out is None else t_out
    a, b = round(a * fps) / fps, round(b * fps) / fps
    if b > dur - 0.02:
        print(f"   경고: 아웃 {b:.3f}s 가 클립 길이 {dur:.3f}s 를 넘음 → {dur - 0.05:.3f}s 로 당김")
        b = dur - 0.05
    if not exact:
        b2 = sharpest_near(clip, b)
        d = b2 - b
        if abs(d) > 0.001:
            if s["link"] == "C" or a + d < 0:
                # C: 첫 프레임이 앞 샷 끝과 이어져 있어 인 포인트를 옮기면 이음매가 튄다 → 보정 안 함
                print(f"   (선명 프레임 {b2:.3f}s 발견했지만 {'C 링크' if s['link'] == 'C' else '인 포인트 0 미만'}라 아웃 유지)")
            else:
                a, b = round(a + d, 4), b2      # 인·아웃을 같이 옮겨 화면 길이(=내레이션 동기) 유지
                print(f"   아웃 포인트 → 가장 선명한 프레임 {b:.3f}s (인 포인트도 {d:+.3f}s 이동, 길이 유지)")
    if abs((b - a) - want) > 0.05:
        print(f"   경고: 화면 길이 {b - a:.2f}s ≠ 계획 {want:.2f}s — 이후 샷이 {b - a - want:+.2f}s 밀린다."
              " 의도한 것이면 assemble --force, 아니면 --out 을 다시 지정")
    old_sha = st.get("out_sha")
    of = out_frame(ep, sid)
    of.parent.mkdir(parents=True, exist_ok=True)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, b - 0.5 / fps):.4f}", "-i", str(clip), "-frames:v", "1", str(of)])
    new_sha = sha(of)
    if old_sha and old_sha != new_sha:
        hit = invalidate_downstream(ep, sid)    # 재승인으로 끝 프레임이 바뀌면 하류 무효
        if hit:
            print(f"   끝 프레임이 바뀜 → 하류 샷 승인 취소: {', '.join(hit)}")
    st.update({"clip_ok": True, "take": take, "in": round(a, 4), "out": round(b, 4),
               "fps": fps, "out_frame": str(of), "out_sha": new_sha})
    ep.save_state()
    nxt = [x["id"] for x in ep.shots if x.get("from") == sid or sid in x.get("context", [])]
    print(f"{sid}: 클립 승인 (take {st['take']}, {a:.3f}–{b:.3f}s, 화면 {b - a:.2f}s / 계획 {tm['screen']:.2f}s)\n"
          f"   끝 프레임 → {of}  · 이 프레임에서 출발하는 샷: {', '.join(nxt) or '없음'}")


def cmd_status(ep: Episode):
    for s in ep.shots:
        st = ep.st(s["id"])
        flag = "✔" if st.get("clip_ok") else ("◐" if st.get("clips") or st.get("start_cands") else "·")
        if s["link"] == "F" and st.get("clip_ok"):
            extra = f"정지 {st.get('length')}s ({st.get('freeze_of')})"
        else:
            extra = f"take {st.get('take')} {st.get('in')}–{st.get('out')}s" if st.get("clip_ok") else ""
        if st.get("clip_ok") and st.get("src_shas") != source_shas(ep, s):
            extra += "  ⚠ 출발 프레임·레퍼런스 바뀜 → retake start"
        print(f"{flag} {s['id']} {s['link']} {s['slot']:9} {extra}")
    refs = ep.state.get("refs", {})
    print("레퍼런스 확정:", ", ".join(refs) or "없음")


def cmd_assemble(ep: Episode, force: bool = False):
    planned = shot_times(ep, line_times(ep))
    stale = [s["id"] for s in ep.shots
             if ep.st(s["id"]).get("clip_ok") and ep.st(s["id"]).get("src_shas") != source_shas(ep, s)]
    if stale:
        sys.exit(f"출발 프레임·레퍼런스가 바뀐 샷: {', '.join(stale)} — retake <샷> start 로 다시 만들 것")
    unbound = [s["id"] for s in ep.shots if s["link"] != "F" and ep.st(s["id"]).get("clip_ok")
               and ep.st(s["id"]).get("take") not in current_takes(ep, s["id"])]
    if unbound:
        sys.exit(f"승인 take 가 현재 시작 프레임으로 만든 것이 아님: {', '.join(unbound)} — retake <샷> clip")
    actual, t, worst = {}, 0.0, 0.0
    for s in ep.shots:
        st = ep.st(s["id"])
        if not st.get("clip_ok"):
            sys.exit(f"{s['id']} 미승인 — assemble 불가")
        length = st["length"] if s["link"] == "F" else st["out"] - st["in"]
        actual[s["id"]] = {"t_in": round(t, 3), "t_out": round(t + length, 3), "screen": round(length, 3)}
        worst = max(worst, abs(t - planned[s["id"]]["t_in"]))
        t += length
    (ep.build / "timeline_actual.json").write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
    if worst > 0.1 and not force:
        sys.exit(f"샷 시작 시각이 계획(내레이션 기준)에서 최대 {worst:.2f}s 어긋남 — 아웃 포인트를 고치거나 "
                 "assemble --force 후 build/timeline_actual.json 기준으로 후반 타이밍을 맞출 것")
    parts, filt, i = [], [], 0
    for k, s in enumerate(ep.shots):
        st = ep.st(s["id"])
        if s["link"] == "F":
            parts += ["-loop", "1", "-t", f"{st['length']:.3f}", "-i", str(out_frame(ep, s["from"]))]
            filt.append(f"[{i}:v]scale=1080:1920:flags=lanczos,setsar=1,fps=24,format=yuv420p[v{i}]")
        else:
            clip = st["clips"][st["take"] - 1]
            parts += ["-i", clip]
            half = 0.5 / st.get("fps", 24)
            # 아웃 프레임 직전까지만 쓴다. 다음 샷의 0번 프레임이 (C는 그대로, A/T는 편집본으로) 그 자리를 잇는다 → 화면 길이 = out - in
            end = st["out"] - half
            filt.append(f"[{i}:v]trim=start={max(0.0, st['in'] - half):.4f}:end={end:.4f},setpts=PTS-STARTPTS,"
                        f"scale=1080:1920:flags=lanczos,setsar=1,fps=24,format=yuv420p[v{i}]")
        i += 1
    graph = ";".join(filt) + ";" + "".join(f"[v{k}]" for k in range(i)) + f"concat=n={i}:v=1:a=0[out]"
    out = ep.build / f"{ep.spec['episode'].replace('.', '')}_picture.mp4"
    sh(["ffmpeg", "-y", "-v", "error", *parts, "-filter_complex", graph, "-map", "[out]",
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(out)])
    print(f"picture lock → {out} ({ffprobe_duration(out):.2f}s, 무음, 계획 대비 최대 어긋남 {worst:.2f}s)."
          " 다음: TTS·효과음·오버레이 합성은 기존 파이프라인.")


def cmd_plan(ep: Episode, run: Runner, sid: str | None):
    tm = shot_times(ep, line_times(ep))
    for s in ep.shots:
        if sid and s["id"] != sid:
            continue
        print(f"\n════ {s['id']} {s['slot']} link={s['link']} 화면 {tm[s['id']]['screen']}s 생성 {tm[s['id']]['gen_s']}s")
        if s["link"] in "KAT":
            body, files = build_edit_body(ep, s, run)
            run.show(f"edit-start:{s['id']}", body, files)
        if s["link"] != "F":
            body, files = build_video_body(ep, s, tm[s["id"]]["gen_s"], run)
            run.show("video", body, files)


# ───────────────────────────────────────────────────────────── main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode")
    ap.add_argument("cmd", choices=["check", "render", "plan", "refs", "pick-ref", "sheet", "next", "shot",
                                    "retake", "approve", "status", "assemble"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--live", action="store_true", help="실제 API 호출")
    ap.add_argument("--simulate", action="store_true", help="API 대신 ffmpeg 더미로 리허설")
    ap.add_argument("--only")
    ap.add_argument("--pick", type=int)
    ap.add_argument("--take", type=int)
    ap.add_argument("--in", dest="t_in", type=float)
    ap.add_argument("--out", dest="t_out", type=float)
    ap.add_argument("--exact", action="store_true", help="아웃 포인트 선명도 보정 끄기")
    ap.add_argument("--force", action="store_true", help="assemble: 타이밍 어긋남 경고 무시")
    a = ap.parse_args()
    ep = Episode(a.episode)
    if a.simulate:
        ep.build = ep.dir / "build_sim"
        ep.state_path = ep.build / "state.json"
        ep.ref_dir = ep.build / "refs"
        ep.state = (json.loads(ep.state_path.read_text(encoding="utf-8"))
                    if ep.state_path.exists() else {"shots": {}, "refs": {}})
    run = Runner(ep, a.live, a.simulate)
    if a.cmd == "check":
        sys.exit(check(ep))
    if a.cmd == "render":
        render(ep)
    elif a.cmd == "plan":
        cmd_plan(ep, run, a.args[0] if a.args else None)
    elif a.cmd == "refs":
        cmd_refs(ep, run, a.only)
    elif a.cmd == "pick-ref":
        cmd_pick_ref(ep, a.args[0], int(a.args[1]))
    elif a.cmd == "sheet":
        cmd_sheet(ep)
    elif a.cmd == "next":
        cmd_next(ep, run)
    elif a.cmd == "shot":
        step(ep, run, a.args[0])
    elif a.cmd == "retake":
        step(ep, run, a.args[0], retake=(a.args[1] if len(a.args) > 1 else "clip"))
    elif a.cmd == "approve":
        cmd_approve(ep, a.args[0], a.args[1], a.pick, a.take, a.t_in, a.t_out, a.exact)
    elif a.cmd == "status":
        cmd_status(ep)
    elif a.cmd == "assemble":
        cmd_assemble(ep, a.force)


if __name__ == "__main__":
    main()
