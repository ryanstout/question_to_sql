#!/bin/bash

set -ex

poetry run waitress-serve python.server:application