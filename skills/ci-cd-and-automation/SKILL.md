---
name: ci-cd-and-automation
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Implements CI/CD pipelines and automation. Use when setting up continuous
  integration, deployment pipelines, automated testing, infrastructure as code,
  or any automation that runs on code changes.
tags:
  - ci-cd
  - automation
  - pipelines
  - devops
  - deployment
trigger_patterns:
  - ci-cd-and-automation
  - set up ci
  - github actions
  - deployment pipeline
  - continuous integration
  - automate deployment
  - run tests on push
  - infrastructure as code
  - docker pipeline
  - automated workflow
  - ci pipeline
  - setup pipeline
  - configure ci
  - set up the pipeline
  - build pipeline
  - continuous deployment
  - pipeline for this project
---

# CI/CD and Automation

## Overview

Automate the path from code to production. CI/CD pipelines give every change a consistent, repeatable journey through testing, validation, and deployment. The goal is a pipeline where passing tests is sufficient confidence to deploy — not a process that needs to be worked around.

## When to Use

- Setting up a new project's CI/CD pipeline
- Adding automated testing to an existing pipeline
- Configuring deployment automation
- Setting up infrastructure as code
- Adding security scanning or quality gates
- Implementing preview environments for PRs

## Pipeline Architecture

### The Four Stages

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────────┐
│   CI    │    │  Test   │    │ Security │    │   Deploy    │
│         │───▶│         │───▶│          │───▶│             │
│ Build   │    │ Unit    │    │ Audit    │    │ Staging     │
│ Lint    │    │ Integr. │    │ SAST     │    │ Production  │
│ Types   │    │ E2E     │    │ Secrets  │    │ (gated)     │
└─────────┘    └─────────┘    └──────────┘    └─────────────┘
     ↑               ↑               ↑               ↑
  Every push    Every push    Every push     Main only
```

### Stage Principles

- **Fast feedback first**: Lint and type-check before running slow tests
- **Fail fast**: Stop the pipeline at the first failure
- **Parallel where safe**: Run independent jobs concurrently
- **Deterministic**: Same commit always produces same result
- **Cached**: Restore dependencies from cache before installing

## GitHub Actions Examples

### Basic CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    name: Quality Checks
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run type-check

      - name: Lint
        run: npm run lint

      - name: Unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: quality

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/
          retention-days: 7
```

### Full Pipeline with Security and Deployment

```yaml
# .github/workflows/pipeline.yml
name: Pipeline

on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    name: Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run type-check && npm run lint && npm test

  security:
    name: Security
    runs-on: ubuntu-latest
    needs: quality
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Dependency audit
        run: npm audit --audit-level=high

      - name: Secret scanning
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [quality, security]
    environment: staging
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci && npm run build

      - name: Deploy to staging
        run: npx vercel --token=${{ secrets.VERCEL_TOKEN }} --env=staging

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # Requires manual approval
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci && npm run build
      - run: npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

## Docker Build Pipeline

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Dockerfile Best Practices

```dockerfile
# Multi-stage build — small production image
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (layer caching)
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production image
FROM node:20-alpine AS runner

# Don't run as root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy only what's needed
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER appuser

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

## Environment and Secrets Management

```yaml
# GitHub Environments with protection rules
environments:
  staging:
    # No approval required — auto-deploys on push to main
    reviewers: []
    deployment_branch_policy:
      protected_branches: false
      custom_branches: ['main']

  production:
    # Requires team lead approval
    reviewers:
      - teams: [engineering-leads]
    deployment_branch_policy:
      protected_branches: true
```

**Secrets in pipelines:**

```yaml
# Reference secrets — never hardcode values
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.STRIPE_API_KEY }}
  # Never: API_KEY: sk_live_actual_key_here
```

## Cache Configuration

```yaml
# Node.js with npm cache
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'  # Caches ~/.npm

# Explicit cache with custom key
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

## Pipeline Quality Standards

### The Pipeline Manifesto

```
A good pipeline:
✓ Runs in < 10 minutes for every PR
✓ Never has flaky tests (fix them, don't retry blindly)
✓ Fails clearly with actionable error messages
✓ Never deploys broken code to production
✓ Can be reproduced locally
✓ Secrets are in the secrets store, not in code
✓ Artifacts are versioned and traceable to a commit
```

### Flaky Test Policy

```
Flaky tests are BROKEN tests.

When a test fails inconsistently:
1. DO NOT add retry logic to hide the flakiness
2. Mark the test as flaky in your tracking system
3. Investigate and fix within one sprint
4. Until fixed: skip + track in issue (don't commit retry workarounds)
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI is slow, we'll skip it for this PR" | Skipping CI is how broken code reaches main. Speed up the pipeline instead. |
| "This test is flaky, let's add retries" | Retries hide real failures. Investigate and fix the flakiness. |
| "We'll set up proper secrets management later" | Hardcoded secrets become vulnerabilities. Set up the secrets store from day one. |
| "The pipeline passed before, this change is safe" | The pipeline tested what you told it to test. Configure it to test what matters. |
| "It works locally" | CI catches environment differences. That's the point of CI. |

## Red Flags

- Pipeline that regularly takes 30+ minutes
- Tests that pass only with retries
- Secrets in workflow files or repository code
- Pipeline that always passes regardless of code quality
- No deployment to staging before production
- Production deployments that bypass the pipeline
- Pipeline configuration drift (pipeline doesn't match what's deployed)

## Verification

After setting up or modifying a pipeline:

- [ ] Pipeline runs end-to-end without failures via `code_execution_tool` (or push to branch)
- [ ] No secrets hardcoded in workflow files
- [ ] Caching configured for dependencies (npm/pip/cargo)
- [ ] Tests run in parallel where possible
- [ ] Failing tests block the pipeline (not just warn)
- [ ] Production deployment requires staging to pass
- [ ] Production deployments require approval (for team projects)
- [ ] Pipeline completes in a reasonable time (< 15 minutes)
