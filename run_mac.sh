#!/bin/bash
echo "============================================"
echo "  AutoTyper - macOS Setup & Launch"
echo "============================================"
echo ""

# ── Step 1: Check for Homebrew ───────────────
if ! command -v brew &>/dev/null; then
    echo "[1/4] Installing Homebrew (needed for Python 3.11)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for Apple Silicon
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "[1/4] Homebrew already installed ✓"
fi

# ── Step 2: Install Python 3.11 ──────────────
echo ""
if ! command -v python3.11 &>/dev/null; then
    echo "[2/4] Installing Python 3.11..."
    brew install python@3.11
else
    echo "[2/4] Python 3.11 already installed ✓"
fi

# Find python3.11 binary
PY=""
for candidate in \
    "$(brew --prefix)/bin/python3.11" \
    "/opt/homebrew/bin/python3.11" \
    "/usr/local/bin/python3.11"; do
    if [ -x "$candidate" ]; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "[ERROR] Could not find python3.11 after install."
    echo "        Try opening a new Terminal window and running this script again."
    exit 1
fi

echo "        Using: $PY"
$PY --version

# ── Step 3: Install Python packages ──────────
echo ""
echo "[3/4] Installing Python packages..."
$PY -m pip install --upgrade pip -q
$PY -m pip install \
    "pynput>=1.7.6" \
    "customtkinter>=5.2.0" \
    "Pillow>=10.0.0" \
    "rumps>=0.4.0" \
    -q

echo ""
echo "[4/4] Launching AutoTyper..."
echo ""
echo "NOTE: If you see an Accessibility permission prompt,"
echo "      go to System Settings → Privacy & Security → Accessibility"
echo "      and enable Terminal or AutoTyper."
echo ""

$PY "$(dirname "$0")/auto_typer_mac.py"
