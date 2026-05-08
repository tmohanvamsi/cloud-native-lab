#!/usr/bin/env bash
# Day 1 — VM health check with optional AI-powered --explain flag.
# Usage:
#   ./vm_health.sh            → shows raw health metrics
#   ./vm_health.sh --explain  → sends metrics to Ollama for plain-English summary

set -euo pipefail

# ── Collect metrics ───────────────────────────────────────────────────────────
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 2>/dev/null \
  || top -bn1 | awk '/Cpu/ {print 100 - $8}' 2>/dev/null \
  || echo "N/A")

MEM_TOTAL=$(free -m | awk '/Mem:/ {print $2}')
MEM_USED=$(free -m  | awk '/Mem:/ {print $3}')
MEM_PCT=$(awk "BEGIN {printf \"%.1f\", ($MEM_USED/$MEM_TOTAL)*100}")

DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')

LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | xargs)
UPTIME=$(uptime -p 2>/dev/null || uptime | awk -F'up ' '{print $2}' | cut -d',' -f1)

# ── Determine health status ───────────────────────────────────────────────────
STATUS="HEALTHY"
ISSUES=()

CPU_INT=${CPU_USAGE%.*}
[[ "$CPU_INT" =~ ^[0-9]+$ ]] && (( CPU_INT > 85 )) && { STATUS="WARNING"; ISSUES+=("High CPU: ${CPU_USAGE}%"); }

MEM_INT=${MEM_PCT%.*}
[[ "$MEM_INT" =~ ^[0-9]+$ ]] && (( MEM_INT > 85 )) && { STATUS="WARNING"; ISSUES+=("High Memory: ${MEM_PCT}%"); }

DISK_INT=${DISK_USAGE%%%}
[[ "$DISK_INT" =~ ^[0-9]+$ ]] && (( DISK_INT > 85 )) && { STATUS="CRITICAL"; ISSUES+=("Disk full: ${DISK_USAGE}"); }

# ── Print report ──────────────────────────────────────────────────────────────
echo "============================================"
echo "  VM Health Check Report"
echo "  $(date)"
echo "============================================"
printf "  %-18s %s\n" "Status:"    "$STATUS"
printf "  %-18s %s\n" "CPU Usage:" "${CPU_USAGE}%"
printf "  %-18s %s / %s MB (${MEM_PCT}%%)\n" "Memory:" "$MEM_USED" "$MEM_TOTAL"
printf "  %-18s %s used, %s available\n" "Disk (/):" "$DISK_USAGE" "$DISK_AVAIL"
printf "  %-18s %s\n" "Load Average:" "$LOAD_AVG"
printf "  %-18s %s\n" "Uptime:" "$UPTIME"

if [[ ${#ISSUES[@]} -gt 0 ]]; then
  echo ""
  echo "  ⚠️  Issues:"
  for issue in "${ISSUES[@]}"; do
    echo "     - $issue"
  done
fi
echo "============================================"

# ── AI Explain mode ───────────────────────────────────────────────────────────
if [[ "${1:-}" == "--explain" ]]; then
  command -v curl >/dev/null 2>&1 || { echo "curl not found — cannot call Ollama"; exit 1; }

  METRICS_SUMMARY="VM Health Report:
- Status: $STATUS
- CPU Usage: ${CPU_USAGE}%
- Memory: ${MEM_USED}MB used of ${MEM_TOTAL}MB (${MEM_PCT}%)
- Disk: ${DISK_USAGE} used, ${DISK_AVAIL} available
- Load Average: $LOAD_AVG
- Uptime: $UPTIME
- Issues: ${ISSUES[*]:-none}"

  PROMPT="You are a DevOps engineer. Analyse this VM health report and provide:
1. A plain-English summary of the VM's current health
2. Whether any metrics are concerning and why
3. Recommended actions if any issues exist

$METRICS_SUMMARY"

  echo ""
  echo "🤖 AI Explanation (via Ollama llama3):"
  echo "--------------------------------------------"

  curl -sf http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"llama3\", \"prompt\": $(echo "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'), \"stream\": false}" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['response'])"

  echo "--------------------------------------------"
fi
