# Ranker Models

A set of models to estimate weights for each table, column, and value hint. Used when generating the schema for the prompt.

# Models

Each model takes in a set of ranking embedding cosine distances (between the query embedding and the table, column or value hint) and/or a histogram of weights downstream (for columns, a histogram of predicted weights for the child value hints. For tables, a histogram of the predicted column estimates)

Quick reminder on the embedding indexes:

### For Tables:

- table name => table
- table + column names => table
- table + columns + all values => table

### For Columns

- column name => column, table
- column name + all column values => column, table

### For values

- value (column@row) => value, column, table
- table name, column name, and value (for row) => value, column, table

# Rankers

Each ranker model is run bottom to top so the outputs of its children can be used as features. The models further up (column, then table) have the task of reweighting to balance around the models below.

## Value Ranker

Run first, simple blend of two embedding indexes

## Column Ranker

Takes the following:

- histogram of value rankings from the child values
- weights of the two query embedding matches for the column

## Table Ranker

Takes the following:

- histogram of column rankings from the child columns
- weights of the two query embedding matches for the column
