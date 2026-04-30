# ICA — Istio Certified Associate

## What Each Piece Is

### The Big Picture

Without Istio, Service A → Service B is a direct connection — no rules, no security, no visibility.
With Istio, every pod gets an **Envoy sidecar** injected automatically. All traffic flows through
that sidecar. Istio controls all sidecars from a central brain called **istiod**.

```text
Pod A                          Pod B
┌─────────────┐               ┌─────────────┐
│ your-app    │               │ your-app    │
│ envoy ◄─────┼───traffic─────┼─► envoy     │
└─────────────┘               └─────────────┘
      ▲                              ▲
      └──────────── istiod ──────────┘
              (the control plane)
```

Your app knows nothing about this. Envoy handles everything transparently. (2/2 READY = app + sidecar)

---

### VirtualService — Traffic Cop

**What it is:** Routing rules that tell Envoy where to send traffic.
**Real world:** Canary deploy — send 10% to v2, watch for errors, bump to 50%, then 100%. No redeploy needed.
**Analogy:** A roundabout officer — "9 of every 10 cars go left, 1 goes right."

```text
User request
    │
    ▼
VirtualService
    ├── x-canary: true header? → always v2
    └── default: 90% → v1 / 10% → v2
```

---

### DestinationRule — Rules for a Specific Destination

**What it is:** Defines subsets (v1/v2) and policies like circuit breaker, connection pool, TLS.
**Real world:** Works hand-in-hand with VirtualService — VS says "send 10% to v2", DR says "v2 means pods with label version=v2".
**Analogy:** The rulebook for each lane — speed limit, max cars, what to do if a car breaks down.

---

### Fault Injection — Break Things on Purpose

**What it is:** Istio deliberately delays or fails requests — without touching app code at all.
**What we did:** 50% of requests got a 3s delay, 20% got a 503 error returned immediately.
**Real world:** Chaos engineering — test whether your frontend handles slow backends gracefully before prod does.
**Analogy:** A fire drill. Not a real fire — but testing whether people know what to do.

```text
Request → Envoy → [50% chance: wait 3s] → [20% chance: return 503] → app
```

---

### Circuit Breaker (outlierDetection) — Auto-eject Bad Pods

**What it is:** If a pod keeps returning errors, Envoy stops sending traffic to it automatically.
**What we configured:** After 3 consecutive 5xx from a pod → eject it for 30s. Max 50% ejected at once.
**Real world:** One pod has a memory leak and starts returning 500s. Istio detects it and routes around it while a healthy pod spins up.
**Analogy:** A supermarket checkout lane — if the register keeps breaking, the supervisor closes it and sends customers elsewhere. Tries reopening after 30 minutes.

---

### mTLS — Encrypted Pod-to-Pod Traffic

**What it is:** All traffic between sidecars is automatically encrypted and mutually authenticated.
**PERMISSIVE** = accepts both plain and mTLS traffic (migration mode)
**STRICT** = only mTLS allowed — plain traffic rejected
**Real world:** Even inside the cluster, traffic between services is encrypted. A rogue pod can't sniff traffic.
**Analogy:** Every conversation in the office requires ID badges on both sides — no anonymous visitors.

---

### AuthorizationPolicy — Istio RBAC

**What it is:** Allow/deny which service can call which other service, on which path, with which method.
**Real world:** Only the `frontend` service can call `backend` on GET /api/* — no other service can reach it.
**Analogy:** Office access control — the intern can enter the lobby but not the server room.

---

### Kiali — The Control Tower

**What it is:** Live service mesh dashboard — nodes = services, edges = traffic between them.
**What you see:** Traffic rates, error %, latency, circuit breaker icons, mTLS lock icons.
**Analogy:** Air traffic control radar — every plane (service), every flight path (traffic), every plane in trouble (errors) in real time.

---

### How They All Fit Together

```text
Request comes in
      │
      ▼
VirtualService         ← which version? header match?
      │
      ▼
DestinationRule        ← is this pod healthy? circuit breaker tripped?
(circuit breaker)
      │
      ▼
Fault Injection        ← should I add a delay or return an error? (if configured)
      │
      ▼
mTLS (Envoy↔Envoy)     ← encrypt + authenticate the connection
      │
      ▼
AuthorizationPolicy    ← is this caller allowed to reach this service?
      │
      ▼
Target pod (v1 / v2)   ← request finally arrives here
```

---

## Install

```bash
make istio-install          # Istio (demo profile) + Kiali
make istio-ui               # Kiali → http://localhost:20001
```

## Lab 1 — Traffic Splitting (VirtualService 90/10)

```bash
# Deploy v1 (2 replicas) and v2 (1 replica) in default namespace
kubectl apply -f manifests/istio/

# Verify sidecar injected — pods show 2/2 READY
kubectl get pods -n default

# Generate traffic — watch split in Kiali → Graph → default namespace
kubectl run traffic-gen --image=curlimages/curl --restart=Never -n default -- \
  sh -c 'while true; do curl -s http://demo-app/get -o /dev/null; sleep 0.5; done'
```

## Lab 2 — Header-based Routing

```bash
# x-canary: true always routes to v2
kubectl exec -n default traffic-gen -- \
  curl -s http://demo-app/get -H "x-canary: true" | python3 -m json.tool | grep -A2 headers
```

## Lab 3 — Fault Injection

```bash
# Apply: 50% requests get 3s delay, 20% get 503
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: demo-app
  namespace: default
spec:
  hosts:
    - demo-app
  http:
    - fault:
        delay:
          percentage:
            value: 50
          fixedDelay: 3s
        abort:
          percentage:
            value: 20
          httpStatus: 503
      route:
        - destination:
            host: demo-app
            subset: v1
          weight: 90
        - destination:
            host: demo-app
            subset: v2
          weight: 10
EOF

# Observe — some fast, some slow, some 503
for i in $(seq 1 10); do
  kubectl exec -n default traffic-gen -- \
    curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://demo-app/get
done
```

## Lab 4 — Circuit Breaker

```bash
# Remove fault injection, apply outlierDetection
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: demo-app
  namespace: default
spec:
  host: demo-app
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
EOF
# Kiali → Services → demo-app → shows circuit breaker icon
```

## Lab 5 — mTLS (NEXT SESSION)

```bash
# Enable STRICT mTLS for default namespace
cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: default
spec:
  mtls:
    mode: STRICT
EOF

# Verify
istioctl proxy-status
istioctl x check-inject -n default

# Kiali → Graph → edges show lock icon = mTLS active
```

## Lab 6 — AuthorizationPolicy (NEXT SESSION)

```bash
cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-traffic-gen-only
  namespace: default
spec:
  selector:
    matchLabels:
      app: demo-app
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/default/sa/default"]
      to:
        - operation:
            methods: ["GET"]
EOF
```

## Key Concepts for ICA Exam

| Concept | Remember |
| --- | --- |
| VirtualService | Routing rules — weights, headers, fault injection |
| DestinationRule | Subsets + policies — circuit breaker, TLS, connection pool |
| PeerAuthentication | mTLS enforcement — PERMISSIVE (both) vs STRICT (mTLS only) |
| AuthorizationPolicy | Istio RBAC — from/to/when rules |
| Kiali | Mesh topology, traffic health, mTLS lock icons |
| Envoy sidecar | All pod traffic goes through it — app is unaware |
| istiod | Control plane — pushes config to all Envoy sidecars |
| demo profile | Install profile for learning — includes egress gateway |
