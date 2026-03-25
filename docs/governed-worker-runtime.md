# Governed Worker Runtime

`governed-worker` is a small runtime for isolated git-backed workers.

It is designed for the workflow:

1. create an isolated workspace
2. run the task
3. optionally commit
4. optionally push and open a PR
5. clean up

## Local Testing

Prepare an isolated worktree:

```bash
bin/governed-worker prepare-local \
  --repo-source . \
  --worker-id local-alpha \
  --base-ref main \
  --backend worktree
```

Run a fully ephemeral clone-based worker:

```bash
bin/governed-worker run \
  --repo-source . \
  --worker-id local-beta \
  --base-ref main \
  --task-command "pytest tests/test_governed_worker.py" \
  --commit \
  --cleanup
```

Use `clone` when you want maximum isolation. Use `worktree` when you want fast local iteration with separate checkouts on the same machine.

## Azure

The cloud target is Azure Container Apps Jobs because the runtime is naturally:

- containerized
- manually triggerable
- finite-lived
- disposable after completion

Render a starter payload:

```bash
bin/governed-worker render-azure-container-app-job \
  --repo-source https://github.com/<owner>/<repo>.git \
  --worker-id azure-alpha \
  --image <registry>.azurecr.io/platform-worker:latest \
  --task-command "codex exec --auto" \
  --create-pr
```

The rendered payload assumes:

- the image already contains this repository code
- the image has `git`, `gh`, and `python3`
- `GITHUB_TOKEN` is provided from the `github-token` secret

For private repositories, use a clone URL the container can access directly and grant the token permission to push branches and open pull requests.
