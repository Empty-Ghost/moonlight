#!/bin/bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
if [[ "$repo_root" != "$PWD" ]]; then
  echo "Run this script from the moonlight-qt repository root." >&2
  exit 1
fi
if [[ ! -d "$repo_root/libs/mac" ]]; then
  echo "Missing libs/mac; run python3 setup-deps.py first." >&2
  exit 1
fi

jobs=$(sysctl -n hw.logicalcpu)
native_qmake=${QMAKE_NATIVE:-qmake}
universal_qmake=${QMAKE_UNIVERSAL:-qmake}
build_one() {
  local folder=$1
  local arches=$2
  local config=$3
  local qmake_command=$4
  local build_dir="$repo_root/build/$folder"
  mkdir -p "$build_dir"
  (
    cd "$build_dir"
    "$qmake_command" "$repo_root/moonlight-qt.pro" "QMAKE_APPLE_DEVICE_ARCHS=$arches" \
      "CONFIG+=$config" "CONFIG-=$([[ "$config" == debug ]] && echo release || echo debug)"
    make -j"$jobs" "$config"
  )
}

build_one phase0-arm64-debug arm64 debug "$native_qmake"
build_one phase0-arm64-release arm64 release "$native_qmake"
build_one phase0-universal-release "x86_64 arm64" release "$universal_qmake"

for binary in \
  build/phase0-arm64-debug/app/Moonlight.app/Contents/MacOS/Moonlight \
  build/phase0-arm64-release/app/Moonlight.app/Contents/MacOS/Moonlight \
  build/phase0-universal-release/app/Moonlight.app/Contents/MacOS/Moonlight; do
  file "$binary"
  lipo -archs "$binary"
done
