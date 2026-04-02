function lonToX(lon, width) {
  return ((lon + 180) / 360) * width;
}

function latToY(lat, height) {
  return ((90 - lat) / 180) * height;
}

export class GroundTrack {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.selectedSatelliteId = null;
    this.onSelect = null;
    canvas.addEventListener("click", (ev) => this.handleClick(ev));
  }

  resize() {
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight;
  }

  handleClick(ev) {
    if (!this.lastSnapshot) {
      return;
    }
    const rect = this.canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;

    let best = null;
    let bestD = 999999;
    for (const sat of this.lastSnapshot.satellites) {
      const sx = lonToX(sat.lon, this.canvas.width);
      const sy = latToY(sat.lat, this.canvas.height);
      const d = Math.hypot(sx - x, sy - y);
      if (d < bestD) {
        bestD = d;
        best = sat;
      }
    }

    if (best && bestD <= 14) {
      this.selectedSatelliteId = best.satellite_id;
      if (this.onSelect) {
        this.onSelect(best.satellite_id);
      }
    }
  }

  render(snapshot) {
    this.lastSnapshot = snapshot;
    this.resize();

    const { ctx, canvas } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "rgba(100, 170, 200, 0.12)";
    for (let lon = -180; lon <= 180; lon += 30) {
      const x = lonToX(lon, canvas.width);
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let lat = -90; lat <= 90; lat += 30) {
      const y = latToY(lat, canvas.height);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    const t = snapshot.simulation_time;
    const terminatorX = ((t / 240) % canvas.width);
    ctx.fillStyle = "rgba(3, 6, 10, 0.35)";
    ctx.fillRect(terminatorX, 0, canvas.width - terminatorX, canvas.height);

    ctx.fillStyle = "rgba(255, 180, 80, 0.28)";
    for (let i = 0; i < snapshot.debris.length; i += 40) {
      const [x3, y3] = snapshot.debris[i];
      const lon = (Math.atan2(y3, x3) * 180) / Math.PI;
      const lat = 0;
      ctx.fillRect(lonToX(lon, canvas.width), latToY(lat, canvas.height), 1, 1);
    }

    for (const sat of snapshot.satellites) {
      const x = lonToX(sat.lon, canvas.width);
      const y = latToY(sat.lat, canvas.height);

      ctx.strokeStyle = "rgba(80, 210, 255, 0.35)";
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo((x + 30) % canvas.width, y);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = sat.status === "NOMINAL" ? "#32e39f" : sat.status === "EVASION" ? "#ffbd4a" : "#ff4c6a";
      ctx.beginPath();
      ctx.arc(x, y, sat.satellite_id === this.selectedSatelliteId ? 5 : 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}
