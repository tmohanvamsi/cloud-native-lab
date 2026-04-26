# CNPE — Certified Cloud Native Platform Engineer

## What this cert covers
Platform Engineering = building internal developer platforms (IDPs) so app teams can self-serve.
Tools: Backstage, Crossplane, ArgoCD, Tekton, Kyverno, OPA, cert-manager, external-secrets.

## Lab 1 — Platform Team vs App Team mental model
```
Platform Team owns:
  - Cluster provisioning (Terraform/Crossplane)
  - Namespace + RBAC templates (Kyverno generate)
  - Golden path templates (Backstage)
  - Observability stack (Prometheus/Grafana/Loki/Tempo)
  - Policy guardrails (Kyverno/OPA)

App Team consumes:
  - Deploys into pre-configured namespaces
  - Gets NetworkPolicy, ResourceQuota, LimitRange auto-generated
  - Uses golden path templates to scaffold new services
  - Sees their service in Backstage catalog automatically
```

## Lab 2 — Namespace-as-a-Service with Kyverno generate
```bash
# When platform team creates a namespace, Kyverno auto-generates:
# 1. NetworkPolicy deny-all
# 2. ResourceQuota
# 3. LimitRange
# Already set up in manifests/kyverno/generate-networkpolicy.yaml

kubectl create namespace team-alpha
kubectl get networkpolicy,resourcequota,limitrange -n team-alpha
```

## Lab 3 — cert-manager (automated TLS)
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true \
  --wait

# Self-signed issuer for local lab
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
EOF

# Issue a cert
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: my-app-tls
  namespace: apps
spec:
  secretName: my-app-tls
  issuerRef:
    name: selfsigned
    kind: ClusterIssuer
  dnsNames:
    - my-app.apps.svc.cluster.local
EOF
kubectl get certificate -n apps
kubectl get secret my-app-tls -n apps
```

## Lab 4 — Platform scorecard (check your platform health)
```bash
# How healthy is your platform?
kubectl get nodes                          # cluster healthy?
kubectl get pods -A | grep -v Running      # anything not Running?
kubectl get policyreport -A               # Kyverno violations?
kubectl top nodes                         # resource pressure?
cilium status                             # network healthy?
```

## Key Concepts
- Platform Engineering: reduce cognitive load on app teams via self-service
- Golden paths: opinionated templates that encode platform team best practices
- Paved roads: make the right thing the easy thing
- Internal Developer Portal (IDP): Backstage is the UI layer of the platform
- GitOps + Policy = guardrails with escape hatches
