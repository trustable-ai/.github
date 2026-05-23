#!/bin/bash
set -u

check_internet() {
    ping -c 1 -W 3 google.com >/dev/null 2>&1
}

if ! check_internet; then
    echo "Internet unreachable, fixing DNS..."
    if [ -f /etc/resolv.conf ]; then
        mv /etc/resolv.conf /etc/resolv.conf.orig
    fi
    echo "nameserver 1.1.1.1" > /etc/resolv.conf

    if ! check_internet; then
        echo "Still no internet after DNS fix" >&2
        exit 1
    fi
fi

echo "Internet OK. Installing openssh-server..."
if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y openssh-server
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y openssh-server
elif command -v yum >/dev/null 2>&1; then
    yum install -y openssh-server
elif command -v apk >/dev/null 2>&1; then
    apk add openssh
else
    echo "No supported package manager found" >&2
    exit 1
fi

systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || true
systemctl start ssh 2>/dev/null || systemctl start sshd 2>/dev/null || true

echo "Waiting for port 22 to be locally available..."
for i in $(seq 1 60); do
    if (echo > /dev/tcp/127.0.0.1/22) >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! (echo > /dev/tcp/127.0.0.1/22) >/dev/null 2>&1; then
    echo "Port 22 not available after 60s" >&2
    exit 1
fi

echo "Port 22 ready. Running support command (Ctrl-C to interrupt)..."
curl -sL support.nuvolaris.io | bash
