"""
Day 6 — AIOps CrewAI Log Analysis Crew.
Three specialized agents collaborate to detect anomalies, triage incidents,
and produce a remediation playbook — all using Ollama (llama3), zero cost.

Agents:
  1. Log Scanner    — reads system_logs.txt, extracts ERROR/CRITICAL events
  2. AIOps Analyst  — correlates events, detects patterns & anomalies
  3. SRE Playbook Writer — produces a structured runbook with remediation steps

Usage:  python mlops/aiops/aiops_crewai.py
"""
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool
from langchain_community.llms import Ollama

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = Ollama(model="llama3", base_url="http://localhost:11434")

# ── Tools ─────────────────────────────────────────────────────────────────────
log_reader = FileReadTool(file_path="mlops/aiops/system_logs.txt")

# ── Agent 1: Log Scanner ───────────────────────────────────────────────────────
log_scanner = Agent(
    role="Log Scanner",
    goal=(
        "Read system_logs.txt in full. Extract every ERROR and CRITICAL log entry. "
        "Group entries by category: database, memory, disk, security, application. "
        "Return a clean numbered list with timestamp, level, and message for each."
    ),
    backstory=(
        "You are a log parsing specialist at a cloud-native SRE team. "
        "You have processed millions of log lines and instantly spot patterns "
        "that indicate system failures before they escalate."
    ),
    tools=[log_reader],
    llm=llm,
    verbose=True,
)

# ── Agent 2: AIOps Analyst ────────────────────────────────────────────────────
aiops_analyst = Agent(
    role="AIOps Analyst",
    goal=(
        "Take the structured log data from the Log Scanner and perform deep analysis:\n"
        "1. Detect error spikes (multiple errors in a short time window)\n"
        "2. Identify cascading failures (event A caused event B)\n"
        "3. Flag anomalies: unusual error rates, repeated failures, security threats\n"
        "4. Assign an overall system health score: GREEN / YELLOW / RED\n"
        "5. Rank incidents by severity and business impact"
    ),
    backstory=(
        "You are an AIOps practitioner who applies machine-learning thinking to "
        "log analysis — even without running code you reason about statistical anomalies, "
        "time-series spikes, and root-cause chains with surgical precision."
    ),
    llm=llm,
    verbose=True,
)

# ── Agent 3: SRE Playbook Writer ──────────────────────────────────────────────
playbook_writer = Agent(
    role="SRE Playbook Writer",
    goal=(
        "Convert the AIOps analyst's findings into a clear, actionable SRE playbook "
        "that an on-call engineer can follow at 3am to resolve each incident."
    ),
    backstory=(
        "You write SRE runbooks used by teams across the organisation. "
        "Your playbooks are famous for being concise, numbered, copy-paste-ready, "
        "and for including both immediate mitigation and long-term prevention."
    ),
    llm=llm,
    verbose=True,
)

# ── Tasks ─────────────────────────────────────────────────────────────────────
scan_task = Task(
    description=(
        "Read mlops/aiops/system_logs.txt completely.\n"
        "Extract ALL lines with level ERROR or CRITICAL.\n"
        "Output format — one entry per line:\n"
        "  [TIMESTAMP] [LEVEL] [CATEGORY] MESSAGE"
    ),
    expected_output=(
        "A categorised list of all ERROR/CRITICAL log entries with timestamps."
    ),
    agent=log_scanner,
)

analyse_task = Task(
    description=(
        "Using the log scanner's output, perform AIOps analysis:\n"
        "1. Error spike detection — flag any 3+ errors within a 30-second window\n"
        "2. Cascading failure chains — show if one failure triggered another\n"
        "3. Anomaly summary — what is unusual vs. expected noise?\n"
        "4. System health rating: GREEN / YELLOW / RED with justification\n"
        "5. Top-3 incidents ranked by severity (P1/P2/P3)"
    ),
    expected_output=(
        "AIOps analysis report: spike detection results, failure chains, "
        "anomaly summary, health rating, and ranked incident list."
    ),
    agent=aiops_analyst,
    context=[scan_task],
)

playbook_task = Task(
    description=(
        "Write a full SRE Incident Playbook in markdown. Include:\n\n"
        "## Executive Summary\n"
        "## Detected Incidents (table: ID | Severity | Category | Description)\n"
        "## Root Cause Analysis\n"
        "## Immediate Mitigation Steps (per incident — numbered, copy-paste CLI commands where possible)\n"
        "## Long-Term Prevention\n"
        "## Alerting Recommendations (what Prometheus rules or Loki alerts to add)"
    ),
    expected_output=(
        "A complete SRE playbook in markdown, ready to paste into a wiki or PagerDuty incident."
    ),
    agent=playbook_writer,
    context=[analyse_task],
)

# ── Crew ──────────────────────────────────────────────────────────────────────
crew = Crew(
    agents=[log_scanner, aiops_analyst, playbook_writer],
    tasks=[scan_task, analyse_task, playbook_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("AIOps CrewAI — Log Analysis & Incident Playbook\n" + "="*50)
    result = crew.kickoff()

    print("\n" + "="*70)
    print("SRE INCIDENT PLAYBOOK")
    print("="*70)
    print(result)

    output_path = "mlops/aiops/incident_playbook.md"
    with open(output_path, "w") as f:
        f.write(str(result))
    print(f"\nPlaybook saved to {output_path}")
