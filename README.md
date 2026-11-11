# Intern Challenges â€” DevOps Roadmap Practice

Hands-on, implementation-based challenges completed as part of my DevOps internship. Each challenge is self-contained in its own folder with a README explaining the task, what I built, and what I learned.

---

## Phase 1 â€” Networking & Version Control

- `01-networking/`
  - `tcp-udp/` â€” Challenge 1: TCP vs UDP
  - `dns/` â€” Challenge 2: DNS resolution
  - `http-https/` â€” Challenge 3: HTTP/HTTPS
  - `load-balancing/` â€” Challenge 4: Load balancing
  - `ssh/` â€” Challenge 5: SSH
  - `firewalls/` â€” Challenge 6: Firewalls & ports
- `02-git/`
  - `branching/` â€” Challenge 7: Branching strategy
  - `merge-vs-rebase/` â€” Challenge 8: Merge vs rebase
  - `collaboration/` â€” Challenge 9: Collaboration workflow
  - `recovery/` â€” Challenge 10: Recovery tools

## Phase 2 â€” Python Scripting & YAML/JSON

- `03-python-scripting/`
  - `uptime-monitor/` â€” Challenge 11: Website uptime checker with email alerts
  - `log-parser/` â€” Challenge 12: Parse Nginx access logs, surface top errors & IPs
  - `api-health/` â€” Challenge 13: Authenticate with GitHub API, parse JSON, alert on bad state
  - `deploy-notifier/` â€” Challenge 14: Run shell commands from Python, post webhook result
- `04-yaml-json/`
  - `jq-workout/` â€” Challenge 15: Slice and dice real API JSON with `jq`
  - `k8s-manifests/` â€” Challenge 16: Write Kubernetes YAML manifests by hand
  - `yaml-validator/` â€” Challenge 17: Find and fix bugs in broken YAML files
  - `github-actions-pipeline/` â€” Challenge 18: Real CI pipeline â€” lint â†’ test â†’ build â†’ push â†’ notify

## Phase 3 â€” Core DevOps Tooling

- `05-containers/`
  - `dockerfile-basics/` â€” Challenge 19: Write your first Dockerfile
  - `layers-and-cache/` â€” Challenge 20: Layers, cache, and image size
  - `volumes-and-mounts/` â€” Challenge 21: Volumes and bind mounts
  - `container-networking/` â€” Challenge 22: Container networking
  - `compose-multi-service/` â€” Challenge 23: Docker Compose multi-service app
  - `compose-secrets/` â€” Challenge 24: Compose secrets and config management
  - `container-healthchecks/` â€” Challenge 25: Container health checks
  - `docker-cleanup/` â€” Challenge 26: Docker cleanup and resource management
- `06-cicd/`
  - `pipeline-stages/` â€” Challenge 27: lint â†’ test â†’ build â†’ deploy, and why that order matters
  - `triggers/` â€” Challenge 28: push, PR, schedule, and manual triggers
  - `secrets-in-ci/` â€” Challenge 29: secrets management in CI â€” never hardcoding credentials
  - `artifact-management/` â€” Challenge 30: build once, promote through environments
  - `pipeline-caching/` â€” Challenge 31: speeding up pipelines with dependency caching
  - `full-deploy-pipeline/` â€” Challenge 32: test on PR, auto-deploy on merge to main
- `07-iac/`
  - `tf-basics/` â€” Challenge 33: Terraform providers, resources, and state files
  - `tf-variables-modules/` â€” Challenge 34: variables, outputs, and reusable modules
  - `tf-plan-apply/` â€” Challenge 35: plan vs apply, state locking, drift detection
  - `ansible-playbooks/` â€” Challenge 36: Ansible playbooks, inventories, and idempotency
  - `ansible-roles/` â€” Challenge 37: roles, templates, handlers, and structure
  - `tf-ansible-combo/` â€” Challenge 38: Terraform provisions, Ansible configures â€” the full combo

---

## Progress

### Phase 1
- [x] Challenge 1 â€” TCP vs UDP
- [x] Challenge 2 â€” DNS resolution
- [x] Challenge 3 â€” HTTP/HTTPS
- [x] Challenge 4 â€” Load balancing
- [x] Challenge 5 â€” SSH
- [x] Challenge 6 â€” Firewalls & ports
- [x] Challenge 7 â€” Branching strategy
- [x] Challenge 8 â€” Merge vs rebase
- [x] Challenge 9 â€” Collaboration workflow
- [x] Challenge 10 â€” Recovery tools

### Phase 2
- [x] Challenge 11 â€” Uptime monitor
- [x] Challenge 12 â€” Log parser
- [x] Challenge 13 â€” API health checker
- [x] Challenge 14 â€” Deploy notifier
- [x] Challenge 15 â€” jq workout
- [x] Challenge 16 â€” K8s manifests by hand
- [x] Challenge 17 â€” YAML debugger
- [x] Challenge 18 â€” GitHub Actions pipeline

### Phase 3 â€” Docker
- [x] Challenge 19 â€” Dockerfile basics
- [x] Challenge 20 â€” Layers, cache, and image size
- [x] Challenge 21 â€” Volumes and bind mounts
- [x] Challenge 22 â€” Container networking
- [x] Challenge 23 â€” Docker Compose multi-service app
- [x] Challenge 24 â€” Compose secrets and config management
- [x] Challenge 25 â€” Container health checks
- [x] Challenge 26 â€” Docker cleanup and resource management

### Phase 3 â€” CI/CD
- [x] Challenge 27 â€” Pipeline stages
- [x] Challenge 28 â€” Triggers
- [x] Challenge 29 â€” Secrets management in CI
- [ ] Challenge 30 â€” Artifact management
- [ ] Challenge 31 â€” Pipeline caching
- [ ] Challenge 32 â€” Full deploy pipeline

### Phase 3 â€” Infrastructure as Code
- [ ] Challenge 33 â€” Terraform basics
- [ ] Challenge 34 â€” Terraform variables and modules
- [ ] Challenge 35 â€” Terraform plan, apply, and drift
- [ ] Challenge 36 â€” Ansible playbooks and inventories
- [ ] Challenge 37 â€” Ansible roles and idempotency
- [ ] Challenge 38 â€” Terraform + Ansible combo

---

## How to read this repo

Each challenge folder contains its own `README.md` with the full write-up.
Start there to see what I did and why for that specific challenge.
