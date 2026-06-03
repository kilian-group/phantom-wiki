#!/usr/bin/env bash
# Harbor verifier entrypoint -- runs in the separate verifier container after the agent.
#
# Reads the agent's answer (forwarded by Harbor to /logs/artifacts/answer.txt), scores it
# against the gold answer from the regenerated universe, and writes:
#   - /logs/verifier/reward.txt   (single float: set-based F1)
#   - /logs/verifier/result.json  (per-question diagnostics incl. difficulty)
set -euo pipefail

mkdir -p /logs/verifier

PYTHONPATH=/opt python /opt/score_answer.py \
  --questions /gold/questions.json \
  --qid "${QID}" \
  --seed "${SEED}" \
  --answer /logs/artifacts/answer.txt \
  --reward-file /logs/verifier/reward.txt \
  --result-file /logs/verifier/result.json
