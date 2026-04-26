CLUSTER_NAME   := cloudnative
KUBECTL        := kubectl
HELM           := helm
CILIUM_NS      := kube-system
ARGOCD_NS      := argocd
MONITORING_NS  := monitoring
ISTIO_NS       := istio-system
KYVERNO_NS     := kyverno
OTEL_NS        := opentelemetry
BACKSTAGE_NS   := backstage

.PHONY: help cluster-create cluster-destroy cluster-status \
        cilium-install cilium-hubble cilium-status \
        argo-install argo-rollouts argo-workflows argo-ui \
        monitoring-install monitoring-ui tempo-install \
        otel-install otel-status \
        istio-install istio-ui kiali-install \
        kyverno-install kyverno-policies \
        backstage-install backstage-ui \
        vagrant-up vagrant-ssh vagrant-destroy \
        lab-lfcs lab-cca lab-capa lab-cgoa lab-cba lab-otca \
        lab-pca lab-ica lab-kca lab-cnpe lab-cnpa \
        full-stack clean

help:
	@echo ""
	@echo "  Cloud Native Lab — command reference"
	@echo "  ====================================="
	@echo ""
	@echo "  CLUSTER"
	@echo "    make cluster-create     Create kind cluster (Cilium CNI, no kube-proxy)"
	@echo "    make cluster-destroy    Delete kind cluster"
	@echo "    make cluster-status     Show node and pod status"
	@echo ""
	@echo "  CILIUM (CCA)"
	@echo "    make cilium-install     Install Cilium CNI + kube-proxy replacement"
	@echo "    make cilium-hubble      Enable Hubble observability UI"
	@echo "    make cilium-status      Run cilium status + connectivity test"
	@echo ""
	@echo "  ARGO (CAPA + CGOA)"
	@echo "    make argo-install       Install ArgoCD"
	@echo "    make argo-rollouts      Install Argo Rollouts"
	@echo "    make argo-workflows     Install Argo Workflows"
	@echo "    make argo-ui            Port-forward ArgoCD UI to :8080"
	@echo ""
	@echo "  MONITORING (PCA)"
	@echo "    make monitoring-install Install kube-prometheus-stack + Loki + Tempo"
	@echo "    make monitoring-ui      Port-forward Grafana to :3000"
	@echo ""
	@echo "  OPENTELEMETRY (OTCA)"
	@echo "    make otel-install       Install OpenTelemetry Operator + Collector"
	@echo "    make otel-status        Show collector pipeline status"
	@echo ""
	@echo "  ISTIO (ICA)"
	@echo "    make istio-install      Install Istio + Kiali dashboard"
	@echo "    make istio-ui           Port-forward Kiali to :20001"
	@echo ""
	@echo "  KYVERNO (KCA)"
	@echo "    make kyverno-install    Install Kyverno"
	@echo "    make kyverno-policies   Apply generate + mutate + verify-image policies"
	@echo ""
	@echo "  BACKSTAGE (CBA)"
	@echo "    make backstage-install  Run Backstage via Docker"
	@echo "    make backstage-ui       Open Backstage at :7007"
	@echo ""
	@echo "  LINUX VM (LFCS)"
	@echo "    make vagrant-up         Start Ubuntu 22.04 VM for Linux exercises"
	@echo "    make vagrant-ssh        SSH into the VM"
	@echo "    make vagrant-destroy    Remove the VM"
	@echo ""
	@echo "  LABS"
	@echo "    make lab-lfcs           LFCS Linux exercises"
	@echo "    make lab-cca            CCA Cilium exercises"
	@echo "    make lab-capa           CAPA Argo exercises"
	@echo "    make lab-cgoa           CGOA GitOps exercises"
	@echo "    make lab-cba            CBA Backstage exercises"
	@echo "    make lab-otca           OTCA OpenTelemetry exercises"
	@echo "    make lab-pca            PCA Prometheus exercises"
	@echo "    make lab-ica            ICA Istio exercises"
	@echo "    make lab-kca            KCA Kyverno exercises"
	@echo "    make lab-cnpe           CNPE Platform Engineering exercises"
	@echo "    make lab-cnpa           CNPA Cloud Native exercises"
	@echo ""
	@echo "  SHORTCUTS"
	@echo "    make full-stack         cluster + cilium + argo + monitoring + otel + istio + kyverno"
	@echo "    make clean              Remove cluster"
	@echo ""

# ─── CLUSTER ─────────────────────────────────────────────────────────────────

cluster-create:
	kind create cluster --config kind/cluster.yaml --name $(CLUSTER_NAME)
	@echo "Labelling nodes..."
	$(KUBECTL) label node cloudnative-worker  role=worker-apps          --overwrite
	$(KUBECTL) label node cloudnative-worker2 role=worker-platform      --overwrite
	@echo "Cluster ready. Now run: make cilium-install"

cluster-destroy:
	@echo "WARNING: This will delete the '$(CLUSTER_NAME)' cluster."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	kind delete cluster --name $(CLUSTER_NAME)

cluster-status:
	@echo "=== Nodes ==="
	$(KUBECTL) get nodes -o wide
	@echo ""
	@echo "=== All Pods ==="
	$(KUBECTL) get pods -A

# ─── CILIUM (CCA) ────────────────────────────────────────────────────────────

cilium-install:
	$(HELM) repo add cilium https://helm.cilium.io/ 2>/dev/null || true
	$(HELM) repo update
	$(HELM) upgrade --install cilium cilium/cilium \
		--namespace $(CILIUM_NS) \
		--set routingMode=tunnel \
		--set tunnelProtocol=vxlan \
		--set kubeProxyReplacement=true \
		--set k8sServiceHost=cloudnative-control-plane \
		--set k8sServicePort=6443 \
		--set hubble.enabled=true \
		--set hubble.relay.enabled=true \
		--set hubble.ui.enabled=true \
		--wait --timeout 5m
	@echo "Cilium installed. Run: make cilium-status"

cilium-hubble:
	@echo "Hubble UI → http://localhost:12000"
	$(KUBECTL) port-forward svc/hubble-ui -n $(CILIUM_NS) 12000:80

cilium-status:
	$(KUBECTL) -n $(CILIUM_NS) exec ds/cilium -- cilium status --brief
	@echo ""
	@echo "=== Hubble Flows ==="
	$(KUBECTL) -n $(CILIUM_NS) exec ds/cilium -- hubble observe --last 20 2>/dev/null || echo "Hubble relay not ready yet"

# ─── ARGO (CAPA + CGOA) ──────────────────────────────────────────────────────

argo-install:
	$(KUBECTL) create namespace $(ARGOCD_NS) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	$(KUBECTL) apply -n $(ARGOCD_NS) --server-side --force-conflicts \
		-f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
	@echo "Waiting for ArgoCD to be ready..."
	$(KUBECTL) wait --for=condition=available --timeout=180s deployment/argocd-server -n $(ARGOCD_NS)
	@echo "ArgoCD ready. Run: make argo-ui"

argo-rollouts:
	$(KUBECTL) create namespace argo-rollouts --dry-run=client -o yaml | $(KUBECTL) apply -f -
	$(KUBECTL) apply -n argo-rollouts --server-side --force-conflicts \
		-f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
	$(KUBECTL) wait --for=condition=available --timeout=120s deployment/argo-rollouts -n argo-rollouts
	$(KUBECTL) apply -f manifests/argo/rollouts/

argo-workflows:
	$(KUBECTL) create namespace argo --dry-run=client -o yaml | $(KUBECTL) apply -f -
	$(KUBECTL) apply -n argo --server-side --force-conflicts \
		-f https://github.com/argoproj/argo-workflows/releases/latest/download/quick-start-minimal.yaml
	$(KUBECTL) wait --for=condition=available --timeout=180s deployment/workflow-controller -n argo
	$(KUBECTL) apply -f manifests/argo/workflows/

argo-password:
	@$(KUBECTL) -n $(ARGOCD_NS) get secret argocd-initial-admin-secret \
		-o jsonpath="{.data.password}" | base64 -d && echo ""

argo-ui:
	@echo "ArgoCD UI → http://localhost:8080  (admin / run 'make argo-password')"
	$(KUBECTL) port-forward svc/argocd-server -n $(ARGOCD_NS) 8080:443

# ─── MONITORING (PCA) ────────────────────────────────────────────────────────

monitoring-install:
	$(HELM) repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
	$(HELM) repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
	$(HELM) repo update
	$(KUBECTL) create namespace $(MONITORING_NS) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	$(HELM) upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
		--namespace $(MONITORING_NS) \
		--values monitoring/prometheus/values.yaml \
		--wait --timeout 5m
	$(HELM) upgrade --install loki grafana/loki \
		--namespace $(MONITORING_NS) \
		--set loki.auth_enabled=false \
		--set loki.commonConfig.replication_factor=1 \
		--set loki.storage.type=filesystem \
		--set loki.useTestSchema=true \
		--set singleBinary.replicas=1 \
		--set read.replicas=0 \
		--set write.replicas=0 \
		--set backend.replicas=0 \
		--set chunksCache.enabled=false \
		--set resultsCache.enabled=false \
		--wait --timeout 3m
	$(HELM) upgrade --install tempo grafana/tempo \
		--namespace $(MONITORING_NS) \
		--set tempo.storage.trace.backend=local \
		--wait --timeout 3m
	$(HELM) upgrade --install promtail grafana/promtail \
		--namespace $(MONITORING_NS) \
		--set "config.clients[0].url=http://loki-gateway.$(MONITORING_NS).svc.cluster.local/loki/api/v1/push" \
		--wait --timeout 2m

monitoring-ui:
	@echo "Grafana → http://localhost:3000  (admin / run: kubectl get secret ...)"
	$(KUBECTL) port-forward svc/kube-prometheus-stack-grafana -n $(MONITORING_NS) 3000:80

# ─── OPENTELEMETRY (OTCA) ────────────────────────────────────────────────────

otel-install:
	$(HELM) repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts 2>/dev/null || true
	$(HELM) repo update
	$(KUBECTL) create namespace $(OTEL_NS) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	$(HELM) upgrade --install opentelemetry-operator open-telemetry/opentelemetry-operator \
		--namespace $(OTEL_NS) \
		--set admissionWebhooks.certManager.enabled=false \
		--set admissionWebhooks.autoGenerateCert.enabled=true \
		--wait --timeout 3m
	$(KUBECTL) apply -f otel/collector/collector.yaml
	$(KUBECTL) apply -f otel/instrumentation/instrumentation.yaml

otel-status:
	$(KUBECTL) get opentelemetrycollector -n $(OTEL_NS)
	$(KUBECTL) get instrumentation -n $(OTEL_NS)

# ─── ISTIO (ICA) ─────────────────────────────────────────────────────────────

istio-install:
	@which istioctl || (echo "istioctl not found — run 'make ansible-tools' first" && exit 1)
	istioctl install --set profile=demo -y
	$(KUBECTL) label namespace default istio-injection=enabled --overwrite
	$(HELM) repo add kiali https://kiali.org/helm-charts 2>/dev/null || true
	$(HELM) repo update
	$(HELM) upgrade --install kiali-server kiali/kiali-server \
		--namespace $(ISTIO_NS) \
		--set auth.strategy=anonymous \
		--wait --timeout 3m
	$(KUBECTL) apply -f manifests/istio/

istio-ui:
	@echo "Kiali UI → http://localhost:20001"
	$(KUBECTL) port-forward svc/kiali -n $(ISTIO_NS) 20001:20001

# ─── KYVERNO (KCA) ───────────────────────────────────────────────────────────

kyverno-install:
	$(HELM) repo add kyverno https://kyverno.github.io/kyverno/ 2>/dev/null || true
	$(HELM) repo update
	$(HELM) upgrade --install kyverno kyverno/kyverno \
		--namespace $(KYVERNO_NS) --create-namespace \
		--set replicaCount=1 \
		--wait

kyverno-policies:
	$(KUBECTL) apply -f manifests/kyverno/

# ─── BACKSTAGE (CBA) ─────────────────────────────────────────────────────────

backstage-install:
	@echo "Starting Backstage via Docker (no cluster resources needed)..."
	docker run -d --name backstage \
		-p 7007:7007 \
		-e BACKSTAGE_BASE_URL=http://localhost:7007 \
		ghcr.io/backstage/backstage:latest 2>/dev/null || \
		docker start backstage
	@echo "Backstage → http://localhost:7007 (takes ~60s to start)"

backstage-ui:
	open http://localhost:7007

# ─── LINUX VM (LFCS) ─────────────────────────────────────────────────────────

vagrant-up:
	cd vagrant && vagrant up

vagrant-ssh:
	cd vagrant && vagrant ssh

vagrant-destroy:
	@echo "WARNING: This will destroy the Linux VM."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	cd vagrant && vagrant destroy -f

# ─── ANSIBLE ─────────────────────────────────────────────────────────────────

ansible-tools:
	ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/setup-tools.yml

# ─── LABS ────────────────────────────────────────────────────────────────────

lab-lfcs:
	@cat labs/lfcs/README.md
lab-cca:
	@cat labs/cca/README.md
lab-capa:
	@cat labs/capa/README.md
lab-cgoa:
	@cat labs/cgoa/README.md
lab-cba:
	@cat labs/cba/README.md
lab-otca:
	@cat labs/otca/README.md
lab-pca:
	@cat labs/pca/README.md
lab-ica:
	@cat labs/ica/README.md
lab-kca:
	@cat labs/kca/README.md
lab-cnpe:
	@cat labs/cnpe/README.md
lab-cnpa:
	@cat labs/cnpa/README.md

# ─── SHORTCUTS ───────────────────────────────────────────────────────────────

full-stack: cluster-create cilium-install argo-install monitoring-install otel-install kyverno-install
	@echo ""
	@echo "Full stack ready."
	@echo "  ArgoCD:       make argo-ui"
	@echo "  Grafana:      make monitoring-ui"
	@echo "  Kiali:        make istio-ui"
	@echo "  Hubble:       make cilium-hubble"
	@echo "  Backstage:    make backstage-install"
	@echo "  Linux VM:     make vagrant-up"

clean:
	@echo "This will delete the cluster."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	kind delete cluster --name $(CLUSTER_NAME) 2>/dev/null || true
