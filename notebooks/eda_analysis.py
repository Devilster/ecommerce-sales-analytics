"""
eda_analysis.py
────────────────────────────────────────────────────────────
Full Exploratory Data Analysis
Tools: Pandas · NumPy · Matplotlib · Seaborn · SQLAlchemy
────────────────────────────────────────────────────────────
"""

import os, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine, text

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(__file__)
DB     = os.path.join(BASE, '..', 'data', 'ecommerce.db')
IMGDIR = os.path.join(BASE, '..', 'images')
os.makedirs(IMGDIR, exist_ok=True)

engine = create_engine(f'sqlite:///{DB}')

PALETTE   = 'Blues_d'
BG        = '#F8F9FA'
ACCENT    = '#1A6FB0'
WARN      = '#E74C3C'
SUCCESS   = '#27AE60'
FIG_DPI   = 150

def q(sql): 
    with engine.connect() as c: 
        return pd.read_sql(text(sql), c)

def save(fig, name):
    path = f'{IMGDIR}/{name}.png'
    fig.savefig(path, dpi=FIG_DPI, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print(f'  💾 saved → {name}.png')

# ── Load all tables ───────────────────────────────────────────────────────────
print('\n📦 Loading data ...')
orders   = pd.read_sql('SELECT * FROM orders',      engine, parse_dates=['order_date','actual_delivery','estimated_delivery'])
items    = pd.read_sql('SELECT * FROM order_items', engine)
products = pd.read_sql('SELECT * FROM products',    engine)
customers= pd.read_sql('SELECT * FROM customers',   engine, parse_dates=['signup_date'])
payments = pd.read_sql('SELECT * FROM payments',    engine, parse_dates=['payment_date'])
sellers  = pd.read_sql('SELECT * FROM sellers',     engine)

# ── Feature Engineering (Pandas + NumPy) ─────────────────────────────────────
print('🔧 Feature engineering ...')
orders['year']          = orders['order_date'].dt.year
orders['month']         = orders['order_date'].dt.month
orders['month_name']    = orders['order_date'].dt.strftime('%b')
orders['quarter']       = orders['order_date'].dt.quarter
orders['day_of_week']   = orders['order_date'].dt.day_name()
orders['hour']          = orders['order_date'].dt.hour

delivered = orders[orders['status']=='delivered'].copy()
delivered['delivery_days'] = (
    delivered['actual_delivery'] - delivered['order_date']
).dt.total_seconds() / 86400
delivered['is_late'] = delivered['actual_delivery'] > delivered['estimated_delivery']

items = items.merge(products[['product_id','category','cost_price']], on='product_id')
items['profit'] = items['line_total'] - (items['cost_price'] * items['quantity'])

# ── NumPy Stats Summary ───────────────────────────────────────────────────────
print('\n📊 NumPy Descriptive Stats (Order Total):')
rev = orders[orders['status']=='delivered']['order_total'].values
print(f"   Mean:    ₹{np.mean(rev):>12,.2f}")
print(f"   Median:  ₹{np.median(rev):>12,.2f}")
print(f"   Std Dev: ₹{np.std(rev):>12,.2f}")
print(f"   P25:     ₹{np.percentile(rev,25):>12,.2f}")
print(f"   P75:     ₹{np.percentile(rev,75):>12,.2f}")
print(f"   Max:     ₹{np.max(rev):>12,.2f}")

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 1 — Monthly Revenue Trend (Line Chart)
# ═══════════════════════════════════════════════════════════════════════════════
print('\n🎨 Generating charts ...')

monthly = (delivered.groupby(delivered['order_date'].dt.to_period('M'))
           .agg(revenue=('order_total','sum'), orders=('order_id','count'))
           .reset_index())
monthly['order_date'] = monthly['order_date'].dt.to_timestamp()
monthly['mom_growth'] = monthly['revenue'].pct_change() * 100

fig, axes = plt.subplots(2, 1, figsize=(14, 8), facecolor=BG)
fig.suptitle('Monthly Revenue Trend (2022–2024)', fontsize=16, fontweight='bold', y=1.01)

ax1 = axes[0]
ax1.set_facecolor(BG)
ax1.plot(monthly['order_date'], monthly['revenue']/1e6, color=ACCENT, lw=2.5, marker='o', ms=4)
ax1.fill_between(monthly['order_date'], monthly['revenue']/1e6, alpha=0.15, color=ACCENT)
ax1.set_ylabel('Revenue (₹ Millions)', fontsize=11)
ax1.set_title('Monthly Revenue', fontweight='bold')
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('₹%.1fM'))
ax1.grid(axis='y', alpha=0.3)
sns.despine(ax=ax1)

ax2 = axes[1]
ax2.set_facecolor(BG)
colors_mom = [SUCCESS if x >= 0 else WARN for x in monthly['mom_growth'].fillna(0)]
ax2.bar(monthly['order_date'], monthly['mom_growth'].fillna(0), color=colors_mom, width=20)
ax2.axhline(0, color='black', lw=0.8, ls='--')
ax2.set_ylabel('MoM Growth (%)', fontsize=11)
ax2.set_title('Month-over-Month Growth %', fontweight='bold')
ax2.grid(axis='y', alpha=0.3)
sns.despine(ax=ax2)

plt.tight_layout()
save(fig, '01_monthly_revenue_trend')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 2 — Category Revenue Bar Chart
# ═══════════════════════════════════════════════════════════════════════════════
cat_rev = (items.merge(orders[['order_id','status']], on='order_id')
           .query("status=='delivered'")
           .groupby('category')
           .agg(revenue=('line_total','sum'), profit=('profit','sum'))
           .sort_values('revenue', ascending=True)
           .reset_index())
cat_rev['margin_pct'] = (cat_rev['profit'] / cat_rev['revenue'] * 100).round(1)

fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)
fig.suptitle('Category Performance Analysis', fontsize=16, fontweight='bold')

ax = axes[0]
ax.set_facecolor(BG)
bars = ax.barh(cat_rev['category'], cat_rev['revenue']/1e6,
               color=sns.color_palette('Blues_d', len(cat_rev)))
ax.set_xlabel('Revenue (₹ Millions)', fontsize=11)
ax.set_title('Revenue by Category', fontweight='bold')
for bar, val in zip(bars, cat_rev['revenue']):
    ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
            f'₹{val/1e6:.1f}M', va='center', fontsize=9)
sns.despine(ax=ax)

ax = axes[1]
ax.set_facecolor(BG)
colors_m = [SUCCESS if x > 40 else WARN for x in cat_rev['margin_pct']]
bars2 = ax.barh(cat_rev['category'], cat_rev['margin_pct'], color=colors_m)
ax.set_xlabel('Profit Margin (%)', fontsize=11)
ax.set_title('Profit Margin % by Category', fontweight='bold')
ax.axvline(cat_rev['margin_pct'].mean(), color='navy', lw=1.5, ls='--',
           label=f"Avg: {cat_rev['margin_pct'].mean():.1f}%")
ax.legend(fontsize=9)
for bar, val in zip(bars2, cat_rev['margin_pct']):
    ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
            f'{val}%', va='center', fontsize=9)
sns.despine(ax=ax)

plt.tight_layout()
save(fig, '02_category_analysis')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 3 — Payment Method Distribution (Pie + Bar)
# ═══════════════════════════════════════════════════════════════════════════════
pay_dist = payments.groupby('payment_type').agg(
    count=('payment_id','count'),
    total=('amount','sum')
).reset_index().sort_values('count', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=BG)
fig.suptitle('Payment Method Analysis', fontsize=16, fontweight='bold')

ax = axes[0]
ax.set_facecolor(BG)
wedge_props = dict()
wedges, texts, autotexts = ax.pie(
    pay_dist['count'], labels=pay_dist['payment_type'],
    autopct='%1.1f%%', startangle=90,
    colors=sns.color_palette('Set2'), **wedge_props)
[t.set_fontsize(10) for t in texts]
[t.set_fontsize(9)  for t in autotexts]
ax.set_title('Transaction Count Split', fontweight='bold')

ax = axes[1]
ax.set_facecolor(BG)
palette = sns.color_palette('Set2', len(pay_dist))
sns.barplot(data=pay_dist, x='payment_type', y='total', palette=palette, ax=ax)
ax.set_title('Total Amount by Payment Method', fontweight='bold')
ax.set_xlabel('')
ax.set_ylabel('Amount (₹)', fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'₹{x/1e7:.1f}Cr'))
ax.tick_params(axis='x', rotation=20)
sns.despine(ax=ax)

plt.tight_layout()
save(fig, '03_payment_analysis')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 4 — Delivery Performance
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=BG)
fig.suptitle('Delivery Performance Analysis', fontsize=16, fontweight='bold')

# On-time vs Late
ax = axes[0]
ax.set_facecolor(BG)
ontime = delivered['is_late'].value_counts()
ax.pie([ontime.get(False,0), ontime.get(True,0)],
       labels=['On Time', 'Late'],
       colors=[SUCCESS, WARN],
       autopct='%1.1f%%', startangle=90,
       )
ax.set_title('On-Time Delivery Rate', fontweight='bold')

# Delivery days distribution
ax = axes[1]
ax.set_facecolor(BG)
ax.hist(delivered['delivery_days'].dropna(), bins=30, color=ACCENT, edgecolor='white', alpha=0.85)
ax.axvline(delivered['delivery_days'].mean(), color=WARN, lw=2, ls='--',
           label=f"Mean: {delivered['delivery_days'].mean():.1f} days")
ax.set_xlabel('Days to Deliver', fontsize=11)
ax.set_ylabel('Orders', fontsize=11)
ax.set_title('Delivery Days Distribution', fontweight='bold')
ax.legend()
sns.despine(ax=ax)

# Avg delivery days by state (top 10)
ax = axes[2]
ax.set_facecolor(BG)
state_del = (delivered.groupby('state')['delivery_days']
             .mean().sort_values(ascending=True).head(10))
sns.barplot(x=state_del.values, y=state_del.index,
            palette='RdYlGn_r', ax=ax)
ax.set_xlabel('Avg Delivery Days', fontsize=11)
ax.set_title('Avg Delivery by State', fontweight='bold')
sns.despine(ax=ax)

plt.tight_layout()
save(fig, '04_delivery_performance')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 5 — Revenue by State (Seaborn + Matplotlib)
# ═══════════════════════════════════════════════════════════════════════════════
state_rev = (delivered.groupby('state')
             .agg(revenue=('order_total','sum'),
                  orders=('order_id','count'),
                  customers=('customer_id','nunique'))
             .sort_values('revenue', ascending=False)
             .reset_index())

fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)
fig.suptitle('Geographic Revenue Analysis', fontsize=16, fontweight='bold')

ax = axes[0]
ax.set_facecolor(BG)
sns.barplot(data=state_rev, x='revenue', y='state',
            palette=sns.color_palette('Blues_d', len(state_rev)), ax=ax)
ax.set_xlabel('Revenue (₹)', fontsize=11)
ax.set_title('Revenue by State', fontweight='bold')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'₹{x/1e6:.0f}M'))
sns.despine(ax=ax)

ax = axes[1]
ax.set_facecolor(BG)
scatter = ax.scatter(state_rev['customers'], state_rev['orders'],
                     s=state_rev['revenue']/5e4,
                     c=state_rev['revenue'],
                     cmap='Blues', alpha=0.8, edgecolors='white', lw=0.8)
for _, row in state_rev.iterrows():
    ax.annotate(row['state'], (row['customers'], row['orders']),
                fontsize=7, ha='center', va='bottom')
plt.colorbar(scatter, ax=ax, label='Revenue (₹)')
ax.set_xlabel('Unique Customers', fontsize=11)
ax.set_ylabel('Total Orders', fontsize=11)
ax.set_title('Orders vs Customers by State\n(bubble = revenue)', fontweight='bold')
sns.despine(ax=ax)

plt.tight_layout()
save(fig, '05_state_revenue')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 6 — Order Status & Order Hour Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=BG)
fig.suptitle('Order Patterns', fontsize=16, fontweight='bold')

# Order status
ax = axes[0]
ax.set_facecolor(BG)
status_cnt = orders['status'].value_counts()
colors_s   = [SUCCESS if s=='delivered' else (WARN if s=='cancelled' else ACCENT)
              for s in status_cnt.index]
ax.bar(status_cnt.index, status_cnt.values, color=colors_s, edgecolor='white')
ax.set_title('Order Status Distribution', fontweight='bold')
ax.set_ylabel('Count', fontsize=11)
ax.tick_params(axis='x', rotation=20)
for i, v in enumerate(status_cnt.values):
    ax.text(i, v+50, f'{v:,}', ha='center', fontsize=9, fontweight='bold')
sns.despine(ax=ax)

# Heatmap: orders by day × hour
ax = axes[1]
ax.set_facecolor(BG)
day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
heat_data = (orders.groupby(['day_of_week','hour'])
             .size().unstack(fill_value=0)
             .reindex(day_order))
sns.heatmap(heat_data, ax=ax, cmap='Blues', linewidths=0.3,
            cbar_kws={'label': 'Orders'})
ax.set_title('Order Volume: Day × Hour', fontweight='bold')
ax.set_xlabel('Hour of Day', fontsize=11)
ax.set_ylabel('')

plt.tight_layout()
save(fig, '06_order_patterns')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 7 — Product Rating & Review Correlation (Seaborn)
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=BG)
fig.suptitle('Product Insights', fontsize=16, fontweight='bold')

ax = axes[0]
ax.set_facecolor(BG)
sns.scatterplot(data=products, x='rating', y='reviews_count',
                hue='category', palette='tab10', alpha=0.7,
                s=50, ax=ax, legend=False)
ax.set_title('Rating vs Reviews Count by Category', fontweight='bold')
ax.set_xlabel('Rating', fontsize=11)
ax.set_ylabel('Reviews Count', fontsize=11)
sns.despine(ax=ax)

ax = axes[1]
ax.set_facecolor(BG)
cat_rating = (products.groupby('category')['rating']
              .mean().sort_values(ascending=False).reset_index())
colors_r = [SUCCESS if r >= 3.8 else WARN for r in cat_rating['rating']]
bars = ax.bar(cat_rating['category'], cat_rating['rating'],
              color=colors_r, edgecolor='white')
ax.axhline(products['rating'].mean(), color='navy', ls='--', lw=1.5,
           label=f"Overall Avg: {products['rating'].mean():.2f}")
ax.set_title('Avg Rating by Category', fontweight='bold')
ax.set_ylabel('Average Rating', fontsize=11)
ax.set_ylim(0, 5.5)
ax.legend()
ax.tick_params(axis='x', rotation=25)
for bar, val in zip(bars, cat_rating['rating']):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
            f'{val:.2f}', ha='center', fontsize=9, fontweight='bold')
sns.despine(ax=ax)

plt.tight_layout()
save(fig, '07_product_insights')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 8 — Customer Lifetime Value Distribution
# ═══════════════════════════════════════════════════════════════════════════════
clv = (delivered.groupby('customer_id')
       .agg(total_orders=('order_id','count'),
            lifetime_value=('order_total','sum'))
       .reset_index())
clv['segment'] = pd.cut(clv['lifetime_value'],
                         bins=[0,50000,200000,500000,np.inf],
                         labels=['Bronze','Silver','Gold','Platinum'])

fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=BG)
fig.suptitle('Customer Lifetime Value Analysis', fontsize=16, fontweight='bold')

ax = axes[0]
ax.set_facecolor(BG)
ax.hist(clv['lifetime_value']/1000, bins=40, color=ACCENT, edgecolor='white', alpha=0.85)
ax.axvline(clv['lifetime_value'].median()/1000, color=WARN, ls='--', lw=2,
           label=f"Median: ₹{clv['lifetime_value'].median()/1000:.0f}K")
ax.set_xlabel('Lifetime Value (₹ Thousands)', fontsize=11)
ax.set_ylabel('Customers', fontsize=11)
ax.set_title('CLV Distribution', fontweight='bold')
ax.legend()
sns.despine(ax=ax)

ax = axes[1]
ax.set_facecolor(BG)
seg_cnt = clv['segment'].value_counts().reindex(['Platinum','Gold','Silver','Bronze'])
colors_seg = ['#FFD700','#C0C0C0','#CD7F32','#6CB4E4']
wedges, texts, autotexts = ax.pie(
    seg_cnt, labels=seg_cnt.index, colors=colors_seg,
    autopct='%1.1f%%', startangle=90,
    )
ax.set_title('Customer Segments by CLV', fontweight='bold')

plt.tight_layout()
save(fig, '08_customer_clv')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 9 — Correlation Heatmap (NumPy + Seaborn)
# ═══════════════════════════════════════════════════════════════════════════════
num_cols = ['order_total','delivery_days','is_late']
merged_corr = delivered[num_cols].copy()
merged_corr['is_late'] = merged_corr['is_late'].astype(int)
corr_matrix = merged_corr.corr()   # NumPy under the hood

# also add product numerics
prod_num = products[['price','cost_price','rating','reviews_count','stock']].corr()

fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=BG)
fig.suptitle('Correlation Analysis', fontsize=16, fontweight='bold')

sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            ax=axes[0], square=True, linewidths=0.5,
            cbar_kws={'shrink': 0.8})
axes[0].set_title('Order Metrics Correlation', fontweight='bold')

sns.heatmap(prod_num, annot=True, fmt='.2f', cmap='coolwarm',
            ax=axes[1], square=True, linewidths=0.5,
            cbar_kws={'shrink': 0.8})
axes[1].set_title('Product Attributes Correlation', fontweight='bold')

plt.tight_layout()
save(fig, '09_correlation_heatmap')

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART 10 — Executive KPI Summary Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
total_revenue   = delivered['order_total'].sum()
total_orders    = len(delivered)
avg_order_val   = delivered['order_total'].mean()
unique_customers= delivered['customer_id'].nunique()
ontime_rate     = (~delivered['is_late']).mean() * 100
total_profit    = items.merge(orders[['order_id','status']], on='order_id').query("status=='delivered'")['profit'].sum()

fig = plt.figure(figsize=(18, 10), facecolor='#1A1A2E')
fig.suptitle('E-Commerce Sales Analytics — Executive KPI Dashboard',
             fontsize=18, fontweight='bold', color='white', y=0.98)

kpis = [
    ('Total Revenue',      f'₹{total_revenue/1e7:.1f} Cr', '#3498DB'),
    ('Total Orders',       f'{total_orders:,}',             '#2ECC71'),
    ('Avg Order Value',    f'₹{avg_order_val:,.0f}',        '#9B59B6'),
    ('Unique Customers',   f'{unique_customers:,}',          '#E67E22'),
    ('On-Time Rate',       f'{ontime_rate:.1f}%',            '#1ABC9C'),
    ('Total Profit',       f'₹{total_profit/1e7:.1f} Cr',   '#E74C3C'),
]

for idx, (label, value, color) in enumerate(kpis):
    ax = fig.add_axes([0.02 + (idx%3)*0.33, 0.72 - (idx//3)*0.18, 0.29, 0.15])
    ax.set_facecolor(color)
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.axis('off')
    ax.text(0.5, 0.65, value, ha='center', va='center', fontsize=20,
            fontweight='bold', color='white', transform=ax.transAxes)
    ax.text(0.5, 0.25, label, ha='center', va='center', fontsize=11,
            color='white', alpha=0.9, transform=ax.transAxes)

# Mini trend chart inside dashboard
ax_trend = fig.add_axes([0.03, 0.07, 0.60, 0.38])
ax_trend.set_facecolor('#16213E')
ax_trend.plot(monthly['order_date'], monthly['revenue']/1e6,
              color='#3498DB', lw=2.5, marker='o', ms=4)
ax_trend.fill_between(monthly['order_date'], monthly['revenue']/1e6, alpha=0.2, color='#3498DB')
ax_trend.set_title('Monthly Revenue Trend', color='white', fontweight='bold', fontsize=12)
ax_trend.tick_params(colors='white')
ax_trend.yaxis.set_major_formatter(mticker.FormatStrFormatter('₹%.0fM'))
ax_trend.spines[:].set_color('#334155')
ax_trend.set_facecolor('#16213E')
for spine in ax_trend.spines.values(): spine.set_color('#334155')

# Mini category chart
ax_cat = fig.add_axes([0.67, 0.07, 0.30, 0.38])
ax_cat.set_facecolor('#16213E')
top5 = cat_rev.tail(5)
colors_kpi = sns.color_palette('Blues_d', 5)
ax_cat.barh(top5['category'], top5['revenue']/1e6, color=colors_kpi)
ax_cat.set_title('Top 5 Categories', color='white', fontweight='bold', fontsize=12)
ax_cat.tick_params(colors='white')
ax_cat.xaxis.set_major_formatter(mticker.FormatStrFormatter('₹%.0fM'))
for spine in ax_cat.spines.values(): spine.set_color('#334155')

save(fig, '10_kpi_dashboard')

print('\n✅ All 10 charts generated successfully!')
print(f'📁 Saved to: {IMGDIR}')
