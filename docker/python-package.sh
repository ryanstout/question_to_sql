#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

install_only_prisma() {
  # this is absolutely insane:
  #
  #   1. You cannot install a NPM package locally without installing everything in your package json
  #     https://stackoverflow.com/questions/22420564/install-only-one-package-from-package-json
  #   2. Prisma does not like installing the package globally
  #   3. If your package.json is in the folder heirarchy, rule #1 applies

  extract_prisma_version

  prisma_tmp_dir=/tmp/prisma
  mkdir $prisma_tmp_dir
  pushd $prisma_tmp_dir
  npm i prisma@$PRISMA_VERSION @prisma/client@$PRISMA_VERSION
  popd

  # intentionally do not delete node_modules, leave this to the build step
  cp -r $prisma_tmp_dir/node_modules node_modules
}

install_only_prisma

# now, let's install everything from poetry
# /usr/local/lib/python3.9/site-packages
poetry install