# HR Payroll Domain Notes

## Core fields

- `payroll_id`, `employee_id`, `department`, `job_title`
- `pay_period_start`, `pay_period_end`, `pay_date`
- `hours_regular`, `hours_overtime`
- `gross_pay`, `bonus`, `deductions`, `net_pay`
- `payment_method`, `bank_account_masked`, `status`, `notes`

## Mess patterns

- overtime as strings (`8h`, `08`, `8.0`)
- status drift (`processed`, `Processed`, `hold`, `re-run`)
- masked account formatting inconsistency (`****1234`, `XXXX-1234`)
- empty bonus/deductions for selective employees
- duplicate payroll lines from reruns

## Validation checks

- `net_pay ~= gross_pay + bonus - deductions`
- pay period end should be >= start
- pay dates should follow pay period
