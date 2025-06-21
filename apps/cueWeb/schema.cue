package cuewebapp

namespace: string | *"dn-cueweb"

deployment: {
	name:     string | *"web-app"
	replicas: int & >=1 & <=10 | *1
	labels:   [string]: string | *"web-app"
	container: {
		name:  string | *"web"
		image: string | *"httpd:2.4"
		ports: [...int] | *[80]
	}
}

service: {
	name:     string | *"web-app"
	type:     "ClusterIP" | "LoadBalancer" | "NodePort" | *"LoadBalancer"
	selector: [string]: string | *"web-app"
	ports: [...{
		port:       int & >=1 & <=65535
		targetPort: int & >=1 & <=65535
	}] | *[{
		port:       80
		targetPort: 80
	}]
}
