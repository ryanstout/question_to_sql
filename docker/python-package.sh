#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

extract_npm_version
npm install -g npm@$NPM_VERSION

node_install_only_prisma

# for depreciated sklearn package, hopefully we can remove in the future
export SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=true

# now, let's install everything from poetry
# /usr/local/lib/python3.9/site-packages
poetry install --no-interaction