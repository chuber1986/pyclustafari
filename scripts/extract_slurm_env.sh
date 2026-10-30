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

# Files that make up a usable Slurm client environment. Only these are
# extracted; no slurmctld/spool state is needed, just link/load.
WANT_RE='^usr/include/slurm/|^usr/lib64/(slurm/libslurmfull\.so|slurm/auth_[a-z0-9]+\.so|libslurm\.so(\.45(\.0\.0)?)?)$'

mkdir -p "${SLURM_DIR}"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

found_any=0
for D in ${LAYER_DIGESTS}; do
  curl -fsSL "${AUTH[@]}" "${BASE}/blobs/${D}" -o "${TMP}/layer.tar.gz"
  # List the archive (streams it once) and keep only the members this layer
  # actually holds, so the extraction below matches every requested member.
  tar tzf "${TMP}/layer.tar.gz" 2>/dev/null | grep -E "${WANT_RE}" > "${TMP}/members" || true
  if [ ! -s "${TMP}/members" ]; then
    continue
  fi
  found_any=1
  echo "extracting slurm files from layer ${D:0:19}..."
  # xzf with member filter streams the archive again, writing only matches.
  tar xzf "${TMP}/layer.tar.gz" -C "${SLURM_DIR}" --no-same-owner --files-from="${TMP}/members" 2>/dev/null
done

if [ "${found_any}" -eq 0 ] || [ ! -f "${SLURM_DIR}/usr/include/slurm/slurm.h" ] || [ ! -f "${SLURM_DIR}/usr/lib64/slurm/libslurmfull.so" ]; then
  echo "error: Slurm headers/library not found in image ${IMAGE}" >&2
  exit 1
fi

SLURM_VER="$(grep -m1 '#define SLURM_VERSION_NUMBER' "${SLURM_DIR}/usr/include/slurm/slurm_version.h" | awk '{print $3}')"
MAJOR=$(( (SLURM_VER >> 16) & 0xFF ))
MINOR=$(( (SLURM_VER >> 8) & 0xFF ))
echo "extracted Slurm ${MAJOR}.${MINOR} client environment to ${SLURM_DIR}"
