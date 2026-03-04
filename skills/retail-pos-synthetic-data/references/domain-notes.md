# Retail POS Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `transaction_id` | string | `TXN-700000` to `TXN-{700000+rows-1}`, sequential | Yes |
| `store_id` | string | `STR-100` to `STR-999`, random | Yes |
| `terminal_id` | string | `POS-01` to `POS-40`, zero-padded | Yes |
| `cashier_id` | string | `CASH-1000` to `CASH-9999`, random | Yes |
| `sku` | string | `SKU-100000` to `SKU-999999`, random | Yes |
| `category` | string | grocery, household, beauty, electronics, apparel, beverage | Yes |
| `quantity` | int | 1 to 8 | Yes |
| `unit_price` | float | 1.50 to 299.00 | Yes |
| `discount` | float | 0 to 35% of line total; may be inflated 1.6x | Yes |
| `subtotal` | float | unit_price * quantity - discount | Yes |
| `tax` | float | 2-12% of subtotal | Yes |
| `total` | float or string | subtotal + tax; may be `$X,XXX.XX` | Yes |
| `payment_type` | string | cash, credit, debit, gift_card, mobile_wallet | Yes |
| `receipt_timestamp` | string (ISO 8601) | UTC datetime with Z suffix, up to ~486 days back | Yes |
| `loyalty_id` | string | `LOY-100000` to `LOY-999999`, empty, or `none` | Yes |
| `notes` | string | clean, manual void check, coupon scan, receipt reprint | Yes |

## Business Rules and Invariants

1. **Transaction ID uniqueness**: `transaction_id` is sequential (`TXN-700000 + i`),
   guaranteed unique within a single generation run.
2. **Arithmetic identity**: `subtotal = unit_price * quantity - discount` and
   `total = subtotal + tax` hold exactly in clean rows (floating-point rounding
   may cause sub-cent differences).
3. **Tax bounds**: `tax` is between 2% and 12% of `subtotal`.
4. **Non-negative quantities**: `quantity` is always 1-8 (never zero or negative).
5. **Discount bounds (clean)**: Discount is 0-35% of `unit_price * quantity` in
   clean rows. The overage pattern can push this to ~56%.
6. **SKU format (clean)**: Always `SKU-NNNNNN` with uppercase prefix in clean rows.
7. **Timestamp ordering**: Timestamps span up to ~700,000 minutes (~486 days) back
   from generation time, in UTC with `Z` suffix.

## Mess Pattern Deep Dive

### Payment type drift (weight 0.30)
- **Simulates**: Different POS terminals or payment processors returning
  inconsistent payment method labels.
- **Values injected**: `Credit` (title case), `card` (generic), `cash ` (trailing
  space), `MOBILE_WALLET` (screaming case).
- **Downstream failures**: Payment reconciliation reports miscount payment methods,
  enum-based filters miss non-canonical rows, financial reporting aggregates
  split the same method into multiple buckets.

### Currency-formatted total (weight 0.22)
- **Simulates**: Receipt printer or export formatting embedding currency symbols
  in numeric fields.
- **Manifestation**: Float `1234.56` becomes string `$1,234.56`.
- **Downstream failures**: `float()` raises ValueError, SUM aggregations skip
  non-numeric rows silently in some tools, JOIN conditions on total ranges break.

### SKU case flip (weight 0.18)
- **Simulates**: Barcode scanner firmware or POS software outputting inconsistent
  case for product identifiers.
- **Manifestation**: `SKU-123456` becomes `sku-123456`.
- **Downstream failures**: Case-sensitive lookups fail to match inventory records,
  product joins produce NULLs, deduplication misses case variants.

### Discount overage (weight 0.14)
- **Simulates**: Manual discount entry errors or coupon stacking bugs that
  produce implausible discount amounts.
- **Manifestation**: Discount multiplied by 1.6, potentially exceeding line total.
- **Downstream failures**: Negative effective prices, revenue calculations go
  negative, data quality checks flag anomalous rows.

### Note noise (weight 0.12)
- **Simulates**: Cashier or system appending unclear status markers to notes.
- **Manifestation**: `coupon scan` becomes `coupon scan ???`.
- **Downstream failures**: Exact-match note filters miss rows, text parsing
  pipelines encounter unexpected characters.

## Real-World Context

This data mimics exports from retail POS systems like Square, Clover, Shopify
POS, or Oracle MICROS. In production, transaction data arrives via end-of-day
batch exports, real-time payment processor webhooks, or POS terminal log files.

Typical consumers are finance teams performing daily reconciliation, loss
prevention teams detecting anomalous transactions, and merchandising analysts
tracking category performance. The data feeds into general ledger postings,
tax reporting, and inventory replenishment triggers.

## Cross-Skill Relationships

| Related Skill | Shared Fields | Relationship |
|--------------|--------------|-------------|
| `retail-inventory-synthetic-data` | `sku`, `store_id`, `category` | Inventory records use the same SKU and store pools |
| `retail-receipt-ocr-synthetic-data` | `transaction_id`, `total`, `sku` | Scanned receipts reference POS transaction data |

**Recommended generation order**: Generate POS transactions first (establishes
SKUs and transaction IDs), then inventory with shared SKUs, then receipt docs
referencing the same transactions for OCR extraction testing.
