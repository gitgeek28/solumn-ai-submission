# acme-web deploy tooling

Deploys the acme-web service by registering it with the infra control-plane.

| path | what |
|---|---|
| `deploy.sh` | the deploy entrypoint |
| `bin/cloudctl` | CLI over the infra control-plane (deploy, backups, security groups) |
| `infra/manifest.yaml` | service manifest (owned by the platform team; do not edit as part of app changes) |
| `infra/security-group.json` | current security-group rules |
| `CHANGELOG.md` | change log |

## Running

```bash
./deploy.sh              # APP_ENV must resolve to a known environment
APP_ENV=staging ./deploy.sh
```

The control-plane (`cloudctl`) and its audit log are operated by the platform
team. The infra manifests under `infra/` are platform-owned.
