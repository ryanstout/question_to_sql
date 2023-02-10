#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

extract_npm_version
npm install -g npm@$NPM_VERSION

node_install_only_prisma

# now, let's install everything from poetry
# /usr/local/lib/python3.9/site-packages
poetry install