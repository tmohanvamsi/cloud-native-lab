"""
Day 7 — Simple AI Agent from scratch (no framework).
Pattern: LLM decides which tool to call → tool runs → result fed back to LLM.
Tools: check_disk, check_memory, list_pods, run_kubectl.
This is the core agent loop every framework (LangChain, CrewAI) builds on top of.
"""
import json
import subprocess
import shutil
import ollama

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = {
    "check_disk": {
        "description": "Check disk usage on the system. Returns used/available space.",
        "func": lambda _: subprocess.getoutput("df -h / | tail -1"),
    },
    "check_memory": {
        "description": "Check current memory usage. Returns free/used memory.",
        "func": lambda _: subprocess.getoutput("free -h | grep Mem"),
    },
    "list_pods": {
        "description": "List all Kubernetes pods across all namespaces.",
        "func": lambda _: (
            subprocess.getoutput("kubectl get pods -A --no-headers 2>&1")
            if shutil.which("kubectl") else "kubectl not available in this environment"
        ),
    },
    "check_logs": {
        "description": "Check recent system/application logs for errors.",
        "func": lambda args: subprocess.getoutput(
            f"grep -i 'error\\|critical' mlops/aiops/system_logs.txt | tail -10"
        ),
    },
}

SYSTEM_PROMPT = """You are a DevOps AI agent. You help diagnose and fix infrastructure issues.
You have access to these tools:
{tool_list}

When the user asks a question:
1. Decide if you need a tool. If yes, respond ONLY with JSON: {{"tool": "<name>", "reason": "<why>"}}
2. If no tool needed, answer directly in plain text.
3. After seeing tool output, give a final plain-text answer with your assessment.

Be concise. One tool call at a time."""


def get_tool_list() -> str:
    return "\n".join(f"  - {name}: {meta['description']}" for name, meta in TOOLS.items())


def call_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    return TOOLS[name]["func"](args)


def agent_loop(user_query: str) -> None:
    print(f"\n{'='*60}")
    print(f"User: {user_query}")
    print(f"{'='*60}\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(tool_list=get_tool_list())},
        {"role": "user",   "content": user_query},
    ]

    for step in range(5):  # max 5 iterations to prevent infinite loops
        response = ollama.chat(model="llama3", messages=messages)
        content  = response["message"]["content"].strip()

        # Try to parse as tool call
        try:
            parsed = json.loads(content)
            if "tool" in parsed:
                tool_name = parsed["tool"]
                print(f"🔧 Agent calling tool: {tool_name}")
                print(f"   Reason: {parsed.get('reason', '')}")

                tool_output = call_tool(tool_name, parsed.get("args", {}))
                print(f"\n📊 Tool output:\n{tool_output}\n")

                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user",      "content": f"Tool output:\n{tool_output}\nNow give your final answer."})
                continue
        except (json.JSONDecodeError, KeyError):
            pass

        # Plain text response — agent is done
        print(f"🤖 Agent: {content}\n")
        break


if __name__ == "__main__":
    print("DevOps AI Agent (type 'quit' to exit)\n")
    print("Example questions:")
    print("  - Is my disk running low?")
    print("  - Are there any errors in the logs?")
    print("  - What's the memory situation?\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if query:
            agent_loop(query)
