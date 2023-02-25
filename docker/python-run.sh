#!/bin/bash

set -ex

docker/enable-swap.sh
poetry run waitress-serve python.server:application