# AMR Prediction Platform

This repository contains an antimicrobial resistance prediction workflow for bacterial genomes. It combines:

- a notebook-based data science pipeline for data cleaning, feature engineering, model training, evaluation, and reporting
- a FASTA to TSV conversion pipeline using AMRFinderPlus
- a lightweight backend for genome-level inference
- a browser-based frontend for demonstration and judge-facing presentation

The current system predicts resistance for:

- Ciprofloxacin
- Gentamicin
- Meropenem

## What The Project Does

At a high level, the project takes genome-level AMR evidence and predicts whether a genome is resistant or susceptible to key antibiotics.

There are two working modes:

1. Offline pipeline mode
   Use the notebooks to clean the dataset, build features from AMRFinder outputs, train models, evaluate performance, and generate final submission files.

2. Live demo mode
   Use the backend and frontend to:
   - browse prediction results from the prepared submission file
   - enter a genome ID and run live prediction from an existing TSV
   - generate a TSV from FASTA when a TSV does not already exist
   - upload a TSV directly and run inference from it

## Repository Structure

```text
.
├── amr_results/                  # Genome-level AMRFinder TSV files used by notebooks and backend
├── amrfinder_db/                 # Repo-local AMRFinder database bootstrap used by FASTA->TSV conversion
├── backend/                      # Inference server
├── data/
│   ├── raw/                      # Original dataset
│   ├── interim/                  # Intermediate files such as sampled genome ID lists
│   ├── features/                 # Antibiotic-specific feature tables
│   └── processed/                # Cleaned data, long predictions, final submission
├── fasta_to_tsv_pipeline/        # FASTA download + conversion utilities
├── frontend/                     # Demo UI
├── models/                       # Trained model bundles
├── notebooks/                    # Numbered notebook pipeline
├── reports/graphs/               # Exported charts for presentation
└── QUICK_REFERENCE.md            # Fast operational guide
```

## End-To-End Workflow

The project is organized as a staged workflow:

1. Load and inspect the source dataset
2. Clean and refine the tabular AMR labels
3. Select or sample genome IDs
4. Generate AMRFinder outputs in `amr_results/`
5. Build gene-presence features from those TSVs
6. Train per-antibiotic models
7. Evaluate the trained models
8. Generate final prediction outputs for reporting/demo use
9. Serve the backend and frontend for interactive demonstration

## Notebook Pipeline

Run the notebooks from the `notebooks/` directory in numeric order.

### 1. `01_Data_Loading_and_Exploration.ipynb`

Purpose:
- initial inspection of the raw source dataset
- sanity checks on schema and label distribution

Reads:
- `../data/raw/data.csv`

Writes:
- notebook outputs only

### 2. `02_Data_Preprocessing.ipynb`

Purpose:
- clean the raw data
- normalize relevant columns
- produce a refined dataset for downstream work

Reads:
- `../data/raw/data.csv`

Writes:
- `../data/processed/refined_data.csv`

### 3. `03_Data_Sampling_and_Balancing.ipynb`

Purpose:
- select and/or balance genome IDs for downstream processing

Reads:
- `../data/processed/refined_data.csv`

Writes:
- `../data/interim/genome_ids.txt`
- `../data/interim/genome_ids_600.txt`

### 4. `04_Feature_Engineering.ipynb`

Purpose:
- parse AMRFinder outputs from `amr_results/`
- convert detected genes into binary feature vectors

Reads:
- `../data/processed/refined_data.csv`
- `../amr_results/`

Writes:
- `../data/processed/amr_features.csv`
- `../data/features/ciprofloxacin_df.csv`
- `../data/features/gentamicin_df.csv`
- `../data/features/meropenem_df.csv`

### 5. `05_Model_Training.ipynb`

Purpose:
- train per-antibiotic prediction models
- serialize model bundles for backend use

Reads:
- processed datasets
- feature tables

Writes:
- `../models/ciprofloxacin_model_bundle.pkl`
- `../models/gentamicin_model_bundle.pkl`
- `../models/meropenem_model_bundle.pkl`
- `../data/processed/model_training_summary.csv`

### 6. `06_Model_Evaluation_and_ROC_Analysis.ipynb`

Purpose:
- evaluate model behavior
- inspect ROC and related metrics

Reads:
- `../models/`
- `../data/features/`

Writes:
- notebook outputs and evaluation visuals

### 7. `07_Final_Predictions_and_Submission_Fixed.ipynb`

Purpose:
- generate final prediction outputs for reporting and demo

Writes:
- `../data/processed/final_predictions_long.csv`
- `../data/processed/submission.csv`

### 8. `08_Graph_Gallery.ipynb`

Purpose:
- create presentation-ready visual summaries

Writes:
- `../reports/graphs/*.png`

## Data And Model Artifacts

Important outputs you can show quickly:

- Final submission table: `data/processed/submission.csv`
- Long-format predictions: `data/processed/final_predictions_long.csv`
- Trained bundles: `models/*.pkl`
- Presentation graphs: `reports/graphs/*.png`
- AMRFinder genome evidence files: `amr_results/*.tsv`

## FASTA To TSV Conversion

The project includes a working FASTA to TSV path in `fasta_to_tsv_pipeline/`.

It can:

- read genome IDs from a file
- fetch a FASTA from multiple sources
- run AMRFinderPlus
- write `<genome_id>.tsv` into `amr_results/`

The backend now reuses this same logic when a user requests a genome that does not already have a local TSV.

Fallback order:

1. existing local TSV in `amr_results/`
2. remote TSV download from BV-BRC
3. FASTA download
4. FASTA to TSV conversion using AMRFinderPlus

## Backend And Frontend

The demo app has two layers:

- Backend: `backend/server.py`
- Frontend: `frontend/index.html` and `frontend/app.js`

The frontend provides:

- a searchable table using the prepared `submission.csv`
- genome ID lookup
- live backend prediction
- uploaded TSV inference
- TSV preparation from genome ID

The backend provides:

- `/api/health`
- `/api/predict`
- `/api/download-genome`
- `/api/predict-upload`

## Environment Setup

There are two runtime layers to consider.

### A. Python dependencies for notebooks and backend

Core packages used in this project:

- pandas
- numpy
- scikit-learn
- xgboost
- matplotlib
- seaborn
- joblib

Install backend packages with:

```bash
pip install -r backend-requirements.txt
```

If you use a virtual environment, activate it first.

### B. AMRFinderPlus for FASTA to TSV conversion

Install once with conda:

```bash
conda create -y -n amrfix -c conda-forge -c bioconda ncbi-amrfinderplus
```

This repo now also supports a repo-local AMRFinder database path at:

```text
amrfinder_db/latest
```

Useful environment variables:

- `AMRFINDER_BIN`
- `AMRFINDER_DB_DIR`
- `AMRFINDER_THREADS`
- `FASTA_API_URL_TEMPLATE`
- `KEEP_FASTA_CACHE`
- `AMRFINDER_SKIP_HMM_CHECK`

## How To Run The Demo

Run from the repository root:

```bash
python3 backend/server.py
```

Then open:

```text
http://127.0.0.1:8000/frontend/
```

Do not run `python3 frontend/app.js`. That file is JavaScript and is loaded by the browser.

## Recommended Judge Demo Flow

This is the cleanest order for a live presentation.

### Demo Goal

Show that the system is not just a static CSV viewer. It can:

- display final model outputs
- explain genome-level resistance calls
- use AMR gene evidence from TSV files
- generate a new TSV from FASTA when needed

### 5-Minute Demo Script

1. Start with the problem
   Explain that antimicrobial resistance prediction usually requires combining biological evidence with machine learning, and your system does both.

2. Show the prepared results table
   Open the web app and point to the searchable prediction table loaded from `submission.csv`.

3. Search a known genome ID
   Use a genome already present in the table to show immediate lookup and probability outputs.

4. Show live inference
   Enter a genome ID that has a local TSV in `amr_results/` and click `Predict`.
   Explain that this path uses gene features extracted from the AMRFinder output, not just a prewritten CSV row.

5. Show TSV upload
   Upload a TSV file from `amr_results/` and run `Predict From TSV`.
   Explain that the backend can accept external AMR evidence directly.

6. Show FASTA to TSV generation
   Use `Download TSV` for a genome that does not already have a local TSV but does have a FASTA path available.
   Explain that the system can construct the required AMR TSV on demand using AMRFinderPlus.

7. Close with the pipeline
   Show the notebook structure and the graphs in `reports/graphs/` to prove the project includes data preparation, modeling, evaluation, and delivery.

### Best Genomes To Use During Demo

For a stable live demo, prefer genomes that already have local artifacts.

Examples already present in this repo:

- `562.100058`
- `562.28997`

Before presenting, verify:

- the backend starts
- the page loads
- the selected genome IDs have working TSVs
- the uploaded TSV path works

### What To Say To Judges

Use concise, technical language:

- "This table shows the final batch prediction outputs produced by our trained models."
- "For live inference, the backend reads AMRFinder gene evidence and constructs the same feature representation used during model training."
- "If a TSV is missing, the system can fetch FASTA data and generate a TSV through AMRFinderPlus, so we are not limited to precomputed files."
- "The notebook pipeline covers the full lifecycle from raw data to model training, evaluation, and final deployment artifacts."

### Strong Demo Angles

If judges ask what is technically interesting, emphasize:

- end-to-end reproducibility from raw data to deployed inference
- biology-aware feature extraction from AMR gene calls
- separate per-antibiotic models
- interactive inference rather than a static notebook-only submission
- fallback from TSV lookup to FASTA conversion

## Troubleshooting

### `python3 frontend/app.js` gives `SyntaxError`

Cause:
- `app.js` is JavaScript, not Python

Fix:
- run `python3 backend/server.py`
- open the browser UI instead

### Backend says `Missing backend dependency 'joblib'`

Cause:
- backend Python environment is missing dependencies

Fix:

```bash
pip install -r backend-requirements.txt
```

### FASTA to TSV conversion fails with AMRFinder database errors

Cause:
- AMRFinder binary exists but its database is incomplete or misconfigured

Fix:
- point `AMRFINDER_DB_DIR` to `amrfinder_db/latest`
- confirm the selected AMRFinder binary is correct

### Genome prediction fails

Cause:
- no local TSV
- remote TSV unavailable
- FASTA retrieval unavailable
- conversion dependency missing

Fix:
- test with a genome that already has `amr_results/<genome_id>.tsv`
- or upload a TSV directly

## Presentation Checklist

Before the final demo, confirm all of the following:

- backend dependencies are installed
- `python3 backend/server.py` starts successfully
- `http://127.0.0.1:8000/frontend/` loads
- `submission.csv` renders in the table
- at least one genome ID works with `Predict`
- at least one TSV works with `Predict From TSV`
- at least one genome works with `Download TSV`
- the graphs in `reports/graphs/` are ready to show

## Related Docs

- [Frontend README](/Users/suvanghosh/IIT_HackBio-1/frontend/README.md)
- [FASTA Pipeline README](/Users/suvanghosh/IIT_HackBio-1/fasta_to_tsv_pipeline/README.md)
- [Quick Reference](/Users/suvanghosh/IIT_HackBio-1/QUICK_REFERENCE.md)
