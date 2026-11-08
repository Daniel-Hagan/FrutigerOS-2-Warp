#!/bin/bash
# Build the Frutiger OS live/installer ISO.
# Run on Debian 12 (or a Debian 12 VM/container with --privileged) as root:
#   sudo ./build.sh
# Output: frutiger-os-1.0-amd64.hybrid.iso  (boot it in a VM or write it to USB)
set -euo pipefail
cd "$(dirname "$0")"
[ "$(id -u)" -eq 0 ] || { echo "Please run as root: sudo ./build.sh"; exit 1; }
command -v lb >/dev/null || apt-get install -y live-build

WORK=build
lb clean --purge 2>/dev/null || true
rm -rf "$WORK"; mkdir -p "$WORK"
cp -a config "$WORK/"
cd "$WORK"

lb config \
  --distribution bookworm \
  --architectures amd64 \
  --archive-areas "main contrib non-free non-free-firmware" \
  --debian-installer none \
  --bootappend-live "boot=live components quiet splash username=aero hostname=frutiger locales=en_US.UTF-8" \
  --iso-application "Frutiger OS" \
  --iso-publisher "Frutiger OS project" \
  --iso-volume "FRUTIGER_OS_1_0" \
  --image-name frutiger-os-1.0 \
  --memtest none

lb build 2>&1 | tee ../build.log
mv -f frutiger-os-1.0-amd64.hybrid.iso .. 2>/dev/null || true
echo
echo "Done: $(ls -1 ../frutiger-os-1.0-*.iso 2>/dev/null || echo 'see build.log for errors')"
