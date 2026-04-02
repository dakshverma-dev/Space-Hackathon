import { exportManeuversCsv, fetchSnapshot, simulateStep } from "./api.js";
import { GroundTrack } from "./groundTrack.js";
import { BullseyePlot } from "./bullseyePlot.js";
import { TelemetryPanel } from "./telemetryPanel.js";
import { GanttTimeline } from "./ganttTimeline.js";

const groundTrack = new GroundTrack(document.getElementById("groundTrackCanvas"));
const bullseye = new BullseyePlot(document.getElementById("bullseyeCanvas"));
const telemetry = new TelemetryPanel(document.getElementById("telemetryCanvas"));
const timeline = new GanttTimeline(document.getElementById("timelineCanvas"));

let paused = false;
let speed = 1;
let snapshot = { satellites: [], debris: [], events: [], simulation_time: 0 };
let lightTheme = false;

groundTrack.onSelect = (id) => bullseye.setSelectedSatellite(id);

function setError(msg) {
  const banner = document.getElementById("errorBanner");
  banner.hidden = !msg;
  banner.textContent = msg || "";
}

function renderAll() {
  groundTrack.render(snapshot);
  bullseye.render(snapshot);
  telemetry.render(snapshot);
  timeline.render(snapshot);
  const list = document.getElementById("eventLogList");
  list.innerHTML = "";
  snapshot.events.slice(-20).reverse().forEach((e) => {
    const li = document.createElement("li");
    const pc = e.collision_probability != null ? ` | Pc ${(Number(e.collision_probability) * 100).toFixed(1)}%` : "";
    li.textContent = `${Math.round(e.time)}s | ${e.satellite_id} | ${e.type} | ${e.dv_m_s?.toFixed?.(2) ?? "0"} m/s${pc}`;
    list.appendChild(li);
  });

  const warnings = snapshot.events.filter((event) => event.type === "CDM");
  const worst = warnings[0];
  document.getElementById("riskSummary").textContent = worst
    ? `${worst.satellite_id} vs ${worst.debris_id} Pc ${(Number(worst.collision_probability) * 100).toFixed(1)}%`
    : "No active warnings";
  document.getElementById("deconflictedCount").textContent = String(snapshot.conflicts_deconflicted ?? 0);
}

async function tick() {
  if (!paused) {
    await simulateStep(2 * speed);
  }
  snapshot = await fetchSnapshot();
  renderAll();
  document.getElementById("loadingOverlay").style.display = "none";
}

setInterval(async () => {
  try {
    await tick();
    setError("");
  } catch (err) {
    setError(err.message || "API error");
  }
}, 2000);

document.getElementById("playPauseBtn").addEventListener("click", () => {
  paused = !paused;
  document.getElementById("playPauseBtn").textContent = paused ? "Play" : "Pause";
});

document.getElementById("speedSelect").addEventListener("change", (ev) => {
  speed = Number(ev.target.value || 1);
});

document.getElementById("themeToggleBtn").addEventListener("click", () => {
  lightTheme = !lightTheme;
  document.body.dataset.theme = lightTheme ? "light" : "dark";
  document.getElementById("themeToggleBtn").textContent = lightTheme ? "Dark" : "Light";
});

document.getElementById("exportCsvBtn").addEventListener("click", async () => {
  try {
    const blob = await exportManeuversCsv();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "maneuvers.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    setError(err.message || "Export failed");
  }
});

window.addEventListener("keydown", (ev) => {
  if (ev.code === "Space") {
    ev.preventDefault();
    paused = !paused;
    document.getElementById("playPauseBtn").textContent = paused ? "Play" : "Pause";
  }
  if (ev.key.toLowerCase() === "s" && snapshot.satellites.length) {
    bullseye.setSelectedSatellite(snapshot.satellites[0].satellite_id);
  }
});
