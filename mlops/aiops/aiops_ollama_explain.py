"""
Day 6 Extension — AIOps + Ollama: Isolation Forest detects anomalies,
then Ollama (llama3) explains each one in plain English and suggests
a remediation step. This is the AI-assisted incident triage pattern.
"""
import re
import pandas as pd
import ollama
from datetime import datetime
from sklearn.ensemble import IsolationForest

import os as _os
LOG_FILE    = _os.path.join(_os.path.dirname(__file__), "system_logs.txt")
LOG_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+)\s+(.+)")
LEVEL_SCORE = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

EXPLAIN_PROMPT = """
You are an SRE analyzing production logs. A machine learning model flagged the following
log entry as anomalous. Explain in 2 sentences what likely went wrong and suggest
one concrete remediation step.

Log entry:
  Timestamp : {timestamp}
  Level     : {level}
  Message   : {message}

Response format:
  What happened: <explanation>
  Fix: <one action>
"""


def parse_logs(path: str) -> pd.DataFrame:
    rows = []
    with open(path) as f:
        for line in f:
            m = LOG_PATTERN.match(line.strip())
            if m:
                rows.append({
                    "timestamp":   datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"),
                    "level":       m.group(2),
                    "message":     m.group(3),
                    "level_score": LEVEL_SCORE.get(m.group(2), 1),
                    "message_len": len(m.group(3)),
                })
    return pd.DataFrame(rows)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    features = df[["level_score", "message_len"]].values
    model = IsolationForest(contamination=0.1, random_state=42)
    df = df.copy()
    df["anomaly"] = model.fit_predict(features)
    return df


def explain_with_ollama(row: pd.Series) -> str:
    prompt = EXPLAIN_PROMPT.format(
        timestamp=row["timestamp"],
        level=row["level"],
        message=row["message"],
    )
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


if __name__ == "__main__":
    df = parse_logs(LOG_FILE)
    df = detect_anomalies(df)

    # Focus on ERROR/CRITICAL anomalies only — skip INFO anomalies (unusual but low risk)
    critical_anomalies = df[(df["anomaly"] == -1) & (df["level"].isin(["ERROR", "CRITICAL"]))]
    print(f"Found {len(critical_anomalies)} critical anomalies. Calling Ollama for triage...\n")
    print("=" * 70)

    for _, row in critical_anomalies.iterrows():
        print(f"\n❌ [{row['timestamp']}] {row['level']} — {row['message']}")
        print("-" * 70)
        explanation = explain_with_ollama(row)
        print(explanation)
        print("=" * 70)
