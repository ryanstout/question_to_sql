#!/bin/bash

# without pg_config, you'll get a cryptic node-gyp error
if ! command -v pg_config &> /dev/null
then
    echo "pg_config could not be found, if you are using the Postgres.app you'll need to add the bin to your path." \
         "\nEx: https://github.com/iloveitaly/dotfiles/commit/ce7377ad4e92f43dd9ede1a5aae19444fac2afaa"
    exit
fi

asdf install
poetry install
npm install

echo "Install libomp openblas for Mac for Faiss kNN library"
brew install libomp openblas


cp .env.example .env
echo "Update .env with fresh secrets"

npm run setup
npm run build

echo "`npm run dev` to start the server"

# for better asdf compatibility
poetry config virtualenvs.prefer-active-python true

# helpful packages for ipython
pip install ipython ipdb pdbr ipython-autoimport rich docrepr colorama
