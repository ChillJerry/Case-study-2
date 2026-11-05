
import ast
import json
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data" / "soar-viewer" / "latest.json"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

STEPS = [
    ("Collect firewall logs", "app/soar/log_analyzer.py", "fetch_firewall_logs"),
    ("Normalize firewall packets", "app/soar/log_analyzer.py", "parse_firewall_log"),
    ("Detect suspicious activity", "app/soar/log_analyzer.py", "detect_suspicious_activity"),
    ("Create SOAR alert", "app/soar/log_response.py", "finding_to_alert"),
    ("Validate and process alert", "app/soar/main.py", "receive_alerts"),
    ("Evaluate security rule", "app/soar/rules.py", "evaluate_event"),
    ("Check duplicate alert", "app/soar/dedup.py", "is_processed"),
    ("Execute response actions", "app/soar/actions.py", "execute_actions"),
]

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SOAR Execution Inspector</title>
<style>
:root {
    font-family: system-ui, Arial, sans-serif;
    color: #e5e7eb;
    background: #0f172a;
}
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 1240px; padding: 28px; }
h1 { margin: 0 0 6px; }
p, .muted { color: #94a3b8; }
.panel {
    background: #172033;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
    margin: 14px 0;
}
textarea {
    width: 100%;
    min-height: 110px;
    background: #0b1220;
    color: #e5e7eb;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 12px;
}
button {
    cursor: pointer;
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 8px;
    padding: 10px 14px;
}
button:hover { background: #1d4ed8; }
.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}
.step {
    display: block;
    width: 100%;
    text-align: left;
    background: #25334c;
    margin: 7px 0;
}
.step:hover { background: #334155; }
pre {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #0b1220;
    padding: 14px;
    border-radius: 8px;
    font-size: 12px;
    max-height: 510px;
    overflow: auto;
}
.tag {
    display: inline-block;
    padding: 4px 8px;
    background: #334155;
    border-radius: 7px;
}
code { color: #93c5fd; }
label { display: block; margin-bottom: 7px; }
summary { cursor: pointer; font-weight: 600; }
.success { color: #86efac; }
.warning { color: #fcd34d; }
@media (max-width: 800px) {
    .grid { grid-template-columns: 1fr; }
    body { padding: 12px; }
}
</style>
</head>
<body>
<h1>SOAR Execution Inspector</h1>

<section class="panel">
<form method="post" action="/import">
<label for="payload">
Paste the JSON output from
<code>python -m app.soar.log_response --execute</code>
</label>
<textarea name="payload" id="payload" required></textarea>
<p><button type="submit">Import execution result</button></p>
</form>
{% if error %}
<p class="warning">{{ error }}</p>
{% endif %}
</section>

{% if data %}
<div class="grid">
<section class="panel">
<h2>Analysis</h2>
<p>Mode: <span class="tag">{{ data.mode }}</span></p>
<p>Raw logs examined: <b>{{ data.analysis.raw_logs_examined }}</b></p>
<p>Normalized TCP events: <b>{{ data.analysis.normalized_tcp_events }}</b></p>
<p>Findings: <b>{{ data.analysis.findings_count }}</b></p>
</section>
<section class="panel">
<h2>Execution results</h2>
<p>Response summaries: <b>{{ data.execution_traces|length }}</b></p>
<p>Containment is not proven by viewing an incident.
Inspect the action result below.</p>
</section>
</div>

{% for incident in incidents %}
<section class="panel">
<h2>{{ incident.finding.classification }}</h2>
<p>
<span class="tag">{{ incident.finding.severity }}</span>
{{ incident.finding.source_ip }} → {{ incident.finding.destination_ip }}
</p>
<div class="grid">
<div>
<p>Blocked TCP attempts: <b>{{ incident.finding.blocked_attempts }}</b></p>
<p>Targeted ports:
<b>{{ incident.finding.destination_ports|join(', ') }}</b></p>
<p>Detection reason: {{ incident.finding.reason }}</p>
<p>Recommended action: {{ incident.finding.recommended_action }}</p>
</div>
<div>
<p>SOAR response status:
<b>{{ incident.trace.status if incident.trace else 'Not executed / not imported' }}</b>
</p>
<p>Containment:
<b>{{ incident.trace.containment if incident.trace else incident.finding.containment }}</b>
</p>
{% if incident.trace %}
{% for step in incident.trace.steps %}
<p>
{{ step.step }}:
<span class="success">{{ step.status }}</span>
— {{ step.details }}
</p>
{% endfor %}
{% endif %}
</div>
</div>
<details>
<summary>Original firewall evidence</summary>
{% for line in incident.finding.evidence %}
<pre>{{ line }}</pre>
{% endfor %}
</details>
</section>
{% endfor %}
{% endif %}

<section class="panel">
<h2>Inspect actual Python functions</h2>
<div class="grid">
<div>
{% for step in steps %}
<button class="step" onclick="showCode({{ loop.index0 }})">
{{ loop.index }}. {{ step[0] }}
<small>{{ step[1] }} · {{ step[2] }}()</small>
</button>
{% endfor %}
</div>
<div>
<h3 id="source-title">Select a processing step</h3>
<pre id="source">Source code appears here.</pre>
</div>
</div>
</section>

<script>
async function showCode(index) {
    const title = document.getElementById("source-title");
    const output = document.getElementById("source");
    output.textContent = "Loading...";
    try {
        const response = await fetch("/code/" + index);
        const data = await response.json();
        if (!response.ok) {
            throw Error(data.error || "Unable to load code");
        }
        title.textContent = data.path + " : " + data.function + "()";
        output.textContent = data.source;
    } catch (error) {
        output.textContent = error.message;
    }
}
</script>
</body>
</html>
"""


def valid_payload(data):
    if not isinstance(data, dict):
        return False

    if data.get("mode") not in {"preview", "execute"}:
        return False

    analysis = data.get("analysis")

    if not isinstance(analysis, dict):
        return False

    if not isinstance(analysis.get("findings"), list):
        return False

    if not isinstance(data.get("execution_traces"), list):
        return False

    return all(
        isinstance(item, dict)
        for item in analysis["findings"]
    )


def read_saved():
    if not STORE.is_file():
        return None

    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None

    return data if valid_payload(data) else None


def render(error=None):
    data = read_saved()
    incidents = []

    if data:
        traces = data["execution_traces"]

        for index, finding in enumerate(data["analysis"]["findings"]):
            trace = traces[index] if index < len(traces) else None

            incidents.append({
                "finding": finding,
                "trace": trace,
            })

    return render_template_string(
        PAGE,
        data=data,
        incidents=incidents,
        steps=STEPS,
        error=error,
    )


@app.get("/")
def index():
    return render()


@app.post("/import")
def import_result():
    try:
        data = json.loads(request.form.get("payload", ""))
    except ValueError:
        return render("Invalid JSON. Paste the complete JSON result."), 400

    if not valid_payload(data):
        return render(
            "Expected SOAR log_response JSON with analysis and execution_traces."
        ), 400

    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return render()


@app.get("/code/<int:index>")
def code(index):
    if index >= len(STEPS):
        return jsonify(error="Unknown processing step"), 404

    _, path, function = STEPS[index]
    file = ROOT / path

    if not file.is_file():
        return jsonify(error=f"File not found: {path}"), 404

    text = file.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)

    nodes = list(tree.body)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            nodes.extend(node.body)

    target = next(
        (
            node for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name == function
        ),
        None,
    )

    if target is None:
        return jsonify(error=f"Function not found: {function}"), 404

    lines = text.splitlines()

    source = "\n".join(
        lines[target.lineno - 1:target.end_lineno]
    )

    return jsonify(
        path=path,
        function=function,
        source=source,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5050,
        debug=False,
    )
