package k8s

import "encoding/yaml"

// Namespace definition
namespace: {
  apiVersion: "v1"
  kind:       "Namespace"
  metadata: {
    name: "dn-cueweb"
  }
}

// Deployment definition
deployment: {
  apiVersion: "apps/v1"
  kind:       "Deployment"
  metadata: {
    name:      "sample-app"
    namespace: "dn-cueweb"
  }
  spec: {
    replicas: 2
    selector: matchLabels: app: "sample"
    template: {
      metadata: labels: app: "sample"
      spec: containers: [{
        name:  "sample"
        image: "nginx:latest"
        ports: [{ containerPort: 80 }]
      }]
    }
  }
}

// Service definition (NodePort)
service: {
  apiVersion: "v1"
  kind:       "Service"
  metadata: {
    name:      "sample-service"
    namespace: "dn-cueweb"
  }
  spec: {
    type: "NodePort"
    selector: app: "sample"
    ports: [{
      port:       80
      targetPort: 80
      nodePort:   32100
    }]
  }
}

// Marshal all resources to YAML
output: yaml.Marshal([namespace, deployment, service])
