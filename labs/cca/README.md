# CCA — Cilium Certified Associate

## Install
```bash
make cluster-create
make cilium-install
```

## Lab 1 — Verify Cilium is running
```bash
kubectl get pods -n kube-system -l k8s-app=cilium
kubectl -n kube-system exec ds/cilium -- cilium status
cilium connectivity test            # end-to-end connectivity check
```

## Lab 2 — Hubble observability
```bash
make cilium-hubble                  # port-forward Hubble UI → :12000
# In Hubble UI: filter by namespace, see live flow graph

# CLI flows
kubectl -n kube-system exec ds/cilium -- \
  hubble observe --namespace apps --last 50
kubectl -n kube-system exec ds/cilium -- \
  hubble observe --verdict DROPPED  # see blocked traffic
```

## Lab 3 — L3/L4 Network Policy (same as K8s NetworkPolicy)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-only-frontend
  namespace: apps
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8080
EOF
```

## Lab 4 — L7 HTTP Policy (Cilium-only, beyond K8s)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-get-only
  namespace: apps
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: "/api/.*"
EOF
# POST requests will now be blocked at L7
```

## Lab 5 — Verify kube-proxy replacement
```bash
kubectl -n kube-system exec ds/cilium -- \
  cilium status | grep "KubeProxyReplacement"
# Should show: KubeProxyReplacement: True
kubectl get pods -n kube-system | grep kube-proxy  # should be empty
```

## Key Concepts
- Cilium uses eBPF — no iptables rules, runs in kernel
- Hubble = Cilium's observability layer (like Wireshark for K8s)
- CiliumNetworkPolicy extends K8s NetworkPolicy with L7 HTTP/gRPC rules
- kube-proxy replacement: Cilium handles all service load-balancing via eBPF
- Identity-based: policies match on labels, not IPs
