from flask import Flask, render_template, jsonify
from kubernetes import client, config
from datetime import datetime
import os

app = Flask(__name__)

# Load kubeconfig (assumes running locally with ~/.kube/config or in-cluster)
try:
    config.load_kube_config()
except:
    config.load_incluster_config()

custom_api = client.CustomObjectsApi()

NAMESPACE = "flux-system"
KUSTOMIZATION_NAME = "web-app"
GROUP = "kustomize.toolkit.fluxcd.io"
VERSION = "v1beta2"
PLURAL = "kustomizations"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/deploy", methods=["POST"])
def deploy():
    now = datetime.utcnow().isoformat() + "Z"
    patch = {
        "spec": {
            "force": now
        }
    }
    try:
        custom_api.patch_namespaced_custom_object(
            GROUP,
            VERSION,
            NAMESPACE,
            PLURAL,
            KUSTOMIZATION_NAME,
            patch,
            _content_type="application/merge-patch+json"
        )
        return jsonify({"status": "success", "message": "Deployment triggered!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
