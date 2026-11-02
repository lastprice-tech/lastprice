"""15차 커밋 전 키 유출 검사 — scripts/law/leakscan.py 를 그대로 쓰되, 이번 컨테이너에 없는 LAW_OC 는 건너뛴다.

컨테이너가 다시 만들어져 .env(LAW_OC)가 사라졌다(2026-11-02). 15차는 법제처 API 를 쓰지 않으므로 이 세션이 만든
파일에 LAW_OC 가 들어갈 길은 없다. DART_API_KEY 는 환경변수에 있어 그대로 검사한다. 원래 leakscan.py 는 고치지 않는다.

    python3 scripts/dart/leakscan15.py     # 유출 0 이면 exit 0
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "law"))
import leakscan  # noqa: E402


def main():
    keys = leakscan.secrets()
    if "DART_API_KEY" not in keys:
        print("DART_API_KEY 를 못 읽어 검사할 수 없습니다", file=sys.stderr)
        return 2
    hits, n = [], 0
    for p in leakscan.git_files():
        for label, data in leakscan.blobs(p) or ():
            n += 1
            for name, val in keys.items():
                if val.encode() in data:
                    hits.append((label, name))
    skipped = [k for k in leakscan.NAMES if k not in keys]
    print("검사 %d개 · 찾은 키 %s · 이번 컨테이너에 없어 건너뛴 키 %s" % (n, ",".join(keys), ",".join(skipped) or "없음"))
    for label, name in hits:
        print("  유출: %s ← %s" % (label, name))
    print("유출 0" if not hits else "유출 %d건" % len(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
