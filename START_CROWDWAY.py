from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
VENV_DIR = ROOT / ".venv"
SETUP_MARKER = VENV_DIR / ".crowdway_setup_ok"
FRONTEND = ROOT / "frontend"
DIST_INDEX = FRONTEND / "dist" / "index.html"
URL = "http://127.0.0.1:8000"


def banner(text: str) -> None:
    print("\n" + "=" * 58)
    print(text)
    print("=" * 58)


def fail(message: str) -> None:
    print(f"\n[오류] {message}")
    print("\n창이 바로 닫히지 않도록 Enter를 기다립니다.")
    try:
        input()
    except EOFError:
        pass
    raise SystemExit(1)


def run(cmd: list[str], label: str) -> None:
    print(f"\n▶ {label}")
    try:
        subprocess.check_call(cmd, cwd=ROOT)
    except FileNotFoundError:
        fail(f"실행 파일을 찾지 못했습니다: {cmd[0]}")
    except subprocess.CalledProcessError as exc:
        fail(f"{label} 중 문제가 발생했습니다. (종료 코드 {exc.returncode})")


def replace_env_value(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    found = False
    out: list[str] = []
    for line in lines:
        if line.startswith(key + "="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    return "\n".join(out).rstrip() + "\n"


def env_value(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return ""


def ensure_env() -> None:
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            text = ENV_EXAMPLE.read_text(encoding="utf-8")
        else:
            text = "USE_MOCK_CONGESTION=false\nSEOUL_API_KEY=\nGRAPHML_PATH=\n"
        text = replace_env_value(text, "USE_MOCK_CONGESTION", "false")
        ENV_FILE.write_text(text, encoding="utf-8")

    text = ENV_FILE.read_text(encoding="utf-8")
    api_key = env_value(text, "SEOUL_API_KEY")
    if not api_key:
        banner("처음 한 번만: 서울시 API 키 입력")
        print("서울 열린데이터광장에서 발급받은 인증키를 붙여넣고 Enter를 누르세요.")
        print("입력한 키는 이 컴퓨터의 .env 파일에만 저장됩니다.\n")
        try:
            api_key = input("서울시 API 키: ").strip()
        except EOFError:
            api_key = ""
        if not api_key:
            fail("API 키가 입력되지 않았습니다.")
        text = replace_env_value(text, "SEOUL_API_KEY", api_key)
        text = replace_env_value(text, "USE_MOCK_CONGESTION", "false")
        ENV_FILE.write_text(text, encoding="utf-8")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_python_dependencies() -> Path:
    py = venv_python()
    requirements = ROOT / "requirements.txt"
    if not py.exists():
        banner("첫 실행 준비 1/3 — Python 환경 만드는 중")
        run([sys.executable, "-m", "venv", str(VENV_DIR)], "Python 가상환경 생성")

    need_install = not SETUP_MARKER.exists()
    if SETUP_MARKER.exists() and requirements.exists():
        need_install = requirements.stat().st_mtime > SETUP_MARKER.stat().st_mtime

    if need_install:
        banner("첫 실행 준비 2/3 — 서버 패키지 설치 중")
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"], "pip 업데이트")
        run([str(py), "-m", "pip", "install", "-r", str(requirements)], "Python 패키지 설치")
        SETUP_MARKER.touch()
    return py


def npm_executable() -> str:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm", "npm.cmd"]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    fail("Node.js/npm을 찾을 수 없습니다. Node.js를 먼저 설치한 뒤 다시 실행해주세요.")
    raise AssertionError


def newest_frontend_source_mtime() -> float:
    candidates = [
        FRONTEND / "package.json",
        FRONTEND / "package-lock.json",
        FRONTEND / "vite.config.ts",
        FRONTEND / "index.html",
    ]
    src = FRONTEND / "src"
    if src.exists():
        candidates.extend(p for p in src.rglob("*") if p.is_file())
    times = [p.stat().st_mtime for p in candidates if p.exists()]
    return max(times, default=0)


def ensure_frontend() -> None:
    npm = npm_executable()
    node_modules = FRONTEND / "node_modules"
    frontend_ready = (node_modules / "vite" / "package.json").is_file() and (node_modules / "typescript" / "package.json").is_file()
    if not frontend_ready:
        banner("첫 실행 준비 3/3 — 화면 패키지 설치 중")
        run([npm, "--prefix", "frontend", "install"], "프론트엔드 패키지 설치")

    needs_build = not DIST_INDEX.exists()
    if DIST_INDEX.exists():
        needs_build = newest_frontend_source_mtime() > DIST_INDEX.stat().st_mtime
    if needs_build:
        banner("CrowdWay 화면 빌드 중")
        run([npm, "--prefix", "frontend", "run", "build"], "프론트엔드 빌드")


def server_is_running() -> bool:
    try:
        with urllib.request.urlopen(URL + "/health", timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def wait_for_server(process: subprocess.Popen, seconds: float = 35.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        if server_is_running():
            return True
        time.sleep(0.4)
    return False


def main() -> None:
    banner("CrowdWay 초간단 실행기")
    print("처음 한 번은 필요한 파일을 자동 설치해서 조금 걸릴 수 있습니다.")
    print("두 번째부터는 훨씬 빨리 열립니다.")

    ensure_env()
    py = ensure_python_dependencies()
    ensure_frontend()

    if server_is_running():
        banner("CrowdWay가 이미 실행 중입니다")
        print(URL)
        webbrowser.open(URL)
        return

    banner("CrowdWay 실행 중")
    print("잠시만 기다리면 브라우저가 자동으로 열립니다.")
    process = subprocess.Popen(
        [str(py), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
    )

    if not wait_for_server(process):
        if process.poll() is not None:
            fail("서버가 시작되지 않았습니다. 위에 표시된 오류 내용을 확인해주세요.")
        process.terminate()
        fail("서버 시작 시간이 너무 오래 걸렸습니다. 인터넷 연결을 확인해주세요.")

    banner("실행 완료")
    print(f"사이트 주소: {URL}")
    print("브라우저를 닫아도 이 창을 닫기 전까지 서버는 실행됩니다.")
    print("종료하려면 이 창에서 Ctrl+C를 누르거나 창을 닫으세요.\n")
    webbrowser.open(URL)

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nCrowdWay를 종료합니다.")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료했습니다.")
