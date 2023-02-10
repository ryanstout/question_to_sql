utilities=(
  nano
  zsh
  ncdu
  git
  fd-find
  fzf
  ripgrep
  curl
  # httpie this ends up installing pythong as welll :/
  less
  # for dig
  dnsutils
  # for psql to run queries directly against the database in the same network
  postgresql-client
  htop
  zsh
  tmux
  unzip
  # for prisma
  ca-certificates openssl
)

# unsure if this is required, but things seem to work a bit better when PRISMA_VERSION is around
extract_prisma_version() {
  prisma_version=$(node -p -e "require('./package.json').dependencies.prisma" | sed 's/[^0-9.]//g')
  export PRISMA_VERSION=$prisma_version
}

extract_npm_version() {
  npm_version=$(node -p -e "require('./package.json').engines.npm")
  export NPM_VERSION=$npm_version
}

remove_python_prisma_generator() {
  echo "Removing python prisma generator"
  sed -i '/generator pyclient/,/}/d' prisma/schema.prisma
}

# TODO should extract this out into a blog post
node_install_only_prisma() {
  # this is absolutely insane:
  #
  #   1. You cannot install a NPM package locally without installing everything in your package json
  #     https://stackoverflow.com/questions/22420564/install-only-one-package-from-package-json
  #   2. Prisma does not like installing the package globally
  #   3. If your package.json is in the folder heirarchy, rule #1 applies

  extract_prisma_version

  # TODO use better randomized folder name
  prisma_tmp_dir=$(mktemp -d)
  pushd $prisma_tmp_dir
  npm i prisma@$PRISMA_VERSION @prisma/client@$PRISMA_VERSION
  popd

  # intentionally do not delete node_modules, this is needed for production
  cp -r $prisma_tmp_dir/node_modules node_modules
  rm -rf $prisma_tmp_dir
}
