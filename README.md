# Cloud Native Lab

A hands-on lab covering 11 Cloud Native Foundation certifications — running entirely locally at $0 cost.

## Certifications covered

| Cert | Tool | Lab |
| ---- | ---- | --- |
| LFCS | Linux (systemd, LVM, networking) | `make lab-lfcs` |
| CCA | Cilium (eBPF CNI, Hubble, L7 policies) | `make lab-cca` |
| CAPA | Argo (ArgoCD + Rollouts + Workflows) | `make lab-capa` |
| CGOA | GitOps (ArgoCD, reconciliation, drift) | `make lab-cgoa` |
| CBA | Backstage (catalog, templates, TechDocs) | `make lab-cba` |
| OTCA | OpenTelemetry (collector, traces, OTLP) | `make lab-otca` |
| PCA | Prometheus (PromQL, recording rules, alerts) | `make lab-pca` |
| ICA | Istio (VirtualService, fault injection, mTLS) | `make lab-ica` |
| KCA | Kyverno (validate, mutate, generate, verify) | `make lab-kca` |
| CNPE | Platform Engineering (IDP, cert-manager, golden paths) | `make lab-cnpe` |
| CNPA | Cloud Native Associate (CNCF landscape, containers) | `make lab-cnpa` |

## Stack

| Layer | Tools |
| ----- | ----- |
| Cluster | kind (Cilium CNI, no kube-proxy) |
| CNI | Cilium + Hubble |
| GitOps | ArgoCD + Argo Rollouts + Argo Workflows |
| Observability | Prometheus + Grafana + Loki + Tempo + Promtail |
| Tracing | OpenTelemetry Collector → Tempo |
| Service Mesh | Istio + Kiali |
| Policy | Kyverno |
| Developer Portal | Backstage (Docker) |
| Linux VM | Vagrant + Ubuntu 22.04 (LFCS) |
| MLOps | DVC + GitHub Actions + FastAPI model server |

## Prerequisites

- Docker Desktop (8GB RAM allocated)
- kind, kubectl, helm, istioctl, cilium CLI
- Vagrant + VirtualBox (for LFCS Linux lab only)

Install all tools:

```bash
make ansible-tools
```

## Daily Usage

```bash
make open     # start of day — restarts cluster + all port-forwards
make close    # end of day — stops port-forwards + saves cluster state
```

## Quick Start (first time)

```bash
make full-stack           # cluster + cilium + argo + monitoring + otel + istio + kyverno

# Or step by step
make cluster-create       # kind cluster with Cilium CNI
make cilium-install       # Cilium CNI + Hubble
make argo-install         # ArgoCD
make argo-rollouts        # Argo Rollouts
make argo-workflows       # Argo Workflows
make monitoring-install   # Prometheus + Grafana + Loki + Tempo
make otel-install         # OpenTelemetry Operator + Collector
make istio-install        # Istio + Kiali
make kyverno-install      # Kyverno
make kyverno-policies     # Apply all policies
make backstage-install    # Backstage (Docker)
make vagrant-up           # Linux VM for LFCS
```

## UIs

| Service | URL | Credentials |
| ------- | --- | ----------- |
| Grafana | <http://localhost:3000> | admin / see .env.local |
| ArgoCD | <http://localhost:8080> | admin / `make argo-password` |
| Argo Workflows | <https://localhost:2746> | none |
| Argo Rollouts | <http://localhost:3100> | none |
| Kiali | <http://localhost:20001> | anonymous |
| Hubble | <http://localhost:12000> | none |
| Backstage | <http://localhost:7007> | none |

## Learning Roadmap

| Day | Topics | Certs |
| --- | ------ | ----- |
| Day 1 ✅ | Cilium L7 policies, Hubble, Argo Rollouts canary, Argo Workflows DAG, Grafana + Loki | CCA, CAPA, PCA |
| Day 2 | PromQL recording/alerting rules, OTel collector, traces in Tempo | PCA, OTCA |
| Day 3 | Istio VirtualService, fault injection, circuit breaker, Kiali | ICA |
| Day 4 | Kyverno generate, mutate, verify-image, PolicyReport | KCA |
| Day 5 | Backstage catalog + templates, LFCS Linux VM, Platform Engineering | CBA, LFCS, CNPE, CNPA |
| Day 6 | MLOps: DVC pipeline, GitHub Actions CI/CD, model deploy to K8s | MLOps/AIOps |

## MLOps Pipeline (Day 6)

```bash
# Local run
pip install -r mlops/requirements.txt
dvc repro mlops/dvc.yaml          # prepare → train → evaluate
dvc metrics show                   # print accuracy

# GitHub Actions (automatic on push)
# mlops-train.yml  → trains model, posts metrics on PR
# mlops-deploy.yml → builds Docker image, pushes to GHCR, deploys to K8s

# GitHub secrets needed before Day 6
# KUBECONFIG = cat ~/.kube/config | base64
```

## Tear down

```bash
make clean
docker stop backstage && docker rm backstage
make vagrant-destroy
```

## Related

- [kubestronaut-lab](https://github.com/tmohanvamsi/kubestronaut-lab) — CKA, CKAD, CKS, KCNA, KCSA

Total cost: $0 — Setup time: 5 minutes with `make full-stack`
