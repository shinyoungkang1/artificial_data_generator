# Logistics Customs Domain Notes

## Core fields

- `declaration_id`, `shipment_id`, `port_code`
- `export_country`, `import_country`, `incoterm`
- `hs_code`, `goods_description`, `declared_value_usd`
- `duty_usd`, `tax_usd`, `clearance_status`
- `inspection_flag`, `inspector_note`, `document_language`

## Mess patterns

- HS code punctuation drift and partial truncation
- declared value as mixed numeric/string currency values
- clearance status variants and spelling errors
- missing inspector notes on flagged shipments
- duplicate declarations from amendment cycles
