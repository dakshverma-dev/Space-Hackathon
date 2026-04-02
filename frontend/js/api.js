const BASE = "";

export async function fetchSnapshot() {
  const response = await fetch(`${BASE}/api/visualization/snapshot`);
  if (!response.ok) {
    throw new Error(`snapshot failed: ${response.status}`);
  }
  return response.json();
}

export async function simulateStep(stepSeconds) {
  const response = await fetch(`${BASE}/api/simulate/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_seconds: stepSeconds }),
  });
  if (!response.ok) {
    throw new Error(`simulate failed: ${response.status}`);
  }
  return response.json();
}

export async function exportManeuversCsv() {
  const response = await fetch(`${BASE}/api/maneuver/export.csv`);
  if (!response.ok) {
    throw new Error(`export failed: ${response.status}`);
  }
  return response.blob();
}
