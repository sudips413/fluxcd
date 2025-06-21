from flask import Flask, render_template, jsonify, request
from kubernetes import client, config
import os

app = Flask(__name__)

# Load kube config with specific context
try:
    config.load_kube_config(context="docker-desktop")
except Exception as e:
    raise RuntimeError("❌ Failed to load kube config with context 'docker-desktop'") from e

custom_api = client.CustomObjectsApi()

# Constants
NAMESPACE = "flux-system"
GROUP = "kustomize.toolkit.fluxcd.io"
VERSION = "v1"
PLURAL = "kustomizations"

# Home route (serves HTML UI)
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/edit", methods=["POST"])
def edit_kustomization():
    data = request.get_json()
    name = data.get("name")
    patch_spec = data.get("patch", {})

    if not name or not patch_spec:
        return jsonify({"status": "error", "message": "Missing 'name' or 'patch'"}), 400

    try:
        patch = {"spec": patch_spec}
        custom_api.patch_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL,
            name=name,
            body=patch
        )
        return jsonify({"status": "success", "message": f"Kustomization {name} updated."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# List all platforms (Flux Kustomizations)
@app.route("/platforms", methods=["GET"])
def list_platforms():
    try:
        kustomizations = custom_api.list_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL
        )

        platform_list = []
        for item in kustomizations.get("items", []):
            name = item["metadata"]["name"]
            status = item.get("status", {}).get("conditions", [])
            ready_condition = next((c for c in status if c["type"] == "Ready"), {})
            platform_list.append({
                "name": name,
                "targetNamespace": item.get("spec", {}).get("targetNamespace", NAMESPACE),
                "status": ready_condition.get("status", "Unknown"),
                "message": ready_condition.get("message", "")
            })

        return jsonify({"status": "success", "platforms": platform_list}), 200

    except Exception as e:
        print("❌ Error listing platforms:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# Trigger deployment for a selected Kustomization
@app.route("/deploy", methods=["POST"])
def deploy():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"status": "error", "message": "Missing 'name' in request"}), 400

    patch = {
        "spec": {
            "suspend": False,
            "force": True,
        }
    }
    try:
        custom_api.patch_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL,
            name=name,
            body=patch
        )
        print(f"✅ Deployment triggered for {name}")
        return jsonify({"status": "success", "message": f"Deployment triggered for {name}"}), 200
    except Exception as e:
        print("❌ Deployment error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# Cluster status monitoring route
@app.route("/cluster-status", methods=["GET"])
def cluster_status():
    try:
        # Get one of the kustomizations to determine target namespace
        sample = custom_api.get_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL,
            name="web-app"  # fallback to one known kustomization name
        )

        target_namespace = sample.get("spec", {}).get("targetNamespace", NAMESPACE)

        core_v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        pods = core_v1.list_namespaced_pod(namespace=target_namespace)
        services = core_v1.list_namespaced_service(namespace=target_namespace)
        deployments = apps_v1.list_namespaced_deployment(namespace=target_namespace)
        replicasets = apps_v1.list_namespaced_replica_set(namespace=target_namespace)
        statefulsets = apps_v1.list_namespaced_stateful_set(namespace=target_namespace)

        def serialize_pod(pod):
            return {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "containers": [c.name for c in pod.spec.containers],
                "conditions": [{"type": c.type, "status": c.status} for c in (pod.status.conditions or [])]
            }

        def serialize_service(svc):
            return {
                "name": svc.metadata.name,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [f"{p.port}/{p.protocol}" for p in svc.spec.ports]
            }

        def serialize_deployment(dep):
            return {
                "name": dep.metadata.name,
                "replicas": dep.status.replicas or 0,
                "ready_replicas": dep.status.ready_replicas or 0,
                "available_replicas": dep.status.available_replicas or 0
            }

        def serialize_replicaset(rs):
            return {
                "name": rs.metadata.name,
                "replicas": rs.status.replicas or 0,
                "ready_replicas": rs.status.ready_replicas or 0
            }

        def serialize_statefulset(ss):
            return {
                "name": ss.metadata.name,
                "replicas": ss.status.replicas or 0,
                "ready_replicas": ss.status.ready_replicas or 0
            }

        return jsonify({
            "status": "success",
            "targetNamespace": target_namespace,
            "pods": [serialize_pod(p) for p in pods.items],
            "services": [serialize_service(s) for s in services.items],
            "deployments": [serialize_deployment(d) for d in deployments.items],
            "replicasets": [serialize_replicaset(r) for r in replicasets.items],
            "statefulsets": [serialize_statefulset(s) for s in statefulsets.items]
        }), 200

    except Exception as e:
        print("❌ Cluster status error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
