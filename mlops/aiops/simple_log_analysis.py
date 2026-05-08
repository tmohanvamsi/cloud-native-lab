"""
Day 6 — AIOps: Simple error spike detection.
Parses logs and alerts when ERROR/CRITICAL count exceeds threshold
in a rolling time window. No ML required — rule-based baseline.
"""
import re
from collections import defaultdict
from datetime import datetime

import os as _os
LOG_FILE   = _os.path.join(_os.path.dirname(__file__), "system_logs.txt")
WINDOW_SEC = 30
THRESHOLD  = 3   # errors per window that trigger an alert

LOG_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+)\s+(.+)")


def parse_logs(path: str) -> list[dict]:
    entries = []
    with open(path) as f:
        for line in f:
            m = LOG_PATTERN.match(line.strip())
            if m:
                entries.append({
                    "timestamp": datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"),
                    "level":     m.group(2),
                    "message":   m.group(3),
                })
    return entries


def detect_spikes(entries: list[dict]) -> list[dict]:
    """Count ERROR/CRITICAL per WINDOW_SEC-second bucket, flag if above threshold."""
    buckets: dict[datetime, list] = defaultdict(list)
    for e in entries:
        if e["level"] in ("ERROR", "CRITICAL"):
            bucket = e["timestamp"].replace(
                second=(e["timestamp"].second // WINDOW_SEC) * WINDOW_SEC,
                microsecond=0,
            )
            buckets[bucket].append(e)

    alerts = []
    for ts, errors in sorted(buckets.items()):
        if len(errors) >= THRESHOLD:
            alerts.append({
                "window_start": ts,
                "count":        len(errors),
                "samples":      [e["message"] for e in errors[:3]],
            })
    return alerts


if __name__ == "__main__":
    entries = parse_logs(LOG_FILE)
    print(f"Parsed {len(entries)} log entries\n")

    alerts = detect_spikes(entries)
    if not alerts:
        print("No error spikes detected.")
    else:
        print(f"⚠️  {len(alerts)} error spike(s) detected:\n")
        for a in alerts:
            print(f"  [{a['window_start']}] {a['count']} errors in {WINDOW_SEC}s window")
            for msg in a["samples"]:
                print(f"    → {msg}")
            print()
