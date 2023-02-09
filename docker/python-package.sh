#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

node_install_only_prisma

# now, let's install everything from poetry
# /usr/local/lib/python3.9/site-packages
poetry install