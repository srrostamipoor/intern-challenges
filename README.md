# Intern Challenges — DevOps Roadmap Practice

Hands-on, implementation-based challenges completed as part of my DevOps internship. Each challenge is self-contained in its own folder with a README explaining the task, what I built, and what I learned.

---

## Phase 1 — Networking & Version Control

- `01-networking/`
  - `tcp-udp/` — Challenge 1: TCP vs UDP
  - `dns/` — Challenge 2: DNS resolution
  - `http-https/` — Challenge 3: HTTP/HTTPS
  - `load-balancing/` — Challenge 4: Load balancing
  - `ssh/` — Challenge 5: SSH
  - `firewalls/` — Challenge 6: Firewalls & ports
- `02-git/`
  - `branching/` — Challenge 7: Branching strategy
  - `merge-vs-rebase/` — Challenge 8: Merge vs rebase
  - `collaboration/` — Challenge 9: Collaboration workflow
  - `recovery/` — Challenge 10: Recovery tools

## Phase 2 — Python Scripting & YAML/JSON

- `03-python-scripting/`
  - `uptime-monitor/` — Challenge 11: Website uptime checker with email alerts
  - `log-parser/` — Challenge 12: Parse Nginx access logs, surface top errors & IPs
  - `api-health/` — Challenge 13: Authenticate with GitHub API, parse JSON, alert on bad state
  - `deploy-notifier/` — Challenge 14: Run shell commands from Python, post webhook result
- `04-yaml-json/`
  - `jq-workout/` — Challenge 15: Slice and dice real API JSON with `jq`
  - `k8s-manifests/` — Challenge 16: Write Kubernetes YAML manifests by hand
  - `yaml-validator/` — Challenge 17: Find and fix bugs in broken YAML files
  - `github-actions-pipeline/` — Challenge 18: Real CI pipeline — lint → test → build → push → notify

## Phase 3 — Core DevOps Tooling

- `05-containers/`
  - `dockerfile-basics/` — Challenge 19: Write your first Dockerfile
  - `layers-and-cache/` — Challenge 20: Layers, cache, and image size
  - `volumes-and-mounts/` — Challenge 21: Volumes and bind mounts
  - `container-networking/` — Challenge 22: Container networking
  - `compose-multi-service/` — Challenge 23: Docker Compose multi-service app
  - `compose-secrets/` — Challenge 24: Compose secrets and config management
  - `container-healthchecks/` — Challenge 25: Container health checks
  - `docker-cleanup/` — Challenge 26: Docker cleanup and resource management
- `06-cicd/`
  - `pipeline-stages/` — Challenge 27: lint → test → build → deploy, and why that order matters
  - `triggers/` — Challenge 28: push, PR, schedule, and manual triggers
  - `secrets-in-ci/` — Challenge 29: secrets management in CI — never hardcoding credentials
  - `artifact-management/` — Challenge 30: build once, promote through environments
  - `pipeline-caching/` — Challenge 31: speeding up pipelines with dependency caching
  - `full-deploy-pipeline/` — Challenge 32: test on PR, auto-deploy on merge to main
- `07-iac/`
  - `tf-basics/` — Challenge 33: Terraform providers, resources, and state files
  - `tf-variables-modules/` — Challenge 34: variables, outputs, and reusable modules
  - `tf-plan-apply/` — Challenge 35: plan vs apply, state locking, drift detection
  - `ansible-playbooks/` — Challenge 36: Ansible playbooks, inventories, and idempotency
  - `ansible-roles/` — Challenge 37: roles, templates, handlers, and structure
  - `tf-ansible-combo/` — Challenge 38: Terraform provisions, Ansible configures — the full combo

---

## Progress

### Phase 1
- [x] Challenge 1 — TCP vs UDP
- [x] Challenge 2 — DNS resolution
- [x] Challenge 3 — HTTP/HTTPS
- [x] Challenge 4 — Load balancing
- [x] Challenge 5 — SSH
- [x] Challenge 6 — Firewalls & ports
- [x] Challenge 7 — Branching strategy
- [x] Challenge 8 — Merge vs rebase
- [x] Challenge 9 — Collaboration workflow
- [x] Challenge 10 — Recovery tools

### Phase 2
- [ ] Challenge 11 — Uptime monitor
- [ ] Challenge 12 — Log parser
- [ ] Challenge 13 — API health checker
- [ ] Challenge 14 — Deploy notifier
- [ ] Challenge 15 — jq workout
- [ ] Challenge 16 — K8s manifests by hand
- [ ] Challenge 17 — YAML debugger
- [ ] Challenge 18 — GitHub Actions pipeline

### Phase 3 — Docker
- [ ] Challenge 19 — Dockerfile basics
- [ ] Challenge 20 — Layers, cache, and image size
- [ ] Challenge 21 — Volumes and bind mounts
- [ ] Challenge 22 — Container networking
- [ ] Challenge 23 — Docker Compose multi-service app
- [ ] Challenge 24 — Compose secrets and config management
- [ ] Challenge 25 — Container health checks
- [ ] Challenge 26 — Docker cleanup and resource management

### Phase 3 — CI/CD
- [ ] Challenge 27 — Pipeline stages
- [ ] Challenge 28 — Triggers
- [ ] Challenge 29 — Secrets management in CI
- [ ] Challenge 30 — Artifact management
- [ ] Challenge 31 — Pipeline caching
- [ ] Challenge 32 — Full deploy pipeline

### Phase 3 — Infrastructure as Code
- [ ] Challenge 33 — Terraform basics
- [ ] Challenge 34 — Terraform variables and modules
- [ ] Challenge 35 — Terraform plan, apply, and drift
- [ ] Challenge 36 — Ansible playbooks and inventories
- [ ] Challenge 37 — Ansible roles and idempotency
- [ ] Challenge 38 — Terraform + Ansible combo

---

## How to read this repo

Each challenge folder contains its own `README.md` with the full write-up.
Start there to see what I did and why for that specific challenge.