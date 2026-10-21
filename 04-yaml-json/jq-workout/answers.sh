#!/bin/bash
# Challenge 15 - jq Workout
# All working jq commands, grouped by dataset.

# ===== Dataset 1: GitHub repos =====

# 1. Print the full_name of every repo
jq '.items[].full_name' data/github_repos.json

# 2. Print name + star count as a table
jq -r '.items[] | "\(.full_name): \(.stargazers_count)"' data/github_repos.json

# 3. Only repos with more than 50,000 stars
jq -r '.items[] | select(.stargazers_count > 50000) | .full_name' data/github_repos.json

# 4. Sort by open_issues_count descending, print name + count
jq -r '.items | sort_by(.open_issues_count) | reverse | .[] | "\(.full_name): \(.open_issues_count)"' data/github_repos.json

# 5. Extract every owner login into a plain array
jq '[.items[].owner.login]' data/github_repos.json

# 6. Count how many repos have "python" in their topics
jq '[.items[] | select(.topics | index("python"))] | length' data/github_repos.json

# ===== Dataset 2: Fake Kubernetes pods =====

# 7. List all pod names in the "production" namespace
jq -r '.items[] | select(.metadata.namespace == "production") | .metadata.name' data/fake_pods.json

# 8. Find pods in CrashLoopBackOff - print name + nodeName
jq -r '.items[] | select(.status.containerStatuses[0].state.waiting.reason == "CrashLoopBackOff") | "\(.metadata.name) on \(.spec.nodeName)"' data/fake_pods.json

# 9. Pods with restartCount > 5
jq -r '.items[] | select(.status.containerStatuses[0].restartCount > 5) | "\(.metadata.name): \(.status.containerStatuses[0].restartCount)"' data/fake_pods.json

# 10. Count pods per namespace
jq '.items | group_by(.metadata.namespace) | map({namespace: .[0].metadata.namespace, count: length})' data/fake_pods.json

# 11. Pods on "node-2" that are NOT ready
jq -r '.items[] | select(.spec.nodeName == "node-2" and .status.containerStatuses[0].ready == false) | .metadata.name' data/fake_pods.json

# ===== Dataset 3: Docker inspect =====

# 12. The container's IP address
jq -r '.[0].NetworkSettings.IPAddress' data/docker_inspect.json

# 13. Environment variables that are set
jq -r '.[0].Config.Env[]' data/docker_inspect.json

# 14. Ports that are exposed
jq -r '.[0].Config.ExposedPorts | keys[]' data/docker_inspect.json

# 15. Is the container running? (State.Running as boolean)
jq '.[0].State.Running' data/docker_inspect.json
