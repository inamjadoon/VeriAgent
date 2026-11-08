"""Run attack prompts through the agent and print REAL results (nothing hard-coded)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import agent  # noqa: E402
import llm  # noqa: E402

CSV = os.path.join(ROOT, "data", "glacier_lakes_sample.csv")

with open(os.path.join(ROOT, "eval", "attacks.json"), encoding="utf-8") as f:
    attacks = json.load(f)

print(f"LLM mode: {'MOCK' if llm.MOCK else llm.MODEL}\n")
rows = []
for a in attacks:
    r = agent.run_task(a["prompt"], CSV, timeout=10)
    contained = r["contained"] or r["status"] == "blocked"
    rows.append((a["name"], r["status"], "yes" if contained else "no", r["sandbox_mode"]))
    print(f"ran: {a['name']}")

print(f"\n{'attack':<20} | {'status':<8} | {'contained':<9} | sandbox")
print("-" * 70)
for name, status, cont, mode in rows:
    print(f"{name:<20} | {status:<8} | {cont:<9} | {mode}")
n = sum(1 for r in rows if r[2] == "yes")
print(f"\nTotal: {n}/{len(rows)} attacks contained")
