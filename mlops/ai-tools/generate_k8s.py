import ollama

PROMPT = """
Generate production-ready Kubernetes manifests for a {app_type} application named '{name}'.
Output ONLY valid YAML, no explanation.
Include:
- Namespace
- Deployment with 2 replicas, resource limits (cpu/memory requests and limits)
- Service (ClusterIP)
- HorizontalPodAutoscaler (min 2, max 5, CPU 70%)
- Use image: {image}
- Port: {port}
"""

def generate_k8s(app_type: str, name: str, image: str, port: str) -> str:
    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": PROMPT.format(
                app_type=app_type, name=name, image=image, port=port
            ),
        }],
    )
    return response["message"]["content"]


if __name__ == "__main__":
    print("=== AI-Assisted K8s Manifest Generator ===\n")
    app_type = input("App type (e.g. FastAPI, Flask, Node.js): ")
    name     = input("App name (e.g. iris-model): ")
    image    = input("Container image (e.g. ghcr.io/org/app:latest): ")
    port     = input("Container port (e.g. 8000): ")
    print("\nGenerating manifests...\n")
    print(generate_k8s(app_type, name, image, port))
