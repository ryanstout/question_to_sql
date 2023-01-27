#!/bin/bash

set -ex

env

# for low memory fly.io; prisma deploy fails
export NODE_OPTIONS="--max-old-space-size=1024"

npx prisma migrate deploy

npm run start