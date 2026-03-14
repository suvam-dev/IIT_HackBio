# Frontend

Run the integrated frontend + backend server from repo root:

```bash
.venv/bin/python backend/server.py
```

Then open:

- `http://localhost:8000/frontend/`

Usage:

- Enter a `Genome ID` and click **Download TSV** to fetch and store the genome file in `amr_results/` from BV-BRC over FTPS when it is available.
- Enter a `Genome ID` and click **Predict** to run live model inference from `amr_results/<genome_id>.tsv`.
- If that file is missing, the backend now attempts to download a genome-specific file from BV-BRC and stores it in `amr_results/`.
- You can also choose a TSV file in the UI and click **Predict From TSV** to run inference directly from an uploaded genome file.
- The page still loads `submission.csv` for the table, stats, and fallback lookup behavior.
- If a genome ID has no matching TSV in `amr_results/`, the backend cannot generate a live prediction.
