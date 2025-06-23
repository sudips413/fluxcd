package k8s

import (
  "encoding/yaml"
  "k8s.io/kube" // optional for CRD validation, can be ignored
)

parameters: _

namespace: {
  apiVersion: "v1"
  kind:       "Namespace"
  metadata: name: parameters.namespace
}

deployment: {
  apiVersion: "apps/v1"
  kind:       "Deployment"
  metadata: {
    name:      parameters.name
    namespace: parameters.namespace
  }
  spec: {
    replicas: parameters.replicas
    selector: matchLabels: app: parameters.name
    template: {
      metadata: labels: app: parameters.name
      spec: containers: [{
        name:  parameters.name
        image: parameters.image
        ports: [{ containerPort: 80 }]
      }]
    }
  }
}

service: {
  apiVersion: "v1"
  kind:       "Service"
  metadata: {
    name:      parameters.name + "-svc"
    namespace: parameters.namespace
  }
  spec: {
    type: "NodePort"
    selector: app: parameters.name
    ports: [{
      port:       80
      targetPort: 80
      nodePort:   parameters.nodePort
    }]
  }
}

output: yaml.Marshal([namespace, deployment, service])
