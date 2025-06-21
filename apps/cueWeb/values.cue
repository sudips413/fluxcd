package cuewebapp

// Namespace name
namespace: "dn-cueweb"

// Deployment spec
deployment: {
  name: "web-app"
  replicas: 1
  labels: {
    app: "web-app"
  }
  container: {
    name:  "web"
    image: "httpd:2.4"
    ports: [80]
  }
}

// Service spec
service: {
  name: "web-app"
  type: "LoadBalancer" // ClusterIP, LoadBalancer, NodePort
  selector: {
    app: "web-app"
  }
  ports: [{
    port:       80
    targetPort: 80
  }]
}
