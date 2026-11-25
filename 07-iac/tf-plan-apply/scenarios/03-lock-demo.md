# Scenario 3: State Lock Demo

## Why state locking exists
`apply` writes the state file. If two runs write it at the same time, one can overwrite the other's
changes or corrupt the state. So Terraform takes a **lock** before it reads or writes the state, and
releases it when the command ends. A second run that finds the lock stops with an error instead of waiting
for nothing or racing the first one.

## How I simulated it
I added a slow resource that sleeps for 45 seconds while it is created, so the first `apply` holds the lock
for a while. (`terraform_data` is built into Terraform, so no extra provider is needed. The challenge suggests
`null_resource`, which works the same way.)

    resource "terraform_data" "slow_demo" {
      provisioner "local-exec" {
        interpreter = ["PowerShell", "-Command"]
        command     = "Start-Sleep -Seconds 45"
      }
    }

- Terminal 1: `terraform apply` (answered `yes`; the resource started sleeping)
- Terminal 2, at the same time: `terraform plan`

## What I saw in terminal 2

    Error: Error acquiring the state lock

    Error message: Failed to read state file: The state file could not be read: read terraform.tfstate:
    The process cannot access the file because another process has locked a portion of the file.

    Terraform acquires a state lock to protect the state from being written
    by multiple users at the same time. Please resolve the issue above and try
    again. For most commands, you can disable locking with the "-lock=false"
    flag, but this is not recommended.

Notes:
- Even `plan` takes the lock, not only `apply`.
- When terminal 1 finished, the lock was released automatically and `terraform plan` worked again.
- This is the **local backend on Windows**: the lock is an operating-system file lock, so the message has no
  lock ID. With a remote backend (S3 + DynamoDB) the lock is a record in the table and the error normally
  shows lock details such as the lock ID and who holds it. I did not run that variant here.

## Local lock vs remote lock
A local lock only protects against two runs on the **same machine**. A teammate on another laptop would not
see it. For a team, the lock must live in a shared place, such as a DynamoDB table with an S3 backend.

## What `terraform force-unlock <LOCK_ID>` does
It removes a lock that is stuck, using the lock ID shown in the error. It does not change any infrastructure
and does not repair the state. It is only for locks that were left behind, for example when a run crashed or
the network dropped. It asks for confirmation.

## When it is safe, and when it is not
| Safe | Not safe |
|---|---|
| You are sure the run that holds the lock is dead (process gone, CI job finished or cancelled) | The owner may still be running (offline does not mean stopped) |
| You checked the lock info: who, when, which operation | You did not check who holds it |
| After unlocking you run `terraform plan` to see the real situation | You unlock and apply straight away |

If two runs write the state at the same time, the state can be corrupted. After a crashed `apply`, some real
resources may be changed while the state is not updated, so always run `plan` after unlocking.

`-lock=false` skips locking. It is for rare emergencies only, never for normal use.

## How to prevent both problems from the scenario
- Overlapping applies: use a remote backend with locking (S3 + DynamoDB), and let only the CI pipeline run `apply`.
- Manual changes (drift): run `plan` regularly, restrict console access, and review every `plan` before `apply`.
