#!/bin/bash
# VOLT - Security Toolkit Manager
# Installation Script for Kali Linux

set -e

echo "  ██╗   ██╗ ██████╗ ██╗  ████████╗"
echo "  ██║   ██║██╔═══██╗██║  ╚══██╔══╝"
echo "  ██║   ██║██║   ██║██║     ██║"
echo "  ╚██╗ ██╔╝██║   ██║██║     ██║"
echo "   ╚████╔╝ ╚██████╔╝███████╗██║"
echo "    ╚═══╝   ╚═════╝ ╚══════╝╚═╝"
echo ""
echo "  Security Toolkit Manager"
echo "  Installation Script"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/share/volt"
CONFIG_DIR="$HOME/.config/volt"
BIN_DIR="$HOME/.local/bin"

echo "[*] Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BIN_DIR"

echo "[*] Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install textual rich
else
    echo "[!] pip3 not found. Installing..."
    sudo apt update && sudo apt install -y python3-pip
    pip3 install textual rich
fi

echo "[*] Copying application files..."
cp -r "$SCRIPT_DIR/src/volt" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/data" "$INSTALL_DIR/"

echo "[*] Creating wrapper script..."
cat > "$BIN_DIR/volt" << 'EOF'
#!/bin/bash
VOLT_DIR="$HOME/.local/share/volt"
PYTHONPATH="$VOLT_DIR:$PYTHONPATH"
exec python3 -m volt "$@"
EOF
chmod +x "$BIN_DIR/volt"

echo "[*] Creating default config..."
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    cat > "$CONFIG_DIR/config.toml" << 'EOF'
[general]
theme = "dark"
show_command_before_execution = true
history_limit = 100
default_category = "All"
EOF
fi

echo "[*] Initializing database..."
export PYTHONPATH="$INSTALL_DIR:$PYTHONPATH"
python3 -c "from volt.storage.database import init_db; init_db()" 2>/dev/null || true

echo ""
echo "[✓] Installation complete!"
echo ""
echo "  Run 'volt' from any directory to start."
echo ""
echo "  Commands:"
echo "    volt              Launch TUI"
echo "    volt --list       List all tools"
echo "    volt --search X   Search for tool"
echo "    volt --help       Show help"
echo ""
echo "  Config: $CONFIG_DIR/config.toml"
echo "  Data:   $CONFIG_DIR/volt.db"
echo ""
