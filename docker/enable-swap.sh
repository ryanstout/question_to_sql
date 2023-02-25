#!/bin/bash
# Description: this needs to be run *after* the container has started

set -eux

# https://community.fly.io/t/swap-memory/2749/3
fallocate -l 2048M /swapfile
chmod 0600 /swapfile
mkswap /swapfile
echo 10 > /proc/sys/vm/swappiness
swapon /swapfile
