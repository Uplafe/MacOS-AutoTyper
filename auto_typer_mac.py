"""
AutoTyper — macOS Edition
Requirements: pip install pynput customtkinter Pillow rumps
"""

import subprocess, sys, os, json, time, threading, math

def install_if_missing(packages):
    for pkg, imp in packages:
        try:
            __import__(imp)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

install_if_missing([
    ("pynput",        "pynput"),
    ("customtkinter", "customtkinter"),
    ("Pillow",        "PIL"),
    ("rumps",         "rumps"),
])

import tkinter as tk
import customtkinter as ctk
from pynput import keyboard
from pynput.keyboard import Controller, Key
from PIL import Image, ImageDraw
import rumps


#  CONSTANTS & PATHS

APP_DIR       = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "autotyper_settings.json")

GLASS_BG     = "#0f0f13"
GLASS_CARD   = "#16161d"
GLASS_BORDER = "#2a2a3a"
GLASS_HOVER  = "#1e1e28"
ACCENT_BLUE  = "#4f8cff"
ACCENT_GREEN = "#22d3a5"
ACCENT_RED   = "#ff5c7a"
ACCENT_AMBER = "#f5a623"
TEXT_PRIMARY = "#f0f0f8"
TEXT_SEC     = "#7878a0"
TEXT_DIM     = "#3c3c58"

FONT_FAMILY  = "Inter"


#  SETTINGS

DEFAULT_SETTINGS = {
    "toggle_keys":    [],
    "type_keys":      [],
    "letter_delay":   0.05,
    "sentence_delay": 1.0,
    "always_on_top":  False,
    "audio_enabled":  True,
}

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)

settings = load_settings()


#  STATE

typer = Controller()
state = {
    "enabled":      False,
    "typing":       False,
    "pressed":      set(),
    "capturing":    None,
    "capture_keys": set(),
}


#  KEY HELPERS

def key_to_str(key) -> str:
    try:
        c = key.char
        return c if c else _key_name(key)
    except AttributeError:
        return _key_name(key)

def _key_name(key) -> str:
    name = str(key).replace("Key.", "")
    aliases = {
        "ctrl_l": "ctrl",  "ctrl_r": "ctrl",
        "shift":  "shift", "shift_l": "shift", "shift_r": "shift",
        "alt_l":  "alt",   "alt_r":  "alt",
        "cmd":    "cmd",   "cmd_l":  "cmd",    "cmd_r":  "cmd",
    }
    return aliases.get(name, name)

def keys_display(keys: list) -> str:
    return " + ".join(k.upper() for k in keys) if keys else "— not set —"

def keys_match(required: list, pressed: set) -> bool:
    return bool(required) and all(k in pressed for k in required)


#  TYPING ENGINE

def do_type():
    if state["typing"] or not state["enabled"]:
        return
    state["typing"] = True
    app.after(0, update_ui_typing_state)

    txt = text_box.get("1.0", "end-1c")
    ld  = float(letter_delay_var.get() or 0.05)
    sd  = float(sentence_delay_var.get() or 1.0)

    def _run():
        sentences = [s for s in txt.split("\n") if s.strip()]
        if not sentences:
            sentences = [txt]
        for i, sentence in enumerate(sentences):
            if not state["enabled"]:
                break
            for ch in sentence:
                if not state["enabled"]:
                    break
                typer.type(ch)
                time.sleep(ld)
            if i < len(sentences) - 1:
                typer.press(Key.enter)
                typer.release(Key.enter)
                time.sleep(sd)
        state["typing"] = False
        app.after(0, update_ui_typing_state)

    threading.Thread(target=_run, daemon=True).start()


#  AUDIO (macOS: afplay system sounds)

def beep(kind="enable"):
    if not settings.get("audio_enabled"):
        return
    sounds = {
        "enable":  "/System/Library/Sounds/Tink.aiff",
        "disable": "/System/Library/Sounds/Basso.aiff",
        "type":    "/System/Library/Sounds/Pop.aiff",
    }
    path = sounds.get(kind, sounds["enable"])
    threading.Thread(
        target=lambda: subprocess.run(["afplay", path], capture_output=True),
        daemon=True
    ).start()


#  NOTIFICATION — native macOS, no window surfacing

def show_overlay(text: str, color: str = ACCENT_GREEN):
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{text}" with title "AutoTyper"'
        ], capture_output=True)
    except Exception:
        pass
    threading.Thread(target=_notify, daemon=True).start()


#  MENU BAR 

class TrayApp(rumps.App):
    def __init__(self, tk_app):
        super().__init__("⌨", quit_button=None)
        self.tk_app = tk_app
        self.menu = [
            rumps.MenuItem("Show AutoTyper", callback=self.show_window),
            rumps.MenuItem("Toggle Macro",   callback=self.toggle),
            None,
            rumps.MenuItem("Quit",           callback=self.quit_app),
        ]

    def show_window(self, _):
        self.tk_app.after(0, lambda: (self.tk_app.deiconify(), self.tk_app.lift()))

    def toggle(self, _):
        self.tk_app.after(0, toggle_macro)

    def quit_app(self, _):
        rumps.quit_application()
        self.tk_app.after(0, self.tk_app.quit)

# ──────────────────────────────────────────────────────────
#  HOTKEY LISTENER
# ──────────────────────────────────────────────────────────
def on_press(key):
    ks = key_to_str(key)
    state["pressed"].add(ks)

    if state["capturing"]:
        state["capture_keys"].add(ks)
        return

    if keys_match(settings["toggle_keys"], state["pressed"]):
        state["enabled"] = not state["enabled"]
        app.after(0, update_enabled_ui)
        beep("enable" if state["enabled"] else "disable")
        msg = "⬤  Macro ENABLED" if state["enabled"] else "○  Macro DISABLED"
        col = ACCENT_GREEN if state["enabled"] else ACCENT_RED
        app.after(0, lambda: show_overlay(msg, col))

    elif keys_match(settings["type_keys"], state["pressed"]):
        if state["enabled"]:
            beep("type")
            do_type()

def on_release(key):
    ks = key_to_str(key)
    if state["capturing"] and state["capture_keys"]:
        captured = list(state["capture_keys"])
        which = state["capturing"]
        state["capturing"] = None
        state["capture_keys"] = set()
        app.after(0, lambda: finalize_capture(which, captured))
    state["pressed"].discard(ks)

def finalize_capture(which: str, keys: list):
    if which == "toggle":
        settings["toggle_keys"] = keys
        toggle_key_lbl.configure(text=keys_display(keys))
        toggle_capture_btn.configure(text="Change")
    else:
        settings["type_keys"] = keys
        type_key_lbl.configure(text=keys_display(keys))
        type_capture_btn.configure(text="Change")
    save_settings(settings)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.daemon = True
listener.start()

# ──────────────────────────────────────────────────────────
#  ETA
# ──────────────────────────────────────────────────────────
def calc_eta(*_):
    try:
        txt = text_box.get("1.0", "end-1c")
        ld  = float(letter_delay_var.get() or 0)
        sd  = float(sentence_delay_var.get() or 0)
        sentences = [s for s in txt.split("\n") if s.strip()]
        chars = sum(len(s) for s in sentences)
        gaps  = max(0, len(sentences) - 1)
        total = chars * ld + gaps * sd
        if total < 1:   eta_lbl.configure(text="< 1 sec")
        elif total < 60: eta_lbl.configure(text=f"~{total:.1f} sec")
        else:            eta_lbl.configure(text=f"~{total/60:.1f} min")
    except Exception:
        eta_lbl.configure(text="—")

# ──────────────────────────────────────────────────────────
#  UI UPDATERS
# ──────────────────────────────────────────────────────────
def update_enabled_ui():
    if state["enabled"]:
        status_pill.configure(fg_color=ACCENT_GREEN,
                              text=" ⬤  ENABLED  ", text_color="#000000")
        master_btn.configure(text="Disable Macro",
                             fg_color=ACCENT_RED, hover_color="#cc3355")
    else:
        status_pill.configure(fg_color="#2a2a3a",
                              text=" ○  DISABLED  ", text_color=TEXT_SEC)
        master_btn.configure(text="Enable Macro",
                             fg_color=ACCENT_BLUE, hover_color="#3a6fd8")

def update_ui_typing_state():
    if state["typing"]:
        typing_badge.configure(text="  ↩ typing…  ",
                               fg_color=ACCENT_AMBER, text_color="#000000")
    else:
        typing_badge.configure(text="  idle  ",
                               fg_color="#2a2a3a", text_color=TEXT_SEC)

def toggle_macro():
    state["enabled"] = not state["enabled"]
    update_enabled_ui()
    beep("enable" if state["enabled"] else "disable")
    msg = "⬤  Macro ENABLED" if state["enabled"] else "○  Macro DISABLED"
    show_overlay(msg, ACCENT_GREEN if state["enabled"] else ACCENT_RED)

def start_capture(which):
    state["capturing"] = which
    state["capture_keys"] = set()
    if which == "toggle":
        toggle_key_lbl.configure(text="hold keys then release…")
        toggle_capture_btn.configure(text="Waiting…")
    else:
        type_key_lbl.configure(text="hold keys then release…")
        type_capture_btn.configure(text="Waiting…")

def apply_always_on_top():
    settings["always_on_top"] = bool(aot_var.get())
    app.attributes("-topmost", settings["always_on_top"])
    save_settings(settings)

def apply_audio():
    settings["audio_enabled"] = bool(audio_var.get())
    save_settings(settings)

def save_timing(*_):
    try:
        settings["letter_delay"]   = float(letter_delay_var.get())
        settings["sentence_delay"] = float(sentence_delay_var.get())
        save_settings(settings)
    except Exception:
        pass
    calc_eta()

# ──────────────────────────────────────────────────────────
#  BUILD UI
# ──────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("AutoTyper")
app.geometry("820x540")
app.minsize(700, 460)
app.configure(fg_color=GLASS_BG)
app.attributes("-topmost", settings["always_on_top"])

def F(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def section_label(parent, text):
    ctk.CTkLabel(parent, text=text, font=F(10, "bold"),
                 text_color=TEXT_DIM).pack(anchor="w", padx=0, pady=(12, 4))

def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=GLASS_CARD, corner_radius=12,
                        border_color=GLASS_BORDER, border_width=1, **kw)

def subtle_sep(parent):
    ctk.CTkFrame(parent, height=1, fg_color=GLASS_BORDER).pack(fill="x", pady=8)

# ── Layout ────────────────────────────────────
root_frame = ctk.CTkFrame(app, fg_color="transparent")
root_frame.pack(fill="both", expand=True, padx=16, pady=12)
root_frame.columnconfigure(0, weight=3)
root_frame.columnconfigure(1, weight=2)
root_frame.rowconfigure(0, weight=1)

left  = ctk.CTkFrame(root_frame, fg_color="transparent")
left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
right = ctk.CTkFrame(root_frame, fg_color="transparent")
right.grid(row=0, column=1, sticky="nsew")

# ── Header ────────────────────────────────────
hdr = ctk.CTkFrame(left, fg_color="transparent")
hdr.pack(fill="x", pady=(0, 8))

ctk.CTkLabel(hdr, text="AutoTyper", font=F(22, "bold"),
             text_color=TEXT_PRIMARY).pack(side="left")
ctk.CTkLabel(hdr, text=" macOS", font=F(14),
             text_color=TEXT_SEC).pack(side="left", pady=(4, 0))

status_pill = ctk.CTkLabel(hdr, text=" ○  DISABLED  ", font=F(11, "bold"),
                            fg_color="#2a2a3a", corner_radius=20,
                            text_color=TEXT_SEC)
status_pill.pack(side="left", padx=10)

typing_badge = ctk.CTkLabel(hdr, text="  idle  ", font=F(10),
                             fg_color="#2a2a3a", corner_radius=20,
                             text_color=TEXT_SEC)
typing_badge.pack(side="left")

# ── Text box ──────────────────────────────────
section_label(left, "TEXT TO TYPE")
text_frame = card(left)
text_frame.pack(fill="both", expand=True, pady=(0, 8))

text_box = ctk.CTkTextbox(text_frame, font=F(13), fg_color="transparent",
                           border_width=0, text_color=TEXT_PRIMARY,
                           wrap="word")
text_box.pack(fill="both", expand=True, padx=12, pady=10)
text_box.insert("1.0", "Hello there!\nEach line is a separate sentence.\nThey are typed one by one.")
text_box.bind("<KeyRelease>", calc_eta)

# ── Timing ────────────────────────────────────
section_label(left, "TIMING")
timing_card = card(left)
timing_card.pack(fill="x", pady=(0, 8))
timing_inner = ctk.CTkFrame(timing_card, fg_color="transparent")
timing_inner.pack(fill="x", padx=14, pady=12)
timing_inner.columnconfigure(0, weight=1)
timing_inner.columnconfigure(1, weight=1)
timing_inner.columnconfigure(2, weight=1)

def timing_cell(parent, col, label, val, color):
    f = ctk.CTkFrame(parent, fg_color="#1a1a22", corner_radius=8)
    f.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
    ctk.CTkLabel(f, text=label, font=F(10), text_color=TEXT_SEC).pack(pady=(8, 0))
    var = tk.StringVar(value=str(val))
    ctk.CTkEntry(f, textvariable=var, font=F(16, "bold"),
                 fg_color="transparent", border_width=0,
                 text_color=color, justify="center", height=40
                 ).pack(padx=8, pady=(2, 8), fill="x")
    ctk.CTkLabel(f, text="seconds", font=F(9), text_color=TEXT_DIM).pack(pady=(0, 6))
    return var

letter_delay_var   = timing_cell(timing_inner, 0, "Per Letter",   settings["letter_delay"],   ACCENT_BLUE)
sentence_delay_var = timing_cell(timing_inner, 1, "Per Sentence", settings["sentence_delay"], ACCENT_AMBER)

eta_f = ctk.CTkFrame(timing_inner, fg_color="#1a1a22", corner_radius=8)
eta_f.grid(row=0, column=2, sticky="ew", padx=(6, 0))
ctk.CTkLabel(eta_f, text="Est. Duration", font=F(10), text_color=TEXT_SEC).pack(pady=(8, 0))
eta_lbl = ctk.CTkLabel(eta_f, text="—", font=F(16, "bold"), text_color=ACCENT_GREEN)
eta_lbl.pack(pady=(4, 8))
ctk.CTkLabel(eta_f, text="total", font=F(9), text_color=TEXT_DIM).pack(pady=(0, 6))

letter_delay_var.trace_add("write", save_timing)
sentence_delay_var.trace_add("write", save_timing)
calc_eta()

# ── Master button ─────────────────────────────
master_btn = ctk.CTkButton(left, text="Enable Macro", font=F(13, "bold"),
                            height=44, corner_radius=10,
                            fg_color=ACCENT_BLUE, hover_color="#3a6fd8",
                            command=toggle_macro)
master_btn.pack(fill="x", pady=(4, 0))

# ── RIGHT: Hotkeys ────────────────────────────
section_label(right, "HOTKEYS")
hk_card = card(right)
hk_card.pack(fill="x")

ctk.CTkLabel(hk_card, text="Hold combo keys, release to set  (⌘ = cmd, ⌥ = alt, ⌃ = ctrl)",
             font=F(9), text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(10, 0))
subtle_sep(hk_card)

def hotkey_row(parent, label, setting_key, which):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=8)
    ctk.CTkLabel(row, text=label, font=F(11), text_color=TEXT_SEC,
                 width=120, anchor="w").pack(side="left")
    lbl = ctk.CTkLabel(row, text=keys_display(settings[setting_key]),
                       font=F(12, "bold"), text_color=TEXT_PRIMARY, anchor="w")
    lbl.pack(side="left", fill="x", expand=True, padx=8)
    btn = ctk.CTkButton(row,
                        text="Set" if not settings[setting_key] else "Change",
                        width=70, height=28, font=F(10),
                        fg_color="#2a2a3a", hover_color="#3a3a50",
                        text_color=ACCENT_BLUE, border_color=ACCENT_BLUE,
                        border_width=1, corner_radius=6,
                        command=lambda w=which: start_capture(w))
    btn.pack(side="right")
    return lbl, btn

toggle_key_lbl, toggle_capture_btn = hotkey_row(hk_card, "Enable / Disable", "toggle_keys", "toggle")
subtle_sep(hk_card)
type_key_lbl,   type_capture_btn   = hotkey_row(hk_card, "Type Text",         "type_keys",   "type")
ctk.CTkFrame(hk_card, height=8, fg_color="transparent").pack()

# ── RIGHT: Options ────────────────────────────
section_label(right, "OPTIONS")
opt_card = card(right)
opt_card.pack(fill="x", pady=(0, 8))

def option_row(parent, label, desc, var, cmd):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=6)
    txt = ctk.CTkFrame(row, fg_color="transparent")
    txt.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(txt, text=label, font=F(12), text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
    ctk.CTkLabel(txt, text=desc,  font=F(9),  text_color=TEXT_DIM,     anchor="w").pack(anchor="w")
    ctk.CTkSwitch(row, variable=var, onvalue=1, offvalue=0, text="",
                  width=44, height=22, progress_color=ACCENT_BLUE,
                  command=cmd).pack(side="right")

aot_var   = tk.IntVar(value=int(settings["always_on_top"]))
audio_var = tk.IntVar(value=int(settings["audio_enabled"]))

option_row(opt_card, "Always on Top",  "Float above all other windows",      aot_var,   apply_always_on_top)
subtle_sep(opt_card)
option_row(opt_card, "Sound Effects",  "System sounds on toggle and type",   audio_var, apply_audio)
ctk.CTkFrame(opt_card, height=4, fg_color="transparent").pack()

# ── macOS permissions note ─────────────────────
note_card = card(right)
note_card.pack(fill="x", pady=(0, 4))
ctk.CTkLabel(note_card,
             text="⚠  macOS Accessibility",
             font=F(11, "bold"), text_color=ACCENT_AMBER).pack(anchor="w", padx=14, pady=(10, 2))
ctk.CTkLabel(note_card,
             text="Go to System Settings → Privacy & Security\n→ Accessibility → add Terminal or AutoTyper\nto allow global hotkeys and typing.",
             font=F(10), text_color=TEXT_SEC, justify="left").pack(anchor="w", padx=14, pady=(0, 10))

# ── Footer ─────────────────────────────────────
ctk.CTkLabel(right, text="✓ Settings auto-saved  ·  AutoTyper v2 macOS",
             font=F(9), text_color=TEXT_DIM).pack(anchor="e", pady=(4, 0))

# ──────────────────────────────────────────────────────────
#  PULSE ANIMATION
# ──────────────────────────────────────────────────────────
def pulse_pill():
    if state["enabled"]:
        status_pill.configure(fg_color=ACCENT_GREEN)
    app.after(500, pulse_pill)

app.after(500, pulse_pill)

# ──────────────────────────────────────────────────────────
#  MENU BAR — run in background thread
# ──────────────────────────────────────────────────────────
def start_tray():
    try:
        tray = TrayApp(app)
        tray.run()
    except Exception as e:
        print(f"Tray unavailable: {e}")

threading.Thread(target=start_tray, daemon=True).start()

# app.after(400, lambda: show_overlay("AutoTyper ready  ⌨", ACCENT_BLUE))
app.withdraw()
app.mainloop()
app.mainloop()
