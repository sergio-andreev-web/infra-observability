#!/usr/bin/env sh
set -eu
check() {
  name="$1"
  url="$2"
  if curl --silent --show-error --fail --output /dev/null "$url"; then
    printf 'OK   %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name" >&2
    exit 1
  fi
}
check web http://127.0.0.1:8080/health
check nginx-exporter http://127.0.0.1:9113/metrics
check blackbox-exporter http://127.0.0.1:9115/metrics
check prometheus http://127.0.0.1:9090/-/healthy
