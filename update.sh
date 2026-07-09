#!/bin/bash
set -euo pipefail

IMAGE_REPO=ghcr.io/trustable-ai/trustable-app
NAMESPACE=nuvolaris
STATEFULSET=trustable
CONTAINER=trustable
NOTIFY="https://landing.nuvolaris.org/api/my/v1/notify?input="

if ! command -v jq >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get -y install jq curl
fi

TOKEN="$(curl -fsSL "https://ghcr.io/token?scope=repository:trustable-ai/trustable-app:pull&service=ghcr.io" | jq -r '.token')"
CURRENT="$(
    curl -fsSL -H "Authorization: Bearer $TOKEN" "https://ghcr.io/v2/trustable-ai/trustable-app/tags/list" |
    jq -r '.tags[] | select(startswith("trustable_"))' |
    sort -Vr |
    head -1
)"

if [[ -z "$CURRENT" ]]; then
    echo "Cannot detect the latest Trustable image tag."
    exit 1
fi

IMAGE="$IMAGE_REPO:$CURRENT"
RUNNING_IMAGE="$(
    sudo k3s kubectl -n "$NAMESPACE" get "sts/$STATEFULSET" \
        -ojsonpath="{range .spec.template.spec.containers[?(@.name==\"$CONTAINER\")]}{.image}{\"\n\"}{end}"
)"
RUNNING="${RUNNING_IMAGE##*:}"
VERSION="$(awk -F_ '{print $2}' <<<"$RUNNING")"
TAG="$(awk -F_ '{print $3}' <<<"$RUNNING")"
echo Running: $RUNNING
echo Current: $CURRENT

case "$VERSION" in
    (v0.3.6|v0.3.7|v0.3.8)
        echo Version is end of life and no more updated.
        echo Download a new installer from https://download2.trustable.it
        curl -sL "${NOTIFY}end-of-life+$VERSION+$TAG" >/dev/null
    ;;
    (v*)
        if [[ "$RUNNING" == "$CURRENT" ]]
        then echo "You are running the latest version available"
                  curl -sL "${NOTIFY}up-to-date+$CURRENT" >/dev/null
        else echo "Updating"
             sudo k3s kubectl -n "$NAMESPACE" set image "statefulset/$STATEFULSET" "$CONTAINER=$IMAGE"
             sudo k3s kubectl -n "$NAMESPACE" rollout status "statefulset/$STATEFULSET"
             curl -sL "${NOTIFY}$RUNNING+to+$CURRENT" >/dev/null
        fi
    ;;
    (*)
        echo "Unknown version. This should not happen."
        curl -sL "${NOTIFY}unknown+$RUNNING" >/dev/null
    ;;
esac
