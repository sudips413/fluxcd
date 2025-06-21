from flask import Flask, render_template, jsonify
from kubernetes import client, config
import os

app = Flask(__name__)

# Strictly load kubeconfig with context "docker-desktop" or raise error
try:
    config.load_kube_config(context="docker-desktop")
except Exception as e:
    raise RuntimeError("❌ Failed to load kube config with context 'docker-desktop'") from e

custom_api = client.CustomObjectsApi()

NAMESPACE = "flux-system"
KUSTOMIZATION_NAME = "web-app"
GROUP = "kustomize.toolkit.fluxcd.io"
VERSION = "v1"
PLURAL = "kustomizations"

@app.route("/")
def index():
    return render_template("index.html")  # ensure index.html is in /templates

@app.route("/cluster-status", methods=["GET"])
def cluster_status():
    try:
        # Step 1: Get the Kustomization custom resource object
        kustomization = custom_api.get_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,           # This is where your Kustomization CR lives, e.g. flux-system
            plural=PLURAL,
            name=KUSTOMIZATION_NAME
        )
        
        # Step 2: Extract targetNamespace from spec (where the managed resources are)
        target_namespace = kustomization.get("spec", {}).get("targetNamespace")
        if not target_namespace:
            # Fallback to default namespace if not specified (can adjust as needed)
            target_namespace = NAMESPACE
        
        # Step 3: Initialize Kubernetes Core and Apps API clients
        core_v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        
        # Step 4: Query pods, services, deployments, etc. from target_namespace
        pods = core_v1.list_namespaced_pod(namespace=target_namespace)
        services = core_v1.list_namespaced_service(namespace=target_namespace)
        deployments = apps_v1.list_namespaced_deployment(namespace=target_namespace)
        replicasets = apps_v1.list_namespaced_replica_set(namespace=target_namespace)
        statefulsets = apps_v1.list_namespaced_stateful_set(namespace=target_namespace)
        
        # Serialization helpers (same as before)
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
        
        # Step 5: Build response JSON including Kustomization status and managed namespace
        kustomization_status = kustomization.get("status", {})
        
        return jsonify({
            "status": "success",
            "kustomizationName": KUSTOMIZATION_NAME,
            "kustomizationNamespace": NAMESPACE,
            "managedNamespace": target_namespace,
            "kustomizationStatus": kustomization_status,
            "pods": [serialize_pod(p) for p in pods.items],
            "services": [serialize_service(s) for s in services.items],
            "deployments": [serialize_deployment(d) for d in deployments.items],
            "replicasets": [serialize_replicaset(r) for r in replicasets.items],
            "statefulsets": [serialize_statefulset(s) for s in statefulsets.items]
        }), 200

    except Exception as e:
        print("❌ Cluster status error:", str(e))
        return jsonify({"status": "error", "message": f"Exception: {str(e)}"}), 500


@app.route("/deploy", methods=["POST"])
def deploy():
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
            name=KUSTOMIZATION_NAME,
            body=patch
        )
        print("✅ Deployment triggered")
        return jsonify({"status": "success", "message": "Deployment triggered! See it in the Flux UI"}), 200
    except Exception as e:
        print("❌ Deployment error:", str(e))
        return jsonify({"status": "error", "message": f"Exception: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
