"""훅·대본 채점에 쓰는 어휘 사전과 텍스트 유틸.

근거: 부정 어휘의 클릭 효과는 10.5만 헤드라인 RCT(Nature Human Behaviour 2023)로
인과 수준 확인 — 이 파일에서 가장 신뢰도 높은 부분이다.
도메인 앵커는 LLM 기반 추천의 토픽 클러스터 오배포 방지용.
"""
from __future__ import annotations

import re

# [강] 가점 부정 렉시콘 — 훅 1문장당 1-2개 가점, 3개 이상은 클릭베이트 톤 감점
NEGATIVE_LEXICON = {
    "missing", "killed", "banned", "wrong", "never", "impossible", "forbidden",
    "collapsed", "mistake", "shouldn't", "shouldnt", "dead", "failed", "gone",
    "lying", "hiding", "cheating", "sinking", "cracked", "stolen", "lost",
}
# 경이감 어휘는 SOLUTION/EFFECT로 미룬다 — 훅에서는 감점
POSITIVE_LEXICON = {"amazing", "beautiful", "incredible", "awesome", "stunning", "wonderful"}

# 도메인 앵커: 역사·공학 식별 명사 (훅 12단어 안에 >=1 필요. 고유명사·연도로도 충족)
ENGINEERING_NOUNS = {
    "bridge", "dome", "wall", "tower", "arch", "vault", "foundation", "beam",
    "column", "concrete", "stone", "iron", "steel", "clamp", "bolt", "pin",
    "aqueduct", "canal", "tunnel", "dam", "castle", "cathedral", "temple",
    "amphitheater", "colosseum", "pyramid", "staircase", "roof", "gate",
    "fortress", "lighthouse", "harbor", "rail", "engine", "crane", "keystone",
    "buttress", "truss", "anchor", "mortar", "brick", "timber", "hull", "mast",
}

STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "it", "its", "this", "that",
    "these", "those", "with", "by", "from", "as", "has", "have", "had", "not",
    "no", "so", "if", "then", "than", "there", "here", "one", "two", "half",
    "you", "your", "they", "their", "them", "he", "she", "his", "her", "who",
    "what", "why", "how", "when", "where", "which", "did", "does", "do",
    "will", "would", "should", "could", "can", "into", "over", "under",
    "before", "after", "still", "just", "every", "all", "some", "any",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z''\-]*")
_NUM_RE = re.compile(r"\d[\d,\.]*")
_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9]|[1-9][0-9]{0,2}\s?(?:AD|BC|BCE|CE))\b")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|(?<=[.!?])$|—|…")


def words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def word_count(text: str) -> int:
    # 숫자 토큰도 발화 단어로 센다 ("47" = one word)
    return len(words(text)) + len(_NUM_RE.findall(text))


def sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENT_SPLIT_RE.split(text) if p and p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def numbers_in(text: str) -> list[float]:
    out = []
    for tok in _NUM_RE.findall(text):
        try:
            out.append(float(tok.replace(",", "")))
        except ValueError:
            pass
    return out


def years_in(text: str) -> list[str]:
    return _YEAR_RE.findall(text)


def is_round_number(n: float) -> bool:
    """반올림 냄새 판정 (heuristic). 20 이상 정수이며 10의 배수면 round로 본다.

    'about 300 tons' -> round. '47 people', '86 days', '1349' -> precise.
    연도(4자리 1000-2029)는 예외 — 연도는 정밀값이다.
    """
    if n != int(n):
        return False
    i = int(n)
    if 1000 <= i <= 2029:  # 연도로 간주
        return False
    return i >= 20 and i % 10 == 0


def proper_nouns(text: str) -> list[str]:
    """문두가 아닌 위치의 대문자 시작 단어 (고유명사 heuristic)."""
    out = []
    for sent in sentences(text):
        toks = sent.split()
        for i, tok in enumerate(toks):
            w = tok.strip(".,!?;:'\"()")
            if i > 0 and w[:1].isupper() and w.lower() not in STOPWORDS and len(w) > 1:
                out.append(w)
    return out


def content_words(text: str) -> list[str]:
    return [w.lower() for w in words(text) if w.lower() not in STOPWORDS and len(w) > 2]


def specificity_tokens(text: str) -> int:
    """구체 토큰 수: 숫자 + 연도 + 고유명사 (구체성 밴드 R03용, 1-2개가 만점)."""
    nums = len(_NUM_RE.findall(text))
    props = len(set(proper_nouns(text)))
    return nums + props


def has_domain_anchor(text: str, max_words: int = 12) -> bool:
    toks = words(text)[:max_words]
    lower = {t.lower() for t in toks}
    if lower & ENGINEERING_NOUNS:
        return True
    head = " ".join(text.split()[:max_words])
    if _YEAR_RE.search(head):
        return True
    return bool(proper_nouns(head))


def negation_hits(text: str) -> list[str]:
    lower = {w.lower() for w in words(text)}
    lower |= {t for t in ("shouldn't",) if t in text.lower()}
    return sorted(lower & NEGATIVE_LEXICON)


def positive_hits(text: str) -> list[str]:
    lower = {w.lower() for w in words(text)}
    return sorted(lower & POSITIVE_LEXICON)
