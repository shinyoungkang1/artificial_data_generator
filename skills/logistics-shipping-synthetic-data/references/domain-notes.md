# Logistics Shipping Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `shipment_id` | string | `SHP-500000` to `SHP-{500000+rows-1}`, sequential | Yes |
| `order_id` | string | `ORD-100000` to `ORD-999999`, random | Yes |
| `carrier` | string | UPS, FedEx, DHL, USPS, XPO, Maersk | Yes |
| `service_level` | string | ground, 2-day, overnight, freight, economy | Yes |
| `origin` | string | Dallas,US; Chicago,US; Atlanta,US; Phoenix,US; Toronto,CA; Monterrey,MX | Yes |
| `destination` | string | Same pool as origin | Yes |
| `ship_date` | string (ISO date) | today minus 1-120 days | Yes |
| `eta_date` | string (ISO or mm/dd/yyyy) | ship_date plus 1-12 days | Yes |
| `delivered_date` | string (ISO date) | eta minus 1 to eta plus 4 days | Yes |
| `weight_kg` | float | 0.2 to 1200.0 | Yes |
| `freight_cost_usd` | float or string | max(10.0, weight * 0.7-3.5); may be `$X,XXX.XX` | Yes |
| `fuel_surcharge_usd` | float | freight * 0.02-0.20 | Yes |
| `status` | string | created, picked_up, in_transit, out_for_delivery, delivered, exception | Yes |
| `pod_signature` | string | A. Kim, J. Patel, M. Brown, none; may be blank | Yes |
| `notes` | string | dock appt, manual scan, label reprint, clean | Yes |

## Business Rules and Invariants

1. **Shipment ID uniqueness**: `shipment_id` is sequential (`SHP-500000 + i`),
   guaranteed unique within a single generation run.
2. **Date ordering**: `ship_date < eta_date` always. `delivered_date` may
   precede `eta_date` (early delivery) but should never precede `ship_date`.
3. **Cost floor**: `freight_cost_usd` has a $10.00 minimum regardless of weight.
4. **Surcharge derivation**: `fuel_surcharge_usd` is always 2-20% of `freight_cost_usd`.
5. **Status lifecycle**: Clean statuses follow
   `created -> picked_up -> in_transit -> out_for_delivery -> delivered | exception`.
   The generator assigns status randomly (not lifecycle-ordered).
6. **Order ID collisions**: `order_id` is randomly generated per row and may
   repeat across rows (simulating multi-piece shipments for one order).

## Mess Pattern Deep Dive

### Status drift (weight 0.28)
- **Simulates**: Carrier API returning inconsistent status strings across
  different endpoints or integration versions.
- **Values injected**: `In Transit` (mixed case), `delivered?` (uncertainty
  marker), `delay` (free-text override), `OUT_FOR_DELIVERY` (all caps).
- **Downstream failures**: Enum-based status mapping breaks, dashboard
  filtering misses rows, SLA calculations produce wrong results.

### Currency-formatted freight (weight 0.24)
- **Simulates**: Cost fields copy-pasted from invoices or formatted in
  spreadsheet exports.
- **Manifestation**: Float `1234.56` becomes string `$1,234.56`.
- **Downstream failures**: `float()` conversion raises ValueError, aggregation
  queries silently drop non-numeric rows, JOIN on cost ranges breaks.

### Blank POD signature (weight 0.20)
- **Simulates**: Unsigned deliveries, driver scanner failures, or contactless
  delivery protocols.
- **Manifestation**: Empty string `""` replaces actual signature name.
- **Downstream failures**: Delivery confirmation logic treats blank as
  undelivered, compliance reports flag false exceptions.

### Date format flip (weight 0.18)
- **Simulates**: Systems exporting dates in locale-dependent formats.
- **Manifestation**: `eta_date` changes from `2025-03-15` to `03/15/2025`.
- **Downstream failures**: ISO date parsers reject the row, date comparisons
  produce wrong ordering, SLA calculations break.

### Late-update note (weight 0.14)
- **Simulates**: Appended status updates from manual warehouse operator edits.
- **Manifestation**: `dock appt` becomes `dock appt / late update`.
- **Downstream failures**: Exact-match note filters miss rows, text parsing
  assumptions about single-value notes break.

## Real-World Context

This data mimics exports from transportation management systems (TMS) like
SAP TM, Oracle OTM, or MercuryGate. In production environments, shipment
data arrives via EDI 214 (shipment status) and EDI 210 (freight invoice)
messages. Common sources include carrier APIs (UPS Tracking, FedEx Track),
warehouse management system (WMS) exports, and 3PL portal downloads.

Typical consumers are freight audit teams, supply chain visibility platforms,
and logistics BI dashboards that must normalize heterogeneous carrier data
into a unified shipment lifecycle view.

## Cross-Skill Relationships

| Related Skill | Shared Fields | Relationship |
|--------------|--------------|-------------|
| `logistics-customs-docs-synthetic-data` | `shipment_id`, `carrier` | Customs records reference shipment IDs for cross-border clearance |
| `logistics-bol-docs-synthetic-data` | `shipment_id`, `weight_kg`, `origin`, `destination` | BOL documents contain shipment details as scanned images |

**Recommended generation order**: Generate shipping data first (establishes
shipment IDs), then customs records (references those IDs), then BOL docs
(references the same IDs with OCR noise added).
