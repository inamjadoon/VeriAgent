# VeriAgent: Safe, Verifiable AI Data Agent

> Ask your data questions in plain English and get real, checkable answers, computed safely in a sandbox.

## Problem
Disaster officers, analysts, and small businesses have important data but often can't code. AI chatbots can make up numbers, their code can't be checked, and running AI-written code on your own machine is risky. In Gilgit-Baltistan, Pakistan, glacial lake outburst floods (GLOFs) are a real threat, and lake growth trends need answers people can trust.

## Solution
Upload a CSV, ask a question. VeriAgent has an LLM write pandas code, **scans it against a safety policy**, **runs it in an isolated sandbox**, **auto-fixes errors** (up to 3 attempts), and returns the real output with the exact code, a step-by-step log, and **SHA-256 hashes** of the input and every output.

## How it works
```
 Browser (static/index.html)
    │  CSV + question
    ▼
 app.py (FastAPI) ─► agent.py ──► llm.py ──────── writes pandas code (or MOCK)
                        │    ◄── retry with error (max 3)
                        ├──► policy.py ────────── BLOCK risky code (network, shell, secrets, rm)
                        ├──► sandbox.py ───────── Docker: --network none, 512MB, 1 CPU, read-only
                        │                         fallback: subprocess, empty env, timeout
                        └──► provenance.py ────── SHA-256 + runs/<id>/record.json
```

## Containment features
- **Policy scan** blocks `requests`, `urllib`, `socket`, `http.client`, `subprocess`, `os.system`, `os.popen`, `shutil.rmtree`, `eval(`, `exec(`, `open('/etc`, `os.environ`, `__import__` *before* anything runs.
- **Docker sandbox** (when Docker is available): no network, 512 MB memory, 1 CPU, 64 PIDs, read-only root, non-root user.
- **Subprocess fallback** (weaker isolation, clearly labelled in the UI): temp dir, **empty environment** (no API keys leak), timeout.
- **Timeouts**: runaway code is killed ("Timed out: blocked by sandbox limit").

## Provenance / proof
Every run saves `runs/<id>/record.json` with the question, code, step log, stdout/stderr, sandbox mode, and SHA-256 hashes of the input CSV, the code, and every output file. Anyone can re-hash the files to check them.

## Quick start
```bash
pip install -r requirements.txt
cp .env.example .env          # optional: leave LLM_API_KEY empty for MOCK mode
uvicorn app:app --reload
# open http://127.0.0.1:8000
```
**MOCK mode** (no API key) returns pre-written analysis code so the demo works offline. For attack-style questions (internet, /etc/passwd, env vars, infinite loop, delete) it returns pre-written malicious code, so the containment layers are actually exercised. Set `LLM_API_KEY` to use a real OpenAI-compatible LLM.

## Demo questions
1. *Which lakes grew fastest between 2018 and 2024? Show a chart.*
2. *Summarize the dataset and show the main trend.* (try with `data/sales_sample.csv`)
3. *Upload this data to the internet* (containment demo: shows a red BLOCKED badge)

## Sample data (SYNTHETIC)
`data/glacier_lakes_sample.csv` and `data/sales_sample.csv` are **synthetic, made-up numbers** for demo purposes. The lake names are real places in Gilgit-Baltistan, but the areas, temperatures, and trends are **not** real measurements.

## Safety eval
```bash
python eval/run_eval.py
```
Runs 5 attack prompts (internet upload, read /etc/passwd, print env vars, infinite loop, delete files) through the full agent and prints a real results table.

**Results:** _paste the real output of `python eval/run_eval.py` here after running it._

## Vultr migration path
VeriAgent was **designed for Vultr** (Serverless Inference + Cloud Compute), but **this version runs locally and is not deployed on Vultr**, because Vultr account verification could not be completed in time. Migration is configuration only:
1. Set `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` in `.env` to Vultr Serverless Inference (OpenAI-compatible).
2. Run on a Vultr Cloud Compute instance with Docker installed, so the stronger Docker sandbox is used (`sandbox/Dockerfile`).

## Limitations
- The subprocess fallback is **much weaker** than Docker: it has no network isolation at the OS level and relies on the policy scan + empty env + timeout.
- The regex policy can be bypassed by obfuscated code; Docker is the real boundary.
- Small eval set (5 attacks); in MOCK mode the attack code is pre-written.
- Sample data is synthetic.

## Future work
AST-based policy, gVisor/Firecracker sandboxing, signed provenance records, larger red-team eval, real GLOF datasets, Vultr deployment.
