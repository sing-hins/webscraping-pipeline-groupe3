cat > api/app.py << 'EOF'
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import os

app = Flask(__name__)

# Monitoring Prometheus — expose les métriques sur /metrics
metrics = PrometheusMetrics(app)

@app.route("/")
def index():
    return jsonify({
        "message": "Observatoire des Prix Cacao & Café",
        "status": "running",
        "version": "1.0.0"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF
