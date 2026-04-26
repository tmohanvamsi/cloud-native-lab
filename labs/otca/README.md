# OTCA — OpenTelemetry Certified Associate

## Install
```bash
make otel-install
make otel-status
```

## Lab 1 — Verify Collector pipeline
```bash
kubectl get pods -n opentelemetry
kubectl logs -n opentelemetry -l app.kubernetes.io/name=otel-collector --tail=50
# Should see: Everything is ready, started pipelines: traces, metrics, logs
```

## Lab 2 — Deploy an instrumented app
```bash
# Auto-instrumentation: just add annotation, no code changes needed
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app
  namespace: apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-app
  template:
    metadata:
      labels:
        app: python-app
      annotations:
        instrumentation.opentelemetry.io/inject-python: "opentelemetry/auto-instrumentation"
    spec:
      containers:
        - name: python-app
          image: python:3.11-slim
          command: ["python", "-m", "http.server", "8080"]
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
EOF
kubectl get pods -n apps -l app=python-app
# OTel sidecar injected — sends traces to collector automatically
```

## Lab 3 — View traces in Grafana/Tempo
```bash
make monitoring-ui          # → http://localhost:3000
# Explore → Tempo datasource → Search traces
# Filter by service: python-app
```

## Lab 4 — Understand the pipeline
```bash
# OTLP signal flow:
# App (SDK) → OTLP/gRPC → Collector receiver
# Collector: receiver → processor → exporter
# Traces → Tempo
# Metrics → Prometheus
# Logs → Loki

kubectl describe opentelemetrycollector otel-collector -n opentelemetry
```

## Lab 5 — Manual trace with curl
```bash
# Send a test span directly to collector
kubectl port-forward svc/otel-collector-collector -n opentelemetry 4318:4318 &
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"test-service"}}]},"scopeSpans":[{"spans":[{"traceId":"5b8efff798038103d269b633813fc60c","spanId":"eee19b7ec3c1b173","name":"test-span","kind":1,"startTimeUnixNano":"1676956426000000000","endTimeUnixNano":"1676956426000000001","status":{}}]}]}]}'
```

## Key Concepts
- OTel = vendor-neutral standard for traces, metrics, logs (replaces Jaeger SDK, Zipkin SDK)
- Collector = agent that receives, processes, exports signals — decouples app from backend
- Auto-instrumentation: inject OTel SDK via annotation, zero code change
- OTLP = OpenTelemetry Protocol (the wire format, gRPC or HTTP)
- Signals: Traces (request path), Metrics (numbers over time), Logs (events)
- Context propagation: traceparent header links spans across services
