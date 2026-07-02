const state = {
  fleet: null,
  checks: [],
};

const hostsTable = document.querySelector("#hostsTable");
const checksList = document.querySelector("#checksList");

function hostStatus(host) {
  const failedChecks = (host.checks || []).filter((check) => check.status === "fail").length;
  if (host.cpu_percent >= 90 || host.memory_percent >= 90 || host.failed_services > 0 || failedChecks > 0) {
    return "critical";
  }
  if (host.cpu_percent >= 75 || host.memory_percent >= 75) {
    return "warning";
  }
  return "healthy";
}

function fmtDate(value) {
  if (!value) return "never";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

function renderFleet() {
  const fleet = state.fleet || { hosts: [], healthy: 0, warning: 0, critical: 0, reports_received: 0 };
  document.querySelector("#healthyCount").textContent = fleet.healthy;
  document.querySelector("#warningCount").textContent = fleet.warning;
  document.querySelector("#criticalCount").textContent = fleet.critical;
  document.querySelector("#reportCount").textContent = fleet.reports_received;
  document.querySelector("#hostCount").textContent = `${fleet.total_hosts || 0} hosts`;

  hostsTable.innerHTML = "";
  if (!fleet.hosts.length) {
    hostsTable.innerHTML = `<tr><td colspan="5">No reports received yet. Run the collector to populate the fleet.</td></tr>`;
    return;
  }

  for (const host of fleet.hosts) {
    const status = hostStatus(host);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><span class="status-pill ${status}">${status}</span> ${host.hostname}</td>
      <td>${Number(host.cpu_percent).toFixed(1)}%</td>
      <td>${Number(host.memory_percent).toFixed(1)}%</td>
      <td>${host.failed_services || 0} failed</td>
      <td>${fmtDate(host.received_at)}</td>
    `;
    hostsTable.appendChild(row);
  }
}

function renderChecks() {
  checksList.innerHTML = "";
  if (!state.checks.length) {
    checksList.innerHTML = `<div class="check warn"><strong>Checks pending</strong><p>Run diagnostics to validate network, disk, and permissions.</p></div>`;
    return;
  }

  for (const check of state.checks) {
    const item = document.createElement("div");
    item.className = `check ${check.status}`;
    const latency = check.latency_ms === undefined ? "" : `<span>${check.latency_ms} ms</span>`;
    item.innerHTML = `<strong>${check.name.replaceAll("_", " ")} ${latency}</strong><p>${check.message}</p>`;
    checksList.appendChild(item);
  }
}

async function refreshFleet() {
  state.fleet = await fetchJson("/api/fleet");
  renderFleet();
}

async function runChecks() {
  const result = await fetchJson("/api/checks");
  state.checks = result.checks;
  renderChecks();
}

document.querySelector("#refreshButton").addEventListener("click", refreshFleet);
document.querySelector("#runChecksButton").addEventListener("click", runChecks);

renderChecks();
refreshFleet().catch((error) => {
  hostsTable.innerHTML = `<tr><td colspan="5">${error.message}</td></tr>`;
});
