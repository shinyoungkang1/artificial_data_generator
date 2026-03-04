# Retail Returns Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `return_id` | str | `RTN-2300000` onward, sequential | yes | Unique per row |
| `original_txn_id` | str | `TXN-1000000` to `TXN-9999999` | yes | Random, not unique |
| `store_id` | str | `STR-100` to `STR-999` | yes | Random, not unique |
| `return_date` | str | ISO date, 1-90 days after purchase | yes | Clean |
| `original_purchase_date` | str | ISO date, today minus 10-400 days | yes | Clean |
| `sku` | str | `SKU-10000` to `SKU-99999` | yes | Lowercased when messy |
| `category` | str | 7 retail categories | yes | Clean |
| `quantity_returned` | int | 1--5 | yes | Clean |
| `unit_price` | float | 5.00--2000.00 | yes | Clean |
| `refund_amount` | float | `unit_price * quantity` | yes | Currency string when messy |
| `restocking_fee_usd` | float | 0%, 10%, 15%, or 20% of refund | yes | Clean |
| `net_refund_usd` | float | `refund_amount - restocking_fee` | yes | Clean, derived |
| `return_reason` | str | 6 standard reasons | yes | Casing/spacing variants when messy |
| `refund_method` | str | `original_payment`, `store_credit`, `cash`, `exchange` | yes | Clean |
| `return_status` | str | `approved`, `pending`, `denied`, `processed`, `escalated` | yes | Casing/typo drift when messy |
| `notes` | str | `clean`, `manager override`, `receipt missing`, `warranty claim` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Date chain
- `original_purchase_date < return_date` always holds
- Return is 1-90 days after purchase
- Purchase date is 10-400 days in the past

### Amount chain (clean rows)
- `refund_amount = unit_price * quantity_returned`
- `net_refund_usd = refund_amount - restocking_fee_usd`
- Restocking fee is 0%, 10%, 15%, or 20% of refund amount

### Uniqueness
- `return_id` is globally unique (sequential: `RTN-2300000`, `RTN-2300001`, ...)
- `original_txn_id`, `store_id`, and `sku` may repeat

## Mess Pattern Deep Dive

### return_status (weight 0.30)
- **What it simulates**: Multi-store POS system consolidation where different store locations use different casing and shorthand for return statuses.
- **Messy values**: `APPROVED` (all caps), `pend` (abbreviation), `Denied ` (trailing space), `processed?` (uncertainty marker)
- **Downstream failure**: Enum validation rejects non-standard values; status-based routing misses variants.

### refund_amount (weight 0.24)
- **What it simulates**: POS export formats that include currency formatting in amount fields.
- **Messy value**: Float `299.99` becomes string `"$299.99"`
- **Downstream failure**: `float(value)` raises ValueError; net refund calculation breaks.

### return_reason (weight 0.20)
- **What it simulates**: Customer service systems that store return reasons in inconsistent formats.
- **Messy values**: `"Wrong Size"` (title case, spaces), `"DEFECTIVE"` (all caps), `"changed mind"` (spaces instead of underscores)
- **Downstream failure**: Reason-based analytics group differently; enum lookup fails.

### sku (weight 0.16)
- **What it simulates**: Case normalization issues in product lookup systems.
- **Messy value**: `"SKU-12345"` becomes `"sku-12345"` (lowercased)
- **Downstream failure**: Case-sensitive SKU lookups against product master fail.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated return processing systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based workflow triggers and warranty detection logic break.

## Real-World Context

Retail return data flows through multiple systems in the retail ecosystem:

- **POS terminal**: Customer initiates return at store register
- **Returns management system**: Validates return policy, calculates restocking fees
- **Inventory system**: Receives returned items, updates stock levels
- **Finance system**: Processes refunds to original payment or store credit

Each system introduces potential format drift: different POS vendors use different
status conventions, return reason codes vary by store location, and SKU casing
depends on the product master data version.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `original_txn_id` | retail-pos-synthetic-data | `transaction_id` | Links return to original sale |
| `sku` | retail-inventory-synthetic-data | `sku` | Product lookup for returned items |
| `store_id` | retail-receipt-ocr-synthetic-data | store reference | Receipts reference store ID |

**Recommended generation order:**
1. Generate POS transactions (establishes transaction IDs)
2. Generate inventory records (establishes SKU catalog)
3. Generate returns (references transaction IDs and SKUs)
4. Generate receipt OCR docs (references transactions)

Note: The current generators do not enforce referential integrity across skills.
Transaction IDs and SKUs in returns are randomly generated. For cross-skill
testing, post-process to align shared identifiers.
