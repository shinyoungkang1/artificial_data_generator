# Logistics Shipping Domain Notes

## Core fields

- `shipment_id`, `order_id`, `carrier`, `service_level`
- `origin`, `destination`
- `ship_date`, `eta_date`, `delivered_date`
- `weight_kg`, `freight_cost_usd`, `fuel_surcharge_usd`
- `status`, `pod_signature`, `notes`

## Mess patterns

- status variants: `in_transit`, `In Transit`, `delivered?`, `delay`
- blank POD signatures for delivered shipments
- negative or string-encoded surcharges
- mixed date formats and timezone suffixes
- duplicated shipment records from integration retries

## Validation checks

- delivered date should be after ship date
- ETA variance should stay in plausible ranges
- shipment IDs unique except intentional duplicate injections
