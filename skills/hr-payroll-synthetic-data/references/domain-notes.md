# HR Payroll Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `payroll_id` | string | `PAY-800000` to `PAY-{800000+rows-1}`, sequential | Yes |
| `employee_id` | string | `EMP-10000` to `EMP-99999`, random | Yes |
| `department` | string | Engineering, Sales, Operations, Finance, HR, Support | Yes |
| `job_title` | string | Analyst, Manager, Associate, Lead, Specialist, Coordinator | Yes |
| `pay_period_start` | string (ISO date) | today minus 30-360 days | Yes |
| `pay_period_end` | string (ISO date) | start + 13 days | Yes |
| `pay_date` | string (ISO date) | end + 1-5 days | Yes |
| `hours_regular` | float | 60.0 to 86.0 | Yes |
| `hours_overtime` | float or string | 0.0 to 18.0; may be `"Xh"`/`"X"`/`"X.X"` | Yes |
| `gross_pay` | float | hours_regular * $22-120 + hours_overtime * $30-140 | Yes |
| `bonus` | float or string | 0.0 to 1500.0; may be empty string | Yes |
| `deductions` | float | 8-33% of gross_pay | Yes |
| `net_pay` | float | gross_pay + bonus - deductions | Yes |
| `payment_method` | string | direct_deposit, check, paycard | Yes |
| `bank_account_masked` | string | `****NNNN`; may be `XXXX-NNNN`/`""`/`N/A` | Yes |
| `status` | string | processed, pending, hold, adjusted | Yes |
| `notes` | string | clean, late approval, manual adjustment, reissue | Yes |

## Business Rules and Invariants

1. **Payroll ID uniqueness**: `payroll_id` is sequential (`PAY-800000 + i`),
   guaranteed unique within a single generation run.
2. **Net pay identity**: `net_pay = gross_pay + bonus - deductions` holds exactly
   in clean rows (floating-point rounding may cause sub-cent differences).
3. **Biweekly periods**: `pay_period_end = pay_period_start + 13 days` always.
4. **Pay date ordering**: `pay_date` is 1-5 days after `pay_period_end`.
5. **Deduction bounds**: Deductions are 8-33% of gross_pay.
6. **Regular hours range**: `hours_regular` is always 60-86 (represents biweekly
   hours for salaried/hourly employees).
7. **Employee ID collisions**: `employee_id` is randomly generated and may repeat
   across rows (same employee across multiple pay periods).

## Mess Pattern Deep Dive

### Overtime string encoding (weight 0.28)
- **Simulates**: Different HRIS exports encoding hours in inconsistent formats.
  Some systems append "h" for hours, some truncate decimals, some cast to integer.
- **Three variants**: `"8.53h"` (with suffix), `"8"` (integer string), `"8.5"`
  (one decimal place).
- **Downstream failures**: `float()` conversion raises ValueError on "h" suffix,
  integer truncation loses partial hours for overtime pay calculation, string
  comparison operators produce wrong results.

### Status drift (weight 0.24)
- **Simulates**: Payroll processors and HRIS platforms using different status
  label conventions across versions or modules.
- **Values injected**: `Processed` (title case), `re-run` (hyphenated), `hold `
  (trailing space), `ADJUSTED` (all caps).
- **Downstream failures**: Enum-based filters miss non-canonical statuses,
  payroll reconciliation reports show incomplete counts, compliance checks
  that look for "hold" miss `hold ` with trailing space.

### Bank account masking (weight 0.20)
- **Simulates**: Different payment processors or HRIS modules using different
  masking conventions for bank account numbers.
- **Values injected**: `XXXX-NNNN` (different mask chars with hyphen), `""`
  (missing), `N/A` (explicit null).
- **Downstream failures**: Regex-based account validation rejects non-standard
  formats, empty values cause NullPointerException in downstream systems,
  ACH routing logic fails on missing account data.

### Blank bonus (weight 0.16)
- **Simulates**: Payroll export omitting bonus field for employees who received
  no bonus, instead of writing `0.0`.
- **Manifestation**: Bonus field is empty string `""`.
- **Downstream failures**: `float("")` raises ValueError, net pay arithmetic
  identity breaks, tax withholding calculations on bonus income fail.

### Verification note (weight 0.12)
- **Simulates**: Payroll admin appending review flags to notes during
  adjustment cycles.
- **Manifestation**: `late approval` becomes `late approval / verify`.
- **Downstream failures**: Exact-match note filters miss rows, automated
  workflow triggers on note content fire unexpectedly.

## Real-World Context

This data mimics exports from payroll systems like ADP, Workday, Gusto,
Paychex, or SAP SuccessFactors. In production, payroll data arrives via
batch exports after each pay run, real-time API feeds for on-demand pay, or
SFTP file drops from third-party payroll processors.

Typical consumers are finance teams performing payroll reconciliation, HR
teams tracking compensation changes, compliance teams auditing overtime and
deduction calculations, and tax teams preparing W-2s and quarterly filings.

## Cross-Skill Relationships

| Related Skill | Shared Fields | Relationship |
|--------------|--------------|-------------|
| `hr-recruiting-synthetic-data` | `employee_id` (conceptual) | Recruited candidates who are hired appear as employees in payroll |
| `hr-employee-file-docs-synthetic-data` | `employee_id`, `department` | Scanned W-4s, I-9s, and offer letters reference payroll employee records |

**Recommended generation order**: Generate recruiting data first (candidates
flow into payroll as hires), then payroll records for active employees, then
employee file docs for onboarding paperwork extraction testing.
