#!/bin/bash

set -eux

npm install
npx prisma generate
npm run build
npm prune --omit dev --omit optional