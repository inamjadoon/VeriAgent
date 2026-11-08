# VeriAgent: Technical Spec

## Architecture
```
Browser (static/index.html)
   │  POST /api/run (CSV + question)
   ▼
app.py (FastAPI) ──► agent.py (loop)
                       ├─► llm.py        (OpenAI-compatible API or MOCK)
                       ├─► policy.py     (regex scan, blocks risky code)
                       ├─► sandbox.py    (Docker --network none, or subprocess fallback)
                       └─► provenance.py (SHA-256 + runs/<id>/record.json)
```

## Components
| File | Job |
|---|---|
| `app.py` | FastAPI: `GET /`, `POST /api/run`, `GET /api/runs/{id}`, static `/runs/...` |
| `agent.py` | `run_task(question, csv_path)`: the agent loop |
| `llm.py` | Builds the prompt, calls the LLM, extracts the code block. MOCK mode if `LLM_API_KEY` is empty |
| `policy.py` | `scan(code) -> list[str]` of findings |
| `sandbox.py` | `run_code(code, data_path, timeout) -> {ok, stdout, stderr, output_files, mode, workdir}` |
| `provenance.py` | `sha256_file`, `save_record` |
| `eval/run_eval.py` | Runs `eval/attacks.json` through the agent and prints real results |

## Agent loop
1. Read CSV columns + 5 sample rows.
2. Ask the LLM for code (attempt 1).
3. Policy scan. If there are findings, set status `blocked`, `contained=True`, and stop (the code never runs).
4. Run in the sandbox. On a timeout, stop with `contained=True` (no retry).
5. On error, send the stderr back to the LLM and retry, up to 3 attempts total.
6. Copy outputs to `runs/<id>/`, hash everything, save `record.json`.

## Sandbox rules
- **Docker** (if `docker info` works and the `veriagent-sandbox` image exists or can be built from `sandbox/Dockerfile`):
  `--network none --memory 512m --cpus 1 --pids-limit 64 --read-only --tmpfs /tmp --user 1000:1000 -v <workdir>:/work -w /work`
- **Subprocess fallback** (weaker isolation): fresh temp dir, empty environment (only `PATH`, `MPLBACKEND=Agg`, plus `SYSTEMROOT` on Windows, which Python needs to start), and a timeout.
- API keys and other env vars are never passed into the sandbox.

## Policy rules (regex)
`requests`, `urllib`, `socket`, `http.client`, `subprocess`, `os.system`, `os.popen`, `shutil.rmtree`, `eval(`, `exec(`, `open('/etc`, `os.environ`, `__import__`.

## Provenance record (`runs/<id>/record.json`)
```json
{
  "id": "a1b2c3d4e5f6",
  "question": "...",
  "status": "success | failed | blocked",
  "contained": false,
  "sandbox_mode": "docker | subprocess (weaker isolation)",
  "attempts": 1,
  "code": "...",
  "stdout": "...",
  "stderr": "...",
  "steps": [{"step": "llm", "detail": "...", "time": "ISO-8601"}],
  "output_files": ["chart.png"],
  "hashes": {"input": {"data.csv": "<sha256>"}, "outputs": {"chart.png": "<sha256>"}, "code": "<sha256>"}
}
```

## API
- `GET /`: UI
- `POST /api/run`: multipart `file` (optional CSV) + `question`; returns the record JSON
- `GET /api/runs/{id}`: returns the saved record
- `GET /runs/{id}/{file}`: output files (charts)

## Vultr migration path (not done yet)
1. Set `LLM_BASE_URL` to the Vultr Serverless Inference OpenAI-compatible endpoint, `LLM_API_KEY` to the Vultr key, and `LLM_MODEL` to a hosted model.
2. Provision a Vultr Cloud Compute instance, install Docker, build `sandbox/Dockerfile`, and run `uvicorn app:app --host 0.0.0.0` behind a reverse proxy.
No code changes are needed; it is configuration only.
