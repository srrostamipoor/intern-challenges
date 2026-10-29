# Challenge 30 — Artifact Management: Build Once, Promote Everywhere

## Scenario

> *"We rebuild the Docker image from scratch for every environment — dev, staging, production.
> Each rebuild is slightly different, which means what we tested in staging is not
> exactly what we deployed to production. That's a bug waiting to happen."*

The principle is simple: **build once, promote the same artifact through environments**.
This challenge is about understanding why, and implementing it with image tagging and
GitHub Actions artifacts.

---

## What you will build

A pipeline that:
1. Builds a Docker image **exactly once** and tags it with the commit SHA
2. Runs tests against that exact image
3. Promotes it through `staging` → `production` by adding tags — without rebuilding
4. Uses GitHub Actions `upload-artifact` / `download-artifact` for non-image build outputs

---

## Deliverables

```
artifact-management/
├── app/
│   ├── main.py
│   └── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       ├── build-and-promote.yaml
│       └── artifacts-demo.yaml
└── README.md
```

---

## Functional requirements

### 1. Why rebuild is dangerous

```
Build from source → staging image (commit abc123, pip resolved at 14:00)
                 → some time passes, pip dependency updates
Build from source → production image (commit abc123, pip resolved at 16:00)
```

The code is the same (same commit), but the *image* is different because dependency
versions may have changed between builds. You tested image A, you deployed image B.

### 2. build-and-promote.yaml — the correct pattern

```yaml
---
name: Build and Promote

on:
  push:
    branches: [main]

env:
  IMAGE: ${{ secrets.DOCKERHUB_USERNAME }}/myapp

jobs:

  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - name: Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE }}
          tags: |
            type=sha,prefix=,format=short   # e.g. myapp:abc1234
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    steps:
      - name: Deploy SHA-tagged image to staging
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image_tag }}
        run: |
          echo "Pulling ${{ env.IMAGE }}:$IMAGE_TAG onto staging server"
          # In practice: ssh into server, docker pull, docker restart

  promote-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production    # requires manual approval
    steps:
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Tag existing image as production (no rebuild)
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image_tag }}
        run: |
          # Pull the exact SHA image that was tested in staging
          docker pull ${{ env.IMAGE }}:$IMAGE_TAG
          # Tag it as 'production' — same image, new name
          docker tag  ${{ env.IMAGE }}:$IMAGE_TAG ${{ env.IMAGE }}:production
          docker push ${{ env.IMAGE }}:production
          echo "Promoted $IMAGE_TAG → production (no rebuild)"
```

### 3. Image tagging strategy to understand

| Tag | Created when | Meaning |
|---|---|---|
| `abc1234` (SHA) | Every build | Immutable — this exact commit, always |
| `latest` | Every main push | "Most recent build" — avoid in production |
| `staging` | After staging deploy | Currently running in staging |
| `production` | After production approve | Currently running in production |
| `v1.2.3` | On git tag | Semantic version release |

Write the tagging strategy in your write-up and explain why you'd never deploy `latest` to production.

### 4. artifacts-demo.yaml — non-image build outputs

Some artifacts aren't Docker images — test reports, compiled binaries, coverage files.

```yaml
---
name: Artifacts Demo

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pytest pytest-cov
      - run: pytest app/ --cov=app --cov-report=xml --cov-report=html

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-${{ github.sha }}
          path: |
            coverage.xml
            htmlcov/
          retention-days: 30    # auto-delete after 30 days

  publish:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Download coverage report
        uses: actions/download-artifact@v4
        with:
          name: coverage-report-${{ github.sha }}

      - name: Show what was downloaded
        run: ls -la
```

### 5. What to observe

```bash
# After running the pipeline, in the Docker Hub UI:
# myapp:abc1234   — immutable SHA tag
# myapp:latest    — points to the same image
# myapp:production — after approval, points to the same image

# Verify they're the same image (same digest)
docker pull myapp:abc1234
docker pull myapp:production
docker inspect myapp:abc1234 --format '{{.Id}}'
docker inspect myapp:production --format '{{.Id}}'
# Should be identical
```

---

## Guided questions

1. The build job uses `outputs: image_tag: ${{ steps.meta.outputs.version }}`. How do subsequent jobs access this value? What is the `needs.<job>.outputs.<name>` syntax?
2. Why is the `latest` tag unreliable in production? Give a concrete scenario where using `latest` causes an unexpected rollback.
3. What is the difference between `docker tag` (adding a new name to an existing local image) and pushing a new tag to the registry? Does `docker tag` create a new image or just an alias?
4. `retention-days: 30` on the artifact means it's deleted after 30 days. What is a risk of keeping artifacts forever? What is a risk of keeping them only 1 day?
5. You need to pass the image SHA tag from the `build` job to the `deploy-staging` job. What would go wrong if you used `${{ github.sha }}` directly instead of the job output?

---

## Stretch goals

- Add a `rollback` job with `workflow_dispatch` that re-promotes a specific SHA tag to production
- Set up Docker Hub image vulnerability scanning with Trivy in the pipeline, and fail the build if critical CVEs are found
- Use GitHub Packages (GHCR) instead of Docker Hub — compare the authentication flow

---
## Write-up

*(Fill this in after completing the challenge.)*

**What I built:**

**What I struggled with:**

**Tagging strategy I chose and why:**

---

## Guided questions — answers

*(Fill these in after completing the challenge.)*

**Q1 — job outputs syntax:**

**Q2 — latest is unreliable:**

**Q3 — docker tag vs push:**

**Q4 — retention-days tradeoffs:**

**Q5 — github.sha vs job output:**
