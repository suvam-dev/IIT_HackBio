from __future__ import annotations

import json
import mimetypes
import posixpath
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from inference import InferenceError, ModelPredictor


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


try:
    PREDICTOR = ModelPredictor()
    PREDICTOR_ERROR = None
except Exception as exc:  # pragma: no cover - startup depends on local runtime
    PREDICTOR = None
    PREDICTOR_ERROR = str(exc)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "AMRBackend/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": PREDICTOR is not None,
                    "predictor_error": PREDICTOR_ERROR,
                },
            )
            return

        if parsed.path == "/api/predict":
            self._handle_predict(parsed.query)
            return

        if parsed.path == "/api/download-genome":
            self._handle_download_genome(parsed.query)
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/predict-upload":
            self._handle_predict_upload()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

    def _handle_predict(self, query: str) -> None:
        genome_id = parse_qs(query).get("genome_id", [""])[0].strip()
        if not genome_id:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Query parameter 'genome_id' is required."})
            return

        if PREDICTOR is None:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": PREDICTOR_ERROR or "Predictor is not available."},
            )
            return

        try:
            payload = PREDICTOR.predict(genome_id)
        except InferenceError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover - runtime dependent
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Unexpected prediction error: {exc}"})
            return

        self._send_json(HTTPStatus.OK, payload)

    def _handle_download_genome(self, query: str) -> None:
        genome_id = parse_qs(query).get("genome_id", [""])[0].strip()
        if not genome_id:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Query parameter 'genome_id' is required."})
            return

        if PREDICTOR is None:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": PREDICTOR_ERROR or "Predictor is not available."},
            )
            return

        try:
            file_path, source = PREDICTOR.ensure_genome_file(genome_id)
        except InferenceError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Unexpected download error: {exc}"})
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "genome_id": genome_id,
                "source": source,
                "saved_file": file_path.name,
                "saved_path": str(file_path),
            },
        )

    def _handle_predict_upload(self) -> None:
        if PREDICTOR is None:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": PREDICTOR_ERROR or "Predictor is not available."},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload."})
            return

        genome_id = str(payload.get("genome_id", "")).strip()
        tsv_text = str(payload.get("tsv_text", ""))
        source_name = str(payload.get("source_name", "uploaded.tsv")).strip() or "uploaded.tsv"

        try:
            result = PREDICTOR.predict_uploaded_tsv(genome_id, tsv_text, source_name)
        except InferenceError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Unexpected prediction error: {exc}"})
            return

        self._send_json(HTTPStatus.OK, result)

    def _serve_static(self, raw_path: str) -> None:
        path = raw_path or "/"
        if path == "/":
            path = "/frontend/"
        if path == "/frontend":
            path = "/frontend/"

        if path.startswith("/frontend/"):
            relative = path[len("/frontend/"):]
            relative = "index.html" if not relative else relative
            file_path = FRONTEND_DIR / posixpath.normpath(unquote(relative))
        else:
            file_path = ROOT / posixpath.normpath(unquote(path.lstrip("/")))

        try:
            resolved = file_path.resolve()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found.")
            return

        if not resolved.exists() or resolved.is_dir():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found.")
            return

        allowed_roots = (ROOT.resolve(), FRONTEND_DIR.resolve())
        if not any(str(resolved).startswith(str(root)) for root in allowed_roots):
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden.")
            return

        content_type, _ = mimetypes.guess_type(str(resolved))
        data = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Serving frontend and API at http://{host}:{port}/frontend/")
    server.serve_forever()


if __name__ == "__main__":
    main()
