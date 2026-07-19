import { app } from "../../scripts/app.js";
import { settings } from "./settings.js";

const EXT_ID = "universal_stats.statbar";

function levelClass(percent) {
  if (percent == null) return "";
  if (percent >= 90) return "crit";
  if (percent >= 70) return "warn";
  return "";
}

function makeItem(id, label) {
  const el = document.createElement("div");
  el.className = "universal-stats-item offline";
  el.dataset.id = id;
  el.innerHTML = `
    <span class="label">${label}</span>
    <span class="value">--</span>
    <div class="bar-track"><div class="bar-fill"></div></div>
  `;
  return el;
}

class StatBar {
  constructor() {
    this.root = document.createElement("div");
    this.root.className = "universal-stats-bar";
    this.items = new Map();
    this.ws = null;
    this.reconnectDelay = 1000;
  }

  mount() {
    const menu = document.querySelector(".comfyui-menu") || document.querySelector(".comfy-menu");
    if (!menu) {
      // ComfyUI's top bar may not exist yet on first extension load; retry.
      setTimeout(() => this.mount(), 500);
      return;
    }
    menu.appendChild(this.root);
    this.connect();
  }

  connect() {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${window.location.host}/universal_stats/ws`;
    this.ws = new WebSocket(url);
    this.ws.onmessage = (evt) => this.onSnapshot(JSON.parse(evt.data));
    this.ws.onclose = () => {
      setTimeout(() => this.connect(), this.reconnectDelay);
    };
    this.ws.onerror = () => this.ws.close();
  }

  ensureItem(id, label) {
    if (this.items.has(id)) return this.items.get(id);
    const el = makeItem(id, label);
    this.root.appendChild(el);
    this.items.set(id, el);
    return el;
  }

  onSnapshot(snapshot) {
    const providers = snapshot.providers || {};
    for (const [id, data] of Object.entries(providers)) {
      if (settings.isProviderHidden(id)) continue;
      this.renderProvider(id, data);
    }
  }

  renderProvider(id, data) {
    const el = this.ensureItem(id, data.label || id);
    el.classList.toggle("offline", !data.ok);
    if (!data.ok) return;

    // GPU-shaped payloads report a `gpus` array; everything else is flat.
    const percent = Array.isArray(data.gpus)
      ? data.gpus[0]?.gpu_percent
      : data.percent ?? data.gpu_percent;

    const valueEl = el.querySelector(".value");
    const fillEl = el.querySelector(".bar-fill");
    valueEl.textContent = percent != null ? `${Math.round(percent)}%` : "--";
    fillEl.style.width = `${Math.max(0, Math.min(100, percent ?? 0))}%`;
    fillEl.className = `bar-fill ${levelClass(percent)}`;

    el.title = this.buildTooltip(id, data);
  }

  buildTooltip(id, data) {
    const lines = [data.label || id];
    const skip = ["id", "label", "ok", "error", "ts", "gpus", "display_adapters"];
    for (const [k, v] of Object.entries(data)) {
      if (skip.includes(k) || v == null) continue;
      lines.push(`${k}: ${v}`);
    }
    if (Array.isArray(data.gpus)) {
      data.gpus.forEach((g, i) => {
        const driver = g.driver_version ? ` | driver ${g.driver_version}` : "";
        lines.push(`gpu${i}: ${g.gpu_percent ?? "?"}% | vram ${g.vram_used_gb ?? "?"}/${g.vram_total_gb ?? "?"}GB${driver}`);
      });
    }
    if (Array.isArray(data.display_adapters)) {
      data.display_adapters.forEach((a) => {
        lines.push(`${a.name}: driver ${a.driver_version ?? "?"} (${a.driver_date ?? "unknown date"})`);
      });
    }
    return lines.join("\n");
  }
}

app.registerExtension({
  name: EXT_ID,
  async setup() {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "extensions/universal_stats/statbar.css";
    document.head.appendChild(link);

    const bar = new StatBar();
    bar.mount();
  },
});
