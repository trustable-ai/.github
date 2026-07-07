#!/bin/bash
sudo apt-get update && sudo apt-get -y install jq curl

TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:trustable-ai/trustable-app:pull&service=ghcr.io" | jq -r '.token')
curl -s -H "Authorization: Bearer $TOKEN" "https://ghcr.io/v2/trustable-ai/trustable-app/tags/list" |\
jq -r '.tags[] | select(startswith("trustable_"))' | awk -F_ '{ print $3 " " $0 }' | sort -r >/tmp/releases
CURRENT="$(head -1 /tmp/releases | awk ' {print $2}' )"

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

if [[ "$RUNNING" == "$CURRENT" ]]
then echo "You are running the latest version available"
    curl -sL "${NOTIFY}up-to-date+$CURRENT" >/dev/null
else echo "Updating"
    sudo k3s kubectl -n "$NAMESPACE" set image "statefulset/$STATEFULSET" "$CONTAINER=$IMAGE"
    sudo k3s kubectl -n "$NAMESPACE" rollout status "statefulset/$STATEFULSET"
    curl -sL "${NOTIFY}$RUNNING+to+$CURRENT" >/dev/null
fi

