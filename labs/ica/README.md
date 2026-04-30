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

Your app knows nothing about this. Envoy handles everything transparently.
`2/2 READY` on a pod = app container + Envoy sidecar.

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

**What we proved:** Applied 90/10 weight split, watched it in Kiali graph. Also routed `x-canary: true` header always to v2 — zero code change in the app.

---

### DestinationRule — Rules for a Specific Destination

**What it is:** Defines subsets (v1/v2) and policies like circuit breaker, connection pool, TLS.

**Real world:** Works hand-in-hand with VirtualService — VS says "send 10% to v2", DR says "v2 means pods with label `version=v2`".

**Analogy:** The rulebook for each lane — speed limit, max cars, what to do if a car breaks down.

---

### Fault Injection — Break Things on Purpose

**What it is:** Istio deliberately delays or fails requests — without touching app code at all.

**What we proved:** 50% of requests got a 3s delay, 20% got a 503 error. Saw alternating fast/slow responses in the output.

**Real world:** Chaos engineering — test whether your frontend handles slow backends gracefully before production does.

**Analogy:** A fire drill. Not a real fire — but testing whether people know what to do when it happens.

```text
Request → Envoy → [50% chance: wait 3s] → [20% chance: return 503] → app
```

**Key insight:** The app never knows faults are injected — it only happens inside Envoy. This lets you test resilience patterns (timeouts, retries, fallbacks) without changing a single line of code.

---

### Circuit Breaker (outlierDetection) — Auto-eject Bad Pods

**What it is:** If a pod keeps returning errors, Envoy stops sending traffic to it automatically.

**What we configured:**

- After 3 consecutive 5xx from a pod → eject it from the pool
- Ejection lasts 30s, then the pod gets a chance to recover
- Max 50% of pods ejected at once — prevents total service outage

**Real world:** One pod has a memory leak and starts returning 500s. Istio detects it and routes around it while your HPA spins up a healthy replacement.

**Analogy:** A supermarket checkout lane — if the register keeps breaking, the supervisor closes it and sends customers elsewhere. Tries reopening after 30 minutes.

---

### mTLS — Encrypted Pod-to-Pod Traffic

**What it is:** All traffic between Envoy sidecars is automatically encrypted (TLS) and mutually authenticated (both sides verify identity).

**PERMISSIVE** = accepts both plain HTTP and mTLS (migration mode — default)

**STRICT** = only mTLS allowed — plain HTTP connections are reset immediately

**What we proved:**

| Caller | Mode | Result |
| --- | --- | --- |
| Pod with sidecar | STRICT | 200 — Envoy handles mTLS transparently |
| Pod without sidecar | STRICT | Connection reset — can't do mTLS handshake |

**Real world:** Even inside the cluster, traffic between services is encrypted. A rogue pod that somehow gets onto the network can't sniff or MITM service-to-service calls.

**Analogy:** Every conversation in the office requires ID badges shown on both sides — no anonymous visitors, no eavesdropping.

**Kiali signal:** Lock icon on graph edges = mTLS active between those services.

---

### AuthorizationPolicy — Istio RBAC

**What it is:** Allow/deny which service can call which other service, on which HTTP path, with which method.

**What we proved:**

```text
traffic-gen  (sa: default)  ── GET  ──► demo-app   ✅ 200
traffic-gen  (sa: default)  ── POST ──► demo-app   ❌ 403
stranger-pod (sa: stranger) ── GET  ──► demo-app   ❌ 403
no-sidecar   (no mTLS)      ── GET  ──► demo-app   ❌ connection reset
```

**Pattern:** Always start with `deny-all` (empty spec), then add explicit ALLOW rules. This is defence-in-depth — nothing is reachable until you say so.

**Real world:** Only the `frontend` service account can call `backend` on `GET /api/*`. The database service can only be reached by the `api` service. No lateral movement between microservices.

**Analogy:** Office access control — the intern can enter the lobby but not the server room.

---

### Kiali — The Control Tower

**What it is:** Live service mesh dashboard — nodes = services, edges = live traffic between them.

**What you see:**

- Traffic rate (rps) on every edge
- Error % highlighted in red/orange
- Circuit breaker icon when outlierDetection is configured
- Lock icon on edges when mTLS is active
- Latency distribution per service

**Analogy:** Air traffic control radar — every plane (service), every flight path (traffic), and every plane in trouble (errors) visible in real time.

**Fix we hit:** Kiali defaults to looking for Prometheus at `prometheus.istio-system:9090`. Since ours is in the `monitoring` namespace, we patched it via:

```bash
helm upgrade kiali-server kiali/kiali-server --namespace istio-system \
  --set external_services.prometheus.url="http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090"
```

---

### Three Layers of Security — How They Stack

```text
Request arrives
      │
      ▼
mTLS (PeerAuthentication)
  └── No sidecar? → connection reset immediately
      │
      ▼
AuthorizationPolicy
  └── Wrong service account? → 403
  └── Wrong HTTP method? → 403
      │
      ▼
VirtualService / DestinationRule
  └── Route to correct version, apply circuit breaker
      │
      ▼
Your app pod — request finally arrives here
```

---

### How All Traffic Features Fit Together

```text
Request comes in
      │
      ▼
VirtualService         ← which version? header match? fault to inject?
      │
      ▼
DestinationRule        ← is this pod healthy? circuit breaker tripped?
      │
      ▼
mTLS (Envoy↔Envoy)     ← encrypt + mutually authenticate
      │
      ▼
AuthorizationPolicy    ← is this caller allowed for this method/path?
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

# Generate continuous traffic — watch split in Kiali → Graph → default namespace
kubectl run traffic-gen --image=curlimages/curl --restart=Never -n default -- \
  sh -c 'while true; do curl -s http://demo-app/get -o /dev/null; sleep 0.5; done'
```

## Lab 2 — Header-based Routing

```bash
# x-canary: true always routes to v2
kubectl exec -n default traffic-gen -- \
  curl -s http://demo-app/get -H "x-canary: true" | python3 -m json.tool
```

## Lab 3 — Fault Injection

```bash
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

## Lab 5 — mTLS STRICT

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

# Pod without sidecar cannot connect
kubectl run no-sidecar --image=curlimages/curl --restart=Never \
  --annotations='sidecar.istio.io/inject=false' -n default -- \
  curl -sv --max-time 5 http://demo-app/get
# Result: "Recv failure: Connection reset by peer"

# Pod with sidecar still works
kubectl exec -n default traffic-gen -- curl -s -o /dev/null -w "%{http_code}" http://demo-app/get
# Result: 200

# Kiali → Graph → lock icon on edges = mTLS active
istioctl proxy-status
```

## Lab 6 — AuthorizationPolicy

```bash
# Step 1: deny everything
cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: default
spec: {}
EOF
# All requests → 403

# Step 2: allow only traffic-gen (sa: default) → demo-app on GET
cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-traffic-gen
  namespace: default
spec:
  selector:
    matchLabels:
      app: demo-app
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/default/sa/default"
      to:
        - operation:
            methods: ["GET"]
EOF

# GET → 200, POST → 403, different service account → 403
kubectl exec -n default traffic-gen -- \
  curl -s -o /dev/null -w "%{http_code}" http://demo-app/get

# Cleanup
kubectl delete authorizationpolicy deny-all allow-traffic-gen -n default
```

## Key Concepts for ICA Exam

| Concept | Remember |
| --- | --- |
| VirtualService | Routing rules — weights, headers, fault injection |
| DestinationRule | Subsets + policies — circuit breaker, TLS, connection pool |
| PeerAuthentication | mTLS enforcement — PERMISSIVE (both) vs STRICT (mTLS only) |
| AuthorizationPolicy | Istio RBAC — deny-all first, then explicit ALLOW rules |
| Kiali | Mesh topology, error %, mTLS lock icons, circuit breaker icons |
| Envoy sidecar | All pod traffic in/out goes through it — app is unaware |
| istiod | Control plane — pushes xDS config to all Envoy sidecars |
| 2/2 READY | App container + Envoy sidecar both running |
| demo profile | Install profile for learning — includes ingress + egress gateways |
| proxy-status | `istioctl proxy-status` — checks all sidecars are synced with istiod |
