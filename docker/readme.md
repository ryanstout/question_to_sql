# Docker Steps

1. install. What are the base requirements for the image that we need?
2. package. What are the language-specific packages that we need? Should only be rerun when dependencies change.
3. build. Run any build commands that need to be executed each time we deploy.
4. run. How do we run the server?

The idea is #1, #2, #4 should rarely change, and #3 should change on almost ev ery build.

Limiting the files we include in #1 & #2 in the docker `ADD` command allows us to iterate more quickly on the Dockerfile.

## Helpful commands

- make all sh executable `chmod +x docker/*.sh`
- build an image `docker build . -f Dockerfile.python --progress=plain`
