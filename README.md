# Astra DB Catalog Image Vector Search

Python scripts and Google Colab notebooks that connect to a [DataStax Astra DB](https://docs.datastax.com/en/astra-db-serverless/get-started/quickstart-tables-python.html) (Cassandra-based) database, create a `catalogimage` table with a vector column and cosine vector index, insert sample rows, and run a vector similarity search.

The project uses the Astra DB **Data API** through the [`astrapy`](https://github.com/datastax/astrapy) client (version 2.x), not the native Cassandra CQL driver.

---

## Project structure

```
.
├── astra_connect.py                  # Connection helper (hardcoded endpoint, token, keyspace)
├── astra_catalogimage.py             # Creates table + index, inserts data, runs vector search
├── astra_connect_colab.ipynb         # Colab notebook: connection test only
├── astra_catalogimage_colab.ipynb    # Colab notebook: full setup, insert and search
└── README.md
```

| File | Purpose |
|---|---|
| `astra_connect.py` | Defines `API_ENDPOINT`, `APPLICATION_TOKEN` and `KEYSPACE`, and `connect_to_database()`. Prints the database name and the keyspace in use, and lists keyspaces and collections as a sanity check. |
| `astra_catalogimage.py` | Imports `connect_to_database` and `KEYSPACE` from `astra_connect.py`, then creates the table, inserts two sample rows and runs a top-2 similarity search. |
| `astra_connect_colab.ipynb` | Self-contained Colab version of the connection check. |
| `astra_catalogimage_colab.ipynb` | Self-contained Colab version of the full flow (connect, create, insert, search). |

---

## Prerequisites

- An [Astra DB](https://astra.datastax.com) account and a **Serverless (vector)** database
- Python 3.10 or later and pip 23.0 or later (for local runs), or a Google Colab account
- Your database's **API endpoint** and an **application token**:
  1. In the Astra Portal, open your database.
  2. Under **Database Details**, copy the **API Endpoint**.
  3. Click **Generate Token** and copy it (it starts with `AstraCS:`).

---

## Setup

### 1. Install the client

```bash
pip install "astrapy>=2.0,<3.0"
```

### 2. Add your credentials

Open `astra_connect.py` and replace the placeholder values:

```python
API_ENDPOINT = "https://<DATABASE_ID>-<REGION>.apps.astra.datastax.com"
APPLICATION_TOKEN = "AstraCS:xxxxxxxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
KEYSPACE = "default_keyspace"   # change to your keyspace, e.g. "fashiondb"
```

The scripts raise an error if the endpoint or token is still a placeholder.

> **Security warning:** the endpoint and token are hardcoded for convenience. Never commit these files to version control, or share them, with a real token filled in. Rotate the token in the Astra Portal if it is ever exposed.

---

## Usage

### Run locally

Test the connection:

```bash
python astra_connect.py
```

Create the table and index, insert data and run the search:

```bash
python astra_catalogimage.py
```

Keep `astra_connect.py` and `astra_catalogimage.py` in the same folder, since the second imports from the first.

### Run in Google Colab

1. Go to [colab.research.google.com](https://colab.research.google.com) and choose **File > Upload notebook**.
2. Upload `astra_catalogimage_colab.ipynb` (or `astra_connect_colab.ipynb` for just the connection test).
3. Edit `API_ENDPOINT`, `APPLICATION_TOKEN` and `KEYSPACE` in the credentials cell.
4. Run the cells in order (**Runtime > Run all**).

---

## What the project does

### Table schema

| Column | Type | Notes |
|---|---|---|
| `product_id` | text | Primary key |
| `brand` | text | |
| `catalogimageurl` | text | |
| `imagevector` | vector (5 dimensions, float) | Indexed with a cosine vector index (`idx_catalogimage`) |

### Flow

1. **Connect** to the database with the hardcoded endpoint, token and keyspace, and print the keyspace in use.
2. **Create** the `catalogimage` table and the `idx_catalogimage` vector index. Both steps use `if_not_exists=True`, so rerunning is safe.
3. **Insert** two sample rows.
4. **Search** for the 2 rows closest to a sample query vector and print each image URL, brand and similarity score.

### CQL to Data API mapping

The original CQL-style setup was translated to Data API calls:

| CQL | Data API (`astrapy`) |
|---|---|
| `CREATE TABLE catalogimage (...)` | `database.create_table(...)` with `CreateTableDefinition` |
| `CREATE CUSTOM INDEX ... 'StorageAttachedIndex'` (cosine) | `table.create_vector_index(..., metric=VectorMetric.COSINE)` |
| `INSERT INTO ...` | `table.insert_many(rows)` |
| `ORDER BY imagevector ANN OF [...] LIMIT 2` | `table.find(sort={"imagevector": [...]}, limit=2, include_similarity=True)` |

---

## Troubleshooting

### `Cannot have more than 100 indexes`

The database has reached its total SAI index limit. For Astra DB Serverless databases this is 100 indexes in total (50 for databases created before June 24, 2024), with at most 10 per table. Collections automatically create up to 10 indexes each, so a few collections can use the whole budget.

To fix it:

1. Inspect what is using the indexes:
   ```python
   print("Collections:", database.list_collection_names())
   for name in database.list_table_names():
       t = database.get_table(name)
       print(f"Table {name}: indexes = {t.list_index_names()}")
   ```
2. Drop collections, tables or indexes you no longer need (this is permanent):
   ```python
   database.drop_collection("unused_collection_name")
   database.get_table("some_table").drop_index("index_name")
   ```
3. Or use a different database and update the endpoint, token and keyspace.

The table is created before the index step, so after freeing capacity you can simply rerun.

### pip warning about `ipython` / `google-colab` in Colab

```
google-colab requires ipython==7.34.0, but you have ipython ...
```

This is a dependency warning in Colab's own environment, not an `astrapy` failure. Confirm the install worked with `import astrapy; print(astrapy.__version__)`. If anything behaves oddly, use **Runtime > Restart session** and rerun.

### Keyspace not found

The connection check lists the keyspaces in your database and warns if `KEYSPACE` is not one of them. Check the name in the Astra Portal, or create one from code:

```python
database.get_database_admin().create_keyspace("my_keyspace")
```

---

## Notes

- The sample data has trailing spaces in some values (for example `'DSH916XL '` and `'Dollar '`). They are kept as provided, so the `product_id` values include the space. Remove them in `astra_catalogimage.py` or the notebook if they are typos.
- The Data API returns a normalised cosine similarity score (0 to 1), so values can differ from CQL's `similarity_cosine`. The ranking is the same.
- Vector similarity search on Astra requires a vector index on the column.
- Tables in the Data API require client version 2.0.x or later.

---

## References

- [Astra DB Serverless quickstart for collections (Python)](https://docs.datastax.com/en/astra-db-serverless/get-started/quickstart-python.html)
- [Astra DB Serverless quickstart for tables (Python)](https://docs.datastax.com/en/astra-db-serverless/get-started/quickstart-tables-python.html)
- [Astra DB Serverless database limits](https://docs.datastax.com/en/astra-db-serverless/databases/database-limits.html)
- [astrapy on GitHub](https://github.com/datastax/astrapy)
