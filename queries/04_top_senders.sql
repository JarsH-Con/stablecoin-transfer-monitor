-- Purpose: top senders of USDT/USDC transfers of USD 1M or more
-- Window:  2026-11-01 to 2026-11-07 (UTC)
-- Source:  bigquery-public-data.crypto_ethereum.token_transfers
-- Output:  exported as senders.csv

DECLARE min_usd INT64 DEFAULT 1000000;

WITH transfers AS (
  SELECT
    from_address AS sender,
    SAFE_CAST(value AS NUMERIC) / 1000000 AS amount_usd_approx
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE block_timestamp >= TIMESTAMP('2026-11-01')
    AND block_timestamp < TIMESTAMP('2026-11-08')
    AND token_address IN (
      '0xdac17f958d2ee523a2206206994597c13d831ec7',
      '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
    )
),
by_sender AS (
  SELECT
    sender,
    COUNT(*) AS transfers,
    SUM(amount_usd_approx) AS total_usd_approx
  FROM transfers
  WHERE amount_usd_approx >= min_usd
  GROUP BY sender
)
SELECT
  sender,
  transfers,
  total_usd_approx,
  ROUND(total_usd_approx / transfers, 0) AS avg_size_usd,
  ROUND(100 * total_usd_approx / SUM(total_usd_approx) OVER (), 2) AS pct_of_volume
FROM by_sender
ORDER BY total_usd_approx DESC
LIMIT 20