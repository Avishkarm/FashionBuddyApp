"""
Create the `catalogimage` table (with a cosine vector index), insert sample
rows and run a vector similarity search on Astra DB.

Reuses connect_to_database() from astra_connect.py (hardcoded endpoint, token
and keyspace live there). Keep both files in the same folder.

Install the client first:
    pip install "astrapy>=2.0,<3.0"
"""

from astrapy import Database
from astrapy.constants import VectorMetric
from astrapy.info import ColumnType, CreateTableDefinition, TableVectorIndexOptions

from astra_connect import KEYSPACE, connect_to_database

TABLE_NAME = "catalogimage"
INDEX_NAME = "idx_catalogimage"


def create_tables(database: Database):
    """
    Equivalent of:
        CREATE TABLE catalogimage (
            product_id text PRIMARY KEY,
            brand text,
            catalogimageurl text,
            imagevector VECTOR<FLOAT,5>);

        CREATE CUSTOM INDEX IF NOT EXISTS idx_catalogimage
        ON catalogimage(imagevector)
        USING 'StorageAttachedIndex'
        WITH OPTIONS = {'similarity_function': 'cosine'};
    """
    definition = (
        CreateTableDefinition.builder()
        .add_column("product_id", ColumnType.TEXT)
        .add_column("brand", ColumnType.TEXT)
        .add_column("catalogimageurl", ColumnType.TEXT)
        .add_vector_column("imagevector", dimension=5)
        .add_partition_by(["product_id"])  # product_id is the PRIMARY KEY
        .build()
    )

    table = database.create_table(
        TABLE_NAME,
        definition=definition,
        if_not_exists=True,
    )
    print(f"Table '{TABLE_NAME}' ready in keyspace '{KEYSPACE}'")

    table.create_vector_index(
        INDEX_NAME,
        column="imagevector",
        options=TableVectorIndexOptions(metric=VectorMetric.COSINE),
        if_not_exists=True,
    )
    print(f"Vector index '{INDEX_NAME}' ready (cosine)")

    return table


def insert_fake_data(table) -> None:
    rows = [
        {
            "product_id": "DSH916XL ",
            "brand": "Dollar ",
            "catalogimageurl": "/Images/in/en/z1975-denim-midi-skirt-p01879223.png",
            "imagevector": [0.0126784321, -0.0185679834, -0.0051237890, -0.0159876543, 0.0082345671],
        },
        {
            "product_id": "DSA1121L ",
            "brand": "Dollar ",
            "catalogimageurl": "/Images/in/en/faux-leather-mini-skirt-with-chain-p08741264.png",
            "imagevector": [-0.0381234567, -0.0073456789, 0.0267890123, 0.0047891234, -0.1112345678],
        },
    ]

    result = table.insert_many(rows)
    print(f"Inserted {len(result.inserted_ids)} rows")


def ann_search(table) -> None:
    query_vector = [
        -0.0499644242227077,
        0.0566278323531151,
        -0.0294290613383055,
        -0.0070271748118103,
        0.0289674568921328,
    ]

    # Equivalent of: SELECT ... ORDER BY imagevector ANN OF [...] LIMIT 2
    results = table.find(
        {},
        sort={"imagevector": query_vector},
        limit=2,
        projection={"catalogimageurl": True, "brand": True},
        include_similarity=True,
    )

    print("\nTop matches:")
    for row in results:
        print(f"{row['catalogimageurl']} (brand: {row['brand'].strip()}, sim: {row['$similarity']:.4f})")


def main() -> None:
    database = connect_to_database()

    table = create_tables(database)
    insert_fake_data(table)
    ann_search(table)


if __name__ == "__main__":
    main()
