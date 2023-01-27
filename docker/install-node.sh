#!/usr/bin/env bash

set -eux

apt-get update
export DEBIAN_FRONTEND=noninteractive

# for prisma
 # for node-gyp
  # because I like it
apt-get -y install --no-install-recommends \
  ca-certificates openssl \
  python-is-python3 libpq-dev g++ make \
  nano zsh ncdu git \


apt-get clean

npm install -g npm@9.4.0

echo -e "#\!/bin/bash\necho 'stubbed prisma-client-py'" > /usr/bin/prisma-client-py
chmod +x /usr/bin/prisma-client-py
