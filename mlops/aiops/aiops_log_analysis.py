"""
Day 6 — AIOps: ML-based anomaly detection using Isolation Forest.
Converts logs into numeric features and flags statistical outliers.
Same approach as Veeramalla Day 6 but wired to our log format.
"""
import re
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest

import os as _os
LOG_FILE    = _os.path.join(_os.path.dirname(__file__), "system_logs.txt")
LOG_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+)\s+(.+)")

LEVEL_SCORE = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}


def parse_logs(path: str) -> pd.DataFrame:
    rows = []
    with open(path) as f:
        for line in f:
            m = LOG_PATTERN.match(line.strip())
            if m:
                rows.append({
                    "timestamp":     datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"),
                    "level":         m.group(2),
                    "message":       m.group(3),
                    "level_score":   LEVEL_SCORE.get(m.group(2), 1),
                    "message_len":   len(m.group(3)),
                })
    return pd.DataFrame(rows)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    features = df[["level_score", "message_len"]].values
    model = IsolationForest(contamination=0.1, random_state=42)
    df["anomaly"] = model.fit_predict(features)   # -1 = anomaly, 1 = normal
    return df


if __name__ == "__main__":
    df = parse_logs(LOG_FILE)
    print(f"Parsed {len(df)} log entries\n")

    df = detect_anomalies(df)
    anomalies = df[df["anomaly"] == -1]

    print(f"Isolation Forest detected {len(anomalies)} anomalies "
          f"({len(anomalies)/len(df)*100:.1f}% of logs):\n")

    for _, row in anomalies.iterrows():
        marker = "✅" if row["level"] == "INFO" else "❌"
        print(f"  {marker} [{row['timestamp']}] {row['level']:8s} {row['message']}")

    print(f"\nAnomaly breakdown by level:")
    print(anomalies["level"].value_counts().to_string())
