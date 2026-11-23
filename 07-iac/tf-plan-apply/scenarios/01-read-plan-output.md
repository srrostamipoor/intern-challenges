# Scenario 1: Reading `terraform plan` Output

Config used: `aws_s3_bucket.assets` (`myapp-dev-assets`) and `aws_security_group.web`,
running against Floci (a local AWS emulator).

## How to read a plan (4 things to check)
1. **The symbol on the left**: `+` create, `~` update in place, `-` destroy, `-/+` destroy and re-create.
2. **The resource address**, e.g. `aws_s3_bucket.assets`. Always read which resource is affected.
3. **`# forces replacement` markers**: the attribute that makes Terraform destroy and re-create.
4. **The summary line**: `Plan: X to add, Y to change, Z to destroy.` An unexpected `destroy` count means stop.

Two levels of symbols: the symbol next to `resource` (e.g. `-/+`) is the action on the whole resource;
the symbols next to attributes (`~` changed value, `+` new value, `-` removed value) describe single fields.

## Example A: create (baseline)
`Plan: 2 to add, 0 to change, 0 to destroy.`

| Output line | Meaning |
|---|---|
| `+ resource "aws_s3_bucket" "assets"` | A new bucket will be created |
| `+ bucket = "myapp-dev-assets"` | Value I set in code |
| `+ arn = (known after apply)` | Value AWS assigns after creation |
| `Changes to Outputs:` | Output values change too (harmless) |
| `Note: You didn't use the -out option...` | The plan is not saved; apply plans again |

After `apply`, a second `terraform plan` printed `No changes.`: code, state and reality match.

## Example B: in-place update (`~`)
Change: added `CostCenter = "engineering"` to `common_tags`.
`Plan: 0 to add, 2 to change, 0 to destroy.`

- `~ update in-place`: the resource is modified, not destroyed.
- Only `+ "CostCenter" = "engineering"` is new; the other tags are shown unchanged
  (`# (3 unchanged elements hidden)`).
- Both the bucket and the security group change because they share `common_tags`.
- Safe: no data is lost.

## Example C: replacement (`-/+`)
Change: `terraform plan -var "environment=prod"` (not applied).
`Plan: 2 to add, 0 to change, 2 to destroy.`

- `-/+ destroy and then create replacement`: the resource is deleted and created again.
- `~ bucket = "myapp-dev-assets" -> "myapp-prod-assets" # forces replacement`:
  a bucket name cannot be changed in place, so Terraform must replace the bucket.
- `~ name = "myapp-dev-sg" -> "myapp-prod-sg" # forces replacement`: same for the security group.
- One variable changed, but two resources would be destroyed, because their names are built from it.

Other lines inside a replacement plan are consequences, not my changes:
- `~ arn = "..." -> (known after apply)`: the old value disappears with the old resource; AWS sets a new one.
- `+ acl = (known after apply)`: the field had no value in the old state; the new resource gets one.
- `- grant {...}` / `~ grant (known after apply)`: default blocks that AWS added to the old bucket are
  removed with it, and the new bucket gets its own defaults.

If this were a database, replacement would delete its data. Always check the `destroy` count.
