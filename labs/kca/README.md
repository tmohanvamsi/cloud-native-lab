# KCA — Kyverno Certified Associate

## Install
```bash
make kyverno-install
make kyverno-policies
```

## Lab 1 — Validate Policy (block non-conforming pods)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-limits
      match:
        any:
          - resources:
              kinds: [Pod]
      validate:
        message: "CPU and memory limits are required."
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    cpu: "?*"
                    memory: "?*"
EOF

# This pod will be blocked
kubectl run bad-pod --image=nginx -n apps
# Error: resource validation failed: CPU and memory limits are required.
```

## Lab 2 — Mutate Policy (auto-add labels)
```bash
kubectl apply -f manifests/kyverno/mutate-labels.yaml

kubectl run test-pod --image=nginx -n apps \
  --requests='cpu=50m,memory=64Mi' --limits='cpu=100m,memory=128Mi'
kubectl get pod test-pod -n apps --show-labels
# Should show: managed-by=kyverno,env=apps automatically added
```

## Lab 3 — Generate Policy (auto-create NetworkPolicy for every namespace)
```bash
kubectl apply -f manifests/kyverno/generate-networkpolicy.yaml

# Create a new namespace — NetworkPolicy auto-generated
kubectl create namespace generated-test
kubectl get networkpolicy -n generated-test
# NAME               POD-SELECTOR   AGE
# deny-all-ingress   <none>         2s
```

## Lab 4 — Image Verification
```bash
kubectl apply -f manifests/kyverno/verify-image.yaml
# Audit mode — won't block, but logs violation
kubectl get policyreport -A
kubectl describe policyreport -n apps
```

## Lab 5 — Policy CLI testing (no cluster needed)
```bash
# Install kyverno CLI
brew install kyverno

# Test policy against a manifest before applying
kyverno apply manifests/kyverno/generate-networkpolicy.yaml \
  --resource /tmp/test-namespace.yaml
```

## Key Concepts
- Validate: admission webhook — blocks or audits non-conforming resources
- Mutate: auto-patch resources on creation (add labels, set defaults)
- Generate: create new resources when a trigger resource is created
- VerifyImages: check image signatures (Cosign/Sigstore)
- Enforce vs Audit: Enforce blocks, Audit logs but allows
- PolicyReport CRD: stores audit results, queryable with kubectl
