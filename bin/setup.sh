#!/bin/bash

# without pg_config, you'll get a cryptic node-gyp error
if ! command -v pg_config &> /dev/null
then
    echo "pg_config could not be found, if you are using the Postgres.app you'll need to add the bin to your path." \
         "\nEx: https://github.com/iloveitaly/dotfiles/commit/ce7377ad4e92f43dd9ede1a5aae19444fac2afaa"
    exit
fi

if ! command -v redis-cli &> /dev/null
then
    echo "redis could not be found, make sure it's installed"
    exit
fi

cat .tool-versions | cut -d' ' -f1 | grep '^[^\#]' | xargs -I{} asdf plugin add {}
asdf install

# for better asdf compatibility
# config writes to: ~/Library/Preferences/pypoetry/config.toml
poetry config virtualenvs.in-project true
poetry config virtualenvs.prefer-active-python true
poetry install

# TODO extract npm version from package json
npm install -g npm@9.4.2
npm install

npx cypress install

# needs to be installed globally per documentation
npm install -g depcheck

echo "Install libomp openblas for Mac for Faiss kNN library"
brew install libomp openblas

cp .env.example .env
echo "Update .env with fresh secrets"

# get the remix application up and running
npm run setup
npm run build

echo "`npm run dev` to start the server"

# helpful packages for ipython
poetry run pip install ipython ipdb pdbr ipython-autoimport rich docrepr colorama ipython-suggestions

# you need python installed properly to generate the prisma bindings
# for now, we are nuking the entire DB, will need to change this in the future
# TODO add IF TABLE EXISTS so it doesn't error out
psql --command="DROP DATABASE nlpquery" && \
    # remove all of the existing migrations
    rm -rf prisma/migrations && \
    # make sure the prisma versions are correct! `prisma-client-py --version`
    poetry run npx prisma migrate dev

# TODO add test database migration creation

psql --command="DROP DATABASE nlpquery_test"

# the prisma bindings are generated when you run `migrate dev`. Should look like:
#   ✔ Generated Prisma Client Python (v0.8.0) to ./../../.asdf/installs/python/3.9.9/lib/python3.9/site-packages/prisma in 132ms
# make sure the install path is the same as your virtualenv!