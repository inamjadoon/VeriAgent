"""Agent loop: LLM code -> policy scan -> sandbox -> retry on error (max 3) -> provenance."""
import csv
import os
import shutil
import uuid
from datetime import datetime, timezone

import llm
import policy
import provenance
import sandbox

MAX_ATTEMPTS = 3


def _peek_csv(path: str):
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))[:6]
    cols = rows[0] if rows else []
    return cols, "\n".join(",".join(r) for r in rows)


def run_task(question: str, csv_path: str, timeout: int = 30) -> dict:
    run_id = uuid.uuid4().hex[:12]
    steps = []

    def log(step, detail):
        steps.append({"step": step, "detail": detail,
                      "time": datetime.now(timezone.utc).isoformat(timespec="seconds")})

    out_dir = provenance.run_dir(run_id)
    shutil.copy(csv_path, os.path.join(out_dir, "input.csv"))
    columns, sample = _peek_csv(csv_path)
    log("load", f"Loaded CSV with columns {columns}")

    code, err, result = None, None, {}
    status, contained, attempts = "failed", False, 0
    mode = "subprocess (weaker isolation)" if not sandbox.docker_available() else "docker"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        attempts = attempt
        log("llm", f"Attempt {attempt}: asking LLM for code ({'MOCK mode' if llm.MOCK else llm.MODEL})"
            + (" with previous error" if err else ""))
        try:
            code = llm.generate_code(question, columns, sample, code, err)
        except Exception as e:
            log("llm_error", f"LLM call failed: {e}")
            break

        findings = policy.scan(code)
        if findings:
            log("policy", "Blocked by policy: " + "; ".join(findings))
            status, contained = "blocked", True
            result = {"stdout": "", "stderr": "Blocked by policy: " + "; ".join(findings), "output_files": []}
            break
        log("policy", "Policy scan passed")

        result = sandbox.run_code(code, csv_path, timeout=timeout)
        mode = result["mode"]
        log("sandbox", f"Ran in {mode}: " + ("success" if result["ok"] else "error"))
        if result["ok"]:
            status = "success"
            break
        if result.get("timed_out"):
            log("sandbox", result["stderr"])
            contained = True
            break
        err = result["stderr"]
        log("error", err.strip().splitlines()[-1] if err.strip() else "unknown error")

    # Copy outputs and hash everything.
    outputs = {}
    for name in result.get("output_files", []):
        src = os.path.join(result["workdir"], "output", name)
        dst = os.path.join(out_dir, name)
        shutil.copy(src, dst)
        outputs[name] = provenance.sha256_file(dst)
    if result.get("workdir"):
        shutil.rmtree(result["workdir"], ignore_errors=True)

    hashes = {"input": {os.path.basename(csv_path): provenance.sha256_file(csv_path)},
              "outputs": outputs,
              "code": provenance.sha256_text(code or "")}
    log("provenance", f"Hashed input + {len(outputs)} output file(s); saved record.json")

    record = {
        "id": run_id, "question": question, "status": status, "contained": contained,
        "sandbox_mode": mode, "llm_mode": "mock" if llm.MOCK else llm.MODEL, "attempts": attempts,
        "code": code or "", "stdout": result.get("stdout", ""), "stderr": result.get("stderr", ""),
        "steps": steps, "output_files": list(outputs), "hashes": hashes,
    }
    provenance.save_record(record)
    return record
