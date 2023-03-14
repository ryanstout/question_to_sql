# NLP Query

A BI tool that lets you dig into your data using natural language

# Development

All local installation is documented in:

```shell
bin/setup.sh
npm run dev
```

# Deployment

Attach the python app to the database:

```shell
fly pg attach knolbe-db --config python.toml --database-name knolbe
```

Proxy to the prod DB for inspection:

```shell
fly proxy 5431:5432 -a knolbe-db
```

Upload stuff to prod ([helpful post](https://community.fly.io/t/scp-a-file-into-a-persistent-volume/2729))

1. auth your machine `flyctl ssh issue --agent`
2. Get wireguard setup and connected
3. upload trained model `scp -r tmp/models root@knolbe-python.internal:/persisted-data/models`
4. upload indexes `scp -r tmp/indexes root@knolbe-python.internal:/persisted-data/indexes`

Increase persistence size (in gbs):

```shell
fly volumes extend vol_okgj5451oe8vy2wz -s 10 --config python.toml
```

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

## Train Table, Column, and Value Rankers

```shell
# Build the dataset and train the models
python -m python.ranker.train

# or to just train on the previous dataset
TRAIN_ONLY=1 python -m python.ranker.train
```

# Few Shot Embeddings

As more evaluation quesitons are added, the few shot embeddings can be updated (and used to provide better few shot examples)

```shell
python -m python.prompts.few_shot_embeddings.builder
```

# Datasources

## Snowflake

- API responses do not return raw SQL, everything comes back as a JSON object
  - Unsure if this is just the specific API we are using or if it is a limitation of Snowflake
- You'll get a `Table 'ABANDONED_CHECKOUTS' does not exist or not authorized.` if you don't specify a specific schema when

# Connections

## Shopify

- [Staff role](https://help.shopify.com/en/manual/your-account/staff-accounts/staff-permissions/staff-permissions-descriptions#apps-and-channels-permissions) does not allow us to create API keys. API keys must be created by generating a private app, which requires a specific permissions set. [More info.](https://help.plytix.com/en/getting-api-credentials-from-your-shopify-store)
