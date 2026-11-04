
#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy a tested SOAR release from S3.
# Run as root through AWS Systems Manager.

BASE="/opt/innovatech/soar"
APP_DIR="$BASE/repo"
VENV="$BASE/venv"
SERVICE="innovatech-soar.service"
HEALTH_URL="http://10.20.20.10:8000/health"

ARTIFACT="${1:?Usage: deploy_release.sh s3_uri sha256}"
EXPECTED_SHA="${2:?Missing artifact SHA256}"

BACKUP=""
STAGING=""
ARCHIVE=""

cleanup() {
    if [[ -n "$STAGING" && -d "$STAGING" ]]; then
        rm -rf -- "$STAGING"
    fi

    if [[ -n "$ARCHIVE" && -f "$ARCHIVE" ]]; then
        rm -f -- "$ARCHIVE"
    fi
}

rollback() {
    local exit_code=$?
    trap - ERR

    echo "Deployment failed (exit code $exit_code)."

    if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
        echo "Restoring previous SOAR release..."

        if [[ -d "$APP_DIR" ]]; then
            mv "$APP_DIR" "$BASE/failed-release-$(date +%s)"
        fi

        mv "$BACKUP" "$APP_DIR"
        systemctl restart "$SERVICE" || true

        echo "Previous release restored."
    fi

    cleanup
    exit "$exit_code"
}

trap rollback ERR
trap cleanup EXIT

if [[ "$(id -u)" -ne 0 ]]; then
    echo "This script must run as root."
    exit 1
fi

if [[ ! -d "$APP_DIR/app/soar" ]]; then
    echo "Existing SOAR installation not found."
    exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "SOAR virtual environment not found."
    exit 1
fi

echo "Downloading SOAR release..."

STAGING="$(mktemp -d "$BASE/.staging-XXXXXXXX")"
ARCHIVE="$(mktemp /tmp/innovatech-soar-XXXXXXXX.zip)"

aws s3 cp "$ARTIFACT" "$ARCHIVE" \
    --region eu-central-1

echo "$EXPECTED_SHA  $ARCHIVE" | sha256sum -c -

unzip -q "$ARCHIVE" -d "$STAGING"

# Validate the expected package structure.
for file in \
    app/soar/__init__.py \
    app/soar/main.py \
    app/soar/rules.py \
    app/soar/actions.py \
    app/soar/dedup.py \
    app/soar/metrics.py \
    app/soar/requirements.txt
do
    if [[ ! -f "$STAGING/$file" ]]; then
        echo "Missing required release file: $file"
        exit 1
    fi
done

if [[ ! -d "$STAGING/app/soar/playbooks" ]]; then
    echo "Missing SOAR playbooks."
    exit 1
fi

# Do not silently change dependencies in the existing venv.
if ! cmp -s \
    "$APP_DIR/app/soar/requirements.txt" \
    "$STAGING/app/soar/requirements.txt"
then
    echo "Dependency changes detected."
    echo "This deployment requires a separate dependency update."
    exit 1
fi

# Make sure the service can read the deployed source.
chmod -R a+rX "$STAGING"

echo "Creating release backup..."

BACKUP="$BASE/repo.backup-$(date +%Y%m%d-%H%M%S)"
mv "$APP_DIR" "$BACKUP"

echo "Installing new release..."

mv "$STAGING" "$APP_DIR"
STAGING=""

systemctl restart "$SERVICE"

echo "Checking SOAR health..."

HEALTHY=0

for attempt in {1..10}; do
    if curl -fsS --max-time 5 "$HEALTH_URL" |
        python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("status")=="healthy" else 1)'
    then
        HEALTHY=1
        break
    fi

    sleep 2
done

if [[ "$HEALTHY" -ne 1 ]]; then
    echo "SOAR health verification failed."
    false
fi

echo "SOAR deployment successful."
echo "Previous release retained at: $BACKUP"
echo "Health endpoint: $HEALTH_URL"
