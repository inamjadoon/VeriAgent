# VeriAgent: Product Requirements (1 page)

## Problem
People with important data (disaster officers tracking glacial lakes, analysts, small business owners) often can't write code. AI chatbots can "answer" data questions, but the answers may be made up, the code they run can't be checked, and running AI-written code on your own machine is risky.

## Target users
- **Disaster risk officers** (e.g. GLOF monitoring in Gilgit-Baltistan, Pakistan): need quick, trustworthy trend analysis of lake growth.
- **Analysts**: want fast exploratory answers with code they can review.
- **Small businesses**: want sales and inventory insights without hiring a data scientist.

## Solution
Upload a CSV and ask a question in plain English. VeriAgent has an LLM write pandas code, checks it against a safety policy, runs it in an isolated sandbox, fixes errors automatically, and returns the real output with the exact code, a step log, and SHA-256 hashes as proof.

## Core features
1. CSV upload + plain-English question.
2. LLM code generation (OpenAI-compatible API; MOCK mode with no key).
3. Policy scan that blocks risky code (network, shell, file deletion, secrets).
4. Sandbox execution (Docker with no network; restricted subprocess fallback).
5. Auto-retry on errors (max 3 attempts).
6. Provenance: SHA-256 of input and outputs, saved as a JSON record.
7. Safety evaluation script with 5 attack prompts.

## Out of scope
User accounts, databases, multi-file datasets, streaming, production deployment, and claims of formal security guarantees.

## Success criteria
- A sample question returns a real chart + text output in under 30 seconds.
- All 5 eval attacks are blocked or contained (results come from actually running the eval).
- Every run produces a `record.json` with matching hashes.
