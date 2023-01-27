# base node image
FROM node:19-bullseye-slim as base

# adding a bunch of packages to avoid warnings and build errors over the main languages I use with asdf
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    # from node docker
    # https://github.com/nodejs/docker-node/blob/754ca131a9c4f7e4ac8c255cbb3e35a446f5b70c/18/bullseye-slim/Dockerfile#LL20C45-L20C104
    ca-certificates \
    curl \
    wget \
    gnupg \
    dirmngr \
    xz-utils \
    libatomic1 \
    # from python docker
    # https://github.com/docker-library/python/blob/6aba522318fc24e245b15f8912a248076e24d163/3.9/slim-bullseye/Dockerfile
    ca-certificates \
		netbase \
		tzdata \
    dpkg-dev \
		gcc \
		gnupg dirmngr \
		libbluetooth-dev \
		libbz2-dev \
		libc6-dev \
		libexpat1-dev \
		libffi-dev \
		libgdbm-dev \
		liblzma-dev \
		libncursesw5-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		make \
		patchelf \
		tk-dev \
		uuid-dev \
		wget \
		xz-utils \
		zlib1g-dev \
    # because I like it
    nano bash ncdu git; \
    # cleanup
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/*

SHELL ["/bin/bash", "-l", "-c"]

# set for base and all layer that inherit from it
ENV NODE_ENV production
ENV PYTHON_ENV production

RUN echo ". \"$HOME/.asdf/asdf.sh\"" >> ~/.bashrc
RUN echo "legacy_version_file = yes" >> ~/.asdfrc

RUN cat ~/.tool-versions | cut -d' ' -f1 | grep "^[^\#]" | xargs -I{} asdf plugin add {}
RUN asdf install

RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.prefer-active-python true

# Install all node_modules, including dev dependencies
FROM base as deps

ENV APP_DIR=/app
WORKDIR $APP_DIR

ADD package.json package-lock.json .npmrc ./
RUN npm install --production=false

ADD poetry.lock pyproject.toml ./
RUN poetry install --only prisma

# Setup production node_modules
FROM base as production-deps

WORKDIR $APP_DIR

COPY --from=deps $APP_DIR/node_modules $APP_DIR/node_modules
ADD package.json package-lock.json .npmrc ./
RUN npm prune --production

# Build the app
FROM base as build

WORKDIR $APP_DIR

COPY --from=deps $APP_DIR/node_modules $APP_DIR/node_modules

ADD prisma .
RUN npx prisma generate

ADD . .
RUN npm run build

# Finally, build the production image with minimal footprint
FROM base

WORKDIR $APP_DIR

COPY --from=production-deps $APP_DIR/node_modules $APP_DIR/node_modules
COPY --from=build $APP_DIR/node_modules/.prisma $APP_DIR/node_modules/.prisma

COPY --from=build $APP_DIR/build $APP_DIR/build
COPY --from=build $APP_DIR/public $APP_DIR/public
ADD . .

CMD ["npm", "start"]
