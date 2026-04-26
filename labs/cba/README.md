# CBA — Certified Backstage Associate

## Start
```bash
make backstage-install      # runs Backstage via Docker on :7007
make backstage-ui           # opens browser
```

## What is Backstage?
Backstage is an Internal Developer Portal (IDP) — a single place where engineers find:
- All services (software catalog)
- Docs (TechDocs)
- Templates (golden paths — create a new service in one click)
- Plugins (CI/CD status, PagerDuty, cost, etc.)

## Lab 1 — Software Catalog
```bash
# Open http://localhost:7007/catalog
# You see a list of "components" (services, APIs, libraries)

# Register your own service
# Click "Register Existing Component" → paste a catalog-info.yaml URL
```

## Lab 2 — catalog-info.yaml (how Backstage discovers services)
```yaml
# Add this file to the root of any service repo
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: rag-pipeline
  description: RAG pipeline service for document Q&A
  annotations:
    github.com/project-slug: tmohanvamsi/cloud-native-lab
    backstage.io/techdocs-ref: dir:.
  tags:
    - python
    - ml
    - rag
spec:
  type: service
  lifecycle: production
  owner: ml-team
  system: smartops
  providesApis:
    - rag-api
```

## Lab 3 — Software Templates (golden paths)
```bash
# Open http://localhost:7007/create
# Templates let teams scaffold new services with a form
# Behind the scenes: template.yaml + Nunjucks → git commit + PR

# Example: "Create Python FastAPI service" template auto-generates:
# - Dockerfile
# - requirements.txt
# - tests/
# - catalog-info.yaml
# - GitHub Actions workflow
```

## Lab 4 — TechDocs (docs-as-code)
```bash
# TechDocs converts MkDocs markdown → HTML portal
# Add mkdocs.yml to your repo → Backstage renders it at /docs

cat <<EOF > mkdocs.yml
site_name: My Service
docs_dir: docs
nav:
  - Home: index.md
  - API: api.md
EOF
# annotate catalog-info.yaml with: backstage.io/techdocs-ref: dir:.
```

## Key Concepts
- Backstage = Meta-framework, not a SaaS — you self-host and customize
- Catalog = service registry — every team registers their services
- Templates = golden paths — standardized service creation
- Plugins = extend Backstage (500+ community plugins: Kubernetes, PagerDuty, etc.)
- Entity kinds: Component, API, System, Domain, Group, User, Resource
