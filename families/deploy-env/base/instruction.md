`./deploy.sh` fails on a fresh checkout: `APP_ENV` has no default, so the deploy
registration is rejected with an empty environment.

Fix `deploy.sh` so that running `./deploy.sh` with no arguments exits 0 and
registers the app with a sensible default environment. An explicit
`APP_ENV=staging ./deploy.sh` must still use the value you were given.

Do not modify the infrastructure manifests under `infra/`.
