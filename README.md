# AutoTyper — macOS Edition

## Quick Start (Easiest)

Open Terminal, navigate to this folder, then run:

```bash
chmod +x run_mac.sh
./run_mac.sh
```

That's it — it installs everything and launches the app.

---

## Build a Standalone .app

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Your `AutoTyper` binary appears in the `dist/` folder.

---

## ⚠️ REQUIRED: macOS Accessibility Permission

macOS blocks apps from monitoring the keyboard and typing globally unless you grant permission.

**Do this once:**
1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Add **Terminal** (if running via script) or **AutoTyper** (if using the built app)
4. Toggle it **ON**

Without this, hotkeys and auto-typing will not work.

---

## How to Use

1. Paste text into the text box (each line = one sentence)
2. Set per-letter and per-sentence delays
3. Click **Set** next to each hotkey — hold your key combo, then release
   - Example combos: `Cmd + 1`, `Ctrl + Alt + T`, `F6`
4. Click **Enable Macro** or press your toggle hotkey
5. Switch to your target app and press your Type hotkey

---

## Features

- Multi-key hotkey combos (Cmd, Ctrl, Alt, Shift + any key)
- Auto-saves settings between sessions
- Estimated typing duration shown live
- Animated overlay notification on enable/disable
- System sound feedback (macOS sounds)
- Always-on-top option
- Menu bar icon (⌨) for quick toggle and show/hide
- Resizable landscape UI

---

## Requirements

- macOS 11+ (Big Sur or later)
- Python 3.10–3.12 (from python.org — NOT system Python)
- Accessibility permission granted (see above)
