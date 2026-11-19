"""
Connect to a DataStax Astra DB (Cassandra-based) database using a hardcoded
API endpoint and application token.

Based on: https://docs.datastax.com/en/astra-db-serverless/get-started/quickstart-python.html

Install the client first:
    pip install "astrapy>=2.0,<3.0"

WARNING: Hardcoding credentials is fine for quick local testing, but never
commit this file to version control or share it with the token filled in.
"""

from astrapy import DataAPIClient, Database

# ---------------------------------------------------------------------------
# Hardcoded credentials -- replace with your own values from the Astra Portal
# (Database Details -> API Endpoint / Generate Token)
# ---------------------------------------------------------------------------



def connect_to_database() -> Database:
    """
    Connects to a DataStax Astra database using the hardcoded
    API_ENDPOINT and APPLICATION_TOKEN.

    Returns:
        Database: An instance of the connected database.

    Raises:
        RuntimeError: If the endpoint or token is missing or still a placeholder.
    """
  
    # Create an instance of the `DataAPIClient` class
    client = DataAPIClient()

     # Get the database specified by your endpoint, with the token and keyspace.
    # Passing the keyspace means all later operations use it.
    database = client.get_database(
        API_ENDPOINT,
        token=APPLICATION_TOKEN,
        keyspace=KEYSPACE,
    )

    print(f"Connected to database: {database.info().name}")
    print(f"Keyspace used: {database.keyspace}")

    return database


def main() -> None:
    database = connect_to_database()

    # Confirm the keyspace exists in this database
    try:
        available = database.get_database_admin().list_keyspaces()
        print(f"Available keyspaces: {available}")
        if KEYSPACE not in available:
            print(f"WARNING: keyspace '{KEYSPACE}' was not found in this database.")
    except Exception as e:
        print(f"Could not list keyspaces: {e}")

    # List the collections inside the selected keyspace
    collections = database.list_collection_names()
    print(f"Collections in '{database.keyspace}': {collections}")


if __name__ == "__main__":
    main()
