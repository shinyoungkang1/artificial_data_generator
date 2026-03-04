# Healthcare Claims Domain Notes

## Core fields

- `claim_id`, `member_id`, `provider_npi`
- `cpt_code`, `icd10_code`
- `date_of_service`, `admit_date`, `discharge_date`
- `billed_amount`, `allowed_amount`, `paid_amount`, `patient_responsibility`
- `claim_status`, `facility_type`, `notes`

## Mess patterns

- CPT/ICD formatting drift and missing punctuation
- `claim_status` variants: `paid`, `PAID`, `pended`, `denied?`
- amount strings mixed with currency symbols and commas
- missing discharge date for outpatient claims
- duplicate claim lines from resubmissions

## Validation checks

- `paid_amount <= allowed_amount <= billed_amount`
- discharge date should not precede admit/date of service
- claim ids must remain unique except intentional duplicates
