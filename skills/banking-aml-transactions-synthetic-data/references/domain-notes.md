# Banking AML Transactions Domain Notes

## Core fields

- `txn_id`, `account_id`, `customer_id`, `counterparty_country`
- `txn_timestamp`, `amount_usd`, `channel`, `txn_type`
- `risk_score`, `rule_triggered`, `alert_id`, `alert_status`
- `investigator_queue`, `sar_filed_flag`, `notes`

## Mess patterns

- amount encoded as float, string, and currency style
- risk score bucket strings mixed with numeric values
- alert status variants and misspellings
- null alert IDs for transactions that should have alerts
- duplicated transactions from ingestion retries
