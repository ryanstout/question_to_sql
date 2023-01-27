# base node image
FROM node:19-bullseye-slim as base

ENV APP_DIR=/app
WORKDIR $APP_DIR

# set for base and all layer that inherit from it
ENV NODE_ENV production

ADD . .

# adding a bunch of packages to avoid warnings and build errors over the main languages I use with asdf
RUN install-node.sh

SHELL ["/bin/bash", "-c"]

RUN npm install --omit-dev=false
RUN poetry install --only prisma

RUN npm prune --omit=dev

# RUN npx prisma generate

# RUN npm run build

# CMD ["npm", "start"]
