#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ftplib
import gzip
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BV_BRC_FTP_HOST = "ftp.bvbrc.org"
BV_BRC_FTP_DIR = "/genomes"
BV_BRC_API_GENOME_QUERY = (
    "https://www.bv-brc.org/api/genome/"
    "?eq(genome_id,{genome_id})&select(assembly_accession)"
)
NCBI_DATASETS_DOWNLOAD = (
    "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{assembly_accession}"
    "/download?include_annotation_type=GENOME_FASTA"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download FASTA files for genome IDs and convert them to AMR TSV files "
            "using AMRFinderPlus."
        )
    )
    parser.add_argument(
        "--genome-ids-file",
        type=Path,
        default=Path("data/interim/genome_ids.txt"),
        help="Text file with one genome ID per line.",
    )
    parser.add_argument(
        "--amr-results-dir",
        type=Path,
        default=Path("amr_results"),
        help="Destination directory for final TSV files.",
    )
    parser.add_argument(
        "--fasta-cache-dir",
        type=Path,
        default=Path("fasta_to_tsv_pipeline/fasta_cache"),
        help="Directory for cached downloaded FASTA files.",
    )
    parser.add_argument(
        "--api-url-template",
        default="",
        help=(
            "Optional FASTA API URL template containing {genome_id}, e.g. "
            "'https://example.org/genomes/{genome_id}.fna'."
        ),
    )
    parser.add_argument(
        "--amrfinder-bin",
        default="amrfinder",
        help="AMRFinderPlus executable name/path.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Threads passed to AMRFinderPlus.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing TSV outputs.",
    )
    parser.add_argument(
        "--keep-fasta",
        action="store_true",
        help="Keep downloaded FASTA files in cache. If omitted, cache is cleaned after conversion.",
    )
    return parser.parse_args()


def read_genome_ids(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Genome ID file not found: {path}")

    genome_ids: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        gid = raw.strip()
        if gid:
            genome_ids.append(gid)

    if not genome_ids:
        raise ValueError(f"No genome IDs found in: {path}")

    return genome_ids


def download_via_api(api_url_template: str, genome_id: str, out_path: Path) -> bool:
    if not api_url_template:
        return False

    url = api_url_template.format(genome_id=genome_id)
    try:
        with urlopen(url, timeout=30) as response, out_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        return out_path.exists() and out_path.stat().st_size > 0
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        return False


def download_via_bvbrc_ftp(genome_id: str, out_path: Path) -> bool:
    candidates = [
        f"{genome_id}/{genome_id}.fna",
        f"{genome_id}/{genome_id}.fa",
        f"{genome_id}/{genome_id}.fasta",
        f"{genome_id}/{genome_id}.fna.gz",
        f"{genome_id}/{genome_id}.fa.gz",
        f"{genome_id}/{genome_id}.fasta.gz",
    ]

    try:
        with ftplib.FTP_TLS() as ftp:
            ftp.connect(BV_BRC_FTP_HOST, 21, timeout=30)
            ftp.login()
            ftp.prot_p()
            ftp.cwd(BV_BRC_FTP_DIR)

            for remote_path in candidates:
                tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
                try:
                    with tmp_path.open("wb") as handle:
                        ftp.retrbinary(f"RETR {remote_path}", handle.write)

                    if tmp_path.stat().st_size == 0:
                        tmp_path.unlink(missing_ok=True)
                        continue

                    if remote_path.endswith(".gz"):
                        with gzip.open(tmp_path, "rb") as gz_in, out_path.open("wb") as fasta_out:
                            shutil.copyfileobj(gz_in, fasta_out)
                        tmp_path.unlink(missing_ok=True)
                    else:
                        tmp_path.replace(out_path)

                    return out_path.exists() and out_path.stat().st_size > 0
                except ftplib.all_errors:
                    tmp_path.unlink(missing_ok=True)
                    continue
                except OSError:
                    tmp_path.unlink(missing_ok=True)
                    continue
    except ftplib.all_errors:
        return False

    return False


def ensure_fasta(genome_id: str, cache_dir: Path, api_url_template: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    fasta_path = cache_dir / f"{genome_id}.fna"

    if fasta_path.exists() and fasta_path.stat().st_size > 0:
        return fasta_path

    ok = download_via_api(api_url_template, genome_id, fasta_path)
    if not ok:
        ok = download_via_bvbrc_ftp(genome_id, fasta_path)
    if not ok:
        ok = download_via_bvbrc_api_ncbi(genome_id, fasta_path)

    if not ok:
        raise RuntimeError(f"Failed to download FASTA for genome ID: {genome_id}")

    return fasta_path


def download_via_bvbrc_api_ncbi(genome_id: str, out_path: Path) -> bool:
    try:
        request = Request(
            BV_BRC_API_GENOME_QUERY.format(genome_id=genome_id),
            headers={"Accept": "application/json"},
        )
        req = urlopen(request, timeout=30)
        payload = req.read()
        meta = json.loads(payload.decode("utf-8"))
        if isinstance(meta, list) and meta:
            meta = meta[0]
        if not isinstance(meta, dict):
            return False
        assembly_accession = str(meta.get("assembly_accession", "")).strip()
        if not assembly_accession:
            return False
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return False

    url = NCBI_DATASETS_DOWNLOAD.format(assembly_accession=assembly_accession)
    tmp_zip_path: Path | None = None
    tmp_extract_dir: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmpf:
            tmp_zip_path = Path(tmpf.name)
            with urlopen(url, timeout=120) as response:
                shutil.copyfileobj(response, tmpf)

        if tmp_zip_path.stat().st_size == 0:
            return False

        tmp_extract_dir = Path(tempfile.mkdtemp(prefix="ncbi_ds_"))
        with zipfile.ZipFile(tmp_zip_path, "r") as zf:
            zf.extractall(tmp_extract_dir)

        fna_candidates = list(tmp_extract_dir.rglob("*.fna"))
        if not fna_candidates:
            return False

        # Choose the largest FASTA if multiple are present.
        chosen = max(fna_candidates, key=lambda p: p.stat().st_size)
        shutil.copyfile(chosen, out_path)
        return out_path.exists() and out_path.stat().st_size > 0
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, zipfile.BadZipFile):
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        return False
    finally:
        if tmp_zip_path and tmp_zip_path.exists():
            tmp_zip_path.unlink(missing_ok=True)
        if tmp_extract_dir and tmp_extract_dir.exists():
            shutil.rmtree(tmp_extract_dir, ignore_errors=True)


def run_amrfinder(amrfinder_bin: str, fasta_path: Path, out_tsv: Path, threads: int) -> None:
    cmd = [
        amrfinder_bin,
        "-n",
        str(fasta_path),
        "-o",
        str(out_tsv),
        "--threads",
        str(threads),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "(no stderr)"
        stdout = result.stdout.strip() or "(no stdout)"
        raise RuntimeError(
            f"AMRFinderPlus failed for {fasta_path.name}\n"
            f"Command: {' '.join(cmd)}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )


def main() -> int:
    args = parse_args()

    if shutil.which(args.amrfinder_bin) is None:
        print(
            "ERROR: AMRFinderPlus executable not found. "
            "Install it and make sure it is available in PATH, or pass --amrfinder-bin.",
            file=sys.stderr,
        )
        return 2

    genome_ids = read_genome_ids(args.genome_ids_file)
    args.amr_results_dir.mkdir(parents=True, exist_ok=True)

    successes = 0
    failures: list[str] = []

    print(f"Genome IDs to process: {len(genome_ids)}")
    for i, genome_id in enumerate(genome_ids, start=1):
        out_tsv = args.amr_results_dir / f"{genome_id}.tsv"
        if out_tsv.exists() and not args.overwrite:
            print(f"[{i}/{len(genome_ids)}] {genome_id}: TSV exists, skipping")
            successes += 1
            continue

        try:
            fasta_path = ensure_fasta(genome_id, args.fasta_cache_dir, args.api_url_template)
            run_amrfinder(args.amrfinder_bin, fasta_path, out_tsv, args.threads)

            if not args.keep_fasta:
                fasta_path.unlink(missing_ok=True)

            print(f"[{i}/{len(genome_ids)}] {genome_id}: wrote {out_tsv}")
            successes += 1
        except Exception as exc:
            failures.append(f"{genome_id}: {exc}")
            print(f"[{i}/{len(genome_ids)}] {genome_id}: FAILED ({exc})", file=sys.stderr)

    print("\nSummary")
    print(f"  Success: {successes}")
    print(f"  Failed: {len(failures)}")

    if failures:
        fail_log = args.amr_results_dir / "download_convert_failures.log"
        fail_log.write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"  Failure log: {fail_log}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
