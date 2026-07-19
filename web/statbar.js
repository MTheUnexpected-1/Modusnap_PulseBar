import { app } from "../../scripts/app.js";
import { settings } from "./settings.js";

const EXT_ID = "modusnap.pulsebar";

function levelClass(percent) {
  if (percent == null) return "";
  if (percent >= 90) return "crit";
  if (percent >= 70) return "warn";
  return "";
}

function makeItem(id, label) {
  const el = document.createElement("div");
  el.className = "modusnap-pulsebar-item offline";
  el.dataset.id = id;

  el.innerHTML = `
    <span class="label">${label}</span>
    <span class="value">--</span>
    <div class="bar-track">
      <div class="bar-fill"></div>
    </div>
  `;

  return el;
}

class PulseBar {
  constructor() {
    this.root = document.createElement("div");
    this.root.className = "modusnap-pulsebar";
    this.items = new Map();
    this.ws = null;
    this.reconnectTimer = null;
    this.reconnectDelay = 1000;
    this.mounted = false;
  }

  mount() {
    if (this.mounted) return;

    const menu =
      document.querySelector(".comfyui-menu") ||
      document.querySelector(".comfy-menu") ||
      document.querySelector("#comfyui-body-top") ||
      document.querySelector("header");

    if (!menu) {
      setTimeout(() => this.mount(), 500);
      return;
    }

    menu.appendChild(this.root);
    this.mounted = true;
    this.connect();
  }

  connect() {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${protocol}://${window.location.host}/modusnap_pulsebar/ws`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("[ModuSnap PulseBar] WebSocket connected");
      this.reconnectDelay = 1000;
    };

    this.ws.onmessage = (event) => {
      try {
        const snapshot = JSON.parse(event.data);
        this.onSnapshot(snapshot);
      } catch (error) {
        console.error("[ModuSnap PulseBar] Invalid WebSocket payload", error);
      }
    };

    this.ws.onerror = (error) => {
      console.error("[ModuSnap PulseBar] WebSocket error", error);

      if (this.ws) {
        this.ws.close();
      }
    };

    this.ws.onclose = () => {
      console.warn("[ModuSnap PulseBar] WebSocket disconnected");

      clearTimeout(this.reconnectTimer);

      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);

      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10000);
    };
  }

  ensureItem(id, label) {
    if (this.items.has(id)) {
      return this.items.get(id);
    }

    const el = makeItem(id, label);
    this.root.appendChild(el);
    this.items.set(id, el);

    return el;
  }

  onSnapshot(snapshot) {
    const providers = snapshot?.providers || {};

    for (const [id, data] of Object.entries(providers)) {
      if (settings?.isProviderHidden?.(id)) {
        continue;
      }

      this.renderProvider(id, data);
    }
  }

  renderProvider(id, data) {
    const el = this.ensureItem(id, data.label || id);

    el.classList.toggle("offline", !data.ok);

    const valueEl = el.querySelector(".value");
    const fillEl = el.querySelector(".bar-fill");

    if (!data.ok) {
      valueEl.textContent = "Offline";
      fillEl.style.width = "0%";
      el.title = data.error || `${data.label || id} unavailable`;
      return;
    }

    let percent = null;

    if (Array.isArray(data.gpus) && data.gpus.length > 0) {
      percent = data.gpus[0]?.gpu_percent;
    } else {
      percent =
        data.percent ??
        data.cpu_percent ??
        data.ram_percent ??
        data.disk_percent ??
        data.gpu_percent ??
        null;
    }

    const safePercent =
      percent == null
        ? 0
        : Math.max(0, Math.min(100, Number(percent)));

    valueEl.textContent =
      percent != null && !Number.isNaN(Number(percent))
        ? `${Math.round(Number(percent))}%`
        : "--";

    fillEl.style.width = `${safePercent}%`;
    fillEl.className = `bar-fill ${levelClass(percent)}`;

    el.title = this.buildTooltip(id, data);
  }

  buildTooltip(id, data) {
    const lines = [data.label || id];

    const skip = new Set([
      "id",
      "label",
      "ok",
      "error",
      "ts",
      "gpus",
      "display_adapters",
    ]);

    for (const [key, value] of Object.entries(data)) {
      if (skip.has(key) || value == null) continue;
      if (typeof value === "object") continue;

      lines.push(`${key}: ${value}`);
    }

    if (Array.isArray(data.gpus)) {
      data.gpus.forEach((gpu, index) => {
        const driver = gpu.driver_version
          ? ` | driver ${gpu.driver_version}`
          : "";

        lines.push(
          `GPU ${index}: ${gpu.gpu_percent ?? "?"}% | VRAM ${
            gpu.vram_used_gb ?? "?"
          }/${gpu.vram_total_gb ?? "?"} GB${driver}`
        );
      });
    }

    if (Array.isArray(data.display_adapters)) {
      data.display_adapters.forEach((adapter) => {
        lines.push(
          `${adapter.name}: driver ${
            adapter.driver_version ?? "?"
          } (${adapter.driver_date ?? "unknown date"})`
        );
      });
    }

    return lines.join("\n");
  }
}

app.registerExtension({
  name: EXT_ID,

  async setup() {
    console.log("[ModuSnap PulseBar] Frontend extension loaded");

    const existingStyle = document.querySelector(
      'link[data-modusnap-pulsebar="true"]'
    );

    if (!existingStyle) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "/extensions/Modusnap_PulseBar/statbar.css";
      link.dataset.modusnapPulsebar = "true";
      document.head.appendChild(link);
    }

    const bar = new PulseBar();
    bar.mount();
  },
});
