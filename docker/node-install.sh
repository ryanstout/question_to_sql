#!/usr/bin/env bash

set -eux
`cd "${0%/*}/.."`
source docker/shared.sh

apt-get update
export DEBIAN_FRONTEND=noninteractive

packages=(
  # for node-gyp
  python-is-python3 libpq-dev g++ make
)
packages=("${packages[@]}" "${utilities[@]}")

apt-get -y install --no-install-recommends ${packages[@]}

apt-get clean

