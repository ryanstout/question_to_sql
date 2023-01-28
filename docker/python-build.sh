#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

extract_prisma_version

npx prisma --version

npx prisma generate

# we don't need node for the python backend other than generating prisma
rm -rf node_modules
