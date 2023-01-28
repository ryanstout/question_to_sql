# TODO extract node version from tool-versions
FROM node:19.2.0-bullseye-slim

ENV APP_DIR=/app
WORKDIR $APP_DIR

# set for base and all layer that inherit from it
ENV NODE_ENV production

# add only the install script so we can iterate on other scripts without reinstalling everything
ADD docker/install-node.sh docker/shared.sh ./docker/
RUN ./docker/install-node.sh

ADD package.json package-lock.json ./
ADD ./docker/node-package.sh ./docker/
RUN ./docker/node-package.sh

ADD . .
RUN docker/build-node.sh

CMD ["docker/run-node.sh"]
