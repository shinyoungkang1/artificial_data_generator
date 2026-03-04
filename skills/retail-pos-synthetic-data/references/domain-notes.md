# Retail POS Domain Notes

## Core fields

- `transaction_id`, `store_id`, `terminal_id`, `cashier_id`
- `sku`, `category`, `quantity`, `unit_price`, `discount`
- `subtotal`, `tax`, `total`
- `payment_type`, `receipt_timestamp`, `loyalty_id`, `notes`

## Mess patterns

- payment drift: `credit`, `Credit`, `card`, `cash `
- string-encoded amounts with currency symbols
- duplicate transactions due to terminal retries
- missing loyalty IDs and malformed SKU prefixes
- discount overages causing negative subtotals

## Validation checks

- `total ~= subtotal + tax`
- quantity and price should be non-negative for normal sales
- transaction IDs unique except explicit duplicates
