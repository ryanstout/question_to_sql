#!/bin/bash

set -eux

`cd "${0%/*}/.."`

npm install --include=dev

# this image will only run the node application adn does not need the python client
sed -i '/generator pyclient/,/}/d' prisma/schema.prisma
npx prisma generate

npm run build

# after building, let's remove all of the dev packages that we do not need
npm prune --omit dev --omit optional