"""Run untrusted code: Docker (no network, limits) if available, else a restricted subprocess."""
import os
import shutil
import subprocess
import sys
import tempfile

IMAGE = "veriagent-sandbox"
HERE = os.path.dirname(os.path.abspath(__file__))
_docker_ok = None


def docker_available() -> bool:
    global _docker_ok
    if _docker_ok is not None:
        return _docker_ok
    _docker_ok = False
    if not shutil.which("docker"):
        return False
    try:
        if subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode != 0:
            return False
        if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode != 0:
            build = subprocess.run(["docker", "build", "-t", IMAGE, os.path.join(HERE, "sandbox")],
                                   capture_output=True, timeout=600)
            if build.returncode != 0:
                return False
        _docker_ok = True
    except Exception:
        pass
    return _docker_ok


def run_code(code: str, data_path: str, timeout: int = 30) -> dict:
    work = tempfile.mkdtemp(prefix="veriagent_")
    out_dir = os.path.join(work, "output")
    os.makedirs(out_dir)
    with open(os.path.join(work, "script.py"), "w", encoding="utf-8") as f:
        f.write(code)
    shutil.copy(data_path, os.path.join(work, "data.csv"))

    if docker_available():
        os.chmod(out_dir, 0o777)
        mode = "docker"
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--tmpfs", "/tmp", "--user", "1000:1000",
               "-e", "MPLBACKEND=Agg", "-e", "MPLCONFIGDIR=/tmp",
               "-v", f"{work}:/work", "-w", "/work", IMAGE, "python", "script.py"]
        env = None  # docker CLI itself; nothing from here is passed into the container
    else:
        mode = "subprocess (weaker isolation)"
        cmd = [sys.executable, "-I", "script.py"]
        tmp = os.path.join(work, "tmp")
        os.makedirs(tmp)
        # EMPTY environment: no API keys or other secrets leak into the sandbox.
        env = {"PATH": os.path.dirname(sys.executable), "MPLBACKEND": "Agg",
               "MPLCONFIGDIR": tmp, "TEMP": tmp, "TMP": tmp, "HOME": tmp}
        if os.name == "nt":
            env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")  # needed for Python to start

    try:
        p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout)
        ok, stdout, stderr = p.returncode == 0, p.stdout, p.stderr
        timed_out = False
    except subprocess.TimeoutExpired as e:
        ok, timed_out = False, True
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = f"Timed out: blocked by sandbox limit ({timeout}s)"

    files = sorted(os.listdir(out_dir))
    return {"ok": ok, "stdout": stdout, "stderr": stderr, "output_files": files,
            "mode": mode, "workdir": work, "timed_out": timed_out}
