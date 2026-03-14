# Frontend Demo Guide

This frontend is the judge-facing interface for the AMR prediction system. It is designed to show both prepared results and live backend inference.

## What The Frontend Shows

The page combines two views:

- a results dashboard driven by `data/processed/submission.csv`
- a live genome predictor driven by the backend API

The dashboard includes:

- summary stats
- searchable prediction table
- genome lookup field
- buttons for live prediction and TSV preparation
- TSV upload for direct inference

## How It Works

The frontend itself is static HTML, CSS, and JavaScript:

- [index.html](/Users/suvanghosh/IIT_HackBio-1/frontend/index.html)
- [styles.css](/Users/suvanghosh/IIT_HackBio-1/frontend/styles.css)
- [app.js](/Users/suvanghosh/IIT_HackBio-1/frontend/app.js)

It is served by the Python backend, which also exposes the API used for live inference.

## How To Run

From the repository root:

```bash
python3 backend/server.py
```

Then open:

```text
http://127.0.0.1:8000/frontend/
```

Do not run:

```bash
python3 frontend/app.js
```

That file is JavaScript and must run in the browser.

## Frontend Features

### 1. Default table view

When the page loads, it attempts to read:

```text
data/processed/submission.csv
```

If the CSV cannot be fetched, it falls back to bundled submission data in `frontend/submission-data.js`.

### 2. Search and filter

Users can search by `Genome ID` to narrow down the displayed rows.

### 3. Local prediction lookup

If the selected genome exists in the loaded submission file, the page can display the stored prediction immediately.

### 4. Live backend prediction

When the user clicks `Predict`, the frontend calls:

```text
/api/predict?genome_id=<id>
```

The backend then:

- looks for an existing local TSV
- tries a remote TSV download
- falls back to FASTA download and conversion if needed
- extracts gene evidence
- runs the trained models

### 5. Download TSV

When the user clicks `Download TSV`, the frontend calls:

```text
/api/download-genome?genome_id=<id>
```

This prepares `amr_results/<genome_id>.tsv` if possible.

The source may be:

- `local`
- `downloaded`
- `converted`

### 6. Predict from uploaded TSV

The user can select any AMRFinder TSV and click `Predict From TSV`.

The frontend sends:

- `genome_id`
- `source_name`
- `tsv_text`

to:

```text
/api/predict-upload
```

This is useful in a demo because it proves the model can consume external TSV evidence directly.

## Judge Demo Walkthrough

A reliable presentation sequence:

1. Open the app and show the loaded table.
2. Search for a known genome such as `562.100058`.
3. Explain the predicted resistance labels and probabilities.
4. Click `Predict` for a genome that has a TSV in `amr_results/`.
5. Upload a TSV from `amr_results/` and show that prediction can be recomputed directly from gene evidence.
6. Use `Download TSV` to show the system can prepare a new TSV when one is missing locally.

## Best Demo Talking Points

- "The table is our prepared batch output, but the right-hand interaction path is live inference."
- "The backend is not simply returning a cached label; it reads AMR gene evidence from a TSV and reconstructs the feature vector used during training."
- "If a TSV is missing, the system can generate one from FASTA using AMRFinderPlus."

## Recommended Files To Keep Ready

Keep these ready before the demo:

- `data/processed/submission.csv`
- one known-good TSV from `amr_results/`
- one genome ID that already works with `Predict`
- one genome ID you can use with `Download TSV`

## Common Problems

### Blank page or failed load

Check that:

- `backend/server.py` is running
- you opened `http://127.0.0.1:8000/frontend/`
- the backend is serving static files successfully

### `Predict` falls back to submission data

This usually means:

- backend dependencies are missing
- no valid TSV was available
- FASTA conversion could not be completed

### Uploaded TSV fails

Check that:

- the file is tab-separated
- it includes a gene symbol column such as `Gene symbol`

## Files Relevant To Frontend Demo

- [index.html](/Users/suvanghosh/IIT_HackBio-1/frontend/index.html)
- [app.js](/Users/suvanghosh/IIT_HackBio-1/frontend/app.js)
- [styles.css](/Users/suvanghosh/IIT_HackBio-1/frontend/styles.css)
- [server.py](/Users/suvanghosh/IIT_HackBio-1/backend/server.py)
- [inference.py](/Users/suvanghosh/IIT_HackBio-1/backend/inference.py)
