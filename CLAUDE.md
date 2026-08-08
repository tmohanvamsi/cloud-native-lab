# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Cloud Native Lab** is a hands-on educational platform covering 11 CNCF certifications (LFCS, CCA, CAPA, CGOA, CBA, OTCA, PCA, ICA, KCA, CNPE, CNPA). This CLAUDE.md focuses on the **MLOps pipeline** component.

The MLOps subsystem (`mlops/` directory) demonstrates a complete machine learning workflow:
- **Data pipeline**: Iris dataset preparation and train/test split
- **ML training**: Random Forest classifier managed by DVC
- **Model serving**: FastAPI REST API for predictions
- **Containerization**: Docker image for K8s deployment
- **Agents**: Optional AI-powered DevOps agents (Ollama, CrewAI)

## Quick Start

### Environment Setup
```bash
cd cloud-native-lab/mlops

# Install dependencies
pip install -r requirements.txt

# Install DVC (if not already installed)
pip install dvc
```

Each subsystem has its **own** `requirements.txt` (they are not unified): `mlops/requirements.txt` (ML pipeline), `mlops/agents/requirements.txt` (ollama, crewai), `mlops/aiops/requirements.txt` (scikit-learn + ollama), `mlops/ai-tools/requirements.txt` (ollama only). Install the one matching what you're running.

Everything under `agents/`, `ai-tools/`, and `aiops/` calls a **local Ollama server** (`llama3.2` model, `http://localhost:11434`) — start it first with `ollama serve` and `ollama pull llama3.2`, or scripts will fail to connect.

### Linting
```bash
ruff check mlops/ --ignore E501    # matches CI (lint:ruff stage in .gitlab-ci.yml)
```

### Running the ML Pipeline

```bash
# Run entire pipeline (prepare → train → evaluate)
dvc repro dvc.yaml

# Run specific stage
dvc repro dvc.yaml -s prepare    # Prepare data only
dvc repro dvc.yaml -s train      # Train model only
dvc repro dvc.yaml -s evaluate   # Evaluate model only

# View latest metrics
dvc metrics show
```

### Running the Model Server

```bash
# Serve model via FastAPI (port 8080)
uvicorn serve:app --host 0.0.0.0 --port 8080 --reload

# Health check: GET http://localhost:8080/health
# Predict: POST http://localhost:8080/predict
#   Body: {"sepal_length_cm": 5.1, "sepal_width_cm": 3.5, "petal_length_cm": 1.4, "petal_width_cm": 0.2}
```

### Docker & Kubernetes

```bash
# Build Docker image (from repo root, not mlops/)
docker build -t iris-model:latest -f mlops/Dockerfile .

# Run locally
docker run -p 8080:8080 iris-model:latest

# Deploy to K8s (via ArgoCD or kubectl apply)
# Image reference: ghcr.io/yourusername/iris-model:latest
```

## Architecture

### Pipeline Stages (DVC-managed)

| Stage | Input | Output | Purpose |
|-------|-------|--------|---------|
| **prepare** | Iris dataset (sklearn) | `data/train.csv`, `data/test.csv` | Load & split dataset per params |
| **train** | `data/train.csv` | `models/model.pkl`, `metrics/train_metrics.json` | Train Random Forest classifier |
| **evaluate** | `models/model.pkl`, `data/test.csv` | `metrics/eval_metrics.json`, `metrics/confusion_matrix.csv` | Compute test accuracy & confusion matrix |

**Pipeline config**: `dvc.yaml` defines stages, dependencies, and outputs.  
**Parameters**: `params.yaml` controls dataset (Iris), target column (species), model hyperparameters (n_estimators, max_depth, test_size, random_state).

### Model Serving (FastAPI)

**File**: `serve.py`

Exposes:
- `GET /health` — Service status check
- `POST /predict` — Iris classification (sepal/petal measurements → species class + confidence)

Input schema: `Features` (Pydantic model) with 4 float fields (sepal/petal dimensions).  
Output: prediction (0/1/2), species name ("setosa"/"versicolor"/"virginica"), confidence score.

### Supporting Components

| Directory | Purpose |
|-----------|---------|
| `agents/` | AI-powered DevOps agents (Ollama, CrewAI); Docker k8s deployment configs |
| `aiops/` | AIOps examples (Ollama-based log analysis, CrewAI workflows) |
| `ai-tools/` | Prompt engineering & code generation (Dockerfile, K8s manifests, VPC configs) |

These three are a "Day 1–10" learning progression (see each file's module docstring, e.g. "Day 7 — Simple AI Agent from scratch"), not a single connected pipeline — each script runs standalone.

### Path Conventions (cwd matters)

Scripts assume different working directories, and running from the wrong one causes `FileNotFoundError`:
- **ML pipeline** (`prepare.py`, `train.py`, `evaluate.py`, `serve.py`, `dvc.yaml`): use relative paths (`data/train.csv`, `models/model.pkl`) and must be run with **cwd = `mlops/`** (or invoked via `dvc repro`, which handles this).
- **Agent/orchestration scripts** (`agents/day7_simple_agent.py`, `agents/day8_crewai_agent.py`, `ai-tools/generate_vpc.py`, etc.): hardcode paths like `"mlops/aiops/system_logs.txt"` and must be run with **cwd = repo root** (see each script's docstring `Usage:` line).
- **`aiops/*.py` log-analysis scripts** (`simple_log_analysis.py`, `aiops_log_analysis.py`, `aiops_ollama_explain.py`): resolve `system_logs.txt` via `os.path.dirname(__file__)`, so they work from any cwd.

## File Structure

```
mlops/
├── dvc.yaml                 # DVC pipeline definition (3 stages)
├── params.yaml              # Hyperparameters & dataset config
├── requirements.txt         # Python dependencies
├── Dockerfile              # Multi-stage Docker image
├── prepare.py              # Stage 1: data prep & split
├── train.py                # Stage 2: model training
├── evaluate.py             # Stage 3: model evaluation
├── serve.py                # FastAPI serving endpoint
├── data/                   # (generated) train.csv, test.csv
├── models/                 # (generated) model.pkl
├── metrics/                # (generated) train_metrics.json, eval_metrics.json, confusion_matrix.csv
├── agents/                 # AI agent implementations + k8s deployment
├── aiops/                  # Log analysis & automation examples
└── ai-tools/               # Code generation utilities
```

## Key Workflows

### Modifying Model Hyperparameters

1. Edit `params.yaml` (e.g., `model.n_estimators`, `model.max_depth`)
2. Run `dvc repro dvc.yaml` — DVC detects parameter changes and reruns affected stages
3. Check metrics: `dvc metrics show`

### Adding a New Pipeline Stage

1. Write Python script (e.g., `preprocess_advanced.py`)
2. Add stage to `dvc.yaml`:
   ```yaml
   new_stage:
     cmd: python preprocess_advanced.py
     deps: [preprocess_advanced.py, data/raw.csv]
     outs: [data/processed.csv]
   ```
3. Update dependent stages' `deps` field
4. Run: `dvc repro dvc.yaml`

### Deploying Model to Kubernetes

The iris-model manifests live at repo root under **`manifests/mlops/`** (`deployment.yaml`, `service.yaml`), not under `agents/k8s/` — that directory is the separate devops-agent's deployment (see `agents/agent_api.py`).

1. Build & push the Docker image (`mlops/Dockerfile`), or update `IMAGE_PLACEHOLDER` in `manifests/mlops/deployment.yaml`
2. Apply manifests (mirrors `.gitlab-ci.yml`'s `deploy:staging`/`deploy:production` jobs):
   ```bash
   sed -i "s|IMAGE_PLACEHOLDER|<image>|g" manifests/mlops/deployment.yaml
   kubectl apply -f manifests/mlops/
   ```
3. Access model via K8s service (e.g., `http://iris-model:8080/predict`)

The devops-agent (`agents/agent_api.py`) has its own image/build (`docker build -f mlops/agents/Dockerfile mlops/` — note the build **context is `mlops/`**, not repo root) and its own manifests at `agents/k8s/deployment.yaml`.

## Testing

The project does **not** include unit tests yet. To add tests:
- Use `pytest` for model training/evaluation functions
- Use `FastAPI.testclient` for server endpoint testing
- Add tests to a `tests/` directory or as test functions in each module

## Dependencies

- **scikit-learn 1.4.2** — RandomForestClassifier, metrics
- **pandas 2.2.2** — Data manipulation
- **numpy 1.26.4** — Numerical operations
- **dvc 3.50.1** — Pipeline orchestration
- **pyyaml 6.0.1** — Config parsing
- **fastapi 0.111.0** — REST API
- **uvicorn 0.29.0** — ASGI server
- **pydantic 2.7.1** — Data validation

Optional (for agents):
- ollama — Local LLM inference
- crewai — Multi-agent orchestration

## Debugging

**DVC pipeline fails:**
```bash
dvc repro dvc.yaml -v            # Verbose output
dvc dag                          # Visualize pipeline
cat dvc.lock                     # See last successful run
```

**Model serving issues:**
```bash
python serve.py                  # Check import errors
# Test endpoint: curl -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d '{...}'
```

**Docker build fails:**
- Check Dockerfile paths (COPY mlops/requirements.txt)
- Ensure models/model.pkl exists (run `dvc repro` first)
- `mlops/Dockerfile`'s `COPY models/model.pkl models/model.pkl` is relative to the build context. Running `dvc repro dvc.yaml` from inside `mlops/` (per the Quick Start above) produces `mlops/models/model.pkl`, but the documented build command uses repo root as context — so `models/model.pkl` won't be found there unless you first copy/symlink it to a repo-root-relative `models/model.pkl`, or adjust the COPY path.
- Verify Python 3.11 compatibility

## Performance Notes

- **Training time**: ~50ms (Iris dataset, 120 samples)
- **Inference time**: ~1ms per prediction
- **Model size**: ~50KB (pickled RandomForestClassifier)
- **Cold start**: ~2s (Python + model load)

For production, consider:
- Model quantization or ONNX export for faster inference
- Batch prediction endpoint
- Model versioning via DVC remote storage
- Caching predictions for repeated feature sets

## Related Documentation

- **README.md** (parent): Overview of all 11 CNCF certifications and quick-start commands
- **DVC docs**: https://dvc.org/
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Iris dataset**: https://scikit-learn.org/stable/datasets/toy_dataset.html#iris-dataset

## Future Enhancements

- [ ] Add integration tests (pytest + testclient)
- [ ] Implement model versioning via DVC remote
- [ ] Add monitoring/telemetry (Prometheus metrics endpoint)
- [ ] Expand agents (e.g., AutoML, hyperparameter tuning)
- [ ] GPU support for training (CUDA in Docker)
