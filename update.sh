
#!/bin/bash
IMAGE="$(sudo k3s kubectl -n nuvolaris get po/trustable-0 -o jsonpath='{.spec.containers[0].image}')"
curl -sL  "https://landing.nuvolaris.org/api/my/v1/notify?input=update+$IMAGE" >/dev/null
echo "You are at the latest version."
