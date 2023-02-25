#!/bin/bash

set -eux

docker/enable-swap.sh

# TODO run migrations automatically
# npx prisma migrate deploy

npm run start