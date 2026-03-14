from __future__ import annotations

import csv
import ftplib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
AMR_DIR = ROOT / "amr_results"
BV_BRC_FTP_HOST = "ftp.bvbrc.org"
BV_BRC_FTP_DIR = "/genomes"


class InferenceError(Exception):
    pass


@dataclass
class PredictionBundle:
    antibiotic: str
    model_name: str
    feature_cols: list[str]
    model: Any


class ModelPredictor:
    def __init__(self) -> None:
        try:
            import joblib  # type: ignore
        except ImportError as exc:
            raise InferenceError(
                "Missing backend dependency 'joblib'. Install backend-requirements.txt first."
            ) from exc

        self._joblib = joblib
        self._bundles = self._load_bundles()

    def _load_bundles(self) -> dict[str, PredictionBundle]:
        bundles: dict[str, PredictionBundle] = {}
        bundle_paths = {
            "ciprofloxacin": ROOT / "models" / "ciprofloxacin_model_bundle.pkl",
            "gentamicin": ROOT / "models" / "gentamicin_model_bundle.pkl",
            "meropenem": ROOT / "models" / "meropenem_model_bundle.pkl",
        }

        for antibiotic, path in bundle_paths.items():
            if not path.exists():
                raise InferenceError(f"Model bundle not found: {path.name}")

            try:
                bundle = self._joblib.load(path)
            except Exception as exc:  # pragma: no cover - depends on local ML runtime
                raise InferenceError(f"Failed to load model bundle {path.name}: {exc}") from exc

            bundles[antibiotic] = PredictionBundle(
                antibiotic=antibiotic,
                model_name=str(bundle.get("model_name", "unknown")),
                feature_cols=list(bundle.get("feature_cols", [])),
                model=bundle.get("model"),
            )

        return bundles

    def _genome_path(self, genome_id: str) -> tuple[Path, str]:
        safe_id = genome_id.strip()
        if not safe_id:
            raise InferenceError("Genome ID is required.")

        path, source = self.ensure_genome_file(safe_id)
        if not path.exists():
            raise InferenceError(f"No AMR TSV found for genome ID {safe_id}, and remote download failed.")
        return path, source

    def ensure_genome_file(self, genome_id: str) -> tuple[Path, str]:
        safe_id = genome_id.strip()
        if not safe_id:
            raise InferenceError("Genome ID is required.")

        for existing in (AMR_DIR / f"{safe_id}.tsv", AMR_DIR / f"{safe_id}.spgene.tab"):
            if existing.exists():
                return existing, "local"

        downloaded = self._download_remote_genome_file(safe_id)
        if downloaded is not None and downloaded.exists():
            return downloaded, "downloaded"

        raise InferenceError(f"No AMR TSV found for genome ID {safe_id}, and remote download failed.")

    def _download_remote_genome_file(self, genome_id: str) -> Path | None:
        AMR_DIR.mkdir(parents=True, exist_ok=True)

        remote_candidates = (
            (f"{genome_id}/{genome_id}.tsv", AMR_DIR / f"{genome_id}.tsv"),
            (f"{genome_id}/{genome_id}.spgene.tab", AMR_DIR / f"{genome_id}.spgene.tab"),
        )

        try:
            with ftplib.FTP_TLS() as ftp:
                ftp.connect(BV_BRC_FTP_HOST, 21, timeout=20)
                ftp.login()
                ftp.prot_p()
                ftp.cwd(BV_BRC_FTP_DIR)

                for remote_path, destination in remote_candidates:
                    try:
                        with destination.open("wb") as handle:
                            ftp.retrbinary(f"RETR {remote_path}", handle.write)
                        if destination.stat().st_size > 0:
                            return destination
                    except ftplib.all_errors:
                        if destination.exists():
                            destination.unlink(missing_ok=True)
                        continue
        except ftplib.all_errors:
            return None

        return None

    def _extract_genes_from_reader(self, reader: csv.DictReader, source_name: str) -> set[str]:
        genes: set[str] = set()
        gene_column = None

        if reader.fieldnames:
            for candidate in ("Gene symbol", "gene", "gene_symbol", "NAME", "Gene", "property", "function"):
                if candidate in reader.fieldnames:
                    gene_column = candidate
                    break

        if not gene_column:
            raise InferenceError(f"No gene symbol column found in {source_name}.")

        for row in reader:
            gene = (row.get(gene_column) or "").strip()
            if gene:
                genes.add(gene)

        if not genes:
            raise InferenceError(f"No gene symbols extracted from {source_name}.")

        return genes

    def _extract_genes(self, genome_id: str) -> tuple[set[str], str, str]:
        path, source = self._genome_path(genome_id)

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            genes = self._extract_genes_from_reader(reader, path.name)

        return genes, source, path.name

    def _feature_vector(self, genes: set[str], feature_cols: list[str]) -> list[int]:
        present = {f"gene_{gene}" for gene in genes}
        return [1 if feature in present else 0 for feature in feature_cols]

    def predict(self, genome_id: str) -> dict[str, Any]:
        genes, source, source_file = self._extract_genes(genome_id)
        return self._predict_from_genes(genome_id.strip(), genes, source, source_file)

    def predict_uploaded_tsv(self, genome_id: str, tsv_text: str, source_name: str) -> dict[str, Any]:
        safe_id = genome_id.strip()
        if not safe_id:
            raise InferenceError("Genome ID is required.")
        if not tsv_text.strip():
            raise InferenceError("Uploaded TSV is empty.")

        reader = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
        genes = self._extract_genes_from_reader(reader, source_name)
        return self._predict_from_genes(safe_id, genes, "uploaded", source_name)

    def _predict_from_genes(self, genome_id: str, genes: set[str], source: str, source_file: str) -> dict[str, Any]:
        predictions: dict[str, Any] = {}

        for antibiotic, bundle in self._bundles.items():
            features = self._feature_vector(genes, bundle.feature_cols)
            model = bundle.model

            if model is None:
                raise InferenceError(f"Model missing in bundle for {antibiotic}.")

            try:
                predicted_class = model.predict([features])[0]
                probability = float(model.predict_proba([features])[0][1])
            except Exception as exc:  # pragma: no cover - depends on ML runtime
                raise InferenceError(f"Prediction failed for {antibiotic}: {exc}") from exc

            label = "Resistant" if int(predicted_class) == 1 else "Susceptible"
            predictions[antibiotic] = {
                "prediction": label,
                "resistance_probability": probability,
                "model_name": bundle.model_name,
                "n_features": len(bundle.feature_cols),
            }

        return {
            "genome_id": genome_id,
            "gene_count": len(genes),
            "input_source": source,
            "source_file": source_file,
            "predictions": predictions,
        }
