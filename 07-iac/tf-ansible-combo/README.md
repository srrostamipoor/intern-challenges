# Challenge 38 — Terraform + Ansible: The Full IaC Combo

## Scenario

> *"Terraform creates the server. Ansible configures it.
> This is the most common IaC pattern in the industry — and it's your portfolio project."*

Terraform provisions infrastructure (the VPC, the EC2 instance, the security group).
Ansible configures it (installs Nginx, deploys the app, creates the user).
Together they cover the full lifecycle from "no server" to "running application".

---

## What you will build

```
tf-ansible-combo/
├── terraform/
│   ├── main.tf         # VPC, subnet, security group, EC2 instance
│   ├── variables.tf
│   ├── outputs.tf      # outputs: instance public IP for Ansible inventory
│   └── terraform.tfvars
├── ansible/
│   ├── inventory/
│   │   └── hosts.ini   # populated with Terraform output IP
│   ├── roles/
│   │   ├── common/
│   │   ├── nginx/
│   │   └── app-deploy/
│   └── site.yaml
├── run.sh              # orchestrates: terraform apply → update inventory → ansible-playbook
└── README.md
```

**Target:** A server running Nginx (reverse proxy) + Python Flask app, accessible at the public IP.

---

## Deliverables

```
tf-ansible-combo/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
├── ansible/
│   ├── inventory/hosts.ini
│   ├── roles/
│   │   ├── common/tasks/main.yaml
│   │   ├── nginx/tasks/main.yaml
│   │   ├── nginx/templates/nginx.conf.j2
│   │   ├── nginx/handlers/main.yaml
│   │   └── app-deploy/tasks/main.yaml
│   └── site.yaml
├── run.sh
└── README.md
```

---

## Functional requirements

### 1. terraform/main.tf — provision the server

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

# Key pair — Ansible SSHes using this key
resource "aws_key_pair" "deploy" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.ssh_public_key_path)
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "${var.project_name}-vpc" }
}

# Public subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  tags = { Name = "${var.project_name}-public" }
}

# Internet gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

# Route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security group
resource "aws_security_group" "web" {
  name   = "${var.project_name}-web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.your_ip_cidr]    # only your IP can SSH
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instance — Ubuntu 22.04
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]    # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"    # free tier eligible
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name               = aws_key_pair.deploy.key_name

  tags = {
    Name      = "${var.project_name}-server"
    ManagedBy = "terraform"
  }
}
```

### 2. terraform/outputs.tf — pass the IP to Ansible

```hcl
output "instance_public_ip" {
  description = "Public IP of the web server — use this in Ansible inventory"
  value       = aws_instance.web.public_ip
}

output "instance_id" {
  value = aws_instance.web.id
}

output "ssh_command" {
  description = "Ready-to-use SSH command"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_instance.web.public_ip}"
}
```

### 3. run.sh — the orchestration glue

```bash
#!/bin/bash
set -euo pipefail

echo "=== Step 1: Terraform apply ==="
cd terraform
terraform init -input=false
terraform apply -auto-approve

# Get the IP from Terraform output
PUBLIC_IP=$(terraform output -raw instance_public_ip)
echo "Instance IP: $PUBLIC_IP"

echo ""
echo "=== Step 2: Update Ansible inventory ==="
cd ../ansible
cat > inventory/hosts.ini << EOF
[web]
server1 ansible_host=${PUBLIC_IP} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_rsa ansible_ssh_extra_args="-o StrictHostKeyChecking=no"
EOF

echo ""
echo "=== Step 3: Wait for SSH to be available ==="
echo "Waiting for the server to accept SSH connections..."
for i in $(seq 1 30); do
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        -i ~/.ssh/id_rsa ubuntu@${PUBLIC_IP} "echo ready" 2>/dev/null \
        && break || echo "  Attempt $i/30 — retrying in 10s..."
    sleep 10
done

echo ""
echo "=== Step 4: Run Ansible ==="
ansible-playbook -i inventory/hosts.ini site.yaml

echo ""
echo "=== Done! ==="
echo "App running at: http://${PUBLIC_IP}"
echo "SSH:           ssh -i ~/.ssh/id_rsa ubuntu@${PUBLIC_IP}"
```

### 4. ansible/site.yaml

```yaml
---
- name: Base server setup
  hosts: web
  become: true
  roles:
    - common

- name: Deploy web stack
  hosts: web
  become: true
  roles:
    - role: nginx
      vars:
        server_name: "{{ ansible_host }}"
        upstream_port: 8080
    - app-deploy
```

### 5. End-to-end test

```bash
chmod +x run.sh
./run.sh

# Test from your machine
curl http://<public-ip>/
curl http://<public-ip>/health

# SSH into the server and verify processes
ssh -i ~/.ssh/id_rsa ubuntu@<public-ip>
systemctl status nginx
systemctl status myapp
```

### 6. Tear down cleanly

```bash
cd terraform
terraform destroy -auto-approve
```

---

## The full picture — who does what

| Tool | Responsibility | Creates |
|---|---|---|
| Terraform | Provision | VPC, subnet, security group, EC2 instance, key pair |
| Ansible | Configure | Nginx install, app deploy, user creation, systemd service |

The handoff is the public IP address: Terraform outputs it, `run.sh` writes it into
the Ansible inventory, Ansible connects to it via SSH.

---

## Guided questions

1. `run.sh` runs Ansible immediately after `terraform apply` returns. Is the EC2 instance ready to accept SSH at that point? What does the retry loop in `run.sh` solve?
2. The SSH security group rule allows only `var.your_ip_cidr`. Why is `0.0.0.0/0` for SSH a bad idea even for a dev server?
3. Terraform creates the infrastructure; Ansible configures it. Could you do both with just Ansible? Could you do both with just Terraform? What would you lose in each case?
4. `run.sh` uses `terraform output -raw instance_public_ip` to get the IP. What would break if someone ran `terraform apply` again after the initial deploy (e.g., to add a firewall rule)?
5. The app is deployed as a `systemd` service. What are the advantages of systemd over just running `python3 app.py &` in the background?

---

## Stretch goals

- Generate the Ansible inventory dynamically using `terraform output -json` and a Python script instead of writing it as a heredoc
- Add a second EC2 instance, put a load balancer (ALB) in front, and have Ansible configure both via the `web` inventory group
- Add Terraform provisioners (`remote-exec`) to bootstrap Ansible itself — then invoke `ansible-playbook` from within Terraform (and document why this approach is controversial)

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**The hardest part (SSH timing? Inventory generation? Debugging Ansible on a real VM?):**

**What the server looks like after a full run (processes, ports, files):**

**What I'd add next:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — SSH not immediately ready:**

**Q2 — SSH 0.0.0.0/0 risk:**

**Q3 — Ansible-only vs Terraform-only:**

**Q4 — second terraform apply breaks IP?:**

**Q5 — systemd vs background process:**
