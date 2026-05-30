"""
db_loader.py
────────────────────────────────────────────────────────────
Loads all CSVs into PostgreSQL (or SQLite for local demo).
Usage:
    python db_loader.py --db postgres   # needs a running PG instance
    python db_loader.py --db sqlite     # zero-config local demo
"""

import os, sys, argparse, pandas as pd
from sqlalchemy import create_engine, text

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

TABLES_ORDER = ['customers', 'sellers', 'products', 'orders', 'order_items', 'payments']

def get_engine(db_type: str):
    if db_type == 'postgres':
        host = os.getenv('PG_HOST', 'localhost')
        port = os.getenv('PG_PORT', '5432')
        user = os.getenv('PG_USER', 'postgres')
        pwd  = os.getenv('PG_PASS', 'password')
        db   = os.getenv('PG_DB',   'ecommerce')
        url  = f'postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}'
    else:
        url = f'sqlite:///{DATA_DIR}/ecommerce.db'
    return create_engine(url)

def load_all(engine):
    dtype_map = {
        'customers':   {'signup_date': 'datetime64[ns]'},
        'orders':      {'order_date': 'datetime64[ns]',
                        'estimated_delivery': 'datetime64[ns]',
                        'actual_delivery': 'datetime64[ns]'},
        'payments':    {'payment_date': 'datetime64[ns]'},
    }
    for table in TABLES_ORDER:
        path = os.path.join(DATA_DIR, f'{table}.csv')
        df = pd.read_csv(path)
        # fix datetime cols
        for col, dtype in dtype_map.get(table, {}).items():
            df[col] = pd.to_datetime(df[col], errors='coerce')
        df.to_sql(table, engine, if_exists='replace', index=False)
        print(f'  ✅ Loaded {table:15s} → {len(df):>7,} rows')

def run_sample_queries(engine):
    queries = {
        'Monthly Revenue (last 6)':
            "SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS orders, ROUND(SUM(order_total),2) AS revenue FROM orders WHERE status='delivered' GROUP BY 1 ORDER BY 1 DESC LIMIT 6",
        'Top 5 Categories':
            "SELECT p.category, ROUND(SUM(oi.line_total),2) AS revenue FROM order_items oi JOIN products p ON oi.product_id=p.product_id JOIN orders o ON oi.order_id=o.order_id WHERE o.status='delivered' GROUP BY p.category ORDER BY revenue DESC LIMIT 5",
        'Payment Split':
            "SELECT payment_type, COUNT(*) AS cnt FROM payments GROUP BY payment_type ORDER BY cnt DESC",
    }
    print('\n── Sample Query Results ─────────────────────────────────')
    for title, q in queries.items():
        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(q), conn)
            print(f'\n📊 {title}\n{df.to_string(index=False)}')
        except Exception as e:
            print(f'  ⚠ {title}: {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', choices=['postgres', 'sqlite'], default='sqlite')
    args = parser.parse_args()

    print(f'\n🔌 Connecting to {args.db.upper()} ...')
    engine = get_engine(args.db)
    print('📦 Loading tables ...')
    load_all(engine)
    run_sample_queries(engine)
    print('\n✅ Database ready!\n')
