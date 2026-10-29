# Challenge 36 — Ansible: Playbooks and Inventories

## Scenario

> *"We have 10 servers. Every time we need to install Nginx or update a config file,
> someone SSHes into each one manually. It takes an hour and we always miss one.
> We need a way to run the same tasks on all of them at once — and know it worked."*

Ansible automates the configuration of existing servers. Unlike Terraform, which creates
infrastructure, Ansible configures what's already there — installing packages, writing
config files, starting services, creating users.

---

## What you will build

A set of Ansible playbooks targeting **local Docker containers** (so you don't need real servers):

1. An inventory that defines your "servers" (Docker containers acting as hosts)
2. A playbook that installs Nginx and deploys a custom config
3. A second playbook that creates a user and sets up their home directory

---

## Deliverables

```
ansible-playbooks/
├── inventory/
│   ├── hosts.ini          # static inventory
│   └── group_vars/
│       ├── all.yaml       # variables for all hosts
│       └── web.yaml       # variables for the 'web' group
├── playbooks/
│   ├── install-nginx.yaml
│   └── create-user.yaml
├── files/
│   └── nginx.conf         # the config file to deploy
├── docker-compose.yaml    # spin up fake "servers" as containers
└── README.md
```

---

## Functional requirements

### 1. Install Ansible

```bash
pip install ansible
ansible --version
```

### 2. Fake servers with Docker Compose

Instead of real VMs, use containers as SSH targets:

`docker-compose.yaml`:

```yaml
services:
  web1:
    image: rastasheep/ubuntu-sshd:22.04
    container_name: web1
    ports:
      - "2221:22"

  web2:
    image: rastasheep/ubuntu-sshd:22.04
    container_name: web2
    ports:
      - "2222:22"

  db1:
    image: rastasheep/ubuntu-sshd:22.04
    container_name: db1
    ports:
      - "2223:22"
```

```bash
docker compose up -d
# Default credentials for rastasheep/ubuntu-sshd: root / root
ssh root@localhost -p 2221   # verify it works
```

### 3. inventory/hosts.ini — static inventory

```ini
# Web servers group
[web]
web1 ansible_host=localhost ansible_port=2221
web2 ansible_host=localhost ansible_port=2222

# Database servers group
[db]
db1  ansible_host=localhost ansible_port=2223

# 'servers' is a group-of-groups containing both
[servers:children]
web
db
```

### 4. inventory/group_vars/all.yaml — variables for every host

```yaml
# Ansible connection settings for all hosts
ansible_user: root
ansible_password: root
ansible_ssh_extra_args: "-o StrictHostKeyChecking=no"

# App-level variables
app_name: "myapp"
app_user: "deploy"
```

### 5. playbooks/install-nginx.yaml — install and configure Nginx

```yaml
---
- name: Install and configure Nginx on web servers
  hosts: web          # targets only the 'web' group
  become: true        # sudo

  vars:
    nginx_port: 80
    server_name: "myapp.example.com"

  tasks:

    - name: Update apt cache
      apt:
        update_cache: true
        cache_valid_time: 3600    # don't update if cache is < 1 hour old

    - name: Install Nginx
      apt:
        name: nginx
        state: present    # 'present' = install if missing, do nothing if already there

    - name: Deploy custom nginx config
      copy:
        src: ../files/nginx.conf
        dest: /etc/nginx/sites-available/myapp
        owner: root
        group: root
        mode: "0644"
      notify: Restart Nginx    # only restart if this task changed something

    - name: Enable site
      file:
        src: /etc/nginx/sites-available/myapp
        dest: /etc/nginx/sites-enabled/myapp
        state: link

    - name: Ensure Nginx is started and enabled
      service:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Restart Nginx
      service:
        name: nginx
        state: restarted
```

### 6. files/nginx.conf — the config to deploy

```nginx
server {
    listen 80;
    server_name {{ server_name }};

    location / {
        return 200 'Hello from Ansible-configured Nginx\n';
        add_header Content-Type text/plain;
    }

    location /health {
        return 200 'ok\n';
        add_header Content-Type text/plain;
    }
}
```

### 7. playbooks/create-user.yaml

```yaml
---
- name: Create deploy user on all servers
  hosts: servers
  become: true

  tasks:

    - name: Create deploy group
      group:
        name: "{{ app_user }}"
        state: present

    - name: Create deploy user
      user:
        name: "{{ app_user }}"
        group: "{{ app_user }}"
        shell: /bin/bash
        home: "/home/{{ app_user }}"
        create_home: true
        state: present

    - name: Create .ssh directory
      file:
        path: "/home/{{ app_user }}/.ssh"
        state: directory
        owner: "{{ app_user }}"
        group: "{{ app_user }}"
        mode: "0700"

    - name: Set up sudoers for deploy user (NOPASSWD)
      copy:
        content: "{{ app_user }} ALL=(ALL) NOPASSWD:ALL\n"
        dest: "/etc/sudoers.d/{{ app_user }}"
        mode: "0440"
```

### 8. Run the playbooks

```bash
# Check connectivity to all hosts
ansible all -i inventory/hosts.ini -m ping

# Dry run (check mode) — see what would change without changing anything
ansible-playbook -i inventory/hosts.ini playbooks/install-nginx.yaml --check

# Apply for real
ansible-playbook -i inventory/hosts.ini playbooks/install-nginx.yaml

# Apply user playbook
ansible-playbook -i inventory/hosts.ini playbooks/create-user.yaml

# Verify from the host
curl http://localhost:2221/   # should return Nginx response (needs port forward adjustment)
```

### 9. Idempotency — run it twice

```bash
# Run the nginx playbook again immediately
ansible-playbook -i inventory/hosts.ini playbooks/install-nginx.yaml
```

Observe the output — every task should show `ok` (unchanged), not `changed`.
That's **idempotency**: running a playbook twice produces the same result as running it once.

This is the core principle of Ansible. Document what "changed" vs "ok" means in your write-up.

---

## Guided questions

1. In the Nginx playbook, the `copy` task has `notify: Restart Nginx`. What does `notify` do, and when does the handler actually run?
2. `state: present` vs `state: latest` for the `apt` module — what is the difference and why is `present` usually preferred in production?
3. What is the difference between a `task` and a `handler`? Can you notify the same handler from multiple tasks?
4. What does `become: true` do? What is the Linux privilege escalation mechanism it uses by default?
5. You run the playbook and a task shows `changed`. You run it again immediately. What should the same task show? If it shows `changed` again, what does that tell you about the module used?

---

## Stretch goals

- Use a **dynamic inventory** script that generates the host list from `docker ps` output
- Add a `when:` condition to skip the Nginx install if the server is in the `db` group
- Write a `pre_tasks` block that checks disk space and fails early if less than 1GB is free

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**changed vs ok — what I observed:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — notify and handlers:**

**Q2 — state present vs latest:**

**Q3 — task vs handler:**

**Q4 — become: true:**

**Q5 — changed twice means:**
