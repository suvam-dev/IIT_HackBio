# Quick Reference

This file is the shortest operational guide for running and presenting the project.

## Start The Demo

From repo root:

```bash
python3 backend/server.py
```

Open:

```text
http://127.0.0.1:8000/frontend/
```

## Do Not Do This

Do not run:

```bash
python3 frontend/app.js
```

`app.js` is browser JavaScript, not a Python script.

## Best Demo Sequence

1. Open the frontend.
2. Show the table loaded from `data/processed/submission.csv`.
3. Search a known genome ID.
4. Click `Predict` for live inference.
5. Upload a TSV and click `Predict From TSV`.
6. Click `Download TSV` to show FASTA-to-TSV preparation.
7. Show graphs in `reports/graphs/`.

## Good Genome IDs To Try

- `562.100058`
- `562.28997`

## Key Paths

- Raw input dataset: `data/raw/data.csv`
- Cleaned dataset: `data/processed/refined_data.csv`
- Final submission: `data/processed/submission.csv`
- AMR TSV inputs: `amr_results/`
- Model bundles: `models/`
- Graphs: `reports/graphs/`
- FASTA cache: `fasta_to_tsv_pipeline/fasta_cache/`
- Local AMRFinder database: `amrfinder_db/latest`

## Notebook Dependency Map

| Notebook | Reads | Writes |
|---|---|---|
| `01_Data_Loading_and_Exploration.ipynb` | `../data/raw/data.csv` | notebook outputs |
| `02_Data_Preprocessing.ipynb` | `../data/raw/data.csv` | `../data/processed/refined_data.csv` |
| `03_Data_Sampling_and_Balancing.ipynb` | `../data/processed/refined_data.csv` | `../data/interim/genome_ids*.txt` |
| `04_Feature_Engineering.ipynb` | `../data/processed/refined_data.csv`, `../amr_results/` | `../data/processed/amr_features.csv`, `../data/features/*.csv` |
| `05_Model_Training.ipynb` | processed/features data | `../models/*.pkl`, `../data/processed/model_training_summary.csv` |
| `06_Model_Evaluation_and_ROC_Analysis.ipynb` | `../models/*.pkl`, `../data/features/*.csv` | notebook outputs |
| `07_Final_Predictions_and_Submission_Fixed.ipynb` | `../models/*.pkl`, `../amr_results/` | `../data/processed/final_predictions_long.csv`, `../data/processed/submission.csv` |
| `08_Graph_Gallery.ipynb` | processed data and features | `../reports/graphs/*.png` |

## Fast Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `SyntaxError` from `python3 app.js` | wrong runtime | run `python3 backend/server.py` instead |
| Backend says `joblib` missing | dependencies not installed | `pip install -r backend-requirements.txt` |
| Predict fails | no usable TSV or conversion path | try a genome with existing TSV or upload a TSV |
| FASTA conversion fails | AMRFinder DB path issue | point `AMRFINDER_DB_DIR` to `amrfinder_db/latest` |
| Submission table missing | frontend cannot load CSV | verify `data/processed/submission.csv` exists |

## Judge One-Liners

- "This view shows our final batch predictions across genomes and antibiotics."
- "The live predictor uses AMRFinder gene evidence, not just a precomputed table row."
- "If a TSV is missing, the system can build one from FASTA using AMRFinderPlus."
- "The notebooks cover the full pipeline from raw data through model evaluation and deployment artifacts."
