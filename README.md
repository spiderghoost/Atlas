# ATLAS — Global Economic Intelligence Platform

Graduation project: an institution-grade web platform for **monitoring, analyzing, and deciding** on country economies, powered by a multi-agent AI system over a multi-source data warehouse anchored by the World Bank WDI. Full rationale, datasets, modules, and risks: see [PROJECT_PROPOSAL_MAP.md](PROJECT_PROPOSAL_MAP.md).

## Pillars

- **Monitor** — macro risk early warning, nowcasting/forecasting, food & energy security, watchlists + alerts.
- **Analyze** — debt sustainability, country intelligence briefs, peer benchmarking, development space.
- **Decide** — Shock & Resilience Studio (history-anchored scenario stress-testing), policy counterfactuals, ask-the-agent chat, PDF decision memos.

## Core modules (must ship)

1. Macro Risk & Early Warning
2. Nowcasting & Forecasting (GDP, inflation, poverty, food insecurity)
3. Food & Energy Security Monitor
4. Watchlists & Alert Engine
5. Debt Sustainability Analytics
6. Country Intelligence Briefs
7. Shock & Resilience Studio (final-phase showcase)
8. Ask-the-Agent Chat

## Setup

```bash
conda env create -f environment.yml
conda activate ds-grad-project
# optional: pip install -r requirements.txt
```

Pin exact versions after first successful install:

```bash
pip freeze > requirements.lock
```

## Layout

```
configs/     pipeline configuration (data paths, split policy, model params)
data/        raw/ (external, never committed) and processed/
notebooks/   EDA and analysis notebooks
results/     metric tables, XAI artifacts, figures (committed)
src/         pipeline modules: data, features, models, evaluate, pipeline, agent, api
```

## Reproducibility

- Deterministic pipeline: seed pinned in `configs/default.yaml`; all splits derived from source indices (leakage-safe by construction).
- Experiment tracking: MLflow (`mlruns/`); data versioning: DVC.
- Run: `python -m src.pipeline --config configs/default.yaml`
