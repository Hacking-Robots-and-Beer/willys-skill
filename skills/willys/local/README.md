# local/ — bundled Python packages

This directory holds the pip-installed Python packages required by the willys skill (`requests` and its dependencies).

## Purpose

When running inside a Kubernetes pod (e.g. `openclaw-zoe-0`) there is no pip available at runtime. Packages must already exist in the service user's `~/.local` directory. This folder is the portable, repo-tracked copy of those packages.

Python automatically finds packages installed here because `~/.local/lib/python*/site-packages` is on the default user site-packages path.

## Populating this directory

### Option A — copy from a running pod

```bash
kubectl exec -it openclaw-zoe-0 -n openclaw-zoe -- pip install requests
kubectl cp openclaw-zoe-0:/root/.local skills/willys/local -n openclaw-zoe
```

### Option B — install locally (used to create this bundle)

```bash
pip install --target skills/willys/local/lib/python3/site-packages requests
```

## Deploying to the pod

Copy this directory to `$HOME/.local` of the OpenClaw service user inside the pod:

```bash
kubectl cp skills/willys/local/. openclaw-zoe-0:/root/.local -n openclaw-zoe
```
