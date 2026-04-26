# PCA — Prometheus Certified Associate

## Access
```bash
make monitoring-ui          # Grafana → http://localhost:3000
# Prometheus direct → http://localhost:9090 (NodePort 30900)
```

## Lab 1 — PromQL Fundamentals
```bash
# In Prometheus UI → Graph tab

# Instant vector: current value
up

# Filter by label
up{job="kubelet"}

# Rate: per-second rate over 5m window
rate(container_cpu_usage_seconds_total[5m])

# Top 5 memory-consuming pods
topk(5, container_memory_working_set_bytes{container!=""})

# Aggregation
sum by (namespace) (container_memory_working_set_bytes{container!=""})

# Ratio: memory used vs limit
container_memory_working_set_bytes / container_spec_memory_limit_bytes
```

## Lab 2 — Recording Rules (pre-compute expensive queries)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: recording-rules
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: cluster.rules
      interval: 30s
      rules:
        - record: cluster:cpu_usage:rate5m
          expr: sum(rate(container_cpu_usage_seconds_total[5m]))
        - record: namespace:memory_usage:bytes
          expr: sum by (namespace) (container_memory_working_set_bytes{container!=""})
EOF
# Query the recording rule — instant, no computation
# cluster:cpu_usage:rate5m
```

## Lab 3 — Alerting Rules
```bash
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: alert-rules
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: node.alerts
      rules:
        - alert: HighMemoryUsage
          expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Node {{ $labels.instance }} memory < 10%"
        - alert: PodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod {{ $labels.pod }} is crash-looping"
EOF
kubectl get prometheusrules -n monitoring
```

## Lab 4 — ServiceMonitor (scrape your own app)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: apps
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
EOF
# Prometheus auto-discovers this and starts scraping /metrics
```

## Key Concepts
- Prometheus scrapes (pull model) — targets expose /metrics endpoint
- PromQL: instant vector, range vector, rate(), irate(), sum by(), topk()
- Recording rules: materialized views for expensive queries
- Alerting rules: fire when expr is true for `for` duration
- AlertManager: routes alerts to Slack/PagerDuty/email, handles silences
- ServiceMonitor/PodMonitor: Prometheus Operator CRDs for scrape config
