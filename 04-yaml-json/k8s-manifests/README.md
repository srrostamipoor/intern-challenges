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
That selector.matchLabels in the Deployment has to exactly match the template's labels — if they don't match, Kubernetes can't connect the Deployment to its pods. Also the difference between apiVersion values (v1 for ConfigMap/Service, apps/v1 for Deployment) wasn't obvious at first.

**YAML quirks I ran into:**
Indentation has to be exact and uses spaces, never tabs. Quoting matters: "100" must be quoted in a ConfigMap because values have to be strings, not numbers. The | block scalar keeps line breaks for the multi-line banner. Lists use -, maps use key: value.

**What I'd add next:**
I'd try applying these with kubectl --dry-run=client to check them against the real Kubernetes schema, and add more resources like an Ingress.

---

## Guided questions — answers

**Q1 — selector must match template labels:** If selector.matchLabels and template.metadata.labels don't match, the Deployment can't find or manage its own pods — it would fail to connect them, and the deployment wouldn't work correctly.

**Q2 — | vs >:** Both are for multi-line strings. | (literal) keeps the line breaks exactly as written. > (folded) joins the lines into one, replacing newlines with spaces. I used | for the banner so each line stays separate.

**Q3 — "100" vs 100:** In YAML, 100 without quotes is a number (integer), and "100" is a string. It matters for ConfigMaps because all ConfigMap values must be strings — an unquoted number would be invalid.

**Q4 — what --- means:** It marks the start of a YAML document. It lets you put multiple separate documents (ConfigMap, Deployment, Service) in one file, separated by ---. It's not strictly required for a single document, but it's good practice.

**Q5 — 100m and 500m in cpu:** The m means milli (thousandths of a CPU core). 100m = 0.1 of a core, 500m = 0.5 of a core. So requests.cpu 100m asks for a tenth of a core, and limits.cpu 500m caps it at half a core.