#!/bin/bash

set -eux

apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends \
  # simple python installation for prisma
  # python-is-python3 python3-pip \
  # for prisma
  ca-certificates openssl \
  # for node-gyp
  libpq-dev g++ make \
  automake \
  # because I like it
  nano bash ncdu git; \
  # cleanup
  apt-get clean

npm install -g npm@9.4.0
pip install --upgrade pip
pip install poetry==$(grep -o '^poetry.*' .tool-versions | grep -o "[0-9.]\+")
poetry config virtualenvs.create false
