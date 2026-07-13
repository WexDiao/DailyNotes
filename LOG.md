# Progress Log

Running log of meaningful sessions. Newest entry on top. One bullet per
thing that actually got *done* (commits, deliverables, decisions) — not
intentions.

For the why behind a session, look at the linked PR / commit / file.

---

## 2026-07-09 · Seminar 2 — cable papers + first XGBoost model

- 🎤 Delivered second group-meeting talk (16-slide English deck, ~8–10 min)
  → `seminars/2026-07-09_cable_papers_and_xgboost/`
    (slides, speech notes, two paired walkthrough docs)
- 📚 Three cable papers read in depth: B-9 Beier (fatigue method),
  B-4 Zhao (lazy- vs double-wave config), B-3 Janocha (open reference cables)
- 🛠 First real-data XGBoost models (warm-up before the OrcaFlex surrogate):
  `code/02_xgboost_real_SCADA.py` (power, R²≈0.96),
  `code/03_xgboost_hs_ndbc.py` (Hs, R²≈0.76),
  `code/04_xgboost_hs_windwave.py` (Hs from wind, R²≈0.66)
  → figures in `figures/xgboost_{scada,hs_ndbc,windwave}/` + `figures/cable_papers/`
- 🔧 Hardened `.gitignore`: global safety net (*.pdf, *.csv, *.txt, *.jpg, …)
  so raw data / literature / photos can't be committed even outside `_local/`
- 📌 Plan set: build OrcaFlex model (B-3 cable) → fatigue dataset (B-9 method)
  → train same XGBoost workflow on it

---

## 2026-06-05 · Repo restructure & rename

- 🔧 Flattened layout: 11 top-level entries → 7
  (`code/`, `notes/{papers,learning}/`, `figures/`, `seminars/`, `_local/`)
  → commit `3c937ad`
- 🌐 Renamed GitHub repo: `DailyNotes` → `fowt-cable-ai`; updated remote
  URL and push-script fallback strings → commits `904186c`, `1e669a8`
- 📝 Trimmed `README.md` to factual content only

---

## 2026-06-05 · Seminar delivered + first AI mini-project

- 🎤 Delivered group-meeting talk (9-slide English deck, ~5 min)
  → `seminars/2026-06-05_cable_review_and_eda/`
- 🛠 First AI mini-project complete: end-to-end EDA on Kaggle SCADA T1.csv
  → `code/01_wind_data_eda.py` (8 PNGs in `figures/eda_wind_scada/`)
- 📓 Code walkthrough doc written: `notes/learning/eda_code_walkthrough.md`
- 📓 Learning notes added:
  `notes/learning/python_data_stack_cheatsheet.md`,
  `notes/learning/dynamic_cable_basics.md`,
  `notes/learning/kaggle_scada_setup.md`
- 🗂 Added top-level `seminars/` folder for time-stamped talks
  (dates live in folder name, not in repo structure)
- 📌 Decided research focus: global-simulation + ML surrogate models
  for cable fatigue prediction

---

## How to use this file

- Add a new section at the top whenever you finish a meaningful chunk
- Date as H2 (`## YYYY-MM-DD · short title`)
- Bullets describe *what was completed*, link to file or commit
- Use emojis sparingly as visual anchors: 🎤 talks · 🛠 code · 📓 notes ·
  📌 decisions · 🐛 bugs fixed · 🔬 experiments
- Keep entries terse — the diffs are in git, this file is the index
