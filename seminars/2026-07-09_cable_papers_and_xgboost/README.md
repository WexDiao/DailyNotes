# Group Seminar · 2026-07-09 — Cable papers + first XGBoost model

Second progress report. Follows the 2026-06-05 review-paper talk.

## Contents

| File | What it is |
|---|---|
| `slides_en.pptx` | 16-slide English deck (~8–10 min) |
| `speech_notes.md` | Per-slide speaking script (English lines + Chinese fallback notes) |
| `walkthrough_papers.md` | Detailed walkthrough of the three cable papers (paired with slides) |
| `walkthrough_xgboost.md` | Detailed walkthrough of the data + XGBoost pipeline (paired with slides) |

## Part 1 · Three cable papers

Read in depth to assemble everything needed to build an own OrcaFlex fatigue model:

- **B-9 · Beier et al. (2023), JMSE** — the *method*: a 4-step fatigue workflow, no UFLEX required. Note: the simplified stress factors overshoot UFLEX under curvature (up to +218%).
- **B-4 · Zhao et al. (2021), AIP Advances** — the *configuration*: lazy-wave vs double-wave; double-wave keeps touch-down-point curvature ≤ lazy-wave across load cases.
- **B-3 · Janocha et al. (2024), Sustainability** — the *reference cable*: open 33/66/132 kV models + a UFLEX→OrcaFlex flow.

Method + configuration + reference cable = the inputs and procedure to build an OrcaFlex fatigue model, then train an ML surrogate on it.

## Part 2 · First real-data XGBoost model

Warm-up before the OrcaFlex surrogate — practice the full pipeline on real public data. Same workflow (clean → split → GridSearchCV → XGBoost → evaluate + explain) will be reused unchanged once the target becomes OrcaFlex fatigue damage.

| Script (in `../../code/`) | Data | Target | R² | Note |
|---|---|---|---|---|
| `02_xgboost_real_SCADA.py` | Kaggle wind-turbine SCADA | Power | 0.96 | Recovers the S-shaped power curve |
| `03_xgboost_hs_ndbc.py` | NDBC 46268 (waves + ADCP) | Hs | 0.76 | Wave period + current dominate |
| `04_xgboost_hs_windwave.py` | NDBC 46028 (Morro Bay CA lease area) | Hs from wind | 0.66 | Season + gust rank above instantaneous wind; residual is distant-storm swell |

Figures: `../../figures/xgboost_scada/`, `../../figures/xgboost_hs_ndbc/`, `../../figures/xgboost_windwave/`, and paper illustrations in `../../figures/cable_papers/`.

## Next steps

Build an OrcaFlex model using the B-3 reference cable → generate a fatigue dataset with the B-9 method → train the same XGBoost workflow on it.

> Data files (NDBC buoy `.txt`, Kaggle `T1.csv`) are not committed — they live in `_local/data/`. See `../../WORKFLOW.md`.
