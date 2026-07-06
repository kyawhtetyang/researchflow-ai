const queryEl = document.querySelector("#query");
const runEl = document.querySelector("#run");
const stepsEl = document.querySelector("#steps");
const sourcesEl = document.querySelector("#sources");
const reportEl = document.querySelector("#report");
const jobStatusEl = document.querySelector("#job-status");
const stepCountEl = document.querySelector("#step-count");
const sourceCountEl = document.querySelector("#source-count");
const readinessEl = document.querySelector("#readiness");
const runStateBadgeEl = document.querySelector("#run-state-badge");
const runStateTextEl = document.querySelector("#run-state-text");
const jobHistoryEl = document.querySelector("#job-history");
const copyReportEl = document.querySelector("#copy-report");
const themeToggleEl = document.querySelector("#theme-toggle");
const reloadPageEl = document.querySelector("#reload-page");
let latestReport = "";
const apiBase = String(window.RESEARCHFLOW_API_BASE || window.location.origin).replace(/\/+$/, "");
let activePollController = null;

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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const statusLabelMap = {
  ready: "Ready",
  pending: "Queued",
  in_progress: "Running",
  completed: "Complete",
  failed: "Failed",
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
  reportEl.classList.toggle("report-body-empty", !html);
  reportEl.innerHTML = html || "No report generated.";
};

const setRunState = (status, message) => {
  const normalizedStatus = statusLabelMap[status] ? status : "ready";
  if (runStateBadgeEl) {
    runStateBadgeEl.textContent = statusLabelMap[normalizedStatus];
    runStateBadgeEl.className = `status-pill status-pill-${normalizedStatus}`;
  }
  if (runStateTextEl) {
    runStateTextEl.textContent = message;
  }
};

const loadJob = async (jobId) => {
  const [detail, summary] = await Promise.all([
    fetch(apiUrl(`/api/research/${jobId}`)).then((res) => res.json()),
    fetch(apiUrl(`/api/research/${jobId}/summary`)).then((res) => res.json()),
  ]);
  renderJob(detail, summary);
};

const pollJobUntilSettled = async (jobId) => {
  const controller = { cancelled: false };
  activePollController = controller;

  while (!controller.cancelled) {
    const [detail, summary] = await Promise.all([
      fetch(apiUrl(`/api/research/${jobId}`)).then((res) => res.json()),
      fetch(apiUrl(`/api/research/${jobId}/summary`)).then((res) => res.json()),
    ]);

    renderJob(detail, summary);

    if (summary.status === "completed" || summary.status === "failed") {
      await refreshJobHistory();
      if (activePollController === controller) {
        activePollController = null;
      }
      return;
    }

    reportEl.textContent = `Research workflow is ${summary.status}...`;
    await sleep(1200);
  }
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

  for (const job of jobs.slice(0, 6)) {
    const li = document.createElement("li");
    li.className = "history-item";
    const status = escapeHtml(job.status);
    const query = escapeHtml(job.query);
    li.innerHTML = `
      <button type="button" class="history-button" data-job-id="${job.id}">
        <span class="history-status history-status-${status}">${status.replaceAll("_", " ")}</span>
        <strong>#${job.id} - ${query}</strong>
        <span>Open this saved run and review the generated report, steps, and sources.</span>
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
  setRunState(
    summary.status,
    summary.status === "completed"
      ? `Research run finished with ${summary.step_count} steps and ${summary.source_count} sources.`
      : summary.status === "failed"
        ? (data.job?.error || "The workflow stopped before generating a report.")
        : summary.status === "pending"
          ? "The job is queued and waiting for the worker to start."
          : "The workflow is searching, analyzing, and assembling the report."
  );

  for (const step of data.steps) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${step.step_order}. ${escapeHtml(step.agent_name.replaceAll("_", " "))}</strong><span>${escapeHtml(step.output)}</span>`;
    stepsEl.appendChild(li);
  }

  for (const source of data.sources) {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${escapeHtml(source.title)}</strong>
      <span>${escapeHtml(source.snippet ?? "No snippet available.")}</span>
      <small>
        <a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.url)}</a>
        <span>quality ${Number(source.quality_score ?? 0).toFixed(2)}</span>
      </small>
    `;
    sourcesEl.appendChild(li);
  }

  const errorText = data.job?.error ? `Research job failed: ${data.job.error}` : "No report generated.";
  renderMarkdown(data.report?.markdown ?? errorText);
};

runEl.addEventListener("click", async () => {
  const query = queryEl.value.trim();
  if (!query) return;

  setLoading(true);
  setRunState("pending", "Creating a new research run and handing it to the worker.");
  reportEl.textContent = "Running research workflow...";
  reportEl.classList.add("report-body-empty");

  try {
    const created = await fetch(apiUrl("/api/research/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, run_now: false }),
    }).then((res) => res.json());

    if (activePollController) {
      activePollController.cancelled = true;
    }

    jobStatusEl.textContent = "pending";
    stepCountEl.textContent = "0";
    sourceCountEl.textContent = "0";
    readinessEl.textContent = "0.00";
    stepsEl.innerHTML = "";
    sourcesEl.innerHTML = "";
    renderMarkdown("No report generated.");
    reportEl.textContent = `Queued research job #${created.id}. Waiting for worker...`;
    setRunState("pending", `Queued job #${created.id}. Waiting for the workflow to start.`);
    await refreshJobHistory();
    await pollJobUntilSettled(created.id);
  } catch (error) {
    reportEl.textContent = `Research failed: ${error}`;
    setRunState("failed", String(error));
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
    setRunState("failed", String(error));
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

setRunState("ready", "Waiting for a new research brief.");
refreshJobHistory();
