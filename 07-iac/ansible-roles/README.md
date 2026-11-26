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

**What I built:**
An Ansible project with three roles: `common` (packages, `deploy` group and user, UFW), `nginx`
(install, Jinja2 config template, reload handler) and `app-deploy` (Python/Flask app behind Nginx).
`site.yaml` has two plays: `common` runs on every server (`servers`), `nginx` and `app-deploy` run only
on the `web` group. I ran it against the three Docker "servers" from challenge 36 (same inventory,
`Dockerfile` and `docker-compose.yaml` are in `../ansible-playbooks`). Tags (`common`, `nginx`, `app`) let
me run a single role.

**What I changed from the challenge text, and why:**
- The challenge's `common` role creates the user with `group: deploy` but never creates the group, so the `user`
  module would fail. I added a `group` task.
- `vars/main.yaml` is listed in the deliverables but has no content. I used it for `common_packages`
  (an internal constant) and kept `defaults/main.yaml` for values a user may override.
- `deploy_user` was only defined in the defaults of `common`, but `app-deploy` runs in the second play where
  `common` is not loaded, so the variable did not exist there. I defined it in `inventory/group_vars/all.yaml`.
- The `app-deploy` tasks notify a handler `Restart app` that is not defined anywhere. I added `handlers/main.yaml`.
- `--tags nginx` needs `tags:` on the roles in `site.yaml`; I added them.
- Containers have no systemd and no real firewall, so I skip both UFW tasks with
  `when: ansible_facts['virtualization_type'] != "docker"`. The systemd unit file is still written; the app is
  started with `start-stop-daemon` when the service manager is not systemd. These branches are only exercised
  in containers: the UFW tasks and the systemd branch were never executed.
- `install_recommends: false` on the Python install (otherwise `python3-pip` pulls a compiler toolchain), and
  `retries`/`until` on apt installs because of an unreliable network.
- I added `add_header X-Served-By {{ inventory_hostname }};` to the Nginx template as a visible per-host value.

**What I struggled with:**
- The network was very slow (about 78 kB/s for package lists), so `apt` tasks took minutes. Pressing Ctrl+C on the
  control node does not stop the `apt` process already running in the container; it kept the apt lock and later
  runs failed with "Could not get lock". After an interrupted run I restarted the containers.
- `cache_valid_time` only checks the time of the last update, not whether the package lists are complete. After an
  interrupted update, the task said `ok` but `apt` then failed with "No package matching 'curl' is available".
  Running `apt-get update` by hand fixed it.
- `--check` (dry run) failed on "Enable site" in the very first run: in check mode the
  config file is not really created, so the symlink target does not exist. It is a limit of check mode, not a bug.
- My first container fallback (`start-stop-daemon --exec /usr/bin/python3`) was not idempotent: every run showed
  `changed`, because the running process is `python3.10` and did not match `--exec`. It also overwrote the pid
  file with the pid of a second instance that died (port 8080 was already in use). Matching by pid file only
  (`--startas` instead of `--exec`) fixed it; the second run then showed `changed=0`.

**What I'd do differently:**
Use a container image with systemd (or a VM) so the real systemd and UFW paths can be tested, bake the common
packages into the image or use a local apt cache to avoid downloading the same packages three times, and add a
Molecule test for the `nginx` role. I did not do the stretch goals (`ansible-galaxy init`, `meta` dependencies, Molecule).

**Idempotency — what I observed:**
- First full run: `changed` for packages, group, user, Nginx install/config/link/default-site removal/start,
  Python and Flask install, app files and app start. `db1` only got the `common` role (`ok=5`).
- Second run: every task `ok`, `changed=0` on all three hosts. The UFW tasks and the systemd task showed `skipping`.
- Change test: after adding one line to the template, `--diff` showed exactly that line for each host, the handler
  `Reload Nginx` ran once per host, and the next run was `changed=0` again.
- The site answers through Nginx: `/health` returns `200 ok`, and `/` returns the Flask JSON
  `{"status": "deployed by ansible"}` with header `X-Served-By: web1` or `web2`. Before the app role was added,
  `/` returned `502 Bad Gateway` because nothing listened on port 8080.

---

## Guided questions — answers

**Q1 — vars vs defaults precedence:**
`defaults/main.yaml` has the lowest precedence of all variables: it is the place for values a user of the role is
expected to override (inventory, `group_vars`, play or role `vars:`, `-e`). `vars/main.yaml` has a much higher
precedence (higher than inventory and play vars; only extra vars `-e` and a few others beat it), so it is for
internal constants that should not be overridden. When both define the same variable, **`vars` wins**.
Observed for defaults: `nginx` has `server_name: localhost` in defaults, `site.yaml` passes
`server_name: "myapp.example.com"` and the config file really was created as
`/etc/nginx/sites-available/myapp.example.com`. The precedence of `vars/main.yaml` itself I did not test; that part
is from the documentation.

**Q2 — template vs copy choice:**
`nginx.conf.j2` contains placeholders (`{{ server_name }}`, port, upstream) and may differ per host or
environment, so it must be rendered with `template`. `app.py` is the same on every server and has no Jinja2
placeholders, so `copy` (verbatim) is enough, and it also avoids Jinja2 interpreting braces in code. Observed:
with the `X-Served-By {{ inventory_hostname }}` line, web1 answered `web1` and web2 answered `web2` from the same template.

**Q3 — reloaded vs restarted:**
`reloaded` makes Nginx re-read its configuration while the master process keeps running and old workers finish
their requests, so there is no dropped connection. `restarted` stops the process and starts it again, which
gives a short downtime and cuts open connections. For Nginx `reload` is preferred for config changes (ideally after
checking the config with `nginx -t`). Observed: the `Reload Nginx` handler worked in the containers; I did not
measure dropped connections.

**Q4 — new server in `web`, which roles run:**
All three. Play 1 targets `servers`, which includes `web` through `[servers:children]`, so `common` runs; play 2
targets `web`, so `nginx` and `app-deploy` run. Consistent with what I saw: `db1` (in `db`, not in `web`) only
received `common` (`ok=5`). I did not add a fourth server.

**Q5 — handler notified by multiple tasks:**
Once per host, at the end of the play, even if several tasks reported `changed`. In my first full run three Nginx
tasks (template, enable site, remove default site) all notified `Reload Nginx` and the handler ran once per host.
If no task changes anything, it does not run at all (second run).
