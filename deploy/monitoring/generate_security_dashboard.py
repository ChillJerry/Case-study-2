
"""Generate the Innovatech Security Log Monitoring dashboard."""

import json
from pathlib import Path

OUTPUT = Path(
    "deploy/monitoring/grafana/dashboards/"
    "security-log-monitoring.json"
)

LOKI = {"type": "loki", "uid": "loki"}
panels = []


def target(query, instant=False):
    return {
        "refId": "A",
        "expr": query,
        "queryType": "instant" if instant else "range",
        "instant": instant,
        "maxLines": 100,
    }


def add_row(panel_id, title, y):
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": title,
        "collapsed": False,
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 1},
        "panels": [],
    })


def add_stat(panel_id, title, query, x, y, width=6,
             color="blue", description=""):
    panels.append({
        "id": panel_id,
        "type": "stat",
        "title": title,
        "description": description,
        "datasource": LOKI,
        "gridPos": {"x": x, "y": y, "w": width, "h": 5},
        "targets": [target(query, instant=True)],
        "options": {
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
            "orientation": "auto",
            "textMode": "value",
            "colorMode": "value",
            "graphMode": "area",
        },
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "decimals": 0,
                "color": {
                    "mode": "fixed",
                    "fixedColor": color,
                },
            },
            "overrides": [],
        },
    })


def add_timeseries(panel_id, title, query, x, y,
                   width=12, height=8, legend="Events"):
    panels.append({
        "id": panel_id,
        "type": "timeseries",
        "title": title,
        "datasource": LOKI,
        "gridPos": {
            "x": x, "y": y, "w": width, "h": height,
        },
        "targets": [{
            **target(query),
            "legendFormat": legend,
        }],
        "options": {
            "legend": {
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {"mode": "multi"},
        },
        "fieldConfig": {
            "defaults": {
                "unit": "none",
                "min": 0,
                "decimals": 0,
                "custom": {
                    "drawStyle": "bars",
                    "lineWidth": 1,
                    "fillOpacity": 55,
                    "showPoints": "never",
                    "axisPlacement": "auto",
                },
            },
            "overrides": [],
        },
    })


def add_logs(panel_id, title, query, x, y,
             width=24, height=9):
    panels.append({
        "id": panel_id,
        "type": "logs",
        "title": title,
        "datasource": LOKI,
        "gridPos": {
            "x": x, "y": y, "w": width, "h": height,
        },
        "targets": [target(query)],
        "options": {
            "showTime": True,
            "showLabels": False,
            "showCommonLabels": False,
            "wrapLogMessage": True,
            "enableLogDetails": True,
            "sortOrder": "Descending",
        },
        "fieldConfig": {
            "defaults": {},
            "overrides": [],
        },
    })


# Loki log streams
firewall = '{job="onprem-firewall"} |= "INNOVATECH_FW_DROP"'
auth = '{job="aws-monitoring-auth"}'
syslog = '{job="aws-monitoring"}'

ssh_failures = (
        auth +
        ' |~ "(?i)(failed password|invalid user|authentication failure)"'
)

system_warnings = (
        syslog +
        ' |~ "(?i)(warning|error|failed|critical)"'
)


# --------------------------------------------------
# Section 1: Security overview
# --------------------------------------------------

add_row(1, "01 | Security Operations Overview", 0)

add_stat(
    2,
    "Firewall Drop Events",
    f"sum(count_over_time({firewall} [$__range])) or vector(0)",
    0, 1,
    color="red",
    description="Firewall log entries in the selected time range.",
)

add_stat(
    3,
    "SSH Authentication Failures",
    f"sum(count_over_time({ssh_failures} [$__range])) or vector(0)",
    6, 1,
    color="yellow",
    description="Matching authentication log entries, not unique login attempts.",
)

add_stat(
    4,
    "System Warning / Error Events",
    f"sum(count_over_time({system_warnings} [$__range])) or vector(0)",
    12, 1,
    color="orange",
    description="System log lines matching warning or error keywords.",
)

add_stat(
    5,
    "Authentication Log Entries",
    f"sum(count_over_time({auth} [$__range])) or vector(0)",
    18, 1,
    color="blue",
    description="Total AWS Monitoring authentication log entries.",
)


# --------------------------------------------------
# Section 2: Firewall traffic analysis
# --------------------------------------------------

add_row(6, "02 | Firewall Threat and Traffic Analysis", 6)

add_timeseries(
    7,
    "Blocked Traffic Over Time",
    f"sum(count_over_time({firewall} [$__interval]))",
    0, 7, width=24,
    legend="Firewall drops",
)

add_timeseries(
    8,
    "Blocked Traffic by Source IP",
    'topk(10, sum by (src_ip) ('
    f'count_over_time({firewall} '
    '| regexp "SRC=(?P<src_ip>[0-9.]+)" '
    '[$__interval])))',
    0, 15,
    legend="{{src_ip}}",
)

add_timeseries(
    9,
    "Blocked Traffic by Destination Port",
    'topk(10, sum by (dst_port) ('
    f'count_over_time({firewall} '
    '| regexp "DPT=(?P<dst_port>[0-9]+)" '
    '[$__interval])))',
    12, 15,
    legend="Port {{dst_port}}",
)


# --------------------------------------------------
# Section 3: Authentication monitoring
# --------------------------------------------------

add_row(10, "03 | Linux Authentication Monitoring", 23)

add_timeseries(
    11,
    "SSH Authentication Failures Over Time",
    f"sum(count_over_time({ssh_failures} [$__interval]))",
    0, 24, width=24,
    legend="Authentication failures",
)

add_logs(
    12,
    "Recent Authentication Security Events",
    ssh_failures,
    0, 32,
)


# --------------------------------------------------
# Section 4: System health and audit
# --------------------------------------------------

add_row(13, "04 | Linux System and Audit Logs", 41)

add_timeseries(
    14,
    "System Warnings and Errors Over Time",
    f"sum(count_over_time({system_warnings} [$__interval]))",
    0, 42, width=24,
    legend="Warnings and errors",
)

add_logs(
    15,
    "Recent System Warnings and Errors",
    system_warnings,
    0, 50,
)


# --------------------------------------------------
# Section 5: Firewall event investigation
# --------------------------------------------------

add_row(16, "05 | Firewall Security Event Investigation", 59)

add_logs(
    17,
    "Recent Firewall Drop Events",
    firewall,
    0, 60,
    height=11,
)


# --------------------------------------------------
# Dashboard configuration
# --------------------------------------------------

dashboard = {
    "id": None,
    "uid": "innovatech-security-logs",
    "title": "Innovatech | Security Log Monitoring",
    "description": (
        "Hybrid-cloud security monitoring using "
        "nftables, Linux logs, Grafana Alloy and Loki."
    ),
    "tags": [
        "innovatech",
        "security",
        "loki",
        "firewall",
        "authentication",
        "hybrid-cloud",
    ],
    "timezone": "browser",
    "schemaVersion": 41,
    "version": 2,
    "editable": False,
    "refresh": "15s",
    "time": {
        "from": "now-6h",
        "to": "now",
    },
    "panels": panels,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

OUTPUT.write_text(
    json.dumps(dashboard, indent=2),
    encoding="utf-8",
)

print("Dashboard created:", OUTPUT)
print("Total dashboard elements:", len(panels))
print("Loki datasource:", LOKI["uid"])
