# Challenge 16 — Write Kubernetes-Style YAML by Hand

## Scenario

> *"Before you ever touch a real cluster, you need to be able to read and write Kubernetes manifests
> fluently. Write the YAML for a small 3-resource application — from scratch, no generator, no Helm."*

Writing YAML by hand for K8s before you know K8s sounds backwards, but it's not —
it forces you to understand YAML structure deeply, and when you do reach Kubernetes, you'll
recognize everything instead of copy-pasting mystery files.

---

## What you will write

Three YAML manifests for a hypothetical "todo-api" application:

| File | Kubernetes resource | What it represents |
|---|---|---|
| `configmap.yaml` | `ConfigMap` | App configuration as key/value pairs |
| `deployment.yaml` | `Deployment` | How to run the container |
| `service.yaml` | `Service` | How to expose the container on the network |

---

## Deliverables

```
k8s-manifests/
├── configmap.yaml
├── deployment.yaml
├── service.yaml
├── all-in-one.yaml     # all three combined with --- separator
└── README.md           # this file + your write-up
```

---

## The YAML you must write

### 1. `configmap.yaml`

A ConfigMap that stores:
- `APP_ENV: production`
- `LOG_LEVEL: info`
- `MAX_CONNECTIONS: "100"`
- A multi-line value `BANNER` containing a 3-line ASCII banner of your choice

Requirements:
- `apiVersion: v1`
- `kind: ConfigMap`
- `metadata.name: todo-api-config`
- `metadata.namespace: default`
- `metadata.labels` must include `app: todo-api` and `version: "1.0"`
- Use the `|` block scalar for the multi-line BANNER value

### 2. `deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-api
  namespace: default
  labels:
    app: todo-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: todo-api       # must match template labels exactly
  template:
    metadata:
      labels:
        app: todo-api
    spec:
      containers:
        - name: todo-api
          image: todo-api:1.0.0
          ports:
            - containerPort: 8080
          env:
            # Load every key from the ConfigMap as an environment variable
            - name: APP_ENV
              valueFrom:
                configMapKeyRef:
                  name: todo-api-config
                  key: APP_ENV
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: todo-api-config
                  key: LOG_LEVEL
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "128Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
```

Write this out yourself — do not copy-paste. Understand every line.

### 3. `service.yaml`

A `ClusterIP` service that:
- Targets pods with label `app: todo-api`
- Exposes port 80
- Forwards to port 8080 on the pod (`targetPort`)
- Has `metadata.name: todo-api-svc`

### 4. `all-in-one.yaml`

Combine all three documents into one file using YAML's multi-document separator:

```yaml
# configmap
---
apiVersion: v1
kind: ConfigMap
...
---
# deployment
apiVersion: apps/v1
kind: Deployment
...
---
# service
apiVersion: v1
kind: Service
...
```

---

## Validate your YAML

```bash
# Install yamllint
pip install yamllint

# Validate
yamllint all-in-one.yaml

# If you have kubectl available (not required):
kubectl apply --dry-run=client -f all-in-one.yaml
```

---

## YAML syntax you must demonstrate

| Concept | Where to use it in this challenge |
|---|---|
| Mapping (key: value) | Everywhere |
| Sequence (list with `-`) | `containers:`, `ports:`, `env:` |
| Nested mappings | `spec.template.spec.containers[0].resources` |
| Multi-line string with `\|` | ConfigMap BANNER value |
| Quoted strings | `"100"` in MAX_CONNECTIONS, `"1.0"` in labels |
| Comments (`#`) | At least 5 meaningful comments in your files |

---

## Guided questions

1. In the Deployment, `selector.matchLabels` must exactly match `template.metadata.labels`. What breaks if they don't match?
2. What is the difference between `|` and `>` in YAML multi-line strings?
3. Why is `"100"` (quoted) different from `100` (unquoted) in YAML? Why does it matter for ConfigMaps?
4. What does `---` at the top of a YAML file mean? Is it required?
5. In `resources.requests.cpu`, what does `100m` mean? What about `500m`?

---

## Write-up

**What I found confusing at first:**

**YAML quirks I ran into:**

**What I'd add next:**
