const API_BASE = "http://localhost:8000";

async function parseResponse(response) {
  if (response.ok) {
    return response.json();
  }

  let message = `Request failed with status ${response.status}`;
  try {
    const body = await response.json();
    message = body.error || body.detail?.error || body.detail || message;
  } catch {
    message = response.statusText || message;
  }

  throw new Error(typeof message === "string" ? message : JSON.stringify(message));
}

async function runPipeline(payload) {
  const response = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

async function getRecentRuns(limit = 10) {
  const response = await fetch(`${API_BASE}/runs?limit=${encodeURIComponent(limit)}`);
  return parseResponse(response);
}

async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return parseResponse(response);
}

window.ContentFlowAPI = {
  runPipeline,
  getRecentRuns,
  getHealth,
};
