# Healthcare Provider Roster Domain Notes

## Core fields

- `provider_id`, `npi`, `tin`
- `provider_name`, `specialty`, `facility_name`
- `address_line1`, `city`, `state`, `zip`
- `phone`, `fax`, `accepting_new_patients`
- `contract_status`, `effective_date`, `termination_date`, `notes`

## Mess patterns

- specialty synonyms and abbreviation drift
- missing or malformed NPIs in small percentages
- phone/fax formatting inconsistency
- stale addresses and duplicate provider rows
- contract status casing and punctuation drift
