# Scenario 2: Drift Demo

**Drift** = the real infrastructure no longer matches what Terraform has in its state and code,
because something was changed *outside* Terraform.
`terraform plan` finds it: it first **refreshes** (reads the real resources, `Refreshing state...`),
then compares the result with the code. The code is the source of truth.

Setup: `aws_s3_bucket.assets` (`myapp-dev-assets`) and `aws_security_group.web`, running on Floci
(a local AWS emulator). Baseline: `terraform plan` -> `No changes.`

## Direction 1: something was ADDED by hand

The challenge uses `aws s3api put-bucket-tagging`. The AWS CLI was not available here, so I sent
the same S3 API call over HTTP to the emulator:

    curl.exe -i -X PUT "http://localhost:4566/myapp-dev-assets?tagging" -H "Content-Type: application/xml" --data-binary "@tagging.xml"

This added the tag `ManualTag = AddedByHand`. (PutBucketTagging replaces the whole tag set, so the
three existing tags were sent again together with the new one.)

`terraform plan` detected it:

    ~ tags = {
        - "ManualTag" = "AddedByHand" -> null
      }
    Plan: 0 to add, 1 to change, 0 to destroy.

Terraform plans to remove the tag that is not in the code. `terraform apply` -> `1 changed`;
the next `terraform plan` -> `No changes.` Reading the tags back showed only the tags from the code.

## Direction 2: something was DELETED by hand

I deleted the bucket directly in the emulator (like clicking "Delete" in the console):

    curl.exe -i -X DELETE "http://localhost:4566/myapp-dev-assets"    # 204 No Content

`terraform plan` showed:

    aws_s3_bucket.assets: Refreshing state... [id=myapp-dev-assets]
    # aws_s3_bucket.assets will be created
    Plan: 1 to add, 0 to change, 0 to destroy.

The state said the bucket existed, but the refresh found nothing, so Terraform dropped it from its
picture and planned to create it again, because the code still declares it. The security group was
not touched. `terraform apply` -> `1 added`; the next plan -> `No changes.`; the new bucket carried
the tags from the code.

Important: Terraform re-creates the *resource*, not the *data inside it*. The bucket was empty here;
a full bucket deleted by hand would come back empty.

## Not drift: changing the code
Adding a tag in `main.tf` (e.g. `NewTag`) is a normal change, not drift: the plan shows `~ update in-place`
and `apply` rolls it out. Drift is only a change that happened outside Terraform.

## How to resolve drift
| Situation | Resolution |
|---|---|
| The manual change was a mistake | `terraform apply` puts reality back to match the code |
| The manual change should stay | Write it into the code, then `plan` shows no changes |
| A resource was deleted by hand and should stay deleted | Remove it from the code |
| A resource exists in real infra but not in code/state | `terraform import` (to be demonstrated) |
