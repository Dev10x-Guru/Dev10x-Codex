---
name: k8s
description: 'Kubernetes cluster operations via aws-vault authenticated kubectl. Check deployments, pods, logs, events, and runtime configuration across environments. TRIGGER when: investigating service health, comparing staging and production, checking restart loops or OOM kills, or verifying what is running versus what git says should be running. DO NOT TRIGGER when: retrieving secrets (use Dev10x:aws-vault), or you need to MUTATE cluster state (apply, create, delete, scale, exec, port-forward) — those run only under direct supervisor control in a separate terminal.'
metadata:
  upstream: skills/k8s/SKILL.md
---

> **Running in Codex.** Generated from `skills/k8s/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/k8s/`.
> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and confirm before any step that writes to GitHub or rewrites history.

# Kubernetes Operations

## When to Use

- Checking pod status or logs for a service
- Comparing deployments across staging and production
- Investigating service health or restart loops
- Verifying runtime configuration of a deployment
- Checking what's running vs what git says should be running

## Prerequisites

- `aws-vault` configured (see `Dev10x:aws-vault`)
- `kubectl` installed and configured with cluster contexts
- Service registry at `~/.config/Dev10x/aws-vault/service-registry.yaml`

## Service Registry

Read `~/.config/Dev10x/aws-vault/service-registry.yaml` to resolve:

- Environment → `aws_vault_profile` and `k8s.context`
- Environment → `k8s.namespace`

A starting template ships at
`<plugin-root>/skills/aws-vault/references/service-registry.example.yaml`.

## Wrapper Script

All kubectl operations go through the wrapper:

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh <env> <kubectl-args...>
```

The wrapper reads the service registry to resolve the profile, context,
and namespace — no manual lookup needed.

**Read-only by contract.** The wrapper accepts only read verbs (`get`,
`describe`, `logs`, `top`, `events`, and similar). Mutating verbs —
`apply`, `create`, `delete`, `scale`, `exec`, `port-forward` — are
rejected. To inspect a pod's environment, read the deployment spec
rather than `exec`-ing into the pod.

## Common Operations

### Check pod status

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging get pods -l app=<service>
```

### Stream logs (live)

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  logs -l app=<service> --tail=100 -f
```

### Recent logs (snapshot)

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  logs -l app=<service> --tail=200 --since=30m
```

### Check deployment

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get deployment <service> -o yaml
```

### Check environment variables in a deployment

`exec` is not available through the read-only wrapper. Read the
injected environment from the deployment spec instead:

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get deploy <service> -o jsonpath='{.spec.template.spec.containers[0].env}'
```

### Check recent events (crashes, OOM, restarts)

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get events --sort-by='.lastTimestamp'
```

### Compare deployment images across environments

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get deploy <service> -o jsonpath='{.spec.template.spec.containers[0].image}'

<plugin-root>/skills/aws-vault/scripts/kubectl.sh production \
  get deploy <service> -o jsonpath='{.spec.template.spec.containers[0].image}'
```

## Workflow: Investigate Service Issues

### Step 1: Check pod health

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get pods -l app=<service> -o wide
```

Look for: `CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff`,
high restart counts.

### Step 2: Check recent logs

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  logs -l app=<service> --tail=200 --since=15m
```

### Step 3: Check events

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  get events --sort-by='.lastTimestamp'
```

### Step 4: Check resource usage

```bash
<plugin-root>/skills/aws-vault/scripts/kubectl.sh staging \
  top pods -l app=<service>
```

## Key Lessons

### Secrets live in AWS Secrets Manager

Application secrets are managed in AWS Secrets Manager and injected
into pods via external-secrets-operator or init containers. Do not
look for credential values in k8s Secret objects directly — use
`Dev10x:aws-vault` instead.

### Use the service registry

Cluster contexts, namespaces, and profile names differ between
environments. Always resolve from the registry rather than
hardcoding a context or namespace.

## Related Skills

- `Dev10x:aws-vault` — secret retrieval and the kubectl wrapper
- `Dev10x:investigate` — root-causing a reported issue end to end
