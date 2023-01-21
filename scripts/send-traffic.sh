#!/usr/bin/env sh
set -eu
while IFS= read -r path; do
  [ -z "$path" ] && continue
  curl --silent --output /dev/null --fail "http://localhost:8080$path"
done < "$(dirname "$0")/../samples/traffic-paths.txt"
echo "Sample traffic sent"
