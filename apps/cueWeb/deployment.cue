package cuewebapp

deployment: {
	apiVersion: "apps/v1"
	kind:       "Deployment"
	metadata: {
		name:      deployment.name
		namespace: namespace
		labels:    deployment.labels
	}
	spec: {
		replicas: deployment.replicas
		selector: {
			matchLabels: deployment.labels
		}
		template: {
			metadata: {
				labels: deployment.labels
			}
			spec: {
				containers: [{
					name:  deployment.container.name
					image: deployment.container.image
					ports: [{
						containerPort: deployment.container.ports[0]
					}]
				}]
			}
		}
	}
}
