#!/usr/bin/env sh
set -eu
count="${1:-1}"
case "$count" in
  *[!0-9]*|'') echo "Usage: sh scripts/send-traffic.sh [repeat-count]" >&2; exit 2 ;;
esac
if [ "$count" -lt 1 ] || [ "$count" -gt 100 ]; then
  echo "repeat-count must be between 1 and 100" >&2
  exit 2
fi
base_url="${BASE_URL:-http://127.0.0.1:8080}"
paths="$(dirname "$0")/../samples/traffic-paths.txt"
requests=0
iteration=0
while [ "$iteration" -lt "$count" ]; do
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    curl --silent --show-error --output /dev/null --fail "${base_url}${path}"
    requests=$((requests + 1))
  done < "$paths"
  iteration=$((iteration + 1))
done
echo "Sent $requests requests"
