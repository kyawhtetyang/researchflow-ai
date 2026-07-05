const queryEl = document.querySelector("#query");
const runEl = document.querySelector("#run");
const stepsEl = document.querySelector("#steps");
const sourcesEl = document.querySelector("#sources");
const reportEl = document.querySelector("#report");
const jobStatusEl = document.querySelector("#job-status");
const stepCountEl = document.querySelector("#step-count");
const sourceCountEl = document.querySelector("#source-count");
const readinessEl = document.querySelector("#readiness");
const jobHistoryEl = document.querySelector("#job-history");
const copyReportEl = document.querySelector("#copy-report");
const themeToggleEl = document.querySelector("#theme-toggle");
const reloadPageEl = document.querySelector("#reload-page");
let latestReport = "";
const apiBase = String(window.RESEARCHFLOW_API_BASE || window.location.origin).replace(/\/+$/, "");

const apiUrl = (path) => `${apiBase}${path}`;

const getStoredTheme = () => {
  try {
    const storedTheme = window.localStorage.getItem("theme");
    return storedTheme === "light" || storedTheme === "dark" ? storedTheme : "dark";
  } catch {
    return "dark";
  }
};

let currentTheme = getStoredTheme();

const applyTheme = (theme) => {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  if (themeToggleEl) {
    const nextTheme = theme === "dark" ? "light" : "dark";
    themeToggleEl.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
    themeToggleEl.setAttribute("title", `Switch to ${nextTheme} mode`);
  }
  try {
    window.localStorage.setItem("theme", theme);
  } catch {
    // Ignore storage errors.
  }
};

applyTheme(currentTheme);

const setLoading = (isLoading) => {
  runEl.disabled = isLoading;
  runEl.textContent = isLoading ? "Researching..." : "Run Research";
};

const escapeHtml = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const renderMarkdown = (markdown) => {
  latestReport = markdown || "";
  const html = latestReport
    .split("\n")
    .map((line) => {
      if (line.startsWith("# ")) return `<h1>${line.slice(2)}</h1>`;
      if (line.startsWith("## ")) return `<h3>${line.slice(3)}</h3>`;
      if (line.startsWith("- ")) return `<p class="bullet">${line.slice(2)}</p>`;
      if (/^\d+\.\s/.test(line)) return `<p class="numbered">${line}</p>`;
      if (!line.trim()) return "";
      return `<p>${line}</p>`;
    })
    .join("");
  reportEl.innerHTML = html || "No report generated.";
};

const loadJob = async (jobId) => {
  const [detail, summary] = await Promise.all([
    fetch(apiUrl(`/api/research/${jobId}`)).then((res) => res.json()),
    fetch(apiUrl(`/api/research/${jobId}/summary`)).then((res) => res.json()),
  ]);
  renderJob(detail, summary);
};

const renderJobHistory = (jobs) => {
  if (!jobHistoryEl) return;
  jobHistoryEl.innerHTML = "";

  if (!jobs.length) {
    const li = document.createElement("li");
    li.innerHTML = "<span>No previous jobs yet.</span>";
    jobHistoryEl.appendChild(li);
    return;
  }

  for (const job of jobs) {
    const li = document.createElement("li");
    li.className = "history-item";
    const status = escapeHtml(job.status);
    const query = escapeHtml(job.query);
    li.innerHTML = `
      <button type="button" class="history-button" data-job-id="${job.id}">
        <strong>#${job.id} - ${query}</strong>
        <span>Status: ${status}</span>
      </button>
    `;
    jobHistoryEl.appendChild(li);
  }
};

const refreshJobHistory = async () => {
  try {
    const jobs = await fetch(apiUrl("/api/research/")).then((res) => res.json());
    renderJobHistory(Array.isArray(jobs) ? jobs : []);
  } catch (error) {
    if (!jobHistoryEl) return;
    jobHistoryEl.innerHTML = `<li><span>Could not load job history: ${escapeHtml(error)}</span></li>`;
  }
};

themeToggleEl?.addEventListener("click", () => {
  currentTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(currentTheme);
});

reloadPageEl?.addEventListener("click", () => {
  window.location.reload();
});

const renderJob = (data, summary) => {
  stepsEl.innerHTML = "";
  sourcesEl.innerHTML = "";
  jobStatusEl.textContent = summary.status;
  stepCountEl.textContent = String(summary.step_count);
  sourceCountEl.textContent = String(summary.source_count);
  readinessEl.textContent = Number(summary.readiness_score).toFixed(2);

  for (const step of data.steps) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${step.step_order}. ${escapeHtml(step.agent_name.replaceAll("_", " "))}</strong><span>${escapeHtml(step.output)}</span>`;
    stepsEl.appendChild(li);
  }

  for (const source of data.sources) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${escapeHtml(source.title)}</strong><span>${escapeHtml(source.snippet ?? "")}</span><small>${escapeHtml(source.url)} · quality ${Number(source.quality_score ?? 0).toFixed(2)}</small>`;
    sourcesEl.appendChild(li);
  }

  const errorText = data.job?.error ? `Research job failed: ${data.job.error}` : "No report generated.";
  renderMarkdown(data.report?.markdown ?? errorText);
};

runEl.addEventListener("click", async () => {
  const query = queryEl.value.trim();
  if (!query) return;

  setLoading(true);
  reportEl.textContent = "Running research workflow...";

  try {
    const created = await fetch(apiUrl("/api/research/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, run_now: true }),
    }).then((res) => res.json());

    const [detail, summary] = await Promise.all([
      fetch(apiUrl(`/api/research/${created.id}`)).then((res) => res.json()),
      fetch(apiUrl(`/api/research/${created.id}/summary`)).then((res) => res.json()),
    ]);
    renderJob(detail, summary);
    await refreshJobHistory();
  } catch (error) {
    reportEl.textContent = `Research failed: ${error}`;
  } finally {
    setLoading(false);
  }
});

jobHistoryEl?.addEventListener("click", async (event) => {
  const button = event.target.closest(".history-button");
  if (!button) return;
  const jobId = button.getAttribute("data-job-id");
  if (!jobId) return;

  try {
    await loadJob(jobId);
  } catch (error) {
    reportEl.textContent = `Could not load saved job: ${error}`;
  }
});

copyReportEl.addEventListener("click", async () => {
  if (!latestReport) return;
  await navigator.clipboard.writeText(latestReport);
  copyReportEl.textContent = "Copied";
  setTimeout(() => {
    copyReportEl.textContent = "Copy";
  }, 1200);
});

refreshJobHistory();
