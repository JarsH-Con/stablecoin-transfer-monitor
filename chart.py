"""Build the two charts used in README.md and REPORT.md.

Inputs:  daily.csv, receivers.csv, senders.csv (exported from BigQuery)
         labels.csv (optional, Etherscan tags compiled by hand)
Outputs: daily_chart.png, flows_chart.png
Run with: python chart.py
"""
import pandas as pd
import matplotlib.pyplot as plt

# Chart 1: large transfers per day
daily = pd.read_csv('daily.csv', parse_dates=['day'])

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(daily['day'].dt.strftime('%d %b'), daily['large_transfers'], color='#1f77b4')
ax.set_title('Large stablecoin transfers per day (USDT and USDC, USD 1M and above)')
ax.set_xlabel('Day (UTC)')
ax.set_ylabel('Number of transfers')
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig('daily_chart.png', dpi=150)
plt.close(fig)
print('saved daily_chart.png')

# Chart 2: USD received vs sent by the ten largest receivers
recv = pd.read_csv('receivers.csv').sort_values('total_usd_approx', ascending=False)
send = pd.read_csv('senders.csv')

top = recv.head(10).merge(
    send[['sender', 'total_usd_approx']],
    left_on='receiver', right_on='sender', how='left', suffixes=('_in', '_out'),
)
top['total_usd_approx_out'] = top['total_usd_approx_out'].fillna(0)
short = top['receiver'].str[:8] + '...' + top['receiver'].str[-4:]
try:
    tags = pd.read_csv('labels.csv').set_index('address')['etherscan_name_tag']
    tag = top['receiver'].map(tags)
    labels = [f'{t}\n{s}' if isinstance(t, str) and t != 'none' else s for t, s in zip(tag, short)]
except FileNotFoundError:
    labels = short
received = top['total_usd_approx_in'] / 1e9
sent = top['total_usd_approx_out'] / 1e9

fig, ax = plt.subplots(figsize=(10, 7))
positions = range(len(top))
height = 0.38
ax.barh([p + height / 2 for p in positions], received, height, label='Received', color='#1f77b4')
ax.barh([p - height / 2 for p in positions], sent, height, label='Sent', color='#ff7f0e')
ax.set_yticks(list(positions))
ax.set_yticklabels(labels)
ax.invert_yaxis()
ax.set_xlabel('USD billions (transfers of USD 1M and above)')
ax.set_title('Top 10 receivers: USD received vs USD sent')
ax.legend()
ax.grid(axis='x', alpha=0.3)
fig.tight_layout()
fig.savefig('flows_chart.png', dpi=150)
plt.close(fig)
print('saved flows_chart.png')