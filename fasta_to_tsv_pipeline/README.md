# FASTA To TSV Pipeline

This folder contains the conversion logic that turns genome IDs or FASTA inputs into AMRFinder TSV outputs suitable for feature extraction and backend inference.

## Why This Pipeline Matters

The machine learning models in this repo do not consume raw FASTA directly. They consume gene-level evidence extracted from AMRFinder TSV outputs.

That means the pipeline from FASTA to TSV is a critical bridge between:

- genomic sequence data
- AMR gene detection
- model-ready binary gene features

## What The Script Does

The main script is:

- [download_and_convert.py](/Users/suvanghosh/IIT_HackBio-1/fasta_to_tsv_pipeline/download_and_convert.py)

Its responsibilities are:

1. read one or more genome IDs
2. obtain FASTA data
3. cache FASTA files locally
4. run AMRFinderPlus
5. write TSV outputs into `amr_results/`

## Download Fallback Order

For each genome ID, the pipeline tries:

1. custom HTTP API template, if provided
2. BV-BRC FTPS
3. BV-BRC API to resolve assembly accession, then NCBI Datasets genome FASTA download

## Output Location

By default, the generated output is:

```text
amr_results/<genome_id>.tsv
```

FASTA cache location:

```text
fasta_to_tsv_pipeline/fasta_cache/
```

## Backend Reuse

This is not just a standalone utility anymore.

The backend imports and reuses this conversion logic when:

- a genome is requested for prediction
- no local TSV exists
- no remote TSV can be downloaded

So this folder is directly part of the live demo path.

## Requirements

### Python

- Python 3.10+

### AMRFinderPlus

Install with:

```bash
conda create -y -n amrfix -c conda-forge -c bioconda ncbi-amrfinderplus
```

### AMRFinder Database

This repo supports a repo-local AMRFinder database at:

```text
amrfinder_db/latest
```

If needed, set:

```bash
export AMRFINDER_DB_DIR=/Users/suvanghosh/IIT_HackBio-1/amrfinder_db/latest
```

## CLI Usage

Run from the repository root.

Example:

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py \
  --genome-ids-file data/interim/genome_ids.txt \
  --amr-results-dir amr_results \
  --fasta-cache-dir fasta_to_tsv_pipeline/fasta_cache \
  --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

Single-genome example:

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py \
  --genome-ids-file data/interim/genome_ids_600.txt \
  --amr-results-dir amr_results \
  --fasta-cache-dir fasta_to_tsv_pipeline/fasta_cache \
  --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

Using a custom FASTA API template:

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py \
  --genome-ids-file data/interim/genome_ids.txt \
  --api-url-template "https://your-api.example/genomes/{genome_id}.fna" \
  --amr-results-dir amr_results \
  --fasta-cache-dir fasta_to_tsv_pipeline/fasta_cache \
  --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

## Environment Variables

The conversion path also respects these variables:

- `AMRFINDER_BIN`
- `AMRFINDER_DB_DIR`
- `AMRFINDER_THREADS`
- `FASTA_API_URL_TEMPLATE`
- `KEEP_FASTA_CACHE`
- `AMRFINDER_SKIP_HMM_CHECK`

### Current Recommended Values In This Repo

```bash
export AMRFINDER_BIN=/Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
export AMRFINDER_DB_DIR=/Users/suvanghosh/IIT_HackBio-1/amrfinder_db/latest
export AMRFINDER_SKIP_HMM_CHECK=1
```

## Generated Files

Typical outputs:

- `amr_results/<genome_id>.tsv`
- `amr_results/download_convert_failures.log`

Temporary and cache files:

- `fasta_to_tsv_pipeline/fasta_cache/*.fna`

## Judge Demo Relevance

If judges ask whether the system can handle new genomes rather than only precomputed TSVs, this pipeline is the answer.

You can explain it this way:

- "Our model expects AMR gene evidence, so we built a sequence-to-evidence conversion layer."
- "When a TSV does not already exist, the system can fetch FASTA and generate the AMRFinder TSV automatically."
- "That makes the platform more realistic than a static classifier on frozen inputs."

## Known Operational Notes

- Existing TSVs are skipped by default.
- Use `--overwrite` to regenerate outputs.
- Use `--keep-fasta` if you want to retain cached FASTA files after conversion.
- Download progress is printed for large transfers.
- In this repo, `AMRFINDER_SKIP_HMM_CHECK=1` is enabled by default in code because the local bootstrap path is designed around a working BLAST-backed flow.

## Common Failure Cases

### AMRFinder executable not found

Fix:
- install `ncbi-amrfinderplus`
- pass `--amrfinder-bin`
- or set `AMRFINDER_BIN`

### FASTA download fails

Possible causes:

- genome ID unavailable upstream
- network access unavailable
- FTPS endpoint unreachable

### AMRFinder database error

Fix:
- set `AMRFINDER_DB_DIR` explicitly
- use the repo-local `amrfinder_db/latest`

### Output TSV missing after run

Check:

- whether the genome ID was skipped because a TSV already existed
- whether `download_convert_failures.log` contains the real failure reason

## Suggested Pre-Demo Validation

Before presenting this feature:

- test one genome that already has a cached FASTA
- confirm it produces a TSV in `amr_results/`
- verify that the backend can subsequently use that TSV
