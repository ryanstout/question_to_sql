# Sql Transforms

The results we get from OpenAI are closest to Postgres format and need to be transformed to snowflake's dialiect (or similar in the future). This requires the following translations:

## 1. Expand table names to fully qualified names

To be able to query across databases in snowflake, the easiest thing to do is to use fully qualified table names. For MVP, we assume no duplicate table names across all databases. (TODO: expand duplicate table names in prompt)

## 2. Cast numerator of divides to float

When asking for something like "What percent of users are over 25?", the resulting query will have a divide of two int's that needs to be cast to a float to get out a percent.
