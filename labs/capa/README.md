# CAPA — Certified Argo Project Associate

## Install
```bash
make argo-install           # ArgoCD
make argo-rollouts          # Argo Rollouts (canary/blue-green)
make argo-workflows         # Argo Workflows (DAG pipelines)
```

## Lab 1 — ArgoCD Core Commands
```bash
# Port-forward UI and get password
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo ""

# Login via CLI
argocd login localhost:8080 --username admin --insecure \
  --password $(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" | base64 -d)

# Create and deploy an app
argocd app create guestbook \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace apps \
  --sync-policy automated \
  --self-heal

# App lifecycle
argocd app list                        # list all apps
argocd app get guestbook               # detailed status
argocd app sync guestbook              # force sync now
argocd app wait guestbook --health     # wait until healthy
argocd app diff guestbook              # diff Git vs live state
argocd app history guestbook           # all previous deployments
argocd app rollback guestbook 1        # rollback to revision 1
argocd app delete guestbook            # delete app (keeps resources by default)
argocd app delete guestbook --cascade  # delete app AND all K8s resources

# Sync options
argocd app sync guestbook --force              # force replace resources
argocd app sync guestbook --prune             # delete resources not in Git
argocd app sync guestbook --dry-run           # preview what would change

# Cluster and repo management
argocd cluster list                    # registered clusters
argocd repo list                       # registered Git repos
argocd repo add https://github.com/YOUR_ORG/repo --username git --password TOKEN

# Check ArgoCD itself
argocd version                         # client + server version
argocd account list                    # users
argocd account update-password         # change admin password
```

## Lab 2 — Argo Rollouts (Canary)
```bash
kubectl create namespace apps --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f manifests/argo/rollouts/rollout-canary.yaml

# Watch canary progression live
kubectl argo rollouts get rollout demo-app -n apps --watch

# Trigger a canary (change image — steps: 20%→50%→80%→100%)
kubectl argo rollouts set image demo-app demo-app=argoproj/rollouts-demo:yellow -n apps
kubectl argo rollouts set image demo-app demo-app=argoproj/rollouts-demo:green -n apps

# Promote to next step manually (skip pause timer)
kubectl argo rollouts promote demo-app -n apps

# Abort mid-canary — snaps back to stable instantly
kubectl argo rollouts abort demo-app -n apps

# After abort, restore to Healthy (set image back to stable)
kubectl argo rollouts set image demo-app demo-app=argoproj/rollouts-demo:yellow -n apps

# Open Rollouts dashboard UI → http://localhost:3100
kubectl argo rollouts dashboard -n apps
```

## Lab 2b — ArgoCD Self-Heal
```bash
# Port-forward ArgoCD UI → https://localhost:8080
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Login
argocd login localhost:8080 --username admin --insecure \
  --password $(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" | base64 -d)

# Deploy guestbook with self-heal enabled
argocd app create guestbook \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace apps \
  --sync-policy automated \
  --self-heal
argocd app sync guestbook

# Prove self-heal — delete pod, ArgoCD recreates it automatically
kubectl delete pod -l app=guestbook-ui -n apps
kubectl get pods -n apps -l app=guestbook-ui --watch
# New pod appears within seconds — ArgoCD detected drift and reconciled
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
