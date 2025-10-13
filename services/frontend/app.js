const API_BASE = "http://localhost:8000"; // RAG container
const INGEST_BASE = "http://localhost:8002"; // Ingest container
const searchBtn = document.getElementById("searchBtn");
const healthBtn = document.getElementById("healthBtn");
const qInput = document.getElementById("q");
const nResultsInput = document.getElementById("nResults");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const healthEl = document.getElementById("health");
const useAiCheckbox = document.getElementById("useAi");

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "crimson" : "#444";
}

searchBtn.addEventListener("click", doSearch);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

// --- Upload Job Listings Section ---
const uploadTypeRadios = document.getElementsByName("uploadType");
const uploadJsonDiv = document.getElementById("upload-json");
const uploadFormDiv = document.getElementById("upload-form");
const uploadExcelDiv = document.getElementById("upload-excel");
const jsonInput = document.getElementById("jsonInput");
const validateJsonBtn = document.getElementById("validateJsonBtn");
const submitJsonBtn = document.getElementById("submitJsonBtn");
const jsonValidationStatus = document.getElementById("jsonValidationStatus");
const jobForm = document.getElementById("jobForm");
const formFieldsDiv = document.getElementById("formFields");
const addFormEntryBtn = document.getElementById("addFormEntryBtn");
const formStatus = document.getElementById("formStatus");
const excelFileInput = document.getElementById("excelFileInput");
const submitExcelBtn = document.getElementById("submitExcelBtn");
const excelStatus = document.getElementById("excelStatus");

const schemaFields = [
  "Title",
  "Employment Type",
  "Employer",
  "Expires",
  "Job Salary",
  "Salary Type",
  "Job Location",
  "Location Type",
  "Residential Address",
  "Job Roles",
];

// Switch upload type UI
function switchUploadType(type) {
  uploadJsonDiv.style.display = type === "json" ? "block" : "none";
  uploadFormDiv.style.display = type === "form" ? "block" : "none";
  uploadExcelDiv.style.display = type === "excel" ? "block" : "none";
}
uploadTypeRadios.forEach((radio) => {
  radio.addEventListener("change", (e) => {
    switchUploadType(e.target.value);
  });
});

// --- JSON Upload ---
let validJsonObjects = [];
function validateJsonInput() {
  let arr;
  try {
    arr = JSON.parse(jsonInput.value);
    if (!Array.isArray(arr)) throw new Error("Not an array");
  } catch (e) {
    jsonValidationStatus.textContent = "Invalid JSON: " + e.message;
    jsonValidationStatus.style.color = "crimson";
    validJsonObjects = [];
    return;
  }
  // Validate each object
  validJsonObjects = arr.filter((obj) => {
    if (typeof obj !== "object" || obj === null) return false;
    for (const field of schemaFields) {
      if (!(field in obj)) return false;
    }
    return true;
  });
  const invalidCount = arr.length - validJsonObjects.length;
  jsonValidationStatus.textContent = `Valid objects: ${validJsonObjects.length}. Invalid: ${invalidCount}.`;
  jsonValidationStatus.style.color = invalidCount === 0 ? "green" : "#b8860b";
}
validateJsonBtn.addEventListener("click", validateJsonInput);

submitJsonBtn.addEventListener("click", async () => {
  if (!validJsonObjects.length) {
    jsonValidationStatus.textContent = "No valid objects to submit.";
    jsonValidationStatus.style.color = "crimson";
    return;
  }
  jsonValidationStatus.textContent = "Uploading...";
  try {
    const res = await fetch(`${INGEST_BASE}/add-json`, {
      method: "POST",
      body: new Blob([JSON.stringify(validJsonObjects)], {
        type: "application/json",
      }),
    });
    if (!res.ok) {
      const txt = await res.text();
      jsonValidationStatus.textContent = `Upload failed: ${res.status} ${txt}`;
      jsonValidationStatus.style.color = "crimson";
      return;
    }
    jsonValidationStatus.textContent = "Upload successful!";
    jsonValidationStatus.style.color = "green";
  } catch (e) {
    jsonValidationStatus.textContent = "Network error: " + e.message;
    jsonValidationStatus.style.color = "crimson";
  }
});

// --- Form Upload ---
let formEntries = [];
function renderFormFields() {
  formFieldsDiv.innerHTML = "";
  formEntries.forEach((entry, idx) => {
    const entryDiv = document.createElement("div");
    entryDiv.style.border = "1px solid #eee";
    entryDiv.style.padding = "8px";
    entryDiv.style.marginBottom = "8px";
    entryDiv.innerHTML = `<b>Entry ${
      idx + 1
    }</b> <button type='button' data-remove='${idx}'>Remove</button><br>`;
    schemaFields.forEach((field) => {
      const val = entry[field] || "";
      entryDiv.innerHTML += `<label>${field}: <input type='text' data-field='${field}' data-idx='${idx}' value="${val}" /></label><br>`;
    });
    formFieldsDiv.appendChild(entryDiv);
  });
  // Add remove handlers
  formFieldsDiv.querySelectorAll("button[data-remove]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const idx = Number(btn.getAttribute("data-remove"));
      formEntries.splice(idx, 1);
      renderFormFields();
    });
  });
  // Add input handlers
  formFieldsDiv.querySelectorAll("input[type='text']").forEach((input) => {
    input.addEventListener("input", (e) => {
      const idx = Number(input.getAttribute("data-idx"));
      const field = input.getAttribute("data-field");
      formEntries[idx][field] = input.value;
    });
  });
}
addFormEntryBtn.addEventListener("click", (e) => {
  formEntries.push(Object.fromEntries(schemaFields.map((f) => [f, ""])));
  renderFormFields();
});
jobForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  // Validate all entries
  const valid = formEntries.filter((entry) =>
    schemaFields.every((f) => entry[f] && entry[f].trim() !== "")
  );
  if (!valid.length) {
    formStatus.textContent = "No valid entries to submit.";
    formStatus.style.color = "crimson";
    return;
  }
  formStatus.textContent = "Uploading...";
  try {
    const res = await fetch(`${INGEST_BASE}/add-json`, {
      method: "POST",
      body: new Blob([JSON.stringify(valid)], { type: "application/json" }),
    });
    if (!res.ok) {
      const txt = await res.text();
      formStatus.textContent = `Upload failed: ${res.status} ${txt}`;
      formStatus.style.color = "crimson";
      return;
    }
    formStatus.textContent = "Upload successful!";
    formStatus.style.color = "green";
    formEntries = [];
    renderFormFields();
  } catch (e) {
    formStatus.textContent = "Network error: " + e.message;
    formStatus.style.color = "crimson";
  }
});
// Initialize with one entry
formEntries = [Object.fromEntries(schemaFields.map((f) => [f, ""]))];
renderFormFields();

// --- Excel Upload ---
submitExcelBtn.addEventListener("click", async () => {
  const file = excelFileInput.files[0];
  if (!file) {
    excelStatus.textContent = "Please select an Excel file.";
    excelStatus.style.color = "crimson";
    return;
  }
  excelStatus.textContent = "Uploading...";
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await fetch(`${INGEST_BASE}/add-excel`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const txt = await res.text();
      excelStatus.textContent = `Upload failed: ${res.status} ${txt}`;
      excelStatus.style.color = "crimson";
      return;
    }
    excelStatus.textContent = "Upload successful!";
    excelStatus.style.color = "green";
    excelFileInput.value = "";
  } catch (e) {
    excelStatus.textContent = "Network error: " + e.message;
    excelStatus.style.color = "crimson";
  }
});

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "crimson" : "#444";
}

async function doSearch() {
  console.log("doing search");
  const q = qInput.value.trim();
  const n_results = parseInt(nResultsInput.value);
  console.log("n results:", n_results);
  if (!q) {
    setStatus("Enter a query", true);
    return;
  }

  setStatus("Searching…");
  resultsEl.innerHTML = "";

  // adapt path/body to your RAG API; this assumes POST /search -> {query, use_ai}
  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: q,
        use_ai: useAiCheckbox.checked,
        n_results,
      }),
    });

    if (!res.ok) {
      const txt = await res.text();
      setStatus(`Server error: ${res.status} ${txt}`, true);
      return;
    }

    const payload = await res.json();
    const data = payload[0];
    const resCode = payload[1];

    if (!data.results.documents[0][1]) setStatus("No results found.");
    else {
      setStatus(`Got ${data.results.documents[0].length} result(s)`);
      displayResults(data.results, data.results.documents[0].length);
    }
  } catch (err) {
    setStatus("Network error: " + err.message, true);
  }
}

function displayResults(results, length) {
  console.log("Display results data:", results);

  for (let i = 0; i < length; i++) {
    const distance = results.distances[0][i];
    const text = results.documents[0][i];
    const metadata = results.metadatas[0][i];
    const location = metadata["Job Location"] || "";
    const url = metadata["URL"] || "";
    const employer = metadata["Employer"] || "";
    const salary = metadata["Job Salary"] || "";
    const title = metadata["Title"] || "";
    const employmentType = metadata["Employment Type"] || "";
    const jobRoles = metadata["Job Roles"] || "";

    const resultDiv = document.createElement("div");
    resultDiv.className = "result-item";
    resultDiv.style.border = "1px solid #ddd";
    resultDiv.style.margin = "12px 0";
    resultDiv.style.padding = "16px";
    resultDiv.style.borderRadius = "8px";
    resultDiv.style.background = "#fafbfc";

    resultDiv.innerHTML = `
      <div style="font-size:1.2em;font-weight:bold;margin-bottom:4px;">${title}</div>
      <div style="margin-bottom:8px;color:#555;">${employmentType} at ${employer}</div>
      <div style="margin-bottom:8px;"><pre style="white-space:pre-wrap;margin:0;">${text}</pre></div>
      <div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:8px;">
      <div><strong>Location:</strong> ${location}</div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:8px;">
      <div><strong>Salary:</strong> ${salary}</div>
      <div><strong>Distance:</strong> ${distance}</div>
      </div>
      <div style="margin-bottom:8px;"><strong>Job Roles:</strong> ${jobRoles}</div>
      ${
        url
          ? `<div><a href="${url}" target="_blank" rel="noopener" style="color:#1976d2;">View Job Posting</a></div>`
          : ""
      }
    `;
    resultsEl.appendChild(resultDiv);
  }
}

searchBtn.addEventListener("click", doSearch);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});
