# FOWT Dynamic Power Cable — ML Surrogate Models

Machine learning surrogate models for predicting fatigue damage and dynamic response of FOWT (Floating Offshore Wind Turbine) dynamic power cables. Work in progress.

## 概要（日本語）

浮体式洋上風力発電機（FOWT）動力電源ケーブルの疲労・動的応答を予測する機械学習サロゲートモデルの研究リポジトリ。継続開発中。

## Current work

| Script | Description |
|---|---|
| `code/01_wind_data_eda.py` | Wind SCADA EDA (Kaggle T1.csv) |
| `code/02_xgboost_real_SCADA.py` | XGBoost on Kaggle SCADA — predict power (R² ≈ 0.96) |
| `code/03_xgboost_hs_ndbc.py` | XGBoost on NDBC 46268 waves+ADCP — predict Hs (R² ≈ 0.76) |
| `code/04_xgboost_hs_windwave.py` | XGBoost on NDBC 46028 wind — predict Hs (R² ≈ 0.66) |

These real-data models are a warm-up: the same pipeline will later be trained on OrcaFlex fatigue output. More scripts will be added as work progresses — see [`LOG.md`](./LOG.md).

## Seminars

| Date | Topic |
|---|---|
| 2026-06-05 | Cable review paper + first EDA |
| 2026-07-09 | Three cable papers (method / configuration / reference model) + first XGBoost model |

## Repository Layout

```
.
├── code/             # Python scripts and notebooks
├── notes/
│   ├── papers/       # Paper reading notes
│   └── learning/     # Self-study notes
├── figures/          # Visual outputs (one subdir per analysis)
├── seminars/         # Group-meeting deliverables (<date>_<topic>/)
├── _local/           # Local-only, gitignored (PDFs, raw data)
└── LOG.md            # Progress log
```

See [`WORKFLOW.md`](./WORKFLOW.md) for repo conventions.
