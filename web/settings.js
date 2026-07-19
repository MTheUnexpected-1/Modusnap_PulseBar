import { app } from "../../scripts/app.js";

const HIDDEN_KEY = "UniversalStats.hiddenProviders";
const INTERVAL_KEY = "UniversalStats.pollIntervalMs";

class SettingsStore {
  constructor() {
    this._hidden = null;
  }

  _load() {
    if (this._hidden) return this._hidden;
    const raw = app.ui.settings.getSettingValue(HIDDEN_KEY, "");
    this._hidden = new Set(raw ? raw.split(",").filter(Boolean) : []);
    return this._hidden;
  }

  isProviderHidden(id) {
    return this._load().has(id);
  }

  toggleProvider(id, hidden) {
    const set = this._load();
    if (hidden) set.add(id);
    else set.delete(id);
    app.ui.settings.setSettingValue(HIDDEN_KEY, Array.from(set).join(","));
  }

  getPollIntervalMs() {
    return app.ui.settings.getSettingValue(INTERVAL_KEY, 1000);
  }
}

export const settings = new SettingsStore();

app.registerExtension({
  name: "universal_stats.settings",
  settings: [
    {
      id: INTERVAL_KEY,
      name: "Universal Stats: Poll interval (ms)",
      type: "number",
      defaultValue: 1000,
      attrs: { min: 250, max: 10000, step: 250 },
    },
    {
      id: HIDDEN_KEY,
      name: "Universal Stats: Hidden providers (comma-separated ids)",
      type: "text",
      defaultValue: "",
      tooltip: "e.g. disk,intel — matches provider ids from server/providers/",
    },
  ],
});
