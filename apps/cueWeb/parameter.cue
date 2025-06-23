package k8s

parameters: {
  name:       string | *"sample-app"
  namespace:  string | *"dn-cueweb"
  image:      string | *"nginx:latest"
  replicas:   int    | *2
  nodePort:   int    | *32100
}