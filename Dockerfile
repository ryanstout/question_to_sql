# TODO extract node version from tool-versions
FROM node:19.2.0-bullseye-slim

ENV APP_DIR=/app
WORKDIR $APP_DIR

# set for base and all layer that inherit from it
ENV NODE_ENV production

# add only the install script so we can iterate on other scripts without reinstalling everything
ADD docker/install-node.sh ./
# ADD docker/stubbed-prisma-client-py /usr/bin/prisma-client-py
RUN ./install-node.sh && rm install-node.sh

ADD . .
RUN docker/build-node.sh

CMD ["docker/run-node.sh"]
