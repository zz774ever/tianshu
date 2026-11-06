#!/usr/bin/env bash
set -euo pipefail
for model in Qwen3.6-27B Qwen3.6-35B-A3B; do
    for mode in graph eager; do
        bash /opt/gate/run-one.sh "$mode" "/models/$model"
    done
done
printf '%s\n' FOUR_ROUNDS_COMPLETE
