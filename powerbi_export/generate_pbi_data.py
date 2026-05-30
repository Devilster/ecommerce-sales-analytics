"""
powerbi_export.py
────────────────────────────────────────────────────────────
Exports pre-aggregated CSVs ready to import into Power BI.
Each CSV corresponds to one visual/table in the dashboard.

Power BI Import Steps:
  1. Open Power BI Desktop
  2. Get Data → Text/CSV → select each file below
  3. Create relationships on order_id / customer_id / product_id
  4. Build visuals as described in README
────────────────────────────────────────────────────────────
"""

import os, pandas as pd, numpy as np
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
DB     = os.path.join(BASE, '..', 'data', 'ecommerce.db')
OUTDIR = os.path.join(BASE, '..', 'powerbi_export')
os.makedirs(OUTDIR, exist_ok=True)

engine = create_engine(f'sqlite:///{DB}')
def q(sql): 
    with engine.connect() as c: 
        return pd.read_sql(text(sql), c)

print('📊 Generating Power BI export files ...\n')

# ── 1. Monthly Revenue KPI ────────────────────────────────────────────────────
monthly = q("""
    SELECT
        strftime('%Y-%m', order_date)   AS month,
        strftime('%Y', order_date)      AS year,
        COUNT(*)                        AS total_orders,
        ROUND(SUM(order_total),2)       AS revenue,
        ROUND(AVG(order_total),2)       AS avg_order_value,
        COUNT(DISTINCT customer_id)     AS unique_customers
    FROM orders WHERE status='delivered'
    GROUP BY 1, 2 ORDER BY 1
""")
monthly['mom_growth_pct'] = monthly['revenue'].pct_change().mul(100).round(2)
monthly.to_csv(f'{OUTDIR}/pbi_monthly_kpi.csv', index=False)
print(f'  ✅ pbi_monthly_kpi.csv          → {len(monthly):>4} rows')

# ── 2. Category Revenue ───────────────────────────────────────────────────────
cat_rev = q("""
    SELECT
        p.category,
        COUNT(DISTINCT o.order_id)          AS orders,
        ROUND(SUM(oi.line_total),2)         AS revenue,
        ROUND(SUM(oi.profit_proxy),2)       AS est_profit,
        ROUND(AVG(p.rating),2)              AS avg_rating
    FROM (
        SELECT oi.*, (oi.line_total * 0.35) AS profit_proxy
        FROM order_items oi
    ) oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders   o ON oi.order_id   = o.order_id
    WHERE o.status = 'delivered'
    GROUP BY p.category ORDER BY revenue DESC
""")
cat_rev.to_csv(f'{OUTDIR}/pbi_category_revenue.csv', index=False)
print(f'  ✅ pbi_category_revenue.csv     → {len(cat_rev):>4} rows')

# ── 3. State Revenue ──────────────────────────────────────────────────────────
state_rev = q("""
    SELECT
        state,
        COUNT(DISTINCT order_id)        AS orders,
        ROUND(SUM(order_total),2)       AS revenue,
        COUNT(DISTINCT customer_id)     AS customers,
        ROUND(AVG(order_total),2)       AS avg_order_value
    FROM orders WHERE status='delivered'
    GROUP BY state ORDER BY revenue DESC
""")
state_rev.to_csv(f'{OUTDIR}/pbi_state_revenue.csv', index=False)
print(f'  ✅ pbi_state_revenue.csv        → {len(state_rev):>4} rows')

# ── 4. Payment Analysis ───────────────────────────────────────────────────────
pay = q("""
    SELECT
        payment_type,
        COUNT(*)                        AS transactions,
        ROUND(SUM(amount),2)            AS total_amount,
        ROUND(AVG(amount),2)            AS avg_amount,
        ROUND(AVG(installments),1)      AS avg_installments
    FROM payments GROUP BY payment_type ORDER BY transactions DESC
""")
pay.to_csv(f'{OUTDIR}/pbi_payment_analysis.csv', index=False)
print(f'  ✅ pbi_payment_analysis.csv     → {len(pay):>4} rows')

# ── 5. Delivery Performance ───────────────────────────────────────────────────
delivery = q("""
    SELECT
        order_id, state, status,
        ROUND(JULIANDAY(actual_delivery) - JULIANDAY(order_date), 1) AS delivery_days,
        CASE WHEN actual_delivery <= estimated_delivery THEN 'On Time' ELSE 'Late' END AS delivery_status
    FROM orders
    WHERE status='delivered' AND actual_delivery IS NOT NULL
""")
delivery.to_csv(f'{OUTDIR}/pbi_delivery_performance.csv', index=False)
print(f'  ✅ pbi_delivery_performance.csv → {len(delivery):>4} rows')

# ── 6. Customer CLV ───────────────────────────────────────────────────────────
clv = q("""
    SELECT
        c.customer_id, c.name, c.state, c.city,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        ROUND(SUM(o.order_total),2)         AS lifetime_value,
        ROUND(AVG(o.order_total),2)         AS avg_order_value,
        MIN(date(o.order_date))             AS first_order,
        MAX(date(o.order_date))             AS last_order
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status='delivered'
    GROUP BY c.customer_id, c.name, c.state, c.city
    ORDER BY lifetime_value DESC
""")
clv['segment'] = pd.cut(clv['lifetime_value'],
                         bins=[0,50000,200000,500000,float('inf')],
                         labels=['Bronze','Silver','Gold','Platinum'])
clv.to_csv(f'{OUTDIR}/pbi_customer_clv.csv', index=False)
print(f'  ✅ pbi_customer_clv.csv         → {len(clv):>4} rows')

# ── 7. Top Products ───────────────────────────────────────────────────────────
top_products = q("""
    SELECT
        p.product_id, p.product_name, p.category,
        p.price, p.rating, p.reviews_count,
        COUNT(DISTINCT oi.order_id)         AS times_ordered,
        ROUND(SUM(oi.line_total),2)         AS total_revenue
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o       ON oi.order_id  = o.order_id
    WHERE o.status = 'delivered'
    GROUP BY p.product_id, p.product_name, p.category, p.price, p.rating, p.reviews_count
    ORDER BY total_revenue DESC LIMIT 50
""")
top_products.to_csv(f'{OUTDIR}/pbi_top_products.csv', index=False)
print(f'  ✅ pbi_top_products.csv         → {len(top_products):>4} rows')

# ── 8. Order Status Summary ───────────────────────────────────────────────────
status_summary = q("""
    SELECT
        status,
        COUNT(*)                        AS orders,
        ROUND(SUM(order_total),2)       AS order_value,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(), 2) AS pct
    FROM orders GROUP BY status ORDER BY orders DESC
""")
status_summary.to_csv(f'{OUTDIR}/pbi_order_status.csv', index=False)
print(f'  ✅ pbi_order_status.csv         → {len(status_summary):>4} rows')

print(f'\n✅ All Power BI export files saved to: {OUTDIR}')
print('\n📌 Power BI Dashboard Layout Suggestion:')
print('   Page 1 → KPI Cards + Monthly Revenue Line Chart')
print('   Page 2 → Category Bar + Payment Donut + State Map')
print('   Page 3 → Delivery Gauge + CLV Segments + Top Products Table')
