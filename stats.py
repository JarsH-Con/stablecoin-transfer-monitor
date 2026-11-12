"""Reproduce the headline numbers quoted in README.md and REPORT.md.

Inputs (exported from BigQuery into this folder):
    daily.csv      output of queries/02_daily_trend.sql
    receivers.csv  output of queries/03_top_receivers.sql
    senders.csv    output of queries/04_top_senders.sql
    labels.csv     Etherscan tags compiled by hand (optional)

Run with: python stats.py
All shares are measured against the total volume in daily.csv.
"""
import pandas as pd

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

daily = pd.read_csv('daily.csv', parse_dates=['day'])
recv = pd.read_csv('receivers.csv').sort_values('total_usd_approx', ascending=False)
send = pd.read_csv('senders.csv').sort_values('total_usd_approx', ascending=False)

daily['avg_size_usd'] = daily.total_usd_approx / daily.large_transfers
daily['weekend'] = daily.day.dt.dayofweek >= 5

total_transfers = int(daily.large_transfers.sum())
total_usd = daily.total_usd_approx.sum()
peak = daily.loc[daily.total_usd_approx.idxmax()]

print('== Window and totals ==')
print(f'Window: {daily.day.min().date()} to {daily.day.max().date()} ({len(daily)} days)')
print(f'Large transfers: {total_transfers:,}')
print(f'Approximate volume: USD {total_usd / 1e9:,.1f}B')
print(f'Average transfer: USD {total_usd / total_transfers / 1e6:,.1f}M')
print(f'Peak day: {peak.day.date()} '
      f'(USD {peak.total_usd_approx / 1e9:,.1f}B, {peak.total_usd_approx / total_usd:.1%} of volume)')
print(f'First 3 days share of volume: {daily.total_usd_approx.head(3).sum() / total_usd:.1%}')
weekend_avg = daily[daily.weekend].large_transfers.mean()
weekday_avg = daily[~daily.weekend].large_transfers.mean()
print(f'Average large transfers per day: weekday {weekday_avg:,.0f}, weekend {weekend_avg:,.0f} '
      f'({weekend_avg / weekday_avg - 1:.0%})')

print()
print('== Concentration (relative to daily.csv total) ==')
for name, df in [('Receivers', recv), ('Senders', send)]:
    share = df.total_usd_approx / total_usd
    print(f'{name}: top 1 {share.head(1).sum():.1%}, top 3 {share.head(3).sum():.1%}, '
          f'top 20 {share.sum():.1%} of volume; '
          f'top 20 = {df.transfers.sum() / total_transfers:.1%} of transfers')

print()
print('== Two-way flows (addresses in both top-20 lists, zero address excluded) ==')
both = recv.merge(send, left_on='receiver', right_on='sender', suffixes=('_in', '_out'))
both = both[both.receiver != ZERO_ADDRESS].copy()
both['out_over_in'] = both.total_usd_approx_out / both.total_usd_approx_in
both['matched_usd'] = both[['total_usd_approx_in', 'total_usd_approx_out']].min(axis=1)
exact = both[(both.transfers_in == both.transfers_out) & both.out_over_in.between(0.999, 1.001)]
print(f'Addresses in both lists: {len(both)}')
print(f'Matched in-and-out volume: USD {both.matched_usd.sum() / 1e9:,.1f}B '
      f'({both.matched_usd.sum() / total_usd:.1%} of volume)')
print(f'Identical in/out counts and totals: {len(exact)} addresses, '
      f'USD {exact.matched_usd.sum() / 1e9:,.1f}B each way ({exact.matched_usd.sum() / total_usd:.1%} of volume)')
view = both[['receiver', 'transfers_in', 'transfers_out', 'total_usd_approx_in',
             'total_usd_approx_out', 'out_over_in']].copy()
view['total_usd_approx_in'] = (view.total_usd_approx_in / 1e9).round(2)
view['total_usd_approx_out'] = (view.total_usd_approx_out / 1e9).round(2)
view['out_over_in'] = view.out_over_in.round(3)
print(view.rename(columns={'total_usd_approx_in': 'in_usd_b', 'total_usd_approx_out': 'out_usd_b'})
      .to_string(index=False))

print()
print('== Mint and burn (zero address) ==')
burned = recv.loc[recv.receiver == ZERO_ADDRESS, 'total_usd_approx'].sum()
minted = send.loc[send.sender == ZERO_ADDRESS, 'total_usd_approx'].sum()
print(f'Received by zero address (burns): USD {burned / 1e9:,.2f}B')
print(f'Sent from zero address (mints): USD {minted / 1e9:,.2f}B')
print(f'Net burn: USD {(burned - minted) / 1e9:,.2f}B')

print()
print('== Largest average transfers among top-20 senders ==')
send['avg_size_usd'] = send.total_usd_approx / send.transfers
print(send.sort_values('avg_size_usd', ascending=False)
      [['sender', 'transfers', 'avg_size_usd']].head(5).round(0).to_string(index=False))

if 'pct_of_volume' in send.columns:
    implied_total = (send.total_usd_approx / (send.pct_of_volume / 100)).mean()
    print()
    print('== Data check ==')
    print(f'daily.csv total: USD {total_usd / 1e9:,.1f}B')
    print(f'Total implied by senders.csv percentages: USD {implied_total / 1e9:,.1f}B '
          f'({implied_total / total_usd - 1:+.1%} vs daily.csv)')

try:
    labels = pd.read_csv('labels.csv')
except FileNotFoundError:
    labels = None

if labels is not None:
    top10 = recv.head(10).merge(labels, left_on='receiver', right_on='address', how='left')
    top10['category'] = top10['category'].fillna('Not checked')
    top10['share_of_volume'] = top10.total_usd_approx / total_usd
    coverage = top10.groupby('category').agg(addresses=('receiver', 'count'), share_of_volume=('share_of_volume', 'sum'))
    coverage['share_of_volume'] = coverage.share_of_volume.map('{:.1%}'.format)
    print()
    print('== Label coverage of the top 10 receivers ==')
    print(f'Top 10 receivers hold {top10.share_of_volume.sum():.1%} of volume')
    print(coverage.to_string())
    print()
    print(top10[['receiver', 'etherscan_name_tag', 'contract_creator', 'source_verified']].to_string(index=False))