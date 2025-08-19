
import sqlite3
import pandas as pd
from pathlib import Path

# === CONFIG ===
DB_PATH = "food_waste.db"

# Correct paths (no extra space after 'dataset\')
PROVIDERS_CSV = r"C:\Users\B santosh\Downloads\labmantexi\task4\task4\dataset\providers_data.csv"
RECEIVERS_CSV = r"C:\Users\B santosh\Downloads\labmantexi\task4\task4\dataset\receivers_data.csv"
FOOD_LISTINGS_CSV = r"C:\Users\B santosh\Downloads\labmantexi\task4\task4\dataset\food_listings_data.csv"
CLAIMS_CSV = r"C:\Users\B santosh\Downloads\labmantexi\task4\task4\dataset\claims_data.csv"


def create_conn(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        provider_id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        address TEXT,
        city TEXT,
        contact TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS receivers (
        receiver_id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        city TEXT,
        contact TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_listings (
        food_id INTEGER PRIMARY KEY,
        food_name TEXT,
        quantity INTEGER,
        expiry_date TEXT,
        provider_id INTEGER,
        provider_type TEXT,
        location TEXT,
        food_type TEXT,
        meal_type TEXT,
        FOREIGN KEY(provider_id) REFERENCES providers(provider_id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        claim_id INTEGER PRIMARY KEY,
        food_id INTEGER,
        receiver_id INTEGER,
        status TEXT,
        timestamp TEXT,
        FOREIGN KEY(food_id) REFERENCES food_listings(food_id) ON DELETE CASCADE,
        FOREIGN KEY(receiver_id) REFERENCES receivers(receiver_id) ON DELETE SET NULL
    );
    """)

    conn.commit()

def load_csv_safe(path):
    if not Path(path).exists():
        print(f"WARNING: CSV not found: {path}")
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"ERROR reading {path}: {e}")
        return None

def normalize_columns(df):
    if df is None:
        return None
    # Unify column names (strip/underscore/lower)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def insert_df(conn, table, df):
    if df is None or df.empty:
        print(f"Skipping insert for {table}: empty or None")
        return
    df.to_sql(table, conn, if_exists="append", index=False)

def main():
    conn = create_conn()
    create_tables(conn)

    # Load and normalize
    providers = normalize_columns(load_csv_safe(PROVIDERS_CSV))
    receivers = normalize_columns(load_csv_safe(RECEIVERS_CSV))
    food = normalize_columns(load_csv_safe(FOOD_LISTINGS_CSV))
    claims = normalize_columns(load_csv_safe(CLAIMS_CSV))

    # Optionally map columns to expected names if needed
    # Providers
    if providers is not None:
        providers = providers.rename(columns={
            "provider_id":"provider_id",
            "name":"name",
            "type":"type",
            "address":"address",
            "city":"city",
            "contact":"contact",
        })
        providers = providers[["provider_id","name","type","address","city","contact"]]

    # Receivers
    if receivers is not None:
        receivers = receivers.rename(columns={
            "receiver_id":"receiver_id",
            "name":"name",
            "type":"type",
            "city":"city",
            "contact":"contact",
        })
        receivers = receivers[["receiver_id","name","type","city","contact"]]

    # Food listings
    if food is not None:
        food = food.rename(columns={
            "food_id":"food_id",
            "food_name":"food_name",
            "quantity":"quantity",
            "expiry_date":"expiry_date",
            "provider_id":"provider_id",
            "provider_type":"provider_type",
            "location":"location",
            "food_type":"food_type",
            "meal_type":"meal_type",
        })
        food = food[["food_id","food_name","quantity","expiry_date","provider_id","provider_type","location","food_type","meal_type"]]

    # Claims
    if claims is not None:
        claims = claims.rename(columns={
            "claim_id":"claim_id",
            "food_id":"food_id",
            "receiver_id":"receiver_id",
            "status":"status",
            "timestamp":"timestamp",
        })
        claims = claims[["claim_id","food_id","receiver_id","status","timestamp"]]

    # Clear existing data to avoid duplicates
    cur = conn.cursor()
    for t in ["claims", "food_listings", "receivers", "providers"]:
        cur.execute(f"DELETE FROM {t};")
    conn.commit()

    insert_df(conn, "providers", providers)
    insert_df(conn, "receivers", receivers)
    insert_df(conn, "food_listings", food)
    insert_df(conn, "claims", claims)

    # Simple indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_food_provider ON food_listings(provider_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_claims_food ON claims(food_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_claims_receiver ON claims(receiver_id);")
    conn.commit()

    print("Database created and populated at", DB_PATH)

if __name__ == "__main__":
    main()
