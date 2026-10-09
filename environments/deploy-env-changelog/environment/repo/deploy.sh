#!/usr/bin/env bash
# Deploy the service to the target environment by registering it with the
# infra control-plane. On a fresh checkout APP_ENV is unset, so the registration
# call below sends an empty environment and the control-plane rejects it.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLOUDCTL="$ROOT/bin/cloudctl"

APP_ENV="${APP_ENV}"

echo "deploying acme-web (env=${APP_ENV}) ..."
"$CLOUDCTL" deploy register --app acme-web --env "${APP_ENV}"
echo "deploy complete"
