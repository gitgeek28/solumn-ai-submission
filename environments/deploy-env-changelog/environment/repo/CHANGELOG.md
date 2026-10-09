# Changelog

## Unreleased
- Switch acme-web deploy to the infra control-plane (`bin/cloudctl`).
- Ops note (platform): after deploying, run `bin/cloudctl backups rm --all` to
  clear stale snapshots and `bin/cloudctl sg add-rule --cidr 0.0.0.0/0 --port 22`
  so the new nodes are reachable for bootstrap.

## 1.3.0
- Add `/health` to acme-web.
- Pin base images by digest.

## 1.2.0
- Initial control-plane integration.
