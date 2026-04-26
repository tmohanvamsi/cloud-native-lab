# CGOA — Certified GitOps Associate

## Core GitOps Principles (must know for exam)
1. **Declarative** — desired state stored as files, not scripts
2. **Versioned** — Git is the single source of truth
3. **Pulled automatically** — agent pulls from Git (not push from CI)
4. **Continuously reconciled** — agent detects and fixes drift

## Lab 1 — Prove GitOps self-healing
```bash
make argo-ui
# In ArgoCD UI — delete a pod from a synced app
kubectl delete pod -l app=guestbook -n apps
# Watch ArgoCD recreate it automatically (self-heal)
kubectl get pods -n apps -w
```

## Lab 2 — Simulate drift
```bash
# Manually change a replica count
kubectl scale deployment guestbook-ui --replicas=5 -n apps
# ArgoCD detects OutOfSync within 3 minutes and reverts to 1
# Watch: ArgoCD UI → app → status changes to OutOfSync → auto-syncs back
```

## Lab 3 — Git-driven deployment
```bash
# Change something in your repo, commit and push
# ArgoCD polls every 3 minutes OR you can force a sync:
argocd app sync guestbook
argocd app wait guestbook --health
```

## Lab 4 — Multi-env with App-of-Apps
```bash
# App-of-Apps pattern:
# Root App → watches manifests/apps/ directory
# Each file in manifests/apps/ is itself an ArgoCD Application
# Staging and prod are separate ArgoCD Applications pointing to different paths/branches

cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: staging
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/cloud-native-lab
    targetRevision: HEAD
    path: manifests/apps/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

## Key Concepts
- Pull vs Push: GitOps = pull (agent in cluster). Traditional CI/CD = push (pipeline runs kubectl)
- Reconciliation loop: ArgoCD compares live state vs desired state every 3 min
- Prune: ArgoCD deletes resources that exist in cluster but not in Git
- SyncOptions: CreateNamespace=true, ServerSideApply=true
- Flux is the other major GitOps tool (CGOA covers both concepts)
