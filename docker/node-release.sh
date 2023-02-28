#!/bin/bash

set -eux
cd "${0%/*}/.."

export SENTRY_ORG=knolbe
export SENTRY_PROJECT=javascript-remix
# export SENTRY_AUTH_TOKEN=

npx sentry-upload-sourcemaps

# TODO submit updated remix docs for this; the docs were incorrect!
rm ./public/**/*.map
rm ./build/*.map

# run migrations on deploy, revert the deploy if something goes wrong
prisma migrate deploy