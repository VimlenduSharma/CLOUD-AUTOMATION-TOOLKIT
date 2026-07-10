const state = {
  fleet: null,
  checks: [],
  demoMode: false,
};

const hostsTable = document.querySelector("#hostsTable");
const checksList = document.querySelector("#checksList");
const demoFleet = {
  total_hosts: 4,
  healthy: 2,
  warning: 1,
  critical: 1,
  reports_received: 18,
  hosts: [
    {
      hostname: "WIN-OPS-001",
      cpu_percent: 38.5,
      memory_percent: 64.1,
      failed_services: 0,
      received_at: "2026-07-10T04:20:00Z",
      checks: [{ name: "http_endpoint", status: "pass", message: "https://github.com returned HTTP 200." }],
    },
    {
      hostname: "WIN-DB-014",
      cpu_percent: 78.2,
      memory_percent: 81.4,
      failed_services: 0,
      received_at: "2026-07-10T04:18:00Z",
      checks: [{ name: "disk_threshold", status: "warn", message: "C:\\ has 16.8% free space." }],
    },
    {
      hostname: "WIN-IIS-022",
      cpu_percent: 91.6,
      memory_percent: 88.0,
      failed_services: 1,
      received_at: "2026-07-10T04:16:00Z",
      checks: [{ name: "tcp_connectivity", status: "fail", message: "Could not connect to app.internal:443." }],
    },
    {
      hostname: "WIN-JUMP-007",
      cpu_percent: 25.3,
      memory_percent: 42.8,
      failed_services: 0,
      received_at: "2026-07-10T04:12:00Z",
      checks: [{ name: "dns_resolution", status: "pass", message: "github.com resolved." }],
    },
  ],
};

const demoChecks = [
  {
    name: "dns_resolution",
    status: "pass",
    message: "github.com resolved to public addresses.",
    latency_ms: 26,
  },
  {
    name: "tcp_connectivity",
    status: "pass",
    message: "Connected to github.com:443.",
    latency_ms: 48,
  },
  {
    name: "http_endpoint",
    status: "pass",
    message: "https://github.com returned HTTP 200.",
    latency_ms: 182,
  },
  {
    name: "disk_threshold",
    status: "warn",
    message: "Demo host C:\\ has 16.8% free space.",
  },
  {
    name: "file_permission",
    status: "pass",
    message: "Collector directory allows read access.",
  },
];

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
  try {
    state.fleet = await fetchJson("/api/fleet");
    state.demoMode = false;
  } catch (error) {
    state.fleet = demoFleet;
    state.demoMode = true;
  }
  renderFleet();
}

async function runChecks() {
  if (state.demoMode || window.location.protocol === "file:") {
    state.checks = demoChecks;
    renderChecks();
    return;
  }
  try {
    const result = await fetchJson("/api/checks");
    state.checks = result.checks;
  } catch (error) {
    state.checks = demoChecks;
    state.demoMode = true;
  }
  renderChecks();
}

document.querySelector("#refreshButton").addEventListener("click", refreshFleet);
document.querySelector("#runChecksButton").addEventListener("click", runChecks);

renderChecks();
refreshFleet();
