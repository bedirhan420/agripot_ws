#!/usr/bin/env bash
# Kolay derleme icin yardimci script (VSCode terminalinden calistirin).
set -e
cd "$(dirname "$0")"
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
echo ""
echo "Derleme tamam. Simdi calistirin: source install/setup.bash"
