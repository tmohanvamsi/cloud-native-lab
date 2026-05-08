import ollama

PROMPT = """
Generate an ideal Dockerfile for {language} with best practices.
Output ONLY the Dockerfile, no explanation.
Include:
- Minimal base image
- Non-root user
- Installing dependencies
- Setting working directory
- Adding source code
- Running the application
"""

def generate_dockerfile(language: str) -> str:
    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": PROMPT.format(language=language)}],
    )
    return response["message"]["content"]


if __name__ == "__main__":
    language = input("Enter the programming language/framework: ")
    print("\nGenerating Dockerfile...\n")
    print(generate_dockerfile(language))
