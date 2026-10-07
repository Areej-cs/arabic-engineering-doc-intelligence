#!/bin/bash
# EC2 user data (Amazon Linux 2023): installs Docker + Compose, clones the repo and starts
# the stack. Paste into "Advanced details -> User data" when launching the instance.
set -euxo pipefail

REPO_URL="https://github.com/Areej-cs/arabic-engineering-doc-intelligence.git"
APP_DIR=/opt/arabic-doc-intel

dnf install -y docker git
systemctl enable --now docker

# Docker Compose v2 plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -sSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 2GB swap: building the image and loading AraBERT can spike memory on small instances
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
fi

git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

# Production settings - change the password; set STORAGE_BACKEND=s3 once the bucket and
# the instance's IAM role are in place (see deployment/aws/README.md).
cat > .env <<ENV
POSTGRES_PASSWORD=$(openssl rand -hex 16)
STORAGE_BACKEND=local
S3_BUCKET_NAME=
AWS_REGION=me-south-1
ENV

docker compose up -d --build
