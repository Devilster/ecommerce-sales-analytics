import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

# ── Config ────────────────────────────────────────────────────────────────────
N_CUSTOMERS   = 2_000
N_PRODUCTS    = 500
N_ORDERS      = 10_000
N_SELLERS     = 150
OUT           = os.path.dirname(__file__)

# ── Reference data ────────────────────────────────────────────────────────────
CATEGORIES = {
    'Electronics':       (5_000, 80_000),
    'Fashion':           (500,   8_000),
    'Home & Furniture':  (1_000, 50_000),
    'Books':             (200,   2_000),
    'Sports & Fitness':  (500,   15_000),
    'Beauty & Health':   (300,   5_000),
    'Toys & Games':      (300,   6_000),
    'Grocery':           (100,   2_000),
    'Automotive':        (1_000, 40_000),
    'Jewellery':         (2_000, 100_000),
}

STATES = ['Maharashtra','Delhi','Karnataka','Tamil Nadu','Telangana',
          'Gujarat','Rajasthan','Uttar Pradesh','West Bengal','Pune',
          'Haryana','Kerala','Madhya Pradesh','Bihar','Odisha']

PAYMENT_TYPES = ['Credit Card','Debit Card','UPI','Net Banking','Cash on Delivery']
ORDER_STATUSES = ['delivered','delivered','delivered','delivered',
                  'shipped','cancelled','returned','processing']

# ── 1. Customers ──────────────────────────────────────────────────────────────
customers = pd.DataFrame({
    'customer_id':   [f'C{str(i).zfill(5)}' for i in range(1, N_CUSTOMERS+1)],
    'name':          [fake.name()            for _ in range(N_CUSTOMERS)],
    'email':         [fake.email()           for _ in range(N_CUSTOMERS)],
    'city':          [fake.city()            for _ in range(N_CUSTOMERS)],
    'state':         np.random.choice(STATES, N_CUSTOMERS),
    'pincode':       [fake.postcode()        for _ in range(N_CUSTOMERS)],
    'signup_date':   pd.date_range('2021-01-01', periods=N_CUSTOMERS, freq='4h')[:N_CUSTOMERS],
})

# ── 2. Products ───────────────────────────────────────────────────────────────
cat_names = list(CATEGORIES.keys())
products_rows = []
for i in range(1, N_PRODUCTS+1):
    cat  = random.choice(cat_names)
    lo, hi = CATEGORIES[cat]
    price   = round(random.uniform(lo, hi), 2)
    cost    = round(price * random.uniform(0.4, 0.75), 2)
    products_rows.append({
        'product_id':   f'P{str(i).zfill(4)}',
        'product_name': f'{cat} Product {i}',
        'category':     cat,
        'price':        price,
        'cost_price':   cost,
        'stock':        random.randint(0, 500),
        'rating':       round(random.uniform(2.5, 5.0), 1),
        'reviews_count':random.randint(1, 5000),
    })
products = pd.DataFrame(products_rows)

# ── 3. Sellers ────────────────────────────────────────────────────────────────
sellers = pd.DataFrame({
    'seller_id':   [f'S{str(i).zfill(3)}' for i in range(1, N_SELLERS+1)],
    'seller_name': [fake.company()         for _ in range(N_SELLERS)],
    'state':       np.random.choice(STATES, N_SELLERS),
    'rating':      np.round(np.random.uniform(2.5, 5.0, N_SELLERS), 1),
})

# ── 4. Orders ─────────────────────────────────────────────────────────────────
start = datetime(2022, 1, 1)
end   = datetime(2024, 12, 31)
delta = (end - start).days

orders_rows = []
items_rows  = []
payments_rows = []

for i in range(1, N_ORDERS+1):
    oid        = f'ORD{str(i).zfill(6)}'
    cid        = random.choice(customers['customer_id'].tolist())
    sid        = random.choice(sellers['seller_id'].tolist())
    order_date = start + timedelta(days=random.randint(0, delta),
                                   hours=random.randint(0,23))
    status     = random.choice(ORDER_STATUSES)

    # delivery window
    est_days   = random.randint(3, 10)
    est_del    = order_date + timedelta(days=est_days)
    if status == 'delivered':
        actual_del = est_del + timedelta(days=random.randint(-2, 5))
    else:
        actual_del = None

    n_items    = random.randint(1, 5)
    total      = 0
    for j in range(n_items):
        pid   = random.choice(products['product_id'].tolist())
        qty   = random.randint(1, 3)
        price = float(products.loc[products['product_id']==pid,'price'].values[0])
        disc  = round(random.uniform(0, 0.30) * price * qty, 2)
        line  = round(price * qty - disc, 2)
        total += line
        items_rows.append({
            'item_id':    f'IT{str(len(items_rows)+1).zfill(7)}',
            'order_id':   oid,
            'product_id': pid,
            'quantity':   qty,
            'unit_price': price,
            'discount':   disc,
            'line_total':  line,
        })

    orders_rows.append({
        'order_id':          oid,
        'customer_id':       cid,
        'seller_id':         sid,
        'order_date':        order_date,
        'estimated_delivery':est_del,
        'actual_delivery':   actual_del,
        'status':            status,
        'order_total':       round(total, 2),
        'state':             customers.loc[customers['customer_id']==cid,'state'].values[0],
    })

    pay_method = random.choice(PAYMENT_TYPES)
    installments = random.randint(1,12) if pay_method=='Credit Card' else 1
    payments_rows.append({
        'payment_id':    f'PAY{str(i).zfill(6)}',
        'order_id':      oid,
        'payment_type':  pay_method,
        'installments':  installments,
        'amount':        round(total, 2),
        'payment_date':  order_date + timedelta(minutes=random.randint(1,30)),
    })

orders   = pd.DataFrame(orders_rows)
items    = pd.DataFrame(items_rows)
payments = pd.DataFrame(payments_rows)

# ── Save CSVs ─────────────────────────────────────────────────────────────────
customers.to_csv(f'{OUT}/customers.csv', index=False)
products.to_csv(f'{OUT}/products.csv',   index=False)
sellers.to_csv(f'{OUT}/sellers.csv',     index=False)
orders.to_csv(f'{OUT}/orders.csv',       index=False)
items.to_csv(f'{OUT}/order_items.csv',   index=False)
payments.to_csv(f'{OUT}/payments.csv',   index=False)

print("✅ Datasets generated:")
for name, df in [('customers',customers),('products',products),
                 ('sellers',sellers),('orders',orders),
                 ('order_items',items),('payments',payments)]:
    print(f"   {name:15s} → {len(df):>7,} rows")
