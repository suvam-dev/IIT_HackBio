const state = {
  rows: [],
  filtered: []
};

const statusEl = document.getElementById("status");
const rowsEl = document.getElementById("rows");
const rowCountEl = document.getElementById("row-count");
const searchInput = document.getElementById("search-input");
const fileInput = document.getElementById("file-input");
const genomeInput = document.getElementById("genome-input");
const predictBtn = document.getElementById("predict-btn");
const downloadTsvBtn = document.getElementById("download-tsv-btn");
const tsvInput = document.getElementById("tsv-input");
const predictUploadBtn = document.getElementById("predict-upload-btn");
const lookupStatusEl = document.getElementById("lookup-status");
const predictionResultEl = document.getElementById("prediction-result");

const statGenomes = document.getElementById("stat-genomes");
const statCip = document.getElementById("stat-cip");
const statGen = document.getElementById("stat-gen");
const statMer = document.getElementById("stat-mer");

const REQUIRED = [
  "Genome ID",
  "ciprofloxacin_prediction",
  "gentamicin_prediction",
  "meropenem_prediction",
  "ciprofloxacin_resistance_probability",
  "gentamicin_resistance_probability",
  "meropenem_resistance_probability"
];

function parseCsv(text) {
  const out = [];
  const lines = [];
  let cur = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];

    if (ch === '"') {
      if (inQuotes && next === '"') {
        cur += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (ch === "\n" && !inQuotes) {
      lines.push(cur);
      cur = "";
      continue;
    }

    if (ch !== "\r") {
      cur += ch;
    }
  }
  if (cur.trim()) lines.push(cur);

  for (const line of lines) {
    const row = [];
    let field = "";
    let q = false;
    for (let i = 0; i < line.length; i += 1) {
      const ch = line[i];
      const next = line[i + 1];
      if (ch === '"') {
        if (q && next === '"') {
          field += '"';
          i += 1;
        } else {
          q = !q;
        }
        continue;
      }
      if (ch === "," && !q) {
        row.push(field);
        field = "";
        continue;
      }
      field += ch;
    }
    row.push(field);
    out.push(row);
  }

  return out;
}

function validateHeaders(headers) {
  return REQUIRED.every((h) => headers.includes(h));
}

function toObjects(matrix) {
  const headers = matrix[0].map((h) => h.trim());
  if (!validateHeaders(headers)) {
    throw new Error("CSV is missing expected submission columns.");
  }

  return matrix.slice(1)
    .filter((r) => r.length && r.some((x) => String(x).trim() !== ""))
    .map((row) => {
      const obj = {};
      headers.forEach((h, i) => {
        obj[h] = row[i] ?? "";
      });
      return obj;
    });
}

function badge(label) {
  const normalized = String(label || "").trim().toLowerCase();
  const res = normalized === "resistant";
  const cls = res ? "badge badge-res" : "badge badge-sus";
  return `<span class="${cls}">${label || "-"}</span>`;
}

function fmtProb(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return "-";
  return n.toFixed(3);
}

function predictionCard(title, prediction, probability) {
  return `
    <article class="prediction-card panel">
      <p class="prediction-label">${title}</p>
      <p class="prediction-badge-wrap">${badge(prediction)}</p>
      <p class="prediction-prob">Resistance probability: <strong>${fmtProb(probability)}</strong></p>
    </article>
  `;
}

function renderPredictionResult(genomeId, payload, sourceLabel) {
  predictionResultEl.innerHTML = `
    <article class="prediction-summary panel">
      <p class="prediction-summary-label">Genome ID</p>
      <h3>${genomeId}</h3>
      <p class="prediction-summary-copy">${sourceLabel}</p>
    </article>
    ${predictionCard("Ciprofloxacin", payload.ciprofloxacin.prediction, payload.ciprofloxacin.resistance_probability)}
    ${predictionCard("Gentamicin", payload.gentamicin.prediction, payload.gentamicin.resistance_probability)}
    ${predictionCard("Meropenem", payload.meropenem.prediction, payload.meropenem.resistance_probability)}
  `;
}

function showLookupMessage(message) {
  predictionResultEl.innerHTML = "";
  lookupStatusEl.textContent = message;
}

function renderLocalPrediction(genomeId) {
  const normalized = String(genomeId || "").trim();
  if (!normalized) {
    predictionResultEl.innerHTML = "";
    lookupStatusEl.textContent = "Enter a Genome ID to view a prediction.";
    return;
  }

  const row = state.rows.find((item) => String(item["Genome ID"]).trim() === normalized);

  if (!row) {
    predictionResultEl.innerHTML = "";
    lookupStatusEl.textContent = `No prediction found for Genome ID ${normalized}.`;
    return;
  }

  lookupStatusEl.textContent = `Prediction loaded for Genome ID ${normalized}.`;
  renderPredictionResult(
    normalized,
    {
      ciprofloxacin: {
        prediction: row.ciprofloxacin_prediction,
        resistance_probability: row.ciprofloxacin_resistance_probability
      },
      gentamicin: {
        prediction: row.gentamicin_prediction,
        resistance_probability: row.gentamicin_resistance_probability
      },
      meropenem: {
        prediction: row.meropenem_prediction,
        resistance_probability: row.meropenem_resistance_probability
      }
    },
    "Stored model output from the loaded submission file."
  );
}

function renderRows() {
  rowsEl.innerHTML = state.filtered.map((r) => `
    <tr>
      <td>${r["Genome ID"] || "-"}</td>
      <td>${badge(r["ciprofloxacin_prediction"])}</td>
      <td>${badge(r["gentamicin_prediction"])}</td>
      <td>${badge(r["meropenem_prediction"])}</td>
      <td>${fmtProb(r["ciprofloxacin_resistance_probability"])}</td>
      <td>${fmtProb(r["gentamicin_resistance_probability"])}</td>
      <td>${fmtProb(r["meropenem_resistance_probability"])}</td>
    </tr>
  `).join("");

  rowCountEl.textContent = `${state.filtered.length} rows`;
}

function updateStats() {
  const data = state.rows;
  statGenomes.textContent = data.length;
  statCip.textContent = data.filter((r) => r.ciprofloxacin_prediction === "Resistant").length;
  statGen.textContent = data.filter((r) => r.gentamicin_prediction === "Resistant").length;
  statMer.textContent = data.filter((r) => r.meropenem_prediction === "Resistant").length;
}

function applyFilter() {
  const q = searchInput.value.trim().toLowerCase();
  state.filtered = q
    ? state.rows.filter((r) => String(r["Genome ID"]).toLowerCase().includes(q))
    : [...state.rows];
  renderRows();
}

function loadCsvText(text, sourceLabel) {
  const matrix = parseCsv(text);
  if (!matrix.length) throw new Error("Empty CSV.");

  state.rows = toObjects(matrix);
  state.filtered = [...state.rows];

  renderRows();
  updateStats();
  statusEl.textContent = `Loaded ${state.rows.length} rows from ${sourceLabel}.`;
  lookupStatusEl.textContent = "Enter a Genome ID to view a prediction.";

  if (genomeInput.value.trim()) {
    renderLocalPrediction(genomeInput.value);
  } else {
    predictionResultEl.innerHTML = "";
  }
}

async function loadDefaultCsv() {
  statusEl.textContent = "Loading submission.csv...";
  try {
    const resp = await fetch("../data/processed/submission.csv");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const text = await resp.text();
    loadCsvText(text, "data/processed/submission.csv");
  } catch (err) {
    if (window.DEFAULT_SUBMISSION_CSV) {
      loadCsvText(window.DEFAULT_SUBMISSION_CSV, "bundled submission data");
      statusEl.textContent = "Loaded bundled submission data.";
      return;
    }
    statusEl.textContent = `Failed to load default CSV (${err.message}). Use Upload CSV.`;
  }
}

async function runPrediction() {
  if (!state.rows.length) {
    lookupStatusEl.textContent = "No data loaded yet.";
    return;
  }

  const genomeId = genomeInput.value.trim();
  if (!genomeId) {
    predictionResultEl.innerHTML = "";
    lookupStatusEl.textContent = "Enter a Genome ID to view a prediction.";
    return;
  }

  lookupStatusEl.textContent = `Running model for Genome ID ${genomeId}...`;

  try {
    const response = await fetch(`/api/predict?genome_id=${encodeURIComponent(genomeId)}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }

    lookupStatusEl.textContent = `Live prediction generated for Genome ID ${genomeId}.`;
    renderPredictionResult(
      genomeId,
      payload.predictions,
      `Live backend inference using ${payload.gene_count} detected gene features from ${payload.source_file} (${payload.input_source}).`
    );
  } catch (error) {
    lookupStatusEl.textContent = `Backend unavailable or genome not found (${error.message}). Falling back to loaded submission data.`;
    renderLocalPrediction(genomeId);
  }
}

async function runUploadedPrediction() {
  const genomeId = genomeInput.value.trim();
  const file = tsvInput.files?.[0];

  if (!genomeId) {
    showLookupMessage("Enter a Genome ID before uploading a TSV.");
    return;
  }

  if (!file) {
    showLookupMessage("Choose a TSV file to run uploaded inference.");
    return;
  }

  lookupStatusEl.textContent = `Uploading ${file.name} for Genome ID ${genomeId}...`;

  try {
    const tsvText = await file.text();
    const response = await fetch("/api/predict-upload", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        genome_id: genomeId,
        source_name: file.name,
        tsv_text: tsvText
      })
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }

    lookupStatusEl.textContent = `Live prediction generated for uploaded TSV ${file.name}.`;
    renderPredictionResult(
      genomeId,
      payload.predictions,
      `Live backend inference using ${payload.gene_count} detected gene features from ${payload.source_file} (${payload.input_source}).`
    );
  } catch (error) {
    showLookupMessage(`Uploaded TSV prediction failed: ${error.message}`);
  }
}

async function downloadGenomeTsv() {
  const genomeId = genomeInput.value.trim();
  if (!genomeId) {
    showLookupMessage("Enter a Genome ID before downloading a TSV.");
    return;
  }

  lookupStatusEl.textContent = `Downloading genome file for ${genomeId}...`;

  try {
    const response = await fetch(`/api/download-genome?genome_id=${encodeURIComponent(genomeId)}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }

    lookupStatusEl.textContent = `Genome file ready: ${payload.saved_file} (${payload.source}).`;
    predictionResultEl.innerHTML = `
      <article class="prediction-summary panel">
        <p class="prediction-summary-label">Downloaded Genome File</p>
        <h3>${payload.genome_id}</h3>
        <p class="prediction-summary-copy">Saved as ${payload.saved_file} in the backend results folder.</p>
      </article>
    `;
  } catch (error) {
    showLookupMessage(`Genome TSV download failed: ${error.message}`);
  }
}

document.getElementById("load-default").addEventListener("click", loadDefaultCsv);

fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  try {
    const text = await file.text();
    loadCsvText(text, file.name);
  } catch (err) {
    statusEl.textContent = `Error reading file: ${err.message}`;
  }
});

searchInput.addEventListener("input", applyFilter);
predictBtn.addEventListener("click", runPrediction);
downloadTsvBtn.addEventListener("click", downloadGenomeTsv);
predictUploadBtn.addEventListener("click", runUploadedPrediction);
genomeInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    runPrediction();
  }
});
tsvInput.addEventListener("change", () => {
  const file = tsvInput.files?.[0];
  if (file) {
    lookupStatusEl.textContent = `Selected TSV: ${file.name}. Click Predict From TSV to run inference.`;
  }
});

loadDefaultCsv();
