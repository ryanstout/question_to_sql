#!/bin/bash

set -eux
cd "${0%/*}/.."
source docker/shared.sh

apt-get update
export DEBIAN_FRONTEND=noninteractive

packages=(
  # for node-gyp
  libpq-dev g++ make
)
packages=("${packages[@]}" "${utilities[@]}")

apt-get -y install --no-install-recommends ${packages[@]}

poetry_version=$(grep -o '^poetry.*' .tool-versions | grep -o "[0-9.]\+")

pip install --upgrade pip
pip install poetry==$poetry_version
poetry config virtualenvs.create false

curl -fsSL https://deb.nodesource.com/setup_19.x | bash -
apt-get install -y nodejs

apt-get clean