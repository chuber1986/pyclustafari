#!/usr/bin/env bash
# Populate SLURM_DIR with the Slurm 26.05 headers, shared libraries, and
# client plugins taken from the giovtorres/slurm-docker image (the same
# image PySlurm/pyslurm builds and tests against in its CI). This provides
# a Slurm environment to build pyslurm on a machine without Slurm
# installed (e.g. a GitHub Actions runner).
#
# The image is a multi-arch OCI index; the amd64 image's layers are fetched
# straight from the Docker Hub registry (no docker/podman needed). Only the
# slurm-specific files are extracted, keeping the working set small.
#
# Usage: extract_slurm_env.sh <SLURM_DIR> [image:tag]
set -euo pipefail

SLURM_DIR="${1:?usage: extract_slurm_env.sh <SLURM_DIR> [image:tag]}"
IMAGE="${2:-giovtorres/slurm-docker:26.05.3-rl10}"

REPO="${IMAGE%%:*}"
TAG="${IMAGE##*:}"

TOKEN="$(curl -fsS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${REPO}:pull" | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')"
AUTH=(-H "Authorization: Bearer ${TOKEN}")
BASE="https://registry-1.docker.io/v2/${REPO}"

INDEX="$(curl -fsSL "${AUTH[@]}" -H 'Accept: application/vnd.oci.image.index.v1+json' "${BASE}/manifests/${TAG}")"
MANIFEST="$(python3 -c '
import json, sys
m = json.loads(sys.stdin.read())
print(next(x["digest"] for x in m["manifests"] if x["platform"]["architecture"] == "amd64"))
' <<<"${INDEX}")"

LAYER_DIGESTS="$(python3 -c '
import json, sys
m = json.loads(sys.stdin.read())
print(" ".join(l["digest"] for l in m["layers"]))
' <<<"$(curl -fsSL "${AUTH[@]}" -H 'Accept: application/vnd.oci.image.manifest.v2+json' "${BASE}/manifests/${MANIFEST}")")"

# Files that make up a usable Slurm client environment. No slurmctld/spool
# state is needed, just headers to compile against and libraries/plugins to
# link and load.
WANT_RE='^usr/include/slurm/|^usr/lib64/(slurm/libslurmfull\.so|slurm/auth_[a-z0-9]+\.so|libslurm\.so(\.45(\.0\.0)?)?)$'

mkdir -p "${SLURM_DIR}"
TMP="$(mktemp -d)"
cleanup() {
  # Extracted image files carry root modes; make them writable so the
  # cleanup can remove them (a failing trap would otherwise mask the exit
  # code of the real work).
  chmod -R u+w "${TMP}" 2>/dev/null || true
  rm -rf "${TMP}" 2>/dev/null || true
}
trap cleanup EXIT

# Member-filtered tar extraction (xzf with member args / --files-from) is
# not portable across tar versions, and `grep -q` in a pipeline fails under
# pipefail (grep exits on first match, tar dies on SIGPIPE). So: list each
# layer, fully extract the ones that hold slurm files, and copy out just the
# wanted paths.
for D in ${LAYER_DIGESTS}; do
  curl -fsSL "${AUTH[@]}" "${BASE}/blobs/${D}" -o "${TMP}/layer.tar.gz"
  tar tzf "${TMP}/layer.tar.gz" 2>/dev/null | grep -E "${WANT_RE}" > "${TMP}/members" || true
  if [ ! -s "${TMP}/members" ]; then
    continue
  fi
  echo "extracting slurm files from layer ${D:0:19}..."
  rm -rf "${TMP}/x"
  mkdir -p "${TMP}/x"
  tar xzf "${TMP}/layer.tar.gz" -C "${TMP}/x" --no-same-owner
  mkdir -p "${SLURM_DIR}/usr/include" "${SLURM_DIR}/usr/lib64"
  if [ -d "${TMP}/x/usr/include/slurm" ]; then
    cp -r "${TMP}/x/usr/include/slurm" "${SLURM_DIR}/usr/include/"
  fi
  if [ -d "${TMP}/x/usr/lib64/slurm" ]; then
    cp -r "${TMP}/x/usr/lib64/slurm" "${SLURM_DIR}/usr/lib64/"
  fi
  if [ -f "${TMP}/x/usr/lib64/libslurm.so" ]; then
    cp "${TMP}/x/usr/lib64/libslurm.so" \
       "${TMP}/x/usr/lib64/libslurm.so.45" \
       "${TMP}/x/usr/lib64/libslurm.so.45.0.0" \
       "${SLURM_DIR}/usr/lib64/"
  fi
done

if [ ! -f "${SLURM_DIR}/usr/include/slurm/slurm.h" ] || [ ! -f "${SLURM_DIR}/usr/lib64/slurm/libslurmfull.so" ]; then
  echo "error: Slurm headers/library not found in image ${IMAGE}" >&2
  exit 1
fi

SLURM_VER="$(grep -m1 '#define SLURM_VERSION_NUMBER' "${SLURM_DIR}/usr/include/slurm/slurm_version.h" | awk '{print $3}')"
MAJOR=$(( (SLURM_VER >> 16) & 0xFF ))
MINOR=$(( (SLURM_VER >> 8) & 0xFF ))
echo "extracted Slurm ${MAJOR}.${MINOR} client environment to ${SLURM_DIR}"
