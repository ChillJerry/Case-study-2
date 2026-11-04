
#!/usr/bin/env bash
set -Eeuo pipefail

BASE="/opt/innovatech/monitoring"
DEST="$BASE/grafana/dashboards"
REGION="eu-central-1"

ARTIFACT="${1:?Missing artifact URI}"
EXPECTED_SHA="${2:?Missing SHA256}"

FILES=(
    infrastructure-overview.json
    soar-monitoring.json
    security-log-monitoring.json
)

STAGING=""
BACKUP=""
MODIFIED=0

cleanup() {
    if [[ -n "$STAGING" && -d "$STAGING" ]]; then
        rm -rf "$STAGING"
    fi
}

rollback() {
    local code=$?
    trap - ERR

    if [[ "$MODIFIED" -eq 1 ]]; then
        echo "Deployment failed. Restoring previous dashboards."

        for name in "${FILES[@]}"; do
            if [[ -f "$BACKUP/$name" ]]; then
                cp -f "$BACKUP/$name" "$DEST/$name"
            else
                rm -f "$DEST/$name"
            fi

            rm -f "$DEST/.$name.new"
        done
    fi

    echo "Deployment failed with exit code $code"
    exit "$code"
}

trap cleanup EXIT
trap rollback ERR

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Deployment must run as root"
    exit 1
fi

if [[ ! -d "$DEST" ]]; then
    echo "Grafana dashboard directory not found"
    exit 1
fi

STAGING="$(mktemp -d /tmp/innovatech-dashboards-XXXXXXXX)"
ARCHIVE="$STAGING/dashboards.zip"

aws s3 cp "$ARTIFACT" "$ARCHIVE" --region "$REGION"

echo "$EXPECTED_SHA  $ARCHIVE" | sha256sum -c -

python3 - "$ARCHIVE" "$STAGING" <<'PY'
import json
import pathlib
import sys
import zipfile

archive = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])

names = [
    "infrastructure-overview.json",
    "soar-monitoring.json",
    "security-log-monitoring.json",
]

with zipfile.ZipFile(archive) as package:
    for name in names:
        source = f"deploy/monitoring/grafana/dashboards/{name}"
        content = package.read(source)
        dashboard = json.loads(content)

        if not isinstance(dashboard, dict):
            raise ValueError(f"Invalid dashboard: {name}")

        if not dashboard.get("uid"):
            raise ValueError(f"Missing dashboard UID: {name}")

        if not isinstance(dashboard.get("panels"), list):
            raise ValueError(f"Invalid dashboard panels: {name}")

        (destination / name).write_bytes(content)

print("Dashboard package validation passed")
PY

BACKUP="$(mktemp -d "$BASE/.dashboard-backup-XXXXXXXX")"

for name in "${FILES[@]}"; do
    if [[ -f "$DEST/$name" ]]; then
        cp -p "$DEST/$name" "$BACKUP/$name"
    fi
done

MODIFIED=1

for name in "${FILES[@]}"; do
    install -m 644 "$STAGING/$name" "$DEST/.$name.new"
    mv -f "$DEST/.$name.new" "$DEST/$name"

    cmp "$STAGING/$name" "$DEST/$name"
    echo "Deployed $name"
done

echo "All Grafana dashboards deployed successfully"
echo "Backup: $BACKUP"
