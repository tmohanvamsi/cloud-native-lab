# ICA — Istio Certified Associate

## Install
```bash
make istio-install          # Istio (demo profile) + Kiali
make istio-ui               # Kiali → http://localhost:20001
```

## Lab 1 — Traffic Management (VirtualService + DestinationRule)
```bash
kubectl create namespace mesh --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace mesh istio-injection=enabled --overwrite

# Deploy v1 and v2 of demo app
kubectl apply -f manifests/istio/

# 90% traffic to v1, 10% to v2 (canary)
kubectl get virtualservice demo-app -n mesh -o yaml

# Switch all traffic to v2
kubectl patch virtualservice demo-app -n mesh --type=json \
  -p='[{"op":"replace","path":"/spec/http/1/route/0/weight","value":0},
       {"op":"replace","path":"/spec/http/1/route/1/weight","value":100}]'
```

## Lab 2 — Fault Injection
```bash
# The VirtualService already has a 10% delay of 5s injected
# Verify with: curl from inside cluster multiple times — some will be slow
kubectl run curl --image=curlimages/curl -it --rm --restart=Never \
  -- sh -c 'for i in $(seq 1 10); do time curl -s http://demo-app.mesh/; done'
```

## Lab 3 — Circuit Breaker (DestinationRule outlierDetection)
```bash
# Already configured in manifests/istio/destination-rule.yaml
# 3 consecutive 5xx → eject endpoint for 30s
kubectl get destinationrule demo-app -n mesh -o yaml

# Simulate errors and watch Kiali circuit breaker icon appear
```

## Lab 4 — mTLS verification
```bash
# Check mTLS status
istioctl x check-inject -n mesh
istioctl proxy-status

# Verify STRICT mTLS
kubectl apply -n mesh -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT
EOF

# Test: non-sidecar pod cannot reach mesh service
kubectl run outsider --image=curlimages/curl --restart=Never \
  -- curl -s http://demo-app.mesh.svc.cluster.local/
# Should get: connection refused or RBAC denied
```

## Lab 5 — Authorization Policy
```bash
cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-only
  namespace: mesh
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/mesh/sa/frontend"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/api/*"]
EOF
```

## Key Concepts
- VirtualService: traffic routing rules (weights, headers, fault injection)
- DestinationRule: load balancing, connection pool, circuit breaker, TLS settings
- PeerAuthentication: mTLS enforcement (PERMISSIVE = allow both, STRICT = only mTLS)
- AuthorizationPolicy: Istio RBAC — who can call what
- Kiali: service mesh topology graph, health, traffic flow visualization
- Envoy sidecar: all traffic in/out of pod goes through Envoy proxy
