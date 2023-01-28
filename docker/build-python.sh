#!/bin/bash

set -eux

`cd "${0%/*}/.."`

npx prisma generate

# we don't need node for the python backend other than generating prisma
rm -rf node_modules
