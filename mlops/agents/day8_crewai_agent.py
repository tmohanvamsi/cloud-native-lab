"""
Day 8 — CrewAI DevOps Crew.
Two agents collaborate: an Analyst (reads logs + internal PDF docs)
and a Responder (produces an incident report + runbook).
Uses Ollama (llama3) as the LLM — zero paid API cost.

PDF support: drop any runbook/architecture PDF into mlops/docs/ and the
analyst will read it alongside the live log data for context-aware triage.

Usage:
  python mlops/agents/day8_crewai_agent.py
  python mlops/agents/day8_crewai_agent.py --pdf mlops/docs/runbook.pdf
"""
import argparse
import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, PDFSearchTool
from langchain_community.llms import Ollama

parser = argparse.ArgumentParser()
parser.add_argument("--pdf", default=None, help="Path to PDF documentation file")
args, _ = parser.parse_known_args()

# ── LLM (local Ollama — no API key needed) ───────────────────────────────────
llm = Ollama(model="llama3", base_url="http://localhost:11434")

# ── Tools ─────────────────────────────────────────────────────────────────────
log_reader = FileReadTool(file_path="mlops/aiops/system_logs.txt")

# PDF tool — attach only when a PDF path is supplied
analyst_tools = [log_reader]
if args.pdf and os.path.exists(args.pdf):
    pdf_tool = PDFSearchTool(pdf=args.pdf)
    analyst_tools.append(pdf_tool)
    print(f"PDF documentation loaded: {args.pdf}")

# ── Agents ────────────────────────────────────────────────────────────────────
analyst = Agent(
    role="SRE Log Analyst",
    goal=(
        "Read the system logs, identify all ERROR and CRITICAL events, "
        "group them by incident type, and determine root causes."
    ),
    backstory=(
        "You are a senior SRE at a cloud-native company. "
        "You have deep experience reading Kubernetes and application logs "
        "and quickly identifying patterns that indicate system failures. "
        "When PDF documentation is available, you cross-reference it to confirm "
        "known issues and follow established runbooks."
    ),
    tools=analyst_tools,
    llm=llm,
    verbose=True,
)

responder = Agent(
    role="Incident Responder",
    goal=(
        "Take the analyst's findings and produce a structured incident report "
        "with severity, timeline, root cause, and step-by-step remediation runbook."
    ),
    backstory=(
        "You are an on-call engineer who writes clear, actionable incident reports. "
        "Your runbooks are used by junior engineers to resolve issues at 3am."
    ),
    llm=llm,
    verbose=True,
)

# ── Tasks ─────────────────────────────────────────────────────────────────────
analyse_task = Task(
    description=(
        "Read the system log file and produce a structured analysis:\n"
        "1. List all unique incident types (database, memory, disk, security, etc.)\n"
        "2. For each incident: timestamp range, log entries involved, likely root cause\n"
        "3. Rate overall system health: GREEN / YELLOW / RED\n"
        "4. If PDF documentation was provided, cross-reference it: note any known issues "
        "   or runbook steps that apply to the detected incidents."
    ),
    expected_output=(
        "A structured incident analysis with incident types, timestamps, root causes, "
        "PDF cross-references (if applicable), and an overall health rating."
    ),
    agent=analyst,
)

respond_task = Task(
    description=(
        "Using the analyst's report, write a full incident response document:\n"
        "## Incident Summary\n"
        "## Timeline\n"
        "## Root Cause Analysis\n"
        "## Impact\n"
        "## Remediation Runbook (numbered steps)\n"
        "## Prevention (how to avoid this next time)"
    ),
    expected_output=(
        "A complete incident report in markdown format, ready to paste into "
        "a PagerDuty incident or Confluence page."
    ),
    agent=responder,
    context=[analyse_task],
)

# ── Crew ──────────────────────────────────────────────────────────────────────
crew = Crew(
    agents=[analyst, responder],
    tasks=[analyse_task, respond_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("🚀 Starting DevOps CrewAI incident analysis...\n")
    result = crew.kickoff()
    print("\n" + "="*70)
    print("📋 INCIDENT REPORT")
    print("="*70)
    print(result)

    with open("incident_report.md", "w") as f:
        f.write(str(result))
    print("\n✅ Report saved to incident_report.md")
