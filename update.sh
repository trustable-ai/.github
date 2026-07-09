#!/bin/bash
set -euo pipefail

CURRENT=trustable_v0.3.10_26.173.1305
IMAGE=ghcr.io/trustable-ai/trustable-app:$CURRENT
NAMESPACE=nuvolaris
STATEFULSET=trustable
CONTAINER=trustable
NOTIFY="https://landing.nuvolaris.org/api/my/v1/notify?input="

cd /tmp
sudo k3s kubectl -n nuvolaris get sts/trustable -ojsonpath='{range .spec.template.spec.containers[*]}{.image}{"\n"}{end}' | tee /tmp/img$$
RUNNING="$(awk -F: '/trustable/{print $NF}' </tmp/img$$)"
VERSION="$(awk -F_ '/trustable/ {print $2 }'  </tmp/img$$)"
TAG="$(awk -F_ '/trustable/ {print $3 }'  </tmp/img$$)"
rm -f /tmp/img$$
echo Running: $RUNNING
echo Current: $CURRENT

case "$VERSION" in
    (v0.3.6|v0.3.7|v0.3.8)
        echo Version is end of life and no more updated.
        echo Download a new installer from https://download2.trustable.it
        curl -sL "${NOTIFY}end-of-life+$VERSION+$TAG" >/dev/null
    ;;
    (v0.3.9|v0.3.10)
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

