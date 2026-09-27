#!/usr/bin/env bash
# Local-only registry round trip, including all platform manifests and attestations.
set -Eeuo pipefail
ARCHIVE="$(realpath "${1:?OCI archive required}")"
WORK="$(mktemp -d)"
CID=''
cleanup() {
  if [[ -n "$CID" ]]; then docker rm -fv "$CID" >/dev/null 2>&1 || true; fi
  rm -rf -- "$WORK"
}
trap cleanup EXIT
CID="$(docker run --rm -d -p 127.0.0.1::5000 -e OTEL_TRACES_EXPORTER=none registry:3)"
ENDPOINT="$(docker port "$CID" 5000/tcp)"
[[ "$ENDPOINT" =~ ^127\.0\.0\.1:[0-9]+$ ]]
READY=0
for ((i=0; i<30; i++)); do
  if curl -fsS --max-time 2 "http://$ENDPOINT/v2/" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
[[ "$READY" == 1 ]]
skopeo inspect --raw "oci-archive:$ARCHIVE" > "$WORK/expected.json"
# HTTP is used only for this disposable loopback test registry.
skopeo copy --all --preserve-digests --dest-tls-verify=false \
  "oci-archive:$ARCHIVE" "docker://$ENDPOINT/autoheal:test"
skopeo copy --all --preserve-digests --src-tls-verify=false \
  "docker://$ENDPOINT/autoheal:test" "oci:$WORK/roundtrip"
skopeo inspect --raw "oci:$WORK/roundtrip" > "$WORK/actual.json"
cmp "$WORK/expected.json" "$WORK/actual.json"
echo 'Multi-platform image and attestations survived registry round trip unchanged.'
