"""커밋 전 키 유출 검사 — LAW_OC(법제처)·DART_API_KEY 값이 git 에 들어가는지 본다.

키 값은 코드에 쓰지 않는다. 환경변수 → 저장소 루트 .env 순으로 읽어 그 문자열을 찾는다.
검사 대상: 스테이징된 파일 + 추적 중인 파일 전부(zip 은 멤버까지). 한 곳이라도 걸리면 exit 1.

    python3 scripts/law/leakscan.py
"""
import os
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NAMES = ("LAW_OC", "DART_API_KEY")


def secrets():
    found = {n: os.environ.get(n, "").strip() for n in NAMES}
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        with open(env, encoding="utf-8") as f:
            for line in f:
                k, _, v = line.strip().partition("=")
                if k in found and not found[k]:
                    found[k] = v.strip().strip('"').strip("'")
    return {k: v for k, v in found.items() if v}


def git_files():
    out = set()
    for args in (["ls-files", "-z"], ["diff", "--cached", "--name-only", "-z"]):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
        out.update(p for p in r.stdout.decode("utf-8").split("\0") if p)
    return sorted(out)


def blobs(path):
    """(표시 이름, 바이트). 스테이징된 내용을 본다 — 작업 트리가 아니라 커밋될 바이트."""
    r = subprocess.run(["git", "show", ":" + path], cwd=ROOT, capture_output=True)
    if r.returncode != 0:          # 스테이징에서 지워진 파일
        return
    data = r.stdout
    yield path, data
    if path.lower().endswith(".zip"):
        import io
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    yield "%s!%s" % (path, n), z.read(n)
        except zipfile.BadZipFile:
            pass


def main():
    keys = secrets()
    missing = [n for n in NAMES if n not in keys]
    if "LAW_OC" in missing:
        print("LAW_OC 값을 못 읽어 검사할 수 없습니다", file=sys.stderr)
        return 2
    hits, n = [], 0
    for p in git_files():
        for label, data in blobs(p) or ():
            n += 1
            for name, val in keys.items():
                if val.encode() in data:
                    hits.append((label, name))
    print("검사 %d개 · 찾은 키 %s · 못 읽은 키 %s" % (n, ",".join(keys), ",".join(missing) or "없음"))
    for label, name in hits:
        print("  유출: %s ← %s" % (label, name))
    print("유출 0" if not hits else "유출 %d건" % len(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
