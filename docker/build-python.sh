#!/bin/bash

set -eux

`cd "${0%/*}/.."`

# this is absolutely insane
# https://stackoverflow.com/questions/22420564/install-only-one-package-from-package-json
prisma_version=$(node -p -e "require('./package.json').dependencies.prisma" | sed 's/[^0-9.]//g')
export PRISMA_VERSION=$prisma_version
prisma_tmp_dir=/tmp/prisma
mkdir $prisma_tmp_dir && pushd $prisma_tmp_dir
npm i prisma@$prisma_version @prisma/client@$prisma_version
popd
cp -r $prisma_tmp_dir/node_modules node_modules

# first, we want to generate the prisma bindings, which we need a full node install for
poetry install --only prisma

npx prisma generate

# we don't need node for the python backend other than generating prisma
rm -rf node_modules

# now, let's install everything from poetry
# /usr/local/lib/python3.9/site-packages
poetry install