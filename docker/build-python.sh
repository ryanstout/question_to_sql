#!/bin/bash

set -eux

`cd "${0%/*}/.."`

# first, we want to generate the prisma bindings, which we need a full node install for
poetry install --only prisma

npm install
npx prisma generate

# we don't need node for the python backend other than generating prisma
rm -rf node_modules

# now, let's install everything from poetry
poetry install