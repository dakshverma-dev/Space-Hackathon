export class BullseyePlot {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.selectedSatelliteId = null;
  }

  setSelectedSatellite(id) {
    this.selectedSatelliteId = id;
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
    const cx = w / 2;
    const cy = h / 2;
    const maxR = Math.min(w, h) * 0.42;

    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(127, 178, 189, 0.25)";
    for (let i = 1; i <= 5; i += 1) {
      const r = (maxR / 5) * i;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    const sat = snapshot.satellites.find((s) => s.satellite_id === this.selectedSatelliteId) || snapshot.satellites[0];
    if (!sat) {
      return;
    }

    ctx.fillStyle = "#32e39f";
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();

    const n = Math.min(snapshot.debris.length, 300);
    for (let i = 0; i < n; i += 1) {
      const d = snapshot.debris[i];
      const ang = ((d[0] + d[1]) % 360) * (Math.PI / 180);
      const pseudoMiss = Math.abs(d[2] % 8);
      const tcaNorm = Math.max(0.05, 1 - pseudoMiss / 8);
      const r = maxR * tcaNorm;

      ctx.fillStyle = pseudoMiss < 1 ? "#ff4c6a" : pseudoMiss < 5 ? "#ffbd4a" : "#32e39f";
      ctx.beginPath();
      ctx.arc(cx + Math.cos(ang) * r, cy + Math.sin(ang) * r, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}
