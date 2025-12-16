import duckdb
import os

db_path = 'Machine Learning/artifacts/ml_analytics.duckdb'

if not os.path.exists(db_path):
    print(f"Error: File not found at {db_path}")
    exit(1)

con = duckdb.connect(db_path)

print("--- Tables ---")
try:
    tables = con.execute("SHOW TABLES").fetchall()
    if not tables:
        print("No tables found.")
    for table in tables:
        print(table[0])

    print("\n--- Content Preview ---")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        try:
            print("Schema:")
            print(con.execute(f"DESCRIBE {table_name}").df())
            print("-" * 20)
            print("Data:")
            print(con.execute(f"SELECT * FROM {table_name} LIMIT 5").df())
        except Exception as e:
            print(f"Error reading table {table_name}: {e}")
except Exception as e:
    print(f"Error connecting or querying: {e}")

con.close()
