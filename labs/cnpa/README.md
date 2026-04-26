# CNPA — Certified Cloud Native Platform Engineering Associate

## What this cert covers
Associate-level: Cloud Native concepts, CNCF landscape, containers, K8s basics,
service mesh basics, observability concepts, GitOps concepts.

## Lab 1 — CNCF Landscape categories (know these)
```
Provisioning:    Terraform, Crossplane, Ansible, Pulumi
Runtime:         containerd, CRI-O, gVisor
Orchestration:   Kubernetes, Nomad
Network:         Cilium, Calico, Flannel, Istio, Linkerd
Storage:         Rook-Ceph, Longhorn, MinIO
Observability:   Prometheus, Grafana, Jaeger, OpenTelemetry, Loki
GitOps:          ArgoCD, Flux
Security:        Falco, OPA/Gatekeeper, Kyverno, cert-manager
```

## Lab 2 — Container fundamentals
```bash
# Image layers
docker history nginx:latest

# Build and inspect
cat <<EOF > /tmp/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
EOF
docker build -t my-app:v1 /tmp/
docker inspect my-app:v1 | jq '.[0].Config'

# Container runtime
crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps
```

## Lab 3 — Kubernetes core objects
```bash
# Deployment → ReplicaSet → Pod chain
kubectl create deployment demo --image=nginx --replicas=3 -n apps
kubectl get deployment,replicaset,pod -n apps -l app=demo

# Service types
kubectl expose deployment demo --port=80 --type=ClusterIP -n apps
kubectl expose deployment demo --port=80 --type=NodePort -n apps
kubectl expose deployment demo --port=80 --type=LoadBalancer -n apps

# ConfigMap and Secret
kubectl create configmap app-config --from-literal=ENV=production -n apps
kubectl create secret generic app-secret --from-literal=API_KEY=test123 -n apps
kubectl get cm,secret -n apps
```

## Lab 4 — Health and readiness
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: health-demo
  namespace: apps
spec:
  containers:
    - name: app
      image: nginx
      readinessProbe:
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 10
      livenessProbe:
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 15
        periodSeconds: 20
      resources:
        requests:
          cpu: 50m
          memory: 64Mi
        limits:
          cpu: 100m
          memory: 128Mi
EOF
kubectl describe pod health-demo -n apps | grep -A5 "Conditions"
```

## Key Concepts
- Cloud Native = containers + dynamic orchestration + microservices + DevOps culture
- 12-Factor App principles: config in env, stateless, disposable, dev/prod parity
- Liveness vs Readiness: liveness restarts pod, readiness removes from service endpoints
- Horizontal vs Vertical scaling: HPA adds pods, VPA resizes pod resources
- Immutable infrastructure: never patch in place, always replace
