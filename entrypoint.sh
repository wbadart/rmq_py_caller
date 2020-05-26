#!/bin/bash

set -euo pipefail

rabtap sub "$INPUT_QUEUE" --format=json-nopp \
  | jq -cr --unbuffered "${INPUT_ADAPTER:-.Body | @base64d | fromjson}" \
  | python -u -m rmq_py_caller \
  | jq -cr --unbuffered "${OUTPUT_ADAPTER:-.result}" \
  | while read -r result; do
      if [ "${PUBLISH_NULL:-0}" = 1 -o "$result" != null ]; then
        rabtap pub <(echo "$result") \
            --exchange "$OUTPUT_EXCHANGE" \
            --routingkey "${OUTPUT_ROUTING_KEY:-}"
      fi
    done
