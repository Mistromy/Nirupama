#!/bin/bash
# Exit immediately if any command fails
set -e

echo "Installing Nirupama..."

# 1. Create the target directory and move inside it
mkdir -p ./Nirupama
cd ./Nirupama

# 2. Detect System Architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)        BINARY_ARCH="amd64" ;;
    aarch64|arm64) BINARY_ARCH="arm64" ;;
    *)             echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

echo "Architecture: $ARCH ($BINARY_ARCH)"

# 3. Download the correct Linux binary from your GitHub releases
# (Swap out 'mistromy/Nirupama' with your exact repo path)
REPO="mistromy/Nirupama"
URL="https://github.com/$REPO/releases/latest/download/supervisor-linux-$BINARY_ARCH"

echo "Installing latest supervisor..."
curl -L -o supervisor "$URL"

# 4. Make the binary executable (No sudo required since we own the file/folder!)
chmod +x supervisor

echo "Launching Supervisor..."

# 5. Execute the binary and pass down all incoming arguments (like -y)
# Any environment variables (like MASTER_ENV_KEY) automatically propagate here
./supervisor "$@"