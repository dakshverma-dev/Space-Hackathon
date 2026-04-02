function fuelColor(frac) {
  if (frac > 0.5) {
    return "#32e39f";
  }
  if (frac > 0.2) {
    return "#ffbd4a";
  }
  return "#ff4c6a";
}

export class TelemetryPanel {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
  }

  resize() {
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight;
  }

  render(snapshot) {
    this.resize();
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);

    const sats = snapshot.satellites;
    const rowH = Math.max(14, Math.floor((h - 60) / Math.max(1, sats.length)));
    ctx.font = "12px Consolas";

    sats.forEach((sat, i) => {
      const y = 10 + i * rowH;
      const bw = Math.max(40, w * 0.35 * sat.fuel_fraction);
      ctx.fillStyle = "rgba(127,178,189,0.15)";
      ctx.fillRect(130, y, w * 0.35, rowH - 4);
      ctx.fillStyle = fuelColor(sat.fuel_fraction);
      ctx.fillRect(130, y, bw, rowH - 4);
      ctx.fillStyle = "#d4f6ff";
      ctx.fillText(sat.satellite_id, 6, y + rowH - 7);
      ctx.fillText(sat.status, 80, y + rowH - 7);
    });

    const evasionCount = snapshot.events.filter((e) => e.type === "EVASION").length;
    const recovered = snapshot.events.filter((e) => e.type === "RECOVERY").length;
    const y0 = h - 34;
    ctx.fillStyle = "#7fb2bd";
    ctx.fillText("Efficiency", 8, y0 - 8);
    ctx.fillStyle = "#32e39f";
    ctx.fillRect(8, y0, Math.min(w * 0.4, evasionCount * 6), 8);
    ctx.fillStyle = "#ffbd4a";
    ctx.fillRect(8, y0 + 12, Math.min(w * 0.4, recovered * 6), 8);
  }
}
