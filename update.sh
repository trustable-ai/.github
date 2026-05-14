#!/bin/bash
set -euo pipefail

IMAGE=ghcr.io/trustable-ai/trustable-app:trustable_v0.3.5_26.134.1644
NAMESPACE=nuvolaris
STATEFULSET=trustable
CONTAINER=trustable

# The StatefulSet has two containers — `trustable` (the app) and
# `reverse-proxy` (nginx, see olaris-bestia/trustable/sts.yaml). Patch only
# the app container; nginx keeps its current image.
sudo k3s kubectl -n "$NAMESPACE" set image "statefulset/$STATEFULSET" \
    "$CONTAINER=$IMAGE"
sudo k3s kubectl -n "$NAMESPACE" rollout status "statefulset/$STATEFULSET"

# notify
curl -sL "https://landing.nuvolaris.org/api/my/v1/notify?input=updated+to+$IMAGE" >/dev/null

echo "Updated Trustable to v0.3.5"
