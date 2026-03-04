# Banking KYC Domain Notes

## Core fields

- `customer_id`, `application_id`, `onboarding_date`
- `nationality`, `residency_country`, `id_document_type`
- `risk_score`, `pep_flag`, `sanctions_hit`
- `source_of_funds`, `annual_income_usd`
- `review_status`, `reviewer_queue`, `notes`

## Mess patterns

- risk score as integer, decimal, or string bucket
- `pep_flag` and `sanctions_hit` encoded as bool/int/string
- status drift (`approved`, `Approved`, `manual-review`, `blocked?`)
- missing source-of-funds notes
- duplicate applications from retries/re-opened reviews

## Validation checks

- high risk should more frequently map to manual review queues
- application dates should be realistic and bounded
- sanction hits should increase hold/blocked statuses
