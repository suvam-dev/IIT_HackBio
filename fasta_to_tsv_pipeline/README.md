# FASTA -> TSV Pipeline

This folder contains a CLI script that:

1. Reads genome IDs from a text file.
2. Downloads FASTA files using this fallback order:
   - custom API URL template (if provided)
   - BV-BRC FTPS
   - BV-BRC genome API -> NCBI Datasets genome FASTA download
3. Runs AMRFinderPlus to generate TSV outputs.
4. Saves TSVs to `amr_results/` as `<genome_id>.tsv`.

## Script

- `download_and_convert.py`

## Prerequisites

- Python 3.10+
- AMRFinderPlus installed and available in `PATH` (or pass `--amrfinder-bin`)
- AMRFinder database configured (per AMRFinderPlus install docs)

## Example usage

Install AMRFinderPlus first:

```bash
conda create -y -n amrfix -c conda-forge -c bioconda ncbi-amrfinderplus
```

From repo root, run as one line:

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py --genome-ids-file data/interim/genome_ids.txt --amr-results-dir amr_results --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

With an HTTP API template for FASTA download:

```bash
conda run -n amrfix python3 fasta_to_tsv_pipeline/download_and_convert.py --genome-ids-file data/interim/genome_ids.txt --api-url-template "https://your-api.example/genomes/{genome_id}.fna" --amr-results-dir amr_results --amrfinder-bin /Users/suvanghosh/miniconda3/envs/amrfix/bin/amrfinder
```

## Notes

- Existing TSV files are skipped by default. Use `--overwrite` to regenerate.
- Failures are logged to `amr_results/download_convert_failures.log`.
- FASTA files are cached in `fasta_to_tsv_pipeline/fasta_cache/` during processing.
- Add `--keep-fasta` if you want to keep cached FASTA files after conversion.
