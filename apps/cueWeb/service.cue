service: {
  apiVersion: "v1"
  kind: "Service"
  metadata: {
    name: values.name
    namespace: values.namespace
  }
  spec: {
    selector: values.selector
    ports: values.ports
    type: values.type
  }
}
