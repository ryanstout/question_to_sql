# Prompt Embeddings

Due to the limited size of current LLM prompts, we need to do some pre-prompt work to filter tables, columns, and column hints based on the question asked. We can use any neural embeddings matched against the question to filter.

We index the following, with pointers to a table, column, or value (for Value Hints). We use the pointers to increase the weights on each table, column, and value when generating tables, columns, and value hints respectively:

[the numbers below correspond to EmbeddingLink#indexNumber]

0. table name => table
1. column name => column, table
2. value (column@row) => value, column, table

The following aggerate indexes are also created. These help find "theme" type matches. (I'm asking about cities and all of the examples are cities. So if a question the LLM embeddings knows you mentioned a city, but isn't in a value in the currnet list of cities, it will still match the column (and correctly return 0 results), eg. "How many orders do we have from Sidney MT?")

3. table + column names => table
4. table + columns + all values => table
5. column name + all column values => column, table

# Few Shot Question Embeddings

Questions can also be matched to similar training question/answers using the embeddings.

question => question
