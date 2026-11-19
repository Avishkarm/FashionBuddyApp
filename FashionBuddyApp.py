
"""
FashionBuddyApp -- main entry point.

A small command-line app on top of the Astra DB `catalogimage` table:
  1. Set up the table and vector index
  2. Load the sample products
  3. Add a product
  4. List products
  5. Find visually similar products from an image vector

Requires astra_connect.py and astra_catalogimage.py in the same folder.

Run:
    python FashionBuddyApp.py
"""

import sys
from pathlib import Path

# Make the DBCode folder importable (it sits next to this file)
sys.path.append(str(Path(__file__).resolve().parent / "DBCode"))

from astra_catalogimage import TABLE_NAME, create_tables, insert_fake_data
from astra_connect import connect_to_database
VECTOR_DIM = 5  # must match the dimension of the `imagevector` column


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def add_product(table, product_id: str, brand: str, image_url: str, vector: list[float]) -> None:
    if len(vector) != VECTOR_DIM:
        raise ValueError(f"Vector must have {VECTOR_DIM} values, got {len(vector)}")

    table.insert_one(
        {
            "product_id": product_id,
            "brand": brand,
            "catalogimageurl": image_url,
            "imagevector": vector,
        }
    )


def list_products(table, limit: int = 20) -> list[dict]:
    return list(
        table.find(
            {},
            limit=limit,
            projection={"product_id": True, "brand": True, "catalogimageurl": True},
        )
    )


def find_similar(table, vector: list[float], top_k: int = 2, brand: str | None = None) -> list[dict]:
    """Return the top_k closest products, optionally filtered by brand."""
    if len(vector) != VECTOR_DIM:
        raise ValueError(f"Vector must have {VECTOR_DIM} values, got {len(vector)}")

    filter_ = {"brand": brand} if brand else {}

    return list(
        table.find(
            filter_,
            sort={"imagevector": vector},
            limit=top_k,
            projection={"product_id": True, "brand": True, "catalogimageurl": True},
            include_similarity=True,
        )
    )


def parse_vector(text: str) -> list[float]:
    return [float(x) for x in text.replace("[", "").replace("]", "").split(",")]


# ---------------------------------------------------------------------------
# Command-line menu
# ---------------------------------------------------------------------------
MENU = """
=== FashionBuddy ===
1. Set up table and index
2. Load sample products
3. Add a product
4. List products
5. Find similar products
0. Exit
"""


def main() -> None:
    database = connect_to_database()
    table = None

    def get_table():
        nonlocal table
        if table is None:
            table = database.get_table(TABLE_NAME)
        return table

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                table = create_tables(database)

            elif choice == "2":
                insert_fake_data(get_table())

            elif choice == "3":
                product_id = input("Product ID: ").strip()
                brand = input("Brand: ").strip()
                url = input("Image URL: ").strip()
                vector = parse_vector(input(f"Image vector ({VECTOR_DIM} comma-separated numbers): "))
                add_product(get_table(), product_id, brand, url, vector)
                print("Product added.")

            elif choice == "4":
                for row in list_products(get_table()):
                    print(f"{row['product_id']} | {row['brand']} | {row['catalogimageurl']}")

            elif choice == "5":
                vector = parse_vector(input(f"Query vector ({VECTOR_DIM} comma-separated numbers): "))
                brand = input("Filter by brand (leave blank for all): ").strip() or None
                for row in find_similar(get_table(), vector, brand=brand):
                    print(f"{row['catalogimageurl']} (brand: {row['brand']}, sim: {row['$similarity']:.4f})")

            elif choice == "0":
                print("Goodbye!")
                break

            else:
                print("Invalid option.")

        except Exception as e:  # keep the menu running after an error
            print(f"Error: {e}")


if __name__ == "__main__":
    main()