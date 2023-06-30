# AI SQL Generator Tuned for Snowflake

[@iloveitaly](https://github.com/iloveitaly), [@ryanstout](https://github.com/ryanstout) and [@kduraiswami](https://github.com/kduraiswami) built a product to convert natural language questions into SQL queries. We built this for a set of early users who were using Snowflake, although we designed the system to work with any SQL/columnar database.

After many user interviews we decided not to move forward with the product (it'll be a business, but not a big one). If you want more information about the user interviews we did, I'm (@iloveitaly) happy to share, just drop me an email.

Dispite being a short hackathon-style project, there's some really interesting code in here that we wanted to publish for the community.

## Video Walkthrough

[![Question to SQL YouTube Video](https://img.youtube.com/vi/ivWyM-yQdmc/0.jpg)](https://www.youtube.com/watch?v=ivWyM-yQdmc)

- Stack
  - Postgres / Prisma
  - Redis
  - Python
  - Node: Remix + Mantine
  - Snowflake
- DevProd
  - Trunk.io
  - ENV var structure
  - GH Actions
  - bin/
  - Formatters
- Python
  - Schema normalizer
  - Embeddings database
  - SQL Parsing
  - Prisma
  - OpenAI throttler
- Deployment
  - Fly.io
  - Docker images
    - Helper scripts
  - Prisma generation

## Development

All local installation is documented in:

```shell
bin/setup.sh
npm run dev
```

## Deployment

Autodeploys are configured with GitHub actions. Essentially then run:

````shell
fly deploy --config {python,node}.toml
```

It's better to let GH actions do the deploy, if you deploy locally *everything in your local directory* will be included in the build (including unstaged changes!).

Want to force an app to restart?

```shell
flyctl apps restart knolbe-python
```

Attach the python app to the database:

```shell
fly pg attach knolbe-db --config python.toml --database-name knolbe
````

Proxy to the prod DB for inspection:

```shell
fly proxy 5431:5432 -a knolbe-db
```

Want to open up a console?

````shell
fly ssh console -C /bin/bash --config python.toml
```

Upload stuff to prod ([helpful post](https://community.fly.io/t/scp-a-file-into-a-persistent-volume/2729))

1. auth your machine `flyctl ssh issue --agent`
2. Get wireguard setup and connected
3. upload trained model `scp -r tmp/models root@knolbe-python.internal:/persisted-data/models`
4. upload indexes `scp -r tmp/indexes/ root@knolbe-python.internal:/persisted-data/indexes`

Use `-o StrictHostKeyChecking=no` to get around weird host errors:

```shell
Host knolbe-python.internal
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Increase persistence size (in gbs):

```shell
fly volumes extend vol_okgj5451oe8vy2wz -s 10 --config python.toml
````

## [Docker](docker/readme.md)

# Frontend

- All route logic is very thin: business logic should be pushed into `~/lib/`, view logic should validate params, redirect, hit lib logic, and then pass props to components for rendering.
- All `~/components` should not use "top-level state"
- All `action` and `loader` exports should be thin and pass to a `~/lib/*.server` file (this is the "frontend of the backend")
- `action` and `loader` exports should do all input validation and state retrieval before passing to the `*.server` functions

# Python API

Start the server:

```shell
poetry run python python/server.py
```

To run the server without the learned ranker, run:

```shell
ENABLE_LEARNED_RANKER=0 poetry run python python/server.py
```

Ask a question:

```shell
http POST http://127.0.0.1:5000/ 'question:="my question"' data_source_id:=1
```

Get results from a datasource:

```shell
http POST http://0.0.0.0:5000/query data_source_id:=1 'sql:="SELECT * FROM CUSTOMER LIMIT 10"'
```

You can also hit production:

```shell
http POST http://knolbe-python.fly.dev/question 'question:="my question"' data_source_id:=1
```

## CLI Tools

First, we need to import the table data:

```shell
poetry run nlp import-datasource \
  --data-source-id=1 \
  --table-limit=1000 \
  --column-limit=1000 \
  --column-value-limit=1000 \
  | tee user.log
```

Once everything is imported, we can ask questions:

```shell
poetry run python python/answer.py \
  --data-source-id 1 \
  --question "What are the top orders of all time?"
```

## Training

### Table, Column, and Value Rankers

Then train the ranker:

```shell
# Build the dataset and train the models
python -m python.ranker.train

cp /tmp/datasets/ranker/values/validation_23.npz /tmp/datasets/ranker/values/tes1.npz

# or to just train on the previous dataset
TRAIN_ONLY=1 python -m python.ranker.train
```

### Few Shot Embeddings

As more evaluation quesitons are added, the few shot embeddings can be updated (and used to provide better few shot examples)

```shell
python -m python.prompts.few_shot_embeddings.builder
```

# Datasources

## Snowflake

- API responses do not return raw SQL, everything comes back as a JSON object
  - Unsure if this is just the specific API we are using or if it is a limitation of Snowflake
- You'll get a `Table 'ABANDONED_CHECKOUTS' does not exist or not authorized.` if you don't specify a specific schema when connecting.

# Connections

## Shopify

- [Staff role](https://help.shopify.com/en/manual/your-account/staff-accounts/staff-permissions/staff-permissions-descriptions#apps-and-channels-permissions) does not allow us to create API keys. API keys must be created by generating a private app, which requires a specific permissions set. [More info.](https://help.plytix.com/en/getting-api-credentials-from-your-shopify-store)
