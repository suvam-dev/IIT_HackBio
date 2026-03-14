# AMR Prediction Project

This repository is organized around a notebook-first antimicrobial resistance workflow, with a separate frontend/backend demo for prediction lookup and inference.

## Project Layout

```text
.
├── notebooks/
│   ├── 01_Data_Loading_and_Exploration.ipynb
│   ├── 02_Data_Preprocessing.ipynb
│   ├── 03_Data_Sampling_and_Balancing.ipynb
│   ├── 04_Feature_Engineering.ipynb
│   ├── 05_Model_Training.ipynb
│   ├── 06_Model_Evaluation_and_ROC_Analysis.ipynb
│   ├── 07_Final_Predictions_and_Submission_Fixed.ipynb
│   └── 08_Graph_Gallery.ipynb
├── data/
│   ├── raw/
│   │   └── data.csv
│   ├── interim/
│   │   ├── genome_ids.txt
│   │   └── genome_ids_600.txt
│   ├── features/
│   │   ├── ciprofloxacin_df.csv
│   │   ├── gentamicin_df.csv
│   │   └── meropenem_df.csv
│   └── processed/
│       ├── amr_features.csv
│       ├── refined_data.csv
│       ├── final_predictions_long.csv
│       ├── submission.csv
│       └── model_training_summary.csv
├── models/
│   ├── ciprofloxacin_model_bundle.pkl
│   ├── gentamicin_model_bundle.pkl
│   └── meropenem_model_bundle.pkl
├── amr_results/
├── reports/
│   └── graphs/
├── scripts/
├── backend/
├── fasta_to_tsv_pipeline/
└── frontend/
```

## Notebook Flow

Run the notebooks from the `notebooks/` directory in numeric order.

1. `01_Data_Loading_and_Exploration.ipynb`
   Reads `../data/raw/data.csv`
2. `02_Data_Preprocessing.ipynb`
   Writes `../data/processed/refined_data.csv`
3. `03_Data_Sampling_and_Balancing.ipynb`
   Writes `../data/interim/genome_ids*.txt`
4. `04_Feature_Engineering.ipynb`
   Reads `../amr_results/` and writes feature tables to `../data/features/`
5. `05_Model_Training.ipynb`
   Reads processed/features data and writes model bundles to `../models/`
6. `06_Model_Evaluation_and_ROC_Analysis.ipynb`
   Reads `../models/` and `../data/features/`
7. `07_Final_Predictions_and_Submission_Fixed.ipynb`
   Writes `../data/processed/final_predictions_long.csv` and `../data/processed/submission.csv`
8. `08_Graph_Gallery.ipynb`
   Saves figures to `../reports/graphs/`

## Frontend and Backend

The web app is kept separate from the notebook layout:

- frontend assets: `frontend/`
- backend inference server: `backend/`
- AMR TSV inputs for inference: `amr_results/`

To run the integrated app:

```bash
.venv/bin/python backend/server.py
```

Then open:

```text
http://localhost:8000/frontend/
```

## Required Python Packages

For the notebooks:

```text
pandas
numpy
scikit-learn
xgboost
matplotlib
seaborn
joblib
```

For the backend:

```bash
.venv/bin/pip install -r backend-requirements.txt
```

## FASTA to TSV Pipeline

Use the helper script in `fasta_to_tsv_pipeline/` to:

1. Read genome IDs
2. Download FASTA files (API template or BV-BRC FTPS fallback)
3. Run AMRFinderPlus
4. Save TSV outputs into `amr_results/`

Install AMRFinderPlus once:

```bash
conda create -y -n amrfix -c conda-forge -c bioconda ncbi-amrfinderplus
```

Run from repo root (single-line command):

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py --genome-ids-file data/interim/genome_ids.txt --amr-results-dir amr_results --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

## Notes

- Notebook paths have been normalized to the new folder structure.
- `amr_results/` remains at repo root because it is shared by the notebook pipeline and backend inference workflow.
- Generated graphs are stored under `reports/graphs/` instead of cluttering the repo root.
