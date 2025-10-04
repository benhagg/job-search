const API_BASE = "http://localhost:8000"; // RAG container
const searchBtn = document.getElementById("searchBtn");
const qInput = document.getElementById("q");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const useAiCheckbox = document.getElementById("useAi");

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "crimson" : "#444";
}

function renderResult(item, index) {
  // item may vary depending on your RAG API shape.
  // Common fields handled: answer, score, source, snippet, metadata
  const el = document.createElement("div");
  el.className = "result";

  const meta = document.createElement("div");
  meta.className = "meta";
  const title = item.title || item.source || `Result ${index + 1}`;
  const score = item.score ? ` — score: ${Number(item.score).toFixed(3)}` : "";
  meta.textContent = title + score;
  el.appendChild(meta);

  if (item.answer) {
    const pre = document.createElement("pre");
    pre.textContent = item.answer;
    el.appendChild(pre);
  } else if (item.snippet || item.text) {
    const pre = document.createElement("pre");
    pre.textContent = item.snippet || item.text;
    el.appendChild(pre);
  } else {
    el.appendChild(document.createTextNode(JSON.stringify(item, null, 2)));
  }

  if (item.source || item.url) {
    const src = document.createElement("div");
    src.style.marginTop = "8px";
    src.innerHTML = `<small>Source: ${item.source || item.url}</small>`;
    el.appendChild(src);
  }

  return el;
}

async function doSearch() {
  const q = qInput.value.trim();
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
      body: JSON.stringify({ query: q, use_ai: useAiCheckbox.checked }),
    });

    if (!res.ok) {
      const txt = await res.text();
      setStatus(`Server error: ${res.status} ${txt}`, true);
      return;
    }

    const payload = await res.json();

    // attempt to handle several response shapes
    // 1) { answer, sources: [...] }
    // 2) { results: [...] }
    // 3) array [...]
    let items = [];
    if (Array.isArray(payload)) items = payload;
    else if (payload.results) items = payload.results;
    else if (payload.sources) {
      // wrap AI answer first
      if (payload.answer)
        items.push({ title: "AI answer", answer: payload.answer });
      items = items.concat(payload.sources);
    } else {
      // fallback: show whole object
      items = [payload];
    }

    if (items.length === 0) setStatus("No results found.");
    else setStatus(`Got ${items.length} result(s)`);

    for (let i = 0; i < items.length; i++) {
      resultsEl.appendChild(renderResult(items[i], i));
    }
  } catch (err) {
    setStatus("Network error: " + err.message, true);
  }
}

searchBtn.addEventListener("click", doSearch);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "crimson" : "#444";
}

function renderResult(item, index) {
  // item may vary depending on your RAG API shape.
  // Common fields handled: answer, score, source, snippet, metadata
  const el = document.createElement("div");
  el.className = "result";

  const meta = document.createElement("div");
  meta.className = "meta";
  const title = item.title || item.source || `Result ${index + 1}`;
  const score = item.score ? ` — score: ${Number(item.score).toFixed(3)}` : "";
  meta.textContent = title + score;
  el.appendChild(meta);

  if (item.answer) {
    const pre = document.createElement("pre");
    pre.textContent = item.answer;
    el.appendChild(pre);
  } else if (item.snippet || item.text) {
    const pre = document.createElement("pre");
    pre.textContent = item.snippet || item.text;
    el.appendChild(pre);
  } else {
    el.appendChild(document.createTextNode(JSON.stringify(item, null, 2)));
  }

  if (item.source || item.url) {
    const src = document.createElement("div");
    src.style.marginTop = "8px";
    src.innerHTML = `<small>Source: ${item.source || item.url}</small>`;
    el.appendChild(src);
  }

  return el;
}

async function doSearch() {
  const q = qInput.value.trim();
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
      body: JSON.stringify({ query: q, use_ai: useAiCheckbox.checked }),
    });

    if (!res.ok) {
      const txt = await res.text();
      setStatus(`Server error: ${res.status} ${txt}`, true);
      return;
    }

    const payload = await res.json();

    // attempt to handle several response shapes
    // 1) { answer, sources: [...] }
    // 2) { results: [...] }
    // 3) array [...]
    let items = [];
    if (Array.isArray(payload)) items = payload;
    else if (payload.results) items = payload.results;
    else if (payload.sources) {
      // wrap AI answer first
      if (payload.answer)
        items.push({ title: "AI answer", answer: payload.answer });
      items = items.concat(payload.sources);
    } else {
      // fallback: show whole object
      items = [payload];
    }

    if (items.length === 0) setStatus("No results found.");
    else setStatus(`Got ${items.length} result(s)`);

    for (let i = 0; i < items.length; i++) {
      resultsEl.appendChild(renderResult(items[i], i));
    }
  } catch (err) {
    setStatus("Network error: " + err.message, true);
  }
}

searchBtn.addEventListener("click", doSearch);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});
