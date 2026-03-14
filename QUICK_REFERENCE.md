# Quick Reference

## Key Paths

- Raw input dataset: `data/raw/data.csv`
- Cleaned dataset: `data/processed/refined_data.csv`
- Gene feature tables: `data/features/*.csv`
- Model bundles: `models/*.pkl`
- Final predictions: `data/processed/submission.csv`
- Graph outputs: `reports/graphs/`
- Genome TSV inputs: `amr_results/`

## Notebook Dependencies

| Notebook | Reads | Writes |
|---|---|---|
| `01_Data_Loading_and_Exploration.ipynb` | `../data/raw/data.csv` | none |
| `02_Data_Preprocessing.ipynb` | `../data/raw/data.csv` | `../data/processed/refined_data.csv` |
| `03_Data_Sampling_and_Balancing.ipynb` | `../data/processed/refined_data.csv` | `../data/interim/genome_ids*.txt` |
| `04_Feature_Engineering.ipynb` | `../data/processed/refined_data.csv`, `../amr_results/` | `../data/processed/amr_features.csv`, `../data/features/*.csv` |
| `05_Model_Training.ipynb` | `../data/processed/refined_data.csv`, `../amr_results/` | `../models/*.pkl`, `../data/features/*.csv`, `../data/processed/model_training_summary.csv` |
| `06_Model_Evaluation_and_ROC_Analysis.ipynb` | `../models/*.pkl`, `../data/features/*.csv` | plots in notebook |
| `07_Final_Predictions_and_Submission_Fixed.ipynb` | `../models/*.pkl`, `../amr_results/` | `../data/processed/final_predictions_long.csv`, `../data/processed/submission.csv` |
| `08_Graph_Gallery.ipynb` | `../data/raw/`, `../data/processed/`, `../data/features/` | `../reports/graphs/*.png` |

## Common Issues

| Problem | Likely Cause | Fix |
|---|---|---|
| `data.csv not found` | Wrong working directory | Run notebooks from `notebooks/` |
| `refined_data.csv not found` | Notebook 2 not run yet | Run `02_Data_Preprocessing.ipynb` |
| No AMR TSV files found | `amr_results/` is empty | Add TSVs to `amr_results/` or use backend download/upload flow |
| Model bundle not found | Notebook 5 not run yet | Run `05_Model_Training.ipynb` |
| Submission file missing | Notebook 7 not run yet | Run `07_Final_Predictions_and_Submission_Fixed.ipynb` |

## Professional Layout Summary

- Notebook code lives in `notebooks/`
- Datasets live in `data/`
- Models live in `models/`
- Graphs live in `reports/graphs/`
- App code stays in `frontend/` and `backend/`
