function blockColor(type) {
  if (type === "EVASION") {
    return "#ff4c6a";
  }
  if (type === "RECOVERY") {
    return "#32e39f";
  }
  return "#ffbd4a";
}

export class GanttTimeline {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.zoom = 1;
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.zoom = Math.max(0.5, Math.min(3, this.zoom + (e.deltaY > 0 ? -0.1 : 0.1)));
    });
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
    const rowH = Math.max(14, Math.floor((h - 20) / Math.max(1, sats.length)));
    const start = snapshot.simulation_time - 3600;
    const span = 7200 / this.zoom;

    for (let i = 0; i < sats.length; i += 1) {
      const y = 10 + i * rowH;
      if ((Math.floor(snapshot.simulation_time / 600) + i) % 2 === 0) {
        ctx.fillStyle = "rgba(255, 189, 74, 0.1)";
        ctx.fillRect(0, y, w, rowH - 2);
      }
      ctx.fillStyle = "#7fb2bd";
      ctx.font = "11px Consolas";
      ctx.fillText(sats[i].satellite_id, 4, y + rowH - 4);
    }

    snapshot.events.slice(-300).forEach((event) => {
      const i = sats.findIndex((s) => s.satellite_id === event.satellite_id);
      if (i < 0) {
        return;
      }
      const y = 10 + i * rowH;
      const x = ((event.time - start) / span) * (w - 100) + 90;
      ctx.fillStyle = blockColor(event.type);
      ctx.fillRect(x, y + 2, 12, rowH - 6);
    });
  }
}
