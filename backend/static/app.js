const API_BASE = "";

const scoreGrid = document.getElementById("score-grid");
const riskList = document.getElementById("risk-list");
const quickWins = document.getElementById("quick-wins");
const sectorBars = document.getElementById("sector-bars");
const scenarioSelect = document.getElementById("scenario-select");
const scenarioMeta = document.getElementById("scenario-meta");
const scenarioResult = document.getElementById("scenario-result");
const copilotQuestion = document.getElementById("copilot-question");
const copilotResponse = document.getElementById("copilot-response");
const assetTable = document.getElementById("asset-table");
const assetCount = document.getElementById("asset-count");
const backendDot = document.getElementById("backend-dot");
const backendStatus = document.getElementById("backend-status");

const primaryButton = document.getElementById("ask-copilot");
const scenarioButton = document.getElementById("run-scenario");
const generateAnswerButton = document.getElementById("generate-answer");
const trySampleButton = document.getElementById("try-sample");

const metricLabels = [
  { key: "overall_score", label: "Overall score", tone: "good" },
  { key: "climate_risk", label: "Climate risk", tone: "warn" },
  { key: "transition_risk", label: "Transition risk", tone: "warn" },
  { key: "physical_risk", label: "Physical risk", tone: "warn" },
  { key: "opportunity_score", label: "Opportunity", tone: "good" },
];

function setBackendStatus(ok) {
  backendDot.className = `dot ${ok ? "green" : "amber"}`;
  backendStatus.textContent = ok ? "Backend connected" : "Backend offline";
}

function createMetric(label, value, tone) {
  const wrapper = document.createElement("div");
  wrapper.className = `metric ${tone}`;

  const labelEl = document.createElement("span");
  labelEl.textContent = label;

  const valueEl = document.createElement("strong");
  valueEl.textContent = value;

  wrapper.append(labelEl, valueEl);
  return wrapper;
}

function renderScore(score) {
  scoreGrid.innerHTML = "";
  metricLabels.forEach((metric) => {
    scoreGrid.appendChild(createMetric(metric.label, score[metric.key], metric.tone));
  });
}

function renderRisks(score) {
  riskList.innerHTML = "";
  score.top_risks.forEach((risk) => {
    const item = document.createElement("li");
    item.textContent = risk;
    riskList.appendChild(item);
  });

  quickWins.innerHTML = "";
  score.quick_wins.forEach((win) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = win;
    quickWins.appendChild(tag);
  });
}

function renderSectors(score) {
  sectorBars.innerHTML = "";
  Object.entries(score.sector_breakdown).forEach(([sector, value]) => {
    const item = document.createElement("div");
    item.className = "bar-item";

    const label = document.createElement("div");
    label.className = "bar-label";
    const name = document.createElement("span");
    name.textContent = sector;
    const val = document.createElement("span");
    val.textContent = value;
    label.append(name, val);

    const bar = document.createElement("div");
    bar.className = "bar";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${value}%`;
    bar.appendChild(fill);

    item.append(label, bar);
    sectorBars.appendChild(item);
  });
}

function renderScenarioMeta(scenarios) {
  const choice = scenarioSelect.value;
  const assumptions = scenarios[choice];
  if (!assumptions) {
    scenarioMeta.innerHTML = "<span>Pick a scenario to see assumptions</span>";
    return;
  }
  scenarioMeta.innerHTML = `
    <span>Carbon price: $${assumptions.carbon_price}/tCO2e</span>
    <span>Revenue shock: ${assumptions.revenue_shock}%</span>
  `;
}

function renderScenarioResult(result) {
  if (!result) {
    scenarioResult.innerHTML = "<p class=\"muted\">Run a scenario to see portfolio impacts.</p>";
    return;
  }

  scenarioResult.innerHTML = "";
  const summary = document.createElement("p");
  summary.textContent = result.impact_summary;

  const highlights = document.createElement("div");
  highlights.className = "scenario-highlights";

  const ebitda = document.createElement("div");
  ebitda.innerHTML = `<strong>EBITDA impact</strong><span>${result.est_ebitda_impact_pct}%</span>`;

  const emissions = document.createElement("div");
  emissions.innerHTML = `<strong>Emissions delta</strong><span>${result.emissions_delta_pct}%</span>`;

  highlights.append(ebitda, emissions);

  const list = document.createElement("ul");
  result.hotspots.forEach((spot) => {
    const item = document.createElement("li");
    item.textContent = spot;
    list.appendChild(item);
  });

  scenarioResult.append(summary, highlights, list);
}

function renderCopilot(response) {
  if (!response) {
    copilotResponse.innerHTML = "<p class=\"muted\">Generate a narrative to guide stakeholders.</p>";
    return;
  }

  copilotResponse.innerHTML = "";
  const answer = document.createElement("p");
  answer.textContent = response.answer;

  const citations = document.createElement("div");
  citations.className = "chip-row";
  response.citations.forEach((cite) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = cite;
    citations.appendChild(chip);
  });

  copilotResponse.append(answer, citations);
}

function renderAssets(portfolio) {
  assetCount.textContent = `${portfolio.assets.length} assets`;
  portfolio.assets.forEach((asset) => {
    const row = document.createElement("div");
    row.className = "row";
    const totalEmissions = asset.scope1_tco2e + asset.scope2_tco2e;
    row.innerHTML = `
      <span>${asset.name}</span>
      <span>${asset.sector}</span>
      <span>${asset.region}</span>
      <span>${asset.revenue_usd_m}</span>
      <span>${totalEmissions}</span>
      <span>${asset.green_revenue_pct}%</span>
    `;
    assetTable.appendChild(row);
  });
}

function setLoading(buttons, loading) {
  buttons.forEach((button) => {
    button.disabled = loading;
    if (loading) {
      button.classList.add("loading");
    } else {
      button.classList.remove("loading");
    }
  });
}

async function fetchJson(url, options) {
  const response = await fetch(`${API_BASE}${url}`, options);
  if (!response.ok) {
    throw new Error("Request failed");
  }
  return response.json();
}

async function init() {
  const submitCopilot = async () => {
    setLoading([scenarioButton, primaryButton, generateAnswerButton], true);
    try {
      const result = await fetchJson("/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ portfolio_id: "P1", question: copilotQuestion.value.trim() }),
      });
      renderCopilot(result);
    } catch (error) {
      renderCopilot(null);
      copilotResponse.innerHTML =
        "<p class=\"muted\">Copilot request failed. Confirm the backend is running.</p>";
    } finally {
      setLoading([scenarioButton, primaryButton, generateAnswerButton], false);
    }
  };

  primaryButton.addEventListener("click", submitCopilot);
  generateAnswerButton.addEventListener("click", submitCopilot);
  trySampleButton.addEventListener("click", () => {
    copilotQuestion.value = "Where can we reallocate capex for the biggest climate upside?";
  });

  scenarioButton.addEventListener("click", async () => {
    setLoading([scenarioButton, primaryButton, generateAnswerButton], true);
    try {
      const result = await fetchJson("/scenario", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ portfolio_id: "P1", scenario: scenarioSelect.value }),
      });
      renderScenarioResult(result);
    } catch (error) {
      renderScenarioResult(null);
    } finally {
      setLoading([scenarioButton, primaryButton, generateAnswerButton], false);
    }
  });

  try {
    const [healthRes, portfolio, score, scenarios] = await Promise.all([
      fetch(`${API_BASE}/health`),
      fetchJson("/portfolio"),
      fetchJson("/score"),
      fetchJson("/scenarios"),
    ]);

    setBackendStatus(healthRes.ok);
    renderScore(score);
    renderRisks(score);
    renderSectors(score);
    renderScenarioMeta(scenarios);
    renderAssets(portfolio);

    scenarioSelect.addEventListener("change", () => renderScenarioMeta(scenarios));
  } catch (error) {
    setBackendStatus(false);
  }
}

init();
