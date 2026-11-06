
#!/usr/bin/env bash
set -Eeuo pipefail

BASE="/opt/innovatech/monitoring"
DEST="$BASE/grafana/dashboards"
PROM_DEST="$BASE/prometheus/prometheus.yml"
REGION="eu-central-1"

ARTIFACT="${1:?Missing artifact URI}"
EXPECTED_SHA="${2:?Missing SHA256}"

STAGING=""
BACKUP=""
MODIFIED=0
PROM_MODIFIED=0
FILES=()

cleanup() {
    if [[ -n "$STAGING" && -d "$STAGING" ]]; then
        rm -rf "$STAGING"
    fi
}

rollback() {
    local code=$?
    trap - ERR
    set +e

    if [[ "$MODIFIED" -eq 1 ]]; then
        echo "Deployment failed; restoring previous configuration"

        for name in "${FILES[@]}"; do
            if [[ -f "$BACKUP/$name" ]]; then
                cp -p "$BACKUP/$name" "$DEST/$name"
            else
                rm -f "$DEST/$name"
            fi
            rm -f "$DEST/.$name.new"
        done

        if [[ "$PROM_MODIFIED" -eq 1 ]]; then
            cp -p "$BACKUP/prometheus.yml" "$PROM_DEST"
            (
                cd "$BASE"
                docker compose restart prometheus
            ) || true
        fi

        (
            cd "$BASE"
            docker compose restart grafana
        ) || true
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

if [[ ! -f "$PROM_DEST" ]]; then
    echo "Prometheus configuration not found"
    exit 1
fi

# Check Prometheus before changing anything.
(
    cd "$BASE"
    docker compose exec -T prometheus promtool --version >/dev/null
)

STAGING="$(mktemp -d /tmp/innovatech-monitoring-XXXXXXXX)"
ARCHIVE="$STAGING/monitoring.zip"

aws s3 cp "$ARTIFACT" "$ARCHIVE" --region "$REGION"

echo "$EXPECTED_SHA  $ARCHIVE" | sha256sum -c -

# Extract and validate the dashboard JSON files.
python3 - "$ARCHIVE" "$STAGING" <<'PY'
import json
from pathlib import Path
import sys
import zipfile

archive = Path(sys.argv[1])
destination = Path(sys.argv[2])

prefix = "deploy/monitoring/grafana/dashboards/"
config_path = "deploy/monitoring/prometheus/prometheus.yml"

with zipfile.ZipFile(archive) as package:
    names = sorted(
        entry[len(prefix):]
        for entry in package.namelist()
        if entry.startswith(prefix)
        and entry.endswith(".json")
        and "/" not in entry[len(prefix):]
    )

    if not names:
        raise ValueError("No dashboard JSON files in package")

    uids = set()

    for name in names:
        content = package.read(prefix + name)
        dashboard = json.loads(content.decode("utf-8-sig"))

        if not isinstance(dashboard, dict):
            raise ValueError(f"Invalid dashboard: {name}")

        uid = dashboard.get("uid")

        if (
            not uid
            or uid in uids
            or not isinstance(dashboard.get("panels"), list)
        ):
            raise ValueError(f"Invalid dashboard UID or panels: {name}")

        uids.add(uid)
        (destination / name).write_bytes(content)

    config = package.read(config_path)

    if not config.strip():
        raise ValueError("Empty prometheus.yml")

    (destination / "prometheus.yml").write_bytes(config)

    (destination / "dashboard-names.txt").write_text(
        "\n".join(names) + "\n"
    )

print(f"Validated {len(names)} dashboards and Prometheus package")
PY

mapfile -t FILES < "$STAGING/dashboard-names.txt"

# Back up the current configuration.
BACKUP="$(mktemp -d "$BASE/.monitoring-backup-XXXXXXXX")"

for name in "${FILES[@]}"; do
    if [[ -f "$DEST/$name" ]]; then
        cp -p "$DEST/$name" "$BACKUP/$name"
    fi
done

cp -p "$PROM_DEST" "$BACKUP/prometheus.yml"

# Deploy every packaged dashboard.
MODIFIED=1

for name in "${FILES[@]}"; do
    install -m 644 "$STAGING/$name" "$DEST/.$name.new"
    mv -f "$DEST/.$name.new" "$DEST/$name"

    cmp "$STAGING/$name" "$DEST/$name"

    echo "Deployed $name"
done

# Update Prometheus in place because it is bind-mounted
# as an individual file in Docker Compose.
PROM_MODIFIED=1

cp "$STAGING/prometheus.yml" "$PROM_DEST"
cmp "$STAGING/prometheus.yml" "$PROM_DEST"

# Validate the new configuration before restarting.
(
    cd "$BASE"
    docker compose exec -T prometheus \
        promtool check config /etc/prometheus/prometheus.yml
)

# Restart Prometheus to load the new scrape jobs.
(
    cd "$BASE"
    docker compose restart prometheus
)

# Verify that Prometheus becomes healthy.
healthy=0

for attempt in {1..12}; do
    if (
        cd "$BASE"
        docker compose exec -T prometheus \
            promtool check ready \
                --url=http://localhost:9090 >/dev/null 2>&1
    ); then
        healthy=1
        break
    fi

    sleep 5
done

if [[ "$healthy" -ne 1 ]]; then
    echo "Prometheus did not become healthy"
    false
fi

# Restart Grafana so newly provisioned dashboards appear.
(
    cd "$BASE"
    docker compose restart grafana
)

echo "All ${#FILES[@]} dashboards deployed successfully"
echo "Prometheus configuration deployed and checked"
echo "Backup: $BACKUP"
