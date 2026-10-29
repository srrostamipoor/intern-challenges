# Challenge 37 — Ansible: Roles and Idempotency

## Scenario

> *"Our playbooks are 400 lines and growing. Three different playbooks copy the same
> 'install Nginx' tasks with slight variations. When we fix a bug in one, we forget
> to fix it in the others. We need to structure this properly."*

Roles are Ansible's way of packaging reusable automation. They enforce a standard
directory layout and let you compose complex playbooks from well-tested building blocks.

---

## What you will build

A structured Ansible project using roles:

```
ansible-roles/
├── roles/
│   ├── common/          # things every server gets (user, ssh, packages)
│   ├── nginx/           # Nginx install + config
│   └── app-deploy/      # deploy a Python app
├── site.yaml            # the top-level playbook — assembles roles
├── inventory/
│   └── hosts.ini
└── README.md
```

---

## Deliverables

```
ansible-roles/
├── roles/
│   ├── common/
│   │   ├── tasks/
│   │   │   └── main.yaml
│   │   ├── vars/
│   │   │   └── main.yaml
│   │   └── defaults/
│   │       └── main.yaml
│   ├── nginx/
│   │   ├── tasks/
│   │   │   └── main.yaml
│   │   ├── handlers/
│   │   │   └── main.yaml
│   │   ├── templates/
│   │   │   └── nginx.conf.j2
│   │   └── defaults/
│   │       └── main.yaml
│   └── app-deploy/
│       ├── tasks/
│       │   └── main.yaml
│       ├── files/
│       │   └── app.py
│       └── defaults/
│           └── main.yaml
├── site.yaml
├── inventory/
│   └── hosts.ini
└── README.md
```

---

## Functional requirements

### 1. Role: common — applied to every server

`roles/common/defaults/main.yaml`:
```yaml
deploy_user: deploy
deploy_group: deploy
ssh_port: 22
```

`roles/common/tasks/main.yaml`:
```yaml
---
- name: Update apt cache
  apt:
    update_cache: true
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name:
      - curl
      - vim
      - git
      - htop
      - ufw
    state: present

- name: Create deploy user
  user:
    name: "{{ deploy_user }}"
    group: "{{ deploy_group | default(deploy_user) }}"
    shell: /bin/bash
    create_home: true
    state: present

- name: Configure UFW — allow SSH
  ufw:
    rule: allow
    port: "{{ ssh_port }}"
    proto: tcp

- name: Enable UFW
  ufw:
    state: enabled
    policy: deny
```

### 2. Role: nginx — Nginx install + Jinja2 config template

`roles/nginx/defaults/main.yaml`:
```yaml
nginx_port: 80
server_name: "localhost"
upstream_host: "127.0.0.1"
upstream_port: 8080
```

`roles/nginx/templates/nginx.conf.j2` — note: Jinja2 template, not a static file:
```nginx
server {
    listen {{ nginx_port }};
    server_name {{ server_name }};

    location / {
        proxy_pass http://{{ upstream_host }}:{{ upstream_port }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

`roles/nginx/tasks/main.yaml`:
```yaml
---
- name: Install Nginx
  apt:
    name: nginx
    state: present

- name: Deploy Nginx config from template
  template:                              # ← renders Jinja2 template with variables
    src: nginx.conf.j2
    dest: /etc/nginx/sites-available/{{ server_name }}
    owner: root
    group: root
    mode: "0644"
  notify: Reload Nginx

- name: Enable site
  file:
    src: /etc/nginx/sites-available/{{ server_name }}
    dest: /etc/nginx/sites-enabled/{{ server_name }}
    state: link
  notify: Reload Nginx

- name: Remove default Nginx site
  file:
    path: /etc/nginx/sites-enabled/default
    state: absent
  notify: Reload Nginx

- name: Ensure Nginx is running
  service:
    name: nginx
    state: started
    enabled: true
```

`roles/nginx/handlers/main.yaml`:
```yaml
---
- name: Reload Nginx
  service:
    name: nginx
    state: reloaded    # reload = re-reads config without dropping connections
```

### 3. Role: app-deploy

`roles/app-deploy/defaults/main.yaml`:
```yaml
app_dir: /opt/app
app_port: 8080
```

`roles/app-deploy/files/app.py`:
```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "deployed by ansible"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

`roles/app-deploy/tasks/main.yaml`:
```yaml
---
- name: Install Python and pip
  apt:
    name:
      - python3
      - python3-pip
    state: present

- name: Create app directory
  file:
    path: "{{ app_dir }}"
    state: directory
    owner: "{{ deploy_user }}"
    mode: "0755"

- name: Install Flask
  pip:
    name: flask
    state: present

- name: Deploy app file
  copy:
    src: app.py
    dest: "{{ app_dir }}/app.py"
    owner: "{{ deploy_user }}"
    mode: "0644"

- name: Create systemd unit for the app
  copy:
    content: |
      [Unit]
      Description=Python App
      After=network.target

      [Service]
      User={{ deploy_user }}
      WorkingDirectory={{ app_dir }}
      ExecStart=/usr/bin/python3 {{ app_dir }}/app.py
      Restart=always

      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/myapp.service
    mode: "0644"
  notify: Restart app

- name: Enable and start app
  systemd:
    name: myapp
    state: started
    enabled: true
    daemon_reload: true
```

### 4. site.yaml — the top-level playbook

```yaml
---
# Apply 'common' role to all servers
- name: Common configuration
  hosts: servers
  become: true
  roles:
    - common

# Apply nginx + app to web servers
- name: Web server setup
  hosts: web
  become: true
  roles:
    - role: nginx
      vars:
        server_name: "myapp.example.com"
        upstream_port: 8080
    - app-deploy
```

### 5. Run and verify idempotency

```bash
# First run
ansible-playbook -i inventory/hosts.ini site.yaml

# Second run — all tasks should be 'ok', none 'changed'
ansible-playbook -i inventory/hosts.ini site.yaml

# Run only one role using tags
ansible-playbook -i inventory/hosts.ini site.yaml --tags nginx
```

### 6. `copy` vs `template` — key difference

| Module | What it does |
|---|---|
| `copy` | Copies a file verbatim — no substitution |
| `template` | Renders a Jinja2 `.j2` file — substitutes `{{ variables }}` |

Use `template` when the file content needs to vary per host or environment.
Use `copy` for static files that are identical everywhere.

---

## Guided questions

1. What is the difference between `vars/main.yaml` and `defaults/main.yaml` in a role? Which takes precedence when both define the same variable?
2. The nginx role uses `template` for `nginx.conf.j2` while the app-deploy role uses `copy` for `app.py`. Why the different choice?
3. What is the difference between `service: state: reloaded` and `service: state: restarted`? For Nginx, which is preferred and why?
4. The `site.yaml` applies `common` to all servers and `nginx` only to the `web` group. If you add a new server to the `web` group and run the playbook, which roles run on it?
5. A handler is notified by multiple tasks in the same play. How many times does the handler actually run?

---

## Stretch goals

- Install your role with `ansible-galaxy init myrole` and compare the generated structure to what you wrote by hand
- Add a `meta/main.yaml` to the `nginx` role declaring that it `depends_on` the `common` role — observe how Ansible enforces the order
- Write a `molecule` test (using Molecule + Docker) that verifies the nginx role idempotently installs and configures Nginx

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**What I'd do differently:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — vars vs defaults precedence:**

**Q2 — template vs copy choice:**

**Q3 — reloaded vs restarted:**

**Q4 — new server, which roles run:**

**Q5 — handler notified multiple times:**
