"""
Day 2 — Prompt Engineering with Ollama (llama3).
Demonstrates: zero-shot, one-shot, few-shot, chain-of-thought, role prompting.
Usage:  python mlops/ai-tools/prompt_engineering.py
"""
import ollama

CLIENT = ollama.Client(host="http://localhost:11434")
MODEL  = "llama3.2"


def ask(prompt: str, label: str) -> str:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"PROMPT:\n{prompt}\n")
    response = CLIENT.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response["message"]["content"]
    print(f"RESPONSE:\n{answer}")
    return answer


# ── 1. Zero-shot ──────────────────────────────────────────────────────────────
ask(
    "Classify the following log line as ERROR, WARNING, or INFO:\n"
    "Log: 'Connection to database timed out after 30s'",
    "1. Zero-Shot Prompting",
)

# ── 2. One-shot ───────────────────────────────────────────────────────────────
ask(
    "Classify log lines as ERROR, WARNING, or INFO.\n\n"
    "Example:\n"
    "Log: 'Disk usage at 95%' → WARNING\n\n"
    "Now classify:\n"
    "Log: 'Pod OOMKilled: container exceeded memory limit'",
    "2. One-Shot Prompting",
)

# ── 3. Few-shot ───────────────────────────────────────────────────────────────
ask(
    "Classify log lines as ERROR, WARNING, or INFO.\n\n"
    "Examples:\n"
    "Log: 'User login successful' → INFO\n"
    "Log: 'Retry attempt 3 of 5 for service mesh call' → WARNING\n"
    "Log: 'Segmentation fault in worker process PID 1042' → ERROR\n\n"
    "Now classify:\n"
    "Log: 'Certificate will expire in 7 days'",
    "3. Few-Shot Prompting",
)

# ── 4. Chain-of-thought ───────────────────────────────────────────────────────
ask(
    "A Kubernetes pod keeps restarting. Its logs show:\n"
    "  - 'OOMKilled' exit code\n"
    "  - Memory limit: 128Mi\n"
    "  - Peak RSS usage: 210Mi\n\n"
    "Think step-by-step: what is the root cause and what should I do to fix it?",
    "4. Chain-of-Thought Prompting",
)

# ── 5. Role prompting ─────────────────────────────────────────────────────────
ask(
    "You are a senior SRE with 10 years of Kubernetes experience.\n"
    "A junior engineer asks: 'Why does my Deployment show 0/3 pods ready '?\n"
    "Give a concise, actionable checklist they should follow to diagnose it.",
    "5. Role Prompting",
)

# ── 6. Structured-output prompt ───────────────────────────────────────────────
ask(
    "You are a JSON API. Respond ONLY with valid JSON, no markdown, no explanation.\n\n"
    "Parse this alert into structured JSON with keys: severity, service, message, action.\n"
    "Alert: 'CRITICAL — payment-service pod crash-looping, 5 restarts in 10 min'",
    "6. Structured-Output Prompting",
)

print("\n✅ All prompt engineering demos complete.")
