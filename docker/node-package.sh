#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

extract_npm_version
npm install -g npm@$NPM_VERSION

node --version
npm --version

npm install --include=dev