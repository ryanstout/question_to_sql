#!/bin/bash

set -eux
`cd "${0%/*}/.."`

node --version
npm --version

npm install --include=dev