-- ============================================================
--  E-Commerce Analytics — PostgreSQL Schema & Business Queries
--  Project: E-Commerce Sales Analytics Dashboard
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  1. SCHEMA CREATION
-- ────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS payments    CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders      CASCADE;
DROP TABLE IF EXISTS products    CASCADE;
DROP TABLE IF EXISTS sellers     CASCADE;
DROP TABLE IF EXISTS customers   CASCADE;

CREATE TABLE customers (
    customer_id  VARCHAR(10)  PRIMARY KEY,
    name         VARCHAR(100),
    email        VARCHAR(150),
    city         VARCHAR(100),
    state        VARCHAR(100),
    pincode      VARCHAR(10),
    signup_date  TIMESTAMP
);

CREATE TABLE sellers (
    seller_id    VARCHAR(10)  PRIMARY KEY,
    seller_name  VARCHAR(150),
    state        VARCHAR(100),
    rating       NUMERIC(3,1)
);

CREATE TABLE products (
    product_id    VARCHAR(10)  PRIMARY KEY,
    product_name  VARCHAR(200),
    category      VARCHAR(100),
    price         NUMERIC(12,2),
    cost_price    NUMERIC(12,2),
    stock         INTEGER,
    rating        NUMERIC(3,1),
    reviews_count INTEGER
);

CREATE TABLE orders (
    order_id           VARCHAR(12) PRIMARY KEY,
    customer_id        VARCHAR(10) REFERENCES customers(customer_id),
    seller_id          VARCHAR(10) REFERENCES sellers(seller_id),
    order_date         TIMESTAMP,
    estimated_delivery TIMESTAMP,
    actual_delivery    TIMESTAMP,
    status             VARCHAR(30),
    order_total        NUMERIC(14,2),
    state              VARCHAR(100)
);

CREATE TABLE order_items (
    item_id     VARCHAR(12) PRIMARY KEY,
    order_id    VARCHAR(12) REFERENCES orders(order_id),
    product_id  VARCHAR(10) REFERENCES products(product_id),
    quantity    INTEGER,
    unit_price  NUMERIC(12,2),
    discount    NUMERIC(12,2),
    line_total  NUMERIC(12,2)
);

CREATE TABLE payments (
    payment_id    VARCHAR(12) PRIMARY KEY,
    order_id      VARCHAR(12) REFERENCES orders(order_id),
    payment_type  VARCHAR(30),
    installments  INTEGER,
    amount        NUMERIC(14,2),
    payment_date  TIMESTAMP
);

-- ────────────────────────────────────────────────────────────
--  2. LOAD DATA  (run after \copy or psycopg2 bulk insert)
-- ────────────────────────────────────────────────────────────
-- \copy customers   FROM 'data/customers.csv'   CSV HEADER;
-- \copy sellers     FROM 'data/sellers.csv'     CSV HEADER;
-- \copy products    FROM 'data/products.csv'    CSV HEADER;
-- \copy orders      FROM 'data/orders.csv'      CSV HEADER;
-- \copy order_items FROM 'data/order_items.csv' CSV HEADER;
-- \copy payments    FROM 'data/payments.csv'    CSV HEADER;


-- ────────────────────────────────────────────────────────────
--  3. BUSINESS QUERIES
-- ────────────────────────────────────────────────────────────

-- Q1: Monthly Revenue Trend
SELECT
    DATE_TRUNC('month', order_date)::DATE AS month,
    COUNT(*)                              AS total_orders,
    SUM(order_total)                      AS revenue,
    AVG(order_total)                      AS avg_order_value
FROM orders
WHERE status = 'delivered'
GROUP BY 1
ORDER BY 1;

-- Q2: Top 10 Categories by Revenue
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)            AS orders,
    SUM(oi.line_total)                    AS total_revenue,
    ROUND(AVG(p.rating),2)                AS avg_rating
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status = 'delivered'
GROUP BY p.category
ORDER BY total_revenue DESC
LIMIT 10;

-- Q3: Revenue by State
SELECT
    o.state,
    COUNT(DISTINCT o.order_id)  AS orders,
    SUM(o.order_total)          AS revenue,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM orders o
WHERE o.status = 'delivered'
GROUP BY o.state
ORDER BY revenue DESC;

-- Q4: Payment Method Distribution
SELECT
    payment_type,
    COUNT(*)                    AS transactions,
    SUM(amount)                 AS total_amount,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM payments
GROUP BY payment_type
ORDER BY transactions DESC;

-- Q5: Delivery Performance (on-time vs late)
SELECT
    CASE WHEN actual_delivery <= estimated_delivery THEN 'On Time'
         ELSE 'Late' END             AS delivery_status,
    COUNT(*)                         AS orders,
    ROUND(AVG(
        EXTRACT(EPOCH FROM (actual_delivery - order_date))/86400
    ),1)                             AS avg_days_to_deliver
FROM orders
WHERE status = 'delivered'
  AND actual_delivery IS NOT NULL
GROUP BY 1;

-- Q6: Customer Lifetime Value (Top 20)
SELECT
    c.customer_id,
    c.name,
    c.state,
    COUNT(DISTINCT o.order_id)  AS total_orders,
    SUM(o.order_total)          AS lifetime_value,
    MIN(o.order_date)           AS first_order,
    MAX(o.order_date)           AS last_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'delivered'
GROUP BY c.customer_id, c.name, c.state
ORDER BY lifetime_value DESC
LIMIT 20;

-- Q7: Seller Performance
SELECT
    s.seller_id,
    s.seller_name,
    s.state,
    COUNT(DISTINCT o.order_id)  AS orders_handled,
    SUM(o.order_total)          AS revenue_generated,
    s.rating                    AS seller_rating
FROM sellers s
JOIN orders o ON s.seller_id = o.seller_id
WHERE o.status = 'delivered'
GROUP BY s.seller_id, s.seller_name, s.state, s.rating
ORDER BY revenue_generated DESC
LIMIT 15;

-- Q8: Month-over-Month Revenue Growth (Window Function)
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS month,
        SUM(order_total) AS revenue
    FROM orders WHERE status = 'delivered'
    GROUP BY 1
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month)   AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- Q9: Product Profit Margin Analysis
SELECT
    p.category,
    p.product_name,
    p.price,
    p.cost_price,
    ROUND((p.price - p.cost_price) / p.price * 100, 1) AS margin_pct,
    p.rating,
    p.reviews_count
FROM products p
ORDER BY margin_pct DESC
LIMIT 20;

-- Q10: Cancellation & Return Rate by Category
SELECT
    p.category,
    COUNT(*) FILTER (WHERE o.status = 'cancelled') AS cancellations,
    COUNT(*) FILTER (WHERE o.status = 'returned')  AS returns,
    COUNT(*)                                        AS total_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE o.status IN ('cancelled','returned'))
          / COUNT(*), 2)                            AS loss_rate_pct
FROM orders o
JOIN order_items oi ON o.order_id   = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY loss_rate_pct DESC;
