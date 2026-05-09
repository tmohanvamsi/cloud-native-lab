"""
Day 4 — AI-powered AWS VPC shell-script generator.
Asks Ollama (llama3) to produce an AWS CLI script that creates a VPC
with public/private subnets, an internet gateway, route tables, and NAT gateway.
Usage:  python mlops/ai-tools/generate_vpc.py [--env dev|staging|prod]
"""
import argparse
import ollama

CLIENT = ollama.Client(host="http://localhost:11434")
MODEL  = "llama3.2"


def generate_vpc_script(env: str, cidr: str, region: str) -> str:
    prompt = f"""You are an AWS infrastructure expert.
Generate a complete, production-ready bash script using the AWS CLI that creates
a VPC for a {env} environment with the following spec:

- Region: {region}
- VPC CIDR: {cidr}
- 2 public subnets  (first two /24 blocks, e.g. .0/24 and .1/24)
- 2 private subnets (next two /24 blocks, e.g. .2/24 and .3/24)
- Internet Gateway attached to the VPC
- Public route table: 0.0.0.0/0 → IGW
- 1 NAT Gateway in the first public subnet with an Elastic IP
- Private route table: 0.0.0.0/0 → NAT Gateway
- All resources tagged: Env={env}, ManagedBy=ai-generated

Requirements:
- Use `set -euo pipefail`
- Use variables for REGION, VPC_CIDR, ENV at the top
- Echo progress messages as each resource is created
- At the end, print a summary table of all created resource IDs
- Add a cleanup function that tears down everything (call it with --cleanup arg)

Output ONLY the bash script, no explanations, no markdown fences."""

    response = CLIENT.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description="AI-generated AWS VPC script")
    parser.add_argument("--env",    default="dev",            choices=["dev", "staging", "prod"])
    parser.add_argument("--cidr",   default="10.0.0.0/16")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--output", default="vpc_setup.sh")
    args = parser.parse_args()

    print(f"Generating VPC script for env={args.env}, cidr={args.cidr}, region={args.region}...")
    script = generate_vpc_script(args.env, args.cidr, args.region)

    # strip accidental markdown fences if the model adds them
    lines = script.strip().splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    clean_script = "\n".join(lines)

    with open(args.output, "w") as f:
        f.write(clean_script + "\n")

    print(f"\n{'='*60}")
    print(f"  Generated VPC script saved to: {args.output}")
    print(f"{'='*60}")
    print(clean_script[:1200] + ("\n... (truncated)" if len(clean_script) > 1200 else ""))
    print(f"\nRun with:  bash {args.output}")
    print("Dry-run:   bash -n {args.output}  (syntax check only)")


if __name__ == "__main__":
    main()
