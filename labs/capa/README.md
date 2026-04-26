# CAPA — Certified Argo Project Associate

## Install
```bash
make argo-install           # ArgoCD
make argo-rollouts          # Argo Rollouts (canary/blue-green)
make argo-workflows         # Argo Workflows (DAG pipelines)
```

## Lab 1 — ArgoCD App of Apps
```bash
make argo-ui                # → http://localhost:8080
make argo-password
argocd login localhost:8080 --username admin --insecure \
  --password $(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" | base64 -d)

# Deploy an app
argocd app create guestbook \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace apps \
  --sync-policy automated \
  --self-heal

argocd app sync guestbook
argocd app get guestbook
```

## Lab 2 — Argo Rollouts (Canary)
```bash
kubectl create namespace apps --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f manifests/argo/rollouts/rollout-canary.yaml

# Watch canary progression
kubectl argo rollouts get rollout demo-app -n apps --watch

# Promote to next step manually
kubectl argo rollouts promote demo-app -n apps

# Update image — triggers new canary
kubectl argo rollouts set image demo-app demo-app=argoproj/rollouts-demo:yellow -n apps

# Abort if something goes wrong
kubectl argo rollouts abort demo-app -n apps
```

## Lab 3 — Argo Workflows (DAG Pipeline)
```bash
kubectl apply -f manifests/argo/workflows/hello-world.yaml
kubectl get workflows -n argo
kubectl logs -n argo -l workflows.argoproj.io/workflow --tail=50

# Submit from CLI
argo submit manifests/argo/workflows/hello-world.yaml -n argo --watch
argo list -n argo
argo get @latest -n argo
```

## Key Concepts
- ArgoCD — pull-based GitOps, cluster polls repo, not push
- Argo Rollouts — replaces Deployment for progressive delivery (canary, blue-green)
- Argo Workflows — Kubernetes-native DAG pipeline engine (like Airflow but in K8s)
- Argo Events — event-driven triggers (webhook → workflow) — Phase 2
- App-of-Apps — ArgoCD managing ArgoCD Applications (meta GitOps)
