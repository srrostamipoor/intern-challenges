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

**What I built:**
An Ansible project that configures three Docker containers acting as servers (`web1`, `web2`, `db1`)
over SSH: a static inventory with groups (`web`, `db`, and `servers` as a group of groups),
`group_vars` for shared and per-group variables, a playbook that installs Nginx and deploys a
config file with a handler, and a playbook that creates a `deploy` user with a `.ssh` directory
and a NOPASSWD sudoers file. Both playbooks are idempotent: the second run showed `changed=0`
on every host.

**What I struggled with / what I changed from the challenge text:**
- The image `rastasheep/ubuntu-sshd:22.04` does not exist (tags stop at 18.04), and the 18.04 image
  has Python 3.6, which is too old for the ansible-core version I installed (2.20). Modules run
  Python on the *target*, so the target Python must be new enough. I built my own small image from
  `ubuntu:22.04` (`Dockerfile`: openssh-server, python3, root login by password) and used it in
  `docker-compose.yaml`.
- Ansible does not run natively on Windows, so I ran it from WSL2 (Ubuntu). Password SSH needs
  `sshpass` on the control node.
- Recreated containers get new SSH host keys, so I added `-o UserKnownHostsFile=/dev/null` to
  `ansible_ssh_extra_args` (in addition to `StrictHostKeyChecking=no`). This is fine for a throwaway
  lab, not for real servers.
- `copy` does not render `{{ server_name }}`, so the placeholder would be written literally into the
  Nginx config. I used the `template` module instead (Jinja2 is rendered).
- Nginx's default site also listens on port 80, so I removed `sites-enabled/default`.
- The base image has no `sudo`, so `create-user.yaml` first installs it (the sudoers task needs
  `/etc/sudoers.d`). That task failed once because `apt` timed out on the network, so I added
  `retries`/`until` to it.
- `root/root` in `group_vars/all.yaml` is a fake credential for a local throwaway lab. Real
  passwords belong in Ansible Vault or SSH keys, never in a repo.

**changed vs ok — what I observed:**
- First run of `install-nginx.yaml`: `changed` for installing Nginx, writing the config, removing
  the default site, creating the symlink and starting the service; the handler ran once at the end.
  First run of `create-user.yaml`: `changed` for group, user, `.ssh` directory and sudoers file on
  all three hosts.
- Second run of both playbooks: every task `ok`, recap `changed=0`. Nothing was touched and the
  handler did not run.
- `--check --diff` showed what would change without changing it (like `terraform plan`).
- `changed` means Ansible modified the host to reach the desired state; `ok` means the host was
  already in that state.
- Verification: `/health` returned HTTP 200 on the web servers; `nginx` is correctly absent on `db1`
  (it is not in the `web` group). On all three hosts `id deploy` shows uid/gid 1000, `/home/deploy/.ssh`
  is `drwx------` owned by `deploy`, and `/etc/sudoers.d/deploy` contains
  `deploy ALL=(ALL) NOPASSWD:ALL`.

---

## Guided questions — answers

**Q1 — notify and handlers:**
`notify` marks a handler to run if the task reports `changed`. The handler runs once, at the end of the
play, no matter how many tasks notified it. In my runs the handler `Restart Nginx` ran on the first
run (the config changed) and did not run on the second (nothing changed).

**Q2 — state present vs latest:**
`present` installs the package only if it is missing and leaves an installed version alone. `latest`
upgrades it to the newest version whenever one exists. `present` is preferred in production because
runs stay predictable and repeatable: a routine playbook run must not silently upgrade a package
and restart or break a service. Upgrades should be a deliberate, tested change (for example with a
pinned version). *(Reasoning only, I did not run `latest`.)*

**Q3 — task vs handler:**
A task runs every time (and reports ok/changed). A handler is a task that runs only when notified by
a task that changed, and only once at the end of the play. Yes, several tasks can notify the same
handler. In my Nginx playbook three tasks (config, removing the default site, enabling the site)
notify `Restart Nginx`, and it still restarts only once.

**Q4 — become: true:**
It makes Ansible run the task with elevated privileges (root by default) after connecting as the
normal user. The default mechanism is `sudo` (`become_method: sudo`; others such as `su` are possible).
In this lab I connect as `root`, so it changes nothing, but it is the correct habit for real servers.

**Q5 — changed twice means:**
On an immediate second run the same task should show `ok`. If it shows `changed` again, the module is
not idempotent or does not know the real state. Typical cases are `command`/`shell` tasks (Ansible
cannot know what they did unless `creates:` or `changed_when:` is set). Proper modules like `apt`,
`user`, `file` and `template` compare the current state with the desired state first. In my runs all
tasks used such modules and the second run was `changed=0`.
