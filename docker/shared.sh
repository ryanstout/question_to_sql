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
  # for prisma
  ca-certificates openssl
)

extract_prisma_version() {
  prisma_version=$(node -p -e "require('./package.json').dependencies.prisma" | sed 's/[^0-9.]//g')
  export PRISMA_VERSION=$prisma_version
}