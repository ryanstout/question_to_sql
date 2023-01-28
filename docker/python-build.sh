#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

# unsure if this is required, but things seem to work a bit better when PRISMA_VERSION is around
extract_prisma_version

npx prisma --version

npx prisma generate

# the node installation downloads some prisma binaries which are required for the python library to work
# do not remove the node_modules folder, it will break the python library