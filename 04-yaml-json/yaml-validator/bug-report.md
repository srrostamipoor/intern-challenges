# Bug Report — Challenge 17: YAML Debugger

Four of the listed items (compose Bug 3, k8s Bugs 1, 2 and 4) are not real errors;
they are documented honestly below.

---

## broken/pipeline.yaml (GitHub Actions)

## Bug 1 — Extra space before `branches`
**File:** broken/pipeline.yaml
**Line:** 4
**Type:** Indentation
**Symptom:** yamllint: `wrong indentation: expected 4 but found 5`.
**Root cause:** `branches` under `push:` has 5 spaces, but the same key under `pull_request:` has 4. YAML uses indentation to decide nesting, so siblings must match.
**Fix:** Use 4 spaces before `branches`.

## Bug 2 — `python-version` not indented under `with`
**File:** broken/pipeline.yaml
**Line:** 17
**Type:** Indentation (semantic)
**Symptom:** The file is valid YAML, so yamllint stays quiet. But GitHub rejects the workflow, because `python-version` becomes a key of the step instead of an input of the action, and `with:` is empty.
**Root cause:** `python-version` is at the same level as `with:`. It must be one level deeper, inside `with:`.
**Fix:** Indent `python-version: "3.11"` by 2 more spaces.

## Bug 3 — Inconsistent indentation inside the `run` block
**File:** broken/pipeline.yaml
**Line:** 22
**Type:** Style
**Symptom:** None that stops the run. In a `|` block, extra indentation is kept, so the line becomes ` pip install pytest` with a leading space.
**Root cause:** The second command has 11 spaces while the first has 10.
**Fix:** Make both lines use 10 spaces.

## Bug 4 — Tab character before `DOCKER_PASS`
**File:** broken/pipeline.yaml
**Line:** 34
**Type:** Syntax
**Symptom:** yamllint: `found character '\t' that cannot start any token`. It is invisible in most editors.
**Root cause:** The YAML spec does not allow tabs for indentation; only spaces. The line mixes 10 spaces and a tab.
**Fix:** Remove the tab; keep 10 spaces so `DOCKER_PASS` lines up with `DOCKER_USER`. Found with `cat -A ... | grep '\^I'`.

## Bug 5 — Only 1 extra space of indentation inside `run`
**File:** broken/pipeline.yaml
**Line:** 46-47
**Type:** Style
**Symptom:** Valid YAML (a block scalar only needs to be deeper than its parent), so no error. But it is inconsistent with the rest of the file.
**Root cause:** The `run: |` block content is indented by 1 space; the file uses 2.
**Fix:** Indent both lines by 2 spaces under `run:`.

## Bug 6 — Missing closing quote in the JSON payload
**File:** broken/pipeline.yaml
**Line:** 55
**Type:** Syntax (inside embedded JSON)
**Symptom:** yamllint does not see it, because the payload is inside a `|` block, which YAML treats as plain text. The Slack action would fail when it tries to parse the JSON.
**Root cause:** `"channel: "#devops"` has a quote that is never closed. YAML cannot check the content of a literal block; only the JSON parser can.
**Fix:** `"channel": "#devops"`.

## Bug 7 — Missing colon after `if`, and an invalid expression
**File:** broken/pipeline.yaml
**Line:** 60
**Type:** Syntax
**Symptom:** yamllint: `could not find expected ':'` (reported at the end of the file, line 64).
**Root cause:** `if` is a key, so it needs `key: value`. Also, `github.always()` does not exist; the GitHub Actions function is `always()`.
**Fix:** `if: always()`.

## Bug 8 — Tabs mixed with spaces
**File:** broken/pipeline.yaml
**Line:** 34 (same line as Bug 4)
**Type:** Syntax
**Symptom:** Same as Bug 4.
**Root cause:** The README lists this as a separate bug, but it is the same tab as Bug 4, described as a rule: never mix tabs and spaces in YAML.
**Fix:** Same as Bug 4. To prevent it: use `.editorconfig` with `indent_style = space`.

---

## broken/compose.yaml (Docker Compose)

## Bug 1 — `interval` indented too deep
**File:** broken/compose.yaml
**Line:** 39
**Type:** Indentation
**Symptom:** PyYAML: `expected <block end>, but found '<block mapping start>'` at line 38-39.
**Root cause:** `interval` is indented under `test`, but `test` already has a list value. `interval`, `timeout` and `retries` must be siblings of `test`.
**Fix:** Align `interval: 10s` with `test:`, `timeout:` and `retries:`.

## Bug 2 — Missing colon after `backend` network
**File:** broken/compose.yaml
**Line:** 47
**Type:** Syntax
**Symptom:** The `networks:` mapping becomes invalid, because `backend` is a bare word, not a `key:`. (The README puts the comment on the `volumes:` line, but the bug is on line 47.)
**Root cause:** A key in a mapping must end with `:`, even when it has no value (`frontend:` has one).
**Fix:** `backend:`.

## Bug 3 — "api has no healthcheck but db depends on service_healthy" (README claim)
**File:** broken/compose.yaml
**Line:** 25-27, 36-41
**Type:** Not a real bug (README is reversed)
**Symptom:** None.
**Root cause:** `api` depends on `db` with `service_healthy`, and `db` DOES have a healthcheck, so this part is correct. The real issue is the opposite direction, which is Bug 4.
**Fix:** No change for this item.

## Bug 4 — `web` depends on `api`, but `api` has no healthcheck
**File:** broken/compose.yaml
**Line:** 12-13 and 25-33
**Type:** Logic
**Symptom:** `web` starts as soon as the `api` container starts, not when the API is ready, so requests can fail at startup.
**Root cause:** Short-form `depends_on` only waits for the container to start. There is also no healthcheck on `api` that `web` could wait for.
**Fix:** Add a `healthcheck` to `api` and change `web` to `depends_on: api: condition: service_healthy`. (The `curl` health URL is an assumption; it needs `curl` in the image and a `/health` endpoint.)

## Bug 5 — Mixed `environment` styles
**File:** broken/compose.yaml
**Line:** 17-19 and 31-34
**Type:** Style
**Symptom:** None; both forms are valid.
**Root cause:** `api` uses a list (`- KEY=VAL`) and `db` uses a map (`KEY: VAL`).
**Fix:** Standardized on the map form. I chose it because it is easier to read and merge. `DEBUG` is quoted (`"false"`) so it stays a string instead of becoming a boolean.

---

## broken/k8s-job.yaml (Kubernetes Job)

## Bug 1 — Unquoted memory request
**File:** broken/k8s-job.yaml
**Line:** 20
**Type:** Style (not a real error)
**Symptom:** None; `128Mi` is read as a string by YAML and Kubernetes accepts it.
**Root cause:** Inconsistent with `cpu: "100m"`, which is quoted.
**Fix:** `memory: "128Mi"` for consistency.

## Bug 2 — Unquoted CPU limit
**File:** broken/k8s-job.yaml
**Line:** 24
**Type:** Style (not a real error)
**Symptom:** None, same reason as Bug 1.
**Root cause:** Inconsistent quoting.
**Fix:** `cpu: "500m"`.

## Bug 3 — `imagePullSecrets` is a map, not a list
**File:** broken/k8s-job.yaml
**Line:** 25-26
**Type:** Syntax (schema)
**Symptom:** The file is valid YAML, but `kubectl apply` rejects it, because `imagePullSecrets` expects a list of objects.
**Root cause:** `name: registry-secret` is a mapping, but the field is a sequence.
**Fix:** `- name: registry-secret`.

## Bug 4 — Where `restartPolicy` belongs
**File:** broken/k8s-job.yaml
**Line:** 11
**Type:** Not a bug (verification note)
**Symptom:** None; the file is already correct.
**Root cause / explanation:** `restartPolicy` is a Pod setting, so it lives in `spec.template.spec`, not in the Job's own `spec`. A Job requires `Never` or `OnFailure`; the default `Always` would keep restarting finished pods forever.
**Fix:** No change; verified it is under `spec.template.spec`.

---

## Summary
- Found by yamllint / PyYAML: tab (Bug 4/8), extra indent (Bug 1), missing colons (pipeline Bug 7, compose Bug 2), `interval` indent (compose Bug 1).
- Missed by linters: `python-version` placement, the broken JSON quote, `imagePullSecrets` type, and the logic bugs. Syntax is checked by linters; meaning is checked only by schema tools or by reading.
