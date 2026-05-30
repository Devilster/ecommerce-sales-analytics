# 🛒 E-Commerce Sales Analytics Dashboard

> **End-to-end data analytics project** covering data generation, SQL analysis, Python EDA, and Power BI dashboarding — built to showcase real-world data analyst skills.

---

## 📊 Tools & Technologies

| Layer | Tool | Purpose |
|---|---|---|
| **Database** | PostgreSQL / SQLite | Store & query structured data |
| **Data Wrangling** | Pandas | Clean, merge, engineer features |
| **Statistics** | NumPy | Descriptive stats, percentiles, aggregations |
| **Visualization** | Matplotlib | Custom line, bar, scatter, histogram charts |
| **Visualization** | Seaborn | Heatmaps, pairplots, styled statistical charts |
| **BI Dashboard** | Power BI | Interactive KPI dashboard for business users |

---

## 📁 Project Structure

```
ecommerce-analytics/
│
├── data/
│   ├── generate_data.py        ← Synthetic dataset generator (10K orders)
│   ├── customers.csv           ← 2,000 customers
│   ├── products.csv            ← 500 products across 10 categories
│   ├── sellers.csv             ← 150 sellers
│   ├── orders.csv              ← 10,000 orders (2022–2024)
│   ├── order_items.csv         ← 30,000+ line items
│   └── payments.csv            ← 10,000 payment records
│
├── sql/
│   ├── schema_and_queries.sql  ← Full PostgreSQL schema + 10 business queries
│   └── db_loader.py            ← Loads CSVs → PostgreSQL or SQLite
│
├── notebooks/
│   └── eda_analysis.py         ← Full EDA: 10 charts with Pandas/NumPy/Matplotlib/Seaborn
│
├── powerbi_export/
│   ├── generate_pbi_data.py    ← Generates aggregated CSVs for Power BI
│   └── *.csv                   ← Pre-aggregated data (monthly KPI, categories, states ...)
│
├── images/                     ← All generated chart PNGs
└── README.md
```

---

## 🗄️ Database Schema

```
customers ──┐
            ├── orders ──── order_items ── products
sellers ────┘       └───── payments
```

**Tables:** `customers` · `sellers` · `products` · `orders` · `order_items` · `payments`

---

## 🔍 SQL Business Queries

| # | Query | Technique Used |
|---|---|---|
| Q1 | Monthly Revenue Trend | `GROUP BY`, `DATE_TRUNC` |
| Q2 | Top 10 Categories by Revenue | Multi-table `JOIN` |
| Q3 | Revenue by State | Aggregation |
| Q4 | Payment Method Distribution | `OVER()` Window Function |
| Q5 | Delivery Performance | `CASE WHEN`, date arithmetic |
| Q6 | Customer Lifetime Value | Subquery, multi-agg |
| Q7 | Seller Performance | JOIN + GROUP BY |
| Q8 | Month-over-Month Growth | `LAG()` Window Function |
| Q9 | Product Profit Margin | Derived columns |
| Q10 | Cancellation Rate by Category | `FILTER (WHERE ...)` |

---

## 📈 EDA Charts (Python)

| Chart | Insight |
|---|---|
| 01 Monthly Revenue Trend | Revenue + MoM growth bars (2022–2024) |
| 02 Category Analysis | Revenue + profit margin by category |
| 03 Payment Analysis | Pie + bar of payment methods |
| 04 Delivery Performance | On-time rate, days distribution, state heatmap |
| 05 State Revenue | Bar + bubble chart geographic analysis |
| 06 Order Patterns | Status distribution + Day×Hour heatmap |
| 07 Product Insights | Rating vs reviews scatter + avg rating bars |
| 08 Customer CLV | Lifetime value histogram + segment pie |
| 09 Correlation Heatmap | Order metrics + product attribute correlations |
| 10 KPI Dashboard | Dark-theme executive summary dashboard |

---

## 📊 Power BI Dashboard

Import the CSVs from `powerbi_export/` into Power BI Desktop:

**Page 1 — Revenue Overview**
- KPI Cards: Total Revenue, Orders, Avg Order Value, Customers
- Line Chart: Monthly Revenue Trend (with forecast)
- Bar Chart: MoM Growth %

**Page 2 — Category & Geography**
- Bar Chart: Top Categories by Revenue
- Donut Chart: Payment Method Split
- Filled Map: Revenue by State

**Page 3 — Operations & Customers**
- Gauge: On-Time Delivery Rate
- Treemap: Customer CLV Segments
- Table: Top 50 Products

---

## 🚀 How to Run

```bash
# 1. Clone and install dependencies
git clone https://github.com/YOUR_USERNAME/ecommerce-analytics
cd ecommerce-analytics
pip install -r requirements.txt

# 2. Generate synthetic dataset
python data/generate_data.py

# 3. Load into database
python sql/db_loader.py --db sqlite     # local demo
python sql/db_loader.py --db postgres   # needs PG running

# 4. Run full EDA (generates all charts)
python notebooks/eda_analysis.py

# 5. Generate Power BI export files
python powerbi_export/generate_pbi_data.py
```

**For PostgreSQL**, set environment variables:
```bash
export PG_HOST=localhost
export PG_PORT=5432
export PG_USER=postgres
export PG_PASS=your_password
export PG_DB=ecommerce
```

---

## 🔑 Key Business Insights

- 💎 **Jewellery** is the highest revenue category (₹12.2 Cr) with strong margins
- 🚚 **83%+ on-time delivery rate** — room to improve for specific states
- 💳 **Payment methods evenly split** — UPI and COD dominate volume
- 👤 **Top 10% customers** contribute ~40% of total revenue (Pareto principle)
- 📅 **Q3 peaks** — July–September show highest order volumes

---

## 🛠️ Requirements

```
pandas
numpy
matplotlib
seaborn
sqlalchemy
psycopg2-binary   # for PostgreSQL
faker
```