-- Purpose: large transfers of USDT/USDC transfers of USD 1M or more
-- Window:  2026-11-01 to 2026-11-07 (UTC)
-- Source:  bigquery-public-data.crypto_ethereum.token_transfers
-- Output:  not exported, but can be used to generate a CSV of the top 100 transfers

DECLARE min_usd INT64 DEFAULT 1000000;

WITH transfers AS (
  SELECT
    block_timestamp,
    transaction_hash,
    token_address,
    from_address AS sender,
    to_address AS receiver,
    SAFE_CAST(value AS NUMERIC) / 1000000 AS amount_usd_approx
  FROM `bigquery-public-data.crypto_ethereum.token_transfers`
  WHERE block_timestamp >= TIMESTAMP('2026-11-01')
AND block_timestamp < TIMESTAMP('2026-11-08')
    AND token_address IN (
      '0xdac17f958d2ee523a2206206994597c13d831ec7',
      '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
    )
)
SELECT *
FROM transfers
WHERE amount_usd_approx >= min_usd
ORDER BY amount_usd_approx DESC
LIMIT 100