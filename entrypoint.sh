#!/bin/bash

set -e

rabtap sub "$INPUT_QUEUE" --format=json-nopp \
  | jq -cr --unbuffered "$INPUT_ADAPTER" \
  | python -u -m rmq_py_caller \
  | jq -cr --unbuffered "$OUTPUT_ADAPTER" \
  | while read -r result; do
      if [ "$PUBLISH_NULL" = 1 -o "$result" != null ]; then
        rabtap pub <(echo "$result") \
            --exchange "$OUTPUT_EXCHANGE" \
            --routingkey "$OUTPUT_ROUTING_KEY"
      fi
    done
