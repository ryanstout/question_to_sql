#!/bin/bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

npx prisma --version

# this image will only run the node application adn does not need the python client
remove_python_prisma_generator
npx prisma generate

npx remix-routes

npm run build

# after building, let's remove all of the dev packages that we do not need
npm prune --omit dev --omit optional