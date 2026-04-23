#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/eval/audio/synthetic"

mkdir -p "${OUT_DIR}/en" "${OUT_DIR}/zh" "${OUT_DIR}/ja"

say -v "Samantha" -r 165 -o "${OUT_DIR}/en/turn_on_bedroom_light.aiff" "Turn on the bedroom light."
say -v "Meijia" -r 165 -o "${OUT_DIR}/zh/turn_on_living_room_ac.aiff" "打開客廳冷氣。"
say -v "Kyoko" -r 165 -o "${OUT_DIR}/ja/volume_down.aiff" "音量を下げて。"

ffmpeg -y -i "${OUT_DIR}/en/turn_on_bedroom_light.aiff" -ar 16000 -ac 1 "${OUT_DIR}/en/turn_on_bedroom_light.wav" >/dev/null 2>&1
ffmpeg -y -i "${OUT_DIR}/zh/turn_on_living_room_ac.aiff" -ar 16000 -ac 1 "${OUT_DIR}/zh/turn_on_living_room_ac.wav" >/dev/null 2>&1
ffmpeg -y -i "${OUT_DIR}/ja/volume_down.aiff" -ar 16000 -ac 1 "${OUT_DIR}/ja/volume_down.wav" >/dev/null 2>&1

rm -f "${OUT_DIR}/en/turn_on_bedroom_light.aiff"
rm -f "${OUT_DIR}/zh/turn_on_living_room_ac.aiff"
rm -f "${OUT_DIR}/ja/volume_down.aiff"

echo "Created synthetic test audio under ${OUT_DIR}"
